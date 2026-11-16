--!strict
-- Net: remotes between client and server for interpretation.
--
-- Server: WordEngineServer.start({ remotes = true }) calls Net.setupServer(handler). Every argument
--   from the client is validated (type, UTF-8, <= 40 characters, integer request id) and rate
--   limited per player BEFORE reaching the Interpreter (which applies its own Safety limits too).
-- Client:
--   local result, info = WordEngine.Net.interpret("dragn")   -- yields for the instant result
--   info.upgraded:Connect(function(better) ... end)           -- fires once if the AI improves it
--   WordEngine.Net.Upgraded:Connect(function(better, requestId) ... end) -- every upgrade
--
-- Touches Roblox APIs only inside functions (pure at require time).

local Schema = require(script.Parent.Schema)

local Net = {}

Net.FOLDER = "WordEngineRemotes"
Net.INTERPRET = "Interpret" -- RemoteFunction (text, requestId) -> { r, id, p, reason }
Net.UPGRADED = "Upgraded" -- RemoteEvent server->client (requestId, WordResult)
Net.MAX_CHARS = 40
Net.INVOKE_TIMEOUT = 8

-- Tiny signal (client + server), Roblox task scheduler.
type Conn = { Connected: boolean, Disconnect: (Conn) -> () }
local SignalMT = {}
SignalMT.__index = SignalMT
function SignalMT.Connect(self: any, fn: (...any) -> ()): Conn
	local conn: any = { Connected = true }
	function conn.Disconnect(c: any)
		c.Connected = false
	end
	table.insert(self._fns, { fn = fn, conn = conn })
	return conn
end
function SignalMT.Once(self: any, fn: (...any) -> ()): Conn
	local conn: any
	conn = SignalMT.Connect(self, function(...)
		if conn.Connected then
			conn:Disconnect()
			fn(...)
		end
	end)
	return conn
end
function SignalMT.Fire(self: any, ...: any)
	for _, e in table.clone(self._fns) do
		if e.conn.Connected then
			(task :: any).spawn(e.fn, ...)
		end
	end
end
function Net.createSignal(): any
	return setmetatable({ _fns = {} }, SignalMT)
end

-- Pure argument validation (shared by server handler and tests).
-- Returns (ok, text, requestId, reason).
function Net.validateArgs(text: any, requestId: any): (boolean, string, number, string)
	local id = 0
	if type(requestId) == "number" and requestId == requestId and requestId >= 0 and requestId < 2 ^ 31 and requestId % 1 == 0 then
		id = requestId
	end
	if type(text) ~= "string" then
		return false, "", id, "Invalid"
	end
	if #text > Net.MAX_CHARS * 4 then
		return false, "", id, "TooLong"
	end
	local n = utf8.len(text)
	if n == nil then
		return false, "", id, "Invalid"
	end
	if n > Net.MAX_CHARS then
		return false, "", id, "TooLong"
	end
	if string.find(text, "%c") then
		text = string.gsub(text, "%c", " ")
	end
	return true, text, id, "Ok"
end

-- Token bucket per player for raw remote traffic.
local buckets: { [number]: { tokens: number, last: number } } = {}
function Net.allow(userId: number, capacity: number, refill: number, now: number): boolean
	local b = buckets[userId]
	if not b then
		b = { tokens = capacity, last = now }
		buckets[userId] = b
	end
	b.tokens = math.min(capacity, b.tokens + (now - b.last) * refill)
	b.last = now
	if b.tokens < 1 then
		return false
	end
	b.tokens -= 1
	return true
end
function Net.forget(userId: number)
	buckets[userId] = nil
end

local function reply(result: any, id: number, pending: boolean, reason: string): { [string]: any }
	return { r = result, id = id, p = pending, reason = reason }
end

