--!strict
-- Structures: tower, building/house, wall, gate, bridge, castle, pyramid, lighthouse, windmill, igloo, tent,
-- statue/monolith. Furniture/Appliance/Container route to Plans/Objects.
-- Trim pieces (roof eaves, window frames, door) protrude past the wall face by >= 0.04 so nothing is flush.

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Heads = require(script.Parent.Parent.Heads)

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
	if t.castle or has("castle") or has("fort") or has("palace") or has("citadel") then
		return "castle"
	elseif has("lighthouse") then
		return "lighthouse"
	elseif has("windmill") or has("mill") then
		return "windmill"
	elseif t.pyramid then
		return "pyramid"
	elseif has("igloo") or has("dome") then
		return "igloo"
	elseif has("tent") or has("teepee") then
		return "tent"
	elseif has("bridge") then
		return "bridge"
	elseif has("gate") or has("portal") or has("arch") or has("door") then
		return "gate"
	elseif t.wall or has("fence") or has("barricade") or has("barrier") then
		return "wall"
	elseif t.tower or has("tower") or has("turret") or has("spire") or has("obelisk") then
		return "tower"
	elseif has("statue") or has("monolith") or has("totem") or has("monument") then
		return "statue"
	end
	return "building"
end

local function face(B: any, ctx: any, cf: any, w: number, o: any?)
	if Heads.wantsFace(B, ctx.traits) then
		Heads.objectFace(B, ctx.traits, cf, w, "Body", o)
	end
end

local K = {}

local function towerLite(B: any, ctx: any, o: any?)
	local oo = o or {}
	local detail = ctx.detail
	local r = oo.r or 1.3
	local h = oo.h or 5.5
	local x, z = oo.x or 0, oo.z or 0
	local col = oo.col or "stone"
	B:cyl(h, r * 2, at(x, h / 2, z, 0, 0, rad(90)), { col = col, mat = "stone", pri = oo.pri or 1, role = "body", name = oo.name or "Tower" })
	-- corbelled parapet ring (wider), then crenellations or a cone roof
	B:cyl(0.5, r * 2 + 0.36, at(x, h + 0.2, z, 0, 0, rad(90)), { col = "darkStone", mat = "stone", pri = (oo.pri or 1) + 0.3, role = "body", name = (oo.name or "Tower") .. "Ring" })
	if oo.roof ~= false and (oo.cone or ctx.traits.roof or detail <= 1) then
		-- tall spire ellipsoid centred at the parapet: its lower half is hidden in the tower, the upper half
		-- reads as a pointed roof
		B:ell(r * 2.3, r * 4.4, r * 2.3, at(x, h + 0.4, z), { col = "roof", mat = "wood", pri = (oo.pri or 1) + 0.2, role = "roof", name = (oo.name or "Tower") .. "Roof" })
		if detail >= 2 then
			B:cyl(0.9, 0.08, at(x, h + 0.3 + r * 2.2, z, 0, 0, rad(90)), { col = "dark", mat = "wood", pri = 2.6, role = "detail" })
			B:block(0.6, 0.35, 0.05, at(x + 0.3, h + 0.55 + r * 2.2, z), { col = "secondary", mat = "cloth", pri = 2.7, role = "flag", name = "Flag", trail = true })
		end
	elseif detail >= 2 then
		Parts.crenellations(B, { kind = "round", cx = x, cz = z, y = h + 0.42, r = r + 0.08, n = if detail >= 3 then 8 else 6, s = 0.45, pri = 2.5 })
	end
	if detail >= 2 then
		-- arrow-slit windows: dark slabs sunk into the curved wall (curved surface, so no coplanar faces)
		for i = 1, (if detail >= 3 then 2 else 1) do
			B:block(0.22, 0.75, 0.3, at(x, h * (0.4 + i * 0.2), z - r + 0.08), { col = "darker", mat = "stone", pri = 2.8 + i * 0.1, role = "window" })
		end
	end
	if not oo.noFace then
		face(B, ctx, at(x, h * 0.45, z - r - 0.02), r * 1.4, { curve = 0.35 })
	end
end

