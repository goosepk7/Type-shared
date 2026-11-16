--!strict
-- Reads a WordResult into feature flags the body plans use to pick parts: silhouette-hint keywords, tags,
-- behaviours, category, id words and stats. Pure.

local Traits = {}

export type Traits = { [string]: any }

-- keyword (matched on whole-word prefixes in id + hint + tags) -> trait flags
local KEYWORDS: { [string]: { string } } = {
	horn = { "horns" }, horned = { "horns" }, antler = { "antlers" }, unicorn = { "unihorn" }, narwhal = { "unihorn" },
	wing = { "wings" }, winged = { "wings" }, bat = { "batwing" }, feather = { "feathers" }, feathered = { "feathers" },
	neck = { "longNeck" }, giraffe = { "longNeck" }, brachiosaurus = { "longNeck" },
	shell = { "shell" }, shelled = { "shell" }, turtle = { "shell" }, tortoise = { "shell" }, snail = { "shell", "snail" },
	armour = { "armour" }, armor = { "armour" }, armored = { "armour" }, armoured = { "armour" }, plate = { "armour" }, plates = { "armour" }, plated = { "armour" },
	spike = { "spikes" }, spiked = { "spikes" }, spikes = { "spikes" }, spiky = { "spikes" }, quill = { "spikes" }, barbed = { "spikes" }, ridge = { "spikes" },
	mane = { "mane" }, maned = { "mane" }, lion = { "mane" }, fluffy = { "fluffy" }, fur = { "fluffy" }, furry = { "fluffy" }, woolly = { "fluffy" }, fuzzy = { "fluffy" },
	trunk = { "trunk" }, elephant = { "trunk", "bigEars", "tusks" }, mammoth = { "trunk", "tusks", "fluffy" },
	tusk = { "tusks" }, tusks = { "tusks" }, beak = { "beak" }, beaked = { "beak" }, bill = { "beak" },
	fin = { "fins" }, fins = { "fins" }, finned = { "fins" }, flipper = { "flippers" }, flippers = { "flippers" },
	claw = { "claws" }, claws = { "claws" }, pincer = { "pincers" }, pincers = { "pincers" }, crab = { "pincers" }, lobster = { "pincers" }, scorpion = { "pincers", "stinger" },
	stinger = { "stinger" }, sting = { "stinger" }, bee = { "stinger" }, wasp = { "stinger" }, hornet = { "stinger" },
	antenna = { "antennae" }, antennae = { "antennae" },
	tail = { "tail" }, tailed = { "tail" }, fluffytail = { "bushyTail" }, bushy = { "bushyTail" }, fox = { "bushyTail", "pointyEars" }, squirrel = { "bushyTail" },
	ear = { "ears" }, ears = { "ears" }, floppy = { "floppyEars" }, rabbit = { "longEars" }, bunny = { "longEars" }, hare = { "longEars" },
	pointy = { "pointyEars" }, cat = { "pointyEars" }, wolf = { "pointyEars" }, kitten = { "pointyEars" },
	mouse = { "roundEars" }, bear = { "roundEars" }, panda = { "roundEars" }, koala = { "bigEars" }, monkey = { "roundEars" },
	stubby = { "stubby" }, chubby = { "chubby" }, round = { "chubby" }, fat = { "chubby" }, plump = { "chubby" }, belly = { "chubby" },
	long = { "long" }, leggy = { "longLegs" }, legs = { "legs" }, lanky = { "longLegs" },
	jaw = { "bigJaw" }, jaws = { "bigJaw" }, teeth = { "teeth" }, toothy = { "teeth" }, fang = { "fangs" }, fangs = { "fangs" }, tooth = { "teeth" },
	eye = { "eyes" }, cyclops = { "oneEye" }, beholder = { "oneEye" }, glowing = { "glowEyes" },
	crest = { "crest" }, crown = { "crown" }, crowned = { "crown" }, frill = { "frill" }, hood = { "hood" }, cobra = { "hood" },
	sail = { "sail" }, sails = { "sail" }, mast = { "sail" }, ship = { "ship" }, boat = { "boat" },
	wheel = { "wheels" }, wheels = { "wheels" }, tyre = { "wheels" }, tyres = { "wheels" }, tire = { "wheels" }, tires = { "wheels" },
	track = { "treads" }, tracked = { "treads" }, tracks = { "treads" }, treads = { "treads" },
	turret = { "turret" }, cannon = { "cannon" }, gun = { "gun" }, barrel = { "cannon" },
	rotor = { "rotor" }, propeller = { "propeller" }, helicopter = { "rotor" }, chopper = { "rotor" },
	rocket = { "rocket" }, missile = { "rocket" }, jet = { "jet" }, plane = { "plane" }, airplane = { "plane" }, aeroplane = { "plane" },
	window = { "windows" }, windows = { "windows" }, tower = { "tower" }, towers = { "tower" }, castle = { "castle" }, crenellated = { "castle" },
	roof = { "roof" }, house = { "house" }, hut = { "house" }, cabin = { "house" }, wall = { "wall" }, pyramid = { "pyramid" },
	petal = { "petals" }, petals = { "petals" }, flower = { "flower" }, blossom = { "flower" }, rose = { "flower" }, tulip = { "flower" }, sunflower = { "flower" },
	leaf = { "leaves" }, leaves = { "leaves" }, leafy = { "leaves" }, tree = { "tree" }, oak = { "tree" }, pine = { "pine" }, cactus = { "cactus" }, mushroom = { "mushroom" }, toadstool = { "mushroom" },
	vine = { "vine" }, vines = { "vine" }, bush = { "bush" }, shrub = { "bush" },
	blade = { "blade" }, sword = { "sword" }, axe = { "axe" }, hammer = { "hammer" }, mace = { "mace" }, spear = { "spear" }, lance = { "spear" }, trident = { "trident" },
	bow = { "bow" }, crossbow = { "crossbow" }, staff = { "staff" }, wand = { "wand" }, scythe = { "scythe" }, dagger = { "dagger" }, knife = { "dagger" },
	club = { "club" }, bat_ = { "club" }, whip = { "whip" }, shield = { "shield" }, handle = { "handle" }, shaft = { "shaft" }, curved = { "curved" },
	helmet = { "helmet" }, hat = { "hat" }, cape = { "cape" }, cloak = { "cape" }, robe = { "robe" }, beard = { "beard" }, bearded = { "beard" },
	tentacle = { "tentacles" }, tentacles = { "tentacles" }, octopus = { "tentacles" }, squid = { "tentacles" }, jellyfish = { "jelly", "tentacles" }, jelly = { "jelly" },
	funnel = { "funnel" }, tornado = { "funnel" }, twister = { "funnel" }, whirlwind = { "funnel" }, cyclone = { "funnel" }, vortex = { "funnel" },
	storm = { "storm" }, thunder = { "storm" }, lightning = { "storm" }, rain = { "rain" }, snow = { "snow" },
	ring = { "rings" }, rings = { "rings" }, orbit = { "rings" }, planet = { "planet" }, star = { "star" }, sun = { "sun" }, moon = { "moon" },
	robot = { "robot" }, mech = { "robot" }, android = { "robot" }, cyborg = { "robot" }, golem = { "golem" }, skeleton = { "skeleton" }, bone = { "skeleton" }, ghost = { "ghost" },
	slime = { "slime" }, blob = { "slime" }, goo = { "slime" },
	cake = { "cake" }, cupcake = { "cupcake" }, pie = { "pie" }, pizza = { "pizza" }, donut = { "donut" }, doughnut = { "donut" }, burger = { "burger" }, hamburger = { "burger" },
	apple = { "fruit" }, orange = { "fruit" }, cherry = { "fruit" }, peach = { "fruit" }, berry = { "fruit" }, lemon = { "fruit" }, tomato = { "fruit" }, plum = { "fruit" }, melon = { "fruit" }, watermelon = { "fruit", "melon" },
	ice = { "frozen" }, icecream = { "icecream" }, candy = { "candy" }, lollipop = { "lollipop" }, cookie = { "cookie" }, bread = { "bread" }, cheese = { "cheese" }, egg = { "egg" },
	banana = { "banana" }, carrot = { "carrot" }, pumpkin = { "pumpkin" },
	ufo = { "ufo" }, saucer = { "ufo" }, spaceship = { "spaceship" }, train = { "train" }, locomotive = { "train" }, bike = { "bike" }, bicycle = { "bike" }, motorcycle = { "bike" },
	scooter = { "bike" }, submarine = { "submarine" }, balloon = { "balloon" }, sled = { "sled" }, sleigh = { "sled" }, car = { "car" }, truck = { "truck" }, van = { "truck" }, bus = { "truck" },
	tank = { "tank" }, cart = { "cart" }, wagon = { "cart" }, carriage = { "cart" }, chariot = { "cart" }, skateboard = { "board" }, surfboard = { "board" }, raft = { "raft" }, canoe = { "boat" }, kayak = { "boat" }, yacht = { "boat" },
	cloud = { "cloud" }, smoke = { "smoke" }, fog = { "smoke" }, mist = { "smoke" },
	swarm = { "swarm" }, flock = { "swarm" },
	bird = { "beak", "feathers" }, owl = { "beak", "feathers", "bigEyes" }, eagle = { "beak", "feathers" }, penguin = { "beak", "flippers" }, duck = { "beak", "bill" },
	shark = { "shark" }, whale = { "whale" }, dolphin = { "dolphin" }, eel = { "eel" },
	dragon = { "dragon" }, dinosaur = { "dino" }, rex = { "dino", "bigJaw" }, raptor = { "dino" },
	knight = { "helmet", "armour" }, wizard = { "hat", "robe", "beard", "staff" }, witch = { "hat", "robe" }, pirate = { "hat" }, ninja = { "mask" }, king = { "crown", "cape" }, queen = { "crown", "cape" }, princess = { "crown" },
	chef = { "chefhat" }, cowboy = { "hat" }, astronaut = { "helmet" }, viking = { "helmet", "beard" }, samurai = { "helmet", "armour" }, soldier = { "helmet" }, firefighter = { "helmet" },
}

