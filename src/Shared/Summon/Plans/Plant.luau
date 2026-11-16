--!strict
-- Plants: Tree (round canopy clusters), pine (tiered), palm, Flower (stem + petal ring), sunflower, Cactus
-- (saguaro arms), Mushroom (stalk + spotted cap), bush, venus flytrap (toothy jaw leaves), vine/beanstalk.

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Heads = require(script.Parent.Parent.Heads)
local Face = require(script.Parent.Parent.Face)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local function kindOf(ctx: any): string
	if ctx.kind then
		return string.lower(ctx.kind)
	end
	local t, id = ctx.traits, string.lower(ctx.result.id)
	local function has(w: string): boolean
		return string.find(id, "%f[%a]" .. w) ~= nil
	end
	if has("flytrap") or has("piranha plant") or string.find(string.lower(ctx.result.visual.silhouetteHint or ""), "jaw") then
		return "flytrap"
	elseif t.pine or has("pine") or has("fir") or has("spruce") or has("christmas") then
		return "pine"
	elseif has("palm") or has("coconut") then
		return "palm"
	elseif t.cactus then
		return "cactus"
	elseif t.mushroom or has("fungus") or has("shroom") then
		return "mushroom"
	elseif t.flower or t.petals or has("daisy") or has("lily") or has("orchid") or has("lotus") or has("poppy") then
		return "flower"
	elseif t.bush or has("hedge") or has("fern") or has("grass") then
		return "bush"
	elseif t.vine or has("beanstalk") or has("ivy") then
		return "vine"
	end
	return "tree"
end

local function sway(B: any, name: string, parent: string, p: { number })
	local b = B:bone(name, parent, p[1], p[2], p[3])
	B:addRig("sway", b)
	return b
end

local function faceOn(B: any, ctx: any, c: { number }, r: { number }, bone: string)
	if Heads.wantsFace(B, ctx.traits) then
		Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = bone, mood = ctx.result.mood, detail = math.max(1, ctx.detail), kind = "cute",
			spacing = r[1] * 0.36, y = r[2] * 0.15, d = math.min(r[1], r[2]) * 0.4, mouthY = -r[2] * 0.3, mouthW = r[1] * 0.55, forceMouth = true, lidCol = "bark" })
	end
end

local K = {}

function K.tree(B: any, ctx: any)
	local detail = ctx.detail
	local h = 3.0
	B:limb({ 0, 0, 0 }, { 0, h, 0 }, 1.0, { col = "bark", mat = "wood", pri = 1, role = "body", name = "Trunk" }, 0.05)
	B:ell(1.7, 0.5, 1.7, at(0, 0.2, 0), { col = "bark", mat = "wood", pri = 1.6, role = "detail", name = "Roots" })
	local crown = sway(B, "Crown", "Body", { 0, h, 0 })
	B:ell(4.2, 3.4, 4.0, at(0, h + 1.4, 0), { col = "leaf", mat = "leaf", bone = crown, pri = 1.05, role = "body", name = "Canopy" })
	local n = if detail <= 0 then 0 elseif detail == 1 then 2 elseif detail == 2 then 3 else 5
	for i = 1, n do
		local a = (i - 1) / n * math.pi * 2 + 0.5
		B:ell(2.4, 2.1, 2.3, at(sin(a) * 1.6, h + 1.2 + (i % 2) * 0.7, cos(a) * 1.5), { col = if i % 2 == 0 then "leafDark" else "leaf", mat = "leaf", bone = crown, pri = 1.3 + i * 0.1, role = "body", name = "Clump" .. i })
	end
	if detail >= 2 then
		B:limb({ 0, h * 0.6, 0 }, { 1.1, h + 0.4, -0.2 }, 0.4, { col = "bark", mat = "wood", pri = 2.2, role = "limb", name = "Branch" }, 0.1)
	end
	if detail >= 3 and ctx.result.element ~= "Ice" then
		for i = 1, 3 do
			local a = i * 2.1
			B:ball(0.45, at(sin(a) * 1.9, h + 0.9 + i * 0.3, cos(a) * 1.8 - 0.3), { col = "red", mat = "plastic", bone = crown, pri = 3.5 + i * 0.05, role = "detail", name = "Fruit" .. i })
		end
	end
	faceOn(B, ctx, { 0, h * 0.5, 0 }, { 0.5, 1.2, 0.5 }, "Body")
