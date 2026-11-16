--!strict
-- Blob: slimes and goo creatures, plus Food (cake, cupcake, pie, pizza, donut, burger, fruit, ice cream,
-- cookie, bread, cheese, egg, banana, carrot, candy, lollipop, generic). Food gets a face when it has a mood
-- or is silly/cute (Heads.wantsFace); slimes always do.

local Geom = require(script.Parent.Parent.Geom)
local Face = require(script.Parent.Parent.Face)
local Heads = require(script.Parent.Parent.Heads)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local function foodKind(t: any, id: string): string?
	for _, k in { "cupcake", "cake", "pie", "pizza", "donut", "burger", "icecream", "lollipop", "candy", "cookie", "bread", "cheese", "egg", "banana", "carrot", "pumpkin", "melon", "fruit" } do
		if t[k] then
			return k
		end
	end
	if string.find(id, "ice cream") or string.find(id, "gelato") or string.find(id, "sundae") then
		return "icecream"
	end
	local function any(list: string): boolean
		for w in string.gmatch(list, "%S+") do
			if string.find(id, "%f[%a]" .. w) then
				return true
			end
		end
		return false
	end
	if any("sandwich reuben panini blt sub hoagie club toastie gyro kebab") then
		return "burger"
	elseif any("croissant kouign danish pastry strudel turnover cruller") then
		return "croissant"
	elseif any("nut pecan walnut almond acorn hazelnut peanut cashew pistachio chestnut macadamia") then
		return "nut"
	end
	return nil
end

local function face(B: any, ctx: any, c: { number }, r: { number }, force: boolean?)
	local t = ctx.traits
	if not force and not Heads.wantsFace(B, t) then
		return
	end
	Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = "Body", mood = ctx.result.mood, detail = math.max(1, ctx.detail), kind = "cute",
		spacing = r[1] * 0.36, y = r[2] * 0.15, d = math.min(r[1], r[2]) * 0.42, mouthY = -r[2] * 0.25, mouthW = r[1] * 0.55, forceMouth = true, lidCol = "primary" })
end

local function flatFace(B: any, ctx: any, cf: any, w: number)
	if Heads.wantsFace(B, ctx.traits) then
		Heads.objectFace(B, ctx.traits, cf, w, "Body")
	end
end

