--!strict
-- Motion: pure procedural animation math for summons (unit-tested under Lune; Animator applies it in Roblox).
--
--   Motion.ease.*                easing curves (t in 0..1)
--   Motion.anticipate(t, a, o)   wind-up -> strike -> overshoot -> settle envelope (0..1 -> -a..1+o..1)
--   Motion.spring(x, v, target, k, damp, dt) -> (x, v)   critically-dampable spring step
--   Motion.clipLength[clip]      seconds (Idle/Move loop; Attack/Hit/Spawn/Die one-shot)
--   Motion.pose(rig, clip, t, o) -> { [bone] = {px,py,pz, rx,ry,rz} }   per-bone offsets (model-axis Euler)
--
-- Gaits (rig.gait): trot, heavy, sprawl, biped, stomp, hop, waddle, bird, buzz, scuttle, swim, float, slither,
-- inch, drive, fly, hover, spin, sway, swarm, surge, static, roll. Material motion (rig.materialMotion) layers on
-- top: wobble (jelly), flop (spaghetti/rope lag), clank (metal: stepped + impact shake), bob, jiggle, swarm,
-- flicker. Mood tweaks speed and posture (Sleepy droops and slows, Hyper doubles, Scared trembles).

local Motion = {}

local sin, cos, pi, abs = math.sin, math.cos, math.pi, math.abs
local TAU = pi * 2

Motion.ease = {
	linear = function(t: number): number
		return t
	end,
	inQuad = function(t: number): number
		return t * t
	end,
	outQuad = function(t: number): number
		return 1 - (1 - t) * (1 - t)
	end,
	inOutSine = function(t: number): number
		return -(cos(pi * t) - 1) / 2
	end,
	outBack = function(t: number): number
		local c1 = 1.70158
		local c3 = c1 + 1
		return 1 + c3 * (t - 1) ^ 3 + c1 * (t - 1) ^ 2
	end,
	outElastic = function(t: number): number
		if t <= 0 then
			return 0
		elseif t >= 1 then
			return 1
		end
		return 2 ^ (-10 * t) * sin((t * 10 - 0.75) * (TAU / 3)) + 1
	end,
}

-- Anticipation envelope: 0 -> dip to -a by 30%, snap to 1+o by 55%, settle to 1 at 100%.
function Motion.anticipate(t: number, a: number?, o: number?): number
	local A, O = a or 0.25, o or 0.15
	t = math.clamp(t, 0, 1)
	if t < 0.3 then
		return -A * Motion.ease.inOutSine(t / 0.3)
	elseif t < 0.55 then
		local u = (t - 0.3) / 0.25
		return -A + (1 + O + A) * Motion.ease.outQuad(u)
	end
	local u = (t - 0.55) / 0.45
	return 1 + O * (1 - Motion.ease.inOutSine(u))
end

-- Strike envelope for one-shot attacks: anticipation then return to rest (0 at both ends).
function Motion.strike(t: number): number
	t = math.clamp(t, 0, 1)
	if t < 0.7 then
		return Motion.anticipate(t / 0.7, 0.3, 0.2)
	end
	return 1 - Motion.ease.inOutSine((t - 0.7) / 0.3)
end

function Motion.spring(x: number, v: number, target: number, k: number, damp: number, dt: number): (number, number)
	local a = -k * (x - target) - damp * v
	v += a * dt
	x += v * dt
	return x, v
end

Motion.clipLength = { Idle = 2.4, Move = 1.0, Attack = 0.7, Hit = 0.35, Die = 1.2, Spawn = 0.6 }
Motion.looping = { Idle = true, Move = true }

local MOOD_SPEED: { [string]: number } = { Sleepy = 0.55, Lazy = 0.7, Hyper = 1.8, Crazy = 1.4, Scared = 1.3, Angry = 1.2, Sad = 0.8 }
function Motion.moodSpeed(mood: string?): number
	return MOOD_SPEED[mood or "Neutral"] or 1
end

