--!nonstrict
-- Status visuals attached to a target (Effects.status(target, name, duration)). Emitters attach to the target's
-- root part (they follow for free); geometry (ice shell, stars, halo) follows via fx:follow or per-frame updates.

local Curves = require(script.Parent.Parent.Curves)
local Runtime = require(script.Parent.Parent.Runtime)
local Common = require(script.Parent.Common)

local S = {}

local function ctx(fx)
	local target = fx.params.target
	local root = Runtime.rootPart(target)
	local size = Runtime.extents(target)
	local w = math.max(size.X, size.Z)
	return root, size, w
end

local function headOffset(size): CFrame
	return CFrame.new(0, size.Y * 0.5 + 0.6, 0)
end

local function feetOffset(size): CFrame
	return CFrame.new(0, -size.Y * 0.5 + 0.2, 0)
end

-- Following CFrame for the root (fallback: effect origin).
local function rootCF(fx, root): CFrame
	if root and root.Parent then
		return root.CFrame
	end
	return fx:at()
end

function S.Burn(fx)
	local root, size, w = ctx(fx)
	fx:emitter("fire", root or fx:at(), { area = size * Vector3.new(0.7, 0.8, 0.7), shape = "Box", rate = 22, size = w / 3.2, speed = 0.7 })
	fx:emitter("embers", root or fx:at(), { area = size * 0.7, shape = "Box", rate = 8 })
	if fx.detail >= 2 then
		fx:emitter("smoke", root or fx:at(), { offset = headOffset(size), rate = 3, size = w / 4 })
	end
	local light = fx:light(root or fx:at(), fx:c(3), 1.5, w * 4)
	if light then
		fx:onUpdate(function(_, t)
			light.Brightness = 1.8 * Curves.flicker(t, fx.uid, 0.35) * fx.fade
		end)
	end
end

function S.Freeze(fx)
	local s = fx.scale
	local root, size, w = ctx(fx)
	local n = ({ 3, 5, 6 })[fx.detail] or 5
	local shards = {}
	for i = 1, n do
		local x, z = Curves.disc(i, n)
		local h = size.Y * fx:rand(0.55, 0.95)
		local thick = w * fx:rand(0.35, 0.55)
		local off = CFrame.new(x * w * 0.45, -size.Y * 0.5 + h * 0.45, z * w * 0.45)
			* CFrame.Angles(fx:rand(-0.35, 0.35), fx:rand(0, 6.28), fx:rand(-0.35, 0.35))
			* CFrame.Angles(0, math.pi / 4, 0)
		local p = fx:part("Block", Vector3.new(thick, h, thick), rootCF(fx, root) * off, { colour = math.floor(fx:rand(1, 3.99)), material = "body", transparency = math.max(0.35, fx:alphaFor("body")) })
		table.insert(shards, { p, off })
	end
	fx:emitter("frostMist", root or fx:at(), { area = size, shape = "Box", rate = 6, size = w / 4 })
	fx:emitter("glints", root or fx:at(), { area = size, shape = "Box", rate = 4 })
	if typeof(fx.params.target) == "Instance" then
		fx:highlight(fx.params.target, fx:c(2), fx:c(1), 0.55, 0.2)
	end
	fx.fadeOut = 0.4
	fx:onUpdate(function(_, t)
		local k = Curves.outBack(math.clamp(t / 0.25, 0, 1)) * fx.fade
		local base = rootCF(fx, root)
		for _, sh in shards do
			sh[1].CFrame = base * sh[2] * CFrame.new(0, -(1 - k) * 1.5 * s, 0)
			sh[1].Transparency = 0.35 + 0.65 * (1 - k)
		end
	end)
end

function S.Shock(fx)
	local root, size, w = ctx(fx)
	local arcs = {}
	for _ = 1, if fx.detail >= 2 then 2 else 1 do
		table.insert(arcs, Common.lightning(fx, Vector3.zero, Vector3.one, { width = 0.25, layers = 1, interval = 0.07 }))
	end
	fx:emitter("electric", root or fx:at(), { area = size, shape = "Box", rate = 10, size = w / 4 })
	local sparks = fx:emitter("sparks", root or fx:at(), { size = 0.5 })
	fx:every(0.3, function()
		sparks:emit(5)
	end)
	fx:onUpdate(function(_, t)
		local base = rootCF(fx, root)
		for i, a in arcs do
			local u = Curves.noise(t * 7, fx.uid + i * 13)
			local v = Curves.noise(t * 9, fx.uid + i * 29)
			local p0 = base * Vector3.new((u - 0.5) * size.X, (v - 0.5) * size.Y, size.Z * 0.5)
			local p1 = base * Vector3.new((v - 0.5) * size.X, (u - 0.5) * size.Y, -size.Z * 0.5)
			a.setEnds(p0, p1)
			for _, b in a.beams do
				b.beam.Enabled = not fx.stopping and (math.floor(t * 20 + i) % 3 ~= 0)
			end
		end
	end)
