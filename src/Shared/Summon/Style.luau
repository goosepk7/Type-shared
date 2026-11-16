--!strict
-- Style pass: turns semantic colour/material keys into concrete values for the two looks, and adds the
-- style-specific layers (Spectral inner cores, rim highlight, trails, wisps, core light; Solid element accents).
-- Pure: output is plain data consumed by Instantiate.

local Palette = require(script.Parent.Palette)
local Geom = require(script.Parent.Geom)

type RGB = Palette.RGB

local Style = {}

-- Solid colour keys -> RGB, derived from the word's own colours.
local function solidColours(r: any, t: any): { [string]: RGB }
	local pc = Palette.hex(r.visual and r.visual.primaryColour or "#9AA5B1")
	local sc = Palette.hex(r.visual and r.visual.secondaryColour or "#E4E7EB")
	-- If the two colours are nearly identical, push the secondary lighter so colour-blocking still reads.
	if math.abs(Palette.luma(pc) - Palette.luma(sc)) < 0.08 then
		sc = Palette.tint(sc, 0.45)
	end
	local ep = Palette.element(r.element or "None", r.visual and r.visual.primaryColour)
	local mech = t.mechanical or t.robot
	local c: { [string]: RGB } = {
		primary = pc,
		secondary = sc,
		dark = Palette.shade(pc, 0.38),
		darker = Palette.shade(pc, 0.6),
		light = Palette.tint(pc, 0.3),
		accent = Palette.shade(sc, 0.12),
		inner = Palette.lerp(Palette.tint(sc, 0.25), { 1, 0.72, 0.75 }, if t.mammal then 0.35 else 0),
		belly = Palette.tint(sc, 0.15),
		membrane = Palette.lerp(Palette.shade(pc, 0.15), sc, 0.45),
		wingTip = Palette.shade(pc, 0.25),
		horn = if t.frozen then Palette.hex("#DDF4FF") elseif mech then Palette.hex("#3A3F47") else Palette.hex("#EFE3C8"),
		claw = Palette.hex("#2B2622"),
		tooth = Palette.hex("#FFF8E8"),
		nail = Palette.hex("#D9CDB4"),
		hoof = Palette.hex("#3B2F2A"),
		beak = Palette.hex("#F2A93B"),
		eyeWhite = Palette.hex("#FFFFFF"),
		pupil = Palette.hex("#15131A"),
		iris = if r.element ~= "None" then Palette.shade(ep.outer, 0.15) else Palette.hex("#E8B423"),
		shine = Palette.hex("#FFFFFF"),
		eyeGlow = if r.element ~= "None" then ep.core else Palette.tint(sc, 0.5),
		bugEye = Palette.shade(sc, 0.55),
		wingGlass = Palette.tint(sc, 0.6),
		gem = if r.element ~= "None" then ep.main else Palette.saturate(sc, 1.3),
		glow = if r.element ~= "None" then ep.main else Palette.saturate(Palette.tint(sc, 0.3), 1.4),
		flame = Palette.hex("#FF8A1F"),
		flameCore = Palette.hex("#FFE7A3"),
		metal = Palette.hex("#A7B1BC"),
		steel = Palette.hex("#7C8794"),
		gunmetal = Palette.hex("#3C434C"),
		gold = Palette.hex("#E8B53A"),
		wood = Palette.hex("#8A5A33"),
		darkWood = Palette.hex("#5A3820"),
		stone = Palette.lerp(Palette.hex("#A39E93"), pc, 0.15),
		darkStone = Palette.lerp(Palette.hex("#6E6A62"), pc, 0.12),
		roof = Palette.shade(sc, 0.2),
		glass = Palette.hex("#9FD8F2"),
		tyre = Palette.hex("#24262B"),
		leaf = Palette.hex("#4E9A3A"),
		leafDark = Palette.hex("#2F6E2A"),
		bark = Palette.hex("#6B4A2E"),
		skin = Palette.hex("#F1C29A"),
		hair = Palette.hex("#5A3A24"),
		cloth = pc,
		cloth2 = sc,
		white = Palette.hex("#F7F7F7"),
		black = Palette.hex("#1D1D22"),
		red = Palette.hex("#D9372B"),
		sail = Palette.hex("#F3ECDD"),
		cream = Palette.hex("#FFF3D6"),
		frosting = Palette.tint(sc, 0.2),
		mouth = Palette.hex("#3B1820"),
		tongue = Palette.hex("#E8607A"),
		blush = Palette.hex("#FF8FA3"),
	}
	return c
end

