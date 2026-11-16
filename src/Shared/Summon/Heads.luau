--!strict
-- Head builders shared by creature plans. Each places a head on bone `o.bone` whose pivot is `o.p` (neck top),
-- facing -Z, sized by `o.s`. Faces (eyes, brows, lids, mouth) come from Face with the word's mood.
-- Returns anchor points for horns/ears/crests and the mouth.

local Geom = require(script.Parent.Geom)
local Parts = require(script.Parent.Parts)
local Face = require(script.Parent.Face)

local at = Geom.at
local rad = math.rad

local Heads = {}

export type HeadInfo = { top: { number }, earY: number, earX: number, earZ: number, mouth: { number }, c: { number }, s: number }

local function eyeKind(t: any, o: any): string
	if o.eyes then
		return o.eyes
	end
	if t.undead or t.ghost or t.robot or t.glowEyes then
		return "glow"
	end
	if t.cute or t.size == "Tiny" or (t.size == "Small" and not t.mythical) then
		return "cute"
	end
	if (t.power or 5) >= 6 or t.spooky or t.mythical then
		return "fierce"
	end
	return "cute"
end
Heads.eyeKind = eyeKind

local function mood(B: any): string
	return (B.ctx.result and B.ctx.result.mood) or "Neutral"
end

function Heads.mammal(B: any, o: any, t: any): HeadInfo
	local s, p, bone = o.s, o.p, o.bone or "Head"
	local detail = t.detail or 2
	local c = { p[1], p[2] + s * 0.22, p[3] - s * 0.2 }
	local long = o.long or 1
	local r = { s * 0.5, s * 0.46, s * 0.48 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "fur", bone = bone, pri = 1.1, role = "head", name = "Head", mesh = "s_head_round" })
	local mz = c[3] - s * 0.42 * long
	local mr = { s * 0.32, s * 0.25, s * 0.3 * long }
	local mc = { c[1], c[2] - s * 0.18, mz }
	B:ell(mr[1] * 2, mr[2] * 2, mr[3] * 2, at(mc[1], mc[2], mc[3]), { col = o.muzzleCol or "belly", mat = "fur", bone = bone, pri = 1.6, role = "snout", name = "Muzzle" })
	if detail >= 1 then
		local np = Face.onEllipsoid(mc, mr, 0, mr[2] * 0.45)
		B:ell(s * 0.24, s * 0.16, s * 0.16, at(np[1], np[2], np[3] + s * 0.03), { col = "pupil", mat = "skin", bone = bone, pri = 2.4, role = "nose", name = "Nose" })
	end
	local kind = eyeKind(t, o)
	Face.build(B, {
		face = { kind = "ellipsoid", c = c, r = r }, mouthFace = { kind = "ellipsoid", c = mc, r = mr },
		bone = bone, mood = mood(B), detail = detail, kind = kind,
		spacing = s * 0.23, y = s * 0.08, d = s * (if kind == "cute" then 0.34 else 0.28) * (o.eyeScale or 1),
		mouthY = -mr[2] * 0.35, mouthW = s * 0.34, lidCol = "primary",
	})
	B:socket("mouth", at(c[1], c[2] - s * 0.28, mz - s * 0.3 * long), bone)
	return { top = { c[1], c[2] + s * 0.42, c[3] + s * 0.05 }, earX = s * 0.3, earY = c[2] + s * 0.3, earZ = c[3] + s * 0.06, mouth = { c[1], c[2] - s * 0.28, mz - s * 0.3 }, c = c, s = s }
end

