-- Hero index (Summon/Heroes/Index.luau): the always-loaded id -> family map must match the generated Data/*.luau
-- families exactly, else a hero would not map (or map to the wrong family) until its data happened to load.
-- Fix a failure with: python3 tools/meshgen/heroes/index.py
local fs = require("@lune/fs")

return function(t: any)
	local load = t.load
	local dir = "src/Shared/Summon/Heroes/Data"
	local STALE = " (stale index: run python3 tools/meshgen/heroes/index.py)"

	t.test("Index.luau lists every hero of every Data family with its metadata", function()
		local Index = load("src/Shared/Summon/Heroes/Index")
		local fams = {}
		for _, name in fs.readDir(dir) do
			local f = string.match(name, "^(.+)%.luau$")
			if f then
				table.insert(fams, f)
			end
		end
		table.sort(fams)
		t.eq(table.concat(Index.families, ","), table.concat(fams, ","), "family list" .. STALE)
		local seen = 0
		for _, f in fams do
			for id, def in load(dir .. "/" .. f) do
				local e = Index.heroes[string.lower(id)]
				t.ok(e ~= nil, id .. " missing from the index" .. STALE)
				t.eq(e.f, f, id .. " family" .. STALE)
				t.eq(e.plan, def.plan, id .. " plan" .. STALE)
				t.eq(e.gait, def.gait, id .. " gait" .. STALE)
				t.eq(table.concat(e.tags or {}, ","), table.concat(def.tags or {}, ","), id .. " tags" .. STALE)
				seen += 1
			end
		end
		local n = 0
		for _ in Index.heroes do
			n += 1
		end
		t.eq(n, seen, "index heroes vs data heroes" .. STALE)
	end)

	t.test("hero families load on demand", function()
		-- a fresh module instance (the loader caches per path, so read the module's own bookkeeping)
		local Heroes = load("src/Shared/Summon").Heroes
		local before = #Heroes.loaded()
		t.ok(Heroes.info("lion") ~= nil and Heroes.family("lion") == "felines", "lion indexed as a feline")
		t.ok(Heroes.get("lion") ~= nil and Heroes.get("lion").parts ~= nil, "lion data loads")
		local fams = Heroes.loaded()
		t.ok(table.find(fams, "felines") ~= nil, "felines loaded after get")
		t.ok(#fams >= before, "load order grows")
	end)
end