end

function K.pine(B: any, ctx: any)
	local detail = ctx.detail
	B:cyl(1.6, 0.8, at(0, 0.8, 0, 0, 0, rad(90)), { col = "bark", mat = "wood", pri = 1.1, role = "body", name = "Trunk" })
	local crown = sway(B, "Crown", "Body", { 0, 1.5, 0 })
	local tiers = if detail <= 1 then 3 else 4
	for i = 1, tiers do
		local w = 4.0 * (1 - (i - 1) / (tiers + 0.6))
		local y = 1.4 + (i - 1) * 1.2
		-- each tier: a squat cone made from a tall-ish ellipsoid bottom-heavy + offset so tiers overlap
		B:limb({ 0, y, 0 }, { 0, y + 1.9, 0 }, w, { col = if i % 2 == 0 then "leafDark" else "leaf", mat = "leaf", bone = crown, pri = 1 + i * 0.05, role = "body", name = "Tier" .. i, depth = w * 0.98 }, 0.02)
	end
	if detail >= 2 and (ctx.result.element == "Ice" or string.find(string.lower(ctx.result.id), "christmas")) then
		B:ball(0.6, at(0, 1.4 + tiers * 1.2 + 0.5, 0), { col = "gold", mat = "neon", glow = true, bone = crown, pri = 2.0, role = "gem", name = "Star" })
	end
	faceOn(B, ctx, { 0, 2.4, 0 }, { 1.45, 0.8, 1.45 }, crown)
end

function K.palm(B: any, ctx: any)
	local detail = ctx.detail
	local pts = { { 0, 0, 0 }, { 0.3, 1.8, 0 }, { 0.8, 3.4, 0 }, { 1.5, 4.8, 0 } }
	for i = 1, 3 do
		B:limb(pts[i], pts[i + 1], 0.7 - i * 0.08, { col = "bark", mat = "wood", pri = 1 + i * 0.05, role = "body", name = "Trunk" .. i }, 0.25)
	end
	local crown = sway(B, "Crown", "Body", pts[4])
	local n = if detail <= 1 then 4 else 6
	for i = 1, n do
		local a = (i - 1) / n * math.pi * 2
		B:ell(0.9, 0.1, 3.0, Geom.mul(at(pts[4][1], pts[4][2], pts[4][3], 0, a, 0), at(0, -0.2, 1.3, rad(22), 0, 0)), { col = "leaf", mat = "leaf", bone = crown, pri = 1.2 + i * 0.05, role = "leaf", name = "Frond" .. i, trail = i == 1 })
	end
	if detail >= 2 then
		B:mball(0.55, at(0.3 + 1.5, 4.4, -0.2), { col = "darkWood", mat = "wood", bone = crown, pri = 2.4, role = "detail", name = "Coconut#" })
	end
end

function K.flower(B: any, ctx: any)
	local detail = ctx.detail
	local sun = string.find(string.lower(ctx.result.id), "sunflower") ~= nil
	local h = if sun then 4.2 else 3.2
	B:cyl(h, 0.28, at(0, h / 2, 0, 0, 0, rad(90)), { col = "leafDark", mat = "leaf", pri = 1.1, role = "body", name = "Stem" })
	B:mell(1.4, 0.12, 0.6, at(0.6, h * 0.35, 0, 0, rad(-10), rad(25)), { col = "leaf", mat = "leaf", pri = 1.5, role = "leaf", name = "Leaf#" })
	local head = sway(B, "Head", "Body", { 0, h, 0 })
	B:setRig("head", head)
	-- flower head faces the viewer (-Z): disc centre + petal ring in the XY plane
	local c = { 0, h + 0.4, -0.1 }
	local r = if sun then 0.95 else 0.6
	B:ell(r * 2, r * 2, 0.5, at(c[1], c[2], c[3]), { col = if sun then "darkWood" else "gold", mat = "skin", bone = head, pri = 1, role = "head", name = "Disc" })
	local n = if detail <= 1 then 5 elseif detail == 2 then 6 else (if sun then 10 else 8)
	for i = 1, n do
		local a = (i - 1) / n * math.pi * 2
		local pr = r + (if sun then 0.65 else 0.55)
		B:ell(if sun then 0.6 else 0.85, if sun then 1.3 else 1.1, 0.1 + (i % 2) * 0.015, at(sin(a) * pr, c[2] + cos(a) * pr, c[3] + 0.06 + (i % 2) * 0.05, 0, 0, -a),
			{ col = "primary", mat = "leaf", bone = head, pri = 1.05 + i * 0.03, role = "petal", name = "Petal" .. i })
	end
	if Heads.wantsFace(B, ctx.traits) then
		Heads.objectFace(B, ctx.traits, at(c[1], c[2], c[3] - 0.24), r * 2, head, { eye = 0.24 })
	end
	B:socket("core", at(c[1], c[2], c[3]), head)