-- Gait parameters: stride (rad of hip swing), bob (studs per unit height), freq (cycles/sec at speed 1).
local GAIT: { [string]: any } = {
	trot = { stride = 0.55, bob = 0.04, freq = 1.6 }, heavy = { stride = 0.32, bob = 0.06, freq = 0.9, roll = 0.05 },
	sprawl = { stride = 0.45, bob = 0.02, freq = 1.2, yaw = 0.12 }, biped = { stride = 0.5, bob = 0.04, freq = 1.3 },
	stomp = { stride = 0.4, bob = 0.07, freq = 1.0, roll = 0.06 }, hop = { stride = 0.25, bob = 0.25, freq = 1.4, hop = true },
	waddle = { stride = 0.25, bob = 0.03, freq = 1.8, roll = 0.16 }, bird = { stride = 0.4, bob = 0.03, freq = 1.8 },
	buzz = { flap = 1.0, flapFreq = 14, bob = 0.05, freq = 2.5, fly = true }, scuttle = { stride = 0.35, bob = 0.01, freq = 3.0 },
	swim = { sway = 0.25, freq = 1.0, fly = true }, float = { bob = 0.08, freq = 0.5, fly = true }, slither = { sway = 0.35, freq = 1.0 },
	inch = { bob = 0.06, freq = 0.8, sway = 0.1 }, drive = { wheel = 1, bob = 0.01, freq = 2 }, fly = { flap = 0.7, flapFreq = 2.2, bob = 0.1, freq = 1, fly = true },
	hover = { bob = 0.08, freq = 0.6, fly = true }, spin = { spin = 2, freq = 1 }, sway = { sway = 0.08, freq = 0.4 },
	swarm = { jitter = 0.06, freq = 3 }, surge = { bob = 0.12, freq = 0.7 }, static = { freq = 0 }, roll = { roll2 = 1, freq = 1 },
}
Motion.Gaits = GAIT

local function add(out: any, bone: string?, px: number, py: number, pz: number, rx: number, ry: number, rz: number)
	if bone == nil then
		return
	end
	local o = out[bone]
	if o == nil then
		o = { 0, 0, 0, 0, 0, 0 }
		out[bone] = o
	end
	o[1] += px
	o[2] += py
	o[3] += pz
	o[4] += rx
	o[5] += ry
	o[6] += rz
end

-- Keyframed clips of hero models (Heroes/, authored in tools/meshgen/heroes/motion.py): c = { len, loop, keys,
-- tracks = { [bone] = { 6 numbers per key } } }. Catmull-Rom between keys, cyclic for loops.
function Motion.sampleClip(c: any, t: number, out: { [string]: { number } }, w: number?, ps: number?)
	local n, L = c.keys, c.len
	local weight = w or 1
	local pscale = ps or 1
	local i0, f
	local i1, i2, i3, im
	if c.loop then
		local u = ((t % L) / L) * n
		i0 = math.floor(u)
		f = u - i0
		i0 %= n
		im, i1, i2, i3 = (i0 - 1) % n, i0, (i0 + 1) % n, (i0 + 2) % n
	else
		local u = math.clamp(t / L, 0, 1) * (n - 1)
		i0 = math.min(math.floor(u), n - 2)
		f = u - i0
		im, i1, i2, i3 = math.max(i0 - 1, 0), i0, i0 + 1, math.min(i0 + 2, n - 1)
	end
	local f2, f3 = f * f, f * f * f
	for bone, tr in c.tracks do
		local o = out[bone]
		if o == nil then
			o = { 0, 0, 0, 0, 0, 0 }
			out[bone] = o
		end
		local a, b, cc, d = im * 6, i1 * 6, i2 * 6, i3 * 6
		for k = 1, 6 do
			local p0, p1, p2, p3 = tr[a + k], tr[b + k], tr[cc + k], tr[d + k]
			o[k] += (if k <= 3 then weight * pscale else weight) * 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f2 + (-p0 + 3 * p1 - 3 * p2 + p3) * f3)
		end
	end
end

