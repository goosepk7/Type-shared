--!strict
-- Speller: turns anything a player types into a library id + modifiers + material + extras, with a confidence.
-- Pipeline (DESIGN.md §5 / §5a, details in README.md next to this file):
--   normalize -> protected names -> whole phrase: exact / alias / spacing variant / stem / known misspelling
--   -> single word: weighted fuzzy (keyboard-aware DL) + Double Metaphone, or compound split ("giantshark")
--   -> phrase parser: segment tokens into count + modifiers + material + ONE base thing + fillers + extras,
--      every slot typo-tolerant, order-free, minimum-cost segmentation (dynamic programming).
-- Results are cached in an LRU keyed by the normalized text.

local Types = require(script.Parent.Types)
local Config = require(script.Parent.Config)
local Normalizer = require(script.Parent.Normalizer)
local Library = require(script.Parent.Library)
local Modifiers = require(script.Parent.Modifiers)
local Stemmer = require(script.Stemmer)
local Fuzzy = require(script.Fuzzy)
local LRU = require(script.LRU)
local Metaphone = require(script.Metaphone)

type SpellResult = Types.SpellResult
type Modifier = Types.Modifier
type CorrectionMethod = Types.CorrectionMethod

local Speller = {}

type Hit = { ord: number, conf: number, method: CorrectionMethod, alts: { number } }

local cache = LRU.new(Config.Speller.CacheSize or 512)
local protected: any = nil

local function cfg(): any
	return Config.Speller
end

