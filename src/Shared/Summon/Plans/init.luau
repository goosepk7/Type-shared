--!strict
-- Body plan registry: BodyPlan name -> generator fn(B: Builder, ctx). 15 generic plans, each parametric over
-- the word's traits (tags, silhouette hint, behaviours, stats, mood) and the seeded RNG, plus 45 specialised
-- plans (Schema.BodyPlanParent) that route to a generator with a forced kind and/or forced traits, so every one
-- of the 60 plans builds something specific. Plans/Objects covers Furniture/Appliance/Container.

local Plans: { [string]: (any, any) -> () } = {}

for _, name in { "Quadruped", "Biped", "Serpent", "Bird", "Fish", "Insect", "Blob", "Vehicle", "Structure", "Weapon", "Orb", "Swarm", "Plant", "Humanoid", "Cloud", "Objects" } do
	local mod = script:FindFirstChild(name)
	if mod then
		Plans[name] = require(mod) :: any
	end
end

-- specialised plan -> { generator, kind, forced traits }
local ROUTES: { [string]: { any } } = {
	Dragon = { "Quadruped", nil, { dragon = true, wings = true, flies = true, horns = true, scaly = true, spikes = true, longTail = true, mythical = true } },
	Turtle = { "Quadruped", nil, { shell = true, stubby = true, scaly = true } },
	Spider = { "Insect", "Spider", { insect = true } },
	Crab = { "Insect", "Crab", { pincers = true } },
	Octopus = { "Fish", "cephalopod", { tentacles = true } },
	Worm = { "Serpent", "Worm", {} },
	Ghost = { "Cloud", "Ghost", { ghost = true } },
	Robot = { "Humanoid", "robot", { robot = true, mechanical = true } },
	Giant = { "Humanoid", "giant", {} },
	Knight = { "Humanoid", "knight", {} },
	Wizard = { "Humanoid", "wizard", {} },
	Tree = { "Plant", "Tree", {} },
	Flower = { "Plant", "Flower", {} },
	Mushroom = { "Plant", "Mushroom", {} },
	Cactus = { "Plant", "Cactus", {} },
	CarWheeled = { "Vehicle", "CarWheeled", {} },
	Tracked = { "Vehicle", "Tracked", {} },
	Aircraft = { "Vehicle", "Aircraft", {} },
	Helicopter = { "Vehicle", "Helicopter", {} },
	Boat = { "Vehicle", "Boat", {} },
	Submarine = { "Vehicle", "Submarine", {} },
	Rocket = { "Vehicle", "Rocket", {} },
	Building = { "Structure", "Building", {} },
	Tower = { "Structure", "Tower", {} },
	Wall = { "Structure", "Wall", {} },
	Gate = { "Structure", "Gate", {} },
	Bridge = { "Structure", "Bridge", {} },
	Castle = { "Structure", "Castle", {} },
	Sword = { "Weapon", "Sword", {} },
	Axe = { "Weapon", "Axe", {} },
	Hammer = { "Weapon", "Hammer", {} },
	Spear = { "Weapon", "Spear", {} },
	Bow = { "Weapon", "Bow", {} },
	Gun = { "Weapon", "Gun", {} },
	Cannon = { "Weapon", "Cannon", {} },
	Shield = { "Weapon", "Shield", {} },
	Staff = { "Weapon", "Staff", {} },
	Furniture = { "Objects", "Furniture", {} },
	Appliance = { "Objects", "Appliance", {} },
	Container = { "Objects", "Container", {} },
	Ball = { "Orb", "Ball", {} },
	Crystal = { "Orb", "Crystal", {} },
	Vortex = { "Cloud", "Vortex", { funnel = true } },
	Wave = { "Cloud", "Wave", {} },
	Food = { "Blob", "Food", {} },
}
Plans.Routes = ROUTES :: any

-- Dragon prefers the hand-built dragon signature when it is registered (set by Summon init).
Plans.signatureHook = nil :: ((string) -> ((any, any) -> ())?)?

for name, route in ROUTES do
	local gen = Plans[route[1]]
	if gen then
		Plans[name] = function(B: any, ctx: any)
			for k, v in route[3] do
				ctx.traits[k] = v
			end
			if route[3].wings then
				ctx.traits.wingKind = "bat"
			end
			if name == "Dragon" and Plans.signatureHook then
				local sig = Plans.signatureHook("dragon")
				if sig then
					return sig(B, ctx)
				end
			end
			if name == "Vortex" and string.find(string.lower(ctx.result.id), "black hole", 1, true) and Plans.Orb then
				-- the Library files "black hole" under Vortex; it is an event horizon with an accretion disc (Orb), not
				-- a wind funnel
				ctx.kind = nil
				return Plans.Orb(B, ctx)
			end
			ctx.kind = route[2]
			return gen(B, ctx)
		end
	end
end

-- Objects are also the default for generic Object-category words routed to Structure with a household id.
local structure = Plans.Structure
local objects = Plans.Objects
if structure and objects then
	local HOUSEHOLD = { "chair", "table", "bed", "sofa", "couch", "lamp", "shelf", "toaster", "fridge", "tv", "television", "microwave", "oven", "washing",
		"fan", "vacuum", "barrel", "chest", "jar", "vase", "bottle", "mug", "cup", "bucket", "trash", "backpack", "box", "crate", "present", "gift", "throne", "desk", "stool", "potion", "lantern", "computer" }
	Plans.Structure = function(B: any, ctx: any)
		if ctx.kind == nil then
			local id = string.lower(ctx.result.id)
			for _, w in HOUSEHOLD do
				if string.find(id, "%f[%a]" .. w) then
					return objects(B, ctx)
				end
			end
			if ctx.result.category == "Food" and Plans.Blob then
				-- "giant pancake", "bread", "lasagna": food filed under Structure is food, not a house with a face.
				-- Only edible architecture ("gingerbread house", "cheese wall", "cake tower") stays a building.
				local building = false
				for _, w in { "house", "tower", "wall", "castle", "gate", "bridge", "fort", "fountain", "hut", "cabin", "pyramid", "shield" } do
					if string.find(id, w, 1, true) then
						building = true
					end
				end
				if not building then
					ctx.kind = "Food"
					return Plans.Blob(B, ctx)
				end
			end
			if ctx.result.category == "Object" or ctx.result.category == "Tool" or ctx.result.category == "Machine" then
				-- non-architectural things that fell back to Structure: a chunky prop rather than a house
				local plain = true
				for _, w in { "house", "tower", "wall", "castle", "gate", "bridge", "pyramid", "igloo", "tent", "statue", "lighthouse", "mill", "fort", "temple", "hut", "cabin", "barn", "shop", "school" } do
					if string.find(id, w, 1, true) then
						plain = false
					end
				end
				if plain then
					return objects(B, ctx)
				end
			end
		end
		return structure(B, ctx)
	end
end

Plans.Blob = Plans.Blob or Plans.Quadruped

return Plans
