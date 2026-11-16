--!strict
-- Element matchups and reactions (DESIGN.md §4, §7). Pure Luau, data-driven.
--
-- Source of truth: data/reactions.json + data/matchups.json + data/material_reactions.json. The block between the GENERATED markers is
-- compiled from them by `python3 tools/gen_reactions.py`; never edit it by hand. The reactions spec checks the
-- embedded data equals the JSON, so a stale block fails CI.
--
-- The engine decides meaning, never balance: matchup() returns a multiplier HINT (0.5 / 1 / 1.5) and each
-- reaction carries semantic hooks + statuses + magnitude/duration hints. Each game maps those to numbers.

local Types = require(script.Parent.Types)

type Element = Types.Element
type Reaction = Types.Reaction

local Reactions = {}

-- Semantic gameplay hooks. Games implement the ones they care about; unknown hooks are safe to ignore.
-- Every hook used in data/reactions.json must be listed here (enforced by the spec).
Reactions.HookInfo = table.freeze({
	Amplify = "Same-element stack: a bigger, stronger version of the element's own effect.",
	AreaDamage = "Damage everything in the reaction radius once.",
	ArmorBreak = "Reduce target armour/durability for the duration.",
	Blocks = "Creates or strengthens something that blocks movement or projectiles.",
	BlocksVision = "Hides what is inside or behind the effect (fog, smoke, darkness, glare).",
	BuffDamage = "Allies (or the caster's next hits) deal more damage.",
	BuffSpeed = "Allies move/cast faster.",
	CancelsBuffs = "Removes active buffs from enemies in the area.",
	CancelsElement = "The two elements cancel: put out burns, ground charge, neutralise poison.",
	Chain = "Damage jumps from target to nearby targets (prefer Wet/Marked ones).",
	Charms = "Enemies are distracted or briefly fight for/ignore the caster.",
	Cleanses = "Removes negative statuses from allies.",
	Confuses = "Enemies wander, reverse controls or target randomly.",
	DamageOverTime = "Ticks damage over the duration.",
	Disarms = "Metal weapons/turrets are yanked away or disabled briefly.",
	Drains = "Steals health/energy from targets to the caster.",
	Explodes = "A big explosive burst (pair with AreaDamage + Knockback).",
	ExtendsStatus = "Statuses applied by this reaction last longer than normal.",
	Freezes = "Targets are frozen in place.",
	GroundHazard = "Leaves a hazardous ground area that hurts or hinders whoever stands in it.",
	Grows = "Plants/objects grow bigger or new ones sprout.",
	Heals = "Restores health to allies in the area.",
	IgnoresShields = "Damage bypasses shields/barriers.",
	Invisibility = "Allies (or the hazard itself) become hard to see.",
	Knockback = "Pushes targets away from the centre.",
	Lifts = "Throws targets up into the air (tornado, quake, magnetism).",
	Lingers = "The effect stays on the field for its duration.",
	Marks = "Marks targets; later hits or chains prefer marked targets.",
	Moves = "The zone drifts or wanders across the field.",
	Pierces = "Passes through targets/armour and keeps going.",
	Pulls = "Drags targets toward the centre.",
	Pushes = "Sweeps targets along a direction.",
	RandomStrikes = "Random strikes land inside the area over the duration.",
	Reflects = "Bounces projectiles or beams back.",
	Roots = "Targets cannot move but can still act.",
	Shields = "Grants allies a damage-absorbing shield.",
	Silences = "Targets cannot cast/type spells briefly.",
	Splits = "Splits into several smaller projectiles/shards.",
	Spreads = "Jumps to nearby targets or grows across the ground over time.",
	Stuns = "Targets cannot move or act.",
	Summons = "Creates an allied summon (golem, blades, ...).",
	Teleports = "Moves targets (or allies) to another place.",
	Wall = "Raises a wall/barrier along a line or ring.",
	Weakens = "Targets deal less damage.",
})

-- Status ids a reaction may apply. Effects.status renders each of them.
Reactions.Statuses = table.freeze({
	"Burn", "Freeze", "Shock", "Poison", "Slow", "Stun", "Blind", "Wet", "Charm",
	"Root", "Confuse", "Weaken", "Haste", "Regen", "Shielded", "Silence", "Corrode",
})

-- Material-side hooks used by material reactions (data/material_reactions.json) on top of HookInfo. They mirror
-- the summon material hooks in data/materials.json, so a game can treat "Ignite on wood" like a BurnsFast material.
Reactions.MaterialHookInfo = table.freeze({
	Burns = "The object is on fire and takes damage over time.",
	BurnsFast = "Burns quickly and spreads fire to neighbours.",
	Conductive = "Carries electricity to whatever touches it.",
	DamageAura = "Hurts enemies that stand next to it.",
	Durable = "Tougher than before (more HP / armour).",
	EdibleLure = "Smells like food: enemies are drawn to it.",
	Flies = "Floats or is blown up into the air.",
	Hardens = "Turns hard: higher durability, no longer soft/sticky.",
	Lures = "Attracts enemies toward it.",
	Melts = "Softens into a puddle; loses its shape over the duration.",
	Poisons = "Becomes poisonous to touch or eat.",
	ShattersOnHit = "Brittle: the next solid hit breaks it into shards.",
	Shrinks = "Gets smaller (lower size/HP).",
	Slows = "Slows enemies that walk through or over it.",
	Transform = "Turns into a different material (see the outcome's transform hint).",
})

Reactions.Results = table.freeze({ "Zone", "Burst", "Status", "Transform", "Buff", "Cancel" })

Reactions.Multipliers = table.freeze({ Strong = 1.5, Neutral = 1, Resisted = 0.5 })

