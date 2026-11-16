-- Summon: determinism, budgets, signatures, materials (construction), accents, faces, split elements, formation,
-- z-fighting checker unit cases, Motion curve math, and Instantiate/Animator structure under @lune/roblox.
local F = require("./summon_fixtures")

return function(t)
	local Schema = t.load("src/Shared/Schema")
	local Summon = t.load("src/Shared/Summon")
	local Overlap = t.load("src/Shared/Summon/Overlap")
	local Geom = t.load("src/Shared/Summon/Geom")
	local Motion = t.load("src/Shared/Summon/Motion")
	local Palette = t.load("src/Shared/Summon/Palette")
	local cfg = Summon.config()

	local function sig(id: string, size: string?)
		for _, s in F.SignatureWords do
			if s[1] == id then
				return F.signatureResult(Schema, s, size)
			end
		end
		error("no signature fixture " .. id)
	end
	local function count(bp, pred)
		local n = 0
		for _, p in bp.parts do
			if pred(p) then
				n += 1
			end
		end
		return n
	end
	local function roleCount(bp, role)
		return count(bp, function(p)
			return p.role == role
		end)
	end

	-- ------------------------------------------------------------ determinism + budgets

	t.test("blueprint is deterministic for (result, seed, style)", function()
		local r = F.synthetic(Schema, "Quadruped", "Large", 2)
		for _, style in { "Solid", "Spectral" } do
			local a = Summon.blueprint(r, { style = style, seed = 7 })
			local b = Summon.blueprint(r, { style = style, seed = 7 })
			t.eq(#a.parts, #b.parts, "part count")
			for i, p in a.parts do
				local q = b.parts[i]
				t.eq(p.name, q.name, "name " .. i)
				for k = 1, 12 do
					t.eq(p.cf[k], q.cf[k], "cf " .. i)
				end
			end
		end
	end)

	t.test("every size respects the part budget (plans, signatures, phrases)", function()
		local report = {}
		for _, size in F.Sizes do
			local maxSeen = 0
			for _, plan in Schema.Enums.BodyPlan do
				local r = if F.Variants[plan] then F.synthetic(Schema, plan, size, 1) else F.special(Schema, plan, size)
				for _, style in { "Solid", "Spectral" } do
					local bp = Summon.blueprint(r, { style = style, seed = 3 })
					t.ok(bp.stats.parts <= bp.stats.budget, r.id .. " " .. size .. " over budget")
					local cap = cfg.PartBudget[size] * (if string.sub(bp.builder, 1, 10) == "signature:" then 1 + cfg.SignatureBonus else 1)
					t.ok(bp.stats.parts <= math.floor(cap), r.id .. " exceeds size budget")
					maxSeen = math.max(maxSeen, bp.stats.parts)
				end
			end
			table.insert(report, size .. "<=" .. maxSeen)
		end
		for _, s in F.SignatureWords do
			local r = F.signatureResult(Schema, s)
			local bp = Summon.blueprint(r, { style = "Spectral" })
			t.ok(bp.stats.parts <= math.floor(cfg.PartBudget[r.size] * (1 + cfg.SignatureBonus)), s[1] .. " signature budget")
		end
	end)

	t.test("opts.budget overrides parts and particles", function()
		local bp = Summon.blueprint(sig("dragon"), { style = "Spectral", budget = { maxParts = 9, maxParticles = 5 } })
		t.ok(#bp.parts <= 9, "maxParts")
		local rate = 0
		for _, e in bp.fx.emitters do
			rate += e.rate
		end
		t.ok(rate <= 5, "maxParticles")
	end)

	t.test("emitter, trail and light budgets per style", function()
		for _, s in F.SignatureWords do
			for _, style in { "Solid", "Spectral" } do
				local bp = Summon.blueprint(F.signatureResult(Schema, s), { style = style })
				t.ok(#bp.fx.emitters <= cfg.EmitterBudget[style], "emitters " .. s[1])
				t.ok(#bp.fx.trails <= cfg.MaxTrails, "trails")
				t.ok(#bp.fx.lights <= cfg.MaxLights, "lights")
				t.ok(#bp.fx.effects <= cfg.EffectBudget[style], "effects")
				for _, e in bp.fx.emitters do
					t.ok(e.rate <= cfg.MaxParticleRate, "rate")
				end
			end
		end
	end)

	t.test("formations reuse one part list and stay in the formation budget", function()
		local r = F.synthetic(Schema, "Insect", "Small", 5)
		r.count = 6
		local bp = Summon.blueprint(r, { style = "Solid" })
		t.eq(#bp.members, 6, "members")
		t.ok(bp.stats.partsTotal <= cfg.PartBudget.Small * cfg.FormationBudgetScale + 6 * cfg.FormationMinParts, "formation total")
	end)

	-- ------------------------------------------------------------ signatures

	t.test("20+ signatures are registered and each fixture uses its signature", function()
		local n = 0
		for _, s in F.SignatureWords do
			local bp = Summon.blueprint(F.signatureResult(Schema, s), { style = "Solid" })
			t.eq(bp.builder, "signature:" .. s[1], "builder for " .. s[1])
			n += 1
		end
		t.ok(n >= 20, "20+ signature fixtures")
		for _, id in { "dragon", "shark", "t rex", "phoenix", "kraken", "golem", "robot", "wizard", "knight", "pirate ship", "tank", "castle", "rocket", "ufo", "cat", "dog", "bee", "octopus", "unicorn", "cannon" } do
			local sid = Summon.signatureFor({ id = id, visual = {} })
			t.eq(sid, id, "registered " .. id)
		end
	end)

	t.test("suffix signature matches respect the body plan (hot dog is not a dog)", function()
		t.eq(Summon.signatureFor({ id = "ice dragon", visual = { bodyPlan = "Dragon" } }), "dragon", "ice dragon")
		t.eq(Summon.signatureFor({ id = "hot dog", visual = { bodyPlan = "Food" } }), nil, "hot dog")
		t.eq(Summon.signatureFor({ id = "ghost pirate ship", visual = { bodyPlan = "Boat" } }), "pirate ship", "two-word suffix")
	end)

	t.test("registerSignature supports custom builders and mesh backing", function()
		Summon.registerSignature("test cube", function(B, _ctx)
			B:block(1, 1, 1, Geom.at(0, 0.5, 0), { role = "body", pri = 1, name = "Cube" })
		end, { plan = "Blob", mesh = { assetId = 123, scale = 1 } })
		local bp = Summon.blueprint({ id = "test cube", size = "Small", element = "None", visual = { bodyPlan = "Blob" } }, { style = "Solid" })
		t.eq(bp.builder, "signature:test cube", "custom signature")
		t.eq(bp.meshAsset and bp.meshAsset.assetId, 123, "mesh asset carried on the blueprint")
	end)

	-- ------------------------------------------------------------ materials

	local function withMaterial(r, id)
		local c = table.clone(r)
		c.material = id
		return c
	end

	t.test("materials reshape construction (both styles, plans and signatures)", function()
		for _, style in { "Solid", "Spectral" } do
			local dragon = Summon.blueprint(withMaterial(sig("dragon"), "spaghetti"), { style = style })
			t.ok(roleCount(dragon, "strand") >= 4, "spaghetti dragon is woven from strands (" .. style .. ")")
			t.ok(roleCount(dragon, "sauce") + roleCount(dragon, "drip") >= 1, "sauce drips")
			t.eq(dragon.material.construction, "Strands", "construction")
			local tank = Summon.blueprint(withMaterial(sig("tank"), "cheese"), { style = style })
			t.ok(roleCount(tank, "hole") >= 2, "cheese tank has holes")
			local wall = Summon.blueprint(withMaterial(F.special(Schema, "Wall", "Large"), "bees"), { style = style })
			t.ok(roleCount(wall, "unit") >= 6, "bee wall is made of bees")
			t.ok(table.find((function()
				local ids = {}
				for _, e in wall.fx.effects do
					table.insert(ids, e.id)
				end
				return ids
			end)(), "bees") ~= nil, "bee wall buzzes")
		end
		local glass = Summon.blueprint(withMaterial(sig("shark"), "glass"), { style = "Solid" })
		t.ok(count(glass, function(p)
			return p.role == "body" and p.transparency >= 0.3 and p.material == "Glass"
		end) >= 1, "glass shark is transparent glass")
		t.ok(roleCount(glass, "shard") >= 2, "glass shards")
	end)

	t.test("every construction kind builds without violations", function()
		for _, id in { "spaghetti", "wicker", "brick", "cardboard", "metal", "jelly", "bees", "glass", "balloons", "coins", "water", "lightning", "gold" } do
			for _, plan in { "Quadruped", "Humanoid", "Vehicle", "Structure" } do
				local r = withMaterial(F.synthetic(Schema, plan, "Large", 1), id)
				for _, style in { "Solid", "Spectral" } do
					local bp = Summon.blueprint(r, { style = style, seed = 2 })
					t.eq(#Summon.check(bp), 0, id .. " " .. plan .. " " .. style)
					t.ok(bp.stats.parts <= bp.stats.budget, "budget")
				end
			end
		end
	end)

	t.test("material provider chain: opts > Library > provider > fallback; unknown is a no-op", function()
		local r = F.synthetic(Schema, "Blob", "Medium", 1)
		local custom = { id = "testium", construction = "Pile", palette = { "#FF00FF", "#00FF00" }, robloxMaterial = "Neon", transparency = 0, glow = 0, particles = {} }
		local bp = Summon.blueprint(r, { style = "Solid", material = custom })
		t.eq(bp.material.id, "testium", "opts.material record")
		Summon.setMaterialProvider(function(id)
			return if id == "zorbium" then custom else nil
		end)
		local bp2 = Summon.blueprint(withMaterial(r, "zorbium"), { style = "Solid" })
		t.eq(bp2.material and bp2.material.construction, "Pile", "provider")
		Summon.setMaterialProvider(nil)
		local bp3 = Summon.blueprint(withMaterial(r, "no such material"), { style = "Solid" })
		t.eq(bp3.material, nil, "unknown material ignored")
	end)

	-- ------------------------------------------------------------ faces, moods, accents, split element

	t.test("creatures get faces; objects only with a mood or silly/cute tags", function()
		local wolf = Summon.blueprint(F.synthetic(Schema, "Quadruped", "Small", 1), { style = "Solid" })
		t.ok(roleCount(wolf, "eye") >= 2, "creature eyes")
		local plain = F.special(Schema, "Furniture", "Medium")
		local bp = Summon.blueprint(plain, { style = "Solid" })
		t.eq(roleCount(bp, "eye"), 0, "plain object stays clean")
		local angry = table.clone(plain)
		angry.mood = "Angry"
		local bp2 = Summon.blueprint(angry, { style = "Solid" })
		t.ok(roleCount(bp2, "eye") >= 2, "angry object gets a face")
		t.ok(roleCount(bp2, "brow") >= 1 or bp2.detail <= 1, "angry brows")
	end)

	t.test("every mood builds a face on a creature and changes it", function()
		local seen = {}
		for _, mood in Schema.Enums.Mood do
			local r = F.synthetic(Schema, "Quadruped", "Large", 6)
			r.mood = mood
			local bp = Summon.blueprint(r, { style = "Solid" })
			t.ok(roleCount(bp, "eye") >= 1, "eyes for " .. mood)
			local sig = {}
			for _, p in bp.parts do
				if p.role == "mouth" or p.role == "brow" or p.role == "lid" or p.role == "pupil" then
					table.insert(sig, p.name .. string.format("%.2f", p.cf[2] + p.size[1]))
				end
			end
			seen[table.concat(sig, ",")] = true
		end
		local n = 0
		for _ in seen do
			n += 1
		end
		t.ok(n >= 8, "moods produce distinct faces (" .. n .. ")")
	end)

	t.test("accents render from the registry; unknown ids are a no-op", function()
		local base = F.synthetic(Schema, "Quadruped", "Large", 1)
		local plainBp = Summon.blueprint(base, { style = "Solid" })
		local r = table.clone(base)
		r.visual = table.clone(base.visual)
		r.visual.accents = { "partyhat", "sunglasses", "steam", "definitely-not-an-accent" }
		local bp = Summon.blueprint(r, { style = "Solid" })
		t.ok(roleCount(bp, "hat") > roleCount(plainBp, "hat"), "party hat")
		t.ok(count(bp, function(p)
			return p.name == "Lens" or p.name == "Lens_2"
		end) >= 1, "sunglasses")
		t.eq(bp.fx.effects[1] and bp.fx.effects[1].id, "anger_steam", "steam effect")
		-- every canonical accent id builds cleanly on a creature and on an object
		local Accents = t.load("src/Shared/Summon/Accents")
		local canonical = t.load("src/Shared/Library/Generated/Modifiers").accents
		for _, a in canonical do
			t.ok(Accents.known(a), "accent registered: " .. a)
			for _, b in { base, F.special(Schema, "Appliance", "Medium") } do
				local x = table.clone(b)
				x.visual = table.clone(b.visual)
				x.visual.accents = { a }
				local abp = Summon.blueprint(x, { style = "Spectral" })
				t.eq(#Summon.check(abp), 0, "accent " .. a .. " on " .. b.id)
			end
		end
	end)

	t.test("accent mouth ids set the face mood when the result is Neutral", function()
		local r = F.synthetic(Schema, "Quadruped", "Large", 1)
		r.visual = table.clone(r.visual)
		r.visual.accents = { "snore" }
		local bp = Summon.blueprint(r, { style = "Solid" })
		t.eq(bp.mood, "Sleepy", "snore -> Sleepy")
	end)

	t.test("secondaryElement gives a split-element look", function()
		local r = F.synthetic(Schema, "Quadruped", "Large", 2)
		local split = table.clone(r)
		split.element, split.secondaryElement = "Fire", "Ice"
		local one = table.clone(r)
		one.element, one.secondaryElement = "Fire", "None"
		for _, style in { "Solid", "Spectral" } do
			local a = Summon.blueprint(split, { style = style })
			local b = Summon.blueprint(one, { style = style })
			local diff = 0
			for i, p in a.parts do
				local q = b.parts[i]
				if q and p.cf[1] < -0.2 and math.abs(Palette.luma(p.colour) - Palette.luma(q.colour)) + math.abs(p.colour[3] - q.colour[3]) > 0.05 then
					diff += 1
				end
			end
			t.ok(diff >= 2, "left half recoloured (" .. style .. ")")
		end
	end)

	-- ------------------------------------------------------------ checker unit cases

	local function block(x, y, z, sx, sy, sz, rx, ry, rz)
		return { shape = "Block", size = { sx, sy, sz }, cf = Geom.at(x, y, z, rx, ry, rz), transparency = 0, name = "B" }
	end

	t.test("checker detects coplanar and coincident surfaces", function()
		t.eq(#Overlap.check({ block(0, 0, 0, 2, 2, 2), block(1, 0, 0, 2, 2, 2) }), 1, "overlapping boxes share top/bottom/front/back? -> faces coplanar")
		t.eq(#Overlap.check({ block(0, 0, 0, 2, 2, 2), block(0, 2, 0, 2, 2, 2) }), 1, "stacked boxes: touching faces coincide")
		t.eq(#Overlap.check({ block(0, 0, 0, 2, 2, 2), block(0, 2.05, 0, 2, 2, 2) }), 0, "gap: fine")
		t.eq(#Overlap.check({ block(0, 0, 0, 2, 2, 2), block(0, 1.9, 0, 1.5, 2, 1.5) }), 0, "inset overlap: fine")
		t.eq(#Overlap.check({ block(0, 0, 0, 2, 2, 2), block(0, 0, 0, 2, 2, 2, 0, math.rad(45), 0) }), 1, "rotated twin shares top and bottom")
		local e1 = { shape = "Ellipsoid", size = { 2, 1, 1 }, cf = Geom.new(0, 0, 0), transparency = 0 }
		local e2 = { shape = "Ellipsoid", size = { 2, 1, 1 }, cf = Geom.new(0, 0, 0), transparency = 0 }
		t.eq(#Overlap.check({ e1, e2 }), 1, "coincident ellipsoids")
		local hidden = block(1, 0, 0, 2, 2, 2)
		hidden.transparency = 1
		t.eq(#Overlap.check({ block(0, 0, 0, 2, 2, 2), hidden }), 0, "invisible parts skipped")
	end)

	t.test("fixer resolves coplanar faces by nudging the less important part", function()
		local a, b = block(0, 0, 0, 2, 2, 2), block(0, 2, 0, 2, 2, 2)
		a.pri, b.pri = 1, 2
		local n = Overlap.fix({ a, b }, 0.02)
		t.ok(n >= 1, "fixed")
		t.eq(#Overlap.check({ a, b }), 0, "no violations after fix")
		t.eq(a.cf[2], 0, "important part untouched")
	end)

	-- ------------------------------------------------------------ motion math

	t.test("easing curves hit their endpoints", function()
		for name, fn in Motion.ease do
			t.ok(math.abs(fn(0)) < 1e-6, name .. "(0)")
			t.ok(math.abs(fn(1) - 1) < 1e-6, name .. "(1)")
		end
		t.ok(Motion.ease.outBack(0.7) > 1, "outBack overshoots")
	end)

	t.test("anticipation dips before the strike and settles", function()
		t.ok(Motion.anticipate(0.25) < 0, "wind-up below zero")
		t.ok(Motion.anticipate(0.55) > 1, "overshoot")
		t.ok(math.abs(Motion.anticipate(1) - 1) < 1e-6, "settles at 1")
		t.ok(math.abs(Motion.strike(0)) < 1e-6 and math.abs(Motion.strike(1)) < 1e-6, "strike returns to rest")
	end)

	t.test("spring converges to its target", function()
		local x, v = 0, 0
		for _ = 1, 600 do
			x, v = Motion.spring(x, v, 1, 120, 22, 1 / 60)
		end
		t.ok(math.abs(x - 1) < 1e-3, "converged")
	end)

	t.test("poses: every gait/clip is finite, deterministic, idle is subtle, die settles", function()
		for _, s in F.SignatureWords do
			local bp = Summon.blueprint(F.signatureResult(Schema, s), { style = "Solid" })
			for clip in Motion.clipLength do
				for _, tt in { 0, 0.13, 0.5, 1.7 } do
					local p1 = Motion.pose(bp.rig, clip, tt, { height = 5 })
					local p2 = Motion.pose(bp.rig, clip, tt, { height = 5 })
					for bone, v in p1 do
						for k = 1, 6 do
							t.ok(v[k] == v[k] and math.abs(v[k]) < 1e4, "finite " .. s[1] .. " " .. clip .. " " .. bone)
							t.eq(v[k], p2[bone][k], "deterministic")
						end
					end
				end
			end
		end
		local rig = { gait = "trot", legs = { { hip = "HipR", side = 1, phase = 0 } } }
		local idle = Motion.pose(rig, "Idle", 0.15, { height = 5 }).HipR[4]
		local move = Motion.pose(rig, "Move", 0.15, { height = 5 }).HipR[4]
		t.ok(math.abs(idle) < math.abs(move), "idle swings less than move")
		local die = Motion.pose({ gait = "static" }, "Die", 5, { height = 5 }).Body
		t.ok(math.abs(die[6] - math.pi * 0.48) < 1e-6, "die ends lying over")
		local wob = Motion.pose({ gait = "static", materialMotion = "wobble" }, "Idle", 0.2, { height = 5 }).Body
		local still = Motion.pose({ gait = "static" }, "Idle", 0.2, { height = 5 }).Body
		t.ok(math.abs(wob[4] - still[4]) > 1e-3, "jelly wobbles")
		local clank = Motion.pose({ gait = "stomp", materialMotion = "clank", legs = { { hip = "H", phase = 0 } } }, "Move", 0.37, { height = 5 }).H
		t.ok(math.abs(clank[4] / 0.06 - math.floor(clank[4] / 0.06 + 0.5)) < 1e-6, "metal motion is stepped")
		t.ok(Motion.moodSpeed("Sleepy") < 1 and Motion.moodSpeed("Hyper") > 1, "mood speed")
	end)

	-- ------------------------------------------------------------ Instantiate under @lune/roblox

	t.test("Instantiate builds a welded Motor6D rig with fx", function()
		local ok, roblox = pcall(require, "@lune/roblox")
		if not ok then
			return
		end
		local Instantiate = t.load("src/Shared/Summon/Instantiate")
		Instantiate.setRuntime({
			Instance = roblox.Instance, CFrame = roblox.CFrame, Vector3 = roblox.Vector3, Vector2 = roblox.Vector2, Color3 = roblox.Color3, Enum = roblox.Enum,
			ColorSequence = roblox.ColorSequence, ColorSequenceKeypoint = roblox.ColorSequenceKeypoint,
			NumberSequence = roblox.NumberSequence, NumberSequenceKeypoint = roblox.NumberSequenceKeypoint, NumberRange = roblox.NumberRange,
		})
		local bp = Summon.blueprint(sig("dragon"), { style = "Spectral" })
		local model = Instantiate.build(bp, sig("dragon"), { effects = false, loadMesh = false })
		t.ok(model.PrimaryPart ~= nil and model.PrimaryPart.Name == "Root", "PrimaryPart root")
		local parts, motors, welds, collide = 0, 0, 0, 0
		local trails, emitters, lights, hl = 0, 0, 0, 0
		for _, d in model:GetDescendants() do
			if d:IsA("BasePart") and d.Name ~= "Root" and string.sub(d.Name, 1, 5) ~= "Bone_" then
				parts += 1
				if d.CanCollide then
					collide += 1
				end
			elseif d:IsA("Motor6D") then
				motors += 1
			elseif d:IsA("Weld") then
				welds += 1
			elseif d:IsA("Trail") then
				trails += 1
			elseif d:IsA("ParticleEmitter") then
				emitters += 1
			elseif d:IsA("PointLight") then
				lights += 1
			elseif d:IsA("Highlight") then
				hl += 1
			end
		end
		t.eq(parts, #bp.parts, "one instance per part")
		t.eq(welds, #bp.parts, "every part welded to a bone")
		t.eq(motors, #bp.bones, "one Motor6D per bone")
		t.eq(collide, 0, "decorative parts never collide")
		t.eq(trails, #bp.fx.trails, "trails")
		t.eq(emitters, #bp.fx.emitters, "emitters")
		t.eq(lights, #bp.fx.lights, "light")
		t.eq(hl, 1, "spectral highlight")
		t.eq(model:GetAttribute("SummonId"), "dragon", "attributes")
		-- formation
		local swarm = sig("bee")
		swarm.count = 4
		local fm = Instantiate.build(Summon.blueprint(swarm, { style = "Solid" }), swarm, { effects = false })
		local members = 0
		for _, c in fm:GetChildren() do
			if c:IsA("Model") then
				members += 1
			end
		end
		t.eq(members, 4, "formation members")
		Instantiate.setRuntime(nil)
	end)
end
