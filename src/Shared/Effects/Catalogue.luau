--!strict
-- The Effects catalogue: every effect id -> how to render it. Pure data + validation (no Roblox APIs).
--
-- An entry is { kind, variant?, element?, duration?, loop?, desc, needs?, layers?, colour?, scale? }:
--   kind      renderer module (Runtime/Kinds): Projectile, Beam, Strike, Impact, Explosion, Burst, Aura, Shield,
--             Wall, Cloud, Rain, Wave, Zone, Weather, Spawn, Status, Attached, Composite
--   variant   renderer-specific look ("bolt", "tornado", "Burn", ...)
--   element   default element when params.element is nil (impact.fire -> Fire)
--   duration  default seconds (params.duration overrides). loop = true: runs until handle:stop() unless a
--             duration is given.
--   needs     which params matter: "at" (CFrame/position), "from"+"to", "target" (Instance)
--   layers    Composite only: { {id, el?, d? (delay), s? (scale), dur?, off? {x,y,z}, colour?} }
-- Reactions get one composite each, id = Reaction.vfx ("reaction.steam"), built from RECIPES below.

local Reactions = require(script.Parent.Parent.Reactions)

local Catalogue = {}

export type Layer = { id: string, el: string?, d: number?, s: number?, dur: number?, off: { number }?, colour: string? }
export type Entry = {
	id: string,
	kind: string,
	variant: string?,
	element: string?,
	duration: number?,
	loop: boolean?,
	desc: string,
	needs: string?,
	layers: { Layer }?,
	colour: string?,
	scale: number?,
	family: string,
}

local ENTRIES: { [string]: Entry } = {}
local ORDER: { string } = {}

local function add(id: string, e: { [string]: any })
	assert(ENTRIES[id] == nil, "duplicate effect id " .. id)
	e.id = id
	e.family = e.family or string.match(id, "^([^%.]+)") or id
	ENTRIES[id] = e :: Entry
	table.insert(ORDER, id)
end

local ELEMENTS = { "Fire", "Water", "Ice", "Lightning", "Earth", "Wind", "Nature", "Light", "Shadow", "Poison", "Metal", "Arcane", "None" }

-- Projectiles -----------------------------------------------------------------------------------------------
-- All projectiles: from -> to (or target). Speed via params.speed (studs/s). On arrival they play their impact
-- (params.impact = false to skip; params.impact = "<id>" to choose). handle:setTarget() re-aims homing ones.
add("projectile.bolt", { kind = "Projectile", variant = "bolt", needs = "from,to|target", desc = "Fast elongated energy bolt with trail, sparks and light; element impact on arrival." })
add("projectile.orb", { kind = "Projectile", variant = "orb", needs = "from,to|target", desc = "Slow pulsing orb with orbiting motes; homes on target if given." })
add("projectile.arrow", { kind = "Projectile", variant = "arrow", needs = "from,to|target", desc = "Arrow/spear-like shaft on a shallow ballistic arc, oriented along its velocity." })
add("projectile.shard", { kind = "Projectile", variant = "shard", needs = "from,to|target", desc = "Spinning crystal shard (ice spike, glass, metal blade)." })
add("projectile.meteor", { kind = "Projectile", variant = "meteor", element = "Fire", needs = "to (from optional: defaults to the sky)", desc = "Asteroid/meteor falling from the sky: burning rock, smoke + fire trail, growing ground shadow and warning ring, huge explosion + crater." })
add("projectile.comet", { kind = "Projectile", variant = "comet", element = "Light", needs = "to", desc = "Small falling star (starfall), lighter explosion." })
add("projectile.boulder", { kind = "Projectile", variant = "boulder", element = "Earth", needs = "from,to", desc = "Lobbed tumbling rock on a high arc with dust trail and landing shadow." })
add("projectile.bubble", { kind = "Projectile", variant = "bubble", element = "Water", needs = "from,to|target", desc = "Wobbling water bubble that pops into a splash." })

-- Beams -----------------------------------------------------------------------------------------------------
add("beam.ray", { kind = "Beam", variant = "ray", duration = 1.2, needs = "from,to|target", desc = "Thick sustained energy beam: core + outer glow + scrolling texture, muzzle and hit glows." })
add("beam.lightning", { kind = "Beam", variant = "lightning", duration = 0.45, needs = "from,to|target", desc = "Jagged lightning bolt that re-forks every few frames, with branches and flash." })
add("beam.chain", { kind = "Beam", variant = "chain", duration = 0.6, needs = "points {Vector3} or targets {Instance} (or from,to)", desc = "Lightning arcing from point to point (chain shock)." })
add("beam.drain", { kind = "Beam", variant = "drain", duration = 2, needs = "from,to|target", desc = "Curving siphon beam with particles flowing from target to caster." })
add("beam.tether", { kind = "Beam", variant = "tether", loop = true, needs = "from,to|target", desc = "Gentle wavy link between two points (heal link, leash, charm)." })
add("beam.rainbow", { kind = "Beam", variant = "rainbow", duration = 5, needs = "at", desc = "A rainbow arc of six coloured bands over the target area with sparkles." })
add("beam.prism", { kind = "Beam", variant = "prism", duration = 2.5, needs = "at", desc = "Floating crystal prism splitting light into a fan of rainbow rays." })
add("beam.aurora", { kind = "Beam", variant = "aurora", duration = 6, needs = "at", desc = "Shimmering aurora curtains overhead." })

