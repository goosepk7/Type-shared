--!strict
-- Prompt + output contract for the word interpreter model. The system prompt is long and STABLE
-- (schema, enums, materials, modifiers, balance bands, safety rules, ~20 worked examples) so the
-- provider caches it (cache_control on the system block; Haiku 5.5 caches prefixes >= 512 tokens):
-- each request then pays full price only for the short list of new phrases.

local Runtime = require(script.Parent.Parent.Runtime)

local Prompt = {}

Prompt.TOOL_NAME = "submit_words"

-- Copied from docs/LIBRARY_AUTHORING.md "Balance bands". Also enforced in code (Prompt.clampPower).
Prompt.PowerBands = {
	Tiny = { 1, 3 },
	Small = { 2, 4 },
	Medium = { 3, 6 },
	Large = { 5, 7 },
	Huge = { 6, 9 },
	Colossal = { 8, 10 },
} :: { [string]: { number } }

local BAND_TABLE = [[
| size | typical power | examples |
|---|---|---|
| Tiny | 1-3 | ant, pebble, candy |
| Small | 2-4 | cat, dagger, cupcake |
| Medium | 3-6 | wolf, sword, car |
| Large | 5-7 | bear, cannon, tank |
| Huge | 6-9 | elephant, dragon, tornado |
| Colossal | 8-10 | kaiju, black hole, asteroid, tsunami |]]

-- Order matters: the model writes fields in this order (schema properties and examples both use it), so the
-- identifying fields come first and the judgement fields (stats, flavour, confidence) come after it has
-- described the thing. Roblox's JSONEncode does not keep key order, hence Prompt.schemaJson below.
local ITEM_FIELDS = {
	"key", "refused", "id", "corrected", "category", "shape", "element", "secondaryElement", "material",
	"size", "mood", "bodyPlan", "silhouetteHint", "behaviours", "power", "speed", "durability", "primaryColour",
	"secondaryColour", "motionHint", "soundHint", "accents", "tags", "flavourText", "confidence",
}
Prompt.ItemFields = ITEM_FIELDS
local schemaJsonCache: string? = nil

-- Used when the Materials module isn't available. Generic, brand-free.
local BUILTIN_MATERIALS = {
	"wood", "stone", "metal", "gold", "silver", "iron", "ice", "glass", "crystal", "lava", "fire", "water", "cloud",
	"sand", "mud", "slime", "jelly", "rubber", "plastic", "paper", "cardboard", "fabric", "wool", "leather", "bone",
	"candy", "chocolate", "cheese", "spaghetti", "bread", "pizza", "cake", "marshmallow", "popcorn", "bubbles",
	"lightning", "shadow", "light", "leaves", "flowers", "moss", "coral", "honey", "pudding", "toast", "toy bricks",
}
local BUILTIN_MODIFIERS = {
	"Size: tiny, small, big, giant, huge, colossal, mini, mega", "Count: two, three, swarm of, army of, pack of",
	"Mood: angry, sleepy, scared, crazy, hungry, happy, sneaky, lazy, hyper, confused, sad, smug, cute",
	"Quality: golden, rainbow, ancient, royal, robot, zombie, ghost, baby, king, legendary",
	"Element: fire, ice, lightning, poison, shadow, holy, earth, wind, water, nature, metal, arcane",
	"State: frozen, burning, rusty, broken, glowing, invisible, inflatable", "Motion: flying, swimming, rolling, spinning",
	"Material: '<material> <thing>' or '<thing> made of <material>'",
}

-- Worked examples. Library-sourced examples are added in front of these (Config.AI.FewShotIds).
local function ex(t: { [string]: any }): { [string]: any }
	local base = {
		refused = false, corrected = "", confidence = 0.9, secondaryElement = "None", material = "", mood = "Neutral",
		accents = {}, tags = {},
	}
	for k, v in t do
		base[k] = v
	end
	return base
end

