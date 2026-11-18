-- dev probe: build every Insect / Spider / Crab / Turtle library word in both styles and report errors, part
-- counts, z-fighting and mesh coverage. lune run tools/dev/bugs_probe [filter]
local process = require("@lune/process")
local load = require("../../tests/loader")
local F = require("../../tests/specs/summon_fixtures")
local Schema = load("src/Shared/Schema")
local Summon = load("src/Shared/Summon")
local filter = process.args[1]
local plans = { Insect = true, Spider = true, Crab = true, Turtle = true }
local n, bad = 0, 0
for _, r in F.library(Schema) do
	if plans[r.visual.bodyPlan] and (filter == nil or string.find(r.id, filter, 1, true)) then
		for _, style in { "Solid", "Spectral" } do
			for _, size in { r.size } do
				local ok, bp = pcall(Summon.blueprint, r, { style = style, seed = 1 })
				n += 1
				if not ok then
					bad += 1
					print("ERROR", r.id, style, bp)
				else
					local v = Summon.check(bp)
					local missing = {}
					if #v > 0 then
						bad += 1
						print("ZFIGHT", r.id, style, #v)
					end
					if process.env.VERBOSE then
						print(string.format("%-28s %-8s %-6s d%d parts %2d mesh %2d gait %s", r.id, style, r.size, bp.detail, #bp.parts, bp.stats.meshParts or -1, tostring(bp.rig.gait)))
					end
					if process.env.LEGS then
						local legs = 0
						for _, p in bp.parts do
							local nm = tostring(p.name)
							if string.match(nm, "^Leg") or string.match(nm, "^Comb") or string.match(nm, "^Femur") or string.match(nm, "^Walk") or string.match(nm, "^Jump") then
								legs += 1
							end
						end
						print(string.format("%-28s %-8s d%d parts %2d legparts %d", r.id, style, bp.detail, #bp.parts, legs))
					end
					if process.env.PARTS then
						print(r.id, style, "d" .. bp.detail)
						for _, p in bp.parts do
							print(string.format("   %-14s %-10s %s  @ %s", tostring(p.name), tostring(p.mesh), table.concat(p.size, ","), if p.cf then string.format("%.2f %.2f %.2f", p.cf[1] or 0, p.cf[2] or 0, p.cf[3] or 0) else "?"))
						end
					end
				end
			end
		end
	end
end
print("built", n, "problems", bad)
