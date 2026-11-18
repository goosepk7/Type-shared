--!strict
-- Biped: two-legged creatures.
--   Primates: great apes (knuckle-walking, massive shoulders, arms to the ground), monkeys (slim, semi-upright, long
--   curling tail), baboons (dog snout, four-square stance), prosimians (huge eyes, big ears, crouched, long tail).
--   Faces are a skin-coloured mask with close-set forward eyes, a brow ridge and a muzzle (sculpt s_primate_face).
--   Theropods: forward-leaning body balanced over the hips by a long counter-weight tail, drumstick thighs, bird
--   feet. Sub-kinds: carnosaur (big skull, three-fingered arms), tyrant (huge head, tiny arms), raptor (slim,
--   feathered arms, sickle claw, stiff tail), ornithomimid (long neck, small beaked head), therizinosaur (pot belly,
--   scythe claws), oviraptor (parrot beak, crest), spinosaur (croc snout, sail). Head crests and horns per word.
--   Other kinds: "brute" (troll, ogre, kobold, kappa), "hopper" (kangaroo).

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Heads = require(script.Parent.Parent.Heads)
local Props = require(script.Parent.Parent.Props)
local Face = require(script.Parent.Parent.Face)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local C = {
	darkSkin = { 0.24, 0.21, 0.21 },
	greySkin = { 0.42, 0.4, 0.42 },
	pinkSkin = { 0.9, 0.62, 0.6 },
	red = { 0.85, 0.2, 0.18 },
	blue = { 0.25, 0.45, 0.9 },
	cream = { 0.95, 0.88, 0.74 },
	black = { 0.12, 0.11, 0.12 },
	white = { 0.94, 0.93, 0.9 },
	gold = { 0.92, 0.66, 0.2 },
	claw = { 0.17, 0.15, 0.14 },
}

local function wordIn(id: string, w: string): boolean
	if string.find(w, " ", 1, true) then
		return string.find(id, w, 1, true) ~= nil
	end
	if string.sub(w, -1) == "*" then
		return string.find(id, "%f[%a]" .. string.sub(w, 1, -2)) ~= nil
	end
	return string.find(id, "%f[%a]" .. w .. "%f[^%a]") ~= nil
end

local KINDS: { { any } } = {
	{ "baboon", { "baboon", "mandrill", "gelada", "drill" } },
	{ "prosimian", { "galago", "bushbaby", "loris", "tarsier", "lemur", "aye-aye", "night monkey" } },
	{ "ape", { "gorilla", "chimp", "chimpanzee", "bonobo", "orangutan", "ape", "gibbon", "siamang", "yeti", "bigfoot", "sasquatch" } },
	{ "monkey", { "monkey*", "macaque", "langur", "capuchin", "colobus", "marmoset", "tamarin", "saki", "uakari", "titi", "howler" } },
	{ "tyrant", { "rex", "tyrannosaurus", "tyrannosaur", "albertosaurus", "daspletosaurus", "gorgosaurus", "tarbosaurus", "nanotyrannus", "yutyrannus",
		"qianzhousaurus", "dilong", "carnotaurus", "abelisaurus", "majungasaurus", "rajasaurus", "rugops", "skorpiovenator" } },
	{ "spino", { "spinosaurus", "baryonyx", "suchomimus" } },
	{ "raptor", { "raptor", "velociraptor", "deinonychus", "utahraptor", "dakotaraptor", "austroraptor", "pyroraptor", "dromaeosaurus", "microraptor",
		"unenlagia", "halszkaraptor", "troodon", "archaeopteryx", "sinosauropteryx", "compsognathus", "eoraptor", "coelophysis", "shuvuuia", "mononykus", "yi qi" } },
	{ "mimic", { "gallimimus", "ornithomimus", "struthiomimus", "deinocheirus" } },
	{ "therizino", { "therizinosaurus", "segnosaurus", "nothronychus", "alxasaurus" } },
	{ "oviraptor", { "oviraptor", "citipati", "gigantoraptor" } },
	{ "carnosaur", { "allosaurus", "giganotosaurus", "carcharodontosaurus", "mapusaurus", "acrocanthosaurus", "torvosaurus", "megalosaurus", "ceratosaurus",
		"concavenator", "cryolophosaurus", "dilophosaurus", "monolophosaurus", "guanlong", "herrerasaurus", "dinosaur", "kaiju" } },
}

local DINO = { carnosaur = true, tyrant = true, raptor = true, mimic = true, therizino = true, oviraptor = true, spino = true }
local PRIMATE = { ape = true, monkey = true, baboon = true, prosimian = true }

local function kindOf(ctx: any): string
	local t, id = ctx.traits, string.lower(ctx.result.id)
	if ctx.kind then
		return ctx.kind
	end
	for _, row in KINDS do
		for _, w in row[2] do
			if wordIn(id, w) then
				return row[1]
			end
		end
	end
	if t.dino or t.scaly or string.find(id, "lizard") then
		return "carnosaur"
	elseif string.find(id, "kangaroo") or string.find(id, "wallaby") or t.longEars then
		return "hopper"
	end
	for _, tag in ctx.result.tags or {} do
		if tag == "primate" then
			return "monkey"
		elseif tag == "dinosaur" then
			return "carnosaur"
		end
	end
	if t.mammal or t.fluffy or string.find(id, "bear") then
		return "ape"
	end
	return "brute"
end

-- ============================================================================================ theropods
-- body = { length, depth, width }, leg = hip height, legW, neck, neckUp (deg from vertical), head (size), arms (length),
-- hand: three|tiny|feather|scythe|thumb, tail (length), feathers, beak (beaked head), sail
local THEROPOD: { [string]: any } = {
	carnosaur = { body = { 2.6, 1.35, 1.25 }, leg = 1.6, legW = 0.42, neck = 0.85, neckUp = 42, head = 1.3, arms = 0.95, hand = "three", tail = 2.9 },
	tyrant = { body = { 2.6, 1.55, 1.45 }, leg = 1.6, legW = 0.5, neck = 0.7, neckUp = 48, head = 1.62, arms = 0.48, hand = "tiny", tail = 2.7 },
	raptor = { body = { 1.9, 1.0, 0.9 }, leg = 1.5, legW = 0.27, neck = 0.95, neckUp = 50, head = 0.86, arms = 1.2, hand = "feather", tail = 3.3, feathers = true,
		sickle = true, tailW = 0.55 },
	mimic = { body = { 1.9, 1.15, 1.0 }, leg = 2.1, legW = 0.3, neck = 1.8, neckUp = 28, head = 0.62, arms = 1.1, hand = "three", tail = 2.8, feathers = true,
		beak = true, tailW = 0.5 },
	therizino = { body = { 2.1, 1.75, 1.65 }, pitch = 30, leg = 1.35, legW = 0.44, neck = 1.5, neckUp = 15, head = 0.6, arms = 1.7, hand = "scythe", tail = 1.7,
		feathers = true, beak = true },
	oviraptor = { body = { 1.8, 1.2, 1.1 }, leg = 1.4, legW = 0.3, neck = 1.0, neckUp = 30, head = 0.95, arms = 1.0, hand = "feather", tail = 1.9, feathers = true,
		beak = true, crest = "casque" },
	spino = { body = { 3.0, 1.3, 1.15 }, leg = 1.25, legW = 0.42, neck = 1.0, neckUp = 38, head = 1.3, arms = 1.15, hand = "thumb", tail = 3.3, snout = 1.7,
		sail = 1.6 },
}

