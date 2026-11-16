--!nonstrict
-- Projectiles: bolt, orb, arrow, shard, bubble (straight/homing), boulder (lobbed arc), meteor/comet (from the sky).
-- Every projectile ends by playing its impact (params.impact = false to skip, or an effect id to override).

local Curves = require(script.Parent.Parent.Curves)
local Common = require(script.Parent.Common)

local Palettes = require(script.Parent.Parent.Palettes)

local function Palettes_secondary(fx): string
	return Palettes.elementFx(fx.element).secondary
end

local function Fx_pos(v): Vector3?
	if typeof(v) == "Vector3" then
		return v
	elseif typeof(v) == "CFrame" then
		return v.Position
	elseif typeof(v) == "Instance" then
		if v:IsA("BasePart") then
			return v.CFrame.Position
		elseif v:IsA("Model") then
			return v:GetPivot().Position
		end
	end
	return nil
end

local SPEED = { bolt = 95, orb = 38, arrow = 75, shard = 85, bubble = 30, meteor = 75, comet = 95, boulder = 0 }

local function defaultImpact(fx, variant: string): string?
	if variant == "meteor" then
		return "explosion.huge"
	elseif variant == "comet" then
		return "explosion.small"
	elseif variant == "boulder" then
		return "impact.earth"
	elseif variant == "bubble" then
		return "burst.splash"
	end
	return Common.impactId(fx.element)
end

