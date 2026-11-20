--!strict
-- Purchases: the ONE MarketplaceService.ProcessReceipt for the experience, plus cached game pass checks.
--
--   Purchases.registerProduct(productId, function(player, receipt) ... return true end)
--   Purchases.registerCurrencyProduct(productId, "Gems", 100)
--   Purchases.registerGamePass(passId, function(player) ... end)   -- runs on join if owned + on purchase
--   Purchases.ownsPass(player, passId) -> boolean                    -- cached (Config GamePassCacheSeconds)
--   Purchases.promptProduct(player, productId) / promptPass(player, passId)
--
-- Receipt rules (https://create.roblox.com/docs/production/monetization/developer-products):
--  * Only one ProcessReceipt callback may exist: never set MarketplaceService.ProcessReceipt elsewhere.
--  * Return PurchaseGranted only once the grant is durably saved. Anything else -> NotProcessedYet and
--    Roblox redelivers (e.g. when the player rejoins).
-- Idempotency: the PurchaseId is recorded in the player's session-locked profile IN THE SAME in-memory update
-- as the grant (handlers must not yield), then the profile is saved. Because the profile is session-locked,
-- the check-then-grant is single-writer, so a redelivered receipt can never be granted twice. A secondary
-- receipt store keeps an audit trail and catches ids that rotated out of the per-player ring.

local Data = require(script.Parent.Data)
local Env = Data.Env
local Signal = Data.Signal

export type Receipt = {
	PurchaseId: string,
	PlayerId: number,
	ProductId: number,
	CurrencySpent: number?,
	CurrencyType: any?,
	PlaceIdWherePurchased: number?,
}
type Handler = (player: any, receipt: Receipt) -> boolean?

local Purchases = {}
Purchases.granted = Signal.new() :: Signal.Signal<any, Receipt>
Purchases.passOwned = Signal.new() :: Signal.Signal<any, number>

local products: { [number]: { handler: Handler, sku: string } } = {}
local passes: { [number]: (player: any) -> () } = {}
local passCache: { [number]: { [number]: { owned: boolean, at: number } } } = {} -- userId -> passId -> entry
local inFlight: { [string]: boolean } = {}
-- Optional game-side readiness (e.g. the game's own profile repair has finished). May yield; false =
-- not ready in time -> NotProcessedYet. Without it a purchase made in the first moments of a session
-- could be refused by the game's grant and wait until the player's next join.
local readyGate: ((player: any, timeout: number) -> boolean)? = nil

function Purchases.setReadyGate(fn: ((player: any, timeout: number) -> boolean)?)
	readyGate = fn
end

local function cfg()
	return Env.config().Services.Purchases
end

local function decision(name: string): any
	local E = (Enum :: any)
	if E then
		return E.ProductPurchaseDecision[name]
	end
	return name
end
Purchases.decision = decision

function Purchases.registerProduct(productId: number, handler: Handler, sku: string?)
	assert(type(productId) == "number" and productId > 0, "productId")
	assert(type(handler) == "function", "handler")
	assert(products[productId] == nil, "product " .. productId .. " already registered")
	products[productId] = { handler = handler, sku = sku or ("product_" .. productId) }
end

function Purchases.registerCurrencyProduct(productId: number, currency: string, amount: number)
	local Currency = require((script.Parent :: any).Currency) -- resolved now, never inside the grant
	Purchases.registerProduct(productId, function(player)
		local ok = Currency.add(player, currency, amount, "IAP", currency .. "_" .. amount)
		return ok
	end, currency .. "_" .. amount)
end

function Purchases.registerGamePass(passId: number, onOwned: (player: any) -> ())
	assert(type(passId) == "number" and passId > 0, "passId")
	passes[passId] = onOwned
end

local function hasReceipt(core: any, id: string): boolean
	return core.receipts.ids[id] ~= nil
end

local function remember(core: any, id: string, productId: number)
	local r = core.receipts
	r.ids[id] = { p = productId, t = math.floor(Env.now()) }
	table.insert(r.order, id)
	while #r.order > Env.config().Services.Data.ReceiptHistory do
		local old = table.remove(r.order, 1)
		if old then
			r.ids[old] = nil
		end
	end
end

local function receiptStore(): any?
	if Data.isOffline() then
		return nil
	end
	local ok, store = pcall(function()
		return Env.service("DataStoreService"):GetDataStore(cfg().ReceiptStoreName)
	end)
	return if ok then store else nil
end

-- Secondary record: was this purchase already granted (e.g. id rotated out of the profile ring)?
local function grantedGlobally(id: string): boolean
	local store = receiptStore()
	if not store then
		return false
	end
	local value: any = nil
	local ok = Data.Queue.new():run({ key = "r" .. id, requestType = "GetAsync", priority = "Critical", attempts = 3 }, function()
		value = store:GetAsync(id)
	end)
	return ok and type(value) == "table" and value.granted == true
end

local function recordGlobally(receipt: Receipt)
	local store = receiptStore()
	if not store then
		return
	end
	Env.spawn(function()
		Data.Queue.new():run({ key = "r" .. receipt.PurchaseId, requestType = "SetIncrementAsync", priority = "Low", attempts = 4, maxBudgetWait = 60 }, function()
			store:SetAsync(receipt.PurchaseId, { granted = true, u = receipt.PlayerId, p = receipt.ProductId, t = math.floor(Env.now()) }, { receipt.PlayerId })
		end)
	end)
end

-- Runs handler without allowing it to yield: a yielding handler would let an autosave capture a grant
-- without its receipt id. Returns (ok, granted?, err?)
local function runHandler(handler: Handler, player: any, receipt: Receipt): (boolean, boolean, string?)
	local co = coroutine.create(handler)
	local ok, res = coroutine.resume(co, player, receipt)
	if not ok then
		return false, false, tostring(res)
	end
	if coroutine.status(co) ~= "dead" then
		return false, false, "handler yielded (grants must be synchronous)"
	end
	return true, res ~= false, nil
end

function Purchases.processReceipt(receipt: Receipt): any
	if type(receipt) ~= "table" or type(receipt.PurchaseId) ~= "string" then
		return decision("NotProcessedYet")
	end
	local id = receipt.PurchaseId
	if inFlight[id] then
		return decision("NotProcessedYet")
	end
	inFlight[id] = true
	local function finish(d: string)
		inFlight[id] = nil
		return decision(d)
	end

	local player = Env.service("Players"):GetPlayerByUserId(receipt.PlayerId)
	if not player then
		return finish("NotProcessedYet") -- redelivered when they rejoin
	end
	if not Data.waitFor(player, 30) then
		return finish("NotProcessedYet")
	end
	if readyGate then
		local okG, ready = pcall(readyGate :: any, player, 30)
		if not okG or ready ~= true then
			return finish("NotProcessedYet")
		end
	end
	local core = Data.get(player)
	if not core then
		return finish("NotProcessedYet")
	end

	if hasReceipt(core, id) then
		-- granted earlier in this session (or a previous one): make sure it is saved, then ack
		return finish(if Data.saveAsync(player) then "PurchaseGranted" else "NotProcessedYet")
	end
	if grantedGlobally(id) then
		Data.update(player, function(c)
			remember(c, id, receipt.ProductId)
		end)
		return finish("PurchaseGranted")
	end

	local product = products[receipt.ProductId]
	if not product then
		Env.log("error", "Purchases: no handler for product " .. tostring(receipt.ProductId))
		return finish("NotProcessedYet")
	end

	-- grant + record atomically (no yield in between)
	local granted, err = false, nil :: string?
	local recorded = Data.update(player, function(c)
		if hasReceipt(c, id) then
			return
		end
		local ok, g, e = runHandler(product.handler, player, receipt)
		if ok and g then
			remember(c, id, receipt.ProductId)
			granted = true
		else
			err = e or "handler returned false"
		end
	end)
	if not recorded or not granted then
		Env.log("error", ("Purchases: grant failed for %s: %s"):format(id, tostring(err)))
		return finish("NotProcessedYet")
	end

	if not Data.saveAsync(player) then
		-- receipt id is in memory, so a redelivery in this session won't double grant; the next
		-- autosave/release will persist both together.
		return finish("NotProcessedYet")
	end
	recordGlobally(receipt)
	Purchases.granted:Fire(player, receipt)
	local okA, A = pcall(function() return require((script.Parent :: any):FindFirstChild("Analytics")) end)
	if okA and A and A.event then
		pcall(A.event, "Purchase", { player = player, value = receipt.CurrencySpent or 0, sku = product.sku })
	end
	return finish("PurchaseGranted")
end

-- Game passes ----------------------------------------------------------------------------------------

function Purchases.ownsPass(player: any, passId: number): boolean
	local uid = player.UserId
	local byUser = passCache[uid]
	if not byUser then
		byUser = {}
		passCache[uid] = byUser
	end
	local c = (byUser :: any)[passId]
	if c and (c.owned or Env.clock() - c.at < cfg().GamePassCacheSeconds) then
		return c.owned -- ownership never goes away mid-session; only negatives expire
	end
	local ok, owned = pcall(function()
		return Env.service("MarketplaceService"):UserOwnsGamePassAsync(uid, passId)
	end)
	if not ok then
		return c ~= nil and c.owned -- keep last known on API failure
	end
	(byUser :: any)[passId] = { owned = owned == true, at = Env.clock() }
	return owned == true
end

local function grantPass(player: any, passId: number)
	local fn = passes[passId]
	if fn then
		local ok, err = pcall(fn, player)
		if not ok then
			Env.log("error", "Purchases: pass " .. passId .. " handler: " .. tostring(err))
		end
	end
	Purchases.passOwned:Fire(player, passId)
end

function Purchases.promptProduct(player: any, productId: number)
	pcall(function()
		Env.service("MarketplaceService"):PromptProductPurchase(player, productId)
	end)
end

function Purchases.promptPass(player: any, passId: number)
	pcall(function()
		Env.service("MarketplaceService"):PromptGamePassPurchase(player, passId)
	end)
end

function Purchases.onPassPurchased(player: any, passId: number, wasPurchased: boolean)
	if not wasPurchased then
		return
	end
	passCache[player.UserId] = passCache[player.UserId] or {}
	passCache[player.UserId][passId] = { owned = true, at = Env.clock() }
	grantPass(player, passId)
end

-- After a backup restore (Data.restoreVersion) the purchases made since that backup are queued in
-- core.regrant: grant each again exactly once (same synchronous rules as a receipt). Entries whose grant
-- fails stay queued for the next load. Returns how many were granted.
function Purchases.processRegrants(player: any): number
	local core = Data.get(player)
	if not core or type(core.regrant) ~= "table" or #core.regrant == 0 then
		return 0
	end
	if readyGate then
		local okG, ready = pcall(readyGate :: any, player, 30)
		if not okG or ready ~= true then
			return 0
		end
	end
	local n = 0
	Data.update(player, function(c)
		local keep = {}
		for _, r in c.regrant do
			local product = type(r) == "table" and products[r.p]
			local done = false
			if product then
				local fake: Receipt = { PurchaseId = tostring(r.id), PlayerId = player.UserId, ProductId = r.p }
				local ok, g = runHandler(product.handler, player, fake)
				done = ok and g
			end
			if done then
				n += 1
				Env.log("warn", ("Purchases: re-granted %s (product %s) after a backup restore"):format(tostring(r.id), tostring(r.p)))
			elseif type(r) == "table" then
				table.insert(keep, r) -- not granted (handler refused / product not registered yet): next load
			end
		end
		c.regrant = keep
	end)
	if n > 0 then
		Data.saveAsync(player)
	end
	return n
end

local started = false
function Purchases.start()
	if started then
		return
	end
	started = true
	local MPS = Env.service("MarketplaceService")
	MPS.ProcessReceipt = Purchases.processReceipt
	MPS.PromptGamePassPurchaseFinished:Connect(Purchases.onPassPurchased)
	Data.onLoaded(function(player)
		Env.spawn(function()
			local ok, err = pcall(Purchases.processRegrants, player)
			if not ok then
				Env.log("error", "Purchases: regrant failed: " .. tostring(err))
			end
		end)
		for passId in passes do
			Env.spawn(function()
				if Purchases.ownsPass(player, passId) then
					grantPass(player, passId)
				end
			end)
		end
	end)
	Env.service("Players").PlayerRemoving:Connect(function(p)
		passCache[p.UserId] = nil
	end)
end

function Purchases._reset()
	products = {}
	passes = {}
	passCache = {}
	inFlight = {}
	readyGate = nil
	started = false
	Purchases.granted:DisconnectAll()
	Purchases.passOwned:DisconnectAll()
end

return Purchases