-- Hero rigs: the authored loop (Idle / Move) underneath, an authored one-shot (Attack / Hit) on top when the hero has
-- one, else the procedural one-shot layer; material motion and mood posture as for generated rigs.
local function heroPose(rig: any, clip: string, t: number, oo: any): { [string]: { number } }
	local out: { [string]: { number } } = {}
	local spd = Motion.moodSpeed(oo.mood)
	local clips = rig.clips
	local looping = Motion.looping[clip] == true
	if looping then
		local c = clips[clip] or clips.Idle
		if c then
			Motion.sampleClip(c, t * spd, out, 1, rig.clipScale)
		end
	else
		local c = clips[clip]
		if c then
			Motion.sampleClip(c, t, out, 1, rig.clipScale)
		else
			if clips.Idle then
				Motion.sampleClip(clips.Idle, t, out, 1, rig.clipScale)
			end
			local proc = Motion.pose({ gait = "static", head = rig.head, legs = rig.legs, arms = rig.arms, jaw = rig.jaw }, clip, t, oo)
			for bone, v in proc do
				local o = out[bone]
				if o == nil then
					out[bone] = v
				else
					for k = 1, 6 do
						o[k] += v[k]
					end
				end
			end
		end
	end
	if rig.materialMotion then
		local proc = Motion.pose({ gait = "static", materialMotion = rig.materialMotion }, "Idle", t, { height = oo.height, seed = oo.seed })
		local body = proc.Body
		if body then
			local o = out.Body or { 0, 0, 0, 0, 0, 0 }
			out.Body = o
			for k = 1, 6 do
				o[k] += body[k]
			end
		end
	end
	if (oo.mood == "Sleepy" or oo.mood == "Sad" or oo.mood == "Lazy") and rig.head then
		local o = out[rig.head] or { 0, 0, 0, 0, 0, 0 }
		out[rig.head] = o
		o[4] -= 0.22
	end
	return out
end

