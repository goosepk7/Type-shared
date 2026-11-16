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
	elseif t.planet or has("planet") or has("saturn") or has("jupiter") or has("world") then
		return "planet"
	elseif t.sun or has("sun") or has("star") or has("supernova") then
		return "sun"
	elseif t.moon or has("moon") then
		return "moon"
	elseif has("bubble") then
		return "bubble"
	elseif has("ball") or has("football") or has("soccer") or has("basketball") or has("baseball") or has("bowling") or has("beach") then
		return "ball"
	elseif has("crystal") or has("gem") or has("diamond") or has("ruby") or has("emerald") or has("sapphire") or has("shard") then
		return "crystal"
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

function K.orb(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.4
	B:ball(2.0, at(0, y, 0), { col = "flameCore", mat = "neon", glow = true, pri = 1, role = "core", name = "Core", noCore = true })
	B:ball(3.0, at(0, y, 0), { col = "primary", mat = "glass", tr = 0.35, pri = 1.1, role = "shell", name = "Shell", noCore = true })
	if detail >= 1 then
		-- two crossed orbit bands (an atom-like gyroscope) so the orb never reads as a plain ball
		for i = 1, 2 do
			B:ell(4.1, 0.14, 4.1, at(0, y, 0, rad(if i == 1 then 32 else -32), rad(i * 40), 0), { col = "secondary", mat = "neon", glow = true, pri = 1.45 + i * 0.05, role = "ring", name = "Band" .. i, noCore = true, tr = 0.15 })
		end
	end
	if detail >= 2 then
		B:ell(3.7, 3.5, 3.7, at(0, y, 0), { col = "secondary", mat = "glass", tr = 0.65, pri = 1.6, role = "shell", name = "Aura", noCore = true })
	end
	B:bone("Motes", "Body", 0, y, 0)
	B:addRig("rotors", { bone = "Motes", axis = "Y", speed = 2.5 })
	local n = if detail <= 1 then 2 elseif detail == 2 then 3 else 5
	for i = 1, n do
		local a = (i - 1) / n * math.pi * 2
		B:ball(0.42, at(sin(a) * 2.4, y + cos(a * 2) * 0.5, cos(a) * 2.4), { col = "secondary", mat = "neon", glow = true, bone = "Motes", pri = 1.4 + i * 0.1, role = "gem", name = "Mote" .. i, trail = true, noCore = true })
	end
	B:emit("wisps", "Core", { socket = "core", rate = 20 })
	face(B, ctx, { 0, y, 0 }, 1.5)
end

function K.planet(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.6
	B:ball(3.6, at(0, y, 0), { col = "primary", mat = "stone", pri = 1, role = "body", name = "Planet" })
	-- bands: thin ellipsoids just larger than the sphere at different latitudes
	for i = 1, (if detail >= 2 then 2 else 1) do
		B:ell(3.66 - i * 0.2, 0.5, 3.66 - i * 0.2, at(0, y - 0.8 + i * 0.9, 0), { col = "secondary", mat = "stone", pri = 1.5 + i * 0.1, role = "detail", name = "Band" .. i })
	end
	B:bone("Ring", "Body", 0, y, 0)
	B:addRig("rotors", { bone = "Ring", axis = "Y", speed = 0.6 })
	B:cyl(0.08, 7.0, at(0, y, 0, rad(18), 0, rad(90) + rad(8)), { col = "secondary", mat = "glass", tr = 0.25, bone = "Ring", pri = 1.1, role = "ring", name = "Ring" })
	B:cyl(0.1, 5.4, at(0, y, 0, rad(18), 0, rad(90) + rad(8)), { col = "darker", mat = "glass", tr = 0.2, bone = "Ring", pri = 1.2, role = "ring", name = "RingGap" })
	face(B, ctx, { 0, y, 0 }, 1.8)
end

function K.sun(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.6
	B:ball(3.4, at(0, y, 0), { col = "gold", mat = "neon", glow = true, pri = 1, role = "core", name = "Sun", noCore = true })
	B:bone("Corona", "Body", 0, y, 0)
	B:addRig("rotors", { bone = "Corona", axis = "Z", speed = 0.8 })
	local n = if detail <= 1 then 6 else 8
	for i = 1, n do
		local a = (i - 1) / n * math.pi * 2
		B:wedge(0.22, 1.1, 0.8, Geom.mul(at(0, y, 0, 0, 0, a), at(0, 2.05, 0, 0, rad(90), 0)), { col = "flame", mat = "neon", glow = true, bone = "Corona", pri = 1.3 + i * 0.02, role = "spike", name = "Ray" .. i, noCore = true })
	end
	table.insert(B.lights, { kind = "PointLight", colour = { 1, 0.85, 0.5 }, brightness = 2, range = 1.5, socket = "core", shadows = false })
	face(B, ctx, { 0, y, 0 }, 1.7, true)
end

function K.moon(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.6
	B:ball(3.4, at(0, y, 0), { col = "primary", mat = "stone", pri = 1, role = "body", name = "Moon" })
	for i = 1, (if detail >= 2 then 4 else 2) do
		local a, b = i * 1.9, i * 0.7
		local nx, ny, nz = sin(a) * cos(b), sin(b) * 0.8, -math.abs(cos(a) * cos(b))
		B:ell(0.7, 0.7, 0.3, at(nx * 1.65, y + ny * 1.65, nz * 1.65, -ny * 0.9, nx * 0.9, 0), { col = "dark", mat = "stone", pri = 1.5 + i * 0.1, role = "detail", name = "Crater" .. i })
	end
	face(B, ctx, { 0, y, 0 }, 1.7)
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
	local f = (K :: any)[kind] or K.orb
	f(B, ctx)
	B.boneIndex.Body.pos = { 0, 2.4, 0 }
	if B.sockets.core == nil then
		B:socket("core", at(0, 2.4, 0), "Body")
	end
	B:setRig("gait", if kind == "ball" then "roll" else "hover")
end
