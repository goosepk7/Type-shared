local fs = require("@lune/fs")
local load = require("../../tests/loader")
local S = load("src/Shared/Speller")
local buckets = {}
local wrongHigh, n = 0, 0
for line in string.gmatch(fs.readFile("tests/data/typos.tsv"), "[^\n]+") do
	local typo, want = string.match(line, "^([^\t]+)\t([^\t]+)")
	if typo and string.sub(typo, 1, 1) ~= "#" then
		local r = S.correct(typo)
		local b = math.floor(r.confidence * 10) / 10
		buckets[b] = buckets[b] or { ok = 0, bad = 0 }
		local good = r.canonical == want
		if good then buckets[b].ok += 1 else buckets[b].bad += 1 end
		n += 1
	end
end
for b = 0, 1, 0.1 do
	local k = math.floor(b * 10 + 0.5) / 10
	local v = buckets[k]
	if v then print(k, "ok", v.ok, "bad", v.bad) end
end
print("n", n)
