-- Visual check for Summon blueprints. Builds blueprints under Lune, dumps JSON, renders PNG via
-- tools/render_blueprint.py (flat-shaded orthographic front/side/top + 3/4 views).
--
--   lune run tools/render_blueprint plans [Solid|Spectral] [Size] out.png   -- every plan x its variants
--   lune run tools/render_blueprint sigs [Solid|Spectral] out.png           -- every signature
--   lune run tools/render_blueprint plan <Plan> [Solid|Spectral] out.png    -- one plan, all variants x sizes
--   lune run tools/render_blueprint lib <n> [Solid|Spectral] out.png        -- n library entries (seeded pick)
--   lune run tools/render_blueprint sheet out.png                           -- docs contact sheet
--   lune run tools/render_blueprint beforeafter out.png                     -- primitives vs sculpted meshes
--
-- Set SUMMON_MESH=0 to draw primitives only, SUMMON_RT=0 to use the flat painter for Solid tiles too. With the
-- defaults the sheets show the sculpted pieces from tools/meshgen/out (run `python3 tools/meshgen/build.py`).
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

local useMesh = process.env.SUMMON_MESH ~= "0"
local useRt = process.env.SUMMON_RT ~= "0"

local function add(r, style, seed, primitive)
	local bp = Summon.blueprint(r, { style = style, seed = seed })
	if primitive then
		bp.meshes = false
	end
	if r.phrase then
		bp.id = r.phrase
	elseif r.material then
		bp.id = r.material .. " " .. bp.id
	end
	table.insert(bps, bp)
end

local libCache
-- 5 stud tall character-height reference figure beside a blueprint
local function addRef(bp)
	local minX, minZ = math.huge, math.huge
	for _, p in bp.parts do
		local e = math.max(p.size[1], p.size[2], p.size[3]) / 2
		minX = math.min(minX, p.cf[1] - e)
		minZ = math.min(minZ, p.cf[3] - e)
	end
	local x, z = minX - 1.5, minZ - 1.5
	local grey = { 0.62, 0.62, 0.66 }
	local function ref(name, shape, sx, sy, sz, y)
		table.insert(bp.parts, { name = name, shape = shape, size = { sx, sy, sz }, cf = { x, y, z, 1, 0, 0, 0, 1, 0, 0, 0, 1 }, colour = grey, material = "SmoothPlastic", transparency = 0 })
	end
	ref("RefLegs", "Block", 1.6, 2, 0.9, 1)
	ref("RefTorso", "Block", 2, 1.9, 1, 2.95)
	ref("RefHead", "Ball", 1.15, 1.15, 1.15, 4.42)
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
elseif mode == "quads" then
	-- one exemplar per quadruped archetype: quads [Solid|Spectral] [Size] out.png
	local style = args[2] or "Solid"
	local size = if args[3] and args[3] ~= out then args[3] else "Medium"
	local Q = {
		{ "wolf", { "mammal" }, "pointy ears, bushy tail", "#7D8590", "#D9DDE2" }, { "fox", { "mammal" }, "", "#E0782E", "#FFF3E6" },
		{ "dog", { "mammal" }, "", "#B8835A", "#F4E6D0" }, { "cat", { "mammal" }, "", "#8E8E96", "#F2F2F2" },
		{ "tiger", { "mammal" }, "", "#F08A24", "#FFF6E8" }, { "lion", { "mammal" }, "mane, tufted tail", "#C8902E", "#7A4A1E" },
		{ "bear", { "mammal" }, "", "#6B4A2E", "#C9A57A" }, { "panda", { "mammal" }, "", "#F4F4F4", "#22252B" },
		{ "horse", { "mammal" }, "", "#8A5A33", "#3A2A1E" }, { "deer", { "mammal" }, "", "#B07A45", "#F4E6D0" },
		{ "cow", { "mammal" }, "", "#F4F4F4", "#3A3A3F" }, { "goat", { "mammal" }, "", "#D9D2C2", "#8A7A62" },
		{ "pig", { "mammal" }, "", "#F2A7B5", "#E07A8E" }, { "mouse", { "mammal", "cute" }, "", "#A8A39C", "#F2C6CC" },
		{ "squirrel", { "mammal" }, "", "#B5652E", "#F4E0C2" }, { "rabbit", { "mammal", "cute" }, "long ears", "#E8DCCB", "#FFFFFF" },
		{ "elephant", { "mammal", "heavy" }, "big ears, trunk, tusks", "#8E8A86", "#C9C2BA" }, { "rhino", { "mammal", "heavy" }, "", "#8E8A86", "#B9B2AA" },
		{ "lizard", { "reptile" }, "", "#5E9A3A", "#D9E27A" }, { "unicorn", { "mythical" }, "spiral horn, flowing mane", "#F7F3FF", "#C77DFF" },
	}
	for _, q in Q do
		local r = Schema.repair({
			id = q[1], canonical = q[1], category = "Creature", element = "None", size = size, shape = "Summon", behaviours = { "Melee" },
			power = 5, speed = 5, durability = 5, count = 1, source = "Library", confidence = 1,
			visual = { primaryColour = q[4], secondaryColour = q[5], bodyPlan = "Quadruped", silhouetteHint = q[3], motionHint = "Walk", soundHint = "roar" },
			flavourText = "", tags = q[2],
		})
		add(r, style, 1)
	end
	cols = "4"
	views = "side,iso"
	tilePx = "200"