local DWORD: { [string]: any } = {
	carnotaurus = { horns = "bull", head = 1.35 },
	majungasaurus = { horns = "bump", head = 1.35 },
	rajasaurus = { horns = "crown", head = 1.35 },
	abelisaurus = { head = 1.4 },
	rugops = { horns = "rugose", head = 1.35 },
	skorpiovenator = { horns = "rugose", head = 1.35 },
	qianzhousaurus = { snout = 1.6, head = 1.3 },
	dilong = { feathers = true, body = { 2.0, 1.15, 1.05 }, head = 1.2 },
	yutyrannus = { feathers = true },
	nanotyrannus = { body = { 2.3, 1.3, 1.2 }, head = 1.35 },
	albertosaurus = { head = 1.45 },
	gorgosaurus = { head = 1.45, horns = "brow" },
	allosaurus = { horns = "brow" },
	ceratosaurus = { horns = "nose", ridge = true },
	dilophosaurus = { crest = "twin" },
	cryolophosaurus = { crest = "transverse" },
	monolophosaurus = { crest = "single" },
	guanlong = { crest = "single", crestK = 1.5, body = { 2.1, 1.1, 1.0 } },
	acrocanthosaurus = { sail = 0.6 },
	concavenator = { hump = true },
	giganotosaurus = { head = 1.45, body = { 2.9, 1.45, 1.35 } },
	carcharodontosaurus = { head = 1.5, teeth = true },
	mapusaurus = { head = 1.4 },
	herrerasaurus = { body = { 2.2, 1.1, 1.0 }, head = 1.05 },
	torvosaurus = { head = 1.45 },
	kaiju = { spikes = true, head = 1.4 },
	spinosaurus = { sail = 1.9 },
	baryonyx = { sail = 0, ridge = true },
	suchomimus = { sail = 0.55 },
	troodon = { bigEyes = true, head = 0.95 },
	compsognathus = { feathers = false, hand = "three", tail = 3.0 },
	coelophysis = { feathers = false, hand = "three", neck = 1.2, body = { 2.0, 0.9, 0.85 } },
	eoraptor = { feathers = false, hand = "three" },
	archaeopteryx = { wings = true },
	microraptor = { wings = true },
	["yi qi"] = { batwings = true, feathers = true },
	halszkaraptor = { neck = 1.7, neckUp = 25, snout = 1.4 },
	austroraptor = { snout = 1.5 },
	utahraptor = { body = { 2.4, 1.25, 1.15 }, head = 1.0 },
	dakotaraptor = { body = { 2.3, 1.2, 1.1 } },
	mononykus = { hand = "tiny", leg = 1.8, legW = 0.22 },
	shuvuuia = { hand = "tiny", leg = 1.8, legW = 0.22 },
	sinosauropteryx = { banded = true, tail = 3.8 },
	unenlagia = { wings = true },
	deinocheirus = { arms = 2.2, hand = "scythe", hump = true, body = { 2.4, 1.6, 1.4 }, neck = 1.4, duck = true },
	gigantoraptor = { body = { 2.3, 1.45, 1.35 }, head = 1.0 },
	citipati = { crest = "casque" },
}

-- Theropod / bird foot: the centre toe leads s_bird_foot_talon; side toes are its members (and a raised sickle claw)
local function dinoLegs(B: any, P: any, hip: { number }, detail: number, mat: string)
	local h, w, x, z = hip[2], P.legW, hip[1], hip[3]
	if detail <= 0 then
		local hb = B:bone("Hip", "Body", 0, h, z)
		B:addRig("legs", { hip = hb, side = 0, phase = 0, len = h })
		B:ell(x * 2 + w * 1.8, h * 1.1, w * 2.2, at(0, h * 0.55, z), { col = "primary", mat = mat, bone = hb, pri = 1.2, role = "limb", name = "Legs" })
		return
	end
	local hr, hl = B:mirrorBone("Hip#", "Body", x, h, z)
	local knee = { x + w * 0.1, h * 0.55, z - h * 0.2 }
	local ankle = { x + w * 0.05, h * 0.24, z + h * 0.08 }
	local foot = { x, 0, z - h * 0.02 }
	local kr, kl = B:mirrorBone("Knee#", "Hip#", knee[1], knee[2], knee[3])
	B:addRig("legs", { hip = hr, knee = kr, side = 1, phase = 0, len = h })
	B:addRig("legs", { hip = hl, knee = kl, side = -1, phase = 0.5, len = h })
	-- drumstick thigh: thick at the hip, muscled down to the knee
	B:mlimb({ x, h + w * 0.55, z + w * 0.2 }, knee, w * 2.2, { col = "primary", mat = mat, bone = "Hip#", pri = 1.2, role = "limb", name = "Thigh#", mesh = "s_drumstick", depth = w * 2.6 }, 0.22)
	if detail == 1 then
		B:mlimb(knee, { foot[1], w * 0.3, foot[3] - w * 0.3 }, w * 0.95, { col = "primary", mat = mat, bone = "Knee#", pri = 1.3, role = "limb", name = "Shin#" }, 0.18)
		return
	end
	B:mlimb(knee, ankle, w * 1.0, { col = "primary", mat = mat, bone = "Knee#", pri = 1.3, role = "limb", name = "Shin#" }, 0.18)
	B:mlimb(ankle, { foot[1], w * 0.32, foot[3] }, w * 0.72, { col = "primary", mat = mat, bone = "Knee#", pri = 1.35, role = "limb", name = "Meta#" }, 0.16)
	local f = w * 3.4
	local toeY = f * 0.11
	local cr, cl = B:mell(f * 0.3, f * 0.22, f, at(foot[1], toeY, foot[3] - f * 0.38), { col = "primary", mat = mat, bone = "Knee#", pri = 1.6, role = "foot", name = "Toe#", mesh = "s_bird_foot_talon" })
	local mem = { {}, {} }
	if detail >= 3 then
		for _, a in { 34, -34 } do
			local ta = rad(a)
			local r, l = B:mlimb({ foot[1], toeY, foot[3] - f * 0.1 }, { foot[1] + sin(ta) * f * 0.78, toeY * 0.8, foot[3] - f * 0.12 - cos(ta) * f * 0.7 }, f * 0.2,
				{ col = "primary", mat = mat, bone = "Knee#", pri = 3.1, role = "foot", name = "SideToe#", depth = f * 0.17, mesh = false }, 0.08)
			table.insert(mem[1], r)
			table.insert(mem[2], l)
		end
	end
	B:sculpt(cr, "s_bird_foot_talon", mem[1])
	B:sculpt(cl, "s_bird_foot_talon", mem[2])
	if P.sickle and detail >= 2 then
		-- the raised killing claw on the second toe
		B:mlimb({ foot[1] - f * 0.12, toeY * 1.6, foot[3] - f * 0.05 }, { foot[1] - f * 0.2, toeY * 3.2, foot[3] - f * 0.42 }, f * 0.12,
			{ col = C.claw, mat = "hard", bone = "Knee#", pri = 2.6, role = "horn", name = "Sickle#", trail = true }, 0.05)
	end
