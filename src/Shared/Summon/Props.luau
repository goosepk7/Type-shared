--!strict
-- Props: hats, held items and accessories shared by Humanoid/Biped plans, signatures and accents.
-- Each takes a model-space anchor and a scale `s` (head size for hats, hand scale for held items).

local Geom = require(script.Parent.Geom)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local Props = {}

-- HATS: anchor = top of head {x,y,z}; s = head size; bone
function Props.hat(B: any, kind: string, top: { number }, s: number, bone: string, o: any?)
	local oo = o or {}
	local x, y, z = top[1], top[2], top[3]
	local col = oo.col or "secondary"
	local detail = B.ctx.detail or 2
	if kind == "wizard" then
		-- brim + three tapering stacked cylinders + a bent tip: reads as a soft pointed hat
		B:cyl(s * 0.12, s * 1.55, at(x, y - s * 0.12, z, 0, 0, rad(90)), { col = col, mat = "cloth", bone = bone, pri = 1.3, role = "hat", name = "HatBrim" })
		B:cyl(s * 0.5, s * 0.9, at(x, y + s * 0.15, z + s * 0.02, rad(-4), 0, rad(90)), { col = col, mat = "cloth", bone = bone, pri = 1.35, role = "hat", name = "HatBase" })
		B:limb({ x, y + s * 0.35, z + s * 0.04 }, { x, y + s * 1.0, z + s * 0.18 }, s * 0.62, { col = col, mat = "cloth", bone = bone, pri = 1.4, role = "hat", name = "HatMid" }, 0.2)
		B:limb({ x, y + s * 0.95, z + s * 0.17 }, { x + s * 0.05, y + s * 1.35, z + s * 0.5 }, s * 0.3, { col = col, mat = "cloth", bone = bone, pri = 1.6, role = "hat", name = "HatTip", trail = true }, 0.25)
		if detail >= 2 then
			B:cyl(s * 0.14, s * 0.93, at(x, y + s * 0.04, z + s * 0.02, rad(-4), 0, rad(90)), { col = oo.band or "gold", mat = "cloth", bone = bone, pri = 2.6, role = "hat", name = "HatBand" })
		end
		if detail >= 3 then
			B:ell(s * 0.2, s * 0.2, s * 0.08, at(x, y + s * 0.55, z - s * 0.27, rad(-12), 0, rad(45)), { col = "gold", mat = "neon", glow = true, bone = bone, pri = 3.4, role = "gem", name = "HatStar" })
		end
	elseif kind == "crown" then
		B:cyl(s * 0.3, s * 0.82, at(x, y + s * 0.02, z, 0, 0, rad(90)), { col = "gold", mat = "metal", bone = bone, pri = 1.3, role = "hat", name = "Crown" })
		local n = if detail >= 2 then 5 else 3
		for i = 1, n do
			local a = (i - 1) / n * math.pi * 2
			B:wedge(s * 0.08, s * 0.32, s * 0.18, at(x + sin(a) * s * 0.38, y + s * 0.3, z + cos(a) * s * 0.38, 0, a + math.pi, 0), { col = "gold", mat = "metal", bone = bone, pri = 2 + i * 0.1, role = "hat" })
		end
		if detail >= 3 then
			B:ball(s * 0.14, at(x, y + s * 0.1, z - s * 0.42), { col = "red", mat = "neon", glow = true, bone = bone, pri = 3.5, role = "gem" })
		end
	elseif kind == "helmet" then
		B:ell(s * 1.08, s * 0.85, s * 1.08, at(x, y - s * 0.25, z + s * 0.02), { col = oo.col or "metal", mat = "metal", bone = bone, pri = 1.2, role = "hat", name = "Helmet" })
		if detail >= 2 then
			-- visor slit band and crest/plume
			B:block(s * 0.86, s * 0.12, s * 0.2, at(x, y - s * 0.42, z - s * 0.47, rad(-4), 0, 0), { col = "darker", mat = "metal", bone = bone, pri = 2.2, role = "hat", name = "Visor" })
			B:limb({ x, y + s * 0.1, z + s * 0.25 }, { x, y + s * 0.45, z + s * 0.75 }, s * 0.2, { col = oo.plume or "red", mat = "cloth", bone = bone, pri = 2.5, role = "hat", name = "Plume", depth = s * 0.45, trail = true }, 0.3)
		end
	elseif kind == "horned" then
		B:ell(s * 1.06, s * 0.75, s * 1.06, at(x, y - s * 0.22, z + s * 0.02), { col = "metal", mat = "metal", bone = bone, pri = 1.2, role = "hat", name = "Helmet" })
		B:mlimb({ s * 0.4, y - s * 0.15, z }, { s * 0.75, y + s * 0.35, z - s * 0.1 }, s * 0.18, { col = "horn", mat = "hard", bone = bone, pri = 1.6, role = "horn", trail = true }, 0.15)
	elseif kind == "chef" then
		B:cyl(s * 0.42, s * 0.8, at(x, y + s * 0.1, z, 0, 0, rad(90)), { col = "white", mat = "cloth", bone = bone, pri = 1.3, role = "hat", name = "ChefBand" })
		B:ell(s * 1.05, s * 0.75, s * 1.0, at(x, y + s * 0.55, z), { col = "white", mat = "cloth", bone = bone, pri = 1.35, role = "hat", name = "ChefPuff" })
	elseif kind == "top" then
		B:cyl(s * 0.06, s * 1.3, at(x, y - s * 0.05, z, 0, 0, rad(90)), { col = "black", mat = "cloth", bone = bone, pri = 1.3, role = "hat", name = "TopBrim" })
		B:cyl(s * 0.7, s * 0.72, at(x, y + s * 0.32, z, 0, 0, rad(90)), { col = "black", mat = "cloth", bone = bone, pri = 1.35, role = "hat", name = "TopCrown" })
		if detail >= 2 then
			B:cyl(s * 0.14, s * 0.75, at(x, y + s * 0.07, z, 0, 0, rad(90)), { col = "red", mat = "cloth", bone = bone, pri = 2.6, role = "hat", name = "TopBand" })
		end
	elseif kind == "pirate" then
		B:ell(s * 1.5, s * 0.22, s * 0.95, at(x, y - s * 0.02, z), { col = "black", mat = "cloth", bone = bone, pri = 1.3, role = "hat", name = "PirateBrim" })
		B:ell(s * 0.95, s * 0.55, s * 0.8, at(x, y + s * 0.15, z + s * 0.03), { col = "black", mat = "cloth", bone = bone, pri = 1.35, role = "hat", name = "PirateCrown" })
		if detail >= 3 then
			B:ell(s * 0.24, s * 0.22, s * 0.08, at(x, y + s * 0.18, z - s * 0.41), { col = "white", mat = "skin", bone = bone, pri = 3.6, role = "hat", name = "Skull" })
		end
	elseif kind == "cowboy" then
		B:ell(s * 1.7, s * 0.14, s * 1.5, at(x, y - s * 0.05, z), { col = "wood", mat = "cloth", bone = bone, pri = 1.3, role = "hat", name = "CowboyBrim" })
		B:ell(s * 0.85, s * 0.6, s * 0.8, at(x, y + s * 0.18, z), { col = "wood", mat = "cloth", bone = bone, pri = 1.35, role = "hat", name = "CowboyCrown" })
	elseif kind == "party" then
		B:limb({ x, y - s * 0.05, z }, { x + s * 0.05, y + s * 0.85, z }, s * 0.55, { col = "red", mat = "plastic", bone = bone, pri = 1.4, role = "hat", name = "PartyHat" }, 0.05)
		B:ball(s * 0.2, at(x + s * 0.06, y + s * 0.9, z), { col = "gold", mat = "plastic", bone = bone, pri = 2.2, role = "hat", name = "Pompom" })
	elseif kind == "hood" or kind == "ninja" then
		-- hood sits back on the skull so the eye band stays visible; ninjas add a lower face mask
		B:ell(s * 1.08, s * 1.06, s * 1.0, at(x, y - s * 0.42, z + s * 0.16), { col = oo.col or "dark", mat = "cloth", bone = bone, pri = 1.25, role = "hat", name = "Hood" })
		if kind == "ninja" then
			B:ell(s * 0.98, s * 0.5, s * 0.96, at(x, y - s * 0.86, z - s * 0.04), { col = oo.col or "dark", mat = "cloth", bone = bone, pri = 1.3, role = "hat", name = "Mask" })
		end
		if kind == "ninja" and detail >= 2 then
			B:cyl(s * 0.16, s * 1.1, at(x, y - s * 0.28, z + s * 0.02, 0, 0, rad(90)), { col = "red", mat = "cloth", bone = bone, pri = 2.2, role = "hat", name = "Headband" })
		end
	elseif kind == "halo" then
		B:cyl(s * 0.06, s * 0.9, at(x, y + s * 0.35, z, 0, 0, rad(90)), { col = "gold", mat = "neon", glow = true, bone = bone, pri = 2.0, role = "halo", name = "Halo" })
	elseif kind == "astronaut" then
		B:ball(s * 1.36, at(x, y - s * 0.48, z), { col = "glass", mat = "glass", tr = 0.55, bone = bone, pri = 1.25, role = "hat", name = "Bubble", noCore = true })
	elseif kind == "hair" then
		B:ell(s * 1.0, s * 0.62, s * 0.98, at(x, y - s * 0.12, z + s * 0.08, rad(10), 0, 0), { col = oo.col or "hair", mat = "fur", bone = bone, pri = 1.3, role = "hair", name = "Hair" })
	end
