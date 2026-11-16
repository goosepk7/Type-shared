--!strict
-- Vehicles and machines: car, truck/van/bus, train, tank (Tracked), boat/ship (Boat), submarine, aircraft,
-- helicopter, rocket, bike, ufo, sled, cart, balloon, board. Specialised plans set ctx.kind.
-- Windows are glass slabs that protrude 0.02 past the body on the faces they show through (never flush).

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Heads = require(script.Parent.Parent.Heads)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local ROUTE: { [string]: string } = {
	CarWheeled = "car", Tracked = "tank", Aircraft = "plane", Helicopter = "heli", Boat = "boat", Submarine = "sub", Rocket = "rocket",
}

local function kindOf(ctx: any): string
	if ctx.kind and ROUTE[ctx.kind] then
		return ROUTE[ctx.kind]
	end
	local t, id = ctx.traits, string.lower(ctx.result.id)
	local function has(w: string): boolean
		return string.find(id, w, 1, true) ~= nil
	end
	if t.tank or t.treads then
		return "tank"
	elseif t.ufo or has("saucer") then
		return "ufo"
	elseif t.rocket or has("shuttle") then
		return "rocket"
	elseif t.rotor or has("heli") or has("chopper") or has("drone") then
		return "heli"
	elseif t.submarine then
		return "sub"
	elseif t.plane or t.jet or has("plane") or has("jet") or has("glider") or has("biplane") then
		return "plane"
	elseif t.ship or t.boat or t.sail or t.raft or has("boat") or has("ship") or has("canoe") or has("ferry") or has("yacht") then
		return "boat"
	elseif t.train or has("tram") or has("trolley") then
		return "train"
	elseif t.bike or has("cycle") or has("scooter") or has("penny") then
		return "bike"
	elseif t.balloon or has("blimp") or has("airship") or has("zeppelin") then
		return "balloon"
	elseif t.sled then
		return "sled"
	elseif t.cart then
		return "cart"
	elseif t.board then
		return "board"
	elseif t.truck or has("bus") or has("van") or has("truck") or has("ambulance") or has("lorry") or has("tractor") then
		return "truck"
	end
	if t.flies then
		return "plane"
	elseif t.swims then
		return "boat"
	end
	return "car"
end

local function face(B: any, ctx: any, cf: any, w: number, o: any?)
	if Heads.wantsFace(B, ctx.traits) then
		Heads.objectFace(B, ctx.traits, cf, w, "Body", o)
	end
end

local function lights(B: any, detail: number, x: number, y: number, zf: number, zb: number, r: number)
	if detail >= 2 then
		B:mball(r, at(x, y, zf), { col = "cream", mat = "neon", glow = true, pri = 2.3, role = "light", name = "Headlight#" })
	end
	if detail >= 3 then
		B:mball(r * 0.8, at(x, y, zb), { col = "red", mat = "neon", glow = true, pri = 3.2, role = "light", name = "Taillight#" })
	end
end

local K = {}

