--!strict
-- Crustaceans and other shelled crawlers (the Crab plan, and the crabs and snails the Library files under Insect).
-- Sub-kinds from the silhouette hints:
--   crab      wide carapace with a toothed front edge, stalked eyes, two chelipeds (claw size by species: the
--             fiddler and pistol shrimp carry one giant claw and one tiny one), four walking legs a side spread
--             sideways; king / spider / yeti crabs on long spidery (or hairy) legs, ghost crabs on tall eye stalks,
--             decorator crab dressed in weed, pom pom crab holding anemones, hermit crab backed into a spiral shell,
--             crab machines (robot crab, crab tank with a turret), crystal / magma / bronze shells
--   lobster   long cephalothorax with a rostrum, segmented tail ending in a fan, big claws (spiny lobster: none,
--             long spiny antennae; slipper lobster: shovel plates), crayfish
--   shrimp    curled segmented body, long whip antennae, stalked eyes, swimmerets; mantis shrimp with folded clubs
--   isopod    a domed, banded oval on short legs (isopod, pill bug), trilobite (three lobes), horseshoe crab (dome +
--             tail spike)
--   cambrian  anomalocaris (lobed body, grasping frontal arms), opabinia (five eyes and a nozzle)
--   snail     a muscular foot under a spiral shell, eye tentacles
-- Motion: crabs sidestep (gait "sidestep"); lobsters, shrimp and isopods skitter; snails glide.
-- Sculpts (catalogue/s_bugs.py): s_crab_carapace, s_crab_claw (+_l), s_crab_leg, s_spiral_shell, s_lobster_body,
-- s_lobster_fan, s_isopod_body, s_trilobite_body, s_horseshoe_shell.

local Geom = require(script.Parent.Parent.Geom)
local Face = require(script.Parent.Parent.Face)
local Kit = require(script.Parent.Arthro)

local at = Geom.at
local rad = math.rad
local has = Kit.has

local function kindOf(ctx: any): string
	local id, hint = Kit.text(ctx)
	if ctx.kind == "Snail" or has(id, "snail slug") then
		return "Snail"
	end
	if has(id, "hermit") then
		return "Hermit"
	end
	if has(id, "lobster crayfish crawfish") then
		return "Lobster"
	end
	if has(id, "shrimp prawn krill amphipod monkey") then
		return "Shrimp"
	end
	if has(id, "isopod pill trilobite horseshoe woodlouse") then
		return "Isopod"
	end
	if has(id, "anomalocaris opabinia") then
		return "Cambrian"
	end
	if has(id, "sea spider") or (has(id, "spider") and not has(id, "crab")) then
		return "SeaSpider"
	end
	local _ = hint
	return "Crab"
end

-- stalked eyes: a stalk per side with an eye ball on top (the face of crabs, shrimp and lobsters)
local function stalkEyes(B: any, ctx: any, o: any)
	local detail = ctx.detail
	local base, h, d = o.base, o.h, o.d
	local bone = o.bone or "Body"
	local top = { base[1] + (o.lean or 0.08), base[2] + h, base[3] - h * 0.18 }
	if h > 0.05 then
		B:mlimb(base, top, d * 0.42, { col = o.col or "primary", mat = "hard", bone = bone, pri = 1.15, role = "stalk", name = "Stalk#", mesh = "s_tail_seg" }, 0.15)
	end
	local mood = Kit.mood(ctx)
	local cute = ctx.traits.cute or (mood ~= "Neutral" and mood ~= "Angry")
	-- the eye itself: a glossy bead on the stalk tip; cute and moody words get pupils and lids via Face on a flat frame
	if cute and detail >= 1 then
		Face.build(B, { face = { kind = "flat", cf = at(0, top[2] + d * 0.1, top[3] - d * 0.45) }, bone = bone, mood = mood, detail = math.min(detail, 2), kind = "cute", spacing = top[1], y = 0, d = d * 1.05, noMouth = true, noBrows = detail < 3, pri = 1.12 })
		B:mball(d * 1.0, at(top[1], top[2] + d * 0.1, top[3]), { col = o.col or "primary", mat = "hard", bone = bone, pri = 1.14, role = "head", name = "EyeCup#" })
	else
		B:mball(d, at(top[1], top[2] + d * 0.15, top[3]), { col = if o.glow then "eyeGlow" else "pupil", mat = if o.glow then "neon" else "glass", glow = o.glow, bone = bone, pri = 1.12, role = "eye", name = "Eye#", noCore = true })
		if detail >= 2 and not o.glow then
			B:mball(d * 0.32, at(top[1] + d * 0.18, top[2] + d * 0.38, top[3] - d * 0.32), { col = "shine", mat = "neon", bone = bone, pri = 3.2, role = "shine", name = "Shine#", noCore = true })
		end
	end
	return top
