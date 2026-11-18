--!strict
-- Finned fish for Plans/Fish: one parametric finfish (fusiform, compressed disc, long, round, deep-sea, catfish,
-- billfish) driven by a profile per kind plus features read from the id and silhouette hint (big mouth, fangs,
-- lure, barbels, bill, tube eyes, hump, spines, bands, walking fins), and the three body plans that are not a
-- spindle: flatfish (lying on one side, eyes on top), rays (a disc with flapping wings and a whip tail) and
-- seahorses (upright, curled tail).
--
-- Every body mass and fin is an ellipsoid in the model's own axes, so the sculpts (tools/meshgen/catalogue/
-- s_aquatic.py, unit pieces in the lead's frame) scale with the profile: the same s_aq_fish_body is a tuna, a
-- discus or a gar. The body sits on Body, the tail half on Tail1 and the caudal fin on Tail2, so swimming
-- undulates the back half.

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Face = require(script.Parent.Parent.Face)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local SeaFish = {}

local function mood(B: any): string
	return B.ctx.result.mood or "Neutral"
end

local function hintOf(ctx: any): string
	return string.lower((ctx.result.visual and ctx.result.visual.silhouetteHint) or "")
end

-- word test on id + hint
function SeaFish.reader(ctx: any): (...string) -> boolean
	local id = string.lower(ctx.result.id)
	local hint = hintOf(ctx)
	return function(...: string): boolean
		for _, w in { ... } do
			if string.find(id, w, 1, true) or string.find(hint, w, 1, true) then
				return true
			end
		end
		return false
	end
end

-- Profiles: L length (snout to peduncle), H height, W width, front (share of L in the front mass), tail kind,
-- dorsal kind, eye size (share of H).
local PROFILE: { [string]: any } = {
	fish = { L = 2.8, H = 1.3, W = 0.85, front = 0.6, tail = "fork", dorsal = "soft", eye = 0.25, tailH = 1.0 },
	disc = { L = 2.0, H = 2.1, W = 0.5, front = 0.68, tail = "fan", dorsal = "tall", eye = 0.2, tailH = 0.75, anal = true },
	long = { L = 4.2, H = 0.8, W = 0.7, front = 0.5, tail = "fan", dorsal = "back", eye = 0.3, tailH = 0.95 },
	round = { L = 1.9, H = 1.7, W = 1.55, front = 0.78, tail = "fan", dorsal = "small", eye = 0.2, tailH = 0.7 },
	deep = { L = 2.3, H = 1.75, W = 1.35, front = 0.72, tail = "fan", dorsal = "small", eye = 0.17, tailH = 0.7 },
	catfish = { L = 3.3, H = 1.0, W = 1.15, front = 0.55, tail = "fork", dorsal = "small", eye = 0.18, tailH = 0.95, flatHead = true },
	billfish = { L = 3.4, H = 1.2, W = 0.8, front = 0.6, tail = "lunate", dorsal = "sail", eye = 0.22, tailH = 1.35 },
	tadpole = { L = 1.5, H = 1.1, W = 1.1, front = 0.95, tail = "ribbon", dorsal = "none", eye = 0.26, tailH = 0.9 },
}
SeaFish.Profiles = PROFILE

-- A fin made of one thin ellipsoid in the model axes (x thin): the sculpt `piece` draws the real fin in its box.
local function fin(B: any, name: string, bone: string, sx: number, sy: number, sz: number, cf: any, col: string, pri: number, piece: string?, o: any?): any
	local spec: any = { col = col, mat = "skin", bone = bone, pri = pri, role = "fin", name = name, mesh = piece or false }
	if o then
		for k, v in o do
			spec[k] = v
		end
	end
	return B:ell(sx, sy, sz, cf, spec)
end

-- Caudal fin at (y, z) on bone; returns nothing. kind: fork | lunate | fan | flow | ribbon | none
local function caudal(B: any, kind: string, bone: string, y: number, z: number, h: number, l: number, t: number, col: string, detail: number)
	if kind == "none" then
		-- clavus (ocean sunfish): a short scalloped frill instead of a tail
		fin(B, "TailFin", bone, t * 1.4, h * 0.9, l * 0.35, at(0, y, z), col, 1.3, "s_aq_caudal_fan", { trail = true })
		return
	end
	if kind == "fan" or kind == "flow" or kind == "ribbon" then
		local k = if kind == "flow" then 1.5 elseif kind == "ribbon" then 1.25 else 1
		local hh = if kind == "ribbon" then h * 0.75 else h * 0.95 * k
		fin(B, "TailFin", bone, t, hh, l * 0.9 * k, at(0, y + (if kind == "ribbon" then 0 else h * 0.02), z + l * 0.4 * k), col, 1.3,
			if kind == "ribbon" then "s_aq_caudal_fan" else "s_aq_caudal_fan", { trail = true })
		return
	end
	-- forked / lunate: a fleshy root (the sculpt lead) and two lobes (its members)
	local lun = kind == "lunate"
	local root = fin(B, "TailFin", bone, t * 1.6, h * 0.42, l * 0.5, at(0, y, z + l * 0.12), col, 1.3, if lun then "s_aq_caudal_lunate" else "s_aq_caudal_fork", { trail = true })
	if detail >= 1 then
		local ang = rad(if lun then 52 else 40)
		local ll = h * (if lun then 0.72 else 0.62)
		local up = fin(B, "TailLobe", bone, t, ll, l * 0.34, at(0, y + h * 0.27, z + l * 0.42, ang, 0, 0), col, 1.32, nil)
		local dn = fin(B, "TailLobe", bone, t, ll * 0.92, l * 0.32, at(0, y - h * 0.25, z + l * 0.4, -ang, 0, 0), col, 1.34, nil)
		B:sculpt(root, root.mesh, { up, dn })
	end
