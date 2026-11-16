--!strict
-- Clouds and weather forms: cloud (puff cluster), storm cloud (+ lightning bolt), rain/snow cloud (+ falling
-- drops), Vortex (tornado funnel of stacked spinning rings + debris), Wave (curling breaker + foam), Ghost
-- (sheet ghost with wavy hem), smoke/fog (loose puffs).

local Geom = require(script.Parent.Parent.Geom)
local Face = require(script.Parent.Parent.Face)
local Heads = require(script.Parent.Parent.Heads)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local function kindOf(ctx: any): string
	if ctx.kind == "Vortex" then
		return "vortex"
	elseif ctx.kind == "Wave" then
		return "wave"
	elseif ctx.kind == "Ghost" then
		return "ghost"
	end
	local t, id = ctx.traits, string.lower(ctx.result.id)
	local function has(w: string): boolean
		return string.find(id, "%f[%a]" .. w) ~= nil
	end
	if t.funnel or has("tornado") or has("twister") or has("whirlwind") or has("hurricane") or has("cyclone") or has("vortex") or has("whirlpool") then
		return "vortex"
	elseif t.ghost or has("ghost") or has("spirit") or has("phantom") or has("specter") or has("spectre") or has("wraith") then
		return "ghost"
	elseif has("wave") or has("tsunami") or has("flood") then
		return "wave"
	elseif t.storm or has("storm") or has("thunder") then
		return "storm"
	elseif t.rain or t.snow or has("rain") or has("snow") or has("blizzard") or has("hail") then
		return "rain"
	elseif t.smoke or has("smoke") or has("fog") or has("mist") or has("steam") or has("gas") then
		return "smoke"
	end
	return "cloud"
end

local function puffs(B: any, ctx: any, y: number, col: string, n: number, spread: number, bone: string?): ({ number }, { number })
	local rng = B.rng
	B:ell(4.2, 2.2, 3.0, at(0, y, 0), { col = col, mat = "cloth", bone = bone, pri = 1, role = "body", name = "Puff0" })
	for i = 1, n do
		local a = (i - 1) / n * math.pi * 2 + 0.3
		local s = rng:range(1.6, 2.4)
		B:ell(s * 1.1, s, s, at(cos(a) * spread * 1.4, y + sin(a) * 0.35 + 0.45 + (i % 2) * 0.3, sin(a) * spread * 0.7), { col = if i % 3 == 0 then "secondary" else col, mat = "cloth", bone = bone, pri = 1.1 + i * 0.07, role = "body", name = "Puff" .. i })
	end
	return { 0, y, 0 }, { 2.1, 1.1, 1.5 }
end

local function face(B: any, ctx: any, c: { number }, r: { number }, bone: string?, force: boolean?)
	if force or Heads.wantsFace(B, ctx.traits) then
		Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = bone or "Body", mood = ctx.result.mood, detail = math.max(1, ctx.detail),
			kind = if ctx.result.element == "Lightning" or ctx.result.element == "Shadow" then "fierce" else "cute",
			spacing = r[1] * 0.3, y = r[2] * 0.1, d = math.min(r[1], r[2]) * 0.42, mouthY = -r[2] * 0.35, mouthW = r[1] * 0.45, forceMouth = true })
	end
end

local K = {}

function K.cloud(B: any, ctx: any)
	local n = if ctx.detail <= 1 then 3 elseif ctx.detail == 2 then 5 else 6
	local c, r = puffs(B, ctx, 3.0, "primary", n, 1.4)
	face(B, ctx, c, r)
	B:setRig("gait", "float")
end

function K.storm(B: any, ctx: any)
	local detail = ctx.detail
	local n = if detail <= 1 then 3 else 5
	local c, r = puffs(B, ctx, 3.6, "primary", n, 1.4)
	-- zig-zag lightning bolt: three angled neon slabs
	local pts = { { 0.2, 2.6, -0.2 }, { -0.5, 1.6, -0.3 }, { 0.4, 1.3, -0.3 }, { -0.2, 0.1, -0.35 } }
	for i = 1, 3 do
		B:beam(pts[i], pts[i + 1], 0.32 - i * 0.04, 0.12, { col = "secondary", mat = "neon", glow = true, pri = 1.3 + i * 0.1, role = "glow", name = "Bolt" .. i, noCore = true, trail = i == 3 }, 0.12)
	end
	B:emit("sparks", "Bolt1", { socket = "core", rate = 20 })
	face(B, ctx, c, r, nil, true)
	B:setRig("gait", "float")
end

function K.rain(B: any, ctx: any)
	local detail = ctx.detail
	local snow = ctx.traits.snow or ctx.result.element == "Ice"
	local c, r = puffs(B, ctx, 3.6, "primary", if detail <= 1 then 3 else 4, 1.3)
	local m = if detail <= 1 then 3 else 6
	for i = 1, m do
		local x = (i - (m + 1) / 2) * 0.6
		local y = 1.4 + (i % 3) * 0.55
		if snow then
			B:ball(0.3, at(x, y, (i % 2) * 0.4 - 0.2), { col = "white", mat = "ice", pri = 1.6 + i * 0.05, role = "detail", name = "Flake" .. i })
		else
			B:ell(0.18, 0.5, 0.18, at(x, y, (i % 2) * 0.4 - 0.2), { col = "secondary", mat = "glass", pri = 1.6 + i * 0.05, role = "detail", name = "Drop" .. i, trail = i == 1 })
		end
	end
	face(B, ctx, c, r)
	B:setRig("gait", "float")
