return function(t)
	local Schema = t.load("src/Shared/Schema")

	t.test("fallback is valid and never nil", function()
		local r = Schema.fallback("asdfgh")
		t.eq(r.source, "Fallback")
		t.eq(r.element, "Arcane")
		t.ok(#r.flavourText > 0)
	end)

	t.test("repair clamps numbers and maps enums case-insensitively", function()
		local r = Schema.repair({ id = "Dragon", category = "creature", element = "FIRE", size = "huge",
			power = 99, speed = -3, durability = "7", behaviours = { "flies", "Nope", "Burns", "Flies" },
			visual = { primaryColour = "f00", bodyPlan = "quadruped" } })
		t.eq(r.id, "dragon")
		t.eq(r.category, "Creature")
		t.eq(r.element, "Fire")
		t.eq(r.size, "Huge")
		t.eq(r.power, 10)
		t.eq(r.speed, 1)
		t.eq(r.durability, 7)
		t.eq(#r.behaviours, 2)
		t.eq(r.visual.primaryColour, "#FF0000")
		t.eq(r.visual.bodyPlan, "Quadruped")
	end)

	t.test("repair survives garbage", function()
		for _, junk in { nil, 5, "x", {}, { id = 3 }, { id = "", power = 0 / 0 }, { id = "a", visual = "no" } } do
			local r = Schema.repair(junk)
			t.ok(r and r.id, "result")
		end
		local r = Schema.repair({ id = "x", power = 0 / 0, speed = math.huge })
		t.eq(r.power, 5)
		t.eq(r.speed, 5)
	end)

	t.test("forBroadcast strips raw input", function()
		local r = Schema.repair({ id = "cat", input = "secret raw text" })
		t.eq(Schema.forBroadcast(r).input, "")
		t.eq(r.input, "secret raw text")
	end)

	t.test("sizeStep clamps", function()
		t.eq(Schema.sizeStep("Huge", 3), "Colossal")
		t.eq(Schema.sizeStep("Small", -5), "Tiny")
	end)
end
