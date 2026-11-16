--!strict
-- Resolver: the full library-only pipeline (no network). Client-safe; the server Interpreter calls
-- resolveLocalDetailed and decides whether to ask Cache/AI.
--
--   Resolver.resolveLocal(text)                      -> WordResult (never nil; Fallback blob when unknown)
--   Resolver.resolveLocalDetailed(text, threshold?)  -> (WordResult, SpellResult, needsAI: boolean)
--   Resolver.parse(text)                             -> phrase breakdown for inspectors / UI

local Types = require(script.Parent.Types)
local Schema = require(script.Parent.Schema)
local Config = require(script.Parent.Config)
local Normalizer = require(script.Parent.Normalizer)
local Library = require(script.Parent.Library)
local Modifiers = require(script.Parent.Modifiers)
local Speller = require(script.Parent.Speller)

type WordResult = Types.WordResult
type SpellResult = Types.SpellResult

local Resolver = {}

-- Plural input ("bees", "wolves", "mice") with no explicit count reads as a small group.
-- Counts by size keep balance sane; abstract/area categories never multiply.
local PLURAL_COUNT: { [string]: number } = { Tiny = 5, Small = 3, Medium = 2, Large = 2, Huge = 1, Colossal = 1 }
local NO_PLURAL_COUNT: { [string]: boolean } = {
	Element = true, Weather = true, Disaster = true, Abstract = true, Place = true,
}
local IRREGULAR: { [string]: string } = {
	mice = "mouse", geese = "goose", teeth = "tooth", feet = "foot", people = "person", children = "child",
	oxen = "ox", men = "man", women = "woman", dice = "die", lice = "louse", octopi = "octopus", cacti = "cactus",
	fungi = "fungus", wolves = "wolf", knives = "knife", leaves = "leaf", elves = "elf", dwarves = "dwarf",
}

local function lastWord(s: string): string
	return string.match(s, "([^%s]+)$") or s
end

local function isPluralOf(typed: string, singular: string): boolean
	if typed == singular then
		return false
	end
	if IRREGULAR[typed] == singular then
		return true
	end
	if typed == singular .. "s" or typed == singular .. "es" then
		return true
	end
	if string.sub(singular, -1) == "y" and typed == string.sub(singular, 1, -2) .. "ies" then
		return true
	end
	local stemF = string.match(singular, "^(.-)fe?$")
	if stemF and typed == stemF .. "ves" then
		return true
	end
	return false
end

-- True when the typed phrase names the base thing in plural form.
function Resolver.isPluralInput(text: string, baseId: string): boolean
	local typed = Normalizer.light(if type(text) == "string" then text else "")
	return isPluralOf(lastWord(typed), lastWord(baseId))
end

local function build(text: string, spell: SpellResult, unknownBelow: number): WordResult
	local raw = if type(text) == "string" then text else ""
	if spell.canonical == nil or spell.confidence < unknownBelow then
		return Schema.fallback(raw)
	end
	local base = Library.get(spell.canonical :: string)
	if base == nil then
		return Schema.fallback(raw)
	end
	local result = Modifiers.apply(base, spell.modifiers)
	local hasCount = false
	for _, m in spell.modifiers do
		if m.kind == "Count" then
			hasCount = true
		end
	end
	if not hasCount and result.count == 1 and not NO_PLURAL_COUNT[result.category]
		and Resolver.isPluralInput(raw, base.id) then
		result.count = PLURAL_COUNT[result.size] or 1
		if result.count > 1 and table.find(result.tags, "group") == nil and #result.tags < Schema.Limits.MaxTags then
			table.insert(result.tags, "group")
		end
	end
	-- A thing made of a material is a different idea for no-repeat rules ("spaghetti dragon" ~= "dragon").
	if result.material then
		result.synonymGroup = result.synonymGroup .. ":" .. result.material
	end
	result.input = string.sub(raw, 1, 200)
	result.confidence = spell.confidence
	result.source = "Library"
	local typed = Normalizer.light(raw)
	if typed ~= result.canonical then
		result.correction = {
			method = spell.method or "Normalized",
			from = typed,
			to = result.canonical,
			confidence = spell.confidence,
			alternatives = table.clone(spell.alternatives),
		}
	end
	return result
end

-- Full detail for the server Interpreter. `aiThreshold` defaults to Config.AI.Threshold (or 0.6).
-- needsAI is true when the library answer is below the threshold or the parser left unplaced extras.
function Resolver.resolveLocalDetailed(text: string, aiThreshold: number?): (WordResult, SpellResult, boolean)
	local spell = Speller.correct(text)
	local threshold = aiThreshold or ((Config :: any).AI and (Config :: any).AI.Threshold) or 0.6
	local result = build(text, spell, Config.Speller.UnknownBelow)
	-- Unplaced words ("kazoo orchestra" with no kazoo in the library) always get a second opinion from the AI.
	local needsAI = spell.canonical == nil or spell.confidence < threshold or (spell.extras ~= nil and #spell.extras > 0)
	return result, spell, needsAI
end

function Resolver.resolveLocal(text: string): WordResult
	local ok, result = pcall(function()
		return (Resolver.resolveLocalDetailed(text))
	end)
	if ok and result then
		return result
	end
	return Schema.fallback(if type(text) == "string" then text else "")
end

export type Parse = {
	count: number,
	modifiers: { Types.AppliedModifier },
	material: string?,
	base: string?,
	extras: { string },
	tokens: { string },
	confidence: number,
	method: string?,
}

-- Phrase breakdown (count + modifiers + material + base + extras) for the test-place inspector and UI.
function Resolver.parse(text: string): Parse
	local spell = Speller.correct(text)
	local count = 1
	local mods = {}
	for _, m in spell.modifiers do
		table.insert(mods, { id = m.id, kind = m.kind })
		if m.kind == "Count" and m.count then
			count *= m.count
		end
	end
	return {
		count = math.clamp(count, 1, Config.Modifiers.MaxCount),
		modifiers = mods,
		material = spell.material,
		base = spell.canonical,
		extras = table.clone(spell.extras),
		tokens = table.clone(spell.tokens),
		confidence = spell.confidence,
		method = spell.method,
	}
end

return Resolver
