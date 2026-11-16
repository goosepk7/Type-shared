--!strict
-- Weighted Damerau-Levenshtein (optimal string alignment) tuned for how players actually mistype:
--   * substitution cost by keyboard distance (cheapest of QWERTY / phone / QWERTZ / AZERTY, data/keyboard.json),
--     phonetic look-alikes (c/k, s/z, i/y...) and vowel swaps are cheap
--   * doubled / missing double letters are cheap ("ballon", "dragonn"), fat-finger insertions of a key next to
--     its neighbour are cheaper than random insertions, a dropped vowel is cheaper than a dropped consonant
--   * transpositions are cheap ("dargon"); edits at the first letter cost extra (people rarely miss it)
-- `typed` is what the player wrote, `target` the library key. Returns math.huge once maxCost is exceeded.

local KB = require(script.Parent.Parent.Library.Generated.Keyboard)

local Distance = {}

local C = KB.costs
local SUBST: number = C.substitute
local VOWEL_SWAP: number = C.vowelSwap
local INSERT: number = C.insert
local DELETE: number = C.delete
local DOUBLED: number = C.doubledLetter
local FAT_FINGER: number = C.fatFingerInsert
local MISSING_VOWEL: number = C.missingVowel
local TRANSPOSE: number = C.transpose
local FIRST: number = C.firstLetterPenalty
local SPACE: number = C.space

local SUB: { [number]: number } = {}
for pair, cost in KB.sub do
	SUB[string.byte(pair, 1) * 256 + string.byte(pair, 2)] = cost
end

local IS_VOWEL: { [number]: boolean } = {}
for _, ch in { "a", "e", "i", "o", "u" } do
	IS_VOWEL[string.byte(ch)] = true
end
local SPACE_BYTE = string.byte(" ")
local HYPHEN_BYTE = string.byte("-")
local APOS_BYTE = string.byte("'")
local function isSep(b: number): boolean
	return b == SPACE_BYTE or b == HYPHEN_BYTE or b == APOS_BYTE
end

local function subCost(x: number, y: number): number
	if x == y then
		return 0
	end
	if isSep(x) and isSep(y) then
		return SPACE * 0.5
	end
	local c = SUB[x * 256 + y]
	if c then
		return c
	end
	if IS_VOWEL[x] and IS_VOWEL[y] then
		return VOWEL_SWAP
	end
	return SUBST
end
Distance.subCost = subCost

export type Prepared = { s: string, n: number, bytes: { number }, del: { number } }

-- Precompute per-query data once; reuse across every candidate.
function Distance.prepare(typed: string): Prepared
	local n = #typed
	local bytes = table.create(n, 0)
	for i = 1, n do
		bytes[i] = string.byte(typed, i)
	end
	local del = table.create(n, DELETE)
	for i = 1, n do
		local b = bytes[i]
		local prev = bytes[i - 1]
		local nxt = bytes[i + 1]
		local c = DELETE
		if (prev and prev == b) or (nxt and nxt == b) then
			c = DOUBLED
		elseif isSep(b) then
			c = SPACE
		else
			local adj = math.min(if prev then subCost(b, prev) else 99, if nxt then subCost(b, nxt) else 99)
			if adj <= 0.55 then
				c = FAT_FINGER
			end
		end
		if i == 1 then
			c += FIRST
		end
		del[i] = c
	end
	return { s = typed, n = n, bytes = bytes, del = del }
end

-- Reused DP rows (module-level to avoid allocation per call).
local row0: { number } = {}
local row1: { number } = {}
local row2: { number } = {}
local tb: { number } = {}
local ins: { number } = {}

function Distance.weighted(q: Prepared, target: string, maxCost: number): number
	local la = q.n
	local lb = #target
	local a = q.bytes
	local del = q.del
	for j = 1, lb do
		tb[j] = string.byte(target, j)
	end
	-- insertion costs (typed text is missing target[j])
	for j = 1, lb do
		local b = tb[j]
		local c
		if j > 1 and tb[j - 1] == b then
			c = DOUBLED
		elseif isSep(b) then
			c = SPACE
		elseif IS_VOWEL[b] then
			c = MISSING_VOWEL
		else
			c = INSERT
		end
		if j == 1 then
			c += FIRST
		end
		ins[j] = c
	end
	-- quick length bound: every missing/extra char costs at least DOUBLED
	if math.abs(la - lb) * DOUBLED > maxCost then
		return math.huge
	end
	local prev2, prev, cur = row2, row1, row0
	prev[1] = 0
	for j = 1, lb do
		prev[j + 1] = prev[j] + ins[j]
	end
	for i = 1, la do
		local ai = a[i]
		local di = del[i]
		cur[1] = prev[1] + di
		local rowMin = cur[1]
		for j = 1, lb do
			local bj = tb[j]
			local v
			if ai == bj then
				v = prev[j]
			else
				local s = subCost(ai, bj)
				if i == 1 and j == 1 then
					s += FIRST
				end
				v = prev[j] + s
			end
			local d = prev[j + 1] + di
			if d < v then
				v = d
			end
			local n = cur[j] + ins[j]
			if n < v then
				v = n
			end
			if i > 1 and j > 1 and ai == tb[j - 1] and a[i - 1] == bj and ai ~= bj then
				local t = prev2[j - 1] + TRANSPOSE
				if t < v then
					v = t
				end
			end
			cur[j + 1] = v
			if v < rowMin then
				rowMin = v
			end
		end
		if rowMin > maxCost then
			return math.huge
		end
		prev2, prev, cur = prev, cur, prev2
	end
	local result = prev[lb + 1]
	if result > maxCost then
		return math.huge
	end
	return result
end

-- Convenience for one-off comparisons.
function Distance.between(typed: string, target: string, maxCost: number?): number
	return Distance.weighted(Distance.prepare(typed), target, maxCost or math.huge)
end

-- Plain (unit cost) OSA distance, used for confidence and tests.
function Distance.unit(a: string, b: string): number
	local la, lb = #a, #b
	local d: { { number } } = {}
	for i = 0, la do
		d[i] = { [0] = i }
	end
	for j = 0, lb do
		d[0][j] = j
	end
	for i = 1, la do
		for j = 1, lb do
			local cost = if string.byte(a, i) == string.byte(b, j) then 0 else 1
			local v = math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
			if i > 1 and j > 1 and string.byte(a, i) == string.byte(b, j - 1) and string.byte(a, i - 1) == string.byte(b, j) then
				v = math.min(v, d[i - 2][j - 2] + 1)
			end
			d[i][j] = v
		end
	end
	return d[la][lb]
end

return Distance
