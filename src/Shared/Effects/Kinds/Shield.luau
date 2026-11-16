--!nonstrict
-- Shields: bubble (follows a target), barrier (flat panel), dome (big ally dome), mirror (orbiting plates).
-- handle:pulse() flashes the shield (call it when the shield absorbs a hit).

local Curves = require(script.Parent.Parent.Curves)
local Runtime = require(script.Parent.Parent.Runtime)
local Common = require(script.Parent.Common)

local S = {}

local function fieldMaterial(fx)
	return if fx:spectral() then Enum.Material.ForceField else Enum.Material.Glass
end

local function pulser(fx)
	local hitAt = -10
	fx.onPulse = function()
		hitAt = fx.t
	end
	return function(t): number
		return math.exp(-(t - hitAt) * 8)
	end
end

function S.bubble(fx)
	local root = Runtime.rootPart(fx.params.target)
	local size = Runtime.extents(fx.params.target)
	local R = (fx.params.radius or math.max(size.X, size.Y, size.Z) * 0.75) * fx.scale
	local spectral = fx:spectral()
	local centre = function(): Vector3
		return if root and root.Parent then root.CFrame.Position else fx:at().Position
	end
	local field = fx:part("Ball", Vector3.one, CFrame.new(centre()), { colour = 2, material = fieldMaterial(fx), transparency = if spectral then 0 else 0.7, reflectance = if spectral then 0 else 0.15 })
	local inner = fx:part("Ball", Vector3.one, CFrame.new(centre()), { colour = 3, material = "shell", transparency = 0.9 })
	local glints = fx:emitter("glints", field, { area = Vector3.one * R * 2, shape = "Sphere", shapeStyle = "Surface", rate = 4 })
	local hit = pulser(fx)
	fx:emitter("ringAir", CFrame.new(centre()), { size = R / 4 }):emit(1)
	fx.fadeOut = 0.35
	fx:onUpdate(function(_, t)
		local grow = Curves.outBack(math.clamp(t / 0.35, 0, 1), 2)
		local shrink = if fx.stopping then fx.fade else 1
		local h = hit(t)
		local r = R * grow * shrink * (1 + 0.04 * h + 0.015 * math.sin(t * 3))
		field.CFrame = CFrame.new(centre())
		field.Size = Vector3.one * 2 * math.max(r, 0.05)
		inner.CFrame = field.CFrame
		inner.Size = field.Size / 1.3
		local base = if spectral then 0 else 0.7
		field.Transparency = math.clamp(base - 0.3 * h + (1 - shrink), 0, 1)
		inner.Transparency = math.clamp(0.9 - 0.5 * h + (1 - shrink) * 0.1, 0, 1)
		if h > 0.9 then
			glints:emit(6)
		end
	end)
end

function S.barrier(fx)
	local s = fx.scale
	local params = fx.params
	local cf
	local width = (params.length or 12) * s
	if params.from and params.to then
		local a, b = Runtime.posOf(params.from), Runtime.posOf(params.to)
		local mid = (a + b) / 2
		width = math.max(4, (b - a).Magnitude)
		cf = CFrame.lookAt(fx:ground(mid), fx:ground(mid) + (b - a).Unit:Cross(Vector3.yAxis))
	else
		local at = fx:at()
		cf = CFrame.new(fx:ground(at.Position)) * at.Rotation
	end
	local H = 7 * s
	local spectral = fx:spectral()
	-- panel spans the width between two posts; its ends are buried inside the posts (round, so no shared plane),
	-- its bottom edge 0.5 below the ground
	local panel = fx:part("Block", Vector3.new(width, H, 0.3 * s), cf, { colour = 2, material = fieldMaterial(fx), transparency = if spectral then 0.05 else 0.55, reflectance = if spectral then 0 else 0.2 })
	local postL = fx:part("Cylinder", Vector3.new(H + 1.6 * s, 0.9 * s, 0.9 * s), cf, { colour = 4, material = if spectral then "core" else Enum.Material.Metal, transparency = if spectral then 0.1 else 0 })
	local postR = fx:part("Cylinder", Vector3.new(H + 1.6 * s, 0.9 * s, 0.9 * s), cf, { colour = 4, material = if spectral then "core" else Enum.Material.Metal, transparency = if spectral then 0.1 else 0 })
	fx:emitter("glints", panel, { area = Vector3.new(width, H, 0.3), shape = "Box", rate = 5 })
	local hit = pulser(fx)
	fx.fadeOut = 0.5
	local up = CFrame.Angles(0, 0, math.pi / 2)
	fx:onUpdate(function(_, t)
		local k = Curves.outBack(math.clamp(t / 0.4, 0, 1), 1.3) * (if fx.stopping then fx.fade else 1)
		local y = -H + (H / 2 - 0.5 * s + H) * k -- rises out of the ground
		panel.CFrame = cf * CFrame.new(0, y, 0)
		postL.CFrame = cf * CFrame.new(-width / 2, y + 0.3 * s, 0) * up
		postR.CFrame = cf * CFrame.new(width / 2, y + 0.3 * s, 0) * up
		panel.Transparency = math.clamp((if spectral then 0.05 else 0.55) - 0.3 * hit(t), 0, 1)
	end)
