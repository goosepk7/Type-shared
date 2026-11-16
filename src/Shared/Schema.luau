--!strict
-- Schema: enum lists, validation, repair and clamping. The ONLY path from untrusted data
-- (AI JSON, DataStore cache, admin edits, remote payloads) to a WordResult. Pure Luau.

local Types = require(script.Parent.Types)

type WordResult = Types.WordResult

local Schema = {}

Schema.VERSION = 1

local Enums = {
	Category = { "Creature", "Object", "Weapon", "Vehicle", "Structure", "Element", "Weather", "Disaster", "Food", "Tool", "Abstract", "Person", "Place", "Plant", "Machine" },
	Element = { "Fire", "Water", "Ice", "Lightning", "Earth", "Wind", "Nature", "Light", "Shadow", "Poison", "Metal", "Arcane", "None" },
	Size = { "Tiny", "Small", "Medium", "Large", "Huge", "Colossal" },
	Shape = { "Bolt", "Beam", "Wall", "Cloud", "Rain", "Wave", "Orb", "Blade", "Shield", "Summon", "Mount", "Trap", "Turret", "Zone", "Buff" },
	Behaviour = {
		"Flies", "Swims", "Burrows", "Charges", "Explodes", "Heals", "Blocks", "Pulls", "Pushes", "Freezes", "Burns",
		"Shocks", "Poisons", "Slows", "Stuns", "Spreads", "Follows", "Orbits", "Lingers", "Pierces", "Bounces", "Splits",
		"Grows", "Shrinks", "Teleports", "Invisible", "Reflects", "Steals", "Lures", "Distracts", "Ranged", "Melee",
		"Rideable", "Summons", "Drains", "Confuses", "Knockback", "Lifts",
	},
	BodyPlan = {
		-- generic (v0)
		"Quadruped", "Biped", "Serpent", "Bird", "Fish", "Insect", "Blob", "Vehicle", "Structure", "Weapon", "Orb", "Swarm", "Plant", "Humanoid", "Cloud",
		-- specialised (brief 4)
		"Dragon", "Spider", "Crab", "Octopus", "Worm", "Turtle", "Ghost", "Robot", "Giant", "Knight", "Wizard",
		"Tree", "Flower", "Mushroom", "Cactus",
		"CarWheeled", "Tracked", "Aircraft", "Helicopter", "Boat", "Submarine", "Rocket",
		"Building", "Tower", "Wall", "Gate", "Bridge", "Castle",
		"Sword", "Axe", "Hammer", "Spear", "Bow", "Gun", "Cannon", "Shield", "Staff",
		"Furniture", "Appliance", "Container", "Ball", "Crystal", "Vortex", "Wave", "Food",
	},
	Motion = { "Walk", "Fly", "Swim", "Slither", "Hover", "Roll", "Hop", "Burrow", "Static", "Float", "Spin", "Drive" },
	Source = { "Library", "Cache", "AI", "Admin", "Fallback" },
	CorrectionMethod = { "Exact", "Alias", "Normalized", "Stem", "Misspelling", "Fuzzy", "Phonetic", "MultiWord", "AI" },
	ModifierKind = { "Size", "Count", "Mood", "Quality", "Element", "State", "Motion", "Material" },
	Mood = { "Neutral", "Angry", "Sleepy", "Scared", "Crazy", "Hungry", "Happy", "Sneaky", "Lazy", "Hyper", "Confused", "Sad", "Smug", "Cute" },
}
Schema.Enums = Enums

-- Sets for O(1) membership, built once.
local Sets: { [string]: { [string]: boolean } } = {}
for name, list in Enums do
	local set = {}
	for _, v in list do
		set[v] = true
	end
	Sets[name] = set
end
Schema.Sets = Sets

-- Case-insensitive index so "fire" / "FIRE" from the AI still map.
local Lower: { [string]: { [string]: string } } = {}
for name, list in Enums do
	local m = {}
	for _, v in list do
		m[string.lower(v)] = v
	end
	Lower[name] = m
end

