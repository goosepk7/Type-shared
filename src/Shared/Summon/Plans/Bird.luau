--!strict
-- Bird: every feathered (and leathery) flyer. The word picks a sub-kind (songbird, corvid, parrot, raptor, vulture,
-- owl, wader, waterfowl, seabird, penguin, auk, fowl, ratite, terror bird, kiwi, hummingbird, kingfisher, toucan,
-- woodpecker, mythic firebird, siren, pterosaur, bat, wyvern) and the sub-kind gives the proportions: body length /
-- depth / posture, neck, head size, beak shape (cone, thin, probe, down-curved, dagger, hook, parrot, duck bill,
-- spoon, pouch, huge), legs (perching, wading, webbed, taloned, ratite), wings (spread feather fan, folded at the
-- flanks, flippers, stubs, bat / pterosaur membrane), tail (fan, long, fork, cocked, train, sickle, ribbons) and
-- crest. A baby ("chick", "duckling", "owlet" ...) is the parent kind as a round fluffball with a big head.
--
-- Sculpts (catalogue/s_gen_bird.py): bird body / fluffball, raptor head, the beak family, folded wing, fanned and
-- forked tails, crest feather, perching and webbed feet; the spread feathered wing is s_wing (Parts.wings).

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Heads = require(script.Parent.Parent.Heads)
local Face = require(script.Parent.Parent.Face)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

-- colours that are not palette keys
local C = {
	darkLeg = { 0.3, 0.27, 0.26 },
	greyLeg = { 0.45, 0.45, 0.47 },
	pinkLeg = { 0.86, 0.6, 0.56 },
	ivory = { 0.92, 0.88, 0.76 },
	black = { 0.13, 0.12, 0.13 },
	red = { 0.82, 0.16, 0.14 },
	bald = { 0.86, 0.5, 0.46 },
	slate = { 0.36, 0.38, 0.42 },
	yellow = { 0.98, 0.8, 0.22 },
	blueNeck = { 0.22, 0.45, 0.85 },
}

-- Beaks, in head units: w, h (depth at the base), l (length), pitch (deg, - = tip down), sculpt piece
local BEAK: { [string]: any } = {
	cone = { 0.42, 0.38, 0.46, -10, "s_beak_cone" },
	thin = { 0.22, 0.2, 0.56, -6, "s_beak_probe" },
	probe = { 0.17, 0.15, 1.55, -10, "s_beak_probe" },
	curve = { 0.2, 0.2, 1.35, -6, "s_beak_curve" },
	bent = { 0.3, 0.34, 1.0, -22, "s_beak_curve" },
	dagger = { 0.27, 0.27, 1.15, -4, "s_beak_dagger" },
	hook = { 0.34, 0.36, 0.62, -12, "s_beak" },
	parrot = { 0.44, 0.62, 0.56, -12, "s_beak_parrot" },
	duck = { 0.52, 0.22, 0.85, -6, "s_beak_duck" },
	spoon = { 0.34, 0.14, 1.45, -6, "s_beak_duck" },
	pouch = { 0.44, 0.5, 1.9, -6, "s_beak_pouch" },
	huge = { 0.5, 0.82, 1.45, -10, "s_beak_huge" },
	shoe = { 0.72, 0.6, 1.0, -8, "s_beak_huge" },
}

-- Sub-kind profiles. body = { length, depth, width } (design units), pitch (deg, + = chest up), leg = hip height,
-- legW = leg thickness, neck = neck length (0: head on the shoulders), neckUp = neck angle from vertical (deg, +
-- forward), head = head size, beak = BEAK key, bl = beak length scale, wings = spread|folded|stub|flipper|bat|none,
-- span, tail = fan|long|fork|cocked|train|sickle|ribbons|plume|short|rudder|none, tl = tail length, feet =
-- perch|web|talon|ratite, mesh = body sculpt.
local BASE = {
	body = { 2.0, 1.35, 1.25 }, pitch = 16, leg = 0.55, legW = 0.13, neck = 0, neckUp = 10, neckW = 1, head = 0.95,
	beak = "thin", bl = 1, wings = "spread", span = 1.4, tail = "fan", tl = 1, feet = "perch", legCol = C.darkLeg,
	beakCol = "beak", mesh = "s_bird_body", eyeD = 0.32, eyeSp = 0.27, headMesh = "s_head_bird",
}

local PROFILE: { [string]: any } = {
	songbird = {},
	finch = { beak = "cone", body = { 1.9, 1.4, 1.35 } },
	corvid = { body = { 2.3, 1.4, 1.3 }, head = 0.9, beak = "dagger", bl = 0.62, beakCol = C.black, tl = 1.25, legCol = C.black, leg = 0.65 },
	pigeon = { body = { 2.1, 1.55, 1.45 }, head = 0.72, beak = "thin", bl = 0.8, beakCol = C.slate, legCol = C.pinkLeg, pitch = 12 },
	parrot = { body = { 1.8, 1.55, 1.35 }, pitch = 52, leg = 0.42, legW = 0.16, head = 1.12, beak = "parrot", beakCol = C.ivory, tail = "long", tl = 1.6,
		legCol = C.greyLeg, wings = "folded", eyeSp = 0.3, breastCol = "light", wingCol = "secondary" },
	raptor = { body = { 2.3, 1.6, 1.5 }, pitch = 38, leg = 0.8, legW = 0.21, head = 0.92, beak = "hook", beakCol = C.slate, feet = "talon", legCol = "beak",
		headMesh = "s_head_raptor", span = 1.7, tl = 1.15, trousers = true, eyeSp = 0.25 },
	vulture = { body = { 2.4, 1.6, 1.55 }, pitch = 22, leg = 0.75, legW = 0.21, neck = 0.85, neckUp = 55, neckW = 0.8, head = 0.72, beak = "hook", bl = 1.15,
		beakCol = C.ivory, feet = "talon", legCol = C.greyLeg, headCol = C.bald, ruff = true, span = 1.8, wings = "folded" },
	owl = { body = { 2.15, 1.65, 1.7 }, pitch = 74, leg = 0.32, legW = 0.2, head = 1.4, headW = 1.15, beak = "hook", bl = 0.55, beakCol = C.slate, tail = "short",
		feet = "talon", legCol = C.slate, mesh = "s_bird_fluff", wings = "folded", owl = true, eyeD = 0.42, eyeSp = 0.2, trousers = true },
	wader = { body = { 1.9, 1.15, 1.0 }, pitch = 10, leg = 2.5, legW = 0.12, neck = 1.6, neckUp = 12, neckW = 0.78, head = 0.66, beak = "dagger", bl = 1.2,
		tail = "short", tl = 0.6, wings = "folded", legCol = C.darkLeg, sCurve = true, breastCol = "light" },
	shorebird = { body = { 1.8, 1.2, 1.1 }, pitch = 8, leg = 1.0, legW = 0.1, neck = 0.25, head = 0.75, beak = "probe", bl = 0.8, tail = "short", tl = 0.6,
		wings = "folded", legCol = C.darkLeg, beakCol = C.black },
	duck = { body = { 2.4, 1.2, 1.45 }, pitch = -2, leg = 0.32, legW = 0.15, hipZ = 0.25, neck = 0.5, neckUp = 5, neckW = 0.85, head = 0.82, beak = "duck",
		tail = "short", tl = 0.7, wings = "folded", feet = "web", legCol = "beak", breastCol = "light" },
	swan = { body = { 2.6, 1.25, 1.5 }, pitch = -2, leg = 0.32, legW = 0.15, hipZ = 0.25, neck = 2.0, neckUp = 4, neckW = 0.55, head = 0.68, beak = "duck", bl = 0.9,
		tail = "short", tl = 0.6, wings = "folded", feet = "web", legCol = C.black, sCurve = true, breastCol = "light" },
	goose = { body = { 2.5, 1.35, 1.5 }, pitch = 4, leg = 0.5, legW = 0.16, hipZ = 0.15, neck = 1.15, neckUp = 8, neckW = 0.6, head = 0.7, beak = "duck", bl = 0.75,
		tail = "short", tl = 0.6, wings = "folded", feet = "web", legCol = "beak", breastCol = "light" },
	seabird = { body = { 2.3, 1.25, 1.15 }, pitch = 8, leg = 0.45, legW = 0.13, neck = 0.25, head = 0.8, beak = "dagger", bl = 0.85, feet = "web", legCol = "beak",
		span = 2.2, tl = 0.85, breastCol = "light" },
	pelican = { body = { 2.5, 1.4, 1.4 }, pitch = 14, leg = 0.5, legW = 0.15, neck = 0.75, neckUp = 25, neckW = 0.65, head = 0.72, beak = "pouch", feet = "web", legCol = "beak",
		wings = "folded", tail = "short", tl = 0.6, breastCol = "light" },
	penguin = { body = { 2.3, 1.5, 1.6 }, pitch = 82, leg = 0.32, legW = 0.17, head = 1.08, beak = "dagger", bl = 0.62, beakCol = C.black, wings = "flipper",
		tail = "short", tl = 0.45, feet = "web", legCol = C.pinkLeg, breastCol = { 0.95, 0.95, 0.93 } },
	auk = { body = { 2.05, 1.55, 1.5 }, pitch = 66, leg = 0.32, legW = 0.15, head = 1.08, beak = "cone", bl = 1.4, wings = "folded", tail = "short", tl = 0.5,
		feet = "web", legCol = "beak" },
	fowl = { body = { 2.0, 1.65, 1.45 }, pitch = 14, leg = 0.75, legW = 0.17, head = 0.72, beak = "cone", bl = 0.85, wings = "folded", tail = "fan", tl = 0.9,
		legCol = "beak", neck = 0.25 },
	ratite = { body = { 2.3, 1.75, 1.7 }, pitch = 8, leg = 2.5, legW = 0.3, neck = 2.1, neckUp = 6, neckW = 0.55, head = 0.55, beak = "duck", bl = 0.7,
		beakCol = C.slate, wings = "stub", tail = "plume", tl = 0.8, feet = "ratite", legCol = C.greyLeg, mesh = "s_bird_fluff", drumstick = true },
	terror = { body = { 2.3, 1.6, 1.4 }, pitch = 16, leg = 2.1, legW = 0.28, neck = 1.0, neckUp = 22, neckW = 0.85, head = 1.15, beak = "huge", bl = 0.95,
		beakCol = C.ivory, wings = "stub", tail = "plume", tl = 0.8, feet = "ratite", legCol = C.greyLeg, headMesh = "s_head_raptor", drumstick = true },
	kiwi = { body = { 2.0, 1.5, 1.55 }, pitch = 0, leg = 0.5, legW = 0.21, head = 0.66, beak = "probe", bl = 1.25, beakCol = C.ivory, wings = "none", tail = "none",
		legCol = C.greyLeg, mesh = "s_bird_fluff", neck = 0.2, neckUp = 60 },
	hummer = { keepSpread = true, body = { 1.6, 1.0, 0.95 }, pitch = 30, leg = 0.3, legW = 0.08, head = 0.78, beak = "probe", bl = 1.35, beakCol = C.black, span = 1.6, tail = "fork",
		tl = 0.8 },
	kingfisher = { body = { 1.65, 1.3, 1.2 }, pitch = 30, leg = 0.32, legW = 0.1, head = 1.15, beak = "dagger", bl = 1.05, beakCol = C.black, tail = "short", tl = 0.8,
		legCol = C.red, wings = "folded" },
	toucan = { body = { 1.9, 1.45, 1.3 }, pitch = 36, leg = 0.45, legW = 0.14, head = 0.95, beak = "huge", bl = 1.25, beakCol = "secondary", tail = "long", tl = 1.2,
		wings = "folded", legCol = C.slate },
	woodpecker = { body = { 2.0, 1.35, 1.2 }, pitch = 55, leg = 0.4, legW = 0.12, head = 0.9, beak = "dagger", bl = 0.75, beakCol = C.slate, tail = "short", tl = 1.0,
		crest = "red", wings = "folded" },
	mythic = { body = { 2.3, 1.6, 1.5 }, pitch = 30, leg = 0.75, legW = 0.19, head = 0.92, beak = "hook", feet = "talon", legCol = "beak", span = 1.9, tail = "ribbons",
		tl = 2.0, crest = "flame", trousers = true },
	siren = { body = { 2.1, 1.6, 1.45 }, pitch = 30, leg = 0.6, legW = 0.17, head = 1.15, beak = "none", tail = "long", tl = 1.5, feet = "talon", legCol = "beak",
		siren = true, span = 1.7 },
	ptero = { body = { 1.9, 0.9, 0.85 }, pitch = 24, leg = 0.85, legW = 0.11, neck = 0.85, neckUp = 35, neckW = 0.6, head = 0.6, beak = "dagger", bl = 3.0,
		beakCol = "secondary", wings = "bat", span = 3.0, tail = "none", feet = "perch", legCol = "primary", ptero = true, crest = "ptero" },
	bat = { body = { 1.35, 1.35, 1.2 }, pitch = 35, leg = 0.32, legW = 0.1, head = 1.15, beak = "none", wings = "bat", span = 2.2, tail = "none", legCol = "dark",
		mesh = "s_bird_fluff", bat = true, earK = 1.3 },
	wyvern = { wyvern = true },
}

