--!strict
-- Element palettes: the ONE place element colours and materials live. Pure Luau (hex strings, material names);
-- the runtime converts to Color3 / Enum.Material.
--
-- Each ramp has 5 stops, brightest -> darkest:
--   1 core (white-hot centre)  2 bright  3 main (the element's identity colour)  4 deep  5 shade (smoke/edges)
-- Spectral = glowing magic energy (used with Neon parts, LightEmission particles).
-- Solid    = natural stylized colours (used with real materials, lit particles).

local Palettes = {}

export type Style = "Spectral" | "Solid"
export type Ramp = { string }

local SPECTRAL: { [string]: Ramp } = {
	Fire = { "#FFF6D5", "#FFD45A", "#FF8A1F", "#E8401C", "#7A1308" },
	Water = { "#E6FBFF", "#7FE3FF", "#1EA7FF", "#1660D9", "#0B2A6B" },
	Ice = { "#FFFFFF", "#D6F7FF", "#8FDFFF", "#4FB3E8", "#24618F" },
	Lightning = { "#FFFFFF", "#FDF8B0", "#FFE14D", "#B794FF", "#4B2A9E" },
	Earth = { "#FFF0C9", "#F2C46B", "#C98A3A", "#8A5A2B", "#3E2614" },
	Wind = { "#FFFFFF", "#E2FFF6", "#A6F5DC", "#5FD3B5", "#2C7F74" },
	Nature = { "#F4FFD6", "#B8F55A", "#5CD63A", "#2F9A3A", "#14501F" },
	Light = { "#FFFFFF", "#FFFBE0", "#FFE9A3", "#FFC857", "#B5862A" },
	Shadow = { "#E2C9FF", "#9A5CFF", "#5B2BB5", "#2A1259", "#0C0418" },
	Poison = { "#F3FFC8", "#BDFF2E", "#6FD62A", "#7A3FB0", "#2D1145" },
	Metal = { "#FFFFFF", "#E4ECF5", "#A9B8C9", "#6B7C91", "#2E3846" },
	Arcane = { "#FFE9FF", "#FF9CF3", "#D54CFF", "#7A2CFF", "#2A0E6B" },
	None = { "#FFFFFF", "#FFD6FF", "#C77DFF", "#7B5CFF", "#2E1A66" },
}

local SOLID: { [string]: Ramp } = {
	Fire = { "#FFE7A3", "#FFB547", "#F26B1D", "#B83A12", "#3B1A12" },
	Water = { "#DFF6FF", "#8CCFF0", "#3F93C9", "#22618F", "#14334D" },
	Ice = { "#F7FDFF", "#CFEFFA", "#9ED6EE", "#6AA9C9", "#3B6E8A" },
	Lightning = { "#FFFFFF", "#FFF5C2", "#FFE066", "#8C7BD1", "#3A3366" },
	Earth = { "#D9C2A0", "#B08D62", "#8A6A47", "#5E4630", "#3A2B1F" },
	Wind = { "#F5FAFA", "#DDEBEA", "#B9D3D0", "#8FB2AE", "#5E7F7B" },
	Nature = { "#E8F5B5", "#9CCF4F", "#5E9E36", "#3D6E2A", "#25401B" },
	Light = { "#FFFFF4", "#FFF3C4", "#FFE08A", "#E8B852", "#9C7A33" },
	Shadow = { "#8E7AA6", "#5E4C78", "#3D3152", "#251E33", "#121019" },
	Poison = { "#E3F5A6", "#A6D63B", "#6A9E2B", "#5B3A70", "#2A1F33" },
	Metal = { "#F0F3F6", "#C5CDD6", "#8F9AA6", "#5D6670", "#33393F" },
	Arcane = { "#F6E3FF", "#D9A6FF", "#A66BE0", "#6B3FA8", "#2E1F4D" },
	None = { "#FFFFFF", "#F3E6FF", "#C9B3E6", "#8A79A8", "#4A4059" },
}

-- Smoke / ash tint used by explosions and fires (Solid uses real smoke; Spectral uses tinted haze).
local SMOKE = { Spectral = "#3A2F4F", Solid = "#4A4442" }

-- Materials by role. "core" = brightest inner part, "shell" = outer layer, "body" = solid mass (rocks, walls),
-- "debris" = flying chunks. Spectral always uses Neon/ForceField energy.
local SOLID_MATERIALS: { [string]: { [string]: string } } = {
	Fire = { core = "Neon", shell = "Neon", body = "Basalt", debris = "Basalt" },
	Water = { core = "Glass", shell = "Glass", body = "Glass", debris = "Glass" },
	Ice = { core = "Glass", shell = "Ice", body = "Ice", debris = "Ice" },
	Lightning = { core = "Neon", shell = "Neon", body = "Slate", debris = "Slate" },
	Earth = { core = "Slate", shell = "Rock", body = "Slate", debris = "Rock" },
	Wind = { core = "Glass", shell = "Glass", body = "SmoothPlastic", debris = "SmoothPlastic" },
	Nature = { core = "LeafyGrass", shell = "Grass", body = "Wood", debris = "WoodPlanks" },
	Light = { core = "Neon", shell = "Glass", body = "Marble", debris = "Marble" },
	Shadow = { core = "SmoothPlastic", shell = "Glass", body = "Basalt", debris = "Basalt" },
	Poison = { core = "Glass", shell = "Glass", body = "Slate", debris = "Slate" },
	Metal = { core = "Metal", shell = "DiamondPlate", body = "Metal", debris = "CorrodedMetal" },
	Arcane = { core = "Neon", shell = "Glass", body = "Marble", debris = "Marble" },
	None = { core = "Neon", shell = "Glass", body = "SmoothPlastic", debris = "SmoothPlastic" },
}
local SPECTRAL_MATERIALS = { core = "Neon", shell = "Neon", body = "Neon", debris = "Neon", field = "ForceField" }

-- Solid: elements whose particles are self-lit even in Solid style (fire glows, lightning glows...).
local EMISSIVE = { Fire = true, Lightning = true, Light = true, Arcane = true, None = true }

-- Signature particles for each element (Presets ids). Generic effects (impact, aura, explosion...) layer these
-- so every element has a recognisable character.
local ELEMENT_FX: { [string]: { primary: string, secondary: string, burst: string, ambient: string } } = {
	Fire = { primary = "fire", secondary = "embers", burst = "sparks", ambient = "smoke" },
	Water = { primary = "splash", secondary = "bubbles", burst = "droplets", ambient = "mist" },
	Ice = { primary = "frostMist", secondary = "snow", burst = "iceShards", ambient = "frostMist" },
	Lightning = { primary = "electric", secondary = "sparks", burst = "sparks", ambient = "motes" },
	Earth = { primary = "dust", secondary = "pebbles", burst = "pebbles", ambient = "dust" },
	Wind = { primary = "windStreaks", secondary = "leavesDrift", burst = "windStreaks", ambient = "windStreaks" },
	Nature = { primary = "leaves", secondary = "pollen", burst = "leaves", ambient = "pollen" },
	Light = { primary = "stars", secondary = "motes", burst = "stars", ambient = "motes" },
	Shadow = { primary = "wisps", secondary = "darkMotes", burst = "wisps", ambient = "wisps" },
	Poison = { primary = "toxicBubbles", secondary = "toxicGas", burst = "toxicSplash", ambient = "toxicGas" },
	Metal = { primary = "metalSparks", secondary = "glints", burst = "metalSparks", ambient = "glints" },
	Arcane = { primary = "runes", secondary = "motes", burst = "stars", ambient = "runes" },
	None = { primary = "glitter", secondary = "motes", burst = "glitter", ambient = "glitter" },
}

Palettes.Elements = { "Fire", "Water", "Ice", "Lightning", "Earth", "Wind", "Nature", "Light", "Shadow", "Poison", "Metal", "Arcane", "None" }

local function norm(element: string?): string
	if element and SPECTRAL[element] then
		return element
	end
	return "None"
end
Palettes.normalize = norm

--- The 5-stop ramp (hex) for an element and style. Unknown/nil element -> "None" (glitter).
function Palettes.ramp(element: string?, style: Style?): Ramp
	local e = norm(element)
	return if style == "Solid" then SOLID[e] else SPECTRAL[e]
end

-- ---------------------------------------------------------------------------------------------------------
-- Colour maths on hex strings (pure, deterministic).

function Palettes.toRGB(hex: string): (number, number, number)
	local h = string.gsub(hex, "#", "")
	if #h == 3 then
		h = string.gsub(h, "(%x)", "%1%1")
	end
	local r = tonumber(string.sub(h, 1, 2), 16) or 255
	local g = tonumber(string.sub(h, 3, 4), 16) or 255
	local b = tonumber(string.sub(h, 5, 6), 16) or 255
	return r / 255, g / 255, b / 255
end

function Palettes.toHex(r: number, g: number, b: number): string
	local function c(x: number): number
		return math.clamp(math.floor(x * 255 + 0.5), 0, 255)
	end
	return string.format("#%02X%02X%02X", c(r), c(g), c(b))
end

function Palettes.lerp(a: string, b: string, t: number): string
	local r1, g1, b1 = Palettes.toRGB(a)
	local r2, g2, b2 = Palettes.toRGB(b)
	return Palettes.toHex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)
