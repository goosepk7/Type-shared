--!strict
-- Humanoid: people and archetypes (wizard, knight, robot, giant, skeleton, astronaut, ninja, chef, royalty,
-- pirate, viking...). Heroic stylised proportions (big head and hands so they read on a phone).

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Heads = require(script.Parent.Parent.Heads)
local Props = require(script.Parent.Parent.Props)

local at = Geom.at
local rad = math.rad

local function archetype(ctx: any): string
	local t, id = ctx.traits, string.lower(ctx.result.id)
	if ctx.kind then
		return string.lower(ctx.kind)
	end
	local function has(w: string): boolean
		-- word-start match so "viking" never matches "king"
		return string.find(id, "%f[%a]" .. w) ~= nil
	end
	if t.robot then
		return "robot"
	elseif t.skeleton or has("skeleton") or has("zombie") then
		return "skeleton"
	elseif has("wizard") or has("mage") or has("sorcer") or has("warlock") or has("witch") then
		return "wizard"
	elseif has("knight") or has("paladin") or has("samurai") or has("soldier") or has("guard") then
		return "knight"
	elseif has("astronaut") or has("cosmonaut") then
		return "astronaut"
	elseif has("ninja") or has("assassin") or has("thief") then
		return "ninja"
	elseif has("chef") or has("cook") or has("baker") then
		return "chef"
	elseif t.crown or has("king") or has("queen") or has("prince") or has("emperor") then
		return "royal"
	elseif has("pirate") or has("captain") then
		return "pirate"
	elseif has("viking") or has("barbarian") then
		return "viking"
	elseif has("cowboy") or has("sheriff") or has("ranger") then
		return "cowboy"
	elseif has("giant") or has("titan") or has("ogre") or has("cyclops") or t.golem then
		return "giant"
	elseif t.helmet then
		return "knight"
	elseif t.hat then
		return "wizard"
	end
	return "person"
end

