--!strict
-- Worms and other soft crawlers (the Worm route and worm-like Serpent words):
--   earth     ringed segments (s_aq_worm_seg), a blunt head with a small mouth (earthworm, nematode, bristle worm,
--             glowworm, ribbon / arrow worm);
--   inch      inchworm / looper: the body arched in a loop, true legs at the front, claspers at the back; the
--             loop opens and closes (rig.arch);
--   cater     caterpillars: plump banded segments, prolegs under each, a round head (hornworm horn, monarch
--             filaments, woolly / puss fuzz, velvet worm antennae);
--   centipede centipedes and millipedes: flat (or round) segments each with a leg pair, antennae, forcipules;
--   grub      grubs, maggots, larvae, mealworms: a C-curled or straight tapering larva;
--   flat      flatworms and tapeworms: a ribbon that hugs the ground, an arrow head with cross eyes;
--   leech     leeches and parasites: a flattened tapering body with a sucker at each end;
--   tube      tube worms: upright tubes with a red plume (feather duster: a fan crown; christmas tree: spirals);
--   giant     sandworms and death worms: a huge ringed body rearing out of a mound, a round mouth ringed with
--             teeth (s_aq_worm_mouth);
--   slug      slugs: a long soft foot, a mantle hump, two eye stalks;
--   bear      water bears: a chubby eight-legged barrel with a tube snout.

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Face = require(script.Parent.Parent.Face)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local Worms = {}

local function reader(ctx: any): (...string) -> boolean
	local id = string.lower(ctx.result.id)
	local hint = string.lower((ctx.result.visual and ctx.result.visual.silhouetteHint) or "")
	return function(...: string): boolean
		for _, w in { ... } do
			if string.find(id, w, 1, true) or string.find(hint, w, 1, true) then
				return true
			end
		end
		return false
	end
end

local function mood(B: any): string
	return B.ctx.result.mood or "Neutral"
end

local function kindOf(has: any): string
	if has("inchworm", "looper", "looping caterpillar") then
		return "inch"
	elseif has("water bear", "tardigrade", "micro bear") then
		return "bear"
	elseif has("tube worm", "tube", "feather duster", "christmas tree", "fan worm", "plume") then
		return "tube"
	elseif has("sand worm", "sandworm", "death worm", "ice worm", "kaiju worm", "space worm", "lava worm", "mongolian", "bobbit", "giant worm", "bursting", "erupting") then
		return "giant"
	elseif has("centipede", "millipede", "scutigera", "arthropleura", "hundreds of legs", "many long legs") then
		return "centipede"
	elseif has("caterpillar", "hornworm", "woolly", "silkworm", "velvet worm", "puss", "many-legged") then
		return "cater"
	elseif has("grub", "maggot", "larva", "mealworm") then
		return "grub"
	elseif has("flatworm", "tapeworm", "flat ribbon", "planarian") then
		return "flat"
	elseif has("leech", "parasite", "sucker", "lamprey") then
		return "leech"
	elseif has("slug") then
		return "slug"
	end
	return "earth"
end

-- Segment chain along pts (index 0 = head end). o: w(i) width function, depth, ringed, banded, mat, col, pri,
-- prefix. Returns bone names per segment.
local function chain(B: any, pts: { { number } }, n: number, o: any): { string }
	local bones = {}
	local parent = o.parent or "Body"
	for i = 1, n do
		local a, b = pts[i - 1], pts[i]
		local bname = B:bone((o.prefix or "Seg") .. i, parent, a[1], a[2], a[3])
		B:addRig("spine", bname)
		local ww = o.w(i)
		local col = o.col or "primary"
		if o.banded and i % 2 == 0 then
			col = "secondary"
		end
		local seg = B:limb(a, b, ww, { col = col, mat = o.mat or "skin", bone = bname, pri = (o.pri or 1) + i * 0.1, role = "body", name = "Seg" .. i, trail = i == n, depth = ww * (o.depth or 1.0) }, o.over or 0.4)
		if o.ringed then
			B:sculpt(seg, "s_aq_worm_seg")
		end
		table.insert(bones, bname)
		parent = bname
	end
	return bones