end
SeaFish.caudal = caudal

-- Dorsal fin: lead ellipsoid centred on the back line, the sculpt sweeps it back.
local function dorsal(B: any, kind: string, bone: string, top: number, z: number, h: number, l: number, t: number, col: string, pri: number)
	if kind == "none" then
		return
	end
	local piece = if kind == "spiny" or kind == "sail" then "s_aq_dorsal_spiny" else "s_aq_dorsal"
	fin(B, "Dorsal", bone, t, h * 1.3, l, at(0, top + h * 0.12, z), col, pri, piece, { trail = true })
end

-- Anal fin: the dorsal sculpt turned upside down under the tail half.
local function anal(B: any, bone: string, bottom: number, z: number, h: number, l: number, t: number, col: string, pri: number)
	fin(B, "Anal", bone, t, h * 1.3, l, at(0, bottom - h * 0.12, z, 0, 0, math.pi), col, pri, "s_aq_dorsal")
end

-- Bands across the body (clownfish, convict cichlid, barbs): thin ellipsoid slices a little proud of the masses.
local function bands(B: any, n: number, y: number, zs: { number }, rs: { { number } }, bones: { string }, pri: number)
	for i = 1, n do
		local r = rs[i]
		B:ell(r[1] * 2.1, r[2] * 2.1, r[3], at(0, y, zs[i]), { col = "secondary", mat = "skin", bone = bones[i], pri = pri + i * 0.05, role = "detail", name = "Band", mesh = false })
	end
end