-- BEGIN GENERATED DATA (tools/gen_reactions.py)
local ELEMENTS = { "Fire", "Water", "Ice", "Lightning", "Earth", "Wind", "Nature", "Light", "Shadow", "Poison", "Metal", "Arcane" }
local MATCHUPS = {
	Fire = {
		Fire = { m = 0.5, why = "Fire cannot burn what is already burning." },
		Water = { m = 0.5, why = "Water resists Fire: water douses flames." },
		Ice = { m = 1.5, why = "Heat melts ice in seconds." },
		Lightning = { m = 1, why = "Fire burns Lightning as well as anything else." },
		Earth = { m = 0.5, why = "Earth resists Fire: dirt and stone smother flames." },
		Wind = { m = 1, why = "Wind fans the flames, but it does not burn." },
		Nature = { m = 1.5, why = "Fire burns through leaves, roots and bark." },
		Light = { m = 1, why = "Fire burns Light as well as anything else." },
		Shadow = { m = 1, why = "Fire burns Shadow as well as anything else." },
		Poison = { m = 1, why = "Fire burns Poison as well as anything else." },
		Metal = { m = 1.5, why = "Forge heat softens steel and cooks whoever wears it." },
		Arcane = { m = 1, why = "Fire burns Arcane as well as anything else." },
	},
	Water = {
		Fire = { m = 1.5, why = "Water douses flames." },
		Water = { m = 0.5, why = "Water just joins more water." },
		Ice = { m = 0.5, why = "Ice resists Water: cold freezes water solid." },
		Lightning = { m = 0.5, why = "Lightning resists Water: water conducts every volt." },
		Earth = { m = 1.5, why = "Floods erode stone and turn soil to mud." },
		Wind = { m = 1, why = "Water splashes Wind without special effect." },
		Nature = { m = 0.5, why = "Nature resists Water: roots drink the water up." },
		Light = { m = 1, why = "Water splashes Light without special effect." },
		Shadow = { m = 1, why = "Water splashes Shadow without special effect." },
		Poison = { m = 0.5, why = "Poison resists Water: toxins taint the water." },
		Metal = { m = 1, why = "Water slowly rusts metal; on its own it barely dents it." },
		Arcane = { m = 1, why = "Water splashes Arcane without special effect." },
	},
	Ice = {
		Fire = { m = 0.5, why = "Fire resists Ice: heat melts ice in seconds." },
		Water = { m = 1.5, why = "Cold freezes water solid." },
		Ice = { m = 0.5, why = "Ice is already as cold as it gets." },
		Lightning = { m = 1, why = "Ice chills Lightning, nothing more." },
		Earth = { m = 1, why = "Frost cracks stone over winters, not seconds." },
		Wind = { m = 1.5, why = "Freezing air goes heavy and still." },
		Nature = { m = 1.5, why = "Frost kills leaves and stops growth." },
		Light = { m = 0.5, why = "Light resists Ice: sunlight melts ice." },
		Shadow = { m = 1, why = "Ice chills Shadow, nothing more." },
		Poison = { m = 1, why = "Ice chills Poison, nothing more." },
		Metal = { m = 0.5, why = "Metal resists Ice: steel shatters brittle ice." },
		Arcane = { m = 1, why = "Ice chills Arcane, nothing more." },
	},
	Lightning = {
		Fire = { m = 1, why = "Lightning hits Fire for normal damage." },
		Water = { m = 1.5, why = "Water conducts every volt." },
		Ice = { m = 1, why = "Lightning hits Ice for normal damage." },
		Lightning = { m = 0.5, why = "A charged target has nowhere to send more charge." },
		Earth = { m = 0.5, why = "Earth resists Lightning: earth grounds the charge harmlessly." },
		Wind = { m = 1.5, why = "Lightning splits open the storm sky." },
		Nature = { m = 0.5, why = "Nature resists Lightning: wood does not conduct; vines absorb the jolt." },
		Light = { m = 1, why = "Lightning hits Light for normal damage." },
		Shadow = { m = 1, why = "Lightning hits Shadow for normal damage." },
		Poison = { m = 1, why = "Lightning hits Poison for normal damage." },
		Metal = { m = 1.5, why = "Metal is a lightning rod." },
		Arcane = { m = 0.5, why = "Arcane resists Lightning: arcane bends raw energy to its will." },
	},
	Earth = {
		Fire = { m = 1.5, why = "Dirt and stone smother flames." },
		Water = { m = 0.5, why = "Water resists Earth: floods erode stone and turn soil to mud." },
		Ice = { m = 1, why = "Stone hits Ice as hard as anything." },
		Lightning = { m = 1.5, why = "Earth grounds the charge harmlessly." },
		Earth = { m = 0.5, why = "Stone meets stone. Very little happens." },
		Wind = { m = 0.5, why = "Wind resists Earth: endless wind erodes rock to sand." },
		Nature = { m = 0.5, why = "Nature resists Earth: roots crack stone apart." },
		Light = { m = 1, why = "Stone hits Light as hard as anything." },
		Shadow = { m = 1, why = "Stone hits Shadow as hard as anything." },
		Poison = { m = 1.5, why = "Soil soaks up and filters toxins." },
		Metal = { m = 1, why = "Ore and stone are old relatives." },
		Arcane = { m = 1, why = "Stone hits Arcane as hard as anything." },
	},
	Wind = {
		Fire = { m = 1, why = "Wind feeds fire as much as it hurts it." },
		Water = { m = 1, why = "Wind buffets Water like anything else." },
		Ice = { m = 0.5, why = "Ice resists Wind: freezing air goes heavy and still." },
		Lightning = { m = 0.5, why = "Lightning resists Wind: lightning splits open the storm sky." },
		Earth = { m = 1.5, why = "Endless wind erodes rock to sand." },
		Wind = { m = 0.5, why = "Wind into wind just makes a breeze." },
		Nature = { m = 1, why = "Wind bends trees, but they bend back." },
		Light = { m = 1, why = "Wind buffets Light like anything else." },
		Shadow = { m = 1.5, why = "Wind tears the shadow veil to shreds." },
		Poison = { m = 1.5, why = "Gales blow toxic clouds away." },
		Metal = { m = 1, why = "Wind buffets Metal like anything else." },
		Arcane = { m = 0.5, why = "Arcane resists Wind: runes bind the air in place." },
	},
	Nature = {
		Fire = { m = 0.5, why = "Fire resists Nature: fire burns through leaves, roots and bark." },
		Water = { m = 1.5, why = "Roots drink the water up." },
		Ice = { m = 0.5, why = "Ice resists Nature: frost kills leaves and stops growth." },
		Lightning = { m = 1.5, why = "Wood does not conduct; vines absorb the jolt." },
		Earth = { m = 1.5, why = "Roots crack stone apart." },
		Wind = { m = 1, why = "Vines and thorns treat Wind like anyone." },
		Nature = { m = 0.5, why = "Plants share; they do not feed on each other." },
		Light = { m = 1, why = "Plants love sunlight; light hits them normally." },
		Shadow = { m = 0.5, why = "Shadow resists Nature: without sun, plants wither." },
		Poison = { m = 0.5, why = "Poison resists Nature: blight rots living things." },
		Metal = { m = 1, why = "Vines and thorns treat Metal like anyone." },
		Arcane = { m = 1, why = "Vines and thorns treat Arcane like anyone." },
	},
	Light = {
		Fire = { m = 1, why = "Light hits Fire with no bonus." },
		Water = { m = 1, why = "Light hits Water with no bonus." },
		Ice = { m = 1.5, why = "Sunlight melts ice." },
		Lightning = { m = 1, why = "Light hits Lightning with no bonus." },
		Earth = { m = 1, why = "Light hits Earth with no bonus." },
		Wind = { m = 1, why = "Light hits Wind with no bonus." },
		Nature = { m = 1, why = "Light feeds plants as much as it hurts them." },
		Light = { m = 0.5, why = "Light passes through light." },
		Shadow = { m = 1.5, why = "Light banishes darkness." },
		Poison = { m = 1.5, why = "Pure light cleanses toxins." },
		Metal = { m = 0.5, why = "Metal resists Light: polished steel throws light back." },
		Arcane = { m = 0.5, why = "Arcane resists Light: arcane twists light into illusions." },
	},
	Shadow = {
		Fire = { m = 1, why = "Shadow strikes Fire without advantage." },
		Water = { m = 1, why = "Shadow strikes Water without advantage." },
		Ice = { m = 1, why = "Shadow strikes Ice without advantage." },
		Lightning = { m = 1, why = "Shadow strikes Lightning without advantage." },
		Earth = { m = 1, why = "Shadow strikes Earth without advantage." },
		Wind = { m = 0.5, why = "Wind resists Shadow: wind tears the shadow veil to shreds." },
		Nature = { m = 1.5, why = "Without sun, plants wither." },
		Light = { m = 1.5, why = "Darkness swallows light: the eternal rivalry." },
		Shadow = { m = 0.5, why = "Shadow hides in shadow." },
		Poison = { m = 1, why = "Shadow strikes Poison without advantage." },
		Metal = { m = 1, why = "Shadow strikes Metal without advantage." },
		Arcane = { m = 1.5, why = "Shadow devours spellwork." },
	},
	Poison = {
		Fire = { m = 1, why = "Poison affects Fire normally." },
		Water = { m = 1.5, why = "Toxins taint the water." },
		Ice = { m = 1, why = "Poison affects Ice normally." },
		Lightning = { m = 1, why = "Poison affects Lightning normally." },
		Earth = { m = 0.5, why = "Earth resists Poison: soil soaks up and filters toxins." },
		Wind = { m = 0.5, why = "Wind resists Poison: gales blow toxic clouds away." },
		Nature = { m = 1.5, why = "Blight rots living things." },
		Light = { m = 0.5, why = "Light resists Poison: pure light cleanses toxins." },
		Shadow = { m = 1, why = "Poison affects Shadow normally." },
		Poison = { m = 0.5, why = "Venomous things are immune to their own venom." },
		Metal = { m = 1.5, why = "Acid corrodes armour." },
		Arcane = { m = 1, why = "Poison affects Arcane normally." },
	},
	Metal = {
		Fire = { m = 0.5, why = "Fire resists Metal: forge heat softens steel and cooks whoever wears it." },
		Water = { m = 1, why = "Steel slices water to no effect, but no harm done either." },
		Ice = { m = 1.5, why = "Steel shatters brittle ice." },
		Lightning = { m = 0.5, why = "Lightning resists Metal: metal is a lightning rod." },
		Earth = { m = 1, why = "A pickaxe works, but stone is stubborn." },
		Wind = { m = 1, why = "A blade cuts Wind as usual." },
		Nature = { m = 1, why = "A blade cuts Nature as usual." },
		Light = { m = 1.5, why = "Polished steel throws light back." },
		Shadow = { m = 1, why = "A blade cuts Shadow as usual." },
		Poison = { m = 0.5, why = "Poison resists Metal: acid corrodes armour." },
		Metal = { m = 0.5, why = "Steel on steel rings, but holds." },
		Arcane = { m = 1.5, why = "Cold iron breaks enchantments." },
	},
	Arcane = {
		Fire = { m = 1, why = "Raw magic hits Fire evenly." },
		Water = { m = 1, why = "Raw magic hits Water evenly." },
		Ice = { m = 1, why = "Raw magic hits Ice evenly." },
		Lightning = { m = 1.5, why = "Arcane bends raw energy to its will." },
		Earth = { m = 1, why = "Raw magic hits Earth evenly." },
		Wind = { m = 1.5, why = "Runes bind the air in place." },
		Nature = { m = 1, why = "Raw magic hits Nature evenly." },
		Light = { m = 1.5, why = "Arcane twists light into illusions." },
		Shadow = { m = 0.5, why = "Shadow resists Arcane: shadow devours spellwork." },
		Poison = { m = 1, why = "Raw magic hits Poison evenly." },
		Metal = { m = 0.5, why = "Metal resists Arcane: cold iron breaks enchantments." },
		Arcane = { m = 0.5, why = "Matching runes cancel each other out." },
	},
}
local REACTIONS = {
	{ id = "Extinguish", elements = { "Fire", "Water" }, name = "Extinguish", description = "Water snuffs the fire in a hissing burst of white vapour; burning targets are put out.", result = "Cancel", statuses = { "Wet" }, hooks = { "CancelsElement", "Cleanses", "BlocksVision" }, magnitudeHint = 0.3, durationHint = 2, vfx = "reaction.extinguish", sfx = "reaction_hiss" },
	{ id = "Steam", elements = { "Fire", "Ice" }, name = "Steam Cloud", description = "Fire flash-melts ice into a scalding cloud that blinds anyone inside.", result = "Zone", statuses = { "Blind" }, hooks = { "BlocksVision", "AreaDamage", "Lingers" }, magnitudeHint = 0.4, durationHint = 6, vfx = "reaction.steam", sfx = "reaction_steam_hiss" },
	{ id = "Plasma", elements = { "Fire", "Lightning" }, name = "Plasma Burst", description = "Superheated plasma detonates and punches through armour.", result = "Burst", statuses = { "Burn", "Shock" }, hooks = { "AreaDamage", "Pierces", "Knockback" }, magnitudeHint = 0.85, durationHint = 1, vfx = "reaction.plasma", sfx = "reaction_plasma_crack" },
	{ id = "Magma", elements = { "Fire", "Earth" }, name = "Magma Pool", description = "The ground melts into a bubbling pool of lava.", result = "Zone", statuses = { "Burn", "Slow" }, hooks = { "GroundHazard", "DamageOverTime", "Lingers" }, magnitudeHint = 0.7, durationHint = 8, vfx = "reaction.magma", sfx = "reaction_lava_bubble" },
	{ id = "Firestorm", elements = { "Fire", "Wind" }, name = "Firestorm", description = "Wind whips the flames into a roaring, wandering fire tornado.", result = "Zone", statuses = { "Burn" }, hooks = { "Spreads", "Moves", "Knockback", "DamageOverTime", "Lifts" }, magnitudeHint = 0.85, durationHint = 7, vfx = "reaction.firestorm", sfx = "reaction_fire_roar" },
	{ id = "Wildfire", elements = { "Fire", "Nature" }, name = "Wildfire", description = "Fire catches on every plant and spreads from target to target.", result = "Zone", statuses = { "Burn" }, hooks = { "Spreads", "DamageOverTime", "GroundHazard" }, magnitudeHint = 0.7, durationHint = 9, vfx = "reaction.wildfire", sfx = "reaction_fire_crackle" },
	{ id = "SolarFlare", elements = { "Fire", "Light" }, name = "Solar Flare", description = "A miniature sun erupts, scorching and dazzling everything nearby.", result = "Burst", statuses = { "Burn", "Blind" }, hooks = { "AreaDamage", "BlocksVision" }, magnitudeHint = 0.8, durationHint = 1.5, vfx = "reaction.solar_flare", sfx = "reaction_flare_whoom" },
	{ id = "Shadowflame", elements = { "Fire", "Shadow" }, name = "Shadowflame", description = "Black fire that slips past shields and clings to its victim.", result = "Status", statuses = { "Burn", "Weaken" }, hooks = { "IgnoresShields", "DamageOverTime" }, magnitudeHint = 0.65, durationHint = 6, vfx = "reaction.shadowflame", sfx = "reaction_dark_flame" },
	{ id = "GasExplosion", elements = { "Fire", "Poison" }, name = "Gas Explosion", description = "Toxic gas meets a spark. Everything nearby is launched.", result = "Burst", statuses = { "Burn", "Poison" }, hooks = { "AreaDamage", "Knockback", "Explodes" }, magnitudeHint = 0.95, durationHint = 1, vfx = "reaction.gas_explosion", sfx = "reaction_boom_big" },
	{ id = "Molten", elements = { "Fire", "Metal" }, name = "Molten Slag", description = "Armour glows red, softens and drips; defences melt away.", result = "Transform", statuses = { "Burn", "Slow" }, hooks = { "ArmorBreak", "DamageOverTime" }, magnitudeHint = 0.7, durationHint = 5, vfx = "reaction.molten", sfx = "reaction_metal_sizzle" },
	{ id = "Spellfire", elements = { "Fire", "Arcane" }, name = "Spellfire", description = "Enchanted flames mark targets; every hit on a marked foe burns brighter.", result = "Buff", statuses = { "Burn" }, hooks = { "BuffDamage", "Marks", "Spreads" }, magnitudeHint = 0.6, durationHint = 8, vfx = "reaction.spellfire", sfx = "reaction_arcane_flame" },
	{ id = "Electrocute", elements = { "Water", "Lightning" }, name = "Electrocute", description = "Lightning races through the water and arcs between every wet target.", result = "Burst", statuses = { "Shock", "Stun", "Wet" }, hooks = { "Chain", "AreaDamage" }, magnitudeHint = 0.8, durationHint = 2, vfx = "reaction.electrocute", sfx = "reaction_zap_chain" },
	{ id = "FlashFreeze", elements = { "Water", "Ice" }, name = "Flash Freeze", description = "Soaked targets freeze solid in an instant.", result = "Status", statuses = { "Freeze" }, hooks = { "Freezes", "Roots" }, magnitudeHint = 0.6, durationHint = 3, vfx = "reaction.flash_freeze", sfx = "reaction_ice_crack" },
	{ id = "Mudslide", elements = { "Water", "Earth" }, name = "Mudslide", description = "A churning river of mud sweeps everything downhill.", result = "Zone", statuses = { "Slow" }, hooks = { "Pushes", "Knockback", "GroundHazard", "Moves" }, magnitudeHint = 0.7, durationHint = 5, vfx = "reaction.mudslide", sfx = "reaction_mud_rumble" },
	{ id = "Typhoon", elements = { "Water", "Wind" }, name = "Typhoon", description = "Sideways rain and screaming wind shove enemies back.", result = "Zone", statuses = { "Wet", "Slow" }, hooks = { "Pushes", "AreaDamage", "BlocksVision", "Moves" }, magnitudeHint = 0.8, durationHint = 7, vfx = "reaction.typhoon", sfx = "reaction_storm_howl" },
	{ id = "Bloom", elements = { "Water", "Nature" }, name = "Bloom", description = "Watered seeds burst into a garden that heals allies and tangles foes.", result = "Buff", statuses = { "Regen" }, hooks = { "Heals", "Grows", "Roots" }, magnitudeHint = 0.5, durationHint = 6, vfx = "reaction.bloom", sfx = "reaction_bloom_chime" },
	{ id = "Abyss", elements = { "Water", "Shadow" }, name = "Abyss", description = "Black water opens a whirlpool that drags victims into the dark.", result = "Zone", statuses = { "Slow", "Blind" }, hooks = { "Pulls", "DamageOverTime", "BlocksVision" }, magnitudeHint = 0.75, durationHint = 6, vfx = "reaction.abyss", sfx = "reaction_deep_gurgle" },
	{ id = "Contamination", elements = { "Water", "Poison" }, name = "Contamination", description = "Toxins spread through the water; every wet target is poisoned.", result = "Zone", statuses = { "Poison", "Wet" }, hooks = { "Spreads", "DamageOverTime", "GroundHazard" }, magnitudeHint = 0.6, durationHint = 8, vfx = "reaction.contamination", sfx = "reaction_toxic_slosh" },
	{ id = "Rust", elements = { "Water", "Metal" }, name = "Rust", description = "Water rusts metal on contact: armour flakes off and joints seize.", result = "Status", statuses = { "Corrode", "Slow" }, hooks = { "ArmorBreak", "Weakens" }, magnitudeHint = 0.55, durationHint = 8, vfx = "reaction.rust", sfx = "reaction_rust_creak" },
	{ id = "Rainbow", elements = { "Water", "Light" }, name = "Rainbow", description = "Sunlight through spray: a rainbow arc speeds allies, and enemies stop to stare.", result = "Buff", statuses = { "Haste", "Charm" }, hooks = { "BuffSpeed", "Charms", "Heals" }, magnitudeHint = 0.55, durationHint = 7, vfx = "reaction.rainbow", sfx = "reaction_rainbow_chime" },
	{ id = "ManaSpring", elements = { "Water", "Arcane" }, name = "Mana Spring", description = "A glowing spring bubbles up, healing and cleansing allies who stand in it.", result = "Buff", statuses = { "Regen" }, hooks = { "Heals", "Cleanses", "Lingers" }, magnitudeHint = 0.5, durationHint = 8, vfx = "reaction.mana_spring", sfx = "reaction_spring_shimmer" },
	{ id = "Superconductor", elements = { "Ice", "Lightning" }, name = "Superconductor", description = "Supercooled lightning arcs further and cracks armour.", result = "Status", statuses = { "Shock", "Slow" }, hooks = { "Chain", "ArmorBreak" }, magnitudeHint = 0.7, durationHint = 4, vfx = "reaction.superconductor", sfx = "reaction_super_hum" },
	{ id = "Permafrost", elements = { "Ice", "Earth" }, name = "Permafrost", description = "The ground freezes solid; feet stick to it.", result = "Zone", statuses = { "Slow", "Root" }, hooks = { "GroundHazard", "Roots", "Lingers" }, magnitudeHint = 0.55, durationHint = 8, vfx = "reaction.permafrost", sfx = "reaction_frost_creep" },
	{ id = "Blizzard", elements = { "Ice", "Wind" }, name = "Blizzard", description = "A howling snowstorm freezes and blinds everything inside.", result = "Zone", statuses = { "Slow", "Freeze", "Blind" }, hooks = { "BlocksVision", "DamageOverTime", "Moves" }, magnitudeHint = 0.8, durationHint = 8, vfx = "reaction.blizzard", sfx = "reaction_blizzard_howl" },
	{ id = "Frostbloom", elements = { "Ice", "Nature" }, name = "Frostbloom", description = "Thorny vines of ice erupt from the ground and pin enemies.", result = "Zone", statuses = { "Root", "Slow" }, hooks = { "Roots", "AreaDamage", "Wall" }, magnitudeHint = 0.6, durationHint = 6, vfx = "reaction.frostbloom", sfx = "reaction_ice_thorns" },
	{ id = "Prism", elements = { "Ice", "Light" }, name = "Prism", description = "A crystal prism splits light into a fan of rainbow beams.", result = "Transform", statuses = { "Blind" }, hooks = { "Splits", "Reflects", "Pierces" }, magnitudeHint = 0.7, durationHint = 5, vfx = "reaction.prism", sfx = "reaction_prism_ring" },
	{ id = "BlackIce", elements = { "Ice", "Shadow" }, name = "Black Ice", description = "An invisible sheet of dark ice. Enemies slip, slide and fall.", result = "Zone", statuses = { "Slow", "Stun" }, hooks = { "GroundHazard", "Invisibility", "Lingers" }, magnitudeHint = 0.5, durationHint = 9, vfx = "reaction.black_ice", sfx = "reaction_ice_slide" },
	{ id = "Cryotoxin", elements = { "Ice", "Poison" }, name = "Cryotoxin", description = "Frozen venom that lasts twice as long and slows the blood.", result = "Status", statuses = { "Poison", "Slow" }, hooks = { "DamageOverTime", "ExtendsStatus" }, magnitudeHint = 0.55, durationHint = 10, vfx = "reaction.cryotoxin", sfx = "reaction_cryo_hiss" },
	{ id = "Shatter", elements = { "Ice", "Metal" }, name = "Shatter", description = "Frozen metal turns brittle and explodes into razor shards.", result = "Burst", statuses = { "Stun" }, hooks = { "ArmorBreak", "AreaDamage", "Splits" }, magnitudeHint = 0.8, durationHint = 1, vfx = "reaction.shatter", sfx = "reaction_glass_shatter" },
	{ id = "Stasis", elements = { "Ice", "Arcane" }, name = "Stasis", description = "Time itself freezes around the target.", result = "Status", statuses = { "Freeze", "Stun" }, hooks = { "Stuns", "Freezes" }, magnitudeHint = 0.7, durationHint = 3, vfx = "reaction.stasis", sfx = "reaction_time_stop" },
	{ id = "Fulgurite", elements = { "Lightning", "Earth" }, name = "Fulgurite", description = "Lightning fuses sand to glass; jagged glass spikes burst out.", result = "Burst", statuses = { "Stun" }, hooks = { "CancelsElement", "AreaDamage", "Splits" }, magnitudeHint = 0.55, durationHint = 1, vfx = "reaction.fulgurite", sfx = "reaction_glass_crack" },
	{ id = "Thunderstorm", elements = { "Lightning", "Wind" }, name = "Thunderstorm", description = "A dark storm cloud rolls in and strikes at random.", result = "Zone", statuses = { "Shock" }, hooks = { "RandomStrikes", "AreaDamage", "Moves", "Lingers" }, magnitudeHint = 0.85, durationHint = 8, vfx = "reaction.thunderstorm", sfx = "reaction_thunder_roll" },
	{ id = "Sparkbloom", elements = { "Lightning", "Nature" }, name = "Sparkbloom", description = "Charged pollen pops in a crackling chain.", result = "Burst", statuses = { "Shock", "Confuse" }, hooks = { "Chain", "Spreads" }, magnitudeHint = 0.6, durationHint = 3, vfx = "reaction.sparkbloom", sfx = "reaction_spark_pop" },
	{ id = "Flashbang", elements = { "Lightning", "Light" }, name = "Flashbang", description = "A blinding flash and a deafening crack.", result = "Burst", statuses = { "Blind", "Stun" }, hooks = { "BlocksVision", "Stuns" }, magnitudeHint = 0.6, durationHint = 2, vfx = "reaction.flashbang", sfx = "reaction_flashbang" },
	{ id = "BlackLightning", elements = { "Lightning", "Shadow" }, name = "Black Lightning", description = "Dark lightning ignores shields and jumps between foes.", result = "Burst", statuses = { "Shock" }, hooks = { "Pierces", "IgnoresShields", "Chain" }, magnitudeHint = 0.85, durationHint = 1, vfx = "reaction.black_lightning", sfx = "reaction_dark_zap" },
	{ id = "Neurotoxin", elements = { "Lightning", "Poison" }, name = "Neurotoxin", description = "Electric venom locks up muscles in twitching jolts.", result = "Status", statuses = { "Poison", "Stun" }, hooks = { "Stuns", "DamageOverTime" }, magnitudeHint = 0.65, durationHint = 5, vfx = "reaction.neurotoxin", sfx = "reaction_neuro_buzz" },
	{ id = "MagneticStorm", elements = { "Lightning", "Metal" }, name = "Magnetic Storm", description = "Raw magnetism rips metal objects into the air and fries them.", result = "Zone", statuses = { "Shock", "Stun" }, hooks = { "Pulls", "Chain", "Lifts", "Disarms" }, magnitudeHint = 0.85, durationHint = 6, vfx = "reaction.magnetic_storm", sfx = "reaction_magnet_hum" },
	{ id = "LeylineSurge", elements = { "Lightning", "Arcane" }, name = "Leyline Surge", description = "Lightning rides the ley lines and arcs to every marked enemy.", result = "Burst", statuses = { "Shock" }, hooks = { "Chain", "Marks", "BuffDamage" }, magnitudeHint = 0.8, durationHint = 2, vfx = "reaction.leyline_surge", sfx = "reaction_ley_surge" },
	{ id = "Sandstorm", elements = { "Earth", "Wind" }, name = "Sandstorm", description = "Stinging sand blots out the sky.", result = "Zone", statuses = { "Blind", "Slow" }, hooks = { "BlocksVision", "DamageOverTime", "Moves" }, magnitudeHint = 0.65, durationHint = 8, vfx = "reaction.sandstorm", sfx = "reaction_sand_hiss" },
	{ id = "Thornwall", elements = { "Earth", "Nature" }, name = "Thornwall", description = "A wall of thorny roots heaves out of the ground.", result = "Zone", statuses = { "Root" }, hooks = { "Wall", "Roots", "AreaDamage", "Blocks" }, magnitudeHint = 0.6, durationHint = 10, vfx = "reaction.thornwall", sfx = "reaction_thorn_rise" },
	{ id = "Crystallize", elements = { "Earth", "Light" }, name = "Crystallize", description = "Glowing crystals grow over allies like armour.", result = "Buff", statuses = { "Shielded" }, hooks = { "Shields", "Reflects" }, magnitudeHint = 0.6, durationHint = 8, vfx = "reaction.crystallize", sfx = "reaction_crystal_ring" },
	{ id = "Sinkhole", elements = { "Earth", "Shadow" }, name = "Sinkhole", description = "The ground opens into a dark pit that swallows the unwary.", result = "Zone", statuses = { "Root", "Slow" }, hooks = { "Pulls", "GroundHazard", "Roots" }, magnitudeHint = 0.7, durationHint = 6, vfx = "reaction.sinkhole", sfx = "reaction_sink_rumble" },
	{ id = "Blight", elements = { "Earth", "Poison" }, name = "Blight", description = "The soil turns toxic and rotten; nothing stands on it for long.", result = "Zone", statuses = { "Poison", "Weaken" }, hooks = { "GroundHazard", "DamageOverTime", "Spreads", "Lingers" }, magnitudeHint = 0.6, durationHint = 10, vfx = "reaction.blight", sfx = "reaction_blight_bubble" },
	{ id = "IronSpikes", elements = { "Earth", "Metal" }, name = "Iron Spikes", description = "Iron spikes burst up from the ground like a bed of nails.", result = "Burst", statuses = { "Slow" }, hooks = { "AreaDamage", "Pierces", "Lifts", "Wall" }, magnitudeHint = 0.8, durationHint = 4, vfx = "reaction.iron_spikes", sfx = "reaction_spike_burst" },
	{ id = "Runequake", elements = { "Earth", "Arcane" }, name = "Runequake", description = "Runes crack the ground and a stone golem pulls itself out.", result = "Transform", statuses = { "Stun" }, hooks = { "Summons", "AreaDamage", "Knockback" }, magnitudeHint = 0.8, durationHint = 8, vfx = "reaction.runequake", sfx = "reaction_golem_rise" },
	{ id = "PollenStorm", elements = { "Wind", "Nature" }, name = "Pollen Storm", description = "A golden swirl of pollen leaves enemies dizzy and dreamy.", result = "Zone", statuses = { "Charm", "Confuse" }, hooks = { "Charms", "Confuses", "Spreads", "Moves" }, magnitudeHint = 0.55, durationHint = 6, vfx = "reaction.pollen_storm", sfx = "reaction_pollen_swirl" },
	{ id = "Aurora", elements = { "Wind", "Light" }, name = "Aurora", description = "Ribbons of shimmering light quicken and heal allies.", result = "Buff", statuses = { "Haste", "Regen" }, hooks = { "BuffSpeed", "Heals", "Lingers" }, magnitudeHint = 0.55, durationHint = 8, vfx = "reaction.aurora", sfx = "reaction_aurora_chime" },
	{ id = "Nightwind", elements = { "Wind", "Shadow" }, name = "Nightwind", description = "A dark breeze hides allies and confuses enemy sight.", result = "Buff", statuses = { "Blind" }, hooks = { "Invisibility", "BuffSpeed", "BlocksVision" }, magnitudeHint = 0.55, durationHint = 6, vfx = "reaction.nightwind", sfx = "reaction_night_whisper" },
	{ id = "ToxicCloud", elements = { "Wind", "Poison" }, name = "Toxic Cloud", description = "Wind carries a sickly green cloud across the battlefield.", result = "Zone", statuses = { "Poison" }, hooks = { "Spreads", "DamageOverTime", "Moves", "Lingers" }, magnitudeHint = 0.65, durationHint = 9, vfx = "reaction.toxic_cloud", sfx = "reaction_gas_hiss" },
	{ id = "Bladestorm", elements = { "Wind", "Metal" }, name = "Bladestorm", description = "A whirlwind full of spinning steel blades.", result = "Zone", statuses = { "Slow" }, hooks = { "AreaDamage", "Pierces", "Moves", "Knockback" }, magnitudeHint = 0.8, durationHint = 5, vfx = "reaction.bladestorm", sfx = "reaction_blade_whirl" },
	{ id = "WarpGale", elements = { "Wind", "Arcane" }, name = "Warp Gale", description = "A gust folds space and throws enemies somewhere else.", result = "Burst", statuses = { "Confuse" }, hooks = { "Teleports", "Knockback", "Confuses" }, magnitudeHint = 0.6, durationHint = 2, vfx = "reaction.warp_gale", sfx = "reaction_warp_whoosh" },
	{ id = "Sunbloom", elements = { "Nature", "Light" }, name = "Sunbloom", description = "Flowers open in the sunlight and heal everyone nearby.", result = "Buff", statuses = { "Regen" }, hooks = { "Heals", "Grows", "Cleanses" }, magnitudeHint = 0.6, durationHint = 8, vfx = "reaction.sunbloom", sfx = "reaction_sunbloom_chime" },
	{ id = "Wither", elements = { "Nature", "Shadow" }, name = "Wither", description = "Life is drained out of the target and into the caster.", result = "Status", statuses = { "Weaken", "Slow" }, hooks = { "Drains", "Weakens" }, magnitudeHint = 0.6, durationHint = 6, vfx = "reaction.wither", sfx = "reaction_wither_creak" },
	{ id = "Spores", elements = { "Nature", "Poison" }, name = "Spore Burst", description = "Giant mushrooms burst and fill the air with dizzy spores.", result = "Zone", statuses = { "Poison", "Confuse" }, hooks = { "Spreads", "DamageOverTime", "Confuses" }, magnitudeHint = 0.6, durationHint = 7, vfx = "reaction.spores", sfx = "reaction_spore_puff" },
	{ id = "Ironbark", elements = { "Nature", "Metal" }, name = "Ironbark", description = "Steel-hard bark grows over allies and walls.", result = "Buff", statuses = { "Shielded" }, hooks = { "Shields", "Blocks" }, magnitudeHint = 0.6, durationHint = 10, vfx = "reaction.ironbark", sfx = "reaction_bark_creak" },
	{ id = "FeyRing", elements = { "Nature", "Arcane" }, name = "Fey Ring", description = "A ring of glowing mushrooms charms anyone who steps inside.", result = "Zone", statuses = { "Charm" }, hooks = { "Charms", "Teleports", "Lingers" }, magnitudeHint = 0.6, durationHint = 7, vfx = "reaction.fey_ring", sfx = "reaction_fey_bells" },
	{ id = "Eclipse", elements = { "Light", "Shadow" }, name = "Eclipse", description = "Light and shadow collide: the sky goes dark with a burning ring.", result = "Zone", statuses = { "Blind" }, hooks = { "BlocksVision", "CancelsBuffs", "AreaDamage" }, magnitudeHint = 0.9, durationHint = 6, vfx = "reaction.eclipse", sfx = "reaction_eclipse_drone" },
	{ id = "Purify", elements = { "Light", "Poison" }, name = "Purify", description = "A cleansing flash burns toxins away and heals allies.", result = "Cancel", statuses = { "Regen" }, hooks = { "Cleanses", "CancelsElement", "Heals" }, magnitudeHint = 0.5, durationHint = 2, vfx = "reaction.purify", sfx = "reaction_purify_chime" },
	{ id = "Mirror", elements = { "Light", "Metal" }, name = "Mirror Shield", description = "A mirrored barrier bounces projectiles back at their source.", result = "Buff", statuses = { "Shielded" }, hooks = { "Reflects", "Shields" }, magnitudeHint = 0.65, durationHint = 6, vfx = "reaction.mirror", sfx = "reaction_mirror_ring" },
	{ id = "Starfall", elements = { "Light", "Arcane" }, name = "Starfall", description = "Shooting stars rain from the sky onto the target area.", result = "Zone", statuses = { "Stun" }, hooks = { "RandomStrikes", "AreaDamage", "Lingers" }, magnitudeHint = 0.9, durationHint = 6, vfx = "reaction.starfall", sfx = "reaction_starfall_whistle" },
	{ id = "Plague", elements = { "Shadow", "Poison" }, name = "Plague", description = "A creeping curse that jumps from victim to victim.", result = "Status", statuses = { "Poison", "Weaken" }, hooks = { "Spreads", "DamageOverTime", "Weakens" }, magnitudeHint = 0.7, durationHint = 10, vfx = "reaction.plague", sfx = "reaction_plague_whisper" },
	{ id = "PhantomBlades", elements = { "Shadow", "Metal" }, name = "Phantom Blades", description = "Ghostly swords slice through walls and shields.", result = "Burst", statuses = { "Weaken" }, hooks = { "Pierces", "IgnoresShields", "Splits" }, magnitudeHint = 0.75, durationHint = 2, vfx = "reaction.phantom_blades", sfx = "reaction_blade_phantom" },
	{ id = "Void", elements = { "Shadow", "Arcane" }, name = "Void", description = "A black hole tears open and drags everything into it.", result = "Zone", statuses = { "Slow", "Stun" }, hooks = { "Pulls", "Lifts", "DamageOverTime", "AreaDamage" }, magnitudeHint = 1, durationHint = 5, vfx = "reaction.void", sfx = "reaction_void_hum" },
	{ id = "Corrosion", elements = { "Poison", "Metal" }, name = "Corrosion", description = "Acid eats through armour and machinery.", result = "Status", statuses = { "Corrode", "Poison" }, hooks = { "ArmorBreak", "DamageOverTime" }, magnitudeHint = 0.65, durationHint = 8, vfx = "reaction.corrosion", sfx = "reaction_acid_sizzle" },
	{ id = "Hex", elements = { "Poison", "Arcane" }, name = "Hex", description = "A green curse that saps strength and scrambles spells.", result = "Status", statuses = { "Weaken", "Confuse", "Silence" }, hooks = { "Weakens", "Confuses", "Silences" }, magnitudeHint = 0.6, durationHint = 6, vfx = "reaction.hex", sfx = "reaction_hex_whisper" },
	{ id = "Enchant", elements = { "Metal", "Arcane" }, name = "Enchanted Steel", description = "Runes flare along every weapon: hits deal extra damage and flying blades guard you.", result = "Buff", statuses = { "Shielded" }, hooks = { "BuffDamage", "Shields", "Summons" }, magnitudeHint = 0.65, durationHint = 10, vfx = "reaction.enchant", sfx = "reaction_enchant_ring" },
	{ id = "Inferno", elements = { "Fire", "Fire" }, name = "Inferno", description = "Fire on fire: a towering blaze that engulfs the whole area.", result = "Zone", statuses = { "Burn" }, hooks = { "Amplify", "AreaDamage", "DamageOverTime", "Spreads" }, magnitudeHint = 1, durationHint = 6, vfx = "reaction.inferno", sfx = "reaction_inferno_roar" },
	{ id = "Tsunami", elements = { "Water", "Water" }, name = "Tsunami", description = "A wall of water crashes down and sweeps the field clean.", result = "Burst", statuses = { "Wet", "Slow" }, hooks = { "Amplify", "Pushes", "Knockback", "AreaDamage" }, magnitudeHint = 1, durationHint = 3, vfx = "reaction.tsunami", sfx = "reaction_wave_crash" },
	{ id = "AbsoluteZero", elements = { "Ice", "Ice" }, name = "Absolute Zero", description = "Cold beyond cold; everything nearby freezes in place.", result = "Status", statuses = { "Freeze", "Stun" }, hooks = { "Amplify", "Freezes", "AreaDamage" }, magnitudeHint = 1, durationHint = 4, vfx = "reaction.absolute_zero", sfx = "reaction_deep_freeze" },
	{ id = "Overcharge", elements = { "Lightning", "Lightning" }, name = "Overcharge", description = "Stacked charge discharges in a branching storm of bolts.", result = "Burst", statuses = { "Shock", "Stun" }, hooks = { "Amplify", "Chain", "AreaDamage" }, magnitudeHint = 1, durationHint = 2, vfx = "reaction.overcharge", sfx = "reaction_overcharge_crack" },
	{ id = "Earthquake", elements = { "Earth", "Earth" }, name = "Earthquake", description = "The ground splits open and heaves enemies into the air.", result = "Burst", statuses = { "Stun", "Slow" }, hooks = { "Amplify", "AreaDamage", "Knockback", "Lifts" }, magnitudeHint = 1, durationHint = 3, vfx = "reaction.earthquake", sfx = "reaction_quake_rumble" },
	{ id = "Tornado", elements = { "Wind", "Wind" }, name = "Tornado", description = "Wind stacks into a full tornado that lifts and flings everything.", result = "Zone", statuses = { "Slow" }, hooks = { "Amplify", "Lifts", "Pulls", "Knockback", "Moves" }, magnitudeHint = 1, durationHint = 7, vfx = "reaction.tornado", sfx = "reaction_tornado_howl" },
	{ id = "Overgrowth", elements = { "Nature", "Nature" }, name = "Overgrowth", description = "The battlefield bursts into jungle: roots grab enemies and allies regrow.", result = "Zone", statuses = { "Root", "Regen" }, hooks = { "Amplify", "Roots", "Heals", "Grows" }, magnitudeHint = 1, durationHint = 10, vfx = "reaction.overgrowth", sfx = "reaction_overgrowth_rustle" },
	{ id = "Supernova", elements = { "Light", "Light" }, name = "Supernova", description = "Light collapses into a star and explodes in a white-hot nova.", result = "Burst", statuses = { "Blind", "Burn" }, hooks = { "Amplify", "AreaDamage", "Knockback", "BlocksVision" }, magnitudeHint = 1, durationHint = 2, vfx = "reaction.supernova", sfx = "reaction_supernova_whoom" },
	{ id = "Blackout", elements = { "Shadow", "Shadow" }, name = "Blackout", description = "All light dies. Enemies stumble in total darkness.", result = "Zone", statuses = { "Blind", "Weaken" }, hooks = { "Amplify", "BlocksVision", "Invisibility", "Drains" }, magnitudeHint = 1, durationHint = 7, vfx = "reaction.blackout", sfx = "reaction_blackout_drone" },
	{ id = "Pandemic", elements = { "Poison", "Poison" }, name = "Pandemic", description = "Stacked toxins become a plague that spreads on its own.", result = "Status", statuses = { "Poison", "Weaken" }, hooks = { "Amplify", "Spreads", "DamageOverTime", "ExtendsStatus" }, magnitudeHint = 1, durationHint = 12, vfx = "reaction.pandemic", sfx = "reaction_pandemic_bubble" },
	{ id = "Fortress", elements = { "Metal", "Metal" }, name = "Fortress", description = "Steel plates slam together into a fortified bastion.", result = "Buff", statuses = { "Shielded" }, hooks = { "Amplify", "Shields", "Wall", "Blocks", "Reflects" }, magnitudeHint = 1, durationHint = 10, vfx = "reaction.fortress", sfx = "reaction_fortress_clang" },
	{ id = "ArcaneOverload", elements = { "Arcane", "Arcane" }, name = "Arcane Overload", description = "Too much magic in one place. It detonates in a storm of runes.", result = "Burst", statuses = { "Stun", "Silence" }, hooks = { "Amplify", "AreaDamage", "Silences", "Knockback" }, magnitudeHint = 1, durationHint = 2, vfx = "reaction.arcane_overload", sfx = "reaction_overload_whine" },
}
local MATERIAL_OUTCOMES = {
	Bake = { name = "Bakes Hard", description = "Bakes solid: tougher than before.", statuses = {}, hooks = { "Hardens", "Durable" }, magnitudeHint = 0.4, durationHint = 6, vfx = "mat.bake", sfx = "mat_bake", transform = { colour = "#B8743A" } },
	Conduct = { name = "Conducts", description = "Electricity races through it and jumps to anything nearby.", statuses = { "Shock" }, hooks = { "Chain", "AreaDamage", "Conductive" }, magnitudeHint = 0.7, durationHint = 2, vfx = "mat.conduct", sfx = "mat_conduct" },
	Cook = { name = "Cooks", description = "Sizzles and smells delicious; enemies are drawn to it.", statuses = {}, hooks = { "EdibleLure", "Lures" }, magnitudeHint = 0.4, durationHint = 6, vfx = "mat.cook", sfx = "mat_sizzle", transform = { colour = "#A0522D" } },
	Cool = { name = "Cools to Stone", description = "Hisses and hardens into rock.", statuses = {}, hooks = { "CancelsElement", "Hardens" }, magnitudeHint = 0.5, durationHint = 3, vfx = "mat.cool", sfx = "mat_hiss", transform = { material = "obsidian" } },
	Corrode = { name = "Corrodes", description = "Acid eats through it.", statuses = { "Corrode", "Poison" }, hooks = { "ArmorBreak", "DamageOverTime" }, magnitudeHint = 0.6, durationHint = 6, vfx = "mat.corrode", sfx = "mat_acid" },
	Crack = { name = "Cracks Apart", description = "Splits open and crumbles.", statuses = {}, hooks = { "ArmorBreak", "Grows" }, magnitudeHint = 0.5, durationHint = 3, vfx = "mat.crack", sfx = "mat_crack" },
	Decay = { name = "Rots", description = "Rots and crumbles.", statuses = { "Weaken" }, hooks = { "Weakens", "DamageOverTime" }, magnitudeHint = 0.5, durationHint = 6, vfx = "mat.decay", sfx = "mat_decay", transform = { colour = "#5A6B3A" } },
	Dissolve = { name = "Dissolves", description = "Fizzes and dissolves away.", statuses = {}, hooks = { "Shrinks", "DamageOverTime" }, magnitudeHint = 0.6, durationHint = 4, vfx = "mat.dissolve", sfx = "mat_fizz" },
	Drift = { name = "Drifts Away", description = "Catches the wind and floats off.", statuses = {}, hooks = { "Lifts", "Flies" }, magnitudeHint = 0.4, durationHint = 3, vfx = "mat.drift", sfx = "mat_drift" },
	Empower = { name = "Empowered", description = "Hums with magic; its effects grow stronger.", statuses = {}, hooks = { "BuffDamage" }, magnitudeHint = 0.5, durationHint = 6, vfx = "mat.empower", sfx = "mat_empower" },
	Evaporate = { name = "Evaporates", description = "Boils away into steam.", statuses = {}, hooks = { "Shrinks", "BlocksVision" }, magnitudeHint = 0.5, durationHint = 3, vfx = "mat.evaporate", sfx = "mat_evaporate" },
	Explode = { name = "Explodes", description = "Goes off like a bomb.", statuses = { "Burn" }, hooks = { "Explodes", "AreaDamage", "Knockback" }, magnitudeHint = 1, durationHint = 1, vfx = "mat.explode", sfx = "mat_boom" },
	Freeze = { name = "Freezes Solid", description = "Freezes solid and turns brittle.", statuses = { "Freeze" }, hooks = { "Freezes", "ShattersOnHit" }, magnitudeHint = 0.6, durationHint = 4, vfx = "mat.freeze", sfx = "mat_freeze", transform = { colour = "#BDEBFF" } },
	Fuse = { name = "Fuses to Glass", description = "Melts into gleaming glass.", statuses = {}, hooks = { "Hardens", "Transform" }, magnitudeHint = 0.5, durationHint = 3, vfx = "mat.fuse", sfx = "mat_fuse", transform = { material = "glass" } },
	Gleam = { name = "Gleams", description = "Flashes blinding reflections.", statuses = { "Blind" }, hooks = { "Reflects", "BlocksVision" }, magnitudeHint = 0.4, durationHint = 3, vfx = "mat.gleam", sfx = "mat_gleam" },
	Grow = { name = "Grows", description = "Sprouts, swells and regrows.", statuses = { "Regen" }, hooks = { "Grows", "Heals" }, magnitudeHint = 0.5, durationHint = 6, vfx = "mat.grow", sfx = "mat_grow" },
	Heat = { name = "Red-Hot", description = "Glows red-hot and burns whatever touches it.", statuses = { "Burn" }, hooks = { "DamageAura", "Burns" }, magnitudeHint = 0.6, durationHint = 6, vfx = "mat.heat", sfx = "mat_heat", transform = { colour = "#FF4A1C" } },
	Ignite = { name = "Ignites", description = "Catches fire and burns fast.", statuses = { "Burn" }, hooks = { "BurnsFast", "Spreads", "DamageOverTime" }, magnitudeHint = 0.7, durationHint = 5, vfx = "mat.ignite", sfx = "mat_ignite", transform = { colour = "#3A3330", material = "ash" } },
	Melt = { name = "Melts", description = "Softens, sags and drips into a puddle.", statuses = { "Slow" }, hooks = { "Melts", "Slows", "GroundHazard" }, magnitudeHint = 0.6, durationHint = 4, vfx = "mat.melt", sfx = "mat_melt", transform = { construction = "Liquid" } },
	Mud = { name = "Turns to Mud", description = "Becomes a sticky mud puddle.", statuses = { "Slow" }, hooks = { "GroundHazard", "Slows" }, magnitudeHint = 0.5, durationHint = 6, vfx = "mat.mud", sfx = "mat_mud", transform = { material = "mud" } },
	Pop = { name = "Pops", description = "Bursts with a bang.", statuses = {}, hooks = { "Explodes", "Knockback" }, magnitudeHint = 0.5, durationHint = 1, vfx = "mat.pop", sfx = "mat_pop" },
	Purify = { name = "Purified", description = "Cleansed of curses and toxins.", statuses = { "Regen" }, hooks = { "Cleanses", "Heals" }, magnitudeHint = 0.5, durationHint = 3, vfx = "mat.purify", sfx = "mat_purify" },
	Rust = { name = "Rusts", description = "Rusts and seizes up.", statuses = { "Corrode" }, hooks = { "ArmorBreak", "Slows" }, magnitudeHint = 0.5, durationHint = 8, vfx = "mat.rust", sfx = "mat_rust", transform = { colour = "#B5562A" } },
	Scatter = { name = "Scatters", description = "Gets blown everywhere.", statuses = {}, hooks = { "Knockback", "Pushes", "Splits" }, magnitudeHint = 0.4, durationHint = 2, vfx = "mat.scatter", sfx = "mat_scatter" },
	Shatter = { name = "Shatters", description = "Shatters into sharp pieces.", statuses = {}, hooks = { "Splits", "AreaDamage", "Pierces" }, magnitudeHint = 0.7, durationHint = 1, vfx = "mat.shatter", sfx = "mat_shatter" },
	ShortCircuit = { name = "Short-Circuits", description = "Sparks, smokes and shuts down for a moment.", statuses = { "Stun", "Shock" }, hooks = { "Stuns", "Disarms" }, magnitudeHint = 0.6, durationHint = 3, vfx = "mat.short", sfx = "mat_short" },
	Shred = { name = "Shredded", description = "Sliced into ribbons.", statuses = {}, hooks = { "Splits", "ArmorBreak" }, magnitudeHint = 0.5, durationHint = 2, vfx = "mat.shred", sfx = "mat_shred" },
	Soggy = { name = "Goes Soggy", description = "Soaks through and goes floppy.", statuses = { "Wet", "Slow" }, hooks = { "Weakens", "Slows" }, magnitudeHint = 0.5, durationHint = 6, vfx = "mat.soggy", sfx = "mat_soggy", transform = { colour = "#8A7A5A" } },
	Spoil = { name = "Spoils", description = "Goes green and stinky; nobody wants it now.", statuses = { "Poison" }, hooks = { "Poisons", "Weakens" }, magnitudeHint = 0.5, durationHint = 6, vfx = "mat.spoil", sfx = "mat_spoil", transform = { colour = "#7A9A3A" } },
	Transmute = { name = "Turns to Gold", description = "Transmuted into solid gold. Heavy, shiny, very slow.", statuses = {}, hooks = { "Transform", "Durable", "Slows" }, magnitudeHint = 0.6, durationHint = 8, vfx = "mat.transmute", sfx = "mat_transmute", transform = { colour = "#FFD54A", material = "gold" } },
	Wilt = { name = "Wilts", description = "Wilts and weakens.", statuses = { "Weaken" }, hooks = { "Weakens", "Shrinks" }, magnitudeHint = 0.5, durationHint = 6, vfx = "mat.wilt", sfx = "mat_wilt" },
}
local MATERIAL_RULES = {
	{ element = "Fire", tags = { "explosive" }, outcome = "Explode" },
	{ element = "Fire", tags = { "inflated" }, outcome = "Pop" },
	{ element = "Fire", tags = { "frozen", "meltable", "plastic", "rubber", "wax" }, outcome = "Melt" },
	{ element = "Fire", tags = { "flammable", "wood", "paper", "cloth", "plant", "straw" }, outcome = "Ignite" },
	{ element = "Fire", tags = { "clay", "dough" }, outcome = "Bake" },
	{ element = "Fire", tags = { "edible" }, outcome = "Cook" },
	{ element = "Fire", tags = { "liquid", "cold" }, outcome = "Evaporate" },
	{ element = "Fire", tags = { "metal", "conductive" }, outcome = "Heat" },
	{ element = "Fire", tags = { "electronic" }, outcome = "ShortCircuit" },
	{ element = "Water", tags = { "hot", "lava" }, outcome = "Cool" },
	{ element = "Water", tags = { "electronic" }, outcome = "ShortCircuit" },
	{ element = "Water", tags = { "soluble", "sweet", "powder" }, outcome = "Dissolve" },
	{ element = "Water", tags = { "absorbent", "paper", "cloth", "dough" }, outcome = "Soggy" },
	{ element = "Water", tags = { "soil", "sand", "clay" }, outcome = "Mud" },
	{ element = "Water", tags = { "metal" }, outcome = "Rust" },
	{ element = "Water", tags = { "plant", "living", "organic" }, outcome = "Grow" },
	{ element = "Ice", tags = { "hot", "lava" }, outcome = "Cool" },
	{ element = "Ice", tags = { "plant" }, outcome = "Wilt" },
	{ element = "Ice", tags = { "liquid", "sticky", "rubber", "edible", "brittle", "glass", "living", "organic", "soft", "bouncy" }, outcome = "Freeze" },
	{ element = "Ice", tags = { "stone", "brick", "hard" }, outcome = "Crack" },
	{ element = "Lightning", tags = { "electronic" }, outcome = "ShortCircuit" },
	{ element = "Lightning", tags = { "explosive" }, outcome = "Explode" },
	{ element = "Lightning", tags = { "inflated" }, outcome = "Pop" },
	{ element = "Lightning", tags = { "conductive", "metal", "liquid" }, outcome = "Conduct" },
	{ element = "Lightning", tags = { "sand", "glass" }, outcome = "Fuse" },
	{ element = "Lightning", tags = { "flammable", "wood", "paper", "straw" }, outcome = "Ignite" },
	{ element = "Earth", tags = { "liquid" }, outcome = "Mud" },
	{ element = "Earth", tags = { "brittle", "glass", "crystal" }, outcome = "Shatter" },
	{ element = "Earth", tags = { "inflated" }, outcome = "Pop" },
	{ element = "Earth", tags = { "plant" }, outcome = "Grow" },
	{ element = "Wind", tags = { "inflated" }, outcome = "Drift" },
	{ element = "Wind", tags = { "light", "paper", "powder", "feather", "leaf", "sand", "smoke", "fluffy" }, outcome = "Scatter" },
	{ element = "Wind", tags = { "flammable" }, outcome = "Ignite" },
	{ element = "Nature", tags = { "wood", "soil", "plant", "organic", "living" }, outcome = "Grow" },
	{ element = "Nature", tags = { "stone", "brick" }, outcome = "Crack" },
	{ element = "Light", tags = { "cursed", "toxic", "undead" }, outcome = "Purify" },
	{ element = "Light", tags = { "frozen" }, outcome = "Melt" },
	{ element = "Light", tags = { "shiny", "glass", "crystal", "metal" }, outcome = "Gleam" },
	{ element = "Light", tags = { "glowing", "magic", "holy" }, outcome = "Empower" },
	{ element = "Shadow", tags = { "holy" }, outcome = "Purify" },
	{ element = "Shadow", tags = { "edible", "organic", "plant", "living" }, outcome = "Decay" },
	{ element = "Poison", tags = { "metal", "conductive" }, outcome = "Corrode" },
	{ element = "Poison", tags = { "edible" }, outcome = "Spoil" },
	{ element = "Poison", tags = { "plant", "living", "organic" }, outcome = "Wilt" },
	{ element = "Poison", tags = { "plastic", "cloth", "rubber" }, outcome = "Dissolve" },
	{ element = "Metal", tags = { "inflated" }, outcome = "Pop" },
	{ element = "Metal", tags = { "brittle", "glass", "crystal", "frozen" }, outcome = "Shatter" },
	{ element = "Metal", tags = { "cloth", "paper", "rope", "strands", "wood" }, outcome = "Shred" },
	{ element = "Metal", tags = { "stone", "brick", "hard", "heavy" }, outcome = "Crack" },
	{ element = "Arcane", tags = { "magical", "magic", "glowing" }, outcome = "Empower" },
	{ element = "Arcane", tags = { "metal" }, outcome = "Transmute" },
	{ element = "Arcane", tags = { "cursed" }, outcome = "Purify" },
}
local MATERIAL_OVERRIDES = {
	["balloon"] = { Fire = "Pop", Metal = "Pop", Wind = "Drift" },
	["bread"] = { Fire = "Cook", Water = "Soggy" },
	["butter"] = { Fire = "Melt" },
	["candy"] = { Fire = "Melt", Water = "Dissolve" },
	["cardboard"] = { Fire = "Ignite", Water = "Soggy" },
	["cheese"] = { Fire = "Melt", Light = "Melt" },
	["chocolate"] = { Fire = "Melt", Light = "Melt" },
	["clay"] = { Fire = "Bake", Water = "Mud" },
	["crystal"] = { Light = "Gleam", Metal = "Shatter" },
	["glass"] = { Earth = "Shatter", Metal = "Shatter" },
	["gold"] = { Arcane = "Empower", Light = "Gleam" },
	["ice"] = { Fire = "Melt", Light = "Melt", Lightning = "Conduct", Metal = "Shatter" },
	["ice cream"] = { Fire = "Melt", Light = "Melt" },
	["iron"] = { Lightning = "Conduct", Water = "Rust" },
	["jelly"] = { Fire = "Melt", Ice = "Freeze" },
	["lava"] = { Ice = "Cool", Water = "Cool" },
	["marshmallow"] = { Fire = "Cook" },
	["paper"] = { Fire = "Ignite", Water = "Soggy" },
	["pixels"] = { Arcane = "Empower", Lightning = "ShortCircuit" },
	["play dough"] = { Fire = "Bake", Water = "Soggy" },
	["popcorn"] = { Fire = "Pop" },
	["sand"] = { Lightning = "Fuse", Water = "Mud", Wind = "Scatter" },
	["slime"] = { Fire = "Evaporate", Ice = "Freeze" },
	["smoke"] = { Water = "Dissolve" },
	["snow"] = { Fire = "Melt", Light = "Melt" },
	["soap"] = { Water = "Dissolve" },
	["spaghetti"] = { Fire = "Cook", Water = "Soggy" },
	["steel"] = { Lightning = "Conduct", Water = "Rust" },
	["sugar"] = { Water = "Dissolve" },
	["water"] = { Earth = "Mud", Fire = "Evaporate", Ice = "Freeze", Lightning = "Conduct" },
	["wax"] = { Fire = "Melt" },
	["wood"] = { Fire = "Ignite", Nature = "Grow" },
}
-- END GENERATED DATA

