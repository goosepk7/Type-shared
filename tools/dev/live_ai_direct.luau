-- Direct AI provider check below the Safety/TextService layer (no players exist in an execution session).
local SSS = game:GetService("ServerScriptService")
local S = require(SSS:WaitForChild("WordEngineServer", 10))
pcall(function() S.start({ game = "Defend", remotes = false }) end)
local AI = require(SSS.WordEngineServer.AI)
local out = { results = {}, errors = {} }
local keys = { "bureaucracy", "homework", "wifi outage", "tax audit", "kazoo orchestra" }
local futs = {}
for _, k in keys do futs[k] = AI.request(k) end
for _, k in keys do
	local done, item, err = futs[k]:await(40)
	if done and item then
		local ok, js = pcall(function() return game:GetService("HttpService"):JSONEncode(item) end)
		table.insert(out.results, k .. " => " .. (ok and string.sub(js, 1, 500) or tostring(item)))
	else
		table.insert(out.errors, k .. ": " .. tostring(err) .. " done=" .. tostring(done))
	end
end
out.status = AI.status()
return out