-- Strikes ---------------------------------------------------------------------------------------------------
add("strike.lightning", { kind = "Strike", variant = "lightning", element = "Lightning", duration = 0.6, needs = "at", desc = "Lightning strike from the sky: forked bolt, flash, scorch mark, sparks." })
add("strike.pillar", { kind = "Strike", variant = "pillar", element = "Light", duration = 1.5, needs = "at", desc = "Column of light descending onto the spot, ring on the ground." })

-- Impacts ---------------------------------------------------------------------------------------------------
add("impact", { kind = "Impact", needs = "at", duration = 1.2, desc = "Generic impact, element from params." })
for _, e in ELEMENTS do
	add("impact." .. string.lower(e), { kind = "Impact", element = e, duration = 1.2, needs = "at", desc = e .. " impact: flash, ring, element particles" .. (if e == "Earth" or e == "Metal" or e == "Ice" then ", debris chunks." else ".") })
end

-- Explosions ------------------------------------------------------------------------------------------------
add("explosion.small", { kind = "Explosion", variant = "small", element = "Fire", duration = 1.6, needs = "at", desc = "Small blast: flash, fireball, ring, sparks, puff of smoke." })
add("explosion.medium", { kind = "Explosion", variant = "medium", element = "Fire", duration = 2.5, needs = "at", desc = "Medium blast: light flash, nested fireballs, ground shockwave ring, debris, smoke column." })
add("explosion.huge", { kind = "Explosion", variant = "huge", element = "Fire", duration = 4, needs = "at", desc = "Huge blast: blinding flash, rising fireball, double shockwave, flying debris, crater scorch, mushroom smoke." })

-- Bursts ----------------------------------------------------------------------------------------------------
add("burst.nova", { kind = "Burst", variant = "nova", duration = 0.9, needs = "at", desc = "Expanding sphere shell of energy with a ring." })
add("burst.shockwave", { kind = "Burst", variant = "shockwave", duration = 0.8, needs = "at", desc = "Ground shockwave ring with dust kicked outward." })
add("burst.flash", { kind = "Burst", variant = "flash", duration = 0.5, needs = "at", desc = "Bright flash and light pop." })
add("burst.spikes", { kind = "Burst", variant = "spikes", duration = 3, needs = "at", desc = "Spikes erupt from the ground in a ring (stone, ice, crystal, metal, thorns by element) then sink." })
add("burst.shards", { kind = "Burst", variant = "shards", element = "Ice", duration = 1.4, needs = "at", desc = "Radial spray of tumbling shards." })
add("burst.quake", { kind = "Burst", variant = "quake", element = "Earth", duration = 3, needs = "at", desc = "Ground cracks, rocks heave upward, dust rings." })
add("burst.geyser", { kind = "Burst", variant = "geyser", element = "Water", duration = 2, needs = "at", desc = "Column of water (or element) erupting upward and raining back down." })
add("burst.frost", { kind = "Burst", variant = "frost", element = "Ice", duration = 2.5, needs = "at", desc = "Frost spreads on the ground, ice crystals snap up, cold mist." })
add("burst.blades", { kind = "Burst", variant = "blades", element = "Metal", duration = 1.6, needs = "at", desc = "Ghostly swords appear in a ring and slash inward." })
add("burst.splash", { kind = "Burst", variant = "splash", element = "Water", duration = 1, needs = "at", desc = "Water splash crown with droplets." })

-- Auras -----------------------------------------------------------------------------------------------------
add("aura.element", { kind = "Aura", variant = "element", loop = true, needs = "target", desc = "Looping element aura around a target: ground circle, rising particles, soft light." })
add("aura.charge", { kind = "Aura", variant = "charge", duration = 1, needs = "target|at", desc = "Charge-up: particles and rings converge before a cast." })
add("aura.buff", { kind = "Aura", variant = "buff", duration = 1.2, needs = "target|at", desc = "Power-up pulse: rising ring and sparkles." })
add("aura.heal", { kind = "Aura", variant = "heal", duration = 1.6, element = "Nature", needs = "target|at", desc = "Healing: soft green light, rising plus signs and leaves." })

-- Shields ---------------------------------------------------------------------------------------------------
add("shield.bubble", { kind = "Shield", variant = "bubble", loop = true, needs = "target|at", desc = "Sphere shield (ForceField in Spectral, glass + rim in Solid); handle:pulse() flashes it on hits." })
add("shield.barrier", { kind = "Shield", variant = "barrier", loop = true, needs = "at (facing) or from,to", desc = "Flat translucent barrier panel with frame posts." })
add("shield.dome", { kind = "Shield", variant = "dome", loop = true, needs = "at", desc = "Large ally dome with base ring." })
add("shield.mirror", { kind = "Shield", variant = "mirror", element = "Light", loop = true, needs = "target|at", desc = "Rotating mirror plates orbiting a target." })

-- Walls -----------------------------------------------------------------------------------------------------
add("wall", { kind = "Wall", loop = true, needs = "at (+ params.length) or from,to", desc = "Wall rising along a line; look by element (stone, ice, fire, thorns, metal, water, energy)." })
for _, v in { "stone", "ice", "fire", "thorns", "metal", "water", "energy" } do
	local el = ({ stone = "Earth", ice = "Ice", fire = "Fire", thorns = "Nature", metal = "Metal", water = "Water", energy = "Arcane" })[v]
	add("wall." .. v, { kind = "Wall", variant = v, element = el, loop = true, needs = "at or from,to", desc = "Wall of " .. v .. "." })
end

