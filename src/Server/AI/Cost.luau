--!strict
-- AI cost + engine counters.
--   * Spend cap: every provider response's token usage is priced and added to a MemoryStore counter
--     per UTC day (hot sorted map key "spend:YYYY-MM-DD", micro-USD), shared by all servers of the
--     game. todayUsd() = last known global total + this server's not-yet-pushed spend; never yields.
--   * Engine counters for this server (AI calls, tokens, cost, cache hits, latency, fallbacks) for the
--     admin panel (snapshot). Persistent daily rollups belong to Analytics (Analytics.aiCost / .word).

local Runtime = require(script.Parent.Parent.Runtime)

local Cost = {}

local day = ""
local totals: { [string]: number } = {} -- this server, today
local pending: { [string]: number } = {} -- analytics deltas not yet flushed to the DataStore
local spendPendingMicro = 0 -- micro-USD not yet added to the MemoryStore counter
local globalMicro = 0 -- MemoryStore counter value (all servers) as last seen
local pushing = false

local function cfg(): any
	local c = Runtime.config()
	return (c and c.AI) or {}
end

local function hotMap(): any
	local c = Runtime.config()
	local name = (c and c.Cache and c.Cache.HotMapName) or "WordEngine_WordCacheHot_v1"
	return Runtime.service("MemoryStoreService"):GetSortedMap(name)
end

local function rollDay()
	local d = Runtime.dayKey()
	if d ~= day then
		day = d
		table.clear(totals)
		table.clear(pending)
		spendPendingMicro = 0
		globalMicro = 0
	end
end

function Cost.reset()
	day = ""
	table.clear(totals)
	table.clear(pending)
	spendPendingMicro = 0
	globalMicro = 0
	pushing = false
end

function Cost.count(name: string, n: number?)
	rollDay()
	local d = n or 1
	totals[name] = (totals[name] or 0) + d
	pending[name] = (pending[name] or 0) + d
end

function Cost.price(usage: any): number
	local p = cfg().Pricing or {}
	local inP = (p.InputPerMTok or 0.10) / 1e6
	local outP = (p.OutputPerMTok or 0.50) / 1e6
	return (usage.input or 0) * inP
		+ (usage.cacheRead or 0) * inP * (p.CacheReadMultiplier or 0.1)
		+ (usage.cacheWrite or 0) * inP * (p.CacheWriteMultiplier or 1.25)
		+ (usage.output or 0) * outP
end

-- Add pending spend to the shared MemoryStore counter. Yields; safe to call often.
function Cost.pushSpend()
	rollDay()
	if pushing then
		return
	end
	pushing = true
	local delta = spendPendingMicro
	spendPendingMicro = 0
	local key = "spend:" .. day
	local ok, err = pcall(function()
		local newValue = hotMap():UpdateAsync(key, function(old: any)
			return (tonumber(old) or 0) + delta
		end, 2 * 86400)
		if tonumber(newValue) then
			globalMicro = tonumber(newValue) :: number
		end
	end)
	if not ok then
		spendPendingMicro += delta
		Runtime.warnOnce("spendpush", "AI spend counter update failed: " .. tostring(err))
	end
	pushing = false
end

-- Re-read the shared counter (other servers' spend). Yields.
function Cost.refreshSpend()
	rollDay()
	pcall(function()
		local v = hotMap():GetAsync("spend:" .. day)
		if tonumber(v) then
			globalMicro = math.max(globalMicro, tonumber(v) :: number)
		end
	end)
end

-- Records one provider response. Returns its USD cost. Pushes the spend in the background.
function Cost.record(usage: any, latencyMs: number?): number
	local usd = Cost.price(usage)
	Cost.count("aiCalls", 1)
	Cost.count("tokensIn", (usage.input or 0) + (usage.cacheRead or 0) + (usage.cacheWrite or 0))
	Cost.count("tokensCacheRead", usage.cacheRead or 0)
	Cost.count("tokensOut", usage.output or 0)
	Cost.count("usd", usd)
	if latencyMs then
		Cost.count("aiLatencyMs", latencyMs)
	end
	spendPendingMicro += math.ceil(usd * 1e6)
	Runtime.task().spawn(Cost.pushSpend)
	return usd
end

-- Cross-server spend today (UTC). Never yields.
function Cost.todayUsd(): number
	rollDay()
	return (globalMicro + spendPendingMicro) / 1e6
end

function Cost.overBudget(): boolean
	local budget = cfg().DailyBudgetUSD
	if type(budget) ~= "number" or budget <= 0 then
		return false
	end
	return Cost.todayUsd() >= budget
end

function Cost.snapshot(): { [string]: any }
	rollDay()
	local out: { [string]: any } = table.clone(totals)
	out.day = day
	out.todayUsd = Cost.todayUsd()
	out.budgetUsd = cfg().DailyBudgetUSD
	local interprets = totals.interprets or 0
	out.fallbackRate = if interprets > 0 then (totals.fallbacks or 0) / interprets else 0
	local lookups = (totals.cacheHits or 0) + (totals.cacheMisses or 0)
	out.cacheHitRate = if lookups > 0 then (totals.cacheHits or 0) / lookups else 0
	out.avgAiLatencyMs = if (totals.aiCalls or 0) > 0 then (totals.aiLatencyMs or 0) / totals.aiCalls else 0
	out.avgCostPerAiPhrase = if (totals.aiResults or 0) > 0 then (totals.usd or 0) / totals.aiResults else 0
	return out
end

-- Push any unpushed spend (BindToClose / periodic). Persistent analytics rollups are written by the
-- services agent's Analytics module (DataStore "WordEngine_Analytics_v1"), fed by Analytics.aiCost/word.
function Cost.flush()
	rollDay()
	table.clear(pending)
	if spendPendingMicro > 0 then
		Cost.pushSpend()
	end
	Cost.refreshSpend()
end

return Cost