end

local function theropod(B: any, ctx: any, kind: string, id: string)
	local t = ctx.traits
	local detail = ctx.detail
	local P = table.clone(THEROPOD[kind] or THEROPOD.carnosaur)
	for k, v in DWORD[id] or {} do
		P[k] = v
	end
	for w, v in DWORD do
		if P ~= nil and string.find(id, "%f[%a]" .. w .. "%f[^%a]") and w ~= id then
			for k, vv in v do
				P[k] = vv
			end
		end
	end
	local baby = wordIn(id, "baby") or wordIn(id, "hatchling")
	if t.spikes and kind == "carnosaur" then
		P.spikes = true
	end
	local rng = B.rng
	local bulk = (0.9 + t.durability * 0.04) * rng:jitter(1, 0.05)
	local L, H, W = P.body[1] * bulk, P.body[2] * bulk, P.body[3] * bulk
	if baby then
		L, H, W = L * 0.8, H * 0.9, W * 0.9
		P.head *= 1.35
		P.tail *= 0.7
		P.leg *= 0.75
		P.feathers = P.feathers or (string.find(id, "rex") ~= nil)
	end
	local mat = if P.feathers then "fur" else "scale"
	if t.robot or t.mechanical then
		mat = "metal"
	end
	local legLen = P.leg * bulk
	local pitch = rad(P.pitch or 8)
	local hipY = legLen + H * 0.18
	local BF = at(0, hipY + H * 0.12, -L * 0.12, pitch, 0, 0)
	local function bp(x: number, y: number, z: number): { number }
		local a, b, c = Geom.point(BF, x, y, z)
		return { a, b, c }
	end
	B.boneIndex.Body.pos = { 0, hipY, 0 }
	B:ell(W, H, L, BF, { col = "primary", mat = mat, pri = 1, role = "body", name = "Torso", mesh = "s_theropod_body" })
	if detail >= 2 then
		B:ell(W * 0.72, H * 0.55, L * 0.72, Geom.offset(BF, 0, -H * 0.24, -L * 0.1), { col = "belly", mat = mat, pri = 2.2, role = "detail", name = "Belly", mesh = "s_bird_breast" })
	end
	dinoLegs(B, P, { W * 0.36, legLen, L * 0.04 }, detail, mat)

	-- neck: rises from the chest in a curve, head carried forward and level
	local neckBase = bp(0, H * 0.22, -L * 0.42)
	local up = rad(P.neckUp)
	local nl = P.neck * bulk
	local s = P.head * bulk
	local top = { 0, neckBase[2] + cos(up) * nl, neckBase[3] - sin(up) * nl }
	B:bone("Neck", "Body", neckBase[1], neckBase[2], neckBase[3])
	B:setRig("neck", "Neck")
	if detail >= 1 then
		local nw = H * (if kind == "tyrant" then 0.62 elseif kind == "mimic" or kind == "therizino" then 0.32 else 0.48)
		B:limb(neckBase, top, nw, { col = "primary", mat = mat, bone = "Neck", pri = 1.25, role = "body", name = "Neck", mesh = if P.feathers then "s_bird_neck" else "s_body_seg" }, 0.35)
	end
	B:bone("Head", "Neck", top[1], top[2], top[3])
	B:setRig("head", "Head")
	local info
	local bigEyes = P.bigEyes or t.bigEyes
	if P.beak then
		info = Heads.bird(B, { p = { top[1], top[2] - s * 0.1, top[3] }, s = s, eyes = if bigEyes then "cute" else nil }, t)
		if P.crest == "casque" and detail >= 1 then
			B:ell(s * 0.12, s * 0.75, s * 0.8, at(0, info.top[2] + s * 0.18, info.c[3] - s * 0.18, rad(-15), 0, 0), { col = "secondary", mat = "skin", bone = "Head", pri = 1.5, role = "crest", name = "Casque", mesh = "s_crest_sail" })
		end
	else
		info = Heads.reptile(B, { p = { top[1], top[2] - s * 0.12, top[3] + s * 0.05 }, s = s, eyeScale = if bigEyes then 1.5 else 1 }, t)
		-- the deep theropod skull (antorbital hollows, brow bosses, lip line) instead of the lizard head
		for _, p in B.parts do
			if p.name == "Head" and p.bone == "Head" and p.mesh == "s_head_reptile" then
				p.mesh = "s_head_theropod"
			end
		end
		local c = info.c
		if P.snout and detail >= 1 then
			-- long crocodile / gharial snout reaching forward from the skull's snout
			local sl = s * (P.snout - 1) * 1.4 + s * 0.4
			B:ell(s * 0.36, s * 0.26, sl, at(0, c[2] - s * 0.1, c[3] - s * 1.0 - sl * 0.4), { col = "primary", mat = mat, bone = "Head", pri = 1.35, role = "snout", name = "LongSnout" })
			if detail >= 2 then
				B:ell(s * 0.3, s * 0.14, sl * 0.95, at(0, c[2] - s * 0.3, c[3] - s * 0.95 - sl * 0.4), { col = "belly", mat = mat, bone = "Jaw", pri = 2.0, role = "jaw", name = "LongJaw" })
			end
		end
		local hz = P.horns
		if hz == "bull" and detail >= 1 then
			-- carnotaurus: thick horns jutting sideways over the eyes
			B:mlimb({ s * 0.2, c[2] + s * 0.26, c[3] + s * 0.02 }, { s * 0.55, c[2] + s * 0.38, c[3] - s * 0.02 }, s * 0.2, { col = "horn", mat = "hard", bone = "Head", pri = 1.5, role = "horn", name = "Horn#", trail = true }, 0.1)
		elseif hz == "brow" and detail >= 2 then
			B:mlimb({ s * 0.2, c[2] + s * 0.28, c[3] - s * 0.12 }, { s * 0.24, c[2] + s * 0.46, c[3] - s * 0.18 }, s * 0.14, { col = "horn", mat = "hard", bone = "Head", pri = 2.3, role = "horn", name = "BrowHorn#", trail = true }, 0.1)
		elseif hz == "nose" and detail >= 1 then
			B:limb({ 0, c[2] + s * 0.15, c[3] - s * 0.85 }, { 0, c[2] + s * 0.5, c[3] - s * 0.92 }, s * 0.18, { col = "horn", mat = "hard", bone = "Head", pri = 1.8, role = "horn", name = "NoseHorn", trail = true }, 0.1)
		elseif hz == "bump" and detail >= 1 then
			B:ell(s * 0.24, s * 0.2, s * 0.3, at(0, c[2] + s * 0.36, c[3] - s * 0.05), { col = "horn", mat = "hard", bone = "Head", pri = 1.9, role = "horn", name = "Bump" })
		elseif hz == "crown" and detail >= 1 then
			B:ell(s * 0.3, s * 0.18, s * 0.36, at(0, c[2] + s * 0.36, c[3] - s * 0.1), { col = "horn", mat = "hard", bone = "Head", pri = 1.9, role = "horn", name = "Crown" })
			if detail >= 2 then
				B:mball(s * 0.16, at(s * 0.16, c[2] + s * 0.38, c[3] + s * 0.08), { col = "horn", mat = "hard", bone = "Head", pri = 2.6, role = "horn", name = "CrownKnob#" })
			end
		elseif hz == "rugose" and detail >= 2 then
			for i = 1, 3 do
				B:ball(s * 0.14, at(0, c[2] + s * (0.36 - i * 0.04), c[3] - s * (0.1 + i * 0.22)), { col = "darker", mat = "hard", bone = "Head", pri = 2.6 + i * 0.1, role = "horn", name = "Rugose" })
			end
		end
		local cr = P.crest
		local k = P.crestK or 1
		if cr == "twin" and detail >= 1 then
			-- dilophosaurus: two thin arched crests along the top of the skull
			B:mell(s * 0.06, s * 0.42 * k, s * 0.95, at(s * 0.13, c[2] + s * 0.36, c[3] - s * 0.4, rad(-6), 0, 0), { col = "secondary", mat = "skin", bone = "Head", pri = 1.5, role = "crest", name = "Crest#", mesh = "s_crest_sail" })
		elseif cr == "single" and detail >= 1 then
			B:ell(s * 0.07, s * 0.5 * k, s * 1.1, at(0, c[2] + s * 0.38, c[3] - s * 0.45, rad(-6), 0, 0), { col = "secondary", mat = "skin", bone = "Head", pri = 1.5, role = "crest", name = "Crest", mesh = "s_crest_sail" })
		elseif cr == "transverse" and detail >= 1 then
			-- cryolophosaurus: a crest across the skull like a swept-up pompadour, ridged
			B:ell(s * 0.7, s * 0.4, s * 0.08, at(0, c[2] + s * 0.42, c[3] - s * 0.05, rad(-12), 0, 0), { col = "secondary", mat = "skin", bone = "Head", pri = 1.5, role = "crest", name = "Crest" })
		end
	end

	-- arms
	local sh = bp(W * 0.36, -H * 0.05, -L * 0.3)
	local hand = P.hand
	local armLen = P.arms * bulk
	if hand == "tiny" then
		Parts.armPair(B, { x = sh[1], y = sh[2], z = sh[3], len = armLen, w = 0.15 * bulk, hand = "claw", out = 0.08, fwd = 0.35, fwd2 = 0.3, pri = 2.0, mat = mat })
	elseif hand == "feather" then
		Parts.armPair(B, { x = sh[1], y = sh[2], z = sh[3], len = armLen, w = 0.17 * bulk, hand = "claw", out = 0.15, fwd = 0.1, fwd2 = 0.45, pri = 1.5, mat = mat })
		if detail >= 2 then
			-- wing-like fans of long feathers trailing from the forearms
			local ex, ey, ez = sh[1] + armLen * 0.15, sh[2] - armLen * 0.5, sh[3] - armLen * 0.1
			B:mell(armLen * 0.12, armLen * 0.55, armLen * 0.95, at(ex + armLen * 0.05, ey - armLen * 0.08, ez + armLen * 0.28, rad(20), rad(-8), 0),
				{ col = "secondary", mat = "fur", bone = "Fore#", pri = 1.7, role = "wing", name = "ArmFeathers#", mesh = "s_wing_folded", meshL = "s_wing_folded_l" })
		end
	elseif hand == "scythe" then
		local hp = Parts.armPair(B, { x = sh[1], y = sh[2], z = sh[3], len = armLen, w = 0.2 * bulk, hand = "claw", out = 0.18, fwd = 0.22, fwd2 = 0.1, pri = 1.45, mat = mat })
		if detail >= 2 then
			for i = 1, (if detail >= 3 then 3 else 2) do
				local o = (i - 2) * 0.12
				B:mlimb({ hp[1] + o * armLen * 0.3, hp[2] - 0.05, hp[3] - 0.05 }, { hp[1] + o * armLen * 0.45, hp[2] - armLen * 0.55, hp[3] - armLen * 0.38 }, armLen * 0.07,
					{ col = C.claw, mat = "hard", bone = "Fore#", pri = 2.0 + i * 0.2, role = "horn", name = "Scythe" .. i .. "#", trail = i == 2 }, 0.05)
			end
		end
	else
		local hp = Parts.armPair(B, { x = sh[1], y = sh[2], z = sh[3], len = armLen, w = 0.2 * bulk, hand = "claw", out = 0.12, fwd = 0.25, fwd2 = 0.3, pri = 1.6, mat = mat })
		if hand == "thumb" and detail >= 2 then
			B:mlimb({ hp[1] - 0.05, hp[2], hp[3] }, { hp[1] - 0.12, hp[2] - armLen * 0.3, hp[3] - armLen * 0.3 }, armLen * 0.1,
				{ col = C.claw, mat = "hard", bone = "Fore#", pri = 2.4, role = "horn", name = "ThumbClaw#", trail = true }, 0.05)
		end
	end
	if P.wings and detail >= 2 then
		-- archaeopteryx / microraptor: proper feathered wings
		Parts.wings(B, { x = sh[1], y = sh[2] + H * 0.25, z = sh[3], span = L * 1.1, kind = "feather", feathers = 2, pri = 1.6 })
	elseif P.batwings and detail >= 1 then
		Parts.wings(B, { x = sh[1], y = sh[2] + H * 0.2, z = sh[3], span = L * 1.2, kind = "bat", pri = 1.6 })
	end

	-- tail: the counter-weight, straight out behind and slightly drooping (stiff on raptors)
	local tb = bp(0, H * 0.12, L * 0.42)
	local tailLen = P.tail * bulk
	local _, tip = Parts.tail(B, { start = tb, dir = { 0, -0.12, 1 }, len = tailLen, w = H * (P.tailW or 0.72), segs = if detail <= 1 then 1 else 3, droop = if P.sickle then 0.05 else -0.25,
		kind = if P.spikes then "spiked" else "plain", taper = if P.sickle then 0.7 else 0.6, mat = mat, banded = P.banded, col = "primary" })
	if P.feathers and detail >= 2 and kind ~= "mimic" then
		-- feather fan at the end of the tail
		local last = "Tail" .. (if detail <= 1 then 1 else 3)
		B:ell(H * 0.75, H * 0.08, tailLen * 0.4, at(tip[1], tip[2], tip[3] - tailLen * 0.12, rad(4), 0, 0), { col = "secondary", mat = "fur", bone = last, pri = 2.0, role = "tail", name = "TailFan", mesh = "s_bird_tail" })
	end
	if P.feathers and detail >= 2 then
		-- downy ruff over the shoulders
		B:ell(W * 1.0, H * 0.65, L * 0.35, Geom.offset(BF, 0, H * 0.15, -L * 0.36), { col = "secondary", mat = "fur", pri = 2.6, role = "detail", name = "Ruff", mesh = "s_bird_fluff" })
	end

	-- back sail / ridge / hump
	if (P.sail or 0) > 0 and detail >= 1 then
		local sl = L * 1.05
		local sh2 = H * P.sail * 0.42
		local sc = bp(0, H * 0.38 + sh2 * 0.45, -L * 0.02)
		B:ell(W * 0.07, sh2 * 1.7, sl, at(sc[1], sc[2], sc[3], pitch, 0, 0), { col = "secondary", mat = "skin", pri = 1.3, role = "fin", name = "Sail", mesh = "s_crest_sail" })
	elseif P.hump and detail >= 1 then
		local hc = bp(0, H * 0.5, L * 0.18)
		B:ell(W * 0.1, H * 0.7, L * 0.4, at(hc[1], hc[2], hc[3], pitch, 0, 0), { col = "secondary", mat = "skin", pri = 1.6, role = "fin", name = "Hump", mesh = "s_crest_sail" })
	end
	if (P.ridge or P.spikes) and detail >= 2 then
		local pts = {}
		for i = 0, 2 do
			local p = bp(0, H * 0.46, -L * 0.28 + i * L * 0.26)
			table.insert(pts, { p[1], p[2] - H * 0.05, p[3], 1 - i * 0.12 })
		end
		Parts.spikeRow(B, { points = pts, h = H * 0.32, pri = 2.8, col = "secondary" })
	end
	if t.fiery or t.element == "Fire" then
		B:emit("embers", "Torso")
	end
	B:socket("core", at(0, hipY, -L * 0.1), "Body")
	B:setRig("gait", if kind == "tyrant" or kind == "spino" or (kind == "carnosaur" and L > 2.4) then "heavy" else "biped")