end

-- Round head at the front of pts[0] toward dir; returns centre and radii.
local function roundHead(B: any, ctx: any, p: { number }, s: number, o: any): ({ number }, { number })
	local detail = ctx.detail
	local hb = B:bone("Head", o.parent or "Seg1", p[1], p[2], p[3])
	B:setRig("head", hb)
	local c = { p[1], p[2] + (o.dy or 0), p[3] - s * (o.fwd or 0.35) }
	local r = { s * 0.5, s * (o.ry or 0.47), s * 0.48 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = o.col or "primary", mat = "skin", bone = hb, pri = 1.05, role = "head", name = "Head", mesh = o.mesh or false })
	Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = hb, mood = mood(B), detail = detail, kind = o.eyes or "cute",
		spacing = r[1] * (o.spacing or 0.5), y = r[2] * (o.eyeY or 0.18), d = s * (o.eye or 0.3), mouthY = -r[2] * 0.42, mouthW = s * 0.45, forceMouth = o.mouth ~= false,
		noMouth = o.mouth == false, lidCol = "primary" })
	B:socket("mouth", at(c[1], c[2] - r[2] * 0.4, c[3] - r[3]), hb)
	return c, r
end

local function straightPts(n: number, len: number, y: number, wave: number, z0: number?): { { number } }
	local pts = {}
	for i = 0, n do
		local u = i / n
		pts[i] = { sin(u * math.pi * 1.6) * wave, y, (z0 or -len * 0.4) + u * len }
	end
	return pts
end

local function earth(B: any, ctx: any, has: any)
	local t, detail = ctx.traits, ctx.detail
	local n = if detail <= 0 then 3 elseif detail == 1 then 4 elseif detail == 2 then 6 else 7
	local w = 0.62 * (if t.chubby or has("fat", "chubby") then 1.3 else 1)
	local pts = straightPts(n, 4.4, w * 0.48, 0.55)
	B.boneIndex.Body.pos = { pts[1][1], pts[1][2], pts[1][3] }
	chain(B, pts, n, { w = function(i)
		return w * (1 - (i - 1) / n * 0.35)
	end, ringed = true, depth = 1.05, mat = if has("glow") then "skin" else "skin", banded = has("band", "ring"), over = 0.45 })
	-- clitellum: the paler saddle band
	if detail >= 2 and not has("clear", "glow") then
		local a, b = pts[1], pts[2]
		B:limb({ (a[1] + b[1]) / 2, a[2], (a[3] * 0.7 + b[3] * 0.3) }, { b[1], b[2], b[3] - 0.1 }, w * 1.12, { col = "secondary", mat = "skin", bone = "Seg2", pri = 2.4, role = "detail", name = "Saddle", depth = w * 1.15, mesh = false }, 0.1)
	end
	if has("bristl", "furry", "sea mouse") and detail >= 2 then
		for i = 2, math.min(n, 4) do
			local p = pts[i - 1]
			B:mlimb({ w * 0.4, p[2], p[3] + 0.2 }, { w * 0.95, p[2] + w * 0.35, p[3] + 0.3 }, 0.07, { col = "secondary", mat = "hard", bone = "Seg" .. i, pri = 3 + i * 0.1, role = "spike", name = "Bristle#", mesh = false }, 0.05)
		end
	end
	if has("glow") and detail >= 1 then
		for i = 1, math.min(n, 3) do
			local p = pts[i]
			B:ball(w * 0.45, at(p[1], p[2] + w * 0.35, p[3]), { col = "glow", mat = "neon", glow = true, bone = "Seg" .. i, pri = 2.6 + i * 0.1, role = "gem", name = "Glow", noCore = true })
		end
	end
	local p = pts[0]
	roundHead(B, ctx, p, w * 1.2, { fwd = 0.2, eye = 0.28, mesh = "s_aq_worm_head" })
	B:setRig("gait", "inch")
end