elseif mode == "orbs" or mode == "builds" or mode == "swarms" then
	-- exemplars for the Orb, Structure and Swarm plans: <mode> [Solid|Spectral] [Size] out.png
	local style = args[2] or "Solid"
	local size = if args[3] and args[3] ~= out then args[3] else "Medium"
	local EX = {
		orbs = {
			{ "fireball", "Element", "Fire", "#FF5A1F", "#FFD23A" }, { "meteor", "Disaster", "Fire", "#5A4A3E", "#FF8A2B" },
			{ "planet", "Place", "Arcane", "#D99A4A", "#F4E1B4" }, { "earth", "Place", "Nature", "#2F6FD6", "#5BA33A" },
			{ "sun", "Place", "Fire", "#FFC83A", "#FF8A1F" }, { "moon", "Place", "Light", "#C9C6BE", "#8E8A86" },
			{ "magic orb", "Object", "Arcane", "#B65CFF", "#FFE6FF" }, { "heal", "Abstract", "Light", "#FFE58A", "#FFFFFF" },
			{ "ball lightning", "Element", "Lightning", "#9FD8F2", "#FFF07A" }, { "ice orb", "Element", "Ice", "#A8E9FF", "#FFFFFF" },
			{ "boulder", "Element", "Earth", "#8E8A80", "#C9B27A" }, { "shadow orb", "Element", "Shadow", "#2A1A3A", "#A974FF" },
			{ "bomb", "Weapon", "Fire", "#22252B", "#FF8A1F" }, { "black hole", "Disaster", "Shadow", "#120A1E", "#A974FF" },
			{ "bubble", "Element", "Water", "#9FD8F2", "#FFFFFF" }, { "apple", "Food", "Nature", "#D62F2F", "#5BA33A" },
		},
		builds = {
			{ "tower", "Structure", "Earth", "#A39E93", "#5A3A6B", "Tower" }, { "house", "Structure", "None", "#E8D8B4", "#A33A2A", "Structure" },
			{ "castle", "Structure", "Earth", "#A39E93", "#2F5AA3", "Castle" }, { "wall", "Structure", "Earth", "#8E8A80", "#5E5A52", "Wall" },
			{ "lighthouse", "Structure", "Light", "#F2F2F2", "#D62F2F", "Structure" }, { "windmill", "Structure", "Wind", "#E8D8B4", "#8A5A33", "Structure" },
			{ "wizard tower", "Structure", "Arcane", "#6E6A8A", "#5A3A9B", "Tower" }, { "igloo", "Structure", "Ice", "#EEF6FA", "#BFD8E8", "Structure" },
			{ "pyramid", "Structure", "Light", "#D9B97A", "#E8B53A", "Structure" }, { "gate", "Structure", "Earth", "#8E8A80", "#6B4A2E", "Gate" },
			{ "cottage", "Structure", "None", "#E8D8B4", "#A33A2A", "Building" }, { "watchtower", "Structure", "Earth", "#A39E93", "#5A3A6B", "Tower" },
		},
		swarms = {
			{ "bees", "Creature", "Nature", "#F2C22F", "#2A2A30", "Swarm" }, { "bee", "Creature", "Nature", "#F2C22F", "#2A2A30", "Insect" },
			{ "wasps", "Creature", "Poison", "#E8B020", "#1D1D22", "Swarm" }, { "bats", "Creature", "Shadow", "#2A2230", "#7A5AA3", "Swarm" },
			{ "fireflies", "Creature", "Light", "#FFE58A", "#7ED957", "Swarm" }, { "piranhas", "Creature", "Water", "#8E8A86", "#D62F2F", "Swarm" },
			{ "locusts", "Creature", "Nature", "#7A8B3A", "#C9B27A", "Swarm" }, { "crows", "Creature", "Shadow", "#22252B", "#5A5A66", "Swarm" },
		},
	}
	local planOf = { orbs = "Orb" }
	for _, q in EX[mode] do
		local r = Schema.repair({
			id = q[1], canonical = q[1], category = q[2], element = q[3], size = size, shape = "Summon", behaviours = {},
			power = 5, speed = 5, durability = 5, count = 1, source = "Library", confidence = 1,
			visual = { primaryColour = q[4], secondaryColour = q[5], bodyPlan = q[6] or planOf[mode], silhouetteHint = "", motionHint = "Float", soundHint = "hum" },
			flavourText = "", tags = if q[2] == "Place" then { "space" } elseif q[6] == "Swarm" or q[6] == "Insect" then { "insect" } else {},
		})
		add(r, style, 1)
	end
	cols = "4"
	views = "front,iso"
	tilePx = "200"
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
elseif mode == "beforeafter" then
	-- the same blueprint twice: primitive parts, then the sculpted pieces swapped in (same builder, same budget)
	local picks = { "dragon", "t rex", "shark", "unicorn", "golem", "robot", "knight", "wizard", "tank", "pirate ship", "castle", "rocket", "ufo", "cannon", "cat", "octopus" }
	if args[2] ~= out and args[2] ~= nil then
		picks = string.split(args[2], ",")
	end
	for _, s in picks do
		local found = false
		for _, sw in F.SignatureWords do
			if sw[1] == s then
				found = true
				add(F.signatureResult(Schema, sw), "Solid", 1, true)
				add(F.signatureResult(Schema, sw), "Solid", 1)
			end
		end
		if not found then
			for _, plan in Schema.Enums.BodyPlan do
				for v, var in F.Variants[plan] or {} do
					if var[1] == s then
						add(F.synthetic(Schema, plan, "Medium", v), "Solid", 1, true)
						add(F.synthetic(Schema, plan, "Medium", v), "Solid", 1)
					end
				end
			end
		end
	end
	cols = "4"
	views = "iso"
	tilePx = "300"