end

-- ============================================================================================ primates
-- leg = hip height, torso = { w, h, d }, lean (deg), arms (len; 0 = to the ground), armW, head, muzzle (length),
-- ears (scale), eyeScale, tail (len), tailKind, face (colour)
local PRIMATE_P: { [string]: any } = {
	ape = { leg = 1.0, torso = { 1.85, 2.05, 1.5 }, lean = 30, arms = 0, armW = 0.44, head = 1.05, muzzle = 0.9, ears = 0.28, eyeScale = 1, tail = 0,
		face = C.darkSkin, torsoMesh = "s_ape_torso" },
	monkey = { leg = 0.95, torso = { 1.2, 1.55, 1.0 }, lean = 18, arms = 1.45, armW = 0.27, head = 1.0, muzzle = 0.6, ears = 0.32, eyeScale = 1.1, tail = 2.6,
		tailKind = "curl", face = "belly" },
	baboon = { leg = 1.0, torso = { 1.45, 1.8, 1.25 }, lean = 52, arms = 0, armW = 0.34, head = 1.0, muzzle = 1.5, ears = 0.22, eyeScale = 0.9, tail = 1.3,
		tailKind = "arch", face = C.darkSkin, torsoMesh = "s_ape_torso" },
	prosimian = { leg = 0.75, torso = { 1.1, 1.4, 1.0 }, lean = 12, arms = 1.0, armW = 0.22, head = 1.15, muzzle = 0.4, ears = 0.6, eyeScale = 1.8, tail = 2.6,
		tailKind = "bushy", face = "belly", earKind = "big" },
}

