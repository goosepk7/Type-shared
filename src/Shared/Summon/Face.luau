--!strict
-- Faces with mood expressions, for creatures AND objects ("angry toaster").
--
-- A face is described in a local "face frame": origin on the front surface of the thing, -Z pointing out of the
-- face, +Y up. Callers give either an ellipsoid head (centre + radii; features are projected onto its surface) or a
-- flat face (frame on a box face). Detail level (0..3) decides how many parts a face may spend:
--   0: dot eyes (2) + 0-1 mouth part     1: dot/lidded eyes (2-4) + mouth (1-2)
--   2: sclera + pupil (4) + mouth (2-3) + brows/lids      3: + highlights, blush, teeth, tongue
-- Every feature is a Ball/Ellipsoid/Block sunk part-way into the surface, never face-to-face.

local Geom = require(script.Parent.Geom)

local at = Geom.at
local rad = math.rad
local sqrt = math.sqrt

local Face = {}

export type Expression = {
	eye: string, -- "open" | "wide" | "lid" | "closed" | "happy" | "glow"
	pupil: number, -- pupil scale vs eye
	look: { number }, -- pupil offset (x, y) in eye radii
	lookR: { number }?, -- right eye override (crazy / confused)
	pupilR: number?,
	brow: number?, -- brow angle in degrees (+ = angry, inner end down); nil = no brows
	browR: number?, -- right brow override (confused / smug)
	browY: number?, -- brow height offset (eye radii)
	lid: number?, -- 0..1 upper lid coverage
	mouth: string, -- "smile" | "grin" | "open" | "frown" | "scowl" | "o" | "line" | "smirk" | "wavy" | "tongue" | "none"
	tongue: boolean?,
	teeth: boolean?,
	blush: boolean?,
	shine: number?, -- number of highlights
}

Face.Expressions = {
	Neutral = { eye = "open", pupil = 0.6, look = { 0, 0 }, mouth = "smile", shine = 1 },
	Angry = { eye = "open", pupil = 0.45, look = { 0, -0.05 }, brow = 24, browY = 0.05, mouth = "scowl", teeth = true, shine = 1 },
	Sleepy = { eye = "lid", pupil = 0.55, look = { 0, -0.15 }, lid = 0.62, mouth = "o", shine = 0 },
	Scared = { eye = "wide", pupil = 0.3, look = { 0, 0.05 }, brow = -22, browY = 0.35, mouth = "wavy", shine = 1 },
	Crazy = { eye = "wide", pupil = 0.62, pupilR = 0.25, look = { 0.15, 0.1 }, lookR = { -0.2, -0.2 }, mouth = "grin", tongue = true, teeth = true, shine = 1 },
	Hungry = { eye = "open", pupil = 0.72, look = { 0, -0.18 }, mouth = "open", tongue = true, shine = 2 },
	Happy = { eye = "happy", pupil = 0.6, look = { 0, 0 }, mouth = "grin", tongue = true, blush = true, shine = 1 },
	Sneaky = { eye = "lid", pupil = 0.5, look = { -0.3, -0.05 }, lid = 0.5, brow = 14, mouth = "smirk", shine = 1 },
	Lazy = { eye = "lid", pupil = 0.55, look = { 0, -0.2 }, lid = 0.55, mouth = "line", shine = 0 },
	Hyper = { eye = "wide", pupil = 0.78, look = { 0, 0.05 }, mouth = "grin", teeth = true, shine = 2 },
	Confused = { eye = "open", pupil = 0.45, look = { 0.25, 0.2 }, lookR = { -0.2, -0.1 }, brow = -18, browR = 10, mouth = "wavy", shine = 1 },
	Sad = { eye = "open", pupil = 0.62, look = { 0, -0.2 }, brow = -24, browY = 0.2, mouth = "frown", shine = 2 },
	Smug = { eye = "lid", pupil = 0.55, look = { 0.1, 0 }, lid = 0.45, brow = 8, browR = -14, mouth = "smirk", shine = 1 },
	Cute = { eye = "open", pupil = 0.74, look = { 0, -0.05 }, mouth = "smile", blush = true, shine = 2 },
} :: { [string]: Expression }

function Face.expression(mood: string?, fierce: boolean?): Expression
	local e = Face.Expressions[mood or "Neutral"] or Face.Expressions.Neutral
	if (mood == nil or mood == "Neutral") and fierce then
		return { eye = "open", pupil = 0.42, look = { 0, 0 }, brow = 20, mouth = "line", shine = 1 }
	end
	return e
end

-- Surface point of an ellipsoid (centre c, semi-axes r, axis-aligned) seen from the front (-Z) at offset (x, y).
function Face.onEllipsoid(c: { number }, r: { number }, x: number, y: number): { number }
	local u = math.clamp((x / r[1]) ^ 2 + (y / r[2]) ^ 2, 0, 0.96)
	local z = c[3] - r[3] * sqrt(1 - u)
	return { c[1] + x, c[2] + y, z }