function K.car(B: any, ctx: any, truck: boolean)
	local detail = ctx.detail
	local id = string.lower(ctx.result.id)
	local W, L = 2.1, if truck then 5.0 else 4.3
	local r = if truck then 0.62 else 0.52
	local chassisH = 0.8
	local y0 = r * 1.15
	B.boneIndex.Body.pos = { 0, y0 + chassisH / 2, 0 }
	B:block(W, chassisH, L, at(0, y0 + chassisH / 2, 0), { col = "primary", mat = "plastic", pri = 1, role = "body", name = "Chassis" })
	-- rounded nose and tail (ellipsoids sunk into the chassis ends)
	B:ell(W * 0.98, chassisH * 0.96, 1.0, at(0, y0 + chassisH * 0.48, -L / 2 + 0.05), { col = "primary", mat = "plastic", pri = 1.3, role = "body", name = "Nose" })
	if detail >= 2 then
		B:ell(W * 0.98, chassisH * 0.96, 0.8, at(0, y0 + chassisH * 0.48, L / 2 - 0.05), { col = "primary", mat = "plastic", pri = 1.9, role = "body", name = "Tail" })
	end
	local cabL = if truck then 1.7 else 2.1
	local cabZ = if truck then -L * 0.22 else 0.15
	local cabH = if truck or string.find(id, "bus") or string.find(id, "van") then 1.25 else 0.85
	local tall = string.find(id, "bus") ~= nil or string.find(id, "van") ~= nil or string.find(id, "ambulance") ~= nil
	if tall then
		cabL = L * 0.9
		cabZ = 0.05
		cabH = 1.45
	end
	local cabY = y0 + chassisH + cabH / 2 - 0.05
	B:block(W * 0.86, cabH, cabL, at(0, cabY, cabZ), { col = if truck then "primary" else "secondary", mat = "plastic", pri = 1.1, role = "body", name = "Cabin" })
	-- window band: slightly wider than the cabin (side glass shows), shorter and lower than its top
	if detail >= 1 then
		B:block(W * 0.86 + 0.04, cabH * 0.5, cabL * 0.86, at(0, cabY + cabH * 0.08, cabZ), { col = "glass", mat = "glass", pri = 1.5, role = "window", name = "Windows" })
	end
	-- windshield: glass wedge leaning against the cabin front
	B:wedge(W * 0.8, cabH * 0.86, 0.6, at(0, cabY - 0.02, cabZ - cabL / 2 - 0.27), { col = "glass", mat = "glass", pri = 1.4, role = "window", name = "Windshield" })
	if truck and not tall then
		-- open bed
		local bedZ = L * 0.22
		B:mblock(0.16, 0.6, L * 0.48, at(W * 0.45, y0 + chassisH + 0.27, bedZ), { col = "secondary", mat = "plastic", pri = 1.6, role = "body", name = "BedSide#" })
		B:block(W * 0.95, 0.6, 0.16, at(0, y0 + chassisH + 0.27, bedZ + L * 0.235), { col = "secondary", mat = "plastic", pri = 2.1, role = "body", name = "Tailgate" })
	end
	if string.find(id, "police") or string.find(id, "ambulance") or string.find(id, "fire") then
		B:block(W * 0.5, 0.2, 0.35, at(0, cabY + cabH / 2 + 0.08, cabZ), { col = "red", mat = "neon", glow = true, pri = 1.8, role = "light", name = "Siren" })
	end
	local wz = L * 0.33
	Parts.wheelPair(B, { index = 1, x = W * 0.46, z = -wz, r = r, w = 0.45 })
	Parts.wheelPair(B, { index = 2, x = W * 0.46, z = wz, r = r, w = 0.45 })
	if truck and L > 4.6 and detail >= 2 then
		Parts.wheelPair(B, { index = 3, x = W * 0.46, z = wz - r * 2.2, r = r, w = 0.45 })
	end
	lights(B, detail, W * 0.33, y0 + chassisH * 0.6, -L / 2 - 0.38, L / 2 + 0.3, 0.3)
	face(B, ctx, at(0, cabY + 0.02, cabZ - cabL / 2 - 0.5, rad(-28), 0, 0), W * 0.8, { eye = 0.24 })
	B:socket("core", at(0, cabY, cabZ), "Body")
	B:socket("muzzle", at(0, y0 + chassisH * 0.5, -L / 2 - 0.5), "Body")
	B:setRig("gait", "drive")
end

