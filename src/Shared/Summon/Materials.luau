--!strict
-- Materials: the second build stage (DESIGN §8: body plan -> MATERIAL reshapes construction -> modifiers).
-- Runs on the Builder's parts after the plan/signature and before Style, in both styles. A material record
-- (Types.Material) supplies palette, robloxMaterial, transparency, glow, construction and particles.
--
--   Solid     recolour + Roblox material only           Strands   core + twisted strands (spaghetti, yarn, rope)
--   Bricks    surface tiled with staggered blocks       Panels    boxy masses + proud plates + rivets (cardboard, metal)
--   Wobble    translucent, suspended bits, gloss        Swarm     masses become clusters of small units (bees)
--   Shards    faceted core + radiating wedges (glass)   Inflated  rounded, glossy, knotted (balloons)
--   Woven     core + alternating bands (wicker, mail)   Pile      heap of small items over a core (coins, popcorn)
--   Liquid    smooth translucent masses + drips/puddle  Energy    neon masses + zig-zag arcs (lightning)
--
-- Record resolution (first hit wins): opts.material (record or id) > Library.material(id) > the provider set with
-- Materials.setProvider > the built-in FALLBACK table. Unknown ids leave the build untouched. Pure.

local Geom = require(script.Parent.Geom)
local Palette = require(script.Parent.Palette)
local Rng = require(script.Parent.Rng)

local at = Geom.at
local sin, cos, sqrt, pi = math.sin, math.cos, math.sqrt, math.pi

local Materials = {}

-- Built-in fallback records for the most common materials (used when Library has no materials table loaded).
local function rec(id, construction, rbx, tr, glow, palette, particles, tags)
	return { id = id, construction = construction, robloxMaterial = rbx, transparency = tr, glow = glow, palette = palette, particles = particles or {}, tags = tags or {} }
end
local FALLBACK: { [string]: any } = {
	spaghetti = rec("spaghetti", "Strands", "SmoothPlastic", 0, 0, { "#F2C46D", "#E8B04B", "#C8361F", "#F7E3A3" }, { "drip_sauce" }),
	cheese = rec("cheese", "Solid", "SmoothPlastic", 0, 0, { "#F9C80E", "#F4A300", "#FFE680" }, { "drip_sauce" }),
	glass = rec("glass", "Shards", "Glass", 0.4, 0.05, { "#DFF6FF", "#A9D6E5", "#FFFFFF" }, { "shards", "sparkle" }, { "transparent" }),
	bees = rec("bees", "Swarm", "SmoothPlastic", 0, 0, { "#F5C518", "#1A1A1A", "#FFFFFF" }, { "bees" }),
	jelly = rec("jelly", "Wobble", "Glass", 0.35, 0.15, { "#E0245E", "#FF6F91", "#FFB3C7" }, { "goo_drip" }),
	wood = rec("wood", "Solid", "Wood", 0, 0, { "#8B5A2B", "#A0522D", "#C19A6B", "#5C3A1E" }),
	stone = rec("stone", "Bricks", "Slate", 0, 0, { "#8D8D8D", "#6E6E6E", "#B5B5B5" }),
	brick = rec("brick", "Bricks", "Brick", 0, 0, { "#A0402A", "#C0583B", "#D9D2C5" }),
	metal = rec("metal", "Panels", "DiamondPlate", 0, 0, { "#8E98A3", "#5F6B76", "#C9D1D9" }, { "sparks" }),
	cardboard = rec("cardboard", "Panels", "Cardboard", 0, 0, { "#C4A484", "#A67B5B", "#E5D3B3" }),
	gold = rec("gold", "Solid", "Foil", 0, 0.2, { "#FFD700", "#D4AF37", "#FFF2A8", "#B8860B" }, { "sparkle", "glitter" }),
	ice = rec("ice", "Shards", "Ice", 0.2, 0.1, { "#BFEFFF", "#8FD3F7", "#E8FBFF" }, { "frost" }),
	lava = rec("lava", "Liquid", "CrackedLava", 0, 0.65, { "#FF4500", "#FF8C00", "#3B0A00", "#FFD166" }, { "embers", "smoke" }),
	water = rec("water", "Liquid", "Glass", 0.45, 0.05, { "#1F7FD1", "#5BB8F5", "#BEE9FF" }, { "bubbles" }),
	yarn = rec("yarn", "Strands", "Fabric", 0, 0, { "#E76F51", "#2A9D8F", "#E9C46A", "#264653" }),
	balloons = rec("balloons", "Inflated", "SmoothPlastic", 0, 0.05, { "#FF3B30", "#FFCC00", "#34C759", "#007AFF" }, { "confetti" }),
	lightning = rec("lightning", "Energy", "Neon", 0.1, 1, { "#F7E23A", "#8C7BFF", "#FFFFFF" }, { "sparks" }),
	coins = rec("coins", "Pile", "Foil", 0, 0.15, { "#FFD700", "#D4AF37", "#B8860B" }, { "sparkle" }),
	wicker = rec("wicker", "Woven", "Wood", 0, 0, { "#C8A165", "#9C7442", "#E3C796" }),
}
Materials.Fallback = FALLBACK

