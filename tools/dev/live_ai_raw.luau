-- Raw Anthropic call diagnostics (output mode x schema order x token budget). Never returns the key.
local SSS = game:GetService("ServerScriptService")
local Http = game:GetService("HttpService")
local S = require(SSS:WaitForChild("WordEngineServer", 10))
pcall(function() S.start({ game = "Defend", remotes = false }) end)
local AIroot = SSS.WordEngineServer.AI
local Prompt = require(AIroot.Prompt)
local Config = require(game:GetService("ReplicatedStorage").WordEngine.Config)
local pcfg = Config.AI.Anthropic
local secret = Http:GetSecret("ANTHROPIC_API_KEY")
local keys = { "bureaucracy", "homework", "wifi outage", "tax audit", "kazoo orchestra" }
local ORDER = { "key", "refused", "id", "corrected", "category", "shape", "element", "secondaryElement", "material",
	"size", "mood", "bodyPlan", "silhouetteHint", "behaviours", "power", "speed", "durability", "primaryColour",
	"secondaryColour", "motionHint", "soundHint", "accents", "tags", "flavourText", "confidence" }
local function orderedSchema()
	local item = Prompt.schema().properties.results.items
	local props, req = {}, {}
	for _, k in ORDER do
		table.insert(props, '"' .. k .. '":' .. Http:JSONEncode(item.properties[k]))
		table.insert(req, '"' .. k .. '"')
	end
	local itemJson = '{"type":"object","properties":{' .. table.concat(props, ",") .. '},"required":[' .. table.concat(req, ",") .. '],"additionalProperties":false}'
	return '{"type":"object","properties":{"results":{"type":"array","items":' .. itemJson .. '}},"required":["results"],"additionalProperties":false}'
end
local SLOT = "@@SLOT@@"
local function run(mode, ordered, maxTokens)
	local schema = if ordered then SLOT else Prompt.schema()
	local body = {
		model = pcfg.Model, max_tokens = maxTokens,
		system = { { type = "text", text = Prompt.system(), cache_control = { type = "ephemeral" } } },
		messages = { { role = "user", content = Prompt.user(keys) } },
		output_config = { effort = "low" }, thinking = { type = "disabled" },
	}
	if mode == "tool" then
		body.tools = { { name = "submit_words", description = "Submit exactly one interpreted result per input phrase.", input_schema = schema, strict = true } }
		body.tool_choice = { type = "tool", name = "submit_words" }
	else
		body.output_config.format = { type = "json_schema", schema = schema }
	end
	local enc = Http:JSONEncode(body)
	if ordered then
		local a, b = string.find(enc, '"' .. SLOT .. '"', 1, true)
		enc = string.sub(enc, 1, a - 1) .. orderedSchema() .. string.sub(enc, b + 1)
	end
	local t0 = os.clock()
	local ok, resp = pcall(function()
		return Http:RequestAsync({ Url = pcfg.Endpoint, Method = "POST", Headers = { ["x-api-key"] = secret, ["anthropic-version"] = pcfg.ApiVersion, ["Content-Type"] = "application/json" }, Body = enc })
	end)
	local r = { mode = mode, ordered = ordered, maxTokens = maxTokens, secs = math.floor((os.clock() - t0) * 10) / 10 }
	if not ok then r.err = tostring(resp) return r end
	r.status = resp.StatusCode
	local d = Http:JSONDecode(resp.Body)
	if resp.StatusCode ~= 200 then r.err = string.sub(resp.Body, 1, 400) return r end
	r.stop = d.stop_reason
	r.usage = { i = d.usage.input_tokens, o = d.usage.output_tokens, cr = d.usage.cache_read_input_tokens, cw = d.usage.cache_creation_input_tokens }
	local data
	for _, blk in d.content do
		if blk.type == "tool_use" then data = blk.input elseif blk.type == "text" then local okd, v = pcall(function() return Http:JSONDecode(blk.text) end) data = okd and v or nil end
	end
	local lines = {}
	if data and data.results then
		for _, it in data.results do
			table.insert(lines, string.format("%s | %s/%s/%s p%s s%s d%s c%s | %s", tostring(it.key), tostring(it.category), tostring(it.shape), tostring(it.bodyPlan), tostring(it.power), tostring(it.speed), tostring(it.durability), tostring(it.confidence), tostring(it.flavourText)))
		end
	end
	r.items = lines
	return r
end
local out = {}
for _, spec in { { "tool", false, 1450 }, { "tool", false, 2400 }, { "tool", true, 2400 }, { "json_schema", true, 2400 } } do
	table.insert(out, run(spec[1], spec[2], spec[3]))
end
return out
