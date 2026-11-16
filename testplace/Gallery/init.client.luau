--!strict
-- Summon gallery (Roblox visual QA, client). The in-engine twin of tools/gallery: lays out a grid of random
-- "base x material x modifier" phrases plus every signature, Solid and Spectral side by side, animates each one,
-- and labels flagged builds (same heuristics as tools/gallery) so problems are visible in real lighting.
--
-- Mount: map this folder into StarterPlayerScripts (e.g. "SummonGallery": { "$path": "testplace/Gallery" } in
-- test.project.json). Keys: G = rebuild with a new seed, M = cycle Move/Idle, F = play Attack on all,
-- H = Hit, P = Spawn. Uses only WordEngine modules; nothing is sent to the server.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local WordEngine = require(ReplicatedStorage:WaitForChild("WordEngine")) :: any
local Summon = WordEngine.Summon
local Library = WordEngine.Library
local Modifiers = WordEngine.Modifiers
local SummonModule = (ReplicatedStorage:WaitForChild("WordEngine") :: any).Summon
local Rng = require(SummonModule.Rng) :: any
local Instantiate = require(SummonModule.Instantiate) :: any

local COUNT = 48 -- phrases per page (x2 styles)
local SPACING = 16
local COLS = 8

local folder = Instance.new("Folder")
folder.Name = "SummonGallery"
folder.Parent = workspace

local animators: { any } = {}
local moving = false

local function clear()
	for _, a in animators do
		a:destroy()
	end
	table.clear(animators)
	folder:ClearAllChildren()
end

local function label(model: Model, text: string, flagged: boolean)
	local root = model.PrimaryPart
	if root == nil then
		return
	end
	local bb = Instance.new("BillboardGui")
	bb.Size = UDim2.fromOffset(220, 40)
	bb.StudsOffsetWorldSpace = Vector3.new(0, root.Size.Y / 2 + 1.5, 0)
	bb.AlwaysOnTop = false
	bb.MaxDistance = 120
	local tl = Instance.new("TextLabel")
	tl.Size = UDim2.fromScale(1, 1)
	tl.BackgroundTransparency = 1
	tl.TextScaled = true
	tl.Font = Enum.Font.GothamBold
	tl.TextColor3 = if flagged then Color3.fromRGB(255, 110, 100) else Color3.new(1, 1, 1)
	tl.TextStrokeTransparency = 0.4
	tl.Text = text
	tl.Parent = bb
	bb.Adornee = root
	bb.Parent = model
end

-- same heuristics as tools/gallery (kept short: parts, face, contrast)
local function flags(r: any, bp: any): { string }
	local out = {}
	if #bp.parts < 5 then
		table.insert(out, "few-parts")
	end
	local alive = r.category == "Creature" or r.category == "Person" or (r.mood and r.mood ~= "Neutral")
	if alive and r.visual.bodyPlan ~= "Swarm" then
		local eyes = false
		for _, p in bp.parts do
			if p.role == "eye" then
				eyes = true
			end
		end
		if not eyes then
			table.insert(out, "no-face")
		end
	end
	if #Summon.check(bp) > 0 then
		table.insert(out, "zfight")
	end
	return out
end

local function phrases(seed: number): { any }
	local rng = Rng.new(seed)
	local ids = Library.ids()
	local mats = {}
	for w, id in Library.materialWords() do
		if w == id then
			table.insert(mats, id)
		end
	end
	table.sort(mats)
	local mods = {}
	for _, m in Modifiers.all() do
		if m.kind == "Mood" or m.kind == "Quality" or m.kind == "Element" then
			table.insert(mods, m)
		end
	end
	local out = {}
	for _ = 1, COUNT do
		local base = Library.get(ids[rng:int(1, #ids)])
		if base then
			local list = {}
			if rng:chance(0.85) then
				table.insert(list, Modifiers.material(mats[rng:int(1, #mats)]))
			end
			table.insert(list, mods[rng:int(1, #mods)])
			local r = Modifiers.apply(base, list)
			r.count = 1
			r.phrase = Modifiers.canonical(base.id, list)
			table.insert(out, r)
		end
	end
	return out
end

local function place(r: any, style: string, slot: number, seed: number)
	local ok, err = pcall(function()
		local bp = Summon.blueprint(r, { style = style, seed = seed })
		local model = Summon.buildBlueprint(bp, { anchored = true })
		local col = (slot - 1) % COLS
		local row = math.floor((slot - 1) / COLS)
		local x = col * SPACING + (if style == "Spectral" then SPACING * COLS + 24 else 0)
		Instantiate.moveModel(model, CFrame.new(x, 0, row * SPACING) * CFrame.Angles(0, math.pi, 0))
		model.Parent = folder
		local f = flags(r, bp)
		label(model, (r.phrase or r.id) .. (if #f > 0 then " [" .. table.concat(f, ",") .. "]" else ""), #f > 0)
		local anim = Summon.animate(model, r)
		anim:play(if moving then "Move" else "Idle")
		table.insert(animators, anim)
	end)
	if not ok then
		warn("[SummonGallery] " .. tostring(r.phrase or r.id) .. ": " .. tostring(err))
	end
end

local seed = 1
local function rebuild()
	clear()
	local list = phrases(seed)
	local slot = 0
	for _, r in list do
		slot += 1
		place(r, "Solid", slot, slot)
		place(r, "Spectral", slot, slot)
		if slot % 8 == 0 then
			task.wait() -- spread instantiation over frames
		end
	end
	-- every signature on the last rows
	for _, id in Summon.signatures() do
		local base = Library.get(id)
		if base then
			slot += 1
			place(base, "Solid", slot, 1)
			place(base, "Spectral", slot, 1)
		end
	end
end

UserInputService.InputBegan:Connect(function(input, processed)
	if processed then
		return
	end
	if input.KeyCode == Enum.KeyCode.G then
		seed += 1
		rebuild()
	elseif input.KeyCode == Enum.KeyCode.M then
		moving = not moving
		for _, a in animators do
			a:play(if moving then "Move" else "Idle")
		end
	elseif input.KeyCode == Enum.KeyCode.F then
		for _, a in animators do
			a:play("Attack")
		end
	elseif input.KeyCode == Enum.KeyCode.H then
		for _, a in animators do
			a:play("Hit")
		end
	elseif input.KeyCode == Enum.KeyCode.P then
		for _, a in animators do
			a:play("Spawn")
		end
	end
end)

local _ = Players
rebuild()
