--!strict
-- Stemmer: candidate base forms for an inflected word, most likely first, each with a confidence.
-- Covers plurals (-s/-es/-ies/-ves/-i/-ae/-men), -ing, -ed, -er/-ers, -est, -ly, -y and an irregular table.
-- For multi-word input only the LAST token is stemmed ("fire dragons" -> "fire dragon"). Pure; no library access.

local Stemmer = {}

export type Candidate = { word: string, confidence: number, plural: boolean }

-- Irregular forms -> base. Plurals first, then verb forms players type as spells ("froze", "flew").
local IRREGULAR: { [string]: string } = {
	mice = "mouse", lice = "louse", geese = "goose", teeth = "tooth", feet = "foot", men = "man", women = "woman",
	children = "child", oxen = "ox", people = "person", dice = "die", sheep = "sheep", deer = "deer", moose = "moose",
	fish = "fish", fishes = "fish", octopi = "octopus", cacti = "cactus", fungi = "fungus", larvae = "larva",
	antennae = "antenna", criteria = "criterion", phenomena = "phenomenon", indices = "index", matrices = "matrix",
	vertices = "vertex", vortices = "vortex", alumni = "alumnus", radii = "radius", nuclei = "nucleus",
	stimuli = "stimulus", cherubim = "cherub", seraphim = "seraph", data = "datum", leaves = "leaf",
	knives = "knife", lives = "life", wives = "wife", thieves = "thief", elves = "elf", dwarves = "dwarf",
	halves = "half", wolves = "wolf", loaves = "loaf", calves = "calf", shelves = "shelf", scarves = "scarf",
	hooves = "hoof", selves = "self", sheaves = "sheaf", staves = "staff", wharves = "wharf", quizzes = "quiz",
	buses = "bus", gasses = "gas", heroes = "hero", potatoes = "potato", tomatoes = "tomato", volcanoes = "volcano",
	tornadoes = "tornado", torpedoes = "torpedo", mosquitoes = "mosquito", buffaloes = "buffalo", echoes = "echo",
	dominoes = "domino", mangoes = "mango", flamingoes = "flamingo", tacos = "taco", ninjas = "ninja",
	-- verbs
	ran = "run", flew = "fly", flown = "fly", froze = "freeze", frozen = "freeze", swam = "swim", swum = "swim",
	bit = "bite", bitten = "bite", ate = "eat", eaten = "eat", threw = "throw", thrown = "throw", fell = "fall",
	fallen = "fall", broke = "break", broken = "break", drew = "draw", drawn = "draw", rode = "ride",
	ridden = "ride", struck = "strike", sang = "sing", sung = "sing", dug = "dig", spun = "spin", stung = "sting",
	bled = "bleed", blew = "blow", blown = "blow", grew = "grow", grown = "grow", shot = "shoot", built = "build",
	caught = "catch", fought = "fight", flung = "fling", burnt = "burn", lit = "light", slept = "sleep",
	swept = "sweep", wept = "weep", shook = "shake", shaken = "shake", woke = "wake", woken = "wake",
	hid = "hide", hidden = "hide", stole = "steal", stolen = "steal", sank = "sink", sunk = "sink", rose = "rise",
	risen = "rise", drove = "drive", driven = "drive", wrote = "write", written = "write", smote = "smite",
	slain = "slay", slew = "slay", fled = "flee", fed = "feed", led = "lead", held = "hold", sold = "sell",
	told = "tell", casts = "cast", summoned = "summon", exploded = "explode",
}

local VOWELS = { a = true, e = true, i = true, o = true, u = true }
local function isVowel(ch: string): boolean
	return VOWELS[ch] == true
end

local function push(out: { Candidate }, seen: { [string]: boolean }, word: string, confidence: number, plural: boolean)
	if #word >= 2 and not seen[word] then
		seen[word] = true
		table.insert(out, { word = word, confidence = confidence, plural = plural })
	end
end

