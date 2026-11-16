--!strict
-- Settings: the player settings panel (modal sheet; bottom sheet on phones, centred card on larger screens).
--
--   local settings = UI.Settings.new({ values = savedValues })
--   settings.Changed:Connect(function(key, value, all) remote:FireServer(all) end)
--   settings:open() / settings:close() / settings:toggle()
--
-- Settings.SCHEMA is pure data: servers use Settings.sanitize(raw) to validate what a client sends before
-- storing it (Data namespace "WordEngine", key `settings`). Applying a value updates Theme (text size,
-- reduced motion) live for every WordEngine widget.

local Theme = require(script.Parent.Theme)

local Settings = {}
Settings.__index = Settings

export type Field = {
	key: string,
	label: string,
	kind: "toggle" | "slider" | "choice",
	default: any,
	min: number?,
	max: number?,
	step: number?,
	choices: { string }?,
	hint: string?,
}

Settings.SCHEMA = {
	{ key = "reducedMotion", label = "Reduced motion", kind = "toggle", default = false, hint = "Calmer animations and no screen shake" },
	{ key = "autocomplete", label = "Word suggestions", kind = "toggle", default = true, hint = "Show chips while you type" },
	{ key = "didYouMean", label = "Did you mean", kind = "toggle", default = true, hint = "Offer corrections for typos" },
	{ key = "textSize", label = "Text size", kind = "choice", default = "M", choices = { "S", "M", "L", "XL" } },
	{ key = "music", label = "Music", kind = "slider", default = 0.6, min = 0, max = 1, step = 0.05 },
	{ key = "sfx", label = "Effects", kind = "slider", default = 0.8, min = 0, max = 1, step = 0.05 },
	{ key = "summonStyle", label = "Summon style", kind = "choice", default = "Auto", choices = { "Auto", "Spectral", "Solid" } },
} :: { Field }

local TEXT_SCALE = { S = 0.9, M = 1, L = 1.12, XL = 1.25 }

-- Pure: validate + fill defaults. Unknown keys dropped, numbers clamped and stepped, choices checked.
function Settings.sanitize(raw: any): { [string]: any }
	local out = {}
	local src = if type(raw) == "table" then raw else {}
	for _, f in Settings.SCHEMA do
		local v = src[f.key]
		if f.kind == "toggle" then
			out[f.key] = if type(v) == "boolean" then v else f.default
		elseif f.kind == "slider" then
			local n = tonumber(v)
			if n == nil or n ~= n then
				n = f.default
			end
			local step = f.step or 0.01
			n = math.clamp(math.floor((n :: number) / step + 0.5) * step, f.min or 0, f.max or 1)
			out[f.key] = n
		else
			out[f.key] = if type(v) == "string" and table.find(f.choices or {}, v) then v else f.default
		end
	end
	return out
end

-- Apply to Theme (text scale / motion). Safe on client only (no-op on server).
function Settings.apply(values: { [string]: any })
	Theme.reducedMotion = values.reducedMotion == true
	Theme.textScale = TEXT_SCALE[values.textSize] or 1
end

