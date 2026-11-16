--!strict
-- Interpreter: typed text -> WordResult, fast and cheap. DESIGN §4/§5.
--
--   Safety (typing rate limit, spam, blocklist) -> Admin ban/override
--   -> per-server memory cache (no yield)
--   -> library + phrase parser (Resolver, pure Luau). Exact/alias library hits return here: the remote
--      cache could only hold the same thing, and skipping it saves MemoryStore/DataStore budget.
--   -> one coalesced job per core phrase across this server:
--        MemoryStore hot -> DataStore permanent (follows typo alias records)
--        -> only if library confidence < Config.AI.Threshold:
--           mash / kill switch / daily cap / per-player NEW-phrase gates
--           -> TextService filter of the phrase (hashed => no AI, Fallback)
--           -> cross-server MemoryStore lock per phrase (other servers wait for the result)
--           -> AI (Claude, strict JSON via a forced tool) -> Schema.repair + balance clamp
--           -> library reconciliation -> blocklist + filter the AI's own text
--           -> permanent cache write (retries + queue) + typo alias record -> unlock
--   interpretAsync waits up to Config.AI.InstantTimeout for that job, then returns the best guess;
--   if the job finishes later with something better, handle.upgraded fires once.
--
-- Never errors, never returns nil. Leading modifiers ("giant fire ...") are split off before the
-- cache/AI key so "giant blorp" and "tiny blorp" share one AI call, then re-applied.

local Runtime = require(script.Parent.Runtime)
local Safety = require(script.Parent.Safety)
local Cache = require(script.Parent.Cache)
local AI = require(script.Parent.AI)

local Interpreter = {}

export type Handle = {
	upgraded: Runtime.Signal, -- fires once with (newResult)
	pending: boolean, -- an AI/Cache upgrade may still arrive
	reason: string, -- "Ok" | "Empty" | "RateLimited" | "Spam" | "Blocked" | "Banned" | "Filtered" | "Refused" | "Error"
	result: any,
}

local jobs: { [string]: Runtime.Future } = {}

local GENERIC_FLAVOUR = {
	"It crackles with mysterious energy.",
	"Nobody is sure what it is. It seems keen.",
	"Freshly conjured. Handle with care.",
}

local function cfg(): any
	local c = Runtime.config()
	return (c and c.AI) or {}
end

local function Schema(): any
	return Runtime.sharedModule("Schema")
end

local function newHandle(): Handle
	return { upgraded = Runtime.signal(true), pending = false, reason = "Ok", result = nil }
end

local function fallback(text: string): any
	return Schema().fallback(text)
end

-- (result, spell) from the shared library pipeline; never errors.
local function resolveLocal(text: string, threshold: number): (any, any)
	local Resolver = Runtime.sharedModule("Resolver")
	if Resolver then
		if Resolver.resolveLocalDetailed then
			local ok, r, spell = pcall(Resolver.resolveLocalDetailed, text, threshold)
			if ok and type(r) == "table" then
				return r, spell
			end
		elseif Resolver.resolveLocal then
			local ok, r = pcall(Resolver.resolveLocal, text)
			if ok and type(r) == "table" then
				return r, nil
			end
		end
	end
	return fallback(text), nil
end

local function isLibraryExact(r: any, spell: any): boolean
	if r.source ~= "Library" or (tonumber(r.confidence) or 0) < 0.9 then
		return false
	end
	if type(spell) == "table" and type(spell.method) == "string" then
		return spell.method == "Exact" or spell.method == "Alias" or spell.method == "Normalized"
	end
	return r.correction == nil
end

-- Split leading modifiers off: "giant fire blorp" -> ("blorp", {giant, fire}).
local function splitModifiers(normalized: string): (string, { any })
	local Normalizer = Runtime.sharedModule("Normalizer")
	local Modifiers = Runtime.sharedModule("Modifiers")
	if not (Normalizer and Normalizer.tokenize and Modifiers and Modifiers.parse) then
		return normalized, {}
	end
	local ok, rest, mods = pcall(function()
		local tokens = Normalizer.tokenize(normalized)
		return Modifiers.parse(tokens)
	end)
	if not ok or type(rest) ~= "table" or #rest == 0 then
		return normalized, {}
	end
	return table.concat(rest, " "), if type(mods) == "table" then mods else {}
end

