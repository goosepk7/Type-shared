--!strict
-- Insects: every build has the three tagmata (head, thorax, abdomen), six jointed legs with knees above the body
-- line, antennae and the mouthparts of its order. The Library's silhouette hints cluster into these sub-kinds, each
-- with its own proportions and signature parts:
--   Beetle    domed elytra over a pronotum, small head, mandibles; horns (rhino / hercules / atlas), stag jaws,
--             weevil rostrum, ladybug spots, long-horn antennae, tortoise-beetle flange
--   Ant       big head with mandibles and elbowed antennae, slim thorax, petiole node, oval gaster (queen: wings)
--   Fly       round thorax, huge compound eyes, glassy wings swept back, short abdomen; bee / wasp bands and
--             stinger, mosquito proboscis and stilt legs, cicada tented wings, firefly glow
--   Butterfly broad scalloped fore and hind wings raised in a V, slim body, clubbed antennae (tails, eyespots)
--   Moth      wide flat wings swept back, furry body, feathery antennae
--   Dragonfly huge eyes, slim segmented abdomen, four long wings held flat
--   Mantis    upright prothorax, triangular head, folded raptorial forelegs, wings folded on the abdomen
--   Hopper    grasshopper / cricket / katydid: tall face, saddle pronotum, huge jumping hind legs
--   Roach     flat: pronotum shield, long whip antennae, spiny sprawled legs (earwig pincers, silverfish tails,
--             water strider stilts)
--   Stick     twig body and legs (leaf insect: leaf-flat body)
--   Crawler   centipede / larva: a chain of segments with a leg pair each (larva: none)
-- Arachnids, crustaceans and snails that the Library files under Insect go to Plans/Arachnid and
-- Plans/Crustacean; the walking machines (walker, robot arm monster) are built here.
--
-- Detail: 0 (Tiny) legs are one comb per side (sculpt s_bug_legs3); 1-2 one part per leg, its sculpt bends into the
-- knee; 3 femur + tibia. Sculpts: catalogue/s_bugs.py.

local Geom = require(script.Parent.Parent.Geom)
local Kit = require(script.Parent.Arthro)

local at = Geom.at
local rad = math.rad
local has = Kit.has

local function arachnid(): any
	return require(script.Parent.Arachnid) :: any
end
local function crustacean(): any
	return require(script.Parent.Crustacean) :: any
end

local function kindOf(ctx: any): string
	local id, hint = Kit.text(ctx)
	local t = ctx.traits
	if ctx.kind == "Spider" or ctx.kind == "Crab" then
		return ctx.kind
	end
	-- machines and chimeras first
	if has(id, "walker") and not has(id, "spider") then
		return "Walker"
	elseif has(id, "robot arm") then
		return "ArmBot"
	end
	if has(id, "snail slug") then
		return "Snail"
	end
	if (has(id, "crab") and not has(id, "spider")) or has(id, "karkinos lobster shrimp") then
		return "Crab"
	end
	if has(id, "scorpion pseudoscorpion") then
		return "Scorpion"
	end
	if has(id, "spider tarantula drider jorogumo anansi tick mite harvestman") or has(id, "ushi") or has(id, "face grabber") or string.find(hint, "eight", 1, true) then
		return "Spider"
	end
	if has(id, "centipede millipede larva grub caterpillar maggot crawler") or string.find(hint, "segmented body", 1, true) then
		return "Crawler"
	end
	if has(id, "mantis mantisfly") then
		return "Mantis"
	end
	if has(id, "dragonfly damselfly meganeura mayfly") then
		return "Dragonfly"
	end
	if has(id, "butterfly swallowtail monarch morpho admiral lady white birdwing") then
		return "Butterfly"
	end
	if has(id, "moth lanternfly caddisfly") then
		return "Moth"
	end
	if has(id, "ant antlion termite") or has(id, "xeno") or has(id, "alien queen") then
		return "Ant"
	end
	if has(id, "grasshopper cricket katydid weta locust leafhopper treehopper spittlebug flea") then
		return "Hopper"
	end
	if has(id, "stick leaf") and has(id, "insect") then
		return "Stick"
	end
	if has(id, "cockroach roach silverfish earwig louse bed strider backswimmer assassin") or has(id, "water bug") then
		return "Roach"
	end
	if has(id, "fly flies bee bumblebee wasp hornet mosquito gnat midge cicada lacewing firefly horsefly botfly hoverfly blowfly sawfly dobsonfly snakefly scorpionfly adze aphid stonefly") then
		return "Fly"
	end
	if has(id, "beetle ladybug ladybird weevil bug insect") then
		return "Beetle"
	end
	if t.wings or t.flies then
		return "Fly"
	end
	return "Beetle"
end

-- shared body build ---------------------------------------------------------------------------------------------

-- Three tagmata. S: y (thorax centre height), T {w,h,l} thorax, Tp thorax pitch (deg), H {rx,ry,rz} head radii,
-- hy/hz head offset, Hp head pitch, A {w,h,l} abdomen, Ap abdomen pitch, gap (waist), ay (abdomen lift),
-- col / abCol / thCol, mat / abMat, thPiece / abPiece / headPiece, node (ant petiole), eye {d, spacing, y}
local function tagmata(B: any, ctx: any, S: any): any
	local t, detail = ctx.traits, ctx.detail
	local y = S.y
	B.boneIndex.Body.pos = { 0, y, 0 }
	local T, A, H = S.T, S.A, S.H
	local thorax = B:ell(T[1], T[2], T[3], at(0, y, 0, rad(S.Tp or 0), 0, 0), { col = S.thCol or S.col or "primary", mat = S.mat or "hard", pri = 1.02, role = "body", name = "Thorax", mesh = S.thPiece or "s_bug_thorax" })
	-- abdomen behind the thorax (its own bone, so it sways)
	local az = T[3] * 0.42 + (S.gap or 0) + A[3] * 0.45
	local ay = y + (S.ay or 0)
	local ab = B:bone("Abdomen", "Body", 0, y, T[3] * 0.4)
	B:addRig("tail", ab)
	local abdomen = B:ell(A[1], A[2], A[3], at(0, ay, az, rad(S.Ap or -6), 0, 0), { col = S.abCol or S.col or "primary", mat = S.abMat or S.mat or "hard", bone = ab, pri = 1, role = "body", name = "Abdomen", mesh = S.abPiece or "s_bug_abdomen" })
	local node
	if S.node and detail >= 1 then
		node = B:ell(S.node, S.node * 1.1, S.node * 1.1, at(0, y + S.node * 0.15, T[3] * 0.42 + (S.gap or 0) * 0.5), { col = S.col or "primary", mat = S.mat or "hard", bone = ab, pri = 1.7, role = "body", name = "Petiole" })
	end
	-- head in front
	local hc = { 0, y + (S.hy or 0), -(T[3] * 0.44 + H[3] * (S.hz or 0.72)) }
	B:bone("Head", "Body", 0, hc[2], -T[3] * 0.42)
	B:setRig("head", "Head")
	local mood = Kit.mood(ctx)
	local ek = S.eyeKind or Kit.eyeKind(ctx, t)
	local e = S.eye or {}
	local head = Kit.head(B, {
		c = hc, r = H, pitch = rad(S.Hp or 0), col = S.headCol or S.col or "primary", mat = S.mat, piece = S.headPiece, mood = mood, detail = detail, kind = ek,
		eyeD = (e.d or (if ek == "bug" then 0.95 else 0.8)) * H[1], spacing = (e.spacing or (if ek == "bug" then 0.7 else 0.5)) * H[1], eyeY = (e.y or 0.18) * H[2],
		noMouth = ek == "bug" or S.noMouth, noBrows = ek == "bug" or detail < 3,
	})
	return { y = y, T = T, A = A, H = H, hc = hc, az = az, ay = ay, ab = ab, thorax = thorax, abdomen = abdomen, head = head, node = node }
end

-- Six legs from the thorax underside. L: hipX, hipY (below centre), z = { front, mid, hind } hip z, feet = { {x, z}
-- per leg }, footY, segs override, piece, thick, col, rise (two-part)
local function sixLegs(B: any, ctx: any, b: any, L: any)
	local detail = ctx.detail
	local y = b.y
	local hx, hy = L.hipX or b.T[1] * 0.3, y - (L.hipY or b.T[2] * 0.22)
	local zs = L.z or { -b.T[3] * 0.28, 0, b.T[3] * 0.28 }
	local feet = L.feet
	local fy = L.footY or 0.04
	if detail <= 1 and not L.noComb then
		-- one comb per side: the middle leg is the primitive, the sculpt carries all three
		Kit.comb(B, { hip = { hx, hy, zs[2] }, foot = { feet[2][1], fy, feet[2][2] }, col = L.col, thick = L.thick, piece = L.comb or "s_bug_legs3", pri = 1.3 })
		return
	end
	local legs = {}
	for i = 1, 3 do
		local f = feet[i]
		table.insert(legs, { { hx, hy, zs[i] }, { f[1], f[3] or fy, f[2] }, thick = (L.thicks and L.thicks[i]) or 1, piece = L.pieces and L.pieces[i] or nil, segs = L.segsBy and L.segsBy[i] or nil })
	end
	Kit.legSet(B, { tagBase = "L", w = nil, thick = L.thick, segs = L.segs or (if detail >= 3 then 2 else 1), rise = L.rise or 0.3, piece = L.piece, col = L.col or "dark", pri = 1.3 }, legs)
