--!strict
-- Toast: short stacked notifications (top centre, under the Roblox top bar, safe-area aware).
--
--   UI.Toast.show("New word discovered: TORNADO", { kind = "word", element = "Wind", title = "WORD BOOK" })
--   UI.Toast.show("Not enough coins", { kind = "error" })
-- kinds: "info" | "success" | "warn" | "error" | "word". Max Config.UI.ToastMax visible; oldest slides out.

local Theme = require(script.Parent.Theme)
local Kit = require(script.Parent.Kit)

local Toast = {}

export type Options = {
	kind: string?,
	title: string?,
	element: string?,
	accent: Color3?,
	duration: number?,
}

local holder: Frame? = nil
local live: { Frame } = {}
local order = 0

local function uiCfg(): any
	local ok, c = pcall(function()
		return (require(script.Parent.Parent.Config) :: any).UI
	end)
	return if ok and c then c else {}
end

local function getHolder(): Frame
	if holder and holder.Parent then
		return holder
	end
	local screen = Kit.screen("WordEngineToasts", 60)
	holder = Kit.new("Frame", {
		Name = "Stack",
		BackgroundTransparency = 1,
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.new(0.5, 0, 0, 12),
		Size = UDim2.new(1, -32, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		ZIndex = Theme.Z.toast,
		Parent = screen,
	}, {
		Kit.new("UISizeConstraint", { MaxSize = Vector2.new(460, math.huge) }),
		Kit.list(Enum.FillDirection.Vertical, Theme.Space.sm, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Top),
	})
	return holder :: Frame
end

local function accentFor(o: Options): Color3
	local T = Theme.get()
	if o.accent then
		return o.accent
	end
	if o.element then
		return (Theme.element(o.element))
	end
	local k = o.kind or "info"
	if k == "success" then
		return T.Color.Success
	elseif k == "warn" then
		return T.Color.Warn
	elseif k == "error" then
		return T.Color.Danger
	end
	return T.Color.Brand
end

local function dismiss(f: Frame)
	local i = table.find(live, f)
	if i then
		table.remove(live, i)
	end
	local T = Theme.get()
	local inner = f:FindFirstChild("Inner") :: Frame?
	if inner and not Theme.reducedMotion then
		Kit.tween(inner, T.Tween.base, { Position = UDim2.fromOffset(0, -18) })
		for _, d in inner:GetDescendants() do
			if d:IsA("TextLabel") then
				Kit.tween(d, T.Tween.base, { TextTransparency = 1 })
			elseif d:IsA("Frame") and d.BackgroundTransparency < 1 then
				Kit.tween(d, T.Tween.base, { BackgroundTransparency = 1 })
			elseif d:IsA("UIStroke") then
				Kit.tween(d, T.Tween.base, { Transparency = 1 })
			end
		end
		task.delay(Theme.Motion.base, function()
			f:Destroy()
		end)
	else
		f:Destroy()
	end
end

function Toast.show(text: string, opts: Options?): Frame
	local o: Options = opts or {}
	local T = Theme.get()
	local cfg = uiCfg()
	local accent = accentFor(o)
	order += 1
	local slotFrame: Frame = Kit.new("Frame", {
		Name = "Toast",
		BackgroundTransparency = 1,
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		LayoutOrder = order,
		ZIndex = Theme.Z.toast,
	})
	local inner: Frame = Kit.new("Frame", {
		Name = "Inner",
		BackgroundTransparency = 1,
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		ZIndex = Theme.Z.toast,
		Parent = slotFrame,
	})
	local root, content = Kit.glass({
		Name = "Card", Size = UDim2.new(1, 0, 0, 0), AutomaticSize = Enum.AutomaticSize.Y,
		Radius = Theme.Radius.lg, ZIndex = Theme.Z.toast, Accent = accent, Parent = inner,
	})
	local _ = root
	Kit.padding(Theme.Space.md, Theme.Space.lg).Parent = content
	Kit.list(Enum.FillDirection.Horizontal, Theme.Space.md, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center).Parent = content
	-- accent bar
	Kit.new("Frame", {
		Name = "Bar", BackgroundColor3 = Color3.new(1, 1, 1), BorderSizePixel = 0, Size = UDim2.fromOffset(4, 34),
		LayoutOrder = 1, ZIndex = Theme.Z.toast + 3, Parent = content,
	}, { Kit.corner(2), Kit.gradient(accent, accent:Lerp(Color3.new(0, 0, 0), 0.4), 90) })
	local col: Frame = Kit.new("Frame", {
		Name = "Text", BackgroundTransparency = 1, AutomaticSize = Enum.AutomaticSize.XY, LayoutOrder = 2,
		ZIndex = Theme.Z.toast + 3, Parent = content,
	}, { Kit.list(Enum.FillDirection.Vertical, 2) })
	if o.title then
		Kit.label({ Name = "Title", Text = string.upper(o.title), Size = "caption", Font = T.Font.Heavy, Color = accent,
			ZIndex = Theme.Z.toast + 3, LayoutOrder = 1, Parent = col })
	end
	local body = Kit.label({ Name = "Body", Text = text, Size = "body", Font = T.Font.Semi, Color = T.Color.Text,
		Wrapped = true, ZIndex = Theme.Z.toast + 3, LayoutOrder = 2, Parent = col })
	Kit.new("UISizeConstraint", { MaxSize = Vector2.new(380, math.huge), Parent = body })

	slotFrame.Parent = getHolder()
	table.insert(live, slotFrame)
	while #live > (cfg.ToastMax or 3) do
		dismiss(live[1])
	end
	if not Theme.reducedMotion then
		inner.Position = UDim2.fromOffset(0, -22)
		Kit.tween(inner, T.Tween.spring, { Position = UDim2.fromOffset(0, 0) })
		Kit.pop(inner, 0.94)
	end
	task.delay(o.duration or cfg.ToastSeconds or 3, function()
		if slotFrame.Parent then
			dismiss(slotFrame)
		end
	end)
	return slotFrame
end

function Toast.clear()
	for _, f in table.clone(live) do
		dismiss(f)
	end
end

return Toast
