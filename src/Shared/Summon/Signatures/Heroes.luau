--!strict
-- Hand-built people signatures: robot, wizard, knight.

local MeshMap = require(script.Parent.Parent.MeshMap)
local Kit = require(script.Parent.Parent.SigKit)
local Props = require(script.Parent.Parent.Props)

local at, rad = Kit.at, Kit.rad

local S = {}

S.robot = {
	plan = "Humanoid|Robot",
	build = function(B: any, ctx: any)
		local A = Kit.base(B, ctx, "Humanoid", "robot", { robot = true, mechanical = true })
		local mn, mx = A.bodyMin, A.bodyMax
		local w, h = mx[1] - mn[1], mx[2] - mn[2]
		local s = A.headW
		-- chest reactor light + vent grille
		B:cyl(w * 0.08, w * 0.3, at(A.bodyC[1], A.bodyC[2] + h * 0.12, mn[3] - w * 0.015, 0, rad(90), 0), { col = "glow", mat = "neon", glow = true, bone = A.body.bone, pri = 1.45, role = "gem", name = "Reactor", noCore = true })
		if ctx.detail >= 2 then
			for i = 1, 2 do
				B:block(w * 0.42, h * 0.035, w * 0.06, at(A.bodyC[1], A.bodyC[2] - h * (0.12 + i * 0.07), mn[3] + w * 0.01), { col = "gunmetal", mat = "metal", bone = A.body.bone, pri = 2.4 + i * 0.1, role = "detail", name = "Vent" .. i, noCore = true })
			end
		end
		-- antenna with blinking tip and ear bolts
		local tip = { A.headC[1] + s * 0.18, A.top[2] + s * 0.55, A.headC[3] }
		B:rod({ A.headC[1] + s * 0.18, A.top[2] - s * 0.05, A.headC[3] }, tip, s * 0.06, { col = "steel", mat = "metal", bone = A.headBone, pri = 1.6, role = "antenna", name = "Antenna", noCore = true })
		B:ball(s * 0.18, at(tip[1], tip[2], tip[3]), { col = "red", mat = "neon", glow = true, bone = A.headBone, pri = 1.7, role = "gem", name = "AntennaTip", noCore = true, needs = "Antenna" })
		B:mcyl(s * 0.16, s * 0.3, at((A.headMax[1] - A.headMin[1]) * 0.5 + s * 0.02, A.headC[2], A.headC[3]), { col = "gunmetal", mat = "metal", bone = A.headBone, pri = 1.9, role = "detail", name = "EarBolt#", noCore = true })
		B:setRig("gait", "stomp")
		B:setRig("materialMotion", "clank")
		-- hero sculpt (catalogue/s_robot.py): panelled chest and head, piston limbs; the lights, vents, antennas and ear
		-- discs stay their own parts
		local P, lead, _, on = MeshMap.sculptor(B, "robot")
		if P.Torso and P.Pelvis and P.Head and on("limb", "KneeR")[1] and on("limb", "ForeR")[1] then
			lead(P.Torso, "s_robot_chest", nil, 1.15)
			lead(P.Pelvis, "s_robot_pelvis")
			lead(P.Head, "s_robot_head")
			for _, side in { "R", "L" } do
				lead(on("limb", "Hip" .. side)[1], "s_robot_thigh", nil, 1.15)
				lead(on("limb", "Knee" .. side)[1], "s_robot_shin", on("foot", "Knee" .. side))
				lead(on("limb", "Arm" .. side)[1], "s_robot_arm", nil, 1.15)
				lead(on("limb", "Fore" .. side)[1], "s_robot_fore", on("hand", "Fore" .. side))
			end
		end
	end,
}

S.wizard = {
	plan = "Humanoid|Wizard",
	build = function(B: any, ctx: any)
		local A = Kit.base(B, ctx, "Humanoid", "wizard", { magic = true, beard = true })
		local mn, mx = A.bodyMin, A.bodyMax
		local w, h = mx[1] - mn[1], mx[2] - mn[2]
		-- flowing cape and a floating spell orb
		Props.cape(B, { 0, mx[2] - h * 0.05, mx[3] }, w * 0.95, h * 1.05, A.body.bone, "secondary")
		B:ball(w * 0.28, at(-w * 0.95, A.bodyC[2] + h * 0.35, mn[3] - w * 0.35), { col = "glow", mat = "neon", glow = true, bone = A.body.bone, pri = 1.6, role = "gem", name = "SpellOrb", trail = true, noCore = true })
		B:emit("runes", nil, { socket = "core", rate = 10 })
		-- hero sculpt (catalogue/s_wizard.py): the floor-length robe contains the legs, the hat is one piece, hands and
		-- face stay their own parts
		local P, lead, named, on = MeshMap.sculptor(B, "wizard")
		if P.Robe and P.Torso and P.HatBrim and P.HatMid and P.Beard and on("limb", "ForeR")[1] then
			local inRobe = named("Pelvis")
			for _, bone in { "HipR", "HipL", "KneeR", "KneeL" } do
				for _, role in { "limb", "foot" } do
					for _, p in on(role, bone) do
						table.insert(inRobe, p)
					end
				end
			end
			for _, m in inRobe do
				m.pri = math.max(m.pri or 2, 3.2)
			end
			for _, m in named("Belt", "HatBase", "HatTip", "StaffClaw") do
				m.pri = math.max(m.pri or 2, 3.2)
			end
			for _, m in named("PupilR", "PupilL") do
				m.pri = math.min(m.pri or 2, 1.52)
			end
			lead(P.Robe, "s_wizard_robe", inRobe, 1.1)
			lead(P.Torso, "s_wizard_top", named("Belt"), 1.2)
			for _, side in { "R", "L" } do
				lead(on("limb", "Arm" .. side)[1], "s_wizard_sleeve")
				local fore = on("limb", "Fore" .. side)[1]
				if fore then
					fore.col, fore.mat = P.Torso.col, P.Torso.mat -- the forearm is sleeve now, not skin
				end
				lead(fore, "s_wizard_cuff")
			end
			lead(P.HatBrim, "s_wizard_hat", named("HatBase", "HatMid", "HatTip"))
			lead(P.Beard, "s_wizard_beard")
			lead(P.Staff, "s_wizard_staff", named("StaffClaw"))
		end
	end,
}