-- Hero tower: battered plinth, stone shaft, string course, a corbelled machicolation ring with merlons standing
-- proud of it, an optional pyramid roof set inside the parapet (four wedges whose hidden back and bottom faces are
-- staggered so none coincide), framed windows and an arched door with the pane/door set back from its frame.
function K.tower(B: any, ctx: any, o: any?)
	local oo = o or {}
	if oo.lite then
		return towerLite(B, ctx, oo)
	end
	local detail = ctx.detail
	local id = string.lower(ctx.result.id)
	local r = oo.r or 1.3
	local h = oo.h or 5.6
	local col = oo.col or "stone"
	local magic = ctx.result.element == "Arcane" or string.find(id, "wizard") ~= nil or string.find(id, "mage") ~= nil
	local roofed = oo.cone or ctx.traits.roof or magic or detail <= 0
	B:cyl(h, r * 2, at(0, h / 2, 0, 0, 0, rad(90)), { col = col, mat = "stone", pri = 1, role = "body", name = "Tower" })
	B:cyl(0.9, r * 2.36, at(0, 0.45, 0, 0, 0, rad(90)), { col = "darkStone", mat = "stone", pri = 1.2, role = "body", name = "Plinth" })
	-- corbelled top: wider ring, then merlons around its rim
	local topY = h + 0.3
	B:cyl(0.7, r * 2.44, at(0, h + 0.05, 0, 0, 0, rad(90)), { col = "darkStone", mat = "stone", pri = 1.1, role = "body", name = "Machicolation" })
	if detail >= 1 then
		local n = if detail >= 3 then 8 elseif detail == 2 then 7 else 6
		for i = 1, n do
			local a2 = (i - 0.5) / n * math.pi * 2
			B:block(0.55, 0.62, 0.42, at(sin(a2) * r * 1.06, topY + 0.38, cos(a2) * r * 1.06, 0, a2, 0),
				{ col = col, mat = "stone", pri = 1.5 + i * 0.01, role = "detail", name = "Merlon" .. i })
		end
	end
	if roofed then
		-- pyramid roof: four wedges, slopes outward, set inside the parapet
		local rr, rh = r * 1.02, r * 2.4
		local roofCol = if magic then "secondary" else "roof"
		for i = 1, 4 do
			local yaw = (i - 1) * math.pi / 2
			-- every wedge gets its own base height and its back face sits 0.03 past the axis: no shared planes
			local odd = i % 2 == 0
			local lift = ({ 0, 0.04, 0.02, 0.06 })[i]
			local back = 0.03
			local f = Geom.mul(at(0, topY + 0.1 + lift + (rh - lift) / 2, 0, 0, yaw, 0), at(0, 0, -rr / 2 + back, 0, 0, 0))
			B:wedge(rr * 2 - (if odd then 0.04 else 0), rh - lift, rr, f, { col = roofCol, mat = "wood", pri = 1.3 + i * 0.01, role = "roof", name = "Roof" .. i })
		end
		if detail >= 2 then
			B:rod({ 0, topY + rh - 0.2, 0 }, { 0, topY + rh + 1.0, 0 }, 0.09, { col = "dark", mat = "metal", pri = 2.4, role = "detail", name = "Pole" })
			B:block(0.75, 0.42, 0.05, at(0.4, topY + rh + 0.75, 0.01, 0, 0, rad(-4)), { col = if magic then "glow" else "secondary", mat = "cloth", pri = 2.5, role = "flag", name = "Flag", trail = true, needs = "Pole" })
		end
		if magic then
			B:ball(0.55, at(0, topY + rh + 0.15, 0), { col = "glow", mat = "neon", glow = true, pri = 1.45, role = "gem", name = "Beacon", noCore = true })
		end
	end
	-- door: frame proud of the round wall (0.14), dark planks proud by only 0.05 so the door sits back inside it
	local fz = -r
	B:block(1.1, 1.55, 0.36, at(0, 0.97 + 0.775, fz + 0.04), { col = "darkStone", mat = "stone", pri = 1.35, role = "door", name = "DoorFrame" })
	B:block(0.78, 1.3, 0.27, at(0, 0.93 + 0.65, fz - 0.08), { col = "darkWood", mat = "wood", pri = 1.4, role = "door", name = "Door", needs = "DoorFrame" })
	if detail >= 2 then
		-- framed windows up the shaft (stagger around the curve so each frame meets the wall at a new angle)
		local nw = if detail >= 3 then 3 else 2
		for i = 1, nw do
			local a2 = (i - (nw + 1) / 2) * rad(34)
			local wy = 0.9 + 1.6 + i * (h - 2.6) / (nw + 0.5)
			local fx, fz2 = sin(a2) * r, -cos(a2) * r
			B:block(0.62, 0.95, 0.3, at(fx * 0.98, wy, fz2 * 0.98, 0, -a2, 0), { col = "darkStone", mat = "stone", pri = 1.6 + i * 0.05, role = "window", name = "WinFrame" .. i })
			B:block(0.38, 0.7, 0.22, at(fx * 1.03, wy - 0.03, fz2 * 1.03, 0, -a2, 0), { col = if magic then "glow" else "darker", mat = if magic then "neon" else "glass", glow = magic, pri = 1.62 + i * 0.05, role = "window", name = "Win" .. i, needs = "WinFrame" .. i, noCore = true })
		end
		B:cyl(0.24, r * 2.12, at(0, 0.9 + 1.75 + 0.02, 0, 0, 0, rad(90)), { col = "darkStone", mat = "stone", pri = 2.2, role = "detail", name = "Course" })
	end
	if not oo.noFace then
		face(B, ctx, at(0, h * 0.52, -r - 0.02), r * 1.4, { curve = 0.35 })
	end
	B:socket("core", at(0, h * 0.6, 0), "Body")