function Heads.reptile(B: any, o: any, t: any): HeadInfo
	local s, p, bone = o.s, o.p, o.bone or "Head"
	local detail = t.detail or 2
	local c = { p[1], p[2] + s * 0.18, p[3] - s * 0.3 }
	local r = { s * 0.43, s * 0.36, s * 0.5 }
	local head = B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "scale", bone = bone, pri = 1.1, role = "head", name = "Head" })
	local sc = { c[1], c[2] - s * 0.04, c[3] - s * 0.66 }
	local sr = { s * 0.31, s * 0.22, s * 0.48 }
	local snout = B:ell(sr[1] * 2, sr[2] * 2, sr[3] * 2, at(sc[1], sc[2], sc[3], rad(4), 0, 0), { col = "primary", mat = "scale", bone = bone, pri = 1.3, role = "snout", name = "Snout" })
	-- one sculpt for skull + snout (same colour, same bone): brow ridges, nostrils, cheek plates
	B:sculpt(head, "s_head_reptile", { snout })
	local jawBone = B:bone("Jaw", bone, c[1], c[2] - s * 0.18, c[3] - s * 0.15)
	B:setRig("jaw", jawBone)
	if detail >= 1 then
		B:ell(s * 0.54, s * 0.24, s * 0.92, at(c[1], c[2] - s * 0.3, c[3] - s * 0.62, rad(-4), 0, 0), { col = "belly", mat = "scale", bone = jawBone, pri = 1.7, role = "jaw", name = "Jaw", mesh = "s_jaw" })
	end
	if detail >= 3 then
		B:mball(s * 0.1, at(s * 0.12, c[2] + s * 0.13, c[3] - s * 1.05), { col = "darker", mat = "skin", bone = bone, pri = 4.2, role = "nose" })
	end
	if detail >= 2 and (t.teeth or t.fangs or (t.power or 5) >= 7 or t.dino) then
		Parts.teeth(B, { bone = bone, y = c[2] - s * 0.22, z = c[3] - s * 0.98, r = s * 0.2, n = 2, h = s * 0.2, pri = 3.4 })
	end
	local kind = eyeKind(t, o)
	local m = mood(B)
	Face.build(B, {
		face = { kind = "ellipsoid", c = c, r = r }, mouthFace = { kind = "ellipsoid", c = sc, r = sr },
		bone = bone, mood = m, detail = detail, kind = kind,
		spacing = s * 0.27, y = s * 0.12, d = s * 0.27 * (o.eyeScale or 1),
		mouthY = -sr[2] * 0.2, mouthW = s * 0.36, noMouth = m == "Neutral", lidCol = "primary",
	})
	B:socket("mouth", at(c[1], c[2] - s * 0.2, c[3] - s * 1.2), bone)
	return { top = { c[1], c[2] + s * 0.32, c[3] + s * 0.1 }, earX = s * 0.32, earY = c[2] + s * 0.2, earZ = c[3] + s * 0.25, mouth = { c[1], c[2] - s * 0.2, c[3] - s * 1.2 }, c = c, s = s }
end

function Heads.bird(B: any, o: any, t: any): HeadInfo
	local s, p, bone = o.s, o.p, o.bone or "Head"
	local detail = t.detail or 2
	local c = { p[1], p[2] + s * 0.3, p[3] - s * 0.12 }
	local r = { s * 0.48, s * 0.48, s * 0.5 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "fur", bone = bone, pri = 1.1, role = "head", name = "Head", mesh = "s_head_bird" })
	local hooked = t.mythical or (t.power or 5) >= 6
	local beak = B:ell(s * 0.34, s * 0.3, s * (if hooked then 0.62 else 0.7), at(c[1], c[2] - s * 0.06, c[3] - s * 0.6, rad(if hooked then -14 else -4), 0, 0), { col = "beak", mat = "hard", bone = bone, pri = 1.3, role = "beak", name = "Beak" })
	local beakLow = nil
	if detail >= 2 then
		beakLow = B:ell(s * 0.26, s * 0.16, s * 0.45, at(c[1], c[2] - s * 0.19, c[3] - s * 0.5, rad(6), 0, 0), { col = "beak", mat = "hard", bone = bone, pri = 2.8, role = "beak", name = "BeakLow" })
	end
	-- both mandibles as one sculpt on the upper beak's frame
	B:sculpt(beak, "s_beak", { beakLow })
	local kind = eyeKind(t, o)
	Face.build(B, {
		face = { kind = "ellipsoid", c = c, r = r }, bone = bone, mood = mood(B), detail = detail, kind = kind,
		spacing = s * 0.27, y = s * 0.1, d = s * (if t.bigEyes then 0.4 else 0.3), noMouth = true, lidCol = "primary",
	})
	B:socket("mouth", at(c[1], c[2] - s * 0.1, c[3] - s * 0.9), bone)
	return { top = { c[1], c[2] + s * 0.45, c[3] + s * 0.05 }, earX = s * 0.3, earY = c[2] + s * 0.35, earZ = c[3], mouth = { c[1], c[2] - s * 0.1, c[3] - s * 0.9 }, c = c, s = s }