-- handler(player, text) -> (WordResult, handle { pending: boolean, reason: string, upgraded: Signal })
function Net.setupServer(handler: (any, string) -> (any, any), opts: { capacity: number?, refill: number? }?)
	local ReplicatedStorage = game:GetService("ReplicatedStorage")
	local Players = game:GetService("Players")
	local folder = ReplicatedStorage:FindFirstChild(Net.FOLDER)
	if not folder then
		folder = Instance.new("Folder")
		folder.Name = Net.FOLDER
		folder.Parent = ReplicatedStorage
	end
	local rf = folder:FindFirstChild(Net.INTERPRET) :: RemoteFunction?
	if not rf then
		local created = Instance.new("RemoteFunction")
		created.Name = Net.INTERPRET
		created.Parent = folder
		rf = created
	end
	local re = folder:FindFirstChild(Net.UPGRADED) :: RemoteEvent?
	if not re then
		local created = Instance.new("RemoteEvent")
		created.Name = Net.UPGRADED
		created.Parent = folder
		re = created
	end
	local capacity = (opts and opts.capacity) or 12
	local refill = (opts and opts.refill) or 5
	local upgradedEvent = re :: RemoteEvent;

	(rf :: RemoteFunction).OnServerInvoke = function(player: Player, text: any, requestId: any)
		local ok, clean, id, reason = Net.validateArgs(text, requestId)
		if not ok then
			return reply(Schema.fallback(""), id, false, reason)
		end
		if not Net.allow(player.UserId, capacity, refill, os.clock()) then
			return reply(Schema.fallback(clean), id, false, "RateLimited")
		end
		local okH, result, handle = pcall(handler, player, clean)
		if not okH or type(result) ~= "table" then
			return reply(Schema.fallback(clean), id, false, "Error")
		end
		local pending = type(handle) == "table" and handle.pending == true
		if pending and handle.upgraded then
			handle.upgraded:Once(function(better: any)
				if player.Parent ~= nil then
					upgradedEvent:FireClient(player, id, better)
				end
			end)
		end
		return reply(result, id, pending, if type(handle) == "table" then tostring(handle.reason or "Ok") else "Ok")
	end

	Players.PlayerRemoving:Connect(function(player: Player)
		Net.forget(player.UserId)
	end)
	return folder
end

-- Client ------------------------------------------------------------------------------------------

Net.Upgraded = Net.createSignal() -- (WordResult, requestId)

local nextId = 0
local waiting: { [number]: any } = {}
local clientRemotes: { rf: RemoteFunction, re: RemoteEvent }? = nil

local function remotes(): { rf: RemoteFunction, re: RemoteEvent }?
	if clientRemotes then
		return clientRemotes
	end
	local ReplicatedStorage = game:GetService("ReplicatedStorage")
	local folder = ReplicatedStorage:WaitForChild(Net.FOLDER, Net.INVOKE_TIMEOUT)
	if not folder then
		return nil
	end
	local rf = folder:WaitForChild(Net.INTERPRET, Net.INVOKE_TIMEOUT) :: RemoteFunction?
	local re = folder:WaitForChild(Net.UPGRADED, Net.INVOKE_TIMEOUT) :: RemoteEvent?
	if not (rf and re) then
		return nil
	end
	re.OnClientEvent:Connect(function(id: any, raw: any)
		local better = Schema.repair(raw)
		local info = if type(id) == "number" then waiting[id] else nil
		if info then
			waiting[id] = nil
			info.pending = false
			info.result = better
			info.upgraded:Fire(better)
		end
		Net.Upgraded:Fire(better, id)
	end)
	clientRemotes = { rf = rf, re = re }
	return clientRemotes
end

local function localGuess(text: string): any
	local ok, r = pcall(function()
		local resolver = script.Parent:FindFirstChild("Resolver")
		return if resolver then (require(resolver :: any) :: any).resolveLocal(text) else nil
	end)
	if ok and type(r) == "table" then
		return r
	end
	return Schema.fallback(text)
end

-- Yields until the server answers (<= ~1.5 s normally). Never errors, never nil.
-- info = { requestId, pending, reason, upgraded: Signal, result }
function Net.interpret(text: string): (any, any)
	nextId += 1
	local id = nextId
	local info: { [string]: any } = { requestId = id, pending = false, reason = "Ok", upgraded = Net.createSignal(), result = nil }
	local r = remotes()
	if not r then
		info.reason = "Offline"
		info.result = localGuess(text)
		return info.result, info
	end
	local ok, resp = pcall(function()
		return r.rf:InvokeServer(text, id)
	end)
	if not ok or type(resp) ~= "table" then
		info.reason = "Offline"
		info.result = localGuess(text)
		return info.result, info
	end
	local result = Schema.repair(resp.r, text)
	info.pending = resp.p == true
	info.reason = if type(resp.reason) == "string" then resp.reason else "Ok"
	info.result = result
	if info.pending then
		waiting[id] = info
		task.delay(60, function()
			waiting[id] = nil
		end)
	end
	return result, info
end

return Net
