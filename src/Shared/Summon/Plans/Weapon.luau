--!strict
-- Weapons and tools, displayed upright and hovering (they spin/bob when summoned): sword, dagger, axe, hammer,
-- mace, club, spear/trident/lance, bow/crossbow, gun/blaster, cannon, shield, staff, wand, scythe, whip,
-- boomerang, shuriken, generic tool. Blades are thin blocks with wedge tips; edges are separate bevel wedges.

local Geom = require(script.Parent.Parent.Geom)
local Heads = require(script.Parent.Parent.Heads)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local ROUTE: { [string]: string } = {
	Sword = "sword", Axe = "axe", Hammer = "hammer", Spear = "spear", Bow = "bow", Gun = "gun", Cannon = "cannon", Shield = "shield", Staff = "staff",
}

local function kindOf(ctx: any): string
	if ctx.kind and ROUTE[ctx.kind] then
		local id = string.lower(ctx.result.id)
		if ctx.kind == "Spear" and (string.find(id, "trident") or string.find(id, "pitchfork")) then
			return "trident"
		elseif ctx.kind == "Staff" and string.find(id, "wand") then
			return "wand"
		elseif ctx.kind == "Sword" and (string.find(id, "dagger") or string.find(id, "knife")) then
			return "dagger"
		elseif ctx.kind == "Hammer" and string.find(id, "mace") then
			return "mace"
		end
		return ROUTE[ctx.kind]
	end
	local t, id = ctx.traits, string.lower(ctx.result.id)
	local function has(w: string): boolean
		return string.find(id, "%f[%a]" .. w) ~= nil
	end
	local hint = string.lower(ctx.result.visual.silhouetteHint or "")
	if t.shield or has("shield") or has("buckler") then
		return "shield"
	elseif t.cannon or has("cannon") or has("mortar") or has("catapult") then
		return "cannon"
	elseif t.crossbow or t.bow or has("bow") or has("longbow") or has("slingshot") then
		return "bow"
	elseif t.gun or has("gun") or has("pistol") or has("rifle") or has("blaster") or has("ray") or has("laser") or has("musket") or has("bazooka") then
		return "gun"
	elseif t.scythe or has("scythe") or has("sickle") then
		return "scythe"
	elseif t.trident or has("trident") or has("pitchfork") then
		return "trident"
	elseif t.spear or has("spear") or has("lance") or has("javelin") or has("pike") or has("halberd") or has("naginata") or has("glaive") then
		return "spear"
	elseif t.hammer or has("hammer") or has("mallet") or has("maul") then
		return "hammer"
	elseif t.mace or has("mace") or has("morning") or has("flail") then
		return "mace"
	elseif t.axe or has("axe") or has("hatchet") or has("tomahawk") then
		return "axe"
	elseif t.staff or has("staff") or has("rod") or has("sceptre") or has("scepter") then
		return "staff"
	elseif t.wand or has("wand") then
		return "wand"
	elseif t.whip or has("whip") then
		return "whip"
	elseif has("boomerang") then
		return "boomerang"
	elseif has("shuriken") or has("star") then
		return "shuriken"
	elseif t.dagger or has("dagger") or has("knife") or has("kunai") or has("dirk") then
		return "dagger"
	elseif t.club or has("club") or has("bat") or has("baton") or has("stick") or string.find(hint, "stick") then
		return "club"
	elseif t.sword or t.blade or has("sword") or has("katana") or has("sabre") or has("saber") or has("blade") or has("rapier") or has("cutlass") or string.find(hint, "blade") then
		return "sword"
	end
	return "sword"
end

local K = {}

local function grip(B: any, y0: number, len: number, w: number)
	B:cyl(len, w, at(0, y0 + len / 2, 0, 0, 0, rad(90)), { col = "secondary", mat = "wood", pri = 1.1, role = "handle", name = "Grip" })
	B:ball(w * 1.5, at(0, y0, 0), { col = "gold", mat = "metal", pri = 1.6, role = "detail", name = "Pommel" })
