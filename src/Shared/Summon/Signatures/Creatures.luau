--!strict
-- Hand-built creature signatures: dragon, shark, t rex, phoenix, kraken, golem, cat, dog, bee, octopus, unicorn,
-- glitter blob. Each starts from a tuned base body (SigKit.base) and adds the iconic details by hand.

local Kit = require(script.Parent.Parent.SigKit)
local Parts = require(script.Parent.Parent.Parts)
local Geom = require(script.Parent.Parent.Geom)

local at, rad = Kit.at, Kit.rad
local sin, cos = math.sin, math.cos

local S = {}

local function bellyPlates(B: any, A: any, n: number)
	local mn, mx = A.bodyMin, A.bodyMax
	local w, h, l = mx[1] - mn[1], mx[2] - mn[2], mx[3] - mn[3]
	for i = 1, n do
		local z = mn[3] + l * (0.22 + (i - 1) * 0.56 / math.max(1, n - 1))
		B:ell(w * 0.62, h * 0.16, l * 0.2, at(A.bodyC[1], mn[2] + h * 0.1, z, rad(4), 0, 0),
			{ col = "belly", mat = "hard", bone = A.body.bone, pri = 1.9 + i * 0.05, role = "detail", name = "BellyPlate" .. i })
	end
end

S.dragon = {
	plan = "Quadruped|Dragon",
	build = function(B: any, ctx: any)
		-- detail 3 wing spars + spikes overflow even the Huge budget; detail 2 keeps every part that is built
		ctx.detail = math.min(ctx.detail, 2)
		ctx.traits.detail = ctx.detail
		local A = Kit.base(B, ctx, "Quadruped", nil, {
			dragon = true, wings = true, flies = true, horns = true, scaly = true, spikes = true, longTail = true, mythical = true,
			wingKind = "bat", longNeck = ctx.detail >= 2, power = math.max(ctx.traits.power or 5, 8),
		})
		if ctx.detail >= 1 then
			bellyPlates(B, A, if ctx.detail >= 3 then 3 else 2)
		end
		-- second, smaller horn pair under the main sweep (reads as a crown of horns)
		if ctx.detail >= 2 then
			Parts.horns(B, { bone = A.headBone, x = A.headW * 0.38, y = A.top[2] - A.headW * 0.32, z = A.headC[3] + A.headW * 0.2, len = A.headW * 0.42, w = A.headW * 0.12, kind = "straight", segs = 1, pri = 2.3 })
		end
		B:emit("flame", nil, { socket = "mouth", rate = 30, spread = 0.3 })
		B:setRig("breath", "mouth")
	end,
}

S.cat = {
	plan = "Quadruped",
	build = function(B: any, ctx: any)
		local A = Kit.base(B, ctx, "Quadruped", nil, { mammal = true, cute = true, longTail = true, bigHead = true, claws = false })
		local s = A.headW
		-- whiskers: three thin rods each side of the muzzle
		if ctx.detail >= 2 then
			for i = 1, (if ctx.detail >= 3 then 3 else 2) do
				local y = A.mouth[2] + s * (0.12 - i * 0.06)
				B:mrod({ s * 0.16, y, A.mouth[3] + s * 0.06 }, { s * 0.62, y + s * (0.08 - i * 0.07), A.mouth[3] + s * 0.02 }, s * 0.025,
					{ col = "white", mat = "hard", bone = A.headBone, pri = 2.6 + i * 0.1, role = "detail", name = "Whisker" .. i .. "#", noCore = true })
			end
		end
		-- collar with a bell
		local ny = A.headMin[2] + s * 0.08
		B:ell(s * 0.82, s * 0.16, s * 0.82, at(A.headC[1], ny, A.headC[3] + s * 0.12, rad(-18), 0, 0), { col = "red", mat = "cloth", bone = A.headBone, pri = 1.6, role = "detail", name = "Collar" })
		B:ball(s * 0.2, at(A.headC[1], ny - s * 0.1, A.headC[3] - s * 0.3), { col = "gold", mat = "metal", bone = A.headBone, pri = 1.9, role = "detail", name = "Bell", needs = "Collar" })
		B:setRig("gait", "trot")
	end,
}

