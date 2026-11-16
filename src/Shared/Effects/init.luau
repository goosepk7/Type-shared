--!nonstrict
-- WordEngine Effects: pooled, phone-friendly VFX for both games, in two styles from one API.
--
--   local Effects = WordEngine.Effects
--   local h = Effects.play("projectile.meteor", { style = "Spectral", element = "Fire", to = hitPos, scale = 1.5 })
--   h:onFinished(function() ... end)   h:stop()   h:setTarget(model)   h:isPlaying()   h:pulse() (shields)
--   Effects.status(model, "Burn", 4)          -- refreshes instead of stacking the same status
--   Effects.reaction(reaction, { at = cf })   -- plays Reaction.vfx
--
-- params: style ("Spectral" | "Solid"; default Effects.setDefaultStyle), element, from, to, at (CFrame/Vector3),
--         target (Instance), scale, colour ("#RRGGBB" override), duration (seconds; loops otherwise run until
--         stop), priority (0 ambient, 1 normal, 2 local player), seed, impact (projectiles), radius, length,
--         points/targets (chains), shake (false to skip camera shake), keepHidden (dissolve)
--
-- Client-side by design (Roblox guidance: keep purely visual effects on the client). On the server play()
-- returns an inert handle unless Config.Visual.Effects.AllowServer is true. Roblox APIs are only touched inside
-- functions, so this module (and its pure submodules) require cleanly under Lune for tests.
-- See docs/EFFECTS.md for every effect id, its params and the budgets.

local Config = require(script.Parent.Config)
local Catalogue = require(script.Catalogue)
local Palettes = require(script.Palettes)
local Curves = require(script.Curves)
local Pool = require(script.Pool)
local Presets = require(script.Presets)
local Assets = require(script.Assets)

local Effects = {}
Effects.Catalogue = Catalogue
Effects.Palettes = Palettes
Effects.Curves = Curves
Effects.Pool = Pool
Effects.Presets = Presets
Effects.Assets = Assets

local ECFG = Config.Visual.Effects
local defaultStyle = "Spectral"
local Runtime = nil
local kinds = {}
local statusByTarget = setmetatable({}, { __mode = "k" })
local warned = {}

local KIND_NAMES = { "Projectile", "Beam", "Strike", "Impact", "Explosion", "Burst", "Aura", "Shield", "Wall", "Cloud", "Rain", "Wave", "Zone", "Weather", "Spawn", "Status", "Attached", "Composite" }
Effects.Kinds = KIND_NAMES

local function warnOnce(key: string, msg: string)
	if not warned[key] then
		warned[key] = true
		warn("[Effects] " .. msg)
	end
end

local function runtime()
	if Runtime == nil then
		Runtime = require(script.Runtime)
		Runtime.facade = Effects
	end
	return Runtime
end

local function kind(name: string)
	local k = kinds[name]
	if k == nil then
		k = require(script.Kinds[name])
		kinds[name] = k
	end
	return k
end

-- ===========================================================================================================
-- Handles

local Handle = {}
Handle.__index = Handle

local function newHandle(id: string, fx)
	return setmetatable({ id = id, _fx = fx, _cbs = {}, _done = fx == nil }, Handle)
end

function Handle:stop()
	if self._fx then
		self._fx:stop()
	elseif not self._done then
		self._done = true
		for _, cb in self._cbs do
			task.spawn(cb)
		end
	end
end

function Handle:isPlaying(): boolean
	return self._fx ~= nil and not self._fx.dead and not self._fx.stopping
end

function Handle:setTarget(target)
	local fx = self._fx
	if fx then
		fx.target = target
		if fx.onTarget then
			fx.onTarget(target)
		end
	end
end

--- Flash a shield (or any effect that defines onPulse) when it is hit.
function Handle:pulse()
	local fx = self._fx
	if fx and fx.onPulse then
		fx.onPulse()
	end
end

function Handle:onFinished(cb: () -> ())
	if self._fx then
		if self._fx.dead then
			task.spawn(cb)
		else
			table.insert(self._fx.finishedCallbacks, cb)
		end
	elseif self._done then
		task.spawn(cb)
	else
		table.insert(self._cbs, cb)
	end
	return self