local function inch(B: any, ctx: any, has: any)
	local detail = ctx.detail
	local n = if detail <= 1 then 4 else 6
	local w = 0.55
	-- an arch: both ends on the ground, the middle looped up high
	local pts = {}
	for i = 0, n do
		local u = i / n
		pts[i] = { 0, w * 0.48 + sin(u * math.pi) * 1.7, -1.5 + u * 3.0 + sin(u * math.pi * 2) * 0.35 }
	end
	B.boneIndex.Body.pos = { pts[1][1], pts[1][2], pts[1][3] }
	local bones = chain(B, pts, n, { w = function(i)
		return w * (1 - (i - 1) / n * 0.15)
	end, ringed = true, depth = 1.0, over = 0.5, col = "primary" })
	-- the loop: segments pitch in alternation so the arch opens and closes
	for i, b in bones do
		B:addRig("arch", { bone = b, k = if i <= n / 2 then 0.25 else -0.25 })
	end
	-- true legs behind the head, claspers at the tail end
	if detail >= 2 then
		local a = pts[0]
		B:mlimb({ w * 0.25, a[2] - w * 0.1, a[3] + 0.25 }, { w * 0.4, 0.05, a[3] + 0.2 }, w * 0.22, { col = "darker", mat = "skin", bone = bones[1], pri = 2.6, role = "limb", name = "TrueLeg#" }, 0.1)
		local z = pts[n]
		B:mlimb({ w * 0.25, z[2] - w * 0.1, z[3] - 0.2 }, { w * 0.42, 0.05, z[3] - 0.25 }, w * 0.32, { col = "primary", mat = "skin", bone = bones[n], pri = 2.8, role = "limb", name = "Clasper#" }, 0.1)
	end
	roundHead(B, ctx, pts[0], w * 1.15, { fwd = 0.3, eye = 0.3, dy = -0.02 })
	B:setRig("gait", "inch")
end

local function cater(B: any, ctx: any, has: any)
	local t, detail = ctx.traits, ctx.detail
	local n = if detail <= 0 then 3 elseif detail == 1 then 4 elseif detail == 2 then 5 else 6
	local w = 0.9 * (if has("fat", "chubby", "plump") then 1.15 else 1)
	local fuzzy = t.fluffy or has("fuzzy", "fluffy", "woolly", "puss", "toupee")
	local pts = straightPts(n, 3.6, w * 0.55, 0.35)
	B.boneIndex.Body.pos = { pts[1][1], pts[1][2], pts[1][3] }
	local bones = chain(B, pts, n, { w = function(i)
		return w * (if i == n then 0.8 else 1)
	end, ringed = not fuzzy, depth = 1.0, banded = has("stripe", "striped", "band", "black-orange", "monarch"), mat = if fuzzy then "fur" else "skin", over = 0.5 })
	-- prolegs: stubby pairs under the segments
	if detail >= 2 then
		for i = 1, math.min(n, if detail >= 3 then 4 else 3) do
			local p = pts[i]
			B:mball(w * 0.32, at(w * 0.3, w * 0.12, p[3] - 0.1), { col = "darker", mat = "skin", bone = bones[i], pri = 3 + i * 0.1, role = "foot", name = "Proleg#" })
		end
	end
	if fuzzy and detail >= 2 then
		-- tufts of setae standing up on alternate segments
		for i = 1, n, 2 do
			local p = pts[i]
			B:ell(w * 0.75, w * 0.55, w * 0.55, at(p[1], p[2] + w * 0.45, p[3] - 0.1), { col = if i % 4 == 1 then "secondary" else "primary", mat = "fur", bone = bones[i], pri = 2.4 + i * 0.1, role = "detail", name = "Tuft", mesh = false })
		end
	end
	if has("horn") and detail >= 1 then
		local p = pts[n]
		B:limb({ p[1], p[2] + w * 0.3, p[3] - 0.3 }, { p[1], p[2] + w * 1.0, p[3] + 0.15 }, w * 0.16, { col = "secondary", mat = "hard", bone = bones[n], pri = 2.2, role = "horn", name = "TailHorn", trail = true }, 0.1)
	end
	if has("monarch", "filament", "velvet", "antenna") and detail >= 2 then
		local p = pts[0]
		B:mlimb({ w * 0.2, p[2] + w * 0.35, p[3] + 0.15 }, { w * 0.45, p[2] + w * 1.15, p[3] - 0.35 }, w * 0.09, { col = "darker", mat = "skin", bone = bones[1], pri = 2.8, role = "antenna", name = "Filament#", trail = true }, 0.05)
	end
	roundHead(B, ctx, pts[0], w * 1.0, { fwd = 0.38, eye = 0.27, col = if has("monarch") then "darker" else "primary", spacing = 0.48 })
	B:setRig("gait", "inch")
