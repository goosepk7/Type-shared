--!strict
-- MeshMap: which sculpted mesh piece (Meshes/MeshAssets, tools/meshgen) stands in for which primitive part.
-- Pure data: it only writes piece ids onto blueprint parts (`part.mesh`), so Summon.blueprint stays deterministic
-- and Lune-testable. Instantiate swaps a part for its MeshPart when that asset is loaded and keeps the primitive
-- otherwise, so every rule here must name a piece that looks right in the SAME box as the primitive.
--
-- Three sources, in priority order:
--   1. the generator itself: `mesh = "piece"` on a part spec, or B:sculpt(lead, "piece", members) for a sculpt that
--      contains several primitives (a head with its snout); `mesh = false` keeps a part primitive;
--   2. NAMED: exact part names of hero parts (signatures and special plans);
--   3. role + shape rules below (limbs, tails, horns, claws, bevelled hard-surface blocks ...).
--
-- Piece frames (tools/meshgen/README.md): a piece fills the part's box. Segment pieces run along +Y from the
-- thick (root) end to the thin end, like Builder.limb. Wedge pieces fill the WedgePart triangle. Cylinder pieces
-- run along X. Asymmetric pieces have a mirrored "<id>_l" twin for the left copy of a mirrored pair.

local MeshMap = {}

-- Pieces that have a mirrored twin (catalogue: mirror=True).
MeshMap.Left = {
	s_wing_feather = true,
	s_fin_side = true,
	s_wing_bat = true,
	s_dragon_thigh_f = true,
	s_dragon_shin_f = true,
	s_dragon_thigh_h = true,
	s_dragon_shin_h = true,
	s_dragon_c_leg_f = true,
	s_trex_thigh = true,
	s_robot_thigh = true,
	s_robot_shin = true,
	s_robot_arm = true,
	s_robot_fore = true,
	s_horse_thigh_f = true,
	s_horse_shin_f = true,
	s_horse_thigh_h = true,
	s_horse_shin_h = true,
	s_octo_fin = true,
	s_wing_arm = true,
	s_wing_full = true,
	s_wing_flight = true,
	s_golem_arm = true,
	s_golem_fist = true,
	s_golem_thigh = true,
	s_golem_foot = true,
	s_wizard_sleeve = true,
	s_wizard_cuff = true,
	s_knight_cuisse = true,
	s_knight_greave = true,
	s_knight_rerebrace = true,
	s_knight_gauntlet = true,
	s_knight_pauldron = true,
	s_wolf_thigh_f = true,
	s_wolf_shin_f = true,
	s_wolf_thigh_h = true,
	s_wolf_shin_h = true,
	s_trex_shin = true,
	s_trex_arm = true,
	s_dragon_c_leg_h = true,
} :: { [string]: boolean }

-- Pieces from the shared "td" set (uploaded by Type-defend) that the summon builder uses too. Instantiate preloads
-- the "summon" set plus these.
MeshMap.Shared = {
	wheel = true,
	quad_paw = true,
	fish_body = true,
	fish_rear = true,
	bird_body = true,
	insect_thorax = true,
	insect_abdomen = true,
	boulder = true,
	droplet = true,
	biped_pauldron = true,
} :: { [string]: boolean }

-- Part names -> piece (hero parts whose frame the generator fixes). Names are compared without their counters
-- and side letters ("Puff3", "Tower2Roof", "PauldronL" -> "Puff", "TowerRoof", "Pauldron").
local NAMED: { [string]: string } = {
	Puff = "s_puff",
	Canopy = "s_canopy",
	Clump = "s_canopy",
	Petal = "s_petal",
	Turret = "s_turret",
	Thorax = "insect_thorax",
	Abdomen = "insect_abdomen",
}
MeshMap.Named = NAMED

