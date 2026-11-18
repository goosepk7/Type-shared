"""Shared sculpt helpers for the dragon and mythic-beast heroes (h_dragons*.py, h_mythic*.py).

NOTE: build.py hashes only the h_*.py module + kit.py, so a change here does not invalidate cached pieces by itself:
rebuild the affected heroes with --force after editing this file.

Thin sheets (wing membranes, fins, frills) are unions of exact triangle distance fields with a thickness, so a
membrane can be fanned from a wrist to finger tips with a scalloped, billowing trailing edge. Feathers are oriented,
flattened ellipsoids / tubes. Everything returns sdf.SDF objects in model space.
"""
import math

import numpy as np

import sdf as S


def V(*a):
    if len(a) == 1:
        return np.asarray(a[0], float)
    return np.asarray(a, float)


def nrm(v):
    v = np.asarray(v, float)
    return v / max(np.linalg.norm(v), 1e-9)


# ------------------------------------------------------------------------------------------------ sheets
def tri(a, b, c, t):
    """Triangle a b c thickened to half thickness t (rounded edges)."""
    a, b, c = V(a), V(b), V(c)
    ba, cb, ac = b - a, c - b, a - c
    nor = np.cross(ba, ac)
    nn = max(float(nor @ nor), 1e-12)
    n_ba, n_cb, n_ac = np.cross(ba, nor), np.cross(cb, nor), np.cross(ac, nor)
    lba, lcb, lac = max(ba @ ba, 1e-12), max(cb @ cb, 1e-12), max(ac @ ac, 1e-12)

    def f(p):
        pa, pb, pc = p - a, p - b, p - c
        s = np.sign(pa @ n_ba) + np.sign(pb @ n_cb) + np.sign(pc @ n_ac)
        e1 = np.clip((pa @ ba) / lba, 0, 1)[:, None] * ba - pa
        e2 = np.clip((pb @ cb) / lcb, 0, 1)[:, None] * cb - pb
        e3 = np.clip((pc @ ac) / lac, 0, 1)[:, None] * ac - pc
        edge = np.minimum(np.minimum((e1 * e1).sum(1), (e2 * e2).sum(1)), (e3 * e3).sum(1))
        face = (pa @ nor) ** 2 / nn
        return np.sqrt(np.where(s < 2, edge, face)) - t

    pts = np.stack([a, b, c])
    return bounded(S.SDF(f), pts.min(0), pts.max(0), max(4 * t, 0.2))


def union_hard(shapes):
    shapes = [s for s in shapes if s is not None]

    def f(p):
        d = shapes[0](p)
        for s in shapes[1:]:
            d = np.minimum(d, s(p))
        return d

    return S.SDF(f)


def bounded(shape, lo, hi, pad=0.3):
    """Speed-up wrapper: outside the box [lo, hi] (+pad) return the box distance instead of evaluating shape."""
    lo, hi = V(lo) - pad, V(hi) + pad
    c, h = (lo + hi) / 2, (hi - lo) / 2

    def f(p):
        q = np.abs(p - c) - h
        out = np.linalg.norm(np.maximum(q, 0), axis=1)
        d = out + pad * 0.5
        m = out <= 0
        if m.any():
            d[m] = shape(p[m])
        return d

    return S.SDF(f)


def scallop(a, b, toward, depth=0.2, sag=0.0, down=None, n=4):
    """Points from a to b (excluded a, included b) with the middle pulled toward `toward` (a scalloped trailing
    edge) and sagging along -down."""
    a, b, toward = V(a), V(b), V(toward)
    out = []
    for i in range(1, n + 1):
        u = i / n
        p = a + (b - a) * u
        k = math.sin(math.pi * u)
        p = p + (toward - p) * depth * k
        if down is not None:
            p = p - V(down) * sag * k
        out.append(p)
    return out


def fan(center, poly, t):
    """Triangle fan from center over the polyline poly (a membrane panel set)."""
    c = V(center)
    return union_hard([tri(c, V(poly[i]), V(poly[i + 1]), t) for i in range(len(poly) - 1)])


