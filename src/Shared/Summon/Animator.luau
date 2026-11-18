--!strict
-- Animator: procedural summon animation in Roblox. Pose math lives in Motion (pure, unit-tested); this module
-- writes Motor6D.Transform for every bone from ONE shared RunService.PreSimulation connection (Transform set
-- there is applied the same frame, after any Roblox Animator has written, so procedural motion wins) with
-- camera-distance LOD:
--   < SummonAnimLodNear  every frame      < SummonAnimLodFar  every 2nd frame
--   < SummonAnimCull     every 6th frame  beyond              paused (Transforms left as they are)
-- Motor6D.Transform does not replicate: run this on clients (each client animates what it sees).
--
--   local anim = Summon.animate(model, result)
--   anim:play("Idle" | "Move" | "Attack" | "Hit" | "Die" | "Spawn")   one-shots return to the last loop
--   anim:setSpeed(1.5)   anim:onFinished(fn)   anim:destroy()

local Motion = require(script.Parent.Motion)

local Animator = {}
Animator.__index = Animator

local active: { any } = {}
local conn: any = nil
local frame = 0

local function cfgLod(): (number, number, number)
	local ok, Config = pcall(function()
		return require(script.Parent.Parent.Config) :: any
	end)
	local v = (ok and Config and Config.Visual) or {}
	return v.SummonAnimLodNear or 120, v.SummonAnimLodFar or 260, v.SummonAnimCull or 600
end

local function blueprintFor(model: any, result: any): any
	local Instantiate = require(script.Parent.Instantiate) :: any
	local bp = Instantiate.blueprintOf[model]
	if bp == nil and result then
		-- not built in this session (e.g. cloned from a template): rebuild the pure blueprint for its rig
		local Summon = require(script.Parent) :: any
		bp = Summon.blueprint(result, { style = model:GetAttribute("Style") or "Solid" })
	end
	return bp
end

-- one rig per member model (formations animate every member with a phase offset)
local function collectRigs(model: any, bp: any): { any }
	local rigs = {}
	local members = {}
	if model:FindFirstChild("Root") then
		table.insert(members, model)
	else
		for _, c in model:GetChildren() do
			if c:IsA("Model") and c:FindFirstChild("Root") then
				table.insert(members, c)
			end
		end
	end
	for i, m in members do
		local motors = {}
		for _, d in m:GetDescendants() do
			if d:IsA("Motor6D") then
				motors[d.Name] = d
			end
		end
		table.insert(rigs, { model = m, motors = motors, root = m:FindFirstChild("Root"), offset = (i - 1) * 0.37 })
	end
	local _ = bp
	return rigs
end

local function step(dt: number)
	frame += 1
	local near, far, cull = cfgLod()
	local cam = workspace.CurrentCamera
	local camPos = cam and cam.CFrame.Position
	for i = #active, 1, -1 do
		local a = active[i]
		if a.destroyed or a.model.Parent == nil then
			table.remove(active, i)
		else
			a.time += dt * a.speed
			a.acc += dt
			local root = a.rigs[1] and a.rigs[1].root
			local d = if camPos and root then (root.Position - camPos).Magnitude else 0
			local every = if d < near then 1 elseif d < far then 2 elseif d < cull then 6 else 0
			if every > 0 and frame % every == 0 then
				a:_apply(a.acc)
				a.acc = 0
			end
		end
	end
	if #active == 0 and conn then
		conn:Disconnect()
		conn = nil
	end
end

-- Manual tick for headless checks: PreSimulation does not fire where RunService:IsRunning() is false
-- (Open Cloud Luau execution), so a simulation can call Animator.step(dt) itself to pose the rigs.
Animator.step = step

local function ensureLoop()
	if conn == nil then
		local RunService = game:GetService("RunService")
		conn = RunService.PreSimulation:Connect(step)
	end
end

function Animator.new(model: any, result: any?): any
	local bp = blueprintFor(model, result)
	local self = setmetatable({
		model = model,
		bp = bp,
		rig = bp and bp.rig or {},
		height = bp and bp.root and bp.root.size[2] or 5,
		mood = (result and result.mood) or model:GetAttribute("Mood") or "Neutral",
		rigs = collectRigs(model, bp),
		clip = "Idle",
		loop = "Idle",
		time = 0,
		acc = 0,
		speed = 1,
		destroyed = false,
		finished = {},
		seed = (bp and bp.seed or 0) % 97,
	}, Animator)
	table.insert(active, self)
	ensureLoop()
	return self
end

function Animator._apply(self: any, _dt: number)
	local clip = self.clip
	local authored = self.rig.clips and self.rig.clips[clip]
	local len = if authored and not authored.loop then authored.len else Motion.clipLength[clip] or 1
	if not Motion.looping[clip] and self.time >= len then
		if clip == "Die" then
			self.time = len
		else
			for _, fn in self.finished do
				task.spawn(fn, clip)
			end
			self.clip = self.loop
			self.time = 0
			clip = self.loop
		end
	end
	local CF = CFrame
	for _, r in self.rigs do
		local t = if Motion.looping[clip] then self.time + r.offset else self.time
		local pose = Motion.pose(self.rig, clip, t, { height = self.height, speed = 1, mood = self.mood, seed = self.seed + r.offset })
		for name, m in r.motors do
			local p = pose[name]
			if p then
				m.Transform = CF.new(p[1], p[2], p[3]) * CF.Angles(p[4], p[5], p[6])
			else
				m.Transform = CF.identity
			end
		end
	end
end

function Animator.play(self: any, clip: string)
	if Motion.clipLength[clip] == nil or self.destroyed then
		return
	end
	if self.clip == "Die" and clip ~= "Spawn" then
		return
	end
	if Motion.looping[clip] then
		self.loop = clip
	end
	self.clip = clip
	self.time = 0
end

function Animator.setSpeed(self: any, s: number)
	self.speed = math.clamp(tonumber(s) or 1, 0, 5)
end

function Animator.onFinished(self: any, fn: (string) -> ())
	table.insert(self.finished, fn)
end

function Animator.destroy(self: any)
	if self.destroyed then
		return
	end
	self.destroyed = true
	for _, r in self.rigs do
		for _, m in r.motors do
			if m.Parent then
				m.Transform = CFrame.identity
			end
		end
	end
end

Animator._active = active

return Animator
