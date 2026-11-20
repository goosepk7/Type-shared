return function(t)
	local M = t.load("tests/specs/server_mocks")

	t.test("blocklist hashes: leetspeak, spacing, repeats, case; no Scunthorpe", function()
		local ctx = M.setup(t)
		local B = ctx.Blocklist
		B._setData({
			exact1 = { B.hash(B.skeleton("badword", 1)) },
			contains1 = { B.hash(B.skeleton("vileterm", 1)) },
			maxLen = 12,
		})
		t.eq(ctx.Safety.isBlocked("badword"), true)
		t.eq(ctx.Safety.isBlocked("B@DW0RD"), true)
		t.eq(ctx.Safety.isBlocked("baaaadwooord"), true)
		t.eq(ctx.Safety.isBlocked("b a d w o r d"), true)
		t.eq(ctx.Safety.isBlocked("giant badword"), true)
		t.eq(ctx.Safety.isBlocked("badwordy"), false, "exact entries don't match inside words")
		t.eq(ctx.Safety.isBlocked("supervileterms"), true, "contains entries do")
		t.eq(ctx.Safety.isBlocked("dragon"), false)
		ctx.Safety.addBlocked("newban")
		t.eq(ctx.Safety.isBlocked("NEWBAN"), true)
		ctx.Safety.removeBlocked("newban")
		t.eq(ctx.Safety.isBlocked("newban"), false)
		B._setData(nil)
	end)

	t.test("shipped blocklist loads, stores no plaintext, and spares innocent words", function()
		local ctx = M.setup(t)
		local fs = require("@lune/fs")
		local raw = fs.readFile("data/blocklist.txt")
		for line in string.gmatch(raw, "[^\n]+") do
			if string.sub(line, 1, 1) ~= "#" then
				t.ok(string.match(line, "^%a+%d? %x+$") ~= nil, "hash-only line: " .. line)
			end
		end
		local data = fs.readFile("src/Server/BlocklistData.luau")
		t.ok(not string.find(data, "%f[%a]fuck"), "no plaintext")
		t.eq(ctx.Safety.isBlocked("sh1t"), true)
		t.eq(ctx.Safety.isBlocked("fuuuuck"), true)
		t.eq(ctx.Safety.isBlocked("f u c k"), true)
		-- 2026-11-20 list: variants, leet, lookalike letters, phrases, slurs, self-harm
		for _, bad in { "FÜCK", "ｆｕｃｋ", "ⓕⓤⓒⓚ", "fvck", "phuck", "motherfucker", "b!tch", "assh0le", "a$$", "n1gg3r",
			"N.I.G.G.A", "kys", "k y s", "kill yourself", "heil hitler", "r3tard", "p0rn", "s3x", "fucking fireball",
			"dragon of shit", "f@g", "kkk", "wizard ass" } do
			t.eq(ctx.Safety.isBlocked(bad), true, bad)
		end
		t.eq(ctx.Safety.isBlocked("fu\u{0441}k"), true, "Cyrillic es folds to c")
		t.eq(ctx.Safety.isBlocked("p\u{043E}rn"), true, "Cyrillic o folds to o")
		for _, ok in {
			"as", "con", "bob", "kung fu", "pocket watch", "smartwatch", "coconut water", "go kart", "crisis",
			"sinigang", "thorny", "fuchsia", "sperm whale", "plumb bob", "maine coon", "alaskan klee kai",
			"bastard sword", "nigersaurus", "puss caterpillar", "cafe con leche", "fire retardant", "torpedo",
			"raccoon", "cocoon", "title", "document", "cucumber", "hancock", "button", "massive", "uranus",
		} do
			t.eq(ctx.Safety.isBlocked(ok), false, ok)
		end
		for _, ok in { "dragon", "grape", "therapist", "class", "scunthorpe", "shiitake", "cocktail", "assassin",
			"bass", "grass", "hello", "naked mole rat", "pumpkin", "drape", "analysis", "nigeria", "condominium",
			"hoe", "glass cannon", "peacock", "shuttlecock", "rapier", "kitty", "spice", "isis" } do
			t.eq(ctx.Safety.isBlocked(ok), false, ok)
		end
	end)

	t.test("token bucket rate limit and spam detection", function()
		local ctx = M.setup(t, { config = function(C)
			C.Safety.RateCapacity = 4
			C.Safety.RateRefill = 0
			C.Safety.RepeatMax = 2
			C.Safety.SpamCooldown = 0.2
		end })
		local p = ctx.player()
		t.eq(ctx.Safety.check(p, "fire").reason, "Ok")
		t.eq(ctx.Safety.check(p, "fire").reason, "Ok")
		t.eq(ctx.Safety.check(p, "fire").reason, "Spam")
		t.eq(ctx.Safety.check(p, "ice").reason, "Spam", "cooldown applies to everything")
		ctx.task.wait(0.25)
		t.eq(ctx.Safety.check(p, "ice").reason, "Ok")
		t.eq(ctx.Safety.check(p, "wind").reason, "RateLimited")
		local q = ctx.player()
		t.eq(ctx.Safety.check(q, "wind").reason, "Ok", "per player")
		t.eq(ctx.Safety.check(q, "   ").reason, "Empty")
	end)

	t.test("clampText: length and UTF-8", function()
		local ctx = M.setup(t)
		t.eq(utf8.len(ctx.Safety.clampText(string.rep("é", 60))), 40)
		t.eq(ctx.Safety.clampText("\255\254"), "")
		t.eq(ctx.Safety.clampText(5), "")
	end)

	t.test("filterForBroadcast / filterForUser use TextService and fail closed", function()
		local ctx = M.setup(t, { filterBad = { ["secret"] = true } })
		local p, q = ctx.player(), ctx.player()
		t.eq(ctx.Safety.filterForBroadcast(p, "my secret"), "my ######")
		t.eq(ctx.Safety.filterForUser(p, "a secret", q), "a ######")
		t.eq(ctx.Safety.isHashed("my secret", "my ######"), true)
		t.eq(ctx.Safety.isHashed("dragon", "dragon"), false)
		local calls = ctx.filterCalls
		ctx.Safety.filterForBroadcast(p, "my secret")
		t.eq(ctx.filterCalls, calls, "short-lived filter cache")
		ctx.filterDown = true
		t.eq(ctx.Safety.filterForBroadcast(p, "brand new text"), "")
		t.eq(ctx.Safety.isHashed("brand new text", ""), true)
	end)

	t.test("looksLikeMash", function()
		local ctx = M.setup(t)
		for _, w in { "asdfghjkl", "qwrtzp", "xkcdvbnm", "zzzzzzzz" } do
			t.eq(ctx.Safety.looksLikeMash(w), true, w)
		end
		for _, w in { "dragon", "rhythm", "strengths", "catchphrase", "tornado", "fire", "lightning bolt" } do
			t.eq(ctx.Safety.looksLikeMash(w), false, w)
		end
	end)
end
