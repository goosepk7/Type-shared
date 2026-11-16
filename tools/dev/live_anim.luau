-- Does Summon.animate move parts on a real (headless) server? Reports motors and parts that changed.
local RS = game:GetService("ReplicatedStorage")
local WE = require(RS:WaitForChild("WordEngine", 10))
local out = {}
for _, word in { "tornado", "dragon" } do
	for _, anchored in { true, false } do
		local r = WE.Resolver.resolveLocal(word)
		local model = WE.Summon.build(r, { style = "Spectral", anchored = anchored, parent = workspace, cframe = CFrame.new(0, 30, 0) })
		local anim = WE.Summon.animate(model, r)
		anim:play("Idle")
		local before, tb = {}, {}
		for _, d in model:GetDescendants() do
			if d:IsA("BasePart") then before[d] = d.CFrame elseif d:IsA("Motor6D") then tb[d] = d.Transform end
		end
		task.wait(0.6)
		local moved, parts, motors, tmoved, anch = 0, 0, 0, 0, 0
		for p, cf in before do parts += 1 if p.Anchored then anch += 1 end if (p.CFrame.Position - cf.Position).Magnitude > 1e-3 or p.CFrame.LookVector:Dot(cf.LookVector) < 0.9999 then moved += 1 end end
		for m, t in tb do motors += 1 if m.Transform ~= t then tmoved += 1 end end
		table.insert(out, string.format("%s anchored=%s parts=%d anchoredParts=%d partsMoved=%d motors=%d transformsChanged=%d", word, tostring(anchored), parts, anch, moved, motors, tmoved))
		anim:destroy() model:Destroy()
	end
end
return out