end

-- Yaw/pitch so a feature at (x, y) on an ellipsoid faces along the surface normal.
local function normalAngles(r: { number }, x: number, y: number): (number, number)
	local yaw = math.atan2(x / (r[1] * r[1]), 1 / r[3]) * 0.9
	local pitch = math.atan2(y / (r[2] * r[2]), 1 / r[3]) * 0.9
	return yaw, pitch
end

-- Place a feature frame on the face. Face spec: { kind = "ellipsoid", c, r } or { kind = "flat", cf (frame on the
-- surface, -Z out), curve? (how much features wrap back with |x|) }.
local function place(face: any, x: number, y: number, sink: number): Geom.Frame
	if face.kind == "ellipsoid" then
		local p = Face.onEllipsoid(face.c, face.r, x, y)
		local yaw, pitch = normalAngles(face.r, x, y)
		-- rotate so local -Z is the outward normal; then push in by `sink` along it
		local f = at(p[1], p[2], p[3], pitch, -yaw, 0)
		return Geom.offset(f, 0, 0, sink)
	end
	local curve = face.curve or 0
	return Geom.mul(face.cf, at(x, y, sink + curve * x * x, 0, 0, 0))
end
Face.place = place

local function eye(B: any, face: any, o: any, side: number, e: Expression, d: number, bone: string, pri: number, mirrorPair: string?)
	local x = o.spacing * side
	local base = place(face, x, o.y, d * 0.18)
	local function add(spec: any)
		spec.bone = bone
		spec.noCore = true
		if side < 0 then
			spec.name = spec.name and (spec.name .. "L")
		else
			spec.name = spec.name and (spec.name .. "R")
		end
		return B:part(spec)
	end
	local isR = side > 0
	local pupilK = (if isR and e.pupilR then e.pupilR else e.pupil)
	local look = if isR and e.lookR then e.lookR else e.look
	local detail = o.detail
	local kind = o.kind or "cute"
	if kind == "glow" or kind == "robot" then
		local s = add({ shape = if kind == "robot" then "Block" else "Ellipsoid", size = if kind == "robot" then { d * 1.15, d * 0.6 * (1 - (e.lid or 0) * 0.6), d * 0.5 } else { d, d * 0.72 * (1 - (e.lid or 0) * 0.5), d * 0.6 },
			cf = base, col = "eyeGlow", mat = "neon", glow = true, pri = pri, role = "eye", name = "Eye", pair = mirrorPair })
		return s
	end
	if kind == "bug" then
		local s = add({ shape = "Ellipsoid", size = { d, d * 1.15, d }, cf = Geom.offset(base, 0, 0, d * 0.15), col = "bugEye", mat = "glass", pri = pri, role = "eye", name = "Eye", pair = mirrorPair })
		if detail >= 2 then
			add({ shape = "Ball", size = { d * 0.28, d * 0.28, d * 0.28 }, cf = Geom.mul(base, at(d * 0.14, d * 0.24, -d * 0.24)), col = "shine", mat = "neon", pri = pri + 2.4, role = "shine", name = "Shine", needs = s.pair })
		end
		return s
	end
	if e.eye == "happy" then
		-- closed happy eye: an upward arc ( ^ ) from two thin bars
		local a = add({ shape = "Ellipsoid", size = { d * 0.62, d * 0.16, d * 0.3 }, cf = Geom.mul(base, at(-d * 0.2, 0, -d * 0.02, 0, 0, rad(-32))), col = "pupil", mat = "skin", pri = pri, role = "eye", name = "EyeA", pair = mirrorPair })
		add({ shape = "Ellipsoid", size = { d * 0.62, d * 0.16, d * 0.3 }, cf = Geom.mul(base, at(d * 0.2, 0, -d * 0.03, 0, 0, rad(32))), col = "pupil", mat = "skin", pri = pri, role = "eye", name = "EyeB", pair = a.pair })
		return a
	end
	if detail <= 1 then
		-- dot eye: glossy dark ellipsoid, big enough to read on a phone; lids still read via squash
		local squash = 1 - (e.lid or 0) * 0.55
		local s = add({ shape = "Ellipsoid", size = { d * 0.78 * (if e.eye == "wide" then 1.1 else 1), d * 0.95 * squash, d * 0.55 },
			cf = Geom.mul(base, at(look[1] * d * 0.1, look[2] * d * 0.1 - (1 - squash) * d * 0.15, 0)), col = "pupil", mat = "glass", pri = pri, role = "eye", name = "Eye", pair = mirrorPair })
		if detail == 1 and (e.shine or 0) > 0 then
			add({ shape = "Ball", size = { d * 0.26, d * 0.26, d * 0.26 }, cf = Geom.mul(base, at(d * 0.15 + look[1] * d * 0.1, d * 0.2, -d * 0.24)), col = "shine", mat = "neon", pri = pri + 2.2, role = "shine", name = "Shine", needs = s.pair })
		end
		return s
	end
	local wide = if e.eye == "wide" then 1.15 else 1
	local sclera = add({ shape = "Ellipsoid", size = { d * wide, d * 1.08 * wide, d * 0.7 }, cf = base, col = "eyeWhite", mat = "skin", pri = pri, role = "eye", name = "Eye", pair = mirrorPair })
	local pr = d * pupilK
	local pcf = Geom.mul(base, at(look[1] * d * 0.3, look[2] * d * 0.3, -d * 0.22))
	add({ shape = "Ellipsoid", size = { pr * (if kind == "fierce" then 0.7 else 1), pr * 1.08, d * 0.42 }, cf = pcf, col = if kind == "fierce" then "iris" else "pupil", mat = "glass", pri = pri + 0.4, role = "pupil", name = "Pupil", needs = sclera.pair })
	if detail >= 3 and (e.shine or 0) > 0 then
		add({ shape = "Ball", size = { d * 0.22, d * 0.22, d * 0.22 }, cf = Geom.mul(pcf, at(pr * 0.24, pr * 0.3, -d * 0.16)), col = "shine", mat = "neon", pri = pri + 2.4, role = "shine", name = "Shine", needs = sclera.pair })
		if (e.shine or 0) > 1 then
			add({ shape = "Ball", size = { d * 0.12, d * 0.12, d * 0.12 }, cf = Geom.mul(pcf, at(-pr * 0.22, -pr * 0.26, -d * 0.15)), col = "shine", mat = "neon", pri = pri + 2.9, role = "shine", name = "Shine2", needs = sclera.pair })
		end
	end
	if (e.lid or 0) > 0 then
		-- upper eyelid: a slightly larger shell in the skin colour covering the top of the eye
		local lid = e.lid :: number
		add({ shape = "Ellipsoid", size = { d * 1.14 * wide, d * 1.2 * wide * (0.35 + lid * 0.6), d * 0.84 }, cf = Geom.mul(base, at(0, d * (0.55 - lid * 0.5), -d * 0.02, rad(-8), 0, 0)),
			col = o.lidCol or "primary", mat = "skin", pri = pri + 0.6, role = "lid", name = "Lid", needs = sclera.pair })
	end
	return sclera