end

-- Insect wings. kind: "glass" (fly / bee / lacewing), "tent" (cicada: folded roof), "bfly" (butterfly V),
-- "moth" (flat, swept), "dfly" (dragonfly: four long flat wings), "fold" (mantis / katydid / roach: closed on
-- the back). o: x, y, z (root), span, chord, col, sweep, raise, hind (bool), clear
local function wings(B: any, ctx: any, o: any)
	local detail = ctx.detail
	local kind = o.kind
	local rb, lb = B:mirrorBone("Wing#", "Body", o.x, o.y, o.z)
	local fold = kind == "fold" or kind == "tent"
	if not fold then
		B:addRig("wings", { bone = rb, side = 1 })
		B:addRig("wings", { bone = lb, side = -1 })
	end
	local span, chord = o.span, o.chord
	local glassy = kind == "glass" or kind == "dfly" or kind == "tent" or o.clear
	local col = o.col or (if glassy then "wingGlass" else "primary")
	local mat = if glassy then "glass" else "skin"
	local tr = if glassy then 0.42 else nil
	local function wing(name: string, sx: number, sz: number, cf: any, pri: number, piece: string?)
		return B:mell(sx, math.max(span * 0.035, 0.03), sz, cf, { col = col, mat = mat, tr = tr, bone = "Wing#", pri = pri, role = "wing", name = name .. "#", trail = true, mesh = piece, meshL = if piece then piece .. "_l" else nil })
	end
	if kind == "bfly" or kind == "moth" then
		-- forewing: leading edge from the root out and forward; hindwing rounder, behind it. Butterflies hold them in
		-- a raised V, moths flat and swept back.
		local raise = rad(o.raise or (if kind == "bfly" then 34 else 8))
		local sweep = rad(o.sweep or (if kind == "bfly" then -8 else 18))
		local fx, fz = o.x + span * 0.45 * math.cos(raise), o.z - chord * 0.08
		local fw = wing("Forewing", span * 0.98, chord, at(fx, o.y + span * 0.45 * math.sin(raise), fz, 0, sweep, raise), 1.06, "s_wing_bfly_f")
		local hs = o.hindSpan or 0.72
		local hx = o.x + span * hs * 0.42 * math.cos(raise)
		wing("Hindwing", span * hs, chord * (o.hindChord or 0.95), at(hx, o.y + span * hs * 0.42 * math.sin(raise) - 0.02, o.z + chord * 0.62, 0, sweep - rad(22), raise), if detail <= 0 then 1.07 else 1.16,
			if o.tails then "s_wing_bfly_tail" else "s_wing_bfly_h")
		-- markings: eyespots / margin bands, thin lenses through the wing (both surfaces curved, never coplanar)
		if detail >= 2 and o.marks then
			local spot = o.marks
			B:mell(chord * 0.42, span * 0.05, chord * 0.42, Geom.mul(fw.cf, at(span * 0.2, 0, chord * 0.12)), { col = spot, mat = "skin", bone = "Wing#", pri = 2.6, role = "detail", name = "Eyespot#", needs = fw.pair })
		end
		if detail >= 3 and o.band then
			B:mell(span * 0.5, span * 0.047, chord * 0.28, Geom.mul(fw.cf, at(span * 0.16, 0, -chord * 0.26)), { col = o.band, mat = "skin", bone = "Wing#", pri = 2.9, role = "detail", name = "Band#", needs = fw.pair })
		end
		return
	end
	if kind == "dfly" then
		-- four long narrow wings held flat, the hind pair a little broader
		if detail <= 0 then
			wing("Wings", span, chord * 2.4, at(o.x + span * 0.48, o.y, o.z + chord * 0.4, 0, 0, rad(4)), 1.06, "s_wing_dfly")
			return
		end
		wing("Forewing", span, chord, at(o.x + span * 0.48, o.y, o.z - chord * 0.3, 0, rad(-6), rad(4)), 1.06, "s_wing_vein")
		wing("Hindwing", span * 0.95, chord * 1.2, at(o.x + span * 0.46, o.y - 0.02, o.z + chord * 0.95, 0, rad(8), rad(3)), 1.14, "s_wing_vein")
		return
	end
	if fold then
		-- wings closed over the abdomen: a long lens on each side, roofed (tent) or flat (fold)
		local roof = rad(if kind == "tent" then 38 else 12)
		wing("Wingcase", chord, o.len, at(o.x * 0.5 + chord * 0.32 * math.cos(roof), o.y - chord * 0.3 * math.sin(roof), o.z + o.len * 0.5, rad(o.pitch or -6), 0, -roof), 1.5, o.piece)
		return
	end
	-- glass: one swept wing per side (a hind wing tucked under at detail 2+)
	local sweep = rad(o.sweep or 32)
	local wx, wz = o.x + span * 0.45 * math.cos(sweep), o.z + span * 0.45 * math.sin(sweep)
	wing("Wing", span * 0.96, chord, at(wx, o.y + span * 0.1, wz, 0, -sweep, rad(o.raise or 14)), 1.1, "s_wing_vein")
	if detail >= 2 and not o.single then
		local s2 = sweep + rad(14)
		wing("Hindwing", span * 0.66, chord * 0.75, at(o.x + span * 0.3 * math.cos(s2), o.y + span * 0.03, o.z + span * 0.3 * math.sin(s2), 0, -s2, rad(8)), 2.1, "s_wing_vein")
	end
end

local function antennae(B: any, ctx: any, b: any, o: any)
	if ctx.detail < (o.minDetail or 0) then
		return
	end
	local H, hc = b.H, b.hc
	local base = { H[1] * (o.x or 0.32), hc[2] + H[2] * (o.y or 0.55), hc[3] - H[3] * (o.z or 0.55) }
	local d = o.dir or { 0.35, 0.55, -0.75 }
	local m = math.sqrt(d[1] * d[1] + d[2] * d[2] + d[3] * d[3])
	Kit.antennae(B, { base = base, dir = { d[1] / m, d[2] / m, d[3] / m }, len = o.len, w = o.w, kind = o.kind, col = o.col, pri = o.pri or 1.55, detail = ctx.detail, clubCol = o.clubCol })
end

local function mandibles(B: any, ctx: any, b: any, len: number, o: any?)
	local oo = o or {}
	local H, hc = b.H, b.hc
	Kit.mandibles(B, { root = { H[1] * (oo.x or 0.28), hc[2] - H[2] * (oo.drop or 0.35), hc[3] - H[3] * 0.72 }, len = len, w = oo.w, spread = oo.spread or 0.1, up = oo.up or 0,
		col = oo.col or "darker", pri = oo.pri or 1.45, piece = oo.piece })
end

-- a horn rising from the head or pronotum. o: from, to, w, segs, col, pri, bone
local function horn(B: any, o: any)
	Kit.seg(B, o.from, o.to, o.w, { col = o.col or "darker", mat = "hard", bone = o.bone or "Head", pri = o.pri or 1.35, role = "horn", name = o.name or "Horn", mesh = o.piece or "s_beetle_horn", trail = true }, o.up or { 0, 0, 1 })
end

-- kinds ------------------------------------------------------------------------------------------------------------

local K: { [string]: (any, any) -> () } = {}