local FACE_KEYS: { [string]: boolean } = { eyeWhite = true, pupil = true, iris = true, shine = true, mouth = true, tongue = true, tooth = true, blush = true, eyeGlow = true, bugEye = true }

local PRESET2: { [string]: string } = {
	Fire = "embers", Ice = "frost", Lightning = "sparks", Poison = "bubbles", Shadow = "smoke", Arcane = "runes",
	Light = "glints", Nature = "leaves", Water = "droplets", Wind = "streaks", Earth = "dust", Metal = "glints",
}

local SOLID_MATERIALS: { [string]: string } = {
	skin = "SmoothPlastic", scale = "SmoothPlastic", fur = "SmoothPlastic", hard = "SmoothPlastic", plastic = "Plastic",
	metal = "Metal", wood = "Wood", cloth = "Fabric", glass = "Glass", stone = "Slate", leaf = "SmoothPlastic",
	neon = "Neon", rubber = "SmoothPlastic", ice = "Ice", sand = "Sand", foil = "Foil",
}

local function spectralColour(key: any, ep: Palette.ElementPalette): RGB
	if key == "eyeWhite" or key == "shine" or key == "eyeGlow" or key == "tooth" or key == "flameCore" then
		return ep.core
	elseif key == "pupil" or key == "iris" or key == "bugEye" or key == "mouth" then
		return ep.deep
	elseif key == "secondary" or key == "accent" or key == "horn" or key == "claw" or key == "nail" or key == "beak"
		or key == "gem" or key == "glow" or key == "gold" or key == "inner" or key == "flame" or key == "tongue" or key == "blush" then
		return ep.glow
	elseif key == "dark" or key == "darker" or key == "black" or key == "tyre" or key == "gunmetal" or key == "hoof" or key == "darkStone" or key == "darkWood" then
		return ep.deep
	elseif key == "membrane" or key == "wingGlass" or key == "wingTip" or key == "sail" then
		return ep.main
	end
	return ep.outer
end

