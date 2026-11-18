--!strict
-- Arachnids (the Spider plan, and the spiders and scorpions the Library files under Insect). Sub-kinds from the
-- silhouette hints:
--   spider     cephalothorax + round abdomen, eight legs with knees high above the body, chelicerae with fangs,
--              a cluster of eyes; per species: tarantula (thick hairy legs), harvestman / cellar (tiny body on
--              stilts), huntsman (flat, crab-like sideways legs), jumping (big front eyes, compact), widow /
--              redback (glossy black globe with a red mark), wolf (babies on the back), peacock (raised fan),
--              crab spider (long front pairs held open), whip spider (whip legs, raptorial palps), camel
--              spider (huge jaws), tick / mite (a round shield on short legs)
--   scorpion   flat segmented body, pincered pedipalps, a five-segment tail curling over the back to the sting;
--              whip scorpion (whip tail), pseudoscorpion (no tail), sea scorpion (eurypterid, jaekelopterus:
--              swimming paddles, a spiked telson, grasping front claws)
--   chimeras   drider / jorogumo (a torso rising from the cephalothorax), ushi-oni (an ox head), face grabber
--              (finger legs and a long tail), spider walker / robot spider (metal pod on piston legs, cannon)
-- Leg sculpts: s_arthro_leg (whole leg with its knee), s_arthro_leg_long (stilts), s_arachnid_legs4 (detail 0:
-- one comb per side). Body sculpts: s_spider_ceph (carapace with eye mound and fanged chelicerae),
-- s_spider_abdomen, s_scorpion_body, s_scorpion_claw, s_scorpion_sting (catalogue/s_bugs.py).

local Geom = require(script.Parent.Parent.Geom)
local Heads = require(script.Parent.Parent.Heads)
local Parts = require(script.Parent.Parent.Parts)
local Face = require(script.Parent.Parent.Face)
local Kit = require(script.Parent.Arthro)

local at = Geom.at
local rad = math.rad
local has = Kit.has

local function kindOf(ctx: any): string
	local id = Kit.text(ctx)
	if has(id, "scorpion pseudoscorpion eurypterid jaekelopterus pterygotus") then
		return "Scorpion"
	end
	return "Spider"
end

-- eight legs (four per side). o: y (hip height), hipR (radius of the hip ring), R (foot reach), zs (hip z per leg),
-- angles (foot direction per leg, deg from +X toward -Z = front), thick, piece, col, mat, lift (foot y), front
-- (extra reach of the front pair), segs
local function eightLegs(B: any, ctx: any, o: any)
	local detail = ctx.detail
	local angles = o.angles or { 52, 18, -14, -46 }
	local zs = o.zs or { -0.32, -0.12, 0.08, 0.28 }
	local hx = o.hipR or 0.42
	if detail <= 1 and not o.noComb then
		Kit.comb(B, { tag = "C", hip = { hx, o.y, zs[2] }, foot = { hx + o.R * math.cos(rad(30)), o.lift or 0.04, zs[2] - o.R * math.sin(rad(8)) }, thick = o.thick, col = o.col, mat = o.mat,
			piece = o.comb or (if o.piece == "s_arthro_leg_hairy" then "s_arachnid_legs4_hairy" else "s_arachnid_legs4"), pri = 1.25 })
		return
	end
	local legs = {}
	for i = 1, 4 do
		local a = rad(angles[i])
		local R = o.R * (if i == 1 then (o.front or 1) elseif i == 2 then (o.second or 1) else 1)
		table.insert(legs, { { hx, o.y, zs[i] }, { hx + R * math.cos(a), o.lift or 0.04, zs[i] - R * math.sin(a) }, thick = if i == 1 then (o.frontThick or 1) else 1 })
	end
	Kit.legSet(B, { tagBase = "L", thick = o.thick, segs = o.segs or (if detail >= 3 then 2 else 1), rise = o.rise or 0.42, out = 0.38, piece = o.piece, col = o.col or "dark", mat = o.mat, pri = 1.25 }, legs)
end

