return function(t)
	local M = t.load("tests/specs/server_mocks")

	t.test("Json.parseLoose: direct, fenced, prose-wrapped, trailing commas, smart quotes", function()
		M.setup(t)
		local Json = t.load("src/Server/AI/Json")
		t.eq(Json.parseLoose('{"a":1}').a, 1)
		t.eq(Json.parseLoose('Sure! ```json\n{"results":[{"key":"x","id":"x"}]}\n``` hope that helps').results[1].id, "x")
		t.eq(Json.parseLoose('{"a":[1,2,],}').a[2], 2)
		t.eq(Json.parseLoose("{\u{201C}a\u{201D}: 3}").a, 3)
		t.eq(Json.parseLoose('noise {"s":"has } brace and \\" quote"} tail').s, 'has } brace and " quote')
		t.eq(Json.parseLoose("no json here"), nil)
		t.eq(Json.parseLoose(nil), nil)
		t.eq(Json.parseLoose(42), nil)
	end)

	t.test("Json.parseLoose closes truncated output (max_tokens)", function()
		M.setup(t)
		local Json = t.load("src/Server/AI/Json")
		local v = Json.parseLoose('{"results":[{"key":"a","id":"a","power":3},{"key":"b","id":"b","flavourText":"cut off mid')
		t.ok(v and v.results, "parsed")
		t.eq(v.results[1].id, "a")
		t.eq(#v.results, 2)
	end)

	t.test("malformed AI JSON is repaired into a valid, clamped WordResult", function()
		local ctx = M.setup(t)
		ctx.useAI(function(keys)
			-- prose + fences + wrong enum case + out-of-band power + bad colour + junk behaviour
			return "Here you go:\n```json\n" .. M.jsonEncode({ results = { {
				key = keys[1], id = "Zorblax", category = "creature", element = "FIRE", size = "tiny",
				shape = "summon", behaviours = { "flies", "Teleports", "Explodes", "NotAThing" }, power = 99,
				speed = -5, durability = "7", primaryColour = "red", secondaryColour = "#abc", bodyPlan = "bird",
				motionHint = "fly", soundHint = "squawk", flavourText = string.rep("ha", 100), tags = { "Silly", 3 },
				confidence = 7,
			} } }) .. "\n```"
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "zorblax", { timeout = 2 })
		t.eq(r.source, "AI")
		t.eq(r.id, "zorblax")
		t.eq(r.category, "Creature")
		t.eq(r.element, "Fire")
		t.eq(r.size, "Tiny")
		t.eq(r.power, 3, "power clamped to Tiny band")
		t.eq(r.speed, 1)
		t.eq(r.durability, 7)
		t.eq(#r.behaviours, 3)
		t.eq(r.visual.primaryColour, "#9AA5B1")
		t.eq(r.visual.secondaryColour, "#AABBCC")
		t.ok(#r.flavourText <= 80, "flavour limited")
		t.ok(r.confidence <= 0.9, "confidence capped")
		t.eq(r.input, "zorblax")
		t.eq(r.signature, false)
	end)

	t.test("garbage AI output never errors and falls back", function()
		local ctx = M.setup(t)
		ctx.useAI(function()
			return "I cannot comply {{{{"
		end)
		local r, h = ctx.Interpreter.interpretAsync(ctx.player(), "flumbo", { timeout = 2 })
		t.eq(r.source, "Fallback")
		t.eq(h.pending, false)
	end)

	t.test("Anthropic request: secret only in x-api-key, forced strict tool, cached system prompt", function()
		local ctx = M.setup(t)
		local seen
		ctx.useAI(function(keys, req, body)
			seen = { req = req, body = body }
			return ctx.resultsJson(keys)
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "glimmerbug", { timeout = 2 })
		t.eq(r.source, "AI")
		t.ok(seen, "request sent")
		t.eq(seen.req.Url, "https://api.anthropic.com/v1/messages")
		t.eq(seen.req.Headers["x-api-key"].__secret, "ANTHROPIC_API_KEY")
		t.eq(seen.req.Headers["anthropic-version"], "2026-10-21")
		t.ok(string.find(seen.req.Body, "sk-test", 1, true) == nil, "key never in body")
		t.eq(seen.body.model, "claude-haiku-5-5")
		t.eq(seen.body.tool_choice.type, "tool")
		t.eq(seen.body.tool_choice.name, "submit_words")
		t.eq(seen.body.tools[1].strict, true)
		t.ok(seen.body.tools[1].input_schema.properties.results ~= nil, "schema")
		local item = seen.body.tools[1].input_schema.properties.results.items
		for _, f in { "material", "mood", "secondaryElement", "accents" } do
			t.ok(item.properties[f] ~= nil, "schema has " .. f)
		end
		t.eq(seen.body.output_config.effort, "low")
		t.eq(seen.body.output_config.format, nil)
		t.eq(seen.body.thinking.type, "disabled")
		t.eq(seen.body.temperature, nil)
		t.ok(seen.body.max_tokens <= 600, "low max_tokens for one word")
		local sys = seen.body.system[1]
		t.eq(sys.cache_control.type, "ephemeral")
		t.ok(string.find(sys.text, "Breathes fire", 1, true) ~= nil, "few-shot from Library")
		t.ok(string.find(sys.text, "| Colossal | 8-10 |", 1, true) ~= nil, "balance bands")
		t.ok(string.find(sys.text, "swamp ogre toenail", 1, true) ~= nil, "brand stripping example")
		t.ok(string.find(sys.text, "Materials:", 1, true) ~= nil, "materials")
		local n = 0
		for _ in string.gmatch(sys.text, '{"key":') do
			n += 1
		end
		t.ok(n >= 12, "worked examples: " .. n)
	end)

	t.test("json_schema output mode, and auto-switch when forced tool_choice is rejected", function()
		local ctx = M.setup(t, { config = function(C)
			C.AI.Anthropic.OutputMode = "json_schema"
		end })
		local seen
		ctx.useAI(function(keys, req, body)
			seen = body
			return ctx.resultsJson(keys)
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "lampwing", { timeout = 2 })
		t.eq(r.source, "AI")
		t.eq(seen.output_config.format.type, "json_schema")
		t.eq(seen.tools, nil)
		-- tool mode rejected by the API -> retried as json_schema
		local ctx2 = M.setup(t)
		local modes = {}
		ctx2.httpHandler = function(req)
			local body = M.jsonDecode(req.Body)
			table.insert(modes, if body.tools then "tool" else "json")
			if body.tools then
				return { Success = false, StatusCode = 400, Headers = {}, Body = '{"error":{"message":"tool_choice: not supported"}}' }
			end
			local keys = M.jsonDecode(string.match(body.messages[1].content, "\n(.*)$"))
			return { Success = true, StatusCode = 200, Headers = {}, Body = M.jsonEncode({
				content = { { type = "text", text = ctx2.resultsJson(keys) } }, stop_reason = "end_turn",
				usage = { input_tokens = 10, output_tokens = 10 } }) }
		end
		local r2 = ctx2.Interpreter.interpretAsync(ctx2.player(), "wobblefish", { timeout = 2 })
		t.eq(r2.source, "AI")
		t.eq(modes[1], "tool")
		t.eq(modes[2], "json")
	end)

	t.test("AI output carries material, mood, secondaryElement, accents, specialised body plan", function()
		local ctx = M.setup(t)
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys, function()
				return { material = "cheese", mood = "Angry", secondaryElement = "Ice", element = "Fire",
					accents = { "scowl", "steam" }, bodyPlan = "Dragon" }
			end)
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "cheesewyrm", { timeout = 2 })
		t.eq(r.material, "cheese")
		t.eq(r.mood, "Angry")
		t.eq(r.secondaryElement, "Ice")
		t.eq(r.visual.bodyPlan, "Dragon")
		t.eq(#r.visual.accents, 2)
	end)

	t.test("OpenAI-compatible adapter: Bearer secret via AddPrefix, parses choices", function()
		local ctx = M.setup(t, { config = function(C)
			C.AI.Provider = "OpenAICompatible"
			C.AI.OpenAICompatible.Endpoint = "https://llm.example.com/v1/chat/completions"
			C.AI.OpenAICompatible.Model = "some-model"
		end })
		ctx.AI.init()
		local seen
		ctx.httpHandler = function(req)
			seen = req
			local body = M.jsonDecode(req.Body)
			local keys = M.jsonDecode(string.match(body.messages[2].content, "\n(.*)$"))
			return { Success = true, StatusCode = 200, Headers = {}, Body = M.jsonEncode({
				choices = { { message = { content = ctx.resultsJson(keys) }, finish_reason = "stop" } },
				usage = { prompt_tokens = 10, completion_tokens = 5 },
			}) }
		end
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "wobblet", { timeout = 2 })
		t.eq(r.source, "AI")
		t.eq(seen.Headers.Authorization.__value, "Bearer sk-test")
		t.eq(seen.Headers.Authorization.__secret, "ANTHROPIC_API_KEY")
	end)

	t.test("batching: words queued together go in one request", function()
		local ctx = M.setup(t)
		local batches = {}
		ctx.useAI(function(keys)
			table.insert(batches, #keys)
			return ctx.resultsJson(keys)
		end)
		local done = 0
		for _, w in { "aaplor", "bezzle", "cronky", "dribbit" } do
			ctx.task.spawn(function()
				ctx.Interpreter.interpretAsync(ctx.player(), w, { timeout = 2 })
				done += 1
			end)
		end
		local waited = 0
		while done < 4 and waited < 3 do
			ctx.task.wait(0.05)
			waited += 0.05
		end
		t.eq(done, 4)
		t.eq(#batches, 1, "one request")
		t.eq(batches[1], 4)
	end)

	t.test("retries transient 529 with backoff, then succeeds", function()
		local ctx = M.setup(t)
		local n = 0
		ctx.useAI(function(keys)
			n += 1
			if n == 1 then
				return nil, 529
			end
			return ctx.resultsJson(keys)
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "snorkel beast", { timeout = 2 })
		t.eq(r.source, "AI")
		t.eq(n, 2)
	end)

	t.test("circuit breaker opens after repeated failures, then half-open probe closes it", function()
		local ctx = M.setup(t, { config = function(C)
			C.AI.MaxRetries = 0
			C.AI.Circuit.FailureThreshold = 2
		end })
		local fail = true
		ctx.useAI(function(keys)
			if fail then
				return nil, 500
			end
			return ctx.resultsJson(keys)
		end)
		local p = ctx.player()
		ctx.Interpreter.interpretAsync(p, "qwopal", { timeout = 1 })
		ctx.Interpreter.interpretAsync(p, "frindle", { timeout = 1 })
		t.eq(ctx.AI.Circuit.state(), "Open")
		t.eq(ctx.AI.available(), false)
		local calls = ctx.aiCalls
		local r = ctx.Interpreter.interpretAsync(p, "plinko", { timeout = 1 })
		t.eq(r.source, "Fallback", "library-only while open")
		t.eq(ctx.aiCalls, calls, "no request while open")
		ctx.task.wait(0.35) -- cooldown 0.3 in tests
		t.eq(ctx.AI.Circuit.state(), "HalfOpen")
		fail = false
		local r2 = ctx.Interpreter.interpretAsync(p, "plinko", { timeout = 2 })
		t.eq(r2.source, "AI")
		t.eq(ctx.AI.Circuit.state(), "Closed")
	end)

	t.test("401 pauses AI (auth cooldown) and never retries", function()
		local ctx = M.setup(t)
		ctx.useAI(function()
			return nil, 401
		end)
		ctx.Interpreter.interpretAsync(ctx.player(), "zappadoo", { timeout = 1 })
		t.eq(ctx.aiCalls, 1)
		t.eq(ctx.AI.Circuit.state(), "Open")
	end)

	t.test("Studio play-solo without a secret: Mock provider, loud log, no HTTP", function()
		local ctx = M.setup(t, { secrets = {}, isStudio = true })
		t.eq(ctx.AI.isMock(), true)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "snorklewump", { timeout = 2 })
		t.eq(r.source, "AI")
		t.ok(string.find(r.flavourText, "[MOCK]", 1, true) ~= nil, "obviously fake")
		t.eq(#ctx.requests, 0)
		local loud = false
		for _, l in ctx.logs do
			if string.find(l, "MOCK AI PROVIDER ACTIVE", 1, true) then
				loud = true
			end
		end
		t.ok(loud, "loud log line")
	end)

	t.test("no secret on a live server: AI disabled cleanly, library still works", function()
		local ctx = M.setup(t, { secrets = {} })
		t.eq(ctx.AI.hasKey(), false)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "dragon")
		t.eq(r.id, "dragon")
		local r2 = ctx.Interpreter.interpretAsync(ctx.player(), "glorbo")
		t.eq(r2.source, "Fallback")
		t.eq(#ctx.requests, 0)
	end)

	t.test("daily spend cap from returned token usage (MemoryStore counter, cross-server)", function()
		local ctx = M.setup(t, { config = function(C)
			C.AI.DailyBudgetUSD = 0.00035 -- one call costs 1000*0.1e-6 + 200*0.5e-6 = 0.0002
		end })
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		ctx.Interpreter.interpretAsync(ctx.player(), "moonwhale", { timeout = 2 })
		t.ok(math.abs(ctx.AI.Cost.todayUsd() - 0.0002) < 1e-9, "usd " .. ctx.AI.Cost.todayUsd())
		ctx.task.wait(0.05)
		local key = "spend:" .. ctx.Runtime.dayKey()
		t.eq(ctx.maps.WordEngine_WordCacheHot_v1.data[key], 200, "micro-USD counter in MemoryStore")
		-- another server spent too: refresh picks it up
		ctx.maps.WordEngine_WordCacheHot_v1.data[key] = 300
		ctx.AI.Cost.refreshSpend()
		t.ok(math.abs(ctx.AI.Cost.todayUsd() - 0.0003) < 1e-9, "global " .. ctx.AI.Cost.todayUsd())
		ctx.Interpreter.interpretAsync(ctx.player(), "sunbadger", { timeout = 2 })
		t.eq(ctx.AI.Cost.overBudget(), true)
		local calls = ctx.aiCalls
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "starmoose", { timeout = 1 })
		t.eq(ctx.aiCalls, calls, "no calls over budget")
		t.eq(r.source, "Fallback")
		local s = ctx.Interpreter.stats()
		t.ok(s.fallbackRate > 0, "fallback rate tracked")
		t.ok(s.avgAiLatencyMs >= 0 and s.aiCalls == 2, "AI calls/day")
		t.ok(s.ai.overBudget, "status")
	end)

	t.test("live kill switch: setEnabled persists, broadcasts, and stops AI; other servers flip", function()
		local ctx = M.setup(t)
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys)
		end)
		ctx.AI.startLoops()
		t.ok(ctx.AI.setEnabled(false, 42), "persisted")
		t.eq(ctx.stores.WordEngine_Control_v1.data.ai.aiEnabled, false)
		t.eq(ctx.published[1].topic, "WordEngineControl")
		t.eq(ctx.AI.isEnabled(), false)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "zorbleflux", { timeout = 1 })
		t.eq(r.source, "Fallback")
		t.eq(ctx.aiCalls, 0)
		t.eq(ctx.Interpreter.interpretAsync(ctx.player(), "dragon").id, "dragon", "library still works")
		-- a message from another server turns it back on
		ctx.subscriber({ Data = { aiEnabled = true } })
		t.eq(ctx.AI.isEnabled(), true)
		-- the poll path reads the DataStore
		ctx.stores.WordEngine_Control_v1.data.ai = { aiEnabled = false }
		ctx.AI.pollControl()
		t.eq(ctx.AI.isEnabled(), false)
		ctx.AI.init()
	end)

	t.test("refusal: model refuses -> fallback and cached as refused", function()
		local ctx = M.setup(t)
		ctx.useAI(function(keys)
			return M.jsonEncode({ results = { { key = keys[1], refused = true, id = "glitter blob" } } })
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "naughtyword", { timeout = 2 })
		t.eq(r.source, "Fallback")
		local calls = ctx.aiCalls
		ctx.Interpreter.interpretAsync(ctx.player(), "naughtyword", { timeout = 2 })
		t.eq(ctx.aiCalls, calls, "refusal cached")
	end)

	t.test("API stop_reason refusal on a batch isolates words", function()
		local ctx = M.setup(t)
		ctx.useAI(function(keys)
			for _, k in keys do
				if k == "badthing" then
					return "", 200, nil, { stop_reason = "refusal" }
				end
			end
			return ctx.resultsJson(keys)
		end)
		local results = {}
		for _, w in { "badthing", "goodthing" } do
			ctx.task.spawn(function()
				results[w] = ctx.Interpreter.interpretAsync(ctx.player(), w, { timeout = 2 })
			end)
		end
		local waited = 0
		while (results.badthing == nil or results.goodthing == nil) and waited < 3 do
			ctx.task.wait(0.05)
			waited += 0.05
		end
		t.eq(results.goodthing.source, "AI")
		t.eq(results.badthing.source, "Fallback")
	end)

	t.test("AI fixes a typo of a library word -> library entry with AI correction", function()
		local ctx = M.setup(t)
		ctx.useAI(function(keys)
			return ctx.resultsJson(keys, function()
				return { id = "dragon", corrected = "dragon" }
			end)
		end)
		local r = ctx.Interpreter.interpretAsync(ctx.player(), "drgoan", { timeout = 2 })
		t.eq(r.id, "dragon")
		t.eq(r.flavourText, "Breathes fire. Hoards loot. Judges you.")
		t.ok(r.correction and r.correction.method == "AI", "correction")
		t.eq(r.correction.to, "dragon")
	end)
end