end

-- Inert handle: same API, nothing rendered (server, culled, refused, unknown). Finishes after `duration`.
local function inert(id: string, duration: number?)
	local h = newHandle(id, nil)
	h._done = false
	if duration and duration > 0 then
		task.delay(duration, function()
			h:stop()
		end)
	end
	return h
end

-- ===========================================================================================================
-- Public API

function Effects.setDefaultStyle(style: string)
	assert(style == "Spectral" or style == "Solid", "style must be Spectral or Solid")
	defaultStyle = style
end

function Effects.defaultStyle(): string
	return defaultStyle
end

--- Override the environment (tests / custom containers). See Runtime.init.
function Effects.init(custom: any?)
	return runtime().init(custom)
end

--- Called on big explosions: fn(position: Vector3, intensity 0..1). Games wire this to their camera shake.
function Effects.setShakeHandler(fn)
	runtime().shake = fn
end

--- Force a quality tier ("Ultra" | "High" | "Medium" | "Low"), e.g. from a settings menu. "Auto" re-detects.
function Effects.setQuality(tier: string)
	ECFG.Quality = tier
	local R = runtime()
	R.init()
	if tier == "Auto" then
		local env = R.env()
		R.setTier(Pool.pickTier(ECFG, env.deviceClass, 0))
	else
		R.setTier(tier)
	end
end

local function isServer(): boolean
	local ok, server = pcall(function()
		return game:GetService("RunService"):IsServer() and not game:GetService("RunService"):IsClient()
	end)
	return ok and server == true
end

local function resolveId(effectId: string)
	local entry = Catalogue.get(effectId)
	if entry then
		return effectId, entry
	end
	-- forgiving fallbacks so data typos never break play: bare material particle -> sparkle, family -> generic
	local family = string.match(effectId or "", "^([^%.]+)")
	local fallback = if family == "impact" then "impact" elseif family == "status" then "status.stun" elseif family == "reaction" then "burst.nova" elseif family == nil or not string.find(effectId, "%.") then "sparkle" else "impact"
	warnOnce("id:" .. tostring(effectId), ("unknown effect id %q, using %q"):format(tostring(effectId), fallback))
	return fallback, Catalogue.get(fallback)
end

--- Play an effect. Never errors for bad input; always returns a handle.
function Effects.play(effectId: string, params: any?)
	params = params or {}
	local id, entry = resolveId(effectId)
	local dur = params.duration or entry.duration
	if isServer() and not ECFG.AllowServer then
		warnOnce("server", "Effects.play on the server is a no-op (play effects on clients; set Config.Visual.Effects.AllowServer to override)")
		return inert(id, dur)
	end
	local R = runtime()
	R.init()
	local style = params.style or defaultStyle
	if style ~= "Solid" then
		style = "Spectral"
	end
	local element = Palettes.normalize(params.element or entry.element)

	local okPos, pos = pcall(function()
		return R.posOf(params.at) or R.posOf(params.target) or R.posOf(params.to) or R.posOf(params.from)
	end)
	if not okPos then
		pos = nil
	end
	-- distance cull (not for camera-relative weather)
	if entry.kind ~= "Weather" then
		local cam = R.cameraPos()
		if cam and pos and (pos - cam).Magnitude > ECFG.CullDistance and (params.priority or 1) < 2 then
			R.stats.culled += 1
			return inert(id, dur)
		end
	end

	local budget = R.budget()
	local cost = if entry.kind == "Composite" then {} else Catalogue.cost(id)
	local ok, scale = budget:admit(cost, params.priority)
	if not ok then
		R.stats.refused += 1
		return inert(id, dur)
	end
	-- the same effect started on the same spot (two players casting the same spell): scale each copy a
	-- little bigger so their shells and faces never coincide
	local stack = if entry.kind == "Weather" then 0 else math.min(R.stacked(entry, pos), 6)
	local fx = R.newFx(entry, params, style, element, (params.scale or 1) * (entry.scale or 1) * (1 + 0.07 * stack), scale)
	fx.origin = pos
	fx.cost = cost
	budget:commit(cost)
	local handle = newHandle(id, fx)
	local success, err = pcall(kind(entry.kind), fx)
	if not success then
		warnOnce("err:" .. id, ("%s failed to start: %s"):format(id, tostring(err)))
		R.releaseFx(fx)
		return inert(id, 0)
	end
	R.stats.started += 1
	R.add(fx)
	return handle