K.Beetle = function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id, hint = Kit.text(ctx)
	local ladybug = has(id, "ladybug ladybird") or string.find(hint, "dome", 1, true) ~= nil
	local stag = has(id, "stag titan") or string.find(hint, "jaws", 1, true) ~= nil
	local rhino = has(id, "rhinoceros hercules atlas") or (string.find(hint, "horn", 1, true) ~= nil and not has(id, "longhorn"))
	local weevil = has(id, "weevil") or string.find(hint, "snout", 1, true) ~= nil
	local longhorn = has(id, "longhorn") or string.find(hint, "long antennae", 1, true) ~= nil
	local flat = has(id, "violin stink") or string.find(hint, "flat", 1, true) ~= nil
	local slim = has(id, "click tiger ground") or string.find(hint, "slim", 1, true) ~= nil
	local metallic = string.find(hint, "metallic", 1, true) ~= nil or string.find(hint, "shimmer", 1, true) ~= nil or has(id, "jewel japanese")
	local big = has(id, "goliath titan hercules atlas") or t.size == "Large" or t.size == "Huge"
	local fourLegs = string.find(hint, "four-legged", 1, true) ~= nil
	local glow = string.find(hint, "glow", 1, true) ~= nil or has(id, "meteor")
	-- proportions
	local Ew, Eh, El = 1.7, 1.15, 2.0
	local Pw, Ph, Pl = 1.4, 0.82, 0.9
	if ladybug or has(id, "tortoise aphid") then
		Ew, Eh, El = 1.95, 1.45, 1.85
		Pw, Ph, Pl = 1.2, 0.7, 0.62
	elseif slim then
		Ew, Eh, El = 1.3, 0.85, 2.1
		Pw, Ph, Pl = 1.1, 0.7, 0.85
	elseif flat then
		Ew, Eh, El = 1.9, 0.7, 2.1
		Pw, Ph, Pl = 1.5, 0.55, 0.8
	elseif has(id, "dung june") then
		Ew, Eh, El = 1.75, 1.3, 1.75
	end
	local legLong = if has(id, "tiger") then 1.35 elseif slim then 1.15 else 1
	local y = (if flat then 0.62 else 0.82) * (if slim then 1.1 else 1)
	local b = tagmata(B, ctx, {
		y = y, T = { Pw, Ph, Pl }, Tp = -4, H = { 0.42, 0.36, 0.38 }, hy = -0.08, hz = 0.55, A = { Ew, Eh, El }, Ap = -3, ay = 0.1, gap = -0.1,
		col = if metallic then "primary" else "primary", mat = if metallic then "metal" else "hard", thCol = if ladybug then "black" else nil,
		thPiece = "s_beetle_pronotum", abPiece = if ladybug then "s_beetle_dome" else "s_beetle_elytra", headPiece = "s_bug_head_jaw",
		headCol = if ladybug then "black" else nil, eye = { d = 0.85, spacing = 0.72, y = 0.12 },
	})
	-- legs: sturdy, splayed, feet well out to the sides
	local reach = 1.25 * legLong
	local L = { hipX = Pw * 0.3, z = { -Pl * 0.22, Pl * 0.3, Pl * 0.62 }, feet = { { Ew * 0.48 + reach * 0.75, -Pl * 0.6 - reach * 0.55 }, { Ew * 0.5 + reach * 0.95, Pl * 0.4 }, { Ew * 0.48 + reach * 0.8, Pl + reach * 0.7 } }, thick = if big then 1.25 else 1.1 }
	if fourLegs then
		L.feet[2] = L.feet[3]
	end
	sixLegs(B, ctx, b, L)
	-- antennae: short clubbed, or long whips (longhorn)
	if longhorn then
		antennae(B, ctx, b, { len = El * 1.8, kind = "thread", dir = { 0.45, 0.5, 0.3 }, w = 0.07, minDetail = 0 })
	elseif string.find(hint, "feathery", 1, true) then
		antennae(B, ctx, b, { len = 1.1, kind = "feather", dir = { 0.4, 0.7, -0.5 } })
	else
		antennae(B, ctx, b, { len = 0.75, kind = "club", dir = { 0.5, 0.35, -0.75 }, w = 0.06, minDetail = 1 })
	end
	local H, hc = b.H, b.hc
	if stag then
		-- antler jaws: long, curved inward, as long as the pronotum is wide
		mandibles(B, ctx, b, Pw * 0.95, { piece = "s_stag_jaw", spread = 0.38, up = 0.18, w = 0.28, x = 0.3, pri = 1.2, col = if has(id, "rainbow") then "secondary" else "darker" })
	elseif detail >= 1 then
		mandibles(B, ctx, b, 0.36, { spread = 0.05, pri = 2.2 })
	end
	if rhino then
		-- head horn curving up and back; hercules: a long thoracic horn arching over it; atlas: two more
		horn(B, { from = { 0, hc[2] + H[2] * 0.2, hc[3] - H[3] * 0.4 }, to = { 0, hc[2] + 1.2, hc[3] - 0.65 }, w = 0.32, pri = 1.2 })
		if has(id, "hercules") or (detail >= 2 and not has(id, "atlas")) then
			horn(B, { bone = "Body", from = { 0, y + Ph * 0.35, -Pl * 0.15 }, to = { 0, y + Ph * 0.55 + 0.25, hc[3] - 0.9 }, w = 0.3, pri = 1.4, name = "ProHorn", piece = "s_beetle_horn_long", up = { 0, -1, 0 } })
		end
		if has(id, "atlas") and detail >= 1 then
			Kit.seg(B, { Pw * 0.35, y + Ph * 0.25, -Pl * 0.2 }, { Pw * 0.55, y + Ph * 0.45, -Pl - 0.6 }, 0.22, { col = "darker", mat = "hard", pri = 1.5, role = "horn", name = "SideHorn#", mesh = "s_beetle_horn", trail = true, mirror = true }, { 0, 1, 0 })
		end
	end
	if weevil then
		-- rostrum: a long snout from the face, jaws at its tip (giraffe weevil: a long neck first)
		local neck = has(id, "giraffe")
		local base = { 0, hc[2] + 0.05, hc[3] - H[3] * 0.6 }
		local tip = if neck then { 0, hc[2] + 1.0, hc[3] - 1.4 } else { 0, hc[2] - 0.45, hc[3] - 0.95 }
		B:limb(base, tip, 0.2, { col = "primary", mat = "hard", bone = "Head", pri = 1.25, role = "snout", name = "Rostrum", mesh = "s_arthro_seg" }, 0.12)
	end
	-- markings
	if ladybug and detail >= 1 then
		-- black spots sunk into the dome: lenses whose inner face lies inside the shell
		local spots = if detail >= 3 then { { 0.45, 0.25, -0.25 }, { 0.62, -0.05, 0.25 }, { 0.32, 0.45, 0.45 }, { 0.2, 0.55, -0.05 } } elseif detail >= 2 then { { 0.45, 0.25, -0.2 }, { 0.6, -0.02, 0.35 } } else { { 0.48, 0.2, 0.05 } }
		for i, sp in spots do
			local rx, ry, rz = Ew / 2, Eh / 2, El / 2
			local u = math.clamp(sp[1] ^ 2 + sp[3] ^ 2, 0, 0.85)
			local x, z = rx * sp[1], rz * sp[3]
			local yy = b.ay + ry * math.sqrt(1 - u)
			local nx, ny, nz = Geom.normalize(x / (rx * rx), (yy - b.ay) / (ry * ry), z / (rz * rz))
			local f = Kit.segFrame({ x, yy, b.az + z }, { x + nx, yy + ny, b.az + z + nz })
			B:mell(0.42 - i * 0.03, 0.2, 0.42 - i * 0.03, f, { col = "black", mat = "hard", bone = b.ab, pri = 1.5 + i * 0.1, role = "detail", name = "Spot" .. i .. "#" })
		end
	elseif has(id, "tortoise") and detail >= 1 then
		-- clear gold flange round the dome
		B:ell(Ew * 1.42, Eh * 0.22, El * 1.15, at(0, b.ay - Eh * 0.12, b.az - 0.15), { col = "secondary", mat = "glass", tr = 0.35, bone = b.ab, pri = 1.6, role = "shell", name = "Flange" })
	elseif detail >= 2 and not metallic and has(id, "carrion goliath blister bombardier") then
		-- bold bands across the elytra in the secondary colour
		for i = 1, (if detail >= 3 then 2 else 1) do
			local z = b.az - El * 0.18 + (i - 1) * El * 0.34
			local k = math.sqrt(math.max(0.1, 1 - ((z - b.az) / (El / 2)) ^ 2)) * 1.04
			B:ell(Ew * k, Eh * k, El * 0.13, at(0, b.ay, z, rad(-3), 0, 0), { col = "secondary", mat = "hard", bone = b.ab, pri = 1.55 + i * 0.05, role = "detail", name = "Band" .. i })
		end
	end
	if has(id, "dung") and detail >= 1 then
		B:ball(1.5, at(0, 0.75, -2.3), { col = "darkStone", mat = "stone", pri = 1.5, role = "prop", name = "DungBall" })
	end
	if has(id, "bombardier") and detail >= 2 then
		B:limb({ 0, b.ay - 0.1, b.az + El * 0.42 }, { 0, b.ay + 0.25, b.az + El * 0.42 + 0.55 }, 0.3, { col = "secondary", mat = "hard", bone = b.ab, pri = 2.0, role = "tail", name = "Nozzle", trail = true }, 0.1)
	end
	if glow and detail >= 1 then
		B:ell(Ew * 0.6, Eh * 0.32, El * 0.42, at(0, b.ay + Eh * 0.36, b.az + El * 0.05, rad(-4), 0, 0), { col = "glow", mat = "neon", glow = true, bone = b.ab, pri = 1.9, role = "detail", name = "Glow" })
	end
	if (t.wings or t.flies) and detail >= 2 and not ladybug then
		-- flying beetles lift the hind wings from under the elytra
		wings(B, ctx, { kind = "glass", x = Pw * 0.3, y = y + Ph * 0.3, z = Pl * 0.4, span = El * 1.0, chord = 0.55, sweep = 40, raise = 20, single = true })
	end
	B:socket("core", at(0, y, 0.4), "Body")
	B:setRig("gait", "skitter")
end

