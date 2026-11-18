--!strict
-- Serpent: snakes, eels, salamanders, sea serpents, eastern (long) dragons, and the long creatures filed under
-- the plan that are better built by a neighbour (worms, caterpillars and slugs -> Plans/Worms; tentacled ->
-- Plans/Cephalopod; snake-bodied people -> Plans/SeaMammal.mer). The Worm route (kind "Worm") goes to
-- Plans/Worms.
--
-- The body is a chain of overlapping tapering segments, one bone each (rig.spine), laid along a path that is the
-- pose: an S on the ground (snakes), a flat spiral (pythons, coiled), humps above a water line (sea serpents), a
-- floating wave (long dragons), a raised fore body (cobras). Heads by type: viper triangle, slim colubrid head,
-- cobra hood, eel / fish head, flat salamander head, horned dragon head.

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Heads = require(script.Parent.Parent.Heads)
local Face = require(script.Parent.Parent.Face)
local Worms = require(script.Parent.Worms)
local Cephalopod = require(script.Parent.Cephalopod)
local SeaMammal = require(script.Parent.SeaMammal)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

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

local function kindOf(ctx: any, has: any): string
	local t = ctx.traits
	if ctx.kind == "Worm" then
		return "worm"
	end
	if has("lamia", "naga", "melusine", "shahmaran", "mother of monsters", "lower half", "lower body", "serpent-tailed", "mami wata") then
		return "naga"
	end
	if t.tentacles or has("kraken", "octopus", "squid", "tentacle") then
		return "tentacle"
	end
	if has("caterpillar", "woolly bear", "silkworm", "slug", "leech", "worm", "caecilian", "blind snake") and not has("dragon", "lindworm", "tatzelwurm", "wyrm") then
		return "worm"
	end
	if has("hydra", "scylla", "heads") then
		return "hydra"
	end
	if has("salamander", "newt", "mudpuppy", "olm", "axolotl", "hellbender") then
		return "salamander"
	end
	if has("eel", "oarfish", "lamprey", "hagfish", "frilled shark", "snakehead", "basilosaurus", "amphiuma", "ribbon eel") then
		return "eel"
	end
	if has("dragon", "coatl", "amphiptere", "sky serpent", "feathered serpent", "horned serpent", "taniwha", "ninki", "lindworm", "tatzelwurm", "nidhogg", "ryujin", "wyrm") then
		return "dragon"
	end
	if has("sea serpent", "ogopogo", "lake monster", "bakunawa", "sea kaiju", "inkanyamba", "humped", "humps", "looping") then
		return "sea"
	end
	return "snake"
end

-- Path of the body: n+1 points from the head end (index 0) to the tail end.
local function path(pose: string, n: number, w: number, len: number, eelWave: boolean?): { { number } }
	local pts = {}
	for i = 0, n do
		local u = i / n
		local x, y, z
		if pose == "coil" then
			-- flat spiral: the tail outside, winding in to the head end, which rises in the middle
			local a = u * math.pi * 2.1
			local r = 0.7 + u * 1.3
			x, z = sin(a + 0.4) * r, -cos(a + 0.4) * r + 0.5
			y = w * 0.42 + (1 - u) * w * 0.5
			if i == 0 then
				x, y, z = x * 0.4, y + w * 0.9, z - 0.5
			end
		elseif pose == "humps" then
			z = -1.6 + u * len
			x = sin(u * math.pi * 1.1) * 0.35
			y = w * 0.45 + math.max(0, sin(u * math.pi * 2.6 - 0.2)) * 1.5 * (1 - u * 0.45)
			if i == 0 then
				y += 2.0
			elseif i == 1 then
				y += 1.0
			end
		elseif pose == "wave" then
			z = -1.4 + u * len
			x = sin(u * math.pi * 1.4) * 0.45
			y = 1.9 + sin(u * math.pi * 2.2 + 0.6) * 0.7 * (if eelWave then 0.35 else 1)
			if i == 0 then
				y += 0.4
			end
		elseif pose == "prowl" then
			-- legged long dragon: a low rolling wave, belly just clear of the ground so the legs stay short
			z = -1.4 + u * len
			x = sin(u * math.pi * 1.4) * 0.45
			y = w * 0.95 + 0.25 + sin(u * math.pi * 2.2 + 0.6) * 0.4 * (0.4 + u * 0.6)
			if i == 0 then
				y += 0.55
			end
		elseif pose == "low" then
			z = -1.0 + u * len
			x = sin(u * math.pi * 1.2) * 0.35 * u
			y = w * 0.5 + 0.25 * (1 - u)
		else
			z = -1.2 + u * len
			x = sin(u * math.pi * 1.6) * 0.75
			y = w * 0.42 * (1 - u * 0.35)
			if pose == "raised" and i == 0 then
				y += 2.3
				z += 0.55
			elseif pose == "raised" and i == 1 then
				y += 1.25
				z += 0.2
			elseif pose == "raised" and i == 2 then
				y += 0.35
			end
		end
		pts[i] = { x, y, z }
	end
	return pts
