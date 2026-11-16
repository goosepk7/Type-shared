--!strict
-- WordEngine test place (server): starts the engine, builds the showcase stage and lighting, and exposes
-- a small remote for recording casts into the word book (so discovery toasts and data can be tested).
-- Everything visual about summons happens on the client (testplace/Client) so both styles render side by side.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local Lighting = game:GetService("Lighting")

local WordEngine = require(ReplicatedStorage:WaitForChild("WordEngine")) :: any
local WordEngineServer = require(ServerScriptService:WaitForChild("WordEngineServer")) :: any

-- Studio play-solo: everyone is admin (Admin.isAdmin checks RunService:IsStudio()).
WordEngineServer.start({ game = "Test", remotes = true })

---------------------------------------------------------------------------------------------------
-- Lighting: cool night studio with warm key, bloom and subtle colour grading.
---------------------------------------------------------------------------------------------------
Lighting.Technology = Enum.Technology.Future
Lighting.Brightness = 2.2
Lighting.ClockTime = 19.4
Lighting.Ambient = Color3.fromRGB(28, 32, 48)
Lighting.OutdoorAmbient = Color3.fromRGB(60, 66, 92)
Lighting.EnvironmentDiffuseScale = 0.6
Lighting.EnvironmentSpecularScale = 0.8
Lighting.ShadowSoftness = 0.25
Lighting.GlobalShadows = true

local function ensure(className: string, name: string, parent: Instance): any
	local inst = parent:FindFirstChild(name)
	if not inst then
		inst = Instance.new(className)
		inst.Name = name
		inst.Parent = parent
	end
	return inst
end

local atmo = ensure("Atmosphere", "TestAtmosphere", Lighting)
atmo.Density = 0.32
atmo.Offset = 0.1
atmo.Color = Color3.fromRGB(70, 78, 120)
atmo.Decay = Color3.fromRGB(40, 30, 70)
atmo.Glare = 0.2
atmo.Haze = 1.4
local bloom = ensure("BloomEffect", "TestBloom", Lighting)
bloom.Intensity = 0.65
bloom.Size = 28
bloom.Threshold = 1.6
local cc = ensure("ColorCorrectionEffect", "TestGrade", Lighting)
cc.Contrast = 0.08
cc.Saturation = 0.08
cc.TintColor = Color3.fromRGB(246, 244, 255)
local sun = ensure("SunRaysEffect", "TestRays", Lighting)
sun.Intensity = 0.04
sun.Spread = 0.6

---------------------------------------------------------------------------------------------------
-- Stage. No coplanar faces: every part that touches another is sunk/inset (Config.Visual.Inset) so
-- surfaces never coincide (no z-fighting / texture shimmer).
---------------------------------------------------------------------------------------------------
local INSET = WordEngine.Config.Visual.Inset or 0.02
local stage = workspace:FindFirstChild("WordEngineStage") or Instance.new("Model")
stage.Name = "WordEngineStage"
stage:ClearAllChildren()
stage.Parent = workspace

local function part(props: { [string]: any }): BasePart
	local className = props.ClassName or "Part"
	local p: any = Instance.new(className)
	p.Anchored = true
	p.CanCollide = props.CanCollide ~= false
	p.CastShadow = props.CastShadow ~= false
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	for k, v in props do
		if k ~= "ClassName" and k ~= "CanCollide" and k ~= "CastShadow" then
			p[k] = v
		end
	end
	p.Parent = stage
	return p
end

-- floor: one big slab, top at y = 0
part({ Name = "Floor", Size = Vector3.new(220, 4, 220), CFrame = CFrame.new(0, -2, 0),
	Material = Enum.Material.Slate, Color = Color3.fromRGB(22, 24, 34) })
-- inner plaza: a slightly raised disc (top at y = 0.3); its bottom is sunk 0.5 into the floor
part({ Name = "Plaza", Shape = Enum.PartType.Cylinder, Size = Vector3.new(0.8, 70, 70),
	CFrame = CFrame.new(0, -0.1, 0) * CFrame.Angles(0, 0, math.rad(90)),
	Material = Enum.Material.Marble, Color = Color3.fromRGB(38, 42, 58) })
-- plaza rim: a neon disc 0.6 studs wider than the plaza whose top (y = 0.24) sits BELOW the plaza top (0.3),
-- so only a glowing band outside the plaza edge shows; no two faces share a plane.
part({ Name = "PlazaRim", Shape = Enum.PartType.Cylinder, Size = Vector3.new(0.6, 71.2, 71.2),
	CFrame = CFrame.new(0, -0.06, 0) * CFrame.Angles(0, 0, math.rad(90)),
	Material = Enum.Material.Neon, Color = Color3.fromRGB(110, 90, 255), CastShadow = false })

