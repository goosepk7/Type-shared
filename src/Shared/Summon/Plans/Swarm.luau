--!strict
-- Swarm: a buzzing cluster of small units (bees, bats, fireflies, locusts, fish schools, sparks...).
-- Each unit is 1-3 parts on its own bone so the animator can buzz/orbit them independently. The unit count
-- fills the part budget (more units at bigger sizes / counts).

local Geom = require(script.Parent.Parent.Geom)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local function unitKind(ctx: any): string
	local t, id = ctx.traits, string.lower(ctx.result.id)
	if string.find(id, "bat") then
		return "bat"
	elseif t.aquatic or t.swims or string.find(id, "fish") or string.find(id, "piranha") then
		return "fish"
	elseif string.find(id, "firefl") or string.find(id, "spark") or string.find(id, "ember") or string.find(id, "wisp") or t.element == "Light" then
		return "spark"
	elseif string.find(id, "bird") or string.find(id, "crow") or string.find(id, "pigeon") then
		return "bird"
	end
	return "bug"
end

-- One unit centred at p; returns parts used.
local function unit(B: any, kind: string, i: number, p: { number }, s: number, detail: number): number
	local bone = B:bone("Unit" .. i, "Body", p[1], p[2], p[3])
	B:addRig("units", { bone = bone, index = i })
	local yaw = (i * 2.399) % (math.pi * 2)
	local base = at(p[1], p[2], p[3], 0, yaw, 0)
	local pri = 1 + i * 0.04
	if kind == "spark" then
		B:ball(s * 0.7, base, { col = "glow", mat = "neon", glow = true, bone = bone, pri = pri, role = "gem", name = "Spark" .. i, noCore = true, trail = i <= 2 })
		return 1
	end
	if kind == "fish" then
		B:ell(s * 0.5, s * 0.7, s * 1.3, base, { col = "primary", mat = "skin", bone = bone, pri = pri, role = "body", name = "Fish" .. i })
		if detail >= 2 then
			B:wedge(s * 0.08, s * 0.6, s * 0.45, Geom.mul(base, at(0, 0, s * 0.75, 0, 0, 0)), { col = "secondary", mat = "skin", bone = bone, pri = pri + 0.5, role = "fin" })
		end
		return if detail >= 2 then 2 else 1
	end
	local bodyCol = if kind == "bat" then "primary" else "primary"
	B:ell(s * 0.6, s * 0.6, s * 0.95, base, { col = bodyCol, mat = "fur", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
	local used = 1
	if detail >= 1 then
		-- wings: one flattened ellipsoid spanning both sides (a single part per unit)
		local wcol = if kind == "bug" then "wingGlass" else "dark"
		B:ell(s * (if kind == "bat" then 2.2 else 1.6), s * 0.08, s * 0.5, Geom.mul(base, at(0, s * 0.3, s * 0.05, rad(8), 0, 0)),
			{ col = wcol, mat = if kind == "bug" then "glass" else "skin", tr = if kind == "bug" then 0.35 else nil, bone = bone, pri = pri + 0.3, role = "wing", name = "Wings" .. i })
		used += 1
	end
	if detail >= 2 and kind == "bug" then
		B:ell(s * 0.63, s * 0.63, s * 0.22, Geom.mul(base, at(0, 0, s * 0.18)), { col = "secondary", mat = "fur", bone = bone, pri = pri + 0.8, role = "detail", name = "Stripe" .. i })
		used += 1
	end
	return used
end

return function(B: any, ctx: any)
	local detail = ctx.detail
	local kind = unitKind(ctx)
	local per = if kind == "spark" then 1 elseif detail >= 2 then (if kind == "bug" then 3 else 2) elseif detail >= 1 then 2 else 1
	local n = math.clamp(math.floor((ctx.budget - (if ctx.style == "Spectral" then 3 else 0)) / per), 3, 16)
	local rng = B.rng
	B.boneIndex.Body.pos = { 0, 2.4, 0 }
	-- golden-angle spiral in a squashed sphere, with seeded jitter; deterministic per seed
	local s = 0.75
	for i = 1, n do
		local u = (i - 0.5) / n
		local yy = 1 - 2 * u
		local r = math.sqrt(1 - yy * yy)
		local th = i * 2.39996
		local R = 2.0 * rng:jitter(1, 0.18)
		local p = { cos(th) * r * R, 2.4 + yy * 1.4 * rng:jitter(1, 0.15), sin(th) * r * R }
		unit(B, kind, i, p, s * rng:jitter(1, 0.15), detail)
	end
	B:socket("core", at(0, 2.4, 0), "Body")
	B:setRig("gait", "swarm")
end
