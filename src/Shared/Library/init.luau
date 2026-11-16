--!strict
-- Library: the compiled word library (src/Shared/Library/Generated, built by tools/build_library.py).
--
--   Library.get(id)                 -> WordResult? (fresh copy, safe to mutate)
--   Library.lookup(word)            -> canonical id for an id / alias / plural / spacing variant ("t rex", "firedragon")
--   Library.synonymGroup(word)      -> no-repeat group ("kitty" -> "cat")
--   Library.isSignature(id), Library.count()
--   Library.prefixSearch(prefix, n) -> autocomplete keys, best first (one key per word)
--   Library.random(filter?)         -> WordResult (bots / empty-slot autofill; deterministic with filter.rng)
--   Library.material(id)            -> Types.Material? (shared frozen record; do not mutate)
--   Library.lookupMaterial(word)    -> material id for an id / alias / known misspelling / plural
--
-- Everything loads lazily on first use: Index (ids, ranks, packed attrs) -> Keys shards (lookup + autocomplete)
-- -> Chunk_NNN (entry bodies, only the chunk that holds a requested id). No Roblox services are touched.

local Types = require(script.Parent.Types)
local Schema = require(script.Parent.Schema)
local Normalizer = require(script.Parent.Normalizer)
local Stemmer = require(script.Parent.Speller.Stemmer)

type WordResult = Types.WordResult

export type RandomFilter = {
	shape: string?,
	element: string?,
	category: string?,
	size: string?,
	excludeGroups: { [string]: boolean }?,
	signatureOnly: boolean?,
	rng: Random?,
}

-- Key kinds returned by Library.keyInfo
export type KeyKind = "Id" | "Alias" | "Variant" | "Misspelling"

local Library = {}

local Generated = script.Generated

type IndexData = {
	version: string,
	count: number,
	chunkSize: number,
	chunks: number,
	keyShards: number,
	missShards: number,
	code: string,
	enums: { [string]: { string } },
	ids: { string },
	rank: { number },
	attrs: string,
	signature: { number },
	groups: { [number]: string },
	prefix: { [string]: { number } },
}

local index: IndexData? = nil
local ordById: { [string]: number } = {}
local sigSet: { [number]: boolean } = {}
local codeIndex: { [number]: number } = {} -- byte of CODE char -> 1-based enum index

local keysLoaded = false
local keys: { string } = {}
local keyOwner: { number } = {}
local keyPhon: { string } = {}
local keyIsId: { boolean } = {}
local keyMap: { [string]: number } = {} -- authored key -> ord
local keyKind: { [string]: KeyKind } = {}
local variantMap: { [string]: number } = {} -- spacing variants of authored keys -> ord
local missMap: { [string]: number } = {}

local chunkCache: { [number]: { { any } } } = {}
local templates: { [number]: WordResult } = {}

local function loadIndex(): IndexData
	local idx = index
	if idx then
		return idx
	end
	local data = require(Generated:FindFirstChild("Index") :: any) :: IndexData
	for i, id in data.ids do
		ordById[id] = i
	end
	for _, o in data.signature do
		sigSet[o] = true
	end
	for i = 1, #data.code do
		codeIndex[string.byte(data.code, i)] = i
	end
	index = data
	return data
end