Reactions.Elements = table.freeze(table.clone(ELEMENTS)) :: { Element }

local elementIndex: { [string]: number } = {}
for i, e in ELEMENTS do
	elementIndex[e] = i
end

local function pairKey(a: string, b: string): string
	local ia, ib = elementIndex[a], elementIndex[b]
	if ia and ib and ib < ia then
		a, b = b, a
	end
	return a .. "+" .. b
end

local byPair: { [string]: Reaction } = {}
local byId: { [string]: Reaction } = {}
local byIdLower: { [string]: Reaction } = {}
local byElement: { [string]: { Reaction } } = {}
local all: { Reaction } = {}

for _, raw in REACTIONS do
	local r: any = table.clone(raw)
	r.elements = table.freeze(table.clone(raw.elements))
	r.statuses = table.freeze(table.clone(raw.statuses))
	r.hooks = table.freeze(table.clone(raw.hooks))
	table.freeze(r)
	table.insert(all, r)
	byId[r.id] = r
	byIdLower[string.lower(r.id)] = r
	byPair[pairKey(r.elements[1], r.elements[2])] = r
	local seen = {}
	for _, e in r.elements do
		if not seen[e] then
			seen[e] = true
			byElement[e] = byElement[e] or {}
			table.insert(byElement[e], r)
		end
	end
