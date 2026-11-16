--!nonstrict
-- Shared building blocks for renderers: debris simulation, crystals, rocks, element impact ids.

local Curves = require(script.Parent.Parent.Curves)

local Common = {}

local GRAVITY = -70 -- studs/s^2 for visual debris (snappier than workspace gravity, reads better)

function Common.impactId(element: string?): string
	return "impact." .. string.lower(element or "none")
end

--- A crystal / gem: Block turned 45 degrees around its long (Y) axis so it reads as a diamond prism.
function Common.crystal(fx, size: Vector3, cf: CFrame, opts)
	return fx:part("Block", size, cf * CFrame.Angles(0, math.pi / 4, 0), opts)
end

--- An irregular rock chunk: Block with a random rotation (rotation hides the box silhouette).
function Common.rock(fx, size: number, cf: CFrame, opts)
	local s = Vector3.new(size * fx:rand(0.8, 1.25), size * fx:rand(0.6, 1), size * fx:rand(0.8, 1.2))
	return fx:part("Block", s, cf * CFrame.Angles(fx:rand(0, 6.28), fx:rand(0, 6.28), fx:rand(0, 6.28)), opts)
end

--- Spawns `count` debris chunks flying out of `origin` and simulates them (ballistic + tumble + ground bounce).
--- opts: speed {min,max}, up {min,max}, size {min,max}, life, material role, colours {ramp idx...}, groundY,
---       shape ("Block"|"Ball"|"Crystal"), spread (0..1 horizontal bias), transparency
function Common.debris(fx, origin: Vector3, count: number, opts)
	opts = opts or {}
	if count <= 0 then
		return
	end
	local s = fx.scale
	local life = opts.life or 1.4
	local groundY = opts.groundY or (origin.Y - 0.5)
	local list = {}
	local colours = opts.colours or { 3, 4, 5 }
	for _ = 1, count do
		local size = fx:rand((opts.size or { 0.35, 0.9 })[1], (opts.size or { 0.35, 0.9 })[2]) * s
		local ang = fx:rand(0, math.pi * 2)
		local hs = fx:rand((opts.speed or { 10, 24 })[1], (opts.speed or { 10, 24 })[2]) * s
		local vs = fx:rand((opts.up or { 12, 30 })[1], (opts.up or { 12, 30 })[2]) * s
		local vel = Vector3.new(math.cos(ang) * hs, vs, math.sin(ang) * hs)
		local cf = CFrame.new(origin)
		local p
		local popts = {
			colour = colours[math.floor(fx:rand(1, #colours + 0.999))],
			material = opts.material or "debris",
			transparency = opts.transparency or fx:alphaFor("body"),
		}
		if opts.shape == "Crystal" then
			p = Common.crystal(fx, Vector3.new(size * 0.6, size * 1.6, size * 0.6), cf, popts)
		elseif opts.shape == "Ball" then
			p = fx:part("Ball", Vector3.one * size, cf, popts)
		else
			p = Common.rock(fx, size, cf, popts)
		end
		table.insert(list, {
			part = p,
			pos = origin,
			vel = vel,
			rot = p.CFrame.Rotation,
			spin = Vector3.new(fx:rand(-8, 8), fx:rand(-8, 8), fx:rand(-8, 8)),
			half = size / 2,
			base = popts.transparency,
			resting = false,
		})
	end
	local start = fx.t
	fx:onUpdate(function(_, t, dt)
		local age = t - start
		local fade = Curves.remap(age, life * 0.65, life, 0, 1)
		for _, d in list do
			if not d.resting then
				d.vel += Vector3.new(0, GRAVITY * s, 0) * dt
				d.pos += d.vel * dt
				if d.pos.Y - d.half < groundY then
					d.pos = Vector3.new(d.pos.X, groundY + d.half, d.pos.Z)
					if math.abs(d.vel.Y) < 6 * s then
						d.resting = true
					else
						d.vel = Vector3.new(d.vel.X * 0.45, -d.vel.Y * 0.3, d.vel.Z * 0.45)
						d.spin *= 0.5
					end
				end
				d.rot = d.rot * CFrame.Angles(d.spin.X * dt, d.spin.Y * dt, d.spin.Z * dt)
			end
			d.part.CFrame = CFrame.new(d.pos) * d.rot
			d.part.Transparency = d.base + (1 - d.base) * math.max(fade, 1 - fx.fade)
		end
	end)
end

--- Rise a part from below ground to its final CFrame with overshoot, starting at `delay`, taking `dur`.
--- Returns a function sink(progress 0..1) to push it back down.
function Common.riser(fx, part: BasePart, final: CFrame, depth: number, delay: number, dur: number)
	local below = final * CFrame.new(0, -depth, 0)
	part.CFrame = below
	local start = fx.t + delay
	local sinkFrom = nil
	fx:onUpdate(function(_, t)
		if fx.stopping then
			sinkFrom = sinkFrom or part.CFrame
			local k = Curves.inQuad(1 - fx.fade)
			part.CFrame = sinkFrom:Lerp(below, k)
			return
		end
		if t < start then
			return
		end
		local k = Curves.outBack((t - start) / dur, 1.4)
		part.CFrame = below:Lerp(final, k)
	end)
end

--- Points of a quadratic Bezier.
function Common.bezier(p0: Vector3, p1: Vector3, p2: Vector3, t: number): Vector3
	local u = 1 - t
	return p0 * (u * u) + p1 * (2 * u * t) + p2 * (t * t)
end

--- A CFrame at pos looking along dir (safe for vertical dirs).
function Common.look(pos: Vector3, dir: Vector3): CFrame
	if dir.Magnitude < 1e-4 then
		return CFrame.new(pos)
	end
	local d = dir.Unit
	local up = if math.abs(d.Y) > 0.98 then Vector3.xAxis else Vector3.yAxis
	return CFrame.lookAt(pos, pos + d, up)
end

--- Lightning: re-randomises a set of textured beams between two points every `interval` seconds.
--- Returns { setEnds(p0, p1), beams }.
function Common.lightning(fx, p0: Vector3, p1: Vector3, opts)
	opts = opts or {}
	local width = opts.width or 0.9
	local beams = {}
	local layers = opts.layers or 2
	for i = 1, layers do
		local core = i == 1
		table.insert(beams, fx:beam(p0, p1, {
			width0 = if core then width else width * 2.6,
			width1 = if core then width * 0.8 else width * 2.2,
			colour = if core then { fx.rampHex[1], fx.rampHex[2] } else { fx.rampHex[2], fx.rampHex[3], fx.rampHex[4] },
			transparency = if core then { { 0, 0 }, { 1, 0.05 } } else { { 0, 0.55 }, { 1, 0.65 } },
			tex = if core then "beam_lightning" else nil,
			texLength = (p1 - p0).Magnitude / fx:rand(1.5, 3),
			segments = 12,
			brightness = if core then 3 else 2,
			zoffset = (i - 1) * 0.02,
			lightEmission = 1,
			lightInfluence = 0,
		}))
	end
	local ends = { p0, p1 }
	local function jitter()
		local len = (ends[2] - ends[1]).Magnitude
		for i, w in beams do
			local amp = len * 0.12 * (if i == 1 then 1 else 0.6)
			w.beam.CurveSize0 = fx:rand(-amp, amp)
			w.beam.CurveSize1 = fx:rand(-amp, amp)
			w.beam.TextureSpeed = fx:rand(-1, 1) * 0.0001 -- frozen texture; offset changes via length
			w.beam.TextureLength = len / fx:rand(1.2, 3.2)
		end
	end
	local function orient()
		-- attachments' X axes point sideways so CurveSize bends the bolt perpendicular to it
		local dir = ends[2] - ends[1]
		local side = if dir.Magnitude > 1e-3 then dir.Unit:Cross(Vector3.yAxis) else Vector3.xAxis
		if side.Magnitude < 1e-3 then
			side = Vector3.xAxis
		end
		side = side.Unit
		local up = dir.Unit:Cross(side)
		for _, w in beams do
			w:set(CFrame.fromMatrix(ends[1], side, up), CFrame.fromMatrix(ends[2], side, up))
		end
	end
	orient()
	jitter()
	fx:every(opts.interval or 0.05, jitter)
	return {
		beams = beams,
		setEnds = function(a: Vector3, b: Vector3)
			ends[1], ends[2] = a, b
			orient()
		end,
	}
end

--- Gather all BaseParts of a target (for LocalTransparencyModifier fades).
function Common.partsOf(target): { BasePart }
	local out = {}
	if typeof(target) ~= "Instance" then
		return out
	end
	if target:IsA("BasePart") then
		table.insert(out, target)
	end
	for _, d in target:GetDescendants() do
		if d:IsA("BasePart") then
			table.insert(out, d)
		end
	end
	return out
end

return Common
