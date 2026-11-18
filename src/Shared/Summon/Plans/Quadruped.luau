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
-- generic sub-kinds with their own body + head (later lists win over the broad ones above)
add("mustelid", "otter otters weasel ferret stoat mink marten sable fisher mongoose meerkat civet genet fossa tayra grison binturong ringtail kinkajou olinguito ermine polecat")
add("badger", "badger badgers wolverine skunk zorilla raccoon coati devil quoll tanuki")
add("anteater", "anteater anteaters tamandua numbat")
add("aardvark", "aardvark bilby bandicoot solenodon")
add("armadillo", "armadillo armadillos pangolin pangolins glyptodon doedicurus")
add("spiny", "hedgehog hedgehogs hoglet porcupine porcupines echidna tenrec")
add("pachyderm", "elephant elephants mammoth mastodon deinotherium gomphotherium airavata")
add("rhino", "rhino rhinos rhinoceros arsinoitherium uintatherium megacerops paraceratherium")
add("hippo", "hippo hippos hippopotamus behemoth toxodon")
add("camelid", "camel camels dromedary llama llamas alpaca alpacas vicuna guanaco macrauchenia")
add("macropod", "kangaroo kangaroos wallaby wallabies quokka pademelon potoroo joey procoptodon springhare jerboa")
add("ursine", "sloth sloths megalonyx")
add("porcine", "peccary babirusa entelodont")
-- mythic hybrids on a real body (their extra parts are added in the plan: MYTH below)
add("feline", "pixiu haetae shisa barong nue ammit chimera manticore")
add("bovine", "xiezhi lamassu")

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
	local lid = string.lower(ctx.result.id or "")
	if string.find(lid, "prairie dog") then
		return "rodent"
	elseif string.find(lid, "koala") or string.find(lid, "wombat") then
		return "ursine" -- koala joey, wombat joey
	elseif string.find(lid, "red panda") then
		return "badger" -- ringed tail, masked face
	elseif string.find(lid, "jersey devil") then
		return "equine"
	elseif string.find(lid, "kangaroo rat") then
		return "macropod"
	elseif string.find(lid, "foo dog") then
		return "feline" -- the lion-dog guardian
	elseif string.find(lid, "bai ze") then
		return "bovine"
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
	-- generic sub-kinds: `mesh` is the body sculpt (torso + chest + haunch), `headMesh` the head sculpt (skull + snout)
	mustelid = { L = 2.75, H = 0.8, W = 0.78, leg = 0.5, legW = 0.22, neck = { 0.42, -0.5 }, head = 1.0, foot = "paw", mesh = "s_body_mustelid", headMesh = "s_head_mustelid" },
	badger = { L = 2.55, H = 0.98, W = 1.12, leg = 0.55, legW = 0.3, neck = { 0.22, -0.38 }, head = 1.1, foot = "paw", mesh = "s_body_badger", headMesh = "s_head_badger" },
	anteater = { L = 2.7, H = 1.12, W = 0.8, leg = 0.92, legW = 0.25, neck = { 0.2, -0.55 }, head = 0.9, foot = "paw", mesh = "s_body_anteater", headMesh = "s_head_anteater" },
	aardvark = { L = 2.55, H = 1.12, W = 0.92, leg = 0.75, legW = 0.27, neck = { 0.15, -0.45 }, head = 0.95, foot = "paw", mesh = "s_body_aardvark", headMesh = "s_head_aardvark" },
	armadillo = { L = 2.3, H = 0.95, W = 1.0, leg = 0.42, legW = 0.24, neck = { 0.1, -0.3 }, head = 0.9, foot = "paw", headMesh = "s_head_armadillo" },
	spiny = { L = 2.0, H = 1.1, W = 1.18, leg = 0.36, legW = 0.24, neck = { 0.05, -0.22 }, head = 0.95, foot = "paw", headMesh = "s_head_spiny" },
	pachyderm = { L = 2.55, H = 1.6, W = 1.35, leg = 1.2, legW = 0.5, neck = { 0.12, -0.25 }, head = 1.55, foot = "pillar", mesh = "s_body_pachy", headMesh = "s_head_pachy" },
	rhino = { L = 2.9, H = 1.35, W = 1.25, leg = 0.78, legW = 0.42, neck = { 0.1, -0.42 }, head = 1.2, foot = "pillar", mesh = "s_body_rhino", headMesh = "s_head_rhino" },
	hippo = { L = 2.75, H = 1.42, W = 1.5, leg = 0.5, legW = 0.44, neck = { 0.06, -0.3 }, head = 1.4, foot = "pillar", mesh = "s_body_hippo", headMesh = "s_head_hippo" },
	camelid = { L = 2.3, H = 1.05, W = 0.9, leg = 1.4, legW = 0.24, neck = { 1.15, -0.4 }, head = 1.0, foot = "hoof", headMesh = "s_head_camelid" },
	macropod = { L = 1.9, H = 1.2, W = 1.0, leg = 0.9, legW = 0.3, neck = { 0.2, -0.15 }, head = 0.95, foot = "paw", headMesh = "s_head_macropod" },
}

-- the head-sculpt hook: Heads.beast builds skull + snout primitives, the archetype's unit sculpt contains both (a
-- snout in another colour stays its own part)
local function sculptHead(B: any, id: string?)
	if id == nil then
		return
	end
	local head, members = nil, {}
	for _, p in B.parts do
		if p.bone == "Head" and p.name == "Head" and p.role == "head" then
			head = p
		elseif p.bone == "Head" and p.name == "Snout" and p.col == "primary" then
			table.insert(members, p)
		end
	end
	if head then
		B:sculpt(head, id, members)
	end
