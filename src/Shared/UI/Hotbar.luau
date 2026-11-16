--!strict
-- Hotbar: 3-5 word slots (Wizard spell loadout / Defend backup defenses).
--
--   local bar = UI.Hotbar.new({ parent = hud, slots = 4 })
--   bar:setSlot(1, { word = "fireball", element = "Fire", charges = 3, maxCharges = 3 })
--   bar.Activated:Connect(function(index) ... end)    -- tap, number keys 1-5, gamepad R2 on the selected slot
--   bar:cooldown(1, 4)            -- 4s radial sweep + countdown
--   bar:setCharges(1, 2)          -- ring of pips around the slot's orb
--   bar:markUsed(1, true)         -- greyed out (no-repeat rules), word struck through
--
-- Radial sweep without images: two half-width clip frames each hold a full-size dark overlay whose UIGradient
-- hides one half-plane; rotating the gradients 0..360 wipes clockwise from 12 o'clock.

local Theme = require(script.Parent.Theme)
local Kit = require(script.Parent.Kit)
local Signal = require(script.Parent.Signal)

local Hotbar = {}
Hotbar.__index = Hotbar

export type SlotData = {
	word: string?,
	element: string?,
	colour: string?, -- fallback hex (result.visual.primaryColour)
	charges: number?,
	maxCharges: number?,
	subtitle: string?, -- e.g. cost "$120" for Defend, or "x3"
	used: boolean?,
}

export type Options = {
	parent: Instance?,
	slots: number?,
	slotSize: number?,
	position: UDim2?,
	anchor: Vector2?,
	keys: { Enum.KeyCode }?,
	zIndex: number?,
}

local KEYS = { Enum.KeyCode.One, Enum.KeyCode.Two, Enum.KeyCode.Three, Enum.KeyCode.Four, Enum.KeyCode.Five }
local HALF_HIDE = NumberSequence.new({
	NumberSequenceKeypoint.new(0, 1),
	NumberSequenceKeypoint.new(0.5, 1),
	NumberSequenceKeypoint.new(0.501, 0),
	NumberSequenceKeypoint.new(1, 0),
})

local function uiCfg(): any
	local ok, c = pcall(function()
		return (require(script.Parent.Parent.Config) :: any).UI
	end)
	return if ok and c then c else {}
end

function Hotbar.new(opts: Options?): any
	local o: Options = opts or {}
	local cfg = uiCfg()
	local T = Theme.get()
	local n = math.clamp(o.slots or 4, cfg.HotbarSlotsMin or 3, cfg.HotbarSlotsMax or 5)
	local size = o.slotSize or 76
	local z = o.zIndex or Theme.Z.hud
	local self: any = setmetatable({}, Hotbar)
	self.Activated = Signal.new() -- (index)
	self.SelectionChanged = Signal.new() -- (index)
	self._slots = {}
	self._conns = {}
	self._selected = 1
	self._n = n

	local gap = Theme.Space.sm + 2
	local root: Frame = Kit.new("Frame", {
		Name = "WordEngineHotbar",
		BackgroundTransparency = 1,
		AnchorPoint = o.anchor or Vector2.new(0.5, 1),
		Position = o.position or UDim2.new(0.5, 0, 1, -16),
		Size = UDim2.fromOffset(n * size + (n - 1) * gap + 24, size + 24),
		ZIndex = z,
	})
	self.root = root
	local _, tray = Kit.glass({ Name = "Tray", Size = UDim2.fromScale(1, 1), Radius = Theme.Radius.xl, ZIndex = z, Parent = root })
	Kit.padding(12).Parent = tray
	Kit.list(Enum.FillDirection.Horizontal, gap, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center).Parent = tray
	-- shrink the whole bar on narrow phones so it always fits (touch targets stay >= 48px: 76 * 0.7 = 53)
	local scale = Kit.new("UIScale", { Parent = root })
	local function fit()
		local cam = workspace.CurrentCamera
		if not cam then
			return
		end
		local w = cam.ViewportSize.X - 32
		scale.Scale = math.clamp(w / root.Size.X.Offset, 0.7, 1)
	end
	fit()
	if workspace.CurrentCamera then
		table.insert(self._conns, (workspace.CurrentCamera :: Camera):GetPropertyChangedSignal("ViewportSize"):Connect(fit))
	end

	for i = 1, n do
		self._slots[i] = self:_buildSlot(i, tray, size, z + 2, (o.keys or KEYS)[i])
	end
	self:select(1)

	local UIS = game:GetService("UserInputService")
	table.insert(self._conns, UIS.InputBegan:Connect(function(input: InputObject, processed: boolean)
		if processed or UIS:GetFocusedTextBox() then
			return
		end
		for i, kc in o.keys or KEYS do
			if input.KeyCode == kc and i <= n then
				self:select(i)
				self:activate(i)
				return
			end
		end
		if input.KeyCode == Enum.KeyCode.ButtonL1 then
			self:select(((self._selected - 2) % n) + 1)
		elseif input.KeyCode == Enum.KeyCode.ButtonR1 then
			self:select((self._selected % n) + 1)
		elseif input.KeyCode == Enum.KeyCode.ButtonR2 then
			self:activate(self._selected)
		end
	end))

	root.Parent = o.parent or Kit.screen("WordEngineHUD", 10)
	return self
