-- Test runner: `lune run tests` (from repo root). Runs every tests/specs/*.spec.luau.
-- A spec returns function(t) with t.test(name, fn), t.eq(a, b, msg), t.ok(cond, msg).
local fs = require("@lune/fs")
local process = require("@lune/process")
local load = require("@self/loader")

local only = process.args[1]
local passed, failed = 0, 0
local failures = {}

local t = {}
function t.ok(cond, msg)
	if not cond then error(msg or "expected truthy", 2) end
end
function t.eq(a, b, msg)
	if a ~= b then
		error(string.format("%s: expected %s, got %s", msg or "eq", tostring(b), tostring(a)), 2)
	end
end
t.load = load

local files = fs.readDir("tests/specs")
table.sort(files)
for _, name in files do
	if string.match(name, "%.spec%.luau$") and (only == nil or string.find(name, only, 1, true)) then
		local spec = require("@self/specs/" .. string.gsub(name, "%.luau$", ""))
		local suite = string.gsub(name, "%.spec%.luau$", "")
		t.test = function(testName, fn)
			local ok, err = pcall(fn)
			if ok then
				passed += 1
			else
				failed += 1
				table.insert(failures, suite .. " > " .. testName .. ": " .. tostring(err))
			end
		end
		spec(t)
	end
end

for _, f in failures do
	print("FAIL " .. f)
end
print(string.format("%d passed, %d failed", passed, failed))
if failed > 0 then
	process.exit(1)
end
