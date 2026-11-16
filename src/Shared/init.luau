--!strict
-- WordEngine facade. Modules load lazily so the client never pays for the word library
-- until it is first needed (e.g. the typing box opens).

local WordEngine = {}
WordEngine.VERSION = "0.1.0"

local loaded: { [string]: any } = {}
local root = script

setmetatable(WordEngine, {
	__index = function(_, key: string)
		local cached = loaded[key]
		if cached ~= nil then
			return cached
		end
		local child = root:FindFirstChild(key)
		if child == nil then
			error(("WordEngine has no module %q"):format(tostring(key)), 2)
		end
		local mod = require(child :: any)
		loaded[key] = mod
		return mod
	end,
})

return WordEngine
