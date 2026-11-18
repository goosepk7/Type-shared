--!strict
-- Chelonian: turtles and tortoises. Called from one hook at the top of Plans/Quadruped (Turtle plan words and
-- shelled words whose id names a turtle / tortoise / terrapin); everything turtle-specific lives here.
-- Sub-kinds from the silhouette hints:
--   tortoise   high domed shell with raised scutes and a flared rim, elephantine column legs with toenails, a
--              beaked head on a wrinkled neck (star / radiated: rayed scutes; giant: long neck)
--   pond       medium dome, clawed webbed feet, striped head (painted, map, mud, musk, terrapin, box, baby)
--   sea        low teardrop shell, long front flippers and small rear paddles, big head (loggerhead); leatherback
--              and archelon: a leathery shell with seven keels
--   snapper    rugged keeled shell with a saw-toothed rear, huge hooked beak, long saw-ridged tail (alligator
--              snapping turtle: spikier, a pink worm lure in the mouth)
--   flat       softshell / pancake / henodus (a flat disc, snorkel nose), mata mata (flat knobbly shell,
--              triangular frilled head)
-- Motion: tortoises plod (slow heavy steps, head bobbing), pond turtles and snappers walk, sea turtles paddle
-- with their flippers. Sculpts (catalogue/s_shells.py): s_turtle_shell_dome, s_turtle_shell_flat,
-- s_turtle_shell_keel, s_turtle_shell_leather, s_turtle_shell_soft, s_turtle_head, s_turtle_head_snap,
-- s_turtle_leg, s_turtle_flipper (+_l).

local Geom = require(script.Parent.Parent.Geom)
local Face = require(script.Parent.Parent.Face)

local at = Geom.at
local rad = math.rad

local function has(s: string, list: string): boolean
	for w in string.gmatch(list, "%S+") do
		for _, suf in { "", "s", "es" } do
			if string.find(s, "%f[%a]" .. w .. suf .. "%f[%A]") then
				return true
			end
		end
	end
	return false
end

local Chelonian = {}

-- Is this word a turtle (as opposed to a snail, armadillo or other shelled quadruped)?
function Chelonian.wants(ctx: any): boolean
	local t = ctx.traits
	local id = string.lower(ctx.result.id or "")
	if t.plan == "Turtle" then
		return true
	end
	return t.shell == true and has(id, "turtle turtles tortoise tortoises terrapin terrapins archelon henodus megalochelys loggerhead ridley")
end

local function kindOf(id: string, hint: string): string
	if has(id, "snapping snapper") or string.find(hint, "spiky shell", 1, true) then
		return "snapper"
	elseif has(id, "softshell pancake henodus") or string.find(hint, "pancake", 1, true) or string.find(hint, "flat square", 1, true) then
		return "flat"
	elseif has(id, "mata") or string.find(hint, "leaf-like", 1, true) then
		return "matamata"
	elseif has(id, "sea leatherback loggerhead ridley archelon hawksbill") or string.find(hint, "flipper", 1, true) then
		return "sea"
	elseif has(id, "tortoise tortoises megalochelys") or string.find(hint, "domed", 1, true) or string.find(hint, "high shell", 1, true) then
		return "tortoise"
	end
	return "pond"
end

-- A leg: a column from the hip under the shell rim to the foot (one sculpt with scales and toenails), or a flipper.
local function leg(B: any, o: any)
	local bone = "Hip" .. o.tag .. "#"
	local hr, hl = B:mirrorBone(bone, "Body", o.hip[1], o.hip[2], o.hip[3])
	B:addRig("legs", { hip = hr, side = 1, phase = o.phase, len = o.hip[2], plod = true })
	B:addRig("legs", { hip = hl, side = -1, phase = (o.phase + 0.5) % 1, len = o.hip[2], plod = true })
	local f, len = Geom.between(o.hip[1], o.hip[2], o.hip[3], o.foot[1], o.foot[2], o.foot[3], "Y")
	f = Geom.rollY(f, 0, 0, -1)
	B:mirror({ shape = "Ellipsoid", size = { o.w, len * 1.12, o.w * 0.92 }, cf = f, seg = "Y", col = o.col, mat = "skin", bone = bone, pri = o.pri, role = "limb", name = "Leg" .. o.tag .. "#", mesh = o.piece or "s_turtle_leg" })
	if o.pad then
		B:mell(o.w * 1.25, o.w * 0.42, o.w * 1.35, at(o.foot[1], o.w * 0.2, o.foot[3] - o.w * 0.12), { col = o.col, mat = "skin", bone = bone, pri = o.pri + 1.4, role = "foot", name = "Foot" .. o.tag .. "#", mesh = "quad_paw" })
	end