end

function Heads.bug(B: any, o: any, t: any): HeadInfo
	local s, p, bone = o.s, o.p, o.bone or "Head"
	local detail = t.detail or 2
	local c = { p[1], p[2] + s * 0.05, p[3] - s * 0.28 }
	local r = { s * 0.45, s * 0.39, s * 0.4 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = o.col or "dark", mat = "hard", bone = bone, pri = 1.1, role = "head", name = "Head", mesh = "s_head_bug" })
	local m = mood(B)
	Face.build(B, {
		face = { kind = "ellipsoid", c = c, r = r }, bone = bone, mood = m, detail = detail,
		kind = if t.cute or m ~= "Neutral" then "cute" else "bug",
		spacing = s * 0.27, y = s * 0.08, d = s * 0.42, mouthY = -r[2] * 0.45, mouthW = s * 0.3, noMouth = m == "Neutral" and not t.cute, lidCol = o.col or "dark", pri = 1.12,
	})
	if (t.antennae or t.insect) and detail >= 1 then
		B:mlimb({ s * 0.12, c[2] + s * 0.3, c[3] - s * 0.15 }, { s * 0.42, c[2] + s * 1.0, c[3] - s * 0.5 }, s * 0.07, { col = "darker", mat = "hard", bone = bone, pri = 2.4, role = "antenna" }, 0.05)
		if detail >= 2 then
			B:mball(s * 0.16, at(s * 0.44, c[2] + s * 1.03, c[3] - s * 0.52), { col = "secondary", mat = "hard", bone = bone, pri = 3.6, role = "antenna", trail = true })
		end
	end
	if detail >= 2 and (t.power or 5) >= 4 and not t.cute then
		B:mlimb({ s * 0.14, c[2] - s * 0.25, c[3] - s * 0.28 }, { s * 0.05, c[2] - s * 0.32, c[3] - s * 0.6 }, s * 0.11, { col = "darker", mat = "hard", bone = bone, pri = 3.2, role = "jaw" }, 0.1)
	end
	B:socket("mouth", at(c[1], c[2] - s * 0.3, c[3] - s * 0.5), bone)
	return { top = { c[1], c[2] + s * 0.38, c[3] }, earX = s * 0.3, earY = c[2] + s * 0.3, earZ = c[3], mouth = { c[1], c[2] - s * 0.3, c[3] - s * 0.5 }, c = c, s = s }
end

-- Mammal head archetypes: silhouette-first, cartoon-readable at phone distance. Each row is in head units (s):
--   cran   cranium semi-axes          snout  { y, z, rx, ry, rz, pitch } (nil = no separate snout)
--   cheeks feline/rodent whisker pads  nose   { kind, d } at the snout tip    ears   Parts.ears kind + scale
--   eyes   { spacing, y, d, yaw }      face   mouth placement on the snout (or the cranium)
local ARCH: { [string]: any } = {
	canine = { cran = { 0.44, 0.4, 0.44 }, snout = { -0.15, -0.5, 0.21, 0.17, 0.36, 4 }, nose = { "ball", 0.17 }, ears = { "pointy", 0.62 }, eyes = { 0.19, 0.13, 0.25 } },
	feline = { cran = { 0.5, 0.43, 0.44 }, cheeks = { -0.15, -0.34, 0.15, 0.12, 0.13 }, nose = { "tri", 0.11 }, ears = { "tri", 0.56 }, eyes = { 0.21, 0.07, 0.3 } },
	ursine = { cran = { 0.5, 0.46, 0.46 }, snout = { -0.15, -0.4, 0.22, 0.18, 0.25, 0 }, nose = { "ball", 0.18 }, ears = { "round", 0.36 }, eyes = { 0.2, 0.1, 0.2 } },
	equine = { cran = { 0.34, 0.37, 0.4 }, snout = { -0.34, -0.5, 0.23, 0.24, 0.55, 32 }, muzzle = { -0.62, -0.84, 0.27, 0.24, 0.26 }, nose = { "nostrils", 0.08 }, ears = { "pointy", 0.4 }, eyes = { 0.27, 0.1, 0.22, 34 } },
	bovine = { cran = { 0.46, 0.4, 0.42 }, muzzle = { -0.2, -0.42, 0.35, 0.26, 0.26 }, nose = { "nostrils", 0.09 }, ears = { "side", 0.5 }, eyes = { 0.26, 0.12, 0.22, 22 } },
	porcine = { cran = { 0.47, 0.43, 0.46 }, nose = { "disc", 0.38 }, ears = { "flop", 0.46 }, eyes = { 0.2, 0.12, 0.2 } },
	rodent = { cran = { 0.46, 0.42, 0.47 }, snout = { -0.1, -0.4, 0.2, 0.17, 0.28, 0 }, nose = { "ball", 0.11, "inner" }, ears = { "round", 0.5 }, eyes = { 0.23, 0.1, 0.27 }, teeth = true },
}
Heads.Arch = ARCH

