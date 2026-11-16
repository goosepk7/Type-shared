--!strict
-- Data: session-locked player data for both games (ProfileStore-like API). See DESIGN.md §10.
--
--   local Data = WordEngineServer.Data
--   Data.register("Wizard", { version = 2, template = { level = 1, xp = 0, loadout = {} },
--       migrations = { [2] = function(d) d.loadout = d.spells or {}; d.spells = nil end } })
--   Data.onLoaded(function(player) ... end)
--   local d = Data.get(player, "Wizard")            -- live table (read)
--   Data.update(player, function(d) d.xp += 10 end, "Wizard")   -- write (marks dirty, fires Data.changed)
--
-- Namespaces: the engine keeps its own data under "WordEngine" (word book, wallet, receipts, settings).
-- Each game registers its own namespace(s) BEFORE players load (before WordEngineServer.start()).
-- Never lose data: if a load fails after retries the player is kicked with a friendly message instead of
-- playing on a blank profile that could later be saved over their real one.

local Env = require(script.Env)
local Signal = require(script.Signal)
local SessionStore = require(script.SessionStore)
local LocalStore = require(script.LocalStore)
local Queue = require(script.Queue)

type Session = SessionStore.Session

local Data = {}
Data.CORE = "WordEngine"
Data.SessionStore = SessionStore
Data.LocalStore = LocalStore
Data.Queue = Queue
Data.Env = Env
Data.Signal = Signal

Data.loaded = Signal.new() :: Signal.Signal<any, Session>
Data.releasing = Signal.new() :: Signal.Signal<any, Session>
Data.changed = Signal.new() :: Signal.Signal<any, string>

local CORE_TEMPLATE = {
	wordbook = { entries = {}, total = 0, syncedAt = 0 },
	wallet = { balances = {}, ledger = {} },
	receipts = { ids = {}, order = {} },
	settings = {},
	stats = { joins = 0, firstJoin = 0, lastJoin = 0, playSeconds = 0 },
	flags = {},
}

local namespaces: { [string]: SessionStore.Namespace } = {
	[Data.CORE] = { template = CORE_TEMPLATE, version = 1, migrations = {} },
}

local store: SessionStore.SessionStore? = nil
local sessions: { [any]: Session } = {} -- player -> session
local joinedAt: { [any]: number } = {}
local started = false
local offline = false
local closing = false

local function cfg()
	return Env.config().Services.Data
end

local function keyFor(userId: number): string
	return cfg().KeyPrefix .. tostring(userId)
end
Data.keyFor = keyFor

-- Register a namespace (template + version + ordered migrations). Call before players load.
function Data.register(name: string, def: { template: { [string]: any }, version: number?, migrations: { [number]: (any) -> any? }? })
	assert(name ~= Data.CORE or def.template == CORE_TEMPLATE, "the WordEngine namespace is reserved")
	local ns: SessionStore.Namespace = { template = def.template, version = def.version or 1, migrations = def.migrations or {} }
	namespaces[name] = ns
	if store then
		store:register(name, ns)
	end
end

local function buildStore(dataStore: any): SessionStore.SessionStore
	local s = SessionStore.new(cfg().StoreName, dataStore, {
		namespaces = table.clone(namespaces),
		requestRelease = function(key: string, lock: SessionStore.Lock)
			if offline or not Env.hasService("MessagingService") then
				return
			end
			Env.spawn(function()
				pcall(function()
					Env.service("MessagingService"):PublishAsync(cfg().ReleaseTopic, { key = key, session = lock.session })
				end)
			end)
		end,
	})
	return s
end

-- Tests / tooling: use a specific DataStore-like object (e.g. LocalStore.new()).
function Data.useStore(dataStore: any)
	store = buildStore(dataStore)
	sessions = {}
end

function Data.store(): SessionStore.SessionStore?
	return store
end

function Data.isOffline(): boolean
	return offline
end

local function findPlayer(key: string): any?
	for p, s in sessions do
		if s.key == key then
			return p
		end
	end
	return nil
end

-- Load + lock a player's record. Normally driven by PlayerAdded; public for tests and the test place.
function Data.loadPlayer(player: any): Session?
	assert(store, "Data.start() (or Data.useStore) first")
	local st = store :: SessionStore.SessionStore
	if sessions[player] then
		return sessions[player]
	end
	local key = keyFor(player.UserId)
	-- Rejoined this same server before the previous session finished releasing: wait for it.
	local waited = 0
	while st:get(key) ~= nil and waited < 30 do
		Env.wait(0.25)
		waited += 0.25
	end
	local session, err = st:load(key, { player.UserId })
	if not session then
		Env.log("error", ("Data: load failed for %s: %s"):format(key, tostring(err)))
		if player.Parent ~= nil and player.Kick then
			player:Kick("We couldn't load your save safely, so we stopped before anything could be lost. Please rejoin in a minute.")
		end
		return nil
	end
	if player.Parent == nil then
		-- left while loading
		st:release(session)
		return nil
	end
	sessions[player] = session
	joinedAt[player] = Env.clock()
	session.released:Connect(function(reason: string)
		if sessions[player] == session then
			sessions[player] = nil
		end
		if reason == "stolen" and player.Parent ~= nil and player.Kick then
			player:Kick("Your save was opened on another server. Please rejoin.")
		end
	end)
	local core = session.data[Data.CORE]
	if core then
		local now = Env.now()
		core.stats.joins += 1
		if core.stats.firstJoin == 0 then
			core.stats.firstJoin = now
		end
		core.stats.lastJoin = now
		session.dirty = true
	end
	Data.loaded:Fire(player, session)
	return session