end

function Hotbar:_buildSlot(i: number, parent: Instance, size: number, z: number, key: Enum.KeyCode?): any
	local T = Theme.get()
	local slot: any = { index = i, data = {} :: SlotData, cooldownToken = 0 }
	local btn: TextButton = Kit.new("TextButton", {
		Name = "Slot" .. i,
		AutoButtonColor = false,
		Text = "",
		BackgroundColor3 = Color3.new(1, 1, 1),
		BackgroundTransparency = 0,
		BorderSizePixel = 0,
		Size = UDim2.fromOffset(size, size),
		LayoutOrder = i,
		ZIndex = z,
		Selectable = true,
		Parent = parent,
	}, {
		Kit.corner(Theme.Radius.lg),
		Kit.gradient(T.Color.RaisedHi, T.Color.Glass, 90),
	})
	btn.SelectionImageObject = Kit.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) })
	slot.button = btn
	slot.gradient = btn:FindFirstChildOfClass("UIGradient")
	slot.stroke = Kit.stroke(Color3.new(1, 1, 1), Theme.StrokeTransparency, 1.5)
	slot.stroke.Parent = btn

	-- element orb (centre-top), ring of charge pips around it
	local orbSize = math.floor(size * 0.36)
	local orb: Frame = Kit.new("Frame", {
		Name = "Orb",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(0.5, 0, 0, math.floor(size * 0.36)),
		Size = UDim2.fromOffset(orbSize, orbSize),
		BackgroundColor3 = Color3.new(1, 1, 1),
		BorderSizePixel = 0,
		ZIndex = z + 2,
		Parent = btn,
	}, { Kit.corner(UDim.new(0.5, 0)), Kit.gradient(T.Element.None[1], T.Element.None[2], 45), Kit.stroke(Color3.new(1, 1, 1), 0.6, 1) })
	slot.orb = orb
	slot.pipHolder = Kit.new("Frame", {
		Name = "Pips",
		BackgroundTransparency = 1,
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = orb.Position,
		Size = UDim2.fromOffset(orbSize + 18, orbSize + 18),
		ZIndex = z + 2,
		Parent = btn,
	})
	slot.pips = {}

	local word = Kit.label({
		Name = "Word", Text = "", Size = "caption", Font = T.Font.Bold, Color = T.Color.Text,
		XAlign = Enum.TextXAlignment.Center, AutomaticSize = Enum.AutomaticSize.None,
		AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -6),
		FrameSize = UDim2.new(1, -8, 0, 16), ZIndex = z + 3, Parent = btn,
	})
	word.TextScaled = true
	Kit.new("UITextSizeConstraint", { MaxTextSize = Theme.textSize("caption"), MinTextSize = 9, Parent = word })
	slot.word = word
	-- strike-through line for used words (sits 1px above the text baseline; no overlap with stroke)
	slot.strike = Kit.new("Frame", {
		Name = "Strike", BackgroundColor3 = T.Color.TextDim, BorderSizePixel = 0, Visible = false,
		AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0.5, 0, 1, -14), Size = UDim2.new(0.7, 0, 0, 2),
		ZIndex = z + 4, Parent = btn,
	})

	local keyLabel = Kit.label({
		Name = "Key", Text = if key then tostring(i) else "", Size = "caption", Font = T.Font.Mono,
		Color = T.Color.TextMute, AutomaticSize = Enum.AutomaticSize.None,
		Position = UDim2.fromOffset(7, 4), FrameSize = UDim2.fromOffset(14, 14), ZIndex = z + 3, Parent = btn,
	})
	local UIS = game:GetService("UserInputService")
	keyLabel.Visible = UIS.KeyboardEnabled
	slot.sub = Kit.label({
		Name = "Sub", Text = "", Size = "caption", Font = T.Font.Bold, Color = T.Color.Warn,
		XAlign = Enum.TextXAlignment.Right, AutomaticSize = Enum.AutomaticSize.None,
		AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -7, 0, 4), FrameSize = UDim2.fromOffset(40, 14),
		ZIndex = z + 3, Parent = btn,
	})

	-- cooldown: radial sweep + number
	local sweep: Frame = Kit.new("Frame", {
		Name = "Cooldown", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = z + 5,
		Visible = false, Parent = btn,
	})
	local halves = {}
	for h = 1, 2 do
		local clip: Frame = Kit.new("Frame", {
			Name = if h == 1 then "Right" else "Left",
			BackgroundTransparency = 1,
			ClipsDescendants = true,
			Position = if h == 1 then UDim2.fromScale(0.5, 0) else UDim2.fromScale(0, 0),
			Size = UDim2.fromScale(0.5, 1),
			ZIndex = z + 5,
			Parent = sweep,
		})
		local overlay: Frame = Kit.new("Frame", {
			Name = "Overlay",
			BackgroundColor3 = Color3.fromHex(Theme.Hex.Ink),
			BackgroundTransparency = 0.28,
			BorderSizePixel = 0,
			Position = if h == 1 then UDim2.fromScale(-1, 0) else UDim2.fromScale(0, 0),
			Size = UDim2.fromScale(2, 1),
			ZIndex = z + 5,
			Parent = clip,
		}, { Kit.corner(Theme.Radius.lg) })
		local g: UIGradient = Kit.new("UIGradient", { Transparency = HALF_HIDE, Rotation = 0, Parent = overlay })
		halves[h] = g
	end
	slot.sweep = sweep
	slot.halves = halves
	slot.count = Kit.label({
		Name = "Count", Text = "", Size = "title", Font = T.Font.Heavy, Color = T.Color.Text,
		XAlign = Enum.TextXAlignment.Center, AutomaticSize = Enum.AutomaticSize.None,
		FrameSize = UDim2.fromScale(1, 1), ZIndex = z + 6, Parent = sweep,
	})

	btn.Activated:Connect(function()
		self:select(i)
		self:activate(i)
	end)
	btn.SelectionGained:Connect(function()
		self:select(i)
	end)
	btn.MouseEnter:Connect(function()
		Kit.tween(Kit.scaleOf(btn), T.Tween.fast, { Scale = 1.05 })
	end)
	btn.MouseLeave:Connect(function()
		Kit.tween(Kit.scaleOf(btn), T.Tween.fast, { Scale = 1 })
	end)
	self:_paint(slot)
	return slot
