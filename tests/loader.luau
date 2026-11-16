-- Lune loader that emulates Roblox's `script` + `require(instance)` for files under src/.
-- Usage: local load = require("./loader"); local Schema = load("src/Shared/Schema")
local fs = require("@lune/fs")
local luau = require("@lune/luau")

local cache: { [string]: any } = {}

-- Pre-scan the tree once: fs calls yield, and yielding inside __index metamethods is not allowed.
local files: { [string]: boolean } = {}
local dirs: { [string]: { string } } = {}
local function scan(dir: string)
	local children = {}
	dirs[dir] = children
	for _, n in fs.readDir(dir) do
		local p = dir .. "/" .. n
		if fs.isDir(p) then
			scan(p)
			table.insert(children, n)
		elseif string.match(n, "%.luau?$") then
			files[p] = true
			local name = string.gsub(n, "%.luau?$", "")
			if name ~= "init" then
				table.insert(children, name)
			end
		end
	end
	table.sort(children)
end
for _, root in { "src", "testplace", "tests" } do
	if fs.isDir(root) then
		scan(root)
	end
end

local function resolveFile(path: string): string?
	if files[path .. ".luau"] then
		return path .. ".luau"
	elseif files[path .. ".lua"] then
		return path .. ".lua"
	elseif dirs[path] and files[path .. "/init.luau"] then
		return path .. "/init.luau"
	end
	return nil
end

local makeInstance

local function loadPath(path: string): any
	if cache[path] ~= nil then
		return cache[path]
	end
	local file = resolveFile(path)
	assert(file, "loader: no module at " .. path)
	local isInit = string.match(file, "/init%.luau$") ~= nil
	local env = setmetatable({}, { __index = getfenv(1) })
	env.script = makeInstance(path, isInit)
	env.require = function(target: any)
		if type(target) == "table" and rawget(target, "__path") then
			return loadPath(rawget(target, "__path"))
		end
		return require(target)
	end
	local fn = luau.load(fs.readFile(file), { debugName = file, environment = env })
	local result = fn()
	cache[path] = result
	return result
end

-- A fake Instance: .Parent, :FindFirstChild, :WaitForChild, indexing children by name.
makeInstance = function(path: string, isFolder: boolean?)
	local inst = { __path = path }
	local function childPath(name: string): string
		return path .. "/" .. name
	end
	return setmetatable(inst, {
		__index = function(_, key)
			if key == "Parent" then
				local parent = string.match(path, "^(.*)/[^/]+$")
				return makeInstance(parent or ".", true)
			elseif key == "Name" then
				return string.match(path, "([^/]+)$")
			elseif key == "FindFirstChild" or key == "WaitForChild" then
				return function(_, name)
					local base = if isFolder then path else path
					local p = base .. "/" .. name
					if resolveFile(p) or dirs[p] ~= nil then
						return makeInstance(p, dirs[p] ~= nil)
					end
					return nil
				end
			elseif key == "GetChildren" then
				return function()
					local out = {}
					for _, name in dirs[path] or {} do
						table.insert(out, makeInstance(path .. "/" .. name, dirs[path .. "/" .. name] ~= nil))
					end
					table.sort(out, function(a, b) return a.__path < b.__path end)
					return out
				end
			end
			local p = childPath(key)
			if resolveFile(p) or dirs[p] ~= nil then
				return makeInstance(p, dirs[p] ~= nil)
			end
			error("loader: " .. path .. " has no child " .. tostring(key))
		end,
	})
end

return loadPath
