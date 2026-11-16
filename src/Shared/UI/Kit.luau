--!strict
-- Kit: UI primitives every WordEngine widget is built from. Roblox-only; touches no API at require time.
--
--   Kit.new(class, props, children)       instance factory (props incl. [Kit.Children] / events via "On_<Event>")
--   Kit.screen(name, order)               ScreenGui: safe-area aware (CoreUISafeInsets), no reset on spawn
--   Kit.glass(props)                      dark translucent panel: gradient + 1px stroke + rounded + soft shadow
--   Kit.label(props) / Kit.button(props)  typographic label / 48px+ button with hover, press and focus states
--   Kit.chip(props)                       pill chip (autocomplete, did-you-mean, tags)
--   Kit.tween(inst, info, goal)           motion helper; respects Theme.reducedMotion
--   Kit.press(inst) / Kit.shake(inst)     micro-interactions

local Theme = require(script.Parent.Theme)

local Kit = {}

local TweenService: TweenService? = nil
local function ts(): TweenService
	if not TweenService then
		TweenService = game:GetService("TweenService")
	end
	return TweenService :: TweenService
end

function Kit.new(className: string, props: { [string]: any }?, children: { Instance }?): any
	local inst: any = Instance.new(className)
	local parent = nil
	for k, v in props or {} do
		if k == "Parent" then
			parent = v
		elseif type(k) == "string" and string.sub(k, 1, 3) == "On_" then
			inst[string.sub(k, 4)]:Connect(v)
		else
			inst[k] = v
		end
	end
	for _, c in children or {} do
		c.Parent = inst
	end
	if parent then
		inst.Parent = parent
	end
	return inst
end

function Kit.corner(radius: number | UDim): UICorner
	return Kit.new("UICorner", { CornerRadius = if typeof(radius) == "UDim" then radius else UDim.new(0, radius :: number) })
end

function Kit.stroke(color: Color3?, transparency: number?, thickness: number?): UIStroke
	return Kit.new("UIStroke", {
		Color = color or Color3.new(1, 1, 1),
		Transparency = transparency or Theme.StrokeTransparency,
		Thickness = thickness or 1,
		ApplyStrokeMode = Enum.ApplyStrokeMode.Border,
		LineJoinMode = Enum.LineJoinMode.Round,
	})
end

function Kit.padding(all: number, horizontal: number?): UIPadding
	local h = horizontal or all
	return Kit.new("UIPadding", {
		PaddingTop = UDim.new(0, all), PaddingBottom = UDim.new(0, all),
		PaddingLeft = UDim.new(0, h), PaddingRight = UDim.new(0, h),
	})
end

function Kit.list(direction: Enum.FillDirection, gap: number, hAlign: Enum.HorizontalAlignment?, vAlign: Enum.VerticalAlignment?): UIListLayout
	return Kit.new("UIListLayout", {
		FillDirection = direction,
		Padding = UDim.new(0, gap),
		HorizontalAlignment = hAlign or Enum.HorizontalAlignment.Left,
		VerticalAlignment = vAlign or Enum.VerticalAlignment.Top,
		SortOrder = Enum.SortOrder.LayoutOrder,
	})
end

function Kit.gradient(c0: Color3, c1: Color3, rotation: number?): UIGradient
	return Kit.new("UIGradient", { Color = ColorSequence.new(c0, c1), Rotation = rotation or 90 })
end

function Kit.tween(inst: Instance, info: TweenInfo?, goal: { [string]: any }): Tween?
	if Theme.reducedMotion then
		for k, v in goal do
			(inst :: any)[k] = v
		end
		return nil
	end
	local tw = ts():Create(inst, info or Theme.get().Tween.base, goal)
	tw:Play()
	return tw
end

-- A UIScale child we can animate for punchy scale effects without disturbing layout.
function Kit.scaleOf(inst: Instance): UIScale
	local s = inst:FindFirstChild("KitScale") :: UIScale?
	if not s then
		s = Kit.new("UIScale", { Name = "KitScale", Scale = 1, Parent = inst })
	end
	return s :: UIScale
end

function Kit.press(inst: Instance)
	local s = Kit.scaleOf(inst)
	local T = Theme.get()
	if Theme.reducedMotion then
		return
	end
	s.Scale = 0.92
	Kit.tween(s, T.Tween.spring, { Scale = 1 })
end

