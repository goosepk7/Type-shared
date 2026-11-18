--!strict
-- Fish & sea life. Plans/Fish sorts a word into a sub-kind from its id and silhouette hint and hands it to a
-- builder: finned fish (Plans/SeaFish: fusiform, compressed disc, long, round, deep-sea, catfish, billfish,
-- tadpole; flatfish, rays, seahorses), sea mammals and reptiles (Plans/SeaMammal: whales and dolphins, seals and
-- sea cows, plesiosaurs and mosasaurs, merfolk), cephalopods (Plans/Cephalopod, the Octopus route: squid,
-- cuttlefish, nautilus, dumbo and vampire octopus), generic sharks on the shark signature, and jellyfish.
--
-- The legacy builds below (kind "shark" and kind "octopus") are the bases of the shark, octopus and kraken
-- signatures (SigKit.base with a forced kind): they stay exactly as they were.

local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Face = require(script.Parent.Parent.Face)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local SeaFish = require(script.Parent.SeaFish)
local SeaMammal = require(script.Parent.SeaMammal)
local Cephalopod = require(script.Parent.Cephalopod)

local function kindOf(ctx: any): string
	if ctx.kind then
		return ctx.kind
	end
	local t, id = ctx.traits, string.lower(ctx.result.id)
	local function has(w: string): boolean
		return string.find(id, w, 1, true) ~= nil
	end
	if t.tentacles and (has("octopus") or has("squid") or has("kraken") or has("cuttle")) then
		return "octopus"
	elseif t.jelly or has("jelly") or has("medusa") then
		return "jelly"
	elseif t.shark or has("shark") then
		return "shark"
	elseif t.whale or t.dolphin or has("whale") or has("dolphin") or has("orca") or has("porpoise") then
		return "whale"
	elseif has("sword") or has("marlin") or has("narwhal") then
		return "sword"
	elseif has("puffer") or has("blowfish") then
		return "puffer"
	elseif t.tentacles then
		return "octopus"
	end
	return "fish"
end

local function mood(B: any): string
	return B.ctx.result.mood or "Neutral"
end

