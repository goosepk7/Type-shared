--!strict
-- WordReveal: the typed word punches onto the screen in its element colours with its flavour text.
--
--   UI.WordReveal.play(result)                       -- centre-screen banner, auto-dismiss
--   UI.WordReveal.play(result, { parent = frame, hold = 3, compact = true })
--
-- Sequence (~2.2s): backdrop light streak sweeps in -> word slams from 1.7x with a slight tilt (Back easing)
-- -> shine sweeps across the letters -> element / mood / material tags fade up -> flavour text types out
-- -> everything lifts and fades. Respects Theme.reducedMotion (cross-fade only). Only shows `canonical`
-- (never raw input), so it is safe to show to every player.

local Theme = require(script.Parent.Theme)
local Kit = require(script.Parent.Kit)

local WordReveal = {}

export type Options = {
	parent: Instance?,
	hold: number?, -- seconds fully visible (default Config.UI.RevealSeconds)
	compact: boolean?, -- smaller, for side-by-side previews
	position: UDim2?,
	caster: string?, -- optional "BRUCE CASTS" line (pass an already-filtered display name)
}

local current: Frame? = nil

local function uiCfg(): any
	local ok, c = pcall(function()
		return (require(script.Parent.Parent.Config) :: any).UI
	end)
	return if ok and c then c else {}
end

local function tagPill(text: string, colour: Color3, z: number, order: number, parent: Instance)
	local T = Theme.get()
	local pill: Frame = Kit.new("Frame", {
		Name = "Tag",
		BackgroundColor3 = colour,
		BackgroundTransparency = 0.78,
		BorderSizePixel = 0,
		AutomaticSize = Enum.AutomaticSize.XY,
		LayoutOrder = order,
		ZIndex = z,
		Parent = parent,
	}, { Kit.corner(UDim.new(0.5, 0)), Kit.stroke(colour, 0.35, 1), Kit.padding(4, 12) })
	Kit.label({ Text = string.upper(text), Size = "caption", Font = T.Font.Heavy, Color = colour:Lerp(Color3.new(1, 1, 1), 0.35),
		ZIndex = z + 1, Parent = pill })
	return pill
end