local PWORD: { [string]: any } = {
	gorilla = { torso = { 2.1, 2.15, 1.65 }, ears = 0.2, crest = true, back = "silver" },
	["mountain gorilla"] = { torso = { 2.1, 2.15, 1.65 }, ears = 0.2, crest = true, shaggy = true },
	["baby gorilla"] = { ears = 0.22 },
	chimpanzee = { ears = 0.5, face = { 0.62, 0.5, 0.42 } },
	chimp = { ears = 0.5, face = { 0.62, 0.5, 0.42 } },
	["baby chimp"] = { ears = 0.56, face = { 0.75, 0.6, 0.5 } },
	bonobo = { ears = 0.42, torso = { 1.55, 1.95, 1.3 }, parted = true, face = C.black },
	orangutan = { shaggy = true, flanges = true, face = { 0.38, 0.3, 0.28 }, ears = 0.15, arms = 0, armW = 0.38, torso = { 1.9, 2.0, 1.6 } },
	["baby orangutan"] = { shaggy = true, face = { 0.55, 0.42, 0.38 }, ears = 0.15 },
	gibbon = { torso = { 1.15, 1.55, 0.95 }, lean = 8, arms = 2.6, armW = 0.22, leg = 1.15, face = C.black, ring = true, ears = 0.15, raised = true },
	siamang = { torso = { 1.2, 1.6, 1.0 }, lean = 8, arms = 2.6, armW = 0.24, leg = 1.15, face = C.black, sac = true, ears = 0.15, raised = true },
	yeti = { shaggy = true, face = { 0.62, 0.72, 0.8 } },
	mandrill = { face = C.red, stripes = C.blue, beard = C.gold, tail = 0.4 },
	gelada = { face = C.pinkSkin, mane = true, chest = C.red, muzzle = 1.3, tail = 1.8, tailKind = "tuft" },
	baboon = { face = { 0.3, 0.26, 0.26 }, mane = true },
	macaque = { face = C.pinkSkin, tail = 0.7, tailKind = "arch" },
	["snow monkey"] = { face = C.red, tail = 0.4, tailKind = "arch", shaggy = true },
	langur = { face = C.black, tail = 2.8, tailKind = "hang" },
	capuchin = { face = C.cream, cap = true },
	colobus = { face = C.black, cape = true, tailKind = "tuft", tail = 2.6 },
	marmoset = { tufts = true, face = C.cream, tailKind = "banded" },
	tamarin = { mane = true, face = C.black },
	saki = { face = C.white, shaggy = true },
	uakari = { face = C.red, tail = 0.6, tailKind = "arch" },
	titi = { tailKind = "hang", shaggy = true },
	["howler monkey"] = { face = C.black, throat = true, shaggy = true },
	["proboscis monkey"] = { nose = true, belly = true, face = C.pinkSkin },
	["golden snub-nosed monkey"] = { face = C.blue, snub = true, shaggy = true },
	["spider monkey"] = { arms = 2.0, leg = 1.2, armW = 0.22, tail = 3.2, face = C.black },
	["squirrel monkey"] = { face = C.white, mask = true },
	["night monkey"] = { eyeScale = 1.9, muzzle = 0.4 },
	["baby monkey"] = {},
	galago = { ears = 0.7, tailKind = "bushy" },
	tarsier = { ears = 0.62, eyeScale = 2.2, muzzle = 0.3, tail = 2.6, tailKind = "thin", leg = 0.95 },
	loris = { ears = 0.18, eyeScale = 1.9, tail = 0, mask = true },
	lemur = { ears = 0.42, earKind = "pointy", muzzle = 1.1, eyeScale = 1.35, tailKind = "banded", tail = 3.0, face = C.black },
	["aye-aye"] = { ears = 0.85, eyeScale = 1.7, shaggy = true, tailKind = "bushy", face = C.darkSkin },
}