local BUILTIN_EXAMPLES = {
	ex({ key = "tornado", id = "tornado", category = "Disaster", element = "Wind", size = "Huge", shape = "Zone", behaviours = { "Knockback", "Lifts", "Lingers", "Pulls", "Spreads" }, power = 8, speed = 6, durability = 5, primaryColour = "#8A9BA8", secondaryColour = "#DCE6EC", bodyPlan = "Vortex", silhouetteHint = "tall funnel, debris ring at base", motionHint = "Spin", soundHint = "howl", flavourText = "Picks things up. Puts them down far away.", tags = { "storm", "natural" } }),
	ex({ key = "asteroid", id = "asteroid", category = "Disaster", element = "Earth", secondaryElement = "Fire", size = "Colossal", shape = "Orb", behaviours = { "Burns", "Explodes", "Knockback" }, power = 9, speed = 7, durability = 8, primaryColour = "#5B4636", secondaryColour = "#FF7A1A", bodyPlan = "Orb", silhouetteHint = "cratered rock, flaming tail", motionHint = "Fly", soundHint = "boom", accents = { "flames", "smoke" }, flavourText = "Special delivery from outer space.", tags = { "space", "explosive", "heavy" } }),
}

local EDGE_EXAMPLES = {
	ex({ key = "toastr", id = "toaster", corrected = "toaster", confidence = 0.85, category = "Machine", element = "Fire", size = "Small", shape = "Turret", behaviours = { "Burns", "Ranged" }, power = 3, speed = 4, durability = 4, primaryColour = "#C0C4C8", secondaryColour = "#E8562A", bodyPlan = "Appliance", silhouetteHint = "boxy chrome body, two slots, lever", motionHint = "Static", soundHint = "ding", flavourText = "Launches golden-brown justice.", tags = { "kitchen", "mechanical" } }),
	ex({ key = "blorpleflump", id = "blorpleflump", confidence = 0.45, category = "Creature", element = "Water", mood = "Happy", size = "Small", shape = "Summon", behaviours = { "Bounces", "Confuses" }, power = 2, speed = 4, durability = 3, primaryColour = "#4FC3B5", secondaryColour = "#D9FFF8", bodyPlan = "Blob", silhouetteHint = "wobbly jelly body, tiny feet", motionHint = "Hop", soundHint = "boing", flavourText = "Nobody knows what it is. It seems happy.", tags = { "silly" } }),
	ex({ key = "shreks toenail", id = "swamp ogre toenail", corrected = "swamp ogre toenail", confidence = 0.7, category = "Object", element = "Poison", size = "Tiny", shape = "Bolt", behaviours = { "Poisons", "Ranged", "Distracts" }, power = 2, speed = 6, durability = 2, primaryColour = "#9C8B4A", secondaryColour = "#5E7D2E", bodyPlan = "Weapon", silhouetteHint = "curved yellowed nail clipping", motionHint = "Spin", soundHint = "squelch", accents = { "stink lines" }, flavourText = "Fresh from the swamp. Do not sniff.", tags = { "gross", "silly" } }),
	ex({ key = "spaghetti dragon", id = "dragon", confidence = 0.9, category = "Creature", element = "Fire", material = "spaghetti", size = "Huge", shape = "Summon", behaviours = { "Burns", "Flies", "Lures", "Ranged" }, power = 7, speed = 5, durability = 5, primaryColour = "#F2C46D", secondaryColour = "#C8361B", bodyPlan = "Dragon", silhouetteHint = "noodle-strand body, meatball eyes, sauce wings", motionHint = "Fly", soundHint = "roar", accents = { "sauce drips", "steam" }, flavourText = "Al dente and very angry about it.", tags = { "food", "mythical", "silly" } }),
	ex({ key = "angry sleepy volcano", id = "volcano", confidence = 0.85, category = "Disaster", element = "Fire", secondaryElement = "Earth", mood = "Angry", size = "Colossal", shape = "Zone", behaviours = { "Burns", "Explodes", "Lingers", "Spreads" }, power = 8, speed = 2, durability = 9, primaryColour = "#4A3B35", secondaryColour = "#FF5A1F", bodyPlan = "Structure", silhouetteHint = "cone mountain, glowing crater, lava streams", motionHint = "Static", soundHint = "rumble", accents = { "scowl", "droopy eyelids", "smoke" }, flavourText = "Woke up on the wrong side of the crust.", tags = { "natural", "explosive" } }),
	ex({ key = "fire ice golem", id = "golem", confidence = 0.8, category = "Creature", element = "Fire", secondaryElement = "Ice", size = "Large", shape = "Summon", behaviours = { "Burns", "Freezes", "Melee", "Blocks" }, power = 6, speed = 3, durability = 8, primaryColour = "#E8572A", secondaryColour = "#8FD3FF", bodyPlan = "Giant", silhouetteHint = "boulder body split half lava, half ice", motionHint = "Walk", soundHint = "clank", accents = { "steam", "split colours" }, flavourText = "Constantly arguing with itself.", tags = { "elemental" } }),
	ex({ key = "flying pancake stack", id = "pancake stack", confidence = 0.8, category = "Food", element = "None", size = "Small", shape = "Orb", behaviours = { "Bounces", "Flies", "Lures", "Splits" }, power = 3, speed = 5, durability = 2, primaryColour = "#D9A35B", secondaryColour = "#7A3E12", bodyPlan = "Food", silhouetteHint = "tall pancake stack, butter pat, syrup", motionHint = "Fly", soundHint = "flap", accents = { "syrup drips", "little wings" }, flavourText = "Breakfast has achieved liftoff.", tags = { "food", "sweet", "silly" } }),
	ex({ key = "magnet", id = "magnet", confidence = 0.95, category = "Tool", element = "Metal", size = "Small", shape = "Trap", behaviours = { "Lifts", "Pulls", "Steals" }, power = 4, speed = 4, durability = 6, primaryColour = "#C62828", secondaryColour = "#CFD8DC", bodyPlan = "Weapon", silhouetteHint = "red horseshoe, silver tips", motionHint = "Hover", soundHint = "hum", accents = { "field lines" }, flavourText = "Attractive personality.", tags = { "magnetic", "metal" } }),
	ex({ key = "a really big wave", id = "tidal wave", corrected = "tidal wave", confidence = 0.85, category = "Disaster", element = "Water", size = "Colossal", shape = "Wave", behaviours = { "Knockback", "Pushes", "Spreads" }, power = 8, speed = 6, durability = 4, primaryColour = "#1E6FA8", secondaryColour = "#E6F6FF", bodyPlan = "Wave", silhouetteHint = "curling wall of water, foam crest", motionHint = "Float", soundHint = "splash", accents = { "foam" }, flavourText = "Surf's up. Way, way up.", tags = { "natural", "aquatic" } }),
	ex({ key = "smug cactus", id = "cactus", confidence = 0.9, category = "Plant", element = "Nature", mood = "Smug", size = "Small", shape = "Trap", behaviours = { "Pierces", "Blocks", "Reflects" }, power = 3, speed = 1, durability = 7, primaryColour = "#4E8A3E", secondaryColour = "#F6D65B", bodyPlan = "Cactus", silhouetteHint = "tall ribbed column, two arms, spines", motionHint = "Static", soundHint = "thud", accents = { "half-lidded eyes", "smirk" }, flavourText = "Knows it's sharp. Won't shut up about it.", tags = { "plant", "sharp", "desert" } }),
	ex({ key = "army of tiny robots", id = "robot", confidence = 0.85, category = "Machine", element = "Metal", size = "Tiny", shape = "Summon", behaviours = { "Charges", "Shocks", "Splits" }, power = 2, speed = 6, durability = 4, primaryColour = "#9EA7AD", secondaryColour = "#3FA9F5", bodyPlan = "Robot", silhouetteHint = "boxy little bots, antenna, treads", motionHint = "Walk", soundHint = "beep", accents = { "antenna lights" }, flavourText = "Small, many, and running a group chat.", tags = { "robot", "mechanical" } }),
}