function WordReveal.play(result: any, opts: Options?): Frame?
	if type(result) ~= "table" then
		return nil
	end
	local o: Options = opts or {}
	local T = Theme.get()
	local cfg = uiCfg()
	local hold = o.hold or cfg.RevealSeconds or 2.2
	local compact = o.compact == true
	local reduced = Theme.reducedMotion
	local c0, c1 = Theme.element(result.element, result.visual and result.visual.primaryColour)
	local s0 = c0
	if result.secondaryElement and result.secondaryElement ~= "None" then
		s0 = (Theme.element(result.secondaryElement))
	end
	local z = Theme.Z.reveal

	local parent = o.parent
	if not parent then
		parent = Kit.screen("WordEngineReveal", 80)
		if current and current.Parent then
			current:Destroy() -- one banner at a time on the main screen
		end
	end

	local root: Frame = Kit.new("Frame", {
		Name = "WordReveal",
		BackgroundTransparency = 1,
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = o.position or UDim2.fromScale(0.5, if compact then 0.5 else 0.36),
		Size = UDim2.new(1, 0, 0, if compact then 150 else 230),
		ZIndex = z,
	})

	-- light streak backdrop: a wide soft band in the element colours, faded at both ends
	local streak: Frame = Kit.new("Frame", {
		Name = "Streak",
		BackgroundColor3 = Color3.new(1, 1, 1),
		BorderSizePixel = 0,
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.42),
		Size = UDim2.new(if reduced then 1 else 0, 0, 0, if compact then 70 else 110),
		BackgroundTransparency = 0.55,
		ZIndex = z,
		Parent = root,
	}, {
		Kit.new("UIGradient", {
			Color = ColorSequence.new({
				ColorSequenceKeypoint.new(0, c1),
				ColorSequenceKeypoint.new(0.5, c0),
				ColorSequenceKeypoint.new(1, if s0 ~= c0 then s0 else c1),
			}),
			Transparency = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 1),
				NumberSequenceKeypoint.new(0.2, 0.55),
				NumberSequenceKeypoint.new(0.5, 0.35),
				NumberSequenceKeypoint.new(0.8, 0.55),
				NumberSequenceKeypoint.new(1, 1),
			}),
		}),
	})
	-- thin bright rules above and below the streak (offset 2px from its edges: no overlapping strokes)
	for _, y in { -1, 1 } do
		Kit.new("Frame", {
			Name = "Rule",
			BackgroundColor3 = c0:Lerp(Color3.new(1, 1, 1), 0.5),
			BorderSizePixel = 0,
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.new(0.5, 0, 0.5, y * ((if compact then 35 else 55) + 2)),
			Size = UDim2.new(0.9, 0, 0, 1),
			BackgroundTransparency = 0.2,
			ZIndex = z,
			Parent = streak,
		}, {
			Kit.new("UIGradient", { Transparency = NumberSequence.new({
				NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0), NumberSequenceKeypoint.new(1, 1) }) }),
		})
	end

	local stack: Frame = Kit.new("Frame", {
		Name = "Stack",
		BackgroundTransparency = 1,
		Size = UDim2.fromScale(1, 1),
		ZIndex = z + 2,
		Parent = root,
	}, { Kit.list(Enum.FillDirection.Vertical, if compact then 4 else 8, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center) })

	if o.caster then
		Kit.label({ Name = "Caster", Text = string.upper(o.caster) .. " CASTS", Size = "caption", Font = T.Font.Heavy,
			Color = T.Color.TextDim, ZIndex = z + 3, LayoutOrder = 0, Parent = stack })
	end

	-- the word
	local wordText = string.upper(result.canonical or result.id or "?")
	local word = Kit.label({
		Name = "Word",
		Text = wordText,
		Size = if compact then "headline" else "display",
		Font = T.Font.Display,
		Color = Color3.new(1, 1, 1),
		XAlign = Enum.TextXAlignment.Center,
		ZIndex = z + 4,
		LayoutOrder = 1,
		Parent = stack,
	})
	-- long phrases shrink to fit the screen width
	word.AutomaticSize = Enum.AutomaticSize.None
	word.Size = UDim2.new(0.94, 0, 0, if compact then 40 else 64)
	word.TextScaled = true
	Kit.new("UITextSizeConstraint", { MaxTextSize = Theme.textSize(if compact then "headline" else "display") + 10, MinTextSize = 18, Parent = word })
	local wordGrad: UIGradient = Kit.new("UIGradient", {
		Color = ColorSequence.new({
			ColorSequenceKeypoint.new(0, c0:Lerp(Color3.new(1, 1, 1), 0.55)),
			ColorSequenceKeypoint.new(0.45, c0),
			ColorSequenceKeypoint.new(1, if s0 ~= c0 then s0 else c1),
		}),
		Rotation = 90,
		Parent = word,
	})
	local _ = wordGrad
	-- text outline for legibility over any scene
	Kit.new("UIStroke", { Color = c1:Lerp(Color3.new(0, 0, 0), 0.55), Thickness = if compact then 1.5 else 2.5,
		Transparency = 0.1, ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual, LineJoinMode = Enum.LineJoinMode.Round, Parent = word })
	-- shine: a white copy of the word masked by a moving narrow gradient band
	local shine = word:Clone()
	shine.Name = "Shine"
	for _, ch in shine:GetChildren() do
		if not ch:IsA("UITextSizeConstraint") then
			ch:Destroy()
		end
	end
	shine.AnchorPoint = Vector2.new(0.5, 0.5)
	shine.Position = UDim2.fromScale(0.5, 0.5)
	shine.Size = UDim2.fromScale(1, 1)
	shine.TextColor3 = Color3.new(1, 1, 1)
	shine.ZIndex = z + 5
	shine.Parent = word
	local shineGrad: UIGradient = Kit.new("UIGradient", {
		Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.42, 1), NumberSequenceKeypoint.new(0.5, 0.15),
			NumberSequenceKeypoint.new(0.58, 1), NumberSequenceKeypoint.new(1, 1) }),
		Rotation = 20,
		Offset = Vector2.new(-1, 0),
		Parent = shine,
	})

	-- tags row: element(s), mood, material, size, count
	local tags: Frame = Kit.new("Frame", {
		Name = "Tags", BackgroundTransparency = 1, AutomaticSize = Enum.AutomaticSize.XY, LayoutOrder = 2,
		ZIndex = z + 3, Parent = stack,
	}, { Kit.list(Enum.FillDirection.Horizontal, 6, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center) })
	local order = 0
	local function tag(text: string?, colour: Color3)
		if text and text ~= "" and text ~= "None" and text ~= "Neutral" then
			order += 1
			tagPill(text, colour, z + 3, order, tags)
		end
	end
	tag(result.element, c0)
	if result.secondaryElement and result.secondaryElement ~= "None" then
		tag(result.secondaryElement, s0)
	end
	tag(result.mood, T.Color.Warn)
	tag(result.material, T.Color.Brand2)
	if not compact then
		tag(result.size, T.Color.TextDim)
		tag(result.category, T.Color.TextDim)
	end
	if (result.count or 1) > 1 then
		tag("x" .. tostring(result.count), T.Color.Success)
	end

	-- flavour line (types out)
	local flavour = Kit.label({
		Name = "Flavour",
		Text = result.flavourText or "",
		Size = if compact then "label" else "body",
		Font = T.Font.Medium,
		Color = T.Color.TextDim,
		XAlign = Enum.TextXAlignment.Center,
		Wrapped = true,
		ZIndex = z + 3,
		LayoutOrder = 3,
		Parent = stack,
	})
	Kit.new("UISizeConstraint", { MaxSize = Vector2.new(if compact then 300 else 520, math.huge), Parent = flavour })
	flavour.MaxVisibleGraphemes = if reduced then -1 else 0

	root.Parent = parent
	if not o.parent then
		current = root
	end

	-- animate
	local sc = Kit.scaleOf(word)
	if reduced then
		root.Visible = true
	else
		Kit.tween(streak, TweenInfo.new(0.32, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), { Size = UDim2.new(1, 0, 0, streak.Size.Y.Offset) })
		sc.Scale = 1.75
		word.Rotation = -4
		word.TextTransparency = 1
		Kit.tween(sc, T.Tween.punch, { Scale = 1 })
		Kit.tween(word, T.Tween.punch, { Rotation = 0, TextTransparency = 0 })
		local tagScale = Kit.scaleOf(tags)
		tagScale.Scale = 0.6
		task.delay(0.18, function()
			Kit.tween(tagScale, T.Tween.spring, { Scale = 1 })
		end)
		task.delay(0.28, function()
			if shineGrad.Parent then
				Kit.tween(shineGrad, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut), { Offset = Vector2.new(1, 0) })
			end
		end)
		task.spawn(function()
			task.wait(0.32)
			local total = utf8.len(flavour.Text) or 0
			local i = 0
			while i < total and flavour.Parent do
				i += 2
				flavour.MaxVisibleGraphemes = i
				task.wait(0.016)
			end
			flavour.MaxVisibleGraphemes = -1
		end)
	end

	task.delay(hold + 0.5, function()
		if not root.Parent then
			return
		end
		if reduced then
			root:Destroy()
			return
		end
		local out = TweenInfo.new(0.35, Enum.EasingStyle.Quint, Enum.EasingDirection.In)
		Kit.tween(root, out, { Position = root.Position - UDim2.fromOffset(0, 24) })
		Kit.tween(streak, out, { BackgroundTransparency = 1 })
		for _, d in root:GetDescendants() do
			if d:IsA("TextLabel") then
				Kit.tween(d, out, { TextTransparency = 1 })
			elseif d:IsA("UIStroke") then
				Kit.tween(d, out, { Transparency = 1 })
			elseif d:IsA("Frame") and d.BackgroundTransparency < 1 then
				Kit.tween(d, out, { BackgroundTransparency = 1 })
			end
		end
		task.delay(0.4, function()
			root:Destroy()
		end)
	end)
	return root
end

return WordReveal