end

function K.cactus(B: any, ctx: any)
	local detail = ctx.detail
	B:limb({ 0, 0, 0 }, { 0, 4.6, 0 }, 1.4, { col = "primary", mat = "skin", pri = 1, role = "body", name = "Trunk" }, 0.08)
	B:mlimb({ 0.55, 2.0, 0 }, { 1.4, 2.2, 0 }, 0.75, { col = "primary", mat = "skin", pri = 1.1, role = "limb", name = "ArmBase#" }, 0.2)
	B:mlimb({ 1.4, 2.0, 0 }, { 1.45, 3.4, 0 }, 0.72, { col = "primary", mat = "skin", pri = 1.15, role = "limb", name = "Arm#" }, 0.2)
	if detail >= 2 then
		B:ell(0.7, 0.45, 0.7, at(0, 4.75, 0), { col = "secondary", mat = "leaf", pri = 2.0, role = "petal", name = "Bloom" })
		for i = 1, (if detail >= 3 then 4 else 2) do
			local a = i * 1.7
			B:wedge(0.05, 0.3, 0.22, at(sin(a) * 0.68, 1.2 + i * 0.7, cos(a) * 0.68, 0, a, rad(90)), { col = "cream", mat = "hard", pri = 3 + i * 0.05, role = "spike" })
		end
	end
	faceOn(B, ctx, { 0, 3.2, 0 }, { 0.7, 1.0, 0.7 }, "Body")
end