end

function Hotbar:_layoutPips(slot: any)
	local T = Theme.get()
	local max = math.clamp(slot.data.maxCharges or 0, 0, 12)
	local have = math.clamp(slot.data.charges or 0, 0, max)
	if #slot.pips ~= max then
		for _, p in slot.pips do
			p:Destroy()
		end
		slot.pips = {}
		local holder = slot.pipHolder
		for k = 1, max do
			-- evenly spaced on a circle, starting at 12 o'clock, clockwise
			local a = math.rad(-90 + (k - 1) * 360 / max)
			local pip: Frame = Kit.new("Frame", {
				Name = "Pip" .. k,
				AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.fromScale(0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)),
				Size = UDim2.fromOffset(7, 7),
				BackgroundColor3 = Color3.new(1, 1, 1),
				BorderSizePixel = 0,
				ZIndex = holder.ZIndex + 1,
				Parent = holder,
			}, { Kit.corner(UDim.new(0.5, 0)) })
			table.insert(slot.pips, pip)
		end
	end
	local c0 = Theme.element(slot.data.element, slot.data.colour)
	for k, pip in slot.pips do
		local lit = k <= have
		Kit.tween(pip, T.Tween.fast, {
			BackgroundColor3 = if lit then c0 else T.Color.TextMute,
			BackgroundTransparency = if lit then 0 else 0.55,
			Size = if lit then UDim2.fromOffset(7, 7) else UDim2.fromOffset(5, 5),
		})
	end
end

function Hotbar:_paint(slot: any)
	local T = Theme.get()
	local d: SlotData = slot.data
	local empty = d.word == nil or d.word == ""
	local c0, c1 = Theme.element(d.element, d.colour)
	local used = d.used == true
	if used then
		c0, c1 = T.Color.TextMute, T.Color.Raised
	end
	slot.word.Text = if empty then "EMPTY" else string.upper(d.word :: string)
	slot.word.TextColor3 = if empty or used then T.Color.TextMute else T.Color.Text
	slot.strike.Visible = used
	slot.sub.Text = d.subtitle or ""
	local og = slot.orb:FindFirstChildOfClass("UIGradient")
	og.Color = ColorSequence.new(c0, c1)
	slot.orb.BackgroundTransparency = if empty then 0.8 else 0
	slot.gradient.Color = if empty
		then ColorSequence.new(T.Color.Raised, T.Color.Glass)
		else ColorSequence.new(T.Color.RaisedHi:Lerp(c1, if used then 0 else 0.22), T.Color.Glass)
	slot.button.BackgroundTransparency = if used then 0.35 else 0
	self:_layoutPips(slot)
