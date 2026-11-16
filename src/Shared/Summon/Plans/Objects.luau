--!strict
-- Everyday objects: Furniture (chair, table, bed, sofa, lamp, bookshelf, throne), Appliance (toaster, fridge,
-- tv, microwave, washing machine, computer, oven, fan, vacuum), Container (box/crate, chest, barrel, jar,
-- bucket, trash can, backpack, vase, bottle, mug, present) and a generic chunky prop. Faces only with a mood.

local Geom = require(script.Parent.Parent.Geom)
local Heads = require(script.Parent.Parent.Heads)

local at = Geom.at
local rad = math.rad

local function has(id: string, w: string): boolean
	return string.find(id, "%f[%a]" .. w) ~= nil
end

local function face(B: any, ctx: any, cf: any, w: number, o: any?)
	if Heads.wantsFace(B, ctx.traits) then
		Heads.objectFace(B, ctx.traits, cf, w, "Body", o)
	end
end

local K = {}

-- legs: four posts under a rectangle
local function legs4(B: any, w: number, d: number, h: number, t: number, col: string, pri: number)
	B:mblock(t, h, t, at(w / 2 - t, h / 2, -d / 2 + t), { col = col, mat = "wood", pri = pri, role = "limb", name = "LegF#" })
	B:mblock(t, h, t, at(w / 2 - t, h / 2, d / 2 - t), { col = col, mat = "wood", pri = pri + 0.05, role = "limb", name = "LegB#" })
end

function K.chair(B: any, ctx: any, throne: boolean)
	local s = if throne then 1.3 else 1
	B:block(2.0 * s, 0.3, 2.0 * s, at(0, 1.6, 0), { col = "primary", mat = "wood", pri = 1, role = "body", name = "Seat" })
	B:block(2.0 * s - 0.04, 2.4 * s, 0.3, at(0, 1.75 + 1.2 * s, 0.85 * s, rad(-6), 0, 0), { col = "primary", mat = "wood", pri = 1.05, role = "body", name = "Back" })
	legs4(B, 2.0 * s - 0.02, 2.0 * s - 0.02, 1.48, 0.28, "darkWood", 1.2)
	if throne then
		B:ell(1.7, 0.4, 1.6, at(0, 1.85, -0.05), { col = "red", mat = "cloth", pri = 1.5, role = "detail", name = "Cushion" })
		B:mblock(0.3, 0.9, 2.2, at(1.2, 2.2, 0.05), { col = "gold", mat = "metal", pri = 1.6, role = "detail", name = "Arm#" })
		B:ball(0.5, at(0, 4.6, 1.0), { col = "red", mat = "neon", glow = true, pri = 2.2, role = "gem" })
	end
	face(B, ctx, at(0, 2.7, 0.66, rad(-6), 0, 0), 1.6)
end

function K.table(B: any, ctx: any)
	B:block(3.6, 0.3, 2.4, at(0, 2.0, 0), { col = "primary", mat = "wood", pri = 1, role = "body", name = "Top" })
	legs4(B, 3.3, 2.1, 1.86, 0.3, "darkWood", 1.1)
	face(B, ctx, at(0, 2.0, -1.22), 1.6)
end

function K.bed(B: any, ctx: any)
	B:block(2.8, 0.7, 4.4, at(0, 0.75, 0), { col = "darkWood", mat = "wood", pri = 1.05, role = "body", name = "Frame" })
	B:block(2.6, 0.5, 4.2, at(0, 1.33, 0.02), { col = "white", mat = "cloth", pri = 1.1, role = "body", name = "Mattress" })
	B:block(2.9, 1.9, 0.3, at(0, 1.35, 2.25), { col = "darkWood", mat = "wood", pri = 1.0, role = "body", name = "Headboard" })
	B:ell(1.9, 0.5, 0.9, at(0, 1.75, 1.5), { col = "white", mat = "cloth", pri = 1.4, role = "detail", name = "Pillow" })
	B:block(2.7, 0.2, 2.6, at(0, 1.62, -0.75, rad(1), 0, 0), { col = "primary", mat = "cloth", pri = 1.3, role = "detail", name = "Blanket" })
	face(B, ctx, at(0, 2.0, 2.08), 1.8)
