--!strict
-- Cephalopods for the Octopus route (Plans/Fish, kind "cephalopod") and tentacled words of other plans:
--   octopus   round mantle over a head, eight curling arms on bone chains (dumbo ear fins, vampire / dumbo web,
--             blue rings, coconut shell, bubble helmet, brain in a jar, crown, fishbowl);
--   squid     a long torpedo mantle with arrowhead fins, big eyes, eight arms and two long clubbed tentacles;
--   cuttle    a horizontal shield mantle ringed by a wavy fin skirt, eight short arms forward;
--   nautilus  a coiled shell (nautilus, ammonite, argonaut) or a straight cone (cameroceras) with a hood and a
--             fringe of thin tentacles out of the aperture.
-- Arms reuse the octopus hero pieces (s_octo_arm1/2/3: local +Z is the sucker side, every arm is rolled so).

local Geom = require(script.Parent.Parent.Geom)
local Face = require(script.Parent.Parent.Face)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local Cephalopod = {}

local function mood(B: any): string
	return B.ctx.result.mood or "Neutral"
end

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

-- n arms radiating from (0, y, zc) with reach and spread. o: segs, w, reach, droop (how far the first segment
-- falls), curl (tip lift), col, startA (first angle), arc (total arc, default full circle), fwd (z bias of the
-- spread: arms reach forward), alt (alternate colour per segment: banded arms), tips (sculpt pieces on)
local function arms(B: any, n: number, y: number, zc: number, o: any)
	local segs = o.segs or 2
	local arc = o.arc or math.pi * 2
	for i = 1, n do
		local a = (o.startA or 0) + (if arc >= math.pi * 2 then (i - 0.5) / n * arc else (if n > 1 then (i - 1) / (n - 1) else 0.5) * arc)
		local dx, dz = sin(a), cos(a)
		dz = dz * (o.flat or 1) - (o.fwd or 0)
		local r0 = o.r0 or 0.6
		local x, yy, z = sin(a) * r0, y, zc + cos(a) * r0 * (o.flat or 1)
		local parent = o.parent or "Body"
		local w = o.w or 0.42
		local reach = o.reach or 1.0
		for sgi = 1, segs do
			local bname = B:bone((o.prefix or "Arm") .. i .. "_" .. sgi, parent, x, yy, z)
			local rr = reach * (1 - (sgi - 1) * 0.12)
			local ex, ez = x + dx * rr * 0.75, z + dz * rr * 0.75
			local ey = yy - rr * (if sgi == 1 then (o.droop or 0.85) else (o.droop2 or 0.35)) + (if sgi == segs then (o.curl or 0.35) else 0)
			local last = sgi == segs
			local col = o.col or (if last and (o.detail or 2) >= 2 then "secondary" else "primary")
			if o.alt and sgi % 2 == 0 then
				col = "secondary"
			end
			local arm = B:limb({ x, yy, z }, { ex, ey, ez }, w, { col = col, mat = o.mat or "skin", bone = bname, pri = (o.pri or 1.2) + sgi * 0.35 + i * 0.01, role = "tentacle", trail = last,
				mesh = if o.plain then false else nil }, 0.3)
			arm.cf = Geom.rollY(arm.cf, 0, -1, 0)
			if not o.plain then
				if sgi == 1 then
					B:sculpt(arm, "s_octo_arm1")
				elseif segs == 2 then
					B:sculpt(arm, "s_octo_arm3")
				elseif sgi == 2 then
					arm.mesh = "s_octo_arm2"
					arm.armLead = true
				end
			end
			B:addRig("tentacles", { bone = bname, index = i, seg = sgi })
			x, yy, z = ex, ey, ez
			parent = bname
			w *= o.taper or 0.72
		end
	end
	-- three-segment arms: the middle piece contains the tip
	if (o.segs or 2) >= 3 and not o.plain then
		for _, p in B.parts do
			if p.armLead then
				local arm, _ = string.match(p.bone, "^(.-)_2$")
				local tips = {}
				for _, q in B.parts do
					if q.bone == arm .. "_3" and q.role == "tentacle" then
						q.pri = math.max(q.pri or 2, 3.2)
						table.insert(tips, q)
					end
				end
				B:sculpt(p, "s_octo_arm2", tips)
				p.armLead = nil
			end
		end
	end
end

