-- Admin: permission gate, validation, overrides/bans hooks, audit trail, rate limit.
return function(t)
	local Mocks = t.load("tests/mocks/services")

	local function fresh()
		local m = Mocks.setup(t)
		local Schema = t.load("src/Shared/Schema")
		local dragon = Schema.repair({ id = "dragon", category = "Creature", element = "Fire", size = "Huge", source = "Library",
			behaviours = { "Flies", "Burns" }, visual = { bodyPlan = "Quadruped" } })
		m.env.shared = {
			Schema = Schema,
			Config = m.Config,
			Library = {
				lookup = function(w) return if w == "dragon" or w == "drake" then "dragon" else nil end,
				get = function(id) return if id == "dragon" then Schema.clone(dragon) else nil end,
			},
			Resolver = { resolveLocal = function(text)
				if text == "dragon" then return Schema.clone(dragon) end
				return Schema.fallback(text)
			end },
		}
		local Data = t.load("src/Server/Data")
		local Admin = t.load("src/Server/Admin")
		Data._reset()
		Admin._reset()
		Data.useStore(m.LocalStore.new("players"))
		m.Admin, m.Schema = Admin, Schema
		m.Config.Services.Admin.UserIds = { 42 }
		return m
	end

	t.test("only admins can act", function()
		local m = fresh()
		local res = m.Admin.handle(Mocks.player(7), "ban", "dragon")
		t.eq(res.ok, false)
		t.eq(m.Admin.isBanned("dragon"), false)
		t.ok(m.Admin.handle(Mocks.player(42), "ban", "  Dragon!! ").ok)
		t.eq(m.Admin.isBanned("dragon"), true, "normalized before banning")
		t.eq(m.Admin.testCast("dragon").source, "Fallback")
	end)

	t.test("force result is validated, repaired and returned by override()", function()
		local m = fresh()
		local admin = Mocks.player(42)
		local res = m.Admin.handle(admin, "force", "zorp", '{"id":"zorp","category":"creature","element":"ICE","power":99}')
		t.ok(res.ok, res.message)
		local r = m.Admin.override("zorp")
		t.eq(r.source, "Admin")
		t.eq(r.element, "Ice")
		t.eq(r.power, 10)
		t.eq(m.Admin.handle(admin, "force", "zorp", "not json").ok, false)
		t.ok(m.Admin.handle(admin, "clear", "zorp").ok)
		t.eq(m.Admin.override("zorp"), nil)
	end)

	t.test("retag whitelists fields, rejects bad enums, and applies to aliases and modified results", function()
		local m = fresh()
		local admin = Mocks.player(42)
		t.eq(m.Admin.handle(admin, "retag", "dragon", { input = "x" }).ok, false, "input not patchable")
		t.eq(m.Admin.handle(admin, "retag", "dragon", { element = "Plasma" }).ok, false, "bad enum")
		t.ok(m.Admin.handle(admin, "retag", "dragon", { element = "Ice", flavourText = "Chilly now." }).ok)
		local r = m.Admin.override("drake")
		t.eq(r.element, "Ice")
		t.eq(r.flavourText, "Chilly now.")
		local giant = m.Schema.repair({ id = "dragon", canonical = "giant dragon", element = "Fire", size = "Colossal" })
		local applied = m.Admin.apply(giant)
		t.eq(applied.element, "Ice")
		t.eq(applied.size, "Colossal", "modifier results keep their other fields")
	end)

	t.test("actions are audit-logged and persisted", function()
		local m = fresh()
		local admin = Mocks.player(42)
		m.Admin.handle(admin, "ban", "meanword")
		local audit = m.dss:GetDataStore("WordEngine_Audit_v1")
		local n = 0
		for _, list in audit.data do
			for _, e in list do
				n += 1
				t.eq(e.u, 42)
			end
		end
		t.ok(n >= 1, "audit entry written")
		local state = m.dss:GetDataStore("WordEngine_Admin_v1").data.state
		t.eq(state.banned.meanword, true)
	end)

	t.test("rate limit per admin", function()
		local m = fresh()
		local admin = Mocks.player(42)
		m.Config.Services.Admin.MaxActionsPerMinute = 3
		for _ = 1, 3 do
			t.ok(m.Admin.handle(admin, "state").ok)
		end
		t.eq(m.Admin.handle(admin, "state").ok, false)
		m.Config.Services.Admin.MaxActionsPerMinute = 30
	end)

	t.test("AI cache tools call the Cache API with validated data; kill switch + spend status", function()
		local m = fresh()
		local admin = Mocks.player(42)
		local cache = {}
		local calls = {}
		m.env.services["WordEngineServer.Cache"] = {
			peek = function(k) return cache[k] end,
			put = function(k, r, o) table.insert(calls, "put:" .. k .. ":" .. o.source); cache[k] = r end,
			invalidate = function(k) table.insert(calls, "inv:" .. k); cache[k] = nil end,
		}
		local aiOn = true
		m.env.services["WordEngineServer.AI"] = {
			setEnabled = function(on) aiOn = on; return true end,
			status = function() return { enabled = aiOn, todayUsd = 1.25, budgetUsd = 5 } end,
		}
		t.ok(m.Admin.handle(admin, "cacheedit", "spaghetti dragon", '{"id":"dragon","element":"Fire","material":"spaghetti"}').ok)
		t.eq(cache["spaghetti dragon"].source, "Admin")
		t.ok(m.Admin.handle(admin, "cacheretag", "spaghetti dragon", { element = "Water" }).ok)
		t.eq(cache["spaghetti dragon"].element, "Water")
		t.eq(m.Admin.handle(admin, "cacheretag", "nothing here", { element = "Water" }).ok, false)
		local view = m.Admin.handle(admin, "cache", "spaghetti dragon")
		t.eq(view.data.cached.element, "Water")
		t.ok(m.Admin.handle(admin, "cachedelete", "spaghetti dragon").ok)
		t.eq(cache["spaghetti dragon"], nil)
		t.ok(m.Admin.handle(admin, "ban", "spaghetti dragon").ok)
		t.eq(calls[#calls], "inv:spaghetti dragon", "ban purges the cache too")
		local off = m.Admin.handle(admin, "ai", "off")
		t.ok(off.ok)
		t.eq(aiOn, false)
		t.eq(off.data.spendFraction, 0.25)
		t.eq(m.Admin.handle(Mocks.player(1), "ai", "on").ok, false, "non-admin cannot flip the switch")
		t.eq(aiOn, false)
	end)
end
