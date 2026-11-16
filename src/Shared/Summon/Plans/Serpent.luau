--!strict
-- Serpent: snakes, eels, sea serpents, worms, lindworms. A chain of overlapping tapering segments, one bone each,
-- laid in a gentle S so the silhouette reads as a snake even when idle. Hood, fin crest, forelegs, wings by tags.

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Heads = require(script.Parent.Parent.Heads)
local Face = require(script.Parent.Parent.Face)

local at = Geom.at
local rad = math.rad
local sin = math.sin

return function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id = string.lower(ctx.result.id)
	local worm = ctx.kind == "Worm" or string.find(id, "worm") ~= nil and not t.mythical
	local raised = t.hood or string.find(id, "cobra") ~= nil or (t.power or 5) >= 7
	local n = if detail <= 0 then 3 elseif detail == 1 then 4 elseif detail == 2 then 6 else 7
	local w = (if worm then 0.9 else 0.85) * (0.9 + t.durability * 0.03)
	local segLen = 4.8 / n
	B.boneIndex.Body.pos = { 0, w * 0.5, 0 }
	local parent = "Body"
	local pts = {}
	-- head end at the front (-Z), tail toward +Z, S-curve in x
	for i = 0, n do
		local u = i / n
		local x = sin(u * math.pi * 1.6) * 0.75
		local z = -1.2 + u * 4.8
		local y = w * 0.42 * (1 - u * 0.35)
		if raised and i == 0 then
			y += 1.4
			z += 0.4
		elseif raised and i == 1 then
			y += 0.55
		end
		pts[i] = { x, y, z }
	end
	for i = 1, n do
		local a, b = pts[i - 1], pts[i]
		local bname = B:bone("Seg" .. i, parent, a[1], a[2], a[3])
		B:addRig("spine", bname)
		local ww = w * (1 - (i - 1) / n * 0.55)
		local banded = worm and i % 2 == 0
		B:limb(a, b, ww, { col = if banded then "secondary" else "primary", mat = "scale", bone = bname, pri = 1 + i * 0.12, role = "body", name = "Seg" .. i, trail = i == n, depth = ww }, 0.45)
		if detail >= 3 and not worm and i <= n - 1 then
			-- belly scutes stripe in the secondary colour, sunk under each segment
			B:limb({ a[1], a[2] - ww * 0.22, a[3] }, { b[1], b[2] - ww * 0.22, b[3] }, ww * 0.7, { col = "belly", mat = "scale", bone = bname, pri = 3.5 + i * 0.05, role = "detail", depth = ww * 0.7 }, 0.3)
		end
		parent = bname
	end
	-- tail tip
	local last = pts[n]
	B:limb(last, { last[1] - 0.15, last[2] * 0.8, last[3] + 0.8 }, w * 0.32, { col = "primary", mat = "scale", bone = parent, pri = 2.1, role = "tail", trail = true }, 0.3)

	-- head
	local hp = pts[0]
	B:bone("Head", "Seg1", hp[1], hp[2], hp[3])
	B:setRig("head", "Head")
	local headS = w * (if worm then 1.25 else 1.35)
	if worm then
		local c = { hp[1], hp[2] + 0.05, hp[3] - 0.25 }
		local r = { headS * 0.5, headS * 0.5, headS * 0.5 }
		B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", bone = "Head", pri = 1.05, role = "head", name = "Head" })
		Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = "Head", mood = ctx.result.mood, detail = detail, kind = "cute", spacing = r[1] * 0.42, y = r[2] * 0.2, d = r[1] * 0.5, mouthY = -r[2] * 0.3, mouthW = r[1] * 0.7, forceMouth = true })
	else
		local info = Heads.reptile(B, { p = { hp[1], hp[2] - headS * 0.15, hp[3] + headS * 0.1 }, s = headS }, t)
		if t.horns or t.crown then
			Parts.horns(B, { bone = "Head", x = headS * 0.22, y = info.top[2] - headS * 0.08, z = info.top[3], len = headS * 0.7, w = headS * 0.16, kind = "swept", segs = 2, pri = 2.2, col = if t.crown then "gold" else "horn" })
		end
		if t.hood or string.find(id, "cobra") then
			B:mell(headS * 1.0, headS * 1.3, headS * 0.18, at(headS * 0.42, hp[2] - headS * 0.35, hp[3] + headS * 0.35, rad(-10), rad(-18), rad(-8)), { col = "secondary", mat = "scale", bone = "Seg1", pri = 1.5, role = "hood", name = "Hood#" })
		end
	end
	-- fin crest (sea serpents / dragons-of-the-sea)
	if detail >= 2 and (t.fins or t.aquatic or t.swims) then
		for i = 1, math.min(3, n - 1) do
			local p = pts[i]
			B:wedge(0.1, w * 0.8, segLen * 0.9, at(p[1], p[2] + w * 0.65, p[3] + segLen * 0.3), { col = "secondary", mat = "skin", bone = "Seg" .. i, pri = 2.6 + i * 0.1, role = "fin" })
		end
	elseif detail >= 2 and t.spikes then
		local sp = {}
		for i = 1, math.min(3, n - 1) do
			local p = pts[i]
			table.insert(sp, { p[1], p[2] + w * 0.35, p[3] + segLen * 0.4, 1, 0, "Seg" .. i })
		end
		Parts.spikeRow(B, { points = sp, h = w * 0.7, pri = 2.8 })
	end
	-- forelegs (lindworm) / wings (amphiptere)
	if t.legs or string.find(ctx.result.visual.silhouetteHint or "", "foreleg") then
		local p = pts[1]
		Parts.legPair(B, { tag = "F", parent = "Seg1", x = w * 0.5, y = p[2] + 0.1, z = p[3], w = w * 0.32, kind = "claw", claws = true, phase = 0 })
	end
	if (t.wings or t.flies) and not t.noWings then
		local p = pts[1]
		Parts.wings(B, { parent = "Seg1", x = w * 0.35, y = p[2] + w * 0.3, z = p[3], span = 2.6, kind = t.wingKind })
	end
	B:socket("core", at(pts[1][1], pts[1][2], pts[1][3]), "Seg1")
	B:setRig("gait", if worm then "inch" else "slither")
end
