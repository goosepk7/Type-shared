-- WordBook: recording, synonym groups, eviction, union merge, per-game export/import seam.
return function(t)
	local Mocks = t.load("tests/mocks/services")

	local function result(id, extra)
		local r = { id = id, synonymGroup = id, element = "Fire", category = "Creature", source = "Library" }
		for k, v in extra or {} do
			r[k] = v
		end
		return r
	end

	local function fresh()
		local m = Mocks.setup(t)
		local Data = t.load("src/Server/Data")
		local WordBook = t.load("src/Server/WordBook")
		Data._reset()
		WordBook._reset()
		m.ds = m.LocalStore.new("players")
		Data.useStore(m.ds)
		m.Data, m.WordBook = Data, WordBook
		return m
	end

	t.test("record counts uses, groups synonyms and fires discovered once", function()
		local m = fresh()
		local p = Mocks.player(1)
		m.Data.loadPlayer(p)
		local found = 0
		m.WordBook.discovered:Connect(function() found += 1 end)
		local e, isNew = m.WordBook.record(p, result("dragon"))
		t.ok(isNew)
		t.eq(e.count, 1)
		m.clock.now += 50
		m.WordBook.record(p, result("dragon"))
		m.WordBook.record(p, result("kitty", { synonymGroup = "cat" }))
		m.WordBook.record(p, result("cat"))
		t.eq(found, 2)
		local d = m.WordBook.entry(p, "dragon")
		t.eq(d.count, 2)
		t.ok(d.last > d.first)
		t.eq(m.WordBook.entry(p, "cat").count, 2)
		local distinct, total = m.WordBook.count(p)
		t.eq(distinct, 2)
		t.eq(total, 4)
		t.eq(m.WordBook.get(p)[1].id, "cat", "newest first")
		t.eq(m.WordBook.top(p, 1)[1].count, 2)
		t.eq((m.WordBook.record(p, { id = "glitter blob", source = "Fallback" })), nil, "fallback not recorded")
	end)

	t.test("eviction keeps the cap and protects favourites over stale one-offs", function()
		local m = fresh()
		local entries = {}
		for i = 1, 12 do
			entries["w" .. i] = { w = "w" .. i, n = 1, f = i, l = 1000 + i, e = "Fire", c = "Object", g = 1 }
		end
		entries.w1.n = 30 -- oldest but a favourite
		local removed = m.WordBook.evict(entries, 10, 2, 100, 30)
		t.eq(removed, 4)
		t.ok(entries.w1 ~= nil, "favourite survives")
		t.eq(entries.w2, nil)
		t.eq(entries.w12 ~= nil, true)
		local n = 0
		for _ in entries do n += 1 end
		t.eq(n, 8)

		-- through record(): cap from config
		m.Config.Services.WordBook.MaxEntries = 5
		m.Config.Services.WordBook.EvictBatch = 1
		local p = Mocks.player(2)
		m.Data.loadPlayer(p)
		for i = 1, 9 do
			m.clock.now += 10
			m.WordBook.record(p, result("x" .. i))
		end
		t.ok((m.WordBook.count(p)) <= 5, "capped")
		t.ok(m.WordBook.has(p, "x9"), "newest kept")
		m.Config.Services.WordBook.MaxEntries = 1500
		m.Config.Services.WordBook.EvictBatch = 75
	end)

	t.test("merge is a commutative, idempotent union", function()
		local m = fresh()
		local a = { fire = { w = "fire", n = 3, f = 10, l = 50, e = "Fire", c = "Element", g = 1 } }
		local b = { fire = { w = "fireball", n = 5, f = 20, l = 40, e = "Fire", c = "Element", g = 2 },
			ice = { w = "ice", n = 1, f = 5, l = 5, e = "Ice", c = "Element", g = 2 } }
		local x = { fire = table.clone(a.fire) }
		m.WordBook.merge(x, b)
		local y = { fire = table.clone(b.fire), ice = table.clone(b.ice) }
		m.WordBook.merge(y, a)
		for _, key in { "fire", "ice" } do
			for _, f in { "n", "f", "l", "g", "w" } do
				t.eq(x[key][f], y[key][f], key .. "." .. f)
			end
		end
		t.eq(x.fire.n, 5)
		t.eq(x.fire.f, 10)
		t.eq(x.fire.l, 50)
		t.eq(x.fire.w, "fire", "latest canonical wins")
		t.eq(x.fire.g, 3)
		t.eq(m.WordBook.merge(x, b), 0, "idempotent")
	end)

	t.test("export/import seam merges another book without losing counts", function()
		local m = fresh()
		local p = Mocks.player(12)
		m.Data.loadPlayer(p)
		m.WordBook.setGame("Wizard")
		m.WordBook.record(p, result("asteroid"))
		local other = { asteroid = { w = "asteroid", n = 5, f = 1, l = 2, e = "Earth", c = "Disaster", g = 2 },
			tornado = { w = "tornado", n = 2, f = 1, l = 3, e = "Wind", c = "Disaster", g = 2 } }
		t.eq(m.WordBook.import(p, other), 2)
		t.eq(m.WordBook.entry(p, "asteroid").count, 5)
		t.eq(m.WordBook.entry(p, "asteroid").games, 3)
		t.eq(m.WordBook.entry(p, "tornado").count, 2)
		local ex = m.WordBook.export(p)
		ex.tornado.n = 99
		t.eq(m.WordBook.entry(p, "tornado").count, 2, "export is a copy")
	end)
end
