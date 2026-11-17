"""Summon set: the wolf (canine) hero sculpt.

Modelled in model space on refs.json "wolf" (the canine archetype of Plans/Quadruped: +Y up, -Z front, studs) and
cut along the quadruped rig: trunk with the chest ruff, maned neck, upper and lower legs with toed paws, a bushy
two-piece tail. The head keeps the canine head sculpt (s_head_canine) and its ear pieces. Each piece is a "unit"
sculpt in the frame of one lead primitive of its bone. Assigned at the end of Plans/Quadruped.luau.
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from . import piece
from .refs import Group, refs

W = "wolf"


def _def(pid, G, tris, res, note, extra=(), mirror=False, pad=0.22):
    def deco(fn):
        piece(pid, G.region_local(pad, extra), tris=tris, kind="unit", res=res, note=note, mirror=mirror, lead=tuple(G.s), smooth=4)(lambda: G.local(fn()))
        return fn
    return deco


def _lock(base, tip, r, t=0.11):
    """A soft lock of fur: 70% of the drawn length, blunt tip, so the coat reads as fur clumps and not as spines."""
    a, b = np.asarray(base, float), np.asarray(tip, float)
    return round_cone(tuple(a), tuple(a + (b - a) * 0.7), r, min(t, r * 0.6))


def _tuft(s, base, tip, r, k=0.16):
    """A lock of fur: fat at the root, pointed at the tip."""
    return s.su(_lock(base, tip, r), k)


GB = Group(W, "Torso", ["Chest", "Haunch", "Belly"])


@_def("s_wolf_body", GB, 2400, 170, "Wolf trunk (lead Torso; members Chest, Haunch, Belly): deep chest, tucked waist, haunches, shoulder blades, breast ruff, "
      "hackles along the spine.", extra=[(1.05, 2.6, 0), (0, 1.5, -1.6), (0, 3.75, -1.6), (0, 3.6, 2.5), (0, 2.6, -2.75)])
def body():
    s = ellipsoid(0.82, 1.0, 1.12, (0, 2.6, -1.3))                                   # chest
    s = s.su(ellipsoid(0.66, 0.72, 1.4, (0, 2.68, 0.15)), 0.4)                       # waist (tucked up)
    s = s.su(ellipsoid(0.76, 0.86, 1.0, (0, 2.62, 1.4)), 0.4)                        # haunch
    s = s.su(ellipsoid(0.3, 0.72, 0.5, (0.56, 2.8, -1.42)).mirror_x(), 0.18)         # shoulder blades
    s = s.su(ellipsoid(0.36, 0.7, 0.62, (0.52, 2.6, 1.45)).mirror_x(), 0.18)         # hips
    s = s.su(round_cone((0, 2.9, -1.5), (0, 3.3, -1.85), 0.66, 0.56), 0.3)           # neck root
    s = s.su(round_cone((0, 2.85, 1.7), (0, 2.9, 2.1), 0.42, 0.32), 0.25)            # tail root
    # breast ruff: overlapping locks hanging from the front of the chest
    for (x, y, z, dx, r) in [(0, 2.35, -2.2, 0, 0.34), (0.38, 2.5, -2.05, 0.1, 0.28), (0.2, 2.05, -2.0, 0.04, 0.26), (0.55, 2.2, -1.75, 0.12, 0.24)]:
        t = _lock((x, y, z), (x + dx, y - 0.55, z - 0.12), r)
        s = s.su(t.mirror_x() if x else t, 0.16)
    for i in range(7):  # hackles
        z = -1.6 + i * 0.52
        y = 3.5 - 0.06 * i - 0.02 * (i - 3) ** 2 + (0.1 if i < 2 else 0)
        s = _tuft(s, (0, y - 0.18, z - 0.1), (0, y + 0.16, z + 0.34), 0.2)
    for sx, y, z in [(0.62, 2.1, 0.9), (0.66, 2.0, -0.6)]:  # flank fur
        s = s.su(_lock((sx, y + 0.3, z - 0.2), (sx + 0.03, y - 0.1, z + 0.25), 0.2).mirror_x(), 0.16)
    return s


GN = Group(W, "Neck")


@_def("s_wolf_neck", GN, 1000, 150, "Wolf neck (lead Neck): thick, with a ruff of fur locks round the throat and a mane down the nape.",
      extra=[(0.95, 3.3, -1.9), (0, 2.3, -2.5), (0, 4.6, -1.8), (0, 2.6, -1.2), (0, 4.4, -2.8)])
def neck():
    s = tube([(0, 2.95, -1.62), (0, 3.6, -2.12), (0, 4.1, -2.5)], [0.62, 0.56, 0.55], k=0.2)
    for i in range(4):  # mane
        u = i / 3
        y, z = 3.45 + u * 0.95, -1.42 - u * 0.62
        s = _tuft(s, (0, y - 0.1, z - 0.2), (0, y + 0.3, z + 0.3), 0.26)
    for ang in (35, 80, 125, 160):  # ruff, both sides, sweeping back and down
        a = np.radians(ang)
        x, y0 = 0.5 * np.sin(a), -0.5 * np.cos(a)
        base = (x, 3.55 + y0 * 0.7, -2.2 + 0.3 * np.cos(a))
        tip = (x * 1.5, base[1] - 0.5, base[2] + 0.4)
        s = s.su(_lock(base, tip, 0.27).mirror_x(), 0.16)
    s = _tuft(s, (0, 3.1, -2.3), (0, 2.55, -2.35), 0.3)  # throat lock
    return s


def _paw(s, x, z, d, w=0.26):
    """Paw at (x, z) pointing in direction d (-1 forward): pad, four toes, short claws."""
    s = s.su(ellipsoid(w, 0.16, 0.34, (x, 0.17, z + d * 0.12)), 0.1)
    for k in (-1.5, -0.5, 0.5, 1.5):
        tx = x + k * w * 0.48
        tz = z + d * (0.42 - 0.05 * abs(k))
        s = s.su(ellipsoid(0.085, 0.1, 0.13, (tx, 0.13, tz)), 0.04)
        s = s.su(round_cone((tx, 0.12, tz + d * 0.1), (tx, 0.04, tz + d * 0.22), 0.04, 0.01), 0.02)
    return SDF(lambda p: np.maximum(s(p), 0.012 - p[:, 1]))


GTF, GSF = Group(W, "limb5"), Group(W, "limb7", ["foot9"])
GTH, GSH = Group(W, "limb11"), Group(W, "limb13", ["foot15"])


@_def("s_wolf_thigh_f", GTF, 450, 130, "Wolf foreleg, upper (lead: front hip limb): shoulder, lean forearm muscle, elbow tuft.", extra=[(0.95, 2.5, -1.4), (0.0, 0.8, -1.4), (0.45, 1.5, -0.9)], mirror=True)
def thigh_f():
    hip, el = (0.47, 2.45, -1.38), (0.45, 1.0, -1.47)
    s = round_cone(hip, el, 0.37, 0.22).su(sphere(0.4, hip), 0.1)
    s = s.su(ellipsoid(0.22, 0.5, 0.3, (0.5, 1.95, -1.3)), 0.12)
    s = _tuft(s, (0.45, 1.45, -1.28), (0.46, 1.05, -1.08), 0.16)
    return s.su(sphere(0.24, el), 0.06)


@_def("s_wolf_shin_f", GSF, 700, 140, "Wolf foreleg, lower (lead: front knee limb; member: paw): slim cannon, toed paw with claws.",
      extra=[(0.85, 0.0, -2.1), (0.05, 1.2, -1.2)], mirror=True)
def shin_f():
    s = round_cone((0.45, 1.0, -1.47), (0.45, 0.3, -1.42), 0.22, 0.165).su(sphere(0.24, (0.45, 1.0, -1.47)), 0.06)
    return _paw(s, 0.45, -1.5, -1)


@_def("s_wolf_thigh_h", GTH, 500, 130, "Wolf hind leg, upper (lead: hind hip limb): strong haunch muscle, stifle.", extra=[(1.05, 2.5, 1.5), (0.0, 0.8, 1.6), (0.47, 1.6, 2.2), (0.47, 1.6, 0.85)], mirror=True)
def thigh_h():
    hip, kn = (0.48, 2.4, 1.44), (0.47, 1.03, 1.65)
    s = round_cone(hip, kn, 0.47, 0.23).su(sphere(0.5, hip), 0.1)
    s = s.su(ellipsoid(0.34, 0.62, 0.5, (0.52, 1.95, 1.36)), 0.14)
    s = _tuft(s, (0.47, 1.6, 1.8), (0.48, 1.15, 2.02), 0.17)
    return s.su(sphere(0.25, kn), 0.06)


@_def("s_wolf_shin_h", GSH, 700, 140, "Wolf hind leg, lower (lead: hind knee limb; member: paw): hock, slim cannon, toed paw.",
      extra=[(0.9, 0.0, 0.75), (0.05, 1.25, 1.95)], mirror=True)
def shin_h():
    s = round_cone((0.47, 1.03, 1.65), (0.47, 0.3, 1.5), 0.23, 0.165).su(sphere(0.25, (0.47, 1.03, 1.65)), 0.06)
    s = s.su(ellipsoid(0.13, 0.2, 0.16, (0.47, 1.0, 1.82)), 0.07)  # hock point
    return _paw(s, 0.47, 1.42, -1)


GT1, GT2 = Group(W, "tail31"), Group(W, "tail32")


@_def("s_wolf_tail1", GT1, 450, 130, "Wolf brush, root (lead: first tail segment): thickening fur with locks.", extra=[(0.55, 2.6, 2.8), (0, 3.35, 2.2), (0, 1.7, 3.6), (0, 2.9, 1.7)])
def tail1():
    a, b = (0, 2.92, 1.95), (0, 2.25, 3.6)
    s = round_cone(a, b, 0.3, 0.46).su(sphere(0.32, a), 0.05)
    for sx, u, r in [(0.22, 0.45, 0.2), (0.0, 0.7, 0.24)]:
        y, z = a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u
        t = _lock((sx, y + 0.22, z - 0.1), (sx * 1.3, y + 0.34, z + 0.45), r)
        s = s.su(t.mirror_x() if sx else t, 0.16)
    return s


@_def("s_wolf_tail2", GT2, 550, 140, "Wolf brush, tip (lead: last tail segment): full bush tapering to a point, shaggy underside.",
      extra=[(0.65, 1.9, 4.1), (0, 2.95, 3.2), (0, 1.1, 5.3), (0, 1.3, 3.6)])
def tail2():
    a, b, c = (0, 2.42, 3.25), (0, 1.85, 4.3), (0, 1.42, 5.08)
    s = round_cone(a, b, 0.46, 0.5).su(round_cone(b, c, 0.5, 0.1), 0.2)
    for i, (u, sx) in enumerate([(0.2, 0.3), (0.5, 0.0), (0.75, 0.28)]):
        y, z = a[1] + (c[1] - a[1]) * u, a[2] + (c[2] - a[2]) * u
        t = _lock((sx, y - 0.3, z - 0.1), (sx * 1.2, y - 0.62, z + 0.3), 0.2)  # under locks
        s = s.su(t.mirror_x() if sx else t, 0.16)
        t2 = _lock((sx * 0.6, y + 0.3, z - 0.1), (sx * 0.7, y + 0.42, z + 0.4), 0.2)
        s = s.su(t2.mirror_x() if sx else t2, 0.16)
    return s


# ------------------------------------------------------------------------------------------------ head
GH = Group(W, "Head", ["Snout", "ear27", "ear28", "ear29", "ear30"])


@_def("s_wolf_head", GH, 2400, 180, "Wolf head (lead Head; members Snout, ears): long deep muzzle with a stop, brow ridges, lower jaw with a lip line, "
      "cheek ruffs, tall cupped ears.", extra=[(1.5, 4.0, -2.8), (0, 6.15, -2.8), (0, 3.2, -3.8), (0, 4.0, -4.85), (0, 4.2, -1.75)])
def head():
    s = GH.blend(0.3, ["Head", "Snout"])
    s = s.su(ellipsoid(0.44, 0.36, 0.8, (0, 3.92, -3.9)), 0.2)                           # deep muzzle
    s = s.su(ellipsoid(0.26, 0.22, 0.62, (0, 4.22, -3.72)), 0.16)                        # nasal bridge up to the stop
    s = s.su(capsule((0.16, 4.82, -3.52), (0.64, 4.72, -3.3), 0.13).mirror_x(), 0.12)    # brow ridges
    s = s.su(ellipsoid(0.34, 0.15, 0.62, (0, 3.56, -3.82)), 0.07)                        # lower jaw
    s = s.ss(capsule((0.14, 3.66, -4.6), (0.46, 3.72, -3.5), 0.035).mirror_x(), 0.04)    # lip line
    s = s.su(ellipsoid(0.3, 0.3, 0.32, (0.56, 3.85, -3.25)).mirror_x(), 0.16)            # cheek / jaw muscle
    for (y, z, dx, dy, dz, r) in [(4.05, -2.75, 0.5, -0.38, 0.3, 0.34), (3.75, -2.95, 0.36, -0.5, 0.28, 0.3), (4.4, -2.5, 0.48, -0.12, 0.42, 0.3)]:
        s = s.su(_lock((0.78, y, z), (0.78 + dx, y + dy, z + dz), r).mirror_x(), 0.14)   # cheek ruff
    s = s.su(_lock((0, 4.75, -2.15), (0, 4.6, -1.6), 0.4), 0.16)                         # scruff
    # ears: tall triangles, thin front to back, cupped toward the front
    base, tip = np.array((0.62, 4.8, -2.72)), np.array((0.98, 6.0, -2.86))
    ear = round_cone(tuple(base), tuple(tip), 0.46, 0.05)
    ax = (tip - base) / np.linalg.norm(tip - base)
    mid = (base + tip) / 2
    slab = SDF(lambda p: np.abs(0.82 * (p - mid)[:, 2] + 0.1 * (p - mid)[:, 1] + 0.56 * np.abs(p[:, 0]) - 0.56 * mid[0]) - 0.17)  # turned outward
    ear = ear.si(slab, 0.06)
    cup = round_cone(tuple(base + ax * 0.25 + np.array((-0.12, 0, -0.22))), tuple(tip - ax * 0.2 + np.array((-0.1, 0, -0.18))), 0.3, 0.03)
    ear = ear.ss(cup, 0.05)
    return s.su(ear.mirror_x(), 0.1)