K.Ant = function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id, hint = Kit.text(ctx)
	local xeno = has(id, "xeno alien")
	local queen = has(id, "queen") and not xeno
	local lion = has(id, "antlion lion")
	local y = if lion then 0.6 else 0.95
	local b = tagmata(B, ctx, {
		y = y, T = { 0.62, 0.62, 1.15 }, Tp = -10, H = if xeno then { 0.42, 0.42, 0.85 } else { 0.55, 0.5, 0.5 }, hy = 0.12, hz = 0.75, Hp = if xeno then -8 else 0,
		A = if queen then { 1.35, 1.15, 2.0 } elseif lion then { 1.4, 0.9, 1.6 } else { 1.15, 1.0, 1.4 }, Ap = if lion then 0 else -14, ay = 0.18, gap = 0.4, node = 0.4,
		abPiece = "s_ant_gaster", thPiece = "s_ant_thorax", headPiece = if xeno then "s_xeno_head" else "s_bug_head_jaw",
		eye = { d = if xeno then 0.0001 else 0.55, spacing = 0.82, y = 0.12 }, eyeKind = if xeno then "glow" else nil,
	})
	local reach = if lion then 1.2 else 1.55
	sixLegs(B, ctx, b, { hipX = 0.18, hipY = 0.18, z = { -0.38, 0.0, 0.32 }, feet = { { 0.7 + reach * 0.6, -0.4 - reach * 0.7 }, { 0.75 + reach * 0.85, 0.1 }, { 0.7 + reach * 0.7, 0.4 + reach * 0.8 } }, thick = 0.95 })
	if not xeno then
		antennae(B, ctx, b, { len = 1.35, kind = "elbow", dir = { 0.45, 0.55, -0.7 }, w = 0.07, minDetail = 1 })
		mandibles(B, ctx, b, if lion then 0.85 else (if has(id, "bullet") then 0.5 else 0.42), { spread = 0.22, pri = 1.4, piece = if lion then "s_stag_jaw" else nil, w = if lion then 0.2 else nil })
	else
		-- xeno: a long smooth crest, inner jaw, a whip tail ending in a blade
		Kit.mandibles(B, { root = { 0.12, b.hc[2] - 0.3, b.hc[3] - 0.55 }, len = 0.4, spread = 0.0, col = "tooth", pri = 2.4, piece = "s_bug_mandible" })
		local tailBones = {}
		local p0 = { 0, b.ay + 0.2, b.az + b.A[3] * 0.4 }
		local n = if detail >= 2 then 3 else 1
		local parent = b.ab
		for i = 1, n do
			local p1 = { 0, p0[2] + 0.35 - i * 0.12, p0[3] + 2.4 / n }
			local bn = B:bone("Tail" .. i, parent, p0[1], p0[2], p0[3])
			table.insert(tailBones, bn)
			B:limb(p0, p1, 0.32 - i * 0.06, { col = "primary", mat = "hard", bone = bn, pri = 1.5 + i * 0.1, role = "tail", name = "Tail" .. i, mesh = "s_arthro_seg" }, 0.15)
			p0 = p1
			parent = bn
		end
		Kit.seg(B, p0, { 0, p0[2] + 0.5, p0[3] + 0.6 }, 0.26, { col = "secondary", mat = "hard", bone = parent, pri = 1.7, role = "tail", name = "TailBlade", mesh = "s_scorpion_sting", trail = true }, { 0, 0, -1 })
		for _, bn in tailBones do
			B:addRig("tail", bn)
		end
		if detail >= 2 then
			B:mlimb({ 0.3, y + 0.25, 0.2 }, { 0.75, y + 1.15, 0.9 }, 0.16, { col = "primary", mat = "hard", pri = 2.3, role = "spike", name = "Dorsal#", mesh = "s_horn_tip", trail = true }, 0.1)
		end
	end
	if queen and detail >= 1 then
		wings(B, ctx, { kind = "glass", x = 0.25, y = y + 0.32, z = 0.15, span = 2.2, chord = 0.62, sweep = 34, raise = 10 })
	end
	if has(id, "bullet") and detail >= 2 then
		B:limb({ 0, b.ay - 0.2, b.az + b.A[3] * 0.42 }, { 0, b.ay - 0.4, b.az + b.A[3] * 0.62 }, 0.14, { col = "darker", mat = "hard", bone = b.ab, pri = 2.2, role = "tail", name = "Sting", trail = true }, 0.1)
	end
	local _ = t
	local _h = hint
	B:socket("core", at(0, y, 0.3), "Body")
	B:setRig("gait", "skitter")
end

K.Fly = function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id, hint = Kit.text(ctx)
	local bee = (has(id, "bee bees bumblebee") and not has(id, "beetle")) or has(id, "hornet wasp") or string.find(hint, "bee-like", 1, true) ~= nil or string.find(hint, "striped", 1, true) ~= nil
	local wasp = has(id, "wasp hornet")
	local mosquito = has(id, "mosquito gnat midge crane") or string.find(hint, "spindly", 1, true) ~= nil
	local cicada = has(id, "cicada")
	local fuzzy = t.fluffy or string.find(hint, "fluffy", 1, true) ~= nil or string.find(hint, "bristly", 1, true) ~= nil or (bee and not wasp)
	local glow = has(id, "firefly adze") or string.find(hint, "glow", 1, true) ~= nil
	local aphid = has(id, "aphid")
	local lace = has(id, "lacewing stonefly")
	local y = if mosquito then 1.45 else 1.15
	local T = if mosquito then { 0.62, 0.62, 0.72 } elseif cicada then { 1.15, 1.0, 1.1 } else { 1.0, 0.95, 1.05 }
	local A = if mosquito then { 0.45, 0.42, 1.5 } elseif wasp then { 0.85, 0.8, 1.3 } elseif cicada then { 1.05, 0.95, 1.5 } elseif aphid then { 1.3, 1.2, 1.5 } elseif lace then { 0.5, 0.5, 1.6 } else { 0.95, 0.82, 1.25 }
	local H = if cicada then { 0.62, 0.42, 0.4 } elseif mosquito then { 0.34, 0.32, 0.3 } else { 0.52, 0.46, 0.4 }
	local b = tagmata(B, ctx, {
		y = y, T = T, H = H, hy = -0.04, hz = 0.6, A = A, Ap = if mosquito then -16 else -12, ay = -0.05, gap = if wasp then 0.32 else 0, node = if wasp then 0.3 else nil,
		mat = if fuzzy then "fur" else "hard", thPiece = if fuzzy then "s_fly_thorax_fuzz" else "s_fly_thorax", abPiece = if bee then "s_bee_abdomen" else "s_bug_abdomen", headPiece = "s_fly_head",
		eye = { d = if cicada then 0.7 else 1.12, spacing = if cicada then 0.92 else 0.6, y = 0.1 }, eyeKind = if t.cute then "cute" else "bug",
	})
	-- bee bands: discs following the abdomen's cross-section x1.05, in black
	if bee then
		local n = if detail >= 2 then 3 elseif detail == 1 then 2 else 1
		local rz = A[3] / 2
		for i = 1, n do
			local z = b.az - rz * 0.42 + (i - 1) * rz * (if n == 1 then 0 else 0.9 / (n - 1)) + (if n == 1 then rz * 0.4 else 0)
			local k = math.sqrt(math.max(0.1, 1 - ((z - b.az) / rz) ^ 2)) * 1.05
			B:ell(A[1] * k, A[2] * k, A[3] * 0.15, at(0, b.ay + (z - b.az) * math.tan(rad(12)), z, rad(-12), 0, 0), { col = "black", mat = if fuzzy then "fur" else "hard", bone = b.ab, pri = 1.12 + i * 0.03, role = "detail", name = "Stripe" .. i })
		end
	end
	if glow then
		B:ell(A[1] * 0.8, A[2] * 0.75, A[3] * 0.42, at(0, b.ay - 0.02, b.az + A[3] * 0.3, rad(-12), 0, 0), { col = "glow", mat = "neon", glow = true, bone = b.ab, pri = 1.15, role = "detail", name = "Lantern" })
	end
	-- wings
	if cicada then
		wings(B, ctx, { kind = "tent", x = 0.2, y = y + T[2] * 0.42, z = -0.1, span = 1, chord = 0.95, len = A[3] * 1.5, pitch = -8 })
	elseif lace then
		wings(B, ctx, { kind = "glass", x = 0.2, y = y + T[2] * 0.4, z = 0.1, span = 2.4, chord = 0.75, sweep = 55, raise = 26 })
	elseif not aphid or detail >= 2 then
		wings(B, ctx, { kind = "glass", x = 0.22, y = y + T[2] * 0.4, z = 0.05, span = if mosquito then 1.8 else 2.0, chord = if mosquito then 0.42 else 0.72, sweep = if mosquito then 48 else 30, raise = 14 })
	end
	-- legs: hanging from the thorax; mosquitoes and crane flies stand on stilts
	local reach = if mosquito then 2.6 else 1.1
	if detail >= 1 or not mosquito then
		sixLegs(B, ctx, b, { hipX = T[1] * 0.22, hipY = T[2] * 0.3, z = { -0.25, 0.05, 0.3 }, feet = { { 0.55 + reach * 0.5, -0.5 - reach * 0.6 }, { 0.6 + reach * 0.7, 0.05 }, { 0.55 + reach * 0.55, 0.5 + reach * 0.85 } },
			footY = 0.04, thick = if mosquito then 0.55 else 0.9, piece = if mosquito then "s_arthro_leg_long" else nil, comb = if mosquito then "s_bug_legs3" else nil })
	end
	-- mouthparts
	if mosquito or has(id, "bee fly assassin") or string.find(hint, "long nose", 1, true) or string.find(hint, "needle", 1, true) then
		local hc = b.hc
		B:limb({ 0, hc[2] - H[2] * 0.4, hc[3] - H[3] * 0.6 }, { 0, hc[2] - H[2] * 1.4, hc[3] - H[3] * 2.6 }, 0.09, { col = "darker", mat = "hard", bone = "Head", pri = 1.35, role = "snout", name = "Proboscis", mesh = "s_tail_tip", trail = true }, 0.05)
	end
	if bee or has(id, "scorpionfly") then
		local tip = { 0, b.ay - 0.15, b.az + A[3] * 0.48 }
		if has(id, "scorpionfly") then
			Kit.seg(B, tip, { 0, b.ay + 0.9, b.az + A[3] * 0.48 + 0.25 }, 0.26, { col = "secondary", mat = "hard", bone = b.ab, pri = 1.4, role = "tail", name = "Sting", mesh = "s_scorpion_sting", trail = true }, { 0, 0, -1 })
		elseif detail >= 1 then
			B:limb(tip, { 0, b.ay - 0.4, b.az + A[3] * 0.72 }, 0.16, { col = "black", mat = "hard", bone = b.ab, pri = 1.5, role = "tail", name = "Sting", mesh = "s_horn_tip", trail = true }, 0.08)
		end
	end
	if has(id, "dobsonfly snakefly") then
		local hc = b.hc
		if has(id, "dobsonfly") then
			mandibles(B, ctx, b, 1.0, { piece = "s_stag_jaw", spread = 0.3, w = 0.2, pri = 1.3 })
		else
			B:limb({ 0, y + 0.1, -T[3] * 0.4 }, { 0, hc[2] + 0.2, hc[3] + 0.2 }, 0.3, { col = "primary", mat = "hard", bone = "Head", pri = 1.4, role = "body", name = "Neck", mesh = "s_arthro_seg" }, 0.2)
		end
	end
	antennae(B, ctx, b, { len = if mosquito then 0.7 else 0.45, kind = if mosquito then "feather" else "short", dir = { 0.3, 0.7, -0.6 }, w = 0.06, minDetail = 2 })
	B:socket("core", at(0, y, 0.3), "Body")
	B:setRig("gait", "buzz")