-- Clouds / rain / waves -------------------------------------------------------------------------------------
add("cloud.puff", { kind = "Cloud", variant = "puff", loop = true, needs = "at", desc = "Puffy cloud of overlapping spheres with drifting mist." })
add("cloud.rain", { kind = "Cloud", variant = "rain", element = "Water", loop = true, needs = "at", desc = "Grey cloud raining on the area (rain falls to the ground, splashes)." })
add("cloud.storm", { kind = "Cloud", variant = "storm", element = "Lightning", loop = true, needs = "at", desc = "Dark storm cloud with internal flashes and random lightning strikes." })
add("cloud.toxic", { kind = "Cloud", variant = "toxic", element = "Poison", loop = true, needs = "at", desc = "Low rolling toxic gas cloud with bubbles." })
add("cloud.steam", { kind = "Cloud", variant = "steam", element = "Water", loop = true, needs = "at", desc = "Thick white steam cloud that blocks vision." })
add("cloud.darkness", { kind = "Cloud", variant = "darkness", element = "Shadow", loop = true, needs = "at", desc = "Ink-black smoke sphere that swallows light." })
add("rain.local", { kind = "Rain", loop = true, needs = "at", desc = "Rain over an area; Fire = ember rain, Poison = acid rain, Ice = hail/snow." })
add("wave.water", { kind = "Wave", variant = "water", element = "Water", duration = 3, needs = "from,to", desc = "Curling wave crest sweeping along a path with foam and spray." })
add("wave.flame", { kind = "Wave", variant = "flame", element = "Fire", duration = 2.5, needs = "from,to", desc = "Rolling wall of fire sweeping forward." })
add("wave.earth", { kind = "Wave", variant = "earth", element = "Earth", duration = 2, needs = "from,to", desc = "Line of rocks heaving up in sequence (ground ripple)." })
add("wave.mud", { kind = "Wave", variant = "mud", element = "Earth", duration = 3, needs = "from,to", desc = "Churning mudslide sweeping forward." })

-- Zones -----------------------------------------------------------------------------------------------------
add("zone.tornado", { kind = "Zone", variant = "tornado", element = "Wind", loop = true, needs = "at (to = wander target)", desc = "Tornado funnel of swirling streak layers that visibly lifts and orbits debris, dust ring at the base; wanders toward params.to." })
add("zone.firestorm", { kind = "Zone", variant = "tornado", element = "Fire", loop = true, needs = "at", desc = "Fire tornado." })
add("zone.bladestorm", { kind = "Zone", variant = "tornado", element = "Metal", loop = true, needs = "at", desc = "Whirlwind carrying spinning blades." })
add("zone.vortex", { kind = "Zone", variant = "vortex", element = "Shadow", loop = true, needs = "at", desc = "Black hole: dark core, bright accretion disc, spiralling beams, debris pulled in and crushed." })
add("zone.whirlpool", { kind = "Zone", variant = "vortex", element = "Water", loop = true, needs = "at", desc = "Dark whirlpool dragging things down." })
add("zone.magnetic", { kind = "Zone", variant = "vortex", element = "Metal", loop = true, needs = "at", desc = "Magnetic storm: metal debris lifted into orbit, arcs between them." })
add("zone.sinkhole", { kind = "Zone", variant = "sinkhole", element = "Earth", loop = true, needs = "at", desc = "Ground caves into a dark pit; dust pours in, rocks sink." })
add("zone.blizzard", { kind = "Zone", variant = "blizzard", element = "Ice", loop = true, needs = "at", desc = "Local howling snowstorm with frost ground, ice crystals and wind." })
add("zone.wildfire", { kind = "Zone", variant = "wildfire", element = "Fire", loop = true, needs = "at", desc = "Ground fire that spreads outward over time: flames, embers, scorch marks, smoke." })
add("zone.pool", { kind = "Zone", variant = "pool", loop = true, needs = "at", desc = "Hazard pool on the ground; element decides: magma, water, frost, poison, mud, black ice, light circle..." })
add("zone.storm", { kind = "Zone", variant = "storm", element = "Lightning", loop = true, needs = "at", desc = "Thunderstorm: storm cloud plus repeated lightning strikes in the area." })
add("zone.sandstorm", { kind = "Zone", variant = "sandstorm", element = "Earth", loop = true, needs = "at", desc = "Wall of driven sand and dust, low visibility." })
add("zone.garden", { kind = "Zone", variant = "garden", element = "Nature", loop = true, needs = "at", desc = "Plants grow out of the ground (flowers; glowing mushrooms for Arcane; crystals for Light; ice flowers for Ice)." })
add("zone.spores", { kind = "Zone", variant = "spores", element = "Poison", loop = true, needs = "at", desc = "Mushrooms puffing clouds of spores." })
add("zone.runes", { kind = "Zone", variant = "runes", element = "Arcane", loop = true, needs = "at", desc = "Rotating magic circle on the ground with rising glyphs." })
add("zone.sanctum", { kind = "Zone", variant = "sanctum", element = "Light", loop = true, needs = "at", desc = "Holy circle: light shafts, motes, soft ground glow." })
add("zone.eclipse", { kind = "Zone", variant = "eclipse", element = "Shadow", loop = true, needs = "at", desc = "Black sun with a burning corona above the area; darkness below." })
add("zone.starfall", { kind = "Zone", variant = "starfall", element = "Light", loop = true, needs = "at", desc = "Shooting stars rain onto the area at random." })

-- Weather (follows the camera; one at a time is recommended) -------------------------------------------------
for _, v in { "rain", "snow", "storm", "sandstorm", "ash", "fireflies", "spores" } do
	add("weather." .. v, { kind = "Weather", variant = v, loop = true, needs = "-", desc = "Screen-filling " .. v .. " around the camera." })