-- Sub-kind by whole words of the id (first match wins). A trailing "*" also matches longer words.
local KINDS: { { any } } = {
	{ "wyvern", { "wyvern", "snallygaster", "piasa", "kaiju", "cockatoo dragon" } },
	{ "bat", { "bat", "pipistrelle", "ahool", "camazotz", "hellbat" } },
	{ "ptero", { "pteranodon", "pterodactyl", "pterosaur", "tapejara", "dimorphodon", "rhamphorhynchus", "nyctosaurus", "ornithocheirus", "anhanguera",
		"hatzegopteryx", "tupandactylus", "pterodaustro", "quetzalcoatlus", "kongamato" } },
	{ "siren", { "alkonost", "sirin", "gamayun", "siren" } },
	{ "penguin", { "penguin*" } },
	{ "auk", { "puffin", "guillemot", "auk", "auklet", "razorbill" } },
	{ "owl", { "owl*" } },
	{ "vulture", { "vulture", "condor", "argentavis" } },
	{ "mythic", { "phoenix", "firebird", "fenghuang", "vermilion", "simurgh", "huma", "sunfire", "thunderbird", "impundulu", "ziz", "seraph", "caladrius",
		"stymphalian" } },
	{ "raptor", { "eagle*", "hawk", "falcon", "kite", "osprey", "buzzard", "harrier", "goshawk", "sparrowhawk", "kestrel", "merlin", "gyrfalcon", "roc",
		"caracara", "garuda", "gandaberunda", "harpy" } },
	{ "terror", { "terror", "titanis", "gastornis", "phorusrhacos" } },
	{ "kiwi", { "kiwi" } },
	{ "ratite", { "ostrich", "emu", "rhea", "cassowary", "moa", "elephant" } },
	{ "pelican", { "pelican", "marabou" } },
	{ "swan", { "swan" } },
	{ "goose", { "goose", "gosling" } },
	{ "duck", { "duck*", "teal", "eider", "merganser", "pintail", "canvasback", "shelduck", "mallard", "coot", "loon", "grebe" } },
	{ "wader", { "heron", "egret", "stork", "crane", "flamingo", "ibis", "spoonbill", "jabiru", "bittern", "shoebill", "hammerkop", "secretary", "seriema",
		"avocet", "curlew", "anhinga", "sunbittern", "kagu" } },
	{ "shorebird", { "sandpiper", "plover", "snipe", "woodcock", "oystercatcher", "rail", "stilt", "dipper", "moorhen", "takahe", "weka" } },
	{ "seabird", { "gull", "seagull", "tern", "albatross", "petrel", "shearwater", "gannet", "booby", "cormorant", "frigatebird", "skua", "kittiwake",
		"pelagornis" } },
	{ "parrot", { "parrot", "macaw", "cockatoo", "cockatiel", "budgie", "budgerigar", "lovebird", "conure", "lorikeet", "rosella", "galah", "kea", "kakapo" } },
	{ "fowl", { "chicken", "rooster", "hen", "bantam", "turkey", "grouse", "quail", "pheasant", "partridge", "peacock", "peafowl", "pea", "guinea", "capercaillie",
		"dodo", "silkie", "hoatzin" } },
	{ "pigeon", { "pigeon", "dove" } },
	{ "hummer", { "hummingbird", "sunbird", "honeyeater" } },
	{ "kingfisher", { "kingfisher", "kookaburra", "motmot", "jacamar", "puffbird", "trogon", "quetzal", "bee" } },
	{ "toucan", { "toucan", "hornbill", "barbet" } },
	{ "woodpecker", { "woodpecker", "nuthatch", "treecreeper", "hoopoe" } },
	{ "corvid", { "crow", "raven", "rook", "jackdaw", "magpie", "jay", "grackle", "starling", "mynah", "blackbird", "cowbird", "drongo", "oxpecker" } },
	{ "finch", { "finch", "chaffinch", "bullfinch", "sparrow", "canary", "grosbeak", "bunting", "crossbill", "cardinal", "weaver", "tanager", "zebra" } },
}