end

function K.sofa(B: any, ctx: any)
	B:block(4.0, 1.0, 1.9, at(0, 0.9, 0), { col = "primary", mat = "cloth", pri = 1, role = "body", name = "Base" })
	B:block(4.0, 1.5, 0.6, at(0, 1.9, 0.68, rad(-8), 0, 0), { col = "primary", mat = "cloth", pri = 1.05, role = "body", name = "Back" })
	B:mell(0.7, 1.4, 2.0, at(1.95, 1.4, 0), { col = "primary", mat = "cloth", pri = 1.1, role = "body", name = "Arm#" })
	B:mell(1.65, 0.5, 1.5, at(0.85, 1.48, -0.1), { col = "secondary", mat = "cloth", pri = 1.4, role = "detail", name = "Cushion#" })
	face(B, ctx, at(0, 2.0, 0.36, rad(-8), 0, 0), 2.2)
end

function K.lamp(B: any, ctx: any)
	B:cyl(0.3, 1.6, at(0, 0.15, 0, 0, 0, rad(90)), { col = "dark", mat = "metal", pri = 1.1, role = "body", name = "Foot" })
	B:cyl(3.4, 0.2, at(0, 1.9, 0, 0, 0, rad(90)), { col = "dark", mat = "metal", pri = 1.05, role = "body", name = "Pole" })
	B:limb({ 0, 3.5, 0 }, { 0, 4.6, 0 }, 1.8, { col = "primary", mat = "cloth", pri = 1, role = "body", name = "Shade" }, 0.0)
	B:ball(0.7, at(0, 3.4, 0), { col = "glow", mat = "neon", glow = true, pri = 1.3, role = "gem", name = "Bulb", noCore = true })
	table.insert(B.lights, { kind = "PointLight", colour = { 1, 0.9, 0.7 }, brightness = 1.5, range = 1.2, socket = "core", shadows = false })
	B:socket("core", at(0, 3.5, 0), "Body")
	face(B, ctx, at(0, 4.0, -0.8, rad(-10), 0, 0), 1.1, { curve = 0.4 })
end

function K.bookshelf(B: any, ctx: any)
	local detail = ctx.detail
	B:block(2.8, 4.0, 1.0, at(0, 2.0, 0.05), { col = "darkWood", mat = "wood", pri = 1, role = "body", name = "Case" })
	for i = 1, (if detail >= 2 then 3 else 2) do
		local y = 0.6 + (i - 1) * 1.25
		B:block(2.4, 0.95, 0.75, at(0, y + 0.5, -0.09), { col = if i % 2 == 0 then "secondary" else "primary", mat = "cloth", pri = 1.2 + i * 0.05, role = "detail", name = "Books" .. i })
	end
	face(B, ctx, at(0, 3.0, -0.49), 1.8)
end

function K.toaster(B: any, ctx: any)
	local detail = ctx.detail
	B:block(2.8, 1.9, 1.7, at(0, 1.05, 0), { col = "primary", mat = "metal", pri = 1, role = "body", name = "Body" })
	B:ell(2.9, 0.6, 1.8, at(0, 1.95, 0), { col = "primary", mat = "metal", pri = 1.1, role = "body", name = "Top" })
	B:mblock(0.36, 0.3, 1.4, at(0.55, 2.2, 0), { col = "darker", mat = "metal", pri = 1.4, role = "detail", name = "Slot#" })
	B:mblock(0.32, 0.5, 1.3, at(0.55, 2.45, 0), { col = "wood", mat = "skin", pri = 1.5, role = "detail", name = "Toast#" })
	if detail >= 2 then
		B:block(0.2, 0.5, 0.35, at(1.45, 1.4, 0), { col = "dark", mat = "plastic", pri = 2.2, role = "detail", name = "Lever" })
		B:mblock(0.35, 0.16, 0.16, at(1.0, 0.08, 0.6), { col = "dark", mat = "plastic", pri = 3.0, role = "detail", name = "Foot#" })
	end
	face(B, ctx, at(0, 1.05, -0.87), 2.2)
	B:socket("core", at(0, 1.2, 0), "Body")
