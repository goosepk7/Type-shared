--!strict
-- Modifiers: vocabulary (data/modifiers.json + data/materials.json via Library), parse and capped apply.
--
--   Modifiers.parse({"tiny","angry","golden","robot","shark"}) -> ({"shark"}, {tiny, angry, golden, robotic})
--   Modifiers.apply(Library.get("shark"), mods)                -> "tiny angry golden robotic shark"
--
-- Kinds are applied in this order (DESIGN §5a): Size, Count, Mood, Quality, Element, State, Motion, Material.
-- Every modifier is visible: it sets mood, visual.accents, colours, motionHint and/or size. Totals are capped by
-- Config.Modifiers so any stack stays balanced. Contradictions resolve with humour: opposing sizes cancel to Medium
-- and make the thing Confused; two elements give a split-element result (element + secondaryElement).

local Types = require(script.Parent.Types)
local Schema = require(script.Parent.Schema)
local Config = require(script.Parent.Config)
local Normalizer = require(script.Parent.Normalizer)
local Library = require(script.Parent.Library)

type WordResult = Types.WordResult
type Modifier = Types.Modifier

local Modifiers = {}

local KIND_ORDER: { [string]: number } = {
	Size = 1, Count = 2, Mood = 3, Quality = 4, Element = 5, State = 6, Motion = 7, Material = 8,
}
Modifiers.KindOrder = KIND_ORDER

-- Words that glue phrases together and carry no meaning of their own ("dragon made out of spaghetti").
local FILLERS: { [string]: boolean } = {
	a = true, an = true, the = true, some = true, made = true, out = true, of = true, from = true, but = true,
	with = true, ["and"] = true, is = true, like = true, very = true, really = true, totally = true, entirely = true,
	full = true, which = true, that = true, its = true, ["it's"] = true, my = true, your = true, super = true,
	so = true, extra = true, kinda = true, sorta = true, just = true, all = true, ["in"] = true, as = true,
	powered = true, shaped = true, style = true, styled = true, themed = true, looking = true, type = true,
	flavored = true, flavoured = true, version = true, edition = true, form = true, mode = true,
}
Modifiers.Fillers = FILLERS

type Data = { modifiers: { any }, elements: { [string]: any }, accents: { string } }

local data: Data? = nil
local byId: { [string]: any } = {}
local byWord: { [string]: any } = {} -- id/alias -> modifier
local byMisspelling: { [string]: any } = {}
local maxWords = 1
local singleWords: { string } = {} -- single-token ids/aliases (fuzzy vocabulary)

local function load(): Data
	local d = data
	if d then
		return d
	end
	local raw = require(script.Parent.Library.Generated.Modifiers) :: any
	for _, m in raw.modifiers do
		table.freeze(m)
		byId[m.id] = m
		local function reg(w: string, map: { [string]: any })
			if map[w] == nil then
				map[w] = m
			end
			local n = #string.split(w, " ")
			if n > maxWords then
				maxWords = n
			end
			if n == 1 then
				table.insert(singleWords, w)
			end
		end
		reg(m.id, byWord)
		for _, a in m.aliases do
			reg(a, byWord)
		end
		for _, a in m.misspellings or {} do
			reg(a, byMisspelling)
		end
	end
	table.sort(singleWords)
	data = raw
	return raw
end

function Modifiers.get(id: string): Modifier?
	load()
	return byId[id]
end

function Modifiers.all(): { Modifier }
	return load().modifiers
end

function Modifiers.elementPalette(element: string): any
	return load().elements[element]
end

-- Single-token modifier words, sorted (vocabulary for fuzzy matching). Shared: do not mutate.
function Modifiers.vocabulary(): { string }
	load()
	return singleWords
end

-- Exact word / phrase -> (modifier, isMisspelling).
function Modifiers.lookup(word: string): (Modifier?, boolean)
	load()
	local m = byWord[word]
	if m then
		return m, false
	end
	m = byMisspelling[word]
	if m then
		return m, true
	end
	return nil, false
end

-- A Count modifier for numbers that aren't in the vocabulary ("100", "21").
function Modifiers.number(tok: string): Modifier?
	local n = Normalizer.toNumber(tok)
	if n == nil or n < 1 then
		return nil
	end
	local known = byWord[tok]
	if known then
		return known
	end
	return { id = tok, kind = "Count", order = KIND_ORDER.Count, count = n, power = if n >= 50 then -2 elseif n >= 6 then -1 else nil } :: any
end

-- Material as a modifier record (kind "Material").
function Modifiers.material(id: string): Modifier?
	local mat = Library.material(id)
	if mat == nil then
		return nil
	end
	return { id = mat.id, kind = "Material", order = KIND_ORDER.Material } :: any
end

