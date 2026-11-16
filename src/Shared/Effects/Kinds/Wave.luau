--!nonstrict
-- Waves sweeping from -> to: water crest (tsunami), flame wall, earth ripple, mudslide.

local Curves = require(script.Parent.Parent.Curves)
local Runtime = require(script.Parent.Parent.Runtime)
local Common = require(script.Parent.Common)

local function path(fx): (Vector3, Vector3)
	local p = fx.params
	if p.from and p.to then
		return fx:ground(Runtime.posOf(p.from)), fx:ground(Runtime.posOf(p.to))
	end
	local at = fx:at()
	local a = fx:ground(at.Position)
	return a, a + at.LookVector * 30 * fx.scale
end

local function crest(fx, mud: boolean)
	local s = fx.scale
	local a, b = path(fx)
	local dir = b - a
	local unit = if dir.Magnitude > 0.01 then dir.Unit else Vector3.zAxis
	local face = CFrame.lookAt(Vector3.zero, unit)
	local W = (fx.params.width or 16) * s
	local H = (if mud then 4 else 7) * s
	local spectral = fx:spectral()
	local n = ({ 4, 6, 8 })[fx.detail] or 6
	local segs = {}
	for i = 1, n do
		local x = (i - (n + 1) / 2) / n * W
		-- each segment is an ellipsoid with its own size and phase: neighbours overlap along curves only
		local p = fx:part("Ellipsoid", Vector3.new(W / n * 1.6, H, 4 * s), CFrame.new(a), {
			colour = if i % 2 == 0 then 2 else 3,
			material = if mud then Enum.Material.Mud elseif spectral then "shell" else Enum.Material.Glass,
			transparency = if mud then 0 elseif spectral then 0.35 else 0.3,
		})
		table.insert(segs, { p, x, fx:rand(0, 6.28), fx:rand(0.85, 1.15) })
	end
	local body = fx:part("Ellipsoid", Vector3.new(W * 1.1, H * 0.45, 9 * s), CFrame.new(a), {
		colour = 4,
		material = if mud then Enum.Material.Mud elseif spectral then "shell" else Enum.Material.Glass,
		transparency = if mud then 0.05 elseif spectral then 0.55 else 0.45,
	})
	local foam = fx:emitter(if mud then "dust" else "splash", CFrame.new(a), { area = Vector3.new(W, 1, 1), shape = "Box", rate = if mud then 18 else 50, size = 1.1, colour = if mud then { "#7A5A3A", "#5E4630" } else nil })
	local mist = fx:emitter(if mud then "dust" else "mist", CFrame.new(a), { area = Vector3.new(W, 2, 2), shape = "Box", rate = 8, size = 1.3, colour = if mud then { "#8A6A47", "#5E4630" } else nil })
	local dur = fx.duration or 3
	fx.fadeOut = 0.3
	fx:onUpdate(function(_, t)
		local k = math.clamp(t / dur, 0, 1)
		local pos = a:Lerp(b, Curves.inOutSine(k))
		local rise = Curves.outCubic(math.clamp(t / 0.4, 0, 1)) * (1 - Curves.inQuad(math.clamp((k - 0.75) / 0.25, 0, 1)))
		local cf = CFrame.new(pos) * face.Rotation
		for _, sg in segs do
			local h = H * sg[4] * math.max(rise, 0.02) * (1 + 0.08 * math.sin(t * 5 + sg[3]))
			sg[1].Size = Vector3.new(W / n * 1.6, h, 4 * s)
			-- crest leans forward, centre buried below the ground so the bottom never sits on it
			sg[1].CFrame = cf * CFrame.new(sg[2], h * 0.32, 0) * CFrame.Angles(math.rad(-18), 0, 0)
		end
		body.CFrame = cf * CFrame.new(0, 0, 4 * s)
		body.Size = Vector3.new(W * 1.1, H * 0.45 * math.max(rise, 0.02), 9 * s)
		foam:moveTo(cf * CFrame.new(0, H * rise * 0.8, -0.5 * s))
		mist:moveTo(cf * CFrame.new(0, H * rise * 0.5, 2 * s))
	end)
