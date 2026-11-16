--!strict
-- WordEngine test place (client).
-- Type ANY word or phrase -> see it as a Spectral summon (left) and a Solid summon (right) at once, the word
-- reveal banner, every WordResult field in the tag inspector, the parsed phrase breakdown, and the reaction
-- between the previous and the current word. Replay buttons drive the summon animators. The hotbar keeps the
-- last five casts (tap to recast, with charges + cooldown) so the whole UI kit is exercised.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local HttpService = game:GetService("HttpService")
local UserInputService = game:GetService("UserInputService")

local WordEngine = require(ReplicatedStorage:WaitForChild("WordEngine")) :: any
local UI = WordEngine.UI
local Theme = UI.Theme
local Kit = UI.Kit
local Toast = UI.Toast
local WordReveal = UI.WordReveal
local SettingsUI = UI.Settings
local T = Theme.get()

local player = Players.LocalPlayer
local testFolder = ReplicatedStorage:WaitForChild("WordEngineTestPlace", 30) :: Folder?

---------------------------------------------------------------------------------------------------
-- Settings (restored from the server-mirrored attribute, saved through WordEngineSettings)
---------------------------------------------------------------------------------------------------
local savedSettings: any = nil
pcall(function()
	local raw = player:GetAttribute("WE_Settings")
	if type(raw) == "string" then
		savedSettings = HttpService:JSONDecode(raw)
	end
end)
local settings = SettingsUI.new({ values = savedSettings, title = "Settings" })
local settingsRemote = ReplicatedStorage:FindFirstChild("WordEngineSettings") :: RemoteEvent?
local settingsDirty = 0
settings.Changed:Connect(function(_, _, all)
	settingsDirty += 1
	local token = settingsDirty
	task.delay(1.2, function()
		if token == settingsDirty and settingsRemote then
			settingsRemote:FireServer(all)
		end
	end)
end)

---------------------------------------------------------------------------------------------------
-- Screens
---------------------------------------------------------------------------------------------------
local hud = Kit.screen("WordEngineHUD", 10)
local overlay = Kit.screen("WordEngineTestOverlay", 30)

local function viewport(): Vector2
	local cam = workspace.CurrentCamera
	return if cam then cam.ViewportSize else Vector2.new(1280, 720)
end

-- Top bar: title card (left), replay controls (centre), tool buttons (right)
local topBar: Frame = Kit.new("Frame", {
	Name = "TopBar", BackgroundTransparency = 1, Position = UDim2.fromOffset(16, 10), Size = UDim2.new(1, -32, 0, 56),
	ZIndex = Theme.Z.panel, Parent = overlay,
})
local titleRoot, titleContent = Kit.glass({ Name = "Title", Size = UDim2.fromOffset(250, 56), Radius = Theme.Radius.lg,
	ZIndex = Theme.Z.panel, Accent = T.Color.Brand, Parent = topBar })
Kit.padding(6, 16).Parent = titleContent
Kit.list(Enum.FillDirection.Vertical, 0, Enum.HorizontalAlignment.Left, Enum.VerticalAlignment.Center).Parent = titleContent
local titleText = Kit.label({ Text = "WORDENGINE", Size = "title", Font = T.Font.Display, ZIndex = Theme.Z.panel + 3,
	LayoutOrder = 1, Parent = titleContent })
local titleGrad = Kit.gradient(T.Color.Brand2, T.Color.Brand, 0)
titleGrad.Parent = titleText
local subtitle = Kit.label({ Text = "TEST PLACE  ·  type anything", Size = "caption", Font = T.Font.Bold, Color = T.Color.TextMute,
	ZIndex = Theme.Z.panel + 3, LayoutOrder = 2, Parent = titleContent })

local tools: Frame = Kit.new("Frame", {
	Name = "Tools", BackgroundTransparency = 1, AnchorPoint = Vector2.new(1, 0), Position = UDim2.fromScale(1, 0),
	Size = UDim2.fromOffset(0, 56), AutomaticSize = Enum.AutomaticSize.X, ZIndex = Theme.Z.panel, Parent = topBar,
}, { Kit.list(Enum.FillDirection.Horizontal, 8, Enum.HorizontalAlignment.Right, Enum.VerticalAlignment.Center) })

local replay: ScrollingFrame = Kit.new("ScrollingFrame", {
	Name = "Replay", BackgroundTransparency = 1, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0),
	Position = UDim2.new(0.5, 0, 0, 66), Size = UDim2.new(1, -32, 0, 52), CanvasSize = UDim2.new(),
	AutomaticCanvasSize = Enum.AutomaticSize.X, ScrollingDirection = Enum.ScrollingDirection.X, ScrollBarThickness = 0,
	ZIndex = Theme.Z.panel, Selectable = false, Parent = overlay,
}, { Kit.list(Enum.FillDirection.Horizontal, 8, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center) })

