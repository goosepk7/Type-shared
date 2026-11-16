--!strict
-- Anthropic Messages API adapter (POST /v1/messages). Raw HTTP: Roblox has no SDK.
--   headers: x-api-key (the Roblox Secret itself, never a string), anthropic-version, content-type
--   output:  OutputMode "tool" (default) = one strict tool whose input_schema is the WordResult batch
--            schema, forced with tool_choice {type="tool"} (Haiku 5.5 accepts forced tool use);
--            "json_schema" = output_config.format. If the API rejects forced tool_choice (400 naming
--            tool_choice), the adapter switches itself to json_schema for the rest of the session.
--   caching: cache_control on the (large, stable) system block; tools render before system, so the
--            tool schema is inside the cached prefix too.
--   usage:   input_tokens, cache_creation_input_tokens, cache_read_input_tokens, output_tokens.

local Runtime = require(script.Parent.Parent.Parent.Runtime)
local Common = require(script.Parent.Common)

local Anthropic = {}
Anthropic.name = "Anthropic"

local modeOverride: string? = nil

export type BuildArgs = { system: string, user: string, schema: any?, schemaJson: string?, maxTokens: number, toolName: string? }

local SCHEMA_SLOT = "@@WE_SCHEMA_SLOT@@"

function Anthropic.mode(cfg: any): string
	return modeOverride or cfg.OutputMode or "tool"
end

function Anthropic.resetMode()
	modeOverride = nil
end

function Anthropic.build(cfg: any, secret: any, args: BuildArgs): any
	local mode = Anthropic.mode(cfg)
	local outputConfig: { [string]: any } = { effort = cfg.Effort or "low" }
	-- schemaJson (ordered properties) is spliced in after encoding: JSONEncode would shuffle the key order.
	local schemaValue: any = if args.schemaJson then SCHEMA_SLOT else args.schema
	local body: { [string]: any } = {
		model = cfg.Model or "claude-haiku-5-5",
		max_tokens = args.maxTokens,
		system = { { type = "text", text = args.system, cache_control = { type = "ephemeral" } } },
		messages = { { role = "user", content = args.user } },
		output_config = outputConfig,
	}
	if args.schema then
		if mode == "tool" then
			local name = args.toolName or "submit_words"
			body.tools = { {
				name = name,
				description = "Submit exactly one interpreted result per input phrase.",
				input_schema = schemaValue,
				strict = true,
			} }
			body.tool_choice = { type = "tool", name = name }
		else
			outputConfig.format = { type = "json_schema", schema = schemaValue }
		end
	end
	if cfg.DisableThinking ~= false then
		body.thinking = { type = "disabled" }
	end
	local encoded = Runtime.jsonEncode(body)
	if encoded and args.schemaJson and args.schema then
		local a, b = string.find(encoded, '"' .. SCHEMA_SLOT .. '"', 1, true)
		if a and b then
			encoded = string.sub(encoded, 1, a - 1) .. args.schemaJson .. string.sub(encoded, b + 1)
		end
	end
	return {
		Url = cfg.Endpoint or "https://api.anthropic.com/v1/messages",
		Method = "POST",
		Headers = {
			["x-api-key"] = secret,
			["anthropic-version"] = cfg.ApiVersion or "2026-10-21",
			["Content-Type"] = "application/json",
		},
		Body = encoded,
	}
end

function Anthropic.parse(response: any): Common.Parsed
	if type(response) ~= "table" then
		return Common.empty("no response")
	end
	if not response.Success then
		local p = Common.httpError(response)
		local body = type(response.Body) == "string" and response.Body or ""
		if response.StatusCode == 400 and string.find(body, "tool_choice", 1, true) and modeOverride == nil then
			modeOverride = "json_schema"
			p.retryable = true
			p.err = "tool_choice unsupported; switching to json_schema"
			Runtime.log("warn", p.err)
		end
		return p
	end
	local data = Runtime.jsonDecode(response.Body or "")
	if type(data) ~= "table" then
		local p = Common.empty("bad body")
		p.retryable = true
		return p
	end
	local p = Common.empty("")
	local u = type(data.usage) == "table" and data.usage or {}
	p.usage = {
		input = tonumber(u.input_tokens) or 0,
		output = tonumber(u.output_tokens) or 0,
		cacheRead = tonumber(u.cache_read_input_tokens) or 0,
		cacheWrite = tonumber(u.cache_creation_input_tokens) or 0,
	}
	if data.stop_reason == "refusal" then
		p.refusal = true
		p.err = "refusal"
		return p
	end
	p.truncated = data.stop_reason == "max_tokens"
	local texts = {}
	if type(data.content) == "table" then
		for _, block in data.content do
			if type(block) == "table" then
				if block.type == "tool_use" and type(block.input) == "table" then
					p.ok = true
					p.data = block.input
					return p
				elseif block.type == "text" and type(block.text) == "string" then
					table.insert(texts, block.text)
				end
			end
		end
	end
	if #texts == 0 then
		p.err = "no output"
		p.retryable = true
		return p
	end
	p.ok = true
	p.text = table.concat(texts, "")
	return p
end

return Anthropic