end

-- one cheliped (right side unless side = -1). o: shoulder, elbow, tip (the chela runs elbow -> tip), size (chela
-- width), col, piece, side, pri, detail, hairy
local function cheliped(B: any, ctx: any, o: any)
	local detail = ctx.detail
	local side = o.side or 1
	local function sx(p: { number }): { number }
		return { p[1] * side, p[2], p[3] }
	end
	local tag = if side > 0 then "R" else "L"
	local bone = B:bone("Claw" .. tag, "Body", o.shoulder[1] * side, o.shoulder[2], o.shoulder[3])
	B:addRig("arms", { arm = bone, side = side })
	local sh, el, tip = sx(o.shoulder), sx(o.elbow), sx(o.tip)
	local s = o.size
	if detail >= 1 or s < 0.6 then
		B:limb(sh, el, math.max(s * 0.42, 0.14), { col = o.armCol or o.col or "primary", mat = o.mat or "hard", bone = bone, pri = (o.pri or 1.2) + 0.15, role = "limb", name = "Merus" .. tag, mesh = "s_arthro_seg" }, 0.15)
	end
	local f, len = Kit.segFrame(el, tip)
	local piece = o.piece or "s_crab_claw"
	B:part({ shape = "Ellipsoid", size = { s, len * 1.08, s * 0.72 }, cf = f, seg = "Y", col = o.col or "primary", mat = o.mat or "hard", bone = bone, pri = o.pri or 1.2, role = "claw", name = "Chela" .. tag,
		mesh = if side > 0 then piece else piece .. "_l", mirrored = side < 0 or nil, trail = true })
end

-- walking legs, spread sideways. o: n per side, hipX, y, z0, z1, R, angles, thick, piece, col, mat, rise, lift
local function crabLegs(B: any, ctx: any, o: any)
	local detail = ctx.detail
	local n = o.n or 4
	if detail <= 0 and not o.noComb then
		local zm = (o.z0 + o.z1) / 2
		Kit.comb(B, { tag = "C", hip = { o.hipX, o.y, zm }, foot = { o.hipX + o.R * 0.95, 0.04, zm }, thick = (o.thick or 1) * 1.1, col = o.col, mat = o.mat, piece = o.comb or "s_crab_legs4", pri = 1.25 })
		return
	end
	local angles = o.angles or { 28, 8, -12, -32, -45 }
	local legs = {}
	for i = 1, n do
		local z = if n == 1 then o.z0 else o.z0 + (i - 1) / (n - 1) * (o.z1 - o.z0)
		local a = rad(angles[i] or 0)
		local R = o.R * (if o.rear and i == n then o.rear else 1)
		table.insert(legs, { { o.hipX, o.y, z }, { o.hipX + R * math.cos(a), o.lift or 0.04, z - R * math.sin(a) } })
	end
	Kit.legSet(B, { tagBase = "L", thick = o.thick or 1.15, segs = if detail >= 3 then 2 else 1, rise = o.rise or 0.4, piece = o.piece or "s_crab_leg", col = o.col or "primary", mat = o.mat, pri = 1.3, tripod = true }, legs)
end

local K: { [string]: (any, any) -> () } = {}