end

function K.sword(B: any, ctx: any, dagger: boolean)
	local detail = ctx.detail
	local curved = ctx.traits.curved
	local L = if dagger then 2.6 else 4.6
	local bw = if dagger then 0.62 else 0.72
	local y0 = 0.35
	grip(B, y0, 1.2, 0.34)
	B:block(if dagger then 1.2 else 1.9, 0.3, 0.42, at(0, y0 + 1.3, 0), { col = "gold", mat = "metal", pri = 1.2, role = "detail", name = "Guard" })
	local by = y0 + 1.42
	local roll = if curved then rad(-6) else 0
	B:block(bw, L, 0.14, Geom.mul(at(0, by, 0, 0, 0, roll), at(0, L / 2, 0)), { col = "primary", mat = "metal", pri = 1, role = "blade", name = "Blade", trail = true })
	B:wedge(0.14, bw * 1.1, bw, Geom.mul(at(0, by, 0, 0, 0, roll), at(0, L + bw * 0.5 - 0.02, 0, rad(90), rad(90), 0)), { col = "primary", mat = "metal", pri = 1.05, role = "blade", name = "Tip" })
	if detail >= 2 then
		-- fuller (blood groove) as a proud strip on both faces
		B:block(bw * 0.22, L * 0.7, 0.18, Geom.mul(at(0, by, 0, 0, 0, roll), at(0, L * 0.4, 0)), { col = "steel", mat = "metal", pri = 2.4, role = "detail", name = "Fuller" })
	end
	if detail >= 3 then
		B:mball(0.24, at(0.8, y0 + 1.3, 0), { col = "gem", mat = "neon", glow = true, pri = 3.2, role = "gem", name = "GuardGem#" })
	end
	B:socket("muzzle", at(0, by + L, 0), "Body")
	return by + L * 0.5
end

function K.axe(B: any, ctx: any)
	local detail = ctx.detail
	B:cyl(4.6, 0.36, at(0, 2.3, 0, 0, 0, rad(90)), { col = "secondary", mat = "wood", pri = 1.1, role = "handle", name = "Haft" })
	-- crescent head: ellipsoid blade + cheek block
	B:ell(0.3, 2.0, 1.9, at(0, 3.9, -0.95), { col = "primary", mat = "metal", pri = 1, role = "blade", name = "Head", trail = true })
	B:block(0.5, 0.75, 0.75, at(0, 3.9, -0.1), { col = "steel", mat = "metal", pri = 1.2, role = "detail", name = "Cheek" })
	if detail >= 2 or string.find(string.lower(ctx.result.id), "battle") then
		B:ell(0.26, 1.3, 1.1, at(0, 3.9, 0.6), { col = "primary", mat = "metal", pri = 1.8, role = "blade", name = "Back" })
	end
	return 3.0
end

function K.hammer(B: any, ctx: any, mace: boolean)
	local detail = ctx.detail
	B:cyl(3.8, 0.38, at(0, 1.9, 0, 0, 0, rad(90)), { col = "secondary", mat = "wood", pri = 1.1, role = "handle", name = "Haft" })
	if mace then
		B:ball(1.5, at(0, 4.2, 0), { col = "primary", mat = "metal", pri = 1, role = "blade", name = "Head", trail = true })
		for i = 1, (if detail >= 2 then 6 else 4) do
			local a = (i - 0.5) / 6 * math.pi * 2
			B:wedge(0.18, 0.55, 0.4, Geom.mul(at(0, 4.2, 0, 0, a, 0), at(0, 0, -0.85, rad(-90), 0, 0)), { col = "steel", mat = "metal", pri = 1.5 + i * 0.05, role = "spike" })
		end
	else
		B:block(2.2, 1.3, 1.3, at(0, 4.2, 0), { col = "primary", mat = "metal", pri = 1, role = "blade", name = "Head", trail = true })
		B:mcyl(0.2, 1.42, at(1.02, 4.2, 0), { col = "steel", mat = "metal", pri = 1.5, role = "detail", name = "Face#" })
		if detail >= 2 then
			B:block(0.6, 1.36, 1.36, at(0, 4.2, 0), { col = "gold", mat = "metal", pri = 2.0, role = "detail", name = "Band" })
		end
	end
	B:ball(0.5, at(0, 0.0, 0), { col = "gold", mat = "metal", pri = 1.8, role = "detail", name = "Pommel" })
	return 3.0
