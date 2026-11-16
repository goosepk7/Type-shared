-- Mocks of the Roblox services the server modules use, for Lune. Not a spec (no .spec suffix).
-- Usage: local M = t.load("tests/specs/server_mocks"); local ctx = M.setup(t, { ... })
local task = require("@lune/task")
local serde = require("@lune/serde")

local M = {}

local function jsonEncode(v)
	return serde.encode("json", v)
end
local function jsonDecode(s)
	return serde.decode("json", s)
end
local function copy(v)
	if v == nil then
		return nil
	end
	if type(v) ~= "table" then
		return v
	end
	return jsonDecode(jsonEncode(v))
end
M.copy = copy
M.jsonEncode = jsonEncode
M.jsonDecode = jsonDecode

local function deepCopy(t)
	if type(t) ~= "table" then
		return t
	end
	local o = {}
	for k, v in t do
		o[k] = deepCopy(v)
	end
	return o
end
M.deepCopy = deepCopy

local function makeSecret(name, value)
	local s = { __secret = name, __value = value }
	function s:AddPrefix(p)
		return makeSecret(name, p .. self.__value)
	end
	function s:AddSuffix(p)
		return makeSecret(name, self.__value .. p)
	end
	return setmetatable(s, { __tostring = function() return "Secret(" .. name .. ")" end })
end

function M.makeHttp(ctx)
	local Http = {}
	ctx.requests = {}
	function Http:GetSecret(name)
		local v = ctx.secrets[name]
		if v == nil then
			error("Can't find secret with given key")
		end
		return makeSecret(name, v)
	end
	function Http:JSONEncode(v)
		return jsonEncode(v)
	end
	function Http:JSONDecode(s)
		return jsonDecode(s)
	end
	function Http:UrlEncode(s)
		return (string.gsub(s, "[^%w%-_%.~]", function(c)
			return string.format("%%%02X", string.byte(c))
		end))
	end
	function Http:RequestAsync(req)
		table.insert(ctx.requests, req)
		if not ctx.httpHandler then
			error("HttpService is not allowed to access that resource")
		end
		return ctx.httpHandler(req)
	end
	return Http
end