end

local function centipede(B: any, ctx: any, has: any)
	local t, detail = ctx.traits, ctx.detail
	local milli = has("millipede", "round body", "arthropleura")
	local longLegs = has("scutigera", "many long legs")
	local n = if detail <= 2 then 4 else 6
	local w = if milli then 0.7 else 0.6
	local pts = straightPts(n, 4.6, 0.55, 0.6)
	B.boneIndex.Body.pos = { pts[1][1], pts[1][2], pts[1][3] }
	local bones = chain(B, pts, n, { w = function(i)
		return w
	end, depth = if milli then 1.05 else 1.6, ringed = true, mat = "hard", col = "primary", banded = has("band", "stripe"), over = 0.35 })
	-- one leg pair per segment (two on the last at high detail)
	if detail >= 1 then
		for i = 1, n do
			local a, b = pts[i - 1], pts[i]
			local m = { (a[1] + b[1]) / 2, (a[2] + b[2]) / 2, (a[3] + b[3]) / 2 }
			local reach = if longLegs then 1.4 elseif milli then 0.45 else 0.75
			local kx, ky = w * 0.55 + reach * 0.45, m[2] + (if longLegs then 0.55 else 0.15)
			local bn = bones[i]
			B:mlimb({ w * 0.45, m[2], m[3] }, { kx, ky, m[3] - 0.05 }, w * 0.16, { col = "secondary", mat = "hard", bone = bn, pri = 1.3 + i * 0.06, role = "limb", name = "Leg" .. i .. "#" }, 0.1)
			if detail >= 2 then
				B:mlimb({ kx, ky, m[3] - 0.05 }, { kx + reach * 0.4, 0.04, m[3] - 0.15 }, w * 0.12, { col = "secondary", mat = "hard", bone = bn, pri = 2.6 + i * 0.15, role = "limb", name = "Foot" .. i .. "#" }, 0.08)
			end
			B:addRig("legs", { hip = bn, side = 1, phase = i * 0.18, len = 0.5 })
		end
	end
	-- head with antennae and forcipules
	local c, r = roundHead(B, ctx, pts[0], w * 1.1, { fwd = 0.25, eye = 0.24, ry = 0.36, eyes = if t.cute or t.size == "Tiny" then "cute" else "fierce", mouth = false })
	if detail >= 1 then
		B:mlimb({ r[1] * 0.4, c[2] + r[2] * 0.5, c[3] - r[3] * 0.6 }, { r[1] * 1.6, c[2] + r[2] * 2.2, c[3] - r[3] * 3.2 }, w * 0.08, { col = "darker", mat = "hard", bone = "Head", pri = 1.9, role = "antenna", name = "Antenna#", trail = true }, 0.05)
	end
	if detail >= 2 and not milli then
		B:mlimb({ r[1] * 0.5, c[2] - r[2] * 0.6, c[3] - r[3] * 0.5 }, { r[1] * 0.15, c[2] - r[2] * 0.7, c[3] - r[3] * 1.5 }, w * 0.14, { col = "darker", mat = "hard", bone = "Head", pri = 2.4, role = "jaw", name = "Forcipule#" }, 0.05)
	end
	B:setRig("gait", "scuttle")
end

