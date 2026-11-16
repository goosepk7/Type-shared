--!strict
-- Budget-aware request runner for DataStore calls.
--  * per-key serialisation: one in-flight request per key on this server (avoids self-throttling a key)
--  * request budget: waits on DataStoreService:GetRequestBudgetForRequestType before each attempt, keeping
--    Config.Services.Data.MinBudget spare for Critical requests (session releases, receipts)
--  * retries with exponential backoff + jitter on transient errors; fails fast on permanent ones
-- Docs: https://create.roblox.com/docs/cloud-services/data-stores/error-codes-and-limits

local Env = require(script.Parent.Env)

local Queue = {}
Queue.__index = Queue

export type Priority = "Critical" | "Normal" | "Low"
export type RunOptions = {
	key: string,
	requestType: string?, -- DataStoreRequestType name; default "UpdateAsync"
	priority: Priority?,
	attempts: number?,
	maxBudgetWait: number?, -- seconds to wait for budget before giving up (Low gives up early)
}

export type Queue = typeof(setmetatable(
	{} :: {
		_busy: { [string]: boolean },
		_cfg: () -> any,
		stats: { requests: number, retries: number, failures: number, budgetWaits: number },
	},
	Queue
))

-- Errors that will not succeed on retry (bad key/value, Studio access disabled, not permitted).
local PERMANENT = { "^%s*10[1-6]:", "API Services", "not allowed", "Cannot store", "Studio access", "403" }

function Queue.isPermanent(err: any): boolean
	local s = tostring(err)
	for _, p in PERMANENT do
		if string.find(s, p) then
			return true
		end
	end
	return false
end

function Queue.new(cfg: (() -> any)?): Queue
	return setmetatable({
		_busy = {},
		_cfg = cfg or function()
			return Env.config().Services.Data
		end,
		stats = { requests = 0, retries = 0, failures = 0, budgetWaits = 0 },
	}, Queue) :: any
end

local function budgetFor(requestType: string): number?
	if not Env.hasService("DataStoreService") then
		return nil
	end
	local ok, n = pcall(function()
		local dss = Env.service("DataStoreService")
		local enumType: any = requestType
		local E = (Enum :: any)
		if E then
			enumType = E.DataStoreRequestType[requestType]
		end
		return dss:GetRequestBudgetForRequestType(enumType)
	end)
	return if ok and type(n) == "number" then n else nil
end
Queue.budgetFor = budgetFor

function Queue._awaitBudget(self: Queue, requestType: string, priority: Priority, maxWait: number): boolean
	local cfg = self._cfg()
	local need = if priority == "Critical" then 1 elseif priority == "Normal" then cfg.MinBudget + 1 else cfg.MinBudget * 3 + 1
	local waited = 0
	while true do
		local b = budgetFor(requestType)
		if b == nil or b >= need then
			return true
		end
		if waited >= maxWait then
			return false
		end
		self.stats.budgetWaits += 1
		Env.wait(0.5)
		waited += 0.5
	end
end

-- Runs fn (which performs ONE DataStore call) with budget, per-key lock and retries.
-- Returns (true, ...results) or (false, errorString).
function Queue.run(self: Queue, opts: RunOptions, fn: () -> ...any): (boolean, ...any)
	local cfg = self._cfg()
	local key = opts.key
	local priority: Priority = opts.priority or "Normal"
	local requestType = opts.requestType or "UpdateAsync"
	local attempts = opts.attempts or cfg.RetryAttempts
	local maxWait = opts.maxBudgetWait or (if priority == "Low" then 5 elseif priority == "Normal" then 30 else 60)

	-- per-key serialisation
	local spins = 0
	while self._busy[key] do
		Env.wait(0.1)
		spins += 1
		if spins > 600 then
			return false, "queue: key busy timeout"
		end
	end
	self._busy[key] = true

	local lastErr: any = nil
	for attempt = 1, attempts do
		if not self:_awaitBudget(requestType, priority, maxWait) then
			lastErr = "queue: request budget exhausted"
			break
		end
		self.stats.requests += 1
		local result = table.pack(pcall(fn))
		if result[1] then
			self._busy[key] = nil
			return table.unpack(result, 1, result.n)
		end
		lastErr = result[2]
		if Queue.isPermanent(lastErr) or attempt == attempts then
			break
		end
		self.stats.retries += 1
		local delay = math.min(cfg.RetryBaseSeconds * 2 ^ (attempt - 1), cfg.RetryMaxSeconds)
		Env.wait(delay * (0.8 + math.random() * 0.4))
	end
	self._busy[key] = nil
	self.stats.failures += 1
	return false, tostring(lastErr)
end

return Queue
