"""Signed-distance sculpting kit for tools/meshgen.

Every shape is an `SDF`: a callable that maps an (N, 3) float array of points to (N,) signed distances
(negative inside). Shapes compose with operators and Python operators:

    a | b          union                    a & b        intersection
    a - b          subtraction
    a.su(b, k)     smooth union (k = blend radius in model units)
    a.ss(b, k)     smooth subtraction
    a.si(b, k)     smooth intersection
    a.at(x, y, z)  translate               a.rot(rx, ry, rz)   rotate (degrees, XYZ order)
    a.scale(s)     uniform scale            a.shell(t)          hollow shell of thickness t
    a.round(r)     inflate by r             a.warp(fn)          arbitrary domain warp p -> p'
    a.twist(k, axis) / a.bend(k) / a.noise(amp, freq, seed)    organic domain warps

Primitives: sphere, ellipsoid, capsule, round_cone (two radii capsule), round_box, torus, cylinder,
cone (capped, rounded), plane, and `tube(points, radii)`: a smooth chain of round cones through
control points (tails, tentacles, horns, limbs).

Conventions used by the catalogue: +Y up, -Z is the FRONT of the piece (Roblox forward), +X right.
"""
from __future__ import annotations

import numpy as np


def _rotm(rx: float, ry: float, rz: float) -> np.ndarray:
    rx, ry, rz = np.radians([rx, ry, rz])
    cx, sx, cy, sy, cz, sz = np.cos(rx), np.sin(rx), np.cos(ry), np.sin(ry), np.cos(rz), np.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


class SDF:
    def __init__(self, f):
        self.f = f

    def __call__(self, p):
        return self.f(p)

    # ---- boolean
    def __or__(self, o):
        return SDF(lambda p: np.minimum(self(p), o(p)))

    def __and__(self, o):
        return SDF(lambda p: np.maximum(self(p), o(p)))

    def __sub__(self, o):
        return SDF(lambda p: np.maximum(self(p), -o(p)))

    def su(self, o, k=0.1):
        return SDF(lambda p: smin(self(p), o(p), k))

    def ss(self, o, k=0.1):
        return SDF(lambda p: smax(self(p), -o(p), k))

    def si(self, o, k=0.1):
        return SDF(lambda p: smax(self(p), o(p), k))

    # ---- transforms
    def at(self, x=0.0, y=0.0, z=0.0):
        t = np.array([x, y, z], dtype=float)
        return SDF(lambda p: self(p - t))

    def rot(self, rx=0.0, ry=0.0, rz=0.0):
        R = _rotm(rx, ry, rz)
        return SDF(lambda p: self(p @ R))  # p @ R == (R^T p^T)^T : inverse rotation of the point

    def scale(self, s):
        return SDF(lambda p: self(p / s) * s)

    def scale3(self, sx, sy, sz):
        """Non-uniform scale (distance is approximate; fine for marching cubes)."""
        s = np.array([sx, sy, sz], dtype=float)
        m = min(sx, sy, sz)
        return SDF(lambda p: self(p / s) * m)

    def round(self, r):
        return SDF(lambda p: self(p) - r)

    def shell(self, t):
        return SDF(lambda p: np.abs(self(p)) - t)

    def mirror_x(self):
        return SDF(lambda p: self(np.column_stack([np.abs(p[:, 0]), p[:, 1], p[:, 2]])))

    def warp(self, fn):
        return SDF(lambda p: self(fn(p)))

    def twist(self, k, axis=1):
        """Rotate about `axis` by k radians per unit along it."""
        a = [0, 1, 2]
        a.remove(axis)
        i, j = a

        def fn(p):
            ang = k * p[:, axis]
            c, s = np.cos(ang), np.sin(ang)
            q = p.copy()
            q[:, i] = c * p[:, i] - s * p[:, j]
            q[:, j] = s * p[:, i] + c * p[:, j]
            return q

        return self.warp(fn)

    def bend(self, k, axis=1, toward=2):
        """Bend the shape: points along `axis` get displaced along `toward` by k * axis^2."""

        def fn(p):
            q = p.copy()
            q[:, toward] = p[:, toward] - k * p[:, axis] ** 2
            return q

        return self.warp(fn)

    def noise(self, amp=0.02, freq=6.0, seed=0):
        """Cheap smooth value-noise displacement (sum of 3 sinusoid octaves, deterministic)."""
        rng = np.random.default_rng(seed)
        dirs = rng.normal(size=(6, 3))
        dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
        ph = rng.uniform(0, 6.283, 6)

        def f(p):
            d = self(p)
            n = np.zeros(len(p))
            for o in range(6):
                fr = freq * (1.0 + 0.7 * o)
                n += np.sin(p @ dirs[o] * fr + ph[o]) / (1.0 + 0.7 * o)
            return d + amp * n / 2.2

        return SDF(f)


# ---------------------------------------------------------------- primitives
def sphere(r, c=(0, 0, 0)):
    c = np.asarray(c, float)
    return SDF(lambda p: np.linalg.norm(p - c, axis=1) - r)


