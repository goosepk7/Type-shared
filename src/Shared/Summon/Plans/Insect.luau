--!strict
-- Insects & arthropods: ant/beetle/bee/fly/butterfly (head-thorax-abdomen, 6 legs, wings), spider (8 legs,
-- round abdomen), crab (wide carapace, big claws, eye stalks), scorpion (pincers + arched stinger tail).

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Heads = require(script.Parent.Parent.Heads)
local Face = require(script.Parent.Parent.Face)

local at = Geom.at
local rad = math.rad

local function kindOf(ctx: any): string
	if ctx.kind then
		return ctx.kind
	end
	local t, id = ctx.traits, string.lower(ctx.result.id)
	local function has(w: string): boolean
		return string.find(id, w, 1, true) ~= nil
	end
	if has("spider") or has("tarantula") or string.find(ctx.result.visual.silhouetteHint or "", "eight legs") then
		return "Spider"
	elseif has("crab") or has("lobster") or has("shrimp") then
		return "Crab"
	elseif has("scorpion") then
		return "Scorpion"
	elseif has("butterfly") or has("moth") then
		return "Butterfly"
	end
	local _ = t
	return "Bug"
end

-- n legs per side along z from z0 to z1, splaying outward; bug legs are thin two-segment limbs.
local function legs(B: any, detail: number, n: number, x: number, y: number, z0: number, z1: number, w: number, col: string, parent: string?)
	for i = 1, n do
		local z = if n == 1 then z0 else z0 + (i - 1) / (n - 1) * (z1 - z0)
		local tag = "L" .. i
		local hr, hl = B:mirrorBone("Hip" .. tag .. "#", parent or "Body", x, y, z)
		B:addRig("legs", { hip = hr, side = 1, phase = (i % 2) * 0.5, len = y })
		B:addRig("legs", { hip = hl, side = -1, phase = ((i + 1) % 2) * 0.5, len = y })
		local splayZ = (z - (z0 + z1) / 2) * 0.6
		local reach = y * 0.75 + 0.4
		local knee = { x + reach * 0.62, y + reach * 0.42, z + splayZ * 0.5 }
		local foot = { x + reach * 1.15, 0.05, z + splayZ * 1.3 }
		if detail <= 1 then
			B:mbeam({ x, y, z }, foot, w * 1.1, w * 1.1, { col = col, mat = "hard", bone = "Hip" .. tag .. "#", pri = 1.3 + i * 0.05, role = "limb" })
		else
			B:mlimb({ x, y, z }, knee, w * 1.2, { col = col, mat = "hard", bone = "Hip" .. tag .. "#", pri = 1.3 + i * 0.05, role = "limb" }, 0.15)
			B:mlimb(knee, foot, w, { col = col, mat = "hard", bone = "Hip" .. tag .. "#", pri = 1.35 + i * 0.05, role = "limb" }, 0.1)
		end
	end
end

