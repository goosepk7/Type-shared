"""Summon set: the T. rex hero sculpt.

Modelled in model space on refs.json "sig:t rex" (+Y up, -Z front, studs) and cut along the biped rig: trunk,
neck, skull, mandible, thighs, shanks with the three-toed feet, the tiny arms, three tail pieces. Each piece is
a "unit" sculpt in the frame of one lead primitive of its bone; joints overlap as balls. Assigned in
Signatures/Creatures.luau (S["t rex"]).
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from . import piece
from .refs import Group, refs

W = "sig:t rex"
_P = {p["name"]: p for p in refs()[W]["parts"]}


def _def(pid, G, tris, res, note, extra=(), mirror=False, pad=0.3):
    def deco(fn):
        piece(pid, G.region_local(pad, extra), tris=tris, kind="unit", res=res, note=note, mirror=mirror, lead=tuple(G.s), smooth=4)(lambda: G.local(fn()))
        return fn
    return deco


def _bumps(s, pts, r, k=0.05):
    for (y, z, w) in pts:
        s = s.su(ellipsoid(r * w, r * 0.7 * w, r * 1.5 * w, (0, y, z)), k)
    return s


GB = Group(W, "Torso", ["Belly"])


@_def("s_trex_body", GB, 2600, 170, "T. rex trunk (lead Torso, member Belly): deep keeled chest, heavy hips, hip and shoulder muscle, neck and tail roots, spine bumps.",
      extra=[(1.75, 3.9, 0), (0, 2.0, -1.5), (0, 5.5, -3.0), (0, 5.4, 1.2), (0, 4.2, 2.7)])
def body():
    s = ellipsoid(1.32, 1.4, 1.75, (0, 4.15, 0.55))                                  # hips
    s = s.su(ellipsoid(1.26, 1.42, 2.0, (0, 3.72, -1.45)), 0.5)                      # rib cage
    s = s.su(ellipsoid(1.02, 1.2, 1.15, (0, 3.75, -2.75)), 0.4)                      # breast
    s = s.su(ellipsoid(0.92, 0.8, 1.9, (0, 2.72, -1.2)), 0.3)                        # belly
    s = s.su(round_cone((0, 4.25, -2.55), (0, 5.05, -2.95), 1.05, 0.9), 0.35)        # neck root
    s = s.su(round_cone((0, 4.3, 1.3), (0, 4.08, 2.3), 1.2, 1.0), 0.35)              # tail root
    s = s.su(ellipsoid(0.55, 1.05, 0.95, (1.02, 3.95, 0.5)).mirror_x(), 0.22)        # hip muscle over the thigh
    s = s.su(ellipsoid(0.4, 0.6, 0.55, (0.92, 3.7, -2.4)).mirror_x(), 0.2)           # shoulder
    s = s.ss(capsule((1.0, 4.35, -1.9), (1.05, 4.6, -0.6), 0.14).mirror_x(), 0.25)   # flank hollow
    spine = [(5.02 + 0.05 * i - 0.012 * (i - 4) ** 2 + (0.0 if i < 8 else -0.1), -2.25 + i * 0.47, 1.0 - 0.03 * abs(i - 4)) for i in range(9)]
    s = _bumps(s, spine, 0.2)
    for i in range(7):  # belly scutes
        z = -2.6 + i * 0.5
        s = s.su(ellipsoid(0.62, 0.16, 0.3, (0, 2.22 + 0.06 * (i - 3) ** 2 * 0.4 + (0.35 if i == 0 else 0), z)), 0.05)
    return s


GN = Group(W, "Neck")


@_def("s_trex_neck", GN, 600, 140, "T. rex neck (lead Neck): thick S-curve, throat wattle, nape bumps.", extra=[(1.0, 5.3, -3.0), (0, 4.3, -2.6), (0, 6.5, -3.4), (0, 4.6, -3.9)])
def neck():
    s = tube([(0, 4.75, -2.75), (0, 5.3, -3.05), (0, 5.85, -3.55)], [0.98, 0.9, 0.86], k=0.25)
    s = s.su(ellipsoid(0.5, 0.6, 0.5, (0, 4.95, -3.6)), 0.25)  # throat
    return _bumps(s, [(5.7, -2.35, 0.9), (6.1, -2.75, 0.9), (6.42, -3.15, 0.8)], 0.2)


GH = Group(W, "Head", ["Snout", "nose19", "nose20", "RidgeR", "RidgeL"])


@_def("s_trex_head", GH, 2600, 180, "T. rex skull (lead Head; members Snout, nostrils, brow ridges): deep boxy muzzle, brow horns, nasal rugosity, "
      "cheek muscle, upper tooth row.", extra=[(1.6, 6.3, -4.4), (0, 7.75, -5.0), (0, 5.0, -8.2), (0, 6.3, -2.6)])
def head():
    s = GH.blend(0.35, ["Head", "Snout"])
    s = s.su(round_box(0.8, 0.55, 1.3, 0.3, (0, 6.2, -6.75)), 0.3)                       # boxy muzzle
    s = s.su(ellipsoid(0.36, 0.2, 0.48, (0.78, 7.24, -5.0)).mirror_x(), 0.16)                 # brow horns
    s = s.su(round_cone((0.84, 7.3, -4.8), (0.93, 7.45, -4.5), 0.13, 0.05).mirror_x(), 0.1)
    for i in range(5):                                                                        # nasal rugosity
        s = s.su(ellipsoid(0.3, 0.16, 0.24, (0, 6.98 - 0.045 * i, -5.9 - i * 0.42)), 0.07)
    s = s.su(ellipsoid(0.2, 0.15, 0.22, (0.4, 6.72, -7.85)).mirror_x(), 0.08)                 # nostril mounds
    s = s.ss(sphere(0.09, (0.47, 6.74, -8.02)).mirror_x(), 0.04)
    s = s.su(ellipsoid(0.5, 0.75, 0.75, (1.05, 6.0, -3.75)).mirror_x(), 0.25)                 # jaw muscle
    s = s.su(ellipsoid(0.75, 0.5, 0.6, (0, 6.95, -3.2)), 0.3)                                 # occiput
    s = s.su(capsule((0.92, 5.72, -5.2), (0.72, 5.66, -7.7), 0.13).mirror_x(), 0.08)          # upper lip
    for i in range(7):                                                                        # upper teeth
        z = -5.5 - i * 0.36
        x = 0.9 - 0.03 * i
        h = 0.5 - 0.035 * abs(i - 3)
        s = s.su(round_cone((x, 5.66, z), (x - 0.02, 5.66 - h, z + 0.05), 0.11, 0.02).mirror_x(), 0.02)
    return s


GJ = Group(W, "Jaw")


@_def("s_trex_jaw", GJ, 900, 150, "T. rex mandible (lead Jaw): deep at the hinge, tapering chin, lower tooth row.", extra=[(1.05, 5.3, -5.0), (0, 4.75, -6.4), (0, 5.95, -8.0), (0, 5.4, -4.3)])
def jaw():
    s = ellipsoid(0.82, 0.36, 1.5, (0, 5.3, -6.4))
    s = s.su(ellipsoid(0.72, 0.5, 0.75, (0, 5.3, -5.1)), 0.2)
    s = s.su(ellipsoid(0.5, 0.3, 0.45, (0, 5.22, -7.55)), 0.15)
    s = s.ss(ellipsoid(0.5, 0.2, 1.2, (0, 5.62, -6.5)), 0.08)  # tongue well
    for i in range(6):
        z = -5.75 - i * 0.36
        x = 0.72 - 0.035 * i
        s = s.su(round_cone((x, 5.48, z), (x, 5.84 - 0.03 * abs(i - 2), z - 0.04), 0.1, 0.02).mirror_x(), 0.02)
    return s


GT, GS = Group(W, "limb3"), Group(W, "limb5", ["foot7", "claw9", "claw11", "claw13"])


@_def("s_trex_thigh", GT, 600, 140, "T. rex thigh (lead: hip limb): massive drumstick, knee.", extra=[(2.1, 4.3, 0.5), (0.3, 1.4, 0.5), (1.2, 3.0, -0.6), (1.2, 3.0, 1.7)], mirror=True)
def thigh():
    hip, knee = (1.12, 4.0, 0.42), (1.18, 1.78, 0.78)
    s = round_cone(hip, knee, 0.92, 0.5)
    s = s.su(sphere(0.95, hip), 0.15)
    s = s.su(ellipsoid(0.62, 1.15, 0.8, (1.28, 3.1, 0.2)), 0.2)   # quadriceps
    s = s.su(ellipsoid(0.5, 0.9, 0.6, (1.15, 3.0, 1.1)), 0.2)     # hamstring
    return s.su(sphere(0.56, knee), 0.1)


@_def("s_trex_shin", GS, 1100, 150, "T. rex shank and foot (lead: knee limb; members foot, claws): shank, ankle, three splayed toes with talons, dewclaw.",
      extra=[(2.0, 0.0, -1.4), (0.4, 2.3, 1.3), (1.2, 0.0, 1.1)], mirror=True)
def shin():
    knee, ankle = (1.18, 1.78, 0.78), (1.18, 0.5, 0.32)
    s = round_cone(knee, ankle, 0.5, 0.32).su(sphere(0.55, knee), 0.1)
    s = s.su(ellipsoid(0.36, 0.5, 0.5, (1.18, 1.35, 0.92)), 0.15)           # calf
    s = s.su(ellipsoid(0.46, 0.26, 0.6, (1.18, 0.3, 0.05)), 0.15)           # foot pad
    for k in (-1, 0, 1):
        x0 = 1.18 + k * 0.3
        tz = -0.82 + abs(k) * 0.1
        s = s.su(round_cone((1.18 + k * 0.12, 0.3, -0.2), (x0, 0.24, tz), 0.2, 0.16), 0.08)                  # toe
        s = s.su(sphere(0.19, (x0, 0.3, tz)), 0.04)                                                          # knuckle
        s = s.su(round_cone((x0 + k * 0.02, 0.3, tz - 0.1), (x0 + k * 0.08, 0.06, tz - 0.52), 0.13, 0.02), 0.04)  # talon
    s = s.su(round_cone((1.02, 0.45, 0.5), (0.9, 0.12, 0.85), 0.12, 0.02), 0.05)                              # dewclaw
    return SDF(lambda p: np.maximum(s(p), 0.012 - p[:, 1]))


GA = Group(W, "TinyArmR", ["limb31", "limb33", "hand35", "claw37", "claw39"])


@_def("s_trex_arm", GA, 400, 130, "T. rex tiny arm (lead TinyArm; members the arm limbs, hand, claws): two-fingered, hanging forward.",
      extra=[(1.55, 3.9, -2.3), (0.7, 2.3, -3.5)], mirror=True, pad=0.2)
def arm():
    sh, el, wr = (0.98, 3.72, -2.4), (1.16, 3.12, -2.68), (1.25, 2.72, -3.08)
    s = round_cone(sh, el, 0.26, 0.19).su(sphere(0.3, sh), 0.08)
    s = s.su(round_cone(el, wr, 0.2, 0.15), 0.06).su(ellipsoid(0.18, 0.13, 0.2, (1.25, 2.68, -3.12)), 0.05)
    for dx in (-0.09, 0.09):
        s = s.su(round_cone((1.25 + dx, 2.66, -3.2), (1.25 + dx * 1.3, 2.46, -3.42), 0.07, 0.012), 0.03)
    return s


def _tail(a, b, r0, r1, n, tip=False):
    s = round_cone(a, b, r0, r1).su(sphere(r0, a), 0.06)
    pts = []
    for i in range(n):
        u = (i + 0.5) / n
        r = r0 * (1 - u) + r1 * u
        pts.append((a[1] * (1 - u) + b[1] * u + r * 0.92, a[2] * (1 - u) + b[2] * u, r / 0.9))
    return _bumps(s, pts, 0.17, 0.04)


for _i, (_a, _b, _r0, _r1, _tr) in enumerate([
        ((0, 4.12, 1.75), (0, 3.78, 4.0), 1.02, 0.7, 500),
        ((0, 3.83, 3.6), (0, 3.36, 5.95), 0.7, 0.42, 400),
        ((0, 3.45, 5.5), (0, 2.86, 7.95), 0.42, 0.07, 300)]):
    _g = Group(W, "tail4%d" % (_i + 1))
    _def("s_trex_tail%d" % (_i + 1), _g, _tr, 130, "T. rex tail, piece %d (lead: that tail segment): heavy counterweight tapering to a point, spine bumps." % (_i + 1),
         extra=[(0, _a[1] + _r0 + 0.25, _a[2]), (_r0 + 0.1, _a[1], _a[2] - _r0 - 0.2), (0, _b[1] - _r1 - 0.1, _b[2] + 0.2)])(
        lambda a=_a, b=_b, r0=_r0, r1=_r1: _tail(a, b, r0, r1, 3))
