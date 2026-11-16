--!nonstrict
-- Bursts: nova, shockwave, flash, spikes, shards, quake, geyser, frost, blades, splash.

local Curves = require(script.Parent.Parent.Curves)
local Palettes = require(script.Parent.Parent.Palettes)
local Common = require(script.Parent.Common)

local B = {}

function B.nova(fx)
	local s = fx.scale
	local cf = fx:at()
	local spectral = fx:spectral()
	local outer = fx:part("Ball", Vector3.one * s, cf, {
		colour = 2,
		material = if spectral then Enum.Material.ForceField else "shell",
		transparency = if spectral then 0 else 0.5,
	})
	local inner = fx:part("Ball", Vector3.one * 0.5 * s, cf, { colour = 1, material = "core", transparency = 0.3 })
	fx:emitter("ringAir", cf, { size = 0.8 }):emit(1)
	fx:emitter(Palettes.elementFx(fx.element).burst, cf):emit(14)
	local light = fx:light(cf, fx:c(2), 0, 18)
	local dur = fx.duration or 0.9
	fx:onUpdate(function(_, t)
		local k = math.clamp(t / dur, 0, 1)
		local r = Curves.outQuint(k) * 12 * s + s
		outer.Size = Vector3.one * r
		inner.Size = Vector3.one * r * 0.72 -- 1/0.72 > ShellRatio: never coincident
		outer.Transparency = (if spectral then 0 else 0.5) + (1 - (if spectral then 0 else 0.5)) * Curves.inQuad(k)
		inner.Transparency = 0.3 + 0.7 * Curves.outQuad(k)
		if light then
			light.Brightness = 4 * Curves.flash(k)
		end
	end)
end