local function octopus(B: any, ctx: any, has: any)
	local t, detail = ctx.traits, ctx.detail
	local dumbo = has("dumbo", "ear fin", "bobtail")
	local robot = t.robot or t.mechanical or has("robot", "steel")
	local alien = has("alien", "brain")
	local y = 2.3
	B.boneIndex.Body.pos = { 0, y, 0 }
	-- mantle (bag) behind and above the head, tilted back
	local mc = { 0, y + 0.85, 0.45 }
	local mr = { 1.05, 1.3, 1.05 }
	if dumbo then
		mc, mr = { 0, y + 0.55, 0.15 }, { 1.2, 1.15, 1.15 }
	end
	if alien then
		-- the "mantle" is a wrinkled brain, the head under it a small face
		mc, mr = { 0, y + 0.95, 0.15 }, { 1.25, 0.95, 1.2 }
	end
	B:ell(mr[1] * 2, mr[2] * 2, mr[3] * 2, at(mc[1], mc[2], mc[3], rad(if dumbo or alien then 0 else -22), 0, 0), {
		col = if alien then "secondary" else "primary", mat = if robot then "metal" else "skin", pri = 1, role = "body", name = "Mantle", mesh = if alien then "s_aq_brain" else "s_octo_mantle" })
	-- head with the eyes, in front of the mantle
	local fc = { 0, y + 0.05, -0.25 }
	local fr = { 0.95, 0.85, 0.85 }
	B:ell(fr[1] * 2, fr[2] * 2, fr[3] * 2, at(fc[1], fc[2], fc[3]), { col = "primary", mat = if robot then "metal" else "skin", pri = 1.1, role = "head", name = "Head", mesh = false })
	local fierce = has("monster", "king", "kraken", "giant") or (t.mythical and not t.cute) or (t.power or 5) >= 8
	Face.build(B, { face = { kind = "ellipsoid", c = fc, r = fr }, bone = "Body", mood = mood(B), detail = detail,
		kind = if robot then "robot" elseif fierce then "fierce" else "cute", spacing = 0.44, y = 0.18, d = if fierce then 0.42 else 0.52, mouthY = -0.4, mouthW = 0.45, lidCol = "primary" })
	-- arms
	local n = if detail <= 0 then 4 elseif detail == 1 then 6 else 8
	local segs = if detail >= 3 then 3 else 2
	arms(B, n, y - 0.45, 0.05, { segs = segs, w = 0.44, reach = if has("long tentacle", "giant", "huge") then 1.25 else 1.0, detail = detail, alt = has("striped", "stripe", "mimic", "wonderpus", "ring"),
		mat = if robot then "metal" else "skin", plain = robot })
	if robot and detail >= 2 then
		-- grabber claws on the front arms: two hard wedges at each tip
		for _, p in B.parts do
			if p.role == "tentacle" and p.trail and (string.match(p.bone, "^Arm1_") or string.match(p.bone, "^Arm" .. n .. "_")) then
				local x, yy, z = p.cf[1], p.cf[2], p.cf[3]
				B:wedge(0.12, 0.35, 0.3, at(x + 0.12, yy - 0.3, z, 0, 0, rad(15)), { col = "gunmetal", mat = "metal", bone = p.bone, pri = 2.8, role = "claw", name = "Grabber" })
			end
		end
	end
	if dumbo and detail >= 1 then
		-- ear fins: two paddles on top of the mantle
		B:mell(1.5, 0.14, 1.0, at(mr[1] * 0.95 + 0.35, mc[2] + mr[2] * 0.45, mc[3], 0, rad(-15), rad(30)), { col = "primary", mat = "skin", pri = 1.5, role = "fin", name = "EarFin#" })
	end
	if (dumbo or has("web", "cloak")) and detail >= 2 then
		-- arm web: a skirt between the arm roots
		B:ell(3.0, 0.5, 3.0, at(0, y - 0.9, 0.05), { col = "secondary", mat = "skin", tr = 0.15, pri = 2.2, role = "detail", name = "Web", mesh = false })
	end
	if has("blue ring", "glowing blue ring", "ringed") and detail >= 2 then
		for i, p in { { 0.6, 0.5, -0.7 }, { -0.65, 0.35, -0.6 }, { 0.2, 1.0, -0.75 }, { -0.4, 1.3, -0.5 } } do
			if i <= detail + 1 then
				B:ell(0.36, 0.36, 0.14, at(mc[1] + p[1], mc[2] + p[2] - 0.3, mc[3] + p[3], rad(-25), rad(p[1] * -40), 0), { col = "glow", mat = "neon", glow = true, pri = 3.2 + i * 0.1, role = "gem", name = "Ring", noCore = true })
			end
		end
	end
	if has("coconut", "shell") and detail >= 1 then
		B:ell(2.4, 2.3, 2.2, at(0, y + 0.6, 1.0, rad(-20), 0, 0), { col = "wood", mat = "wood", pri = 1.6, role = "shell", name = "Coconut", mesh = false })
	end
	if has("bubble helmet", "helmet", "fishbowl", "jar", "bowl") and detail >= 1 then
		local jar = has("jar")
		B:ell(4.2, if jar then 4.8 else 4.2, 4.2, at(0, y + 0.25, 0.1), { col = "glass", mat = "glass", tr = 0.7, pri = 2.0, role = "shell", name = if jar then "Jar" else "Bubble", noCore = true, mesh = false })
		if jar and detail >= 2 then
			B:cyl(0.5, 3.2, at(0, y - 2.1, 0.1, 0, 0, rad(90)), { col = "metal", mat = "metal", pri = 2.4, role = "detail", name = "JarBase" })
		end
	end
	if (t.crown or has("crown")) and detail >= 1 then
		B:cyl(0.45, 1.25, at(0, mc[2] + mr[2] * 0.95, mc[3] + 0.1, 0, 0, rad(90)), { col = "gold", mat = "metal", pri = 1.9, role = "hat", name = "Crown" })
	end
	B:socket("core", at(0, y + 0.3, 0.2), "Body")
	B:socket("mouth", at(0, y - 0.3, -1.0), "Body")
	B:setRig("gait", "swim")