end
table.freeze(all)
for _, list in byElement do
	table.freeze(list)
end

local EMPTY: { Reaction } = table.freeze({})

--- Reaction for two elements, order-independent. `nil` for unknown elements or "None".
function Reactions.get(a: Element | string, b: Element | string): Reaction?
	if type(a) ~= "string" or type(b) ~= "string" then
		return nil
	end
	return byPair[pairKey(a, b)]
end

--- Reaction by id ("Steam"); case-insensitive.
function Reactions.byId(id: string): Reaction?
	if type(id) ~= "string" then
		return nil
	end
	return byId[id] or byIdLower[string.lower(id)]
end

--- Every reaction (frozen array, stable order).
function Reactions.all(): { Reaction }
	return all
end

--- Every reaction that involves `e` (including its same-element amplifier).
function Reactions.forElement(e: Element | string): { Reaction }
	return byElement[e :: string] or EMPTY
end

--- Damage multiplier HINT for `attacker` hitting `defender`: 1.5 strong, 1 neutral, 0.5 resisted.
--- "None" or unknown elements are always neutral.
function Reactions.matchup(attacker: Element | string, defender: Element | string): number
	local row = MATCHUPS[attacker :: string]
	local cell = row and row[defender :: string]
	return if cell then cell.m else 1