-- Finned fish. kind: fish | disc | long | round | deep | catfish | billfish | tadpole
function SeaFish.finfish(B: any, ctx: any, kind: string)
	local t, detail = ctx.traits, ctx.detail
	local has = SeaFish.reader(ctx)
	local P = table.clone(PROFILE[kind] or PROFILE.fish)
	local id = string.lower(ctx.result.id)
	-- per-word reshaping inside a kind
	if has("sunfish") and not has("bluegill") and has("huge round", "no tail") then
		P.L, P.H, P.W, P.tail, P.dorsal, P.front, P.anal = 2.2, 2.4, 0.6, "none", "tall", 0.85, true
	end
	if has("boxfish", "cube") then
		P.box = true
	end
	if has("flowing", "fan tail", "silky", "long fins", "long wing fins", "flowing tail") then
		P.tail = "flow"
		P.flow = true
	end
	if has("tuna", "mackerel", "wahoo", "amberjack", "trevally", "bonito", "torpedo", "streamlined", "speedy") then
		P.tail, P.H, P.W = "lunate", P.H * 1.05, P.W * 1.1
	end
	if has("sword tail") then
		P.swordTail = true
	end
	if has("moorish idol", "streamer") then
		P.dorsal = "streamer"
	end
	if has("spiny", "spines", "spine", "venom") and P.dorsal ~= "sail" then
		P.dorsal = "spiny"
	end
	if has("perch", "bass", "grouper", "snapper", "zander", "walleye", "sculpin", "rockfish", "crappie", "bluegill", "cichlid", "tilapia", "oscar", "lionfish", "scorpionfish") then
		P.dorsal = if P.dorsal == "tall" then "tall" else "spiny"
	end
	local mouthBig = has("big-mouth", "big mouth", "huge mouth", "gaping", "huge lips", "toothy", "bass", "grouper", "giant bulldog") or kind == "deep"
	local fangs = has("fang", "teeth", "toothy", "underbite", "buzzsaw", "jaws") or kind == "deep"
	local lure = has("lure", "glowing barbel")
	local barbels = kind == "catfish" or has("whisker", "barbel", "carp", "cod", "sturgeon", "burbot", "loach", "beard")
	local tubeEyes = has("tube eye")
	local hump = has("hump", "melon head")
	local legs = has("walks on fin", "leg-fin", "leg fins", "walking", "crawling", "tripod", "stilt", "perched")
	local glowDots = has("lights", "glowing spots", "glowing eye patch", "glowing belly", "glowing neon", "glowing")
	local banded = has("stripe", "striped", "bars", "bands", "banded") and not has("side stripe")
	local bigEyes = t.bigEyes or has("big-eyed", "goggle", "glassy", "huge dark eyes")
	local armour = has("armor", "armour", "bony", "plates", "scaled long")
	local bill = kind == "billfish" or has("spear bill", "sword bill", "beak", "long beak", "needle", "alligator snout", "paddle", "trunk-like", "shovel", "saw snout", "rostrum", "lower jaw much longer")

	local L, H, W = P.L, P.H, P.W
	if t.chubby or has("chubby", "chunky", "stocky", "blocky", "fat", "sausage") then
		H *= 1.15
		W *= 1.2
	end
	if has("thin", "slender", "slim") and kind ~= "long" then
		H *= 0.85
		W *= 0.8
	end
	local y = H * 0.5 + (if legs then 0.75 else 0.8)
	B.boneIndex.Body.pos = { 0, y, 0 }
	local z0 = -L * 0.5
	local fl = L * P.front
	local fc = { 0, y, z0 + fl * 0.5 }
	local fr = { W * 0.5, H * 0.5, fl * 0.5 }
	if P.flatHead then
		fr[2] *= 0.88
		fc[2] -= H * 0.05
	end
	local body
	if P.box then
		body = B:block(W * 1.05, H * 0.95, fl, at(fc[1], fc[2], fc[3]), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Body" })
	else
		body = B:ell(fr[1] * 2, fr[2] * 2, fr[3] * 2, at(fc[1], fc[2], fc[3]), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Body",
			mesh = if kind == "deep" or kind == "round" then "s_aq_fish_head" else "s_aq_fish_body" })
	end
	-- belly: a pale underside sunk into the front mass (countershading)
	if detail >= 2 and not P.box then
		B:ell(fr[1] * 1.7, fr[2] * 1.1, fr[3] * 1.7, at(0, fc[2] - fr[2] * 0.45, fc[3] + fr[3] * 0.05), { col = "belly", mat = "skin", pri = 2.0, role = "detail", name = "Belly", mesh = false })
	end
	-- tail half
	local t1 = B:bone("Tail1", "Body", 0, y, z0 + fl * 0.62)
	local t2 = B:bone("Tail2", t1, 0, y, z0 + L * 0.86)
	B:addRig("tail", t1)
	B:addRig("tail", t2)
	-- reference proportions of the s_aq_fish_tail sculpt: W * 0.84, H * 0.88, L * 0.64 (rear 34% .. 98% of L)
	local rl = L * (if kind == "tadpole" then 0.4 else 0.64)
	local rc = { 0, y + H * 0.01, z0 + L * (if kind == "tadpole" then 0.85 else 0.66) }
	local rr = { W * 0.42, H * 0.44, rl * 0.5 }
	if kind == "disc" then
		rr = { W * 0.44, H * 0.36, rl * 0.5 }
	end
	local rear = B:ell(rr[1] * 2, rr[2] * 2, rr[3] * 2, at(rc[1], rc[2], rc[3]), { col = "primary", mat = "skin", bone = t1, pri = 1.1, role = "body", name = "Rear", mesh = "s_aq_fish_tail" })
	local ped
	if detail >= 1 and kind ~= "tadpole" then
		ped = B:ell(W * 0.24, H * 0.26, L * 0.18, at(0, y + H * 0.01, z0 + L * 0.92), { col = "primary", mat = "skin", bone = t2, pri = 1.25, role = "body", name = "Peduncle", mesh = false })
		B:sculpt(rear, "s_aq_fish_tail", { ped })
	end
	-- caudal fin
	local finCol = if t.shark or kind == "deep" then "primary" else "secondary"
	local th = H * P.tailH * (if kind == "disc" then 1.15 else 1)
	caudal(B, P.tail, t2, y + H * 0.01, z0 + L * 0.94, th, L * 0.3, 0.1, finCol, detail)
	if P.swordTail and detail >= 2 then
		B:limb({ 0, y - th * 0.3, z0 + L * 1.05 }, { 0, y - th * 0.45, z0 + L * 1.55 }, 0.12, { col = "dark", mat = "skin", bone = t2, pri = 2.3, role = "fin", name = "Sword", trail = true, mesh = false }, 0.1)
	end
	-- dorsal / anal
	local top = fc[2] + fr[2]
	if P.dorsal == "sail" then
		dorsal(B, "sail", "Body", top - H * 0.08, z0 + L * 0.45, H * 1.05, L * 0.62, 0.1, "secondary", 1.4)
	elseif P.dorsal == "tall" then
		dorsal(B, "soft", "Body", top - H * 0.12, z0 + L * 0.58, H * 0.55, L * 0.55, 0.1, finCol, 1.4)
	elseif P.dorsal == "streamer" then
		dorsal(B, "soft", "Body", top - H * 0.12, z0 + L * 0.45, H * 0.9, L * 0.35, 0.1, finCol, 1.4)
		if detail >= 2 then
			B:limb({ 0, top + H * 0.6, z0 + L * 0.45 }, { 0, top + H * 0.5, z0 + L * 1.25 }, 0.1, { col = "secondary", mat = "skin", pri = 2.6, role = "fin", name = "Streamer", trail = true, mesh = false }, 0.1)
		end
	elseif P.dorsal == "back" then
		dorsal(B, "soft", t1, rc[2] + rr[2] - H * 0.08, z0 + L * 0.74, H * 0.42, L * 0.2, 0.09, finCol, 1.45)
	elseif P.dorsal == "small" then
		dorsal(B, "soft", "Body", top - H * 0.1, z0 + L * 0.55, H * 0.3, L * 0.22, 0.09, finCol, 1.5)
	elseif P.dorsal == "spiny" then
		dorsal(B, "spiny", "Body", top - H * 0.1, z0 + L * 0.5, H * 0.48, L * 0.42, 0.1, finCol, 1.4)
	elseif P.dorsal ~= "none" then
		dorsal(B, "soft", "Body", top - H * 0.1, z0 + L * 0.47, H * (if P.flow then 0.75 else 0.5), L * 0.3, 0.1, finCol, 1.4)
	end
	if (P.anal and detail >= 1) or ((P.flow or kind == "billfish") and detail >= 2) then
		local ah = if kind == "disc" or P.dorsal == "tall" then H * 0.5 else H * 0.3
		anal(B, if kind == "disc" then "Body" else t1, rc[2] - rr[2] + H * 0.08, z0 + L * (if kind == "disc" then 0.62 else 0.7), ah, L * (if kind == "disc" then 0.4 else 0.22), 0.09, finCol, if kind == "disc" then 1.42 else 2.2)
	end
	-- pectoral fins (sculpt: s_fin_side by the role rule) and pelvic fins
	if detail >= 1 then
		local pw = W * (if P.flow then 1.1 else 0.85) * (if has("flying fish", "wing fins") then 2.6 else 1)
		local px, pz = fr[1] * 0.92 + pw * 0.3, fc[3] + fr[3] * 0.25
		if legs then
			-- fins that walk: a pectoral leg on each side reaching the ground
			local hr, hl = B:mirrorBone("Fin#", "Body", px * 0.8, y - H * 0.2, pz)
			B:addRig("legs", { hip = hr, side = 1, phase = 0, len = y })
			B:addRig("legs", { hip = hl, side = -1, phase = 0.5, len = y })
			B:mlimb({ px * 0.8, y - H * 0.2, pz }, { px * 1.25, 0.12, pz - L * 0.08 }, W * 0.32, { col = finCol, mat = "skin", bone = "Fin#", pri = 1.6, role = "limb", name = "FinLeg#" }, 0.15)
			if detail >= 2 then
				B:mell(W * 0.55, 0.12, W * 0.45, at(px * 1.3, 0.08, pz - L * 0.12), { col = finCol, mat = "skin", bone = "Fin#", pri = 2.4, role = "fin", name = "FinFoot#", mesh = "s_fin_side" })
			end
		else
			B:mell(pw, 0.09, L * 0.17, at(px, y - H * 0.18, pz, rad(8), rad(-28), rad(-24)), { col = finCol, mat = "skin", pri = 1.8, role = "fin", name = "Pectoral#" })
		end
		if detail >= 3 and kind ~= "round" then
			B:mell(W * 0.45, 0.07, L * 0.11, at(fr[1] * 0.45, fc[2] - fr[2] * 0.92, fc[3] + fr[3] * 0.55, rad(-10), rad(-15), rad(-55)), { col = finCol, mat = "skin", pri = 3.0, role = "fin", name = "Pelvic#" })
		end
	end
	-- jaws, bills and snouts
	local mz = fc[3] - fr[3]
	if bill then
		local bl = L * (if has("needle", "lower jaw much longer") then 0.35 elseif kind == "billfish" then 0.5 else 0.3)
		local by = fc[2] - fr[2] * (if has("lower jaw much longer") then 0.35 else 0.05)
		local bw = H * (if has("paddle", "shovel") then 0.18 else 0.12)
		if has("paddle", "shovel") then
			B:ell(W * 0.75, bw, bl, at(0, by, mz - bl * 0.32, rad(-4), 0, 0), { col = "secondary", mat = "skin", pri = 1.35, role = "snout", name = "Paddle", mesh = false })
		elseif has("trunk-like") then
			B:limb({ 0, by - H * 0.15, mz + fr[3] * 0.1 }, { 0, by - H * 0.55, mz - bl * 0.6 }, bw * 1.2, { col = "primary", mat = "skin", pri = 1.35, role = "horn", name = "Trunk", trail = true }, 0.1)
		else
			B:limb({ 0, by, mz + fr[3] * 0.25 }, { 0, by + H * 0.02, mz - bl }, bw, { col = if kind == "billfish" then "secondary" else "primary", mat = "hard", pri = 1.35, role = "horn", name = "Bill", trail = true }, 0.06)
			if has("saw", "rostrum") and detail >= 2 then
				for i = 1, 3 do
					B:mwedge(0.05, bw * 0.8, bw * 0.6, at(bw * 0.45, by, mz - bl * (0.25 + i * 0.22), 0, 0, rad(-90)), { col = "tooth", mat = "hard", pri = 3 + i * 0.1, role = "tooth" })
				end
			end
		end
	end
	if mouthBig or has("lips", "red lips", "huge lips", "beak") then
		local jb = B:bone("Jaw", "Body", 0, fc[2] - fr[2] * 0.25, fc[3] - fr[3] * 0.2)
		B:setRig("jaw", jb)
		local jw, jh, jl = fr[1] * 1.55, fr[2] * 0.62, fr[3] * 0.95
		local beak = has("beak") and not bill
		B:ell(jw, jh, jl, at(0, fc[2] - fr[2] * 0.45, fc[3] - fr[3] * 0.48, rad(-8), 0, 0), { col = if beak then "beak" elseif has("red lips") then "accent" else "primary", mat = if beak then "hard" else "skin", bone = jb, pri = 1.45, role = "jaw", name = "Jaw", mesh = false })
		if fangs and detail >= 2 then
			Parts.teeth(B, { bone = "Body", y = fc[2] - fr[2] * 0.2, z = mz + fr[3] * 0.12, r = fr[1] * 0.42, n = if detail >= 3 then 4 else 2, h = H * (if kind == "deep" then 0.26 else 0.14), pri = 2.6 })
		end
	end
	if barbels and detail >= 1 then
		local n = if kind == "catfish" and detail >= 2 then 2 else 1
		for i = 1, n do
			local bx = fr[1] * (0.45 + 0.2 * i)
			local by = fc[2] - fr[2] * (0.2 + 0.25 * i)
			local bz = mz + fr[3] * 0.25
			local len = H * (if kind == "catfish" then 0.9 else 0.45) / i
			B:mlimb({ bx, by, bz }, { bx + len * 0.6, by - len * 0.45, bz + len * 0.55 }, 0.07, { col = "darker", mat = "skin", pri = 2.4 + i * 0.3, role = "antenna", name = "Barbel#", trail = true }, 0.1)
		end
	end
	if lure then
		-- illicium: a stalk from the forehead arching forward, a glowing bulb (esca) at its tip
		local lb = B:bone("Lure", "Body", 0, top, fc[3] - fr[3] * 0.3)
		B:addRig("sway", lb)
		local a = { 0, top - H * 0.05, fc[3] - fr[3] * 0.25 }
		local m = { 0, top + H * 0.55, fc[3] - fr[3] * 0.55 }
		local e = { 0, top + H * 0.5, fc[3] - fr[3] * 1.15 }
		B:limb(a, m, 0.09, { col = "primary", mat = "skin", bone = lb, pri = 1.5, role = "antenna", name = "Stalk", mesh = false }, 0.15)
		B:limb(m, e, 0.07, { col = "primary", mat = "skin", bone = lb, pri = 1.55, role = "antenna", name = "Stalk2", mesh = false }, 0.2)
		B:ball(H * 0.2, at(e[1], e[2] - H * 0.05, e[3]), { col = "glow", mat = "neon", glow = true, bone = lb, pri = 1.6, role = "gem", name = "Esca", noCore = true })
	end
	if hump and detail >= 1 then
		B:ell(fr[1] * 1.5, fr[2] * 1.05, fr[3] * 1.0, at(0, fc[2] + fr[2] * 0.55, fc[3] - fr[3] * 0.3), { col = if has("melon") then "primary" else "secondary", mat = "skin", pri = 1.5, role = "body", name = "Hump", mesh = false })
	end
	if armour and detail >= 2 then
		local pts = {}
		for i = 1, (if detail >= 3 then 4 else 3) do
			local z = z0 + L * (0.18 + i * 0.13)
			local bone = if z > z0 + fl * 0.62 then t1 else "Body"
			table.insert(pts, { 0, y + H * 0.42 - (i - 1) * H * 0.05, z, 0.8, 0, bone })
		end
		Parts.spikeRow(B, { points = pts, h = H * 0.22, pri = 3.2, col = "darker" })
	end
	if banded and detail >= 2 then
		local zs = { fc[3] - fr[3] * 0.3, fc[3] + fr[3] * 0.45, rc[3] + rr[3] * 0.35 }
		local function slice(c: { number }, r: { number }, z: number): { number }
			local u = math.clamp(1 - ((z - c[3]) / r[3]) ^ 2, 0.05, 1)
			local k = math.sqrt(u)
			return { r[1] * k * 1.05, r[2] * k * 1.05, L * 0.06 }
		end
		local rs = { slice(fc, fr, zs[1]), slice(fc, fr, zs[2]), slice(rc, rr, zs[3]) }
		bands(B, if detail >= 3 then 3 else 2, y, zs, rs, { "Body", "Body", t1 }, 2.7)
	end
	if glowDots and detail >= 2 then
		for i = 1, (if detail >= 3 then 3 else 2) do
			local z = fc[3] + fr[3] * (-0.1 + i * 0.35)
			local u = math.clamp(1 - ((z - fc[3]) / fr[3]) ^ 2, 0.05, 1)
			B:mball(H * 0.1, at(fr[1] * math.sqrt(u) * 0.93, fc[2] - fr[2] * 0.4, z), { col = "glow", mat = "neon", glow = true, pri = 3.4 + i * 0.1, role = "gem", name = "Photophore#", noCore = true })
		end
	end
	if has("spikes", "spiky", "fanned venomous spines") and detail >= 2 then
		local n = if detail >= 3 then 4 else 3
		for i = 1, n do
			local a = rad(-50 + (i - 1) * 100 / (n - 1))
			B:mlimb({ fr[1] * 0.7, fc[2] + fr[2] * 0.2, fc[3] + fr[3] * 0.2 }, { fr[1] * 0.7 + cos(a) * H * 0.75, fc[2] + fr[2] * 0.2 + sin(a) * H * 0.75, fc[3] + fr[3] * 0.6 }, 0.07,
				{ col = "secondary", mat = "hard", pri = 3.0 + i * 0.1, role = "horn", name = "Spine#", trail = i == n }, 0.05)
		end
	end
	if legs and has("tripod", "stilt") and detail >= 2 then
		B:limb({ 0, rc[2] - rr[2] * 0.8, rc[3] }, { 0, 0.05, rc[3] + L * 0.15 }, 0.1, { col = finCol, mat = "skin", bone = t1, pri = 2.4, role = "limb", name = "Stilt", mesh = false }, 0.1)
	end
	-- face
	local eyeD = H * P.eye * (if bigEyes then 1.35 else 1) * (if t.size == "Tiny" then 1.2 else 1)
	local fierce = kind == "deep" or fangs or (not t.cute and (t.power or 5) >= 7)
	local faceC, faceR = fc, fr
	if P.box then
		faceR = { W * 0.55, H * 0.5, fl * 0.55 }
	end
	if tubeEyes then
		-- barreleye: a clear dome over the head, two tube eyes looking up
		local dc = { 0, top - H * 0.05, fc[3] - fr[3] * 0.25 }
		B:ell(fr[1] * 1.5, fr[2] * 1.0, fr[3] * 1.1, at(dc[1], dc[2], dc[3]), { col = "glass", mat = "glass", tr = 0.55, pri = 2.2, role = "detail", name = "Dome", mesh = false, noCore = true })
		for _, sx in { 1, -1 } do
			B:limb({ sx * fr[1] * 0.25, top - H * 0.15, dc[3] }, { sx * fr[1] * 0.25, top + H * 0.25, dc[3] - fr[3] * 0.1 }, H * 0.16, { col = "glow", mat = "skin", pri = 1.5, role = "eye", name = if sx > 0 then "TubeEyeR" else "TubeEyeL", glow = true, noCore = true }, 0.1)
		end
		Face.build(B, { face = { kind = "ellipsoid", c = faceC, r = faceR }, bone = "Body", mood = mood(B), detail = detail, kind = "cute",
			spacing = faceR[1] * 0.6, y = -faceR[2] * 0.05, d = eyeD * 0.5, mouthY = -faceR[2] * 0.4, mouthW = W * 0.35, lidCol = "primary", noBrows = true })
	else
		Face.build(B, { face = { kind = "ellipsoid", c = faceC, r = faceR }, bone = "Body", mood = mood(B), detail = detail,
			kind = if fierce then "fierce" else "cute",
			spacing = faceR[1] * 0.64, y = faceR[2] * 0.2, d = eyeD, mouthY = -faceR[2] * 0.4, mouthW = W * (if mouthBig then 0.6 else 0.42),
			lidCol = "primary", forceMouth = mouthBig })
	end
	B:socket("mouth", at(0, fc[2] - fr[2] * 0.3, mz - 0.1), "Body")
	B:socket("core", at(0, y, fc[3]), "Body")
	B:setRig("gait", if legs then "sprawl" else "swim")
	local _ = id
	local _b = body
