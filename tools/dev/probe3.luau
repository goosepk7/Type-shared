local load = require("../../tests/loader")
local R = load("src/Shared/Resolver")
local Summon = load("src/Shared/Summon")
local process = require("@lune/process")
for _, p in process.args do
	local r = R.resolveLocal(p)
	for _, style in { "Spectral", "Solid" } do
		local bp = Summon.blueprint(r, { style = style })
		print(string.format("%-16s %-8s id=%s size=%s plan=%s motion=%s shape=%s scale=" .. tostring(bp.scale) .. " parts=%d root=%.1f x %.1f x %.1f", p, style, r.id, r.size, r.visual.bodyPlan, r.visual.motionHint, r.shape, #bp.parts, bp.root.size[1], bp.root.size[2], bp.root.size[3]))
	end
end
