--!strict
-- Pure bookkeeping for Effects: object pools, budget admission and FPS-driven auto-degrade.
-- No Roblox APIs here; the runtime supplies create/reset callbacks. Fully unit-tested.

local Pool = {}

-- ===========================================================================================================
-- Object pool

export type ObjectPool<T> = {
	name: string,
	acquire: (self: ObjectPool<T>) -> T,
	release: (self: ObjectPool<T>, obj: T) -> boolean,
	prewarm: (self: ObjectPool<T>, n: number) -> (),
	stats: (self: ObjectPool<T>) -> { free: number, inUse: number, created: number, destroyed: number },
	trim: (self: ObjectPool<T>, maxIdle: number) -> number,
	clear: (self: ObjectPool<T>) -> (),
}

--- create(): T makes a new object. reset(obj) parks a released object (hide/disable). destroy(obj) frees one
--- that will not be reused (beyond maxIdle). Releasing an object twice or one this pool did not hand out is
--- ignored and returns false (never corrupts the free list).
function Pool.new<T>(name: string, create: () -> T, reset: ((T) -> ())?, destroy: ((T) -> ())?, maxIdle: number?): ObjectPool<T>
	local free: { T } = {}
	local inUse: { [any]: boolean } = {}
	local inUseCount, created, destroyed = 0, 0, 0
	local cap = maxIdle or math.huge

	local self = {} :: any
	self.name = name

	function self.acquire(_): T
		local obj = table.remove(free)
		if obj == nil then
			obj = create()
			created += 1
		end
		inUse[obj] = true
		inUseCount += 1
		return obj :: T
	end

	function self.release(_, obj: T): boolean
		if obj == nil or not inUse[obj] then
			return false
		end
		inUse[obj] = nil
		inUseCount -= 1
		if reset then
			reset(obj)
		end
		if #free < cap then
			table.insert(free, obj)
		else
			destroyed += 1
			if destroy then
				destroy(obj)
			end
		end
		return true
	end

	function self.prewarm(_, n: number)
		for _ = #free + 1, math.min(n, cap) do
			local obj = create()
			created += 1
			if reset then
				reset(obj)
			end
			table.insert(free, obj)
		end
	end

	function self.trim(_, maxIdleNow: number): number
		local n = 0
		while #free > maxIdleNow do
			local obj = table.remove(free)
			destroyed += 1
			n += 1
			if destroy and obj ~= nil then
				destroy(obj)
			end
		end
		return n
	end

	function self.clear(_)
		self:trim(0)
	end

	function self.stats(_)
		return { free = #free, inUse = inUseCount, created = created, destroyed = destroyed }
	end

	return self :: ObjectPool<T>
end

-- ===========================================================================================================
-- Budget: admission control across all live effects.

export type Cost = { parts: number?, emitters: number?, beams: number?, trails: number?, lights: number?, highlights: number? }

local RESOURCES = { "parts", "emitters", "beams", "trails", "lights", "highlights" }
local LIMIT_KEY = { parts = "maxParts", emitters = "maxEmitters", beams = "maxBeams", trails = "maxTrails", lights = "maxLights", highlights = "maxHighlights" }
Pool.Resources = RESOURCES

export type Budget = {
	tier: string,
	limits: { [string]: any },
	usage: { [string]: number },
	effects: number,
	setTier: (self: Budget, tier: string) -> (),
	admit: (self: Budget, cost: Cost, priority: number?) -> (boolean, number, string?),
	commit: (self: Budget, cost: Cost) -> (),
	refund: (self: Budget, cost: Cost) -> (),
	fraction: (self: Budget) -> number,
}

--- cfg = Config.Visual.Effects. Returns a Budget for `tier`.
function Pool.budget(cfg: any, tier: string): Budget
	local self = {} :: any
	self.usage = { parts = 0, emitters = 0, beams = 0, trails = 0, lights = 0, highlights = 0 }
	self.effects = 0

	function self.setTier(_, t: string)
		assert(cfg.Budgets[t], "unknown quality tier " .. tostring(t))
		self.tier = t
		self.limits = cfg.Budgets[t]
	end
	self:setTier(tier)

	--- Highest usage fraction across resources (0..1+), including the effect count.
	function self.fraction(_): number
		local f = self.effects / self.limits.maxEffects
		for _, r in RESOURCES do
			local lim = self.limits[LIMIT_KEY[r]]
			if lim and lim > 0 then
				f = math.max(f, self.usage[r] / lim)
			end
		end
		return f
	end

	--- Can an effect costing `cost` start now? Returns (ok, scale, reason):
	--- scale (0.4..1) is a suggested particle/detail multiplier when the budget is getting full.
	--- priority 0 = ambient (refused early), 1 = normal, 2+ = local player (may overflow by PriorityOverflow).
	function self.admit(_, cost: Cost, priority: number?): (boolean, number, string?)
		local p = priority or 1
		local overflow = if p >= 2 then cfg.PriorityOverflow else 1
		local cutoff = if p <= 0 then cfg.LowPriorityCutoff else 1
		if (self.effects + 1) > self.limits.maxEffects * overflow * cutoff then
			return false, 0, "maxEffects"
		end
		local worst = (self.effects + 1) / self.limits.maxEffects
		for _, r in RESOURCES do
			local need = (cost :: any)[r] or 0
			if need > 0 then
				local lim = self.limits[LIMIT_KEY[r]] or 0
				if r == "highlights" or r == "lights" then
					-- optional extras: never block an effect, the runtime simply skips them when over
					continue
				end
				if self.usage[r] + need > lim * overflow * cutoff then
					return false, 0, LIMIT_KEY[r]
				end
				if lim > 0 then
					worst = math.max(worst, (self.usage[r] + need) / lim)
				end
			end
		end
		-- Above 60% usage, start thinning particles smoothly down to 0.4 at 100%.
		local scale = if worst <= 0.6 then 1 else math.max(0.4, 1 - (worst - 0.6) * 1.5)
		return true, scale, nil
	end

	function self.commit(_, cost: Cost)
		self.effects += 1
		for _, r in RESOURCES do
			self.usage[r] += (cost :: any)[r] or 0
		end
	end

	function self.refund(_, cost: Cost)
		self.effects = math.max(0, self.effects - 1)
		for _, r in RESOURCES do
			self.usage[r] = math.max(0, self.usage[r] - ((cost :: any)[r] or 0))
		end
	end

	--- Can one more optional resource of kind r be used right now (lights/highlights)?
	function self.allow(_, r: string): boolean
		local lim = self.limits[LIMIT_KEY[r]] or 0
		return self.usage[r] < lim
	end

	--- Count live optional resources (lights/highlights acquired outside the estimate).
	function self.use(_, r: string, delta: number)
		self.usage[r] = math.max(0, self.usage[r] + delta)
	end

	return self :: Budget
end

-- ===========================================================================================================
-- Quality: device class -> tier, plus FPS auto-degrade with hysteresis.

--- Pick the starting tier. deviceClass in Desktop/Console/Tablet/Phone. savedQuality is the player's
--- graphics level 1..10 (0/nil = automatic). Very low graphics settings pull the tier down too.
function Pool.pickTier(cfg: any, deviceClass: string, savedQuality: number?): string
	if cfg.Quality and cfg.Quality ~= "Auto" and cfg.Budgets[cfg.Quality] then
		return cfg.Quality
	end
	local tier = cfg.DeviceTier[deviceClass] or "Medium"
	if savedQuality and savedQuality > 0 then
		if savedQuality <= 3 then
			tier = "Low"
		elseif savedQuality <= 5 and tier ~= "Low" then
			tier = "Medium"
		elseif savedQuality >= 9 and tier == "High" then
			tier = "Ultra"
		end
	end
	return tier
end

export type Degrader = {
	tier: string,
	ceiling: string,
	fps: number,
	step: (self: Degrader, dt: number) -> string?,
}

--- Auto-degrade controller. step(dt) feeds one frame; returns the new tier name when it changes, else nil.
--- Steps down one tier after DowngradeAfter seconds below DowngradeFps (immediately at CriticalFps for
--- DowngradeAfter/3), and back up one tier after UpgradeAfter seconds above UpgradeFps, never above ceiling.
function Pool.degrader(cfg: any, ceiling: string): Degrader
	local ad = cfg.AutoDegrade
	local order = cfg.TierOrder
	local index: { [string]: number } = {}
	for i, t in order do
		index[t] = i
	end
	local self = {} :: any
	self.tier = ceiling
	self.ceiling = ceiling
	self.fps = 60
	local low, high = 0, 0
	local cooldown = 0

	function self.step(_, dt: number): string?
		if not ad.Enabled or dt <= 0 then
			return nil
		end
		local inst = 1 / math.max(dt, 1 / 240)
		self.fps += (inst - self.fps) * (ad.Smoothing or 0.1)
		cooldown = math.max(0, cooldown - dt)
		if self.fps < ad.DowngradeFps then
			low += dt * (if self.fps < ad.CriticalFps then 3 else 1)
			high = 0
		elseif self.fps > ad.UpgradeFps then
			high += dt
			low = 0
		else
			low = math.max(0, low - dt)
			high = math.max(0, high - dt)
		end
		local i = index[self.tier]
		if low >= ad.DowngradeAfter and i > 1 and cooldown <= 0 then
			self.tier = order[i - 1]
			low, high, cooldown = 0, 0, ad.DowngradeAfter
			return self.tier
		end
		if high >= ad.UpgradeAfter and i < index[self.ceiling] and cooldown <= 0 then
			self.tier = order[i + 1]
			low, high, cooldown = 0, 0, ad.DowngradeAfter
			return self.tier
		end
		return nil
	end

	function self.setCeiling(_, t: string)
		self.ceiling = t
		if index[self.tier] > index[t] then
			self.tier = t
		end
	end

	return self :: Degrader
end

-- ===========================================================================================================
-- Ground height slots: overlapping ground layers from different effects never share a plane.

--- Returns a function next() -> slot in 1..n, cycling. With n >= concurrent ground layers in one spot,
--- two overlapping layers always get different heights.
function Pool.slots(n: number): () -> number
	local i = 0
	return function(): number
		i = i % n + 1
		return i
	end
end

return Pool