local function grub(B: any, ctx: any, has: any)
	local detail = ctx.detail
	local curled = has("curled", "grub", "c-shaped")
	local n = if detail <= 1 then 3 else 5
	local w = if has("mealworm") then 0.55 else 0.85
	local pts = {}
	for i = 0, n do
		local u = i / n
		if curled then
			local a = rad(-60) + u * rad(230)
			pts[i] = { 0, 1.05 + sin(a) * -0.85 + 0.1, -cos(a) * 0.95 }
		else
			pts[i] = { sin(u * math.pi) * 0.25, w * 0.5, -1.4 + u * (if has("mealworm") then 3.6 else 2.8) }
		end
	end
	B.boneIndex.Body.pos = { pts[1][1], pts[1][2], pts[1][3] }
	chain(B, pts, n, { w = function(i)
		return w * (if curled then 1.05 - (i - 1) / n * 0.25 else (if has("maggot") then 1 - (i - 1) / n * -0.15 else 1))
	end, ringed = true, depth = 1.0, over = 0.5, mat = if has("mealworm") then "hard" else "skin" })
	local p = pts[0]
	local c, r = roundHead(B, ctx, p, w * (if has("maggot") then 0.85 else 0.95), { fwd = 0.25, eye = 0.25, col = if has("maggot") then "primary" else "secondary" })
	if curled and detail >= 2 then
		-- three pairs of little legs under the thorax
		for i = 1, 2 do
			local q = pts[i]
			B:mlimb({ w * 0.3, q[2] - w * 0.2, q[3] }, { w * 0.6, q[2] - w * 0.6, q[3] - 0.2 }, w * 0.14, { col = "secondary", mat = "skin", bone = "Seg" .. i, pri = 3 + i * 0.1, role = "limb", name = "GrubLeg" .. i .. "#" }, 0.1)
		end
	end
	local _ = c
	local _r = r
	B:setRig("gait", "inch")
end

local function flat(B: any, ctx: any, has: any)
	local detail = ctx.detail
	local n = if detail <= 1 then 3 else 5
	local long = has("tapeworm", "long")
	local w = 0.2
	local pts = {}
	for i = 0, n do
		local u = i / n
		pts[i] = { sin(u * math.pi * 2) * 0.55, 0.14, -1.6 + u * (if long then 5.0 else 3.4) }
	end
	B.boneIndex.Body.pos = { pts[1][1], pts[1][2], pts[1][3] }
	chain(B, pts, n, { w = function(i)
		return w * (if long then 1 else 1 - (i - 1) / n * 0.3)
	end, depth = if long then 3.2 else 5.5, ringed = long, over = 0.4, banded = long })
	-- arrow head with the two cross-eyed eye spots
	local p = pts[0]
	local hb = B:bone("Head", "Seg1", p[1], p[2], p[3])
	B:setRig("head", hb)
	local c = { p[1], p[2], p[3] - 0.45 }
	B:ell(1.3, 0.24, 0.9, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", bone = hb, pri = 1.05, role = "head", name = "Head", mesh = false })
	if detail >= 1 then
		B:mell(0.35, 0.2, 0.55, at(0.55, c[2], c[3] + 0.05, 0, rad(-35), 0), { col = "primary", mat = "skin", bone = hb, pri = 1.6, role = "ear", name = "Auricle#", mesh = false })
	end
	local cf = Geom.mul(at(c[1], c[2] + 0.11, c[3] - 0.05), at(0, 0, 0, rad(80), 0, 0))
	Face.build(B, { face = { kind = "flat", cf = cf }, bone = hb, mood = mood(B), detail = detail, kind = "cute", spacing = 0.16, y = 0.05, d = 0.24, noMouth = true, noBrows = true, lidCol = "primary" })
	B:setRig("gait", "slither")
end

local function leech(B: any, ctx: any, has: any)
	local detail = ctx.detail
	local n = if detail <= 1 then 3 else 5
	local w = 0.42
	local pts = straightPts(n, 3.6, 0.35, 0.4)
	B.boneIndex.Body.pos = { pts[1][1], pts[1][2], pts[1][3] }
	chain(B, pts, n, { w = function(i)
		local u = (i - 0.5) / n
		return w * (0.65 + sin(u * math.pi) * 0.7)
	end, depth = 1.7, ringed = true, over = 0.45 })
	local p = pts[0]
	local hb = B:bone("Head", "Seg1", p[1], p[2], p[3])
	B:setRig("head", hb)
	local c = { p[1], p[2] + 0.05, p[3] - 0.3 }
	local r = { 0.45, 0.3, 0.45 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", bone = hb, pri = 1.05, role = "head", name = "Head", mesh = false })
	-- oral sucker facing forward, ringed with teeth on the sculpt
	B:cyl(0.22, 0.7, at(c[1], c[2] - 0.02, c[3] - r[3] * 0.85, 0, rad(90), 0), { col = "inner", mat = "skin", bone = hb, pri = 1.4, role = "snout", name = "Sucker", mesh = "s_aq_worm_mouth" })
	Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = hb, mood = mood(B), detail = detail, kind = "cute", spacing = r[1] * 0.55, y = r[2] * 0.75, d = 0.18, noMouth = true, noBrows = true, lidCol = "primary" })
	if detail >= 1 then
		local q = pts[n]
		B:ell(w * 2.0, 0.25, w * 2.0, at(q[1], 0.15, q[3] + 0.1), { col = "darker", mat = "skin", bone = "Seg" .. n, pri = 2.0, role = "detail", name = "TailSucker", mesh = false })
	end
	B:setRig("gait", "inch")
