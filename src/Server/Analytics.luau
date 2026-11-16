--!strict
-- Analytics: word-engine health metrics for both games.
--
-- Live (per server, Analytics.snapshot()):  words interpreted, fallback rate, cache hit rate, correction rate,
--   did-you-mean acceptance (correction success rate), AI calls, AI cost (USD) + tokens, mean AI latency,
--   most-typed words, unknown phrases with counts.
-- Unknown phrases: fallback results that Safety did not refuse, letters only (no digits => no PII), counted
--   into OrderedDataStore `WordEngine_Unknown_v1` for tools/promote.py's coverage report.
-- Roblox dashboards: AnalyticsService:LogCustomEvent with a FIXED small set of event names and the three
--   CustomField keys (cardinality-safe: Source x Element x Category < 8,000 combos), and LogEconomyEvent for
--   currencies. https://create.roblox.com/docs/production/analytics/custom-events
-- Rollup (all servers): every FlushSeconds, counters are added into DataStore `WordEngine_Analytics_v1`,
--   key "<game>/<YYYY-MM-DD>" (UpdateAsync add-merge), and per-word counts into the OrderedDataStore
--   `WordEngine_TopWords_v1` (scope = game) with IncrementAsync. All Low priority: analytics never
--   competes with player saves for request budget. Only library/AI ids are stored, never raw input.

local Data = require(script.Parent.Data)
local Env = Data.Env

local Analytics = {}

type Counters = {
	words: number,
	fallback: number,
	corrected: number,
	ai: number,
	cache: number,
	library: number,
	admin: number,
	latencyMs: number,
	latencyN: number,
	aiCostUsd: number,
	tokensIn: number,
	tokensOut: number,
	chipShown: number,
	chipAccepted: number,
	casts: number,
	purchases: number,
	robux: number,
	aiCalls: number,
	aiLatencyMs: number,
	cacheHits: number,
	unknown: number,
}

local function zero(): Counters
	return { words = 0, fallback = 0, corrected = 0, ai = 0, cache = 0, library = 0, admin = 0, latencyMs = 0,
		latencyN = 0, aiCostUsd = 0, tokensIn = 0, tokensOut = 0, chipShown = 0, chipAccepted = 0, casts = 0,
		purchases = 0, robux = 0, aiCalls = 0, aiLatencyMs = 0, cacheHits = 0, unknown = 0 }
end

local gameName = "Shared"
local live: Counters = zero() -- since server start
local pending: Counters = zero() -- since last flush
local pendingWords: { [string]: number } = {}
local pendingWordCount = 0
local liveWords: { [string]: number } = {}
local pendingUnknown: { [string]: number } = {}
local pendingUnknownCount = 0
local liveUnknown: { [string]: number } = {}
local started = false

local function cfg()
	return Env.config().Services.Analytics
end

local function service(): any?
	if not Env.hasService("AnalyticsService") then
		return nil
	end
	local ok, s = pcall(Env.service, "AnalyticsService")
	return if ok then s else nil
end

local function fieldKeys(): { string }
	local E = (Enum :: any)
	if E then
		local k = E.AnalyticsCustomFieldKeys
		return { k.CustomField01.Name, k.CustomField02.Name, k.CustomField03.Name }
	end
	return { "CustomField01", "CustomField02", "CustomField03" }
end

local function fields(a: string?, b: string?, c: string?): { [string]: string }
	local k = fieldKeys()
	local out = {}
	if a then
		out[k[1]] = a
	end
	if b then
		out[k[2]] = b
	end
	if c then
		out[k[3]] = c
	end
	return out
end

-- Generic event (DESIGN.md §4). fields: { player = Player?, value = number?, a/b/c or sku = string? }
-- Event names should come from a small fixed set (custom event names have tight cardinality limits).
function Analytics.event(name: string, f: { [string]: any }?)
	local x = f or {}
	if not cfg().Enabled then
		return
	end
	if name == "Purchase" then
		pending.purchases += 1
		live.purchases += 1
		pending.robux += tonumber(x.value) or 0
		live.robux += tonumber(x.value) or 0
	end
	local svc = service()
	if svc and x.player then
		pcall(function()
			svc:LogCustomEvent(x.player, name, tonumber(x.value) or 1, fields(x.a or x.sku, x.b, x.c))
		end)
	end
