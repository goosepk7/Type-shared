--!nonstrict
-- Explosions (small / medium / huge). Timeline:
--   0.00  light flash + burst sprite + sparks + element burst
--   0.00  nested fireball shells expand (outCubic) and burn off; huge ones rise
--   0.02  ground shockwave ring (+ dust pushed outward), huge: second ring at 0.25
--   0.05  debris flies (medium/huge), scorch decal on the ground, smoke column / mushroom
-- Solid style with a non-emissive element (Earth, Water...) uses dust/water shells instead of fire.

local Curves = require(script.Parent.Parent.Curves)
local Palettes = require(script.Parent.Parent.Palettes)
local Common = require(script.Parent.Common)
local Runtime = require(script.Parent.Parent.Runtime)

local SIZE = { small = 3, medium = 6, huge = 12 }

return function(fx)
	local variant = fx.entry.variant or "medium"
	local s = fx.scale
	local R = SIZE[variant] * s
	local cf = fx:at()
	local pos = cf.Position
	local g = fx:ground(pos)
	local nearGround = (pos - g).Magnitude < R
	local spectral = fx:spectral()
	local emissive = Palettes.emissive(fx.element, fx.style)
	local efx = Palettes.elementFx(fx.element)
	local huge = variant == "huge"
	local detail = fx.detail

	-- flash + light
	fx:emitter("flash", cf, { size = R / 4 }):emit(if huge then 2 else 1)
	fx:emitter("sparks", cf, { size = R / 5, speed = R / 5 }):emit(if huge then 70 else if variant == "medium" then 45 else 24)
	fx:emitter(efx.burst, cf, { size = R / 5, speed = R / 6 }):emit(if huge then 30 else 16)
	local light = fx:light(cf, fx:c(2), 0, R * 3)
	if light then
		fx:onUpdate(function(_, t)
			light.Brightness = (if huge then 10 else 6) * Curves.flash(t / (if huge then 1.4 else 0.8))
		end)
	end
	if Runtime.shake and fx.params.shake ~= false then
		Runtime.shake(pos, if huge then 1 else if variant == "medium" then 0.5 else 0.2)
	end

	-- fireball shells: radii keep a fixed ratio while growing, so they never coincide
	local count = if huge and detail >= 2 then 3 else 2
	local colours = if spectral or emissive then { 1, 3, 4 } else { 2, 3, 4 }
	local materials = if spectral or emissive then { "core", "shell", "shell" } else { Enum.Material.SmoothPlastic, Enum.Material.SmoothPlastic, Enum.Material.SmoothPlastic }
	local shells = fx:shells(cf, R * 0.12, count, { ratio = 1.35, colours = colours, materials = materials, alphas = { 0, 0.3, 0.55 } })
	local base = {}
	for i, p in shells do
		base[i] = p.Size.X
	end
	local rise = if huge then R * 0.7 else 0
	local life = if huge then 1.5 elseif variant == "medium" then 0.9 else 0.55
	fx:onUpdate(function(_, t)
		local k = math.clamp(t / life, 0, 1)
		local grow = 1 + Curves.outCubic(k) * 6.5
		local c = cf * CFrame.new(0, rise * Curves.outQuad(k), 0)
		for i, p in shells do
			p.Size = Vector3.one * base[i] * grow
			p.CFrame = c * CFrame.Angles(t * (0.6 + i * 0.3), t * 0.4, 0)
			local a0 = if i == 1 then 0 elseif i == 2 then 0.3 else 0.55
			p.Transparency = a0 + (1 - a0) * Curves.inQuad(math.clamp(k * (1.15 - i * 0.1), 0, 1))
		end
	end)

	-- shockwave(s) on the ground
	if nearGround then
		local ringAt = CFrame.new(g + Vector3.new(0, 0.2, 0))
		local ring = fx:emitter("ring", ringAt, { size = R / 5, life = if huge then 1.6 else 1 })
		ring:emit(1)
		local dr = fx:emitter("dustRing", CFrame.new(g + Vector3.new(0, 0.4, 0)), { area = Vector3.new(R * 0.7, 0.2, R * 0.7), size = R / 6, speed = R / 6 })
		dr:emit(if huge then 30 else 16)
		if huge then
			fx:after(0.25, function()
				ring:emit(1)
				dr:emit(18)
			end)
		end
		-- scorch / crater
		local mark = fx:groundDecal(g, R * 1.8, "scorch", { transparency = 0.15, noRaycast = true })
		local crack = huge and fx:groundDecal(g, R * 1.4, "crack", { transparency = 0.2, noRaycast = true }) or nil
		local dur = fx.duration or 3
		fx:onUpdate(function(_, t)
			local a = Curves.remap(t, dur * 0.6, dur, 0.15, 1)
			if mark then
				mark:set(math.max(a, 1 - fx.fade))
			end
			if crack then
				crack:set(math.max(a, 1 - fx.fade))
			end
		end)
	else
		fx:emitter("ringAir", cf, { size = R / 4 }):emit(1)
	end

	-- debris
	if variant ~= "small" and detail >= 2 then
		Common.debris(fx, pos + Vector3.new(0, 0.5, 0), if huge then (if detail >= 3 then 14 else 9) else (if detail >= 3 then 8 else 5), {
			size = { 0.4 * R / 6, 1.1 * R / 6 },
			speed = { R * 1.6, R * 3.4 },
			up = { R * 2.4, R * 4.6 },
			life = if huge then 2.4 else 1.6,
			groundY = g.Y,
			colours = if spectral then { 2, 3, 4 } else { 4, 5, 5 },
			material = "debris",
			transparency = if spectral then 0.1 else 0,
		})
	end

	-- smoke
	local smoke = fx:emitter("smoke", cf, { size = R / 3.5, speed = R / 5, life = if huge then 1.6 else 1 })
	smoke:emit(if huge then 22 else if variant == "medium" then 12 else 6)
	if huge and detail >= 2 then
		-- mushroom: a second puff that follows the rising fireball
		fx:after(0.35, function()
			smoke:moveTo(cf * CFrame.new(0, rise, 0))
			smoke:emit(14)
		end)
		local embers = fx:emitter("embers", cf, { size = 2, speed = 3 })
		embers:emit(40)
	end
end
