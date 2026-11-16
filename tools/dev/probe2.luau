local load = require("../../tests/loader")
local R = load("src/Shared/Resolver")
local process = require("@lune/process")
for _, p in process.args do
	local r, _, needs = R.resolveLocalDetailed(p)
	print(string.format("%-12s -> %-16s id=%-14s %s/%s %s conf=%.2f ai=%s mat=%s corr=%s", p, r.canonical, r.id, r.category, r.shape, r.source, r.confidence, tostring(needs), tostring(r.material), r.correction and r.correction.to or "-"))
end
