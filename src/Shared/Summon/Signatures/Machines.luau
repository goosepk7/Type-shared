--!strict
-- Hand-built machine and building signatures: pirate ship, tank, castle, rocket, ufo, cannon.

local Kit = require(script.Parent.Parent.SigKit)

local at, rad = Kit.at, Kit.rad
local sin, cos = math.sin, math.cos

local S = {}

local function hullBounds(B: any, name: string): ({ number }?, { number }?, any)
	local p = Kit.find(B, name)
	if p == nil then
		return nil, nil, nil
	end
	local s = p.size
	return { p.cf[1] - s[1] / 2, p.cf[2] - s[2] / 2, p.cf[3] - s[3] / 2 }, { p.cf[1] + s[1] / 2, p.cf[2] + s[2] / 2, p.cf[3] + s[3] / 2 }, p
end

S["pirate ship"] = {
	plan = "Vehicle|Boat",
	build = function(B: any, ctx: any)
		Kit.base(B, ctx, "Vehicle", "Boat", { ship = true, sail = true, pirate = true })
		local mn, mx, hull = hullBounds(B, "Hull")
		if mn == nil or mx == nil then
			return
		end
		local w, h, l = mx[1] - mn[1], mx[2] - mn[2], mx[3] - mn[3]
		-- gun deck: cannons poking out of both sides
		local n = if ctx.detail >= 3 then 3 elseif ctx.detail >= 1 then 2 else 1
		for i = 1, n do
			local z = mn[3] + l * (0.3 + (i - 1) * 0.4 / math.max(1, n - 1))
			B:mcyl(w * 0.3, h * 0.2, at(mx[1] + w * 0.05, mn[2] + h * 0.62, z), { col = "black", mat = "metal", bone = hull.bone, pri = 1.5 + i * 0.05, role = "cannon", name = "GunPort" .. i .. "#", noCore = true })
		end
		-- stern castle
		B:block(w * 0.9, h * 0.7, l * 0.22, at(0, mx[2] + h * 0.3, mx[3] - l * 0.1), { col = "darkWood", mat = "wood", bone = hull.bone, pri = 1.35, role = "body", name = "SternCastle" })
		-- jolly roger at the masthead
		local mast = Kit.find(B, "Mast")
		if mast then
			local top = mast.cf[2] + mast.size[1] / 2
			B:block(w * 0.04, h * 0.5, h * 0.75, at(0, top - h * 0.3, mast.cf[3] + h * 0.42), { col = "black", mat = "cloth", bone = mast.bone, pri = 1.6, role = "flag", name = "JollyRoger" })
			if ctx.detail >= 2 then
				B:ball(h * 0.2, at(w * 0.035, top - h * 0.28, mast.cf[3] + h * 0.42), { col = "white", mat = "hard", bone = mast.bone, pri = 2.4, role = "detail", name = "Skull", needs = "JollyRoger", noCore = true })
				-- crow's nest
				B:cyl(h * 0.3, h * 0.6, at(0, top - h * 1.15, mast.cf[3], 0, 0, rad(90)), { col = "wood", mat = "wood", bone = mast.bone, pri = 2.5, role = "detail", name = "CrowsNest" })
			end
		end
		B:socket("muzzle", at(mx[1] + w * 0.25, mn[2] + h * 0.62, (mn[3] + mx[3]) / 2), hull.bone)
	end,
}

