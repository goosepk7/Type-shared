--!strict
-- Instantiate: blueprint -> Roblox Model (DESIGN §8). Roblox-only stage; Summon.blueprint stays pure.
--
-- Model
--   Root            invisible PrimaryPart (bounding box), Anchored by default, CanCollide/CanTouch off, CanQuery on
--   Bone_<name>     invisible 0.05 stud joints; Motor6D chain Root -> Body -> ... (Animator drives .Transform)
--   <parts>         visible parts welded (Weld, fixed C0) to their bone; CanCollide/CanTouch/CanQuery off, Massless
--   AnimationController + Animator (so Roblox animations can also play on the rig)
-- FX: Highlight (Spectral rim), Trails on extremities, ParticleEmitters at sockets, one PointLight, and looping
-- Effects.play attachments (accents + material particles; stopped when the model is destroyed).
-- Formation (count > 1): a Model of member Models, leader's Root is the PrimaryPart.
--
-- opts: { anchored = true, collisionGroup = string?, parent = Instance?, cframe = CFrame?, effects = true,
--         loadMesh = true }. Instantiate.setCollisionGroupHook(fn(part)) lets the game assign groups centrally.

local Geom = require(script.Parent.Geom)

local Instantiate = {}

-- Roblox constructors, injectable for tests (Lune's @lune/roblox provides the same API).
local RT: any = nil
function Instantiate.setRuntime(rt: any)
	RT = rt
end
local function rt(): any
	if RT == nil then
		RT = {
			Instance = Instance, CFrame = CFrame, Vector3 = Vector3, Color3 = Color3, Enum = Enum,
			ColorSequence = ColorSequence, ColorSequenceKeypoint = ColorSequenceKeypoint,
			NumberSequence = NumberSequence, NumberSequenceKeypoint = NumberSequenceKeypoint, NumberRange = NumberRange,
		}
	end
	return RT
end

local collisionHook: ((any) -> ())? = nil
function Instantiate.setCollisionGroupHook(fn: ((any) -> ())?)
	collisionHook = fn
end

-- blueprint per built model (weak keys) for the Animator
Instantiate.blueprintOf = setmetatable({}, { __mode = "k" }) :: any

local function cf(f: { number }): any
	return rt().CFrame.new(f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], f[9], f[10], f[11], f[12])
end

local function v3(t: { number }): any
	return rt().Vector3.new(t[1], t[2], t[3])
end

local function c3(c: { number }?): any
	local col = c or { 0.6, 0.6, 0.6 }
	return rt().Color3.new(col[1], col[2], col[3])
end

local function material(name: string?): any
	local E = rt().Enum
	local ok, m = pcall(function()
		return (E.Material :: any)[name or "SmoothPlastic"]
	end)
	return if ok and m then m else E.Material.SmoothPlastic
end

