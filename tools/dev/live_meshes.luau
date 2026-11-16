-- Loads the mesh pieces on a real server, then builds hero summons and counts MeshParts.
local RS = game:GetService("ReplicatedStorage")
local WE = require(RS:WaitForChild("WordEngine", 10))
local ML = require(RS.WordEngine.Meshes.MeshLibrary)
local t0 = os.clock()
WE.Summon.preloadMeshes()
local ready = ML.ready()
while not ready.isReady() and os.clock() - t0 < 150 do task.wait(0.5) end
local folder = RS:FindFirstChild("WE_Meshes")
local total = 0
for _ in ML.records() do total += 1 end
local out = { ready = ready.isReady(), secs = math.floor(os.clock() - t0), loaded = folder and #folder:GetChildren() or 0, manifest = total, failed = folder and folder:GetAttribute("Failed"), builds = {} }
for _, word in { "dragon", "tornado", "asteroid", "shark", "wolf" } do
	for _, style in { "Spectral", "Solid" } do
		local r = WE.Resolver.resolveLocal(word)
		local ok, model = pcall(WE.Summon.build, r, { style = style, parent = workspace })
		if ok then
			local parts, meshes = 0, 0
			for _, d in model:GetDescendants() do
				if d:IsA("BasePart") then parts += 1 if d:IsA("MeshPart") then meshes += 1 end end
			end
			local size = model:GetExtentsSize()
			table.insert(out.builds, string.format("%s %s parts=%d meshParts=%d extents=%.0fx%.0fx%.0f", word, style, parts, meshes, size.X, size.Y, size.Z))
			model:Destroy()
		else
			table.insert(out.builds, word .. " " .. style .. " ERROR " .. tostring(model))
		end
	end
end
return out
