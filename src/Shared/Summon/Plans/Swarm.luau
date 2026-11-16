--!strict
-- Swarm: a buzzing cluster of small units (bees, bats, fireflies, locusts, fish schools, sparks...).
-- Each unit is 1-3 parts on its own bone so the animator can buzz/orbit them independently. The unit count
-- fills the part budget (more units at bigger sizes / counts).

local Geom = require(script.Parent.Parent.Geom)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local function unitKind(ctx: any): string
	local t, id = ctx.traits, string.lower(ctx.result.id)
	if string.find(id, "bat") then
		return "bat"
	elseif t.aquatic or t.swims or string.find(id, "fish") or string.find(id, "piranha") then
		return "fish"
	elseif string.find(id, "firefl") or string.find(id, "glowworm") or string.find(id, "lightning bug") then
		return "firefly"
	elseif string.find(id, "spark") or string.find(id, "ember") or string.find(id, "wisp") or t.element == "Light" then
		return "spark"
	elseif string.find(id, "bird") or string.find(id, "crow") or string.find(id, "pigeon") then
		return "bird"
	end
	return "bug"
end

-- One unit centred at p; returns parts used. tier 1 = hero (full detail, near the front), 2 = filler.
local function unit(B: any, kind: string, i: number, p: { number }, s: number, detail: number, tier: number, striped: boolean): number
	local bone = B:bone("Unit" .. i, "Body", p[1], p[2], p[3])
	B:addRig("units", { bone = bone, index = i })
	-- the swarm travels together: units face roughly forward (-Z) with a seeded spread, not every which way
	local yaw = ((i * 2.399) % 1.4) - 0.7
	local base = at(p[1], p[2], p[3], rad(((i * 37) % 21) - 10), yaw, 0)
	local pri = (if tier == 1 then 1 else 1.4) + i * 0.02
	if kind == "firefly" then
		-- a dark little beetle with a glowing lantern abdomen; the distant ones are just the lanterns
		if tier == 1 then
			B:ell(s * 0.42, s * 0.36, s * 0.62, Geom.mul(base, at(0, s * 0.05, -s * 0.28)), { col = "dark", mat = "hard", bone = bone, pri = pri, role = "body", name = "Bug" .. i })
		end
		-- far lanterns shrink with depth (three steps), so the cloud reads as a deep field of lights, not dots
		local k = if tier == 1 then 1 else ({ 0.9, 0.68, 0.5 })[i % 3 + 1]
		B:ell(s * 0.5 * k, s * 0.46 * k, s * 0.62 * k, Geom.mul(base, at(0, 0, s * 0.22)), { col = { 0.86, 1, 0.38 }, mat = "neon", glow = true, bone = bone, pri = pri + 0.02, role = "gem", name = "Lantern" .. i, noCore = true, trail = i <= 2 })
		return if tier == 1 then 2 else 1
	end
	if kind == "spark" then
		B:ball(s * (if tier == 1 then 0.75 else 0.5), base, { col = "glow", mat = "neon", glow = true, bone = bone, pri = pri, role = "gem", name = "Spark" .. i, noCore = true, trail = i <= 2 })
		return 1
	end
	if kind == "fish" then
		B:ell(s * 0.5, s * 0.75, s * 1.35, base, { col = "primary", mat = "skin", bone = bone, pri = pri, role = "body", name = "Fish" .. i })
		if tier == 1 or detail >= 3 then
			B:wedge(s * 0.08, s * 0.65, s * 0.5, Geom.mul(base, at(0, 0, s * 0.78, 0, 0, 0)), { col = "secondary", mat = "skin", bone = bone, pri = pri + 0.3, role = "fin", name = "Tail" .. i })
			return 2
		end
		return 1
	end
	if kind == "bat" or kind == "bird" then
		B:ell(s * 0.55, s * 0.6, s * 0.8, base, { col = "primary", mat = "fur", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		-- wings: one swept chevron-like flattened ellipsoid per unit, wide (the flock reads by its wing shapes)
		B:ell(s * 2.4, s * 0.08, s * 0.55, Geom.mul(base, at(0, s * 0.18, s * 0.08, rad(6), 0, 0)), { col = if kind == "bat" then "membrane" else "dark", mat = "skin", bone = bone, pri = pri + 0.05, role = "wing", name = "Wings" .. i, trail = tier == 1 and i <= 2 })
		return 2
	end
	-- insects: plump body; bees/wasps get black bands (thin discs whose rims stand proud of the body) and a
	-- translucent wing pair. Fillers keep body + one band so even the back of the cloud still says "bee".
	local slim = kind == "wasp"
	local bw, bl = s * (if slim then 0.5 else 0.62), s * (if slim then 1.15 else 1.0)
	B:ell(bw, bw, bl, base, { col = "primary", mat = "fur", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
	local used = 1
	local bands = if not striped then 0 elseif tier == 1 then 2 else 1
	for j = 1, bands do
		local z = bl * (if bands == 1 then 0.1 else (-0.08 + (j - 1) * 0.3))
		local k = math.sqrt(math.max(0.1, 1 - (z / (bl / 2)) ^ 2)) * 1.07
		B:ell(bw * k, bw * k, bl * 0.2, Geom.mul(base, at(0, 0, z)), { col = "black", mat = "fur", bone = bone, pri = pri + 0.04 + j * 0.01, role = "detail", name = "Band" .. i .. "_" .. j, needs = "Unit" .. i })
		used += 1
	end
	if tier == 1 or not striped then
		B:ell(s * 1.5, s * 0.06, s * 0.48, Geom.mul(base, at(0, bw * 0.5, -s * 0.05, rad(10), 0, 0)),
			{ col = "wingGlass", mat = "glass", tr = 0.35, bone = bone, pri = pri + 0.08, role = "wing", name = "Wings" .. i, needs = "Unit" .. i, trail = tier == 1 and i == 1 })
		used += 1
	end
	return used
end

return function(B: any, ctx: any)
	local detail = ctx.detail
	local kind = unitKind(ctx)
	local id = string.lower(ctx.result.id)
	local t = ctx.traits
	local beeish = t.stinger or string.find(id, "bee") ~= nil or string.find(id, "wasp") ~= nil or string.find(id, "hornet") ~= nil
	if kind == "bug" and (string.find(id, "wasp") or string.find(id, "hornet")) then
		kind = "wasp"
	end
	local striped = (kind == "bug" or kind == "wasp") and beeish
	local rng = B.rng
	B.boneIndex.Body.pos = { 0, 2.4, 0 }
	local avail = ctx.budget - (if ctx.style == "Spectral" then 3 else 0)
	-- heroes first (full detail), then fillers until the budget is spent: more, smaller units read as a cloud
	local heroCost = if kind == "firefly" then 2 elseif kind == "spark" then 1 elseif kind == "fish" then 2 elseif kind == "bat" or kind == "bird" then 2 elseif striped then 4 else 2
	local fillCost = if kind == "firefly" then 1 elseif kind == "spark" then 1 elseif kind == "fish" then 1 elseif kind == "bat" or kind == "bird" then 2 elseif striped then 2 else 2
	local heroes = if kind == "spark" then 2 elseif kind == "firefly" then 4 else math.clamp(math.floor(avail / 6), 1, 4)
	local fillers = math.clamp(math.floor((avail - heroes * heroCost) / fillCost), 2, 24)
	local n = heroes + fillers
	-- a squashed, slightly lumpy cloud (wider than tall, denser toward the middle); heroes sit at the front
	local s = if n > 10 then 0.62 else 0.72
	for i = 1, n do
		local tier = if i <= heroes then 1 else 2
		local u = (i - 0.5) / n
		local yy = 1 - 2 * u
		local r = math.sqrt(1 - yy * yy)
		local th = i * 2.39996
		local R = (if tier == 1 then 1.5 else 1.9) * rng:jitter(1, 0.22) * (0.75 + 0.25 * r)
		local p = { cos(th) * r * R, 2.4 + yy * 1.15 * rng:jitter(1, 0.15), sin(th) * r * R }
		if tier == 1 then
			p = { (i - (heroes + 1) / 2) * 1.2, 2.4 + ((i % 2) - 0.5) * 0.7, -1.4 - (i % 2) * 0.4 }
		end
		unit(B, kind, i, p, s * rng:jitter(1, 0.12) * (if tier == 1 then 1.15 else 1), detail, tier, striped)
	end
	if kind ~= "spark" and kind ~= "fish" and kind ~= "firefly" then
		-- drifting specks around the cloud sell the density the part budget cannot
		B:emit("dust", nil, { socket = "core", rate = 24, spread = 1.6 })
	end
	B:socket("core", at(0, 2.4, 0), "Body")
	B:setRig("gait", "swarm")
end