local REFUSAL_EXAMPLE = ex({ key = "<an offensive input>", refused = true, id = "glitter blob", confidence = 0, category = "Creature", element = "Arcane", size = "Tiny", shape = "Summon", behaviours = { "Confuses", "Distracts" }, power = 1, speed = 3, durability = 1, primaryColour = "#C77DFF", secondaryColour = "#FFD6FF", bodyPlan = "Blob", silhouetteHint = "", motionHint = "Hop", soundHint = "boing", flavourText = "", tags = {} })

local function enumLine(Schema: any, name: string): string
	return name .. ": " .. table.concat(Schema.Enums[name], ", ")
end

-- Convert a library WordResult into the model's output format (for few-shot consistency).
function Prompt.fromResult(r: any, key: string?): { [string]: any }
	local v = r.visual or {}
	return {
		key = key or r.id,
		refused = false,
		id = r.id,
		corrected = "",
		confidence = 0.95,
		category = r.category,
		element = r.element,
		secondaryElement = r.secondaryElement or "None",
		material = r.material or "",
		mood = r.mood or "Neutral",
		size = r.size,
		shape = r.shape,
		behaviours = r.behaviours,
		power = r.power,
		speed = r.speed,
		durability = r.durability,
		primaryColour = v.primaryColour,
		secondaryColour = v.secondaryColour,
		bodyPlan = v.bodyPlan,
		silhouetteHint = v.silhouetteHint,
		motionHint = v.motionHint,
		soundHint = v.soundHint,
		accents = v.accents or {},
		flavourText = r.flavourText,
		tags = r.tags,
	}
