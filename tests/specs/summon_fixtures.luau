-- Shared fixtures for the Summon specs and tools/render_blueprint.luau (not a spec: no .spec suffix).
-- Builds WordResults from library JSONL short keys, and synthetic results that exercise every body plan.
local fs = require("@lune/fs")
local serde = require("@lune/serde")

local F = {}

function F.fromShort(Schema: any, e: any): any
	return Schema.repair({
		id = e.w, canonical = e.w, category = e.c, element = e.e, size = e.z, shape = e.s, behaviours = e.b or {},
		power = e.p, speed = e.sp, durability = e.d, count = 1, signature = e.sig == 1, synonymGroup = e.g or e.w,
		source = "Library", confidence = 1,
		visual = { primaryColour = e.pc, secondaryColour = e.sc, bodyPlan = e.bp, silhouetteHint = e.sh, motionHint = e.m, soundHint = e.snd },
		flavourText = e.f, tags = e.t or {},
	})
end

function F.library(Schema: any): { any }
	local out = {}
	if not fs.isDir("data/words") then
		return out
	end
	local files = fs.readDir("data/words")
	table.sort(files)
	for _, name in files do
		if string.match(name, "%.jsonl$") then
			for line in string.gmatch(fs.readFile("data/words/" .. name), "[^\n]+") do
				local ok, e = pcall(serde.decode, "json", line)
				if ok and type(e) == "table" and e.w then
					table.insert(out, F.fromShort(Schema, e))
				end
			end
		end
	end
	return out
end

