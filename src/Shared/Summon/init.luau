--!strict
-- Summon: procedural summon builder for WordEngine (DESIGN.md §8).
--
--   Summon.blueprint(result, opts) -> Blueprint   PURE + deterministic (Lune-testable). Same (result, opts.seed)
--                                                  gives an identical blueprint on every client and server.
--   Summon.build(result, opts) -> Model            Roblox only. Instantiates a blueprint (welds + Motor6D rig).
--   Summon.animate(model, result) -> Animator      Roblox only. Procedural animation, shared Heartbeat with LOD.
--   Summon.registerSignature(id, fn)               Hand-built blueprint for a word id (fn(B, ctx) using Builder).
--   Summon.check(blueprint) -> { Violation }       Z-fighting checker (coplanar / coincident surfaces).
--
-- opts = { style = "Spectral" | "Solid", seed = number?, scale = number?, budget = { maxParts?, maxParticles? }?,
--          meshes = false? (no sculpted-mesh hints: primitives only) }
-- Summon.preloadMeshes() starts loading the sculpted MeshPart pieces on the server (returns at once; on a client it
-- only watches the replicated folder). Summon.setMeshLibrary(lib) swaps in a game's own compatible library.

local Builder = require(script.Builder)
local Geom = require(script.Geom)
local Rng = require(script.Rng)
local Traits = require(script.Traits)
local Style = require(script.Style)
local Overlap = require(script.Overlap)
local Plans = require(script.Plans)
local Signatures = require(script.Signatures)
local Materials = require(script.Materials)
local Accents = require(script.Accents)
local MeshMap = require(script.MeshMap)
local Heroes = require(script.Heroes)

local Summon = {}

Summon.Geom = Geom
Summon.Overlap = Overlap
Summon.Traits = Traits
Summon.Plans = Plans
Summon.Materials = Materials
Summon.Accents = Accents
Summon.MeshMap = MeshMap
Summon.Heroes = Heroes

-- Material records come from Library.material when present; a provider can supply them otherwise.
function Summon.setMaterialProvider(fn: ((string) -> any)?)
	Materials.setProvider(fn)
end
Plans.signatureHook = Signatures.get

local function cfgVisual(): any
	local ok, Config = pcall(function()
		return require(script.Parent.Config) :: any
	end)
	local v = (ok and Config and Config.Visual) or {}
	return {
		Inset = v.Inset or 0.02,
		PartBudget = v.SummonPartBudget or { Tiny = 8, Small = 12, Medium = 20, Large = 30, Huge = 40, Colossal = 40 },
		SignatureBonus = v.SummonSignatureBonus or 0.25,
		EmitterBudget = v.SummonEmitterBudget or { Solid = 2, Spectral = 3 },
		MaxParticleRate = v.SummonMaxParticleRate or 60,
		MaxTrails = v.SummonMaxTrails or 4,
		MaxLights = v.SummonMaxLights or 1,
		Height = v.SummonHeight or { Tiny = 1.6, Small = 3, Medium = 5, Large = 8, Huge = 13, Colossal = 20 },
		SpectralCoreScale = v.SummonSpectralCoreScale or 0.6,
		SpectralHighlight = if v.SummonSpectralHighlight == nil then true else v.SummonSpectralHighlight,
		FormationBudgetScale = v.SummonFormationBudgetScale or 2,
		FormationMinParts = v.SummonFormationMinParts or 5,
		EffectBudget = v.SummonEffectBudget or { Solid = 2, Spectral = 3 },
	}
end
Summon.config = cfgVisual

-- SIGNATURES -----------------------------------------------------------------------------------------------

-- registerSignature(id, fn, opts?) with opts = { plan: string? ("Quadruped|Dragon"), mesh: { assetId, scale?,
-- offset?, keepRoles? }? }. A mesh-backed signature still builds its procedural blueprint (fallback + faces,
-- accents, materials, effects); Instantiate swaps the body for the loaded mesh when the asset arrives.
function Summon.registerSignature(id: string, fn: (any, any) -> (), opts: any?)
	local o = opts or {}
	Signatures.register(id, fn, o.plan)
	if o.mesh then
		Signatures.setMesh(id, o.mesh)
	end