function K.tank(B: any, ctx: any)
	local detail = ctx.detail
	local W, L, H = 2.6, 4.4, 0.85
	local tread = 0.95
	B.boneIndex.Body.pos = { 0, tread + H / 2, 0 }
	B:block(W - 0.5, H, L * 0.86, at(0, tread + H / 2 - 0.05, 0.1), { col = "primary", mat = "metal", pri = 1, role = "body", name = "Hull" })
	-- sloped glacis plate in front
	B:wedge(W - 0.52, H * 0.96, 0.9, at(0, tread + H / 2 - 0.06, -L * 0.43 + 0.1 - 0.42, 0, math.pi, 0) :: any, { col = "primary", mat = "metal", pri = 1.2, role = "body", name = "Glacis" })
	Parts.treads(B, { x = W / 2 - 0.12, len = L, h = tread, w = 0.6, wheels = if detail >= 2 then 3 else 0 })
	-- turret + barrel on yaw/pitch bones
	local ty = tread + H + 0.32
	B:bone("Turret", "Body", 0, ty, 0.1)
	B:setRig("turret", "Turret")
	B:ell(W * 0.62, 0.78, 1.9, at(0, ty + 0.05, 0.25), { col = "primary", mat = "metal", bone = "Turret", pri = 1.05, role = "body", name = "Turret" })
	B:bone("Barrel", "Turret", 0, ty + 0.1, -0.6)
	B:setRig("barrel", "Barrel")
	B:cyl(2.6, 0.26, at(0, ty + 0.1, -1.75, 0, rad(90), 0), { col = "dark", mat = "metal", bone = "Barrel", pri = 1.1, role = "cannon", name = "Barrel" })
	if detail >= 2 then
		B:cyl(0.45, 0.4, at(0, ty + 0.1, -3.0, 0, rad(90), 0), { col = "dark", mat = "metal", bone = "Barrel", pri = 2.2, role = "cannon", name = "Muzzle" })
		B:cyl(0.3, 0.55, at(0.35, ty + 0.5, 0.55, 0, 0, rad(90)), { col = "dark", mat = "metal", bone = "Turret", pri = 2.6, role = "detail", name = "Hatch" })
	end
	B:socket("muzzle", at(0, ty + 0.1, -3.3), "Barrel")
	face(B, ctx, at(0, ty + 0.12, 0.25 - 0.95 + 0.12), 1.2, { eye = 0.28, curve = 0.2 })
	B:socket("core", at(0, ty, 0), "Turret")
	B:setRig("gait", "drive")
end

function K.boat(B: any, ctx: any)
	local detail = ctx.detail
	local W, L, H = 2.0, 4.6, 1.0
	local y = 0.6
	B.boneIndex.Body.pos = { 0, y, 0 }
	-- hull: box + pointed bow (wedge turned so its slope faces forward-up) + rounded stern
	B:block(W, H, L * 0.7, at(0, y + H / 2, 0.35), { col = "primary", mat = "wood", pri = 1, role = "body", name = "Hull" })
	-- pointed bow: two right-triangle wedges lying on their side (triangle in the XZ plane), mirrored; each
	-- overlaps the centre line by 0.02 so their inner faces are never coincident, and is 4% shorter than the hull
	local bowLen = L * 0.34
	local hullFront = 0.35 - L * 0.35
	B:mwedge(H * 0.96, W * 0.5, bowLen, at(W * 0.25 - 0.02, y + H / 2, hullFront - bowLen / 2 + 0.06, 0, 0, rad(-90)), { col = "primary", mat = "wood", pri = 1.1, role = "body", name = "Bow#" })
	if detail >= 1 then
		B:block(W + 0.06, 0.16, L * 0.66, at(0, y + H - 0.12, 0.35), { col = "secondary", mat = "wood", pri = 1.6, role = "detail", name = "Gunwale" })
	end
	-- mast + sail
	B:bone("Mast", "Body", 0, y + H, -0.1)
	B:addRig("sway", "Mast")
	B:cyl(3.4, 0.18, at(0, y + H + 1.6, -0.1, 0, 0, rad(90)), { col = "darkWood", mat = "wood", bone = "Mast", pri = 1.2, role = "mast", name = "Mast" })
	B:wedge(0.08, 2.9, 2.2, at(0, y + H + 1.7, 0.95, 0, 0, 0), { col = "sail", mat = "cloth", bone = "Mast", pri = 1.3, role = "sail", name = "Sail", trail = true })
	if detail >= 2 then
		B:wedge(0.07, 1.8, 1.3, at(0, y + H + 1.2, -0.85, 0, math.pi, 0), { col = "sail", mat = "cloth", bone = "Mast", pri = 2.0, role = "sail", name = "Jib" })
		B:block(0.5, 0.3, 0.06, at(0.3, y + H + 3.2, -0.1), { col = "red", mat = "cloth", bone = "Mast", pri = 2.8, role = "flag", name = "Pennant", trail = true })
	end
	face(B, ctx, at(0, y + H * 0.5, -L * 0.15 - 0.2, 0, 0, 0), W * 0.6)
	B:socket("core", at(0, y + H, 0), "Body")
	B:setRig("gait", "float")
end