end

-- Spawn / despawn -------------------------------------------------------------------------------------------
add("spawn.materialize", { kind = "Spawn", variant = "materialize", duration = 1.4, needs = "target (Model/BasePart) or at", desc = "Summon materialize: rune circle, light pillar, particles converge, target fades in (LocalTransparencyModifier)." })
add("spawn.dissolve", { kind = "Spawn", variant = "dissolve", duration = 1.2, needs = "target or at", desc = "Despawn: target fades out while particles stream upward." })
add("spawn.portal", { kind = "Spawn", variant = "portal", duration = 2.5, needs = "at", desc = "Swirling vertical portal ring opening then closing." })
add("spawn.teleport", { kind = "Spawn", variant = "teleport", duration = 0.8, needs = "from,to or at", desc = "Blink: implode at from, burst at to." })

-- Status effects (Effects.status(target, name, duration)) ---------------------------------------------------
local STATUS = {
	Burn = "Flames and embers licking the target, flickering orange light.",
	Freeze = "Encased in ice crystals, frost mist, icy tint.",
	Shock = "Electric arcs crawling over the target, sparks.",
	Poison = "Green bubbles and drips, sickly tint.",
	Slow = "Heavy blue rings at the feet, sluggish motes.",
	Stun = "Stars orbiting over the head.",
	Blind = "Dark cloud around the head.",
	Wet = "Water drips and a small puddle ring.",
	Charm = "Floating hearts and pink sparkles.",
	Root = "Vines wrapping the legs.",
	Confuse = "Swirling question marks over the head.",
	Weaken = "Sinking down-arrows, dim aura.",
	Haste = "Speed streaks and wind at the feet.",
	Regen = "Rising plus signs and soft green light.",
	Shielded = "Thin shimmering shell.",
	Silence = "Purple rune ring over the head with a sealing glyph.",
	Corrode = "Rust flakes and acid fizz.",
}
local STATUS_ELEMENT = {
	Burn = "Fire", Freeze = "Ice", Shock = "Lightning", Poison = "Poison", Slow = "Water", Stun = "Light", Blind = "Shadow",
	Wet = "Water", Charm = "Arcane", Root = "Nature", Confuse = "Arcane", Weaken = "Shadow", Haste = "Wind", Regen = "Nature",
	Shielded = "Light", Silence = "Arcane", Corrode = "Poison",
}
for name, desc in STATUS do
	add("status." .. string.lower(name), { kind = "Status", variant = name, element = STATUS_ELEMENT[name], loop = true, needs = "target", desc = desc })
end
Catalogue.Statuses = STATUS

-- Material / mood particles (looping, attached to a target; referenced by data/materials.json and accents) ---
-- Bare snake_case ids by contract with the material data. LOD-aware: thinned/hidden by distance and quality.
local ATTACHED = {
	drip_sauce = "Red sauce drips.", drip_honey = "Slow amber honey drips.", goo_drip = "Green slime drips.",
	water_drip = "Water drips.", ink_drip = "Black ink drips.", sawdust = "Falling sawdust flakes.",
	crumbs = "Falling crumbs.", sprinkles = "Colourful sprinkles.", sparkle = "Twinkling stars.", glitter = "Rainbow glitter.",
	confetti = "Confetti bursts.", bees = "A buzzing swarm of little bees orbiting.", flies = "Buzzing flies.",
	butterflies = "Fluttering butterflies.", shards = "Glinting shards dropping off.", steam = "Rising steam.",
	smoke = "Rising smoke.", embers = "Rising embers.", sparks = "Periodic spark spits.", zap = "Electric crackle.",
	frost = "Cold mist falling off.", snowflakes = "Snowflakes.", bubbles = "Rising bubbles.", petals = "Drifting petals.",
	leaves = "Drifting leaves.", feathers = "Drifting feathers.", fluff = "Soft fluff floating off.", sand = "Trickling sand.",
	dust = "Dusty puffs.", coins = "Spinning gold glints.", music_notes = "Floating music notes.", hearts = "Floating hearts.",
	snore = "Zzz rising from the head.", anger_steam = "Angry steam puffs from the head.", sweat_drops = "Nervous sweat drops.",
	thruster = "Thruster flame jet (points along the target's back).", glitch = "Glitch flicker with pixel bits.",
	rainbow_trail = "Rainbow trail while moving.", stars = "Small stars circling.", question_marks = "Floating question marks.",
	halo_glow = "Glowing halo above the head.",
}
for id, desc in ATTACHED do
	add(id, { kind = "Attached", variant = id, loop = true, needs = "target", family = "material", desc = desc })
end
Catalogue.Attached = ATTACHED