end

K.Butterfly = function(B: any, ctx: any, moth: boolean?)
	local t, detail = ctx.traits, ctx.detail
	local id, hint = Kit.text(ctx)
	local fuzzy = moth or t.fluffy
	local big = has(id, "atlas birdwing cecropia giant luna moon") or t.size ~= "Tiny"
	local y = 1.55
	-- detail 0: thorax + abdomen are one fuzzy body (four wings and two eyes fill the budget)
	local T = if moth then { 0.62, 0.62, 0.7 } else { 0.42, 0.44, 0.6 }
	local A = if moth then { 0.58, 0.55, 1.35 } else { 0.32, 0.32, 1.35 }
	local b = tagmata(B, ctx, {
		y = y, T = T, H = if moth then { 0.36, 0.34, 0.32 } else { 0.27, 0.26, 0.25 }, hy = -0.02, hz = 0.6, A = A, Ap = -8, gap = -0.04,
		col = "dark", abCol = if moth then "primary" else "dark", thCol = if moth then "primary" else "dark", headCol = if moth then "primary" else "dark",
		mat = if fuzzy then "fur" else "hard", thPiece = "s_fly_thorax_fuzz", abPiece = "s_bfly_body", headPiece = false,
		eye = { d = 0.85, spacing = 0.72, y = 0.15 }, eyeKind = if t.cute or moth then "cute" else "bug",
	})
	local span = if big then 2.7 else 2.35
	local spots = string.find(hint, "eye", 1, true) ~= nil or string.find(hint, "spot", 1, true) ~= nil or has(id, "owl io peacock")
	local clear = has(id, "glasswing") or string.find(hint, "clear", 1, true) ~= nil or string.find(hint, "see-through", 1, true) ~= nil
	wings(B, ctx, {
		kind = if moth then "moth" else "bfly", x = T[1] * 0.3, y = y + T[2] * 0.28, z = -0.05, span = span, chord = if moth then 1.45 else 1.4, clear = clear,
		col = if clear then "wingGlass" else "primary", marks = if spots then "secondary" else nil, band = if clear then nil else (if moth then "secondary" else "dark"),
		tails = has(id, "luna swallowtail moon") or string.find(hint, "tail", 1, true) ~= nil,
		hindSpan = if moth then 0.66 else 0.74,
	})
	antennae(B, ctx, b, if moth then { len = 0.75, kind = "feather", dir = { 0.5, 0.75, -0.45 }, minDetail = 1, col = "secondary" } else { len = 1.25, kind = "club", dir = { 0.35, 0.75, -0.55 }, w = 0.045, minDetail = 1 })
	if detail >= 2 then
		sixLegs(B, ctx, b, { hipX = 0.12, hipY = 0.18, z = { -0.18, 0.0, 0.18 }, feet = { { 0.5, -0.75, y - 0.9 }, { 0.6, -0.05, y - 1.0 }, { 0.5, 0.6, y - 0.95 } }, thick = 0.6, segs = 1 })
	end
	B:socket("core", at(0, y, 0.3), "Body")
	B:setRig("gait", "flutter")
end

K.Moth = function(B: any, ctx: any)
	K.Butterfly(B, ctx, true)
end

K.Dragonfly = function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id = Kit.text(ctx)
	local mech = t.robot or t.mechanical
	local damsel = has(id, "damselfly mayfly")
	local y = 1.4
	local b = tagmata(B, ctx, {
		y = y, T = { 0.62, 0.7, 0.8 }, Tp = -10, H = if damsel then { 0.42, 0.28, 0.26 } else { 0.48, 0.42, 0.4 }, hy = 0.02, hz = 0.55, A = { 0.26, 0.26, 1.2 }, Ap = 2, gap = -0.02,
		mat = if mech then "metal" else "hard", thPiece = "s_fly_thorax", abPiece = "s_arthro_seg", headPiece = "s_fly_head",
		eye = { d = if damsel then 0.75 else 1.25, spacing = if damsel then 0.95 else 0.5, y = 0.3 }, eyeKind = if mech then "glow" elseif t.cute then "cute" else "bug",
	})
	-- the long tail: abdomen + more segments behind it, thinning (detail 1+)
	local segs = if detail >= 3 then 3 elseif detail >= 1 then 2 else 0
	local p0 = { 0, b.ay - 0.01, b.az + 0.55 }
	local parent = b.ab
	for i = 1, segs do
		local p1 = { 0, p0[2] - 0.03 * i, p0[3] + 1.25 }
		local bn = B:bone("Tail" .. i, parent, p0[1], p0[2], p0[3])
		B:addRig("tail", bn)
		B:limb(p0, p1, 0.24 - i * 0.025, { col = if i % 2 == 0 then "secondary" else "primary", mat = if mech then "metal" else "hard", bone = bn, pri = 1.2 + i * 0.1, role = "tail", name = "Tail" .. i, mesh = "s_arthro_seg", trail = i == segs }, 0.1)
		p0 = p1
		parent = bn
	end
	if has(id, "mayfly") and detail >= 2 then
		B:mlimb(p0, { p0[1] + 0.25, p0[2] + 0.3, p0[3] + 1.4 }, 0.04, { col = "darker", mat = "hard", bone = parent, pri = 2.6, role = "tail", name = "Cercus#", trail = true }, 0.05)
	end
	wings(B, ctx, { kind = "dfly", x = 0.2, y = y + 0.32, z = -0.05, span = if damsel then 2.3 else 2.7, chord = if damsel then 0.36 else 0.46, col = if mech then "secondary" else nil })
	if detail >= 2 then
		sixLegs(B, ctx, b, { hipX = 0.14, hipY = 0.3, z = { -0.25, -0.05, 0.15 }, feet = { { 0.55, -0.85, y - 1.15 }, { 0.65, -0.35, y - 1.2 }, { 0.6, 0.25, y - 1.15 } }, thick = 0.7, segs = 1 })
	end
	antennae(B, ctx, b, { len = 0.3, kind = "short", dir = { 0.3, 0.8, -0.5 }, minDetail = 3 })
	if has(id, "knight") and detail >= 1 then
		-- tiny lance rider: a knight's helm and lance on the thorax
		B:ell(0.45, 0.6, 0.45, at(0, y + 0.75, 0.0), { col = "steel", mat = "metal", pri = 1.5, role = "rider", name = "Rider" })
		B:limb({ 0.3, y + 0.85, 0.2 }, { 0.45, y + 0.95, -2.2 }, 0.1, { col = "wood", mat = "wood", pri = 1.6, role = "weapon", name = "Lance", trail = true }, 0.02)
	end
	if mech and detail >= 2 then
		B:mball(0.18, at(0.22, b.hc[2] + 0.05, b.hc[3] - 0.42), { col = "red", mat = "neon", glow = true, bone = "Head", pri = 2.0, role = "detail", name = "Laser#" })
	end
	B:socket("core", at(0, y, 0.3), "Body")
	B:setRig("gait", "hover")
