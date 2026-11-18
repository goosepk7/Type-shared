--!strict
-- Blob: slimes and goo creatures, plus Food (cake, cupcake, pie, pizza, donut, burger, fruit, ice cream,
-- cookie, bread, cheese, egg, banana, carrot, candy, lollipop, generic). Food gets a face when it has a mood
-- or is silly/cute (Heads.wantsFace); slimes always do.

local Geom = require(script.Parent.Parent.Geom)
local Face = require(script.Parent.Parent.Face)
local Heads = require(script.Parent.Parent.Heads)

local at = Geom.at
local rad = math.rad
local sin, cos = math.sin, math.cos

local function foodKind(t: any, id: string): string?
	for _, k in { "cupcake", "cake", "pie", "pizza", "donut", "burger", "icecream", "lollipop", "candy", "cookie", "bread", "cheese", "egg", "banana", "carrot", "pumpkin", "melon", "fruit" } do
		if t[k] then
			return k
		end
	end
	if string.find(id, "ice cream") or string.find(id, "gelato") or string.find(id, "sundae") then
		return "icecream"
	end
	local function any(list: string): boolean
		for w in string.gmatch(list, "%S+") do
			if string.find(id, "%f[%a]" .. w) then
				return true
			end
		end
		return false
	end
	if any("pancake flapjack hotcake crepe blini") then
		return "pancake"
	elseif any("sandwich reuben panini blt sub hoagie club toastie gyro kebab") then
		return "burger"
	elseif any("croissant kouign danish pastry strudel turnover cruller") then
		return "croissant"
	elseif any("nut pecan walnut almond acorn hazelnut peanut cashew pistachio chestnut macadamia") then
		return "nut"
	end
	return nil
end

local function face(B: any, ctx: any, c: { number }, r: { number }, force: boolean?)
	local t = ctx.traits
	if not force and not Heads.wantsFace(B, t) then
		return
	end
	Face.build(B, { face = { kind = "ellipsoid", c = c, r = r }, bone = "Body", mood = ctx.result.mood, detail = math.max(1, ctx.detail), kind = "cute",
		spacing = r[1] * 0.36, y = r[2] * 0.15, d = math.min(r[1], r[2]) * 0.42, mouthY = -r[2] * 0.25, mouthW = r[1] * 0.55, forceMouth = true, lidCol = "primary" })
end

local function flatFace(B: any, ctx: any, cf: any, w: number)
	if Heads.wantsFace(B, ctx.traits) then
		Heads.objectFace(B, ctx.traits, cf, w, "Body")
	end
end

-- ============================================================================================================
-- CREATURES. Non-food Blob words cluster into sub-kinds, each with its own build (docs/SUMMON.md "Plan notes"):
--   slime (goo dome + skirt, drips, big face; crown / helmet / wings / antennae / nucleus / chrome / ooze variants),
--   slug (foot, mantle, eye stalks; sea slugs with rhinophores, cerata, ruffles, ear flaps; sea cucumber, sea pig),
--   snail (slug foot + coiled or spired shell), bivalve (two hinged valves, flesh, pearl, siphon), cap shells
--   (abalone, limpet, chiton, cowrie), jelly (bell + tentacles + oral arms; box, fried egg, man o war, comb jelly),
--   star (upright sea star, brittle star, crown-of-thorns, sand dollar), urchin, fuzz (dust bunny, cotton candy,
--   closet monster), cube (gelatinous / ice), heap (abomination, eldritch horror, shapeshifter, void), maw (planet
--   and star eaters, taotie, soul eater, umibozu), elemental (mud / poison sludge, rock monster), ghost (sheet ghosts,
--   poltergeist), tube (sea squirt, hydra, pyrosome, sea lily, cocoon), chain (salp, siphonophore), bubble (bubble
--   and balloon monsters), bot (robot vacuum, mine bot, pixel invader, ankle biter) and spirit (candle, lantern,
--   teapot, umbrella, sock). Sculpted unit pieces: tools/meshgen/catalogue/s_gen_blob.py.
-- ============================================================================================================

local Parts = require(script.Parent.Parent.Parts)
local Props = require(script.Parent.Parent.Props)

local KIND_BY_ID: { [string]: string } = {}
for kind, list in {
	slime = "alien blob|alien goo pet|blob|blob alien|blobfish|cell|dragon slime|fire slime|ghost slime|gold slime|jelly knight|kaiju slime|king slime|lava sprite|mecha slime|metal slime|poison slime|radiation blob|rainbow slime|tar monster|the blob|ink monster|ooze|virus bot|glitter blob|slime",
	slug = "banana slug|blue sea slug|lettuce sea slug|sea bunny|sea hare|sea slug|slug|sea pig|sea cucumber|nudibranch",
	snail = "conch|whelk|periwinkle|moon snail|giant african snail|cone snail|snail|sea snail|nautilus",
	bivalve = "clam|giant clam|oyster|mussel|scallop|geoduck|shipworm|cockle",
	cap = "abalone|limpet|chiton|cowrie",
	jelly = "box jellyfish|moon jellyfish|lion's mane jellyfish|immortal jellyfish|fried egg jellyfish|cassiopea|space jellyfish|moon jelly giant|robot jellyfish|portuguese man o war|comb jelly|sea gooseberry|jellyfish",
	star = "starfish|brittle star|crown-of-thorns starfish|sand dollar|sea star",
	urchin = "sea urchin|urchin",
	fuzz = "dust bunny monster|cotton candy monster|closet monster|dust bunny",
	cube = "gelatinous cube|ice slime",
	heap = "abomination|eldritch horror|shapeshifter|shapeshift alien|void creature",
	maw = "planet eater|star eater|taotie|soul eater|umibozu",
	elemental = "mud elemental|poison elemental|rock monster",
	ghost = "disco ghost|ghost costume kid|robot ghost|it|poltergeist",
	tube = "sea squirt|hydra polyp|pyrosome|sea lily|cocoon",
	chain = "salp|siphonophore",
	bubble = "bubble monster|balloon monster",
	bot = "robot vacuum monster|mine bot|alien invader|ankle",
	spirit = "candle spirit|spirit lantern|teapot spirit|tsukumogami|sock monster|sock puppet",
} do
	for w in string.gmatch(list, "[^|]+") do
		KIND_BY_ID[w] = kind
	end
end

-- silhouette-hint keywords for Blob words outside the list above (first match wins)
local KIND_HINTS: { { string } } = {
	{ "jellyfish", "jelly" }, { "slime", "slime" }, { "goo", "slime" }, { "ooze", "slime" }, { "slug", "slug" }, { "snail", "snail" },
	{ "spiral", "snail" }, { "clam", "bivalve" }, { "oyster", "bivalve" }, { "bivalve", "bivalve" }, { "starfish", "star" },
	{ "urchin", "urchin" }, { "spines", "urchin" }, { "fluff", "fuzz" }, { "furry", "fuzz" }, { "cube", "cube" },
	{ "tentacled", "heap" }, { "heap", "heap" }, { "maw", "maw" }, { "mouth", "maw" }, { "sludge", "elemental" },
	{ "elemental", "elemental" }, { "sheet", "ghost" }, { "ghost", "ghost" }, { "bubble", "bubble" }, { "balloon", "bubble" },
	{ "polyp", "tube" }, { "tube", "tube" }, { "chain", "chain" }, { "jelly", "slime" }, { "blob", "slime" },
}

local function creatureKind(id: string, hint: string, explicitOnly: boolean): string?
	local k = KIND_BY_ID[id]
	if k or explicitOnly then
		return k
	end
	local s = id .. " " .. hint
	for _, h in KIND_HINTS do
		if string.find(s, "%f[%a]" .. h[1]) then
			return h[1] and h[2]
		end
	end
	return nil
end

local function has(s: string, w: string): boolean
	return string.find(s, "%f[%a]" .. w) ~= nil
end

-- Face on an ellipsoid front. o: d (eye size), spacing, y, kind, fierce, mood, noMouth, detail
local function eface(B: any, ctx: any, c: { number }, r: { number }, o: any?)
	local oo = o or {}
	local m = math.min(r[1], r[2])
	return Face.build(B, {
		face = { kind = "ellipsoid", c = c, r = r }, bone = oo.bone or "Body", mood = oo.mood or ctx.result.mood, detail = oo.detail or math.max(1, ctx.detail),
		kind = oo.kind or (if oo.fierce then "fierce" else "cute"), spacing = oo.spacing or r[1] * 0.36, y = oo.y or r[2] * 0.14, d = oo.d or m * 0.46,
		mouthY = oo.mouthY or -r[2] * 0.28, mouthW = oo.mouthW or r[1] * 0.5, forceMouth = not oo.noMouth, noMouth = oo.noMouth, noBrows = oo.noBrows,
		lidCol = oo.lidCol or "primary", pri = oo.pri,
	})
end

-- A loose eyeball (abominations, closet monsters, floating alien eyes): white ball + pupil looking forward.
local function eyeball(B: any, d: number, cf: any, bone: string?, pri: number, name: string)
	local e = B:ball(d, cf, { col = "eyeWhite", mat = "skin", bone = bone, pri = pri, role = "detail", name = name, noCore = true, mesh = false })
	B:ell(d * 0.5, d * 0.5, d * 0.3, Geom.mul(cf, at(0, 0, -d * 0.36)), { col = "pupil", mat = "glass", bone = bone, pri = pri + 0.3, role = "detail", name = name .. "P", noCore = true, needs = e.name, mesh = false })
	return e
end

-- Point on an axis-aligned ellipsoid surface at azimuth a (0 = front, -Z; + toward +X) and height fraction v (-1..1).
local function onSurf(c: { number }, r: { number }, a: number, v: number, push: number?): { number }
	local k = math.sqrt(math.max(0, 1 - v * v))
	local p = push or 0
	return { c[1] + sin(a) * (r[1] * k + p), c[2] + v * r[2], c[3] - cos(a) * (r[3] * k + p) }
end

-- Tentacle hanging from p0 down to the ground-ish y1: 1-2 segments on their own bones (rig.tentacles).
local function tentacle(B: any, i: number, p0: { number }, p1: { number }, w: number, segs: number, o: any)
	local parent = o.parent or "Body"
	local prev = p0
	local made = {}
	for s = 1, segs do
		local u = s / segs
		local wob = if s < segs then (o.curl or 0.25) * (if i % 2 == 0 then 1 else -1) else 0
		local q = { p0[1] + (p1[1] - p0[1]) * u + wob * 0.3, p0[2] + (p1[2] - p0[2]) * u, p0[3] + (p1[3] - p0[3]) * u + wob * 0.2 }
		local bn = B:bone((o.name or "Tent") .. i .. "_" .. s, parent, prev[1], prev[2], prev[3])
		B:addRig("tentacles", { bone = bn, index = i, seg = s })
		local part = B:limb(prev, q, w * (1 - (s - 1) * 0.35), { col = o.col or "secondary", mat = o.mat or "skin", tr = o.tr, bone = bn, pri = (o.pri or 2) + (s - 1) * 0.4, role = "tentacle", name = (o.name or "Tent") .. i .. "S" .. s, trail = s == segs and i <= 2, glow = o.glow, mesh = o.mesh })
		table.insert(made, part)
		parent = bn
		prev = q
	end
	return made
end

-- SLIME ------------------------------------------------------------------------------------------------------
local function buildSlime(B: any, ctx: any, id: string, hint: string)
	local t, detail = ctx.traits, ctx.detail
	local f: { [string]: any } = {
		ooze = has(id, "ooze") or has(id, "tar") or has(id, "ink") or has(hint, "puddle"),
		float = has(id, "ghost") or has(hint, "floating jelly"),
		clear = has(id, "cell") or has(id, "ghost") or has(id, "the blob") or has(hint, "translucent") or has(hint, "see%-through"),
		metal = has(id, "metal") or has(id, "mecha") or has(hint, "chrome"),
		gold = has(id, "gold"),
		crown = t.crown or has(id, "king"),
		helmet = has(id, "knight") or has(hint, "helmet"),
		dragon = has(id, "dragon"),
		antennae = if has(hint, "one antenna") then 1 elseif t.antennae or has(id, "alien") then 2 else 0,
		floatEyes = has(hint, "floating eyes"),
		nose = has(id, "blobfish") or has(hint, "big nose"),
		cell = has(id, "cell"),
		code = has(id, "virus") or has(hint, "code"),
		bubbles = has(hint, "bubbl") or has(id, "radiation") or has(id, "poison"),
		embers = t.element == "Fire" or has(id, "lava") or has(id, "fire"),
		frost = t.element == "Ice",
		rainbow = has(id, "rainbow"),
	}
	local fierce = has(id, "tar") or has(id, "ink") or has(id, "kaiju") or has(id, "ooze") or t.spooky
	local flat = if f.ooze then 0.66 elseif f.nose then 0.86 else 1
	local wide = if f.ooze then 1.2 elseif f.nose then 1.08 else 1
	local r = { 1.45 * wide, 1.15 * flat, 1.35 * wide }
	local lift = if f.float then 0.7 else 0
	local c = { 0, r[2] + lift, 0 }
	B.boneIndex.Body.pos = { 0, 0.4 + lift, 0 }
	local mat = if f.metal then "metal" elseif f.gold then "foil" else "glass"
	local col = if f.gold then "gold" else "primary"
	local tr = if f.clear then 0.32 else nil
	local body = B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = col, mat = mat, tr = tr, pri = 1, role = "body", name = "Body" })
	local members = {}
	if detail >= 1 then
		table.insert(members, B:ell(r[1] * 2.35, r[2] * 0.7, r[3] * 2.3, at(0, c[2] - r[2] * 0.67, 0.02), { col = col, mat = mat, tr = tr, pri = 1.4, role = "body", name = "Base" }))
	end
	if detail >= 2 then
		-- drips running down the flanks (the sculpt has them; the primitive build shows these)
		for i, a in { 75, 180, 285 } do
			local p = onSurf(c, r, rad(a), -0.35, -0.04)
			table.insert(members, B:ell(r[1] * 0.26, r[2] * 0.62, r[1] * 0.24, at(p[1], p[2], p[3]), { col = col, mat = mat, tr = tr, pri = 2.4 + i * 0.05, role = "body", name = "Drip" .. i }))
		end
	end
	B:sculpt(body, "s_blob_slime", members)
	-- face: big, on the front, a touch above centre
	local fo: any = { d = math.min(r[1], r[2]) * (if f.ooze then 0.62 else 0.5), spacing = r[1] * 0.34, y = r[2] * (if f.ooze then 0.2 else 0.16), fierce = fierce }
	if f.metal and has(id, "mecha") or f.code then
		fo.kind = "robot"
	end
	if f.nose then
		fo.y, fo.mouthY = r[2] * 0.3, -r[2] * 0.42
	end
	eface(B, ctx, c, r, fo)
	if detail >= 2 and not f.metal then
		B:ell(r[1] * 0.4, r[2] * 0.2, r[3] * 0.24, at(-r[1] * 0.5, c[2] + r[2] * 0.6, c[3] - r[3] * 0.5, rad(-30), rad(24), rad(22)), { col = "shine", mat = "neon", pri = 3.2, role = "shine", name = "Gloss", noCore = true })
	end
	local top = { 0, c[2] + r[2] * 0.96, c[3] + 0.1 }
	if f.nose then
		B:limb({ 0, c[2] + r[2] * 0.12, c[3] - r[3] * 0.9 }, { 0, c[2] - r[2] * 0.3, c[3] - r[3] * 1.02 }, r[1] * 0.42, { col = "light", mat = "skin", pri = 1.3, role = "detail", name = "Nose", depth = r[1] * 0.36 }, 0.3)
	end
	if f.crown then
		Props.hat(B, "crown", { 0, top[2] - 0.12, top[3] }, r[1] * 0.95, "Body")
	elseif f.helmet then
		Props.hat(B, "helmet", { 0, top[2] + r[2] * 0.12, top[3] }, r[1] * 0.95, "Body", { plume = "secondary" })
	end
	if f.dragon then
		B:mlimb({ r[1] * 0.4, c[2] + r[2] * 0.72, 0 }, { r[1] * 0.62, c[2] + r[2] * 1.25, 0.35 }, 0.32, { col = "horn", mat = "hard", pri = 1.6, role = "horn", trail = true }, 0.2)
		Parts.wings(B, { x = r[1] * 0.6, y = c[2] + r[2] * 0.35, z = r[3] * 0.45, span = r[1] * 1.5, kind = "bat", pri = 1.7, detail = math.min(detail, 1) })
	end
	if f.antennae > 0 then
		for i = 1, f.antennae do
			local sx = if f.antennae == 1 then 0 else (if i == 1 then 1 else -1) * r[1] * 0.3
			local bn = B:bone("Antenna" .. i, "Body", sx, c[2] + r[2] * 0.9, 0)
			B:addRig("tentacles", { bone = bn, index = i, seg = 1 })
			B:limb({ sx, c[2] + r[2] * 0.85, 0.05 }, { sx * 1.5, c[2] + r[2] * 1.65, -0.15 }, 0.16, { col = col, mat = mat, bone = bn, pri = 1.7, role = "antenna", name = "Antenna" .. i }, 0.1)
			B:ball(0.42, at(sx * 1.55, c[2] + r[2] * 1.7, -0.17), { col = "glow", mat = "neon", glow = true, bone = bn, pri = 2.0, role = "gem", name = "AntennaTip" .. i, noCore = true })
		end
	end
	if f.floatEyes and detail >= 1 then
		for i = 1, (if detail >= 2 then 3 else 2) do
			local a = rad(-60 + i * 40)
			local p = onSurf(c, r, a, 0.7, 0.05)
			eyeball(B, 0.42 - i * 0.05, at(p[1], p[2] + 0.15, p[3]), "Body", 2.2 + i * 0.1, "FloatEye" .. i)
		end
	end
	if f.cell then
		B:ell(r[1] * 0.75, r[2] * 0.75, r[3] * 0.7, at(r[1] * 0.12, c[2] - r[2] * 0.08, c[3] + r[3] * 0.25), { col = "secondary", mat = "skin", pri = 1.5, role = "detail", name = "Nucleus", noCore = true })
		if detail >= 1 then
			-- dividing: a daughter lobe pinching off the side, with its own nucleus
			local d = { r[1] * 1.15, c[2] - r[2] * 0.25, c[3] + r[3] * 0.25 }
			B:ell(r[1] * 1.2, r[2] * 1.25, r[3] * 1.15, at(d[1], d[2], d[3]), { col = "primary", mat = "glass", tr = tr, pri = 1.6, role = "body", name = "Daughter" })
			B:ell(r[1] * 0.4, r[2] * 0.4, r[3] * 0.4, at(d[1] + 0.1, d[2], d[3]), { col = "secondary", mat = "skin", pri = 2.3, role = "detail", name = "Nucleus2", noCore = true })
		end
	elseif f.clear and detail >= 2 then
		B:ell(0.62, 0.62, 0.62, at(r[1] * 0.25, c[2] - r[2] * 0.15, c[3] + r[3] * 0.3), { col = "secondary", mat = "skin", pri = 3.0, role = "detail", name = "Nucleus", noCore = true })
	end
	if f.code and detail >= 1 then
		for i = 1, (if detail >= 2 then 4 else 2) do
			local a = rad(60 + i * 62)
			local p = onSurf(c, r, a, 0.15 + (i % 2) * 0.4, 0.18 + (i % 3) * 0.12)
			B:block(0.32, 0.32, 0.32, at(p[1], p[2], p[3], rad(i * 23), rad(i * 41), 0), { col = "glow", mat = "neon", glow = true, pri = 2.6 + i * 0.1, role = "gem", name = "Bit" .. i, noCore = true })
		end
	end
	if (f.bubbles or f.embers or f.frost or f.rainbow) and detail >= 2 then
		local n = if detail >= 3 then 5 else 3
		for i = 1, n do
			local a = rad(70 + i * 47)
			local p = onSurf(c, r, a, -0.1 + (i % 3) * 0.32, -0.06)
			local dd = (if f.embers then 0.2 else 0.34) * (1 + (i % 2) * 0.4)
			local o: any = { col = if f.embers then "flame" elseif f.rainbow then ({ "red", "gold", "leaf", "glass" })[(i % 4) + 1] else "secondary", mat = if f.embers then "neon" else "glass", glow = f.embers,
				pri = 2.8 + i * 0.1, role = "detail", name = "Fleck" .. i, noCore = true }
			if f.frost then
				o.col, o.mat = "white", "ice"
			end
			B:ball(dd, at(p[1], p[2], p[3]), o)
		end
	end
	if f.embers then
		B:emit("embers", nil, { socket = "core", rate = 10 })
	elseif f.bubbles then
		B:emit("bubbles", nil, { socket = "core", rate = 8 })
	end
	B:socket("core", at(c[1], c[2], c[3]), "Body")
	B:setRig("gait", if f.float then "float" else "hop")
	B:setRig("materialMotion", B.rig.materialMotion or "wobble")