-- Resolve every part to concrete colour/material/transparency; add the style layers.
-- Returns extra parts (cores) to be budgeted together with the geometry, and FX lists.
function Style.apply(bp: any, B: any, r: any, t: any, style: string, cfg: any)
	local parts = B.parts
	local fx = { emitters = {}, trails = {}, lights = {}, highlight = nil }
	-- split element ("fire ice dragon"): the left half (and alternating centre details) take the second element
	local ep2: any = nil
	local second = r.secondaryElement
	if second and second ~= "None" and second ~= r.element then
		ep2 = Palette.element(second, nil)
	end
	local width = 0
	for _, p in parts do
		width = math.max(width, math.abs(p.cf[1]))
	end
	local function splitSide(p: any): boolean
		local x = p.cf[1]
		if x < -width * 0.08 then
			return true
		elseif x <= width * 0.08 then
			return (p.pri or 2) >= 2 and (p.id or 0) % 2 == 0
		end
		return false
	end
	if style == "Spectral" then
		local ep = Palette.element(r.element or "None", r.visual and r.visual.primaryColour)
		local extra = {}
		for _, p in parts do
			local key = p.col
			local role = p.role
			local isEye = role == "eye" or role == "pupil" or role == "shine" or role == "gem" or p.glow
			local pep = if ep2 and splitSide(p) then ep2 else ep
			p.colour = if type(key) == "table" then key else spectralColour(key, pep)
			if p.mcol then
				-- material look carried into energy: glowing noodle strands, glowing bricks
				p.colour = Palette.lerp(p.colour, Palette.tint(p.mcol, 0.25), 0.4)
			end
			if role == "pupil" or (role == "mouth" and (key == "mouth" or key == "pupil")) or key == "pupil" then
				-- the face must read on glowing energy: pupils, nostrils and mouth cavities are solid deep ink
				p.colour = Palette.shade(pep.deep, 0.55)
				p.material = "SmoothPlastic"
				p.transparency = 0
			elseif isEye then
				p.material = "Neon"
				p.transparency = 0
			elseif (p.pri or 2) <= 1.3 and not p.noCore and (role == "body" or role == "head" or role == "core" or role == "torso") then
				-- big masses: shimmering energy shell around a brighter inner core of strictly smaller size
				p.material = "ForceField"
				p.transparency = 0
				local s = p.size
				local k = cfg.SpectralCoreScale
				-- Block/Cylinder cores share the shell's shape; everything else gets an ellipsoid core. A wedge's
				-- slope passes through its box centre, so its core sits at the wedge centroid instead.
				local shape = if p.shape == "Block" or p.shape == "Cylinder" then p.shape else "Ellipsoid"
				local ccf = p.cf
				-- round masses (planets, orbs, heads) carry surface detail: a smaller core keeps it readable
				local ck = if p.shape == "Ball" then k * 0.78 else k
				if p.shape == "Wedge" then
					ccf = Geom.offset(p.cf, 0, -s[2] / 6, s[3] / 6)
					ck = k * 0.6
				end
				local core = {
					shape = shape,
					size = { s[1] * ck, s[2] * ck, s[3] * ck },
					cf = ccf,
					bone = p.bone,
					pri = (p.pri or 1) + 0.9,
					role = "core",
					colour = Palette.lerp(ep.core, ep.main, 0.2),
					material = "Neon",
					transparency = 0.4,
					noCore = true,
					name = (p.name or "Part") .. "Core",
				}
				table.insert(extra, core)
			else
				p.material = "Neon"
				-- deeper detail gets more transparent: layered energy rather than a solid neon lump
				local pri = p.pri or 2
				p.transparency = math.clamp(0.22 + (pri - 1) * 0.08, 0.22, 0.55)
				if p.colour == pep.outer then
					-- limbs and secondary masses sit a value step below the cores: the light hierarchy is
					-- core > eyes/accents > shells > limbs, so the summon reads as one glowing body, not a pile of bulbs
					p.colour = Palette.lerp(pep.outer, pep.deep, 0.3)
				end
				if role == "wing" or role == "petal" or role == "fin" then
					p.transparency = math.max(p.transparency, 0.35)
					p.material = if role == "wing" and (pri or 2) < 2 then "Neon" else "ForceField"
				end
			end
			if p.tr ~= nil then
				p.transparency = math.max(p.transparency, p.tr)
			end
			p.castShadow = false
		end
		-- aura: one extra outer shell on the biggest torso mass (strictly larger radii on every axis), so the body
		-- reads as layered energy (aura > shell > core) rather than a single glowing surface
		local big, bigV = nil, 0
		for _, p in parts do
			if p.material == "ForceField" and p.role == "body" and (p.shape == "Ellipsoid" or p.shape == "Ball") then
				local v = p.size[1] * p.size[2] * p.size[3]
				if v > bigV then
					big, bigV = p, v
				end
			end
		end
		if big then
			local s = big.size
			table.insert(extra, {
				shape = big.shape, size = { s[1] * 1.14, s[2] * 1.14, s[3] * 1.1 }, cf = big.cf, bone = big.bone,
				pri = (big.pri or 1) + 1.2, role = "aura", colour = ep.glow, material = "ForceField", transparency = 0.55,
				noCore = true, name = (big.name or "Part") .. "Aura",
			})
		end
		for _, c in extra do
			table.insert(parts, c)
		end
		fx.highlight = cfg.SpectralHighlight and {
			fill = ep.main, fillTransparency = 0.82, outline = ep.glow, outlineTransparency = 0.15,
		} or nil
		-- core light
		table.insert(fx.lights, { kind = "PointLight", colour = ep.glow, brightness = 1.6, range = 1.6, socket = "core", shadows = false })
		-- emitters: wisps rising off the body, element motes, and a request from the plan if any
		table.insert(fx.emitters, { preset = "wisps", colour = { ep.main, ep.deep }, rate = 14, socket = "core", spread = 1 })
		local elementPreset = ({
			Fire = "embers", Ice = "frost", Lightning = "sparks", Water = "bubbles", Earth = "dust", Wind = "streaks",
			Nature = "leaves", Light = "glints", Shadow = "smoke", Poison = "bubbles", Metal = "glints", Arcane = "runes",
		} :: any)[r.element or "None"] or "glints"
		table.insert(fx.emitters, { preset = elementPreset, colour = { ep.core, ep.glow }, rate = 10, socket = "core", spread = 1 })
		if ep2 then
			table.insert(fx.emitters, { preset = PRESET2[second] or "glints", colour = { ep2.core, ep2.glow }, rate = 10, socket = "core", spread = 1 })
		end
		for _, e in B.emitters do
			table.insert(fx.emitters, { preset = e.preset, colour = { ep.core, ep.main }, rate = e.rate or 20, socket = e.socket, part = e.part, spread = e.spread or 0.4 })
		end
		-- trails on extremities
		for _, p in parts do
			if p.trail then
				table.insert(fx.trails, { part = p.name, pri = p.pri or 2, colour = { ep.core, ep.main, ep.deep }, lifetime = 0.35 })
			end
		end
	else
		local cols = solidColours(r, t)
		local ep = Palette.element(r.element or "None", r.visual and r.visual.primaryColour)
		for _, p in parts do
			local key = p.col
			p.colour = if type(key) == "table" then key else (cols[key] or cols.primary)
			p.material = if p.glow then "Neon" else (SOLID_MATERIALS[p.mat or "skin"] or "SmoothPlastic")
			if t.mechanical and (p.mat == "skin" or p.mat == "hard") and (p.role == "body" or p.role == "limb" or p.role == "head") then
				p.material = "Metal"
			end
			if ep2 and splitSide(p) and type(key) == "string" and not FACE_KEYS[key] then
				-- split element: tint the second-element half toward its palette, keeping light/dark structure
				local target = if Palette.luma(p.colour) < 0.3 then ep2.deep else ep2.main
				p.colour = Palette.lerp(p.colour, target, 0.7)
			end
			if p.mcol then
				p.colour = p.mcol
			end
			if p.mrbx then
				p.material = p.mrbx
			end
			if p.mglow then
				p.material = "Neon"
			end
			p.transparency = p.tr or 0
			p.castShadow = (p.pri or 2) < 2.5
		end
		-- dark dot eyes on a dark head vanish (ninja, shadow, black cat): swap them for bright catch-light eyes
		local head, hv = nil, 0
		for _, p in parts do
			if p.role == "head" or p.role == "body" then
				local v = p.size[1] * p.size[2] * p.size[3]
				if v > hv and p.transparency < 0.5 then
					head, hv = p, v
				end
			end
		end
		if head then
			local hl = Palette.luma(head.colour)
			for _, p in parts do
				if p.role == "eye" and (p.col == "pupil" or p.col == "bugEye") and math.abs(Palette.luma(p.colour) - hl) < 0.22 then
					p.colour = if hl < 0.28 then { 0.97, 0.95, 0.88 } else { 0.06, 0.05, 0.08 }
				end
			end
		end
		-- glowing eyes for elemental creatures that already asked for glow eyes (handled by the plan via kind="glow")
		if r.element and r.element ~= "None" then
			local preset = ({
				Fire = "embers", Ice = "frost", Lightning = "sparks", Poison = "bubbles", Shadow = "smoke", Arcane = "runes",
				Light = "glints", Nature = "leaves", Water = "droplets", Wind = "streaks", Earth = "dust", Metal = "glints",
			} :: any)[r.element]
			if preset then
				table.insert(fx.emitters, { preset = preset, colour = { ep.core, ep.main }, rate = 8, socket = "core", spread = 1 })
			end
		end
		if ep2 then
			table.insert(fx.emitters, { preset = PRESET2[second] or "glints", colour = { ep2.core, ep2.main }, rate = 8, socket = "core", spread = 1 })
		end
		for _, e in B.emitters do
			table.insert(fx.emitters, { preset = e.preset, colour = { cols.flameCore, cols.flame }, rate = e.rate or 20, socket = e.socket, part = e.part, spread = e.spread or 0.4 })
		end
		-- plan-requested lights (e.g. rocket flame, lantern)
		for _, l in B.lights do
			table.insert(fx.lights, l)
		end
	end
	bp.fx = fx
