--!strict
-- Circuit breaker for the AI provider: Closed -> (N consecutive failures) -> Open for a cooldown
-- (doubling per re-open, capped) -> HalfOpen lets ONE probe through -> Closed on success.
-- Auth failures (401/403) open it for AuthCooldown: a bad key shouldn't be hammered.

local Runtime = require(script.Parent.Parent.Runtime)

local Circuit = {}

export type State = "Closed" | "Open" | "HalfOpen"

local state: State = "Closed"
local failures = 0
local openUntil = 0
local cooldown = 0
local probing = false

local function cfg(): any
	local c = Runtime.config()
	return (c and c.AI and c.AI.Circuit) or {}
end

function Circuit.reset()
	state, failures, openUntil, cooldown, probing = "Closed", 0, 0, 0, false
end

function Circuit.state(): State
	if state == "Open" and Runtime.clock() >= openUntil then
		state = "HalfOpen"
		probing = false
	end
	return state
end

-- May a request start now? In HalfOpen only one probe at a time.
function Circuit.allow(): boolean
	local s = Circuit.state()
	if s == "Closed" then
		return true
	elseif s == "HalfOpen" and not probing then
		probing = true
		return true
	end
	return false
end

-- Is the AI usable at all right now (without consuming the half-open probe)?
function Circuit.available(): boolean
	local s = Circuit.state()
	return s == "Closed" or (s == "HalfOpen" and not probing)
end

function Circuit.success()
	state, failures, cooldown, probing = "Closed", 0, 0, false
end

local function open(seconds: number)
	state = "Open"
	openUntil = Runtime.clock() + seconds
	probing = false
end

function Circuit.failure(auth: boolean?)
	local c = cfg()
	if auth then
		open(c.AuthCooldown or 900)
		Runtime.log("warn", "AI provider rejected the API key (401/403); AI paused. Check the secret.")
		return
	end
	failures += 1
	if state == "HalfOpen" or failures >= (c.FailureThreshold or 4) then
		cooldown = if cooldown == 0 then (c.Cooldown or 20) else math.min(cooldown * 2, c.MaxCooldown or 300)
		failures = 0
		open(cooldown)
		Runtime.log("warn", string.format("AI circuit open for %ds (library-only mode)", cooldown))
	end
end

return Circuit
