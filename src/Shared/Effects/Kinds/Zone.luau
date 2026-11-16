--!nonstrict
-- Zones: tornado, vortex, sinkhole, blizzard, wildfire, pool, storm, sandstorm, garden, spores, runes, sanctum,
-- eclipse, starfall. Most loop until stopped; tornado/sandstorm wander toward params.to or handle:setTarget().

local Curves = require(script.Parent.Parent.Curves)
local Palettes = require(script.Parent.Parent.Palettes)
local Runtime = require(script.Parent.Parent.Runtime)
local Common = require(script.Parent.Common)

local Z = {}

-- Moving centre on the ground: drifts toward the target (handle:setTarget / params.to), else wanders slowly.
local function mover(fx, speed: number)
	local home = fx:ground(fx:at().Position)
	local pos = home
	local last = -1
	return function(t: number): Vector3
		local dt = if last < 0 then 0 else t - last
		last = t
		local target = Runtime.posOf(fx.target) or Runtime.posOf(fx.params.to)
		if target then
			local d = Vector3.new(target.X - pos.X, 0, target.Z - pos.Z)
			if d.Magnitude > 0.5 then
				pos += d.Unit * math.min(d.Magnitude, speed * dt)
			end
		elseif fx.params.wander ~= false then
			local wx = (Curves.noise(t * 0.3, fx.uid) - 0.5) * 2
			local wz = (Curves.noise(t * 0.3, fx.uid + 50) - 0.5) * 2
			pos = home + Vector3.new(wx, 0, wz) * 4 * fx.scale
		end
		return pos
	end
end

-- Debris kit per element for tornado/vortex.
local function debrisPart(fx, i: number, size: number)
	local e = fx.element
	local spectral = fx:spectral()
	if e == "Metal" then
		return fx:part("Block", Vector3.new(0.12, 0.5, 2.2) * size, CFrame.new(), { colour = 1, material = if spectral then "core" else Enum.Material.Metal, transparency = if spectral then 0.2 else 0, reflectance = 0.3 })
	elseif e == "Nature" then
		return fx:part("Ellipsoid", Vector3.new(0.9, 0.12, 0.6) * size, CFrame.new(), { colour = (i % 3) + 2, material = if spectral then "shell" else Enum.Material.LeafyGrass, transparency = if spectral then 0.3 else 0 })
	elseif e == "Fire" then
		return Common.rock(fx, 0.8 * size, CFrame.new(), { colour = if i % 2 == 0 then 2 else 4, material = if spectral then "core" else Enum.Material.CrackedLava, transparency = 0 })
	elseif e == "Water" then
		return fx:part("Ball", Vector3.one * 0.7 * size, CFrame.new(), { colour = 2, material = if spectral then "shell" else Enum.Material.Glass, transparency = 0.4 })
	end
	if spectral then
		return Common.rock(fx, 0.8 * size, CFrame.new(), { colour = (i % 3) + 2, material = "core", transparency = 0.25 })
	end
	-- Wind/Earth/Solid default: a mix of rocks and wooden planks, the classic "tornado debris"
	if i % 3 == 0 then
		return fx:part("Block", Vector3.new(0.3, 0.2, 2.4) * size, CFrame.new(), { colour = Color3.fromRGB(139, 101, 63), material = Enum.Material.WoodPlanks, transparency = 0 })
	end
	return Common.rock(fx, 0.8 * size, CFrame.new(), { colour = Color3.fromRGB(110 + i * 7 % 30, 100, 88), material = Enum.Material.Slate, transparency = 0 })
end