-- Specialised body plan -> generic parent (builders fall back to the parent).
Schema.BodyPlanParent = {
	Dragon = "Quadruped", Spider = "Insect", Crab = "Insect", Octopus = "Blob", Worm = "Serpent", Turtle = "Quadruped",
	Ghost = "Humanoid", Robot = "Humanoid", Giant = "Humanoid", Knight = "Humanoid", Wizard = "Humanoid",
	Tree = "Plant", Flower = "Plant", Mushroom = "Plant", Cactus = "Plant",
	CarWheeled = "Vehicle", Tracked = "Vehicle", Aircraft = "Vehicle", Helicopter = "Vehicle", Boat = "Vehicle",
	Submarine = "Vehicle", Rocket = "Vehicle",
	Building = "Structure", Tower = "Structure", Wall = "Structure", Gate = "Structure", Bridge = "Structure", Castle = "Structure",
	Sword = "Weapon", Axe = "Weapon", Hammer = "Weapon", Spear = "Weapon", Bow = "Weapon", Gun = "Weapon", Cannon = "Weapon",
	Shield = "Weapon", Staff = "Weapon",
	Furniture = "Structure", Appliance = "Structure", Container = "Structure", Ball = "Orb", Crystal = "Orb",
	Vortex = "Cloud", Wave = "Cloud", Food = "Blob",
} :: { [string]: string }

Schema.SizeIndex = { Tiny = 1, Small = 2, Medium = 3, Large = 4, Huge = 5, Colossal = 6 } :: { [string]: number }

Schema.Limits = {
	StatMin = 1,
	StatMax = 10,
	MaxCount = 12,
	MaxBehaviours = 8,
	MaxTags = 8,
	MaxFlavour = 80,
	MaxHint = 60,
	MaxWord = 40, -- single word / id
	MaxPhrase = 80, -- canonical phrase with stacked modifiers
	MaxModifiers = 6,
}

local FALLBACK_VISUAL: Types.Visual = {
	accents = { "sparkle" },
	primaryColour = "#C77DFF",
	secondaryColour = "#FFD6FF",
	bodyPlan = "Blob",
	silhouetteHint = "small round blob, big confused eyes",
	motionHint = "Hop",
	soundHint = "boing",
}

local FALLBACK_LINES = {
	"It has no idea what you meant either.",
	"A small glittery blob. It is trying its best.",
	"Spell unclear. Glitter deployed.",
	"The blob blinks at you. Then sneezes sparkles.",
}

local function clampNum(v: any, lo: number, hi: number, default: number): number
	local n = tonumber(v)
	if n == nil or n ~= n or n == math.huge or n == -math.huge then
		return default
	end
	return math.clamp(n, lo, hi)
end

local function cleanString(v: any, maxLen: number, default: string): string
	if type(v) ~= "string" then
		return default
	end
	-- strip control chars, collapse whitespace
	local s = string.gsub(v, "%c", " ")
	s = string.gsub(s, "%s+", " ")
	s = string.match(s, "^%s*(.-)%s*$") or ""
	if s == "" then
		return default
	end
	if #s > maxLen then
		-- cut on a utf8 boundary
		local cut = utf8.offset(s, maxLen + 1)
		s = string.sub(s, 1, (cut or (maxLen + 1)) - 1)
	end
	return s
end

local function enumOf(kind: string, v: any, default: string): string
	if type(v) ~= "string" then
		return default
	end
	if Sets[kind][v] then
		return v
	end
	return Lower[kind][string.lower(v)] or default
end

local function cleanHex(v: any, default: string): string
	if type(v) ~= "string" then
		return default
	end
	local h = string.match(v, "^#?(%x%x%x%x%x%x)$")
	if h then
		return "#" .. string.upper(h)
	end
	local s = string.match(v, "^#?(%x%x%x)$")
	if s then
		local r, g, b = string.sub(s, 1, 1), string.sub(s, 2, 2), string.sub(s, 3, 3)
		return "#" .. string.upper(r .. r .. g .. g .. b .. b)
	end
	return default
end

local function enumList(kind: string, v: any, max: number): { string }
	local out, seen = {}, {}
	if type(v) == "table" then
		-- accept arrays and sets ({Flies=true})
		local items = {}
		for k, val in v do
			if type(k) == "number" then
				table.insert(items, val)
			elseif val == true then
				table.insert(items, k)
			end
		end
		for _, item in items do
			local e = enumOf(kind, item, "")
			if e ~= "" and not seen[e] then
				seen[e] = true
				table.insert(out, e)
			end
		end
	end
	table.sort(out)
	while #out > max do
		table.remove(out)
	end
	return out
end

local function tagList(v: any): { string }
	local out, seen = {}, {}
	if type(v) == "table" then
		for _, item in v do
			local t = cleanString(item, 24, "")
			t = string.lower(t)
			if t ~= "" and not seen[t] and #out < Schema.Limits.MaxTags then
				seen[t] = true
				table.insert(out, t)
			end
		end
	end
	return out
