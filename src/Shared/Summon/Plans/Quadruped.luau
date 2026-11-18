--!strict
-- Quadruped: mammals, reptiles, dragons, dinosaurs on four legs. The body is a horizontal torso (+ deep chest),
-- two-bone legs and a head on a short neck, all proportioned by ARCHETYPE so the animal is recognisable from its
-- silhouette at phone distance:
--   canine (wolf, dog, fox: long snout, tall pointed ears, bushy or up-curled tail)
--   feline (cat, lion, tiger: round head, whisker pads, broad triangle ears, long slim S-curved tail)
--   ursine (bear, panda: heavy, short legs, round ears, light snout, stub tail)
--   equine (horse, deer, zebra: long legs, tall neck, long face angled down, hair tail, mane)
--   bovine (cow, bull, goat, sheep: barrel body, broad pink muzzle, side ears, horns)
--   porcine (pig, boar: low and round, disc snout, flop ears, curly tail)
--   rodent (mouse, rabbit, squirrel: small round body, big head and ears, buck teeth, archetypal tail)
--   pachyderm (elephant, rhino, hippo), reptile (lizards, dragons, dinos), beaked (griffin).
-- Part priorities put the silhouette features (ears, snout, tail) right after the body masses, so a tight budget
-- drops shading layers (chest, belly, inner ears) and never the things that say "wolf" or "cat".

local MeshMap = require(script.Parent.Parent.MeshMap)
local Geom = require(script.Parent.Parent.Geom)
local Parts = require(script.Parent.Parent.Parts)
local Heads = require(script.Parent.Parent.Heads)
local Face = require(script.Parent.Parent.Face)
local Palette = require(script.Parent.Parent.Palette)

local at = Geom.at
local rad = math.rad

-- id word -> archetype (matched on whole words, last word first: "bear cub" -> bear, "sea otter" -> otter)
local WORDS: { [string]: string } = {}
local function add(arch: string, list: string)
	for w in string.gmatch(list, "%S+") do
		WORDS[w] = arch
	end
end
add("canine", "wolf wolves dog dogs puppy pup fox foxes coyote jackal dingo hyena husky malamute retriever labrador shepherd chihuahua dane poodle corgi dachshund pug bulldog beagle dalmatian collie rottweiler doberman pitbull terrier greyhound bernard hound boxer shiba akita samoyed newfoundland chow schnauzer maltese bichon pointer sheepdog spaniel weimaraner vizsla mastiff wolfhound borzoi whippet saluki basenji pekingese papillon havanese westie scottie airedale pyrenees leonberger thylacine dhole mongoose meerkat civet genet fossa aardwolf otter weasel ferret stoat mink marten wolverine badger skunk raccoon coati kinkajou devil quoll tayra grison sable zorilla ringtail olinguito binturong cerberus hellhound werewolf warg fenrir kitsune")
add("feline", "cat cats kitten kitty lion lions lioness tiger tigers leopard jaguar panther cheetah cougar puma lynx bobcat caracal serval ocelot margay jaguarundi tabby siamese persian coon sphynx ragdoll liger tigon manticore sphinx nekomata")
add("ursine", "bear bears panda pandas grizzly koala wombat")
add("equine", "horse horses pony foal mare stallion mustang zebra donkey mule unicorn pegasus okapi deer fawn reindeer moose elk stag doe antelope gazelle impala camel llama alpaca giraffe kirin qilin thoroughbred appaloosa palomino clydesdale quagga addax waterbuck topi hartebeest nyala sitatunga duiker klipspringer steenbok chital pudu blackbuck kudu oryx gnu wildebeest centaur nightmare kelpie sleipnir")
add("bovine", "cow cows bull ox oxen bison buffalo yak goat goats sheep ram lamb calf aurochs takin banteng anoa mouflon ibex tahr serow minotaur")
add("porcine", "pig pigs piglet boar hog hogs warthog tapir")
add("rodent", "mouse mice rat rats hamster gerbil guinea squirrel chipmunk beaver rabbit bunny hare capybara hedgehog porcupine mole shrew vole lemming marmot groundhog gopher chinchilla jerboa dormouse pika degu possum opossum hoglet agouti paca nutria muskrat mara jackalope")
add("pachyderm", "elephant mammoth mastodon rhino rhinoceros hippo hippopotamus")