end

function K.building(B: any, ctx: any)
	local detail = ctx.detail
	local W, D, H = 4.0, 3.2, 2.6
	B:block(W, H, D, at(0, H / 2, 0), { col = "primary", mat = "plastic", pri = 1, role = "body", name = "Walls" })
	-- pitched roof: two wedges back to back, each 0.02 past the ridge so they interpenetrate (not touching faces)
	local rh, overhang = 1.6, 0.35
	-- a wedge's vertical face is at +Z and its slope faces -Z: the front half needs no rotation (ridge at z = 0)
	B:wedge(W + overhang * 2, rh, D / 2 + overhang + 0.02, at(0, H + rh / 2 - 0.02, -(D / 2 + overhang) / 2 + 0.01, 0, 0, 0), { col = "roof", mat = "wood", pri = 1.1, role = "roof", name = "RoofF" })
	B:wedge(W + overhang * 2 - 0.04, rh - 0.02, D / 2 + overhang + 0.02, at(0, H + rh / 2 - 0.03, (D / 2 + overhang) / 2 - 0.01, 0, math.pi, 0), { col = "roof", mat = "wood", pri = 1.1, role = "roof", name = "RoofB" })
	-- stone foundation course (wider than the walls, so its faces never meet theirs)
	B:block(W + 0.24, 0.34, D + 0.24, at(0, 0.15, 0), { col = "darkStone", mat = "stone", pri = 1.25, role = "body", name = "Foundation" })
	-- door: a proud timber frame with the door set back inside it (frame front 0.16 out, door front 0.07 out)
	B:block(1.06, 1.62, 0.2, at(0.9, 0.34 + 0.81, -D / 2 - 0.06), { col = "wood", mat = "wood", pri = 1.35, role = "door", name = "DoorFrame" })
	B:block(0.78, 1.42, 0.16, at(0.9, 0.36 + 0.71, -D / 2 + 0.01), { col = "darkWood", mat = "wood", pri = 1.4, role = "door", name = "Door", needs = "DoorFrame" })
	if detail >= 1 then
		B:block(1.0, 0.92, 0.2, at(-0.9, 1.55, -D / 2 - 0.06), { col = "white", mat = "wood", pri = 1.55, role = "window", name = "WindowFrame" })
		B:block(0.78, 0.7, 0.16, at(-0.9, 1.55, -D / 2 + 0.01), { col = "glass", mat = "glass", pri = 1.6, role = "window", name = "Window", needs = "WindowFrame" })
	end
	if detail >= 2 then
		-- cross mullion inside the window, standing between pane and frame depth
		B:block(0.07, 0.72, 0.17, at(-0.9, 1.55, -D / 2 - 0.005), { col = "white", mat = "wood", pri = 2.6, role = "detail", name = "Mullion", needs = "WindowFrame" })
		B:block(0.8, 0.07, 0.18, at(-0.9, 1.56, -D / 2 - 0.012), { col = "white", mat = "wood", pri = 2.65, role = "detail", name = "Transom", needs = "WindowFrame" })
	end
	if detail >= 2 then
		B:block(0.55, 1.4, 0.55, at(-1.2, H + 1.3, 0.6), { col = "secondary", mat = "stone", pri = 2.0, role = "detail", name = "Chimney" })
		B:block(1.16, 0.12, 0.34, at(-0.9, 1.06, -D / 2 - 0.1), { col = "white", mat = "wood", pri = 2.5, role = "detail", name = "Sill" })
		B:socket("smoke", at(-1.2, H + 2.1, 0.6), "Body")
		B:emit("smoke", nil, { socket = "smoke", rate = 8 })
	end
	if detail >= 3 then
		B:mblock(0.1, 0.75, 0.85, at(W / 2 + 0.03, 1.5, 0), { col = "glass", mat = "glass", pri = 3.0, role = "window", name = "SideWindow#" })
	end
	face(B, ctx, at(-0.2, 1.5, -D / 2 - 0.18), 2.6)