end

function K.box(B: any, ctx: any, kind: string)
	local detail = ctx.detail
	if kind == "fridge" then
		B:block(2.2, 4.4, 2.0, at(0, 2.2, 0), { col = "white", mat = "metal", pri = 1, role = "body", name = "Body" })
		B:block(2.12, 0.08, 0.1, at(0, 3.0, -1.02), { col = "steel", mat = "metal", pri = 1.4, role = "detail", name = "Split" })
		B:mblock(0.12, 0.9, 0.16, at(0.85, 3.6, -1.06), { col = "steel", mat = "metal", pri = 1.6, role = "detail", name = "Handle#" })
		face(B, ctx, at(0, 1.6, -1.04), 1.8)
	elseif kind == "tv" or kind == "computer" then
		B:block(3.6, 2.3, 0.4, at(0, 2.2, 0), { col = "black", mat = "plastic", pri = 1, role = "body", name = "Frame" })
		B:block(3.3, 2.0, 0.1, at(0, 2.2, -0.21), { col = "glow", mat = "neon", glow = true, pri = 1.1, role = "gem", name = "Screen", noCore = true })
		B:block(0.4, 0.9, 0.4, at(0, 0.6, 0.05), { col = "black", mat = "plastic", pri = 1.2, role = "body", name = "Stand" })
		B:block(1.6, 0.18, 0.9, at(0, 0.12, 0.05), { col = "black", mat = "plastic", pri = 1.3, role = "body", name = "Foot" })
		face(B, ctx, at(0, 2.2, -0.27), 2.6, { kind = "robot" })
	elseif kind == "washing" or kind == "oven" or kind == "microwave" then
		local h = if kind == "microwave" then 1.6 else 3.0
		B:block(2.6, h, 2.2, at(0, h / 2, 0), { col = "white", mat = "metal", pri = 1, role = "body", name = "Body" })
		if kind == "washing" then
			B:cyl(0.16, 1.6, at(0, h * 0.42, -1.12, 0, rad(90), 0), { col = "steel", mat = "metal", pri = 1.2, role = "detail", name = "DoorRing" })
			B:cyl(0.2, 1.2, at(0, h * 0.42, -1.12, 0, rad(90), 0), { col = "glass", mat = "glass", pri = 1.3, role = "window", name = "DoorGlass" })
		else
			B:block(1.9, h * 0.6, 0.1, at(-0.25, h * 0.45, -1.12), { col = "dark", mat = "glass", pri = 1.2, role = "window", name = "Door" })
		end
		B:block(2.4, 0.4, 0.12, at(0, h - 0.3, -1.12), { col = "steel", mat = "metal", pri = 1.5, role = "detail", name = "Panel" })
		face(B, ctx, at(0, h * 0.45, -1.2), 1.7)
	elseif kind == "fan" then
		B:cyl(0.25, 1.4, at(0, 0.12, 0, 0, 0, rad(90)), { col = "dark", mat = "plastic", pri = 1.1, role = "body", name = "Foot" })
		B:cyl(2.4, 0.22, at(0, 1.3, 0, 0, 0, rad(90)), { col = "dark", mat = "plastic", pri = 1.05, role = "body", name = "Pole" })
		B:ell(0.8, 0.8, 1.0, at(0, 2.7, 0.2), { col = "primary", mat = "plastic", pri = 1, role = "body", name = "Motor" })
		B:bone("Blades", "Body", 0, 2.7, -0.4)
		B:addRig("rotors", { bone = "Blades", axis = "Z", speed = 18 })
		for i = 1, 3 do
			local a = (i - 1) * math.pi * 2 / 3
			B:ell(0.6, 1.3, 0.08 + i * 0.01, Geom.mul(at(0, 2.7, -0.42 - i * 0.012, 0, 0, a), at(0, 0.62, 0, 0, rad(18), 0)), { col = "secondary", mat = "plastic", bone = "Blades", pri = 1.2 + i * 0.02, role = "rotor" })
		end
		face(B, ctx, at(0, 2.7, -0.3), 0.7)
	else -- vacuum / generic appliance
		B:cyl(0.9, 2.6, at(0, 0.55, 0, 0, 0, rad(90)), { col = "primary", mat = "plastic", pri = 1, role = "body", name = "Body" })
		B:cyl(0.12, 2.0, at(0, 1.06, 0, 0, 0, rad(90)), { col = "secondary", mat = "plastic", pri = 1.4, role = "detail", name = "Lid" })
		face(B, ctx, at(0, 0.6, -1.32), 1.4, { curve = 0.3 })
	end
	local _ = detail
