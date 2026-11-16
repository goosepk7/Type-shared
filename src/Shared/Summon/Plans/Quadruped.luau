--!strict
-- Quadruped: mammals, reptiles, dragons, dinosaurs on four legs. Torso is sculpted from chest + belly + haunch
-- masses; legs are two-bone; head kind from tags (mammal / reptile / bird-beaked gryphon).

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Heads = require(script.Parent.Parent.Heads)

local at = Geom.at
local rad = math.rad

return function(B: any, ctx: any)
	local t = ctx.traits
	local rng = B.rng
	local reptile = t.scaly or t.dragon or t.dino
	local heavy = t.heavy or t.durability >= 8 or t.trunk or t.shell
	local bulk = (0.85 + t.durability * 0.045) * rng:jitter(1, 0.05)
	local legLen = (0.95 + t.speed * 0.07) * rng:jitter(1, 0.06)
	if t.stubby or t.shell then
		legLen *= 0.6
	elseif t.longLegs then
		legLen *= 1.35
	end
	if reptile and not t.dragon then
		legLen *= 0.82
	end
	if t.chubby then
		bulk *= 1.12
	end
	local L = (2.4 + (if t.long or t.longTail then 0.4 else 0)) * rng:jitter(1, 0.05)
	local H = 1.15 * bulk
	local W = 1.05 * bulk * (if heavy then 1.12 else 1)
	local bodyY = legLen + H * 0.36

	B.boneIndex.Body.pos = { 0, bodyY, 0 }
	-- torso: chest (front, tallest), barrel, haunch
	local detail = ctx.detail
	if detail <= 1 then
		B:ell(W * 1.04, H * 1.08, L * 1.02, at(0, bodyY + H * 0.03, 0), { col = "primary", mat = "fur", pri = 1, role = "body", name = "Torso" })
	else
		B:ell(W, H, L * 0.78, at(0, bodyY, 0.02), { col = "primary", mat = "fur", pri = 1, role = "body", name = "Torso" })
		B:ell(W * 1.06, H * 1.1, L * 0.5, at(0, bodyY + H * 0.06, -L * 0.3, rad(-8), 0, 0), { col = "primary", mat = "fur", pri = 1.05, role = "body", name = "Chest" })
		B:ell(W * 1.0, H * 1.0, L * 0.46, at(0, bodyY + H * 0.03, L * 0.32), { col = "primary", mat = "fur", pri = 1.15, role = "body", name = "Haunch" })
	end
	if detail >= 2 then
		-- belly / chest plate in the secondary colour
		B:ell(W * 0.8, H * 0.62, L * 0.7, at(0, bodyY - H * 0.24, -L * 0.04), { col = "belly", mat = "fur", pri = 2.2, role = "detail", name = "Belly" })
	end

	-- shell (turtle) or armour plates on the back
	if t.shell then
		B:ell(W * 1.35, H * 1.05, L * 1.1, at(0, bodyY + H * 0.32, 0.02), { col = "secondary", mat = "hard", pri = 1.02, role = "body", name = "Shell" })
		B:ell(W * 1.42, H * 0.22, L * 1.16, at(0, bodyY - H * 0.05, 0.02), { col = "dark", mat = "hard", pri = 1.9, role = "detail", name = "ShellRim" })
	elseif t.armour then
		for i = 1, 3 do
			B:ell(W * 0.8, H * 0.32, L * 0.26, at(0, bodyY + H * 0.44, -L * 0.3 + (i - 1) * L * 0.3, rad(-6 + i * 4), 0, 0),
				{ col = "accent", mat = "hard", pri = 2.6 + i * 0.1, role = "detail" })
		end
	end

	-- legs: front pair under the chest, back pair under the haunch (thicker thighs)
	local legW = 0.34 * bulk * (if heavy then 1.3 else 1)
	local kind = if t.trunk or (heavy and not reptile and t.size ~= "Small") then "pillar"
		elseif reptile then "claw"
		elseif string.find(ctx.result.id, "horse") or string.find(ctx.result.id, "deer") or t.unihorn or string.find(ctx.result.id, "goat") or string.find(ctx.result.id, "cow") then "hoof"
		else "paw"
	local hipY = legLen + H * 0.05
	local splay = if reptile then W * 0.12 else 0
	Parts.legPair(B, { tag = "F", x = W * 0.34, y = hipY, z = -L * 0.3, w = legW, kind = kind, phase = 0, splay = splay, claws = reptile or t.claws, thigh = 1.25 })
	Parts.legPair(B, { tag = "B", x = W * 0.36, y = hipY, z = L * 0.32, w = legW * 1.05, kind = kind, phase = 0.5, splay = splay, claws = reptile or t.claws, thigh = 1.5, bend = if kind == "paw" or kind == "hoof" then 0.6 else nil })

	-- neck + head
	local neckLen = (if t.longNeck then 1.7 else 0.55) * (if reptile then 1.15 else 1)
	local neckBase = { 0, bodyY + H * 0.25, -L * 0.42 }
	local neckTop = { 0, neckBase[2] + neckLen * 0.85, neckBase[3] - neckLen * 0.5 }
	B:bone("Neck", "Body", neckBase[1], neckBase[2], neckBase[3])
	B:setRig("neck", "Neck")
	if detail >= 2 or t.longNeck then
		B:limb(neckBase, neckTop, W * (if t.longNeck then 0.42 else 0.62), { col = "primary", mat = "fur", bone = "Neck", pri = if t.longNeck then 1.2 else 1.75, role = "body", name = "Neck" }, 0.35)
	else
		-- short-necked at low detail: head sits low on the chest
		neckTop = { 0, neckBase[2] + neckLen * 0.45, neckBase[3] - neckLen * 0.2 }
	end
	B:bone("Head", "Neck", neckTop[1], neckTop[2], neckTop[3])
	B:setRig("head", "Head")
	local headS = (1.05 + (if t.bigHead or t.cute then 0.3 else 0) + (if detail <= 1 then 0.2 else 0)) * (0.8 + bulk * 0.2)
	local info
	if t.beak then
		info = Heads.bird(B, { p = neckTop, s = headS }, t)
	elseif reptile then
		info = Heads.reptile(B, { p = neckTop, s = headS * 1.05 }, t)
	else
		local long = if kind == "hoof" then 1.6 else 1
		info = Heads.mammal(B, { p = neckTop, s = headS, long = long }, t)
	end

	-- ears / horns / crest / mane
	if not reptile and not t.beak then
		local ek = if t.longEars then "long" elseif t.floppyEars then "floppy" elseif t.roundEars then "round" elseif t.bigEars then "big" else "pointy"
		if t.trunk then
			ek = "big"
		end
		Parts.ears(B, { bone = "Head", x = info.earX, y = info.earY, z = info.earZ, s = headS * (if ek == "big" then 0.95 else 0.42), kind = ek })
	elseif reptile and (t.dragon or t.mythical) then
		Parts.ears(B, { bone = "Head", x = info.earX, y = info.earY, z = info.earZ, s = headS * 0.5, kind = "fin", pri = 3.2 })
	end
	if t.unihorn then
		Parts.horns(B, { bone = "Head", x = 0, y = info.top[2] - headS * 0.05, z = info.c[3] - headS * 0.3, len = headS * 1.1, w = headS * 0.2, kind = "uni", segs = 2, pri = 1.5, col = "gold" })
	elseif t.horns or t.dragon or (reptile and t.mythical) then
		Parts.horns(B, { bone = "Head", x = headS * 0.24, y = info.top[2] - headS * 0.1, z = info.top[3] + headS * 0.05, len = headS * (0.8 + t.power * 0.05), w = headS * 0.2, kind = if reptile then "swept" else "curved", segs = 3, pri = 1.6 })
	elseif t.antlers then
		Parts.antlers(B, { bone = "Head", x = headS * 0.2, y = info.top[2] - headS * 0.05, z = info.top[3], len = headS * 1.3 })
	end
	if t.mane then
		-- mane: fluffy collar around the neck root and head
		B:ell(W * 1.35, H * 1.05, L * 0.34, at(0, neckBase[2] + neckLen * 0.35, neckBase[3] - neckLen * 0.12, rad(-30), 0, 0), { col = "secondary", mat = "fur", bone = "Neck", pri = 1.4, role = "mane" })
		B:ell(headS * 1.5, headS * 1.45, headS * 0.7, at(0, info.c[2] + headS * 0.05, info.c[3] + headS * 0.32), { col = "secondary", mat = "fur", bone = "Head", pri = 1.5, role = "mane" })
	end
	if t.trunk then
		local m = info.mouth
		local tb = B:bone("Trunk", "Head", m[1], m[2] + headS * 0.1, m[3] + headS * 0.1)
		B:addRig("tail", tb)
		B:limb({ m[1], m[2] + headS * 0.12, m[3] + headS * 0.12 }, { m[1], m[2] - headS * 0.7, m[3] - headS * 0.25 }, headS * 0.3, { col = "primary", mat = "skin", bone = tb, pri = 1.4, role = "trunk" }, 0.2)
		B:limb({ m[1], m[2] - headS * 0.7, m[3] - headS * 0.25 }, { m[1], m[2] - headS * 1.25, m[3] - headS * 0.5 }, headS * 0.22, { col = "primary", mat = "skin", bone = tb, pri = 1.8, role = "trunk", trail = true }, 0.2)
	end
	if t.tusks then
		local m = info.mouth
		B:mlimb({ headS * 0.22, m[2] + headS * 0.05, m[3] + headS * 0.25 }, { headS * 0.36, m[2] - headS * 0.25, m[3] - headS * 0.45 }, headS * 0.14, { col = "tooth", mat = "hard", bone = "Head", pri = 2.0, role = "horn" }, 0.12)
	end

	-- wings
	if (t.wings or t.flies) and not t.noWings then
		local span = (L * 0.95 + W) * (if t.dragon then 1.25 else 1)
		Parts.wings(B, { x = W * 0.3, y = bodyY + H * 0.36, z = -L * 0.22, span = span, kind = t.wingKind })
	end

	-- back spikes
	if detail >= 2 and (t.spikes or (t.dragon and not t.fluffy)) then
		local pts = {}
		local n = 4
		for i = 1, n do
			local z = -L * 0.32 + (i - 1) / (n - 1) * L * 0.7
			table.insert(pts, { 0, bodyY + H * 0.44 - math.abs(z) * 0.08, z, 1 - math.abs(i - 2) * 0.15 })
		end
		Parts.spikeRow(B, { points = pts, h = H * 0.42, w = H * 0.14, pri = 2.8 })
	end

	-- tail
	local tailKind = if t.bushyTail or (t.fluffy and not reptile) then "bushy"
		elseif t.spikes and reptile then "spiked"
		elseif t.dragon then "spiked"
		elseif t.unihorn or kind == "hoof" then "tuft"
		else "plain"
	local tailLen = if reptile or t.longTail then L * 1.15 else L * 0.55
	local tailW = if reptile then W * 0.45 else (if tailKind == "bushy" then W * 0.3 else W * 0.16)
	Parts.tail(B, {
		start = { 0, bodyY + H * 0.12, L * 0.5 }, dir = { 0, if reptile then -0.12 else 0.55, 1 }, len = tailLen, w = tailW,
		segs = if detail <= 1 then 1 elseif reptile or t.longTail then 3 else 2, droop = if reptile then -0.1 else 0.1, kind = tailKind, taper = if tailKind == "bushy" then 0.95 else 0.68,
	})

	B:socket("core", at(0, bodyY, 0), "Body")
	B:setRig("gait", if heavy then "heavy" elseif reptile then "sprawl" else "trot")
end