end

-- Default body plan / motion / shape guesses from category, used by repair when the AI omits fields.
local CATEGORY_DEFAULTS: { [string]: { shape: string, bodyPlan: string, motion: string } } = {
	Creature = { shape = "Summon", bodyPlan = "Quadruped", motion = "Walk" },
	Object = { shape = "Trap", bodyPlan = "Structure", motion = "Static" },
	Weapon = { shape = "Blade", bodyPlan = "Weapon", motion = "Spin" },
	Vehicle = { shape = "Mount", bodyPlan = "Vehicle", motion = "Drive" },
	Structure = { shape = "Wall", bodyPlan = "Structure", motion = "Static" },
	Element = { shape = "Bolt", bodyPlan = "Orb", motion = "Float" },
	Weather = { shape = "Cloud", bodyPlan = "Cloud", motion = "Float" },
	Disaster = { shape = "Zone", bodyPlan = "Cloud", motion = "Spin" },
	Food = { shape = "Trap", bodyPlan = "Blob", motion = "Static" },
	Tool = { shape = "Turret", bodyPlan = "Weapon", motion = "Static" },
	Abstract = { shape = "Buff", bodyPlan = "Orb", motion = "Float" },
	Person = { shape = "Summon", bodyPlan = "Humanoid", motion = "Walk" },
	Place = { shape = "Zone", bodyPlan = "Structure", motion = "Static" },
	Plant = { shape = "Trap", bodyPlan = "Plant", motion = "Static" },
	Machine = { shape = "Turret", bodyPlan = "Vehicle", motion = "Static" },
}
Schema.CategoryDefaults = CATEGORY_DEFAULTS