end

K.Mantis = function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id = Kit.text(ctx)
	local orchid = has(id, "orchid")
	local warrior = has(id, "warrior")
	local y = 1.05
	B.boneIndex.Body.pos = { 0, y, 0 }
	-- abdomen: long, behind; mesothorax at the origin; prothorax rising forward (the "neck")
	local ab = B:bone("Abdomen", "Body", 0, y, 0.3)
	B:addRig("tail", ab)
	B:ell(0.62, 0.6, 0.8, at(0, y, 0, rad(-8), 0, 0), { col = "primary", mat = "hard", pri = 1.02, role = "body", name = "Thorax", mesh = "s_bug_thorax" })
	B:ell(if orchid then 0.95 else 0.72, 0.62, 2.0, at(0, y + 0.12, 1.25, rad(-8), 0, 0), { col = "primary", mat = "hard", bone = ab, pri = 1.0, role = "body", name = "Abdomen", mesh = "s_mantis_abdomen" })
	local neckTop = { 0, y + 1.35, -0.75 }
	B:bone("Pro", "Body", 0, y + 0.1, -0.25)
	B:limb({ 0, y + 0.05, -0.2 }, neckTop, 0.36, { col = "primary", mat = "hard", bone = "Pro", pri = 1.03, role = "body", name = "Prothorax", mesh = "s_arthro_seg" }, 0.18)
	-- head: wide triangle, eyes on the top corners
	B:bone("Head", "Pro", neckTop[1], neckTop[2], neckTop[3])
	B:setRig("head", "Head")
	local hc = { 0, neckTop[2] + 0.12, neckTop[3] - 0.22 }
	Kit.head(B, { c = hc, r = { 0.48, 0.34, 0.26 }, col = "primary", piece = "s_mantis_head", mood = Kit.mood(ctx), detail = detail, kind = Kit.eyeKind(ctx, t), eyeD = 0.36, spacing = 0.36, eyeY = 0.12, noMouth = true, noBrows = true })
	-- raptorial forelegs folded under the head (one sculpt per arm, the primitive is the femur)
	local sh = { 0.2, y + 1.0, -0.6 }
	local rb = B:mirrorBone("Arm#", "Pro", sh[1], sh[2], sh[3])
	local _ = rb
	B:addRig("arms", { arm = "ArmR", side = 1 })
	B:addRig("arms", { arm = "ArmL", side = -1 })
	local elbow = { 0.36, y + 0.45, -1.25 }
	Kit.seg(B, sh, elbow, 0.24, { col = if warrior then "secondary" else "primary", mat = "hard", bone = "Arm#", pri = 1.15, role = "limb", name = "Raptor#", mesh = "s_mantis_arm", meshL = "s_mantis_arm_l", trail = true, mirror = true, over = 0.12 }, { 0, 1, 0 })
	if detail >= 2 then
		B:mlimb(elbow, { 0.32, y + 1.15, -1.45 }, 0.15, { col = if warrior then "steel" else "primary", mat = if warrior then "metal" else "hard", bone = "Arm#", pri = 1.5, role = "claw", name = "Blade#", mesh = "s_horn_tip", trail = true }, 0.05)
	end
	-- four walking legs
	local legs = {
		{ { 0.2, y - 0.12, 0.05 }, { 1.45, 0.04, -0.6 } },
		{ { 0.22, y - 0.12, 0.3 }, { 1.55, 0.04, 1.6 } },
	}
	if detail <= 1 then
		Kit.comb(B, { hip = legs[1][1], foot = { 1.55, 0.04, 0.5 }, piece = "s_bug_legs2", pri = 1.3, thick = 0.8 })
	else
		Kit.legSet(B, { tagBase = "L", segs = if detail >= 3 then 2 else 1, rise = 0.32, thick = 0.75, col = "primary", pri = 1.3 }, legs)
	end
	-- wings folded on the abdomen (leaf green, or petal pink for the orchid mantis)
	if detail >= 1 then
		B:mell(0.42, 0.08, 1.85, at(0.2, y + 0.45, 1.2, rad(-9), 0, rad(-10)), { col = if orchid then "secondary" else "light", mat = "skin", pri = 1.6, role = "wing", name = "Tegmen#", mesh = "s_leaf_wing", meshL = "s_leaf_wing_l" })
	end
	if orchid and detail >= 2 then
		-- petal lobes on the walking-leg femurs
		B:mell(0.55, 0.12, 0.42, at(0.95, 0.75, -0.3, 0, 0, rad(-30)), { col = "secondary", mat = "skin", pri = 2.4, role = "petal", name = "Petal#", mesh = "s_petal" })
	end
	antennae(B, ctx, { H = { 0.48, 0.34, 0.26 }, hc = hc }, { len = 1.0, kind = "thread", dir = { 0.3, 0.7, -0.4 }, x = 0.2, y = 0.6, z = 0.4, w = 0.035, minDetail = 2 })
	B:socket("core", at(0, y, 0.3), "Body")
	B:setRig("gait", "stalk")
end

K.Hopper = function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id, hint = Kit.text(ctx)
	local cricket = has(id, "cricket weta")
	local katydid = has(id, "katydid")
	local small = has(id, "leafhopper treehopper spittlebug flea")
	local cave = has(id, "cave")
	local jeru = has(id, "jerusalem")
	local y = if cave then 1.1 else 0.85
	local b = tagmata(B, ctx, {
		y = y, T = if katydid then { 0.75, 0.9, 0.85 } else { 0.8, 0.85, 0.95 }, Tp = -6,
		H = if jeru then { 0.68, 0.62, 0.55 } else { 0.42, 0.52, 0.42 }, hy = 0.08, hz = 0.6, Hp = 8,
		A = if small then { 0.9, 0.9, 1.3 } elseif cricket then { 0.85, 0.75, 1.6 } else { 0.62, 0.66, 1.9 }, Ap = if cave then -12 else -4, ay = if cave then 0.2 else 0.0, gap = -0.05,
		thPiece = "s_hopper_pronotum", abPiece = "s_bug_abdomen", headPiece = "s_hopper_head", eye = { d = 0.62, spacing = 0.78, y = 0.25 },
		abCol = if jeru then "secondary" else nil,
	})
	-- hind legs: the jumping legs. Femur from the hip up and back to a knee level with the back, tibia down and
	-- forward to the foot (one sculpt at detail 0-2; femur + tibia at 3)
	local hip = { 0.32, y - 0.1, 0.35 }
	local knee = { 0.55, y + (if cave then 0.9 else 0.55), 1.55 }
	local foot = { 0.65, 0.04, 1.35 }
	local rb = B:mirrorBone("HipH#", "Body", hip[1], hip[2], hip[3])
	local _ = rb
	B:addRig("legs", { hip = "HipHR", side = 1, phase = 0.5, len = hip[2], jump = true })
	B:addRig("legs", { hip = "HipHL", side = -1, phase = 0, len = hip[2], jump = true })
	if detail >= 3 then
		Kit.seg(B, hip, knee, 0.42, { col = "primary", mat = "hard", bone = "HipH#", pri = 1.1, role = "limb", name = "JumpFemur#", mesh = "s_hopper_femur", mirror = true, over = 0.1 }, { 0, -1, 0 })
		B:mlimb(knee, foot, 0.14, { col = "dark", mat = "hard", bone = "HipH#", pri = 1.15, role = "limb", name = "JumpTibia#", mesh = "s_arthro_tibia" }, 0.05)
	else
		-- the primitive is the thigh (the silhouette); the sculpt folds the shin back under it
		Kit.seg(B, hip, knee, 0.42, { col = "primary", mat = "hard", bone = "HipH#", pri = 1.1, role = "limb", name = "JumpLeg#", mesh = "s_hopper_leg", mirror = true, over = 0.1 }, { 0, -1, 0 })
	end
	-- front and middle legs: small
	if detail >= 1 then
		Kit.legSet(B, { tagBase = "L", thick = 0.85, segs = if detail >= 3 then 2 else 1, rise = 0.3, col = "dark", pri = 1.35 }, {
			{ { 0.25, y - 0.25, -0.35 }, { 0.85, 0.04, -1.15 } },
			{ { 0.28, y - 0.25, 0.0 }, { 1.0, 0.04, -0.1 } },
		})
	end
	-- antennae: long whips (crickets, katydids: longer than the body)
	antennae(B, ctx, b, { len = if cricket or katydid or cave then 3.0 else 1.2, kind = "thread", dir = if cricket or katydid or cave then { 0.3, 0.45, 0.35 } else { 0.35, 0.75, -0.45 }, w = 0.05, minDetail = 0 })
	-- wings folded along the back (katydid: a big leaf)
	if detail >= 1 and not small and not jeru and not cave then
		wings(B, ctx, { kind = "fold", x = 0.2, y = y + 0.42, z = 0.1, span = 1, chord = if katydid then 0.7 else 0.45, len = if katydid then 2.2 else 1.8, col = if katydid then "primary" else "secondary", piece = "s_leaf_wing", pitch = -6 })
	end
	if has(id, "treehopper") and detail >= 1 then
		B:limb({ 0, y + 0.3, -0.2 }, { 0, y + 1.2, 0.5 }, 0.3, { col = "secondary", mat = "hard", pri = 1.4, role = "horn", name = "Helmet", mesh = "s_horn_tip" }, 0.1)
	end
	if has(id, "mole") and detail >= 1 then
		B:mell(0.45, 0.32, 0.4, at(0.55, 0.3, -1.0, 0, 0, rad(-20)), { col = "secondary", mat = "hard", pri = 1.5, role = "claw", name = "Digger#", mesh = "s_crab_claw", meshL = "s_crab_claw_l" })
	end
	if has(id, "spittlebug") and detail >= 1 then
		B:ell(2.2, 1.4, 2.4, at(0, 0.55, 0.6), { col = "white", mat = "glass", tr = 0.45, pri = 2.2, role = "shell", name = "Foam" })
	end
	local _ = t
	local _h = hint
	B:socket("core", at(0, y, 0.3), "Body")
	B:setRig("gait", "hop")
