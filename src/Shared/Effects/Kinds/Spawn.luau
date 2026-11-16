--!nonstrict
-- Summon materialize / dissolve, portal, teleport.
-- Target fades use BasePart.LocalTransparencyModifier: a client-only multiplier that never touches the replicated
-- Transparency the summon builder set, so pooled/replicated models stay correct.

local Curves = require(script.Parent.Parent.Curves)
local Palettes = require(script.Parent.Parent.Palettes)
local Runtime = require(script.Parent.Parent.Runtime)
local Common = require(script.Parent.Common)

local S = {}

local function setLTM(parts, v: number)
	for _, p in parts do
		if p.Parent then
			p.LocalTransparencyModifier = v
		end
	end
end

function S.materialize(fx)
	local s = fx.scale
	local target = fx.params.target
	local parts = Common.partsOf(target)
	local size = Runtime.extents(target)
	local root = Runtime.rootPart(target)
	local centre = if root then root.CFrame.Position else fx:at().Position
	local g = fx:ground(centre)
	local R = math.max(size.X, size.Z) * 0.75 + 1.5 * s
	local H = math.max(size.Y * 1.6, 8 * s)
	local dur = fx.duration or 1.4
	local reveal = dur * 0.45

	setLTM(parts, 1)
	fx:onCleanup(function()
		setLTM(parts, 0)
	end)

	local circle = fx:groundDecal(g, R * 2, "rune_circle", { colour = 2, transparency = 1, noRaycast = true, yaw = 0 })
	local cf0 = circle and circle.part.CFrame
	if not circle then
		fx:emitter("ring", CFrame.new(g + Vector3.new(0, 0.2, 0)), { size = R / 6 }):emit(1)
	end
	-- light pillar: two coaxial cylinders, the inner 1.6x thinner and longer (no shared faces), base underground
	local up = CFrame.Angles(0, 0, math.pi / 2)
	local outer = fx:part("Cylinder", Vector3.new(H, 0.1, 0.1), CFrame.new(g) * up, { colour = 2, material = "shell", transparency = 0.6 })
	local inner = fx:part("Cylinder", Vector3.new(H, 0.1, 0.1), CFrame.new(g) * up, { colour = 1, material = "core", transparency = 0.3 })
	local converge = fx:emitter("motes", CFrame.new(centre), { area = Vector3.one * R * 2, shape = "Sphere", shapeStyle = "Surface", shapeInOut = "Inward", rate = 40, speed = 4 })
	local efx = Palettes.elementFx(fx.element)
	fx:emitter(efx.secondary, CFrame.new(g + Vector3.new(0, 0.5, 0)), { area = Vector3.new(R * 1.6, 0.5, R * 1.6), shape = "Cylinder", rate = 16 })
	local light = fx:light(CFrame.new(centre), fx:c(2), 0, R * 3)
	local flashed = false
	fx:onUpdate(function(_, t)
		local k = math.clamp(t / dur, 0, 1)
		local env = Curves.envelope(t, dur, 0.2, 0.45) * fx.fade
		if circle then
			circle.part.CFrame = cf0 * CFrame.Angles(0, t * 1.4, 0)
			circle:set(1 - 0.9 * env)
		end
		local r = R * 0.55 * env * (1 + 0.06 * math.sin(t * 25))
		local len = H + 1
		outer.CFrame = CFrame.new(g + Vector3.new(0, len / 2 - 1, 0)) * up
		inner.CFrame = outer.CFrame
		outer.Size = Vector3.new(len, math.max(0.05, 2 * r), math.max(0.05, 2 * r))
		inner.Size = Vector3.new(len + 0.6, math.max(0.03, 2 * r / 1.6), math.max(0.03, 2 * r / 1.6))
		outer.Transparency = 0.6 + 0.4 * (1 - env)
		inner.Transparency = 0.3 + 0.7 * (1 - env)
		if t >= reveal then
			if not flashed then
				flashed = true
				converge:setRate(0)
				fx:emitter("flash", CFrame.new(centre), { size = R / 4 }):emit(1)
				fx:emitter("stars", CFrame.new(centre), { size = 1.2 }):emit(18)
				fx:emitter("ring", CFrame.new(g + Vector3.new(0, 0.2, 0)), { size = R / 5 }):emit(1)
			end
			setLTM(parts, 1 - Curves.outCubic((t - reveal) / (dur * 0.35)))
		end
		if light then
			light.Brightness = 4 * (if t >= reveal then Curves.flash((t - reveal) / (dur - reveal)) else k)
		end
	end)
end

