--!strict
-- Pure CFrame-like math for the blueprint stage. Runs under Lune and Roblox identically (no Roblox datatypes),
-- so blueprints are bit-for-bit deterministic everywhere.
--
-- A frame is a 12-number array laid out exactly like CFrame.new(x, y, z, R00, R01, R02, R10, R11, R12, R20, R21, R22):
--   { x, y, z, r00, r01, r02, r10, r11, r12, r20, r21, r22 }   (row-major rotation; columns = right, up, back)

export type Frame = { number }
export type Vec = { number } -- {x, y, z}

local Geom = {}

local sin, cos, sqrt = math.sin, math.cos, math.sqrt

function Geom.new(x: number?, y: number?, z: number?): Frame
	return { x or 0, y or 0, z or 0, 1, 0, 0, 0, 1, 0, 0, 0, 1 }
end

-- Rotation part only (matches CFrame.Angles(rx, ry, rz) = Rx * Ry * Rz).
function Geom.angles(rx: number, ry: number, rz: number): Frame
	local cx, sx = cos(rx), sin(rx)
	local cy, sy = cos(ry), sin(ry)
	local cz, sz = cos(rz), sin(rz)
	-- Rx * Ry * Rz
	return {
		0, 0, 0,
		cy * cz, -cy * sz, sy,
		cx * sz + sx * sy * cz, cx * cz - sx * sy * sz, -sx * cy,
		sx * sz - cx * sy * cz, sx * cz + cx * sy * sz, cx * cy,
	}
end

-- Position + Euler (radians) in one call.
function Geom.at(x: number, y: number, z: number, rx: number?, ry: number?, rz: number?): Frame
	local f = Geom.angles(rx or 0, ry or 0, rz or 0)
	f[1], f[2], f[3] = x, y, z
	return f
end

function Geom.mul(a: Frame, b: Frame): Frame
	local a00, a01, a02, a10, a11, a12, a20, a21, a22 = a[4], a[5], a[6], a[7], a[8], a[9], a[10], a[11], a[12]
	local b00, b01, b02, b10, b11, b12, b20, b21, b22 = b[4], b[5], b[6], b[7], b[8], b[9], b[10], b[11], b[12]
	return {
		a[1] + a00 * b[1] + a01 * b[2] + a02 * b[3],
		a[2] + a10 * b[1] + a11 * b[2] + a12 * b[3],
		a[3] + a20 * b[1] + a21 * b[2] + a22 * b[3],
		a00 * b00 + a01 * b10 + a02 * b20, a00 * b01 + a01 * b11 + a02 * b21, a00 * b02 + a01 * b12 + a02 * b22,
		a10 * b00 + a11 * b10 + a12 * b20, a10 * b01 + a11 * b11 + a12 * b21, a10 * b02 + a11 * b12 + a12 * b22,
		a20 * b00 + a21 * b10 + a22 * b20, a20 * b01 + a21 * b11 + a22 * b21, a20 * b02 + a21 * b12 + a22 * b22,
	}
end

function Geom.inverse(f: Frame): Frame
	-- R^T, -R^T p
	local r00, r01, r02, r10, r11, r12, r20, r21, r22 = f[4], f[5], f[6], f[7], f[8], f[9], f[10], f[11], f[12]
	local x, y, z = f[1], f[2], f[3]
	return {
		-(r00 * x + r10 * y + r20 * z), -(r01 * x + r11 * y + r21 * z), -(r02 * x + r12 * y + r22 * z),
		r00, r10, r20, r01, r11, r21, r02, r12, r22,
	}
end

-- Transform a local point into the frame's parent space.
function Geom.point(f: Frame, x: number, y: number, z: number): (number, number, number)
	return f[1] + f[4] * x + f[5] * y + f[6] * z, f[2] + f[7] * x + f[8] * y + f[9] * z, f[3] + f[10] * x + f[11] * y + f[12] * z
end

-- Rotate a direction (no translation).
function Geom.vector(f: Frame, x: number, y: number, z: number): (number, number, number)
	return f[4] * x + f[5] * y + f[6] * z, f[7] * x + f[8] * y + f[9] * z, f[10] * x + f[11] * y + f[12] * z
end

-- Frame translated by a local offset.
function Geom.offset(f: Frame, x: number, y: number, z: number): Frame
	local c = table.clone(f)
	c[1], c[2], c[3] = Geom.point(f, x, y, z)
	return c
end