end

function Summon.setSignatureMesh(id: string, mesh: any?)
	Signatures.setMesh(id, mesh)
end

function Summon.signatures(): { string }
	return Signatures.list()
end

function Summon.signatureFor(result: any): (string?, any)
	return Signatures.find(result)
end

-- BUDGET ---------------------------------------------------------------------------------------------------

-- Keep the most important parts. Mirrored pairs stay together; parts that `need` a dropped pair go too.
local function fitBudget(parts: { any }, maxParts: number): ({ any }, number)
	if #parts <= maxParts then
		return parts, 0
	end
	local units: { any } = {}
	local unitOf: { [string]: any } = {}
	for i, p in parts do
		local key = p.pair or ("#" .. i)
		local u = unitOf[key]
		if u == nil then
			u = { key = key, pri = p.pri or 2, first = i, parts = {} }
			unitOf[key] = u
			table.insert(units, u)
		end
		u.pri = math.min(u.pri, p.pri or 2)
		table.insert(u.parts, p)
	end
	table.sort(units, function(a, b)
		if a.pri ~= b.pri then
			return a.pri < b.pri
		end
		return a.first < b.first
	end)
	local keptKeys: { [string]: boolean } = {}
	local keptNames: { [string]: boolean } = {}
	local n = 0
	for _, u in units do
		local ok = n + #u.parts <= maxParts
		if ok then
			for _, p in u.parts do
				if p.needs and not (keptKeys[p.needs] or keptNames[p.needs]) then
					ok = false
				end
			end
		end
		if ok then
			keptKeys[u.key] = true
			for _, p in u.parts do
				keptNames[p.name] = true
			end
			n += #u.parts
		end
	end
	local out = {}
	for i, p in parts do
		if keptKeys[p.pair or ("#" .. i)] then
			table.insert(out, p)
		end
	end
	return out, #parts - #out
end
Summon._fitBudget = fitBudget

-- BOUNDS / SCALE -------------------------------------------------------------------------------------------

local function bounds(parts: { any }): ({ number }, { number })
	local mn = { math.huge, math.huge, math.huge }
	local mx = { -math.huge, -math.huge, -math.huge }
	for _, p in parts do
		local cf, s = p.cf, p.size
		local hx, hy, hz = s[1] / 2, s[2] / 2, s[3] / 2
		local ex = math.abs(cf[4]) * hx + math.abs(cf[5]) * hy + math.abs(cf[6]) * hz
		local ey = math.abs(cf[7]) * hx + math.abs(cf[8]) * hy + math.abs(cf[9]) * hz
		local ez = math.abs(cf[10]) * hx + math.abs(cf[11]) * hy + math.abs(cf[12]) * hz
		mn[1] = math.min(mn[1], cf[1] - ex)
		mn[2] = math.min(mn[2], cf[2] - ey)
		mn[3] = math.min(mn[3], cf[3] - ez)
		mx[1] = math.max(mx[1], cf[1] + ex)
		mx[2] = math.max(mx[2], cf[2] + ey)
		mx[3] = math.max(mx[3], cf[3] + ez)
	end
	if mn[1] == math.huge then
		return { -0.5, 0, -0.5 }, { 0.5, 1, 0.5 }
	end
	return mn, mx
end
Summon._bounds = bounds

local VEHICLE_SCALE: { [string]: number } = { Tiny = 0.55, Small = 0.8, Medium = 1, Large = 1.1, Huge = 1.25, Colossal = 1.5 }

local function scaleAll(bp: any, k: number)
	for _, p in bp.parts do
		p.cf = Geom.scaled(p.cf, k)
		p.size = { p.size[1] * k, p.size[2] * k, p.size[3] * k }
	end
	for _, b in bp.bones do
		b.pos = { b.pos[1] * k, b.pos[2] * k, b.pos[3] * k }
	end
	for name, f in bp.sockets do
		bp.sockets[name] = Geom.scaled(f, k)
	end
