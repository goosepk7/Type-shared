--!strict
-- Parts library: reusable anatomical and mechanical pieces placed in model space through a Builder.
-- Each function takes the builder and a small options table; positions are model-space design units.
-- Everything overlaps its parent volume (embedded), never sits face-to-face, so no coplanar faces arise.

local Geom = require(script.Parent.Geom)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local Parts = {}

-- EYES ------------------------------------------------------------------------------------------------------
-- o: bone, x (abs, right eye), y, z (centre), d (diameter), kind ("cute"|"fierce"|"glow"|"bug"|"robot"|"small"),
--    yaw (radians, eye turned outward), pri
function Parts.eyes(B: any, o: any)
	local d = o.d
	local yaw = o.yaw or rad(12)
	local kind = o.kind or "cute"
	local pri = o.pri or 2
	local bone = o.bone or "Head"
	local base = at(o.x, o.y, o.z, 0, -yaw, 0)
	if kind == "glow" or kind == "robot" then
		B:mirror({ shape = if kind == "robot" then "Block" else "Ellipsoid", size = if kind == "robot" then { d * 1.1, d * 0.55, d * 0.5 } else { d, d * 0.75, d * 0.7 }, cf = base, col = "eyeGlow", mat = "neon", glow = true, bone = bone, pri = pri, role = "eye", noCore = true })
		return
	end
	if kind == "bug" then
		B:mirror({ shape = "Ellipsoid", size = { d, d * 1.15, d }, cf = base, col = "bugEye", mat = "glass", bone = bone, pri = pri, role = "eye", noCore = true })
		B:mirror({ shape = "Ball", size = { d * 0.3, d * 0.3, d * 0.3 }, cf = Geom.mul(base, at(d * 0.12, d * 0.22, -d * 0.38)), col = "shine", mat = "neon", bone = bone, pri = pri + 2, role = "shine", noCore = true })
		return
	end
	-- sclera (white) as a slightly flattened ellipsoid facing forward
	local sclera = B:mirror({ shape = "Ellipsoid", size = { d, d * 1.05, d * 0.8 }, cf = base, col = "eyeWhite", mat = "skin", bone = bone, pri = pri, role = "eye", noCore = true })
	local needs = sclera.pair
	-- pupil (iris) pushed forward so it reads at distance: big for cute, slit-ish for fierce
	local pw, ph = d * 0.62, d * 0.66
	if kind == "fierce" then
		pw, ph = d * 0.36, d * 0.7
	end
	local pupil = Geom.mul(base, at(0, -d * 0.02, -d * 0.24))
	B:mirror({ shape = "Ellipsoid", size = { pw, ph, d * 0.5 }, cf = pupil, col = if kind == "fierce" then "iris" else "pupil", mat = "glass", bone = bone, pri = pri + 0.5, role = "pupil", noCore = true, needs = needs })
	-- specular highlight: small bright ball up and out from the pupil
	B:mirror({ shape = "Ball", size = { d * 0.22, d * 0.22, d * 0.22 }, cf = Geom.mul(pupil, at(d * 0.12, d * 0.16, -d * 0.2)), col = "shine", mat = "neon", bone = bone, pri = pri + 2.5, role = "shine", noCore = true, needs = needs })
	if kind == "fierce" then
		-- angry brow ridge angled down toward the centre
		B:mirror({ shape = "Block", size = { d * 1.25, d * 0.28, d * 0.5 }, cf = Geom.mul(base, at(-d * 0.05, d * 0.52, -d * 0.12, 0, 0, rad(-20))), col = "dark", mat = "skin", bone = bone, pri = pri + 1, role = "brow", needs = needs })
	end
end

-- HORNS -----------------------------------------------------------------------------------------------------
-- A curved horn made of tapering segments. o: bone, x, y, z (root, right side), len, w (root width),
-- kind ("swept" back, "curved" up-out, "ram" spiral, "straight" up, "uni" single centre), segs, pri, col
function Parts.horns(B: any, o: any)
	local kind = o.kind or "swept"
	local segs = o.segs or 3
	local pri = o.pri or 2
	local col = o.col or "horn"
	local function chain(px: number, py: number, pz: number, mirror: boolean)
		local x, y, z = px, py, pz
		local w = o.w
		local segLen = o.len / segs
		-- direction evolves per segment
		for i = 1, segs do
			local t = (i - 1) / math.max(1, segs - 1)
			local dx, dy, dz
			if kind == "swept" then
				dx, dy, dz = 0.25, 0.7 - t * 0.6, 0.6 + t * 0.4
			elseif kind == "curved" then
				dx, dy, dz = 0.7 - t * 0.5, 0.6 + t * 0.2, -0.1 - t * 0.3
			elseif kind == "ram" then
				local a = t * math.pi * 1.2
				dx, dy, dz = 0.35, cos(a), sin(a)
			elseif kind == "uni" then
				dx, dy, dz = 0, 0.75, -0.66
			else -- straight
				dx, dy, dz = 0.15, 1, -0.05
			end
			local nx, ny, nz = Geom.normalize(dx, dy, dz)
			local ex, ey, ez = x + nx * segLen, y + ny * segLen, z + nz * segLen
			local spec = {
				shape = "Ellipsoid",
				size = { w, segLen * 1.35, w },
				cf = (Geom.between(x, y, z, ex, ey, ez, "Y")),
				col = col, mat = "hard", bone = o.bone, pri = pri + (i - 1) * 0.3, role = "horn",
				trail = i == segs,
			}
			if mirror then
				B:mirror(spec)
			else
				B:part(spec)
			end
			x, y, z = ex, ey, ez
			w *= 0.68
		end
	end
	if kind == "uni" then
		chain(0, o.y, o.z, false)
	else
		chain(o.x, o.y, o.z, true)
	end