end

function S.Poison(fx)
	local root, size, w = ctx(fx)
	fx:emitter("toxicBubbles", root or fx:at(), { area = size * 0.8, shape = "Box", rate = 10, size = w / 4 })
	fx:emitter("drips", root or fx:at(), { area = size * Vector3.new(0.8, 0.3, 0.8), offset = CFrame.new(0, -size.Y * 0.2, 0), rate = 6, colour = { fx.rampHex[2], fx.rampHex[3] } })
	if fx.detail >= 2 then
		fx:emitter("toxicGas", root or fx:at(), { offset = feetOffset(size), rate = 3, size = w / 4 })
	end
end

function S.Slow(fx)
	local root, size, w = ctx(fx)
	local ring = fx:emitter("ring", root or fx:at(), { offset = feetOffset(size), size = w / 9, life = 1.2, sizeKeys = { { 0, 14 }, { 1, 3 } }, colour = { "#CFE6FF", "#7FA6D9" } })
	fx:every(0.8, function()
		ring:emit(1)
	end)
	fx:emitter("darkMotes", root or fx:at(), { area = size, shape = "Box", rate = 6, accel = Vector3.new(0, -6, 0), colour = { "#BFD4F0", "#6F8FBF" } })
end

function S.Stun(fx)
	local s = fx.scale
	local root, size, w = ctx(fx)
	local stars = {}
	for i = 1, 3 do
		table.insert(stars, { fx:part("Block", Vector3.new(0.38, 0.38, 0.14) * s, rootCF(fx, root), { colour = 1, material = "core", transparency = 0 }), Curves.ring(i, 3) })
	end
	fx:emitter("stars", root or fx:at(), { offset = headOffset(size), rate = 3, size = 0.6 })
	fx:onUpdate(function(_, t)
		local head = rootCF(fx, root) * headOffset(size)
		local r = w * 0.45
		for _, st in stars do
			local ang = st[2] + t * 4
			st[1].CFrame = CFrame.new(head.Position + Vector3.new(math.cos(ang) * r, math.sin(t * 6 + st[2]) * 0.12, math.sin(ang) * r)) * CFrame.Angles(0, -ang, math.pi / 4 + t * 3)
			st[1].Transparency = 1 - fx.fade
		end
	end)
end

function S.Blind(fx)
	local root, size, w = ctx(fx)
	fx:emitter("wisps", root or fx:at(), { offset = headOffset(size) * CFrame.new(0, -0.6, 0), rate = 12, size = w / 3.5, colour = { "#2A1A40", "#0A0612" } })
	fx:emitter("darkMotes", root or fx:at(), { offset = headOffset(size), rate = 6 })
end

function S.Wet(fx)
	local root, size, w = ctx(fx)
	fx:emitter("drips", root or fx:at(), { area = size * Vector3.new(0.9, 0.2, 0.9), offset = CFrame.new(0, size.Y * 0.1, 0), rate = 8 })
	fx:emitter("glints", root or fx:at(), { area = size, shape = "Box", rate = 3, colour = { "#FFFFFF", "#BFE6FF" } })
	local _ = w
end

function S.Charm(fx)
	local root, size, w = ctx(fx)
	fx:emitter("hearts", root or fx:at(), { offset = headOffset(size), rate = 3, size = w / 3 })
	fx:emitter("glitter", root or fx:at(), { area = size, shape = "Box", rate = 4, colour = { "#FFFFFF", "#FFB3D9", "#FF7FB6" } })
end

function S.Root(fx)
	local s = fx.scale
	local root, size, w = ctx(fx)
	local feet = rootCF(fx, root) * feetOffset(size)
	local g = fx:ground(feet.Position)
	local n = ({ 3, 5, 6 })[fx.detail] or 5
	local spectral = fx:spectral()
	for i = 1, n do
		local ang = Curves.ring(i, n, fx:rand(0, 0.5))
		local p = g + Vector3.new(math.cos(ang) * w * 0.55, 0, math.sin(ang) * w * 0.55)
		local h = size.Y * fx:rand(0.35, 0.6)
		-- vines lean inward over the legs; their lower part is buried
		local final = CFrame.new(p) * CFrame.Angles(0, -ang, 0) * CFrame.Angles(0, 0, math.rad(fx:rand(14, 26))) * CFrame.new(0, h * 0.35, 0)
		local vine = fx:part("Ellipsoid", Vector3.new(0.45 * s, h, 0.45 * s), final, {
			colour = if spectral then 3 else Color3.fromRGB(86 + i * 6, 120, 52),
			material = if spectral then "shell" else Enum.Material.Wood,
			transparency = if spectral then 0.25 else 0,
		})
		Common.riser(fx, vine, final, h, i * 0.05, 0.3)
	end
	fx:emitter("leaves", CFrame.new(g + Vector3.new(0, 0.5, 0)), { size = 0.6 }):emit(10)
	fx.fadeOut = 0.5