end

local function squid(B: any, ctx: any, has: any)
	local t, detail = ctx.traits, ctx.detail
	local bigFin = has("bigfin", "huge fins", "ear fins", "bobtail")
	local round = has("bobtail", "balloon", "round")
	local glass = has("glass", "transparent")
	local y = 2.2
	B.boneIndex.Body.pos = { 0, y, 0 }
	local tilt = rad(28)
	local ml = if round then 1.5 else 3.4
	local mw = if round then 1.4 else 1.05
	local mc = { 0, y + 0.5 + ml * 0.42 * cos(tilt), 0.2 + ml * 0.42 * sin(tilt) }
	local mantle = B:ell(mw, ml, mw, at(mc[1], mc[2], mc[3], tilt, 0, 0), { col = "primary", mat = if glass then "glass" else "skin", tr = if glass then 0.35 else nil, pri = 1, role = "body", name = "Mantle",
		mesh = if round then "s_octo_mantle" else "s_aq_squid_mantle" })
	-- arrowhead fins near the tip (the sculpt has them; the primitive build adds two fin ellipsoids)
	if detail >= 1 and not round then
		local fy, fz = mc[2] + ml * 0.33 * cos(tilt), mc[3] + ml * 0.33 * sin(tilt)
		local fa, fb = B:mell(if bigFin then 1.6 else 0.9, 0.1, if bigFin then 1.4 else 0.95, at(mw * 0.45 + (if bigFin then 0.55 else 0.3), fy, fz, tilt - rad(90), 0, rad(-10)), { col = "primary", mat = "skin", pri = 1.5, role = "fin", name = "MantleFin#", mesh = false })
		if not bigFin then
			B:sculpt(mantle, "s_aq_squid_mantle", { fa, fb })
		end
	elseif detail >= 1 then
		B:mell(0.8, 0.1, 0.6, at(mw * 0.6, mc[2] + 0.1, mc[3], 0, rad(-10), rad(20)), { col = "secondary", mat = "skin", pri = 1.5, role = "fin", name = "EarFin#" })
	end
	-- head: eyes big
	local fc = { 0, y + 0.1, -0.05 }
	local fr = { 0.72, 0.62, 0.7 }
	B:ell(fr[1] * 2, fr[2] * 2, fr[3] * 2, at(fc[1], fc[2], fc[3]), { col = "primary", mat = if glass then "glass" else "skin", tr = if glass then 0.25 else nil, pri = 1.1, role = "head", name = "Head", mesh = false })
	local fierce = has("colossal", "humboldt", "vampire", "hook") or (not t.cute and (t.power or 5) >= 8)
	Face.build(B, { face = { kind = "ellipsoid", c = fc, r = fr }, bone = "Body", mood = mood(B), detail = detail,
		kind = if has("vampire", "glowing eye") then "glow" elseif fierce then "fierce" else "cute", spacing = 0.4, y = 0.12, d = 0.52, mouthW = nil, noMouth = true, lidCol = "primary" })
	-- eight arms forward and down, two long tentacles with clubs
	local n = if detail <= 0 then 4 elseif detail == 1 then 6 else 8
	arms(B, n, y - 0.35, -0.1, { segs = if detail >= 3 then 3 else 2, w = if bigFin then 0.26 else 0.34, reach = if bigFin then 1.5 else 0.95, droop = 0.9, droop2 = 0.55, curl = 0.15,
		r0 = 0.42, flat = 0.6, fwd = 0.35, detail = detail })
	if detail >= 2 and not has("vampire") then
		for _, side in { 1, -1 } do
			local bn = B:bone(if side > 0 then "ClubR" else "ClubL", "Body", side * 0.25, y - 0.4, -0.4)
			B:addRig("tentacles", { bone = bn, index = 9 + side, seg = 1 })
			local a, b = { side * 0.25, y - 0.4, -0.4 }, { side * 0.7, 0.35, -1.9 }
			B:limb(a, b, 0.14, { col = "primary", mat = "skin", bone = bn, pri = 2.4, role = "tentacle", name = "Feeder", mesh = false }, 0.1)
			B:ell(0.32, 0.6, 0.26, at(b[1] + side * 0.05, 0.4, b[3] - 0.3, rad(-70), 0, 0), { col = "secondary", mat = "skin", bone = bn, pri = 2.6, role = "tentacle", name = "Club", trail = true, mesh = false })
		end
	end
	if has("vampire", "cloak") and detail >= 1 then
		B:ell(2.6, 1.1, 2.4, at(0, y - 0.75, -0.2), { col = "secondary", mat = "skin", pri = 1.6, role = "detail", name = "Cloak", mesh = false })
	end
	if has("glowing", "firefly", "flashing") and detail >= 2 then
		for i = 1, (if detail >= 3 then 3 else 2) do
			local u = i / 4
			B:mball(0.18, at(mw * 0.45, mc[2] - ml * (0.3 - u * 0.6) * cos(tilt), mc[3] - ml * (0.3 - u * 0.6) * sin(tilt) - 0.1), { col = "glow", mat = "neon", glow = true, pri = 3.2 + i * 0.1, role = "gem", name = "Photophore#", noCore = true })
		end
	end
	B:socket("core", at(0, y + 0.5, 0.2), "Body")
	B:socket("mouth", at(0, y - 0.3, -0.8), "Body")
	B:setRig("gait", "swim")