function B.shockwave(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	fx:emitter("ring", CFrame.new(g + Vector3.new(0, 0.2, 0)), { size = 1.1 }):emit(1)
	fx:emitter("dustRing", CFrame.new(g + Vector3.new(0, 0.4, 0)), { area = Vector3.new(2 * s, 0.2, 2 * s), size = 0.8 }):emit(20)
	-- a thin expanding energy disc (lifted ground slot: never coplanar with the ground)
	if fx:spectral() then
		local disc = fx:groundDisc(g, 1 * s, { noRaycast = true, colour = 2, material = "shell", transparency = 0.5, thickness = 0.08 })
		local dur = fx.duration or 0.8
		local cf0 = disc.CFrame
		fx:onUpdate(function(_, t)
			local k = math.clamp(t / dur, 0, 1)
			local r = (1 + Curves.outQuint(k) * 13) * s
			disc.Size = Vector3.new(0.08, 2 * r, 2 * r)
			disc.CFrame = cf0
			disc.Transparency = 0.5 + 0.5 * Curves.inQuad(k)
		end)
	end
end

function B.flash(fx)
	local cf = fx:at()
	fx:emitter("flash", cf, { size = 0.9 }):emit(1)
	fx:emitter("coreGlow", cf, { size = 1.6, rate = 0 }):emit(2)
	local light = fx:light(cf, fx:c(1), 0, 24)
	if light then
		fx:onUpdate(function(_, t)
			light.Brightness = 8 * Curves.flash(t / (fx.duration or 0.5))
		end)
	end
end

-- Spikes erupting in rings. Look by element: stone, ice, crystal, metal, thorns, energy.
local SPIKE_LOOK = {
	Earth = { shape = "rock", material = "body" },
	Ice = { shape = "crystal", material = "body" },
	Light = { shape = "crystal", material = "core" },
	Metal = { shape = "blade", material = "body" },
	Nature = { shape = "thorn", material = "body" },
}

function B.spikes(fx)
	local s = fx.scale
	local centre = fx:ground(fx:at().Position)
	local look = SPIKE_LOOK[fx.element] or { shape = "crystal", material = "core" }
	local n = ({ 6, 9, 12 })[fx.detail] or 9
	local dur = fx.duration or 3
	fx.fadeOut = 0.6
	for i = 1, n do
		local ang = Curves.ring(i, n, fx:rand(0, 0.4))
		local radius = (2.5 + (i % 3) * 1.6 + fx:rand(0, 0.8)) * s
		local base = centre + Vector3.new(math.cos(ang) * radius, 0, math.sin(ang) * radius)
		local h = fx:rand(3.2, 5.6) * s
		local w = fx:rand(0.8, 1.3) * s
		-- tilt outward; the bottom third is buried below the ground (no face at ground level)
		local tilt = CFrame.Angles(0, -ang, 0) * CFrame.Angles(0, 0, -math.rad(fx:rand(10, 24)))
		local final = CFrame.new(base) * tilt * CFrame.new(0, h * 0.5 - h * 0.3, 0)
		local part
		local opts = { colour = math.floor(fx:rand(2, 4.99)), material = look.material, transparency = fx:alphaFor(look.material) }
		if look.shape == "rock" then
			part = fx:part("Block", Vector3.new(w * 1.2, h, w), final, opts)
			final = final * CFrame.Angles(0, fx:rand(0, 1.5), 0)
		elseif look.shape == "blade" then
			part = fx:part("Block", Vector3.new(w * 0.25, h, w), final, opts)
			opts.reflectance = 0.2
		elseif look.shape == "thorn" then
			part = fx:part("Ellipsoid", Vector3.new(w * 0.7, h * 1.1, w * 0.7), final, opts)
		else
			part = Common.crystal(fx, Vector3.new(w, h, w), CFrame.new(), opts)
			final = final * CFrame.Angles(0, math.pi / 4, 0)
		end
		Common.riser(fx, part, final, h, (i - 1) * 0.025, 0.28)
	end
	fx:emitter("dustRing", CFrame.new(centre + Vector3.new(0, 0.4, 0)), { area = Vector3.new(6 * s, 0.2, 6 * s), size = 0.8 }):emit(16)
	fx:emitter(Palettes.elementFx(fx.element).burst, CFrame.new(centre + Vector3.new(0, 1, 0))):emit(14)
	fx:after(math.max(0.5, dur - 0.6), function()
		fx:stop()
	end)
end

function B.shards(fx)
	local cf = fx:at()
	local g = fx:ground(cf.Position)
	Common.debris(fx, cf.Position, ({ 5, 8, 12 })[fx.detail] or 8, {
		shape = "Crystal",
		size = { 0.4, 0.9 },
		speed = { 16, 30 },
		up = { 8, 20 },
		life = 1.3,
		groundY = g.Y,
		colours = { 1, 2, 3 },
		material = "core",
		transparency = fx:alphaFor("core"),
	})
	fx:emitter("iceShards", cf, { colour = { fx.rampHex[1], fx.rampHex[3] } }):emit(18)
	fx:emitter("glints", cf):emit(8)
end

function B.quake(fx)
	local s = fx.scale
	local centre = fx:ground(fx:at().Position)
	local crack = fx:groundDecal(centre, 2 * s, "crack", { transparency = 0.1, noRaycast = true })
	local dur = fx.duration or 3
	fx.fadeOut = 0.6
	fx:onUpdate(function(_, t)
		if crack then
			local k = Curves.outCubic(math.clamp(t / 0.6, 0, 1))
			crack:set(Curves.remap(t, dur * 0.7, dur, 0.1, 1), (2 + 18 * k) * s)
		end
	end)
	local n = ({ 5, 8, 12 })[fx.detail] or 8
	for i = 1, n do
		local x, z = Curves.disc(i, n)
		local p = centre + Vector3.new(x * 9 * s, 0, z * 9 * s)
		local size = fx:rand(1.4, 2.6) * s
		local rock = Common.rock(fx, size, CFrame.new(p), { colour = math.floor(fx:rand(3, 5.99)), material = "body", transparency = fx:alphaFor("body") })
		local final = CFrame.new(p + Vector3.new(0, size * 0.25, 0)) * rock.CFrame.Rotation
		Common.riser(fx, rock, final, size * 1.2, 0.05 + i * 0.03, 0.3)
	end
	local dr = fx:emitter("dustRing", CFrame.new(centre + Vector3.new(0, 0.4, 0)), { area = Vector3.new(8 * s, 0.2, 8 * s), size = 1.2 })
	dr:emit(24)
	fx:after(0.4, function()
		dr:emit(14)
	end)
	fx:emitter("pebbles", CFrame.new(centre + Vector3.new(0, 1, 0)), { size = 1.2 }):emit(24)
	fx:after(math.max(0.6, dur - 0.6), function()
		fx:stop()
	end)
end

function B.geyser(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local spectral = fx:spectral()
	local H = 16 * s
	local column = fx:part("Ellipsoid", Vector3.new(2.4, 1, 2.4) * s, CFrame.new(g), {
		colour = 2,
		material = if spectral then "core" else Enum.Material.Glass,
		transparency = if spectral then 0.35 else 0.4,
	})
	local core = fx:part("Ellipsoid", Vector3.new(1.2, 1, 1.2) * s, CFrame.new(g), { colour = 1, material = "core", transparency = 0.3 })
	local spray = fx:emitter("splash", CFrame.new(g), { rate = 50, speed = 2, spread = { 12, 12 } })
	fx:emitter("mist", CFrame.new(g + Vector3.new(0, 2, 0)), { rate = 6 })
	local dur = fx.duration or 2
	fx:onUpdate(function(_, t)
		local up = Curves.outCubic(math.clamp(t / 0.35, 0, 1))
		local down = Curves.inQuad(math.clamp((t - dur * 0.55) / (dur * 0.45), 0, 1))
		local h = math.max(0.2, H * up * (1 - down))
		column.Size = Vector3.new(2.4 * s * (1 + 0.1 * math.sin(t * 20)), h * 1.05, 2.4 * s)
		column.CFrame = CFrame.new(g + Vector3.new(0, h * 0.5 - 0.4 * s, 0))
		core.Size = Vector3.new(1.2 * s, h * 0.9, 1.2 * s)
		core.CFrame = column.CFrame
		spray:moveTo(CFrame.new(g + Vector3.new(0, h * 0.9, 0)))
	end)
	fx:after(dur * 0.6, function()
		spray:setRate(0)
		fx:emitter("droplets", CFrame.new(g + Vector3.new(0, H * 0.7, 0)), { size = 1.4 }):emit(30)
	end)
end

function B.frost(fx)
	local s = fx.scale
	local centre = fx:ground(fx:at().Position)
	local decal = fx:groundDecal(centre, 2 * s, "frost", { colour = 1, transparency = 0.1, noRaycast = true })
	local dur = fx.duration or 2.5
	fx.fadeOut = 0.5
	fx:onUpdate(function(_, t)
		if decal then
			local k = Curves.outCubic(math.clamp(t / 0.5, 0, 1))
			decal:set(math.max(Curves.remap(t, dur * 0.6, dur, 0.1, 1), 1 - fx.fade), (2 + 12 * k) * s)
		end
	end)
	local n = ({ 4, 7, 9 })[fx.detail] or 7
	for i = 1, n do
		local x, z = Curves.disc(i, n)
		local p = centre + Vector3.new(x * 5 * s, 0, z * 5 * s)
		local h = fx:rand(1.4, 3) * s
		local w = h * 0.35
		local tilt = CFrame.Angles(fx:rand(-0.4, 0.4), fx:rand(0, 6.28), fx:rand(-0.4, 0.4))
		local final = CFrame.new(p) * tilt * CFrame.new(0, h * 0.25, 0) * CFrame.Angles(0, math.pi / 4, 0)
		local c = fx:part("Block", Vector3.new(w, h, w), final, { colour = math.floor(fx:rand(1, 3.99)), material = "body", transparency = fx:alphaFor("body") })
		Common.riser(fx, c, final, h, 0.03 * i, 0.22)
	end
	fx:emitter("frostMist", CFrame.new(centre + Vector3.new(0, 1, 0)), { size = 1.5 }):emit(12)
	fx:emitter("snow", CFrame.new(centre + Vector3.new(0, 2, 0))):emit(20)
	fx:after(math.max(0.5, dur - 0.5), function()
		fx:stop()
	end)
end

function B.blades(fx)
	local s = fx.scale
	local cf = fx:at()
	local centre = cf.Position + Vector3.new(0, 2.5 * s, 0)
	local spectral = fx:spectral()
	local n = ({ 4, 6, 8 })[fx.detail] or 6
	local R = 7 * s
	local swords = {}
	for i = 1, n do
		local ang = Curves.ring(i, n)
		local start = centre + Vector3.new(math.cos(ang) * R, fx:rand(-0.6, 1.2) * s, math.sin(ang) * R)
		local blade = fx:part("Block", Vector3.new(0.14, 0.6, 3.2) * s, CFrame.new(start), {
			colour = if spectral then 2 else 1,
			material = if spectral then "core" else Enum.Material.Metal,
			transparency = if spectral then 0.35 else 0,
			reflectance = if spectral then 0 else 0.3,
		})
		local guard = fx:part("Block", Vector3.new(0.3, 1.3, 0.22) * s, CFrame.new(start), { colour = 3, material = if spectral then "shell" else Enum.Material.Metal, transparency = if spectral then 0.4 else 0 })
		local hilt = fx:part("Cylinder", Vector3.new(0.9, 0.24, 0.24) * s, CFrame.new(start), { colour = 4, material = if spectral then "shell" else Enum.Material.Wood, transparency = if spectral then 0.4 else 0 })
		fx:trail(blade, 0.5, 0.15, { colour = { 1, 2, 3 } })
		table.insert(swords, { blade = blade, guard = guard, hilt = hilt, start = start, delay = 0.25 + i * 0.05 })
	end
	fx:onUpdate(function(_, t)
		for _, sw in swords do
			local k = Curves.inCubic(math.clamp((t - sw.delay) / 0.3, 0, 1))
			local p = sw.start:Lerp(centre, k)
			local look = Common.look(p, centre - sw.start)
			local appear = math.clamp(t / 0.25, 0, 1)
			sw.blade.CFrame = look
			-- guard and hilt sit behind the blade (blade spans z -1.6..1.6; guard at z 1.5..1.72 overlaps
			-- by 0.1 with different dimensions on every axis: no coincident faces)
			sw.guard.CFrame = look * CFrame.new(0, 0, 1.6 * s)
			sw.hilt.CFrame = look * CFrame.new(0, 0, 2.1 * s) * CFrame.Angles(0, math.pi / 2, 0)
			local a = 1 - appear + (if k >= 1 then 1 else 0)
			for _, p2 in { sw.blade, sw.guard, sw.hilt } do
				p2.Transparency = math.clamp((if spectral then 0.35 else 0) + a, 0, 1)
			end
		end
	end)
	fx:after(0.62 + n * 0.05, function()
		fx:emitter("flash", CFrame.new(centre), { size = 0.6 }):emit(1)
		fx:emitter("metalSparks", CFrame.new(centre)):emit(30)
	end)
end

function B.splash(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local at = CFrame.new(g + Vector3.new(0, 0.3, 0))
	fx:emitter("splash", at, { size = 1.3, speed = 1.1 }):emit(36)
	fx:emitter("droplets", at, { speed = 0.8 }):emit(16)
	fx:emitter("ring", CFrame.new(g + Vector3.new(0, 0.15, 0)), { size = 0.5 }):emit(1)
	fx:emitter("mist", at, { size = 0.6 }):emit(4)
	local disc = fx:groundDisc(g, 1 * s, { noRaycast = true, colour = 2, material = if fx:spectral() then "shell" else Enum.Material.Glass, transparency = 0.4, thickness = 0.06 })
	local cf0 = disc.CFrame
	fx:onUpdate(function(_, t)
		local k = math.clamp(t / (fx.duration or 1), 0, 1)
		local r = (1 + 4 * Curves.outCubic(k)) * s
		disc.Size = Vector3.new(0.06, 2 * r, 2 * r)
		disc.CFrame = cf0
		disc.Transparency = 0.4 + 0.6 * k
	end)
end

return function(fx)
	local f = B[fx.entry.variant or "nova"] or B.nova
	f(fx)
end
