"""Summon set: the knight hero sculpt (full plate harness, sword, heater shield, cape, plume).

Modelled in model space on refs.json "sig:knight" (+Y up, -Z front, studs) and cut along the humanoid rig. The
face stays the person head (eyes, nose, mouth are the builder's parts); the helm is an open-faced barbute around
it. Each piece is a "unit" sculpt in the frame of one lead primitive. Assigned in Signatures/Heroes.luau.
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from . import piece
from .refs import Group

W = "sig:knight"


def _def(pid, G, tris, res, note, extra=(), mirror=False, pad=0.25, smooth=3):
    def deco(fn):
        piece(pid, G.region_local(pad, extra), tris=tris, kind="unit", res=res, note=note, mirror=mirror, lead=tuple(G.s), smooth=smooth)(lambda: G.local(fn()))
        return fn
    return deco


def _ext(lo, hi):
    """Region corner points for a model-space box."""
    return [(lo[0], lo[1], lo[2]), (hi[0], hi[1], hi[2]), (lo[0], hi[1], lo[2]), (hi[0], lo[1], hi[2])]


# ------------------------------------------------------------------------------------------------ cuirass, fauld
GC = Group(W, "Torso", ["Belt"])


@_def("s_knight_cuirass", GC, 1400, 160, "Knight cuirass (lead Torso, member Belt): breast and back plate, gorget, plackart lames with rivets, spine ridge.",
      extra=_ext((-1.7, 3.9, -1.2), (1.7, 8.2, 1.2)))
def cuirass():
    s = GC.sdf("Torso")
    s = s.su(ellipsoid(1.0, 0.3, 0.95, (0, 7.72, 0.0)), 0.12)                    # gorget
    s = s.su(ellipsoid(1.08, 0.16, 1.0, (0, 7.5, 0.0)), 0.05)
    s = s.su(ellipsoid(1.55, 0.42, 1.06, (0, 4.95, 0.0)), 0.04)                  # plackart, upper lame
    s = s.su(ellipsoid(1.5, 0.36, 1.03, (0, 4.45, 0.0)), 0.04)                   # lower lame
    for i in range(7):                                                           # rivets round the front
        a = np.radians(-60 + i * 20)
        s = s.su(sphere(0.085, (1.56 * np.sin(a), 5.02, -1.07 * np.cos(a))), 0.02)
    s = s.su(capsule((0, 7.3, 0.92), (0, 5.2, 0.98), 0.1), 0.08)                 # spine ridge
    s = s.su(capsule((0.95, 7.0, -0.62), (0.5, 5.35, -0.92), 0.07).mirror_x(), 0.07)  # pectoral edge
    return s


GF = Group(W, "Pelvis")


@_def("s_knight_fauld", GF, 700, 150, "Knight fauld (lead Pelvis): three flaring lames and two ridged tassets over the thighs.",
      extra=_ext((-1.75, 2.5, -1.25), (1.75, 4.8, 1.25)))
def fauld():
    s = GF.sdf("Pelvis")
    for i, (y, k) in enumerate([(4.35, 1.0), (4.02, 1.05), (3.7, 1.1)]):
        s = s.su(ellipsoid(1.46 * k, 0.27, 1.0 * k, (0, y, 0.03)), 0.03)
    t = round_box(0.45, 0.6, 0.13, 0.1, (0.73, 3.25, -0.82)).su(capsule((0.73, 3.75, -0.94), (0.73, 2.8, -0.94), 0.07), 0.05)
    s = s.su(t.mirror_x(), 0.06)
    return s


# ------------------------------------------------------------------------------------------------ legs
GCu, GGr = Group(W, "limb4"), Group(W, "limb6", ["foot8"])


@_def("s_knight_cuisse", GCu, 450, 130, "Knight thigh armour (lead: hip limb): cuisse with a ridge, poleyn with a side fan.",
      extra=_ext((0.1, 1.3, -0.8), (1.45, 4.8, 0.6)), mirror=True)
def cuisse():
    s = round_cone((0.73, 4.6, 0.0), (0.73, 2.15, -0.12), 0.56, 0.45)
    s = s.su(capsule((0.73, 4.3, -0.5), (0.73, 2.4, -0.55), 0.07), 0.06)
    s = s.su(sphere(0.52, (0.73, 1.85, -0.18)), 0.06)                             # poleyn
    s = s.su(ellipsoid(0.1, 0.34, 0.36, (1.24, 1.85, -0.12)), 0.05)               # fan
    s = s.su(ellipsoid(0.5, 0.12, 0.5, (0.73, 2.25, -0.15)), 0.03)
    return s


@_def("s_knight_greave", GGr, 700, 140, "Knight greave and sabaton (lead: knee limb, member foot): ridged greave, calf, pointed sabaton of lames.",
      extra=_ext((0.15, 0.0, -1.2), (1.3, 2.1, 0.6)), mirror=True)
def greave():
    s = round_cone((0.73, 1.85, -0.14), (0.73, 0.55, 0.0), 0.43, 0.34)
    s = s.su(ellipsoid(0.33, 0.5, 0.3, (0.73, 1.35, 0.18)), 0.12)
    s = s.su(capsule((0.73, 1.75, -0.52), (0.73, 0.6, -0.32), 0.07), 0.05)
    s = s.su(ellipsoid(0.46, 0.27, 0.6, (0.73, 0.29, -0.2)), 0.1)                 # sabaton
    s = s.su(round_cone((0.73, 0.25, -0.6), (0.73, 0.15, -1.06), 0.3, 0.07), 0.08)
    for i, z in enumerate((-0.15, -0.42, -0.68)):
        s = s.su(ellipsoid(0.47 - 0.07 * i, 0.3 - 0.05 * i, 0.06, (0.73, 0.3 - 0.02 * i, z)), 0.02)
    return SDF(lambda p: np.maximum(s(p), 0.012 - p[:, 1]))


# ------------------------------------------------------------------------------------------------ arms
GRe, GVa = Group(W, "limb10"), Group(W, "limb12", ["hand14"])
GPa = Group(W, "PauldronR")


@_def("s_knight_rerebrace", GRe, 350, 120, "Knight upper arm (lead: arm limb): rerebrace and elbow cop with a fan.",
      extra=_ext((1.0, 4.6, -1.1), (3.3, 7.9, 0.6)), mirror=True)
def rerebrace():
    a, b = (1.5, 7.6, 0.05), (2.55, 5.25, -0.43)
    s = round_cone(a, b, 0.5, 0.42)
    s = s.su(sphere(0.5, b), 0.06)
    s = s.su(ellipsoid(0.12, 0.36, 0.36, (3.02, 5.2, -0.4)), 0.05)
    return s


@_def("s_knight_gauntlet", GVa, 600, 140, "Knight forearm and gauntlet (lead: forearm limb, member hand): vambrace, flared cuff, plated fist.",
      extra=_ext((1.85, 2.8, -1.55), (3.2, 5.7, -0.1)), mirror=True)
def gauntlet():
    s = round_cone((2.46, 5.5, -0.38), (2.52, 4.0, -0.77), 0.4, 0.34)
    s = s.su(round_cone((2.52, 4.35, -0.68), (2.53, 3.88, -0.8), 0.36, 0.52), 0.05)       # cuff
    s = s.su(round_box(0.5, 0.42, 0.5, 0.2, (2.53, 3.4, -0.87)), 0.06)                    # fist
    for i in range(4):                                                                     # knuckle plates
        s = s.su(ellipsoid(0.13, 0.14, 0.16, (2.2 + i * 0.22, 3.25, -1.34)), 0.03)
    s = s.su(ellipsoid(0.16, 0.3, 0.2, (2.0, 3.45, -1.05)), 0.05)                         # thumb
    return s


@_def("s_knight_pauldron", GPa, 450, 130, "Knight pauldron (lead Pauldron): three overlapping lames and an upstanding neck guard.",
      extra=_ext((0.7, 6.5, -1.0), (3.05, 8.6, 1.0)), mirror=True)
def pauldron():
    s = ellipsoid(0.98, 0.52, 0.92, (1.55, 7.62, 0.0))
    s = s.su(ellipsoid(0.8, 0.42, 0.86, (2.02, 7.3, -0.02)), 0.03)
    s = s.su(ellipsoid(0.62, 0.36, 0.76, (2.34, 6.98, -0.05)), 0.03)
    s = s.su(ellipsoid(0.1, 0.42, 0.62, (0.98, 8.05, 0.0)), 0.06)
    for z in (-0.6, 0.6):
        s = s.su(sphere(0.08, (1.75, 8.02, z * 0.9)), 0.02)
    return s


# ------------------------------------------------------------------------------------------------ helm, plume
GHe = Group(W, "Helmet", ["Visor"])


@_def("s_knight_helm", GHe, 1400, 170, "Knight helm (lead Helmet, member Visor): open-faced barbute with a rimmed face opening, comb, raised slotted visor, "
      "pivot studs, flared neck guard.", extra=_ext((-1.85, 8.0, -1.95), (1.85, 11.75, 2.0)))
def helm():
    outer = ellipsoid(1.63, 1.74, 1.62, (0, 9.5, 0.05))
    opening = round_box(0.98, 1.0, 1.3, 0.35, (0, 9.05, -1.6))
    s = outer.ss(opening, 0.05)
    rim = ellipsoid(1.71, 1.82, 1.7, (0, 9.5, 0.05)).si(round_box(1.14, 1.16, 1.3, 0.42, (0, 9.05, -1.6)), 0.03).ss(opening, 0.03)
    s = s.su(rim, 0.03)
    s = s.su(ellipsoid(1.5, 0.45, 1.05, (0, 8.55, 0.85)), 0.2)                             # neck guard
    s = SDF(lambda p, s=s: np.maximum(s(p), 8.05 - p[:, 1]))
    comb = ellipsoid(0.5, 1.98, 1.84, (0, 9.5, 0.1)).si(box(0.075, 50, 50), 0.04)
    comb = SDF(lambda p, c=comb: np.maximum(c(p), 10.3 - p[:, 1]))
    s = s.su(comb, 0.06)
    visor = ellipsoid(1.73, 1.84, 1.72, (0, 9.5, 0.05)).si(round_box(1.3, 0.42, 0.8, 0.12, (0, 10.52, -1.25)), 0.04)
    for y in (10.42, 10.62):
        visor = visor.ss(capsule((0.25, y, -1.75), (0.95, y, -1.45), 0.045).mirror_x(), 0.02)
    s = s.su(visor, 0.03)
    s = s.su(sphere(0.17, (1.6, 10.05, -0.25)).mirror_x(), 0.04)                           # pivot studs
    return s


GPl = Group(W, "Plume", ["Plume_2"])


@_def("s_knight_plume", GPl, 450, 140, "Helm plume (lead Plume, member its second lock): a full feather crest sweeping up and back.",
      extra=_ext((-0.55, 10.4, -0.6), (0.55, 13.0, 3.4)))
def plume():
    s = tube([(0, 10.75, -0.25), (0, 11.55, 0.3), (0, 12.3, 1.3), (0, 12.25, 2.4), (0, 11.65, 3.1)], [0.3, 0.44, 0.46, 0.36, 0.12], k=0.2)
    for (y, z, dy, dz, r) in [(12.0, 0.6, 0.45, 0.3, 0.26), (12.55, 1.5, 0.3, 0.5, 0.26), (12.4, 2.4, 0.1, 0.55, 0.22), (11.6, 1.6, -0.4, 0.5, 0.24), (11.2, 0.9, -0.3, 0.45, 0.22)]:
        s = s.su(round_cone((0, y, z), (0, y + dy, z + dz), r, 0.08), 0.1)
    return s.si(ellipsoid(0.36, 3.0, 3.5, (0, 11.6, 1.4)), 0.08)


# ------------------------------------------------------------------------------------------------ sword, shield, cape
GBl = Group(W, "Blade", ["BladeTip", "Guard", "Grip"])


@_def("s_sword", GBl, 520, 170, "Arming sword in one piece (lead Blade; members BladeTip, Guard, Grip): fullered diamond blade tapering to the point, "
      "down-swept quillons with ball ends, wrapped grip, round pommel.", extra=_ext((1.75, 2.7, -1.1), (3.3, 8.15, -0.64)), pad=0.08, smooth=1)
def sword():
    xc, zc = 2.53, -0.87

    def f(p):
        y = p[:, 1]
        w = 0.26 * np.clip((8.08 - y) / 0.8, 0.0, 1.0) + 1e-3
        d = (np.abs(p[:, 0] - xc) / w + np.abs(p[:, 2] - zc) / 0.075 - 1.0) * 0.06
        return np.maximum(np.maximum(d, 4.1 - y), y - 8.08)
    s = SDF(f)
    s = s.ss(capsule((xc, 4.45, zc - 0.085), (xc, 7.1, zc - 0.085), 0.04), 0.01).ss(capsule((xc, 4.45, zc + 0.085), (xc, 7.1, zc + 0.085), 0.04), 0.01)
    g = ellipsoid(0.22, 0.15, 0.17, (xc, 4.11, zc))
    for sx in (-1, 1):
        g = g.su(capsule((xc, 4.12, zc), (xc + sx * 0.59, 4.04, zc), 0.09), 0.04).su(sphere(0.13, (xc + sx * 0.61, 4.03, zc)), 0.03)
    h = capsule((xc, 3.15, zc), (xc, 4.0, zc), 0.11)
    for i in range(4):
        h = h.su(ellipsoid(0.135, 0.05, 0.135, (xc, 3.3 + i * 0.2, zc)), 0.02)
    h = h.su(sphere(0.2, (xc, 2.98, zc)), 0.04)
    return s.su(g, 0.02).su(h, 0.02)


GCr = Group(W, "CrossV", ["CrossH"])


@_def("s_knight_cross", GCr, 120, 110, "Heraldic cross on the breastplate (lead CrossV, member CrossH): one raised cross with flared ends.",
      extra=_ext((-0.55, 5.5, -1.1), (0.55, 6.95, -0.9)), pad=0.05, smooth=1)
def cross():
    zc = -0.99
    v = round_box(0.12, 0.63, 0.075, 0.03, (0, 6.22, zc))
    h = round_box(0.455, 0.14, 0.075, 0.03, (0, 6.45, zc))
    s = v.su(h, 0.02)
    for (x, y) in [(0, 6.82), (0, 5.62), (0.43, 6.45), (-0.43, 6.45)]:
        s = s.su(round_box(0.17 if x == 0 else 0.06, 0.06 if x == 0 else 0.2, 0.075, 0.03, (x, y, zc)), 0.02)
    return s


GSh = Group(W, "Shield", ["Boss"])


@_def("s_knight_shield", GSh, 500, 160, "Heater shield (lead Shield, member Boss): pointed heater outline, raised rim, boss and an embossed cross on the face.",
      extra=_ext((-3.2, 2.6, -2.4), (-2.6, 5.6, 0.35)), pad=0.1, smooth=2)
def shield():
    x0, z0 = -2.81, -1.03

    def outline(p):
        y, z = p[:, 1], p[:, 2]
        a = np.hypot(z - (z0 + 1.0), y - 4.95) - 2.3
        b = np.hypot(z - (z0 - 1.0), y - 4.95) - 2.3
        return np.maximum(np.maximum(a, b), y - 5.4)

    def f(p):
        d = outline(p)
        x = p[:, 0] - x0 + 0.1 * ((p[:, 2] - z0) / 1.3) ** 2            # gently bowed round the arm
        body = np.maximum(d, np.abs(x) - 0.1)
        rim = np.maximum(np.abs(d + 0.1) - 0.08, np.abs(x) - 0.16)
        bar = np.minimum(np.abs(p[:, 2] - z0), np.abs(p[:, 1] - 4.5)) - 0.12
        cross = np.maximum(np.maximum(d + 0.3, bar), np.abs(x + 0.1) - 0.05)
        return np.minimum(np.minimum(body, rim), cross)
    return SDF(f).su(sphere(0.34, (x0 - 0.08, 4.5, z0)), 0.03)


GCa = Group(W, "Cape", ["CapeLow"])


@_def("s_cape", GCa, 500, 170, "Cape of Props.cape, any caped summon (lead Cape, member CapeLow): cloth hanging from the shoulders, widening to a scalloped hem, deep vertical folds.",
      extra=_ext((-1.9, 3.8, 0.85), (1.9, 7.95, 2.0)), pad=0.1, smooth=2)
def cape():
    def f(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        t = np.clip((7.8 - y) / 3.7, 0.0, 1.0)                           # 0 at the shoulders, 1 at the hem
        surf = 1.12 + 0.5 * t + 0.13 * t * np.cos(x * 5.2) - 0.25 * (x / 1.7) ** 2
        d = np.abs(z - surf) - 0.055
        half = 1.42 + 0.25 * t
        hem = 4.1 + 0.1 * np.cos(x * 5.2)
        return np.maximum(np.maximum(d * 0.7, np.abs(x) - half), np.maximum(hem - y, y - 7.8))
    return SDF(f)