end

function K.wall(B: any, ctx: any)
	local detail = ctx.detail
	local W, H, D = 6.0, 2.6, 1.0
	B:block(W, H, D, at(0, H / 2, 0), { col = "stone", mat = "stone", pri = 1, role = "body", name = "Wall" })
	B:block(W + 0.2, 0.35, D + 0.24, at(0, H + 0.12, 0), { col = "darkStone", mat = "stone", pri = 1.2, role = "body", name = "Coping" })
	B:block(W + 0.3, 0.5, D + 0.36, at(0, 0.24, 0), { col = "darkStone", mat = "stone", pri = 1.3, role = "body", name = "Footing" })
	if detail >= 1 then
		local n = if detail >= 3 then 5 else 4
		for i = 1, n do
			local x = (i - (n + 1) / 2) * (W / n)
			B:block(W / n * 0.5, 0.65, D * 0.9, at(x, H + 0.6, 0), { col = "stone", mat = "stone", pri = 1.5 + i * 0.05, role = "detail", name = "Merlon" .. i })
		end
	end
	if detail >= 3 then
		-- bricks hinted by a few proud stones (each sticks out 0.05 from the face)
		for i = 1, 4 do
			B:block(0.9, 0.45, 0.2, at(-2.2 + i * 1.0 + (i % 2) * 0.3, 0.8 + (i % 2) * 0.9, -D / 2 - 0.02), { col = "darkStone", mat = "stone", pri = 3.5 + i * 0.05, role = "detail" })
		end
	end
	face(B, ctx, at(0, 1.4, -D / 2 - 0.06), 2.4)
	B:setRig("gait", "static")
end

