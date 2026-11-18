-- Sculpted mesh pieces: manifest validity, every piece id the summon builder can reference exists in the manifest,
-- the blueprint stays pure and deterministic, the primitive fallback works without assets and the MeshPart path
-- works with registered stand-ins (under @lune/roblox).
local fs = require("@lune/fs")
local serde = require("@lune/serde")
local F = require("./summon_fixtures")

return function(t)
	local Schema = t.load("src/Shared/Schema")
	local Summon = t.load("src/Shared/Summon")
	local MeshMap = t.load("src/Shared/Summon/MeshMap")
	local Assets = t.load("src/Shared/Meshes/MeshAssets")

	local function sig(word: string, size: string?): any
		for _, sw in F.SignatureWords do
			if sw[1] == word then
				return F.signatureResult(Schema, sw, size)
			end
		end
		error("no signature " .. word)
	end

	local function allResults(): { any }
		local out = {}
		for _, sw in F.SignatureWords do
			table.insert(out, F.signatureResult(Schema, sw))
		end
		for _, plan in Schema.Enums.BodyPlan do
			for v in F.Variants[plan] or {} do
				table.insert(out, F.synthetic(Schema, plan, "Medium", v))
			end
		end
		for plan in F.Special do
			table.insert(out, F.special(Schema, plan, "Large"))
		end
		return out
	end

	t.test("mesh manifest is valid and matches data/mesh_assets.json", function()
		local json = serde.decode("json", fs.readFile("data/mesh_assets.json"))
		local n, summon, tris = 0, 0, 0
		for id, rec in Assets do
			n += 1
			t.ok(type(id) == "string" and #id > 0, "id")
			t.ok(rec.kind == "box" or rec.kind == "anchor" or rec.kind == "unit", id .. " kind")
			t.ok(rec.set == "td" or rec.set == "summon", id .. " set")
			t.ok(type(rec.size) == "table" and #rec.size == 3 and rec.size[1] > 0 and rec.size[2] > 0 and rec.size[3] > 0, id .. " size")
			t.ok(type(rec.origin) == "table" and #rec.origin == 3, id .. " origin")
			t.ok(type(rec.tris) == "number" and rec.tris > 0 and rec.tris <= 4000, id .. " triangle budget")
			t.ok(type(rec.assetId) == "number" and rec.assetId > 0, id .. " uploaded asset id")
			local j = json[id]
			t.ok(j ~= nil and j.assetId == rec.assetId and j.tris == rec.tris, id .. " same as the JSON record")
			if rec.set == "summon" then
				summon += 1
				tris += rec.tris
				t.ok(rec.tris <= (if rec.kind == "unit" then 3200 else 1500), id .. " summon piece budget")
			end
		end
		local jn = 0
		for _ in json do
			jn += 1
		end
		t.eq(n, jn, "same number of records")
		t.ok(summon >= 60, "summon set present")
	end)

	local function usable(id: string): boolean
		local rec = Assets[id]
		if string.sub(id, 1, 2) == "h_" then
			return true -- hero pieces ship in per-hero packs (Heroes/Packs.luau); hero.spec checks them
		end
		return rec ~= nil and (rec.set == "summon" or MeshMap.Shared[id] == true)
	end

	t.test("every piece id the rules can produce is in the manifest and preloaded", function()
		for _, id in MeshMap.ruleIds() do
			t.ok(usable(id), "rule piece " .. id)
		end
		for id in MeshMap.Left do
			t.ok(Assets[id .. "_l"] ~= nil, id .. " has a mirrored twin")
		end
		for id in MeshMap.Shared do
			t.ok(Assets[id] ~= nil and Assets[id].set == "td", id .. " is a shared td piece")
		end
	end)

	t.test("every blueprint references known pieces; sculpt groups resolve; box pieces fill a box", function()
		local total = 0
		for _, r in allResults() do
			for _, style in { "Solid", "Spectral" } do
				for seed = 1, 3 do
					local bp = Summon.blueprint(r, { style = style, seed = seed })
					local byName = {}
					for _, p in bp.parts do
						byName[p.name] = p
					end
					local n = 0
					for _, p in bp.parts do
						if p.mesh ~= nil then
							n += 1
							t.ok(type(p.mesh) == "string" and usable(p.mesh), r.id .. ": piece " .. tostring(p.mesh) .. " on " .. p.name)
						end
						if p.meshOf ~= nil then
							local lead = byName[p.meshOf]
							t.ok(type(p.meshOf) == "string" and lead ~= nil and type(lead.mesh) == "string", r.id .. ": " .. p.name .. " meshOf")
							t.ok(lead == nil or Assets[lead.mesh] == nil or Assets[lead.mesh].kind == "unit", r.id .. ": group lead is a unit sculpt")
						end
						t.ok(p.meshShape == nil and p.meshSize == nil and p.noMesh == nil and p.meshL == nil, "helper fields removed")
					end
					t.eq(bp.stats.meshParts, n, "stats.meshParts")
					total += n
				end
			end
		end
		t.ok(total > 1000, "meshes are assigned")
	end)

	t.test("mesh assignment is deterministic and never changes the primitive build", function()
		for _, r in { sig("dragon"), sig("tank"), sig("wizard"), F.synthetic(Schema, "Quadruped", "Medium", 1) } do
			for _, style in { "Solid", "Spectral" } do
				local a = Summon.blueprint(r, { style = style, seed = 7 })
				local b = Summon.blueprint(r, { style = style, seed = 7 })
				local plain = Summon.blueprint(r, { style = style, seed = 7, meshes = false })
				t.eq(#a.parts, #b.parts, "same part count")
				t.eq(#a.parts, #plain.parts, "meshes = false keeps every part")
				t.eq(plain.stats.meshParts, 0, "meshes = false assigns none")
				for i, p in a.parts do
					local q, o = b.parts[i], plain.parts[i]
					t.ok(p.name == q.name and p.mesh == q.mesh and p.meshOf == q.meshOf, "deterministic " .. p.name)
					t.ok(o.mesh == nil and o.meshOf == nil, "no mesh fields")
					t.ok(p.name == o.name and p.shape == o.shape, "same primitive " .. p.name)
					for k = 1, 3 do
						t.ok(p.size[k] == o.size[k], "same size " .. p.name)
					end
					for k = 1, 12 do
						t.ok(p.cf[k] == o.cf[k] and p.cf[k] == q.cf[k], "same frame " .. p.name)
					end
				end
			end
		end
	end)

	t.test("MeshMap name rules", function()
		local b, u = MeshMap.baseName("Tower2Roof")
		t.eq(b, "TowerRoof", "counter removed")
		b, u = MeshMap.baseName("PauldronL")
		t.eq(u, "Pauldron", "side removed")
		t.eq(MeshMap.pick({ name = "Puff3", role = "body", shape = "Ellipsoid", size = { 2, 2, 2 } }, {}), "s_puff", "numbered name")
		t.eq(MeshMap.pick({ name = "EyeR", role = "eye", shape = "Ellipsoid", size = { 1, 1, 1 } }, {}), nil, "faces stay primitive")
		t.eq(MeshMap.pick({ name = "Sail", role = "sail", shape = "Block", size = { 4, 4, 0.05 } }, {}), nil, "paper-thin sheets stay primitive")
		t.eq(MeshMap.pick({ name = "Hull", role = "body", shape = "Block", size = { 3, 1, 9.2 } }, {}), "s_block_319", "block proportions")
	end)

	t.test("Spectral keeps a solid silhouette (dragon body, neck, limbs, wings)", function()
		for seed = 1, 4 do
			local bp = Summon.blueprint(sig("dragon"), { style = "Spectral", seed = seed, heroes = false })
			local solid, masses, membranes = 0, 0, 0
			for _, p in bp.parts do
				if p.role == "body" or p.role == "head" or p.role == "torso" then
					masses += 1
					t.ok(p.material == "SmoothPlastic" and p.transparency <= 0.2, "mass " .. p.name .. " is solid, got " .. tostring(p.material))
				end
				if p.role == "limb" or p.role == "tail" or p.role == "wing" then
					t.ok(p.material ~= "ForceField" and p.transparency <= 0.3, p.name .. " is part of the silhouette")
					solid += 1
				end
				if p.name == "Membrane" or p.name == "MembraneL" or (string.sub(p.name, 1, 8) == "Membrane") then
					membranes += 1
					t.ok(string.sub(p.mesh or "", 1, 10) == "s_wing_bat", "membrane sculpt")
				end
			end
			t.ok(masses >= 3 and solid >= 8, "dragon silhouette parts")
			t.eq(membranes, 2, "both wing membranes survive the part budget")
			t.ok(bp.fx.highlight ~= nil, "glow stays as a rim accent")
		end
	end)

	t.test("Vortex: every ring is its own rotor, alternating direction, with debris and swirl emitters", function()
		local Motion = t.load("src/Shared/Summon/Motion")
		local r
		for _, plan in Schema.Enums.BodyPlan do
			for v, var in F.Variants[plan] or {} do
				if var[1] == "tornado" then
					r = F.synthetic(Schema, plan, "Medium", v)
				end
			end
		end
		t.ok(r ~= nil, "tornado fixture")
		for _, style in { "Solid", "Spectral" } do
			local bp = Summon.blueprint(r, { style = style, seed = 2 })
			local pos, neg, speeds = 0, 0, {}
			for _, rot in bp.rig.rotors do
				if string.sub(rot.bone, 1, 4) == "Ring" then
					if rot.speed > 0 then
						pos += 1
					else
						neg += 1
					end
					speeds[rot.speed] = true
				end
			end
			local distinct = 0
			for _ in speeds do
				distinct += 1
			end
			t.ok(pos >= 2 and neg >= 2, style .. ": rings turn both ways")
			t.ok(distinct >= 4, style .. ": rings turn at different speeds")
			local streaks, debris = 0, 0
			for _, p in bp.parts do
				if string.find(p.name, "Streak") then
					streaks += 1
				elseif string.sub(p.name, 1, 6) == "Debris" then
					debris += 1
				end
			end
			t.ok(streaks >= 4, style .. ": wind streaks make the rotation readable")
			t.ok(debris >= 3, style .. ": debris ring")
			t.ok(#bp.fx.emitters >= 2, style .. ": swirl emitters")
			local a = Motion.pose(bp.rig, "Idle", 0.5, { height = 5 })
			t.ok(a.Ring1 ~= nil and a.Ring2 ~= nil and a.Ring1[5] * a.Ring2[5] < 0, style .. ": neighbouring rings counter-rotate while idle")
			t.ok(a.Debris ~= nil and math.abs(a.Debris[5]) > 0.5, style .. ": debris orbits")
		end
	end)

	t.test("hero sculpts: dragon and shark are cut along the rig and fall back as a whole", function()
		-- this test covers the procedural sculpts; hero packs are checked by hero.spec
		local Summon = setmetatable({ blueprint = function(b, o) o = table.clone(o or {}); if o.heroes == nil then o.heroes = false end; return Summon.blueprint(b, o) end }, { __index = Summon })
		local function leads(bp: any, prefix: string): (number, { [string]: boolean })
			local n, bones = 0, {}
			for _, p in bp.parts do
				if type(p.mesh) == "string" and string.sub(p.mesh, 1, #prefix) == prefix then
					n += 1
					bones[p.bone or "Body"] = true
					t.ok(Assets[p.mesh] ~= nil and Assets[p.mesh].kind == "unit", p.mesh .. " is a unit sculpt")
					t.ok(Assets[p.mesh].tris <= 4000, p.mesh .. " stays under 4k triangles")
				end
			end
			return n, bones
		end
		for _, style in { "Solid", "Spectral" } do
			for seed = 1, 3 do
				local bp = Summon.blueprint(sig("dragon"), { style = style, seed = seed })
				local n, bones = leads(bp, "s_dragon_")
				t.ok(n >= 14, style .. " dragon hero pieces, got " .. n)
				for _, b in { "Body", "Neck", "Head", "Jaw", "HipFR", "KneeFR", "HipBL", "KneeBL", "Tail1", "Tail3" } do
					t.ok(bones[b], "dragon piece on bone " .. b)
				end
				local tris = 0
				for _, p in bp.parts do
					if p.mesh then
						tris += Assets[p.mesh].tris
					end
				end
				t.ok(tris < 30000, "dragon triangle total " .. tris)
				local sb = Summon.blueprint(sig("shark"), { style = style, seed = seed, heroes = false })
				local ns = leads(sb, "s_shark_")
				t.ok(ns == 4 or (style == "Spectral" and ns == 5), style .. " shark hero pieces (Spectral adds the aura shell), got " .. ns)
			end
		end
		-- materials never take a hero sculpt apart: surface materials (glass, metal, gold, ice ...) recolour the
		-- full sculpt, strand / pile constructions lay their units round it and leave head, horns and claws alone
		local function has(bp: any, id: string): boolean
			for _, p in bp.parts do
				if p.mesh == id then
					return true
				end
			end
			return false
		end
		for _, mat in { "spaghetti", "glass", "crystal", "metal", "gold", "ice", "jelly", "chocolate", "coins", "yarn", "lightning", "leaves", "cotton candy", "honey", "bread" } do
			for _, style in { "Solid", "Spectral" } do
				local r = sig("dragon")
				r.material = mat
				local bp = Summon.blueprint(r, { style = style, seed = 1, heroes = false })
				for _, id in { "s_dragon_body", "s_dragon_neck", "s_dragon_head", "s_dragon_horns", "s_dragon_shin_f", "s_dragon_shin_h_l", "s_dragon_tail1", "s_wing_bat" } do
					t.ok(has(bp, id), mat .. " dragon (" .. style .. ") keeps " .. id)
				end
				t.eq(#Summon.check(bp), 0, mat .. " dragon z-fighting")
				for _, p in bp.parts do
					t.ok(p.heroHull == nil and p.heroKeep == nil and p.heroProxy == nil, "helper fields cleared")
				end
				local g = sig("shark")
				g.material = mat
				local gb = Summon.blueprint(g, { style = style, seed = 1, heroes = false })
				t.ok(leads(gb, "s_shark_") >= 4, mat .. " shark (" .. style .. ") keeps the sculpt")
				t.eq(#Summon.check(gb), 0, mat .. " shark z-fighting")
			end
		end
		-- small and medium dragons: the compact set on the low-detail layout, never the generic blocks
		for _, style in { "Solid", "Spectral" } do
			local small = Summon.blueprint(sig("dragon", "Small"), { style = style, seed = 1, heroes = false })
			for _, id in { "s_dragon_c_body", "s_dragon_c_leg_f", "s_dragon_c_leg_h_l", "s_dragon_head", "s_dragon_c_horns", "s_dragon_c_tail", "s_wing_bat", "s_wing_bat_l" } do
				t.ok(has(small, id), "small dragon (" .. style .. ") has " .. id)
			end
			t.eq(#Summon.check(small), 0, "small dragon z-fighting")
			local medium = Summon.blueprint(sig("dragon", "Medium"), { style = style, seed = 1, heroes = false })
			local pupils = 0
			for _, p in medium.parts do
				if p.role == "pupil" then
					pupils += 1
				end
			end
			t.ok(pupils == 0 or pupils == 2, "medium dragon is never one-eyed")
			t.ok(has(medium, "s_dragon_c_tail") or (has(medium, "s_dragon_tail1") and has(medium, "s_dragon_tail3")), "medium dragon (" .. style .. ") keeps its whole tail")
		end
		local tiny = sig("dragon", "Small")
		tiny.material = "spaghetti"
		local tb = Summon.blueprint(tiny, { style = "Solid", seed = 1, heroes = false })
		t.ok(has(tb, "s_dragon_c_body") and (has(tb, "s_dragon_c_legs_f") or has(tb, "s_dragon_c_leg_f")), "small spaghetti dragon keeps the compact sculpt")
		-- t rex (signature) and wolf (canine archetype of the Quadruped plan)
		for _, style in { "Solid", "Spectral" } do
			local rex = Summon.blueprint(sig("t rex"), { style = style, seed = 1, heroes = false })
			for _, id in { "s_trex_body", "s_trex_neck", "s_trex_head", "s_trex_jaw", "s_trex_thigh", "s_trex_shin_l", "s_trex_arm", "s_trex_tail1", "s_trex_tail3" } do
				t.ok(has(rex, id), "t rex (" .. style .. ") has " .. id)
			end
			local _, rexBones = leads(rex, "s_trex_")
			for _, bone in { "Body", "Neck", "Head", "Jaw", "HipR", "KneeL", "Tail1", "Tail3" } do
				t.ok(rexBones[bone], "t rex sculpt has a piece on bone " .. bone)
			end
			t.eq(#Summon.check(rex), 0, "t rex z-fighting")
			local wolf
			for v, var in F.Variants.Quadruped do
				if var[1] == "wolf" then
					wolf = Summon.blueprint(F.synthetic(Schema, "Quadruped", "Large", v), { style = style, seed = 1, heroes = false })
				end
			end
			t.ok(wolf ~= nil, "wolf fixture")
			for _, id in { "s_wolf_body", "s_wolf_neck", "s_wolf_thigh_f", "s_wolf_shin_f_l", "s_wolf_thigh_h_l", "s_wolf_shin_h", "s_wolf_tail1", "s_wolf_tail2", "s_wolf_head" } do
				t.ok(has(wolf, id), "wolf (" .. style .. ") has " .. id)
			end
			t.eq(#Summon.check(wolf), 0, "wolf z-fighting")
		end
		-- knight: full harness, nothing of the budget wasted on hidden primitives
		for _, style in { "Solid", "Spectral" } do
			local kn = Summon.blueprint(sig("knight"), { style = style, seed = 1, heroes = false })
			for _, id in { "s_knight_cuirass", "s_knight_fauld", "s_knight_cuisse", "s_knight_greave_l", "s_knight_rerebrace", "s_knight_gauntlet_l", "s_knight_pauldron",
				"s_knight_pauldron_l", "s_knight_helm", "s_knight_plume", "s_sword", "s_knight_shield", "s_cape", "s_knight_cross" } do
				t.ok(has(kn, id), "knight (" .. style .. ") has " .. id)
			end
			local pupils = 0
			for _, p in kn.parts do
				if p.role == "pupil" then
					pupils += 1
				end
			end
			t.eq(pupils, 2, "knight has both pupils")
			t.eq(#Summon.check(kn), 0, "knight z-fighting")
		end
		-- wizard: robe, hat and staff are single sculpts
		for _, style in { "Solid", "Spectral" } do
			local wz = Summon.blueprint(sig("wizard"), { style = style, seed = 1, heroes = false })
			for _, id in { "s_wizard_robe", "s_wizard_top", "s_wizard_sleeve", "s_wizard_cuff_l", "s_wizard_hat", "s_wizard_beard", "s_wizard_staff", "s_cape" } do
				t.ok(has(wz, id), "wizard (" .. style .. ") has " .. id)
			end
			t.eq(#Summon.check(wz), 0, "wizard z-fighting")
		end
		-- further full sculpts: every listed piece present, no z-fighting, phone triangle budget
		local sculpted = {
			robot = { "s_robot_chest", "s_robot_pelvis", "s_robot_head", "s_robot_thigh", "s_robot_shin_l", "s_robot_arm", "s_robot_fore_l" },
			unicorn = { "s_horse_body", "s_horse_neck", "s_horse_mane", "s_horse_thigh_f", "s_horse_shin_f_l", "s_horse_thigh_h_l", "s_horse_shin_h", "s_horse_tail1", "s_horse_tail2", "s_unicorn_horn", "s_unicorn_lock" },
			kraken = { "s_octo_mantle", "s_octo_head", "s_octo_arm1", "s_octo_arm2", "s_octo_rear", "s_octo_arm3", "s_octo_fin", "s_octo_fin_l" },
			octopus = { "s_octo_mantle", "s_octo_head", "s_octo_arm1" },
			castle = { "s_castle_keep", "s_castle_tower", "s_castle_roof", "s_castle_gate" },
			["pirate ship"] = { "s_ship_hull", "s_ship_stern", "s_ship_sail", "s_ship_jib" },
			tank = { "s_tank_hull" },
			phoenix = { "s_wing_arm", "s_wing_arm_l", "s_wing_flight", "s_wing_flight_l" },
			golem = { "s_golem_body", "s_golem_head", "s_golem_arm", "s_golem_fist_l", "s_golem_thigh", "s_golem_foot_l", "s_golem_club" },
		}
		for word, ids in sculpted do
			for _, style in { "Solid", "Spectral" } do
				local bp = Summon.blueprint(sig(word), { style = style, seed = 1, heroes = false })
				for _, id in ids do
					t.ok(has(bp, id), word .. " (" .. style .. ") has " .. id)
				end
				t.eq(#Summon.check(bp), 0, word .. " z-fighting")
			end
		end
		-- the horse family shares the unicorn's body sculpt (and a maned horse wears a crest mane, not a lion collar)
		for _, e in F.library(Schema) do
			if e.id == "horse" then
				local hb = Summon.blueprint(e, { style = "Solid", seed = 1 })
				for _, id in { "s_horse_body", "s_horse_neck", "s_horse_mane", "s_horse_thigh_f", "s_horse_tail2", "s_hoof" } do
					t.ok(has(hb, id), "horse has " .. id)
				end
				t.ok(not has(hb, "s_unicorn_horn"), "horse has no horn")
				t.eq(#Summon.check(hb), 0, "horse z-fighting")
			end
		end
		-- black hole: reads standing still (photon ring, jets, layered discs, infalling debris)
		local hole
		for _, e in F.library(Schema) do
			if e.id == "black hole" then
				hole = Summon.blueprint(e, { style = "Solid", seed = 1 })
			end
		end
		if hole then
			t.ok(has(hole, "s_photon_ring") and has(hole, "s_accretion"), "black hole has its photon ring and discs")
			t.ok(hole.stats.meshParts >= 5, "black hole is not thin: " .. hole.stats.meshParts .. " mesh parts")
			t.eq(#Summon.check(hole), 0, "black hole z-fighting")
		end
		local sp = sig("dragon")
		sp.material = "spaghetti"
		local spb = Summon.blueprint(sp, { style = "Solid", seed = 1 })
		t.ok(leads(spb, "s_noodle_wrap") >= 3, "spaghetti dragon is wound in noodles")
		local gl = sig("shark")
		gl.material = "glass"
		local glb = Summon.blueprint(gl, { style = "Solid", seed = 1 })
		for _, p in glb.parts do
			if p.mesh == "s_shark_body" then
				t.ok((p.transparency or 0) > 0.2, "glass shark body is see-through")
			end
		end
	end)

	t.test("Instantiate: primitives without assets, MeshParts with them, hot swap", function()
		local ok, roblox = pcall(require, "@lune/roblox")
		if not ok then
			return
		end
		local rt = {
			Instance = roblox.Instance, CFrame = roblox.CFrame, Vector3 = roblox.Vector3, Vector2 = roblox.Vector2, Color3 = roblox.Color3, Enum = roblox.Enum,
			ColorSequence = roblox.ColorSequence, ColorSequenceKeypoint = roblox.ColorSequenceKeypoint,
			NumberSequence = roblox.NumberSequence, NumberSequenceKeypoint = roblox.NumberSequenceKeypoint, NumberRange = roblox.NumberRange,
		}
		local Instantiate = t.load("src/Shared/Summon/Instantiate")
		local Lib = t.load("src/Shared/Meshes/MeshLibrary")
		Instantiate.setRuntime(rt)
		Lib.setRuntime(rt)
		Lib.clear()
		Instantiate.setMeshLibrary(Lib)
		local r = sig("dog")
		local bp = Summon.blueprint(r, { style = "Solid", seed = 3 })
		t.ok(bp.stats.meshParts > 0, "the dog has sculpted parts")

		local function census(model: any): (number, number)
			local parts, meshes = 0, 0
			for _, d in model:GetDescendants() do
				if d:IsA("BasePart") and d.Name ~= "Root" and string.sub(d.Name, 1, 5) ~= "Bone_" then
					parts += 1
					if d:IsA("MeshPart") then
						meshes += 1
					end
				end
			end
			return parts, meshes
		end

		-- 1. nothing loaded: the whole primitive build
		local plain = Instantiate.build(bp, r, { effects = false })
		local parts, meshes = census(plain)
		t.eq(parts, #bp.parts, "fallback: one primitive per part")
		t.eq(meshes, 0, "fallback: no MeshPart")

		-- 2. stand-in templates registered: leads become MeshParts, their group members are not built
		local ids = {}
		for _, p in bp.parts do
			if p.mesh then
				ids[p.mesh] = true
			end
		end
		for id in ids do
			local mp = roblox.Instance.new("MeshPart")
			mp.Size = roblox.Vector3.new(1, 1, 1)
			Lib.register(id, mp)
		end
		local members = 0
		for _, p in bp.parts do
			if p.meshOf then
				members += 1
			end
		end
		local model = Instantiate.build(bp, r, { effects = false })
		parts, meshes = census(model)
		t.eq(meshes, bp.stats.meshParts, "every sculpted part is a MeshPart")
		t.eq(parts, #bp.parts - members, "group members are replaced by their lead's sculpt")
		for _, d in model:GetDescendants() do
			if d:IsA("MeshPart") then
				t.ok(d.Size.X > 0 and d.Size.Y > 0 and d.Size.Z > 0, "sized")
				t.ok(not d.CanCollide, "decorative")
			end
		end
		-- 3. meshes = false keeps primitives even when assets are loaded
		local off = Instantiate.build(bp, r, { effects = false, meshes = false })
		parts, meshes = census(off)
		t.eq(meshes, 0, "meshes = false")
		t.eq(parts, #bp.parts, "meshes = false: all primitives")
		-- 4. a model built before the assets arrived is upgraded in place
		local n = Instantiate.upgradeMeshes(plain, bp, { effects = false })
		parts, meshes = census(plain)
		t.eq(meshes, bp.stats.meshParts, "hot swap: MeshParts")
		t.eq(parts, #bp.parts - members, "hot swap: members removed")
		t.ok(n > 0, "hot swap count")

		Lib.clear()
		Lib.setRuntime(nil)
		Instantiate.setMeshLibrary(nil)
		Instantiate.setRuntime(nil)
	end)
end
