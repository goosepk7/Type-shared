--!strict
-- Word cache, forever (DESIGN §5, §10). Lookup order, fastest first:
--   1. per-server memory LRU          (no yield; also memoizes local library/parser results)
--   2. MemoryStore sorted map (hot)   (TTL Config.Cache.HotTTL, refreshed on hit at most daily)
--   3. DataStore (permanent)          (WordEngine_WordCache_v1, per game; tools/promote.py merges games)
-- A hit in a lower layer back-fills the layers above it.
--
-- Paid AI results are never lost: written to MemoryStore + DataStore immediately with retries; a
-- write that still fails goes to a retry queue drained by the flush loop and on BindToClose.
--
-- The hot map also holds the cross-server per-phrase AI lock ("lock:<key>") so only one server of
-- the game pays for a phrase; other servers wait for its result (Cache.lock / Cache.waitForResult).
--
-- Records (DataStore "w1:<key>", hot "<key>"):
--   { v = 1, r = WordResult without input, src = "AI"|"Admin"|"Cache", fs = firstSeen, pc = playCount, t = hot time }
--   { v = 1, alias = "<target key>" }   -- a typo / variant pointing at the canonical phrase (or library id)
--   { v = 1, ref = true }               -- the AI refused this phrase: never ask again

local Runtime = require(script.Parent.Runtime)
local Blocklist = require(script.Parent.Blocklist)

local Cache = {}

export type Meta = { playCount: number, firstSeen: number, source: string, refused: boolean, layer: string, alias: string? }

type LruEntry = { rec: any, tick: number, memo: boolean }

local lru: { [string]: LruEntry } = {}
local lruCount = 0
local tick = 0
local negative: { [string]: number } = {} -- key -> clock of a confirmed remote miss
local plays: { [string]: number } = {}
local retryQueue: { { key: string, rec: any, tries: number } } = {}
local loopGen = 0
local stats = { hits = 0, misses = 0, hitLocal = 0, hitHot = 0, hitStore = 0, writeFailures = 0, aliasHits = 0 }

local function cfg(): any
	local c = Runtime.config()
	return (c and c.Cache) or {}
end

function Cache.keyFor(normalized: string): string
	if #normalized > 0 and #normalized <= 40 and string.match(normalized, "^[a-z0-9 '%-]+$") then
		return normalized
	end
	return "#" .. Blocklist.hash(normalized)
end

local function storeKey(key: string): string
	return "w1:" .. key -- <= 46 chars (DataStore key limit is 50)
end

local function dataStore(): any
	return Runtime.service("DataStoreService"):GetDataStore(cfg().DataStoreName or "WordEngine_WordCache_v1")
end

local function hotMap(): any
	return Runtime.service("MemoryStoreService"):GetSortedMap(cfg().HotMapName or "WordEngine_WordCacheHot_v1")
end

local function lruPut(key: string, rec: any, memo: boolean?)
	tick += 1
	if lru[key] == nil then
		lruCount += 1
	end
	lru[key] = { rec = rec, tick = tick, memo = memo == true }
	local max = cfg().LocalSize or 3000
	if lruCount > max then
		local entries = {}
		for k, e in lru do
			table.insert(entries, { k = k, t = e.tick })
		end
		table.sort(entries, function(a, b)
			return a.t < b.t
		end)
		for i = 1, math.max(1, math.floor(max * 0.1)) do
			lru[entries[i].k] = nil
			lruCount -= 1
		end
	end
end

local function lruGet(key: string): LruEntry?
	local e = lru[key]
	if e then
		tick += 1
		e.tick = tick
	end
	return e
end

local function lruDel(key: string)
	if lru[key] then
		lru[key] = nil
		lruCount -= 1
	end
end

local function validRecord(rec: any): boolean
	return type(rec) == "table" and (rec.ref == true or type(rec.r) == "table" or type(rec.alias) == "string")
end

local function toResult(rec: any): (any, Meta)
	local meta: Meta = {
		playCount = tonumber(rec.pc) or 0,
		firstSeen = tonumber(rec.fs) or 0,
		source = if type(rec.src) == "string" then rec.src else "AI",
		refused = rec.ref == true,
		layer = "",
		alias = nil,
	}
	if rec.ref == true or type(rec.r) ~= "table" then
		return nil, meta
	end
	local Schema = Runtime.sharedModule("Schema")
	local ok, r = pcall(Schema.repair, rec.r)
	if not ok or type(r) ~= "table" or r.source == "Fallback" then
		return nil, meta
	end
	return r, meta
end

local function hotSet(key: string, rec: any): boolean
	return (pcall(function()
		rec.t = Runtime.now()
		hotMap():SetAsync(key, rec, cfg().HotTTL or 604800)
	end))