-- Particle presets (built-in rbxasset textures, no uploads needed).
local PRESETS: { [string]: any } = {
	wisps = { tex = "rbxasset://textures/particles/smoke_main.dds", size = { 0.6, 1.4 }, life = { 1.2, 2 }, speed = { 0.6, 1.4 }, light = 1, tr = { 0.55, 1 }, up = true },
	embers = { tex = "rbxasset://textures/particles/sparkles_main.dds", size = { 0.25, 0.05 }, life = { 0.8, 1.6 }, speed = { 2, 4 }, light = 1, tr = { 0, 1 }, up = true },
	flame = { tex = "rbxasset://textures/particles/fire_main.dds", size = { 1.2, 0.2 }, life = { 0.3, 0.6 }, speed = { 6, 10 }, light = 1, tr = { 0.1, 1 }, forward = true },
	frost = { tex = "rbxasset://textures/particles/sparkles_main.dds", size = { 0.3, 0 }, life = { 1, 2 }, speed = { 0.4, 1 }, light = 0.6, tr = { 0.2, 1 } },
	sparks = { tex = "rbxasset://textures/particles/sparkles_main.dds", size = { 0.18, 0 }, life = { 0.2, 0.5 }, speed = { 5, 9 }, light = 1, tr = { 0, 1 } },
	bubbles = { tex = "rbxasset://textures/particles/sparkles_main.dds", size = { 0.3, 0.45 }, life = { 1.2, 2.2 }, speed = { 0.8, 1.6 }, light = 0.3, tr = { 0.3, 1 }, up = true },
	droplets = { tex = "rbxasset://textures/particles/sparkles_main.dds", size = { 0.2, 0.1 }, life = { 0.6, 1 }, speed = { 1, 2 }, light = 0.2, tr = { 0.2, 1 }, down = true },
	dust = { tex = "rbxasset://textures/particles/smoke_main.dds", size = { 0.5, 1.5 }, life = { 1, 2 }, speed = { 0.3, 0.8 }, light = 0, tr = { 0.6, 1 } },
	streaks = { tex = "rbxasset://textures/particles/sparkles_main.dds", size = { 0.12, 0 }, life = { 0.4, 0.8 }, speed = { 4, 7 }, light = 0.5, tr = { 0.3, 1 } },
	leaves = { tex = "rbxasset://textures/particles/sparkles_main.dds", size = { 0.3, 0.2 }, life = { 1.5, 2.5 }, speed = { 0.5, 1.2 }, light = 0, tr = { 0, 1 }, down = true },
	glints = { tex = "rbxasset://textures/particles/sparkles_main.dds", size = { 0.25, 0 }, life = { 0.5, 1 }, speed = { 0.2, 0.6 }, light = 1, tr = { 0, 1 } },
	smoke = { tex = "rbxasset://textures/particles/smoke_main.dds", size = { 0.8, 2 }, life = { 1.5, 2.5 }, speed = { 0.4, 1 }, light = 0, tr = { 0.5, 1 }, up = true },
	runes = { tex = "rbxasset://textures/particles/sparkles_main.dds", size = { 0.35, 0.1 }, life = { 1, 1.8 }, speed = { 0.3, 0.8 }, light = 1, tr = { 0, 1 }, up = true },
	sparkle = { tex = "rbxasset://textures/particles/sparkles_main.dds", size = { 0.3, 0 }, life = { 0.6, 1.2 }, speed = { 0.3, 1 }, light = 1, tr = { 0, 1 } },
	glitter = { tex = "rbxasset://textures/particles/sparkles_main.dds", size = { 0.2, 0 }, life = { 0.5, 1 }, speed = { 0.5, 1.5 }, light = 1, tr = { 0, 1 } },
}

local function numberSeq(a: number, b: number): any
	local R = rt()
	return R.NumberSequence.new({ R.NumberSequenceKeypoint.new(0, a), R.NumberSequenceKeypoint.new(1, b) })
end

