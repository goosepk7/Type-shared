--!nonstrict
-- Material / mood particles attached to a target (bare ids referenced by data/materials.json and accents).
-- LOD: every 0.5 s the camera distance is checked; beyond Near the rates halve, beyond Far everything pauses.

local Curves = require(script.Parent.Parent.Curves)
local Runtime = require(script.Parent.Parent.Runtime)

local NEAR, FAR = 60, 140

-- where: body (volume of the target), head, back, feet. colour = hex list override.
local SPEC = {
	drip_sauce = { preset = "drips", where = "body", rate = 4, colour = { "#D7261E", "#8E1410" } },
	drip_honey = { preset = "drips", where = "body", rate = 2, colour = { "#FFC23A", "#D98A14" }, life = 1.6 },
	goo_drip = { preset = "drips", where = "body", rate = 4, colour = { "#9DFF4A", "#3FAF1E" } },
	water_drip = { preset = "drips", where = "body", rate = 5 },
	ink_drip = { preset = "drips", where = "body", rate = 3, colour = { "#2A2A3A", "#0A0A12" } },
	sawdust = { preset = "flakes", where = "body", rate = 4, colour = { "#E8C99A", "#B98E5A" } },
	crumbs = { preset = "flakes", where = "body", rate = 3, colour = { "#D9A15E", "#9C6A35" } },
	sprinkles = { preset = "sprinkles", where = "body", rate = 3 },
	sparkle = { preset = "glints", where = "body", rate = 4 },
	glitter = { preset = "glitter", where = "body", rate = 6 },
	confetti = { preset = "confetti", where = "head", burst = 14, every = 1.6 },
	shards = { preset = "glints", where = "body", rate = 3, extra = "iceShards" },
	steam = { preset = "steam", where = "head", rate = 3, size = 0.35 },
	smoke = { preset = "smoke", where = "head", rate = 3, size = 0.45 },
	embers = { preset = "embers", where = "body", rate = 5 },
	sparks = { preset = "metalSparks", where = "body", burst = 8, every = 0.9, size = 0.5 },
	zap = { preset = "electric", where = "body", rate = 8 },
	frost = { preset = "frostMist", where = "body", rate = 4, size = 0.6 },
	snowflakes = { preset = "snow", where = "head", rate = 5, size = 0.8 },
	bubbles = { preset = "bubbles", where = "body", rate = 4 },
	petals = { preset = "petals", where = "body", rate = 2 },
	leaves = { preset = "leavesDrift", where = "body", rate = 2 },
	feathers = { preset = "feathers", where = "body", rate = 1 },
	fluff = { preset = "fluff", where = "body", rate = 2 },
	sand = { preset = "flakes", where = "body", rate = 6, colour = { "#E6CF9A", "#C9A86A" } },
	dust = { preset = "dust", where = "feet", rate = 1.5, size = 0.4 },
	coins = { preset = "coins", where = "body", rate = 3 },
	music_notes = { preset = "notes", where = "head", rate = 1.6 },
	hearts = { preset = "hearts", where = "head", rate = 1.5 },
	snore = { preset = "zzz", where = "head", rate = 0.8 },
	anger_steam = { preset = "steam", where = "head", burst = 4, every = 0.7, size = 0.3, colour = { "#FFFFFF", "#FFD6D6" } },
	sweat_drops = { preset = "drips", where = "head", rate = 2, colour = { "#CFEFFF", "#7FC6FF" } },
	stars = { preset = "stars", where = "head", rate = 3, size = 0.5 },
	question_marks = { preset = "questions", where = "head", rate = 1.2 },
	halo_glow = { preset = "halo", where = "head", size = 1 },
	thruster = { preset = "fire", where = "back", rate = 40, size = 0.5, speed = 4, dir = "Back", spread = { 6, 6 } },
	glitch = { preset = "pixels", where = "body", burst = 6, every = 0.25 },
	rainbow_trail = { trail = true },
	bees = { swarm = { count = { 2, 3, 4 }, colour = Color3.fromRGB(245, 196, 48), wing = true, speed = 3.2, radius = 1.4 } },
	flies = { swarm = { count = { 2, 3, 5 }, colour = Color3.fromRGB(30, 30, 34), wing = true, speed = 4.5, radius = 1.1, size = 0.6 } },
	butterflies = { swarm = { count = { 1, 2, 3 }, colour = Color3.fromRGB(255, 140, 200), flutter = true, speed = 1.4, radius = 1.8 } },
}

local RAINBOW = { "#FF4A4A", "#FF9F3A", "#FFE84A", "#5BE36B", "#4AB8FF", "#9A6BFF" }

local function offsetFor(where: string, size: Vector3): CFrame
	if where == "head" then
		return CFrame.new(0, size.Y * 0.5 + 0.4, 0)
	elseif where == "feet" then
		return CFrame.new(0, -size.Y * 0.5 + 0.2, 0)
	elseif where == "back" then
		return CFrame.new(0, 0, size.Z * 0.5)
	end
	return CFrame.new()
end