function K.sub(B: any, ctx: any)
	local detail = ctx.detail
	local y = 1.4
	B.boneIndex.Body.pos = { 0, y, 0 }
	local c, r = { 0, y, 0 }, { 1.1, 1.05, 2.4 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "metal", pri = 1, role = "body", name = "Hull" })
	B:block(0.7, 0.9, 1.3, at(0, y + 1.1, -0.2), { col = "primary", mat = "metal", pri = 1.1, role = "body", name = "Tower" })
	B:cyl(0.9, 0.12, at(0.15, y + 1.85, -0.5, 0, 0, rad(90)), { col = "dark", mat = "metal", pri = 2.0, role = "detail", name = "Periscope" })
	B:wedge(0.12, 0.9, 0.9, at(0, y + 0.5, 2.4), { col = "secondary", mat = "metal", pri = 1.5, role = "fin", name = "Rudder" })
	B:bone("Prop", "Body", 0, y, 2.6)
	B:addRig("rotors", { bone = "Prop", axis = "Z", speed = 8 })
	B:block(1.2, 0.2, 0.08, at(0, y, 2.65, 0, 0, rad(20)), { col = "gold", mat = "metal", bone = "Prop", pri = 1.8, role = "rotor", name = "Prop" })
	if detail >= 2 then
		for i = 1, 3 do
			B:mcyl(0.12, 0.55, at(r[1] * 0.93, y + 0.1, -1.2 + i * 0.8, 0, 0, 0), { col = "glass", mat = "glass", pri = 2.3 + i * 0.1, role = "window", name = "Port" .. i .. "#" })
		end
	end
	face(B, ctx, at(0, y + 0.1, -r[3] + 0.35, rad(-6), 0, 0), 1.3, { curve = 0.25 })
	B:socket("core", at(0, y, 0), "Body")
	B:setRig("gait", "swim")
end

function K.plane(B: any, ctx: any)
	local detail = ctx.detail
	local jet = ctx.traits.jet or string.find(string.lower(ctx.result.id), "jet") ~= nil
	local y = 1.6
	B.boneIndex.Body.pos = { 0, y, 0 }
	B:ell(1.1, 1.1, 5.0, at(0, y, 0), { col = "primary", mat = "metal", pri = 1, role = "body", name = "Fuselage" })
	B:ell(0.7, 0.5, 1.3, at(0, y + 0.42, -1.1), { col = "glass", mat = "glass", pri = 1.4, role = "window", name = "Canopy" })
	B:mblock(2.7, 0.14, 1.2, at(1.4, y - 0.12, -0.2, 0, rad(if jet then -24 else -4), rad(-4)), { col = "secondary", mat = "metal", pri = 1.1, role = "wing", name = "Wing#", trail = true })
	B:mblock(1.0, 0.1, 0.6, at(0.55, y + 0.05, 2.15, 0, rad(-12), 0), { col = "secondary", mat = "metal", pri = 1.6, role = "wing", name = "Stab#" })
	B:wedge(0.12, 1.1, 1.0, at(0, y + 0.6, 2.1), { col = "secondary", mat = "metal", pri = 1.3, role = "fin", name = "Fin" })
	if jet then
		B:cyl(0.5, 0.75, at(0, y, 2.45, 0, rad(90), 0), { col = "dark", mat = "metal", pri = 1.8, role = "detail", name = "Exhaust" })
		B:emit("thruster", "Exhaust", { socket = "exhaust", rate = 30 })
		B:socket("exhaust", at(0, y, 2.75), "Body")
	else
		B:bone("Prop", "Body", 0, y, -2.55)
		B:addRig("rotors", { bone = "Prop", axis = "Z", speed = 20 })
		B:ell(0.42, 0.42, 0.42, at(0, y, -2.48), { col = "red", mat = "plastic", bone = "Prop", pri = 1.7, role = "detail", name = "Spinner" })
		B:block(0.2, 2.0, 0.08, at(0, y, -2.62), { col = "dark", mat = "metal", bone = "Prop", pri = 1.5, role = "rotor", name = "Prop", trail = true })
	end
	if detail >= 2 then
		B:mrod({ 0.35, y - 0.4, -0.9 }, { 0.5, 0.42, -0.9 }, 0.1, { col = "dark", mat = "metal", pri = 2.6, role = "detail", name = "Strut#" })
		B:mcyl(0.25, 0.75, at(0.5, 0.38, -0.9), { col = "tyre", mat = "rubber", pri = 2.7, role = "wheel", name = "Gear#" })
	end
	face(B, ctx, at(0, y + 0.05, -2.35, 0, 0, 0), 0.9, { curve = 0.6, eye = 0.3 })
	B:socket("core", at(0, y, 0), "Body")
	B:setRig("gait", "fly")