K.Crab = function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id, hint = Kit.text(ctx)
	local mech = t.robot or t.mechanical
	local tank = has(id, "tank")
	local longLegs = has(id, "king spider") or string.find(hint, "spidery", 1, true) ~= nil or string.find(hint, "long", 1, true) ~= nil and string.find(hint, "legs", 1, true) ~= nil
	local hairy = has(id, "yeti") or string.find(hint, "hairy", 1, true) ~= nil
	local fiddler = has(id, "fiddler") or string.find(hint, "one gigantic claw", 1, true) ~= nil or string.find(hint, "one giant", 1, true) ~= nil
	local ghost = has(id, "ghost") or string.find(hint, "stalk eyes", 1, true) ~= nil
	local flat = has(id, "porcelain blue") or string.find(hint, "flat", 1, true) ~= nil
	local egg = has(id, "sand")
	local spiky = has(id, "king") or string.find(hint, "spiky", 1, true) ~= nil
	local monster = has(id, "monster giant karkinos coconut") or t.size == "Large" or t.size == "Huge" or t.size == "Colossal"
	local crystal = has(id, "crystal")
	local magma = has(id, "magma")
	local y = if longLegs then 1.5 elseif egg then 0.75 else 0.95
	B.boneIndex.Body.pos = { 0, y, 0 }
	local W, H, L = 2.5, 0.88, 1.85
	if flat then
		W, H, L = 2.5, 0.68, 1.9
	elseif egg then
		W, H, L = 1.6, 1.0, 2.2
	elseif longLegs then
		W, H, L = 2.0, 0.95, 1.95
	elseif monster then
		W, H, L = 2.7, 1.0, 1.95
	end
	local mat = if mech or has(id, "karkinos") then "metal" elseif crystal then "glass" elseif magma then "stone" elseif hairy then "fur" else "hard"
	local carapace = B:ell(W, H, L, at(0, y, 0), { col = "primary", mat = mat, pri = 1.0, role = "body", name = "Carapace",
		mesh = if spiky then "s_crab_carapace_spiky" elseif egg then "s_sand_crab" elseif mech then "s_mech_pod" else "s_crab_carapace" })
	local _ = carapace
	if detail >= 2 and not mech then
		-- pale underside: a flatter lens below the rim
		B:ell(W * 0.86, H * 0.5, L * 0.82, at(0, y - H * 0.24, 0.02), { col = "belly", mat = "hard", pri = 2.6, role = "detail", name = "Plastron" })
	end
	-- eyes on stalks at the front edge (ghost crabs: tall)
	B:bone("Head", "Body", 0, y + H * 0.3, -L * 0.42)
	B:setRig("head", "Head")
	stalkEyes(B, ctx, { base = { W * 0.14, y + H * 0.3, -L * 0.42 }, h = if ghost then 0.95 else 0.42, d = if ghost then 0.32 else 0.26, bone = "Head", glow = mech or magma })
	-- claws
	local big = if monster then 1.35 else 1.0
	local right, left = 1.0, 1.0
	if fiddler then
		right, left = 2.1, 0.5
	elseif has(id, "coconut") then
		right, left = 1.25, 1.05
	elseif longLegs then
		right, left = 0.75, 0.75
	end
	local clawCol = if fiddler then "secondary" elseif has(id, "blue") then "secondary" else "primary"
	for _, side in { 1, -1 } do
		local k = (if side > 0 then right else left) * big
		local sh = { W * 0.36, y - 0.08, -L * 0.36 }
		local el = { W * 0.36 + 0.55 * k, y + 0.12 * k, -L * 0.36 - 0.55 * k }
		local tip = { el[1] - 0.3 * k, el[2] + 0.16 * k, el[3] - 1.15 * k }
		cheliped(B, ctx, { side = side, shoulder = sh, elbow = el, tip = tip, size = 0.62 * k, col = clawCol, mat = mat, pri = if k < 0.7 then 1.4 else 1.12, piece = if spiky or hairy then "s_crab_claw_spiky" else "s_crab_claw" })
	end
	-- walking legs
	crabLegs(B, ctx, { n = if detail >= 1 then 4 else 4, hipX = W * 0.36, y = y - H * 0.12, z0 = -L * 0.18, z1 = L * 0.34, R = if longLegs then 3.3 else 1.85, thick = if longLegs then 0.85 elseif hairy then 1.35 else 1.15,
		piece = if hairy then "s_crab_leg_hairy" elseif longLegs then "s_arthro_leg_long" else "s_crab_leg", col = "primary", mat = mat, rise = if longLegs then 0.5 else 0.38 })
	-- dressing
	if has(id, "decorator") and detail >= 1 then
		for i, p in { { 0.3, 0.2, 0.25 }, { -0.35, 0.1, 0.32 }, { 0.05, -0.3, 0.3 } } do
			if i <= detail then
				B:ell(p[3] * 2.2, p[3] * 1.4, p[3] * 2.0, at(W * p[1] * 0.8, y + H * 0.42, L * p[2]), { col = "secondary", mat = "leaf", pri = 1.6 + i * 0.1, role = "detail", name = "Weed" .. i, mesh = "s_canopy" })
			end
		end
	elseif has(id, "pom") and detail >= 1 then
		B:mball(0.7, at(W * 0.36 + 0.3, y + 0.35, -L * 0.36 - 1.45), { col = "secondary", mat = "fur", pri = 1.5, role = "detail", name = "Pompom#", mesh = "s_puff" })
	elseif crystal and detail >= 1 then
		for i = 1, math.min(detail + 1, 3) do
			local a = rad(-50 + i * 30)
			B:limb({ math.sin(a) * W * 0.25, y + H * 0.3, math.cos(a) * L * 0.1 }, { math.sin(a) * W * 0.4, y + H * 0.3 + 0.9 - i * 0.12, math.cos(a) * L * 0.25 }, 0.4, { col = "gem", mat = "glass", pri = 1.5 + i * 0.1, role = "spike", name = "Geode" .. i, mesh = "s_horn_tip" }, 0.1)
		end
	elseif magma and detail >= 1 then
		B:ell(W * 0.55, H * 0.25, L * 0.5, at(0, y + H * 0.42, 0.05), { col = "glow", mat = "neon", glow = true, pri = 1.6, role = "detail", name = "Lava" })
	elseif tank and detail >= 1 then
		B:cyl(0.8, 1.3, at(0, y + H * 0.6, 0.1, 0, 0, rad(90)), { col = "secondary", mat = "metal", pri = 1.3, role = "body", name = "TurretRing" })
		B:cyl(2.0, 0.34, at(0, y + H * 0.75, -1.1, 0, rad(90), 0), { col = "gunmetal", mat = "metal", pri = 1.35, role = "cannon", name = "Barrel" })
	end
	B:socket("core", at(0, y, 0), "Body")
	B:setRig("gait", "sidestep")
	if mech then
		B:setRig("materialMotion", "clank")
	end
