--!nonstrict
-- rain.local: precipitation over an area, flavoured by element (water rain, ember rain, acid rain, snow/hail,
-- glitter for Arcane/Light). Following Roblox guidance, the area is covered by several low-rate emitters on a
-- grid rather than one high-rate emitter.

local LOOK = {
	Water = { preset = "rain", splash = "droplets" },
	Fire = { preset = "embers", splash = "sparks", fall = true },
	Poison = { preset = "rain", splash = "toxicSplash", colour = true },
	Ice = { preset = "snow", splash = nil },
	Light = { preset = "stars", splash = nil, fall = true },
	Arcane = { preset = "motes", splash = nil, fall = true },
	Earth = { preset = "pebbles", splash = "dust", fall = true },
}

return function(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local R = (fx.params.radius or 12) * s
	local look = LOOK[fx.element] or LOOK.Water
	local cells = if fx.detail >= 3 then 2 else 1
	local cell = 2 * R / cells
	local height = 28 * s
	for ix = 1, cells do
		for iz = 1, cells do
			local p = g + Vector3.new(-R + cell * (ix - 0.5), height, -R + cell * (iz - 0.5))
			local opts = { area = Vector3.new(cell, 1, cell), shape = "Box", rate = 60 / cells, dir = "Bottom" }
			if look.fall then
				opts.accel = Vector3.new(0, -40, 0)
				opts.speed = 4
				opts.life = 1.4
				opts.spread = { 5, 5 }
			end
			if look.colour then
				opts.colour = { fx.rampHex[2], fx.rampHex[3] }
			end
			fx:emitter(look.preset, CFrame.new(p), opts)
		end
	end
	if look.splash and fx.detail >= 2 then
		fx:emitter(look.splash, CFrame.new(g + Vector3.new(0, 0.3, 0)), { area = Vector3.new(2 * R, 0.2, 2 * R), shape = "Box", rate = 16, size = 0.5, speed = 0.3 })
	end
	fx:emitter("mist", CFrame.new(g + Vector3.new(0, 2, 0)), { area = Vector3.new(2 * R, 2, 2 * R), shape = "Box", rate = 3, size = 1.5 })
	fx.fadeOut = 1
end