end

K.Roach = function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id, hint = Kit.text(ctx)
	local strider = has(id, "strider")
	local earwig = has(id, "earwig")
	local silver = has(id, "silverfish")
	local tiny = has(id, "louse bed")
	local water = has(id, "water backswimmer giant")
	local assassin = has(id, "assassin")
	local shield = has(id, "stink")
	local y = if strider then 1.0 elseif tiny then 0.4 else 0.5
	local A = if silver then { 1.2, 0.5, 2.4 } elseif earwig then { 0.85, 0.5, 2.2 } elseif tiny then { 1.6, 0.55, 1.8 } elseif strider then { 0.35, 0.3, 1.8 } elseif assassin then { 0.95, 0.55, 2.1 } else { 1.55, 0.6, 2.5 }
	local b = tagmata(B, ctx, {
		y = y, T = if strider then { 0.4, 0.35, 0.7 } else { if silver then 1.15 else 1.4, 0.45, 0.85 }, Tp = -2, H = { 0.36, 0.28, 0.32 }, hy = -0.05, hz = 0.55, A = A, Ap = 0, gap = -0.08,
		thPiece = "s_roach_pronotum", abPiece = if silver then "s_silverfish_body" else "s_roach_body", headPiece = "s_bug_head_jaw",
		mat = if silver then "metal" else "hard", eye = { d = 0.7, spacing = 0.78, y = 0.15 },
	})
	-- legs: sprawled wide (water striders: enormous middle and hind oars)
	local reach = if strider then 3.4 elseif water then 1.5 else 1.35
	local L = { hipX = 0.3, hipY = 0.08, z = { -0.3, 0.05, 0.35 }, feet = { { 1.0 + reach * 0.45, -0.7 - reach * 0.55 }, { 1.0 + reach * 0.85, 0.25 }, { 1.0 + reach * 0.7, 0.8 + reach * 0.85 } }, thick = if strider then 0.5 else 1.0, piece = if strider then "s_arthro_leg_long" else "s_arthro_leg_spiny" }
	if water and not strider then
		L.thicks = { 1.3, 1.2, 1.4 }
	end
	sixLegs(B, ctx, b, L)
	if not tiny then
		antennae(B, ctx, b, { len = if silver or has(id, "roach") then 2.8 else 1.4, kind = "thread", dir = { 0.45, 0.35, -0.75 }, w = 0.045, minDetail = 0 })
	end
	if earwig and detail >= 0 then
		-- forceps on the tail end
		local tip = { 0.12, b.ay + 0.05, b.az + A[3] * 0.45 }
		B:mlimb(tip, { 0.05, b.ay + 0.15, b.az + A[3] * 0.45 + 0.9 }, 0.16, { col = "secondary", mat = "hard", bone = b.ab, pri = 1.2, role = "claw", name = "Forceps#", mesh = "s_bug_mandible", meshL = "s_bug_mandible_l", trail = true }, 0.05)
	end
	if silver and detail >= 1 then
		for i, dx in { 0.0, 0.35 } do
			if i == 1 then
				B:limb({ 0, b.ay, b.az + A[3] * 0.45 }, { 0, b.ay + 0.1, b.az + A[3] * 0.45 + 1.1 }, 0.05, { col = "secondary", mat = "hard", bone = b.ab, pri = 2.0, role = "tail", name = "Filament", trail = true }, 0.05)
			elseif detail >= 2 then
				B:mlimb({ 0.1, b.ay, b.az + A[3] * 0.43 }, { dx + 0.3, b.ay + 0.1, b.az + A[3] * 0.43 + 0.95 }, 0.045, { col = "secondary", mat = "hard", bone = b.ab, pri = 2.3, role = "tail", name = "Cercus#", trail = true }, 0.05)
			end
		end
	end
	if assassin and detail >= 1 then
		local hc = b.hc
		B:limb({ 0, hc[2] - 0.1, hc[3] - 0.2 }, { 0, hc[2] - 0.35, hc[3] - 0.9 }, 0.1, { col = "darker", mat = "hard", bone = "Head", pri = 1.4, role = "snout", name = "Beak", mesh = "s_horn_tip", trail = true }, 0.05)
	end
	if water and not strider and detail >= 1 then
		Kit.mandibles(B, { root = { 0.35, y - 0.1, -0.7 }, len = 0.75, spread = 0.2, w = 0.28, piece = "s_crab_claw", col = "primary", pri = 1.4 })
	end
	if shield and detail >= 2 then
		B:ell(0.7, 0.18, 0.7, at(0, b.ay + A[2] * 0.42, b.az - A[3] * 0.25), { col = "secondary", mat = "hard", bone = b.ab, pri = 2.2, role = "detail", name = "Scutellum" })
	end
	local _ = t
	local _h = hint
	B:socket("core", at(0, y, 0.4), "Body")
	B:setRig("gait", if strider then "skate" else "skitter")
end

K.Stick = function(B: any, ctx: any)
	local detail = ctx.detail
	local id = Kit.text(ctx)
	local leaf = has(id, "leaf")
	local y = 0.85
	local b = tagmata(B, ctx, {
		y = y, T = if leaf then { 0.7, 0.32, 1.1 } else { 0.24, 0.24, 1.8 }, H = { 0.2, 0.2, 0.26 }, hy = 0.02, hz = 0.7,
		A = if leaf then { 1.9, 0.18, 2.6 } else { 0.22, 0.22, 2.8 }, Ap = 2, gap = -0.05, col = "primary", mat = if leaf then "skin" else "wood",
		thPiece = if leaf then "s_leaf_wing" else "s_stick_seg", abPiece = if leaf then "s_leaf_body" else "s_stick_seg", headPiece = false, eye = { d = 0.7, spacing = 0.8 },
	})
	sixLegs(B, ctx, b, { hipX = 0.1, hipY = 0.05, z = { -0.75, -0.1, 0.55 }, feet = { { 1.2, -2.0 }, { 1.6, -0.1 }, { 1.4, 1.6 } }, thick = 0.55, piece = "s_arthro_leg_long", comb = "s_bug_legs3" })
	antennae(B, ctx, b, { len = 1.4, kind = "thread", dir = { 0.15, 0.25, -0.95 }, w = 0.035, minDetail = 1 })
	local _ = detail
	B:socket("core", at(0, y, 0.4), "Body")
	B:setRig("gait", "sway")
end