end

-- Encode with a stable key order so the system prompt is byte-identical between requests (cache hits).
local function encodeItem(item: { [string]: any }): string
	local parts = {}
	for _, k in ITEM_FIELDS do
		local v = item[k]
		if v ~= nil then
			local enc = Runtime.jsonEncode(v) or "null"
			if type(v) == "table" and next(v) == nil then
				enc = "[]"
			end
			table.insert(parts, '"' .. k .. '":' .. enc)
		end
	end
	return "{" .. table.concat(parts, ",") .. "}"
end
Prompt.encodeItem = encodeItem

local cachedSystem: string? = nil

function Prompt.resetCache()
	schemaJsonCache = nil
	cachedSystem = nil
end

function Prompt.examples(): string
	local lines = {}
	local cfg = Runtime.config()
	local Library = Runtime.sharedModule("Library")
	local ids = (cfg and cfg.AI and cfg.AI.FewShotIds) or {}
	if Library and Library.get then
		for _, id in ids do
			local ok, r = pcall(Library.get, id)
			if ok and type(r) == "table" then
				table.insert(lines, encodeItem(Prompt.fromResult(r)))
			end
		end
	end
	if #lines < 4 then
		for _, e in BUILTIN_EXAMPLES do
			table.insert(lines, encodeItem(e))
		end
	end
	for _, e in EDGE_EXAMPLES do
		table.insert(lines, encodeItem(e))
	end
	table.insert(lines, encodeItem(REFUSAL_EXAMPLE))
	return table.concat(lines, "\n")
end

local function materialsLine(): string
	local M = Runtime.sharedModule("Materials")
	local ids = {}
	if M then
		local ok, list = pcall(function()
			return if M.all then M.all() elseif M.list then M.list() else nil
		end)
		if ok and type(list) == "table" then
			for _, m in list do
				local id = if type(m) == "table" then m.id elseif type(m) == "string" then m else nil
				if type(id) == "string" then
					table.insert(ids, id)
				end
			end
		end
	end
	if #ids == 0 then
		ids = BUILTIN_MATERIALS
	end
	table.sort(ids)
	return table.concat(ids, ", ")
end

local function modifiersBlock(): string
	local Mods = Runtime.sharedModule("Modifiers")
	if Mods then
		local ok, list = pcall(function()
			return if Mods.all then Mods.all() elseif Mods.list then Mods.list() else nil
		end)
		if ok and type(list) == "table" and #list > 0 then
			local byKind: { [string]: { string } } = {}
			for _, m in list do
				if type(m) == "table" and type(m.id) == "string" and type(m.kind) == "string" then
					byKind[m.kind] = byKind[m.kind] or {}
					table.insert(byKind[m.kind], m.id)
				end
			end
			local out = {}
			for _, kind in { "Size", "Count", "Mood", "Quality", "Element", "State", "Motion", "Material" } do
				if byKind[kind] then
					table.sort(byKind[kind])
					table.insert(out, kind .. ": " .. table.concat(byKind[kind], ", "))
				end
			end
			if #out > 0 then
				return table.concat(out, "\n")
			end
		end
	end
	return table.concat(BUILTIN_MODIFIERS, "\n")