-- Candidates for one token (no spaces).
local function stemToken(w: string): { Candidate }
	local out: { Candidate } = {}
	local seen: { [string]: boolean } = { [w] = true }
	local n = #w
	if n < 3 then
		return out
	end
	local irr = IRREGULAR[w]
	if irr and irr ~= w then
		push(out, seen, irr, 0.96, true)
	end
	local function ends(suffix: string): boolean
		return #w > #suffix and string.sub(w, -#suffix) == suffix
	end
	local function cut(k: number): string
		return string.sub(w, 1, n - k)
	end

	-- plurals
	if ends("ies") and n > 4 then
		push(out, seen, cut(3) .. "y", 0.96, true) -- puppies -> puppy
		push(out, seen, cut(1), 0.9, true) -- pies -> pie, zombies -> zombie
	end
	if ends("ves") then
		push(out, seen, cut(3) .. "f", 0.94, true)
		push(out, seen, cut(3) .. "fe", 0.93, true)
		push(out, seen, cut(1), 0.92, true) -- caves -> cave
	end
	if ends("men") and n > 4 then
		push(out, seen, cut(3) .. "man", 0.95, true)
	end
	if ends("es") then
		local stem = cut(2)
		local last = string.sub(stem, -1)
		local last2 = string.sub(stem, -2)
		if last == "s" or last == "x" or last == "z" or last2 == "ch" or last2 == "sh" or last == "o" then
			push(out, seen, stem, 0.96, true) -- foxes -> fox, tornadoes -> tornado
		end
	end
	if ends("s") and not ends("ss") and not ends("us") and not ends("is") then
		push(out, seen, cut(1), 0.96, true) -- dragons -> dragon, tes -> te handled by lookups failing
	end
	if ends("es") then
		push(out, seen, cut(2), 0.88, true)
	end
	if ends("i") and n > 4 then
		push(out, seen, cut(1) .. "us", 0.86, true) -- octopi -> octopus
	end
	if ends("ae") and n > 4 then
		push(out, seen, cut(1), 0.86, true) -- larvae -> larva
	end
	if ends("'s") then
		push(out, seen, cut(2), 0.95, true) -- dragon's -> dragon
	end
	if ends("s'") then
		push(out, seen, cut(2), 0.95, true)
	end

	-- -ing / -ed
	local function verb(suffix: string, conf: number)
		if not ends(suffix) or n - #suffix < 3 then
			return
		end
		local stem = cut(#suffix)
		local m = #stem
		local a, b = string.sub(stem, m, m), string.sub(stem, m - 1, m - 1)
		if a == b and not isVowel(a) and a ~= "l" and a ~= "s" and a ~= "z" then
			push(out, seen, string.sub(stem, 1, m - 1), conf, false) -- running -> run
		end
		push(out, seen, stem, conf - 0.01, false) -- burning -> burn
		push(out, seen, stem .. "e", conf - 0.02, false) -- freezing -> freeze
		if a == "i" and suffix == "ed" then
			push(out, seen, string.sub(stem, 1, m - 1) .. "y", conf, false) -- fried -> fry
		end
		if a == "y" and suffix == "ing" then
			push(out, seen, stem, conf, false) -- flying -> fly
		end
		if a == b and (a == "l" or a == "s" or a == "z") then
			push(out, seen, string.sub(stem, 1, m - 1), conf - 0.03, false)
		end
	end
	verb("ing", 0.9)
	if n >= 6 then
		verb("in", 0.84) -- "burnin"
	end
	verb("ed", 0.9)
	-- -er / -ers / -est / -ly / -y : meaning drifts, keep confidence lower
	if ends("ers") then
		verb("ers", 0.8)
	end
	verb("er", 0.8)
	verb("est", 0.8)
	if ends("ly") and n > 4 then
		push(out, seen, cut(2), 0.8, false)
		if string.sub(w, -3, -3) == "i" then
			push(out, seen, cut(3) .. "y", 0.8, false)
		end
	end
	if ends("y") and n > 4 and not ends("ey") then
		push(out, seen, cut(1), 0.78, false) -- rocky -> rock
		push(out, seen, cut(1) .. "e", 0.76, false) -- slimy -> slime
		local stem = cut(1)
		local m = #stem
		if string.sub(stem, m, m) == string.sub(stem, m - 1, m - 1) then
			push(out, seen, string.sub(stem, 1, m - 1), 0.76, false) -- muddy -> mud
		end
	end
	table.sort(out, function(x, y)
		if x.confidence ~= y.confidence then
			return x.confidence > y.confidence
		end
		return x.word < y.word
	end)
	return out
end

-- Candidates for a word or phrase. Only the last token of a phrase is stemmed.
function Stemmer.candidates(text: string): { Candidate }
	local head, last = string.match(text, "^(.*) (%S+)$")
	if head and last then
		local out = stemToken(last)
		for _, c in out do
			c.word = head .. " " .. c.word
		end
		return out
	end
	return stemToken(text)
end

-- Plural-only candidates (used by Library.lookup, which must stay strict).
function Stemmer.plurals(text: string): { Candidate }
	local out = {}
	for _, c in Stemmer.candidates(text) do
		if c.plural and c.confidence >= 0.9 then
			table.insert(out, c)
		end
	end
	return out
end

return Stemmer