-- Material x element reaction visuals (Reactions.material(...).vfx) -----------------------------------------
local MAT = {
	["mat.ignite"] = { "Catches fire fast: flames race over it, embers and smoke.", { { id = "impact.fire" }, { id = "smoke", d = 0.1, dur = 3 }, { id = "embers", dur = 3 } } },
	["mat.melt"] = { "Melts and drips into a puddle.", { { id = "goo_drip", dur = 3 }, { id = "zone.pool", dur = 4, s = 0.5 }, { id = "steam", dur = 2 } } },
	["mat.bake"] = { "Bakes hard with a warm glow and steam.", { { id = "aura.buff", el = "Fire" }, { id = "steam", dur = 2 } } },
	["mat.cook"] = { "Sizzles and smells delicious.", { { id = "steam", dur = 2.5 }, { id = "embers", dur = 1.5 }, { id = "impact.fire", s = 0.6 } } },
	["mat.pop"] = { "Pops!", { { id = "burst.flash", s = 0.6 }, { id = "confetti", dur = 1 }, { id = "burst.shockwave", s = 0.5 } } },
	["mat.heat"] = { "Glows red-hot.", { { id = "aura.buff", el = "Fire" }, { id = "sparks", dur = 2 } } },
	["mat.soggy"] = { "Goes soggy and droopy.", { { id = "water_drip", dur = 4 }, { id = "impact.water", s = 0.6 } } },
	["mat.mud"] = { "Turns to mud.", { { id = "zone.pool", el = "Earth", colour = "#5E4630", dur = 5, s = 0.6 }, { id = "burst.splash", colour = "#5E4630" } } },
	["mat.rust"] = { "Rusts and flakes.", { { id = "impact.metal", colour = "#B5562A" }, { id = "dust", colour = "#B5562A", dur = 2 } } },
	["mat.dissolve"] = { "Fizzes and dissolves.", { { id = "bubbles", dur = 2.5 }, { id = "spawn.dissolve" } } },
	["mat.cool"] = { "Hisses and cools to stone.", { { id = "cloud.steam", dur = 2, s = 0.5 }, { id = "impact.earth", s = 0.6 } } },
	["mat.grow"] = { "Sprouts and grows.", { { id = "zone.garden", dur = 4, s = 0.5 }, { id = "aura.heal" } } },
	["mat.short"] = { "Short-circuits in a shower of sparks.", { { id = "sparks", dur = 1.5 }, { id = "zap", dur = 1.5 }, { id = "smoke", d = 0.3, dur = 2 } } },
	["mat.freeze"] = { "Freezes solid.", { { id = "burst.frost", s = 0.6 }, { id = "frost", dur = 3 } } },
	["mat.wilt"] = { "Wilts and browns.", { { id = "leaves", dur = 2, colour = "#8A6A3A" }, { id = "impact.shadow", s = 0.5 } } },
	["mat.conduct"] = { "Electricity races through it.", { { id = "zap", dur = 2 }, { id = "beam.chain" }, { id = "burst.flash", el = "Lightning", s = 0.6 } } },
	["mat.fuse"] = { "Fuses into glass.", { { id = "burst.flash", el = "Lightning" }, { id = "burst.shards", colour = "#CFE8E2", s = 0.6 } } },
	["mat.shatter"] = { "Shatters into pieces.", { { id = "burst.shards" }, { id = "burst.flash", s = 0.5 } } },
	["mat.scatter"] = { "Gets blown everywhere.", { { id = "burst.shockwave", el = "Wind" }, { id = "leaves", dur = 1.5 } } },
	["mat.drift"] = { "Floats away on the wind.", { { id = "aura.buff", el = "Wind" }, { id = "fluff", dur = 2 } } },
	["mat.crack"] = { "Roots crack it apart.", { { id = "burst.spikes", el = "Nature", s = 0.6 }, { id = "dust", dur = 1.5 } } },
	["mat.gleam"] = { "Gleams and reflects the light.", { { id = "sparkle", dur = 2 }, { id = "burst.flash", el = "Light", s = 0.6 } } },
	["mat.purify"] = { "Cleansed by light.", { { id = "burst.nova", el = "Light", s = 0.7 }, { id = "sparkle", dur = 1.5 } } },
	["mat.decay"] = { "Rots and crumbles.", { { id = "flies", dur = 3 }, { id = "impact.shadow", s = 0.6 } } },
	["mat.corrode"] = { "Acid eats into it.", { { id = "bubbles", el = "Poison", dur = 2.5 }, { id = "impact.poison", s = 0.6 } } },
	["mat.spoil"] = { "Spoils: green and stinky.", { { id = "flies", dur = 3 }, { id = "cloud.toxic", s = 0.4, dur = 3 } } },
	["mat.shred"] = { "Sliced to ribbons.", { { id = "burst.blades", s = 0.6 }, { id = "confetti", dur = 1, colour = "#EDE6D6" } } },
	["mat.transmute"] = { "Transmuted to gold!", { { id = "burst.nova", el = "Arcane" }, { id = "coins", dur = 2 }, { id = "sparkle", dur = 2 } } },
	["mat.empower"] = { "Hums with magic.", { { id = "aura.buff", el = "Arcane" }, { id = "zone.runes", s = 0.4, dur = 2 } } },
	["mat.explode"] = { "Explodes!", { { id = "explosion.medium" } } },
	["mat.evaporate"] = { "Boils off into steam.", { { id = "cloud.steam", s = 0.6, dur = 3 } } },
}
for id, def in MAT do
	add(id, { kind = "Composite", family = "mat", desc = def[1], layers = def[2], duration = 3 })
end

-- Reactions: one composite per reaction ----------------------------------------------------------------------
-- Layers inherit at/from/to/target/style/scale from the play() params; el overrides the element.
local function L(id: string, el: string?, d: number?, s: number?, extra: { [string]: any }?): Layer
	local l: any = { id = id, el = el, d = d, s = s }
	if extra then
		for k, v in extra do
			l[k] = v
		end
	end
	return l
end

