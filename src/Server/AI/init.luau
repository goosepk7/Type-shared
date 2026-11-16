--!strict
-- AI client: pluggable provider, request queue with batching, coalescing (one in-flight lookup per
-- key per server), per-minute limiter, retries with exponential backoff + jitter, circuit breaker,
-- cost tracking and a daily budget. The model output is untrusted: AI.request resolves with a raw
-- item table that callers must pass through Prompt.toRaw -> Schema.repair.

local Runtime = require(script.Parent.Runtime)
local Json = require(script.Json)
local Prompt = require(script.Prompt)
local Circuit = require(script.Circuit)
local Cost = require(script.Cost)

local AI = {}
AI.Json = Json
AI.Prompt = Prompt
AI.Circuit = Circuit
AI.Cost = Cost

local Providers: { [string]: any } = {
	Anthropic = require(script.Providers.Anthropic),
	OpenAICompatible = require(script.Providers.OpenAICompatible),
	Mock = require(script.Providers.Mock),
}

local secret: any = nil
local secretName = "ANTHROPIC_API_KEY"
local useMock = false
local liveEnabled = true -- live kill switch (DataStore + MessagingService), see AI.setEnabled
local futures: { [string]: Runtime.Future } = {}
local queue: { string } = {}
local inflight = 0
local sentAt: { number } = {}
local flushScheduled = false
local generation = 0 -- bumps on init so stale threads from a previous init do nothing

local function cfg(): any
	local c = Runtime.config()
	return (c and c.AI) or {}
end

local function provider(): (any, any)
	local c = cfg()
	local name = if useMock then "Mock" else (c.Provider or "Anthropic")
	return Providers[name], c[name] or {}
end

-- Register an extra provider adapter ({ build(cfg, secret, args), parse(response) }).
function AI.registerProvider(name: string, adapter: any)
	Providers[name] = adapter
end

function AI.init(opts: { secretName: string? }?)
	generation += 1
	secretName = (opts and opts.secretName) or cfg().SecretName or "ANTHROPIC_API_KEY"
	secret = nil
	useMock = false
	liveEnabled = true
	table.clear(futures)
	table.clear(queue)
	table.clear(sentAt)
	inflight = 0
	flushScheduled = false
	Circuit.reset()
	Cost.reset()
	Prompt.resetCache()
	Providers.Anthropic.resetMode()
	local c = cfg()
	if c.Enabled == false then
		return
	end
	if c.Provider == "Mock" then
		useMock = true
		return
	end
	local ok, s = pcall(function()
		return Runtime.service("HttpService"):GetSecret(secretName)
	end)
	if ok and s ~= nil then
		secret = s
		return
	end
	-- Secrets exist only in live servers and Team Test. In Studio play-solo use the Mock provider.
	local okStudio, isStudio = pcall(function()
		return Runtime.service("RunService"):IsStudio()
	end)
	if okStudio and isStudio and c.MockInStudio ~= false then
		useMock = true
		Runtime.log("warn", "*** AI secret '" .. secretName .. "' not available in this Studio session: MOCK AI PROVIDER ACTIVE ***")
	else
		Runtime.log("warn", "AI disabled: secret '" .. secretName .. "' not available (library/cache only)")
	end
end

-- Live kill switch -------------------------------------------------------------------------------

function AI.isEnabled(): boolean
	return cfg().Enabled ~= false and liveEnabled
end

local function controlStore(): any
	return Runtime.service("DataStoreService"):GetDataStore(cfg().ControlStore or "WordEngine_Control_v1")
end

local function applyControl(rec: any)
	if type(rec) == "table" and type(rec.aiEnabled) == "boolean" and rec.aiEnabled ~= liveEnabled then
		liveEnabled = rec.aiEnabled
		Runtime.log("warn", "AI live switch: " .. (if liveEnabled then "ENABLED" else "DISABLED (library/cache only)"))
	end
end

-- Flip AI on/off for every server of this game. Persists (DataStore) and broadcasts
-- (MessagingService); servers also poll every Config.AI.ControlPoll seconds. Yields.
function AI.setEnabled(enabled: boolean, actorUserId: number?): boolean
	local rec = { aiEnabled = enabled == true, by = actorUserId or 0, at = Runtime.now() }
	applyControl(rec)
	local ok = pcall(function()
		controlStore():SetAsync("ai", rec)
	end)
	pcall(function()
		Runtime.service("MessagingService"):PublishAsync(cfg().ControlTopic or "WordEngineControl", rec)
	end)
	return ok
end

function AI.pollControl()
	local ok, rec = pcall(function()
		return controlStore():GetAsync("ai")
	end)
	if ok then
		applyControl(rec)
	end
end