end

--- Status visual on a target. Re-applying the same status refreshes its duration instead of stacking.
--- Extra opts: { style, element, colour }. At most MaxStatusesPerTarget visuals per target (oldest replaced).
function Effects.status(target: Instance, status: string, duration: number?, opts: any?)
	local id = Catalogue.statusId(status or "")
	if not Catalogue.has(id) then
		warnOnce("status:" .. tostring(status), ("unknown status %q"):format(tostring(status)))
		return inert(id, duration)
	end
	local list = statusByTarget[target]
	if list == nil then
		list = {}
		statusByTarget[target] = list
	end
	local existing = list[status]
	if existing and existing.handle:isPlaying() then
		local fx = existing.handle._fx
		fx.duration = fx.t + (duration or 3)
		fx.loop = false
		return existing.handle
	end
	-- cap concurrent statuses on one target
	local count, oldestKey, oldestAt = 0, nil, math.huge
	for k, rec in list do
		if rec.handle:isPlaying() then
			count += 1
			if rec.at < oldestAt then
				oldestKey, oldestAt = k, rec.at
			end
		else
			list[k] = nil
		end
	end
	if count >= ECFG.MaxStatusesPerTarget and oldestKey then
		list[oldestKey].handle:stop()
		list[oldestKey] = nil
	end
	local p = { target = target, duration = duration or 3, priority = 1 }
	if opts then
		for k, v in opts do
			p[k] = v
		end
	end
	local h = Effects.play(id, p)
	list[status] = { handle = h, at = os.clock() }
	return h
end

--- Remove a status visual early (e.g. cleansed).
function Effects.clearStatus(target: Instance, status: string?)
	local list = statusByTarget[target]
	if not list then
		return
	end
	for k, rec in list do
		if status == nil or k == status then
			rec.handle:stop()
			list[k] = nil
		end
	end
end

--- Play a Reaction's visual (accepts a Reaction table or id).
function Effects.reaction(reaction: any, params: any?)
	local r = reaction
	if type(r) == "string" then
		r = require(script.Parent.Reactions).byId(r)
	end
	if not r then
		return inert("reaction", 0)
	end
	local p = table.clone(params or {})
	p.duration = p.duration or r.durationHint
	return Effects.play(r.vfx, p)
end

--- Plain table for remotes: server tells clients what to play (Instances, Vector3, CFrame serialise natively).
function Effects.serialize(effectId: string, params: any?): any
	local out = { id = effectId }
	for k, v in params or {} do
		local tv = typeof(v)
		if tv ~= "function" and tv ~= "thread" then
			out[k] = v
		end
	end
	return out
end

function Effects.playSerialized(msg: any)
	if type(msg) ~= "table" or type(msg.id) ~= "string" then
		return inert("invalid", 0)
	end
	local params = table.clone(msg)
	params.id = nil
	return Effects.play(msg.id, params)
end

function Effects.exists(effectId: string): boolean
	return Catalogue.has(effectId)
end

function Effects.ids(): { string }
	return Catalogue.ids()
end

--- Runtime stats: live effects, budget usage, tier, pool sizes, refused/culled counts.
function Effects.stats()
	local R = runtime()
	local b = R.budget()
	return {
		active = R.activeCount(),
		cooling = R.coolingCount(),
		tier = b and b.tier,
		usage = b and table.clone(b.usage),
		effects = b and b.effects,
		started = R.stats.started,
		refused = R.stats.refused,
		culled = R.stats.culled,
		pools = R.poolStats(),
	}
end

--- Advance the scheduler manually (tests, or games that drive effects from their own loop).
function Effects.step(dt: number)
	runtime().step(dt)
end

--- Stop and release everything immediately.
function Effects.clear()
	runtime().clearAll()
	table.clear(statusByTarget)
end

return Effects