K.Crawler = function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id, hint = Kit.text(ctx)
	local larva = has(id, "larva grub caterpillar maggot")
	local carrion = has(id, "carrion")
	local glowy = string.find(hint, "glow", 1, true) ~= nil
	local n = if detail >= 3 then 7 elseif detail == 2 then 5 elseif detail == 1 then 4 else 3
	if larva then
		n = math.min(n, if detail >= 2 then 5 else 3)
	end
	local segL = if larva then 0.8 else 0.75
	local w = if larva then 1.0 else 0.95
	local y = if larva then 0.5 else 0.55
	B.boneIndex.Body.pos = { 0, y, 0 }
	-- head segment at the front, a chain of body segments behind, each its own bone in a spine (lateral wave)
	B:bone("Head", "Body", 0, y, -segL * 0.5)
	B:setRig("head", "Head")
	local hc = { 0, y + 0.06, -segL * 0.75 }
	local mood = Kit.mood(ctx)
	Kit.head(B, { c = hc, r = { w * 0.45, w * 0.36, segL * 0.45 }, col = if carrion then "secondary" else "primary", piece = "s_bug_head_jaw", mood = mood, detail = detail, kind = if larva then "cute" else Kit.eyeKind(ctx, t),
		eyeD = w * 0.3, spacing = w * 0.24, eyeY = w * 0.08, noMouth = not larva, noBrows = true })
	local parent = "Body"
	for i = 1, n do
		local z = (i - 1) * segL * 0.86
		local bn = if i == 1 then "Body" else B:bone("Seg" .. i, parent, 0, y, z - segL * 0.45)
		if i > 1 then
			B:addRig("spine", bn)
		end
		local k = if larva then 1 - math.abs(i - n * 0.45) / n * 0.5 else 1 - (i - 1) / n * 0.25
		B:ell(w * k, w * 0.72 * k, segL * 1.05, at(0, y + (if larva then (k - 1) * 0.3 else 0), z, 0, 0, 0), { col = if i % 2 == 0 and not larva then "secondary" else "primary", mat = if larva then "skin" else "hard",
			bone = bn, pri = 1 + i * 0.02, role = "body", name = "Seg" .. i, mesh = if larva then "s_larva_seg" else "s_centipede_seg" })
		if not larva and (detail >= 1 or i % 2 == 1) then
			local hip = { w * 0.35 * k, y - 0.1, z }
			Kit.leg(B, { tag = "S" .. i, parent = bn, hip = hip, foot = { w * 0.35 * k + 1.0, 0.04, z - 0.25 }, w = 1.1 * Kit.LEG_RATIO * 1.1, col = "secondary", pri = 1.4 + i * 0.05, phase = (i * 0.17) % 1 })
		end
		if glowy and detail >= 1 and i % 2 == 0 then
			B:mball(0.22 * k, at(w * 0.3 * k, y + w * 0.22, z), { col = "glow", mat = "neon", glow = true, bone = bn, pri = 2.2 + i * 0.05, role = "detail", name = "Spot" .. i .. "#" })
		end
		parent = bn
	end
	if not larva then
		Kit.mandibles(B, { root = { 0.18, hc[2] - 0.15, hc[3] - segL * 0.35 }, len = 0.55, spread = 0.12, col = "darker", pri = 1.3, piece = "s_bug_mandible" })
		antennae(B, ctx, { H = { w * 0.45, w * 0.36, segL * 0.45 }, hc = hc }, { len = 1.2, kind = "thread", dir = { 0.4, 0.5, -0.7 }, w = 0.05, minDetail = 1 })
	end
	if carrion and detail >= 1 then
		for i = 1, (if detail >= 2 then 2 else 1) do
			B:mlimb({ 0.15 + i * 0.1, hc[2] + 0.1 - i * 0.12, hc[3] - 0.3 }, { 0.35 + i * 0.35, hc[2] + 0.4 - i * 0.4, hc[3] - 1.3 }, 0.1, { col = "secondary", mat = "skin", bone = "Head", pri = 1.5 + i * 0.2, role = "tentacle", name = "Feeler" .. i .. "#", trail = true }, 0.1)
		end
	end
	B:socket("core", at(0, y, 0.5), "Body")
	B:setRig("gait", if larva then "inch" else "crawl")
end

-- walking machines: a cockpit on two tall jointed legs, or a tripod with a grabber arm
K.Walker = function(B: any, ctx: any)
	local detail = ctx.detail
	local y = 3.2
	B.boneIndex.Body.pos = { 0, y, 0 }
	B:block(2.2, 1.5, 2.0, at(0, y + 0.4, 0), { col = "primary", mat = "metal", pri = 1, role = "body", name = "Cockpit" })
	B:block(1.6, 0.45, 0.25, at(0, y + 0.65, -1.05), { col = "glass", mat = "glass", tr = 0.2, pri = 1.2, role = "detail", name = "Visor" })
	B:mcyl(0.6, 0.7, at(1.25, y, 0), { col = "secondary", mat = "metal", pri = 1.3, role = "detail", name = "HipDrum#" })
	for side = 1, 1 do
		local hip = { 1.25, y, 0 }
		local knee = { 1.4, y - 1.2, -0.9 }
		local foot = { 1.35, 0.25, 0.1 }
		B:mirrorBone("Hip#", "Body", hip[1], hip[2], hip[3])
		B:addRig("legs", { hip = "HipR", side = 1, phase = 0 })
		B:addRig("legs", { hip = "HipL", side = -1, phase = 0.5 })
		B:mlimb(hip, knee, 0.5, { col = "secondary", mat = "metal", bone = "Hip#", pri = 1.2, role = "limb", name = "Thigh#" }, 0.1)
		B:mlimb(knee, foot, 0.42, { col = "secondary", mat = "metal", bone = "Hip#", pri = 1.25, role = "limb", name = "Shin#" }, 0.1)
		B:mblock(0.9, 0.3, 1.4, at(1.35, 0.15, -0.1), { col = "dark", mat = "metal", bone = "Hip#", pri = 1.3, role = "foot", name = "Foot#" })
		local _ = side
	end
	if detail >= 1 then
		B:mcyl(0.9, 0.3, at(1.3, y + 0.35, -0.8, 0, rad(90), 0), { col = "gunmetal", mat = "metal", pri = 1.6, role = "cannon", name = "Gun#" })
	end
	B:socket("core", at(0, y, 0), "Body")
	B:setRig("gait", "stomp")
	B:setRig("materialMotion", "clank")
end

K.ArmBot = function(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.0
	B.boneIndex.Body.pos = { 0, y, 0 }
	B:ell(2.0, 1.4, 2.0, at(0, y + 0.3, 0), { col = "primary", mat = "metal", pri = 1, role = "body", name = "Hub", mesh = "s_mech_pod" })
	B:ball(0.7, at(0, y + 0.4, -0.95), { col = "eyeGlow", mat = "neon", glow = true, pri = 1.1, role = "eye", name = "Lens" })
	for i = 1, 3 do
		local a = rad(90 + (i - 1) * 120)
		local hip = { math.cos(a) * 0.7, y - 0.2, math.sin(a) * 0.7 }
		local foot = { math.cos(a) * 2.2, 0.04, math.sin(a) * 2.2 }
		B:bone("Leg" .. i, "Body", hip[1], hip[2], hip[3])
		B:addRig("legs", { hip = "Leg" .. i, side = if math.cos(a) >= 0 then 1 else -1, phase = (i - 1) / 3 })
		local f = Kit.segFrame(hip, foot)
		local _, len = Kit.segFrame(hip, foot)
		B:part({ shape = "Ellipsoid", size = { 0.3, len * 1.05, 0.3 }, cf = f, seg = "Y", col = "secondary", mat = "metal", bone = "Leg" .. i, pri = 1.2, role = "limb", name = "Leg" .. i, mesh = "s_arthro_leg" })
	end
	B:bone("Arm", "Body", 0, y + 0.8, 0)
	B:addRig("arms", { arm = "Arm", side = 1 })
	B:limb({ 0, y + 0.8, 0 }, { 0.3, y + 2.6, -0.8 }, 0.45, { col = "secondary", mat = "metal", bone = "Arm", pri = 1.1, role = "limb", name = "Boom", mesh = "s_arthro_seg" }, 0.1)
	B:limb({ 0.3, y + 2.6, -0.8 }, { 0.4, y + 1.6, -2.2 }, 0.38, { col = "secondary", mat = "metal", bone = "Arm", pri = 1.2, role = "limb", name = "Jib", mesh = "s_arthro_seg" }, 0.1)
	B:ell(1.0, 0.8, 1.3, at(0.45, y + 1.3, -2.6, rad(-40), 0, 0), { col = "dark", mat = "metal", bone = "Arm", pri = 1.25, role = "claw", name = "Grabber", mesh = "s_crab_claw", trail = true })
	local _ = detail
	B:socket("core", at(0, y, 0), "Body")
	B:setRig("gait", "skitter")
	B:setRig("materialMotion", "clank")
end

return function(B: any, ctx: any)
	local kind = kindOf(ctx)
	ctx.traits.insect = true
	if kind == "Spider" or kind == "Scorpion" then
		ctx.kind = kind
		return arachnid()(B, ctx)
	elseif kind == "Crab" or kind == "Snail" then
		ctx.kind = kind
		return crustacean()(B, ctx)
	end
	local fn = K[kind] or K.Beetle
	fn(B, ctx)
	-- knights: a helm on the head and a lance
	local id = Kit.text(ctx)
	if has(id, "knight") and kind ~= "Dragonfly" and ctx.detail >= 1 then
		local hp = B.boneIndex.Head and B.boneIndex.Head.pos or { 0, 1.5, -1 }
		B:ell(0.9, 0.6, 0.9, at(0, hp[2] + 0.45, hp[3] - 0.3), { col = "steel", mat = "metal", bone = "Head", pri = 1.5, role = "hat", name = "Helm" })
		B:limb({ 0.6, hp[2] - 0.2, hp[3] + 0.3 }, { 0.75, hp[2] + 0.3, hp[3] - 2.6 }, 0.14, { col = "steel", mat = "metal", pri = 1.55, role = "weapon", name = "Lance", trail = true }, 0.02)
	end
end
