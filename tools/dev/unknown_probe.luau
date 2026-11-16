local load = require("../../tests/loader")
local R = load("src/Shared/Resolver")
for _, p in { "defenestration", "bureaucracy", "kazoo orchestra", "existential dread", "tax audit", "monday morning", "wifi outage", "quantum entanglement", "awkward silence", "homework", "procrastination", "sock puppet theater" } do
	local r, spell, needsAI = R.resolveLocalDetailed(p)
	print(p, "->", r.canonical, r.source, spell.confidence, needsAI)
end
