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

	local function sig(word: string): any
		for _, sw in F.SignatureWords do
			if sw[1] == word then
				return F.signatureResult(Schema, sw)
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
			t.ok(type(rec.tris) == "number" and rec.tris > 0 and rec.tris <= 2200, id .. " triangle budget")
			t.ok(type(rec.assetId) == "number" and rec.assetId > 0, id .. " uploaded asset id")
			local j = json[id]
			t.ok(j ~= nil and j.assetId == rec.assetId and j.tris == rec.tris, id .. " same as the JSON record")
			if rec.set == "summon" then
				summon += 1
				tris += rec.tris
				t.ok(rec.tris <= 1500, id .. " summon piece budget")
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
			local bp = Summon.blueprint(sig("dragon"), { style = "Spectral", seed = seed })
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