end

function K.heli(B: any, ctx: any)
	local detail = ctx.detail
	local y = 1.5
	B.boneIndex.Body.pos = { 0, y, 0 }
	local c, r = { 0, y + 0.1, -0.2 }, { 1.0, 0.95, 1.4 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "metal", pri = 1, role = "body", name = "Cabin" })
	B:ell(1.6, 1.25, 1.4, at(0, y + 0.3, -0.9), { col = "glass", mat = "glass", pri = 1.3, role = "window", name = "Bubble" })
	B:limb({ 0, y + 0.3, 0.9 }, { 0, y + 0.6, 3.4 }, 0.42, { col = "primary", mat = "metal", pri = 1.1, role = "body", name = "Boom" }, 0.05)
	B:wedge(0.1, 0.9, 0.7, at(0, y + 1.0, 3.3), { col = "secondary", mat = "metal", pri = 1.6, role = "fin", name = "TailFin" })
	B:bone("Rotor", "Body", 0, y + 1.25, -0.2)
	B:addRig("rotors", { bone = "Rotor", axis = "Y", speed = 22 })
	B:cyl(0.42, 0.22, at(0, y + 1.0, -0.2, 0, 0, rad(90)), { col = "dark", mat = "metal", pri = 1.5, role = "detail", name = "Mast" })
	B:block(5.6, 0.07, 0.36, at(0, y + 1.25, -0.2), { col = "dark", mat = "metal", bone = "Rotor", pri = 1.2, role = "rotor", name = "BladeA", trail = true })
	B:block(0.34, 0.06, 5.6, at(0, y + 1.27, -0.2), { col = "dark", mat = "metal", bone = "Rotor", pri = 1.25, role = "rotor", name = "BladeB" })
	if detail >= 2 then
		B:bone("TailRotor", "Body", 0.12, y + 0.7, 3.4)
		B:addRig("rotors", { bone = "TailRotor", axis = "X", speed = 30 })
		B:block(0.06, 1.1, 0.16, at(0.16, y + 0.7, 3.4), { col = "dark", mat = "metal", bone = "TailRotor", pri = 2.3, role = "rotor", name = "TailBlade" })
		B:mcyl(2.6, 0.16, at(0.75, 0.12, -0.2, 0, rad(90), 0), { col = "dark", mat = "metal", pri = 2.0, role = "detail", name = "Skid#" })
		B:mrod({ 0.55, y - 0.6, -0.8 }, { 0.75, 0.15, -0.8 }, 0.1, { col = "dark", mat = "metal", pri = 2.6, role = "detail", name = "SkidStrut#" })
	end
	face(B, ctx, at(0, y + 0.3, -1.55, 0, 0, 0), 1.1, { curve = 0.3 })
	B:socket("core", at(0, y, 0), "Body")
	B:setRig("gait", "hover")
end

function K.rocket(B: any, ctx: any)
	local detail = ctx.detail
	local y = 1.0
	B.boneIndex.Body.pos = { 0, y + 2, 0 }
	B:cyl(4.2, 1.5, at(0, y + 2.1, 0, 0, 0, rad(90)), { col = "primary", mat = "metal", pri = 1, role = "body", name = "Body" })
	B:limb({ 0, y + 4.0, 0 }, { 0, y + 5.9, 0 }, 1.5, { col = "secondary", mat = "metal", pri = 1.1, role = "body", name = "Nose" }, 0.02)
	for i = 1, (if detail <= 1 then 2 else 4) do
		local a = (i - 0.5) / (if detail <= 1 then 2 else 4) * math.pi * 2
		B:wedge(0.14, 1.5, 1.1, Geom.mul(at(0, y + 0.55, 0, 0, a, 0), at(0, 0, 0.95)), { col = "secondary", mat = "metal", pri = 1.2 + i * 0.05, role = "fin", name = "Fin" .. i })
	end
	B:cyl(0.6, 1.0, at(0, y - 0.25, 0, 0, 0, rad(90)), { col = "dark", mat = "metal", pri = 1.4, role = "detail", name = "Nozzle" })
	if detail >= 2 then
		B:cyl(0.12, 0.62, at(0, y + 3.0, -0.72, 0, rad(90), 0), { col = "glass", mat = "glass", pri = 2.0, role = "window", name = "Porthole" })
	end
	B:ell(0.8, 1.8, 0.8, at(0, y - 1.3, 0), { col = "flame", mat = "neon", glow = true, pri = 1.6, role = "glow", name = "Flame", trail = true, noCore = true })
	B:socket("exhaust", at(0, y - 1.0, 0), "Body")
	B:emit("thruster", "Flame", { socket = "exhaust", rate = 40 })
	table.insert(B.lights, { kind = "PointLight", colour = { 1, 0.6, 0.2 }, brightness = 2, range = 1.2, socket = "exhaust", shadows = false })
	face(B, ctx, at(0, y + 2.6, -0.76, 0, 0, 0), 1.2, { curve = 0.5 })
	B:socket("core", at(0, y + 2, 0), "Body")
	B:setRig("gait", "hover")