end

local function brow(B: any, face: any, o: any, side: number, e: Expression, d: number, bone: string, pri: number, needs: string)
	local angle = if side > 0 and e.browR then e.browR else e.brow
	if angle == nil then
		return
	end
	local f = place(face, o.spacing * side, o.y + d * (0.72 + (e.browY or 0)), d * 0.1)
	-- inner end (towards x = 0) down for positive angles
	local tilt = rad(angle) * side
	B:part({ shape = "Ellipsoid", size = { d * 1.05, d * 0.22, d * 0.42 }, cf = Geom.mul(f, at(0, 0, 0, 0, 0, tilt)), col = o.browCol or "darker", mat = "skin",
		bone = bone, pri = pri + 0.9, role = "brow", name = if side > 0 then "BrowR" else "BrowL", needs = needs, noCore = true })
end

local function mouth(B: any, face: any, o: any, e: Expression, bone: string, pri: number)
	local w = o.mouthW
	local my = o.mouthY
	local detail = o.detail
	local kind = e.mouth
	if o.noMouth or kind == "none" then
		return
	end
	local function bar(x: number, y: number, len: number, thick: number, roll: number, name: string, p: number, col: string?)
		local f = place(face, x, y, thick * 0.25)
		B:part({ shape = "Ellipsoid", size = { len, thick, thick * 1.4 }, cf = Geom.mul(f, at(0, 0, 0, 0, 0, roll)), col = col or "mouth", mat = "skin", bone = bone, pri = p, role = "mouth", name = name, noCore = true })
	end
	if kind == "smile" or kind == "frown" or kind == "scowl" then
		local s = if kind == "smile" then 1 else -1
		if detail == 0 then
			bar(0, my - s * w * 0.04, w * 0.7, w * 0.16, 0, "Mouth", pri)
			return
		end
		bar(-w * 0.22, my, w * 0.56, w * 0.13, rad(-20) * s, "MouthL", pri)
		bar(w * 0.22, my, w * 0.56, w * 0.13, rad(20) * s, "MouthR", pri)
		if kind == "scowl" and e.teeth and detail >= 3 then
			local f = place(face, 0, my - w * 0.06, w * 0.06)
			B:part({ shape = "Block", size = { w * 0.5, w * 0.12, w * 0.12 }, cf = f, col = "tooth", mat = "hard", bone = bone, pri = pri + 2.5, role = "mouth", name = "Teeth", noCore = true })
		end
		return
	end
	if kind == "grin" or kind == "open" then
		-- "D" shaped open mouth: dark cavity + tongue + optional top teeth
		local f = place(face, 0, my - w * 0.1, w * 0.12)
		local hgt = if kind == "open" then w * 0.62 else w * 0.42
		B:part({ shape = "Ellipsoid", size = { w * (if kind == "grin" then 1.0 else 0.72), hgt, w * 0.4 }, cf = f, col = "mouth", mat = "skin", bone = bone, pri = pri, role = "mouth", name = "Mouth", noCore = true })
		if e.tongue and detail >= 2 then
			B:part({ shape = "Ellipsoid", size = { w * 0.45, hgt * 0.42, w * 0.3 }, cf = Geom.mul(f, at(w * 0.04, -hgt * 0.22, -w * 0.08)), col = "tongue", mat = "skin", bone = bone, pri = pri + 1.2, role = "mouth", name = "Tongue", noCore = true })
		end
		if e.teeth and detail >= 3 then
			B:part({ shape = "Block", size = { w * 0.55, hgt * 0.18, w * 0.16 }, cf = Geom.mul(f, at(0, hgt * 0.3, -w * 0.12)), col = "tooth", mat = "hard", bone = bone, pri = pri + 2.2, role = "mouth", name = "Teeth", noCore = true })
		end
		return
	end
	if kind == "o" then
		local f = place(face, 0, my, w * 0.08)
		B:part({ shape = "Ellipsoid", size = { w * 0.3, w * 0.36, w * 0.24 }, cf = f, col = "mouth", mat = "skin", bone = bone, pri = pri, role = "mouth", name = "Mouth", noCore = true })
		return
	end
	if kind == "smirk" then
		bar(w * 0.12, my + w * 0.02, w * 0.62, w * 0.12, rad(14), "Mouth", pri)
		return
	end
	if kind == "wavy" then
		if detail == 0 then
			bar(0, my, w * 0.6, w * 0.12, 0, "Mouth", pri)
			return
		end
		bar(-w * 0.17, my + w * 0.02, w * 0.4, w * 0.11, rad(18), "MouthL", pri)
		bar(w * 0.17, my - w * 0.02, w * 0.4, w * 0.11, rad(18), "MouthR", pri)
		return
	end
	-- line
	bar(0, my, w * 0.62, w * 0.11, 0, "Mouth", pri)
