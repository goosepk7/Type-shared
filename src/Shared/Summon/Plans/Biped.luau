--!strict
-- Biped: two-legged creatures. Kinds: "dino" (horizontal spine balanced by a heavy tail: t rex, raptor),
-- "ape" (upright, long knuckle-walking arms: gorilla, yeti), "brute" (troll, ogre, golem), "hopper" (kangaroo).

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Heads = require(script.Parent.Parent.Heads)
local Props = require(script.Parent.Parent.Props)

local at = Geom.at
local rad = math.rad

local function kindOf(ctx: any): string
	local t, id = ctx.traits, string.lower(ctx.result.id)
	if ctx.kind then
		return ctx.kind
	end
	if t.dino or t.scaly or string.find(id, "rex") or string.find(id, "raptor") or string.find(id, "lizard") then
		return "dino"
	elseif string.find(id, "kangaroo") or string.find(id, "wallaby") or t.longEars then
		return "hopper"
	elseif t.mammal or t.fluffy or string.find(id, "ape") or string.find(id, "gorilla") or string.find(id, "yeti") or string.find(id, "bear") then
		return "ape"
	end
	return "brute"
end

return function(B: any, ctx: any)
	local t = ctx.traits
	local detail = ctx.detail
	local kind = kindOf(ctx)
	local rng = B.rng
	local bulk = (0.9 + t.durability * 0.04) * rng:jitter(1, 0.05)

	if kind == "dino" then
		local legLen = 1.5 * bulk
		local hipY = legLen + 0.25
		local L = 2.6 * bulk
		local H = 1.35 * bulk
		B.boneIndex.Body.pos = { 0, hipY, 0 }
		-- torso pitched up toward the chest
		B:ell(H * 0.95, H, L, at(0, hipY + 0.15, -L * 0.12, rad(-14), 0, 0), { col = "primary", mat = "scale", pri = 1, role = "body", name = "Torso" })
		if detail >= 2 then
			B:ell(H * 0.7, H * 0.6, L * 0.75, at(0, hipY - H * 0.22, -L * 0.2, rad(-14), 0, 0), { col = "belly", mat = "scale", pri = 2.2, role = "detail", name = "Belly" })
		end
		Parts.legPair(B, { tag = "", x = H * 0.42, y = hipY, z = 0.15, w = 0.42 * bulk, kind = "claw", thigh = 1.7, claws = true, phase = 0 })
		-- neck + big head
		local neckBase = { 0, hipY + H * 0.45, -L * 0.48 }
		local headP = { 0, neckBase[2] + 0.45, neckBase[3] - 0.45 }
		B:bone("Neck", "Body", neckBase[1], neckBase[2], neckBase[3])
		B:setRig("neck", "Neck")
		if detail >= 2 then
			B:limb(neckBase, headP, H * 0.62, { col = "primary", mat = "scale", bone = "Neck", pri = 1.25, role = "body", name = "Neck" }, 0.35)
		end
		B:bone("Head", "Neck", headP[1], headP[2], headP[3])
		B:setRig("head", "Head")
		local headS = 1.35 * bulk * (if t.bigJaw then 1.15 else 1)
		Heads.reptile(B, { p = headP, s = headS }, t)
		-- tiny arms (t rex charm) or raptor claws
		Parts.armPair(B, { x = H * 0.38, y = hipY + H * 0.05, z = -L * 0.42, len = if t.bigJaw then 0.55 else 0.85, w = 0.16 * bulk, hand = "claw", out = 0.1, fwd = 0.35, fwd2 = 0.3, pri = 2.0 })
		Parts.tail(B, { start = { 0, hipY + 0.25, L * 0.32 }, dir = { 0, -0.1, 1 }, len = L * 1.1, w = H * 0.7, segs = if detail <= 1 then 1 else 3, droop = -0.15, kind = if t.spikes then "spiked" else "plain", taper = 0.62 })
		if detail >= 2 and (t.spikes or t.mythical) then
			Parts.spikeRow(B, { points = { { 0, hipY + H * 0.55, -L * 0.25, 1 }, { 0, hipY + H * 0.5, 0, 1.1 }, { 0, hipY + H * 0.4, L * 0.25, 0.9 } }, h = H * 0.38, pri = 2.8 })
		end
		B:socket("core", at(0, hipY, -L * 0.1), "Body")
		B:setRig("gait", "heavy")
		return
	end

	-- upright kinds
	local ape = kind == "ape"
	local hopper = kind == "hopper"
	local legLen = (if ape then 1.1 elseif hopper then 1.3 else 1.25) * bulk
	local hipY = legLen
	local torsoH = (if ape then 2.0 else 1.9) * bulk
	local torsoW = (if ape then 1.8 elseif hopper then 1.2 else 1.75) * bulk
	B.boneIndex.Body.pos = { 0, hipY, 0 }
	B:bone("Chest", "Body", 0, hipY + 0.3, 0)
	B:setRig("chest", "Chest")
	local lean = if ape then rad(-16) else rad(-6)
	B:ell(torsoW, torsoH, torsoW * 0.8, at(0, hipY + torsoH * 0.48, -torsoH * 0.08, lean, 0, 0), { col = "primary", mat = "fur", bone = "Chest", pri = 1, role = "body", name = "Torso" })
	if detail >= 2 then
		B:ell(torsoW * 0.72, torsoH * 0.62, torsoW * 0.5, at(0, hipY + torsoH * 0.4, -torsoW * 0.3, lean, 0, 0), { col = "belly", mat = "fur", bone = "Chest", pri = 2.2, role = "detail", name = "Belly" })
	end
	Parts.legPair(B, {
		tag = "", x = torsoW * 0.3, y = hipY + 0.1, z = 0.05, w = 0.45 * bulk, kind = "paw", thigh = 1.4, claws = t.claws, phase = 0,
		footZ = if hopper then -0.35 else 0,
	})
	if hopper then
		B:mell(0.5 * bulk, 0.35 * bulk, 1.6 * bulk, at(torsoW * 0.3, 0.18, -0.45), { col = "primary", mat = "fur", bone = "Knee#", pri = 1.5, role = "foot", name = "BigFoot#" })
	end
	local shoulderY = hipY + torsoH * 0.85
	local armLen = (if ape then 2.1 elseif hopper then 0.9 else 1.9) * bulk
	local hand = Parts.armPair(B, {
		x = torsoW * 0.5, y = shoulderY, z = -torsoH * 0.15, len = armLen, w = (if hopper then 0.22 else 0.42) * bulk,
		hand = if t.claws then "claw" else "fist", handCol = if ape then "dark" else "primary", out = 0.2, fwd = 0.18, upper = 1.25, pri = 1.3,
	})
	local neckTop = { 0, hipY + torsoH * 0.92, -torsoH * 0.28 }
	B:bone("Head", "Chest", neckTop[1], neckTop[2], neckTop[3])
	B:setRig("head", "Head")
	local headS = (if hopper then 1.0 else 1.05) * bulk
	local info = Heads.mammal(B, { p = { neckTop[1], neckTop[2] - headS * 0.15, neckTop[3] }, s = headS, muzzleCol = if ape then "secondary" else "belly", long = if hopper then 1.3 else 0.85 }, t)
	if hopper or t.longEars then
		Parts.ears(B, { bone = "Head", x = info.earX, y = info.earY, z = info.earZ, s = headS * 0.45, kind = "long" })
	elseif t.horns then
		Parts.horns(B, { bone = "Head", x = headS * 0.28, y = info.top[2] - headS * 0.1, z = info.top[3], len = headS * 0.8, w = headS * 0.2, kind = "curved", segs = 2 })
	elseif not ape then
		Parts.ears(B, { bone = "Head", x = info.earX, y = info.earY, z = info.earZ, s = headS * 0.4, kind = "round" })
	end
	if hopper then
		Parts.tail(B, { start = { 0, hipY, torsoW * 0.3 }, dir = { 0, -0.45, 1 }, len = 2.0 * bulk, w = 0.45 * bulk, segs = if detail <= 1 then 1 else 2, kind = "plain", taper = 0.6 })
	end
	if kind == "brute" and (t.club or (t.power or 5) >= 6) then
		Props.held(B, "club", hand, 0.42 * bulk, "ForeR")
	end
	B:socket("core", at(0, hipY + torsoH * 0.5, 0), "Chest")
	B:setRig("gait", if hopper then "hop" elseif ape then "heavy" else "stomp")
end
