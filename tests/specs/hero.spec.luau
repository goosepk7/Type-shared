-- Hero models (Summon/Heroes): data integrity, mapping, blueprints, authored motion.
return function(t: any)
	local load = t.load
	local Summon = load("src/Shared/Summon")
	local Heroes = Summon.Heroes
	Heroes.setRequirePack(false) -- every authored hero, uploaded or not
	local Map = load("src/Shared/Summon/Heroes/Map")
	local Motion = load("src/Shared/Summon/Motion")

	local function result(id: string, plan: string?, cat: string?): any
		return {
			id = id, canonical = id, category = cat or "Creature", element = "None", size = "Medium", shape = "Summon", tags = {},
			behaviours = {}, modifiers = {}, mood = "Neutral", power = 5, speed = 5, durability = 5,
			visual = { bodyPlan = plan or "Quadruped", primaryColour = "#C8963E", secondaryColour = "#6B4423", motionHint = "Walk", accents = {} },
		}
	end

	t.test("every hero's data is well formed", function()
		local n = 0
		for _, id in Heroes.list() do
			local d = Heroes.get(id)
			n += 1
			local bones = {}
			for i, b in d.bones do
				t.ok(i == 1 or bones[b[2]] ~= nil, id .. ": bone " .. b[1] .. " parent before child")
				bones[b[1]] = true
			end
			t.ok(#d.parts >= 4 and #d.parts <= 60, id .. ": part count " .. #d.parts)
			for _, p in d.parts do
				t.ok(bones[p.bone] ~= nil, id .. ": " .. p.name .. " on a known bone")
				t.ok(#p.size == 3 and #p.pos == 3, id .. ": " .. p.name .. " box")
			end
			for _, clip in { "Idle", "Move" } do
				t.ok(d.clips and d.clips[clip] ~= nil, id .. ": clip " .. clip)
			end
			for name, c in d.clips or {} do
				for bone, tr in c.tracks do
					t.ok(bones[bone] ~= nil, id .. ": clip " .. name .. " bone " .. bone)
					t.eq(#tr, c.keys * 6, id .. ": clip " .. name .. " track length")
				end
			end
		end
		t.ok(n >= 10, "heroes registered")
	end)

	t.test("words map to heroes and the filters hold", function()
		t.eq(Heroes.find(result("lion")), "lion", "lion")
		t.eq(Heroes.find(result("ice tiger")), "tiger", "ice tiger -> tiger")
		t.ok(Heroes.find(result("tiger shark", "Fish")) ~= "tiger", "tiger shark is not a tiger")
		t.eq(Heroes.find(result("hot dog", "Blob", "Food")), nil, "food never maps to an animal")
		t.eq(Map.match("frost lion cub", result("x")), "lion", "trailing words allowed")
		t.eq(Map.match("lion tamer", result("x")), nil, "a different head noun is not a lion")
	end)

	t.test("hero blueprints build, stay deterministic and play their clips", function()
		for _, id in Heroes.list() do
			local r = result(id)
			for _, style in { "Solid", "Spectral" } do
				local a = Summon.blueprint(r, { style = style, seed = 4 })
				local b = Summon.blueprint(r, { style = style, seed = 4 })
				t.eq(a.builder, "hero:" .. id, id .. " builder")
				t.eq(#a.parts, #b.parts, id .. " deterministic")
				t.ok(a.stats.meshParts >= 4, id .. " sculpted parts")
				t.ok(a.rig.clips ~= nil and a.rig.clipScale ~= nil, id .. " clips")
				local pose = Motion.pose(a.rig, "Move", 0.3, { height = 5 })
				t.ok(next(pose) ~= nil, id .. " move pose")
				local hit = Motion.pose(a.rig, "Die", 0.5, { height = 5 })
				t.ok(hit.Body ~= nil, id .. " die pose")
			end
			local low = Summon.blueprint(r, { style = "Solid", budget = { maxParts = 12 } })
			t.ok(#low.parts <= 12, id .. " low budget")
		end
	end)

	t.test("heroes switch off for A/B builds", function()
		local bp = Summon.blueprint(result("lion"), { style = "Solid", heroes = false })
		t.ok(string.sub(bp.builder, 1, 5) ~= "hero:", "opts.heroes = false")
	end)
end
