-- One AI call, then the spend counters after the MemoryStore push has had time to land.
local SSS = game:GetService("ServerScriptService")
local S = require(SSS:WaitForChild("WordEngineServer", 10))
pcall(function() S.start({ game = (game.GameId == 10777140284) and "Wizard" or "Defend", remotes = false }) end)
local AI = require(SSS.WordEngineServer.AI)
local Cost = require(SSS.WordEngineServer.AI.Cost)
local f = AI.request("lost sock dimension")
local done, item, err = f:await(40)
task.wait(4)
return { done = done, err = err, flavour = item and item.flavourText, status = AI.status(), snapshot = Cost.snapshot() }