local RECIPES: { [string]: { Layer } } = {
	Extinguish = { L("cloud.steam", "Water", 0, 0.6, { dur = 2 }), L("burst.splash", "Water"), L("burst.flash", "Water", 0, 0.5) },
	Steam = { L("cloud.steam", "Water"), L("impact.ice", "Ice", 0, 0.8), L("burst.flash", "Fire", 0, 0.6) },
	Plasma = { L("burst.flash", "Lightning", 0, 1.4), L("explosion.medium", "Lightning"), L("burst.nova", "Fire", 0.05) },
	Magma = { L("zone.pool", "Fire"), L("impact.earth", "Earth"), L("embers", "Fire", 0, 1, { dur = 3 }) },
	Firestorm = { L("zone.firestorm", "Fire"), L("burst.shockwave", "Wind") },
	Wildfire = { L("zone.wildfire", "Fire"), L("impact.nature", "Nature", 0, 0.7) },
	SolarFlare = { L("burst.flash", "Light", 0, 2), L("explosion.medium", "Fire", 0.04), L("burst.nova", "Light", 0.04, 1.4) },
	Shadowflame = { L("impact.fire", "Fire", 0, 1, { colour = "#8A3CFF" }), L("burst.nova", "Shadow", 0.05) },
	GasExplosion = { L("burst.nova", "Poison", 0, 0.8), L("explosion.huge", "Fire", 0.12) },
	Molten = { L("impact.metal", "Metal"), L("impact.fire", "Fire", 0.05), L("goo_drip", "Fire", 0.1, 1, { dur = 3, colour = "#FF7A1F" }) },
	Spellfire = { L("burst.nova", "Arcane"), L("impact.fire", "Fire", 0.05), L("aura.buff", "Fire", 0.15) },
	Electrocute = { L("burst.splash", "Water"), L("beam.chain", "Lightning", 0.05), L("burst.nova", "Lightning", 0.05, 1.2) },
	FlashFreeze = { L("burst.frost", "Ice"), L("impact.water", "Water", 0, 0.6) },
	Mudslide = { L("wave.mud", "Earth") },
	Typhoon = { L("zone.tornado", "Water", 0, 1.2), L("rain.local", "Water", 0, 1.4) },
	Bloom = { L("zone.garden", "Nature"), L("aura.heal", "Water", 0.1) },
	Abyss = { L("zone.whirlpool", "Water", 0, 1, { colour = "#14335C" }), L("cloud.darkness", "Shadow", 0, 0.6) },
	Contamination = { L("zone.pool", "Poison"), L("burst.splash", "Poison") },
	Rust = { L("impact.metal", "Metal", 0, 1, { colour = "#B5562A" }), L("impact.water", "Water", 0.05, 0.7) },
	ManaSpring = { L("burst.geyser", "Arcane"), L("zone.sanctum", "Water", 0.2) },
	Rainbow = { L("beam.rainbow", "Light"), L("burst.splash", "Water", 0, 0.7) },
	Superconductor = { L("burst.frost", "Ice", 0, 0.7), L("beam.chain", "Lightning", 0.05, 1, { colour = "#BDEBFF" }) },
	Permafrost = { L("zone.pool", "Ice"), L("burst.spikes", "Ice", 0, 0.6) },
	Blizzard = { L("zone.blizzard", "Ice") },
	Frostbloom = { L("burst.spikes", "Ice", 0, 1.1), L("zone.garden", "Ice", 0.2, 0.8) },
	Prism = { L("beam.prism", "Light"), L("impact.ice", "Ice", 0, 0.7) },
	BlackIce = { L("zone.pool", "Ice", 0, 1, { colour = "#2C3E5C" }), L("burst.frost", "Shadow", 0, 0.7) },
	Cryotoxin = { L("impact.poison", "Poison"), L("burst.frost", "Ice", 0.05, 0.6) },
	Shatter = { L("burst.shards", "Ice", 0, 1.3), L("impact.metal", "Metal"), L("burst.flash", "Ice", 0, 0.8) },
	Stasis = { L("shield.bubble", "Ice", 0, 1, { colour = "#B9A6FF" }), L("zone.runes", "Arcane", 0, 0.7), L("burst.frost", "Ice", 0, 0.5) },
	Fulgurite = { L("strike.lightning", "Lightning"), L("burst.spikes", "Earth", 0.05, 0.8, { colour = "#CFE8E2" }), L("burst.flash", "Lightning", 0.05) },
	Thunderstorm = { L("zone.storm", "Lightning") },
	Sparkbloom = { L("burst.nova", "Nature", 0, 0.9), L("beam.chain", "Lightning", 0.05), L("stars", "Lightning", 0, 1, { dur = 1.5 }) },
	Flashbang = { L("burst.flash", "Light", 0, 3), L("burst.shockwave", "Lightning", 0.02) },
	BlackLightning = { L("strike.lightning", "Shadow"), L("beam.chain", "Shadow", 0.08) },
	Neurotoxin = { L("impact.poison", "Poison"), L("impact.lightning", "Lightning", 0.05) },
	MagneticStorm = { L("zone.magnetic", "Metal"), L("burst.nova", "Lightning", 0, 0.8) },
	LeylineSurge = { L("zone.runes", "Arcane", 0, 1, { dur = 2 }), L("strike.lightning", "Arcane", 0.15), L("beam.chain", "Arcane", 0.2) },
	Sandstorm = { L("zone.sandstorm", "Earth") },
	Thornwall = { L("wall.thorns", "Nature") },
	Crystallize = { L("burst.spikes", "Light", 0, 0.8), L("aura.buff", "Light", 0.1) },
	Sinkhole = { L("zone.sinkhole", "Earth"), L("cloud.darkness", "Shadow", 0, 0.4) },
	Blight = { L("zone.pool", "Poison", 0, 1, { colour = "#4A3A1E" }), L("cloud.toxic", "Poison", 0.2, 0.6) },
	IronSpikes = { L("burst.spikes", "Metal", 0, 1.2), L("burst.shockwave", "Earth") },
	Runequake = { L("zone.runes", "Arcane", 0, 1, { dur = 3 }), L("burst.quake", "Earth", 0.2), L("spawn.materialize", "Earth", 0.6) },
	PollenStorm = { L("zone.tornado", "Nature", 0, 0.7), L("zone.spores", "Nature", 0, 1, { colour = "#FFD84A" }) },
	Aurora = { L("beam.aurora", "Wind"), L("aura.heal", "Light", 0.2) },
	Nightwind = { L("zone.tornado", "Shadow", 0, 0.6), L("cloud.darkness", "Shadow", 0.1, 0.8) },
	ToxicCloud = { L("cloud.toxic", "Poison") },
	Bladestorm = { L("zone.bladestorm", "Metal") },
	WarpGale = { L("spawn.teleport", "Arcane"), L("burst.shockwave", "Wind") },
	Sunbloom = { L("zone.garden", "Light"), L("aura.heal", "Nature", 0.1), L("burst.flash", "Light", 0, 0.6) },
	Wither = { L("beam.drain", "Shadow"), L("impact.nature", "Nature", 0, 0.8, { colour = "#7A5A2E" }) },
	Spores = { L("zone.spores", "Poison") },
	Ironbark = { L("aura.buff", "Metal"), L("impact.nature", "Nature", 0.05) },
	FeyRing = { L("zone.garden", "Arcane"), L("zone.runes", "Nature", 0, 0.8) },
	Eclipse = { L("zone.eclipse", "Shadow"), L("burst.flash", "Light", 0, 1.2) },
	Purify = { L("burst.nova", "Light"), L("aura.heal", "Light", 0.1), L("burst.flash", "Light", 0, 0.8) },
	Mirror = { L("shield.mirror", "Light") },
	Starfall = { L("zone.starfall", "Light") },
	Plague = { L("cloud.toxic", "Shadow", 0, 1, { colour = "#4E7A2A" }), L("impact.shadow", "Shadow") },
	PhantomBlades = { L("burst.blades", "Shadow") },
	Void = { L("zone.vortex", "Shadow"), L("burst.nova", "Arcane", 0, 0.8) },
	Corrosion = { L("impact.poison", "Poison"), L("impact.metal", "Metal", 0.05, 0.8, { colour = "#B5562A" }), L("bubbles", "Poison", 0, 1, { dur = 3 }) },
	Hex = { L("zone.runes", "Poison", 0, 0.7, { dur = 2.5 }), L("burst.nova", "Arcane", 0.1) },
	Enchant = { L("aura.buff", "Arcane"), L("burst.blades", "Arcane", 0.1, 0.8) },
	Inferno = { L("zone.wildfire", "Fire", 0, 1.4), L("explosion.medium", "Fire") },
	Tsunami = { L("wave.water", "Water", 0, 1.6) },
	AbsoluteZero = { L("burst.frost", "Ice", 0, 2), L("burst.shockwave", "Ice"), L("zone.blizzard", "Ice", 0.1, 0.8) },
	Overcharge = { L("strike.lightning", "Lightning"), L("strike.lightning", "Lightning", 0.12, 1, { off = { 6, 0, 3 } }), L("strike.lightning", "Lightning", 0.24, 1, { off = { -5, 0, -4 } }), L("beam.chain", "Lightning", 0.3) },
	Earthquake = { L("burst.quake", "Earth", 0, 1.5), L("burst.shockwave", "Earth", 0, 1.5) },
	Tornado = { L("zone.tornado", "Wind", 0, 1.3) },
	Overgrowth = { L("zone.garden", "Nature", 0, 1.5), L("burst.spikes", "Nature", 0, 1.1) },
	Supernova = { L("burst.flash", "Light", 0, 2.5), L("explosion.huge", "Light", 0.05) },
	Blackout = { L("cloud.darkness", "Shadow", 0, 1.5), L("burst.nova", "Shadow") },
	Pandemic = { L("cloud.toxic", "Poison", 0, 1.4), L("zone.pool", "Poison", 0.1) },
	Fortress = { L("shield.dome", "Metal"), L("burst.spikes", "Metal", 0, 0.8) },
	ArcaneOverload = { L("zone.runes", "Arcane", 0, 1.2, { dur = 1 }), L("explosion.huge", "Arcane", 0.5), L("burst.nova", "Arcane", 0.5, 1.5) },
}
Catalogue.Recipes = RECIPES