-- "role/Name" -> shape -> piece: the hero pieces of the signature builds and special plans. A piece only stands in
-- for the exact primitive it was sculpted on (same role, name and shape).
local HERO: { [string]: { [string]: string } } = {
	["body/Trunk"] = { Ellipsoid = "s_trunk_y", Cylinder = "s_trunk_x" },
	["body/Rock"] = { Block = "boulder" },
	["detail/Chip"] = { Block = "boulder" },
	["body/Boulder"] = { Ellipsoid = "boulder" },
	["detail/Drop"] = { Ellipsoid = "droplet" },
	["spike/Lick"] = { Ellipsoid = "s_flame_lick" },
	["body/Body"] = { Cylinder = "s_rocket_body" },
	["detail/Nozzle"] = { Cylinder = "s_nozzle" },
	["cannon/Barrel"] = { Cylinder = "s_gun_barrel" },
	["cannon/Muzzle"] = { Cylinder = "s_muzzle" },
	["tread/tread"] = { Block = "s_tread_run", Cylinder = "s_tread_end" },
	["body/Disc"] = { Ellipsoid = "s_saucer" },
	["body/Tower"] = { Cylinder = "s_tower_drum" },
	["roof/TowerRoof"] = { Ellipsoid = "s_roof_cone" },
	["body/Mantle"] = { Ellipsoid = "s_mantle" },
	["hat/HatMid"] = { Ellipsoid = "s_hat_mid" },
	["hat/HatTip"] = { Ellipsoid = "s_hat_tip" },
	["beard/Beard"] = { Ellipsoid = "s_beard" },
	["torso/Robe"] = { Ellipsoid = "s_robe" },
	["hat/Helmet"] = { Ellipsoid = "s_helmet" },
	["armour/Pauldron"] = { Ellipsoid = "biped_pauldron" },
	["blade/Blade"] = { Block = "s_blade" },
	["body/Ring"] = { Ellipsoid = "s_funnel" }, -- tornado funnel segments
	["detail/RingStreak"] = { Ellipsoid = "s_streak" },
	["detail/Debris"] = { Block = "boulder" },
}
MeshMap.Hero = HERO

local function baseName(name: string): (string, string)
	local b = string.gsub(name, "[%d_]+", "")
	local unsided = string.gsub(b, "(%l)[RL]$", "%1")
	return b, unsided
end
MeshMap.baseName = baseName

local function sorted3(s: { number }): (number, number, number)
	local a, b, c = s[1], s[2], s[3]
	if a > b then
		a, b = b, a
	end
	if b > c then
		b, c = c, b
	end
	if a > b then
		a, b = b, a
	end
	return a, b, c
end

-- Bevelled block variant whose own proportions are closest to the part's, so the bevel keeps an even width when
-- the unit mesh is stretched to the part's Size. Variants: each axis short (1) or long (3 / 9).
local function blockPiece(s: { number }): string?
	local lo, _, hi = sorted3(s)
	if lo < 1e-4 or hi / lo > 40 then
		return nil -- paper-thin sheets (sails, membranes) stay primitive
	end
	local id = "s_block_"
	for i = 1, 3 do
		local r = s[i] / lo
		id ..= if r >= 5.2 then "9" elseif r >= 1.75 then "3" else "1"
	end
	return id
end

local function cylPiece(s: { number }): string
	local r = s[1] / math.max(math.min(s[2], s[3]), 1e-6) -- length / diameter
	return if r >= 5 then "s_cyl_pole" elseif r >= 1.6 then "s_cyl_rod" elseif r >= 0.55 then "s_cyl_drum" else "s_cyl_disc"
end

-- true when the part's own axes are the model's (the generator did not rotate it): front is -Z
local function upright(p: any): boolean
	local cf = p.cf
	return cf[4] > 0.97 and cf[8] > 0.97 and cf[12] > 0.97
end

local function thinAxis(s: { number }): number
	if s[1] <= s[2] and s[1] <= s[3] then
		return 1
	end
	return if s[2] <= s[3] then 2 else 3
end

-- role -> shape -> piece id | function(p, ctx) -> id?
local RULES: { [string]: { [string]: any } } = {
	body = {
		Ellipsoid = function(p: any): string?
			if p.seg == "Y" then
				return "s_body_seg"
			end
			return if p.name == "Torso" and not p.mirrored then "s_torso" else nil
		end,
	},
	torso = {
		Ellipsoid = function(p: any): string?
			return if p.name == "Torso" then "s_torso" else nil
		end,
	},
	foot = {
		Ellipsoid = function(p: any): string?
			if p.seg == "Y" then
				return "s_tail_tip" -- toes
			end
			return if upright(p) and p.size[3] > p.size[2] then "quad_paw" else nil
		end,
		Cylinder = "s_hoof",
	},
	ear = {
		Wedge = "s_ear_w",
		Ellipsoid = function(p: any): string?
			return if p.col ~= "inner" and thinAxis(p.size) == 3 then "s_ear_cup" else nil
		end,
	},
	wing = {
		Ellipsoid = function(p: any): string?
			if p.seg == "Y" then
				return "s_limb" -- wing arm bones
			end
			if thinAxis(p.size) ~= 2 or (p.tr or 0) > 0.3 then
				return nil
			end
			if p.col == "membrane" then
				return nil
			end
			return if p.size[3] < p.size[1] * 0.32 then "s_feather" else "s_wing_feather"
		end,
	},
	petal = {
		Ellipsoid = function(p: any): string?
			return if thinAxis(p.size) == 2 and p.size[3] > p.size[1] then "s_petal" else nil
		end,
	},
	limb = {
		Ellipsoid = function(p: any): string?
			return if p.seg == "Y" then "s_limb" else nil
		end,
	},
	tail = {
		Ellipsoid = function(p: any): string?
			if p.seg ~= "Y" or p.glow then
				return nil
			end
			return if p.trail then "s_tail_tip" else "s_tail_seg"
		end,
	},
	tentacle = {
		Ellipsoid = function(p: any): string?
			if p.seg ~= "Y" then
				return nil
			end
			return if p.trail then "s_tail_tip" else "s_tail_seg"
		end,
	},
	horn = {
		Ellipsoid = function(p: any): string?
			if p.seg ~= "Y" then
				return nil
			end
			return if p.trail then "s_horn_tip" else "s_horn_seg"
		end,
	},
	antenna = {
		Ellipsoid = function(p: any): string?
			return if p.seg == "Y" then "s_tail_tip" else nil
		end,
	},
	claw = { Wedge = "s_claw_w" },
	tooth = { Wedge = "s_tooth_w" },
	spike = { Wedge = "s_spike_w" },
	fin = {
		Wedge = "s_fin_w",
		Ellipsoid = function(p: any): string?
			return if thinAxis(p.size) == 2 and p.size[1] > p.size[3] then "s_fin_side" else nil
		end,
	},
	hand = { Ball = "s_fist" },
	wheel = {
		Cylinder = function(p: any): string?
			if p.col == "tyre" then
				return "wheel" -- chunky tyre with tread blocks (shared with Type-defend)
			end
			return "s_hubcap"
		end,
	},
}