-- Builds the visual body. Returns the root part (moved every frame) and an optional per-frame animator.
local function buildBody(fx, variant: string)
	local s = fx.scale
	local spectral = fx:spectral()
	local anim = nil
	local root
	if variant == "bolt" then
		root = fx:part("Ellipsoid", Vector3.new(0.55, 0.55, 2.6) * s, CFrame.new(), { colour = 1, material = "core", transparency = 0 })
		local shell = fx:part("Ellipsoid", Vector3.new(1.3, 1.3, 4.2) * s, CFrame.new(), { colour = 3, material = "shell", transparency = if spectral then 0.55 else 0.6 })
		fx:emitter(Palettes_secondary(fx), root, { rate = 26 })
		fx:emitter("coreGlow", root, { size = 0.8 })
		fx:trail(root, 0.9, 0.22, { colour = { 1, 3, 4 } })
		fx:light(root, fx:c(2), 3, 12)
		anim = function(cf, t)
			shell.CFrame = cf
			local wob = 1 + 0.08 * math.sin(t * 40)
			shell.Size = Vector3.new(1.3 * wob, 1.3 * wob, 4.2) * s
		end
	elseif variant == "orb" then
		root = fx:part("Ball", Vector3.one * 1.2 * s, CFrame.new(), { colour = 1, material = "core", transparency = 0 })
		local shells = fx:shells(CFrame.new(), 1.0 * s, 2, { ratio = 1.45, colours = { 2, 3 }, alphas = { 0.45, 0.72 }, materials = { "shell", "shell" } })
		fx:emitter("motes", root, { rate = 14, speed = 1.5 })
		fx:emitter(Palettes_secondary(fx), root, { rate = 10 })
		fx:trail(root, 1.6, 0.35, { colour = { 2, 3, 5 } })
		fx:light(root, fx:c(2), 2.5, 14)
		anim = function(cf, t)
			local pulse = 1 + 0.12 * math.sin(t * 9)
			shells[1].CFrame = cf
			shells[1].Size = Vector3.one * 2 * s * pulse
			shells[2].CFrame = cf * CFrame.Angles(t * 2, t * 3, 0)
			shells[2].Size = Vector3.one * 2.9 * s * (2 - pulse) -- counter-pulse; always > shell 1 * 1.25
		end
	elseif variant == "arrow" then
		local spectralShaft = if spectral then "core" else "body"
		root = fx:part("Cylinder", Vector3.new(3.2, 0.16, 0.16) * s, CFrame.new(), { colour = if spectral then 2 else 4, material = spectralShaft, transparency = if spectral then 0.1 else 0 })
		local head = fx:part("Block", Vector3.new(0.42, 0.42, 0.8) * s, CFrame.new(), { colour = 1, material = "core", transparency = 0 })
		local f1 = fx:part("Block", Vector3.new(0.04, 0.55, 0.7) * s, CFrame.new(), { colour = 3, material = "shell", transparency = if spectral then 0.35 else 0 })
		-- second vane is shorter so the crossed vanes' front/back faces sit on different planes
		local f2 = fx:part("Block", Vector3.new(0.55, 0.04, 0.62) * s, CFrame.new(), { colour = 3, material = "shell", transparency = if spectral then 0.35 else 0 })
		fx:trail(head, 0.35, 0.18, { colour = { 1, 3 } })
		if spectral then
			fx:emitter("motes", head, { rate = 12 })
		end
		anim = function(cf)
			-- the shaft cylinder's axis is X: turn it to the travel axis (Z)
			root.CFrame = cf * CFrame.Angles(0, math.pi / 2, 0)
			head.CFrame = cf * CFrame.new(0, 0, -1.75 * s) * CFrame.Angles(0, 0, math.pi / 4)
			f1.CFrame = cf * CFrame.new(0, 0, 1.3 * s)
			f2.CFrame = cf * CFrame.new(0, 0, 1.3 * s)
		end
		return root, anim, true
	elseif variant == "shard" then
		root = fx:part("Block", Vector3.new(0.55, 0.55, 2.4) * s, CFrame.new(), { colour = 2, material = "core", transparency = if spectral then 0.1 else fx:alphaFor("core") })
		local glow = fx:part("Ellipsoid", Vector3.new(1.2, 1.2, 3.4) * s, CFrame.new(), { colour = 3, material = "shell", transparency = 0.7 })
		fx:trail(root, 0.6, 0.2, { colour = { 1, 2, 4 } })
		fx:emitter("glints", root, { rate = 10 })
		anim = function(cf, t)
			root.CFrame = cf * CFrame.Angles(0, 0, t * 14) * CFrame.Angles(0, 0, math.pi / 4)
			glow.CFrame = cf
		end
		return root, anim, true
	elseif variant == "bubble" then
		root = fx:part("Ellipsoid", Vector3.one * 2.2 * s, CFrame.new(), {
			colour = 2,
			material = if spectral then Enum.Material.ForceField else Enum.Material.Glass,
			transparency = if spectral then 0 else 0.55,
			reflectance = if spectral then 0 else 0.25,
		})
		local inner = fx:part("Ball", Vector3.one * 0.7 * s, CFrame.new(), { colour = 1, material = "core", transparency = 0.5 })
		fx:emitter("bubbles", root, { rate = 8 })
		anim = function(cf, t)
			local w = math.sin(t * 11) * 0.12
			root.CFrame = cf
			local mesh = root:FindFirstChildOfClass("SpecialMesh")
			if mesh then
				mesh.Scale = Vector3.new(1 + w, 1 - w, 1 + w * 0.5)
			end
			inner.CFrame = cf * CFrame.new(-0.35 * s, 0.4 * s, 0)
		end
		return root, anim, false
	elseif variant == "meteor" or variant == "comet" then
		local big = variant == "meteor"
		local r = (if big then 2.6 else 0.9) * s
		root = fx:part("Ball", Vector3.one * 2 * r, CFrame.new(), {
			colour = if spectral then 2 else 5,
			material = if spectral then "core" else Enum.Material.Basalt,
			transparency = 0,
		})
		-- glowing heat cap on the leading side + long tail; ellipsoids around a ball never share a surface
		local cap = fx:part("Ellipsoid", Vector3.new(2.5, 2.5, 2.9) * r, CFrame.new(), { colour = if spectral then 1 else 3, material = "shell", transparency = if spectral then 0.6 else 0.45 })
		local tail = fx:part("Ellipsoid", Vector3.new(1.9, 1.9, 7) * r, CFrame.new(), { colour = 3, material = "shell", transparency = 0.6 })
		fx:emitter("fire", root, { rate = if big then 46 else 20, size = r / 1.2, speed = 0.4 })
		fx:emitter("smoke", root, { rate = if big then 16 else 0, size = r / 1.3 })
		fx:emitter("embers", root, { rate = 18, speed = 2 })
		fx:trail(root, 2 * r, if big then 0.6 else 0.4, { colour = { 1, 2, 4 } })
		fx:light(root, fx:c(2), if big then 5 else 3, if big then 30 else 16)
		anim = function(cf, t)
			root.CFrame = cf * CFrame.Angles(t * 2, t * 3, 0)
			cap.CFrame = cf * CFrame.new(0, 0, -0.35 * r)
			tail.CFrame = cf * CFrame.new(0, 0, 3.3 * r)
			local fl = Curves.flicker(t, fx.uid, 0.15)
			tail.Size = Vector3.new(1.9 * fl, 1.9 * fl, 7) * r
		end
		return root, anim, false
	elseif variant == "boulder" then
		root = Common.rock(fx, 2.6 * s, CFrame.new(), { colour = if spectral then 3 else 4, material = "body", transparency = if spectral then 0.15 else 0 })
		local second = Common.rock(fx, 1.8 * s, CFrame.new(), { colour = if spectral then 2 else 3, material = "body", transparency = if spectral then 0.15 else 0 })
		local spin = root.CFrame.Rotation
		local spin2 = second.CFrame.Rotation
		fx:emitter("dust", root, { rate = 6, size = 0.6 })
		anim = function(cf, t)
			root.CFrame = CFrame.new(cf.Position) * spin * CFrame.Angles(t * 5, t * 3, 0)
			second.CFrame = root.CFrame * CFrame.new(0.6 * s, 0.35 * s, 0.2 * s) * spin2
		end
		return root, anim, false
	end
	return root, anim, true
