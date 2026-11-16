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
	local needsAI = spell.canonical == nil or spell.confidence < threshold
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