end

-- HELD ITEMS: grip at `g` (hand centre), item points up (+Y) and slightly forward. s = hand scale (~arm width).
function Props.held(B: any, kind: string, g: { number }, s: number, bone: string, o: any?)
	local oo = o or {}
	local x, y, z = g[1], g[2], g[3]
	local detail = B.ctx.detail or 2
	if kind == "staff" then
		B:cyl(s * 9, s * 0.36, at(x, y + s * 1.6, z, 0, 0, rad(90)), { col = "wood", mat = "wood", bone = bone, pri = 1.5, role = "held", name = "Staff" })
		B:ell(s * 1.0, s * 1.3, s * 1.0, at(x, y + s * 6.4, z), { col = oo.gem or "gem", mat = "neon", glow = true, bone = bone, pri = 1.7, role = "gem", name = "StaffGem", trail = true, noCore = true })
		if detail >= 2 then
			B:mlimb({ x + s * 0.12, y + s * 5.7, z }, { x + s * 0.6, y + s * 6.9, z }, s * 0.22, { col = "wood", mat = "wood", bone = bone, pri = 2.6, role = "held", name = "StaffClaw" }, 0.1)
		end
		B:socket("muzzle", at(x, y + s * 6.4, z), bone)
	elseif kind == "wand" then
		B:cyl(s * 3.2, s * 0.24, at(x, y + s * 0.6, z - s * 0.4, rad(25), 0, rad(90)), { col = "darkWood", mat = "wood", bone = bone, pri = 1.6, role = "held", name = "Wand" })
		B:ball(s * 0.55, at(x, y + s * 2.0, z - s * 1.05), { col = "gem", mat = "neon", glow = true, bone = bone, pri = 1.9, role = "gem", name = "WandTip", trail = true, noCore = true })
		B:socket("muzzle", at(x, y + s * 2.0, z - s * 1.05), bone)
	elseif kind == "sword" then
		B:block(s * 0.38, s * 1.3, s * 0.38, at(x, y, z), { col = "darkWood", mat = "wood", bone = bone, pri = 1.7, role = "held", name = "Grip" })
		B:block(s * 1.7, s * 0.3, s * 0.45, at(x, y + s * 0.75, z), { col = "gold", mat = "metal", bone = bone, pri = 1.75, role = "held", name = "Guard" })
		B:block(s * 0.62, s * 4.2, s * 0.16, at(x, y + s * 2.95, z), { col = "steel", mat = "metal", bone = bone, pri = 1.5, role = "held", name = "Blade", trail = true })
		if detail >= 2 then
			B:wedge(s * 0.16, s * 0.62, s * 0.62, at(x, y + s * 5.3, z, 0, 0, rad(90)) :: any, { col = "steel", mat = "metal", bone = bone, pri = 2.2, role = "held", name = "BladeTip" })
		end
	elseif kind == "axe" then
		B:cyl(s * 5, s * 0.34, at(x, y + s * 1.2, z, 0, 0, rad(90)), { col = "wood", mat = "wood", bone = bone, pri = 1.5, role = "held", name = "Haft" })
		B:ell(s * 0.32, s * 1.9, s * 1.6, at(x, y + s * 3.1, z - s * 0.7), { col = "steel", mat = "metal", bone = bone, pri = 1.55, role = "held", name = "AxeHead", trail = true })
	elseif kind == "shield" then
		B:cyl(s * 0.32, s * 3.4, at(x - s * 0.35, y, z - s * 0.2, 0, rad(10), 0), { col = oo.col or "secondary", mat = "metal", bone = bone, pri = 1.5, role = "held", name = "Shield" })
		if detail >= 2 then
			B:cyl(s * 0.36, s * 1.0, at(x - s * 0.5, y, z - s * 0.21, 0, rad(10), 0), { col = "gold", mat = "metal", bone = bone, pri = 2.4, role = "held", name = "Boss" })
		end
	elseif kind == "spoon" then
		B:cyl(s * 3.5, s * 0.26, at(x, y + s * 0.8, z, 0, 0, rad(90)), { col = "wood", mat = "wood", bone = bone, pri = 1.7, role = "held", name = "Spoon" })
		B:ell(s * 0.8, s * 1.1, s * 0.3, at(x, y + s * 2.7, z), { col = "wood", mat = "wood", bone = bone, pri = 1.9, role = "held", name = "SpoonBowl" })
	elseif kind == "club" then
		B:limb({ x, y - s * 0.4, z }, { x, y + s * 3.8, z - s * 0.3 }, s * 0.9, { col = "wood", mat = "wood", bone = bone, pri = 1.5, role = "held", name = "Club", trail = true }, 0.1)
	end
end

-- Cape: a slightly curved thin slab behind the shoulders, made of two panels at different tilts (never coplanar).
function Props.cape(B: any, top: { number }, w: number, h: number, bone: string, col: string?)
	local x, y, z = top[1], top[2], top[3]
	local upper = B:block(w, h * 0.55, w * 0.06, at(x, y - h * 0.27, z + w * 0.08, rad(8), 0, 0), { col = col or "secondary", mat = "cloth", bone = bone, pri = 1.6, role = "cape", name = "Cape", trail = true })
	local lower = B:block(w * 1.1, h * 0.5, w * 0.055, at(x, y - h * 0.72, z + w * 0.16, rad(14), 0, 0), { col = col or "secondary", mat = "cloth", bone = bone, pri = 3.2, role = "cape", name = "CapeLow" })
	-- sculpt: one hanging cloth with folds and a scalloped hem (s_cape); the two slabs are the primitive fallback
	B:sculpt(upper, "s_cape", { lower })
end

return Props