end

-- SLUG / SEA SLUG ----------------------------------------------------------------------------------------------
-- The slug body on its own: Body (foot) + Mantle + Head + Tail, all in one sculpt. k scales x/y, kz the length.
local function slugBody(B: any, ctx: any, k: number, kz: number, o: any)
	local detail = ctx.detail
	local col, mat = o.col or "primary", o.mat or "skin"
	local function E(sx, sy, sz, x, y, z, oo)
		oo.col, oo.mat, oo.tr = oo.col or col, oo.mat or mat, o.tr
		return B:ell(sx * k, sy * k, sz * kz, at(x * k, y * k, z * kz), oo)
	end
	local body = E(1.5, 0.9, 4.0, 0, 0.45, 0.15, { pri = 1, role = "body", name = "Body" })
	local head = E(1.0, 0.9, 1.0, 0, 0.72, -1.5, { pri = 1.05, role = "body", name = "Head" })
	local members = { head }
	if not o.noMantle then
		table.insert(members, E(1.3, 1.0, 1.9, 0, 0.82, -0.35, { pri = 1.25, role = "body", name = "Mantle", col = o.mantleCol }))
	end
	if detail >= 1 then
		table.insert(members, E(0.85, 0.6, 2.0, 0, 0.32, 1.6, { pri = 1.3, role = "body", name = "Tail" }))
	end
	if o.sculpt ~= false then
		B:sculpt(body, "s_blob_slug", members)
	end
	return { c = { 0, 0.72 * k, -1.5 * kz }, r = { 0.5 * k, 0.45 * k, 0.5 * kz }, top = 1.32 * k, head = head }
end

-- Two stalks from the top of the head; eyes on the tips (garden slugs, snails) or plain rhinophores (sea slugs).
local function stalks(B: any, ctx: any, H: any, o: any)
	local c, r = H.c, H.r
	local len = r[2] * (o.len or 1.8)
	for _, side in { 1, -1 } do
		local nm = if side > 0 then "R" else "L"
		local base = { side * r[1] * 0.42, c[2] + r[2] * 0.72, c[3] - r[3] * 0.1 }
		local tip = { side * r[1] * (0.42 + (o.splay or 0.5)), base[2] + len, base[3] - len * (o.lean or 0.45) }
		local bn = B:bone("Stalk" .. nm, "Body", base[1], base[2], base[3])
		B:addRig("tentacles", { bone = bn, index = if side > 0 then 1 else 2, seg = 1 })
		B:limb(base, tip, r[1] * (o.w or 0.3), { col = o.col or "primary", mat = o.mat or "skin", bone = bn, pri = 1.08, role = "antenna", name = "Stalk" .. nm, pair = "stalks", depth = r[1] * (o.depth or o.w or 0.3), mesh = o.mesh }, 0.12)
		if o.eyes then
			local d = r[1] * 0.46
			local small = ctx.detail == 0
			local e = B:ball(d, at(tip[1], tip[2] + d * 0.15, tip[3] - d * 0.05), { col = if small then "pupil" else "eyeWhite", mat = if small then "glass" else "skin", bone = bn, pri = 1.1, role = "eye", name = "Eye" .. nm, pair = "eyes", needs = "stalks", noCore = true })
			if small then
				continue
			end
			B:ell(d * 0.56, d * 0.6, d * 0.34, at(tip[1] + side * d * 0.04, tip[2] + d * 0.15, tip[3] - d * 0.43), { col = "pupil", mat = "glass", bone = bn, pri = 1.12, role = "pupil", name = "Pupil" .. nm, pair = "pupils", needs = e.pair, noCore = true })
			if ctx.detail >= 3 then
				B:ball(d * 0.18, at(tip[1] + side * d * 0.1 + d * 0.08, tip[2] + d * 0.3, tip[3] - d * 0.58), { col = "shine", mat = "neon", bone = bn, pri = 3.4, role = "shine", name = "Shine" .. nm, noCore = true, needs = "pupils" })
			end
		elseif o.tipCol then
			B:ball(r[1] * (o.w or 0.3) * 1.05, at(tip[1], tip[2], tip[3]), { col = o.tipCol, mat = "skin", bone = bn, pri = 2.4, role = "detail", name = "StalkTip" .. nm, pair = "stalkTips" })
		end
	end
end

local function slugMouth(B: any, ctx: any, H: any)
	if ctx.detail >= 1 then
		local c, r = H.c, H.r
		local p = Face.place({ kind = "ellipsoid", c = c, r = r }, 0, -r[2] * 0.3, r[2] * 0.03)
		B:ell(r[1] * 0.55, r[2] * 0.1, r[2] * 0.14, p, { col = "mouth", mat = "skin", pri = 2.2, role = "mouth", name = "Mouth", noCore = true })
	end
end

local function buildSlug(B: any, ctx: any, id: string, hint: string)
	local t, detail = ctx.traits, ctx.detail
	local sea = has(id, "sea") or has(id, "nudibranch") or t.swims
	B.boneIndex.Body.pos = { 0, 0.5, 0 }
	if has(id, "cucumber") then
		-- lumpy sausage on tube feet, crown of feeding tentacles at the front, papillae along the back
		for i = 1, 3 do
			local z = -1.3 + (i - 1) * 1.3
			B:ell(1.7 - math.abs(i - 2) * 0.15, 1.35 - math.abs(i - 2) * 0.12, 1.9, at(0, 0.68, z), { col = "primary", mat = "skin", pri = 1 + (i - 1) * 0.03, role = "body", name = if i == 2 then "Body" else "Lobe" .. i })
		end
		local c, r = { 0, 0.72, -1.7 }, { 0.78, 0.62, 0.7 }
		eface(B, ctx, c, r, { d = 0.42, spacing = 0.3, y = 0.15, mouthY = -0.3, mouthW = 0.3 })
		local n = if detail >= 2 then 5 elseif detail >= 1 then 3 else 0
		for i = 1, n do
			local a = rad(-70 + (i - 1) * 140 / math.max(1, n - 1))
			B:limb({ sin(a) * 0.4, 0.72 + cos(a) * 0.35, -2.4 }, { sin(a) * 0.75, 0.72 + cos(a) * 0.75, -2.9 }, 0.2, { col = "secondary", mat = "skin", pri = 2.2 + i * 0.05, role = "tentacle", name = "Feeler" .. i }, 0.2)
		end
		for i = 1, (if detail >= 2 then 6 else 0) do
			local side = if i % 2 == 0 then 1 else -1
			local z = -0.9 + math.floor((i - 1) / 2) * 1.0
			B:limb({ side * 0.45, 1.25, z }, { side * 0.62, 1.6, z + 0.1 }, 0.26, { col = "secondary", mat = "skin", pri = 3 + i * 0.05, role = "spike", name = "Papilla" .. i }, 0.2)
		end
		B:socket("core", at(0, 0.7, 0), "Body")
		B:setRig("gait", "inch")
		return
	end
	local k, kz = 1, 1
	local o: any = {}
	if has(id, "bunny") then
		o.mat = "fur"
	elseif has(id, "pig") then
		o.tr, o.noMantle = 0.18, true
		k = 1.25
	elseif has(id, "hare") then
		k = 1.15
	elseif has(id, "banana") then
		kz = 1.1
	end
	local H = slugBody(B, ctx, k, kz, o)
	local c, r = H.c, H.r
	if sea then
		-- rhinophores (scent horns) on top; small eyes on the face
		local bunny = has(id, "bunny")
		stalks(B, ctx, H, { len = if bunny then 2.1 else 1.4, w = if bunny then 0.42 else 0.26, splay = if bunny then 0.55 else 0.4, lean = 0.2, col = if bunny then "black" else "secondary", depth = if bunny then 0.28 else nil, tipCol = if not bunny and detail >= 2 then "white" else nil })
		eface(B, ctx, c, r, { d = r[1] * 0.42, spacing = r[1] * 0.42, y = r[2] * 0.12, mouthY = -r[2] * 0.36, mouthW = r[1] * 0.42, noBrows = true })
	else
		stalks(B, ctx, H, { len = 2.0, w = 0.24, eyes = true, col = "primary" })
		if detail >= 2 then
			-- lower feelers
			for _, side in { 1, -1 } do
				B:limb({ side * r[1] * 0.45, c[2] - r[2] * 0.35, c[3] - r[3] * 0.6 }, { side * r[1] * 0.9, c[2] - r[2] * 0.6, c[3] - r[3] * 1.3 }, r[1] * 0.18, { col = "primary", mat = "skin", pri = 3.0, role = "antenna", name = "Feeler" .. (if side > 0 then "R" else "L") }, 0.1)
			end
		end
		slugMouth(B, ctx, H)
	end
	if has(id, "lettuce") and detail >= 1 then
		-- ruffled parapodia: wavy frills along both flanks, each a little tilted so none lie flush
		local n = if detail >= 2 then 3 else 2
		for i = 1, n do
			local z = -0.5 + (i - 1) * 1.05
			B:mell(0.7, 0.18, 1.15, at(0.72, 0.95 + (i % 2) * 0.12, z, rad(8 * i), rad(-6 + i * 5), rad(-38 - (i % 2) * 10)), { col = if i % 2 == 0 then "light" else "primary", mat = "leaf", pri = 1.6 + i * 0.2, role = "fin", name = "Frill" .. i .. "#" })
		end
	elseif has(id, "hare") and detail >= 1 then
		-- parapodial flaps folded up over the back, and ear-like rhinophores already on
		B:mell(0.22, 0.95, 1.9, at(0.55, 1.15, 0.15, rad(6), 0, rad(-24)), { col = "secondary", mat = "skin", pri = 1.6, role = "fin", name = "Flap#" })
	elseif has(hint, "dragon") or has(id, "blue sea slug") then
		-- glaucus: three pairs of finger fans spread sideways
		local n = if detail >= 2 then 3 elseif detail >= 1 then 2 else 1
		for i = 1, n do
			local z = -0.6 + (i - 1) * 0.9
			for j = 1, (if detail >= 2 then 3 else 2) do
				local a = rad(-30 + j * 20)
				B:mlimb({ 0.6, 0.55, z }, { 0.6 + cos(a) * 1.1, 0.5 + sin(a) * 0.4 + 0.2, z + sin(a) * 0.5 }, 0.16, { col = if j == 2 then "secondary" else "primary", mat = "skin", pri = 1.7 + i * 0.2 + j * 0.05, role = "fin", name = "Finger" .. i .. j .. "#" }, 0.15)
			end
		end
	elseif sea and has(id, "sea slug") and detail >= 1 then
		-- nudibranch cerata: two rows of tapering spikes along the back, tipped in the second colour
		local n = if detail >= 2 then 3 else 2
		for i = 1, n do
			local z = -0.55 + (i - 1) * 0.75
			B:mlimb({ 0.32, 1.1, z }, { 0.62, 1.75, z + 0.15 }, 0.3, { col = "secondary", mat = "skin", pri = 1.6 + i * 0.25, role = "spike", name = "Cerata" .. i .. "#" }, 0.15)
		end
		B:ell(0.5, 0.18, 1.4, at(0, 1.32, 0.0), { col = "secondary", mat = "skin", pri = 2.5, role = "detail", name = "Stripe" })
	elseif has(id, "bunny") and detail >= 2 then
		for i = 1, 3 do
			local a = rad(80 + i * 55)
			local p = onSurf({ 0, 0.82, -0.35 }, { 0.65, 0.5, 0.95 }, a, 0.4, -0.04)
			B:ball(0.16, at(p[1], p[2], p[3]), { col = "secondary", mat = "skin", pri = 3 + i * 0.1, role = "detail", name = "Speck" .. i, noCore = true })
		end
	elseif has(id, "pig") and detail >= 1 then
		-- tube feet underneath and the dorsal "antennae" papillae
		for i = 1, (if detail >= 2 then 3 else 2) do
			local z = -1.0 + (i - 1) * 1.0
			B:mlimb({ 0.7, 0.4, z }, { 1.05, 0.05, z }, 0.28, { col = "primary", mat = "skin", tr = 0.18, pri = 1.6 + i * 0.2, role = "limb", name = "TubeFoot" .. i .. "#" }, 0.2)
		end
	elseif has(id, "banana") and detail >= 2 then
		for i = 1, 3 do
			local p = onSurf({ 0, 0.82, -0.35 }, { 0.65, 0.5, 0.95 }, rad(100 + i * 70), 0.3, -0.03)
			B:ell(0.22, 0.16, 0.3, at(p[1], p[2], p[3]), { col = "darker", mat = "skin", pri = 3 + i * 0.1, role = "detail", name = "Spot" .. i, noCore = true })
		end
	end
	B:socket("core", at(0, 0.6, -0.3), "Body")
	B:setRig("gait", "inch")
end

-- SNAIL -------------------------------------------------------------------------------------------------------
local function buildSnail(B: any, ctx: any, id: string, hint: string)
	local detail = ctx.detail
	local spire = has(id, "conch") or has(id, "whelk") or has(id, "african") or has(id, "cone") or has(hint, "pointed") or has(hint, "conical")
	local wideFoot = has(id, "moon snail") or has(hint, "huge foot")
	B.boneIndex.Body.pos = { 0, 0.5, 0 }
	local H = slugBody(B, ctx, if wideFoot then 1.0 else 0.85, if wideFoot then 1.05 else 0.9, { col = "belly", noMantle = true })
	stalks(B, ctx, H, { len = 2.2, w = 0.26, eyes = true, col = "belly" })
	slugMouth(B, ctx, H)
	if spire then
		local cone = has(id, "cone")
		local sz = if cone then { 1.5, 1.4, 2.8 } else { 1.7, 1.6, 3.0 }
		local cpos = { 0, 1.35, 0.55 }
		local shell = B:ell(sz[1], sz[2], sz[3], at(cpos[1], cpos[2], cpos[3]), { col = "primary", mat = "hard", pri = 1.02, role = "body", name = "Shell" })
		local mem = {}
		if detail >= 1 then
			table.insert(mem, B:limb({ 0, 1.6, 1.2 }, { 0, 2.05, 2.25 }, 0.8, { col = "primary", mat = "hard", pri = 1.5, role = "body", name = "Spire" }, 0.1))
		end
		B:sculpt(shell, "s_blob_spire", mem)
		if has(id, "conch") or has(hint, "lip") then
			B:ell(0.55, 0.45, 1.2, at(0.4, 1.0, 0.25), { col = "inner", mat = "glass", pri = 1.8, role = "detail", name = "Lip" })
		end
		if cone and detail >= 1 then
			-- the venom harpoon (proboscis) reaching forward
			B:limb({ 0, 0.55, -1.75 }, { 0, 0.45, -2.6 }, 0.14, { col = "secondary", mat = "hard", pri = 2.0, role = "spike", name = "Harpoon" }, 0.1)
		end
		if detail >= 2 then
			for i = 1, (if cone then 4 else 2) do
				local p = onSurf(cpos, { sz[1] / 2, sz[2] / 2, sz[3] / 2 }, rad(110 + i * 50), 0.1 + (i % 2) * 0.35, -0.03)
				B:ell(0.36, 0.26, 0.42, at(p[1], p[2], p[3]), { col = "secondary", mat = "hard", pri = 3 + i * 0.1, role = "detail", name = "Mark" .. i, noCore = true })
			end
		end
	else
		local s = if has(id, "periwinkle") then 0.9 else 1
		local cpos = { 0, 1.62 * s, 0.35 }
		local shell = B:ell(1.6 * s, 1.9 * s, 1.9 * s, at(cpos[1], cpos[2], cpos[3]), { col = "primary", mat = "hard", pri = 1.02, role = "body", name = "Shell" })
		local mem = {}
		if detail >= 1 then
			table.insert(mem, B:ell(0.8 * s, 0.9 * s, 0.9 * s, at(-0.5 * s, cpos[2] + 0.05, cpos[3] - 0.05), { col = "secondary", mat = "hard", pri = 1.6, role = "body", name = "Whorl" }))
		end
		B:sculpt(shell, "s_blob_coil", mem)
	end
	B:socket("core", at(0, 1.2, 0.3), "Body")
	B:setRig("gait", "inch")
