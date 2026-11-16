--!strict
-- Normalizer: turns raw player text into the canonical lookup form. Pure Luau (runs under Lune).
--
--   normalize("  Giant FIIIRE-Shark!!! 🔥 ") -> "giant fiire-shark"
--   normalize("dr4gon")   -> "dragon"      (leetspeak only inside words that have >= 2 letters)
--   normalize("2 headed") -> "two headed"  (standalone 1..20 become words; "100" stays "100")
--   tokenize(text)        -> { "giant", "fiire-shark" }
--
-- Steps: unicode fold (accents, full-width, smart quotes) -> lowercase -> punctuation/emoji become spaces
-- -> apostrophes/hyphens kept only inside words -> leetspeak -> number words -> 3+ repeated letters collapse to 2.
-- The Speller additionally tries collapseRepeats(s, 1) and the variants() list when the primary form misses.

local Normalizer = {}

local MAX_INPUT = 200 -- bytes processed; anything longer is truncated (player words are <= 40 chars)

-- Latin-1 Supplement + Latin Extended-A folds (lowercase result). Codepoint -> ASCII.
local FOLD: { [number]: string } = {}
do
	local function map(chars: string, to: string)
		for _, cp in utf8.codes(chars) do
			FOLD[cp] = to
		end
	end
	map("ÀÁÂÃÄÅàáâãäåĀāĂăĄą", "a")
	map("ÇçĆćĈĉĊċČč", "c")
	map("ÐðĎďĐđ", "d")
	map("ÈÉÊËèéêëĒēĔĕĖėĘęĚě", "e")
	map("ĜĝĞğĠġĢģ", "g")
	map("ĤĥĦħ", "h")
	map("ÌÍÎÏìíîïĨĩĪīĬĭĮįİı", "i")
	map("Ĵĵ", "j")
	map("Ķķ", "k")
	map("ĹĺĻļĽľĿŀŁł", "l")
	map("ÑñŃńŅņŇň", "n")
	map("ÒÓÔÕÖØòóôõöøŌōŎŏŐő", "o")
	map("ŔŕŖŗŘř", "r")
	map("ŚśŜŝŞşŠš", "s")
	map("ŢţŤťŦŧ", "t")
	map("ÙÚÛÜùúûüŨũŪūŬŭŮůŰűŲų", "u")
	map("Ŵŵ", "w")
	map("ÝýÿŶŷŸ", "y")
	map("ŹźŻżŽž", "z")
	map("ß", "ss")
	map("Ææ", "ae")
	map("Œœ", "oe")
	map("Þþ", "th")
	-- apostrophe-likes and hyphen-likes
	map("‘’‛′`´", "'")
	map("‐‑", "-")
end

local NUMBER_WORDS = {
	"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
	"eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
}
Normalizer.NumberWords = NUMBER_WORDS

local WORD_NUMBERS: { [string]: number } = {}
for i, w in NUMBER_WORDS do
	WORD_NUMBERS[w] = i
end
WORD_NUMBERS["a"] = 1
WORD_NUMBERS["an"] = 1
Normalizer.WordNumbers = WORD_NUMBERS

-- Leetspeak digits/symbols -> letters. Primary mapping; LEET_ALT holds the second reading.
local LEET: { [string]: string } = { ["0"] = "o", ["1"] = "i", ["3"] = "e", ["4"] = "a", ["5"] = "s", ["7"] = "t", ["@"] = "a", ["$"] = "s" }
local LEET_ALT: { [string]: string } = { ["1"] = "l", ["0"] = "o", ["3"] = "e", ["4"] = "a", ["5"] = "s", ["7"] = "t", ["@"] = "a", ["$"] = "s" }

local ORDINAL_SUFFIX = { st = true, nd = true, rd = true, th = true, s = true, x = true, d = true, k = true, m = true }

Normalizer.Stopwords = { a = true, an = true, the = true, of = true, ["and"] = true, with = true, some = true, my = true }