function Z.tornado(fx)
	local s = fx.scale
	local H = 30 * s
	local base, top = 1.6 * s, 10 * s
	local e = fx.element
	local efx = Palettes.elementFx(e)
	local move = mover(fx, 6 * s)
	local spectral = fx:spectral()

	-- 1) spinning funnel: helical beams from the narrow base to the wide top
	local beams = {}
	local nb = ({ 3, 4, 6 })[fx.detail] or 4
	local funnelCols = if spectral then { fx.rampHex[1], fx.rampHex[2], fx.rampHex[3] } elseif e == "Fire" then { fx.rampHex[2], fx.rampHex[3], fx.rampHex[5] } else { "#E6EBEF", "#B9C2CA", "#8D979F" }
	for i = 1, nb do
		local w = fx:beam(Vector3.zero, Vector3.new(0, H, 0), {
			width0 = 1.2,
			width1 = 7,
			colour = funnelCols,
			transparency = { { 0, 0.55 }, { 0.5, 0.45 }, { 1, 0.75 } },
			tex = "beam_energy",
			texSpeed = 3,
			texLength = 10,
			segments = 18,
			zoffset = i * 0.01,
			lightEmission = if spectral or e == "Fire" then 1 else 0.2,
			lightInfluence = if spectral or e == "Fire" then 0 else 0.8,
		})
		table.insert(beams, { w, Curves.ring(i, nb) })
	end

	-- 2) orbiting streak emitters at each funnel layer (attachments move around the funnel)
	local layers = {}
	local nl = ({ 3, 4, 6 })[fx.detail] or 4
	local layerPreset = if e == "Fire" then "fire" elseif e == "Water" then "splash" elseif e == "Nature" then "leaves" elseif e == "Shadow" then "wisps" else "windStreaks"
	for i = 1, nl do
		local h = (i - 0.5) / nl
		table.insert(layers, { fx:emitter(layerPreset, CFrame.new(), { rate = if layerPreset == "fire" then 16 else 10, size = 0.6 + h * 1.4, speed = 0.4 }), h, Curves.ring(i, nl) })
	end

	-- 3) debris visibly lifted up the funnel, orbiting, then flung out at the top
	local debris = {}
	local nd = ({ 4, 7, 10 })[fx.detail] or 7
	for i = 1, nd do
		local p = debrisPart(fx, i, s * fx:rand(0.7, 1.3))
		table.insert(debris, { part = p, phase = (i - 1) / nd, ang = fx:rand(0, 6.28), spin = Vector3.new(fx:rand(-6, 6), fx:rand(-6, 6), fx:rand(-6, 6)), rot = CFrame.Angles(fx:rand(0, 6), fx:rand(0, 6), 0), fling = nil })
	end

	-- 4) base: dust kicked outward + pebbles
	local dust = fx:emitter("dustRing", CFrame.new(), { area = Vector3.new(5 * s, 0.2, 5 * s), rate = 20, size = 1.1, colour = if e == "Fire" then { fx.rampHex[5], "#2A2522" } else nil })
	local pebbles = fx:emitter(efx.burst, CFrame.new(), { rate = 6 })
	local light = (e == "Fire" or spectral) and fx:light(CFrame.new(), fx:c(2), 3, 30) or nil
	local cycle = 2.6 -- seconds for debris to ride from ground to top

	fx.fadeOut = 0.8
	fx:onUpdate(function(_, t, dt)
		local c = move(t)
		local grow = Curves.outCubic(math.clamp(t / 0.8, 0, 1)) * (if fx.stopping then fx.fade else 1)
		local spin = t * 3.2
		for _, rec in beams do
			local w, a0 = rec[1], rec[2]
			local ang0 = a0 + spin
			local ang1 = ang0 + 2.2
			local p0 = c + Vector3.new(math.cos(ang0) * base, 0.2, math.sin(ang0) * base)
			local p1 = c + Vector3.new(math.cos(ang1) * top * grow, H * grow, math.sin(ang1) * top * grow)
			local outward0 = Vector3.new(math.cos(ang0), 0, math.sin(ang0))
			local outward1 = Vector3.new(math.cos(ang1), 0, math.sin(ang1))
			-- bow the ribbon outward around the funnel
			w:set(CFrame.fromMatrix(p0, outward0, Vector3.yAxis), CFrame.fromMatrix(p1, outward1, Vector3.yAxis))
			w.beam.CurveSize0 = 3 * s * grow
			w.beam.CurveSize1 = -2 * s * grow
			w.beam.Width0 = 1.2 * s * grow
			w.beam.Width1 = 7 * s * grow
		end
		for _, l in layers do
			local h = l[2]
			local r = Curves.funnel(h, base, top) * grow
			local ang = l[3] + t * (4 - h * 1.5)
			l[1]:moveTo(CFrame.new(c + Vector3.new(math.cos(ang) * r, H * h * grow, math.sin(ang) * r)) * CFrame.Angles(0, -ang, 0))
		end
		for _, d in debris do
			if d.fling then
				d.fling.vel += Vector3.new(0, -50 * s, 0) * dt
				d.fling.pos += d.fling.vel * dt
				d.rot = d.rot * CFrame.Angles(d.spin.X * dt, d.spin.Y * dt, d.spin.Z * dt)
				d.part.CFrame = CFrame.new(d.fling.pos) * d.rot
				if d.fling.pos.Y < c.Y - 2 or t - d.fling.start > 2 then
					d.fling = nil
					d.phase = 0
				end
			else
				d.phase += dt / cycle
				local h = Curves.inOutSine(math.min(d.phase, 1))
				local r = Curves.funnel(h, base * 2.2, top * 0.9) * grow
				d.ang += dt * (5 - h * 2.2)
				local pos = c + Vector3.new(math.cos(d.ang) * r, 0.5 + H * 0.92 * h * grow, math.sin(d.ang) * r)
				d.rot = d.rot * CFrame.Angles(d.spin.X * dt, d.spin.Y * dt, d.spin.Z * dt)
				d.part.CFrame = CFrame.new(pos) * d.rot
				if d.phase >= 1 and not fx.stopping then
					-- fling out tangentially at the top
					local tangent = Vector3.new(-math.sin(d.ang), 0.4, math.cos(d.ang))
					d.fling = { pos = pos, vel = tangent * 26 * s + Vector3.new(math.cos(d.ang), 0, math.sin(d.ang)) * 10 * s, start = t }
				end
			end
			d.part.Transparency = (1 - grow) + (if spectral then 0.2 else 0) * grow
		end
		dust:moveTo(CFrame.new(c + Vector3.new(0, 0.4, 0)))
		pebbles:moveTo(CFrame.new(c + Vector3.new(0, 1, 0)))
		if light then
			light.Parent.WorldCFrame = CFrame.new(c + Vector3.new(0, H * 0.4, 0))
			light.Brightness = 3 * Curves.flicker(t, fx.uid, 0.25) * grow
		end
	end)
end