-- Per-material extras on top of the generic construction (the "spaghetti dragon has meatball eyes" layer).
local EXTRAS: { [string]: any } = {
	spaghetti = { meatballs = true, sauce = true, core = 2 },
	noodles = { core = 2 },
	macaroni = { core = 2 },
	cheese = { holes = true, wedge = true },
	swiss = { holes = true, wedge = true },
	sponge = { holes = true },
	cheesecake = { wedge = true },
	["googly eyes"] = { googly = true },
	pizza = { sauce = true },
	honey = { sauce = true },
	slime = { sauce = true },
	["peanut butter"] = { sauce = true },
	["toy bricks"] = { studs = true },
}
Materials.Extras = EXTRAS

local provider: ((string) -> any)? = nil
function Materials.setProvider(fn: ((string) -> any)?)
	provider = fn
end

local libraryMaterial: any = false
local function fromLibrary(id: string): any
	if libraryMaterial == false then
		libraryMaterial = nil
		local ok, Library = pcall(function()
			return require(script.Parent.Parent.Library) :: any
		end)
		if ok and type(Library) == "table" and type(Library.material) == "function" then
			libraryMaterial = Library.material
		end
	end
	if libraryMaterial then
		local ok, m = pcall(libraryMaterial, id)
		if ok and type(m) == "table" then
			return m
		end
	end
	return nil
end

-- (record?, id?) for a result + opts.
function Materials.resolve(result: any, opts: any?): any
	local o = opts or {}
	if type(o.material) == "table" then
		return o.material
	end
	local id = if type(o.material) == "string" then o.material else result.material
	if type(id) ~= "string" or id == "" then
		return nil
	end
	local m = fromLibrary(id)
	if m == nil and provider then
		local ok, pm = pcall(provider, id)
		if ok and type(pm) == "table" then
			m = pm
		end
	end
	return m or FALLBACK[id]
end

-- Parts budget the construction wants (the plan builds at lower detail to leave this room).
function Materials.reserve(m: any, maxParts: number): number
	if m == nil then
		return 0
	end
	local c = m.construction or "Solid"
	local ex = EXTRAS[m.id] or {}
	local base = if c == "Solid" then 0 elseif c == "Inflated" or c == "Liquid" then 3 else math.max(3, math.floor(maxParts * 0.3))
	if ex.holes or ex.sauce or ex.googly then
		base += 3
	end
	return math.min(base, math.floor(maxParts * 0.5))
end

-- ------------------------------------------------------------------ geometry helpers

local FACE = { eye = true, pupil = true, shine = true, mouth = true, brow = true, lid = true, blush = true, tooth = true }
local KEEP = { gem = true, window = true, light = true, glow = true, halo = true }
local MASS = {
	body = 1, head = 1, torso = 1, shell = 1, limb = 0.8, tail = 0.8, wing = 0.6, roof = 0.8, blade = 0.7, trunk = 0.8,
	snout = 0.6, jaw = 0.5, hood = 0.6, cape = 0.5, sail = 0.6, tentacle = 0.6, fin = 0.5, cannon = 0.6, tread = 0.6,
	hat = 0.4, mane = 0.6, beard = 0.5, wheel = 0.4, handle = 0.3, leaf = 0.5, petal = 0.5, door = 0.3,
}
local DARK = { dark = true, darker = true, tyre = true, gunmetal = true, claw = true, hoof = true, darkStone = true, darkWood = true, black = true, pupil = true, mouth = true }
local SECOND = { secondary = true, accent = true, belly = true, inner = true, horn = true, light = true, membrane = true, wingTip = true, beak = true, nail = true, gold = true, sail = true, cream = true, frosting = true, cloth2 = true, roof = true }

local function vol(p: any): number
	return p.size[1] * p.size[2] * p.size[3]
end

local function sub(p: any, spec: any): any
	-- a new part that rides the same bone; mirrored masses give mirrored pairs (pair key derived from the mass)
	local s = spec
	s.bone = p.bone
	s.mat = s.mat or p.mat
	if p.pair and s.pairTag then
		s.pair = p.pair .. "_" .. s.pairTag
	end
	s.pairTag = nil
	s.matPart = true
	return s
end

-- Point on the surface of p for a local unit direction (u, v, w); returns world point and world normal.
local function surface(p: any, u: number, v: number, w: number, inset: number): ({ number }, { number })
	local hx, hy, hz = p.size[1] / 2, p.size[2] / 2, p.size[3] / 2
	local lx, ly, lz, nx, ny, nz
	if p.shape == "Block" or p.shape == "Wedge" then
		local m = math.max(math.abs(u), math.abs(v), math.abs(w), 1e-6)
		lx, ly, lz = u / m * hx, v / m * hy, w / m * hz
		local au, av, aw = math.abs(u), math.abs(v), math.abs(w)
		if au >= av and au >= aw then
			nx, ny, nz = if u > 0 then 1 else -1, 0, 0
		elseif av >= aw then
			nx, ny, nz = 0, if v > 0 then 1 else -1, 0
		else
			nx, ny, nz = 0, 0, if w > 0 then 1 else -1
		end
	else
		lx, ly, lz = u * hx, v * hy, w * hz
		nx, ny, nz = Geom.normalize(u / hx, v / hy, w / hz)
	end
	local px, py, pz = Geom.point(p.cf, lx * inset, ly * inset, lz * inset)
	local wx, wy, wz = Geom.vector(p.cf, nx, ny, nz)
	return { px, py, pz }, { wx, wy, wz }
end

-- Evenly spread unit directions (Fibonacci sphere), deterministic.
local function fib(n: number, i: number, phase: number): (number, number, number)
	local y = 1 - (i - 0.5) / n * 2
	local r = sqrt(math.max(0, 1 - y * y))
	local a = i * 2.39996 + phase
	return cos(a) * r, y, sin(a) * r