-- Per-word touches on top of the kind (beak, crest, tail, colours, proportions).
local WORD: { [string]: any } = {
	flamingo = { beak = "bent", legCol = C.pinkLeg, beakCol = C.black, leg = 2.9, neck = 1.9 },
	ibis = { beak = "curve", beakCol = C.black },
	curlew = { beak = "curve", beakCol = C.black },
	["sacred ibis"] = { beak = "curve", beakCol = C.black, headCol = C.black },
	spoonbill = { beak = "spoon", beakCol = C.slate },
	avocet = { beak = "probe", bl = 0.6, beakPitch = 8, beakCol = C.black },
	shoebill = { beak = "shoe", bl = 1.1, neck = 0.9, head = 1.0, leg = 1.9, beakCol = C.ivory },
	["boat-billed heron"] = { beak = "shoe", bl = 0.7, neck = 0.5, leg = 1.2, beakCol = C.black },
	stork = { beakCol = C.red, legCol = C.red },
	jabiru = { beakCol = C.black, legCol = C.black, ruffCol = C.red },
	crane = { crest = "cap", beakCol = C.slate },
	["crowned crane"] = { crest = "crown", beakCol = C.black },
	["whooping crane"] = { crest = "cap", beakCol = C.slate },
	["crane bird"] = { crest = "cap", beakCol = C.slate },
	egret = { beakCol = C.yellow, legCol = C.black },
	heron = { beakCol = C.yellow, crest = "plume" },
	["night heron"] = { leg = 1.4, neck = 0.6, crest = "plume" },
	bittern = { leg = 1.4, neck = 1.0, neckUp = -10 },
	hammerkop = { crest = "hammer", leg = 1.5, neck = 0.6, beakCol = C.black },
	secretary = { beak = "hook", bl = 0.9, crest = "quills", leg = 3.0, neck = 0.9, headMesh = "s_head_raptor", feet = "talon", legCol = C.ivory },
	seriema = { beak = "hook", bl = 0.8, crest = "plume", leg = 2.0, neck = 0.8 },
	anhinga = { leg = 0.6, neck = 1.8, beakCol = C.yellow },
	kagu = { leg = 1.2, neck = 0.4, crest = "plume", beakCol = C.red },
	sunbittern = { leg = 1.0, neck = 0.8 },
	marabou = { beak = "dagger", bl = 1.5, headCol = C.bald, leg = 2.2, neck = 0.6, pouch = true, beakCol = C.ivory, legCol = C.greyLeg },
	frigatebird = { beak = "hook", bl = 1.4, balloon = true, beakCol = C.slate, wings = "spread", span = 2.6, tail = "fork" },
	albatross = { beak = "hook", bl = 1.2, span = 2.9, beakCol = C.pinkLeg },
	gull = { beak = "hook", bl = 1.15, beakCol = C.yellow },
	seagull = { beak = "hook", bl = 1.15, beakCol = C.yellow },
	kittiwake = { beak = "hook", bl = 1.0, beakCol = C.yellow },
	skua = { beak = "hook", bl = 1.0, beakCol = C.black, legCol = C.black },
	tern = { tail = "fork", beakCol = C.red, crest = "cap" },
	cormorant = { beak = "hook", bl = 1.1, neck = 0.8, neckUp = 15, wings = "folded", pitch = 40, beakCol = C.slate, legCol = C.black },
	gannet = { bl = 1.0, beakCol = C.slate, legCol = C.slate },
	booby = { bl = 1.0, beakCol = C.slate, legCol = C.blueNeck, wings = "folded" },
	["blue-footed booby"] = { bl = 1.0, beakCol = C.slate, legCol = C.blueNeck, wings = "folded", leg = 0.6 },
	pelagornis = { span = 3.2, bl = 1.6, teeth = true },
	petrel = { beak = "hook", bl = 0.8, beakCol = C.black, legCol = C.black },
	shearwater = { beak = "hook", bl = 0.9, beakCol = C.slate, span = 2.4 },
	coot = { beak = "cone", bl = 0.9, beakCol = C.ivory, shield = true, neck = 0.3, legCol = C.greyLeg },
	moorhen = { beak = "cone", bl = 0.9, beakCol = C.red, shield = true, leg = 0.9 },
	loon = { beak = "dagger", bl = 0.9, beakCol = C.black, neck = 0.6 },
	grebe = { beak = "dagger", bl = 0.7, beakCol = C.black, crest = "punk", neck = 0.6 },
	merganser = { beak = "dagger", bl = 0.9, crest = "punk", beakCol = C.red },
	pintail = { tail = "long", tl = 1.1 },
	["mandarin duck"] = { crest = "punk" },
	["wood duck"] = { crest = "punk" },
	["muscovy duck"] = { wattle = true },
	["whistling duck"] = { leg = 0.9, neck = 0.8 },
	["giant rubber duck"] = { toy = true, leg = 0, wings = "none" },
	["rubber duck"] = { toy = true, leg = 0, wings = "none" },
	["swan goose"] = { knob = true },
	["black swan"] = { beakCol = C.red },
	cockatoo = { crest = "fan", beakCol = C.slate },
	cockatiel = { crest = "plume", tail = "long", beakCol = C.slate },
	galah = { crest = "cap", beakCol = C.ivory },
	macaw = { tail = "long", tl = 2.4 },
	["hyacinth macaw"] = { tail = "long", tl = 2.3, beakCol = C.black },
	budgie = { tl = 1.6, beakCol = C.yellow },
	rosella = { tl = 1.8 },
	lorikeet = { beakCol = C.red },
	["rainbow lorikeet"] = { beakCol = C.red },
	kakapo = { pitch = 25, body = { 2.2, 1.7, 1.7 }, tail = "short" },
	kea = { beakCol = C.slate },
	["african grey"] = { beakCol = C.black, tl = 1.1 },
	rooster = { comb = true, wattle = true, tail = "sickle" },
	chicken = { comb = true, wattle = true, tail = "sickle", tl = 0.8 },
	hen = { comb = true, wattle = true },
	bantam = { comb = true, wattle = true, tail = "sickle" },
	["zombie chicken"] = { comb = true, wattle = true, tail = "sickle" },
	["rubber chicken monster"] = { comb = true, wattle = true, neck = 1.4, leg = 1.2, tail = "short" },
	silkie = { crest = "pom", mesh = "s_bird_fluff" },
	turkey = { wattle = true, snood = true, tail = "train", headCol = C.bald, neck = 0.6 },
	peacock = { crest = "crown", tail = "train", tl = 1.5, neck = 0.75 },
	peafowl = { crest = "crown", tail = "train", tl = 1.5, neck = 0.75 },
	pheasant = { tail = "long", tl = 2.6, wattle = true, neck = 0.5 },
	["golden pheasant"] = { tail = "long", tl = 2.6, crest = "cap", neck = 0.5 },
	quail = { crest = "topknot", tail = "short", body = { 1.8, 1.5, 1.45 } },
	partridge = { tail = "short", body = { 1.9, 1.55, 1.5 } },
	grouse = { tail = "fan" },
	["sage grouse"] = { tail = "train", tl = 1.0 },
	["prairie chicken"] = { tail = "short" },
	capercaillie = { tail = "train", tl = 1.0, beakCol = C.ivory },
	["guinea fowl"] = { neck = 0.5, wattle = true, body = { 2.1, 1.7, 1.55 }, tail = "short", casque = true },
	dodo = { beak = "huge", bl = 0.8, body = { 2.3, 2.0, 1.9 }, head = 0.95, tail = "plume", leg = 0.6, legW = 0.22, beakCol = C.ivory },
	hoatzin = { crest = "punk", tail = "long" },
	cassowary = { casque = true, beak = "cone", bl = 0.9, neckCol = C.blueNeck, wattle = true },
	emu = { beak = "cone", bl = 0.8, neckCol = C.blueNeck },
	rhea = { beak = "duck", bl = 0.65 },
	moa = { beak = "cone", bl = 0.85, neck = 2.5 },
	["elephant bird"] = { beak = "cone", bl = 0.9, body = { 2.6, 2.2, 2.0 }, leg = 2.0, legW = 0.38, neck = 1.6 },
	ostrich = { beak = "duck", bl = 0.7 },
	condor = { headCol = C.slate, ruffCol = C.ivory },
	["king vulture"] = { headCol = C.red, ruffCol = C.slate },
	["turkey vulture"] = { headCol = C.red },
	["bearded vulture"] = { headCol = "primary", ruff = false, beard = true },
	["griffon vulture"] = { headCol = C.ivory, ruffCol = C.ivory },
	osprey = { beakCol = C.black },
	["bald eagle"] = { headCol = "secondary", beakCol = C.yellow, breastCol = false, tailCol = "secondary" },
	["harpy eagle"] = { crest = "plume" },
	["philippine eagle"] = { crest = "shaggy" },
	caracara = { headCol = C.red, crest = "cap" },
	["secretary bird"] = { crest = "quills" },
	kestrel = { pitch = 46 },
	falcon = { tail = "short" },
	["kite bird"] = { tail = "fork" },
	garuda = { crest = "flame" },
	["great horned owl"] = { ears = true },
	["eagle owl"] = { ears = true },
	["long-eared owl"] = { ears = true },
	["screech owl"] = { ears = true },
	["horned owl"] = { ears = true },
	["barn owl"] = { headW = 1.0, discCol = C.ivory },
	["snowy owl"] = {},
	toucan = { beakCol = C.yellow },
	hornbill = { casque = true, beakCol = C.yellow },
	barbet = { beak = "cone", bl = 1.25, beakCol = C.ivory },
	kookaburra = { head = 1.3, bl = 1.0, beakCol = C.slate },
	motmot = { tail = "long", tl = 2.0, racket = true },
	jacamar = { beak = "probe", bl = 1.0, tail = "long", tl = 1.6 },
	trogon = { beak = "cone", bl = 0.8, tail = "long", tl = 1.6, beakCol = C.yellow },
	quetzal = { beak = "cone", bl = 0.7, tail = "ribbons", tl = 2.8, crest = "pom" },
	["bee-eater"] = { beak = "curve", bl = 0.65, tail = "long", tl = 1.4 },
	puffbird = { body = { 1.7, 1.5, 1.45 }, beak = "hook", bl = 0.6 },
	hoopoe = { beak = "curve", bl = 0.9, crest = "fan", beakCol = C.black },
	nuthatch = { pitch = 10, bl = 0.75, tail = "short" },
	treecreeper = { beak = "curve", bl = 0.7, pitch = 60 },
	sunbird = { beak = "curve", bl = 0.9, body = { 1.6, 1.15, 1.05 } },
	honeyeater = { beak = "curve", bl = 0.75 },
	magpie = { tail = "long", tl = 2.0 },
	["blue jay"] = { crest = "plume" },
	["steller's jay"] = { crest = "plume" },
	jay = { crest = "plume" },
	drongo = { tail = "fork", tl = 1.6 },
	raven = { body = { 2.5, 1.5, 1.4 }, bl = 0.75, ruffCol = "primary", beard = true },
	["shadow raven"] = { body = { 2.5, 1.5, 1.4 }, bl = 0.75 },
	cardinal = { crest = "plume", beakCol = C.red },
	waxwing = { crest = "plume" },
	lark = { crest = "plume" },
	["steller jay"] = { crest = "plume" },
	["red-winged blackbird"] = { epaulet = true },
	swallow = { tail = "fork", tl = 1.6, span = 1.7 },
	swift = { tail = "fork", span = 1.9, legW = 0.06, leg = 0.25 },
	wren = { tail = "cocked", body = { 1.6, 1.4, 1.35 } },
	fairywren = { tail = "cocked", body = { 1.6, 1.4, 1.35 } },
	kinglet = { crest = "cap" },
	chickadee = { body = { 1.7, 1.45, 1.4 } },
	robin = { body = { 1.9, 1.55, 1.45 } },
	["bird of paradise"] = { tail = "ribbons", tl = 2.2, crest = "plume" },
	lyrebird = { tail = "train", tl = 1.6 },
	["fantail pigeon"] = { tail = "train", tl = 1.0 },
	["dove of peace"] = { wings = "spread", branch = true },
	["homing pigeon"] = {},
	crossbill = { bl = 0.9 },
	grosbeak = { bl = 1.25 },
	["java sparrow"] = { bl = 1.15, beakCol = C.pinkLeg },
	["zebra finch"] = { beakCol = C.red },
	tapejara = { crest = "sail" },
	tupandactylus = { crest = "sail", crestK = 1.5 },
	pteranodon = { crest = "back", crestK = 1.4 },
	nyctosaurus = { crest = "antler" },
	dimorphodon = { head = 1.0, bl = 1.0, beak = "huge", crest = "none", tail = "rudder", teeth = true },
	rhamphorhynchus = { tail = "rudder", crest = "none", bl = 1.6, teeth = true },
	["pterodactyl hatchling"] = { crest = "back" },
	anhanguera = { crest = "keel", teeth = true },
	ornithocheirus = { crest = "keel", teeth = true },
	pterodaustro = { beakPitch = 10, crest = "none", bl = 3.4 },
	hatzegopteryx = { head = 0.9, crest = "back", body = { 2.2, 1.3, 1.3 } },
	kongamato = { crest = "none", teeth = true, tail = "rudder" },
	["long-eared bat"] = { earK = 2.0 },
	["fruit bat"] = { fox = true },
	["hammer-headed bat"] = { fox = true, head = 1.4 },
	["vampire bat lord"] = { cape = true },
	ahool = { head = 1.35 },
	chonchon = { head = 1.8, body = { 0.9, 0.9, 0.9 }, earK = 1.6 },
}