end

-- Hopping marsupials (kangaroo, wallaby, quokka ...): sitting tripod posture. Pear-shaped trunk leaning forward
-- over big folded hind legs with long flat feet, small fore-arms held in front of the chest, a thick tail that
-- reaches the ground behind, head with tall ears on a short neck. Both hind legs share one phase (the hop gait).
local function macropod(B: any, ctx: any, t: any, P: any)
	local rng = B.rng
	local detail = ctx.detail
	local id = string.lower(ctx.result.id or "")
	local bulk = (0.92 + t.durability * 0.016) * rng:jitter(1, 0.04)
	local tree = idHas(id, "tree")
	local small = idHas(id, "quokka potoroo pademelon joey jerboa springhare") or t.size == "Tiny"
	local a = P.leg * (0.95 + t.speed * 0.01) * rng:jitter(1, 0.04) * (if tree then 0.8 else 1)
	local L, H, W = P.L * rng:jitter(1, 0.04), P.H * bulk, P.W * bulk
	local hy = a * 0.95
	B.boneIndex.Body.pos = { 0, hy, 0 }
	local lean = rad(if small then -18 else -24)
	local torso = B:ell(W, H * 1.25, L * 0.55, at(0, hy + H * 0.32, 0.18, lean, 0, 0), { col = "primary", mat = "fur", pri = 1, role = "body", name = "Torso" })
	local chest = nil
	if detail >= 1 then
		chest = B:ell(W * 0.82, H * 0.8, L * 0.42, at(0, hy + H * 0.95, -0.12, lean, 0, 0), { col = "primary", mat = "fur", pri = 1.5, role = "body", name = "Chest" })
	end
	B:sculpt(torso, "s_body_macropod", { chest })
	if detail >= 3 then
		B:ell(W * 0.6, H * 0.95, L * 0.3, at(0, hy + H * 0.45, -0.02, lean, 0, 0), { col = "belly", mat = "fur", pri = 2.2, role = "detail", name = "Belly" })
	end
	-- hind legs: thigh folded forward, shin back to the heel, long foot flat on the ground pointing forward
	local x = W * 0.36
	local knee = { x * 1.08, a * 0.42, -0.32 * a }
	local heel = { x, a * 0.12, 0.42 * a }
	local footLen = a * (if small then 0.85 else 1.05)
	if detail <= 0 then
		local hb = B:bone("HipB", "Body", 0, hy, 0.1)
		B:addRig("legs", { hip = hb, side = 0, phase = 0, len = hy })
		B:ell(x * 2 + W * 0.5, hy, footLen * 1.1, at(0, hy * 0.45, 0.05), { col = "primary", mat = "fur", bone = hb, pri = 1.2, role = "limb", name = "LegsB" })
	else
		local hr, hl = B:mirrorBone("HipB#", "Body", x, hy, 0.12)
		local kr, kl = B:mirrorBone("KneeB#", "HipB#", knee[1], knee[2], knee[3])
		B:addRig("legs", { hip = hr, knee = if detail >= 2 then kr else nil, side = 1, phase = 0, len = hy })
		B:addRig("legs", { hip = hl, knee = if detail >= 2 then kl else nil, side = -1, phase = 0, len = hy })
		-- the haunch: a big drumstick from the hip down to the knee
		B:mlimb({ x, hy + W * 0.1, 0.22 }, knee, W * 0.62, { col = "primary", mat = "fur", bone = "HipB#", pri = 1.2, role = "limb", name = "ThighB#" }, 0.3)
		B:mlimb(knee, heel, W * 0.24, { col = "primary", mat = "fur", bone = "KneeB#", pri = 1.3, role = "limb", name = "ShinB#" }, 0.2)
		B:mell(W * 0.3, W * 0.2, footLen, at(heel[1], W * 0.1 + 0.01, heel[3] - footLen * 0.42), { col = "primary", mat = "fur", bone = "KneeB#", pri = 1.35, role = "foot", name = "FootB#" })
	end
	-- fore-arms: short, held bent in front of the chest
	if detail >= 2 then
		local sy, sz = hy + H * 0.98, -0.32
		local arL = H * (if tree then 0.95 else 0.62)
		local ar, al = B:mirrorBone("Arm#", "Body", W * 0.3, sy, sz)
		B:addRig("arms", { arm = ar, side = 1 })
		B:addRig("arms", { arm = al, side = -1 })
		local elbow = { W * 0.36, sy - arL * 0.55, sz - arL * 0.1 }
		local hand = { W * 0.24, sy - arL * 0.72, sz - arL * 0.5 }
		B:mlimb({ W * 0.3, sy, sz }, elbow, W * 0.15, { col = "primary", mat = "fur", bone = "Arm#", pri = 1.6, role = "limb", name = "Arm#" }, 0.25)
		B:mlimb(elbow, hand, W * 0.12, { col = "primary", mat = "fur", bone = "Arm#", pri = 1.7, role = "limb", name = "Fore#" }, 0.25)
	end
	-- tail: thick at the root, reaches the ground behind (the third leg of the tripod)
	local tl = L * (if tree then 1.2 elseif idHas(id, "jerboa springhare") then 1.25 else 1.05)
	local tw = W * (if tree or idHas(id, "jerboa springhare") then 0.17 elseif small then 0.26 else 0.36)
	Parts.tail(B, {
		start = { 0, hy + H * 0.05, 0.62 }, dir = { 0, if tree then -1.1 else -0.42, 1 }, len = tl, w = tw,
		segs = if detail <= 1 then 1 else 2, droop = if tree then 0 else -0.05, kind = if idHas(id, "jerboa springhare") then "tuft" else "plain",
		taper = if tree then 0.9 else 0.55, pri = 0.95, tuftCol = "dark",
	})
	-- head
	local neckBase = { 0, hy + H * 1.22, -0.36 }
	local neckTop = { 0, neckBase[2] + P.neck[1] * bulk, neckBase[3] + P.neck[2] }
	B:bone("Neck", "Body", neckBase[1], neckBase[2], neckBase[3])
	B:setRig("neck", "Neck")
	if detail >= 1 then
		B:limb({ 0, neckBase[2] - H * 0.2, neckBase[3] + 0.1 }, { neckTop[1], neckTop[2] + 0.08, neckTop[3] + 0.1 }, W * 0.42,
			{ col = "primary", mat = "fur", bone = "Neck", pri = 1.25, role = "body", name = "Neck" }, 0.3)
	end
	B:bone("Head", "Neck", neckTop[1], neckTop[2], neckTop[3])
	B:setRig("head", "Head")
	local headS = P.head * (if t.cute or small then 1.15 else 1) * (if detail <= 1 then 1.12 else 1) * (0.85 + bulk * 0.15)
	local info = Heads.beast(B, { p = neckTop, s = headS, arch = "macropod" }, t)
	sculptHead(B, P.headMesh)
	local ek = if idHas(id, "quokka potoroo") then "round" else "pointy"
	local es = headS * (if ek == "round" then 0.36 elseif tree then 0.42 elseif idHas(id, "jerboa") then 0.95 else 0.78) * (if idHas(id, "joey") then 1.1 else 1)
	Parts.ears(B, { bone = "Head", x = info.earX * 0.85, y = info.earY, z = info.earZ, s = es, kind = ek, pri = 1.3 })
	B:socket("core", at(0, hy + H * 0.5, 0), "Body")
	B:setRig("gait", "hop")