end

function K.container(B: any, ctx: any, kind: string)
	local detail = ctx.detail
	if kind == "barrel" then
		B:ell(2.2, 3.0, 2.2, at(0, 1.5, 0), { col = "wood", mat = "wood", pri = 1, role = "body", name = "Staves" })
		for i = 1, (if detail >= 2 then 2 else 1) do
			B:cyl(0.2, 2.1, at(0, 0.6 + (i - 1) * 1.8, 0, 0, 0, rad(90)), { col = "dark", mat = "metal", pri = 1.3 + i * 0.1, role = "detail", name = "Hoop" .. i })
		end
		B:cyl(0.1, 1.7, at(0, 2.95, 0, 0, 0, rad(90)), { col = "darkWood", mat = "wood", pri = 1.5, role = "detail", name = "Lid" })
		face(B, ctx, at(0, 1.6, -1.08), 1.4, { curve = 0.4 })
	elseif kind == "chest" then
		B:block(3.0, 1.6, 2.0, at(0, 0.8, 0), { col = "wood", mat = "wood", pri = 1, role = "body", name = "Box" })
		B:cyl(3.0 - 0.04, 2.0, at(0, 1.6, 0), { col = "wood", mat = "wood", pri = 1.05, role = "body", name = "Lid" })
		B:mblock(0.25, 2.66, 2.06, at(0.9, 1.3, 0), { col = "gold", mat = "metal", pri = 1.3, role = "detail", name = "Band#" })
		B:block(0.45, 0.55, 0.2, at(0, 1.4, -1.08), { col = "gold", mat = "metal", pri = 1.4, role = "detail", name = "Lock" })
		face(B, ctx, at(0, 0.8, -1.04), 2.0)
	elseif kind == "jar" or kind == "vase" or kind == "bottle" or kind == "mug" or kind == "bucket" or kind == "can" then
		local h = if kind == "bottle" then 3.2 elseif kind == "mug" then 1.8 else 2.6
		local w = if kind == "bottle" then 1.4 else 2.0
		B:cyl(h, w, at(0, h / 2, 0, 0, 0, rad(90)), { col = "primary", mat = if kind == "jar" or kind == "bottle" then "glass" else "plastic", pri = 1, role = "body", name = "Body" })
		if kind == "bottle" then
			B:limb({ 0, h - 0.1, 0 }, { 0, h + 1.2, 0 }, 0.6, { col = "primary", mat = "glass", pri = 1.1, role = "body", name = "Neck" }, 0.02)
			B:cyl(0.35, 0.5, at(0, h + 1.25, 0, 0, 0, rad(90)), { col = "secondary", mat = "plastic", pri = 1.3, role = "detail", name = "Cap" })
		elseif kind == "mug" then
			B:limb({ w / 2, h * 0.8, 0 }, { w / 2 + 0.55, h * 0.45, 0 }, 0.3, { col = "primary", mat = "plastic", pri = 1.2, role = "detail", name = "Handle" }, 0.3)
			B:limb({ w / 2 + 0.55, h * 0.45, 0 }, { w / 2, h * 0.15, 0 }, 0.3, { col = "primary", mat = "plastic", pri = 1.25, role = "detail", name = "Handle2" }, 0.3)
		else
			B:cyl(0.3, w + 0.12, at(0, h - 0.1, 0, 0, 0, rad(90)), { col = "secondary", mat = "plastic", pri = 1.2, role = "detail", name = "Rim" })
		end
		face(B, ctx, at(0, h * 0.48, -w / 2 - 0.02), w * 0.85, { curve = 0.45 })
	elseif kind == "backpack" then
		B:ell(2.0, 2.6, 1.3, at(0, 1.4, 0), { col = "primary", mat = "cloth", pri = 1, role = "body", name = "Pack" })
		B:ell(1.5, 1.0, 0.7, at(0, 0.95, -0.5), { col = "secondary", mat = "cloth", pri = 1.2, role = "detail", name = "Pocket" })
		B:mlimb({ 0.55, 2.5, 0.45 }, { 0.6, 0.6, 0.62 }, 0.22, { col = "dark", mat = "cloth", pri = 1.5, role = "detail", name = "Strap#", depth = 0.1 }, 0.1)
		face(B, ctx, at(0, 1.85, -0.64), 1.2, { curve = 0.4 })
	else -- crate / box / present
		local present = has(string.lower(ctx.result.id), "present") or has(string.lower(ctx.result.id), "gift")
		B:block(2.4, 2.4, 2.4, at(0, 1.2, 0), { col = "primary", mat = if present then "plastic" else "wood", pri = 1, role = "body", name = "Box" })
		if present then
			B:block(2.46, 2.46, 0.4, at(0, 1.2, 0), { col = "secondary", mat = "cloth", pri = 1.2, role = "detail", name = "RibbonA" })
			B:block(0.4, 2.48, 2.5, at(0, 1.2, 0), { col = "secondary", mat = "cloth", pri = 1.25, role = "detail", name = "RibbonB" })
			B:mell(0.9, 0.55, 0.3, at(0.42, 2.6, 0, 0, 0, rad(25)), { col = "secondary", mat = "cloth", pri = 1.4, role = "detail", name = "Bow#" })
		elseif detail >= 1 then
			B:block(2.46, 0.3, 2.46, at(0, 2.2, 0), { col = "darkWood", mat = "wood", pri = 1.3, role = "detail", name = "BandTop" })
			B:block(2.46, 0.3, 2.46, at(0, 0.25, 0), { col = "darkWood", mat = "wood", pri = 1.35, role = "detail", name = "BandLow" })
			B:block(0.3, 2.46, 2.46 + 0.04, at(0, 1.2, 0, rad(45), 0, 0), { col = "darkWood", mat = "wood", pri = 2.0, role = "detail", name = "Brace" })
		end
		face(B, ctx, at(0, 1.25, -1.24), 2.0)
	end
