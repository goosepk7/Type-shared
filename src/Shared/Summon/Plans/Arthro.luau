--!strict
-- Arthro: the shared kit of the arthropod and shelled builds (Plans/Insect, Arachnid, Crustacean, Chelonian).
-- Not a body plan itself (Plans/init only registers its fixed list): jointed legs with real knees, leg combs for
-- tiny budgets, antennae, mandibles, compound-eye heads and the word-matching helpers.
--
-- Leg pieces (catalogue/s_bugs.py): a single-part leg is a straight limb from hip to foot whose sculpt
-- (`s_arthro_leg`, `s_arthro_leg_long`, `s_crab_leg`) bends up into a knee above that line (local +Z is rolled
-- to world up, so the knee always points to the sky). The sculpt's knee height scales with the limb's width, so
-- callers keep width / length near the piece's reference ratio (Kit.LEG_RATIO). Two-part legs (detail 3) are a
-- femur rising to the knee and a tibia down to the foot. A leg comb (detail 0) is one primitive per side whose
-- sculpt carries three (insect) or four (spider) legs.

local Geom = require(script.Parent.Parent.Geom)
local Face = require(script.Parent.Parent.Face)

local at = Geom.at
local rad = math.rad

local Kit = {}

-- reference width / length of the whole-leg sculpts (catalogue/s_bugs.py LEG_REF)
Kit.LEG_RATIO = 0.085

-- whole-word match (plural -s / -es allowed) of any word in `list` inside `s`: "bee" never matches "beetle"
function Kit.has(s: string, list: string): boolean
	for w in string.gmatch(list, "%S+") do
		for _, suf in { "", "s", "es" } do
			if string.find(s, "%f[%a]" .. w .. suf .. "%f[%A]") then
				return true
			end
		end
	end
	return false
end

function Kit.text(ctx: any): (string, string)
	local id = string.lower(ctx.result.id or "")
	local hint = string.lower((ctx.result.visual and ctx.result.visual.silhouetteHint) or "")
	return id, hint
end

-- frame of the straight segment a -> b: local +Y along it, local +Z rolled toward `up` (default world up)
function Kit.segFrame(a: { number }, b: { number }, up: { number }?): (Geom.Frame, number)
	local f, len = Geom.between(a[1], a[2], a[3], b[1], b[2], b[3], "Y")
	local u = up or { 0, 1, 0 }
	return Geom.rollY(f, u[1], u[2], u[3]), len
end

-- A segment part a -> b whose local frame is rolled so +Z points toward `up` (asymmetric sculpts: horns that
-- curl, stings, folded arms rely on this). o: the part spec (col, mat, bone, pri, role, name, mesh, meshL ...),
-- w (local X), depth (local Z, default w), over (length overshoot). Mirrored with `mirror = true`.
function Kit.seg(B: any, a: { number }, b: { number }, w: number, o: any, up: { number }?): any
	local f, len = Kit.segFrame(a, b, up)
	local s = table.clone(o)
	s.shape, s.cf, s.seg = "Ellipsoid", f, "Y"
	s.size = { w, len * (1 + (o.over or 0.08)), o.depth or w }
	s.over, s.depth, s.mirror = nil, nil, nil
	if o.mirror then
		return B:mirror(s)
	end
	s.meshL = nil
	return B:part(s)
end

-- One mirrored leg (right side given). o:
--   tag, parent ("Body"), hip, foot, knee (two-part legs), w, col ("dark"), mat ("hard"), segs (1 | 2),
--   piece (whole-leg sculpt, default s_arthro_leg), pri, phase (0..1, the left leg is half a cycle later),
--   femur / tibia (piece ids of the two-part leg), trail
function Kit.leg(B: any, o: any)
	local hip, foot = o.hip, o.foot
	local bone = "Hip" .. o.tag .. "#"
	local hr, hl = B:mirrorBone(bone, o.parent or "Body", hip[1], hip[2], hip[3])
	local ph = o.phase or 0
	B:addRig("legs", { hip = hr, side = 1, phase = ph, len = hip[2] })
	B:addRig("legs", { hip = hl, side = -1, phase = (ph + 0.5) % 1, len = hip[2] })
	local col, mat, pri, w = o.col or "dark", o.mat or "hard", o.pri or 1.3, o.w
	if (o.segs or 1) >= 2 and o.knee then
		local knee = o.knee
		B:mlimb(hip, knee, w * 1.18, { col = col, mat = mat, bone = bone, pri = pri, role = "limb", name = "Femur" .. o.tag .. "#", mesh = o.femur or "s_arthro_seg" }, 0.14)
		B:mlimb(knee, foot, w * 0.86, { col = o.tipCol or col, mat = mat, bone = bone, pri = pri + 0.04, role = "limb", name = "Tibia" .. o.tag .. "#", mesh = o.tibia or "s_arthro_tibia", trail = o.trail }, 0.06)
		return
	end
	local f, len = Kit.segFrame(hip, foot)
	local piece = o.piece or "s_arthro_leg"
	B:mirror({ shape = "Ellipsoid", size = { w, len * 1.06, w }, cf = f, seg = "Y", col = col, mat = mat, bone = bone, pri = pri, role = "limb",
		name = "Leg" .. o.tag .. "#", mesh = piece, meshL = o.pieceL, trail = o.trail })