end

local function bump(word: string)
	if pendingWords[word] == nil then
		if pendingWordCount >= cfg().MaxPendingWords then
			return
		end
		pendingWordCount += 1
		pendingWords[word] = 0
	end
	pendingWords[word] += 1
	liveWords[word] = (liveWords[word] or 0) + 1
end

-- Called by the Interpreter once per interpret.
function Analytics.word(player: any, result: any, info: { [string]: any }?)
	local i = info or {}
	for _, c in { live, pending } do
		c.words += 1
		if i.fallback or result.source == "Fallback" then
			c.fallback += 1
		end
		if i.corrected then
			c.corrected += 1
		end
		if i.ai then
			c.ai += 1
		end
		if result.source == "Cache" then
			c.cache += 1
		elseif result.source == "Library" then
			c.library += 1
		elseif result.source == "Admin" then
			c.admin += 1
		end
		if type(i.latencyMs) == "number" then
			c.latencyMs += i.latencyMs
			c.latencyN += 1
		end
	end
	if result.source ~= "Fallback" and type(result.id) == "string" then
		bump(string.sub(result.id, 1, 40))
	end
	if i.cacheHit then
		live.cacheHits += 1
		pending.cacheHits += 1
	end
	if (i.fallback or result.source == "Fallback") and (i.reason == nil or i.reason == "Ok") then
		Analytics.unknownPhrase(i.normalized)
	end
	if player and cfg().Enabled then
		local svc = service()
		if svc then
			pcall(function()
				svc:LogCustomEvent(player, "WordInterpreted", 1, fields(result.source, result.element, result.category))
			end)
		end
	end
end

-- Called by games when a word is actually used (cast / placed).
function Analytics.cast(player: any, result: any)
	live.casts += 1
	pending.casts += 1
	local svc = service()
	if svc and player and cfg().Enabled then
		pcall(function()
			svc:LogCustomEvent(player, "WordCast", 1, fields(gameName, result.element, result.shape))
		end)
	end
end

-- One call per provider response (the Interpreter/AI layer reports it).
function Analytics.aiCost(usd: number, tokensIn: number?, tokensOut: number?, latencyMs: number?)
	for _, c in { live, pending } do
		c.aiCalls += 1
		c.aiCostUsd += tonumber(usd) or 0
		c.tokensIn += tonumber(tokensIn) or 0
		c.tokensOut += tonumber(tokensOut) or 0
		c.aiLatencyMs += tonumber(latencyMs) or 0
	end
end

-- Unknown phrase (resolved to Fallback without being refused). Only clean lowercase letter phrases are kept:
-- no digits or symbols (could be phone numbers, codes, personal info), 2..40 chars.
function Analytics.isLoggablePhrase(phrase: any): boolean
	return type(phrase) == "string" and #phrase >= 2 and #phrase <= 40 and string.match(phrase, "^[a-z][a-z' %-]*$") ~= nil
end

function Analytics.unknownPhrase(phrase: any)
	if not Analytics.isLoggablePhrase(phrase) then
		return
	end
	live.unknown += 1
	pending.unknown += 1
	liveUnknown[phrase] = (liveUnknown[phrase] or 0) + 1
	if pendingUnknown[phrase] == nil then
		if pendingUnknownCount >= cfg().MaxPendingUnknown then
			return
		end
		pendingUnknownCount += 1
		pendingUnknown[phrase] = 0
	end
	pendingUnknown[phrase] += 1
end

-- Did-you-mean chip. shown -> chipShown; accepted true/false resolves it.
function Analytics.correctionShown(player: any)
	live.chipShown += 1
	pending.chipShown += 1
	local _ = player
end

function Analytics.correctionAccepted(player: any, accepted: boolean)
	if accepted then
		live.chipAccepted += 1
		pending.chipAccepted += 1
	end
	local svc = service()
	if svc and player and cfg().Enabled then
		pcall(function()
			svc:LogCustomEvent(player, "DidYouMean", if accepted then 1 else 0, fields(if accepted then "Accepted" else "Ignored"))
		end)
	end
end