return function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id = string.lower(ctx.result.id)
	local food = ctx.kind == "Food" or t.category == "Food"
	local k = foodKind(t, id)
	if not food and not k then
		-- SLIME: squat glossy body, droop lumps at the base, big eyes, a highlight blob
		local c, r = { 0, 1.15, 0 }, { 1.45, 1.15, 1.35 }
		B.boneIndex.Body.pos = { 0, 0.4, 0 }
		B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "glass", pri = 1, role = "body", name = "Body" })
		if detail >= 1 then
			B:ell(r[1] * 2.35, r[2] * 0.7, r[3] * 2.3, at(0, 0.38, 0.02), { col = "primary", mat = "glass", pri = 1.4, role = "body", name = "Base" })
		end
		if detail >= 2 then
			B:ell(r[1] * 0.5, r[2] * 0.36, r[3] * 0.3, at(-r[1] * 0.42, c[2] + r[2] * 0.55, c[3] - r[3] * 0.55, rad(-30), rad(20), rad(20)), { col = "shine", mat = "neon", pri = 2.6, role = "shine", name = "Gloss", noCore = true })
			B:ell(0.5, 0.5, 0.5, at(0.3, c[2] - 0.2, c[3] + 0.3), { col = "secondary", mat = "glass", pri = 3.0, role = "detail", name = "Nucleus", noCore = true })
		end
		face(B, ctx, c, r, true)
		B:socket("core", at(c[1], c[2], c[3]), "Body")
		B:setRig("gait", "hop")
		return
	end
	B.boneIndex.Body.pos = { 0, 1, 0 }
	local fc, fr -- face ellipsoid (when food is rounded)
	k = k or "generic"
	if k == "cake" or k == "cupcake" then
		local cup = k == "cupcake"
		local tiers = if cup or detail <= 1 then 1 else 2
		local y = 0
		local r0 = if cup then 1.0 else 1.6
		if cup then
			B:cyl(1.3, 1.9, at(0, 0.65, 0, 0, 0, rad(90)), { col = "secondary", mat = "plastic", pri = 1, role = "body", name = "Wrapper" })
			B:ell(2.3, 1.7, 2.3, at(0, 1.55, 0), { col = "frosting", mat = "skin", pri = 1.1, role = "body", name = "Frosting" })
			fc, fr = { 0, 0.75, 0 }, { 0.95, 0.65, 0.95 }
			y = 2.3
		else
			for i = 1, tiers do
				local rr = r0 * (1 - (i - 1) * 0.3)
				local h = 1.0
				B:cyl(h, rr * 2, at(0, y + h / 2, 0, 0, 0, rad(90)), { col = "secondary", mat = "skin", pri = 1 + i * 0.05, role = "body", name = "Tier" .. i })
				B:cyl(h * 0.28, rr * 2 + 0.12, at(0, y + h * 0.92, 0, 0, 0, rad(90)), { col = "frosting", mat = "skin", pri = 1.4 + i * 0.1, role = "detail", name = "Icing" .. i })
				if i == 1 then
					fc, fr = { 0, y + h * 0.45, 0 }, { rr, h * 0.48, rr }
				end
				y += h * 1.0
			end
			y += 0.14
		end
		B:ball(0.55, at(0, y + 0.15, 0), { col = "red", mat = "glass", pri = 1.5, role = "detail", name = "Cherry" })
		if detail >= 2 then
			B:limb({ 0, y + 0.35, 0 }, { 0.15, y + 0.85, 0.1 }, 0.08, { col = "leafDark", mat = "wood", pri = 3, role = "detail" }, 0.05)
		end
	elseif k == "pie" or k == "pizza" then
		if k == "pizza" then
			-- a slice standing up on its crust, tip up: one big wedge + crust log + toppings
			B:wedge(0.32, 3.0, 2.0, at(0, 1.55, 0, rad(90), 0, 0), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Slice" })
			B:cyl(2.25, 0.62, at(0, 0.3, 0.1), { col = "wood", mat = "skin", pri = 1.1, role = "body", name = "Crust" })
			local tops = if detail >= 2 then 3 else 1
			for i = 1, tops do
				local yy = 0.9 + i * 0.55
				B:cyl(0.12, 0.42 - i * 0.04, at((i % 2 - 0.5) * 0.4 * (1 - i * 0.2), yy, -0.2, 0, rad(90), 0), { col = "secondary", mat = "skin", pri = 1.8 + i * 0.2, role = "detail", name = "Pepperoni" .. i })
			end
			flatFace(B, ctx, at(0, 1.1, -0.17), 1.2)
		else
			B:cyl(0.9, 3.2, at(0, 0.45, 0, 0, 0, rad(90)), { col = "wood", mat = "skin", pri = 1, role = "body", name = "Dish" })
			B:ell(3.0, 0.9, 3.0, at(0, 0.85, 0), { col = "primary", mat = "skin", pri = 1.1, role = "body", name = "Filling" })
			fc, fr = { 0, 0.45, 0 }, { 1.6, 0.45, 1.6 }
		end
	elseif k == "donut" then
		-- torus from a ring of overlapping balls, frosting ring on top, standing on edge
		local n = if detail <= 1 then 6 elseif detail == 2 then 8 else 10
		local R, rr = 1.1, 0.75
		for i = 1, n do
			local a = (i - 1) / n * math.pi * 2
			B:ball(rr * 2, at(sin(a) * R, 1.85 + cos(a) * R, 0), { col = "primary", mat = "skin", pri = 1 + i * 0.01, role = "body", name = "Dough" .. i })
			if detail >= 2 and i % 2 == 0 then
				B:ell(rr * 1.6, rr * 1.6, rr * 0.9, at(sin(a) * R, 1.85 + cos(a) * R, -rr * 0.45), { col = "secondary", mat = "skin", pri = 1.6 + i * 0.01, role = "detail", name = "Frost" .. i })
			end
		end
		flatFace(B, ctx, at(0, 3.0, -rr * 0.8), 1.0)
	elseif k == "burger" then
		B:ell(2.8, 0.7, 2.8, at(0, 0.35, 0), { col = "primary", mat = "skin", pri = 1.05, role = "body", name = "BunLow" })
		B:cyl(0.5, 2.75, at(0, 0.85, 0, 0, 0, rad(90)), { col = "secondary", mat = "skin", pri = 1.1, role = "body", name = "Patty" })
		if detail >= 1 then
			B:ell(3.0, 0.22, 3.0, at(0, 1.13, 0), { col = "leaf", mat = "leaf", pri = 1.5, role = "detail", name = "Lettuce" })
			B:block(2.3, 0.08, 2.3, at(0, 1.17, 0, 0, rad(45), 0), { col = "gold", mat = "skin", pri = 1.7, role = "detail", name = "Cheese" })
		end
		B:ell(2.85, 1.5, 2.85, at(0, 1.45, 0), { col = "primary", mat = "skin", pri = 1, role = "body", name = "BunTop" })
		fc, fr = { 0, 1.62, 0 }, { 1.4, 0.72, 1.4 }
		if detail >= 3 then
			for i = 1, 3 do
				local a = i * 2.1
				B:ell(0.18, 0.08, 0.1, at(sin(a) * 0.6, 2.13, cos(a) * 0.6 + 0.2, 0, a, 0), { col = "cream", mat = "skin", pri = 3.5, role = "detail" })
			end
		end
	elseif k == "icecream" then
		B:limb({ 0, 0.05, 0 }, { 0, 1.9, 0 }, 1.0, { col = "wood", mat = "skin", pri = 1.05, role = "body", name = "Cone" }, 0.02)
		B:ell(1.9, 1.6, 1.9, at(0, 2.3, 0), { col = "secondary", mat = "skin", pri = 1, role = "body", name = "Scoop1" })
		fc, fr = { 0, 2.3, 0 }, { 0.95, 0.8, 0.95 }
		if detail >= 1 then
			B:ell(1.55, 1.3, 1.55, at(0.05, 3.3, 0.05), { col = "primary", mat = "skin", pri = 1.4, role = "body", name = "Scoop2" })
			B:ball(0.4, at(0, 4.05, 0), { col = "red", mat = "glass", pri = 2, role = "detail", name = "Cherry" })
		end
	elseif k == "lollipop" or k == "candy" then
		if k == "lollipop" then
			B:cyl(3.0, 0.2, at(0, 1.5, 0, 0, 0, rad(90)), { col = "white", mat = "plastic", pri = 1.1, role = "body", name = "Stick" })
			B:cyl(0.5, 2.6, at(0, 3.9, 0, 0, rad(90), 0), { col = "primary", mat = "glass", pri = 1, role = "body", name = "Disc" })
			if detail >= 2 then
				B:cyl(0.56, 1.6, at(0, 3.9, 0, 0, rad(90), 0), { col = "secondary", mat = "glass", pri = 2, role = "detail", name = "Swirl" })
			end
			flatFace(B, ctx, at(0, 3.9, -0.28), 1.4)
		else
			B:ell(2.2, 1.5, 1.5, at(0, 1.0, 0), { col = "primary", mat = "glass", pri = 1, role = "body", name = "Candy" })
			B:mwedge(0.9, 1.4, 0.7, at(1.45, 1.0, 0, 0, rad(90), rad(90)), { col = "secondary", mat = "plastic", pri = 1.3, role = "detail", name = "Wrap#" })
			fc, fr = { 0, 1.0, 0 }, { 1.1, 0.75, 0.75 }
		end
	elseif k == "cookie" then
		B:cyl(0.5, 3.0, at(0, 1.6, 0, 0, rad(90), 0), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Cookie" })
		for i = 1, (if detail >= 2 then 4 else 2) do
			local a = i * 1.7
			B:ball(0.4, at(sin(a) * 0.9, 1.6 + cos(a) * 0.9, -0.15), { col = "secondary", mat = "skin", pri = 1.8 + i * 0.1, role = "detail" })
		end
		flatFace(B, ctx, at(0, 1.6, -0.25), 1.5)
	elseif k == "cheese" then
		B:wedge(2.6, 1.6, 2.2, at(0, 0.8, 0, 0, rad(180), 0), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Cheese" })
		for i = 1, (if detail >= 2 then 3 else 1) do
			B:ell(0.5, 0.45, 0.2, at(-0.7 + i * 0.5, 0.45 + (i % 2) * 0.35, -1.1), { col = "dark", mat = "skin", pri = 1.8 + i * 0.1, role = "detail", name = "Hole" .. i })
		end
		flatFace(B, ctx, at(0.3, 0.75, 1.11, 0, math.pi, 0), 1.0)
	elseif k == "croissant" then
		-- crescent of plump rolled segments: fattest in the middle, tapering horns curling forward
		local n = if detail <= 1 then 3 else 5
		for i = 1, n do
			local t0 = (i - 1) / n
			local t1 = i / n
			local a0, a1 = rad(-80 + t0 * 160), rad(-80 + t1 * 160)
			local R = 1.7
			local w = 1.45 * (1 - math.abs((t0 + t1) / 2 - 0.5) * 1.3)
			B:limb({ sin(a0) * R, 1.0, -cos(a0) * R * 0.55 + 0.6 }, { sin(a1) * R, 1.0, -cos(a1) * R * 0.55 + 0.6 }, w,
				{ col = if i % 2 == 0 then "secondary" else "primary", mat = "skin", pri = 1 + math.abs(i - (n + 1) / 2) * 0.08, role = "body", name = "Roll" .. i, depth = w * 0.9 }, 0.3)
		end
		fc, fr = { 0, 1.05, -0.1 }, { 0.75, 0.62, 0.62 }
	elseif k == "nut" then
		-- pointed oval with a seam ridge; acorns get a scaly cap and stalk
		local acorn = string.find(id, "acorn") ~= nil
		B:ell(2.2, 2.9, 2.0, at(0, 1.45, 0), { col = "primary", mat = "wood", pri = 1, role = "body", name = "Shell" })
		B:ell(0.26, 2.92, 2.06, at(0, 1.46, 0), { col = "dark", mat = "wood", pri = 1.3, role = "detail", name = "Seam" })
		if acorn or detail >= 1 then
			B:ell(2.45, 1.3, 2.25, at(0, 2.55, 0), { col = if acorn then "secondary" else "darker", mat = "wood", pri = 1.2, role = "detail", name = "Cap" })
			B:limb({ 0, 3.1, 0 }, { 0.12, 3.6, 0.05 }, 0.22, { col = "bark", mat = "wood", pri = 1.5, role = "detail", name = "Stalk" }, 0.1)
		end
		fc, fr = { 0, 1.35, 0 }, { 1.1, 1.2, 1.0 }
	elseif k == "banana" or k == "carrot" then
		local col = "primary"
		local n = if detail <= 1 then 2 else 3
		for i = 1, n do
			local a0 = rad(-50 + (i - 1) * 100 / n)
			local a1 = rad(-50 + i * 100 / n)
			local R = 2.2
			local w = if k == "carrot" then 1.1 * (1 - (i - 1) * 0.3) else 0.85
			B:limb({ sin(a0) * R, 2.6 - cos(a0) * R * (if k == "carrot" then 0 else 0.6) - (if k == "carrot" then (i - 1) * 1.1 else 0), 0 },
				{ sin(a1) * R, 2.6 - cos(a1) * R * (if k == "carrot" then 0 else 0.6) - (if k == "carrot" then i * 1.1 else 0), 0 }, w,
				{ col = col, mat = "skin", pri = 1 + i * 0.05, role = "body", name = "Seg" .. i }, 0.35)
		end
		if k == "carrot" then
			B:ell(0.9, 1.0, 0.3, at(0, 3.6, 0), { col = "leaf", mat = "leaf", pri = 1.5, role = "detail", name = "Greens" })
		end
		flatFace(B, ctx, at(0, 2.0, -0.45), 0.9)
	else
		-- fruit / egg / bread / pumpkin / generic: one big rounded form with a stem and leaf
		local sx, sy = 2.6, 2.5
		if k == "egg" then
			sx, sy = 2.1, 2.8
		elseif k == "bread" then
			sx, sy = 3.4, 1.8
		elseif k == "pumpkin" or k == "melon" then
			sx, sy = 3.2, 2.4
		end
		B:ell(sx, sy, sx * (if k == "bread" then 0.62 else 1), at(0, sy / 2, 0), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Body" })
		fc, fr = { 0, sy / 2, 0 }, { sx / 2, sy / 2, sx / 2 * (if k == "bread" then 0.62 else 1) }
		if k == "pumpkin" and detail >= 1 then
			B:mell(sx * 0.5, sy * 0.95, sx * 0.62, at(sx * 0.3, sy / 2, 0), { col = "primary", mat = "skin", pri = 1.4, role = "body", name = "Lobe#" })
		end
		if k == "bread" and detail >= 2 then
			for i = 1, 3 do
				B:ell(0.18, 0.12, sx * 0.4, at(-0.9 + i * 0.6, sy * 0.96, 0, 0, rad(30), 0), { col = "secondary", mat = "skin", pri = 2.5 + i * 0.1, role = "detail" })
			end
		end
		if k == "generic" then
			-- an unknown dish: served on a plate with a drizzle band and a garnish leaf so it still reads as food
			B:cyl(0.24, sx * 1.55, at(0, 0.1, 0, 0, 0, rad(90)), { col = "white", mat = "plastic", pri = 1.2, role = "detail", name = "Plate" })
			if detail >= 1 then
				local k2 = math.sqrt(1 - 0.35 ^ 2) * 1.04
				B:ell(sx * k2, sy * 0.16, sx * k2, at(0, sy / 2 + sy * 0.175, 0), { col = "secondary", mat = "skin", pri = 1.4, role = "detail", name = "Drizzle" })
				B:ell(0.8, 0.12, 0.42, at(0.3, sy * 1.0, -0.1, 0, rad(-20), rad(-15)), { col = "leaf", mat = "leaf", pri = 1.7, role = "detail", name = "Garnish" })
			end
		elseif k ~= "egg" and k ~= "bread" then
			B:limb({ 0, sy * 0.92, 0 }, { 0.1, sy * 1.15, 0.05 }, 0.2, { col = "bark", mat = "wood", pri = 1.6, role = "detail", name = "Stem" }, 0.1)
			if detail >= 1 then
				B:ell(0.9, 0.12, 0.45, at(0.45, sy * 1.07, 0, 0, rad(-20), rad(-25)), { col = "leaf", mat = "leaf", pri = 1.7, role = "detail", name = "Leaf" })
			end
		end
		if k == "melon" and detail >= 2 then
			for i = 1, 3 do
				B:ell(sx * 1.02, sy * 1.02, 0.25, at(0, sy / 2, 0, 0, rad(i * 60), 0), { col = "secondary", mat = "skin", pri = 2.2 + i * 0.1, role = "detail" })
			end
		end
	end
	if fc then
		face(B, ctx, fc, fr)
	end
	B:socket("core", at(0, 1.2, 0), "Body")
	B:setRig("gait", "hop")
end
