--!strict
-- Currency: integer wallets stored in the session-locked profile (namespace "WordEngine", key `wallet`).
--
--   Currency.define("Coins", { initial = 0 })                -- each game defines its own (max 5 for analytics)
--   Currency.add(player, "Coins", 50, "MatchReward")          -- -> (ok, balance)
--   Currency.spend(player, "Coins", 30, "Shop", "skin_frost") -- -> (ok, balance | "insufficient" | error)
--   Currency.balance(player, "Coins")
--   Currency.changed:Connect(fn(player, name, balance, delta))
--
-- Every change is validated (positive finite integers, defined currency, cap), applied atomically in memory
-- (check + debit in one Data.update, no yield in between), written to a short ledger, mirrored to a
-- player attribute "WE_<name>" for client UI, and reported to AnalyticsService economy events.

local Data = require(script.Parent.Data)
local Env = Data.Env
local Signal = Data.Signal

export type CurrencyDef = { initial: number, max: number? }

local Currency = {}
Currency.changed = Signal.new() :: Signal.Signal<any, string, number, number>

local defs: { [string]: CurrencyDef } = {}

-- Resolved once, outside any purchase handler (a first require must never happen inside a grant).
local analyticsMod: any = nil
local function loadAnalytics(): any
	if analyticsMod == nil then
		local ok, A = pcall(function()
			return require((script.Parent :: any):FindFirstChild("Analytics"))
		end)
		analyticsMod = if ok and A then A else false
	end
	return analyticsMod
end


local function cfg()
	return Env.config().Services.Currency
end

function Currency.define(name: string, def: CurrencyDef?)
	assert(type(name) == "string" and string.match(name, "^[%w_]+$") and #name <= 24, "currency name: 1-24 word chars")
	local d = def or { initial = 0 }
	assert(type(d.initial) == "number" and d.initial >= 0 and d.initial % 1 == 0, "initial must be a non-negative integer")
	defs[name] = { initial = d.initial, max = d.max }
	loadAnalytics()
end

function Currency.defined(name: string): boolean
	return defs[name] ~= nil
end

local function validAmount(n: any): boolean
	return type(n) == "number" and n == n and n > 0 and n ~= math.huge and n % 1 == 0
end

local function mirror(player: any, name: string, balance: number)
	pcall(function()
		player:SetAttribute("WE_" .. name, balance)
	end)
end

function Currency.balance(player: any, name: string): number
	local def = defs[name]
	local core = Data.get(player)
	if not def or not core then
		return 0
	end
	local b = core.wallet.balances[name]
	return if type(b) == "number" then b else def.initial
end

local function analytics(player: any, flow: string, name: string, amount: number, ending: number, reason: string, sku: string?)
	local A = loadAnalytics()
	if A and A.economy then
		pcall(A.economy, player, flow, name, amount, ending, reason, sku)
	end
end

local function apply(player: any, name: string, delta: number, reason: string, sku: string?): (boolean, number | string)
	local def = defs[name]
	if not def then
		return false, "unknown currency"
	end
	if not Data.isLoaded(player) then
		return false, "not loaded"
	end
	local result: number | string = "failed"
	local actual = 0
	local okUpdate = Data.update(player, function(core)
		local w = core.wallet
		local cur = w.balances[name]
		if type(cur) ~= "number" then
			cur = def.initial
		end
		local nextBal = cur + delta
		local cap = math.min(def.max or math.huge, cfg().MaxBalance)
		if nextBal < 0 then
			result = "insufficient"
			return
		end
		if nextBal > cap then
			if delta > 0 and cur >= cap then
				result = "cap"
				return
			end
			nextBal = cap
		end
		w.balances[name] = nextBal
		actual = nextBal - cur
		table.insert(w.ledger, { c = name, d = nextBal - cur, b = nextBal, r = string.sub(reason, 1, 32), t = math.floor(Env.now()) })
		while #w.ledger > cfg().LedgerSize do
			table.remove(w.ledger, 1)
		end
		result = nextBal
	end)
	if not okUpdate or type(result) ~= "number" then
		return false, result
	end
	local bal = result :: number
	mirror(player, name, bal)
	Currency.changed:Fire(player, name, bal, actual)
	analytics(player, if actual > 0 then "Source" else "Sink", name, math.abs(actual), bal, reason, sku)
	return true, bal
end

function Currency.add(player: any, name: string, amount: number, reason: string?, sku: string?): (boolean, number | string)
	if not validAmount(amount) then
		return false, "invalid amount"
	end
	return apply(player, name, amount, reason or "Gameplay", sku)
end

function Currency.spend(player: any, name: string, amount: number, reason: string?, sku: string?): (boolean, number | string)
	if not validAmount(amount) then
		return false, "invalid amount"
	end
	return apply(player, name, -amount, reason or "Shop", sku)
end

function Currency.canAfford(player: any, name: string, amount: number): boolean
	return validAmount(amount) and Currency.balance(player, name) >= amount
end

function Currency.ledger(player: any): { any }
	local core = Data.get(player)
	return core and table.clone(core.wallet.ledger) or {}
end

local started = false
function Currency.start()
	if started then
		return
	end
	started = true
	Data.onLoaded(function(player)
		for name in defs do
			mirror(player, name, Currency.balance(player, name))
		end
	end)
end

function Currency._reset()
	defs = {}
	started = false
	Currency.changed:DisconnectAll()
end

return Currency