end

function Hotbar:setSlot(i: number, data: SlotData?)
	local slot = self._slots[i]
	if not slot then
		return
	end
	local prevWord = slot.data.word
	slot.data = table.clone(data or {})
	self:_paint(slot)
	if data and data.word and data.word ~= prevWord then
		Kit.pop(slot.button, 0.75)
	end
end

function Hotbar:getSlot(i: number): SlotData?
	local s = self._slots[i]
	return s and table.clone(s.data)
end

function Hotbar:setCharges(i: number, charges: number, maxCharges: number?)
	local slot = self._slots[i]
	if not slot then
		return
	end
	slot.data.charges = charges
	if maxCharges then
		slot.data.maxCharges = maxCharges
	end
	self:_layoutPips(slot)
end

function Hotbar:markUsed(i: number, used: boolean)
	local slot = self._slots[i]
	if not slot then
		return
	end
	slot.data.used = used
	self:_paint(slot)
end

-- Radial cooldown. `total` lets you resume a partially elapsed cooldown (remaining = seconds).
function Hotbar:cooldown(i: number, seconds: number, total: number?)
	local slot = self._slots[i]
	if not slot or seconds <= 0 then
		return
	end
	local full = math.max(total or seconds, seconds)
	slot.cooldownToken += 1
	local token = slot.cooldownToken
	slot.sweep.Visible = true
	slot.coolingUntil = os.clock() + seconds
	local RunService = game:GetService("RunService")
	local conn: RBXScriptConnection
	conn = RunService.RenderStepped:Connect(function()
		if token ~= slot.cooldownToken or not slot.button.Parent then
			conn:Disconnect()
			return
		end
		local remaining = slot.coolingUntil - os.clock()
		if remaining <= 0 then
			conn:Disconnect()
			slot.sweep.Visible = false
			slot.coolingUntil = nil
			Kit.pop(slot.button, 1.12)
			local T = Theme.get()
			slot.stroke.Color = Theme.element(slot.data.element, slot.data.colour)
			slot.stroke.Transparency = 0
			Kit.tween(slot.stroke, T.Tween.slow, { Transparency = if self._selected == i then 0.15 else Theme.StrokeTransparency,
				Color = if self._selected == i then slot.stroke.Color else Color3.new(1, 1, 1) })
			return
		end
		local elapsedAngle = 360 * (1 - remaining / full)
		slot.halves[1].Rotation = math.clamp(elapsedAngle, 0, 180)
		slot.halves[2].Rotation = math.clamp(elapsedAngle, 180, 360)
		slot.count.Text = if remaining >= 10 then tostring(math.ceil(remaining)) else string.format("%.1f", remaining)
	end)
end

function Hotbar:isCooling(i: number): boolean
	local s = self._slots[i]
	return s ~= nil and s.coolingUntil ~= nil
end

function Hotbar:select(i: number)
	if i < 1 or i > self._n then
		return
	end
	local T = Theme.get()
	self._selected = i
	for k, slot in self._slots do
		local on = k == i
		local c0 = Theme.element(slot.data.element, slot.data.colour)
		Kit.tween(slot.stroke, T.Tween.fast, {
			Color = if on then c0 else Color3.new(1, 1, 1),
			Transparency = if on then 0.15 else Theme.StrokeTransparency,
			Thickness = if on then 2.5 else 1.5,
		})
		Kit.tween(Kit.scaleOf(slot.button), T.Tween.fast, { Scale = if on then 1.06 else 1 })
	end
	self.SelectionChanged:Fire(i)
end

function Hotbar:activate(i: number)
	local slot = self._slots[i]
	if not slot then
		return
	end
	if self:isCooling(i) or slot.data.used or not slot.data.word then
		Kit.shake(slot.button)
		return
	end
	Kit.press(slot.button)
	self.Activated:Fire(i)
end

function Hotbar:destroy()
	for _, c in self._conns do
		c:Disconnect()
	end
	self.Activated:Destroy()
	self.SelectionChanged:Destroy()
	self.root:Destroy()
end

return Hotbar
