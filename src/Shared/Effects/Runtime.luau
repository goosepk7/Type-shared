--!nonstrict
-- Effects runtime: pooled Roblox instances, one scheduler, and the "Fx" toolkit every renderer (Kinds/*) uses.
-- Roblox APIs are touched ONLY inside functions (the module requires cleanly under Lune). --!nonstrict because
-- the Instance-heavy code would need casts on nearly every line; the pure logic it depends on is --!strict.
--
-- Rules every renderer follows (enforced by helpers here):
--   * All parts: Anchored, CanCollide/CanTouch/CanQuery false, CastShadow false, Massless, pooled.
--   * Ground layers go through fx:groundDisc / fx:groundDecal, which lift them by DecalOffset * slot so they
--     never share a plane with the ground or with each other (rotating slots across all effects).
--   * Nested shells are built with fx:shells(), which enforces radius ratios >= ShellRatio.
--   * Emitters and trails are cooled down (kept until their last particle dies) before reuse: no popping.

local Config = require(script.Parent.Parent.Config)
local Palettes = require(script.Parent.Palettes)
local Presets = require(script.Parent.Presets)
local Assets = require(script.Parent.Assets)
local Curves = require(script.Parent.Curves)
local PoolLib = require(script.Parent.Pool)

local Runtime = {}

local VCFG = Config.Visual
local ECFG = Config.Visual.Effects
local PARK = nil -- CFrame far below the map for parked pooled parts (built lazily: CFrame is a Roblox global)

-- Environment (overridable for tests): workspace, container, attachment root, camera, clock.
local env = nil
local pools = {}
local active = {} -- array of live Fx
local cooling = {} -- { {expires, release} } emitters/trails waiting for their particles to die
local budget = nil
local degrader = nil
local slotNext = PoolLib.slots(ECFG.GroundSlots)
local clock = 0
local connection = nil
local colourCache = {}
local numberSeqCache = {}
local stats = { started = 0, refused = 0, culled = 0 }

-- ===========================================================================================================
-- Environment

local function detectDeviceClass(): string
	local ok, cls = pcall(function()
		local UIS = game:GetService("UserInputService")
		local GuiService = game:GetService("GuiService")
		if GuiService:IsTenFootInterface() then
			return "Console"
		end
		if UIS.TouchEnabled and not UIS.KeyboardEnabled then
			local cam = workspace.CurrentCamera
			local vp = cam and cam.ViewportSize
			if vp and math.min(vp.X, vp.Y) >= 700 then
				return "Tablet"
			end
			return "Phone"
		end
		return "Desktop"
	end)
	return if ok and cls then cls else "Desktop"
end

local function savedQuality(): number
	local ok, q = pcall(function()
		return UserSettings().GameSettings.SavedQualityLevel.Value
	end)
	return if ok and type(q) == "number" then q else 0
end

--- Initialise lazily. `custom` (tests) may supply { workspace, attachRoot, camera, deviceClass, noConnect }.
function Runtime.init(custom: any?)
	if env and not custom then
		return env
	end
	custom = custom or {}
	PARK = CFrame.new(0, -5000, 0)
	local ws = custom.workspace or workspace
	local container = custom.container
	if not container then
		container = ws:FindFirstChild("WordEngineFX")
		if not container then
			container = Instance.new("Folder")
			container.Name = "WordEngineFX"
			container.Parent = ws
		end
	end
	env = {
		workspace = ws,
		container = container,
		attachRoot = custom.attachRoot or (ws:FindFirstChildOfClass("Terrain") or ws.Terrain),
		camera = custom.camera,
		raycast = custom.raycast,
		deviceClass = custom.deviceClass or detectDeviceClass(),
	}
	local tier = PoolLib.pickTier(ECFG, env.deviceClass, if custom.deviceClass then 0 else savedQuality())
	budget = PoolLib.budget(ECFG, tier)
	degrader = PoolLib.degrader(ECFG, tier)
	Runtime.buildPools()
	if not custom.noConnect then
		local RunService = game:GetService("RunService")
		connection = RunService.Heartbeat:Connect(function(dt)
			Runtime.step(dt)
		end)
	end
	return env
end

function Runtime.env()
	return env
end

function Runtime.budget()
	return budget
end

function Runtime.setTier(tier: string)
	Runtime.init()
	budget:setTier(tier)
	degrader:setCeiling(tier)
end

-- ===========================================================================================================
-- Pools

-- Clear an Instance reference property (pcall: some non-Roblox hosts, e.g. Lune in tests, reject nil refs).
local function unset(obj: Instance, prop: string)
	pcall(function()
		(obj :: any)[prop] = nil
	end)
end

local function basePart(shape: string?): BasePart
	local p = Instance.new("Part")
	p.Anchored = true
	p.CanCollide = false
	p.CanTouch = false
	p.CanQuery = false
	p.CastShadow = false
	p.Massless = true
	p.Locked = true
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	if shape then
		p.Shape = Enum.PartType[shape]
	end
	p.CFrame = PARK
	p.Parent = env.container
	return p
end

local function parkPart(p)
	p.CFrame = PARK
	p.Transparency = 1
	p.LocalTransparencyModifier = 0
	p.Reflectance = 0
end

local function makePartPool(shape: string, withMesh: boolean)
	return PoolLib.new("Part" .. shape .. (if withMesh then "Mesh" else ""), function()
		local p = basePart(shape)
		if withMesh then
			local m = Instance.new("SpecialMesh")
			m.MeshType = Enum.MeshType.Sphere
			m.Parent = p
		end
		return p
	end, parkPart, function(p)
		p:Destroy()
	end, ECFG.PoolMaxIdle.Part)
end

function Runtime.buildPools()
	pools.Block = makePartPool("Block", false)
	pools.Ball = makePartPool("Ball", false)
	pools.Cylinder = makePartPool("Cylinder", false)
	pools.Ellipsoid = makePartPool("Block", true) -- Block + SpecialMesh(Sphere): stretched spheres
	pools.Carrier = PoolLib.new("Carrier", function()
		local p = basePart("Block")
		p.Transparency = 1
		return p
	end, parkPart, function(p)
		p:Destroy()
	end, ECFG.PoolMaxIdle.Emitter)
	pools.Attachment = PoolLib.new("Attachment", function()
		local a = Instance.new("Attachment")
		a.Parent = env.attachRoot
		return a
	end, function(a)
		a.Parent = env.attachRoot
		a.WorldCFrame = PARK
	end, function(a)
		a:Destroy()
	end, ECFG.PoolMaxIdle.Emitter * 2)
	pools.Emitter = {} -- per preset name, created on demand
	pools.Beam = PoolLib.new("Beam", function()
		local b = Instance.new("Beam")
		b.Enabled = false
		b.FaceCamera = true
		b.Parent = env.container
		return b
	end, function(b)
		b.Enabled = false
		unset(b, "Attachment0")
		unset(b, "Attachment1")
	end, function(b)
		b:Destroy()
	end, ECFG.PoolMaxIdle.Beam)
	pools.Trail = PoolLib.new("Trail", function()
		local t = Instance.new("Trail")
		t.Enabled = false
		t.FaceCamera = true
		t.Parent = env.container
		return t
	end, function(t)
		t.Enabled = false
		unset(t, "Attachment0")
		unset(t, "Attachment1")
		t.Parent = env.container
	end, function(t)
		t:Destroy()
	end, ECFG.PoolMaxIdle.Trail)
	pools.Light = PoolLib.new("Light", function()
		local l = Instance.new("PointLight")
		l.Enabled = false
		l.Shadows = false
		return l
	end, function(l)
		l.Enabled = false
		l.Parent = nil
	end, function(l)
		l:Destroy()
	end, ECFG.PoolMaxIdle.Light)
	pools.Decal = PoolLib.new("Decal", function()
		local p = basePart("Block")
		p.Transparency = 1
		local d = Instance.new("Decal")
		d.Face = Enum.NormalId.Top
		d.Parent = p
		return p
	end, function(p)
		parkPart(p)
		p.Transparency = 1
		local d = p:FindFirstChildOfClass("Decal")
		if d then
			d.Transparency = 1
		end
	end, function(p)
		p:Destroy()
	end, 32)
	pools.Highlight = PoolLib.new("Highlight", function()
		local h = Instance.new("Highlight")
		h.Enabled = false
		h.DepthMode = Enum.HighlightDepthMode.Occluded
		h.Parent = env.container
		return h
	end, function(h)
		h.Enabled = false
		unset(h, "Adornee")
	end, function(h)
		h:Destroy()
	end, ECFG.PoolMaxIdle.Highlight)
	local pw = ECFG.PoolPrewarm
	pools.Block:prewarm(pw.Part // 2)
	pools.Ball:prewarm(pw.Part // 2)
	pools.Beam:prewarm(pw.Beam)
	pools.Light:prewarm(pw.Light)
end

function Runtime.poolStats()
	local out = {}
	for name, p in pools do
		if name == "Emitter" then
			for preset, ep in p do
				out["Emitter:" .. preset] = ep:stats()
			end
		else
			out[name] = p:stats()
		end
	end
	return out
end

-- ===========================================================================================================
-- Colour / sequence helpers (cached: ColorSequence/NumberSequence are immutable values)

local function c3(hex: string): Color3
	local v = colourCache[hex]
	if not v then
		local r, g, b = Palettes.toRGB(hex)
		v = Color3.new(r, g, b)
		colourCache[hex] = v
	end
	return v
end
Runtime.c3 = c3

local function colourSeq(points: { { any } }): ColorSequence
	local key = ""
	for _, p in points do
		key ..= string.format("%.3f%s", p[1], p[2])
	end
	local cached = colourCache[key]
	if cached then
		return cached
	end
	local kps = {}
	for _, p in points do
		table.insert(kps, ColorSequenceKeypoint.new(p[1], c3(p[2])))
	end
	local seq = ColorSequence.new(kps)
	colourCache[key] = seq
	return seq
end
Runtime.colourSeq = colourSeq

local function numberSeq(points: any, mul: number?): NumberSequence
	local m = mul or 1
	if type(points) == "number" then
		points = { { 0, points }, { 1, points } }
	end
	local key = string.format("%.3f|", m)
	for _, p in points do
		key ..= string.format("%.3f:%.3f,", p[1], p[2])
	end
	local cached = numberSeqCache[key]
	if cached then
		return cached
	end
	local kps = {}
	for _, p in points do
		table.insert(kps, NumberSequenceKeypoint.new(p[1], p[2] * m))
	end
	local seq = NumberSequence.new(kps)
	numberSeqCache[key] = seq
	return seq
end
Runtime.numberSeq = numberSeq

local function range(r: { number }?, mul: number?): NumberRange
	if not r then
		return NumberRange.new(0)
	end
	local m = mul or 1
	return NumberRange.new(r[1] * m, (r[2] or r[1]) * m)
end

-- ===========================================================================================================
-- Emitters

local function configureEmitter(pe: ParticleEmitter, preset)
	local tex, layout = Assets.texture(preset.tex, budget.limits.flipbooks)
	pe.Texture = tex
	pe.FlipbookLayout = Enum.ParticleFlipbookLayout[layout]
	if layout ~= "None" and preset.flip then
		pe.FlipbookMode = Enum.ParticleFlipbookMode[preset.flip]
		pe.FlipbookFramerate = range(preset.fps or { 20, 30 })
		pe.FlipbookStartRandom = preset.flip == "Random" or preset.flip == "Loop"
	end
	pe.Lifetime = range(preset.life)
	pe.Transparency = numberSeq(preset.trans or { { 0, 0 }, { 1, 1 } })
	if preset.squash then
		pe.Squash = numberSeq(preset.squash)
	end
	pe.SpreadAngle = Vector2.new((preset.spread or { 0, 0 })[1], (preset.spread or { 0, 0 })[2])
	pe.EmissionDirection = Enum.NormalId[preset.dir or "Top"]
	pe.Rotation = range(preset.rot or { 0, 0 })
	pe.RotSpeed = range(preset.rotSpeed or { 0, 0 })
	pe.Drag = preset.drag or 0
	pe.Orientation = Enum.ParticleOrientation[preset.orient or "FacingCamera"]
	pe.Brightness = preset.brightness or 1
	pe.ZOffset = preset.zoffset or 0
	pe.LockedToPart = preset.locked == true
	pe.VelocityInheritance = preset.velInherit or 0
	if preset.shape then
		pe.Shape = Enum.ParticleEmitterShape[preset.shape]
		pe.ShapeStyle = Enum.ParticleEmitterShapeStyle[preset.shapeStyle or "Volume"]
		pe.ShapeInOut = Enum.ParticleEmitterShapeInOut[preset.shapeInOut or "Outward"]
	end
end

local function emitterPool(name: string)
	local p = pools.Emitter[name]
	if p then
		return p
	end
	local preset = Presets.get(name)
	assert(preset, "Effects: unknown emitter preset " .. tostring(name))
	p = PoolLib.new("Emitter:" .. name, function()
		local pe = Instance.new("ParticleEmitter")
		pe.Enabled = false
		pe.Rate = 0
		configureEmitter(pe, preset)
		return pe
	end, function(pe)
		pe.Enabled = false
		pe.Parent = nil
	end, function(pe)
		pe:Destroy()
	end, 16)
	pools.Emitter[name] = p
	return p
end

-- ===========================================================================================================
-- Fx: one live effect

local Fx = {}
Fx.__index = Fx
Runtime.Fx = Fx

local nextId = 0

function Runtime.newFx(entry, params, style: string, element: string, scale: number, pscale: number)
	nextId += 1
	local self = setmetatable({}, Fx)
	self.uid = nextId
	self.entry = entry
	self.params = params
	self.style = style
	self.element = element
	self.scale = scale
	self.pscale = pscale * budget.limits.particleScale
	self.detail = budget.limits.detail
	self.rampHex = Palettes.resolve(element, style, params.colour or entry.colour)
	self.ramp = {}
	for i, h in self.rampHex do
		self.ramp[i] = c3(h)
	end
	self.t = 0
	self.duration = params.duration or entry.duration
	self.loop = entry.loop == true and params.duration == nil
	self.fadeOut = params.fadeOut or 0.5
	self.fade = 1
	self.stopping = false
	self.dead = false
	self.seed = params.seed or nextId * 7919
	self.res = { parts = {}, emitters = {}, beams = {}, trails = {}, lights = {}, decals = {}, highlights = {}, attachments = {}, carriers = {} }
	self.updates = {}
	self.timers = {}
	self.followers = {}
	self.children = {}
	self.cleanups = {}
	self.finishedCallbacks = {}
	return self
end

-- Deterministic per-effect random numbers (xorshift); no Random global needed.
function Fx:rand(a: number?, b: number?): number
	local x = self.seed
	x = bit32.bxor(x, bit32.lshift(x, 13))
	x = bit32.bxor(x, bit32.rshift(x, 17))
	x = bit32.bxor(x, bit32.lshift(x, 5))
	x = bit32.band(x, 0x7FFFFFFF)
	if x == 0 then
		x = 1
	end
	self.seed = x
	local u = x / 0x7FFFFFFF
	if a == nil then
		return u
	end
	if b == nil then
		return u * a
	end
	return a + (b - a) * u
end

function Fx:c(i: number): Color3
	return self.ramp[math.clamp(i, 1, 5)]
end

function Fx:mat(role: string): Enum.Material
	return Enum.Material[Palettes.material(self.element, self.style, role)]
end

function Fx:spectral(): boolean
	return self.style ~= "Solid"
end

--- Base transparency for a role in this style (Spectral glows translucent, Solid is mostly opaque).
function Fx:alphaFor(role: string): number
	return Palettes.transparency(self.element, self.style, role)
end

-- Resolved positions --------------------------------------------------------------------------------------

local function posOf(v): Vector3?
	if v == nil then
		return nil
	end
	local tv = typeof(v)
	if tv == "Vector3" then
		return v
	elseif tv == "CFrame" then
		return v.Position
	elseif tv == "Instance" then
		if v:IsA("BasePart") then
			return v.CFrame.Position
		elseif v:IsA("Model") then
			return v:GetPivot().Position
		elseif v:IsA("Attachment") then
			return v.WorldPosition
		end
	end
	return nil
end
Runtime.posOf = posOf

--- Part to attach things to for an Instance target (Model -> PrimaryPart/HumanoidRootPart/first BasePart).
function Runtime.rootPart(target): BasePart?
	if typeof(target) ~= "Instance" then
		return nil
	end
	if target:IsA("BasePart") then
		return target
	end
	if target:IsA("Model") then
		return target.PrimaryPart or target:FindFirstChild("HumanoidRootPart") or target:FindFirstChildWhichIsA("BasePart", true)
	end
	return nil
end

--- Bounding size of a target (for status/aura sizing).
function Runtime.extents(target): Vector3
	if typeof(target) == "Instance" then
		if target:IsA("Model") then
			local ok, _, size = pcall(function()
				return target:GetBoundingBox()
			end)
			if ok and size then
				return size
			end
		elseif target:IsA("BasePart") then
			return target.Size
		end
	end
	return Vector3.new(4, 5, 4)
end

function Fx:targetPos(): Vector3?
	return posOf(self.target or self.params.target)
end

function Fx:at(): CFrame
	local p = self.params
	if typeof(p.at) == "CFrame" then
		return p.at
	elseif typeof(p.at) == "Vector3" then
		return CFrame.new(p.at)
	end
	local tp = posOf(p.target) or p.to or p.from
	if typeof(tp) == "CFrame" then
		return tp
	end
	return CFrame.new(tp or Vector3.zero)
end

function Fx:from(): Vector3
	return posOf(self.params.from) or self:at().Position
end

function Fx:to(): Vector3
	return posOf(self.target) or posOf(self.params.to) or posOf(self.params.target) or self:at().Position
end

--- Ground point below a position: raycast down (ignoring effects and characters), else the position itself.
function Fx:ground(pos: Vector3): (Vector3, Vector3)
	local rc = env.raycast
	if rc then
		local hit, normal = rc(pos)
		if hit then
			return hit, normal or Vector3.yAxis
		end
		return pos, Vector3.yAxis
	end
	local ok, result = pcall(function()
		local rp = RaycastParams.new()
		rp.FilterType = Enum.RaycastFilterType.Exclude
		local ignore = { env.container }
		local Players = game:GetService("Players")
		for _, pl in Players:GetPlayers() do
			if pl.Character then
				table.insert(ignore, pl.Character)
			end
		end
		if typeof(self.params.target) == "Instance" then
			table.insert(ignore, self.params.target)
		end
		rp.FilterDescendantsInstances = ignore
		rp.IgnoreWater = false
		return env.workspace:Raycast(pos + Vector3.new(0, 6, 0), Vector3.new(0, -80, 0), rp)
	end)
	if ok and result then
		return result.Position, result.Normal
	end
	return pos, Vector3.yAxis
end

-- Parts ----------------------------------------------------------------------------------------------------

--- Pooled part. shape: "Block" | "Ball" | "Cylinder" | "Ellipsoid". opts: colour (Color3 | ramp index),
--- material (role name or Enum.Material), transparency, reflectance.
function Fx:part(shape: string, size: Vector3, cf: CFrame, opts: any?): BasePart
	opts = opts or {}
	local pool = pools[shape] or pools.Block
	local p = pool:acquire()
	p.Size = size
	p.CFrame = cf
	local col = opts.colour
	p.Color = if typeof(col) == "Color3" then col else self:c(col or 3)
	local m = opts.material
	p.Material = if typeof(m) == "EnumItem" then m else self:mat(m or "core")
	p.Transparency = opts.transparency or self:alphaFor(opts.role or "core")
	p.Reflectance = opts.reflectance or 0
	if shape == "Ellipsoid" then
		local mesh = p:FindFirstChildOfClass("SpecialMesh")
		if mesh then
			mesh.Scale = Vector3.one
		end
	end
	table.insert(self.res.parts, { p, pool })
	return p
end

--- Concentric glow shells around a centre: radii grow by >= ShellRatio, so no two surfaces coincide.
--- Returns parts inner -> outer. alphas/colours are per shell.
function Fx:shells(cf: CFrame, radius: number, count: number, opts: any?): { BasePart }
	opts = opts or {}
	local ratio = math.max(opts.ratio or ECFG.ShellRatio, ECFG.ShellRatio)
	local out = {}
	local r = radius
	for i = 1, count do
		local p = self:part("Ball", Vector3.one * (2 * r), cf, {
			colour = (opts.colours and opts.colours[i]) or (i == 1 and 1 or math.min(5, i + 1)),
			material = (opts.materials and opts.materials[i]) or (if i == 1 then "core" else "shell"),
			transparency = (opts.alphas and opts.alphas[i]) or (if i == 1 then self:alphaFor("core") else 0.45 + i * 0.12),
		})
		table.insert(out, p)
		r *= ratio
	end
	return out
end

--- Flat disc on the ground (Cylinder rotated to lie flat). Height comes from a rotating global slot so stacked
--- ground layers never coincide. Returns the part and its ground-plane CFrame (centre at the bottom face).
function Fx:groundDisc(pos: Vector3, radius: number, opts: any?): (BasePart, CFrame)
	opts = opts or {}
	local g = if opts.noRaycast then pos else self:ground(pos)
	local slot = slotNext()
	local thick = opts.thickness or 0.05
	local lift = VCFG.DecalOffset * slot
	local base = CFrame.new(g + Vector3.new(0, lift, 0))
	local p = self:part("Cylinder", Vector3.new(thick, radius * 2, radius * 2), base * CFrame.new(0, thick / 2, 0) * CFrame.Angles(0, 0, math.pi / 2), opts)
	return p, base
end

--- Textured decal lying on the ground (scorch, crack, frost, shadow, rune circle). Invisible carrier part whose
--- top face sits DecalOffset * slot above the ground. Returns a wrapper {part, decal, set(transparency, size?)}.
--- When the texture is not uploaded (fallback ""), returns a soft disc look when opts.discFallback, else nil.
function Fx:groundDecal(pos: Vector3, size: number, texName: string, opts: any?)
	opts = opts or {}
	local tex = Assets.texture(texName, false)
	local g = if opts.noRaycast then pos else self:ground(pos)
	local slot = slotNext()
	local lift = VCFG.DecalOffset * slot
	local yaw = opts.yaw or self:rand(0, math.pi * 2)
	if tex == "" then
		if not opts.discFallback then
			return nil
		end
		local disc = self:groundDisc(g, size / 2, { noRaycast = true, colour = opts.colour, material = Enum.Material.SmoothPlastic, transparency = opts.transparency or 0.5 })
		return {
			part = disc,
			set = function(_, t: number, s: number?)
				disc.Transparency = t
				if s then
					disc.Size = Vector3.new(disc.Size.X, s, s)
				end
			end,
		}
	end
	local pool = pools.Decal
	local p = pool:acquire()
	local thick = 0.04
	p.Size = Vector3.new(size, thick, size)
	-- part top face = ground + lift (part centre half a thickness lower)
	p.CFrame = CFrame.new(g + Vector3.new(0, lift - thick / 2, 0)) * CFrame.Angles(0, yaw, 0)
	local d = p:FindFirstChildOfClass("Decal")
	d.Texture = tex
	d.Color3 = if typeof(opts.colour) == "Color3" then opts.colour elseif opts.colour then self:c(opts.colour) else Color3.new(1, 1, 1)
	d.Transparency = opts.transparency or 0
	d.ZIndex = slot
	table.insert(self.res.decals, p)
	return {
		part = p,
		decal = d,
		set = function(_, t: number, s: number?)
			d.Transparency = t
			if s then
				local cf = p.CFrame
				p.Size = Vector3.new(s, thick, s)
				p.CFrame = cf
			end
		end,
	}
end

-- Emitters -------------------------------------------------------------------------------------------------

--- Pooled ParticleEmitter configured from a preset with this effect's palette/style/scale.
--- where: CFrame (world), BasePart/Attachment (attached), or nil (effect origin).
--- opts: rate, size (multiplier), speed (mult), life (mult), colour (hex list), area (Vector3, area shapes),
---       offset (CFrame for attached), accel (Vector3), enabled (bool), dir (NormalId name), spread {x,y}
function Fx:emitter(name: string, where: any?, opts: any?)
	opts = opts or {}
	local preset = Presets.get(name)
	assert(preset, "Effects: unknown preset " .. tostring(name))
	local ep = emitterPool(name)
	local pe = ep:acquire()
	local s = self.scale * (opts.size or 1)
	pe.Size = numberSeq(opts.sizeKeys or preset.size or 1, s)
	if opts.trans then
		pe.Transparency = numberSeq(opts.trans)
	elseif opts.trans == nil and preset.trans then
		pe.Transparency = numberSeq(preset.trans)
	end
	pe.Speed = range(preset.speed or { 0, 0 }, self.scale * (opts.speed or 1))
	if opts.life then
		pe.Lifetime = range(preset.life, opts.life)
	else
		pe.Lifetime = range(preset.life)
	end
	local a = opts.accel
	if a then
		pe.Acceleration = a
	elseif preset.accel then
		pe.Acceleration = Vector3.new(preset.accel[1], preset.accel[2], preset.accel[3]) * self.scale
	else
		pe.Acceleration = Vector3.zero
	end
	if opts.spread then
		pe.SpreadAngle = Vector2.new(opts.spread[1], opts.spread[2])
	else
		pe.SpreadAngle = Vector2.new((preset.spread or { 0, 0 })[1], (preset.spread or { 0, 0 })[2])
	end
	pe.EmissionDirection = Enum.NormalId[opts.dir or preset.dir or "Top"]
	-- colour
	local seq
	if opts.colour then
		local pts = {}
		for i, h in opts.colour do
			table.insert(pts, { if #opts.colour == 1 then 0 else (i - 1) / (#opts.colour - 1), h })
		end
		if #pts == 1 then
			table.insert(pts, { 1, pts[1][2] })
		end
		seq = colourSeq(pts)
	elseif preset.hex then
		local pts = {}
		for i, h in preset.hex do
			table.insert(pts, { if #preset.hex == 1 then 0 else (i - 1) / (#preset.hex - 1), h })
		end
		if #pts == 1 then
			table.insert(pts, { 1, pts[1][2] })
		end
		seq = colourSeq(pts)
	elseif preset.smoke then
		local sm = Palettes.smoke(self.style)
		seq = colourSeq({ { 0, Palettes.lerp(sm, self.rampHex[5], 0.35) }, { 1, sm } })
	else
		local kps = Palettes.keypoints(self.rampHex, preset.colour or { 2, 3 })
		if preset.smokeMix then
			for _, kp in kps do
				kp[2] = Palettes.lerp(kp[2], Palettes.smoke(self.style), preset.smokeMix)
			end
		end
		seq = colourSeq(kps)
	end
	pe.Color = seq
	local em = preset.emission or { 1, 0 }
	local inf = preset.influence or { 0, 1 }
	local emissive = Palettes.emissive(self.element, self.style)
	if self.style == "Solid" then
		pe.LightEmission = if emissive then math.max(em[2], em[1] * 0.8) else em[2]
		pe.LightInfluence = if emissive then math.min(inf[2], 0.2) else inf[2]
	else
		pe.LightEmission = em[1]
		pe.LightInfluence = inf[1]
	end
	local baseRate = opts.rate or preset.rate or 0
	pe.Rate = baseRate * self.pscale

	-- parent (area shapes need a BasePart carrier; attachments emit from a point)
	local holder, carrier, att
	local shape = opts.shape or preset.shape
	if shape then
		pe.Shape = Enum.ParticleEmitterShape[shape]
		pe.ShapeStyle = Enum.ParticleEmitterShapeStyle[opts.shapeStyle or preset.shapeStyle or "Volume"]
		pe.ShapeInOut = Enum.ParticleEmitterShapeInOut[opts.shapeInOut or preset.shapeInOut or "Outward"]
	end
	if shape then
		carrier = pools.Carrier:acquire()
		carrier.Size = opts.area or (Vector3.one * (2 * self.scale))
		local cf = if typeof(where) == "CFrame" then where else self:at()
		carrier.CFrame = cf
		if typeof(where) == "Instance" then
			local root = if where:IsA("Attachment") then where.Parent else where
			table.insert(self.followers, { carrier, root, opts.offset or CFrame.new() })
			if root and root:IsA("BasePart") then
				carrier.CFrame = root.CFrame * (opts.offset or CFrame.new())
			end
		end
		pe.Parent = carrier
		holder = carrier
		table.insert(self.res.carriers, carrier)
	else
		att = pools.Attachment:acquire()
		if typeof(where) == "Instance" and where:IsA("BasePart") then
			att.Parent = where
			att.CFrame = opts.offset or CFrame.new()
		elseif typeof(where) == "Instance" and where:IsA("Attachment") then
			att.Parent = where.Parent
			att.CFrame = where.CFrame * (opts.offset or CFrame.new())
		else
			att.Parent = env.attachRoot
			att.WorldCFrame = if typeof(where) == "CFrame" then where else self:at()
		end
		pe.Parent = att
		holder = att
	end
	pe.Enabled = opts.enabled ~= false and baseRate > 0
	local wrapper = {
		pe = pe,
		holder = holder,
		pool = ep,
		att = att,
		carrier = carrier,
		maxLife = (preset.life and (preset.life[2] or preset.life[1]) or 1) * (opts.life or 1),
		baseRate = baseRate,
	}
	local fx = self
	function wrapper.emit(_, n: number)
		local count = math.max(1, math.floor(n * fx.pscale + 0.5))
		pe:Emit(count)
	end
	function wrapper.setRate(_, r: number)
		pe.Rate = r * fx.pscale
		pe.Enabled = r > 0 and not fx.stopping
	end
	function wrapper.setEnabled(_, on: boolean)
		pe.Enabled = on and pe.Rate > 0
	end
	function wrapper.moveTo(_, cf: CFrame)
		if carrier then
			carrier.CFrame = cf
		elseif att.Parent == env.attachRoot then
			att.WorldCFrame = cf
		else
			att.CFrame = cf
		end
	end
	table.insert(self.res.emitters, wrapper)
	return wrapper
end

-- Beams / trails / lights ----------------------------------------------------------------------------------

local function worldAttachment(fx, cf: CFrame)
	local a = pools.Attachment:acquire()
	a.Parent = env.attachRoot
	a.WorldCFrame = cf
	table.insert(fx.res.attachments, a)
	return a
end

--- Pooled Beam between two world CFrames/positions (or existing Attachments).
--- opts: width0, width1, colour (ColorSequence | hex list), transparency (keypoints), tex (texture name),
---       texLength, texSpeed, segments, curve0, curve1, lightEmission, zoffset, faceCamera
function Fx:beam(p0: any, p1: any, opts: any?)
	opts = opts or {}
	local b = pools.Beam:acquire()
	local a0 = if typeof(p0) == "Instance" then p0 else worldAttachment(self, if typeof(p0) == "CFrame" then p0 else CFrame.new(p0))
	local a1 = if typeof(p1) == "Instance" then p1 else worldAttachment(self, if typeof(p1) == "CFrame" then p1 else CFrame.new(p1))
	b.Attachment0 = a0
	b.Attachment1 = a1
	b.Width0 = (opts.width0 or 1) * self.scale
	b.Width1 = (opts.width1 or opts.width0 or 1) * self.scale
	if typeof(opts.colour) == "ColorSequence" then
		b.Color = opts.colour
	elseif type(opts.colour) == "table" then
		local pts = {}
		for i, h in opts.colour do
			table.insert(pts, { if #opts.colour == 1 then 0 else (i - 1) / (#opts.colour - 1), h })
		end
		if #pts == 1 then
			table.insert(pts, { 1, pts[1][2] })
		end
		b.Color = colourSeq(pts)
	else
		b.Color = colourSeq({ { 0, self.rampHex[2] }, { 1, self.rampHex[3] } })
	end
	b.Transparency = numberSeq(opts.transparency or { { 0, 0.1 }, { 1, 0.1 } })
	local tex = ""
	if opts.tex then
		tex = Assets.texture(opts.tex, false)
	end
	b.Texture = tex
	b.TextureMode = Enum.TextureMode[opts.texMode or "Wrap"]
	b.TextureLength = opts.texLength or 4
	b.TextureSpeed = opts.texSpeed or 0
	b.Segments = opts.segments or 10
	b.CurveSize0 = opts.curve0 or 0
	b.CurveSize1 = opts.curve1 or 0
	b.LightEmission = opts.lightEmission or (if self:spectral() then 1 else 0.6)
	b.LightInfluence = opts.lightInfluence or (if self:spectral() then 0 else 0.3)
	b.Brightness = opts.brightness or 1.5
	b.ZOffset = opts.zoffset or 0
	b.FaceCamera = opts.faceCamera ~= false
	b.Enabled = true
	local w = { beam = b, a0 = a0, a1 = a1 }
	function w.set(_, q0: any, q1: any)
		if q0 and a0.Parent == env.attachRoot then
			a0.WorldCFrame = if typeof(q0) == "CFrame" then q0 else CFrame.new(q0)
		end
		if q1 and a1.Parent == env.attachRoot then
			a1.WorldCFrame = if typeof(q1) == "CFrame" then q1 else CFrame.new(q1)
		end
	end
	table.insert(self.res.beams, w)
	return w
end

--- Trail on a moving part. width in studs, life seconds.
function Fx:trail(part: BasePart, width: number, life: number, opts: any?)
	opts = opts or {}
	local t = pools.Trail:acquire()
	local a0 = pools.Attachment:acquire()
	local a1 = pools.Attachment:acquire()
	a0.Parent = part
	a1.Parent = part
	local axis = opts.axis or Vector3.yAxis
	a0.CFrame = CFrame.new(axis * (width * self.scale / 2))
	a1.CFrame = CFrame.new(-axis * (width * self.scale / 2))
	table.insert(self.res.attachments, a0)
	table.insert(self.res.attachments, a1)
	t.Attachment0 = a0
	t.Attachment1 = a1
	t.Lifetime = life
	t.MinLength = 0.05
	t.WidthScale = numberSeq(opts.widthScale or { { 0, 1 }, { 1, 0 } })
	t.Transparency = numberSeq(opts.transparency or { { 0, 0.1 }, { 1, 1 } })
	t.Color = opts.colourSeq or colourSeq(Palettes.keypoints(self.rampHex, opts.colour or { 1, 3, 4 }))
	t.LightEmission = opts.lightEmission or (if self:spectral() then 1 else 0.4)
	t.LightInfluence = if self:spectral() then 0 else 0.5
	t.Brightness = opts.brightness or 1.5
	t.Texture = if opts.tex then Assets.texture(opts.tex, false) else ""
	t.TextureMode = Enum.TextureMode.Stretch
	t.FaceCamera = true
	t.Parent = part
	t:Clear()
	t.Enabled = true
	table.insert(self.res.trails, { t, life })
	return t
end

--- PointLight (skipped when the light budget is used up or the tier disables lights). where: CFrame or BasePart.
function Fx:light(where: any, colour: Color3?, brightness: number, rangeStuds: number)
	if self.detail < 2 or not budget:allow("lights") then
		return nil
	end
	local l = pools.Light:acquire()
	budget:use("lights", 1)
	local parent = where
	if typeof(where) ~= "Instance" then
		local a = worldAttachment(self, if typeof(where) == "CFrame" then where else self:at())
		parent = a
	end
	l.Parent = parent
	l.Color = colour or self:c(2)
	l.Brightness = brightness
	l.Range = math.min(60, rangeStuds * self.scale)
	l.Shadows = false
	l.Enabled = true
	table.insert(self.res.lights, l)
	return l
end

--- Highlight on a target (budgeted, optional). Returns nil when over budget.
function Fx:highlight(target: Instance, fill: Color3, outline: Color3, fillT: number, outlineT: number)
	if not budget:allow("highlights") then
		return nil
	end
	local h = pools.Highlight:acquire()
	budget:use("highlights", 1)
	h.Adornee = target
	h.FillColor = fill
	h.OutlineColor = outline
	h.FillTransparency = fillT
	h.OutlineTransparency = outlineT
	h.Enabled = true
	table.insert(self.res.highlights, h)
	return h
end

-- Scheduling -----------------------------------------------------------------------------------------------

function Fx:onUpdate(fn)
	table.insert(self.updates, fn)
end

function Fx:after(delay: number, fn)
	table.insert(self.timers, { at = self.t + delay, fn = fn })
end

function Fx:every(interval: number, fn, startDelay: number?)
	table.insert(self.timers, { at = self.t + (startDelay or 0), every = interval, fn = fn })
end

function Fx:onCleanup(fn)
	table.insert(self.cleanups, fn)
end

--- Keep `obj` (part/carrier) glued to `target` part each frame at `offset`.
function Fx:follow(obj: BasePart, target: BasePart, offset: CFrame?)
	table.insert(self.followers, { obj, target, offset or CFrame.new() })
end

--- Start a child effect (stopped with the parent).
function Fx:child(id: string, params: any)
	local Effects = Runtime.facade
	local p = table.clone(params)
	p.style = p.style or self.style
	p.priority = p.priority or self.params.priority
	local h = Effects.play(id, p)
	table.insert(self.children, h)
	return h
end

--- Release one emitter early (cools down so its particles finish).
function Fx:dropEmitter(w)
	w.pe.Enabled = false
	local idx = table.find(self.res.emitters, w)
	if idx then
		table.remove(self.res.emitters, idx)
	end
	Runtime.cool(w)
end

function Fx:stop()
	if self.stopping or self.dead then
		return
	end
	self.stopping = true
	self.stopT = self.t
	for _, w in self.res.emitters do
		w.pe.Enabled = false
	end
	for _, h in self.children do
		h:stop()
	end
end

-- ===========================================================================================================
-- Release

function Runtime.cool(w)
	table.insert(cooling, {
		expires = clock + w.maxLife + 0.1,
		release = function()
			w.pool:release(w.pe)
			if w.att then
				pools.Attachment:release(w.att)
			end
			if w.carrier then
				pools.Carrier:release(w.carrier)
			end
		end,
	})
end

function Runtime.releaseFx(fx)
	if fx.dead then
		return
	end
	fx.dead = true
	for _, fn in fx.cleanups do
		local ok, err = pcall(fn)
		if not ok then
			warn("[Effects] cleanup failed: " .. tostring(err))
		end
	end
	for _, rec in fx.res.parts do
		rec[2]:release(rec[1])
	end
	for _, p in fx.res.decals do
		pools.Decal:release(p)
	end
	for _, w in fx.res.emitters do
		w.pe.Enabled = false
		Runtime.cool(w)
	end
	for _, w in fx.res.beams do
		pools.Beam:release(w.beam)
	end
	for _, rec in fx.res.trails do
		local t, life = rec[1], rec[2]
		t.Enabled = false
		table.insert(cooling, {
			expires = clock + life,
			release = function()
				pools.Trail:release(t)
			end,
		})
	end
	-- attachments that hold trails/beams: release after the trails cool (same delay as the longest trail)
	local maxTrail = 0
	for _, rec in fx.res.trails do
		maxTrail = math.max(maxTrail, rec[2])
	end
	for _, a in fx.res.attachments do
		if maxTrail > 0 then
			table.insert(cooling, {
				expires = clock + maxTrail + 0.05,
				release = function()
					pools.Attachment:release(a)
				end,
			})
		else
			pools.Attachment:release(a)
		end
	end
	for _, l in fx.res.lights do
		pools.Light:release(l)
		budget:use("lights", -1)
	end
	for _, h in fx.res.highlights do
		pools.Highlight:release(h)
		budget:use("highlights", -1)
	end
	if fx.cost then
		budget:refund(fx.cost)
	end
	for _, cb in fx.finishedCallbacks do
		task.spawn(cb)
	end
	fx.res = nil
end

-- ===========================================================================================================
-- Scheduler

--- How many live copies of `entry` started at (almost) the same spot in the last 0.75 s. The facade scales a
--- stacked copy up a little so two identical effects never render coincident shells/faces (z-fighting).
function Runtime.stacked(entry, pos: Vector3?): number
	if pos == nil then
		return 0
	end
	local n = 0
	for _, fx in active do
		if fx.entry == entry and not fx.stopping and not fx.dead and fx.t < 0.75 and fx.origin and (fx.origin - pos).Magnitude < 1 then
			n += 1
		end
	end
	return n
end

function Runtime.add(fx)
	table.insert(active, fx)
end

local function stepFx(fx, dt: number)
	fx.t += dt
	local t = fx.t
	if not fx.stopping and not fx.loop and fx.duration and t >= fx.duration then
		fx:stop()
	end
	if fx.stopping then
		local f = if fx.fadeOut > 0 then 1 - (t - fx.stopT) / fx.fadeOut else 0
		fx.fade = math.clamp(f, 0, 1)
		if fx.fade <= 0 then
			return false
		end
	end
	for _, f in fx.followers do
		local obj, target, offset = f[1], f[2], f[3]
		if target and target.Parent then
			obj.CFrame = target.CFrame * offset
		end
	end
	local timers = fx.timers
	local i = 1
	while i <= #timers do
		local tm = timers[i]
		if t >= tm.at then
			if fx.stopping and tm.every then
				table.remove(timers, i)
			else
				local ok, err = pcall(tm.fn, fx)
				if not ok then
					warn("[Effects] " .. fx.entry.id .. " timer error: " .. tostring(err))
				end
				if tm.every then
					tm.at += tm.every
					i += 1
				else
					table.remove(timers, i)
				end
			end
		else
			i += 1
		end
	end
	for _, fn in fx.updates do
		local ok, err = pcall(fn, fx, t, dt)
		if not ok then
			warn("[Effects] " .. fx.entry.id .. " update error: " .. tostring(err))
			return false
		end
	end
	return true
end

function Runtime.step(dt: number)
	if not env then
		return
	end
	clock += dt
	local newTier = degrader:step(dt)
	if newTier then
		budget:setTier(newTier)
	end
	local n = #active
	local w = 1
	for r = 1, n do
		local fx = active[r]
		local alive = not fx.dead and stepFx(fx, dt)
		if alive then
			active[w] = fx
			w += 1
		else
			Runtime.releaseFx(fx)
		end
	end
	-- effects started during this step (children, timers) were appended past n: slide them down so the
	-- array stays contiguous
	local total = #active
	for k = n + 1, total do
		active[w] = active[k]
		w += 1
	end
	for k = w, math.max(n, total) do
		active[k] = nil
	end
	local c = 1
	while c <= #cooling do
		if clock >= cooling[c].expires then
			local rec = table.remove(cooling, c)
			rec.release()
		else
			c += 1
		end
	end
end

function Runtime.activeCount(): number
	return #active
end

function Runtime.coolingCount(): number
	return #cooling
end

--- Stop and release everything now (place teardown / tests).
function Runtime.clearAll()
	for _, fx in active do
		Runtime.releaseFx(fx)
	end
	table.clear(active)
	for _, rec in cooling do
		rec.release()
	end
	table.clear(cooling)
end

function Runtime.cameraPos(): Vector3?
	if env and env.camera then
		return env.camera
	end
	local cam = workspace and workspace.CurrentCamera
	return cam and cam.CFrame.Position
end

Runtime.stats = stats
Runtime.Curves = Curves

return Runtime
