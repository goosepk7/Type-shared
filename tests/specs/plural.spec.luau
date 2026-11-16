return function(t)
	local Resolver = t.load("src/Shared/Resolver")
	local Schema = t.load("src/Shared/Schema")

	t.test("plural input becomes a small group", function()
		t.ok(Resolver.resolveLocal("bees").count > 1, "bees")
		t.eq(Resolver.resolveLocal("bee").count, 1)
		t.ok(Resolver.resolveLocal("wolves").count > 1, "wolves")
	end)

	t.test("explicit count wins over plural", function()
		local r = Resolver.resolveLocal("swarm of bees")
		t.ok(r.count > 1)
	end)

	t.test("disasters never multiply", function()
		t.eq(Resolver.resolveLocal("tornadoes").count, 1)
	end)

	t.test("fallback groups are per phrase", function()
		t.ok(Schema.fallback("zzqx").synonymGroup ~= Schema.fallback("qqvv").synonymGroup)
	end)
end
