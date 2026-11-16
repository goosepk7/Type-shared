--!nonstrict
-- Element impact: flash, expanding core, camera-facing ring, element particles, ground ring when near the
-- ground, a light pop, and debris for physical elements.

local Curves = require(script.Parent.Parent.Curves)
local Palettes = require(script.Parent.Parent.Palettes)
local Common = require(script.Parent.Common)

local DEBRIS = { Earth = "Block", Metal = "Block", Ice = "Crystal" }

return function(fx)
	local s = fx.scale
	local cf = fx:at()
	local pos = cf.Position
	local e = fx.element
	local efx = Palettes.elementFx(e)
	local spectral = fx:spectral()
	local emissive = Palettes.emissive(e, fx.style)

	local burst = fx:emitter("flash", cf, { size = 0.45 })
	burst:emit(1)
	local ring = fx:emitter("ringAir", cf, { size = 0.6 })
	ring:emit(1)
	local primary = fx:emitter(efx.burst, cf)
	primary:emit(16)
	if fx.detail >= 2 then
		local secondary = fx:emitter(efx.primary, cf, { size = 0.8 })
		secondary:emit(8)
	end

	-- expanding core: energy elements always; physical elements only in Spectral (Solid uses dust/debris)
	if spectral or emissive then
		local core = fx:part("Ball", Vector3.one * 0.5 * s, cf, { colour = 1, material = "core", transparency = 0 })
		local shell = fx:part("Ball", Vector3.one * 0.8 * s, cf, { colour = 3, material = "shell", transparency = 0.5 })
		fx:onUpdate(function(_, t)
			local k = math.clamp(t / 0.32, 0, 1)
			local r = Curves.outCubic(k)
			core.Size = Vector3.one * (0.5 + 2.6 * r) * s
			shell.Size = core.Size * 1.45 -- always 1.45x the core: never coincident
			core.Transparency = 0.05 + 0.95 * Curves.inQuad(k)
			shell.Transparency = 0.5 + 0.5 * k
		end)
	else
		local dust = fx:emitter("dust", cf, { size = 0.7 })
		dust:emit(6)
	end

	-- ground ring if the hit is near the ground
	local g = fx:ground(pos)
	if (pos - g).Magnitude < 4 * s then
		local gr = fx:emitter("ring", CFrame.new(g + Vector3.new(0, 0.15, 0)), { size = 0.55 })
		gr:emit(1)
		if not spectral and not emissive then
			local dr = fx:emitter("dustRing", CFrame.new(g + Vector3.new(0, 0.3, 0)), { area = Vector3.new(2 * s, 0.2, 2 * s), size = 0.6 })
			dr:emit(10)
		end
	end

	local shape = DEBRIS[e]
	if shape and fx.detail >= 2 then
		Common.debris(fx, pos, if fx.detail >= 3 then 6 else 4, {
			shape = shape,
			size = { 0.3, 0.75 },
			speed = { 8, 18 },
			up = { 10, 22 },
			life = 1.1,
			groundY = g.Y,
		})
	end

	local light = fx:light(cf, fx:c(2), 0, 16)
	if light then
		fx:onUpdate(function(_, t)
			light.Brightness = 5 * Curves.flash(t / 0.5)
		end)
	end
end