---------------------------------------------------------------------------------------------------
-- Summons on the two pedestals
---------------------------------------------------------------------------------------------------
local STYLES = { "Spectral", "Solid" }
local PEDESTAL = { Spectral = Vector3.new(-10, 1.9, 0), Solid = Vector3.new(10, 1.9, 0) }
local MAX_HEIGHT = 15

local summonFolder = workspace:FindFirstChild("WordEngineSummons") or Instance.new("Folder")
summonFolder.Name = "WordEngineSummons"
summonFolder.Parent = workspace

local models: { [string]: Model? } = {}
local animators: { [string]: any } = {}
local current: any = nil -- WordResult
local previous: any = nil
local currentText = ""

local function seedOf(s: string): number
	local h = 2166136261
	for i = 1, #s do
		h = bit32.bxor(h, string.byte(s, i))
		h = (h * 16777619) % 4294967296
	end
	return h
end

local function clearSummons()
	for style, anim in animators do
		pcall(function()
			anim:destroy()
		end)
		animators[style] = nil
	end
	for style, m in models do
		if m then
			m:Destroy()
		end
		models[style] = nil
	end
end

local function pedestalLabel(style: string)
	local anchorName = style .. "Label"
	if workspace:FindFirstChild(anchorName) then
		return
	end
	local p = Instance.new("Part")
	p.Name = anchorName
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.Transparency = 1
	p.Size = Vector3.new(0.2, 0.2, 0.2)
	p.CFrame = CFrame.new(PEDESTAL[style] + Vector3.new(0, -0.6, 7.2))
	p.Parent = workspace
	local bb = Instance.new("BillboardGui")
	bb.Size = UDim2.fromOffset(170, 44)
	bb.LightInfluence = 0
	bb.MaxDistance = 140
	bb.Parent = p
	local _, content = Kit.glass({ Size = UDim2.fromScale(1, 1), Radius = 22, ZIndex = 2, Shadow = false,
		Accent = if style == "Spectral" then T.Color.Brand2 else T.Color.Warn, Parent = bb })
	Kit.label({ Text = string.upper(style), Size = "label", Font = T.Font.Heavy, XAlign = Enum.TextXAlignment.Center,
		AutomaticSize = Enum.AutomaticSize.None, FrameSize = UDim2.fromScale(1, 1), ZIndex = 5,
		Color = if style == "Spectral" then T.Color.Brand2 else T.Color.Warn, Parent = content })
end
for _, s in STYLES do
	pedestalLabel(s)
end

local function place(model: Model, style: string)
	local _, size = model:GetBoundingBox()
	if size.Y > MAX_HEIGHT then
		pcall(function()
			model:ScaleTo(model:GetScale() * MAX_HEIGHT / size.Y)
		end)
	end
	local cf, sz = model:GetBoundingBox()
	local pivot = model:GetPivot()
	local bottomOffset = (cf.Position.Y - sz.Y / 2) - pivot.Position.Y
	local base = PEDESTAL[style]
	-- face the camera, sit 0.05 above the plate (no contact faces with the pedestal)
	model:PivotTo(CFrame.new(base.X, base.Y + 0.05 - bottomOffset, base.Z) * CFrame.Angles(0, math.rad(if style == "Spectral" then 20 else -20), 0))
end

local function buildSummons(result: any)
	clearSummons()
	local seed = seedOf(result.canonical or result.id or "")
	for _, style in STYLES do
		local ok, model = pcall(function()
			return WordEngine.Summon.build(result, { style = style, seed = seed })
		end)
		if ok and model then
			model.Name = style .. "Summon"
			model.Parent = summonFolder
			place(model, style)
			models[style] = model
			local okA, anim = pcall(function()
				return WordEngine.Summon.animate(model, result)
			end)
			if okA and anim then
				animators[style] = anim
				pcall(function()
					anim:play("Spawn")
				end)
			end
		else
			warn("[TestPlace] Summon.build failed (" .. style .. "): " .. tostring(model))
		end
	end
end

local function playAll(name: string)
	for _, anim in animators do
		pcall(function()
			anim:play(name)
		end)
	end
end