end

-- Body chain on Seg bones. o: w, taper, flat (depth / width), banded, col, mat, pri, scutes
local function body(B: any, pts: { { number } }, n: number, o: any): string
	local parent = "Body"
	for i = 1, n do
		local a, b = pts[i - 1], pts[i]
		local bname = B:bone("Seg" .. i, parent, a[1], a[2], a[3])
		B:addRig("spine", bname)
		local ww = o.w * (1 - (i - 1) / n * (o.taper or 0.55))
		local banded = o.banded and i % 2 == 0
		B:limb(a, b, ww, { col = if banded then "secondary" else (o.col or "primary"), mat = o.mat or "scale", bone = bname, pri = (o.pri or 1) + i * 0.12, role = "body", name = "Seg" .. i,
			trail = i == n and not o.tip, depth = ww * (o.flat or 1.12) }, o.over or 0.8)
		if o.scutes and i <= n - 1 then
			-- belly scutes in the belly colour, sunk under each segment
			B:limb({ a[1], a[2] - ww * 0.24, a[3] }, { b[1], b[2] - ww * 0.24, b[3] }, ww * 0.62, { col = "belly", mat = "scale", bone = bname, pri = 3.5 + i * 0.05, role = "detail", name = "Scutes", depth = ww * 0.82, mesh = false }, 0.3)
		end
		parent = bname
	end
	return parent
end

-- Snake head on bone Head at p, size s. kind: viper | slim | cobra | python | eel | blind
local function snakeHead(B: any, t: any, p: { number }, s: number, kind: string, has: any): any
	local detail = t.detail or 2
	local viper = kind == "viper"
	local c = { p[1], p[2] + s * 0.05, p[3] - s * 0.25 }
	local r = if viper then { s * 0.52, s * 0.3, s * 0.58 } elseif kind == "python" then { s * 0.42, s * 0.32, s * 0.6 } else { s * 0.4, s * 0.3, s * 0.56 }
	local head = B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "scale", bone = "Head", pri = 1.05, role = "head", name = "Head",
		mesh = if viper then "s_aq_viper_head" else "s_aq_snake_head" })
	local members = {}
	-- snout: narrower, in front
	local sc = { c[1], c[2] - s * 0.04, c[3] - r[3] * 0.72 }
	local sr = { r[1] * (if viper then 0.55 else 0.72), r[2] * 0.78, r[3] * 0.55 }
	if has("upturned") then
		sr[2] *= 1.2
		sc[2] += s * 0.06
	end
	table.insert(members, B:ell(sr[1] * 2, sr[2] * 2, sr[3] * 2, at(sc[1], sc[2], sc[3], rad(if has("upturned") then -14 else 4), 0, 0), { col = "primary", mat = "scale", bone = "Head", pri = 1.25, role = "snout", name = "Snout" }))
	if viper and detail >= 2 then
		-- jaw-hinge bulges behind the eyes: the triangle
		local a, b2 = B:mell(r[1] * 0.9, r[2] * 1.3, r[3] * 0.8, at(r[1] * 0.45, c[2] - s * 0.04, c[3] + r[3] * 0.35), { col = "primary", mat = "scale", bone = "Head", pri = 1.7, role = "head", name = "Cheek#", mesh = false })
		table.insert(members, a)
		table.insert(members, b2)
	end
	B:sculpt(head, head.mesh, members)
	local jb = B:bone("Jaw", "Head", c[1], c[2] - s * 0.12, c[3] + r[3] * 0.3)
	B:setRig("jaw", jb)
	if detail >= 1 then
		local open = has("open mouth", "white open mouth", "inky black mouth", "spitting")
		B:ell(r[1] * 1.6, r[2] * 0.7, r[3] * 1.65, at(c[1], c[2] - r[2] * 0.62, c[3] - r[3] * 0.2, rad(if open then 22 else 4), 0, 0), { col = "belly", mat = "scale", bone = jb, pri = 1.6, role = "jaw", name = "Jaw", mesh = false })
		if open and detail >= 2 then
			B:ell(r[1] * 1.2, r[2] * 0.4, r[3] * 1.3, at(c[1], c[2] - r[2] * 0.45, c[3] - r[3] * 0.3, rad(12), 0, 0), { col = if has("white") then "tooth" else "mouth", mat = "skin", bone = jb, pri = 2.3, role = "mouth", name = "Gape", mesh = false })
		end
	end
	if detail >= 2 and (t.fangs or has("fang", "viper", "cobra", "mamba", "taipan", "venom", "spitting")) then
		B:mwedge(s * 0.06, s * 0.22, s * 0.1, at(r[1] * 0.35, c[2] - r[2] * 0.75, sc[3] - sr[3] * 0.2, math.pi, 0, 0), { col = "tooth", mat = "hard", bone = "Head", pri = 3.0, role = "tooth", name = "Fang#" })
	end
	if detail >= 2 and has("horn", "eyelash", "horned") then
		B:mlimb({ r[1] * 0.5, c[2] + r[2] * 0.6, c[3] - r[3] * 0.2 }, { r[1] * 0.65, c[2] + r[2] * 1.6, c[3] - r[3] * 0.05 }, s * 0.1, { col = "secondary", mat = "hard", bone = "Head", pri = 2.6, role = "horn", name = "BrowHorn#", trail = true }, 0.1)
	end
	if detail >= 3 and (has("tongue") or t.silly or mood(B) == "Silly") then
		B:limb({ 0, c[2] - r[2] * 0.4, sc[3] - sr[3] * 0.8 }, { 0, c[2] - r[2] * 0.6, sc[3] - sr[3] * 2.2 }, s * 0.06, { col = "tongue", mat = "skin", bone = jb, pri = 4.0, role = "detail", name = "Tongue", mesh = false }, 0.05)
	end
	local fierce = viper or has("cobra", "mamba", "taipan", "python", "titanoboa", "king", "monster", "colossal", "giant") or (not t.cute and (t.power or 5) >= 7)
	local kindF = if t.undead or t.robot or t.glowEyes then "glow" elseif fierce and not t.cute and t.size ~= "Tiny" then "fierce" else "cute"
	Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, mouthFace = { kind = "ellipsoid", c = sc, r = sr }, bone = "Head", mood = mood(B), detail = detail, kind = kindF,
		spacing = r[1] * 0.62, y = r[2] * 0.35, d = s * (if has("huge eyes", "big eyes", "boomslang") then 0.36 else 0.27), mouthY = -sr[2] * 0.3, mouthW = s * 0.34,
		noMouth = mood(B) == "Neutral", lidCol = "primary", noBrows = not viper })
	B:socket("mouth", at(c[1], c[2] - s * 0.1, sc[3] - sr[3]), "Head")
	return { c = c, r = r, top = { c[1], c[2] + r[2], c[3] }, s = s }
