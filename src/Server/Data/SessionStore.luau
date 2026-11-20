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
--  * A stored record this build cannot read (not a table, missing meta/ns, newer `format`) is NEVER replaced:
--    the load fails (the player is kicked with a retry message) and the record stays as it was.
--  * A namespace entry that exists but is unreadable is frozen (read-only), never reset to the template.
--  * Lock hand-off: while the holder answers our release requests (`holderAlive`), we keep waiting up to
--    LockBusySeconds instead of stealing at LockWaitSeconds, so a server that is still writing its final
--    save (throttled at match end, say) is not robbed of it. A holder that never answers is dead: steal.
--  * Wipe tripwire: a namespace may define guard(stored, new) -> (ok, reason). A save that fails it is not
--    written for that namespace (the stored copy stays) and the namespace is frozen for the session.
--  * Backups: every write is a DataStore version (kept 30 days by Roblox). listVersions / restoreVersion
--    roll an OFFLINE player back, keeping the receipt ids granted since (no double grants after a restore).

local Env = require(script.Parent.Env)
local Queue = require(script.Parent.Queue)
local Signal = require(script.Parent.Signal)

local FORMAT = 1

export type Namespace = {
	template: { [string]: any },
	version: number,
	migrations: { [number]: (data: any) -> any? }, -- migrations[n] upgrades n-1 -> n (may mutate or return new)
	guard: ((stored: any, new: any) -> (boolean, string?))?, -- wipe tripwire (see header)
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
		holderAlive: ((lock: Lock, since: number) -> boolean)?,
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
	holderAlive: ((lock: Lock, since: number) -> boolean)?, -- did the holder answer a release request since `since` (clock)?
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
		holderAlive = o.holderAlive,
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
	self.namespaces[name] = { template = ns.template, version = ns.version or 1, migrations = migrations, guard = ns.guard }
end

local function newRecord(now: number): any
	return { format = FORMAT, meta = { created = now, updated = now, saves = 0 }, ns = {} }
end

-- nil = no record yet; true = a record this build understands; false + reason = keep away from it.
local function readable(rec: any): (boolean?, string?)
	if rec == nil then
		return nil, nil
	end
	if type(rec) ~= "table" or type(rec.meta) ~= "table" or type(rec.ns) ~= "table" then
		return false, "stored record is unreadable (" .. type(rec) .. ")"
	end
	local f = tonumber(rec.format) or 1
	if f > FORMAT then
		return false, ("stored record format %d is newer than this server's %d"):format(f, FORMAT)
	end
	return true, nil
end
SessionStore.readable = readable

-- Upgrade one namespace entry; returns (data, frozenReason?)
local function upgrade(name: string, ns: Namespace, entry: any): (any, string?)
	if entry == nil then
		return deepCopy(ns.template), nil
	end
	if type(entry) ~= "table" or type(entry.d) ~= "table" then
		-- present but unreadable: never reset it to the template (that would be saved over it)
		return deepCopy(ns.template), ("namespace %s is unreadable (%s); left untouched"):format(name, type(entry))
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
	local askedAt: number? = nil -- clock of the first release request
	local lastAsk = -math.huge
	local loops = 0
	local busy = cfg.LockBusySeconds or (cfg.LockWaitSeconds * 5)
	local refused: string? = nil

	while true do
		loops += 1
		local now = Env.now()
		local waited = now - startedAt
		local force = waited >= cfg.LockWaitSeconds
		local blocked: Lock? = nil
		local loaded: any = nil

		local ok, err = self.queue:run({ key = key, priority = "Normal" }, function()
			blocked, loaded, refused = nil, nil, nil
			self.store:UpdateAsync(key, function(old: any)
				local good, why = readable(old)
				if good == false then
					refused = why
					return nil -- never overwrite a record we cannot read
				end
				local rec = if good then old else newRecord(now)
				local lock = rec.meta.lock
				if type(lock) == "table" and lock.session ~= sessionId then
					local age = now - (tonumber(lock.t) or 0)
					if age < cfg.LockStaleSeconds then
						-- the holder is alive and answering (still writing its final save): give it longer
						local alive = force and askedAt ~= nil and self.holderAlive ~= nil
							and (self.holderAlive :: any)(lock, askedAt :: number) == true
						if not force or (alive and waited < busy) then
							blocked = lock
							return nil -- cancel: someone else holds a fresh lock
						end
					end
				end
				rec.meta.lock = { job = job, session = sessionId, place = Env.placeId(), t = now }
				loaded = rec
				return rec, userIds
			end)
		end)

		if refused then
			Env.log("error", ("%s/%s: %s; load refused, record left untouched"):format(self.name, key, refused :: string))
			return nil, refused
		end
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
			-- ask the holder to release (again every ~5 s: a MessagingService message can be lost)
			if self.requestRelease and Env.clock() - lastAsk >= 5 then
				lastAsk = Env.clock()
				askedAt = askedAt or lastAsk
				pcall(self.requestRelease :: any, key, blocked)
			end
			if loops > 120 then
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
	local tripped: { [string]: string } = {}

	local ok, err = self.queue:run({ key = s.key, priority = if release then "Critical" else "Normal" }, function()
		stolen = false
		self.store:UpdateAsync(s.key, function(old: any)
			if type(old) ~= "table" or type(old.meta) ~= "table" or type(old.meta.lock) ~= "table"
				or old.meta.lock.session ~= s.id then
				stolen = true
				return nil
			end
			old.ns = if type(old.ns) == "table" then old.ns else {}
			tripped = {}
			for name, data in snapshot do
				local ns = self.namespaces[name]
				local stored = old.ns[name]
				if ns and ns.guard and type(stored) == "table" and type(stored.d) == "table" then
					local okG, pass, why = pcall(ns.guard :: any, stored.d, data)
					if okG and pass == false then
						tripped[name] = tostring(why or "guard")
						continue -- keep the stored copy
					end
				end
				old.ns[name] = { v = ns and ns.version or 1, d = data }
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
	for name, why in tripped do
		-- wipe tripwire: this session's copy looks like a wipe of the stored one. Stop writing it.
		s.frozen[name] = "save guard: " .. why
		Env.log("error", ("%s/%s: save guard tripped for %s (%s); stored copy kept, namespace read-only this session"):format(self.name, s.key, name, why))
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
			local good, why = readable(old)
			if good == false then
				refused = why
				return nil
			end
			local rec = if good then old else newRecord(now)
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

-- Backups: DataStore keeps every write as a version for 30 days. Newest first:
-- { { version: string, created: number (unix ms), deleted: boolean } }
function SessionStore.listVersions(self: SessionStore, key: string, maxCount: number?): ({ any }?, string?)
	local out = {}
	local limit = maxCount or 20
	local ok, err = self.queue:run({ key = key, requestType = "GetVersionAsync", priority = "Low", maxBudgetWait = 30 }, function()
		table.clear(out)
		local E = (Enum :: any)
		local dir = if E then E.SortDirection.Descending else "Descending"
		local pages = self.store:ListVersionsAsync(key, dir, nil, nil, math.min(limit, 100))
		while true do
			for _, info in pages:GetCurrentPage() do
				table.insert(out, { version = info.Version, created = info.CreatedTime, deleted = info.IsDeleted == true })
				if #out >= limit then
					return
				end
			end
			if pages.IsFinished then
				return
			end
			pages:AdvanceToNextPageAsync()
		end
	end)
	if not ok then
		return nil, err
	end
	return out, nil
end

-- One stored version of a record (read only).
function SessionStore.getVersion(self: SessionStore, key: string, version: string): (any, string?)
	local value: any = nil
	local ok, err = self.queue:run({ key = key, requestType = "GetVersionAsync", priority = "Low", maxBudgetWait = 30 }, function()
		value = self.store:GetVersionAsync(key, version)
	end)
	if not ok then
		return nil, err
	end
	return value, nil
end

-- Roll an OFFLINE player back to `version`. Refuses while a fresh lock is held elsewhere (that server
-- would overwrite the restore). merge(current, restored) may carry fields over from the current record
-- (receipt ids, ...) and runs inside the write. Returns (ok, error?).
function SessionStore.restoreVersion(self: SessionStore, key: string, version: string, merge: ((current: any, restored: any) -> ())?): (boolean, string?)
	local cfg = self._cfg()
	local restored, err = self:getVersion(key, version)
	if err then
		return false, err
	end
	local good, why = readable(restored)
	if good ~= true then
		return false, why or "that version is empty"
	end
	local now = Env.now()
	local refused: string? = nil
	local ok, err2 = self.queue:run({ key = key, priority = "Normal" }, function()
		refused = nil
		self.store:UpdateAsync(key, function(old: any)
			local cur = old
			if readable(cur) == false then
				cur = nil -- an unreadable current record is exactly what a restore is for
			end
			local lock = cur and cur.meta.lock
			if type(lock) == "table" and now - (tonumber(lock.t) or 0) < cfg.LockStaleSeconds then
				refused = "player session is active on server " .. tostring(lock.job)
				return nil
			end
			local rec = deepCopy(restored)
			rec.meta.lock = nil
			rec.meta.updated = now
			rec.meta.saves = (tonumber(cur and cur.meta.saves) or tonumber(rec.meta.saves) or 0) + 1
			rec.meta.restored = { from = version, t = now }
			if merge and cur then
				local okM, e = pcall(merge, cur, rec)
				if not okM then
					refused = "merge failed: " .. tostring(e)
					return nil
				end
			end
			return rec
		end)
	end)
	if not ok then
		return false, err2
	end
	if refused then
		return false, refused
	end
	return true, nil
end

return SessionStore
