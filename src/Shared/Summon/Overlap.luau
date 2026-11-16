--!strict
-- Z-fighting checker (pure). Finds pairs of visible parts whose surfaces coincide:
--   * planar faces that are coplanar (normals parallel or anti-parallel, planes within Tolerance) and whose
--     polygons overlap with area > MinArea (Block, Wedge, CornerWedge faces, Cylinder end caps);
--   * curved surfaces that coincide (Ball/Ellipsoid shells with the same surface, Cylinder sides on the same
--     axis and radius with overlapping length).
-- Parts with transparency >= 1 never render and are skipped. Used by the blueprint stage (auto-fix pass) and
-- by tests (which require zero violations after the fix pass AND count what the fixer had to do).

local Geom = require(script.Parent.Geom)

type Frame = Geom.Frame

local Overlap = {}

Overlap.Tolerance = 0.005
Overlap.MinArea = 1e-4
local CAP_SEGMENTS = 16

export type Violation = { a: number, b: number, kind: string, area: number, nx: number, ny: number, nz: number, fa: number?, fb: number? }

type Face = { pts: { { number } }, nx: number, ny: number, nz: number, d: number }

local sqrt, abs = math.sqrt, math.abs

local function transformPts(cf: Frame, pts: { { number } }): { { number } }
	local out = table.create(#pts)
	for i, p in pts do
		local x, y, z = Geom.point(cf, p[1], p[2], p[3])
		out[i] = { x, y, z }
	end
	return out
end

local function faceFrom(pts: { { number } }): Face?
	-- Newell normal (robust for convex polygons)
	local nx, ny, nz = 0, 0, 0
	local n = #pts
	for i = 1, n do
		local a, b = pts[i], pts[i % n + 1]
		nx += (a[2] - b[2]) * (a[3] + b[3])
		ny += (a[3] - b[3]) * (a[1] + b[1])
		nz += (a[1] - b[1]) * (a[2] + b[2])
	end
	local m = sqrt(nx * nx + ny * ny + nz * nz)
	if m < 1e-12 then
		return nil
	end
	nx, ny, nz = nx / m, ny / m, nz / m
	local p = pts[1]
	return { pts = pts, nx = nx, ny = ny, nz = nz, d = nx * p[1] + ny * p[2] + nz * p[3] }
end

-- Local-space convex polygons (counter-clockwise seen from outside) for each planar face of a shape.
local function localFaces(shape: string, sx: number, sy: number, sz: number): { { { number } } }
	local hx, hy, hz = sx / 2, sy / 2, sz / 2
	if shape == "Block" then
		return {
			{ { hx, -hy, -hz }, { hx, hy, -hz }, { hx, hy, hz }, { hx, -hy, hz } }, -- +X
			{ { -hx, -hy, hz }, { -hx, hy, hz }, { -hx, hy, -hz }, { -hx, -hy, -hz } }, -- -X
			{ { -hx, hy, -hz }, { -hx, hy, hz }, { hx, hy, hz }, { hx, hy, -hz } }, -- +Y
			{ { -hx, -hy, hz }, { -hx, -hy, -hz }, { hx, -hy, -hz }, { hx, -hy, hz } }, -- -Y
			{ { -hx, -hy, hz }, { hx, -hy, hz }, { hx, hy, hz }, { -hx, hy, hz } }, -- +Z
			{ { hx, -hy, -hz }, { -hx, -hy, -hz }, { -hx, hy, -hz }, { hx, hy, -hz } }, -- -Z
		}
	elseif shape == "Wedge" then
		-- Roblox WedgePart: vertical face at +Z, slope rising from the bottom-front (-Z) edge to the top-back edge.
		return {
			{ { -hx, -hy, hz }, { -hx, -hy, -hz }, { hx, -hy, -hz }, { hx, -hy, hz } }, -- bottom
			{ { -hx, -hy, hz }, { hx, -hy, hz }, { hx, hy, hz }, { -hx, hy, hz } }, -- back
			{ { hx, -hy, -hz }, { hx, hy, hz }, { hx, -hy, hz } }, -- +X side
			{ { -hx, -hy, hz }, { -hx, hy, hz }, { -hx, -hy, -hz } }, -- -X side
			{ { hx, -hy, -hz }, { -hx, -hy, -hz }, { -hx, hy, hz }, { hx, hy, hz } }, -- slope
		}
	elseif shape == "CornerWedge" then
		-- Assumed peak at (+hx, +hy, -hz) (see docs/platform/summon.md; blueprints do not use CornerWedge).
		local P = { hx, hy, -hz }
		return {
			{ { -hx, -hy, hz }, { -hx, -hy, -hz }, { hx, -hy, -hz }, { hx, -hy, hz } }, -- bottom
			{ { hx, -hy, -hz }, P, { hx, -hy, hz } }, -- +X
			{ { -hx, -hy, -hz }, P, { hx, -hy, -hz } }, -- -Z
			{ { -hx, -hy, hz }, P, { -hx, -hy, -hz } },
			{ { hx, -hy, hz }, P, { -hx, -hy, hz } },
		}
	elseif shape == "Cylinder" then
		local r = math.min(sy, sz) / 2
		local capA, capB = {}, {}
		for i = 0, CAP_SEGMENTS - 1 do
			local a = i / CAP_SEGMENTS * math.pi * 2
			table.insert(capA, { hx, math.cos(a) * r, math.sin(a) * r })
			table.insert(capB, 1, { -hx, math.cos(a) * r, math.sin(a) * r })
		end
		return { capA, capB }
	end
	return {}
end

export type Prepared = {
	faces: { Face },
	min: { number },
	max: { number },
	quadric: { center: { number }, axes: { { number } }, radii: { number } }?,
	cylinder: { a: { number }, dir: { number }, len: number, r: number }?,
	vol: number,
}

local function prepare(p: any): Prepared?
	if math.max(p.tr or 0, p.transparency or 0) >= 0.999 or p.shape == "Mesh" then
		return nil
	end
	local cf: Frame = p.cf
	local sx, sy, sz = p.size[1], p.size[2], p.size[3]
	local faces = {}
	for _, poly in localFaces(p.shape, sx, sy, sz) do
		local f = faceFrom(transformPts(cf, poly))
		if f then
			table.insert(faces, f)
		end
	end
	-- world AABB of the oriented box
	local hx, hy, hz = sx / 2, sy / 2, sz / 2
	local ex = abs(cf[4]) * hx + abs(cf[5]) * hy + abs(cf[6]) * hz
	local ey = abs(cf[7]) * hx + abs(cf[8]) * hy + abs(cf[9]) * hz
	local ez = abs(cf[10]) * hx + abs(cf[11]) * hy + abs(cf[12]) * hz
	local prep: Prepared = {
		faces = faces,
		min = { cf[1] - ex, cf[2] - ey, cf[3] - ez },
		max = { cf[1] + ex, cf[2] + ey, cf[3] + ez },
		quadric = nil,
		cylinder = nil,
		vol = sx * sy * sz,
	}
	if p.shape == "Ball" or p.shape == "Ellipsoid" then
		prep.quadric = {
			center = { cf[1], cf[2], cf[3] },
			axes = { { cf[4], cf[7], cf[10] }, { cf[5], cf[8], cf[11] }, { cf[6], cf[9], cf[12] } },
			radii = { hx, hy, hz },
		}
	elseif p.shape == "Cylinder" then
		local ax, ay, az = Geom.point(cf, -hx, 0, 0)
		prep.cylinder = { a = { ax, ay, az }, dir = { cf[4], cf[7], cf[10] }, len = sx, r = math.min(sy, sz) / 2 }
	end
	return prep
end
Overlap.prepare = prepare

-- 2D convex polygon clipping (Sutherland-Hodgman) and area.
local function clip(subject: { { number } }, clipPoly: { { number } }): { { number } }
	local out = subject
	local n = #clipPoly
	-- orientation of clip polygon
	local area2 = 0
	for i = 1, n do
		local a, b = clipPoly[i], clipPoly[i % n + 1]
		area2 += a[1] * b[2] - b[1] * a[2]
	end
	local sgn = if area2 >= 0 then 1 else -1
	for i = 1, n do
		if #out == 0 then
			break
		end
		local a, b = clipPoly[i], clipPoly[i % n + 1]
		local input = out
		out = {}
		local function inside(p: { number }): boolean
			return sgn * ((b[1] - a[1]) * (p[2] - a[2]) - (b[2] - a[2]) * (p[1] - a[1])) >= -1e-9
		end
		local function intersect(p: { number }, q: { number }): { number }
			local x1, y1, x2, y2 = p[1], p[2], q[1], q[2]
			local x3, y3, x4, y4 = a[1], a[2], b[1], b[2]
			local den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
			if abs(den) < 1e-15 then
				return { x1, y1 }
			end
			local t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
			return { x1 + t * (x2 - x1), y1 + t * (y2 - y1) }
		end
		local m = #input
		for j = 1, m do
			local cur, prev = input[j], input[(j - 2) % m + 1]
			local ci, pi = inside(cur), inside(prev)
			if ci then
				if not pi then
					table.insert(out, intersect(prev, cur))
				end
				table.insert(out, cur)
			elseif pi then
				table.insert(out, intersect(prev, cur))
			end
		end
	end
	return out
end

local function area(poly: { { number } }): number
	local s = 0
	local n = #poly
	for i = 1, n do
		local a, b = poly[i], poly[i % n + 1]
		s += a[1] * b[2] - b[1] * a[2]
	end
	return abs(s) / 2
end

local function project(pts: { { number } }, ux: number, uy: number, uz: number, vx: number, vy: number, vz: number): { { number } }
	local out = table.create(#pts)
	for i, p in pts do
		out[i] = { p[1] * ux + p[2] * uy + p[3] * uz, p[1] * vx + p[2] * vy + p[3] * vz }
	end
	return out
end

local function coplanarArea(f: Face, g: Face, tol: number): number
	local dot = f.nx * g.nx + f.ny * g.ny + f.nz * g.nz
	if abs(dot) < 0.9995 then
		return 0
	end
	-- distance between planes, measured with f's normal at g's first vertex
	local p = g.pts[1]
	local dist = f.nx * p[1] + f.ny * p[2] + f.nz * p[3] - f.d
	if abs(dist) > tol then
		return 0
	end
	-- also check g's other vertices (nearly parallel planes can diverge across a big face)
	for _, q in g.pts do
		if abs(f.nx * q[1] + f.ny * q[2] + f.nz * q[3] - f.d) > tol then
			return 0
		end
	end
	-- basis on f's plane
	local hx, hy, hz = 1, 0, 0
	if abs(f.nx) > 0.8 then
		hx, hy, hz = 0, 1, 0
	end
	local ux, uy, uz = Geom.normalize(Geom.cross(f.nx, f.ny, f.nz, hx, hy, hz))
	local vx, vy, vz = Geom.cross(f.nx, f.ny, f.nz, ux, uy, uz)
	local a2 = project(f.pts, ux, uy, uz, vx, vy, vz)
	local b2 = project(g.pts, ux, uy, uz, vx, vy, vz)
	local inter = clip(a2, b2)
	if #inter < 3 then
		return 0
	end
	return area(inter)
end

-- Fraction of sample points on quadric A's surface that also lie on quadric B's surface.
local SAMPLES: { { number } } = {}
for i = 0, 5 do
	for j = 0, 7 do
		local th = (i + 0.5) / 6 * math.pi
		local ph = j / 8 * math.pi * 2
		table.insert(SAMPLES, { math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph) })
	end
end

local function quadricCoincide(qa: any, qb: any, tol: number): boolean
	local hits = 0
	for _, s in SAMPLES do
		local px = qa.center[1]
		local py = qa.center[2]
		local pz = qa.center[3]
		for k = 1, 3 do
			local ax = qa.axes[k]
			local r = qa.radii[k] * s[k]
			px += ax[1] * r
			py += ax[2] * r
			pz += ax[3] * r
		end
		-- into B's local frame
		local dx, dy, dz = px - qb.center[1], py - qb.center[2], pz - qb.center[3]
		local sum = 0
		local minR = math.huge
		for k = 1, 3 do
			local ax = qb.axes[k]
			local l = (dx * ax[1] + dy * ax[2] + dz * ax[3]) / qb.radii[k]
			sum += l * l
			minR = math.min(minR, qb.radii[k])
		end
		local f = sqrt(sum) - 1
		if abs(f) * minR <= tol then
			hits += 1
		end
	end
	return hits >= #SAMPLES * 0.25
end

local function cylinderCoincide(ca: any, cb: any, tol: number): boolean
	if abs(ca.r - cb.r) > tol then
		return false
	end
	local dot = ca.dir[1] * cb.dir[1] + ca.dir[2] * cb.dir[2] + ca.dir[3] * cb.dir[3]
	if abs(dot) < 0.9995 then
		return false
	end
	-- distance from cb.a to ca's axis line
	local dx, dy, dz = cb.a[1] - ca.a[1], cb.a[2] - ca.a[2], cb.a[3] - ca.a[3]
	local t = dx * ca.dir[1] + dy * ca.dir[2] + dz * ca.dir[3]
	local px, py, pz = dx - t * ca.dir[1], dy - t * ca.dir[2], dz - t * ca.dir[3]
	if sqrt(px * px + py * py + pz * pz) > tol then
		return false
	end
	-- overlap of [0, la] and [t, t +- lb]
	local b0, b1 = t, t + dot * cb.len
	if b0 > b1 then
		b0, b1 = b1, b0
	end
	return math.min(ca.len, b1) - math.max(0, b0) > tol
end

local function aabbTouch(a: Prepared, b: Prepared, pad: number): boolean
	return a.min[1] - pad <= b.max[1] and b.min[1] - pad <= a.max[1]
		and a.min[2] - pad <= b.max[2] and b.min[2] - pad <= a.max[2]
		and a.min[3] - pad <= b.max[3] and b.min[3] - pad <= a.max[3]
end

-- Returns every violation in a part list (blueprint.parts).
function Overlap.check(parts: { any }, tol: number?): { Violation }
	local t = tol or Overlap.Tolerance
	local prepped: { Prepared? } = {}
	for i, p in parts do
		prepped[i] = prepare(p)
	end
	local out: { Violation } = {}
	local n = #parts
	for i = 1, n do
		local a = prepped[i]
		if a then
			for j = i + 1, n do
				local b = prepped[j]
				if b and aabbTouch(a, b, t * 2) then
					local found = false
					for fi, fa in a.faces do
						for fj, fb in b.faces do
							local ar = coplanarArea(fa, fb, t)
							if ar > Overlap.MinArea then
								table.insert(out, { a = i, b = j, kind = "coplanar", area = ar, nx = fb.nx, ny = fb.ny, nz = fb.nz, fa = fi, fb = fj })
								found = true
								break
							end
						end
						if found then
							break
						end
					end
					if not found and a.quadric and b.quadric then
						if quadricCoincide(a.quadric, b.quadric, t) or quadricCoincide(b.quadric, a.quadric, t) then
							table.insert(out, { a = i, b = j, kind = "quadric", area = 0, nx = 0, ny = 1, nz = 0 })
							found = true
						end
					end
					if not found and a.cylinder and b.cylinder and cylinderCoincide(a.cylinder, b.cylinder, t) then
						table.insert(out, { a = i, b = j, kind = "cylinder", area = 0, nx = 0, ny = 1, nz = 0 })
					end
				end
			end
		end
	end
	return out
end

-- Resolve violations in place by nudging the less important part (higher pri, then smaller volume):
-- coplanar faces -> translate along that part's face normal by `inset` (it protrudes / embeds slightly);
-- coincident curved shells -> grow the less important part by 2 * inset. Returns number of fixes applied.
function Overlap.fix(parts: { any }, inset: number, maxPasses: number?): number
	local fixes = 0
	for pass = 1, maxPasses or 10 do
		local vs = Overlap.check(parts)
		-- vary the step per pass so a nudge never lands exactly on a neighbouring plane (chains of thin plates)
		local step = inset * (1 + ((pass - 1) * 0.618) % 1)
		if #vs == 0 then
			break
		end
		local moved: { [number]: boolean } = {}
		for _, v in vs do
			local pa, pb = parts[v.a], parts[v.b]
			local victimIdx: number
			if (pa.pri or 2) ~= (pb.pri or 2) then
				victimIdx = if (pa.pri or 2) > (pb.pri or 2) then v.a else v.b
			else
				local va = pa.size[1] * pa.size[2] * pa.size[3]
				local vb = pb.size[1] * pb.size[2] * pb.size[3]
				victimIdx = if va <= vb then v.a else v.b
			end
			if not moved[victimIdx] then
				moved[victimIdx] = true
				local p = parts[victimIdx]
				fixes += 1
				if v.kind == "coplanar" then
					-- normal of the victim's own face
					local prep = prepare(p)
					local fi = if victimIdx == v.a then v.fa else v.fb
					local face = prep and fi and prep.faces[fi]
					local nx, ny, nz = v.nx, v.ny, v.nz
					if face then
						nx, ny, nz = face.nx, face.ny, face.nz
					end
					local cf = table.clone(p.cf)
					cf[1] += nx * step
					cf[2] += ny * step
					cf[3] += nz * step
					p.cf = cf
				else
					local s = p.size
					p.size = { s[1] + step * 2, s[2] + step * 2, s[3] + step * 2 }
				end
			end
		end
	end
	return fixes
end

return Overlap