-- Mirror a frame across the YZ plane (x -> -x) keeping a right-handed basis: R' = S R S, S = diag(-1, 1, 1).
function Geom.mirrorX(f: Frame): Frame
	return {
		-f[1], f[2], f[3],
		f[4], -f[5], -f[6],
		-f[7], f[8], f[9],
		-f[10], f[11], f[12],
	}
end

local function normalize(x: number, y: number, z: number): (number, number, number)
	local m = sqrt(x * x + y * y + z * z)
	if m < 1e-9 then
		return 0, 1, 0
	end
	return x / m, y / m, z / m
end
Geom.normalize = normalize

local function cross(ax: number, ay: number, az: number, bx: number, by: number, bz: number): (number, number, number)
	return ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
end
Geom.cross = cross

-- Frame at the midpoint of a->b whose `axis` ("X" or "Y" or "Z") points from a to b. `up` hints the roll.
function Geom.between(ax: number, ay: number, az: number, bx: number, by: number, bz: number, axis: string?): (Frame, number)
	local dx, dy, dz = bx - ax, by - ay, bz - az
	local len = sqrt(dx * dx + dy * dy + dz * dz)
	local fx, fy, fz = normalize(dx, dy, dz)
	-- pick a helper not parallel to f
	local hx, hy, hz = 0, 0, 1
	if math.abs(fz) > 0.9 then
		hx, hy, hz = 1, 0, 0
	end
	local ux, uy, uz = normalize(cross(hx, hy, hz, fx, fy, fz)) -- perpendicular 1
	local vx, vy, vz = cross(fx, fy, fz, ux, uy, uz) -- perpendicular 2
	local mx, my, mz = (ax + bx) / 2, (ay + by) / 2, (az + bz) / 2
	axis = axis or "Y"
	local f: Frame
	if axis == "X" then
		-- columns: X=f, Y=v, Z=u... keep right-handed: X cross Y = Z
		f = { mx, my, mz, fx, vx, ux, fy, vy, uy, fz, vz, uz }
		-- check handedness: f x v should equal u
		local cx, cy, cz = cross(fx, fy, fz, vx, vy, vz)
		if cx * ux + cy * uy + cz * uz < 0 then
			f = { mx, my, mz, fx, vx, -ux, fy, vy, -uy, fz, vz, -uz }
		end
	elseif axis == "Z" then
		f = { mx, my, mz, ux, vx, fx, uy, vy, fy, uz, vz, fz }
		local cx, cy, cz = cross(ux, uy, uz, vx, vy, vz)
		if cx * fx + cy * fy + cz * fz < 0 then
			f = { mx, my, mz, -ux, vx, fx, -uy, vy, fy, -uz, vz, fz }
		end
	else
		f = { mx, my, mz, ux, fx, vx, uy, fy, vy, uz, fz, vz }
		local cx, cy, cz = cross(ux, uy, uz, fx, fy, fz)
		if cx * vx + cy * vy + cz * vz < 0 then
			f = { mx, my, mz, -ux, fx, vx, -uy, fy, vy, -uz, fz, vz }
		end
	end
	return f, len
end

-- Roll a frame about its own Y axis so that local +Z points as close to (tx, ty, tz) as it can. For a part that is
-- round about Y (a limb ellipsoid with equal width and depth) the primitive looks the same; a sculpt on it gets a
-- known "under side". Returns the frame unchanged when the target is parallel to Y.
function Geom.rollY(f: Frame, tx: number, ty: number, tz: number): Frame
	local fx, fy, fz = f[5], f[8], f[11]
	local d = tx * fx + ty * fy + tz * fz
	local vx, vy, vz = tx - d * fx, ty - d * fy, tz - d * fz
	local l = sqrt(vx * vx + vy * vy + vz * vz)
	if l < 1e-4 then
		return f
	end
	vx, vy, vz = vx / l, vy / l, vz / l
	local ux, uy, uz = cross(fx, fy, fz, vx, vy, vz)
	return { f[1], f[2], f[3], ux, fx, vx, uy, fy, vy, uz, fz, vz }
end

-- Uniformly scale a frame's translation (rotation unchanged).
function Geom.scaled(f: Frame, k: number): Frame
	local c = table.clone(f)
	c[1], c[2], c[3] = f[1] * k, f[2] * k, f[3] * k
	return c
end

-- Round to 1e-4 so float noise can never differ between platforms in serialized output.
function Geom.round(f: Frame): Frame
	local c = table.create(12)
	for i = 1, 12 do
		c[i] = math.floor(f[i] * 10000 + 0.5) / 10000
	end
	return c
end

return Geom
