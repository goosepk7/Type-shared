--!nonstrict
-- Strikes from the sky: forked lightning bolt, or a descending pillar of light.

local Curves = require(script.Parent.Parent.Curves)
local Common = require(script.Parent.Common)

local S = {}

function S.lightning(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local top = g + Vector3.new(fx:rand(-8, 8) * s, 70 * s, fx:rand(-8, 8) * s)
	local dur = fx.duration or 0.6
	-- pre-glow in the sky, then the bolt
	local bolt = Common.lightning(fx, top, g, { width = 1.1, layers = if fx.detail >= 2 then 2 else 1, interval = 0.04 })
	local forks = {}
	for i = 1, (if fx.detail >= 3 then 3 elseif fx.detail >= 2 then 2 else 0) do
		local k = fx:rand(0.25, 0.75)
		local p = top:Lerp(g, k)
		local off = Vector3.new(fx:rand(-1, 1) * 12, -fx:rand(6, 14), fx:rand(-1, 1) * 12) * s
		table.insert(forks, Common.lightning(fx, p, p + off, { width = 0.45, layers = 1, interval = 0.04 }))
		local _ = i
	end
	local at = CFrame.new(g + Vector3.new(0, 0.5, 0))
	fx:emitter("flash", at, { size = 0.9 }):emit(1)
	fx:emitter("sparks", at, { size = 1.1, speed = 1.1 }):emit(36)
	fx:emitter("ring", CFrame.new(g + Vector3.new(0, 0.2, 0)), { size = 0.7 }):emit(1)
	fx:emitter("electric", at, { area = Vector3.new(4, 1, 4) * s, rate = 30 })
	local scorch = fx:groundDecal(g, 6 * s, "scorch", { transparency = 0.2, noRaycast = true })
	local light = fx:light(at, fx:c(1), 10, 40)
	fx:onUpdate(function(_, t)
		local on = t < dur * 0.3 or (t > dur * 0.42 and t < dur * 0.62)
		for _, w in bolt.beams do
			w.beam.Enabled = on and not fx.stopping
		end
		for _, f in forks do
			for _, w in f.beams do
				w.beam.Enabled = on and t < dur * 0.3 and not fx.stopping
			end
		end
		if light then
			light.Brightness = if on then 10 else 2 * (1 - t / dur)
		end
		if scorch then
			scorch:set(math.max(0.2, 1 - fx.fade))
		end
	end)
end

function S.pillar(fx)
	local s = fx.scale
	local g = fx:ground(fx:at().Position)
	local H = 60 * s
	local spectral = fx:spectral()
	local outer = fx:part("Cylinder", Vector3.new(H, 0.2, 0.2), CFrame.new(g), { colour = 2, material = "shell", transparency = 0.55 })
	local inner = fx:part("Cylinder", Vector3.new(H, 0.1, 0.1), CFrame.new(g), { colour = 1, material = "core", transparency = 0.15 })
	fx:emitter("ring", CFrame.new(g + Vector3.new(0, 0.2, 0)), { size = 0.6 }):emit(1)
	local motes = fx:emitter("motes", CFrame.new(g + Vector3.new(0, 1, 0)), { area = Vector3.new(4, 1, 4) * s, shape = "Cylinder", rate = 24, speed = 3 })
	local light = fx:light(CFrame.new(g + Vector3.new(0, 3, 0)), fx:c(1), 0, 22)
	local dur = fx.duration or 1.5
	local upright = CFrame.Angles(0, 0, math.pi / 2)
	fx:onUpdate(function(_, t)
		local down = Curves.outCubic(math.clamp(t / 0.2, 0, 1))
		local env = Curves.envelope(t, dur, 0.15, 0.5) * fx.fade
		local len = H * down + 1 * s -- reaches 1 stud below the ground: no end cap on the ground plane
		local r = (2.2 + 0.25 * math.sin(t * 18)) * s * env
		-- column hangs from the sky; the inner core is 1.6x thinner and 0.8 studs longer at both ends, so no
		-- cap or side of the two cylinders ever coincides
		local centre = g + Vector3.new(0, H - len / 2, 0) -- spans [ground - 1, ground + H] when fully down
		outer.CFrame = CFrame.new(centre) * upright
		inner.CFrame = outer.CFrame
		outer.Size = Vector3.new(len, 2 * r, 2 * r)
		inner.Size = Vector3.new(len + 0.8 * s, 2 * r / 1.6, 2 * r / 1.6)
		outer.Transparency = 0.55 + 0.45 * (1 - env)
		inner.Transparency = 0.15 + 0.85 * (1 - env)
		if light then
			light.Brightness = 6 * env
		end
		if t > dur * 0.6 then
			motes:setRate(0)
		end
	end)
	local _ = spectral
end

return function(fx)
	local f = S[fx.entry.variant or "lightning"] or S.lightning
	f(fx)
end