-- spider eyes: the two big front eyes (the face), and at detail 2+ the smaller pairs on the eye mound
local function spiderEyes(B: any, ctx: any, c: { number }, r: { number }, o: any)
	local t, detail = ctx.traits, ctx.detail
	local mood = Kit.mood(ctx)
	local kind = o.kind or (if t.cute or (mood ~= "Neutral" and mood ~= "Angry") then "cute" else "bug")
	Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = "Body", mood = mood, detail = detail, kind = kind, spacing = r[1] * (o.spacing or 0.24), y = r[2] * (o.y or 0.35), d = r[1] * (o.d or 0.34),
		noMouth = true, noBrows = kind == "bug" or detail < 3, pri = 1.12, lidCol = "primary" })
	if detail >= 2 and not o.noExtra then
		-- secondary eyes: a wider pair beside and above the main pair, glossy black (or glowing red)
		local glow = o.glow
		for i, e in { { 0.52, 0.55, 0.2 }, { 0.3, 0.85, 0.15 } } do
			if i == 1 or detail >= 3 then
				local f = Face.place({ kind = "ellipsoid", c = c, r = r }, r[1] * e[1], r[2] * e[2], r[1] * 0.02)
				B:mirror({ shape = "Ellipsoid", size = { r[1] * e[3], r[1] * e[3], r[1] * e[3] * 0.6 }, cf = f, col = if glow then "eyeGlow" else "pupil", mat = if glow then "neon" else "glass", glow = glow,
					bone = "Body", pri = 2.0 + i * 0.4, role = "eye", name = "SmallEye" .. i .. "#", noCore = true })
			end
		end
	end
end

-- a torso (drider, jorogumo) rising from the front of the cephalothorax: hips, chest, head with a face, arms
local function riderTorso(B: any, ctx: any, base: { number }, o: any)
	local detail = ctx.detail
	local t = ctx.traits
	B:bone("Waist", "Body", base[1], base[2], base[3])
	B:limb(base, { 0, base[2] + 1.6, base[3] - 0.2 }, 1.05, { col = o.col or "secondary", mat = o.mat or "cloth", bone = "Waist", pri = 1.05, role = "torso", name = "Torso", mesh = "s_torso" }, 0.15)
	local hp = { 0, base[2] + 2.15, base[3] - 0.25 }
	B:bone("Head", "Waist", hp[1], hp[2] - 0.4, hp[3])
	B:setRig("head", "Head")
	Heads.person(B, { p = { hp[1], hp[2] - 0.45, hp[3] }, s = 0.95 }, t)
	if detail >= 1 then
		Parts.armPair(B, { x = 0.62, y = base[2] + 1.35, z = base[3] - 0.2, len = 1.4, w = 0.26, col = "skin", parent = "Waist", detail = math.min(detail, 1) })
	end
end