-- flow: "Source" | "Sink"
function Analytics.economy(player: any, flow: string, currency: string, amount: number, ending: number, transactionType: string, sku: string?)
	local svc = service()
	if not svc or not cfg().Enabled then
		return
	end
	pcall(function()
		local E = (Enum :: any)
		local flowEnum = if E then E.AnalyticsEconomyFlowType[flow] else flow
		local tx = transactionType
		if E then
			local ok, v = pcall(function()
				return E.AnalyticsEconomyTransactionType[transactionType].Name
			end)
			tx = if ok then v else transactionType
		end
		svc:LogEconomyEvent(player, flowEnum, currency, amount, ending, tx, sku or "")
	end)
end

local function rates(c: Counters): { [string]: number }
	local w = math.max(c.words, 1)
	return {
		fallbackRate = c.fallback / w,
		correctionRate = c.corrected / w,
		aiRate = c.ai / w,
		cacheRate = c.cache / w,
		cacheHitRate = c.cacheHits / w,
		unknownRate = c.unknown / w,
		correctionSuccessRate = if c.chipShown > 0 then c.chipAccepted / c.chipShown else 0,
		meanLatencyMs = if c.latencyN > 0 then c.latencyMs / c.latencyN else 0,
		meanAiLatencyMs = if c.aiCalls > 0 then c.aiLatencyMs / c.aiCalls else 0,
		aiCostPer1kWords = c.aiCostUsd / w * 1000,
		aiCostPerCall = if c.aiCalls > 0 then c.aiCostUsd / c.aiCalls else 0,
	}
end
Analytics.rates = rates