function Kit.pop(inst: Instance, from: number?)
	local s = Kit.scaleOf(inst)
	if Theme.reducedMotion then
		s.Scale = 1
		return
	end
	s.Scale = from or 0.6
	Kit.tween(s, Theme.get().Tween.spring, { Scale = 1 })
end

function Kit.shake(inst: GuiObject)
	if Theme.reducedMotion then
		return
	end
	if inst.Parent and inst.Parent:FindFirstChildWhichIsA("UIGridStyleLayout") then
		-- laid-out children ignore Position: wobble rotation instead
		task.spawn(function()
			for _, r in { 6, -5, 4, -2, 0 } do
				inst.Rotation = r
				task.wait(0.035)
			end
		end)
		return
	end
	local base = inst.Position
	task.spawn(function()
		for i, dx in { 10, -8, 6, -4, 2, 0 } do
			inst.Position = base + UDim2.fromOffset(dx, 0)
			task.wait(0.03 + i * 0.002)
		end
		inst.Position = base
	end)
end

-- Safe-area-aware ScreenGui: content stays clear of notches and Roblox's top bar on every device.
-- https://create.roblox.com/docs/reference/engine/classes/ScreenGui (ScreenInsets)
function Kit.screen(name: string, displayOrder: number?, parent: Instance?): ScreenGui
	local playerGui = parent
	if not playerGui then
		local Players = game:GetService("Players")
		local lp = Players.LocalPlayer
		playerGui = lp and lp:WaitForChild("PlayerGui")
	end
	local existing = playerGui and playerGui:FindFirstChild(name)
	if existing and existing:IsA("ScreenGui") then
		return existing
	end
	return Kit.new("ScreenGui", {
		Name = name,
		ResetOnSpawn = false,
		IgnoreGuiInset = false,
		ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling,
		DisplayOrder = displayOrder or 10,
		Parent = playerGui,
	})
end

-- Soft shadow from three stacked rounded frames behind `host` (same parent, lower ZIndex). Cheaper than
-- an image and crisp at every resolution. Returns the holder so callers can fade it with the panel.
function Kit.shadow(host: GuiObject, radius: number, depth: number?): Frame
	local d = depth or 1
	local holder: Frame = Kit.new("Frame", {
		Name = "Shadow",
		BackgroundTransparency = 1,
		Size = UDim2.fromScale(1, 1),
		ZIndex = host.ZIndex - 1,
	})
	for i = 1, 3 do
		local grow = (2 + i * 4) * d
		Kit.new("Frame", {
			Name = "L" .. i,
			BackgroundColor3 = Color3.fromHex(Theme.Hex.Ink),
			BackgroundTransparency = 0.72 + i * 0.07,
			BorderSizePixel = 0,
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.new(0.5, 0, 0.5, 3 * d + i),
			Size = UDim2.new(1, grow, 1, grow),
			ZIndex = host.ZIndex - 1,
			Parent = holder,
		}, { Kit.corner(radius + grow / 2) })
	end
	return holder
end

export type GlassProps = {
	Name: string?,
	Size: UDim2?,
	Position: UDim2?,
	AnchorPoint: Vector2?,
	ZIndex: number?,
	Radius: number?,
	Accent: Color3?, -- tints the top edge highlight
	Shadow: boolean?,
	Transparency: number?,
	Parent: Instance?,
	AutomaticSize: Enum.AutomaticSize?,
}