local function loadKeys()
	if keysLoaded then
		return
	end
	local idx = loadIndex()
	for s = 1, idx.keyShards do
		local shard = require(Generated:FindFirstChild(string.format("Keys_%02d", s)) :: any) :: any
		local base = #keys
		for i, k in shard.keys do
			local o = shard.owners[i]
			local isId = string.sub(shard.kinds, i, i) == "I"
			keys[base + i] = k
			keyOwner[base + i] = o
			keyPhon[base + i] = shard.phon[i]
			keyIsId[base + i] = isId
			keyMap[k] = o
			keyKind[k] = if isId then "Id" else "Alias"
		end
	end
	-- Spacing variants ("t-rex" -> "t rex", "trex"; "fire dragon" -> "firedragon"). Ambiguous ones are dropped.
	local ambiguous: { [string]: boolean } = {}
	local function addVariant(v: string, o: number)
		if keyMap[v] ~= nil or ambiguous[v] then
			return
		end
		local prev = variantMap[v]
		if prev ~= nil and prev ~= o then
			variantMap[v] = nil
			ambiguous[v] = true
		else
			variantMap[v] = o
		end
	end
	for i, k in keys do
		if string.find(k, "[ %-']") then
			local o = keyOwner[i]
			addVariant((string.gsub(k, "[ %-']", "")), o)
			if string.find(k, "-", 1, true) then
				addVariant((string.gsub(k, "%-", " ")), o)
			end
			if string.find(k, "'", 1, true) then
				addVariant((string.gsub(k, "'", "")), o)
			end
			if string.find(k, " ", 1, true) then
				addVariant((string.gsub(k, " ", "-")), o)
			end
		end
	end
	for s = 1, idx.missShards do
		local inst = Generated:FindFirstChild(string.format("Miss_%02d", s))
		if inst then
			local shard = require(inst :: any) :: any
			for i, k in shard.keys do
				missMap[k] = shard.owners[i]
			end
		end
	end
	keysLoaded = true
end

local function enumAt(idx: IndexData, kind: string, ch: number): string
	return idx.enums[kind][codeIndex[ch]]
end

local function decode(idx: IndexData, ord: number, row: { any }): WordResult
	local enums = row[2] :: string
	local behaviours = {}
	local bs = row[3] :: string
	for i = 1, #bs do
		table.insert(behaviours, enumAt(idx, "Behaviour", string.byte(bs, i)))
	end
	table.sort(behaviours)
	local tags = {}
	if row[12] ~= "" then
		tags = string.split(row[12] :: string, ",")
	end
	local id = row[1] :: string
	return {
		schemaVersion = Schema.VERSION,
		id = id,
		canonical = id,
		input = "",
		confidence = 1,
		source = "Library",
		correction = nil,
		category = enumAt(idx, "Category", string.byte(enums, 1)) :: any,
		element = enumAt(idx, "Element", string.byte(enums, 2)) :: any,
		secondaryElement = "None",
		material = nil,
		mood = "Neutral",
		size = enumAt(idx, "Size", string.byte(enums, 3)) :: any,
		shape = enumAt(idx, "Shape", string.byte(enums, 4)) :: any,
		behaviours = behaviours,
		power = row[4] :: number,
		speed = row[5] :: number,
		durability = row[6] :: number,
		count = 1,
		modifiers = {},
		signature = sigSet[ord] == true,
		synonymGroup = idx.groups[ord] or id,
		visual = {
			primaryColour = "#" .. (row[7] :: string),
			secondaryColour = "#" .. (row[8] :: string),
			bodyPlan = enumAt(idx, "BodyPlan", string.byte(enums, 5)) :: any,
			silhouetteHint = row[9] :: string,
			motionHint = enumAt(idx, "Motion", string.byte(enums, 6)) :: any,
			soundHint = row[10] :: string,
			accents = {},
		},
		flavourText = row[11] :: string,
		tags = tags,
	}
end

local function template(ord: number): WordResult?
	local cached = templates[ord]
	if cached then
		return cached
	end
	local idx = loadIndex()
	if ord < 1 or ord > idx.count then
		return nil
	end
	local c = (ord - 1) // idx.chunkSize + 1
	local chunk = chunkCache[c]
	if chunk == nil then
		chunk = require(Generated:FindFirstChild(string.format("Chunk_%03d", c)) :: any) :: any
		chunkCache[c] = chunk :: any
	end
	local row = (chunk :: any)[(ord - 1) % idx.chunkSize + 1]
	if row == nil then
		return nil
	end
	local r = decode(idx, ord, row)
	templates[ord] = r
	return r
end

-- ------------------------------------------------------------------ public API

function Library.count(): number
	return loadIndex().count
end

function Library.version(): string
	return loadIndex().version
end

function Library.get(id: string): WordResult?
	if type(id) ~= "string" then
		return nil
	end
	loadIndex()
	local ord = ordById[id]
	if ord == nil then
		return nil
	end
	local t = template(ord)
	return if t then Schema.clone(t) else nil
end

