local load = require("../../tests/loader")
local R = load("src/Shared/Resolver")
for _, p in { "angry shark", "summon asteroid", "call in an asteroid", "small tornado", "giant fire shark", "spagetti dragn", "dragon made of spaghetti", "tiny angry golden robot shark", "frozen shark", "summon a dragon", "bees", "cheese tank", "glass shark", "bee wall", "fire ice dragon", "tiny giant shark", "shark angry", "pikachu", "dr4gon", "fiiiire" } do
	local r = R.resolveLocal(p)
	local mods = {}
	for _, m in r.modifiers do table.insert(mods, m.id) end
	print(string.format("%-30s -> %-28s id=%-14s %s/%s %s %s el=%s/%s mat=%s mood=%s n=%d [%s] %s", p, r.canonical, r.id, r.category, r.shape, r.size, r.source, r.element, r.secondaryElement, tostring(r.material), r.mood, r.count, table.concat(mods, ","), table.concat(r.behaviours, ",")))
end