end

local function cuttle(B: any, ctx: any, has: any)
	local t, detail = ctx.traits, ctx.detail
	local y = 1.5
	B.boneIndex.Body.pos = { 0, y, 0 }
	local L, W, H = 3.0, 1.75, 1.05
	local c = { 0, y, 0.35 }
	local body = B:ell(W, H, L, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Shield", mesh = "s_aq_cuttle_body" })
	if detail >= 1 then
		-- wavy fin skirt round the mantle: in the sculpt; primitive: a flat oval a little wider than the body
		local skirt = B:ell(W * 1.45, 0.14, L * 1.04, at(0, y - H * 0.08, c[3]), { col = "secondary", mat = "skin", pri = 1.4, role = "fin", name = "Skirt", mesh = false })
		B:sculpt(body, "s_aq_cuttle_body", { skirt })
	end
	-- head in front, arms forward
	local fc = { 0, y - 0.05, c[3] - L * 0.55 }
	local fr = { 0.72, 0.58, 0.55 }
	B:ell(fr[1] * 2, fr[2] * 2, fr[3] * 2, at(fc[1], fc[2], fc[3]), { col = "primary", mat = "skin", pri = 1.1, role = "head", name = "Head", mesh = false })
	Face.build(B, { face = { kind = "ellipsoid", c = fc, r = fr }, bone = "Body", mood = mood(B), detail = detail, kind = if t.cute then "cute" else "fierce",
		spacing = 0.5, y = 0.18, d = 0.46, noMouth = true, lidCol = "primary" })
	local n = if detail <= 0 then 4 elseif detail == 1 then 6 else 8
	arms(B, n, y - 0.15, fc[3] - 0.3, { segs = if detail >= 2 then 2 else 1, w = 0.26, reach = 0.75, droop = 0.25, droop2 = 0.2, curl = 0.05, r0 = 0.3, startA = math.pi - rad(55), arc = rad(110), flat = 1.6, detail = detail })
	if detail >= 3 then
		for i, p in { { 0.35, 0.05 }, { -0.3, 0.35 }, { 0.15, 0.65 } } do
			B:ell(0.38, 0.1, 0.5, at(W * 0.5 * p[1], y + H * 0.47, c[3] - L * 0.3 + L * p[2] * 0.7), { col = "darker", mat = "skin", pri = 3.6 + i * 0.1, role = "detail", name = "Mottle", mesh = false })
		end
	end
	B:socket("core", at(0, y, c[3]), "Body")
	B:socket("mouth", at(0, y - 0.1, fc[3] - 0.9), "Body")
	B:setRig("gait", "swim")
end

local function shelled(B: any, ctx: any, has: any)
	local t, detail = ctx.traits, ctx.detail
	local straight = has("straight", "cameroceras", "orthocone")
	local argonaut = has("argonaut", "papery")
	local y = 2.1
	B.boneIndex.Body.pos = { 0, y, 0 }
	local sc
	if straight then
		-- long straight cone pointing back, aperture at the front
		B:limb({ 0, y + 0.2, -0.4 }, { 0, y + 1.0, 4.2 }, 1.9, { col = "secondary", mat = "hard", pri = 1, role = "shell", name = "Cone", mesh = "s_aq_orthocone" }, 0.05)
		sc = { 0, y + 0.3, -0.3 }
	else
		-- planispiral shell in the yz plane: the coil behind and above the head
		local w = if argonaut then 1.0 else 1.2
		sc = { 0, y + 0.9, 0.55 }
		B:ell(w, 3.0, 3.0, at(sc[1], sc[2], sc[3]), { col = if argonaut then "secondary" else "primary", mat = "hard", pri = 1, role = "shell", name = "Shell", mesh = if argonaut then "s_aq_argonaut_shell" else "s_aq_nautilus_shell" })
		if detail >= 2 and not argonaut and has("stripe", "nautilus") then
			for i = 1, 2 do
				local a = rad(30 + i * 40)
				B:ell(w * 1.04, 0.22, 1.2, at(0, sc[2] + 1.5 * cos(a) * 0.95, sc[3] + 1.5 * sin(a) * 0.95, -a, 0, 0), { col = "darker", mat = "hard", pri = 3.4 + i * 0.1, role = "detail", name = "Stripe", mesh = false })
			end
		end
	end
	-- hood and head out of the aperture
	local hc = { 0, y - 0.1, -0.55 }
	local hr = { 0.75, 0.62, 0.6 }
	B:ell(hr[1] * 2, hr[2] * 2, hr[3] * 2, at(hc[1], hc[2], hc[3]), { col = if argonaut then "primary" else "accent", mat = "skin", pri = 1.1, role = "head", name = "Head", mesh = false })
	if detail >= 1 and not argonaut then
		B:ell(1.6, 0.55, 1.1, at(0, hc[2] + hr[2] * 0.75, hc[3] + 0.15, rad(-12), 0, 0), { col = "darker", mat = "hard", pri = 1.5, role = "detail", name = "Hood", mesh = false })
	end
	Face.build(B, { face = { kind = "ellipsoid", c = hc, r = hr }, bone = "Body", mood = mood(B), detail = detail, kind = if t.cute then "cute" elseif (t.power or 5) >= 7 then "fierce" else "cute",
		spacing = 0.45, y = 0.08, d = 0.4, noMouth = true, lidCol = "primary" })
	-- fringe of thin tentacles reaching forward and down
	local n = if detail <= 0 then 4 elseif detail == 1 then 6 elseif argonaut then 8 else 10
	arms(B, n, hc[2] - 0.3, hc[3] - 0.2, { segs = if argonaut then 2 else 1, w = if argonaut then 0.32 else 0.2, reach = if argonaut then 0.95 else 1.25, droop = 0.6, curl = 0.2, r0 = 0.32,
		startA = math.pi - rad(70), arc = rad(140), flat = 1.3, detail = detail, plain = not argonaut, col = if argonaut then nil else "accent" })
	B:socket("core", at(0, sc[2], sc[3]), "Body")
	B:socket("mouth", at(0, hc[2] - 0.2, hc[3] - 0.8), "Body")
	B:setRig("gait", "swim")
end

function Cephalopod.build(B: any, ctx: any)
	local has = reader(ctx)
	if has("nautilus", "ammonite", "argonaut", "cameroceras", "coiled", "spiral shell", "straight-shell") then
		return shelled(B, ctx, has)
	elseif has("cuttle", "shield body") then
		return cuttle(B, ctx, has)
	elseif has("squid") and not has("kraken") then
		return squid(B, ctx, has)
	end
	return octopus(B, ctx, has)
end

return Cephalopod
