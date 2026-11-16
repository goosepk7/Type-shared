-- Suggest: word book first, then library by signature/popularity; < 1 ms.
return function(t)
	local Suggest = t.load("src/Shared/Suggest")

	t.test("word book first, then library", function()
		local r = Suggest.prefix("dra", { "drawbridge", "dragon fruit", "shark" }, 5)
		t.eq(r[1], "drawbridge")
		t.eq(r[2], "dragon fruit")
		t.ok(#r <= 5)
		for _, s in r do
			t.eq(string.sub(s, 1, 3), "dra")
		end
		local seen = {}
		for _, s in r do
			t.ok(not seen[s], "no duplicates")
			seen[s] = true
		end
	end)

	t.test("library only, limits and junk", function()
		t.ok(#Suggest.prefix("sh", nil, 4) <= 4)
		t.ok(#Suggest.prefix("sh", nil, 4) >= 1)
		t.eq(#Suggest.prefix("", nil, 4), 0)
		t.eq(#Suggest.prefix(nil :: any, nil, 4), 0)
		t.eq(#Suggest.prefix("qzqzqz", nil, 4), 0)
	end)

	t.test("completes the last word after modifiers", function()
		local r = Suggest.prefix("giant shar", nil, 4)
		t.ok(#r >= 1, "some completion")
		t.eq(string.sub(r[1], 1, 10), "giant shar")
	end)

	t.test("under 1 ms", function()
		Suggest.prefix("a", nil, 4)
		local book = {}
		for i = 1, 300 do
			book[i] = "word" .. i
		end
		local c = os.clock()
		local n = 0
		for _, p in { "a", "b", "dr", "fir", "sha", "tor", "giant sha", "x", "spa", "ro" } do
			for _ = 1, 20 do
				Suggest.prefix(p, book, 4)
				n += 1
			end
		end
		local per = (os.clock() - c) / n * 1000
		print(string.format("[suggest] %.3f ms per call", per))
		t.ok(per < 1, "per call ms " .. per)
	end)
end