function K.gate(B: any, ctx: any)
	local detail = ctx.detail
	local portal = string.find(string.lower(ctx.result.id), "portal") ~= nil
	if portal then
		-- stone ring of blocks around a glowing disc
		local n = if detail <= 1 then 6 else 10
		for i = 1, n do
			local a = (i - 0.5) / n * math.pi * 2
			B:block(0.9, 0.9, 0.7, at(sin(a) * 2.0, 2.6 + cos(a) * 2.0, 0, 0, 0, -a), { col = "stone", mat = "stone", pri = 1 + i * 0.01, role = "body", name = "Stone" .. i })
		end
		B:cyl(0.12, 3.6, at(0, 2.6, 0, 0, rad(90), 0), { col = "glow", mat = "neon", glow = true, pri = 1.2, role = "gem", name = "Portal", noCore = true })
		B:bone("Spin", "Body", 0, 2.6, 0)
		-- stepped plinth and a proud keystone: the ring stands on something and has a top
		B:block(4.6, 0.5, 1.7, at(0, 0.25, 0), { col = "darkStone", mat = "stone", pri = 1.25, role = "body", name = "Plinth" })
		B:block(3.3, 0.36, 1.3, at(0, 0.66, 0.03), { col = "stone", mat = "stone", pri = 1.6, role = "detail", name = "Step" })
		B:block(1.0, 1.25, 0.98, at(0, 4.62, 0.01), { col = "darkStone", mat = "stone", pri = 1.3, role = "body", name = "Keystone" })
		-- vortex: two offset swirl lobes on the rotor (they read as turning) and a hot eye, each its own depth
		B:ell(3.0, 1.15, 0.06, at(0, 2.6, -0.12, 0, 0, rad(20)), { col = "secondary", mat = "neon", glow = true, tr = 0.25, bone = "Spin", pri = 1.35, role = "gem", name = "Swirl1", noCore = true })
		B:ell(1.15, 2.6, 0.06, at(0, 2.6, -0.2, 0, 0, rad(20)), { col = "secondary", mat = "neon", glow = true, tr = 0.35, bone = "Spin", pri = 1.45, role = "gem", name = "Swirl2", noCore = true })
		B:cyl(0.08, 1.1, at(0, 2.6, -0.28, 0, rad(90), 0), { col = "flameCore", mat = "neon", glow = true, pri = 1.5, role = "gem", name = "VortexEye", noCore = true })
		if detail >= 2 then
			-- runes cut into every other stone (sunk 0.01 into the face, never flush)
			for i = 1, n, 2 do
				local a = (i - 0.5) / n * math.pi * 2
				B:block(0.34, 0.34, 0.06, at(sin(a) * 2.0, 2.6 + cos(a) * 2.0, -0.37, 0, 0, -a + rad(45)), { col = "glow", mat = "neon", glow = true, pri = 1.9 + i * 0.01, role = "detail", name = "Rune" .. i, noCore = true })
			end
		end
		B:addRig("rotors", { bone = "Spin", axis = "Z", speed = 1 })
		B:socket("core", at(0, 2.6, 0), "Body")
		return
	end
	B:block(1.2, 4.2, 1.2, at(-1.9, 2.1, 0), { col = "stone", mat = "stone", pri = 1, role = "body", name = "PostL" })
	B:block(1.2, 4.2, 1.2, at(1.9, 2.1, 0), { col = "stone", mat = "stone", pri = 1, role = "body", name = "PostR" })
	B:block(5.2, 1.0, 1.4, at(0, 4.6, 0), { col = "darkStone", mat = "stone", pri = 1.05, role = "body", name = "Lintel" })
	B:block(2.66, 3.4, 0.3, at(0, 1.7, 0.05), { col = "wood", mat = "wood", pri = 1.2, role = "door", name = "Doors" })
	if detail >= 2 then
		for i = 1, 3 do
			B:block(2.7, 0.18, 0.36, at(0, 0.6 + i * 0.85, 0.05), { col = "dark", mat = "metal", pri = 2.2 + i * 0.05, role = "detail", name = "Band" .. i })
		end
		Parts.crenellations(B, { kind = "rect", cx = 0, cz = 0, y = 5.08, w = 4.8, d = 1.0, n = 2, s = 0.5, pri = 2.8 })
	end
	face(B, ctx, at(0, 2.2, -0.12), 2.2)
end

function K.bridge(B: any, ctx: any)
	local detail = ctx.detail
	local L = 7.0
	-- arched deck from three planks at slightly different pitches, piers underneath, rails
	local n = if detail <= 1 then 3 else 5
	local R = 9.0
	local span = math.asin((L / 2) / R)
	for i = 1, n do
		local a = -span + (i - 0.5) / n * span * 2
		local z = math.sin(a) * R
		local y = 1.0 + (math.cos(a) * R - math.cos(span) * R)
		local seg = L / n + 0.3
		B:block(2.2 - (i % 2) * 0.04, 0.35, seg, at(0, y, z, a, 0, 0), { col = if i % 2 == 0 then "darkWood" else "wood", mat = "wood", pri = 1 + math.abs(i - (n + 1) / 2) * 0.05, role = "body", name = "Deck" .. i })
	end
	B:mblock(0.6, 1.5, 0.6, at(0.8, 0.7, -L * 0.33), { col = "stone", mat = "stone", pri = 1.3, role = "body", name = "PierF#" })
	B:mblock(0.6, 1.5, 0.6, at(0.8, 0.7, L * 0.33), { col = "stone", mat = "stone", pri = 1.3, role = "body", name = "PierB#" })
	if detail >= 2 then
		B:mblock(0.14, 0.14, L, at(1.05, 2.4, 0), { col = "darkWood", mat = "wood", pri = 2.0, role = "detail", name = "Rail#" })
		for i = 1, 3 do
			B:mblock(0.14, 0.8, 0.14, at(1.05, 2.0 - math.abs(i - 2) * 0.2, (i - 2) * L / 3), { col = "darkWood", mat = "wood", pri = 2.2 + i * 0.05, role = "detail", name = "Post" .. i .. "#" })
		end
	end
	face(B, ctx, at(0, 1.4, -L / 2 - 0.2, rad(-8), 0, 0), 1.6)
end