end

local function serpent(B: any, ctx: any, kind: string, has: any)
	local t, detail = ctx.traits, ctx.detail
	local n = if detail <= 0 then 3 elseif detail == 1 then 4 elseif detail == 2 then 6 else 7
	local snakeKind = "slim"
	if has("viper", "adder", "rattle", "bushmaster", "fer-de-lance", "copperhead", "cottonmouth", "gaboon", "sidewinder", "triangle head", "spearhead", "heat pit") then
		snakeKind = "viper"
	elseif has("cobra", "hood", "naga", "king cobra") then
		snakeKind = "cobra"
	elseif has("python", "boa", "anaconda", "titanoboa", "constrictor", "coiled") then
		snakeKind = "python"
	end
	local thick = snakeKind == "python" or has("thick", "fat", "chunky", "chubby", "bulging", "huge", "colossal", "titanoboa")
	local slim = has("slender", "slim", "thin", "vine", "tree snake", "mamba", "whip", "garter", "flying snake", "ribbon")
	local w = 0.85 * (0.9 + (t.durability or 5) * 0.03) * (if thick then 1.25 elseif slim then 0.7 else 1)
	local len = 4.8 * (if slim then 1.15 else 1)
	local pose = "s"
	-- feathered / winged sky serpents float without legs
	local legless = kind == "dragon" and has("coatl", "feather", "amphiptere", "sky serpent", "rainbow serpent")
	if kind == "sea" then
		pose = "humps"
	elseif kind == "dragon" then
		pose = if has("lindworm", "tatzelwurm", "taniwha", "ninki") then "low" elseif legless then "wave" else "prowl"
	elseif kind == "eel" and not has("garden") then
		pose = "wave"
	elseif snakeKind == "cobra" or has("standing tall", "raised") then
		pose = "raised"
	elseif snakeKind == "python" or has("coil", "curled", "ball") then
		pose = "coil"
	end
	if kind == "eel" then
		w *= 0.8
	end
	if pose == "coil" then
		w *= 0.85
	end
	local pts = path(pose, n, w, len, kind == "eel")
	if kind == "eel" and pose == "wave" then
		for i = 0, n do
			pts[i][2] -= 0.7
		end
	end
	B.boneIndex.Body.pos = { pts[1][1], pts[1][2], pts[1][3] }
	local banded = has("band", "rings", "ringed", "krait", "coral", "milk snake", "striped", "rainbow", "hourglass") or (kind == "worm")
	local last = body(B, pts, n, { w = w, banded = banded, flat = if kind == "eel" then 0.75 else 1.12, scutes = detail >= 3 and kind ~= "eel" and kind ~= "dragon",
		mat = if kind == "eel" then "skin" else "scale", taper = if kind == "dragon" then 0.45 else 0.55 })
	-- tail tip (rattle, paddle tail for sea snakes, fin for eels)
	local tl = pts[n]
	local tipDir = { tl[1] - pts[n - 1][1], tl[2] - pts[n - 1][2], tl[3] - pts[n - 1][3] }
	local dl = math.sqrt(tipDir[1] ^ 2 + tipDir[2] ^ 2 + tipDir[3] ^ 2)
	local tip = { tl[1] + tipDir[1] / dl * 0.8, tl[2] + tipDir[2] / dl * 0.8 - 0.05, tl[3] + tipDir[3] / dl * 0.8 }
	tip[2] = math.max(tip[2], w * 0.12)
	B:limb(tl, tip, w * 0.32, { col = if has("rattle") then "horn" else "primary", mat = "scale", bone = last, pri = 2.1, role = "tail", trail = true }, 0.3)
	if has("rattle") and detail >= 2 then
		for i = 1, 2 do
			local u = 0.6 + i * 0.35
			B:ell(w * 0.38, w * 0.3, w * 0.3, at(tl[1] + tipDir[1] / dl * u, tl[2] + tipDir[2] / dl * u, tl[3] + tipDir[3] / dl * u), { col = "horn", mat = "hard", bone = last, pri = 3.2 + i * 0.1, role = "detail", name = "Rattle", mesh = false })
		end
	end
	if has("paddle tail", "sea snake", "sea krait") and detail >= 1 then
		B:ell(0.1, w * 0.9, 0.8, at(tip[1], tip[2] + w * 0.15, tip[3] + 0.1), { col = "secondary", mat = "skin", bone = last, pri = 2.2, role = "fin", name = "Paddle", mesh = "s_aq_caudal_fan" })
	end
	-- head
	local hp = pts[0]
	B:bone("Head", "Seg1", hp[1], hp[2], hp[3])
	B:setRig("head", "Head")
	local headS = w * (if snakeKind == "viper" then 1.6 else 1.35)
	local info: any
	if kind == "eel" then
		-- fish head: the fish body sculpt on a long head ellipsoid, a gaping mouth, pectoral fins
		local s = headS
		local c = { hp[1], hp[2] + s * 0.02, hp[3] - s * 0.3 }
		local r = { s * 0.38, s * 0.42, s * 0.62 }
		B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", bone = "Head", pri = 1.05, role = "head", name = "Head", mesh = "s_aq_fish_body" })
		local jb = B:bone("Jaw", "Head", c[1], c[2] - s * 0.15, c[3] + r[3] * 0.2)
		B:setRig("jaw", jb)
		local sucker = has("sucker", "lamprey", "hagfish")
		if sucker then
			B:cyl(s * 0.3, s * 0.62, at(c[1], c[2] - s * 0.05, c[3] - r[3] * 0.92, 0, rad(90), 0), { col = "inner", mat = "skin", bone = "Head", pri = 1.5, role = "snout", name = "Sucker", mesh = "s_aq_worm_mouth" })
		elseif detail >= 1 then
			local big = has("pelican", "gulper", "huge mouth", "gaping")
			B:ell(r[1] * (if big then 2.6 else 1.6), r[2] * (if big then 1.4 else 0.6), r[3] * (if big then 1.8 else 1.5), at(c[1], c[2] - r[2] * (if big then 0.8 else 0.55), c[3] - r[3] * 0.15, rad(10), 0, 0),
				{ col = "belly", mat = "skin", bone = jb, pri = 1.5, role = "jaw", name = "Jaw", mesh = false })
			if detail >= 2 and not has("ribbon", "garden") then
				Parts.teeth(B, { bone = "Head", y = c[2] - r[2] * 0.25, z = c[3] - r[3] * 0.75, r = r[1] * 0.45, n = 2, h = s * 0.13, pri = 3.0 })
			end
		end
		if detail >= 1 and not sucker then
			B:mell(s * 0.42, 0.08, s * 0.3, at(r[1] * 1.0, c[2] - r[2] * 0.2, c[3] + r[3] * 0.55, 0, rad(-25), rad(-20)), { col = "secondary", mat = "skin", bone = "Head", pri = 2.0, role = "fin", name = "Pectoral#" })
		end
		if has("frill", "gills") and detail >= 2 then
			for i = 1, 2 do
				B:mell(s * 0.12, r[2] * 1.7, s * 0.14, at(r[1] * 0.85, c[2], c[3] + r[3] * (0.45 + i * 0.18)), { col = "inner", mat = "skin", bone = "Head", pri = 3 + i * 0.1, role = "detail", name = "Gill#", mesh = false })
			end
		end
		if has("crest", "red crest") and detail >= 1 then
			B:limb({ 0, c[2] + r[2] * 0.6, c[3] }, { 0, c[2] + r[2] * 3.2, c[3] + r[3] * 0.7 }, s * 0.18, { col = "secondary", mat = "skin", bone = "Head", pri = 1.8, role = "fin", name = "Crest", trail = true, mesh = false }, 0.1)
		end
		local fierce = not t.cute and ((t.power or 5) >= 6 or has("monster", "teeth", "storm"))
		Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = "Head", mood = mood(B), detail = detail, kind = if fierce then "fierce" else "cute",
			spacing = r[1] * 0.62, y = r[2] * 0.3, d = s * 0.26, mouthY = -r[2] * 0.35, mouthW = s * 0.35, noMouth = sucker or mood(B) == "Neutral", lidCol = "primary" })
		B:socket("mouth", at(c[1], c[2] - s * 0.12, c[3] - r[3]), "Head")
		info = { c = c, r = r, top = { c[1], c[2] + r[2], c[3] }, s = s }
		-- ribbon dorsal fin along the back
		if detail >= 1 then
			for i = 1, math.min(n, if detail >= 3 then 4 else 3) do
				local a, b = pts[i - 1], pts[i]
				local ww = w * (1 - (i - 1) / n * 0.55)
				local mid = { (a[1] + b[1]) / 2, (a[2] + b[2]) / 2 + ww * 0.5, (a[3] + b[3]) / 2 }
				local f, l = Geom.between(a[1], a[2] + ww * 0.5, a[3], b[1], b[2] + ww * 0.5, b[3], "Z")
				local _ = mid
				B:part({ shape = "Ellipsoid", size = { 0.08, ww * 0.9, l * 1.2 }, cf = f, col = "secondary", mat = "skin", bone = "Seg" .. i, pri = 2.4 + i * 0.1, role = "fin", name = "FinRibbon", mesh = false })
			end
		end
	elseif kind == "dragon" then
		local tt = table.clone(t)
		tt.teeth = true
		info = Heads.reptile(B, { p = { hp[1], hp[2] - headS * 0.1, hp[3] + headS * 0.1 }, s = headS, eyes = if t.cute or t.size == "Tiny" then "cute" else "fierce" }, tt)
		if detail >= 1 then
			-- antlers (long dragons) or swept horns
			if has("lindworm", "tatzelwurm", "nidhogg") then
				Parts.horns(B, { bone = "Head", x = headS * 0.22, y = info.top[2] - headS * 0.08, z = info.top[3], len = headS * 0.7, w = headS * 0.16, kind = "swept", segs = 2, pri = 2.2, col = "horn" })
			else
				Parts.antlers(B, { bone = "Head", x = headS * 0.2, y = info.top[2] - headS * 0.06, z = info.top[3] + headS * 0.05, len = headS * 0.75 })
			end
		end
		if detail >= 2 then
			-- whiskers from the snout
			local m = info.mouth
			B:mlimb({ headS * 0.2, m[2] + headS * 0.12, m[3] + headS * 0.35 }, { headS * 0.95, m[2] - headS * 0.25, m[3] + headS * 1.2 }, headS * 0.07, { col = "secondary", mat = "skin", bone = "Head", pri = 2.6, role = "antenna", name = "Whisker#", trail = true }, 0.1)
			-- mane tufts along the neck
			local pts2 = {}
			for i = 1, math.min(3, n - 1) do
				local p = pts[i]
				table.insert(pts2, { p[1], p[2] + w * 0.3, p[3] - 0.1, 1 - i * 0.15, rad(-25), "Seg" .. i })
			end
			Parts.spikeRow(B, { points = pts2, h = w * 0.85, pri = 2.8, col = "secondary" })
		end
		if has("pearl", "orb") and detail >= 2 then
			B:ball(headS * 0.55, at(info.mouth[1], info.mouth[2] - headS * 0.2, info.mouth[3] - headS * 0.25), { col = "gem", mat = "glass", bone = "Head", pri = 2.4, role = "gem", name = "Pearl" })
		end
	else
		local hk = if kind == "sea" then "python" else snakeKind
		info = snakeHead(B, t, hp, headS * (if kind == "sea" then 1.2 else 1), hk, has)
		if kind == "sea" and detail >= 1 then
			Parts.ears(B, { bone = "Head", x = info.r[1] * 0.8, y = info.c[2] + info.r[2] * 0.2, z = info.c[3] + info.r[3] * 0.4, kind = "fin", s = info.s * 0.7, pri = 2.3 })
		end
	end
	if (t.horns or (t.crown and (t.mythical or has("crown")))) and kind ~= "dragon" and detail >= 1 then
		Parts.horns(B, { bone = "Head", x = info.s * 0.22, y = info.top[2] - info.s * 0.08, z = info.top[3], len = info.s * 0.7, w = info.s * 0.16, kind = "swept", segs = 2, pri = 2.2, col = if t.crown then "gold" else "horn" })
	end
	-- cobra hood: one spread hood behind the head on the raised neck
	if snakeKind == "cobra" and kind == "snake" and detail >= 1 then
		local p = pts[0]
		local q = pts[1]
		local hs = headS
		B:ell(hs * 1.9, hs * 1.75, hs * 0.32, at(p[1] * 0.6 + q[1] * 0.4, p[2] * 0.6 + q[2] * 0.4 - hs * 0.05, p[3] * 0.6 + q[3] * 0.4 + hs * 0.25, rad(-15), 0, 0),
			{ col = "primary", mat = "scale", bone = "Seg1", pri = 1.35, role = "hood", name = "Hood", mesh = "s_aq_hood" })
		if detail >= 3 then
			B:ell(hs * 0.9, hs * 0.75, hs * 0.2, at(p[1] * 0.6 + q[1] * 0.4, p[2] * 0.6 + q[2] * 0.4 - hs * 0.05, p[3] * 0.6 + q[3] * 0.4 + hs * 0.08, rad(-15), 0, 0),
				{ col = "belly", mat = "scale", bone = "Seg1", pri = 3.4, role = "detail", name = "HoodFront", mesh = false })
		end
	end
	-- fin crest (sea serpents, sea dragons)
	if detail >= 2 and (kind == "sea" or (kind == "dragon" and (t.fins or t.aquatic or has("sea", "fin")))) then
		for i = 1, math.min(3, n - 1) do
			local p = pts[i]
			B:ell(0.1, w * 1.3, len / n * 0.85, at(p[1], p[2] + w * 0.5, p[3] + len / n * 0.4), { col = "secondary", mat = "skin", bone = "Seg" .. i, pri = 2.6 + i * 0.1, role = "fin", name = "Crest", mesh = "s_aq_dorsal" })
		end
	elseif detail >= 2 and t.spikes and kind ~= "dragon" then
		local sp = {}
		for i = 1, math.min(3, n - 1) do
			local p = pts[i]
			table.insert(sp, { p[1], p[2] + w * 0.35, p[3] + len / n * 0.4, 1, 0, "Seg" .. i })
		end
		Parts.spikeRow(B, { points = sp, h = w * 0.7, pri = 2.8 })
	end
	-- legs: long dragons four short clawed legs, lindworms two, tiny-legged eels / sirens two stubs
	if (kind == "dragon" and not legless) or t.legs or has("foreleg", "tiny legs", "tiny arms", "lizard") then
		local four = kind == "dragon" and not has("lindworm", "two clawed", "tatzelwurm", "foreleg")
		local p = pts[1]
		local tiny = has("tiny legs", "tiny arms")
		local lw = w * (if tiny then 0.18 elseif kind == "dragon" then 0.4 else 0.32)
		local ly = math.max(p[2] - w * 0.2, 0.4)
		Parts.legPair(B, { tag = "F", parent = "Seg1", x = w * (if pose == "low" then 0.6 else 0.45), y = (if pose == "low" then math.max(ly, w * 0.75) else ly), z = p[3], w = lw, kind = "claw", claws = not tiny, phase = 0, splay = if pose == "wave" or pose == "prowl" then w * 0.3 else 0 })
		if four and n >= 3 then
			local q = pts[math.min(3, n - 1)]
			Parts.legPair(B, { tag = "H", parent = "Seg" .. math.min(3, n - 1), x = w * 0.42, y = math.max(q[2] - w * 0.2, 0.4), z = q[3], w = lw * 0.95, kind = "claw", claws = true, phase = 0.5, splay = if pose == "wave" or pose == "prowl" then w * 0.3 else 0 })
		end
	end
	local wingy = has("winged", " wings", " wing ", "feather", "amphiptere") and not has("wingless")
	if (wingy or (kind ~= "dragon" and (t.wings or t.flies))) and not t.noWings then
		local p = pts[1]
		Parts.wings(B, { parent = "Seg1", x = w * 0.35, y = p[2] + w * 0.3, z = p[3], span = 2.6, kind = if has("feather") then "feather" else t.wingKind })
	end
	if has("egg") and detail >= 2 then
		local p = pts[math.floor(n / 2)]
		B:ell(w * 1.5, w * 1.35, w * 1.8, at(p[1], p[2] + w * 0.1, p[3]), { col = "primary", mat = "scale", bone = "Seg" .. math.floor(n / 2), pri = 2.5, role = "body", name = "Bulge", mesh = false })
	end
	B:socket("core", at(pts[1][1], pts[1][2], pts[1][3]), "Seg1")
	B:setRig("gait", "slither")