local function colourSeq(cols: { any }?): any
	local R = rt()
	local list = cols or { { 1, 1, 1 } }
	if #list == 1 then
		return R.ColorSequence.new(c3(list[1]))
	end
	local kps = {}
	for i, c in list do
		table.insert(kps, R.ColorSequenceKeypoint.new((i - 1) / (#list - 1), c3(c)))
	end
	return R.ColorSequence.new(kps)
end

local function newPart(p: any): any
	local R = rt()
	local E = R.Enum
	local inst
	if p.shape == "Wedge" then
		inst = R.Instance.new("WedgePart")
	else
		inst = R.Instance.new("Part")
		if p.shape == "Ball" then
			inst.Shape = E.PartType.Ball
		elseif p.shape == "Cylinder" then
			inst.Shape = E.PartType.Cylinder
		else
			inst.Shape = E.PartType.Block
		end
	end
	inst.Name = p.name or "Part"
	inst.Size = v3(p.size)
	inst.CFrame = cf(p.cf)
	inst.Color = c3(p.colour)
	inst.Material = material(p.material)
	inst.Transparency = p.transparency or 0
	inst.CastShadow = p.castShadow ~= false
	inst.CanCollide = false
	inst.CanTouch = false
	inst.CanQuery = false
	inst.Massless = true
	inst.Anchored = false
	inst.TopSurface = E.SurfaceType.Smooth
	inst.BottomSurface = E.SurfaceType.Smooth
	if p.shape == "Ellipsoid" then
		local mesh = R.Instance.new("SpecialMesh")
		mesh.MeshType = E.MeshType.Sphere
		mesh.Parent = inst
	end
	if p.role then
		inst:SetAttribute("Role", p.role)
	end
	if p.swarmUnit then
		inst:SetAttribute("SwarmUnit", true)
	end
	if p.accent then
		inst:SetAttribute("Accent", true)
	end
	return inst
end

local function applyGroup(part: any, group: string?)
	if group then
		pcall(function()
			part.CollisionGroup = group
		end)
	end
	if collisionHook then
		pcall(collisionHook, part)
	end
end

-- Move a whole model by a world transform (PivotTo where available; part-wise otherwise, e.g. under Lune).
local function moveModel(model: any, transform: any)
	local ok = pcall(function()
		model:PivotTo(transform * model:GetPivot())
	end)
	if not ok then
		for _, d in model:GetDescendants() do
			if d:IsA("BasePart") then
				d.CFrame = transform * d.CFrame
			end
		end
	end
end
Instantiate.moveModel = moveModel

-- Build one member model at the origin (blueprint model space).
local function buildMember(bp: any, opts: any, name: string): (any, any)
	local R = rt()
	local model = R.Instance.new("Model")
	model.Name = name
	local root = R.Instance.new("Part")
	root.Name = "Root"
	root.Size = v3(bp.root.size)
	root.CFrame = cf(bp.root.cf)
	root.Transparency = 1
	root.CanCollide = false
	root.CanTouch = false
	root.CanQuery = true
	root.Anchored = opts.anchored ~= false
	root.CastShadow = false
	root.Parent = model
	applyGroup(root, opts.collisionGroup)
	model.PrimaryPart = root

	-- bones: invisible joints in a Motor6D chain (pure translation frames; poses are model-axis Euler angles)
	local boneParts: { [string]: any } = {}
	local bonePos: { [string]: { number } } = {}
	for _, b in bp.bones do
		bonePos[b.name] = b.pos
	end
	for _, b in bp.bones do
		local bpPart = R.Instance.new("Part")
		bpPart.Name = "Bone_" .. b.name
		bpPart.Size = R.Vector3.new(0.05, 0.05, 0.05)
		bpPart.CFrame = R.CFrame.new(b.pos[1], b.pos[2], b.pos[3])
		bpPart.Transparency = 1
		bpPart.CanCollide = false
		bpPart.CanTouch = false
		bpPart.CanQuery = false
		bpPart.Massless = true
		bpPart.CastShadow = false
		bpPart.Parent = model
		boneParts[b.name] = bpPart
		local parentPart = if b.parent and boneParts[b.parent] then boneParts[b.parent] else root
		local parentCf = if b.parent and bonePos[b.parent] then R.CFrame.new(bonePos[b.parent][1], bonePos[b.parent][2], bonePos[b.parent][3]) else root.CFrame
		local m6 = R.Instance.new("Motor6D")
		m6.Name = b.name
		m6.Part0 = parentPart
		m6.Part1 = bpPart
		m6.C0 = parentCf:Inverse() * bpPart.CFrame
		m6.C1 = R.CFrame.new()
		m6.Parent = parentPart
	end

	local partsByName: { [string]: any } = {}
	for _, p in bp.parts do
		local inst = newPart(p)
		local bone = boneParts[p.bone] or boneParts.Body or root
		local w = R.Instance.new("Weld")
		w.Name = "W"
		w.Part0 = bone
		w.Part1 = inst
		w.C0 = bone.CFrame:Inverse() * inst.CFrame
		w.C1 = R.CFrame.new()
		w.Parent = inst
		inst.Parent = model
		applyGroup(inst, opts.collisionGroup)
		partsByName[inst.Name] = inst
	end

	-- sockets as attachments on their bones
	local sockets: { [string]: any } = {}
	for sname, f in bp.sockets do
		local bname = bp.rig.socketBones and bp.rig.socketBones[sname] or "Body"
		local bone = boneParts[bname] or boneParts.Body or root
		local a = R.Instance.new("Attachment")
		a.Name = "Socket_" .. sname
		a.CFrame = bone.CFrame:Inverse() * cf(f)
		a.Parent = bone
		sockets[sname] = a
	end

	local fx = bp.fx or {}
	if fx.highlight then
		local h = R.Instance.new("Highlight")
		h.FillColor = c3(fx.highlight.fill)
		h.FillTransparency = fx.highlight.fillTransparency
		h.OutlineColor = c3(fx.highlight.outline)
		h.OutlineTransparency = fx.highlight.outlineTransparency
		h.DepthMode = R.Enum.HighlightDepthMode.Occluded
		h.Adornee = model
		h.Parent = model
	end
	for _, tr in fx.trails or {} do
		local part = partsByName[tr.part]
		if part then
			-- attachments across the part's longest axis
			local s = part.Size
			local axis = if s.X >= s.Y and s.X >= s.Z then R.Vector3.new(s.X * 0.45, 0, 0) elseif s.Y >= s.Z then R.Vector3.new(0, s.Y * 0.45, 0) else R.Vector3.new(0, 0, s.Z * 0.45)
			local a0, a1 = R.Instance.new("Attachment"), R.Instance.new("Attachment")
			a0.Position, a1.Position = axis, -axis
			a0.Parent, a1.Parent = part, part
			local t = R.Instance.new("Trail")
			t.Attachment0, t.Attachment1 = a0, a1
			t.Color = colourSeq(tr.colour)
			t.Transparency = numberSeq(0.25, 1)
			t.Lifetime = tr.lifetime or 0.35
			t.LightEmission = if bp.style == "Spectral" then 1 else 0.3
			t.FaceCamera = true
			t.Parent = part
		end
	end
	for i, e in fx.emitters or {} do
		local preset = PRESETS[e.preset] or PRESETS.glints
		local host = (e.part and partsByName[e.part]) or sockets[e.socket or "core"] or root
		local pe = R.Instance.new("ParticleEmitter")
		pe.Name = "Fx_" .. tostring(e.preset) .. i
		pe.Texture = preset.tex
		pe.Color = colourSeq(e.colour)
		pe.Rate = e.rate or 10
		pe.Size = numberSeq(preset.size[1] * (e.spread or 1) + preset.size[1] * 0.5, preset.size[2])
		pe.Transparency = numberSeq(preset.tr[1], preset.tr[2])
		pe.Lifetime = R.NumberRange.new(preset.life[1], preset.life[2])
		pe.Speed = R.NumberRange.new(preset.speed[1], preset.speed[2])
		pe.LightEmission = preset.light
		pe.SpreadAngle = R.Vector2 and R.Vector2.new(30, 30) or pe.SpreadAngle
		if preset.up then
			pe.EmissionDirection = R.Enum.NormalId.Top
			pe.Acceleration = R.Vector3.new(0, 1.5, 0)
		elseif preset.down then
			pe.EmissionDirection = R.Enum.NormalId.Bottom
			pe.Acceleration = R.Vector3.new(0, -6, 0)
		elseif preset.forward then
			pe.EmissionDirection = R.Enum.NormalId.Front
		end
		pe.Parent = host
	end
	for _, l in fx.lights or {} do
		local host = sockets[l.socket or "core"] or root
		local pl = R.Instance.new("PointLight")
		pl.Color = c3(l.colour)
		pl.Brightness = l.brightness or 1
		pl.Range = l.range or 8
		pl.Shadows = l.shadows == true
		pl.Parent = host
	end

	local ac = R.Instance.new("AnimationController")
	ac.Parent = model
	local an = R.Instance.new("Animator")
	an.Parent = ac

	model:SetAttribute("SummonId", bp.id)
	model:SetAttribute("Style", bp.style)
	model:SetAttribute("BodyPlan", bp.bodyPlan)
	model:SetAttribute("Builder", bp.builder)
	model:SetAttribute("Gait", bp.rig.gait or "static")
	model:SetAttribute("MaterialMotion", bp.rig.materialMotion or "")
	model:SetAttribute("Mood", bp.mood or "Neutral")
	model:SetAttribute("Parts", #bp.parts)
	return model, sockets
end

-- Looping attached effects via the shared Effects library (client only; pooled + LOD there).
local function playEffects(bp: any, model: any, sockets: { [string]: any }, opts: any)
	if opts.effects == false then
		return
	end
	local fxs = bp.fx and bp.fx.effects
	if fxs == nil or #fxs == 0 then
		return
	end
	local ok, Effects = pcall(function()
		return require(script.Parent.Parent.Effects) :: any
	end)
	if not ok or type(Effects) ~= "table" or type(Effects.play) ~= "function" then
		return
	end
	local handles = {}
	for _, e in fxs do
		local target = sockets[e.socket] or sockets.core or model.PrimaryPart
		local okPlay, h = pcall(Effects.play, e.id, { target = target, style = bp.style, element = bp.element, loop = true })
		if okPlay and h then
			table.insert(handles, h)
		end
	end
	model.Destroying:Connect(function()
		for _, h in handles do
			pcall(function()
				h:stop()
			end)
		end
	end)
end

-- Swap the procedural body for an uploaded mesh asset once it loads (InsertService:LoadAsset; server-side or
-- assets the place owns). Face/accent/material-detail/effect parts stay visible on top; on failure nothing changes.
local KEEP_ROLES = { eye = true, pupil = true, shine = true, mouth = true, brow = true, lid = true, blush = true, gem = true, glow = true, light = true, hat = true, held = true }
function Instantiate.attachMesh(model: any, bp: any, mesh: any)
	local ok, InsertService = pcall(function()
		return (game :: any):GetService("InsertService")
	end)
	if not ok or InsertService == nil or type(mesh) ~= "table" or not mesh.assetId then
		return
	end
	task.spawn(function()
		local okLoad, container = pcall(function()
			return InsertService:LoadAsset(mesh.assetId)
		end)
		if not okLoad or container == nil or model.Parent == nil then
			return
		end
		local src = container:FindFirstChildWhichIsA("Model") or container:FindFirstChildWhichIsA("BasePart", true)
		if src == nil then
			return
		end
		local R = rt()
		local body = model:FindFirstChild("Bone_Body") or model.PrimaryPart
		local root = model.PrimaryPart
		local meshModel = if src:IsA("Model") then src else (function()
			local m = R.Instance.new("Model")
			src.Parent = m
			return m
		end)()
		-- fit the mesh to the procedural bounds (same height), offset optional
		local _, size = meshModel:GetBoundingBox()
		local k = (mesh.scale or 1) * root.Size.Y / math.max(size.Y, 1e-3)
		pcall(function()
			meshModel:ScaleTo(k)
		end)
		local off = mesh.offset or { 0, 0, 0 }
		meshModel:PivotTo(root.CFrame * R.CFrame.new(off[1], off[2], off[3]))
		local keep = {}
		for _, r in mesh.keepRoles or {} do
			keep[r] = true
		end
		for _, d in meshModel:GetDescendants() do
			if d:IsA("BasePart") then
				d.Anchored = false
				d.CanCollide, d.CanTouch, d.CanQuery, d.Massless = false, false, false, true
				local w = R.Instance.new("WeldConstraint")
				w.Part0, w.Part1 = body, d
				w.Parent = d
			end
		end
		for _, d in model:GetChildren() do
			if d:IsA("BasePart") and d ~= root and not string.match(d.Name, "^Bone_") then
				local role = d:GetAttribute("Role")
				if not (KEEP_ROLES[role] or keep[role] or d:GetAttribute("Accent")) then
					d.Transparency = 1
				end
			end
		end
		meshModel.Name = "Mesh"
		meshModel.Parent = model
		container:Destroy()
		model:SetAttribute("MeshLoaded", true)
	end)
end

function Instantiate.build(bp: any, result: any?, opts: any?): any
	local o = opts or {}
	local R = rt()
	if result then
		bp.element = result.element
	end
	local top, sockets
	if bp.members and #bp.members > 1 then
		top = R.Instance.new("Model")
		top.Name = bp.id
		local leader, leaderSockets
		for i, f in bp.members do
			local m, s = buildMember(bp, o, bp.id .. "_" .. i)
			moveModel(m, cf(f))
			m.Parent = top
			Instantiate.blueprintOf[m] = bp
			if i == 1 then
				leader, leaderSockets = m, s
			end
			playEffects(bp, m, s, if i == 1 then o else { effects = false })
		end
		top.PrimaryPart = leader.PrimaryPart
		top:SetAttribute("SummonId", bp.id)
		top:SetAttribute("Members", #bp.members)
		sockets = leaderSockets
	else
		top, sockets = buildMember(bp, o, bp.id)
		playEffects(bp, top, sockets, o)
	end
	Instantiate.blueprintOf[top] = bp
	if o.cframe then
		moveModel(top, o.cframe)
	end
	if bp.meshAsset and o.loadMesh ~= false then
		Instantiate.attachMesh(top, bp, bp.meshAsset)
	end
	if o.parent then
		top.Parent = o.parent
	end
	return top
end

Instantiate._geom = Geom

return Instantiate