end

function K.vortex(B: any, ctx: any)
	local detail = ctx.detail
	local water = string.find(string.lower(ctx.result.id), "whirlpool") ~= nil
	local n = if detail <= 1 then 4 elseif detail == 2 then 6 else 7
	local H = 7.0
	local wantsFace = Heads.wantsFace(B, ctx.traits)
	local faceRing = math.max(1, math.floor(n * 0.6))
	-- Funnel of stacked rings, each on its OWN bone under Body, so every ring is a separate rotor: odd rings whip
	-- one way, even rings turn back the other way at a different rate, and the speed falls off toward the wide
	-- top. A plain ellipsoid of revolution looks the same at every angle, so rotation is made readable three
	-- ways: the ring is oval and sits off its axis (it wobbles), wind streaks ride on its rim, and the streaks
	-- carry trails and particle emitters that draw spirals.
	for i = 1, n do
		local u = (i - 1) / (n - 1)
		local y = 0.3 + u * H
		local r = 0.6 + u ^ 1.6 * 2.45
		local sx = sin(u * 3) * 0.4
		local still = wantsFace and i == faceRing -- the face ring keeps looking forward
		local b = B:bone("Ring" .. i, "Body", sx, y, 0)
		if not still then
			local dir = if i % 2 == 1 then 1 else -0.62
			B:addRig("rotors", { bone = b, axis = "Y", speed = dir * (7.5 - u * 3.5) })
		end
		B:addRig("sway", b)
		local ecc = if still then 0 else r * 0.14
		local ea = i * 2.1
		local col = if i % 2 == 0 then "secondary" else "primary"
		-- thick enough to overlap the next ring: one continuous funnel, not a stack of plates
		B:ell(r * 2, math.max(1.05 + u * 0.35, H / (n - 1) * 1.3), r * (if still then 2 else 1.72), at(sx + cos(ea) * ecc, y, sin(ea) * ecc, rad(4 + i * 2), 0, rad(-6 + i * 3)),
			{ col = col, mat = "cloth", tr = 0.15 + u * 0.15, bone = b, pri = 1 + i * 0.05, role = "body", name = "Ring" .. i, trail = i == n })
		if not still then
			for k = 1, 2 do
				local a = i * 1.3 + k * 2.5
				local rr = r * (if k == 1 then 1.02 else 0.9)
				B:ell(r * (1.25 - k * 0.2) + 0.3, 0.26 + u * 0.12 + k * 0.03, r * 0.34 + 0.12,
					at(sx + cos(a) * rr, y + (k - 1.5) * (0.3 + u * 0.1), sin(a) * rr, 0, a + math.pi / 2, rad(k * 16 - 14)),
					{ col = if (k + i) % 2 == 0 then "dark" else "light", mat = "cloth", tr = 0.1, bone = b, pri = (if k == 1 then 1.32 else 2.1) + i * 0.04, role = "detail",
						name = "Ring" .. i .. "Streak" .. k, trail = k == 1 and (i == 2 or i == n - 1) })
			end
		end
	end
	-- debris caught in the base: two orbits turning against each other
	if detail >= 1 and not water then
		B:bone("Debris", "Body", 0, 0.8, 0)
		B:addRig("rotors", { bone = "Debris", axis = "Y", speed = 4.5 })
		B:bone("DebrisHigh", "Body", 0, 1.9, 0)
		B:addRig("rotors", { bone = "DebrisHigh", axis = "Y", speed = -3 })
		local m = if detail >= 3 then 6 elseif detail == 2 then 5 else 3
		for i = 1, m do
			local a = (i - 1) / m * math.pi * 2 + (i % 2) * 0.35
			local s = 0.35 + (i % 3) * 0.12
			local high = i % 2 == 0
			local rad0 = if high then 2.5 else 1.9 + (i % 3) * 0.15
			B:block(s, s * 0.8, s * 1.2, at(cos(a) * rad0, (if high then 1.9 else 0.8) + (i % 3) * 0.18, sin(a) * rad0, i, i * 0.7, i * 0.3),
				{ col = if i % 2 == 0 then "wood" else "stone", mat = if i % 2 == 0 then "wood" else "stone", bone = if high then "DebrisHigh" else "Debris", pri = 1.5 + i * 0.07,
					role = "detail", name = "Debris" .. i, trail = i == 1 })
		end
		B:emit("dust", "Debris1", { rate = 14, spread = 0.6 })
	end
	-- swirling particles: emitted from streaks that ride the spinning rings, so they are flung off in spirals
	B:emit("streaks", "Ring2Streak1", { rate = 26, spread = 0.5 })
	B:emit("wisps", "Ring" .. (n - 1) .. "Streak1", { rate = 16, spread = 0.8 })
	B:emit("streaks", nil, { socket = "core", rate = 30 })
	B:socket("core", at(0, H * 0.45, 0), "Body")
	if wantsFace then
		local y = 0.3 + H * 0.6
		face(B, ctx, { 0, y, 0 }, { 1.6, 1.0, 1.6 }, "Ring" .. faceRing, true)
	end
	B:setRig("gait", "spin")