end

K.Hermit = function(B: any, ctx: any)
	local detail = ctx.detail
	local y = 0.9
	B.boneIndex.Body.pos = { 0, y, 0 }
	-- the borrowed shell: a spiral whorl leaning back over the body, aperture facing forward
	local shell = B:ell(2.4, 2.3, 2.6, at(0, y + 0.55, 0.75, rad(-20), 0, 0), { col = "secondary", mat = "hard", pri = 1.0, role = "body", name = "Shell", mesh = "s_spiral_shell" })
	local _ = shell
	-- the crab: a small front body peeking out of the aperture
	B:ell(1.35, 0.75, 0.9, at(0, y, -0.55), { col = "primary", mat = "hard", pri = 1.02, role = "body", name = "Front", mesh = "s_crab_carapace" })
	B:bone("Head", "Body", 0, y + 0.2, -0.85)
	B:setRig("head", "Head")
	stalkEyes(B, ctx, { base = { 0.18, y + 0.22, -0.92 }, h = 0.5, d = 0.26, bone = "Head" })
	-- claws: the right one bigger (hermit crabs block the aperture with it)
	cheliped(B, ctx, { side = 1, shoulder = { 0.45, y - 0.1, -0.85 }, elbow = { 0.95, y + 0.1, -1.3 }, tip = { 0.65, y + 0.15, -2.25 }, size = 0.7, pri = 1.12 })
	cheliped(B, ctx, { side = -1, shoulder = { 0.45, y - 0.1, -0.85 }, elbow = { 0.8, y + 0.05, -1.25 }, tip = { 0.55, y + 0.1, -1.95 }, size = 0.5, pri = 1.2 })
	crabLegs(B, ctx, { n = 2, hipX = 0.5, y = y - 0.2, z0 = -0.65, z1 = -0.25, R = 1.6, angles = { 30, 5 }, thick = 1.15, col = "primary", rise = 0.4 })
	if detail >= 2 then
		Kit.antennae(B, { bone = "Head", base = { 0.08, y + 0.15, -0.95 }, dir = { 0.25, 0.45, -0.85 }, len = 1.3, w = 0.04, kind = "thread", col = "secondary", pri = 2.4 })
	end
	B:socket("core", at(0, y, 0.4), "Body")
	B:setRig("gait", "sidestep")
end