return function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local kind = kindOf(ctx)
	local mood = ctx.result.mood or "Neutral"

	if kind == "Crab" then
		local y = 1.0
		B.boneIndex.Body.pos = { 0, y, 0 }
		local c, r = { 0, y + 0.1, 0 }, { 1.5, 0.6, 1.05 }
		B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "hard", pri = 1, role = "body", name = "Carapace" })
		if detail >= 2 then
			B:ell(r[1] * 1.7, r[2] * 1.1, r[3] * 1.6, at(c[1], c[2] - 0.22, c[3] + 0.02), { col = "belly", mat = "hard", pri = 2.3, role = "detail", name = "Under" })
		end
		-- eye stalks
		B:mirrorBone("Stalk#", "Body", 0.45, y + 0.5, -0.7)
		B:mrod({ 0.45, y + 0.4, -0.7 }, { 0.5, y + 1.05, -0.8 }, 0.14, { col = "primary", mat = "hard", bone = "Stalk#", pri = 1.6, role = "stalk" })
		Face.build(B, { face = { kind = "flat", cf = at(0, y + 1.15, -0.85) }, bone = "Body", mood = mood, detail = math.min(detail, 2), kind = "cute", spacing = 0.5, y = 0, d = 0.42, noMouth = true, noBrows = detail < 3 })
		-- claws: arm + big pincer on each side
		B:mirrorBone("Claw#", "Body", 1.2, y + 0.1, -0.6)
		B:addRig("arms", { arm = "ClawR", side = 1 })
		B:addRig("arms", { arm = "ClawL", side = -1 })
		B:mlimb({ 1.2, y + 0.1, -0.6 }, { 1.85, y + 0.5, -1.4 }, 0.36, { col = "primary", mat = "hard", bone = "Claw#", pri = 1.2, role = "limb" }, 0.2)
		B:mell(0.75, 0.62, 1.1, at(1.95, y + 0.65, -1.95, rad(-10), rad(12), 0), { col = "secondary", mat = "hard", bone = "Claw#", pri = 1.25, role = "claw", name = "Pincer#", trail = true })
		if detail >= 2 then
			B:mell(0.32, 0.3, 0.85, at(1.75, y + 0.35, -2.0, rad(8), rad(-14), 0), { col = "secondary", mat = "hard", bone = "Claw#", pri = 2.2, role = "claw" })
		end
		legs(B, detail, if detail <= 1 then 2 else 3, 1.1, y, -0.2, 0.75, 0.13, "dark")
		B:socket("core", at(0, y + 0.2, 0), "Body")
		B:setRig("gait", "scuttle")
		return
	end

	local spider = kind == "Spider"
	local y = if spider then 1.35 else 1.05
	B.boneIndex.Body.pos = { 0, y, 0 }
	local bodyCol = if kind == "Butterfly" then "dark" else "primary"
	-- thorax, abdomen
	B:ell(0.95, 0.8, 1.05, at(0, y, 0), { col = bodyCol, mat = "hard", pri = 1.05, role = "body", name = "Thorax" })
	local ab = B:bone("Abdomen", "Body", 0, y, 0.45)
	B:addRig("tail", ab)
	local abSize = if spider then { 1.9, 1.6, 2.0 } elseif kind == "Butterfly" then { 0.55, 0.5, 1.8 } else { 1.25, 1.05, 1.8 }
	B:ell(abSize[1], abSize[2], abSize[3], at(0, y + (if spider then 0.35 else 0.05), 0.45 + abSize[3] * 0.45, rad(if spider then 10 else -8), 0, 0),
		{ col = "primary", mat = if t.fluffy then "fur" else "hard", bone = ab, pri = 1, role = "body", name = "Abdomen" })
	-- stripes (bee/wasp) or shell (beetle) or markings (spider)
	if detail >= 2 and (t.stinger or string.find(string.lower(ctx.result.id), "bee") or string.find(string.lower(ctx.result.id), "wasp")) then
		for i = 1, 2 do
			B:ell(abSize[1] * 1.03, abSize[2] * 1.03, 0.3, at(0, y + 0.05, 0.45 + abSize[3] * (0.25 + i * 0.22), rad(-8), 0, 0), { col = "secondary", mat = "hard", bone = ab, pri = 2.0 + i * 0.2, role = "detail", name = "Stripe" .. i })
		end
	elseif t.shell and detail >= 1 then
		B:mell(abSize[1] * 0.56, abSize[2] * 1.06, abSize[3] * 1.04, at(abSize[1] * 0.23, y + 0.1, 0.45 + abSize[3] * 0.45, rad(-8), 0, rad(-4)), { col = "secondary", mat = "hard", bone = ab, pri = 1.4, role = "shell", name = "Elytra#" })
	elseif spider and detail >= 3 then
		B:ell(0.7, 0.5, 0.25, at(0, y + 1.0, 1.0 + 0.6, rad(-60), 0, 0), { col = "secondary", mat = "hard", bone = ab, pri = 3.0, role = "detail", name = "Mark" })
	end
	-- head
	B:bone("Head", "Body", 0, y + 0.05, -0.45)
	B:setRig("head", "Head")
	Heads.bug(B, { p = { 0, y + 0.05, -0.45 }, s = if spider then 1.0 else 0.95, col = bodyCol }, t)
	-- legs
	if spider then
		legs(B, detail, if detail <= 1 then 2 else 4, 0.38, y, -0.35, 0.35, 0.13, "dark")
	else
		legs(B, detail, if detail <= 0 then 2 else 3, 0.35, y - 0.1, -0.3, 0.3, 0.1, "dark")
	end
	-- wings
	if (t.wings or t.flies) and not spider then
		if kind == "Butterfly" then
			Parts.wings(B, { x = 0.3, y = y + 0.4, z = -0.1, span = 2.4, kind = "feather", feathers = 2 })
		else
			Parts.wings(B, { x = 0.3, y = y + 0.45, z = 0.1, span = 1.8, kind = "insect" })
		end
	end
	-- stinger / scorpion tail + pincers
	if kind == "Scorpion" then
		Parts.tail(B, { parent = ab, start = { 0, y + 0.3, 0.45 + abSize[3] * 0.85 }, dir = { 0, 1, 0.35 }, len = 2.2, w = 0.45, segs = if detail <= 1 then 1 else 3, curl = -1.2, kind = "stinger", taper = 0.8 })
		B:mirrorBone("Claw#", "Body", 0.5, y, -0.5)
		B:mlimb({ 0.5, y, -0.5 }, { 1.0, y + 0.1, -1.4 }, 0.26, { col = "primary", mat = "hard", bone = "Claw#", pri = 1.3, role = "limb" }, 0.2)
		B:mell(0.5, 0.42, 0.8, at(1.05, y + 0.12, -1.85), { col = "secondary", mat = "hard", bone = "Claw#", pri = 1.35, role = "claw", trail = true })
		B:addRig("arms", { arm = "ClawR", side = 1 })
		B:addRig("arms", { arm = "ClawL", side = -1 })
	elseif t.stinger and detail >= 2 then
		B:limb({ 0, y, 0.45 + abSize[3] * 0.85 }, { 0, y - 0.15, 0.45 + abSize[3] * 1.15 }, 0.16, { col = "darker", mat = "hard", bone = ab, pri = 2.5, role = "tail", trail = true }, 0.1)
	end
	if t.horns and detail >= 1 then
		Parts.horns(B, { bone = "Head", x = 0, y = y + 0.3, z = -0.85, len = 0.9, w = 0.22, kind = "uni", segs = 2, pri = 1.6, col = "secondary" })
	end
	B:socket("core", at(0, y, 0.3), "Body")
	B:setRig("gait", if (t.wings or t.flies) and not spider then "buzz" else "scuttle")
end