def membrane(wrist, tips, t=0.05, depth=0.22, sag=0.18, up=None, n=4, tail=None):
    """Outer wing membrane: panels between consecutive finger tips, fanned from the wrist; each trailing edge is
    scalloped toward the wrist and sags along -up. tail: optional extra polyline appended after the last tip."""
    W = V(wrist)
    poly = [V(tips[0])]
    for a, b in zip(tips[:-1], tips[1:]):
        poly += scallop(a, b, W, depth, sag, up, n)
    if tail:
        poly += [V(q) for q in tail]
    return fan(W, poly, t)


# ------------------------------------------------------------------------------------------------ oriented shapes
def frame(d, up=(0, 1, 0)):
    """Orthonormal frame (columns: d, side, normal) with d forward and normal as close to `up` as possible."""
    d = nrm(d)
    up = nrm(up)
    if abs(d @ up) > 0.98:
        up = nrm((0.0, 0.0, 1.0) if abs(d[2]) < 0.9 else (1.0, 0.0, 0.0))
    side = nrm(np.cross(up, d))
    n = np.cross(d, side)
    return np.stack([d, side, n], axis=1)


def oell(c, R, radii):
    """Ellipsoid centred at c whose axes are the columns of R."""
    c = V(c)
    r = V(radii)
    base = S.ellipsoid(*r)
    return S.SDF(lambda p: base((p - c) @ R))


def squash(shape, c, axis, f):
    """Squash shape about point c along unit axis by factor f (<1 flattens)."""
    c, axis = V(c), nrm(axis)
    k = 1.0 / f - 1.0

    def g(p):
        q = p + (((p - c) @ axis) * k)[:, None] * axis
        return shape(q) * f

    return S.SDF(g)


def flat_tube(points, radii, normal, flat=0.35, k=0.0):
    """A tube through points, flattened along `normal` (blades, feathers, flames, fins)."""
    pts = [V(q) for q in points]
    c = sum(pts) / len(pts)
    return squash(S.tube(pts, radii, k=k), c, normal, flat)


def feather(p0, d, L, w, normal, th=0.045, curl=0.0):
    """Leaf-shaped feather from p0 along d (length L, half width w), face normal `normal`. curl bends the tip
    along -normal."""
    d = nrm(d)
    n = nrm(normal - (normal @ d) * d) if abs(nrm(normal) @ d) < 0.99 else nrm(np.cross(d, (1, 0, 0)))
    p0 = V(p0)
    pts = [p0, p0 + d * L * 0.35, p0 + d * L * 0.75 - n * curl * 0.5, p0 + d * L - n * curl]
    rad = [w * 0.45, w, w * 0.8, w * 0.12]
    return flat_tube(pts, rad, n, flat=th / max(w, 1e-6))


def spike(base, d, h, r, tip=0.15):
    """Round cone spike from base along d."""
    b = V(base)
    return S.round_cone(b, b + nrm(d) * h, r, r * tip)


def curved_horn(pts, r0, r1):
    """Tapering horn through points (radius r0 at the root to r1 at the tip)."""
    n = len(pts)
    rad = [r0 + (r1 - r0) * (i / (n - 1)) ** 0.8 for i in range(n)]
    return S.tube([V(q) for q in pts], rad, k=0.0)


def blade_fin(base, d, h, r, side_axis, flat=0.35, back=None):
    """A flattened triangular dorsal spine (fin plate) from base along d, thin across side_axis."""
    b = V(base)
    tipp = b + nrm(d) * h
    if back is not None:
        tipp = tipp + V(back) * h * 0.45
    c = S.round_cone(b, tipp, r, r * 0.12)
    return squash(c, b, side_axis, flat)


def surface_y(shape, x, z, ytop, ybot, n=400):
    """Highest y in [ybot, ytop] where shape(x, y, z) <= 0 (top of a body at (x, z))."""
    ys = np.linspace(ytop, ybot, n)
    P = np.column_stack([np.full(n, x), ys, np.full(n, z)])
    d = shape(P)
    idx = np.argmax(d <= 0)
    if d[idx] > 0:
        return ybot
    return float(ys[idx])


