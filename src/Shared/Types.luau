--!strict
-- WordEngine shared types. The contract both games build against. See DESIGN.md §3.

export type Category =
	"Creature" | "Object" | "Weapon" | "Vehicle" | "Structure" | "Element" | "Weather" | "Disaster"
	| "Food" | "Tool" | "Abstract" | "Person" | "Place" | "Plant" | "Machine"

export type Element =
	"Fire" | "Water" | "Ice" | "Lightning" | "Earth" | "Wind" | "Nature" | "Light" | "Shadow"
	| "Poison" | "Metal" | "Arcane" | "None"

export type Size = "Tiny" | "Small" | "Medium" | "Large" | "Huge" | "Colossal"

export type Shape =
	"Bolt" | "Beam" | "Wall" | "Cloud" | "Rain" | "Wave" | "Orb" | "Blade" | "Shield" | "Summon"
	| "Mount" | "Trap" | "Turret" | "Zone" | "Buff"

export type Behaviour = string -- one of Schema.Enums.Behaviour

-- 15 generic plans (v0, used by library data) + specialised plans (brief 4). Builders treat a specialised
-- plan as a refinement of its parent (Schema.BodyPlanParent) so every plan always builds.
export type BodyPlan = string -- one of Schema.Enums.BodyPlan

export type Mood =
	"Neutral" | "Angry" | "Sleepy" | "Scared" | "Crazy" | "Hungry" | "Happy" | "Sneaky" | "Lazy" | "Hyper"
	| "Confused" | "Sad" | "Smug" | "Cute"

export type Motion =
	"Walk" | "Fly" | "Swim" | "Slither" | "Hover" | "Roll" | "Hop" | "Burrow" | "Static" | "Float" | "Spin" | "Drive"

export type Source = "Library" | "Cache" | "AI" | "Admin" | "Fallback"

export type CorrectionMethod =
	"Exact" | "Alias" | "Normalized" | "Stem" | "Misspelling" | "Fuzzy" | "Phonetic" | "MultiWord" | "AI"

export type ModifierKind = "Size" | "Count" | "Mood" | "Quality" | "Element" | "State" | "Motion" | "Material"

export type Visual = {
	primaryColour: string, -- "#RRGGBB"
	secondaryColour: string,
	bodyPlan: BodyPlan,
	silhouetteHint: string,
	motionHint: Motion,
	soundHint: string,
	accents: { string }, -- builder feature hints added by modifiers/materials: "scowl","steam","thrusters","halo","crack"
}

export type Correction = {
	method: CorrectionMethod,
	from: string,
	to: string,
	confidence: number,
	alternatives: { string },
}

export type AppliedModifier = { id: string, kind: ModifierKind }

export type WordResult = {
	schemaVersion: number,
	id: string,
	canonical: string,
	input: string,
	confidence: number,
	source: Source,
	correction: Correction?,
	category: Category,
	element: Element,
	secondaryElement: Element, -- "None" unless split-element ("fire ice dragon")
	material: string?, -- material id from data/materials.json ("spaghetti"), nil = natural material of the thing
	mood: Mood, -- drives faces/posture/sound ("Neutral" default)
	size: Size,
	shape: Shape,
	behaviours: { Behaviour },
	power: number,
	speed: number,
	durability: number,
	count: number,
	modifiers: { AppliedModifier },
	signature: boolean,
	synonymGroup: string,
	visual: Visual,
	flavourText: string,
	tags: { string },
}

export type Modifier = {
	id: string, -- "giant"
	kind: ModifierKind,
	order: number?, -- application order within kind (see DESIGN.md §5a)
	mood: Mood?,
	accents: { string }?,
	aliases: { string }?,
	misspellings: { string }?,
	motion: Motion?,
	tint: string?, -- hex tint blended into colours
	colour2: string?, -- override secondary colour
	size: number?, -- size steps (+2 giant, -2 tiny)
	element: Element?,
	count: number?, -- multiply count
	power: number?, -- additive delta
	speed: number?,
	durability: number?,
	addBehaviours: { Behaviour }?,
	addTags: { string }?,
	colour: string?, -- override primary colour (golden, rainbow)
}

-- Material record (data/materials.json, compiled). Look + construction + gameplay hooks.
export type Material = {
	id: string,
	family: "Food" | "Natural" | "Manufactured" | "Weird",
	aliases: { string },
	palette: { string }, -- hex colours, 2-5
	robloxMaterial: string, -- Enum.Material name for Solid style ("SmoothPlastic","Glass","Wood",...)
	transparency: number,
	glow: number, -- 0..1
	construction: "Solid" | "Strands" | "Bricks" | "Panels" | "Wobble" | "Swarm" | "Shards" | "Inflated" | "Woven" | "Pile" | "Liquid" | "Energy",
	particles: { string }, -- effect ids: "drip_sauce","sawdust","sparkle","bees"
	sound: string,
	element: Element, -- affinity used by reactions ("Fire" for lava, "None" for most)
	tags: { string },
	hooks: { string }, -- gameplay hooks: "Bounces","ShattersOnHit","EdibleLure","BurnsFast","Durable","Slow","DamageAura","Conductive","Tangles"
	statHints: { power: number?, speed: number?, durability: number? }, -- small deltas, capped by Config.Modifiers
}

export type SpellResult = {
	canonical: string?, -- library id, nil if unknown
	confidence: number,
	method: CorrectionMethod?,
	alternatives: { string },
	tokens: { string },
	modifiers: { Modifier },
	material: string?,
	extras: { string }, -- leftover tokens the parser could not place (sent to the AI if confidence is low)
}

export type Reaction = {
	id: string,
	elements: { Element },
	name: string,
	description: string,
	result: "Zone" | "Burst" | "Status" | "Transform" | "Buff" | "Cancel",
	statuses: { string },
	hooks: { string },
	magnitudeHint: number,
	durationHint: number,
	vfx: string,
	sfx: string,
}

export type SummonStyle = "Spectral" | "Solid"

export type SummonOptions = {
	style: SummonStyle,
	budget: { maxParts: number?, maxParticles: number? }?,
	scale: number?,
	seed: number?,
}

return {}
