"""Dragons, the signature summon and mount of Typing Wizards: western dragon (saddled mount), elder dragon (wild,
crowned, ragged wings), drake (wingless), wyvern (wing-arms, two legs), baby dragon and fairy dragon.

One parametric sculpt (`_dragon`): a deep-chested torso with shoulder and haunch masses, overlapping belly plates
in the belly colour, dorsal blade spines (darkened by a mask, not a separate part), an S-curved two-bone neck, a
long wedge-snouted head with brow ridges, nostrils, cheek frills, swept horns (horn colour), upper and lower teeth
and a jaw that opens; three-segment legs with taloned feet; big bat wings (arm + finger bones, a billowing,
scalloped membrane in the membrane colour, a thumb claw) on two bones per side so the hand lags the flap; a
four-bone tail ending in a spade. Motion: motion_mythic.flyer (flying Move with a powerful flap, rear-and-breathe
Attack) or motion.quadruped for the wingless drake.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from kit import Hero, hero, stripes, combine
from map import NOTFOOD
import motion
import motion_mythic as mm
from mythic_geo import (V, nrm, tri, fan, membrane, scallop, union_hard, bounded, frame, oell, squash, flat_tube, spike,
                        curved_horn, blade_fin, surface_y, bez, outside, band_y, feather)

BASE = dict(
    s=1.0, body=1.0, girth=1.0, leg=1.0, neck=1.0, head=1.0, tail=1.0,
    wings="bat",        # "bat" | "none" | "butterfly" | "ragged"
    wing=1.0,           # wing span factor
    legs4=True,         # False: wyvern (the wings are the arms)
    saddle=False,
    horns="classic",    # "classic" | "crown" | "nub" | "antler"
    spines=1.0,         # dorsal spine height factor (0 = none)
    cute=0.0,           # 0..1: big head, big round eyes, stubby limbs
    snout=1.0,
    eye=1.0,
    frill=1.0,
    spade=True,
    stinger=False,
    belly=True,
    preview={},
)


def _dragon(hid, **kw):
    P = dict(BASE)
    P.update(kw)
    s, BL, G, LG, CU = P["s"], P["body"], P["girth"], P["leg"], P["cute"]
    H = Hero(hid, plan="Quadruped", gait="fly" if P["wings"] != "none" else "heavy", tags=["dragon", "reptile"])
    H.preview = P["preview"]

    def v(x, y, z):
        return V(x * s, y * s, z * s)

    biped = not P["legs4"]
    bodyY = (2.95 * LG if not biped else 3.5 * LG) - 0.75 * CU
    H.body(v(0, bodyY, 0))
    zc, zr = -1.15 * BL, 1.55 * BL           # chest / hips
    tilt = 0.32 if biped else 0.0          # wyvern torso pitches nose-up

    def T(x, y, z):
        """Torso-space point (pitched for the wyvern about the hips)."""
        if not tilt:
            return v(x, y, z)
        dy, dz = y - bodyY, z - zr
        c, sn = math.cos(tilt), math.sin(tilt)
        return v(x, bodyY + dy * c - dz * sn, zr + dy * sn + dz * c)

    # ------------------------------------------------------------------ torso
    core = ellipsoid(1.0 * G * s, 1.02 * G * s, 1.45 * BL * s, T(0, bodyY + 0.12, zc + 0.2))                      # ribcage
    core = core.su(ellipsoid(0.82 * G * s, 0.86 * G * s, 1.25 * BL * s, T(0, bodyY - 0.02, 0.55 * BL)), 0.5)      # waist
    core = core.su(ellipsoid(0.92 * G * s, 0.92 * G * s, 1.0 * BL * s, T(0, bodyY + 0.12, zr)), 0.45)             # hips
    core = core.su(ellipsoid(0.42 * G * s, 0.55 * s, 0.7 * s, T(0.62 * G, bodyY + 0.55, zc - 0.1)).mirror_x(), 0.3)  # wing / shoulder muscle
    core = core.su(ellipsoid(0.45 * G * s, 0.75 * s, 0.85 * s, T(0.62 * G, bodyY + 0.05, zr + 0.05)).mirror_x(), 0.3)  # haunch
    core = core.su(ellipsoid(0.75 * G * s, 0.75 * G * s, 0.75 * s, T(0, bodyY - 0.35, zc - 0.55)), 0.4)           # breast
    nb0, nb1 = T(0, bodyY + 0.35, zc - 0.85), T(0, bodyY + 0.95, zc - 1.55)
    core = core.su(round_cone(nb0, nb1, 0.78 * G * s, 0.6 * s), 0.4)                                              # neck root
    tb0, tb1 = T(0, bodyY + 0.15, zr + 0.8), T(0, bodyY - 0.05, zr + 1.6)
    core = core.su(round_cone(tb0, tb1, 0.72 * G * s, 0.58 * s), 0.35)                                            # tail root

    sp = P["spines"]
    spines = []
    saddle_z = (zc + 0.55 * BL)
    if sp > 0:
        zs = np.linspace(zc - 1.0, zr + 1.4, 11)
        for i, z in enumerate(zs):
            if P["saddle"] and abs(z - saddle_z) < 1.05:
                continue
            y = surface_y(core, 0.0, z * s, (bodyY + 2.5) * s, (bodyY - 1) * s) / s
            h = (0.42 + 0.12 * math.sin(i * 0.9)) * sp * (1 - 0.3 * CU)
            spines.append(blade_fin(V(0, y - 0.12, z) * s, (0, 1, 0.45), h * s, 0.16 * s, (1, 0, 0), flat=0.32, back=(0, 0, 1)))
    torso = core
    for f in spines:
        torso = torso.su(f, 0.06)
    pat_body = combine(band_y((bodyY - 0.9) * s, (bodyY + 1.0) * s, 1.0, 0.82), outside(core, 0.05, 0.45, 0.12))
    H.piece("Torso", "Body", torso, col="primary", tris=2300, res=136, pattern=pat_body)

    if P["belly"]:
        pa, pb = T(0, bodyY + 0.45, zc - 1.45), T(0, bodyY - 0.55, zr + 0.2)
        dd = nrm(pb - pa)
        nup = nrm(V(0, dd[2], -dd[1]))
        if nup[1] < 0:
            nup = -nup
        bel = core.round(0.045 * s) & plane(nup, float(nup @ pa)) & plane((1, 0, 0), 0.62 * G * s) & plane((-1, 0, 0), 0.62 * G * s)
        H.piece("Belly", "Body", bel, col="belly", tris=900, res=120, role="body",
                pattern=stripes(lambda Q: Q[:, 2] / s, 2.6, width=0.18, depth=0.3))

    # ------------------------------------------------------------------ saddle
    if P["saddle"]:
        zs0 = saddle_z
        top = surface_y(core, 0.0, zs0 * s, (bodyY + 2.5) * s, bodyY * s) / s
        sad_box = box(0.95 * G * s, 0.75 * s, 0.75 * s, v(0, top - 0.35, zs0))
        cloth = core.round(0.07 * s) & sad_box
        cloth = cloth.su(core.round(0.06 * s) & box(1.4 * s, 1.6 * s, 0.12 * s, v(0, bodyY, zs0 + 0.35)), 0.02)   # girth strap
        H.piece("SaddleCloth", "Body", cloth, col="secondary", mat="cloth", tris=700, res=120, role="detail", pri=1.3)
        seat = core.round(0.18 * s) & box(0.5 * G * s, 0.5 * s, 0.52 * s, v(0, top - 0.1, zs0))
        seat = seat.su(ellipsoid(0.24 * s, 0.24 * s, 0.14 * s, v(0, top + 0.2, zs0 - 0.48)), 0.08)                 # pommel
        seat = seat.su(ellipsoid(0.42 * s, 0.2 * s, 0.13 * s, v(0, top + 0.18, zs0 + 0.5)), 0.08)                  # cantle
        seat = seat.su(capsule(v(0.52 * G, top - 0.35, zs0 + 0.05), v(0.56 * G, top - 0.95, zs0 + 0.05), 0.05 * s).mirror_x(), 0.02)  # stirrup straps
        seat = seat.su(torus(0.11 * s, 0.035 * s, axis=2).at(*v(0.58 * G, top - 1.05, zs0 + 0.05)).mirror_x(), 0.02)                  # stirrups
        H.piece("Saddle", "Body", seat, col="leather", mat="cloth", tris=800, res=128, role="detail", pri=1.2)
        sy = top + 0.22
        H.socket("seat", v(0, sy, zs0), "Body")
        H.mount = {"seat": "Torso", "saddle": {"pos": tuple(v(0, sy, zs0)), "size": tuple(v(0.9 * G, 0.25, 1.05))}}

    # ------------------------------------------------------------------ legs
    legs = []
    claw_dark = 0.32

    def foot(c, fwd, toes=3, toe_len=0.55, r=0.13, back=True):
        """Taloned foot centred at c (ground level), toes along fwd (horizontal)."""
        c = V(c)
        fwd = nrm(fwd)
        side = nrm(np.cross((0, 1, 0), fwd))
        k = s * (1.3 + 0.3 * CU)
        palm = oell(c + V(0, 0.2, 0) * k, frame(fwd), (0.32 * k, 0.24 * k, 0.17 * k))
        talons = []
        spread = [-0.35, 0.0, 0.35] if toes == 3 else [-0.45, -0.15, 0.15, 0.45]
        for a in spread:
            d = nrm(fwd * math.cos(a) + side * math.sin(a))
            p0 = c + V(0, 0.2, 0) * k + d * 0.12 * k
            p1 = c + V(0, 0.12, 0) * k + d * (0.12 + toe_len * 0.6) * k
            p2 = c + V(0, 0.1, 0) * k + d * (0.12 + toe_len) * k
            palm = palm.su(tube([p0, p1, p2], [r * k, r * 0.85 * k, r * 0.7 * k]), 0.05 * k)
            tal = curved_horn([p2 - d * 0.03 * k, p2 + d * 0.16 * k + V(0, 0.0, 0) * k, p2 + d * 0.26 * k - V(0, 0.11, 0) * k], 0.075 * k, 0.012 * k)
            talons.append(tal)
        if back:
            p0 = c + V(0, 0.22, 0) * k - fwd * 0.15 * k
            p1 = c + V(0, 0.1, 0) * k - fwd * 0.42 * k
            palm = palm.su(round_cone(p0, p1, 0.1 * k, 0.07 * k), 0.04 * k)
            talons.append(curved_horn([p1, p1 - fwd * 0.14 * k, p1 - fwd * 0.2 * k - V(0, 0.08, 0) * k], 0.06 * k, 0.012 * k))
        core_f = palm
        for t_ in talons:
            palm = palm.su(t_, 0.02 * k)
        return palm & plane((0, -1, 0), 0.0), outside(core_f, 0.03 * k, claw_dark, 0.05 * k)

    leg_r = (1 + 0.12 * CU) * (1.18 if biped else 1.0)
    if not biped:
        sh = v(0.78 * G, bodyY + 0.15, zc - 0.25)
        el = v(0.98 * G, bodyY * 0.55, zc + 0.05)
        wr = v(0.92 * G, 0.55 + 0.1 * CU, zc - 0.4)
        H.mbone("ShoulderF#", "Body", tuple(sh))
        H.mbone("ElbowF#", "ShoulderF#", tuple(el))
        H.mbone("WristF#", "ElbowF#", tuple(wr))
        up = round_cone(sh + v(0, 0.25, 0), el, 0.62 * G * s * leg_r, 0.38 * s * leg_r)
        up = up.su(ellipsoid(0.46 * s * leg_r, 0.62 * s * LG, 0.55 * s * leg_r, sh + v(0.05, -0.55 * LG, -0.05)), 0.25)
        H.mpiece("UpperF#", "ShoulderF#", up, col="primary", tris=550, role="limb", pattern=band_y(0, bodyY * s, 1.0, 0.86))
        fo = round_cone(el, wr + v(0, 0.12, 0), 0.4 * s * leg_r, 0.27 * s * leg_r)
        fo = fo.su(ellipsoid(0.34 * s * leg_r, 0.5 * s * LG, 0.38 * s * leg_r, el + v(0.02, -0.4 * LG, -0.1)), 0.15)
        fo = fo.su(spike(el + v(0, 0.05, 0.2), (0.2, 0.3, 1), 0.3 * s, 0.09 * s), 0.05)        # elbow spur
        H.mpiece("ForeF#", "ElbowF#", fo, col="primary", tris=500, role="limb")
        fshape, fpat = foot(v(0.92 * G, 0.0, zc - 0.55), (0.12, 0, -1), toes=3)
        fshape = fshape.su(round_cone(wr + v(0, 0.08, 0), v(0.92 * G, 0.3, zc - 0.55), 0.27 * s * leg_r, 0.28 * s * leg_r), 0.08)
        H.mpiece("FootF#", "WristF#", fshape, col="primary", tris=520, role="foot", pattern=fpat)
        legs += [("ShoulderFR", "ElbowFR", "WristFR", True, 1), ("ShoulderFL", "ElbowFL", "WristFL", True, -1)]

    hp = T(0.82 * G, bodyY + 0.05, zr + 0.05)
    kn = v(1.0 * G, bodyY * 0.6, zr - 0.6)
    hk = v(0.95 * G, (0.95 + 0.15 * CU) * LG, zr + 0.45)
    ftc = v(0.95 * G, 0.0, zr - 0.1)
    if biped:
        kn = v(0.95 * G, bodyY * 0.58, zr - 0.75)
        hk = v(0.9 * G, 1.0 * LG, zr + 0.35)
        ftc = v(0.9 * G, 0.0, zr - 0.35)
    H.mbone("Hip#", "Body", tuple(hp))
    H.mbone("Knee#", "Hip#", tuple(kn))
    H.mbone("Hock#", "Knee#", tuple(hk))
    th = round_cone(hp + v(0, 0.3, 0.1), kn, 0.76 * G * s * leg_r, 0.42 * s * leg_r)
    th = th.su(ellipsoid(0.56 * G * s * leg_r, 0.9 * s, 0.88 * s * leg_r, hp + v(0.06, -0.45, -0.05)), 0.3)
    H.mpiece("Thigh#", "Hip#", th, col="primary", tris=650, role="limb", pattern=band_y(0, bodyY * s, 1.0, 0.86))
    sn = round_cone(kn, hk, 0.42 * s * leg_r, 0.26 * s * leg_r)
    sn = sn.su(ellipsoid(0.34 * s * leg_r, 0.45 * s, 0.38 * s * leg_r, kn + v(0, -0.3, 0.25)), 0.15)
    H.mpiece("Shin#", "Knee#", sn, col="primary", tris=500, role="limb")
    fshape, fpat = foot(ftc, (0.1, 0, -1), toes=3)
    fshape = fshape.su(round_cone(hk, ftc + v(0, 0.28, 0.1), 0.26 * s * leg_r, 0.27 * s * leg_r), 0.08)
    fshape = fshape.su(spike(hk + v(0, 0.0, 0.05), (0, 0.2, 1), 0.25 * s, 0.08 * s), 0.04)     # hock spur
    H.mpiece("FootB#", "Hock#", fshape, col="primary", tris=520, role="foot", pattern=fpat)
    legs += [("HipR", "KneeR", "HockR", False, 1), ("HipL", "KneeL", "HockL", False, -1)]

    # ------------------------------------------------------------------ neck + head
    NK = P["neck"]
    n0 = T(0, bodyY + 0.5, zc - 1.1)
    n1 = n0 + v(0, 1.05, -0.75) * NK
    n2 = n1 + v(0, 0.95, -0.45) * NK
    hc = n2 + v(0, 0.2, -0.3) * NK
    if CU:
        hc = n0 + v(0, 1.25, -0.6)
        n1 = n0 + v(0, 0.55, -0.3)
        n2 = n1 + v(0, 0.45, -0.15)
    H.bone("Neck1", "Body", tuple(n0))
    H.bone("Neck2", "Neck1", tuple(n1))
    H.bone("Head", "Neck2", tuple(hc))
    nr = (0.72 if not CU else 0.55) * G
    ncore1 = tube([n0 + v(0, -0.15, 0.25), n0 + (n1 - n0) * 0.55 + v(0, 0, 0.05), n1 + (n2 - n1) * 0.15], [nr * 1.12 * s, nr * 0.95 * s, nr * 0.82 * s], k=0.1)
    ncore2 = tube([n1 - (n1 - n0) * 0.12, n1 + (n2 - n1) * 0.55, hc + v(0, -0.05, 0.12)], [nr * 0.84 * s, nr * 0.74 * s, nr * 0.66 * s], k=0.1)

    def neck_spines(a, b, nspine, rr):
        out = []
        d = nrm(b - a)
        back = nrm(np.cross(d, (1, 0, 0)))   # perpendicular, pointing up/back
        if back[1] < 0:
            back = -back
        for i in range(nspine):
            u = (i + 0.5) / nspine
            base = a + (b - a) * u + back * (rr * s - 0.12 * s)
            out.append(blade_fin(base, back + 0.0 * d, 0.32 * sp * s * (1 - 0.3 * CU), 0.13 * s, (1, 0, 0), flat=0.32, back=-d))
        return out

    neck1 = ncore1
    neck2 = ncore2
    if sp > 0:
        for f in neck_spines(n0 + v(0, 0.1, 0.1), n1, 3, nr * 0.95):
            neck1 = neck1.su(f, 0.05)
        for f in neck_spines(n1, hc, 3, nr * 0.75):
            neck2 = neck2.su(f, 0.05)
    npat = band_y((n0[1] - 1.0 * s), (hc[1] + 0.6 * s), 1.0, 0.86)
    H.piece("NeckA", "Neck1", neck1, col="primary", tris=750, role="limb", pattern=combine(npat, outside(ncore1, 0.05, 0.45, 0.1)))
    H.piece("NeckB", "Neck2", neck2, col="primary", tris=700, role="limb", pattern=combine(npat, outside(ncore2, 0.05, 0.45, 0.1)))

    hs = s * 1.38 * P["head"] * (1 + 0.6 * CU)
    SN = P["snout"] * (1 - 0.45 * CU)

    def h(x, y, z):
        return hc + V(x, y, z) * hs

    head = ellipsoid(0.43 * hs, 0.4 * hs, 0.5 * hs, h(0, 0.12, -0.3))                                                 # cranium
    if CU:
        head = ellipsoid(0.52 * hs, 0.5 * hs, 0.5 * hs, h(0, 0.18, -0.3))
    snout = tube([h(0, 0.06, -0.55), h(0, 0.0, -0.55 - 0.55 * SN), h(0, -0.04, -0.55 - 1.0 * SN)], [0.33 * hs, 0.27 * hs, 0.2 * hs], k=0.08)
    snout = squash(snout, h(0, 0, -1.0), (1, 0, 0), 1.0)
    head = head.su(snout, 0.18)
    head = head.su(ellipsoid(0.3 * hs, 0.25 * hs, 0.32 * hs, h(0.24, -0.02, -0.42)).mirror_x(), 0.15)                 # cheeks
    head = head.su(capsule(h(0.2, 0.32, -0.72), h(0.32, 0.4, -0.3), 0.1 * hs).mirror_x(), 0.1)                        # brow ridges
    head = head.su(sphere(0.1 * hs, h(0.12, 0.08, -0.5 - 1.0 * SN)).mirror_x(), 0.07)                                  # nostril bumps
    head = head.ss(sphere(0.045 * hs, h(0.13, 0.1, -0.59 - 1.0 * SN)).mirror_x(), 0.02)                                # nostrils
    head = head.ss(sphere(0.12 * hs, h(0.28, 0.2, -0.66)).mirror_x(), 0.05)                                            # eye sockets
    if P["frill"] > 0 and not CU:
        fr = P["frill"]
        for i, (y, z, ln) in enumerate(((0.05, -0.15, 0.55), (-0.1, -0.05, 0.45), (0.2, -0.05, 0.42))):
            a = h(0.36, y, z)
            head = head.su(blade_fin(a, (0.6, 0.12 * (1 - i), 1.0), ln * fr * hs, 0.08 * hs, (0, 1, 0), flat=0.4), 0.05)
    head = head.si(plane((0, -1, 0), -(hc[1] - 0.16 * hs)), 0.03)                                                       # flat upper lip
    hcore = head
    H.piece("HeadP", "Head", head, col="primary", tris=2100, res=144, role="head",
            pattern=band_y(hc[1] - 0.3 * hs, hc[1] + 0.5 * hs, 1.0, 0.85))

    # horns
    hz = P["horns"]
    horns = []
    if hz in ("classic", "crown"):
        horns.append(curved_horn([h(0.2, 0.35, -0.3), h(0.32, 0.55, 0.1), h(0.38, 0.62, 0.55), h(0.33, 0.85, 1.0)], 0.13 * hs, 0.015 * hs))
        horns.append(curved_horn([h(0.36, 0.1, -0.15), h(0.58, 0.05, 0.2), h(0.72, 0.12, 0.55)], 0.08 * hs, 0.012 * hs))
        horns.append(spike(h(0.0, 0.18, -0.4 - 0.75 * SN), (0, 1, 0.4), 0.18 * hs, 0.06 * hs))
    if hz == "crown":
        horns.append(curved_horn([h(0.1, 0.4, -0.12), h(0.12, 0.75, 0.15), h(0.08, 1.05, 0.5)], 0.09 * hs, 0.012 * hs))
        horns.append(curved_horn([h(0.42, 0.3, -0.05), h(0.75, 0.45, 0.15), h(0.95, 0.65, 0.35)], 0.09 * hs, 0.012 * hs))
        horns.append(spike(h(0.0, 0.22, -0.4 - 0.45 * SN), (0, 1, 0.3), 0.14 * hs, 0.05 * hs))
    if hz == "nub":
        horns.append(curved_horn([h(0.2, 0.42, -0.25), h(0.27, 0.62, -0.05), h(0.3, 0.72, 0.12)], 0.11 * hs, 0.04 * hs))
    hshape = union_hard([x.mirror_x() if i != 2 and i != 5 else x for i, x in enumerate(horns)])
    H.piece("Horns", "Head", hshape, col="horn", mat="hard", tris=1000, res=128, role="horn", pri=1.3)

    # jaw
    jw = h(0, -0.12, -0.15)
    H.bone("Jaw", "Head", tuple(jw))
    jaw = tube([h(0, -0.24, -0.2), h(0, -0.27, -0.6 - 0.4 * SN), h(0, -0.25, -0.45 - 0.95 * SN)], [0.27 * hs, 0.2 * hs, 0.15 * hs], k=0.08)
    jaw = jaw.su(capsule(h(0.25, -0.18, -0.15), h(0.17, -0.24, -0.5 - 0.5 * SN), 0.08 * hs).mirror_x(), 0.08)
    if not CU:
        for i in range(3):
            jaw = jaw.su(spike(h(0.22 - 0.05 * i, -0.3, -0.25 - 0.25 * i), (0.6, -0.7, 0.6), (0.28 - 0.05 * i) * hs, 0.06 * hs).mirror_x(), 0.04)
    jaw = jaw.si(plane((0, 1, 0), hc[1] - 0.17 * hs), 0.03)
    H.piece("JawP", "Jaw", jaw, col="primary", tris=900, role="jaw", pri=1.3, pattern=band_y(hc[1] - 0.4 * hs, hc[1] - 0.15 * hs, 1.08, 0.9))
    H.prim("Mouth", "Head", "Ellipsoid", (0.4 * hs, 0.05 * hs, (0.3 + 0.95 * SN) * hs), h(0, -0.185, -0.25 - 0.5 * SN), col="mouth", mat="hard", role="mouth", pri=2.3)
    H.prim("Tongue", "Jaw", "Ellipsoid", (0.22 * hs, 0.07 * hs, (0.2 + 0.7 * SN) * hs), h(0, -0.2, -0.3 - 0.4 * SN), col="tongue", mat="skin", role="mouth", pri=2.4)
    # teeth: upper on the head, lower on the jaw
    tu, tl = [], []
    nt = 5 if not CU else 2
    for i in range(nt):
        u = (i + 0.5) / nt
        z = -0.5 - u * 0.92 * SN
        wx = (0.24 - 0.09 * u) * (1 + 0.15 * CU)
        ln = (0.13 if i != nt - 2 else 0.22) * (0.8 if CU else 1)
        tu.append(round_cone(h(wx, -0.12, z), h(wx - 0.01, -0.12 - ln, z - 0.01), 0.04 * hs, 0.008 * hs))
        if not CU:
            tl.append(round_cone(h(wx - 0.04, -0.22, z + 0.06), h(wx - 0.05, -0.22 + ln * 0.8, z + 0.05), 0.035 * hs, 0.008 * hs))
    H.piece("TeethU", "Head", union_hard(tu).mirror_x(), col="tooth", mat="hard", tris=420, role="tooth", pri=2.0, ao=False, smooth=2)
    if tl:
        H.piece("TeethL", "Jaw", union_hard(tl).mirror_x(), col="tooth", mat="hard", tris=380, role="tooth", pri=2.1, ao=False, smooth=2)
    er = 0.095 * hs * P["eye"] * (1 + 0.6 * CU)
    H.eyes("Head", h(0.3 if not CU else 0.33, 0.2, -0.66 if not CU else -0.62), er, col="iris", pupil="slit" if not CU else "round", look=(0.55, 0.05, -1.0))

    # ------------------------------------------------------------------ tail
    TL = P["tail"] * (1 - 0.35 * CU)
    t0 = T(0, bodyY + 0.05, zr + 1.0)
    t1 = t0 + v(0, -0.35, 1.55) * TL
    t2 = t1 + v(0, -0.55, 1.45) * TL
    t3 = t2 + v(0, -0.6, 1.3) * TL
    t4 = t3 + v(0, -0.45, 1.15) * TL
    if biped:
        t1 = t0 + v(0, -0.15, 1.55) * TL
        t2 = t1 + v(0, -0.35, 1.5) * TL
        t3 = t2 + v(0, -0.5, 1.35) * TL
        t4 = t3 + v(0, -0.45, 1.2) * TL
    tb = ["Tail1", "Tail2", "Tail3", "Tail4"]
    H.bone("Tail1", "Body", tuple(t0))
    H.bone("Tail2", "Tail1", tuple(t1))
    H.bone("Tail3", "Tail2", tuple(t2))
    H.bone("Tail4", "Tail3", tuple(t3))
    rr = [0.7 * G, 0.55, 0.4, 0.27, 0.13]
    pts = [t0, t1, t2, t3, t4]
    for i in range(4):
        a, b = pts[i], pts[i + 1]
        seg = round_cone(a - (b - a) * (0.18 if i else 0.3), b + (b - a) * 0.05, rr[i] * s, rr[i + 1] * s)
        core_t = seg
        if sp > 0:
            d = nrm(b - a)
            up_ = nrm(np.cross(d, (1, 0, 0)))
            if up_[1] < 0:
                up_ = -up_
            for j in range(2):
                u = (j + 0.5) / 2
                base = a + (b - a) * u + up_ * (rr[i] + (rr[i + 1] - rr[i]) * u - 0.08) * s
                seg = seg.su(blade_fin(base, up_, (0.32 - 0.06 * i) * sp * s * (1 - 0.3 * CU), (0.12 - 0.02 * i) * s, (1, 0, 0), flat=0.3, back=d), 0.04)
        if i == 3 and P["spade"]:
            d = nrm(b - a)
            side = V(1, 0, 0)
            c = b - d * 0.1 * s
            w = 0.6 * s * (1 + 0.2 * CU)
            spade = union_hard([tri(c, c + side * w + d * 0.05 * s, b + d * 0.75 * s, 0.07 * s),
                                tri(c, b + d * 0.75 * s, c - side * w + d * 0.05 * s, 0.07 * s),
                                tri(c, c + side * w + d * 0.05 * s, c - d * 0.3 * s, 0.07 * s),
                                tri(c, c - side * w + d * 0.05 * s, c - d * 0.3 * s, 0.07 * s)])
            seg = seg.su(spade, 0.05 * s)
        if i == 3 and P["stinger"]:
            d = nrm(b - a)
            seg = seg.su(curved_horn([b - d * 0.1 * s, b + d * 0.5 * s + V(0, 0.15, 0) * s, b + d * 0.85 * s + V(0, 0.45, 0) * s], 0.13 * s, 0.015 * s), 0.05)
        pat = combine(band_y(a[1] - 0.6 * s, a[1] + 0.6 * s, 1.0, 0.84), outside(core_t, 0.05, 0.45, 0.1))
        H.piece(f"Tail{'ABCD'[i]}", tb[i], seg, col="primary", tris=[650, 520, 420, 520 if (P["spade"] or P["stinger"]) else 320][i],
                role="tail", pri=1.4 + 0.15 * i, pattern=pat)

    # ------------------------------------------------------------------ wings
    wings = []
    if P["wings"] in ("bat", "ragged"):
        WS = P["wing"] * (1 - 0.45 * CU)
        S0 = T(0.62 * G, bodyY + 0.95 - 0.2 * CU, zc - 0.05)
        if biped:
            S0 = T(0.75 * G, bodyY + 0.7, zc - 0.35)

        def wpt(x, y, z):
            return S0 + V(x, y, z) * s * WS
        E = wpt(1.55, 1.15, 0.75)
        W = wpt(3.25, 2.45, -0.35)
        F = [wpt(7.0, 1.5, 0.35), wpt(6.6, 0.0, 2.05), wpt(5.0, -0.95, 3.15), wpt(3.0, -0.95, 3.35)]
        if biped:
            E = wpt(1.6, 0.6, 0.5)
            W = wpt(3.2, 1.6, -0.45)
            F = [wpt(6.8, 0.9, 0.3), wpt(6.4, -0.6, 2.0), wpt(4.8, -1.5, 3.05), wpt(2.9, -1.55, 3.2)]
        B1 = T(0.5 * G, bodyY + 0.45, zr - 0.05) if not biped else T(0.55 * G, bodyY + 0.3, zr - 0.3)
        up_n = nrm(np.cross(F[1] - W, F[3] - W))
        if up_n[1] < 0:
            up_n = -up_n
        t = 0.055 * s
        H.mbone("Wing#", "Body", tuple(S0))
        H.mbone("Hand#", "Wing#", tuple(W))
        # arm: humerus + forearm + inner membrane (wrist -> last finger -> body)
        ragged = P["wings"] == "ragged"
        arm = round_cone(S0 - (E - S0) * 0.1, E, 0.24 * s, 0.16 * s).su(round_cone(E, W, 0.17 * s, 0.12 * s), 0.08 * s)
        arm = arm.su(sphere(0.2 * s, E), 0.05)
        inner_poly = [W, F[3]] + scallop(F[3], B1, E + (S0 - E) * 0.3, 0.2, 0.25 * s, up_n, 5) + [S0 + (B1 - S0) * 0.1]
        mem_in = union_hard([fan(E, inner_poly, t), tri(S0, E, W, t), tri(S0, E, S0 + (B1 - S0) * 0.12, t)])
        _pts = [S0, E, W, B1] + list(F)
        mem_in = bounded(mem_in, np.min(_pts, 0), np.max(_pts, 0), 0.4 * s)
        if ragged:
            mem_in = mem_in - sphere(0.35 * s, (F[3] + B1) / 2 - up_n * 0.2 * s) - sphere(0.25 * s, F[3] + (B1 - F[3]) * 0.75)
        H.mpiece("WingArm#", "Wing#", arm.su(mem_in, 0.03 * s), col="membrane", mat="skin", tris=1100, res=150, role="wing", pri=1.2, smooth=2)
        # hand: fingers + outer membrane + thumb claw
        hand = sphere(0.16 * s, W)
        for i, f in enumerate(F):
            hand = hand.su(round_cone(W, f, (0.1 - 0.012 * i) * s, 0.03 * s), 0.04 * s)
        hand = hand.su(curved_horn([W, W + nrm(W - E) * 0.28 * s + V(0, 0.12, 0) * s, W + nrm(W - E) * 0.45 * s + V(0, 0.02, -0.08) * s], 0.07 * s, 0.012 * s), 0.03)
        hand = hand.su(spike(F[0], F[0] - W, 0.35 * s, 0.05 * s), 0.02)
        mem_out = bounded(membrane(W, F, t=t, depth=0.24, sag=0.28 * s, up=up_n, n=5), np.min(_pts, 0), np.max(_pts, 0), 0.4 * s)
        if ragged:
            for a, b in zip(F[:-1], F[1:]):
                m = (a + b) / 2 + (W - (a + b) / 2) * 0.22
                mem_out = mem_out - sphere(0.3 * s, m) - sphere(0.18 * s, a + (b - a) * 0.25 + (W - a) * 0.12)
        H.mpiece("WingHand#", "Hand#", hand.su(mem_out, 0.03 * s), col="membrane", mat="skin", tris=1300, res=160, role="wing", pri=1.25, smooth=2)
        wings = [("WingR", "HandR", 1), ("WingL", "HandL", -1)]

    elif P["wings"] == "butterfly":
        S0 = T(0.45 * G, bodyY + 0.85, zc + 0.1)
        H.mbone("Wing#", "Body", tuple(S0))
        H.mbone("Hand#", "Wing#", tuple(S0 + v(0.15, 0, 0.2)))
        ws = s * P["wing"]

        def lobe(c, d, L, w, n_, veins=4):
            R = frame(d, n_)
            sh = oell(c + R[:, 0] * L * 0.5, R, (L * 0.5, w, 0.05 * s))
            sh = sh.su(oell(c + R[:, 0] * L * 0.78 + R[:, 1] * w * 0.25, R, (L * 0.3, w * 0.85, 0.05 * s)), 0.1 * s)
            rim = sh & (oell(c + R[:, 0] * L * 0.55, R, (L * 0.62, w * 1.2, 0.2 * s)) - oell(c + R[:, 0] * L * 0.5, R, (L * 0.42, w * 0.78, 0.3 * s)))
            for k in range(veins):
                a_ = -0.6 + 1.2 * k / max(veins - 1, 1)
                dv = nrm(R[:, 0] * math.cos(a_) + R[:, 1] * math.sin(a_) * 0.8)
                sh = sh.su(round_cone(c, c + dv * L * 0.85, 0.05 * s, 0.02 * s), 0.02)
            return sh, rim

        fw, frim = lobe(S0, (1.0, 0.75, -0.55), 3.0 * ws, 0.95 * ws, (0.1, 0.3, 1.0))
        hw, hrim = lobe(S0 + v(0.1, -0.1, 0.25), (1.0, 0.1, 0.75), 2.2 * ws, 0.8 * ws, (0.0, 1.0, 0.2))
        H.mpiece("WingArm#", "Wing#", fw, col="membrane", mat="skin", tris=900, res=150, role="wing", pri=1.2, smooth=2,
                 pattern=combine(outside(fw - frim, -0.01, 0.55, 0.03), stripes(lambda Q: np.linalg.norm(Q - S0, axis=1) / s, 1.6, width=0.12, depth=0.25)))
        H.mpiece("WingHand#", "Hand#", hw, col="secondary", mat="skin", tris=800, res=150, role="wing", pri=1.25, smooth=2,
                 pattern=outside(hw - hrim, -0.01, 0.55, 0.03))
        wings = [("WingR", "HandR", 1), ("WingL", "HandL", -1)]

    # ------------------------------------------------------------------ sockets, rig, motion
    H.socket("mouth", h(0, -0.15, -0.65 - 1.0 * SN), "Jaw")
    H.socket("head", h(0, 0.55, -0.3), "Head")
    if "seat" not in H.sockets:
        H.socket("seat", v(0, bodyY + 1.1, saddle_z), "Body")
    tail_b = ["Tail1", "Tail2", "Tail3", "Tail4"]
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": tail_b, "neck": ["Neck1", "Neck2"]})
    rl = []
    for up, lo, ft, front, side in legs:
        rl.append({"hip": up, "knee": lo, "side": side})
    H.rig["legs"] = rl
    height = bodyY + 1.2
    if P["wings"] == "none":
        ql = [("ShoulderFR", "ElbowFR", "WristFR", 0.75, True), ("ShoulderFL", "ElbowFL", "WristFL", 0.25, True),
              ("HipR", "KneeR", "HockR", 0.5, False), ("HipL", "KneeL", "HockL", 0.0, False)]
        motion.quadruped(H, ql, neck="Neck1", head="Head", jaw="Jaw", tail=tail_b, stride=0.36, walk=1.25, height=height, attack="bite")
        mm.overlay(H, "Move", lambda t: {"Neck2": (0, 0, 0, 0.04 * math.sin(2 * math.pi * t / 1.25 * 2), 0, 0)})
    else:
        mm.flyer(H, legs, wings, neck=["Neck1", "Neck2"], head="Head", jaw="Jaw", tail=tail_b, height=height, hipz=zr * s,
                 flap=1.0 if not CU else 0.8, lift=0.22 if not CU else 0.3, period=1.15 if not CU else 0.5, tuck=1.0)
    return H


DRAGON_PREVIEW = {"primary": "#B3261E", "secondary": "#F2A43A", "belly": "#F5C27A", "membrane": "#D4683A", "horn": "#EFE3C8",
                  "iris": "#F2C230", "leather": "#6B4423"}


@hero("dragon", "dragons")
def dragon():
    return _dragon("dragon", saddle=True, preview=DRAGON_PREVIEW)


@hero("elder dragon", "dragons")
def elder_dragon():
    return _dragon("elder dragon", wings="ragged", horns="crown", girth=1.15, body=1.08, wing=1.15, spines=1.45, frill=1.45, head=1.05,
                   tail=1.1, preview={"primary": "#57534E", "secondary": "#F59E0B", "belly": "#C9A46A", "membrane": "#6E5A4A", "horn": "#D8CBB0", "iris": "#F59E0B"})


@hero("drake", "dragons")
def drake():
    return _dragon("drake", wings="none", leg=0.82, girth=1.2, body=1.05, neck=0.78, spines=1.35, head=1.0, snout=0.9, tail=0.9,
                   preview={"primary": "#C2410C", "secondary": "#FDBA74", "belly": "#FDCB94", "horn": "#3A2A22", "iris": "#FFD23A"})


@hero("wyvern", "dragons")
def wyvern():
    return _dragon("wyvern", legs4=False, saddle=True, stinger=True, spade=False, girth=0.92, wing=1.08, neck=0.95, horns="classic", frill=0.8,
                   preview={"primary": "#3F6212", "secondary": "#BEF264", "belly": "#C9E6A0", "membrane": "#6B8A3A", "iris": "#E8E23A", "leather": "#6B4423"})


@hero("baby dragon", "dragons")
def baby_dragon():
    return _dragon("baby dragon", cute=1.0, horns="nub", spines=0.6, frill=0.0, girth=1.1, body=0.8, eye=1.0,
                   preview={"primary": "#F97316", "secondary": "#FDE68A", "belly": "#FDE9A8", "membrane": "#FBBF6A", "iris": "#3A8AE8"})


@hero("fairy dragon", "dragons")
def fairy_dragon():
    return _dragon("fairy dragon", cute=1.0, wings="butterfly", horns="nub", spines=0.4, frill=0.0, girth=0.75, body=0.8, wing=1.7, leg=1.05,
                   preview={"primary": "#F0ABFC", "secondary": "#93C5FD", "belly": "#FCE7F3", "membrane": "#C4B5FD", "iris": "#7C3AED"})


