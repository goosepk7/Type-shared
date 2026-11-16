--!strict
-- Timing curves for Effects. Pure number maths (no Roblox types) so every curve is unit-tested.
-- Convention: t is normalised 0..1 unless noted; outputs are 0..1 unless noted.

local Curves = {}

local PI, TAU = math.pi, 2 * math.pi

local function clamp01(t: number): number
	return if t < 0 then 0 elseif t > 1 then 1 else t
end
Curves.clamp01 = clamp01

function Curves.linear(t: number): number
	return clamp01(t)
end
function Curves.inQuad(t: number): number
	t = clamp01(t)
	return t * t
end
function Curves.outQuad(t: number): number
	t = clamp01(t)
	return 1 - (1 - t) * (1 - t)
end
function Curves.outCubic(t: number): number
	t = clamp01(t)
	return 1 - (1 - t) ^ 3
end
function Curves.inCubic(t: number): number
	t = clamp01(t)
	return t * t * t
end
function Curves.outQuint(t: number): number
	t = clamp01(t)
	return 1 - (1 - t) ^ 5
end
function Curves.outExpo(t: number): number
	t = clamp01(t)
	return if t >= 1 then 1 else 1 - 2 ^ (-10 * t)
end
function Curves.inOutSine(t: number): number
	t = clamp01(t)
	return -(math.cos(PI * t) - 1) / 2
end
function Curves.inOutCubic(t: number): number
	t = clamp01(t)
	return if t < 0.5 then 4 * t * t * t else 1 - (-2 * t + 2) ^ 3 / 2
end
--- Anticipation-free overshoot (pop-in). s ~ 1.7 classic.
function Curves.outBack(t: number, s: number?): number
	t = clamp01(t)
	local c1 = s or 1.70158
	local c3 = c1 + 1
	return 1 + c3 * (t - 1) ^ 3 + c1 * (t - 1) ^ 2
end
--- Springy settle (shields, walls rising).
function Curves.outElastic(t: number): number
	t = clamp01(t)
	if t == 0 or t == 1 then
		return t
	end
	return 2 ^ (-10 * t) * math.sin((t * 10 - 0.75) * (TAU / 3)) + 1
end

Curves.byName = {
	linear = Curves.linear,
	inQuad = Curves.inQuad,
	outQuad = Curves.outQuad,
	outCubic = Curves.outCubic,
	inCubic = Curves.inCubic,
	outQuint = Curves.outQuint,
	outExpo = Curves.outExpo,
	inOutSine = Curves.inOutSine,
	inOutCubic = Curves.inOutCubic,
	outBack = function(t: number): number
		return Curves.outBack(t)
	end,
	outElastic = Curves.outElastic,
}

--- Envelope for a lifetime: ramps 0->1 over fadeIn seconds, holds, 1->0 over the last fadeOut seconds.
--- `elapsed`/`duration` in seconds. Returns 0..1 (multiply with alpha/size).
function Curves.envelope(elapsed: number, duration: number, fadeIn: number, fadeOut: number): number
	if duration <= 0 then
		return 0
	end
	local a = if fadeIn > 0 then clamp01(elapsed / fadeIn) else 1
	local b = if fadeOut > 0 then clamp01((duration - elapsed) / fadeOut) else (if elapsed < duration then 1 else 0)
	return math.min(a, b)
end

--- Height of a parabolic arc at t (0 at both ends, `height` at t=0.5).
function Curves.arc(t: number, height: number): number
	t = clamp01(t)
	return 4 * height * t * (1 - t)
end

--- Derivative of arc() w.r.t. t (for orienting lobbed projectiles along their path).
function Curves.arcSlope(t: number, height: number): number
	return 4 * height * (1 - 2 * clamp01(t))
end

--- Expanding shockwave: radius 0->1 with a fast start, alpha 1->0 with a delayed fade.
function Curves.shockwave(t: number): (number, number)
	t = clamp01(t)
	return Curves.outQuint(t), 1 - Curves.inQuad(t)
end

--- Flash: very fast rise (first 8%), exponential decay. Good for light Brightness and core flashes.
function Curves.flash(t: number): number
	t = clamp01(t)
	if t < 0.08 then
		return t / 0.08
	end
	return math.exp(-(t - 0.08) * 6)
end

--- Smooth pulse 0..1 at `hz` (sin-based), phase in cycles.
function Curves.pulse(time: number, hz: number, phase: number?): number
	return 0.5 + 0.5 * math.sin((time * hz + (phase or 0)) * TAU)
end

--- Deterministic hash noise in [0,1) for an integer-ish input (no math.random: reproducible per seed).
function Curves.hash(n: number): number
	local x = math.sin(n * 12.9898 + 78.233) * 43758.5453
	return x - math.floor(x)
end

--- Smooth 1D value noise in [0,1] (flicker for fire lights, wobble for bolts).
function Curves.noise(x: number, seed: number?): number
	local s = (seed or 0) * 31.7
	local i = math.floor(x)
	local f = x - i
	local u = f * f * (3 - 2 * f)
	local a, b = Curves.hash(i + s), Curves.hash(i + 1 + s)
	return a + (b - a) * u
end

--- Flicker multiplier around 1 (e.g. 0.75..1.15) for fire/electric lights.
function Curves.flicker(time: number, seed: number?, amount: number?): number
	local amt = amount or 0.25
	local n = Curves.noise(time * 9, seed) * 0.65 + Curves.noise(time * 23, (seed or 0) + 7) * 0.35
	return 1 - amt + n * amt * 1.6
end

--- Remap from [a,b] to [c,d], clamped.
function Curves.remap(x: number, a: number, b: number, c: number, d: number): number
	if b == a then
		return d
	end
	return c + (d - c) * clamp01((x - a) / (b - a))
end

--- Golden-angle spiral distribution: point i of n inside a unit disc (even coverage, no clumping).
--- Returns x, z in -1..1.
function Curves.disc(i: number, n: number): (number, number)
	local golden = PI * (3 - math.sqrt(5))
	local r = math.sqrt((i - 0.5) / math.max(n, 1))
	local a = i * golden
	return math.cos(a) * r, math.sin(a) * r
end

--- Point i of n evenly around a circle (angle in radians), with optional phase.
function Curves.ring(i: number, n: number, phase: number?): number
	return (i - 1) / math.max(n, 1) * TAU + (phase or 0)
end

--- Tornado funnel radius at normalised height h (0 ground .. 1 top): narrow neck, flared top.
function Curves.funnel(h: number, base: number, top: number): number
	h = clamp01(h)
	return base + (top - base) * (h ^ 1.8)
end

--- Spiral-in for vortex debris: radius over normalised life (1 -> 0, accelerating).
function Curves.spiralIn(t: number): number
	return 1 - Curves.inCubic(t)
end

--- Ballistic position helper (1D): p0 + v*t + 0.5*g*t^2.
function Curves.ballistic(p0: number, v: number, g: number, t: number): number
	return p0 + v * t + 0.5 * g * t * t
end

return Curves