end

function K.spear(B: any, ctx: any, trident: boolean)
	local detail = ctx.detail
	B:cyl(6.0, 0.28, at(0, 3.0, 0, 0, 0, rad(90)), { col = "secondary", mat = "wood", pri = 1.1, role = "handle", name = "Shaft" })
	if trident then
		B:block(1.6, 0.25, 0.3, at(0, 6.05, 0), { col = "primary", mat = "metal", pri = 1.15, role = "detail", name = "Crossbar" })
		for i = -1, 1 do
			B:cyl(1.1, 0.2, at(i * 0.68, 6.7, 0, 0, 0, rad(90)), { col = "primary", mat = "metal", pri = 1.0 + math.abs(i) * 0.05, role = "blade", name = "Tine" .. (i + 2) })
			B:wedge(0.2, 0.55, 0.35, at(i * 0.68, 7.5, 0, rad(-90), rad(90), 0) :: any, { col = "primary", mat = "metal", pri = 1.2 + math.abs(i) * 0.05, role = "blade", name = "Barb" .. (i + 2), trail = i == 0 })
		end
	else
		-- leaf blade: elongated ellipsoid, flattened
		B:ell(0.75, 1.9, 0.16, at(0, 6.7, 0), { col = "primary", mat = "metal", pri = 1, role = "blade", name = "Head", trail = true })
		if detail >= 2 then
			B:cyl(0.3, 0.42, at(0, 5.85, 0, 0, 0, rad(90)), { col = "gold", mat = "metal", pri = 2.0, role = "detail", name = "Socket" })
			B:limb({ 0, 5.75, 0 }, { 0.2, 5.0, -0.12 }, 0.18, { col = "red", mat = "cloth", pri = 2.6, role = "detail", name = "Tassel", trail = true }, 0.1)
		end
	end
	return 3.8
end

function K.scythe(B: any, ctx: any)
	B:cyl(5.6, 0.3, at(0, 2.8, 0, 0, 0, rad(-6) + rad(90)), { col = "secondary", mat = "wood", pri = 1.1, role = "handle", name = "Snath" })
	-- curved blade from three tapering segments
	local pts = { { 0.25, 5.4, 0 }, { 0.5, 5.6, -1.1 }, { 0.2, 5.3, -2.2 }, { -0.35, 4.6, -2.9 } }
	for i = 1, 3 do
		B:limb(pts[i], pts[i + 1], 0.75 - i * 0.18, { col = "primary", mat = "metal", pri = 1 + i * 0.05, role = "blade", name = "Blade" .. i, trail = i == 3, depth = 0.1 }, 0.25)
	end
	return 3.4
end

