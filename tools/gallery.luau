-- Visual QA gallery (DESIGN §8): renders random "base x material x modifier" phrases in both styles to contact
-- sheets and flags builds that look broken, unreadable or generic.
--
--   lune run tools/gallery [n=320] [seed=11] [outdir=docs/img]
--
-- Writes <outdir>/gallery_<style>_<k>.png (100 tiles each), <outdir>/gallery_flagged.png (worst builds) and prints
-- a flag report. Heuristics (any one flags a tile):
--   few-parts   fewer than 5 parts, or fewer than 4 distinct shape/size groups (reads as a lump)
--   boxy        living thing whose visible volume is >80% plain Blocks
--   low-contrast luminance spread across the biggest parts < 0.07 (colours melt together)
--   no-face     the build should have a face (alive, mood, silly/cute) but has no eye parts
--   zfight      any coplanar/coincident violation left after the fix pass
--   over-budget part count above the budget
--   invisible   most visible volume nearly transparent in Solid style
local fs = require("@lune/fs")
local serde = require("@lune/serde")
local process = require("@lune/process")
local load = require("../tests/loader")
local F = require("../tests/specs/summon_fixtures")

local Schema = load("src/Shared/Schema")
local Summon = load("src/Shared/Summon")
local Palette = load("src/Shared/Summon/Palette")
local Traits = load("src/Shared/Summon/Traits")

local args = process.args
local N = tonumber(args[1]) or 320
local SEED = tonumber(args[2]) or 11
local OUT = args[3] or "docs/img"
local PER_SHEET = 100

local function flagsFor(r: any, bp: any): { string }
	local flags = {}
	local parts = bp.parts
	local groups = {}
	local nGroups = 0
	local vol, blockVol, clearVol = 0, 0, 0
	for _, p in parts do
		local v = p.size[1] * p.size[2] * p.size[3]
		vol += v
		if p.shape == "Block" then
			blockVol += v
		end
		if (p.transparency or 0) > 0.6 then
			clearVol += v
		end
		local key = p.shape .. ":" .. math.floor(math.log(math.max(v, 1e-6)) * 2)
		if not groups[key] then
			groups[key] = true
			nGroups += 1
		end
	end
	if #parts < 5 or nGroups < 4 then
		table.insert(flags, "few-parts")
	end
	local t = Traits.read(r)
	local alive = t.alive or (r.mood and r.mood ~= "Neutral")
	-- boxy only matters for living things (walls, thrones and toasters are allowed to be boxes)
	if (r.category == "Creature" or r.category == "Person") and vol > 0 and blockVol / vol > 0.8 then
		table.insert(flags, "boxy")
	end
	-- contrast across the 6 biggest parts
	local sorted = table.clone(parts)
	table.sort(sorted, function(a, b)
		return a.size[1] * a.size[2] * a.size[3] > b.size[1] * b.size[2] * b.size[3]
	end)
	local lo, hi = 1, 0
	for i = 1, math.min(6, #sorted) do
		local l = Palette.luma(sorted[i].colour)
		lo, hi = math.min(lo, l), math.max(hi, l)
	end
	-- the face counts toward contrast (eyes are what make a creature read)
	for _, p in parts do
		if p.role == "eye" or p.role == "pupil" then
			local l = Palette.luma(p.colour)
			lo, hi = math.min(lo, l), math.max(hi, l)
		end
	end
	if hi - lo < 0.07 then
		table.insert(flags, "low-contrast")
	end
	local wantsFace = alive or (r.tags and (table.find(r.tags, "silly") or table.find(r.tags, "cute")))
	-- swarm units are too small to carry faces (by design)
	if wantsFace and r.visual.bodyPlan ~= "Swarm" then
		local eyes = false
		for _, p in parts do
			if p.role == "eye" then
				eyes = true
			end
		end
		if not eyes then
			table.insert(flags, "no-face")
		end
	end
	if #Summon.check(bp) > 0 then
		table.insert(flags, "zfight")
	end
	if bp.stats.parts > bp.stats.budget then
		table.insert(flags, "over-budget")
	end
	if bp.style == "Solid" and vol > 0 and clearVol / vol > 0.6 then
		table.insert(flags, "invisible")
	end
	return flags
end

local function clean(bp: any, label: string, flags: { string }): any
	local parts = {}
	for _, p in bp.parts do
		table.insert(parts, { shape = p.shape, size = p.size, cf = p.cf, colour = p.colour, material = p.material, transparency = p.transparency, name = p.name })
	end
	return { id = bp.id, label = label, flags = flags, style = bp.style, size = bp.size, builder = bp.builder, stats = bp.stats, parts = parts }
end

local function render(list: { any }, out: string, cols: number, tile: number)
	local tmp = out .. ".json"
	fs.writeFile(tmp, serde.encode("json", list))
	local res = process.exec("python3", { "tools/render_blueprint.py", tmp, out, "--cols", tostring(cols), "--tile", tostring(tile), "--views", "iso" })
	print(res.stdout, res.stderr)
	fs.removeFile(tmp)
end

local phrases = F.phrases(Schema, N, SEED, load)
local byStyle = { Solid = {}, Spectral = {} }
local flagged = {}
local counts: { [string]: number } = {}
local total = 0
for i, r in phrases do
	for _, style in { "Solid", "Spectral" } do
		local bp = Summon.blueprint(r, { style = style, seed = i })
		local flags = flagsFor(r, bp)
		local label = string.sub(r.phrase or r.id, 1, 34)
		local c = clean(bp, label, flags)
		table.insert(byStyle[style], c)
		total += 1
		if #flags > 0 then
			table.insert(flagged, c)
			for _, f in flags do
				counts[f] = (counts[f] or 0) + 1
			end
			print(string.format("FLAG %-40s %-8s %s  (%s, %s)", r.phrase or r.id, style, table.concat(flags, ","), bp.builder, tostring(r.material)))
		end
	end
end

if not fs.isDir(OUT) then
	fs.writeDir(OUT)
end
for style, list in byStyle do
	local k = 0
	for s = 1, #list, PER_SHEET do
		k += 1
		local page = {}
		for j = s, math.min(#list, s + PER_SHEET - 1) do
			table.insert(page, list[j])
		end
		render(page, string.format("%s/gallery_%s_%d.png", OUT, string.lower(style), k), 10, 150)
	end
end
if #flagged > 0 then
	local worst = {}
	for j = 1, math.min(#flagged, 60) do
		table.insert(worst, flagged[j])
	end
	render(worst, OUT .. "/gallery_flagged.png", 10, 150)
end
local parts = {}
for f, n in counts do
	table.insert(parts, f .. "=" .. n)
end
table.sort(parts)
print(string.format("gallery: %d builds, %d flagged (%.1f%%) %s", total, #flagged, #flagged / math.max(total, 1) * 100, table.concat(parts, " ")))
