-- Reference blueprints for the sculptors: tools/meshgen/refs.json.
--   lune run tools/meshgen/export_refs
-- Hero and head sculpts ("unit" pieces) are modelled on top of the exact primitives a generator emits, in the unit
-- frame of their lead part, so eyes, mouths and accents that the builder places on the primitive surfaces sit
-- right on the sculpt. This script dumps those primitives (no material, no accents, Solid, seed 1, no part budget)
-- for every fixture word; catalogue/refs.py reads the file. The JSON is committed: a sculpt only changes when it is
-- re-exported on purpose.
local fs = require("@lune/fs")
local serde = require("@lune/serde")
local load = require("../../tests/loader")
local F = require("../../tests/specs/summon_fixtures")
local Schema = load("src/Shared/Schema")
local Summon = load("src/Shared/Summon")

local out = {}
local function add(key: string, r: any)
	local bp = Summon.blueprint(r, { style = "Solid", seed = 1, budget = { maxParts = 400 } })
	local parts = {}
	for _, p in bp.parts do
		local cf = {}
		for i = 1, 12 do
			cf[i] = math.floor(p.cf[i] * 1e5 + 0.5) / 1e5
		end
		table.insert(parts, {
			name = p.name, role = p.role, shape = p.shape, bone = p.bone, col = if type(p.col) == "string" then p.col else "rgb",
			size = { p.size[1], p.size[2], p.size[3] }, cf = cf, mesh = p.mesh, meshOf = p.meshOf, mirrored = p.mirrored, tr = p.tr,
		})
	end
	out[key] = { builder = bp.builder, scale = bp.scale, parts = parts }
end

for _, plan in Schema.Enums.BodyPlan do
	for v, var in F.Variants[plan] or {} do
		add(var[1], F.synthetic(Schema, plan, "Large", v))
	end
	if F.Special and F.Special[plan] then
		add("special:" .. plan, F.special(Schema, plan, "Large"))
	end
end
for _, s in F.SignatureWords do
	add("sig:" .. s[1], F.signatureResult(Schema, s, "Huge"))
end
-- extra exemplars (quadruped archetypes, orbs, structures) that the fixtures only reach through the renderer
local EX = {
	{ "fox", "Quadruped", "Creature", "None", { "mammal" } }, { "cat*", "Quadruped", "Creature", "None", { "mammal" } },
	{ "bear", "Quadruped", "Creature", "None", { "mammal" } }, { "horse", "Quadruped", "Creature", "None", { "mammal" } },
	{ "cow", "Quadruped", "Creature", "None", { "mammal" } }, { "pig", "Quadruped", "Creature", "None", { "mammal" } },
	{ "mouse", "Quadruped", "Creature", "None", { "mammal", "cute" } }, { "lizard", "Quadruped", "Creature", "None", { "reptile" } },
	{ "fireball", "Orb", "Element", "Fire", {} }, { "meteor", "Orb", "Disaster", "Fire", {} }, { "asteroid", "Orb", "Disaster", "Earth", {} },
	{ "black hole", "Orb", "Disaster", "Shadow", {} }, { "boulder", "Orb", "Element", "Earth", {} }, { "planet", "Orb", "Place", "Arcane", { "space" } },
	{ "tornado", "Cloud", "Disaster", "Wind", {} }, { "castle*", "Castle", "Structure", "Earth", {} }, { "tower*", "Tower", "Structure", "Earth", {} },
	{ "crystal", "Orb", "Element", "Ice", {} },
}
for _, q in EX do
	local id = (string.gsub(q[1], "%*", ""))
	add(q[1], Schema.repair({
		id = id, canonical = id, category = q[3], element = q[4], size = "Large", shape = "Summon", behaviours = {}, power = 5, speed = 5,
		durability = 5, count = 1, source = "Library", confidence = 1,
		visual = { primaryColour = "#8E8A86", secondaryColour = "#C9C2BA", bodyPlan = q[2], silhouetteHint = "", motionHint = "Walk", soundHint = "roar" },
		flavourText = "", tags = q[5],
	}))
end
fs.writeFile("tools/meshgen/refs.json", serde.encode("json", out))
local n = 0
for _ in out do
	n += 1
end
print("wrote tools/meshgen/refs.json", n, "blueprints")