S.dog = {
	plan = "Quadruped",
	build = function(B: any, ctx: any)
		local A = Kit.base(B, ctx, "Quadruped", nil, { mammal = true, cute = true, floppyEars = true, bushyTail = false })
		local s = A.headW
		local ny = A.headMin[2] + s * 0.06
		B:ell(s * 0.86, s * 0.18, s * 0.86, at(A.headC[1], ny, A.headC[3] + s * 0.14, rad(-18), 0, 0), { col = "secondary", mat = "cloth", bone = A.headBone, pri = 1.55, role = "detail", name = "Collar" })
		B:cyl(s * 0.05, s * 0.24, at(A.headC[1], ny - s * 0.14, A.headC[3] - s * 0.28, 0, rad(90), 0), { col = "gold", mat = "metal", bone = A.headBone, pri = 1.9, role = "detail", name = "Tag", needs = "Collar" })
		-- happy tongue unless the mood already shaped the mouth
		local mood = ctx.result.mood or "Neutral"
		if mood == "Neutral" or mood == "Happy" or mood == "Hungry" then
			B:ell(s * 0.2, s * 0.08, s * 0.24, at(A.mouth[1] + s * 0.04, A.mouth[2] - s * 0.06, A.mouth[3] - s * 0.04, rad(-25), 0, 0), { col = "tongue", mat = "skin", bone = A.headBone, pri = 1.7, role = "mouth", name = "DogTongue", noCore = true })
		end
		B:setRig("tailWag", true)
	end,
}

S.unicorn = {
	plan = "Quadruped",
	build = function(B: any, ctx: any)
		local A = Kit.base(B, ctx, "Quadruped", nil, { mammal = true, unihorn = true, mane = false, longTail = true, mythical = true, longLegs = true, magic = true })
		local s = A.headW
		-- flowing rainbow mane: three pastel locks down the neck, and a forelock
		local cols = { { 1, 0.62, 0.78 }, { 0.62, 0.8, 1 }, { 0.78, 0.66, 1 } }
		local n = if ctx.detail >= 2 then 3 else 1
		for i = 1, n do
			local y = A.top[2] - s * (0.05 + i * 0.32)
			local z = A.headC[3] + s * (0.42 + i * 0.36)
			B:ell(s * 0.32, s * 0.62, s * 0.5, at(A.headC[1], y, z, rad(-35 - i * 6), 0, 0), { col = cols[i], mat = "fur", bone = A.headBone, pri = 1.5 + i * 0.1, role = "mane", name = "Mane" .. i })
		end
		B:ell(s * 0.3, s * 0.36, s * 0.26, at(A.headC[1], A.top[2] - s * 0.08, A.headC[3] - s * 0.18, rad(30), 0, 0), { col = cols[2], mat = "fur", bone = A.headBone, pri = 2.0, role = "mane", name = "Forelock" })
		B:emit("sparkle", nil, { socket = "core", rate = 12 })
	end,
}

S.shark = {
	plan = "Fish",
	build = function(B: any, ctx: any)
		local A = Kit.base(B, ctx, "Fish", "shark", { shark = true, aquatic = true, fierce = true, teeth = true })
		local mn, mx = A.bodyMin, A.bodyMax
		local w, h, l = mx[1] - mn[1], mx[2] - mn[2], mx[3] - mn[3]
		-- gill slits: three thin dark curves behind the head on each side
		if ctx.detail >= 1 then
			for i = 1, (if ctx.detail >= 2 then 3 else 1) do
				local z = mn[3] + l * (0.26 + i * 0.045)
				B:mell(w * 0.06, h * 0.38, l * 0.025, at(w * 0.44, A.bodyC[2] + h * 0.02, z, 0, rad(-12), rad(6)), { col = "darker", mat = "skin", bone = A.body.bone, pri = 2.0 + i * 0.1, role = "detail", name = "Gill" .. i .. "#", noCore = true })
			end
		end
		-- toothy grin
		if ctx.detail >= 2 then
			Parts.teeth(B, { bone = A.headBone, y = A.mouth[2] + h * 0.02, z = A.mouth[3] + l * 0.03, r = w * 0.22, n = 4, h = h * 0.14, pri = 2.2 })
		end
	end,
}

S.octopus = {
	plan = "Fish",
	build = function(B: any, ctx: any)
		local A = Kit.base(B, ctx, "Fish", "octopus", { tentacles = true, cute = true })
		local s = A.headW
		-- spots on the mantle
		if ctx.detail >= 2 then
			for i = 1, 3 do
				local a = rad(-40 + i * 25)
				B:ell(s * 0.16, s * 0.16, s * 0.06, at(A.headC[1] + sin(a) * s * 0.38, A.top[2] - s * (0.2 + i * 0.06), A.headC[3] + cos(a) * s * 0.3, rad(-30), a, 0),
					{ col = "secondary", mat = "skin", bone = A.headBone, pri = 2.4 + i * 0.1, role = "detail", name = "Spot" .. i, noCore = true })
			end
		end
		B:emit("bubbles", nil, { socket = "core", rate = 8 })
	end,
}