-- Background loops: kill-switch subscription + poll, spend counter refresh. Server only.
function AI.startLoops()
	local gen = generation
	pcall(function()
		Runtime.service("MessagingService"):SubscribeAsync(cfg().ControlTopic or "WordEngineControl", function(msg: any)
			applyControl(type(msg) == "table" and msg.Data or nil)
		end)
	end)
	AI.pollControl()
	Runtime.task().spawn(function()
		local sinceControl = 0
		while gen == generation do
			local step = cfg().SpendRefreshInterval or 10
			Runtime.task().wait(step)
			if gen ~= generation then
				break
			end
			pcall(Cost.flush)
			sinceControl += step
			if sinceControl >= (cfg().ControlPoll or 30) then
				sinceControl = 0
				AI.pollControl()
			end
		end
	end)
end

function AI.hasKey(): boolean
	return secret ~= nil
end

function AI.isMock(): boolean
	return useMock
end

-- Is it worth queueing a word right now?
function AI.available(): boolean
	local c = cfg()
	if not AI.isEnabled() or (secret == nil and not useMock) then
		return false
	end
	local p, pc = provider()
	if p == nil or (p.name == "OpenAICompatible" and (pc.Endpoint == "" or pc.Model == "")) then
		return false
	end
	if #queue >= (c.MaxQueue or 64) then
		return false
	end
	return Circuit.available() and not Cost.overBudget()
end

local function settle(key: string, item: any, err: string?)
	local f = futures[key]
	if f then
		futures[key] = nil
		f:resolve(item, err)
	end
end

local function failAll(keys: { string }, err: string)
	for _, k in keys do
		settle(k, nil, err)
	end
end

local function rpmWait(): number
	local now = Runtime.clock()
	local kept = {}
	for _, t in sentAt do
		if now - t < 60 then
			table.insert(kept, t)
		end
	end
	sentAt = kept
	if #kept < (cfg().MaxRequestsPerMinute or 60) then
		return 0
	end
	return math.max(0.05, 60 - (now - kept[1]))
end

local pump: () -> ()

local function schedule(delay: number)
	if flushScheduled then
		return
	end
	flushScheduled = true
	local gen = generation
	Runtime.task().delay(delay, function()
		if gen ~= generation then
			return
		end
		flushScheduled = false
		pump()
	end)
end

-- Map model results back to keys (by echoed key, case-insensitive; positional as last resort).
local function matchResults(keys: { string }, data: any): { [string]: any }
	local list: { any } = {}
	if type(data) == "table" then
		if type(data.results) == "table" then
			list = data.results
		elseif data[1] ~= nil then
			list = data
		elseif data.id ~= nil or data.key ~= nil then
			list = { data }
		end
	end
	local byKey: { [string]: any } = {}
	local wanted: { [string]: string } = {}
	for _, k in keys do
		wanted[string.lower(k)] = k
	end
	local unmatched = {}
	for _, item in list do
		if type(item) == "table" then
			local k = type(item.key) == "string" and wanted[string.lower(item.key)] or nil
			if k and byKey[k] == nil then
				byKey[k] = item
			else
				table.insert(unmatched, item)
			end
		end
	end
	if #list == #keys then
		local u = 1
		for _, k in keys do
			if byKey[k] == nil and unmatched[u] then
				byKey[k] = unmatched[u]
				u += 1
			end
		end
	end
	return byKey
end

local function backoff(attempt: number, retryAfter: number?): number
	if retryAfter then
		return retryAfter
	end
	local c = cfg()
	local base = (c.BackoffBase or 1) * 2 ^ attempt
	return math.min(base, c.BackoffMax or 8) * (0.75 + 0.5 * Runtime.random())
end

local sendBatch: (keys: { string }, gen: number) -> ()

