-- Modifiers: vocabulary, parse, capped apply, contradictions, split elements, materials, visibility.
return function(t)
	local Modifiers = t.load("src/Shared/Modifiers")
	local Library = t.load("src/Shared/Library")
	local Config = t.load("src/Shared/Config")
	local Schema = t.load("src/Shared/Schema")

	local function mods(words: { string })
		local out = {}
		for _, w in words do
			local m = Modifiers.lookup(w) or Modifiers.number(w) or Modifiers.material(Library.lookupMaterial(w) or "")
			assert(m, "no modifier " .. w)
			table.insert(out, m)
		end
		return out
	end

	t.test("vocabulary is large and well-formed", function()
		local all = Modifiers.all()
		t.ok(#all >= 300, "300+ modifiers, got " .. #all)
		local kinds = {}
		local accents = {}
		for _, a in t.load("src/Shared/Library/Generated/Modifiers").accents do
			accents[a] = true
		end
		for _, m in all do
			kinds[m.kind] = (kinds[m.kind] or 0) + 1
			t.ok(Schema.Sets.ModifierKind[m.kind], "kind " .. m.id)
			for _, a in (m :: any).accents or {} do
				t.ok(accents[a], "known accent " .. a)
			end
			for _, b in m.addBehaviours or {} do
				t.ok(Schema.Sets.Behaviour[b], "behaviour " .. b)
			end
			if (m :: any).mood then
				t.ok(Schema.Sets.Mood[(m :: any).mood], "mood " .. m.id)
			end
		end
		for _, k in { "Size", "Count", "Mood", "Quality", "Element", "State", "Motion" } do
			t.ok((kinds[k] or 0) >= 10, k .. " has 10+")
		end
	end)

	t.test("every non-count modifier is visible", function()
		local base = Library.get("shark")
		for _, m in Modifiers.all() do
			if m.kind ~= "Count" then
				local r = Modifiers.apply(base, { m })
				local visible = r.mood ~= base.mood or #r.visual.accents > 0 or r.size ~= base.size
					or r.visual.primaryColour ~= base.visual.primaryColour or r.element ~= base.element
					or r.visual.motionHint ~= base.visual.motionHint or r.visual.secondaryColour ~= base.visual.secondaryColour
				t.ok(visible, "modifier " .. m.id .. " changes nothing visible")
			end
		end
	end)

	t.test("parse: multi-word, numbers, fillers, materials, any order", function()
		local rest, m = Modifiers.parse({ "a", "swarm", "of", "tiny", "angry", "bees" })
		t.eq(#rest, 1)
		t.eq(rest[1], "bees")
		t.eq(m[1].id, "swarm of")
		t.eq(#m, 3)
		local r2, m2 = Modifiers.parse({ "shark", "angry" })
		t.eq(r2[1], "shark")
		t.eq(m2[1].id, "angry")
		local r3, m3 = Modifiers.parse({ "100", "bees" })
		t.eq(m3[1].count, 100)
		t.eq(r3[1], "bees")
		local r4, m4 = Modifiers.parse({ "dragon", "made", "of", "spaghetti" })
		t.eq(r4[1], "dragon")
		t.eq(m4[1].kind, "Material")
		local r5, m5 = Modifiers.parse({ "giant", "fire" })
		t.eq(r5[1], "fire") -- nothing else to be the thing
		t.eq(#m5, 1)
	end)

	t.test("apply: giant fire shark", function()
		local shark = Library.get("shark")
		local r = Modifiers.apply(shark, mods({ "giant", "fire" }))
		t.eq(r.canonical, "giant fire shark")
		t.eq(r.id, "shark")
		t.eq(r.element, "Fire")
		t.eq(r.size, Schema.sizeStep(shark.size, 2))
		t.ok(Schema.has(r, "Burns"), "fire burns")
		t.ok(r.visual.primaryColour ~= shark.visual.primaryColour, "recoloured")
		t.ok(table.find(r.visual.accents, "flames") ~= nil, "flame accents")
		t.eq(#r.modifiers, 2)
		t.eq(r.modifiers[1].kind, "Size")
	end)

	t.test("apply: 4+ stacked, application order, canonical order", function()
		local r = Modifiers.apply(Library.get("shark"), mods({ "zombie", "golden", "angry", "tiny" }))
		t.eq(r.canonical, "tiny angry golden zombie shark")
		t.eq(r.mood, "Angry")
		t.eq(#r.modifiers, 4)
		local order = {}
		for _, m in r.modifiers do
			table.insert(order, Modifiers.KindOrder[m.kind])
		end
		for i = 2, #order do
			t.ok(order[i - 1] <= order[i], "applied in kind order")
		end
	end)

	t.test("caps: stacking cannot break balance", function()
		local cfg = Config.Modifiers
		local base = Library.get("shark")
		local stack = mods({ "colossal", "gargantuan", "titanic", "legendary", "nuclear", "strong", "deadly", "angry" })
		local r = Modifiers.apply(base, stack)
		t.ok(#r.modifiers <= cfg.MaxModifiers, "max modifiers")
		t.ok(r.power - base.power <= cfg.MaxPowerDelta + 1e-9, "power delta cap")
		t.ok(r.power <= 10 and r.speed <= 10 and r.durability <= 10, "stat max")
		local weak = Modifiers.apply(base, mods({ "tiny", "micro", "weak", "broken", "rusty", "sleepy" }))
		t.ok(base.power - weak.power <= cfg.MaxPowerDelta + 1e-9, "negative cap")
		t.ok(weak.power >= 1 and weak.speed >= 1 and weak.durability >= 1, "stat min")
		local army = Modifiers.apply(base, mods({ "million" }))
		t.eq(army.count, math.min(cfg.MaxCount, Schema.Limits.MaxCount))
		t.eq(army.canonical, "million sharks")
		t.ok(#r.behaviours <= Schema.Limits.MaxBehaviours and #r.tags <= Schema.Limits.MaxTags, "list caps")
		t.ok(#r.visual.accents <= cfg.MaxAccents, "accent cap")
	end)

	t.test("contradictions: tiny giant -> Medium + Confused; two elements split", function()
		local r = Modifiers.apply(Library.get("shark"), mods({ "tiny", "giant" }))
		t.eq(r.size, "Medium")
		t.eq(r.mood, "Confused")
		local d = Modifiers.apply(Library.get("dragon"), mods({ "fire", "ice" }))
		t.eq(d.element, "Fire")
		t.eq(d.secondaryElement, "Ice")
		local same = Modifiers.apply(Library.get("dragon"), mods({ "fire", "flaming" }))
		t.eq(same.secondaryElement, "None")
	end)

	t.test("materials: palette, capped stat hints, element affinity", function()
		local dragon = Library.get("dragon")
		local r = Modifiers.apply(dragon, mods({ "spaghetti" }))
		t.eq(r.material, "spaghetti")
		t.eq(r.canonical, "spaghetti dragon")
		t.ok(r.visual.primaryColour ~= dragon.visual.primaryColour, "material recolours")
		local cap = Config.Modifiers.MaterialStatCap
		t.ok(math.abs(r.speed - dragon.speed) <= cap and math.abs(r.durability - dragon.durability) <= cap, "hint cap")
		t.eq(r.element, "Fire", "spaghetti keeps the dragon's element")
	end)

	t.test("apply never mutates the input and tolerates empty/junk", function()
		local shark = Library.get("shark")
		local before = shark.canonical
		Modifiers.apply(shark, mods({ "giant" }))
		t.eq(shark.canonical, before)
		t.eq(Modifiers.apply(shark, {}).canonical, "shark")
		t.eq(Modifiers.apply(shark, { {} :: any, { id = 5 } :: any }).canonical, "shark")
	end)

	t.test("pluralize", function()
		t.eq(Modifiers.pluralize("wolf"), "wolves")
		t.eq(Modifiers.pluralize("fox"), "foxes")
		t.eq(Modifiers.pluralize("puppy"), "puppies")
		t.eq(Modifiers.pluralize("snow man"), "snow men")
		t.eq(Modifiers.pluralize("shark"), "sharks")
	end)
end