local function words(id: string): { string }
	local out = {}
	for w in string.gmatch(string.lower(id), "[%a]+") do
		table.insert(out, w)
	end
	return out
end

local function archetype(ctx: any, t: any): string
	if t.arch then
		return t.arch
	end
	if t.dragon or t.dino or t.scaly then
		return "reptile"
	end
	if t.beak then
		return "bird"
	end
	local ws = words(ctx.result.id or "")
	if string.find(string.lower(ctx.result.id or ""), "prairie dog") then
		return "rodent"
	end
	for i = #ws, 1, -1 do
		local w = ws[i]
		local a = WORDS[w] or (#w > 3 and string.sub(w, -1) == "s" and WORDS[string.sub(w, 1, -2)]) or nil
		if a then
			return a
		end
	end
	if t.trunk then
		return "pachyderm"
	elseif t.unihorn then
		return "equine"
	elseif t.mane then
		return "feline"
	elseif t.longEars then
		return "rodent"
	elseif t.horns then
		return "bovine"
	end
	return "canine"
end

local function idHas(id: string, list: string): boolean
	for w in string.gmatch(list, "%S+") do
		if string.find(id, "%f[%a]" .. w) then
			return true
		end
	end
	return false
end

-- body proportions per archetype: length, height, width, leg length, leg width, neck rise/forward, head size
local BODY: { [string]: any } = {
	canine = { L = 2.75, H = 1.0, W = 0.88, leg = 1.15, legW = 0.27, neck = { 0.55, -0.42 }, head = 1.28, foot = "paw" },
	feline = { L = 2.6, H = 0.86, W = 0.8, leg = 1.0, legW = 0.25, neck = { 0.45, -0.32 }, head = 1.3, foot = "paw" },
	ursine = { L = 2.45, H = 1.35, W = 1.28, leg = 0.8, legW = 0.42, neck = { 0.32, -0.32 }, head = 1.15, foot = "paw" },
	equine = { L = 2.6, H = 1.0, W = 0.86, leg = 1.75, legW = 0.23, neck = { 1.25, -0.72 }, head = 1.05, foot = "hoof" },
	bovine = { L = 2.85, H = 1.32, W = 1.2, leg = 1.05, legW = 0.3, neck = { 0.36, -0.5 }, head = 1.12, foot = "hoof" },
	porcine = { L = 2.5, H = 1.25, W = 1.2, leg = 0.62, legW = 0.3, neck = { 0.12, -0.36 }, head = 1.1, foot = "hoof" },
	rodent = { L = 1.95, H = 1.15, W = 1.08, leg = 0.55, legW = 0.28, neck = { 0.22, -0.22 }, head = 1.22, foot = "paw" },
}

return function(B: any, ctx: any)
	local t = ctx.traits
	-- turtles and tortoises have their own build (Plans/Chelonian: shells with scutes, column legs, flippers)
	local Chelonian = require(script.Parent.Chelonian) :: any
	if Chelonian.wants(ctx) then
		return Chelonian.build(B, ctx)
	end
	local rng = B.rng
	local id = string.lower(ctx.result.id or "")
	local arch = archetype(ctx, t)
	t.arch = arch
	local P = BODY[arch]
	local reptile = arch == "reptile"
	local heavy = t.heavy or t.durability >= 8 or t.trunk or t.shell or arch == "pachyderm"
	local bulk = (0.85 + t.durability * 0.045) * rng:jitter(1, 0.05)
	local legLen = (0.95 + t.speed * 0.07) * rng:jitter(1, 0.06)
	if P then
		-- archetype proportions, nudged by stats (fast = a little leggier, tough = a little bulkier)
		bulk = (0.92 + t.durability * 0.016) * rng:jitter(1, 0.04)
		legLen = P.leg * (0.94 + t.speed * 0.012) * rng:jitter(1, 0.04)
	end
	if t.stubby or t.shell then
		legLen *= 0.6
	elseif t.longLegs then
		legLen *= 1.3
	end
	if reptile and not t.dragon then
		legLen *= 0.82
	end
	if t.chubby then
		bulk *= 1.12
	end
	local L = (if P then P.L else 2.4 + (if t.long or t.longTail then 0.4 else 0)) * rng:jitter(1, 0.04)
	local H = (if P then P.H else 1.15) * bulk
	local W = (if P then P.W else 1.05) * bulk * (if heavy and not P then 1.12 else 1)
	local bodyY = legLen + H * 0.36

	B.boneIndex.Body.pos = { 0, bodyY, 0 }
	local detail = ctx.detail
	-- torso: one long mass at low detail; long barrel + deep chest (+ haunch at detail 3)
	if detail <= 1 then
		B:ell(W * 1.04, H * 1.08, L * 1.02, at(0, bodyY + H * 0.03, 0), { col = "primary", mat = "fur", pri = 1, role = "body", name = "Torso" })
	else
		local torso = B:ell(W, H, L * 0.86, at(0, bodyY, 0.04), { col = "primary", mat = "fur", pri = 1, role = "body", name = "Torso" })
		-- deep chest: the shoulders stand a little proud of the back line (a strong read for canines/felines)
		local chest = B:ell(W * 1.06, H * 1.12, L * 0.46, at(0, bodyY + H * 0.05, -L * 0.29, rad(-10), 0, 0), { col = "primary", mat = "fur", pri = 1.55, role = "body", name = "Chest" })
		-- torso + chest + haunch are one sculpt in the torso's unit frame (their layout is fixed in W / H / L)
		B:sculpt(torso, "s_body_quad", { chest })
		if detail >= 3 then
			local haunch = B:ell(W * 1.0, H * 1.02, L * 0.44, at(0, bodyY + H * 0.04, L * 0.3), { col = "primary", mat = "fur", pri = 2.0, role = "body", name = "Haunch" })
			haunch.meshOf = torso
		end
	end
	if detail >= 3 and arch ~= "porcine" then
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
	local legW = if P then P.legW * bulk else 0.34 * bulk * (if heavy then 1.3 else 1)
	local kind = if arch == "pachyderm" or (heavy and not reptile and not P and t.size ~= "Small") then "pillar"
		elseif reptile then "claw"
		elseif P then P.foot
		elseif idHas(id, "horse deer goat cow") or t.unihorn then "hoof"
		else "paw"
	local hipY = legLen + H * 0.05
	local splay = if reptile then W * 0.12 else 0
	local legX = if P then W * 0.3 else W * 0.34
	-- archetype mammals at detail 2 use one tapered mass per leg: the four parts saved go to the face, ears
	-- and tail, which carry the read far more than a knee joint at phone distance
	local legDetail = if P and detail == 2 then 1 else nil
	local panda = idHas(id, "panda") and not string.find(id, "red panda", 1, true)
	local legCol = if panda then "secondary" else nil
	Parts.legPair(B, { col = legCol, detail = legDetail, tag = "F", x = legX, y = hipY, z = -L * 0.3, w = legW, kind = kind, phase = 0, splay = splay, claws = reptile or t.claws, thigh = 1.25 })
	Parts.legPair(B, { col = legCol, detail = legDetail, tag = "B", x = legX * 1.05, y = hipY, z = L * 0.32, w = legW * 1.05, kind = kind, phase = 0.5, splay = splay, claws = reptile or t.claws, thigh = 1.5, bend = if kind == "paw" or kind == "hoof" then 0.6 else nil })

	-- neck + head
	local neckLen = (if t.longNeck then 1.7 else 0.55) * (if reptile then 1.15 else 1)
	local neckBase = { 0, bodyY + H * 0.25, -L * 0.42 }
	local neckTop = { 0, neckBase[2] + neckLen * 0.85, neckBase[3] - neckLen * 0.5 }
	if P then
		local rise, fwd = P.neck[1], P.neck[2]
		if t.longNeck then
			rise, fwd = rise + 1.2, fwd - 0.3
		end
		neckBase = { 0, bodyY + H * 0.22, -L * 0.4 }
		neckTop = { 0, neckBase[2] + rise * bulk, neckBase[3] + fwd }
	end
	B:bone("Neck", "Body", neckBase[1], neckBase[2], neckBase[3])
	B:setRig("neck", "Neck")
	local tallNeck = t.longNeck or arch == "equine"
	if P and not tallNeck and arch ~= "rodent" and arch ~= "porcine" then
		-- short thick neck from inside the chest into the back of the skull: no gap between head and body
		local into = { neckTop[1], neckTop[2] + 0.1, neckTop[3] + 0.12 }
		B:limb({ neckBase[1], neckBase[2] - H * 0.1, neckBase[3] + L * 0.06 }, into, W * (if arch == "feline" then 0.5 else 0.56),
			{ col = "primary", mat = "fur", bone = "Neck", pri = 1.25, role = "body", name = "Neck" }, 0.3)
	elseif tallNeck or (detail >= 2 and not P) then
		B:limb(neckBase, neckTop, W * (if tallNeck then 0.46 else 0.62), { col = "primary", mat = "fur", bone = "Neck", pri = if tallNeck then 1.12 else 1.75, role = "body", name = "Neck" }, 0.35)
	elseif not P then
		-- short-necked at low detail: head sits low on the chest
		neckTop = { 0, neckBase[2] + neckLen * 0.45, neckBase[3] - neckLen * 0.2 }
	end
	B:bone("Head", "Neck", neckTop[1], neckTop[2], neckTop[3])
	B:setRig("head", "Head")
	local headS = if P
		then P.head * (if t.bigHead or t.cute then 1.15 else 1) * (if detail <= 1 then 1.12 else 1) * (0.85 + bulk * 0.15)
		else (1.05 + (if t.bigHead or t.cute then 0.3 else 0) + (if detail <= 1 then 0.2 else 0)) * (0.8 + bulk * 0.2)
	local info
	if t.beak then
		info = Heads.bird(B, { p = neckTop, s = headS }, t)
	elseif reptile then
		info = Heads.reptile(B, { p = neckTop, s = headS * 1.05 }, t)
	elseif P then
		local big = arch == "feline" and (t.mane or idHas(id, "tiger leopard jaguar panther cheetah cougar puma lynx"))
		info = Heads.beast(B, { p = neckTop, s = headS, arch = arch, snoutCol = if panda then "primary" else nil, eyes = if big and not t.cute then "fierce" else nil }, t)
	else
		info = Heads.mammal(B, { p = neckTop, s = headS, long = if kind == "hoof" then 1.6 else 1 }, t)
	end

	-- ears / horns / crest / mane
	if P then
		local A = Heads.Arch[arch]
		local ek = A.ears[1]
		if t.floppyEars then
			ek = "floppy"
		elseif t.longEars or idHas(id, "rabbit bunny hare jackalope") then
			ek = "long"
		elseif arch == "rodent" and idHas(id, "squirrel chipmunk") then
			ek = "pointy"
		elseif arch == "rodent" and idHas(id, "hedgehog beaver capybara guinea hamster porcupine mole") then
			ek = "round"
		end
		local es = headS * (if ek == "long" then 0.62 elseif ek == "floppy" then 0.5 else A.ears[2])
		local ex = if ek == "side" then info.earX * 0.9 elseif ek == "long" then info.earX * 0.6 else info.earX
		Parts.ears(B, { bone = "Head", x = ex, y = info.earY, z = info.earZ, s = es, kind = ek, pri = 1.3, col = if panda then "secondary" else nil })
	elseif not reptile and not t.beak then
		local ek = if t.longEars then "long" elseif t.floppyEars then "floppy" elseif t.roundEars then "round" elseif t.bigEars then "big" else "pointy"
		if t.trunk then
			ek = "big"
		end
		Parts.ears(B, { bone = "Head", x = info.earX, y = info.earY, z = info.earZ, s = headS * (if ek == "big" then 0.95 else 0.42), kind = ek, pri = 1.4 })
	elseif reptile and (t.dragon or t.mythical) then
		Parts.ears(B, { bone = "Head", x = info.earX, y = info.earY, z = info.earZ, s = headS * 0.5, kind = "fin", pri = 3.2 })
	end
	local antlers = t.antlers or idHas(id, "deer reindeer moose elk stag caribou")
	if t.unihorn then
		Parts.horns(B, { bone = "Head", x = 0, y = info.top[2] - headS * 0.05, z = info.c[3] - headS * 0.3, len = headS * 1.1, w = headS * 0.2, kind = "uni", segs = 2, pri = 1.5, col = "gold" })
	elseif antlers and not reptile then
		Parts.antlers(B, { bone = "Head", x = headS * 0.16, y = info.top[2] - headS * 0.05, z = info.top[3], len = headS * 1.25 })
	elseif arch == "bovine" and not idHas(id, "cow calf lamb") or t.horns or t.dragon or (reptile and t.mythical) then
		local hk = if reptile then "swept" elseif idHas(id, "ram sheep mouflon") then "ram" elseif idHas(id, "goat ibex tahr serow") then "swept" else "curved"
		Parts.horns(B, { bone = "Head", x = headS * (if P then 0.3 else 0.24), y = info.top[2] - headS * 0.1, z = info.top[3] + headS * 0.05, len = headS * (0.8 + t.power * 0.05), w = headS * 0.2, kind = hk, segs = if detail <= 1 then 2 else 3, pri = if P then 1.35 else 1.6 })
	end
	if t.mane and (arch ~= "equine" or antlers) then
		-- mane: fluffy collar around the neck root and a ring framing the face (a maned horse gets the crest mane)
		B:ell(W * 1.35, H * 1.05, L * 0.34, at(0, neckBase[2] + 0.2, neckBase[3] - 0.08, rad(-30), 0, 0), { col = "secondary", mat = "fur", bone = "Neck", pri = 1.4, role = "mane" })
		B:ell(headS * 1.45, headS * 1.4, headS * 0.6, at(0, info.c[2] + headS * 0.02, info.c[3] + headS * 0.34), { col = "secondary", mat = "fur", bone = "Head", pri = 1.32, role = "mane" })
	elseif arch == "equine" and not antlers and detail >= 1 then
		-- crest mane along the top of the neck (hair colour), leaning back like it is blowing in the wind
		local a = { neckBase[1], neckBase[2] + W * 0.3, neckBase[3] + W * 0.14 }
		local b = { neckTop[1], neckTop[2] + headS * 0.3, neckTop[3] + headS * 0.26 }
		B:limb(a, b, W * 0.16, { col = "dark", mat = "fur", bone = "Neck", pri = 1.38, role = "mane", name = "Mane", depth = W * 0.5 }, 0.2)
	end
	if t.trunk then
		local m = info.mouth
		local tb = B:bone("Trunk", "Head", m[1], m[2] + headS * 0.1, m[3] + headS * 0.1)
		B:addRig("tail", tb)
		B:limb({ m[1], m[2] + headS * 0.12, m[3] + headS * 0.12 }, { m[1], m[2] - headS * 0.7, m[3] - headS * 0.25 }, headS * 0.3, { col = "primary", mat = "skin", bone = tb, pri = 1.4, role = "trunk" }, 0.2)
		B:limb({ m[1], m[2] - headS * 0.7, m[3] - headS * 0.25 }, { m[1], m[2] - headS * 1.25, m[3] - headS * 0.5 }, headS * 0.22, { col = "primary", mat = "skin", bone = tb, pri = 1.8, role = "trunk", trail = true }, 0.2)
	end
	if t.tusks or (arch == "porcine" and idHas(id, "boar warthog")) then
		local m = info.mouth
		B:mlimb({ headS * 0.22, m[2] + headS * 0.05, m[3] + headS * 0.25 }, { headS * 0.36, m[2] + headS * (if arch == "porcine" then 0.2 else -0.25), m[3] - headS * 0.3 }, headS * 0.12, { col = "tooth", mat = "hard", bone = "Head", pri = 1.9, role = "horn" }, 0.12)
	end
	if idHas(id, "rhino rhinoceros") then
		local m = info.mouth
		B:limb({ 0, m[2] + headS * 0.3, m[3] + headS * 0.05 }, { 0, m[2] + headS * 0.9, m[3] - headS * 0.15 }, headS * 0.26, { col = "horn", mat = "hard", bone = "Head", pri = 1.35, role = "horn", name = "NoseHorn" }, 0.1)
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

	-- coat patterns: the second thing (after the silhouette) that names the animal. Stripes are thin discs whose
	-- rims stand just proud of the torso (radii follow the torso's cross-section at that z, x1.05), spots are
	-- flattened lenses sunk into the flank; both are curved shells of distinct radii, never coplanar.
	if P and detail >= 2 then
		local pc = Palette.hex(ctx.result.visual and ctx.result.visual.primaryColour or "#888888")
		local sc = Palette.hex(ctx.result.visual and ctx.result.visual.secondaryColour or "#222222")
		local markCol = if Palette.luma(pc) - Palette.luma(sc) > 0.25 then "secondary" else "black"
		local rx, ry, rz, cz = W / 2, H / 2, L * 0.43, 0.04
		local function onTorso(z: number): number
			return math.sqrt(math.max(0.05, 1 - ((z - cz) / rz) ^ 2))
		end
		if idHas(id, "tiger zebra okapi bengal tabby quagga liger tigon") then
			local n = if detail >= 3 then 4 else 3
			for i = 1, n do
				local z = cz - rz * 0.55 + (i - 1) / (n - 1) * rz * 1.15
				local k = onTorso(z) * 1.06
				B:ell(rx * 2 * k, ry * 2 * k, L * 0.1, at(0, bodyY + H * 0.03, z, rad(-8 + i * 5), 0, 0),
					{ col = markCol, mat = "fur", pri = 1.48 + i * 0.02, role = "detail", name = "Stripe" .. i })
			end
		elseif idHas(id, "cow calf dalmatian giraffe leopard cheetah jaguar appaloosa fawn ocelot hyena") then
			local spots = { { -0.35, 0.25, 0.42 }, { 0.3, -0.05, 0.34 } }
			for i, sp in spots do
				local z = cz + rz * sp[1]
				local y = bodyY + ry * sp[2]
				local u = math.clamp(((z - cz) / rz) ^ 2 + (sp[2]) ^ 2, 0, 0.9)
				local x = rx * math.sqrt(1 - u)
				local d = (ry + rz) * sp[3] * (if idHas(id, "leopard cheetah jaguar ocelot hyena dalmatian") then 0.55 else 1)
				B:mell(d * 0.3, d, d * 1.2, at(x - d * 0.08, y, z, 0, 0, rad(-12 * sp[2])), { col = markCol, mat = "fur", pri = 1.56 + i * 0.03, role = "detail", name = "Spot" .. i .. "#" })
			end
		end
		if panda then
			-- the panda face: dark tear-drop patches behind each eye
			local E = Heads.Arch.ursine.eyes
			for side = -1, 1, 2 do
				local f = Face.place({ kind = "ellipsoid", c = info.c, r = info.r }, side * headS * E[1], headS * (E[2] - 0.03), headS * 0.05)
				B:part({ shape = "Ellipsoid", size = { headS * 0.34, headS * 0.42, headS * 0.16 }, cf = Geom.mul(f, at(0, 0, 0, 0, 0, rad(-25 * side))),
					col = "secondary", mat = "fur", bone = "Head", pri = 1.14, role = "detail", name = if side > 0 then "PatchR" else "PatchL", pair = "pandaPatch", noCore = true })
			end
		end
	end

	-- tail: the archetype's signature shape
	local tailStart = { 0, bodyY + H * 0.18, L * 0.47 }
	local segsBy = function(n: number): number
		return if detail <= 1 then 1 elseif detail == 2 then math.min(n, 2) else n
	end
	if P then
		local o: any
		if arch == "canine" then
			local bushy = t.bushyTail or t.fluffy or idHas(id, "wolf fox husky malamute samoyed coyote dingo jackal warg fenrir kitsune")
			if bushy then
				o = { dir = { 0, -0.3, 1 }, len = L * 0.58, w = W * 0.3, kind = "bushy", taper = 0.95, droop = -0.18, segs = segsBy(2) }
			else
				o = { dir = { 0, 0.95, 0.65 }, len = L * 0.48, w = W * 0.13, kind = "plain", taper = 0.7, curl = 0.25, segs = segsBy(2) }
			end
		elseif arch == "feline" then
			o = { dir = { 0, 0.3, 1 }, len = L * 0.82, w = W * 0.15, kind = if t.mane then "tuft" else "plain", taper = 0.9, curl = 0.9, segs = segsBy(3), tuftCol = "dark" }
		elseif arch == "ursine" then
			o = { dir = { 0, 0.4, 1 }, len = L * 0.14, w = W * 0.2, kind = "plain", taper = 1, segs = 1 }
		elseif arch == "equine" then
			if antlers or idHas(id, "deer fawn antelope gazelle impala goat") then
				o = { dir = { 0, 0.5, 1 }, len = L * 0.16, w = W * 0.2, kind = "plain", taper = 1, segs = 1, col = "belly" }
			else
				o = { dir = { 0, -0.9, 0.55 }, len = L * 0.55, w = W * 0.2, kind = "bushy", taper = 0.95, segs = segsBy(2), col = "dark" }
			end
		elseif arch == "bovine" then
			o = { dir = { 0, -1, 0.3 }, len = L * 0.4, w = W * 0.06, kind = "tuft", taper = 1, segs = 1, tuftCol = "dark", tuftPri = 2.4 }
		elseif arch == "porcine" then
			o = { dir = { 0, 0.6, 1 }, len = L * 0.2, w = W * 0.07, kind = "plain", taper = 0.9, curl = 1.4, segs = segsBy(2) }
		else -- rodent
			if idHas(id, "rabbit bunny hare jackalope") then
				B:ell(W * 0.36, W * 0.36, W * 0.32, at(0, bodyY + H * 0.12, L * 0.52), { col = "white", mat = "fur", pri = 1.35, role = "tail", name = "Cottontail" })
			elseif idHas(id, "squirrel chipmunk") then
				o = { dir = { 0, 1.5, 0.6 }, len = L * 0.9, w = W * 0.3, kind = "bushy", taper = 0.95, curl = -0.5, segs = segsBy(2) }
			elseif idHas(id, "beaver") then
				o = { dir = { 0, -0.25, 1 }, len = L * 0.5, w = W * 0.5, kind = "plain", taper = 1, segs = 1, flat = 0.25, col = "dark" }
			elseif not idHas(id, "hamster guinea hedgehog capybara mole porcupine") then
				o = { dir = { 0, 0.1, 1 }, len = L * 0.85, w = W * 0.07, kind = "plain", taper = 0.85, curl = 0.3, segs = segsBy(2), col = "inner" }
			end
		end
		if o then
			o.start = tailStart
			o.pri = 0.95
			Parts.tail(B, o)
		end
	else
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
	end

	B:socket("core", at(0, bodyY, 0), "Body")
	B:setRig("gait", if heavy then "heavy" elseif reptile then "sprawl" else "trot")

	-- wolf hero sculpt (catalogue/s_canine.py) for the wild, bushy-tailed canines: trunk with the breast ruff, maned
	-- neck, wolf head with cupped ears, legs with toed paws, brush. Needs the two-segment legs and tail of detail 2+.
	if arch == "canine" and detail >= 2 and idHas(id, "wolf wolves coyote jackal dingo husky malamute warg fenrir werewolf hellhound dhole") then
		local N, lead, named, on = MeshMap.sculptor(B, "wolf")
		local tails = {}
		for _, p in B.parts do
			if p.role == "tail" then
				table.insert(tails, p)
			end
		end
		if N.Torso and N.Neck and #tails == 2 and on("limb", "KneeFR")[1] and on("limb", "KneeBR")[1] then
			for _, m in named("Chest", "Haunch", "Belly") do
				m.pri = 3.2
			end
			lead(N.Torso, "s_wolf_body", named("Chest", "Haunch", "Belly"), 1.3)
			lead(N.Neck, "s_wolf_neck", nil, 1.5)
			for _, tag in { "F", "B" } do
				local suffix = if tag == "F" then "_f" else "_h"
				for _, side in { "R", "L" } do
					lead(on("limb", "Hip" .. tag .. side)[1], "s_wolf_thigh" .. suffix, nil, 1.3)
					lead(on("limb", "Knee" .. tag .. side)[1], "s_wolf_shin" .. suffix, on("foot", "Knee" .. tag .. side))
				end
			end
			if N.Head and N.Snout then
				local inHead = on("ear", N.Head.bone)
				for _, e in inHead do
					e.pri = 3.2
				end
				table.insert(inHead, N.Snout)
				lead(N.Head, "s_wolf_head", inHead)
			end
			lead(tails[1], "s_wolf_tail1", nil, 1.4)
			lead(tails[2], "s_wolf_tail2", nil, 1.4)
		end
	end

	-- horse family hero sculpt (catalogue/s_horse.py): trunk, arched neck, mane of locks, legs with knee, hock and
	-- fetlock, flowing tail; the unicorn adds its spiral horn and pastel locks. Head, ears and hooves keep their own
	-- pieces. Needs the two-segment legs and tail of detail 2+.
	if arch == "equine" and detail >= 2 and (t.unihorn or idHas(id, "horse horses pony foal mare stallion mustang zebra donkey mule unicorn pegasus thoroughbred appaloosa palomino clydesdale quagga nightmare kelpie sleipnir")) then
		local N, lead, named, on = MeshMap.sculptor(B, "horse")
		local tails, horns = {}, {}
		for _, p in B.parts do
			if p.role == "tail" then
				table.insert(tails, p)
			elseif p.role == "horn" then
				table.insert(horns, p)
			end
		end
		if N.Torso and N.Neck and #tails == 2 and on("limb", "KneeFR")[1] and on("limb", "KneeBR")[1] then
			for _, m in named("Chest", "Haunch", "Belly") do
				m.pri = 3.2
			end
			lead(N.Torso, "s_horse_body", named("Chest", "Haunch", "Belly"), 1.3)
			lead(N.Neck, "s_horse_neck", nil, 1.5)
			lead(N.Mane, "s_horse_mane")
			for _, tag in { "F", "B" } do
				local suffix = if tag == "F" then "_f" else "_h"
				for _, side in { "R", "L" } do
					lead(on("limb", "Hip" .. tag .. side)[1], "s_horse_thigh" .. suffix, nil, 1.3)
					lead(on("limb", "Knee" .. tag .. side)[1], "s_horse_shin" .. suffix, nil, 1.3)
				end
			end
			lead(tails[1], "s_horse_tail1", nil, 1.4)
			lead(tails[2], "s_horse_tail2", nil, 1.4)
			if t.unihorn and #horns == 2 then
				horns[2].pri = math.max(horns[2].pri or 2, 3.2)
				lead(horns[1], "s_unicorn_horn", { horns[2] })
			end
		end
	end
end