function Settings.new(opts: { values: { [string]: any }?, parent: Instance?, title: string? }?): any
	local Kit = require(script.Parent.Kit)
	local Signal = require(script.Parent.Signal)
	local o = opts or {}
	local T = Theme.get()
	local self: any = setmetatable({}, Settings)
	self.values = Settings.sanitize(o.values)
	self.Changed = Signal.new() -- (key, value, allValues)
	self.Closed = Signal.new()
	self._rows = {}
	self._open = false
	self._conns = {}
	Settings.apply(self.values)

	local screen = o.parent or Kit.screen("WordEngineSettings", 100)
	local z = Theme.Z.modal
	local scrim: TextButton = Kit.new("TextButton", {
		Name = "Scrim", Text = "", AutoButtonColor = false, BackgroundColor3 = Color3.fromHex(Theme.Hex.Ink),
		BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = z, Visible = false,
		Selectable = false, Parent = screen,
	})
	scrim.Activated:Connect(function()
		self:close()
	end)
	self._scrim = scrim

	local root, content = Kit.glass({
		Name = "SettingsPanel", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.new(1, -32, 0, 520), Radius = Theme.Radius.xl, ZIndex = z + 1, Transparency = 0.06,
		Accent = T.Color.Brand,
	})
	Kit.new("UISizeConstraint", { MaxSize = Vector2.new(460, 560), Parent = root })
	root.Visible = false
	root.Parent = screen
	self.root = root
	Kit.padding(Theme.Space.xl, Theme.Space.xl).Parent = content

	-- header
	local header: Frame = Kit.new("Frame", { Name = "Header", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 48),
		ZIndex = z + 3, Parent = content })
	Kit.label({ Text = o.title or "Settings", Size = "headline", Font = T.Font.Heavy, ZIndex = z + 4,
		AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.fromScale(0, 0.5), Parent = header })
	Kit.button({ Name = "Close", Text = "Done", Style = "Primary", Size = UDim2.fromOffset(96, 48),
		AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.fromScale(1, 0.5), ZIndex = z + 4, Parent = header,
		OnActivated = function()
			self:close()
		end })

	local list: ScrollingFrame = Kit.new("ScrollingFrame", {
		Name = "Rows", BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 60),
		Size = UDim2.new(1, 0, 1, -60), CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 3, ScrollBarImageColor3 = T.Color.TextMute, ScrollingDirection = Enum.ScrollingDirection.Y,
		ZIndex = z + 3, Selectable = false, Parent = content,
	}, { Kit.list(Enum.FillDirection.Vertical, Theme.Space.sm) })

	for i, f in Settings.SCHEMA do
		self._rows[f.key] = self:_row(f, i, list, z + 3)
	end

	-- Esc / B closes
	local UIS = game:GetService("UserInputService")
	table.insert(self._conns, UIS.InputBegan:Connect(function(input: InputObject)
		if self._open and (input.KeyCode == Enum.KeyCode.Escape or input.KeyCode == Enum.KeyCode.ButtonB) then
			self:close()
		end
	end))
	return self
end

function Settings:_set(key: string, value: any)
	local Kit = require(script.Parent.Kit)
	self.values[key] = value
	self.values = Settings.sanitize(self.values)
	Settings.apply(self.values)
	if key == "textSize" then
		local Players = game:GetService("Players")
		local pg = Players.LocalPlayer and Players.LocalPlayer:FindFirstChild("PlayerGui")
		if pg then
			Kit.rescaleText(pg)
		end
	end
	local row = self._rows[key]
	if row and row.refresh then
		row.refresh()
	end
	self.Changed:Fire(key, self.values[key], table.clone(self.values))
end

