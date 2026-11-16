--!nonstrict
-- Walls rising along a line (from -> to, or `at` facing + params.length). Segments are separated by a gap and
-- each gets its own small yaw/tilt, so neighbouring faces are never coplanar; bottoms are buried below ground.

local Curves = require(script.Parent.Parent.Curves)
local Runtime = require(script.Parent.Parent.Runtime)
local Common = require(script.Parent.Common)

local LOOK = { Earth = "stone", Ice = "ice", Fire = "fire", Nature = "thorns", Metal = "metal", Water = "water" }

local function line(fx): (Vector3, Vector3)
	local p = fx.params
	local s = fx.scale
	if p.from and p.to then
		return fx:ground(Runtime.posOf(p.from)), fx:ground(Runtime.posOf(p.to))
	end
	local at = fx:at()
	local half = (p.length or 16) * s / 2
	local right = at.RightVector
	local c = fx:ground(at.Position)
	return c - right * half, c + right * half
end

return function(fx)
	local s = fx.scale
	local look = fx.entry.variant or LOOK[fx.element] or "energy"
	local a, b = line(fx)
	local dir = b - a
	local len = math.max(dir.Magnitude, 2)
	local unit = if dir.Magnitude > 0.01 then dir.Unit else Vector3.xAxis
	local facing = CFrame.lookAt(Vector3.zero, unit:Cross(Vector3.yAxis))
	local segW = (if look == "metal" then 3.2 elseif look == "thorns" then 1.6 else 2.4) * s
	local gap = 0.18 * s
	local n = math.clamp(math.floor(len / (segW + gap)), 3, ({ 6, 9, 12 })[fx.detail] or 9)
	local spacing = len / n
	local H = (fx.params.height or 7) * s
	fx.fadeOut = 0.7

	if look == "fire" then
		-- no solid parts: a curtain of flame emitters along the line, scorch marks under it
		local carriers = math.max(2, math.floor(n / 2))
		for i = 1, carriers do
			local p = a + unit * (len * (i - 0.5) / carriers)
			local cf = CFrame.new(p) * facing.Rotation
			fx:emitter("fire", cf * CFrame.new(0, 0.5, 0), { area = Vector3.new(len / carriers, 0.5, 1.2 * s), shape = "Box", rate = 36, size = 1.6, speed = 1.6 })
			if fx.detail >= 2 then
				fx:emitter("embers", cf * CFrame.new(0, 1, 0), { area = Vector3.new(len / carriers, 1, 1), shape = "Box", rate = 8 })
			end
			fx:groundDecal(p, len / carriers * 1.3, "scorch", { transparency = 0.25, noRaycast = true })
		end
		fx:emitter("smoke", CFrame.new((a + b) / 2 + Vector3.new(0, H, 0)), { area = Vector3.new(len, 1, 2), shape = "Box", rate = 6, size = 1.4 })
		local light = fx:light(CFrame.new((a + b) / 2 + Vector3.new(0, 3, 0)), fx:c(3), 3, len)
		if light then
			fx:onUpdate(function(_, t)
				light.Brightness = 3 * Curves.flicker(t, fx.uid, 0.3) * fx.fade
			end)
		end
		return
	end

	local spectral = fx:spectral()
	for i = 1, n do
		local p = a + unit * (spacing * (i - 0.5))
		local h = H * fx:rand(0.8, 1.15)
		local yaw = math.rad(fx:rand(-8, 8))
		local tilt = math.rad(fx:rand(-4, 4))
		local base = CFrame.new(p) * facing.Rotation * CFrame.Angles(tilt, yaw, 0)
		local part
		local final
		if look == "stone" then
			final = base * CFrame.new(0, h / 2 - 0.8 * s, 0)
			part = fx:part("Block", Vector3.new(spacing - gap, h, 2.2 * s), final, { colour = math.floor(fx:rand(3, 4.99)), material = "body", transparency = fx:alphaFor("body") })
		elseif look == "ice" then
			final = base * CFrame.new(0, h / 2 - 0.8 * s, 0) * CFrame.Angles(0, math.pi / 4, 0)
			local w = (spacing - gap) * 0.72
			part = fx:part("Block", Vector3.new(w, h, w), final, { colour = math.floor(fx:rand(1, 3.99)), material = "body", transparency = fx:alphaFor("body") })
		elseif look == "thorns" then
			final = base * CFrame.Angles(0, 0, math.rad(fx:rand(-14, 14))) * CFrame.new(0, h / 2 - 1 * s, 0)
			part = fx:part("Ellipsoid", Vector3.new(spacing * 0.9, h * 1.15, 1.4 * s), final, { colour = math.floor(fx:rand(3, 4.99)), material = "body", transparency = fx:alphaFor("body") })
			if fx.detail >= 2 then
				local thorn = fx:part("Ellipsoid", Vector3.new(0.3, 1.4, 0.3) * s, final, { colour = 5, material = "debris", transparency = fx:alphaFor("body") })
				Common.riser(fx, thorn, final * CFrame.new(0, h * 0.2, 0.6 * s) * CFrame.Angles(math.rad(70), 0, 0), h, (i - 1) * 0.04 + 0.05, 0.3)
			end
		elseif look == "metal" then
			final = base * CFrame.new(0, h / 2 - 0.8 * s, (i % 2) * 0.35 * s)
			part = fx:part("Block", Vector3.new(spacing - gap, h, 0.5 * s), final, { colour = if i % 2 == 0 then 3 else 4, material = if i % 2 == 0 then "body" else "shell", transparency = fx:alphaFor("body"), reflectance = 0.15 })
		elseif look == "water" then
			final = base * CFrame.new(0, h / 2 - 0.8 * s, 0)
			part = fx:part("Ellipsoid", Vector3.new(spacing * 1.25, h * 1.1, 2 * s), final, { colour = math.floor(fx:rand(2, 3.99)), material = if spectral then "shell" else Enum.Material.Glass, transparency = if spectral then 0.4 else 0.35 })
			fx:emitter("splash", final * CFrame.new(0, h / 2, 0), { rate = 10, size = 0.8 })
		else -- energy
			final = base * CFrame.new(0, h / 2 - 0.8 * s, 0)
			part = fx:part("Block", Vector3.new(spacing - gap, h, 0.3 * s), final, { colour = 2, material = if spectral then Enum.Material.ForceField else Enum.Material.Glass, transparency = if spectral then 0 else 0.5 })
		end
		Common.riser(fx, part, final, h + 1, (i - 1) * 0.045, 0.32)
	end
	local mid = (a + b) / 2
	fx:emitter("dustRing", CFrame.new(mid + Vector3.new(0, 0.4, 0)) * facing.Rotation, { area = Vector3.new(len, 0.2, 2), shape = "Box", size = 0.8 }):emit(18)
	local efxName = if look == "ice" then "frostMist" elseif look == "thorns" then "leaves" elseif look == "metal" then "metalSparks" else "pebbles"
	fx:emitter(efxName, CFrame.new(mid + Vector3.new(0, 1, 0)), { area = Vector3.new(len, 1, 1), shape = "Box" }):emit(16)
end
