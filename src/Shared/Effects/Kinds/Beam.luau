--!nonstrict
-- Beams: ray, lightning, chain, drain, tether, rainbow, prism, aurora. Layered Beam instances get distinct
-- ZOffsets so overlapping ribbons never fight for depth.

local Curves = require(script.Parent.Parent.Curves)
local Palettes = require(script.Parent.Parent.Palettes)
local Common = require(script.Parent.Common)

local RAINBOW = { "#FF4A4A", "#FF9F3A", "#FFE84A", "#5BE36B", "#4AB8FF", "#9A6BFF" }

local V = {}

function V.ray(fx)
	local s = fx.scale
	local layers = {
		{ w = 0.55, col = { fx.rampHex[1], fx.rampHex[1] }, tr = { { 0, 0 }, { 1, 0 } }, tex = "beam_energy", speed = 6, z = 0 },
		{ w = 1.5, col = { fx.rampHex[2], fx.rampHex[3] }, tr = { { 0, 0.25 }, { 1, 0.35 } }, tex = "beam_energy", speed = -3, z = 0.01 },
		{ w = 3.2, col = { fx.rampHex[3], fx.rampHex[4] }, tr = { { 0, 0.7 }, { 1, 0.75 } }, z = 0.02 },
	}
	local beams = {}
	for i, l in layers do
		if i < 3 or fx.detail >= 2 then
			table.insert(beams, { fx:beam(fx:from(), fx:to(), { width0 = l.w, colour = l.col, transparency = l.tr, tex = l.tex, texSpeed = l.speed, texLength = 6, zoffset = l.z, brightness = 2 }), l.w })
		end
	end
	local muzzle = fx:emitter("coreGlow", CFrame.new(fx:from()), { size = 0.7 })
	local hitGlow = fx:emitter("coreGlow", CFrame.new(fx:to()), { size = 1 })
	local hitSparks = fx:emitter(Palettes.elementFx(fx.element).burst, CFrame.new(fx:to()), { rate = 30 })
	local light = fx:light(CFrame.new(fx:to()), fx:c(2), 3, 16)
	local dur = fx.duration or 1.2
	fx:onUpdate(function(_, t)
		local a, b = fx:from(), fx:to()
		local env = Curves.envelope(t, dur, 0.12, 0.25) * fx.fade
		for _, rec in beams do
			local w, base = rec[1], rec[2]
			w:set(a, b)
			local pulse = 1 + 0.1 * math.sin(t * 30)
			w.beam.Width0 = base * s * env * pulse
			w.beam.Width1 = base * s * env * pulse * 1.1
		end
		muzzle:moveTo(CFrame.new(a))
		hitGlow:moveTo(CFrame.new(b))
		hitSparks:moveTo(CFrame.lookAt(b, a))
		if light then
			light.Parent.WorldCFrame = CFrame.new(b)
			light.Brightness = 3 * env * Curves.flicker(t, fx.uid, 0.2)
		end
	end)
end

function V.lightning(fx)
	local a, b = fx:from(), fx:to()
	local bolt = Common.lightning(fx, a, b, { width = 0.8, layers = if fx.detail >= 2 then 2 else 1 })
	-- branches
	local branches = {}
	if fx.detail >= 2 then
		for _ = 1, 2 do
			local k = fx:rand(0.3, 0.7)
			local p = a:Lerp(b, k)
			local off = Vector3.new(fx:rand(-1, 1), fx:rand(-0.5, 0.5), fx:rand(-1, 1)) * (b - a).Magnitude * 0.25
			table.insert(branches, { Common.lightning(fx, p, p + off, { width = 0.4, layers = 1 }), k, off })
		end
	end
	fx:emitter("sparks", CFrame.new(b), { size = 0.8 }):emit(20)
	fx:emitter("flash", CFrame.new(b), { size = 0.5 }):emit(1)
	local light = fx:light(CFrame.new(b), fx:c(1), 6, 22)
	local dur = fx.duration or 0.45
	fx:onUpdate(function(_, t)
		local a2, b2 = fx:from(), fx:to()
		bolt.setEnds(a2, b2)
		for _, br in branches do
			local p = a2:Lerp(b2, br[2])
			br[1].setEnds(p, p + br[3])
		end
		-- strobe: lightning flickers on and off twice
		local on = (t < dur * 0.35) or (t > dur * 0.5 and t < dur * 0.85)
		for _, w in bolt.beams do
			w.beam.Enabled = on and not fx.stopping
		end
		for _, br in branches do
			for _, w in br[1].beams do
				w.beam.Enabled = on and not fx.stopping
			end
		end
		if light then
			light.Brightness = if on then 6 else 1
		end
	end)