local TAG_TRAITS: { [string]: { string } } = {
	reptile = { "scaly" }, mechanical = { "mechanical" }, robot = { "robot", "mechanical" }, metal = { "mechanical" },
	bird = { "beak", "feathers" }, insect = { "insect" }, aquatic = { "aquatic" }, mammal = { "mammal", "ears" },
	undead = { "undead" }, spooky = { "spooky" }, cute = { "cute" }, mythical = { "mythical" }, flying = { "wings" },
	holy = { "halo" }, royal = { "crown" }, silly = { "silly" }, glowing = { "glowEyes" }, heavy = { "heavy" }, sharp = { "sharp" },
	scifi = { "scifi" }, medieval = { "medieval" }, space = { "space" }, fire = { "fiery" }, frozen = { "frozen" },
}

local function addWords(text: string, out: { [string]: any })
	for word in string.gmatch(string.lower(text), "[%a]+") do
		local hit = KEYWORDS[word]
		if hit == nil and #word > 3 and string.sub(word, -1) == "s" then
			hit = KEYWORDS[string.sub(word, 1, -2)]
		end
		if hit then
			for _, t in hit do
				out[t] = true
			end
		end
	end
end

function Traits.read(r: any): Traits
	local t: Traits = {}
	addWords(r.id or "", t)
	addWords((r.visual and r.visual.silhouetteHint) or "", t)
	-- "long neck" / "long tail" / "long legs"
	local hint = string.lower((r.visual and r.visual.silhouetteHint) or "")
	if string.find(hint, "long neck") then
		t.longNeck = true
	end
	if string.find(hint, "long tail") or string.find(hint, "long spiked tail") then
		t.longTail = true
	end
	if string.find(hint, "long leg") then
		t.longLegs = true
	end
	if string.find(hint, "no wings") or string.find(hint, "wingless") then
		t.noWings = true
	end
	if string.find(hint, "two legs") then
		t.twoLegs = true
	end
	if string.find(hint, "big head") then
		t.bigHead = true
	end
	if string.find(hint, "big eye") or string.find(hint, "huge eye") then
		t.bigEyes = true
	end
	for _, tag in r.tags or {} do
		local tag2 = string.gsub(tag, "^%+", "")
		local hit = TAG_TRAITS[tag2]
		if hit then
			for _, x in hit do
				t[x] = true
			end
		end
		addWords(tag2, t)
	end
	local beh: { [string]: boolean } = {}
	for _, b in r.behaviours or {} do
		beh[b] = true
	end
	t.beh = beh
	if beh.Flies and not t.noWings then
		t.flies = true
	end
	if t.noWings then
		t.wings = nil
	end
	t.swims = beh.Swims == true
	t.category = r.category
	t.element = r.element
	t.size = r.size
	t.power = r.power or 5
	t.speed = r.speed or 5
	t.durability = r.durability or 5
	t.motion = r.visual and r.visual.motionHint or "Walk"
	t.plan = r.visual and r.visual.bodyPlan or "Blob"
	-- wing style
	if t.insect then
		t.wingKind = "insect"
	elseif t.feathers or t.beak then
		t.wingKind = "feather"
	else
		t.wingKind = "bat"
	end
	if t.batwing then
		t.wingKind = "bat"
	end
	-- creature-ness: whether to give a face
	t.alive = (r.category == "Creature" or r.category == "Person" or t.robot or t.golem or t.silly or t.cute or t.slime) and true or false
	return t
end

return Traits
