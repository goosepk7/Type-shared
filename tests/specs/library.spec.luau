-- Library: compiled index integrity, lookups, autocomplete, random(filter), materials.
local process = require("@lune/process")

return function(t)
	local Library = t.load("src/Shared/Library")
	local Schema = t.load("src/Shared/Schema")

	t.test("generated library is not stale", function()
		local r = process.exec("python3", { "tools/build_library.py", "--check" })
		t.ok(r.ok, "build_library.py --check: " .. r.stdout .. r.stderr)
	end)

	t.test("count and ids are sorted and unique", function()
		local ids = Library.ids()
		t.eq(#ids, Library.count())
		t.ok(#ids > 100, "library has entries")
		for i = 2, #ids do
			t.ok(ids[i - 1] < ids[i], "sorted/unique at " .. ids[i])
		end
	end)

	t.test("every entry decodes to a valid WordResult", function()
		local ids = Library.ids()
		for _, id in ids do
			local r = Library.get(id)
			t.ok(r ~= nil, id)
			local _, problems = Schema.validate(r)
			t.eq(#problems, 0, id .. ": " .. table.concat(problems, ", "))
			t.eq(r.source, "Library")
			t.eq(r.mood, "Neutral")
			t.eq(r.secondaryElement, "None")
			t.ok(type(r.visual.accents) == "table", "accents")
			t.ok(string.match(r.visual.primaryColour, "^#%x%x%x%x%x%x$") ~= nil, "colour " .. id)
		end
	end)

	t.test("get returns independent copies", function()
		local a = Library.get("dragon")
		a.power = 99
		a.behaviours[1] = "Nope"
		local b = Library.get("dragon")
		t.ok(b.power <= 10, "template untouched")
		t.ok(b.behaviours[1] ~= "Nope", "behaviours untouched")
		t.eq(Library.get("definitely not a word"), nil)
		t.eq(Library.get(nil :: any), nil)
	end)

	t.test("lookup: id, alias, plural, spacing variants", function()
		t.eq(Library.lookup("dragon"), "dragon")
		t.eq(Library.lookup("Dragons"), "dragon")
		t.eq(Library.lookup("wolves"), "wolf")
		t.eq(Library.lookup("asteroids"), "asteroid")
		t.eq(Library.lookup("  TORNADO "), "tornado")
		t.eq(Library.lookup("twister"), "tornado")
		t.eq(Library.lookup("tornadoes"), "tornado")
		t.eq(Library.lookup("zzqx"), nil)
		-- every authored key resolves to its owner
		local keys, owners = Library.keyArrays()
		for i, k in keys do
			t.eq(Library.lookup(k), Library.idOf(owners[i]), "key " .. k)
		end
	end)

	t.test("joined / hyphenated variants of multi-word keys", function()
		local keys, owners = Library.keyArrays()
		local checked = 0
		for i, k in keys do
			if string.find(k, " ", 1, true) and checked < 200 then
				local joined = string.gsub(k, " ", "")
				local o = Library.keyInfo(joined)
				if o ~= nil then
					checked += 1
				end
			end
		end
		t.ok(checked > 0, "some joined variants resolve")
	end)

	t.test("synonymGroup and signature", function()
		t.eq(Library.synonymGroup("dragon"), Library.get("dragon").synonymGroup)
		t.eq(Library.synonymGroup("qqqq"), nil)
		t.eq(Library.isSignature("dragon"), Library.get("dragon").signature)
		t.eq(Library.isSignature("nope nope"), false)
	end)

	t.test("prefixSearch: ranked, one key per word, fast", function()
		local r = Library.prefixSearch("dra", 5)
		t.ok(#r >= 1 and #r <= 5, "results")
		for _, k in r do
			t.eq(string.sub(k, 1, 3), "dra")
		end
		local owners = {}
		for _, k in Library.prefixSearch("s", 12) do
			local id = Library.lookup(k)
			t.ok(not owners[id], "one key per word: " .. k)
			owners[id] = true
		end
		t.eq(#Library.prefixSearch("", 5), 0)
		t.eq(#Library.prefixSearch("zzzzzz", 5), 0)
		local c = os.clock()
		for i = 1, 200 do
			Library.prefixSearch("ba", 8)
			Library.prefixSearch("fire", 8)
		end
		t.ok((os.clock() - c) / 400 < 0.001, "prefixSearch < 1 ms")
	end)

	t.test("random(filter) matches filters and is deterministic with an rng", function()
		local function rng(seed: number)
			local s = seed
			return {
				NextInteger = function(_, lo: number, hi: number): number
					s = (s * 1103515245 + 12345) % 2147483648
					return lo + s % (hi - lo + 1)
				end,
			}
		end
		local a = Library.random({ element = "Fire", rng = rng(7) :: any })
		local b = Library.random({ element = "Fire", rng = rng(7) :: any })
		t.eq(a.id, b.id)
		t.eq(a.element, "Fire")
		for _ = 1, 30 do
			local r = Library.random({ shape = "Summon", size = "Huge" })
			t.eq(r.shape, "Summon")
			t.eq(r.size, "Huge")
		end
		local s = Library.random({ signatureOnly = true, category = "Creature" })
		t.ok(s.signature and s.category == "Creature", "signature creature")
		local ex = Library.random({ element = "Fire", excludeGroups = { [a.synonymGroup] = true }, rng = rng(7) :: any })
		t.ok(ex.synonymGroup ~= a.synonymGroup, "excluded group")
		t.eq(Library.random({ element = "NotAnElement" }).source, "Fallback")
	end)

	t.test("materials: get and lookup", function()
		local m = Library.material("spaghetti")
		t.ok(m ~= nil, "spaghetti material")
		t.eq(m.id, "spaghetti")
		t.ok(#m.palette >= 2, "palette")
		t.ok(table.isfrozen(m), "shared records are frozen")
		t.eq(Library.lookupMaterial("Pasta"), "spaghetti")
		local id, miss = Library.lookupMaterial("spagetti")
		t.eq(id, "spaghetti")
		t.eq(miss, true)
		t.eq(Library.lookupMaterial("not a material at all"), nil)
		t.eq(Library.material("nope"), nil)
	end)
end