-- Longest modifier/number match starting at tokens[i]: (modifier, tokensUsed, isMisspelling).
function Modifiers.match(tokens: { string }, i: number): (Modifier?, number, boolean)
	load()
	for len = math.min(maxWords, #tokens - i + 1), 1, -1 do
		local phrase = table.concat(tokens, " ", i, i + len - 1)
		local m, miss = Modifiers.lookup(phrase)
		if m then
			return m, len, miss
		end
	end
	local num = Modifiers.number(tokens[i])
	if num then
		return num, 1, false
	end
	return nil, 0, false
end

-- Material match (up to 3 tokens) starting at tokens[i]: (modifier, tokensUsed, isMisspelling).
function Modifiers.matchMaterial(tokens: { string }, i: number): (Modifier?, number, boolean)
	for len = math.min(3, #tokens - i + 1), 1, -1 do
		local id, miss = Library.lookupMaterial(table.concat(tokens, " ", i, i + len - 1))
		if id then
			return Modifiers.material(id), len, miss
		end
	end
	return nil, 0, false
end

-- Strict parse (no fuzzy matching; Speller.correct is the forgiving one). Modifiers, materials and numbers
-- anywhere in the phrase are collected; fillers are dropped; everything else is returned in `rest`. If nothing
-- would be left, the last consumed word that is itself a library thing goes back into `rest` ("giant fire" ->
-- rest {"fire"}, mods {giant}).
function Modifiers.parse(tokens: { string }): ({ string }, { Modifier })
	load()
	local rest: { string } = {}
	local mods: { Modifier } = {}
	local consumed: { { word: string, index: number } } = {}
	local i = 1
	while i <= #tokens do
		local m, len = Modifiers.match(tokens, i)
		local mat, mlen = Modifiers.matchMaterial(tokens, i)
		-- "made of X", "out of X", "of X", "but X": X is a material whenever it is one.
		local prev = tokens[i - 1]
		local materialSlot = prev == "of" or prev == "but"
		if mat and materialSlot then
			table.insert(mods, mat)
			table.insert(consumed, { word = table.concat(tokens, " ", i, i + mlen - 1), index = #mods })
			i += mlen
			continue
		end
		-- a library thing spanning more tokens beats a shorter modifier ("laser beam" is a thing)
		local thingLen = 0
		for l = math.min(4, #tokens - i + 1), 1, -1 do
			if Library.keyInfo(table.concat(tokens, " ", i, i + l - 1)) then
				thingLen = l
				break
			end
		end
		if thingLen > math.max(len, mlen) then
			for k = i, i + thingLen - 1 do
				table.insert(rest, tokens[k])
			end
			i += thingLen
		elseif mat and mlen >= len then
			table.insert(mods, mat)
			table.insert(consumed, { word = table.concat(tokens, " ", i, i + mlen - 1), index = #mods })
			i += mlen
		elseif m then
			table.insert(mods, m)
			table.insert(consumed, { word = table.concat(tokens, " ", i, i + len - 1), index = #mods })
			i += len
		elseif FILLERS[tokens[i]] then
			i += 1
		else
			table.insert(rest, tokens[i])
			i += 1
		end
	end
	if #rest == 0 then
		for k = #consumed, 1, -1 do
			local c = consumed[k]
			if Library.keyInfo(c.word) then
				table.remove(mods, c.index)
				table.insert(rest, c.word)
				break
			end
		end
	end
	return rest, mods
end

-- ------------------------------------------------------------------ colour helpers

local function hexToRgb(hex: string): (number, number, number)
	local h = string.match(hex, "^#?(%x%x%x%x%x%x)$") or "9AA5B1"
	return tonumber(string.sub(h, 1, 2), 16) :: number, tonumber(string.sub(h, 3, 4), 16) :: number,
		tonumber(string.sub(h, 5, 6), 16) :: number
end

local function lerpHex(a: string, b: string, t: number): string
	local r1, g1, b1 = hexToRgb(a)
	local r2, g2, b2 = hexToRgb(b)
	local function mix(x: number, y: number): number
		return math.clamp(math.floor(x + (y - x) * t + 0.5), 0, 255)
	end
	return string.format("#%02X%02X%02X", mix(r1, r2), mix(g1, g2), mix(b1, b2))
end
Modifiers.lerpHex = lerpHex

-- ------------------------------------------------------------------ canonical text

local MAN_EXCEPTIONS = { human = true, talisman = true, shaman = true, caiman = true, ottoman = true, cayman = true, doberman = true }

local function pluralize(word: string): string
	local head, last = string.match(word, "^(.* )(%S+)$")
	local pre = head or ""
	local w = last or word
	local n = #w
	local function ends(s: string): boolean
		return string.sub(w, -#s) == s
	end
	local out
	if ends("s") or ends("x") or ends("z") or ends("ch") or ends("sh") then
		out = w .. "es"
	elseif ends("y") and n > 1 and not string.find("aeiou", string.sub(w, -2, -2), 1, true) then
		out = string.sub(w, 1, n - 1) .. "ies"
	elseif ends("man") and not MAN_EXCEPTIONS[w] then
		out = string.sub(w, 1, n - 3) .. "men"
	elseif ends("fe") then
		out = string.sub(w, 1, n - 2) .. "ves"
	elseif ends("f") and not ends("ff") then
		out = string.sub(w, 1, n - 1) .. "ves"
	else
		out = w .. "s"
	end
	return pre .. out
end
Modifiers.pluralize = pluralize

-- Sort a copy of mods into application order (stable within a kind).
local function ordered(mods: { Modifier }): { Modifier }
	local list = {}
	for i, m in mods do
		table.insert(list, { m = m, i = i })
	end
	table.sort(list, function(a, b)
		local ka, kb = KIND_ORDER[a.m.kind] or 9, KIND_ORDER[b.m.kind] or 9
		if ka ~= kb then
			return ka < kb
		end
		return a.i < b.i
	end)
	local out = {}
	for _, x in list do
		table.insert(out, x.m)
	end
	return out
end

-- "three tiny angry golden fire robotic spaghetti sharks". Count phrases ("swarm of") pluralize the base.
function Modifiers.canonical(base: string, mods: { Modifier }): string
	local words = {}
	local plural = false
	local countWord: string? = nil
	for _, m in ordered(mods) do
		if m.kind == "Count" then
			if (m.count or 1) > 1 and countWord == nil then
				countWord = m.id
				plural = true
			end
		else
			table.insert(words, m.id)
		end
	end
	table.insert(words, if plural then pluralize(base) else base)
	if countWord then
		table.insert(words, 1, countWord)
	end
	return table.concat(words, " ")
end

-- ------------------------------------------------------------------ apply

local function addUnique(list: { string }, items: { string }?, cap: number)
	if items == nil then
		return
	end
	for _, v in items do
		if #list >= cap then
			return
		end
		if not table.find(list, v) then
			table.insert(list, v)
		end
	end
end

-- Keep at most MaxModifiers, dedupe by id, merge Count numbers. Returns mods in TYPED order.
local function sanitize(mods: { Modifier }, maxMods: number): { Modifier }
	local out: { Modifier } = {}
	local seen: { [string]: boolean } = {}
	for _, m in mods do
		if type(m) == "table" and type(m.id) == "string" and KIND_ORDER[m.kind] ~= nil then
			local key = m.kind .. ":" .. m.id
			if not seen[key] and #out < maxMods then
				seen[key] = true
				table.insert(out, m)
			end
		end
	end
	return out
end

function Modifiers.apply(result: WordResult, mods: { Modifier }): WordResult
	local cfg = Config.Modifiers
	local out = Schema.clone(result)
	out.visual.accents = out.visual.accents or {}
	out.secondaryElement = out.secondaryElement or "None"
	out.mood = out.mood or "Neutral"
	if mods == nil or #mods == 0 then
		return out
	end
	load()
	local list = sanitize(mods, cfg.MaxModifiers)
	local baseBehaviours = #out.behaviours
	local maxBehaviours = Schema.Limits.MaxBehaviours
	local maxTags = Schema.Limits.MaxTags
	local accents = out.visual.accents
	local behaviours = table.clone(out.behaviours)
	local tags = table.clone(out.tags)

	local sizeSteps, sizeUp, sizeDown = 0, false, false
	local dPower, dSpeed, dDur = 0, 0, 0
	local countMul = 1
	local elements: { string } = {}
	local colourOverride = false
	local applied: { Types.AppliedModifier } = {}

	for _, m in ordered(list) do
		local mm: any = m
		table.insert(applied, { id = m.id, kind = m.kind })
		if m.kind == "Material" then
			local mat = Library.material(m.id)
			if mat then
				out.material = mat.id
				local strength = if colourOverride then 0.5 else cfg.MaterialTint
				out.visual.primaryColour = lerpHex(out.visual.primaryColour, mat.palette[1], strength)
				out.visual.secondaryColour = lerpHex(out.visual.secondaryColour, mat.palette[2] or mat.palette[1], strength)
				local cap = cfg.MaterialStatCap
				local hints: any = mat.statHints or {}
				dPower += math.clamp(hints.power or 0, -cap, cap)
				dSpeed += math.clamp(hints.speed or 0, -cap, cap)
				dDur += math.clamp(hints.durability or 0, -cap, cap)
				local hooks = {}
				for _, h in mat.hooks do
					if Schema.Sets.Behaviour[h] then
						table.insert(hooks, h)
					end
				end
				addUnique(behaviours, hooks, maxBehaviours)
				addUnique(tags, mat.tags, maxTags)
				-- material affinity ("lava golem") unless the player named an element explicitly
				if mat.element ~= "None" and #elements == 0 then
					out.element = mat.element :: any
				end
				if mat.glow > 0.3 then
					addUnique(accents, { "glow" }, cfg.MaxAccents)
				end
			end
		else
			if mm.size then
				sizeSteps += mm.size
				if mm.size > 0 then
					sizeUp = true
				elseif mm.size < 0 then
					sizeDown = true
				end
			end
			if mm.count then
				countMul *= math.max(1, mm.count)
			end
			dPower += mm.power or 0
			dSpeed += mm.speed or 0
			dDur += mm.durability or 0
			if mm.mood then
				out.mood = mm.mood
			end
			if mm.motion then
				out.visual.motionHint = mm.motion
			end
			local newElement = false
			if mm.element and not table.find(elements, mm.element) then
				table.insert(elements, mm.element)
				newElement = true
			end
			if mm.colour then
				out.visual.primaryColour = mm.colour
				colourOverride = true
			end
			if mm.colour2 then
				out.visual.secondaryColour = mm.colour2
			end
			if mm.tint then
				out.visual.primaryColour = lerpHex(out.visual.primaryColour, mm.tint, 0.25)
			end
			addUnique(accents, mm.accents, cfg.MaxAccents)
			addUnique(behaviours, mm.addBehaviours, maxBehaviours)
			addUnique(tags, mm.addTags, maxTags)
			-- elements are applied when the Element kind is reached (below) so split elements resolve together
			if newElement then
				local pal = Modifiers.elementPalette(mm.element)
				local first = #elements == 1
				if pal then
					if first then
						out.element = mm.element
						out.visual.primaryColour = lerpHex(out.visual.primaryColour, pal.pc, if colourOverride then 0.25 else cfg.ElementTint)
						out.visual.secondaryColour = lerpHex(out.visual.secondaryColour, pal.sc, 0.7)
						addUnique(behaviours, pal.b, maxBehaviours)
					elseif #elements == 2 then
						out.secondaryElement = mm.element
						out.visual.secondaryColour = lerpHex(out.visual.secondaryColour, pal.pc, cfg.SecondaryElementTint + 0.3)
						addUnique(behaviours, { pal.b[1] }, maxBehaviours)
					end
					if #elements <= 2 then
						addUnique(tags, pal.t, maxTags)
						addUnique(accents, pal.accents, cfg.MaxAccents)
					end
				end
			end
		end
	end

	-- contradictions: "tiny giant shark" -> Medium + Confused
	if sizeUp and sizeDown then
		out.size = "Medium"
		out.mood = "Confused"
		addUnique(accents, { "question" }, cfg.MaxAccents)
		sizeSteps = 0
	else
		sizeSteps = math.clamp(sizeSteps, -cfg.MaxSizeSteps, cfg.MaxSizeSteps)
		out.size = Schema.sizeStep(out.size, sizeSteps) :: any
	end
	-- "fire ice dragon" where "ice dragon" is itself a library thing: the base's own element word becomes the split
	if #elements == 1 and result.element ~= "None" and result.element ~= out.element and out.secondaryElement == "None" then
		for w in string.gmatch(result.id, "%S+") do
			local em = byWord[w]
			if em and em.element == result.element then
				out.secondaryElement = result.element
				break
			end
		end
	end
	if out.secondaryElement == out.element then
		out.secondaryElement = "None"
	end
	dPower += sizeSteps * cfg.SizePowerPerStep
	dDur += sizeSteps * cfg.SizePowerPerStep * 0.5
	local L = Schema.Limits
	out.power = math.clamp(out.power + math.clamp(dPower, -cfg.MaxPowerDelta, cfg.MaxPowerDelta), L.StatMin, L.StatMax)
	out.speed = math.clamp(out.speed + math.clamp(dSpeed, -cfg.MaxSpeedDelta, cfg.MaxSpeedDelta), L.StatMin, L.StatMax)
	out.durability = math.clamp(out.durability + math.clamp(dDur, -cfg.MaxDurabilityDelta, cfg.MaxDurabilityDelta), L.StatMin, L.StatMax)
	out.count = math.clamp(math.floor(out.count * countMul), 1, math.min(cfg.MaxCount, L.MaxCount))

	-- base behaviours always survive; added ones fill up to the cap
	local finalB = {}
	for i = 1, math.min(#behaviours, maxBehaviours) do
		if i <= baseBehaviours or #finalB < maxBehaviours then
			table.insert(finalB, behaviours[i])
		end
	end
	table.sort(finalB)
	out.behaviours = finalB
	out.tags = tags
	out.visual.accents = accents
	out.modifiers = applied
	out.canonical = Modifiers.canonical(result.id, list)
	return out
end

return Modifiers