end

local function Runtime_pos(v): Vector3
	if typeof(v) == "Vector3" then
		return v
	elseif typeof(v) == "CFrame" then
		return v.Position
	elseif typeof(v) == "Instance" then
		if v:IsA("Model") then
			return v:GetPivot().Position
		elseif v:IsA("BasePart") then
			return v.CFrame.Position
		end
	end
	return Vector3.zero
end

local function chainPoints(fx): { Vector3 }
	local p = fx.params
	local pts = {}
	if type(p.points) == "table" then
		for _, v in p.points do
			table.insert(pts, Runtime_pos(v))
		end
	elseif type(p.targets) == "table" then
		table.insert(pts, fx:from())
		for _, v in p.targets do
			table.insert(pts, Runtime_pos(v))
		end
	end
	if #pts < 2 then
		local c = fx:at().Position
		pts = { fx:from(), fx:to() }
		if (pts[1] - pts[2]).Magnitude < 0.5 then
			-- no endpoints given: arc around the centre to a few nearby points (visual-only chain)
			pts = { c }
			for i = 1, 3 do
				local ang = Curves.ring(i, 3, fx:rand(0, 1))
				table.insert(pts, c + Vector3.new(math.cos(ang) * 7, fx:rand(0, 2), math.sin(ang) * 7) * fx.scale)
			end
		end
	end
	return pts
end

