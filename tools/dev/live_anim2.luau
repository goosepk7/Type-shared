local RunService = game:GetService("RunService")
local n = { pre = 0, hb = 0, post = 0 }
local c1 = RunService.PreSimulation:Connect(function() n.pre += 1 end)
local c2 = RunService.Heartbeat:Connect(function() n.hb += 1 end)
local c3 = RunService.PostSimulation:Connect(function() n.post += 1 end)
task.wait(0.6)
c1:Disconnect() c2:Disconnect() c3:Disconnect()
n.running = RunService:IsRunning()
n.server = RunService:IsServer()
return n
