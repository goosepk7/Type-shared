-- Summon z-fighting sweep: every body plan x size x style x 50 seeds, every signature, 300 library entries,
-- and material x mood combinations must produce ZERO coplanar / coincident surface violations after the fix pass.
-- SUMMON_SEEDS=<n> overrides the seed count (default 50) for quicker local runs.
local process = require("@lune/process")
local F = require("./summon_fixtures")

return function(t)
	local Schema = t.load("src/Shared/Schema")
	local Summon = t.load("src/Shared/Summon")
	local Rng = t.load("src/Shared/Summon/Rng")
	local SEEDS = tonumber(process.env.SUMMON_SEEDS) or 50
	local STYLES = { "Solid", "Spectral" }

	local function report(label: string, bp: any, v: { any }): string
		local a = bp.parts[v[1].a]
		local b = bp.parts[v[1].b]
		return string.format("%s: %d violations, first %s/%s (%s)", label, #v, a and a.name or "?", b and b.name or "?", v[1].kind)
	end

	local function sweep(name: string, results: { any }, seeds: number)
		t.test(name, function()
			local bad, n = {}, 0
			for _, r in results do
				for _, style in STYLES do
					for seed = 1, seeds do
						local bp = Summon.blueprint(r, { style = style, seed = seed })
						n += 1
						local v = Summon.check(bp)
						if #v > 0 then
							table.insert(bad, report(r.id .. " " .. r.size .. " " .. style .. " seed " .. seed, bp, v))
							if #bad >= 8 then
								break
							end
						end
					end
				end
			end
			t.ok(#bad == 0, n .. " builds; " .. table.concat(bad, "\n  "))
		end)
	end

	-- every plan (15 generic + 45 specialised) x size
	for _, plan in Schema.Enums.BodyPlan do
		local results = {}
		for _, size in F.Sizes do
			if F.Variants[plan] then
				for v = 1, #F.Variants[plan] do
					table.insert(results, F.synthetic(Schema, plan, size, v))
				end
			elseif F.Special[plan] then
				table.insert(results, F.special(Schema, plan, size))
			end
		end
		t.ok(#results > 0, "fixture for plan " .. plan)
		-- generic plans have several variants; keep total work bounded by spreading seeds across variants
		local per = if F.Variants[plan] then math.max(1, math.ceil(SEEDS / #F.Variants[plan])) else SEEDS
		sweep("no z-fighting: plan " .. plan, results, per)
	end

	-- every signature at every size
	local sigs = {}
	for _, s in F.SignatureWords do
		for _, size in F.Sizes do
			table.insert(sigs, F.signatureResult(Schema, s, size))
		end
	end
	sweep("no z-fighting: signatures", sigs, 3)

	-- 300 random library entries
	local lib = F.library(Schema)
	if #lib > 0 then
		local rng = Rng.new(20240611)
		local pick = {}
		for _ = 1, math.min(300, #lib) do
			table.insert(pick, lib[rng:int(1, #lib)])
		end
		sweep("no z-fighting: 300 library entries", pick, 1)
	end

	-- materials x moods x accents on a spread of plans (phrase-style results)
	if F.phrases then
		sweep("no z-fighting: material/mood/accent phrases", F.phrases(Schema, 240, 99), 1)
	end
end