end

function K.generic(B: any, ctx: any)
	-- chunky rounded prop: body + cap + base band in the word's colours
	B:ell(2.4, 2.6, 2.0, at(0, 1.4, 0), { col = "primary", mat = "plastic", pri = 1, role = "body", name = "Body" })
	B:ell(1.4, 0.8, 1.2, at(0, 2.75, 0), { col = "secondary", mat = "plastic", pri = 1.2, role = "detail", name = "Cap" })
	B:cyl(0.4, 2.3, at(0, 0.3, 0, 0, 0, rad(90)), { col = "secondary", mat = "plastic", pri = 1.3, role = "detail", name = "Base" })
	if Heads.wantsFace(B, ctx.traits) then
		local Face = require(script.Parent.Parent.Face)
		Face.build(B, { face = { kind = "ellipsoid", c = { 0, 1.4, 0 }, r = { 1.2, 1.3, 1.0 } }, bone = "Body", mood = ctx.result.mood, detail = math.max(1, ctx.detail), kind = "cute", spacing = 0.42, y = 0.25, d = 0.45, mouthY = -0.35, mouthW = 0.7, forceMouth = true })
	end
end

return function(B: any, ctx: any)
	local id = string.lower(ctx.result.id)
	local plan = ctx.kind
	B.boneIndex.Body.pos = { 0, 1, 0 }
	local done = true
	if has(id, "throne") then
		K.chair(B, ctx, true)
	elseif has(id, "chair") or has(id, "stool") or has(id, "bench") then
		K.chair(B, ctx, false)
	elseif has(id, "table") or has(id, "desk") then
		K.table(B, ctx)
	elseif has(id, "bed") then
		K.bed(B, ctx)
	elseif has(id, "sofa") or has(id, "couch") then
		K.sofa(B, ctx)
	elseif has(id, "lamp") or has(id, "lantern") then
		K.lamp(B, ctx)
	elseif has(id, "book") or has(id, "shelf") then
		K.bookshelf(B, ctx)
	elseif has(id, "toaster") then
		K.toaster(B, ctx)
	elseif has(id, "fridge") or has(id, "refrigerator") or has(id, "freezer") then
		K.box(B, ctx, "fridge")
	elseif has(id, "tv") or has(id, "television") or has(id, "monitor") or has(id, "computer") or has(id, "laptop") then
		K.box(B, ctx, "tv")
	elseif has(id, "washing") or has(id, "washer") or has(id, "dryer") then
		K.box(B, ctx, "washing")
	elseif has(id, "microwave") then
		K.box(B, ctx, "microwave")
	elseif has(id, "oven") or has(id, "stove") then
		K.box(B, ctx, "oven")
	elseif has(id, "fan") then
		K.box(B, ctx, "fan")
	elseif has(id, "vacuum") or has(id, "roomba") then
		K.box(B, ctx, "vacuum")
	elseif has(id, "barrel") or has(id, "keg") then
		K.container(B, ctx, "barrel")
	elseif has(id, "chest") or has(id, "treasure") then
		K.container(B, ctx, "chest")
	elseif has(id, "jar") or has(id, "pot") then
		K.container(B, ctx, "jar")
	elseif has(id, "vase") or has(id, "urn") then
		K.container(B, ctx, "vase")
	elseif has(id, "bottle") or has(id, "potion") or has(id, "flask") then
		K.container(B, ctx, "bottle")
	elseif has(id, "mug") or has(id, "cup") or has(id, "teacup") then
		K.container(B, ctx, "mug")
	elseif has(id, "bucket") or has(id, "pail") then
		K.container(B, ctx, "bucket")
	elseif has(id, "trash") or has(id, "bin") or has(id, "can") then
		K.container(B, ctx, "can")
	elseif has(id, "backpack") or has(id, "bag") then
		K.container(B, ctx, "backpack")
	elseif has(id, "box") or has(id, "crate") or has(id, "present") or has(id, "gift") or has(id, "package") then
		K.container(B, ctx, "box")
	else
		done = false
	end
	if not done then
		if plan == "Furniture" then
			K.chair(B, ctx, false)
		elseif plan == "Appliance" then
			K.toaster(B, ctx)
		elseif plan == "Container" then
			K.container(B, ctx, "box")
		else
			K.generic(B, ctx)
		end
	end
	if B.sockets.core == nil then
		B:socket("core", at(0, 1.4, 0), "Body")
	end
	B:setRig("gait", "hop")
end