end

local function dist(a: { number }, b: { number }): number
	local dx, dy, dz = a[1] - b[1], a[2] - b[2], a[3] - b[3]
	return sqrt(dx * dx + dy * dy + dz * dz)
end

-- Face keep-out: surface items never cover the eyes/mouth.
local function faceZones(parts: { any }): { any }
	local z = {}
	for _, p in parts do
		if FACE[p.role] then
			table.insert(z, { c = { p.cf[1], p.cf[2], p.cf[3] }, r = math.max(p.size[1], p.size[2], p.size[3]) * 0.9 })
		end
	end
	return z
end

local function clearOfFace(zones: { any }, pt: { number }, r: number): boolean
	for _, z in zones do
		if dist(z.c, pt) < z.r + r then
			return false
		end
	end
	return true
end

-- Frame at point with local Y along dir.
local function along(c: { number }, d: { number }, _len: number): any
	local f = Geom.between(c[1] - d[1] * 0.5, c[2] - d[2] * 0.5, c[3] - d[3] * 0.5, c[1] + d[1] * 0.5, c[2] + d[2] * 0.5, c[3] + d[3] * 0.5, "Y")
	return f
end

local function longAxis(p: any): (number, number, number)
	local s = p.size
	if s[1] >= s[2] and s[1] >= s[3] then
		return 1, 2, 3
	elseif s[2] >= s[3] then
		return 2, 1, 3
	end
	return 3, 1, 2
end

local function axisVec(p: any, i: number): { number }
	local x, y, z = Geom.vector(p.cf, if i == 1 then 1 else 0, if i == 2 then 1 else 0, if i == 3 then 1 else 0)
	return { x, y, z }
end

local function shrink(p: any, k: number)
	p.size = { p.size[1] * k, p.size[2] * k, p.size[3] * k }
end

local function roundify(p: any)
	if p.shape == "Block" or p.shape == "Wedge" or p.shape == "Cylinder" then
		local s = p.size
		p.shape = "Ellipsoid"
		p.size = { s[1] * 1.08, s[2] * 1.08, s[3] * 1.08 }
	end
end

-- ------------------------------------------------------------------ constructions (mass p, n extra parts)

local C = {}

function C.Strands(p: any, n: number, env: any)
	local ex = env.extras
	local a, b, c = longAxis(p)
	local s = p.size
	local la, rb, rc = s[a] / 2, s[b] / 2, s[c] / 2
	roundify(p)
	shrink(p, 0.8)
	p.mcol = env.pal[ex.core or 2]
	local va, vb, vc = axisVec(p, a), axisVec(p, b), axisVec(p, c)
	local th = math.min(rb, rc) * 0.42
	for i = 1, n do
		local ang = (i - 1) / n * pi * 2 + env.rng:range(-0.3, 0.3)
		local ca, sa = cos(ang), sin(ang)
		local tw = env.rng:range(0.15, 0.32) * (if i % 2 == 0 then 1 else -1)
		local off = 0.7
		local cx = p.cf[1] + (vb[1] * ca * rb + vc[1] * sa * rc) * off
		local cy = p.cf[2] + (vb[2] * ca * rb + vc[2] * sa * rc) * off
		local cz = p.cf[3] + (vb[3] * ca * rb + vc[3] * sa * rc) * off
		-- tangent around the long axis: twist the strand like a rope ply
		local tx, ty, tz = -vb[1] * sa + vc[1] * ca, -vb[2] * sa + vc[2] * ca, -vb[3] * sa + vc[3] * ca
		local dx, dy, dz = Geom.normalize(va[1] * cos(tw) + tx * sin(tw), va[2] * cos(tw) + ty * sin(tw), va[3] * cos(tw) + tz * sin(tw))
		local len = la * 2 * env.rng:range(0.72, 0.86)
		table.insert(env.out, sub(p, {
			shape = "Ellipsoid", size = { th, len, th * 0.9 }, cf = along({ cx, cy, cz }, { dx, dy, dz }, 0),
			col = p.col, mcol = env.pal[if i % 3 == 0 then 4 else 1] or env.pal[1], pri = (p.pri or 2) + 0.05 + i * 0.01, role = "strand",
			name = (p.name or "M") .. "Strand" .. i, pairTag = "s" .. i, noCore = true,
		}))
	end
end

function C.Woven(p: any, n: number, env: any)
	local a, b, c = longAxis(p)
	local s = p.size
	roundify(p)
	local va = axisVec(p, a)
	local bands = math.max(1, n)
	for i = 1, bands do
		local tpos = if bands == 1 then 0 else -0.6 + (i - 1) / (bands - 1) * 1.2
		local k = sqrt(math.max(0.05, 1 - tpos * tpos)) * 1.08
		local size = { 0, 0, 0 }
		size[a] = s[a] * 0.13
		size[b] = s[b] * k
		size[c] = s[c] * k
		local cf = table.clone(p.cf)
		cf[1] += va[1] * tpos * s[a] / 2
		cf[2] += va[2] * tpos * s[a] / 2
		cf[3] += va[3] * tpos * s[a] / 2
		table.insert(env.out, sub(p, {
			shape = "Ellipsoid", size = size, cf = cf, col = p.col, mcol = env.pal[if i % 2 == 0 then 3 else 2] or env.pal[2],
			pri = (p.pri or 2) + 0.1 + i * 0.01, role = "band", name = (p.name or "M") .. "Band" .. i, pairTag = "w" .. i, noCore = true,
		}))
	end