for _, r in Reactions.all() do
	local recipe = RECIPES[r.id]
	if recipe then
		add(r.vfx, {
			kind = "Composite",
			family = "reaction",
			duration = r.durationHint,
			desc = r.name .. ": " .. r.description,
			layers = recipe,
			reaction = r.id,
		})
	end
end

-- ===========================================================================================================
-- Queries

--- Entry for an id, or nil.
function Catalogue.get(id: string): Entry?
	return ENTRIES[id]
end

function Catalogue.has(id: string): boolean
	return ENTRIES[id] ~= nil
end

--- All ids in declaration order.
function Catalogue.ids(): { string }
	return table.clone(ORDER)
end

--- Status entry id for a status name ("Burn" -> "status.burn").
function Catalogue.statusId(name: string): string
	return "status." .. string.lower(name)
end

-- Resource cost estimates per kind/variant (used for budget admission; conservative). The runtime reports
-- actual usage in Effects.stats().
local COST: { [string]: { [string]: { [string]: number } } } = {
	Projectile = {
		["*"] = { parts = 2, emitters = 2, trails = 1, lights = 1 },
		meteor = { parts = 4, emitters = 4, trails = 1, lights = 1 },
		boulder = { parts = 3, emitters = 1, trails = 0, lights = 0 },
	},
	Beam = { ["*"] = { parts = 0, emitters = 2, beams = 3, lights = 1 }, chain = { emitters = 1, beams = 8, lights = 1 }, rainbow = { emitters = 1, beams = 6 }, prism = { parts = 1, emitters = 1, beams = 7 }, aurora = { emitters = 1, beams = 4 } },
	Strike = { ["*"] = { parts = 1, emitters = 2, beams = 6, lights = 1 } },
	Impact = { ["*"] = { parts = 2, emitters = 3, lights = 1 } },
	Explosion = { small = { parts = 3, emitters = 4, lights = 1 }, medium = { parts = 10, emitters = 5, lights = 1 }, huge = { parts = 18, emitters = 6, lights = 1 } },
	Burst = { ["*"] = { parts = 2, emitters = 2, lights = 1 }, spikes = { parts = 12, emitters = 2 }, quake = { parts = 12, emitters = 2 }, blades = { parts = 8, emitters = 1, trails = 4 }, frost = { parts = 9, emitters = 2 } },
	Aura = { ["*"] = { parts = 1, emitters = 3, lights = 1 } },
	Shield = { ["*"] = { parts = 3, emitters = 1, lights = 1 }, mirror = { parts = 4, emitters = 1 } },
	Wall = { ["*"] = { parts = 12, emitters = 2 } },
	Cloud = { ["*"] = { parts = 7, emitters = 3, lights = 1 } },
	Rain = { ["*"] = { parts = 4, emitters = 4 } },
	Wave = { ["*"] = { parts = 10, emitters = 3 } },
	Zone = {
		["*"] = { parts = 4, emitters = 4, lights = 1 },
		tornado = { parts = 14, emitters = 6, beams = 4, lights = 1 },
		vortex = { parts = 14, emitters = 4, beams = 6, lights = 1 },
		wildfire = { parts = 10, emitters = 10, lights = 1 },
		garden = { parts = 24, emitters = 2 },
		storm = { parts = 7, emitters = 4, beams = 6, lights = 1 },
	},
	Weather = { ["*"] = { parts = 4, emitters = 5 } },
	Spawn = { ["*"] = { parts = 3, emitters = 3, lights = 1 } },
	Status = { ["*"] = { parts = 0, emitters = 2, lights = 0 }, Freeze = { parts = 6, emitters = 1, highlights = 1 }, Stun = { parts = 3, emitters = 0 }, Root = { parts = 6, emitters = 1 }, Shielded = { parts = 1, emitters = 0 } },
	Attached = { ["*"] = { emitters = 1 }, bees = { parts = 6 }, flies = { parts = 5 }, butterflies = { parts = 4 }, halo_glow = { parts = 1 }, rainbow_trail = { trails = 1 } },
}

