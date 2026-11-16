-- Session-locked player data: locking, contention/steal, migrations, retries, budget, facade.
return function(t)
	local Mocks = t.load("tests/mocks/services")

	local function fresh()
		local m = Mocks.setup(t)
		local SessionStore = t.load("src/Server/Data/SessionStore")
		local Data = t.load("src/Server/Data")
		Data._reset()
		m.SessionStore = SessionStore
		m.Data = Data
		m.ds = m.LocalStore.new("players")
		return m
	end

	local function nsGame()
		return { template = { level = 1, inv = {}, opts = { music = true } }, version = 1, migrations = {} }
	end

	t.test("load creates a record, takes the lock and applies the template", function()
		local m = fresh()
		local ss = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
		local s = assert(ss:load("u_1", { 1 }))
		t.eq(s.data.Game.level, 1)
		t.eq(m.ds.data.u_1.meta.lock.session, s.id)
		t.eq(m.ds.data.u_1.meta.lock.job, "server-A")
		t.eq(m.ds.userIds.u_1[1], 1)
		s.data.Game.level = 7
		t.ok(ss:save(s), "save")
		t.eq(m.ds.data.u_1.ns.Game.d.level, 7)
		t.ok(ss:release(s), "release")
		t.eq(m.ds.data.u_1.meta.lock, nil)
		t.eq(s.active, false)
	end)

	t.test("contention: second server asks for release, then steals; old server cannot overwrite", function()
		local m = fresh()
		local ssA = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
		local a = assert(ssA:load("u_2", { 2 }))
		a.data.Game.level = 5
		assert(ssA:save(a))

		m.env.jobId = "server-B"
		local asked = 0
		local ssB = m.SessionStore.new("P", m.ds, {
			namespaces = { Game = nsGame() },
			requestRelease = function(key, lock)
				asked += 1
				t.eq(key, "u_2")
				t.eq(lock.job, "server-A")
			end,
		})
		local t0 = m.clock.now
		local b = assert(ssB:load("u_2", { 2 }))
		t.eq(asked, 1, "release requested once")
		t.ok(m.clock.now - t0 >= m.Config.Services.Data.LockWaitSeconds, "waited before stealing")
		t.eq(b.data.Game.level, 5, "B sees A's last save")

		-- A's next save must be refused and A's session must end
		a.data.Game.level = 99
		local ok, err = ssA:save(a)
		t.eq(ok, false)
		t.eq(err, "stolen")
		t.eq(a.active, false)
		t.eq(m.ds.data.u_2.ns.Game.d.level, 5, "stolen session never wrote")
		t.eq(m.ds.data.u_2.meta.lock.session, b.id)
	end)

	t.test("released lock is taken immediately, stale lock is stolen without waiting", function()
		local m = fresh()
		local ss = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
		local s = assert(ss:load("u_3", { 3 }))
		ss:release(s)
		local t0 = m.clock.now
		m.env.jobId = "server-B"
		local ss2 = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
		assert(ss2:load("u_3", { 3 }))
		t.eq(m.clock.now, t0, "no wait on a released lock")

		m.ds.data.u_4 = { format = 1, meta = { created = 0, updated = 0, saves = 1,
			lock = { job = "dead-server", session = "old", place = 1, t = m.clock.now - 10_000 } }, ns = {} }
		local asked = false
		local ss3 = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() }, requestRelease = function() asked = true end })
		local t1 = m.clock.now
		assert(ss3:load("u_4", { 4 }))
		t.eq(asked, false)
		t.eq(m.clock.now, t1)
	end)

	t.test("ordered migrations upgrade old data and reconcile new template keys", function()
		local m = fresh()
		m.ds.data.u_5 = { format = 1, meta = { created = 0, updated = 0, saves = 3 },
			ns = { Game = { v = 1, d = { level = 4, spells = { "fire" } } } } }
		local order = {}
		local ss = m.SessionStore.new("P", m.ds, { namespaces = { Game = {
			version = 3,
			template = { level = 1, loadout = {}, gold = 0, opts = { music = true } },
			migrations = {
				[2] = function(d)
					table.insert(order, 2)
					d.loadout = d.spells
					d.spells = nil
				end,
				[3] = function(d)
					table.insert(order, 3)
					return { level = d.level * 10, loadout = d.loadout }
				end,
			},
		} } })
		local s = assert(ss:load("u_5", { 5 }))
		t.eq(table.concat(order, ","), "2,3")
		t.eq(s.data.Game.level, 40)
		t.eq(s.data.Game.loadout[1], "fire")
		t.eq(s.data.Game.gold, 0, "new key from template")
		t.eq(s.data.Game.opts.music, true, "nested template reconciled")
		assert(ss:save(s))
		t.eq(m.ds.data.u_5.ns.Game.v, 3, "stored with new version")
	end)

	t.test("data from a newer server version is frozen, and unknown namespaces are preserved", function()
		local m = fresh()
		m.ds.data.u_6 = { format = 1, meta = { created = 0, updated = 0, saves = 1 },
			ns = { Game = { v = 9, d = { level = 77, future = "x" } }, OtherGame = { v = 1, d = { keep = true } } } }
		local ss = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
		local s = assert(ss:load("u_6", { 6 }))
		t.ok(s.frozen.Game ~= nil, "frozen")
		s.data.Game.level = 1
		assert(ss:save(s))
		t.eq(m.ds.data.u_6.ns.Game.v, 9)
		t.eq(m.ds.data.u_6.ns.Game.d.level, 77, "newer data untouched")
		t.eq(m.ds.data.u_6.ns.OtherGame.d.keep, true, "unknown namespace kept")
	end)

	t.test("a failing migration freezes the namespace instead of corrupting it", function()
		local m = fresh()
		m.ds.data.u_7 = { format = 1, meta = { created = 0, updated = 0, saves = 1 }, ns = { Game = { v = 1, d = { level = 3 } } } }
		local ss = m.SessionStore.new("P", m.ds, { namespaces = { Game = { version = 2, template = { level = 1 },
			migrations = { [2] = function() error("boom") end } } } })
		local s = assert(ss:load("u_7", { 7 }))
		t.ok(s.frozen.Game and string.find(s.frozen.Game, "boom"), "reason recorded")
		assert(ss:save(s))
		t.eq(m.ds.data.u_7.ns.Game.v, 1)
	end)

	t.test("transient errors retry with backoff; permanent errors fail fast; exhaustion fails", function()
		local m = fresh()
		local ss = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
		m.ds:failNext("UpdateAsync", 3)
		local t0 = m.clock.now
		local s = assert(ss:load("u_8", { 8 }))
		t.eq(ss.queue.stats.retries, 3)
		t.ok(m.clock.now - t0 >= 1 + 2 + 4 - 1.5, "exponential backoff waited")
		ss:release(s)

		m.ds.calls.UpdateAsync = 0
		m.ds:failNext("UpdateAsync", 1, "104: Cannot store value")
		local s2, err = ss:load("u_9", { 9 })
		t.eq(s2, nil)
		t.ok(string.find(err, "104"), "permanent error surfaced")
		t.eq(m.ds.calls.UpdateAsync, 1, "no retries for permanent errors")

		m.ds:failNext("UpdateAsync", 100, "500: down")
		local s3 = ss:load("u_10", { 10 })
		t.eq(s3, nil)
		m.ds:failNext("UpdateAsync", 0)
	end)

	t.test("release keeps retrying through an outage until it lands", function()
		local m = fresh()
		local ss = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
		local s = assert(ss:load("u_11", { 11 }))
		s.data.Game.level = 12
		m.ds:failNext("UpdateAsync", 9) -- more than one queue run's attempts
		t.ok(ss:release(s), "eventually released")
		t.eq(m.ds.data.u_11.ns.Game.d.level, 12)
		t.eq(m.ds.data.u_11.meta.lock, nil)
	end)

	t.test("budget-aware queue: low priority gives up, critical waits", function()
		local m = fresh()
		local Queue = t.load("src/Server/Data/Queue")
		local q = Queue.new()
		m.dss.budget = 0
		local ok, err = q:run({ key = "k", priority = "Low" }, function() return 1 end)
		t.eq(ok, false)
		t.ok(string.find(err, "budget"), err)
		local waits = 0
		m.env.wait = function(s)
			waits += 1
			m.clock.now += s
			m.clock.mono += s
			if waits == 3 then
				m.dss.budget = 5
			end
		end
		local ok2, v = q:run({ key = "k", priority = "Critical" }, function() return 42 end)
		t.ok(ok2)
		t.eq(v, 42)
		t.ok(q.stats.budgetWaits >= 3)
	end)

	t.test("facade: load, update, change signal, release, rejoin and failure kick", function()
		local m = fresh()
		local Data = m.Data
		Data.useStore(m.ds)
		Data.register("Wizard", { version = 1, template = { xp = 0 } })
		local loaded, changed, releasing = 0, 0, 0
		Data.onLoaded(function() loaded += 1 end)
		Data.changed:Connect(function(_, ns) if ns == "Wizard" then changed += 1 end end)
		Data.onReleasing(function() releasing += 1 end)
		local p = Mocks.player(100)
		t.ok(Data.loadPlayer(p), "loaded")
		t.eq(loaded, 1)
		t.eq(Data.get(p).stats.joins, 1)
		t.ok(Data.update(p, function(d) d.xp += 25 end, "Wizard"))
		t.eq(changed, 1)
		t.eq(Data.get(p, "Wizard").xp, 25)
		t.ok(Data.saveAsync(p))
		t.ok(Data.releasePlayer(p))
		t.eq(releasing, 1)
		t.eq(Data.get(p, "Wizard"), nil)
		t.eq(m.ds.data.u_100.ns.Wizard.d.xp, 25)

		local p2 = Mocks.player(100)
		Data.loadPlayer(p2)
		t.eq(Data.get(p2, "Wizard").xp, 25)
		t.eq(Data.get(p2).stats.joins, 2)
		Data.releasePlayer(p2)

		m.ds:failNext("UpdateAsync", 1000, "500: outage")
		local p3 = Mocks.player(101)
		t.eq(Data.loadPlayer(p3), nil)
		t.ok(p3.kicked ~= nil, "kicked rather than playing on blank data")
		m.ds:failNext("UpdateAsync", 0)
	end)

	t.test("offline edit refuses while a fresh session lock is held", function()
		local m = fresh()
		local ss = m.SessionStore.new("P", m.ds, { namespaces = { Game = nsGame() } })
		local s = assert(ss:load("u_12", { 12 }))
		local ok = ss:editOffline("u_12", "Game", function(d) d.level = 50 end)
		t.eq(ok, false)
		ss:release(s)
		t.ok(ss:editOffline("u_12", "Game", function(d) d.level = 50 end))
		t.eq(m.ds.data.u_12.ns.Game.d.level, 50)
	end)

	t.test("settings sanitize: whitelist, clamp, step, defaults (shared UI schema, used by the server)", function()
		local Settings = t.load("src/Shared/UI/Settings")
		local v = Settings.sanitize({ music = 7, sfx = 0.333, textSize = "HUGE", reducedMotion = "yes", hacker = true, summonStyle = "Solid" })
		t.eq(v.music, 1)
		t.ok(math.abs(v.sfx - 0.35) < 1e-9, "stepped to 0.05")
		t.eq(v.textSize, "M")
		t.eq(v.reducedMotion, false)
		t.eq(v.hacker, nil)
		t.eq(v.summonStyle, "Solid")
		t.eq(Settings.sanitize(nil).autocomplete, true)
	end)
end