local PEDESTALS = {
	{ name = "Spectral", x = -10, accent = Color3.fromRGB(56, 214, 245) },
	{ name = "Solid", x = 10, accent = Color3.fromRGB(255, 181, 71) },
}
for _, ped in PEDESTALS do
	-- base drum: bottom sunk into the plaza, top at y = 1.6
	part({ Name = ped.name .. "Base", Shape = Enum.PartType.Cylinder, Size = Vector3.new(1.6, 13, 13),
		CFrame = CFrame.new(ped.x, 0.8, 0) * CFrame.Angles(0, 0, math.rad(90)),
		Material = Enum.Material.Basalt, Color = Color3.fromRGB(46, 50, 66) })
	-- top plate: narrower, top at y = 1.9, its bottom inset INSET below the drum top
	part({ Name = ped.name .. "Plate", Shape = Enum.PartType.Cylinder, Size = Vector3.new(0.3 + INSET, 11.4, 11.4),
		CFrame = CFrame.new(ped.x, 1.9 - (0.3 + INSET) / 2, 0) * CFrame.Angles(0, 0, math.rad(90)),
		Material = Enum.Material.SmoothPlastic, Color = Color3.fromRGB(30, 33, 46) })
	-- glow band around the drum: radius 6.55 (drum 6.5), height 0.25, centred 0.4 below the drum top
	part({ Name = ped.name .. "Glow", Shape = Enum.PartType.Cylinder, Size = Vector3.new(0.25, 13.1, 13.1),
		CFrame = CFrame.new(ped.x, 1.2, 0) * CFrame.Angles(0, 0, math.rad(90)),
		Material = Enum.Material.Neon, Color = ped.accent, CastShadow = false, CanCollide = false })
	local lamp = part({ Name = ped.name .. "Lamp", Size = Vector3.new(0.2, 0.2, 0.2), CFrame = CFrame.new(ped.x, 14, 6),
		Transparency = 1, CanCollide = false, CastShadow = false })
	local light = Instance.new("SpotLight")
	light.Face = Enum.NormalId.Bottom
	light.Angle = 70
	light.Range = 26
	light.Brightness = 3.2
	light.Color = ped.accent:Lerp(Color3.new(1, 1, 1), 0.6)
	light.Shadows = true
	light.Parent = lamp
	local label = Instance.new("Attachment")
	label.Name = ped.name .. "Anchor"
	label.Position = Vector3.new(ped.x, 1.9, 0)
	label.Parent = workspace.Terrain
end

-- backdrop arc of tall monoliths (spaced, never touching each other)
for i = -4, 4 do
	local a = math.rad(i * 13)
	local r = 48
	local h = 16 + (4 - math.abs(i)) * 2.5
	part({ Name = "Monolith" .. i, Size = Vector3.new(5, h, 2.4),
		CFrame = CFrame.new(math.sin(a) * r, h / 2 - 0.5, -math.cos(a) * r) * CFrame.Angles(0, -a, 0),
		Material = Enum.Material.Slate, Color = Color3.fromRGB(34, 36, 52) })
	-- neon inlay strip on the monolith's plaza-facing side: sunk 0.03 in, standing 0.07 proud (never coplanar)
	part({ Name = "Inlay" .. i, Size = Vector3.new(0.35, h - 3, 0.1),
		CFrame = CFrame.new(math.sin(a) * r, h / 2 - 0.5, -math.cos(a) * r) * CFrame.Angles(0, -a, 0) * CFrame.new(0, 0, 1.22),
		Material = Enum.Material.Neon, Color = if i % 2 == 0 then Color3.fromRGB(139, 108, 255) else Color3.fromRGB(56, 214, 245),
		CastShadow = false, CanCollide = false })
end

local spawn = workspace:FindFirstChildOfClass("SpawnLocation") or Instance.new("SpawnLocation")
spawn.Anchored = true
spawn.Size = Vector3.new(6, 1, 6)
spawn.CFrame = CFrame.new(0, 0.5 - INSET, 30)
spawn.Material = Enum.Material.SmoothPlastic
spawn.Color = Color3.fromRGB(46, 50, 66)
spawn.Transparency = 0
spawn.Parent = workspace
local decal = spawn:FindFirstChildOfClass("Decal")
if decal then
	decal:Destroy() -- default spawn decal would sit flush on the top face
end

---------------------------------------------------------------------------------------------------
-- Test remotes: record a cast into the word book, report discoveries back to the caster.
---------------------------------------------------------------------------------------------------
local folder = ReplicatedStorage:FindFirstChild("WordEngineTestPlace") or Instance.new("Folder")
folder.Name = "WordEngineTestPlace"
folder.Parent = ReplicatedStorage
local castRemote = folder:FindFirstChild("Cast") or Instance.new("RemoteEvent")
castRemote.Name = "Cast"
castRemote.Parent = folder
local bookRemote = folder:FindFirstChild("Book") or Instance.new("RemoteFunction")
bookRemote.Name = "Book"
bookRemote.Parent = folder
local discovered = folder:FindFirstChild("Discovered") or Instance.new("RemoteEvent")
discovered.Name = "Discovered"
discovered.Parent = folder

local WordBook = WordEngineServer.WordBook
local Analytics = WordEngineServer.Analytics
local lastCast: { [Player]: number } = {}

-- The client sends only the canonical id; the server re-resolves it locally so a client can't inject data.
castRemote.OnServerEvent:Connect(function(player: Player, id: any)
	if type(id) ~= "string" or #id > 40 then
		return
	end
	local now = os.clock()
	if now - (lastCast[player] or 0) < 0.25 then
		return
	end
	lastCast[player] = now
	local ok, result = pcall(function()
		return WordEngine.Resolver.resolveLocal(id)
	end)
	if not ok or type(result) ~= "table" then
		return
	end
	local entry, isNew = WordBook.record(player, result)
	pcall(Analytics.cast, player, result)
	if entry and isNew then
		local distinct = WordBook.count(player)
		discovered:FireClient(player, { word = result.canonical, element = result.element, total = distinct })
	end
end)

bookRemote.OnServerInvoke = function(player: Player)
	local list = WordBook.get(player)
	local out = {}
	for i = 1, math.min(#list, 60) do
		local e = list[i]
		out[i] = { word = e.word, count = e.count, element = e.element }
	end
	return out
end

Players.PlayerRemoving:Connect(function(p)
	lastCast[p] = nil
end)
