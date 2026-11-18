--!strict
-- Hero models: whole summons authored as ONE sculpted model with their own skeleton and keyframed motion
-- (tools/meshgen/heroes, docs/SUMMON.md "Hero models"). They replace the generic plan for every word that maps to
-- one, so a "tiger" is a sculpted tiger with its own walk cycle instead of a quadruped assembled from primitives.
--
--   Heroes.find(result) -> (heroId?, def?)     word -> hero (Map.luau: exact ids, synonym groups, keyword rules)
--   Heroes.build(B, ctx, heroId, def)          fill a Builder from the data (bones, parts, rig, clips, sockets)
--   Heroes.pieces(heroId) -> { pieceId }       mesh pieces a hero uses (to load them on demand)
--   Heroes.list() -> { heroId }
--
-- Data/<family>.luau (generated) = { [heroId] = { plan, gait, bones = { {name, parent, x, y, z} }, parts = { ... },
--   rig = { ... }, sockets = { [name] = { pos, bone } }, clips = { [clip] = { len, loop, keys, tracks } }, mount? } }.
-- A part carries name, bone, shape (primitive fallback), size, pos, rot?, col, mat, pri, role, mesh? ("box" piece
-- filling the part's box), pair?, mirrored?, tr?, glow?, needs?, trail?.

local Geom = require(script.Parent.Geom)

local Heroes = {}

local defs: { [string]: any } = {}
local order: { string } = {}

local dataFolder = script:FindFirstChild("Data")
if dataFolder then
	for _, child in dataFolder:GetChildren() do
		local ok, mod = pcall(require, child)
		if ok and type(mod) == "table" then
			for id, def in mod :: any do
				defs[string.lower(id)] = def
				table.insert(order, string.lower(id))
			end
		end
	end
end
table.sort(order)

local Map: any = nil
local mapMod = script:FindFirstChild("Map")
if mapMod then
	local ok, m = pcall(require, mapMod)
	if ok then
		Map = m
	end
end

local Packs: { [string]: number } = {}
local packsMod = script:FindFirstChild("Packs")
if packsMod then
	local ok, m = pcall(require, packsMod)
	if ok and type(m) == "table" then
		Packs = m :: any
	end
end

local disabled = false
-- Tooling / A-B comparisons: Heroes.setEnabled(false) falls back to the generic plans everywhere.
function Heroes.setEnabled(on: boolean)
	disabled = not on
end

function Heroes.get(id: string): any?
	return defs[string.lower(id)]
end

function Heroes.list(): { string }
	return table.clone(order)
end

local function resolve(id: string?): (string?, any?)
	if id == nil then
		return nil, nil
	end
	local d = defs[id]
	if d then
		return id, d
	end
	return nil, nil
end

-- word -> hero. Order: explicit word map, the id itself, the synonym group, then keyword rules over the words of
-- the id (last word first: "ice tiger" -> tiger, "tiger shark" -> shark), each rule optionally limited to body plans
-- or categories so "hot dog" never becomes a dog.
function Heroes.find(r: any): (string?, any?)
	if disabled or next(defs) == nil then
		return nil, nil
	end
	local id = string.lower(tostring(r.id or ""))
	local words = Map and Map.words or {}
	local hid, def = resolve(words[id])
	if hid then
		return hid, def
	end
	hid, def = resolve(id)
	if hid then
		return hid, def
	end
	local g = r.synonymGroup and string.lower(r.synonymGroup)
	if g then
		hid, def = resolve(words[g])
		if hid then
			return hid, def
		end
		hid, def = resolve(g)
		if hid then
			return hid, def
		end
	end
	if Map and Map.match then
		local m = Map.match(id, r)
		if m then
			return resolve(m)
		end
	end
	return nil, nil
end

function Heroes.pieces(id: string): { string }
	local d = defs[string.lower(id)]
	local out = {}
	if d then
		for _, p in d.parts do
			if p.mesh then
				table.insert(out, p.mesh)
			end
		end
	end
	return out
end

-- The Model asset holding a hero's sculpted pieces (nil until tools/meshgen/heroes/upload.py has uploaded it).
function Heroes.pack(id: string): number?
	return Packs[string.lower(id)]
end

local HULL_ROLES: { [string]: boolean } = { body = true, limb = true, tail = true, neck = true, torso = true, mane = true, wing = true }

-- Fill the builder from a hero definition. Parts that carry a sculpt form one hero set (MeshMap: a material never
-- takes it apart, an accent that reshapes a piece steps the whole set down to primitives).
function Heroes.build(B: any, ctx: any, id: string, def: any)
	local set = "hero:" .. id
	-- bones (data order is parent before child)
	local root = def.bones[1]
	if root and root[1] == "Body" then
		local b = B.boneIndex.Body
		b.pos = { root[3], root[4], root[5] }
	end
	for i = 2, #def.bones do
		local b = def.bones[i]
		B:bone(b[1], b[2] or "Body", b[3], b[4], b[5])
	end
	local detail = ctx.detail or 3
	for _, s in def.parts do
		local rot = s.rot
		local cf = if rot then Geom.at(s.pos[1], s.pos[2], s.pos[3], rot[1], rot[2], rot[3]) else Geom.new(s.pos[1], s.pos[2], s.pos[3])
		local p = B:part({
			name = s.name,
			shape = s.shape,
			size = { s.size[1], s.size[2], s.size[3] },
			cf = cf,
			col = s.col,
			mat = s.mat,
			bone = s.bone,
			-- small detail (shines, claws) slips down the list on low detail budgets
			pri = s.pri + (if detail <= 1 and s.pri >= 2 then 0.5 else 0),
			role = s.role,
			tr = s.tr,
			glow = s.glow,
			trail = s.trail,
			needs = s.needs,
			mesh = s.mesh or false,
			noCore = true,
		})
		if s.pair then
			p.pair = s.pair
		end
		if s.mirrored then
			p.mirrored = true
		end
		if s.mesh then
			p.heroSet = set
			p.heroHull = if HULL_ROLES[s.role] then 1.08 else nil
			p.heroKeep = not HULL_ROLES[s.role]
			p.meshShape = s.shape
			p.meshSize = { s.size[1], s.size[2], s.size[3] }
			p.heroModel = true
		end
	end
	-- rig + motion
	for k, v in def.rig or {} do
		B.rig[k] = v
	end
	B.rig.gait = def.gait or B.rig.gait
	if def.clips then
		B.rig.clips = def.clips
	end
	B.rig.hero = id
	for name, s in def.sockets or {} do
		B:socket(name, Geom.new(s.pos[1], s.pos[2], s.pos[3]), s.bone)
	end
	if def.mount then
		B.rig.mount = def.mount
	end
end

return Heroes