end

--- One-line, player-readable reason for the matchup ("Water douses flames."). nil when neutral by default.
function Reactions.matchupReason(attacker: Element | string, defender: Element | string): string?
	local row = MATCHUPS[attacker :: string]
	local cell = row and row[defender :: string]
	return cell and cell.why
end

--- Elements `e` is strong against (attacker 1.5x), in element order.
function Reactions.strongAgainst(e: Element | string): { Element }
	local out = {}
	for _, d in ELEMENTS do
		if Reactions.matchup(e, d) > 1 then
			table.insert(out, d)
		end
	end
	return out
end

--- Elements that are strong against `e`, in element order.
function Reactions.weakTo(e: Element | string): { Element }
	local out = {}
	for _, a in ELEMENTS do
		if Reactions.matchup(a, e) > 1 then
			table.insert(out, a)
		end
	end
	return out
end

-- Material reactions ----------------------------------------------------------------------------------------
-- Element x material: what happens to a summoned object made of a material when an element hits it.
-- Lookup: overrides[materialId][element], then the first MATERIAL_RULES entry for the element whose tags
-- intersect the material's match set (its tags + lowercased family + lowercased construction).

export type MaterialReaction = {
	id: string, -- outcome key ("Ignite", "Melt", ...)
	name: string,
	description: string,
	statuses: { string },
	hooks: { string },
	magnitudeHint: number,
	durationHint: number,
	vfx: string,
	sfx: string,
	transform: { material: string?, colour: string?, construction: string? }?,
	material: string, -- material id it was resolved for
	element: string,
	via: string, -- "override" | "tag:<tag>"
}