end

-- Final save + unlock. Normally driven by PlayerRemoving.
function Data.releasePlayer(player: any, deadline: number?): boolean
	local s = sessions[player]
	if not s or not store then
		return false
	end
	Data.releasing:Fire(player, s)
	local core = s.data[Data.CORE]
	if core and joinedAt[player] then
		core.stats.playSeconds += math.floor(Env.clock() - joinedAt[player])
	end
	joinedAt[player] = nil
	sessions[player] = nil
	return (store :: SessionStore.SessionStore):release(s, deadline)
end

function Data.session(player: any): Session?
	local s = sessions[player]
	if s and s.active then
		return s
	end
	return nil
end

function Data.isLoaded(player: any): boolean
	return Data.session(player) ~= nil
end

-- Live data table for a namespace (default: the engine's own "WordEngine" namespace). nil until loaded.
function Data.get(player: any, ns: string?): any?
	local s = Data.session(player)
	return s and s.data[ns or Data.CORE]
end

-- Mutate data. fn may mutate in place or return a replacement table. Returns false if not loaded or the
-- namespace is read-only this session (written by a newer server version).
function Data.update(player: any, fn: (any) -> any?, ns: string?): boolean
	local name = ns or Data.CORE
	local s = Data.session(player)
	if not s or s.data[name] == nil then
		return false
	end
	if s.frozen[name] then
		Env.log("warn", ("Data.update refused: %s"):format(s.frozen[name]))
		return false
	end
	local ok, res = pcall(fn, s.data[name])
	if not ok then
		Env.log("error", "Data.update callback error: " .. tostring(res))
		return false
	end
	if type(res) == "table" then
		s.data[name] = res
	end
	s.dirty = true
	Data.changed:Fire(player, name)
	return true
end

function Data.isReadOnly(player: any, ns: string?): boolean
	local s = Data.session(player)
	return s ~= nil and s.frozen[ns or Data.CORE] ~= nil
end

-- Force a save now (e.g. right after a purchase). Yields. Returns success.
function Data.saveAsync(player: any): boolean
	local s = Data.session(player)
	if not s or not store then
		return false
	end
	local ok = (store :: SessionStore.SessionStore):save(s, false)
	return ok
end

-- Yields until the player's data is loaded (or they leave / timeout). Returns loaded?
function Data.waitFor(player: any, timeout: number?): boolean
	local t = 0
	local limit = timeout or 60
	while not Data.isLoaded(player) do
		if player.Parent == nil or t >= limit then
			return false
		end
		Env.wait(0.2)
		t += 0.2
	end
	return true
end

-- Fires for every player whose data loads, including ones already loaded when you connect.
function Data.onLoaded(fn: (player: any, session: Session) -> ()): Signal.Connection
	for p, s in sessions do
		if s.active then
			Env.spawn(fn, p, s)
		end
	end
	return Data.loaded:Connect(fn)
end

-- Fires just before a player's final save; write last-minute data synchronously here (don't yield long).
function Data.onReleasing(fn: (player: any, session: Session) -> ()): Signal.Connection
	return Data.releasing:Connect(fn)
end

-- Offline access (Admin): read a record, or edit a namespace of a player who is NOT in any server.
function Data.peekOffline(userId: number): any?
	if not store then
		return nil
	end
	return (store :: SessionStore.SessionStore):peek(keyFor(userId))
end

function Data.editOffline(userId: number, ns: string, fn: (any) -> ()): (boolean, string?)
	if not store then
		return false, "not started"
	end
	return (store :: SessionStore.SessionStore):editOffline(keyFor(userId), ns, fn)
end

local function autosaveLoop()
	while started and not closing do
		Env.wait(1)
		local st = store
		if st then
			local period = cfg().AutosaveSeconds
			local now = Env.clock()
			-- save the single most overdue session per tick: spreads writes evenly across the period
			local pick: Session? = nil
			for _, s in sessions do
				if s.active and not s.saving and now - s.lastSave >= period then
					if pick == nil or s.lastSave < (pick :: Session).lastSave then
						pick = s
					end
				end
			end
			if pick then
				Env.spawn(function()
					st:save(pick :: Session, false)
				end)
			end
		end
	end