end

-- BIVALVE -----------------------------------------------------------------------------------------------------
local function buildBivalve(B: any, ctx: any, id: string, hint: string)
	local t, detail = ctx.traits, ctx.detail
	local mussel = has(id, "mussel") or has(hint, "long shells")
	local giant = has(id, "giant")
	local scallop = has(id, "scallop") or has(hint, "fan shell")
	local w, h, l = 3.0, 0.9, 2.5
	if mussel then
		w, h, l = 1.9, 0.85, 3.2
	elseif scallop then
		w, h, l = 3.0, 0.75, 2.7
	end
	local open = rad(if giant then 24 elseif mussel then 16 else 30)
	local hingeY, hingeZ = 0.62, l * 0.48
	B.boneIndex.Body.pos = { 0, hingeY, 0 }
	B:bone("Lid", "Body", 0, hingeY, hingeZ)
	local cy = hingeY - 0.2 * (h / 0.9)
	-- the valve sculpt is a cap with its rim at -0.2 (lead frame, studs at h = 0.9): the lower valve is the cap
	-- upside down, the upper one hinged at the back and opened
	local lower = B:ell(w, h, l, at(0, hingeY - 0.2 * h / 0.9 - 0.02 + 0.0, 0, 0, 0, math.pi), { col = "primary", mat = "hard", pri = 1, role = "body", name = "Valve" })
	local _ = cy
	B:sculpt(lower, "s_blob_valve")
	local upper = B:ell(w, h, l, Geom.mul(at(0, hingeY, hingeZ, open, 0, 0), at(0, 0.2 * h / 0.9 + 0.02, -hingeZ)), { col = "primary", mat = "hard", bone = "Lid", pri = 1.02, role = "body", name = "Lid" })
	B:sculpt(upper, "s_blob_valve")
	B:addRig("tentacles", { bone = "Lid", index = 1, seg = 1 })
	-- flesh (mantle) bulging out of the gap: carries the face
	local fc, fr = { 0, hingeY + 0.12, -l * 0.08 }, { w * 0.4, 0.42, l * 0.38 }
	local flesh = B:ell(fr[1] * 2, fr[2] * 2, fr[3] * 2, at(fc[1], fc[2], fc[3]), { col = if giant then "secondary" else "inner", mat = "skin", pri = 1.05, role = "body", name = "Flesh" })
	local _f = flesh
	if has(id, "geoduck") or has(hint, "long neck") then
		-- the siphon neck: a long wrinkled trunk rising from the front, with the face at its tip
		local nb = B:bone("Neck", "Body", 0, hingeY, -l * 0.3)
		B:addRig("tentacles", { bone = nb, index = 2, seg = 1 })
		local segs = if detail >= 1 then 2 else 1
		local p0, p1 = { 0, hingeY, -l * 0.3 }, { 0, hingeY + 2.6, -l * 0.62 }
		local prev = p0
		for i = 1, segs do
			local q = { 0, p0[2] + (p1[2] - p0[2]) * i / segs, p0[3] + (p1[3] - p0[3]) * i / segs }
			B:limb(prev, q, 0.95 - i * 0.08, { col = "secondary", mat = "skin", bone = nb, pri = 1.08 + i * 0.05, role = "body", name = "Siphon" .. i }, 0.2)
			prev = q
		end
		local hc, hr = { 0, p1[2] + 0.15, p1[3] }, { 0.48, 0.42, 0.45 }
		B:ell(hr[1] * 2, hr[2] * 2, hr[3] * 2, at(hc[1], hc[2], hc[3]), { col = "secondary", mat = "skin", bone = nb, pri = 1.09, role = "head", name = "SiphonTip" })
		eface(B, ctx, hc, hr, { bone = nb, d = 0.36, spacing = 0.2, y = 0.08, mouthY = -0.2, mouthW = 0.3, noBrows = true })
	else
		eface(B, ctx, fc, fr, { d = math.min(0.62, w * 0.18), spacing = fr[1] * 0.42, y = fr[2] * 0.32, mouthY = -fr[2] * 0.25, mouthW = fr[1] * 0.4, noBrows = true })
	end
	if (has(id, "oyster") or has(hint, "pearl")) and detail >= 1 then
		B:ball(0.62, at(w * 0.24, fc[2] + 0.28, fc[3] - fr[3] * 0.62), { col = "white", mat = "glass", pri = 1.5, role = "gem", name = "Pearl" })
	end
	if scallop and detail >= 1 then
		-- hinge ears, and the row of little blue eyes along the mantle edge
		B:mwedge(0.3, 0.55, 0.7, at(w * 0.28, hingeY, hingeZ + 0.05, 0, 0, rad(-90)), { col = "primary", mat = "hard", pri = 1.9, role = "detail", name = "Ear#" })
		if detail >= 2 then
			for i = 1, 3 do
				local a = rad(28 + i * 22)
				B:mball(0.17, at(sin(a) * w * 0.44, hingeY + 0.02, -cos(a) * l * 0.42), { col = "glass", mat = "neon", glow = true, pri = 3 + i * 0.1, role = "gem", name = "Ocellus" .. i .. "#", noCore = true })
			end
		end
	end
	if giant and detail >= 2 then
		for i = 1, 4 do
			local x = (i - 2.5) * w * 0.17
			B:ball(0.2, at(x, fc[2] + fr[2] * 0.8, fc[3] + (i % 2) * 0.3), { col = "glow", mat = "neon", glow = true, pri = 3 + i * 0.1, role = "gem", name = "Glint" .. i, noCore = true })
		end
	end
	if mussel and detail >= 2 then
		for i = 1, 3 do
			B:limb({ 0, hingeY - 0.2, -l * 0.1 + i * 0.2 }, { (i - 2) * 0.5, 0.03, -l * 0.25 + i * 0.25 }, 0.07, { col = "wood", mat = "cloth", pri = 3.5 + i * 0.1, role = "detail", name = "Byssus" .. i }, 0.05)
		end
	end
	if has(id, "shipworm") then
		-- a long pale worm trailing out behind the tiny drilling shell
		local prev = { 0, hingeY, hingeZ }
		for i = 1, (if detail >= 1 then 3 else 2) do
			local q = { sin(i * 1.3) * 0.5, 0.35 + i * 0.1, hingeZ + i * 1.4 }
			B:limb(prev, q, 0.75 - i * 0.12, { col = "secondary", mat = "skin", pri = 1.1 + i * 0.1, role = "tail", name = "Worm" .. i }, 0.2)
			prev = q
		end
	end
	B:socket("core", at(fc[1], fc[2], fc[3]), "Body")
	B:setRig("gait", "hop")
end

-- CAP SHELLS (abalone, limpet, chiton, cowrie) --------------------------------------------------------------------
local function buildCap(B: any, ctx: any, id: string, hint: string)
	local detail = ctx.detail
	B.boneIndex.Body.pos = { 0, 0.5, 0 }
	local foot = { 0, 0.3, 0 }
	if has(id, "limpet") then
		B:ell(3.4, 1.0, 3.2, at(0, 0.45, 0.1), { col = "darkStone", mat = "stone", pri = 1.1, role = "body", name = "Boulder" })
		local sc = B:ell(2.6, 1.3, 2.4, at(0, 1.3, 0), { col = "primary", mat = "hard", pri = 1, role = "body", name = "Shell" })
		local _ = sc
		B:ell(1.2, 1.0, 1.1, at(0, 1.95, 0.12), { col = "secondary", mat = "hard", pri = 1.3, role = "body", name = "Apex" })
		eface(B, ctx, { 0, 1.15, 0 }, { 1.3, 0.65, 1.2 }, { d = 0.5, spacing = 0.42, y = 0.02, mouthY = -0.32, mouthW = 0.4, noBrows = true })
		if detail >= 2 then
			for i = 1, 4 do
				local a = rad(i * 90 - 45)
				B:ell(0.22, 1.0, 0.5, at(sin(a) * 1.0, 1.35, -cos(a) * 0.92, -cos(a) * rad(35), 0, sin(a) * rad(35)), { col = "secondary", mat = "hard", pri = 3 + i * 0.1, role = "detail", name = "Ray" .. i })
			end
		end
		B:socket("core", at(0, 1.3, 0), "Body")
		B:setRig("gait", "inch")
		return
	end
	if has(id, "chiton") then
		B:ell(2.2, 0.6, 3.6, at(foot[1], foot[2], foot[3]), { col = "secondary", mat = "skin", pri = 1, role = "body", name = "Body" })
		local n = if detail >= 2 then 8 elseif detail >= 1 then 6 else 4
		for i = 1, n do
			local z = -1.35 + (i - 1) * 2.7 / (n - 1)
			local wv = 1.75 - math.abs(i - (n + 1) / 2) * 0.12
			B:ell(wv, 0.5, 3.2 / n * 1.35, at(0, 0.62, z, rad(-12), 0, 0), { col = if i % 2 == 0 then "primary" else "darker", mat = "hard", pri = 1.1 + i * 0.02, role = "body", name = "Plate" .. i })
		end
		eface(B, ctx, { 0, 0.4, -1.55 }, { 0.6, 0.32, 0.4 }, { d = 0.32, spacing = 0.26, y = 0.0, mouthY = -0.15, mouthW = 0.24, noBrows = true, noMouth = detail < 2 })
		B:socket("core", at(0, 0.5, 0), "Body")
		B:setRig("gait", "inch")
		return
	end
	-- abalone / cowrie: a low foot with eye stalks and one big shell on top
	local H = slugBody(B, ctx, 1.0, 0.9, { col = "secondary", noMantle = true, sculpt = false })
	stalks(B, ctx, H, { len = 1.8, w = 0.24, eyes = true, col = "secondary" })
	if has(id, "cowrie") then
		B:ell(2.0, 1.55, 3.3, at(0, 1.1, 0.25), { col = "primary", mat = "glass", pri = 1, role = "body", name = "Shell" })
		if detail >= 1 then
			for i = 1, (if detail >= 2 then 5 else 3) do
				local p = onSurf({ 0, 1.1, 0.25 }, { 1.0, 0.775, 1.65 }, rad(40 + i * 56), 0.35 + (i % 2) * 0.3, -0.03)
				B:ell(0.34, 0.2, 0.34, at(p[1], p[2], p[3]), { col = "secondary", mat = "glass", pri = 3 + i * 0.1, role = "detail", name = "Spot" .. i, noCore = true })
			end
		end
	else
		-- abalone: flat ear-shaped shell (the valve sculpt, skewed) with its row of breathing holes and a rainbow lip
		local shell = B:ell(2.6, 0.75, 3.4, at(0, 0.92, 0.2, 0, rad(12), 0), { col = "primary", mat = "hard", pri = 1, role = "body", name = "Shell" })
		B:sculpt(shell, "s_blob_valve")
		B:ell(2.3, 0.4, 3.0, at(0.05, 0.86, 0.22, 0, rad(12), 0), { col = "glow", mat = "foil", pri = 1.4, role = "detail", name = "Nacre" })
		if detail >= 2 then
			for i = 1, 4 do
				local z = -0.9 + i * 0.5
				B:ell(0.2, 0.12, 0.2, at(0.92 + z * 0.2, 1.22 - math.abs(z) * 0.05, z), { col = "black", mat = "hard", pri = 3 + i * 0.1, role = "detail", name = "Pore" .. i, noCore = true })
			end
		end
	end
	slugMouth(B, ctx, H)
	B:socket("core", at(0, 0.9, 0), "Body")
	B:setRig("gait", "inch")
end

-- JELLYFISH ---------------------------------------------------------------------------------------------------
local function buildJelly(B: any, ctx: any, id: string, hint: string)
	local t, detail = ctx.traits, ctx.detail
	local robot = has(id, "robot") or t.robot
	local box = has(id, "box")
	local egg = has(id, "fried egg")
	local cass = has(id, "cassiopea") or has(hint, "upside down")
	local mow = has(id, "man o war") or has(hint, "float sail")
	local comb = has(id, "comb") or has(id, "gooseberry") or has(hint, "cilia")
	local lion = has(id, "lion")
	local glowy = has(id, "space") or has(id, "giant") or t.element == "Light"
	local tr = if robot then nil else 0.22
	local mat = if robot then "metal" else "glass"
	local H = if cass then 0.6 elseif comb then 2.0 else 4.1
	B.boneIndex.Body.pos = { 0, H, 0 }
	local c, r = { 0, H, 0 }, { 1.5, 1.1, 1.5 }
	if comb then
		r = { 1.15, 1.45, 1.15 }
		local body = B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "glass", tr = 0.35, pri = 1, role = "body", name = "Body" })
		local _ = body
		eface(B, ctx, c, r, { d = 0.55, spacing = 0.42, y = 0.2, noBrows = true })
		local n = if detail >= 2 then 6 elseif detail >= 1 then 4 else 2
		local cols = { "red", "gold", "leaf", "glow", "glass", "blush" }
		for i = 1, n do
			local a = rad(55 + (i - 1) * 250 / math.max(1, n - 1))
			local p = onSurf(c, r, a, 0, -0.05)
			B:ell(0.16, r[2] * 1.7, 0.16, at(p[1], p[2], p[3], 0, a, 0), { col = cols[(i - 1) % 6 + 1], mat = "neon", glow = true, pri = 1.6 + i * 0.1, role = "gem", name = "Comb" .. i, noCore = true })
		end
		if has(id, "gooseberry") or detail >= 2 then
			for i, side in { 1, -1 } do
				tentacle(B, i, { side * r[1] * 0.8, c[2] - r[2] * 0.2, 0.2 }, { side * 2.4, 0.15, 0.6 }, 0.14, if detail >= 2 then 2 else 1, { col = "secondary", pri = 2.4, curl = 0.6 })
			end
		end
		B:socket("core", at(c[1], c[2], c[3]), "Body")
		B:setRig("gait", "float")
		return
	end
	if mow then
		-- the float: an inflated translucent sac with a crested sail, long trailing tentacles below
		local fr = { 1.2, 0.9, 1.9 }
		B:ell(fr[1] * 2, fr[2] * 2, fr[3] * 2, at(0, H, 0, rad(-8), 0, 0), { col = "primary", mat = "glass", tr = 0.3, pri = 1, role = "body", name = "Float" })
		B:ell(0.25, 1.3, 3.0, at(0, H + 1.0, 0.1, rad(-8), 0, 0), { col = "secondary", mat = "glass", tr = 0.2, pri = 1.3, role = "fin", name = "Sail" })
		eface(B, ctx, { 0, H, 0 }, fr, { d = 0.6, spacing = 0.48, y = 0.05, noBrows = true })
		local n = if detail >= 2 then 6 elseif detail >= 1 then 4 else 3
		for i = 1, n do
			local x = (i - (n + 1) / 2) * 0.45
			tentacle(B, i, { x, H - 0.75, (i % 2) * 0.5 - 0.1 }, { x * 1.3, 0.1, 0.4 + (i % 3) * 0.3 }, 0.18, if detail >= 2 then 2 else 1, { col = "primary", pri = 1.8, curl = 0.3 })
		end
		B:socket("core", at(0, H, 0), "Body")
		B:setRig("gait", "float")
		return
	end
	local bell
	if box then
		bell = B:block(2.6, 2.3, 2.6, at(c[1], c[2], c[3]), { col = "primary", mat = mat, tr = tr, pri = 1, role = "body", name = "Bell" })
		r = { 1.3, 1.15, 1.3 }
	elseif egg then
		r = { 1.7, 0.6, 1.7 }
		bell = B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "glass", tr = 0.1, pri = 1, role = "body", name = "Bell" })
		B:sculpt(bell, "s_blob_bell")
	elseif cass then
		-- lying upside down on the sand: the bell is an upturned saucer, oral arms bloom upward
		r = { 1.6, 0.55, 1.6 }
		bell = B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3], 0, 0, math.pi), { col = "primary", mat = "glass", tr = 0.1, pri = 1, role = "body", name = "Bell" })
		B:sculpt(bell, "s_blob_bell")
	else
		if lion then
			r = { 1.7, 1.15, 1.7 }
		end
		bell = B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = mat, tr = tr, pri = 1, role = "body", name = "Bell" })
		B:sculpt(bell, "s_blob_bell")
	end
	local _ = bell
	-- face: on the yolk for the fried egg, on the bell otherwise
	if egg then
		local yc, yr = { 0, H + 0.45, -0.1 }, { 0.8, 0.5, 0.8 }
		B:ell(yr[1] * 2, yr[2] * 2, yr[3] * 2, at(yc[1], yc[2], yc[3]), { col = "secondary", mat = "glass", pri = 1.05, role = "body", name = "Yolk" })
		eface(B, ctx, yc, yr, { d = 0.4, spacing = 0.3, y = 0.08, noBrows = true })
	elseif cass then
		eface(B, ctx, c, r, { d = 0.42, spacing = 0.5, y = 0.0, mouthY = -0.2, mouthW = 0.5, noBrows = true })
	else
		eface(B, ctx, c, r, { d = r[1] * 0.38, spacing = r[1] * 0.36, y = r[2] * 0.12, kind = if robot then "robot" else nil, noBrows = not robot })
	end
	-- inner organs read through the clear bell
	if has(id, "moon") and detail >= 1 then
		for i = 1, (if detail >= 2 then 4 else 2) do
			local a = rad(45 + i * 90)
			B:ell(0.55, 0.14, 0.55, at(sin(a) * 0.45, H + 0.42, cos(a) * 0.45 + 0.2, 0, a, 0), { col = "inner", mat = "skin", pri = 2.0 + i * 0.1, role = "detail", name = "Ring" .. i, noCore = true })
		end
	elseif has(id, "immortal") then
		B:ball(0.9, at(0, H - 0.05, 0.25), { col = "red", mat = "skin", pri = 1.3, role = "detail", name = "Heart", noCore = true })
	elseif glowy and detail >= 1 then
		B:ell(1.4, 0.8, 1.4, at(0, H + 0.1, 0.25), { col = "glow", mat = "neon", glow = true, pri = 1.8, role = "core", name = "Glow", noCore = true })
	end
	if robot and detail >= 2 then
		for i = 1, 4 do
			local a = rad(i * 90 - 45)
			B:ball(0.22, at(sin(a) * r[1] * 0.98, H - 0.2, -cos(a) * r[3] * 0.98), { col = "glow", mat = "neon", glow = true, pri = 3 + i * 0.1, role = "gem", name = "Led" .. i, noCore = true })
		end
	end
	-- tentacles round the rim (or in four corner bundles for the box jelly)
	local n = if detail >= 3 then 10 elseif detail >= 2 then 8 elseif detail >= 1 then 6 else 4
	if lion then
		n += 2
	end
	local segs = if detail >= 2 then 2 else 1
	if not cass then
		local rimY = H - (if egg then 0.3 elseif box then 1.05 else 0.45)
		for i = 1, n do
			local a = rad(22 + (i - 1) * 360 / n)
			local rr = if box then 1.25 else r[1] * 0.86
			if box then
				local corner = (i - 1) % 4
				a = rad(45 + corner * 90) + (math.floor((i - 1) / 4) - 0.5) * 0.25
				rr = 1.55
			end
			local p0 = { sin(a) * rr, rimY, -cos(a) * rr }
			local p1 = { sin(a) * rr * 1.25, if egg then H - 1.8 else 0.15 + (i % 3) * 0.25, -cos(a) * rr * 1.25 + 0.4 }
			tentacle(B, i, p0, p1, if lion then 0.32 else 0.15, segs, { col = if robot then "rubber" elseif lion then "secondary" else "primary", mat = if robot then "rubber" else "skin", tr = if robot then nil else 0.15, pri = 1.7 + i * 0.03, curl = 0.3 })
		end
	end
	-- oral arms: ruffled ribbons from the centre (blooming upward on the cassiopea)
	if detail >= 1 and not box and not robot then
		local m = if detail >= 2 then 4 else 2
		for i = 1, m do
			local a = rad(45 + i * 360 / m)
			if cass then
				B:ell(0.9, 0.7, 0.9, at(sin(a) * 0.7, H + 0.62, -cos(a) * 0.7), { col = "secondary", mat = "leaf", pri = 1.4 + i * 0.1, role = "detail", name = "Bloom" .. i })
			else
				local len = if egg then 1.6 else 2.3
				B:limb({ sin(a) * 0.35, H - 0.4, -cos(a) * 0.35 + 0.1 }, { sin(a) * 0.65, H - 0.4 - len, -cos(a) * 0.65 + 0.3 }, 0.5, { col = if egg then "inner" else "secondary", mat = "skin", tr = 0.1, pri = 1.6 + i * 0.1, role = "tentacle", name = "OralArm" .. i, depth = 0.2 }, 0.15)
			end
		end
	end
	if glowy then
		B:emit("glints", nil, { socket = "core", rate = 8 })
	end
	B:socket("core", at(0, H, 0), "Body")
	B:setRig("gait", if cass then "sway" else "float")