end

-- Antlers: main beam + 2 tines per side.
function Parts.antlers(B: any, o: any)
	local s = o.len
	local base = { o.x, o.y, o.z }
	local mid = { o.x + s * 0.35, o.y + s * 0.55, o.z + s * 0.15 }
	local tip = { o.x + s * 0.55, o.y + s * 1.0, o.z + s * 0.05 }
	B:mlimb(base, mid, s * 0.12, { col = "horn", mat = "wood", bone = o.bone, pri = 2, role = "horn" }, 0.12)
	B:mlimb(mid, tip, s * 0.1, { col = "horn", mat = "wood", bone = o.bone, pri = 2.5, role = "horn", trail = true }, 0.12)
	B:mlimb(mid, { mid[1] + s * 0.05, mid[2] + s * 0.35, mid[3] - s * 0.25 }, s * 0.08, { col = "horn", mat = "wood", bone = o.bone, pri = 3.5, role = "horn" }, 0.12)
end

-- EARS ------------------------------------------------------------------------------------------------------
-- kind: "pointy" (cat/fox, wedge-like ellipsoid tilted out), "round" (bear/mouse discs), "long" (rabbit),
-- "floppy" (dog), "big" (elephant), "fin" (dragon frills)
function Parts.ears(B: any, o: any)
	local kind = o.kind or "pointy"
	local s = o.s
	local pri = o.pri or 2
	if kind == "round" then
		B:mell(s, s, s * 0.35, at(o.x, o.y, o.z, 0, rad(-10), rad(-15)), { col = o.col or "primary", mat = "fur", bone = o.bone, pri = pri, role = "ear" })
		B:mell(s * 0.62, s * 0.62, s * 0.3, at(o.x + s * 0.0, o.y, o.z - s * 0.06, 0, rad(-10), rad(-15)), { col = "inner", mat = "fur", bone = o.bone, pri = pri + 1.5, role = "ear" })
	elseif kind == "long" then
		B:mell(s * 0.42, s * 1.7, s * 0.22, at(o.x, o.y + s * 0.75, o.z + s * 0.1, rad(-12), 0, rad(-14)), { col = "primary", mat = "fur", bone = o.bone, pri = pri, role = "ear", trail = true })
		B:mell(s * 0.26, s * 1.35, s * 0.2, at(o.x - s * 0.02, o.y + s * 0.78, o.z + s * 0.06, rad(-12), 0, rad(-14)), { col = "inner", mat = "fur", bone = o.bone, pri = pri + 1.5, role = "ear" })
	elseif kind == "floppy" then
		B:mell(s * 0.5, s * 1.25, s * 0.28, at(o.x + s * 0.12, o.y - s * 0.35, o.z + s * 0.05, 0, 0, rad(18)), { col = "dark", mat = "fur", bone = o.bone, pri = pri, role = "ear" })
	elseif kind == "big" then
		B:mell(s * 0.25, s * 1.4, s * 1.2, at(o.x, o.y - s * 0.1, o.z + s * 0.2, 0, rad(-25), 0), { col = "primary", mat = "skin", bone = o.bone, pri = pri, role = "ear" })
	elseif kind == "fin" then
		B:mwedge(s * 0.12, s * 0.9, s * 0.9, at(o.x, o.y + s * 0.2, o.z + s * 0.35, rad(-10), rad(-30), rad(-25)), { col = "secondary", mat = "skin", bone = o.bone, pri = pri, role = "ear" })
	elseif kind == "side" then
		-- cattle: leaf-shaped ears sticking out sideways under the horns
		B:mell(s * 0.95, s * 0.3, s * 0.5, at(o.x + s * 0.38, o.y - s * 0.12, o.z + s * 0.05, 0, rad(-20), rad(-18)), { col = "primary", mat = "fur", bone = o.bone, pri = pri, role = "ear" })
		B:mell(s * 0.62, s * 0.2, s * 0.32, at(o.x + s * 0.42, o.y - s * 0.12, o.z - s * 0.04, 0, rad(-20), rad(-18)), { col = "inner", mat = "fur", bone = o.bone, pri = pri + 1.5, role = "ear" })
	else
		-- triangular ear seen from the front: a wedge yawed so its right-triangle profile faces forward, the
		-- vertical edge on the inside, the slope falling to the outside, rolled outward. pointy = tall (wolf, fox),
		-- tri = broad (cat), flop = tipped forward (pig). The inner ear is a smaller wedge proud of the front face.
		local hgt, base, roll, pitch = s * 1.0, s * 0.62, rad(-12), rad(-6)
		if kind == "tri" then
			hgt, base, roll, pitch = s * 0.86, s * 0.78, rad(-22), rad(-4)
		elseif kind == "flop" then
			hgt, base, roll, pitch = s * 0.8, s * 0.7, rad(-30), rad(-58)
		end
		local thick = s * 0.16
		local root = at(o.x, o.y, o.z, pitch, 0, roll)
		local yaw = at(0, 0, 0, 0, -math.pi / 2, 0)
		local outer = Geom.mul(Geom.mul(root, at(base * 0.18, hgt * 0.42, 0)), yaw)
		local ro = B:mwedge(thick, hgt, base, outer, { col = if kind == "flop" then "primary" else (o.col or "primary"), mat = "fur", bone = o.bone, pri = pri, role = "ear", trail = kind == "pointy" })
		local inner = Geom.mul(Geom.mul(root, at(base * 0.18 - base * 0.05, hgt * 0.42 + hgt * 0.02, -thick * 0.32)), yaw)
		B:mwedge(thick * 0.6, hgt * 0.7, base * 0.58, inner, { col = "inner", mat = "fur", bone = o.bone, pri = pri + 1.6, role = "ear", needs = ro.pair })
	end