-- o: p (pivot = neck top), s (size), bone, arch (ARCH key), ears (override kind), eyes (Face kind), noseCol
function Heads.beast(B: any, o: any, t: any): HeadInfo
	local s, p, bone = o.s, o.p, o.bone or "Head"
	local A = ARCH[o.arch] or ARCH.canine
	local detail = t.detail or 2
	local m = mood(B)
	local c = { p[1], p[2] + s * 0.16, p[3] - s * 0.14 }
	local r = { s * A.cran[1], s * A.cran[2], s * A.cran[3] }
	local head = B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "fur", bone = bone, pri = 1.1, role = "head", name = "Head",
		mesh = if o.arch == "feline" then "s_head_feline" else "s_head_round" })
	local mouthFace = { kind = "ellipsoid", c = c, r = r }
	local tip = { c[1], c[2] - s * 0.05, c[3] - r[3] } -- front-most point of the face (nose goes here)
	local mouthY = -r[2] * 0.45
	if A.snout then
		local sn = A.snout
		local sc = { c[1], c[2] + s * sn[1], c[3] + s * sn[2] }
		local sr = { s * sn[3], s * sn[4], s * sn[5] }
		local snoutCol = o.snoutCol or (if o.arch == "ursine" or o.arch == "rodent" then "belly" else "primary")
		local snout = B:ell(sr[1] * 2, sr[2] * 2, sr[3] * 2, at(sc[1], sc[2], sc[3], rad(-(sn[6] or 0)), 0, 0),
			{ col = snoutCol, mat = "fur", bone = bone, pri = 1.15, role = "snout", name = "Snout" })
		-- skull + same-coloured snout as one sculpt (the archetype fixes their layout in the head's unit frame)
		if snoutCol == "primary" and (o.arch == nil or o.arch == "canine" or ARCH[o.arch] == nil) then
			B:sculpt(head, "s_head_canine", { snout })
		elseif snoutCol == "primary" and o.arch == "equine" then
			B:sculpt(head, "s_head_equine", { snout })
		end
		local pitch = rad(sn[6] or 0)
		tip = { sc[1], sc[2] + sr[2] * 0.55 - math.sin(pitch) * sr[3] * 0.9, sc[3] - math.cos(pitch) * sr[3] * 0.92 }
		if sn[6] == 0 or sn[6] == nil or sn[6] < 10 then
			mouthFace = { kind = "ellipsoid", c = sc, r = sr }
			mouthY = -sr[2] * 0.5
		end
	end
	if A.muzzle then
		local mz = A.muzzle
		local mc = { c[1], c[2] + s * mz[1], c[3] + s * mz[2] }
		local mr = { s * mz[3], s * mz[4], s * mz[5] }
		B:ell(mr[1] * 2, mr[2] * 2, mr[3] * 2, at(mc[1], mc[2], mc[3]), { col = if o.arch == "bovine" then "inner" else "light", mat = "skin", bone = bone, pri = 1.16, role = "snout", name = "Muzzle" })
		tip = { mc[1], mc[2] + mr[2] * 0.2, mc[3] - mr[3] * 0.92 }
		mouthFace = { kind = "ellipsoid", c = mc, r = mr }
		mouthY = -mr[2] * 0.55
	end
	if A.cheeks then
		-- whisker pads: two puffs under the nose, the feline/rodent "w" mouth
		local ch = A.cheeks
		local cc = { s * 0.105, c[2] + s * ch[1], c[3] + s * ch[2] }
		B:mell(s * ch[3] * 2, s * ch[4] * 2, s * ch[5] * 2, at(cc[1], cc[2], cc[3]), { col = "belly", mat = "fur", bone = bone, pri = 1.15, role = "snout", name = "Cheek#" })
		tip = { c[1], cc[2] + s * ch[4] * 0.9, cc[3] - s * ch[5] * 0.55 }
		mouthFace = { kind = "ellipsoid", c = { c[1], cc[2], cc[3] }, r = { s * ch[3] * 2, s * ch[4], s * ch[5] } }
		mouthY = -s * ch[4] * 0.75
		if detail >= 3 then
			-- whiskers fan out of the pads (thin rods, angled apart so none run parallel)
			for i = 1, 2 do
				local y = cc[2] + s * (0.03 - i * 0.04)
				B:mrod({ cc[1] + s * 0.08, y, cc[3] - s * 0.06 }, { cc[1] + s * 0.62, y + s * (0.1 - i * 0.09), cc[3] + s * 0.02 }, s * 0.022,
					{ col = "white", mat = "hard", bone = bone, pri = 3.2 + i * 0.1, role = "detail", name = "Whisker" .. i .. "#", noCore = true })
			end
		end
	end
	-- nose
	local nose = A.nose
	if nose and detail >= 1 or (nose and nose[1] == "disc") then
		local nk, nd = nose[1], s * nose[2]
		local ncol = o.noseCol or nose[3] or (if nk == "tri" then "inner" else "pupil")
		if nk == "ball" then
			B:ell(nd * 1.35, nd * 0.95, nd, at(tip[1], tip[2], tip[3] + nd * 0.2), { col = ncol, mat = "glass", bone = bone, pri = 1.45, role = "nose", name = "Nose", noCore = true })
		elseif nk == "tri" then
			-- small downward wedge nose sitting on top of the whisker pads
			B:wedge(nd * 1.5, nd * 0.95, nd * 0.8, at(tip[1], tip[2] + nd * 0.25, tip[3] + nd * 0.1, rad(180), 0, 0), { col = ncol, mat = "skin", bone = bone, pri = 1.45, role = "nose", name = "Nose", noCore = true })
		elseif nk == "disc" then
			-- pig snout: a short cylinder pointing forward, two dark nostrils sunk into its face
			B:cyl(nd * 0.5, nd, at(c[1], c[2] - s * 0.1, c[3] - r[3] * 0.92, 0, rad(90), 0), { col = "inner", mat = "skin", bone = bone, pri = 1.15, role = "snout", name = "Snout" })
			tip = { c[1], c[2] - s * 0.1, c[3] - r[3] * 0.92 - nd * 0.25 }
			if detail >= 2 then
				B:mell(nd * 0.18, nd * 0.26, nd * 0.2, at(nd * 0.17, tip[2], tip[3] + nd * 0.02), { col = "darker", mat = "skin", bone = bone, pri = 2.2, role = "nose", name = "Nostril#", noCore = true })
			end
			mouthFace = { kind = "ellipsoid", c = c, r = r }
			mouthY = -r[2] * 0.6
		elseif nk == "nostrils" and detail >= 2 then
			B:mell(nd * 1.1, nd * 0.7, nd * 0.8, at(nd * 1.3, tip[2] + nd * 0.2, tip[3] + nd * 0.25, 0, rad(-15), 0), { col = "darker", mat = "skin", bone = bone, pri = 2.3, role = "nose", name = "Nostril#", noCore = true })
		end
	end
	if A.teeth and detail >= 2 then
		B:block(s * 0.13, s * 0.12, s * 0.06, at(tip[1], tip[2] - s * 0.27, tip[3] + s * 0.1, rad(-8), 0, 0), { col = "tooth", mat = "hard", bone = bone, pri = 1.7, role = "tooth", name = "BuckTeeth", noCore = true })
	end
	local E = A.eyes
	local kind = o.eyes or eyeKind(t, o)
	if o.arch == "feline" and kind == "fierce" then
		kind = "fierce"
	end
	Face.build(B, {
		face = { kind = "ellipsoid", c = c, r = r }, mouthFace = mouthFace,
		bone = bone, mood = m, detail = detail, kind = kind,
		spacing = s * E[1], y = s * E[2], d = s * E[3] * (o.eyeScale or 1),
		mouthY = mouthY, mouthW = s * 0.3, noMouth = m == "Neutral" and not t.cute, lidCol = "primary", pri = 1.12,
	})
	local mouth = { tip[1], tip[2] - s * 0.16, tip[3] + s * 0.04 }
	B:socket("mouth", at(mouth[1], mouth[2], mouth[3]), bone)
	return { top = { c[1], c[2] + r[2] * 0.95, c[3] + s * 0.04 }, earX = r[1] * 0.62, earY = c[2] + r[2] * 0.62, earZ = c[3] + r[3] * 0.18, mouth = mouth, c = c, s = s, r = r } :: any
end

-- Humanoid head: skull + face; hair/hat handled by the Humanoid plan.
function Heads.person(B: any, o: any, t: any): HeadInfo
	local s, p, bone = o.s, o.p, o.bone or "Head"
	local detail = t.detail or 2
	local c = { p[1], p[2] + s * 0.5, p[3] }
	local r = { s * 0.46, s * 0.5, s * 0.45 }
	local head = B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = o.skin or "skin", mat = "skin", bone = bone, pri = 1.1, role = "head", name = "Head", mesh = "s_head_person" })
	local kind = o.eyes or (if t.robot or t.undead then "glow" else "cute")
	Face.build(B, {
		face = { kind = "ellipsoid", c = c, r = r }, bone = bone, mood = mood(B), detail = detail, kind = kind,
		spacing = s * 0.18, y = s * 0.05, d = s * 0.24, mouthY = -s * 0.24, mouthW = s * 0.3,
		noMouth = o.noMouth, lidCol = o.skin or "skin", browCol = "hair",
	})
	if detail >= 3 and not o.noNose then
		local np = Face.onEllipsoid(c, r, 0, -s * 0.08)
		local nose = B:ell(s * 0.13, s * 0.17, s * 0.14, at(np[1], np[2], np[3] + s * 0.02), { col = o.skin or "skin", mat = "skin", bone = bone, pri = 3.8, role = "nose" })
		B:sculpt(head, "s_head_person", { nose })
	end
	B:socket("mouth", at(c[1], c[2] - s * 0.25, c[3] - s * 0.45), bone)
	return { top = { c[1], c[2] + s * 0.5, c[3] }, earX = s * 0.46, earY = c[2], earZ = c[3], mouth = { c[1], c[2] - s * 0.25, c[3] - s * 0.45 }, c = c, s = s, r = r } :: any
end

-- Generic face for objects (toaster, car, tree...). frame: model-space frame on the front surface (-Z out),
-- w: usable face width. Only built when the thing should have a face (see Heads.wantsFace).
function Heads.objectFace(B: any, t: any, frame: Geom.Frame, w: number, bone: string?, o: any?)
	local oo = o or {}
	Face.build(B, {
		face = { kind = "flat", cf = frame, curve = oo.curve }, bone = bone or "Body", mood = mood(B), detail = math.max(1, t.detail or 2),
		kind = oo.kind or "cute", spacing = w * 0.22, y = w * 0.12, d = w * (oo.eye or 0.26), mouthY = -w * 0.2, mouthW = w * 0.36,
		lidCol = oo.lidCol or "primary", pri = oo.pri or 1.5,
	})
end

function Heads.wantsFace(B: any, t: any): boolean
	local r = B.ctx.result
	if t.alive then
		return true
	end
	if r.mood and r.mood ~= "Neutral" then
		return true
	end
	return t.silly or t.cute or false
end

return Heads
