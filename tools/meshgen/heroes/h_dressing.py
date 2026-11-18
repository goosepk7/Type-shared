"""Element dressing kit: sculpted add-on pieces that make elemental variants of any creature read as Fire / Ice /
Lightning / Earth / Nature / Water / Wind / Shadow / Light / Arcane / Poison / Metal instead of a plain recolour
("ice tiger", "fire wolf", "storm eagle", "stone bear").

Every piece is authored in a UNIT frame: it fits the 1 x 1 x 1 box centred at the origin (+Y up, -Z front, +X right)
and the engine scales / places it on a creature. Anchors:

  Back      along the spine on top of the torso: long axis Z (front -Z), base at y = -0.5 with a slightly concave
            underside (hugs a rounded back), the dressing rises toward +Y.
  Head      on top of the head: base at y = -0.5, centred, front -Z.
  TailTip   sleeve / ornament on the end of a tail: the tail runs along +Z, it attaches at z = -0.5 (toward the body) and
            the ornament ends at z = +0.5.
  Shoulder  RIGHT shoulder (+X); the base sits on the shoulder top at the -X / -Y corner and the dressing flares up and
            out (+X, +Y). ShoulderL is the mirrored copy (mesh "<key>_l").
  Cuff      ring around a leg just above the paw / hoof: axis Y, open centre (inner radius ~0.27) so the leg passes
            through; ornaments stay inside the unit box.

One Hero per element ("dressing_<element>") is the container: anchor bones lay the pieces out side by side for the
preview (back row: ShoulderL, Back, ShoulderR; upper row: Head, TailTip, Cuff). The mesh of each piece is re-centred
on its own bounds by the mesher, so the .glb is the unit-frame piece itself.
"""
import math

import numpy as np

from sdf import SDF, sphere, ellipsoid, capsule, round_cone, tube, round_box, box, torus, cylinder, cone, half_space
from kit import Hero, hero, gradient, combine, spots, stripes

FAM = "dressing"
LAY = {"Back": (0.0, 0.6, 0.0), "Head": (-1.35, 1.95, 0.0), "TailTip": (0.0, 1.95, 0.0), "Cuff": (1.35, 1.95, 0.0),
       "Shoulder": (1.35, 0.6, 0.0)}


# ================================================================================================ sdf helpers
def _poly2(P):
    """Signed distance to a 2D polygon (iq), returned as f(u, v)."""
    P = np.asarray(P, float)
    n = len(P)

    def f(u, v):
        d = (u - P[0, 0]) ** 2 + (v - P[0, 1]) ** 2
        s = np.ones_like(u)
        j = n - 1
        for i in range(n):
            ex, ey = P[j, 0] - P[i, 0], P[j, 1] - P[i, 1]
            wx, wy = u - P[i, 0], v - P[i, 1]
            h = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
            bx, by = wx - ex * h, wy - ey * h
            d = np.minimum(d, bx * bx + by * by)
            c1 = v >= P[i, 1]
            c2 = v < P[j, 1]
            c3 = ex * wy > ey * wx
            flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
            s = np.where(flip, -s, s)
            j = i
        return s * np.sqrt(d)

    return f


def extrude(P, th, r=0.0, plane="zy"):
    """A 2D outline P (in the (u, v) = plane axes) extruded `th` either side along the remaining axis, edges rounded r."""
    ax = {"x": 0, "y": 1, "z": 2}
    ui, vi = ax[plane[0]], ax[plane[1]]
    wi = 3 - ui - vi
    f2 = _poly2(P)

    def f(p):
        d2 = f2(p[:, ui], p[:, vi]) + r
        dw = np.abs(p[:, wi]) - th + r
        return np.minimum(np.maximum(d2, dw), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(dw, 0) ** 2) - r

    return SDF(f)


def facet(c, r, n=9, seed=0, squash=(1.0, 1.0, 1.0), jitter=0.18):
    """Faceted rock: intersection of n jittered planes around c (a convex chunk with flat faces)."""
    rng = np.random.default_rng(seed)
    # always bounded: the 8 cube-corner directions (jittered) plus n random ones
    base = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float) + rng.normal(scale=0.25, size=(8, 3))
    N = np.vstack([base, rng.normal(size=(n, 3))])
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    n = len(N)
    D = r * (1 + rng.uniform(-jitter, jitter, n))
    c = np.asarray(c, float)
    sq = np.asarray(squash, float)

    def f(p):
        q = (p - c) / sq
        return (q @ N.T - D).max(1) * sq.min()

    return SDF(f)


def crystal(base, direction, length, r, tip=0.35, sides=6, twist=0.0):
    """Faceted crystal prism from `base` along `direction`: `sides` flat faces, a pyramidal point of `tip` x length."""
    d = np.asarray(direction, float)
    d /= np.linalg.norm(d)
    a = np.array([1.0, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 0, 1.0])
    e1 = np.cross(d, a)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(d, e1)
    b = np.asarray(base, float)
    L = length
    ht = L * tip
    ang = [twist + k / sides * math.tau for k in range(sides)]
    slope = r / ht

    def f(p):
        q = p - b
        y = q @ d
        x1, x2 = q @ e1, q @ e2
        dist = np.full(len(p), -1e9)
        for t in ang:
            rad = x1 * math.cos(t) + x2 * math.sin(t)
            dist = np.maximum(dist, rad - r)
            # tip facet: plane through the rim at y = L - ht and the apex at y = L
            dist = np.maximum(dist, (rad + (y - (L - ht)) * slope - r) / math.sqrt(1 + slope * slope))
        dist = np.maximum(dist, -y)
        return dist

    return SDF(f)


def curve(pts, radii, k=0.03):
    return tube(pts, radii, k=k)


def flame(base, h, r, lean=(0.0, 0.0), sway=0.12, seed=0, curl=1.0):
    """A stylised flame tongue: a fat base tapering through an S-curve to a sharp tip."""
    rng = np.random.default_rng(seed)
    b = np.asarray(base, float)
    ph = rng.uniform(0, math.tau)
    pts, rad = [], []
    n = 6
    for i in range(n):
        t = i / (n - 1)
        off = math.sin(ph + t * 3.2) * sway * t * curl
        pts.append(tuple(b + np.array([lean[0] * t * t * h + off * 0.6, t * h, lean[1] * t * t * h + off])))
        rad.append(r * (1 - t) ** 0.85 * (1 + 0.25 * math.sin(t * 3.1)) + 0.004)
    return tube(pts, rad, k=0.02)


def leaf(base, direction, L, W, th=0.018, bend=0.25, up=(0, 1, 0)):
    """Pointed leaf / feather blade from `base` along `direction`, flat in the plane spanned with `up`, curved by bend."""
    out = []
    for i in range(13):
        t = i / 12
        out.append((t * L, W * math.sin(math.pi * t) ** 0.8 * (1 - 0.25 * t)))
    for i in range(11, 0, -1):
        t = i / 12
        out.append((t * L, -W * math.sin(math.pi * t) ** 0.8 * (1 - 0.25 * t)))
    shp = extrude(out, th, r=th * 0.8, plane="xy")          # long axis +X, width Y, thickness Z

    def bendw(p):
        q = p.copy()
        q[:, 2] = p[:, 2] - bend * (p[:, 0] / max(L, 1e-6)) ** 2 * L
        return q

    shp = shp.warp(bendw)
    shp = shp.ss(box(L * 0.45, 0.004, th * 3).at(L * 0.5, 0, th * 1.4), 0.006)      # midrib groove
    d = np.asarray(direction, float)
    d /= np.linalg.norm(d)
    u = np.asarray(up, float)
    n = np.cross(d, u)
    if np.linalg.norm(n) < 1e-6:
        n = np.cross(d, [1.0, 0, 0])
    n /= np.linalg.norm(n)
    w = np.cross(n, d)
    R = np.stack([d, w, n], 1)       # local x->d, y->w, z->n
    b = np.asarray(base, float)
    return SDF(lambda p: shp((p - b) @ R))


def place(sd, R, t):
    """Rotate a shape by the 3x3 matrix R (local->world columns) and move it to t."""
    t = np.asarray(t, float)
    return SDF(lambda p: sd((p - t) @ R))