end

local function tube(B: any, ctx: any, has: any)
	local detail = ctx.detail
	local tree = has("christmas", "spiral")
	local duster = has("feather duster", "fan", "feathery")
	local count = if has("giant", "tubes") and detail >= 2 then 3 else 1
	B.boneIndex.Body.pos = { 0, 1.0, 0 }
	-- a rock / mound the tubes stand in
	B:ell(2.6, 0.7, 2.2, at(0, 0.2, 0.2), { col = "darkStone", mat = "stone", pri = 1.3, role = "body", name = "Base", mesh = "boulder" })
	for k = 1, count do
		local x = (k - (count + 1) / 2) * 0.75
		local z = if k == 2 then 0.45 else 0
		local hgt = 3.0 - math.abs(x) * 0.6
		local tb = B:bone("Tube" .. k, "Body", x, 0.3, z)
		B:addRig("sway", tb)
		B:cyl(hgt, 0.6, at(x, 0.3 + hgt / 2, z, 0, 0, rad(90)), { col = if duster then "secondary" else "secondary", mat = "hard", bone = tb, pri = 1 + k * 0.1, role = "body", name = "Tube", mesh = "s_aq_tube" })
		local top = { x, 0.3 + hgt, z }
		local pb = B:bone("Plume" .. k, tb, top[1], top[2], top[3])
		B:addRig("sway", pb)
		if tree then
			for s = -1, 1, 2 do
				B:ell(0.75, 1.25, 0.75, at(x + s * 0.35, top[2] + 0.55, z), { col = "primary", mat = "skin", bone = pb, pri = 1.2 + k * 0.1, role = "petal", name = "Spiral", mesh = "s_aq_spiral_plume" })
			end
		elseif duster then
			B:ell(2.0, 1.0, 2.0, at(x, top[2] + 0.4, z), { col = "primary", mat = "skin", bone = pb, pri = 1.2 + k * 0.1, role = "petal", name = "Fan", mesh = "s_aq_fan_plume" })
		else
			B:ell(0.9, 1.4, 0.9, at(x, top[2] + 0.45, z), { col = "primary", mat = "skin", bone = pb, pri = 1.2 + k * 0.1, role = "petal", name = "Plume", mesh = "s_aq_plume" })
		end
		if k == 1 then
			-- face on the collar just under the plume
			Face.build(B, { face = { kind = "ellipsoid", c = { x, top[2] - 0.35, z }, r = { 0.36, 0.4, 0.36 } }, bone = tb, mood = mood(B), detail = detail, kind = "cute", spacing = 0.16, y = 0, d = 0.24, mouthY = -0.2, mouthW = 0.2, lidCol = "secondary", noBrows = true })
		end
	end
	B:socket("core", at(0, 1.5, 0), "Body")
	B:setRig("gait", "sway")