-- Variants per plan: { id, category, element, tags, hint, behaviours, motion, pc, sc }
F.Variants = {
	Quadruped = {
		{ "wolf", "Creature", "None", { "mammal" }, "pointy ears, bushy tail", { "Melee" }, "Walk", "#7D8590", "#D9DDE2" },
		{ "fire drake", "Creature", "Fire", { "reptile", "mythical" }, "horns, back spikes, long tail", { "Burns" }, "Walk", "#B3261E", "#F2A43A" },
		{ "elephant", "Creature", "None", { "mammal", "heavy" }, "big ears, trunk, tusks", { "Charges" }, "Walk", "#8E8A86", "#C9C2BA" },
		{ "turtle", "Creature", "Water", { "reptile", "aquatic" }, "domed shell, stubby legs", { "Blocks" }, "Walk", "#3E7D4A", "#C2B280" },
		{ "lion", "Creature", "None", { "mammal" }, "mane, tufted tail", { "Melee" }, "Walk", "#C8902E", "#7A4A1E" },
		{ "rabbit", "Creature", "None", { "mammal", "cute" }, "long ears, fluffy tail", { "Bounces" }, "Hop", "#E8DCCB", "#FFFFFF" },
		{ "griffin", "Creature", "Wind", { "mythical", "bird" }, "eagle head, lion body, wings", { "Flies" }, "Fly", "#C28E3A", "#F4F1EA" },
	},
	Biped = {
		{ "raptor", "Creature", "None", { "reptile", "extinct" }, "two legs, big jaw, claws", { "Melee", "Charges" }, "Walk", "#5E7D3A", "#D9C27A" },
		{ "gorilla", "Creature", "None", { "mammal", "heavy" }, "huge arms, round ears", { "Melee" }, "Walk", "#3A3A3F", "#6E6A6A" },
		{ "troll", "Creature", "Earth", { "mythical" }, "big nose, club, hunched", { "Melee", "Knockback" }, "Walk", "#6E8B5A", "#A68A64" },
		{ "kangaroo", "Creature", "None", { "mammal" }, "long ears, big feet, tail", { "Bounces" }, "Hop", "#B8835A", "#E8D2B4" },
		{ "yeti", "Creature", "Ice", { "mythical", "fluffy" }, "fur, horns, big feet", { "Freezes" }, "Walk", "#EEF4FA", "#9AB8D6" },
	},
	Serpent = {
		{ "cobra", "Creature", "Poison", { "reptile" }, "hood, fangs", { "Poisons" }, "Slither", "#6B5A2E", "#E8D27A" },
		{ "sea serpent", "Creature", "Water", { "mythical", "aquatic" }, "fin crest, long body", { "Swims" }, "Swim", "#1F6F8B", "#A6E3E9" },
		{ "worm", "Creature", "Earth", { "silly" }, "segmented pink tube", { "Burrows" }, "Burrow", "#E58FA0", "#F7C6CF" },
		{ "lindworm", "Creature", "Shadow", { "mythical", "reptile" }, "horns, spikes, two clawed forelegs", { "Melee" }, "Slither", "#2E2A44", "#8A6BD1" },
	},
	Bird = {
		{ "eagle", "Creature", "Wind", { "bird" }, "hooked beak, broad wings", { "Flies" }, "Fly", "#5A3E2B", "#F4F1EA" },
		{ "penguin", "Creature", "Ice", { "bird", "cute" }, "flippers, round belly", { "Swims" }, "Walk", "#22252B", "#F5F5F5" },
		{ "parrot", "Creature", "None", { "bird" }, "crest, long tail", { "Flies" }, "Fly", "#D62F2F", "#2F6FD6" },
		{ "wyvern", "Creature", "Poison", { "mythical", "reptile" }, "two legs, bat wings, barbed stinger tail", { "Flies" }, "Fly", "#3E6B2A", "#C7E36B" },
	},
	Fish = {
		{ "goldfish", "Creature", "Water", { "aquatic", "cute" }, "round body, flowing tail", { "Swims" }, "Swim", "#F28A1F", "#FFD08A" },
		{ "swordfish", "Creature", "Water", { "aquatic" }, "long bill, tall fin", { "Pierces" }, "Swim", "#2F4E7A", "#C8D6E6" },
		{ "jellyfish", "Creature", "Lightning", { "aquatic" }, "bell, trailing tentacles", { "Shocks" }, "Float", "#E39BF2", "#FFE1FF" },
		{ "whale", "Creature", "Water", { "aquatic", "mammal" }, "huge body, fluke tail", { "Knockback" }, "Swim", "#3A5A7A", "#D8E4EE" },
	},
	Insect = {
		{ "beetle", "Creature", "Earth", { "insect" }, "shell, horn", { "Blocks" }, "Walk", "#2D5A3A", "#7AC27A" },
		{ "scorpion", "Creature", "Poison", { "insect" }, "pincers, stinger tail", { "Poisons" }, "Walk", "#4A3A2A", "#C9A35A" },
		{ "butterfly", "Creature", "Nature", { "insect", "cute" }, "big colourful wings", { "Flies" }, "Fly", "#3A8BD6", "#FFD23A" },
		{ "spider", "Creature", "Shadow", { "insect", "spooky" }, "eight legs, round body", { "Slows" }, "Walk", "#2A2230", "#B33A3A" },
		{ "ant", "Creature", "None", { "insect" }, "three segments, antennae", { "Melee" }, "Walk", "#7A2E1E", "#3A1A12" },
	},
	Blob = {
		{ "slime", "Creature", "Poison", { "silly" }, "wobbly goo, big eyes", { "Splits" }, "Hop", "#7ED957", "#D8FFB0" },
		{ "cake", "Food", "None", { "sweet", "edible" }, "layered cake, frosting, cherry", { "Lures" }, "Static", "#F6D2E0", "#8A4A2A" },
		{ "pizza", "Food", "Fire", { "edible" }, "slice, melted cheese, pepperoni", { "Lures" }, "Static", "#F4C25A", "#C2412D" },
		{ "donut", "Food", "None", { "sweet" }, "ring, pink frosting, sprinkles", { "Bounces" }, "Roll", "#D9A066", "#F48FB1" },
		{ "apple", "Food", "Nature", { "edible" }, "round fruit, leaf, stem", { "Heals" }, "Roll", "#D62F2F", "#5BA33A" },
		{ "burger", "Food", "None", { "edible" }, "bun, patty, lettuce, cheese", { "Lures" }, "Static", "#D99A4A", "#5A3A1E" },
		{ "ice cream", "Food", "Ice", { "sweet" }, "cone, scoops", { "Freezes" }, "Static", "#F7E1C4", "#F48FB1" },
	},
	Vehicle = {
		{ "car", "Vehicle", "None", { "mechanical", "vehicle" }, "four wheels, rounded roof", { "Charges" }, "Drive", "#D62F2F", "#F2F2F2" },
		{ "pickup truck", "Vehicle", "None", { "mechanical", "vehicle" }, "cab and open bed, big tyres", { "Charges" }, "Drive", "#2F6FD6", "#E8E8E8" },
		{ "tank", "Vehicle", "Metal", { "mechanical" }, "tracked hull, rotating turret, long cannon", { "Ranged" }, "Drive", "#5A6B3A", "#3A4228" },
		{ "sailboat", "Vehicle", "Water", { "vehicle" }, "hull, tall mast, white sail", { "Swims" }, "Swim", "#8A5A33", "#F3ECDD" },
		{ "helicopter", "Vehicle", "Wind", { "mechanical" }, "rotor, tail boom, skids", { "Flies" }, "Fly", "#2E4E3A", "#C9D6CF" },
		{ "airplane", "Vehicle", "Wind", { "mechanical" }, "wings, tail fin, propeller", { "Flies" }, "Fly", "#F2F2F2", "#2F6FD6" },
		{ "train", "Vehicle", "Fire", { "mechanical" }, "steam engine, funnel, cowcatcher", { "Charges" }, "Drive", "#2A2A30", "#C2412D" },
		{ "bicycle", "Vehicle", "None", { "vehicle" }, "two wheels, handlebars", { "Charges" }, "Drive", "#2FA36B", "#2A2A30" },
		{ "submarine", "Vehicle", "Water", { "mechanical" }, "periscope, porthole windows, propeller", { "Swims" }, "Swim", "#F2C22F", "#3A3A3A" },
	},
	Structure = {
		{ "tower", "Structure", "Earth", { "medieval" }, "round tower, crenellations, cone roof", { "Blocks", "Ranged" }, "Static", "#A39E93", "#5A3A6B" },
		{ "house", "Structure", "None", { "home" }, "cottage, pitched roof, chimney", { "Blocks" }, "Static", "#E8D8B4", "#A33A2A" },
		{ "wall", "Structure", "Earth", { "medieval" }, "stone wall, crenellations", { "Blocks" }, "Static", "#8E8A80", "#5E5A52" },
		{ "pyramid", "Structure", "Light", { "ancient" }, "stepped sandstone, gold cap", { "Blocks" }, "Static", "#D9B97A", "#E8B53A" },
		{ "lighthouse", "Structure", "Light", { "sea" }, "striped tower, lantern room", { "Lures" }, "Static", "#F2F2F2", "#D62F2F" },
		{ "windmill", "Structure", "Wind", { "farm" }, "tower, four sails", { "Pushes" }, "Spin", "#E8D8B4", "#8A5A33" },
		{ "igloo", "Structure", "Ice", { "frozen" }, "snow dome, tunnel door", { "Blocks" }, "Static", "#EEF6FA", "#BFD8E8" },
	},
	Weapon = {
		{ "sword", "Weapon", "Metal", { "medieval", "sharp" }, "long blade, cross guard", { "Melee" }, "Spin", "#C9D2DB", "#8A5A33" },
		{ "axe", "Weapon", "None", { "medieval", "sharp" }, "broad head on wooden haft", { "Melee" }, "Spin", "#9AA5B1", "#6B4A2E" },
		{ "hammer", "Weapon", "Lightning", { "heavy" }, "big block head, short handle", { "Knockback" }, "Spin", "#7C8794", "#6B4A2E" },
		{ "bow", "Weapon", "Nature", { "ranged" }, "curved limbs, string", { "Ranged" }, "Static", "#8A5A33", "#E8E1D0" },
		{ "staff", "Weapon", "Arcane", { "magic" }, "long staff, glowing crystal", { "Ranged" }, "Float", "#5A3A24", "#C77DFF" },
		{ "spear", "Weapon", "None", { "medieval", "sharp" }, "leaf blade on long wooden shaft", { "Pierces" }, "Spin", "#9AA5B1", "#8A5A33" },
		{ "shield", "Weapon", "Metal", { "medieval" }, "round shield, boss, rim", { "Blocks", "Reflects" }, "Static", "#3A5AA3", "#E8B53A" },
		{ "scythe", "Weapon", "Shadow", { "spooky" }, "curved blade on long shaft", { "Melee" }, "Spin", "#2A2A30", "#B8C2CC" },
		{ "gun", "Weapon", "None", { "ranged" }, "barrel, grip, trigger", { "Ranged" }, "Static", "#3C434C", "#8A5A33" },
		{ "wand", "Weapon", "Arcane", { "magic" }, "thin stick, star tip", { "Ranged" }, "Float", "#5A3A24", "#FFD23A" },
	},
	Orb = {
		{ "fireball", "Element", "Fire", {}, "blazing sphere", { "Explodes", "Burns" }, "Float", "#FF5A1F", "#FFD23A" },
		{ "planet", "Object", "Earth", { "space" }, "sphere with rings", { "Pulls" }, "Spin", "#D99A4A", "#F4E1B4" },
		{ "black hole", "Disaster", "Shadow", { "space" }, "dark core, accretion ring", { "Pulls" }, "Spin", "#120A1E", "#A974FF" },
		{ "bubble", "Element", "Water", {}, "clear sphere", { "Bounces" }, "Float", "#9FD8F2", "#FFFFFF" },
		{ "crystal", "Object", "Arcane", { "magic" }, "faceted gem", { "Reflects" }, "Float", "#B65CFF", "#FFE6FF" },
	},
	Swarm = {
		{ "bees", "Creature", "Nature", { "insect" }, "buzzing cloud of bees", { "Stings" }, "Fly", "#F2C22F", "#2A2A30" },
		{ "bats", "Creature", "Shadow", { "spooky" }, "flock of bats", { "Flies" }, "Fly", "#2A2230", "#7A5AA3" },
		{ "fireflies", "Creature", "Light", { "insect" }, "glowing dots", { "Distracts" }, "Hover", "#FFE58A", "#7ED957" },
		{ "piranhas", "Creature", "Water", { "aquatic" }, "school of toothy fish", { "Swims" }, "Swim", "#8E8A86", "#D62F2F" },
	},
	Plant = {
		{ "tree", "Plant", "Nature", { "plant" }, "thick trunk, round canopy", { "Blocks" }, "Static", "#4E9A3A", "#6B4A2E" },
		{ "sunflower", "Plant", "Light", { "plant" }, "tall stem, big yellow petals", { "Heals" }, "Static", "#F2C22F", "#5A3A1E" },
		{ "cactus", "Plant", "Earth", { "plant", "sharp" }, "arms, spines, flower", { "Pierces" }, "Static", "#3E8A4A", "#F48FB1" },
		{ "mushroom", "Plant", "Poison", { "plant" }, "spotted cap, stalk", { "Poisons" }, "Static", "#D62F2F", "#F5F5F5" },
		{ "pine tree", "Plant", "Ice", { "plant" }, "tall cone of needles", { "Blocks" }, "Static", "#2F6E3A", "#6B4A2E" },
		{ "venus flytrap", "Plant", "Nature", { "plant", "carnivorous" }, "toothy jaw leaves", { "Melee" }, "Static", "#5BA33A", "#D62F2F" },
	},
	Humanoid = {
		{ "chef", "Person", "Fire", { "person" }, "tall white hat, apron", { "Heals" }, "Walk", "#F5F5F5", "#2A2A30" },
		{ "ninja", "Person", "Shadow", { "person" }, "mask, headband, sword", { "Melee" }, "Walk", "#22252B", "#D62F2F" },
		{ "astronaut", "Person", "None", { "space" }, "helmet visor, backpack", { "Flies" }, "Float", "#F2F2F2", "#2F6FD6" },
		{ "viking", "Person", "Ice", { "person" }, "horned helmet, beard, axe", { "Melee" }, "Walk", "#8A5A33", "#9AA5B1" },
		{ "skeleton", "Creature", "Shadow", { "undead", "spooky" }, "bones, glowing eyes", { "Melee" }, "Walk", "#E8E1D0", "#7ED957" },
		{ "king", "Person", "Light", { "royal" }, "crown, red cape, sceptre", { "Summons" }, "Walk", "#B3261E", "#E8B53A" },
	},
	Cloud = {
		{ "tornado", "Disaster", "Wind", { "storm" }, "tall funnel, debris ring at base", { "Lifts", "Pulls" }, "Spin", "#8A9BA8", "#DCE6EC" },
		{ "storm cloud", "Weather", "Lightning", { "storm" }, "dark cloud, lightning", { "Shocks" }, "Float", "#4A5568", "#FDE047" },
		{ "rain cloud", "Weather", "Water", {}, "grey cloud, rain", { "Slows" }, "Float", "#9AA5B1", "#5AB0F2" },
		{ "ghost", "Creature", "Shadow", { "spooky", "undead" }, "sheet ghost, wavy tail", { "Invisible" }, "Float", "#F2F2F7", "#8A6BD1" },
		{ "smoke", "Element", "None", {}, "billowing puffs", { "Confuses" }, "Float", "#7A7A80", "#B8B8BE" },
	},
}