local outcomeCache: { [string]: any } = {}
local function frozenOutcome(key: string): any
	local o = outcomeCache[key]
	if o == nil then
		local raw = (MATERIAL_OUTCOMES :: any)[key]
		if raw == nil then
			return nil
		end
		o = table.clone(raw)
		o.statuses = table.freeze(table.clone(raw.statuses))
		o.hooks = table.freeze(table.clone(raw.hooks))
		if raw.transform then
			o.transform = table.freeze(table.clone(raw.transform))
		end
		table.freeze(o)
		outcomeCache[key] = o
	end
	return o
end

local rulesByElement: { [string]: { any } } = {}
for _, rule in MATERIAL_RULES do
	rulesByElement[rule.element] = rulesByElement[rule.element] or {}
	table.insert(rulesByElement[rule.element], rule)
end

local libraryLookup: ((string) -> any)? = nil
local function materialRecord(id: string): any
	if libraryLookup == nil then
		libraryLookup = function(_: string): any
			return nil
		end
		local ok, Library = pcall(function(): any
			return require((script.Parent :: any).Library)
		end)
		if ok and type(Library) == "table" and type(Library.material) == "function" then
			libraryLookup = Library.material
		end
	end
	return (libraryLookup :: any)(id)
end

local resultCache: { [string]: MaterialReaction | false } = {}