end

local function giant(B: any, ctx: any, has: any)
	local t, detail = ctx.traits, ctx.detail
	local n = if detail <= 0 then 3 elseif detail == 1 then 4 elseif detail == 2 then 5 else 6
	local w = 1.25 * (if has("fat", "chubby") then 1.15 else 1)
	-- rearing out of the ground: from the mound up and over, the mouth facing forward and down
	local pts = {}
	for i = 0, n do
		local v = 1 - i / n -- 1 at the head
		local a = v * rad(100)
		pts[i] = { sin(v * 2.2) * 0.25, 0.3 + sin(a) * 3.4, 0.8 - (1 - cos(a)) * 1.6 }
	end
	B.boneIndex.Body.pos = { pts[n][1], pts[n][2], pts[n][3] }
	chain(B, pts, n, { w = function(i)
		return w * (1 - (i - 1) / n * -0.12)
	end, ringed = true, depth = 1.0, over = 0.4, banded = has("band", "segment") and detail >= 3, mat = if has("lava", "rock") then "stone" else "skin" })
	-- mound of earth / ice / sand where it breaks out
	local q = pts[n]
	B:ell(w * 3.2, w * 0.9, w * 3.0, at(q[1], 0.15, q[3] + 0.2), { col = if has("ice") then "glass" elseif has("lava") then "darkStone" else "darker", mat = if has("ice") then "glass" else "stone", pri = 1.8, role = "body", name = "Mound", mesh = "boulder" })
	-- head: a collar and the round toothed maw facing forward
	local p = pts[0]
	local hb = B:bone("Head", "Seg1", p[1], p[2], p[3])
	B:setRig("head", hb)
	local c = { p[1], p[2] - 0.1, p[3] - w * 0.35 }
	local r = { w * 0.62, w * 0.62, w * 0.5 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", bone = hb, pri = 1.05, role = "head", name = "Head", mesh = false })
	local maw = B:cyl(w * 0.3, w * 1.1, at(c[1], c[2] - w * 0.05, c[3] - r[3] * 0.8, 0, rad(90), rad(-20)), { col = "inner", mat = "skin", bone = hb, pri = 1.2, role = "snout", name = "Maw", mesh = "s_aq_worm_mouth" })
	local _ = maw
	if not has("no eyes", "eyeless", "blind") then
		Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = hb, mood = mood(B), detail = detail, kind = if t.cute or t.size == "Tiny" or t.size == "Small" then "cute" else "fierce",
			spacing = r[1] * 0.72, y = r[2] * 0.6, d = w * 0.22, noMouth = true, lidCol = "primary" })
	end
	if has("electric", "crackling") and detail >= 2 then
		for i = 1, 2 do
			local s = pts[i + 1]
			B:ell(w * 0.3, w * 1.4, w * 0.3, at(s[1] + w * 0.8, s[2], s[3], 0, 0, rad(25)), { col = "glow", mat = "neon", glow = true, bone = "Seg" .. (i + 1), pri = 3.2, role = "gem", name = "Spark", noCore = true })
		end
	end
	if has("lava", "glowing") and detail >= 2 then
		for i = 1, 2 do
			local s = pts[i]
			B:ell(w * 1.9, w * 0.3, w * 0.35, at(s[1], s[2], s[3]), { col = "glow", mat = "neon", glow = true, bone = "Seg" .. i, pri = 3.0 + i * 0.1, role = "gem", name = "Crack", noCore = true })
		end
	end
	B:socket("mouth", at(c[1], c[2] - w * 0.1, c[3] - r[3] * 1.1), hb)
	B:socket("core", at(pts[1][1], pts[1][2], pts[1][3]), "Seg1")
	B:setRig("gait", "sway")
end