end

function K.wave(B: any, ctx: any)
	local detail = ctx.detail
	-- curling breaker: an arc of overlapping ellipsoids rising and curling forward, foam on the lip
	local n = if detail <= 1 then 4 else 6
	local prev = "Body"
	for i = 1, n do
		local u = (i - 1) / (n - 1)
		local a = u * math.pi * 1.15
		local y = 0.6 + sin(a) * 3.2
		local z = 1.6 - (1 - cos(a)) * 1.8
		local b = B:bone("Crest" .. i, prev, 0, y, z)
		B:addRig("spine", b)
		B:ell(6.4 - u * 1.4, 2.4 - u * 0.7, 2.9 - u * 0.6, at(0, y, z, -a + rad(20), 0, 0), { col = if u > 0.75 then "secondary" else "primary", mat = "glass", tr = 0.1, bone = b, pri = 1 + i * 0.05, role = "body", name = "Water" .. i, trail = i == n })
		prev = b
	end
	if detail >= 2 then
		for i = 1, 3 do
			B:ball(0.7, at((i - 2) * 1.5, 3.6, -0.6), { col = "white", mat = "cloth", bone = prev, pri = 2.0 + i * 0.1, role = "detail", name = "Foam" .. i })
		end
	end
	B:ell(7.0, 0.6, 4.0, at(0, 0.3, 0.8), { col = "primary", mat = "glass", tr = 0.25, pri = 1.2, role = "body", name = "Base" })
	B:emit("bubbles", nil, { socket = "core", rate = 20 })
	face(B, ctx, { 0, 2.0, 0.9 }, { 2.4, 0.9, 1.0 })
	B:socket("core", at(0, 2, 0.5), "Body")
	B:setRig("gait", "surge")
end

function K.ghost(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.2
	local c, r = { 0, y + 1.0, 0 }, { 1.4, 1.5, 1.3 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "cloth", tr = 0.1, pri = 1, role = "body", name = "Sheet" })
	B:limb({ 0, y + 0.6, 0 }, { 0, y - 1.2, 0.2 }, 2.6, { col = "primary", mat = "cloth", tr = 0.1, pri = 1.05, role = "body", name = "Drape", depth = 2.4 }, 0.1)
	-- wavy hem: 3-4 drooping tails on bones so they flutter
	local n = if detail <= 1 then 3 else 4
	for i = 1, n do
		local a = (i - 0.5) / n * math.pi * 2
		local bx, bz = sin(a) * 0.9, cos(a) * 0.85 + 0.2
		local b = B:bone("Hem" .. i, "Body", bx, y - 1.0, bz)
		B:addRig("tail", b)
		B:limb({ bx, y - 0.9, bz }, { bx * 1.1, y - 2.0, bz * 1.1 + 0.3 }, 0.8, { col = "primary", mat = "cloth", tr = 0.1, bone = b, pri = 1.3 + i * 0.05, role = "tail", name = "Hem" .. i, trail = i == 1 }, 0.2)
	end
	B:mirrorBone("Arm#", "Body", 1.25, y + 0.5, -0.1)
	B:mlimb({ 1.2, y + 0.6, -0.1 }, { 1.9, y + 0.1, -0.6 }, 0.55, { col = "primary", mat = "cloth", tr = 0.1, bone = "Arm#", pri = 1.4, role = "limb", name = "Arm#", trail = true }, 0.25)
	B:addRig("arms", { arm = "ArmR", side = 1 })
	B:addRig("arms", { arm = "ArmL", side = -1 })
	local m = ctx.result.mood
	Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = "Body", mood = if m == nil or m == "Neutral" then "Scared" else m, detail = math.max(1, detail),
		kind = "cute", spacing = r[1] * 0.32, y = r[2] * 0.12, d = r[1] * 0.42, mouthY = -r[2] * 0.3, mouthW = r[1] * 0.5, forceMouth = true, noBrows = true })
	B:socket("core", at(0, y + 0.8, 0), "Body")
	B:setRig("gait", "float")
end

function K.smoke(B: any, ctx: any)
	local n = if ctx.detail <= 1 then 3 else 5
	local c, r = puffs(B, ctx, 2.4, "primary", n, 1.0)
	for _, p in B.parts do
		p.tr = 0.25
	end
	B:emit("smoke", nil, { socket = "core", rate = 25 })
	face(B, ctx, c, r)
	B:setRig("gait", "float")
end

return function(B: any, ctx: any)
	local kind = kindOf(ctx)
	local f = (K :: any)[kind] or K.cloud
	f(B, ctx)
	B.boneIndex.Body.pos = { 0, 2.5, 0 }
	if B.sockets.core == nil then
		B:socket("core", at(0, 3, 0), "Body")
	end
end