end

-- SPIKES ----------------------------------------------------------------------------------------------------
-- Row of wedge spikes along a polyline (list of {x,y,z, scale}) on the centre line. Wedge's vertical face is at
-- the back, slope faces forward: swept-back spines.
function Parts.spikeRow(B: any, o: any)
	local pts = o.points
	for i, p in pts do
		local h = o.h * (p[4] or 1)
		local tilt = p[5] or 0
		B:wedge(o.w or h * 0.22, h, h * 0.9, at(p[1], p[2] + h * 0.42, p[3], tilt, 0, 0), {
			col = o.col or "accent", mat = "hard", bone = p[6] or o.bone, pri = (o.pri or 3) + i * 0.05, role = "spike",
		})
	end
end

-- TEETH: a row of small downward wedges along an arc. o: bone, y, z (front), r (half width), n, h
function Parts.teeth(B: any, o: any)
	local n = o.n or 4
	for i = 1, n do
		local t = (i - 0.5) / n
		local x = (t - 0.5) * 2 * o.r
		local zz = o.z + math.abs(x) * 0.6
		B:wedge(o.h * 0.45, o.h, o.h * 0.5, at(x, o.y - o.h * 0.35, zz, math.pi, rad(180), 0), {
			col = "tooth", mat = "hard", bone = o.bone, pri = o.pri or 3.5, role = "tooth",
		})
	end
end