--- What happens when `element` hits a summon made of `material`. `material` is a material id ("wood"; tags
--- come from Library.material) or a record { id, tags, family?, construction? }. nil when nothing happens,
--- for "None" / unknown elements, or for unknown materials with no tags.
function Reactions.material(material: string | { [string]: any }, element: Element | string): MaterialReaction?
	if type(element) ~= "string" or elementIndex[element] == nil then
		return nil
	end
	local rec: any = material
	if type(material) == "string" then
		rec = materialRecord(material) or { id = material, tags = {} }
	end
	if type(rec) ~= "table" then
		return nil
	end
	local id = tostring(rec.id or "?")
	local outcome, via = nil, nil
	local ov = (MATERIAL_OVERRIDES :: any)[id]
	if ov and ov[element] then
		outcome, via = ov[element], "override"
	else
		local set = {}
		for _, tg in rec.tags or {} do
			set[tg] = true
		end
		if type(rec.family) == "string" then
			set[string.lower(rec.family)] = true
		end
		if type(rec.construction) == "string" then
			set[string.lower(rec.construction)] = true
		end
		for _, rule in rulesByElement[element] or {} do
			for _, tg in rule.tags do
				if set[tg] then
					outcome, via = rule.outcome, "tag:" .. tg
					break
				end
			end
			if outcome then
				break
			end
		end
	end
	if not outcome then
		return nil
	end
	local key = id .. "|" .. element .. "|" .. outcome .. "|" .. via
	local cached = resultCache[key]
	if cached then
		return cached
	end
	local base = frozenOutcome(outcome)
	if not base then
		return nil
	end
	local r: any = table.clone(base)
	r.id, r.material, r.element, r.via = outcome, id, element, via
	table.freeze(r)
	resultCache[key] = r
	return r
