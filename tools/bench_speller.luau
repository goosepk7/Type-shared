-- Speller benchmark. Run from the repo root:  lune run tools/bench_speller.luau
-- Reports cold-start costs and per-lookup latency (cache disabled per call) for exact words, single-word typos
-- (the golden set) and multi-word phrases.
local fs = require("@lune/fs")
local load = require("../tests/loader")

local function now(): number
	return os.clock()
end

local t0 = now()
local Library = load("src/Shared/Library")
local Speller = load("src/Shared/Speller")
local Fuzzy = load("src/Shared/Speller/Fuzzy")
local Suggest = load("src/Shared/Suggest")
local tRequire = now() - t0

t0 = now()
Library.count()
local tIndex = now() - t0
t0 = now()
Library.preload()
local tKeys = now() - t0
t0 = now()
Fuzzy.preload()
local tFuzzy = now() - t0
t0 = now()
Speller.correct("giant fire shark") -- loads modifiers + materials
local tMods = now() - t0

local function stats(name: string, inputs: { string }, rounds: number)
	local times = {}
	for _ = 1, rounds do
		for _, s in inputs do
			Speller.clearCache()
			local c = now()
			Speller.correct(s)
			table.insert(times, (now() - c) * 1000)
		end
	end
	table.sort(times)
	local sum = 0
	for _, v in times do
		sum += v
	end
	local function pct(p: number): number
		return times[math.clamp(math.floor(#times * p + 0.5), 1, #times)]
	end
	print(string.format("%-28s n=%-5d median %.3f ms  p90 %.3f ms  p99 %.3f ms  mean %.3f ms  max %.2f ms",
		name, #times, pct(0.5), pct(0.9), pct(0.99), sum / #times, times[#times]))
end

local typos, phrases = {}, {}
for line in string.gmatch(fs.readFile("tests/data/typos.tsv"), "[^\n]+") do
	local a = string.match(line, "^([^#][^\t]*)\t")
	if a then
		if string.find(a, " ", 1, true) then
			table.insert(phrases, a)
		else
			table.insert(typos, a)
		end
	end
end
local exact = {}
for i, id in Library.ids() do
	if i % 7 == 0 then
		table.insert(exact, id)
	end
end

print(string.format("library: %d entries, %d authored keys", Library.count(), #(select(1, Library.keyArrays()))))
print(string.format("cold: require %.1f ms, index %.1f ms, keys+variants %.1f ms, fuzzy index %.1f ms, modifiers+materials %.1f ms",
	tRequire * 1000, tIndex * 1000, tKeys * 1000, tFuzzy * 1000, tMods * 1000))
print("(cold numbers include Lune compiling the generated source; Roblox ships precompiled bytecode)")
stats("exact / alias words", exact, 1)
stats("single-word typos (golden)", typos, 3)
stats("multi-word phrases (golden)", phrases, 3)

Speller.clearCache()
local c = now()
for _ = 1, 20 do
	for _, s in typos do
		Speller.correct(s)
	end
end
print(string.format("%-28s %.4f ms per call", "cached repeat lookups", (now() - c) * 1000 / (20 * #typos)))

c = now()
local n = 0
for _, p in { "a", "dr", "fir", "sha", "tor", "giant sha", "spa", "ro", "bl", "ze" } do
	for _ = 1, 50 do
		Suggest.prefix(p, { "dragonfly", "shark", "fireball" }, 4)
		n += 1
	end
end
print(string.format("%-28s %.4f ms per call", "Suggest.prefix", (now() - c) * 1000 / n))