local function maxCostFor(len: number): number
	local t = cfg().FuzzyMaxCost
	return t[math.clamp(len, 1, #t)]
end

local function loadProtected(): any
	if protected == nil then
		local inst = script.Parent.Library.Generated:FindFirstChild("Protected")
		local p = if inst then require(inst :: any) :: any else { names = {}, strip = {} }
		local strip = {}
		for _, w in p.strip do
			strip[w] = true
		end
		protected = { names = p.names, strip = strip }
	end
	return protected
end

-- ------------------------------------------------------------------ single key lookups

local function cheapLookup(form: string): Hit?
	if form == "" then
		return nil
	end
	local o, kind = Library.keyInfo(form)
	if o then
		local method: CorrectionMethod = if kind == "Id" then "Exact" elseif kind == "Alias" then "Alias" else "Normalized"
		return { ord = o, conf = if kind == "Variant" then 0.97 else 1, method = method, alts = {} }
	end
	local mo = Library.misspelling(form)
	if mo then
		return { ord = mo, conf = 0.93, method = "Misspelling", alts = {} }
	end
	for _, c in Stemmer.candidates(form) do
		local so = Library.keyInfo(c.word)
		if so then
			return { ord = so, conf = c.confidence, method = "Stem", alts = {} }
		end
		local sm = if c.plural then Library.misspelling(c.word) else nil
		if sm then
			return { ord = sm, conf = math.min(c.confidence, 0.9), method = "Misspelling", alts = {} }
		end
	end
	return nil
end

local function fuzzyConf(cost: number, n: number, phoneticOnly: boolean): number
	if phoneticOnly then
		return math.clamp(0.86 - 0.05 * cost, 0.55, 0.86)
	end
	return math.clamp(0.98 - 0.06 * cost - 0.4 * cost / math.max(n, 3), 0.4, 0.97)
end

local function fuzzyLookup(form: string): Hit?
	local n = #form
	if n < 3 then
		return nil
	end
	local maxCost = maxCostFor(n)
	local cands = Fuzzy.search(form, maxCost, cfg().PhoneticExtraCost, cfg().FuzzyCandidates)
	if #cands == 0 then
		return nil
	end
	-- phonetic agreement is evidence: discount it, then re-rank
	local scored = {}
	local qp = Metaphone.encode(form)
	local phonBonus = if #qp >= 4 and n >= 5 then 0.6 elseif #qp >= 3 then 0.3 else 0.1
	for _, c in cands do
		local key, owner, keyIsId = Fuzzy.keyAt(c.key)
		local rank = Library.rankOf(owner)
		-- Bayesian-ish prior: popular / signature words are likelier targets; aliases slightly less likely than ids;
		-- matching sounds is evidence (stronger for longer codes).
		local eff = c.cost
			- (if c.phonetic then phonBonus else 0)
			- 0.25 * math.min(rank, 800) / 800
			+ (if keyIsId then 0 else 0.12)
			+ (if string.find(key, " ", 1, true) and not string.find(form, " ", 1, true) then 0.1 else 0)
		table.insert(scored, { owner = owner, eff = eff, cost = c.cost, phonetic = c.phonetic, rank = rank })
	end
	table.sort(scored, function(a, b)
		if math.abs(a.eff - b.eff) > 1e-6 then
			return a.eff < b.eff
		end
		if a.rank ~= b.rank then
			return a.rank > b.rank
		end
		return a.owner < b.owner
	end)
	local best = scored[1]
	local alts: { number } = {}
	local second: any = nil
	for k = 2, #scored do
		local s = scored[k]
		if s.owner ~= best.owner and not table.find(alts, s.owner) then
			second = second or s
			if #alts < 3 then
				table.insert(alts, s.owner)
			end
		end
	end
	local phoneticOnly = best.cost > maxCost
	local conf = fuzzyConf(best.cost, n, phoneticOnly)
	if second and second.eff - best.eff < 0.2 then
		conf -= 0.08
	end
	return {
		ord = best.owner,
		conf = conf,
		method = if phoneticOnly then "Phonetic" else "Fuzzy",
		alts = alts,
	}
end

-- ------------------------------------------------------------------ result helpers

local function emptyResult(tokens: { string }): SpellResult
	return { canonical = nil, confidence = 0, method = nil, alternatives = {}, tokens = tokens, modifiers = {}, material = nil, extras = {} }
end

local function altStrings(alts: { number }, mods: { Modifier }): { string }
	local out = {}
	for _, o in alts do
		local s = if #mods > 0 then Modifiers.canonical(Library.idOf(o), mods) else Library.idOf(o)
		if not table.find(out, s) and #out < 3 then
			table.insert(out, s)
		end
	end
	return out
end

local function fromHit(h: Hit, tokens: { string }): SpellResult
	return {
		canonical = Library.idOf(h.ord),
		confidence = h.conf,
		method = h.method,
		alternatives = altStrings(h.alts, {}),
		tokens = tokens,
		modifiers = {},
		material = nil,
		extras = {},
	}
end

local function copyResult(r: SpellResult): SpellResult
	local c = table.clone(r)
	c.alternatives = table.clone(r.alternatives)
	c.tokens = table.clone(r.tokens)
	c.modifiers = table.clone(r.modifiers)
	c.extras = table.clone(r.extras)
	return c
end

-- ------------------------------------------------------------------ phrase parser

type Option = {
	kind: "Base" | "Mod" | "Fill" | "Extra",
	cost: number,
	conf: number,
	hit: Hit?,
	mod: Modifier?,
	fuzzy: boolean,
}

-- Words after which nouns are accessories, not the head ("shark wearing a hat", "knight riding a horse").
local ACCESSORY_WORDS: { [string]: boolean } = {
	wearing = true, with = true, holding = true, riding = true, carrying = true, eating = true, on = true,
	inside = true, under = true, wielding = true, using = true, has = true, having = true,
}

local function isKnownToken(tok: string): boolean
	if ACCESSORY_WORDS[tok] or Modifiers.Fillers[tok] or Library.keyInfo(tok) or Modifiers.lookup(tok) or Modifiers.number(tok) then
		return true
	end
	return (Library.lookupMaterial(tok)) ~= nil
end

local function bestFuzzyWord(tok: string, vocab: { string }): ({ word: string, cost: number }?, number)
	local maxCost = maxCostFor(#tok)
	local list = Fuzzy.searchList(tok, vocab, maxCost)
	local best = list[1]
	if best == nil then
		return nil, 0
	end
	local conf = fuzzyConf(best.cost, #tok, false)
	if list[2] and list[2].cost - best.cost < 0.15 then
		conf -= 0.06
	end
	return best, conf
end

local materialVocab: { string }? = nil
local function materialWordList(): { string }
	local v = materialVocab
	if v then
		return v
	end
	local out = {}
	for w in Library.materialWords() do
		if not string.find(w, " ", 1, true) then
			table.insert(out, w)
		end
	end
	table.sort(out)
	materialVocab = out
	return out
end

local function spanOptions(tokens: { string }, i: number, j: number, n: number, unknown: { boolean }, accessory: { boolean }): { Option }
	local opts: { Option } = {}
	local L = j - i + 1
	local phrase = table.concat(tokens, " ", i, j)
	local anyUnknown = false
	for k = i, j do
		if unknown[k] then
			anyUnknown = true
		end
	end
	-- base thing
	local h = cheapLookup(phrase)
	if h == nil and L == 1 and anyUnknown then
		h = fuzzyLookup(phrase)
	elseif h == nil and L == 2 and unknown[i] and unknown[j] then
		h = fuzzyLookup(phrase) -- "tyranosaurus reks": only when neither token means anything alone
	end
	if h then
		local cost = (1 - h.conf) * 2 - 0.12 * (L - 1) + 0.05 * (n - j)
		if accessory[i] then
			cost += 0.6 -- "shark wearing a monocle": the head noun comes before wearing/with/holding
		end
		table.insert(opts, { kind = "Base", cost = cost, conf = h.conf, hit = h, fuzzy = h.method == "Fuzzy" or h.method == "Phonetic" })
	end
	-- modifier (exact span)
	local m, miss = Modifiers.lookup(phrase)
	if m == nil and L == 1 then
		m = Modifiers.number(phrase)
	end
	if m then
		table.insert(opts, { kind = "Mod", cost = if miss then 0.2 else 0.05, conf = if miss then 0.93 else 1, mod = m, fuzzy = false })
	end
	-- material (exact span)
	local matId, matMiss = Library.lookupMaterial(phrase)
	if matId then
		table.insert(opts, { kind = "Mod", cost = if matMiss then 0.21 else 0.06, conf = if matMiss then 0.93 else 1, mod = Modifiers.material(matId), fuzzy = false })
	end
	if L == 1 then
		local tok = phrase
		if Modifiers.Fillers[tok] or ACCESSORY_WORDS[tok] then
			table.insert(opts, { kind = "Fill", cost = 0.03, conf = 1, fuzzy = false })
		end
		if m == nil and matId == nil and #tok >= 4 and unknown[i] then
			local bm, conf = bestFuzzyWord(tok, Modifiers.vocabulary())
			if bm then
				local mod = Modifiers.lookup(bm.word)
				if mod then
					table.insert(opts, { kind = "Mod", cost = (1 - conf) * 2 + 0.05, conf = conf, mod = mod, fuzzy = true })
				end
			end
			local bt, tconf = bestFuzzyWord(tok, materialWordList())
			if bt then
				local id = Library.lookupMaterial(bt.word)
				if id then
					table.insert(opts, { kind = "Mod", cost = (1 - tconf) * 2 + 0.06, conf = tconf, mod = Modifiers.material(id), fuzzy = true })
				end
			end
		end
		table.insert(opts, { kind = "Extra", cost = 1.0, conf = 1, fuzzy = false })
	end
	return opts
end

type Segment = { i: number, j: number, opt: Option }


local MAX_SPAN = 4

local function parsePhrase(tokens: { string }): (SpellResult, boolean)
	local n = #tokens
	local unknown: { boolean } = {}
	local accessory: { boolean } = {}
	local after = false
	for k = 1, n do
		unknown[k] = not isKnownToken(tokens[k])
		accessory[k] = after
		if ACCESSORY_WORDS[tokens[k]] and k > 1 then
			after = true
		end
	end
	-- DP over (position, baseUsed)
	local INF = math.huge
	local best: { [number]: { number } } = {}
	local back: { [number]: { any } } = {}
	for p = 1, n + 1 do
		best[p] = { INF, INF }
		back[p] = { false, false }
	end
	best[1][1] = 0
	local optCache: { [number]: { Option } } = {}
	for p = 1, n do
		for used = 1, 2 do
			local here = best[p][used]
			if here < INF then
				for j = p, math.min(n, p + MAX_SPAN - 1) do
					local key = p * 100 + j
					local opts = optCache[key]
					if opts == nil then
						opts = spanOptions(tokens, p, j, n, unknown, accessory)
						optCache[key] = opts
					end
					for _, o in opts do
						local nextUsed = used
						local ok = true
						if o.kind == "Base" then
							if used == 2 then
								ok = false
							end
							nextUsed = 2
						end
						if ok then
							local c = here + o.cost
							if c < best[j + 1][nextUsed] then
								best[j + 1][nextUsed] = c
								back[j + 1][nextUsed] = { from = p, used = used, opt = o }
							end
						end
					end
				end
			end
		end
	end
	local withBase, noBase = best[n + 1][2], best[n + 1][1] + 1.5
	local state = if withBase <= noBase then 2 else 1
	if best[n + 1][state] == INF then
		return emptyResult(tokens), false
	end
	-- walk back
	local segs: { Segment } = {}
	local p, used = n + 1, state
	while p > 1 do
		local b = back[p][used]
		table.insert(segs, 1, { i = b.from, j = p - 1, opt = b.opt })
		p, used = b.from, b.used
	end
	local mods: { Modifier } = {}
	local extras: { string } = {}
	local material: string? = nil
	local baseHit: Hit? = nil
	local conf = 1
	local meaningful = 0
	for _, s in segs do
		local o = s.opt
		if o.kind == "Base" then
			baseHit = o.hit
			conf *= o.conf
			meaningful += 1
		elseif o.kind == "Mod" and o.mod then
			table.insert(mods, o.mod)
			if o.mod.kind == "Material" then
				material = o.mod.id
			end
			conf *= o.conf
			meaningful += 1
		elseif o.kind == "Extra" then
			for k = s.i, s.j do
				table.insert(extras, tokens[k])
			end
		end
	end
	conf *= (cfg().ExtraPenalty :: number) ^ #extras
	if baseHit == nil then
		local r = emptyResult(tokens)
		r.modifiers = mods
		r.material = material
		r.extras = extras
		r.confidence = 0
		return r, false
	end
	local method: CorrectionMethod = if meaningful == 1 then baseHit.method else "MultiWord"
	return {
		canonical = Library.idOf(baseHit.ord),
		confidence = math.clamp(conf, 0, 1),
		method = method,
		alternatives = altStrings(baseHit.alts, mods),
		tokens = tokens,
		modifiers = mods,
		material = material,
		extras = extras,
	}, true
end

-- "giantshark" / "spaghettidragon": modifier or material glued to a base thing.
local function compoundSplit(tok: string): SpellResult?
	local n = #tok
	for p = n - 3, 3, -1 do
		local left, right = string.sub(tok, 1, p), string.sub(tok, p + 1)
		local mod: Modifier? = Modifiers.lookup(left)
		if mod == nil then
			local id = Library.lookupMaterial(left)
			if id then
				mod = Modifiers.material(id)
			end
		end
		if mod then
			local h = cheapLookup(right)
			if h then
				return {
					canonical = Library.idOf(h.ord),
					confidence = 0.9 * h.conf,
					method = "MultiWord",
					alternatives = {},
					tokens = { left, right },
					modifiers = { mod },
					material = if mod.kind == "Material" then mod.id else nil,
					extras = {},
				}
			end
		end
	end
	return nil
end

-- Replace protected names (brands, franchises, real people) with their generic idea; drop stripped words.
local function applyProtected(tokens: { string }): ({ string }, boolean)
	local p = loadProtected()
	local out: { string } = {}
	local changed = false
	local i = 1
	while i <= #tokens do
		local replaced = false
		for len = math.min(4, #tokens - i + 1), 1, -1 do
			local phrase = table.concat(tokens, " ", i, i + len - 1)
			local rep = p.names[phrase]
			if rep then
				for _, w in string.split(rep, " ") do
					table.insert(out, w)
				end
				i += len
				replaced = true
				changed = true
				break
			end
		end
		if not replaced then
			if p.strip[tokens[i]] and #tokens > 1 then
				changed = true
			else
				table.insert(out, tokens[i])
			end
			i += 1
		end
	end
	return out, changed
end

local function expandTokens(tokens: { string }): { string }
	local out = {}
	for _, t in tokens do
		if string.find(t, "-", 1, true) and Library.keyInfo(t) == nil and Modifiers.lookup(t) == nil then
			for _, part in string.split(t, "-") do
				if part ~= "" then
					table.insert(out, part)
				end
			end
		else
			table.insert(out, t)
		end
	end
	return out
end

local function correctUncached(text: string, norm: string): SpellResult
	local light = Normalizer.light(text)
	local tokens = string.split(norm, " ")
	local protectedHit = false
	tokens, protectedHit = applyProtected(tokens)
	if #tokens == 0 then
		return emptyResult({})
	end

	-- whole phrase, cheap
	if not protectedHit then
		for _, form in Normalizer.variants(text) do
			local h = cheapLookup(form)
			if h then
				if form ~= light and (h.method == "Exact" or h.method == "Alias") then
					h.method = "Normalized"
					h.conf = 0.97
				end
				return fromHit(h, tokens)
			end
		end
	else
		local h = cheapLookup(table.concat(tokens, " "))
		if h then
			local r = fromHit(h, tokens)
			r.method = "MultiWord"
			r.confidence = math.min(r.confidence, 0.88)
			return r
		end
	end

	tokens = expandTokens(tokens)
	local maxTokens = cfg().MaxTokens
	local overflow: { string } = {}
	while #tokens > maxTokens do
		table.insert(overflow, 1, table.remove(tokens) :: string)
	end

	local result: SpellResult
	if #tokens == 1 then
		local tok = tokens[1]
		local best: SpellResult? = nil
		local h = fuzzyLookup(tok)
		if h then
			best = fromHit(h, tokens)
		end
		if best == nil or best.confidence < 0.85 then
			local split = compoundSplit(tok)
			if split and (best == nil or split.confidence > best.confidence) then
				best = split
			end
		end
		if best == nil then
			-- a lone modifier / material ("giant", "spaghetti"): nothing to apply it to
			local r = parsePhrase(tokens)
			best = r
		end
		result = best :: SpellResult
	else
		result = parsePhrase(tokens)
		-- a typo'd multi-word library phrase ("tyranosaurus reks") may beat the segmentation
		if result.confidence < 0.85 then
			local joined = table.concat(tokens, " ")
			if #joined <= 24 then
				local h = fuzzyLookup(joined)
				if h and h.conf > result.confidence then
					result = fromHit(h, tokens)
				end
			end
		end
	end
	if #overflow > 0 then
		for _, w in overflow do
			table.insert(result.extras, w)
		end
		result.confidence *= (cfg().ExtraPenalty :: number) ^ #overflow
	end
	if protectedHit then
		result.confidence = math.min(result.confidence, 0.88)
		if result.method ~= nil then
			result.method = "MultiWord"
		end
	end
	return result
end

function Speller.correct(text: string): SpellResult
	if type(text) ~= "string" then
		return emptyResult({})
	end
	local norm = Normalizer.normalize(text)
	if norm == "" then
		return emptyResult({})
	end
	-- cache key includes the light form so "Dragon" (Exact) and "dr4gon" (Normalized) keep their own method
	local key = norm .. "\0" .. Normalizer.light(text)
	local cached = cache:get(key)
	if cached then
		return copyResult(cached)
	end
	local ok, result = pcall(correctUncached, text, norm)
	if not ok then
		warn("[WordEngine.Speller] correct failed: " .. tostring(result))
		result = emptyResult(string.split(norm, " "))
	end
	cache:set(key, result)
	return copyResult(result)
end

-- Single word through the library-only ladder (exact -> stem -> misspelling -> fuzzy -> phonetic).
function Speller.correctWord(word: string): SpellResult
	local norm = Normalizer.normalize(word)
	local h = cheapLookup(norm) or fuzzyLookup(norm)
	if h then
		return fromHit(h, { norm })
	end
	return emptyResult({ norm })
end

function Speller.clearCache()
	cache:clear()
end

function Speller.cacheStats(): { hits: number, misses: number, size: number }
	return { hits = cache.hits, misses = cache.misses, size = cache.size }
end

function Speller.preload()
	Library.preload()
	Fuzzy.preload()
	Modifiers.vocabulary()
end

return Speller