end

-- Resolve emitter/trail/light budgets (after part budget, because trails need surviving parts).
function Style.budgetFx(bp: any, style: string, cfg: any)
	local fx = bp.fx
	local kept = {}
	local maxE = if style == "Spectral" then cfg.EmitterBudget.Spectral else cfg.EmitterBudget.Solid
	-- plan-requested emitters first (they are the iconic ones: rocket flame), then element, then wisps
	local ordered = {}
	for i = #fx.emitters, 1, -1 do
		table.insert(ordered, fx.emitters[i])
	end
	for _, e in ordered do
		if #kept < maxE then
			e.rate = math.min(e.rate, cfg.MaxParticleRate)
			table.insert(kept, e)
		end
	end
	fx.emitters = kept
	local names: { [string]: boolean } = {}
	for _, p in bp.parts do
		names[p.name] = true
	end
	local trails = {}
	table.sort(fx.trails, function(a, b)
		if a.pri ~= b.pri then
			return a.pri < b.pri
		end
		return a.part < b.part
	end)
	for _, tr in fx.trails do
		if names[tr.part] and #trails < cfg.MaxTrails then
			table.insert(trails, tr)
		end
	end
	fx.trails = trails
	local lights = {}
	for _, l in fx.lights do
		if #lights < cfg.MaxLights then
			table.insert(lights, l)
		end
	end
	fx.lights = lights
	return fx
end

Style.solidColours = solidColours
Style._geom = Geom

return Style