function Settings:_row(f: Field, order: number, parent: Instance, z: number): any
	local Kit = require(script.Parent.Kit)
	local T = Theme.get()
	local row: Frame = Kit.new("Frame", {
		Name = f.key, BackgroundColor3 = T.Color.Raised, BackgroundTransparency = 0.45, BorderSizePixel = 0,
		Size = UDim2.new(1, -4, 0, if f.hint then 64 else 56), LayoutOrder = order, ZIndex = z, Parent = parent,
	}, { Kit.corner(Theme.Radius.md), Kit.stroke(Color3.new(1, 1, 1), 0.92, 1), Kit.padding(0, Theme.Space.lg) })
	local textCol: Frame = Kit.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(0.5, 0, 1, 0), ZIndex = z + 1, Parent = row },
		{ Kit.list(Enum.FillDirection.Vertical, 2, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center) })
	Kit.label({ Text = f.label, Size = "body", Font = T.Font.Semi, ZIndex = z + 1, LayoutOrder = 1, Parent = textCol })
	if f.hint then
		local h = Kit.label({ Text = f.hint, Size = "caption", Font = T.Font.Regular, Color = T.Color.TextMute, ZIndex = z + 1,
			LayoutOrder = 2, Parent = textCol })
		h.TextTruncate = Enum.TextTruncate.AtEnd
	end
	local r: any = { frame = row }
	if f.kind == "toggle" then
		-- switch: 56x32 track inside a 64x48 hit area
		local hit: TextButton = Kit.new("TextButton", { Name = "Toggle", Text = "", AutoButtonColor = false, BackgroundTransparency = 1,
			AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.fromScale(1, 0.5), Size = UDim2.fromOffset(64, 48), ZIndex = z + 1,
			Selectable = true, Parent = row })
		local track: Frame = Kit.new("Frame", { Name = "Track", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
			Size = UDim2.fromOffset(56, 32), BackgroundColor3 = T.Color.Raised, BorderSizePixel = 0, ZIndex = z + 1, Parent = hit },
			{ Kit.corner(UDim.new(0.5, 0)), Kit.stroke(Color3.new(1, 1, 1), 0.85, 1) })
		local knob: Frame = Kit.new("Frame", { Name = "Knob", AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, 3, 0.5, 0),
			Size = UDim2.fromOffset(26, 26), BackgroundColor3 = Color3.new(1, 1, 1), BorderSizePixel = 0, ZIndex = z + 2, Parent = track },
			{ Kit.corner(UDim.new(0.5, 0)) })
		hit.SelectionImageObject = Kit.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) })
		r.refresh = function()
			local on = self.values[f.key] == true
			Kit.tween(track, T.Tween.base, { BackgroundColor3 = if on then T.Color.Brand else T.Color.Raised })
			Kit.tween(knob, T.Tween.spring, { Position = if on then UDim2.new(1, -29, 0.5, 0) else UDim2.new(0, 3, 0.5, 0) })
		end
		hit.Activated:Connect(function()
			self:_set(f.key, not (self.values[f.key] == true))
		end)
	elseif f.kind == "choice" then
		local seg: Frame = Kit.new("Frame", { Name = "Segments", AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.fromScale(1, 0.5),
			Size = UDim2.fromOffset(0, 48), AutomaticSize = Enum.AutomaticSize.X, BackgroundColor3 = T.Color.Glass,
			BackgroundTransparency = 0.2, BorderSizePixel = 0, ZIndex = z + 1, Parent = row },
			{ Kit.corner(Theme.Radius.md), Kit.padding(3, 3), Kit.list(Enum.FillDirection.Horizontal, 3, Enum.HorizontalAlignment.Right, Enum.VerticalAlignment.Center) })
		local buttons = {}
		for i, choice in f.choices or {} do
			local b: TextButton = Kit.new("TextButton", { Name = choice, Text = choice, AutoButtonColor = false,
				FontFace = T.Font.Bold, TextSize = Theme.textSize("label"), TextColor3 = T.Color.TextDim,
				BackgroundColor3 = T.Color.Brand, BackgroundTransparency = 1, BorderSizePixel = 0,
				Size = UDim2.fromOffset(if #choice > 2 then 76 else 48, 42), LayoutOrder = i, ZIndex = z + 2, Selectable = true, Parent = seg },
				{ Kit.corner(Theme.Radius.sm) })
			b:SetAttribute("TypeToken", "label")
			b.Activated:Connect(function()
				Kit.press(b)
				self:_set(f.key, choice)
			end)
			buttons[choice] = b
		end
		r.refresh = function()
			for choice, b in buttons do
				local on = self.values[f.key] == choice
				Kit.tween(b, T.Tween.fast, { BackgroundTransparency = if on then 0 else 1, TextColor3 = if on then Color3.new(1, 1, 1) else T.Color.TextDim })
			end
		end
	else
		-- slider: track + fill + knob; UIDragDetector drives the knob along the track (touch, mouse, gamepad)
		local width = 170
		local holder: TextButton = Kit.new("TextButton", { Name = "Slider", Text = "", AutoButtonColor = false, BackgroundTransparency = 1,
			AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.fromScale(1, 0.5), Size = UDim2.fromOffset(width + 24, 48),
			ZIndex = z + 1, Selectable = true, Parent = row })
		holder.SelectionImageObject = Kit.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) })
		local track: Frame = Kit.new("Frame", { Name = "Track", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
			Size = UDim2.fromOffset(width, 6), BackgroundColor3 = T.Color.Raised, BorderSizePixel = 0, ZIndex = z + 1, Parent = holder },
			{ Kit.corner(UDim.new(0.5, 0)) })
		local fill: Frame = Kit.new("Frame", { Name = "Fill", Size = UDim2.fromScale(0, 1), BackgroundColor3 = Color3.new(1, 1, 1),
			BorderSizePixel = 0, ZIndex = z + 2, Parent = track }, { Kit.corner(UDim.new(0.5, 0)), Kit.gradient(T.Color.Brand2, T.Color.Brand, 0) })
		local knob: Frame = Kit.new("Frame", { Name = "Knob", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0, 0.5),
			Size = UDim2.fromOffset(28, 28), BackgroundColor3 = Color3.new(1, 1, 1), BorderSizePixel = 0, ZIndex = z + 3, Parent = track },
			{ Kit.corner(UDim.new(0.5, 0)), Kit.stroke(T.Color.Brand, 0.2, 2) })
		local min, max = f.min or 0, f.max or 1
		local function setFromFraction(fr: number)
			self:_set(f.key, min + math.clamp(fr, 0, 1) * (max - min))
		end
		local ok = pcall(function()
			local drag: any = Instance.new("UIDragDetector")
			drag.DragStyle = Enum.UIDragDetectorDragStyle.TranslateLine
			drag.DragAxis = Vector2.new(1, 0)
			drag.BoundingUI = track
			drag.ResponseStyle = Enum.UIDragDetectorResponseStyle.Offset
			drag.Parent = knob
			drag.DragContinue:Connect(function()
				local fr = (knob.AbsolutePosition.X + knob.AbsoluteSize.X / 2 - track.AbsolutePosition.X) / track.AbsoluteSize.X
				self.values[f.key] = min + math.clamp(fr, 0, 1) * (max - min)
				fill.Size = UDim2.fromScale(math.clamp(fr, 0, 1), 1)
			end)
			drag.DragEnd:Connect(function()
				local fr = (knob.AbsolutePosition.X + knob.AbsoluteSize.X / 2 - track.AbsolutePosition.X) / track.AbsoluteSize.X
				setFromFraction(fr)
			end)
		end)
		local _ = ok
		-- tap anywhere on the slider to jump
		holder.InputBegan:Connect(function(input: InputObject)
			if input.UserInputType == Enum.UserInputType.MouseButton1 or input.UserInputType == Enum.UserInputType.Touch then
				setFromFraction((input.Position.X - track.AbsolutePosition.X) / track.AbsoluteSize.X)
			end
		end)
		-- gamepad / keyboard: left/right while selected
		local UIS = game:GetService("UserInputService")
		table.insert(self._conns, UIS.InputBegan:Connect(function(input: InputObject)
			local GuiService = game:GetService("GuiService")
			if GuiService.SelectedObject ~= holder then
				return
			end
			local step = f.step or 0.05
			if input.KeyCode == Enum.KeyCode.DPadRight or input.KeyCode == Enum.KeyCode.Right then
				self:_set(f.key, (self.values[f.key] :: number) + step)
			elseif input.KeyCode == Enum.KeyCode.DPadLeft or input.KeyCode == Enum.KeyCode.Left then
				self:_set(f.key, (self.values[f.key] :: number) - step)
			end
		end))
		r.refresh = function()
			local fr = ((self.values[f.key] :: number) - min) / (max - min)
			Kit.tween(fill, T.Tween.fast, { Size = UDim2.fromScale(fr, 1) })
			Kit.tween(knob, T.Tween.fast, { Position = UDim2.fromScale(fr, 0.5) })
		end
	end
	r.refresh()
	return r
