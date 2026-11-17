"""Summon set: the wizard hero sculpt (floor-length robe, mantle and sash, bell sleeves, crooked hat, long beard,
gnarled staff).

Modelled in model space on refs.json "sig:wizard" (+Y up, -Z front, studs). The robe hides the legs (they are its
members), the head stays the person head, the hands stay their own skin-coloured parts. Each piece is a "unit"
sculpt in the frame of one lead primitive. Assigned in Signatures/Heroes.luau.
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from . import piece
from .refs import Group
from .s_knight import _def, _ext

W = "sig:wizard"

GR = Group(W, "Robe", ["Pelvis"])


@_def("s_wizard_robe", GR, 1700, 170, "Wizard robe skirt (lead Robe; members Pelvis, legs, feet): floor-length bell with deep folds, trimmed hem, front seam, "
      "curled shoe tips.", extra=_ext((-2.05, 0.0, -1.95), (2.05, 4.5, 1.75)))
def robe():
    zc = 0.08

    def f(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2] - zc
        t = np.clip((4.3 - y) / 4.2, 0.0, 1.0)
        th = np.arctan2(z, x)
        fold = 1 + 0.075 * t ** 1.3 * np.cos(9 * th) + 0.03 * t * np.cos(4 * th + 1.0)
        rx = (1.22 + 0.58 * t ** 0.85) * fold
        rz = (0.84 + 0.56 * t ** 0.85) * fold
        d = (np.hypot(x / rx, z / rz) - 1.0) * 0.85
        hem = np.abs(y - 0.3) - 0.2
        trim = np.maximum((np.hypot(x / (rx + 0.06), z / (rz + 0.06)) - 1.0) * 0.85, hem)
        return np.maximum(np.minimum(d, trim), np.maximum(0.1 - y, y - 4.3))
    s = SDF(f).su(ellipsoid(1.22, 0.3, 0.86, (0, 4.2, zc)), 0.1)
    s = s.ss(capsule((0, 3.9, -0.9), (0, 0.3, -1.5), 0.05), 0.04)
    shoe = ellipsoid(0.3, 0.2, 0.5, (0.5, 0.2, -1.3)).su(tube([(0.5, 0.2, -1.7), (0.5, 0.3, -1.95), (0.5, 0.52, -1.92)], [0.14, 0.09, 0.05], k=0.05), 0.06)
    s = s.su(shoe.mirror_x(), 0.03)
    return SDF(lambda p: np.maximum(s(p), 0.012 - p[:, 1]))


GT = Group(W, "Torso", ["Belt"])


@_def("s_wizard_top", GT, 1100, 160, "Wizard robe top (lead Torso, member Belt): shoulder mantle with a scalloped edge, standing collar, front trim, knotted sash.",
      extra=_ext((-1.7, 3.3, -1.25), (1.7, 7.5, 1.15)))
def top():
    s = GT.sdf("Torso")

    def mantle(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        th = np.arctan2(z, x)
        edge = 5.75 + 0.12 * np.cos(8 * th)
        r = np.hypot(x / 1.55, z / 1.05)
        d = (r - (1.0 - 0.42 * np.clip((y - edge) / 1.1, 0, 1) ** 1.5)) * 0.9
        return np.maximum(d, np.maximum(edge - y, y - 6.9))
    s = s.su(SDF(mantle), 0.06)
    s = s.su(ellipsoid(0.8, 0.5, 0.36, (0, 6.85, 0.5)), 0.12)                          # standing collar
    s = s.su(capsule((0.5, 6.55, -0.72), (0.0, 5.0, -0.92), 0.08).mirror_x(), 0.05)    # front trim
    s = s.su(ellipsoid(1.33, 0.27, 0.9, (0, 4.02, 0.0)), 0.04)                         # sash
    s = s.su(sphere(0.2, (0.32, 3.98, -0.86)), 0.05)
    s = s.su(round_cone((0.32, 3.95, -0.88), (0.42, 3.42, -0.96), 0.13, 0.08), 0.04)
    s = s.su(round_cone((0.3, 3.95, -0.88), (0.18, 3.52, -0.98), 0.12, 0.07), 0.04)
    return s


GS, GCf = Group(W, "limb10"), Group(W, "limb12")


@_def("s_wizard_sleeve", GS, 350, 120, "Wizard sleeve, upper (lead: arm limb): loose cloth with two folds.", extra=_ext((0.75, 3.9, -0.95), (2.75, 6.95, 0.6)), mirror=True)
def sleeve():
    a, b = (1.26, 6.45, 0.05), (2.15, 4.42, -0.37)
    s = round_cone(a, b, 0.45, 0.52).su(sphere(0.5, a), 0.1)
    for u in (0.4, 0.75):
        c = np.array(a) * (1 - u) + np.array(b) * u
        s = s.su(sphere(0.5 + 0.05 * u, tuple(c)), 0.12)
    return s


@_def("s_wizard_cuff", GCf, 500, 140, "Wizard bell sleeve (lead: forearm limb): flares to a wide open cuff the hand comes out of, hanging drape.",
      extra=_ext((1.3, 2.45, -1.5), (2.95, 5.0, 0.2)), mirror=True)
def cuff():
    s = round_cone((2.07, 4.65, -0.32), (2.13, 3.3, -0.67), 0.44, 0.74)
    s = s.su(ellipsoid(0.5, 0.5, 0.42, (2.12, 3.1, -0.45)), 0.2)                       # drape under the wrist
    s = s.ss(round_cone((2.13, 3.6, -0.6), (2.15, 2.6, -0.86), 0.34, 0.66), 0.06)      # open mouth
    return s


GH = Group(W, "HatBrim", ["HatBase", "HatMid", "HatTip"])


@_def("s_wizard_hat", GH, 1300, 170, "Wizard hat (lead HatBrim; members HatBase, HatMid, HatTip): wide wavy brim, tall crooked cone with creases, bent tip.",
      extra=_ext((-2.2, 8.2, -2.2), (2.2, 12.95, 2.2)))
def hat():
    def brim(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        r = np.hypot(x, z)
        th = np.arctan2(z, x)
        surf = 8.86 - 0.3 * (r / 2.0) ** 2 + 0.13 * (r / 2.0) * np.cos(3 * th + 0.5)
        return np.maximum(np.abs(y - surf) * 0.9 - 0.075, r - 2.0)
    s = SDF(brim)
    cone = tube([(0, 8.9, 0.05), (0, 9.9, 0.1), (0, 10.85, 0.28), (0.04, 11.7, 0.58), (0.1, 12.32, 1.02), (0.14, 12.62, 1.5)], [1.12, 0.98, 0.74, 0.46, 0.26, 0.09], k=0.25)
    s = s.su(cone, 0.12)
    s = s.su(ellipsoid(0.62, 0.17, 0.6, (0.03, 11.25, 0.42)), 0.1)                     # creases where the cone folds
    s = s.su(ellipsoid(0.36, 0.13, 0.36, (0.09, 12.1, 0.86)), 0.07)
    return s


GBe = Group(W, "Beard")


@_def("s_wizard_beard", GBe, 700, 150, "Wizard beard (lead Beard): sweeping moustache, full beard combed into three long locks to the belt, sideburns.",
      extra=_ext((-1.2, 5.0, -1.4), (1.2, 7.95, 0.0)))
def beard():
    s = ellipsoid(0.82, 0.55, 0.42, (0, 7.05, -0.72))
    s = s.su(round_cone((0, 6.9, -0.85), (0, 5.2, -0.72), 0.42, 0.07), 0.15)
    s = s.su(round_cone((0.38, 6.85, -0.72), (0.3, 5.65, -0.62), 0.3, 0.06).mirror_x(), 0.1)
    s = s.su(round_cone((0.82, 7.2, -0.45), (0.98, 7.75, -0.22), 0.22, 0.14).mirror_x(), 0.1)        # sideburns
    m = tube([(0.05, 7.52, -1.08), (0.45, 7.42, -1.06), (0.82, 7.3, -0.95), (1.0, 7.42, -0.85)], [0.17, 0.17, 0.11, 0.05], k=0.05)
    s = s.su(m.mirror_x(), 0.05)
    s = s.ss(capsule((0.2, 6.9, -1.15), (0.14, 5.8, -0.95), 0.035).mirror_x(), 0.05)
    return s


GSt = Group(W, "Staff", ["StaffClaw"])


@_def("s_wizard_staff", GSt, 700, 170, "Wizard staff (lead Staff, members the claws): gnarled, knotted shaft, three root prongs cradling the gem, iron ferrule.",
      extra=_ext((1.45, 0.85, -1.4), (2.85, 8.1, -0.05)), pad=0.1)
def staff():
    xc, zc = 2.14, -0.73
    pts, rad = [], []
    for i in range(8):
        y = 1.0 + i * 0.84
        pts.append((xc + 0.06 * np.sin(i * 1.7), y, zc + 0.06 * np.cos(i * 2.3)))
        rad.append(0.125 + 0.03 * ((i * 3) % 2) + (0.03 if i == 7 else 0))
    s = tube(pts, rad, k=0.12)
    for (y, a) in [(2.4, 0.5), (4.6, 2.6), (5.9, 4.4)]:
        s = s.su(sphere(0.12, (xc + 0.13 * np.cos(a), y, zc + 0.13 * np.sin(a))), 0.06)   # knots
    s = s.su(ellipsoid(0.17, 0.14, 0.17, (xc, 1.02, zc)), 0.03)                           # ferrule
    for a in (0.3, 2.4, 4.5):
        dx, dz = np.cos(a), np.sin(a)
        s = s.su(tube([(xc + 0.08 * dx, 6.8, zc + 0.08 * dz), (xc + 0.5 * dx, 7.15, zc + 0.5 * dz), (xc + 0.52 * dx, 7.62, zc + 0.52 * dz),
                       (xc + 0.24 * dx, 7.98, zc + 0.24 * dz)], [0.13, 0.11, 0.08, 0.035], k=0.05), 0.06)
    return s