end

-- Flatfish (halibut, flounder): an oval disc lying flat a little above the ground, a fringe fin all round, both
-- eyes on the upper side near the head end, the tail fin upright at the back.
function SeaFish.flatfish(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local L, W, Hh = 3.0, 1.9, 0.5
	local y = 0.7
	B.boneIndex.Body.pos = { 0, y, 0 }
	local c = { 0, y, -0.15 }
	local r = { W * 0.5, Hh * 0.5, L * 0.42 }
	local disc = B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Disc", mesh = "s_aq_flatfish" })
	local members = {}
	if detail >= 1 then
		-- fringe: dorsal and anal fins run round both long edges
		local fa, fb = B:mell(W * 0.32, Hh * 0.22, L * 0.8, at(r[1] * 0.92, y, c[3] + L * 0.02), { col = "darker", mat = "skin", pri = 1.6, role = "fin", name = "Fringe#", mesh = false })
		table.insert(members, fa)
		table.insert(members, fb)
	end
	if detail >= 2 then
		table.insert(members, B:ell(r[1] * 1.6, Hh * 0.35, r[3] * 1.6, at(0, y - Hh * 0.18, c[3]), { col = "belly", mat = "skin", pri = 2.2, role = "detail", name = "Underside", mesh = false }))
	end
	B:sculpt(disc, "s_aq_flatfish", members)
	local t1 = B:bone("Tail1", "Body", 0, y, c[3] + r[3] * 0.7)
	B:addRig("tail", t1)
	B:ell(W * 0.36, Hh * 0.7, L * 0.22, at(0, y, c[3] + r[3] * 1.05), { col = "primary", mat = "skin", bone = t1, pri = 1.2, role = "body", name = "Peduncle", mesh = false })
	-- tail fin lies flat (the fish is on its side): a fan wide in x, thin in y
	B:ell(W * 0.62, 0.1, L * 0.22, at(0, y, c[3] + r[3] * 1.32), { col = "darker", mat = "skin", bone = t1, pri = 1.3, role = "fin", name = "TailFin", trail = true, mesh = "s_aq_flat_tail" })
	if detail >= 2 then
		B:ell(W * 0.32, 0.08, L * 0.12, at(r[1] * 0.75, y + Hh * 0.2, c[3] - r[3] * 0.35, 0, rad(-35), 0), { col = "secondary", mat = "skin", pri = 2.6, role = "fin", name = "PectoralR", mesh = "s_fin_side" })
	end
	-- face on the top side, near the head: a flat face frame looking up and forward
	local fz = c[3] - r[3] * 0.62
	local fy = y + r[2] * 0.75
	local cf = Geom.mul(at(0.12, fy, fz), at(0, 0, 0, rad(62), 0, 0))
	Face.build(B, { face = { kind = "flat", cf = cf, curve = 0.15 }, bone = "Body", mood = mood(B), detail = detail, kind = if (t.power or 5) >= 7 then "fierce" else "cute",
		spacing = W * 0.13, y = 0.06, d = W * 0.17, mouthY = -0.35, mouthW = W * 0.18, lidCol = "primary", noBrows = true })
	B:socket("mouth", at(0, y, c[3] - r[3]), "Body")
	B:socket("core", at(0, y, c[3]), "Body")
	B:setRig("gait", "swim")
end

-- Rays and skates: a raised body disc, two flapping wings (bones Wing#, flipper flap), a whip tail with a barb.
-- Sawfish and guitarfish keep a thicker shark-like tail with fins; eagle / cownose / mobula rays have a head
-- that pokes out in front.
function SeaFish.ray(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local has = SeaFish.reader(ctx)
	local guitar = has("guitarfish", "sawfish", "guitar")
	local round = has("round flat", "electric ray", "polka", "freshwater")
	local snouted = has("eagle ray", "cownose", "duck-like", "cow nose", "mobula", "manta", "bat ray")
	local span = if guitar then 2.6 elseif round then 3.2 else 4.8
	local L = if guitar then 2.6 elseif round then 2.6 else 2.4
	local y = 1.1
	B.boneIndex.Body.pos = { 0, y, 0 }
	local c = { 0, y, -0.2 }
	local r = { span * (if guitar then 0.24 else 0.2), 0.32, L * 0.42 }
	local body = B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Disc", mesh = "s_aq_ray_body" })
	local under
	if detail >= 2 then
		under = B:ell(r[1] * 1.7, r[2] * 1.1, r[3] * 1.7, at(0, y - r[2] * 0.4, c[3]), { col = "belly", mat = "skin", pri = 2.1, role = "detail", name = "Underside", mesh = false })
		B:sculpt(body, "s_aq_ray_body", { under })
	end
	-- wings: one thin ellipsoid per side, root inside the disc, on its own bone so it flaps
	local wr, wl = B:mirrorBone("Wing#", "Body", r[1] * 0.6, y, c[3])
	B:addRig("wings", { bone = wr, side = 1, flipper = true })
	B:addRig("wings", { bone = wl, side = -1, flipper = true })
	local ww = span * 0.5 - r[1] * 0.35
	local wing = if round then { ww * 1.0, 0.16, L * 0.8 } else { ww * 1.12, 0.14, L * (if guitar then 0.6 else 0.85) }
	local sweep = if round or guitar then 0 else rad(-14)
	B:mell(wing[1], wing[2], wing[3], at(r[1] * 0.45 + wing[1] * 0.4, y - 0.02, c[3] + L * 0.05, 0, sweep, rad(-4)), { col = "primary", mat = "skin", bone = "Wing#", pri = 1.1, role = "fin", name = "RayWing#",
		mesh = if round then "s_aq_ray_wing_round" else "s_aq_ray_wing", meshL = if round then "s_aq_ray_wing_round_l" else "s_aq_ray_wing_l" })
	-- head lobe / snout
	if snouted and detail >= 1 then
		local hc = { 0, y + 0.02, c[3] - r[3] * 0.95 }
		B:ell(r[1] * 1.0, r[2] * 1.3, r[3] * 0.45, at(hc[1], hc[2], hc[3]), { col = "primary", mat = "skin", pri = 1.4, role = "head", name = "HeadLobe", mesh = false })
		if has("mobula", "manta") and detail >= 2 then
			B:mell(0.18, 0.4, r[3] * 0.45, at(r[1] * 0.6, y, hc[3] - r[3] * 0.25, rad(10), 0, 0), { col = "primary", mat = "skin", pri = 2.6, role = "fin", name = "Horn#", mesh = false })
		end
	end
	if has("sawfish", "rostrum", "saw") then
		local bl = L * 0.7
		B:ell(r[1] * 0.35, 0.12, bl, at(0, y, c[3] - r[3] - bl * 0.42), { col = "secondary", mat = "hard", pri = 1.35, role = "horn", name = "Saw", mesh = false })
		if detail >= 2 then
			for i = 1, (if detail >= 3 then 4 else 3) do
				B:mwedge(0.05, 0.16, 0.14, at(r[1] * 0.2, y, c[3] - r[3] - bl * (0.05 + i * 0.2), 0, 0, rad(-90)), { col = "tooth", mat = "hard", pri = 3 + i * 0.1, role = "tooth" })
			end
		end
	end
	-- tail
	local t1 = B:bone("Tail1", "Body", 0, y, c[3] + r[3] * 0.8)
	local t2 = B:bone("Tail2", t1, 0, y, c[3] + r[3] * 0.8 + L * 0.5)
	B:addRig("tail", t1)
	B:addRig("tail", t2)
	local z1 = c[3] + r[3] * 0.75
	if guitar then
		-- shark-like rear: thick tail, two dorsal fins, a small caudal fin
		B:limb({ 0, y, z1 }, { 0, y + 0.05, z1 + L * 0.65 }, r[1] * 0.75, { col = "primary", mat = "skin", bone = t1, pri = 1.2, role = "body", name = "TailStock", depth = 0.38 }, 0.25)
		dorsal(B, "soft", t1, y + 0.12, z1 + L * 0.3, 0.35, L * 0.18, 0.08, "primary", 1.6)
		caudal(B, "fork", t2, y + 0.05, z1 + L * 0.68, 0.7, 0.6, 0.08, "primary", detail)
	else
		B:limb({ 0, y, z1 }, { 0, y + 0.05, z1 + L * 0.7 }, 0.2, { col = "primary", mat = "skin", bone = t1, pri = 1.3, role = "tail", name = "Whip" }, 0.15)
		B:limb({ 0, y + 0.05, z1 + L * 0.7 }, { 0, y + 0.12, z1 + L * 1.4 }, 0.1, { col = "darker", mat = "skin", bone = t2, pri = 1.6, role = "tail", name = "WhipTip", trail = true }, 0.15)
		if detail >= 2 and has("barb", "stingray", "sting") then
			B:wedge(0.06, 0.2, 0.35, at(0, y + 0.14, z1 + L * 0.62, rad(15), 0, 0), { col = "horn", mat = "hard", bone = t1, pri = 3.2, role = "spike", name = "Barb" })
		end
	end
	-- face: eyes up on the front of the disc, mouth under
	local fierce = (t.power or 5) >= 7 and not t.cute
	Face.build(B, { face = { kind = "ellipsoid", c = { c[1], c[2] + r[2] * 0.25, c[3] }, r = r }, bone = "Body", mood = mood(B), detail = detail, kind = if fierce then "fierce" else "cute",
		spacing = r[1] * 0.42, y = r[2] * 0.45, d = 0.42, mouthY = -r[2] * 0.6, mouthW = r[1] * 0.5, lidCol = "primary", noBrows = true })
	if has("spot", "polka") and detail >= 3 then
		for i, p in { { 0.35, 0.1 }, { -0.4, 0.3 }, { 0.15, 0.55 } } do
			B:ell(0.32, 0.12, 0.32, at(r[1] * p[1], y + r[2] * 0.85, c[3] + r[3] * (p[2] - 0.1)), { col = "secondary", mat = "skin", pri = 3.6 + i * 0.1, role = "detail", name = "Spot", mesh = false })
		end
	end
	B:socket("mouth", at(0, y - r[2] * 0.5, c[3] - r[3] * 0.7), "Body")
	B:socket("core", at(0, y, c[3]), "Body")
	B:setRig("gait", "swim")
end

-- Seahorses, sea dragons, pipefish: upright, a horse-like head on a bent neck, a ridged trunk, a tail that curls
-- forward under the body; pipefish are the straight version.
function SeaFish.seahorse(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local has = SeaFish.reader(ctx)
	local straight = has("pipefish", "stick", "shrimpfish", "head-down")
	local leafy = has("leafy", "frond", "seaweed", "ornate")
	local y = 1.1
	B.boneIndex.Body.pos = { 0, y + 1.2, 0 }
	-- trunk: belly bulging forward
	local tc = { 0, y + 1.25, 0.05 }
	local tr = { 0.5, 0.95, 0.55 }
	if straight then
		tr = { 0.32, 1.25, 0.32 }
	end
	B:ell(tr[1] * 2, tr[2] * 2, tr[3] * 2, at(tc[1], tc[2], tc[3], rad(-8), 0, 0), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Trunk", mesh = if straight then false else "s_aq_seahorse" })
	-- head on a short neck, snout tube forward
	local hb = B:bone("Head", "Body", 0, tc[2] + tr[2] * 0.8, tc[3])
	B:setRig("head", hb)
	local hc = { 0, tc[2] + tr[2] * 1.05, tc[3] - 0.15 }
	local hr = { 0.36, 0.42, 0.42 }
	B:ell(hr[1] * 2, hr[2] * 2, hr[3] * 2, at(hc[1], hc[2], hc[3]), { col = "primary", mat = "skin", bone = hb, pri = 1.1, role = "head", name = "Head", mesh = false })
	B:limb({ 0, hc[2] - 0.05, hc[3] - hr[3] * 0.5 }, { 0, hc[2] - 0.15, hc[3] - hr[3] - 0.65 }, 0.2, { col = "primary", mat = "skin", bone = hb, pri = 1.3, role = "snout", name = "SnoutTube", mesh = false }, 0.1)
	if detail >= 2 and not straight then
		-- coronet
		B:limb({ 0, hc[2] + hr[2] * 0.6, hc[3] + 0.1 }, { 0, hc[2] + hr[2] * 1.3, hc[3] + 0.25 }, 0.16, { col = "secondary", mat = "skin", bone = hb, pri = 2.5, role = "horn", name = "Coronet" }, 0.1)
	end
	Face.build(B, { face = { kind = "ellipsoid", c = hc, r = hr }, bone = hb, mood = mood(B), detail = detail, kind = if t.cute or t.size == "Tiny" then "cute" else "fierce",
		spacing = hr[1] * 0.68, y = hr[2] * 0.15, d = 0.3, mouthW = nil, lidCol = "primary", noMouth = true })
	-- tail: a chain of shrinking segments curling forward
	local parent = "Body"
	local x, yy, z = 0, tc[2] - tr[2] * 0.75, tc[3] + 0.1
	local w = tr[1] * 1.3
	local n = if detail <= 0 then 2 elseif detail == 1 then 3 else 4
	for i = 1, n do
		local bn = B:bone("Tail" .. i, parent, x, yy, z)
		B:addRig("tail", bn)
		-- down and a little back first, then curling forward under the belly
		local a = if straight then 0 else rad(-30) + (i - 1) * rad(if n <= 2 then 110 else 70)
		local seg = if straight then 0.55 else 0.5
		local ex, ey, ez = x, yy - cos(a) * seg, z - sin(a) * seg * (if straight then 0 else 1)
		B:limb({ x, yy, z }, { ex, ey, ez }, w, { col = "primary", mat = "skin", bone = bn, pri = 1.2 + i * 0.2, role = "tail", trail = i == n }, 0.35)
		x, yy, z = ex, ey, ez
		parent = bn
		w *= 0.72
	end
	-- dorsal fin on the back and pectoral fins behind the head
	fin(B, "Dorsal", "Body", 0.08, 0.55, 0.42, at(0, tc[2] - 0.1, tc[3] + tr[3] * 0.95, 0, 0, 0), "secondary", 1.6, "s_aq_dorsal", { trail = true })
	if detail >= 2 then
		B:mell(0.32, 0.3, 0.08, at(hr[1] * 0.85, hc[2] - 0.15, hc[3] + 0.3, 0, rad(-20), 0), { col = "secondary", mat = "skin", bone = hb, pri = 2.6, role = "fin", name = "Pectoral#", mesh = false })
	end
	if leafy and detail >= 2 then
		-- leafy appendages: frond fins along the trunk and tail
		for i, p in { { tr[1] * 0.8, tc[2] + 0.3, tc[3] }, { tr[1] * 0.6, tc[2] - 0.5, tc[3] + 0.2 } } do
			B:mell(0.55, 0.08, 0.32, at(p[1] + 0.2, p[2], p[3], rad(20), rad(-20), rad(-30 - i * 15)), { col = "secondary", mat = "leaf", pri = 2.8 + i * 0.2, role = "fin", name = "Frond#", trail = true })
		end
	elseif detail >= 3 then
		-- ridged rings across the trunk
		for i = 1, 2 do
			local ry = tc[2] + tr[2] * (0.35 - i * 0.4)
			B:ell(tr[1] * 2.06, 0.12, tr[3] * 2.02, at(0, ry, tc[3]), { col = "darker", mat = "skin", pri = 3.6 + i * 0.1, role = "detail", name = "Ring", mesh = false })
		end
	end
	B:socket("mouth", at(0, hc[2] - 0.15, hc[3] - hr[3] - 0.7), hb)
	B:socket("core", at(0, tc[2], tc[3]), "Body")
	B:setRig("gait", "float")
end

return SeaFish