end

function S.Confuse(fx)
	local root, size, w = ctx(fx)
	local q = fx:emitter("questions", root or fx:at(), { offset = headOffset(size), rate = 2, size = w / 3 })
	local swirl = fx:emitter("windStreaks", root or fx:at(), { offset = headOffset(size), rate = 4, size = w / 6, colour = { fx.rampHex[1], fx.rampHex[2] } })
	local _ = q
	local _s = swirl
end

function S.Weaken(fx)
	local root, size, w = ctx(fx)
	fx:emitter("arrowsDown", root or fx:at(), { area = size * Vector3.new(0.9, 0.4, 0.9), shape = "Box", offset = CFrame.new(0, size.Y * 0.2, 0), rate = 3, size = w / 3, colour = { "#FF8A8A", "#B03A6A" } })
	fx:emitter("darkMotes", root or fx:at(), { area = size, shape = "Box", rate = 4 })
end

function S.Haste(fx)
	local root, size, w = ctx(fx)
	fx:emitter("windStreaks", root or fx:at(), { offset = feetOffset(size), rate = 8, size = w / 5 })
	fx:emitter("motes", root or fx:at(), { area = size, shape = "Box", rate = 6, accel = Vector3.new(0, 4, 0) })
end

function S.Regen(fx)
	local root, size, w = ctx(fx)
	fx:emitter("plusUp", root or fx:at(), { area = size * 0.7, shape = "Box", rate = 4, size = w / 3 })
	fx:emitter("motes", root or fx:at(), { area = size, shape = "Box", rate = 4, colour = { "#E9FFD9", "#7CE07C" } })
	local light = fx:light(root or fx:at(), Color3.fromRGB(150, 255, 150), 0.8, w * 3)
	if light then
		fx:onUpdate(function(_, t)
			light.Brightness = (0.6 + 0.4 * Curves.pulse(t, 0.8)) * fx.fade
		end)
	end
end

function S.Shielded(fx)
	local root, size = ctx(fx)
	local r = math.max(size.X, size.Y, size.Z) * 0.62
	local shell = fx:part("Ball", Vector3.one * 2 * r, rootCF(fx, root), {
		colour = 2,
		material = if fx:spectral() then Enum.Material.ForceField else Enum.Material.Glass,
		transparency = if fx:spectral() then 0.2 else 0.8,
	})
	fx.fadeOut = 0.3
	fx:onUpdate(function(_, t)
		shell.CFrame = rootCF(fx, root)
		local k = Curves.outBack(math.clamp(t / 0.3, 0, 1)) * fx.fade
		shell.Size = Vector3.one * math.max(0.1, 2 * r * k)
	end)
end

function S.Silence(fx)
	local s = fx.scale
	local root, size, w = ctx(fx)
	fx:emitter("halo", root or fx:at(), { offset = headOffset(size), size = w / 2.2, colour = { fx.rampHex[2], fx.rampHex[3] } })
	fx:emitter("runes", root or fx:at(), { offset = headOffset(size), rate = 4, size = 0.7 })
	local seal = fx:part("Block", Vector3.new(0.5, 0.5, 0.08) * s, rootCF(fx, root), { colour = 1, material = "core", transparency = 0.1 })
	fx:onUpdate(function(_, t)
		local head = rootCF(fx, root) * headOffset(size) * CFrame.new(0, 0.5, 0)
		seal.CFrame = CFrame.new(head.Position) * CFrame.Angles(0, t * 2, math.pi / 4)
		seal.Transparency = 0.1 + 0.9 * (1 - fx.fade)
	end)
end

function S.Corrode(fx)
	local root, size, w = ctx(fx)
	fx:emitter("flakes", root or fx:at(), { area = size, rate = 8, colour = { "#C2683A", "#7A3A1E" } })
	fx:emitter("toxicBubbles", root or fx:at(), { area = size * 0.7, shape = "Box", rate = 5, colour = { "#FFB36B", "#C2683A" } })
	local sparks = fx:emitter("metalSparks", root or fx:at(), { size = 0.4 })
	fx:every(0.9, function()
		sparks:emit(4)
	end)
	local _ = w
end

return function(fx)
	local f = S[fx.entry.variant or "Burn"] or S.Burn
	f(fx)
end