S.tank = {
	plan = "Vehicle|Tracked",
	build = function(B: any, ctx: any)
		Kit.base(B, ctx, "Vehicle", "Tracked", { tank = true, treads = true })
		local turret = Kit.find(B, "Turret")
		local mn, mx, hull = hullBounds(B, "Hull")
		if turret and hull and mn and mx then
			local s = turret.size
			-- commander hatch, whip antenna, side skirts and an emblem
			B:cyl(s[2] * 0.14, s[1] * 0.34, at(turret.cf[1] + s[1] * 0.12, turret.cf[2] + s[2] * 0.47, turret.cf[3] + s[3] * 0.12, 0, 0, rad(90)), { col = "dark", mat = "metal", bone = turret.bone, pri = 1.6, role = "detail", name = "Hatch", noCore = true })
			B:rod({ turret.cf[1] - s[1] * 0.3, turret.cf[2] + s[2] * 0.3, turret.cf[3] + s[3] * 0.32 }, { turret.cf[1] - s[1] * 0.36, turret.cf[2] + s[2] * 2.1, turret.cf[3] + s[3] * 0.5 }, s[2] * 0.05,
				{ col = "dark", mat = "metal", bone = turret.bone, pri = 2.2, role = "antenna", name = "Whip", noCore = true })
			local w, h, l = mx[1] - mn[1], mx[2] - mn[2], mx[3] - mn[3]
			if ctx.detail >= 2 then
				B:mblock(w * 0.06, h * 0.55, l * 0.84, at(mx[1] + w * 0.13, mn[2] + h * 0.42, (mn[3] + mx[3]) / 2, 0, 0, rad(4)), { col = "secondary", mat = "metal", bone = hull.bone, pri = 2.3, role = "detail", name = "Skirt#" })
			end
			B:ell(s[1] * 0.22, s[2] * 0.3, s[1] * 0.22, at(turret.cf[1] + s[1] * 0.5, turret.cf[2], turret.cf[3] + s[3] * 0.05, 0, 0, rad(90)), { col = "white", mat = "hard", bone = turret.bone, pri = 1.9, role = "detail", name = "Emblem", noCore = true })
		end
		B:setRig("materialMotion", "clank")
	end,
}

S.castle = {
	plan = "Structure|Castle",
	build = function(B: any, ctx: any)
		Kit.base(B, ctx, "Structure", "Castle", { castle = true })
		-- banners on every roof spire
		local roofs = Kit.findRole(B, "roof")
		table.sort(roofs, function(a, b)
			return a.id < b.id
		end)
		local n = 0
		for _, r in roofs do
			if n >= (if ctx.detail >= 2 then 4 else 2) then
				break
			end
			n += 1
			local top = r.cf[2] + r.size[2] / 2
			local d = math.min(r.size[1], r.size[3])
			B:rod({ r.cf[1], top - d * 0.15, r.cf[3] }, { r.cf[1], top + d * 0.85, r.cf[3] }, d * 0.06, { col = "darkWood", mat = "wood", bone = r.bone, pri = 1.6 + n * 0.05, role = "flag", name = "Pole" .. n, noCore = true })
			B:block(d * 0.04, d * 0.34, d * 0.6, at(r.cf[1], top + d * 0.66, r.cf[3] + d * 0.31), { col = "secondary", mat = "cloth", bone = r.bone, pri = 1.7 + n * 0.05, role = "flag", name = "Banner" .. n, needs = "Pole" .. n, trail = n == 1 })
		end
		B:setRig("flags", true)
	end,
}

S.rocket = {
	plan = "Vehicle|Rocket",
	build = function(B: any, ctx: any)
		Kit.base(B, ctx, "Vehicle", "Rocket", { rocket = true, space = true })
		local A = Kit.anchors(B)
		local body = A.body
		if body then
			local s = body.size
			local r = math.min(s[1], s[3]) / 2
			-- porthole and racing stripes
			B:cyl(r * 0.2, r * 0.7, at(body.cf[1], body.cf[2] + s[2] * 0.12, body.cf[3] - r * 0.92, 0, rad(90), 0), { col = "glass", mat = "glass", bone = body.bone, pri = 1.5, role = "window", name = "Porthole", noCore = true })
			if ctx.detail >= 2 then
				B:cyl(r * 0.12, r * 0.5, at(body.cf[1], body.cf[2] + s[2] * 0.12, body.cf[3] - r * 0.96, 0, rad(90), 0), { col = "glow", mat = "neon", glow = true, bone = body.bone, pri = 2.6, role = "window", name = "PortholeGlow", noCore = true, needs = "Porthole" })
			end
			B:cyl(s[2] * 0.08, r * 2.06, at(body.cf[1], body.cf[2] - s[2] * 0.12, body.cf[3], 0, 0, rad(90)), { col = "secondary", mat = "metal", bone = body.bone, pri = 1.7, role = "detail", name = "Stripe" })
		end
		B:emit("flame", nil, { socket = "exhaust", rate = 40, spread = 0.2 })
	end,
}