function Z.vortex(fx)
	local s = fx.scale
	local e = fx.element
	local spectral = fx:spectral()
	local onGround = e == "Water"
	local magnetic = e == "Metal"
	local g = fx:ground(fx:at().Position)
	local c = if onGround then g + Vector3.new(0, 0.3, 0) else g + Vector3.new(0, 7 * s, 0)
	local R = (fx.params.radius or 11) * s
	fx.fadeOut = 0.8

	local core, horizon, disc
	if not magnetic then
		if onGround then
			core = fx:groundDisc(g, 2.4 * s, { noRaycast = true, colour = fx:c(5), material = Enum.Material.SmoothPlastic, transparency = 0.05, thickness = 0.06 })
			disc = fx:groundDisc(g, 1 * s, { noRaycast = true, colour = 3, material = if spectral then "shell" else Enum.Material.Glass, transparency = 0.45, thickness = 0.06 })
		else
			core = fx:part("Ball", Vector3.one * 4 * s, CFrame.new(c), { colour = Color3.new(0, 0, 0), material = Enum.Material.SmoothPlastic, transparency = 0 })
			horizon = fx:part("Ball", Vector3.one * 4 * s * 1.3, CFrame.new(c), { colour = 2, material = if spectral then "shell" else Enum.Material.Glass, transparency = 0.72 })
			-- accretion disc: a thin, tilted cylinder crossing the core (intersection is a curve, not a face)
			disc = fx:part("Cylinder", Vector3.new(0.15 * s, 11 * s, 11 * s), CFrame.new(c), { colour = 3, material = "shell", transparency = 0.5 })
		end
	end

	-- inward-spiralling ribbons
	local beams = {}
	for i = 1, ({ 3, 4, 6 })[fx.detail] or 4 do
		local w = fx:beam(c, c, {
			width0 = 2.2,
			width1 = 0.2,
			colour = { fx.rampHex[3], fx.rampHex[2], fx.rampHex[1] },
			transparency = { { 0, 0.8 }, { 1, 0.2 } },
			tex = "beam_energy",
			texSpeed = -3,
			segments = 16,
			zoffset = i * 0.01,
		})
		table.insert(beams, { w, Curves.ring(i, 6) })
	end
	-- inward rings (flat, shrinking)
	local rings = fx:emitter("ring", CFrame.new(c), { rate = 2.5, life = 1.6, sizeKeys = { { 0, R / 1.1 }, { 1, 0.5 } }, colour = { fx.rampHex[2], fx.rampHex[3] } })
	local motes = fx:emitter("motes", CFrame.new(c), { area = Vector3.one * R * 2, shape = "Sphere", shapeStyle = "Surface", shapeInOut = "Inward", rate = 20, speed = 6 })
	local _ = rings
	local _m = motes

	-- debris pulled in (magnetic: orbits in rings and arcs)
	local debris = {}
	local nd = ({ 4, 7, 10 })[fx.detail] or 7
	for i = 1, nd do
		local p = debrisPart(fx, i, s * fx:rand(0.7, 1.2))
		table.insert(debris, { part = p, phase = (i - 1) / nd, ang = fx:rand(0, 6.28), tilt = fx:rand(-0.6, 0.6), rot = p.CFrame.Rotation, size = p.Size, spin = Vector3.new(fx:rand(-5, 5), fx:rand(-5, 5), fx:rand(-5, 5)) })
	end
	local arcs = nil
	if magnetic and fx.detail >= 2 then
		arcs = Common.lightning(fx, c, c + Vector3.new(1, 0, 0), { width = 0.4, layers = 1, interval = 0.12 })
	end
	local light = fx:light(CFrame.new(c), fx:c(2), 2, R * 2)

	fx:onUpdate(function(_, t, dt)
		local grow = Curves.outCubic(math.clamp(t / 0.7, 0, 1)) * (if fx.stopping then fx.fade else 1)
		if core and not onGround then
			local pulse = 1 + 0.05 * math.sin(t * 6)
			core.Size = Vector3.one * math.max(0.1, 4 * s * grow * pulse)
			horizon.Size = core.Size * 1.3
			disc.CFrame = CFrame.new(c) * CFrame.Angles(0.35, t * 1.5, math.pi / 2 + 0.2)
			disc.Size = Vector3.new(0.15 * s, 11 * s * grow, 11 * s * grow)
		elseif core then
			core.Size = Vector3.new(0.06, 4.8 * s * grow, 4.8 * s * grow)
			disc.Size = Vector3.new(0.06, 2 * R * 0.8 * grow, 2 * R * 0.8 * grow)
			disc.Transparency = 0.45 + 0.25 * math.sin(t * 2)
		end
		for _, rec in beams do
			local w, a0 = rec[1], rec[2]
			local ang = a0 + t * 2.4
			local outer = c + Vector3.new(math.cos(ang) * R * grow, (if onGround then 0.2 else math.sin(ang * 2) * 2 * s), math.sin(ang) * R * grow)
			local tangent = Vector3.new(-math.sin(ang), 0, math.cos(ang))
			w:set(CFrame.fromMatrix(outer, tangent, Vector3.yAxis), CFrame.fromMatrix(c, tangent, Vector3.yAxis))
			w.beam.CurveSize0 = R * 0.5 * grow
			w.beam.CurveSize1 = R * 0.2 * grow
		end
		for _, d in debris do
			if magnetic then
				d.ang += dt * 2.2
				local r = R * (0.45 + 0.4 * d.phase) * grow
				local pos = c + CFrame.Angles(d.tilt, 0, 0) * Vector3.new(math.cos(d.ang) * r, math.sin(d.ang * 3) * s, math.sin(d.ang) * r)
				d.rot = d.rot * CFrame.Angles(d.spin.X * dt, d.spin.Y * dt, d.spin.Z * dt)
				d.part.CFrame = CFrame.new(pos) * d.rot
			else
				d.phase += dt / 2.2
				if d.phase >= 1 then
					d.phase -= 1
					d.ang = fx:rand(0, 6.28)
				end
				local k = d.phase
				local r = R * Curves.spiralIn(k) * grow + 0.3
				d.ang += dt * (2 + 8 * k)
				local y = if onGround then -k * 2 * s + 0.3 else d.tilt * r * 0.5
				local pos = c + Vector3.new(math.cos(d.ang) * r, y, math.sin(d.ang) * r)
				d.rot = d.rot * CFrame.Angles(d.spin.X * dt, d.spin.Y * dt, d.spin.Z * dt)
				d.part.CFrame = CFrame.new(pos) * d.rot
				-- spaghettify: stretch toward the core as it falls in, then vanish
				local stretch = 1 + 2 * Curves.inCubic(k)
				d.part.Size = Vector3.new(d.size.X / math.sqrt(stretch), d.size.Y / math.sqrt(stretch), d.size.Z * stretch)
				d.part.CFrame = Common.look(pos, c - pos) * CFrame.Angles(0, 0, d.ang)
				d.part.Transparency = if k > 0.9 then 1 else (if spectral then 0.2 else 0)
			end
		end
		if arcs and #debris >= 2 then
			local i1 = math.floor(t * 8) % #debris + 1
			local i2 = (i1 + 2) % #debris + 1
			arcs.setEnds(debris[i1].part.CFrame.Position, debris[i2].part.CFrame.Position)
		end
		if light then
			light.Brightness = (2 + math.sin(t * 4)) * grow
		end
	end)
