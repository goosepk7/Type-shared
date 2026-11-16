--!strict
-- Fuzzy candidate search over the library's authored keys (ids + aliases).
--
-- Candidate generation (built lazily on first fuzzy query, then reused):
--   1. edits-1 neighbourhood of the typed word (delete / transpose / substitute / insert) against the key hash:
--      exhaustive for one edit, ~50n hash probes, the main path for short words.
--   2. padded-bigram inverted index bucketed by key length: keys sharing the most bigrams with the typed word
--      (length within +-3) are the multi-edit candidates for words >= 5 letters.
--   3. Double Metaphone codes (precomputed by the build) for sound-alike spellings ("fenix" -> phoenix).
-- Every candidate is then scored with the keyboard-weighted Damerau-Levenshtein (Distance.luau).
-- Why not a BK-tree: weighted keyboard costs break the triangle inequality, and a precomputed deletion index for
-- 30k+ keys would be several MB of committed source. The bigram index is built at runtime from the keys in
-- ~15-40 ms (see tools/bench_speller.luau) and costs no download.

local Library = require(script.Parent.Parent.Library)
local Distance = require(script.Parent.Distance)
local Metaphone = require(script.Parent.Metaphone)

local Fuzzy = {}

export type Candidate = { key: number, cost: number, phonetic: boolean }

local built = false
local keys: { string } = {}
local owners: { number } = {}
local isId: { boolean } = {}
local keyIndex: { [string]: number } = {}
local postings: { [number]: { number } } = {} -- bigramCode * 64 + len -> key indices
local phonMap: { [string]: { number } } = {}

local START, FINISH = 1, 2
local MAX_LEN = 63

local function bigramCode(a: number, b: number, len: number): number
	return (a * 256 + b) * 64 + len
end