---------------------------------------------------------------------------------------------------
-- Camera: framed on both pedestals, gentle drift; "Free cam" hands control back
---------------------------------------------------------------------------------------------------
local freeCam = false
local camStart = os.clock()
RunService:BindToRenderStep("WordEngineTestCamera", Enum.RenderPriority.Camera.Value + 1, function()
	local cam = workspace.CurrentCamera
	if not cam or freeCam then
		return
	end
	cam.CameraType = Enum.CameraType.Scriptable
	local maxH = 6
	for _, m in models do
		if m and m.Parent then
			local _, s = m:GetBoundingBox()
			maxH = math.max(maxH, s.Y)
		end
	end
	local vp = viewport()
	local aspect = vp.X / math.max(vp.Y, 1)
	local dist = (30 + maxH * 1.25) * math.clamp(1.6 / aspect, 0.85, 1.6)
	local t = os.clock() - camStart
	local target = Vector3.new(0, 1.9 + maxH * 0.45, 0)
	local sway = if Theme.reducedMotion then 0 else math.sin(t * 0.25) * 4
	local eye = target + Vector3.new(sway, 6 + maxH * 0.25, dist)
	cam.CFrame = cam.CFrame:Lerp(CFrame.lookAt(eye, target), 0.08)
	cam.FieldOfView = 50
end)

---------------------------------------------------------------------------------------------------
-- Inspector panel
---------------------------------------------------------------------------------------------------
local inspectorRoot, inspectorContent = Kit.glass({
	Name = "Inspector", AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -16, 0, 128),
	Size = UDim2.new(0, 360, 1, -150), Radius = Theme.Radius.xl, ZIndex = Theme.Z.panel, Transparency = 0.1,
	Parent = overlay,
})
Kit.padding(14, 14).Parent = inspectorContent
local scroller: ScrollingFrame = Kit.new("ScrollingFrame", {
	Name = "Scroll", BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1),
	CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 3,
	ScrollBarImageColor3 = T.Color.TextMute, ScrollingDirection = Enum.ScrollingDirection.Y, ZIndex = Theme.Z.panel + 3,
	Selectable = false, Parent = inspectorContent,
}, { Kit.list(Enum.FillDirection.Vertical, 10) })
local inspectorOpen = true

local Z = Theme.Z.panel + 4
local function clear(frame: Instance)
	for _, c in frame:GetChildren() do
		if c:IsA("GuiObject") then
			c:Destroy()
		end
	end
end

local layoutN = 0
local function nextOrder(): number
	layoutN += 1
	return layoutN
end

local function section(title: string, accent: Color3?): Frame
	local f: Frame = Kit.new("Frame", {
		Name = title, BackgroundColor3 = T.Color.Raised, BackgroundTransparency = 0.55, BorderSizePixel = 0,
		Size = UDim2.new(1, -4, 0, 0), AutomaticSize = Enum.AutomaticSize.Y, LayoutOrder = nextOrder(), ZIndex = Z,
		Parent = scroller,
	}, { Kit.corner(Theme.Radius.md), Kit.stroke(Color3.new(1, 1, 1), 0.92, 1), Kit.padding(10, 12),
		Kit.list(Enum.FillDirection.Vertical, 6) })
	Kit.label({ Name = "Heading", Text = string.upper(title), Size = "caption", Font = T.Font.Heavy,
		Color = accent or T.Color.TextMute, ZIndex = Z + 1, LayoutOrder = 0, Parent = f })
	return f
end

local function row(parent: Instance, key: string, value: string, swatch: Color3?): Frame
	local r: Frame = Kit.new("Frame", { Name = key, BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y, LayoutOrder = nextOrder(), ZIndex = Z + 1, Parent = parent })
	Kit.label({ Text = key, Size = "label", Font = T.Font.Medium, Color = T.Color.TextDim, ZIndex = Z + 1,
		AutomaticSize = Enum.AutomaticSize.Y, FrameSize = UDim2.new(0.4, 0, 0, 20), Parent = r })
	local valueX = 0.4
	if swatch then
		Kit.new("Frame", { Name = "Swatch", BackgroundColor3 = swatch, BorderSizePixel = 0, Position = UDim2.new(0.4, 0, 0, 3),
			Size = UDim2.fromOffset(14, 14), ZIndex = Z + 1, Parent = r }, { Kit.corner(4), Kit.stroke(Color3.new(1, 1, 1), 0.6, 1) })
	end
	local v = Kit.label({ Text = value, Size = "label", Font = T.Font.Semi, ZIndex = Z + 1, Wrapped = true,
		AutomaticSize = Enum.AutomaticSize.Y, Position = UDim2.new(valueX, if swatch then 20 else 0, 0, 0),
		FrameSize = UDim2.new(1 - valueX, if swatch then -20 else 0, 0, 20), Parent = r })
	v.RichText = false
	return r
end

