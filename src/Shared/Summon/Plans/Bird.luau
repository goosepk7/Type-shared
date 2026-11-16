--!strict
-- Bird: songbirds, raptors, waterfowl, penguins (upright, flippers), and wyverns (bat-winged two-legged
-- reptiles with a stinger tail). Feathered wings, fanned tail, three-toed legs.

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Heads = require(script.Parent.Parent.Heads)

local at = Geom.at
local rad = math.rad

return function(B: any, ctx: any)
	local t = ctx.traits
	local detail = ctx.detail
	local id = string.lower(ctx.result.id)
	local penguin = t.flippers or string.find(id, "penguin") ~= nil
	local reptile = t.scaly or t.dragon or string.find(id, "wyvern") ~= nil
	local bulk = 0.9 + t.durability * 0.03
	local legLen = if penguin then 0.45 else 0.9
	local bodyL = (if penguin then 1.5 else 2.1) * bulk
	local bodyH = (if penguin then 2.2 else 1.35) * bulk
	local bodyY = legLen + bodyH * 0.45
	local pitch = if penguin then rad(-4) else rad(-22)
	B.boneIndex.Body.pos = { 0, bodyY, 0 }

	B:ell(bodyH * 0.82, bodyH, bodyL, at(0, bodyY, 0, pitch + (if penguin then rad(90) - rad(90) else 0), 0, 0), { col = "primary", mat = if reptile then "scale" else "fur", pri = 1, role = "body", name = "Body" })
	if detail >= 1 then
		B:ell(bodyH * 0.6, bodyH * 0.78, bodyL * 0.62, at(0, bodyY - bodyH * 0.12, -bodyL * 0.22, pitch, 0, 0), { col = "belly", mat = "fur", pri = 1.8, role = "detail", name = "Breast" })
	end
	Parts.legPair(B, { tag = "", x = bodyH * 0.22, y = legLen + 0.1, z = 0.12, w = 0.2 * bulk, kind = if reptile then "claw" else "bird", thigh = 1.4, claws = reptile, phase = 0 })

	-- head on a short neck
	local headP = { 0, bodyY + bodyH * 0.42, -bodyL * 0.42 }
	if penguin then
		headP = { 0, bodyY + bodyH * 0.42, -bodyL * 0.05 }
	end
	B:bone("Head", "Body", headP[1], headP[2], headP[3])
	B:setRig("head", "Head")
	local headS = (if penguin then 1.1 else 0.95) * bulk
	local info
	if reptile then
		info = Heads.reptile(B, { p = headP, s = headS * 1.05 }, t)
		Parts.horns(B, { bone = "Head", x = headS * 0.24, y = info.top[2] - headS * 0.08, z = info.top[3], len = headS * 0.7, w = headS * 0.16, kind = "swept", segs = 2, pri = 2.2 })
	else
		info = Heads.bird(B, { p = headP, s = headS }, t)
		if detail >= 2 and (t.crest or string.find(id, "parrot") or string.find(id, "cockatoo") or t.mythical) then
			for i = 1, 3 do
				B:limb({ 0, info.top[2] - 0.1, info.c[3] + i * 0.08 }, { 0, info.top[2] + 0.35 + i * 0.08, info.c[3] + 0.25 + i * 0.18 }, headS * 0.13, { col = if i == 2 then "secondary" else "accent", mat = "fur", bone = "Head", pri = 2.4 + i * 0.3, role = "crest", trail = i == 3 }, 0.1)
			end
		end
	end

	-- wings
	if penguin then
		B:mirrorBone("Wing#", "Body", bodyH * 0.38, bodyY + bodyH * 0.25, 0)
		B:mlimb({ bodyH * 0.38, bodyY + bodyH * 0.25, 0 }, { bodyH * 0.55, bodyY - bodyH * 0.3, 0.05 }, 0.32 * bulk, { col = "primary", mat = "fur", bone = "Wing#", pri = 1.4, role = "wing", depth = 0.12 * bulk }, 0.1)
		B:addRig("wings", { bone = "WingR", side = 1, flipper = true })
		B:addRig("wings", { bone = "WingL", side = -1, flipper = true })
	else
		Parts.wings(B, { x = bodyH * 0.3, y = bodyY + bodyH * 0.22, z = -bodyL * 0.12, span = bodyL * (if reptile then 1.6 else 1.35), kind = if reptile then "bat" else "feather", feathers = if detail >= 3 then 3 else 2 })
	end

	-- tail
	if reptile then
		Parts.tail(B, { start = { 0, bodyY - bodyH * 0.1, bodyL * 0.42 }, dir = { 0, -0.2, 1 }, len = bodyL * 1.2, w = bodyH * 0.4, segs = if detail <= 1 then 1 else 3, kind = "stinger", taper = 0.65 })
	elseif not penguin then
		local tz = bodyL * 0.48
		local n = if detail >= 2 then 3 else 1
		local long = t.longTail or string.find(id, "peacock") or string.find(id, "phoenix") or string.find(id, "parrot")
		B:bone("Tail1", "Body", 0, bodyY - bodyH * 0.05, tz)
		B:addRig("tail", "Tail1")
		for i = 1, n do
			local yaw = if n == 1 then 0 else rad((i - (n + 1) / 2) * 16)
			B:ell(0.38 * bulk, 0.08 * bulk, (if long then 1.9 else 1.05) * bulk, Geom.mul(at(0, bodyY - bodyH * 0.02 + i * 0.012, tz + 0.35, rad(14), yaw, 0), at(0, 0, (if long then 0.7 else 0.35) * bulk)),
				{ col = if i == 2 then "secondary" else "wingTip", mat = "fur", bone = "Tail1", pri = 1.7 + i * 0.4, role = "tail", trail = i == 1 })
		end
	end
	B:socket("core", at(0, bodyY, 0), "Body")
	B:setRig("gait", if penguin then "waddle" else "bird")
end
