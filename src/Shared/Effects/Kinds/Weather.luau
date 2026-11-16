--!nonstrict
-- Weather around the camera: a 2x2 (Low: 1x1) grid of low-rate area emitters that re-centres on the camera,
-- as Roblox recommends for rain. One weather effect at a time is the intended use.

local Curves = require(script.Parent.Parent.Curves)
local Runtime = require(script.Parent.Parent.Runtime)

local LOOK = {
	rain = { preset = "rain", rate = 70, height = 26, colour = nil },
	snow = { preset = "snow", rate = 40, height = 18, speed = 1.2 },
	storm = { preset = "rain", rate = 100, height = 26, strikes = true },
	sandstorm = { preset = "dust", rate = 18, height = 6, wind = Vector3.new(36, 2, 8), colour = { "#D9B98A", "#B08D62" } },
	ash = { preset = "embers", rate = 30, height = 20, fall = true, colour = { "#9A928C", "#5A5550" } },
	fireflies = { preset = "motes", rate = 10, height = 2, colour = { "#F4FF9A", "#B8FF5A" } },
	spores = { preset = "pollen", rate = 20, height = 6 },
}

return function(fx)
	local variant = fx.entry.variant or "rain"
	local look = LOOK[variant] or LOOK.rain
	local cells = if fx.detail >= 2 then 2 else 1
	local span = 90
	local cell = span / cells
	local emitters = {}
	for ix = 1, cells do
		for iz = 1, cells do
			local opts = { area = Vector3.new(cell, 2, cell), shape = "Box", rate = look.rate / cells, colour = look.colour }
			if look.fall then
				opts.accel = Vector3.new(2, -10, 0)
				opts.dir = "Bottom"
				opts.life = 2
			end
			if look.wind then
				opts.accel = look.wind
			end
			if look.speed then
				opts.speed = look.speed
			end
			table.insert(emitters, { fx:emitter(look.preset, CFrame.new(), opts), -span / 2 + cell * (ix - 0.5), -span / 2 + cell * (iz - 0.5) })
		end
	end
	fx.fadeOut = 1.5
	local lastCentre = nil
	local nextStrike = 2
	fx:onUpdate(function(_, t)
		local cam = Runtime.cameraPos() or fx:at().Position
		-- snap to a coarse grid so the emitters do not slide with every tiny camera move
		local cx, cz = math.floor(cam.X / 8 + 0.5) * 8, math.floor(cam.Z / 8 + 0.5) * 8
		local centre = Vector3.new(cx, cam.Y + look.height, cz)
		if lastCentre == nil or (centre - lastCentre).Magnitude > 0.1 then
			lastCentre = centre
			for _, e in emitters do
				e[1]:moveTo(CFrame.new(centre + Vector3.new(e[2], 0, e[3])))
			end
		end
		if look.strikes and t >= nextStrike and not fx.stopping then
			nextStrike = t + fx:rand(2.5, 6)
			local ang = fx:rand(0, 6.28)
			local d = fx:rand(30, 90)
			fx:child("strike.lightning", { at = CFrame.new(cam + Vector3.new(math.cos(ang) * d, -20, math.sin(ang) * d)), scale = 1.4, priority = 0 })
			table.remove(fx.children)
		end
		local _ = Curves
	end)
end