end

function K.ufo(B: any, ctx: any)
	local detail = ctx.detail
	local y = 2.0
	B.boneIndex.Body.pos = { 0, y, 0 }
	B:ell(5.0, 0.9, 5.0, at(0, y, 0), { col = "primary", mat = "metal", pri = 1, role = "body", name = "Disc" })
	B:ell(3.0, 0.55, 3.0, at(0, y - 0.35, 0), { col = "dark", mat = "metal", pri = 1.3, role = "body", name = "Belly" })
	B:ell(2.2, 1.7, 2.2, at(0, y + 0.45, 0), { col = "glass", mat = "glass", tr = 0.35, pri = 1.1, role = "window", name = "Dome" })
	B:bone("Ring", "Body", 0, y, 0)
	B:addRig("rotors", { bone = "Ring", axis = "Y", speed = 2 })
	local n = if detail <= 1 then 4 else 8
	for i = 1, n do
		local a = (i - 0.5) / n * math.pi * 2
		B:ball(0.36, at(sin(a) * 2.35, y - 0.05, cos(a) * 2.35), { col = "secondary", mat = "neon", glow = true, bone = "Ring", pri = 1.6 + i * 0.02, role = "light", name = "Light" .. i })
	end
	if detail >= 2 then
		B:ell(1.0, 1.0, 1.0, at(0, y + 0.55, 0), { col = "secondary", mat = "skin", pri = 2.2, role = "detail", name = "Pilot" })
	end
	B:socket("muzzle", at(0, y - 0.6, 0), "Body")
	face(B, ctx, at(0, y + 0.1, -2.2, rad(-6), 0, 0), 1.6, { curve = 0.25 })
	B:socket("core", at(0, y, 0), "Body")
	B:setRig("gait", "hover")
end

function K.train(B: any, ctx: any)
	local detail = ctx.detail
	local y = 0.9
	B.boneIndex.Body.pos = { 0, y + 0.8, 0 }
	B:block(2.0, 0.5, 5.2, at(0, y + 0.25, 0.2), { col = "dark", mat = "metal", pri = 1.05, role = "body", name = "Frame" })
	B:cyl(3.0, 1.7, at(0, y + 1.3, -0.8, 0, rad(90), 0), { col = "primary", mat = "metal", pri = 1, role = "body", name = "Boiler" })
	B:block(2.1, 2.2, 1.7, at(0, y + 1.55, 1.75), { col = "primary", mat = "metal", pri = 1.1, role = "body", name = "Cab" })
	B:block(2.3, 0.18, 2.0, at(0, y + 2.72, 1.75), { col = "secondary", mat = "metal", pri = 1.5, role = "body", name = "Roof" })
	B:cyl(1.1, 0.6, at(0, y + 2.6, -1.6, 0, 0, rad(90)), { col = "dark", mat = "metal", pri = 1.3, role = "detail", name = "Funnel" })
	B:wedge(1.9, 0.8, 0.7, at(0, y + 0.1, -2.75, 0, math.pi, 0), { col = "secondary", mat = "metal", pri = 1.6, role = "detail", name = "Cowcatcher" })
	if detail >= 1 then
		B:mblock(0.06, 0.8, 0.9, at(1.07, y + 1.9, 1.75), { col = "glass", mat = "glass", pri = 2.1, role = "window", name = "CabWindow#" })
	end
	for i = 1, (if detail >= 2 then 3 else 2) do
		Parts.wheelPair(B, { index = i, x = 0.95, z = -1.8 + (i - 1) * 1.5, r = 0.55, w = 0.3, spokes = detail >= 3 })
	end
	B:socket("smoke", at(0, y + 3.2, -1.6), "Body")
	B:emit("smoke", nil, { socket = "smoke", rate = 12 })
	face(B, ctx, at(0, y + 1.3, -2.31, 0, 0, 0), 1.3, { curve = 0.3 })
	B:socket("core", at(0, y + 1.3, 0), "Body")
	B:setRig("gait", "drive")