end

function S.dome(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local R = (fx.params.radius or 14) * s
	local spectral = fx:spectral()
	-- sphere centred 0.6 studs below the ground: the ground cuts it on a circle, never a shared face
	local dome = fx:part("Ball", Vector3.one, CFrame.new(g - Vector3.new(0, 0.6, 0)), { colour = 2, material = fieldMaterial(fx), transparency = if spectral then 0 else 0.75, reflectance = if spectral then 0 else 0.1 })
	local rim = fx:groundDecal(g, R * 2.1, "ring", { colour = 2, transparency = 0.3, noRaycast = true })
	fx:emitter("motes", CFrame.new(g + Vector3.new(0, 1, 0)), { area = Vector3.new(R * 1.6, 1, R * 1.6), shape = "Cylinder", rate = 10 })
	local hit = pulser(fx)
	fx.fadeOut = 0.6
	fx:onUpdate(function(_, t)
		local k = Curves.outBack(math.clamp(t / 0.6, 0, 1), 1.2) * (if fx.stopping then fx.fade else 1)
		dome.Size = Vector3.one * 2 * math.max(0.05, R * k)
		dome.Transparency = math.clamp((if spectral then 0 else 0.75) - 0.25 * hit(t) + (1 - k) * 0.3, 0, 1)
		if rim then
			rim:set(1 - 0.7 * k)
		end
	end)
end

function S.mirror(fx)
	local s = fx.scale
	local root = Runtime.rootPart(fx.params.target)
	local size = Runtime.extents(fx.params.target)
	local R = math.max(size.X, size.Z) * 0.9 + 1.2 * s
	local plates = {}
	local n = ({ 3, 4, 5 })[fx.detail] or 4
	for i = 1, n do
		local p = fx:part("Block", Vector3.new(2.2, 3.2, 0.12) * s, CFrame.new(), {
			colour = 1,
			material = if fx:spectral() then "core" else Enum.Material.Glass,
			transparency = if fx:spectral() then 0.35 else 0.1,
			reflectance = 0.6,
		})
		table.insert(plates, { p, Curves.ring(i, n) })
	end
	fx:emitter("glints", root or fx:at(), { area = Vector3.new(R * 2, size.Y, R * 2), shape = "Cylinder", rate = 6 })
	pulser(fx)
	fx.fadeOut = 0.4
	fx:onUpdate(function(_, t)
		local c = if root and root.Parent then root.CFrame.Position else fx:at().Position
		local k = Curves.outBack(math.clamp(t / 0.4, 0, 1)) * fx.fade
		for i, rec in plates do
			local ang = rec[2] + t * 1.6
			local pos = c + Vector3.new(math.cos(ang) * R * k, math.sin(t * 2 + i) * 0.4 * s, math.sin(ang) * R * k)
			rec[1].CFrame = Common.look(pos, pos - c)
		end
	end)
end

return function(fx)
	local f = S[fx.entry.variant or "bubble"] or S.bubble
	f(fx)
end