end

-- Remove bones without parts; children re-parent to the nearest kept ancestor.
local function pruneBones(bp: any)
	local used: { [string]: boolean } = { Body = true }
	for _, p in bp.parts do
		used[p.bone] = true
	end
	local byName: { [string]: any } = {}
	for _, b in bp.bones do
		byName[b.name] = b
	end
	local function keptAncestor(name: string?): string?
		local cur = name
		while cur ~= nil and not used[cur] do
			local b = byName[cur]
			cur = b and b.parent or nil
		end
		return cur
	end
	local out = {}
	for _, b in bp.bones do
		if used[b.name] then
			local nb = table.clone(b)
			if nb.parent ~= nil then
				nb.parent = keptAncestor(nb.parent) or "Body"
			end
			table.insert(out, nb)
		end
	end
	bp.bones = out
	-- sockets on pruned bones fall back to the nearest kept ancestor
	if bp.rig.socketBones then
		for s, bname in bp.rig.socketBones do
			bp.rig.socketBones[s] = keptAncestor(bname) or "Body"
		end
	end
end

-- FORMATION ------------------------------------------------------------------------------------------------

local function formation(count: number, spacing: number, rng: any): { any }
	local slots = {}
	if count <= 3 then
		for i = 1, count do
			table.insert(slots, { (i - (count + 1) / 2) * spacing, 0, (i % 2) * spacing * 0.25 })
		end
	elseif count <= 6 then
		-- V wedge, leader at front
		table.insert(slots, { 0, 0, 0 })
		for i = 2, count do
			local rank = math.floor(i / 2)
			local side = if i % 2 == 0 then 1 else -1
			table.insert(slots, { side * rank * spacing * 0.9, 0, rank * spacing * 0.8 })
		end
	else
		local cols = math.ceil(math.sqrt(count))
		for i = 1, count do
			local row = math.floor((i - 1) / cols)
			local col = (i - 1) % cols
			local stagger = if row % 2 == 1 then 0.5 else 0
			table.insert(slots, { (col - (cols - 1) / 2 + stagger) * spacing, 0, row * spacing * 0.9 })
		end
	end
	local out = {}
	for i, s in slots do
		local yaw = if i == 1 then 0 else (rng:next() - 0.5) * 0.3
		table.insert(out, Geom.at(s[1], s[2], s[3], 0, yaw, 0))
	end
	return out
end

-- BLUEPRINT ------------------------------------------------------------------------------------------------

export type Blueprint = {
	id: string,
	style: string,
	bodyPlan: string,
	builder: string, -- "signature:<id>" or "plan:<BodyPlan>"
	seed: number,
	size: string,
	scale: number,
	parts: { any },
	bones: { any },
	rig: { [string]: any },
	sockets: { [string]: any },
	fx: any,
	root: { size: { number }, cf: { number } },
	members: { any }?, -- formation offsets (count > 1); every member reuses `parts`
	motion: string,
	stats: { [string]: number },
}

