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
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "fur", bone = bone, pri = 1.1, role = "head", name = "Head" })
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
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "scale", bone = bone, pri = 1.1, role = "head", name = "Head" })
	local sc = { c[1], c[2] - s * 0.04, c[3] - s * 0.66 }
	local sr = { s * 0.31, s * 0.22, s * 0.48 }
	B:ell(sr[1] * 2, sr[2] * 2, sr[3] * 2, at(sc[1], sc[2], sc[3], rad(4), 0, 0), { col = "primary", mat = "scale", bone = bone, pri = 1.3, role = "snout", name = "Snout" })
	local jawBone = B:bone("Jaw", bone, c[1], c[2] - s * 0.18, c[3] - s * 0.15)
	B:setRig("jaw", jawBone)
	if detail >= 1 then
		B:ell(s * 0.54, s * 0.24, s * 0.92, at(c[1], c[2] - s * 0.3, c[3] - s * 0.62, rad(-4), 0, 0), { col = "belly", mat = "scale", bone = jawBone, pri = 1.7, role = "jaw", name = "Jaw" })
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
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "fur", bone = bone, pri = 1.1, role = "head", name = "Head" })
	local hooked = t.mythical or (t.power or 5) >= 6
	B:ell(s * 0.34, s * 0.3, s * (if hooked then 0.62 else 0.7), at(c[1], c[2] - s * 0.06, c[3] - s * 0.6, rad(if hooked then -14 else -4), 0, 0), { col = "beak", mat = "hard", bone = bone, pri = 1.3, role = "beak", name = "Beak" })
	if detail >= 2 then
		B:ell(s * 0.26, s * 0.16, s * 0.45, at(c[1], c[2] - s * 0.19, c[3] - s * 0.5, rad(6), 0, 0), { col = "beak", mat = "hard", bone = bone, pri = 2.8, role = "beak", name = "BeakLow" })
	end
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
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = o.col or "dark", mat = "hard", bone = bone, pri = 1.1, role = "head", name = "Head" })
	local m = mood(B)
	Face.build(B, {
		face = { kind = "ellipsoid", c = c, r = r }, bone = bone, mood = m, detail = detail,
		kind = if t.cute or m ~= "Neutral" then "cute" else "bug",
		spacing = s * 0.27, y = s * 0.08, d = s * 0.42, mouthY = -r[2] * 0.45, mouthW = s * 0.3, noMouth = m == "Neutral" and not t.cute, lidCol = o.col or "dark",
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

-- Humanoid head: skull + face; hair/hat handled by the Humanoid plan.
function Heads.person(B: any, o: any, t: any): HeadInfo
	local s, p, bone = o.s, o.p, o.bone or "Head"
	local detail = t.detail or 2
	local c = { p[1], p[2] + s * 0.5, p[3] }
	local r = { s * 0.46, s * 0.5, s * 0.45 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = o.skin or "skin", mat = "skin", bone = bone, pri = 1.1, role = "head", name = "Head" })
	local kind = o.eyes or (if t.robot or t.undead then "glow" else "cute")
	Face.build(B, {
		face = { kind = "ellipsoid", c = c, r = r }, bone = bone, mood = mood(B), detail = detail, kind = kind,
		spacing = s * 0.18, y = s * 0.05, d = s * 0.24, mouthY = -s * 0.24, mouthW = s * 0.3,
		noMouth = o.noMouth, lidCol = o.skin or "skin", browCol = "hair",
	})
	if detail >= 3 and not o.noNose then
		local np = Face.onEllipsoid(c, r, 0, -s * 0.08)
		B:ell(s * 0.13, s * 0.17, s * 0.14, at(np[1], np[2], np[3] + s * 0.02), { col = o.skin or "skin", mat = "skin", bone = bone, pri = 3.8, role = "nose" })
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
