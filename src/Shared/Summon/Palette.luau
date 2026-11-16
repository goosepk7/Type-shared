--!strict
-- Colour helpers and element palettes. Colours are {r, g, b} in 0..1 (Color3.new order). Pure.

export type RGB = { number }

local Palette = {}

function Palette.hex(s: string?): RGB
	if type(s) ~= "string" then
		return { 0.6, 0.6, 0.6 }
	end
	local h = string.gsub(s, "#", "")
	if #h == 3 then
		h = string.gsub(h, "(.)", "%1%1")
	end
	local r = tonumber(string.sub(h, 1, 2), 16)
	local g = tonumber(string.sub(h, 3, 4), 16)
	local b = tonumber(string.sub(h, 5, 6), 16)
	if not (r and g and b) then
		return { 0.6, 0.6, 0.6 }
	end
	return { r / 255, g / 255, b / 255 }
end

function Palette.toHex(c: RGB): string
	return string.format("#%02X%02X%02X", math.floor(c[1] * 255 + 0.5), math.floor(c[2] * 255 + 0.5), math.floor(c[3] * 255 + 0.5))
end

function Palette.lerp(a: RGB, b: RGB, t: number): RGB
	return { a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t, a[3] + (b[3] - a[3]) * t }
end

function Palette.mul(c: RGB, k: number): RGB
	return { math.clamp(c[1] * k, 0, 1), math.clamp(c[2] * k, 0, 1), math.clamp(c[3] * k, 0, 1) }
end

function Palette.luma(c: RGB): number
	return 0.2126 * c[1] + 0.7152 * c[2] + 0.0722 * c[3]
end

-- HSV helpers for saturation tweaks.
function Palette.toHsv(c: RGB): (number, number, number)
	local r, g, b = c[1], c[2], c[3]
	local mx, mn = math.max(r, g, b), math.min(r, g, b)
	local d = mx - mn
	local h = 0
	if d > 1e-6 then
		if mx == r then
			h = ((g - b) / d) % 6
		elseif mx == g then
			h = (b - r) / d + 2
		else
			h = (r - g) / d + 4
		end
		h /= 6
	end
	local s = if mx > 0 then d / mx else 0
	return h, s, mx
end

function Palette.fromHsv(h: number, s: number, v: number): RGB
	h = (h % 1) * 6
	local i = math.floor(h)
	local f = h - i
	local p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
	if i == 0 then
		return { v, t, p }
	elseif i == 1 then
		return { q, v, p }
	elseif i == 2 then
		return { p, v, t }
	elseif i == 3 then
		return { p, q, v }
	elseif i == 4 then
		return { t, p, v }
	end
	return { v, p, q }
end

-- Shade: darker and slightly more saturated (painterly shadow colour rather than grey mud).
function Palette.shade(c: RGB, amount: number): RGB
	local h, s, v = Palette.toHsv(c)
	return Palette.fromHsv(h, math.clamp(s + amount * 0.15, 0, 1), math.clamp(v * (1 - amount), 0, 1))
end

-- Tint: lighter, slightly desaturated.
function Palette.tint(c: RGB, amount: number): RGB
	local h, s, v = Palette.toHsv(c)
	return Palette.fromHsv(h, math.clamp(s * (1 - amount * 0.5), 0, 1), math.clamp(v + (1 - v) * amount, 0, 1))
end

function Palette.saturate(c: RGB, k: number): RGB
	local h, s, v = Palette.toHsv(c)
	return Palette.fromHsv(h, math.clamp(s * k, 0, 1), v)
end

-- Spectral palettes per element: outer (shell), main (body energy), core (hot inner), glow (light/rim), deep (trail end).
export type ElementPalette = { outer: RGB, main: RGB, core: RGB, glow: RGB, deep: RGB }

local E: { [string]: { string } } = {
	Fire = { "#FF5A1F", "#FF8A2B", "#FFE6A0", "#FFB347", "#B3200E" },
	Water = { "#1C8CFF", "#3FB6FF", "#D2F4FF", "#6FD6FF", "#0B3FA8" },
	Ice = { "#7FD8FF", "#A8E9FF", "#F2FDFF", "#C8F3FF", "#3C8FD6" },
	Lightning = { "#FFE03A", "#FFF07A", "#FFFFFF", "#BFD4FF", "#5B6CFF" },
	Earth = { "#C88A3A", "#E0A85A", "#FFE2B0", "#F0C070", "#6B3E1A" },
	Wind = { "#8FF5D8", "#C2FFEE", "#FFFFFF", "#B5FFF0", "#3FB9A8" },
	Nature = { "#3EDB6A", "#8CF25A", "#EAFFC8", "#A8FF7A", "#11803A" },
	Light = { "#FFE58A", "#FFF3BF", "#FFFFFF", "#FFF0A8", "#E0A21A" },
	Shadow = { "#7B3CFF", "#5A22C8", "#E3C6FF", "#A974FF", "#1C0838" },
	Poison = { "#8CFF2E", "#B5FF5A", "#F3FFD0", "#C77DFF", "#3B8A12" },
	Metal = { "#B9C8D8", "#DCE6F0", "#FFFFFF", "#9FC4E8", "#4E6A88" },
	Arcane = { "#B65CFF", "#D58CFF", "#FFE6FF", "#FF9CF2", "#5A1FA8" },
}

local cache: { [string]: ElementPalette } = {}

-- For element None, derive a spectral palette from the word's own primary colour.
function Palette.element(element: string, primaryHex: string?): ElementPalette
	local key = element .. "|" .. (if element == "None" then (primaryHex or "") else "")
	local hit = cache[key]
	if hit then
		return hit
	end
	local p: ElementPalette
	local list = E[element]
	if list then
		p = {
			outer = Palette.hex(list[1]),
			main = Palette.hex(list[2]),
			core = Palette.hex(list[3]),
			glow = Palette.hex(list[4]),
			deep = Palette.hex(list[5]),
		}
	else
		local base = Palette.hex(primaryHex or "#9AC8FF")
		local h, s, v = Palette.toHsv(base)
		-- energy needs saturation and value; greys become a cool silver-blue
		if s < 0.15 then
			h, s = 0.58, 0.35
		end
		local main = Palette.fromHsv(h, math.clamp(s, 0.45, 0.9), math.max(v, 0.85))
		p = {
			outer = Palette.fromHsv(h, math.clamp(s, 0.55, 1), math.max(v, 0.8)),
			main = main,
			core = Palette.tint(main, 0.8),
			glow = Palette.tint(main, 0.4),
			deep = Palette.fromHsv(h, math.clamp(s + 0.1, 0.5, 1), 0.45),
		}
	end
	cache[key] = p
	return p
end

Palette.Elements = E

return Palette
