-- Speller: pipeline stages, phrase parser, Metaphone parity with the build, cache, and the golden typo set.
local fs = require("@lune/fs")

return function(t)
	local Speller = t.load("src/Shared/Speller")
	local Resolver = t.load("src/Shared/Resolver")
	local Library = t.load("src/Shared/Library")
	local Metaphone = t.load("src/Shared/Speller/Metaphone")
	local Distance = t.load("src/Shared/Speller/Distance")
	local Stemmer = t.load("src/Shared/Speller/Stemmer")
	local LRU = t.load("src/Shared/Speller/LRU")

	local function has(id: string): boolean
		return Library.get(id) ~= nil
	end

	t.test("exact, alias, normalized", function()
		local r = Speller.correct("dragon")
		t.eq(r.canonical, "dragon")
		t.eq(r.method, "Exact")
		t.eq(r.confidence, 1)
		t.eq(Speller.correct("wolves").canonical, "wolf")
		local n = Speller.correct("Dr4gon!!!")
		t.eq(n.canonical, "dragon")
		t.eq(n.method, "Normalized")
		t.ok(n.confidence >= 0.9, "normalized is silent")
	end)

	t.test("stemming: plurals, -ing/-ed, irregulars", function()
		t.eq(Speller.correct("asteroids").canonical, "asteroid")
		t.eq(Speller.correct("mice").canonical, "mouse")
		local c = Stemmer.candidates("wolves")
		t.eq(c[1].word, "wolf")
		t.ok(table.find((function()
			local out = {}
			for _, x in Stemmer.candidates("freezing") do table.insert(out, x.word) end
			return out
		end)(), "freeze") ~= nil, "freezing -> freeze")
		t.eq(Stemmer.candidates("fire dragons")[1].word, "fire dragon")
	end)

	t.test("known misspellings table", function()
		local r = Speller.correct("pheonix")
		t.eq(r.canonical, "phoenix")
		t.eq(r.method, "Misspelling")
		t.eq(Speller.correct("nite").canonical, "night")
		t.eq(Speller.correct("lightening").canonical, "lightning")
	end)

	t.test("fuzzy: keyboard-weighted, length-scaled, alternatives", function()
		local r = Speller.correct("elephamt") -- n/m adjacent
		t.eq(r.canonical, "elephant")
		t.eq(r.method, "Fuzzy")
		t.ok(r.confidence >= 0.6, "fuzzy confidence band")
		t.ok(#r.alternatives <= 3)
		-- short words are strict: a 2-letter garble never fuzzy-matches
		t.eq(Speller.correct("qz").canonical, nil)
		-- adjacent keys are cheaper than distant ones
		t.ok(Distance.between("dragpn", "dragon") < Distance.between("dragzn", "dragon"), "adjacent cheaper")
		t.ok(Distance.between("ballon", "balloon") < 1, "missing double letter is cheap")
		t.ok(Distance.between("dargon", "dragon") < 1, "transposition is cheap")
	end)

	t.test("phonetic (Double Metaphone)", function()
		local p = Metaphone.encode("phoenix")
		t.eq(p, "FNKS")
		t.eq(Metaphone.encode("fenix"), "FNKS")
		t.eq(Metaphone.code("smith"), "SM0/XMT")
		t.eq(Metaphone.code("schmidt"), "XMT/SMT")
		t.eq(Metaphone.code("michael"), "MKL/MXL")
		t.eq(Metaphone.code("knight"), Metaphone.code("night"))
	end)

	t.test("metaphone parity with build on every library key", function()
		local keys, _, phon = Library.keyArrays()
		local bad = 0
		local first = nil
		for i, k in keys do
			if Metaphone.code(k) ~= phon[i] then
				bad += 1
				first = first or (k .. " lua=" .. Metaphone.code(k) .. " py=" .. phon[i])
			end
		end
		t.eq(bad, 0, "mismatches (first: " .. tostring(first) .. ")")
	end)

	t.test("phrase parser: stacking 4+ modifiers, order, fillers", function()
		-- pick a State word that doesn't form its own library entry with "shark" (the library keeps growing)
		local state = "zombie"
		for _, s in { "inflatable", "mutant", "zombie", "clockwork", "upside down" } do
			if Library.lookup(s .. " shark") == nil then
				state = s
				break
			end
		end
		local r = Speller.correct("tiny angry golden " .. state .. " shark")
		t.eq(r.canonical, "shark")
		t.eq(#r.modifiers, 4)
		local kinds = {}
		for _, m in r.modifiers do kinds[m.kind] = true end
		t.ok(kinds.Size and kinds.Mood and kinds.Quality and kinds.State, "size+mood+quality+state")
		local a = Speller.correct("shark angry")
		t.eq(a.canonical, "shark")
		t.eq(a.modifiers[1].id, "angry")
		t.eq(Speller.correct("a giant shark").canonical, "shark")
		t.eq(#Speller.correct("the giant shark").extras, 0)
	end)

	t.test("phrase parser: every material phrasing", function()
		for _, s in { "spaghetti dragon", "dragon made of spaghetti", "dragon made out of spaghetti", "spaghetti-dragon",
			"dragon of spaghetti", "dragon but spaghetti", "dragon made from spaghetti" } do
			local r = Speller.correct(s)
			t.eq(r.canonical, "dragon", s)
			t.eq(r.material, "spaghetti", s)
			t.eq(#r.extras, 0, s .. " extras")
		end
	end)

	t.test("phrase parser: thing-vs-material ambiguity", function()
		local r = Speller.correct("cheese tank")
		t.eq(r.canonical, "tank")
		t.eq(r.material, "cheese")
		t.eq(Speller.correct("cheese").canonical, "cheese")
		t.eq(Speller.correct("cheese").material, nil)
	end)

	t.test("phrase parser: misspellings in every slot", function()
		local r = Speller.correct("spagetti dragn")
		t.eq(r.canonical, "dragon")
		t.eq(r.material, "spaghetti")
		local g = Speller.correct("giatn angery shrak")
		t.eq(g.canonical, "shark")
		t.eq(#g.modifiers, 2)
		t.ok(g.confidence >= 0.6 and g.confidence < 0.9, "typos show the did-you-mean chip")
		local c = Speller.correct("swarm of bes")
		t.eq(c.canonical, "bee")
	end)

	t.test("unknown words become extras for the AI", function()
		local r = Speller.correct("shark wearing a monocle and xyzzq")
		t.eq(r.canonical, "shark")
		t.ok(#r.extras >= 1, "extras kept")
		t.ok(r.confidence < 0.6, "extras push to AI")
		local _, spell, needsAI = Resolver.resolveLocalDetailed("shark qwxzv plorf", 0.6)
		t.ok(needsAI, "needs AI")
		t.eq(spell.canonical, "shark")
		local z = Speller.correct("asdfghjk")
		t.eq(z.canonical, nil)
	end)

	t.test("protected names become the generic idea", function()
		local r = Speller.correct("pikachu")
		t.eq(r.canonical, "mouse")
		t.ok(r.confidence < 0.9, "shown as a correction")
		local l = Speller.correct("lego dragon")
		t.eq(l.canonical, "dragon")
		t.eq(l.material, "toy bricks")
		local s = Speller.correct("pokemon dragon")
		t.eq(s.canonical, "dragon")
	end)

	t.test("every protected replacement parses with no extras", function()
		local P = t.load("src/Shared/Library/Generated/Protected")
		local bad = {}
		for name, rep in P.names do
			local r = Speller.correct(rep)
			if r.canonical == nil or #r.extras > 0 then
				table.insert(bad, name .. " -> " .. rep)
			end
		end
		table.sort(bad)
		t.eq(#bad, 0, "bad replacements: " .. table.concat(bad, "; "))
	end)

	t.test("compound words and spacing", function()
		t.eq(Speller.correct("giantshark").canonical, "shark")
		if has("black hole") then
			t.eq(Speller.correct("blackhole").canonical, "black hole")
		end
		if has("ice cream") then
			t.eq(Speller.correct("ice-cream").canonical, "ice cream")
		end
	end)

	t.test("LRU cache: hits, eviction, returned copies are independent", function()
		Speller.clearCache()
		local a = Speller.correct("dargon")
		a.alternatives[1] = "mutated"
		a.modifiers[1] = {} :: any
		local b = Speller.correct("dargon")
		t.eq(#b.modifiers, 0)
		t.ok(Speller.cacheStats().hits >= 1, "cache hit")
		local c = LRU.new(2)
		c:set("a", 1)
		c:set("b", 2)
		c:get("a")
		c:set("c", 3)
		t.eq(c:get("b"), nil)
		t.eq(c:get("a"), 1)
		t.eq(c.size, 2)
	end)

	t.test("never errors on junk", function()
		for _, junk in { "", "   ", "🔥🔥", string.rep("x", 500), "a the of", "\0\1\2", "1234567", "-'-'-" } do
			local r = Speller.correct(junk)
			t.ok(r ~= nil and type(r.confidence) == "number", "junk " .. junk)
		end
		t.eq(Speller.correct(nil :: any).canonical, nil)
	end)

	t.test("golden typo set >= 95%", function()
		local rows = {}
		for line in string.gmatch(fs.readFile("tests/data/typos.tsv"), "[^\n]+") do
			if string.sub(line, 1, 1) ~= "#" then
				local a, b = string.match(line, "^(.-)\t(.+)$")
				-- a "typo" that is itself a library word or a real English word is not a typo ("lunch" for launch)
				if a and Library.lookup(a) == nil and not Library.isRealWord(a) then
					table.insert(rows, { a, b })
				end
			end
		end
		local ok, fails = 0, {}
		for _, r in rows do
			local got = Resolver.resolveLocal(r[1]).canonical
			if got == r[2] then
				ok += 1
			else
				table.insert(fails, string.format("%q -> %s (want %s)", r[1], got, r[2]))
			end
		end
		local acc = ok / #rows
		print(string.format("[golden] %d/%d = %.1f%%", ok, #rows, acc * 100))
		for i = 1, math.min(#fails, 40) do
			print("  miss " .. fails[i])
		end
		t.ok(#rows >= 500, "golden set has >= 500 rows")
		t.ok(acc >= 0.95, string.format("accuracy %.3f", acc))
	end)
end
