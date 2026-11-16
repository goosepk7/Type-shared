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

export type BodyPlan =
	"Quadruped" | "Biped" | "Serpent" | "Bird" | "Fish" | "Insect" | "Blob" | "Vehicle" | "Structure"
	| "Weapon" | "Orb" | "Swarm" | "Plant" | "Humanoid" | "Cloud"

export type Motion =
	"Walk" | "Fly" | "Swim" | "Slither" | "Hover" | "Roll" | "Hop" | "Burrow" | "Static" | "Float" | "Spin" | "Drive"

export type Source = "Library" | "Cache" | "AI" | "Admin" | "Fallback"

export type CorrectionMethod =
	"Exact" | "Alias" | "Normalized" | "Stem" | "Misspelling" | "Fuzzy" | "Phonetic" | "MultiWord" | "AI"

export type ModifierKind = "Size" | "Element" | "Count" | "Quality"

export type Visual = {
	primaryColour: string, -- "#RRGGBB"
	secondaryColour: string,
	bodyPlan: BodyPlan,
	silhouetteHint: string,
	motionHint: Motion,
	soundHint: string,
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
	aliases: { string }?,
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

export type SpellResult = {
	canonical: string?, -- library id, nil if unknown
	confidence: number,
	method: CorrectionMethod?,
	alternatives: { string },
	tokens: { string },
	modifiers: { Modifier },
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