local function octopus(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local squid = string.find(string.lower(ctx.result.id), "squid") or string.find(string.lower(ctx.result.id), "kraken")
	local headY = 2.3
	B.boneIndex.Body.pos = { 0, headY, 0 }
	local hr = { 1.15, 1.25, 1.1 }
	local hc = { 0, headY + 0.55, 0.25 }
	if squid then
		hr = { 0.9, 1.8, 0.9 }
		hc = { 0, headY + 1.2, 0.3 }
	end
	B:ell(hr[1] * 2, hr[2] * 2, hr[3] * 2, at(hc[1], hc[2], hc[3], rad(-12), 0, 0), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Mantle" })
	if squid and detail >= 2 then
		-- mantle fins: broad side to the viewer (thin axis front to back), sweeping out and up
		B:mwedge(0.12, 1.1, 1.0, Geom.mul(at(0.85, hc[2] + hr[2] * 0.6, hc[3] + 0.2, 0, 0, rad(-60)), at(0, 0, 0, 0, rad(90), 0)), { col = "secondary", mat = "skin", pri = 2.4, role = "fin", name = "MantleFin#" })
	end
	-- face on the front-lower mantle
	local fc = { 0, headY + 0.1, -0.15 }
	local fr = { 0.95, 0.85, 0.85 }
	B:ell(fr[1] * 2, fr[2] * 2, fr[3] * 2, at(fc[1], fc[2], fc[3]), { col = "primary", mat = "skin", pri = 1.1, role = "head", name = "Head" })
	Face.build(B, { face = { kind = "ellipsoid", c = fc, r = fr }, bone = "Body", mood = mood(B), detail = detail,
		kind = if t.mythical or (t.power or 5) >= 7 then "fierce" else "cute", spacing = 0.42, y = 0.2, d = 0.48, mouthY = -0.35, mouthW = 0.5, lidCol = "primary" })
	-- arms: radial, each a 2-3 segment curl on its own bone chain
	local n = if detail <= 0 then 4 elseif detail == 1 then 6 else 8
	local segs = if detail >= 3 then 3 elseif detail == 2 then 2 else 1
	for i = 1, n do
		local a = (i - 0.5) / n * math.pi * 2
		local dx, dz = sin(a), cos(a)
		local x, y, z = dx * 0.65, headY - 0.45, dz * 0.65 + 0.05
		local parent = "Body"
		local w = 0.42
		for sgi = 1, segs do
			local bname = B:bone("Arm" .. i .. "_" .. sgi, parent, x, y, z)
			local reach = (if squid then 1.2 else 1.0) * (1 - (sgi - 1) * 0.12)
			local ex = x + dx * reach * 0.75
			local ez = z + dz * reach * 0.75
			local ey = y - reach * (if sgi == 1 then 0.85 else 0.35) + (if sgi == segs then 0.35 else 0)
			local arm = B:limb({ x, y, z }, { ex, ey, ez }, w, { col = if sgi == segs and detail >= 2 then "secondary" else "primary", mat = "skin", bone = bname, pri = 1.2 + sgi * 0.35 + i * 0.01, role = "tentacle", trail = sgi == segs }, 0.3)
			arm.cf = Geom.rollY(arm.cf, 0, -1, 0) -- local +Z is the under side: where the sculpted suckers are
			B:addRig("tentacles", { bone = bname, index = i, seg = sgi })
			x, y, z = ex, ey, ez
			parent = bname
			w *= 0.72
		end
	end
	B:socket("core", at(0, headY + 0.3, 0.2), "Body")
	B:setRig("gait", "swim")
end

local function jelly(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local y = 2.6
	B.boneIndex.Body.pos = { 0, y, 0 }
	local c, r = { 0, y + 0.4, 0 }, { 1.3, 0.95, 1.3 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "glass", tr = 0.3, pri = 1, role = "body", name = "Bell" })
	B:ell(r[1] * 2.1, r[2] * 0.5, r[3] * 2.1, at(c[1], c[2] - r[2] * 0.62, c[3]), { col = "secondary", mat = "glass", tr = 0.35, pri = 1.5, role = "body", name = "Rim" })
	if detail >= 2 then
		B:ell(r[1] * 1.0, r[2] * 0.9, r[3] * 1.0, at(c[1], c[2] + 0.05, c[3]), { col = "glow", mat = "neon", glow = true, pri = 2.2, role = "gem", name = "Glow", noCore = true })
	end
	Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = "Body", mood = mood(B), detail = detail, kind = "cute", spacing = 0.45, y = 0.0, d = 0.42, mouthY = -0.32, mouthW = 0.45, lidCol = "primary" })
	local n = if detail <= 1 then 3 else 5
	for i = 1, n do
		local a = (i - 0.5) / n * math.pi * 2
		local bx, bz = sin(a) * 0.7, cos(a) * 0.7
		local bname = B:bone("Tent" .. i, "Body", bx, y - 0.2, bz)
		B:addRig("tentacles", { bone = bname, index = i, seg = 1 })
		B:limb({ bx, y - 0.1, bz }, { bx * 1.1, y - 2.3, bz * 1.1 }, 0.18, { col = "secondary", mat = "glass", tr = 0.25, bone = bname, pri = 1.6 + i * 0.05, role = "tentacle", trail = true }, 0.05)
	end
	B:socket("core", at(0, y + 0.3, 0), "Body")
	B:setRig("gait", "float")
end