end

-- Salamanders and newts: a low lizard-like body on four splayed legs, a broad flat head with small eyes on top,
-- a tall flat tail; gills (mudpuppy, axolotl, olm), a back crest (crested newt), blotches.
local function salamander(B: any, ctx: any, has: any)
	local t, detail = ctx.traits, ctx.detail
	local giant = has("giant", "huge")
	local w = if giant then 1.0 else 0.8
	local y = 0.62
	local L = 2.4
	B.boneIndex.Body.pos = { 0, y, 0 }
	-- trunk: two masses on Body
	local c = { 0, y, 0.05 }
	local r = { w * 0.62, w * 0.42, L * 0.36 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Trunk", mesh = "s_aq_seal_hips" })
	if detail >= 2 then
		B:ell(r[1] * 1.7, r[2] * 1.0, r[3] * 1.8, at(0, y - r[2] * 0.45, c[3]), { col = "belly", mat = "skin", pri = 2.0, role = "detail", name = "Belly", mesh = false })
	end
	-- tail: flattened side to side, wavy
	local tb = Parts.tail(B, { start = { 0, y, c[3] + r[3] * 0.75 }, dir = { 0.15, -0.08, 1 }, len = L * 0.85, w = w * 0.62, segs = if detail >= 2 then 3 else 2, taper = 0.66, flat = 0.55, pri = 1.15 })
	local _ = tb
	-- head
	local hb = B:bone("Head", "Body", 0, y + 0.02, c[3] - r[3] * 0.85)
	B:setRig("head", hb)
	local s = w * 1.15
	local hc = { 0, y + 0.02, c[3] - r[3] - s * 0.25 }
	local hr = { s * 0.55, s * 0.28, s * 0.48 }
	B:ell(hr[1] * 2, hr[2] * 2, hr[3] * 2, at(hc[1], hc[2], hc[3]), { col = "primary", mat = "skin", bone = hb, pri = 1.05, role = "head", name = "Head", mesh = "s_aq_newt_head" })
	if detail >= 1 then
		B:ell(hr[1] * 1.8, hr[2] * 0.75, hr[3] * 1.7, at(0, hc[2] - hr[2] * 0.5, hc[3] - hr[3] * 0.08), { col = "belly", mat = "skin", bone = hb, pri = 1.6, role = "jaw", name = "Jaw", mesh = false })
	end
	-- eyes on top-front: bulging, wide set
	Face.build(B, { face = { kind = "ellipsoid", c = { hc[1], hc[2] + hr[2] * 0.35, hc[3] }, r = hr }, bone = hb, mood = mood(B), detail = detail,
		kind = if has("blind", "olm", "eyeless") then "glow" else "cute", spacing = hr[1] * 0.62, y = hr[2] * 0.4, d = if has("blind", "olm") then s * 0.08 else s * 0.3,
		mouthY = -hr[2] * 0.7, mouthW = s * 0.6, forceMouth = true, lidCol = "primary", noBrows = true })
	if has("gill", "mudpuppy", "axolotl", "olm", "siren") and detail >= 1 then
		for i = 1, (if detail >= 2 then 3 else 1) do
			local a = rad(-30 + (i - 1) * 30)
			B:mlimb({ hr[1] * 0.75, hc[2] + hr[2] * 0.2, hc[3] + hr[3] * 0.6 }, { hr[1] * 0.75 + s * 0.6 * cos(a), hc[2] + hr[2] * 0.2 + s * 0.6 * sin(a) + s * 0.15, hc[3] + hr[3] * 0.9 }, s * 0.12,
				{ col = "inner", mat = "skin", bone = hb, pri = 1.9 + i * 0.2, role = "antenna", name = "Gill" .. i .. "#", trail = true }, 0.1)
		end
	end
	if has("crest", "jagged") and detail >= 2 then
		local pts = {}
		for i = 1, 3 do
			table.insert(pts, { 0, y + r[2] * 0.75, c[3] - r[3] * 0.6 + i * r[3] * 0.4, 1 - i * 0.1, 0, "Body" })
		end
		Parts.spikeRow(B, { points = pts, h = w * 0.5, pri = 2.6, col = "darker" })
	end
	-- legs: sprawled, elbows out
	local legW = w * (if has("tiny") then 0.16 else 0.24)
	Parts.legPair(B, { tag = "F", parent = "Body", x = r[1] * 0.75, y = y - 0.05, z = c[3] - r[3] * 0.6, w = legW, kind = "claw", phase = 0, splay = w * 0.55, bend = -0.6 })
	if not has("siren", "front legs only") then
		Parts.legPair(B, { tag = "H", parent = "Body", x = r[1] * 0.75, y = y - 0.05, z = c[3] + r[3] * 0.65, w = legW * 1.05, kind = "claw", phase = 0.5, splay = w * 0.55, bend = -0.6 })
	end
	-- blotches / spots on the back
	if detail >= 2 and has("spot", "blotch", "polka", "yellow", "orange blotch") then
		local spots = { { 0.35, -0.5 }, { -0.4, -0.05 }, { 0.3, 0.45 }, { -0.25, 0.75 } }
		for i, p in spots do
			if i <= detail then
				B:ell(w * 0.36, w * 0.14, w * 0.42, at(r[1] * p[1], y + r[2] * 0.9, c[3] + r[3] * p[2]), { col = "secondary", mat = "skin", pri = 3.4 + i * 0.1, role = "detail", name = "Blotch", mesh = false })
			end
		end
	end
	B:socket("core", at(0, y, c[3]), "Body")
	B:socket("mouth", at(0, hc[2] - hr[2] * 0.3, hc[3] - hr[3]), hb)
	B:setRig("gait", "sprawl")
end

-- Several heads on long necks from one coiled body (hydra, scylla).
local function hydra(B: any, ctx: any, has: any)
	local t, detail = ctx.traits, ctx.detail
	local heads = if has("nine") then 5 elseif has("six") then 4 else 3
	if detail <= 1 then
		heads = 3
	end
	local w = 1.0
	local y = 1.0
	B.boneIndex.Body.pos = { 0, y, 0 }
	B:ell(2.4, 1.8, 2.6, at(0, y, 0.3), { col = "primary", mat = "scale", pri = 1, role = "body", name = "Body", mesh = "s_aq_seal_hips" })
	Parts.tail(B, { start = { 0, y - 0.2, 1.4 }, dir = { 0.4, -0.25, 1 }, len = 2.6, w = 0.75, segs = if detail >= 2 then 3 else 2, taper = 0.62, pri = 1.2 })
	for h = 1, heads do
		local a = (h - (heads + 1) / 2) / heads * rad(110)
		local base = { sin(a) * 0.7, y + 0.6, -0.2 }
		local top = { sin(a) * 2.0, y + 2.6 + cos(a * 2) * 0.4, -1.3 - cos(a) * 0.3 }
		local nb = B:bone("Neck" .. h, "Body", base[1], base[2], base[3])
		B:addRig("spine", nb)
		B:limb(base, top, w * 0.55, { col = "primary", mat = "scale", bone = nb, pri = 1.15 + h * 0.05, role = "body", name = "Neck" }, 0.25)
		local hb = B:bone("Head" .. h, nb, top[1], top[2], top[3])
		local s = 0.75
		local c = { top[1], top[2] + 0.1, top[3] - 0.3 }
		local r = { s * 0.42, s * 0.34, s * 0.6 }
		B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3], 0, -a * 0.5, 0), { col = "primary", mat = "scale", bone = hb, pri = 1.2 + h * 0.05, role = "head", name = "Head", mesh = "s_head_reptile" })
		Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = hb, mood = mood(B), detail = math.min(detail, if h == 1 then 3 else 1), kind = if t.cute then "cute" else "fierce",
			spacing = r[1] * 0.6, y = r[2] * 0.3, d = s * 0.28, mouthY = -r[2] * 0.4, mouthW = s * 0.3, noMouth = mood(B) == "Neutral", lidCol = "primary", pri = 1.4 + h * 0.05 })
		if h == 1 then
			B:setRig("head", hb)
		end
	end
	Parts.legPair(B, { tag = "F", parent = "Body", x = 0.9, y = y - 0.3, z = -0.4, w = 0.32, kind = "claw", claws = true, phase = 0 })
	B:socket("core", at(0, y, 0.3), "Body")
	B:setRig("gait", "sprawl")
end

return function(B: any, ctx: any)
	local has = reader(ctx)
	local kind = kindOf(ctx, has)
	if kind == "worm" then
		return Worms.build(B, ctx)
	elseif kind == "tentacle" then
		return Cephalopod.build(B, ctx)
	elseif kind == "naga" then
		return SeaMammal.mer(B, ctx)
	elseif kind == "salamander" then
		return salamander(B, ctx, has)
	elseif kind == "hydra" then
		return hydra(B, ctx, has)
	end
	return serpent(B, ctx, kind, has)
end