local SIZES = { "Tiny", "Small", "Medium", "Large", "Huge", "Colossal" }
F.Sizes = SIZES

function F.synthetic(Schema: any, plan: string, size: string, variant: number): any
	local list = F.Variants[plan]
	local v = list[(variant - 1) % #list + 1]
	return Schema.repair({
		id = v[1], canonical = v[1], category = v[2], element = v[3], size = size, shape = "Summon", behaviours = v[6],
		power = 5, speed = 5, durability = 5, count = 1, source = "Library", confidence = 1,
		visual = { primaryColour = v[8], secondaryColour = v[9], bodyPlan = plan, silhouetteHint = v[5], motionHint = v[7], soundHint = "roar" },
		flavourText = "", tags = v[4],
	})
end

-- Representative results for each signature (id, plan, category, element, tags, hint, motion, pc, sc, size)
F.SignatureWords = {
	{ "dragon", "Quadruped", "Creature", "Fire", { "mythical", "reptile" }, "winged reptile, horns, long spiked tail", "Fly", "#B3261E", "#F2A43A", "Huge" },
	{ "shark", "Fish", "Creature", "Water", { "aquatic" }, "torpedo body, tall dorsal fin, toothy grin", "Swim", "#5E7489", "#EEF2F5", "Large" },
	{ "t rex", "Biped", "Creature", "None", { "reptile", "extinct" }, "huge jaw, tiny arms, thick tail", "Walk", "#4F6B3A", "#C9B27A", "Huge" },
	{ "phoenix", "Bird", "Creature", "Fire", { "mythical", "bird" }, "flaming wings, long tail plumes", "Fly", "#FF5A1F", "#FFD23A", "Large" },
	{ "kraken", "Fish", "Creature", "Water", { "mythical", "aquatic" }, "giant squid, many tentacles", "Swim", "#7A2E4A", "#E8A3B8", "Colossal" },
	{ "golem", "Biped", "Creature", "Earth", { "mythical", "heavy" }, "boulder body, glowing runes", "Walk", "#7A746A", "#7ED957", "Huge" },
	{ "robot", "Humanoid", "Machine", "Metal", { "robot", "mechanical" }, "boxy body, antenna, visor eyes", "Walk", "#9AA5B1", "#2FA3F2", "Medium" },
	{ "wizard", "Humanoid", "Person", "Arcane", { "magic" }, "pointy hat, long beard, staff", "Walk", "#3A3AA3", "#E8B53A", "Medium" },
	{ "knight", "Humanoid", "Person", "Metal", { "medieval" }, "plate armour, plumed helmet, sword and shield", "Walk", "#B8C2CC", "#B3261E", "Medium" },
	{ "pirate ship", "Vehicle", "Vehicle", "Water", { "vehicle" }, "wooden hull, sails, cannons", "Swim", "#6B4A2E", "#F3ECDD", "Huge" },
	{ "tank", "Vehicle", "Vehicle", "Metal", { "mechanical" }, "tracked hull, turret, long cannon", "Drive", "#5A6B3A", "#3A4228", "Large" },
	{ "castle", "Structure", "Structure", "Earth", { "medieval" }, "towers, gate, flags", "Static", "#A39E93", "#2F5AA3", "Colossal" },
	{ "rocket", "Vehicle", "Vehicle", "Fire", { "space" }, "tall body, fins, nose cone, flame", "Fly", "#F2F2F2", "#D62F2F", "Large" },
	{ "ufo", "Vehicle", "Vehicle", "Arcane", { "space" }, "flying saucer, dome, lights", "Hover", "#9AA5B1", "#7ED957", "Large" },
	{ "cat", "Quadruped", "Creature", "None", { "mammal", "cute" }, "pointy ears, whiskers, curled tail", "Walk", "#E8964A", "#FFF1E0", "Small" },
	{ "dog", "Quadruped", "Creature", "None", { "mammal", "cute" }, "floppy ears, wagging tail", "Walk", "#B8835A", "#F4E6D0", "Small" },
	{ "bee", "Insect", "Creature", "Nature", { "insect", "cute" }, "striped fuzzy body, stinger", "Fly", "#F2C22F", "#2A2A30", "Tiny" },
	{ "octopus", "Fish", "Creature", "Water", { "aquatic" }, "round head, eight curling arms", "Swim", "#E2584A", "#FFC2B8", "Medium" },
	{ "unicorn", "Quadruped", "Creature", "Light", { "mythical" }, "spiral horn, flowing mane", "Walk", "#F7F3FF", "#C77DFF", "Large" },
	{ "cannon", "Weapon", "Weapon", "Fire", { "medieval", "heavy" }, "barrel on wheeled carriage", "Static", "#3C434C", "#6B4A2E", "Medium" },
	{ "glitter blob", "Blob", "Creature", "Arcane", { "fallback", "silly" }, "small round blob, big confused eyes", "Hop", "#C77DFF", "#FFD6FF", "Tiny" },
}

function F.signatureResult(Schema: any, s: any, size: string?): any
	return Schema.repair({
		id = s[1], canonical = s[1], category = s[3], element = s[4], size = size or s[10], shape = "Summon",
		behaviours = {}, power = 7, speed = 5, durability = 6, count = 1, signature = true, source = "Library", confidence = 1,
		visual = { primaryColour = s[8], secondaryColour = s[9], bodyPlan = s[2], silhouetteHint = s[6], motionHint = s[7], soundHint = "roar" },
		flavourText = "", tags = s[5],
	})
end

-- One representative word per specialised plan (brief 4): plan -> variant row (same layout as F.Variants).
F.Special = {
	Dragon = { "bone dragon", "Creature", "Shadow", { "mythical", "undead" }, "ribcage body, tattered wings", { "Flies" }, "Fly", "#E8E1D0", "#7ED957" },
	Spider = { "tarantula", "Creature", "Poison", { "spooky" }, "hairy eight legs", { "Poisons" }, "Walk", "#4A3426", "#D9822B" },
	Crab = { "crab", "Creature", "Water", { "aquatic" }, "wide shell, big claws", { "Melee" }, "Walk", "#D9482B", "#F4C29A" },
	Octopus = { "squid", "Creature", "Water", { "aquatic" }, "long mantle, tentacles", { "Pulls" }, "Swim", "#E8B4C8", "#FFFFFF" },
	Worm = { "earthworm", "Creature", "Earth", { "silly" }, "pink segments", { "Burrows" }, "Burrow", "#E58FA0", "#F7C6CF" },
	Turtle = { "tortoise", "Creature", "Earth", { "reptile" }, "high domed shell", { "Blocks" }, "Walk", "#6B7D3A", "#C2A35A" },
	Ghost = { "phantom", "Creature", "Shadow", { "spooky" }, "floating sheet", { "Invisible" }, "Float", "#F2F2F7", "#8A6BD1" },
	Robot = { "mech", "Machine", "Metal", { "robot" }, "boxy armour, visor", { "Ranged" }, "Walk", "#5A6B7A", "#F2C22F" },
	Giant = { "ogre", "Creature", "Earth", { "mythical" }, "huge, club", { "Knockback" }, "Walk", "#7A8B4A", "#6B4A2E" },
	Knight = { "paladin", "Person", "Light", { "holy" }, "shining armour", { "Heals" }, "Walk", "#E8E8F0", "#E8B53A" },
	Wizard = { "warlock", "Person", "Shadow", { "magic" }, "dark robe, hat", { "Drains" }, "Walk", "#2A1A3A", "#7ED957" },
	Tree = { "oak", "Plant", "Nature", { "plant" }, "broad canopy", { "Blocks" }, "Static", "#4E9A3A", "#6B4A2E" },
	Flower = { "rose", "Plant", "Nature", { "plant" }, "red petals, thorny stem", { "Heals" }, "Static", "#D62F4A", "#2F6E2A" },
	Mushroom = { "toadstool", "Plant", "Poison", { "plant" }, "red spotted cap", { "Poisons" }, "Static", "#D62F2F", "#F5F5F5" },
	Cactus = { "saguaro", "Plant", "Earth", { "plant" }, "tall with arms", { "Pierces" }, "Static", "#3E8A4A", "#F48FB1" },
	CarWheeled = { "race car", "Vehicle", "Fire", { "vehicle" }, "low, spoiler", { "Charges" }, "Drive", "#D62F2F", "#F2C22F" },
	Tracked = { "bulldozer", "Machine", "Earth", { "mechanical" }, "tracks, blade", { "Pushes" }, "Drive", "#F2C22F", "#2A2A30" },
	Aircraft = { "jet", "Vehicle", "Wind", { "mechanical" }, "swept wings", { "Flies" }, "Fly", "#9AA5B1", "#2F6FD6" },
	Helicopter = { "chopper", "Vehicle", "Wind", { "mechanical" }, "rotor", { "Flies" }, "Fly", "#C2412D", "#F2F2F2" },
	Boat = { "canoe", "Vehicle", "Water", { "vehicle" }, "wooden hull", { "Swims" }, "Swim", "#8A5A33", "#F3ECDD" },
	Submarine = { "u boat", "Vehicle", "Water", { "mechanical" }, "periscope", { "Swims" }, "Swim", "#3A4A5A", "#F2C22F" },
	Rocket = { "missile", "Weapon", "Fire", { "explosive" }, "fins, nose cone", { "Explodes" }, "Fly", "#F2F2F2", "#D62F2F" },
	Building = { "cottage", "Structure", "None", { "home" }, "pitched roof", { "Blocks" }, "Static", "#E8D8B4", "#A33A2A" },
	Tower = { "watchtower", "Structure", "Earth", { "medieval" }, "round, crenellations", { "Ranged" }, "Static", "#A39E93", "#5A3A6B" },
	Wall = { "rampart", "Structure", "Earth", { "medieval" }, "thick stone wall", { "Blocks" }, "Static", "#8E8A80", "#5E5A52" },
	Gate = { "portal", "Structure", "Arcane", { "magic" }, "stone ring, glowing", { "Teleports" }, "Static", "#8E8A80", "#C77DFF" },
	Bridge = { "bridge", "Structure", "None", {}, "arched planks", { "Blocks" }, "Static", "#8A5A33", "#5E5A52" },
	Castle = { "fortress", "Structure", "Earth", { "medieval" }, "towers, keep", { "Blocks" }, "Static", "#A39E93", "#2F5AA3" },
	Sword = { "katana", "Weapon", "Metal", { "sharp" }, "curved blade", { "Melee" }, "Spin", "#D9E2EA", "#2A2A30" },
	Axe = { "battle axe", "Weapon", "None", { "sharp" }, "double head", { "Melee" }, "Spin", "#9AA5B1", "#6B4A2E" },
	Hammer = { "warhammer", "Weapon", "Lightning", { "heavy" }, "big head", { "Knockback" }, "Spin", "#7C8794", "#6B4A2E" },
	Spear = { "trident", "Weapon", "Water", { "sharp" }, "three prongs", { "Pierces" }, "Spin", "#E8B53A", "#3A5AA3" },
	Bow = { "crossbow", "Weapon", "None", { "ranged" }, "stock, limbs", { "Ranged" }, "Static", "#6B4A2E", "#9AA5B1" },
	Gun = { "laser blaster", "Weapon", "Light", { "scifi" }, "glowing coils", { "Ranged" }, "Static", "#F2F2F2", "#2FA3F2" },
	Cannon = { "cannon", "Weapon", "Fire", { "heavy" }, "barrel on carriage", { "Ranged" }, "Static", "#3C434C", "#6B4A2E" },
	Shield = { "round shield", "Weapon", "Metal", { "medieval" }, "round shield, boss", { "Blocks" }, "Static", "#8A5A33", "#9AA5B1" },
	Staff = { "magic staff", "Weapon", "Arcane", { "magic" }, "crystal orb", { "Ranged" }, "Float", "#5A3A24", "#C77DFF" },
	Furniture = { "throne", "Object", "Light", { "royal" }, "golden seat", { "Blocks" }, "Static", "#E8B53A", "#B3261E" },
	Appliance = { "toaster", "Machine", "Fire", { "kitchen" }, "two slots, lever", { "Burns" }, "Static", "#B8C2CC", "#2A2A30" },
	Container = { "treasure chest", "Object", "None", { "loot" }, "wooden chest, gold bands", { "Lures" }, "Static", "#8A5A33", "#E8B53A" },
	Ball = { "beach ball", "Object", "Water", { "toy" }, "striped panels", { "Bounces" }, "Roll", "#F2F2F2", "#D62F2F" },
	Crystal = { "amethyst", "Object", "Arcane", { "magic" }, "purple shards", { "Reflects" }, "Float", "#9B5CFF", "#E6CCFF" },
	Vortex = { "whirlwind", "Disaster", "Wind", { "storm" }, "spinning funnel", { "Lifts", "Pulls" }, "Spin", "#B8C8D8", "#E8F0F8" },
	Wave = { "tsunami", "Disaster", "Water", { "natural" }, "towering wave", { "Knockback" }, "Static", "#1F6FB8", "#BFE6FF" },
	Food = { "hamburger", "Food", "None", { "edible" }, "bun, patty", { "Lures" }, "Static", "#D99A4A", "#5A3A1E" },
}

function F.special(Schema: any, plan: string, size: string, mood: string?): any
	local v = F.Special[plan]
	return Schema.repair({
		id = v[1], canonical = v[1], category = v[2], element = v[3], size = size, shape = "Summon", behaviours = v[6],
		power = 6, speed = 5, durability = 6, count = 1, source = "Library", confidence = 1, mood = mood,
		visual = { primaryColour = v[8], secondaryColour = v[9], bodyPlan = plan, silhouetteHint = v[5], motionHint = v[7], soundHint = "roar" },
		flavourText = "", tags = v[4],
	})
end


-- Random "base x material x modifiers" phrases (gallery + z-fighting sweep). Bases mix every plan fixture and
-- library entries; materials come from Library (all 250) and modifiers from the Modifiers vocabulary.
-- Returns WordResults with .phrase set to the canonical text.
function F.phrases(Schema: any, n: number, seed: number?, load: any?): { any }
	local ld = load or require("../loader")
	local Modifiers = ld("src/Shared/Modifiers")
	local Library = ld("src/Shared/Library")
	local Rng = ld("src/Shared/Summon/Rng")
	local rng = Rng.new(seed or 1)
	local bases = {}
	for _, plan in Schema.Enums.BodyPlan do
		if F.Variants[plan] then
			for v = 1, #F.Variants[plan] do
				table.insert(bases, F.synthetic(Schema, plan, "Medium", v))
			end
		elseif F.Special[plan] then
			table.insert(bases, F.special(Schema, plan, "Medium"))
		end
	end
	for _, s in F.SignatureWords do
		table.insert(bases, F.signatureResult(Schema, s, "Medium"))
	end
	local lib = F.library(Schema)
	for _ = 1, math.min(#lib, 120) do
		table.insert(bases, lib[rng:int(1, #lib)])
	end
	local mats = {}
	for w, id in Library.materialWords() do
		if w == id then
			table.insert(mats, id)
		end
	end
	table.sort(mats)
	local byKind: { [string]: { any } } = {}
	for _, m in Modifiers.all() do
		if m.kind ~= "Material" and m.kind ~= "Count" then
			byKind[m.kind] = byKind[m.kind] or {}
			table.insert(byKind[m.kind], m)
		end
	end
	local kinds = { "Mood", "Quality", "Element", "State", "Size", "Motion" }
	local out = {}
	for i = 1, n do
		local base = bases[rng:int(1, #bases)]
		local mods = {}
		-- 85% get a material; 1-2 other modifiers, mood/quality most often
		if rng:chance(0.85) and #mats > 0 then
			local mm = Modifiers.material(mats[rng:int(1, #mats)])
			if mm then
				table.insert(mods, mm)
			end
		end
		for _ = 1, rng:int(1, 2) do
			local k = if rng:chance(0.6) then kinds[rng:int(1, 2)] else kinds[rng:int(3, #kinds)]
			local list = byKind[k]
			if list and #list > 0 then
				table.insert(mods, list[rng:int(1, #list)])
			end
		end
		local r = Modifiers.apply(base, mods)
		r.phrase = Modifiers.canonical(base.id, mods)
		r.count = 1
		out[i] = r
	end
	return out
end

return F
