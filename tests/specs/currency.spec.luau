-- Currency: validation, atomic spend, caps, ledger, persistence, attribute mirror.
return function(t)
	local Mocks = t.load("tests/mocks/services")

	local function fresh()
		local m = Mocks.setup(t)
		local Data = t.load("src/Server/Data")
		local Currency = t.load("src/Server/Currency")
		Data._reset()
		Currency._reset()
		m.ds = m.LocalStore.new("players")
		Data.useStore(m.ds)
		Currency.define("Coins", { initial = 10 })
		Currency.define("Gems", { initial = 0, max = 100 })
		m.Data, m.Currency = Data, Currency
		local p = Mocks.player(1)
		p.attrs = {}
		function p:SetAttribute(k, v)
			self.attrs[k] = v
		end
		Data.loadPlayer(p)
		m.p = p
		return m
	end

	t.test("initial balance, add and spend", function()
		local m = fresh()
		t.eq(m.Currency.balance(m.p, "Coins"), 10)
		local ok, bal = m.Currency.add(m.p, "Coins", 15, "Quest")
		t.ok(ok)
		t.eq(bal, 25)
		ok, bal = m.Currency.spend(m.p, "Coins", 20, "Shop", "hat")
		t.ok(ok)
		t.eq(bal, 5)
		t.eq(m.p.attrs.WE_Coins, 5, "mirrored to attribute")
		local ledger = m.Currency.ledger(m.p)
		t.eq(#ledger, 2)
		t.eq(ledger[2].d, -20)
	end)

	t.test("rejects invalid amounts, unknown currencies and overspend", function()
		local m = fresh()
		for _, bad in { 0, -5, 1.5, 0 / 0, math.huge, "10" } do
			t.eq((m.Currency.add(m.p, "Coins", bad)), false, "amount " .. tostring(bad))
			t.eq((m.Currency.spend(m.p, "Coins", bad)), false, "spend " .. tostring(bad))
		end
		t.eq((m.Currency.add(m.p, "Nope", 5)), false)
		local ok, why = m.Currency.spend(m.p, "Coins", 11)
		t.eq(ok, false)
		t.eq(why, "insufficient")
		t.eq(m.Currency.balance(m.p, "Coins"), 10, "unchanged after failed spend")
		t.ok(m.Currency.canAfford(m.p, "Coins", 10))
		t.eq(m.Currency.canAfford(m.p, "Coins", 11), false)
	end)

	t.test("caps clamp and refuse when already full", function()
		local m = fresh()
		local ok, bal = m.Currency.add(m.p, "Gems", 150)
		t.ok(ok)
		t.eq(bal, 100)
		local ok2, why = m.Currency.add(m.p, "Gems", 1)
		t.eq(ok2, false)
		t.eq(why, "cap")
	end)

	t.test("changed signal reports the applied delta; balances persist across sessions", function()
		local m = fresh()
		local seen = {}
		m.Currency.changed:Connect(function(_, name, bal, delta)
			table.insert(seen, name .. ":" .. bal .. ":" .. delta)
		end)
		m.Currency.add(m.p, "Gems", 120)
		t.eq(seen[1], "Gems:100:100")
		m.Data.releasePlayer(m.p)
		t.eq(m.Currency.balance(m.p, "Gems"), 0, "no data while not loaded")
		local p2 = Mocks.player(1)
		m.Data.loadPlayer(p2)
		t.eq(m.Currency.balance(p2, "Gems"), 100)
	end)

	t.test("not-loaded players cannot transact", function()
		local m = fresh()
		local ghost = Mocks.player(999)
		t.eq((m.Currency.add(ghost, "Coins", 5)), false)
	end)
end