local function legacy(B: any, ctx: any)
	local kind = kindOf(ctx)
	if kind == "octopus" then
		return octopus(B, ctx)
	elseif kind == "jelly" then
		return jelly(B, ctx)
	end
	local t, detail = ctx.traits, ctx.detail
	local shark, whale = kind == "shark", kind == "whale"
	local L = (if whale then 4.2 elseif shark then 3.8 elseif kind == "sword" then 3.2 else 2.6)
	local H = (if whale then 1.7 elseif shark then 1.25 elseif kind == "puffer" then 2.0 else 1.5)
	local W = (if kind == "puffer" then 2.0 elseif whale then 1.6 else H * 0.7)
	local y = H * 0.5 + 0.8
	B.boneIndex.Body.pos = { 0, y, 0 }
	-- body: front mass + tapering rear on the first tail bone (so the whole back half undulates)
	local hc, hr = { 0, y + H * 0.02, -L * 0.18 }, { W * 0.5, H * 0.5, L * 0.36 }
	B:ell(hr[1] * 2, hr[2] * 2, hr[3] * 2, at(hc[1], hc[2], hc[3]), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Body", mesh = "fish_body" })
	if detail >= 1 then
		B:ell(W * 0.8, H * 0.55, L * 0.62, at(0, y - H * 0.2, -L * 0.12), { col = "belly", mat = "skin", pri = 1.9, role = "detail", name = "Belly" })
	end
	local t1 = B:bone("Tail1", "Body", 0, y, L * 0.1)
	local t2 = B:bone("Tail2", t1, 0, y, L * 0.38)
	B:addRig("tail", t1)
	B:addRig("tail", t2)
	B:ell(W * 0.72, H * 0.72, L * 0.55, at(0, y, L * 0.22), { col = "primary", mat = "skin", bone = t1, pri = 1.1, role = "body", name = "Rear", mesh = "fish_rear" })
	-- tail fin
	if whale then
		B:mell(L * 0.32, 0.12, L * 0.16, at(L * 0.14, y + 0.05, L * 0.55, 0, rad(-25), 0), { col = "primary", mat = "skin", bone = t2, pri = 1.3, role = "fin", name = "Fluke#", trail = true })
	else
		local fh = H * (if shark then 1.0 else 0.9)
		B:wedge(0.12, fh * 0.7, L * 0.25, at(0, y + fh * 0.32, L * 0.6, rad(-35), 0, 0), { col = if shark then "primary" else "secondary", mat = "skin", bone = t2, pri = 1.3, role = "fin", name = "TailTop", trail = true })
		B:wedge(0.11, fh * 0.55, L * 0.2, at(0, y - fh * 0.24, L * 0.58, rad(180 + 35), 0, 0), { col = if shark then "primary" else "secondary", mat = "skin", bone = t2, pri = 1.35, role = "fin", name = "TailLow" })
	end
	-- dorsal + pectoral fins
	if kind ~= "puffer" then
		Parts.dorsal(B, { y = y + H * 0.4, z = -L * 0.05, t = 0.14, h = H * (if shark then 0.85 elseif kind == "sword" then 1.0 else 0.55), l = L * 0.3, col = if shark or whale then "primary" else "secondary", pri = 1.4 })
	end
	if detail >= 1 then
		B:mell(W * 0.9, 0.1, L * 0.18, at(W * 0.5, y - H * 0.22, -L * 0.15, rad(10), rad(-30), rad(-25)), { col = if shark or whale then "primary" else "secondary", mat = "skin", pri = 1.8, role = "fin", name = "Pectoral#" })
	end
	if kind == "sword" then
		B:limb({ 0, y + H * 0.05, -L * 0.45 }, { 0, y + H * 0.02, -L * 0.95 }, 0.14, { col = "secondary", mat = "hard", pri = 1.2, role = "horn", name = "Bill", trail = true }, 0.05)
	end
	if kind == "puffer" and detail >= 2 then
		for i = 1, 6 do
			local a = (i - 0.5) / 6 * math.pi * 2
			B:wedge(0.1, 0.45, 0.35, Geom.mul(at(0, y, -L * 0.15), at(sin(a) * W * 0.45, cos(a) * H * 0.45, 0, 0, 0, -a)), { col = "secondary", mat = "hard", pri = 3 + i * 0.05, role = "spike" })
		end
	end
	-- face on the front of the head
	local m = mood(B)
	Face.build(B, { face = { kind = "ellipsoid", c = hc, r = hr }, bone = "Body", mood = m, detail = detail,
		kind = if shark then "fierce" elseif t.cute then "cute" else (if (t.power or 5) >= 6 then "fierce" else "cute"),
		spacing = hr[1] * 0.62, y = hr[2] * 0.22, d = H * (if shark then 0.2 else 0.28), mouthY = -hr[2] * 0.35, mouthW = W * 0.5, lidCol = "primary",
		forceMouth = shark })
	if shark and detail >= 2 then
		Parts.teeth(B, { bone = "Body", y = y - H * 0.18, z = hc[3] - hr[3] * 0.86, r = W * 0.18, n = if detail >= 3 then 4 else 2, h = H * 0.14, pri = 2.6 })
	end
	B:socket("mouth", at(0, y - H * 0.15, -L * 0.55), "Body")
	B:socket("core", at(0, y, -L * 0.1), "Body")
	B:setRig("gait", "swim")
end

-- Sub-kind of a generic (non-signature) sea creature. Order matters: the first match wins.
local KINDS: { { any } } = {
	{ "mer", { "mermaid", "merman", "merrow", "iara", "amabie", "sea witch", "sharkataur", "mami wata", "siren queen" } },
	{ "seal", { "seal", "sea lion", "walrus", "manatee", "dugong", "sea cow" } },
	{ "reptile", { "plesiosaur", "elasmosaur", "pliosaur", "kronosaur", "liopleurodon", "nothosaur", "placodus", "mosasaur", "tylosaur", "prognathodon", "ambulocetus", "makara", "ketos" } },
	{ "whale", { "whale", "dolphin", "porpoise", "beluga", "narwhal", "orca", "vaquita", "ichthyosaur", "shonisaurus", "temnodontosaurus", "livyatan", "encantado", "bakekujira" } },
	{ "ray", { "stingray", " ray", "skate", "guitarfish", "sawfish", "manta" } },
	{ "flat", { "halibut", "flounder", "plaice", "turbot", "sole fish", "both eyes on one side" } },
	{ "seahorse", { "seahorse", "sea dragon", "pipefish", "shrimpfish", "hippocampus" } },
	{ "shark", { "shark", "bonnethead", "dogfish", "wobbegong", "cretoxyrhina", "edestus", "helicoprion", "stethacanthus", "megalodon" } },
	{ "billfish", { "swordfish", "marlin", "sailfish", "spear bill", "sword bill" } },
	{ "deep", { "angler", "fangtooth", "viperfish", "barreleye", "dragonfish", "coffinfish", "gulper", "huge fangs" } },
	{ "round", { "puffer", "blowfish", "porcupinefish", "boxfish", "lumpfish", "frogfish", "stonefish", "toadfish", "goldfish", "swell", "spiky round", "round lumpy", "cube" } },
	{ "catfish", { "catfish", "namazu", "pleco", "wels", "suckermouth" } },
	{ "tadpole", { "tadpole" } },
	{ "long", { "barracuda", " gar", "needlefish", "halfbeak", "pike", "muskellunge", "arowana", "bichir", "bowfin", "burbot", "lungfish", "paddlefish", "sturgeon", "wahoo", "cobia", "wolf fish", "snakehead", "tiktaalik", "coelacanth", "trumpetfish", "black dragon", "eel-like", "long body", "long toothy", "elephantnose", "oarfish", "remora", "mudskipper" } },
	{ "disc", { "angelfish", "discus", "butterflyfish", "tang", "surgeonfish", "moorish idol", "bluegill", "crappie", "opah", "sunfish", "batfish", "triggerfish", "filefish", "rabbitfish", "hatchetfish", "damselfish", "garibaldi", "spadefish", "sheepshead", "pompano", "piranha", "payara", "disc", "diamond fish", "oval fish", "tall" } },
}

local function classify(ctx: any): string
	local id = " " .. string.lower(ctx.result.id)
	local hint = string.lower((ctx.result.visual and ctx.result.visual.silhouetteHint) or "")
	local t = ctx.traits
	if t.jelly or string.find(id, "jelly", 1, true) or string.find(id, "medusa", 1, true) then
		return "jelly"
	end
	if t.tentacles and not string.find(id, "mermaid", 1, true) and not string.find(id, "witch", 1, true) then
		return "cephalopod"
	end
	for _, k in KINDS do
		for _, w in k[2] do
			if string.find(id, w, 1, true) then
				return k[1]
			end
		end
	end
	-- second pass on the hint only (so "ray-like shark" in a hint never beats the id)
	for _, k in KINDS do
		for _, w in k[2] do
			if #w > 4 and string.find(hint, w, 1, true) then
				return k[1]
			end
		end
	end
	if t.whale or t.dolphin then
		return "whale"
	end
	return "fish"
end

-- Generic sharks (bonnethead, dogfish, sawshark ...): the shark signature's body, recoloured, plus the trait that
-- names the species.
local plansMod: any = nil
local function shark(B: any, ctx: any)
	plansMod = plansMod or require(script.Parent) :: any
	local sig = plansMod.signatureHook and plansMod.signatureHook("shark")
	if sig == nil then
		ctx.kind = "shark"
		return legacy(B, ctx)
	end
	sig(B, ctx)
	local has = SeaFish.reader(ctx)
	local head
	for _, p in B.parts do
		if p.role == "body" and p.bone == "Body" and (head == nil or p.cf[3] < head.cf[3]) then
			head = p
		end
	end
	if head == nil then
		return
	end
	local hx, hy, hz = head.cf[1], head.cf[2], head.cf[3]
	local w, h, l = head.size[1], head.size[2], head.size[3]
	if has("hammer", "shovel") then
		-- cephalofoil: a flat wing of a head across the snout, eyes at its tips
		local span = w * (if has("small", "shovel") then 1.5 else 2.3)
		B:ell(span, h * 0.22, l * 0.3, at(hx, hy + h * 0.05, hz - l * 0.42), { col = "primary", mat = "skin", pri = 1.2, role = "head", name = "Hammer", mesh = false })
		if ctx.detail >= 1 then
			B:mball(h * 0.16, at(span * 0.47, hy + h * 0.08, hz - l * 0.44), { col = "pupil", mat = "glass", pri = 1.5, role = "eye", name = "HammerEye#", noCore = true })
		end
	end
	if has("saw") then
		B:ell(w * 0.22, h * 0.1, l * 0.7, at(hx, hy - h * 0.05, hz - l * 0.75), { col = "secondary", mat = "hard", pri = 1.3, role = "horn", name = "Saw", mesh = false })
	end
	if has("anvil") then
		B:ell(w * 0.9, h * 0.3, l * 0.25, at(hx, hy + h * 0.95, hz + l * 0.35), { col = "dark", mat = "hard", pri = 1.6, role = "fin", name = "Anvil", mesh = false })
	end
	if has("buzzsaw", "spiral of teeth", "scissor") and ctx.detail >= 2 then
		B:cyl(w * 0.18, h * 0.55, at(hx, hy - h * 0.38, hz - l * 0.25, 0, 0, 0), { col = "tooth", mat = "hard", pri = 2.2, role = "tooth", name = "Whorl" })
	end
	if has("beard", "tassel", "camo", "flat") and ctx.detail >= 2 then
		B:ell(w * 0.9, h * 0.25, l * 0.25, at(hx, hy - h * 0.4, hz - l * 0.35), { col = "secondary", mat = "skin", pri = 2.8, role = "detail", name = "Tassels", mesh = false })
	end
end

return function(B: any, ctx: any)
	local forced = ctx.kind
	if forced == "octopus" or forced == "shark" or forced == "jelly" then
		return legacy(B, ctx) -- signature bases (SigKit.base) and the jellyfish build
	end
	if forced == "cephalopod" then
		return Cephalopod.build(B, ctx)
	end
	local kind = forced or classify(ctx)
	if kind == "jelly" then
		ctx.kind = "jelly"
		return legacy(B, ctx)
	elseif kind == "cephalopod" then
		return Cephalopod.build(B, ctx)
	elseif kind == "mer" then
		return SeaMammal.mer(B, ctx)
	elseif kind == "seal" then
		return SeaMammal.seal(B, ctx)
	elseif kind == "reptile" then
		return SeaMammal.reptile(B, ctx)
	elseif kind == "whale" then
		return SeaMammal.whale(B, ctx)
	elseif kind == "ray" then
		return SeaFish.ray(B, ctx)
	elseif kind == "flat" then
		return SeaFish.flatfish(B, ctx)
	elseif kind == "seahorse" then
		return SeaFish.seahorse(B, ctx)
	elseif kind == "shark" then
		return shark(B, ctx)
	elseif kind == "sword" then
		return SeaFish.finfish(B, ctx, "billfish")
	elseif kind == "puffer" then
		return SeaFish.finfish(B, ctx, "round")
	end
	return SeaFish.finfish(B, ctx, kind)
end