end

-- SEA STARS ---------------------------------------------------------------------------------------------------
local function buildStar(B: any, ctx: any, id: string, hint: string)
	local detail = ctx.detail
	local brittle = has(id, "brittle") or has(hint, "whippy")
	local thorns = has(id, "thorns") or has(hint, "many%-armed")
	if has(id, "sand dollar") or has(hint, "flat round disc") then
		-- a coin standing on edge: flat disc, five-petal flower on the face side
		local C = { 0, 1.65, 0 }
		B:cyl(0.42, 3.2, at(C[1], C[2], C[3], 0, rad(90), 0), { col = "primary", mat = "stone", pri = 1, role = "body", name = "Disc" })
		local np = if detail >= 1 then 5 else 0
		for i = 1, np do
			local a = rad(i * 72)
			B:ell(0.24, 0.62, 0.12, at(C[1] + sin(a) * 0.55, C[2] + 0.3 + cos(a) * 0.55, -0.22, 0, 0, -a), { col = "secondary", mat = "stone", pri = 2.0 + i * 0.1, role = "detail", name = "Petal" .. i })
		end
		Face.build(B, { face = { kind = "flat", cf = at(C[1], C[2] - 0.35, -0.21) }, bone = "Body", mood = ctx.result.mood, detail = math.max(1, detail), kind = "cute",
			spacing = 0.42, y = 0.05, d = 0.42, mouthY = -0.42, mouthW = 0.45, forceMouth = true, noBrows = true })
		B:socket("core", at(C[1], C[2], C[3]), "Body")
		B:setRig("gait", "roll")
		return
	end
	local n = if thorns then (if detail >= 2 then 10 elseif detail >= 1 then 8 else 6) else 5
	local L = if brittle then 2.4 else 2.0
	local Cy = L * cos(rad(36)) + (if brittle then 0.1 else 0.18)
	if thorns then
		Cy = L * 0.92
	end
	local C = { 0, Cy, 0 }
	B.boneIndex.Body.pos = { C[1], C[2], C[3] }
	local dr = if brittle then { 0.6, 0.6, 0.35 } elseif thorns then { 1.0, 1.0, 0.45 } else { 0.85, 0.85, 0.4 }
	local disc = B:ell(dr[1] * 2, dr[2] * 2, dr[3] * 2, at(C[1], C[2], C[3]), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Disc" })
	local arms = {}
	for i = 1, n do
		local a = rad(90 + (i - 1) * 360 / n)
		local d = { cos(a), sin(a) }
		local w = if brittle then 0.32 elseif thorns then 0.6 else 0.95
		local bn = B:bone("Arm" .. i, "Body", C[1] + d[1] * dr[1] * 0.6, C[2] + d[2] * dr[1] * 0.6, C[3])
		if brittle then
			-- whippy arms in two segments, the outer one curling
			local m = { C[1] + d[1] * L * 0.55, C[2] + d[2] * L * 0.55, C[3] }
			local curl = (if i % 2 == 0 then 1 else -1) * 0.5
			local e = { m[1] + (d[1] * cos(curl) - d[2] * sin(curl)) * L * 0.5, m[2] + (d[1] * sin(curl) + d[2] * cos(curl)) * L * 0.5, C[3] }
			e[2] = math.max(e[2], 0.12)
			B:limb({ C[1] + d[1] * 0.3, C[2] + d[2] * 0.3, C[3] }, m, w, { col = "primary", mat = "skin", bone = bn, pri = 1.1 + i * 0.02, role = "limb", name = "Arm" .. i, depth = w * 0.8 }, 0.12)
			if detail >= 1 then
				local b2 = B:bone("ArmTip" .. i, bn, m[1], m[2], m[3])
				B:addRig("tentacles", { bone = b2, index = i, seg = 2 })
				B:limb(m, e, w * 0.7, { col = if i % 2 == 0 then "secondary" else "primary", mat = "skin", bone = b2, pri = 1.6 + i * 0.03, role = "limb", name = "ArmTip" .. i, trail = i <= 2 }, 0.12)
			end
			B:addRig("tentacles", { bone = bn, index = i, seg = 1 })
		else
			local len = if thorns then L * 0.95 else L
			local mid = { C[1] + d[1] * len * 0.5, C[2] + d[2] * len * 0.5, C[3] }
			local arm = B:part({ shape = "Ellipsoid", size = { w, len * 1.12, w * 0.62 }, cf = at(mid[1], mid[2], mid[3], 0, 0, a - math.pi / 2), col = "primary", mat = "skin", bone = bn,
				pri = 1.05 + i * 0.01, role = "limb", name = "Arm" .. i, mesh = false })
			table.insert(arms, arm)
			if thorns and detail >= 1 and i % 2 == 0 then
				B:limb({ mid[1], mid[2], mid[3] - 0.15 }, { mid[1] + d[1] * 0.2, mid[2] + d[2] * 0.2, mid[3] - 0.75 }, 0.16, { col = "secondary", mat = "hard", bone = bn, pri = 2.2 + i * 0.05, role = "spike", name = "Thorn" .. i }, 0.1)
			end
		end
		-- the two lower arms are the legs, the side ones wave
		local deg = (90 + (i - 1) * 360 / n) % 360
		if deg > 200 and deg < 340 then
			B:addRig("legs", { hip = bn, side = if deg < 270 then -1 else 1, phase = if deg < 270 then 0 else 0.5, len = Cy })
		elseif deg > 100 and deg < 200 or deg > 340 or deg < 80 then
			B:addRig("arms", { arm = bn, side = if deg > 100 and deg < 200 then -1 else 1 })
		end
	end
	if not brittle and not thorns then
		B:sculpt(disc, "s_blob_star", arms)
		if detail >= 2 then
			for i = 1, 5 do
				local a = rad(90 + (i - 1) * 72)
				B:ball(0.22, at(C[1] + cos(a) * 1.15, C[2] + sin(a) * 1.15, C[3] - 0.27), { col = "secondary", mat = "skin", pri = 3.2 + i * 0.05, role = "detail", name = "Wart" .. i, noCore = true })
			end
		end
	end
	eface(B, ctx, C, dr, { d = dr[1] * 0.5, spacing = dr[1] * 0.36, y = dr[2] * 0.12, mouthY = -dr[2] * 0.36, mouthW = dr[1] * 0.5, fierce = thorns })
	B:socket("core", at(C[1], C[2], C[3]), "Body")
	B:setRig("gait", "waddle")
end

-- SEA URCHIN --------------------------------------------------------------------------------------------------
local function buildUrchin(B: any, ctx: any, id: string, hint: string)
	local detail = ctx.detail
	local c = { 0, 1.35, 0 }
	B.boneIndex.Body.pos = { 0, 1.35, 0 }
	local core = B:ball(2.4, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Core" })
	local spines = {}
	local n = if detail >= 2 then 10 elseif detail >= 1 then 7 else 4
	for i = 1, n do
		-- spread over the back and sides, clear of the face
		local a = rad(60 + (i - 1) * 240 / math.max(1, n - 1))
		local v = ((i * 0.618) % 1) * 1.3 - 0.45
		local dir = { sin(a) * math.sqrt(1 - v * v), v, -cos(a) * math.sqrt(1 - v * v) }
		local p0 = { c[1] + dir[1] * 1.0, c[2] + dir[2] * 1.0, c[3] + dir[3] * 1.0 }
		local p1 = { c[1] + dir[1] * 2.1, c[2] + dir[2] * 2.1, c[3] + dir[3] * 2.1 }
		table.insert(spines, B:limb(p0, p1, 0.16, { col = "secondary", mat = "hard", pri = 1.3 + i * 0.05, role = "spike", name = "Spine" .. i, mesh = false }, 0.1))
	end
	B:sculpt(core, "s_blob_urchin", spines)
	eface(B, ctx, c, { 1.2, 1.2, 1.2 }, { d = 0.6, spacing = 0.42, y = 0.2, fierce = true })
	B:socket("core", at(c[1], c[2], c[3]), "Body")
	B:setRig("gait", "sway")
end

-- FUZZ BALLS --------------------------------------------------------------------------------------------------
local function buildFuzz(B: any, ctx: any, id: string, hint: string)
	local detail = ctx.detail
	local closet = has(id, "closet")
	local candy = has(id, "cotton candy") or has(hint, "cloud beast")
	local R = 1.3
	local sy = if closet then 1.45 else 1
	local c = { 0, R * sy + 0.2, 0 }
	B.boneIndex.Body.pos = { 0, c[2], 0 }
	local fluff = B:ell(R * 2, R * 2 * sy, R * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "fur", pri = 1, role = "body", name = "Fluff" })
	local tufts = {}
	for i = 1, (if detail >= 2 then 5 elseif detail >= 1 then 3 else 0) do
		local a = rad(70 + i * 55)
		local p = onSurf(c, { R, R * sy, R }, a, -0.2 + (i % 3) * 0.45, -0.25)
		table.insert(tufts, B:ell(0.9, 0.8, 0.9, at(p[1], p[2], p[3]), { col = "primary", mat = "fur", pri = 2.2 + i * 0.1, role = "body", name = "Tuft" .. i }))
	end
	B:sculpt(fluff, "s_blob_fluff", tufts)
	local r = { R, R * sy, R }
	eface(B, ctx, c, r, { d = R * 0.5, spacing = R * 0.36, y = r[2] * 0.18, fierce = closet and not ctx.traits.cute })
	-- little feet
	B:mell(0.75, 0.42, 1.0, at(R * 0.45, 0.22, -R * 0.35), { col = "darker", mat = "fur", pri = 1.5, role = "foot", name = "Foot#" })
	if has(id, "bunny") then
		-- dust bunny: two floppy fluff ears
		B:mlimb({ R * 0.32, c[2] + R * 0.8, 0.1 }, { R * 0.62, c[2] + R * 1.85, 0.35 }, 0.62, { col = "primary", mat = "fur", pri = 1.3, role = "ear", name = "Ear#", depth = 0.4 }, 0.2)
	end
	if candy then
		-- a second fluff in the other colour, piled up behind: a two-tone cloud beast
		local c2 = { R * 0.7, c[2] + R * 0.7, R * 0.6 }
		local f2 = B:ell(R * 1.6, R * 1.5, R * 1.6, at(c2[1], c2[2], c2[3]), { col = "secondary", mat = "fur", pri = 1.2, role = "body", name = "Fluff2" })
		B:sculpt(f2, "s_blob_fluff")
		if detail >= 1 then
			local f3 = B:ell(R * 1.2, R * 1.1, R * 1.2, at(-R * 0.85, c[2] + R * 0.45, R * 0.5), { col = "secondary", mat = "fur", pri = 1.6, role = "body", name = "Fluff3" })
			B:sculpt(f3, "s_blob_fluff")
		end
	end
	if closet then
		-- extra eyes peering out of the fur and long gangly arms
		for i = 1, (if detail >= 2 then 4 elseif detail >= 1 then 2 else 0) do
			local a = rad(((i % 2) * 2 - 1) * (30 + i * 9))
			local p = onSurf(c, r, a, 0.45 + i * 0.1, -0.05)
			eyeball(B, 0.42 - i * 0.03, at(p[1], p[2], p[3], 0, a, 0), "Body", 2.4 + i * 0.1, "ExtraEye" .. i)
		end
		Parts.armPair(B, { x = R * 0.85, y = c[2] + 0.3, z = 0, len = 2.2, w = 0.42, handCol = "primary", detail = math.min(detail, 2), col = "primary", mat = "fur" })
	end
	B:socket("core", at(c[1], c[2], c[3]), "Body")
	B:setRig("gait", if closet then "waddle" else "hop")
end

-- CUBES -------------------------------------------------------------------------------------------------------
local function buildCube(B: any, ctx: any, id: string, hint: string)
	local detail = ctx.detail
	local ice = has(id, "ice") or ctx.traits.frozen
	local s = 3.0
	local c = { 0, s / 2, 0 }
	B.boneIndex.Body.pos = { 0, s / 2, 0 }
	B:block(s, s, s, at(c[1], c[2], c[3]), { col = "primary", mat = if ice then "ice" else "glass", tr = if ice then 0.2 else 0.45, pri = 1, role = "body", name = "Cube" })
	Heads.objectFace(B, ctx.traits, at(0, s * 0.55, -s / 2), s * 0.85, "Body", { eye = 0.24 })
	if ice then
		for i = 1, (if detail >= 2 then 4 elseif detail >= 1 then 2 else 0) do
			local x = (i - 2.5) * 0.7
			B:wedge(0.25, 0.7, 0.45, at(x, s + 0.3, -0.6 + (i % 2) * 0.9, 0, (i % 2) * math.pi, 0), { col = "white", mat = "ice", pri = 2.3 + i * 0.1, role = "spike", name = "Icicle" .. i })
		end
		if detail >= 2 then
			B:ell(1.6, 0.5, 1.6, at(0.2, s * 0.7, 0.3), { col = "secondary", mat = "glass", tr = 0.3, pri = 3, role = "detail", name = "Frozen", noCore = true })
		end
	elseif detail >= 1 then
		-- odds and ends dissolving inside: a skull, a sword, coins, a bone
		B:ball(0.8, at(0.55, 1.1, 0.4), { col = "white", mat = "hard", pri = 1.8, role = "detail", name = "Skull", noCore = true })
		B:block(0.18, 2.0, 0.42, at(-0.75, 1.5, 0.5, 0, rad(20), rad(35)), { col = "steel", mat = "metal", pri = 2.0, role = "detail", name = "Sword", noCore = true })
		if detail >= 2 then
			B:cyl(0.1, 0.55, at(0.3, 2.1, -0.3, rad(30), 0, rad(70)), { col = "gold", mat = "metal", pri = 2.6, role = "detail", name = "Coin1", noCore = true })
			B:cyl(0.1, 0.55, at(-0.4, 0.6, -0.2, rad(-20), rad(40), rad(10)), { col = "gold", mat = "metal", pri = 2.7, role = "detail", name = "Coin2", noCore = true })
			B:limb({ 0.6, 2.2, 0.6 }, { 1.0, 2.6, -0.2 }, 0.22, { col = "white", mat = "hard", pri = 2.8, role = "detail", name = "Bone", noCore = true, mesh = false }, 0.1)
		end
	end
	B:socket("core", at(c[1], c[2], c[3]), "Body")
	B:setRig("gait", "hop")
	B:setRig("materialMotion", "wobble")
end

-- HEAPS / HORRORS ---------------------------------------------------------------------------------------------
local function buildHeap(B: any, ctx: any, id: string, hint: string)
	local t, detail = ctx.traits, ctx.detail
	local eldritch = has(id, "eldritch") or has(hint, "tentacled")
	local void = has(id, "void") or has(hint, "silhouette of stars")
	local shifter = has(id, "shape")
	local c, r = { 0, 1.2, 0 }, { 1.7, 1.2, 1.5 }
	if void then
		c, r = { 0, 2.4, 0 }, { 1.4, 2.0, 1.2 }
	end
	B.boneIndex.Body.pos = { 0, c[2], 0 }
	local body = B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = if void then "glass" else "skin", pri = 1, role = "body", name = "Body" })
	local lumps = {}
	if detail >= 1 and not void then
		for i, L in { { 1.25, 0.25, 0.45, 0.85, 0.8, 0.9 }, { -1.2, 0.05, 0.6, 0.9, 0.75, 0.85 }, { 0.3, 0.75, 0.75, 1.0, 0.7, 0.85 } } do
			table.insert(lumps, B:ell(L[4] * 2, L[5] * 2, L[6] * 2, at(c[1] + L[1], c[2] + L[2], c[3] + L[3]), { col = if i == 2 then "secondary" else "primary", mat = "skin", pri = 1.5 + i * 0.1, role = "body", name = "Lump" .. i }))
		end
	end
	if not void then
		B:sculpt(body, "s_blob_heap", lumps)
	end
	-- main face: fierce eyes and a toothy mouth
	eface(B, ctx, c, r, { d = r[1] * 0.3, spacing = r[1] * 0.28, y = r[2] * 0.2, fierce = not shifter, kind = if void then "glow" else nil, mood = if (ctx.result.mood or "Neutral") == "Neutral" and not shifter then "Angry" else nil })
	-- more eyes, mismatched, everywhere
	local ne = if detail >= 2 then 4 elseif detail >= 1 then 2 else 0
	if void then
		ne = 0
	end
	for i = 1, ne do
		local a = rad(((i % 2) * 2 - 1) * (38 + i * 12))
		local p = onSurf(c, r, a, 0.55 - (i % 3) * 0.15, -0.06)
		eyeball(B, 0.35 + (i % 3) * 0.18, at(p[1], p[2], p[3], 0, a, 0), "Body", 1.9 + i * 0.1, "ExtraEye" .. i)
	end
	-- limbs: tentacles (eldritch), or a wrong assortment of arms (abomination), or a half-formed reach (shifter)
	if eldritch or void then
		local n = if detail >= 2 then 6 elseif detail >= 1 then 4 else 2
		for i = 1, n do
			local a = rad(30 + (i - 1) * 300 / math.max(1, n - 1))
			local p0 = onSurf(c, r, a, -0.55, -0.2)
			local p1 = { p0[1] + sin(a) * 1.8, 0.1, p0[3] - cos(a) * 1.8 }
			tentacle(B, i, p0, p1, 0.55, if detail >= 2 then 2 else 1, { col = if void then "primary" else "secondary", pri = 1.4 + i * 0.05, curl = 0.5, name = "Tentacle" })
		end
	elseif not shifter and detail >= 1 then
		Parts.armPair(B, { x = r[1] * 0.92, y = c[2] + 0.35, z = -0.3, len = 1.45, w = 0.5, out = 0.5, out2 = 0.25, fwd2 = 0.3, hand = "claw", handCol = "secondary", detail = math.min(detail, 2), col = "secondary" })
		local p0 = onSurf(c, r, rad(-120), -0.2, -0.15)
		tentacle(B, 1, p0, { p0[1] - 1.6, 0.2, p0[3] + 0.8 }, 0.5, if detail >= 2 then 2 else 1, { col = "primary", pri = 1.6, curl = 0.6, name = "Tentacle" })
	elseif shifter and detail >= 1 then
		-- reaching arm still forming, and a second face surfacing on the flank
		B:limb(onSurf(c, r, rad(70), 0.1, -0.3), { r[1] * 1.9, c[2] + 1.0, -0.9 }, 0.62, { col = "secondary", mat = "skin", pri = 1.5, role = "limb", name = "FormingArm" }, 0.2)
		B:ball(0.7, at(r[1] * 1.95, c[2] + 1.05, -0.95), { col = "skin", mat = "skin", pri = 1.7, role = "hand", name = "FormingHand" })
		if detail >= 2 then
			local p = onSurf(c, r, rad(-75), 0.35, -0.05)
			eyeball(B, 0.5, at(p[1], p[2], p[3], 0, rad(-75), 0), "Body", 2.2, "SecondEye")
		end
	end
	if detail >= 2 and (eldritch or void) then
		for i = 1, (if detail >= 3 then 6 else 4) do
			local a = rad(60 + i * 50)
			local p = onSurf(c, r, a, 0.1 + (i % 3) * 0.3, 0.02)
			B:ball(0.18, at(p[1], p[2], p[3]), { col = "white", mat = "neon", glow = true, pri = 3 + i * 0.1, role = "gem", name = "Star" .. i, noCore = true })
		end
	end
	B:socket("core", at(c[1], c[2], c[3]), "Body")
	B:setRig("gait", if void or eldritch and t.flies then "float" else "surge")
	B:setRig("materialMotion", B.rig.materialMotion or "wobble")
