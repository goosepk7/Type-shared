-- Reactions: data validity, symmetry, coverage, matchup table coherence, JSON <-> embedded data parity,
-- material reactions.
local fs = require("@lune/fs")
local serde = require("@lune/serde")

return function(t)
	local Reactions = t.load("src/Shared/Reactions")
	local Catalogue = t.load("src/Shared/Effects/Catalogue")
	local E = Reactions.Elements

	t.test("structural validation passes (hooks, statuses, hints, vfx exist in Effects catalogue)", function()
		local errs = Reactions.validate(Catalogue.has)
		t.ok(#errs == 0, table.concat(errs, "\n"))
	end)

	t.test("45+ reactions, every element pair covered, plus 12 same-element amplifiers", function()
		t.ok(#Reactions.all() >= 45, "need 45+ reactions, have " .. #Reactions.all())
		for i, a in E do
			for j = i, #E do
				t.ok(Reactions.get(a, E[j]) ~= nil, "missing reaction " .. a .. "+" .. E[j])
			end
			local amp = Reactions.get(a, a)
			t.ok(amp and table.find(amp.hooks, "Amplify"), a .. " amplifier needs the Amplify hook")
		end
	end)

	t.test("get() is order-independent and handles None/unknown", function()
		for _, a in E do
			for _, b in E do
				t.eq(Reactions.get(a, b), Reactions.get(b, a), a .. "/" .. b)
			end
		end
		t.eq(Reactions.get("Fire", "None"), nil)
		t.eq(Reactions.get("Nope", "Fire"), nil)
		t.eq(Reactions.get(nil :: any, "Fire"), nil)
		t.eq(Reactions.get("Fire", "Ice").id, "Steam")
		t.eq(Reactions.get("Lightning", "Water").id, "Electrocute")
		t.eq(Reactions.get("Nature", "Fire").id, "Wildfire")
		t.eq(Reactions.get("Shadow", "Light").id, "Eclipse")
		t.eq(Reactions.get("Metal", "Water").id, "Rust")
		t.eq(Reactions.byId("steam").id, "Steam")
	end)

	t.test("coverage: every element participates in >= 5 reactions", function()
		for _, e in E do
			t.ok(#Reactions.forElement(e) >= 5, e .. " has " .. #Reactions.forElement(e))
		end
		t.eq(#Reactions.forElement("None"), 0)
	end)

	t.test("ids, vfx ids and pairs are unique", function()
		local ids, vfx = {}, {}
		for _, r in Reactions.all() do
			t.ok(not ids[r.id], "dup id " .. r.id)
			t.ok(not vfx[r.vfx], "dup vfx " .. r.vfx)
			ids[r.id], vfx[r.vfx] = true, true
		end
	end)

	t.test("matchup table: full 12x12, values in {0.5,1,1.5}, reads as rock-paper-scissors", function()
		for _, a in E do
			local strong = 0
			for _, d in E do
				local m = Reactions.matchup(a, d)
				t.ok(m == 0.5 or m == 1 or m == 1.5, a .. "->" .. d)
				t.ok(type(Reactions.matchupReason(a, d)) == "string", "reason " .. a .. "->" .. d)
				if m == 1.5 then
					strong += 1
					-- strong one way => resisted the other way, except the Light/Shadow rivalry
					if not ((a == "Light" and d == "Shadow") or (a == "Shadow" and d == "Light")) then
						t.eq(Reactions.matchup(d, a), 0.5, d .. "->" .. a .. " should be resisted")
					end
				end
			end
			t.ok(strong >= 2 and strong <= 4, a .. " strong count " .. strong)
			t.ok(#Reactions.weakTo(a) >= 2 and #Reactions.weakTo(a) <= 4, a .. " weakness count")
			t.eq(Reactions.matchup(a, a), 0.5, a .. " resists itself")
			t.eq(Reactions.matchup(a, "None"), 1)
		end
		t.eq(Reactions.matchup("Water", "Fire"), 1.5)
		t.eq(Reactions.matchup("Earth", "Lightning"), 1.5)
		t.eq(Reactions.matchup("Lightning", "Earth"), 0.5)
		t.eq(Reactions.matchup("Light", "Shadow"), 1.5)
		t.eq(Reactions.matchup("Fire", "Nature"), 1.5)
	end)

	t.test("JSON schema: data/*.json parse, have required fields, and match the embedded data", function()
		local rj = serde.decode("json", fs.readFile("data/reactions.json"))
		local mj = serde.decode("json", fs.readFile("data/matchups.json"))
		t.eq(type(rj.reactions), "table")
		local _, MATCH, RAW = Reactions._raw()
		t.eq(#rj.reactions, #RAW, "reaction count (run python3 tools/gen_reactions.py)")
		local required = { "id", "elements", "name", "description", "result", "statuses", "hooks", "magnitudeHint", "durationHint", "vfx", "sfx" }
		for i, r in rj.reactions do
			for _, k in required do
				t.ok(r[k] ~= nil, ("reactions.json[%d] missing %s"):format(i, k))
			end
			local e = RAW[i]
			t.eq(e.id, r.id, "order/id drift at " .. i)
			t.eq(e.vfx, r.vfx, "vfx drift " .. r.id)
			t.eq(e.magnitudeHint, r.magnitudeHint, "magnitude drift " .. r.id)
			t.eq(table.concat(e.hooks, ","), table.concat(r.hooks, ","), "hooks drift " .. r.id)
			t.eq(table.concat(e.statuses, ","), table.concat(r.statuses, ","), "statuses drift " .. r.id)
		end
		t.eq(#mj.elements, 12)
		for _, a in mj.elements do
			for _, d in mj.elements do
				local cell = mj.table[a][d]
				t.ok(cell and type(cell.why) == "string", "matchups.json " .. a .. "->" .. d)
				t.eq(MATCH[a][d].m, cell.m, "matchup drift " .. a .. "->" .. d)
			end
		end
	end)

	-- Material reactions ------------------------------------------------------------------------------------

	t.test("material reactions: rules validate and every vfx exists", function()
		local errs = Reactions.validateMaterials(Catalogue.has)
		t.ok(#errs == 0, table.concat(errs, "\n"))
	end)

	t.test("material reactions: signature interactions", function()
		local function m(tags, e)
			return Reactions.material({ id = "x", tags = tags }, e)
		end
		t.eq(m({ "flammable", "wood" }, "Fire").id, "Ignite")
		t.eq(m({ "meltable", "edible" }, "Fire").id, "Melt")
		t.eq(m({ "clay" }, "Fire").id, "Bake")
		t.eq(m({ "absorbent", "paper" }, "Water").id, "Soggy")
		t.eq(m({ "conductive", "metal" }, "Lightning").id, "Conduct")
		t.eq(m({ "metal" }, "Water").id, "Rust")
		t.eq(m({ "liquid" }, "Ice").id, "Freeze")
		t.eq(m({ "brittle", "glass" }, "Metal").id, "Shatter")
		t.eq(m({ "metal" }, "Arcane").id, "Transmute")
		t.eq(m({}, "Fire"), nil)
		t.eq(m({ "flammable" }, "None"), nil)
		-- explicit per-material overrides beat tag rules
		t.eq(Reactions.material({ id = "cheese", tags = { "edible" } }, "Fire").id, "Melt")
		t.eq(Reactions.material({ id = "ice", tags = {} }, "Fire").id, "Melt")
		t.eq(Reactions.material({ id = "chocolate", tags = {} }, "Fire").id, "Melt")
		t.eq(Reactions.material({ id = "cardboard", tags = {} }, "Water").id, "Soggy")
		t.eq(Reactions.material({ id = "popcorn", tags = {} }, "Fire").id, "Pop")
	end)

	t.test("material reactions: cover data/materials.json when present", function()
		if not fs.isFile("data/materials.json") then
			return -- materials authored by another thread; coverage enforced once the file lands
		end
		local raw = serde.decode("json", fs.readFile("data/materials.json"))
		local list = if raw.materials then raw.materials else raw
		local weak = {}
		local n = 0
		for _, mat in list do
			n += 1
			local reacting = 0
			for _, e in E do
				if Reactions.material(mat, e) then
					reacting += 1
				end
			end
			if reacting < 2 then
				table.insert(weak, tostring(mat.id) .. "(" .. reacting .. ")")
			end
		end
		t.ok(#weak <= math.floor(n * 0.05), "materials reacting to < 2 elements: " .. table.concat(weak, ", "))
	end)
end
