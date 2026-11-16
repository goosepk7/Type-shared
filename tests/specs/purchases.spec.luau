-- Purchases: single ProcessReceipt dispatcher, idempotent receipts, save-before-grant, game pass cache.
return function(t)
	local Mocks = t.load("tests/mocks/services")

	local function fresh()
		local m = Mocks.setup(t)
		local Data = t.load("src/Server/Data")
		local Currency = t.load("src/Server/Currency")
		local Purchases = t.load("src/Server/Purchases")
		Data._reset()
		Currency._reset()
		Purchases._reset()
		m.ds = m.LocalStore.new("players")
		Data.useStore(m.ds)
		Currency.define("Gems", { initial = 0 })
		local online = {}
		m.env.services.Players = {
			GetPlayerByUserId = function(_, id)
				return online[id]
			end,
		}
		m.passOwned = {}
		m.passCalls = 0
		m.env.services.MarketplaceService = {
			UserOwnsGamePassAsync = function(_, uid, passId)
				m.passCalls += 1
				if m.passError then
					error("HTTP 500")
				end
				return m.passOwned[uid .. ":" .. passId] == true
			end,
		}
		m.online = online
		m.Data, m.Currency, m.Purchases = Data, Currency, Purchases
		return m
	end

	local function join(m, id)
		local p = Mocks.player(id)
		m.online[id] = p
		m.Data.loadPlayer(p)
		return p
	end

	local function receipt(id, pid, product)
		return { PurchaseId = id, PlayerId = pid, ProductId = product, CurrencySpent = 99 }
	end

	t.test("grants once, saves before acknowledging, and is idempotent on redelivery", function()
		local m = fresh()
		m.Purchases.registerCurrencyProduct(111, "Gems", 100)
		local p = join(m, 1)
		local before = m.ds.calls.UpdateAsync or 0
		local d1 = m.Purchases.processReceipt(receipt("r1", 1, 111))
		t.eq(d1, "PurchaseGranted")
		t.ok((m.ds.calls.UpdateAsync or 0) > before, "saved before granting")
		t.eq(m.ds.data.u_1.ns.WordEngine.d.wallet.balances.Gems, 100, "grant is durable")
		t.ok(m.ds.data.u_1.ns.WordEngine.d.receipts.ids.r1 ~= nil, "receipt id durable with the grant")
		t.eq(m.Purchases.processReceipt(receipt("r1", 1, 111)), "PurchaseGranted")
		t.eq(m.Purchases.processReceipt(receipt("r1", 1, 111)), "PurchaseGranted")
		t.eq(m.Currency.balance(p, "Gems"), 100, "redelivery did not double grant")
		t.eq(m.Purchases.processReceipt(receipt("r2", 1, 111)), "PurchaseGranted")
		t.eq(m.Currency.balance(p, "Gems"), 200)
	end)

	t.test("redelivery after rejoin (new session) is still idempotent", function()
		local m = fresh()
		m.Purchases.registerCurrencyProduct(111, "Gems", 50)
		local p = join(m, 2)
		t.eq(m.Purchases.processReceipt(receipt("r9", 2, 111)), "PurchaseGranted")
		m.Data.releasePlayer(p)
		m.online[2] = nil
		local p2 = join(m, 2)
		t.eq(m.Purchases.processReceipt(receipt("r9", 2, 111)), "PurchaseGranted")
		t.eq(m.Currency.balance(p2, "Gems"), 50)
	end)

	t.test("player not in server, unknown product, failing or yielding handler -> NotProcessedYet", function()
		local m = fresh()
		t.eq(m.Purchases.processReceipt(receipt("x1", 77, 111)), "NotProcessedYet")
		local p = join(m, 3)
		t.eq(m.Purchases.processReceipt(receipt("x2", 3, 424242)), "NotProcessedYet")
		m.Purchases.registerProduct(5, function() error("boom") end)
		t.eq(m.Purchases.processReceipt(receipt("x3", 3, 5)), "NotProcessedYet")
		m.Purchases.registerProduct(6, function() return false end)
		t.eq(m.Purchases.processReceipt(receipt("x4", 3, 6)), "NotProcessedYet")
		m.Purchases.registerProduct(7, function()
			coroutine.yield()
			return true
		end)
		t.eq(m.Purchases.processReceipt(receipt("x5", 3, 7)), "NotProcessedYet")
		t.eq(m.Data.get(p).receipts.ids.x3, nil, "failed receipts not recorded")
		t.eq(m.Purchases.processReceipt(nil), "NotProcessedYet")
	end)

	t.test("save failure -> NotProcessedYet, then the retry acks without granting again", function()
		local m = fresh()
		m.Purchases.registerCurrencyProduct(111, "Gems", 10)
		local p = join(m, 4)
		m.ds:failNext("UpdateAsync", 100, "500: outage")
		t.eq(m.Purchases.processReceipt(receipt("s1", 4, 111)), "NotProcessedYet")
		m.ds:failNext("UpdateAsync", 0)
		t.eq(m.Purchases.processReceipt(receipt("s1", 4, 111)), "PurchaseGranted")
		t.eq(m.Currency.balance(p, "Gems"), 10)
		t.eq(m.ds.data.u_4.ns.WordEngine.d.wallet.balances.Gems, 10)
	end)

	t.test("receipt ring rotates; the global receipt store still blocks old duplicates", function()
		local m = fresh()
		m.Config.Services.Data.ReceiptHistory = 3
		m.Purchases.registerCurrencyProduct(111, "Gems", 1)
		local p = join(m, 5)
		for i = 1, 5 do
			t.eq(m.Purchases.processReceipt(receipt("q" .. i, 5, 111)), "PurchaseGranted")
		end
		t.eq(m.Data.get(p).receipts.ids.q1, nil, "rotated out of the ring")
		t.eq(m.Purchases.processReceipt(receipt("q1", 5, 111)), "PurchaseGranted")
		t.eq(m.Currency.balance(p, "Gems"), 5, "no double grant")
		m.Config.Services.Data.ReceiptHistory = 64
	end)

	t.test("game pass checks are cached; purchases flip the cache and fire the handler", function()
		local m = fresh()
		local p = join(m, 6)
		local fired = 0
		m.Purchases.registerGamePass(900, function() fired += 1 end)
		t.eq(m.Purchases.ownsPass(p, 900), false)
		t.eq(m.Purchases.ownsPass(p, 900), false)
		t.eq(m.passCalls, 1, "negative cached")
		m.clock.mono += m.Config.Services.Purchases.GamePassCacheSeconds + 1
		m.Purchases.ownsPass(p, 900)
		t.eq(m.passCalls, 2, "negative expires")
		m.Purchases.onPassPurchased(p, 900, true)
		t.eq(fired, 1)
		m.passError = true
		t.eq(m.Purchases.ownsPass(p, 900), true, "purchase cached; no API call needed")
		t.eq(m.passCalls, 2)
	end)
end