function S.dissolve(fx)
	local s = fx.scale
	local target = fx.params.target
	local parts = Common.partsOf(target)
	local size = Runtime.extents(target)
	local root = Runtime.rootPart(target)
	local centre = if root then root.CFrame.Position else fx:at().Position
	local dur = fx.duration or 1.2
	local keepHidden = fx.params.keepHidden ~= false
	fx:onCleanup(function()
		if not keepHidden then
			setLTM(parts, 0)
		end
	end)
	local efx = Palettes.elementFx(fx.element)
	local stream = fx:emitter("motes", CFrame.new(centre), { area = size, shape = "Box", rate = 50, speed = 3, accel = Vector3.new(0, 8, 0) })
	local bits = fx:emitter(efx.secondary, CFrame.new(centre), { area = size, shape = "Box", rate = 20 })
	local light = fx:light(CFrame.new(centre), fx:c(2), 2, math.max(size.X, size.Y) * 3)
	fx:onUpdate(function(_, t)
		local k = math.clamp(t / (dur * 0.85), 0, 1)
		setLTM(parts, Curves.inQuad(k))
		local c = if root and root.Parent then root.CFrame else CFrame.new(centre)
		stream:moveTo(c)
		bits:moveTo(c)
		if k >= 1 then
			stream:setRate(0)
			bits:setRate(0)
		end
		if light then
			light.Brightness = 2 * (1 - k)
		end
	end)
	fx:after(dur * 0.85, function()
		fx:emitter("flash", CFrame.new(centre), { size = 0.5 * s }):emit(1)
	end)
end

function S.portal(fx)
	local s = fx.scale
	local at = fx:at()
	local g = fx:ground(at.Position)
	local R = (fx.params.radius or 4) * s
	local cf = CFrame.new(g + Vector3.new(0, R + 0.6 * s, 0)) * at.Rotation
	-- rim disc (thin, bright) and a thicker dark inner disc of smaller radius: faces at different depths
	local rim = fx:part("Cylinder", Vector3.new(0.12, 0.1, 0.1), cf * CFrame.Angles(0, math.pi / 2, 0), { colour = 2, material = "core", transparency = 0.1 })
	local void = fx:part("Cylinder", Vector3.new(0.3, 0.1, 0.1), cf * CFrame.Angles(0, math.pi / 2, 0), { colour = fx:c(5), material = if fx:spectral() then Enum.Material.ForceField else Enum.Material.SmoothPlastic, transparency = 0.05 })
	local swirl = fx:emitter("windStreaks", cf, { rate = 20, size = R / 2.5, colour = { fx.rampHex[1], fx.rampHex[3] } })
	local inward = fx:emitter("motes", cf, { area = Vector3.new(R * 2.4, R * 2.4, 0.2), shape = "Cylinder", shapeStyle = "Surface", shapeInOut = "Inward", rate = 24, speed = 2 })
	local _ = swirl
	local _i = inward
	local light = fx:light(cf, fx:c(3), 3, R * 4)
	local dur = fx.duration or 2.5
	fx:onUpdate(function(_, t)
		local open = Curves.outBack(math.clamp(t / 0.4, 0, 1), 1.5)
		local close = 1 - Curves.inQuad(math.clamp((t - (dur - 0.4)) / 0.4, 0, 1))
		local k = math.max(0, open * close * fx.fade)
		local r = math.max(0.05, R * k)
		rim.Size = Vector3.new(0.12, 2 * r, 2 * r)
		void.Size = Vector3.new(0.3, 2 * r * 0.84, 2 * r * 0.84)
		rim.CFrame = cf * CFrame.Angles(0, math.pi / 2, 0) * CFrame.Angles(t * 2, 0, 0)
		void.CFrame = rim.CFrame
		if light then
			light.Brightness = 3 * k
		end
	end)
end

function S.teleport(fx)
	local s = fx.scale
	local a = fx:from()
	local b = fx:to()
	local shell = fx:part("Ball", Vector3.one * 4 * s, CFrame.new(a), { colour = 2, material = "shell", transparency = 0.3 })
	fx:emitter("stars", CFrame.new(a)):emit(12)
	fx:onUpdate(function(_, t)
		local k = math.clamp(t / 0.25, 0, 1)
		shell.Size = Vector3.one * math.max(0.05, 4 * s * (1 - Curves.inCubic(k)))
		shell.Transparency = 0.3 + 0.7 * k
	end)
	fx:after(0.25, function()
		fx:emitter("flash", CFrame.new(b), { size = 0.6 }):emit(1)
		fx:emitter("ringAir", CFrame.new(b), { size = 0.6 }):emit(1)
		fx:emitter("stars", CFrame.new(b)):emit(18)
		local l = fx:light(CFrame.new(b), fx:c(1), 5, 16)
		if l then
			fx:onUpdate(function(_, t)
				l.Brightness = 5 * Curves.flash((t - 0.25) / 0.5)
			end)
		end
	end)
end

return function(fx)
	local f = S[fx.entry.variant or "materialize"] or S.materialize
	f(fx)
end