function K.bow(B: any, ctx: any, crossbow: boolean)
	local detail = ctx.detail
	if crossbow then
		B:block(0.42, 0.42, 3.2, at(0, 2.0, 0.3), { col = "secondary", mat = "wood", pri = 1.1, role = "handle", name = "Stock" })
	end
	-- limbs: two curved segments each side of the grip
	local cy = if crossbow then 2.0 else 2.6
	local axisZ = crossbow
	local function P(u: number, v: number): { number }
		-- u: along the limb, v: curve depth
		if axisZ then
			return { u, cy, -1.2 + v }
		end
		return { 0, cy + u, v }
	end
	for side = -1, 1, 2 do
		local a, b, c = P(side * 0.4, 0), P(side * 1.5, 0.35), P(side * 2.4, 0.9)
		B:limb(a, b, 0.3, { col = "primary", mat = "wood", pri = 1, role = "blade", name = "LimbA" .. side }, 0.2)
		B:limb(b, c, 0.24, { col = "primary", mat = "wood", pri = 1.05, role = "blade", name = "LimbB" .. side, trail = true }, 0.2)
	end
	local top, bot = P(2.4, 0.9), P(-2.4, 0.9)
	B:rod(top, bot, 0.06, { col = "white", mat = "cloth", pri = 1.3, role = "detail", name = "String" })
	if not crossbow then
		B:cyl(0.9, 0.42, at(0, cy, -0.02, 0, 0, rad(90)), { col = "darkWood", mat = "cloth", pri = 1.2, role = "handle", name = "Grip" })
	end
	if detail >= 2 then
		-- nocked arrow
		local z0 = if crossbow then 1.0 else 0.9
		B:cyl(3.4, 0.1, at(0, if crossbow then 2.3 else cy, z0 - 1.7, 0, rad(90), 0), { col = "darkWood", mat = "wood", pri = 2.0, role = "detail", name = "Arrow" })
		B:wedge(0.08, 0.3, 0.32, at(0, if crossbow then 2.3 else cy, z0 - 3.55, rad(90), 0, 0), { col = "steel", mat = "metal", pri = 2.2, role = "blade", name = "Arrowhead" })
	end
	B:socket("muzzle", at(0, cy, -1.5), "Body")
	return cy
end

function K.gun(B: any, ctx: any)
	local detail = ctx.detail
	local scifi = ctx.traits.scifi or string.find(string.lower(ctx.result.id), "blast") or string.find(string.lower(ctx.result.id), "ray") or string.find(string.lower(ctx.result.id), "laser")
	B:block(0.7, 1.0, 3.0, at(0, 2.2, 0), { col = "primary", mat = "metal", pri = 1, role = "body", name = "Receiver" })
	B:cyl(2.6, 0.42, at(0, 2.35, -2.6, 0, rad(90), 0), { col = "dark", mat = "metal", pri = 1.05, role = "cannon", name = "Barrel" })
	B:block(0.55, 1.5, 0.75, at(0, 1.3, 0.9, rad(-14), 0, 0), { col = "secondary", mat = "wood", pri = 1.1, role = "handle", name = "Grip" })
	if scifi then
		for i = 1, 3 do
			B:cyl(0.16, 0.7 - i * 0.05, at(0, 2.35, -1.6 - i * 0.55, 0, rad(90), 0), { col = "glow", mat = "neon", glow = true, pri = 1.5 + i * 0.1, role = "gem", name = "Coil" .. i, noCore = true })
		end
	else
		B:block(0.6, 0.5, 1.6, at(0, 2.85, 0.2), { col = "dark", mat = "metal", pri = 1.4, role = "detail", name = "Top" })
	end
	if detail >= 2 then
		B:limb({ 0, 1.8, 0.35 }, { 0, 1.35, 0.15 }, 0.12, { col = "dark", mat = "metal", pri = 2.4, role = "detail", name = "Trigger" }, 0.1)
		B:cyl(0.3, 0.55, at(0, 2.35, -3.95, 0, rad(90), 0), { col = "dark", mat = "metal", pri = 2.5, role = "cannon", name = "Muzzle" })
	end
	B:socket("muzzle", at(0, 2.35, -4.2), "Body")
	return 2.2
end