end

function K.bike(B: any, ctx: any)
	local detail = ctx.detail
	local r = 0.9
	B.boneIndex.Body.pos = { 0, r + 0.6, 0 }
	for i, z in { -1.3, 1.3 } do
		local bn = B:bone("Wheel" .. i, "Body", 0, r, z)
		B:addRig("wheels", { bone = bn, r = r })
		B:cyl(0.16, r * 2, at(0, r, z), { col = "tyre", mat = "rubber", bone = bn, pri = 1, role = "wheel", name = "Tyre" .. i })
		B:cyl(0.2, r * 0.5, at(0, r, z), { col = "metal", mat = "metal", bone = bn, pri = 2.2, role = "wheel", name = "Hub" .. i })
	end
	B:rod({ 0, r, 1.3 }, { 0, r + 0.9, 0.2 }, 0.14, { col = "primary", mat = "metal", pri = 1.1, role = "body", name = "SeatTube" })
	B:rod({ 0, r + 0.9, 0.2 }, { 0, r + 1.0, -1.0 }, 0.14, { col = "primary", mat = "metal", pri = 1.15, role = "body", name = "TopTube" })
	B:rod({ 0, r + 1.0, -1.0 }, { 0, r, -1.3 }, 0.14, { col = "primary", mat = "metal", pri = 1.2, role = "body", name = "Fork" })
	B:rod({ 0, r, 1.3 }, { 0, r + 0.12, 0.05 }, 0.12, { col = "primary", mat = "metal", pri = 1.4, role = "body", name = "Chain" })
	B:ell(0.4, 0.18, 0.75, at(0, r + 1.05, 0.3), { col = "dark", mat = "plastic", pri = 1.3, role = "detail", name = "Seat" })
	B:cyl(1.0, 0.12, at(0, r + 1.35, -1.05), { col = "dark", mat = "metal", pri = 1.5, role = "detail", name = "Handlebar" })
	if detail >= 2 then
		B:rod({ 0, r + 1.0, -1.0 }, { 0, r + 1.35, -1.05 }, 0.1, { col = "metal", mat = "metal", pri = 2.0, role = "detail", name = "Stem" })
	end
	face(B, ctx, at(0, r + 1.25, -1.2, 0, 0, 0), 0.7)
	B:socket("core", at(0, r + 0.6, 0), "Body")
	B:setRig("gait", "drive")
end

function K.balloon(B: any, ctx: any)
	local detail = ctx.detail
	local blimp = string.find(string.lower(ctx.result.id), "blimp") or string.find(string.lower(ctx.result.id), "zeppelin") or string.find(string.lower(ctx.result.id), "airship")
	local y = 4.0
	B.boneIndex.Body.pos = { 0, y, 0 }
	local c, r
	if blimp then
		c, r = { 0, y, 0 }, { 1.4, 1.4, 3.2 }
	else
		c, r = { 0, y + 0.5, 0 }, { 1.8, 2.1, 1.8 }
	end
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "cloth", pri = 1, role = "body", name = "Envelope" })
	if detail >= 2 and not blimp then
		for i = 1, 3 do
			B:ell(r[1] * 2.03, r[2] * 2.03, 0.35, at(c[1], c[2], c[3], 0, rad(i * 60), 0), { col = "secondary", mat = "cloth", pri = 2.0 + i * 0.1, role = "detail", name = "Stripe" .. i })
		end
	end
	local by = y - (if blimp then 1.6 else 2.4)
	B:block(1.1, 0.8, 1.1, at(0, by, 0), { col = "wood", mat = "wood", pri = 1.1, role = "body", name = "Basket" })
	if detail >= 1 then
		for _, s in { { 1, 1 }, { -1, -1 } } do
			B:rod({ s[1] * 0.45, by + 0.35, s[2] * 0.45 }, { s[1] * 0.75, c[2] - r[2] * 0.75, s[2] * 0.75 }, 0.05, { col = "darkWood", mat = "wood", pri = 2.4, role = "detail" })
		end
	end
	if blimp then
		B:mwedge(0.1, 0.9, 0.9, at(0.45, y + 0.4, 3.0, 0, 0, rad(-50)), { col = "secondary", mat = "cloth", pri = 1.6, role = "fin" })
	end
	if Heads.wantsFace(B, ctx.traits) then
		local Face = require(script.Parent.Parent.Face)
		Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = "Body", mood = ctx.result.mood, detail = math.max(1, detail), kind = "cute", spacing = r[1] * 0.35, y = r[2] * 0.1, d = r[1] * 0.4, mouthY = -r[2] * 0.3, mouthW = r[1] * 0.6, forceMouth = true })
	end
	B:socket("core", at(0, y, 0), "Body")
	B:setRig("gait", "float")
