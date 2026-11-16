return function(t)
	local M = t.load("tests/specs/server_mocks")

	local function sample(ctx, id)
		local Schema = ctx.shared.Schema
		return Schema.repair({ id = id, category = "Creature", element = "Water", size = "Small", power = 3,
			source = "AI", input = "RAW PLAYER TEXT", flavourText = "Splish." })
	end

	t.test("keyFor: plain keys stay readable, odd ones are hashed", function()
		local ctx = M.setup(t)
		t.eq(ctx.Cache.keyFor("fire bat"), "fire bat")
		t.eq(string.sub(ctx.Cache.keyFor("ünïcode"), 1, 1), "#")
		t.eq(string.sub(ctx.Cache.keyFor(string.rep("a", 41)), 1, 1), "#")
		t.ok(#("w1:" .. ctx.Cache.keyFor(string.rep("a", 41))) <= 50, "DataStore key limit")
	end)

	t.test("put writes every layer without the raw input; get hits local, then hot, then store", function()
		local ctx = M.setup(t)
		ctx.Cache.putAsync("puddle cat", sample(ctx, "puddle cat"), { source = "AI" })
		local store = ctx.stores.WordEngine_WordCache_v1.data["w1:puddle cat"]
		t.ok(store and store.r.id == "puddle cat", "datastore")
		t.eq(store.r.input, "", "raw input never persisted")
		t.ok(ctx.maps.WordEngine_WordCacheHot_v1.data["puddle cat"], "memorystore")
		local r, meta = ctx.Cache.get("puddle cat")
		t.eq(r.id, "puddle cat")
		t.eq(meta.layer, "local")
		-- new server: empty LRU -> hot layer
		ctx.Cache.init()
		r, meta = ctx.Cache.get("puddle cat")
		t.eq(meta.layer, "hot")
		-- hot expired -> DataStore, which back-fills hot
		ctx.Cache.init()
		ctx.maps.WordEngine_WordCacheHot_v1.data = {}
		r, meta = ctx.Cache.get("puddle cat")
		t.eq(meta.layer, "store")
		ctx.task.wait(0.05)
		t.ok(ctx.maps.WordEngine_WordCacheHot_v1.data["puddle cat"], "back-filled")
	end)

	t.test("cache hit path in the interpreter: no AI call, source Cache, play counted", function()
		local ctx = M.setup(t)
		ctx.Cache.putAsync("fizzwump", sample(ctx, "fizzwump"), { source = "AI" })
		ctx.Cache.init() -- cold LRU: must come from MemoryStore/DataStore
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "fizzwump")
		t.eq(r.source, "Cache")
		t.eq(r.input, "fizzwump")
		t.eq(ctx.aiCalls, 0)
		ctx.Interpreter.interpretAsync(ctx.player(), "fizzwump")
		ctx.Cache.flushPlays()
		t.eq(ctx.stores.WordEngine_WordCache_v1.data["w1:fizzwump"].pc, 2)
		t.eq(ctx.ordered.WordEngine_AIWordPlays_v1.data["fizzwump"], 2)
		local top = ctx.Cache.topPlayed(5)
		t.eq(top[1].key, "fizzwump")
	end)

	t.test("store outage: cache degrades to miss, interpret still works", function()
		local ctx = M.setup(t)
		ctx.failStores = true
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "glowmoss", { timeout = 2 })
		t.eq(r.source, "AI")
		t.eq(ctx.Cache.get("glowmoss").id, "glowmoss", "still in local LRU")
	end)

	t.test("peek does not count; invalidate removes all layers", function()
		local ctx = M.setup(t)
		ctx.Cache.putAsync("sneeze", sample(ctx, "sneeze"), { source = "Admin" })
		local before = ctx.Cache.stats().hits
		local r, meta = ctx.Cache.peek("sneeze")
		t.eq(r.id, "sneeze")
		t.eq(meta.source, "Admin")
		t.eq(ctx.Cache.stats().hits, before)
		ctx.Cache.invalidate("sneeze")
		t.eq(ctx.Cache.peek("sneeze"), nil)
		t.eq(ctx.stores.WordEngine_WordCache_v1.data["w1:sneeze"], nil)
	end)

	t.test("merge keeps earliest firstSeen and max playCount", function()
		local ctx = M.setup(t)
		ctx.stores.WordEngine_WordCache_v1 = nil
		local ds = ctx.services.DataStoreService:GetDataStore("WordEngine_WordCache_v1")
		ds.data["w1:ooze"] = { v = 1, r = M.copy(sample(ctx, "ooze")), src = "AI", fs = 5, pc = 9 }
		ctx.Cache.putAsync("ooze", sample(ctx, "ooze"), { source = "AI" })
		t.eq(ds.data["w1:ooze"].fs, 5)
		t.eq(ds.data["w1:ooze"].pc, 9)
	end)

	t.test("AI typo result: canonical record + alias record for the typo", function()
		local ctx = M.setup(t)
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys, function()
				return { id = "toaster", corrected = "toaster" }
			end)
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "toastr", { timeout = 2 })
		t.eq(r.id, "toaster")
		t.eq(r.correction.to, "toaster")
		ctx.task.wait(0.1)
		local data = ctx.stores.WordEngine_WordCache_v1.data
		t.ok(data["w1:toaster"] and data["w1:toaster"].r.id == "toaster", "canonical record")
		t.eq(data["w1:toastr"].alias, "toaster", "alias record")
		-- a fresh server resolves the typo through the alias with no AI call
		ctx.Cache.init()
		local calls = ctx.aiCalls
		local r2 = ctx.Interpreter.interpretAsync(ctx.player(), "toastr")
		t.eq(r2.id, "toaster")
		t.eq(r2.source, "Cache")
		t.eq(ctx.aiCalls, calls)
	end)

	t.test("AI typo of a library word: alias points at the library id", function()
		local ctx = M.setup(t)
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys, function()
				return { id = "dragon", corrected = "dragon" }
			end)
		end)
		ctx.Interpreter.interpretAsync(ctx.player(), "drgaon", { timeout = 2 })
		ctx.task.wait(0.1)
		t.eq(ctx.stores.WordEngine_WordCache_v1.data["w1:drgaon"].alias, "dragon")
		ctx.Cache.init()
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "drgaon")
		t.eq(r.id, "dragon")
		t.eq(r.flavourText, "Breathes fire. Hoards loot. Judges you.")
	end)

	t.test("cache-first: a cached phrase wins over a weak library/parser guess", function()
		local ctx = M.setup(t)
		ctx.fuzzy = { dargonfly = "dragon" }
		local Schema = ctx.shared.Schema
		ctx.Cache.putAsync("dargonfly", Schema.repair({ id = "dragonfly", category = "Creature", size = "Tiny", source = "AI" }), { source = "AI" })
		ctx.Cache.init()
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "dargonfly")
		t.eq(r.id, "dragonfly")
		t.eq(r.source, "Cache")
		t.eq(ctx.aiCalls, 0)
	end)

	t.test("good parser results are memoized per server (remote layers read once)", function()
		local ctx = M.setup(t)
		ctx.fuzzy = { dragn = "dragon" }
		ctx.shared.Config.AI.Threshold = 0.4 -- fuzzy guesses (0.5) count as good here
		local reads = 0
		local map = ctx.services.MemoryStoreService:GetSortedMap("WordEngine_WordCacheHot_v1")
		local orig = map.GetAsync
		map.GetAsync = function(self, k)
			reads += 1
			return orig(self, k)
		end
		for _ = 1, 3 do
			local r = ctx.Interpreter.interpretAsync(ctx.player(), "dragn")
			t.eq(r.id, "dragon")
		end
		t.eq(reads, 1)
		map.GetAsync = orig
	end)

	t.test("paid results survive DataStore outages: retries, then a retry queue", function()
		local ctx = M.setup(t, { config = function(C)
			C.Cache.WriteRetries = 1
		end })
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		local ds = ctx.services.DataStoreService:GetDataStore("WordEngine_WordCache_v1")
		local origUpdate = ds.UpdateAsync
		ds.UpdateAsync = function()
			error("DataStore throttled")
		end
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "glintmoth", { timeout = 2 })
		t.eq(r.source, "AI")
		ctx.task.wait(0.1)
		t.eq(ctx.Cache.stats().pendingWrites, 1)
		ds.UpdateAsync = origUpdate
		ctx.Cache.flushPending()
		t.eq(ctx.Cache.stats().pendingWrites, 0)
		t.ok(ds.data["w1:glintmoth"], "written after recovery")
	end)

	t.test("cross-server de-dup: second server waits for the lock holder's result", function()
		local ctx = M.setup(t)
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		local map = ctx.services.MemoryStoreService:GetSortedMap("WordEngine_WordCacheHot_v1")
		-- server B holds the lock for "plasma newt" and publishes its result shortly
		map.data["lock:plasma newt"] = { job = "server-B", exp = os.time() + 20 }
		ctx.task.delay(0.15, function()
			local Schema = ctx.shared.Schema
			map.data["plasma newt"] = M.copy({ v = 1, src = "AI", fs = 1, pc = 0,
				r = Schema.repair({ id = "plasma newt", category = "Creature", element = "Lightning", size = "Small", source = "AI" }) })
			map.data["lock:plasma newt"] = { job = "server-B", exp = 0 }
		end)
		local r, h = ctx.Interpreter.interpretAsync(ctx.player(), "plasma newt", { timeout = 2 })
		t.eq(r.id, "plasma newt")
		t.eq(r.source, "Cache")
		t.eq(ctx.aiCalls, 0, "this server never paid")
	end)

	t.test("cross-server de-dup: holder gives up -> we take the lock and pay once", function()
		local ctx = M.setup(t)
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		local map = ctx.services.MemoryStoreService:GetSortedMap("WordEngine_WordCacheHot_v1")
		map.data["lock:frost gecko"] = { job = "server-B", exp = os.time() + 20 }
		ctx.task.delay(0.1, function()
			map.data["lock:frost gecko"] = nil -- B crashed / released without a result
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "frost gecko", { timeout = 2 })
		t.eq(r.source, "AI")
		t.eq(ctx.aiCalls, 1)
		ctx.task.wait(0.1)
		t.eq(map.data["lock:frost gecko"].exp, 0, "released after writing")
		t.ok(map.data["frost gecko"], "result published for other servers")
	end)
end