function K.cannon(B: any, ctx: any)
	local detail = ctx.detail
	B:block(2.2, 0.8, 3.0, at(0, 1.1, 0.2), { col = "secondary", mat = "wood", pri = 1.1, role = "body", name = "Carriage" })
	B:bone("Barrel", "Body", 0, 1.9, 0.2)
	B:setRig("barrel", "Barrel")
	B:cyl(4.2, 1.3, at(0, 2.05, -0.5, 0, rad(90), rad(-12)), { col = "primary", mat = "metal", bone = "Barrel", pri = 1, role = "cannon", name = "Barrel" })
	B:ball(1.5, at(0, 1.7, 1.45), { col = "primary", mat = "metal", bone = "Barrel", pri = 1.2, role = "cannon", name = "Breech" })
	B:cyl(0.4, 1.6, at(0, 2.5, -2.55, 0, rad(90), rad(-12)), { col = "primary", mat = "metal", bone = "Barrel", pri = 1.3, role = "cannon", name = "Muzzle" })
	for i, z in { -0.8, 1.2 } do
		local bn = B:mirrorBone("Wheel" .. i .. "#", "Body", 1.25, 0.9, z)
		B:addRig("wheels", { bone = bn, r = 0.9 })
		B:mcyl(0.3, 1.8, at(1.25, 0.9, z), { col = "darkWood", mat = "wood", bone = "Wheel" .. i .. "#", pri = 1.2 + i * 0.05, role = "wheel", name = "Wheel" .. i .. "#" })
		if detail >= 2 then
			B:mcyl(0.36, 0.5, at(1.25, 0.9, z), { col = "dark", mat = "metal", bone = "Wheel" .. i .. "#", pri = 2.4 + i * 0.05, role = "wheel" })
		end
	end
	if detail >= 3 then
		B:ball(0.9, at(1.4, 0.45, 2.3), { col = "dark", mat = "metal", pri = 3.4, role = "detail", name = "Cannonball" })
	end
	B:socket("muzzle", at(0, 2.55, -2.85), "Barrel")
	return 2.0
end

function K.shield(B: any, ctx: any)
	local detail = ctx.detail
	local round = string.find(string.lower(ctx.result.visual.silhouetteHint or ""), "round") ~= nil or string.find(string.lower(ctx.result.id), "buckler") ~= nil
	if round then
		B:cyl(0.35, 4.0, at(0, 2.4, 0, 0, rad(90), 0), { col = "primary", mat = "wood", pri = 1, role = "body", name = "Board" })
		B:cyl(0.4, 4.25, at(0, 2.4, 0.02, 0, rad(90), 0), { col = "secondary", mat = "metal", pri = 1.1, role = "detail", name = "Rim" })
	else
		-- heater shield: block + downward point from two wedges
		B:block(3.4, 2.4, 0.36, at(0, 3.2, 0), { col = "primary", mat = "metal", pri = 1, role = "body", name = "Board" })
		B:mwedge(0.34, 1.7 - 0.02, 1.7, at(0.85 - 0.02, 1.15, 0, rad(-90), rad(-90), 0), { col = "primary", mat = "metal", pri = 1.05, role = "body", name = "Point#" })
	end
	B:ell(1.0, 1.0, 0.7, at(0, 2.6, -0.2), { col = "secondary", mat = "metal", pri = 1.2, role = "detail", name = "Boss" })
	if round and detail >= 1 then
		-- plank seams and a ring of rivets: a round shield that reads as built, not a disc
		for i = -1, 1, 2 do
			B:block(0.07, 3.3 - (if i == 0 then 0 else 0.5), 0.1, at(i * 0.68, 2.4, -0.2), { col = "darkWood", mat = "wood", pri = 1.9, role = "detail", name = "Seam" .. (if i > 0 then "R" else "L") })
		end
		for i = 1, (if detail >= 2 then 6 else 4) do
			local a = (i - 0.5) / (if detail >= 2 then 6 else 4) * math.pi * 2
			B:ball(0.26, at(math.sin(a) * 1.72, 2.4 + math.cos(a) * 1.72, -0.2), { col = "metal", mat = "metal", pri = 2.1 + i * 0.02, role = "detail", name = "Rivet" .. i })
		end
	end
	if detail >= 2 and not round then
		B:block(0.5, 3.2, 0.42, at(0, 2.9, 0), { col = "secondary", mat = "metal", pri = 2.0, role = "detail", name = "Pale" })
		B:block(3.44, 0.5, 0.42, at(0, 3.5, 0), { col = "secondary", mat = "metal", pri = 2.05, role = "detail", name = "Fess" })
	end
	return 2.6
