-- Visual check for Summon blueprints. Builds blueprints under Lune, dumps JSON, renders PNG via
-- tools/render_blueprint.py (flat-shaded orthographic front/side/top + 3/4 views).
--
--   lune run tools/render_blueprint plans [Solid|Spectral] [Size] out.png   -- every plan x its variants
--   lune run tools/render_blueprint sigs [Solid|Spectral] out.png           -- every signature
--   lune run tools/render_blueprint plan <Plan> [Solid|Spectral] out.png    -- one plan, all variants x sizes
--   lune run tools/render_blueprint lib <n> [Solid|Spectral] out.png        -- n library entries (seeded pick)
--   lune run tools/render_blueprint sheet out.png                           -- docs contact sheet
local fs = require("@lune/fs")
local serde = require("@lune/serde")
local process = require("@lune/process")
local load = require("../tests/loader")
local F = require("../tests/specs/summon_fixtures")

local Schema = load("src/Shared/Schema")
local Summon = load("src/Shared/Summon")

local args = process.args
local mode = args[1] or "plans"
local bps = {}
local out = args[#args]
local cols, tilePx, views = "2", "200", "front,side,top,iso"

local function add(r, style, seed)
	local bp = Summon.blueprint(r, { style = style, seed = seed })
	if r.phrase then
		bp.id = r.phrase
	elseif r.material then
		bp.id = r.material .. " " .. bp.id
	end
	table.insert(bps, bp)
end

if mode == "plans" then
	local style = args[2] or "Solid"
	local size = args[3] or "Medium"
	for _, plan in Schema.Enums.BodyPlan do
		if F.Variants[plan] then
			for v = 1, #F.Variants[plan] do
				add(F.synthetic(Schema, plan, size, v), style, 1)
			end
		end
	end
	cols = "3"
elseif mode == "special" then
	local style = args[2] or "Solid"
	local size = args[3] or "Medium"
	local mood = args[4]
	for _, plan in Schema.Enums.BodyPlan do
		if F.Special[plan] then
			add(F.special(Schema, plan, size, if mood ~= out then mood else nil), style, 1)
		end
	end
	cols = "4"
	views = "front,side,iso"
elseif mode == "plan" then
	local plan = args[2]
	local style = args[3] or "Solid"
	for v = 1, #(F.Variants[plan] or {}) do
		for _, size in { "Small", "Medium", "Huge" } do
			add(F.synthetic(Schema, plan, size, v), style, v)
		end
	end
	cols = "3"
elseif mode == "sigs" then
	local style = args[2] or "Solid"
	for _, s in F.SignatureWords do
		add(F.signatureResult(Schema, s), style, 1)
	end
	cols = "3"
elseif mode == "sig" then
	local style = args[3] or "Solid"
	for _, s in F.SignatureWords do
		if s[1] == args[2] then
			for _, size in { "Small", "Medium", "Huge" } do
				add(F.signatureResult(Schema, s, size), style, 1)
			end
			add(F.signatureResult(Schema, s), if style == "Solid" then "Spectral" else "Solid", 1)
		end
	end
	cols = "2"
	tilePx = "260"
elseif mode == "lib" then
	local n = tonumber(args[2]) or 12
	local style = args[3] or "Solid"
	local lib = F.library(Schema)
	local Rng = load("src/Shared/Summon/Rng")
	local rng = Rng.new(tonumber(args[4]) or 7)
	for _ = 1, math.min(n, #lib) do
		add(lib[rng:int(1, #lib)], style, 1)
	end
	cols = "3"
elseif mode == "word" then
	local style = args[3] or "Solid"
	for _, r in F.library(Schema) do
		if r.id == args[2] then
			add(r, style, 1)
			add(r, if style == "Solid" then "Spectral" else "Solid", 1)
		end
	end
elseif mode == "phrases" then
	-- random base x material x modifier phrases: phrases <n> [Solid|Spectral] [seed] out.png
	local n = tonumber(args[2]) or 12
	local style = args[3] or "Solid"
	for _, r in F.phrases(Schema, n, tonumber(args[4]) or 3, load) do
		add(r, style, 1)
	end
	cols = "4"
	views = "front,iso"
elseif mode == "mat" then
	-- one material over a spread of plans: mat <material> [Solid|Spectral] out.png
	local style = args[3] or "Solid"
	for _, plan in { "Quadruped", "Humanoid", "Fish", "Vehicle", "Structure", "Weapon", "Bird", "Blob" } do
		local r = F.synthetic(Schema, plan, "Medium", 1)
		r.material = args[2]
		add(r, style, 1)
	end
	cols = "4"
	views = "front,iso"
elseif mode == "sheet" then
	for _, s in F.SignatureWords do
		add(F.signatureResult(Schema, s), "Solid", 1)
	end
	for _, s in { "dragon", "phoenix", "wizard", "golem", "unicorn", "kraken" } do
		for _, sw in F.SignatureWords do
			if sw[1] == s then
				add(F.signatureResult(Schema, sw), "Spectral", 1)
			end
		end
	end
	for _, plan in Schema.Enums.BodyPlan do
		if F.Variants[plan] then
			add(F.synthetic(Schema, plan, "Medium", 1), "Solid", 1)
			add(F.synthetic(Schema, plan, "Medium", 2), "Spectral", 2)
		end
	end
	cols = "4"
	views = "front,iso"
	tilePx = "230"
end

-- strip non-serialisable fields
local clean = {}
for _, bp in bps do
	local parts = {}
	for _, p in bp.parts do
		table.insert(parts, { shape = p.shape, size = p.size, cf = p.cf, colour = p.colour, material = p.material, transparency = p.transparency, name = p.name })
	end
	table.insert(clean, { id = bp.id, style = bp.style, size = bp.size, builder = bp.builder, stats = bp.stats, parts = parts, members = bp.members })
end
local tmp = out .. ".json"
fs.writeFile(tmp, serde.encode("json", clean))
local res = process.exec("python3", { "tools/render_blueprint.py", tmp, out, "--cols", cols, "--tile", tilePx, "--views", views })
print(res.stdout, res.stderr)
fs.removeFile(tmp)