function Summon.blueprint(result: any, opts: any?): Blueprint
	local o = opts or {}
	local style = if o.style == "Spectral" then "Spectral" else "Solid"
	local cfg = cfgVisual()
	local r = result
	local id = tostring(r.id or "thing")
	local seed = if type(o.seed) == "number" then o.seed else Rng.hash(id)
	local rng = Rng.new(bit32.bxor(Rng.hash(id .. "|" .. style), math.floor(seed) % 4294967296))
	local t = Traits.read(r)
	local sigId, sigFn = Signatures.find(r)
	-- hero models (Heroes/): a fully sculpted model with its own skeleton wins over signatures and plans
	local heroId, heroDef = nil, nil
	if o.heroes ~= false then
		heroId, heroDef = Heroes.find(r)
	end
	if heroDef then
		sigId, sigFn = nil, nil
	end
	-- Budget first, so generators pick a matching level of detail instead of building parts that get dropped.
	local count = math.clamp(math.floor(tonumber(r.count) or 1), 1, 12)
	local maxParts = (cfg.PartBudget[r.size or "Medium"] or 20)
	if sigFn then
		maxParts = math.floor(maxParts * (1 + cfg.SignatureBonus))
	end
	if heroDef then
		-- a hero is one coherent model: its own part list is the budget (fine detail still drops first on Low);
		-- a formation of heroes keeps the class formation budget (six sculpted ants must not cost six full models)
		maxParts = math.floor(maxParts * (1 + cfg.SignatureBonus))
		if count == 1 then
			maxParts = math.max(maxParts, #heroDef.parts + 4)
		end
	end
	if count > 1 then
		maxParts = math.max(cfg.FormationMinParts, math.floor(maxParts * cfg.FormationBudgetScale / count))
	end
	if o.budget and o.budget.maxParts then
		maxParts = math.max(1, math.floor(o.budget.maxParts))
	end
	-- stage 2/3 inputs: material record and modifier accents (they reserve part budget, so the plan builds leaner)
	local material = Materials.resolve(r, o)
	local accents = (r.visual and r.visual.accents) or {}
	local accentMood = Accents.moodFor(accents)
	if accentMood and (r.mood == nil or r.mood == "Neutral") then
		r = table.clone(r)
		r.mood = accentMood
	end
	local matReserve = Materials.reserve(material, maxParts)
	local accReserve = Accents.reserve(accents)
	local spectralReserve = if style == "Spectral" then 3 else 0
	local avail = maxParts - spectralReserve - matReserve - accReserve
	local detail = if avail <= 9 then 0 elseif avail <= 15 then 1 elseif avail <= 24 then 2 else 3
	if type(o.detail) == "number" then
		detail = math.clamp(math.floor(o.detail), 0, 3) -- tooling: reference builds of a low-detail layout (export_refs)
	end
	local ctx = { result = r, traits = t, style = style, rng = rng, seed = seed, detail = detail, budget = maxParts, material = material }
	t.detail = detail
	local B = Builder.new(ctx, rng)

	local builderName
	local plan = (r.visual and r.visual.bodyPlan) or "Blob"
	if heroDef and heroId then
		Heroes.build(B, ctx, heroId, heroDef)
		builderName = "hero:" .. heroId
	elseif sigFn then
		sigFn(B, ctx)
		builderName = "signature:" .. sigId
	else
		local fn = Plans[plan] or Plans.Blob
		fn(B, ctx)
		builderName = "plan:" .. plan
	end
	-- sculpted look: every part the plan did not hint itself gets its mesh piece by role and shape. Pure data (piece
	-- ids only): whether an asset is loaded is Instantiate's business, so the blueprint stays deterministic.
	if o.meshes ~= false then
		MeshMap.assign(B, ctx)
	else
		for _, p in B.parts do
			p.mesh, p.meshOf, p.meshL = nil, nil, nil -- generator hints too: the plain primitive build
		end
	end
	if B.sockets.core == nil then
		-- default core socket: centre of the most important body part
		local best
		for _, p in B.parts do
			if best == nil or (p.pri or 2) < (best.pri or 2) then
				best = p
			end
		end
		if best then
			B:socket("core", Geom.new(best.cf[1], best.cf[2], best.cf[3]), best.bone)
		else
			B:socket("core", Geom.new(0, 1, 0), "Body")
		end
	end

	-- stage 2: material reshapes construction; stage 3: accents (modifiers) on top
	local matInfo = nil
	if material then
		-- signatures and dense plans may already fill the budget: the construction still gets a share and competes
		-- on priority in fitBudget (it outranks fine plan details, never the face)
		local room = maxParts - spectralReserve - accReserve - #B.parts
		room = math.max(room, math.floor(matReserve * 0.75))
		matInfo = Materials.apply(B, material, room, ctx)
	end
	local accentFx = Accents.apply(B, accents, t)
	MeshMap.validate(B.parts)
	if B.sockets.head == nil and #B.parts > 0 then
		local A = Accents._anchors(B)
		B:socket("head", Geom.new(A.top[1], A.top[2], A.top[3]), A.headBone)
	end

	local bp: any = {
		id = id,
		style = style,
		bodyPlan = plan,
		builder = builderName,
		meshAsset = if sigId then Signatures.mesh(sigId) else nil,
		seed = seed,
		size = r.size or "Medium",
		parts = B.parts,
		bones = B.bones,
		rig = B.rig,
		sockets = B.sockets,
		motion = (r.visual and r.visual.motionHint) or "Static",
		stats = {},
	}

	-- style layers (adds Spectral cores) then the part budget
	Style.apply(bp, B, r, t, style, cfg)
	bp.detail = detail
	local generated = #bp.parts
	local dropped
	bp.parts, dropped = fitBudget(bp.parts, maxParts)
	pruneBones(bp)

	-- normalise to the size class height (x opts.scale), then resolve coincident faces at final scale
	local mn, mx = bounds(bp.parts)
	local extent = math.max(mx[2] - math.min(0, mn[2]), (mx[3] - mn[3]) * 0.8, (mx[1] - mn[1]) * 0.8)
	local target = (cfg.Height[bp.size] or 5) * (tonumber(o.scale) or 1)
	local k = target / math.max(extent, 1e-3)
	-- sculpted vehicles are authored at their real size around a 5-stud rider (a rowboat seats one, a galleon is
	-- a galleon): keep that size, nudged by the size class, never more than VehicleMaxClass x the class height
	local hdef = bp.rig.hero and Heroes.get(bp.rig.hero)
	if hdef and hdef.plan == "Vehicle" then
		local f = (cfg.VehicleScale and cfg.VehicleScale[bp.size]) or VEHICLE_SCALE[bp.size] or 1
		k = math.min(f * (tonumber(o.scale) or 1), (cfg.VehicleMaxClass or 2.5) * target / math.max(extent, 1e-3))
	end
	scaleAll(bp, k)
	bp.scale = k
	if bp.rig.clips then
		bp.rig.clipScale = k -- authored clip translations are in model studs
	end
	local fixes = Overlap.fix(bp.parts, cfg.Inset)

	-- unique, stable part names
	local seen: { [string]: number } = {}
	for _, p in bp.parts do
		local nm = p.name or "Part"
		if seen[nm] then
			seen[nm] += 1
			p.name = nm .. "_" .. seen[nm]
		else
			seen[nm] = 1
		end
	end
	-- mesh hints: drop the ones a material or accent invalidated (reshaped parts), resolve sculpt groups to names
	local meshParts = MeshMap.settle(bp.parts)

	local fx = Style.budgetFx(bp, style, cfg)
	-- looping attached effects (Effects.play ids): accent effects first (the modifier must be visible), then the
	-- material's own particles. Budgeted separately from the builder's emitters; Instantiate pools/LODs them.
	local effects = {}
	local maxFx = cfg.EffectBudget[style] or 2
	local seenFx: { [string]: boolean } = {}
	local function addFx(e: any)
		if #effects < maxFx and not seenFx[e.id] then
			seenFx[e.id] = true
			local socket = if e.at == "head" then "head" elseif e.at == "mouth" then (if bp.sockets.mouth then "mouth" else "head") elseif e.at == "back" then (if bp.sockets.exhaust then "exhaust" else "core") else "core"
			table.insert(effects, { id = e.id, socket = socket, accent = e.accent, material = e.material })
		end
	end
	for _, e in accentFx do
		addFx(e)
	end
	if matInfo then
		for _, pid in matInfo.particles do
			addFx({ id = pid, at = "body", material = matInfo.id })
		end
	end
	fx.effects = effects
	bp.material = matInfo
	bp.accents = accents
	bp.mood = r.mood or "Neutral"
	if o.budget and o.budget.maxParticles then
		local total = 0
		for _, e in fx.emitters do
			e.rate = math.min(e.rate, math.max(0, o.budget.maxParticles - total))
			total += e.rate
		end
	end
	-- light range scales with the summon
	for _, l in fx.lights do
		l.range = math.clamp((l.range or 1.5) * target, 4, 40)
	end

	mn, mx = bounds(bp.parts)
	bp.bounds = { min = mn, max = mx }
	local bodyBone = bp.bones[1]
	local rootSize = { math.max(0.2, mx[1] - mn[1]), math.max(0.2, mx[2] - mn[2]), math.max(0.2, mx[3] - mn[3]) }
	bp.root = {
		size = rootSize,
		cf = Geom.new((mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2, (mn[3] + mx[3]) / 2),
	}
	if bodyBone == nil then
		table.insert(bp.bones, 1, { name = "Body", parent = nil, pos = { 0, rootSize[2] / 2, 0 } })
	end

	if count > 1 then
		local spacing = math.max(rootSize[1], rootSize[3] * 0.8) * 1.3
		bp.members = formation(count, spacing, rng)
	end

	local emitterRate = 0
	for _, e in fx.emitters do
		emitterRate += e.rate
	end
	bp.stats = {
		parts = #bp.parts,
		partsTotal = #bp.parts * math.max(1, count),
		generated = generated,
		dropped = dropped,
		budget = maxParts,
		detail = detail,
		fixes = fixes,
		bones = #bp.bones,
		emitters = #fx.emitters,
		effects = #fx.effects,
		particleRate = emitterRate,
		trails = #fx.trails,
		lights = #fx.lights,
		members = count,
		meshParts = meshParts,
	}
	return bp
end

function Summon.check(bp: any): { Overlap.Violation }
	return Overlap.check(bp.parts)
end

-- ROBLOX STAGES (lazy so Lune never touches Roblox APIs) ----------------------------------------------------

-- Start loading the sculpted mesh pieces the builder uses (server only, non-yielding, idempotent). Instantiate
-- also calls this on its first build; call it at startup so the first summons already look sculpted.
function Summon.preloadMeshes()
	local Instantiate = require(script.Instantiate) :: any
	Instantiate.preloadMeshes()
end

-- SERVER: start loading the sculpted pieces of the hero model `result` builds as (one pack asset per hero; no-op for
-- words without a hero, or offline). Call it when a summon / mount is cast, before clients build the body: they
-- upgrade from the primitive fallback the moment the pieces replicate. Returns the hero id (or nil).
function Summon.ensureMeshes(result: any): string?
	local id = Heroes.find(result)
	if id then
		local ok, lib = pcall(function(): any
			return require(script.Parent.Meshes.MeshLibrary) :: any
		end)
		if ok and lib and type(lib.loadPack) == "function" then
			local asset = Heroes.pack(id)
			if asset then
				pcall(lib.loadPack, asset)
			end
			-- the element's dressing kit (Heroes.dressingFor) rides on the hero
			local did = Heroes.dressingFor(result.element)
			local dasset = did and Heroes.pack(did)
			if dasset then
				pcall(lib.loadPack, dasset)
			end
		end
	end
	return id
end

-- Use a game's own MeshLibrary-compatible module (same get/place/fit/has/info/preload API) for summon pieces.
function Summon.setMeshLibrary(lib: any)
	local Instantiate = require(script.Instantiate) :: any
	Instantiate.setMeshLibrary(lib)
end

function Summon.build(result: any, opts: any?): any
	local Instantiate = require(script.Instantiate) :: any
	return Instantiate.build(Summon.blueprint(result, opts), result, opts)
end

function Summon.buildBlueprint(bp: any, opts: any?): any
	local Instantiate = require(script.Instantiate) :: any
	return Instantiate.build(bp, nil, opts)
end

function Summon.animate(model: any, result: any): any
	local Animator = require(script.Animator) :: any
	return Animator.new(model, result)
end

return Summon