end

-- The knee of a two-part leg: `out` of the way from hip to foot, raised `rise` above the higher end.
function Kit.knee(hip: { number }, foot: { number }, out: number, rise: number): { number }
	return { hip[1] + (foot[1] - hip[1]) * out, math.max(hip[2], foot[2]) + rise, hip[3] + (foot[3] - hip[3]) * out }
end

-- A set of legs on one side (right side given; each is mirrored). legs = { { hip, foot }, ... } front to back.
-- o: tagBase, parent, w (or nil = length x LEG_RATIO x thick), thick, segs, rise (two-part knee height, x leg
-- length), piece, col, mat, pri, tripod (alternate phases: insects walk on tripods, spiders on alternating
-- tetrapods), wave (metachronal phase step for many legs)
function Kit.legSet(B: any, o: any, legs: { any })
	for i, l in legs do
		local hip, foot = l[1], l[2]
		local dx, dy, dz = foot[1] - hip[1], foot[2] - hip[2], foot[3] - hip[3]
		local len = math.sqrt(dx * dx + dy * dy + dz * dz)
		local w = (o.w or len * Kit.LEG_RATIO) * (o.thick or 1) * (l.thick or 1)
		local phase = if o.wave then ((i - 1) * o.wave) % 1 else ((i - 1) % 2) * 0.5
		local segs = l.segs or o.segs or 1
		Kit.leg(B, {
			tag = (o.tagBase or "L") .. i, parent = o.parent, hip = hip, foot = foot, w = w, col = l.col or o.col, mat = o.mat, segs = segs,
			knee = if segs >= 2 then Kit.knee(hip, foot, l.out or o.out or 0.42, len * (l.rise or o.rise or 0.32)) else nil,
			piece = l.piece or o.piece, pieceL = l.pieceL or o.pieceL, pri = (o.pri or 1.3) + i * 0.03 + (l.pri or 0), phase = phase,
			femur = o.femur, tibia = o.tibia, tipCol = o.tipCol,
		})
	end
end

Kit.COMB_THICK = { s_bug_legs3 = 1.1, s_bug_legs2 = 0.8, s_arachnid_legs4 = 1.0, s_arachnid_legs4_hairy = 1.0, s_crab_legs4 = 1.265 }

-- Leg comb (detail 0): one primitive per side, the middle leg, whose sculpt carries the whole side's legs.
function Kit.comb(B: any, o: any)
	local hip, foot = o.hip, o.foot
	local bone = "Hip" .. (o.tag or "C") .. "#"
	local hr, hl = B:mirrorBone(bone, o.parent or "Body", hip[1], hip[2], hip[3])
	B:addRig("legs", { hip = hr, side = 1, phase = 0, len = hip[2] })
	B:addRig("legs", { hip = hl, side = -1, phase = 0.5, len = hip[2] })
	local f, len = Kit.segFrame(hip, foot)
	-- the comb sculpt spans all the legs, so its width must stay the one it was sculpted at (a thicker plan leg
	-- would spread the whole fan sideways): the per-piece reference thickness wins over o.thick
	local w = o.w or len * Kit.LEG_RATIO * (Kit.COMB_THICK[o.piece or "s_bug_legs3"] or o.thick or 1)
	B:mirror({ shape = "Ellipsoid", size = { w, len * 1.06, w }, cf = f, seg = "Y", col = o.col or "dark", mat = o.mat or "hard", bone = bone, pri = o.pri or 1.3,
		role = "limb", name = "Comb#", mesh = o.piece or "s_bug_legs3", meshL = (o.piece or "s_bug_legs3") .. "_l" })
end