end

return function(B: any, ctx: any)
	local t = ctx.traits
	local rng = B.rng
	local id = string.lower(ctx.result.id or "")
	local arch = archetype(ctx, t)
	t.arch = arch
	local P = BODY[arch]
	if arch == "macropod" then
		return macropod(B, ctx, t, P)
	end
	-- mythic hybrids: wings, horns and manes on the real body they borrow
	local manticore = idHas(id, "manticore")
	local chimera = idHas(id, "chimera") and arch == "feline"
	local snakeTail = chimera or idHas(id, "nue")
	if manticore or idHas(id, "pixiu lamassu") then
		t.wings = true
		t.noWings = nil
		t.wingKind = if manticore then "bat" else "feather"
	end
	if idHas(id, "haetae xiezhi pixiu") then
		t.unihorn = true
	end
	if idHas(id, "haetae shisa barong foo pixiu chimera manticore") then
		t.mane = true
	end
	if idHas(id, "cub kit pup kitten") then
		t.mane = nil -- young lions (and the mythic cubs) have no mane yet
	end
	if idHas(id, "qilin kirin haetae") then
		t.armour = true
		t.antlers = idHas(id, "qilin kirin")
	end
	-- armoured / spiny mammals build their own coat (not the turtle shell), elephants always get the trunk
	local armadillo = arch == "armadillo"
	local spiny = arch == "spiny"
	if armadillo or spiny then
		t.shell = nil
	end
	if arch == "pachyderm" then
		t.trunk = true
		t.tusks = not idHas(id, "baby calf") and (t.tusks or idHas(id, "elephant mammoth mastodon deinotherium gomphotherium airavata"))
	end
	local hornless = idHas(id, "baby calf paraceratherium")
	local camel = arch == "camelid" and idHas(id, "camel dromedary macrauchenia")
	local bodyMesh = if P then P.mesh else nil
	if arch == "camelid" and not camel then
		bodyMesh = "s_body_wool"
	end
	local reptile = arch == "reptile"
	local heavy = t.heavy or t.durability >= 8 or t.trunk or t.shell or arch == "pachyderm" or arch == "rhino" or arch == "hippo"
	local bulk = (0.85 + t.durability * 0.045) * rng:jitter(1, 0.05)
	local legLen = (0.95 + t.speed * 0.07) * rng:jitter(1, 0.06)
	if P then
		-- archetype proportions, nudged by stats (fast = a little leggier, tough = a little bulkier)
		bulk = (0.92 + t.durability * 0.016) * rng:jitter(1, 0.04)
		legLen = P.leg * (0.94 + t.speed * 0.012) * rng:jitter(1, 0.04)
	end
	if idHas(id, "glyptodon doedicurus giant") and armadillo then
		bulk *= 1.15
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
		local torso = B:ell(W * 1.04, H * 1.08, L * 1.02, at(0, bodyY + H * 0.03, 0), { col = "primary", mat = "fur", pri = 1, role = "body", name = "Torso" })
		if bodyMesh then
			B:sculpt(torso, bodyMesh)
		end
	else
		local torso = B:ell(W, H, L * 0.86, at(0, bodyY, 0.04), { col = "primary", mat = "fur", pri = 1, role = "body", name = "Torso" })
		-- deep chest: the shoulders stand a little proud of the back line (a strong read for canines/felines)
		local chest = B:ell(W * 1.06, H * 1.12, L * 0.46, at(0, bodyY + H * 0.05, -L * 0.29, rad(-10), 0, 0), { col = "primary", mat = "fur", pri = 1.55, role = "body", name = "Chest" })
		-- torso + chest + haunch are one sculpt in the torso's unit frame (their layout is fixed in W / H / L)
		B:sculpt(torso, bodyMesh or "s_body_quad", { chest })
		if detail >= 3 then
			local haunch = B:ell(W * 1.0, H * 1.02, L * 0.44, at(0, bodyY + H * 0.04, L * 0.3), { col = "primary", mat = "fur", pri = 2.0, role = "body", name = "Haunch" })
			haunch.meshOf = torso
		end
	end
	local skin = arch == "pachyderm" or arch == "rhino" or arch == "hippo"
	if detail >= 3 and arch ~= "porcine" and not skin and not armadillo and not spiny then
		-- belly / chest plate in the secondary colour
		B:ell(W * 0.8, H * 0.62, L * 0.7, at(0, bodyY - H * 0.24, -L * 0.04), { col = "belly", mat = "fur", pri = 2.2, role = "detail", name = "Belly" })
	end

	-- armoured mammals: a banded (armadillo) or scaled (pangolin) dome over the back, glyptodonts a high carapace;
	-- spiny mammals: a quill coat. Fallback bands are rings of distinct radii proud of the dome, never coplanar.
	if armadillo then
		local pangolin = idHas(id, "pangolin")
		local glyp = idHas(id, "glyptodon doedicurus")
		local sw, sh, sl = W * 1.14, H * (if glyp then 1.2 else 0.92), L * (if pangolin then 0.98 else 0.9)
		local sy = bodyY + H * (if glyp then 0.22 else 0.15)
		local shell = B:ell(sw, sh, sl, at(0, sy, 0.03), { col = if pangolin then "primary" else "secondary", mat = "hard", pri = 1.02, role = "body", name = "Shell",
			mesh = if pangolin then "s_shell_pangolin" elseif glyp then "s_shell_glyptodon" else "s_shell_armadillo" })
		if not pangolin and detail >= 2 then
			local n = if detail >= 3 then 3 else 2
			for i = 1, n do
				local z = 0.03 - sl * 0.12 + (i - 1) / math.max(1, n - 1) * sl * 0.24
				local k = math.sqrt(math.max(0.05, 1 - ((z - 0.03) / (sl / 2)) ^ 2)) * 1.035
				local band = B:ell(sw * k, sh * k, sl * 0.07, at(0, sy, z), { col = "dark", mat = "hard", pri = 1.6 + i * 0.05, role = "detail", name = "Band" .. i })
				band.meshOf = shell
			end
		end
	elseif spiny then
		local long = idHas(id, "porcupine")
		B:ell(W * 1.2, H * 1.0, L * 0.98, at(0, bodyY + H * 0.2, 0.06), { col = "secondary", mat = "fur", pri = 1.02, role = "body", name = "Quills",
			mesh = if long then "s_quills_long" else "s_quills" })
	elseif t.shell then
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
	local legCol = if panda or idHas(id, "mink sable") or string.find(id, "red panda", 1, true) then "secondary" elseif idHas(id, "ferret polecat") then "dark" else nil
	local digger = arch == "anteater" or arch == "aardvark" or arch == "armadillo" or arch == "badger" or idHas(id, "sloth megalonyx mole")
	local claws = reptile or t.claws or digger
	local fThigh = if arch == "pachyderm" or arch == "rhino" or arch == "hippo" then 1.08 elseif arch == "camelid" then 1.35 else 1.25
	Parts.legPair(B, { col = legCol, detail = legDetail, tag = "F", x = legX, y = hipY, z = -L * 0.3, w = legW, kind = kind, phase = 0, splay = splay, claws = claws, thigh = fThigh })
	Parts.legPair(B, { col = legCol, detail = legDetail, tag = "B", x = legX * 1.05, y = hipY, z = L * 0.32, w = legW * 1.05, kind = kind, phase = 0.5, splay = splay, claws = reptile or (t.claws and not digger), thigh = if fThigh < 1.2 then 1.15 else 1.5, bend = if kind == "paw" or kind == "hoof" then 0.6 else nil })

	if kind == "pillar" and legDetail == 1 then
		-- one-piece pillar legs (elephant, rhino, hippo): column with foot pad and toenails
		for _, p in B.parts do
			if p.role == "limb" and p.name and string.match(p.name, "^Leg[FB][RL]$") then
				p.mesh = "s_leg_pillar"
			end
		end
	end

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
	if arch == "camelid" and not camel then
		neckTop = { 0, neckBase[2] + 0.95 * bulk, neckBase[3] - 0.32 }
	end
	if camel then
		-- the camel's neck dips forward and rises to the head (llamas carry theirs upright)
		neckTop = { 0, neckBase[2] + 0.95 * bulk, neckBase[3] - 0.95 }
	end
	local tallNeck = t.longNeck or arch == "equine" or arch == "camelid"
	if P and not tallNeck and arch ~= "rodent" and arch ~= "porcine" then
		-- short thick neck from inside the chest into the back of the skull: no gap between head and body
		local into = { neckTop[1], neckTop[2] + 0.1, neckTop[3] + 0.12 }
		B:limb({ neckBase[1], neckBase[2] - H * 0.1, neckBase[3] + L * 0.06 }, into, W * (if arch == "feline" then 0.5 else 0.56),
			{ col = "primary", mat = "fur", bone = "Neck", pri = 1.25, role = "body", name = "Neck" }, 0.3)
	elseif tallNeck or (detail >= 2 and not P) then
		B:limb(neckBase, neckTop, W * (if arch == "camelid" then (if camel then 0.5 else 0.78) elseif tallNeck then 0.46 else 0.62), { col = "primary", mat = "fur", bone = "Neck", pri = if tallNeck then 1.12 else 1.75, role = "body", name = "Neck" }, 0.35)
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
	elseif reptile or idHas(id, "ammit") then
		info = Heads.reptile(B, { p = neckTop, s = headS * 1.05 }, t)
	elseif P then
		local big = arch == "feline" and (t.mane or idHas(id, "tiger leopard jaguar panther cheetah cougar puma lynx"))
		info = Heads.beast(B, { p = neckTop, s = headS, arch = arch, snoutCol = if panda then "primary" else nil, eyes = if big and not t.cute then "fierce" else nil }, t)
		sculptHead(B, P.headMesh)
	else
		info = Heads.mammal(B, { p = neckTop, s = headS, long = if kind == "hoof" then 1.6 else 1 }, t)
	end

	-- ears / horns / crest / mane
	if P and not idHas(id, "ammit") then
		local A = Heads.Arch[arch]
		local ek = A.ears[1]
		if ek == "none" then
			-- elephant ear flaps: broad, thin, hanging down the side of the head and swept back
			local big = if idHas(id, "asian baby") then 0.8 elseif idHas(id, "mammoth woolly") then 0.55 else 1.0
			local es = headS * big
			B:mell(es * 0.14, es * 1.15, es * 0.95, at(info.r[1] * 0.95, info.c[2] - headS * 0.04, info.c[3] + headS * 0.36, rad(-4), rad(-14), rad(-6)),
				{ col = "primary", mat = "skin", bone = "Head", pri = 1.3, role = "ear", name = "EarFlap#", mesh = "s_ear_elephant" })
		elseif t.floppyEars then
			ek = "floppy"
		elseif t.longEars or idHas(id, "rabbit bunny hare jackalope") then
			ek = "long"
		elseif arch == "rodent" and idHas(id, "squirrel chipmunk") then
			ek = "pointy"
		elseif arch == "rodent" and idHas(id, "hedgehog beaver capybara guinea hamster porcupine mole") then
			ek = "round"
		end
		if ek ~= "none" then
			local es = headS * (if ek == "long" then (if arch == "aardvark" then A.ears[2] else 0.62) elseif ek == "floppy" then 0.5 else A.ears[2])
			if arch == "aardvark" and not idHas(id, "aardvark bilby") then
				ek, es = "round", headS * 0.3
			end
			local ex = if ek == "side" then info.earX * 0.9 elseif ek == "long" then info.earX * 0.6 else info.earX
			Parts.ears(B, { bone = "Head", x = ex, y = info.earY, z = info.earZ, s = es, kind = ek, pri = 1.3, col = if panda then "secondary" else nil })
		end
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
	elseif arch == "rhino" or arch == "pachyderm" or arch == "hippo" or arch == "camelid" or armadillo or spiny then
		-- these build their own horns / tusks below (a "horned" hint must not add cattle horns)
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
	if arch == "pachyderm" then
		-- trunk: three ringed segments from the middle of the face, hanging down and curling forward at the tip,
		-- each on its own bone so it sways like a tail
		local c, r = info.c, info.r
		local s = headS
		local pts = { { 0, c[2] - r[2] * 0.3, c[3] - r[3] * 0.8 }, { 0, c[2] - s * 0.72, c[3] - r[3] - s * 0.08 }, { 0, c[2] - s * 1.22, c[3] - r[3] - s * 0.1 }, { 0, c[2] - s * 1.52, c[3] - r[3] - s * 0.36 } }
		local ws = { s * 0.34, s * 0.26, s * 0.18 }
		if detail <= 1 then
			pts = { pts[1], pts[3], pts[4] }
			ws = { s * 0.32, s * 0.2 }
		end
		local parent = "Head"
		for i = 1, #pts - 1 do
			local tb = B:bone("Trunk" .. i, parent, pts[i][1], pts[i][2], pts[i][3])
			B:addRig("tail", tb)
			B:limb(pts[i], pts[i + 1], ws[i], { col = "primary", mat = "skin", bone = tb, pri = 1.28 + i * 0.12, role = "trunk", name = "Trunk" .. i, trail = i == #pts - 1, mesh = "s_trunk_seg" }, 0.22)
			parent = tb
		end
		if t.tusks then
			local mam = idHas(id, "mammoth")
			local deino = idHas(id, "deinotherium")
			local x0 = s * 0.24
			local a = { x0, c[2] - r[2] * 0.42, c[3] - r[3] * 0.72 }
			local b, e
			if deino then
				a = { s * 0.12, c[2] - r[2] * 0.75, c[3] - r[3] * 0.62 }
				b = { s * 0.16, c[2] - s * 0.95, c[3] - r[3] * 0.85 }
				e = { s * 0.13, c[2] - s * 1.2, c[3] - r[3] * 0.35 }
			elseif mam then
				b = { s * 0.42, c[2] - s * 0.95, c[3] - r[3] - s * 0.35 }
				e = { s * 0.16, c[2] - s * 0.45, c[3] - r[3] - s * 1.05 }
			else
				b = { s * 0.32, c[2] - s * 0.85, c[3] - r[3] - s * 0.22 }
				e = { s * 0.26, c[2] - s * 0.72, c[3] - r[3] - s * 0.7 }
			end
			local tw = s * (if mam then 0.17 else 0.13)
			if detail <= 1 then
				B:mlimb(a, e, tw, { col = "tooth", mat = "hard", bone = "Head", pri = 1.9, role = "horn", name = "Tusk#" }, 0.1)
			else
				B:mlimb(a, b, tw, { col = "tooth", mat = "hard", bone = "Head", pri = 1.9, role = "horn", name = "Tusk#" }, 0.1)
				B:mlimb(b, e, tw * 0.8, { col = "tooth", mat = "hard", bone = "Head", pri = 2.3, role = "horn", name = "TuskTip#" }, 0.1)
			end
		end
	elseif t.trunk then
		local m = info.mouth
		local tb = B:bone("Trunk", "Head", m[1], m[2] + headS * 0.1, m[3] + headS * 0.1)
		B:addRig("tail", tb)
		B:limb({ m[1], m[2] + headS * 0.12, m[3] + headS * 0.12 }, { m[1], m[2] - headS * 0.7, m[3] - headS * 0.25 }, headS * 0.3, { col = "primary", mat = "skin", bone = tb, pri = 1.4, role = "trunk" }, 0.2)
		B:limb({ m[1], m[2] - headS * 0.7, m[3] - headS * 0.25 }, { m[1], m[2] - headS * 1.25, m[3] - headS * 0.5 }, headS * 0.22, { col = "primary", mat = "skin", bone = tb, pri = 1.8, role = "trunk", trail = true }, 0.2)
	end
	if arch ~= "pachyderm" and (t.tusks or (arch == "porcine" and idHas(id, "boar warthog babirusa entelodont"))) then
		local m = info.mouth
		B:mlimb({ headS * 0.22, m[2] + headS * 0.05, m[3] + headS * 0.25 }, { headS * 0.36, m[2] + headS * (if arch == "porcine" then 0.2 else -0.25), m[3] - headS * 0.3 }, headS * 0.12, { col = "tooth", mat = "hard", bone = "Head", pri = 1.9, role = "horn" }, 0.12)
	end
	if arch == "rhino" and not hornless then
		-- horns stand on the top of the sloping snout: a big front horn, a smaller one behind it (one in the Indian
		-- rhino), a side-by-side pair in arsinoitherium / megacerops / uintatherium
		local sn = Heads.Arch.rhino.snout
		local s = headS
		local sc = { 0, info.c[2] + s * sn[1], info.c[3] + s * sn[2] }
		local topY = sc[2] + s * sn[4] * 0.8
		if idHas(id, "arsinoitherium megacerops uintatherium") then
			local big = idHas(id, "arsinoitherium")
			B:mlimb({ s * 0.12, topY, sc[3] }, { s * 0.2, topY + s * (if big then 1.05 else 0.55), sc[3] - s * (if big then 0.32 else 0.1) }, s * (if big then 0.26 else 0.2),
				{ col = "horn", mat = "hard", bone = "Head", pri = 1.35, role = "horn", name = "NoseHorn#" }, 0.1)
		else
			B:limb({ 0, topY, sc[3] - s * 0.22 }, { 0, topY + s * 0.95, sc[3] - s * 0.05 }, s * 0.3, { col = "horn", mat = "hard", bone = "Head", pri = 1.35, role = "horn", name = "NoseHorn", mesh = "s_rhino_horn" }, 0.1)
			if not idHas(id, "indian") and detail >= 1 then
				B:limb({ 0, topY + s * 0.02, sc[3] + s * 0.22 }, { 0, topY + s * 0.42, sc[3] + s * 0.3 }, s * 0.22, { col = "horn", mat = "hard", bone = "Head", pri = 1.9, role = "horn", name = "BackHorn", mesh = "s_rhino_horn" }, 0.1)
			end
		end
	end
	if arch == "camelid" then
		if camel then
			-- humps: one (dromedary) or two (bactrian camel)
			local two = not idHas(id, "dromedary macrauchenia")
			local zs = if two then { -L * 0.17, L * 0.15 } else { -L * 0.02 }
			for i, z in zs do
				B:ell(W * 0.62, H * (if two then 0.62 else 0.78), L * (if two then 0.27 else 0.4), at(0, bodyY + H * 0.42, z), { col = "primary", mat = "fur", pri = 1.05 + i * 0.01, role = "body", name = "Hump" .. i, mesh = "s_hump" })
			end
		elseif detail >= 1 then
			-- woolly topknot (alpaca pom-pom, llama fringe)
			B:ell(headS * 0.62, headS * 0.42, headS * 0.55, at(0, info.top[2] - headS * 0.02, info.c[3] + headS * 0.02), { col = "primary", mat = "fur", bone = "Head", pri = 1.5, role = "mane", name = "Topknot", mesh = "s_puff" })
		end
	end

	if chimera and detail >= 2 then
		-- the chimera's goat rising from the middle of the back: neck, head and swept-back ram horns
		local gb = B:bone("GoatNeck", "Body", 0, bodyY + H * 0.38, -L * 0.1)
		local top = { 0, bodyY + H * 1.0, -L * 0.04 }
		B:limb({ 0, bodyY + H * 0.3, -L * 0.12 }, top, W * 0.24, { col = "primary", mat = "fur", bone = gb, pri = 2.2, role = "body", name = "GoatNeck" }, 0.3)
		local gs = W * 0.42
		local hc = { 0, top[2] + gs * 0.15, top[3] - gs * 0.35 }
		B:ell(gs * 0.7, gs * 0.72, gs * 1.25, at(hc[1], hc[2], hc[3], rad(-28), 0, 0), { col = "primary", mat = "fur", bone = gb, pri = 2.3, role = "head", name = "GoatHead", mesh = "s_head_round" })
		B:mball(gs * 0.16, at(gs * 0.3, hc[2] + gs * 0.12, hc[3] - gs * 0.22), { col = "pupil", mat = "glass", bone = gb, pri = 2.5, role = "eye", noCore = true })
		Parts.horns(B, { bone = gb, x = gs * 0.2, y = hc[2] + gs * 0.3, z = hc[3] + gs * 0.15, len = gs * 1.2, w = gs * 0.22, kind = "ram", segs = 2, pri = 2.45 })
	end

	-- wings
	if (t.wings or t.flies) and not t.noWings then
		local span = (L * 0.95 + W) * (if t.dragon then 1.25 else 1)
		Parts.wings(B, { x = W * 0.3, y = bodyY + H * 0.36, z = -L * 0.22, span = span, kind = t.wingKind })
	end

	-- back spikes
	if detail >= 2 and not spiny and not armadillo and (t.spikes or (t.dragon and not t.fluffy)) then
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
		if not armadillo and idHas(id, "tiger zebra okapi bengal tabby quagga liger tigon numbat banded thylacine") then
			local n = if detail >= 3 then 4 else 3
			for i = 1, n do
				local z = cz - rz * 0.55 + (i - 1) / (n - 1) * rz * 1.15
				local k = onTorso(z) * 1.06
				B:ell(rx * 2 * k, ry * 2 * k, L * 0.1, at(0, bodyY + H * 0.03, z, rad(-8 + i * 5), 0, 0),
					{ col = markCol, mat = "fur", pri = 1.48 + i * 0.02, role = "detail", name = "Stripe" .. i })
			end
		elseif idHas(id, "cow calf dalmatian giraffe leopard cheetah jaguar appaloosa fawn ocelot hyena quoll genet civet") then
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
		local A = Heads.Arch[arch]
		if A and (idHas(id, "raccoon ferret polecat tanuki sloth") or string.find(id, "red panda", 1, true)) then
			-- the bandit mask: a dark band across each eye, swept back toward the ear
			local E = A.eyes
			local mcol = if string.find(id, "red panda", 1, true) then "white" elseif idHas(id, "sloth") then "dark" else "black"
			for side = -1, 1, 2 do
				local f = Face.place({ kind = "ellipsoid", c = info.c, r = info.r }, side * headS * E[1] * 1.15, headS * E[2], headS * 0.05)
				B:part({ shape = "Ellipsoid", size = { headS * 0.46, headS * 0.24, headS * 0.16 }, cf = Geom.mul(f, at(0, 0, 0, 0, 0, rad(12 * side))),
					col = mcol, mat = "fur", bone = "Head", pri = 1.14, role = "detail", name = if side > 0 then "MaskR" else "MaskL", pair = "banditMask", noCore = true })
			end
		end
		if idHas(id, "badger skunk zorilla") and info.r then
			-- white blaze from the nose bridge over the crown (badger, skunk)
			local r = info.r
			B:ell(headS * 0.2, r[2] * 2 * 1.04, r[3] * 2 * 1.04, at(0, info.c[2], info.c[3], rad(-14), 0, 0), { col = "white", mat = "fur", bone = "Head", pri = 1.17, role = "detail", name = "Blaze", noCore = true })
		end
		if idHas(id, "skunk zorilla honey") then
			-- skunk back stripe / honey badger mantle: a pale band proud of the back line
			B:ell(W * (if idHas(id, "honey") then 0.9 else 0.42), H * 1.06, L * 0.84, at(0, bodyY + H * 0.04, 0.04), { col = "white", mat = "fur", pri = 1.5, role = "detail", name = "BackStripe" })
		end
		if arch == "anteater" and not idHas(id, "tamandua silky numbat") then
			-- the giant anteater's dark shoulder sash
			local z = -L * 0.2
			local k = onTorso(z) * 1.06
			B:ell(rx * 2 * k, ry * 2 * k, L * 0.12, at(0, bodyY + H * 0.03, z, rad(38), 0, 0), { col = "black", mat = "fur", pri = 1.5, role = "detail", name = "Sash" })
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
		elseif arch == "mustelid" then
			if idHas(id, "otter") then
				o = { dir = { 0, -0.12, 1 }, len = L * 0.6, w = W * 0.36, kind = "plain", taper = 0.5, segs = segsBy(2), flat = 0.62 }
			elseif idHas(id, "genet civet ringtail kinkajou olinguito binturong") then
				o = { dir = { 0, 0.05, 1 }, len = L * 0.78, w = W * 0.24, kind = "plain", taper = 0.8, curl = -0.15, segs = segsBy(3), banded = not idHas(id, "kinkajou olinguito binturong") }
			elseif idHas(id, "marten sable fisher tayra") then
				o = { dir = { 0, 0.1, 1 }, len = L * 0.5, w = W * 0.26, kind = "bushy", taper = 0.8, segs = segsBy(2) }
			elseif idHas(id, "mongoose meerkat fossa grison") then
				o = { dir = { 0, if idHas(id, "meerkat") then 0.5 else -0.1, 1 }, len = L * 0.62, w = W * 0.24, kind = "plain", taper = 0.5, segs = segsBy(2) }
			else -- weasel, stoat, ferret, mink: short tail with a dark tip
				o = { dir = { 0, 0.15, 1 }, len = L * 0.38, w = W * 0.2, kind = "tuft", taper = 0.85, segs = segsBy(2), tuftCol = "dark", tuftPri = 2.6 }
			end
		elseif arch == "badger" then
			if idHas(id, "skunk zorilla") then
				o = { dir = { 0, 1.4, 0.5 }, len = L * 0.72, w = W * 0.34, kind = "bushy", taper = 0.95, curl = -0.45, segs = segsBy(2) }
			elseif idHas(id, "raccoon panda") then
				o = { dir = { 0, -0.05, 1 }, len = L * 0.62, w = W * 0.25, kind = "bushy", taper = 0.92, segs = segsBy(3), banded = true }
			elseif idHas(id, "coati") then
				o = { dir = { 0, 1.6, 0.45 }, len = L * 0.72, w = W * 0.15, kind = "plain", taper = 0.75, curl = -0.2, segs = segsBy(3), banded = true }
			elseif idHas(id, "wolverine tanuki") then
				o = { dir = { 0, -0.2, 1 }, len = L * 0.36, w = W * 0.26, kind = "bushy", taper = 0.9, segs = segsBy(2) }
			elseif idHas(id, "quoll") then
				o = { dir = { 0, 0.1, 1 }, len = L * 0.6, w = W * 0.14, kind = "plain", taper = 0.8, segs = segsBy(2) }
			else -- badgers, tasmanian devil: short thick tail
				o = { dir = { 0, 0.25, 1 }, len = L * 0.22, w = W * 0.2, kind = "plain", taper = 0.7, segs = 1 }
			end
		elseif arch == "anteater" then
			if idHas(id, "tamandua silky") then
				o = { dir = { 0, -0.3, 1 }, len = L * 0.7, w = W * 0.18, kind = "plain", taper = 0.6, curl = -0.35, segs = segsBy(2) }
			else -- the giant anteater's flag tail, numbat brush
				o = { dir = { 0, -0.02, 1 }, len = L * (if idHas(id, "numbat") then 0.55 else 0.72), w = W * 0.4, kind = "bushy", taper = 1, droop = -0.2, segs = segsBy(2), flat = 0.45 }
			end
		elseif arch == "aardvark" then
			o = { dir = { 0, -0.3, 1 }, len = L * 0.6, w = W * (if idHas(id, "aardvark") then 0.34 else 0.16), kind = if idHas(id, "bilby") then "tuft" else "plain", taper = 0.48, segs = segsBy(2), tuftCol = "white" }
		elseif armadillo then
			if idHas(id, "pangolin") then
				o = { dir = { 0, -0.3, 1 }, len = L * 0.82, w = W * 0.48, kind = "plain", taper = 0.62, segs = segsBy(2), flat = 0.5, mesh = "s_tail_pangolin" }
			elseif idHas(id, "glyptodon doedicurus") then
				o = { dir = { 0, -0.15, 1 }, len = L * 0.5, w = W * 0.3, kind = "club", taper = 0.7, segs = segsBy(2), col = "secondary" }
			else
				o = { dir = { 0, -0.35, 1 }, len = L * 0.48, w = W * 0.2, kind = "plain", taper = 0.5, segs = segsBy(2), col = "secondary", mesh = "s_tail_banded" }
			end
			o.start = { 0, bodyY + H * 0.05, L * 0.42 }
		elseif spiny then
			if idHas(id, "porcupine") then
				o = { dir = { 0, 0.1, 1 }, len = L * 0.25, w = W * 0.2, kind = "plain", taper = 0.7, segs = 1, col = "secondary" }
			end
		elseif arch == "pachyderm" or arch == "rhino" then
			o = { dir = { 0, -1, 0.22 }, len = L * (if arch == "rhino" then 0.26 else 0.36), w = W * 0.06, kind = "tuft", taper = 1, segs = 1, tuftCol = "dark", tuftPri = 2.4 }
		elseif arch == "hippo" then
			o = { dir = { 0, -0.6, 1 }, len = L * 0.14, w = W * 0.12, kind = "plain", taper = 0.6, segs = 1, flat = 0.4 }
		elseif arch == "camelid" then
			if camel then
				o = { dir = { 0, -1, 0.25 }, len = L * 0.36, w = W * 0.07, kind = "tuft", taper = 1, segs = 1, tuftCol = "dark", tuftPri = 2.4 }
			else
				o = { dir = { 0, 0.7, 1 }, len = L * 0.16, w = W * 0.22, kind = "bushy", taper = 1, segs = 1 }
			end
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
		if manticore then
			-- scorpion tail arching over the back, ending in the sting
			o = { dir = { 0, 1.2, 0.55 }, len = L * 0.95, w = W * 0.18, kind = "stinger", taper = 0.85, curl = -0.55, segs = segsBy(3), col = "dark" }
		elseif snakeTail then
			o = { dir = { 0, 0.55, 1 }, len = L * 0.8, w = W * 0.15, kind = "plain", taper = 0.9, curl = 0.55, segs = segsBy(3), col = "secondary" }
		elseif idHas(id, "qilin kirin xiezhi") then
			o = { dir = { 0, -0.9, 0.5 }, len = L * 0.45, w = W * 0.07, kind = "tuft", taper = 1, segs = 1, tuftCol = "accent", tuftPri = 2.2 }
		end
		if o then
			o.start = o.start or tailStart
			-- where the tail names the animal (skunk plume, otter rudder, anteater flag) it outranks the ears
			o.pri = if arch == "mustelid" or arch == "badger" or arch == "anteater" or manticore or snakeTail or idHas(id, "pangolin") then 0.78 else 0.95
			local bones, tip = Parts.tail(B, o)
			if snakeTail and detail >= 1 then
				-- the serpent head at the tail tip, looking back over the body
				local hs = W * 0.36
				local last = bones[#bones]
				local hc = { tip[1], tip[2] + hs * 0.15, tip[3] + hs * 0.2 }
				B:ell(hs * 0.8, hs * 0.62, hs * 1.15, at(hc[1], hc[2], hc[3], rad(-25), 0, 0), { col = "secondary", mat = "scale", bone = last, pri = 1.3, role = "head", name = "SnakeHead" })
				if detail >= 2 then
					B:mball(hs * 0.22, at(hs * 0.3, hc[2] + hs * 0.2, hc[3] - hs * 0.05), { col = "eyeGlow", mat = "neon", glow = true, bone = last, pri = 2.6, role = "eye", noCore = true })
				end
			end
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