-- rig: blueprint rig; clip: Idle|Move|Attack|Hit|Die|Spawn; t: seconds into the clip.
-- o: { height = studs, speed = multiplier, mood = string, seed = number }
function Motion.pose(rig: any, clip: string, t: number, o: any?): { [string]: { number } }
	local oo = o or {}
	if rig.clips then
		return heroPose(rig, clip, t, oo)
	end
	local out: { [string]: { number } } = {}
	local g = GAIT[rig.gait or "static"] or GAIT.static
	local h = oo.height or 5
	local spd = (oo.speed or 1) * Motion.moodSpeed(oo.mood)
	local moving = clip == "Move"
	local amp = if moving then 1 else 0.18 -- idle = small "alive" motion in the same rhythm
	local f = (g.freq or 1) * (if moving then 1 else 0.45) * spd
	local ph = t * f * TAU
	local seed = oo.seed or 0

	-- body bob / roll / yaw
	local bob = (g.bob or 0) * h
	if g.hop and moving then
		add(out, "Body", 0, abs(sin(ph * 0.5)) * bob * 1.6, 0, -sin(ph) * 0.12, 0, 0)
	else
		add(out, "Body", 0, sin(ph * 2) * bob * amp + (if g.fly then sin(t * 1.3 + seed) * h * 0.04 else 0), 0, 0, sin(ph) * (g.yaw or 0) * amp, sin(ph) * (g.roll or 0) * (if moving then 1 else 0.3))
	end
	if g.spin then
		add(out, "Body", 0, 0, 0, 0, t * g.spin * spd, 0)
	end
	if not moving then
		-- breathing
		add(out, "Body", 0, sin(t * 1.8) * h * 0.006, 0, sin(t * 1.8) * 0.015, 0, 0)
	end

	-- legs
	for _, l in rig.legs or {} do
		local p = ph + (l.phase or 0) * TAU
		local swing = sin(p) * (g.stride or 0.3) * amp
		add(out, l.hip, 0, 0, 0, swing, 0, 0)
		if l.knee then
			add(out, l.knee, 0, 0, 0, math.max(0, -cos(p)) * 0.5 * amp, 0, 0)
		end
	end
	-- arms swing opposite to the legs
	for _, a in rig.arms or {} do
		local side = a.side or 1
		add(out, a.arm, 0, 0, 0, -sin(ph) * 0.35 * amp * side, 0, side * 0.04 * sin(t * 1.8))
		if a.fore then
			add(out, a.fore, 0, 0, 0, -0.15 - math.max(0, sin(ph)) * 0.2 * amp, 0, 0)
		end
	end
	-- wings
	for _, w in rig.wings or {} do
		local side = w.side or 1
		local flapF = (g.flapFreq or 1.2) * spd
		local flap = (g.flap or 0.25) * (if moving or g.fly then 1 else 0.25)
		add(out, w.bone, 0, 0, 0, 0, 0, side * sin(t * flapF * TAU) * flap * (if w.flipper then 0.5 elseif w.folded then 0.35 else 1))
	end
	-- tail: lagged sway down the chain
	for i, b in rig.tail or {} do
		local lag = i * 0.6
		add(out, if type(b) == "table" then b.bone else b, 0, 0, 0, sin(ph - lag) * 0.06, sin(ph * 0.5 - lag) * (0.18 + (g.sway or 0)) * (0.5 + amp * 0.5), 0)
	end
	for i, b in rig.spine or {} do
		add(out, b, 0, 0, 0, 0, sin(ph - i * 0.7) * (g.sway or 0.1), 0)
	end
	for _, tt in rig.tentacles or {} do
		local p = t * 1.2 * spd + (tt.index or 0) * 0.8 + (tt.seg or 1) * 0.5
		add(out, tt.bone, 0, 0, 0, sin(p) * 0.22, 0, cos(p * 0.8) * 0.18)
	end
	for _, b in rig.sway or {} do
		add(out, if type(b) == "table" then b.bone else b, 0, 0, 0, sin(t * 0.9) * 0.04, 0, sin(t * 0.7) * 0.06)
	end
	-- wheels / rotors / orbiting units
	for _, w in rig.wheels or {} do
		local r = math.max(w.r or 0.5, 0.05)
		add(out, w.bone, 0, 0, 0, -(if moving then t * 6 * spd / r else 0), 0, 0)
	end
	for _, r in rig.rotors or {} do
		local a = t * (r.speed or 10) * spd
		add(out, r.bone, 0, 0, 0, if r.axis == "X" then a else 0, if r.axis == "Y" then a else 0, if r.axis == "Z" then a else 0)
	end
	for _, u in rig.units or {} do
		local i = u.index or 1
		local j = (g.jitter or 0.04) * h
		add(out, u.bone, sin(t * 5.1 + i * 1.7) * j, sin(t * 6.3 + i * 2.3) * j, cos(t * 4.7 + i) * j, 0, 0, 0)
	end
	-- head: look around while idle, steady while moving
	if rig.head then
		add(out, rig.head, 0, 0, 0, sin(t * 0.7 + seed) * 0.06, sin(t * 0.45 + seed) * (if moving then 0.04 else 0.22), 0)
	end
	if rig.tailWag then
		for i, b in rig.tail or {} do
			add(out, if type(b) == "table" then b.bone else b, 0, 0, 0, 0, sin(t * 12) * 0.35 / i, 0)
		end
	end

	-- material motion overlay
	local mm = rig.materialMotion
	if mm == "wobble" then
		local k = 0.05 * (if moving then 1.6 else 1)
		add(out, "Body", 0, sin(t * 7) * h * 0.01, 0, sin(t * 7) * k, 0, sin(t * 5.3) * k)
		for i, l in rig.legs or {} do
			add(out, l.hip, 0, 0, 0, sin(t * 7 - i) * k, 0, 0)
		end
		if rig.head then
			add(out, rig.head, 0, 0, 0, sin(t * 7 - 1.2) * k * 1.4, 0, sin(t * 6 - 1) * k)
		end
	elseif mm == "flop" then
		-- floppy: every limb and tail lags and droops like wet noodles
		for i, l in rig.legs or {} do
			add(out, l.hip, 0, 0, 0, sin(ph - 1.1) * 0.12, 0, (l.side or 0) * (0.1 + sin(t * 2 + i) * 0.05))
		end
		for _, a in rig.arms or {} do
			add(out, a.arm, 0, 0, 0, 0.15 + sin(t * 2.2) * 0.1, 0, (a.side or 1) * -0.18)
		end
		for i, b in rig.tail or {} do
			add(out, if type(b) == "table" then b.bone else b, 0, 0, 0, 0.12 * i, sin(t * 1.5 - i) * 0.2, 0)
		end
		if rig.head then
			add(out, rig.head, 0, 0, 0, 0.1 + sin(t * 1.3) * 0.08, 0, sin(t * 1.1) * 0.1)
		end
	elseif mm == "clank" then
		-- metal: motion snaps in steps and each footfall shakes the frame
		for _, v in out do
			for i = 4, 6 do
				v[i] = math.floor(v[i] / 0.06 + 0.5) * 0.06
			end
		end
		if moving then
			local impact = math.max(0, cos(ph * 2)) ^ 8
			add(out, "Body", 0, -impact * h * 0.015, 0, 0, 0, sin(t * 60) * impact * 0.02)
		end
	elseif mm == "bob" then
		add(out, "Body", 0, sin(t * 1.4) * h * 0.04, 0, 0, 0, sin(t * 0.9) * 0.05)
	elseif mm == "jiggle" then
		add(out, "Body", 0, abs(sin(t * 9)) * h * 0.008, 0, 0, 0, sin(t * 9) * 0.015)
	elseif mm == "swarm" then
		add(out, "Body", sin(t * 7.1) * h * 0.01, sin(t * 8.3) * h * 0.01, cos(t * 6.7) * h * 0.01, 0, 0, 0)
	elseif mm == "flicker" then
		local n = sin(t * 37.1 + seed) * sin(t * 23.3)
		add(out, "Body", n * h * 0.006, 0, 0, 0, n * 0.03, 0)
	end

	-- mood posture
	if oo.mood == "Sleepy" or oo.mood == "Sad" or oo.mood == "Lazy" then
		if rig.head then
			add(out, rig.head, 0, 0, 0, 0.22, 0, 0)
		end
		add(out, "Body", 0, -h * 0.01, 0, 0.03, 0, 0)
	elseif oo.mood == "Scared" then
		add(out, "Body", sin(t * 40) * h * 0.003, -h * 0.02, 0, -0.05, 0, 0)
	elseif oo.mood == "Angry" and rig.head then
		add(out, rig.head, 0, 0, 0, 0.1, 0, 0)
	elseif oo.mood == "Confused" and rig.head then
		add(out, rig.head, 0, 0, 0, 0, 0, 0.25)
	end

	-- one-shot clips (layered over the idle rhythm)
	local L = Motion.clipLength[clip]
	if clip == "Attack" then
		local s = Motion.strike(t / L)
		add(out, "Body", 0, 0, -s * h * 0.08, -s * 0.12, 0, 0)
		if rig.head then
			add(out, rig.head, 0, 0, 0, -s * 0.35, 0, 0)
		end
		for _, a in rig.arms or {} do
			add(out, a.arm, 0, 0, 0, -s * 1.5, 0, 0)
		end
		if rig.jaw then
			add(out, rig.jaw, 0, 0, 0, s * 0.5, 0, 0)
		end
		for i, b in rig.tail or {} do
			add(out, if type(b) == "table" then b.bone else b, 0, 0, 0, 0, s * 0.3 * (if i % 2 == 0 then -1 else 1), 0)
		end
	elseif clip == "Hit" then
		local u = t / L
		local s = sin(math.min(u, 1) * pi) * (1 - u * 0.3)
		add(out, "Body", 0, 0, s * h * 0.05, s * 0.18, 0, sin(t * 50) * s * 0.06)
		if rig.head then
			add(out, rig.head, 0, 0, 0, s * 0.25, 0, 0)
		end
	elseif clip == "Die" then
		local u = Motion.ease.inQuad(math.clamp(t / L, 0, 1))
		add(out, "Body", 0, -u * h * 0.35, 0, 0, 0, u * pi * 0.48)
		for _, l in rig.legs or {} do
			add(out, l.hip, 0, 0, 0, u * 0.6 * (l.side or 1), 0, 0)
		end
	elseif clip == "Spawn" then
		-- rise from below with an overshoot pop
		local u = math.clamp(t / L, 0, 1)
		local e = Motion.ease.outBack(u)
		add(out, "Body", 0, (e - 1) * h * 0.6, 0, 0, (1 - u) * pi * 0.5, 0)
	end
	return out
end

return Motion
