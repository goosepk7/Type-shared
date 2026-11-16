--!strict
-- SessionStore: session-locked records in one DataStore, ProfileStore-style.
--
-- Record layout (what is stored under each key):
--   { format = 1,
--     meta = { created, updated, saves, lock = { job, session, place, t }? },
--     ns   = { [namespace] = { v = schemaVersion, d = data } } }
--
-- Guarantees
--  * One writer per key: every write is an UpdateAsync whose transform first checks that the stored lock
--    belongs to this session. If another server stole the lock, the write is cancelled and the session
--    ends ("stolen") instead of clobbering newer data.
--  * Load takes the lock if it is free, ours, or stale (Config LockStaleSeconds). If it is fresh and held by
--    another session we ask the holder to release (MessagingService) and steal after LockWaitSeconds.
--  * Each namespace has its own version + ordered migrations. Data written by a NEWER server version is
--    never migrated down or overwritten: that namespace is frozen (read-only) for the session.
--  * Namespaces this server does not know are carried through untouched.
--  * All calls go through Queue (budget, per-key serialisation, exponential backoff).

local Env = require(script.Parent.Env)
local Queue = require(script.Parent.Queue)
local Signal = require(script.Parent.Signal)

local FORMAT = 1

export type Namespace = {
	template: { [string]: any },
	version: number,
	migrations: { [number]: (data: any) -> any? }, -- migrations[n] upgrades n-1 -> n (may mutate or return new)
}

export type Lock = { job: string, session: string, place: number, t: number }

export type Session = {
	key: string,
	id: string,
	userIds: { number },
	data: { [string]: any }, -- namespace -> live data table
	meta: { created: number, updated: number, saves: number },
	frozen: { [string]: string }, -- namespace -> reason (newer version / migration error)
	active: boolean,
	dirty: boolean,
	lastSave: number,
	stolen: boolean,
	saving: boolean,
	released: Signal.Signal<string>, -- reason: "released" | "stolen" | "failed"
}

local SessionStore = {}
SessionStore.__index = SessionStore

export type SessionStore = typeof(setmetatable(
	{} :: {
		name: string,
		store: any,
		queue: Queue.Queue,
		namespaces: { [string]: Namespace },
		sessions: { [string]: Session },
		requestRelease: ((key: string, lock: Lock) -> ())?,
		_cfg: () -> any,
	},
	SessionStore
))

local function deepCopy(v: any): any
	if type(v) ~= "table" then
		return v
	end
	local out = {}
	for k, x in v do
		out[k] = deepCopy(x)
	end
	return out
end
SessionStore.deepCopy = deepCopy

-- Fill keys missing from `data` with template defaults (never overwrites existing values).
local function reconcile(data: any, template: any)
	for k, def in template do
		local cur = data[k]
		if cur == nil then
			data[k] = deepCopy(def)
		elseif type(cur) == "table" and type(def) == "table" and next(def) ~= nil and #def == 0 then
			-- only recurse into dictionary templates (arrays/maps of player content are left as is)
			reconcile(cur, def)
		end
	end
end
SessionStore.reconcile = reconcile

function SessionStore.new(name: string, store: any, opts: {
	namespaces: { [string]: Namespace }?,
	queue: Queue.Queue?,
	requestRelease: ((key: string, lock: Lock) -> ())?,
	config: (() -> any)?,
}?): SessionStore
	local o = opts or {}
	local cfg = o.config or function()
		return Env.config().Services.Data
	end
	return setmetatable({
		name = name,
		store = store,
		queue = o.queue or Queue.new(cfg),
		namespaces = o.namespaces or {},
		sessions = {},
		requestRelease = o.requestRelease,
		_cfg = cfg,
	}, SessionStore) :: any
end