--- Estimated resource cost of an effect (composites sum their layers).
function Catalogue.cost(id: string, depth: number?): { [string]: number }
	local out = { parts = 0, emitters = 0, beams = 0, trails = 0, lights = 0, highlights = 0 }
	local e = ENTRIES[id]
	if e == nil or (depth or 0) > 4 then
		return out
	end
	if e.kind == "Composite" then
		for _, layer in e.layers or {} do
			local c = Catalogue.cost(layer.id, (depth or 0) + 1)
			for k, v in c do
				out[k] += v
			end
		end
		return out
	end
	local byKind = COST[e.kind] or {}
	local c = byKind[e.variant or "*"] or byKind["*"] or {}
	for k, v in c do
		out[k] += v
	end
	return out
end

--- Validates the catalogue. `kinds` (optional) = set of renderer kinds that exist; `presets`/`assets`
--- optional checks too. Returns a list of problems.
function Catalogue.validate(kinds: { [string]: boolean }?): { string }
	local errs = {}
	for _, id in ORDER do
		local e = ENTRIES[id]
		if not string.match(id, "^[%l%d_%.]+$") then
			table.insert(errs, id .. ": ids are lowercase dotted/snake_case")
		end
		if type(e.desc) ~= "string" or #e.desc < 5 then
			table.insert(errs, id .. ": missing desc")
		end
		if kinds and not kinds[e.kind] then
			table.insert(errs, id .. ": no renderer for kind " .. e.kind)
		end
		if e.kind == "Composite" then
			if not e.layers or #e.layers == 0 then
				table.insert(errs, id .. ": composite without layers")
			end
			for _, l in e.layers or {} do
				local target = ENTRIES[l.id]
				if target == nil then
					table.insert(errs, id .. ": layer " .. l.id .. " does not exist")
				elseif target.kind == "Composite" and target.family == "reaction" then
					table.insert(errs, id .. ": layer " .. l.id .. " nests a reaction")
				end
			end
		end
	end
	for _, r in Reactions.all() do
		if not ENTRIES[r.vfx] then
			table.insert(errs, "reaction " .. r.id .. ": no effect " .. r.vfx .. " (add a RECIPES entry)")
		end
	end
	for name in RECIPES do
		if not Reactions.byId(name) then
			table.insert(errs, "recipe " .. name .. " has no reaction")
		end
	end
	return errs
end

return Catalogue