-- Glass panel. Returns (root, content): root carries shadow + panel; put children in content.
function Kit.glass(p: GlassProps): (Frame, Frame)
	local T = Theme.get()
	local radius = p.Radius or Theme.Radius.lg
	local z = p.ZIndex or Theme.Z.panel
	local root: Frame = Kit.new("Frame", {
		Name = p.Name or "Glass",
		BackgroundTransparency = 1,
		Size = p.Size or UDim2.fromOffset(320, 200),
		Position = p.Position or UDim2.new(),
		AnchorPoint = p.AnchorPoint or Vector2.zero,
		AutomaticSize = p.AutomaticSize or Enum.AutomaticSize.None,
		ZIndex = z,
	})
	local auto = p.AutomaticSize ~= nil and p.AutomaticSize ~= Enum.AutomaticSize.None
	local panel: Frame = Kit.new("Frame", {
		Name = "Panel",
		BackgroundColor3 = Color3.new(1, 1, 1), -- coloured by the gradient
		BackgroundTransparency = p.Transparency or Theme.GlassTransparency,
		BorderSizePixel = 0,
		-- auto-sized panels must not use scale height (circular with the auto-sized parent)
		Size = if auto then UDim2.new(1, 0, 0, 0) else UDim2.fromScale(1, 1),
		AutomaticSize = p.AutomaticSize or Enum.AutomaticSize.None,
		ZIndex = z,
		ClipsDescendants = false,
		Parent = root,
	}, {
		Kit.corner(radius),
		Kit.gradient(T.Color.GlassHi, T.Color.GlassLo, 90),
		Kit.stroke(Color3.new(1, 1, 1), Theme.StrokeTransparency, 1),
	})
	-- top sheen: a thin highlight line inset 1px from the top edge (inset avoids overlapping the stroke)
	local accent = p.Accent or Color3.new(1, 1, 1)
	Kit.new("Frame", {
		Name = "Sheen",
		BackgroundColor3 = accent,
		BackgroundTransparency = if p.Accent then 0.35 else 0.88,
		BorderSizePixel = 0,
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.new(0.5, 0, 0, 1),
		Size = UDim2.new(1, -radius * 2, 0, 1),
		ZIndex = z + 1,
		Parent = panel,
	}, {
		Kit.new("UIGradient", {
			Transparency = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 1),
				NumberSequenceKeypoint.new(0.5, 0),
				NumberSequenceKeypoint.new(1, 1),
			}),
		}),
	})
	if p.Shadow ~= false then
		local sh = Kit.shadow(panel, radius, 1)
		sh.ZIndex = z - 1
		sh.Parent = root
	end
	local content: Frame = Kit.new("Frame", {
		Name = "Content",
		BackgroundTransparency = 1,
		Size = if auto then UDim2.new(1, 0, 0, 0) else UDim2.fromScale(1, 1),
		AutomaticSize = p.AutomaticSize or Enum.AutomaticSize.None,
		ZIndex = z + 2,
		Parent = panel,
	})
	if p.Parent then
		root.Parent = p.Parent
	end
	return root, content
end

export type LabelProps = {
	Text: string,
	Size: string?, -- TypeScale token
	Font: Font?,
	Color: Color3?,
	Transparency: number?,
	XAlign: Enum.TextXAlignment?,
	YAlign: Enum.TextYAlignment?,
	Wrapped: boolean?,
	RichText: boolean?,
	AutomaticSize: Enum.AutomaticSize?,
	Name: string?,
	ZIndex: number?,
	Parent: Instance?,
	LayoutOrder: number?,
	FrameSize: UDim2?,
	Position: UDim2?,
	AnchorPoint: Vector2?,
}

function Kit.label(p: LabelProps): TextLabel
	local T = Theme.get()
	local sizeToken = p.Size or "body"
	local l: TextLabel = Kit.new("TextLabel", {
		Name = p.Name or "Label",
		BackgroundTransparency = 1,
		Text = p.Text,
		FontFace = p.Font or T.Font.Medium,
		TextSize = Theme.textSize(sizeToken),
		TextColor3 = p.Color or T.Color.Text,
		TextTransparency = p.Transparency or 0,
		TextXAlignment = p.XAlign or Enum.TextXAlignment.Left,
		TextYAlignment = p.YAlign or Enum.TextYAlignment.Center,
		TextWrapped = p.Wrapped == true,
		RichText = p.RichText == true,
		AutomaticSize = p.AutomaticSize or Enum.AutomaticSize.XY,
		Size = p.FrameSize or UDim2.new(),
		Position = p.Position or UDim2.new(),
		AnchorPoint = p.AnchorPoint or Vector2.zero,
		ZIndex = p.ZIndex or Theme.Z.panel + 3,
		LayoutOrder = p.LayoutOrder or 0,
		Parent = p.Parent,
	})
	l:SetAttribute("TypeToken", sizeToken)
	return l
end

export type ButtonStyle = "Primary" | "Secondary" | "Ghost" | "Danger"
export type ButtonProps = {
	Text: string,
	Style: ButtonStyle?,
	Accent: Color3?,
	Size: UDim2?,
	Position: UDim2?,
	AnchorPoint: Vector2?,
	Name: string?,
	ZIndex: number?,
	LayoutOrder: number?,
	Parent: Instance?,
	OnActivated: (() -> ())?,
	Hint: string?, -- keyboard/controller hint shown at the right ("Enter", "X")
}