local function wordIn(id: string, w: string): boolean
	if string.sub(w, -1) == "*" then
		return string.find(id, "%f[%a]" .. string.sub(w, 1, -2)) ~= nil
	end
	if string.find(w, " ", 1, true) then
		return string.find(id, w, 1, true) ~= nil
	end
	return string.find(id, "%f[%a]" .. w .. "%f[^%a]") ~= nil
end

local function classify(id: string, t: any): string
	for _, row in KINDS do
		for _, w in row[2] do
			if wordIn(id, w) then
				return row[1]
			end
		end
	end
	if t.dragon or (t.scaly and not t.feathers) then
		return "wyvern"
	end
	if t.batwing then
		return "bat"
	end
	return "songbird"
end

local BABY = { "chick", "duckling", "gosling", "owlet", "eaglet", "hatchling", "fledgling", "baby", "cygnet", "nestling" }

local function profile(id: string, t: any): (string, any, boolean)
	local kind = classify(id, t)
	local P = table.clone(BASE)
	for k, v in PROFILE[kind] or {} do
		P[k] = v
	end
	-- word touches: exact id first, then each whole word of a multi-word id
	local touches = WORD[id]
	if touches == nil then
		for w in string.gmatch(id, "[%a%-']+") do
			if WORD[w] then
				touches = WORD[w]
			end
		end
	end
	for k, v in touches or {} do
		P[k] = v
	end
	local baby = false
	for _, w in BABY do
		if wordIn(id, w) or (w == "chick" and id == "chick") then
			baby = true
		end
	end
	-- trait-driven variety
	if P.crest == nil and t.crest then
		P.crest = "plume"
	end
	if t.longTail and (P.tail == "fan" or P.tail == "short") then
		P.tail, P.tl = "long", math.max(P.tl, 1.8)
	end
	if t.chubby then
		P.body = { P.body[1] * 1.02, P.body[2] * 1.12, P.body[3] * 1.15 }
	end
	if t.longLegs and P.leg < 1.2 then
		P.leg *= 1.8
	end
	if t.noWings then
		P.wings = "none"
	end
	if baby and kind ~= "wyvern" and kind ~= "bat" then
		P.body = { 1.55, 1.6, 1.55 }
		P.pitch = 8
		P.leg = math.min(P.leg, 0.45) * (if kind == "ratite" or kind == "wader" then 1.6 else 1)
		P.legW = math.max(P.legW, 0.14)
		P.neck = math.min(P.neck, 0.25)
		P.head = 1.25 * (if kind == "ptero" then 0.8 else 1)
		P.bl = (P.bl or 1) * (if P.beak == "pouch" or P.beak == "huge" or kind == "ptero" then 0.45 else 0.62)
		P.mesh = "s_bird_fluff"
		P.wings = if P.wings == "bat" then "bat" elseif P.wings == "none" then "none" else "stub"
		P.span = (P.span or 1.4) * 0.6
		P.tail = if P.tail == "none" then "none" else "short"
		P.tl = 0.5
		P.crest = if P.crest == "flame" then "flame" elseif P.crest == "pom" then "pom" else nil
		P.comb, P.wattle, P.snood, P.ruff, P.casque, P.ears, P.pouch = nil, nil, nil, nil, nil, nil, nil
		P.eyeD = 0.36
		P.trousers, P.drumstick = nil, nil
	end
	return kind, P, baby
end

-- Wyvern (bat-winged two-legged reptile with a stinger tail): the reptile build.
local function wyvern(B: any, ctx: any, t: any, id: string)
	local detail = ctx.detail
	local bulk = 0.9 + t.durability * 0.03
	local legLen = 0.9
	local bodyL = 2.1 * bulk
	local bodyH = 1.35 * bulk
	local bodyY = legLen + bodyH * 0.45
	local pitch = rad(-22)
	B.boneIndex.Body.pos = { 0, bodyY, 0 }
	B:ell(bodyH * 0.82, bodyH, bodyL, at(0, bodyY, 0, pitch, 0, 0), { col = "primary", mat = "scale", pri = 1, role = "body", name = "Body" })
	if detail >= 1 then
		B:ell(bodyH * 0.6, bodyH * 0.78, bodyL * 0.62, at(0, bodyY - bodyH * 0.12, -bodyL * 0.22, pitch, 0, 0), { col = "belly", mat = "scale", pri = 1.8, role = "detail", name = "Breast" })
	end
	Parts.legPair(B, { tag = "", x = bodyH * 0.3, y = legLen + 0.1, z = 0.12, w = 0.2 * bulk, kind = "claw", thigh = 1.4, claws = true, phase = 0 })
	local headP = { 0, bodyY + bodyH * 0.42, -bodyL * 0.42 }
	B:bone("Head", "Body", headP[1], headP[2], headP[3])
	B:setRig("head", "Head")
	local headS = 0.95 * bulk
	local info = Heads.reptile(B, { p = headP, s = headS * 1.05 }, t)
	Parts.horns(B, { bone = "Head", x = headS * 0.24, y = info.top[2] - headS * 0.08, z = info.top[3], len = headS * 0.7, w = headS * 0.16, kind = "swept", segs = 2, pri = 2.2 })
	if t.crest or string.find(id, "cockatoo") then
		for i = 1, 3 do
			B:limb({ 0, info.top[2] - 0.1, info.c[3] + i * 0.08 }, { 0, info.top[2] + 0.35 + i * 0.08, info.c[3] + 0.25 + i * 0.18 }, headS * 0.13,
				{ col = if i == 2 then "secondary" else "accent", mat = "fur", bone = "Head", pri = 2.4 + i * 0.3, role = "crest", trail = i == 3, mesh = "s_crest_feather" }, 0.1)
		end
	end
	Parts.wings(B, { x = bodyH * 0.3, y = bodyY + bodyH * 0.22, z = -bodyL * 0.12, span = bodyL * 1.6, kind = "bat" })
	Parts.tail(B, { start = { 0, bodyY - bodyH * 0.1, bodyL * 0.42 }, dir = { 0, -0.2, 1 }, len = bodyL * 1.2, w = bodyH * 0.4, segs = if detail <= 1 then 1 else 3, kind = "stinger", taper = 0.65 })
	B:socket("core", at(0, bodyY, 0), "Body")
	B:setRig("gait", "bird")
end