-- Strict key lookup on an already-normalized key: authored keys, spacing variants. Returns ord + kind.
function Library.keyInfo(key: string): (number?, KeyKind?)
	loadKeys()
	local o = keyMap[key]
	if o then
		return o, keyKind[key]
	end
	o = variantMap[key]
	if o then
		return o, "Variant"
	end
	return nil, nil
end

function Library.misspelling(key: string): number?
	loadKeys()
	return missMap[key]
end

function Library.lookup(word: string): string?
	if type(word) ~= "string" then
		return nil
	end
	local idx = loadIndex()
	local tried: { [string]: boolean } = {}
	for _, form in { Normalizer.light(word), Normalizer.normalize(word) } do
		if form ~= "" and not tried[form] then
			tried[form] = true
			local o = Library.keyInfo(form)
			if o then
				return idx.ids[o]
			end
			for _, c in Stemmer.plurals(form) do
				local p = Library.keyInfo(c.word)
				if p then
					return idx.ids[p]
				end
			end
		end
	end
	return nil
end

function Library.synonymGroup(word: string): string?
	local id = Library.lookup(word)
	if id == nil then
		return nil
	end
	local idx = loadIndex()
	return idx.groups[ordById[id]] or id
end

function Library.isSignature(id: string): boolean
	loadIndex()
	local o = ordById[id]
	return o ~= nil and sigSet[o] == true
end

-- Internal accessors for Speller / Suggest (stable within this package; games should not depend on them).
function Library.idOf(ord: number): string
	return loadIndex().ids[ord]
end

function Library.ordOf(id: string): number?
	loadIndex()
	return ordById[id]
end

function Library.rankOf(ord: number): number
	return loadIndex().rank[ord] or 0
end

function Library.signatureOrd(ord: number): boolean
	loadIndex()
	return sigSet[ord] == true
end

function Library.keyArrays(): ({ string }, { number }, { string }, { boolean })
	loadKeys()
	return keys, keyOwner, keyPhon, keyIsId
end

function Library.preload()
	loadKeys()
end

-- First index i with keys[i] >= p.
local function lowerBound(p: string): number
	local lo, hi = 1, #keys + 1
	while lo < hi do
		local mid = (lo + hi) // 2
		if keys[mid] < p then
			lo = mid + 1
		else
			hi = mid
		end
	end
	return lo
end

local MAX_PREFIX_SCAN = 4000