end

function Z.sinkhole(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local R = (fx.params.radius or 7) * s
	local pit = fx:groundDisc(g, 0.5, { noRaycast = true, colour = Color3.new(0.03, 0.02, 0.02), material = Enum.Material.SmoothPlastic, transparency = 0, thickness = 0.05 })
	local rim = fx:groundDecal(g, R * 2.6, "crack", { transparency = 0.15, noRaycast = true })
	local rocks = {}
	for i = 1, ({ 3, 5, 7 })[fx.detail] or 5 do
		local ang = Curves.ring(i, 7, fx:rand(0, 1))
		local p = fx:part("Block", Vector3.one * fx:rand(1, 1.8) * s, CFrame.new(g), { colour = math.floor(fx:rand(3, 5.99)), material = "body", transparency = fx:alphaFor("body") })
		table.insert(rocks, { p, ang, fx:rand(0, 1), p.CFrame.Rotation * CFrame.Angles(fx:rand(0, 6), fx:rand(0, 6), 0) })
	end
	fx:emitter("dust", CFrame.new(g + Vector3.new(0, 0.5, 0)), { area = Vector3.new(R * 2, 0.5, R * 2), shape = "Cylinder", rate = 10, size = 1 })
	fx:emitter("pebbles", CFrame.new(g + Vector3.new(0, 0.5, 0)), { area = Vector3.new(R * 2, 0.5, R * 2), shape = "Disc", shapeStyle = "Surface", shapeInOut = "Inward", rate = 10, speed = 0.3 })
	fx.fadeOut = 0.8
	fx:onUpdate(function(_, t, dt)
		local grow = Curves.outCubic(math.clamp(t / 1, 0, 1)) * (if fx.stopping then fx.fade else 1)
		local cf0 = pit.CFrame
		pit.Size = Vector3.new(0.05, 2 * R * 0.8 * grow + 0.2, 2 * R * 0.8 * grow + 0.2)
		pit.CFrame = cf0
		if rim then
			rim:set(0.15 + 0.85 * (1 - grow))
		end
		for _, r in rocks do
			r[3] = (r[3] + dt * 0.35) % 1
			local k = r[3]
			local rad = R * (1 - k) * grow
			r[2] += dt * 0.6
			local pos = g + Vector3.new(math.cos(r[2]) * rad, 0.5 - k * 3 * s, math.sin(r[2]) * rad)
			r[1].CFrame = CFrame.new(pos) * r[4]
			r[1].Transparency = if k > 0.85 then 1 else fx:alphaFor("body")
		end
	end)
end

function Z.blizzard(fx)
	local s = fx.scale
	local move = mover(fx, 3 * s)
	local R = (fx.params.radius or 14) * s
	local snow = fx:emitter("snow", CFrame.new(), { area = Vector3.new(R * 2, 6 * s, R * 2), shape = "Box", rate = 70, size = 1.3, speed = 2 })
	local streaks = fx:emitter("windStreaks", CFrame.new(), { area = Vector3.new(R * 2, 4 * s, R * 2), shape = "Box", rate = 14, size = 1.4, colour = { fx.rampHex[1], fx.rampHex[2] } })
	local mist = fx:emitter("frostMist", CFrame.new(), { area = Vector3.new(R * 2, 1, R * 2), shape = "Box", rate = 12, size = 2 })
	local frost = fx:groundDecal(fx:ground(fx:at().Position), R * 2.2, "frost", { colour = 1, transparency = 1, noRaycast = true })
	local crystals = {}
	for i = 1, ({ 2, 4, 6 })[fx.detail] or 4 do
		local x, z = Curves.disc(i, 6)
		local p = fx:ground(fx:at().Position) + Vector3.new(x * R * 0.8, 0, z * R * 0.8)
		local h = fx:rand(1.5, 3) * s
		local final = CFrame.new(p) * CFrame.Angles(fx:rand(-0.3, 0.3), fx:rand(0, 6.28), fx:rand(-0.3, 0.3)) * CFrame.new(0, h * 0.25, 0) * CFrame.Angles(0, math.pi / 4, 0)
		local c = fx:part("Block", Vector3.new(h * 0.35, h, h * 0.35), final, { colour = math.floor(fx:rand(1, 3.99)), material = "body", transparency = fx:alphaFor("body") })
		Common.riser(fx, c, final, h, 0.4 + i * 0.15, 0.3)
		table.insert(crystals, c)
	end
	local light = fx:light(CFrame.new(fx:at().Position + Vector3.new(0, 4, 0)), Color3.fromRGB(190, 230, 255), 1.5, R * 2)
	fx.fadeOut = 1
	fx:onUpdate(function(_, t)
		local c = move(t)
		local windAng = t * 0.25
		local wind = Vector3.new(math.cos(windAng), 0, math.sin(windAng)) * 22 * s
		snow.pe.Acceleration = wind + Vector3.new(0, -4, 0)
		streaks.pe.Acceleration = wind * 0.6
		snow:moveTo(CFrame.new(c + Vector3.new(0, 7 * s, 0)))
		streaks:moveTo(CFrame.new(c + Vector3.new(0, 3 * s, 0)))
		mist:moveTo(CFrame.new(c + Vector3.new(0, 0.8, 0)))
		if frost then
			frost:set(math.max(0.15, 1 - Curves.outCubic(math.clamp(t / 2, 0, 1)) * fx.fade))
		end
		if light then
			light.Brightness = 1.5 * fx.fade
		end
	end)
end

function Z.wildfire(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local R = (fx.params.radius or 10) * s
	local maxPatches = ({ 5, 8, 12 })[fx.detail] or 8
	local patches = 0
	local spreadTime = fx.params.spreadTime or 4
	local smoke = fx:emitter("smoke", CFrame.new(g + Vector3.new(0, 4 * s, 0)), { area = Vector3.new(R, 2, R), shape = "Box", rate = 6, size = 1.6 })
	local embers = fx:emitter("embers", CFrame.new(g + Vector3.new(0, 1, 0)), { area = Vector3.new(R, 1, R), shape = "Box", rate = 12 })
	local _ = smoke
	local _e = embers
	local light = fx:light(CFrame.new(g + Vector3.new(0, 3, 0)), fx:c(3), 3, R * 2.5)
	local function spawnPatch()
		patches += 1
		local x, z = Curves.disc(patches, maxPatches)
		local p = g + Vector3.new(x * R, 0, z * R)
		local size = fx:rand(0.9, 1.4)
		fx:emitter("fire", CFrame.new(p + Vector3.new(0, 0.3, 0)), { area = Vector3.new(2.4, 0.4, 2.4) * s, shape = "Box", rate = 14, size = size * 1.3 })
		fx:groundDecal(p, 5 * s * size, "scorch", { transparency = 0.3, noRaycast = true })
		if fx.detail >= 3 and patches % 3 == 0 then
			fx:emitter("sparks", CFrame.new(p), { size = 0.6 }):emit(10)
		end
	end
	spawnPatch()
	fx:every(spreadTime / maxPatches, function()
		if patches < maxPatches and not fx.stopping then
			spawnPatch()
		end
	end, 0.2)
	fx.fadeOut = 1
	if light then
		fx:onUpdate(function(_, t)
			light.Brightness = (2 + patches / maxPatches * 2) * Curves.flicker(t, fx.uid, 0.3) * fx.fade
		end)
	end
end

-- Hazard pool look per element.
local POOL = {
	Fire = { mat = "CrackedLava", glow = true, bubbles = "embers", vapour = "smoke", colour = 4, alpha = 0 },
	Water = { mat = "Glass", bubbles = "bubbles", vapour = "mist", colour = 3, alpha = 0.3 },
	Ice = { mat = "Glacier", bubbles = nil, vapour = "frostMist", colour = 2, alpha = 0.1, decal = "frost" },
	Poison = { mat = "Glass", glow = true, bubbles = "toxicBubbles", vapour = "toxicGas", colour = 3, alpha = 0.15 },
	Earth = { mat = "Mud", bubbles = "bubbles", vapour = nil, colour = 4, alpha = 0 },
	Shadow = { mat = "SmoothPlastic", bubbles = "wisps", vapour = "darkMotes", colour = 5, alpha = 0.05 },
	Light = { mat = "Neon", bubbles = "motes", vapour = "stars", colour = 2, alpha = 0.6 },
	Nature = { mat = "LeafyGrass", bubbles = "pollen", vapour = "leavesDrift", colour = 3, alpha = 0 },
}

function Z.pool(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local R = (fx.params.radius or 7) * s
	local look = POOL[fx.element] or { mat = "Neon", bubbles = Palettes.elementFx(fx.element).secondary, vapour = Palettes.elementFx(fx.element).ambient, colour = 3, alpha = 0.5, glow = true }
	local spectral = fx:spectral()
	local mat = if spectral then (if fx.element == "Shadow" then Enum.Material.SmoothPlastic else Enum.Material.Neon) else Enum.Material[look.mat]
	local base = fx:groundDisc(g, 0.5, { noRaycast = true, colour = look.colour, material = mat, transparency = if spectral then 0.35 else look.alpha, thickness = 0.1 })
	local glowDisc
	if look.glow then
		-- second layer on its own (higher) slot and a smaller radius: never coincident with the base
		glowDisc = fx:groundDisc(g, 0.4, { noRaycast = true, colour = 2, material = Enum.Material.Neon, transparency = 0.65, thickness = 0.05 })
	end
	local decal = look.decal and fx:groundDecal(g, R * 2.4, look.decal, { colour = 1, transparency = 1, noRaycast = true }) or nil
	if look.bubbles then
		fx:emitter(look.bubbles, CFrame.new(g + Vector3.new(0, 0.3, 0)), { area = Vector3.new(R * 1.6, 0.3, R * 1.6), shape = "Cylinder", rate = 8 })
	end
	if look.vapour and fx.detail >= 2 then
		fx:emitter(look.vapour, CFrame.new(g + Vector3.new(0, 1, 0)), { area = Vector3.new(R * 1.6, 1, R * 1.6), shape = "Cylinder", rate = 5 })
	end
	local ring = fx:emitter("ring", CFrame.new(g + Vector3.new(0, 0.25, 0)), { size = R / 6, life = 1.6 })
	fx:every(1.6, function()
		ring:emit(1)
	end)
	local light = (look.glow or spectral) and fx:light(CFrame.new(g + Vector3.new(0, 2, 0)), fx:c(3), 1.5, R * 2) or nil
	local cf0, cf1 = base.CFrame, glowDisc and glowDisc.CFrame
	fx.fadeOut = 0.8
	fx:onUpdate(function(_, t)
		local grow = Curves.outCubic(math.clamp(t / 0.5, 0, 1)) * (if fx.stopping then fx.fade else 1)
		local r = math.max(0.1, R * grow)
		base.Size = Vector3.new(0.1, 2 * r, 2 * r)
		base.CFrame = cf0
		if glowDisc then
			glowDisc.Size = Vector3.new(0.05, 2 * r * 0.78, 2 * r * 0.78)
			glowDisc.CFrame = cf1
			glowDisc.Transparency = 0.55 + 0.2 * Curves.pulse(t, 0.6)
		end
		if decal then
			decal:set(1 - 0.85 * grow)
		end
		if light then
			light.Brightness = 1.5 * grow * Curves.flicker(t, fx.uid, 0.15)
		end
	end)
end

function Z.storm(fx)
	local params = { at = fx:at(), scale = fx.scale, element = "Lightning", strikeMin = 0.5, strikeMax = 1.3 }
	fx:child("cloud.storm", params)
	fx:child("rain.local", { at = fx:at(), scale = fx.scale, element = "Water" })
end

function Z.sandstorm(fx)
	local s = fx.scale
	local move = mover(fx, 5 * s)
	local R = (fx.params.radius or 14) * s
	local cols = { fx.rampHex[2], fx.rampHex[3] }
	local dust = fx:emitter("dust", CFrame.new(), { area = Vector3.new(R * 2, 6 * s, R * 2), shape = "Box", rate = 30, size = 2.2, colour = cols })
	local sand = fx:emitter("windStreaks", CFrame.new(), { area = Vector3.new(R * 2, 5 * s, R * 2), shape = "Box", rate = 18, size = 1.4, colour = cols })
	local grit = fx:emitter("pebbles", CFrame.new(), { area = Vector3.new(R * 2, 5 * s, R * 2), shape = "Box", rate = 20, size = 0.4 })
	fx.fadeOut = 1
	fx:onUpdate(function(_, t)
		local c = move(t)
		local ang = t * 0.2
		local wind = Vector3.new(math.cos(ang), 0.1, math.sin(ang)) * 30 * s
		dust.pe.Acceleration = wind
		sand.pe.Acceleration = wind
		grit.pe.Acceleration = wind + Vector3.new(0, -20, 0)
		dust:moveTo(CFrame.new(c + Vector3.new(0, 3 * s, 0)))
		sand:moveTo(CFrame.new(c + Vector3.new(0, 3 * s, 0)))
		grit:moveTo(CFrame.new(c + Vector3.new(0, 3 * s, 0)))
	end)
end

-- One plant. Returns parts and the final CFrames to grow into.
local function plant(fx, p: Vector3, i: number)
	local s = fx.scale
	local e = fx.element
	local spectral = fx:spectral()
	local h = fx:rand(1.4, 2.8) * s
	local parts = {}
	local stemCol = if spectral then 3 else Color3.fromRGB(88, 140, 60)
	local stemMat = if spectral then "shell" else Enum.Material.Grass
	-- stem: vertical cylinder buried 0.4 studs (its end cap is below the ground)
	local stemCF = CFrame.new(p + Vector3.new(0, h / 2 - 0.4 * s, 0)) * CFrame.Angles(0, 0, math.pi / 2)
	table.insert(parts, { fx:part("Cylinder", Vector3.new(h, 0.22 * s, 0.22 * s), stemCF, { colour = stemCol, material = stemMat, transparency = if spectral then 0.3 else 0 }), stemCF })
	local top = p + Vector3.new(0, h - 0.4 * s, 0)
	if e == "Arcane" or e == "Poison" then
		-- glowing mushroom: wide flattened cap; stem top is inside the cap
		local capCF = CFrame.new(top)
		table.insert(parts, { fx:part("Ellipsoid", Vector3.new(1.9, 0.9, 1.9) * s, capCF, { colour = (i % 2) + 2, material = if spectral or e == "Arcane" then "core" else Enum.Material.SmoothPlastic, transparency = 0.1 }), capCF })
	elseif e == "Light" or e == "Ice" then
		local cf = CFrame.new(top) * CFrame.Angles(0, fx:rand(0, 1), 0)
		table.insert(parts, { fx:part("Block", Vector3.new(0.8, 1.8, 0.8) * s, cf * CFrame.Angles(0, math.pi / 4, 0), { colour = 1, material = "core", transparency = fx:alphaFor("core") }), cf * CFrame.Angles(0, math.pi / 4, 0) })
	else
		-- flower: petals radiate from a centre ball; each petal is rotated so petals only meet along curves
		local petals = if fx.detail >= 3 then 5 else 4
		local petalCol = ({ Color3.fromRGB(255, 120, 170), Color3.fromRGB(255, 214, 90), Color3.fromRGB(170, 140, 255), Color3.fromRGB(255, 255, 255) })[i % 4 + 1]
		for k = 1, petals do
			local ang = Curves.ring(k, petals)
			local cf = CFrame.new(top) * CFrame.Angles(0, ang, 0) * CFrame.new(0, 0, -0.5 * s) * CFrame.Angles(math.rad(25), 0, 0)
			table.insert(parts, { fx:part("Ellipsoid", Vector3.new(0.55, 0.14, 0.95) * s, cf, { colour = if spectral then 2 else petalCol, material = if spectral then "core" else Enum.Material.SmoothPlastic, transparency = if spectral then 0.2 else 0 }), cf })
		end
		local centre = CFrame.new(top + Vector3.new(0, 0.08 * s, 0))
		table.insert(parts, { fx:part("Ball", Vector3.one * 0.48 * s, centre, { colour = if spectral then 1 else Color3.fromRGB(255, 200, 60), material = if spectral then "core" else Enum.Material.SmoothPlastic, transparency = 0 }), centre })
	end
	return parts, top
end

function Z.garden(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local R = (fx.params.radius or 7) * s
	local n = ({ 4, 7, 10 })[fx.detail] or 7
	for i = 1, n do
		local x, z = Curves.disc(i, n)
		local p = g + Vector3.new(x * R, 0, z * R)
		local parts = plant(fx, p, i)
		local delay = i * 0.08
		for _, rec in parts do
			local part, final = rec[1], rec[2]
			local start = fx.t + delay
			local baseAlpha = part.Transparency
			local baseSize = part.Size
			local rel = CFrame.new(p):ToObjectSpace(final)
			part.CFrame = final * CFrame.new(0, -3 * s, 0)
			fx:onUpdate(function(_, t)
				local k = Curves.outBack(math.clamp((t - start) / 0.45, 0, 1), 1.6) * (if fx.stopping then fx.fade else 1)
				-- grow from the ground point: UNIFORM scale (positions and sizes) about the plant base, so the
				-- plant keeps its no-shared-face layout at every frame of the animation
				local kk = math.max(k, 0.02)
				local sway = CFrame.Angles(math.sin(t * 1.4 + i) * 0.04, 0, math.cos(t * 1.1 + i) * 0.04)
				part.Size = baseSize * kk
				part.CFrame = CFrame.new(p) * sway * CFrame.new(rel.Position * kk) * rel.Rotation
				part.Transparency = if k <= 0.02 then 1 else baseAlpha
			end)
		end
	end
	local e = fx.element
	local bloom = if e == "Arcane" then "motes" elseif e == "Poison" then "toxicGas" elseif e == "Light" or e == "Ice" then "glints" else "petals"
	fx:emitter(bloom, CFrame.new(g + Vector3.new(0, 1.5, 0)), { area = Vector3.new(R * 2, 2, R * 2), shape = "Cylinder", rate = 8 })
	fx:emitter("pollen", CFrame.new(g + Vector3.new(0, 1, 0)), { area = Vector3.new(R * 2, 2, R * 2), shape = "Cylinder", rate = 6 })
	if e == "Arcane" or e == "Light" then
		fx:light(CFrame.new(g + Vector3.new(0, 2, 0)), fx:c(2), 1.5, R * 2)
	end
	fx.fadeOut = 0.6
end

function Z.spores(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local R = (fx.params.radius or 7) * s
	local n = ({ 3, 4, 6 })[fx.detail] or 4
	local caps = {}
	local spectral = fx:spectral()
	for i = 1, n do
		local x, z = Curves.disc(i, n)
		local p = g + Vector3.new(x * R * 0.8, 0, z * R * 0.8)
		local h = fx:rand(1.5, 2.6) * s
		local stemCF = CFrame.new(p + Vector3.new(0, h / 2 - 0.4 * s, 0)) * CFrame.Angles(0, 0, math.pi / 2)
		local stem = fx:part("Cylinder", Vector3.new(h, 0.5 * s, 0.5 * s), stemCF, { colour = if spectral then 2 else Color3.fromRGB(235, 228, 205), material = if spectral then "shell" else Enum.Material.SmoothPlastic, transparency = if spectral then 0.3 else 0 })
		local capCF = CFrame.new(p + Vector3.new(0, h - 0.4 * s, 0))
		local cap = fx:part("Ellipsoid", Vector3.new(2.6, 1.2, 2.6) * s, capCF, { colour = 3, material = if spectral then "core" else Enum.Material.SmoothPlastic, transparency = if spectral then 0.15 else 0 })
		Common.riser(fx, stem, stemCF, h, i * 0.1, 0.4)
		Common.riser(fx, cap, capCF, h, i * 0.1, 0.4)
		table.insert(caps, capCF)
	end
	local puff = fx:emitter("toxicGas", CFrame.new(g), { size = 0.9 })
	fx:every(0.7, function()
		local cf = caps[math.floor(fx:rand(1, #caps + 0.999))]
		puff:moveTo(cf * CFrame.new(0, 0.8 * s, 0))
		puff:emit(5)
	end, 0.5)
	fx:emitter("pollen", CFrame.new(g + Vector3.new(0, 2, 0)), { area = Vector3.new(R * 2, 3, R * 2), shape = "Cylinder", rate = 10, colour = { fx.rampHex[1], fx.rampHex[2] } })
	fx.fadeOut = 0.6
end

function Z.runes(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local R = (fx.params.radius or 7) * s
	local outer = fx:groundDecal(g, R * 2, "rune_circle", { colour = 2, transparency = 1, noRaycast = true, yaw = 0 })
	local inner = fx:groundDecal(g, R * 1.15, "rune_circle", { colour = 1, transparency = 1, noRaycast = true, yaw = 0 })
	if not outer then
		-- decal texture unavailable: flat ring particles keep the circle readable
		local ring = fx:emitter("ring", CFrame.new(g + Vector3.new(0, 0.2, 0)), { size = R / 6, life = 1.2 })
		fx:every(0.6, function()
			ring:emit(1)
		end)
	end
	fx:emitter("runes", CFrame.new(g + Vector3.new(0, 0.6, 0)), { area = Vector3.new(R * 1.8, 0.5, R * 1.8), shape = "Cylinder", rate = 10 })
	local orbit = {}
	if fx.detail >= 2 then
		for i = 1, 4 do
			table.insert(orbit, { Common.crystal(fx, Vector3.new(0.5, 1.2, 0.5) * s, CFrame.new(g), { colour = 2, material = "core", transparency = 0.15 }), Curves.ring(i, 4) })
		end
	end
	local light = fx:light(CFrame.new(g + Vector3.new(0, 2, 0)), fx:c(3), 2, R * 2)
	local cfO = outer and outer.part.CFrame
	local cfI = inner and inner.part.CFrame
	fx.fadeOut = 0.6
	fx:onUpdate(function(_, t)
		local k = Curves.outCubic(math.clamp(t / 0.5, 0, 1)) * fx.fade
		if outer then
			outer.part.CFrame = cfO * CFrame.Angles(0, t * 0.5, 0)
			outer:set(1 - 0.9 * k)
		end
		if inner then
			inner.part.CFrame = cfI * CFrame.Angles(0, -t * 0.8, 0)
			inner:set(1 - 0.75 * k)
		end
		for _, o in orbit do
			local ang = o[2] + t * 1.2
			o[1].CFrame = CFrame.new(g + Vector3.new(math.cos(ang) * R * 0.9, 2 * s + math.sin(t * 2 + o[2]) * 0.4 * s, math.sin(ang) * R * 0.9)) * CFrame.Angles(0, t * 2 + math.pi / 4, 0)
			o[1].Transparency = 0.15 + 0.85 * (1 - k)
		end
		if light then
			light.Brightness = 2 * k
		end
	end)
end

function Z.sanctum(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local R = (fx.params.radius or 7) * s
	local shafts = {}
	for i = 1, ({ 2, 3, 4 })[fx.detail] or 3 do
		local x, z = Curves.disc(i, 4)
		local p = g + Vector3.new(x * R * 0.6, 0, z * R * 0.6)
		local w = fx:rand(1.4, 2.4) * s
		-- shafts start 1 stud underground (no end cap on the ground) and fade into the sky
		local cf = CFrame.new(p + Vector3.new(0, 20 * s - 1, 0)) * CFrame.Angles(0, 0, math.pi / 2)
		table.insert(shafts, { fx:part("Cylinder", Vector3.new(40 * s, w, w), cf, { colour = 1, material = "core", transparency = 0.8 }), i })
	end
	local glow = fx:groundDisc(g, R, { noRaycast = true, colour = 2, material = Enum.Material.Neon, transparency = 0.75, thickness = 0.05 })
	local _ = glow
	fx:emitter("motes", CFrame.new(g + Vector3.new(0, 1, 0)), { area = Vector3.new(R * 2, 1, R * 2), shape = "Cylinder", rate = 14, speed = 1.5 })
	local light = fx:light(CFrame.new(g + Vector3.new(0, 3, 0)), fx:c(2), 2, R * 2.5)
	fx.fadeOut = 0.8
	fx:onUpdate(function(_, t)
		local k = Curves.outCubic(math.clamp(t / 0.6, 0, 1)) * fx.fade
		for _, sh in shafts do
			sh[1].Transparency = 1 - (0.25 + 0.08 * math.sin(t * 2 + sh[2])) * k
		end
		glow.Transparency = 1 - 0.25 * k
		if light then
			light.Brightness = 2 * k
		end
	end)
end

function Z.eclipse(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local c = g + Vector3.new(0, 34 * s, 0)
	local sun = fx:part("Ball", Vector3.one * 12 * s, CFrame.new(c), { colour = Color3.new(0, 0, 0), material = Enum.Material.SmoothPlastic, transparency = 0 })
	-- corona shells behind the black disc (radii 1.3x and 1.69x: never coincident)
	local corona = fx:shells(CFrame.new(c), 6 * s * 1.3, 2, { colours = { 1, 2 }, materials = { "core", "shell" }, alphas = { 0.55, 0.8 } })
	local flares = {}
	if fx.detail >= 2 then
		for i = 1, 6 do
			local ang = Curves.ring(i, 6)
			local dir = Vector3.new(math.cos(ang), math.sin(ang), 0)
			table.insert(flares, { fx:beam(c + dir * 7 * s, c + dir * 13 * s, { width0 = 2.4, width1 = 0, colour = { fx.rampHex[1], fx.rampHex[2] }, transparency = { { 0, 0.3 }, { 1, 1 } }, zoffset = 0.01 * i }), dir })
		end
	end
	fx:emitter("wisps", CFrame.new(g + Vector3.new(0, 1, 0)), { area = Vector3.new(24 * s, 2, 24 * s), shape = "Cylinder", rate = 16, size = 1.6, colour = { "#1A0F2E", "#05030A" } })
	fx:emitter("darkMotes", CFrame.new(g + Vector3.new(0, 2, 0)), { area = Vector3.new(24 * s, 4, 24 * s), shape = "Cylinder", rate = 8 })
	fx.fadeOut = 1
	fx:onUpdate(function(_, t)
		local k = Curves.outCubic(math.clamp(t / 1.2, 0, 1)) * fx.fade
		sun.Transparency = 1 - k
		for i, p in corona do
			p.Transparency = 1 - (if i == 1 then 0.45 else 0.2) * k * (0.85 + 0.15 * math.sin(t * 3 + i))
		end
		for _, f in flares do
			local len = (10 + 3 * math.sin(t * 2 + f[2].X * 5)) * s
			f[1]:set(c + f[2] * 7 * s, c + f[2] * len)
			f[1].beam.Width0 = 2.4 * s * k
		end
	end)
end

function Z.starfall(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local R = (fx.params.radius or 12) * s
	fx:emitter("motes", CFrame.new(g + Vector3.new(0, 24 * s, 0)), { area = Vector3.new(R * 2, 2, R * 2), shape = "Box", rate = 10 })
	local nextAt = 0.2
	fx:onUpdate(function(_, t)
		if t >= nextAt and not fx.stopping then
			nextAt = t + fx:rand(0.35, 0.75) / (if fx.detail >= 3 then 1 else 0.7)
			local x, z = fx:rand(-1, 1), fx:rand(-1, 1)
			local to = g + Vector3.new(x * R, 0, z * R)
			fx:child("projectile.comet", { to = to, element = fx.element, scale = s * 0.6, impactScale = s * 0.6 })
			table.remove(fx.children) -- stars finish on their own
		end
	end)
end

return function(fx)
	local f = Z[fx.entry.variant or "pool"] or Z.pool
	f(fx)
end