-- Bird legs: feathered thigh (or a bare drumstick on ratites), scaly shank, foot (three toes forward, hallux
-- back; webbed on waterfowl). Returns nothing; registers the leg rig.
local function legs(B: any, P: any, hip: { number }, detail: number, col: any)
	local h = hip[2]
	local w = P.legW * (P.bulk or 1)
	local x, z = hip[1], hip[3]
	local legCol = P.legCol
	if detail <= 0 or h <= 0.05 then
		if h <= 0.05 then
			return
		end
		local hb = B:bone("Hip", "Body", 0, h, z)
		B:addRig("legs", { hip = hb, side = 0, phase = 0, len = h })
		B:mlimb({ x, h * 0.9, z }, { x, w * 0.4, z - w * 0.6 }, w * 1.6, { col = legCol, mat = "hard", bone = "Hip", pri = 1.35, role = "limb", name = "Leg#" }, 0.15)
		return
	end
	local hr, hl = B:mirrorBone("Hip#", "Body", x, h, z)
	-- the visible "backward knee" is the ankle: heel behind the hip, at about 40% of the leg
	local heelY = h * (if P.feet == "ratite" or h > 1.5 then 0.42 else 0.36)
	local heel = { x, heelY, z + h * 0.12 }
	local kr, kl = B:mirrorBone("Knee#", "Hip#", heel[1], heel[2], heel[3])
	B:addRig("legs", { hip = hr, knee = kr, side = 1, phase = 0, len = h })
	B:addRig("legs", { hip = hl, knee = kl, side = -1, phase = 0.5, len = h })
	local foot = { x * 1.05, 0, z - h * 0.02 }
	local thighW = w * (if P.drumstick then 2.6 elseif P.trousers then 2.3 else 1.7)
	local thighTop = { x, h + w * 0.6, z - h * 0.04 }
	if detail <= 1 then
		-- one tapered leg per side on small budgets
		B:mlimb({ x, h + w * 0.3, z }, { foot[1], w * 0.4, foot[3] - w * 0.5 }, w * 1.5, { col = legCol, mat = "hard", bone = "Hip#", pri = 1.3, role = "limb", name = "Leg#" }, 0.15)
		return
	end
	B:mlimb(thighTop, heel, thighW, { col = if P.drumstick then legCol else col, mat = if P.drumstick then "skin" else "fur", bone = "Hip#", pri = 1.3, role = "limb", name = "Thigh#" }, 0.18)
	B:mlimb(heel, { foot[1], w * 0.5, foot[3] }, w, { col = legCol, mat = "hard", bone = "Knee#", pri = 1.36, role = "limb", name = "Shank#" }, 0.12)
	if detail <= 1 then
		return
	end
	-- foot: the centre toe leads the sculpt; the outer and inner toes (and the web) are its members
	local f = w * (if P.feet == "ratite" then 3.0 elseif P.feet == "web" then 4.6 else 3.8)
	local toeY = f * 0.11
	local web = P.feet == "web"
	local mesh = if web then "s_bird_foot_web" elseif P.feet == "talon" then "s_bird_foot_talon" else "s_bird_foot"
	local cr, cl = B:mell(f * 0.3, f * 0.22, f, at(foot[1], toeY, foot[3] - f * 0.38), { col = legCol, mat = "hard", bone = "Knee#", pri = 1.8, role = "foot", name = "Toe#", mesh = mesh })
	if detail >= 3 then
		local members = { {}, {} }
		for _, a in { 34, -34 } do
			local ta = rad(a)
			local tip = { foot[1] + sin(ta) * f * 0.78, toeY * 0.8, foot[3] - f * 0.12 - cos(ta) * f * 0.7 }
			local r, l = B:mlimb({ foot[1], toeY, foot[3] - f * 0.1 }, tip, f * 0.2, { col = legCol, mat = "hard", bone = "Knee#", pri = 3.1, role = "foot", name = "SideToe#", depth = f * 0.17, mesh = false }, 0.08)
			table.insert(members[1], r)
			table.insert(members[2], l)
		end
		if web then
			local r, l = B:mell(f * 0.95, f * 0.06, f * 0.55, at(foot[1], toeY * 0.5, foot[3] - f * 0.48), { col = legCol, mat = "hard", bone = "Knee#", pri = 3.3, role = "foot", name = "Web#", mesh = false })
			table.insert(members[1], r)
			table.insert(members[2], l)
		end
		B:sculpt(cr, mesh, members[1])
		B:sculpt(cl, mesh, members[2])
	end
end

-- Head: crown + beak + eyes (+ owl facial disc). hc = head centre (model space), s = head size.
local function head(B: any, P: any, t: any, hc: { number }, s: number, detail: number): any
	local bone = "Head"
	local r = { s * 0.5 * (P.headW or 1), s * 0.5, s * 0.52 }
	local headCol = P.headCol or "primary"
	local h = B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(hc[1], hc[2], hc[3]), { col = headCol, mat = "fur", bone = bone, pri = 1.1, role = "head", name = "Head", mesh = P.headMesh })
	local info = { c = hc, r = r, s = s, top = { hc[1], hc[2] + r[2] * 0.92, hc[3] + r[3] * 0.1 }, head = h }
	-- beak
	local bk = BEAK[P.beak]
	local beakTip = { hc[1], hc[2] - s * 0.1, hc[3] - r[3] }
	if bk then
		local bl = bk[3] * (P.bl or 1)
		local pitch = rad(bk[4] + (P.beakPitch or 0))
		local base = { hc[1], hc[2] - s * (if P.beak == "parrot" or P.beak == "huge" then 0.02 else 0.08), hc[3] - r[3] * 0.72 }
		local dy, dz = sin(pitch), -cos(pitch)
		local bw, bh = bk[1] * s, bk[2] * s
		local cen = { base[1], base[2] + dy * bl * s * 0.5, base[3] + dz * bl * s * 0.5 }
		local beak = B:ell(bw, bh, bl * s, at(cen[1], cen[2], cen[3], pitch, 0, 0), { col = P.beakCol, mat = "hard", bone = bone, pri = 1.2, role = "beak", name = "Beak" })
		beakTip = { base[1], base[2] + dy * bl * s, base[3] + dz * bl * s }
		local members = {}
		if detail >= 2 and P.beak ~= "duck" and P.beak ~= "spoon" then
			-- lower mandible, a little shorter
			local lc = Geom.offset(at(cen[1], cen[2], cen[3], pitch, 0, 0), 0, -bh * 0.3, bl * s * 0.06)
			table.insert(members, B:ell(bw * 0.78, bh * 0.5, bl * s * 0.86, lc, { col = P.beakCol, mat = "hard", bone = bone, pri = 2.8, role = "beak", name = "BeakLow" }))
		end
		if P.beak == "pouch" and detail >= 1 then
			-- the throat pouch hangs under the bill (a member: the pouch sculpt has it)
			local pc = Geom.offset(at(cen[1], cen[2], cen[3], pitch, 0, 0), 0, -bh * 0.55, bl * s * 0.08)
			table.insert(members, B:ell(bw * 0.95, bh * 1.0, bl * s * 0.78, pc, { col = "inner", mat = "skin", bone = bone, pri = 2.2, role = "beak", name = "Pouch" }))
		end
		if P.teeth and detail >= 2 then
			Parts.teeth(B, { bone = bone, y = cen[2] - bh * 0.3, z = cen[3] - bl * s * 0.2, r = bw * 0.3, n = 2, h = s * 0.12, pri = 3.6 })
		end
		local mesh = bk[5]
		if mesh == "s_beak" then
			-- the classic hooked beak sculpt was authored on Heads.bird's upper beak (0.34 x 0.3 x 0.62 head units)
			B:sculpt(beak, mesh, members)
		else
			B:sculpt(beak, mesh, members)
		end
		if P.casque and detail >= 1 then
			local cc = Geom.offset(at(cen[1], cen[2], cen[3], pitch, 0, 0), 0, bh * 0.5, bl * s * 0.2)
			B:ell(bw * 0.8, bh * 0.6, bl * s * 0.62, cc, { col = if P.kind == "ratite" or P.kind == "fowl" then "horn" else "accent", mat = "hard", bone = bone, pri = 1.9, role = "crest", name = "Casque" })
		end
		if P.shield and detail >= 2 then
			B:ell(bw * 0.7, bh * 1.1, s * 0.28, at(base[1], base[2] + bh * 0.45, base[3] + s * 0.02, rad(-50), 0, 0), { col = P.beakCol, mat = "hard", bone = bone, pri = 2.6, role = "beak", name = "Shield" })
		end
		if P.knob and detail >= 2 then
			B:ball(s * 0.28, at(base[1], base[2] + bh * 0.5, base[3] + s * 0.02), { col = "dark", mat = "hard", bone = bone, pri = 2.8, role = "beak", name = "Knob" })
		end
	end
	-- face
	local face = { kind = "ellipsoid", c = hc, r = r }
	local eyeSp, eyeY, eyeD = s * P.eyeSp, s * 0.1, s * P.eyeD * (if t.bigEyes then 1.2 else 1)
	if P.owl then
		-- facial disc: a dished mask in the pale colour; the eyes sit on it, facing forward
		local dc = { hc[1], hc[2] - s * 0.04, hc[3] - r[3] * 0.62 }
		local dr = { r[1] * 0.86, r[2] * 0.8, r[3] * 0.5 }
		B:ell(dr[1] * 2, dr[2] * 2, dr[3] * 2, at(dc[1], dc[2], dc[3]), { col = P.discCol or "belly", mat = "fur", bone = bone, pri = 1.14, role = "head", name = "FaceDisc", mesh = "s_owl_disc" })
		face = { kind = "ellipsoid", c = dc, r = dr }
		eyeSp, eyeY = s * 0.21, s * 0.06
		-- the beak sits on the disc between the eyes
	end
	Face.build(B, {
		face = face, bone = bone, mood = (B.ctx.result and B.ctx.result.mood) or "Neutral", detail = detail, kind = Heads.eyeKind(t, {}),
		spacing = eyeSp, y = eyeY, d = eyeD, noMouth = true, lidCol = headCol,
	})
	info.beakTip = beakTip
	return info
end

-- Crest feather (seg Y: root -> tip) in the bird's centre plane
local function feather(B: any, a: { number }, b: { number }, w: number, col: any, pri: number, trail: boolean?, mirror: boolean?)
	local spec = { col = col, mat = "fur", bone = "Head", pri = pri, role = "crest", depth = w * 1.8, trail = trail, mesh = "s_crest_feather" }
	if mirror then
		return B:mlimb(a, b, w * 0.55, spec, 0.06)
	end
	return B:limb(a, b, w * 0.55, spec, 0.06)
end

