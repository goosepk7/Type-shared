--!strict
-- Swarm: many small units. Each unit is 1-6 parts on its own bone so the animator can buzz / orbit / shuffle them
-- independently. Heroes stand (or fly) in front at full detail; fillers behind are cheaper versions of the same unit
-- and fill the part budget, so the swarm reads as a crowd at every size.
--
-- Two formations:
--   cloud  (bees, wasps, bats, birds, fireflies, sparks, fish, drones, pixies, ghosts, wyrmlings, jellies, krill,
--           imps; and tumbling bits for food / objects / abstract words): a squashed lumpy cloud;
--   ground (people, armies, bands, crews, skeletons, zombies, mummies, goblins, gremlins, ants, termites, beetles,
--           rats, robots, slimes, the funayurei's hands): rows / columns on the ground, heroes in the front row.

local Geom = require(script.Parent.Parent.Geom)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local function has(s: string, w: string): boolean
	return string.find(s, "%f[%a]" .. w) ~= nil
end

local function word(s: string, w: string): boolean
	return string.find(s, "%f[%a]" .. w .. "%f[%A]") ~= nil
end

local GROUND: { [string]: boolean } = { person = true, ant = true, beetle = true, rat = true, robot = true, slime = true, hand = true }

local function unitKind(ctx: any): string
	local t, id = ctx.traits, string.lower(ctx.result.id)
	local hint = string.lower((ctx.result.visual and ctx.result.visual.silhouetteHint) or "")
	local s = id .. " " .. hint
	local cat = ctx.result.category
	if word(id, "bat") then
		return "bat"
	elseif has(s, "drone") and not has(s, "bee") or has(s, "quadcopter") then
		return "drone"
	elseif has(id, "funayurei") or has(hint, "hands holding") then
		return "hand"
	elseif has(s, "ghost") then
		return "ghost"
	elseif has(s, "pixie") or has(s, "sprite") or has(s, "fairy") then
		return "pixie"
	elseif has(s, "wyrmling") or has(s, "dragons") then
		return "wyrm"
	elseif has(s, "jelly") or has(s, "jellies") or has(s, "jellyfish") then
		return if has(s, "slime") or has(s, "bouncing") then "slime" else "jelly"
	elseif has(s, "slime") then
		return "slime"
	elseif has(s, "krill") or has(s, "shrimp") or has(s, "copepod") or has(s, "plankton") then
		return "shrimp"
	elseif word(s, "rat") or word(s, "rats") or has(s, "vermin") or has(s, "nibblers") then
		return "rat"
	elseif has(s, "robot") and not has(s, "bee") then
		return "robot"
	elseif has(s, "scarab") or has(s, "beetle") or has(s, "beetles") then
		return "beetle"
	elseif word(s, "ant") or word(s, "ants") or has(s, "termite") or has(s, "colony") then
		return "ant"
	elseif (word(s, "imp") or word(s, "imps")) and not has(s, "gremlin") and not has(s, "goblin") then
		return "imp"
	elseif cat == "Person" or has(s, "crowd") or has(s, "army") or has(s, "horde") or has(s, "skeleton") or has(s, "skeletons") or has(s, "zombie")
		or has(s, "zombies") or has(s, "mummy") or has(s, "undead") or has(s, "goblin") or has(s, "gremlin") or has(s, "vikings") or has(s, "soldiers")
		or has(s, "figures") or has(s, "silhouettes") or has(s, "raiders") or has(s, "monsters") then
		return "person"
	elseif t.aquatic or t.swims or has(id, "fish") or has(id, "piranha") then
		return "fish"
	elseif has(id, "firefl") or has(id, "glowworm") or has(id, "lightning bug") then
		return "firefly"
	elseif has(s, "spark") or has(s, "ember") or has(s, "wisp") or has(s, "lights") or has(s, "stars") or has(s, "glowing dots") or t.element == "Light" then
		return "spark"
	elseif has(s, "bird") or has(s, "birds") or has(s, "crow") or has(s, "pigeon") or has(s, "flock") then
		return "bird"
	elseif cat == "Creature" or cat == "Machine" or t.insect or t.stinger then
		return "bug"
	end
	return "bit" -- food, objects, abstract words: a tumble of their own shapes and colours, never winged bugs
end

-- Person styles: what a crowd member wears and carries. Picked from the word; `mix` alternates per unit.
local function personStyle(id: string, hint: string): any
	local s = id .. " " .. hint
	local st: any = { cloth = "primary", cloth2 = "secondary", pants = "darker", skin = "skin", prop = nil, head = nil }
	if has(s, "skeleton") then
		st.cloth, st.pants, st.skin, st.ribs, st.prop = "white", "white", "white", true, "sword"
		st.undead = true
	elseif has(s, "zombie") or has(s, "shambling") then
		st.skin, st.cloth, st.pants, st.zombie = { 0.55, 0.72, 0.45 }, "darker", "dark", true
		st.undead = true
	elseif has(s, "mummy") or has(s, "bandaged") then
		st.cloth, st.pants, st.skin, st.wrap = "cream", "cream", "cream", true
		st.undead = true
	elseif has(s, "undead") then
		st.mix = { "skeleton", "zombie" }
		st.undead = true
	elseif has(s, "goblin") then
		st.skin, st.ears, st.prop, st.cloth = { 0.45, 0.68, 0.3 }, "pointy", "club", "leather"
	elseif has(s, "gremlin") then
		st.skin, st.ears, st.prop, st.cloth = { 0.42, 0.55, 0.36 }, "long", "wrench", "darker"
	elseif has(s, "viking") or has(id, "einherjar") then
		st.head, st.prop, st.cloth = "viking", "shield", "primary"
	elseif has(s, "torches") or has(s, "pitchfork") or has(s, "pitchforks") or has(id, "mob") or has(id, "militia") then
		st.mix = { "torch", "pitchfork" }
	elseif has(s, "musician") or has(s, "musicians") or has(id, "band") or has(id, "orchestra") then
		st.mix, st.head = { "horn", "drum" }, if has(id, "marching") then "shako" else nil
	elseif has(s, "robed") or has(id, "choir") then
		st.robe, st.cloth, st.mouth = true, "primary", true
	elseif has(s, "soldier") or has(s, "soldiers") or has(id, "squad") or has(id, "army") or has(id, "legion") or has(id, "police") then
		st.head, st.prop, st.cloth = "helmet", if has(id, "legion") then "spear" else "rifle", if has(id, "police") then { 0.15, 0.2, 0.42 } else "primary"
	elseif has(s, "pirate") or has(s, "pirates") then
		st.head, st.stripes, st.prop = "bandana", true, "sword"
	elseif has(s, "sailors") or has(id, "crew") then
		st.stripes, st.head, st.rope = true, "cap", true
	elseif has(s, "ninja") or has(s, "black%-clad") then
		st.cloth, st.pants, st.skin, st.head = "black", "black", "black", "mask"
	elseif has(s, "leather") or has(id, "gang") then
		st.cloth, st.pants = "black", { 0.2, 0.25, 0.42 }
	elseif has(s, "jerseys") or has(id, "team") or has(id, "rugby") then
		st.cloth, st.prop = "red", "ball"
	elseif has(s, "glow sticks") or has(id, "fandom") or has(id, "crowd") then
		st.mix = { "glowstick", "sign" }
	elseif has(s, "cheerleaders") or has(id, "cheer") then
		st.prop = "pompom"
	elseif has(s, "coffee") or has(id, "group") then
		st.prop = "cup"
	elseif has(id, "guild") or has(s, "heroes") then
		st.mix = { "knight", "mage", "archer", "healer" }
	elseif has(s, "tartan") or has(id, "clan") then
		st.stripes, st.mix = true, { "banner", "drum" }
	elseif has(s, "hug") or id == "us" then
		st.hug, st.mix = true, { "red", "gold", "leaf", "glass", "blush" }
	elseif has(s, "monsters") or has(id, "horde") then
		st.mix = { "goblin", "skeleton", "zombie" }
	end
	return st
end

-- PERSON: legs, torso, head (+ prop / headwear on heroes). Feet at p[2] = 0.
local function person(B: any, st: any, i: number, p: { number }, s: number, detail: number, tier: number, bone: string, pri: number): number
	local var = if st.mix then st.mix[(i - 1) % #st.mix + 1] else nil
	local cloth, pants, skin, prop, head = st.cloth, st.pants, st.skin, st.prop, st.head
	local ears = st.ears
	if var == "skeleton" then
		cloth, pants, skin, prop = "white", "white", "white", "sword"
	elseif var == "zombie" then
		cloth, pants, skin = "darker", "dark", { 0.55, 0.72, 0.45 }
	elseif var == "goblin" then
		skin, ears, prop, cloth = { 0.45, 0.68, 0.3 }, "pointy", "club", "leather"
	elseif var == "knight" then
		head, prop, cloth = "helmet", "sword", "steel"
	elseif var == "mage" then
		head, prop, cloth = "wizard", "staff", "secondary"
	elseif var == "archer" then
		head, prop, cloth = "hood", "bow", "leaf"
	elseif var == "healer" then
		prop, cloth = "staff", "white"
	elseif var == "red" or var == "gold" or var == "leaf" or var == "glass" or var == "blush" then
		cloth = var
	elseif var then
		prop = var
	elseif i % 2 == 0 and cloth == "primary" then
		cloth = "secondary"
	end
	local x, z = p[1], p[3]
	local yaw = ((i * 2.399) % 0.6) - 0.3
	local function F(lx: number, ly: number, lz: number, rx: number?, ry: number?, rz: number?): any
		return Geom.mul(at(x, 0, z, 0, yaw, 0), at(lx, ly, lz, rx or 0, ry or 0, rz or 0))
	end
	local used = 0
	local hero = tier == 1
	-- torso (robes reach the ground)
	if st.robe then
		B:ell(s * 0.85, s * 1.75, s * 0.62, F(0, s * 0.88, 0), { col = cloth, mat = "cloth", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		used += 1
	else
		B:ell(s * 0.78, s * 0.98, s * 0.52, F(0, s * 1.18, 0), { col = cloth, mat = if cloth == "steel" then "metal" else "cloth", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		used += 1
		if hero or detail >= 3 then
			B:ell(s * 0.62, s * 0.86, s * 0.42, F(0, s * 0.45, 0.01), { col = pants, mat = "cloth", bone = bone, pri = pri + 0.05, role = "limb", name = "Legs" .. i, needs = "Unit" .. i })
			used += 1
		end
	end
	B:ball(s * 0.62, F(0, s * 1.93, -0.01), { col = skin, mat = "skin", bone = bone, pri = pri + 0.02, role = "head", name = "Head" .. i, needs = "Unit" .. i })
	used += 1
	if not hero then
		return used
	end
	-- arms: one bar across the shoulders (hug) or a pair of short sleeves
	if st.hug then
		B:ell(s * 1.9, s * 0.2, s * 0.24, F(s * 0.05, s * 1.5, 0.03, 0, 0, rad(-4)), { col = cloth, mat = "cloth", bone = bone, pri = pri + 0.1, role = "limb", name = "Arms" .. i })
		used += 1
	elseif st.zombie or var == "zombie" then
		B:ell(s * 0.75, s * 0.18, s * 0.9, F(0, s * 1.4, -s * 0.5), { col = skin, mat = "skin", bone = bone, pri = pri + 0.1, role = "limb", name = "Arms" .. i })
		used += 1
	end
	-- headwear
	local top = s * 2.2
	if head == "helmet" then
		B:ell(s * 0.7, s * 0.38, s * 0.7, F(0, top - s * 0.08, 0), { col = "steel", mat = "metal", bone = bone, pri = pri + 0.2, role = "hat", name = "Helmet" .. i })
		used += 1
	elseif head == "viking" then
		B:ell(s * 0.68, s * 0.36, s * 0.68, F(0, top - s * 0.08, 0), { col = "steel", mat = "metal", bone = bone, pri = pri + 0.2, role = "hat", name = "Helmet" .. i })
		B:ell(s * 1.15, s * 0.14, s * 0.14, F(0, top + s * 0.02, 0.0, 0, 0, 0), { col = "horn", mat = "hard", bone = bone, pri = pri + 0.4, role = "horn", name = "Horns" .. i })
		used += 2
	elseif head == "wizard" then
		B:limb({ x, top - s * 0.15, z }, { x + s * 0.08, top + s * 0.7, z + s * 0.1 }, s * 0.55, { col = "secondary", mat = "cloth", bone = bone, pri = pri + 0.2, role = "hat", name = "Hat" .. i }, 0.05)
		used += 1
	elseif head == "bandana" or head == "cap" or head == "hood" or head == "shako" then
		local c = if head == "bandana" then "red" elseif head == "hood" then "leaf" elseif head == "shako" then "secondary" else "white"
		local hgt = if head == "shako" then s * 0.6 else s * 0.3
		B:ell(s * 0.66, hgt, s * 0.66, F(0, top - s * 0.12 + hgt * 0.3, 0.02), { col = c, mat = "cloth", bone = bone, pri = pri + 0.2, role = "hat", name = "Hat" .. i })
		used += 1
	elseif head == "mask" then
		B:ell(s * 0.5, s * 0.1, s * 0.12, F(0, s * 1.98, -s * 0.28), { col = "skin", mat = "skin", bone = bone, pri = pri + 0.2, role = "detail", name = "EyeBand" .. i })
		used += 1
	end
	if ears then
		local long = ears == "long"
		B:mwedge(s * 0.08, s * (if long then 0.62 else 0.4), s * 0.3, F(s * 0.32, s * 2.05, 0.02, 0, 0, rad(if long then -62 else -38)), { col = skin, mat = "skin", bone = bone, pri = pri + 0.3, role = "ear", name = "Ear" .. i .. "#" })
		used += 2
	end
	if st.stripes and detail >= 2 then
		B:ell(s * 0.8, s * 0.14, s * 0.54, F(0, s * 1.22, 0), { col = "white", mat = "cloth", bone = bone, pri = pri + 0.5, role = "detail", name = "Stripe" .. i })
		used += 1
	end
	if st.wrap and detail >= 2 then
		B:ell(s * 0.82, s * 0.12, s * 0.56, F(0, s * 1.35, 0, 0, 0, rad(12)), { col = "darker", mat = "cloth", bone = bone, pri = pri + 0.5, role = "detail", name = "Wrap" .. i })
		used += 1
	end
	if st.ribs and detail >= 2 then
		B:ell(s * 0.6, s * 0.12, s * 0.12, F(0, s * 1.3, -s * 0.25), { col = "dark", mat = "hard", bone = bone, pri = pri + 0.5, role = "detail", name = "Rib" .. i })
		used += 1
	end
	if st.mouth and detail >= 2 then
		B:ell(s * 0.16, s * 0.2, s * 0.1, F(0, s * 1.84, -s * 0.29), { col = "mouth", mat = "skin", bone = bone, pri = pri + 0.6, role = "mouth", name = "Mouth" .. i, noCore = true })
		used += 1
	end
	-- the prop, held in the right hand
	local hx, hy = s * 0.5, s * 1.25
	local P = prop
	if P == "torch" then
		B:limb({ x + hx, hy - s * 0.2, z - s * 0.1 }, { x + hx, hy + s * 1.0, z - s * 0.2 }, s * 0.12, { col = "wood", mat = "wood", bone = bone, pri = pri + 0.3, role = "held", name = "Torch" .. i }, 0.05)
		B:ell(s * 0.32, s * 0.5, s * 0.32, F(hx, hy + s * 1.15, -s * 0.22), { col = "flame", mat = "neon", glow = true, bone = bone, pri = pri + 0.35, role = "glow", name = "Flame" .. i, noCore = true, trail = i == 1 })
		used += 2
	elseif P == "pitchfork" or P == "spear" or P == "rifle" or P == "staff" then
		local len = if P == "rifle" then s * 1.2 else s * 2.4
		B:limb({ x + hx, hy - s * 0.6, z - s * 0.1 }, { x + hx, hy - s * 0.6 + len, z - s * 0.15 }, s * 0.1, { col = if P == "rifle" then "gunmetal" else "wood", mat = if P == "rifle" then "metal" else "wood", bone = bone, pri = pri + 0.3, role = "held", name = "Pole" .. i, mesh = false }, 0.02)
		used += 1
		if P == "pitchfork" or P == "spear" then
			B:wedge(s * 0.06, s * 0.36, s * (if P == "spear" then 0.16 else 0.36), F(hx, hy - s * 0.6 + len + s * 0.15, -s * 0.15, 0, rad(90), 0), { col = "steel", mat = "metal", bone = bone, pri = pri + 0.4, role = "held", name = "Tip" .. i })
			used += 1
		elseif P == "staff" then
			B:ball(s * 0.3, F(hx, hy - s * 0.6 + len, -s * 0.15), { col = "gem", mat = "neon", glow = true, bone = bone, pri = pri + 0.4, role = "gem", name = "Orb" .. i, noCore = true })
			used += 1
		end
	elseif P == "sword" or P == "club" or P == "wrench" then
		B:block(s * 0.1, s * (if P == "sword" then 1.0 else 0.75), s * (if P == "club" then 0.22 else 0.08), F(hx + s * 0.05, hy + s * 0.25, -s * 0.2, rad(-20), 0, 0), { col = if P == "club" then "wood" else "steel", mat = if P == "club" then "wood" else "metal", bone = bone, pri = pri + 0.3, role = "held", name = "Blade" .. i })
		used += 1
	elseif P == "shield" then
		B:cyl(s * 0.1, s * 0.9, F(-s * 0.45, s * 1.15, -s * 0.32, 0, rad(90 - 15), 0), { col = "secondary", mat = "wood", bone = bone, pri = pri + 0.3, role = "held", name = "Shield" .. i })
		used += 1
	elseif P == "horn" then
		B:cyl(s * 0.7, s * 0.22, F(s * 0.2, s * 1.65, -s * 0.5, 0, rad(90), rad(10)), { col = "gold", mat = "metal", bone = bone, pri = pri + 0.3, role = "held", name = "Horn" .. i })
		B:cyl(s * 0.1, s * 0.45, F(s * 0.2, s * 1.72, -s * 0.88, 0, rad(90), rad(10)), { col = "gold", mat = "metal", bone = bone, pri = pri + 0.35, role = "held", name = "Bell" .. i })
		used += 2
	elseif P == "drum" then
		B:cyl(s * 0.45, s * 0.75, F(0, s * 1.0, -s * 0.5, 0, 0, rad(90)), { col = "red", mat = "plastic", bone = bone, pri = pri + 0.3, role = "held", name = "Drum" .. i })
		used += 1
	elseif P == "glowstick" then
		B:limb({ x + hx, hy, z - s * 0.1 }, { x + hx + s * 0.15, hy + s * 0.9, z - s * 0.2 }, s * 0.12, { col = "glow", mat = "neon", glow = true, bone = bone, pri = pri + 0.3, role = "gem", name = "Glow" .. i, noCore = true, trail = i == 1 }, 0.02)
		used += 1
	elseif P == "sign" or P == "banner" then
		B:limb({ x + hx, hy - s * 0.3, z }, { x + hx, hy + s * 1.3, z }, s * 0.08, { col = "wood", mat = "wood", bone = bone, pri = pri + 0.3, role = "held", name = "Pole" .. i, mesh = false }, 0.02)
		B:block(s * (if P == "banner" then 0.65 else 0.95), s * 0.6, s * 0.06, F(hx + (if P == "banner" then s * 0.34 else 0), hy + s * 1.0, -s * 0.06), { col = if P == "banner" then "secondary" else "white", mat = "cloth", bone = bone, pri = pri + 0.35, role = "held", name = "Sign" .. i })
		used += 2
	elseif P == "pompom" then
		B:mball(s * 0.42, F(s * 0.55, s * 1.75, -s * 0.1), { col = "secondary", mat = "cloth", bone = bone, pri = pri + 0.3, role = "held", name = "Pom" .. i .. "#" })
		used += 2
	elseif P == "cup" then
		B:cyl(s * 0.3, s * 0.22, F(hx, hy + s * 0.05, -s * 0.3, 0, 0, rad(90)), { col = "white", mat = "plastic", bone = bone, pri = pri + 0.3, role = "held", name = "Cup" .. i })
		used += 1
	elseif P == "ball" then
		B:ball(s * 0.42, F(hx, hy - s * 0.15, -s * 0.3), { col = "wood", mat = "skin", bone = bone, pri = pri + 0.3, role = "held", name = "Ball" .. i })
		used += 1
	elseif P == "bow" then
		B:ell(s * 0.08, s * 1.3, s * 0.3, F(-s * 0.5, s * 1.3, -s * 0.2), { col = "wood", mat = "wood", bone = bone, pri = pri + 0.3, role = "held", name = "Bow" .. i })
		used += 1
	end
	return used
end

-- One unit centred at p; returns parts used. tier 1 = hero (full detail, near the front), 2 = filler.
local function unit(B: any, kind: string, i: number, p: { number }, s: number, detail: number, tier: number, striped: boolean, st: any): number
	local bone = B:bone("Unit" .. i, "Body", p[1], p[2], p[3])
	B:addRig("units", { bone = bone, index = i })
	-- the swarm travels together: units face roughly forward (-Z) with a seeded spread, not every which way
	local yaw = ((i * 2.399) % 1.4) - 0.7
	local base = at(p[1], p[2], p[3], rad(((i * 37) % 21) - 10), yaw, 0)
	local flat = at(p[1], p[2], p[3], 0, yaw * 0.5, 0)
	local pri = (if tier == 1 then 1 else 1.4) + i * 0.02
	local hero = tier == 1
	if kind == "person" then
		return person(B, st, i, p, s, detail, tier, bone, pri)
	end
	if kind == "firefly" then
		-- a dark little beetle with a glowing lantern abdomen; the distant ones are just the lanterns
		if hero then
			B:ell(s * 0.42, s * 0.36, s * 0.62, Geom.mul(base, at(0, s * 0.05, -s * 0.28)), { col = "dark", mat = "hard", bone = bone, pri = pri, role = "body", name = "Bug" .. i })
		end
		-- far lanterns shrink with depth (three steps), so the cloud reads as a deep field of lights, not dots
		local k = if hero then 1 else ({ 0.9, 0.68, 0.5 })[i % 3 + 1]
		B:ell(s * 0.5 * k, s * 0.46 * k, s * 0.62 * k, Geom.mul(base, at(0, 0, s * 0.22)), { col = { 0.86, 1, 0.38 }, mat = "neon", glow = true, bone = bone, pri = pri + 0.02, role = "gem", name = "Lantern" .. i, noCore = true, trail = i <= 2 })
		return if hero then 2 else 1
	end
	if kind == "spark" then
		B:ball(s * (if hero then 0.75 else 0.5), base, { col = "glow", mat = "neon", glow = true, bone = bone, pri = pri, role = "gem", name = "Spark" .. i, noCore = true, trail = i <= 2 })
		return 1
	end
	if kind == "fish" then
		B:ell(s * 0.5, s * 0.75, s * 1.35, base, { col = "primary", mat = "skin", bone = bone, pri = pri, role = "body", name = "Fish" .. i })
		if hero or detail >= 3 then
			B:wedge(s * 0.08, s * 0.65, s * 0.5, Geom.mul(base, at(0, 0, s * 0.78, 0, 0, 0)), { col = "secondary", mat = "skin", bone = bone, pri = pri + 0.3, role = "fin", name = "Tail" .. i })
			return 2
		end
		return 1
	end
	if kind == "bat" or kind == "bird" then
		B:ell(s * 0.55, s * 0.6, s * 0.8, base, { col = "primary", mat = "fur", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		-- wings: one swept chevron-like flattened ellipsoid per unit, wide (the flock reads by its wing shapes)
		B:ell(s * 2.4, s * 0.08, s * 0.55, Geom.mul(base, at(0, s * 0.18, s * 0.08, rad(6), 0, 0)), { col = if kind == "bat" then "membrane" else "dark", mat = "skin", bone = bone, pri = pri + 0.05, role = "wing", name = "Wings" .. i, trail = hero and i <= 2 })
		return 2
	end
	if kind == "drone" then
		-- quadcopter: a hub with four arms, rotor discs on the heroes
		B:block(s * 0.62, s * 0.26, s * 0.62, flat, { col = "primary", mat = "plastic", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		B:block(s * 1.5, s * 0.08, s * 0.12, Geom.mul(flat, at(0, s * 0.02, 0, 0, rad(45), 0)), { col = "dark", mat = "plastic", bone = bone, pri = pri + 0.05, role = "detail", name = "ArmA" .. i, needs = "Unit" .. i })
		-- both arms on every unit: the X reads as a quadcopter even far back in the swarm
		B:block(s * 1.5, s * 0.08, s * 0.12, Geom.mul(flat, at(0, s * 0.03, 0, 0, rad(-45), 0)), { col = "dark", mat = "plastic", bone = bone, pri = pri + 0.06, role = "detail", name = "ArmB" .. i, needs = "Unit" .. i })
		local used = 3
		if hero then
			for j = 1, 4 do
				local a = rad(45 + j * 90)
				B:cyl(s * 0.04, s * 0.55, Geom.mul(flat, at(sin(a) * s * 0.53, s * 0.13, cos(a) * s * 0.53, 0, 0, rad(90))), { col = "wingGlass", mat = "glass", tr = 0.4, bone = bone, pri = pri + 0.1 + j * 0.01, role = "wing", name = "Rotor" .. i .. "_" .. j, needs = "Unit" .. i })
			end
			B:ball(s * 0.16, Geom.mul(flat, at(0, -s * 0.02, -s * 0.33)), { col = "red", mat = "neon", glow = true, bone = bone, pri = pri + 0.2, role = "gem", name = "Led" .. i, noCore = true })
			used += 5
		end
		return used
	end
	if kind == "ghost" then
		local body = B:ell(s * 1.1, s * 1.3, s * 1.0, flat, { col = "white", mat = "cloth", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		local skirt = B:ell(s * 1.3, s * 0.95, s * 1.2, Geom.mul(flat, at(0, -s * 0.58, s * 0.02)), { col = "white", mat = "cloth", bone = bone, pri = pri + 0.03, role = "body", name = "Skirt" .. i, needs = "Unit" .. i })
		B:sculpt(body, "s_blob_ghost", { skirt })
		local used = 2
		if hero then
			B:mell(s * 0.2, s * 0.3, s * 0.1, Geom.mul(flat, at(s * 0.19, s * 0.12, -s * 0.47)), { col = "black", mat = "skin", bone = bone, pri = pri + 0.1, role = "eye", name = "Eye" .. i .. "#", noCore = true })
			used += 2
		end
		return used
	end
	if kind == "pixie" then
		B:ell(s * 0.32, s * 0.6, s * 0.3, flat, { col = "primary", mat = "skin", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		B:ell(s * 1.5, s * 0.05, s * 0.6, Geom.mul(flat, at(0, s * 0.2, s * 0.12, rad(-12), 0, 0)), { col = "wingGlass", mat = "glass", tr = 0.35, bone = bone, pri = pri + 0.05, role = "wing", name = "Wings" .. i, needs = "Unit" .. i })
		local used = 2
		if hero then
			B:ball(s * 0.38, Geom.mul(flat, at(0, s * 0.45, 0)), { col = "skin", mat = "skin", bone = bone, pri = pri + 0.02, role = "head", name = "Head" .. i })
			B:ball(s * 0.22, Geom.mul(flat, at(0, -s * 0.38, 0)), { col = "glow", mat = "neon", glow = true, bone = bone, pri = pri + 0.1, role = "gem", name = "Glow" .. i, noCore = true, trail = i <= 2 })
			used += 2
		end
		return used
	end
	if kind == "wyrm" then
		B:ell(s * 0.5, s * 0.5, s * 1.1, base, { col = "primary", mat = "scale", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		B:ell(s * 1.9, s * 0.06, s * 0.6, Geom.mul(base, at(0, s * 0.22, s * 0.05, rad(5), 0, 0)), { col = "membrane", mat = "skin", bone = bone, pri = pri + 0.05, role = "wing", name = "Wings" .. i, needs = "Unit" .. i, trail = hero and i <= 2 })
		local used = 2
		if hero then
			B:ell(s * 0.42, s * 0.38, s * 0.62, Geom.mul(base, at(0, s * 0.22, -s * 0.66, rad(-10), 0, 0)), { col = "primary", mat = "scale", bone = bone, pri = pri + 0.02, role = "head", name = "Head" .. i })
			B:ell(s * 0.2, s * 0.2, s * 0.9, Geom.mul(base, at(0, -s * 0.05, s * 0.85, rad(10), 0, 0)), { col = "secondary", mat = "scale", bone = bone, pri = pri + 0.1, role = "tail", name = "Tail" .. i })
			used += 2
		end
		return used
	end
	if kind == "imp" then
		-- a little red devil: pot belly, big head with horns, bat wings
		B:ell(s * 0.55, s * 0.62, s * 0.5, flat, { col = "primary", mat = "skin", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		B:ball(s * 0.58, Geom.mul(flat, at(0, s * 0.55, -s * 0.03)), { col = "primary", mat = "skin", bone = bone, pri = pri + 0.02, role = "head", name = "Head" .. i, needs = "Unit" .. i })
		local used = 2
		if hero then
			B:ell(s * 1.7, s * 0.06, s * 0.5, Geom.mul(flat, at(0, s * 0.25, s * 0.25, rad(-10), 0, 0)), { col = "membrane", mat = "skin", bone = bone, pri = pri + 0.05, role = "wing", name = "Wings" .. i, trail = i <= 2 })
			B:mlimb({ p[1] + s * 0.14, p[2] + s * 0.75, p[3] }, { p[1] + s * 0.3, p[2] + s * 1.05, p[3] + s * 0.05 }, s * 0.1, { col = "horn", mat = "hard", bone = bone, pri = pri + 0.08, role = "horn", name = "Horn" .. i .. "#" }, 0.1)
			B:mell(s * 0.14, s * 0.18, s * 0.08, Geom.mul(flat, at(s * 0.12, s * 0.6, -s * 0.28)), { col = "eyeWhite", mat = "neon", bone = bone, pri = pri + 0.1, role = "eye", name = "Eye" .. i .. "#", noCore = true })
			used += 5
		end
		return used
	end
	if kind == "jelly" then
		local bell = B:ell(s * 1.0, s * 0.73, s * 1.0, flat, { col = "primary", mat = "glass", tr = 0.25, bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		B:sculpt(bell, "s_blob_bell")
		B:ell(s * 0.36, s * 0.3, s * 0.36, Geom.mul(flat, at(0, 0, 0)), { col = "glow", mat = "neon", glow = true, bone = bone, pri = pri + 0.04, role = "core", name = "Glow" .. i, noCore = true, needs = "Unit" .. i })
		local used = 2
		if hero then
			for j = 1, 2 do
				B:ell(s * 0.08, s * 1.1, s * 0.08, Geom.mul(flat, at((j - 1.5) * s * 0.4, -s * 0.75, 0, 0, 0, rad((j - 1.5) * 16))), { col = "secondary", mat = "skin", bone = bone, pri = pri + 0.1 + j * 0.01, role = "tentacle", name = "Tent" .. i .. "_" .. j, needs = "Unit" .. i, mesh = false })
			end
			used += 2
		end
		return used
	end
	if kind == "slime" then
		local dome = B:ell(s * 1.2, s * 0.95, s * 1.1, Geom.mul(flat, at(0, s * 0.47, 0)), { col = if i % 3 == 0 then "secondary" else "primary", mat = "glass", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		B:sculpt(dome, "s_blob_slime")
		local used = 1
		if hero then
			B:mell(s * 0.2, s * 0.26, s * 0.12, Geom.mul(flat, at(s * 0.18, s * 0.62, -s * 0.52)), { col = "pupil", mat = "glass", bone = bone, pri = pri + 0.1, role = "eye", name = "Eye" .. i .. "#", noCore = true })
			used += 2
		end
		return used
	end
	if kind == "shrimp" then
		-- krill / copepod: a curled translucent body with a dark eye; the heroes get feelers
		B:ell(s * 0.38, s * 0.42, s * 1.2, Geom.mul(base, at(0, 0, 0, rad(-14), 0, 0)), { col = "primary", mat = "glass", tr = 0.3, bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		local used = 1
		if hero then
			B:ell(s * 0.3, s * 0.32, s * 0.6, Geom.mul(base, at(0, -s * 0.12, s * 0.62, rad(30), 0, 0)), { col = "primary", mat = "glass", tr = 0.3, bone = bone, pri = pri + 0.03, role = "tail", name = "Tail" .. i })
			B:ball(s * 0.18, Geom.mul(base, at(0, s * 0.1, -s * 0.55)), { col = "black", mat = "glass", bone = bone, pri = pri + 0.05, role = "eye", name = "Eye" .. i, noCore = true })
			B:ell(s * 1.4, s * 0.04, s * 0.06, Geom.mul(base, at(0, s * 0.15, -s * 0.5, 0, 0, rad(8))), { col = "secondary", mat = "skin", bone = bone, pri = pri + 0.1, role = "antenna", name = "Feelers" .. i })
			used += 3
		end
		return used
	end
	if kind == "rat" then
		local g = at(p[1], 0, p[3], 0, yaw * 0.6, 0)
		B:ell(s * 0.7, s * 0.62, s * 1.15, Geom.mul(g, at(0, s * 0.34, 0)), { col = "primary", mat = "fur", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		B:ell(s * 0.14, s * 0.1, s * 1.2, Geom.mul(g, at(0, s * 0.16, s * 1.05, rad(-6), 0, 0)), { col = "inner", mat = "skin", bone = bone, pri = pri + 0.03, role = "tail", name = "Tail" .. i, needs = "Unit" .. i })
		local used = 2
		if hero then
			B:ell(s * 0.42, s * 0.4, s * 0.62, Geom.mul(g, at(0, s * 0.42, -s * 0.66, rad(12), 0, 0)), { col = "primary", mat = "fur", bone = bone, pri = pri + 0.02, role = "head", name = "Head" .. i })
			B:mball(s * 0.26, Geom.mul(g, at(s * 0.16, s * 0.68, -s * 0.52)), { col = "inner", mat = "skin", bone = bone, pri = pri + 0.08, role = "ear", name = "Ear" .. i .. "#" })
			used += 3
		end
		return used
	end
	if kind == "robot" then
		local g = at(p[1], 0, p[3], 0, yaw * 0.6, 0)
		B:block(s * 0.8, s * 0.5, s * 0.9, Geom.mul(g, at(0, s * 0.42, 0)), { col = "primary", mat = "metal", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		B:ell(s * 0.36, s * 0.16, s * 0.08, Geom.mul(g, at(0, s * 0.5, -s * 0.47)), { col = "red", mat = "neon", glow = true, bone = bone, pri = pri + 0.02, role = "eye", name = "Eye" .. i, noCore = true, needs = "Unit" .. i })
		local used = 2
		if hero then
			B:block(s * 1.1, s * 0.2, s * 0.24, Geom.mul(g, at(0, s * 0.12, -s * 0.25)), { col = "dark", mat = "metal", bone = bone, pri = pri + 0.05, role = "limb", name = "LegsA" .. i })
			B:block(s * 1.1, s * 0.2, s * 0.24, Geom.mul(g, at(0, s * 0.1, s * 0.27)), { col = "dark", mat = "metal", bone = bone, pri = pri + 0.06, role = "limb", name = "LegsB" .. i })
			B:limb({ p[1], s * 0.66, p[3] }, { p[1] + s * 0.15, s * 1.15, p[3] + s * 0.1 }, s * 0.07, { col = "dark", mat = "metal", bone = bone, pri = pri + 0.1, role = "antenna", name = "Aerial" .. i, mesh = false }, 0.05)
			used += 3
		end
		return used
	end
	if kind == "ant" or kind == "beetle" then
		-- on the ground: abdomen, thorax / shell, head; heroes add a leg spread and jaws (ants) or legs (beetles)
		local g = at(p[1], 0, p[3], 0, yaw * 0.6, 0)
		local st2 = st or {}
		if kind == "beetle" then
			B:ell(s * 0.95, s * 0.62, s * 1.25, Geom.mul(g, at(0, s * 0.4, 0)), { col = "primary", mat = "metal", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
			B:ell(s * 0.5, s * 0.36, s * 0.42, Geom.mul(g, at(0, s * 0.3, -s * 0.72)), { col = "darker", mat = "hard", bone = bone, pri = pri + 0.02, role = "head", name = "Head" .. i, needs = "Unit" .. i })
			if hero then
				B:ell(s * 1.5, s * 0.1, s * 0.9, Geom.mul(g, at(0, s * 0.14, -s * 0.05)), { col = "dark", mat = "hard", bone = bone, pri = pri + 0.05, role = "limb", name = "Legs" .. i })
				B:ell(s * 0.06, s * 0.6, s * 1.3, Geom.mul(g, at(0, s * 0.7, 0.02)), { col = "darker", mat = "metal", bone = bone, pri = pri + 0.1, role = "detail", name = "Seam" .. i })
				return 4
			end
			return 2
		end
		local abd = st2.abdomen or 1
		B:ell(s * 0.62 * abd, s * 0.55 * abd, s * 0.85 * abd, Geom.mul(g, at(0, s * 0.42 * math.max(1, abd * 0.8), s * (0.55 + (abd - 1) * 0.3))), { col = st2.abdomenCol or "primary", mat = if st2.abdomenCol then "glass" else "hard", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		B:ell(s * 0.5, s * 0.48, s * 0.5, Geom.mul(g, at(0, s * 0.45, -s * 0.48)), { col = st2.headCol or "primary", mat = "hard", bone = bone, pri = pri + 0.02, role = "head", name = "Head" .. i, needs = "Unit" .. i })
		local used = 2
		if hero then
			B:ell(s * 0.36, s * 0.32, s * 0.48, Geom.mul(g, at(0, s * 0.4, 0)), { col = "primary", mat = "hard", bone = bone, pri = pri + 0.03, role = "body", name = "Thorax" .. i, mesh = false })
			B:ell(s * 1.6, s * 0.08, s * 0.95, Geom.mul(g, at(0, s * 0.16, -s * 0.02)), { col = "dark", mat = "hard", bone = bone, pri = pri + 0.05, role = "limb", name = "Legs" .. i })
			B:mlimb({ p[1] + s * 0.12, s * 0.38, p[3] - s * 0.7 }, { p[1] + s * 0.2, s * 0.3, p[3] - s * (if st2.trapJaw then 1.45 else 1.0) }, s * 0.09, { col = "dark", mat = "hard", bone = bone, pri = pri + 0.08, role = "detail", name = "Jaw" .. i .. "#", mesh = false }, 0.05)
			B:mlimb({ p[1] + s * 0.12, s * 0.62, p[3] - s * 0.62 }, { p[1] + s * 0.38, s * 1.05, p[3] - s * 0.95 }, s * 0.06, { col = "dark", mat = "hard", bone = bone, pri = pri + 0.12, role = "antenna", name = "Feeler" .. i .. "#", mesh = false }, 0.05)
			used += 6
			if st2.leaf then
				B:ell(s * 1.0, s * 0.05, s * 0.8, Geom.mul(g, at(0, s * 1.05, -s * 0.3, rad(-25), 0, rad(10))), { col = "leaf", mat = "leaf", bone = bone, pri = pri + 0.15, role = "detail", name = "Leaf" .. i })
				used += 1
			end
		elseif st2.leaf then
			B:ell(s * 0.85, s * 0.05, s * 0.7, Geom.mul(g, at(0, s * 0.95, -s * 0.2, rad(-25), 0, rad(10))), { col = "leaf", mat = "leaf", bone = bone, pri = pri + 0.15, role = "detail", name = "Leaf" .. i })
			used += 1
		end
		return used
	end
	if kind == "hand" then
		-- pale hands rising out of the sea, gripping ladles
		local g = at(p[1], 0, p[3], 0, yaw * 0.4, rad(((i * 13) % 17) - 8))
		B:ell(s * 0.42, s * 1.6, s * 0.38, Geom.mul(g, at(0, s * 0.8, 0)), { col = "white", mat = "skin", bone = bone, pri = pri, role = "limb", name = "Unit" .. i })
		B:ell(s * 0.62, s * 0.7, s * 0.3, Geom.mul(g, at(0, s * 1.75, -s * 0.05)), { col = "white", mat = "skin", bone = bone, pri = pri + 0.02, role = "hand", name = "Palm" .. i, needs = "Unit" .. i })
		local used = 2
		if hero then
			B:limb({ p[1] + s * 0.1, s * 1.5, p[3] - s * 0.3 }, { p[1] + s * 0.2, s * 2.9, p[3] - s * 0.5 }, s * 0.1, { col = "wood", mat = "wood", bone = bone, pri = pri + 0.05, role = "held", name = "Ladle" .. i, mesh = false }, 0.02)
			B:ell(s * 0.55, s * 0.32, s * 0.55, at(p[1] + s * 0.22, s * 3.05, p[3] - s * 0.52), { col = "wood", mat = "wood", bone = bone, pri = pri + 0.06, role = "held", name = "Bowl" .. i })
			for j = 1, 2 do
				B:ell(s * 0.12, s * 0.42, s * 0.12, Geom.mul(g, at((j - 1.5) * s * 0.26, s * 2.25, -s * 0.05, 0, 0, rad((j - 1.5) * 14))), { col = "white", mat = "skin", bone = bone, pri = pri + 0.1 + j * 0.01, role = "hand", name = "Finger" .. i .. "_" .. j })
			end
			used += 4
		end
		return used
	end
	if kind == "bit" then
		-- tumbling things in the word's colours: rounded cubes and balls, a few discs
		local f = (i - 1) % 3
		local col = if i % 2 == 0 then "secondary" else "primary"
		if f == 0 then
			B:block(s * 0.75, s * 0.75, s * 0.75, base, { col = col, mat = "plastic", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		elseif f == 1 then
			B:ball(s * 0.85, base, { col = col, mat = "plastic", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		else
			B:cyl(s * 0.22, s * 0.9, Geom.mul(base, at(0, 0, 0, rad(30), 0, rad(60))), { col = col, mat = "plastic", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
		end
		return 1
	end
	-- insects: plump body; bees/wasps get black bands (thin discs whose rims stand proud of the body) and a
	-- translucent wing pair. Fillers keep body + one band so even the back of the cloud still says "bee".
	local slim = kind == "wasp"
	local bw, bl = s * (if slim then 0.5 else 0.62), s * (if slim then 1.15 else 1.0)
	B:ell(bw, bw, bl, base, { col = "primary", mat = if st and st.metal then "metal" else "fur", bone = bone, pri = pri, role = "body", name = "Unit" .. i })
	local used = 1
	local bands = if not striped then 0 elseif hero then 2 else 1
	for j = 1, bands do
		local z = bl * (if bands == 1 then 0.1 else (-0.08 + (j - 1) * 0.3))
		local k = math.sqrt(math.max(0.1, 1 - (z / (bl / 2)) ^ 2)) * 1.07
		B:ell(bw * k, bw * k, bl * 0.2, Geom.mul(base, at(0, 0, z)), { col = "black", mat = "fur", bone = bone, pri = pri + 0.04 + j * 0.01, role = "detail", name = "Band" .. i .. "_" .. j, needs = "Unit" .. i })
		used += 1
	end
	if hero and slim then
		-- wasp: the orange head ahead of a pinched waist
		B:ell(bw * 0.8, bw * 0.8, bw * 0.75, Geom.mul(base, at(0, 0, -bl * 0.62)), { col = "secondary", mat = "hard", bone = bone, pri = pri + 0.03, role = "head", name = "Head" .. i, needs = "Unit" .. i })
		used += 1
	end
	if hero or not striped then
		B:ell(s * 1.5, s * 0.06, s * 0.48, Geom.mul(base, at(0, bw * 0.5, -s * 0.05, rad(10), 0, 0)),
			{ col = if st and st.wingCol then st.wingCol else "wingGlass", mat = "glass", tr = 0.35, bone = bone, pri = pri + 0.08, role = "wing", name = "Wings" .. i, needs = "Unit" .. i, trail = hero and i == 1 })
		used += 1
	end
	return used
end

-- part cost of a hero / filler unit (plans the count so the budget is spent on units, not dropped)
local COST: { [string]: { number } } = {
	firefly = { 2, 1 }, spark = { 1, 1 }, fish = { 2, 1 }, bat = { 2, 2 }, bird = { 2, 2 }, drone = { 8, 3 }, ghost = { 4, 2 },
	pixie = { 4, 2 }, wyrm = { 4, 2 }, jelly = { 4, 2 }, slime = { 3, 1 }, shrimp = { 4, 1 }, rat = { 5, 2 }, robot = { 5, 2 },
	imp = { 7, 2 }, ant = { 8, 2 }, beetle = { 4, 2 }, hand = { 6, 2 }, bit = { 1, 1 }, person = { 6, 2 }, bug = { 2, 2 }, wasp = { 4, 2 },
}

return function(B: any, ctx: any)
	local detail = ctx.detail
	local kind = unitKind(ctx)
	local id = string.lower(ctx.result.id)
	local hint = string.lower((ctx.result.visual and ctx.result.visual.silhouetteHint) or "")
	local t = ctx.traits
	local beeish = t.stinger or has(id, "bee") or has(id, "wasp") or has(id, "hornet") or has(hint, "wasp")
	if kind == "bug" and (has(id, "wasp") or has(id, "hornet") or has(hint, "wasp")) then
		kind = "wasp"
	end
	local striped = (kind == "bug" or kind == "wasp") and beeish and not has(hint, "metallic") and not has(hint, "shiny black") and not has(hint, "blue%-black")
	local st: any = nil
	if kind == "person" then
		st = personStyle(id, hint)
	elseif kind == "ant" then
		st = {}
		if has(id, "honeypot") then
			st.abdomen, st.abdomenCol = 1.6, "gold"
		elseif has(id, "termite") then
			st.headCol = "darker"
			if has(id, "queen") then
				st.abdomen = 1.3
			end
		elseif has(id, "trap") then
			st.trapJaw = true
		elseif has(id, "leafcutter") or has(hint, "leaf") then
			st.leaf = true
		end
	elseif kind == "bug" or kind == "wasp" then
		st = { metal = has(hint, "metallic") or has(hint, "shiny") or has(id, "robot"), wingCol = if has(hint, "orange wings") then "secondary" else nil }
	end
	local rng = B.rng
	local ground = GROUND[kind] == true
	B.boneIndex.Body.pos = { 0, if ground then 0.6 else 2.4, 0 }
	local avail = ctx.budget - (if ctx.style == "Spectral" then 3 else 0)
	local cost = COST[kind] or COST.bug
	local heroCost, fillCost = cost[1], cost[2]
	if kind == "bug" and striped then
		heroCost, fillCost = 4, 2
	end
	-- heroes first (full detail), then fillers until the budget is spent: more, smaller units read as a crowd
	local heroes = if kind == "spark" then 2 elseif kind == "firefly" then 4 else math.clamp(math.floor(avail / (heroCost * 2.2)), 1, if ground then 3 else 4)
	if kind == "hand" then
		heroes = math.min(heroes, 2)
	end
	local reserve = if kind == "hand" then 1 else 0
	local fillers = math.clamp(math.floor((avail - reserve - heroes * heroCost) / fillCost), 2, 24)
	local n = heroes + fillers
	local s = if n > 10 then 0.62 else 0.72
	if kind == "person" then
		s = 0.95
	elseif ground then
		s = 0.8
	end
	if ground then
		-- rows (people, robots, slimes, hands) or a winding column (ants, beetles, rats), heroes in front
		local column = kind == "ant" or kind == "beetle" or kind == "rat"
		local perRow = math.max(heroes, math.min(5, math.ceil(math.sqrt(n * 1.6))))
		local gap = s * (if kind == "person" then 1.05 else 1.3)
		for i = 1, n do
			local tier = if i <= heroes then 1 else 2
			local p
			if column and kind ~= "rat" then
				local u = (i - 1)
				local lane = (u % 2) - 0.5
				p = { sin(u * 0.45) * 1.1 + lane * gap * 0.9, 0, -2.2 + math.floor(u / 2) * gap * 0.95 + lane * 0.3 }
			else
				local row = if i <= heroes then 0 else 1 + math.floor((i - heroes - 1) / perRow)
				local col = if i <= heroes then i - (heroes + 1) / 2 else ((i - heroes - 1) % perRow) - (perRow - 1) / 2
				local stagger = (row % 2) * 0.5
				p = { (col + stagger) * gap * (if st and st.hug then 0.85 else 1.15) * rng:jitter(1, 0.06), 0, -1.6 + row * gap * 1.1 + rng:range(-0.12, 0.12) }
			end
			if kind == "hand" then
				p[2] = 0
			end
			unit(B, kind, i, p, s * rng:jitter(1, 0.06) * (if tier == 1 then 1.08 else 1), detail, tier, striped, st)
		end
		if kind == "hand" then
			-- the sea they rise from
			B:cyl(0.2, n * 0.6 + 3, at(0, 0.1, 0, 0, 0, rad(90)), { col = { 0.12, 0.3, 0.42 }, mat = "glass", tr = 0.2, pri = 1.05, role = "detail", name = "Sea" })
		end
		if kind == "rat" and has(id, "king") then
			-- the rat king's crown on the lead rat, tails knotted in the middle
			B:cyl(s * 0.3, s * 0.55, at(-(heroes - 1) / 2 * gap * 1.15, s * 1.05, -1.6 - s * 0.6, 0, 0, rad(90)), { col = "gold", mat = "metal", bone = "Unit1", pri = 1.3, role = "hat", name = "Crown" })
			B:ball(s * 0.9, at(0, s * 0.3, 0.2), { col = "inner", mat = "skin", pri = 1.5, role = "detail", name = "Knot" })
		end
		if kind == "person" and st and st.rope and detail >= 1 then
			-- the crew hauls one long rope together
			B:cyl(n * gap * 0.6 + 2, s * 0.14, at(0.3, s * 1.2, -1.6 - s * 0.35, 0, rad(4), 0), { col = "wood", mat = "cloth", pri = 1.6, role = "held", name = "Rope", mesh = false })
		end
		if kind == "person" and (has(id, "clan") or has(id, "guild") or has(id, "legion") or has(id, "army")) and detail >= 2 then
			-- a standard over the crowd
			B:limb({ 0.4, 0, 0.6 }, { 0.4, 4.4, 0.6 }, 0.12, { col = "wood", mat = "wood", pri = 2.2, role = "held", name = "Standard", mesh = false }, 0.02)
			B:block(1.4, 1.0, 0.08, at(1.12, 3.8, 0.6), { col = "secondary", mat = "cloth", pri = 2.3, role = "held", name = "Flag" })
		end
		B:socket("core", at(0, 1.2, 0), "Body")
		B:setRig("gait", if kind == "person" or kind == "hand" then "crowd" else "swarm")
		if t.element == "Light" and kind == "person" then
			B:emit("glints", nil, { socket = "core", rate = 10 })
		end
		return
	end
	-- a squashed, slightly lumpy cloud (wider than tall, denser toward the middle); heroes sit at the front
	for i = 1, n do
		local tier = if i <= heroes then 1 else 2
		local u = (i - 0.5) / n
		local yy = 1 - 2 * u
		local r = math.sqrt(1 - yy * yy)
		local th = i * 2.39996
		local R = (if tier == 1 then 1.5 else 1.9) * rng:jitter(1, 0.22) * (0.75 + 0.25 * r)
		local p = { cos(th) * r * R, 2.4 + yy * 1.15 * rng:jitter(1, 0.15), sin(th) * r * R }
		if tier == 1 then
			p = { (i - (heroes + 1) / 2) * 1.2, 2.4 + ((i % 2) - 0.5) * 0.7, -1.4 - (i % 2) * 0.4 }
		end
		unit(B, kind, i, p, s * rng:jitter(1, 0.12) * (if tier == 1 then 1.15 else 1), detail, tier, striped, st)
	end
	if kind ~= "spark" and kind ~= "fish" and kind ~= "firefly" and kind ~= "bit" and kind ~= "jelly" and kind ~= "ghost" then
		-- drifting specks around the cloud sell the density the part budget cannot
		B:emit("dust", nil, { socket = "core", rate = 24, spread = 1.6 })
	end
	if kind == "pixie" then
		B:emit("glitter", nil, { socket = "core", rate = 16 })
	end
	B:socket("core", at(0, 2.4, 0), "Body")
	B:setRig("gait", "swarm")
end
