--!strict
-- OpenAI-compatible chat completions adapter (any /v1/chat/completions endpoint). Optional: set
-- Config.AI.Provider = "OpenAICompatible" plus Config.AI.OpenAICompatible.Endpoint/Model.
-- Auth: Authorization: Bearer <Secret> built with Secret:AddPrefix (the key never becomes a string).

local Runtime = require(script.Parent.Parent.Parent.Runtime)
local Common = require(script.Parent.Common)

local OpenAICompatible = {}
OpenAICompatible.name = "OpenAICompatible"

function OpenAICompatible.build(cfg: any, secret: any, args: any): any
	local auth = secret
	local ok, prefixed = pcall(function()
		return secret:AddPrefix("Bearer ")
	end)
	if ok then
		auth = prefixed
	end
	local body = {
		model = cfg.Model,
		max_tokens = args.maxTokens,
		messages = {
			{ role = "system", content = args.system },
			{ role = "user", content = args.user },
		},
		response_format = { type = "json_object" },
	}
	return {
		Url = cfg.Endpoint,
		Method = "POST",
		Headers = { ["Authorization"] = auth, ["Content-Type"] = "application/json" },
		Body = Runtime.jsonEncode(body),
	}
end

function OpenAICompatible.parse(response: any): Common.Parsed
	if type(response) ~= "table" then
		return Common.empty("no response")
	end
	if not response.Success then
		return Common.httpError(response)
	end
	local data = Runtime.jsonDecode(response.Body or "")
	if type(data) ~= "table" then
		local p = Common.empty("bad body")
		p.retryable = true
		return p
	end
	local p = Common.empty("")
	local u = type(data.usage) == "table" and data.usage or {}
	p.usage = { input = tonumber(u.prompt_tokens) or 0, output = tonumber(u.completion_tokens) or 0, cacheRead = 0, cacheWrite = 0 }
	local choice = type(data.choices) == "table" and data.choices[1] or nil
	local msg = type(choice) == "table" and choice.message or nil
	if type(msg) == "table" and type(msg.refusal) == "string" and msg.refusal ~= "" then
		p.refusal = true
		p.err = "refusal"
		return p
	end
	local text = type(msg) == "table" and msg.content or nil
	if type(text) ~= "string" or text == "" then
		p.err = "no text"
		p.retryable = true
		return p
	end
	p.truncated = type(choice) == "table" and choice.finish_reason == "length"
	p.ok = true
	p.text = text
	return p
end

return OpenAICompatible
