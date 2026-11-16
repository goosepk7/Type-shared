--!nonstrict
-- Auras: element (looping, follows a target), charge (converging), buff (rising ring), heal.

local Curves = require(script.Parent.Parent.Curves)
local Palettes = require(script.Parent.Parent.Palettes)
local Runtime = require(script.Parent.Parent.Runtime)

local A = {}

local function anchor(fx)
	local root = Runtime.rootPart(fx.params.target)
	local size = Runtime.extents(fx.params.target)
	return root, size
end

-- Feet-level CFrame for a target (or the effect origin).
local function feet(fx, root, size): CFrame
	if root then
		return CFrame.new(root.CFrame.Position - Vector3.new(0, size.Y / 2, 0))
	end
	return CFrame.new(fx:ground(fx:at().Position))
end

function A.element(fx)
	local root, size = anchor(fx)
	local w = math.max(size.X, size.Z)
	local efx = Palettes.elementFx(fx.element)
	local where = root or fx:at()
	local body = fx:emitter(efx.ambient, where, { area = size * 0.8, shape = "Cylinder", rate = 6, size = w / 4 })
	local rise = fx:emitter(efx.secondary, where, { offset = CFrame.new(0, -size.Y / 2, 0), rate = 6, size = w / 5 })
	local ring = fx:emitter("ring", feet(fx, root, size), { size = w / 6, life = 1.4 })
	local light = fx:light(where, fx:c(2), 1.2, w * 3)
	local _ = body
	local _r = rise
	fx:every(0.7, function()
		ring:moveTo(feet(fx, root, size) * CFrame.new(0, 0.2, 0))
		ring:emit(1)
	end)
	if light then
		fx:onUpdate(function(_, t)
			light.Brightness = (0.9 + 0.4 * Curves.pulse(t, 1.2)) * fx.fade
		end)
	end
end

function A.charge(fx)
	local s = fx.scale
	local root, size = anchor(fx)
	local centre = if root then root.CFrame.Position else fx:at().Position
	local R = math.max(size.X, size.Y) * 0.9
	local dur = fx.duration or 1
	local orbs = {}
	for i = 1, ({ 5, 8, 10 })[fx.detail] or 8 do
		local dir = Vector3.new(fx:rand(-1, 1), fx:rand(-0.6, 1), fx:rand(-1, 1))
		dir = if dir.Magnitude > 0.1 then dir.Unit else Vector3.yAxis
		local p = fx:part("Ball", Vector3.one * 0.35 * s, CFrame.new(centre + dir * R), { colour = 1, material = "core", transparency = 0.1 })
		fx:trail(p, 0.3, 0.12, { colour = { 1, 3 } })
		table.insert(orbs, { p, dir, fx:rand(0, dur * 0.4) })
	end
	local glow = fx:part("Ball", Vector3.one * 0.4 * s, CFrame.new(centre), { colour = 2, material = "core", transparency = 0.4 })
	local field = fx:part("Ball", Vector3.one * R * 2, CFrame.new(centre), { colour = 3, material = if fx:spectral() then Enum.Material.ForceField else "shell", transparency = 0.6 })
	local light = fx:light(CFrame.new(centre), fx:c(2), 0, 14)
	fx:onUpdate(function(_, t)
		local c = if root and root.Parent then root.CFrame.Position else centre
		local k = math.clamp(t / dur, 0, 1)
		for _, o in orbs do
			local kk = Curves.inCubic(math.clamp((t - o[3]) / (dur * 0.6), 0, 1))
			local swirl = CFrame.Angles(0, kk * 3, 0)
			o[1].CFrame = CFrame.new(c + (swirl * (o[2] * R * (1 - kk))))
			o[1].Transparency = if kk >= 1 then 1 else 0.1
		end
		glow.CFrame = CFrame.new(c)
		glow.Size = Vector3.one * (0.4 + 2.2 * Curves.inQuad(k)) * s
		field.CFrame = CFrame.new(c)
		field.Size = Vector3.one * math.max(glow.Size.X * 1.3, R * 2 * (1 - Curves.outCubic(k)))
		field.Transparency = 0.6 + 0.4 * k
		if light then
			light.Brightness = 4 * k
		end
	end)
	fx:after(dur * 0.98, function()
		fx:emitter("flash", CFrame.new(if root then root.CFrame.Position else centre), { size = 0.5 }):emit(1)
	end)
end

function A.buff(fx)
	local root, size = anchor(fx)
	local w = math.max(size.X, size.Z)
	local base = feet(fx, root, size) * CFrame.new(0, 0.2, 0)
	local ring = fx:emitter("ring", base, { size = w / 7, speed = 900, life = 1.6 })
	ring:emit(1)
	fx:after(0.2, function()
		ring:emit(1)
	end)
	fx:emitter("stars", if root then root.CFrame else base, { size = w / 5 }):emit(14)
	fx:emitter(Palettes.elementFx(fx.element).burst, if root then root.CFrame else base):emit(10)
	local light = fx:light(if root then root else base, fx:c(2), 0, w * 3)
	if light then
		fx:onUpdate(function(_, t)
			light.Brightness = 3 * Curves.flash(t / (fx.duration or 1.2))
		end)
	end
end

function A.heal(fx)
	local root, size = anchor(fx)
	local w = math.max(size.X, size.Z)
	local where = root or fx:at()
	fx:emitter("plusUp", where, { area = size * 0.7, shape = "Box", rate = 10, size = w / 4 })
	fx:emitter("leavesDrift", where, { rate = 4, size = w / 5 })
	local ring = fx:emitter("ring", feet(fx, root, size) * CFrame.new(0, 0.2, 0), { size = w / 7, speed = 500, life = 1.4, colour = { "#E9FFD9", "#7CE07C" } })
	ring:emit(1)
	local light = fx:light(where, Color3.fromRGB(150, 255, 150), 0, w * 3)
	if light then
		fx:onUpdate(function(_, t)
			light.Brightness = 2 * Curves.envelope(t, fx.duration or 1.6, 0.2, 0.6)
		end)
	end
end

return function(fx)
	local f = A[fx.entry.variant or "element"] or A.element
	f(fx)
end