-- Button: 48px+ hit area, hover lift, press squash, gamepad selection ring.
function Kit.button(p: ButtonProps): TextButton
	local T = Theme.get()
	local style = p.Style or "Secondary"
	local accent = p.Accent or T.Color.Brand
	local z = p.ZIndex or Theme.Z.panel + 4
	local bg, bg2, textColor, strokeT
	if style == "Primary" then
		bg, bg2, textColor, strokeT = accent, accent:Lerp(Color3.new(0, 0, 0), 0.35), Color3.new(1, 1, 1), 0.65
	elseif style == "Danger" then
		bg, bg2, textColor, strokeT = T.Color.Danger, T.Color.Danger:Lerp(Color3.new(0, 0, 0), 0.35), Color3.new(1, 1, 1), 0.65
	elseif style == "Ghost" then
		bg, bg2, textColor, strokeT = T.Color.Raised, T.Color.Raised, T.Color.TextDim, 0.88
	else
		bg, bg2, textColor, strokeT = T.Color.RaisedHi, T.Color.Raised, T.Color.Text, 0.82
	end
	local btn: TextButton = Kit.new("TextButton", {
		Name = p.Name or "Button",
		AutoButtonColor = false,
		Text = "",
		BackgroundColor3 = Color3.new(1, 1, 1),
		BackgroundTransparency = if style == "Ghost" then 0.7 else 0,
		BorderSizePixel = 0,
		Size = p.Size or UDim2.fromOffset(160, Theme.MinTouch),
		Position = p.Position or UDim2.new(),
		AnchorPoint = p.AnchorPoint or Vector2.zero,
		ZIndex = z,
		LayoutOrder = p.LayoutOrder or 0,
		Selectable = true,
		SelectionImageObject = nil,
	}, {
		Kit.corner(Theme.Radius.md),
		Kit.gradient(bg, bg2, 90),
		Kit.stroke(Color3.new(1, 1, 1), strokeT, 1),
		Kit.new("UISizeConstraint", { MinSize = Vector2.new(Theme.MinTouch, Theme.MinTouch) }),
	})
	local text = Kit.label({
		Name = "Text",
		Text = p.Text,
		Size = "label",
		Font = T.Font.Bold,
		Color = textColor,
		XAlign = Enum.TextXAlignment.Center,
		AutomaticSize = Enum.AutomaticSize.None,
		FrameSize = UDim2.fromScale(1, 1),
		ZIndex = z + 1,
		Parent = btn,
	})
	text.TextTruncate = Enum.TextTruncate.AtEnd
	if p.Hint then
		local hint = Kit.label({
			Name = "Hint",
			Text = p.Hint,
			Size = "caption",
			Font = T.Font.Mono,
			Color = textColor,
			Transparency = 0.45,
			XAlign = Enum.TextXAlignment.Right,
			AutomaticSize = Enum.AutomaticSize.None,
			FrameSize = UDim2.new(1, -12, 1, 0),
			ZIndex = z + 1,
			Parent = btn,
		})
		local _ = hint
	end
	-- selection ring (gamepad / keyboard focus) drawn as a second stroke frame, inset to avoid overlap
	local ring: Frame = Kit.new("Frame", {
		Name = "FocusRing",
		BackgroundTransparency = 1,
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.new(1, 6, 1, 6),
		ZIndex = z,
		Visible = false,
		Parent = btn,
	}, { Kit.corner(Theme.Radius.md + 3), Kit.stroke(accent, 0, 2) })
	btn.SelectionImageObject = Kit.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) })
	btn.SelectionGained:Connect(function()
		ring.Visible = true
	end)
	btn.SelectionLost:Connect(function()
		ring.Visible = false
	end)
	local stroke = btn:FindFirstChildOfClass("UIStroke") :: UIStroke
	btn.MouseEnter:Connect(function()
		Kit.tween(stroke, T.Tween.fast, { Transparency = math.max(strokeT - 0.25, 0.3) })
		Kit.tween(Kit.scaleOf(btn), T.Tween.fast, { Scale = 1.03 })
	end)
	btn.MouseLeave:Connect(function()
		Kit.tween(stroke, T.Tween.fast, { Transparency = strokeT })
		Kit.tween(Kit.scaleOf(btn), T.Tween.fast, { Scale = 1 })
	end)
	btn.Activated:Connect(function()
		Kit.press(btn)
		if p.OnActivated then
			p.OnActivated()
		end
	end)
	if p.Parent then
		btn.Parent = p.Parent
	end
	return btn