local function build()
	if built then
		return
	end
	local k, o, phon, ids = Library.keyArrays()
	keys, owners, isId = k, o, ids
	for i, key in keys do
		keyIndex[key] = i
		local n = #key
		if n <= MAX_LEN then
			local prev = START
			for j = 1, n + 1 do
				local b = if j <= n then string.byte(key, j) else FINISH
				local code = bigramCode(prev, b, n)
				local list = postings[code]
				if list == nil then
					postings[code] = { i }
				elseif list[#list] ~= i then -- a key repeats a bigram: count it once
					list[#list + 1] = i
				end
				prev = b
			end
		end
		local code = phon[i]
		if code ~= "" then
			local slash = string.find(code, "/", 1, true)
			local a = if slash then string.sub(code, 1, slash - 1) else code
			local list = phonMap[a]
			if list == nil then
				phonMap[a] = { i }
			else
				list[#list + 1] = i
			end
			if slash then
				local b2 = string.sub(code, slash + 1)
				local l2 = phonMap[b2]
				if l2 == nil then
					phonMap[b2] = { i }
				elseif l2[#l2] ~= i then
					l2[#l2 + 1] = i
				end
			end
		end
	end
	built = true
end

function Fuzzy.preload()
	build()
end

function Fuzzy.keyAt(i: number): (string, number, boolean)
	return keys[i], owners[i], isId[i]
end

local ALPHABET = "abcdefghijklmnopqrstuvwxyz"

-- Reused scratch tables
local counts: { [number]: number } = {}
local touched: { number } = {}

local function addCandidate(found: { [number]: Candidate }, out: { Candidate }, i: number, cost: number, phonetic: boolean)
	local cur = found[i]
	if cur == nil then
		local c = { key = i, cost = cost, phonetic = phonetic }
		found[i] = c
		table.insert(out, c)
	elseif cost < cur.cost then
		cur.cost = cost
	end
	if phonetic and cur then
		cur.phonetic = true
	end
end

-- Search keys within maxCost of `word`. Phonetic matches are allowed up to maxCost + phoneticExtra.
-- Returns candidates sorted by cost (ties: owner rank desc), at most `limit` distinct owners.
function Fuzzy.search(word: string, maxCost: number, phoneticExtra: number, candidateLimit: number): { Candidate }
	build()
	local n = #word
	local out: { Candidate } = {}
	local found: { [number]: Candidate } = {}
	if n == 0 or n > MAX_LEN then
		return out
	end
	local q = Distance.prepare(word)
	local checked: { [number]: boolean } = {}
	local function score(i: number, limit: number, phonetic: boolean)
		if checked[i] and not phonetic then
			return
		end
		checked[i] = true
		local c = Distance.weighted(q, keys[i], limit)
		if c <= limit then
			addCandidate(found, out, i, c, phonetic)
		end
	end

	if maxCost > 0 and n <= 8 then
		-- 1. edits-1 neighbourhood (long words are covered by the bigram pass below, which is cheaper for them)
		local function probe(s: string)
			local i = keyIndex[s]
			if i then
				score(i, maxCost, false)
			end
		end
		for p = 1, n do
			probe(string.sub(word, 1, p - 1) .. string.sub(word, p + 1))
			if p < n then
				probe(string.sub(word, 1, p - 1) .. string.sub(word, p + 1, p + 1) .. string.sub(word, p, p) .. string.sub(word, p + 2))
			end
		end
		for p = 1, n + 1 do
			local head, tail = string.sub(word, 1, p - 1), string.sub(word, p)
			local tail1 = string.sub(word, p + 1)
			for c = 1, 26 do
				local ch = string.sub(ALPHABET, c, c)
				probe(head .. ch .. tail)
				if p <= n then
					probe(head .. ch .. tail1)
				end
			end
		end

	end
	if maxCost > 0 then
		-- 2. bigram candidates for longer words (multi-edit typos)
		if n >= 5 then
			local lenSlack = math.min(if n >= 8 then 3 else 2, math.ceil(maxCost))
			-- gather the posting lists per query bigram; very common bigrams ("er", "in" at common lengths)
			-- discriminate little and dominate the cost, so the longest lists are skipped (prefix filtering)
			local seenGram: { [number]: boolean } = {}
			local gramLists: { { list: { { number } }, size: number } } = {}
			local prev = START
			for j = 1, n + 1 do
				local b = if j <= n then string.byte(word, j) else FINISH
				local g = prev * 256 + b
				if not seenGram[g] then
					seenGram[g] = true
					local lists, size = {}, 0
					for len = math.max(1, n - lenSlack), math.min(MAX_LEN, n + lenSlack) do
						local list = postings[g * 64 + len]
						if list then
							table.insert(lists, list)
							size += #list
						end
					end
					table.insert(gramLists, { list = lists, size = size })
				end
				prev = b
			end
			table.sort(gramLists, function(x, y)
				return x.size < y.size
			end)
			local grams = #gramLists
			local keep = math.max(3, math.ceil(grams * 0.7))
			for gi = 1, math.min(keep, grams) do
				for _, list in gramLists[gi].list do
					for _, i in list do
						local c = counts[i]
						if c == nil then
							counts[i] = 1
							table.insert(touched, i)
						else
							counts[i] = c + 1
						end
					end
				end
			end
			grams = math.min(keep, grams)
			-- bucket by shared count, take the best `candidateLimit`
			local need = math.max(2, grams - 2 * math.ceil(maxCost) - 1)
			local buckets: { [number]: { number } } = {}
			local top = 0
			for _, i in touched do
				local c = counts[i]
				if c >= need then
					local bkt = buckets[c]
					if bkt == nil then
						bkt = {}
						buckets[c] = bkt
					end
					table.insert(bkt, i)
					if c > top then
						top = c
					end
				end
				counts[i] = nil
			end
			table.clear(touched)
			local taken = 0
			for c = top, need, -1 do
				local bkt = buckets[c]
				if bkt then
					for _, i in bkt do
						score(i, maxCost, false)
						taken += 1
						if taken >= candidateLimit then
							break
						end
					end
				end
				if taken >= candidateLimit then
					break
				end
			end
		end
	end

	-- 3. phonetic
	local bestSoFar = math.huge
	for _, c in out do
		if c.cost < bestSoFar then
			bestSoFar = c.cost
		end
	end
	-- a clear one-slip match needs no sound-alike search
	if phoneticExtra > 0 and n >= 3 and bestSoFar > 0.6 then
		local p, s = Metaphone.encode(word)
		local limit = maxCost + phoneticExtra
		for _, code in { p, s } do
			local list = if code ~= "" then phonMap[code] else nil
			if list then
				local scored = 0
				for _, i in list do
					if math.abs(#keys[i] - n) <= 3 then
						score(i, limit, true)
						scored += 1
						if scored >= 150 then
							break
						end
					end
				end
			end
		end
	end

	table.sort(out, function(a, b)
		if a.cost ~= b.cost then
			return a.cost < b.cost
		end
		local ra, rb = Library.rankOf(owners[a.key]), Library.rankOf(owners[b.key])
		if ra ~= rb then
			return ra > rb
		end
		return keys[a.key] < keys[b.key]
	end)
	return out
end

-- Brute-force weighted search over a small vocabulary (modifier / material words). Returns (word, cost)s sorted.
function Fuzzy.searchList(word: string, vocab: { string }, maxCost: number): { { word: string, cost: number } }
	local out = {}
	if maxCost <= 0 then
		return out
	end
	local q = Distance.prepare(word)
	local n = #word
	for _, v in vocab do
		if math.abs(#v - n) <= 3 then
			local c = Distance.weighted(q, v, maxCost)
			if c <= maxCost then
				table.insert(out, { word = v, cost = c })
			end
		end
	end
	table.sort(out, function(a, b)
		if a.cost ~= b.cost then
			return a.cost < b.cost
		end
		return a.word < b.word
	end)
	return out
end

return Fuzzy