function K.mushroom(B: any, ctx: any)
	local detail = ctx.detail
	B:limb({ 0, 0, 0 }, { 0, 2.4, 0 }, 1.3, { col = "cream", mat = "skin", pri = 1.05, role = "body", name = "Stalk" }, 0.1)
	local c, r = { 0, 2.7, 0 }, { 2.2, 1.2, 2.2 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", pri = 1, role = "head", name = "Cap" })
	B:ell(r[1] * 1.8, 0.4, r[3] * 1.8, at(0, c[2] - r[2] * 0.6, 0), { col = "cream", mat = "skin", pri = 1.5, role = "detail", name = "Gills" })
	local spots = if detail <= 1 then 2 elseif detail == 2 then 4 else 6
	for i = 1, spots do
		local a, b = i * 2.4, 0.35 + (i % 3) * 0.25
		local nx, ny, nz = sin(a) * cos(b), sin(b), cos(a) * cos(b)
		local p = { nx * r[1] * 0.98, c[2] + ny * r[2] * 0.98, nz * r[3] * 0.98 }
		B:ell(0.75, 0.75, 0.25, at(p[1], p[2], p[3], -math.asin(ny) * 0 - b * 0.9, math.atan2(nx, nz) + math.pi, 0), { col = "secondary", mat = "skin", pri = 1.6 + i * 0.05, role = "detail", name = "Spot" .. i })
	end
	faceOn(B, ctx, { 0, 1.3, 0 }, { 0.65, 0.8, 0.65 }, "Body")
end

function K.bush(B: any, ctx: any)
	local detail = ctx.detail
	B:ell(3.6, 2.4, 3.0, at(0, 1.2, 0), { col = "leaf", mat = "leaf", pri = 1, role = "body", name = "Bush" })
	for i = 1, (if detail >= 2 then 4 else 2) do
		local a = i * 1.6
		B:ell(1.9, 1.7, 1.8, at(sin(a) * 1.3, 1.0 + (i % 2) * 0.7, cos(a) * 1.0), { col = "leafDark", mat = "leaf", pri = 1.3 + i * 0.05, role = "body", name = "Clump" .. i })
	end
	if detail >= 3 then
		for i = 1, 4 do
			local a = i * 1.3 + 0.4
			B:ball(0.36, at(sin(a) * 1.75, 1.2 + (i % 2) * 0.6, cos(a) * 1.45), { col = "red", mat = "plastic", pri = 3.4 + i * 0.05, role = "detail" })
		end
	end
	faceOn(B, ctx, { 0, 1.2, 0 }, { 1.8, 1.2, 1.5 }, "Body")
end

function K.flytrap(B: any, ctx: any)
	local detail = ctx.detail
	B:limb({ 0, 0, 0 }, { 0, 2.4, -0.2 }, 0.5, { col = "leafDark", mat = "leaf", pri = 1.1, role = "body", name = "Stem" }, 0.1)
	B:mell(1.8, 0.15, 0.8, at(0.8, 0.3, 0, 0, 0, rad(10)), { col = "leaf", mat = "leaf", pri = 1.6, role = "leaf", name = "Leaf#" })
	local head = B:bone("Head", "Body", 0, 2.6, -0.3)
	B:setRig("head", head)
	local jaw = B:bone("Jaw", head, 0, 2.6, 0.0)
	B:setRig("jaw", jaw)
	-- upper and lower trap lobes, each a half-open clam with teeth along the rim
	B:ell(2.4, 0.8, 2.0, at(0, 3.25, -0.9, rad(-22), 0, 0), { col = "primary", mat = "leaf", bone = head, pri = 1, role = "head", name = "UpperLobe" })
	B:ell(2.3, 0.7, 1.9, at(0, 2.45, -0.9, rad(16), 0, 0), { col = "primary", mat = "leaf", bone = jaw, pri = 1.05, role = "jaw", name = "LowerLobe" })
	B:ell(1.8, 0.3, 1.5, at(0, 2.86, -0.95, rad(-4), 0, 0), { col = "secondary", mat = "skin", bone = head, pri = 1.3, role = "mouth", name = "Inside" })
	local n = if detail >= 2 then 4 else 2
	for i = 1, n do
		local x = (i - (n + 1) / 2) * 0.5
		B:wedge(0.12, 0.5, 0.2, at(x, 2.86, -1.84 + math.abs(x) * 0.25, math.pi, 0, 0), { col = "cream", mat = "hard", bone = head, pri = 1.6 + i * 0.05, role = "tooth" })
	end
	if Heads.wantsFace(B, ctx.traits) or true then
		Face.build(B, { face = { kind = "ellipsoid", c = { 0, 3.25, -0.9 }, r = { 1.2, 0.4, 1.0 } }, bone = head, mood = ctx.result.mood, detail = math.max(1, detail),
			kind = "fierce", spacing = 0.45, y = 0.35, d = 0.42, noMouth = true })
	end
	B:socket("mouth", at(0, 2.86, -1.9), head)
end

function K.vine(B: any, ctx: any)
	local detail = ctx.detail
	local parent = "Body"
	local x, y = 0, 0
	local n = if detail <= 1 then 3 else 5
	for i = 1, n do
		local b = sway(B, "Seg" .. i, parent, { x, y, 0 })
		local nx, ny = sin(i * 1.2) * 0.7, y + 1.3
		B:limb({ x, y, 0 }, { nx, ny, 0 }, 0.42 - i * 0.04, { col = "leafDark", mat = "leaf", bone = b, pri = 1 + i * 0.05, role = "body", name = "Vine" .. i, trail = i == n }, 0.25)
		B:ell(0.9, 0.1, 0.55, at(nx + 0.35, ny - 0.3, 0, 0, rad(30 * i), rad(20)), { col = "leaf", mat = "leaf", bone = b, pri = 1.4 + i * 0.05, role = "leaf", name = "Leaf" .. i })
		x, y, parent = nx, ny, b
	end
end

return function(B: any, ctx: any)
	local kind = kindOf(ctx)
	local f = (K :: any)[kind] or K.tree
	f(B, ctx)
	B.boneIndex.Body.pos = { 0, 1, 0 }
	if B.sockets.core == nil then
		B:socket("core", at(0, 2, 0), "Body")
	end
	local _ = Parts
	B:setRig("gait", "sway")
end
