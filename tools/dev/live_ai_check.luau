-- Live AI path check (spends a fraction of a cent on the game's Anthropic key).
-- Run: python3 tools/cloud_exec.py tools/dev/live_ai_check.luau
local SSS = game:GetService("ServerScriptService")
local S = require(SSS:WaitForChild("WordEngineServer", 10))
local out = { errors = {}, first = {}, second = {} }
local ok, err = pcall(function() S.start({ game = "Defend", remotes = false }) end)
if not ok then table.insert(out.errors, "start: " .. tostring(err)) end
local Interpreter = require(SSS.WordEngineServer.Interpreter)
local phrases = { "bureaucracy", "homework", "wifi outage", "tax audit" }
local function pass(into)
	for _, p in phrases do
		local t0 = os.clock()
		local ok2, r, h = pcall(Interpreter.interpretAsync, nil, p, { timeout = 20 })
		if not ok2 then table.insert(out.errors, p .. ": " .. tostring(r)) continue end
		local upgraded
		if h and h.upgraded and r.source ~= "AI" and r.source ~= "Cache" then
			local done = false
			h.upgraded:Connect(function(nr) upgraded = nr; done = true end)
			local t = os.clock()
			while not done and os.clock() - t < 20 do task.wait(0.25) end
		end
		local f = upgraded or r
		table.insert(into, string.format("%s -> %s [%s] %s/%s/%s p%d mat=%s mood=%s %.2fs | %s", p, f.canonical, f.source,
			f.category, f.shape, f.size, f.power, tostring(f.material), f.mood, os.clock() - t0, f.flavourText))
	end
end
pass(out.first)
task.wait(2)
pass(out.second)
pcall(function() out.stats = S.stats() end)
return out
