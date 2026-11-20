--!strict
-- Admin: live word-tuning tools for Bruce and trusted staff. Every action is validated on the server,
-- rate-limited per admin, and audit-logged (DataStore `WordEngine_Audit_v1`, one key per UTC day).
--
--   Admin.retag(id, patch, actor?)        -- change tags of a library word everywhere (patch is whitelisted)
--   Admin.forceResult(word, result, actor?) -- pin what a typed word resolves to (Schema.repair'd, source Admin)
--   Admin.ban(word, actor?) / Admin.unban(word, actor?)   -- banned words resolve to Fallback
--   Admin.clear(word, actor?)              -- remove a forced result
--   Admin.viewCache(word)                  -- Cache.peek: what the global cache holds for a word
--   Admin.testCast(word, actor?)           -- resolve a word exactly as a player would (returns WordResult)
--
-- Permanent AI cache (owned by Server/Cache; Admin validates, audits and calls its API):
--   Admin.cacheList(prefix?, cursor?)      -- browse cached phrases (DataStore ListKeysAsync, paged)
--   Admin.viewCache(word)                  -- record + meta (playCount, firstSeen, source) via Cache.peek
--   Admin.cacheEdit(word, result, actor?)  -- replace a cached result (Schema.validate'd, source Admin)
--   Admin.cacheRetag(word, patch, actor?)  -- patch a cached result's tags
--   Admin.cacheDelete(word, actor?)        -- remove from every cache layer (next cast re-resolves)
-- AI controls (owned by Server/AI):
--   Admin.setAIEnabled(on, actor?)         -- live kill switch, flips every server
--   Admin.aiStatus()                       -- enabled, today's spend vs Config.AI.DailyBudgetUSD, circuit, queue
-- Player saves (Server/Data backups = DataStore versions, 30 days):
--   /we saves <userId>                     -- list backups, newest first
--   /we restore <userId> <version>         -- roll an OFFLINE player back (audited; later purchases re-granted)
--
-- Hooks used by the Interpreter (O(1), never yield):
--   Admin.isBanned(normalized) -> boolean
--   Admin.override(normalized) -> WordResult?   (forced result, or a retagged library word)
--   Admin.apply(result) -> WordResult           (applies a retag patch to any result by id, e.g. "giant dragon")
--
-- Triggers: chat command "/we <action> <args>" (TextChatCommand; Triggered fires on the server and the
-- message is not replicated) and the RemoteFunction ReplicatedStorage.WordEngineAdmin (for the panel).
-- State lives in DataStore `WordEngine_Admin_v1` key "state" and is broadcast to all servers with
-- MessagingService so a change applies everywhere within seconds.

local Data = require(script.Parent.Data)
local Env = Data.Env
local Signal = Data.Signal

local Admin = {}
Admin.changed = Signal.new() :: Signal.Signal<string, string> -- (action, target)

type State = {
	banned: { [string]: boolean },
	forced: { [string]: any }, -- normalized -> raw result table (repaired on read)
	retag: { [string]: { [string]: any } }, -- library id -> patch
	rev: number,
}

local state: State = { banned = {}, forced = {}, retag = {}, rev = 0 }
local repairedForced: { [string]: any } = {}
local actionLog: { [number]: { number } } = {} -- userId -> timestamps (rate limit)
local started = false

local PATCHABLE = {
	category = true, element = true, size = true, shape = true, behaviours = true, power = true, speed = true,
	durability = true, flavourText = true, tags = true, signature = true, visual = true, count = true,
	synonymGroup = true,
}
local MAX_WORD = 40

local function cfg()
	return Env.config().Services.Admin
end

local function shared(): any?
	local ok, s = pcall(Env.shared)
	return if ok then s else nil
end

local function schema(): any
	local s = shared()
	return assert(s and s.Schema, "Schema unavailable")
end

-- Normalise exactly like the Interpreter does (Normalizer when present).
function Admin.normalize(word: any): string?
	if type(word) ~= "string" then
		return nil
	end
	local s = shared()
	local out: string? = nil
	if s then
		local ok, N = pcall(function()
			return s.Normalizer
		end)
		if ok and N and N.normalize then
			local ok2, n = pcall(N.normalize, word)
			if ok2 and type(n) == "string" then
				out = n
			end
		end
	end
	if out == nil then
		local x = string.lower(word)
		x = string.gsub(x, "[%c%p]", " ")
		x = string.gsub(x, "%s+", " ")
		out = string.match(x, "^%s*(.-)%s*$")
	end
	if out == nil or out == "" or #out > MAX_WORD then
		return nil
	end
	return out
end

local function rebuild()
	repairedForced = {}
	local okS, S = pcall(schema)
	for k, raw in state.forced do
		if okS then
			local r = S.repair(raw, k)
			r.source = "Admin"
			r.confidence = 1
			repairedForced[k] = r
		end
	end
end

-- Interpreter hooks ----------------------------------------------------------------------------------

function Admin.isBanned(normalized: string): boolean
	return state.banned[normalized] == true
end

local function applyPatch(result: any, patch: { [string]: any }): any
	local S = schema()
	local raw = S.clone(result)
	for k, v in patch do
		if k == "visual" and type(v) == "table" then
			for vk, vv in v do
				raw.visual[vk] = vv
			end
		else
			raw[k] = v
		end
	end
	local fixed = S.repair(raw, result.input)
	fixed.source = "Admin"
	return fixed
end

function Admin.apply(result: any): any
	local patch = type(result) == "table" and state.retag[result.id]
	if not patch then
		return result
	end
	local ok, r = pcall(applyPatch, result, patch)
	return if ok then r else result
end

function Admin.override(normalized: string): any?
	local f = repairedForced[normalized]
	if f then
		return schema().clone(f)
	end
	if next(state.retag) == nil then
		return nil
	end
	local s = shared()
	if not s then
		return nil
	end
	local ok, r = pcall(function()
		local id = s.Library.lookup(normalized)
		local patch = id and state.retag[id]
		if not patch then
			return nil
		end
		local base = s.Library.get(id)
		return base and applyPatch(base, patch)
	end)
	return if ok then r else nil
end

-- Permissions, rate limit, audit -----------------------------------------------------------------------

function Admin.isAdmin(player: any): boolean
	if type(player) ~= "table" and typeof(player) ~= "Instance" then
		return false
	end
	local uid = player.UserId
	if type(uid) ~= "number" then
		return false
	end
	if table.find(cfg().UserIds, uid) then
		return true
	end
	if Env.isStudio() then
		return true -- local Studio testing: the person at the keyboard owns the place
	end
	local g = (game :: any)
	if g and g.CreatorType == (Enum :: any).CreatorType.User and g.CreatorId == uid then
		return true
	end
	-- Group-owned experience: the group owner (rank 255) is admin automatically.
	if g and g.CreatorType == (Enum :: any).CreatorType.Group then
		local ok, rank = pcall(function()
			return player:GetRankInGroup(g.CreatorId)
		end)
		if ok and rank >= 255 then
			return true
		end
	end
	if cfg().GroupId ~= 0 then
		local ok, rank = pcall(function()
			return player:GetRankInGroup(cfg().GroupId)
		end)
		if ok and rank >= cfg().MinGroupRank then
			return true
		end
	end
	return false
end

local function rateOk(uid: number): boolean
	local now = Env.clock()
	local list = actionLog[uid] or {}
	local fresh = {}
	for _, t in list do
		if now - t < 60 then
			table.insert(fresh, t)
		end
	end
	if #fresh >= cfg().MaxActionsPerMinute then
		actionLog[uid] = fresh
		return false
	end
	table.insert(fresh, now)
	actionLog[uid] = fresh
	return true
end

local auditBuffer: { any } = {}
local function audit(actor: number, action: string, target: string, detail: string?)
	local entry = { t = math.floor(Env.now()), u = actor, a = action, w = target, d = detail and string.sub(detail, 1, 200) }
	Env.log("info", ("ADMIN %d %s %s %s"):format(actor, action, target, detail or ""))
	table.insert(auditBuffer, entry)
	if Data.isOffline() or not Env.hasService("DataStoreService") then
		return
	end
	Env.spawn(function()
		local batch = auditBuffer
		auditBuffer = {}
		if #batch == 0 then
			return
		end
		local store = Env.service("DataStoreService"):GetDataStore(cfg().AuditStoreName)
		local key = os.date("!%Y-%m-%d", entry.t) :: string
		local ok = Data.Queue.new():run({ key = "audit" .. key, priority = "Normal", attempts = 4 }, function()
			store:UpdateAsync(key, function(old: any)
				local list = if type(old) == "table" then old else {}
				for _, e in batch do
					table.insert(list, e)
				end
				while #list > 1000 do
					table.remove(list, 1)
				end
				return list
			end)
		end)
		if not ok then
			for _, e in batch do
				table.insert(auditBuffer, e) -- retried with the next action
			end
		end
	end)
end

function Admin.auditLog(dateIso: string?): { any }
	local ok, v = pcall(function()
		return Env.service("DataStoreService"):GetDataStore(cfg().AuditStoreName)
			:GetAsync(dateIso or os.date("!%Y-%m-%d", math.floor(Env.now())))
	end)
	if ok and type(v) == "table" then
		return v
	end
	return table.clone(auditBuffer)
end

-- Persistence + broadcast ------------------------------------------------------------------------------

local function persist(mutate: (State) -> ()): boolean
	mutate(state)
	state.rev += 1
	rebuild()
	if Data.isOffline() or not Env.hasService("DataStoreService") then
		return true
	end
	local store = Env.service("DataStoreService"):GetDataStore(cfg().StoreName)
	local saved: any = nil
	local ok = Data.Queue.new():run({ key = "adminstate", priority = "Normal" }, function()
		store:UpdateAsync("state", function(old: any)
			local s: State = if type(old) == "table" then old else { banned = {}, forced = {}, retag = {}, rev = 0 }
			s.banned = s.banned or {}
			s.forced = s.forced or {}
			s.retag = s.retag or {}
			mutate(s) -- re-apply onto the latest stored state (other servers may have changed it)
			s.rev = (tonumber(s.rev) or 0) + 1
			saved = s
			return s
		end)
	end)
	if ok and saved then
		state = saved
		rebuild()
		pcall(function()
			Env.service("MessagingService"):PublishAsync(cfg().Topic, { rev = state.rev })
		end)
	end
	return ok
end

local function reload()
	if Data.isOffline() or not Env.hasService("DataStoreService") then
		return
	end
	local store = Env.service("DataStoreService"):GetDataStore(cfg().StoreName)
	local v: any = nil
	local ok = Data.Queue.new():run({ key = "adminstate", requestType = "GetAsync", priority = "Normal" }, function()
		v = store:GetAsync("state")
	end)
	if ok and type(v) == "table" then
		state = { banned = v.banned or {}, forced = v.forced or {}, retag = v.retag or {}, rev = tonumber(v.rev) or 0 }
		rebuild()
	end
end
Admin.reload = reload

local function cacheModule(): any?
	return Env.server("Cache")
end

-- Actions (validated) ---------------------------------------------------------------------------------

local function validPatch(patch: any): ({ [string]: any }?, string?)
	if type(patch) ~= "table" then
		return nil, "patch must be a table"
	end
	local out = {}
	for k, v in patch do
		if not PATCHABLE[k] then
			return nil, "field not patchable: " .. tostring(k)
		end
		out[k] = v
	end
	if next(out) == nil then
		return nil, "empty patch"
	end
	-- dry-run through Schema.repair so invalid enums are caught now, not at cast time
	local S = schema()
	local probe = S.repair({ id = "probe", category = out.category, element = out.element, size = out.size,
		shape = out.shape, behaviours = out.behaviours })
	for _, key in { "category", "element", "size", "shape" } do
		if out[key] ~= nil and (probe :: any)[key] ~= out[key] then
			return nil, ("invalid %s %q (valid: %s)"):format(key, tostring(out[key]), table.concat(S.Enums[string.upper(string.sub(key, 1, 1)) .. string.sub(key, 2)], ", "))
		end
	end
	if out.behaviours ~= nil and type(out.behaviours) == "table" and #probe.behaviours ~= #out.behaviours then
		return nil, "unknown behaviour in list"
	end
	return out, nil
end

function Admin.retag(id: string, patch: any, actor: number?): (boolean, string?)
	local key = Admin.normalize(id)
	if not key then
		return false, "bad id"
	end
	local p, err = validPatch(patch)
	if not p then
		return false, err
	end
	local ok = persist(function(s)
		s.retag[key] = p :: any
	end)
	local okJ, json = pcall(function()
		return Env.service("HttpService"):JSONEncode(p)
	end)
	audit(actor or 0, "retag", key, if okJ then json else nil)
	pcall(function()
		local C = cacheModule()
		if C and C.invalidate then
			C.invalidate(key)
		end
	end)
	Admin.changed:Fire("retag", key)
	return ok, if ok then nil else "saved locally; DataStore write failed"
end

function Admin.forceResult(word: string, result: any, actor: number?): (boolean, string?)
	local key = Admin.normalize(word)
	if not key then
		return false, "bad word"
	end
	if type(result) ~= "table" then
		return false, "result must be a table"
	end
	local S = schema()
	local fixed, problems = S.validate(result)
	if not fixed then
		return false, "invalid result: " .. table.concat(problems, "; ")
	end
	fixed.input = ""
	fixed.source = "Admin"
	fixed.confidence = 1
	local ok = persist(function(s)
		s.forced[key] = fixed
	end)
	audit(actor or 0, "force", key, fixed.id .. (if #problems > 0 then " (repaired: " .. table.concat(problems, "; ") .. ")" else ""))
	pcall(function()
		local C = cacheModule()
		if C and C.put then
			C.put(key, fixed, { source = "Admin" })
		end
	end)
	Admin.changed:Fire("force", key)
	return ok, if #problems > 0 then "repaired: " .. table.concat(problems, "; ") else nil
end

function Admin.clear(word: string, actor: number?): (boolean, string?)
	local key = Admin.normalize(word)
	if not key then
		return false, "bad word"
	end
	local ok = persist(function(s)
		s.forced[key] = nil
		s.retag[key] = nil
	end)
	audit(actor or 0, "clear", key)
	pcall(function()
		local C = cacheModule()
		if C and C.invalidate then
			C.invalidate(key)
		end
	end)
	Admin.changed:Fire("clear", key)
	return ok, nil
end

function Admin.ban(word: string, actor: number?): (boolean, string?)
	local key = Admin.normalize(word)
	if not key then
		return false, "bad word"
	end
	local ok = persist(function(s)
		s.banned[key] = true
	end)
	audit(actor or 0, "ban", key)
	pcall(function()
		local C = cacheModule()
		if C and C.invalidate then
			C.invalidate(key)
		end
	end)
	Admin.changed:Fire("ban", key)
	return ok, nil
end

function Admin.unban(word: string, actor: number?): (boolean, string?)
	local key = Admin.normalize(word)
	if not key then
		return false, "bad word"
	end
	local ok = persist(function(s)
		s.banned[key] = nil
	end)
	audit(actor or 0, "unban", key)
	Admin.changed:Fire("unban", key)
	return ok, nil
end

function Admin.viewCache(word: string): { [string]: any }
	local key = Admin.normalize(word)
	if not key then
		return { error = "bad word" }
	end
	local out: { [string]: any } = { key = key, banned = Admin.isBanned(key), forced = repairedForced[key] }
	local C = cacheModule()
	if C and C.peek then
		local ok, r, meta = pcall(C.peek, key)
		if ok then
			out.cached = r
			out.meta = meta
		else
			out.error = tostring(r)
		end
	else
		out.error = "Cache module not available"
	end
	return out
end

-- Resolve as a player would. With a player, uses the full Interpreter (incl. AI); otherwise local only.
function Admin.testCast(word: string, actor: any?): any
	local key = Admin.normalize(word)
	local S = schema()
	if not key then
		return S.fallback(tostring(word))
	end
	if Admin.isBanned(key) then
		return S.fallback(key)
	end
	local forced = Admin.override(key)
	if forced then
		return forced
	end
	local I = Env.server("Interpreter")
	if I and I.interpretAsync and actor ~= nil and type(actor) ~= "number" then
		local ok, r = pcall(I.interpretAsync, actor, word, { admin = true })
		if ok and r then
			return r
		end
	end
	local s = shared()
	local ok, r = pcall(function()
		return s.Resolver.resolveLocal(word)
	end)
	if ok and r then
		return Admin.apply(r)
	end
	return S.fallback(key)
end

local function aiModule(): any?
	return Env.server("AI")
end

function Admin.cacheList(prefix: string?, cursor: string?): { keys: { string }, cursor: string? , error: string? }
	local out = { keys = {} :: { string }, cursor = nil :: string?, error = nil :: string? }
	local name = Env.config().Cache and Env.config().Cache.DataStoreName or "WordEngine_WordCache_v1"
	local p = if type(prefix) == "string" then (Admin.normalize(prefix) or "") else ""
	local ok, err = pcall(function()
		local store = Env.service("DataStoreService"):GetDataStore(name)
		local pages = store:ListKeysAsync("w1:" .. p, 50, cursor or "", true)
		for _, k in pages:GetCurrentPage() do
			local key = string.gsub(k.KeyName, "^w1:", "")
			table.insert(out.keys, key)
		end
		if not pages.IsFinished then
			out.cursor = pages.Cursor
		end
	end)
	if not ok then
		out.error = tostring(err)
	end
	return out
end

function Admin.cacheEdit(word: string, result: any, actor: number?): (boolean, string?)
	local key = Admin.normalize(word)
	if not key then
		return false, "bad word"
	end
	local C = cacheModule()
	if not (C and C.put) then
		return false, "Cache module not available"
	end
	local S = schema()
	local fixed, problems = S.validate(result)
	if not fixed then
		return false, "invalid result: " .. table.concat(problems, "; ")
	end
	fixed.input = ""
	fixed.source = "Admin"
	local ok, err = pcall(C.put, key, fixed, { source = "Admin" })
	audit(actor or 0, "cacheEdit", key, fixed.id)
	Admin.changed:Fire("cacheEdit", key)
	if not ok then
		return false, tostring(err)
	end
	return true, if #problems > 0 then "repaired: " .. table.concat(problems, "; ") else nil
end

function Admin.cacheRetag(word: string, patch: any, actor: number?): (boolean, string?)
	local key = Admin.normalize(word)
	if not key then
		return false, "bad word"
	end
	local p, perr = validPatch(patch)
	if not p then
		return false, perr
	end
	local C = cacheModule()
	if not (C and C.peek and C.put) then
		return false, "Cache module not available"
	end
	local okPeek, current = pcall(C.peek, key)
	if not okPeek or type(current) ~= "table" then
		return false, "phrase is not in the cache"
	end
	local patched = applyPatch(current, p :: any)
	patched.input = ""
	local ok, err = pcall(C.put, key, patched, { source = "Admin" })
	local okJ, json = pcall(function()
		return Env.service("HttpService"):JSONEncode(p)
	end)
	audit(actor or 0, "cacheRetag", key, if okJ then json else nil)
	Admin.changed:Fire("cacheRetag", key)
	return ok, if ok then nil else tostring(err)
end

function Admin.cacheDelete(word: string, actor: number?): (boolean, string?)
	local key = Admin.normalize(word)
	if not key then
		return false, "bad word"
	end
	local C = cacheModule()
	if not (C and C.invalidate) then
		return false, "Cache module not available"
	end
	local ok, err = pcall(C.invalidate, key)
	audit(actor or 0, "cacheDelete", key)
	Admin.changed:Fire("cacheDelete", key)
	return ok, if ok then nil else tostring(err)
end

function Admin.setAIEnabled(enabled: boolean, actor: number?): (boolean, string?)
	if type(enabled) ~= "boolean" then
		return false, "expected on/off"
	end
	local AI = aiModule()
	if not (AI and AI.setEnabled) then
		return false, "AI module not available"
	end
	local ok, res = pcall(AI.setEnabled, enabled, actor)
	audit(actor or 0, "aiEnabled", tostring(enabled))
	Admin.changed:Fire("aiEnabled", tostring(enabled))
	return ok and res ~= false, if ok then nil else tostring(res)
end

function Admin.aiStatus(): { [string]: any }
	local AI = aiModule()
	local out: { [string]: any } = {}
	if AI and AI.status then
		local ok, st = pcall(AI.status)
		if ok and type(st) == "table" then
			out = table.clone(st)
		end
	end
	if out.todayUsd == nil and AI and AI.Cost and AI.Cost.todayUsd then
		local ok, usd = pcall(AI.Cost.todayUsd)
		out.todayUsd = if ok then usd else nil
	end
	if out.enabled == nil and AI and AI.isEnabled then
		local ok, on = pcall(AI.isEnabled)
		out.enabled = if ok then on else nil
	end
	local budget = Env.config().AI and Env.config().AI.DailyBudgetUSD
	out.budgetUsd = out.budgetUsd or budget
	if type(out.todayUsd) == "number" and type(out.budgetUsd) == "number" and out.budgetUsd > 0 then
		out.spendFraction = out.todayUsd / out.budgetUsd
	end
	if next(out) == nil then
		out.error = "AI module not available"
	end
	return out
end

function Admin.state(): { banned: { string }, forced: { string }, retag: { string }, rev: number }
	local function keys(t: { [string]: any }): { string }
		local out = {}
		for k in t do
			table.insert(out, k)
		end
		table.sort(out)
		return out
	end
	return { banned = keys(state.banned), forced = keys(state.forced), retag = keys(state.retag), rev = state.rev }
end

-- Single validated entry point for chat commands and the admin remote.
-- Returns a plain table (safe to send back to the admin's client).
function Admin.handle(player: any, action: any, a: any?, b: any?): { ok: boolean, message: string, data: any? }
	if not Admin.isAdmin(player) then
		return { ok = false, message = "not an admin" }
	end
	if type(action) ~= "string" then
		return { ok = false, message = "bad action" }
	end
	if not rateOk(player.UserId) then
		return { ok = false, message = "slow down (rate limited)" }
	end
	local uid = player.UserId
	local function decode(json: any): any
		if type(json) == "table" then
			return json
		end
		if type(json) ~= "string" or #json > 4000 then
			return nil
		end
		local ok, v = pcall(function()
			return Env.service("HttpService"):JSONDecode(json)
		end)
		return if ok then v else nil
	end
	action = string.lower(action)
	if action == "ban" then
		local ok, e = Admin.ban(a, uid)
		return { ok = ok, message = e or ("banned " .. tostring(a)) }
	elseif action == "unban" then
		local ok, e = Admin.unban(a, uid)
		return { ok = ok, message = e or ("unbanned " .. tostring(a)) }
	elseif action == "clear" then
		local ok, e = Admin.clear(a, uid)
		return { ok = ok, message = e or ("cleared " .. tostring(a)) }
	elseif action == "retag" then
		local ok, e = Admin.retag(a, decode(b), uid)
		return { ok = ok, message = e or ("retagged " .. tostring(a)) }
	elseif action == "force" then
		local ok, e = Admin.forceResult(a, decode(b), uid)
		return { ok = ok, message = e or ("forced " .. tostring(a)) }
	elseif action == "cache" then
		return { ok = true, message = "cache entry", data = Admin.viewCache(a) }
	elseif action == "test" then
		local r = Admin.testCast(a, player)
		audit(uid, "test", tostring(r.id))
		local S = schema()
		return { ok = true, message = "test cast " .. r.canonical, data = S.forBroadcast(r) }
	elseif action == "state" then
		return { ok = true, message = "admin state", data = Admin.state() }
	elseif action == "stats" then
		local okA, A = pcall(function()
			return require((script.Parent :: any):FindFirstChild("Analytics"))
		end)
		return { ok = true, message = "analytics", data = okA and A.snapshot() or nil }
	elseif action == "audit" then
		return { ok = true, message = "audit log", data = Admin.auditLog(a) }
	elseif action == "cachelist" then
		return { ok = true, message = "cached phrases", data = Admin.cacheList(a, if type(b) == "string" then b else nil) }
	elseif action == "cacheedit" then
		local ok, e = Admin.cacheEdit(a, decode(b), uid)
		return { ok = ok, message = e or ("cache entry replaced: " .. tostring(a)) }
	elseif action == "cacheretag" then
		local ok, e = Admin.cacheRetag(a, decode(b), uid)
		return { ok = ok, message = e or ("cache entry retagged: " .. tostring(a)) }
	elseif action == "cachedelete" then
		local ok, e = Admin.cacheDelete(a, uid)
		return { ok = ok, message = e or ("cache entry deleted: " .. tostring(a)) }
	elseif action == "ai" then
		local want = if a == true or a == "on" then true elseif a == false or a == "off" then false else nil
		if want == nil then
			return { ok = true, message = "AI status", data = Admin.aiStatus() }
		end
		local ok, e = Admin.setAIEnabled(want :: boolean, uid)
		return { ok = ok, message = e or ("AI " .. (if want then "enabled" else "disabled") .. " on every server"), data = Admin.aiStatus() }
	elseif action == "aistatus" then
		return { ok = true, message = "AI status", data = Admin.aiStatus() }
	elseif action == "saves" then
		-- backups of a player's save (DataStore versions, newest first, 30 days)
		local target = tonumber(a)
		if not target then
			return { ok = false, message = "saves <userId>" }
		end
		local list, e = Data.listVersions(target, 25)
		if not list then
			return { ok = false, message = "could not list backups: " .. tostring(e) }
		end
		return { ok = true, message = ("%d backups of %d (newest first)"):format(#list, target), data = list }
	elseif action == "restore" then
		-- roll an OFFLINE player back to a backup; purchases made since are re-granted on their next join
		local target = tonumber(a)
		if not target or type(b) ~= "string" or #b == 0 or #b > 128 then
			return { ok = false, message = "restore <userId> <version> (see: saves <userId>)" }
		end
		local ok, e, regrants = Data.restoreVersion(target, b)
		audit(uid, "restore", tostring(target), b .. (if ok then (" ok, regrants " .. tostring(regrants)) else (" refused: " .. tostring(e))))
		return { ok = ok, message = if ok then ("restored %d to %s (%d purchase(s) will be re-granted on join)"):format(target, b, regrants) else ("restore refused: " .. tostring(e)) }
	elseif action == "unknown" or action == "history" then
		local okA, A = pcall(function()
			return require((script.Parent :: any):FindFirstChild("Analytics"))
		end)
		if not okA then
			return { ok = false, message = "Analytics not available" }
		end
		if action == "unknown" then
			return { ok = true, message = "unknown phrases", data = A.unknownPhrases(tonumber(a) or 25) }
		end
		return { ok = true, message = "daily history", data = A.history(tonumber(a) or 7) }
	end
	return { ok = false, message = "unknown action " .. action
		.. " (ban, unban, clear, retag <id> <json>, force <word> <json>, cache <word>, cachelist [prefix],"
		.. " cacheedit <word> <json>, cacheretag <word> <json>, cachedelete <word>, ai [on|off], test <word>,"
		.. " state, stats, unknown, history, audit, saves <userId>, restore <userId> <version>)" }
end

local function sendSystem(player: any, text: string)
	-- Shown by any client UI listening to ReplicatedStorage.WordEngineAdminNotice (the test place shows a toast).
	pcall(function()
		local remote = Env.service("ReplicatedStorage"):FindFirstChild("WordEngineAdminNotice")
		if remote then
			remote:FireClient(player, text)
		end
	end)
end

function Admin.start()
	if started then
		return
	end
	started = true
	Env.spawn(reload)
	pcall(function()
		Env.service("MessagingService"):SubscribeAsync(cfg().Topic, function(msg: any)
			local d = msg and msg.Data
			if type(d) == "table" and tonumber(d.rev) and tonumber(d.rev) > state.rev then
				reload()
			end
		end)
	end)
	local g = (game :: any)
	if not g then
		return
	end
	local RS = Env.service("ReplicatedStorage")
	-- Admin panel remote (server re-validates everything; non-admins get "not an admin").
	local rf = RS:FindFirstChild("WordEngineAdmin") or Instance.new("RemoteFunction")
	rf.Name = "WordEngineAdmin"
	rf.Parent = RS
	rf.OnServerInvoke = function(player, action, a, b)
		return Admin.handle(player, action, a, b)
	end
	local notice = RS:FindFirstChild("WordEngineAdminNotice") or Instance.new("RemoteEvent")
	notice.Name = "WordEngineAdminNotice"
	notice.Parent = RS

	-- Chat command: "/we ban word", "/we force word {json}", "/we test giant fire shark"
	pcall(function()
		local TCS = Env.service("TextChatService")
		local cmd = Instance.new("TextChatCommand")
		cmd.Name = "WordEngineAdminCommand"
		cmd.PrimaryAlias = cfg().CommandPrefix
		cmd.Parent = TCS
		cmd.Triggered:Connect(function(source: any, text: string)
			local player = Env.service("Players"):GetPlayerByUserId(source.UserId)
			if not player or not Admin.isAdmin(player) then
				return
			end
			local rest = string.match(text, "^%S+%s*(.*)$") or ""
			local action, args = string.match(rest, "^(%S+)%s*(.*)$")
			if not action then
				sendSystem(player, "usage: " .. cfg().CommandPrefix .. " <ban|unban|clear|retag|force|cache|cachelist|cacheedit|cacheretag|cachedelete|ai|test|state|stats|unknown|history|audit> ...")
				return
			end
			local a, b = args, nil
			if action == "retag" or action == "force" or action == "cacheedit" or action == "cacheretag" then
				local w, json = string.match(args, "^(.-)%s+(%b{})%s*$")
				a, b = w, json
			end
			local res = Admin.handle(player, action, a, b)
			local msg = res.message
			if res.data and action ~= "ban" and action ~= "unban" and action ~= "clear" then
				local ok, enc = pcall(function()
					return Env.service("HttpService"):JSONEncode(res.data)
				end)
				if ok then
					msg ..= ": " .. string.sub(enc, 1, 400)
				end
			end
			sendSystem(player, (if res.ok then "[WordEngine] " else "[WordEngine] error: ") .. msg)
		end)
	end)
end

function Admin._reset()
	state = { banned = {}, forced = {}, retag = {}, rev = 0 }
	repairedForced = {}
	actionLog = {}
	auditBuffer = {}
	started = false
	Admin.changed:DisconnectAll()
end

return Admin