end

function Prompt.system(): string
	if cachedSystem then
		return cachedSystem :: string
	end
	local Schema = Runtime.sharedModule("Schema")
	cachedSystem = table.concat({
		"You tag words for two family-friendly Roblox typing games (a wizard duel and a tower defense). A player types any word or short phrase; it becomes a spell, a summoned creature, or a defense. You decide what the phrase MEANS: category, element(s), material, mood, size, delivery shape, behaviours and look. The game decides the numbers.",
		"",
		"How to read a phrase: count + modifiers + material + base thing + extras, in any word order (\"shark angry\" = \"angry shark\"). id is the base thing (singular, lowercase, no modifiers); modifiers become mood, size, secondaryElement, material and accents. Every modifier must be visible: add accents for it (\"scowl\", \"steam\", \"thrusters\", \"halo\", \"crack\", \"snore bubbles\").",
		"",
		"Rules:",
		"- Fix misspellings first (\"dargon\" -> \"dragon\"); put the fixed phrase in corrected (\"\" when nothing was fixed).",
		"- Make it FUN: pick behaviours that let the thing play like itself (a tornado Lifts, Pulls, Knockbacks; an asteroid Explodes; cheese Lures). Use 2-6 behaviours.",
		"- Nonsense or made-up words: invent the closest fun thing, keep it Tiny/Small with power 1-3, confidence below 0.5.",
		"- Keep power inside the band for its size. Power 9-10 only for world-ending things. speed: cheetah 10, snail 1. durability: fortress 10, bubble 1.",
		"- Two elements (\"fire ice golem\") -> element + secondaryElement. Otherwise secondaryElement is \"None\".",
		"- material: a material id from the list when the phrase names one (\"spaghetti dragon\", \"dragon made of cheese\"), else \"\".",
		"- NO brands, franchises, copyrighted characters or real people: reduce them to the generic idea (\"shreks toenail\" -> \"swamp ogre toenail\", a famous plumber -> \"plumber\", a sneaker brand -> \"sneaker\"). Put the generic phrase in id and corrected.",
		"- flavourText: one short, clean, funny line, at most 60 characters, never mean.",
		"- silhouetteHint: concrete shape cues for a 3D builder, at most 60 characters. Colours are real, tasteful #RRGGBB colours of the thing (material colours win).",
		"- tags: up to 6 lowercase gameplay tags (mythical, robot, edible, spooky, cute, explosive, heavy...).",
		"- SAFETY: if an input is sexual, hateful, a slur, drugs, self-harm, gore, a real tragedy, personal info, or otherwise not OK for kids, return refused=true for it with id \"glitter blob\" and empty text fields. Never repeat the offensive words anywhere.",
		"- Echo each input exactly in key and return exactly one result per input, by calling " .. Prompt.TOOL_NAME .. " with {\"results\":[...]} (or, if you cannot call tools, output only that JSON).",
		"",
		"Balance bands:",
		BAND_TABLE,
		"",
		"Allowed values (exact spelling):",
		enumLine(Schema, "Category"),
		enumLine(Schema, "Element"),
		enumLine(Schema, "Size"),
		enumLine(Schema, "Shape"),
		enumLine(Schema, "Behaviour"),
		enumLine(Schema, "BodyPlan") .. " (prefer the most specific plan)",
		enumLine(Schema, "Mood"),
		enumLine(Schema, "Motion"),
		"",
		"Materials: " .. materialsLine(),
		"",
		"Modifiers by kind (applied in this order):",
		modifiersBlock(),
		"",
		"Worked examples (one result object each; the first ones are hand-tagged library entries, match their style):",
		Prompt.examples(),
	}, "\n")
	return cachedSystem :: string
end

function Prompt.user(keys: { string }): string
	return "Interpret these inputs:\n" .. (Runtime.jsonEncode(keys) or "[]")
end