end

-- One key through hot -> store (no alias following). Returns (rec, layer).
local function remoteRecord(key: string): (any, string)
	local ok, v = pcall(function()
		return hotMap():GetAsync(key)
	end)
	if ok and validRecord(v) then
		if Runtime.now() - (tonumber(v.t) or 0) > (cfg().HotRefreshAfter or 86400) then
			Runtime.task().spawn(hotSet, key, table.clone(v))
		end
		return v, "hot"
	end
	local ok2, v2 = pcall(function()
		return dataStore():GetAsync(storeKey(key))
	end)
	if ok2 and validRecord(v2) then
		Runtime.task().spawn(hotSet, key, table.clone(v2))
		return v2, "store"
	end
	return nil, "miss"
end

local function countLayer(layer: string)
	stats.hits += 1
	if layer == "local" then
		stats.hitLocal += 1
	elseif layer == "hot" then
		stats.hitHot += 1
	elseif layer == "store" then
		stats.hitStore += 1
	end
end

-- Resolve an alias record to a result: the target phrase's record (local -> remote) or a library id.
local function followAlias(rec: any, allowRemote: boolean): (any, Meta?)
	local target = rec.alias
	local e = lruGet(target)
	local trec = e and e.rec or nil
	if trec == nil and allowRemote then
		trec = remoteRecord(target)
		if trec then
			lruPut(target, trec)
		end
	end
	if validRecord(trec) and trec.alias == nil then
		local r, meta = toResult(trec)
		if r or meta.refused then
			meta.alias = target
			return r, meta
		end
	end
	local Library = Runtime.sharedModule("Library")
	if Library and Library.get then
		local ok, lib = pcall(Library.get, target)
		if ok and type(lib) == "table" then
			local meta: Meta = { playCount = 0, firstSeen = 0, source = "Library", refused = false, layer = "", alias = target }
			return lib, meta
		end
	end
	return nil, nil
end

local function lookup(normalized: string, countHit: boolean, allowRemote: boolean): (any, Meta?)
	if cfg().Enabled == false or type(normalized) ~= "string" or normalized == "" then
		return nil, nil
	end
	local key = Cache.keyFor(normalized)
	local layer = "local"
	local e = lruGet(key)
	local rec = e and e.rec or nil
	if rec == nil and allowRemote then
		local neg = negative[key]
		if neg and Runtime.clock() - neg < (cfg().NegativeTTL or 120) then
			if countHit then
				stats.misses += 1
			end
			return nil, nil
		end
		rec, layer = remoteRecord(key)
		if rec then
			lruPut(key, rec)
		else
			negative[key] = Runtime.clock()
		end
	end
	if rec == nil then
		if countHit and allowRemote then
			stats.misses += 1
		end
		return nil, nil
	end
	local r, meta
	if type(rec.alias) == "string" then
		r, meta = followAlias(rec, allowRemote)
		if meta == nil then
			return nil, nil
		end
		stats.aliasHits += if countHit then 1 else 0
	else
		r, meta = toResult(rec)
	end
	meta.layer = layer
	if countHit then
		countLayer(layer)
	end
	return r, meta
end

-- Memory, then MemoryStore, then DataStore (yields). A refused entry returns (nil, meta.refused=true).
function Cache.get(normalized: string): (any, Meta?)
	return lookup(normalized, true, true)
end

-- Same as get without counting a hit (Admin tooling); bypasses the negative memo.
function Cache.peek(normalized: string): (any, Meta?)
	negative[Cache.keyFor(normalized)] = nil
	return lookup(normalized, false, true)
end

-- Memory only, never yields. Also returns local memos (meta.source == "Memo").
function Cache.getLocal(normalized: string): (any, Meta?)
	local key = Cache.keyFor(normalized)
	local e = lruGet(key)
	if not e then
		return nil, nil
	end
	if e.memo then
		local meta: Meta = { playCount = 0, firstSeen = 0, source = "Memo", refused = false, layer = "local", alias = nil }
		local Schema = Runtime.sharedModule("Schema")
		return Schema.clone(e.rec), meta
	end
	return lookup(normalized, true, false)
end

-- Remember a locally resolved (library/parser) result in this server only, so the remote layers
-- are consulted once per phrase per server. Never persisted.
function Cache.memo(normalized: string, result: any)
	local key = Cache.keyFor(normalized)
	local e = lru[key]
	if e and not e.memo then
		return -- never shadow a real cache record
	end
	local Schema = Runtime.sharedModule("Schema")
	local ok, c = pcall(Schema.clone, result)
	if ok then
		lruPut(key, c, true)
	end