end

-- MAWS --------------------------------------------------------------------------------------------------------
local function buildMaw(B: any, ctx: any, id: string, hint: string)
	local detail = ctx.detail
	if has(id, "umibozu") or has(hint, "rising from the sea") then
		local c, r = { 0, 1.7, 0 }, { 1.7, 1.75, 1.55 }
		B.boneIndex.Body.pos = { 0, 1.2, 0 }
		B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Head" })
		B:cyl(0.3, 5.6, at(0, 0.32, 0, 0, 0, rad(90)), { col = { 0.18, 0.42, 0.62 }, mat = "glass", tr = 0.25, pri = 1.2, role = "detail", name = "Sea" })
		if detail >= 1 then
			B:cyl(0.24, 4.3, at(0, 0.5, -0.05, 0, 0, rad(90)), { col = "white", mat = "glass", tr = 0.3, pri = 2.2, role = "detail", name = "Foam" })
		end
		eface(B, ctx, c, r, { d = 0.5, spacing = 0.55, y = 0.55, kind = "glow", noMouth = true, noBrows = true })
		B:socket("core", at(c[1], c[2], c[3]), "Body")
		B:setRig("gait", "surge")
		return
	end
	if has(id, "soul eater") or has(hint, "wraith") then
		local c, r = { 0, 3.0, 0 }, { 1.1, 1.3, 1.0 }
		B.boneIndex.Body.pos = { 0, 3.0, 0 }
		local body = B:ell(2.2, 2.6, 2.0, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Body" })
		local skirt = B:ell(2.6, 1.9, 2.4, at(0, 1.85, 0.04), { col = "primary", mat = "skin", pri = 1.2, role = "body", name = "Skirt" })
		B:sculpt(body, "s_blob_ghost", { skirt })
		local p = Face.place({ kind = "ellipsoid", c = c, r = r }, 0, -r[2] * 0.25, 0.12)
		B:ell(1.15, 1.0, 0.5, p, { col = "glow", mat = "neon", glow = true, pri = 1.1, role = "mouth", name = "Maw", noCore = true })
		eface(B, ctx, c, r, { d = 0.42, spacing = 0.42, y = r[2] * 0.3, kind = "glow", noMouth = true, noBrows = true })
		if detail >= 1 then
			for i = 1, 3 do
				local q = Face.place({ kind = "ellipsoid", c = c, r = r }, (i - 2) * 0.32, -r[2] * 0.06, 0.05)
				B:wedge(0.12, 0.3, 0.16, Geom.mul(q, at(0, 0, 0, math.pi, 0, 0)), { col = "tooth", mat = "hard", pri = 2.4 + i * 0.1, role = "tooth", name = "Fang" .. i })
			end
		end
		B:emit("smoke", nil, { socket = "core", rate = 10 })
		B:socket("core", at(c[1], c[2], c[3]), "Body")
		B:setRig("gait", "float")
		return
	end
	local taotie = has(id, "taotie") or has(hint, "no body")
	local c = { 0, 2.0, 0 }
	local r = if taotie then { 1.7, 1.35, 1.35 } else { 1.8, 1.7, 1.7 }
	B.boneIndex.Body.pos = { 0, c[2], 0 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = if taotie then "metal" else "stone", pri = 1, role = "body", name = "Body" })
	-- the maw: a gaping dark cavity with a ring of teeth
	local mw, mh = r[1] * 1.25, r[2] * 0.85
	local mp = Face.place({ kind = "ellipsoid", c = c, r = r }, 0, -r[2] * 0.3, 0.32)
	B:ell(mw, mh, 0.9, mp, { col = "mouth", mat = "skin", pri = 1.05, role = "mouth", name = "Maw", noCore = true })
	if detail >= 1 then
		B:ell(mw * 0.5, mh * 0.35, 0.5, Geom.mul(mp, at(0, -mh * 0.22, -0.12)), { col = if taotie then "tongue" else "glow", mat = if taotie then "skin" else "neon", glow = not taotie, pri = 2.2, role = "mouth", name = "Throat", noCore = true })
		local nt = if detail >= 2 then 4 else 2
		for i = 1, nt do
			local x = (i - (nt + 1) / 2) * mw * 0.22
			B:wedge(0.18, 0.5, 0.3, Geom.mul(mp, at(x, mh * 0.36 - math.abs(x) * 0.25, -0.18, math.pi, 0, 0)), { col = "tooth", mat = "hard", pri = 1.6 + i * 0.05, role = "tooth", name = "ToothU" .. i })
			B:wedge(0.18, 0.42, 0.3, Geom.mul(mp, at(x * 0.9, -mh * 0.36 + math.abs(x) * 0.2, -0.16)), { col = "tooth", mat = "hard", pri = 1.7 + i * 0.05, role = "tooth", name = "ToothL" .. i })
		end
	end
	eface(B, ctx, c, r, { d = if taotie then 0.75 else 0.5, spacing = r[1] * (if taotie then 0.4 else 0.3), y = r[2] * 0.42, fierce = true, noMouth = true, mood = "Angry" })
	if taotie then
		Parts.horns(B, { x = r[1] * 0.5, y = c[2] + r[2] * 0.75, z = 0.2, len = 2.6, w = 0.6, kind = "ram", segs = if detail >= 2 then 3 else 2, pri = 1.3, bone = "Body" })
		if detail >= 2 then
			B:mell(0.9, 0.35, 0.5, at(r[1] * 0.42, c[2] + r[2] * 0.68, -r[3] * 0.82, 0, 0, rad(-20)), { col = "secondary", mat = "metal", pri = 2.5, role = "brow", name = "Crest#" })
		end
	else
		-- craters, and orbiting debris that is being eaten
		if detail >= 2 then
			for i = 1, 3 do
				local p = onSurf(c, r, rad(90 + i * 60), 0.3 + (i % 2) * 0.3, -0.12)
				B:ell(0.75, 0.75, 0.75, at(p[1], p[2], p[3]), { col = "darker", mat = "stone", pri = 3 + i * 0.1, role = "detail", name = "Crater" .. i })
			end
		end
		if detail >= 1 then
			B:bone("Debris", "Body", 0, c[2], 0)
			B:addRig("rotors", { bone = "Debris", axis = "Y", speed = 1.6 })
			for i = 1, (if detail >= 2 then 4 else 2) do
				local a = rad(i * 90 + 20)
				B:block(0.6, 0.5, 0.55, at(sin(a) * 3.0, c[2] + (i % 2) * 0.8 - 0.3, cos(a) * 3.0, rad(i * 30), rad(i * 50), 0), { col = if i % 2 == 0 then "secondary" else "stone", mat = "stone", bone = "Debris", pri = 2.5 + i * 0.1, role = "body", name = "Rock" .. i })
			end
		end
		B:emit("glints", nil, { socket = "core", rate = 6 })
	end
	B:socket("core", at(c[1], c[2], c[3]), "Body")
	B:setRig("gait", if taotie then "stomp" else "hover")
end

-- ELEMENTALS --------------------------------------------------------------------------------------------------
local function buildElemental(B: any, ctx: any, id: string, hint: string)
	local detail = ctx.detail
	if has(id, "rock") or has(hint, "boulder") then
		local c, r = { 0, 2.0, 0 }, { 1.7, 1.5, 1.5 }
		B.boneIndex.Body.pos = { 0, 2.0, 0 }
		B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "stone", pri = 1, role = "body", name = "Boulder" })
		eface(B, ctx, c, r, { d = 0.55, spacing = 0.5, y = 0.35, fierce = true })
		Parts.armPair(B, { x = r[1] * 0.95, y = c[2] + 0.3, z = 0, len = 1.6, w = 0.75, handCol = "secondary", detail = math.min(detail, 2), col = "secondary", mat = "stone" })
		Parts.legPair(B, { x = 0.75, y = 0.75, z = 0.1, w = 0.7, kind = "pillar", detail = math.min(detail, 1), col = "secondary", mat = "stone" })
		if detail >= 2 then
			for i = 1, 2 do
				B:block(0.8, 0.6, 0.7, at((i * 2 - 3) * 0.7, c[2] + r[2] * 0.85, 0.4, rad(i * 20), rad(i * 35), 0), { col = "darkStone", mat = "stone", pri = 2.6 + i * 0.1, role = "body", name = "Rock" .. i })
			end
		end
		B:socket("core", at(c[1], c[2], c[3]), "Body")
		B:setRig("gait", "stomp")
		return
	end
	-- sludge humanoid: a heaped base rising into a slumped torso and head, drooping arms, drips
	local poison = has(id, "poison") or ctx.traits.element == "Poison"
	local mat = if poison then "glass" else "skin"
	B.boneIndex.Body.pos = { 0, 1.8, 0 }
	local base = B:ell(3.2, 1.3, 2.8, at(0, 0.55, 0), { col = "primary", mat = mat, pri = 1.02, role = "body", name = "Base" })
	local _ = base
	B:ell(2.4, 2.6, 2.1, at(0, 2.1, 0.05), { col = "primary", mat = mat, pri = 1, role = "body", name = "Torso" })
	local hc, hr = { 0, 3.75, -0.2 }, { 0.82, 0.72, 0.75 }
	B:ell(hr[1] * 2, hr[2] * 2, hr[3] * 2, at(hc[1], hc[2], hc[3]), { col = "primary", mat = mat, pri = 1.05, role = "head", name = "Head" })
	eface(B, ctx, hc, hr, { d = 0.42, spacing = 0.3, y = 0.1, fierce = true })
	Parts.armPair(B, { x = 1.25, y = 2.9, z = 0, len = 2.6, w = 0.62, handCol = "primary", detail = math.min(detail, 2), col = "primary", mat = mat })
	if detail >= 1 then
		for i = 1, (if detail >= 2 then 4 else 2) do
			local a = rad(-50 + i * 75)
			local p = onSurf({ 0, 2.1, 0.05 }, { 1.2, 1.3, 1.05 }, a, -0.1 - (i % 2) * 0.3, 0.02)
			B:ell(0.35, 0.6, 0.35, at(p[1], p[2], p[3]), { col = if poison then "secondary" else "darker", mat = mat, pri = 2.2 + i * 0.1, role = "detail", name = "Drop" .. i })
		end
	end
	if poison and detail >= 2 then
		for i = 1, 3 do
			local p = onSurf({ 0, 2.1, 0.05 }, { 1.2, 1.3, 1.05 }, rad(100 + i * 55), 0.3 + (i % 2) * 0.25, -0.06)
			B:ball(0.4, at(p[1], p[2], p[3]), { col = "secondary", mat = "glass", pri = 3 + i * 0.1, role = "detail", name = "Bubble" .. i, noCore = true })
		end
		B:emit("bubbles", nil, { socket = "core", rate = 8 })
	end
	B:socket("core", at(0, 2.1, 0), "Body")
	B:setRig("gait", if ctx.traits.flies then "float" else "heavy")
	B:setRig("materialMotion", B.rig.materialMotion or "wobble")
end

-- GHOSTS ------------------------------------------------------------------------------------------------------
local function sheetGhost(B: any, ctx: any, H: number, o: any)
	local c, r = { 0, H, 0 }, { 1.1, 1.3, 1.0 }
	B.boneIndex.Body.pos = { 0, H, 0 }
	local body = B:ell(2.2, 2.6, 2.0, at(c[1], c[2], c[3]), { col = o.col or "primary", mat = o.mat or "cloth", pri = 1, role = "body", name = "Body" })
	local skirt = B:ell(2.6, 1.9, 2.4, at(0, H - 1.15, 0.04), { col = o.col or "primary", mat = o.mat or "cloth", pri = 1.2, role = "body", name = "Skirt" })
	B:sculpt(body, "s_blob_ghost", { skirt })
	return c, r