local function spider(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id, hint = Kit.text(ctx)
	local mech = t.robot or t.mechanical
	local walker = has(id, "walker")
	local tank = has(id, "tank")
	local tick = has(id, "tick mite")
	local stilts = has(id, "harvestman cellar daddy") or string.find(hint, "spindly", 1, true) ~= nil or string.find(hint, "very long legs", 1, true) ~= nil or string.find(hint, "extremely long legs", 1, true) ~= nil
	local tarantula = has(id, "tarantula birdeater goliath") or string.find(hint, "thick legs", 1, true) ~= nil
	local huntsman = has(id, "huntsman") or string.find(hint, "flat", 1, true) ~= nil
	local jumper = has(id, "jumping peacock")
	local widow = has(id, "widow redback") or string.find(hint, "hourglass", 1, true) ~= nil
	local crabby = has(id, "crab")
	local whip = has(id, "whip")
	local camel = has(id, "camel")
	local hairy = tarantula or has(id, "wolf camel jumping") or string.find(hint, "hairy", 1, true) ~= nil or string.find(hint, "fuzzy", 1, true) ~= nil
	local giant = has(id, "giant kaiju queen goliath") or t.size == "Large" or t.size == "Huge" or t.size == "Colossal"
	local rider = has(id, "drider jorogumo")
	local ox = has(id, "ushi")
	local grabber = has(id, "grabber")
	local crystal = has(id, "crystal")
	local phase = has(id, "phase")

	-- proportions: body height y, cephalothorax C, abdomen A, leg reach R
	local y = 1.15
	local C = { 1.1, 0.72, 1.25 }
	local A = { 1.65, 1.42, 1.85 }
	local R = 2.5
	if tarantula then
		y, C, A, R = 1.0, { 1.25, 0.8, 1.35 }, { 1.7, 1.45, 1.8 }, 2.25
	elseif stilts then
		y, C, A, R = 2.2, { 0.55, 0.42, 0.6 }, { 0.85, 0.7, 0.95 }, 3.6
	elseif huntsman then
		y, C, A, R = 0.6, { 1.2, 0.48, 1.25 }, { 1.25, 0.65, 1.7 }, 2.9
	elseif jumper then
		y, C, A, R = 0.9, { 1.2, 0.95, 1.2 }, { 1.25, 1.05, 1.45 }, 1.55
	elseif widow then
		y, C, A, R = 1.3, { 0.85, 0.6, 0.95 }, { 1.85, 1.75, 1.95 }, 2.6
	elseif tick then
		y, C, A, R = 0.55, { 0.62, 0.38, 0.55 }, { 1.9, 0.95, 2.1 }, 1.15
	elseif walker or tank then
		y, C, A, R = 2.4, { 2.2, 1.4, 2.2 }, { 1.4, 1.0, 1.4 }, 3.2
	end
	B.boneIndex.Body.pos = { 0, y, 0 }
	local mat = if mech then "metal" elseif crystal then "glass" elseif hairy then "fur" else "hard"
	local cc = { 0, y + C[2] * 0.12, 0 }
	if walker or tank then
		-- the pod: cockpit dome (walker) or hull with a turret (tank)
		B:ell(C[1], C[2], C[3], at(cc[1], cc[2], cc[3]), { col = "primary", mat = "metal", pri = 1, role = "body", name = "Pod", mesh = "s_mech_pod" })
		if walker then
			B:ell(1.3, 0.75, 0.9, at(0, cc[2] + 0.35, -0.75), { col = "glass", mat = "glass", tr = 0.25, pri = 1.1, role = "detail", name = "Canopy" })
		else
			B:cyl(1.0, 1.4, at(0, cc[2] + 0.75, 0, 0, 0, rad(90)), { col = "secondary", mat = "metal", pri = 1.1, role = "body", name = "TurretRing" })
			B:cyl(2.4, 0.38, at(0, cc[2] + 0.95, -1.4, 0, rad(90), 0), { col = "gunmetal", mat = "metal", pri = 1.2, role = "cannon", name = "Barrel" })
		end
		B:mball(0.32, at(0.5, cc[2] + 0.05, -C[3] * 0.48), { col = "eyeGlow", mat = "neon", glow = true, pri = 1.15, role = "eye", name = "Lens#" })
		eightLegs(B, ctx, { y = y - 0.1, hipR = C[1] * 0.42, R = R, thick = 1.6, col = "secondary", mat = "metal", piece = "s_mech_leg", comb = "s_arachnid_legs4", zs = if tank then { -0.6, 0.0, 0.6, 0.6 } else { -0.6, -0.2, 0.2, 0.6 } })
		B:socket("core", at(0, y, 0), "Body")
		B:setRig("gait", "skitter")
		B:setRig("materialMotion", "clank")
		return
	end

	-- cephalothorax with the eye mound and chelicerae
	local ceph = B:ell(C[1], C[2], C[3], at(cc[1], cc[2], cc[3], rad(-4), 0, 0), { col = "primary", mat = mat, pri = 1.0, role = "body", name = "Ceph", mesh = "s_spider_ceph" })
	local _ = ceph
	-- abdomen on its own bone, behind and above the waist
	local ab = B:bone("Abdomen", "Body", 0, y, C[3] * 0.45)
	B:addRig("tail", ab)
	local az = C[3] * 0.42 + A[3] * 0.44
	local ay = y + A[2] * (if stilts then 0.15 elseif tick then -0.02 else 0.22)
	if tick then
		-- tick: the scutum shield and the bloated body are one flat oval; the capitulum is a small head in front
		az = C[3] * 0.1 + A[3] * 0.32
		ay = y
	end
	B:ell(A[1], A[2], A[3], at(0, ay, az, rad(if tick then 0 else 14), 0, 0), { col = if widow or phase then "primary" else "primary", mat = if widow then "glass" elseif has(id, "mirror") then "metal" else mat,
		tr = if phase then 0.35 else nil, bone = ab, pri = 1.0, role = "body", name = "Abdomen", mesh = if tick then "s_tick_body" else "s_spider_abdomen" })
	-- markings
	if widow and detail >= 1 then
		B:ell(A[1] * 0.3, A[2] * 0.14, A[3] * 0.46, at(0, ay + A[2] * 0.47, az + A[3] * 0.04, rad(14), 0, 0), { col = if has(id, "redback") then "red" else "red", mat = "hard", bone = ab, pri = 1.4, role = "detail", name = "Hourglass" })
	elseif (string.find(hint, "violin", 1, true) or has(id, "recluse")) and detail >= 2 then
		B:ell(C[1] * 0.3, C[2] * 0.2, C[3] * 0.55, at(0, cc[2] + C[2] * 0.42, cc[3] + 0.05, rad(-4), 0, 0), { col = "darker", mat = "hard", pri = 2.2, role = "detail", name = "Violin" })
	elseif detail >= 2 and (has(id, "spitting wolf orb fishing") or string.find(hint, "spotted", 1, true)) then
		for i = 1, (if detail >= 3 then 3 else 2) do
			B:ell(A[1] * (0.42 - i * 0.07), A[2] * 0.12, A[3] * 0.13, at(0, ay + A[2] * 0.47 - i * 0.07, az - A[3] * 0.18 + i * A[3] * 0.18, rad(14 + i * 14), 0, 0),
				{ col = "secondary", mat = "hard", bone = ab, pri = 2.0 + i * 0.1, role = "detail", name = "Chevron" .. i })
		end
	end
	if has(id, "wolf") and detail >= 2 then
		for i, p in { { 0.35, 0.4, -0.1 }, { -0.3, 0.42, 0.2 }, { 0.05, 0.47, 0.42 } } do
			if i <= detail - 1 then
				B:ball(A[1] * 0.2, at(A[1] * p[1] * 0.8, ay + A[2] * p[2] * 1.1, az + A[3] * p[3] * 0.6), { col = "secondary", mat = "fur", bone = ab, pri = 2.4 + i * 0.1, role = "detail", name = "Baby" .. i })
			end
		end
	end
	if has(id, "peacock") and detail >= 1 then
		B:ell(A[1] * 1.9, A[2] * 1.4, 0.12, at(0, ay + A[2] * 0.85, az + A[3] * 0.2, rad(-20), 0, 0), { col = "secondary", mat = "skin", bone = ab, pri = 1.3, role = "detail", name = "Fan", mesh = "s_petal" })
	end
	if has(id, "diving") and detail >= 1 then
		B:ell(5.4, 3.0, 5.4, at(0, 1.3, 0.6), { col = "glass", mat = "glass", tr = 0.7, pri = 2.6, role = "shell", name = "Bubble", noCore = true })
	end
	if has(id, "bolas") and detail >= 2 then
		B:limb({ 0.9, y - 0.1, -1.1 }, { 1.1, 0.35, -1.6 }, 0.03, { col = "white", mat = "skin", pri = 2.6, role = "detail", name = "Thread" }, 0.02)
		B:ball(0.45, at(1.1, 0.3, -1.65), { col = "secondary", mat = "glass", pri = 2.5, role = "detail", name = "Bolas" })
	end
	if has(id, "queen") and detail >= 1 then
		-- crown-shaped carapace: spikes round the back of the cephalothorax
		for i = 1, (if detail >= 3 then 3 else 2) do
			local a = rad(-60 + (i - 1) * 60)
			B:mlimb({ C[1] * 0.3 * math.cos(a) + 0.08, cc[2] + C[2] * 0.3, cc[3] + C[3] * 0.18 * math.sin(a) + 0.15 }, { C[1] * 0.45 * math.cos(a) + 0.15, cc[2] + C[2] * 0.3 + 0.75 - i * 0.08, cc[3] + 0.3 }, 0.18,
				{ col = "secondary", mat = if crystal then "glass" else "hard", pri = 1.5 + i * 0.1, role = "spike", name = "Crown" .. i .. "#", mesh = "s_horn_tip" }, 0.08)
		end
	end

	-- head / face
	local face = { cc[1], cc[2] + C[2] * 0.05, cc[3] - C[3] * 0.08 }
	local fr = { C[1] * 0.5, C[2] * 0.62, C[3] * 0.5 }
	if rider then
		B:setRig("head", nil)
		riderTorso(B, ctx, { 0, cc[2] + C[2] * 0.3, cc[3] - C[3] * 0.32 }, { col = if has(id, "jorogumo") then "secondary" else "dark", mat = if has(id, "jorogumo") then "cloth" else "skin" })
	elseif ox then
		B:bone("Head", "Body", 0, cc[2] + 0.2, cc[3] - C[3] * 0.4)
		B:setRig("head", "Head")
		local info = Heads.beast(B, { p = { 0, cc[2] + 0.35, cc[3] - C[3] * 0.55 }, s = 1.35, arch = "bovine", eyes = "fierce" }, t)
		Parts.horns(B, { bone = "Head", x = 0.42, y = info.top[2] - 0.1, z = info.top[3] + 0.05, len = 1.2, w = 0.28, kind = "curved", segs = if detail <= 1 then 2 else 3, pri = 1.3 })
	else
		B:bone("Head", "Body", 0, cc[2], cc[3] - C[3] * 0.3)
		B:setRig("head", "Head")
		spiderEyes(B, ctx, face, fr, {
			d = if jumper then 0.62 elseif has(id, "ogre") then 0.6 elseif tick then 0.35 else 0.38, spacing = if jumper then 0.36 else 0.3, y = if jumper then 0.05 else 0.3,
			glow = string.find(hint, "red eyes", 1, true) ~= nil or has(id, "kaiju"), kind = if mech then "glow" elseif string.find(hint, "red eyes", 1, true) then "glow" else nil, noExtra = tick,
		})
		-- chelicerae + fangs (the ceph sculpt carries them; primitives from detail 1)
		if detail >= 1 and not tick then
			local big = camel or has(id, "pelican")
			Kit.mandibles(B, { bone = "Head", root = { C[1] * 0.16, cc[2] - C[2] * 0.15, cc[3] - C[3] * 0.4 }, len = if big then 1.1 else C[3] * 0.32, up = if has(id, "pelican") then 0.5 else -0.35, spread = 0.05,
				w = if big then 0.38 else C[1] * 0.24, col = if big then "secondary" else "darker", pri = 1.35, piece = if big then "s_stag_jaw" else "s_spider_fang" })
		end
	end
	if detail >= 2 and not tick and not rider then
		-- pedipalps: short feelers beside the fangs
		B:mlimb({ C[1] * 0.3, cc[2] - C[2] * 0.1, cc[3] - C[3] * 0.38 }, { C[1] * 0.5, cc[2] - C[2] * 0.25, cc[3] - C[3] * 0.85 }, 0.16, { col = "dark", mat = mat, bone = "Head", pri = 2.1, role = "limb", name = "Palp#", mesh = "s_arthro_tibia" }, 0.08)
	end
	if whip and detail >= 1 then
		-- whip spider: spiny raptorial palps held out front
		Kit.seg(B, { C[1] * 0.3, cc[2], cc[3] - C[3] * 0.4 }, { C[1] * 0.75, cc[2] + 0.2, cc[3] - C[3] * 1.2 }, 0.22, { col = "secondary", mat = mat, bone = "Head", pri = 1.4, role = "claw", name = "Raptor#", mesh = "s_mantis_arm", meshL = "s_mantis_arm_l", mirror = true }, { 0, 1, 0 })
	end

	-- legs
	local legO = { y = y - C[2] * 0.12, hipR = C[1] * 0.38, R = R, thick = if tarantula then 1.75 elseif jumper then 1.4 elseif stilts then 0.7 else 1.0,
		piece = if stilts then "s_arthro_leg_long" elseif hairy then "s_arthro_leg_hairy" else "s_arthro_leg", col = if crystal then "secondary" else "dark", mat = if crystal then "glass" elseif hairy then "fur" else "hard",
		zs = { -C[3] * 0.3, -C[3] * 0.1, C[3] * 0.1, C[3] * 0.3 }, rise = if stilts then 0.62 else 0.42 }
	if huntsman then
		legO.angles = { 38, 12, -12, -38 }
		legO.front, legO.second = 1.2, 1.15
	elseif crabby then
		legO.angles = { 40, 20, -15, -42 }
		legO.front, legO.second = 1.35, 1.3
		legO.frontThick = 1.2
	elseif whip then
		legO.angles = { 70, 14, -16, -44 }
		legO.front = 1.9
		legO.frontThick = 0.5
	elseif tick then
		legO.angles = { 50, 20, -15, -45 }
	elseif grabber then
		legO.angles = { 70, 25, -20, -70 }
		legO.piece = "s_finger_leg"
	end
	eightLegs(B, ctx, legO)
	if grabber then
		-- long whip tail
		local p0 = { 0, ay, az + A[3] * 0.45 }
		local parent = ab
		for i = 1, (if detail >= 2 then 3 else 1) do
			local p1 = { 0, p0[2] - 0.15, p0[3] + 1.4 }
			local bn = B:bone("Tail" .. i, parent, p0[1], p0[2], p0[3])
			B:addRig("tail", bn)
			B:limb(p0, p1, 0.3 - i * 0.06, { col = "primary", mat = "skin", bone = bn, pri = 1.3 + i * 0.1, role = "tail", name = "Tail" .. i, trail = true }, 0.15)
			p0, parent = p1, bn
		end
	end
	if has(id, "anansi") and detail >= 1 then
		B:cyl(0.5, 0.75, at(0, cc[2] + C[2] * 0.75, cc[3] - 0.05, 0, 0, rad(90)), { col = "secondary", mat = "cloth", bone = "Head", pri = 1.4, role = "hat", name = "HatCrown" })
		B:cyl(0.08, 1.25, at(0, cc[2] + C[2] * 0.5, cc[3] - 0.05, 0, 0, rad(90)), { col = "secondary", mat = "cloth", bone = "Head", pri = 1.45, role = "hat", name = "HatBrim" })
	end
	B:socket("core", at(0, y, 0.4), "Body")
	B:setRig("gait", if jumper then "pounce" else "skitter")
end

local function scorpion(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id, hint = Kit.text(ctx)
	local sea = has(id, "eurypterid jaekelopterus pterygotus") or string.find(hint, "sea scorpion", 1, true) ~= nil or string.find(hint, "aquatic scorpion", 1, true) ~= nil
	local whip = has(id, "whip")
	local pseudo = has(id, "pseudoscorpion") or string.find(hint, "without tail", 1, true) ~= nil
	local glowSting = string.find(hint, "glowing stinger", 1, true) ~= nil
	local glossy = string.find(hint, "glossy", 1, true) ~= nil
	local y = if sea then 0.75 else 0.85
	B.boneIndex.Body.pos = { 0, y, 0 }
	local Bw, Bh, Bl = 1.35, 0.6, 2.5
	if sea then
		Bw, Bh, Bl = 1.6, 0.5, 3.2
	elseif pseudo then
		Bw, Bh, Bl = 1.3, 0.55, 2.0
	end
	local mat = if glossy then "glass" else "hard"
	-- body: carapace + mesosoma in one flat plated mass
	B:ell(Bw, Bh, Bl, at(0, y, 0.15, rad(-2), 0, 0), { col = "primary", mat = mat, pri = 1.0, role = "body", name = "Mesosoma", mesh = if sea then "s_eurypterid_body" else "s_scorpion_body" })
	B:bone("Head", "Body", 0, y, -Bl * 0.4)
	B:setRig("head", "Head")
	local face = { 0, y + 0.02, -Bl * 0.28 }
	spiderEyes(B, ctx, face, { Bw * 0.32, Bh * 0.55, Bl * 0.22 }, { d = 0.42, spacing = 0.3, y = 0.55, noExtra = true })
	-- pedipalps with pincers (the scorpion's arms)
	local sh = { Bw * 0.3, y - 0.05, -Bl * 0.38 }
	B:mirrorBone("Claw#", "Body", sh[1], sh[2], sh[3])
	B:addRig("arms", { arm = "ClawR", side = 1 })
	B:addRig("arms", { arm = "ClawL", side = -1 })
	local big = (if pseudo then 1.35 elseif whip then 0.9 elseif sea then (if has(id, "jaekelopterus") then 1.0 else 0.0) else 1.0) * (if has(id, "emperor") then 1.2 else 1)
	if big > 0 then
		local elbow = { Bw * 0.85, y + 0.1, -Bl * 0.62 }
		local wrist = { Bw * 0.62, y + 0.15, -Bl * 0.62 - 0.85 * big }
		if detail >= 1 then
			B:mlimb(sh, elbow, 0.3 * big, { col = "primary", mat = mat, bone = "Claw#", pri = 1.25, role = "limb", name = "Humerus#", mesh = "s_arthro_seg" }, 0.12)
		end
		if detail >= 2 then
			B:mlimb(elbow, wrist, 0.32 * big, { col = "primary", mat = mat, bone = "Claw#", pri = 1.3, role = "limb", name = "Patella#", mesh = "s_arthro_seg" }, 0.1)
		end
		-- the chela: palm + fingers, pointing forward (sculpt s_scorpion_claw)
		local cl = if detail >= 2 then wrist else elbow
		local tip = { cl[1] - 0.05, cl[2] + 0.02, cl[3] - 1.25 * big }
		local f, len = Kit.segFrame(cl, tip)
		B:mirror({ shape = "Ellipsoid", size = { 0.62 * big, len * 1.05, 0.42 * big }, cf = f, seg = "Y", col = if sea then "primary" else "secondary", mat = mat, bone = "Claw#", pri = 1.12, role = "claw", name = "Chela#",
			mesh = "s_scorpion_claw", meshL = "s_scorpion_claw_l", trail = true })
	end
	-- walking legs (sea scorpions: three pairs + the big swimming paddles)
	local legY = y - 0.08
	if detail <= 1 then
		Kit.comb(B, { tag = "C", hip = { Bw * 0.35, legY, 0.1 }, foot = { Bw * 0.35 + 1.5, 0.04, 0.2 }, thick = 1.1, piece = "s_arachnid_legs4", pri = 1.28 })
	else
		local legs = {}
		local n = if sea then 3 else 4
		for i = 1, n do
			local z = -Bl * 0.22 + (i - 1) * Bl * 0.16
			local a = rad(30 - (i - 1) * 25)
			local R = 1.55 + i * 0.08
			table.insert(legs, { { Bw * 0.35, legY, z }, { Bw * 0.35 + R * math.cos(a), 0.04, z - R * math.sin(a) } })
		end
		Kit.legSet(B, { tagBase = "L", thick = 1.0, segs = if detail >= 3 then 2 else 1, rise = 0.38, col = "dark", mat = mat, pri = 1.32 }, legs)
	end
	if sea and detail >= 1 then
		-- swimming paddles: a long oar leg ending in a broad blade
		B:mirrorBone("Paddle#", "Body", Bw * 0.4, y - 0.05, Bl * 0.15)
		B:addRig("wings", { bone = "PaddleR", side = 1, flipper = true })
		B:addRig("wings", { bone = "PaddleL", side = -1, flipper = true })
		B:mlimb({ Bw * 0.4, y - 0.05, Bl * 0.15 }, { Bw * 0.4 + 1.3, y - 0.3, Bl * 0.15 + 0.9 }, 0.24, { col = "dark", mat = mat, bone = "Paddle#", pri = 1.35, role = "limb", name = "Oar#", mesh = "s_arthro_seg" }, 0.1)
		B:mell(1.0, 0.1, 0.7, at(Bw * 0.4 + 1.7, y - 0.38, Bl * 0.15 + 1.2, 0, rad(-35), rad(-8)), { col = "secondary", mat = mat, bone = "Paddle#", pri = 1.4, role = "fin", name = "Paddle#", mesh = "s_turtle_flipper", meshL = "s_turtle_flipper_l" })
	end
	-- tail (metasoma): segments curling up over the back to the sting; whip scorpions a thin whip; sea scorpions a
	-- flat spike; pseudoscorpions none
	if not pseudo then
		local ab = B:bone("Tail0", "Body", 0, y, Bl * 0.55)
		local p0 = { 0, y + 0.05, Bl * 0.6 }
		local n = if detail >= 3 then 5 elseif detail == 2 then 3 elseif detail == 1 then 2 else 1
		local parent = ab
		B:addRig("tail", ab)
		if whip then
			B:limb(p0, { 0, y + 0.5, p0[3] + 2.6 }, 0.07, { col = "dark", mat = "hard", bone = ab, pri = 1.3, role = "tail", name = "Whip", trail = true }, 0.05)
		elseif sea then
			for i = 1, math.min(n, 3) do
				local p1 = { 0, p0[2] + 0.02, p0[3] + 0.8 }
				local bn = B:bone("Tail" .. i, parent, p0[1], p0[2], p0[3])
				B:addRig("tail", bn)
				B:limb(p0, p1, 0.7 - i * 0.12, { col = "primary", mat = mat, bone = bn, pri = 1.2 + i * 0.1, role = "tail", name = "Tail" .. i, mesh = "s_scorpion_seg", depth = 0.32 }, 0.15)
				p0, parent = p1, bn
			end
			B:limb(p0, { 0, p0[2] + 0.05, p0[3] + 1.2 }, 0.5, { col = "secondary", mat = mat, bone = parent, pri = 1.5, role = "tail", name = "Telson", mesh = "s_fin_side", depth = 0.12, trail = true }, 0.1)
		else
			-- a curl from the rear up and forward: points on an arc
			local L = 3.4
			local arc = rad(if detail <= 0 then 110 else 150)
			local cR = L / arc
			local cx = { 0, y + 0.05 + cR, Bl * 0.6 }
			for i = 1, n do
				local a0, a1 = (i - 1) / n * arc, i / n * arc
				local q0 = { 0, cx[2] - cR * math.cos(a0), cx[3] + cR * math.sin(a0) }
				local q1 = { 0, cx[2] - cR * math.cos(a1), cx[3] + cR * math.sin(a1) }
				local bn = B:bone("Tail" .. i, parent, q0[1], q0[2], q0[3])
				B:addRig("tail", bn)
				B:limb(q0, q1, 0.48 - i * 0.03, { col = "primary", mat = mat, bone = bn, pri = 1.1 + i * 0.06, role = "tail", name = "Tail" .. i, mesh = "s_scorpion_seg" }, 0.12)
				p0, parent = q1, bn
			end
			-- telson: bulb + curved sting pointing forward and down
			local tipA = arc + rad(40)
			local tip = { 0, p0[2] - 0.9 * math.cos(tipA) * 0.6, p0[3] - 0.9 }
			Kit.seg(B, p0, tip, 0.5, { col = if glowSting then "glow" else "secondary", mat = if glowSting then "neon" else mat, glow = glowSting, bone = parent, pri = 1.15, role = "tail", name = "Telson", mesh = "s_scorpion_sting", trail = true }, { 0, 1, 0 })
		end
	end
	local _ = t
	B:socket("core", at(0, y, 0.2), "Body")
	B:setRig("gait", "skitter")
end

return function(B: any, ctx: any)
	local kind = if ctx.kind == "Scorpion" then "Scorpion" else kindOf(ctx)
	if kind == "Scorpion" then
		return scorpion(B, ctx)
	end
	return spider(B, ctx)
end
