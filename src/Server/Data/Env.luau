--!strict
-- Env: the single seam between the services layer and the Roblox engine.
-- Every Roblox global the services use (game services, task, JobId, time) goes through here so the
-- whole layer runs under Lune with mocks (tests call Env.set({...})). Never touches `game` at require time.

local Env = {}

export type Overrides = {
	services: { [string]: any }?,
	now: (() -> number)?, -- unix seconds (wall clock, comparable across servers)
	clock: (() -> number)?, -- monotonic seconds
	wait: ((number) -> ())?,
	spawn: ((fn: (...any) -> ...any, ...any) -> ())?,
	jobId: string?,
	placeId: number?,
	gameId: number?,
	isStudio: boolean?,
	shared: any?, -- WordEngine facade (ReplicatedStorage.WordEngine)
	config: any?,
	guid: (() -> string)?,
	log: ((level: string, msg: string) -> ())?,
}

local o: Overrides = {}

function Env.set(overrides: Overrides)
	o = overrides
end

function Env.reset()
	o = {}
end

local function rbx(): any
	return (game :: any)
end

function Env.service(name: string): any
	local s = o.services and o.services[name]
	if s ~= nil then
		return s
	end
	local g = rbx()
	assert(g, "Env.service: no game and no mock for " .. name)
	return g:GetService(name)
end

function Env.hasService(name: string): boolean
	if o.services and o.services[name] ~= nil then
		return true
	end
	return rbx() ~= nil
end

function Env.now(): number
	if o.now then
		return o.now()
	end
	local DT = (DateTime :: any)
	if DT then
		return DT.now().UnixTimestampMillis / 1000
	end
	return os.time()
end

function Env.clock(): number
	if o.clock then
		return o.clock()
	end
	return os.clock()
end

function Env.wait(seconds: number)
	if o.wait then
		o.wait(seconds)
		return
	end
	local t = (task :: any)
	t.wait(seconds)
end

function Env.spawn(fn: (...any) -> ...any, ...: any)
	if o.spawn then
		o.spawn(fn, ...)
		return
	end
	local t = (task :: any)
	t.spawn(fn, ...)
end

local studioJob: string? = nil
function Env.jobId(): string
	if o.jobId then
		return o.jobId
	end
	local g = rbx()
	local id = g and g.JobId or ""
	if id == "" then
		-- Studio: JobId is empty. Use one stable per-process id so locks still work.
		studioJob = studioJob or ("studio-" .. Env.guid())
		return studioJob :: string
	end
	return id
end

function Env.placeId(): number
	if o.placeId then
		return o.placeId
	end
	local g = rbx()
	return g and g.PlaceId or 0
end

function Env.gameId(): number
	if o.gameId then
		return o.gameId
	end
	local g = rbx()
	return g and g.GameId or 0
end

function Env.isStudio(): boolean
	if o.isStudio ~= nil then
		return o.isStudio :: boolean
	end
	local g = rbx()
	if not g then
		return false
	end
	local ok, res = pcall(function()
		return g:GetService("RunService"):IsStudio()
	end)
	return ok and res == true
end

local counter = 0
function Env.guid(): string
	if o.guid then
		return o.guid()
	end
	local g = rbx()
	if g then
		return g:GetService("HttpService"):GenerateGUID(false)
	end
	counter += 1
	return string.format("guid-%d-%d", os.time(), counter)
end

function Env.shared(): any
	if o.shared then
		return o.shared
	end
	local g = rbx()
	return require(g:GetService("ReplicatedStorage"):WaitForChild("WordEngine") :: any)
end

function Env.config(): any
	if o.config then
		return o.config
	end
	return Env.shared().Config
end

-- Optional sibling server module (owned by other agents). Returns nil if it does not exist.
function Env.server(name: string): any?
	local s = o.services and o.services["WordEngineServer." .. name]
	if s ~= nil then
		return s
	end
	local g = rbx()
	if not g then
		return nil
	end
	local root = g:GetService("ServerScriptService"):FindFirstChild("WordEngineServer")
	local m = root and root:FindFirstChild(name)
	if not m then
		return nil
	end
	local ok, mod = pcall(require, m :: any)
	return if ok then mod else nil
end

function Env.log(level: string, msg: string)
	if o.log then
		o.log(level, msg)
		return
	end
	if level == "error" or level == "warn" then
		warn("[WordEngine] " .. msg)
	else
		print("[WordEngine] " .. msg)
	end
end

return Env
