--!strict
-- Runtime: the single seam between server modules and Roblox globals. Everything that touches
-- `game`, `task`, `Enum`, the clock or Shared goes through here so tests (Lune) can inject mocks
-- with Runtime.set({...}). Production code never calls Runtime.set.

local Runtime = {}

type Overrides = {
	services: { [string]: any }?,
	task: any?,
	clock: (() -> number)?,
	now: (() -> number)?,
	shared: any?,
	config: any?,
	gameId: number?,
	filterContext: any?,
	random: (() -> number)?,
	log: ((level: string, msg: string) -> ())?,
	serverModules: { [string]: any }?,
	jobId: string?,
}

local overrides: Overrides = {}

function Runtime.set(o: Overrides)
	overrides = o
end

function Runtime.reset()
	overrides = {}
end

function Runtime.service(name: string): any
	local s = overrides.services
	if s and s[name] ~= nil then
		return s[name]
	end
	return (game :: any):GetService(name)
end

-- The `task` library (Roblox global; injected under Lune).
function Runtime.task(): any
	if overrides.task then
		return overrides.task
	end
	return (task :: any)
end

function Runtime.clock(): number
	if overrides.clock then
		return overrides.clock()
	end
	return os.clock()
end

-- Unix seconds.
function Runtime.now(): number
	if overrides.now then
		return overrides.now()
	end
	return os.time()
end

function Runtime.random(): number
	if overrides.random then
		return overrides.random()
	end
	return math.random()
end

function Runtime.dayKey(): string
	local t = os.date("!*t", Runtime.now()) :: any
	return string.format("%04d-%02d-%02d", t.year, t.month, t.day)
end

function Runtime.gameId(): number
	if overrides.gameId then
		return overrides.gameId
	end
	return (game :: any).GameId
end

-- This server's id (game.JobId; "" in Studio play-solo, so fall back to a random per-process id).
local fallbackJobId: string? = nil
function Runtime.jobId(): string
	if overrides.jobId then
		return overrides.jobId
	end
	local ok, id = pcall(function()
		return (game :: any).JobId
	end)
	if ok and type(id) == "string" and id ~= "" then
		return id
	end
	if not fallbackJobId then
		fallbackJobId = string.format("local-%08x", math.random(0, 0x7fffffff))
	end
	return fallbackJobId :: string
end

function Runtime.filterContext(): any
	if overrides.filterContext ~= nil then
		return overrides.filterContext
	end
	return (Enum :: any).TextFilterContext.PublicChat
end

local sharedRoot: any = nil
function Runtime.shared(): any
	if overrides.shared then
		return overrides.shared
	end
	if sharedRoot == nil then
		local rs = (game :: any):GetService("ReplicatedStorage")
		sharedRoot = require(rs:WaitForChild("WordEngine") :: any)
	end
	return sharedRoot
end

-- A Shared module or nil (modules owned by other agents may be missing during development).
function Runtime.sharedModule(name: string): any
	local root = Runtime.shared()
	local ok, mod = pcall(function()
		return root[name]
	end)
	if ok then
		return mod
	end
	return nil
end

-- A sibling server module owned by another subsystem (Analytics, Admin, ...) or nil.
local serverModuleCache: { [string]: any } = {}
function Runtime.serverModule(name: string): any
	local o = (overrides :: any).serverModules
	if o then
		return o[name]
	end
	if serverModuleCache[name] ~= nil then
		return serverModuleCache[name] or nil
	end
	local ok, mod = pcall(function()
		local inst = script.Parent:FindFirstChild(name)
		return if inst then require(inst :: any) else nil
	end)
	serverModuleCache[name] = if ok and mod ~= nil then mod else false
	return if ok then mod else nil
end

-- pcall a function on another subsystem's module; never errors, returns nothing useful on failure.
function Runtime.call(moduleName: string, fnName: string, ...: any): (boolean, any)
	local mod = Runtime.serverModule(moduleName)
	local fn = mod and mod[fnName]
	if type(fn) ~= "function" then
		return false, nil
	end
	return pcall(fn, ...)
end

function Runtime.config(): any
	if overrides.config then
		return overrides.config
	end
	return Runtime.sharedModule("Config")
end

-- Logging never includes secrets: callers pass plain strings and the Secret datatype prints as
-- Secret(name) anyway. Keep messages short and without player text.
function Runtime.log(level: string, msg: string)
	if overrides.log then
		overrides.log(level, msg)
		return
	end
	if level == "warn" then
		warn("[WordEngine] " .. msg)
	else
		print("[WordEngine] " .. msg)
	end