-- Map one codepoint to its ASCII contribution (may be "" or " ").
local function foldCodepoint(cp: number): string
	if cp < 128 then
		local ch = string.char(cp)
		if cp >= 65 and cp <= 90 then
			return string.lower(ch)
		elseif (cp >= 97 and cp <= 122) or (cp >= 48 and cp <= 57) then
			return ch
		elseif ch == "'" or ch == "-" or ch == "@" or ch == "$" then
			return ch
		elseif ch == "&" then
			return " and "
		end
		return " "
	end
	if cp >= 0xFF01 and cp <= 0xFF5E then -- full-width ASCII
		return foldCodepoint(cp - 0xFEE0)
	end
	return FOLD[cp] or " "
end

local function foldUnicode(text: string): string
	local out = table.create(#text)
	local ok = pcall(function()
		for _, cp in utf8.codes(text) do
			table.insert(out, foldCodepoint(cp))
		end
	end)
	if not ok then
		-- invalid UTF-8: keep ASCII bytes only
		table.clear(out)
		for i = 1, #text do
			local b = string.byte(text, i)
			table.insert(out, if b < 128 then foldCodepoint(b) else " ")
		end
	end
	return table.concat(out)
end

-- Collapse runs of the same letter longer than maxRun (digits are left alone: "1000" stays).
function Normalizer.collapseRepeats(s: string, maxRun: number): string
	local out = table.create(#s)
	local prev, run = "", 0
	for i = 1, #s do
		local ch = string.sub(s, i, i)
		if ch == prev then
			run += 1
		else
			prev, run = ch, 1
		end
		local isLetter = ch >= "a" and ch <= "z"
		if not isLetter or run <= maxRun then
			table.insert(out, ch)
		end
	end
	return table.concat(out)
end

local function countLetters(tok: string): (number, number)
	local letters, digits = 0, 0
	for i = 1, #tok do
		local ch = string.sub(tok, i, i)
		if ch >= "a" and ch <= "z" then
			letters += 1
		elseif ch >= "0" and ch <= "9" then
			digits += 1
		end
	end
	return letters, digits
end

-- Leetspeak for a token that mixes letters with digits/symbols. Returns nil when it shouldn't be touched.
local function deleet(tok: string, map: { [string]: string }): string?
	local letters, digits = countLetters(tok)
	local symbols = select(2, string.gsub(tok, "[@%$]", ""))
	if digits + symbols == 0 or letters < 2 then
		return nil
	end
	local out = table.create(#tok)
	for i = 1, #tok do
		local ch = string.sub(tok, i, i)
		if (ch >= "0" and ch <= "9") or ch == "@" or ch == "$" then
			local m = map[ch]
			if m == nil then
				return nil -- an unmapped digit (2, 6, 8, 9) means it's a model number like "r2d2"
			end
			table.insert(out, m)
		else
			table.insert(out, ch)
		end
	end
	return table.concat(out)
end

local function numberWord(digits: string): string?
	local n = tonumber(digits)
	if n and n >= 1 and n <= 20 and string.sub(digits, 1, 1) ~= "0" then
		return NUMBER_WORDS[n]
	end
	return nil
end

-- Normalize a single whitespace-free token. Returns one or more space-separated words.
local function normalizeToken(tok: string, leet: { [string]: string }): string
	-- keep apostrophes/hyphens only between word characters
	tok = string.gsub(tok, "^[%-']+", "")
	tok = string.gsub(tok, "[%-']+$", "")
	tok = string.gsub(tok, "%-%-+", "-")
	tok = string.gsub(tok, "''+", "'")
	if tok == "" then
		return ""
	end
	-- plain number
	if string.match(tok, "^%d+$") then
		return numberWord(tok) or tok
	end
	-- "2-headed" / "2headed" -> "two-headed" / "two headed"
	local num, sep, rest = string.match(tok, "^(%d+)(%-?)(%a[%a%-']*)$")
	if num and rest and not ORDINAL_SUFFIX[rest] then
		local w = numberWord(num)
		if w and (sep == "-" or (#rest >= 4 and string.sub(rest, -2) == "ed")) then
			return w .. (if sep == "-" then "-" else " ") .. rest
		end
	end
	-- leetspeak per hyphen-part so "f1re-dr4gon" works
	if string.find(tok, "[%d@%$]") then
		local parts = string.split(tok, "-")
		for i, part in parts do
			parts[i] = deleet(part, leet) or part
		end
		tok = table.concat(parts, "-")
	end
	tok = string.gsub(tok, "[@%$]", "")
	tok = string.gsub(tok, "^[%-']+", "")
	tok = string.gsub(tok, "[%-']+$", "")
	return tok
end

local function normalizeWith(text: any, leet: { [string]: string }, maxRun: number): string
	if type(text) ~= "string" then
		return ""
	end
	local s = text
	if #s > MAX_INPUT then
		s = string.sub(s, 1, MAX_INPUT)
	end
	s = foldUnicode(s)
	local out = {}
	for tok in string.gmatch(s, "%S+") do
		local n = normalizeToken(tok, leet)
		if n ~= "" then
			table.insert(out, n)
		end
	end
	local joined = table.concat(out, " ")
	joined = string.gsub(joined, "%s+", " ")
	return Normalizer.collapseRepeats(joined, maxRun)
end

-- Canonical normalized form used for every lookup.
function Normalizer.normalize(text: string): string
	return normalizeWith(text, LEET, 2)
end

function Normalizer.tokenize(text: string): { string }
	local s = Normalizer.normalize(text)
	if s == "" then
		return {}
	end
	return string.split(s, " ")
end

-- Light form: unicode fold + lowercase + punctuation strip + whitespace collapse, no leet/number/repeat rewriting.
-- Used to tell an exact hit ("Dragon!") from one that needed real normalization ("dr4gon").
function Normalizer.light(text: string): string
	if type(text) ~= "string" then
		return ""
	end
	local s = foldUnicode(if #text > MAX_INPUT then string.sub(text, 1, MAX_INPUT) else text)
	s = string.gsub(s, "[@%$]", " ")
	local out = {}
	for tok in string.gmatch(s, "%S+") do
		tok = string.gsub(tok, "^[%-']+", "")
		tok = string.gsub(tok, "[%-']+$", "")
		if tok ~= "" then
			table.insert(out, tok)
		end
	end
	return table.concat(out, " ")
end

-- Ordered, de-duplicated candidate forms for lookup: primary normalize, repeats collapsed to 1,
-- alternative leet reading (1 -> l), and the light form (keeps real digits such as "mp3").
function Normalizer.variants(text: string): { string }
	local out, seen = {}, {}
	local function push(s: string)
		if s ~= "" and not seen[s] then
			seen[s] = true
			table.insert(out, s)
		end
	end
	local primary = Normalizer.normalize(text)
	push(primary)
	push(Normalizer.collapseRepeats(primary, 1))
	local alt = normalizeWith(text, LEET_ALT, 2)
	push(alt)
	push(Normalizer.collapseRepeats(alt, 1))
	local light = Normalizer.light(text)
	push(Normalizer.collapseRepeats(light, 2))
	return out
end

-- Spacing variants of a key: "t-rex" -> "t rex", "trex"; "fire dragon" -> "firedragon", "fire-dragon".
function Normalizer.spacingVariants(key: string): { string }
	local out = {}
	local function push(v: string)
		v = string.gsub(v, "%s+", " ")
		if v ~= key and v ~= "" and not table.find(out, v) then
			table.insert(out, v)
		end
	end
	if string.find(key, "-", 1, true) then
		push((string.gsub(key, "%-", " ")))
		push((string.gsub(key, "%-", "")))
	end
	if string.find(key, " ", 1, true) then
		push((string.gsub(key, " ", "")))
		push((string.gsub(key, " ", "-")))
	end
	if string.find(key, "'", 1, true) then
		push((string.gsub(key, "'", "")))
	end
	return out
end

-- Parse a count token: "7" -> 7, "seven" -> 7, "100" -> 100. nil if not a number.
function Normalizer.toNumber(tok: string): number?
	local n = tonumber(tok)
	if n and string.match(tok, "^%d+$") then
		return n
	end
	local w = WORD_NUMBERS[tok]
	if w and tok ~= "a" and tok ~= "an" then
		return w
	end
	return nil
end

return Normalizer
