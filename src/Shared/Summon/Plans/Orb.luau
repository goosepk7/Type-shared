--!strict
-- Orbs: energy orb/fireball (layered core + shells + orbiting motes), planet (+ ring), sun/star (corona
-- spikes), moon (craters), black hole (dark core + accretion disc), bubble, Ball (sports balls) and Crystal
-- (faceted shard cluster). Shells always use distinct radii, so no two curved surfaces coincide.

local Geom = require(script.Parent.Parent.Geom)
local Heads = require(script.Parent.Parent.Heads)
local Face = require(script.Parent.Parent.Face)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local function kindOf(ctx: any): string
	if ctx.kind == "Ball" then
		return "ball"
	elseif ctx.kind == "Crystal" then
		return "crystal"
	end
	local t, id = ctx.traits, string.lower(ctx.result.id)
	local function has(w: string): boolean
		return string.find(id, "%f[%a]" .. w) ~= nil
	end
	if has("black hole") or has("vortex") and t.space then
		return "blackhole"
	elseif has("earth") and (t.space or ctx.result.category == "Place") or has("world") then
		return "earth"
	elseif t.planet or has("planet") or has("saturn") or has("jupiter") or has("world") then
		return "planet"
	elseif t.sun or has("sun") or has("star") or has("supernova") or has("red giant") or has("dwarf") then
		return "sun"
	elseif has("meteor") or has("comet") or has("bolide") or has("fireball") or has("fire orb") or has("fire ball") or has("lava bomb") then
		return "fireball"
	elseif t.moon or has("moon") then
		return "moon"
	elseif has("bubble") then
		return "bubble"
	elseif (has("ball") and not has("ball lightning") and ctx.result.category ~= "Element") or has("football") or has("soccer") or has("basketball") or has("baseball") or has("bowling") or has("beach") then
		return "ball"
	elseif has("crystal") or has("gem") or has("diamond") or has("ruby") or has("emerald") or has("sapphire") or has("shard") then
		return "crystal"
	elseif ctx.result.category == "Food" then
		return "food"
	elseif has("bomb") or has("grenade") or has("nuke") or has("landmine") or has("dynamite") or has("c4") then
		return "bomb"
	elseif has("rock") or has("boulder") or has("stone") or has("pebble") then
		return "boulder"
	end
	-- energy orbs take their look from the element: every element has its own silhouette
	local el = ctx.result.element
	if el == "Fire" then
		return "fireball"
	elseif el == "Lightning" then
		return "plasma"
	elseif el == "Ice" then
		return "frost"
	elseif el == "Earth" then
		return "boulder"
	elseif el == "Shadow" or el == "Poison" then
		return "void"
	elseif el == "Water" then
		return "bubble"
	end
	return "orb"
end

local function face(B: any, ctx: any, c: { number }, r: number, force: boolean?)
	if force or Heads.wantsFace(B, ctx.traits) then
		Face.build(B, { face = { kind = "ellipsoid", c = c, r = { r, r, r } }, bone = "Body", mood = ctx.result.mood, detail = math.max(1, ctx.detail),
			kind = "cute", spacing = r * 0.36, y = r * 0.15, d = r * 0.38, mouthY = -r * 0.28, mouthW = r * 0.6, forceMouth = true })
	end
end

local K = {}

-- Point on a sphere of radius R around (0, y, 0): longitude a (0 = facing -Z), latitude b.
local function onSphere(R: number, y: number, a: number, b: number): ({ number }, number, number)
	return { sin(a) * cos(b) * R, y + sin(b) * R, -cos(a) * cos(b) * R }, a, b
end

-- Thin lens sunk into a sphere's surface (craters, continents, rune marks): faces outward along the normal.
local function lens(B: any, R: number, y: number, a: number, b: number, w: number, h: number, depth: number, o: any)
	local p = onSphere(R - depth * 0.3, y, a, b)
	local f = at(p[1], p[2], p[3], b, -a, 0)
	local spec = table.clone(o)
	spec.shape, spec.size, spec.cf = "Ellipsoid", { w, h, depth }, f
	return B:part(spec)
end

