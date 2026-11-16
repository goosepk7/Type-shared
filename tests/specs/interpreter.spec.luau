return function(t)
	local M = t.load("tests/specs/server_mocks")

	local function waitFor(ctx, cond, limit)
		local waited = 0
		while not cond() and waited < (limit or 3) do
			ctx.task.wait(0.03)
			waited += 0.03
		end
		return cond()
	end

	t.test("library hit returns immediately without AI", function()
		local ctx = M.setup(t)
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		local r, h = ctx.Interpreter.interpretAsync(ctx.player(), "Dragon")
		t.eq(r.id, "dragon")
		t.eq(r.source, "Library")
		t.eq(r.input, "Dragon")
		t.eq(h.pending, false)
		t.eq(ctx.aiCalls, 0)
		t.eq(#ctx.analytics, 1, "Analytics.word once")
		t.eq(ctx.analytics[1].result.input, "", "analytics gets broadcast-safe result")
	end)

	t.test("AI answers within the instant timeout -> AI result directly", function()
		local ctx = M.setup(t)
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		local r, h = ctx.Interpreter.interpretAsync(ctx.player(), "glorptank")
		t.eq(r.source, "AI")
		t.eq(h.pending, false)
	end)

	t.test("timeout then upgrade: best guess now, handle.upgraded fires once later", function()
		local ctx = M.setup(t)
		ctx.fuzzy = { dargonfly = "dragon" } -- low-confidence library guess
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys, function(k)
				return { id = "dragonfly", category = "Creature", size = "Tiny", power = 2 }
			end), 200, 0.5 -- slower than InstantTimeout (0.25)
		end)
		local t0 = os.clock()
		local r, h = ctx.Interpreter.interpretAsync(ctx.player(), "dargonfly")
		t.ok(os.clock() - t0 < 0.45, "returned at the instant timeout")
		t.eq(r.id, "dragon", "best guess")
		t.eq(h.pending, true)
		local fired = {}
		h.upgraded:Connect(function(better)
			table.insert(fired, better)
		end)
		t.ok(waitFor(ctx, function()
			return #fired > 0
		end), "upgrade fired")
		ctx.task.wait(0.1)
		t.eq(#fired, 1, "exactly once")
		t.eq(fired[1].id, "dragonfly")
		t.eq(fired[1].source, "AI")
		t.eq(fired[1].input, "dargonfly")
		t.ok(fired[1].correction and fired[1].correction.to == "dragonfly", "correction set")
		t.eq(h.pending, false)
		t.eq(h.result.id, "dragonfly")
		-- late subscribers still receive it (replaying signal)
		local late
		h.upgraded:Connect(function(b)
			late = b
		end)
		ctx.task.wait(0.05)
		t.eq(late and late.id, "dragonfly")
	end)

	t.test("no upgrade when the AI fails after a timeout", function()
		local ctx = M.setup(t, { config = function(C)
			C.AI.MaxRetries = 0
		end })
		ctx.useAI(function()
			return nil, 500, 0.4
		end)
		local r, h = ctx.Interpreter.interpretAsync(ctx.player(), "wibblewump")
		t.eq(r.source, "Fallback")
		t.eq(h.pending, true)
		local fired = false
		h.upgraded:Connect(function()
			fired = true
		end)
		ctx.task.wait(0.6)
		t.eq(fired, false)
		t.eq(h.pending, false)
	end)

	t.test("coalescing: concurrent identical requests -> one AI call across the server", function()
		local ctx = M.setup(t)
		local keysSeen = 0
		ctx.useAI(function(keys)
			keysSeen += #keys
			return ctx.resultsJson(keys), 200, 0.1
		end)
		local results = {}
		for i = 1, 6 do
			ctx.task.spawn(function()
				results[i] = ctx.Interpreter.interpretAsync(ctx.player(), if i % 2 == 0 then "Sparkle Moth" else "sparkle  moth!")
			end)
		end
		t.ok(waitFor(ctx, function()
			return #results == 6
		end), "all answered")
		t.eq(ctx.aiCalls, 1)
		t.eq(keysSeen, 1)
		for i = 1, 6 do
			t.eq(results[i].source, "AI")
		end
		-- and it is cached: a later request makes no call
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "sparkle moth")
		t.eq(r.source, "Cache")
		t.eq(ctx.aiCalls, 1)
	end)

	t.test("blocklisted input -> Fallback, never reaches AI or cache", function()
		local ctx = M.setup(t)
		ctx.Blocklist._setData({ exact1 = { ctx.Blocklist.hash("badword") } })
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		local r, h = ctx.Interpreter.interpretAsync(ctx.player(), "B4DW0RD")
		t.eq(r.source, "Fallback")
		t.eq(h.reason, "Blocked")
		t.eq(ctx.aiCalls, 0)
		ctx.Blocklist._setData(nil)
	end)

	t.test("rate limiting -> Fallback with reason, recovers after refill", function()
		local ctx = M.setup(t, { config = function(C)
			C.Safety.RateCapacity = 3
			C.Safety.RateRefill = 10
		end })
		local p = ctx.player()
		local reasons = {}
		for i = 1, 5 do
			local _, h = ctx.Interpreter.interpretAsync(p, "dragon")
			table.insert(reasons, h.reason)
		end
		t.eq(reasons[3], "Ok")
		t.eq(reasons[4], "RateLimited")
		ctx.task.wait(0.15)
		local r, h = ctx.Interpreter.interpretAsync(p, "dragon")
		t.eq(h.reason, "Ok")
		t.eq(r.id, "dragon")
	end)

	t.test("hashed input (TextService) -> no AI, Fallback", function()
		local ctx = M.setup(t, { filterBad = { ["myphone"] = true } })
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "myphone")
		t.eq(r.source, "Fallback")
		t.eq(ctx.aiCalls, 0)
	end)

	t.test("filter outage fails closed (no AI, Fallback)", function()
		local ctx = M.setup(t)
		ctx.filterDown = true
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "frobnik", { timeout = 1 })
		t.eq(r.source, "Fallback")
		t.eq(ctx.aiCalls, 0)
	end)

	t.test("AI text that the filter hashes is never shown", function()
		local ctx = M.setup(t, { filterBad = { ["rudeline"] = true } })
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys, function()
				return { flavourText = "a rudeline here" }
			end)
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "puddlecat")
		t.eq(r.source, "AI")
		t.ok(string.find(r.flavourText, "rudeline", 1, true) == nil, "flavour replaced")
	end)

	t.test("keyboard mash skips the AI", function()
		local ctx = M.setup(t)
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "sdfghjklq")
		t.eq(r.source, "Fallback")
		t.eq(ctx.aiCalls, 0)
	end)

	t.test("per-player NEW-phrase limit (separate from typing limit) protects cost", function()
		local ctx = M.setup(t, { config = function(C)
			C.AI.NewPhrasePerMinute = 2
			C.Safety.RateCapacity = 50
		end })
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		local p = ctx.player()
		for _, w in { "aardwolfie", "bumblesnoot", "cattywump" } do
			ctx.Interpreter.interpretAsync(p, w, { timeout = 2 })
		end
		t.eq(ctx.aiCalls, 2)
	end)

	t.test("never errors, never nil: hostile inputs and crashing dependencies", function()
		local ctx = M.setup(t)
		ctx.shared.Resolver = { resolveLocalDetailed = function()
			error("boom")
		end }
		ctx.httpHandler = function()
			error("network down")
		end
		local p = ctx.player()
		for _, input in { nil, 5, {}, "", string.rep("x", 500), "\255\254", "   ", "drag\0on", "😀🔥" } do
			local r, h = ctx.Interpreter.interpretAsync(p, input, { timeout = 0.5 })
			t.ok(type(r) == "table" and type(r.id) == "string", "result for " .. tostring(input))
			t.ok(h and h.upgraded, "handle")
		end
		local r = ctx.Interpreter.interpretAsync(nil, "dragon")
		t.ok(r and r.id, "nil player")
	end)

	t.test("modifiers are split before the AI key and re-applied", function()
		local applied = 0
		local ctx = M.setup(t, { shared = {
			Normalizer = {
				normalize = function(s)
					return string.lower(s)
				end,
				tokenize = function(s)
					local out = {}
					for w in string.gmatch(s, "%S+") do
						table.insert(out, w)
					end
					return out
				end,
			},
			Modifiers = {
				parse = function(tokens)
					local rest, mods = {}, {}
					for _, tok in tokens do
						if tok == "giant" then
							table.insert(mods, { id = "giant", kind = "Size" })
						else
							table.insert(rest, tok)
						end
					end
					return rest, mods
				end,
				apply = function(r, mods)
					applied += 1
					r.size = "Huge"
					r.canonical = "giant " .. r.id
					return r
				end,
			},
		} })
		local keys = {}
		ctx.useAI(function(k)
			table.insert(keys, k[1])
			return ctx.resultsJson(k)
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "giant blorbus")
		t.eq(keys[1], "blorbus")
		t.eq(r.canonical, "giant blorbus")
		t.eq(r.size, "Huge")
		local r2 = ctx.Interpreter.interpretAsync(ctx.player(), "blorbus")
		t.eq(r2.source, "Cache")
		t.eq(ctx.aiCalls, 1)
	end)

	t.test("Admin hooks: ban, override, apply", function()
		local ctx = M.setup(t)
		ctx.serverModules.Admin = {
			isBanned = function(n)
				return n == "bannedword"
			end,
			override = function(n)
				if n == "secret sauce" then
					return { id = "secret sauce", category = "Food", element = "Fire", size = "Small", power = 4 }
				end
				return nil
			end,
			apply = function(r)
				if r.id == "dragon" then
					r.flavourText = "Retagged!"
				end
				return r
			end,
		}
		local r1, h1 = ctx.Interpreter.interpretAsync(ctx.player(), "bannedword")
		t.eq(r1.source, "Fallback")
		t.eq(h1.reason, "Banned")
		local r2 = ctx.Interpreter.interpretAsync(ctx.player(), "Secret Sauce")
		t.eq(r2.source, "Admin")
		t.eq(r2.category, "Food")
		local r3 = ctx.Interpreter.interpretAsync(ctx.player(), "dragon")
		t.eq(r3.flavourText, "Retagged!")
		ctx.serverModules.Admin = nil
	end)

	t.test("Net.validateArgs rejects bad remote arguments", function()
		M.setup(t)
		local Net = t.load("src/Shared/Net")
		local ok, text, id, reason = Net.validateArgs("dragon", 7)
		t.ok(ok and text == "dragon" and id == 7 and reason == "Ok", "valid")
		t.eq(select(4, Net.validateArgs(nil, 1)), "Invalid")
		t.eq(select(4, Net.validateArgs({}, 1)), "Invalid")
		t.eq(select(4, Net.validateArgs(string.rep("a", 41), 1)), "TooLong")
		t.eq(select(4, Net.validateArgs(string.rep("é", 40), 1)), "Ok")
		t.eq(select(4, Net.validateArgs("\255bad", 1)), "Invalid")
		t.eq(select(3, Net.validateArgs("x", 1.5)), 0)
		t.eq(select(3, Net.validateArgs("x", -1)), 0)
		t.eq(select(3, Net.validateArgs("x", 0 / 0)), 0)
		t.eq(select(2, Net.validateArgs("a\nb", 1)), "a b")
		-- per-player bucket
		local allowed = 0
		for _ = 1, 20 do
			if Net.allow(42, 5, 1, 100) then
				allowed += 1
			end
		end
		t.eq(allowed, 5)
		t.eq(Net.allow(42, 5, 1, 102), true)
	end)
end