S.ufo = {
	plan = "Vehicle|Aircraft",
	build = function(B: any, ctx: any)
		Kit.base(B, ctx, "Vehicle", nil, { ufo = true, hover = true })
		local A = Kit.anchors(B)
		local body = A.body
		local dome = Kit.find(B, "Dome")
		if body then
			local s = body.size
			local R = s[1] / 2
			-- rim lights
			local n = if ctx.detail >= 2 then 6 else 3
			for i = 1, n do
				local a = (i - 0.5) / n * math.pi * 2
				B:ball(R * 0.16, at(body.cf[1] + sin(a) * R * 0.93, body.cf[2] - s[2] * 0.02, body.cf[3] + cos(a) * R * 0.93), { col = if i % 2 == 0 then "glow" else "gold", mat = "neon", glow = true, bone = body.bone, pri = 1.6 + i * 0.03, role = "light", name = "RimLight" .. i, noCore = true })
			end
			-- tractor beam
			B:ell(R * 0.62, s[2] * 2.2, R * 0.62, at(body.cf[1], body.cf[2] - s[2] * 1.45, body.cf[3]), { col = "glow", mat = "neon", glow = true, tr = 0.72, bone = body.bone, pri = 2.0, role = "glow", name = "TractorBeam", noCore = true })
		end
		if dome then
			-- little alien pilot
			local d = dome.size[1]
			B:ell(d * 0.32, d * 0.36, d * 0.32, at(dome.cf[1], dome.cf[2] - d * 0.02, dome.cf[3]), { col = "leaf", mat = "skin", bone = dome.bone, pri = 1.5, role = "head", name = "Alien" })
			B:mell(d * 0.08, d * 0.12, d * 0.05, at(d * 0.07, dome.cf[2] + d * 0.03, dome.cf[3] - d * 0.155), { col = "black", mat = "glass", bone = dome.bone, pri = 1.55, role = "eye", name = "AlienEye#", noCore = true })
		end
		B:setRig("gait", "hover")
	end,
}

S.cannon = {
	plan = "Weapon|Cannon",
	build = function(B: any, ctx: any)
		Kit.base(B, ctx, "Weapon", "Cannon", { cannon = true })
		local barrel = Kit.find(B, "Barrel")
		if barrel then
			local d = barrel.size[2]
			local gx, gz = barrel.cf[1] + d * 1.3, barrel.cf[3] + d * 0.9
			-- pyramid of cannonballs beside the carriage
			local n = if ctx.detail >= 2 then 3 else 1
			for i = 1, n do
				local y = d * 0.36 + (if i == 3 then d * 0.6 else 0)
				local x = gx + (if i == 2 then d * 0.74 elseif i == 3 then d * 0.37 else 0)
				B:ball(d * 0.72, at(x, y, gz), { col = "black", mat = "metal", pri = 1.8 + i * 0.1, role = "detail", name = "Ball" .. i })
			end
			-- lit fuse
			local breech = Kit.find(B, "Breech")
			if breech then
				local b = breech.cf
				B:rod({ b[1], b[2] + breech.size[2] * 0.45, b[3] }, { b[1], b[2] + breech.size[2] * 0.75, b[3] + breech.size[2] * 0.12 }, d * 0.06, { col = "darkWood", mat = "cloth", bone = breech.bone, pri = 1.9, role = "detail", name = "Fuse", noCore = true })
				B:ball(d * 0.12, at(b[1], b[2] + breech.size[2] * 0.78, b[3] + breech.size[2] * 0.13), { col = "flame", mat = "neon", glow = true, bone = breech.bone, pri = 2.0, role = "glow", name = "FuseSpark", noCore = true, needs = "Fuse" })
				B:emit("sparks", "FuseSpark", { rate = 16 })
			end
		end
	end,
}

return S