end

function K.staff(B: any, ctx: any, wand: boolean)
	local detail = ctx.detail
	local L = if wand then 3.0 else 6.0
	B:cyl(L, if wand then 0.2 else 0.34, at(0, L / 2, 0, 0, 0, rad(90)), { col = "secondary", mat = "wood", pri = 1.05, role = "handle", name = "Shaft" })
	if wand then
		B:ball(0.6, at(0, L + 0.2, 0), { col = "glow", mat = "neon", glow = true, pri = 1, role = "gem", name = "Tip", trail = true, noCore = true })
		if string.find(string.lower(ctx.result.visual.silhouetteHint or ""), "star") then
			for i = 1, 5 do
				local a = (i - 1) / 5 * math.pi * 2
				B:wedge(0.12, 0.45, 0.3, Geom.mul(at(0, L + 0.2, 0, 0, 0, a), at(0, 0.45, 0, 0, rad(90), 0)), { col = "gold", mat = "neon", glow = true, pri = 1.4 + i * 0.05, role = "gem", noCore = true })
			end
		end
	else
		-- claw cradle holding an orb
		for i = 1, (if detail >= 2 then 3 else 2) do
			local a = (i - 1) / 3 * math.pi * 2
			B:limb({ sin(a) * 0.2, L - 0.1, cos(a) * 0.2 }, { sin(a) * 0.7, L + 0.9, cos(a) * 0.7 }, 0.2, { col = "secondary", mat = "wood", pri = 1.3 + i * 0.05, role = "detail", name = "Claw" .. i }, 0.15)
		end
		B:ball(1.1, at(0, L + 0.65, 0), { col = "glow", mat = "neon", glow = true, pri = 1, role = "gem", name = "Orb", trail = true, noCore = true })
		table.insert(B.lights, { kind = "PointLight", colour = { 0.8, 0.6, 1 }, brightness = 1.5, range = 0.8, socket = "muzzle", shadows = false })
	end
	B:socket("muzzle", at(0, L + 0.65, 0), "Body")
	return L * 0.6
end

function K.club(B: any, ctx: any)
	B:limb({ 0, 0, 0 }, { 0, 4.8, 0 }, 1.0, { col = "primary", mat = "wood", pri = 1, role = "blade", name = "Club", trail = true }, 0.05)
	B:limb({ 0, 0.2, 0 }, { 0, 1.6, 0 }, 0.5, { col = "secondary", mat = "cloth", pri = 1.2, role = "handle", name = "Wrap" }, 0.05)
	return 2.6
end

function K.whip(B: any, ctx: any)
	B:cyl(1.4, 0.35, at(0, 0.7, 0, 0, 0, rad(90)), { col = "secondary", mat = "wood", pri = 1.1, role = "handle", name = "Handle" })
	local x, y = 0, 1.4
	local bones = {}
	for i = 1, 4 do
		local bn = B:bone("Tail" .. i, if i == 1 then "Body" else "Tail" .. (i - 1), x, y, 0)
		table.insert(bones, bn)
		B:addRig("tail", bn)
		local nx, ny = x + sin(i * 0.9) * 0.9, y + 0.9 - i * 0.1
		B:limb({ x, y, 0 }, { nx, ny, 0 }, 0.22 - i * 0.03, { col = "primary", mat = "skin", bone = bn, pri = 1 + i * 0.1, role = "blade", trail = i == 4 }, 0.25)
		x, y = nx, ny
	end
	return 2