return function(B: any, ctx: any)
	local t = ctx.traits
	local detail = ctx.detail
	local kind = archetype(ctx)
	local giant = kind == "giant"
	local robot = kind == "robot"
	local skel = kind == "skeleton"
	local legLen = if giant then 1.7 else 1.45
	local torsoH = if giant then 1.9 else 1.45
	local torsoW = if giant then 1.7 elseif robot then 1.3 else 1.12
	local headS = if giant then 1.0 else 1.12
	local armW = if giant then 0.5 elseif skel then 0.18 else 0.3
	local hipY = legLen
	B.boneIndex.Body.pos = { 0, hipY, 0 }

	local shirt = if robot then "primary" elseif kind == "chef" then "white" elseif kind == "knight" then "metal" elseif skel then "white" else "primary"
	local pants = if robot then "dark" elseif kind == "knight" then "steel" elseif skel then "white" elseif kind == "chef" then "black" else "secondary"
	local mat = if robot or kind == "knight" then "metal" else "cloth"

	-- torso (chest bone for leaning / breathing)
	B:bone("Chest", "Body", 0, hipY + 0.3, 0)
	B:setRig("chest", "Chest")
	if robot then
		B:block(torsoW, torsoH, torsoW * 0.72, at(0, hipY + torsoH * 0.55, 0), { col = shirt, mat = "metal", bone = "Chest", pri = 1, role = "torso", name = "Torso" })
		if detail >= 2 then
			B:block(torsoW * 0.55, torsoH * 0.35, 0.1, at(0, hipY + torsoH * 0.62, -torsoW * 0.36 - 0.02), { col = "glow", mat = "neon", glow = true, bone = "Chest", pri = 2.2, role = "gem", name = "ChestLight" })
		end
	elseif skel then
		B:ell(torsoW * 0.85, torsoH * 0.8, torsoW * 0.55, at(0, hipY + torsoH * 0.6, 0), { col = "white", mat = "hard", bone = "Chest", pri = 1, role = "torso", name = "Ribs", tr = 0 })
		if detail >= 2 then
			for i = 1, 2 do
				B:cyl(0.12, torsoW * 0.62, at(0, hipY + torsoH * (0.45 + i * 0.15), -torsoW * 0.27 - 0.02, 0, 0, 0), { col = "dark", mat = "hard", bone = "Chest", pri = 2.5 + i * 0.1, role = "detail" })
			end
		end
	else
		B:ell(torsoW, torsoH, torsoW * 0.66, at(0, hipY + torsoH * 0.52, 0), { col = shirt, mat = mat, bone = "Chest", pri = 1, role = "torso", name = "Torso" })
	end
	-- pelvis / belt
	B:ell(torsoW * 0.92, 0.6, torsoW * 0.62, at(0, hipY + 0.05, 0.01), { col = pants, mat = mat, pri = 1.15, role = "torso", name = "Pelvis" })
	if detail >= 2 and not robot and not skel then
		B:ell(torsoW * 0.97, 0.22, torsoW * 0.66, at(0, hipY + 0.3, 0.005), { col = if kind == "wizard" then "gold" else "darkWood", mat = "cloth", bone = "Chest", pri = 2.4, role = "detail", name = "Belt" })
	end

	-- legs
	Parts.legPair(B, { tag = "", x = torsoW * 0.24, y = hipY, z = 0, w = if giant then 0.5 elseif skel then 0.2 else 0.32, kind = if robot then "robot" else "paw", col = pants, mat = mat, phase = 0, thigh = 1.15, bend = -0.25 })

	-- arms
	local shoulderY = hipY + torsoH * 0.88
	local hand = Parts.armPair(B, {
		x = torsoW * 0.52, y = shoulderY, z = 0, len = (if giant then 2.2 else 1.45), w = armW,
		col = if skel then "white" else shirt, sleeve = if skel then "white" else shirt, foreCol = if robot or kind == "knight" or skel then nil else "skin",
		mat = mat, hand = if robot or kind == "knight" then "mitt" elseif giant then "fist" else "fist",
		handCol = if skel then "white" elseif kind == "knight" then "steel" else "skin", out = 0.22, fwd = 0.1,
	})

	-- neck and head
	local neckTop = { 0, hipY + torsoH * 1.0, 0 }
	B:bone("Head", "Chest", neckTop[1], neckTop[2], neckTop[3])
	B:setRig("head", "Head")
	local info: any
	if robot then
		local s = headS
		B:block(s * 0.95, s * 0.82, s * 0.85, at(0, neckTop[2] + s * 0.45, 0), { col = "primary", mat = "metal", bone = "Head", pri = 1.1, role = "head", name = "Head" })
		Heads.objectFace(B, t, at(0, neckTop[2] + s * 0.48, -s * 0.425), s * 0.95, "Head", { kind = "robot", eye = 0.24 })
		if detail >= 2 then
			B:cyl(s * 0.5, s * 0.08, at(0, neckTop[2] + s * 1.05, 0, 0, 0, rad(90)), { col = "steel", mat = "metal", bone = "Head", pri = 2.5, role = "antenna", name = "Antenna" })
			B:ball(s * 0.2, at(0, neckTop[2] + s * 1.3, 0), { col = "glow", mat = "neon", glow = true, bone = "Head", pri = 2.6, role = "gem", name = "AntennaTip", trail = true })
			B:mcyl(s * 0.16, s * 0.4, at(s * 0.5, neckTop[2] + s * 0.45, 0), { col = "secondary", mat = "metal", bone = "Head", pri = 2.8, role = "ear" })
		end
		info = { top = { 0, neckTop[2] + s * 0.86, 0 } }
	else
		info = Heads.person(B, { p = neckTop, s = headS, bone = "Head", skin = if skel then "white" else "skin", eyes = if skel then "glow" else nil, noNose = skel }, t)
	end

	-- archetype dressing
	local top = info.top
	if kind == "wizard" then
		Props.hat(B, "wizard", { 0, top[2] - headS * 0.05, top[3] }, headS, "Head", { col = "primary" })
		-- long beard
		if detail >= 1 then
			B:ell(headS * 0.62, headS * 0.85, headS * 0.42, at(0, top[2] - headS * 1.08, -headS * 0.28, rad(-10), 0, 0), { col = "white", mat = "fur", bone = "Head", pri = 1.5, role = "beard", name = "Beard" })
		end
		Props.held(B, "staff", hand, armW, "ForeR")
		-- robe skirt
		B:limb({ 0, hipY + 0.3, 0 }, { 0, 0.3, 0.05 }, torsoW * 1.25, { col = "primary", mat = "cloth", pri = 1.3, role = "torso", name = "Robe", depth = torsoW * 0.9 }, 0.15)
	elseif kind == "knight" then
		Props.hat(B, "helmet", top, headS, "Head", { col = "metal", plume = "secondary" })
		Props.held(B, "sword", hand, armW, "ForeR")
		Props.held(B, "shield", { -hand[1], hand[2] + 0.2, hand[3] }, armW, "ForeL", { col = "secondary" })
		if detail >= 2 then
			B:mell(armW * 2.4, armW * 1.4, armW * 2.2, at(torsoW * 0.55, shoulderY + 0.05, 0), { col = "steel", mat = "metal", bone = "Arm#", pri = 1.8, role = "armour", name = "Pauldron#" })
		end
	elseif kind == "astronaut" then
		Props.hat(B, "astronaut", top, headS, "Head")
		B:block(torsoW * 0.8, torsoH * 0.7, 0.55, at(0, hipY + torsoH * 0.6, torsoW * 0.42), { col = "white", mat = "plastic", bone = "Chest", pri = 1.6, role = "detail", name = "Backpack" })
	elseif kind == "ninja" then
		Props.hat(B, "ninja", top, headS, "Head", { col = "primary" })
		Props.held(B, "sword", hand, armW, "ForeR")
	elseif kind == "chef" then
		Props.hat(B, "chef", { 0, top[2] - headS * 0.08, top[3] }, headS, "Head")
		Props.held(B, "spoon", hand, armW, "ForeR")
		if detail >= 3 then
			B:mell(headS * 0.25, headS * 0.08, headS * 0.1, at(headS * 0.12, top[2] - headS * 0.78, -headS * 0.43, 0, 0, rad(12)), { col = "hair", mat = "fur", bone = "Head", pri = 3.2, role = "beard", name = "Mustache#" })
		end
	elseif kind == "royal" then
		Props.hat(B, "crown", { 0, top[2] - headS * 0.08, top[3] }, headS, "Head")
		Props.cape(B, { 0, shoulderY + 0.1, torsoW * 0.32 }, torsoW * 1.25, torsoH + legLen * 0.8, "Chest", "red")
		Props.held(B, "wand", hand, armW, "ForeR")
	elseif kind == "pirate" then
		Props.hat(B, "pirate", { 0, top[2] - headS * 0.1, top[3] }, headS, "Head")
		Props.held(B, "sword", hand, armW, "ForeR")
	elseif kind == "viking" then
		Props.hat(B, "horned", top, headS, "Head")
		B:ell(headS * 0.66, headS * 0.7, headS * 0.42, at(0, top[2] - headS * 1.02, -headS * 0.3, rad(-10), 0, 0), { col = "hair", mat = "fur", bone = "Head", pri = 1.5, role = "beard", name = "Beard" })
		Props.held(B, "axe", hand, armW, "ForeR")
	elseif kind == "cowboy" then
		Props.hat(B, "cowboy", { 0, top[2] - headS * 0.1, top[3] }, headS, "Head")
	elseif kind == "giant" then
		Props.held(B, "club", hand, armW, "ForeR")
		Props.hat(B, "hair", top, headS, "Head")
	elseif skel then
		-- nothing: the glow eyes and white bones are the read
	elseif not robot then
		Props.hat(B, "hair", top, headS, "Head")
	end

	B:socket("core", at(0, hipY + torsoH * 0.55, 0), "Chest")
	B:setRig("gait", if giant then "heavy" elseif robot then "stomp" else "biped")
end