end

return function(fx)
	local variant = fx.entry.variant or "bolt"
	local s = fx.scale
	local params = fx.params
	local to = fx:to()
	local from
	if variant == "meteor" or variant == "comet" then
		local g = fx:ground(to)
		to = g
		local dir = Vector3.new(fx:rand(-1, 1), 0, fx:rand(-1, 1))
		dir = if dir.Magnitude > 0.1 then dir.Unit else Vector3.xAxis
		from = Fx_pos(params.from) or (to + dir * (if variant == "meteor" then 70 else 40) * s + Vector3.new(0, (if variant == "meteor" then 140 else 90) * s, 0))
	else
		from = fx:from()
	end
	local speed = (params.speed or SPEED[variant] or 80)
	local dist = (to - from).Magnitude
	local flight = if variant == "boulder" then 0.9 + dist / 70 else math.max(0.12, dist / speed)
	local arcHeight = if variant == "boulder" then math.max(6, dist * 0.35) elseif variant == "arrow" then dist * 0.06 else 0

	local root, anim, alignsToPath = buildBody(fx, variant)
	fx.fadeOut = 0.05

	-- Landing cues: meteors and lobbed rocks show a growing shadow + warning ring where they will land.
	local shadow, warn
	if variant == "meteor" or variant == "comet" or variant == "boulder" then
		local landing = fx:ground(to)
		shadow = fx:groundDecal(landing, 4 * s, "shadow", { discFallback = true, colour = Color3.new(0, 0, 0), transparency = 0.9, noRaycast = true })
		if variant ~= "boulder" then
			warn = fx:groundDecal(landing, (if variant == "meteor" then 18 else 8) * s, "ring", { colour = 3, transparency = 0.6, noRaycast = true })
		end
	end

	local start = fx.t
	local landed = false
	local pos = from
	local lastPos = from
	local wobblePhase = fx:rand(0, 6.28)
	fx:onUpdate(function(_, t)
		if landed then
			return
		end
		local k = (t - start) / flight
		local target = fx:to()
		if variant == "meteor" or variant == "comet" or variant == "boulder" then
			target = to -- committed landing point
		end
		if variant == "orb" or variant == "bubble" or variant == "bolt" or variant == "shard" then
			-- homing: step toward the live target at constant speed
			local d = target - pos
			local step = speed * (1 / 60)
			if fx.lastT then
				step = speed * (t - fx.lastT)
			end
			fx.lastT = t
			if d.Magnitude <= step then
				pos = target
				k = 1
			else
				pos += d.Unit * step
				k = 0
			end
			if variant == "orb" or variant == "bubble" then
				local side = if d.Magnitude > 0.01 then d.Unit:Cross(Vector3.yAxis) else Vector3.xAxis
				pos += side * math.sin(t * 6 + wobblePhase) * 0.04 * s + Vector3.new(0, math.cos(t * 5 + wobblePhase) * 0.03 * s, 0)
			end
		else
			local e = if variant == "meteor" or variant == "comet" then Curves.inQuad(k) * 0.35 + k * 0.65 else k
			pos = from:Lerp(target, math.clamp(e, 0, 1)) + Vector3.new(0, Curves.arc(k, arcHeight), 0)
		end
		local dir = pos - lastPos
		if dir.Magnitude < 1e-4 then
			dir = target - pos
		end
		lastPos = pos
		local cf = Common.look(pos, dir)
		if anim then
			anim(cf, t)
			if alignsToPath and variant ~= "arrow" and variant ~= "shard" then
				root.CFrame = cf
			end
		else
			root.CFrame = cf
		end
		if shadow then
			local kk = math.clamp(k, 0, 1)
			shadow:set(0.9 - 0.55 * kk, (4 + 10 * kk) * s * (if variant == "comet" then 0.5 else 1))
		end
		if warn then
			local pulse = Curves.pulse(t, 2.5)
			warn:set(0.85 - 0.35 * pulse * math.clamp(k * 2, 0, 1))
		end
		if k >= 1 then
			landed = true
			local impact = params.impact
			if impact == nil then
				impact = defaultImpact(fx, variant)
			end
			if impact then
				fx:child(impact, {
					at = CFrame.new(pos),
					element = fx.element,
					colour = params.colour,
					scale = params.impactScale or (s * (if variant == "orb" then 1.2 elseif variant == "comet" then 0.6 else 1)),
					style = fx.style,
					priority = params.priority,
				})
				-- the child must outlive this projectile: detach it from the stop cascade
				table.remove(fx.children)
			end
			if params.onHit then
				task.spawn(params.onHit, pos)
			end
			fx:stop()
		end
	end)
end