elseif mode == "scale" then
	-- lune run tools/render_blueprint scale <Solid|Spectral> <comma list> out.png: each word next to a 5 stud
	-- tall character-height reference figure (grey), to judge silhouette and size
	local style = args[2] or "Spectral"
	for _, s in string.split(args[3] or "dragon", ",") do
		local r
		for _, sw in F.SignatureWords do
			if sw[1] == s then
				r = F.signatureResult(Schema, sw)
			end
		end
		for _, plan in Schema.Enums.BodyPlan do
			for v, var in F.Variants[plan] or {} do
				if r == nil and var[1] == s then
					r = F.synthetic(Schema, plan, "Medium", v)
				end
			end
		end
		if r then
			add(r, style, 1)
			addRef(bps[#bps])
		end
	end
	cols = "2"
	views = "front,iso"
	tilePx = "420"
elseif mode == "hero" then
	-- lune run tools/render_blueprint hero <comma list> out.png [size]: per word three rows with a 5 stud reference
	-- figure: Solid primitives, Solid sculpt, Spectral sculpt (side + 3/4 view)
	for _, s in string.split(args[2] or "dragon", ",") do
		local SIZES = { tiny = "Tiny", small = "Small", baby = "Small", medium = "Medium", large = "Large", big = "Large", huge = "Huge" }
		local function base(word)
			-- "<size> <word>" (small dragon, baby dragon)
			local sz, rest = string.match(word, "^(%S+)%s+(.+)$")
			local size = args[4]
			if sz and SIZES[sz] then
				word, size = rest, SIZES[sz]
			end
			for _, sw in F.SignatureWords do
				if sw[1] == word then
					return F.signatureResult(Schema, sw, size)
				end
			end
			for _, plan in Schema.Enums.BodyPlan do
				for v, var in F.Variants[plan] or {} do
					if var[1] == word then
						return F.synthetic(Schema, plan, size or "Medium", v)
					end
				end
			end
			libCache = libCache or F.library(Schema)
			for _, e in libCache do
				if e.id == word then
					local copy = table.clone(e)
					copy.visual = table.clone(e.visual)
					return copy
				end
			end
			return nil
		end
		-- "<word>@<Element>" (tiger@Ice) renders the word with that element (element dressing)
		local el
		s, el = string.match(s, "^([^@]+)@?(%a*)$")
		local function result()
			local r = base(s)
			if r and el ~= "" then
				r = table.clone(r)
				r.element = el
			end
			if r == nil then
				-- "<material> <word>" (glass shark, spaghetti dragon)
				local mat, rest = string.match(s, "^(%S+)%s+(.+)$")
				if mat then
					r = base(rest)
					if r then
						r.material = mat
						r.phrase = s
					end
				end
			end
			return r
		end
		if result() then
			add(result(), "Solid", 1, true)
			addRef(bps[#bps])
			add(result(), "Solid", 1)
			addRef(bps[#bps])
			add(result(), "Spectral", 1)
			addRef(bps[#bps])
		end
	end
	cols = "3"
	views = "side,iso"
	tilePx = "400"
end
if false then
	do
		do
			local bp = bps[#bps]
			local minX = math.huge
			for _, p in bp.parts do
				minX = math.min(minX, p.cf[1] - math.max(p.size[1], p.size[3]) / 2)
			end
			local x = minX - 2
			local grey = { 0.62, 0.62, 0.66 }
			local function ref(name, shape, sx, sy, sz, y)
				table.insert(bp.parts, { name = name, shape = shape, size = { sx, sy, sz }, cf = { x, y, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1 }, colour = grey, material = "SmoothPlastic", transparency = 0 })
			end
			ref("RefLegs", "Block", 1.6, 2, 0.9, 1)
			ref("RefTorso", "Block", 2, 1.9, 1, 2.95)
			ref("RefHead", "Ball", 1.15, 1.15, 1.15, 4.42)
		end
	end
	cols = "2"
	views = "front,iso"
	tilePx = "420"
end

-- strip non-serialisable fields
local clean = {}
for _, bp in bps do
	local parts = {}
	for _, p in bp.parts do
		table.insert(parts, { shape = p.shape, size = p.size, cf = p.cf, colour = p.colour, material = p.material, transparency = p.transparency, name = p.name,
			mesh = p.mesh, meshOf = p.meshOf })
	end
	table.insert(clean, { id = bp.id, style = bp.style, size = bp.size, builder = bp.builder, stats = bp.stats, parts = parts, members = bp.members, fx = { highlight = bp.fx and bp.fx.highlight },
		meshes = bp.meshes })
end
local tmp = out .. ".json"
fs.writeFile(tmp, serde.encode("json", clean))
tilePx = process.env.SUMMON_TILE or tilePx
views = process.env.SUMMON_VIEWS or views
local pyArgs = { "tools/render_blueprint.py", tmp, out, "--cols", cols, "--tile", tilePx, "--views", views }
if useMesh then
	table.insert(pyArgs, "--mesh")
end
if useRt then
	table.insert(pyArgs, "--rt")
end
local res = process.exec("python3", pyArgs)
print(res.stdout, res.stderr)
fs.removeFile(tmp)