local function chips(parent: Instance, items: { string }, accent: Color3, emptyText: string?)
	local wrap: Frame = Kit.new("Frame", { Name = "Chips", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y, LayoutOrder = nextOrder(), ZIndex = Z + 1, Parent = parent }, {
		Kit.new("UIGridLayout", { CellSize = UDim2.fromOffset(98, 26), CellPadding = UDim2.fromOffset(6, 6),
			SortOrder = Enum.SortOrder.LayoutOrder, FillDirectionMaxCells = 3 }),
	})
	if #items == 0 then
		wrap:FindFirstChildOfClass("UIGridLayout"):Destroy()
		Kit.label({ Text = emptyText or "none", Size = "label", Color = T.Color.TextMute, ZIndex = Z + 1, Parent = wrap })
		return
	end
	for i, text in items do
		local c: Frame = Kit.new("Frame", { Name = text, BackgroundColor3 = accent, BackgroundTransparency = 0.8,
			BorderSizePixel = 0, LayoutOrder = i, ZIndex = Z + 1, Parent = wrap },
			{ Kit.corner(UDim.new(0.5, 0)), Kit.stroke(accent, 0.45, 1) })
		local l = Kit.label({ Text = text, Size = "caption", Font = T.Font.Bold, Color = accent:Lerp(Color3.new(1, 1, 1), 0.45),
			XAlign = Enum.TextXAlignment.Center, AutomaticSize = Enum.AutomaticSize.None, FrameSize = UDim2.fromScale(1, 1),
			ZIndex = Z + 2, Parent = c })
		l.TextTruncate = Enum.TextTruncate.AtEnd
	end
end

local function statBar(parent: Instance, key: string, value: number, colour: Color3)
	local r: Frame = Kit.new("Frame", { Name = key, BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 20),
		LayoutOrder = nextOrder(), ZIndex = Z + 1, Parent = parent })
	Kit.label({ Text = key, Size = "label", Color = T.Color.TextDim, ZIndex = Z + 1, AutomaticSize = Enum.AutomaticSize.None,
		FrameSize = UDim2.new(0.32, 0, 1, 0), Parent = r })
	local track: Frame = Kit.new("Frame", { BackgroundColor3 = T.Color.Glass, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 0.5),
		Position = UDim2.new(0.32, 0, 0.5, 0), Size = UDim2.new(0.52, 0, 0, 8), ZIndex = Z + 1, Parent = r }, { Kit.corner(4) })
	local fill: Frame = Kit.new("Frame", { BackgroundColor3 = Color3.new(1, 1, 1), BorderSizePixel = 0, Size = UDim2.fromScale(0, 1),
		ZIndex = Z + 2, Parent = track }, { Kit.corner(4), Kit.gradient(colour:Lerp(Color3.new(1, 1, 1), 0.3), colour, 0) })
	Kit.tween(fill, T.Tween.slow, { Size = UDim2.fromScale(math.clamp(value / 10, 0, 1), 1) })
	Kit.label({ Text = string.format("%.1f", value), Size = "label", Font = T.Font.Mono, XAlign = Enum.TextXAlignment.Right,
		AutomaticSize = Enum.AutomaticSize.None, AnchorPoint = Vector2.new(1, 0), Position = UDim2.fromScale(1, 0),
		FrameSize = UDim2.new(0.14, 0, 1, 0), ZIndex = Z + 1, Parent = r })
end

local SOURCE_COLOUR = {
	Library = T.Color.Success, Cache = T.Color.Brand2, AI = T.Color.Brand, Admin = T.Color.Warn, Fallback = T.Color.Danger,
}

local function parse(text: string): any?
	local ok, p = pcall(function()
		return WordEngine.Resolver.parse(text)
	end)
	return if ok and type(p) == "table" then p else nil
end

local function str(v: any): string
	if v == nil then
		return "nil"
	end
	if type(v) == "number" then
		return if v % 1 == 0 then tostring(v) else string.format("%.2f", v)
	end
	return tostring(v)
end

local function hexColour(h: any): Color3?
	local ok, c = pcall(Color3.fromHex, h)
	return if ok then c else nil
end

local renderInspector -- forward