K.Lobster = function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id, hint = Kit.text(ctx)
	local spiny = has(id, "spiny") or string.find(hint, "spiny antennae", 1, true) ~= nil
	local slipper = has(id, "slipper") or string.find(hint, "shovel", 1, true) ~= nil
	local small = has(id, "crayfish crawfish")
	local y = 0.75
	B.boneIndex.Body.pos = { 0, y, 0 }
	local C = if slipper then { 1.55, 0.6, 1.6 } else { 1.05, 0.88, 1.9 }
	B:ell(C[1], C[2], C[3], at(0, y + 0.05, 0, rad(-3), 0, 0), { col = "primary", mat = "hard", pri = 1.0, role = "body", name = "Cephalothorax", mesh = if spiny then "s_lobster_body_spiny" else "s_lobster_body" })
	B:bone("Head", "Body", 0, y + 0.1, -C[3] * 0.4)
	B:setRig("head", "Head")
	stalkEyes(B, ctx, { base = { 0.18, y + 0.25, -C[3] * 0.44 }, h = 0.22, d = 0.24, bone = "Head" })
	-- tail: segments tapering back, then the fan
	local n = if detail >= 3 then 4 elseif detail == 2 then 3 elseif detail == 1 then 2 else 1
	local p0 = { 0, y + 0.02, C[3] * 0.42 }
	local parent = "Body"
	local w = C[1] * 0.85
	local segL = 2.0 / n
	for i = 1, n do
		local p1 = { 0, p0[2] - 0.06, p0[3] + segL }
		local bn = B:bone("Tail" .. i, parent, p0[1], p0[2], p0[3])
		B:addRig("tail", bn)
		B:limb(p0, p1, w, { col = "primary", mat = "hard", bone = bn, pri = 1.05 + i * 0.05, role = "tail", name = "Tail" .. i, mesh = "s_lobster_seg", depth = w * 0.72 }, 0.2)
		p0, parent = p1, bn
		w *= 0.9
	end
	B:ell(w * 2.0, 0.16, 1.0, at(0, p0[2] - 0.05, p0[3] + 0.4), { col = "secondary", mat = "hard", bone = parent, pri = 1.15, role = "tail", name = "Fan", mesh = "s_lobster_fan", trail = true })
	-- claws (spiny lobsters have none: they lead with thick spiny antennae)
	if not spiny and not slipper then
		local k = if small then 0.85 else 1.15
		for _, side in { 1, -1 } do
			cheliped(B, ctx, { side = side, shoulder = { C[1] * 0.32, y - 0.08, -C[3] * 0.35 }, elbow = { C[1] * 0.32 + 0.55 * k, y + 0.05, -C[3] * 0.35 - 0.7 * k }, tip = { C[1] * 0.32 + 0.4 * k, y + 0.12, -C[3] * 0.35 - 0.7 * k - 1.3 * k },
				size = 0.62 * k, col = "primary", pri = 1.12 })
		end
	end
	if slipper and detail >= 1 then
		B:mell(0.7, 0.14, 0.55, at(0.35, y + 0.05, -C[3] * 0.55, 0, rad(-12), 0), { col = "secondary", mat = "hard", bone = "Head", pri = 1.3, role = "detail", name = "Shovel#", mesh = "s_lobster_fan" })
	end
	crabLegs(B, ctx, { n = if detail >= 2 then 4 else 3, hipX = C[1] * 0.32, y = y - 0.2, z0 = -C[3] * 0.18, z1 = C[3] * 0.3, R = 1.25, angles = { 20, 0, -18, -35 }, thick = 0.9, col = "primary", rise = 0.36, piece = "s_arthro_leg", comb = "s_crab_legs4" })
	-- antennae: long whips swept back over the body (spiny lobster: thick, spiny, forward)
	Kit.antennae(B, { bone = "Head", base = { 0.2, y + 0.15, -C[3] * 0.5 }, dir = if spiny then { 0.3, 0.25, -0.92 } else { 0.4, 0.3, -0.86 }, len = if spiny then 3.0 else 2.6, w = if spiny then 0.14 else 0.05,
		kind = "thread", col = if spiny then "secondary" else "primary", pri = if spiny then 1.2 else 1.6 })
	local _ = t
	B:socket("core", at(0, y, 0.3), "Body")
	B:setRig("gait", "skitter")
end

