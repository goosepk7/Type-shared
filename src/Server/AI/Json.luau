--!strict
-- Safe JSON handling for untrusted model output. decode never errors; extract finds the first
-- balanced JSON object/array in text that may be wrapped in prose or ``` fences; repair fixes the
-- usual LLM slips (trailing commas, smart quotes, unterminated output) before a second attempt.

local Runtime = require(script.Parent.Parent.Runtime)

local Json = {}

function Json.decode(s: any): any
	if type(s) ~= "string" or s == "" then
		return nil
	end
	return Runtime.jsonDecode(s)
end

-- Returns the first balanced {...} (or [...] when allowArray) substring, honouring strings and
-- escapes. If the text ends inside an object, returns the partial tail (repair may close it).
function Json.extract(text: string, allowArray: boolean?): (string?, boolean)
	local startPos: number? = nil
	for i = 1, #text do
		local c = string.sub(text, i, i)
		if c == "{" or (allowArray and c == "[") then
			startPos = i
			break
		end
	end
	if not startPos then
		return nil, false
	end
	local depth = 0
	local inString = false
	local escaped = false
	for i = startPos :: number, #text do
		local c = string.sub(text, i, i)
		if inString then
			if escaped then
				escaped = false
			elseif c == "\\" then
				escaped = true
			elseif c == '"' then
				inString = false
			end
		elseif c == '"' then
			inString = true
		elseif c == "{" or c == "[" then
			depth += 1
		elseif c == "}" or c == "]" then
			depth -= 1
			if depth == 0 then
				return string.sub(text, startPos :: number, i), true
			end
		end
	end
	return string.sub(text, startPos :: number), false
end

-- Close unbalanced strings/brackets of a truncated JSON prefix.
local function closeOpen(s: string): string
	local stack = {}
	local inString, escaped = false, false
	for i = 1, #s do
		local c = string.sub(s, i, i)
		if inString then
			if escaped then
				escaped = false
			elseif c == "\\" then
				escaped = true
			elseif c == '"' then
				inString = false
			end
		elseif c == '"' then
			inString = true
		elseif c == "{" then
			table.insert(stack, "}")
		elseif c == "[" then
			table.insert(stack, "]")
		elseif c == "}" or c == "]" then
			table.remove(stack)
		end
	end
	local out = s
	if inString then
		out ..= '"'
	end
	-- drop a dangling key or comma before closing
	out = string.gsub(out, ",%s*$", "")
	out = string.gsub(out, ',%s*"[^"]*"%s*:?%s*$', "")
	out = string.gsub(out, ":%s*$", ": null")
	for i = #stack, 1, -1 do
		out ..= stack[i]
	end
	return out
end

function Json.repairText(s: string): string
	local out = s
	out = string.gsub(out, "\u{201C}", '"')
	out = string.gsub(out, "\u{201D}", '"')
	out = string.gsub(out, "\u{2018}", "'")
	out = string.gsub(out, "\u{2019}", "'")
	out = string.gsub(out, ",(%s*[}%]])", "%1") -- trailing commas
	out = string.gsub(out, "%f[%w]NaN%f[%W]", "null")
	out = string.gsub(out, "%f[%w]Infinity%f[%W]", "null")
	return out
end

-- Best-effort parse of model text into a Lua table. Never errors; nil when hopeless.
function Json.parseLoose(text: any, allowArray: boolean?): any
	if type(text) ~= "string" then
		return nil
	end
	local direct = Json.decode(text)
	if type(direct) == "table" then
		return direct
	end
	local body, complete = Json.extract(text, allowArray)
	if not body then
		return nil
	end
	local v = Json.decode(body)
	if type(v) == "table" then
		return v
	end
	local fixed = Json.repairText(body)
	if not complete then
		fixed = closeOpen(fixed)
		fixed = Json.repairText(fixed)
	end
	v = Json.decode(fixed)
	if type(v) == "table" then
		return v
	end
	return nil
end

return Json