local function renderReaction(a: any?, b: any?)
	local accent = T.Color.Brand2
	local s = section("Reaction preview", accent)
	if not (a and b) then
		Kit.label({ Text = "Type two words to preview how their elements react.", Size = "label", Color = T.Color.TextMute,
			Wrapped = true, AutomaticSize = Enum.AutomaticSize.Y, FrameSize = UDim2.new(1, 0, 0, 0), ZIndex = Z + 1,
			LayoutOrder = nextOrder(), Parent = s })
		return
	end
	local ca = Theme.element(a.element, a.visual and a.visual.primaryColour)
	local cb = Theme.element(b.element, b.visual and b.visual.primaryColour)
	row(s, "A (previous)", string.upper(a.canonical) .. "  ·  " .. a.element, ca)
	row(s, "B (current)", string.upper(b.canonical) .. "  ·  " .. b.element, cb)
	local okR, reaction = pcall(function()
		return WordEngine.Reactions.get(a.element, b.element)
	end)
	local okM, ab = pcall(function()
		return WordEngine.Reactions.matchup(a.element, b.element)
	end)
	local okN, ba = pcall(function()
		return WordEngine.Reactions.matchup(b.element, a.element)
	end)
	row(s, "A hits B", if okM then ("x" .. str(ab)) else "n/a")
	row(s, "B hits A", if okN then ("x" .. str(ba)) else "n/a")
	if okR and reaction then
		row(s, "Reaction", reaction.name .. "  (" .. reaction.result .. ")")
		local d = Kit.label({ Text = reaction.description, Size = "label", Color = T.Color.TextDim, Wrapped = true,
			AutomaticSize = Enum.AutomaticSize.Y, FrameSize = UDim2.new(1, 0, 0, 0), ZIndex = Z + 1, LayoutOrder = nextOrder(), Parent = s })
		local _ = d
		statBar(s, "magnitude", (reaction.magnitudeHint or 0) * 10, accent)
		row(s, "duration", str(reaction.durationHint) .. " s")
		chips(s, reaction.hooks or {}, accent, "no hooks")
		chips(s, reaction.statuses or {}, T.Color.Warn, "no statuses")
		Kit.button({ Text = "Play reaction", Style = "Primary", Accent = accent, Size = UDim2.new(1, 0, 0, 48),
			LayoutOrder = nextOrder(), ZIndex = Z + 2, Parent = s, OnActivated = function()
				pcall(function()
					WordEngine.Effects.play(reaction.vfx, { position = Vector3.new(0, 4, 0), elements = reaction.elements, scale = 1.5 })
				end)
				Toast.show(reaction.name .. "!", { kind = "word", element = b.element, title = "Reaction" })
			end })
	else
		row(s, "Reaction", "none (no special interaction)")
	end
end

