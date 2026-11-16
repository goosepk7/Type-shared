-- Resolver: full library-only pipeline -> WordResult, never nil.
return function(t)
	local Resolver = t.load("src/Shared/Resolver")
	local Schema = t.load("src/Shared/Schema")

	t.test("exact word: no correction, source Library", function()
		local r = Resolver.resolveLocal("asteroid")
		t.eq(r.id, "asteroid")
		t.eq(r.source, "Library")
		t.eq(r.correction, nil)
		t.eq(r.confidence, 1)
		t.eq(r.input, "asteroid")
	end)

	t.test("typo fills correction with alternatives", function()
		local r = Resolver.resolveLocal("elephamt")
		t.eq(r.id, "elephant")
		t.ok(r.correction ~= nil, "correction")
		t.eq(r.correction.to, "elephant")
		t.eq(r.correction.from, "elephamt")
		t.ok(#r.correction.alternatives <= 3)
	end)

	t.test("phrases: modifiers, material, mood, count", function()
		local Library = t.load("src/Shared/Library")
		local state = "zombie"
		for _, s in { "inflatable", "mutant", "zombie", "clockwork" } do
			if Library.lookup(s .. " shark") == nil then
				state = s
				break
			end
		end
		local r = Resolver.resolveLocal("tiny angry golden " .. state .. " shark")
		t.eq(r.canonical, "tiny angry golden " .. state .. " shark")
		t.eq(r.mood, "Angry")
		t.eq(#r.modifiers, 4)
		local s = Resolver.resolveLocal("dragon made out of spagetti")
		t.eq(s.material, "spaghetti")
		t.eq(s.canonical, "spaghetti dragon")
		local c = Resolver.resolveLocal("swarm of bees")
		t.ok(c.count > 1, "count")
		local split = Resolver.resolveLocal("fire ice dragon")
		t.eq(split.element, "Fire")
		t.eq(split.secondaryElement, "Ice")
		local conf = Resolver.resolveLocal("tiny giant shark")
		t.eq(conf.size, "Medium")
		t.eq(conf.mood, "Confused")
	end)

	t.test("fun inputs land on exciting things", function()
		t.eq(Resolver.resolveLocal("small tornado").id, "mini tornado")
		t.ok(Schema.has(Resolver.resolveLocal("small tornado"), "Knockback"), "small tornado flings")
		t.eq(Resolver.resolveLocal("wall made of metal").material, "metal")
		t.ok(Resolver.resolveLocal("spaghetti dragon").synonymGroup ~= Resolver.resolveLocal("dragon").synonymGroup, "material group")
		t.ok(Schema.hasTag(Resolver.resolveLocal("black hole"), "danger"), "danger tag")
		t.ok(Schema.has(Resolver.resolveLocal("small tornado"), "Lifts"), "tornado lifts")
		t.eq(Resolver.resolveLocal("asteroid").size, "Colossal")
	end)

	t.test("never nil; unknown -> Fallback", function()
		for _, s in { "", "qwzxv plorf", "🔥", nil :: any, 42 :: any, string.rep("z", 300) } do
			local r = Resolver.resolveLocal(s)
			t.ok(r ~= nil and r.id ~= nil, "result")
		end
		t.eq(Resolver.resolveLocal("qwzxvplorf").source, "Fallback")
	end)

	t.test("resolveLocalDetailed reports AI need by threshold", function()
		local r, spell, needs = Resolver.resolveLocalDetailed("dragon", 0.6)
		t.eq(r.id, "dragon")
		t.eq(spell.canonical, "dragon")
		t.eq(needs, false)
		local _, _, needs2 = Resolver.resolveLocalDetailed("dragon", 1.01)
		t.eq(needs2, true)
		local _, s3, needs3 = Resolver.resolveLocalDetailed("shark qwzxv plorf")
		t.eq(needs3, true)
		t.ok(#s3.extras >= 1, "extras for the AI")
	end)

	t.test("parse breakdown for the inspector", function()
		local p = Resolver.parse("three tiny angry spaghetti sharks wearing a xyzzq")
		t.eq(p.base, "shark")
		t.eq(p.count, 3)
		t.eq(p.material, "spaghetti")
		t.ok(#p.modifiers >= 3, "mods")
		t.ok(#p.extras >= 1, "extras")
	end)
end