-- WINGS -----------------------------------------------------------------------------------------------------
-- Right wing (mirrored). Root at (x, y, z) on the Body; bone "Wing#" pivots there. span = tip distance.
-- kind: "bat" (arm bones + membrane panels), "feather" (layered flight feathers), "insect" (two translucent blades)
function Parts.wings(B: any, o: any)
	local x, y, z, span = o.x, o.y, o.z, o.span
	local kind = o.kind or "bat"
	local pri = o.pri or 1.5
	local rb, lb = B:mirrorBone("Wing#", o.parent or "Body", x, y, z)
	B:addRig("wings", { bone = rb, side = 1 })
	B:addRig("wings", { bone = lb, side = -1 })
	local detail = o.detail or B.ctx.detail or 3
	if detail <= 1 then
		-- single sculpted wing shape per side
		local col = if kind == "insect" then "wingGlass" elseif kind == "feather" then "primary" else "membrane"
		B:mell(span * 0.95, span * 0.07, span * (if kind == "feather" then 0.4 else 0.5), at(x + span * 0.46, y + span * 0.08, z + span * 0.12, 0, rad(-14), rad(10)),
			{ col = col, mat = if kind == "insect" then "glass" else "skin", tr = if kind == "insect" then 0.4 else nil, bone = "Wing#", pri = pri, role = "wing", trail = true,
				mesh = if kind == "bat" then "s_wing_bat" else nil, name = if kind == "bat" then "Membrane" else nil })
		return
	end
	if kind == "insect" then
		B:mell(span * 0.95, span * 0.06, span * 0.36, at(x + span * 0.45, y + span * 0.05, z + span * 0.05, 0, rad(-18), rad(8)),
			{ col = "wingGlass", mat = "glass", tr = 0.45, bone = "Wing#", pri = pri, role = "wing", trail = true })
		B:mell(span * 0.7, span * 0.05, span * 0.3, at(x + span * 0.32, y - span * 0.02, z + span * 0.28, 0, rad(-42), rad(4)),
			{ col = "wingGlass", mat = "glass", tr = 0.5, bone = "Wing#", pri = pri + 1.5, role = "wing" })
		return
	end
	if kind == "feather" then
		-- covert (arm) + 3 primaries fanned, each a flattened ellipsoid at a slightly different pitch
		B:mell(span * 0.55, span * 0.12, span * 0.38, at(x + span * 0.26, y + span * 0.02, z + span * 0.04, 0, rad(-4), rad(6)),
			{ col = "primary", mat = "fur", bone = "Wing#", pri = pri, role = "wing" })
		local n = o.feathers or 3
		for i = 1, n do
			local t = (i - 1) / math.max(1, n - 1)
			local ang = rad(-12 + t * 34)
			local cx = x + span * (0.55 + 0.1 * (1 - t))
			local cz = z + span * (0.08 + t * 0.22)
			B:mell(span * 0.62, span * (0.05 + i * 0.006), span * 0.16, at(cx, y + span * (0.01 + i * 0.012), cz, rad(i * 1.5), ang, rad(5 - i * 2)),
				{ col = if i == n then "secondary" else "wingTip", mat = "fur", bone = "Wing#", pri = pri + 0.5 + i * 0.5, role = "wing", trail = i == 1 })
		end
		return
	end
	-- bat / dragon: arm bone along the leading edge, then fingers, membrane panels between
	local shoulder = { x, y, z }
	-- raised in a strong V (the membrane shows as a sail from the side as well as from the front)
	local wrist0 = { x + span * 0.68, y + span * 0.56, z + span * 0.08 }
	local tips = {
		{ x + span * 0.98, y + span * 0.46, z + span * 0.18 },
		{ x + span * 0.86, y + span * 0.2, z + span * 0.42 },
		{ x + span * 0.55, y - span * 0.02, z + span * 0.55 },
	}
	-- membrane: ONE taut skin hanging from the arm, in the plane of the spread wing (root at the shoulder, tip at
	-- the longest finger). It is the wing's silhouette, so it survives the part budget right after the upper arm;
	-- bare wing bones read as an insect. Sculpt: s_wing_bat (ribs, scalloped trailing edge); primitive fallback:
	-- a thin ellipsoid sail.
	local tip, back = tips[1], tips[3]
	local mx, my, mz = (wrist0[1] + tip[1]) / 2 - x, (wrist0[2] + tip[2]) / 2 - y, (wrist0[3] + tip[3]) / 2 - z
	local ml = math.sqrt(mx * mx + my * my + mz * mz)
	local Xx, Xy, Xz = mx / ml, my / ml, mz / ml
	local L = math.sqrt((tip[1] - x) ^ 2 + (tip[2] - y) ^ 2 + (tip[3] - z) ^ 2)
	-- chord direction: toward the trailing inner finger, made perpendicular to the span axis
	local bx, by, bz = back[1] - (x + Xx * L * 0.5), back[2] - (y + Xy * L * 0.5), back[3] - (z + Xz * L * 0.5)
	local d = bx * Xx + by * Xy + bz * Xz
	bx, by, bz = bx - d * Xx, by - d * Xy, bz - d * Xz
	local bl = math.sqrt(bx * bx + by * by + bz * bz)
	local Zx, Zy, Zz = bx / bl, by / bl, bz / bl
	local Yx, Yy, Yz = Zy * Xz - Zz * Xy, Zz * Xx - Zx * Xz, Zx * Xy - Zy * Xx
	local chord = span * 0.66
	local cx, cy, cz = x + Xx * L * 0.52 + Zx * chord * 0.3, y + Xy * L * 0.52 + Zy * chord * 0.3, z + Xz * L * 0.52 + Zz * chord * 0.3
	-- the arm bones lie IN the membrane, along its leading edge (the edge curve of s_wing_bat at 42% and 76% of
	-- the span), so skin and bone never part company whatever the wing's pose
	local function onEdge(t: number): { number }
		local lx = (t - 0.5) * L * 1.02
		local lz = ((-0.31 + 0.1 * t * t + 0.04 * math.sin(math.pi * t)) / 0.62 + 0.012) * chord
		return { cx + Xx * lx + Zx * lz, cy + Xy * lx + Zy * lz, cz + Xz * lx + Zz * lz }
	end
	local elbow, wrist = onEdge(0.42), onEdge(0.76)
	B:mlimb(shoulder, elbow, span * 0.07, { col = "dark", mat = "skin", bone = "Wing#", pri = pri, role = "wing" }, 0.1)
	B:mlimb(elbow, wrist, span * 0.05, { col = "dark", mat = "skin", bone = "Wing#", pri = pri + 0.2, role = "wing" }, 0.1)
	-- finger spars (thin)
	for i, ft in (if detail >= 3 then tips else {}) do
		B:mrod(wrist, ft, span * 0.035, { col = "dark", mat = "skin", bone = "Wing#", pri = pri + 2 + i * 0.2, role = "wing", trail = i == 1 })
	end
	B:mell(L * 1.02, span * 0.03, chord, { cx, cy, cz, Xx, Yx, Zx, Xy, Yy, Zy, Xz, Yz, Zz },
		{ col = "membrane", mat = "skin", bone = "Wing#", pri = pri + 0.1, role = "wing", tr = o.membraneTr, mesh = "s_wing_bat", name = "Membrane" })