function Schema.fallback(input: string?): WordResult
	local text = cleanString(input, Schema.Limits.MaxWord, "")
	local line = FALLBACK_LINES[(#text % #FALLBACK_LINES) + 1]
	return {
		schemaVersion = Schema.VERSION,
		id = "glitter blob",
		canonical = "glitter blob",
		input = text,
		confidence = 0,
		source = "Fallback",
		correction = nil,
		category = "Creature",
		element = "Arcane",
		secondaryElement = "None",
		material = nil,
		mood = "Confused",
		size = "Tiny",
		shape = "Summon",
		behaviours = { "Confuses", "Distracts" },
		power = 1,
		speed = 3,
		durability = 1,
		count = 1,
		modifiers = {},
		signature = true,
		synonymGroup = "glitter blob",
		visual = table.clone(FALLBACK_VISUAL),
		flavourText = line,
		tags = { "fallback", "silly" },
	}
end

-- Repair anything table-shaped into a valid WordResult. Never errors. Unknowns -> defaults.
function Schema.repair(raw: any, input: string?): WordResult
	if type(raw) ~= "table" then
		return Schema.fallback(input)
	end
	local id = string.lower(cleanString(raw.id or raw.canonical, Schema.Limits.MaxWord, ""))
	if id == "" then
		return Schema.fallback(input)
	end
	local category = enumOf("Category", raw.category, "Object")
	local defaults = CATEGORY_DEFAULTS[category]
	local v = if type(raw.visual) == "table" then raw.visual else {}

	local correction: Types.Correction? = nil
	if type(raw.correction) == "table" then
		local c = raw.correction
		local alts = {}
		if type(c.alternatives) == "table" then
			for _, a in c.alternatives do
				local s = string.lower(cleanString(a, Schema.Limits.MaxWord, ""))
				if s ~= "" and #alts < 3 then
					table.insert(alts, s)
				end
			end
		end
		correction = {
			method = enumOf("CorrectionMethod", c.method, "AI") :: any,
			from = cleanString(c.from, Schema.Limits.MaxWord, ""),
			to = cleanString(c.to, Schema.Limits.MaxWord, id),
			confidence = clampNum(c.confidence, 0, 1, 0.5),
			alternatives = alts,
		}
	end

	local mods: { Types.AppliedModifier } = {}
	if type(raw.modifiers) == "table" then
		for _, m in raw.modifiers do
			if type(m) == "table" and type(m.id) == "string" and #mods < Schema.Limits.MaxModifiers then
				table.insert(mods, {
					id = string.lower(cleanString(m.id, 24, "")),
					kind = enumOf("ModifierKind", m.kind, "Quality") :: any,
				})
			end
		end
	end

	local L = Schema.Limits
	return {
		schemaVersion = Schema.VERSION,
		id = id,
		canonical = string.lower(cleanString(raw.canonical, L.MaxPhrase, id)),
		input = cleanString(raw.input or input, L.MaxPhrase, id),
		confidence = clampNum(raw.confidence, 0, 1, 0.5),
		source = enumOf("Source", raw.source, "AI") :: any,
		correction = correction,
		category = category :: any,
		element = enumOf("Element", raw.element, "None") :: any,
		secondaryElement = enumOf("Element", raw.secondaryElement, "None") :: any,
		material = (function()
			local m = string.lower(cleanString(raw.material, 24, ""))
			return if m == "" or m == "none" then nil else m
		end)(),
		mood = enumOf("Mood", raw.mood, "Neutral") :: any,
		size = enumOf("Size", raw.size, "Medium") :: any,
		shape = enumOf("Shape", raw.shape, defaults.shape) :: any,
		behaviours = enumList("Behaviour", raw.behaviours, L.MaxBehaviours),
		power = clampNum(raw.power, L.StatMin, L.StatMax, 5),
		speed = clampNum(raw.speed, L.StatMin, L.StatMax, 5),
		durability = clampNum(raw.durability, L.StatMin, L.StatMax, 5),
		count = math.floor(clampNum(raw.count, 1, L.MaxCount, 1)),
		modifiers = mods,
		signature = raw.signature == true,
		synonymGroup = string.lower(cleanString(raw.synonymGroup, L.MaxWord, id)),
		visual = {
			primaryColour = cleanHex(v.primaryColour, "#9AA5B1"),
			secondaryColour = cleanHex(v.secondaryColour, "#E4E7EB"),
			bodyPlan = enumOf("BodyPlan", v.bodyPlan, defaults.bodyPlan) :: any,
			silhouetteHint = cleanString(v.silhouetteHint, L.MaxHint, ""),
			motionHint = enumOf("Motion", v.motionHint, defaults.motion) :: any,
			soundHint = string.lower(cleanString(v.soundHint, 24, "whoosh")),
			accents = tagList(v.accents),
		},
		flavourText = cleanString(raw.flavourText, L.MaxFlavour, ""),
		tags = tagList(raw.tags),
	}
end

-- Strict validation: returns (result, problems). result is the repaired value; problems lists
-- everything that had to be fixed (empty = raw was already valid).
function Schema.validate(raw: any): (WordResult?, { string })
	local problems = {}
	if type(raw) ~= "table" then
		return nil, { "not a table" }
	end
	local fixed = Schema.repair(raw)
	if fixed.source == "Fallback" and raw.source ~= "Fallback" then
		return nil, { "missing id" }
	end
	for _, key in { "category", "element", "size", "shape" } do
		if raw[key] ~= (fixed :: any)[key] then
			table.insert(problems, key .. ": " .. tostring(raw[key]))
		end
	end
	for _, key in { "power", "speed", "durability" } do
		if raw[key] ~= (fixed :: any)[key] then
			table.insert(problems, key .. " out of range: " .. tostring(raw[key]))
		end
	end
	if type(raw.behaviours) ~= "table" or #fixed.behaviours ~= #raw.behaviours then
		table.insert(problems, "behaviours had invalid entries")
	end
	if type(raw.visual) ~= "table" then
		table.insert(problems, "visual missing")
	end
	return fixed, problems
end

function Schema.has(result: WordResult, behaviour: string): boolean
	return table.find(result.behaviours, behaviour) ~= nil
end

function Schema.hasTag(result: WordResult, tag: string): boolean
	return table.find(result.tags, tag) ~= nil
end

local function deepClone<T>(t: T): T
	if type(t) ~= "table" then
		return t
	end
	local out = {}
	for k, v in t :: any do
		out[k] = deepClone(v)
	end
	return out :: any
end

function Schema.clone(result: WordResult): WordResult
	return deepClone(result)
end

-- Strip the unfiltered input before replicating a result to OTHER clients.
function Schema.forBroadcast(result: WordResult): WordResult
	local c = deepClone(result)
	c.input = ""
	if c.correction then
		c.correction.from = ""
	end
	return c
end

function Schema.sizeStep(size: string, steps: number): string
	local i = Schema.SizeIndex[size] or 3
	return Enums.Size[math.clamp(i + steps, 1, #Enums.Size)]
end

return Schema