end

local function buildGhost(B: any, ctx: any, id: string, hint: string)
	local detail = ctx.detail
	if has(id, "poltergeist") or has(hint, "floating furniture") then
		-- a small wisp in the middle and a ring of household things whirling round it
		local c, r = sheetGhost(B, ctx, 2.6, { mat = "glass" })
		eface(B, ctx, c, r, { d = 0.5, spacing = 0.38, y = r[2] * 0.2, detail = 1, noBrows = true })
		B:bone("Whirl", "Body", 0, 2.4, 0)
		B:addRig("rotors", { bone = "Whirl", axis = "Y", speed = 2.2 })
		local items = if detail >= 2 then 5 elseif detail >= 1 then 3 else 2
		for i = 1, items do
			local a = rad(i * 360 / items + 15)
			local p = { sin(a) * 2.6, 1.6 + (i % 3) * 0.9, -cos(a) * 2.6 }
			local kind = (i - 1) % 4
			if kind == 0 then
				B:cyl(0.12, 1.0, at(p[1], p[2], p[3], rad(20), a, rad(70)), { col = "white", mat = "plastic", bone = "Whirl", pri = 1.5 + i * 0.1, role = "detail", name = "Plate" .. i })
			elseif kind == 1 then
				B:block(0.9, 0.12, 0.9, at(p[1], p[2], p[3], rad(15), a, rad(-20)), { col = "wood", mat = "wood", bone = "Whirl", pri = 1.5 + i * 0.1, role = "detail", name = "Seat" .. i })
				B:block(0.12, 1.0, 0.9, at(p[1] + 0.4, p[2] + 0.5, p[3], rad(15), a, rad(-20)), { col = "wood", mat = "wood", bone = "Whirl", pri = 1.6 + i * 0.1, role = "detail", name = "Back" .. i })
			elseif kind == 2 then
				B:block(0.75, 0.22, 0.55, at(p[1], p[2], p[3], rad(-25), a, rad(30)), { col = "red", mat = "cloth", bone = "Whirl", pri = 1.5 + i * 0.1, role = "detail", name = "Book" .. i })
			else
				B:cyl(0.7, 0.45, at(p[1], p[2], p[3], 0, a, rad(80)), { col = "white", mat = "plastic", bone = "Whirl", pri = 1.5 + i * 0.1, role = "detail", name = "Cup" .. i })
			end
		end
		B:socket("core", at(c[1], c[2], c[3]), "Body")
		B:setRig("gait", "float")
		return
	end
	local kid = has(id, "kid") or has(hint, "kid in")
	local robot = has(id, "robot") or ctx.traits.robot
	local disco = has(id, "disco")
	local it = id == "it" or has(hint, "under a sheet")
	local H = if kid then 2.15 elseif it then 1.9 else 2.8
	local c, r = sheetGhost(B, ctx, H, { col = if disco then "chrome" else nil, mat = if disco then "foil" elseif robot then "glass" else "cloth" })
	-- eye holes: dark ovals (or glowing slits / LEDs)
	eface(B, ctx, c, r, { d = 0.62, spacing = 0.4, y = r[2] * 0.15, detail = if robot or it then nil else 1, kind = if robot then "robot" elseif it then "glow" else nil, noBrows = true, noMouth = kid or it })
	if kid then
		-- sneakers poking out under the hem, a candy bucket
		B:mell(0.7, 0.45, 1.05, at(0.42, 0.24, -0.2), { col = "secondary", mat = "plastic", pri = 1.3, role = "foot", name = "Shoe#" })
		if detail >= 1 then
			B:mlimb({ 0.42, 0.95, 0 }, { 0.42, 0.45, -0.05 }, 0.42, { col = "skin", mat = "skin", pri = 2.2, role = "limb", name = "Shin#" }, 0.1)
		end
		if detail >= 2 then
			B:cyl(0.8, 0.85, at(1.45, 1.1, -0.35, 0, 0, rad(90)), { col = "flame", mat = "plastic", pri = 2.6, role = "held", name = "Bucket" })
		end
	end
	if it then
		local p0 = { 0.5, H - 1.5, -0.6 }
		tentacle(B, 1, p0, { 1.7, 0.12, -1.6 }, 0.4, if detail >= 1 then 2 else 1, { col = "secondary", pri = 1.4, curl = 0.7, name = "Tentacle" })
	end
	if disco and detail >= 1 then
		for i = 1, (if detail >= 2 then 6 else 3) do
			local a = rad(70 + i * 40)
			local p = onSurf(c, r, a, -0.1 + (i % 3) * 0.35, -0.02)
			B:block(0.3, 0.3, 0.08, at(p[1], p[2], p[3], 0, a + math.pi, 0), { col = if i % 2 == 0 then "secondary" else "white", mat = "neon", glow = true, pri = 2.6 + i * 0.1, role = "gem", name = "Tile" .. i, noCore = true })
		end
		B:emit("glitter", nil, { socket = "core", rate = 12 })
	end
	if robot and detail >= 1 then
		for i = 1, (if detail >= 2 then 4 else 2) do
			B:block(0.3, 0.3, 0.3, at((i - 2.5) * 0.6, H - 1.95 - (i % 2) * 0.4, 0.2, rad(i * 25), rad(i * 35), 0), { col = "glow", mat = "neon", glow = true, pri = 2.5 + i * 0.1, role = "gem", name = "Pixel" .. i, noCore = true })
		end
		B:setRig("materialMotion", "flicker")
	end
	B:socket("core", at(c[1], c[2], c[3]), "Body")
	B:setRig("gait", if kid then "waddle" elseif it then "surge" else "float")
end

-- TUBES / POLYPS ----------------------------------------------------------------------------------------------
local function buildTube(B: any, ctx: any, id: string, hint: string)
	local detail = ctx.detail
	B.boneIndex.Body.pos = { 0, 1.2, 0 }
	if has(id, "cocoon") then
		B:cyl(3.4, 0.35, at(0, 5.2, 0, 0, rad(20), 0), { col = "bark", mat = "wood", pri = 1.3, role = "detail", name = "Twig" })
		B:limb({ 0, 5.1, 0 }, { 0, 4.3, 0 }, 0.12, { col = "white", mat = "cloth", pri = 1.6, role = "detail", name = "Thread" }, 0.1)
		local c, r = { 0, 2.6, 0 }, { 0.95, 1.65, 0.95 }
		B.boneIndex.Body.pos = { 0, 4.3, 0 }
		B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "cloth", pri = 1, role = "body", name = "Pod" })
		for i = 1, (if detail >= 2 then 3 elseif detail >= 1 then 2 else 0) do
			local y = c[2] + 0.9 - i * 0.6
			local k = math.sqrt(math.max(0.1, 1 - ((y - c[2]) / r[2]) ^ 2)) * 1.04
			B:ell(r[1] * 2 * k, 0.22, r[3] * 2 * k, at(0, y, 0, rad(10 + i * 4), 0, rad(-8)), { col = "secondary", mat = "cloth", pri = 2 + i * 0.1, role = "detail", name = "Silk" .. i })
		end
		eface(B, ctx, c, r, { d = 0.45, spacing = 0.32, y = 0.35, mood = if (ctx.result.mood or "Neutral") == "Neutral" then "Sleepy" else nil, noBrows = true })
		B:addRig("sway", { bone = "Body" })
		B:socket("core", at(c[1], c[2], c[3]), "Body")
		B:setRig("gait", "sway")
		return
	end
	if has(id, "squirt") then
		local c, r = { 0, 1.35, 0 }, { 0.95, 1.3, 0.95 }
		B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "glass", tr = 0.15, pri = 1, role = "body", name = "Body" })
		B:limb({ 0, 2.2, 0.15 }, { 0, 3.55, 0.05 }, 0.62, { col = "primary", mat = "skin", pri = 1.2, role = "body", name = "Siphon1" }, 0.1)
		B:limb({ 0.6, 1.9, 0.3 }, { 1.55, 2.75, 0.35 }, 0.52, { col = "primary", mat = "skin", pri = 1.3, role = "body", name = "Siphon2" }, 0.1)
		B:ell(0.78, 0.24, 0.78, at(0, 3.68, 0.04), { col = "secondary", mat = "skin", pri = 1.35, role = "detail", name = "Rim1" })
		B:ell(0.66, 0.66, 0.22, Geom.mul(at(1.63, 2.83, 0.35), at(0, 0, 0, 0, rad(90), rad(-48))), { col = "secondary", mat = "skin", pri = 1.4, role = "detail", name = "Rim2" })
		if detail >= 1 then
			B:ell(0.4, 0.14, 0.4, at(0, 3.74, 0.04), { col = "dark", mat = "skin", pri = 2.0, role = "detail", name = "Hole1", noCore = true })
		end
		eface(B, ctx, c, r, { d = 0.5, spacing = 0.34, y = 0.1, noBrows = true })
		B:socket("core", at(c[1], c[2], c[3]), "Body")
		B:setRig("gait", "sway")
		return
	end
	if has(id, "pyrosome") or has(hint, "glowing hollow tube") then
		local c, r = { 0, 2.4, 0 }, { 1.0, 2.1, 1.0 }
		B.boneIndex.Body.pos = { 0, 2.4, 0 }
		B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "glass", tr = 0.2, pri = 1, role = "body", name = "Body" })
		B:ell(1.3, 0.5, 1.3, at(0, c[2] + r[2] * 0.86, 0), { col = "dark", mat = "skin", pri = 1.3, role = "detail", name = "Mouth", noCore = true })
		eface(B, ctx, c, r, { d = 0.48, spacing = 0.34, y = 0.45, noBrows = true, noMouth = true })
		for i = 1, (if detail >= 2 then 8 elseif detail >= 1 then 5 else 3) do
			local a = rad(50 + i * 47)
			local p = onSurf(c, r, a, -0.7 + (i % 5) * 0.32, -0.04)
			B:ball(0.3, at(p[1], p[2], p[3]), { col = "glow", mat = "neon", glow = true, pri = 1.6 + i * 0.08, role = "gem", name = "Zooid" .. i, noCore = true })
		end
		B:socket("core", at(c[1], c[2], c[3]), "Body")
		B:setRig("gait", "float")
		return
	end
	-- stalked polyps: hydra (tube + crown of tentacles), sea lily (segmented stalk + feathery arms)
	local lily = has(id, "lily") or has(hint, "stalk")
	B:cyl(0.3, 1.6, at(0, 0.15, 0, 0, 0, rad(90)), { col = "secondary", mat = "skin", pri = 2.5, role = "foot", name = "Foot" })
	local segs = if detail >= 1 then 3 else 1
	local prev = { 0, 0.2, 0 }
	local parent = "Body"
	for i = 1, segs do
		local q = { sin(i * 0.9) * 0.18, 0.2 + i * 3.0 / segs, 0 }
		local bn = B:bone("Stalk" .. i, parent, prev[1], prev[2], prev[3])
		B:addRig("tail", { bone = bn })
		B:limb(prev, q, if lily then 0.32 else 0.55, { col = "primary", mat = "skin", bone = bn, pri = 1.1 + i * 0.05, role = "body", name = "Stalk" .. i }, 0.15)
		prev, parent = q, bn
	end
	local c, r = { prev[1], prev[2] + 0.35, 0 }, { 0.62, 0.55, 0.6 }
	B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", bone = parent, pri = 1.05, role = "head", name = "Calyx" })
	eface(B, ctx, c, r, { bone = parent, d = 0.4, spacing = 0.24, y = 0.05, noBrows = true })
	local n = if detail >= 2 then 6 elseif detail >= 1 then 5 else 4
	for i = 1, n do
		local a = rad(i * 360 / n)
		local p0 = { c[1] + sin(a) * 0.45, c[2] + 0.4, -cos(a) * 0.45 }
		local p1 = { c[1] + sin(a) * 1.6, c[2] + (if lily then 1.6 else 0.9), -cos(a) * 1.6 + 0.3 }
		local made = tentacle(B, i, p0, p1, if lily then 0.3 else 0.18, 1, { parent = parent, col = if lily then "secondary" else "primary", pri = 1.2 + i * 0.02, name = "Arm" })
		if lily and detail >= 3 then
			B:ell(0.7, 0.06, 0.25, Geom.mul(made[1].cf, at(0, 0.2, 0, 0, 0, rad(90))), { col = "secondary", mat = "leaf", bone = made[1].bone, pri = 3.5 + i * 0.05, role = "detail", name = "Pinnule" .. i })
		end
	end
	B:socket("core", at(c[1], c[2], c[3]), parent)
	B:setRig("gait", "sway")
end

-- CHAINS (salp, siphonophore) -----------------------------------------------------------------------------------
local function buildChain(B: any, ctx: any, id: string, hint: string)
	local detail = ctx.detail
	local siph = has(id, "siphonophore")
	local n = if detail >= 2 then 6 elseif detail >= 1 then 4 else 3
	local Hh = 3.0
	B.boneIndex.Body.pos = { 0, Hh, -1.6 }
	local parent = "Body"
	local first
	for i = 1, n do
		local u = (i - 1) / math.max(1, n - 1)
		local p = if siph then { sin(u * 3) * 0.6, 4.6 - u * 4.0, u * 0.6 } else { sin(u * 4.2) * 0.9, Hh + sin(u * 3.0) * 0.4, -1.8 + u * 4.2 }
		local bn = if i == 1 then "Body" else B:bone("Unit" .. i, parent, p[1], p[2], p[3])
		if i > 1 then
			B:addRig("tail", { bone = bn })
		end
		local s = if siph then (if i == 1 then 1.3 else 0.9) else (if i == 1 then 1.25 else 1.05 - u * 0.2)
		local unit = B:ell(1.2 * s, (if siph then 1.0 else 1.0) * s, 1.45 * s, at(p[1], p[2], p[3], 0, rad((i % 2) * 14), 0),
			{ col = if siph and i % 2 == 0 then "secondary" else "primary", mat = "glass", tr = 0.3, bone = bn, pri = 1 + i * 0.05, role = "body", name = if i == 1 then "Body" else "Unit" .. i })
		if i == 1 then
			first = { c = p, r = { 0.6 * s, 0.5 * s, 0.725 * s } }
		end
		if detail >= 1 then
			B:ball(0.42 * s, at(p[1], p[2], p[3] + 0.1), { col = "glow", mat = "neon", glow = true, bone = bn, pri = 1.8 + i * 0.05, role = "core", name = "Gut" .. i, noCore = true, needs = unit.name })
		end
		parent = bn
	end
	local _ = first
	eface(B, ctx, first.c, first.r, { d = 0.42, spacing = 0.3, y = 0.08, noBrows = true })
	if siph and detail >= 1 then
		for i = 1, 3 do
			tentacle(B, i, { (i - 2) * 0.4, 1.0, 0.6 }, { (i - 2) * 0.6, 0.1, 0.8 }, 0.1, 1, { col = "secondary", pri = 2.5, glow = true, mesh = false })
		end
	end
	B:socket("core", at(first.c[1], first.c[2], first.c[3]), "Body")
	B:setRig("gait", "swim")
end

-- BUBBLES / BALLOONS ------------------------------------------------------------------------------------------
local function buildBubble(B: any, ctx: any, id: string, hint: string)
	local detail = ctx.detail
	if has(id, "balloon") then
		-- a twisted-balloon monster: sausage segments with pinched joints, a round head and a knot
		B.boneIndex.Body.pos = { 0, 1.9, 0 }
		local m = { col = "primary", mat = "plastic", role = "body" }
		B:limb({ 0, 1.9, 0.9 }, { 0, 2.0, -0.6 }, 1.0, { col = "primary", mat = "plastic", pri = 1, role = "body", name = "Body" }, 0.05)
		local hc, hr = { 0, 3.0, -1.0 }, { 0.75, 0.75, 0.75 }
		B:ball(1.5, at(hc[1], hc[2], hc[3]), { col = "secondary", mat = "plastic", pri = 1.05, role = "head", name = "Head" })
		eface(B, ctx, hc, hr, { d = 0.42, spacing = 0.28, y = 0.08, fierce = true })
		Parts.legPair(B, { x = 0.42, y = 1.6, z = -0.45, w = 0.45, kind = "paw", detail = math.min(detail, 1), tag = "F", col = "primary", mat = "plastic" })
		Parts.legPair(B, { x = 0.42, y = 1.6, z = 0.75, w = 0.45, kind = "paw", detail = math.min(detail, 1), tag = "H", phase = 0.5, col = "primary", mat = "plastic" })
		if detail >= 1 then
			B:mlimb({ 0.3, 3.55, -1.0 }, { 0.65, 4.5, -0.9 }, 0.36, { col = "secondary", mat = "plastic", pri = 1.6, role = "ear", name = "Ear#" }, 0.1)
		end
		if detail >= 2 then
			B:limb({ 0, 2.0, 0.95 }, { 0, 2.9, 1.7 }, 0.38, { col = "primary", mat = "plastic", pri = 2.2, role = "tail", name = "Tail" }, 0.1)
		end
		local _ = m
		B:socket("core", at(0, 2.0, 0), "Body")
		B:setRig("gait", "hop")
		return
	end
	local c = { 0, 2.0, 0 }
	B.boneIndex.Body.pos = { 0, 2.0, 0 }
	B:ball(2.6, at(c[1], c[2], c[3]), { col = "primary", mat = "glass", tr = 0.4, pri = 1, role = "body", name = "Bubble" })
	eface(B, ctx, c, { 1.3, 1.3, 1.3 }, { d = 0.55, spacing = 0.4, y = 0.15, noBrows = true })
	local n = if detail >= 2 then 6 elseif detail >= 1 then 4 else 2
	for i = 1, n do
		local a = rad(50 + i * 52)
		local d = 1.4 - (i % 3) * 0.3
		local p = onSurf(c, { 1.3, 1.3, 1.3 }, a, -0.6 + (i % 4) * 0.45, d * 0.25)
		B:ball(d, at(p[1], p[2], p[3]), { col = if i % 2 == 0 then "secondary" else "primary", mat = "glass", tr = 0.45, pri = 1.4 + i * 0.1, role = "body", name = "Bubble" .. i })
	end
	if detail >= 2 then
		B:ell(0.5, 0.3, 0.2, at(-0.55, c[2] + 0.75, -0.95, rad(-30), rad(20), rad(30)), { col = "shine", mat = "neon", pri = 3, role = "shine", name = "Gloss", noCore = true })
	end
	B:emit("bubbles", nil, { socket = "core", rate = 10 })
	B:socket("core", at(c[1], c[2], c[3]), "Body")
	B:setRig("gait", "float")