local function crest(B: any, P: any, info: any, detail: number)
	local kind = P.crest
	if kind == nil or kind == "none" or detail < 1 then
		return
	end
	local s, c, top = info.s, info.c, info.top
	if kind == "plume" or kind == "shaggy" or kind == "punk" then
		-- swept-back tuft of 2-3 feathers from the crown
		local n = if detail >= 3 then 3 else (if detail >= 2 then 2 else 1)
		local len = s * (if kind == "punk" then 0.75 else 0.62)
		for i = 1, n do
			local a = { 0, top[2] - s * 0.08, c[3] - s * 0.1 + i * s * 0.12 }
			local ang = rad(28 + i * 18 + (if kind == "punk" then -12 else 0))
			local b = { 0, a[2] + cos(ang) * len * (1.1 - i * 0.12), a[3] + sin(ang) * len }
			feather(B, a, b, s * 0.2, if i == 2 then "secondary" else "primary", 2.1 + i * 0.25, i == n)
		end
	elseif kind == "fan" then
		-- cockatoo / hoopoe: a fan of feathers standing up and curling forward
		local n = if detail >= 3 then 4 else 2
		for i = 1, n do
			local a = { 0, top[2] - s * 0.12, c[3] + s * 0.05 + i * s * 0.06 }
			local ang = rad(-18 + i * (60 / n))
			local len = s * (0.95 - i * 0.06)
			feather(B, a, { 0, a[2] + cos(ang) * len, a[3] + sin(ang) * len }, s * 0.22, if i % 2 == 0 then "secondary" else "accent", 1.9 + i * 0.2, i == 1)
		end
	elseif kind == "crown" or kind == "pom" then
		-- crowned crane / peacock: a spray of stiff quills fanned sideways; silkie / quetzal: a pom-pom
		if kind == "pom" then
			B:ell(s * 0.72, s * 0.5, s * 0.72, at(c[1], top[2] - s * 0.02, c[3] + s * 0.05), { col = "light", mat = "fur", bone = "Head", pri = 2.0, role = "crest", name = "Pom", mesh = "s_bird_fluff" })
			return
		end
		local n = if detail >= 3 then 3 else 1
		for i = 1, n do
			local spread = (i - (n + 1) / 2) * 0.22
			local a = { 0, top[2] - s * 0.05, c[3] }
			local b = { spread * s, a[2] + s * 0.6, a[3] + s * 0.08 }
			if spread == 0 then
				feather(B, a, b, s * 0.18, "secondary", 2.0, true)
			else
				local _ = feather(B, a, { math.abs(spread) * s, b[2], b[3] }, s * 0.16, "secondary", 2.3 + i * 0.1, false, true)
				break
			end
		end
		B:ell(s * 0.55, s * 0.32, s * 0.5, at(c[1], top[2] + s * 0.52, c[3] + s * 0.06), { col = "accent", mat = "fur", bone = "Head", pri = 2.5, role = "crest", name = "CrownTuft", mesh = "s_bird_fluff" })
	elseif kind == "cap" or kind == "red" then
		-- coloured cap on the crown (crane's red, kinglet's gold, woodpecker's red)
		B:ell(s * 0.66, s * 0.3, s * 0.7, at(c[1], top[2] - s * 0.1, c[3] + s * 0.06, rad(-8), 0, 0), { col = if kind == "red" then C.red else "secondary", mat = "fur", bone = "Head", pri = 2.0, role = "crest", name = "Cap" })
		if kind == "red" and detail >= 2 then
			feather(B, { 0, top[2] - s * 0.05, c[3] + s * 0.2 }, { 0, top[2] + s * 0.15, c[3] + s * 0.62 }, s * 0.2, C.red, 2.3, true)
		end
	elseif kind == "topknot" then
		-- quail: one plume curling forward over the face
		feather(B, { 0, top[2] - s * 0.05, c[3] - s * 0.05 }, { 0, top[2] + s * 0.45, c[3] - s * 0.38 }, s * 0.22, "dark", 2.0, true)
	elseif kind == "quills" then
		-- secretary bird: long black quills off the back of the head
		for i = 1, (if detail >= 3 then 3 else 2) do
			local yaw = (i - 2) * 0.35
			feather(B, { 0, c[2] + s * 0.05 * i, c[3] + s * 0.3 }, { yaw * s, c[2] + s * (0.2 + 0.12 * i), c[3] + s * 1.15 }, s * 0.14, C.black, 2.0 + i * 0.2, i == 1)
		end
	elseif kind == "hammer" then
		B:ell(s * 0.36, s * 0.4, s * 1.0, at(c[1], c[2] + s * 0.12, c[3] + s * 0.55, rad(12), 0, 0), { col = "primary", mat = "fur", bone = "Head", pri = 1.7, role = "crest", name = "Hammer" })
	elseif kind == "flame" then
		-- firebird: a crown of flame feathers, glowing tips
		local n = if detail >= 3 then 3 else 2
		for i = 1, n do
			local a = { 0, top[2] - s * 0.1, c[3] + (i - 1) * s * 0.16 }
			local ang = rad(10 + i * 22)
			local len = s * (1.0 - i * 0.12)
			feather(B, a, { 0, a[2] + cos(ang) * len, a[3] + sin(ang) * len }, s * 0.22, if i == 1 then "secondary" else "accent", 1.9 + i * 0.2, i == 1)
		end
		if detail >= 2 then
			B:ball(s * 0.22, at(0, top[2] + s * 0.85, c[3] + s * 0.36), { col = "glow", mat = "neon", glow = true, bone = "Head", pri = 3.2, role = "detail", name = "CrestGlow" })
		end
	elseif kind == "ptero" or kind == "back" then
		-- pteranodon: a long blade swept back from the skull
		local k = P.crestK or 1
		B:limb({ 0, c[2] + s * 0.15, c[3] + s * 0.1 }, { 0, c[2] + s * 0.55 * k, c[3] + s * 1.5 * k }, s * 0.24, { col = "secondary", mat = "hard", bone = "Head", pri = 1.25, role = "crest", name = "Crest", depth = s * 0.75, mesh = "s_crest_feather", trail = true }, 0.1)
	elseif kind == "sail" then
		-- tapejara: a tall sail rising off the snout and skull
		local k = P.crestK or 1
		B:ell(s * 0.1, s * 1.5 * k, s * 1.5 * k, at(0, c[2] + s * 0.6 * k, c[3] - s * 0.2, rad(-25), 0, 0), { col = "secondary", mat = "skin", bone = "Head", pri = 1.25, role = "crest", name = "Sail", mesh = "s_crest_sail" })
	elseif kind == "keel" then
		-- anhanguera: rounded keels on the beak (top and bottom)
		local bt = info.beakTip
		B:ell(s * 0.08, s * 0.45, s * 0.6, at(0, bt[2] + s * 0.18, bt[3] + s * 0.35), { col = "secondary", mat = "skin", bone = "Head", pri = 2.0, role = "crest", name = "Keel", mesh = false })
	elseif kind == "antler" then
		-- nyctosaurus: a forked antler crest rising up and back
		local a = { 0, top[2] - s * 0.05, c[3] + s * 0.15 }
		local m = { 0, a[2] + s * 1.3, a[3] + s * 0.4 }
		B:limb(a, m, s * 0.12, { col = "secondary", mat = "hard", bone = "Head", pri = 1.8, role = "horn", name = "Antler" }, 0.08)
		if detail >= 2 then
			B:limb(m, { 0, m[2] + s * 0.2, m[3] + s * 1.0 }, s * 0.1, { col = "secondary", mat = "hard", bone = "Head", pri = 2.4, role = "horn", trail = true }, 0.08)
			B:limb(m, { 0, m[2] + s * 0.9, m[3] - s * 0.15 }, s * 0.09, { col = "secondary", mat = "hard", bone = "Head", pri = 2.6, role = "horn", trail = true }, 0.08)
		end
	end
end

-- Tail: fanned feathers, long streamers, forks, upright trains, sickles, ribbons, pterosaur rudder.
local function tail(B: any, P: any, base: { number }, bodyL: number, pitch: number, detail: number)
	local kind = P.tail
	if kind == "none" then
		return
	end
	B:bone("Tail1", "Body", base[1], base[2], base[3])
	B:addRig("tail", "Tail1")
	local tl = (P.tl or 1) * bodyL * 0.55
	local droop = pitch * 0.85 - rad(10) -- follows the body line, lifted a little
	if kind == "train" then
		-- upright fan (peacock, turkey, lyrebird): a wide disc of feathers standing behind the body
		local W = tl * 2.4
		local cf = at(base[1], base[2], base[3], rad(-62), 0, 0)
		B:ell(W, tl * 0.14, W * 0.62, Geom.offset(cf, 0, 0, W * 0.26), { col = "secondary", mat = "fur", bone = "Tail1", pri = 1.5, role = "tail", name = "Train", mesh = "s_bird_train" })
		if detail >= 3 then
			for i = -1, 1 do
				local ex, ey, ez = Geom.point(cf, i * W * 0.28, -tl * 0.09, W * 0.44 - math.abs(i) * W * 0.06)
				B:ell(W * 0.11, W * 0.11, tl * 0.06, at(ex, ey, ez, rad(-62), 0, 0), { col = "accent", mat = "fur", bone = "Tail1", pri = 3.4, role = "detail", name = "EyeSpot" })
			end
		end
		return
	end
	if kind == "ribbons" then
		-- firebird / quetzal: two long streamers trailing and curling, a short fan above them
		local ln = tl * 1.1
		local mid = { base[1] + 0.12, base[2] - ln * 0.2, base[3] + ln * 0.55 }
		local tip = { base[1] + 0.2, base[2] - ln * 0.15, base[3] + ln * 1.05 }
		B:mlimb({ base[1] + 0.06, base[2], base[3] }, mid, tl * 0.14, { col = "secondary", mat = "fur", bone = "Tail1", pri = 1.6, role = "tail", name = "Ribbon#", depth = tl * 0.05 }, 0.1)
		if detail >= 2 then
			B:mlimb(mid, { tip[1], tip[2] + ln * 0.18, tip[3] }, tl * 0.12, { col = "accent", mat = "fur", bone = "Tail1", pri = 2.2, role = "tail", trail = true, name = "RibbonTip#", depth = tl * 0.05 }, 0.1)
		end
		kind, tl = "fan", bodyL * 0.45
	end
	if kind == "rudder" then
		-- rhamphorhynchus: a long thin tail ending in a diamond vane
		local tip = { base[1], base[2] - bodyL * 0.1, base[3] + bodyL * 1.3 }
		B:limb(base, tip, bodyL * 0.08, { col = "primary", mat = "skin", bone = "Tail1", pri = 1.8, role = "tail", name = "TailRod" }, 0.05)
		B:ell(bodyL * 0.04, bodyL * 0.3, bodyL * 0.3, at(tip[1], tip[2], tip[3], 0, 0, 0), { col = "secondary", mat = "skin", bone = "Tail1", pri = 2.2, role = "fin", name = "Vane", trail = true })
		return
	end
	if kind == "plume" or kind == "short" then
		local len = tl * (if kind == "plume" then 0.9 else 0.7)
		local lift = if kind == "plume" then rad(-30) else droop + rad(-10)
		B:ell(tl * 0.9, tl * 0.32, len, Geom.mul(at(base[1], base[2], base[3], lift, 0, 0), at(0, 0, len * 0.38)), { col = if kind == "plume" then "light" else "wingTip", mat = "fur", bone = "Tail1", pri = 1.9, role = "tail", name = "TailTuft", mesh = if kind == "plume" then "s_bird_fluff" else "s_bird_tail" })
		return
	end
	if kind == "sickle" then
		-- rooster: arching sickle feathers rising then falling behind
		local n = if detail >= 3 then 3 else (if detail >= 2 then 2 else 1)
		for i = 1, n do
			local yaw = (i - (n + 1) / 2) * 0.18
			local a = { base[1] + yaw * 0.3, base[2] + tl * 0.05, base[3] }
			local m = { a[1] + yaw * tl * 0.3, a[2] + tl * (0.95 - i * 0.1), a[3] + tl * 0.45 }
			B:limb(a, m, tl * 0.22, { col = if i == 1 then "secondary" else "dark", mat = "fur", bone = "Tail1", pri = 1.35 + i * 0.3, role = "tail", name = "Sickle", depth = tl * 0.07, mesh = "s_crest_feather" }, 0.06)
			if detail >= 2 then
				B:limb(m, { m[1] + yaw * tl * 0.2, m[2] - tl * 0.55, m[3] + tl * 0.62 }, tl * 0.2, { col = if i == 1 then "secondary" else "dark", mat = "fur", bone = "Tail1", pri = 2.0 + i * 0.3, role = "tail", trail = i == 1, name = "SickleTip", depth = tl * 0.06, mesh = "s_crest_feather" }, 0.06)
			end
		end
		return
	end
	-- fan / long / fork / cocked: one sculpted fan (fallback: a flat feather ellipsoid plus two side feathers)
	local len = tl * (if kind == "long" then 1.3 else 1)
	local wid = tl * (if kind == "long" then 0.42 else (if kind == "fork" then 0.62 else 0.7))
	local tilt = if kind == "cocked" then rad(-60) elseif kind == "long" then droop + rad(4) else droop
	-- long tails on upright birds (macaw): flatten the droop, then shorten, so the tip never sinks into the ground
	if tilt > 0 then
		local room = math.max(base[2] - 0.12, 0.2)
		if math.sin(tilt) * len * 0.94 > room then
			tilt = math.max(math.min(tilt, math.asin(math.min(room / (len * 0.94), 1))), rad(12))
			local short = math.min(len, room / math.max(math.sin(tilt) * 0.94, 0.05))
			wid *= math.max(short / len, 0.6)
			len = short
		end
	end
	local cf = Geom.mul(at(base[1], base[2], base[3], tilt, 0, 0), at(0, 0, len * 0.44))
	local mesh = if kind == "fork" then "s_bird_tail_fork" else "s_bird_tail"
	local lead = B:ell(wid, tl * 0.1, len, cf, { col = P.tailCol or "wingTip", mat = "fur", bone = "Tail1", pri = 1.7, role = "tail", name = "Tail", trail = true })
	local members = {}
	if detail >= 2 then
		for _, side in { 1, -1 } do
			local yaw = side * rad(if kind == "fork" then 16 else 22)
			local f = Geom.mul(at(base[1], base[2], base[3], tilt, yaw, 0), at(0, tl * 0.012, len * 0.4))
			table.insert(members, B:ell(wid * 0.45, tl * 0.08, len * (if kind == "fork" then 1.05 else 0.88), f, { col = "secondary", mat = "fur", bone = "Tail1", pri = 3.0, role = "tail", name = "TailSide" }))
		end
	end
	B:sculpt(lead, mesh, members)
	if P.racket and detail >= 2 then
		local ex, ey, ez = Geom.point(cf, 0, 0, len * 0.55)
		B:ell(wid * 0.5, tl * 0.06, len * 0.22, at(ex, ey, ez, tilt, 0, 0), { col = "dark", mat = "fur", bone = "Tail1", pri = 3.0, role = "tail", name = "Racket" })
	end
end

return function(B: any, ctx: any)
	local t = ctx.traits
	local detail = ctx.detail
	local id = string.lower(ctx.result.id)
	local kind, P, baby = profile(id, t)
	P.kind = kind
	if P.wyvern then
		return wyvern(B, ctx, t, id)
	end
	local rng = B.rng
	local bulk = (0.92 + t.durability * 0.025) * rng:jitter(1, 0.04)
	P.bulk = bulk
	local L, H, W = P.body[1] * bulk, P.body[2] * bulk, P.body[3] * bulk
	local pitch = rad(P.pitch)
	-- vertical half-extent of the tilted body, so the legs reach the ground under it
	local hz = math.sqrt((H * 0.5 * cos(pitch)) ^ 2 + (L * 0.5 * sin(pitch)) ^ 2)
	local legLen = P.leg * bulk
	local bodyY = legLen + hz * 0.82
	if P.toy then
		bodyY = hz * 0.95
	end
	local BF = at(0, bodyY, 0, pitch, 0, 0)
	local function bp(x: number, y: number, z: number): { number }
		local a, b, c = Geom.point(BF, x, y, z)
		return { a, b, c }
	end
	B.boneIndex.Body.pos = { 0, bodyY, 0 }
	local mat = if P.bat then "fur" elseif P.ptero then "skin" else "fur"
	local mech = t.robot or t.mechanical
	if mech then
		mat = "metal"
	end
	local body = B:ell(W, H, L, BF, { col = "primary", mat = mat, pri = 1, role = "body", name = "Body", mesh = P.mesh })
	if detail >= 1 and not P.bat and P.breastCol ~= false then
		-- breast / belly patch (pale front), set into the body's lower front
		local bc = Geom.offset(BF, 0, -H * 0.17, -L * 0.16)
		B:ell(W * 0.84, H * 0.74, L * 0.78, bc, { col = P.breastCol or "belly", mat = mat, pri = if P.pitch > 50 then 1.5 else 2.4, role = "detail", name = "Breast", mesh = "s_bird_breast" })
	end
	local _ = body

	-- neck and head
	local s = P.head * bulk * (if baby then 1 else 1)
	local neckBase = bp(0, H * 0.3, -L * 0.4)
	if P.pitch > 45 then
		neckBase = bp(0, H * 0.18, -L * 0.42)
	end
	local hc: { number }
	local neckLen = P.neck * bulk * 1.15
	if neckLen > 0.05 then
		B:bone("Neck", "Body", neckBase[1], neckBase[2], neckBase[3])
		B:setRig("neck", "Neck")
		local up = rad(P.neckUp)
		local nw = H * 0.34 * P.neckW
		local top = { 0, neckBase[2] + cos(up) * neckLen, neckBase[3] - sin(up) * neckLen }
		local neckCol = P.neckCol or (if P.headCol == C.bald then P.headCol else "primary")
		if P.sCurve and detail >= 2 then
			-- S-curve: the lower neck leans back, the upper neck reaches forward
			local mid = { 0, neckBase[2] + neckLen * 0.55, neckBase[3] + neckLen * 0.12 }
			top = { 0, neckBase[2] + neckLen * 0.98, neckBase[3] - neckLen * 0.28 }
			B:limb(neckBase, mid, nw, { col = "primary", mat = mat, bone = "Neck", pri = 1.15, role = "body", name = "Neck", mesh = "s_bird_neck" }, 0.3)
			B:limb(mid, top, nw * 0.8, { col = neckCol, mat = mat, bone = "Neck", pri = 1.16, role = "body", name = "NeckUp", mesh = "s_bird_neck" }, 0.32)
		else
			B:limb(neckBase, top, nw, { col = neckCol, mat = mat, bone = "Neck", pri = 1.15, role = "body", name = "Neck", mesh = "s_bird_neck" }, 0.3)
		end
		hc = { 0, top[2] + s * 0.18, top[3] - s * 0.12 }
		B:bone("Head", "Neck", top[1], top[2], top[3])
	else
		local up = if P.pitch > 45 then s * 0.42 else s * 0.3
		hc = { 0, neckBase[2] + up, neckBase[3] - s * (if P.pitch > 45 then 0.05 else 0.18) }
		B:bone("Head", "Body", neckBase[1], neckBase[2], neckBase[3])
	end
	B:setRig("head", "Head")
	local info
	if P.bat then
		info = Heads.beast(B, { p = { hc[1], hc[2] - s * 0.16, hc[3] + s * 0.14 }, s = s, arch = if P.fox then "canine" else "rodent" }, t)
		local earK = P.earK or 1
		if earK > 1.5 then
			Parts.ears(B, { bone = "Head", x = info.earX, y = info.earY, z = info.earZ, s = s * 0.42 * earK * 0.6, kind = "long", pri = 1.5 })
		else
			Parts.ears(B, { bone = "Head", x = info.earX * 1.05, y = info.earY, z = info.earZ, s = s * 0.62 * earK, kind = "pointy", pri = 1.5 })
		end
		if detail >= 2 and t.fangs ~= false and (string.find(id, "vampire") or (t.power or 5) >= 6) then
			Parts.teeth(B, { bone = "Head", y = info.mouth[2] + s * 0.02, z = info.mouth[3] + s * 0.04, r = s * 0.14, n = 2, h = s * 0.16, pri = 2.6 })
		end
	elseif P.siren then
		info = Heads.person(B, { p = { hc[1], hc[2] - s * 0.5, hc[3] }, s = s * 0.95, eyes = "cute" }, t)
		-- long hair falling behind the face
		B:ell(s * 1.0, s * 1.15, s * 0.82, at(hc[1], hc[2] + s * 0.02, hc[3] + s * 0.18), { col = "secondary", mat = "fur", bone = "Head", pri = 1.4, role = "hair", name = "Hair" })
		if detail >= 2 then
			B:limb({ 0, hc[2] - s * 0.1, hc[3] + s * 0.3 }, { 0, hc[2] - s * 0.95, hc[3] + s * 0.42 }, s * 0.8, { col = "secondary", mat = "fur", bone = "Head", pri = 2.2, role = "hair", name = "HairFall", depth = s * 0.35 }, 0.2)
		end
		if t.crown or string.find(id, "queen") then
			Parts.ears(B, { bone = "Head", x = s * 0.2, y = info.top[2] - s * 0.1, z = info.c[3], s = s * 0.3, kind = "fin", pri = 2.4 })
		end
	else
		info = head(B, P, t, hc, s, detail)
		crest(B, P, info, detail)
		local c, r = info.c, info.r
		if P.ears and detail >= 1 then
			-- owl ear tufts: two feather horns at the top corners of the head
			for _, side in { 1 } do
				feather(B, { side * r[1] * 0.55, c[2] + r[2] * 0.7, c[3] - r[3] * 0.05 }, { side * r[1] * 0.95, c[2] + r[2] * 1.45, c[3] + r[3] * 0.05 }, s * 0.24, "dark", 1.6, true, true)
			end
		end
		if P.comb and detail >= 1 then
			-- rooster comb: a row of red lobes along the crown, wattles under the beak
			local n = if detail >= 3 then 3 else 1
			for i = 1, n do
				local z = c[3] - r[3] * 0.4 + (i - 1) * r[3] * 0.38
				B:ell(s * 0.14, s * (0.42 - math.abs(i - 2) * 0.08), s * 0.3, at(0, c[2] + r[2] * 0.95, z, rad(-10 + i * 12), 0, 0), { col = C.red, mat = "skin", bone = "Head", pri = 1.3 + i * 0.2, role = "crest", name = "Comb" })
			end
		end
		if P.wattle and detail >= 2 then
			B:mell(s * 0.16, s * 0.34, s * 0.22, at(s * 0.08, c[2] - r[2] * 0.75, c[3] - r[3] * 0.62), { col = C.red, mat = "skin", bone = "Head", pri = 2.3, role = "detail", name = "Wattle#" })
		end
		if P.snood and detail >= 2 then
			B:limb({ 0, c[2] + r[2] * 0.35, c[3] - r[3] * 0.85 }, { s * 0.06, c[2] - r[2] * 0.6, c[3] - r[3] * 1.15 }, s * 0.1, { col = C.red, mat = "skin", bone = "Head", pri = 2.6, role = "detail", name = "Snood" }, 0.1)
		end
		if P.balloon and detail >= 1 then
			B:ell(s * 0.9, s * 1.0, s * 0.85, at(0, c[2] - r[2] * 1.3, c[3] - r[3] * 0.25), { col = C.red, mat = "skin", bone = "Head", pri = 1.6, role = "detail", name = "Balloon" })
		end
		if P.beard and detail >= 2 then
			B:ell(s * 0.5, s * 0.55, s * 0.38, at(0, c[2] - r[2] * 0.85, c[3] - r[3] * 0.45), { col = "dark", mat = "fur", bone = "Head", pri = 2.5, role = "detail", name = "Beard" })
		end
	end
	if P.ruff and detail >= 1 then
		-- vulture / condor collar: a fluffy ruff round the base of the neck
		B:ell(W * 0.82, H * 0.42, W * 0.82, at(neckBase[1], neckBase[2] + H * 0.02, neckBase[3] + L * 0.03, pitch * 0.5, 0, 0), { col = P.ruffCol or "belly", mat = "fur", pri = 1.45, role = "detail", name = "Ruff", mesh = "s_bird_fluff" })
	end
	if P.pouch and detail >= 2 then
		B:ell(s * 0.6, s * 1.0, s * 0.55, at(0, neckBase[2] + H * 0.05, neckBase[3] - s * 0.2), { col = C.pinkLeg, mat = "skin", bone = "Neck", pri = 2.4, role = "detail", name = "ThroatPouch" })
	end
	if P.epaulet and detail >= 2 then
		local e = bp(W * 0.45, H * 0.15, -L * 0.15)
		B:mell(W * 0.22, H * 0.2, L * 0.18, at(e[1], e[2], e[3]), { col = C.red, mat = "fur", pri = 2.5, role = "detail", name = "Epaulet#" })
	end

	-- legs
	local hip = bp(W * 0.24, -H * 0.12, L * (P.hipZ or 0.06))
	hip[2] = legLen
	if not P.toy then
		legs(B, P, { hip[1], legLen, hip[3] }, detail, "primary")
	end

	-- wings
	local wk = P.wings
	if wk == "spread" and not (t.flies or t.motion == "Fly") and P.span < 2 and not P.keepSpread then
		wk = "folded" -- a perching bird folds its wings along its flanks
	end
	if wk == "spread" or wk == "bat" then
		local sh = bp(W * 0.36, H * 0.24, -L * 0.14)
		Parts.wings(B, { x = sh[1], y = sh[2], z = sh[3], span = L * P.span * (if wk == "bat" then 0.82 else 0.72), kind = if wk == "bat" then "bat" else "feather",
			feathers = if detail >= 3 then 3 else 2, pri = 1.45, membraneTr = if P.bat or P.ptero then nil else nil })
	elseif wk == "folded" or wk == "stub" then
		-- folded along the flank: shoulder at the front, primaries crossing over the rump
		local stub = wk == "stub"
		local wl = L * (if stub then 0.42 else 0.78)
		local sh = bp(W * 0.42, H * 0.12, -L * 0.2)
		local cen = bp(W * (if stub then 0.47 else 0.44), H * 0.04, -L * 0.2 + wl * 0.46)
		B:mirrorBone("Wing#", "Body", sh[1], sh[2], sh[3])
		B:addRig("wings", { bone = "WingR", side = 1, folded = true })
		B:addRig("wings", { bone = "WingL", side = -1, folded = true })
		B:mell(W * 0.2, H * (if stub then 0.4 else 0.62), wl, at(cen[1], cen[2], cen[3], pitch - rad(if stub then 0 else 8), rad(-5), 0),
			{ col = if stub then "light" else (P.wingCol or "wingTip"), mat = mat, bone = "Wing#", pri = 1.5, role = "wing", name = "Wing#", mesh = if stub then "s_bird_fluff" else "s_wing_folded", meshL = if stub then nil else "s_wing_folded_l" })
	elseif wk == "flipper" then
		local sh = bp(W * 0.42, H * 0.25, -L * 0.05)
		B:mirrorBone("Wing#", "Body", sh[1], sh[2], sh[3])
		B:mlimb(sh, { sh[1] + W * 0.22, sh[2] - H * 0.5, sh[3] + 0.05 }, 0.34 * bulk, { col = "primary", mat = mat, bone = "Wing#", pri = 1.4, role = "wing", depth = 0.12 * bulk, name = "Flipper#" }, 0.1)
		B:addRig("wings", { bone = "WingR", side = 1, flipper = true })
		B:addRig("wings", { bone = "WingL", side = -1, flipper = true })
	end
	if P.cape and detail >= 2 then
		local cp = bp(0, H * 0.3, L * 0.1)
		B:ell(W * 1.2, H * 1.3, W * 0.3, at(cp[1], cp[2] - H * 0.2, cp[3] + W * 0.2, rad(15), 0, 0), { col = C.red, mat = "cloth", pri = 2.2, role = "detail", name = "Cape" })
	end
	if P.branch and detail >= 2 then
		local bt = info.beakTip or info.mouth
		B:limb({ bt[1] - s * 0.3, bt[2], bt[3] + s * 0.05 }, { bt[1] + s * 0.4, bt[2] - s * 0.1, bt[3] + s * 0.1 }, s * 0.08, { col = "leaf", mat = "wood", bone = "Head", pri = 3, role = "detail", name = "Branch" }, 0.05)
		B:mell(s * 0.3, s * 0.08, s * 0.14, at(bt[1] + s * 0.18, bt[2] + s * 0.05, bt[3] + s * 0.05, 0, 0, rad(25)), { col = "leaf", mat = "fur", bone = "Head", pri = 3.2, role = "detail", name = "Leaf#" })
	end

	-- tail
	local tb = bp(0, H * 0.1, L * 0.44)
	tail(B, P, tb, L, pitch, detail)
	if t.fiery or t.element == "Fire" then
		B:emit("embers", "Body")
	end

	B:socket("core", at(0, bodyY, 0), "Body")
	local gait = "bird"
	if kind == "penguin" or kind == "auk" or (kind == "duck" or kind == "goose" or kind == "swan") or (baby and kind ~= "bat" and kind ~= "ptero") then
		gait = "waddle"
	elseif kind == "ratite" or kind == "terror" then
		gait = "biped"
	end
	B:setRig("gait", gait)
end
