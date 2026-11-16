--!strict
-- Server-only blocklist. Stores NO plaintext: every entry is a 64-bit FNV-1a hash (two 32-bit
-- lanes) of a "skeleton" form of the word, so the list can't be read out of the place file and
-- never replicates (this module lives in ServerScriptService).
--
-- Skeleton: lowercase -> leetspeak digits/symbols to letters -> keep a-z only -> collapse repeats
-- (to 1 letter for collapse=1, to 2 letters for collapse=2). Two collapse levels exist because
-- collapsing to 1 catches "fuuuuck" while collapsing to 2 avoids false positives for words that
-- differ only by a double letter.
--
-- Sets (see BlocklistData, generated from data/blocklist.txt):
--   exact1/exact2       -- a token, or the whole phrase without spaces, equals the entry
--   contains1/contains2 -- the entry appears anywhere in the phrase (only for terms that never
--                          occur inside innocent words: no Scunthorpe problems)

local Blocklist = {}

local LEET: { [string]: string } = {
	["0"] = "o", ["1"] = "i", ["2"] = "z", ["3"] = "e", ["4"] = "a", ["5"] = "s", ["6"] = "g", ["7"] = "t",
	["8"] = "b", ["9"] = "g", ["@"] = "a", ["$"] = "s", ["!"] = "i", ["|"] = "l", ["+"] = "t", ["€"] = "e",
}

local function collapse(s: string, keep: number): string
	local out = table.create(#s)
	local last, run = "", 0
	for i = 1, #s do
		local c = string.sub(s, i, i)
		if c == last then
			run += 1
		else
			last, run = c, 1
		end
		if run <= keep then
			table.insert(out, c)
		end
	end
	return table.concat(out)
end

-- Tokens of the skeleton (split on anything that isn't a letter/leet char).
function Blocklist.tokens(text: string, keep: number): { string }
	local lower = string.lower(text)
	local mapped = string.gsub(lower, "[%d@%$!|%+]", LEET)
	mapped = string.gsub(mapped, "€", "e")
	local out = {}
	for word in string.gmatch(mapped, "[a-z]+") do
		table.insert(out, collapse(word, keep))
	end
	return out
end

function Blocklist.skeleton(text: string, keep: number): string
	return collapse(table.concat(Blocklist.tokens(text, keep)), keep)
end

-- FNV-1a 32-bit without float precision loss: x * 16777619 == (x << 24) + x * 403 (mod 2^32).
local function fnv(s: string, basis: number): number
	local h = basis
	for i = 1, #s do
		h = bit32.bxor(h, string.byte(s, i))
		h = (bit32.lshift(h, 24) + h * 403) % 4294967296
	end
	return h
end

function Blocklist.hash(s: string): string
	return string.format("%08x%08x", fnv(s, 2166136261), fnv(s, 3735928559))
end

type Sets = { exact1: { [string]: boolean }, exact2: { [string]: boolean }, contains1: { [string]: boolean }, contains2: { [string]: boolean }, maxLen: number }

local sets: Sets? = nil
local extra: { [string]: boolean } = {} -- runtime additions (Admin.ban), exact1 semantics

local function load(): Sets
	if sets then
		return sets
	end
	local ok, data = pcall(function()
		return require(script.Parent.BlocklistData) :: any
	end)
	local s: Sets = { exact1 = {}, exact2 = {}, contains1 = {}, contains2 = {}, maxLen = 24 }
	if ok and type(data) == "table" then
		for _, name in { "exact1", "exact2", "contains1", "contains2" } do
			for _, h in data[name] or {} do
				(s :: any)[name][h] = true
			end
		end
		s.maxLen = tonumber(data.maxLen) or 24
	end
	sets = s
	return s
end

local function checkLevel(text: string, keep: number, exact: { [string]: boolean }, contains: { [string]: boolean }, maxLen: number): boolean
	local toks = Blocklist.tokens(text, keep)
	for _, tok in toks do
		if exact[Blocklist.hash(tok)] or (keep == 1 and extra[Blocklist.hash(tok)]) then
			return true
		end
	end
	local whole = collapse(table.concat(toks), keep)
	if whole == "" then
		return false
	end
	if exact[Blocklist.hash(whole)] or (keep == 1 and extra[Blocklist.hash(whole)]) then
		return true
	end
	if next(contains) == nil then
		return false
	end
	-- all substrings of length 3..maxLen (input is <= 40 chars, so at most ~800 hashes)
	local n = #whole
	for i = 1, n do
		for j = i + 2, math.min(n, i + maxLen - 1) do
			if contains[Blocklist.hash(string.sub(whole, i, j))] then
				return true
			end
		end
	end
	return false
end

function Blocklist.isBlocked(text: string): boolean
	if type(text) ~= "string" or text == "" then
		return false
	end
	local s = load()
	return checkLevel(text, 1, s.exact1, s.contains1, s.maxLen) or checkLevel(text, 2, s.exact2, s.contains2, s.maxLen)
end

-- Runtime ban (exact, collapse-1 skeleton). Persistence belongs to Admin.
function Blocklist.add(word: string)
	local sk = Blocklist.skeleton(word, 1)
	if sk ~= "" then
		extra[Blocklist.hash(sk)] = true
	end
end

function Blocklist.remove(word: string)
	extra[Blocklist.hash(Blocklist.skeleton(word, 1))] = nil
end

-- Tests: replace the hash sets (lists of hashes) and clear runtime additions.
function Blocklist._setData(data: any?)
	sets = nil
	table.clear(extra)
	if data then
		local s: Sets = { exact1 = {}, exact2 = {}, contains1 = {}, contains2 = {}, maxLen = data.maxLen or 24 }
		for _, name in { "exact1", "exact2", "contains1", "contains2" } do
			for _, h in data[name] or {} do
				(s :: any)[name][h] = true
			end
		end
		sets = s
	end
end

return Blocklist