end

-- BOTS --------------------------------------------------------------------------------------------------------
local function buildBot(B: any, ctx: any, id: string, hint: string)
	local detail = ctx.detail
	if has(id, "vacuum") then
		B.boneIndex.Body.pos = { 0, 0.5, 0 }
		B:cyl(0.8, 3.4, at(0, 0.5, 0, 0, 0, rad(90)), { col = "primary", mat = "plastic", pri = 1, role = "body", name = "Shell" })
		B:cyl(0.3, 1.1, at(0, 1.02, 0.35, 0, 0, rad(90)), { col = "secondary", mat = "plastic", pri = 1.4, role = "detail", name = "Sensor" })
		B:block(2.4, 0.4, 0.3, at(0, 0.45, -1.5), { col = "dark", mat = "rubber", pri = 1.3, role = "detail", name = "Bumper" })
		Heads.objectFace(B, ctx.traits, at(0, 0.98, -0.9, rad(-90), 0, 0), 2.0, "Body", { kind = "robot", eye = 0.24 })
		if detail >= 1 then
			for _, side in { 1, -1 } do
				B:bone("Brush" .. side, "Body", side * 1.25, 0.12, -1.1)
				B:addRig("rotors", { bone = "Brush" .. side, axis = "Y", speed = side * 9 })
				for j = 1, 3 do
					local a = rad(j * 120)
					B:limb({ side * 1.25, 0.12, -1.1 }, { side * 1.25 + sin(a) * 0.7, 0.08, -1.1 - cos(a) * 0.7 }, 0.08, { col = "secondary", mat = "plastic", bone = "Brush" .. side, pri = 2.5 + j * 0.1, role = "detail", name = "Bristle" .. side .. j, mesh = false }, 0.05)
				end
			end
		end
		B:socket("core", at(0, 0.6, 0), "Body")
		B:setRig("gait", "drive")
		return
	end
	if has(id, "mine") then
		local c = { 0, 1.35, 0 }
		B.boneIndex.Body.pos = { 0, 1.35, 0 }
		B:ball(2.2, at(c[1], c[2], c[3]), { col = "primary", mat = "metal", pri = 1, role = "body", name = "Body" })
		eface(B, ctx, c, { 1.1, 1.1, 1.1 }, { kind = "robot", d = 0.5, spacing = 0.38, y = 0.1, noMouth = true })
		B:ball(0.5, at(0, 2.5, 0.1), { col = "red", mat = "neon", glow = true, pri = 1.4, role = "gem", name = "Blinker", noCore = true })
		for i = 1, (if detail >= 2 then 6 elseif detail >= 1 then 4 else 2) do
			local a = rad(60 + i * 48)
			local p0 = onSurf(c, { 1.1, 1.1, 1.1 }, a, ((i % 3) - 1) * 0.5, -0.15)
			local p1 = onSurf(c, { 1.1, 1.1, 1.1 }, a, ((i % 3) - 1) * 0.5, 0.55)
			B:limb(p0, p1, 0.3, { col = "steel", mat = "metal", pri = 1.6 + i * 0.1, role = "spike", name = "Prong" .. i, mesh = false }, 0.05)
		end
		Parts.wheelPair(B, { x = 0.95, y = 0.35, z = 0, r = 0.35, w = 0.3, detail = detail })
		B:socket("core", at(c[1], c[2], c[3]), "Body")
		B:setRig("gait", "drive")
		return
	end
	if has(id, "ankle") or has(hint, "snappy") then
		-- a little round nipper with a big hinged jaw
		local c, r = { 0, 0.95, 0 }, { 0.95, 0.75, 0.9 }
		B.boneIndex.Body.pos = { 0, 0.95, 0 }
		B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Body" })
		eface(B, ctx, c, r, { d = 0.42, spacing = 0.3, y = 0.3, noMouth = true, fierce = true })
		B:bone("Jaw", "Body", 0, 0.75, 0.2)
		B:setRig("jaw", "Jaw")
		B:ell(1.5, 0.45, 1.1, at(0, 0.45, -0.55), { col = "secondary", mat = "skin", bone = "Jaw", pri = 1.1, role = "jaw", name = "Jaw" })
		if detail >= 1 then
			Parts.teeth(B, { bone = "Jaw", y = 0.82, z = -1.0, r = 0.5, n = if detail >= 2 then 4 else 2, h = 0.28, pri = 1.6 })
		end
		Parts.legPair(B, { x = 0.45, y = 0.4, z = 0.1, w = 0.3, kind = "paw", detail = math.min(detail, 1) })
		B:socket("core", at(c[1], c[2], c[3]), "Body")
		B:setRig("gait", "scuttle")
		return
	end
	-- pixel invader: a voxel crab built from cubes on a grid (claws up, little legs)
	B.boneIndex.Body.pos = { 0, 2.0, 0 }
	local u = 0.55
	local cells = { { 0, 0 }, { -1, 0 }, { 1, 0 }, { -2, 0 }, { 2, 0 }, { 0, 1 }, { -1, 1 }, { 1, 1 }, { -1, -1 }, { 1, -1 }, { -3, 1 }, { 3, 1 }, { -2, -2 }, { 2, -2 }, { -3, 2 }, { 3, 2 } }
	local limit = if detail >= 2 then #cells elseif detail >= 1 then 12 else 8
	for i = 1, limit do
		local cxy = cells[i]
		B:block(u * 0.96, u * 0.96, u * 1.4, at(cxy[1] * u, 2.0 + cxy[2] * u + ((i % 2) * 0.012), (i % 3) * 0.01), { col = "primary", mat = "neon", pri = 1 + i * 0.02, role = "body", name = if i == 1 then "Body" else "Pixel" .. i })
	end
	for _, side in { 1, -1 } do
		B:block(u * 0.7, u * 0.7, u * 0.5, at(side * u, 2.0 + u, -u * 0.6), { col = "black", mat = "plastic", pri = 1.05, role = "eye", name = "Eye" .. (if side > 0 then "R" else "L"), pair = "eyes" })
	end
	B:socket("core", at(0, 2.0, 0), "Body")
	B:setRig("gait", "hover")
end

-- HAUNTED OBJECTS (candle, lantern, teapot, umbrella, sock) -------------------------------------------------------
local function buildSpirit(B: any, ctx: any, id: string, hint: string)
	local detail = ctx.detail
	if has(id, "candle") then
		B.boneIndex.Body.pos = { 0, 1.4, 0 }
		B:cyl(2.8, 1.8, at(0, 1.4, 0, 0, 0, rad(90)), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Wax" })
		B:ell(1.95, 0.4, 1.95, at(0, 2.75, 0), { col = "light", mat = "skin", pri = 1.3, role = "detail", name = "Pool" })
		B:limb({ 0, 2.85, 0 }, { 0, 3.3, 0 }, 0.12, { col = "black", mat = "cloth", pri = 1.5, role = "detail", name = "Wick" }, 0.05)
		B:ell(0.62, 1.15, 0.62, at(0, 3.8, 0), { col = "flame", mat = "neon", glow = true, pri = 1.2, role = "glow", name = "Flame", trail = true, noCore = true })
		if detail >= 1 then
			B:ell(0.32, 0.6, 0.32, at(0, 3.6, -0.02), { col = "flameCore", mat = "neon", glow = true, pri = 2.0, role = "glow", name = "FlameCore", noCore = true })
		end
		for i = 1, (if detail >= 2 then 4 elseif detail >= 1 then 2 else 0) do
			local a = rad(30 + i * 70)
			B:ell(0.32, 0.9 - (i % 2) * 0.3, 0.32, at(sin(a) * 0.9, 2.3 - (i % 2) * 0.25, -cos(a) * 0.9), { col = "light", mat = "skin", pri = 2.4 + i * 0.1, role = "detail", name = "Drip" .. i })
		end
		Heads.objectFace(B, ctx.traits, at(0, 1.5, -0.9), 1.5, "Body", { curve = 0.25 })
		B:socket("core", at(0, 3.6, 0), "Body")
		B:setRig("gait", "hop")
		return
	end
	if has(id, "lantern") then
		local c, r = { 0, 2.6, 0 }, { 1.15, 1.35, 1.15 }
		B.boneIndex.Body.pos = { 0, 2.6, 0 }
		B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "cloth", pri = 1, role = "body", name = "Paper" })
		B:cyl(0.3, 1.2, at(0, c[2] + r[2] * 0.97, 0, 0, 0, rad(90)), { col = "dark", mat = "wood", pri = 1.2, role = "detail", name = "Cap" })
		B:cyl(0.3, 1.2, at(0, c[2] - r[2] * 0.97, 0, 0, 0, rad(90)), { col = "dark", mat = "wood", pri = 1.25, role = "detail", name = "Base" })
		for i = 1, (if detail >= 2 then 3 elseif detail >= 1 then 2 else 0) do
			local y = (i - (if detail >= 2 then 2 else 1.5)) * 0.65
			local k = math.sqrt(1 - (y / r[2]) ^ 2) * 1.03
			B:ell(r[1] * 2 * k, 0.12, r[3] * 2 * k, at(0, c[2] + y + 0.15, 0), { col = "dark", mat = "wood", pri = 2.2 + i * 0.1, role = "detail", name = "Rib" .. i })
		end
		eface(B, ctx, c, r, { d = 0.55, spacing = 0.42, y = 0.35, mouthY = -0.25, mood = if (ctx.result.mood or "Neutral") == "Neutral" then "Crazy" else nil })
		if detail >= 1 then
			B:limb({ 0, c[2] - 0.45, -r[3] * 0.82 }, { 0.1, c[2] - 1.6, -r[3] * 1.05 }, 0.42, { col = "tongue", mat = "skin", pri = 1.6, role = "mouth", name = "Tongue", depth = 0.18 }, 0.1)
		end
		B:socket("core", at(c[1], c[2], c[3]), "Body")
		B:setRig("gait", "hover")
		return
	end
	if has(id, "teapot") then
		local c, r = { 0, 1.25, 0 }, { 1.35, 1.05, 1.25 }
		B.boneIndex.Body.pos = { 0, 1.25, 0 }
		B:ell(r[1] * 2, r[2] * 2, r[3] * 2, at(c[1], c[2], c[3]), { col = "primary", mat = "plastic", pri = 1, role = "body", name = "Pot" })
		B:ell(1.4, 0.4, 1.4, at(0, c[2] + r[2] * 0.95, 0), { col = "secondary", mat = "plastic", pri = 1.3, role = "detail", name = "Lid" })
		B:ball(0.45, at(0, c[2] + r[2] * 1.22, 0), { col = "secondary", mat = "plastic", pri = 1.6, role = "detail", name = "Knob" })
		B:limb({ 1.0, 1.05, 0 }, { 2.05, 2.15, 0 }, 0.42, { col = "primary", mat = "plastic", pri = 1.2, role = "detail", name = "Spout" }, 0.1)
		if detail >= 1 then
			B:limb({ -1.15, 1.85, 0 }, { -1.85, 1.35, 0 }, 0.3, { col = "primary", mat = "plastic", pri = 1.5, role = "detail", name = "HandleTop" }, 0.15)
			B:limb({ -1.85, 1.35, 0 }, { -1.2, 0.65, 0 }, 0.3, { col = "primary", mat = "plastic", pri = 1.55, role = "detail", name = "HandleLow" }, 0.15)
		end
		if detail >= 2 then
			local k = math.sqrt(1 - 0.2 ^ 2) * 1.03
			B:ell(r[1] * 2 * k, 0.22, r[3] * 2 * k, at(0, c[2] + 0.2, 0), { col = "secondary", mat = "plastic", pri = 2.6, role = "detail", name = "Band" })
		end
		eface(B, ctx, c, r, { d = 0.48, spacing = 0.42, y = -0.05, mouthY = -0.45 })
		B:emit("steam", nil, { socket = "core", rate = 6 })
		B:socket("core", at(2.05, 2.15, 0), "Body")
		B:setRig("gait", "hop")
		return
	end
	if has(id, "tsukumogami") or has(hint, "umbrella") then
		-- a closed paper umbrella hopping on one leg: one big eye, long tongue
		B.boneIndex.Body.pos = { 0, 2.4, 0 }
		B:limb({ 0, 1.2, 0 }, { 0, 4.6, 0 }, 1.9, { col = "primary", mat = "cloth", pri = 1, role = "body", name = "Canopy" }, 0.05)
		local c, r = { 0, 2.6, 0 }, { 0.88, 1.2, 0.88 }
		if detail >= 1 then
			B:cyl(0.24, 1.55, at(0, 2.05, 0, 0, 0, rad(90)), { col = "secondary", mat = "cloth", pri = 2.0, role = "detail", name = "Tie" })
		end
		B:limb({ 0, 4.4, 0 }, { 0, 5.1, 0 }, 0.2, { col = "darkWood", mat = "wood", pri = 1.5, role = "detail", name = "Tip" }, 0.1)
		B:limb({ 0, 1.3, 0 }, { 0, 0.3, 0 }, 0.42, { col = "skin", mat = "skin", pri = 1.2, role = "limb", name = "Leg" }, 0.1)
		B:ell(0.6, 0.35, 0.95, at(0, 0.17, -0.25), { col = "wood", mat = "wood", pri = 1.4, role = "foot", name = "Geta" })
		local p = Face.place({ kind = "ellipsoid", c = c, r = r }, 0, r[2] * 0.15, 0.1)
		local e = B:ell(0.95, 0.95, 0.4, p, { col = "eyeWhite", mat = "skin", pri = 1.05, role = "eye", name = "Eye", noCore = true })
		B:ell(0.48, 0.5, 0.3, Geom.mul(p, at(0, 0, -0.14)), { col = "pupil", mat = "glass", pri = 1.1, role = "pupil", name = "Pupil", needs = e.name, noCore = true })
		B:limb(Face.onEllipsoid(c, r, 0, -r[2] * 0.4), { 0.1, c[2] - 1.5, -r[3] * 1.4 }, 0.4, { col = "tongue", mat = "skin", pri = 1.5, role = "mouth", name = "Tongue", depth = 0.16 }, 0.1)
		B:socket("core", at(0, 2.6, 0), "Body")
		B:setRig("gait", "hop")
		return
	end
	-- sock: an upright tube folding over at the top into a head (toe forward), striped, with button eyes
	B.boneIndex.Body.pos = { 0, 1.5, 0 }
	B:limb({ 0, 0.1, 0.3 }, { 0, 2.6, 0.2 }, 1.45, { col = "primary", mat = "cloth", pri = 1, role = "body", name = "Leg" }, 0.12)
	local hc, hr = { 0, 3.1, -0.35 }, { 0.78, 0.66, 0.95 }
	B:ell(hr[1] * 2, hr[2] * 2, hr[3] * 2, at(hc[1], hc[2], hc[3]), { col = "primary", mat = "cloth", pri = 1.05, role = "head", name = "Foot" })
	for i = 1, (if detail >= 2 then 3 elseif detail >= 1 then 2 else 0) do
		local y = 0.5 + i * 0.62
		B:ell(1.52, 0.3, 1.52, at(0, y, 0.27), { col = "secondary", mat = "cloth", pri = 1.9 + i * 0.1, role = "detail", name = "Stripe" .. i })
	end
	if detail >= 1 then
		B:ell(1.62, 0.5, 1.62, at(0, 0.3, 0.3), { col = "secondary", mat = "cloth", pri = 1.6, role = "detail", name = "Cuff" })
	end
	-- button eyes: flat discs with thread crosses
	for _, side in { 1, -1 } do
		local p = Face.place({ kind = "ellipsoid", c = hc, r = hr }, side * 0.32, 0.22, 0.04)
		B:cyl(0.12, 0.42, Geom.mul(p, at(0, 0, 0, 0, rad(90), 0)), { col = "black", mat = "plastic", pri = 1.1, role = "eye", name = "Button" .. (if side > 0 then "R" else "L"), pair = "eyes", noCore = true })
	end
	local mp = Face.place({ kind = "ellipsoid", c = hc, r = hr }, 0, -0.32, 0.1)
	B:ell(1.1, 0.16, 0.25, mp, { col = "mouth", mat = "cloth", pri = 1.3, role = "mouth", name = "Mouth", noCore = true })
	if has(id, "monster") and detail >= 1 then
		Parts.teeth(B, { bone = "Body", y = mp[2] + 0.06, z = mp[3] - 0.05, r = 0.4, n = 3, h = 0.25, pri = 1.8 })
	end
	B:socket("core", at(0, 1.6, 0), "Body")
	B:setRig("gait", "hop")
end

local BUILD: { [string]: (any, any, string, string) -> () } = {
	slime = buildSlime, slug = buildSlug, snail = buildSnail, bivalve = buildBivalve, cap = buildCap, jelly = buildJelly,
	star = buildStar, urchin = buildUrchin, fuzz = buildFuzz, cube = buildCube, heap = buildHeap, maw = buildMaw,
	elemental = buildElemental, ghost = buildGhost, tube = buildTube, chain = buildChain, bubble = buildBubble,
	bot = buildBot, spirit = buildSpirit,
}