S.kraken = {
	plan = "Fish",
	build = function(B: any, ctx: any)
		local A = Kit.base(B, ctx, "Fish", "octopus", { tentacles = true, mythical = true, fierce = true, power = 10 })
		local s = A.headW
		-- two huge rearing tentacles that frame the head (the silhouette people recognise)
		for side = -1, 1, 2 do
			local x = side * s * 0.75
			local base = { x, A.headMin[2] + s * 0.1, A.headC[3] - s * 0.1 }
			local mid = { x + side * s * 0.6, A.top[2] + s * 0.2, A.headC[3] - s * 0.45 }
			local tip = { x + side * s * 0.25, A.top[2] + s * 0.9, A.headC[3] - s * 0.95 }
			B:limb(base, mid, s * 0.36, { col = "primary", mat = "skin", bone = A.headBone, pri = 1.3, role = "tentacle", name = "Rear" .. (if side > 0 then "R" else "L"), pair = "kraken" }, 0.2)
			B:limb(mid, tip, s * 0.22, { col = "primary", mat = "skin", bone = A.headBone, pri = 1.4, role = "tentacle", name = "RearTip" .. (if side > 0 then "R" else "L"), pair = "krakenTip", trail = true }, 0.2)
		end
		B:setRig("menace", true)
	end,
}

S["t rex"] = {
	plan = "Biped",
	build = function(B: any, ctx: any)
		local A = Kit.base(B, ctx, "Biped", "dino", { reptile = true, bigHead = true, scaly = true, power = 10, tinyArms = true })
		local s = A.headW
		-- tiny arms: the joke and the silhouette
		local mn, mx = A.bodyMin, A.bodyMax
		local ax, ay, az = (mx[1] - mn[1]) * 0.36, mn[2] + (mx[2] - mn[2]) * 0.45, mn[3] + (mx[3] - mn[3]) * 0.2
		B:mlimb({ ax, ay, az }, { ax + s * 0.12, ay - s * 0.38, az - s * 0.3 }, s * 0.14, { col = "primary", mat = "skin", bone = A.body.bone, pri = 1.6, role = "limb", name = "TinyArm#" }, 0.1)
		if ctx.detail >= 2 then
			Parts.teeth(B, { bone = A.headBone, y = A.mouth[2] + s * 0.1, z = A.mouth[3] + s * 0.08, r = s * 0.26, n = 5, h = s * 0.16, pri = 2.0 })
			-- brow ridges
			B:mell(s * 0.34, s * 0.1, s * 0.3, at(s * 0.2, A.face[2] + A.eyeSize * 0.75, A.face[3] + s * 0.05, rad(-10), 0, rad(-12)), { col = "dark", mat = "skin", bone = A.headBone, pri = 2.3, role = "detail", name = "Ridge#", noCore = true })
		end
		B:setRig("gait", "stomp")
	end,
}

S.golem = {
	plan = "Biped",
	build = function(B: any, ctx: any)
		local A = Kit.base(B, ctx, "Biped", "brute", { golem = true, heavy = true, rock = true, stone = true, glowEyes = true, power = 9, durability = 10 })
		local mn, mx = A.bodyMin, A.bodyMax
		local w, h = mx[1] - mn[1], mx[2] - mn[2]
		-- boulder shoulders and glowing runes cut into the chest
		B:mell(w * 0.42, h * 0.32, w * 0.4, at(w * 0.42, mx[2] - h * 0.12, A.bodyC[3], rad(12), rad(20), rad(-14)), { col = "secondary", mat = "stone", bone = A.body.bone, pri = 1.35, role = "body", name = "Boulder#" })
		local n = if ctx.detail >= 2 then 3 else 1
		for i = 1, n do
			B:ell(w * 0.1, h * 0.12, w * 0.05, at(A.bodyC[1] + (i - (n + 1) / 2) * w * 0.16, A.bodyC[2] + h * (0.05 - (i % 2) * 0.08), mn[3] + w * 0.02, 0, 0, rad(i * 30)),
				{ col = "glow", mat = "neon", glow = true, bone = A.body.bone, pri = 1.7 + i * 0.1, role = "gem", name = "Rune" .. i, noCore = true })
		end
		if ctx.detail >= 2 then
			B:mell(w * 0.26, h * 0.08, w * 0.24, at(w * 0.42, mx[2] - h * 0.0, A.bodyC[3] + w * 0.02, 0, rad(20), rad(-14)), { col = "leaf", mat = "leaf", bone = A.body.bone, pri = 2.6, role = "detail", name = "Moss#", noCore = true })
		end
		B:emit("dust", nil, { socket = "core", rate = 6 })
		B:setRig("gait", "stomp")
	end,
}