return function(fx)
	local id = fx.entry.variant
	local spec = SPEC[id] or SPEC.sparkle
	local target = fx.params.target
	local root = Runtime.rootPart(target)
	local size = if root then Runtime.extents(target) else Vector3.new(3, 3, 3) * fx.scale
	local where = root or fx:at()
	local w = math.max(size.X, size.Z)
	local emitters = {}
	local parts = {}

	if spec.preset then
		local opts = {
			rate = spec.rate or 0,
			size = (spec.size or 1) * math.max(0.6, w / 3),
			colour = spec.colour,
			offset = offsetFor(spec.where or "body", size),
			life = spec.life,
			speed = spec.speed,
			dir = spec.dir,
			spread = spec.spread,
		}
		if spec.where == "body" then
			opts.area = size * 0.85
		end
		local e = fx:emitter(spec.preset, where, opts)
		table.insert(emitters, e)
		if spec.burst then
			fx:every(spec.every or 1, function()
				if fx.lod ~= 0 then
					e:emit(spec.burst)
				end
			end, 0.1)
		end
		if spec.extra then
			local x = fx:emitter(spec.extra, where, { size = 0.4 })
			fx:every(1.2, function()
				if fx.lod ~= 0 then
					x:emit(3)
				end
			end)
		end
		if id == "thruster" then
			local flame = fx:part("Ellipsoid", Vector3.new(0.6, 0.6, 1.8) * math.max(0.6, w / 3), CFrame.new(), { colour = 2, material = "core", transparency = 0.3 })
			table.insert(parts, flame)
			local light = fx:light(where, fx:c(3), 2, 10)
			fx:onUpdate(function(_, t)
				local base = if root and root.Parent then root.CFrame else fx:at()
				local fl = Curves.flicker(t, fx.uid, 0.3)
				flame.CFrame = base * offsetFor("back", size) * CFrame.new(0, 0, 0.9 * fl)
				flame.Size = Vector3.new(0.6, 0.6, 1.8 * fl) * math.max(0.6, w / 3)
				flame.Transparency = if fx.lod == 0 then 1 else 0.3 + 0.7 * (1 - fx.fade)
				if light then
					light.Brightness = 2 * fl * fx.fade
				end
			end)
		elseif id == "glitch" and typeof(target) == "Instance" then
			local list = {}
			for _, d in target:GetDescendants() do
				if d:IsA("BasePart") then
					table.insert(list, d)
				end
			end
			fx:every(0.12, function()
				local on = fx:rand() < 0.25 and fx.lod ~= 0
				for _, p in list do
					p.LocalTransparencyModifier = if on then 0.6 else 0
				end
			end)
			fx:onCleanup(function()
				for _, p in list do
					if p.Parent then
						p.LocalTransparencyModifier = 0
					end
				end
			end)
		end
	elseif spec.trail and root then
		local seq = {}
		for i, h in RAINBOW do
			seq[i] = { (i - 1) / (#RAINBOW - 1), h }
		end
		fx:trail(root, math.max(1, w * 0.6), 0.6, { colourSeq = Runtime.colourSeq(seq), axis = Vector3.yAxis, lightEmission = 0.8 })
	elseif spec.swarm then
		local sw = spec.swarm
		local n = sw.count[fx.detail] or sw.count[2]
		local bugs = {}
		local bs = (sw.size or 1) * 0.45 * fx.scale
		for i = 1, n do
			local body = fx:part("Ellipsoid", Vector3.new(0.7, 0.6, 1) * bs, CFrame.new(), { colour = sw.colour, material = Enum.Material.SmoothPlastic, transparency = 0 })
			local wing = nil
			if sw.wing or sw.flutter then
				-- wing ellipsoid sits above the body, flatter and wider: surfaces meet only along curves
				wing = fx:part("Ellipsoid", (if sw.flutter then Vector3.new(2.2, 0.08, 1.2) else Vector3.new(1.4, 0.06, 0.6)) * bs, CFrame.new(), {
					colour = if sw.flutter then sw.colour else Color3.fromRGB(235, 245, 255),
					material = Enum.Material.SmoothPlastic,
					transparency = if sw.flutter then 0.1 else 0.45,
				})
			end
			table.insert(bugs, { body = body, wing = wing, phase = Curves.ring(i, n), seed = fx.uid * 10 + i })
			table.insert(parts, body)
			if wing then
				table.insert(parts, wing)
			end
		end
		fx:onUpdate(function(_, t)
			local c = if root and root.Parent then root.CFrame.Position + Vector3.new(0, size.Y * 0.3, 0) else fx:at().Position
			local hidden = fx.lod == 0
			for _, b in bugs do
				local nx = Curves.noise(t * sw.speed, b.seed) - 0.5
				local ny = Curves.noise(t * sw.speed * 1.3, b.seed + 7) - 0.5
				local ang = b.phase + t * sw.speed * 0.7
				local r = (sw.radius + nx) * math.max(1, w / 3)
				local pos = c + Vector3.new(math.cos(ang) * r, ny * 1.5, math.sin(ang) * r)
				local heading = Vector3.new(-math.sin(ang), 0, math.cos(ang))
				local cf = CFrame.lookAt(pos, pos + heading)
				b.body.CFrame = cf
				b.body.Transparency = if hidden then 1 else 0
				if b.wing then
					local flap = if sw.flutter then math.sin(t * 14 + b.phase) * 0.9 else math.sin(t * 60) * 0.5
					b.wing.CFrame = cf * CFrame.new(0, 0.32 * bs, 0) * CFrame.Angles(0, 0, flap)
					b.wing.Transparency = if hidden then 1 else (if sw.flutter then 0.1 else 0.45)
				end
			end
		end)
	end

	-- LOD by camera distance
	fx.lod = 1
	local function applyLod()
		local cam = Runtime.cameraPos()
		local pos = if root and root.Parent then root.CFrame.Position else fx:at().Position
		local d = if cam then (cam - pos).Magnitude else 0
		local lod = if d > FAR then 0 elseif d > NEAR then 0.5 else 1
		if lod ~= fx.lod then
			fx.lod = lod
			for _, e in emitters do
				e:setRate(e.baseRate * lod)
			end
			for _, p in parts do
				if lod == 0 then
					p.Transparency = 1
				end
			end
		end
	end
	applyLod()
	fx:every(0.5, applyLod, 0.5)
	fx.fadeOut = 0.3
end