return function(B: any, ctx: any)
	local t, detail = ctx.traits, ctx.detail
	local id = string.lower(ctx.result.id)
	local hint = string.lower((ctx.result.visual and ctx.result.visual.silhouetteHint) or "")
	local food = ctx.kind == "Food" or t.category == "Food"
	local k = foodKind(t, id)
	if not food then
		-- creatures: a listed word builds its sub-kind even when a food word hides in it ("fried egg jellyfish");
		-- otherwise a food trait wins ("pumpkin spirit", "humpty dumpty"), then the silhouette hint picks a sub-kind
		local ck = creatureKind(id, hint, true) or (if k == nil then (creatureKind(id, hint, false) or "slime") else nil)
		if ck then
			BUILD[ck](B, ctx, id, hint)
			return
		end
	end
	local _ = detail
	B.boneIndex.Body.pos = { 0, 1, 0 }
	local fc, fr -- face ellipsoid (when food is rounded)
	k = k or "generic"
	if k == "cake" or k == "cupcake" then
		local cup = k == "cupcake"
		local tiers = if cup or detail <= 1 then 1 else 2
		local y = 0
		local r0 = if cup then 1.0 else 1.6
		if cup then
			B:cyl(1.3, 1.9, at(0, 0.65, 0, 0, 0, rad(90)), { col = "secondary", mat = "plastic", pri = 1, role = "body", name = "Wrapper" })
			B:ell(2.3, 1.7, 2.3, at(0, 1.55, 0), { col = "frosting", mat = "skin", pri = 1.1, role = "body", name = "Frosting" })
			fc, fr = { 0, 0.75, 0 }, { 0.95, 0.65, 0.95 }
			y = 2.3
		else
			for i = 1, tiers do
				local rr = r0 * (1 - (i - 1) * 0.3)
				local h = 1.0
				B:cyl(h, rr * 2, at(0, y + h / 2, 0, 0, 0, rad(90)), { col = "secondary", mat = "skin", pri = 1 + i * 0.05, role = "body", name = "Tier" .. i })
				B:cyl(h * 0.28, rr * 2 + 0.12, at(0, y + h * 0.92, 0, 0, 0, rad(90)), { col = "frosting", mat = "skin", pri = 1.4 + i * 0.1, role = "detail", name = "Icing" .. i })
				if i == 1 then
					fc, fr = { 0, y + h * 0.45, 0 }, { rr, h * 0.48, rr }
				end
				y += h * 1.0
			end
			y += 0.14
		end
		B:ball(0.55, at(0, y + 0.15, 0), { col = "red", mat = "glass", pri = 1.5, role = "detail", name = "Cherry" })
		if detail >= 2 then
			B:limb({ 0, y + 0.35, 0 }, { 0.15, y + 0.85, 0.1 }, 0.08, { col = "leafDark", mat = "wood", pri = 3, role = "detail" }, 0.05)
		end
	elseif k == "pancake" then
		-- a short stack of fluffy discs (each a little smaller and offset), melting butter pat, syrup drip
		local n = if detail <= 1 then 2 else 3
		local y = 0
		for i = 1, n do
			local d = 3.3 - (i - 1) * 0.22
			local ox, oz = ((i % 2) - 0.5) * 0.14, ((i % 3) - 1) * 0.08
			B:cyl(0.5, d, at(ox, y + 0.25, oz, 0, 0, rad(90)), { col = "primary", mat = "skin", pri = 1 + i * 0.1, role = "body", name = "Cake" .. i })
			y += 0.44
		end
		B:ell(2.5, 0.16, 2.5, at(0, y + 0.07, 0), { col = "secondary", mat = "glass", pri = 1.5, role = "detail", name = "Syrup" })
		B:block(0.7, 0.26, 0.7, at(0.1, y + 0.22, -0.05, 0, rad(20), 0), { col = "cream", mat = "skin", pri = 1.7, role = "detail", name = "Butter" })
		if detail >= 2 then
			B:ell(0.32, 0.7, 0.2, at(0.2, y - 0.3, -1.62), { col = "secondary", mat = "glass", pri = 1.9, role = "detail", name = "Drip" })
		end
		flatFace(B, ctx, at(0, 0.5, -1.66), 1.3)
	elseif k == "pie" or k == "pizza" then
		if k == "pizza" then
			-- a slice standing up on its crust, tip up: one big wedge + crust log + toppings
			B:wedge(0.32, 3.0, 2.0, at(0, 1.55, 0, rad(90), 0, 0), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Slice" })
			B:cyl(2.25, 0.62, at(0, 0.3, 0.1), { col = "wood", mat = "skin", pri = 1.1, role = "body", name = "Crust" })
			local tops = if detail >= 2 then 3 else 1
			for i = 1, tops do
				local yy = 0.9 + i * 0.55
				B:cyl(0.12, 0.42 - i * 0.04, at((i % 2 - 0.5) * 0.4 * (1 - i * 0.2), yy, -0.2, 0, rad(90), 0), { col = "secondary", mat = "skin", pri = 1.8 + i * 0.2, role = "detail", name = "Pepperoni" .. i })
			end
			flatFace(B, ctx, at(0, 1.1, -0.17), 1.2)
		else
			B:cyl(0.9, 3.2, at(0, 0.45, 0, 0, 0, rad(90)), { col = "wood", mat = "skin", pri = 1, role = "body", name = "Dish" })
			B:ell(3.0, 0.9, 3.0, at(0, 0.85, 0), { col = "primary", mat = "skin", pri = 1.1, role = "body", name = "Filling" })
			fc, fr = { 0, 0.45, 0 }, { 1.6, 0.45, 1.6 }
		end
	elseif k == "donut" then
		-- torus from a ring of overlapping balls, frosting ring on top, standing on edge
		local n = if detail <= 1 then 6 elseif detail == 2 then 8 else 10
		local R, rr = 1.1, 0.75
		for i = 1, n do
			local a = (i - 1) / n * math.pi * 2
			B:ball(rr * 2, at(sin(a) * R, 1.85 + cos(a) * R, 0), { col = "primary", mat = "skin", pri = 1 + i * 0.01, role = "body", name = "Dough" .. i })
			if detail >= 2 and i % 2 == 0 then
				B:ell(rr * 1.6, rr * 1.6, rr * 0.9, at(sin(a) * R, 1.85 + cos(a) * R, -rr * 0.45), { col = "secondary", mat = "skin", pri = 1.6 + i * 0.01, role = "detail", name = "Frost" .. i })
			end
		end
		flatFace(B, ctx, at(0, 3.0, -rr * 0.8), 1.0)
	elseif k == "burger" then
		B:ell(2.8, 0.7, 2.8, at(0, 0.35, 0), { col = "primary", mat = "skin", pri = 1.05, role = "body", name = "BunLow" })
		B:cyl(0.5, 2.75, at(0, 0.85, 0, 0, 0, rad(90)), { col = "secondary", mat = "skin", pri = 1.1, role = "body", name = "Patty" })
		if detail >= 1 then
			B:ell(3.0, 0.22, 3.0, at(0, 1.13, 0), { col = "leaf", mat = "leaf", pri = 1.5, role = "detail", name = "Lettuce" })
			B:block(2.3, 0.08, 2.3, at(0, 1.17, 0, 0, rad(45), 0), { col = "gold", mat = "skin", pri = 1.7, role = "detail", name = "Cheese" })
		end
		B:ell(2.85, 1.5, 2.85, at(0, 1.45, 0), { col = "primary", mat = "skin", pri = 1, role = "body", name = "BunTop" })
		fc, fr = { 0, 1.62, 0 }, { 1.4, 0.72, 1.4 }
		if detail >= 3 then
			for i = 1, 3 do
				local a = i * 2.1
				B:ell(0.18, 0.08, 0.1, at(sin(a) * 0.6, 2.13, cos(a) * 0.6 + 0.2, 0, a, 0), { col = "cream", mat = "skin", pri = 3.5, role = "detail" })
			end
		end
	elseif k == "icecream" then
		B:limb({ 0, 0.05, 0 }, { 0, 1.9, 0 }, 1.0, { col = "wood", mat = "skin", pri = 1.05, role = "body", name = "Cone" }, 0.02)
		B:ell(1.9, 1.6, 1.9, at(0, 2.3, 0), { col = "secondary", mat = "skin", pri = 1, role = "body", name = "Scoop1" })
		fc, fr = { 0, 2.3, 0 }, { 0.95, 0.8, 0.95 }
		if detail >= 1 then
			B:ell(1.55, 1.3, 1.55, at(0.05, 3.3, 0.05), { col = "primary", mat = "skin", pri = 1.4, role = "body", name = "Scoop2" })
			B:ball(0.4, at(0, 4.05, 0), { col = "red", mat = "glass", pri = 2, role = "detail", name = "Cherry" })
		end
	elseif k == "lollipop" or k == "candy" then
		if k == "lollipop" then
			B:cyl(3.0, 0.2, at(0, 1.5, 0, 0, 0, rad(90)), { col = "white", mat = "plastic", pri = 1.1, role = "body", name = "Stick" })
			B:cyl(0.5, 2.6, at(0, 3.9, 0, 0, rad(90), 0), { col = "primary", mat = "glass", pri = 1, role = "body", name = "Disc" })
			if detail >= 2 then
				B:cyl(0.56, 1.6, at(0, 3.9, 0, 0, rad(90), 0), { col = "secondary", mat = "glass", pri = 2, role = "detail", name = "Swirl" })
			end
			flatFace(B, ctx, at(0, 3.9, -0.28), 1.4)
		else
			B:ell(2.2, 1.5, 1.5, at(0, 1.0, 0), { col = "primary", mat = "glass", pri = 1, role = "body", name = "Candy" })
			B:mwedge(0.9, 1.4, 0.7, at(1.45, 1.0, 0, 0, rad(90), rad(90)), { col = "secondary", mat = "plastic", pri = 1.3, role = "detail", name = "Wrap#" })
			fc, fr = { 0, 1.0, 0 }, { 1.1, 0.75, 0.75 }
		end
	elseif k == "cookie" then
		B:cyl(0.5, 3.0, at(0, 1.6, 0, 0, rad(90), 0), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Cookie" })
		for i = 1, (if detail >= 2 then 4 else 2) do
			local a = i * 1.7
			B:ball(0.4, at(sin(a) * 0.9, 1.6 + cos(a) * 0.9, -0.15), { col = "secondary", mat = "skin", pri = 1.8 + i * 0.1, role = "detail" })
		end
		flatFace(B, ctx, at(0, 1.6, -0.25), 1.5)
	elseif k == "cheese" then
		B:wedge(2.6, 1.6, 2.2, at(0, 0.8, 0, 0, rad(180), 0), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Cheese" })
		for i = 1, (if detail >= 2 then 3 else 1) do
			B:ell(0.5, 0.45, 0.2, at(-0.7 + i * 0.5, 0.45 + (i % 2) * 0.35, -1.1), { col = "dark", mat = "skin", pri = 1.8 + i * 0.1, role = "detail", name = "Hole" .. i })
		end
		flatFace(B, ctx, at(0.3, 0.75, 1.11, 0, math.pi, 0), 1.0)
	elseif k == "croissant" then
		-- crescent of plump rolled segments: fattest in the middle, tapering horns curling forward
		local n = if detail <= 1 then 3 else 5
		for i = 1, n do
			local t0 = (i - 1) / n
			local t1 = i / n
			local a0, a1 = rad(-80 + t0 * 160), rad(-80 + t1 * 160)
			local R = 1.7
			local w = 1.45 * (1 - math.abs((t0 + t1) / 2 - 0.5) * 1.3)
			B:limb({ sin(a0) * R, 1.0, -cos(a0) * R * 0.55 + 0.6 }, { sin(a1) * R, 1.0, -cos(a1) * R * 0.55 + 0.6 }, w,
				{ col = if i % 2 == 0 then "secondary" else "primary", mat = "skin", pri = 1 + math.abs(i - (n + 1) / 2) * 0.08, role = "body", name = "Roll" .. i, depth = w * 0.9 }, 0.3)
		end
		fc, fr = { 0, 1.05, -0.1 }, { 0.75, 0.62, 0.62 }
	elseif k == "nut" then
		-- pointed oval with a seam ridge; acorns get a scaly cap and stalk
		local acorn = string.find(id, "acorn") ~= nil
		B:ell(2.2, 2.9, 2.0, at(0, 1.45, 0), { col = "primary", mat = "wood", pri = 1, role = "body", name = "Shell" })
		B:ell(0.26, 2.92, 2.06, at(0, 1.46, 0), { col = "dark", mat = "wood", pri = 1.3, role = "detail", name = "Seam" })
		if acorn or detail >= 1 then
			B:ell(2.45, 1.3, 2.25, at(0, 2.55, 0), { col = if acorn then "secondary" else "darker", mat = "wood", pri = 1.2, role = "detail", name = "Cap" })
			B:limb({ 0, 3.1, 0 }, { 0.12, 3.6, 0.05 }, 0.22, { col = "bark", mat = "wood", pri = 1.5, role = "detail", name = "Stalk" }, 0.1)
		end
		fc, fr = { 0, 1.35, 0 }, { 1.1, 1.2, 1.0 }
	elseif k == "banana" or k == "carrot" then
		local col = "primary"
		local n = if detail <= 1 then 2 else 3
		for i = 1, n do
			local a0 = rad(-50 + (i - 1) * 100 / n)
			local a1 = rad(-50 + i * 100 / n)
			local R = 2.2
			local w = if k == "carrot" then 1.1 * (1 - (i - 1) * 0.3) else 0.85
			B:limb({ sin(a0) * R, 2.6 - cos(a0) * R * (if k == "carrot" then 0 else 0.6) - (if k == "carrot" then (i - 1) * 1.1 else 0), 0 },
				{ sin(a1) * R, 2.6 - cos(a1) * R * (if k == "carrot" then 0 else 0.6) - (if k == "carrot" then i * 1.1 else 0), 0 }, w,
				{ col = col, mat = "skin", pri = 1 + i * 0.05, role = "body", name = "Seg" .. i }, 0.35)
		end
		if k == "carrot" then
			B:ell(0.9, 1.0, 0.3, at(0, 3.6, 0), { col = "leaf", mat = "leaf", pri = 1.5, role = "detail", name = "Greens" })
		end
		flatFace(B, ctx, at(0, 2.0, -0.45), 0.9)
	else
		-- fruit / egg / bread / pumpkin / generic: one big rounded form with a stem and leaf
		local sx, sy = 2.6, 2.5
		if k == "egg" then
			sx, sy = 2.1, 2.8
		elseif k == "bread" then
			sx, sy = 3.4, 1.8
		elseif k == "pumpkin" or k == "melon" then
			sx, sy = 3.2, 2.4
		end
		B:ell(sx, sy, sx * (if k == "bread" then 0.62 else 1), at(0, sy / 2, 0), { col = "primary", mat = "skin", pri = 1, role = "body", name = "Body" })
		fc, fr = { 0, sy / 2, 0 }, { sx / 2, sy / 2, sx / 2 * (if k == "bread" then 0.62 else 1) }
		if k == "pumpkin" and detail >= 1 then
			B:mell(sx * 0.5, sy * 0.95, sx * 0.62, at(sx * 0.3, sy / 2, 0), { col = "primary", mat = "skin", pri = 1.4, role = "body", name = "Lobe#" })
		end
		if k == "bread" and detail >= 2 then
			for i = 1, 3 do
				B:ell(0.18, 0.12, sx * 0.4, at(-0.9 + i * 0.6, sy * 0.96, 0, 0, rad(30), 0), { col = "secondary", mat = "skin", pri = 2.5 + i * 0.1, role = "detail" })
			end
		end
		if k == "generic" then
			-- an unknown dish: served on a plate with a drizzle band and a garnish leaf so it still reads as food
			B:cyl(0.24, sx * 1.55, at(0, 0.1, 0, 0, 0, rad(90)), { col = "white", mat = "plastic", pri = 1.2, role = "detail", name = "Plate" })
			if detail >= 1 then
				local k2 = math.sqrt(1 - 0.35 ^ 2) * 1.04
				B:ell(sx * k2, sy * 0.16, sx * k2, at(0, sy / 2 + sy * 0.175, 0), { col = "secondary", mat = "skin", pri = 1.4, role = "detail", name = "Drizzle" })
				B:ell(0.8, 0.12, 0.42, at(0.3, sy * 1.0, -0.1, 0, rad(-20), rad(-15)), { col = "leaf", mat = "leaf", pri = 1.7, role = "detail", name = "Garnish" })
			end
		elseif k ~= "egg" and k ~= "bread" then
			B:limb({ 0, sy * 0.92, 0 }, { 0.1, sy * 1.15, 0.05 }, 0.2, { col = "bark", mat = "wood", pri = 1.6, role = "detail", name = "Stem" }, 0.1)
			if detail >= 1 then
				B:ell(0.9, 0.12, 0.45, at(0.45, sy * 1.07, 0, 0, rad(-20), rad(-25)), { col = "leaf", mat = "leaf", pri = 1.7, role = "detail", name = "Leaf" })
			end
		end
		if k == "melon" and detail >= 2 then
			for i = 1, 3 do
				B:ell(sx * 1.02, sy * 1.02, 0.25, at(0, sy / 2, 0, 0, rad(i * 60), 0), { col = "secondary", mat = "skin", pri = 2.2 + i * 0.1, role = "detail" })
			end
		end
	end
	if fc then
		face(B, ctx, fc, fr)
	end
	B:socket("core", at(0, 1.2, 0), "Body")
	B:setRig("gait", "hop")
end
