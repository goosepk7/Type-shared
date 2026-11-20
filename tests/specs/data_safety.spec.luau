-- Save-data safety under failure injection: unreadable records are never replaced, busy holders are not
-- robbed of their final save, the wipe tripwire, backups (versions) + restore without losing or doubling
-- purchases, and the receipt ready gate.
return function(t)
	local Mocks = t.load("tests/mocks/services")

	local function fresh()
		local m = Mocks.setup(t)
		local SessionStore = t.load("src/Server/Data/SessionStore")
		local Data = t.load("src/Server/Data")
		local Currency = t.load("src/Server/Currency")
		local Purchases = t.load("src/Server/Purchases")
		Data._reset()
		Currency._reset()
		Purchases._reset()
		m.SessionStore, m.Data, m.Currency, m.Purchases = SessionStore, Data, Currency, Purchases
		m.ds = m.LocalStore.new("players")
		local online = {}
		m.online = online
		local sig = { Connect = function() end }
		m.env.services.Players = { GetPlayerByUserId = function(_, id) return online[id] end, PlayerRemoving = sig }
		m.env.services.MarketplaceService = { UserOwnsGamePassAsync = function() return false end, PromptGamePassPurchaseFinished = sig }
		return m
	end

	local function nsGame(guard)
		return { template = { xp = 0, inv = {} }, version = 1, migrations = {}, guard = guard }
	end

	local function join(m, id)
		local p = Mocks.player(id)
		m.online[id] = p
		m.Data.loadPlayer(p)
		return p
	end

	t.test("an unreadable record is never replaced: load refused, record untouched, player kicked", function()
		for _, bad in { "garbage", 42, { meta = "x", ns = {} }, { format = 1, meta = {} } } do
			local m = fresh()
			m.ds.data.u_1 = bad
			local ss = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
			local s, err = ss:load("u_1", { 1 })
			t.eq(s, nil, "refused")
			t.ok(err and string.find(err, "unreadable"), tostring(err))
			if type(bad) == "table" then
				t.eq(m.ds.data.u_1.meta, bad.meta, "untouched")
			else
				t.eq(m.ds.data.u_1, bad, "untouched")
			end
		end
		local m = fresh()
		m.Data.useStore(m.ds)
		m.ds.data.u_7 = "corrupt"
		local p = join(m, 7)
		t.ok(p.kicked ~= nil, "kicked instead of playing on a blank save")
		t.eq(m.ds.data.u_7, "corrupt")
	end)

	t.test("a record written in a newer format is refused, not downgraded", function()
		local m = fresh()
		m.ds.data.u_2 = { format = 99, meta = { saves = 5 }, ns = { Game = { v = 1, d = { xp = 900 } } } }
		local ss = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
		local s, err = ss:load("u_2", { 2 })
		t.eq(s, nil)
		t.ok(string.find(err, "newer"), err)
		t.eq(m.ds.data.u_2.format, 99)
		t.ok(not ss:editOffline("u_2", "Game", function(d) d.xp = 0 end), "offline edit refused too")
		t.eq(m.ds.data.u_2.ns.Game.d.xp, 900)
	end)

	t.test("an unreadable namespace entry is frozen, never reset to the template", function()
		local m = fresh()
		m.ds.data.u_3 = { format = 1, meta = { created = 0, updated = 0, saves = 1 }, ns = { Game = { v = 1, d = "oops" } } }
		local ss = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
		local s = assert(ss:load("u_3", { 3 }))
		t.ok(s.frozen.Game ~= nil, "frozen")
		s.data.Game.xp = 5
		assert(ss:release(s))
		t.eq(m.ds.data.u_3.ns.Game.d, "oops", "stored value kept for a manual fix / restore")
	end)

	t.test("a holder that answers keeps its final save: no steal at LockWaitSeconds", function()
		local m = fresh()
		local ssA = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
		local a = assert(ssA:load("u_4", { 4 }))
		a.data.Game.xp = 10
		assert(ssA:save(a))
		a.data.Game.xp = 777 -- earned in the last seconds: only the final save carries it

		m.env.jobId = "server-B"
		local acked: { [string]: number } = {}
		local ssB = m.SessionStore.new("P", m.ds, {
			namespaces = { Game = nsGame() },
			requestRelease = function(_key, lock)
				acked[lock.session] = m.clock.mono -- A answers: "on it" (throttled, still writing)
			end,
			holderAlive = function(lock, since)
				return acked[lock.session] ~= nil and acked[lock.session] >= since
			end,
		})
		local waitCfg = m.Config.Services.Data
		local start = m.clock.mono
		local released = false
		m.env.wait = function(sec)
			m.clock.now += sec
			m.clock.mono += sec
			-- A's final save lands at 25 s: after LockWaitSeconds (12), before LockBusySeconds (60)
			if not released and m.clock.mono - start >= 25 then
				released = true
				assert(ssA:release(a), "A's final save is not refused")
			end
		end
		local b = assert(ssB:load("u_4", { 4 }))
		t.ok(m.clock.mono - start >= 25, "B waited for A")
		t.ok(m.clock.mono - start < waitCfg.LockBusySeconds, "but not longer than needed")
		t.eq(b.data.Game.xp, 777, "B sees A's final save")
		t.eq(a.stolen, false)
	end)

	t.test("a holder that answers but never finishes is stolen from at LockBusySeconds; a silent one at LockWaitSeconds", function()
		local m = fresh()
		local cfg = m.Config.Services.Data
		local ssA = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
		assert(ssA:load("u_5", { 5 }))
		m.env.jobId = "server-B"
		local ssB = m.SessionStore.new("P", m.ds, {
			namespaces = { Game = nsGame() },
			requestRelease = function() end,
			holderAlive = function() return true end,
		})
		local t0 = m.clock.mono
		assert(ssB:load("u_5", { 5 }))
		t.ok(m.clock.mono - t0 >= cfg.LockBusySeconds, "waited the busy window")
		t.ok(m.clock.mono - t0 < cfg.LockBusySeconds + 5)

		assert(ssA:load("u_6", { 6 }))
		local ssC = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() }, requestRelease = function() end, holderAlive = function() return false end })
		local t1 = m.clock.mono
		assert(ssC:load("u_6", { 6 }))
		t.ok(m.clock.mono - t1 >= cfg.LockWaitSeconds and m.clock.mono - t1 < cfg.LockBusySeconds, "silent holder: normal wait")
	end)

	t.test("release requests are repeated while waiting (a lost message does not strand the player)", function()
		local m = fresh()
		local ssA = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
		assert(ssA:load("u_8", { 8 }))
		m.env.jobId = "server-B"
		local asks = 0
		local ssB = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() }, requestRelease = function() asks += 1 end })
		assert(ssB:load("u_8", { 8 }))
		t.ok(asks >= 2, "asked again: " .. asks)
	end)

	t.test("wipe tripwire: a save that would drop lifetime xp is not written and freezes the namespace", function()
		local m = fresh()
		local guard = function(stored, new)
			if (tonumber(new.xp) or 0) < (tonumber(stored.xp) or 0) then
				return false, "xp " .. tostring(stored.xp) .. " -> " .. tostring(new.xp)
			end
			return true
		end
		local ss = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame(guard) } })
		local s = assert(ss:load("u_9", { 9 }))
		s.data.Game.xp = 5000
		assert(ss:save(s))
		-- a bug replaces the live table with a blank one
		s.data.Game = { xp = 0, inv = {} }
		assert(ss:save(s))
		t.eq(m.ds.data.u_9.ns.Game.d.xp, 5000, "stored copy kept")
		t.ok(s.frozen.Game and string.find(s.frozen.Game, "save guard"), "frozen")
		assert(ss:release(s))
		t.eq(m.ds.data.u_9.ns.Game.d.xp, 5000, "still kept after release")
		t.eq(m.ds.data.u_9.meta.lock, nil, "lock released normally")
	end)

	t.test("backups: list versions, restore an offline player, refuse while online", function()
		local m = fresh()
		m.Data.useStore(m.ds)
		m.Data.register("Game", nsGame())
		local p = join(m, 10)
		m.Data.update(p, function(d) d.xp = 100 end, "Game")
		assert(m.Data.saveAsync(p))
		local versions = assert(m.Data.listVersions(10, 10))
		local good = versions[1].version -- newest: xp 100
		m.Data.update(p, function(d) d.xp = 3 d.inv = { "junk" } end, "Game")
		assert(m.Data.saveAsync(p))
		local ok, err = m.Data.restoreVersion(10, good)
		t.eq(ok, false, "refused while the player is online")
		t.ok(string.find(err, "active"), err)
		m.Data.releasePlayer(p)
		m.online[10] = nil
		local listed = assert(m.Data.listVersions(10, 50))
		t.ok(#listed >= 4, "every write kept as a version")
		local peek = m.Data.peekVersion(10, good)
		t.eq(peek.ns.Game.d.xp, 100)
		assert(m.Data.restoreVersion(10, good))
		t.eq(m.ds.data.u_10.ns.Game.d.xp, 100, "restored")
		t.eq(m.ds.data.u_10.meta.lock, nil, "restored record is unlocked")
		t.eq(m.ds.data.u_10.meta.restored.from, good)
		local p2 = join(m, 10)
		t.eq(m.Data.get(p2, "Game").xp, 100)
	end)

	t.test("restore keeps later receipts and re-grants those purchases once on the next load", function()
		local m = fresh()
		m.Data.useStore(m.ds)
		m.Currency.define("Gems", { initial = 0 })
		m.Purchases.registerCurrencyProduct(111, "Gems", 100)
		m.Purchases.start()
		local p = join(m, 11)
		assert(m.Data.saveAsync(p))
		local backup = assert(m.Data.listVersions(11, 1))[1].version
		t.eq(m.Purchases.processReceipt({ PurchaseId = "buy1", PlayerId = 11, ProductId = 111 }), "PurchaseGranted")
		t.eq(m.Currency.balance(p, "Gems"), 100)
		m.Data.releasePlayer(p)
		m.online[11] = nil

		local ok, err, regrants = m.Data.restoreVersion(11, backup)
		t.ok(ok, tostring(err))
		t.eq(regrants, 1)
		local core = m.ds.data.u_11.ns.WordEngine.d
		t.ok(core.receipts.ids.buy1 ~= nil, "receipt id kept: no double grant on redelivery")
		t.eq(core.wallet.balances.Gems or 0, 0, "wallet rolled back...")

		local p2 = join(m, 11)
		t.eq(m.Currency.balance(p2, "Gems"), 100, "...and the paid product granted again")
		t.eq(#m.Data.get(p2).regrant, 0, "queue cleared")
		t.eq(m.Purchases.processReceipt({ PurchaseId = "buy1", PlayerId = 11, ProductId = 111 }), "PurchaseGranted")
		t.eq(m.Currency.balance(p2, "Gems"), 100, "redelivered receipt not granted twice")
		m.Data.releasePlayer(p2)
		m.online[11] = nil
		local p3 = join(m, 11)
		t.eq(m.Currency.balance(p3, "Gems"), 100, "regrant ran exactly once across sessions")
	end)

	t.test("receipt ready gate: not ready -> NotProcessedYet and nothing granted; ready -> granted", function()
		local m = fresh()
		m.Data.useStore(m.ds)
		m.Currency.define("Gems", { initial = 0 })
		m.Purchases.registerCurrencyProduct(111, "Gems", 100)
		local ready = false
		m.Purchases.setReadyGate(function() return ready end)
		local p = join(m, 12)
		t.eq(m.Purchases.processReceipt({ PurchaseId = "g1", PlayerId = 12, ProductId = 111 }), "NotProcessedYet")
		t.eq(m.Currency.balance(p, "Gems"), 0)
		ready = true
		t.eq(m.Purchases.processReceipt({ PurchaseId = "g1", PlayerId = 12, ProductId = 111 }), "PurchaseGranted")
		t.eq(m.Currency.balance(p, "Gems"), 100)
	end)

	t.test("purchase survives a save outage: NotProcessedYet, then granted once when saves recover", function()
		local m = fresh()
		m.Data.useStore(m.ds)
		m.Currency.define("Gems", { initial = 0 })
		m.Purchases.registerCurrencyProduct(111, "Gems", 100)
		local p = join(m, 13)
		m.ds:failNext("UpdateAsync", 1000, "500: outage")
		t.eq(m.Purchases.processReceipt({ PurchaseId = "o1", PlayerId = 13, ProductId = 111 }), "NotProcessedYet")
		m.ds:failNext("UpdateAsync", 0)
		t.eq(m.Purchases.processReceipt({ PurchaseId = "o1", PlayerId = 13, ProductId = 111 }), "PurchaseGranted")
		t.eq(m.Currency.balance(p, "Gems"), 100, "granted exactly once")
		t.ok(m.ds.data.u_13.ns.WordEngine.d.receipts.ids.o1 ~= nil)
	end)

	t.test("server crash before the final save: the next server steals the stale lock, no blank profile", function()
		local m = fresh()
		local ssA = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
		local a = assert(ssA:load("u_14", { 14 }))
		a.data.Game.xp = 40
		assert(ssA:save(a))
		a.data.Game.xp = 41 -- lost with the crash (only since the last autosave)
		m.env.jobId = "server-B"
		local ssB = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() }, requestRelease = function() end })
		local b = assert(ssB:load("u_14", { 14 }))
		t.eq(b.data.Game.xp, 40, "last autosave, never a blank profile")
	end)
end