function Library.prefixSearch(prefix: string, limit: number?): { string }
	local n = math.clamp(math.floor(limit or 8), 1, 50)
	if type(prefix) ~= "string" then
		return {}
	end
	local p = string.gsub(string.lower(prefix), "^%s+", "")
	p = string.gsub(p, "%s+", " ")
	if p == "" then
		return {}
	end
	local idx = loadIndex()
	loadKeys()
	local pre = idx.prefix[p]
	if pre then
		local out = {}
		for i = 1, math.min(n, #pre) do
			out[i] = keys[pre[i]]
		end
		return out
	end
	-- best key per owner: prefer the id itself, then the shortest alias
	local bestKey: { [number]: number } = {}
	local owners: { number } = {}
	local i = lowerBound(p)
	local plen = #p
	local scanned = 0
	while i <= #keys and scanned < MAX_PREFIX_SCAN do
		local k = keys[i]
		if string.sub(k, 1, plen) ~= p then
			break
		end
		local o = keyOwner[i]
		local cur = bestKey[o]
		if cur == nil then
			bestKey[o] = i
			table.insert(owners, o)
		elseif (keyIsId[i] and not keyIsId[cur]) or (keyIsId[i] == keyIsId[cur] and #k < #keys[cur]) then
			bestKey[o] = i
		end
		i += 1
		scanned += 1
	end
	local rank = idx.rank
	table.sort(owners, function(a, b)
		local ra, rb = rank[a], rank[b]
		if ra ~= rb then
			return ra > rb
		end
		local ka, kb = keys[bestKey[a]], keys[bestKey[b]]
		if #ka ~= #kb then
			return #ka < #kb
		end
		return ka < kb
	end)
	local out = {}
	for j = 1, math.min(n, #owners) do
		out[j] = keys[bestKey[owners[j]]]
	end
	return out
end

local ATTR_FIELDS = { category = { 1, "Category" }, element = { 2, "Element" }, size = { 3, "Size" }, shape = { 4, "Shape" } }

function Library.random(filter: RandomFilter?): WordResult
	local idx = loadIndex()
	local f: RandomFilter = filter or {}
	-- expected CODE byte per attribute slot
	local want: { [number]: number } = {}
	for field, spec in ATTR_FIELDS do
		local value = (f :: any)[field]
		if value ~= nil then
			local pos = table.find(idx.enums[spec[2]], value)
			if pos == nil then
				return Schema.fallback("")
			end
			want[spec[1]] = string.byte(idx.code, pos)
		end
	end
	local exclude = f.excludeGroups
	local matches: { number } = {}
	local attrs = idx.attrs
	for ord = 1, idx.count do
		local ok = true
		local base = (ord - 1) * 4
		for slot, b in want do
			if string.byte(attrs, base + slot) ~= b then
				ok = false
				break
			end
		end
		if ok and f.signatureOnly and not sigSet[ord] then
			ok = false
		end
		if ok and exclude then
			local g = idx.groups[ord] or idx.ids[ord]
			if exclude[g] then
				ok = false
			end
		end
		if ok then
			table.insert(matches, ord)
		end
	end
	if #matches == 0 then
		return Schema.fallback("")
	end
	local pick: number
	local rng: any = f.rng
	if rng ~= nil then
		pick = rng:NextInteger(1, #matches)
	else
		pick = math.random(1, #matches)
	end
	local t = template(matches[pick])
	return if t then Schema.clone(t) else Schema.fallback("")
end

-- ------------------------------------------------------------------ materials

local materials: { [string]: Types.Material }? = nil
local materialWords: { [string]: string } = {} -- id / alias -> id
local materialMisspellings: { [string]: string } = {}

local function deepFreeze(t: any): any
	for _, v in t do
		if type(v) == "table" and not table.isfrozen(v) then
			deepFreeze(v)
		end
	end
	return table.freeze(t)
end

local function loadMaterials(): { [string]: Types.Material }
	local m = materials
	if m then
		return m
	end
	local out: { [string]: Types.Material } = {}
	local inst = Generated:FindFirstChild("Materials")
	if inst then
		for _, rec in require(inst :: any) :: any do
			out[rec.id] = deepFreeze(rec)
			materialWords[rec.id] = rec.id
			for _, a in rec.aliases do
				if materialWords[a] == nil then
					materialWords[a] = rec.id
				end
			end
			for _, a in rec.misspellings or {} do
				if materialWords[a] == nil and materialMisspellings[a] == nil then
					materialMisspellings[a] = rec.id
				end
			end
		end
	end
	materials = out
	return out
end

function Library.material(id: string): Types.Material?
	if type(id) ~= "string" then
		return nil
	end
	return loadMaterials()[id]
end

-- Returns (id, isMisspelling). Strict: no fuzzy matching (the Speller does that).
function Library.lookupMaterial(word: string): (string?, boolean)
	if type(word) ~= "string" then
		return nil, false
	end
	loadMaterials()
	local form = Normalizer.light(word)
	if form == "" then
		return nil, false
	end
	local id = materialWords[form]
	if id then
		return id, false
	end
	for _, v in Normalizer.spacingVariants(form) do
		id = materialWords[v]
		if id then
			return id, false
		end
	end
	for _, c in Stemmer.plurals(form) do
		id = materialWords[c.word]
		if id then
			return id, false
		end
	end
	id = materialMisspellings[form]
	if id then
		return id, true
	end
	return nil, false
end

-- All material words (ids + aliases + misspellings) for fuzzy matching. Allocates.
function Library.materialWords(): { [string]: string }
	loadMaterials()
	local out = table.clone(materialWords)
	for k, v in materialMisspellings do
		out[k] = out[k] or v
	end
	return out
end

-- All ids in ordinal (sorted) order. Allocates; for tools/tests.
function Library.ids(): { string }
	return table.clone(loadIndex().ids)
end

return Library
