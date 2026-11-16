--!strict
-- Accents: the modifier stage (DESIGN §8). result.visual.accents ids come from modifiers/materials ("angry" ->
-- scowl + steam, "pirate" -> piratehat + eyepatch, "robotic" -> bolts + visor). Each id is a registry entry that
-- adds geometry on anchors found in the built parts (eyes, head, body), re-tints the build, and/or requests a
-- looping attached effect (Effects.play id). Unknown ids are a no-op. Runs after the material stage, so hats and
-- props keep their own colours on a spaghetti dragon. Pure.
--
-- Face accents (scowl, smile, tongue, snore...) pick the mood the face is built with when the result's own mood is
-- Neutral (see Accents.moodFor), and add the bits a mood cannot (tears, sweat drop, drool).

local Geom = require(script.Parent.Geom)
local Palette = require(script.Parent.Palette)
local Props = require(script.Parent.Props)
local Parts = require(script.Parent.Parts)
local Face = require(script.Parent.Face)

local at = Geom.at
local rad = math.rad

local Accents = {}

-- Accent -> face mood (only when the result's mood is Neutral).
local MOOD: { [string]: string } = {
	scowl = "Angry", frown = "Sad", smile = "Happy", grin = "Hyper", smirk = "Smug", tongue = "Hungry", drool = "Hungry",
	snore = "Sleepy", sweat = "Scared", tears = "Sad", blush = "Cute", question = "Confused",
}

-- Accent -> looping attached effect id (Effects catalogue); `at` = "head" | "body" | "mouth".
local EFFECT: { [string]: { string } } = {
	steam = { "anger_steam", "head" }, snore = { "snore", "head" }, sweat = { "sweat_drops", "head" }, sparkle = { "sparkle", "body" },
	glitter = { "glitter", "body" }, stars = { "stars", "head" }, hearts = { "hearts", "head" }, notes = { "music_notes", "head" },
	question = { "question_marks", "head" }, sparks = { "sparks", "body" }, flames = { "embers", "body" }, frost = { "frost", "body" },
	drip = { "drip_sauce", "body" }, slime = { "goo_drip", "body" }, bubbles = { "bubbles", "body" }, rainbow = { "rainbow_trail", "body" },
	lightning = { "zap", "body" }, leaves = { "leaves", "body" }, petals = { "petals", "body" }, glow = { "halo_glow", "body" },
	disco = { "glitter", "body" }, pixel = { "glitch", "body" }, cursed = { "smoke", "body" }, ghostly = { "halo_glow", "body" },
	thrusters = { "thruster", "back" }, jetpack = { "thruster", "back" }, halo = { "halo_glow", "head" }, drool = { "goo_drip", "mouth" },
	tears = { "water_drip", "head" }, zombie = { "flies", "body" }, laser = { "sparks", "head" },
}

-- Extra parts each geometry accent tends to add (for the budget reservation).
local COST: { [string]: number } = {
	crown = 3, partyhat = 2, tophat = 2, piratehat = 3, wizardhat = 3, chefhat = 2, halo = 1, horns = 2, wings = 2, spikes = 3,
	fangs = 2, extrahead = 3, extraheads = 5, propeller = 3, jetpack = 3, thrusters = 2, laser = 2, cannon = 2, armour = 2, shield = 2,
	eyepatch = 2, monocle = 1, sunglasses = 3, visor = 1, mustache = 2, bowtie = 3, crack = 2, bandage = 1, stitches = 3, bolts = 2,
	gears = 2, tears = 2, sweat = 1, drool = 1, blush = 2,
}

function Accents.moodFor(accents: { string }?): string?
	for _, a in accents or {} do
		if MOOD[a] then
			return MOOD[a]
		end
	end
	return nil
end

function Accents.reserve(accents: { string }?): number
	local n = 0
	for _, a in accents or {} do
		n += COST[a] or 0
	end
	return math.min(n, 8)
end

function Accents.known(id: string): boolean
	return MOOD[id] ~= nil or EFFECT[id] ~= nil or Accents.Registry[id] ~= nil
end

-- ------------------------------------------------------------------ anchors

local function aabb(p: any): ({ number }, { number })
	local cf, s = p.cf, p.size
	local hx, hy, hz = s[1] / 2, s[2] / 2, s[3] / 2
	local ex = math.abs(cf[4]) * hx + math.abs(cf[5]) * hy + math.abs(cf[6]) * hz
	local ey = math.abs(cf[7]) * hx + math.abs(cf[8]) * hy + math.abs(cf[9]) * hz
	local ez = math.abs(cf[10]) * hx + math.abs(cf[11]) * hy + math.abs(cf[12]) * hz
	return { cf[1] - ex, cf[2] - ey, cf[3] - ez }, { cf[1] + ex, cf[2] + ey, cf[3] + ez }
end

local HEADISH = { head = true, body = true, torso = true, snout = true, core = true, shell = true, roof = true, blade = true }

local function anchors(B: any): any
	local A: any = {}
	local eyes = {}
	for _, p in B.parts do
		if p.role == "eye" and not p.accent then
			table.insert(eyes, p)
		end
	end
	-- the biggest body mass
	local body, bodyVol = nil, 0
	for _, p in B.parts do
		if HEADISH[p.role] and not p.accent then
			local v = p.size[1] * p.size[2] * p.size[3]
			if v > bodyVol then
				body, bodyVol = p, v
			end
		end
	end
	if body == nil then
		body = B.parts[1]
	end
	A.body = body
	if body then
		local mn, mx = aabb(body)
		A.bodyMin, A.bodyMax = mn, mx
		A.bodyC = { body.cf[1], body.cf[2], body.cf[3] }
	else
		A.bodyMin, A.bodyMax, A.bodyC = { -0.5, 0, -0.5 }, { 0.5, 1, 0.5 }, { 0, 0.5, 0 }
	end
	if #eyes > 0 then
		local sx, sy, sz, minX, maxX, es = 0, 0, 0, math.huge, -math.huge, 0
		for _, e in eyes do
			sx += e.cf[1]
			sy += e.cf[2]
			sz += e.cf[3]
			minX = math.min(minX, e.cf[1])
			maxX = math.max(maxX, e.cf[1])
			es = math.max(es, e.size[1], e.size[2])
		end
		A.face = { sx / #eyes, sy / #eyes, sz / #eyes }
		A.eyeR = { maxX, A.face[2], A.face[3] }
		A.eyeL = { minX, A.face[2], A.face[3] }
		A.eyeSize = es
		A.spacing = math.max(maxX - minX, es * 1.4)
		A.headBone = eyes[1].bone
		-- head part: the head-ish mass nearest the eyes that is clearly bigger than an eye
		local best, bestD = nil, math.huge
		for _, p in B.parts do
			if HEADISH[p.role] and not p.accent and math.min(p.size[1], p.size[2], p.size[3]) > es * 1.2 then
				local d = math.sqrt((p.cf[1] - A.face[1]) ^ 2 + (p.cf[2] - A.face[2]) ^ 2 + (p.cf[3] - A.face[3]) ^ 2) / math.max(p.size[1], p.size[2], p.size[3])
				if d < bestD then
					best, bestD = p, d
				end
			end
		end
		A.head = best or body
	else
		A.head = body
		A.headBone = body and body.bone or "Body"
		local mn, mx = A.bodyMin, A.bodyMax
		A.face = { (mn[1] + mx[1]) / 2, mn[2] + (mx[2] - mn[2]) * 0.6, mn[3] }
		A.eyeSize = (mx[1] - mn[1]) * 0.15
		A.spacing = (mx[1] - mn[1]) * 0.35
		A.eyeR = { A.face[1] + A.spacing / 2, A.face[2], A.face[3] }
		A.eyeL = { A.face[1] - A.spacing / 2, A.face[2], A.face[3] }
	end
	local hmn, hmx = aabb(A.head)
	A.headMin, A.headMax = hmn, hmx
	A.headC = { A.head.cf[1], A.head.cf[2], A.head.cf[3] }
	A.headW = math.max(0.2, math.min(hmx[1] - hmn[1], hmx[3] - hmn[3]))
	A.headBone = A.headBone or A.head.bone
	-- the top of the head, slightly sunk into the curve so hats sit on it
	A.top = { A.headC[1], hmx[2] - (hmx[2] - hmn[2]) * 0.08, A.headC[3] }
	A.mouth = B.sockets.mouth and { B.sockets.mouth[1], B.sockets.mouth[2], B.sockets.mouth[3] } or { A.face[1], A.face[2] - A.spacing * 0.6, A.face[3] - A.eyeSize * 0.1 }
	A.back = { A.bodyC[1], A.bodyC[2] + (A.bodyMax[2] - A.bodyMin[2]) * 0.2, A.bodyMax[3] }
	return A
end

-- ------------------------------------------------------------------ registry

local function mark(B: any, from: number)
	for i = from + 1, #B.parts do
		B.parts[i].accent = true
	end
end

local R: { [string]: (B: any, A: any, t: any) -> () } = {}
Accents.Registry = R

local function hat(kind: string, scale: number?)
	return function(B: any, A: any, _t: any)
		Props.hat(B, kind, A.top, A.headW * (scale or 0.62), A.headBone, { col = if kind == "party" then "red" else nil })
	end
end
R.crown = hat("crown", 0.7)
R.partyhat = hat("party")
R.tophat = hat("top")
R.piratehat = hat("pirate")
R.wizardhat = hat("wizard")
R.chefhat = hat("chef")
R.halo = function(B, A, _t)
	Props.hat(B, "halo", { A.top[1], A.top[2] + A.headW * 0.25, A.top[3] }, A.headW * 0.6, A.headBone)
end

R.horns = function(B, A, _t)
	Parts.horns(B, { bone = A.headBone, x = A.headW * 0.28, y = A.top[2] - A.headW * 0.05, z = A.headC[3], len = A.headW * 0.55, w = A.headW * 0.16, kind = "curved", segs = 2, pri = 1.5, col = "horn" })
end

R.wings = function(B, A, _t)
	local mn, mx = A.bodyMin, A.bodyMax
	local w = mx[1] - mn[1]
	Parts.wings(B, { x = w * 0.3, y = mx[2] - (mx[2] - mn[2]) * 0.15, z = A.bodyC[3], span = math.max(w, mx[2] - mn[2]) * 1.1, kind = "feather", feathers = 2, pri = 1.5, detail = 1 })
end

R.spikes = function(B, A, _t)
	local mn, mx = A.bodyMin, A.bodyMax
	local pts = {}
	for i = 1, 3 do
		local z = mn[3] + (mx[3] - mn[3]) * (0.3 + (i - 1) * 0.2)
		table.insert(pts, { A.bodyC[1], mx[2] - (mx[2] - mn[2]) * 0.12, z, 1 - (i - 2) ^ 2 * 0.25, 0, A.body and A.body.bone })
	end
	Parts.spikeRow(B, { points = pts, h = (mx[2] - mn[2]) * 0.28, col = "accent", pri = 1.6 })
end

R.fangs = function(B, A, _t)
	local s = A.spacing
	for side = -1, 1, 2 do
		B:wedge(s * 0.12, s * 0.28, s * 0.12, at(A.mouth[1] + side * s * 0.18, A.mouth[2] - s * 0.12, A.mouth[3] - s * 0.04, math.pi, 0, 0), { col = "tooth", mat = "hard", bone = A.headBone, pri = 1.7, role = "tooth", name = "Fang", noCore = true })
	end
end

local function extraHead(B: any, A: any, side: number, k: number)
	local s = A.headW * 0.85
	local c = { A.headC[1] + side * A.headW * (0.75 + k * 0.25), A.headC[2] + A.headW * (0.05 + k * 0.08), A.headC[3] + A.headW * 0.05 }
	B:ell(s, s * 0.95, s, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", bone = A.headBone, pri = 1.45 + k * 0.02, role = "head", name = "ExtraHead" })
	Face.build(B, { face = { kind = "ellipsoid", c = c, r = { s / 2, s * 0.95 / 2, s / 2 } }, bone = A.headBone, mood = B.ctx.result.mood or "Neutral", detail = math.min(B.ctx.detail or 1, 1), kind = "cute", spacing = 0.45, y = 0.1, pri = 1.5 + k * 0.02 })
end
R.extrahead = function(B, A, _t)
	extraHead(B, A, 1, 0)
end
R.extraheads = function(B, A, _t)
	extraHead(B, A, 1, 0)
	extraHead(B, A, -1, 1)
end

R.propeller = function(B, A, _t)
	local s = A.headW * 0.5
	local x, y, z = A.top[1], A.top[2], A.top[3]
	B:ell(s * 0.9, s * 0.45, s * 0.9, at(x, y + s * 0.05, z), { col = "secondary", mat = "plastic", bone = A.headBone, pri = 1.5, role = "hat", name = "PropCap" })
	B:cyl(s * 0.35, s * 0.12, at(x, y + s * 0.3, z, 0, 0, rad(90)), { col = "dark", mat = "metal", bone = A.headBone, pri = 1.55, role = "hat", name = "PropHub" })
	local pb = B:bone("Propeller", A.headBone, x, y + s * 0.5, z)
	B:ell(s * 2.2, s * 0.06, s * 0.3, at(x, y + s * 0.5, z, 0, rad(20), rad(4)), { col = "red", mat = "plastic", bone = pb, pri = 1.6, role = "rotor", name = "PropBlade" })
	B:addRig("rotors", { bone = pb, axis = "Y", speed = 14 })
end

R.jetpack = function(B, A, _t)
	local mn, mx = A.bodyMin, A.bodyMax
	local h = (mx[2] - mn[2]) * 0.45
	local w = h * 0.32
	for side = -1, 1, 2 do
		B:cyl(h, w, at(A.bodyC[1] + side * w * 0.62, A.bodyC[2] + h * 0.15, mx[3] + w * 0.32, 0, 0, rad(90)), { col = "metal", mat = "metal", bone = A.body.bone, pri = 1.55, role = "detail", name = "Jet" })
	end
	B:socket("exhaust", at(A.bodyC[1], A.bodyC[2] - h * 0.4, mx[3] + w * 0.32), A.body.bone)
end

R.thrusters = function(B, A, _t)
	local mn, mx = A.bodyMin, A.bodyMax
	local w = (mx[2] - mn[2]) * 0.22
	B:mcyl(w * 1.3, w, at((mx[1] - mn[1]) * 0.22, A.bodyC[2], mx[3] + w * 0.4), { col = "gunmetal", mat = "metal", bone = A.body.bone, pri = 1.55, role = "detail", name = "Thruster#" })
	B:mball(w * 0.72, at((mx[1] - mn[1]) * 0.22, A.bodyC[2], mx[3] + w * 1.02), { col = "flame", mat = "neon", glow = true, bone = A.body.bone, pri = 2.2, role = "glow", name = "ThrustGlow#", noCore = true })
	B:socket("exhaust", at(A.bodyC[1], A.bodyC[2], mx[3] + w), A.body.bone)
end

R.laser = function(B, A, _t)
	local s = A.headW
	local x, y, z = A.headC[1] + s * 0.42, A.top[2] - s * 0.05, A.headC[3]
	B:limb({ x, y, z + s * 0.1 }, { x, y + s * 0.05, z - s * 0.45 }, s * 0.16, { col = "gunmetal", mat = "metal", bone = A.headBone, pri = 1.55, role = "cannon", name = "Laser" }, 0.1)
	B:ball(s * 0.13, at(x, y + s * 0.05, z - s * 0.5), { col = "red", mat = "neon", glow = true, bone = A.headBone, pri = 1.9, role = "glow", name = "LaserTip", noCore = true })
	B:socket("muzzle", at(x, y + s * 0.05, z - s * 0.55), A.headBone)
end

R.cannon = function(B, A, _t)
	local mn, mx = A.bodyMin, A.bodyMax
	local w = (mx[1] - mn[1]) * 0.18
	local y = mx[2] + w * 0.1
	B:limb({ A.bodyC[1], y, A.bodyC[3] + w }, { A.bodyC[1], y + w * 0.5, A.bodyC[3] - w * 3 }, w, { col = "gunmetal", mat = "metal", bone = A.body.bone, pri = 1.5, role = "cannon", name = "BackCannon" }, 0.05)
	B:socket("muzzle", at(A.bodyC[1], y + w * 0.5, A.bodyC[3] - w * 3.2), A.body.bone)
end

R.armour = function(B, A, _t)
	local p = A.body
	if p == nil then
		return
	end
	local s = p.size
	B:ell(s[1] * 1.06, s[2] * 0.62, s[3] * 0.7, Geom.offset(p.cf, 0, s[2] * 0.12, 0), { col = "steel", mat = "metal", bone = p.bone, pri = 1.5, role = "armour", name = "ArmourPlate" })
	B:ell(s[1] * 0.5, s[2] * 0.2, s[3] * 0.4, Geom.offset(p.cf, 0, s[2] * 0.42, 0), { col = "gold", mat = "metal", bone = p.bone, pri = 2.2, role = "armour", name = "ArmourTrim" })
end

R.shield = function(B, A, _t)
	local mn, mx = A.bodyMin, A.bodyMax
	local s = (mx[2] - mn[2]) * 0.16
	Props.held(B, "shield", { mn[1] - s * 0.6, A.bodyC[2], A.bodyC[3] - s }, s, A.body.bone)
end

R.eyepatch = function(B, A, _t)
	local e = A.eyeR
	local d = A.eyeSize * 1.35
	B:ell(d, d * 0.95, d * 0.45, at(e[1], e[2], e[3] - A.eyeSize * 0.3), { col = "black", mat = "cloth", bone = A.headBone, pri = 1.45, role = "detail", name = "Eyepatch", noCore = true })
	B:ell(A.headW * 1.04, A.eyeSize * 0.16, A.headW * 1.04, at(A.headC[1], e[2] + A.eyeSize * 0.45, A.headC[3], 0, 0, rad(-14)), { col = "black", mat = "cloth", bone = A.headBone, pri = 2.4, role = "detail", name = "PatchStrap", noCore = true })
end

R.monocle = function(B, A, _t)
	local e = A.eyeL
	local d = A.eyeSize * 1.3
	B:cyl(d * 0.12, d, at(e[1], e[2], e[3] - A.eyeSize * 0.42, 0, rad(90), 0), { col = "gold", mat = "metal", bone = A.headBone, pri = 1.5, role = "detail", name = "Monocle", noCore = true, tr = 0 })
end

R.sunglasses = function(B, A, _t)
	local d = A.eyeSize * 1.25
	for _, e in { A.eyeR, A.eyeL } do
		B:ell(d * 1.1, d * 0.8, d * 0.35, at(e[1], e[2], e[3] - A.eyeSize * 0.4), { col = "black", mat = "glass", bone = A.headBone, pri = 1.45, role = "detail", name = "Lens", noCore = true, pair = "sunglasses" })
	end
	B:ell(A.spacing * 0.6, d * 0.14, d * 0.18, at(A.face[1], A.face[2] + d * 0.15, A.face[3] - A.eyeSize * 0.45), { col = "black", mat = "metal", bone = A.headBone, pri = 1.5, role = "detail", name = "Bridge", noCore = true, needs = "sunglasses" })
end

R.visor = function(B, A, _t)
	local d = A.eyeSize
	B:ell(A.spacing + d * 1.6, d * 0.8, d * 0.5, at(A.face[1], A.face[2], A.face[3] - d * 0.38), { col = "eyeGlow", mat = "neon", glow = true, bone = A.headBone, pri = 1.45, role = "detail", name = "Visor", noCore = true })
end

R.mustache = function(B, A, _t)
	local s = A.spacing
	local y = (A.face[2] + A.mouth[2]) / 2
	local z = math.min(A.face[3], A.mouth[3]) - A.eyeSize * 0.15
	B:mell(s * 0.55, s * 0.16, s * 0.2, at(A.face[1] + s * 0.24, y, z, 0, rad(-12), rad(-12)), { col = "hair", mat = "fur", bone = A.headBone, pri = 1.5, role = "detail", name = "Mustache#", noCore = true })
end

R.bowtie = function(B, A, _t)
	local s = A.spacing * 0.6
	local x, y, z = A.headC[1], A.headMin[2] + s * 0.1, A.headMin[3] + (A.headMax[3] - A.headMin[3]) * 0.22
	B:mwedge(s * 0.5, s * 0.55, s * 0.18, at(x + s * 0.3, y, z, 0, 0, rad(90)), { col = "red", mat = "cloth", bone = A.headBone, pri = 1.5, role = "detail", name = "Bow#", noCore = true })
	B:ball(s * 0.26, at(x, y, z - s * 0.02), { col = "red", mat = "cloth", bone = A.headBone, pri = 1.55, role = "detail", name = "BowKnot", noCore = true })
end

R.crack = function(B, A, _t)
	local p = A.body
	if p == nil then
		return
	end
	local s = p.size
	for i = 1, 2 do
		local f = Geom.offset(p.cf, s[1] * (0.12 - i * 0.1), s[2] * (0.2 - i * 0.18), -s[3] * 0.47)
		B:block(s[1] * 0.04, s[2] * 0.3, s[3] * 0.08, Geom.mul(f, at(0, 0, 0, 0, 0, rad(if i == 1 then 28 else -24))), { col = "black", mat = "hard", bone = p.bone, pri = 1.6 + i * 0.05, role = "detail", name = "Crack" .. i, noCore = true })
	end
end

R.bandage = function(B, A, _t)
	local w = A.headW
	B:ell(w * 1.05, w * 0.2, w * 1.05, at(A.headC[1], A.top[2] - w * 0.18, A.headC[3], 0, 0, rad(10)), { col = "white", mat = "cloth", bone = A.headBone, pri = 1.5, role = "detail", name = "Bandage", noCore = true })
end

R.stitches = function(B, A, _t)
	local s = A.spacing
	local x, y, z = A.headC[1] + A.headW * 0.18, A.top[2] - A.headW * 0.12, A.headMin[3] + (A.headMax[3] - A.headMin[3]) * 0.2
	B:block(s * 0.05, s * 0.6, s * 0.05, at(x, y - s * 0.1, z, rad(-30), 0, 0), { col = "black", mat = "cloth", bone = A.headBone, pri = 1.6, role = "detail", name = "Stitch", noCore = true })
	for i = 1, 2 do
		B:block(s * 0.32, s * 0.05, s * 0.05, at(x, y - s * 0.1 + (i - 1.5) * s * 0.28, z - s * 0.01 * i, rad(-30), 0, 0), { col = "black", mat = "cloth", bone = A.headBone, pri = 1.65 + i * 0.05, role = "detail", name = "StitchX" .. i, noCore = true })
	end
end

R.bolts = function(B, A, _t)
	local w = A.headW
	B:mcyl(w * 0.3, w * 0.16, at(A.headC[1] + (A.headMax[1] - A.headMin[1]) * 0.48, A.headC[2] - w * 0.08, A.headC[3]), { col = "steel", mat = "metal", bone = A.headBone, pri = 1.5, role = "detail", name = "Bolt#", noCore = true })
end

R.gears = function(B, A, _t)
	local p = A.body
	if p == nil then
		return
	end
	local mn, mx = A.bodyMin, A.bodyMax
	local d = (mx[2] - mn[2]) * 0.38
	B:cyl(d * 0.16, d, at(mx[1] + d * 0.02, A.bodyC[2], A.bodyC[3]), { col = "gold", mat = "metal", bone = p.bone, pri = 1.55, role = "detail", name = "Gear", noCore = true })
	B:cyl(d * 0.2, d * 0.35, at(mx[1] + d * 0.09, A.bodyC[2], A.bodyC[3]), { col = "gunmetal", mat = "metal", bone = p.bone, pri = 1.6, role = "detail", name = "GearHub", noCore = true })
end

R.tears = function(B, A, _t)
	local d = A.eyeSize * 0.32
	for _, e in { A.eyeR, A.eyeL } do
		B:ell(d, d * 1.5, d * 0.8, at(e[1], e[2] - A.eyeSize * 0.75, e[3] - d * 0.2), { col = { 0.45, 0.75, 1 }, mat = "glass", tr = 0.15, bone = A.headBone, pri = 1.6, role = "detail", name = "Tear", noCore = true, pair = "tears" })
	end
end

R.sweat = function(B, A, _t)
	local d = A.eyeSize * 0.45
	B:ell(d, d * 1.5, d * 0.8, at(A.headMax[1] - A.headW * 0.08, A.top[2] - A.headW * 0.15, A.face[3] + A.headW * 0.05), { col = { 0.55, 0.82, 1 }, mat = "glass", tr = 0.1, bone = A.headBone, pri = 1.6, role = "detail", name = "SweatDrop", noCore = true })
end

R.drool = function(B, A, _t)
	local d = A.spacing * 0.12
	B:ell(d, d * 2.2, d, at(A.mouth[1] + A.spacing * 0.15, A.mouth[2] - d * 1.2, A.mouth[3] - d * 0.2), { col = { 0.75, 0.9, 1 }, mat = "glass", tr = 0.25, bone = A.headBone, pri = 1.7, role = "detail", name = "Drool", noCore = true })
end

R.blush = function(B, A, _t)
	for _, p in B.parts do
		if p.role == "blush" then
			return
		end
	end
	local d = A.eyeSize * 0.7
	for _, e in { A.eyeR, A.eyeL } do
		local side = if e[1] >= A.face[1] then 1 else -1
		B:ell(d, d * 0.5, d * 0.35, at(e[1] + side * d * 0.25, e[2] - A.eyeSize * 0.7, e[3] + d * 0.05), { col = "blush", mat = "skin", bone = A.headBone, pri = 1.8, role = "blush", name = "Blush", noCore = true, pair = "blushAccent" })
	end
end

-- re-tints (no parts)
local function retint(B: any, fn: (p: any) -> ())
	for _, p in B.parts do
		if p.role ~= "eye" and p.role ~= "pupil" and p.role ~= "shine" and p.role ~= "mouth" and not p.accent then
			fn(p)
		end
	end
end
R.zombie = function(B, _A, _t)
	retint(B, function(p)
		if p.col == "skin" or p.col == "primary" or p.col == "light" then
			p.col = { 0.48, 0.66, 0.42 }
			p.mcol = nil
		end
	end)
end
R.skeleton = function(B, _A, _t)
	retint(B, function(p)
		if p.role ~= "hat" and p.role ~= "held" then
			p.col = { 0.93, 0.9, 0.82 }
			p.mcol = nil
		end
	end)
end
R.ghostly = function(B, _A, _t)
	retint(B, function(p)
		p.tr = math.max(p.tr or 0, 0.45)
	end)
end
R.cursed = function(B, _A, _t)
	retint(B, function(p)
		local c = p.mcol or (if type(p.col) == "table" then p.col else nil)
		p.cursed = true
		if c then
			p.mcol = Palette.lerp(c, { 0.35, 0.12, 0.45 }, 0.45)
		end
	end)
end
R.rainbow = function(B, _A, _t)
	local i = 0
	retint(B, function(p)
		if p.role == "body" or p.role == "limb" or p.role == "tail" or p.role == "wing" or p.role == "strand" or p.role == "head" then
			i += 1
			p.mcol = Palette.fromHsv(((i * 0.13) % 1), 0.75, 0.95)
		end
	end)
end
R.glow = function(B, _A, _t)
	for _, p in B.parts do
		if p.role == "eye" and p.col == "eyeWhite" then
			p.col = "eyeGlow"
			p.glow = true
		end
	end
end
R.disco = function(B, _A, _t)
	retint(B, function(p)
		if p.role == "body" or p.role == "head" then
			p.mrbx = "Foil"
			p.mcol = { 0.85, 0.87, 0.92 }
		end
	end)
end
R.pixel = function(B, _A, _t)
	-- voxel look: round masses become blocks, axis-aligned to their own frame
	retint(B, function(p)
		if p.shape == "Ellipsoid" and (p.role == "body" or p.role == "head" or p.role == "limb" or p.role == "tail") then
			p.shape = "Block"
			p.size = { p.size[1] * 0.84, p.size[2] * 0.84, p.size[3] * 0.84 }
		end
	end)
end

-- ------------------------------------------------------------------ apply

-- Adds accent geometry/tints to B and returns the effect requests { { id, at } }. Unknown ids are skipped.
function Accents.apply(B: any, accents: { string }?, t: any): { any }
	local effects = {}
	if accents == nil or #accents == 0 or #B.parts == 0 then
		return effects
	end
	local A = anchors(B)
	local seen: { [string]: boolean } = {}
	for _, id in accents do
		if not seen[id] then
			seen[id] = true
			local fn = R[id]
			if fn then
				local before = #B.parts
				local ok = pcall(fn, B, A, t)
				if not ok then
					-- a broken accent must never break the summon: drop whatever it half-built
					for i = #B.parts, before + 1, -1 do
						table.remove(B.parts, i)
					end
				end
				mark(B, before)
			end
			local e = EFFECT[id]
			if e then
				table.insert(effects, { id = e[1], at = e[2], accent = id })
			end
		end
	end
	return effects
end

Accents._anchors = anchors

return Accents