end

function K.sled(B: any, ctx: any)
	B.boneIndex.Body.pos = { 0, 0.7, 0 }
	B:block(1.6, 0.2, 2.8, at(0, 0.75, 0.1), { col = "primary", mat = "wood", pri = 1, role = "body", name = "Deck" })
	B:mcyl(3.2, 0.14, at(0.75, 0.1, 0, 0, rad(90), 0), { col = "secondary", mat = "metal", pri = 1.1, role = "body", name = "Runner#" })
	B:mlimb({ 0.75, 0.1, -1.55 }, { 0.75, 0.6, -1.85 }, 0.15, { col = "secondary", mat = "metal", pri = 1.3, role = "body", name = "Curl#" }, 0.1)
	B:mrod({ 0.6, 0.15, -0.8 }, { 0.6, 0.7, -0.8 }, 0.1, { col = "dark", mat = "wood", pri = 1.8, role = "detail" })
	B:mrod({ 0.6, 0.15, 0.9 }, { 0.6, 0.7, 0.9 }, 0.1, { col = "dark", mat = "wood", pri = 1.9, role = "detail" })
	face(B, ctx, at(0, 0.75, -1.25, rad(-80), 0, 0), 1.0)
	B:socket("core", at(0, 0.8, 0), "Body")
	B:setRig("gait", "drive")
end

function K.cart(B: any, ctx: any)
	local detail = ctx.detail
	B.boneIndex.Body.pos = { 0, 1.2, 0 }
	B:block(2.0, 1.0, 2.6, at(0, 1.3, 0), { col = "primary", mat = "wood", pri = 1, role = "body", name = "Box" })
	B:block(2.06, 0.18, 2.66, at(0, 1.85, 0), { col = "secondary", mat = "wood", pri = 1.5, role = "body", name = "Rim" })
	Parts.wheelPair(B, { index = 1, x = 1.08, z = 0.4, r = 0.75, w = 0.2, spokes = detail >= 3 })
	B:mrod({ 0.5, 1.1, -1.25 }, { 0.6, 0.9, -2.6 }, 0.12, { col = "darkWood", mat = "wood", pri = 1.7, role = "detail", name = "Shaft#" })
	face(B, ctx, at(0, 1.3, -1.31), 1.6)
	B:socket("core", at(0, 1.3, 0), "Body")
	B:setRig("gait", "drive")
end

function K.board(B: any, ctx: any)
	B.boneIndex.Body.pos = { 0, 0.5, 0 }
	B:ell(1.0, 0.18, 3.6, at(0, 0.55, 0), { col = "primary", mat = "plastic", pri = 1, role = "body", name = "Deck" })
	for i, z in { -1.1, 1.1 } do
		Parts.wheelPair(B, { index = i, x = 0.33, z = z, r = 0.22, w = 0.18 })
	end
	face(B, ctx, at(0, 0.66, 0, rad(-90), 0, 0), 0.8)
	B:socket("core", at(0, 0.6, 0), "Body")
	B:setRig("gait", "drive")
end

return function(B: any, ctx: any)
	local kind = kindOf(ctx)
	local _ = sin(0) + cos(0)
	if kind == "truck" then
		return K.car(B, ctx, true)
	end
	local f = (K :: any)[kind] or K.car
	return f(B, ctx, false)
end
