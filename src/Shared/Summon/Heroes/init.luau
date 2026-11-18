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
				if def.plan ~= "Dressing" then -- kits ride on heroes (Heroes.dressingFor), they are not bodies
					table.insert(order, string.lower(id))
				end
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
local requirePack = true
-- Tooling: let heroes without an uploaded pack map too (previews of unuploaded work).
function Heroes.setRequirePack(on: boolean)
	requirePack = on
end
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
	-- a hero whose sculpted pieces were never uploaded would only show its primitive stand-ins: leave the word to
	-- the generic plan until its pack exists (tooling with no Packs at all still sees every hero)
	if d and d.plan ~= "Dressing" and (Packs[id] ~= nil or next(Packs) == nil or requirePack == false) then
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


-- ── element dressing ─────────────────────────────────────────────────────────
-- An elemental creature ("ice tiger", "fire wolf", "stone bear") wears its element's sculpted kit (Data/dressing,
-- tools/meshgen/heroes/h_dressing.py): a back crest, a head piece, a tail tip, shoulder pieces and front cuffs, so
-- element variants differ in shape, not only in colour. Kit pieces are authored in a unit box and fitted here to the
-- hero's own torso / head / tail / feet boxes (model space), riding the bone of the part they sit on.
local DRESS_KIT: { [string]: string } = {
	Fire = "fire", Ice = "ice", Lightning = "lightning", Earth = "earth", Stone = "earth", Nature = "nature",
	Water = "water", Wind = "wind", Shadow = "shadow", Light = "light", Arcane = "arcane", Poison = "poison",
	Metal = "metal",
}
local NO_DRESS: { [string]: boolean } = { Vehicle = true, Dressing = true }

local function box(p: any)
	return p.pos[1], p.pos[2], p.pos[3], p.size[1], p.size[2], p.size[3]
end

local function biggest(parts: { any }, test: (any) -> boolean): any?
	local best, bv = nil, 0
	for _, p in parts do
		if test(p) then
			local v = p.size[1] * p.size[2] * p.size[3]
			if v > bv then
				best, bv = p, v
			end
		end
	end
	return best
end

function Heroes.dressingFor(element: string?): (string?, any?)
	local k = element and DRESS_KIT[element]
	if not k then
		return nil, nil
	end
	local id = "dressing_" .. k
	return id, defs[id]
end

local function dress(B: any, ctx: any, def: any, set: string)
	if NO_DRESS[def.plan or ""] or (ctx.detail or 3) <= 0 then
		return
	end
	local r = ctx.result or {}
	local kid, kit = Heroes.dressingFor(r.element)
	-- no uploaded kit = its pieces would only ever show as stand-in blobs
	if not kit or (requirePack ~= false and next(Packs) ~= nil and Packs[kid :: string] == nil) then
		return
	end
	local parts = def.parts
	local torso = biggest(parts, function(p)
		return p.role == "body" or p.role == "torso"
	end)
	if not torso then
		return
	end
	local head = biggest(parts, function(p)
		local n = string.lower(p.name)
		return (p.role == "head" or string.find(n, "head", 1, true) ~= nil) and not string.find(n, "dress", 1, true)
	end)
	local tail: any = nil
	for _, p in parts do
		if p.role == "tail" and (tail == nil or p.pos[3] > tail.pos[3]) then
			tail = p
		end
	end
	-- front feet: the lowest limb pieces in the front half of the body (-Z is the front)
	local feet = {}
	local tx, ty, tz, tw, th, tl = box(torso)
	for _, p in parts do
		local n = string.lower(p.name)
		if (p.role == "foot" or string.find(n, "paw", 1, true) or string.find(n, "hoof", 1, true) or string.find(n, "foot", 1, true))
			and p.pos[3] < tz then
			table.insert(feet, p)
		end
	end
	table.sort(feet, function(a, b)
		return a.pos[1] < b.pos[1]
	end)
	local function put(k: any, bone: string, size: { number }, pos: { number }, mirrored: boolean?)
		local pr = B:part({
			name = "Dress" .. k.name,
			shape = k.shape,
			size = size,
			cf = Geom.new(pos[1], pos[2], pos[3]),
			col = k.col,
			mat = k.mat,
			bone = bone,
			pri = 2.2,
			role = k.role,
			mesh = k.mesh or false,
			noCore = true,
		})
		if k.mesh then
			pr.heroSet = set
			pr.heroKeep = true
			pr.meshShape = k.shape
			pr.meshSize = size
			pr.heroModel = true
		end
		if mirrored then
			pr.mirrored = true
		end
	end
	for _, k in kit.parts do
		local sx, sy, sz = k.size[1], k.size[2], k.size[3]
		local a = (kit.rig and kit.rig.anchors or {})[k.name]
		if a == "back" then
			local w = tw * 0.55
			-- the torso box top sits above the rounded spine: seat the crest's base a little into the back
			put(k, torso.bone, { sx * w, sy * w, sz * tl * 0.7 }, { tx, ty + th * 0.36 + sy * w * 0.3, tz })
		elseif a == "head" and head then
			local hx, hy, hz, hw, hh = box(head)
			local w = hw * 0.8
			put(k, head.bone, { sx * w, sy * w, sz * w }, { hx, hy + hh / 2 + sy * w * 0.3, hz })
		elseif a == "tail" and tail then
			local x, y, z, w, h, l = box(tail)
			local s = math.max(w, h) * 1.7
			put(k, tail.bone, { sx * s, sy * s, sz * s }, { x, y, z + l / 2 + sz * s * 0.25 })
		elseif a == "shoulder" then
			local right = k.name == "ShoulderR"
			local s = tw * 0.42
			local x = tx + (if right then 1 else -1) * (tw / 2 - sx * s * 0.2)
			put(k, torso.bone, { sx * s, sy * s, sz * s }, { x, ty + th * 0.3, tz - tl * 0.3 }, not right and k.mirrored)
		elseif a == "foot" then
			for i, f in feet do
				if i > 2 then
					break
				end
				local x, y, z, w, h, l = box(f)
				local s = math.max(w, l) * 1.35
				put(k, f.bone, { sx * s, sy * s, sz * s }, { x, y + h * 0.55, z })
			end
		end
	end
end

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
	dress(B, ctx, def, set)
end

return Heroes