end

-- TAIL ------------------------------------------------------------------------------------------------------
-- Chain of tapering segments, each on its own bone for a whip-like wave. o: start {x,y,z}, dir {dx,dy,dz},
-- len, w, segs, droop (y per seg), kind ("plain"|"spiked"|"club"|"tuft"|"fan"|"bushy"|"stinger"), parent bone
function Parts.tail(B: any, o: any)
	local segs = o.segs or 3
	local x, y, z = o.start[1], o.start[2], o.start[3]
	local dx, dy, dz = Geom.normalize(o.dir[1], o.dir[2], o.dir[3])
	local segLen = o.len / segs
	local w = o.w
	local parent = o.parent or "Body"
	local bones = {}
	local kind = o.kind or "plain"
	for i = 1, segs do
		local bname = B:bone("Tail" .. i, parent, x, y, z)
		table.insert(bones, bname)
		local curl = o.curl or 0
		local ex = x + dx * segLen
		local ey = y + dy * segLen + (o.droop or 0) * (i / segs) + curl * i * segLen * 0.25
		local ez = z + dz * segLen
		local ww = if kind == "bushy" then w * (1.2 + 0.25 * i) else w
		B:limb({ x, y, z }, { ex, ey, ez }, ww, {
			col = if (i % 2 == 0 and o.banded) then "secondary" else (o.col or "primary"), mat = if kind == "bushy" then "fur" else "skin",
			bone = bname, pri = (o.pri or 1.1) + i * 0.4, role = "tail", trail = i == segs, depth = ww * (o.flat or 1),
		}, if kind == "bushy" then 0.4 else 0.3)
		if kind == "spiked" and i < segs then
			B:wedge(ww * 0.25, ww * 0.9, ww * 0.9, at((x + ex) / 2, (y + ey) / 2 + ww * 0.55, (z + ez) / 2, 0, 0, 0),
				{ col = "accent", mat = "hard", bone = bname, pri = 3 + i * 0.2, role = "spike" })
		end
		x, y, z = ex, ey, ez
		parent = bname
		w *= o.taper or 0.72
	end
	local last = bones[#bones]
	if kind == "club" then
		B:ell(w * 2.6, w * 2.0, w * 2.6, at(x, y, z), { col = "accent", mat = "hard", bone = last, pri = 2, role = "tail", trail = true })
	elseif kind == "tuft" then
		B:ell(w * 2.2, w * 2.2, w * 3.0, at(x, y, z + w), { col = o.tuftCol or "secondary", mat = "fur", bone = last, pri = o.tuftPri or 2.5, role = "tail" })
	elseif kind == "spiked" then
		B:wedge(w * 0.4, w * 1.6, w * 2.6, at(x, y + w * 0.3, z + w * 0.8, 0, 0, 0), { col = "accent", mat = "hard", bone = last, pri = 2.5, role = "spike", trail = true })
	elseif kind == "stinger" then
		B:limb({ x, y, z }, { x, y - w * 1.8, z - w * 1.6 }, w * 1.0, { col = "dark", mat = "hard", bone = last, pri = 2.2, role = "tail", trail = true }, 0.15)
	elseif kind == "fan" then
		B:mwedge(w * 0.3, w * 3.0, w * 3.2, at(w * 0.8, y + w * 0.6, z + w * 1.2, rad(-25), 0, rad(-30)), { col = "secondary", mat = "skin", bone = last, pri = 2.2, role = "tail" })
	end
	for _, b in bones do
		B:addRig("tail", b)
	end
	return bones, { x, y, z }
end

-- LEGS ------------------------------------------------------------------------------------------------------
-- One leg pair (mirrored). Hip at (x, y, z); bones Hip# (thigh) and Knee# (shin + foot).
-- kind: "pillar" (elephant), "paw" (mammal), "hoof", "claw" (reptile/digitigrade), "bird", "bug", "robot"
function Parts.legPair(B: any, o: any)
	local x, y, z = o.x, o.y, o.z
	local h = y -- hip height above ground
	local w = o.w
	local kind = o.kind or "paw"
	local tag = o.tag or "F"
	local hipName = "Hip" .. tag .. "#"
	local kneeName = "Knee" .. tag .. "#"
	local detail = o.detail or (B.ctx.detail or 3)
	local col0 = o.col or "primary"
	local mat0 = if kind == "robot" then "metal" else (o.mat or "skin")
	if detail <= 0 and kind ~= "bug" then
		-- one stubby "pair" mass under the body (phone-scale tiny summons): reads as legs, costs one part
		local hb = B:bone("Hip" .. tag, o.parent or "Body", 0, y, z)
		B:addRig("legs", { hip = hb, side = 0, phase = o.phase or 0, len = h })
		B:ell(x * 2 + w * 1.4, y * 1.25 + w * 0.3, w * 1.5, at(0, (y + w * 0.3) / 2 + 0.01, z + (o.footZ or 0)), { col = col0, mat = mat0, bone = hb, pri = o.pri or 1.2, role = "limb", name = "Legs" .. tag })
		return hb, hb
	end
	local hr, hl = B:mirrorBone(hipName, o.parent or "Body", x, y, z)
	if detail == 1 and kind ~= "bug" then
		B:addRig("legs", { hip = hr, side = 1, phase = o.phase or 0, len = h })
		B:addRig("legs", { hip = hl, side = -1, phase = (o.phase or 0) + 0.5, len = h })
		local fx, fz = x + (o.splay or 0), z + (o.footZ or 0)
		B:mlimb({ x, y + w * 0.4, z }, { fx, w * 0.35, fz - w * 0.1 }, w * (o.thigh or 1.2) * 0.92, { col = col0, mat = mat0, bone = hipName, pri = o.pri or 1.2, role = "limb", name = "Leg" .. tag .. "#" }, 0.22)
		return hr, hl
	end
	local bend = o.bend or (if kind == "claw" or kind == "bird" then 1 else -0.35) -- + knee forward... z offset sign
	local kx, ky, kz = x + (o.splay or 0) * 0.5, h * 0.48, z + bend * h * 0.12
	local kr, kl = B:mirrorBone(kneeName, hipName, kx, ky, kz)
	B:addRig("legs", { hip = hr, knee = kr, side = 1, phase = o.phase or 0, len = h })
	B:addRig("legs", { hip = hl, knee = kl, side = -1, phase = (o.phase or 0) + 0.5, len = h })
	local fx, fz = x + (o.splay or 0), z + (o.footZ or 0)
	local col = o.col or "primary"
	local mat = if kind == "robot" then "metal" else (o.mat or "skin")
	local pri = o.pri or 1.2
	if kind == "pillar" then
		B:mlimb({ x, y + w * 0.3, z }, { kx, ky, kz }, w * 1.05, { col = col, mat = mat, bone = hipName, pri = pri, role = "limb" }, 0.25)
		B:mcyl(ky + w * 0.2, w * 0.9, at(fx, (ky + w * 0.2) / 2 + 0.02, fz, 0, 0, rad(90)), { col = col, mat = mat, bone = kneeName, pri = pri, role = "limb" })
		B:mcyl(w * 0.18, w * 0.98, at(fx, w * 0.09 + 0.01, fz - 0.01, 0, 0, rad(90)), { col = "nail", mat = "hard", bone = kneeName, pri = pri + 2.5, role = "foot" })
		return hr, hl
	end
	if kind == "bug" then
		-- jointed bug leg: up-and-out femur, then down tibia
		local kneeX, kneeY = x + w * 3.2, y + w * 1.4
		local kr2 = B.boneIndex[kr]
		kr2.pos = { kneeX, kneeY, z }
		B.boneIndex[kl].pos = { -kneeX, kneeY, z }
		B:mlimb({ x, y, z }, { kneeX, kneeY, z }, w, { col = "dark", mat = "hard", bone = hipName, pri = pri, role = "limb" }, 0.12)
		B:mlimb({ kneeX, kneeY, z }, { kneeX + w * 1.6, 0.02, z + (o.footZ or 0) }, w * 0.75, { col = "dark", mat = "hard", bone = kneeName, pri = pri + 0.3, role = "limb" }, 0.08)
		return hr, hl
	end
	if kind == "bird" then
		B:mlimb({ x, y + w * 0.4, z }, { kx, ky, kz }, w * 1.2, { col = col, mat = "fur", bone = hipName, pri = pri, role = "limb" }, 0.2)
		B:mrod({ kx, ky, kz }, { fx, w * 0.45, fz }, w * 0.42, { col = "beak", mat = "hard", bone = kneeName, pri = pri + 0.2, role = "limb" })
		-- three toes: centre + two splayed
		for i, a in { 0, -35, 35 } do
			local ta = rad(a)
			local ex, ez = fx + sin(ta) * w * 1.4, fz - cos(ta) * w * 1.4
			B:mlimb({ fx, w * 0.3, fz }, { ex, w * 0.18, ez }, w * 0.35, { col = "beak", mat = "hard", bone = kneeName, pri = pri + 1.5 + i * 0.3, role = "foot", depth = w * 0.3 }, 0.1)
		end
		return hr, hl
	end
	-- thigh (bulky), shin, foot
	local thighW = w * (o.thigh or 1.3)
	B:mlimb({ x, y + w * 0.5, z }, { kx, ky, kz }, thighW, { col = col, mat = mat, bone = hipName, pri = pri, role = "limb" }, 0.3)
	B:mlimb({ kx, ky, kz }, { fx, if detail <= 2 then w * 0.3 else w * 0.5, fz }, w * 0.85, { col = col, mat = mat, bone = kneeName, pri = pri + 0.1, role = "limb" }, 0.2)
	if detail <= 2 then
		return hr, hl
	end
	if kind == "hoof" then
		B:mcyl(w * 0.55, w * 0.95, at(fx, w * 0.28 + 0.01, fz, 0, 0, rad(90)), { col = "hoof", mat = "hard", bone = kneeName, pri = pri + 0.8, role = "foot" })
	elseif kind == "robot" then
		B:mblock(w * 1.3, w * 0.5, w * 1.8, at(fx, w * 0.25 + 0.01, fz - w * 0.2), { col = "dark", mat = "metal", bone = kneeName, pri = pri + 0.5, role = "foot" })
	else
		local footLen = w * (if kind == "claw" then 1.9 else 1.5)
		B:mell(w * 1.15, w * 0.62, footLen, at(fx, w * 0.3 + 0.01, fz - footLen * 0.22), { col = col, mat = mat, bone = kneeName, pri = pri + 0.8, role = "foot" })
		if o.claws then
			for i, a in { -1, 0, 1 } do
				B:mwedge(w * 0.18, w * 0.32, w * 0.42, at(fx + a * w * 0.32, w * 0.16 + 0.01, fz - footLen * 0.68, 0, 0, 0) :: any,
					{ col = "claw", mat = "hard", bone = kneeName, pri = 3.6 + i * 0.1, role = "claw" })
			end
		end
	end
	return hr, hl
end

-- ARMS ------------------------------------------------------------------------------------------------------
-- Mirrored arm: shoulder (x,y,z) -> elbow -> hand. bones Arm#, Fore#. Returns hand frame for the right side.
function Parts.armPair(B: any, o: any)
	local x, y, z, len, w = o.x, o.y, o.z, o.len, o.w
	local ar, al = B:mirrorBone("Arm#", o.parent or "Body", x, y, z)
	local ex, ey, ez = x + len * (o.out or 0.18), y - len * 0.5, z - len * (o.fwd or 0.05)
	local hx, hy, hz = ex + len * (o.out2 or 0.02), ey - len * 0.46, ez - len * (o.fwd2 or 0.12)
	local fr, fl = B:mirrorBone("Fore#", "Arm#", ex, ey, ez)
	B:addRig("arms", { arm = ar, fore = fr, side = 1 })
	B:addRig("arms", { arm = al, fore = fl, side = -1 })
	local col = o.col or "primary"
	local mat = o.mat or "skin"
	B:mlimb({ x, y, z }, { ex, ey, ez }, w * (o.upper or 1.1), { col = o.sleeve or col, mat = o.sleeveMat or mat, bone = "Arm#", pri = o.pri or 1.4, role = "limb" }, 0.28)
	B:mlimb({ ex, ey, ez }, { hx, hy, hz }, w * 0.9, { col = o.foreCol or col, mat = o.foreMat or mat, bone = "Fore#", pri = (o.pri or 1.4) + 0.1, role = "limb" }, 0.2)
	local hand = o.hand or "fist"
	if hand == "fist" then
		B:mball(w * 1.25, at(hx, hy - w * 0.15, hz), { col = o.handCol or "skin", mat = "skin", bone = "Fore#", pri = (o.pri or 1.4) + 0.6, role = "hand", trail = true })
	elseif hand == "claw" then
		B:mell(w * 1.1, w * 0.8, w * 1.3, at(hx, hy - w * 0.1, hz - w * 0.2), { col = col, mat = mat, bone = "Fore#", pri = (o.pri or 1.4) + 0.6, role = "hand", trail = true })
		for i, a in { -1, 1 } do
			B:mwedge(w * 0.2, w * 0.55, w * 0.4, at(hx + a * w * 0.28, hy - w * 0.5, hz - w * 0.55, rad(160), 0, 0),
				{ col = "claw", mat = "hard", bone = "Fore#", pri = 3.8 + i * 0.1, role = "claw" })
		end
	elseif hand == "mitt" then
		B:mblock(w * 1.5, w * 1.3, w * 1.5, at(hx, hy - w * 0.25, hz), { col = o.handCol or "dark", mat = "metal", bone = "Fore#", pri = (o.pri or 1.4) + 0.6, role = "hand", trail = true })
	end
	B:socket("handR", at(hx, hy - w * 0.15, hz), "ForeR")
	B:socket("handL", at(-hx, hy - w * 0.15, hz), "ForeL")
	return { hx, hy - w * 0.15, hz }
end

-- WHEELS ----------------------------------------------------------------------------------------------------
-- Mirrored wheel at (x, y, z): tyre (cylinder along X) + hub cap (smaller cylinder, protruding) on bone Wheel..
function Parts.wheelPair(B: any, o: any)
	local idx = o.index or 1
	local r = o.r
	local wr, wl = B:mirrorBone("Wheel" .. idx .. "#", "Body", o.x, r, o.z)
	B:addRig("wheels", { bone = wr, r = r })
	B:addRig("wheels", { bone = wl, r = r })
	B:mcyl(o.w, r * 2, at(o.x, r, o.z), { col = "tyre", mat = "rubber", bone = "Wheel" .. idx .. "#", pri = 1.3, role = "wheel" })
	B:mcyl(o.w + 0.06, r * 1.1, at(o.x + 0.0, r, o.z), { col = o.hub or "metal", mat = "metal", bone = "Wheel" .. idx .. "#", pri = 2.8, role = "wheel" })
	if o.spokes then
		B:mblock(o.w + 0.03, r * 1.7, r * 0.18, at(o.x, r, o.z, rad(45), 0, 0), { col = "metal", mat = "metal", bone = "Wheel" .. idx .. "#", pri = 4.5, role = "wheel" })
	end
end

-- TREADS: track assembly along z with road wheels (mirrored). o: x, len, h, w
function Parts.treads(B: any, o: any)
	local x, len, h, w = o.x, o.len, o.h, o.w
	local r = h / 2
	-- track belt: block body + cylinder ends (rounded track)
	B:mblock(w, h, len - h, at(x, r, 0), { col = "tyre", mat = "rubber", pri = 1.1, role = "tread" })
	B:mcyl(w * 0.98, h, at(x, r, -(len - h) / 2), { col = "tyre", mat = "rubber", pri = 1.2, role = "tread" })
	B:mcyl(w * 0.98, h, at(x, r, (len - h) / 2), { col = "tyre", mat = "rubber", pri = 1.2, role = "tread" })
	-- road wheels poking out of the belt's outer face
	local n = o.wheels or 3
	for i = 1, n do
		local zz = -(len - h) / 2 + (i - 0.5) / n * (len - h)
		local bone = "Road" .. i .. "#"
		local rb, lb = B:mirrorBone(bone, "Body", x, r, zz)
		B:addRig("wheels", { bone = rb, r = r * 0.7 })
		B:addRig("wheels", { bone = lb, r = r * 0.7 })
		B:mcyl(w + 0.08, h * 0.62, at(x, r, zz), { col = "metal", mat = "metal", bone = bone, pri = 3 + i * 0.1, role = "wheel" })
	end
	-- mudguard
	B:mblock(w * 1.12, h * 0.12, len * 0.96, at(x, h + h * 0.04, 0), { col = "dark", mat = "metal", pri = 2.5, role = "detail" })
end

-- CRENELLATIONS: merlons around a rectangle or circle top. o: kind "rect"|"round", cx, cz, y, w|r, n, s
function Parts.crenellations(B: any, o: any)
	if o.kind == "round" then
		local n = o.n or 6
		for i = 1, n do
			local a = (i - 0.5) / n * math.pi * 2
			B:block(o.s, o.s * 1.1, o.s * 0.7, at(o.cx + sin(a) * o.r, o.y + o.s * 0.5, o.cz + cos(a) * o.r, 0, a, 0),
				{ col = o.col or "stone", mat = "stone", pri = (o.pri or 3) + i * 0.02, role = "detail" })
		end
		return
	end
	local n = o.n or 3
	for side = 1, 4 do
		for i = 1, n do
			local t = (i - 0.5) / n - 0.5
			local x, z, a
			if side == 1 then
				x, z, a = t * o.w, -o.d / 2, 0
			elseif side == 2 then
				x, z, a = t * o.w, o.d / 2, 0
			elseif side == 3 then
				x, z, a = -o.w / 2, t * o.d, math.pi / 2
			else
				x, z, a = o.w / 2, t * o.d, math.pi / 2
			end
			B:block(o.s, o.s * 1.1, o.s * 0.62, at(o.cx + x, o.y + o.s * 0.5, o.cz + z, 0, a, 0),
				{ col = o.col or "stone", mat = "stone", pri = (o.pri or 3) + (side * n + i) * 0.01, role = "detail" })
		end
	end
end

-- PETALS: ring of flattened ellipsoids around a centre facing +y / tilted outward.
function Parts.petals(B: any, o: any)
	local n = o.n or 6
	for i = 1, n do
		local a = (i - 1) / n * math.pi * 2 + (o.phase or 0)
		local r = o.r
		B:ell(o.s * 0.62, o.s * 0.1, o.s * 1.1, Geom.mul(at(o.x + sin(a) * r, o.y, o.z + cos(a) * r, 0, a, 0), at(0, 0, 0, rad(o.tilt or -25), 0, 0)),
			{ col = o.col or "secondary", mat = "leaf", bone = o.bone, pri = (o.pri or 2) + i * 0.05, role = "petal" })
	end
end

-- FINS: dorsal (centre wedge) / pectoral pair.
function Parts.dorsal(B: any, o: any)
	-- isosceles-ish shark fin from one wedge: vertical trailing edge at the back, swept leading slope
	B:wedge(o.t, o.h, o.l, at(0, o.y + o.h / 2 - 0.02, o.z, 0, 0, 0), { col = o.col or "primary", mat = "skin", bone = o.bone, pri = o.pri or 1.6, role = "fin", trail = true })
end

-- Text-free "glow mark": emissive accent ellipsoid (belly runes, crystal cores).
function Parts.gem(B: any, o: any)
	B:ell(o.s, o.s * (o.ky or 1.3), o.s * (o.kz or 0.7), o.cf, { col = o.col or "gem", mat = "neon", glow = true, bone = o.bone, pri = o.pri or 3, role = "gem", noCore = true })
end

return Parts