-- Primate head: cranium + skin-coloured face mask (eyes, brow ridge, muzzle), ears. Returns head info.
local function primateHead(B: any, P: any, t: any, hc: { number }, s: number, detail: number): any
	local bone = "Head"
	local face = P.face
	local cr = { s * 0.5, s * 0.48, s * 0.48 }
	local crMesh = "s_head_round"
	B:ell(cr[1] * 2, cr[2] * 2, cr[3] * 2, at(hc[1], hc[2], hc[3]), { col = "primary", mat = "fur", bone = bone, pri = 1.1, role = "head", name = "Head", mesh = crMesh })
	-- face mask: the bare face, set into the front of the skull
	local mc = { hc[1], hc[2] - s * 0.04, hc[3] - s * 0.27 }
	local mr = { s * 0.37, s * 0.36, s * 0.24 }
	local mask = B:ell(mr[1] * 2, mr[2] * 2, mr[3] * 2, at(mc[1], mc[2], mc[3]), { col = face, mat = "skin", bone = bone, pri = 1.12, role = "head", name = "FaceMask" })
	local members = {}
	local mz = P.muzzle
	-- muzzle below the eyes (dog-like on baboons)
	local mu = { hc[1], mc[2] - s * (if mz > 1 then 0.22 else 0.17), mc[3] - mr[3] * 0.75 - s * 0.12 * mz }
	local muR = { s * (if mz > 1 then 0.22 else 0.25), s * (if mz > 1 then 0.2 else 0.17), s * (0.12 + 0.12 * mz) }
	local muzzle = B:ell(muR[1] * 2, muR[2] * 2, muR[3] * 2, at(mu[1], mu[2], mu[3]), { col = P.muzzleCol or face, mat = "skin", bone = bone, pri = 1.2, role = "snout", name = "Muzzle" })
	if mz <= 1.0 then
		table.insert(members, muzzle)
	end
	if detail >= 2 and P.lean > 15 then
		-- heavy brow ridge (apes, baboons)
		local br = B:ell(s * 0.66, s * 0.13, s * 0.22, at(mc[1], mc[2] + mr[2] * 0.62, mc[3] - mr[3] * 0.62, rad(-12), 0, 0), { col = face, mat = "skin", bone = bone, pri = 2.4, role = "detail", name = "BrowRidge" })
		table.insert(members, br)
	end
	B:sculpt(mask, if mz <= 1.0 then "s_primate_face" else "s_primate_mask", members)
	if detail >= 2 then
		-- nostrils on the muzzle tip
		local tip = { mu[1], mu[2] + muR[2] * 0.4, mu[3] - muR[3] * 0.82 }
		B:mell(s * 0.07, s * 0.05, s * 0.05, at(s * 0.06, tip[2], tip[3]), { col = C.black, mat = "skin", bone = bone, pri = 3.0, role = "nose", name = "Nostril#", noCore = true })
	end
	if P.stripes and detail >= 2 then
		-- mandrill: ridged blue cheeks either side of a red nose
		B:mell(s * 0.12, s * 0.2, muR[3] * 1.7, at(muR[1] * 0.55, mu[2] + s * 0.02, mu[3] + s * 0.02), { col = P.stripes, mat = "skin", bone = bone, pri = 2.2, role = "detail", name = "CheekRidge#" })
	end
	if P.nose and detail >= 1 then
		B:ell(s * 0.24, s * 0.34, s * 0.2, at(mu[1], mu[2] + s * 0.02, mu[3] - muR[3] * 0.9), { col = C.pinkSkin, mat = "skin", bone = bone, pri = 1.6, role = "nose", name = "BigNose" })
	end
	local kind = Heads.eyeKind(t, {})
	local m = (B.ctx.result and B.ctx.result.mood) or "Neutral"
	Face.build(B, {
		face = { kind = "ellipsoid", c = mc, r = mr }, mouthFace = { kind = "ellipsoid", c = mu, r = muR },
		bone = bone, mood = m, detail = detail, kind = kind,
		spacing = s * 0.15 * math.min(P.eyeScale, 1.6), y = s * 0.08, d = s * 0.2 * P.eyeScale,
		mouthY = -muR[2] * 0.35, mouthW = s * 0.26, noMouth = m == "Neutral", lidCol = face, browCol = "dark",
	})
	B:socket("mouth", at(mu[1], mu[2] - muR[2] * 0.5, mu[3] - muR[3] * 0.8), bone)
	-- ears on the sides of the skull
	local ek = P.earKind or "round"
	if ek == "pointy" then
		Parts.ears(B, { bone = bone, x = cr[1] * 0.62, y = hc[2] + cr[2] * 0.6, z = hc[3] + cr[3] * 0.1, s = s * P.ears * 1.4, kind = "pointy", pri = 1.8 })
	else
		local es = s * P.ears
		B:mell(es * 0.32, es * 1.0, es * 0.85, at(cr[1] * 0.98, hc[2] + s * 0.02 + (if ek == "big" then es * 0.25 else 0), hc[3] + s * 0.02, 0, rad(-25), rad(-10)),
			{ col = face, mat = "skin", bone = bone, pri = if P.ears > 0.55 then 1.25 elseif P.ears > 0.4 then 1.5 else 2.2, role = "ear", name = "Ear#" })
	end
	local info = { c = hc, r = cr, s = s, top = { hc[1], hc[2] + cr[2] * 0.95, hc[3] } }
	if P.crest and detail >= 2 then
		B:ell(s * 0.3, s * 0.4, s * 0.62, at(hc[1], hc[2] + cr[2] * 0.72, hc[3] + s * 0.05), { col = "primary", mat = "fur", bone = bone, pri = 2.6, role = "detail", name = "SagittalCrest" })
	end
	if P.flanges and detail >= 1 then
		-- orangutan cheek pads: broad discs framing the face
		B:ell(s * 1.7, s * 1.05, s * 0.2, at(hc[1], hc[2] - s * 0.05, hc[3] - s * 0.12), { col = face, mat = "skin", bone = bone, pri = 1.55, role = "detail", name = "Flanges" })
	end
	if P.cap and detail >= 2 then
		B:ell(s * 0.82, s * 0.36, s * 0.8, at(hc[1], hc[2] + cr[2] * 0.68, hc[3] + s * 0.02), { col = "dark", mat = "fur", bone = bone, pri = 2.5, role = "detail", name = "Cap" })
	end
	if P.tufts and detail >= 2 then
		B:mell(s * 0.42, s * 0.3, s * 0.12, at(cr[1] * 1.15, hc[2] + s * 0.08, hc[3] + s * 0.05, 0, rad(-25), 0), { col = C.white, mat = "fur", bone = bone, pri = 2.4, role = "ear", name = "Tuft#", mesh = "s_bird_fluff" })
	end
	if P.beard and detail >= 2 then
		B:ell(s * 0.5, s * 0.36, s * 0.3, at(mu[1], mu[2] - muR[2] * 1.1, mu[3] + muR[3] * 0.5), { col = P.beard, mat = "fur", bone = bone, pri = 2.6, role = "beard", name = "Beard", mesh = "s_bird_fluff" })
	end
	if P.throat and detail >= 2 then
		B:ell(s * 0.55, s * 0.5, s * 0.45, at(hc[1], hc[2] - s * 0.5, hc[3] - s * 0.15), { col = "primary", mat = "fur", bone = bone, pri = 2.3, role = "detail", name = "Throat", mesh = "s_bird_fluff" })
	end
	if P.sac and detail >= 2 then
		B:ell(s * 0.6, s * 0.55, s * 0.5, at(hc[1], hc[2] - s * 0.55, hc[3] - s * 0.18), { col = C.greySkin, mat = "skin", bone = bone, pri = 2.3, role = "detail", name = "ThroatSac" })
	end
	return info