function K.castle(B: any, ctx: any)
	local detail = ctx.detail
	local W, D, H = 5.0, 4.0, 3.2
	B:block(W, H, D, at(0, H / 2, 0), { col = "stone", mat = "stone", pri = 1, role = "body", name = "Keep" })
	B:block(1.6, 2.2, 0.3, at(0, 1.1, -D / 2 - 0.1), { col = "darkWood", mat = "wood", pri = 1.3, role = "door", name = "Gate" })
	local corners = { { 1, -1 }, { -1, -1 }, { 1, 1 }, { -1, 1 } }
	local n = if detail <= 1 then 2 else 4
	for i = 1, n do
		local c = corners[i]
		K.tower(B, ctx, { lite = true, x = c[1] * W / 2, z = c[2] * D / 2, r = 0.95, h = H + 1.6, name = "Tower" .. i, pri = 1.1 + i * 0.05, cone = true, noFace = true })
	end
	if detail >= 2 then
		Parts.crenellations(B, { kind = "rect", cx = 0, cz = 0, y = H, w = W - 1.6, d = D - 1.6, n = if detail >= 3 then 3 else 2, s = 0.45, pri = 3.0 })
	end
	face(B, ctx, at(0, H * 0.72, -D / 2 - 0.05), 2.4)
end

function K.pyramid(B: any, ctx: any)
	local detail = ctx.detail
	local steps = if detail <= 1 then 3 else 5
	local base = 6.0
	for i = 1, steps do
		local w = base * (1 - (i - 1) / steps)
		B:block(w, 0.9, w, at(0, (i - 0.5) * 0.9 - (i - 1) * 0.02, 0, 0, rad(i * 0.5), 0), { col = "primary", mat = "stone", pri = 1 + i * 0.05, role = "body", name = "Step" .. i })
	end
	B:wedge(base / steps * 0.98, 1.0, base / steps * 0.98, at(0, steps * 0.88 + 0.45, 0), { col = "gold", mat = "metal", pri = 1.4, role = "detail", name = "Cap" })
	face(B, ctx, at(0, 1.3, -base / 2 - 0.02), 2.6)
end

function K.lighthouse(B: any, ctx: any)
	local detail = ctx.detail
	local h = 6.0
	B:limb({ 0, 0, 0 }, { 0, h, 0 }, 2.0, { col = "primary", mat = "plastic", pri = 1, role = "body", name = "Tower", depth = 2.0 }, 0.0)
	for i = 1, (if detail >= 2 then 2 else 1) do
		B:ell(2.0 - i * 0.25 + 0.06, 0.7, 2.0 - i * 0.25 + 0.06, at(0, h * (0.3 + i * 0.3), 0), { col = "secondary", mat = "plastic", pri = 1.4 + i * 0.1, role = "detail", name = "Stripe" .. i })
	end
	B:cyl(0.3, 2.0, at(0, h * 0.95, 0, 0, 0, rad(90)), { col = "dark", mat = "metal", pri = 1.2, role = "body", name = "Gallery" })
	B:cyl(1.0, 1.2, at(0, h * 0.95 + 0.6, 0, 0, 0, rad(90)), { col = "glow", mat = "neon", glow = true, pri = 1.3, role = "gem", name = "Lamp", noCore = true })
	B:limb({ 0, h * 0.95 + 1.05, 0 }, { 0, h * 0.95 + 1.9, 0 }, 1.45, { col = "secondary", mat = "metal", pri = 1.35, role = "roof", name = "Cap" }, 0.02)
	table.insert(B.lights, { kind = "PointLight", colour = { 1, 0.95, 0.7 }, brightness = 2, range = 1.5, socket = "core", shadows = false })
	B:socket("core", at(0, h * 0.95 + 0.6, 0), "Body")
	face(B, ctx, at(0, h * 0.42, -0.86), 1.3, { curve = 0.4 })
end