end

local W = {}

function W.water(fx)
	crest(fx, false)
end

function W.mud(fx)
	crest(fx, true)
end

function W.flame(fx)
	local s = fx.scale
	local a, b = path(fx)
	local dir = b - a
	local unit = if dir.Magnitude > 0.01 then dir.Unit else Vector3.zAxis
	local face = CFrame.lookAt(Vector3.zero, unit)
	local Wd = (fx.params.width or 14) * s
	local fire = fx:emitter("fire", CFrame.new(a), { area = Vector3.new(Wd, 1, 2), shape = "Box", rate = 70, size = 2.2, speed = 2 })
	local embers = fx:emitter("embers", CFrame.new(a), { area = Vector3.new(Wd, 2, 2), shape = "Box", rate = 18 })
	local smoke = fx:emitter("smoke", CFrame.new(a), { area = Vector3.new(Wd, 1, 2), shape = "Box", rate = 8, size = 1.6 })
	local glow
	if fx:spectral() then
		glow = fx:part("Ellipsoid", Vector3.new(Wd, 5 * s, 2.5 * s), CFrame.new(a), { colour = 2, material = "shell", transparency = 0.6 })
	end
	local light = fx:light(CFrame.new(a), fx:c(3), 4, Wd * 1.2)
	local dur = fx.duration or 2.5
	local lastScorch = 0
	fx:onUpdate(function(_, t)
		local k = math.clamp(t / dur, 0, 1)
		local pos = a:Lerp(b, Curves.outQuad(k))
		local cf = CFrame.new(pos) * face.Rotation
		fire:moveTo(cf * CFrame.new(0, 0.5, 0))
		embers:moveTo(cf * CFrame.new(0, 2, 0))
		smoke:moveTo(cf * CFrame.new(0, 4 * s, 1.5))
		if glow then
			glow.CFrame = cf * CFrame.new(0, 1.2 * s, 0)
			glow.Transparency = 0.6 + 0.4 * (1 - fx.fade)
		end
		if light then
			light.Parent.WorldCFrame = cf * CFrame.new(0, 3, 0)
			light.Brightness = 4 * Curves.flicker(t, fx.uid, 0.3) * fx.fade
		end
		if t - lastScorch > 0.35 and fx.detail >= 2 then
			lastScorch = t
			fx:groundDecal(pos, Wd * 0.6, "scorch", { transparency = 0.35, noRaycast = true })
		end
	end)
end

function W.earth(fx)
	local s = fx.scale
	local a, b = path(fx)
	local len = (b - a).Magnitude
	local unit = if len > 0.01 then (b - a).Unit else Vector3.zAxis
	local n = math.clamp(math.floor(len / (2.6 * s)), 3, ({ 6, 10, 14 })[fx.detail] or 10)
	local dur = fx.duration or 2
	for i = 1, n do
		local p = a + unit * (len * (i - 0.5) / n) + unit:Cross(Vector3.yAxis) * fx:rand(-0.8, 0.8) * s
		local size = fx:rand(1.6, 2.6) * s
		local rock = Common.rock(fx, size, CFrame.new(p), { colour = math.floor(fx:rand(3, 5.99)), material = "body", transparency = fx:alphaFor("body") })
		local final = CFrame.new(p + Vector3.new(0, size * 0.3, 0)) * rock.CFrame.Rotation
		local delay = (i - 1) / n * dur * 0.5
		Common.riser(fx, rock, final, size * 1.4, delay, 0.25)
		fx:after(delay, function()
			fx:emitter("dust", CFrame.new(p + Vector3.new(0, 0.5, 0)), { size = 0.8 }):emit(4)
		end)
	end
	fx.fadeOut = 0.6
end

return function(fx)
	local f = W[fx.entry.variant or "water"] or W.water
	f(fx)
end