def ellipsoid(rx, ry, rz, c=(0, 0, 0)):
    r = np.array([rx, ry, rz], float)
    c = np.asarray(c, float)

    def f(p):
        q = p - c
        k0 = np.linalg.norm(q / r, axis=1)
        k1 = np.linalg.norm(q / (r * r), axis=1)
        return np.where(k1 > 1e-9, k0 * (k0 - 1.0) / np.maximum(k1, 1e-9), -r.min())

    return SDF(f)


def capsule(a, b, r):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ba = b - a
    L = ba @ ba

    def f(p):
        pa = p - a
        h = np.clip((pa @ ba) / L, 0, 1)
        return np.linalg.norm(pa - h[:, None] * ba, axis=1) - r

    return SDF(f)


def round_cone(a, b, ra, rb):
    """Capsule with different end radii (exact SDF, iq)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ba = b - a
    l2 = ba @ ba
    rr = ra - rb
    a2 = l2 - rr * rr
    il2 = 1.0 / l2

    def f(p):
        pa = p - a
        y = pa @ ba
        z = y - l2
        xv = pa * l2 - y[:, None] * ba
        x2 = (xv * xv).sum(1)
        y2 = y * y * l2
        z2 = z * z * l2
        k = np.sign(rr) * rr * rr * x2
        d1 = np.sqrt(x2 + z2) * il2 - rb
        d2 = np.sqrt(x2 + y2) * il2 - ra
        d3 = (np.sqrt(x2 * a2 * il2) + y * rr) * il2 - ra
        return np.where(np.sign(z) * a2 * z2 > k, d1, np.where(np.sign(y) * a2 * y2 < k, d2, d3))

    return SDF(f)


def tube(points, radii, k=0.0):
    """Smooth chain of round cones through control points. radii: one per point."""
    pts = [np.asarray(q, float) for q in points]
    s = round_cone(pts[0], pts[1], radii[0], radii[1])
    for i in range(1, len(pts) - 1):
        seg = round_cone(pts[i], pts[i + 1], radii[i], radii[i + 1])
        s = s.su(seg, k) if k > 0 else (s | seg)
    return s


def round_box(hx, hy, hz, r, c=(0, 0, 0)):
    b = np.array([hx - r, hy - r, hz - r], float)
    c = np.asarray(c, float)

    def f(p):
        q = np.abs(p - c) - b
        return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0) - r

    return SDF(f)


def box(hx, hy, hz, c=(0, 0, 0)):
    return round_box(hx, hy, hz, 0.0, c)


def torus(R, r, axis=1):
    """Ring around `axis` (default Y: lying flat)."""
    a = [0, 1, 2]
    a.remove(axis)

    def f(p):
        q = np.linalg.norm(p[:, a], axis=1) - R
        return np.sqrt(q * q + p[:, axis] ** 2) - r

    return SDF(f)


def cylinder(r, h, axis=1, rr=0.0):
    """Capped cylinder along axis with half-height h, rounded edge rr."""
    a = [0, 1, 2]
    a.remove(axis)

    def f(p):
        d0 = np.linalg.norm(p[:, a], axis=1) - (r - rr)
        d1 = np.abs(p[:, axis]) - (h - rr)
        return np.minimum(np.maximum(d0, d1), 0) + np.sqrt(np.maximum(d0, 0) ** 2 + np.maximum(d1, 0) ** 2) - rr

    return SDF(f)


def cone(r0, r1, h, axis=1, rr=0.0):
    """Capped cone along axis from -h (radius r0) to +h (radius r1), optional rounding."""
    a = [0, 1, 2]
    a.remove(axis)

    def f(p):
        qx = np.linalg.norm(p[:, a], axis=1)
        qy = p[:, axis]
        k1 = np.array([r1, h])
        k2 = np.array([r1 - r0, 2 * h])
        cax = qx - np.minimum(qx, np.where(qy < 0, r0, r1))
        cay = np.abs(qy) - h
        q = np.stack([qx, qy], 1)
        t = np.clip(((k1 - q) @ k2) / (k2 @ k2), 0, 1)
        cb = q - k1 + t[:, None] * k2
        s = np.where((cb[:, 0] < 0) & (cay < 0), -1.0, 1.0)
        d = np.sqrt(np.minimum(cax * cax + cay * cay, (cb * cb).sum(1)))
        return s * d - rr

    return SDF(f)


def plane(n=(0, 1, 0), d=0.0):
    n = np.asarray(n, float)
    n = n / np.linalg.norm(n)
    return SDF(lambda p: p @ n - d)


def half_space(axis, sign, at=0.0):
    """Keep points with sign*(p[axis]-at) <= 0 (use with & to slice)."""
    return SDF(lambda p: sign * (p[:, axis] - at))


def union(*shapes, k=0.0):
    s = shapes[0]
    for o in shapes[1:]:
        s = s.su(o, k) if k > 0 else (s | o)
    return s