def saddle(sd, r=1.25, depth=0.5):
    """Hollow the underside so a back piece hugs a rounded back (a big cylinder along Z under y = -depth)."""
    return sd - cylinder(r, 2.0, axis=2).at(0, -depth - r, 0)


def ring(r_in, r_out, h, y=0.0, rr=0.03):
    """A flat band (axis Y) between radii r_in .. r_out, height 2h."""
    return cylinder(r_out, h, axis=1, rr=rr).at(0, y, 0) - cylinder(r_in, h + 0.1, axis=1).at(0, y, 0)


def helix(R, pitch, turns, r0, r1, y0=0.0, ph=0.0, n=40):
    pts, rad = [], []
    for i in range(n):
        t = i / (n - 1)
        a = ph + t * turns * math.tau
        pts.append((R * math.cos(a), y0 + t * pitch * turns, R * math.sin(a)))
        rad.append(r0 + (r1 - r0) * t)
    return tube(pts, rad, k=0.0)


def Ry(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


def Rz(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def Rx(deg):
    a = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


UNIT = box(0.49, 0.49, 0.49)


def unit(sd):
    """Clip to the unit box (safety: every piece must fit 1 x 1 x 1)."""
    return sd & UNIT


# ================================================================================================ FIRE
def fire_back():
    s = round_box(0.14, 0.08, 0.46, 0.07, (0, -0.42, 0))
    spec = [(-0.36, 0.48, 0.1), (-0.2, 0.68, 0.12), (-0.02, 0.86, 0.13), (0.16, 0.78, 0.125), (0.32, 0.6, 0.11), (0.44, 0.4, 0.08)]
    for i, (z, h, r) in enumerate(spec):
        s = s.su(flame((0, -0.45, z), h, r, lean=(0.0, 0.38), sway=0.08, seed=i), 0.06)
        if i % 2 == 0:
            for sx in (1, -1):
                s = s.su(flame((0.1 * sx, -0.45, z + 0.06), h * 0.55, r * 0.7, lean=(0.22 * sx, 0.3), sway=0.05, seed=10 + i), 0.05)
    return unit(saddle(s))


def fire_head():
    s = cylinder(0.24, 0.05, axis=1, rr=0.04).at(0, -0.44, 0.0)
    for i, (x, z, h, r) in enumerate([(0, -0.05, 0.92, 0.13), (0.17, 0.02, 0.7, 0.1), (-0.17, 0.02, 0.7, 0.1), (0.1, 0.18, 0.58, 0.09),
                                      (-0.1, 0.18, 0.58, 0.09), (0.25, -0.12, 0.45, 0.08), (-0.25, -0.12, 0.45, 0.08)]):
        s = s.su(flame((x, -0.46, z), h, r, lean=(x * 0.6, 0.25), sway=0.06, seed=20 + i), 0.05)
    return unit(s)


def flame_dir(base, d, side, h, r, sway=0.06, seed=0, rise=0.0):
    """A flame tongue growing from `base` along direction d, flickering toward `side`, its tip lifting by `rise`."""
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, math.tau)
    b, d, side = (np.asarray(v, float) for v in (base, d, side))
    d /= np.linalg.norm(d)
    pts, rad = [], []
    for i in range(6):
        t = i / 5
        off = math.sin(ph + t * 3.2) * sway * t
        pts.append(tuple(b + d * t * h + side * off + np.array([0, rise * t * t * h, 0])))
        rad.append(r * (1 - t) ** 0.85 * (1 + 0.25 * math.sin(t * 3.1)) + 0.004)
    return tube(pts, rad, k=0.02)


def fire_tail():
    s = round_cone((0, 0, -0.48), (0, 0, -0.3), 0.13, 0.15)
    s = s.su(flame_dir((0, 0.0, -0.36), (0, 0.15, 1), (1, 0, 0), 0.8, 0.17, seed=30, rise=0.15), 0.05)
    for i in range(6):
        a = i / 6 * math.tau + 0.3
        d = np.array([0.75 * math.cos(a), 0.75 * math.sin(a) + 0.15, 1.0])
        s = s.su(flame_dir((0.06 * math.cos(a), 0.06 * math.sin(a), -0.34), d, (-math.sin(a), math.cos(a), 0), 0.48, 0.09, seed=31 + i, rise=0.2), 0.04)
    return unit(s)


def fire_shoulder():
    s = ellipsoid(0.26, 0.12, 0.3, (-0.18, -0.38, 0))
    for i, (x, z, h, r, lx) in enumerate([(-0.15, 0.0, 0.78, 0.14, 0.45), (0.05, -0.18, 0.6, 0.11, 0.6), (0.05, 0.18, 0.58, 0.11, 0.6),
                                          (-0.3, 0.15, 0.45, 0.09, 0.2), (0.2, 0.0, 0.4, 0.09, 0.8)]):
        s = s.su(flame((x, -0.44, z), h, r, lean=(lx, 0.15), sway=0.06, seed=40 + i), 0.05)
    return unit(s)


def fire_cuff():
    s = ring(0.27, 0.36, 0.09, y=-0.3, rr=0.04)
    for i in range(8):
        a = i / 8 * math.tau
        c = (0.32 * math.cos(a), -0.32, 0.32 * math.sin(a))
        s = s.su(flame(c, 0.55 + 0.12 * (i % 2), 0.075, lean=(0.25 * math.cos(a), 0.25 * math.sin(a)), sway=0.05, seed=50 + i), 0.04)
    return unit(s - cylinder(0.27, 1.0, axis=1))


# ================================================================================================ ICE
def ice_back():
    s = round_box(0.16, 0.07, 0.46, 0.06, (0, -0.42, 0))
    spec = [(-0.36, 0.45, 0.07, 0, 0), (-0.2, 0.7, 0.09, 8, 0), (-0.02, 0.9, 0.11, -6, 0), (0.17, 0.72, 0.09, 6, 0), (0.33, 0.5, 0.075, -8, 0),
            (-0.1, 0.42, 0.06, 0, 32), (-0.1, 0.42, 0.06, 0, -32), (0.1, 0.5, 0.06, 0, 30), (0.1, 0.5, 0.06, 0, -30), (0.28, 0.3, 0.05, 0, 35),
            (0.28, 0.3, 0.05, 0, -35), (-0.3, 0.3, 0.05, 0, -30)]
    for i, (z, L, r, tz, tx) in enumerate(spec):
        d = Rz(-tx) @ Rx(-tz - 18) @ np.array([0, 1.0, 0])     # lean back a little
        s = s | crystal((math.sin(math.radians(tx)) * 0.05, -0.47, z), d, L, r, tip=0.35, twist=i * 0.4)
    return unit(saddle(s))


def ice_head():
    s = cylinder(0.22, 0.04, axis=1, rr=0.03).at(0, -0.45, 0)
    for i, (x, z, L, r, tx, tz) in enumerate([(0, 0, 0.9, 0.1, 0, -6), (0.14, 0.04, 0.62, 0.075, 24, -4), (-0.14, 0.04, 0.62, 0.075, -24, -4),
                                              (0.24, -0.05, 0.42, 0.06, 45, 6), (-0.24, -0.05, 0.42, 0.06, -45, 6), (0.0, 0.18, 0.5, 0.065, 0, -35)]):
        d = Rz(-tx) @ Rx(tz) @ np.array([0, 1.0, 0])
        s = s | crystal((x, -0.47, z), d, L, r, twist=i)
    return unit(s)


def ice_tail():
    s = round_cone((0, 0, -0.48), (0, 0, -0.2), 0.15, 0.17)
    s = s | crystal((0, 0, -0.3), (0, 0, 1.0), 0.78, 0.13, tip=0.4)
    for i, (dx, dy) in enumerate([(1, 0.4), (-1, 0.4), (0.3, -1), (-0.3, 1.0), (0.9, -0.6), (-0.9, -0.6)]):
        d = np.array([dx * 0.7, dy * 0.7, 1.0])
        s = s | crystal((0, 0, -0.32 + 0.04 * i), d, 0.38, 0.06, twist=i)
    return unit(s)


def ice_shoulder():
    s = ellipsoid(0.26, 0.1, 0.3, (-0.2, -0.4, 0))
    for i, (x, z, L, r, a) in enumerate([(-0.18, 0.0, 0.8, 0.1, 22), (-0.05, -0.17, 0.6, 0.08, 40), (-0.05, 0.17, 0.62, 0.08, 38),
                                         (0.08, 0.0, 0.55, 0.075, 58), (-0.32, 0.12, 0.4, 0.06, 10), (-0.3, -0.14, 0.38, 0.06, 15)]):
        d = Rz(-a) @ np.array([0, 1.0, 0])
        s = s | crystal((x, -0.46, z), d, L, r, twist=i * 0.7)
    return unit(s)


def ice_cuff():
    s = ring(0.27, 0.35, 0.08, y=-0.15, rr=0.02)
    for i in range(9):
        a = i / 9 * math.tau
        d = np.array([math.cos(a) * 0.8, -0.55 if i % 2 else 0.5, math.sin(a) * 0.8])
        s = s | crystal((0.3 * math.cos(a), -0.15, 0.3 * math.sin(a)), d, 0.3 if i % 2 else 0.36, 0.055, twist=i)
    return unit(s - cylinder(0.27, 1.0, axis=1))


# ================================================================================================ LIGHTNING
BOLT = [(0.12, -0.5), (-0.2, 0.02), (0.01, 0.02), (-0.13, 0.5), (0.24, -0.1), (0.04, -0.1), (0.26, -0.5)]


def bolt(base, h, w=1.0, th=0.035, flip=1, R=None):
    P = [(x * w * flip, (y + 0.5) * h) for x, y in BOLT]
    if flip < 0:
        P = P[::-1]
    sd = extrude(P, th, r=th * 0.6, plane="zy")
    if R is not None:
        sd = place(sd, R, (0, 0, 0))
    return sd.at(*base)


def lightning_back():
    s = round_box(0.13, 0.07, 0.46, 0.06, (0, -0.42, 0))
    for i, (z, h, w) in enumerate([(-0.33, 0.55, 0.8), (-0.12, 0.85, 1.0), (0.12, 0.7, 0.9), (0.33, 0.5, 0.7)]):
        s = s.su(bolt((0, -0.48, z), h, w=w, th=0.04, flip=1 if i % 2 == 0 else -1), 0.02)
    for sx in (1, -1):
        s = s.su(bolt((0.08 * sx, -0.48, 0.0), 0.45, w=0.6, th=0.03, R=Rz(-28 * sx)), 0.02)
    return unit(saddle(s))


def lightning_head():
    s = cylinder(0.2, 0.04, axis=1, rr=0.03).at(0, -0.45, 0)
    s = s.su(bolt((0, -0.47, 0.0), 0.92, w=0.9, th=0.04), 0.02)
    for sx in (1, -1):
        s = s.su(bolt((0.12 * sx, -0.47, 0.02), 0.6, w=0.7, th=0.035, R=Rz(-35 * sx), flip=sx), 0.02)
    return unit(s)


def lightning_tail():
    s = round_cone((0, 0, -0.48), (0, 0, -0.25), 0.14, 0.16)
    b = extrude([(x * 0.9, (y + 0.5) * 0.8) for x, y in BOLT], 0.045, r=0.025, plane="xy")   # outline in x/y: points +Y
    s = s.su(place(b, Rx(90), (0, 0, -0.32)), 0.03)
    b2 = place(extrude([(x * 0.7, (y + 0.5) * 0.55) for x, y in BOLT], 0.035, r=0.02, plane="zy"), Rx(90), (0, 0, -0.3))
    s = s.su(b2, 0.03)
    return unit(s)


def lightning_shoulder():
    s = ellipsoid(0.25, 0.1, 0.28, (-0.2, -0.4, 0))
    for i, (z, a, h) in enumerate([(0.0, 25, 0.85), (-0.17, 45, 0.6), (0.17, 45, 0.6)]):
        s = s.su(bolt((-0.12, -0.46, z), h, w=0.75, th=0.035, R=Rz(-a), flip=1 if i != 1 else -1), 0.02)
    return unit(s)


def lightning_cuff():
    s = ring(0.27, 0.35, 0.07, y=-0.2, rr=0.02)
    # zig-zag band
    pts = []
    for i in range(17):
        a = i / 16 * math.tau
        pts.append((0.355 * math.cos(a), -0.2 + (0.12 if i % 2 else -0.12), 0.355 * math.sin(a)))
    s = s.su(tube(pts, [0.035] * len(pts)), 0.02)
    for i in range(4):
        a = i / 4 * math.tau + 0.4
        Rm = Ry(-math.degrees(a)) @ Rz(-60)
        s = s.su(bolt((0.33 * math.cos(a), -0.15, 0.33 * math.sin(a)), 0.4, w=0.5, th=0.03, R=Rm), 0.02)
    return unit(s - cylinder(0.27, 1.0, axis=1))


# ================================================================================================ EARTH / STONE
def rock_spike(base, d, L, r, seed):
    """A stout, irregular five-sided stone spike (less regular and blunter than an ice crystal)."""
    sp = crystal(base, d, L, r, tip=0.5, sides=5, twist=seed * 0.7)
    return sp.round(0.012) | facet(tuple(np.asarray(base, float) + np.asarray(d, float) / np.linalg.norm(d) * L * 0.25), r * 1.05, n=9, seed=seed, jitter=0.12)


def pebble(c, r, seed, sq=(1.0, 0.8, 1.0)):
    return facet(c, r, n=11, seed=seed, squash=sq, jitter=0.1).round(0.01)


def earth_back():
    s = round_box(0.18, 0.08, 0.46, 0.06, (0, -0.42, 0))
    for i, (z, L, r) in enumerate([(-0.34, 0.42, 0.1), (-0.15, 0.68, 0.13), (0.06, 0.82, 0.14), (0.26, 0.6, 0.12), (0.4, 0.38, 0.09)]):
        d = Rx(-14) @ np.array([0, 1.0, 0])
        s = s | rock_spike((0, -0.45, z), d, L, r, seed=i + 1)
    for i, (x, z, r) in enumerate([(0.18, -0.26, 0.09), (-0.17, -0.18, 0.1), (0.18, 0.12, 0.1), (-0.18, 0.24, 0.09), (0.1, 0.38, 0.07), (-0.1, -0.4, 0.07)]):
        s = s | pebble((x, -0.36, z), r, seed=20 + i)
    return unit(saddle(s))


def earth_head():
    s = pebble((0, -0.38, 0), 0.2, seed=3, sq=(1.3, 0.55, 1.2))
    for i, (x, z, a, L, r) in enumerate([(0.0, -0.02, 0, 0.82, 0.12), (0.18, 0.02, 28, 0.6, 0.1), (-0.18, 0.02, -28, 0.6, 0.1),
                                         (0.28, -0.08, 50, 0.38, 0.07), (-0.28, -0.08, -50, 0.38, 0.07)]):
        d = Rz(-a) @ Rx(-10) @ np.array([0, 1.0, 0])
        s = s | rock_spike((x, -0.45, z), d, L, r, seed=30 + i)
    return unit(s)


def earth_tail():
    s = round_cone((0, 0, -0.48), (0, 0, -0.2), 0.14, 0.16)
    s = s | pebble((0, 0, -0.08), 0.17, seed=7, sq=(1.0, 0.95, 1.25))
    for i in range(5):
        a = i / 5 * math.tau
        s = s | rock_spike((0.08 * math.cos(a), 0.08 * math.sin(a), -0.08), (0.9 * math.cos(a), 0.9 * math.sin(a), 0.6), 0.42, 0.065, seed=40 + i)
    s = s | rock_spike((0, 0, 0.0), (0, 0.1, 1.0), 0.48, 0.09, seed=46)
    return unit(s)


def earth_shoulder():
    s = pebble((-0.12, -0.32, 0.0), 0.22, seed=11, sq=(1.3, 0.65, 1.3))
    for i, (x, z, a, L, r) in enumerate([(-0.12, 0.0, 25, 0.8, 0.13), (0.05, -0.17, 45, 0.55, 0.1), (0.05, 0.17, 45, 0.52, 0.1), (-0.3, 0.1, 5, 0.4, 0.08)]):
        d = Rz(-a) @ np.array([0, 1.0, 0])
        s = s | rock_spike((x, -0.42, z), d, L, r, seed=12 + i)
    return unit(s)


def earth_cuff():
    s = ring(0.27, 0.36, 0.1, y=-0.28, rr=0.03).noise(0.008, 12, 2)
    for i in range(7):
        a = i / 7 * math.tau
        s = s | pebble((0.36 * math.cos(a), -0.24 + 0.06 * (i % 2), 0.36 * math.sin(a)), 0.1, seed=60 + i, sq=(1, 1.2, 1))
        if i % 2 == 0:
            s = s | rock_spike((0.34 * math.cos(a), -0.2, 0.34 * math.sin(a)), (math.cos(a) * 0.5, 1.0, math.sin(a) * 0.5), 0.36, 0.06, seed=70 + i)
    return unit(s - cylinder(0.27, 1.0, axis=1))


# ================================================================================================ NATURE
def moss(sd, seed=0):
    return sd.noise(0.018, 22, seed)


def nature_back():
    m = moss(ellipsoid(0.3, 0.12, 0.48, (0, -0.4, 0)), 1)
    s = m
    rng = np.random.default_rng(3)
    for i in range(11):
        z = -0.4 + i * 0.08
        sx = 1 if i % 2 else -1
        s = s | leaf((0.04 * sx, -0.36, z), (0.55 * sx, 0.6, 0.45), 0.42 - 0.12 * abs(z), 0.1, bend=0.2)
    for i, z in enumerate((-0.25, 0.0, 0.25)):
        s = s | leaf((0, -0.36, z), (0, 1.0, 0.25), 0.5, 0.11, bend=-0.15, up=(1, 0, 0))
    # sprouting twigs with buds
    s = s.su(curve([(0.05, -0.35, -0.1), (0.12, -0.05, -0.05), (0.08, 0.2, 0.05)], [0.03, 0.02, 0.012]), 0.02)
    s = s | sphere(0.05, (0.08, 0.22, 0.05))
    return unit(saddle(s))


def nature_head():
    s = moss(cylinder(0.24, 0.05, axis=1, rr=0.04).at(0, -0.44, 0), 2)
    for sx in (1, -1):        # antler-like branches
        br = curve([(0.1 * sx, -0.42, 0), (0.22 * sx, -0.1, 0.02), (0.3 * sx, 0.2, 0.05), (0.26 * sx, 0.42, 0.08)], [0.05, 0.04, 0.03, 0.015])
        br = br.su(curve([(0.24 * sx, -0.02, 0.02), (0.4 * sx, 0.1, -0.02), (0.44 * sx, 0.25, -0.02)], [0.03, 0.022, 0.012]), 0.02)
        s = s.su(br, 0.03)
        s = s | leaf((0.3 * sx, 0.18, 0.04), (0.6 * sx, 0.4, -0.3), 0.2, 0.06, bend=0.1)
        s = s | leaf((0.26 * sx, 0.4, 0.07), (0.1 * sx, 1.0, -0.2), 0.18, 0.05, bend=0.1)
    for i in range(5):
        a = (i / 5 - 0.4) * 2.4
        s = s | leaf((0.2 * math.sin(a), -0.4, -0.2 * math.cos(a)), (math.sin(a), 0.5, -math.cos(a)), 0.25, 0.08, bend=0.15)
    return unit(s)


def nature_tail():
    s = moss(round_cone((0, 0, -0.48), (0, 0, 0.0), 0.14, 0.18), 3)
    for i in range(8):
        a = i / 8 * math.tau
        s = s | leaf((0.1 * math.cos(a), 0.1 * math.sin(a), -0.05), (0.7 * math.cos(a), 0.7 * math.sin(a), 1.0), 0.42, 0.1, bend=0.15,
                     up=(-math.sin(a), math.cos(a), 0))
    s = s | sphere(0.09, (0, 0, 0.08))
    return unit(s)


def nature_shoulder():
    s = moss(ellipsoid(0.28, 0.12, 0.3, (-0.15, -0.38, 0)), 4)
    for i in range(6):
        z = -0.25 + i * 0.1
        s = s | leaf((-0.1, -0.33, z), (0.7, 0.55 - 0.1 * (i % 2), 0.2 * (z / 0.25)), 0.5 - 0.06 * abs(i - 2.5), 0.11, bend=0.2)
    s = s | leaf((-0.2, -0.33, 0.0), (0.1, 1.0, 0.0), 0.55, 0.12, bend=-0.15, up=(0, 0, 1))
    return unit(s)


def nature_cuff():
    s = moss(ring(0.27, 0.35, 0.09, y=-0.25, rr=0.04), 5)
    s = s.su(helix(0.36, 0.06, 1.2, 0.025, 0.02, y0=-0.32), 0.02)       # twining vine
    for i in range(7):
        a = i / 7 * math.tau
        s = s | leaf((0.34 * math.cos(a), -0.2, 0.34 * math.sin(a)), (math.cos(a), 0.5, math.sin(a)), 0.22, 0.07, bend=0.1)
    return unit(s - cylinder(0.27, 1.0, axis=1))


# ================================================================================================ WATER
def wave_outline(L=0.95, H=0.85, curl=0.25, n=28):
    """Side outline (z, y) of a cresting wave fin: rises from the front, crests and curls forward over the back."""
    top = []
    for i in range(1, n):
        t = i / n
        z = -L / 2 + t * L
        y = H * (math.sin(math.pi * t ** 0.8) ** 1.3) * (0.75 + 0.25 * t)
        top.append((z, y))
    # curl: a hook at the crest
    cz, cy = top[int(n * 0.62)]
    hook = [(cz + curl * 0.6 * math.cos(a), cy + curl * 0.5 * math.sin(a)) for a in np.linspace(0.3, 2.8, 8)]
    pts = [(-L / 2, 0.0)] + top[: int(n * 0.62)] + hook[::-1][:0] + top[int(n * 0.62):] + [(L / 2, 0.0)]
    return pts


def water_fin(L, H, th, curl=0.25):
    P = wave_outline(L, H, curl)
    sd = extrude(P, th, r=th * 0.8, plane="zy")
    # a curling lip at the crest
    lip = tube([(0, H * 0.95, 0.02), (0, H * 1.05, -0.08), (0, H * 0.98, -0.18), (0, H * 0.84, -0.2)], [th * 1.2, th * 1.1, th, th * 0.8])
    sd = sd.su(lip, 0.03)
    # ripple grooves
    sd = sd.ss(SDF(lambda p: np.abs(np.mod(p[:, 1] * 9 - p[:, 2] * 3, 1.0) - 0.5) / 9 - 0.006) & half_space(1, 1, 0.08), 0.008)
    return sd


def water_back():
    s = round_box(0.15, 0.07, 0.46, 0.06, (0, -0.42, 0))
    s = s.su(water_fin(0.92, 0.82, 0.045).at(0, -0.45, 0.0), 0.05)
    for sx in (1, -1):
        s = s.su(place(water_fin(0.6, 0.35, 0.03), Rz(-35 * sx), (0.07 * sx, -0.45, 0.12)), 0.04)
    for i, (x, y, z, r) in enumerate([(0.12, 0.35, -0.3, 0.05), (-0.14, 0.25, -0.38, 0.04), (0.18, 0.1, 0.4, 0.04)]):
        s = s | sphere(r, (x, y, z)).su(round_cone((x, y, z), (x, y + r * 2.0, z + 0.02), r * 0.9, 0.003), 0.02)
    return unit(saddle(s))


def water_head():
    s = cylinder(0.2, 0.04, axis=1, rr=0.03).at(0, -0.45, 0)
    s = s.su(water_fin(0.62, 0.85, 0.04).at(0, -0.47, 0.05), 0.04)
    for sx in (1, -1):
        s = s.su(place(water_fin(0.4, 0.5, 0.03), Rz(-40 * sx), (0.1 * sx, -0.47, 0.08)), 0.03)
    s = s | sphere(0.06, (0.0, 0.42, -0.3))
    return unit(s)


def water_tail():
    s = round_cone((0, 0, -0.48), (0, 0, -0.18), 0.13, 0.15)
    for sy in (1, -1):    # fluke
        P = [(-0.25, 0.0), (0.05, 0.12), (0.4, 0.42), (0.47, 0.36), (0.3, 0.12), (0.45, 0.0)]
        fl = extrude([(z, y * sy) for z, y in P], 0.035, r=0.025, plane="zy")
        s = s.su(fl, 0.05)
    s = s.su(place(water_fin(0.5, 0.25, 0.03), np.eye(3), (0, 0.06, -0.15)), 0.03)
    return unit(s)


def water_shoulder():
    s = ellipsoid(0.25, 0.1, 0.28, (-0.2, -0.4, 0))
    for i, (a, L, H, z) in enumerate([(25, 0.7, 0.75, 0.0), (55, 0.5, 0.45, -0.1), (5, 0.45, 0.5, 0.15)]):
        s = s.su(place(water_fin(L, H, 0.035), Rz(-a), (-0.18, -0.44, z)), 0.04)
    s = s | sphere(0.05, (0.3, 0.3, -0.2))
    return unit(s)


def water_cuff():
    s = ring(0.27, 0.34, 0.07, y=-0.3, rr=0.03)
    for i in range(6):
        a = i / 6 * math.tau
        fin = place(water_fin(0.3, 0.32, 0.025), Ry(-math.degrees(a) - 90), (0.33 * math.cos(a), -0.32, 0.33 * math.sin(a)))
        s = s.su(fin, 0.03)
    for i in range(3):
        a = i / 3 * math.tau + 0.5
        s = s | sphere(0.045, (0.42 * math.cos(a), 0.15, 0.42 * math.sin(a)))
    return unit(s - cylinder(0.27, 1.0, axis=1))


# ================================================================================================ WIND
def gust(R, turns, r0, r1, y0, pitch, ph=0.0, flat=0.6):
    """A flattened swirl ribbon: a helix tube squashed into a blade."""
    h = helix(R, pitch, turns, r0, r1, y0=y0, ph=ph)
    return h


def wind_back():
    s = round_box(0.13, 0.06, 0.46, 0.05, (0, -0.43, 0))
    # a swirl rising off the spine and two swept feathers either side
    sw = helix(0.18, 0.12, 2.2, 0.05, 0.012, y0=-0.4, ph=0.0)
    s = s.su(place(sw, np.eye(3), (0, 0, -0.12)), 0.04)
    for sx in (1, -1):
        for i, (z, L) in enumerate([(-0.3, 0.55), (-0.08, 0.6), (0.15, 0.55), (0.35, 0.42)]):
            s = s | leaf((0.04 * sx, -0.4, z), (0.45 * sx, 0.55, 0.7), L, 0.075, th=0.014, bend=0.35, up=(0, 1, 0))
    for i, z in enumerate((-0.35, 0.05, 0.38)):
        crescent = extrude([(math.cos(a) * 0.22, math.sin(a) * 0.3 + 0.0) for a in np.linspace(-0.3, 2.6, 14)] +
                           [(math.cos(a) * 0.15, math.sin(a) * 0.2 + 0.03) for a in np.linspace(2.6, -0.3, 14)], 0.02, r=0.012, plane="zy")
        s = s | crescent.at(0, -0.25, z * 0.6)
    return unit(saddle(s))


def wind_head():
    s = cylinder(0.18, 0.04, axis=1, rr=0.03).at(0, -0.45, 0)
    s = s.su(helix(0.14, 0.1, 2.5, 0.045, 0.01, y0=-0.42), 0.03)
    for i, a in enumerate((-50, -20, 20, 50)):
        d = Rz(-a) @ np.array([0, 1.0, 0.45])
        s = s | leaf((0.04 * math.sin(math.radians(a)), -0.42, 0.05), d, 0.7 - 0.12 * abs(a) / 50, 0.07, th=0.014, bend=0.3)
    return unit(s)


def wind_tail():
    s = round_cone((0, 0, -0.48), (0, 0, -0.25), 0.12, 0.14)
    sw = place(helix(0.2, 0.09, 2.5, 0.05, 0.012, y0=-0.3), Rx(90), (0, 0, -0.05))
    s = s.su(sw, 0.03)
    for i in range(5):
        a = i / 5 * math.tau
        s = s | leaf((0.06 * math.cos(a), 0.06 * math.sin(a), -0.25), (0.45 * math.cos(a), 0.45 * math.sin(a), 1.0), 0.65, 0.07, th=0.014, bend=0.25,
                     up=(-math.sin(a), math.cos(a), 0))
    return unit(s)


def wind_shoulder():
    s = ellipsoid(0.24, 0.09, 0.27, (-0.2, -0.41, 0))
    for i, (z, a, L) in enumerate([(-0.15, 30, 0.8), (0.0, 45, 0.85), (0.15, 60, 0.75), (0.0, 15, 0.6)]):
        d = Rz(-a) @ np.array([0, 1.0, 0.35])
        s = s | leaf((-0.25, -0.4, z), d, L, 0.075, th=0.014, bend=0.3)
    s = s.su(place(helix(0.12, 0.08, 1.8, 0.035, 0.01), Rz(-30), (-0.05, -0.15, 0.2)), 0.02)
    return unit(s)


def wind_cuff():
    s = ring(0.27, 0.33, 0.05, y=-0.3, rr=0.02)
    s = s.su(helix(0.36, 0.11, 2.0, 0.03, 0.03, y0=-0.33), 0.02)
    for i in range(5):
        a = i / 5 * math.tau
        s = s | leaf((0.34 * math.cos(a), -0.2, 0.34 * math.sin(a)), (math.cos(a - 1.2), 0.35, math.sin(a - 1.2)), 0.3, 0.05, th=0.012, bend=0.25)
    return unit(s - cylinder(0.27, 1.0, axis=1))


# ================================================================================================ SHADOW
def wisp(base, h, r, lean=(0.0, 0.4), seed=0, hook=0.6):
    """A tattered shadow wisp: a flame-like tongue that hooks backward, with a torn notch."""
    rng = np.random.default_rng(seed)
    b = np.asarray(base, float)
    pts, rad = [], []
    for i in range(7):
        t = i / 6
        pts.append(tuple(b + np.array([lean[0] * t * h + 0.05 * math.sin(t * 5 + seed), t * h * (1 - 0.3 * t * hook), lean[1] * t * t * h * (1 + hook)])))
        rad.append(r * (1 - t) ** 0.7 + 0.004)
    w = tube(pts, rad, k=0.02)
    tip = np.array(pts[3])
    w = w.ss(sphere(r * 0.55, tuple(tip + np.array([r * 0.9, 0.0, -r * 0.2]))), 0.02)
    return w


def shadow_back():
    s = round_box(0.15, 0.07, 0.46, 0.06, (0, -0.42, 0)).noise(0.01, 14, 1)
    for i, (z, h, r) in enumerate([(-0.38, 0.55, 0.09), (-0.2, 0.78, 0.11), (0.0, 0.88, 0.12), (0.2, 0.7, 0.1), (0.36, 0.48, 0.08)]):
        s = s.su(wisp((0, -0.45, z), h, r, lean=(0.0, 0.32), seed=i), 0.05)
    for sx in (1, -1):
        for i, z in enumerate((-0.28, 0.0, 0.28)):
            s = s.su(wisp((0.12 * sx, -0.45, z), 0.42, 0.07, lean=(0.45 * sx, 0.3), seed=10 + i + (5 if sx < 0 else 0)), 0.04)
    for i, z in enumerate((-0.12, 0.12)):   # thorns
        s = s | round_cone((0.0, -0.36, z), (0.0, -0.05, z + 0.12), 0.05, 0.004)
    return unit(saddle(s))


def shadow_head():
    s = cylinder(0.22, 0.05, axis=1, rr=0.04).at(0, -0.44, 0).noise(0.01, 14, 2)
    for sx in (1, -1):     # swept-back horn wisps
        s = s.su(tube([(0.12 * sx, -0.42, 0.0), (0.24 * sx, -0.05, 0.08), (0.3 * sx, 0.22, 0.22), (0.24 * sx, 0.45, 0.4)], [0.08, 0.06, 0.035, 0.006], k=0.02), 0.04)
    for i, (x, h) in enumerate([(0.0, 0.8), (0.1, 0.55), (-0.1, 0.55)]):
        s = s.su(wisp((x, -0.45, -0.1), h, 0.08, lean=(x, 0.35), seed=20 + i), 0.04)
    return unit(s)


def shadow_tail():
    s = round_cone((0, 0, -0.48), (0, 0, -0.2), 0.13, 0.15).noise(0.01, 14, 3)
    for i in range(6):
        a = i / 6 * math.tau
        w = wisp((0, 0, 0), 0.62, 0.08, lean=(0.25, 0.0), seed=30 + i, hook=0.3)
        Rm = Rz(math.degrees(a)) @ Rx(90)
        s = s.su(place(w, Rm, (0, 0, -0.3)), 0.04)
    return unit(s)


def shadow_shoulder():
    s = ellipsoid(0.26, 0.11, 0.3, (-0.18, -0.38, 0)).noise(0.01, 14, 4)
    for i, (z, h, lx) in enumerate([(0.0, 0.85, 0.45), (-0.17, 0.6, 0.65), (0.17, 0.6, 0.65), (0.05, 0.45, 0.9)]):
        s = s.su(wisp((-0.15, -0.44, z), h, 0.1, lean=(lx, 0.2), seed=40 + i), 0.04)
    return unit(s)


def shadow_cuff():
    s = ring(0.27, 0.35, 0.08, y=-0.3, rr=0.03).noise(0.01, 14, 5)
    for i in range(7):
        a = i / 7 * math.tau
        s = s.su(wisp((0.32 * math.cos(a), -0.33, 0.32 * math.sin(a)), 0.5 + 0.1 * (i % 2), 0.065, lean=(0.3 * math.cos(a + 0.8), 0.3 * math.sin(a + 0.8)), seed=50 + i), 0.03)
    return unit(s - cylinder(0.27, 1.0, axis=1))


# ================================================================================================ LIGHT
def ray_disc(R, n, th, ray=0.12):
    """A sunburst disc in the x/y plane (faces Z): a ring with alternating long / short pointed rays."""
    pts = []
    for i in range(n * 2):
        a = i / (n * 2) * math.tau
        rr = R + (ray if i % 2 == 0 else ray * 0.25)
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return extrude(pts, th, r=th * 0.8, plane="xy")


def light_back():
    s = round_box(0.14, 0.06, 0.46, 0.05, (0, -0.43, 0))
    for sx in (1, -1):         # small folded wings of feathers
        for i in range(6):
            t = i / 5
            d = np.array([0.3 * sx, 0.9 - 0.35 * t, 0.35 + 0.7 * t])
            s = s | leaf((0.05 * sx, -0.4, -0.3 + 0.08 * i), d, 0.62 - 0.22 * t, 0.075, th=0.016, bend=0.15)
    halo = (torus(0.17, 0.028, axis=2)).at(0, 0.1, -0.32)
    s = s.su(halo, 0.01).su(cylinder(0.025, 0.2, axis=1).at(0, -0.2, -0.32), 0.02)
    return unit(saddle(s))


def light_head():
    s = cylinder(0.12, 0.04, axis=1, rr=0.03).at(0, -0.45, 0.1)
    s = s.su(round_cone((0, -0.45, 0.1), (0, -0.05, 0.12), 0.05, 0.03), 0.03)
    s = s | ray_disc(0.27, 12, 0.03, ray=0.13).at(0, 0.03, 0.12)
    s = s - cylinder(0.17, 0.2, axis=2).at(0, 0.03, 0.12)
    return unit(s)


def light_tail():
    s = round_cone((0, 0, -0.48), (0, 0, -0.2), 0.12, 0.14)
    for i in range(7):
        a = i / 7 * math.tau
        s = s | leaf((0.05 * math.cos(a), 0.05 * math.sin(a), -0.25), (0.35 * math.cos(a), 0.35 * math.sin(a), 1.0), 0.7, 0.08, th=0.015, bend=0.12,
                     up=(-math.sin(a), math.cos(a), 0))
    s = s | sphere(0.09, (0, 0, -0.18))
    return unit(s)


def light_shoulder():
    s = ellipsoid(0.24, 0.09, 0.27, (-0.2, -0.41, 0))
    for i in range(5):
        t = i / 4
        d = np.array([0.6 + 0.3 * t, 1.0 - 0.6 * t, 0.15])
        s = s | leaf((-0.25, -0.4, -0.15 + 0.08 * i), d, 0.75 - 0.2 * t, 0.075, th=0.015, bend=0.15)
    s = s | ray_disc(0.07, 6, 0.02, ray=0.05).at(-0.25, -0.12, -0.22)
    return unit(s)


def light_cuff():
    s = ring(0.27, 0.35, 0.08, y=-0.2, rr=0.03)
    s = s.su(ring(0.27, 0.38, 0.025, y=-0.08, rr=0.012), 0.01).su(ring(0.27, 0.38, 0.025, y=-0.32, rr=0.012), 0.01)
    for i in range(6):
        a = i / 6 * math.tau
        s = s | leaf((0.34 * math.cos(a), -0.15, 0.34 * math.sin(a)), (math.cos(a) * 0.5, 1.0, math.sin(a) * 0.5), 0.36, 0.06, th=0.013, bend=0.1)
    return unit(s - cylinder(0.27, 1.0, axis=1))


# ================================================================================================ ARCANE
def runes(seed, n=5, w=0.012, scale=0.1):
    """Random angular rune strokes (thin capsules) on a plane z=0, for carving."""
    rng = np.random.default_rng(seed)
    out = None
    for i in range(n):
        a = rng.uniform(-1, 1, 2) * scale
        b = a + rng.choice([-1, 1]) * np.array(rng.choice([(1, 0), (0, 1), (0.7, 0.7), (0.7, -0.7)])) * scale * rng.uniform(0.7, 1.2)
        c = capsule((a[0], a[1], 0), (b[0], b[1], 0), w)
        out = c if out is None else out | c
    return out


def runestone(c, h, w, d, seed, face=(0, 0, -1)):
    st = facet((0, 0, 0), 1.0, n=8, seed=seed, squash=(w, h, d), jitter=0.06)
    st = st.ss(place(runes(seed, n=5, scale=min(w, h) * 0.45), np.eye(3), (0, 0, -d * 0.95)), 0.006)
    return st.at(*c)


def arcane_back():
    s = round_box(0.15, 0.07, 0.46, 0.06, (0, -0.42, 0))
    for i, (z, h, rx) in enumerate([(-0.3, 0.26, -12), (0.0, 0.34, 0), (0.3, 0.24, 12)]):
        s = s | place(runestone((0, 0, 0), h, 0.1, 0.06, seed=i + 1), Rx(rx), (0, -0.4 + h, z))
    for z, h, rx in ((-0.3, 0.26, -12), (0.0, 0.34, 0), (0.3, 0.24, 12)):
        d = Rx(rx) @ np.array([0, 1.0, 0])
        top = np.array([0, -0.4 + h, z]) + d * (h - 0.04)
        s = s | crystal(tuple(top), tuple(d), 0.2 if z else 0.26, 0.04, tip=0.45, sides=4)
    return unit(saddle(s))


def arcane_head():
    s = ring(0.18, 0.26, 0.05, y=-0.42, rr=0.02)
    s = s.ss(place(runes(7, n=8, scale=0.08), np.eye(3), (0, -0.42, -0.26)), 0.004)
    for i in range(5):
        a = (i / 5) * math.tau
        L = 0.75 if i == 0 else 0.45
        d = np.array([0.25 * math.sin(a), 1.0, -0.25 * math.cos(a)])
        s = s | crystal((0.22 * math.sin(a), -0.42, -0.22 * math.cos(a)), d, L, 0.05, tip=0.35, sides=4)
    s = s | sphere(0.09, (0, 0.2, -0.05))
    return unit(s)


def arcane_tail():
    s = round_cone((0, 0, -0.48), (0, 0, -0.25), 0.12, 0.13)
    s = s.su(ring(0.12, 0.2, 0.06).rot(90, 0, 0).at(0, 0, -0.25), 0.02)
    s = s | sphere(0.2, (0, 0, 0.12))
    s = s | torus(0.3, 0.025, axis=2).rot(0, 30, 20).at(0, 0, 0.12)
    s = s | torus(0.3, 0.022, axis=0).rot(25, 0, 0).at(0, 0, 0.12)
    return unit(s)


def arcane_shoulder():
    s = facet((-0.12, -0.38, 0), 0.2, n=10, seed=5, squash=(1.2, 0.5, 1.2), jitter=0.08)
    s = s.ss(place(runes(9, n=6, scale=0.09), Rx(-90), (-0.1, -0.29, 0.0)), 0.004)
    for i, (x, z, a, L) in enumerate([(-0.05, 0.0, 28, 0.82), (-0.2, 0.15, 10, 0.55), (-0.2, -0.15, 15, 0.52), (0.1, -0.08, 55, 0.45), (0.08, 0.12, 48, 0.4)]):
        d = Rz(-a) @ np.array([0, 1.0, 0])
        s = s | crystal((x, -0.4, z), d, L, 0.055, tip=0.35, sides=4)
    return unit(s)


def arcane_cuff():
    s = ring(0.27, 0.36, 0.1, y=-0.25, rr=0.02)
    for i in range(8):
        a = i / 8 * math.tau
        rn = place(runes(30 + i, n=3, scale=0.04, w=0.01), Ry(-math.degrees(a) - 90), (0.36 * math.cos(a), -0.25, 0.36 * math.sin(a)))
        s = s.ss(rn, 0.004)
    for i in range(4):
        a = i / 4 * math.tau + 0.4
        s = s | crystal((0.33 * math.cos(a), -0.15, 0.33 * math.sin(a)), (math.cos(a) * 0.4, 1.0, math.sin(a) * 0.4), 0.4, 0.045, sides=4)
    return unit(s - cylinder(0.27, 1.0, axis=1))


# ================================================================================================ POISON
def pustule(c, r, spikes=3, seed=0):
    rng = np.random.default_rng(seed)
    p = sphere(r, c).su(sphere(r * 0.7, tuple(np.asarray(c) + np.array([r * 0.5, -r * 0.4, 0.0]))), r * 0.3)
    for i in range(spikes):
        d = rng.normal(size=3)
        d[1] = abs(d[1]) + 0.6
        d /= np.linalg.norm(d)
        a = np.asarray(c) + d * r * 0.8
        p = p.su(round_cone(tuple(a), tuple(a + d * r * 0.9), r * 0.18, 0.004), r * 0.1)
    return p


def drip(c, L, r):
    c = np.asarray(c, float)
    return round_cone(tuple(c), tuple(c + np.array([0, -L, 0])), r * 0.5, r).su(sphere(r * 1.05, tuple(c + np.array([0, -L, 0]))), 0.01)


def poison_back():
    s = ellipsoid(0.25, 0.12, 0.48, (0, -0.4, 0)).noise(0.015, 10, 1)
    for i, (x, z, r) in enumerate([(0, -0.3, 0.12), (0.0, 0.0, 0.16), (0.0, 0.28, 0.12), (0.15, -0.15, 0.09), (-0.15, 0.12, 0.09), (0.15, 0.2, 0.08),
                                   (-0.16, -0.22, 0.08)]):
        s = s.su(pustule((x, -0.3 + r * 0.9, z), r, spikes=3, seed=i), 0.05)
    for i, z in enumerate((-0.4, -0.15, 0.4)):   # spines
        s = s | round_cone((0, -0.33, z), (0, 0.05 + 0.1 * (i % 2), z + 0.15), 0.04, 0.004)
    return unit(saddle(s))


def poison_head():
    s = cylinder(0.24, 0.05, axis=1, rr=0.04).at(0, -0.44, 0).noise(0.012, 10, 2)
    for i, (x, z, r) in enumerate([(0, 0, 0.16), (0.2, 0.05, 0.1), (-0.2, 0.05, 0.1), (0.08, 0.2, 0.08), (-0.08, -0.2, 0.08)]):
        s = s.su(pustule((x, -0.35 + r, z), r, spikes=2 + (i == 0) * 2, seed=10 + i), 0.04)
    s = s.su(round_cone((0, -0.1, 0.0), (0, 0.4, 0.08), 0.06, 0.004), 0.03)
    return unit(s)


def poison_tail():
    s = round_cone((0, 0, -0.48), (0, 0, -0.1), 0.13, 0.16)
    s = s.su(sphere(0.22, (0, 0, 0.06)), 0.08)
    s = s.su(round_cone((0, 0, 0.18), (0, 0.1, 0.48), 0.12, 0.006), 0.05)      # stinger
    for i, (x, y, z) in enumerate([(0.18, 0.1, -0.05), (-0.17, 0.12, 0.0), (0.0, 0.22, -0.15)]):
        s = s.su(pustule((x, y, z), 0.07, spikes=1, seed=20 + i), 0.03)
    s = s.su(drip((0, -0.18, 0.1), 0.2, 0.05), 0.04)
    return unit(s)


def poison_shoulder():
    s = ellipsoid(0.26, 0.12, 0.3, (-0.18, -0.38, 0)).noise(0.012, 10, 4)
    for i, (x, z, r) in enumerate([(-0.15, 0.0, 0.15), (0.05, -0.12, 0.11), (0.05, 0.14, 0.1), (0.2, 0.0, 0.08)]):
        s = s.su(pustule((x, -0.3 + r, z), r, spikes=3, seed=30 + i), 0.04)
    s = s.su(drip((0.25, -0.35, 0.1), 0.12, 0.04), 0.03)
    return unit(s)


def poison_cuff():
    s = ring(0.27, 0.36, 0.09, y=-0.2, rr=0.04).noise(0.012, 10, 5)
    for i in range(7):
        a = i / 7 * math.tau
        c = (0.36 * math.cos(a), -0.1, 0.36 * math.sin(a))
        s = s.su(pustule(c, 0.07, spikes=1, seed=40 + i), 0.03)
        if i % 2 == 0:
            s = s.su(drip((0.38 * math.cos(a + 0.4), -0.25, 0.38 * math.sin(a + 0.4)), 0.15, 0.035), 0.03)
    return unit(s - cylinder(0.27, 1.0, axis=1))


# ================================================================================================ METAL
def plate(c, w, h, d, th=0.035, curve_r=0.6, rivets=True, ridge=True):
    """A curved armour plate (a slice of a cylinder shell along Z), bevelled, with rivets."""
    shell = (cylinder(curve_r, d, axis=2) - cylinder(curve_r - th, d + 0.1, axis=2)).at(0, -curve_r + h, 0)
    sl = shell & box(w, h, d)
    sl = sl.round(0.008)
    if ridge:
        sl = sl.su(box(0.012, 0.012, d * 0.9).at(0, h + 0.002, 0), 0.01)
    if rivets:
        for sx in (1, -1):
            for sz in (1, -1):
                xx = w * 0.75 * sx
                yy = h - (curve_r - math.sqrt(max(curve_r ** 2 - xx ** 2, 0)))
                sl = sl | sphere(0.022, (xx, yy, d * 0.7 * sz))
    return sl.at(*c)


def metal_back():
    s = round_box(0.16, 0.06, 0.46, 0.05, (0, -0.43, 0))
    for i in range(5):
        z = -0.36 + i * 0.18
        s = s | place(plate((0, 0, 0), 0.26, 0.1, 0.11, curve_r=0.32), Rx(12), (0, -0.4 + 0.02 * (i % 2), z))
        s = s | round_cone((0, -0.25, z - 0.02), (0, 0.15 - 0.06 * abs(i - 2), z + 0.08), 0.06, 0.006)
    return unit(saddle(s))


def metal_head():
    s = plate((0, -0.46, 0), 0.3, 0.15, 0.3, curve_r=0.35, rivets=False)
    s = s.su(round_box(0.03, 0.18, 0.3, 0.02, (0, -0.25, 0.0)), 0.02)                 # crest blade
    s = s | extrude([(-0.32, 0.0), (-0.2, 0.55), (0.0, 0.3), (0.15, 0.42), (0.35, 0.0)], 0.025, r=0.015, plane="zy").at(0, -0.36, 0)
    for sx in (1, -1):
        s = s | round_cone((0.22 * sx, -0.35, -0.05), (0.42 * sx, 0.1, 0.05), 0.07, 0.006)
    return unit(s)


def metal_tail():
    s = None
    for i in range(4):
        z = -0.42 + i * 0.16
        r = 0.18 - 0.02 * i
        seg = (cylinder(r, 0.07, axis=2, rr=0.015) - cylinder(r - 0.04, 0.2, axis=2)).at(0, 0, z)
        seg = seg | (torus(r, 0.015, axis=2).at(0, 0, z - 0.06))
        s = seg if s is None else s | seg
    blade = extrude([(-0.2, 0.0), (0.25, 0.32), (0.48, 0.0), (0.25, -0.32)], 0.03, r=0.015, plane="zy").at(0, 0, 0.0)
    s = s | (blade - cylinder(0.12, 0.3, axis=2).at(0, 0, -0.2))
    s = s | blade.rot(0, 0, 90)
    return unit(s)


def metal_shoulder():
    s = None
    for i in range(3):
        p = place(plate((0, 0, 0), 0.32 - 0.04 * i, 0.12, 0.28 - 0.03 * i, curve_r=0.36), Rz(-25 - 8 * i), (0.0 + 0.1 * i, -0.35 + 0.1 * i, 0))
        s = p if s is None else s | p
    s = s | round_cone((-0.08, -0.05, 0.0), (0.05, 0.42, 0.0), 0.075, 0.008)
    s = s | round_cone((0.12, -0.12, -0.08), (0.38, 0.2, -0.1), 0.06, 0.006)
    return unit(s)


def metal_cuff():
    s = ring(0.27, 0.35, 0.12, y=-0.25, rr=0.02)
    s = s.su(ring(0.27, 0.37, 0.02, y=-0.12, rr=0.01), 0.005).su(ring(0.27, 0.37, 0.02, y=-0.38, rr=0.01), 0.005)
    for i in range(8):
        a = i / 8 * math.tau
        s = s | sphere(0.025, (0.355 * math.cos(a), -0.25, 0.355 * math.sin(a)))
    for i in range(4):
        a = i / 4 * math.tau + 0.39
        c = np.array([0.34 * math.cos(a), -0.25, 0.34 * math.sin(a)])
        s = s | round_cone(tuple(c), tuple(c + np.array([math.cos(a), 0.15, math.sin(a)]) * 0.16), 0.05, 0.005)
    return unit(s - cylinder(0.27, 1.0, axis=1))


# ================================================================================================ assembly
ELEMENTS = {
    # element: (builders, colour keys per piece, material, preview colours, tris scale)
    "fire": ((fire_back, fire_head, fire_tail, fire_shoulder, fire_cuff), {"*": "flame"}, "skin",
             {"flame": "#FF8A1F", "glow": "#FF8A2B"}),
    "ice": ((ice_back, ice_head, ice_tail, ice_shoulder, ice_cuff), {"*": "glow"}, "ice", {"glow": "#A8E9FF"}),
    "lightning": ((lightning_back, lightning_head, lightning_tail, lightning_shoulder, lightning_cuff), {"*": "glow"}, "hard", {"glow": "#FFF07A"}),
    "earth": ((earth_back, earth_head, earth_tail, earth_shoulder, earth_cuff), {"*": "stone"}, "stone", {"stone": "#9C8F7E", "darkStone": "#6E6A62"}),
    "nature": ((nature_back, nature_head, nature_tail, nature_shoulder, nature_cuff), {"*": "leaf"}, "leaf", {"leaf": "#4E9A3A"}),
    "water": ((water_back, water_head, water_tail, water_shoulder, water_cuff), {"*": "glow"}, "glass", {"glow": "#3FB6FF"}),
    "wind": ((wind_back, wind_head, wind_tail, wind_shoulder, wind_cuff), {"*": "glow"}, "skin", {"glow": "#C2FFEE"}),
    "shadow": ((shadow_back, shadow_head, shadow_tail, shadow_shoulder, shadow_cuff), {"*": "glow"}, "skin", {"glow": "#5A22C8"}),
    "light": ((light_back, light_head, light_tail, light_shoulder, light_cuff), {"*": "gold"}, "foil", {"gold": "#E8B53A"}),
    "arcane": ((arcane_back, arcane_head, arcane_tail, arcane_shoulder, arcane_cuff), {"*": "gem"}, "hard", {"gem": "#D58CFF"}),
    "poison": ((poison_back, poison_head, poison_tail, poison_shoulder, poison_cuff), {"*": "glow"}, "skin", {"glow": "#B5FF5A"}),
    "metal": ((metal_back, metal_head, metal_tail, metal_shoulder, metal_cuff), {"*": "steel"}, "metal", {"steel": "#7C8794"}),
}

# per-piece colour overrides (a second key so the kit is two-toned where it helps)
COLOURS = {
    "fire": {"Back": "flame", "Head": "flame", "TailTip": "flame", "Shoulder": "flame", "Cuff": "flame"},
    "earth": {"Cuff": "darkStone"},
    "metal": {"Cuff": "gunmetal"},
    "shadow": {},
}

TRIS = {"Back": 2200, "Head": 1500, "TailTip": 1100, "Shoulder": 1000, "Cuff": 1000}
SMOOTH = {"ice": 1, "earth": 2, "metal": 2, "lightning": 2, "arcane": 2}


def _base_pattern(el, part):
    """Darken the root of each piece (where it meets the creature), so the dressing grows out of the body."""
    if part == "Cuff":
        return None
    return None


def _dressing(el):
    builders, cols, mat, prev = ELEMENTS[el]
    H = Hero(f"dressing_{el}", plan="Dressing", gait="float", tags=["dressing", el])
    H.preview = dict(prev)
    for name in ("Back", "Head", "TailTip", "Cuff"):
        H.bone(name + "B", "Body", LAY[name])
    H.mbone("ShoulderB#", "Body", LAY["Shoulder"])
    sm = SMOOTH.get(el, 4)

    def col_of(part):
        return COLOURS.get(el, {}).get(part, cols["*"])

    def root_shade(part):
        # a soft darkening toward the attachment side (darker roots, bright tips), in the laid-out position
        ox, oy, oz = LAY[part]
        if part == "TailTip":
            return lambda P: 0.72 + 0.28 * np.clip((P[:, 2] - oz + 0.5), 0, 1)
        if part == "Cuff":
            return lambda P: 0.8 + 0.2 * np.clip((P[:, 1] - oy + 0.5), 0, 1)
        return lambda P: 0.7 + 0.3 * np.clip((P[:, 1] - oy + 0.5) * 1.2, 0, 1)

    back, head, tail, sh, cuff = builders
    for part, fn in (("Back", back), ("Head", head), ("TailTip", tail), ("Cuff", cuff)):
        H.piece(part, part + "B", fn().at(*LAY[part]), col=col_of(part), mat=mat, tris=TRIS[part], role="spike" if part != "Cuff" else "armour",
                smooth=sm, pattern=root_shade(part), pri=1.6, res=128)
    shp = sh().at(*LAY["Shoulder"])
    lay = LAY["Shoulder"]
    H.mpiece("Shoulder#", "ShoulderB#", shp, col=col_of("Shoulder"), mat=mat, tris=TRIS["Shoulder"], role="spike", smooth=sm,
             pattern=lambda P: 0.7 + 0.3 * np.clip((P[:, 1] - lay[1] + 0.5) * 1.2, 0, 1), pri=1.7, res=128)

    def idle(t):
        a = math.sin(t / 2.0 * math.tau)
        return {"Body": (0, 0.02 * a, 0, 0, 0, 0)}

    H.clip("Idle", 2.0, idle, keys=8)
    H.clip("Move", 1.0, lambda t: {"Body": (0, 0.03 * math.sin(t * math.tau), 0, 0, 0, 0)}, keys=8)
    H.clip("Attack", 0.6, lambda t: {"Body": (0, 0.05 * math.sin(math.pi * t / 0.6), 0, 0, 0, 0)}, keys=6, loop=False)
    H.clip("Hit", 0.4, lambda t: {"Body": (0, 0, 0.04 * math.sin(math.pi * t / 0.4), 0, 0, 0)}, keys=6, loop=False)
    H.rig.update({"anchors": {"Back": "back", "Head": "head", "TailTip": "tail", "ShoulderR": "shoulder", "ShoulderL": "shoulder", "Cuff": "foot"}})
    H.socket("head", (0, 1.9, 0), "Body")
    return H


def _reg(el):
    hero(f"dressing_{el}", FAM)(lambda: _dressing(el))


for _el in ELEMENTS:
    _reg(_el)

MAP = []