end

local function flipper(B: any, o: any)
	local bone = "Flip" .. o.tag .. "#"
	local hr, hl = B:mirrorBone(bone, "Body", o.root[1], o.root[2], o.root[3])
	B:addRig("wings", { bone = hr, side = 1, flipper = true })
	B:addRig("wings", { bone = hl, side = -1, flipper = true })
	local f, len = Geom.between(o.root[1], o.root[2], o.root[3], o.tip[1], o.tip[2], o.tip[3], "Y")
	f = Geom.rollY(f, 0, 1, 0)
	-- a long flat paddle: wide in local X (the chord), thin in local Z (up)
	B:mirror({ shape = "Ellipsoid", size = { o.chord, len * 1.1, o.chord * 0.22 }, cf = f, seg = "Y", col = o.col, mat = "skin", bone = bone, pri = o.pri, role = "fin", name = "Flipper" .. o.tag .. "#",
		mesh = "s_turtle_flipper", meshL = "s_turtle_flipper_l", trail = o.trail })
end

function Chelonian.build(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id = string.lower(ctx.result.id or "")
	local hint = string.lower((ctx.result.visual and ctx.result.visual.silhouetteHint) or "")
	local kind = kindOf(id, hint)
	local mood = ctx.result.mood or "Neutral"
	local leather = has(id, "leatherback archelon") or string.find(hint, "leathery", 1, true) ~= nil
	local giant = has(id, "giant megalochelys archelon sulcata") or t.size == "Large" or t.size == "Huge"
	local baby = has(id, "baby") or t.cute
	local soft = has(id, "softshell")
	t.arch = "reptile"

	-- shell dimensions (W wide, H tall, L long) and the height of its centre
	local W, H, L, sy = 2.6, 1.55, 3.0, 1.15
	local legW, legH = 0.55, 0.62
	local shellPiece = "s_turtle_shell_dome"
	if kind == "tortoise" then
		W, H, L, sy = 2.7, if has(id, "radiated star box") or string.find(hint, "high", 1, true) then 2.0 else 1.85, 3.0, 1.2
		legW, legH = 0.62, 0.72
	elseif kind == "pond" then
		W, H, L, sy = 2.45, 1.25, 2.95, 0.9
		legW, legH = 0.42, 0.5
	elseif kind == "sea" then
		W, H, L, sy = 2.5, 0.95, 3.2, 1.25
		shellPiece = if leather then "s_turtle_shell_leather" else "s_turtle_shell_flat"
	elseif kind == "snapper" then
		W, H, L, sy = 2.5, 1.15, 2.9, 0.95
		legW, legH = 0.5, 0.55
		shellPiece = "s_turtle_shell_keel"
	elseif kind == "flat" then
		W, H, L, sy = 2.75, if soft then 0.5 else 0.7, 3.0, 0.7
		legW, legH = 0.42, 0.45
		shellPiece = if soft or has(id, "henodus") then "s_turtle_shell_soft" else "s_turtle_shell_flat"
	elseif kind == "matamata" then
		W, H, L, sy = 2.6, 0.75, 3.0, 0.72
		legW, legH = 0.4, 0.45
		shellPiece = "s_turtle_shell_keel"
	end
	if baby then
		-- hatchlings: a bigger head and rounder shell
		H *= 1.08
	end
	B.boneIndex.Body.pos = { 0, sy, 0 }
	local skin = if kind == "sea" or kind == "flat" then "secondary" else "secondary"
	local shellMat = if leather or soft then "skin" else "hard"

	-- carapace + plastron (the plastron is a flatter lens under the rim, belly coloured)
	local shell = B:ell(W, H, L, at(0, sy, 0), { col = "primary", mat = shellMat, pri = 1.0, role = "body", name = "Shell", mesh = shellPiece })
	local _ = shell
	if detail >= 1 then
		B:ell(W * 0.86, H * 0.42, L * 0.88, at(0, sy - H * 0.3, 0.02), { col = "belly", mat = "hard", pri = 1.9, role = "detail", name = "Plastron" })
	end
	-- shell markings (primitive layer; the sculpt carries scutes and keels): radiating star rays, painted lines
	if detail >= 2 and (has(id, "radiated star map painted box") or string.find(hint, "star", 1, true) or string.find(hint, "markings", 1, true) or string.find(hint, "lines", 1, true)) then
		local n = if detail >= 3 then 3 else 2
		for i = 1, n do
			local z = -L * 0.22 + (i - 1) * (L * 0.44 / math.max(n - 1, 1))
			local yy = sy + H * 0.5 * math.sqrt(math.max(0.05, 1 - (z / (L * 0.5)) ^ 2))
			local nx, ny, nz = Geom.normalize(0, (yy - sy) / (H * H * 0.25), z / (L * L * 0.25))
			local f = Geom.rollY((Geom.between(0, yy, z, nx, yy + ny, z + nz, "Y")), 0, 0, -1)
			B:part({ shape = "Ellipsoid", size = { W * 0.2, H * 0.12, L * 0.16 }, cf = f, col = "secondary", mat = "hard", pri = 2.4 + i * 0.1, role = "detail", name = "Scute" .. i })
		end
	end

	-- neck + head
	local neckLen = if has(id, "giant") or string.find(hint, "long neck", 1, true) then 1.15 elseif kind == "matamata" then 1.1 elseif kind == "sea" then 0.45 else 0.6
	local nb = { 0, sy - H * 0.05, -L * 0.44 }
	local nt = { 0, nb[2] + neckLen * (if kind == "sea" or kind == "flat" or kind == "matamata" then 0.15 else 0.55), nb[3] - neckLen * 0.85 }
	B:bone("Neck", "Body", nb[1], nb[2], nb[3])
	B:setRig("neck", "Neck")
	B:limb(nb, nt, if kind == "snapper" then 0.7 else 0.55, { col = skin, mat = "skin", bone = "Neck", pri = 1.2, role = "body", name = "Neck", mesh = "s_tail_seg" }, 0.35)
	B:bone("Head", "Neck", nt[1], nt[2], nt[3])
	B:setRig("head", "Head")
	local hs = (if kind == "snapper" then 0.62 elseif kind == "sea" then (if has(id, "loggerhead") then 0.6 else 0.5) elseif kind == "matamata" then 0.55 else 0.48) * (if baby then 1.25 else 1) * (if giant and kind == "tortoise" then 0.9 else 1)
	local hr = { hs * 0.82, hs * 0.72, hs * 1.05 }
	local flatHead = kind == "matamata"
	if flatHead then
		hr = { hs * 1.15, hs * 0.38, hs * 1.1 }
	end
	local hc = { 0, nt[2] + hr[2] * 0.25, nt[3] - hr[3] * 0.62 }
	B:ell(hr[1] * 2, hr[2] * 2, hr[3] * 2, at(hc[1], hc[2], hc[3], rad(if kind == "tortoise" then -6 else 0), 0, 0), { col = skin, mat = "skin", bone = "Head", pri = 1.05, role = "head", name = "Head",
		mesh = if kind == "snapper" then "s_turtle_head_snap" elseif flatHead then "s_matamata_head" else "s_turtle_head" })
	local fierce = kind == "snapper" and not baby
	local cute = baby or (mood ~= "Neutral" and mood ~= "Angry")
	Face.build(B, {
		face = { kind = "ellipsoid", c = hc, r = hr }, bone = "Head", mood = mood, detail = detail, kind = if fierce then "fierce" elseif cute then "cute" else "cute",
		spacing = hr[1] * (if flatHead then 0.7 else 0.62), y = hr[2] * (if flatHead then 0.4 else 0.28), d = hr[1] * (if baby then 0.62 else 0.48), mouthY = -hr[2] * 0.45, mouthW = hr[1] * 0.7,
		noMouth = not cute, noBrows = detail < 3 and not fierce, lidCol = skin, pri = 1.12,
	})
	B:socket("mouth", at(hc[1], hc[2] - hr[2] * 0.3, hc[3] - hr[3] * 0.85), "Head")
	if (soft or kind == "matamata") and detail >= 1 then
		-- snorkel snout
		B:limb({ 0, hc[2] + hr[2] * 0.1, hc[3] - hr[3] * 0.75 }, { 0, hc[2] + hr[2] * 0.25, hc[3] - hr[3] * 1.35 }, hr[1] * 0.35, { col = skin, mat = "skin", bone = "Head", pri = 1.3, role = "snout", name = "Snorkel", mesh = "s_tail_tip" }, 0.1)
	end
	if kind == "matamata" and detail >= 2 then
		B:mell(hr[1] * 0.9, hr[2] * 0.3, hr[3] * 0.7, at(hr[1] * 0.95, hc[2] - hr[2] * 0.3, hc[3] + hr[3] * 0.2, 0, 0, rad(-25)), { col = "primary", mat = "skin", bone = "Head", pri = 2.2, role = "detail", name = "Frill#", mesh = "s_petal" })
	end
	if has(id, "alligator") and detail >= 2 then
		B:ell(hr[1] * 0.35, hr[2] * 0.2, hr[3] * 0.25, at(0, hc[2] - hr[2] * 0.42, hc[3] - hr[3] * 0.62), { col = "tongue", mat = "skin", bone = "Head", pri = 2.4, role = "mouth", name = "Lure" })
	end
	if has(id, "terrapin painted") and detail >= 2 then
		B:mell(hr[1] * 0.18, hr[2] * 0.35, hr[3] * 0.55, at(hr[1] * 0.95, hc[2] + hr[2] * 0.05, hc[3] + hr[3] * 0.35), { col = if has(id, "terrapin") then "red" else "gold", mat = "skin", bone = "Head", pri = 2.3, role = "detail", name = "EarStripe#" })
	end

	-- limbs
	if kind == "sea" then
		local big = if leather or has(id, "archelon") then 1.25 else 1
		flipper(B, { tag = "F", root = { W * 0.36, sy - H * 0.1, -L * 0.26 }, tip = { W * 0.36 + 2.1 * big, sy - H * 0.3, -L * 0.26 + 0.75 * big }, chord = 0.95 * big, col = skin, pri = 1.1, trail = true })
		if detail >= 1 then
			flipper(B, { tag = "B", root = { W * 0.3, sy - H * 0.15, L * 0.36 }, tip = { W * 0.3 + 0.8, sy - H * 0.3, L * 0.36 + 0.7 }, chord = 0.62, col = skin, pri = 1.35 })
		end
	else
		local hipY = sy - H * 0.12
		local spread = if kind == "flat" or kind == "matamata" then 0.6 elseif kind == "tortoise" then 0.32 else 0.45
		leg(B, { tag = "F", hip = { W * 0.36, hipY, -L * 0.3 }, foot = { W * 0.36 + spread, 0.06, -L * 0.3 - 0.2 }, w = legW * (if kind == "tortoise" then 1.1 else 1), col = skin, pri = 1.15, phase = 0,
			piece = if kind == "tortoise" then "s_turtle_leg" else "s_turtle_leg_webbed", pad = detail >= 3 and kind ~= "tortoise" })
		leg(B, { tag = "B", hip = { W * 0.34, hipY, L * 0.3 }, foot = { W * 0.34 + spread * 0.9, 0.06, L * 0.3 + 0.18 }, w = legW, col = skin, pri = 1.2, phase = 0.5,
			piece = if kind == "tortoise" then "s_turtle_leg" else "s_turtle_leg_webbed", pad = detail >= 3 and kind ~= "tortoise" })
		local _ = legH
	end

	-- tail: a stub (tortoises), long and saw-ridged (snappers)
	if detail >= 1 or kind == "snapper" then
		local tb = B:bone("Tail1", "Body", 0, sy - H * 0.15, L * 0.45)
		B:addRig("tail", tb)
		local tl = if kind == "snapper" then 2.0 else 0.6
		B:limb({ 0, sy - H * 0.15, L * 0.44 }, { 0, sy - H * 0.3 - tl * 0.25, L * 0.44 + tl }, if kind == "snapper" then 0.42 else 0.3, { col = skin, mat = "skin", bone = tb, pri = if kind == "snapper" then 1.3 else 2.0, role = "tail", name = "Tail", mesh = if kind == "snapper" then "s_tail_spiked" else "s_tail_tip", trail = true }, 0.1)
	end
	B:socket("core", at(0, sy, 0), "Body")
	B:setRig("gait", if kind == "sea" then "paddle" elseif kind == "tortoise" or giant then "plod" else "plod")
end

return Chelonian
