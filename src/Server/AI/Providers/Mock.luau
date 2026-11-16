--!strict
-- Mock provider: canned, deterministic results with NO network. Used automatically in Studio play-solo
-- (Secrets are only available in live servers and Team Test) and by tests. Results are obviously
-- fake (flavour text starts with "[MOCK]") so nobody mistakes them for real AI output.

local Runtime = require(script.Parent.Parent.Parent.Runtime)
local Common = require(script.Parent.Common)

local Mock = {}
Mock.name = "Mock"
Mock.offline = true

local KINDS = {
	{ category = "Creature", element = "Arcane", shape = "Summon", bodyPlan = "Blob", motion = "Hop", behaviours = { "Bounces", "Confuses" }, colours = { "#B388FF", "#EDE7F6" } },
	{ category = "Object", element = "Fire", shape = "Orb", bodyPlan = "Orb", motion = "Float", behaviours = { "Burns", "Explodes" }, colours = { "#FF7043", "#FFE0B2" } },
	{ category = "Machine", element = "Metal", shape = "Turret", bodyPlan = "Robot", motion = "Static", behaviours = { "Ranged", "Shocks" }, colours = { "#90A4AE", "#4FC3F7" } },
	{ category = "Plant", element = "Nature", shape = "Trap", bodyPlan = "Plant", motion = "Static", behaviours = { "Poisons", "Slows" }, colours = { "#66BB6A", "#F0F4C3" } },
	{ category = "Weather", element = "Water", shape = "Rain", bodyPlan = "Cloud", motion = "Float", behaviours = { "Slows", "Spreads" }, colours = { "#5C8DB8", "#E3F2FD" } },
}

local function hash(s: string): number
	local h = 5381
	for i = 1, #s do
		h = (h * 33 + string.byte(s, i)) % 2147483647
	end
	return h
end

function Mock.item(key: string): { [string]: any }
	local k = KINDS[(hash(key) % #KINDS) + 1]
	return {
		key = key, refused = false, id = key, corrected = "", confidence = 0.55, category = k.category,
		element = k.element, secondaryElement = "None", material = "", mood = "Neutral", size = "Small",
		shape = k.shape, behaviours = k.behaviours, power = 3, speed = 4, durability = 3,
		primaryColour = k.colours[1], secondaryColour = k.colours[2], bodyPlan = k.bodyPlan,
		silhouetteHint = "placeholder shape", motionHint = k.motion, soundHint = "boing", accents = {},
		flavourText = "[MOCK] Studio stand-in for real AI.", tags = { "mock" },
	}
end

function Mock.build(_cfg: any, _secret: any, args: any): any
	return { keys = args.keys }
end

function Mock.respond(cfg: any, keys: { string }): Common.Parsed
	Runtime.warnOnce("mockai", "*** MOCK AI PROVIDER ACTIVE: phrases get canned [MOCK] results, no API calls. "
		.. "Use Team Test or a live server with the ANTHROPIC_API_KEY secret for real AI. ***")
	local latency = (cfg and cfg.Latency) or 0.3
	if latency > 0 then
		Runtime.task().wait(latency)
	end
	local results = {}
	for _, k in keys do
		table.insert(results, Mock.item(k))
	end
	local p = Common.empty("")
	p.ok = true
	p.data = { results = results }
	return p
end

function Mock.parse(_response: any): Common.Parsed
	return Common.empty("mock has no HTTP")
end

return Mock