end

-- Build a full face. o fields:
--   face   { kind = "ellipsoid", c, r } | { kind = "flat", cf, curve? }
--   bone, mood, detail, spacing (eye x), y (eye y in face space; for ellipsoid relative to centre), d (eye size),
--   mouthY, mouthW, kind ("cute"|"fierce"|"glow"|"bug"|"robot"), noMouth, noBrows, pri, lidCol, browCol
function Face.build(B: any, o: any)
	local e = Face.expression(o.mood, o.kind == "fierce")
	local pri = o.pri or 1.5
	if (o.detail or 2) <= 1 then
		-- small budgets: the eyes outrank secondary limbs, a face is what makes the summon read as alive
		pri = math.min(pri, 1.12)
	end
	local bone = o.bone or "Body"
	local d = o.d
	local right = eye(B, o.face, o, 1, e, d, bone, pri, nil)
	local pair = right and right.pair or B:newPair()
	if right then
		right.pair = pair
	end
	local left = eye(B, o.face, o, -1, e, d, bone, pri, pair)
	-- eye pairs: keep both or none (the second eye's parts already share the pair id via mirrorPair)
	if o.detail >= 2 and not o.noBrows and e.eye ~= "happy" then
		brow(B, o.face, o, 1, e, d, bone, pri, pair)
		brow(B, o.face, o, -1, e, d, bone, pri, pair)
	end
	local neutral = o.mood == nil or o.mood == "Neutral"
	if not o.noMouth and o.mouthW and not (neutral and o.detail <= 1 and not o.forceMouth) then
		mouth(B, o.mouthFace or o.face, o, e, o.mouthBone or bone, pri + 0.3)
	end
	if e.blush and o.detail >= 3 and o.mouthW then
		for _, side in { 1, -1 } do
			local f = place(o.face, o.spacing * side * 1.25, o.y - d * 0.75, d * 0.12)
			B:part({ shape = "Ellipsoid", size = { d * 0.7, d * 0.36, d * 0.3 }, cf = f, col = "blush", mat = "skin", bone = bone, pri = pri + 2.8, role = "blush", name = if side > 0 then "BlushR" else "BlushL", noCore = true, needs = pair })
		end
	end
	local _ = left
	return pair
end

return Face