renderInspector = function(result: any?, text: string, info: any?)
	clear(scroller)
	layoutN = 0
	if not result then
		local s = section("Inspector")
		Kit.label({ Text = "Cast a word to inspect every field of its WordResult.", Size = "body", Color = T.Color.TextDim,
			Wrapped = true, AutomaticSize = Enum.AutomaticSize.Y, FrameSize = UDim2.new(1, 0, 0, 0), ZIndex = Z + 1,
			LayoutOrder = nextOrder(), Parent = s })
		renderReaction(nil, nil)
		return
	end
	local c0 = Theme.element(result.element, result.visual and result.visual.primaryColour)

	-- header
	local head = section("Result", c0)
	local big = Kit.label({ Text = string.upper(result.canonical), Size = "headline", Font = T.Font.Display, ZIndex = Z + 1,
		Wrapped = true, AutomaticSize = Enum.AutomaticSize.Y, FrameSize = UDim2.new(1, 0, 0, 0), LayoutOrder = nextOrder(), Parent = head })
	Kit.gradient(c0:Lerp(Color3.new(1, 1, 1), 0.4), c0, 90).Parent = big
	row(head, "source", result.source .. (if info and info.pending then "  (AI upgrade pending...)" else ""), SOURCE_COLOUR[result.source])
	statBar(head, "confidence", (result.confidence or 0) * 10, SOURCE_COLOUR[result.source] or c0)
	if info and info.reason and info.reason ~= "Ok" then
		row(head, "reason", tostring(info.reason))
	end

	-- phrase breakdown: count + modifiers + material + base + extras
	local p = parse(text)
	local pb = section("Phrase breakdown", T.Color.Brand)
	row(pb, "typed", text)
	local count = if p then p.count else result.count
	local mods = {}
	for _, m in (if p then p.modifiers else result.modifiers) or {} do
		table.insert(mods, m.id .. " · " .. string.lower(m.kind))
	end
	row(pb, "count", "x" .. str(count or 1))
	row(pb, "modifiers", if #mods > 0 then tostring(#mods) else "none")
	chips(pb, mods, T.Color.Brand, "no modifiers")
	row(pb, "material", str(if p then p.material else result.material))
	row(pb, "base", str(if p then (p.base or "?") else result.id))
	local extras = if p then (p.extras or {}) else {}
	row(pb, "extras", if #extras > 0 then table.concat(extras, ", ") else "none")
	if p and p.tokens then
		row(pb, "tokens", table.concat(p.tokens, " | "))
	end
	if not p then
		row(pb, "note", "Resolver.parse unavailable; derived from the result")
	end

	-- correction
	if result.correction then
		local cr = section("Correction (did you mean)", T.Color.Warn)
		row(cr, "method", result.correction.method)
		row(cr, "from -> to", str(result.correction.from) .. "  ->  " .. str(result.correction.to))
		statBar(cr, "confidence", (result.correction.confidence or 0) * 10, T.Color.Warn)
		chips(cr, result.correction.alternatives or {}, T.Color.Warn, "no alternatives")
	end

	-- classification
	local cl = section("Classification", c0)
	row(cl, "category", result.category)
	row(cl, "element", result.element, c0)
	local se = result.secondaryElement or "None"
	row(cl, "secondaryElement", se, if se ~= "None" then (Theme.element(se)) else nil)
	row(cl, "material", str(result.material))
	row(cl, "mood", str(result.mood))
	row(cl, "size", result.size)
	row(cl, "shape", result.shape)

	-- stats
	local st = section("Stats", c0)
	statBar(st, "power", result.power, c0)
	statBar(st, "speed", result.speed, c0)
	statBar(st, "durability", result.durability, c0)
	row(st, "count", str(result.count))

	local bh = section("Behaviours (" .. #result.behaviours .. ")", c0)
	chips(bh, result.behaviours, c0, "no behaviours")

	-- visual
	local v = result.visual or {}
	local vs = section("Visual", c0)
	row(vs, "primaryColour", str(v.primaryColour), hexColour(v.primaryColour))
	row(vs, "secondaryColour", str(v.secondaryColour), hexColour(v.secondaryColour))
	local parentPlan = nil
	pcall(function()
		parentPlan = WordEngine.Schema.BodyPlanParent[v.bodyPlan]
	end)
	row(vs, "bodyPlan", str(v.bodyPlan) .. (if parentPlan and parentPlan ~= v.bodyPlan then ("  (" .. parentPlan .. ")") else ""))
	row(vs, "silhouetteHint", str(v.silhouetteHint))
	row(vs, "motionHint", str(v.motionHint))
	row(vs, "soundHint", str(v.soundHint))
	Kit.label({ Text = "accents", Size = "label", Color = T.Color.TextDim, ZIndex = Z + 1, LayoutOrder = nextOrder(), Parent = vs })
	chips(vs, v.accents or {}, T.Color.Brand2, "no accents")

	-- identity / meta
	local me = section("Identity", T.Color.TextMute)
	row(me, "id", result.id)
	row(me, "canonical", result.canonical)
	row(me, "input", str(result.input))
	row(me, "synonymGroup", result.synonymGroup)
	row(me, "signature", str(result.signature))
	row(me, "schemaVersion", str(result.schemaVersion))
	local am = {}
	for _, m in result.modifiers or {} do
		table.insert(am, m.id)
	end
	row(me, "modifiers", if #am > 0 then table.concat(am, ", ") else "none")
	Kit.label({ Text = "tags", Size = "label", Color = T.Color.TextDim, ZIndex = Z + 1, LayoutOrder = nextOrder(), Parent = me })
	chips(me, result.tags or {}, T.Color.TextDim, "no tags")

	local fl = section("Flavour text", c0)
	Kit.label({ Text = "\u{201C}" .. (result.flavourText or "") .. "\u{201D}", Size = "body", Font = T.Font.Medium, Wrapped = true,
		AutomaticSize = Enum.AutomaticSize.Y, FrameSize = UDim2.new(1, 0, 0, 0), ZIndex = Z + 1, LayoutOrder = nextOrder(), Parent = fl })

	renderReaction(previous, current)
end

---------------------------------------------------------------------------------------------------
-- Typing box + hotbar
---------------------------------------------------------------------------------------------------
local hotbar = UI.Hotbar.new({ parent = hud, slots = 5 })
local function wordBookList(): { string }
	local out = {}
	for i = 1, 5 do
		local s = hotbar:getSlot(i)
		if s and s.word then
			table.insert(out, s.word)
		end
	end
	return out
end
local box = UI.TypingBox.new({
	parent = hud,
	placeholder = "Type anything... try \"small tornado\"",
	submitLabel = "CAST",
	wordBook = wordBookList,
})

local recent: { any } = {} -- hotbar results, newest first
local castRemote = testFolder and testFolder:FindFirstChild("Cast") :: RemoteEvent?

local function refreshHotbar()
	for i = 1, 5 do
		local r = recent[i]
		if r then
			hotbar:setSlot(i, { word = r.result.canonical, element = r.result.element, colour = r.result.visual.primaryColour,
				charges = r.charges, maxCharges = 3, used = r.charges <= 0, subtitle = if r.result.count > 1 then ("x" .. r.result.count) else nil })
		else
			hotbar:setSlot(i, nil)
		end
	end
end

local function show(result: any, text: string, info: any?, isUpgrade: boolean?)
	if not isUpgrade then
		previous = current
	end
	current = result
	currentText = text
	box:setResult(result)
	buildSummons(result)
	WordReveal.play(result)
	renderInspector(result, text, info)
	if not isUpgrade then
		table.insert(recent, 1, { result = result, charges = 3 })
		while #recent > 5 do
			table.remove(recent)
		end
		refreshHotbar()
		hotbar:select(1)
	else
		for _, r in recent do
			if r.result == previous or r.result.canonical == result.canonical then
				r.result = result
			end
		end
		refreshHotbar()
	end
	if castRemote and result.source ~= "Fallback" then
		castRemote:FireServer(result.id)
	end
end

local busy = false
local function resolve(text: string)
	if busy then
		return
	end
	busy = true
	box:setBusy(true)
	local result, info = WordEngine.Net.interpret(text)
	box:setBusy(false)
	busy = false
	if info and info.reason == "RateLimited" then
		Toast.show("Slow down a little!", { kind = "warn" })
	end
	show(result, text, info, false)
	if info and info.upgraded then
		info.upgraded:Connect(function(better)
			Toast.show("The AI found a better match: " .. string.upper(better.canonical), { kind = "word", element = better.element, title = "Upgraded" })
			show(better, text, info, true)
		end)
	end
end

box.Submitted:Connect(function(text)
	task.spawn(resolve, text)
end)
box.CorrectionAccepted:Connect(function(word)
	Toast.show("Corrected to " .. string.upper(word), { kind = "success" })
end)

hotbar.Activated:Connect(function(i)
	local r = recent[i]
	if not r or r.charges <= 0 then
		return
	end
	r.charges -= 1
	hotbar:setCharges(i, r.charges, 3)
	if r.charges <= 0 then
		hotbar:markUsed(i, true)
		task.delay(8, function()
			if recent[i] == r then
				r.charges = 3
				hotbar:markUsed(i, false)
				hotbar:setCharges(i, 3, 3)
				Toast.show(string.upper(r.result.canonical) .. " recharged", { kind = "success", element = r.result.element })
			end
		end)
	end
	hotbar:cooldown(i, 2.5)
	previous = current
	current = r.result
	buildSummons(r.result)
	WordReveal.play(r.result, { caster = player.DisplayName })
	renderInspector(r.result, r.result.canonical, nil)
	playAll("Attack")
end)

---------------------------------------------------------------------------------------------------
-- Replay controls + tool buttons
---------------------------------------------------------------------------------------------------
local function replayButton(text: string, order: number, fn: () -> ())
	Kit.button({ Text = text, Style = "Secondary", Size = UDim2.fromOffset(if #text > 6 then 108 else 92, 48), LayoutOrder = order,
		ZIndex = Theme.Z.panel + 2, Parent = replay, OnActivated = fn })
end
replayButton("Spawn", 1, function()
	playAll("Spawn")
end)
replayButton("Idle", 2, function()
	playAll("Idle")
end)
replayButton("Move", 3, function()
	playAll("Move")
end)
replayButton("Attack", 4, function()
	playAll("Attack")
end)
replayButton("Hit", 5, function()
	playAll("Hit")
end)
replayButton("Die", 6, function()
	playAll("Die")
	local r = current
	task.delay(1.6, function()
		if r and current == r then
			buildSummons(r)
		end
	end)
end)
replayButton("Reveal", 7, function()
	if current then
		WordReveal.play(current)
	end
end)
replayButton("Rebuild", 8, function()
	if current then
		buildSummons(current)
	end
end)
replayButton("Swap A/B", 9, function()
	if current and previous then
		current, previous = previous, current
		buildSummons(current)
		renderInspector(current, current.canonical, nil)
	end
end)

local function toolButton(text: string, order: number, fn: () -> (), style: string?)
	return Kit.button({ Text = text, Style = (style or "Secondary") :: any, Size = UDim2.fromOffset(if #text > 6 then 112 else 92, 48),
		LayoutOrder = order, ZIndex = Theme.Z.panel + 2, Parent = tools, OnActivated = fn })
end

local function setInspector(open: boolean)
	inspectorOpen = open
	local T2 = Theme.get()
	if open then
		inspectorRoot.Visible = true
		Kit.tween(inspectorRoot, T2.Tween.base, { Position = UDim2.new(1, -16, 0, 128) })
	else
		Kit.tween(inspectorRoot, T2.Tween.base, { Position = UDim2.new(1, inspectorRoot.AbsoluteSize.X + 24, 0, 128) })
		task.delay(Theme.Motion.base, function()
			if not inspectorOpen then
				inspectorRoot.Visible = false
			end
		end)
	end
end

toolButton("Inspect", 1, function()
	setInspector(not inspectorOpen)
end)
toolButton("Word book", 2, function()
	local fn = testFolder and testFolder:FindFirstChild("Book") :: RemoteFunction?
	if not fn then
		return
	end
	local ok, list = pcall(function()
		return fn:InvokeServer()
	end)
	if ok and type(list) == "table" then
		local names = {}
		for i = 1, math.min(#list, 8) do
			table.insert(names, string.upper(list[i].word) .. " x" .. list[i].count)
		end
		Toast.show(if #names > 0 then table.concat(names, ",  ") else "Nothing cast yet.",
			{ kind = "info", title = #list .. " words in your book", duration = 5 })
	end
end)
toolButton("Free cam", 3, function()
	freeCam = not freeCam
	local cam = workspace.CurrentCamera
	if freeCam and cam then
		cam.CameraType = Enum.CameraType.Custom
	end
	Toast.show(if freeCam then "Free camera" else "Showcase camera", { kind = "info", duration = 1.5 })
end)
toolButton("Settings", 4, function()
	settings:toggle()
end, "Ghost")

-- sample phrases (quick taps for mobile testing)
local samples: Frame = Kit.new("Frame", { Name = "Samples", BackgroundTransparency = 1, Position = UDim2.fromOffset(16, 128),
	Size = UDim2.fromOffset(190, 0), AutomaticSize = Enum.AutomaticSize.Y, ZIndex = Theme.Z.panel, Parent = overlay },
	{ Kit.list(Enum.FillDirection.Vertical, 2) })
for i, word in { "asteroid", "small tornado", "spaghetti dragon", "fire ice dragon", "tiny angry golden robot shark", "drgaon", "flibberjab" } do
	Kit.chip({ Text = word, LayoutOrder = i, Parent = samples, ZIndex = Theme.Z.panel + 1, OnActivated = function()
		box:submit(word)
	end })
end

---------------------------------------------------------------------------------------------------
-- Responsive layout: phones get a side-by-side bottom row and a closed inspector
---------------------------------------------------------------------------------------------------
local function relayout()
	local vp = viewport()
	local small = vp.X < 1000 or vp.Y < 560
	subtitle.Visible = not small
	titleRoot.Size = UDim2.fromOffset(if small then 170 else 250, 56)
	samples.Visible = vp.Y >= 520
	local hb = hotbar.root
	if small then
		hb.AnchorPoint = Vector2.new(1, 1)
		hb.Position = UDim2.new(1, -16, 1, -8)
		local hbW = hb.AbsoluteSize.X
		box.root.AnchorPoint = Vector2.new(0, 1)
		box.root.Size = UDim2.new(1, -(hbW + 48), 0, 0)
		box._basePos = UDim2.new(0, 16, 1, -12)
	else
		hb.AnchorPoint = Vector2.new(0.5, 1)
		hb.Position = UDim2.new(0.5, 0, 1, -12)
		box.root.AnchorPoint = Vector2.new(0.5, 1)
		box.root.Size = UDim2.new(1, -32, 0, 0)
		box._basePos = UDim2.new(0.5, 0, 1, -(hb.AbsoluteSize.Y + 24))
	end
	box.root.Position = box._basePos
	inspectorRoot.Size = UDim2.new(0, math.min(360, vp.X - 32), 1, -150)
	if small and inspectorOpen and current == nil then
		setInspector(false)
	end
end
task.defer(relayout)
if workspace.CurrentCamera then
	(workspace.CurrentCamera :: Camera):GetPropertyChangedSignal("ViewportSize"):Connect(relayout)
end

---------------------------------------------------------------------------------------------------
-- Server notices
---------------------------------------------------------------------------------------------------
if testFolder then
	local disc = testFolder:FindFirstChild("Discovered") :: RemoteEvent?
	if disc then
		disc.OnClientEvent:Connect(function(info)
			if type(info) == "table" then
				Toast.show("New word: " .. string.upper(tostring(info.word)) .. "  ·  " .. tostring(info.total) .. " discovered",
					{ kind = "word", element = info.element, title = "Word book" })
			end
		end)
	end
end
task.spawn(function()
	local notice = ReplicatedStorage:WaitForChild("WordEngineAdminNotice", 20) :: RemoteEvent?
	if notice then
		notice.OnClientEvent:Connect(function(text)
			Toast.show(tostring(text), { kind = "info", title = "Admin", duration = 6 })
		end)
	end
end)

renderInspector(nil, "", nil)
Toast.show("Type any word and press CAST. Both summon styles appear side by side.", { kind = "info", title = "Welcome", duration = 5 })
UserInputService.InputBegan:Connect(function(input, processed)
	if not processed and input.KeyCode == Enum.KeyCode.I and not UserInputService:GetFocusedTextBox() then
		setInspector(not inspectorOpen)
	end
end)
