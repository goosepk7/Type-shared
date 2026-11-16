--!nonstrict
-- Clouds: puff, rain, storm (random strikes), toxic, steam, darkness.
-- Puffy clouds are overlapping spheres of distinct radii and centres (curved surfaces only intersect along
-- curves, never share a face).

local Curves = require(script.Parent.Parent.Curves)

local C = {}

local function puffs(fx, centre: Vector3, R: number, opts)
	local spectral = fx:spectral()
	local n = ({ 4, 6, 8 })[fx.detail] or 6
	local balls = {}
	for i = 1, n do
		local x, z = Curves.disc(i, n)
		local r = R * (0.42 + 0.22 * Curves.hash(i * 3.1 + fx.uid) + (1 - math.sqrt(x * x + z * z)) * 0.18)
		local off = Vector3.new(x * R * 0.95, (1 - (x * x + z * z)) * R * 0.25 + Curves.hash(i) * R * 0.1, z * R * 0.6)
		local p = fx:part("Ball", Vector3.one * 2 * r, CFrame.new(centre + off), {
			colour = opts.colours[(i - 1) % #opts.colours + 1],
			material = if spectral then "shell" else Enum.Material.SmoothPlastic,
			transparency = if spectral then 0.45 else (opts.alpha or 0.05),
		})
		table.insert(balls, { p, off, r, fx:rand(0, 6.28) })
	end
	fx.fadeOut = 0.8
	fx:onUpdate(function(_, t)
		local grow = Curves.outCubic(math.clamp(t / 0.8, 0, 1)) * (if fx.stopping then fx.fade else 1)
		for _, b in balls do
			local bob = Vector3.new(0, math.sin(t * 0.8 + b[4]) * 0.25 * fx.scale, 0)
			b[1].CFrame = CFrame.new(centre + b[2] * grow + bob)
			b[1].Size = Vector3.one * 2 * math.max(0.05, b[3] * grow)
		end
	end)
	return balls
end

function C.puff(fx)
	local s = fx.scale
	local c = fx:at().Position
	puffs(fx, c, 5 * s, { colours = { 1, 2 } })
	fx:emitter("mist", CFrame.new(c), { area = Vector3.new(10, 3, 6) * s, shape = "Box", rate = 4, size = 1.2 })
end

local function skyCloud(fx, storm: boolean)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local c = g + Vector3.new(0, 16 * s, 0)
	local spectral = fx:spectral()
	local colours
	if storm then
		colours = if spectral then { 4, 5 } else nil
	end
	if not colours then
		colours = if spectral then { 2, 3 } else nil
	end
	local balls = puffs(fx, c, 7 * s, { colours = colours or { 1, 2 }, alpha = 0 })
	if not spectral then
		-- Solid: real cloud greys (independent of element)
		local greys = if storm then { Color3.fromRGB(78, 82, 94), Color3.fromRGB(96, 100, 112) } else { Color3.fromRGB(205, 210, 218), Color3.fromRGB(226, 230, 236) }
		for i, b in balls do
			b[1].Color = greys[(i - 1) % 2 + 1]
		end
	end
	fx:emitter("mist", CFrame.new(c), { area = Vector3.new(16, 4, 10) * s, shape = "Box", rate = 5, size = 1.6, colour = if storm then { "#5A5F6E", "#3A3D48" } else { "#FFFFFF", "#DDE3EA" } })
	return c, g
end

function C.rain(fx)
	local s = fx.scale
	local c, g = skyCloud(fx, false)
	local rain = fx:emitter("rain", CFrame.new(c - Vector3.new(0, 2 * s, 0)), { area = Vector3.new(12, 1, 8) * s, rate = 70 })
	local _ = rain
	local splash = fx:emitter("droplets", CFrame.new(g + Vector3.new(0, 0.3, 0)), { area = Vector3.new(12, 0.2, 8) * s, shape = "Box", rate = 18, size = 0.5, speed = 0.3 })
	local _s = splash
end

function C.storm(fx)
	local s = fx.scale
	local c, g = skyCloud(fx, true)
	fx:emitter("rain", CFrame.new(c - Vector3.new(0, 2 * s, 0)), { area = Vector3.new(14, 1, 10) * s, rate = 80 })
	local inner = fx:light(CFrame.new(c), Color3.fromRGB(200, 200, 255), 0, 30)
	local nextStrike = 0.6
	fx:onUpdate(function(_, t)
		if inner then
			local flick = Curves.noise(t * 6, fx.uid)
			inner.Brightness = if flick > 0.82 then 6 else 0
		end
		if t >= nextStrike and not fx.stopping then
			nextStrike = t + fx:rand(fx.params.strikeMin or 1.0, fx.params.strikeMax or 2.2)
			local ang = fx:rand(0, 6.28)
			local r = fx:rand(0, 9) * s
			local h = fx:child("strike.lightning", { at = CFrame.new(g + Vector3.new(math.cos(ang) * r, 0, math.sin(ang) * r)), element = "Lightning", scale = s * 0.8 })
			table.remove(fx.children) -- strikes finish on their own
			local _ = h
		end
	end)
end

function C.toxic(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local R = (fx.params.radius or 9) * s
	fx:emitter("toxicGas", CFrame.new(g + Vector3.new(0, 1.5 * s, 0)), { area = Vector3.new(R * 2, 2 * s, R * 2), shape = "Cylinder", rate = 16, size = 1.4 * R / 9 })
	if fx.detail >= 2 then
		fx:emitter("toxicGas", CFrame.new(g + Vector3.new(0, 4 * s, 0)), { area = Vector3.new(R * 1.4, 2 * s, R * 1.4), shape = "Cylinder", rate = 8, size = 1.8 * R / 9 })
	end
	fx:emitter("toxicBubbles", CFrame.new(g + Vector3.new(0, 0.4, 0)), { area = Vector3.new(R * 1.6, 0.4, R * 1.6), shape = "Cylinder", rate = 10 })
	local light = fx:light(CFrame.new(g + Vector3.new(0, 3, 0)), fx:c(3), 1.2, R * 2)
	if light then
		fx:onUpdate(function(_, t)
			light.Brightness = (1 + 0.3 * Curves.pulse(t, 0.7)) * fx.fade
		end)
	end
end

function C.steam(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local R = (fx.params.radius or 8) * s
	local st = fx:emitter("steam", CFrame.new(g + Vector3.new(0, 1.5, 0)), { area = Vector3.new(R * 1.6, 2, R * 1.6), shape = "Cylinder", rate = 26, size = R / 6 })
	st:emit(20)
	if fx.detail >= 2 then
		fx:emitter("steam", CFrame.new(g + Vector3.new(0, 5 * s, 0)), { area = Vector3.new(R, 2, R), shape = "Cylinder", rate = 10, size = R / 5 })
	end
end

function C.darkness(fx)
	local s = fx.scale
	local c = fx:at().Position
	local R = (fx.params.radius or 7) * s
	local core = fx:part("Ball", Vector3.one, CFrame.new(c), { colour = Color3.new(0.02, 0.01, 0.04), material = Enum.Material.SmoothPlastic, transparency = 0.3 })
	fx:emitter("wisps", CFrame.new(c), { area = Vector3.one * R * 1.8, shape = "Sphere", rate = 22, size = R / 3, colour = { "#1A0F2E", "#05030A" } })
	fx:emitter("darkMotes", CFrame.new(c), { area = Vector3.one * R * 2.2, shape = "Sphere", shapeStyle = "Surface", rate = 8 })
	fx.fadeOut = 0.8
	fx:onUpdate(function(_, t)
		local k = Curves.outCubic(math.clamp(t / 0.6, 0, 1)) * (if fx.stopping then fx.fade else 1)
		core.Size = Vector3.one * math.max(0.1, 2 * R * 0.85 * k * (1 + 0.03 * math.sin(t * 2)))
		core.Transparency = 0.3 + 0.7 * (1 - k)
	end)
end

return function(fx)
	local f = C[fx.entry.variant or "puff"] or C.puff
	f(fx)
end