function Analytics.topLive(n: number?): { { word: string, count: number } }
	local list = {}
	for w, c in liveWords do
		table.insert(list, { word = w, count = c })
	end
	table.sort(list, function(a, b)
		if a.count == b.count then
			return a.word < b.word
		end
		return a.count > b.count
	end)
	local out = {}
	for i = 1, math.min(n or 10, #list) do
		out[i] = list[i]
	end
	return out
end

local function topOf(map: { [string]: number }, n: number?): { { word: string, count: number } }
	local list = {}
	for w, c in map do
		table.insert(list, { word = w, count = c })
	end
	table.sort(list, function(a, b)
		if a.count == b.count then
			return a.word < b.word
		end
		return a.count > b.count
	end)
	local out = {}
	for i = 1, math.min(n or 10, #list) do
		out[i] = list[i]
	end
	return out
end

function Analytics.snapshot(): { [string]: any }
	return { game = gameName, counters = table.clone(live), rates = rates(live), topWords = Analytics.topLive(10),
		unknown = topOf(liveUnknown, 10) }
end

local function dayKey(): string
	return gameName .. "/" .. os.date("!%Y-%m-%d", math.floor(Env.now()))
end

-- Push pending counters + word counts to the rollup stores. Yields. Returns success.
function Analytics.flush(): boolean
	if Data.isOffline() or not Env.hasService("DataStoreService") then
		return false
	end
	local c = cfg()
	local counters = pending
	local words = pendingWords
	pending = zero()
	pendingWords = {}
	pendingWordCount = 0
	local q = Data.Queue.new()
	local dss = Env.service("DataStoreService")
	local ok = true
	if counters.words > 0 or counters.casts > 0 or counters.aiCalls > 0 or counters.purchases > 0 then
		local store = dss:GetDataStore(c.RollupStoreName)
		local key = dayKey()
		local okW = q:run({ key = "an" .. key, priority = "Low", attempts = 3, maxBudgetWait = 20 }, function()
			store:UpdateAsync(key, function(old: any)
				local v = if type(old) == "table" then old else {}
				for k, n in counters :: any do
					v[k] = (tonumber(v[k]) or 0) + n
				end
				v.servers = v.servers or 0
				return v
			end)
		end)
		if not okW then
			ok = false
			-- put them back for the next flush
			for k, n in counters :: any do
				(pending :: any)[k] += n
			end
		end
	end
	-- top words: biggest counts first, limited per cycle (ordered store write budget is small)
	local list = {}
	for w, n in words do
		table.insert(list, { w = w, n = n })
	end
	table.sort(list, function(a, b)
		return a.n > b.n
	end)
	local ordered = dss:GetOrderedDataStore(c.TopWordsStoreName, gameName)
	for i, item in list do
		if i > c.TopWordsFlushPerCycle then
			-- carry the rest over
			if pendingWords[item.w] == nil then
				pendingWordCount += 1
			end
			pendingWords[item.w] = (pendingWords[item.w] or 0) + item.n
		else
			q:run({ key = "tw" .. item.w, requestType = "SetIncrementSortedAsync", priority = "Low", attempts = 2, maxBudgetWait = 5 }, function()
				ordered:IncrementAsync(item.w, item.n)
			end)
		end
	end
	-- unknown phrases -> OrderedDataStore (coverage report for tools/promote.py)
	local unknown = pendingUnknown
	pendingUnknown = {}
	pendingUnknownCount = 0
	local ulist = {}
	for w, n in unknown do
		table.insert(ulist, { w = w, n = n })
	end
	table.sort(ulist, function(a, b)
		return a.n > b.n
	end)
	if #ulist > 0 then
		local ustore = dss:GetOrderedDataStore(c.UnknownStoreName)
		for i, item in ulist do
			if i > c.UnknownFlushPerCycle then
				if pendingUnknown[item.w] == nil then
					pendingUnknownCount += 1
				end
				pendingUnknown[item.w] = (pendingUnknown[item.w] or 0) + item.n
			else
				q:run({ key = "uk" .. item.w, requestType = "SetIncrementSortedAsync", priority = "Low", attempts = 2, maxBudgetWait = 5 }, function()
					ustore:IncrementAsync(item.w, item.n)
				end)
			end
		end
	end
	return ok
end

-- Most common unknown phrases (all servers, all time) from the OrderedDataStore. Yields.
function Analytics.unknownPhrases(n: number?): { { word: string, count: number } }
	local out = {}
	pcall(function()
		local ordered = Env.service("DataStoreService"):GetOrderedDataStore(cfg().UnknownStoreName)
		local pages = ordered:GetSortedAsync(false, math.clamp(n or 20, 1, 100))
		for _, row in pages:GetCurrentPage() do
			table.insert(out, { word = row.key, count = row.value })
		end
	end)
	return out
end

-- Last `days` daily rollups (newest first) for the admin dashboard: AI calls/day, cost/day, cache hit rate,
-- mean AI latency, fallback rate.
function Analytics.history(days: number?): { any }
	local out = {}
	local now = math.floor(Env.now())
	for d = 0, math.clamp(days or 7, 1, 30) - 1 do
		local iso = os.date("!%Y-%m-%d", now - d * 86400) :: string
		local day = Analytics.daily(iso)
		if day then
			table.insert(out, day)
		end
	end
	return out
end

-- All-time most-typed words for this game (from the OrderedDataStore). Yields.
function Analytics.topWords(n: number?): { { word: string, count: number } }
	local out = {}
	local okRun = pcall(function()
		local ordered = Env.service("DataStoreService"):GetOrderedDataStore(cfg().TopWordsStoreName, gameName)
		local pages = ordered:GetSortedAsync(false, math.clamp(n or 20, 1, 100))
		for _, row in pages:GetCurrentPage() do
			table.insert(out, { word = row.key, count = row.value })
		end
	end)
	local _ = okRun
	return out
end

-- Day rollup for this game: counters + derived rates. Yields.
function Analytics.daily(dateIso: string?): { [string]: any }?
	local key = gameName .. "/" .. (dateIso or os.date("!%Y-%m-%d", math.floor(Env.now())))
	local ok, v = pcall(function()
		return Env.service("DataStoreService"):GetDataStore(cfg().RollupStoreName):GetAsync(key)
	end)
	if not ok or type(v) ~= "table" then
		return nil
	end
	local c = zero()
	for k in c :: any do
		(c :: any)[k] = tonumber(v[k]) or 0
	end
	return { key = key, counters = c, rates = rates(c) }
end

function Analytics.start(name: string?)
	if started then
		return
	end
	started = true
	gameName = name or gameName
	Env.spawn(function()
		while started do
			Env.wait(cfg().FlushSeconds)
			Analytics.flush()
		end
	end)
	local g = (game :: any)
	if g then
		g:BindToClose(function()
			Analytics.flush()
		end)
	end
end

function Analytics._reset()
	started = false
	live, pending = zero(), zero()
	pendingWords, liveWords = {}, {}
	pendingWordCount = 0
	pendingUnknown, liveUnknown = {}, {}
	pendingUnknownCount = 0
end

function Analytics._setGame(name: string)
	gameName = name
end

return Analytics