end

local function primate(B: any, ctx: any, kind: string, id: string)
	local t = ctx.traits
	local detail = ctx.detail
	local P = table.clone(PRIMATE_P[kind])
	local touched = PWORD[id]
	if touched == nil then
		for w, v in PWORD do
			if string.find(id, "%f[%a]" .. w .. "%f[^%a]") then
				touched = v
			end
		end
	end
	for k, v in touched or {} do
		P[k] = v
	end
	local baby = wordIn(id, "baby")
	local rng = B.rng
	local bulk = (0.9 + t.durability * 0.03) * rng:jitter(1, 0.05)
	local tw, th, td = P.torso[1] * bulk, P.torso[2] * bulk, P.torso[3] * bulk
	local s = P.head * bulk
	if baby then
		tw, th, td = tw * 0.82, th * 0.78, td * 0.82
		s *= 1.3
		P.eyeScale *= 1.2
	end
	local hipY = P.leg * bulk
	local lean = rad(P.lean)
	B.boneIndex.Body.pos = { 0, hipY, 0 }
	B:bone("Chest", "Body", 0, hipY + th * 0.2, 0)
	B:setRig("chest", "Chest")
	-- torso hinged at the hips, leaning forward by `lean`
	local TF = Geom.mul(at(0, hipY + th * 0.05, 0, -lean, 0, 0), at(0, th * 0.42, 0))
	local function tp(x: number, y: number, z: number): { number }
		local a, b, c = Geom.point(TF, x, y, z)
		return { a, b, c }
	end
	B:ell(tw, th, td, TF, { col = "primary", mat = "fur", bone = "Chest", pri = 1, role = "body", name = "Torso", mesh = P.torsoMesh or "s_torso" })
	if detail >= 2 then
		B:ell(tw * 0.62, th * 0.6, td * 0.5, Geom.offset(TF, 0, -th * 0.08, -td * 0.3), { col = if P.chest then P.chest elseif P.belly then C.pinkSkin else "belly", mat = "fur", bone = "Chest", pri = 2.2, role = "detail", name = "Belly" })
	end
	-- legs: short, bowed, hand-like feet
	Parts.legPair(B, { tag = "", x = tw * 0.27, y = hipY + 0.1, z = 0.05, w = (if kind == "ape" then 0.42 else 0.3) * bulk, kind = "paw", thigh = 1.35, phase = 0, col = "primary", mat = "fur", footZ = -0.1 })
	-- shoulders and arms: knuckle-walkers reach the ground in front of them
	local sh = tp(tw * 0.42, th * 0.36, 0)
	local armLen = P.arms * bulk
	local fwd, fwd2 = 0.18, 0.12
	if P.arms == 0 then
		armLen = (sh[2] - 0.25 * bulk) / 0.96
		fwd, fwd2 = 0.3, 0.12
	end
	Parts.armPair(B, {
		x = sh[1], y = sh[2], z = sh[3], len = armLen, w = P.armW * bulk, hand = "fist", handCol = P.handCol or "dark", out = 0.12, fwd = fwd, fwd2 = fwd2, upper = 1.3, pri = 1.3,
		col = "primary", mat = "fur",
	})
	-- head on the shoulders, chin forward
	local neck = tp(0, th * 0.48, -td * 0.18)
	B:bone("Head", "Chest", neck[1], neck[2], neck[3])
	B:setRig("head", "Head")
	local hc = { 0, neck[2] + s * 0.22, neck[3] - s * 0.22 }
	local info = primateHead(B, P, t, hc, s, detail)
	local _ = info
	-- coat details
	if P.shaggy and detail >= 2 then
		B:ell(tw * 1.08, th * 0.5, td * 1.05, Geom.offset(TF, 0, th * 0.22, 0.02), { col = "primary", mat = "fur", bone = "Chest", pri = 2.5, role = "detail", name = "Shag", mesh = "s_bird_fluff" })
	end
	if P.mane and detail >= 1 then
		B:ell(tw * 1.15, th * 0.55, td * 1.15, Geom.offset(TF, 0, th * 0.3, 0.0), { col = "light", mat = "fur", bone = "Chest", pri = 1.6, role = "detail", name = "Mane", mesh = "s_bird_fluff" })
	end
	if P.cape and detail >= 2 then
		B:ell(tw * 1.1, th * 0.85, td * 0.4, Geom.offset(TF, 0, 0, td * 0.42), { col = C.white, mat = "fur", bone = "Chest", pri = 2.4, role = "detail", name = "Cape", mesh = "s_bird_fluff" })
	end
	if P.back == "silver" and detail >= 2 then
		B:ell(tw * 0.7, th * 0.5, td * 0.4, Geom.offset(TF, 0, th * 0.05, td * 0.36), { col = "secondary", mat = "fur", bone = "Chest", pri = 2.7, role = "detail", name = "Saddle" })
	end
	-- tail
	if (P.tail or 0) > 0 then
		local tk = P.tailKind
		local tb = tp(0, -th * 0.4, td * 0.42)
		local len = P.tail * bulk
		local dir = if tk == "curl" then { 0, 0.15, 1 } elseif tk == "arch" then { 0, 0.6, 1 } elseif tk == "hang" then { 0, -0.6, 1 } else { 0, 0.05, 1 }
		Parts.tail(B, { start = tb, dir = dir, len = len, w = (if tk == "bushy" then 0.32 elseif tk == "banded" then 0.26 else 0.17) * bulk, segs = if detail <= 1 then 1 else 3,
			kind = if tk == "bushy" then "bushy" elseif tk == "tuft" then "tuft" else "plain", curl = if tk == "curl" then 1.6 elseif tk == "hang" then -0.4 else 0.4,
			droop = if tk == "hang" then -0.4 else 0, taper = if tk == "bushy" or tk == "banded" then 0.9 else 0.78, banded = tk == "banded", col = "primary", tuftCol = "light",
			pri = if P.tail > 1.5 then 0.85 else 1.1 })
	end
	B:socket("core", at(0, hipY + th * 0.5, 0), "Chest")
	B:setRig("gait", if P.arms == 0 then "heavy" elseif kind == "prosimian" then "hop" else "biped")
end