-- Roles that are never meshed: the face is built from mood-driven ellipsoids, glows and shells are simple energy.
local SKIP: { [string]: boolean } = {
	eye = true, pupil = true, shine = true, brow = true, lid = true, mouth = true, blush = true, core = true, aura = true,
	shell = true, ring = true, hole = true, bit = true,
}

function MeshMap.pick(p: any, ctx: any): string?
	if SKIP[p.role or ""] then
		return nil
	end
	local base, unsided = baseName(p.name or "")
	local role = p.role or ""
	local hero = HERO[role .. "/" .. base] or HERO[role .. "/" .. unsided]
	if hero and hero[p.shape] then
		return hero[p.shape]
	end
	if role == "body" and base == "Nose" and p.shape == "Ellipsoid" and p.seg == "Y" then
		return "s_nose_cone" -- rocket nose (Builder.limb from the fuselage top)
	end
	local named = NAMED[base]
	if named and (p.shape == "Ellipsoid" or p.shape == "Ball") then
		return named
	end
	local byRole = RULES[p.role or ""]
	local r = byRole and byRole[p.shape]
	if type(r) == "function" then
		r = r(p, ctx)
	end
	if r then
		return r
	end
	-- hard-surface defaults: bevelled blocks and cylinders (flat faces stay on the primitive's faces)
	if p.glow or (p.tr or 0) > 0.3 then
		return nil
	end
	if p.shape == "Block" then
		return blockPiece(p.size)
	elseif p.shape == "Cylinder" then
		return cylPiece(p.size)
	end
	return nil
end

-- Give every part its piece id and remember the shape it was chosen for.
function MeshMap.assign(B: any, ctx: any)
	for _, p in B.parts do
		if p.mesh == nil and p.meshOf == nil then
			p.mesh = MeshMap.pick(p, ctx)
		end
		if p.mesh == false then
			p.mesh = nil
		end
		if p.mesh and p.mirrored and MeshMap.Left[p.mesh] then
			p.mesh ..= "_l"
		end
		p.meshShape = p.shape
		p.meshSize = p.size
	end
end

local function sameProportions(a: { number }, b: { number }): boolean
	local k = (b[1] + b[2] + b[3]) / math.max(a[1] + a[2] + a[3], 1e-9)
	for i = 1, 3 do
		if math.abs(a[i] * k - b[i]) > 0.02 * math.max(b[i], 1e-9) then
			return false
		end
	end
	return true
end

-- After materials and accents: a part that was reshaped (bricks, pixel, panels ...) or rebuilt out of material
-- units keeps its primitive. A sculpt group falls back as a whole when any of its members changed.
function MeshMap.validate(parts: { any })
	local function changed(p: any): boolean
		return p.noMesh == true or (p.meshShape ~= nil and (p.shape ~= p.meshShape or not sameProportions(p.meshSize, p.size)))
	end
	-- Hero sculpts (part.heroSet, e.g. the dragon) are one coherent model cut along the rig: when a material or an
	-- accent takes any piece of it back to a primitive, the whole set steps down to the generic role / shape
	-- pieces, so a hero model never mixes a sculpted hind leg with a reshaped primitive torso. (Materials leave
	-- hero pieces intact, see Materials.apply; this covers accents and styles that reshape parts.)
	local failed: { [string]: boolean } = {}
	for _, p in parts do
		local lead = p.meshOf
		if p.heroSet and p.mesh and changed(p) then
			failed[p.heroSet] = true
		elseif type(lead) == "table" and lead.heroSet and changed(p) then
			failed[lead.heroSet] = true
		end
	end
	local function generic(p: any)
		p.mesh = nil
		if not changed(p) then
			local id = MeshMap.pick(p, nil)
			if id and p.mirrored and MeshMap.Left[id] then
				id ..= "_l"
			end
			p.mesh = id
		end
	end
	if next(failed) then
		for _, p in parts do
			local lead = p.meshOf
			if type(lead) == "table" and lead.heroSet and failed[lead.heroSet] then
				p.meshOf = nil
				generic(p)
			end
		end
		for _, p in parts do
			if p.heroSet and failed[p.heroSet] then
				p.heroSet = nil
				generic(p)
			end
		end
	end
	for _, p in parts do
		if p.mesh and changed(p) then
			p.mesh = nil
		end
	end
	for _, p in parts do
		local lead = p.meshOf
		if type(lead) == "table" and changed(p) then
			lead.mesh = nil
		end
	end
	for _, p in parts do
		local lead = p.meshOf
		if type(lead) == "table" and lead.mesh == nil then
			p.meshOf = nil
		end
	end
end

-- Final pass (after the budget and naming): group members point at their lead by name, or become ordinary parts
-- again when the lead did not survive. Returns the number of parts that carry a mesh piece.
function MeshMap.settle(parts: { any }): number
	local alive: { [any]: boolean } = {}
	for _, p in parts do
		alive[p] = true
	end
	local n = 0
	for _, p in parts do
		local lead = p.meshOf
		if type(lead) == "table" then
			p.meshOf = if alive[lead] and lead.mesh then lead.name else nil
		end
		if p.mesh then
			n += 1
		end
		p.meshShape, p.meshSize, p.noMesh, p.heroSet = nil, nil, nil, nil
		p.heroHull, p.heroKeep = nil, nil
	end
	return n
end

-- Shared by the hero sets: look parts up by name, and lead(part, id, members, hull) assigns one piece of `set`.
-- hull: how much wider than the primitive the sculpt is (material units wrap that hull); nil = the material only
-- recolours this piece (heads, claws, horns stay as modelled). Members inside a sculpt are the first to go when the
-- budget is short (their lead already shows them).
function MeshMap.sculptor(B: any, set: string)
	-- names are not unique yet at this stage (the "_2" suffixes come later): byName is the FIRST part of a name,
	-- named(...) returns every part carrying one of the names
	local byName: { [string]: any } = {}
	for _, p in B.parts do
		if p.name and byName[p.name] == nil then
			byName[p.name] = p
		end
	end
	local function lead(part: any?, id: string, members: { any }?, hull: number?)
		if part == nil then
			return
		end
		local list = {}
		for _, m in members or {} do
			if m ~= nil and m ~= part then
				m.mesh = nil
				table.insert(list, m)
			end
		end
		B:sculpt(part, id, list)
		part.heroSet = set
		part.heroHull = hull
		part.heroKeep = hull == nil
	end
	local function named(...: string): { any }
		local want, out = {}, {}
		for _, n in { ... } do
			want[n] = true
		end
		for _, p in B.parts do
			if p.name and want[p.name] then
				table.insert(out, p)
			end
		end
		return out
	end
	local function on(role: string, bone: string): { any }
		local out = {}
		for _, p in B.parts do
			if p.role == role and p.bone == bone then
				table.insert(out, p)
			end
		end
		return out
	end
	return byName, lead, named, on
end

-- Every piece id the role/shape rules and the name table can produce (tests check them against the manifest).
function MeshMap.ruleIds(): { string }
	local seen: { [string]: boolean } = {}
	for _, id in { "s_torso", "s_body_seg", "quad_paw", "s_hoof", "s_ear_cup", "s_feather", "s_petal", "s_limb", "s_tail_seg", "s_tail_tip", "s_horn_seg", "s_horn_tip", "s_claw_w", "s_tooth_w", "s_spike_w", "s_fin_w", "s_ear_w", "s_fist", "wheel", "s_hubcap",
		"s_cyl_pole", "s_cyl_rod", "s_cyl_drum", "s_cyl_disc" } do
		seen[id] = true
	end
	for _, a in { "1", "3", "9" } do
		for _, b in { "1", "3", "9" } do
			for _, c in { "1", "3", "9" } do
				if a == "1" or b == "1" or c == "1" then
					seen["s_block_" .. a .. b .. c] = true
				end
			end
		end
	end
	for _, id in NAMED do
		seen[id] = true
	end
	for _, byShape in HERO do
		for _, id in byShape do
			seen[id] = true
		end
	end
	seen["s_nose_cone"] = true
	for id in MeshMap.Left do
		seen[id] = true
		seen[id .. "_l"] = true
	end
	local out = {}
	for id in seen do
		table.insert(out, id)
	end
	table.sort(out)
	return out
end

return MeshMap