end

local warned: { [string]: boolean } = {}
function Runtime.warnOnce(key: string, msg: string)
	if warned[key] then
		return
	end
	warned[key] = true
	Runtime.log("warn", msg)
end
function Runtime.clearWarnOnce()
	table.clear(warned)
end

function Runtime.jsonEncode(v: any): string?
	local ok, s = pcall(function()
		return Runtime.service("HttpService"):JSONEncode(v)
	end)
	return if ok then s else nil
end

function Runtime.jsonDecode(s: string): any
	local ok, v = pcall(function()
		return Runtime.service("HttpService"):JSONDecode(s)
	end)
	return if ok then v else nil
end

-- Minimal signal with late-subscriber replay (handle.upgraded may fire before :Connect in edge
-- cases; a replaying signal makes that race harmless).
export type Connection = { Connected: boolean, Disconnect: (self: Connection) -> () }
export type Signal = {
	Connect: (self: Signal, fn: (...any) -> ()) -> Connection,
	Once: (self: Signal, fn: (...any) -> ()) -> Connection,
	Fire: (self: Signal, ...any) -> (),
	_fns: { any },
	_last: { any }?,
	_replay: boolean,
}

local SignalImpl = {}
SignalImpl.__index = SignalImpl

function SignalImpl.Connect(self: any, fn: (...any) -> ()): Connection
	local conn: any = { Connected = true }
	function conn.Disconnect(c: any)
		c.Connected = false
	end
	local entry = { fn = fn, conn = conn, once = false }
	table.insert(self._fns, entry)
	if self._replay and self._last then
		local args = self._last
		Runtime.task().spawn(function()
			if conn.Connected then
				fn(table.unpack(args, 1, args.n))
			end
		end)
	end
	return conn
end

function SignalImpl.Once(self: any, fn: (...any) -> ()): Connection
	local conn: Connection
	conn = SignalImpl.Connect(self, function(...)
		if conn.Connected then
			conn:Disconnect()
			fn(...)
		end
	end)
	return conn
end

function SignalImpl.Fire(self: any, ...: any)
	if self._replay then
		self._last = table.pack(...)
	end
	for _, entry in table.clone(self._fns) do
		if entry.conn.Connected then
			Runtime.task().spawn(entry.fn, ...)
		end
	end
end

function Runtime.signal(replay: boolean?): Signal
	return setmetatable({ _fns = {}, _last = nil, _replay = replay == true }, SignalImpl) :: any
end

-- Future: resolved once; await(timeout) yields the current thread until resolved or timed out.
export type Future = {
	done: boolean,
	value: any,
	err: string?,
	resolve: (self: Future, value: any, err: string?) -> (),
	onDone: (self: Future, fn: (value: any, err: string?) -> ()) -> (),
	await: (self: Future, timeout: number?) -> (boolean, any, string?),
	_cbs: { (any, string?) -> () },
}

local FutureImpl = {}
FutureImpl.__index = FutureImpl

function FutureImpl.resolve(self: any, value: any, err: string?)
	if self.done then
		return
	end
	self.done = true
	self.value = value
	self.err = err
	local cbs = self._cbs
	self._cbs = {}
	for _, cb in cbs do
		local ok, e = pcall(cb, value, err)
		if not ok then
			Runtime.log("warn", "future callback failed: " .. tostring(e))
		end
	end
end

function FutureImpl.onDone(self: any, fn: (any, string?) -> ())
	if self.done then
		fn(self.value, self.err)
	else
		table.insert(self._cbs, fn)
	end
end

-- Returns (finished, value, err). Never errors.
function FutureImpl.await(self: any, timeout: number?): (boolean, any, string?)
	if self.done then
		return true, self.value, self.err
	end
	local thread = coroutine.running()
	local resumed = false
	local t = Runtime.task()
	local function wake(finished: boolean)
		if resumed then
			return
		end
		resumed = true
		t.spawn(thread, finished)
	end
	table.insert(self._cbs, function()
		wake(true)
	end)
	if timeout then
		t.delay(timeout, function()
			wake(false)
		end)
	end
	local finished = coroutine.yield()
	if finished then
		return true, self.value, self.err
	end
	return false, nil, "timeout"
end

function Runtime.future(): Future
	return setmetatable({ done = false, value = nil, err = nil, _cbs = {} }, FutureImpl) :: any
end

return Runtime