-- Ring of motes on their own rotor bone (they orbit in the animator).
local function motes(B: any, n: number, R: number, y: number, col: string, size: number, pri: number)
	B:bone("Motes", "Body", 0, y, 0)
	B:addRig("rotors", { bone = "Motes", axis = "Y", speed = 2.5 })
	for i = 1, n do
		local a = (i - 1) / n * math.pi * 2
		B:ball(size, at(sin(a) * R, y + cos(a * 2) * R * 0.2, cos(a) * R), { col = col, mat = "neon", glow = true, bone = "Motes", pri = pri + i * 0.08, role = "gem", name = "Mote" .. i, trail = i <= 2, noCore = true })
	end
end

-- MAGIC ORB (arcane, light, wind, nature, abstract spells): glowing core with a bright hot spot, glass shell,
-- two crossed rune bands like a gyroscope, swirling wisps inside, orbiting motes.
function K.orb(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.4
	B:ball(1.9, at(0, y, 0), { col = "glow", mat = "neon", glow = true, pri = 1, role = "core", name = "Core", noCore = true })
	B:ball(3.0, at(0, y, 0), { col = "primary", mat = "glass", tr = 0.45, pri = 1.1, role = "shell", name = "Shell", noCore = true })
	B:ball(0.8, at(-0.32, y + 0.38, -0.55), { col = "flameCore", mat = "neon", glow = true, pri = 1.2, role = "core", name = "HotSpot", noCore = true })
	if detail >= 1 then
		-- a dashed rune ring orbiting at a tilt: short curved glyph segments with gaps (a hollow ring, not a disc)
		B:bone("Runes", "Body", 0, y, 0)
		B:addRig("rotors", { bone = "Runes", axis = "Y", speed = -1.2 })
		local tilt = at(0, y, 0, rad(24), 0, rad(-12))
		local n = if detail >= 3 then 7 elseif detail == 2 then 6 else 4
		local Rr = 2.15
		for i = 1, n do
			local a0 = (i - 1) / n * math.pi * 2
			local a1 = a0 + math.pi * 2 / n * 0.62
			local px, py, pz = Geom.point(tilt, sin(a0) * Rr, 0, cos(a0) * Rr)
			local qx, qy, qz = Geom.point(tilt, sin(a1) * Rr, 0, cos(a1) * Rr)
			B:limb({ px, py, pz }, { qx, qy, qz }, 0.16, { col = "secondary", mat = "neon", glow = true, bone = "Runes", pri = 1.3 + i * 0.03, role = "ring", name = "Rune" .. i, noCore = true, depth = 0.1, trail = i == 1 }, 0.05)
		end
	end
	if detail >= 2 then
		-- inner swirl: two curved wisps chasing each other inside the glass
		for i = 1, 2 do
			local a = i * math.pi
			B:ell(1.9, 0.26, 0.7, at(sin(a) * 0.55, y + (i - 1.5) * 0.5, cos(a) * 0.55, rad(20 * i), a + rad(30), rad(-25)), { col = "secondary", mat = "neon", glow = true, tr = 0.25, pri = 1.6 + i * 0.05, role = "gem", name = "Swirl" .. i, noCore = true })
		end
		B:ell(3.75, 3.6, 3.75, at(0, y, 0), { col = "glow", mat = "glass", tr = 0.78, pri = 2.2, role = "shell", name = "Aura", noCore = true })
	end
	if ctx.result.element == "Light" and detail >= 1 then
		B:ell(2.4, 0.16, 2.4, at(0, y + 2.05, 0, rad(-12), 0, 0), { col = "gold", mat = "neon", glow = true, pri = 1.45, role = "ring", name = "Halo", noCore = true })
	end
	motes(B, if detail <= 1 then 2 elseif detail == 2 then 3 else 5, 2.45, y, "secondary", 0.42, 1.4)
	B:emit("wisps", "Core", { socket = "core", rate = 20 })
	table.insert(B.lights, { kind = "PointLight", colour = { 0.8, 0.7, 1 }, brightness = 1.5, range = 1.5, socket = "core", shadows = false })
	face(B, ctx, { 0, y, 0 }, 1.5)
end

-- FIREBALL / METEOR / COMET: white-hot core inside nested flame shells (strictly growing radii), flame licks
-- streaming back off the rear hemisphere, and a tapering trail behind (it flies toward -Z).
function K.fireball(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.4
	local id = string.lower(ctx.result.id)
	local rocky = string.find(id, "meteor") ~= nil or string.find(id, "bolide") ~= nil or string.find(id, "lava") ~= nil
	local hot, mid, deep = "flameCore", "flame", { 0.86, 0.2, 0.05 }
	if rocky then
		-- meteor: a dark faceted rock leading, wrapped in fire
		B:block(2.2, 2.0, 2.3, at(0, y, -0.25, rad(23), rad(31), rad(12)), { col = "darkStone", mat = "stone", pri = 1, role = "body", name = "Rock" })
		B:block(1.9, 2.1, 1.8, at(0.1, y - 0.05, -0.2, rad(-17), rad(-8), rad(37)), { col = "stone", mat = "stone", pri = 1.05, role = "body", name = "Rock2" })
		B:ell(2.5, 2.5, 2.9, at(0, y, 0.35), { col = mid, mat = "neon", glow = true, tr = 0.35, pri = 1.1, role = "core", name = "Blaze", noCore = true })
	else
		B:ball(1.5, at(0, y, -0.1), { col = hot, mat = "neon", glow = true, pri = 1, role = "core", name = "Core", noCore = true })
		B:ball(2.3, at(0, y, 0), { col = mid, mat = "neon", glow = true, tr = 0.3, pri = 1.05, role = "core", name = "Flame", noCore = true })
		B:ell(3.0, 3.0, 3.35, at(0, y, 0.18), { col = deep, mat = "neon", glow = true, tr = 0.62, pri = 1.1, role = "shell", name = "Heat", noCore = true })
	end
	-- flame licks: teardrops from the rear hemisphere, curling back and outward, alternating colours
	local n = if detail <= 0 then 3 elseif detail == 1 then 4 elseif detail == 2 then 5 else 6
	for i = 1, n do
		local a = (i - 1) / n * math.pi * 2 + 0.3
		local cx, cy = sin(a), cos(a)
		local p0 = { cx * 0.9, y + cy * 0.9, 0.35 }
		local p1 = { cx * 1.5, y + cy * 1.35 + 0.45, 2.7 + (i % 2) * 0.7 }
		B:limb(p0, p1, 0.7 - (i % 2) * 0.14, { col = if i % 2 == 0 then mid else deep, mat = "neon", glow = true, tr = 0.15 + (i % 2) * 0.12, pri = 1.25 + i * 0.04, role = "spike", name = "Lick" .. i, trail = i == 1, noCore = true, depth = 0.55 }, 0.1)
	end
	-- trail: tapering, fading blobs behind
	local k = if detail <= 1 then 1 else 2
	for i = 1, k do
		local z = 2.2 + i * 1.5
		local d = 2.0 - i * 0.55
		B:ell(d, d, d * 1.8, at(0, y + i * 0.15, z), { col = if i == 1 then mid else deep, mat = "neon", glow = true, tr = 0.4 + i * 0.12, pri = 1.5 + i * 0.1, role = "tail", name = "Trail" .. i, trail = i == k, noCore = true })
	end
	B:emit("embers", nil, { socket = "core", rate = 30 })
	table.insert(B.lights, { kind = "PointLight", colour = { 1, 0.6, 0.25 }, brightness = 2.2, range = 1.6, socket = "core", shadows = false })
	face(B, ctx, { 0, y, -0.1 }, if rocky then 1.15 else 1.15)
end

-- PLANET: rocky sphere, latitude bands as separate shells just proud of the surface (each band's radii follow the
-- sphere at its latitude, x1.035), sunk craters, and two nested ring discs (different radii and thicknesses).
function K.planet(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.6
	local R = 1.8
	local id = string.lower(ctx.result.id)
	local ringed = not (string.find(id, "mercury") or string.find(id, "venus") or string.find(id, "mars") or string.find(id, "pluto") or string.find(id, "io"))
	B:ball(R * 2, at(0, y, 0), { col = "primary", mat = "stone", pri = 1, role = "body", name = "Planet" })
	local bands = if detail >= 2 then { 0.62, -0.42 } else { 0.5 }
	for i, by in bands do
		local k = math.sqrt(1 - (by / R) ^ 2) * 1.035
		B:ell(R * 2 * k, 0.5 - i * 0.08, R * 2 * k, at(0, y + by, 0), { col = if i == 1 then "secondary" else "dark", mat = "stone", pri = 1.3 + i * 0.05, role = "detail", name = "Band" .. i })
	end
	if detail >= 2 then
		for i = 1, (if detail >= 3 then 3 else 2) do
			lens(B, R, y, -0.55 + i * 0.5, -0.05 - (i % 2) * 0.3, 0.62 - i * 0.08, 0.62 - i * 0.08, 0.28, { col = "darker", mat = "stone", pri = 1.6 + i * 0.05, role = "detail", name = "Crater" .. i })
		end
	end
	if ringed then
		B:bone("Ring", "Body", 0, y, 0)
		B:addRig("rotors", { bone = "Ring", axis = "Y", speed = 0.6 })
		local tilt = at(0, y, 0, rad(16), rad(20), rad(-10))
		B:ell(7.6, 0.07, 7.6, tilt, { col = "light", mat = "glass", tr = 0.2, bone = "Ring", pri = 1.1, role = "ring", name = "RingOuter" })
		B:ell(5.9, 0.12, 5.9, tilt, { col = "secondary", mat = "glass", tr = 0.1, bone = "Ring", pri = 1.2, role = "ring", name = "RingInner" })
	end
	if detail >= 3 then
		B:ball(0.7, at(4.2, y + 0.9, 0.8), { col = "light", mat = "stone", bone = if ringed then "Ring" else "Body", pri = 2.4, role = "detail", name = "Moonlet" })
	end
	face(B, ctx, { 0, y, 0 }, R)
end

-- EARTH / WORLD: ocean sphere, continents sunk into it, an ice cap, and a thin glass atmosphere shell.
function K.earth(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.6
	local R = 1.8
	B:ball(R * 2, at(0, y, 0), { col = { 0.16, 0.45, 0.86 }, mat = "plastic", pri = 1, role = "body", name = "Ocean" })
	local land = { { -0.5, 0.35, 1.3, 1.0 }, { 0.65, -0.25, 1.0, 1.25 }, { 2.4, 0.2, 1.4, 0.9 } }
	for i = 1, (if detail >= 2 then 3 else 2) do
		local l = land[i]
		lens(B, R, y, l[1], l[2], l[3], l[4], 0.36, { col = { 0.3, 0.68, 0.3 }, mat = "plastic", pri = 1.2 + i * 0.05, role = "detail", name = "Land" .. i })
	end
	local cap = math.sqrt(1 - (1.55 / R) ^ 2) * 2 * R * 1.04
	B:ell(cap, 0.4, cap, at(0, y + 1.55, 0), { col = "white", mat = "plastic", pri = 1.4, role = "detail", name = "IceCap" })
	if detail >= 2 then
		B:ball(R * 2.24, at(0, y, 0), { col = { 0.6, 0.85, 1 }, mat = "glass", tr = 0.78, pri = 1.7, role = "shell", name = "Atmosphere", noCore = true })
	end
	face(B, ctx, { 0, y, 0 }, R)
end

-- SUN / STAR: neon core, a translucent corona shell, alternating long and short rays on a slow rotor.
function K.sun(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.6
	B:ball(3.4, at(0, y, 0), { col = "gold", mat = "neon", glow = true, pri = 1, role = "core", name = "Sun", noCore = true })
	if detail >= 1 then
		B:ball(4.1, at(0, y, 0), { col = "flame", mat = "neon", glow = true, tr = 0.6, pri = 1.4, role = "shell", name = "Corona", noCore = true })
	end
	B:bone("Corona", "Body", 0, y, 0)
	B:addRig("rotors", { bone = "Corona", axis = "Z", speed = 0.8 })
	local n = if detail <= 1 then 6 elseif detail == 2 then 8 else 10
	for i = 1, n do
		local a = (i - 1) / n * math.pi * 2
		local long = i % 2 == 1
		local h = if long then 1.5 else 0.95
		B:wedge(0.24, h, 0.9, Geom.mul(at(0, y, 0.08 * (i % 3), 0, 0, a), at(0, 1.95 + h * 0.3, 0, 0, rad(90), 0)), { col = if long then "flame" else "gold", mat = "neon", glow = true, bone = "Corona", pri = 1.3 + i * 0.02, role = "spike", name = "Ray" .. i, noCore = true })
	end
	table.insert(B.lights, { kind = "PointLight", colour = { 1, 0.85, 0.5 }, brightness = 2, range = 1.5, socket = "core", shadows = false })
	face(B, ctx, { 0, y, 0 }, 1.7, true)
end

-- PLASMA / BALL LIGHTNING: white core in a glass shell, zig-zag arcs crawling over it, sparks.
function K.plasma(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.4
	B:ball(1.5, at(0, y, 0), { col = "flameCore", mat = "neon", glow = true, pri = 1, role = "core", name = "Core", noCore = true })
	B:ball(3.0, at(0, y, 0), { col = "primary", mat = "glass", tr = 0.55, pri = 1.1, role = "shell", name = "Shell", noCore = true })
	B:bone("Arcs", "Body", 0, y, 0)
	B:addRig("rotors", { bone = "Arcs", axis = "Y", speed = 4 })
	local arcs = if detail <= 1 then 2 else 3
	for i = 1, arcs do
		local a = (i - 1) / arcs * math.pi * 2
		local pts = {}
		for j = 0, 3 do
			local b = rad(-50 + j * 33)
			local r = 1.55 + (j % 2) * 0.55
			table.insert(pts, { sin(a + j * 0.3) * cos(b) * r, y + sin(b) * r, cos(a + j * 0.3) * cos(b) * r })
		end
		for j = 1, (if detail >= 2 then 3 else 2) do
			B:rod(pts[j], pts[j + 1], 0.13, { col = "glow", mat = "neon", glow = true, bone = "Arcs", pri = 1.25 + i * 0.05 + j * 0.1, role = "spike", name = "Arc" .. i .. "_" .. j, trail = j == 1 and i == 1, noCore = true }, 0.06)
		end
	end
	if detail >= 2 then
		B:ell(3.45, 3.45, 3.45, at(0, y, 0), { col = "glow", mat = "glass", tr = 0.8, pri = 2.2, role = "shell", name = "Aura", noCore = true })
	end
	B:emit("sparks", "Core", { socket = "core", rate = 30 })
	table.insert(B.lights, { kind = "PointLight", colour = { 0.75, 0.85, 1 }, brightness = 2, range = 1.5, socket = "core", shadows = false })
	face(B, ctx, { 0, y, 0 }, 1.5)
end

-- FROST ORB: pale core, icy glass shell, diamond-section ice spikes radiating out.
function K.frost(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.4
	B:ball(1.7, at(0, y, 0), { col = "flameCore", mat = "neon", glow = true, pri = 1, role = "core", name = "Core", noCore = true })
	B:ball(3.0, at(0, y, 0), { col = "glass", mat = "ice", tr = 0.35, pri = 1.1, role = "shell", name = "Shell", noCore = true })
	local n = if detail <= 1 then 4 elseif detail == 2 then 6 else 8
	for i = 1, n do
		local a = i * 2.39996
		local b = math.asin(1 - 2 * (i - 0.5) / n) * 0.85
		local d = { sin(a) * cos(b), sin(b), -cos(a) * cos(b) }
		local p0 = { d[1] * 1.15, y + d[2] * 1.15, d[3] * 1.15 }
		local reach = 2.15 + (i % 2) * 0.45
		local p1 = { d[1] * reach, y + d[2] * reach, d[3] * reach }
		local f, len = Geom.between(p0[1], p0[2], p0[3], p1[1], p1[2], p1[3], "Y")
		B:block(0.62, len, 0.62, Geom.mul(f, at(0, 0, 0, 0, rad(45 + i * 7), 0)), { col = if i % 2 == 0 then "white" else "glass", mat = "ice", tr = 0.15, pri = 1.3 + i * 0.04, role = "spike", name = "Shard" .. i, noCore = true, trail = i == 1 })
	end
	B:emit("frost", "Core", { socket = "core", rate = 20 })
	face(B, ctx, { 0, y, 0 }, 1.5)
end

-- BOULDER / ROCK / EARTH ORB: a low-poly stone from intersecting blocks at unrelated angles (no two faces share
-- a plane), lighter and darker chips, and glowing cracks when it is magical.
function K.boulder(B: any, ctx: any)
	local detail = ctx.detail
	local y = 1.6
	local rocks = {
		{ 2.8, 2.4, 2.6, 0, 0, 0, 17, 29, 11, "primary" },
		{ 2.5, 2.7, 2.3, 0.15, 0.1, -0.1, -23, 61, 37, "light" },
		{ 2.3, 2.2, 2.8, -0.2, -0.1, 0.12, 41, -13, -29, "dark" },
	}
	for i, r in rocks do
		if i <= 2 or detail >= 1 then
			B:block(r[1], r[2], r[3], at(r[4], y + r[5], r[6], rad(r[7]), rad(r[8]), rad(r[9])), { col = r[10], mat = "stone", pri = 1 + i * 0.05, role = "body", name = "Rock" .. i })
		end
	end
	if detail >= 2 then
		B:block(1.1, 0.9, 1.2, at(1.2, y - 0.7, 0.6, rad(12), rad(33), rad(-21)), { col = "darker", mat = "stone", pri = 1.6, role = "detail", name = "Chip1" })
		B:block(0.9, 1.0, 0.8, at(-1.15, y - 0.75, -0.5, rad(-31), rad(9), rad(18)), { col = "light", mat = "stone", pri = 1.65, role = "detail", name = "Chip2" })
	end
	if ctx.result.category ~= "Object" and ctx.result.element ~= "None" then
		-- magical earth: a molten seam glowing out of the cracks
		B:ell(3.1, 0.18, 2.9, at(0, y + 0.1, 0, rad(-14), rad(21), rad(9)), { col = "glow", mat = "neon", glow = true, pri = 1.4, role = "gem", name = "Seam", noCore = true })
	end
	B:socket("core", at(0, y, 0), "Body")
	if Heads.wantsFace(B, ctx.traits) then
		Face.build(B, { face = { kind = "ellipsoid", c = { 0, y, 0 }, r = { 1.35, 1.25, 1.35 } }, bone = "Body", mood = ctx.result.mood, detail = math.max(1, ctx.detail),
			kind = "cute", spacing = 0.5, y = 0.25, d = 0.55, mouthY = -0.4, mouthW = 0.8, forceMouth = true, lidCol = "primary" })
	end
end

-- VOID (shadow / poison): an ink-dark core, a fast swirling neon ring, a glowing translucent shell and tendrils.
function K.void(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.4
	B:ball(2.2, at(0, y, 0), { col = "black", mat = "glass", pri = 1, role = "core", name = "Void", noCore = true })
	B:ball(3.1, at(0, y, 0), { col = "glow", mat = "glass", tr = 0.6, pri = 1.1, role = "shell", name = "Shell", noCore = true })
	B:bone("Swirl", "Body", 0, y, 0)
	B:addRig("rotors", { bone = "Swirl", axis = "Y", speed = 3 })
	B:ell(4.2, 0.16, 4.2, at(0, y, 0, rad(18), 0, rad(-8)), { col = "glow", mat = "neon", glow = true, tr = 0.1, bone = "Swirl", pri = 1.2, role = "ring", name = "Ring", noCore = true })
	local n = if detail <= 1 then 2 elseif detail == 2 then 3 else 4
	for i = 1, n do
		local a = (i - 1) / n * math.pi * 2 + 0.5
		local p0 = { sin(a) * 1.3, y - 0.3, cos(a) * 1.3 }
		local p1 = { sin(a + 0.6) * 2.4, y - 1.6 - (i % 2) * 0.4, cos(a + 0.6) * 2.4 }
		B:limb(p0, p1, 0.42, { col = "secondary", mat = "neon", glow = true, tr = 0.3, pri = 1.35 + i * 0.05, role = "tail", name = "Tendril" .. i, trail = i == 1, noCore = true }, 0.1)
	end
	B:emit("smoke", "Void", { socket = "core", rate = 24 })
	face(B, ctx, { 0, y, 0 }, 1.1)
end

-- BOMB: black iron sphere, a metal cap, a curved fuse and a fizzing spark (cartoon classic).
function K.bomb(B: any, ctx: any)
	local detail = ctx.detail
	local y = 1.7
	B:ball(3.2, at(0, y, 0), { col = "black", mat = "metal", pri = 1, role = "body", name = "Bomb" })
	B:cyl(0.45, 1.0, at(0, y + 1.62, 0.25, rad(-12), 0, rad(90)), { col = "gunmetal", mat = "metal", pri = 1.2, role = "detail", name = "Cap" })
	B:limb({ 0, y + 1.75, 0.3 }, { 0.15, y + 2.45, 0.75 }, 0.2, { col = "wood", mat = "wood", pri = 1.3, role = "detail", name = "Fuse" }, 0.1)
	B:ball(0.6, at(0.17, y + 2.55, 0.8), { col = "flameCore", mat = "neon", glow = true, pri = 1.35, role = "gem", name = "Spark", trail = true, noCore = true })
	if detail >= 2 then
		B:ell(0.7, 0.45, 0.25, at(-0.75, y + 0.85, -1.1, rad(-35), rad(30), rad(25)), { col = "white", mat = "neon", pri = 2.0, role = "shine", name = "Gloss", noCore = true })
	end
	B:emit("sparks", "Spark", { socket = "core", rate = 25 })
	face(B, ctx, { 0, y, 0 }, 1.6)
end

function K.moon(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.6
	local R = 1.7
	B:ball(R * 2, at(0, y, 0), { col = "primary", mat = "stone", pri = 1, role = "body", name = "Moon" })
	-- maria (big dark plains) then craters with a lighter floor: lenses of distinct sizes sunk to distinct depths
	local spots = { { -0.7, 0.45, 1.3, "dark" }, { 0.55, -0.35, 0.9, "darker" }, { 0.15, 0.75, 0.55, "light" }, { -0.2, -0.75, 0.65, "dark" }, { 1.0, 0.35, 0.45, "darker" } }
	for i = 1, (if detail >= 2 then 5 elseif detail == 1 then 3 else 2) do
		local sp = spots[i]
		lens(B, R, y, sp[1], sp[2], sp[3], sp[3] * 0.85, 0.24 + i * 0.03, { col = sp[4], mat = "stone", pri = 1.3 + i * 0.08, role = "detail", name = "Crater" .. i })
	end
	face(B, ctx, { 0, y, 0 }, R)
end

function K.blackhole(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.6
	B:ball(2.4, at(0, y, 0), { col = "black", mat = "glass", pri = 1, role = "core", name = "Horizon", noCore = true })
	B:bone("Disc", "Body", 0, y, 0)
	B:addRig("rotors", { bone = "Disc", axis = "Y", speed = 3 })
	B:ell(6.0, 0.18, 6.0, at(0, y, 0, rad(12), 0, 0), { col = "glow", mat = "neon", glow = true, tr = 0.2, bone = "Disc", pri = 1.1, role = "ring", name = "Accretion", noCore = true })
	B:ell(4.2, 0.26, 4.2, at(0, y, 0, rad(12), 0, 0), { col = "flameCore", mat = "neon", glow = true, tr = 0.1, bone = "Disc", pri = 1.2, role = "ring", name = "Inner", noCore = true })
	if detail >= 2 then
		B:ell(2.9, 2.9, 2.9, at(0, y, 0), { col = "secondary", mat = "glass", tr = 0.7, pri = 1.6, role = "shell", name = "Lens", noCore = true })
	end
	B:emit("wisps", "Horizon", { socket = "core", rate = 30 })
	face(B, ctx, { 0, y, 0 }, 1.2)
end

function K.bubble(B: any, ctx: any)
	local y = 2.2
	B:ball(3.2, at(0, y, 0), { col = "primary", mat = "glass", tr = 0.6, pri = 1, role = "shell", name = "Bubble", noCore = true })
	B:ell(0.9, 0.5, 0.3, at(-0.6, y + 0.85, -1.2, rad(-35), rad(25), rad(30)), { col = "shine", mat = "neon", pri = 1.4, role = "shine", name = "Gloss", noCore = true })
	if ctx.detail >= 1 then
		-- iridescent inner film and two baby bubbles drifting alongside
		B:ell(2.7, 2.7, 2.7, at(0.05, y + 0.05, 0.05), { col = "secondary", mat = "glass", tr = 0.8, pri = 1.5, role = "shell", name = "Film", noCore = true })
		B:ball(0.9, at(1.9, y + 1.1, 0.4), { col = "primary", mat = "glass", tr = 0.55, pri = 1.6, role = "shell", name = "Baby1", noCore = true })
		B:ball(0.6, at(-1.8, y - 0.9, -0.3), { col = "primary", mat = "glass", tr = 0.55, pri = 1.7, role = "shell", name = "Baby2", noCore = true })
	end
	face(B, ctx, { 0, y, 0 }, 1.6)
end

function K.ball(B: any, ctx: any)
	local detail = ctx.detail
	local id = string.lower(ctx.result.id)
	local y = 1.6
	B:ball(3.2, at(0, y, 0), { col = "primary", mat = "plastic", pri = 1, role = "body", name = "Ball" })
	if string.find(id, "beach") then
		for i = 1, 3 do
			B:ell(3.25, 3.25, 0.8, at(0, y, 0, 0, rad(i * 60), 0), { col = if i == 2 then "secondary" else "white", mat = "plastic", pri = 1.3 + i * 0.1, role = "detail", name = "Panel" .. i })
		end
	elseif string.find(id, "basket") then
		B:ell(3.26, 3.26, 0.12, at(0, y, 0), { col = "black", mat = "plastic", pri = 1.4, role = "detail", name = "Seam1" })
		B:ell(0.12, 3.26, 3.26, at(0, y, 0), { col = "black", mat = "plastic", pri = 1.5, role = "detail", name = "Seam2" })
	elseif string.find(id, "soccer") or string.find(id, "football") then
		for i = 1, (if detail >= 2 then 5 else 3) do
			local a, b = i * 1.26, (i % 2) * 0.6 - 0.2
			local nx, ny, nz = sin(a) * cos(b), sin(b), cos(a) * cos(b)
			B:ell(0.9, 0.9, 0.3, at(nx * 1.55, y + ny * 1.55, nz * 1.55, -ny, math.atan2(nx, nz), 0), { col = "black", mat = "plastic", pri = 1.4 + i * 0.05, role = "detail" })
		end
	elseif string.find(id, "bowling") then
		for i = 1, 3 do
			B:ell(0.4, 0.4, 0.3, at((i - 2) * 0.45, y + 0.7 + (i % 2) * 0.35, -1.42), { col = "black", mat = "plastic", pri = 1.4 + i * 0.05, role = "detail" })
		end
	end
	face(B, ctx, { 0, y, 0 }, 1.6)
end

function K.crystal(B: any, ctx: any)
	local detail = ctx.detail
	-- cluster of hexagonal-ish prisms: each a block with a pyramid (two wedges) tip, tilted outward
	local n = if detail <= 1 then 2 elseif detail == 2 then 3 else 5
	for i = 1, n do
		local a = (i - 1) / n * math.pi * 2 + 0.4
		local tilt = if i == 1 then 0 else rad(22)
		local h = if i == 1 then 3.4 else 2.0 - i * 0.12
		local w = if i == 1 then 1.1 else 0.7
		local base = if i == 1 then at(0, 0.2, 0) else at(sin(a) * 0.55, 0.15, cos(a) * 0.55, tilt * cos(a), a, -tilt * sin(a) * 0)
		local f = Geom.mul(base, at(0, h / 2, 0, 0, rad(45 + i * 9), 0))
		B:block(w, h, w, f, { col = if i == 1 then "primary" else "secondary", mat = "glass", tr = 0.15, pri = 1 + i * 0.1, role = "body", name = "Prism" .. i })
		B:wedge(w * 0.98, w * 1.1, w * 0.52, Geom.mul(f, at(0, h / 2 + w * 0.55 - 0.03, -w * 0.25, 0, 0, 0)), { col = if i == 1 then "primary" else "secondary", mat = "glass", tr = 0.15, pri = 1.05 + i * 0.1, role = "body", name = "TipA" .. i, trail = i == 1 })
		B:wedge(w * 0.96, w * 1.08, w * 0.52, Geom.mul(f, at(0, h / 2 + w * 0.54 - 0.03, w * 0.25, 0, math.pi, 0)), { col = if i == 1 then "primary" else "secondary", mat = "glass", tr = 0.15, pri = 1.06 + i * 0.1, role = "body", name = "TipB" .. i })
	end
	B:ball(0.9, at(0, 1.6, 0), { col = "glow", mat = "neon", glow = true, pri = 1.3, role = "gem", name = "Glow", noCore = true })
	if Heads.wantsFace(B, ctx.traits) then
		-- front face of the main prism (yawed 54 degrees): centre 0.55 out along its local -Z
		local yaw = rad(54)
		Heads.objectFace(B, ctx.traits, at(-sin(yaw) * 0.56, 1.9, -cos(yaw) * 0.56, 0, yaw, 0), 0.9)
	end
	B:socket("core", at(0, 1.6, 0), "Body")
end

return function(B: any, ctx: any)
	local kind = kindOf(ctx)
	if kind == "food" then
		-- fruit, veg, bread and sweets that were filed under Orb build as food (stem, leaf, slices...)
		local blob = require(script.Parent.Blob) :: any
		ctx.kind = "Food"
		return blob(B, ctx)
	end
	local f = (K :: any)[kind] or K.orb
	f(B, ctx)
	B.boneIndex.Body.pos = { 0, 2.4, 0 }
	if B.sockets.core == nil then
		B:socket("core", at(0, 2.4, 0), "Body")
	end
	B:setRig("gait", if kind == "ball" then "roll" else "hover")
end
