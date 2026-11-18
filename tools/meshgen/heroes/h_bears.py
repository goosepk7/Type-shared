"""Bears (family "canines" data module): brown bear, grizzly (shoulder hump), black bear (tan muzzle), polar bear (long
neck, narrow head), giant panda (black limbs, ears, eye patches and shoulder band), cave bear, koala, and the armoured
bear warrior mount.

_bear(): a heavy plantigrade sculpt: a long barrel body with a muscular shoulder hump and a high rump, thick
three-segment legs (shoulder-elbow-wrist / hip-knee-ankle) ending in broad paws whose whole sole meets the ground,
long front claws, a broad dished skull with a short muzzle, small round ears on their own bones, a separate jaw with
fangs, and a stubby tail. Walks with a rolling lateral gait; attacks by rearing up and slamming a paw down.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from kit import Hero, hero, spots, stripes, gradient, combine, _mirror_sdf
from map import NOTFOOD
import motion_canines as MC

NOSE = [0.12, 0.1, 0.1]
LEATHER = [0.42, 0.26, 0.14]


def A(*a):
    return np.array(a, float)


def T(a):
    return tuple(float(x) for x in a)


def overlay(base, region, off):
    return base.round(off) & region


BBASE = dict(
    s=1.0, leg=1.0, body=1.0, girth=1.0, hump=0.5, neck=1.0, head=1.0, muzzle=1.0, mw=1.0, dome=0.0, ear=1.0, eye=1.0,
    fluff=0.012, belly=0.85, claws=1.0, tail=1.0, legdark=0.0,
    panda=False, koala=False, marks=None, armor=False, mount=False, preview=None, tags=(),
)


def _bear(hid, **kw):
    P = dict(BBASE)
    P.update(kw)
    s, LG, BL, G = P["s"], P["leg"], P["body"], P["girth"]
    H = MC.FastHero(hid, plan="Quadruped", gait="heavy", tags=["bear"] + list(P["tags"]))
    H.preview = P["preview"] or {}
    marks = P["marks"] or {}
    fl = P["fluff"]

    def v(x, y, z):
        return A(x * s, y * s, z * s)

    def furry(sd, amp=1.0, freq=7.0, seed=0):
        return sd.noise(fl * amp * s, freq / s, seed) if fl > 0 else sd

    legH = 1.15 * LG
    chD = 1.65 * G ** 0.5
    backY = legH + chD
    zc, zr = -0.75 * BL, 1.0 * BL
    H.body(T(v(0, legH + 0.55 * chD, 0)))
    HU = P["hump"]

    def back_shade(Q):
        t = np.clip((Q[:, 1] / s - (legH + 0.2 * chD)) / (chD + 0.8), 0, 1)
        return 1.0 - (1.0 - P["belly"]) * t

    LD = P["legdark"]

    def legshade(Q):
        if LD <= 0:
            return np.ones(len(Q))
        t = np.clip((legH + 0.2 - Q[:, 1] / s) / (legH * 0.8), 0, 1)
        return 1 - LD * t

    # ---------------------------------------------------------------- torso
    torso = ellipsoid(s * (0.78 * G), s * (0.52 * chD), s * (1.05 * BL), T(v(0, legH + 0.52 * chD, zc + 0.2)))                       # chest barrel
    torso = torso.su(ellipsoid(s * (0.72 * G), s * (0.48 * chD), s * (0.95 * BL), T(v(0, legH + 0.5 * chD, 0.45 * BL))), 0.5 * s)          # belly / loins
    torso = torso.su(ellipsoid(s * (0.7 * G), s * (0.5 * chD), s * (0.7 * BL), T(v(0, legH + 0.55 * chD, zr))), 0.45 * s)                 # rump
    torso = torso.su(ellipsoid(s * (0.48 * G), s * (0.3 + 0.25 * HU), s * (0.65), T(v(0, backY - 0.1 + 0.12 * HU, zc - 0.05))), 0.4 * s)    # shoulder hump
    torso = torso.su(ellipsoid(s * (0.3 * G), s * (0.55 * chD), s * (0.5), T(v(0.5 * G, legH + 0.6 * chD, zc - 0.35))).mirror_x(), 0.3 * s)  # shoulders
    torso = torso.su(ellipsoid(s * (0.32 * G), s * (0.5 * chD), s * (0.55), T(v(0.48 * G, legH + 0.55 * chD, zr + 0.1))).mirror_x(), 0.3 * s)  # haunches
    nb = v(0, backY - 0.35, zc - 0.85 * BL)
    NK = P["neck"]
    torso = torso.su(round_cone(T(v(0, legH + 0.6 * chD, zc - 0.4)), T(nb + v(0, 0.15, -0.25 * NK)), 0.66 * G * s, 0.5 * G * s), 0.35)
    torso = furry(torso, 1.0, 5.0, 1)
    H.piece("Torso", "Body", torso, col="primary", tris=2600, res=128, pattern=back_shade)
    if P["panda"]:  # black shoulder band over the back and down the forelegs
        reg = (ellipsoid(s * (1.4 * G), s * (1.4), s * (0.5), T(v(0, legH + 0.5 * chD, zc - 0.5))) | ellipsoid(s * (1.4 * G), s * (0.55 * chD), s * (0.75), T(v(0, legH + 0.15, zc - 0.85)))).noise(0.03 * s, 6 / s, 2)
        H.piece("Band", "Body", overlay(torso, reg, 0.05 * s), col="secondary", tris=1100, role="body", pri=1.2)
    if P["armor"]:  # bear warrior: steel chest plate and back plate
        plate = overlay(torso, ellipsoid(s * (1.2 * G), s * (0.95), s * (0.7), T(v(0, legH + 0.55 * chD, zc - 0.85 * BL))), 0.1 * s)
        plate = plate.su(overlay(torso, box(1.3 * G * s, 0.08 * s, 0.9 * s, T(v(0, legH + 0.62 * chD, zc - 0.6))), 0.12 * s), 0.02)
        H.piece("ChestPlate", "Body", plate, col="steel", mat="metal", tris=1000, role="armor", pri=1.3)
        rump = overlay(torso, ellipsoid(s * (1.3 * G), s * (0.6), s * (0.85), T(v(0, backY - 0.05, zr + 0.25))), 0.1 * s)
        H.piece("RumpPlate", "Body", rump, col="steel", mat="metal", tris=900, role="armor", pri=1.3)
    if P["mount"]:
        st = v(0, backY + 0.08 + 0.1 * HU, -0.05)
        seat = round_box(0.5 * G * s, 0.1 * s, 0.55 * s, 0.08 * s, T(st + v(0, 0.12, 0)))
        seat = seat.su(round_box(0.34 * G * s, 0.15 * s, 0.09 * s, 0.06 * s, T(st + v(0, 0.24, -0.5))), 0.05)
        seat = seat.su(round_box(0.42 * G * s, 0.18 * s, 0.08 * s, 0.06 * s, T(st + v(0, 0.26, 0.52))), 0.05)
        seat = (seat & torso.round(0.4 * s)) - torso.round(0.07 * s)
        H.piece("SaddleSeat", "Body", seat, col=LEATHER, mat="skin", tris=900, role="saddle", pri=1.4)
        blanket = overlay(torso, box(1.1 * G * s, 0.5 * s, 0.75 * s, T(st + v(0, 0.1, 0))), 0.05 * s)
        H.piece("Blanket", "Body", blanket, col="secondary", mat="cloth", tris=800, role="saddle", pri=1.3)
        H.socket("seat", T(st + v(0, 0.32, 0)), "Body")
        H.mount = {"seat": "Torso", "saddle": {"pos": T(st + v(0, 0.24, 0)), "size": T(v(1.0 * G, 0.25, 1.2))}}

    # ---------------------------------------------------------------- legs
    lcol = "secondary" if P["panda"] else "primary"
    lpat = None if P["panda"] else legshade
    CL = P["claws"]

    def paw(c, front):
        c = A(*c)
        k = s * G ** 0.5
        p = ellipsoid(0.3 * k, 0.15 * k, 0.33 * k if front else 0.45 * k, T(c + A(0, 0.14, 0.02 if front else 0.12) * k))
        p = p.su(ellipsoid(0.28 * k, 0.12 * k, 0.12 * k, T(c + A(0, 0.12, -0.25) * k)), 0.08 * k)
        for dx in (-0.2, -0.1, 0.0, 0.1, 0.2):
            p = p.su(sphere(0.075 * k, T(c + A(dx, 0.08, -0.33 + 0.25 * dx * dx) * k)), 0.05 * k)
        return p & plane((0, -1, 0), 0.0)

    def claws(c, front):
        c = A(*c)
        k = s * G ** 0.5
        L = (0.2 if front else 0.1) * CL
        out = None
        for dx in (-0.2, -0.1, 0.0, 0.1, 0.2):
            b = c + A(dx, 0.09, -0.37 + 0.25 * dx * dx) * k
            cl = round_cone(T(b), T(b + A(0, -0.06, -L) * k), 0.035 * k, 0.012 * k)
            out = cl if out is None else out | cl
        return out & plane((0, -1, 0), -0.005)

    sh = v(0.5 * G, legH + 0.55 * chD, zc - 0.45)
    el = v(0.52 * G, legH * 0.95, zc - 0.25)
    wr = v(0.48 * G, 0.32 * LG, zc - 0.38)
    fp = A(wr[0], 0, wr[2] - 0.05 * s)
    H.mbone("ShoulderF#", "Body", T(sh))
    H.mbone("ElbowF#", "ShoulderF#", T(el))
    H.mbone("WristF#", "ElbowF#", T(wr))
    up = round_cone(T(sh + v(0, 0.35, 0.15)), T(el), 0.44 * G * s, 0.27 * G * s)
    up = up.su(ellipsoid(s * (0.3 * G), s * (0.6), s * (0.45), T((sh + el) / 2 + v(0.02, 0, 0.08))), 0.25 * s)
    H.mpiece("UpperF#", "ShoulderF#", furry(up, 0.9, 6, 2), col=lcol, tris=900, role="limb", pattern=lpat)
    fo = round_cone(T(el), T(wr + v(0, 0.05, 0)), 0.27 * G * s, 0.21 * G * s)
    fo = fo.su(ellipsoid(s * (0.25 * G), s * (0.35), s * (0.26 * G), T(el + v(0, -0.2, -0.04))), 0.12 * s)
    H.mpiece("ForeF#", "ElbowF#", furry(fo, 0.8, 7, 3), col=lcol, tris=700, role="limb", pattern=lpat)
    pf = round_cone(T(wr), T(fp + v(0, 0.18, 0)), 0.21 * G * s, 0.24 * G * s).su(paw(fp, True), 0.1 * s)
    H.mpiece("PawF#", "WristF#", furry(pf, 0.6, 8, 4), col=lcol, tris=700, role="foot", pattern=lpat)
    H.mpiece("ClawF#", "WristF#", claws(fp, True), col="claw", mat="hard", tris=400, role="claw", pri=2.0, ao=False)

    hp = v(0.48 * G, legH + 0.55 * chD, zr + 0.05)
    kn = v(0.52 * G, legH * 1.0, zr - 0.3)
    an = v(0.48 * G, 0.36 * LG, zr + 0.28)
    bp = A(an[0], 0, an[2] - 0.32 * s)
    H.mbone("HipB#", "Body", T(hp))
    H.mbone("KneeB#", "HipB#", T(kn))
    H.mbone("HockB#", "KneeB#", T(an))
    th = round_cone(T(hp + v(0, 0.3, 0.1)), T(kn), 0.5 * G * s, 0.3 * G * s)
    th = th.su(ellipsoid(s * (0.36 * G), s * (0.65), s * (0.55), T((hp + kn) / 2 + v(0.02, 0, 0.2))), 0.3 * s)
    H.mpiece("Thigh#", "HipB#", furry(th, 0.9, 6, 5), col=lcol, tris=900, role="limb", pattern=lpat)
    sn = round_cone(T(kn), T(an), 0.3 * G * s, 0.21 * G * s)
    sn = sn.su(ellipsoid(s * (0.24 * G), s * (0.4), s * (0.27), T(kn + v(0, -0.2, 0.12))), 0.12 * s)
    H.mpiece("Shin#", "KneeB#", furry(sn, 0.8, 7, 6), col=lcol, tris=700, role="limb", pattern=lpat)
    pb = round_cone(T(an), T(an + v(0, -0.2, 0.06)), 0.21 * G * s, 0.2 * G * s).su(paw(bp, False), 0.12 * s)
    H.mpiece("PawB#", "HockB#", furry(pb, 0.6, 8, 7), col=lcol, tris=700, role="foot", pattern=lpat)
    H.mpiece("ClawB#", "HockB#", claws(bp, False), col="claw", mat="hard", tris=300, role="claw", pri=2.0, ao=False)
    if P["armor"]:
        pa = overlay(up, ellipsoid(s * (0.6 * G), s * (0.5), s * (0.55), T(sh + v(0.15, 0.25, 0))), 0.09 * s)
        H.mpiece("Pauldron#", "ShoulderF#", pa, col="steel", mat="metal", tris=600, role="armor", pri=1.4)

    # ---------------------------------------------------------------- neck + head
    H.bone("Neck", "Body", T(nb))
    hc = nb + v(0, 0.25 * NK + 0.1, -0.75 * NK - 0.15)
    neck = tube([T(nb + v(0, -0.25, 0.35)), T(nb + v(0, 0.08, -0.35 * NK)), T(hc + v(0, -0.05, 0.15))], [0.62 * G * s, 0.52 * G * s, 0.42 * s * P["head"]], k=0.25)
    neck = furry(neck, 1.0, 6, 8)
    H.piece("NeckP", "Neck", neck, col="primary", tris=900, role="limb", pattern=back_shade)
    hs = P["head"] * s * 1.25
    H.bone("Head", "Neck", T(hc))
    M, MW, DM = P["muzzle"], P["mw"], P["dome"]
    mz = 0.45 * M

    def hw(x, y, z):
        return T(hc + A(x, y, z) * hs)

    def W(sd):
        return sd.scale(hs).at(*T(hc))

    head = ellipsoid(0.42 * (1 + 0.1 * DM), 0.36 * (1 + 0.2 * DM), 0.42, (0, 0.06 + 0.04 * DM, -0.2))
    head = head.su(ellipsoid(0.22, 0.2, 0.25, (0.24, -0.06, -0.3)).mirror_x(), 0.14)                        # big cheeks
    head = head.su(ellipsoid(0.26, 0.2, 0.2, (0, 0.13 + 0.04 * DM, -0.45)), 0.12)                           # forehead
    head = head.su(round_cone((0, 0, 0), (0, -0.03, -0.05 - mz), 0.19 * MW, 0.13 * MW).scale3(1, 1.1, 1).at(0, -0.08, -0.5), 0.12)
    head = head.su(ellipsoid(0.11 * MW, 0.1, 0.18 * M + 0.1, (0.08 * MW, -0.16, -0.52 - 0.5 * mz)).mirror_x(), 0.06)
    if P["koala"]:
        head = head.su(ellipsoid(0.48, 0.36, 0.4, (0, 0.0, -0.2)), 0.1)
    # eyes sit on the actual surface: march out from inside the skull along the gaze direction
    er_l = 0.055 * P["eye"]
    gaze = A(0.62, 0.12, -0.78)
    gaze = gaze / np.linalg.norm(gaze)
    p0 = A(0.1, 0.1, -0.4)
    for _ in range(80):
        if head(p0[None])[0] > 0:
            break
        p0 = p0 + gaze * 0.01
    eye_l = p0 - gaze * er_l * 0.45
    head = head.ss(sphere(er_l * 1.15, T(eye_l)).mirror_x(), 0.03)
    headW = furry(W(head), 0.45, 9, 9)
    H.piece("HeadP", "Head", headW, col="primary", tris=2200, res=128, role="head")
    mk = None
    if P["panda"]:  # eye patches
        reg = ellipsoid(0.13, 0.17, 0.16).rot(0, 0, -35).at(*T(eye_l + A(0.01, -0.03, 0.02))).mirror_x()
        mk = ("EyePatch", reg, "secondary")
    elif "muzzle" in marks:
        reg = ellipsoid(0.3 * MW, 0.28, 0.25 + mz, (0, -0.1, -0.6 - 0.4 * mz)) & plane((0, -1, 0), 0.03)
        reg = reg | (ellipsoid(0.24 * MW, 0.25, 0.25 + mz, (0, -0.06, -0.62 - 0.4 * mz)))
        mk = ("Mask", reg, marks["muzzle"])
    if mk:
        H.piece(mk[0], "Head", overlay(headW, W(mk[1]), 0.04 * s), col=mk[2], tris=600, role="head", pri=1.3)
    nz = -0.58 - mz
    nr = 1.6 if P["koala"] else 1.0
    nose = ellipsoid(0.11 * MW * nr, 0.075 * nr * (1.5 if P["koala"] else 1), 0.08 * nr, (0, -0.07 - (0.06 if P["koala"] else 0), nz + (0.05 if P["koala"] else 0)))
    nose = nose.ss(sphere(0.028, (0.05 * MW * nr, -0.1, nz - 0.07)).mirror_x(), 0.01)
    H.piece("Nose", "Head", W(nose), col=NOSE, mat="skin", tris=300, role="nose", pri=1.6, ao=False)
    jb = H.bone("Jaw", "Head", hw(0, -0.12, -0.3))
    jl = mz + 0.1
    jaw = ellipsoid(0.13 * MW, 0.075, 0.14 + 0.45 * jl, (0, -0.23, -0.42 - 0.5 * jl))
    jaw = jaw.su(capsule((0.16, -0.14, -0.28), (0.09 * MW, -0.22, -0.45 - 0.6 * jl), 0.065).mirror_x(), 0.06)
    jcol = marks.get("muzzle", "primary")
    H.piece("JawP", "Jaw", furry(W(jaw), 0.3, 10, 10), col=jcol, tris=500, role="jaw", pri=1.4)
    H.prim("Mouth", "Jaw", "Ellipsoid", (0.18 * MW * hs, 0.05 * hs, (0.2 + 0.8 * jl) * hs), hw(0, -0.155, -0.42 - 0.5 * jl), col="mouth", mat="hard", role="mouth", pri=2.4)
    fang = round_cone((0.08 * MW, -0.16, -0.52 - 0.85 * mz), (0.075 * MW, -0.28, -0.53 - 0.85 * mz), 0.03, 0.007)
    H.mpiece("Fang#", "Head", W(fang), col="tooth", mat="hard", tris=150, role="tooth", pri=2.2, ao=False, smooth=2)
    er = er_l * hs
    H.eyes("Head", hw(*eye_l), er, col="iris", pupil=None if P["panda"] or P["koala"] else "round",
           look=(0.62, 0.12, -0.78))
    # round ears
    EA = P["ear"]
    if P["koala"]:
        ear = ellipsoid(0.3 * hs * EA, 0.27 * hs * EA, 0.09 * hs).noise(0.03 * hs, 12 / hs, 3)
        ear = ear.ss(ellipsoid(0.18 * hs * EA, 0.16 * hs * EA, 0.06 * hs, (0, 0, -0.07 * hs)), 0.03 * hs)
        ear = ear.at(0.12 * hs * EA, 0.05 * hs, 0).rot(0, -15, -15)
        epos = (0.38, 0.22, -0.1)
    else:
        r = 0.14 * EA * hs
        ear = sphere(r).scale3(1, 0.95, 0.5).ss(sphere(r * 0.7).scale3(1, 0.95, 0.4).at(0, 0.0, -r * 0.35), 0.02 * hs)
        ear = ear.at(0, r * 0.45, 0).rot(-10, -25, -18)
        epos = (0.28, 0.33 + 0.04 * DM, -0.12)
    ears = []
    for sx, tag in ((1, "R"), (-1, "L")):
        bpos = A(*hw(sx * epos[0], epos[1], epos[2]))
        bn = H.bone(f"Ear{tag}", "Head", T(bpos))
        ears.append(bn)
        sh_ = ear if sx > 0 else _mirror_sdf(ear)
        H.piece(f"Ear{tag}", bn, sh_.at(*T(bpos)), col="secondary" if P["panda"] else ("light" if P["koala"] else "primary"), tris=350, role="ear", pri=1.5,
                key=f"h_{H.id}_ear".replace(" ", "_") + ("" if sx > 0 else "_l"), mirrored=sx < 0)
    if P["armor"]:
        helm = overlay(headW, ellipsoid(0.55, 0.3, 0.45, (0, 0.28, -0.25)).scale(hs).at(*T(hc)), 0.08 * s)
        helm = helm.su(round_cone(hw(0, 0.3, -0.42), hw(0, 0.1, -0.78), 0.05 * hs, 0.04 * hs), 0.03)       # nose guard
        H.piece("Helmet", "Head", helm, col="steel", mat="metal", tris=800, role="armor", pri=1.4)
    # ---------------------------------------------------------------- tail
    t0 = v(0, backY - 0.25, zr + 0.65 * BL)
    t1 = t0 + v(0, -0.12, 0.28) * P["tail"]
    H.bone("Tail1", "Body", T(t0))
    H.piece("TailA", "Tail1", furry(ellipsoid(0.17 * s, 0.15 * s, 0.22 * s * P["tail"], T((t0 + t1) / 2)), 1.0, 9, 11), col="primary", tris=300, role="tail", pri=1.6)
    # ---------------------------------------------------------------- rig + motion
    H.socket("mouth", hw(0, -0.15, -0.65 - mz), "Jaw")
    H.socket("head", hw(0, 0.5, -0.2), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": ["Tail1"]})
    legs = [("ShoulderFR", "ElbowFR", "WristFR", True, 1), ("ShoulderFL", "ElbowFL", "WristFL", True, -1),
            ("HipBR", "KneeBR", "HockBR", False, 1), ("HipBL", "KneeBL", "HockBL", False, -1)]
    MC.quad(H, legs, neck="Neck", head="Head", jaw="Jaw", tail=["Tail1"], ears=ears, height=backY * s + 0.6, gait="walk", stride=0.36,
            lift=0.85, walk=1.15 * s ** 0.3, attack=P.get("attack", "swipe"), sway=1.4)
    return H


def PV(primary, secondary, **k):
    d = {"primary": primary, "secondary": secondary, "iris": "#3A2416"}
    d.update(k)
    return d


@hero("bear", "canines")
def bear():
    return _bear("bear", hump=0.6, legdark=0.35, preview=PV("#6E4A2E", "#A8846A"))


@hero("grizzly bear", "canines")
def grizzly():
    return _bear("grizzly bear", s=1.08, hump=1.25, girth=1.08, claws=1.5, fluff=0.02, legdark=0.45, dome=0.2, muzzle=0.95, mw=1.1,
                 preview=PV("#7A5636", "#C2A07A"))


@hero("black bear", "canines")
def black_bear():
    return _bear("black bear", s=0.9, hump=0.2, girth=0.92, ear=1.25, muzzle=1.05, mw=0.9, marks={"muzzle": "secondary"}, belly=0.95,
                 preview=PV("#1E1A18", "#A0805E"))


@hero("polar bear", "canines")
def polar_bear():
    return _bear("polar bear", s=1.1, hump=0.0, neck=1.45, head=0.9, muzzle=1.3, mw=0.85, ear=0.8, body=1.1, leg=1.08, belly=0.95,
                 preview=PV("#F5F3EC", "#2A2A2A"))


@hero("panda", "canines")
def panda():
    return _bear("panda", s=0.9, panda=True, hump=0.1, girth=1.1, head=1.25, dome=0.8, muzzle=0.45, mw=1.15, eye=1.1, ear=1.1, belly=1.0, fluff=0.008,
                 attack="bite", preview=PV("#F7F7F5", "#1A1A1A"))


@hero("cave bear", "canines")
def cave_bear():
    return _bear("cave bear", s=1.2, hump=0.8, girth=1.15, dome=0.9, head=1.12, muzzle=1.0, mw=1.15, claws=1.4, fluff=0.024, legdark=0.3,
                 preview=PV("#5A4030", "#8A6A50"))


@hero("koala", "canines")
def koala():
    return _bear("koala", s=0.6, koala=True, hump=0.0, girth=0.95, leg=1.05, body=0.75, head=1.45, dome=0.6, muzzle=0.35, mw=1.0, ear=1.25,
                 fluff=0.016, belly=1.0, claws=0.8, tail=0.3, attack="bite", preview=PV("#9E9A98", "#F2EEEA", light="#D9D5D2"))


@hero("bear warrior", "canines")
def bear_warrior():
    return _bear("bear warrior", s=1.15, hump=0.2, neck=1.3, head=0.95, muzzle=1.2, mw=0.9, ear=0.85, body=1.1, armor=True, mount=True,
                 belly=0.95, preview=PV("#F5F3EC", "#94A3B8", steel="#8A94A0"))


BEARX = "!water bear, !woolly bear, !wooly bear, !teddy bear, !bear trap, !gummy bear, !bear claw, !care bear"
MAP = [
    ("bear", "bear, bears, brown bear, kodiak bear, kodiak, sun bear, sloth bear, spectacled bear, asiatic black bear, short-faced bear, "
             "short faced bear, spirit bear, thunder bear, ice bear, bear cub, mama bear, ursa, robot bear, " + BEARX, NOTFOOD),
    ("grizzly bear", "grizzly, grizzly bear, grizzly cub, " + BEARX, NOTFOOD),
    ("black bear", "black bear, " + BEARX, NOTFOOD),
    ("polar bear", "polar bear, polar bear cub, white bear, " + BEARX, NOTFOOD),
    ("panda", "panda, panda bear, giant panda, panda cub, panda monk, !red panda", NOTFOOD),
    ("cave bear", "cave bear, dire bear, owlbear, bearowl, owl bear, " + BEARX, NOTFOOD),
    ("koala", "koala, koala joey, drop bear, " + BEARX, NOTFOOD),
    ("bear warrior", "bear warrior, war bear, armored bear, armoured bear, bear rider, battle bear, " + BEARX,
     {"bp": ["Quadruped", "Biped", "Humanoid"], "cat": ["Creature", "Person", "Abstract", "Element", "Machine"]}),
]
