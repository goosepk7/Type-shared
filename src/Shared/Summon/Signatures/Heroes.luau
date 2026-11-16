--!strict
-- Hand-built people signatures: robot, wizard, knight.

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
	end,
}

return S
