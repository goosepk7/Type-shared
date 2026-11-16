"""Summon set: the dragon hero sculpt.

One coherent dragon modelled in MODEL space on the signature's reference build (refs.json "sig:dragon": +Y up,
-Z front, studs), then cut along the rig: every piece belongs to one bone and is expressed in the local frame of
one lead primitive of that bone (kind "unit", lead = that primitive's reference size), so the Animator still
moves neck, head, jaw, legs, tail and wings. Joints are overlapping balls, so the pieces stay closed when a bone
turns and when a seed stretches the proportions a few percent. Signatures/Creatures.luau assigns the pieces.
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from . import piece
from .refs import Group, refs

W = "sig:dragon"
_names = [p["name"] for p in refs()[W]["parts"]]


def _first(role, bone, shape=None):
    for p in refs()[W]["parts"]:
        if p.get("role") == role and p.get("bone") == bone and (shape is None or p["shape"] == shape) and not p.get("mirrored"):
            return p["name"]
    raise KeyError((role, bone))


def _blade(a, b, r0, r1, thick=0.07):
    """Flat spike in the x = 0 plane."""
    return round_cone(a, b, r0, r1).si(box(thick, 50, 50), 0.05)


def _scales(s, pts, r=0.16, k=0.07):
    """Raised scute plates at the given points."""
    for (x, y, z, sx, sy, sz) in pts:
        s = s.su(ellipsoid(sx, sy, sz, (x, y, z)), k)
    return s


def _def(pid, G, tris, res, note, extra=(), mirror=False, pad=0.25):
    def deco(fn):
        piece(pid, G.region_local(pad, extra), tris=tris, kind="unit", res=res, note=note, mirror=mirror, lead=tuple(G.s), smooth=4)(lambda: G.local(fn()))
        return fn
    return deco


# ------------------------------------------------------------------------------------------------ body
GB = Group(W, "Torso", ["Chest"])


@_def("s_dragon_body", GB, 3200, 170, "Dragon torso (lead Torso, members Chest): keeled chest, barrel, haunches, shoulder and hip muscle, wing roots, scale rows.",
      extra=[(1.45, 2.6, 0), (0, 1.3, 0), (0, 3.9, -2.3), (0, 3.0, 2.6)])
def body():
    s = ellipsoid(1.08, 1.22, 1.3, (0, 2.78, -1.12))
    s = s.su(ellipsoid(0.95, 1.02, 1.7, (0, 2.68, 0.15)), 0.35)
    s = s.su(ellipsoid(1.02, 1.08, 1.15, (0, 2.68, 1.3)), 0.35)
    s = s.su(ellipsoid(0.42, 0.78, 0.6, (0.88, 2.62, -1.18)).mirror_x(), 0.18)  # shoulders
    s = s.su(ellipsoid(0.5, 0.85, 0.72, (0.86, 2.58, 1.45)).mirror_x(), 0.18)  # hips
    s = s.su(ellipsoid(0.3, 0.26, 0.42, (0.42, 3.62, -1.1)).mirror_x(), 0.16)  # wing roots
    s = s.su(round_cone((0, 3.05, -1.7), (0, 3.55, -2.05), 0.82, 0.66), 0.25)  # neck root
    s = s.su(round_cone((0, 2.8, 1.7), (0, 2.8, 2.35), 0.8, 0.58), 0.25)  # tail root
    s = s.ss(capsule((0.62, 3.2, -0.5), (0.62, 3.1, 0.9), 0.1).mirror_x(), 0.2)  # flank hollow under the wing
    # the back stays just under the primitive torso so the dorsal spikes keep their footing
    return s


GBe = Group(W, "BellyPlate1", ["BellyPlate2"])


@_def("s_dragon_belly", GBe, 900, 150, "Dragon underbelly (lead BellyPlate1, member BellyPlate2): overlapping scutes from throat to tail root.",
      extra=[(0.8, 1.5, -2.2), (0, 1.3, 2.2), (0, 3.4, -2.7)])
def belly():
    s = None
    n = 10
    for i in range(n):
        u = i / (n - 1)
        z = -1.75 + u * 3.6
        y = 1.52 + 0.2 * abs(2 * u - 1) ** 2.5
        w = 0.7 - 0.22 * (2 * u - 1) ** 2
        e = ellipsoid(w, 0.2, 0.27, (0, y, z))
        s = e if s is None else s.su(e, 0.03)
    # breast plates climbing the front of the chest to the neck root
    for i in range(1, 6):
        th = np.radians(i * 15 + 22)
        e = ellipsoid(0.62 - 0.05 * i, 0.24, 0.24, (0, 2.78 - 1.27 * np.cos(th), -1.12 - 1.35 * np.sin(th)))
        s = s.su(e, 0.03)
    return s


# ------------------------------------------------------------------------------------------------ neck
GN = Group(W, "Neck")


@_def("s_dragon_neck", GN, 1500, 150, "Dragon neck (lead Neck): thick base tapering to the skull, throat scutes in front, dorsal fins.",
      extra=[(0.9, 3.0, -1.6), (0, 6.3, -3.2), (0, 2.6, -1.9)])
def neck():
    a, b, c, d = (0, 3.0, -1.72), (0, 3.95, -2.3), (0, 4.95, -2.95), (0, 5.8, -3.5)
    s = tube([a, b, c, d], [0.78, 0.62, 0.52, 0.5], k=0.2)
    # throat scutes (front / under side)
    for i in range(7):
        u = i / 6
        y, z = 3.05 + u * 2.55, -2.3 - u * 1.62
        s = s.su(ellipsoid(0.4 - 0.12 * u, 0.2, 0.2, (0, y, z)), 0.05)
    # dorsal fins
    for i in range(5):
        u = i / 4
        y, z = 3.75 + u * 2.0, -1.72 - u * 1.3
        s = s.su(_blade((0, y - 0.1, z - 0.05), (0, y + 0.3, z + 0.42), 0.2, 0.03), 0.05)
    return s


# ------------------------------------------------------------------------------------------------ head
GH = Group(W, "Head", ["Snout"])


@_def("s_dragon_head", GH, 2600, 170, "Dragon skull (lead Head, members Snout, ears): wedge muzzle, nostrils, brow ridges, cheek spikes, jaw hinge, frill.",
      extra=[(1.2, 6.0, -3.2), (0, 6.9, -3.0), (0, 5.5, -5.9)])
def head():
    s = GH.blend(0.3)
    s = s.su(ellipsoid(0.34, 0.24, 0.85, (0, 6.16, -4.7)), 0.14)  # nasal ridge
    s = s.su(ellipsoid(0.1, 0.07, 0.14, (0.22, 6.2, -5.5)).mirror_x(), 0.07)  # nostrils
    s = s.ss(sphere(0.045, (0.25, 6.22, -5.64)).mirror_x(), 0.03)
    s = s.su(capsule((0.5, 6.5, -4.15), (0.62, 6.62, -3.55), 0.13).mirror_x(), 0.1)  # brow ridge above / behind the eye
    s = s.su(round_cone((0.66, 5.85, -3.7), (1.02, 5.8, -3.15), 0.2, 0.04).mirror_x(), 0.1)  # cheek spikes
    s = s.su(round_cone((0.62, 5.62, -3.9), (0.9, 5.45, -3.5), 0.15, 0.03).mirror_x(), 0.08)
    s = s.su(ellipsoid(0.34, 0.3, 0.34, (0.42, 5.75, -3.75)).mirror_x(), 0.15)  # jaw muscle
    s = s.su(_blade((0, 6.5, -3.6), (0, 6.85, -3.0), 0.2, 0.04), 0.08)  # crest
    # frill ears
    s = s.su(round_cone((0.55, 6.3, -3.3), (0.78, 6.75, -2.75), 0.17, 0.03).mirror_x().si(ellipsoid(1.2, 1.2, 1.4, (0, 6.3, -3.3)), 0.05), 0.08)
    s = s.ss(capsule((0.3, 5.74, -5.7), (0.52, 5.72, -4.3), 0.035).mirror_x(), 0.05)  # lip line
    return s


GJ = Group(W, "Jaw")


@_def("s_dragon_jaw", GJ, 700, 140, "Dragon lower jaw (lead Jaw): tapering mandible, chin spikes, a row of lower teeth.",
      extra=[(0.6, 5.2, -4.0), (0, 5.2, -5.8)])
def jaw():
    s = ellipsoid(0.47, 0.2, 0.8, (0, 5.5, -4.9))
    s = s.su(ellipsoid(0.3, 0.17, 0.4, (0, 5.5, -5.35)), 0.12)
    s = s.su(round_cone((0, 5.4, -5.35), (0, 5.2, -5.2), 0.1, 0.02), 0.05)  # chin spike
    s = s.su(round_cone((0.3, 5.42, -4.5), (0.4, 5.22, -4.25), 0.1, 0.02).mirror_x(), 0.05)
    for i in range(5):
        z = -5.5 + i * 0.25
        x = 0.2 + 0.05 * i
        s = s.su(round_cone((x, 5.6, z), (x, 5.78, z), 0.05, 0.012).mirror_x(), 0.02)
    return s


GHo = Group(W, _first("horn", "Head"))


@_def("s_dragon_horns", GHo, 1300, 150, "Dragon horn crown (lead: first horn segment; members: every other horn): two long swept horns with growth rings, two side horns.",
      extra=[(1.3, 7.6, -1.6), (-1.3, 6.0, -3.8)], pad=0.2)
def horns():
    def horn(pts, radii):
        h = tube(pts, radii, k=0.08)
        for i in range(1, 6):  # growth rings on the lower half
            u = i / 11
            p = np.array(pts[0]) * (1 - u * 2) + np.array(pts[1]) * (u * 2) if u < 0.5 else np.array(pts[1])
            h = h.su(sphere(radii[0] * (1.12 - u * 0.5), tuple(p)), 0.02)
        return h
    s = horn([(0.46, 6.4, -3.5), (0.62, 6.95, -2.95), (0.8, 7.25, -2.25), (0.95, 7.3, -1.7)], [0.2, 0.16, 0.1, 0.03]).mirror_x()
    s = s.su(horn([(0.6, 6.1, -3.5), (0.85, 6.3, -3.05), (1.1, 6.55, -2.7)], [0.13, 0.09, 0.025]).mirror_x(), 0.02)
    return s


# ------------------------------------------------------------------------------------------------ legs
def _leg(hip, knee, r0, r1, bulge):
    s = round_cone(hip, knee, r0, r1)
    s = s.su(sphere(r0 * 1.05, hip), 0.1)
    s = s.su(ellipsoid(r0 * 0.75, r0 * 1.3, r0 * 0.95, bulge), 0.15)
    return s.su(sphere(r1 * 1.12, knee), 0.08)


def _shin(knee, ankle, toe, r0, r1, span):
    s = round_cone(knee, ankle, r0, r1).su(sphere(r0 * 1.1, knee), 0.08)
    ax, ay, az = ankle
    tx, tz = toe
    s = s.su(ellipsoid(span * 1.25, 0.17, abs(tz - az) * 0.62 + 0.12, (tx, 0.19, (az + tz) / 2)), 0.14)  # foot
    d = -1 if tz < az else 1
    for k in (-1, 0, 1):
        x0 = tx + k * span
        s = s.su(round_cone((x0, 0.2, tz), (x0 + k * 0.05, 0.3, tz + d * 0.12), 0.11, 0.1), 0.05)  # knuckle
        s = s.su(round_cone((x0 + k * 0.05, 0.24, tz + d * 0.14), (x0 + k * 0.1, 0.05, tz + d * 0.42), 0.085, 0.015), 0.03)  # claw
    s = s.su(round_cone((ax, 0.3, az - d * 0.1), (ax, 0.1, az - d * 0.38), 0.09, 0.02), 0.04)  # heel spur
    return SDF(lambda p: np.maximum(s(p), 0.012 - p[:, 1]))  # stands on the ground plane


GTF, GSF = Group(W, "limb3"), Group(W, "limb5")
GTH, GSH = Group(W, "limb7"), Group(W, "limb9")


@_def("s_dragon_thigh_f", GTF, 800, 130, "Dragon foreleg, upper (lead: front hip limb): shoulder ball, biceps, elbow.", extra=[(1.3, 2.6, -1.2), (0.1, 0.7, -1.2)], mirror=True)
def thigh_f():
    return _leg((0.68, 2.45, -1.18), (0.74, 1.0, -1.1), 0.5, 0.33, (0.78, 2.0, -0.98))


@_def("s_dragon_shin_f", GSF, 1000, 140, "Dragon foreleg, lower (lead: front knee limb): forearm, clawed foot with three talons and a heel spur.",
      extra=[(1.3, 0.0, -1.9), (0.2, 1.3, -0.7)], mirror=True)
def shin_f():
    return _shin((0.74, 1.0, -1.1), (0.78, 0.3, -1.22), (0.78, -1.62), 0.34, 0.23, 0.2)


@_def("s_dragon_thigh_h", GTH, 900, 130, "Dragon hind leg, upper (lead: hind hip limb): heavy haunch, knee.", extra=[(1.45, 2.7, 1.5), (0.0, 0.7, 1.5)], mirror=True)
def thigh_h():
    return _leg((0.7, 2.45, 1.5), (0.78, 1.0, 1.72), 0.6, 0.37, (0.82, 2.05, 1.3))


@_def("s_dragon_shin_h", GSH, 1000, 140, "Dragon hind leg, lower (lead: hind knee limb): hock, clawed foot.", extra=[(1.35, 0.0, 0.85), (0.2, 1.3, 2.1)], mirror=True)
def shin_h():
    return _shin((0.78, 1.0, 1.72), (0.8, 0.3, 1.5), (0.8, 1.08), 0.37, 0.25, 0.22)


# ------------------------------------------------------------------------------------------------ tail
_tails = [p["name"] for p in refs()[W]["parts"] if p.get("role") == "tail"]
GT1, GT2, GT3 = Group(W, _tails[0]), Group(W, _tails[1]), Group(W, _tails[2])


def _tail(a, b, r0, r1, fins):
    s = round_cone(a, b, r0, r1).su(sphere(r0, a), 0.05)
    for i in range(fins):
        u = (i + 0.5) / fins
        p = np.array(a) * (1 - u) + np.array(b) * u
        r = r0 * (1 - u) + r1 * u
        s = s.su(_blade((0, p[1] + r * 0.6, p[2] - 0.1), (0, p[1] + r + 0.3 * r0 / 0.58 + 0.08, p[2] + 0.3), 0.17 * r / 0.5 + 0.04, 0.02, 0.05), 0.04)
        s = s.su(ellipsoid(r * 0.75, r * 0.3, 0.2, (0, p[1] - r * 0.86, p[2])), 0.04)  # under scute
    return s


@_def("s_dragon_tail1", GT1, 800, 130, "Dragon tail root (lead: first tail segment): heavy, dorsal fins, under scutes.", extra=[(0, 3.9, 3.0), (0.7, 2.8, 1.7)])
def tail1():
    return _tail((0, 2.8, 1.95), (0, 2.68, 4.05), 0.58, 0.42, 3)


@_def("s_dragon_tail2", GT2, 700, 130, "Dragon tail, middle (lead: second tail segment).", extra=[(0, 3.4, 4.6), (0.5, 2.6, 3.4)])
def tail2():
    return _tail((0, 2.66, 3.6), (0, 2.38, 5.7), 0.42, 0.27, 3)


@_def("s_dragon_tail3", GT3, 800, 140, "Dragon tail tip (lead: last tail segment): whip ending in a barbed spade.", extra=[(0, 3.0, 7.0), (0, 1.3, 8.0), (0.4, 2.2, 5.2)])
def tail3():
    s = round_cone((0, 2.36, 5.25), (0, 2.1, 7.0), 0.27, 0.1).su(sphere(0.27, (0, 2.36, 5.25)), 0.05)
    spade = ellipsoid(0.07, 0.62, 0.62, (0, 2.06, 7.25)).si(round_cone((0, 2.06, 6.75), (0, 2.02, 7.95), 0.68, 0.01), 0.06)
    spade = spade.ss(sphere(0.3, (0, 2.75, 6.72)), 0.05).ss(sphere(0.3, (0, 1.37, 6.72)), 0.05)  # barbs
    return s.su(spade, 0.08)