function K.windmill(B: any, ctx: any)
	local detail = ctx.detail
	B:limb({ 0, 0, 0 }, { 0, 4.6, 0 }, 2.4, { col = "primary", mat = "wood", pri = 1, role = "body", name = "Tower" }, 0.0)
	B:limb({ 0, 4.3, 0 }, { 0, 5.6, 0 }, 1.9, { col = "secondary", mat = "wood", pri = 1.1, role = "roof", name = "Cap" }, 0.05)
	B:bone("Sails", "Body", 0, 4.4, -1.05)
	B:addRig("rotors", { bone = "Sails", axis = "Z", speed = 1.5 })
	B:ball(0.5, at(0, 4.4, -1.05), { col = "dark", mat = "wood", bone = "Sails", pri = 1.3, role = "detail", name = "Hub" })
	for i = 1, 4 do
		local a = (i - 1) * math.pi / 2 + rad(15)
		local cx, cy = sin(a) * 1.5, cos(a) * 1.5
		B:block(0.65, 2.8, 0.06 + i * 0.012, at(cx, 4.4 + cy, -1.12 - i * 0.015, 0, 0, -a), { col = "sail", mat = "cloth", bone = "Sails", pri = 1.2 + i * 0.03, role = "sail", name = "Sail" .. i, trail = i == 1 })
	end
	if detail >= 2 then
		B:block(0.7, 1.1, 0.12, at(0, 0.55, -1.0, rad(-14), 0, 0), { col = "darkWood", mat = "wood", pri = 2.0, role = "door", name = "Door" })
	end
	face(B, ctx, at(0, 2.6, -1.0, rad(-12), 0, 0), 1.6, { curve = 0.3 })
end

function K.igloo(B: any, ctx: any)
	local detail = ctx.detail
	local c, r = { 0, 0.2, 0 }, { 2.5, 2.3, 2.5 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "ice", pri = 1, role = "body", name = "Dome" })
	B:limb({ 0, 0.85, -1.8 }, { 0, 0.85, -3.0 }, 1.6, { col = "primary", mat = "ice", pri = 1.2, role = "body", name = "Tunnel" }, 0.05)
	B:ell(1.0, 1.1, 0.4, at(0, 0.7, -3.1), { col = "darker", mat = "skin", pri = 1.4, role = "door", name = "Door" })
	if detail >= 2 then
		for i = 1, 2 do
			B:ell(r[1] * 2.02, 0.12, r[3] * 2.02, at(0, c[2] + i * 0.7, 0), { col = "secondary", mat = "ice", pri = 2.4 + i * 0.1, role = "detail" })
		end
	end
	if Heads.wantsFace(B, ctx.traits) then
		local Face = require(script.Parent.Parent.Face)
		Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = "Body", mood = ctx.result.mood, detail = math.max(1, detail), kind = "cute", spacing = 0.9, y = 1.25, d = 0.7, noMouth = true })
	end
end

function K.tent(B: any, ctx: any)
	B:wedge(3.6, 2.6, 1.8, at(0, 1.3, -0.88, 0, 0, 0), { col = "primary", mat = "cloth", pri = 1, role = "body", name = "FlyF" })
	B:wedge(3.56, 2.58, 1.8, at(0, 1.29, 0.88, 0, math.pi, 0), { col = "primary", mat = "cloth", pri = 1.05, role = "body", name = "FlyB" })
	B:mwedge(0.08, 1.4, 0.7, at(0.3, 0.7, -1.4, 0, math.pi, 0), { col = "secondary", mat = "cloth", pri = 1.5, role = "door", name = "Flap#" })
	face(B, ctx, at(0, 1.3, -0.95, rad(-35), 0, 0), 1.4)
end

function K.statue(B: any, ctx: any)
	local detail = ctx.detail
	B:block(2.4, 0.8, 2.4, at(0, 0.4, 0), { col = "darkStone", mat = "stone", pri = 1.05, role = "body", name = "Plinth" })
	B:ell(1.6, 3.0, 1.2, at(0, 2.3, 0), { col = "stone", mat = "stone", pri = 1, role = "body", name = "Figure" })
	B:ball(1.2, at(0, 4.2, -0.05), { col = "stone", mat = "stone", pri = 1.1, role = "head", name = "Head" })
	if detail >= 2 then
		B:mlimb({ 0.7, 3.3, 0 }, { 1.3, 4.3, -0.2 }, 0.42, { col = "stone", mat = "stone", pri = 1.6, role = "limb", name = "Arm#" }, 0.2)
	end
	face(B, ctx, at(0, 4.2, -0.62), 0.9, { curve = 0.6 })
end

return function(B: any, ctx: any)
	local kind = kindOf(ctx)
	if kind == "tower" then
		K.tower(B, ctx, { cone = ctx.traits.roof })
	else
		local f = (K :: any)[kind] or K.building
		f(B, ctx)
	end
	B.boneIndex.Body.pos = { 0, 0.5, 0 }
	if B.sockets.core == nil then
		B:socket("core", at(0, 2, 0), "Body")
	end
	B:setRig("gait", "static")
end
