--!strict
-- Sea mammals and sea reptiles for Plans/Fish: whales and dolphins (horizontal fluke, flippers, beak / melon /
-- boxy head by species), seals and sea lions (lying or propped on fore flippers, hind flippers fanned back,
-- whiskered head; walrus tusks, elephant seal trunk, hooded seal balloon), sea cows (paddle tail), plesiosaurs
-- and pliosaurs (four long flippers, long or short neck), mosasaurs and ichthyosaurs, and merfolk (a person's
-- torso on a fish tail).

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Heads = require(script.Parent.Parent.Heads)
local Face = require(script.Parent.Parent.Face)
local SeaFish = require(script.Parent.SeaFish)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local SeaMammal = {}

local function mood(B: any): string
	return B.ctx.result.mood or "Neutral"
end

-- Flipper pair (mirrored ellipsoid flat in y on bone Flip<tag>#; flaps with the wing rig as a flipper). The right
-- flipper reaches out from (x, y, z), swept `back` radians toward the tail and drooping `droop` radians.
local function flippers(B: any, tag: string, x: number, y: number, z: number, len: number, wid: number, back: number, droop: number, col: string, pri: number, o: any?)
	local oo = o or {}
	local br, bl = B:mirrorBone("Flip" .. tag .. "#", oo.parent or "Body", x, y, z)
	if oo.flap ~= false then
		B:addRig("wings", { bone = br, side = 1, flipper = true })
		B:addRig("wings", { bone = bl, side = -1, flipper = true })
	end
	local k = len * 0.42
	local cx, cy, cz = x + cos(back) * cos(droop) * k, y - sin(droop) * k, z + sin(back) * cos(droop) * k
	B:mell(len, 0.16 * (oo.thick or 1), wid, at(cx, cy, cz, 0, -back, -droop), {
		col = col, mat = "skin", bone = "Flip" .. tag .. "#", pri = pri, role = "fin", name = "Flipper" .. tag .. "#", mesh = "s_aq_flipper", meshL = "s_aq_flipper_l",
	})
	return br, bl
end

-- Whales, dolphins, porpoises, ichthyosaurs.
function SeaMammal.whale(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local has = SeaFish.reader(ctx)
	local dolphin = has("dolphin", "porpoise", "vaquita", "orca", "killer", "ichthyo", "shonisaurus", "temnodontosaurus", "encantado", "risso")
	local beaked = has("dolphin", "beak", "ichthyo", "shonisaurus", "temnodontosaurus", "encantado") and not has("blunt", "risso")
	local melon = has("beluga", "melon", "pilot", "bulbous", "risso", "blunt", "narwhal", "porpoise")
	local boxy = has("sperm", "livyatan", "boxy")
	local baleen = has("blue whale", "fin whale", "humpback", "minke", "sei whale", "bryde", "gray whale", "grooved", "baleen", "right whale", "bowhead")
	local noDorsal = has("beluga", "narwhal", "right whale", "bowhead", "skeleton")
	local reptile = has("ichthyo", "shonisaurus", "temnodontosaurus")
	local L = if dolphin then 3.6 else 4.6
	local H = if dolphin then 1.15 else 1.6
	local W = if dolphin then 1.0 else 1.55
	if t.chubby or has("chubby", "chunky", "round") then
		H *= 1.12
		W *= 1.15
	end
	local y = H * 0.5 + 0.7
	B.boneIndex.Body.pos = { 0, y, 0 }
	local z0 = -L * 0.5
	local fl = L * (if boxy then 0.66 else 0.6)
	local fc = { 0, y, z0 + fl * 0.5 }
	local fr = { W * 0.5, H * 0.5, fl * 0.5 }
	local body = B:ell(fr[1] * 2, fr[2] * 2, fr[3] * 2, at(fc[1], fc[2], fc[3]), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Body", mesh = "s_aq_whale_body" })
	local members = {}
	if detail >= 2 then
		table.insert(members, B:ell(fr[1] * 1.7, fr[2] * 1.05, fr[3] * 1.8, at(0, fc[2] - fr[2] * 0.48, fc[3]), { col = "belly", mat = "skin", pri = 2.0, role = "detail", name = "Belly", mesh = false }))
	end
	if boxy then
		-- sperm whale: a long box of a head in front, the narrow jaw slung under it
		local hc = { 0, y + H * 0.08, z0 + fl * 0.25 }
		B:block(W * 0.92, H * 0.98, fl * 0.75, at(hc[1], hc[2], hc[3] + fl * 0.02), { col = "primary", mat = "skin", pri = 1.05, role = "head", name = "Case" })
		local jb = B:bone("Jaw", "Body", 0, y - H * 0.35, z0 + fl * 0.45)
		B:setRig("jaw", jb)
		B:ell(W * 0.32, H * 0.2, fl * 0.62, at(0, y - H * 0.4, z0 + fl * 0.27), { col = "belly", mat = "skin", bone = jb, pri = 1.5, role = "jaw", name = "Jaw", mesh = false })
		if detail >= 2 then
			Parts.teeth(B, { bone = jb, y = y - H * 0.28, z = z0 + fl * 0.08, r = W * 0.1, n = 2, h = H * 0.12, pri = 3 })
		end
	end
	if melon and not boxy then
		table.insert(members, B:ell(fr[1] * 1.6, fr[2] * 1.3, fr[3] * 0.85, at(0, fc[2] + fr[2] * 0.15, fc[3] - fr[3] * 0.4), { col = "primary", mat = "skin", pri = 1.05, role = "head", name = "Melon", mesh = false }))
	end
	B:sculpt(body, "s_aq_whale_body", members)
	if beaked then
		B:limb({ 0, fc[2] - fr[2] * 0.25, fc[3] - fr[3] * 0.7 }, { 0, fc[2] - fr[2] * 0.3, fc[3] - fr[3] - L * (if has("long thin beak", "long beak") then 0.28 else 0.16) }, H * 0.28,
			{ col = "primary", mat = "skin", pri = 1.2, role = "snout", name = "Rostrum", depth = H * 0.24, mesh = false }, 0.15)
	end
	-- tail stock and fluke
	local t1 = B:bone("Tail1", "Body", 0, y, z0 + fl * 0.62)
	local t2 = B:bone("Tail2", t1, 0, y, z0 + L * 0.9)
	B:addRig("tail", t1)
	B:addRig("tail", t2)
	local rl = L * 0.52
	local rc = { 0, y + H * 0.04, z0 + L - rl * 0.5 - L * 0.04 }
	local rear = B:ell(W * 0.8, H * 0.8, rl, at(rc[1], rc[2], rc[3]), { col = "primary", mat = "skin", bone = t1, pri = 1.1, role = "body", name = "Rear", mesh = "s_aq_fish_tail" })
	if detail >= 1 then
		local ped = B:ell(W * 0.3, H * 0.3, L * 0.18, at(0, y + H * 0.05, z0 + L * 0.95), { col = "primary", mat = "skin", bone = t2, pri = 1.25, role = "body", name = "Peduncle", mesh = false })
		B:sculpt(rear, "s_aq_fish_tail", { ped })
	end
	if reptile then
		SeaFish.caudal(B, "lunate", t2, y + H * 0.05, z0 + L * 1.0, H * 1.5, L * 0.28, 0.1, "primary", detail)
	else
		B:ell(L * 0.52, 0.16, L * 0.21, at(0, y + H * 0.05, z0 + L * 1.08), { col = "primary", mat = "skin", bone = t2, pri = 1.3, role = "fin", name = "Fluke", trail = true, mesh = "s_aq_fluke" })
	end
	-- dorsal
	if not noDorsal then
		local dh = H * (if dolphin then 0.55 elseif has("blue whale", "fin whale", "minke", "sei") then 0.22 else 0.3)
		B:ell(0.12, dh * 1.3, L * (if dolphin then 0.16 else 0.12), at(0, rc[2] + H * 0.36 + dh * 0.12, z0 + L * (if dolphin then 0.5 else 0.66)), { col = "primary", mat = "skin", bone = if dolphin then "Body" else t1, pri = 1.45, role = "fin", name = "Dorsal", trail = true, mesh = "s_aq_dorsal" })
	elseif detail >= 2 and has("right whale", "bowhead") then
		B:ell(W * 0.5, H * 0.3, fl * 0.4, at(0, fc[2] + fr[2] * 0.8, fc[3] - fr[3] * 0.45), { col = "secondary", mat = "skin", pri = 2.6, role = "detail", name = "Callosity", mesh = false })
	end
	-- flippers
	if detail >= 1 then
		local long = has("long white flipper", "humpback")
		flippers(B, "F", fr[1] * 0.8, fc[2] - fr[2] * 0.45, fc[3] - fr[3] * 0.1, H * (if long then 1.9 else 0.85), H * (if long then 0.32 else 0.32), rad(28), rad(30),
			if long or has("white flipper") then "secondary" else "primary", 1.7, { back = 1 })
		if reptile then
			flippers(B, "H", fr[1] * 0.6, fc[2] - fr[2] * 0.5, rc[3] - rl * 0.1, H * 0.55, H * 0.24, rad(32), rad(30), "primary", 2.6, { parent = t1 })
		end
	end
	if has("narwhal", "spiral horn", "unicorn") then
		B:limb({ 0, fc[2] - fr[2] * 0.05, fc[3] - fr[3] * 0.8 }, { 0.1, fc[2] + fr[2] * 0.2, fc[3] - fr[3] - L * 0.5 }, H * 0.13, { col = if has("rainbow") then "gem" else "horn", mat = "hard", pri = 1.3, role = "horn", name = "Tusk", trail = true, mesh = "s_unicorn_horn" }, 0.05)
	end
	if has("orca", "killer") and not has("false") and detail >= 2 then
		B:mell(fr[1] * 0.25, fr[2] * 0.35, fr[3] * 0.35, at(fr[1] * 0.75, fc[2] + fr[2] * 0.25, fc[3] - fr[3] * 0.25, 0, rad(-40), 0), { col = "secondary", mat = "skin", pri = 2.8, role = "detail", name = "EyePatch#", mesh = false })
	end
	if has("starry", "glowing spots", "nebula", "stars", "celestial", "astro", "space") and detail >= 2 then
		for i, p in { { 0.4, 0.55, -0.2 }, { -0.5, 0.6, 0.25 }, { 0.15, 0.8, 0.55 } } do
			if i <= detail then
				B:ball(H * 0.14, at(fr[1] * p[1], fc[2] + fr[2] * p[2], fc[3] + fr[3] * p[3]), { col = "glow", mat = "neon", glow = true, pri = 3.6 + i * 0.1, role = "gem", name = "Star", noCore = true })
			end
		end
	end
	-- face: eyes near the mouth corner, smile line for dolphins
	local fierce = has("teeth", "toothy", "livyatan", "orca", "killer") or (not t.cute and (t.power or 5) >= 8)
	Face.build(B, { face = { kind = "ellipsoid", c = fc, r = fr }, bone = "Body", mood = mood(B), detail = detail, kind = if fierce then "fierce" else "cute",
		spacing = fr[1] * 0.66, y = -fr[2] * 0.05, d = H * (if dolphin then 0.24 else 0.18) * (if reptile then 1.6 else 1), mouthY = -fr[2] * 0.42, mouthW = W * 0.55, lidCol = "primary",
		forceMouth = dolphin or has("smile", "smiley") })
	B:socket("mouth", at(0, fc[2] - fr[2] * 0.3, fc[3] - fr[3] - 0.1), "Body")
	B:socket("core", at(0, y, fc[3]), "Body")
	B:setRig("gait", "swim")
end

-- Seals, sea lions, walruses, and sea cows (manatee, dugong: float, paddle tail, no hind flippers).
function SeaMammal.seal(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local has = SeaFish.reader(ctx)
	local sirenian = has("manatee", "dugong", "sea cow")
	local walrus = has("walrus")
	local lion = has("sea lion", "fur seal", "upright")
	local pup = has("pup")
	local L = if walrus then 3.4 elseif sirenian then 3.8 else 3.0
	local H = if walrus then 1.6 elseif sirenian then 1.4 else 1.15
	local W = H * (if walrus or sirenian then 1.15 else 1.0)
	if pup or t.chubby or has("blubbery", "chubby", "chunky", "giant") then
		H *= 1.1
		W *= 1.15
	end
	local y = if sirenian then H * 0.5 + 0.6 else H * 0.5
	B.boneIndex.Body.pos = { 0, y, 0 }
	local lift = if lion then rad(-22) else 0 -- sea lions prop the chest up on their fore flippers
	-- chest (Body) and hindquarters (Tail1 -> Tail2 hind flippers / paddle)
	local cc = { 0, y + (if lion then H * 0.3 else H * 0.05), -L * 0.12 }
	local cr = { W * 0.5, H * 0.52, L * 0.33 }
	local chest = B:ell(cr[1] * 2, cr[2] * 2, cr[3] * 2, at(cc[1], cc[2], cc[3], lift, 0, 0), { col = "primary", mat = if t.fluffy or pup then "fur" else "skin", pri = 1, role = "body", name = "Body", mesh = "s_aq_seal_body" })
	if detail >= 2 then
		local belly = B:ell(cr[1] * 1.6, cr[2] * 1.2, cr[3] * 1.7, at(0, cc[2] - cr[2] * 0.4, cc[3] + cr[3] * 0.1, lift, 0, 0), { col = "belly", mat = "skin", pri = 2.1, role = "detail", name = "Belly", mesh = false })
		B:sculpt(chest, "s_aq_seal_body", { belly })
	end
	local t1 = B:bone("Tail1", "Body", 0, y, L * 0.12)
	local t2 = B:bone("Tail2", t1, 0, y * 0.7, L * 0.42)
	B:addRig("tail", t1)
	B:addRig("tail", t2)
	local hc = { 0, y - H * 0.04, L * 0.2 }
	B:ell(W * 0.82, H * 0.8, L * 0.52, at(hc[1], hc[2], hc[3], rad(-6), 0, 0), { col = "primary", mat = if t.fluffy or pup then "fur" else "skin", bone = t1, pri = 1.1, role = "body", name = "Hips", mesh = "s_aq_seal_hips" })
	if sirenian then
		B:ell(L * (if has("dugong", "fluke") then 0.4 else 0.3), 0.16, L * 0.24, at(0, hc[2] + H * 0.02, L * 0.55), { col = "primary", mat = "skin", bone = t2, pri = 1.3, role = "fin", name = "Paddle", trail = true,
			mesh = if has("dugong", "fluke") then "s_aq_fluke" else "s_aq_paddle" })
	elseif detail >= 1 then
		-- hind flippers fanned back, soles up
		local hy = math.max(0.12, hc[2] - H * 0.28)
		local hr, hl = B:mirrorBone("FlipH#", t2, W * 0.16, hy, L * 0.45)
		local _ = hr
		local _l = hl
		B:mell(W * 0.38, 0.12, L * 0.26, at(W * 0.2, hy, L * 0.56, rad(4), rad(-12), rad(-14)), { col = "darker", mat = "skin", bone = "FlipH#", pri = 1.5, role = "fin", name = "HindFlipper#", trail = true, mesh = "s_aq_flipper", meshL = "s_aq_flipper_l" })
	end
	-- fore flippers: planted on the ground (seals, sea lions) or paddling (sea cows)
	if detail >= 1 then
		if sirenian then
			flippers(B, "F", cr[1] * 0.85, cc[2] - cr[2] * 0.5, cc[3] - cr[3] * 0.3, H * 0.6, H * 0.3, rad(35), rad(35), "primary", 1.7, {})
		else
			local fy = cc[2] - cr[2] * (if lion then 0.35 else 0.55)
			local fx = cr[1] * 0.85
			local fz = cc[3] - cr[3] * 0.25
			local br, bl = B:mirrorBone("FlipF#", "Body", fx, fy, fz)
			B:addRig("legs", { hip = br, side = 1, phase = 0, len = fy })
			B:addRig("legs", { hip = bl, side = -1, phase = 0.5, len = fy })
			local len = H * (if lion then 1.0 else 0.75)
			B:mlimb({ fx, fy, fz }, { fx + len * 0.35, 0.1, fz - len * 0.25 }, H * 0.24, { col = "primary", mat = "skin", bone = "FlipF#", pri = 1.6, role = "limb", name = "ForeArm#", depth = H * 0.16 }, 0.15)
			B:mell(H * 0.42, 0.1, H * 0.6, at(fx + len * 0.42, 0.06, fz - len * 0.42, 0, rad(-25), 0), { col = "darker", mat = "skin", bone = "FlipF#", pri = 1.9, role = "fin", name = "ForeFlipper#", mesh = "s_aq_flipper", meshL = "s_aq_flipper_l" })
		end
	end
	-- neck and head
	local hp = { 0, cc[2] + cr[2] * (if lion then 0.9 else 0.45), cc[3] - cr[3] * (if lion then 0.85 else 0.95) }
	local hb = B:bone("Head", "Body", hp[1], hp[2], hp[3])
	B:setRig("head", hb)
	local s = H * (if walrus then 0.82 elseif sirenian then 0.85 elseif pup then 0.95 else 0.8)
	if lion and detail >= 1 then
		B:limb({ 0, cc[2], cc[3] - cr[3] * 0.4 }, { hp[1], hp[2] + s * 0.1, hp[3] }, s * 0.75, { col = "primary", mat = "skin", bone = "Body", pri = 1.2, role = "body", name = "Neck", mesh = false }, 0.3)
	end
	local info = Heads.beast(B, { p = { hp[1], hp[2], hp[3] - s * 0.1 }, s = s, bone = hb, arch = "pinniped", eyeScale = if pup then 1.3 elseif walrus then 0.75 else 1,
		eyes = if pup or t.cute then "cute" elseif walrus or has("big jaws", "reptile head", "leopard") then "fierce" else nil }, t) :: any
	local hc2, hr2 = info.c, info.r
	if walrus and detail >= 1 then
		-- tusks down from the whisker pads, a bristly moustache pad
		B:mlimb({ s * 0.12, hc2[2] - s * 0.38, hc2[3] - hr2[3] * 0.85 }, { s * 0.2, hc2[2] - s * 1.35, hc2[3] - hr2[3] * 0.8 }, s * 0.13, { col = "horn", mat = "hard", bone = hb, pri = 1.4, role = "horn", name = "Tusk#", trail = true }, 0.05)
		if detail >= 2 then
			B:ell(s * 0.75, s * 0.32, s * 0.36, at(0, hc2[2] - s * 0.3, hc2[3] - hr2[3] * 0.82), { col = "light", mat = "fur", bone = hb, pri = 2.3, role = "snout", name = "Moustache", mesh = false })
		end
	elseif has("trunk", "droopy") and detail >= 1 then
		B:limb({ 0, hc2[2] - s * 0.05, hc2[3] - hr2[3] * 0.8 }, { 0, hc2[2] - s * 0.5, hc2[3] - hr2[3] * 1.25 }, s * 0.3, { col = "primary", mat = "skin", bone = hb, pri = 1.45, role = "snout", name = "Proboscis", trail = true, mesh = false }, 0.2)
	elseif has("balloon", "inflatable") and detail >= 2 then
		B:ell(s * 0.5, s * 0.45, s * 0.55, at(0, hc2[2] + s * 0.25, hc2[3] - hr2[3] * 0.7), { col = "accent", mat = "skin", bone = hb, pri = 2.2, role = "snout", name = "Balloon", mesh = false })
	end
	if (lion or has("fur seal")) and detail >= 2 then
		Parts.ears(B, { bone = hb, x = info.earX, y = info.earY, z = info.earZ, kind = "round", s = s * 0.28, pri = 3.2 })
	end
	if detail >= 3 and (has("spot", "ring", "harp", "throat") or t.spots) then
		for i, p in { { 0.6, 0.3, -0.1 }, { -0.5, 0.5, 0.3 } } do
			B:ell(H * 0.35, H * 0.08, H * 0.3, at(cr[1] * p[1], cc[2] + cr[2] * p[2] * 1.6, cc[3] + cr[3] * p[3], 0, 0, rad(p[1] * 40)), { col = "darker", mat = "skin", pri = 3.6 + i * 0.1, role = "detail", name = "Spot", mesh = false })
		end
	end
	B:socket("core", at(0, cc[2], cc[3]), "Body")
	B:setRig("gait", if sirenian then "swim" else "waddle")
end

-- Plesiosaurs (long neck), pliosaurs (huge head, short neck), mosasaurs (long body, tail fin), nothosaurs,
-- placodonts, ambulocetus (legs). Four flippers on a broad trunk.
function SeaMammal.reptile(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local has = SeaFish.reader(ctx)
	local longNeck = has("plesio", "elasmo", "long neck", "nothosaur") or t.longNeck
	local bigHead = has("pliosaur", "kronosaur", "liopleur", "huge-headed", "huge pliosaur", "short neck", "short-necked", "prognath", "crushing")
	local mosa = has("mosasaur", "tylosaur", "prognath", "ambulocetus", "makara", "ketos")
	local legs = has("with legs", "ambulocetus")
	local L = if mosa then 3.6 else 2.8
	local H, W = 1.15, 1.5
	local y = H * 0.5 + 0.9
	B.boneIndex.Body.pos = { 0, y, 0 }
	local c = { 0, y, 0 }
	local r = { W * 0.5, H * 0.5, L * 0.36 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "scale", pri = 1, role = "body", name = "Body", mesh = "s_aq_seal_body" })
	if detail >= 2 then
		B:ell(r[1] * 1.6, r[2] * 1.15, r[3] * 1.75, at(0, y - r[2] * 0.45, 0), { col = "belly", mat = "scale", pri = 2.1, role = "detail", name = "Belly", mesh = false })
	end
	-- flippers fore and hind (or legs)
	if legs then
		Parts.legPair(B, { tag = "F", parent = "Body", x = r[1] * 0.7, y = y - r[2] * 0.4, z = -r[3] * 0.5, w = 0.32, kind = "claw", claws = true, phase = 0 })
		Parts.legPair(B, { tag = "H", parent = "Body", x = r[1] * 0.7, y = y - r[2] * 0.4, z = r[3] * 0.6, w = 0.34, kind = "claw", claws = true, phase = 0.5 })
	else
		flippers(B, "F", r[1] * 0.75, y - r[2] * 0.35, -r[3] * 0.45, L * (if mosa then 0.28 else 0.45), 0.42, rad(40), rad(15), "primary", 1.5, {})
		if detail >= 1 then
			flippers(B, "H", r[1] * 0.7, y - r[2] * 0.35, r[3] * 0.55, L * (if mosa then 0.24 else 0.38), 0.38, rad(55), rad(15), "primary", 1.7, {})
		end
	end
	-- tail
	local tail = Parts.tail(B, { start = { 0, y, r[3] * 0.8 }, dir = { 0, -0.05, 1 }, len = L * (if mosa then 0.9 else 0.5), w = W * 0.38, segs = if detail >= 2 then 2 else 1, taper = 0.62, flat = 0.85, pri = 1.2 })
	if mosa and detail >= 1 then
		local last = tail[#tail]
		B:ell(0.12, H * 0.9, L * 0.22, at(0, y - 0.05, r[3] * 0.8 + L * 0.85), { col = "secondary", mat = "skin", bone = last, pri = 1.6, role = "fin", name = "TailFin", trail = true, mesh = "s_aq_caudal_fan" })
	end
	-- neck chain and head
	local n = if longNeck then (if detail >= 2 then 3 else 2) else 1
	local neckLen = if longNeck then L * 0.95 else L * 0.15
	local parent = "Body"
	local p = { 0, y + 0.05, -r[3] * 0.75 }
	local w = W * (if bigHead then 0.55 else 0.38)
	for i = 1, n do
		local u = i / n
		local q = { 0, y + neckLen * (if longNeck then 0.55 else 0.1) * u + (if longNeck then sin(u * math.pi) * 0.2 else 0), -r[3] * 0.75 - neckLen * u * (if longNeck then 0.75 else 1) }
		local bn = B:bone("Neck" .. i, parent, p[1], p[2], p[3])
		B:addRig("spine", bn)
		B:limb(p, q, w, { col = "primary", mat = "scale", bone = bn, pri = 1.2 + i * 0.1, role = "body", name = "Neck" }, 0.3)
		parent = bn
		p = q
		w *= 0.85
	end
	local hb = B:bone("Head", parent, p[1], p[2], p[3])
	B:setRig("head", hb)
	local s = if bigHead or mosa then 1.25 else 0.7
	Heads.reptile(B, { p = { p[1], p[2] - s * 0.05, p[3] + s * 0.2 }, s = s, bone = hb, eyes = if t.cute then "cute" else "fierce" }, (function()
		local tt = table.clone(t)
		tt.teeth = true
		return tt
	end)())
	B:socket("core", at(0, y, 0), "Body")
	B:setRig("gait", if legs then "sprawl" else "swim")
end

-- Merfolk: a person's torso, arms and head on a fish tail that curves down and back to a fluke.
function SeaMammal.mer(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local has = SeaFish.reader(ctx)
	local octo = has("tentacle", "octopus")
	local y = 1.4
	B.boneIndex.Body.pos = { 0, y + 1.2, 0 }
	-- torso
	local tc = { 0, y + 1.55, 0 }
	B:ell(1.15, 1.5, 0.75, at(tc[1], tc[2], tc[3]), { col = "skin", mat = "skin", pri = 1.05, role = "torso", name = "Torso", mesh = "s_torso" })
	-- hips: scales start here
	B:ell(1.05, 0.8, 0.8, at(0, y + 0.85, 0.05), { col = "primary", mat = "scale", pri = 1, role = "body", name = "Hips", mesh = false })
	if octo then
		for i = 1, (if detail >= 2 then 6 else 4) do
			local a = (i - 0.5) / (if detail >= 2 then 6 else 4) * math.pi * 2
			local bn = B:bone("Arm" .. i .. "_1", "Body", sin(a) * 0.35, y + 0.6, cos(a) * 0.35)
			local arm = B:limb({ sin(a) * 0.35, y + 0.6, cos(a) * 0.35 }, { sin(a) * 1.4, 0.2, cos(a) * 1.4 }, 0.36, { col = "primary", mat = "skin", bone = bn, pri = 1.3 + i * 0.05, role = "tentacle", trail = true }, 0.2)
			arm.cf = Geom.rollY(arm.cf, 0, -1, 0)
			B:addRig("tentacles", { bone = bn, index = i, seg = 1 })
		end
	else
		local parent = "Body"
		local p = { 0, y + 0.6, 0.1 }
		local w = 0.85
		local pts = { { 0, 0.55, 0.55 }, { 0, 0.25, 1.35 }, { 0, 0.35, 2.05 } }
		local n = if detail <= 0 then 2 else 3
		for i = 1, n do
			local q = pts[i]
			local bn = B:bone("Tail" .. i, parent, p[1], p[2], p[3])
			B:addRig("tail", bn)
			B:limb(p, q, w, { col = "primary", mat = "scale", bone = bn, pri = 1.1 + i * 0.15, role = "body", name = "TailSeg", depth = w * 0.9 }, 0.35)
			p = q
			parent = bn
			w *= 0.72
		end
		B:ell(1.5, 0.12, 0.7, at(0, p[2] + 0.12, p[3] + 0.3, rad(-15), 0, 0), { col = "secondary", mat = "skin", bone = parent, pri = 1.3, role = "fin", name = "Fluke", trail = true, mesh = "s_aq_fluke" })
	end
	-- arms and head
	local hand = Parts.armPair(B, { x = 0.62, y = tc[2] + 0.55, z = 0, len = 1.3, w = 0.28, col = "skin", hand = "fist", pri = 1.5 })
	local hb = B:bone("Head", "Body", 0, tc[2] + 0.75, 0)
	B:setRig("head", hb)
	local info = Heads.person(B, { p = { 0, tc[2] + 0.72, 0 }, s = 0.95, bone = hb, skin = "skin" }, t) :: any
	-- hair: a long mane down the back
	if detail >= 1 then
		B:ell(1.0, 1.5, 0.55, at(0, info.c[2] - 0.35, info.c[3] + 0.32), { col = if has("green-haired", "green hair") then "secondary" else "dark", mat = "fur", bone = hb, pri = 1.6, role = "hair", name = "Hair", mesh = false })
	end
	if (t.crown or has("crown", "queen")) and detail >= 1 then
		B:cyl(0.25, 0.75, at(0, info.top[2] + 0.02, info.c[3], 0, 0, rad(90)), { col = "gold", mat = "metal", bone = hb, pri = 2.0, role = "hat", name = "Crown" })
	elseif has("cap", "hat") and detail >= 1 then
		B:ell(0.95, 0.5, 0.95, at(0, info.top[2] - 0.02, info.c[3]), { col = "accent", mat = "cloth", bone = hb, pri = 2.0, role = "hat", name = "Cap", mesh = false })
	end
	if (has("trident", "scepter", "spear", "warrior") or t.trident) and detail >= 1 then
		B:rod({ hand[1], hand[2] - 1.0, hand[3] }, { hand[1], hand[2] + 1.6, hand[3] }, 0.12, { col = "gold", mat = "metal", bone = "ForeR", pri = 2.1, role = "weapon", name = "Shaft" })
		if detail >= 2 then
			for i = -1, 1 do
				B:wedge(0.06, 0.45, 0.16, at(hand[1] + i * 0.18, hand[2] + 1.75, hand[3], 0, 0, rad(i * 12)), { col = "gold", mat = "metal", bone = "ForeR", pri = 3 + math.abs(i) * 0.2, role = "spike", name = "Prong" })
			end
		end
	end
	if has("shark") and detail >= 1 then
		B:ell(0.12, 0.9, 0.6, at(0, tc[2] + 0.3, tc[3] + 0.45), { col = "primary", mat = "skin", pri = 1.8, role = "fin", name = "Dorsal", mesh = "s_aq_dorsal" })
	end
	if has("snake") and detail >= 2 then
		B:limb({ -0.7, tc[2] + 0.75, 0.1 }, { 0.75, tc[2] + 0.6, -0.15 }, 0.26, { col = "secondary", mat = "scale", pri = 2.6, role = "tail", name = "Snake" }, 0.3)
	end
	B:socket("core", at(0, tc[2], 0), "Body")
	B:setRig("gait", "float")
end

return SeaMammal