S.knight = {
	plan = "Humanoid|Knight",
	build = function(B: any, ctx: any)
		local A = Kit.base(B, ctx, "Humanoid", "knight", { armour = true })
		local s = A.headW
		local mn, mx = A.bodyMin, A.bodyMax
		local w, h = mx[1] - mn[1], mx[2] - mn[2]
		-- red plume sweeping back off the helmet
		B:limb({ A.headC[1], A.top[2] - s * 0.02, A.headC[3] - s * 0.1 }, { A.headC[1], A.top[2] + s * 0.42, A.headC[3] + s * 0.55 }, s * 0.32,
			{ col = "secondary", mat = "fur", bone = A.headBone, pri = 1.45, role = "hat", name = "Plume", trail = true }, 0.15)
		Props.cape(B, { 0, mx[2] - h * 0.05, mx[3] }, w * 0.95, h * 0.95, A.body.bone, "secondary")
		-- heraldic cross on the chest
		B:block(w * 0.08, h * 0.32, w * 0.05, at(A.bodyC[1], A.bodyC[2] + h * 0.06, mn[3] + w * 0.005), { col = "secondary", mat = "cloth", bone = A.body.bone, pri = 1.9, role = "detail", name = "CrossV", noCore = true })
		B:block(w * 0.3, h * 0.07, w * 0.05, at(A.bodyC[1], A.bodyC[2] + h * 0.12, mn[3] + w * 0.003), { col = "secondary", mat = "cloth", bone = A.body.bone, pri = 1.95, role = "detail", name = "CrossH", noCore = true, needs = "CrossV" })
		B:setRig("gait", "stomp")
		B:setRig("materialMotion", "clank")
		-- hero sculpt (catalogue/s_knight.py): full plate cut along the humanoid rig; the face stays the person head
		local P, lead, named, on = MeshMap.sculptor(B, "knight")
		local thigh, shin = on("limb", "HipR")[1], on("limb", "KneeR")[1]
		if P.Torso and P.Pelvis and P.Helmet and thigh and shin and on("limb", "ForeR")[1] then
			-- primitives that only exist inside a sculpt go first when the budget is short; both pupils outrank them
			for _, m in named("Belt", "Visor", "BladeTip", "Guard", "Grip", "Boss", "CrossH") do
				m.pri = math.max(m.pri or 2, 3.2)
			end
			for _, m in named("PupilR", "PupilL", "PauldronR", "PauldronL", "CrossV") do
				m.pri = math.min(m.pri or 2, 1.52)
			end
			lead(P.Torso, "s_knight_cuirass", named("Belt"), 1.15)
			lead(P.Pelvis, "s_knight_fauld")
			for _, side in { "R", "L" } do
				lead(on("limb", "Hip" .. side)[1], "s_knight_cuisse", nil, 1.2)
				lead(on("limb", "Knee" .. side)[1], "s_knight_greave", on("foot", "Knee" .. side))
				lead(on("limb", "Arm" .. side)[1], "s_knight_rerebrace")
				lead(on("limb", "Fore" .. side)[1], "s_knight_gauntlet", on("hand", "Fore" .. side))
				lead(P["Pauldron" .. side], "s_knight_pauldron")
			end
			lead(P.Helmet, "s_knight_helm", named("Visor"))
			for _, m in named("Plume") do
				if m ~= P.Plume then
					m.pri = math.max(m.pri or 2, 3.2)
				end
			end
			lead(P.Plume, "s_knight_plume", named("Plume"))
			lead(P.Blade, "s_sword", named("BladeTip", "Guard", "Grip"))
			lead(P.CrossV, "s_knight_cross", named("CrossH"))
			lead(P.Shield, "s_knight_shield", named("Boss"))
		end
	end,
}

return S