local function slug(B: any, ctx: any, has: any)
	local t, detail = ctx.traits, ctx.detail
	local y = 0.5
	B.boneIndex.Body.pos = { 0, y, 0 }
	B:ell(1.6, 0.9, 4.2, at(0, y, 0.3), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Foot", mesh = "s_aq_seal_hips" })
	B:ell(1.5, 0.95, 1.9, at(0, y + 0.35, -0.3), { col = "secondary", mat = "skin", pri = 1.2, role = "body", name = "MantleHump", mesh = false })
	local hb = B:bone("Head", "Body", 0, y + 0.1, -1.6)
	B:setRig("head", hb)
	local c = { 0, y + 0.25, -1.75 }
	local r = { 0.62, 0.55, 0.55 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", bone = hb, pri = 1.05, role = "head", name = "Head", mesh = false })
	if detail >= 1 then
		B:mlimb({ 0.2, c[2] + r[2] * 0.6, c[3] }, { 0.42, c[2] + r[2] * 2.3, c[3] - 0.3 }, 0.14, { col = "primary", mat = "skin", bone = hb, pri = 1.6, role = "antenna", name = "Stalk#" }, 0.05)
		B:mball(0.3, at(0.43, c[2] + r[2] * 2.35, c[3] - 0.32), { col = "pupil", mat = "glass", bone = hb, pri = 1.7, role = "eye", name = "StalkEye#", noCore = true })
	end
	-- the eyes ride on the stalks; the face is a mouth under them
	local mp = Face.onEllipsoid(c, r, 0, -r[2] * 0.3)
	B:ell(0.42, 0.1, 0.12, at(mp[1], mp[2], mp[3] + 0.02, rad(-15), 0, 0), { col = "mouth", mat = "skin", bone = hb, pri = 1.8, role = "mouth", name = "Mouth", noCore = true })
	local _ = mood
	if has("glow", "lava", "burning") and detail >= 2 then
		B:ell(1.3, 0.25, 3.4, at(0, 0.12, 1.3), { col = "glow", mat = "neon", glow = true, pri = 2.8, role = "gem", name = "Trail", noCore = true })
	end
	B:setRig("gait", "inch")
	local _ = t
end

local function bear(B: any, ctx: any, has: any)
	local detail = ctx.detail
	local y = 1.0
	B.boneIndex.Body.pos = { 0, y, 0 }
	local pts = straightPts(3, 2.6, y, 0)
	chain(B, pts, 3, { w = function(i)
		return 1.35 - math.abs(i - 2) * 0.12
	end, ringed = true, depth = 1.05, over = 0.6, parent = "Body" })
	for i = 1, (if detail >= 2 then 4 else 2) do
		local z = -0.9 + (i - 1) * 0.6
		Parts.legPair(B, { tag = tostring(i), parent = "Seg" .. math.min(3, math.ceil(i * 0.75)), x = 0.5, y = y - 0.35, z = z, w = 0.26, kind = "claw", claws = detail >= 3, phase = i * 0.25 })
	end
	local c, r = roundHead(B, ctx, pts[0], 1.15, { fwd = 0.15, eye = 0.2, mouth = false })
	B:cyl(0.35, 0.45, at(c[1], c[2] - 0.08, c[3] - r[3] * 0.9, 0, rad(90), 0), { col = "inner", mat = "skin", bone = "Head", pri = 1.5, role = "snout", name = "TubeSnout" })
	B:setRig("gait", "waddle")
end

function Worms.build(B: any, ctx: any)
	local has = reader(ctx)
	local k = kindOf(has)
	if k == "inch" then
		return inch(B, ctx, has)
	elseif k == "cater" then
		return cater(B, ctx, has)
	elseif k == "centipede" then
		return centipede(B, ctx, has)
	elseif k == "grub" then
		return grub(B, ctx, has)
	elseif k == "flat" then
		return flat(B, ctx, has)
	elseif k == "leech" then
		return leech(B, ctx, has)
	elseif k == "tube" then
		return tube(B, ctx, has)
	elseif k == "giant" then
		return giant(B, ctx, has)
	elseif k == "slug" then
		return slug(B, ctx, has)
	elseif k == "bear" then
		return bear(B, ctx, has)
	end
	return earth(B, ctx, has)
end

return Worms