def bez(p0, p1, p2, p3, n):
    """Cubic Bezier points (n samples, ends included)."""
    p0, p1, p2, p3 = V(p0), V(p1), V(p2), V(p3)
    out = []
    for i in range(n):
        t = i / (n - 1)
        out.append((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3)
    return out


def outside(core, amount=0.04, dark=0.5, soft=0.08):
    """Pattern mask: darken points that lie outside `core` (spines, claws, ridges sculpted onto a body) so they read
    as darker horn without a separate part."""

    def f(P):
        d = core(P)
        t = np.clip((d - amount) / soft, 0, 1)
        return 1 - (1 - dark) * t

    return f


def band_y(lo, hi, a=1.0, b=0.75):
    """Shade between heights (countershading: b on the back, a under the belly)."""

    def f(P):
        t = np.clip((P[:, 1] - lo) / (hi - lo), 0, 1)
        return a + (b - a) * t

    return f


def mxc(shape, cx):
    """mirror_x about the plane x = cx (for heads that are not on the model's centre line)."""
    cx = float(cx)

    def f(p):
        q = p.copy()
        q[:, 0] = cx + np.abs(p[:, 0] - cx)
        return shape(q)

    return S.SDF(f)


def eyes_c(H, bone, cx, pos, r, col="iris", pupil="slit", shine=True, pri=1.2, look=(0.25, 0.0, -1.0)):
    """kit.Hero.eyes mirrored about x = cx instead of the model centre line (side heads of multi-headed beasts)."""
    x, y, z = pos
    dx = x - cx
    d = nrm(look)
    for side in (1, -1):
        px = cx + dx * side
        nm = "R" if side > 0 else "L"
        pair = None
        H.prim(f"Eye{bone}{nm}", bone, "Ball", (r * 2,) * 3, (px, y, z), col=col, mat="hard", pri=pri, role="eye")
        if pupil:
            c = (px + side * d[0] * r * 0.8, y + d[1] * r * 0.8, z + d[2] * r * 0.8)
            size = (r * 0.42, r * 1.25, r * 0.42) if pupil == "slit" else (r * 1.05,) * 3
            ry = math.atan2(-d[0] * side, -d[2])
            H.prim(f"Pupil{bone}{nm}", bone, "Ellipsoid" if pupil == "slit" else "Ball", size, c, rot=(0, ry, 0), col="pupil", mat="hard", pri=pri + 0.1, role="pupil")
        if shine:
            c = (px + side * (d[0] * r * 0.85 + r * 0.05), y + r * 0.4, z + d[2] * r * 0.85)
            H.prim(f"Shine{bone}{nm}", bone, "Ball", (r * 0.42,) * 3, c, col="shine", mat="hard", pri=pri + 1.4, role="shine")


class Shift:
    """Proxy for a Hero that moves everything built through it by dx along X. Head builders sculpt a head centred on
    x = 0 (so mirror_x / mprim / eyes mirror about the head's own centre) and a side head of a multi-headed beast is
    built through Shift(H, its x)."""

    def __init__(self, H, dx):
        self.H, self.dx = H, float(dx)

    def __getattr__(self, k):
        return getattr(self.H, k)

    def _p(self, pos):
        return (pos[0] + self.dx, pos[1], pos[2])

    def bone(self, name, parent, pos):
        return self.H.bone(name, parent, self._p(pos))

    def bpos(self, name):
        return self.H.bpos(name) - V(self.dx, 0, 0)

    def piece(self, name, bone, shape, pattern=None, **kw):
        dx = self.dx
        pat = None
        if pattern is not None:
            def pat(P, _p=pattern):
                Q = P.copy()
                Q[:, 0] -= dx
                return _p(Q)
        return self.H.piece(name, bone, shape.at(dx, 0, 0), pattern=pat, **kw)

    def prim(self, name, bone, shape, size, pos, **kw):
        return self.H.prim(name, bone, shape, size, self._p(pos), **kw)

    def mprim(self, name, bone, shape, size, pos, rot=(0, 0, 0), **kw):
        for side, nm in ((1, "R"), (-1, "L")):
            self.H.prim(name.replace("#", nm), bone, shape, size, (pos[0] * side + self.dx, pos[1], pos[2]),
                        rot=(rot[0], rot[1] * side, rot[2] * side), **kw)

    def eyes(self, bone, pos, r, **kw):
        eyes_c(self.H, bone, self.dx, self._p(pos), r, **kw)

    def socket(self, name, pos, bone="Body"):
        return self.H.socket(name, self._p(pos), bone)