sendBatch = function(keys: { string }, gen: number)
	local c = cfg()
	local adapter, pcfg = provider()
	local maxTokens = (pcfg.MaxTokensBase or 120) + (pcfg.MaxTokensPerWord or 220) * #keys
	local args = {
		system = Prompt.system(),
		user = Prompt.user(keys),
		schema = Prompt.schema(),
		schemaJson = Prompt.schemaJson(),
		maxTokens = maxTokens,
		toolName = Prompt.TOOL_NAME,
		keys = keys,
	}
	local attempt = 0
	while true do
		if gen ~= generation then
			return
		end
		table.insert(sentAt, Runtime.clock())
		local t0 = Runtime.clock()
		local parsed: any
		local okReq, response
		if adapter.offline then
			okReq, parsed = pcall(adapter.respond, pcfg, keys)
			if not okReq then
				parsed = { ok = false, retryable = false, err = "mock crash", usage = {} }
				okReq = true
			end
		else
			okReq, response = pcall(function()
				local request = adapter.build(pcfg, secret, args)
				return Runtime.service("HttpService"):RequestAsync(request)
			end)
		end
		local latencyMs = math.floor((Runtime.clock() - t0) * 1000)
		if gen ~= generation then
			return
		end
		if adapter.offline then
			-- parsed already set
		elseif okReq then
			local okParse, p = pcall(adapter.parse, response)
			parsed = if okParse then p else { ok = false, retryable = true, err = "parse crash", usage = {} }
		else
			parsed = { ok = false, retryable = true, err = "request error", usage = {} }
			Runtime.warnOnce("aihttp", "AI request failed: " .. tostring(response))
		end
		local usage = parsed.usage or {}
		if (usage.input or 0) + (usage.output or 0) > 0 then
			local usd = Cost.record(usage, latencyMs)
			Runtime.call("Analytics", "aiCost", usd, (usage.input or 0) + (usage.cacheRead or 0) + (usage.cacheWrite or 0), usage.output or 0, latencyMs)
		end
		if parsed.ok then
			Circuit.success()
			local data = if type(parsed.data) == "table" then parsed.data else Json.parseLoose(parsed.text, true)
			local byKey = matchResults(keys, data)
			for _, k in keys do
				local item = byKey[k]
				if item ~= nil then
					settle(k, item, nil)
				else
					settle(k, nil, if data == nil then "bad json" else "missing")
				end
			end
			if data == nil then
				Cost.count("aiBadJson", 1)
			end
			return
		elseif parsed.refusal then
			Circuit.success() -- the provider is healthy; one input tripped its safety layer
			if #keys == 1 then
				settle(keys[1], { key = keys[1], refused = true }, nil)
			else
				-- isolate the offending word: retry each alone
				for _, k in keys do
					inflight += 1
					Runtime.task().spawn(function()
						sendBatch({ k }, gen)
						inflight -= 1
					end)
				end
			end
			return
		elseif parsed.retryable and attempt < (c.MaxRetries or 2) then
			Circuit.failure(false)
			if Circuit.state() == "Open" then
				failAll(keys, "circuit open")
				return
			end
			Runtime.task().wait(backoff(attempt, parsed.retryAfter))
			attempt += 1
		else
			Circuit.failure(parsed.auth == true)
			Cost.count("aiErrors", 1)
			failAll(keys, parsed.err or "error")
			return
		end
	end
end

pump = function()
	local c = cfg()
	while #queue > 0 and inflight < (c.MaxConcurrent or 2) do
		if (secret == nil and not useMock) or Cost.overBudget() or not AI.isEnabled() then
			local keys = queue
			queue = {}
			failAll(keys, if Cost.overBudget() then "budget" elseif not AI.isEnabled() then "disabled" else "no key")
			return
		end
		local wait = rpmWait()
		if wait > 0 then
			schedule(wait)
			return
		end
		if not Circuit.allow() then
			if Circuit.state() == "Open" then
				local keys = queue
				queue = {}
				failAll(keys, "circuit open")
				return
			end
			schedule(0.25) -- half-open probe in flight
			return
		end
		local batch = {}
		while #batch < (c.MaxBatch or 8) and #queue > 0 do
			table.insert(batch, table.remove(queue, 1) :: string)
		end
		inflight += 1
		local gen = generation
		Runtime.task().spawn(function()
			local ok, err = pcall(sendBatch, batch, gen)
			if gen ~= generation then
				return
			end
			if not ok then
				Runtime.log("warn", "AI batch crashed: " .. tostring(err))
				failAll(batch, "crash")
			end
			inflight -= 1
			if #queue > 0 then
				pump()
			end
		end)
	end
end

-- Queue a normalized key for interpretation. Returns a Future resolving (item | nil, err).
-- Identical keys share one Future (coalescing).
function AI.request(key: string): Runtime.Future
	local existing = futures[key]
	if existing then
		return existing
	end
	local f = Runtime.future()
	if not AI.available() then
		f:resolve(nil, "unavailable")
		return f
	end
	futures[key] = f
	table.insert(queue, key)
	schedule(cfg().BatchWindow or 0.12)
	return f
end

function AI.status(): { [string]: any }
	local _, pcfg = provider()
	return {
		enabled = AI.isEnabled(),
		hasKey = secret ~= nil,
		provider = if useMock then "Mock" else (cfg().Provider or "Anthropic"),
		model = pcfg.Model,
		budgetUsd = cfg().DailyBudgetUSD,
		circuit = Circuit.state(),
		queued = #queue,
		inflight = inflight,
		overBudget = Cost.overBudget(),
		todayUsd = Cost.todayUsd(),
	}
end

return AI