end

export type ChipProps = {
	Text: string,
	Accent: Color3?,
	Strong: boolean?, -- filled (primary) vs outlined
	Prefix: string?, -- dim prefix text, e.g. "Did you mean"
	Name: string?,
	ZIndex: number?,
	LayoutOrder: number?,
	Parent: Instance?,
	OnActivated: (() -> ())?,
}

-- Pill chip. Auto-width, 48px tall hit area (visual pill is 40px, centred, so rows stay tight).
function Kit.chip(p: ChipProps): TextButton
	local T = Theme.get()
	local z = p.ZIndex or Theme.Z.chips
	local accent = p.Accent or T.Color.Brand
	local hit: TextButton = Kit.new("TextButton", {
		Name = p.Name or "Chip",
		AutoButtonColor = false,
		Text = "",
		BackgroundTransparency = 1,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, Theme.MinTouch),
		ZIndex = z,
		LayoutOrder = p.LayoutOrder or 0,
		Selectable = true,
	})
	local pill: Frame = Kit.new("Frame", {
		Name = "Pill",
		BackgroundColor3 = Color3.new(1, 1, 1),
		BackgroundTransparency = if p.Strong then 0 else 0.1,
		BorderSizePixel = 0,
		AutomaticSize = Enum.AutomaticSize.X,
		AnchorPoint = Vector2.new(0, 0.5),
		Position = UDim2.fromScale(0, 0.5),
		Size = UDim2.fromOffset(0, 40),
		ZIndex = z,
		Parent = hit,
	}, {
		Kit.corner(UDim.new(0.5, 0)),
		if p.Strong
			then Kit.gradient(accent, accent:Lerp(Color3.new(0, 0, 0), 0.3), 90)
			else Kit.gradient(T.Color.RaisedHi, T.Color.Raised, 90),
		Kit.stroke(accent, if p.Strong then 0.5 else 0.45, 1),
		Kit.padding(0, 16),
		Kit.list(Enum.FillDirection.Horizontal, 6, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center),
		Kit.new("UISizeConstraint", { MinSize = Vector2.new(Theme.MinTouch, 0) }),
	})
	if p.Prefix then
		Kit.label({ Name = "Prefix", Text = p.Prefix, Size = "label", Font = T.Font.Medium,
			Color = if p.Strong then Color3.new(1, 1, 1) else T.Color.TextDim, Transparency = if p.Strong then 0.25 else 0,
			ZIndex = z + 1, LayoutOrder = 1, Parent = pill })
	end
	Kit.label({ Name = "Text", Text = p.Text, Size = "label", Font = T.Font.Bold,
		Color = if p.Strong then Color3.new(1, 1, 1) else T.Color.Text, ZIndex = z + 1, LayoutOrder = 2, Parent = pill })
	hit.SelectionImageObject = Kit.new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) })
	local stroke = pill:FindFirstChildOfClass("UIStroke") :: UIStroke
	hit.SelectionGained:Connect(function()
		stroke.Thickness = 2
		stroke.Transparency = 0
	end)
	hit.SelectionLost:Connect(function()
		stroke.Thickness = 1
		stroke.Transparency = if p.Strong then 0.5 else 0.45
	end)
	hit.MouseEnter:Connect(function()
		Kit.tween(Kit.scaleOf(pill), T.Tween.fast, { Scale = 1.04 })
	end)
	hit.MouseLeave:Connect(function()
		Kit.tween(Kit.scaleOf(pill), T.Tween.fast, { Scale = 1 })
	end)
	hit.Activated:Connect(function()
		Kit.press(pill)
		if p.OnActivated then
			p.OnActivated()
		end
	end)
	if p.Parent then
		hit.Parent = p.Parent
	end
	return hit
end

-- Apply the current Theme.textScale to every Kit label under root (Settings "Text size").
function Kit.rescaleText(root: Instance)
	for _, d in root:GetDescendants() do
		if (d:IsA("TextLabel") or d:IsA("TextButton") or d:IsA("TextBox")) and d:GetAttribute("TypeToken") then
			(d :: any).TextSize = Theme.textSize(d:GetAttribute("TypeToken") :: string)
		end
	end
end

return Kit