end

function K.boomerang(B: any, ctx: any)
	B:block(0.7, 2.6, 0.2, at(-0.6, 2.4, 0, 0, 0, rad(40)), { col = "primary", mat = "wood", pri = 1, role = "blade", name = "ArmA", trail = true })
	B:block(0.7, 2.6, 0.18, at(0.6, 2.4, 0.005, 0, 0, rad(-40)), { col = "primary", mat = "wood", pri = 1.05, role = "blade", name = "ArmB", trail = true })
	return 2.4
end

function K.shuriken(B: any, ctx: any)
	for i = 1, 4 do
		local a = (i - 1) * math.pi / 2
		B:wedge(0.12 + i * 0.01, 1.4, 0.9, Geom.mul(at(0, 2.4, 0, 0, 0, a), at(0.45, 0.6, 0, 0, rad(90), 0)), { col = "primary", mat = "metal", pri = 1 + i * 0.02, role = "blade", name = "Point" .. i, trail = i == 1 })
	end
	B:cyl(0.24, 0.9, at(0, 2.4, 0, 0, rad(90), 0), { col = "dark", mat = "metal", pri = 1.1, role = "detail", name = "Hub" })
	return 2.4
end

return function(B: any, ctx: any)
	local kind = kindOf(ctx)
	local fy
	if kind == "dagger" then
		fy = K.sword(B, ctx, true)
	elseif kind == "mace" then
		fy = K.hammer(B, ctx, true)
	elseif kind == "trident" then
		fy = K.spear(B, ctx, true)
	elseif kind == "wand" then
		fy = K.staff(B, ctx, true)
	elseif kind == "bow" then
		fy = K.bow(B, ctx, ctx.traits.crossbow or string.find(string.lower(ctx.result.id), "crossbow") ~= nil)
	else
		local f = (K :: any)[kind] or K.sword
		fy = f(B, ctx, false)
	end
	B.boneIndex.Body.pos = { 0, fy or 2, 0 }
	if Heads.wantsFace(B, ctx.traits) then
		-- face frames per weapon: on the broad, viewer-facing surface (-Z out of the face)
		local side = rad(-90) -- yaw that turns the face toward +X (axe/scythe/gun broad sides)
		local F: { [string]: { any } } = {
			sword = { at(0, 3.4, -0.08), 0.62 }, dagger = { at(0, 2.5, -0.08), 0.52 },
			axe = { at(0.16, 3.9, -0.95, 0, side, 0), 1.3 }, hammer = { at(0, 4.2, -0.66), 1.2 }, mace = { at(0, 4.2, -0.76), 0.9, 0.6 },
			spear = { at(0, 6.6, -0.09), 0.6 }, trident = { at(0, 6.05, -0.16), 1.2 }, scythe = { at(0.06, 2.6, -0.16), 0.32 },
			bow = { at(0, 2.6, -0.22), 0.5 }, gun = { at(0.36, 2.2, 0.1, 0, side, 0), 1.6 }, cannon = { at(0, 1.1, -1.31), 1.6 },
			shield = { at(0, 3.75, -0.19), 2.0 }, staff = { at(0, 6.65, -0.55), 0.9, 0.8 }, wand = { at(0, 3.2, -0.3), 0.5, 0.8 },
			club = { at(0, 3.6, -0.45), 0.8, 0.6 }, whip = { at(0, 0.7, -0.18), 0.4 }, boomerang = { at(0, 2.4, -0.11), 0.8 },
			shuriken = { at(0, 2.4, -0.13), 0.8 },
		}
		local f = F[kind] or F.sword
		Heads.objectFace(B, ctx.traits, f[1], f[2], "Body", { eye = 0.3, curve = f[3] })
	end
	B:socket("core", at(0, fy or 2, 0), "Body")
	local _ = cos(0)
	B:setRig("gait", if kind == "cannon" then "static" else "hover")
end