-- The t rex signature's base (SigKit.base kind "dino"): the original dino layout its hero sculpt (s_trex.py) was cut
-- on, kept as is so the hero pieces fit.
local function legacyDino(B: any, ctx: any)
	local t = ctx.traits
	local detail = ctx.detail
	local rng = B.rng
	local bulk = (0.9 + t.durability * 0.04) * rng:jitter(1, 0.05)
	local legLen = 1.5 * bulk
	local hipY = legLen + 0.25
	local L = 2.6 * bulk
	local H = 1.35 * bulk
	B.boneIndex.Body.pos = { 0, hipY, 0 }
	-- torso pitched up toward the chest
	B:ell(H * 0.95, H, L, at(0, hipY + 0.15, -L * 0.12, rad(-14), 0, 0), { col = "primary", mat = "scale", pri = 1, role = "body", name = "Torso" })
	if detail >= 2 then
		B:ell(H * 0.7, H * 0.6, L * 0.75, at(0, hipY - H * 0.22, -L * 0.2, rad(-14), 0, 0), { col = "belly", mat = "scale", pri = 2.2, role = "detail", name = "Belly" })
	end
	Parts.legPair(B, { tag = "", x = H * 0.42, y = hipY, z = 0.15, w = 0.42 * bulk, kind = "claw", thigh = 1.7, claws = true, phase = 0 })
	-- neck + big head
	local neckBase = { 0, hipY + H * 0.45, -L * 0.48 }
	local headP = { 0, neckBase[2] + 0.45, neckBase[3] - 0.45 }
	B:bone("Neck", "Body", neckBase[1], neckBase[2], neckBase[3])
	B:setRig("neck", "Neck")
	if detail >= 2 then
		B:limb(neckBase, headP, H * 0.62, { col = "primary", mat = "scale", bone = "Neck", pri = 1.25, role = "body", name = "Neck" }, 0.35)
	end
	B:bone("Head", "Neck", headP[1], headP[2], headP[3])
	B:setRig("head", "Head")
	local headS = 1.35 * bulk * (if t.bigJaw then 1.15 else 1)
	Heads.reptile(B, { p = headP, s = headS }, t)
	-- tiny arms (t rex charm) or raptor claws
	Parts.armPair(B, { x = H * 0.38, y = hipY + H * 0.05, z = -L * 0.42, len = if t.bigJaw then 0.55 else 0.85, w = 0.16 * bulk, hand = "claw", out = 0.1, fwd = 0.35, fwd2 = 0.3, pri = 2.0 })
	Parts.tail(B, { start = { 0, hipY + 0.25, L * 0.32 }, dir = { 0, -0.1, 1 }, len = L * 1.1, w = H * 0.7, segs = if detail <= 1 then 1 else 3, droop = -0.15, kind = if t.spikes then "spiked" else "plain", taper = 0.62 })
	if detail >= 2 and (t.spikes or t.mythical) then
		Parts.spikeRow(B, { points = { { 0, hipY + H * 0.55, -L * 0.25, 1 }, { 0, hipY + H * 0.5, 0, 1.1 }, { 0, hipY + H * 0.4, L * 0.25, 0.9 } }, h = H * 0.38, pri = 2.8 })
	end
	B:socket("core", at(0, hipY, -L * 0.1), "Body")
	B:setRig("gait", "heavy")
end

return function(B: any, ctx: any)
	local t = ctx.traits
	local detail = ctx.detail
	local kind = kindOf(ctx)
	local id = string.lower(ctx.result.id)
	if kind == "dino" then
		return legacyDino(B, ctx)
	end
	if DINO[kind] then
		return theropod(B, ctx, kind, id)
	end
	if PRIMATE[kind] then
		return primate(B, ctx, kind, id)
	end
	local rng = B.rng
	local bulk = (0.9 + t.durability * 0.04) * rng:jitter(1, 0.05)

	-- upright kinds
	local ape = kind == "ape"
	local hopper = kind == "hopper"
	local legLen = (if ape then 1.1 elseif hopper then 1.3 else 1.25) * bulk
	local hipY = legLen
	local torsoH = (if ape then 2.0 else 1.9) * bulk
	local torsoW = (if ape then 1.8 elseif hopper then 1.2 else 1.75) * bulk
	B.boneIndex.Body.pos = { 0, hipY, 0 }
	B:bone("Chest", "Body", 0, hipY + 0.3, 0)
	B:setRig("chest", "Chest")
	local lean = if ape then rad(-16) else rad(-6)
	B:ell(torsoW, torsoH, torsoW * 0.8, at(0, hipY + torsoH * 0.48, -torsoH * 0.08, lean, 0, 0), { col = "primary", mat = "fur", bone = "Chest", pri = 1, role = "body", name = "Torso" })
	if detail >= 2 then
		B:ell(torsoW * 0.72, torsoH * 0.62, torsoW * 0.5, at(0, hipY + torsoH * 0.4, -torsoW * 0.3, lean, 0, 0), { col = "belly", mat = "fur", bone = "Chest", pri = 2.2, role = "detail", name = "Belly" })
	end
	Parts.legPair(B, {
		tag = "", x = torsoW * 0.3, y = hipY + 0.1, z = 0.05, w = 0.45 * bulk, kind = "paw", thigh = 1.4, claws = t.claws, phase = 0,
		footZ = if hopper then -0.35 else 0,
	})
	if hopper then
		B:mell(0.5 * bulk, 0.35 * bulk, 1.6 * bulk, at(torsoW * 0.3, 0.18, -0.45), { col = "primary", mat = "fur", bone = "Knee#", pri = 1.5, role = "foot", name = "BigFoot#" })
	end
	local shoulderY = hipY + torsoH * 0.85
	local armLen = (if ape then 2.1 elseif hopper then 0.9 else 1.9) * bulk
	local hand = Parts.armPair(B, {
		x = torsoW * 0.5, y = shoulderY, z = -torsoH * 0.15, len = armLen, w = (if hopper then 0.22 else 0.42) * bulk,
		hand = if t.claws then "claw" else "fist", handCol = if ape then "dark" else "primary", out = 0.2, fwd = 0.18, upper = 1.25, pri = 1.3,
	})
	local neckTop = { 0, hipY + torsoH * 0.92, -torsoH * 0.28 }
	B:bone("Head", "Chest", neckTop[1], neckTop[2], neckTop[3])
	B:setRig("head", "Head")
	local headS = (if hopper then 1.0 else 1.05) * bulk
	local info = Heads.mammal(B, { p = { neckTop[1], neckTop[2] - headS * 0.15, neckTop[3] }, s = headS, muzzleCol = if ape then "secondary" else "belly", long = if hopper then 1.3 else 0.85 }, t)
	if hopper or t.longEars then
		Parts.ears(B, { bone = "Head", x = info.earX, y = info.earY, z = info.earZ, s = headS * 0.45, kind = "long" })
	elseif t.horns then
		Parts.horns(B, { bone = "Head", x = headS * 0.28, y = info.top[2] - headS * 0.1, z = info.top[3], len = headS * 0.8, w = headS * 0.2, kind = "curved", segs = 2 })
	elseif not ape then
		Parts.ears(B, { bone = "Head", x = info.earX, y = info.earY, z = info.earZ, s = headS * 0.4, kind = "round" })
	end
	if hopper then
		Parts.tail(B, { start = { 0, hipY, torsoW * 0.3 }, dir = { 0, -0.45, 1 }, len = 2.0 * bulk, w = 0.45 * bulk, segs = if detail <= 1 then 1 else 2, kind = "plain", taper = 0.6 })
	end
	if kind == "brute" and (t.club or (t.power or 5) >= 6) then
		Props.held(B, "club", hand, 0.42 * bulk, "ForeR")
	end
	B:socket("core", at(0, hipY + torsoH * 0.5, 0), "Chest")
	B:setRig("gait", if hopper then "hop" elseif ape then "heavy" else "stomp")
end