K.Shrimp = function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id, hint = Kit.text(ctx)
	local mantis = has(id, "mantis")
	local pistol = has(id, "pistol") or string.find(hint, "one giant", 1, true) ~= nil
	local harlequin = has(id, "harlequin")
	local amphipod = has(id, "amphipod")
	local monkey = has(id, "monkey")
	local y = if mantis then 0.7 else 1.1
	B.boneIndex.Body.pos = { 0, y, 0 }
	-- carapace, then a tail arching down and back (shrimp hunch)
	local C = if mantis then { 1.0, 0.65, 1.3 } else { 0.85, 0.9, 1.35 }
	B:ell(C[1], C[2], C[3], at(0, y + 0.08, 0, rad(-6), 0, 0), { col = "primary", mat = "hard", pri = 1.0, role = "body", name = "Carapace", mesh = if mantis then "s_mantis_shrimp_body" else "s_shrimp_body" })
	B:bone("Head", "Body", 0, y + 0.1, -C[3] * 0.4)
	B:setRig("head", "Head")
	stalkEyes(B, ctx, { base = { 0.16, y + 0.3, -C[3] * 0.45 }, h = if mantis then 0.42 else 0.15, d = if mantis then 0.36 else 0.28, bone = "Head", col = if mantis then "secondary" else "primary" })
	local n = if detail >= 3 then 5 elseif detail == 2 then 3 elseif detail == 1 then 2 else 1
	local p0 = { 0, y + 0.05, C[3] * 0.42 }
	local parent = "Body"
	local w = C[1] * 0.92
	local curl = if mantis then 0.1 else 0.55
	for i = 1, n do
		local a = rad(10 + i * curl * 70 / n)
		local seg = 2.3 / n
		local p1 = { 0, p0[2] - math.sin(a) * seg, p0[3] + math.cos(a) * seg }
		local bn = B:bone("Tail" .. i, parent, p0[1], p0[2], p0[3])
		B:addRig("tail", bn)
		B:limb(p0, p1, w, { col = if (mantis or harlequin) and i % 2 == 0 then "secondary" else "primary", mat = "hard", bone = bn, pri = 1.05 + i * 0.05, role = "tail", name = "Tail" .. i, mesh = "s_lobster_seg", depth = w * (if mantis then 0.62 else 0.9) }, 0.2)
		p0, parent = p1, bn
		w *= 0.85
	end
	B:ell(w * 2.2, 0.14, 0.85, at(0, p0[2] - 0.12, p0[3] + 0.25, rad(if mantis then 0 else 35), 0, 0), { col = "secondary", mat = "hard", bone = parent, pri = 1.15, role = "tail", name = "Fan", mesh = "s_lobster_fan", trail = true })
	-- legs: thin walking legs under the carapace
	crabLegs(B, ctx, { n = if detail >= 2 then 3 else 2, hipX = C[1] * 0.25, y = y - C[2] * 0.3, z0 = -C[3] * 0.15, z1 = C[3] * 0.25, R = if amphipod or monkey then 0.9 else 1.15, angles = { 15, -5, -25 }, thick = 0.7, col = "primary", rise = 0.3, piece = "s_arthro_leg", comb = "s_crab_legs4" })
	-- arms: pistol shrimp's one giant snapper; mantis shrimp's folded clubs; harlequin's flat paddle claws
	if pistol then
		cheliped(B, ctx, { side = 1, shoulder = { 0.3, y - 0.05, -C[3] * 0.35 }, elbow = { 0.75, y + 0.05, -C[3] * 0.35 - 0.5 }, tip = { 0.55, y + 0.15, -C[3] * 0.35 - 1.7 }, size = 0.8, col = "secondary", pri = 1.1 })
		cheliped(B, ctx, { side = -1, shoulder = { 0.3, y - 0.05, -C[3] * 0.35 }, elbow = { 0.5, y, -C[3] * 0.35 - 0.3 }, tip = { 0.4, y, -C[3] * 0.35 - 0.7 }, size = 0.24, pri = 1.6 })
	elseif mantis then
		B:mirrorBone("Club#", "Body", 0.3, y - 0.1, -C[3] * 0.38)
		B:addRig("arms", { arm = "ClubR", side = 1 })
		B:addRig("arms", { arm = "ClubL", side = -1 })
		Kit.seg(B, { 0.3, y - 0.1, -C[3] * 0.38 }, { 0.45, y - 0.15, -C[3] * 0.38 - 0.85 }, 0.34, { col = "secondary", mat = "hard", bone = "Club#", pri = 1.15, role = "claw", name = "Club#", mesh = "s_mantis_arm", meshL = "s_mantis_arm_l", trail = true, mirror = true }, { 0, 1, 0 })
	elseif harlequin and detail >= 1 then
		for _, side in { 1, -1 } do
			cheliped(B, ctx, { side = side, shoulder = { 0.28, y, -C[3] * 0.38 }, elbow = { 0.75, y + 0.2, -C[3] * 0.38 - 0.3 }, tip = { 1.0, y + 0.35, -C[3] * 0.38 - 1.1 }, size = 0.75, col = "secondary", pri = 1.2, piece = "s_crab_claw" })
		end
	end
	-- antennae: long whips arching back (cleaner shrimp: white)
	if not amphipod or detail >= 1 then
		Kit.antennae(B, { bone = "Head", base = { 0.12, y + 0.18, -C[3] * 0.5 }, dir = { 0.25, 0.55, -0.8 }, len = if mantis then 1.0 else 2.7, w = 0.04, kind = "thread", col = if has(id, "cleaner") then "white" else "secondary", pri = 1.5 })
	end
	if mantis and detail >= 2 then
		B:mell(0.4, 0.08, 0.3, at(0.32, y + 0.2, -C[3] * 0.62, 0, rad(-25), 0), { col = "secondary", mat = "hard", bone = "Head", pri = 2.2, role = "detail", name = "Scale#", mesh = "s_petal" })
	end
	local _ = t
	B:socket("core", at(0, y, 0.3), "Body")
	B:setRig("gait", if monkey or amphipod then "swim" else "skitter")