end

local function probeStore(dataStore: any): boolean
	local ok, err = pcall(function()
		dataStore:GetAsync("__probe")
	end)
	if not ok and Queue.isPermanent(err) then
		return false
	end
	return true
end

-- Player settings (UI Settings panel): the client fires ReplicatedStorage.WordEngineSettings with its values;
-- the server sanitises them with the shared Settings.SCHEMA, stores them in core.settings and mirrors them to the
-- player attribute "WE_Settings" (JSON) so the client restores them on join. Rate limited to 1 write / 2s.
local settingsBound = false
local lastSettingsWrite: { [any]: number } = {}
function Data.bindSettings()
	if settingsBound or (game :: any) == nil then
		return
	end
	settingsBound = true
	local okS, SettingsMod = pcall(function()
		return Env.shared().UI.Settings
	end)
	if not okS then
		return
	end
	local Http = Env.service("HttpService")
	local RS = Env.service("ReplicatedStorage")
	local remote = RS:FindFirstChild("WordEngineSettings") or Instance.new("RemoteEvent")
	remote.Name = "WordEngineSettings"
	remote.Parent = RS
	local function mirror(player: any)
		local core = Data.get(player)
		if core then
			pcall(function()
				player:SetAttribute("WE_Settings", Http:JSONEncode(SettingsMod.sanitize(core.settings)))
			end)
		end
	end
	Data.onLoaded(mirror)
	remote.OnServerEvent:Connect(function(player: any, raw: any)
		local now = Env.clock()
		if now - (lastSettingsWrite[player] or 0) < 2 or type(raw) ~= "table" then
			return
		end
		lastSettingsWrite[player] = now
		local clean = SettingsMod.sanitize(raw)
		Data.update(player, function(core)
			core.settings = clean
		end)
		mirror(player)
	end)
	Env.service("Players").PlayerRemoving:Connect(function(p)
		lastSettingsWrite[p] = nil
	end)
end

-- Idempotent. Binds Players, autosave, BindToClose and lock-release messages.
function Data.start(opts: { dataStore: any? }?)
	if started then
		return
	end
	started = true
	local o = opts or {}
	if not store then
		local ds = o.dataStore
		if ds == nil then
			ds = Env.service("DataStoreService"):GetDataStore(cfg().StoreName)
			if Env.isStudio() and not probeStore(ds) then
				Env.log("warn", "Data: Studio has no DataStore access (Game Settings > Security > Enable Studio Access to API Services). Using an in-memory store; nothing will persist.")
				ds = LocalStore.new("studio")
				offline = true
			end
		end
		store = buildStore(ds)
	end

	if not offline and Env.hasService("MessagingService") then
		Env.spawn(function()
			pcall(function()
				Env.service("MessagingService"):SubscribeAsync(cfg().ReleaseTopic, function(msg: any)
					local d = msg and msg.Data
					if type(d) ~= "table" or type(d.key) ~= "string" or not store then
						return
					end
					local s = (store :: SessionStore.SessionStore):get(d.key)
					if s and s.id == d.session then
						local p = findPlayer(d.key)
						Env.log("warn", "Data: another server asked for " .. d.key .. "; releasing")
						if p then
							Data.releasePlayer(p)
							if p.Parent ~= nil then
								p:Kick("You joined another server. See you there!")
							end
						else
							(store :: SessionStore.SessionStore):release(s)
						end
					end
				end)
			end)
		end)
	end

	local Players = Env.service("Players")
	Players.PlayerAdded:Connect(function(p)
		Data.loadPlayer(p)
	end)
	Players.PlayerRemoving:Connect(function(p)
		Data.releasePlayer(p)
	end)
	for _, p in Players:GetPlayers() do
		Env.spawn(Data.loadPlayer, p)
	end

	Env.spawn(autosaveLoop)
	pcall(Data.bindSettings)

	local g = (game :: any)
	if g then
		g:BindToClose(function()
			closing = true
			-- BindToClose gives ~30s total; leave margin for other handlers.
			local deadline = Env.clock() + 24
			local pending = 0
			for p in table.clone(sessions) do
				pending += 1
				Env.spawn(function()
					Data.releasePlayer(p, deadline)
					pending -= 1
				end)
			end
			while pending > 0 and Env.clock() < deadline + 1 do
				Env.wait(0.1)
			end
		end)
	end
end

-- Tests only.
function Data._reset()
	store = nil
	sessions = {}
	joinedAt = {}
	started = false
	offline = false
	closing = false
	Data.loaded:DisconnectAll()
	Data.releasing:DisconnectAll()
	Data.changed:DisconnectAll()
	for k in namespaces do
		if k ~= Data.CORE then
			namespaces[k] = nil
		end
	end
end

return Data