-- JSON schema (tool input_schema / json_schema format). No numeric/length constraints: unsupported
-- by strict mode; Schema.repair + clampPower enforce them.
function Prompt.schema(): { [string]: any }
	local Schema = Runtime.sharedModule("Schema")
	local E = Schema.Enums
	local str = { type = "string" }
	local strList = { type = "array", items = str }
	local item = {
		type = "object",
		properties = {
			key = str,
			refused = { type = "boolean" },
			id = str,
			corrected = str,
			confidence = { type = "number" },
			category = { type = "string", enum = E.Category },
			element = { type = "string", enum = E.Element },
			secondaryElement = { type = "string", enum = E.Element },
			material = str,
			mood = { type = "string", enum = E.Mood },
			size = { type = "string", enum = E.Size },
			shape = { type = "string", enum = E.Shape },
			behaviours = { type = "array", items = { type = "string", enum = E.Behaviour } },
			power = { type = "integer" },
			speed = { type = "integer" },
			durability = { type = "integer" },
			primaryColour = str,
			secondaryColour = str,
			bodyPlan = { type = "string", enum = E.BodyPlan },
			silhouetteHint = str,
			motionHint = { type = "string", enum = E.Motion },
			soundHint = str,
			accents = strList,
			flavourText = str,
			tags = strList,
		},
		required = ITEM_FIELDS,
		additionalProperties = false,
	}
	return {
		type = "object",
		properties = { results = { type = "array", items = item } },
		required = { "results" },
		additionalProperties = false,
	}
end

-- The same schema as Prompt.schema(), as a JSON string with properties in ITEM_FIELDS order.
function Prompt.schemaJson(): string?
	if schemaJsonCache then
		return schemaJsonCache
	end
	local schema = Prompt.schema()
	local item = schema.properties.results.items
	local props, req = {}, {}
	for _, k in ITEM_FIELDS do
		local enc = Runtime.jsonEncode(item.properties[k])
		if enc == nil then
			return nil
		end
		table.insert(props, '"' .. k .. '":' .. enc)
		table.insert(req, '"' .. k .. '"')
	end
	local itemJson = '{"type":"object","properties":{' .. table.concat(props, ",") .. '},"required":[' .. table.concat(req, ",") .. '],"additionalProperties":false}'
	schemaJsonCache = '{"type":"object","properties":{"results":{"type":"array","items":' .. itemJson .. '}},"required":["results"],"additionalProperties":false}'
	return schemaJsonCache
end

-- Model item -> raw table for Schema.repair (WordResult shape). Untrusted in, untrusted out.
function Prompt.toRaw(item: any): any
	if type(item) ~= "table" then
		return nil
	end
	local material = item.material
	if type(material) ~= "string" or material == "" or material == "none" then
		material = nil
	end
	return {
		id = item.id,
		canonical = item.id,
		confidence = item.confidence,
		source = "AI",
		category = item.category,
		element = item.element,
		secondaryElement = item.secondaryElement,
		material = material,
		mood = item.mood,
		size = item.size,
		shape = item.shape,
		behaviours = item.behaviours,
		power = item.power,
		speed = item.speed,
		durability = item.durability,
		count = 1,
		signature = false,
		visual = {
			primaryColour = item.primaryColour,
			secondaryColour = item.secondaryColour,
			bodyPlan = item.bodyPlan,
			silhouetteHint = item.silhouetteHint,
			motionHint = item.motionHint,
			soundHint = item.soundHint,
			accents = item.accents,
		},
		flavourText = item.flavourText,
		tags = item.tags,
	}
end

-- Enforce the balance band for the result's size (in place) and keep AI confidence honest.
function Prompt.clampPower(r: any)
	local band = Prompt.PowerBands[r.size] or { 1, 10 }
	r.power = math.clamp(math.floor((tonumber(r.power) or band[1]) + 0.5), band[1], band[2])
	r.speed = math.clamp(math.floor((tonumber(r.speed) or 5) + 0.5), 1, 10)
	r.durability = math.clamp(math.floor((tonumber(r.durability) or 5) + 0.5), 1, 10)
	r.confidence = math.clamp(tonumber(r.confidence) or 0.6, 0.3, 0.9)
end

return Prompt