end

function C.Bricks(p: any, n: number, env: any)
	local mortar = env.pal[3] or Palette.tint(env.pal[1], 0.5)
	if p.shape == "Block" then
		-- tile the two broad faces and the top with staggered slabs
		local s = p.size
		local faces = {}
		local thin = if s[1] <= s[3] then 1 else 3
		table.insert(faces, { axis = thin, sign = -1 })
		table.insert(faces, { axis = thin, sign = 1 })
		local per = math.max(1, math.floor(n / #faces))
		p.mcol = mortar
		for fi, f in faces do
			local u = if f.axis == 1 then 3 else 1
			local rows = math.max(1, math.floor(sqrt(per * s[2] / math.max(s[u], 1e-3)) + 0.5))
			local cols = math.max(1, math.ceil(per / rows))
			local cw, rh = s[u] / cols, s[2] / rows
			local k = 0
			for r = 1, rows do
				for cI = 1, cols do
					k += 1
					if k > per then
						break
					end
					local stagger = if r % 2 == 0 then 0.25 else -0.25
					local lu = -s[u] / 2 + (cI - 0.5 + stagger) * cw
					lu = math.clamp(lu, -s[u] / 2 + cw * 0.45, s[u] / 2 - cw * 0.45)
					local ly = -s[2] / 2 + (r - 0.5) * rh
					local depth = s[f.axis] * 0.22 * (1 + env.rng:range(-0.08, 0.08))
					local lp = { 0, ly, 0 }
					lp[u] = lu
					lp[f.axis] = f.sign * (s[f.axis] / 2 + depth * 0.18)
					local size = { 0, rh * env.rng:range(0.8, 0.88), 0 }
					size[u] = cw * env.rng:range(0.84, 0.9)
					size[f.axis] = depth
					local x, y, z = Geom.point(p.cf, lp[1], lp[2], lp[3])
					local cf = table.clone(p.cf)
					cf[1], cf[2], cf[3] = x, y, z
					table.insert(env.out, sub(p, {
						shape = "Block", size = size, cf = cf, col = p.col, mcol = Palette.shade(env.pal[if (r + cI) % 2 == 0 then 1 else 2] or env.pal[1], env.rng:range(0, 0.08)),
						pri = (p.pri or 2) + 0.1 + k * 0.005 + fi * 0.002, role = "brick", name = (p.name or "M") .. "Brick" .. fi .. "_" .. k, pairTag = "b" .. fi .. k, noCore = true,
					}))
				end
			end
		end
		return
	end
	-- round masses: rows of bricks around the local Y axis
	shrink(p, 0.92)
	p.mcol = mortar
	local rows = math.max(1, math.floor(sqrt(n / 2) + 0.5))
	local per = math.max(1, math.ceil(n / rows))
	local s = p.size
	local k = 0
	for r = 1, rows do
		local phi = if rows == 1 then 0 else -0.75 + (r - 1) / (rows - 1) * 1.5
		for j = 1, per do
			k += 1
			if k > n then
				break
			end
			local lam = (j - 1) / per * pi * 2 + (if r % 2 == 0 then pi / per else 0)
			local u, v, w = cos(phi) * sin(lam), sin(phi), cos(phi) * cos(lam)
			local pt = surface(p, u, v, w, 0.96)
			if clearOfFace(env.zones, pt, math.min(s[1], s[3]) * 0.2) then
				local circ = pi * math.min(s[1], s[3]) * cos(phi)
				local bw = math.max(circ / per * 0.82, s[2] * 0.08)
				local bh = s[2] / (rows + 1) * 0.8
				local depth = math.min(s[1], s[3]) * 0.14 * (1 + env.rng:range(-0.1, 0.1))
				local lf = Geom.mul(p.cf, at(0, 0, 0, 0, lam, 0))
				local cf = Geom.mul(lf, at(0, 0, 0, -phi * 0.7, 0, 0))
				cf[1], cf[2], cf[3] = pt[1], pt[2], pt[3]
				table.insert(env.out, sub(p, {
					shape = "Block", size = { bw, bh, depth }, cf = cf, col = p.col, mcol = Palette.shade(env.pal[if (r + j) % 2 == 0 then 1 else 2] or env.pal[1], env.rng:range(0, 0.08)),
					pri = (p.pri or 2) + 0.1 + k * 0.005, role = "brick", name = (p.name or "M") .. "Brick" .. k, pairTag = "b" .. k, noCore = true,
				}))
			end
		end
	end
end

function C.Panels(p: any, n: number, env: any)
	if (p.shape == "Ellipsoid" or p.shape == "Ball") and not (p.role == "head" and #env.zones > 0) then
		p.shape = "Block"
		shrink(p, 0.82)
	end
	local s = p.size
	local metal = env.m.tags and table.find(env.m.tags, "metal") ~= nil
	-- plates on +X, -X and +Y faces; each inset 15% from the edges, embedded 40% of its thickness
	local faces = { { 1, 1 }, { 1, -1 }, { 2, 1 }, { 3, -1 }, { 3, 1 } }
	local k = 0
	for _, f in faces do
		if k >= n then
			break
		end
		local axis, sign = f[1], f[2]
		local th = math.max(math.min(s[1], s[2], s[3]) * 0.07, 0.03)
		local size = { s[1] * 0.72, s[2] * 0.72, s[3] * 0.72 }
		size[axis] = th
		local lp = { 0, 0, 0 }
		lp[axis] = sign * (s[axis] / 2 + th * 0.1)
		local pt = { Geom.point(p.cf, lp[1], lp[2], lp[3]) }
		if clearOfFace(env.zones, pt, math.min(size[1], size[2], size[3]) * 0.5 + 0.05) then
			k += 1
			local cf = table.clone(p.cf)
			cf[1], cf[2], cf[3] = pt[1], pt[2], pt[3]
			table.insert(env.out, sub(p, {
				shape = "Block", size = size, cf = cf, col = p.col, mcol = env.pal[2] or Palette.shade(env.pal[1], 0.15),
				pri = (p.pri or 2) + 0.1 + k * 0.01, role = "panel", name = (p.name or "M") .. "Panel" .. k, pairTag = "pl" .. k, noCore = true,
			}))
			if metal and k + 2 <= n then
				-- two rivets on the plate's diagonal
				for ri = -1, 1, 2 do
					local rp = table.clone(lp)
					local u = if axis == 1 then 3 else 1
					rp[u] += ri * size[u] * 0.38
					rp[2] += (if axis == 2 then 0 else ri * size[2] * 0.38)
					if axis == 2 then
						rp[3] += ri * size[3] * 0.38
					end
					rp[axis] += sign * th * 0.5
					local rx, ry, rz = Geom.point(p.cf, rp[1], rp[2], rp[3])
					k += 1
					table.insert(env.out, sub(p, {
						shape = "Ball", size = { th * 1.6, th * 1.6, th * 1.6 }, cf = Geom.new(rx, ry, rz), col = p.col, mcol = env.pal[3] or env.pal[1],
						pri = (p.pri or 2) + 0.4 + k * 0.01, role = "rivet", name = (p.name or "M") .. "Rivet" .. k, pairTag = "rv" .. k, noCore = true,
					}))
				end
			end
		end
	end
end

function C.Wobble(p: any, n: number, env: any)
	roundify(p)
	local s = p.size
	for i = 1, n do
		local u, v, w = fib(n + 1, i, env.rng:range(0, 6))
		local r = env.rng:range(0.2, 0.45)
		local x, y, z = Geom.point(p.cf, u * s[1] / 2 * r, v * s[2] / 2 * r, w * s[3] / 2 * r)
		local d = math.min(s[1], s[2], s[3]) * env.rng:range(0.16, 0.24)
		table.insert(env.out, sub(p, {
			shape = "Ellipsoid", size = { d, d * 0.8, d * 1.1 }, cf = at(x, y, z, env.rng:range(0, 3), env.rng:range(0, 3), 0),
			col = p.col, mcol = env.pal[if i % 2 == 0 then 3 else 2] or env.pal[1], pri = (p.pri or 2) + 0.5 + i * 0.01, role = "bit",
			name = (p.name or "M") .. "Bit" .. i, pairTag = "j" .. i, noCore = true, tr = 0,
		}))
	end
end

function C.Swarm(p: any, n: number, env: any)
	roundify(p)
	local s = p.size
	shrink(p, 0.72)
	p.mcol = env.pal[2] or Palette.shade(env.pal[1], 0.6)
	local unit = math.clamp(math.min(s[1], s[2], s[3]) * 0.3, 0.12, math.max(s[1], s[2], s[3]) * 0.22)
	local k = 0
	local phase = env.rng:range(0, 6)
	for i = 1, n * 2 do
		if k >= n then
			break
		end
		local u, v, w = fib(n * 2, i, phase)
		local pt, nrm = surface(p, u, v, w, 1.0)
		if clearOfFace(env.zones, pt, unit * 0.6) then
			k += 1
			local cf = along(pt, nrm, 0)
			cf = Geom.mul(cf, at(0, 0, 0, 0, env.rng:range(0, 6), math.rad(90)))
			cf[1], cf[2], cf[3] = pt[1] + nrm[1] * unit * 0.15, pt[2] + nrm[2] * unit * 0.15, pt[3] + nrm[3] * unit * 0.15
			table.insert(env.out, sub(p, {
				shape = "Ellipsoid", size = { unit * 0.8, unit * 1.35, unit * 0.8 }, cf = cf, col = p.col, mcol = env.pal[1],
				pri = (p.pri or 2) + 0.05 + k * 0.01, role = "unit", name = (p.name or "M") .. "Unit" .. k, pairTag = "u" .. k, noCore = true, swarmUnit = true,
			}))
		end
	end
end

function C.Shards(p: any, n: number, env: any)
	local s = p.size
	shrink(p, 0.8)
	local k = 0
	local phase = env.rng:range(0, 6)
	for i = 1, n * 2 do
		if k >= n then
			break
		end
		local u, v, w = fib(n * 2, i, phase)
		if v > -0.6 then
			local pt, nrm = surface(p, u, v, w, 0.85)
			local len = math.min(s[1], s[2], s[3]) * env.rng:range(0.45, 0.7)
			local wd = len * env.rng:range(0.32, 0.42)
			if clearOfFace(env.zones, pt, len * 0.6) then
				k += 1
				local cf = along({ pt[1] + nrm[1] * len * 0.3, pt[2] + nrm[2] * len * 0.3, pt[3] + nrm[3] * len * 0.3 }, nrm, 0)
				cf = Geom.mul(cf, at(0, 0, 0, env.rng:range(-0.25, 0.25), env.rng:range(0, 6), 0))
				table.insert(env.out, sub(p, {
					shape = "Wedge", size = { wd, len, wd * 0.8 }, cf = cf, col = p.col, mcol = env.pal[if k % 2 == 0 then 2 else 1] or env.pal[1],
					pri = (p.pri or 2) + 0.1 + k * 0.01, role = "shard", name = (p.name or "M") .. "Shard" .. k, pairTag = "sh" .. k, noCore = true,
				}))
			end
		end
	end
end

function C.Inflated(p: any, _n: number, env: any)
	roundify(p)
	local s = p.size
	local m = (s[1] + s[2] + s[3]) / 3
	p.size = { (s[1] * 0.65 + m * 0.35) * 1.06, (s[2] * 0.65 + m * 0.35) * 1.06, (s[3] * 0.65 + m * 0.35) * 1.06 }
	if env.first then
		-- knot under the biggest mass and a gloss highlight on top
		local bpt = surface(p, 0, -1, 0, 0.98)
		local d = math.min(p.size[1], p.size[3]) * 0.14
		table.insert(env.out, sub(p, { shape = "Ellipsoid", size = { d, d * 1.2, d }, cf = Geom.new(bpt[1], bpt[2] - d * 0.3, bpt[3]), col = p.col,
			mcol = Palette.shade(env.pal[1], 0.2), pri = (p.pri or 2) + 0.6, role = "knot", name = (p.name or "M") .. "Knot", noCore = true }))
		local tpt = surface(p, 0.35, 0.75, -0.55, 0.97)
		local g = math.min(p.size[1], p.size[2], p.size[3]) * 0.22
		table.insert(env.out, sub(p, { shape = "Ellipsoid", size = { g, g * 0.6, g * 0.35 }, cf = at(tpt[1], tpt[2], tpt[3], math.rad(-35), math.rad(-20), 0), col = "shine",
			mcol = { 1, 1, 1 }, pri = (p.pri or 2) + 0.7, role = "gloss", name = (p.name or "M") .. "Gloss", noCore = true, tr = 0.25 }))
	end
end

function C.Pile(p: any, n: number, env: any)
	local s = p.size
	shrink(p, 0.86)
	p.mcol = env.pal[2] or Palette.shade(env.pal[1], 0.2)
	local id = env.m.id
	local k = 0
	local phase = env.rng:range(0, 6)
	local base = math.min(s[1], s[2], s[3])
	for i = 1, n * 2 do
		if k >= n then
			break
		end
		local u, v, w = fib(n * 2, i, phase)
		if v > -0.5 then
			local pt, nrm = surface(p, u, v, w, 0.95)
			local d = base * env.rng:range(0.26, 0.36)
			if clearOfFace(env.zones, pt, d * 0.6) then
				k += 1
				local spec: any
				local col = env.pal[(k - 1) % #env.pal + 1]
				if id == "coins" or id == "cash" or id == "buttons" or id == "playing cards" then
					local cf = Geom.mul(along(pt, nrm, 0), at(0, 0, 0, 0, 0, math.rad(90)))
					spec = { shape = "Cylinder", size = { d * 0.18, d * 1.1, d * 1.1 }, cf = cf }
				elseif id == "leaves" or id == "petals" or id == "feathers" or id == "paper" or id == "sticky notes" then
					spec = { shape = "Ellipsoid", size = { d * 1.3, d * 0.22, d * 0.8 }, cf = Geom.mul(along(pt, nrm, 0), at(0, 0, 0, math.rad(90), env.rng:range(0, 6), 0)) }
				else
					spec = { shape = "Ellipsoid", size = { d * env.rng:range(0.9, 1.1), d * env.rng:range(0.85, 1.05), d * env.rng:range(0.9, 1.15) }, cf = at(pt[1], pt[2], pt[3], env.rng:range(0, 3), env.rng:range(0, 3), 0) }
				end
				spec.col, spec.mcol = p.col, col
				spec.pri = (p.pri or 2) + 0.1 + k * 0.01
				spec.role, spec.name, spec.pairTag, spec.noCore = "item", (p.name or "M") .. "Item" .. k, "it" .. k, true
				table.insert(env.out, sub(p, spec))
				if env.extras.googly and k < n then
					-- every googly item gets its pupil, set slightly forward along the normal
					k += 1
					local pc = { pt[1] + nrm[1] * d * 0.38, pt[2] + nrm[2] * d * 0.38, pt[3] + nrm[3] * d * 0.38 }
					table.insert(env.out, sub(p, { shape = "Ball", size = { d * 0.45, d * 0.45, d * 0.45 }, cf = Geom.new(pc[1], pc[2] - d * 0.1, pc[3]), col = "pupil",
						mcol = { 0.07, 0.07, 0.08 }, pri = spec.pri + 0.005, role = "item", name = spec.name .. "P", noCore = true, needs = spec.name }))
				end
			end
		end
	end
end

function C.Liquid(p: any, n: number, env: any)
	roundify(p)
	local s = p.size
	local k = 0
	for i = 1, n do
		local ang = env.rng:range(0, pi * 2)
		local pt = surface(p, cos(ang) * 0.45, -0.88, sin(ang) * 0.45, 0.9)
		local d = math.min(s[1], s[3]) * env.rng:range(0.14, 0.2)
		if clearOfFace(env.zones, pt, d) then
			k += 1
			table.insert(env.out, sub(p, { shape = "Ellipsoid", size = { d, d * 2.2, d }, cf = Geom.new(pt[1], pt[2] - d * 0.7, pt[3]), col = p.col, mcol = env.pal[1],
				pri = (p.pri or 2) + 0.4 + k * 0.01, role = "drip", name = (p.name or "M") .. "Drip" .. k, pairTag = "dr" .. k, noCore = true }))
		end
	end
end

function C.Energy(p: any, n: number, env: any)
	p.mglow = true
	local s = p.size
	for i = 1, n do
		-- zig-zag arc: one bent rod across the surface
		local u1, v1, w1 = fib(n + 2, i, env.rng:range(0, 6))
		local a = surface(p, u1, v1, w1, 1.02)
		local u2, v2, w2 = fib(n + 2, i + 1, env.rng:range(0, 6))
		local b = surface(p, u2, v2, w2, 1.02)
		local len = dist(a, b)
		if len > 1e-3 then
			local d = { (b[1] - a[1]) / len, (b[2] - a[2]) / len, (b[3] - a[3]) / len }
			local c = { (a[1] + b[1]) / 2, (a[2] + b[2]) / 2, (a[3] + b[3]) / 2 }
			local th = math.min(s[1], s[2], s[3]) * 0.07
			local cf = Geom.mul(along(c, d, 0), at(0, 0, 0, 0, 0, env.rng:range(-0.4, 0.4)))
			table.insert(env.out, sub(p, { shape = "Block", size = { th, len, th }, cf = cf, col = p.col, mcol = env.pal[if i % 2 == 0 then 3 else 1] or env.pal[1],
				pri = (p.pri or 2) + 0.3 + i * 0.01, role = "arc", name = (p.name or "M") .. "Arc" .. i, pairTag = "ar" .. i, noCore = true, mglow = true, tr = 0.1 }))
		end
	end
end

function C.Solid(_p: any, _n: number, _env: any) end

-- ------------------------------------------------------------------ extras

local function holes(p: any, n: number, env: any)
	local s = p.size
	local phase = env.rng:range(0, 6)
	local k = 0
	for i = 1, n * 3 do
		if k >= n then
			break
		end
		local u, v, w = fib(n * 3, i, phase)
		local pt, nrm = surface(p, u, v, w, 0.97)
		local d = math.min(s[1], s[2], s[3]) * env.rng:range(0.26, 0.36)
		if v > -0.4 and clearOfFace(env.zones, pt, d * 0.7) then
			k += 1
			local cf = along(pt, nrm, 0)
			table.insert(env.out, sub(p, { shape = "Ellipsoid", size = { d, d * 0.5, d * 0.92 }, cf = cf, col = p.col, mcol = Palette.shade(env.pal[2] or env.pal[1], 0.45),
				pri = (p.pri or 2) + 0.3 + k * 0.01, role = "hole", name = (p.name or "M") .. "Hole" .. k, pairTag = "h" .. k, noCore = true }))
		end
	end
end

local function sauce(p: any, n: number, env: any)
	local s = p.size
	local col = env.pal[3] or Palette.hex("#C8361F")
	for i = 1, n do
		local ang = (i - 1) / math.max(1, n) * pi * 2 + 0.6
		local pt = surface(p, cos(ang) * 0.55, 0.62, sin(ang) * 0.55, 0.98)
		local d = math.min(s[1], s[2], s[3]) * 0.22
		if clearOfFace(env.zones, pt, d) then
			-- a sauce blob on the upper surface with a drip running down
			table.insert(env.out, sub(p, { shape = "Ellipsoid", size = { d * 1.6, d * 0.55, d * 1.4 }, cf = at(pt[1], pt[2], pt[3], 0, ang, 0), col = p.col, mcol = col,
				pri = (p.pri or 2) + 0.35 + i * 0.01, role = "sauce", name = (p.name or "M") .. "Sauce" .. i, noCore = true }))
		end
	end
	local bpt = surface(p, 0.3, -0.85, -0.3, 0.92)
	local d = math.min(s[1], s[3]) * 0.16
	table.insert(env.out, sub(p, { shape = "Ellipsoid", size = { d, d * 2.4, d }, cf = Geom.new(bpt[1], bpt[2] - d * 0.8, bpt[3]), col = p.col, mcol = col,
		pri = (p.pri or 2) + 0.45, role = "drip", name = (p.name or "M") .. "SauceDrip", noCore = true }))
end

-- ------------------------------------------------------------------ apply

local function paletteOf(m: any): { any }
	local pal = {}
	for _, h in m.palette or {} do
		table.insert(pal, Palette.hex(h))
	end
	if #pal == 0 then
		pal = { Palette.hex("#B0B0B0") }
	end
	while #pal < 3 do
		table.insert(pal, Palette.shade(pal[1], 0.2 * #pal))
	end
	-- keep colour-blocking readable: the second colour must differ in brightness from the first
	if math.abs(Palette.luma(pal[1]) - Palette.luma(pal[2])) < 0.12 then
		pal[2] = if Palette.luma(pal[1]) > 0.45 then Palette.shade(pal[2], 0.35) else Palette.tint(pal[2], 0.35)
	end
	return pal
end

-- Applies material m to the builder's parts. room = extra parts the construction may add.
local SURFACE: { [string]: boolean } = { Strands = true, Woven = true, Bricks = true, Panels = true, Swarm = true, Shards = true, Pile = true }

function Materials.apply(B: any, m: any, room: number, ctx: any): any
	if m == nil then
		return nil
	end
	local construction = m.construction or "Solid"
	if ctx.result and ctx.result.visual and ctx.result.visual.bodyPlan == "Swarm" then
		-- swarm units are already tiny: the material only recolours them
		construction = "Solid"
	end
	local fn = C[construction] or C.Solid
	local rng = Rng.new(Rng.hash((m.id or "m") .. "|" .. tostring(ctx.result and ctx.result.id or "")))
	local pal = paletteOf(m)
	local extras = EXTRAS[m.id] or {}
	local parts = B.parts
	local zones = faceZones(parts)

	local swarmPlan = ctx.result and ctx.result.visual and ctx.result.visual.bodyPlan == "Swarm"
	-- recolour everything except the face and lit features; first palette colour on the main masses
	for i, p in parts do
		if FACE[p.role] then
			if extras.meatballs and p.role == "eye" and p.col == "eyeWhite" then
				p.mcol = Palette.hex("#7A3B1F")
				p.mrbx = "SmoothPlastic"
			end
		elseif not KEEP[p.role] and not p.glow then
			local key = p.col
			local c = if DARK[key] then Palette.shade(pal[2], 0.35) elseif SECOND[key] then pal[2] else pal[1]
			if swarmPlan then
				-- a swarm of material units reads better two-toned
				c = if i % 2 == 0 then pal[1] else Palette.shade(pal[1], 0.45)
			end
			p.mcol = Palette.shade(c, rng:range(0, 0.06))
			p.mrbx = m.robloxMaterial
			if (m.transparency or 0) > 0 then
				p.tr = math.max(p.tr or 0, m.transparency)
			end
			if (m.glow or 0) >= 0.6 then
				p.mglow = true
			end
		end
	end

	-- masses, biggest first
	local masses = {}
	for _, p in parts do
		local w = MASS[p.role]
		if w and not p.glow then
			table.insert(masses, { p = p, w = vol(p) * w })
		end
	end
	table.sort(masses, function(a, b)
		if a.w ~= b.w then
			return a.w > b.w
		end
		return a.p.id < b.p.id
	end)
	local top = masses[1] and masses[1].w or 0
	local chosen = {}
	for _, ms in masses do
		if ms.w >= top * 0.04 and #chosen < 8 then
			table.insert(chosen, ms)
		end
	end
	-- mirrored masses consume budget twice; share the room by weight
	local sum = 0
	for _, ms in chosen do
		sum += ms.w
	end
	local env = { rng = rng, pal = pal, out = {}, zones = zones, m = m, extras = extras, first = true }
	local cap = ({ Strands = 6, Woven = 3, Bricks = 10, Panels = 5, Wobble = 3, Swarm = 12, Shards = 6, Inflated = 2, Pile = 10, Liquid = 2, Energy = 3, Solid = 0 } :: any)[construction] or 0
	local left = math.max(0, room)
	local extraRoom = 0
	if extras.holes or extras.sauce then
		extraRoom = math.min(4, math.floor(left * 0.3))
		left -= extraRoom
	end
	for i, ms in chosen do
		local p = ms.p
		local share = math.floor(left * ms.w / math.max(sum, 1e-6) + 0.5)
		local mult = if p.pair then 2 else 1
		local n = math.min(cap, math.floor(share / mult))
		if i == 1 then
			n = math.max(n, math.min(cap, math.floor(left / mult), 3))
		end
		env.first = i == 1
		if n > 0 or construction == "Inflated" or construction == "Panels" then
			fn(p, n, env)
			-- constructions that rebuild a mass out of units (strands, bricks, plates, shards, a pile, a swarm) sit on
			-- the primitive's own surface: that mass keeps its primitive instead of a sculpted mesh
			if SURFACE[construction] then
				p.noMesh = true
			end
		end
		if construction == "Wobble" or construction == "Liquid" then
			roundify(p)
		end
		if i == 1 and extras.wedge and p.shape == "Block" and (p.role == "body" or p.role == "torso") then
			p.shape = "Wedge"
		end
	end
	if chosen[1] then
		local p = chosen[1].p
		local n = math.max(1, extraRoom)
		if extras.holes then
			holes(p, n, env)
			if chosen[2] and extraRoom >= 4 then
				holes(chosen[2].p, 1, env)
			end
		end
		if extras.sauce then
			sauce(p, math.max(1, n - 1), env)
		end
	end
	for _, s in env.out do
		-- construction detail ranks below the face: eyes (pri 1.5) always survive the budget first
		s.pri = math.max(s.pri or 2, 1.55 + ((s.pri or 2) - 1) * 0.3)
		s.mrbx = s.mrbx or m.robloxMaterial
		if (m.transparency or 0) > 0 and s.role ~= "hole" and s.role ~= "bit" then
			s.tr = math.max(s.tr or 0, m.transparency)
		end
		B:part(s)
	end

	-- what the rest of the pipeline needs to know
	local motion = ({ Wobble = "wobble", Liquid = "wobble", Inflated = "bob", Strands = "flop", Woven = "flop", Swarm = "swarm", Energy = "flicker",
		Panels = "clank", Bricks = "clank", Shards = "clank", Pile = "jiggle", Solid = nil } :: any)[construction]
	if motion == nil and m.tags and (table.find(m.tags, "metal") or table.find(m.tags, "heavy")) then
		motion = "clank"
	end
	B.rig.materialMotion = motion
	local swarm = {}
	for _, p in B.parts do
		if p.swarmUnit then
			table.insert(swarm, p.name)
		end
	end
	if #swarm > 0 then
		B.rig.swarmUnits = swarm
	end
	return { id = m.id, construction = construction, particles = m.particles or {}, motion = motion, sound = m.sound, palette = pal, glow = m.glow or 0 }
end

return Materials