local function makeKV(ctx, name, kind)
	local store = { data = {}, name = name, writes = 0 }
	local function check()
		if ctx.failStores then
			error(kind .. " unavailable")
		end
	end
	function store:GetAsync(k)
		check()
		return copy(self.data[k])
	end
	function store:SetAsync(k, v)
		check()
		self.writes += 1
		self.data[k] = copy(v)
		return true
	end
	function store:UpdateAsync(k, fn)
		check()
		local new = fn(copy(self.data[k]))
		if new ~= nil then
			self.writes += 1
			self.data[k] = copy(new)
		end
		return copy(self.data[k])
	end
	function store:IncrementAsync(k, n)
		check()
		self.data[k] = (self.data[k] or 0) + (n or 1)
		return self.data[k]
	end
	function store:RemoveAsync(k)
		check()
		local old = self.data[k]
		self.data[k] = nil
		return old
	end
	function store:GetSortedAsync(asc, n)
		check()
		local items = {}
		for k, v in self.data do
			table.insert(items, { key = k, value = v })
		end
		table.sort(items, function(a, b)
			if asc then return a.value < b.value end
			return a.value > b.value
		end)
		local page = {}
		for i = 1, math.min(n, #items) do
			page[i] = items[i]
		end
		return { GetCurrentPage = function() return page end }
	end
	return store
end

function M.setup(t, opts)
	opts = opts or {}
	local ctx = {
		secrets = opts.secrets or { ANTHROPIC_API_KEY = "sk-test" },
		httpHandler = nil,
		failStores = false,
		filterBad = opts.filterBad or {},
		analytics = {},
		logs = {},
		stores = {},
		ordered = {},
		maps = {},
		gameId = opts.gameId or 10777140284,
		isStudio = opts.isStudio == true,
		published = {},
		jobId = opts.jobId or "server-A",
	}
	local Http = M.makeHttp(ctx)
	local DataStoreService = {}
	function DataStoreService:GetDataStore(name)
		ctx.stores[name] = ctx.stores[name] or makeKV(ctx, name, "DataStore")
		return ctx.stores[name]
	end
	function DataStoreService:GetOrderedDataStore(name)
		ctx.ordered[name] = ctx.ordered[name] or makeKV(ctx, name, "OrderedDataStore")
		return ctx.ordered[name]
	end
	local MemoryStoreService = {}
	function MemoryStoreService:GetSortedMap(name)
		ctx.maps[name] = ctx.maps[name] or makeKV(ctx, name, "MemoryStore")
		return ctx.maps[name]
	end
	local TextService = {}
	ctx.filterCalls = 0
	function TextService:FilterStringAsync(text, userId, context)
		ctx.filterCalls += 1
		if ctx.filterDown then
			error("filter unavailable")
		end
		local function filtered()
			local out = text
			for bad in ctx.filterBad do
				out = string.gsub(out, bad, string.rep("#", #bad))
			end
			return out
		end
		return {
			GetNonChatStringForBroadcastAsync = function() return filtered() end,
			GetNonChatStringForUserAsync = function(_, toUserId) return filtered() end,
		}
	end
	local Players = { PlayerRemoving = { Connect = function() return { Disconnect = function() end } end } }
	local RunService = { IsStudio = function() return ctx.isStudio end }
	local MessagingService = {
		PublishAsync = function(_, topic, data)
			table.insert(ctx.published, { topic = topic, data = data })
		end,
		SubscribeAsync = function(_, topic, fn)
			ctx.subscriber = fn
			return { Disconnect = function() end }
		end,
	}
	ctx.services = {
		HttpService = Http,
		DataStoreService = DataStoreService,
		MemoryStoreService = MemoryStoreService,
		TextService = TextService,
		Players = Players,
		RunService = RunService,
		MessagingService = MessagingService,
	}

	-- Shared: real Schema + a copy of the real Config with fast test timings, mock Resolver/Library.
	local Schema = t.load("src/Shared/Schema")
	local RealConfig = t.load("src/Shared/Config")
	local Config = deepCopy(RealConfig)
	Config.AI.InstantTimeout = 0.25
	Config.AI.BatchWindow = 0.02
	Config.AI.BackoffBase = 0.01
	Config.AI.BackoffMax = 0.02
	Config.AI.Circuit.Cooldown = 0.3
	Config.AI.Circuit.MaxCooldown = 0.6
	Config.AI.LockPoll = 0.05
	Config.AI.LockWait = 1
	Config.AI.Mock.Latency = 0.05
	if opts.config then
		opts.config(Config)
	end
	ctx.Config = Config

	local library = opts.library or {}
	library.dragon = library.dragon or Schema.repair({
		id = "dragon", category = "Creature", element = "Fire", size = "Huge", shape = "Summon",
		behaviours = { "Flies", "Burns", "Ranged" }, power = 8, speed = 6, durability = 8, source = "Library",
		confidence = 1, signature = true, flavourText = "Breathes fire. Hoards loot. Judges you.",
		visual = { primaryColour = "#B3261E", secondaryColour = "#F2A43A", bodyPlan = "Quadruped", motionHint = "Fly", soundHint = "roar" },
	})
	ctx.library = library
	local Library = {
		get = function(id)
			local r = library[id]
			return r and Schema.clone(r) or nil
		end,
	}
	local Resolver = {
		resolveLocalDetailed = function(text, threshold)
			local lower = string.lower(text)
			if library[lower] then
				local r = Schema.clone(library[lower])
				r.input = text
				r.confidence = 1
				return r, { canonical = lower, confidence = 1, method = "Exact", alternatives = {}, tokens = { lower }, modifiers = {} }
			end
			if ctx.fuzzy and ctx.fuzzy[lower] then
				local id = ctx.fuzzy[lower]
				local r = Schema.clone(library[id])
				r.input = text
				r.confidence = 0.5
				return r, { canonical = id, confidence = 0.5, method = "Fuzzy", alternatives = {}, tokens = { lower }, modifiers = {} }
			end
			return Schema.fallback(text), { canonical = nil, confidence = 0, method = nil, alternatives = {}, tokens = { lower }, modifiers = {} }
		end,
	}
	ctx.shared = { Schema = Schema, Config = Config, Library = Library, Resolver = Resolver }
	if opts.shared then
		for k, v in opts.shared do
			ctx.shared[k] = v
		end
	end
	local sharedProxy = setmetatable({}, {
		__index = function(_, k)
			local v = ctx.shared[k]
			if v == nil then
				error("WordEngine has no module " .. tostring(k))
			end
			return v
		end,
	})

	local Analytics = {
		word = function(player, result, info)
			table.insert(ctx.analytics, { player = player, result = result, info = info })
		end,
		aiCost = function() end,
	}
	ctx.serverModules = { Analytics = Analytics }

	local Runtime = t.load("src/Server/Runtime")
	Runtime.set({
		services = ctx.services,
		task = task,
		shared = sharedProxy,
		config = Config,
		gameId = ctx.gameId,
		filterContext = "PublicChat",
		serverModules = ctx.serverModules,
		jobId = ctx.jobId,
		log = function(level, msg)
			table.insert(ctx.logs, level .. ": " .. msg)
		end,
	})
	Runtime.clearWarnOnce()
	ctx.Runtime = Runtime
	ctx.task = task

	ctx.Safety = t.load("src/Server/Safety")
	ctx.Cache = t.load("src/Server/Cache")
	ctx.AI = t.load("src/Server/AI")
	ctx.Interpreter = t.load("src/Server/Interpreter")
	ctx.Blocklist = t.load("src/Server/Blocklist")
	ctx.Blocklist._setData(nil)
	ctx.Safety.init()
	ctx.Cache.init()
	ctx.AI.init()
	ctx.Interpreter.init()

	local nextUser = 100
	function ctx.player()
		nextUser += 1
		return { UserId = nextUser, Name = "Player" .. nextUser, Parent = true }
	end

	-- AI responder helpers --------------------------------------------------------------------
	-- ctx.aiItem(key) builds a valid model item; ctx.useAI(fn) installs an Anthropic-style
	-- handler where fn(keys, req) returns (text | nil, status?, delay?).
	function ctx.aiItem(key, patch)
		local item = {
			key = key, refused = false, id = key, corrected = "", confidence = 0.8, category = "Creature",
			element = "Water", size = "Small", shape = "Summon", behaviours = { "Bounces", "Confuses" },
			power = 3, speed = 4, durability = 3, primaryColour = "#4FC3B5", secondaryColour = "#D9FFF8",
			bodyPlan = "Blob", silhouetteHint = "wobbly jelly body", motionHint = "Hop", soundHint = "boing",
			flavourText = "It wobbles with intent.", tags = { "silly" },
		}
		for k, v in patch or {} do
			item[k] = v
		end
		return item
	end
	ctx.aiCalls = 0
	function ctx.useAI(fn)
		ctx.httpHandler = function(req)
			ctx.aiCalls += 1
			local body = jsonDecode(req.Body)
			local user = body.messages[1].content
			local keys = jsonDecode(string.match(user, "\n(.*)$"))
			local text, status, delay, extra = fn(keys, req, body)
			if delay then
				task.wait(delay)
			end
			if status and status ~= 200 then
				return { Success = false, StatusCode = status, StatusMessage = "err", Headers = extra or {}, Body = "{}" }
			end
			local content = { { type = "text", text = text } }
			if body.tools and not (extra and extra.asText) then
				local ok, input = pcall(jsonDecode, text)
				if ok and type(input) == "table" then
					content = { { type = "tool_use", id = "toolu_1", name = body.tools[1].name, input = input } }
				end
			end
			local resp = {
				content = content,
				stop_reason = (extra and extra.stop_reason) or "end_turn",
				usage = { input_tokens = 1000, output_tokens = 200 },
			}
			return { Success = true, StatusCode = 200, StatusMessage = "OK", Headers = {}, Body = jsonEncode(resp) }
		end
	end
	function ctx.resultsJson(keys, patch)
		local items = {}
		for _, k in keys do
			table.insert(items, ctx.aiItem(k, patch and patch(k)))
		end
		return jsonEncode({ results = items })
	end
	return ctx
end

return M