local function applyModifiers(r: any, mods: { any }): any
	if #mods == 0 then
		return r
	end
	local Modifiers = Runtime.sharedModule("Modifiers")
	if Modifiers and Modifiers.apply then
		local ok, out = pcall(Modifiers.apply, r, mods)
		if ok and type(out) == "table" then
			return out
		end
	end
	return r
end

-- Admin retag patches (by result.id) apply to every final result, incl. modified ones.
local function finalize(r: any): any
	local ok, out = Runtime.call("Admin", "apply", r)
	if ok and type(out) == "table" then
		return out
	end
	return r
end

-- Model item -> clamped WordResult (or nil when unusable). Second value: true when it's a library entry.
local function buildFromItem(item: any, core: string): (any, boolean)
	local Prompt = AI.Prompt
	local raw = Prompt.toRaw(item)
	if raw == nil then
		return nil, false
	end
	local r = Schema().repair(raw, core)
	if r.source == "Fallback" then
		return nil, false
	end
	r.source = "AI"
	r.signature = false
	r.count = 1
	r.modifiers = {}
	r.synonymGroup = r.id
	r.canonical = r.id
	Prompt.clampPower(r)
	if r.flavourText == "" then
		r.flavourText = GENERIC_FLAVOUR[(#core % #GENERIC_FLAVOUR) + 1]
	end
	-- The AI fixed a typo of a hand-tagged word: prefer the library entry (consistent visuals/stats).
	local Library = Runtime.sharedModule("Library")
	if Library and Library.get then
		local ok, lib = pcall(Library.get, r.id)
		if ok and type(lib) == "table" then
			local libResult = Schema().clone(lib)
			libResult.confidence = math.max(r.confidence, 0.75)
			return libResult, true
		end
	end
	return r, false
end

-- The AI path for one phrase (runs inside a job). Returns (result?, err?).
local function askAI(core: string, player: any): (any, string?)
	if Safety.looksLikeMash(core) then
		return nil, "mash"
	end
	if not AI.available() then
		return nil, if AI.isEnabled() then "unavailable" else "disabled"
	end
	if not Safety.allowNewPhrase(player) then
		return nil, "playerLimit"
	end
	-- Filter the phrase before it leaves Roblox (DESIGN §9: hashed => no AI, Fallback).
	local filtered = Safety.filterForBroadcast(player, core)
	if Safety.isHashed(core, filtered) then
		return nil, "filtered"
	end

	-- Cross-server de-dup: one server per phrase pays; the rest wait for its result.
	local locked = false
	for _ = 1, 3 do
		if Cache.lock(core) then
			locked = true
			break
		end
		AI.Cost.count("lockWaits", 1)
		local r, meta, status = Cache.waitForResult(core, cfg().LockWait or 12)
		if status == "result" and r then
			if r.source ~= "Library" then
				r.source = "Cache"
			end
			return r, nil
		elseif status == "refused" or (meta and meta.refused) then
			return nil, "refused"
		elseif status == "timeout" then
			break -- holder is stuck: go ahead ourselves
		end
		-- "released" without a result: the holder failed; try to take the lock
	end
	local function release()
		if locked then
			Cache.unlock(core)
		end
	end
	if locked then
		-- Someone may have finished between our miss and our lock.
		local r, meta = Cache.peek(core)
		if meta and meta.refused then
			release()
			return nil, "refused"
		end
		if r then
			release()
			if r.source ~= "Library" then
				r.source = "Cache"
			end
			return r, nil
		end
	end

	local _, item, aiErr = AI.request(core):await(nil)
	if item == nil then
		release()
		return nil, aiErr or "ai"
	end
	if type(item) == "table" and item.refused == true then
		Cache.putAsync(core, nil, { source = "AI", refused = true })
		release()
		return nil, "refused"
	end
	local r, isLibrary = buildFromItem(item, core)
	if r == nil then
		release()
		return nil, "unusable"
	end
	-- The AI's own words are shown to players: blocklist + TextService them too.
	if Safety.isBlocked(r.id) or Safety.isBlocked(r.flavourText) then
		Cache.putAsync(core, nil, { source = "AI", refused = true })
		release()
		return nil, "refused"
	end
	if not isLibrary then
		local fc = Safety.filterForBroadcast(player, r.id)
		if Safety.isHashed(r.id, fc) then
			release()
			return nil, "filtered"
		end
		local ff = Safety.filterForBroadcast(player, r.flavourText)
		if Safety.isHashed(r.flavourText, ff) then
			r.flavourText = GENERIC_FLAVOUR[(#core % #GENERIC_FLAVOUR) + 1]
		end
	end
	AI.Cost.count("aiResults", 1)
	-- Persist (paid result: retries + queue), then the typo alias, then let other servers in.
	local stored = Schema().clone(r)
	Runtime.task().spawn(function()
		if isLibrary then
			Cache.putAlias(core, stored.id)
		elseif stored.id ~= core then
			Cache.putAsync(stored.id, stored, { source = "AI" })
			Cache.putAlias(core, stored.id)
		else
			Cache.putAsync(core, stored, { source = "AI" })
		end
		release()
	end)
	return r, nil
end

local function jobFor(core: string, needAI: boolean, player: any): Runtime.Future
	local jobKey = core .. (if needAI then "\0ai" else "")
	local existing = jobs[jobKey]
	if existing then
		return existing
	end
	local f = Runtime.future()
	jobs[jobKey] = f
	Runtime.task().spawn(function()
		local ok, value, err = pcall(function(): (any, string?)
			local hit, meta = Cache.get(core)
			if meta and meta.refused then
				return nil, "refused"
			end
			if hit then
				AI.Cost.count("cacheHits", 1)
				if hit.source ~= "Library" then
					hit.source = "Cache"
				end
				return hit, nil
			end
			AI.Cost.count("cacheMisses", 1)
			if not needAI then
				return nil, "miss"
			end
			return askAI(core, player)
		end)
		jobs[jobKey] = nil
		if ok then
			f:resolve(value, err)
		else
			Runtime.log("warn", "interpret job failed: " .. tostring(value))
			f:resolve(nil, "error")
		end
	end)
	return f
end

-- Personalise a shared job result for this request (input, correction, modifiers).
local function adapt(v: any, text: string, core: string, mods: { any }, spell: any): any
	local r = Schema().clone(v)
	r.input = text
	local canon = r.id
	if canon ~= core then
		local alts = {}
		if type(spell) == "table" and type(spell.alternatives) == "table" then
			for _, a in spell.alternatives do
				if type(a) == "string" and a ~= canon and #alts < 3 then
					table.insert(alts, a)
				end
			end
		end
		r.correction = { method = "AI", from = text, to = canon, confidence = r.confidence, alternatives = alts }
	elseif r.correction then
		r.correction.from = text
	end
	return applyModifiers(r, mods)
end

local function isUsable(r: any): boolean
	return type(r) == "table" and r.source ~= "Fallback" and (tonumber(r.confidence) or 0) > 0
end

local function report(player: any, result: any, handle: Handle, normalized: string, t0: number, viaAI: boolean, cacheHit: boolean?)
	AI.Cost.count("interprets", 1)
	AI.Cost.count("src" .. tostring(result.source), 1)
	local latency = (Runtime.clock() - t0) * 1000
	AI.Cost.count("latencyMs", latency)
	if result.source == "Fallback" then
		AI.Cost.count("fallbacks", 1)
	end
	if result.source == "AI" or result.source == "Cache" then
		Cache.recordPlay(normalized)
	end
	Runtime.call("Analytics", "word", player, Schema().forBroadcast(result), {
		normalized = normalized,
		fallback = result.source == "Fallback",
		corrected = result.correction ~= nil,
		ai = viaAI,
		cacheHit = cacheHit == true,
		source = result.source,
		reason = handle.reason,
		pending = handle.pending,
		latencyMs = math.floor(latency),
	})
end

local REASONS: { [string]: string } = { refused = "Refused", filtered = "Filtered" }

local function run(player: any, text: any, opts: any, handle: Handle): any
	local t0 = Runtime.clock()
	local check = Safety.check(player, text)
	if not check.ok then
		handle.reason = check.reason
		local r = fallback(check.text)
		report(player, r, handle, check.normalized, t0, false)
		return r
	end
	local normalized = check.normalized
	local raw = check.text

	-- Admin ban / override (services agent's Admin module; optional)
	local okBan, banned = Runtime.call("Admin", "isBanned", normalized)
	if okBan and banned == true then
		handle.reason = "Banned"
		local r = fallback(raw)
		report(player, r, handle, normalized, t0, false)
		return r
	end
	local okOv, override = Runtime.call("Admin", "override", normalized)
	if okOv and type(override) == "table" then
		local r = Schema().repair(override, raw)
		r.source = "Admin"
		r.input = raw
		report(player, r, handle, normalized, t0, false)
		return r
	end

	local threshold = cfg().Threshold or 0.6
	local core, mods = splitModifiers(normalized)

	-- 1. per-server memory (whole-phrase memo first, then the core phrase record)
	local memo, memoMeta = Cache.getLocal(normalized)
	if memo and memoMeta and memoMeta.source == "Memo" then
		memo.input = raw
		report(player, memo, handle, normalized, t0, false, true)
		return memo
	end
	local localHit, localMeta = Cache.getLocal(core)
	if localMeta and localMeta.refused then
		handle.reason = "Refused"
		local r = fallback(raw)
		report(player, r, handle, core, t0, false, true)
		return r
	end
	if localHit and localMeta and localMeta.source ~= "Memo" then
		if localHit.source ~= "Library" then
			localHit.source = "Cache"
		end
		AI.Cost.count("cacheHits", 1)
		local r = adapt(localHit, raw, core, mods, nil)
		report(player, r, handle, core, t0, true, true)
		return r
	end

	-- 2. library + phrase parser
	local res, spell = resolveLocal(raw, threshold)
	res.input = raw
	if isLibraryExact(res, spell) or (opts and opts.skipAI) then
		report(player, res, handle, normalized, t0, false)
		return res
	end
	local good = (tonumber(res.confidence) or 0) >= threshold
	local needAI = not good and cfg().Enabled ~= false

	-- 3. remote cache (+ AI when needed), coalesced per phrase
	local job = jobFor(core, needAI, player)
	local timeout = (opts and opts.timeout) or cfg().InstantTimeout or 1.5
	local finished, value, err = job:await(timeout)
	if finished then
		if value then
			local r = adapt(value, raw, core, mods, spell)
			report(player, r, handle, core, t0, true, value.source == "Cache")
			return r
		end
		if err == "refused" or err == "filtered" then
			handle.reason = REASONS[err :: string]
			local r = fallback(raw) -- DESIGN §9: only exact/alias library hits survive a hashed input
			report(player, r, handle, core, t0, needAI)
			return r
		end
		if good then
			Cache.memo(normalized, res) -- remote layers had nothing: don't ask them again for a while
			report(player, res, handle, normalized, t0, false)
			return res
		end
		local best = if isUsable(res) then res else fallback(raw)
		report(player, best, handle, core, t0, needAI)
		return best
	end

	-- Timed out: answer now, upgrade later.
	local best = if isUsable(res) then res else fallback(raw)
	handle.pending = true
	AI.Cost.count("timeouts", 1)
	local bestId, bestSource = best.id, best.source
	job:onDone(function(v: any)
		handle.pending = false
		if v == nil then
			if good then
				Cache.memo(normalized, res)
			end
			return
		end
		local r = finalize(adapt(v, raw, core, mods, spell))
		if bestSource == "Fallback" or r.id ~= bestId or r.source ~= bestSource then
			handle.result = r
			AI.Cost.count("upgrades", 1)
			if r.source == "AI" or r.source == "Cache" then
				Cache.recordPlay(core)
			end
			handle.upgraded:Fire(r)
		end
	end)
	report(player, best, handle, core, t0, needAI)
	return best
end

-- interpretAsync(player, text, opts?) -> (WordResult, Handle). opts = { skipAI: boolean?, timeout: number? }
function Interpreter.interpretAsync(player: any, text: any, opts: { skipAI: boolean?, timeout: number? }?): (any, Handle)
	local handle = newHandle()
	local ok, result = pcall(run, player, text, opts, handle)
	if not ok or type(result) ~= "table" then
		Runtime.log("warn", "interpretAsync failed: " .. tostring(result))
		handle.reason = "Error"
		handle.pending = false
		local okFb, fb = pcall(function()
			return fallback(if type(text) == "string" then text else "")
		end)
		result = if okFb then fb else { id = "glitter blob", canonical = "glitter blob", source = "Fallback", confidence = 0 }
	end
	if result.source ~= "Fallback" then
		result = finalize(result)
	end
	handle.result = result
	return result, handle
end

function Interpreter.stats(): { [string]: any }
	local s = AI.Cost.snapshot()
	s.ai = AI.status()
	s.cache = Cache.stats()
	local n = 0
	for _ in jobs do
		n += 1
	end
	s.jobs = n
	s.avgLatencyMs = if (s.interprets or 0) > 0 then (s.latencyMs or 0) / s.interprets else 0
	return s
end

function Interpreter.init()
	table.clear(jobs)
end

function Interpreter.forget(player: any)
	Safety.forget(player)
end

return Interpreter