end

function Settings:open()
	local Kit = require(script.Parent.Kit)
	local T = Theme.get()
	if self._open then
		return
	end
	self._open = true
	self._scrim.Visible = true
	self.root.Visible = true
	Kit.tween(self._scrim, T.Tween.base, { BackgroundTransparency = 0.45 })
	Kit.pop(self.root, 0.9)
	local GuiService = game:GetService("GuiService")
	local UIS = game:GetService("UserInputService")
	if UIS.GamepadEnabled then
		local first = self.root:FindFirstChild("Close", true)
		GuiService.SelectedObject = first
	end
end

function Settings:close()
	local Kit = require(script.Parent.Kit)
	local T = Theme.get()
	if not self._open then
		return
	end
	self._open = false
	Kit.tween(self._scrim, T.Tween.base, { BackgroundTransparency = 1 })
	local sc = Kit.scaleOf(self.root)
	Kit.tween(sc, T.Tween.fast, { Scale = 0.94 })
	task.delay(Theme.Motion.fast, function()
		if not self._open then
			self.root.Visible = false
			self._scrim.Visible = false
			sc.Scale = 1
		end
	end)
	local GuiService = game:GetService("GuiService")
	if GuiService.SelectedObject and GuiService.SelectedObject:IsDescendantOf(self.root) then
		GuiService.SelectedObject = nil
	end
	self.Closed:Fire(table.clone(self.values))
end

function Settings:toggle()
	if self._open then
		self:close()
	else
		self:open()
	end
end

function Settings:destroy()
	for _, c in self._conns do
		c:Disconnect()
	end
	self.root:Destroy()
	self._scrim:Destroy()
end

return Settings