end

K.Isopod = function(B: any, ctx: any)
	local detail = ctx.detail
	local id = Kit.text(ctx)
	local trilobite = has(id, "trilobite")
	local horseshoe = has(id, "horseshoe")
	local pill = has(id, "pill")
	local y = if horseshoe then 0.6 else 0.62
	B.boneIndex.Body.pos = { 0, y, 0 }
	local W, H, L = 1.9, 1.0, 3.0
	if pill then
		W, H, L = 1.9, 1.25, 2.6
	elseif trilobite then
		W, H, L = 2.0, 0.7, 2.8
	elseif horseshoe then
		W, H, L = 2.8, 1.0, 2.6
	end
	B:ell(W, H, L, at(0, y + H * 0.12, 0), { col = "primary", mat = "hard", pri = 1.0, role = "body", name = "Shell",
		mesh = if trilobite then "s_trilobite_body" elseif horseshoe then "s_horseshoe_shell" else "s_isopod_body" })
	B:bone("Head", "Body", 0, y, -L * 0.42)
	B:setRig("head", "Head")
	local mood = Kit.mood(ctx)
	local cute = ctx.traits.cute or (mood ~= "Neutral" and mood ~= "Angry")
	local hc = { 0, y + H * 0.12, -L * 0.36 }
	Face.build(B, { face = { kind = "ellipsoid", c = hc, r = { W * 0.42, H * 0.5, L * 0.18 } }, bone = "Head", mood = mood, detail = detail, kind = if cute then "cute" else "bug",
		spacing = W * (if horseshoe then 0.24 else 0.18), y = H * (if horseshoe then 0.35 else 0.08), d = W * 0.13, noMouth = not cute, noBrows = true, pri = 1.12 })
	if not horseshoe then
		crabLegs(B, ctx, { n = if detail >= 2 then 4 else 3, hipX = W * 0.3, y = y - H * 0.15, z0 = -L * 0.25, z1 = L * 0.3, R = 0.75, angles = { 20, 5, -10, -25 }, thick = 0.9, col = "dark", rise = 0.3, piece = "s_arthro_leg", comb = "s_crab_legs4" })
		if detail >= 1 then
			Kit.antennae(B, { bone = "Head", base = { W * 0.22, y, -L * 0.47 }, dir = { 0.55, 0.2, -0.8 }, len = if trilobite then 1.3 else 1.0, w = 0.06, kind = "thread", col = "dark", pri = 1.5 })
		end
	else
		B:bone("Tail1", "Body", 0, y, L * 0.45)
		B:addRig("tail", "Tail1")
		B:limb({ 0, y + 0.05, L * 0.42 }, { 0, y - 0.05, L * 0.42 + 2.2 }, 0.22, { col = "secondary", mat = "hard", bone = "Tail1", pri = 1.15, role = "tail", name = "Telson", mesh = "s_horn_tip", trail = true }, 0.05)
	end
	B:socket("core", at(0, y, 0.3), "Body")
	B:setRig("gait", if pill then "roll" else "skitter")
	if pill then
		B:setRig("gait", "skitter")
	end
end