-- Antennae from the head. o: bone, base (right root), dir (unit-ish direction), len, w, kind:
--   "thread" (long whip), "club" (butterfly knob), "feather" (moth frond), "elbow" (ant: scape + flagellum),
--   "short" (beetle), "horn" (stout), col, pri, detail
function Kit.antennae(B: any, o: any)
	local b, d, len, w = o.base, o.dir, o.len, o.w or o.len * 0.06
	local col, pri, bone = o.col or "darker", o.pri or 1.6, o.bone or "Head"
	local tip = { b[1] + d[1] * len, b[2] + d[2] * len, b[3] + d[3] * len }
	local kind = o.kind or "thread"
	if kind == "elbow" then
		local el = { b[1] + d[1] * len * 0.42, b[2] + d[2] * len * 0.42 + len * 0.12, b[3] + d[3] * len * 0.42 }
		local t2 = { el[1] + d[1] * len * 0.2, el[2] - len * 0.15, el[3] + d[3] * len * 0.7 - len * 0.1 }
		B:mlimb(b, el, w * 1.1, { col = col, mat = "hard", bone = bone, pri = pri, role = "antenna", name = "Scape#" }, 0.08)
		if (o.detail or 2) >= 1 then
			B:mlimb(el, t2, w * 1.25, { col = col, mat = "hard", bone = bone, pri = pri + 0.5, role = "antenna", name = "Flag#", trail = true }, 0.08)
		end
		return
	end
	if kind == "feather" then
		-- moth: a broad feathery frond (flattened, in the plane of the head's front)
		local f = Kit.segFrame(b, tip, { 0, 0, -1 })
		B:mirror({ shape = "Ellipsoid", size = { len * 0.34, len * 1.04, len * 0.05 }, cf = f, seg = "Y", col = col, mat = "fur", bone = bone, pri = pri, role = "antenna", name = "Frond#", mesh = "s_bug_frond", trail = true })
		return
	end
	B:mlimb(b, tip, w, { col = col, mat = "hard", bone = bone, pri = pri, role = "antenna", name = "Antenna#", trail = kind ~= "club" }, 0.05)
	if kind == "club" and (o.detail or 2) >= 1 then
		B:mell(w * 2.6, w * 2.6, w * 4.2, Geom.mul(Kit.segFrame(b, tip), at(0, len * 0.5, 0, rad(90), 0, 0)), { col = o.clubCol or col, mat = "hard", bone = bone, pri = pri + 0.4, role = "antenna", name = "Club#", trail = true })
	end
end

-- Mandibles: a mirrored pair of curved jaws at the front of the head. o: bone, root (right), len, w, spread,
-- col, pri, piece (s_bug_mandible; stag beetles: s_stag_jaw), up (how much they rise)
function Kit.mandibles(B: any, o: any)
	local r, len = o.root, o.len
	local tip = { r[1] + len * (o.spread or 0.25), r[2] + len * (o.up or 0), r[3] - len }
	local f, l = Kit.segFrame(r, tip)
	local piece = o.piece or "s_bug_mandible"
	B:mirror({ shape = "Ellipsoid", size = { o.w or len * 0.32, l * 1.08, o.depth or (o.w or len * 0.32) * 0.7 }, cf = f, seg = "Y", col = o.col or "darker", mat = "hard", bone = o.bone or "Head",
		pri = o.pri or 1.5, role = "jaw", name = "Mandible#", mesh = piece, meshL = piece .. "_l", trail = true })
end

-- Insect head: an ellipsoid with compound (or cute) eyes. o: c (centre), r (radii), bone, col, eyeD, eyeY,
-- spacing, piece (head sculpt), kind ("bug" compound eyes | "cute" | "fierce" | "glow"), mood, detail, pri
function Kit.head(B: any, o: any): any
	local c, r = o.c, o.r
	local head = B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3], o.pitch or 0, 0, 0), { col = o.col or "primary", mat = o.mat or "hard", bone = o.bone or "Head", pri = o.pri or 1.08,
		role = "head", name = "Head", mesh = if o.piece == false then nil else (o.piece or "s_head_bug") })
	if o.noFace then
		return head
	end
	Face.build(B, {
		face = { kind = "ellipsoid", c = c, r = r }, bone = o.bone or "Head", mood = o.mood, detail = o.detail,
		kind = o.kind or "bug", spacing = o.spacing or r[1] * 0.62, y = o.eyeY or r[2] * 0.15, d = o.eyeD or r[1] * 0.75,
		mouthY = -r[2] * 0.5, mouthW = r[1] * 0.6, noMouth = o.noMouth, noBrows = o.noBrows, lidCol = o.col or "primary", pri = 1.12,
	})
	return head
end

-- mood of the word, with "menacing" words kept stern
function Kit.mood(ctx: any): string
	return ctx.result.mood or "Neutral"
end

-- face kind: cute words get big friendly eyes, the rest compound bug eyes (fierce ones when menacing)
function Kit.eyeKind(ctx: any, t: any): string
	local m = ctx.result.mood or "Neutral"
	if t.robot or t.mechanical then
		return "glow"
	end
	if t.cute or (m ~= "Neutral" and m ~= "Angry") then
		return "cute"
	end
	return "bug"
end

return Kit