function SessionStore.register(self: SessionStore, name: string, ns: Namespace)
	assert(type(name) == "string" and #name > 0 and #name <= 32, "namespace name 1..32 chars")
	assert(type(ns.template) == "table", "namespace template must be a table")
	local migrations = ns.migrations or {}
	for v = 2, ns.version do
		assert(migrations[v] == nil or type(migrations[v]) == "function", "migration " .. v .. " must be a function")
	end
	self.namespaces[name] = { template = ns.template, version = ns.version or 1, migrations = migrations }
end

local function newRecord(now: number): any
	return { format = FORMAT, meta = { created = now, updated = now, saves = 0 }, ns = {} }
end

-- Upgrade one namespace entry; returns (data, frozenReason?)
local function upgrade(name: string, ns: Namespace, entry: any): (any, string?)
	if type(entry) ~= "table" or type(entry.d) ~= "table" then
		return deepCopy(ns.template), nil
	end
	local v = tonumber(entry.v) or 1
	local data = entry.d
	if v > ns.version then
		reconcile(data, ns.template)
		return data, ("namespace %s is v%d, this server knows v%d"):format(name, v, ns.version)
	end
	for target = v + 1, ns.version do
		local m = ns.migrations[target]
		if m then
			local ok, res = pcall(m, data)
			if not ok then
				return data, ("migration %s v%d failed: %s"):format(name, target, tostring(res))
			end
			if type(res) == "table" then
				data = res
			end
		end
	end
	reconcile(data, ns.template)
	return data, nil
end
SessionStore.upgrade = upgrade

-- Loads and locks `key`. Yields. Returns (session?, error?).
function SessionStore.load(self: SessionStore, key: string, userIds: { number }?): (Session?, string?)
	local cfg = self._cfg()
	if self.sessions[key] then
		return nil, "already loaded on this server"
	end
	local sessionId = Env.guid()
	local job = Env.jobId()
	local startedAt = Env.now()
	local asked = false
	local loops = 0

	while true do
		loops += 1
		local now = Env.now()
		local force = (now - startedAt) >= cfg.LockWaitSeconds
		local blocked: Lock? = nil
		local loaded: any = nil

		local ok, err = self.queue:run({ key = key, priority = "Normal" }, function()
			blocked, loaded = nil, nil
			self.store:UpdateAsync(key, function(old: any)
				local rec = old
				if type(rec) ~= "table" or type(rec.meta) ~= "table" or type(rec.ns) ~= "table" then
					rec = newRecord(now)
				end
				local lock = rec.meta.lock
				if type(lock) == "table" and lock.session ~= sessionId then
					local age = now - (tonumber(lock.t) or 0)
					if age < cfg.LockStaleSeconds and not force then
						blocked = lock
						return nil -- cancel: someone else holds a fresh lock
					end
				end
				rec.meta.lock = { job = job, session = sessionId, place = Env.placeId(), t = now }
				loaded = rec
				return rec, userIds
			end)
		end)

		if not ok then
			return nil, err
		end
		if loaded then
			local rec = loaded
			local session: Session = {
				key = key,
				id = sessionId,
				userIds = userIds or {},
				data = {},
				meta = { created = rec.meta.created or now, updated = rec.meta.updated or now, saves = rec.meta.saves or 0 },
				frozen = {},
				active = true,
				dirty = false,
				lastSave = Env.clock(),
				stolen = false,
				saving = false,
				released = Signal.new(),
			}
			for name, ns in self.namespaces do
				local data, frozen = upgrade(name, ns, rec.ns[name])
				session.data[name] = data
				if frozen then
					session.frozen[name] = frozen
					Env.log("warn", ("%s/%s: %s (namespace is read-only this session)"):format(self.name, key, frozen))
				end
			end
			self.sessions[key] = session
			return session, nil
		end
		if blocked then
			if not asked and self.requestRelease then
				asked = true
				pcall(self.requestRelease :: any, key, blocked)
			end
			if loops > 60 then
				return nil, "lock wait exceeded"
			end
			Env.wait(1.5)
		else
			return nil, "update returned nothing"
		end
	end
end

function SessionStore.get(self: SessionStore, key: string): Session?
	return self.sessions[key]
end

local function endSession(self: SessionStore, s: Session, reason: string)
	if not s.active then
		return
	end
	s.active = false
	if self.sessions[s.key] == s then
		self.sessions[s.key] = nil
	end
	s.released:Fire(reason)
end

-- Writes the session. release=true drops the lock and ends the session.
-- Returns (ok, error?). A stolen session ends immediately and is never written.
function SessionStore.save(self: SessionStore, s: Session, release: boolean?): (boolean, string?)
	if not s.active then
		return false, "session not active"
	end
	-- serialise saves of one session (autosave + release can overlap)
	local spins = 0
	while s.saving do
		Env.wait(0.1)
		spins += 1
		if spins > 900 then
			return false, "save already in progress"
		end
	end
	if not s.active then
		return false, "session not active"
	end
	s.saving = true
	local now = Env.now()
	local stolen = false
	local snapshot: { [string]: any } = {}
	for name, data in s.data do
		if not s.frozen[name] then
			snapshot[name] = deepCopy(data)
		end
	end
	local wasDirty = s.dirty
	s.dirty = false

	local ok, err = self.queue:run({ key = s.key, priority = if release then "Critical" else "Normal" }, function()
		stolen = false
		self.store:UpdateAsync(s.key, function(old: any)
			if type(old) ~= "table" or type(old.meta) ~= "table" or type(old.meta.lock) ~= "table"
				or old.meta.lock.session ~= s.id then
				stolen = true
				return nil
			end
			old.ns = if type(old.ns) == "table" then old.ns else {}
			for name, data in snapshot do
				old.ns[name] = { v = self.namespaces[name] and self.namespaces[name].version or 1, d = data }
			end
			old.format = FORMAT
			old.meta.updated = now
			old.meta.saves = (tonumber(old.meta.saves) or 0) + 1
			if release then
				old.meta.lock = nil
			else
				old.meta.lock.t = now
			end
			return old, s.userIds
		end)
	end)
	s.saving = false

	if not ok then
		s.dirty = s.dirty or wasDirty
		return false, err
	end
	if stolen then
		s.stolen = true
		Env.log("warn", ("%s/%s: session lock was taken by another server; this session ends without writing"):format(self.name, s.key))
		endSession(self, s, "stolen")
		return false, "stolen"
	end
	s.lastSave = Env.clock()
	s.meta.updated = now
	s.meta.saves += 1
	if release then
		endSession(self, s, "released")
	end
	return true, nil
end

-- Release with persistence: retries until it succeeds, the lock is stolen, or `deadline` (clock) passes.
function SessionStore.release(self: SessionStore, s: Session, deadline: number?): boolean
	local stop = deadline or (Env.clock() + 120)
	while s.active do
		local ok, err = self:save(s, true)
		if ok then
			return true
		end
		if err == "stolen" or not s.active then
			return false
		end
		if Env.clock() >= stop then
			Env.log("error", ("%s/%s: release failed until deadline: %s"):format(self.name, s.key, tostring(err)))
			endSession(self, s, "failed")
			return false
		end
		Env.wait(2)
	end
	return false
end

-- Read a record without locking (admin tools, offline inspection).
function SessionStore.peek(self: SessionStore, key: string): (any, string?)
	local value: any = nil
	local ok, err = self.queue:run({ key = key, requestType = "GetAsync", priority = "Low" }, function()
		value = self.store:GetAsync(key)
	end)
	if not ok then
		return nil, err
	end
	return value, nil
end

-- Edit an OFFLINE player's namespace (admin grants, receipt fixes). Refuses if a fresh lock is held
-- elsewhere (that server would overwrite us); use only when the player is not in-game.
function SessionStore.editOffline(self: SessionStore, key: string, nsName: string, fn: (any) -> ()): (boolean, string?)
	local cfg = self._cfg()
	local ns = self.namespaces[nsName]
	if not ns then
		return false, "unknown namespace"
	end
	local now = Env.now()
	local refused: string? = nil
	local ok, err = self.queue:run({ key = key, priority = "Normal" }, function()
		refused = nil
		self.store:UpdateAsync(key, function(old: any)
			local rec = if type(old) == "table" and type(old.meta) == "table" then old else newRecord(now)
			rec.ns = rec.ns or {}
			local lock = rec.meta.lock
			if type(lock) == "table" and now - (tonumber(lock.t) or 0) < cfg.LockStaleSeconds then
				refused = "player session is active on server " .. tostring(lock.job)
				return nil
			end
			local data, frozen = upgrade(nsName, ns, rec.ns[nsName])
			if frozen then
				refused = frozen
				return nil
			end
			local okFn, e = pcall(fn, data)
			if not okFn then
				refused = tostring(e)
				return nil
			end
			rec.ns[nsName] = { v = ns.version, d = data }
			rec.meta.updated = now
			return rec
		end)
	end)
	if not ok then
		return false, err
	end
	if refused then
		return false, refused
	end
	return true, nil
end

return SessionStore