K.Cambrian = function(B: any, ctx: any)
	local detail = ctx.detail
	local id = Kit.text(ctx)
	local opa = has(id, "opabinia")
	local y = 1.1
	B.boneIndex.Body.pos = { 0, y, 0 }
	B:ell(1.3, 0.62, 3.6, at(0, y, 0.4), { col = "primary", mat = "skin", pri = 1.0, role = "body", name = "Body", mesh = "s_anomalocaris_body" })
	-- lateral swimming flaps
	local n = if detail >= 2 then 3 else if detail == 1 then 2 else 1
	B:mirrorBone("Flap#", "Body", 0.6, y, 0.4)
	B:addRig("wings", { bone = "FlapR", side = 1, flipper = true })
	B:addRig("wings", { bone = "FlapL", side = -1, flipper = true })
	for i = 1, n do
		local z = -0.6 + (i - 1) * (2.2 / math.max(n - 1, 1))
		B:mell(1.4 - i * 0.12, 0.08, 0.8, at(0.95, y - 0.05, z, 0, rad(-10), rad(-8)), { col = "secondary", mat = "skin", bone = "Flap#", pri = 1.2 + i * 0.1, role = "fin", name = "Flap" .. i .. "#", mesh = "s_fin_side" })
	end
	B:bone("Head", "Body", 0, y, -1.3)
	B:setRig("head", "Head")
	stalkEyes(B, ctx, { base = { 0.35, y + 0.15, -1.25 }, h = 0.45, d = 0.32, bone = "Head" })
	if opa then
		if detail >= 1 then
			B:ball(0.3, at(0, y + 0.62, -1.3), { col = "pupil", mat = "glass", bone = "Head", pri = 1.3, role = "eye", name = "MidEye", noCore = true })
		end
		B:limb({ 0, y - 0.05, -1.7 }, { 0, y - 0.5, -3.6 }, 0.18, { col = "primary", mat = "skin", bone = "Head", pri = 1.15, role = "snout", name = "Nozzle", mesh = "s_tail_seg" }, 0.05)
		B:mell(0.22, 0.25, 0.4, at(0.12, y - 0.55, -3.7), { col = "secondary", mat = "hard", bone = "Head", pri = 1.4, role = "claw", name = "Grab#" })
	else
		B:mirrorBone("Arm#", "Head", 0.3, y - 0.1, -1.7)
		B:addRig("arms", { arm = "ArmR", side = 1 })
		B:addRig("arms", { arm = "ArmL", side = -1 })
		Kit.seg(B, { 0.3, y - 0.1, -1.7 }, { 0.45, y - 0.85, -2.5 }, 0.32, { col = "secondary", mat = "hard", bone = "Arm#", pri = 1.12, role = "claw", name = "Grasper#", mesh = "s_mantis_arm", meshL = "s_mantis_arm_l", trail = true, mirror = true }, { 0, 0, -1 })
	end
	B:bone("Tail1", "Body", 0, y, 2.2)
	B:addRig("tail", "Tail1")
	B:mell(0.9, 0.08, 0.7, at(0.45, y + 0.05, 2.45, 0, rad(25), 0), { col = "secondary", mat = "skin", bone = "Tail1", pri = 1.5, role = "fin", name = "TailFan#", mesh = "s_fin_side" })
	B:socket("core", at(0, y, 0.3), "Body")
	B:setRig("gait", "swim")
end

K.Snail = function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id, hint = Kit.text(ctx)
	local cosmic = has(id, "gravity") or string.find(hint, "black", 1, true) ~= nil
	local y = 0.5
	B.boneIndex.Body.pos = { 0, y, 0 }
	-- foot: a long low muscle with a raised neck at the front
	B:ell(1.4, 0.75, 3.6, at(0, 0.38, 0.2), { col = "primary", mat = "skin", pri = 1.0, role = "body", name = "Foot", mesh = "s_snail_foot" })
	B:bone("Head", "Body", 0, 0.7, -1.3)
	B:setRig("head", "Head")
	local hc = { 0, 1.15, -1.45 }
	B:ell(0.95, 1.1, 0.9, at(hc[1], hc[2], hc[3], rad(-15), 0, 0), { col = "primary", mat = "skin", bone = "Head", pri = 1.05, role = "head", name = "Head" })
	-- eye stalks with the eyes on top
	stalkEyes(B, ctx, { base = { 0.18, hc[2] + 0.3, hc[3] - 0.1 }, h = 0.85, d = 0.3, bone = "Head", col = "primary", lean = 0.18 })
	-- shell on the back
	local shellBone = B:bone("ShellB", "Body", 0, 1.0, 0.5)
	B:ell(2.2, 2.3, 2.4, at(0, 1.55, 0.6, rad(-12), 0, 0), { col = if cosmic then "dark" else "secondary", mat = "hard", bone = shellBone, pri = 1.0, role = "body", name = "Shell", mesh = "s_spiral_shell" })
	if cosmic and detail >= 1 then
		B:ell(1.0, 1.0, 0.2, at(1.13, 1.6, 0.6, 0, rad(90), 0), { col = "glow", mat = "neon", glow = true, bone = shellBone, pri = 1.5, role = "detail", name = "Swirl" })
	end
	if detail >= 2 then
		B:mlimb({ 0.25, hc[2] - 0.25, hc[3] - 0.35 }, { 0.42, hc[2] - 0.35, hc[3] - 0.85 }, 0.12, { col = "primary", mat = "skin", bone = "Head", pri = 2.5, role = "antenna", name = "Feeler#" }, 0.1)
	end
	local _ = t
	B:socket("core", at(0, 1.5, 0.6), "Body")
	B:setRig("gait", "glide")
end

K.SeaSpider = function(B: any, ctx: any)
	ctx.kind = "Spider"
	return (require(script.Parent.Arachnid) :: any)(B, ctx)
end

return function(B: any, ctx: any)
	local kind = kindOf(ctx)
	local fn = K[kind] or K.Crab
	fn(B, ctx)
end