end

--- Material outcome by key ("Ignite"), without a material/element (frozen, shared).
function Reactions.materialOutcome(key: string): any
	return frozenOutcome(key)
end

--- Every material outcome key, sorted.
function Reactions.materialOutcomes(): { string }
	local out = {}
	for k in MATERIAL_OUTCOMES :: any do
		table.insert(out, k)
	end
	table.sort(out)
	return out
end

--- Validate the embedded material reaction data. `effectExists(id)` (optional) checks vfx ids.
function Reactions.validateMaterials(effectExists: ((string) -> boolean)?): { string }
	local errs = {}
	local function err(fmt: string, ...)
		table.insert(errs, string.format(fmt, ...))
	end
	local statusSet = {}
	for _, st in Reactions.Statuses do
		statusSet[st] = true
	end
	local vfxSeen = {}
	for key, o in MATERIAL_OUTCOMES :: any do
		if not string.match(key, "^%u%w+$") then
			err("bad outcome key %s", key)
		end
		if #o.hooks == 0 then
			err("%s: no hooks", key)
		end
		for _, h in o.hooks do
			if Reactions.HookInfo[h] == nil and Reactions.MaterialHookInfo[h] == nil then
				err("%s: unknown hook %s", key, h)
			end
		end
		for _, st in o.statuses do
			if not statusSet[st] then
				err("%s: unknown status %s", key, st)
			end
		end
		if type(o.magnitudeHint) ~= "number" or o.magnitudeHint <= 0 or o.magnitudeHint > 1 then
			err("%s: magnitudeHint must be in (0,1]", key)
		end
		if type(o.durationHint) ~= "number" or o.durationHint <= 0 or o.durationHint > 30 then
			err("%s: durationHint must be in (0,30]", key)
		end
		if type(o.name) ~= "string" or #o.name == 0 or #o.name > 24 then
			err("%s: name must be 1..24 chars", key)
		end
		if type(o.description) ~= "string" or #o.description < 10 or #o.description > 120 then
			err("%s: description must be 10..120 chars", key)
		end
		if type(o.sfx) ~= "string" or not string.match(o.sfx, "^[%l%d_]+$") then
			err("%s: bad sfx key", key)
		end
		if type(o.vfx) ~= "string" or not string.match(o.vfx, "^[%l%d_%.]+$") then
			err("%s: bad vfx id", key)
		elseif effectExists and not effectExists(o.vfx) then
			err("%s: vfx %s is not in the Effects catalogue", key, o.vfx)
		end
		if vfxSeen[o.vfx] then
			err("%s: vfx %s shared with %s", key, o.vfx, vfxSeen[o.vfx])
		end
		vfxSeen[o.vfx] = key
		if o.transform then
			for k in o.transform do
				if k ~= "material" and k ~= "colour" and k ~= "construction" then
					err("%s: unknown transform field %s", key, tostring(k))
				end
			end
		end
	end
	for i, rule in MATERIAL_RULES do
		if not elementIndex[rule.element] then
			err("rule %d: unknown element %s", i, tostring(rule.element))
		end
		if (MATERIAL_OUTCOMES :: any)[rule.outcome] == nil then
			err("rule %d: unknown outcome %s", i, tostring(rule.outcome))
		end
		if #rule.tags == 0 then
			err("rule %d: no tags", i)
		end
	end
	for mid, row in MATERIAL_OVERRIDES :: any do
		for e, outcome in row do
			if not elementIndex[e] then
				err("override %s: unknown element %s", mid, tostring(e))
			end
			if (MATERIAL_OUTCOMES :: any)[outcome] == nil then
				err("override %s.%s: unknown outcome %s", mid, e, tostring(outcome))
			end
		end
	end
	return errs
end

--- Raw embedded data, for tests and tools.
function Reactions._raw(): (any, any, any, any)
	return ELEMENTS, MATCHUPS, REACTIONS, { outcomes = MATERIAL_OUTCOMES, rules = MATERIAL_RULES, overrides = MATERIAL_OVERRIDES }
end

--- Structural validation of the embedded data. Returns a list of problems (empty when valid).
--- `effectExists(id)` (optional) checks vfx ids against the Effects catalogue.
function Reactions.validate(effectExists: ((string) -> boolean)?): { string }
	local errs = {}
	local function err(fmt: string, ...)
		table.insert(errs, string.format(fmt, ...))
	end
	local statusSet = {}
	for _, s in Reactions.Statuses do
		statusSet[s] = true
	end
	local resultSet = {}
	for _, s in Reactions.Results do
		resultSet[s] = true
	end
	local seenPair = {}
	for _, r in all do
		if type(r.id) ~= "string" or not string.match(r.id, "^%u%w+$") then
			err("bad id %s", tostring(r.id))
		end
		if #r.elements ~= 2 then
			err("%s: needs exactly 2 elements", r.id)
		end
		for _, e in r.elements do
			if not elementIndex[e] then
				err("%s: unknown element %s", r.id, tostring(e))
			end
		end
		local k = pairKey(r.elements[1], r.elements[2])
		if seenPair[k] then
			err("%s: duplicate pair %s (also %s)", r.id, k, seenPair[k])
		end
		seenPair[k] = r.id
		if not resultSet[r.result] then
			err("%s: bad result %s", r.id, tostring(r.result))
		end
		if #r.hooks == 0 then
			err("%s: no hooks", r.id)
		end
		for _, h in r.hooks do
			if Reactions.HookInfo[h] == nil then
				err("%s: unknown hook %s", r.id, h)
			end
		end
		for _, s in r.statuses do
			if not statusSet[s] then
				err("%s: unknown status %s", r.id, s)
			end
		end
		if type(r.magnitudeHint) ~= "number" or r.magnitudeHint <= 0 or r.magnitudeHint > 1 then
			err("%s: magnitudeHint must be in (0,1]", r.id)
		end
		if type(r.durationHint) ~= "number" or r.durationHint <= 0 or r.durationHint > 30 then
			err("%s: durationHint must be in (0,30]", r.id)
		end
		if type(r.name) ~= "string" or #r.name == 0 or #r.name > 24 then
			err("%s: name must be 1..24 chars", r.id)
		end
		if type(r.description) ~= "string" or #r.description < 10 or #r.description > 120 then
			err("%s: description must be 10..120 chars", r.id)
		end
		if type(r.sfx) ~= "string" or not string.match(r.sfx, "^[%l%d_]+$") then
			err("%s: bad sfx key", r.id)
		end
		if type(r.vfx) ~= "string" or not string.match(r.vfx, "^[%l%d_%.]+$") then
			err("%s: bad vfx id", r.id)
		elseif effectExists and not effectExists(r.vfx) then
			err("%s: vfx %s is not in the Effects catalogue", r.id, r.vfx)
		end
	end
	for _, a in ELEMENTS do
		for _, d in ELEMENTS do
			local cell = MATCHUPS[a] and MATCHUPS[a][d]
			if not cell then
				err("matchup %s->%s missing", a, d)
			elseif cell.m ~= 0.5 and cell.m ~= 1 and cell.m ~= 1.5 then
				err("matchup %s->%s bad multiplier %s", a, d, tostring(cell.m))
			elseif type(cell.why) ~= "string" or #cell.why < 8 then
				err("matchup %s->%s needs a reason", a, d)
			end
		end
	end
	return errs
end

return table.freeze(Reactions)