end

local function persist(key: string, rec: any): boolean
	local retries = cfg().WriteRetries or 3
	for attempt = 1, retries do
		local ok = pcall(function()
			dataStore():UpdateAsync(storeKey(key), function(old: any)
				if validRecord(old) and type(old.r) == "table" and type(rec.r) == "table" then
					rec.fs = math.min(tonumber(old.fs) or rec.fs, rec.fs)
					rec.pc = math.max(tonumber(old.pc) or 0, rec.pc or 0)
				end
				return rec
			end)
		end)
		if ok then
			return true
		end
		if attempt < retries then
			Runtime.task().wait(0.5 * 2 ^ (attempt - 1))
		end
	end
	return false
end

local function writeThrough(key: string, rec: any)
	hotSet(key, table.clone(rec))
	if not persist(key, rec) then
		stats.writeFailures += 1
		table.insert(retryQueue, { key = key, rec = rec, tries = 0 })
		Runtime.warnOnce("cachewrite", "Word cache DataStore write failed; queued for retry")
	end
end

local function makeRecord(result: any, opts: any): any
	local rec: { [string]: any } = { v = 1, src = (opts and opts.source) or "AI", fs = Runtime.now(), pc = 0 }
	if opts and opts.refused then
		rec.ref = true
	else
		local Schema = Runtime.sharedModule("Schema")
		local r = Schema.clone(result)
		r.input = ""
		if r.correction then
			r.correction.from = ""
		end
		rec.r = r
	end
	return rec
end

-- Store a result (or a refusal) for a normalized phrase in every layer. Returns immediately; the
-- writes (with retries) run in the background. opts = { source = "AI" | "Admin", refused = boolean? }
function Cache.put(normalized: string, result: any, opts: { source: string?, refused: boolean? }?)
	if cfg().Enabled == false or type(normalized) ~= "string" or normalized == "" then
		return
	end
	local key = Cache.keyFor(normalized)
	local ok, rec = pcall(makeRecord, result, opts)
	if not ok then
		return
	end
	negative[key] = nil
	lruPut(key, rec)
	Runtime.task().spawn(writeThrough, key, rec)
end

-- Yielding variant (Admin / tests).
function Cache.putAsync(normalized: string, result: any, opts: { source: string?, refused: boolean? }?)
	local key = Cache.keyFor(normalized)
	local rec = makeRecord(result, opts)
	negative[key] = nil
	lruPut(key, rec)
	writeThrough(key, rec)
end

-- Record that `normalized` (e.g. a typo) means the phrase `target` (a cached phrase or library id).
function Cache.putAlias(normalized: string, target: string)
	if cfg().Enabled == false or normalized == "" or target == "" or normalized == target then
		return
	end
	local key = Cache.keyFor(normalized)
	local rec = { v = 1, alias = Cache.keyFor(target), fs = Runtime.now() }
	negative[key] = nil
	lruPut(key, rec)
	Runtime.task().spawn(writeThrough, key, rec)
end

function Cache.invalidate(normalized: string)
	local key = Cache.keyFor(normalized)
	lruDel(key)
	negative[key] = nil
	pcall(function()
		hotMap():RemoveAsync(key)
	end)
	pcall(function()
		dataStore():RemoveAsync(storeKey(key))
	end)
end

-- Cross-server AI lock -----------------------------------------------------------------------------

local function lockKey(normalized: string): string
	return "lock:" .. Cache.keyFor(normalized)
end

-- Try to become the one server that asks the AI about this phrase. Returns true when we hold the
-- lock (or MemoryStore is unavailable: then we proceed, worst case the phrase is paid twice).
function Cache.lock(normalized: string): boolean
	local me = Runtime.jobId()
	local ttl = (Runtime.config().AI or {}).LockTTL or 20
	local ok, result = pcall(function()
		return hotMap():UpdateAsync(lockKey(normalized), function(old: any)
			local now = Runtime.now()
			if type(old) == "table" and old.job ~= me and (tonumber(old.exp) or 0) > now then
				return nil -- someone else holds it
			end
			return { job = me, exp = now + ttl }
		end, ttl)
	end)
	if not ok then
		return true
	end
	return type(result) == "table" and result.job == me
end

function Cache.unlock(normalized: string)
	local me = Runtime.jobId()
	pcall(function()
		hotMap():UpdateAsync(lockKey(normalized), function(old: any)
			if type(old) == "table" and old.job == me then
				return { job = me, exp = 0 }
			end
			return nil
		end, 5)
	end)
end