S.phoenix = {
	plan = "Bird",
	build = function(B: any, ctx: any)
		local A = Kit.base(B, ctx, "Bird", nil, { bird = true, flies = true, wings = true, crest = true, longTail = true, mythical = true, glowEyes = true })
		local mn, mx = A.bodyMin, A.bodyMax
		local l = mx[3] - mn[3]
		-- three long flame plumes fanning out behind
		local n = if ctx.detail >= 2 then 3 else 1
		for i = 1, n do
			local yaw = (i - (n + 1) / 2) * rad(16)
			local a = { A.bodyC[1], A.bodyC[2], mx[3] - l * 0.1 }
			local b = { a[1] + sin(yaw) * l * 1.3, a[2] - l * 0.25 + (i % 2) * l * 0.12, a[3] + cos(yaw) * l * 1.3 }
			B:limb(a, b, l * 0.16, { col = if i == 2 then "flameCore" else "flame", mat = "neon", glow = true, bone = A.body.bone, pri = 1.4 + i * 0.05, role = "tail", name = "Plume" .. i, trail = true, noCore = true }, 0.1)
		end
		-- crest flame
		B:limb({ A.headC[1], A.top[2] - A.headW * 0.1, A.headC[3] }, { A.headC[1], A.top[2] + A.headW * 0.55, A.headC[3] + A.headW * 0.4 }, A.headW * 0.3,
			{ col = "flame", mat = "neon", glow = true, bone = A.headBone, pri = 1.6, role = "crest", name = "CrestFlame", noCore = true }, 0.1)
		B:emit("embers", nil, { socket = "core", rate = 24 })
	end,
}

S.bee = {
	plan = "Insect",
	build = function(B: any, ctx: any)
		local A = Kit.base(B, ctx, "Insect", "Bug", { insect = true, stinger = true, wings = true, flies = true, fluffy = true, cute = true })
		local s = A.headW
		-- antennae with ball tips
		for side = -1, 1, 2 do
			local b = { A.headC[1] + side * s * 0.18, A.top[2] - s * 0.05, A.headC[3] - s * 0.1 }
			local tip = { A.headC[1] + side * s * 0.42, A.top[2] + s * 0.5, A.headC[3] - s * 0.4 }
			B:rod(b, tip, s * 0.06, { col = "black", mat = "hard", bone = A.headBone, pri = 1.6, role = "antenna", name = "Antenna" .. (if side > 0 then "R" else "L"), pair = "beeAnt", noCore = true })
			B:ball(s * 0.16, at(tip[1], tip[2], tip[3]), { col = "black", mat = "hard", bone = A.headBone, pri = 2.0, role = "antenna", name = "AntennaTip" .. (if side > 0 then "R" else "L"), pair = "beeTip", noCore = true, needs = "beeAnt" })
		end
		-- fuzzy collar between head and thorax
		B:ell(s * 0.95, s * 0.6, s * 0.5, at(A.headC[1], A.headC[2] - s * 0.05, A.headC[3] + s * 0.42), { col = "light", mat = "fur", bone = A.body.bone, pri = 1.8, role = "detail", name = "Fuzz", noCore = true })
		B:setRig("gait", "buzz")
	end,
}

S["glitter blob"] = {
	plan = "Blob",
	build = function(B: any, ctx: any)
		local A = Kit.base(B, ctx, "Blob", nil, { slime = true, cute = true, glitter = true })
		local mn, mx = A.bodyMin, A.bodyMax
		local w, h = mx[1] - mn[1], mx[2] - mn[2]
		-- embedded glitter flakes catching the light
		local n = if ctx.detail >= 2 then 6 else 3
		local cols = { "gold", "white", "glow" }
		for i = 1, n do
			local a = i * 2.39996
			local y = 0.25 + (i / n) * 0.55
			local r = math.sqrt(math.max(0.05, 1 - (y * 2 - 1) ^ 2)) * 0.5
			local x, z = A.bodyC[1] + cos(a) * w * r * 0.98, A.bodyC[3] + sin(a) * w * r * 0.98
			if z > A.face[3] + A.spacing * 0.6 or math.abs(x - A.face[1]) > A.spacing then
				B:block(w * 0.06, w * 0.06, w * 0.015, Geom.mul(at(x, mn[2] + h * y, z), at(0, 0, 0, rad(i * 37), a, rad(45))),
					{ col = cols[(i % 3) + 1], mat = "neon", glow = true, bone = A.body.bone, pri = 2.2 + i * 0.05, role = "gem", name = "Glitter" .. i, noCore = true })
			end
		end
		B:emit("glitter", nil, { socket = "core", rate = 20 })
		B:setRig("materialMotion", "wobble")
	end,
}

return S