end

function Palettes.toHSV(hex: string): (number, number, number)
	local r, g, b = Palettes.toRGB(hex)
	local mx, mn = math.max(r, g, b), math.min(r, g, b)
	local d = mx - mn
	local h = 0
	if d > 0 then
		if mx == r then
			h = ((g - b) / d) % 6
		elseif mx == g then
			h = (b - r) / d + 2
		else
			h = (r - g) / d + 4
		end
		h /= 6
	end
	return h, if mx > 0 then d / mx else 0, mx
end

function Palettes.fromHSV(h: number, s: number, v: number): string
	h = (h % 1) * 6
	local i = math.floor(h)
	local f = h - i
	local p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
	local r, g, b
	if i == 0 then
		r, g, b = v, t, p
	elseif i == 1 then
		r, g, b = q, v, p
	elseif i == 2 then
		r, g, b = p, v, t
	elseif i == 3 then
		r, g, b = p, q, v
	elseif i == 4 then
		r, g, b = t, p, v
	else
		r, g, b = v, p, q
	end
	return Palettes.toHex(r, g, b)
end

--- Build a 5-stop ramp around any colour (colour override, e.g. a "golden" or "rainbow" modifier, or a
--- summon's own primaryColour). Keeps the element ramp's value/saturation profile so overrides look as
--- polished as the built-in palettes.
function Palettes.rampFrom(hex: string, style: Style?): Ramp
	local h, s, v = Palettes.toHSV(hex)
	if style == "Solid" then
		return {
			Palettes.fromHSV(h, s * 0.25, math.min(1, v * 0.35 + 0.65)),
			Palettes.fromHSV(h, s * 0.6, math.min(1, v * 0.2 + 0.8)),
			hex,
			Palettes.fromHSV(h, math.min(1, s * 1.05), v * 0.68),
			Palettes.fromHSV(h, math.min(1, s * 0.9), v * 0.35),
		}
	end
	return {
		Palettes.fromHSV(h, s * 0.12, 1),
		Palettes.fromHSV(h, s * 0.5, 1),
		Palettes.fromHSV(h, math.max(s, 0.65), math.max(v, 0.85)),
		Palettes.fromHSV(h + 0.02, math.min(1, s * 1.1 + 0.1), math.max(v * 0.7, 0.45)),
		Palettes.fromHSV(h + 0.04, math.min(1, s * 1.1 + 0.15), 0.2),
	}
end

--- Ramp for effect params: colour override wins, else the element ramp.
function Palettes.resolve(element: string?, style: Style?, colour: string?): Ramp
	if type(colour) == "string" and string.match(colour, "^#%x%x%x%x%x%x$") then
		return Palettes.rampFrom(colour, style)
	end
	return Palettes.ramp(element, style)
end

--- ColorSequence keypoints as { {time, hex} } from ramp indices spread evenly over 0..1.
--- `stops` like {1, 3, 5} -> {{0, ramp[1]}, {0.5, ramp[3]}, {1, ramp[5]}}. Explicit {t, idx} pairs also allowed.
function Palettes.keypoints(ramp: Ramp, stops: { any }): { { any } }
	local out = {}
	local n = #stops
	for i, s in stops do
		if type(s) == "table" then
			table.insert(out, { s[1], ramp[s[2]] or ramp[3] })
		else
			table.insert(out, { if n == 1 then 0 else (i - 1) / (n - 1), ramp[s] or ramp[3] })
		end
	end
	if #out == 1 then
		table.insert(out, { 1, out[1][2] })
	end
	out[1][1] = 0
	out[#out][1] = 1
	return out
end

function Palettes.material(element: string?, style: Style?, role: string): string
	if style ~= "Solid" then
		return SPECTRAL_MATERIALS[role] or "Neon"
	end
	local m = SOLID_MATERIALS[norm(element)]
	return m[role] or m.core
end

--- Whether particles of this element should glow (LightEmission) in this style.
function Palettes.emissive(element: string?, style: Style?): boolean
	return style ~= "Solid" or EMISSIVE[norm(element)] == true
end

function Palettes.smoke(style: Style?): string
	return if style == "Solid" then SMOKE.Solid else SMOKE.Spectral
end

function Palettes.elementFx(element: string?)
	return ELEMENT_FX[norm(element)]
end

-- Transparency base for parts of a role. Spectral energy is translucent; Solid mass is opaque (water/ice/glass
-- are translucent in both).
local SOLID_TRANSLUCENT = { Water = 0.35, Ice = 0.2, Wind = 0.75, Poison = 0.3, Shadow = 0.15 }
function Palettes.transparency(element: string?, style: Style?, role: string): number
	if style ~= "Solid" then
		return if role == "core" then 0.05 elseif role == "shell" then 0.55 else 0.25
	end
	local t = SOLID_TRANSLUCENT[norm(element)] or 0
	if role == "shell" then
		return math.max(t, 0.45)
	end
	return t
end

Palettes._raw = { SPECTRAL = SPECTRAL, SOLID = SOLID, ELEMENT_FX = ELEMENT_FX, SOLID_MATERIALS = SOLID_MATERIALS }

return Palettes