function V.chain(fx)
	local pts = chainPoints(fx)
	local links = {}
	local maxLinks = ({ 3, 5, 8 })[fx.detail] or 5
	for i = 1, math.min(#pts - 1, maxLinks) do
		local a, b = pts[i], pts[i + 1]
		local link = Common.lightning(fx, a, b, { width = 0.6, layers = if fx.detail >= 3 then 2 else 1, interval = 0.06 })
		table.insert(links, { link, i })
		fx:after((i - 1) * 0.06, function()
			fx:emitter("sparks", CFrame.new(b), { size = 0.6 }):emit(12)
			fx:emitter("electric", CFrame.new(b), { area = Vector3.one * 2, rate = 0 }):emit(6)
		end)
	end
	local light = fx:light(CFrame.new(pts[1]), fx:c(1), 4, 18)
	fx:onUpdate(function(_, t)
		for _, rec in links do
			local on = t >= (rec[2] - 1) * 0.06 and not fx.stopping
			for _, w in rec[1].beams do
				w.beam.Enabled = on and (math.floor(t * 30) % 5 ~= 0)
			end
		end
		if light then
			light.Brightness = 4 * Curves.flicker(t, fx.uid, 0.5)
		end
	end)
end

function V.drain(fx)
	local s = fx.scale
	local w = fx:beam(fx:to(), fx:from(), {
		width0 = 1.2,
		width1 = 0.6,
		colour = { fx.rampHex[3], fx.rampHex[2], fx.rampHex[1] },
		transparency = { { 0, 0.3 }, { 1, 0.15 } },
		tex = "beam_energy",
		texSpeed = 4,
		texLength = 5,
		segments = 20,
	})
	local glow = fx:beam(fx:to(), fx:from(), { width0 = 2.6, width1 = 1.4, colour = { fx.rampHex[4], fx.rampHex[3] }, transparency = { { 0, 0.75 }, { 1, 0.7 } }, segments = 20, zoffset = 0.02 })
	local motes = {}
	for i = 1, ({ 2, 4, 6 })[fx.detail] or 4 do
		table.insert(motes, { fx:part("Ball", Vector3.one * 0.5 * s, CFrame.new(fx:to()), { colour = 1, material = "core", transparency = 0.1 }), (i - 1) / 6 })
	end
	fx:emitter(Palettes.elementFx(fx.element).secondary, CFrame.new(fx:to()), { rate = 14 })
	local dur = fx.duration or 2
	fx:onUpdate(function(_, t)
		local a, b = fx:to(), fx:from()
		local mid = (a + b) / 2 + Vector3.new(0, (a - b).Magnitude * 0.25, 0)
		local bend = math.sin(t * 3) * (a - b).Magnitude * 0.15
		local dir = b - a
		local side = if dir.Magnitude > 0.01 then dir.Unit:Cross(Vector3.yAxis) else Vector3.xAxis
		if side.Magnitude < 0.01 then
			side = Vector3.xAxis
		end
		local up = side.Unit:Cross(dir.Unit)
		local c0 = CFrame.fromMatrix(a, up, side.Unit)
		local c1 = CFrame.fromMatrix(b, up, side.Unit)
		w:set(c0, c1)
		glow:set(c0, c1)
		local env = Curves.envelope(t, dur, 0.2, 0.3) * fx.fade
		w.beam.CurveSize0 = (a - b).Magnitude * 0.3 + bend
		w.beam.CurveSize1 = -(a - b).Magnitude * 0.3 + bend
		glow.beam.CurveSize0 = w.beam.CurveSize0
		glow.beam.CurveSize1 = w.beam.CurveSize1
		w.beam.Width0, w.beam.Width1 = 1.2 * s * env, 0.6 * s * env
		glow.beam.Width0, glow.beam.Width1 = 2.6 * s * env, 1.4 * s * env
		for _, m in motes do
			local k = (t * 0.9 + m[2]) % 1
			m[1].CFrame = CFrame.new(Common.bezier(a, mid, b, Curves.inOutSine(k)))
			m[1].Transparency = 0.1 + 0.9 * math.max(1 - env, math.abs(k - 0.5) * 1.6 - 0.3)
		end
	end)
end

function V.tether(fx)
	local w = fx:beam(fx:from(), fx:to(), {
		width0 = 0.5,
		width1 = 0.5,
		colour = { fx.rampHex[2], fx.rampHex[3], fx.rampHex[2] },
		transparency = { { 0, 0.3 }, { 0.5, 0.15 }, { 1, 0.3 } },
		tex = "beam_energy",
		texSpeed = 1.5,
		segments = 16,
	})
	fx:onUpdate(function(_, t)
		w:set(fx:from(), fx:to())
		local len = (fx:to() - fx:from()).Magnitude
		w.beam.CurveSize0 = math.sin(t * 2.2) * len * 0.12
		w.beam.CurveSize1 = math.sin(t * 2.2 + 1.3) * len * 0.12
		w.beam.Width0 = 0.5 * fx.scale * fx.fade
		w.beam.Width1 = 0.5 * fx.scale * fx.fade
	end)
end

function V.rainbow(fx)
	local s = fx.scale
	local centre = fx:ground(fx:at().Position)
	local span = 22 * s
	local h = 16 * s
	local beams = {}
	for i, hex in RAINBOW do
		local r = span / 2 - (i - 1) * 0.85 * s
		local left = centre + Vector3.new(-r, 0.5, 0)
		local right = centre + Vector3.new(r, 0.5, 0)
		-- attachment X axes point up so CurveSize lifts the ribbon into an arch
		local c0 = CFrame.fromMatrix(left, Vector3.yAxis, Vector3.zAxis)
		local c1 = CFrame.fromMatrix(right, Vector3.yAxis, Vector3.zAxis)
		local w = fx:beam(c0, c1, {
			width0 = 0.9,
			width1 = 0.9,
			colour = { hex, hex },
			transparency = { { 0, 1 }, { 0.12, 0.35 }, { 0.5, 0.25 }, { 0.88, 0.35 }, { 1, 1 } },
			segments = 24,
			curve0 = h * (1 - (i - 1) * 0.06),
			curve1 = -h * (1 - (i - 1) * 0.06),
			zoffset = i * 0.01,
			lightEmission = if fx:spectral() then 1 else 0.7,
			faceCamera = true,
		})
		table.insert(beams, w)
	end
	fx:emitter("glitter", CFrame.new(centre + Vector3.new(0, h * 0.6, 0)), { area = Vector3.new(span, 2, 2), shape = "Box", rate = 10 })
	local dur = fx.duration or 5
	fx:onUpdate(function(_, t)
		local env = Curves.envelope(t, dur, 0.6, 1) * fx.fade
		for _, w in beams do
			w.beam.Width0 = 0.9 * s * env
			w.beam.Width1 = 0.9 * s * env
		end
	end)
end

function V.prism(fx)
	local s = fx.scale
	local centre = fx:ground(fx:at().Position) + Vector3.new(0, 5 * s, 0)
	local crystal = Common.crystal(fx, Vector3.new(1.6, 3, 1.6) * s, CFrame.new(centre), {
		colour = 1,
		material = if fx:spectral() then "core" else Enum.Material.Glass,
		transparency = if fx:spectral() then 0.2 else 0.3,
		reflectance = 0.2,
	})
	local incoming = fx:beam(centre + Vector3.new(0, 40 * s, 0), centre, { width0 = 1.4, width1 = 0.8, colour = { "#FFFFFF", "#FFFFFF" }, transparency = { { 0, 0.6 }, { 1, 0.1 } }, zoffset = 0 })
	local rays = {}
	for i, hex in RAINBOW do
		local ang = math.rad(-60 + (i - 1) * 24)
		local tip = centre + Vector3.new(math.sin(ang) * 18, -5, math.cos(ang) * 18) * s
		table.insert(rays, { fx:beam(centre, tip, { width0 = 0.3, width1 = 1.4, colour = { "#FFFFFF", hex }, transparency = { { 0, 0.1 }, { 1, 0.5 } }, zoffset = 0.01 * i }), ang })
	end
	fx:emitter("glints", crystal, { rate = 8 })
	fx:light(crystal, Color3.new(1, 1, 1), 3, 18)
	local dur = fx.duration or 2.5
	fx:onUpdate(function(_, t)
		local env = Curves.envelope(t, dur, 0.3, 0.5) * fx.fade
		crystal.CFrame = CFrame.new(centre + Vector3.new(0, math.sin(t * 2) * 0.3 * s, 0)) * CFrame.Angles(0, t * 1.5 + math.pi / 4, 0)
		incoming.beam.Width0 = 1.4 * s * env
		incoming.beam.Width1 = 0.8 * s * env
		for _, r in rays do
			local sweep = r[2] + math.sin(t * 1.2) * 0.25
			r[1]:set(centre, centre + Vector3.new(math.sin(sweep) * 18, -5, math.cos(sweep) * 18) * s)
			r[1].beam.Width0 = 0.3 * s * env
			r[1].beam.Width1 = 1.4 * s * env
		end
	end)
end

function V.aurora(fx)
	local s = fx.scale
	local centre = fx:ground(fx:at().Position) + Vector3.new(0, 26 * s, 0)
	local cols = { { "#7CFFB2", "#3CE3D0" }, { "#5BD8FF", "#9A7BFF" }, { "#B4FF8A", "#55E0FF" }, { "#E07BFF", "#7CFFB2" } }
	local bands = {}
	for i = 1, ({ 2, 3, 4 })[fx.detail] or 3 do
		local z = (i - 2.5) * 5 * s
		local a = centre + Vector3.new(-24 * s, (i % 2) * 2 * s, z)
		local b = centre + Vector3.new(24 * s, -(i % 2) * 2 * s, z)
		local w = fx:beam(a, b, {
			width0 = 9,
			width1 = 7,
			colour = cols[i],
			transparency = { { 0, 1 }, { 0.2, 0.55 }, { 0.5, 0.45 }, { 0.8, 0.55 }, { 1, 1 } },
			tex = "beam_energy",
			texSpeed = 0.6 + i * 0.2,
			texLength = 18,
			segments = 30,
			zoffset = i * 0.02,
			lightEmission = 1,
		})
		table.insert(bands, { w, i })
	end
	fx:emitter("motes", CFrame.new(centre - Vector3.new(0, 20 * s, 0)), { area = Vector3.new(30 * s, 2, 30 * s), shape = "Box", rate = 12, colour = { "#B4FFE0", "#9AD8FF" } })
	local dur = fx.duration or 6
	fx:onUpdate(function(_, t)
		local env = Curves.envelope(t, dur, 1.2, 1.5) * fx.fade
		for _, rec in bands do
			local w, i = rec[1], rec[2]
			w.beam.CurveSize0 = math.sin(t * 0.7 + i) * 8 * s
			w.beam.CurveSize1 = math.sin(t * 0.6 + i * 2) * 8 * s
			w.beam.Width0 = 9 * s * env
			w.beam.Width1 = 7 * s * env
		end
	end)
end

return function(fx)
	local f = V[fx.entry.variant or "ray"] or V.ray
	f(fx)
end