-- Wait for the lock holder's result. Returns (result?, meta?, status) where status is "result",
-- "refused", "released" (holder gave up: try to lock again) or "timeout".
function Cache.waitForResult(normalized: string, timeout: number): (any, Meta?, string)
	local key = Cache.keyFor(normalized)
	local poll = (Runtime.config().AI or {}).LockPoll or 0.5
	local deadline = Runtime.clock() + timeout
	while Runtime.clock() < deadline do
		Runtime.task().wait(poll)
		local ok, v = pcall(function()
			return hotMap():GetAsync(key)
		end)
		if ok and validRecord(v) then
			lruPut(key, v)
			negative[key] = nil
			local r, meta
			if type(v.alias) == "string" then
				r, meta = followAlias(v, true)
			else
				r, meta = toResult(v)
			end
			if meta and meta.refused then
				return nil, meta, "refused"
			end
			if r then
				return r, meta, "result"
			end
		end
		local okL, lockRec = pcall(function()
			return hotMap():GetAsync(lockKey(normalized))
		end)
		if okL and (type(lockRec) ~= "table" or (tonumber(lockRec.exp) or 0) <= Runtime.now()) then
			return nil, nil, "released"
		end
	end
	return nil, nil, "timeout"
end

-- Play counts / promotion ----------------------------------------------------------------------------

-- Count a play of an AI/Cache-sourced phrase (promotion review). Cheap; flushed in batches.
function Cache.recordPlay(normalized: string)
	local key = Cache.keyFor(normalized)
	plays[key] = (plays[key] or 0) + 1
end

function Cache.flushPlays()
	local max = cfg().MaxFlushKeys or 20
	local batch = {}
	for k, n in plays do
		table.insert(batch, { k = k, n = n })
		if #batch >= max then
			break
		end
	end
	for _, e in batch do
		plays[e.k] = nil
	end
	local ordered: any = nil
	pcall(function()
		ordered = Runtime.service("DataStoreService"):GetOrderedDataStore(cfg().PlaysOrderedStore or "WordEngine_AIWordPlays_v1")
	end)
	for _, e in batch do
		pcall(function()
			dataStore():UpdateAsync(storeKey(e.k), function(old: any)
				if not validRecord(old) or type(old.r) ~= "table" then
					return nil -- nothing cached (cancel the write)
				end
				old.pc = (tonumber(old.pc) or 0) + e.n
				return old
			end)
		end)
		if ordered and string.sub(e.k, 1, 1) ~= "#" then
			pcall(function()
				ordered:IncrementAsync(e.k, e.n)
			end)
		end
	end
end

-- Retry paid results whose DataStore write failed.
function Cache.flushPending()
	local n = #retryQueue
	for _ = 1, math.min(n, cfg().MaxFlushKeys or 20) do
		local item = table.remove(retryQueue, 1)
		if item then
			if not persist(item.key, item.rec) then
				item.tries += 1
				table.insert(retryQueue, item) -- keep it: a paid result is never dropped
			end
		end
	end
end

-- Most played AI phrases: { { key: string, plays: number } } (yields).
function Cache.topPlayed(n: number?): { { key: string, plays: number } }
	local out = {}
	pcall(function()
		local store = Runtime.service("DataStoreService"):GetOrderedDataStore(cfg().PlaysOrderedStore or "WordEngine_AIWordPlays_v1")
		local pages = store:GetSortedAsync(false, math.clamp(n or 50, 1, 100))
		for _, item in pages:GetCurrentPage() do
			table.insert(out, { key = item.key, plays = item.value })
		end
	end)
	return out
end

function Cache.stats(): { [string]: number }
	local s = table.clone(stats)
	s.localEntries = lruCount
	s.pendingWrites = #retryQueue
	local lookups = stats.hits + stats.misses
	s.hitRate = if lookups > 0 then stats.hits / lookups else 0
	return s
end

function Cache.init()
	loopGen += 1
	table.clear(lru)
	lruCount = 0
	table.clear(negative)
	table.clear(plays)
	table.clear(retryQueue)
	for k in stats do
		stats[k] = 0
	end
end

-- Background flush loop (server only; tests call the flush functions directly).
function Cache.startLoop()
	local gen = loopGen
	Runtime.task().spawn(function()
		while gen == loopGen do
			Runtime.task().wait(cfg().FlushInterval or 30)
			if gen ~= loopGen then
				break
			end
			pcall(Cache.flushPending)
			pcall(Cache.flushPlays)
		end
	end)
end

function Cache.flushAll()
	for _ = 1, 3 do
		if #retryQueue == 0 then
			break
		end
		pcall(Cache.flushPending)
	end
	pcall(Cache.flushPlays)
end

return Cache
