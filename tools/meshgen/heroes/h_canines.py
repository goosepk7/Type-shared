"""Canines (dogs, wolves, foxes, hyenas, cerberus) and bears.

_canid(): one parametric dog sculpt. A deep, laterally narrow ribcage with a tucked waist and croup, scapulae and a
prosternum, a rising neck, a dog skull (cranium, zygomas, stop, brows, muzzle with flews) with a separate opening jaw,
nose leather, tongue, fangs, ears on their own bones (erect / floppy / rose / bat / round, so floppy ears bounce),
digitigrade legs (shoulder-elbow-wrist / hip-stifle-hock) with compact four-toed paws, and a three-bone tail
(hanging brush, sickle, curl over the back, whip, bob). Markings are separate overlay pieces (the base sculpt
inflated and clipped to a region: chest bib, saddle, face mask, muzzle, blaze, socks, tail tip) coloured with the
word's secondary colour, so "fire husky" still keeps its mask.

_bear(): plantigrade, heavy: shoulder hump, big round head, round ears, short tail, long claws; rears up to swipe.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from kit import Hero, hero, spots, stripes, gradient, combine, _mirror_sdf
from map import NOTFOOD
import motion_canines as MC
import mountkit as MK

NOSE = [0.13, 0.11, 0.11]
LEATHER = [0.42, 0.26, 0.14]
PINK = [0.86, 0.55, 0.55]


def A(*a):
    return np.array(a, float)


def T(a):
    return tuple(float(x) for x in a)


def overlay(base, region, off):
    """A colour patch: the base sculpt inflated by `off` and clipped to `region` (stands proud, never coplanar)."""
    return base.round(off) & region


# ====================================================================================================== canids
CBASE = dict(
    s=1.0, leg=1.0, body=1.0, girth=1.0, chest=1.0, tuck=1.0, slope=0.0, neck=0.85, lt=1.0,
    head=1.0, muzzle=1.0, mw=1.0, dome=0.0, jowls=0.0, eye=1.0, underbite=0.0, wrinkles=0.0,
    ear="erect", ear_size=1.0, ear_w=1.0,
    tail="hang", tail_len=1.0, tail_thick=1.0,
    fluff=0.0, ruff=0.0, belly=0.85,
    pattern=None, marks=None, socks=None, stock=0.0,
    hips=1.0, collar=None, tongue=False, fangs=1.0, paws=1.0, heads=1, poodle=False, mane=0.0,
    attack="bite", wag=0.0, gait="trot", mount=None, saddle=None, eyecol="iris", pupil="round",
    tags=(), preview=None,
)


def _canid(hid, **kw):
    P = dict(CBASE)
    P.update(kw)
    s, LG, BL, G, CH = P["s"], P["leg"], P["body"], P["girth"], P["chest"]
    HS, M, MW, LT = P["head"], P["muzzle"], P["mw"], P["lt"]
    H = MC.FastHero(hid, plan="Quadruped", gait="trot", tags=["canine"] + list(P["tags"]))
    H.preview = P["preview"] or {}
    marks = P["marks"] or {}
    fl = P["fluff"]

    def v(x, y, z):
        return A(x * s, y * s, z * s)

    def furry(sd, amp=1.0, freq=8.0, seed=0):
        return sd.noise(fl * amp * s, freq / s, seed) if fl > 0 else sd

    # ---------------------------------------------------------------- landmarks
    legH = 1.45 * LG
    chD = 1.42 * CH
    backY = legH + chD
    SL = P["slope"]
    zc, zr = -0.6 * BL, 0.95 * BL
    bodyC = v(0, legH + 0.55 * chD, 0)
    H.body(T(bodyC))

    def back_shade(Q):
        t = np.clip((Q[:, 1] / s - (legH + 0.3 * chD)) / (0.8 * chD + 1.2), 0, 1)
        return 1.0 - (1.0 - P["belly"]) * t

    pat = None
    if P["pattern"] == "dalmatian":
        pat = spots(0.36 * s, 0.11 * s, depth=0.92, seed=4)
    elif P["pattern"] == "hyena":
        pat = spots(0.3 * s, 0.09 * s, depth=0.6, seed=9)
    elif P["pattern"] == "brindle":
        pat = stripes(lambda Q: Q[:, 2] / s + 0.3 * Q[:, 1] / s, 2.6, width=0.3, depth=0.35, wobble=0.15, seed=2)
    elif P["pattern"] == "saddle":  # dark back blanket (german shepherd, jackal, beagle)
        def pat(Q):
            y = Q[:, 1] / s
            z = Q[:, 2] / s
            d = np.clip((y - (backY - 0.55 * chD + 0.08 * np.sin(z * 5))) / 0.18, 0, 1) * np.clip((1.75 * BL - np.abs(z - 0.2 * BL)) / 0.3, 0, 1)
            return 1 - 0.8 * d
    elif P["pattern"] == "stripes":  # aardwolf / striped hyena / thylacine
        pat = stripes(lambda Q: Q[:, 2] / s, 2.2, width=0.28, depth=0.7, wobble=0.1, seed=1,
                      region=lambda Q: np.clip((Q[:, 1] / s - legH * 0.4) / 0.6, 0, 1))
    stock = P["stock"]

    def legshade(Q):  # dark "stockings" on the lower legs (fox, coyote)
        if stock <= 0:
            return np.ones(len(Q))
        t = np.clip((legH * 0.75 - Q[:, 1] / s) / (legH * 0.4), 0, 1)
        return 1 - stock * t

    def skin(extra=None):
        return combine(back_shade, pat, extra)

    # ---------------------------------------------------------------- torso
    W = P["tuck"]
    torso = ellipsoid(0.47 * G, 0.5 * chD, 0.9 * BL, T(v(0, legH + 0.5 * chD, zc + 0.1)))                         # ribcage
    torso = torso.su(ellipsoid(0.4 * G, 0.42 * chD, 0.4, T(v(0, legH + 0.48 * chD, zc - 0.65 * BL))), 0.3)          # brisket / prosternum
    wy = 0.33 * chD * W
    torso = torso.su(ellipsoid(0.36 * G, wy, 0.75 * BL, T(v(0, backY - 0.04 - wy - 0.25 * SL, 0.3 * BL))), 0.45)     # loin / waist
    torso = torso.su(ellipsoid(0.43 * G * P['hips'], 0.4 * chD, 0.55 * BL, T(v(0, backY - 0.4 * chD - SL, zr))), 0.4)               # rump
    torso = torso.su(ellipsoid(0.33 * G * P['hips'], 0.24, 0.5 * BL, T(v(0, backY - 0.2 - SL, zr + 0.05))), 0.3)                 # croup
    torso = torso.su(ellipsoid(0.18 * G, 0.48 * chD, 0.34, T(v(0.3 * G, legH + 0.62 * chD, zc - 0.35 * BL))).mirror_x(), 0.22)  # scapulae
    torso = torso.su(ellipsoid(0.26 * G, 0.5 * chD, 0.45, T(v(0.26 * G * P['hips'], backY - 0.5 * chD - SL, zr + 0.05))).mirror_x(), 0.3)  # hip muscle
    nb = v(0, backY - 0.15, zc - 0.75 * BL)
    torso = torso.su(round_cone(T(v(0, backY - 0.35, zc - 0.2)), T(nb + v(0, 0.3 * P["neck"], -0.3 * P["neck"])), 0.44 * G * s, 0.36 * s * max(G, 0.9) ** 0.5), 0.3)  # neck root
    if SL > 0:  # hyena: high withers
        torso = torso.su(ellipsoid(0.32 * G, 0.4, 0.6, T(v(0, backY - 0.1, zc - 0.1))), 0.3)
    if P["mane"] > 0:  # crest along the spine (hyena, aardwolf, maned wolf)
        mn = P["mane"]
        for i in range(7):
            z = zc - 0.4 + i * 0.36 * BL
            y = backY + 0.05 - SL * (i / 6.0) * 1.0
            torso = torso.su(round_cone(T(v(0, y - 0.25, z)), T(v(0, y + 0.18 * mn, z + 0.12)), 0.13 * s, 0.03 * s), 0.12)
    if P["ruff"] > 0 and P["heads"] == 1:  # thick neck / chest ruff (wolf, husky, samoyed)
        rf = P["ruff"]
        torso = torso.su(ellipsoid(0.5 * G * (1 + 0.25 * rf), 0.55 * chD * (0.8 + 0.2 * rf), 0.5 * (1 + 0.3 * rf), T(v(0, legH + 0.62 * chD, zc - 0.55 * BL))), 0.3)
    torso = furry(torso, 1.0, 6.0, 1)
    H.piece("Torso", "Body", torso, col="primary", mat="skin", tris=2600, res=128, pattern=skin())
    # markings on the torso
    oT = 0.05 * s
    if "bib" in marks:  # throat / chest / belly
        reg = ellipsoid(0.7 * G, 0.6 * chD, 0.7, T(v(0, legH + 0.25 * chD, zc - 0.55 * BL)))
        reg = reg.noise(0.04 * s, 7 / s, 3)
        H.piece("Bib", "Body", overlay(torso, reg, oT), col=marks["bib"], tris=900, role="body", pri=1.2)
    if "saddle" in marks:
        reg = (ellipsoid(1.2 * G, 0.75 * chD, 1.55 * BL, T(v(0, backY + 0.15 - 0.5 * SL, 0.15 * BL)))).noise(0.05 * s, 6 / s, 4)
        H.piece("Saddle", "Body", overlay(torso, reg, oT), col=marks["saddle"], tris=1000, role="body", pri=1.2)
    if "stripe" in marks:  # skunk-like dorsal stripe (unused for dogs, kept for variants)
        reg = box(0.18 * G * s, 1.0 * s, 2.0 * BL * s, T(v(0, backY, 0.2)))
        H.piece("Stripe", "Body", overlay(torso, reg, oT), col=marks["stripe"], tris=600, role="body", pri=1.2)

    # ---------------------------------------------------------------- legs
    pw = P["paws"]
    lt = LT

    def paw(c, front=True):
        c = A(*c)
        k = pw * s
        p = ellipsoid(0.15 * k, 0.09 * k, 0.16 * k, T(c + A(0, 0.09, -0.02) * k))
        for dx, dz in ((-0.1, -0.12), (-0.035, -0.17), (0.035, -0.17), (0.1, -0.12)):
            p = p.su(ellipsoid(0.062 * k, 0.06 * k, 0.07 * k, T(c + A(dx, 0.065, dz - 0.02) * k)), 0.035)
        p = p.su(ellipsoid(0.1 * k, 0.06 * k, 0.08 * k, T(c + A(0, 0.06, 0.08) * k)), 0.05)          # heel pad
        return p & plane((0, -1, 0), 0.0)

    sh = v(0.29 * G, legH + 0.55 * chD, zc - 0.85 * BL)
    el = v(0.3 * G, legH + 0.04, zc - 0.5 * BL)
    wr = v(0.28 * G, max(0.3 * legH, 0.24), zc - 0.58 * BL)
    fpaw = A(wr[0], 0, wr[2] - 0.08 * s)
    H.mbone("ShoulderF#", "Body", T(sh))
    H.mbone("ElbowF#", "ShoulderF#", T(el))
    H.mbone("WristF#", "ElbowF#", T(wr))
    up = round_cone(T(sh + v(0.0, 0.25 * chD, 0.2)), T(el), 0.27 * G * s * lt, 0.15 * s * lt)
    up = up.su(ellipsoid(0.17 * G * lt, 0.4 * chD, 0.3, T((sh + el) / 2 + v(0.01, 0, 0.1))), 0.2)   # triceps
    up = up.su(sphere(0.13 * s * lt, T(el + v(0, 0.02, 0.07))), 0.08)                             # olecranon
    H.mpiece("UpperF#", "ShoulderF#", furry(up, 0.7, 8, 2), col="primary", tris=800, role="limb", pattern=skin())
    fo = round_cone(T(el), T(wr + v(0, 0.02, 0)), 0.13 * s * lt * pw ** 0.3, 0.085 * s * lt * pw ** 0.5)
    fo = fo.su(ellipsoid(0.11 * lt, 0.32 * LG, 0.12 * lt, T(el + v(0, -0.25 * LG, -0.02))), 0.1)
    if P["poodle"]:
        fo = fo.su(ellipsoid(0.17, 0.16, 0.17, T(wr + v(0, 0.18, 0))).noise(0.025 * s, 14 / s, 6), 0.03)   # pom bracelet
    H.mpiece("ForeF#", "ElbowF#", furry(fo, 0.5, 10, 3), col="primary", tris=600, role="limb", pattern=skin(legshade))
    pf = round_cone(T(wr), T(fpaw + v(0, 0.1, -0.02)), 0.085 * s * lt * pw ** 0.5, 0.1 * s * pw)
    pf = pf.su(paw(fpaw), 0.06)
    socks = P["socks"]
    H.mpiece("PawF#", "WristF#", furry(pf, 0.3, 12, 4), col=socks or "primary", tris=550, role="foot",
             pattern=None if socks else skin(lambda Q: legshade(Q) * 0.97))

    hp = v(0.28 * G * P['hips'], backY - 0.42 * chD - SL, zr)
    kn = v(0.33 * G * P['hips'], legH * 0.93 + 0.05 - 0.3 * SL, zr - 0.38 * BL ** 0.5)
    hk = v(0.3 * G * P['hips'], max(0.42 * legH, 0.3), zr + 0.4 * LG ** 0.5)
    bpaw = A(hk[0], 0, hk[2] - 0.12 * s)
    H.mbone("HipB#", "Body", T(hp))
    H.mbone("KneeB#", "HipB#", T(kn))
    H.mbone("HockB#", "KneeB#", T(hk))
    th = round_cone(T(hp + v(0, 0.2, 0.1)), T(kn), 0.36 * G * s * lt, 0.17 * s * lt)
    th = th.su(ellipsoid(0.24 * G * lt, 0.5 * (hp[1] - kn[1]) / s + 0.1, 0.4 * lt, T((hp + kn) / 2 + v(0.01, 0.0, 0.15))), 0.25)  # thigh mass
    H.mpiece("Thigh#", "HipB#", furry(th, 0.7, 8, 5), col="primary", tris=900, role="limb", pattern=skin())
    sn = round_cone(T(kn), T(hk), 0.15 * s * lt, 0.085 * s * lt)
    sn = sn.su(ellipsoid(0.12 * lt, 0.3 * LG, 0.15 * lt, T(kn + v(0, -0.15 * LG, 0.14))), 0.12)        # gastrocnemius
    sn = sn.su(sphere(0.09 * s * lt, T(hk + v(0, 0.02, 0.06))), 0.06)                                   # point of hock
    if P["poodle"]:
        sn = sn.su(ellipsoid(0.17, 0.16, 0.17, T(hk + v(0, -0.08, -0.02))).noise(0.025 * s, 14 / s, 7), 0.03)
    H.mpiece("Shin#", "KneeB#", furry(sn, 0.5, 10, 6), col="primary", tris=650, role="limb", pattern=skin(legshade))
    pb = round_cone(T(hk), T(bpaw + v(0, 0.1, 0.0)), 0.085 * s * lt * pw ** 0.5, 0.095 * s * pw)
    pb = pb.su(paw(bpaw), 0.06)
    H.mpiece("PawB#", "HockB#", furry(pb, 0.3, 12, 7), col=socks or "primary", tris=550, role="foot",
             pattern=None if socks else skin(lambda Q: legshade(Q) * 0.97))

    # ---------------------------------------------------------------- neck(s) and head(s)
    NK = P["neck"]
    heads = []
    nheads = P["heads"]
    offs = [(0.0, 0.0)] if nheads == 1 else [(0.0, 0.0), (0.7, -30.0), (-0.7, 30.0)][:nheads]
    for hi, (hx, yaw) in enumerate(offs):
        sfx = "" if hi == 0 else ("R" if hx > 0 else "L")
        side_head = hi > 0
        nkb = nb + v(hx * 0.6, 0, 0)
        hc = nkb + v(hx * 0.8, 0.72 * NK, -0.7 * NK - 0.08)
        H.bone("Neck" + sfx, "Body", T(nkb))
        neckR = 0.36 * s * max(G, 0.85) ** 0.6 * (0.8 if side_head else 1.0)
        neck = tube([T(nkb + v(-hx * 0.4, -0.3, 0.3)), T(nkb + v(hx * 0.3, 0.38 * NK, -0.22 * NK)), T(hc + v(0, -0.05, 0.12))],
                    [neckR * 1.15, neckR, 0.27 * s * HS], k=0.2)
        if P["ruff"] > 0:
            rf = P["ruff"]
            neck = neck.su(ellipsoid(0.38 * rf + 0.25, 0.35 * rf + 0.3, 0.32 * rf + 0.25, T(nkb + v(hx * 0.3, 0.25 * NK, -0.25 * NK))), 0.25)
        neck = furry(neck, 1.0, 7.0, 10 + hi)
        H.piece("NeckP" + sfx, "Neck" + sfx, neck, col="primary", tris=900 if not side_head else 700, role="limb", pattern=skin())
        if "bib" in marks:
            nrm = A(0, 0.7, 0.72) / np.linalg.norm(A(0, 0.7, 0.72))
            mid = nkb + v(hx * 0.3, 0.36 * NK, -0.35 * NK)
            reg = plane(T(nrm), float(mid @ nrm) - 0.08 * s).noise(0.04 * s, 7 / s, 3)
            H.piece("Throat" + sfx, "Neck" + sfx, overlay(neck, reg, oT * 0.8), col=marks["bib"], tris=500, role="limb", pri=1.3)
        heads.append(_canid_head(H, P, sfx, "Neck" + sfx, T(hc), yaw if side_head else 0.0, side_head, pat, furry))
        if P["collar"] and not side_head:
            c0 = nkb + v(hx * 0.2, 0.2 * NK, -0.12 * NK)
            col = torus(neckR * 1.08, 0.055 * s, axis=1).rot(-40, 0, 0).at(*T(c0))
            spikes = None
            if P["collar"] == "spiked":
                for i in range(8):
                    a = i / 8 * math.tau
                    d = A(math.cos(a), math.sin(a) * 0.77, -math.sin(a) * 0.64)
                    base = c0 + d * neckR * 1.1
                    sp = round_cone(T(base), T(base + d * 0.2 * s), 0.05 * s, 0.008 * s)
                    spikes = sp if spikes is None else spikes | sp
            H.piece("Collar" + sfx, "Neck" + sfx, col, col="red" if P["collar"] != "spiked" else "secondary", mat="cloth" if P["collar"] != "spiked" else "skin",
                    tris=400, role="detail", pri=1.6)
            if spikes is not None:
                H.piece("Spikes" + sfx, "Neck" + sfx, spikes, col="metal", mat="metal", tris=500, role="detail", pri=2.0, ao=False)
            elif not side_head and P["collar"] == "tag":
                tg = c0 + A(0, -neckR * 0.77 * 1.12 - 0.07 * s, -neckR * 0.64 * 1.12)
                H.prim("Tag", "Neck", "Cylinder", (0.03 * s, 0.14 * s, 0.14 * s), T(tg), rot=(0, math.pi / 2, 0), col="gold", mat="metal", pri=2.2)

    # ---------------------------------------------------------------- tail
    TL, TT = P["tail_len"], P["tail_thick"]
    tt = P["tail"]
    t0 = v(0, backY - 0.2 - SL, zr + 0.48 * BL)
    if tt == "curl":
        dirs = [A(0, 0.55, 0.25), A(0, 0.3, -0.35), A(0.12, -0.15, -0.38)]
        radii = [0.13, 0.17, 0.16, 0.08]
    elif tt == "up":
        dirs = [A(0, 0.45, 0.45), A(0, 0.5, 0.18), A(0, 0.4, -0.02)]
        radii = [0.11, 0.095, 0.07, 0.035]
    elif tt == "sickle":
        dirs = [A(0, 0.25, 0.55), A(0, 0.45, 0.3), A(0, 0.25, -0.2)]
        radii = [0.12, 0.16, 0.15, 0.06]
    elif tt == "whip":
        dirs = [A(0, -0.35, 0.55), A(0, -0.75, 0.25), A(0, -0.45, 0.35)]
        radii = [0.07, 0.05, 0.035, 0.02]
    elif tt == "otter":
        dirs = [A(0, -0.25, 0.6), A(0, -0.55, 0.35), A(0, -0.45, 0.2)]
        radii = [0.15, 0.11, 0.075, 0.035]
    elif tt == "brush":  # fox: long, thick, nearly level
        dirs = [A(0, -0.35, 0.55), A(0, -0.42, 0.62), A(0, -0.25, 0.65)]
        radii = [0.13, 0.25, 0.27, 0.12]
    elif tt == "bob":
        dirs = [A(0, 0.05, 0.22), A(0, 0.0, 0.08), A(0, -0.05, 0.05)]
        radii = [0.13, 0.1, 0.06, 0.03]
    elif tt == "pom":  # poodle: short straight up with a pompom
        dirs = [A(0, 0.4, 0.2), A(0, 0.35, 0.05), A(0, 0.25, 0.0)]
        radii = [0.08, 0.06, 0.05, 0.05]
    elif tt == "snake":  # orthrus / cerberus serpent tail
        dirs = [A(0, -0.2, 0.6), A(0, -0.55, 0.45), A(0, -0.1, 0.6)]
        radii = [0.12, 0.1, 0.08, 0.04]
    else:  # hang: wolf / dog low bushy tail
        dirs = [A(0, -0.4, 0.5), A(0, -0.62, 0.22), A(0, -0.5, 0.08)]
        radii = [0.12, 0.15, 0.13, 0.06]
    pts = [t0]
    for d in dirs:
        pts.append(pts[-1] + d * TL * s)
    H.bone("Tail1", "Body", T(pts[0]))
    H.bone("Tail2", "Tail1", T(pts[1]))
    H.bone("Tail3", "Tail2", T(pts[2]))
    r = [x * TT * s for x in radii]
    tailfl = 1.6 if tt in ("brush", "hang", "sickle", "curl") else 0.6
    tA = round_cone(T(pts[0] - (pts[1] - pts[0]) * 0.35), T(pts[1]), r[0], r[1])
    tB = round_cone(T(pts[1]), T(pts[2]), r[1], r[2])
    tC = round_cone(T(pts[2]), T(pts[3]), r[2], r[3])
    if tt == "pom":
        tC = tC.su(sphere(0.22 * s * TT, T(pts[3])).noise(0.03 * s, 12 / s, 8), 0.05)
    tcol = "primary"
    H.piece("TailA", "Tail1", furry(tA, tailfl, 8, 20), col=tcol, tris=450, role="tail", pri=1.5, pattern=skin())
    if tt != "bob":
        H.piece("TailB", "Tail2", furry(tB, tailfl, 8, 21), col=tcol, tris=450, role="tail", pri=1.7, pattern=skin())
        tip_col = marks.get("tailtip")
        if tip_col:  # tip piece in the marking colour, base of segment C in primary
            cut = sphere(0.36 * s * TL * max(TT, 1.0), T(pts[3]))
            H.piece("TailC", "Tail3", furry(tC - cut, tailfl, 8, 22), col=tcol, tris=400, role="tail", pri=1.9, pattern=skin())
            H.piece("TailTip", "Tail3", furry(tC & cut.round(0.02 * s), tailfl, 8, 22), col=tip_col, tris=400, role="tail", pri=1.9)
        else:
            H.piece("TailC", "Tail3", furry(tC, tailfl, 8, 22), col=tcol, tris=400, role="tail", pri=1.9,
                    pattern=skin(lambda Q: np.where(np.linalg.norm(Q - pts[3], axis=1) < 0.3 * s, 0.4, 1.0)) if P["pattern"] in ("stripes",) else skin())

    # ---------------------------------------------------------------- saddle (mounts)
    if P["mount"] and P.get("mount_len"):
        pass                                     # fitted tack + clips are added by MK.rig_mount after the legs / head exist
    elif P["mount"]:
        st = v(0, backY + 0.02, -0.15 * BL)
        sd = P["saddle"] or "saddle"
        seat = round_box(0.42 * G * s, 0.09 * s, 0.5 * s, 0.07 * s, T(st + v(0, 0.12, 0)))
        seat = seat.su(round_box(0.3 * G * s, 0.14 * s, 0.08 * s, 0.05 * s, T(st + v(0, 0.22, -0.45))), 0.05)    # pommel
        seat = seat.su(round_box(0.36 * G * s, 0.16 * s, 0.07 * s, 0.05 * s, T(st + v(0, 0.24, 0.46))), 0.05)    # cantle
        seat = seat & torso.round(0.32 * s)
        seat = seat - torso.round(0.06 * s)
        H.piece("SaddleSeat", "Body", seat, col=LEATHER, mat="skin", tris=900, role="saddle", pri=1.4)
        blanket = overlay(torso, box(0.95 * G * s, 0.42 * s, 0.68 * s, T(st + v(0, 0.2, 0))), 0.045 * s)
        if sd == "goblin":  # ragged hide blanket + bone trim
            blanket = blanket.noise(0.03 * s, 9 / s, 30)
        H.piece("Blanket", "Body", blanket, col="secondary", mat="cloth", tris=800, role="saddle", pri=1.3)
        girth_ = overlay(torso, box(0.98 * G * s, 1.6 * s, 0.09 * s, T(st + v(0, -0.5, 0.15))), 0.065 * s)
        H.piece("Girth", "Body", girth_, col=LEATHER, mat="skin", tris=600, role="saddle", pri=1.4)
        H.socket("seat", T(st + v(0, 0.3, 0)), "Body")
        H.mount = {"seat": "Torso", "saddle": {"pos": T(st + v(0, 0.22, 0)), "size": T(v(0.9 * G, 0.25, 1.1))}}

    # ---------------------------------------------------------------- rig and motion
    legs = [("ShoulderFR", "ElbowFR", "WristFR", True, 1), ("ShoulderFL", "ElbowFL", "WristFL", True, -1),
            ("HipBR", "KneeBR", "HockBR", False, 1), ("HipBL", "KneeBL", "HockBL", False, -1)]
    main = heads[0]
    H.socket("mouth", main["mouth"], main["jaw"])
    H.socket("head", main["top"], main["head"])
    ears = [e for h in heads for e in h["ears"]]
    H.rig.update({"head": main["head"], "jaw": main["jaw"], "tail": ["Tail1", "Tail2", "Tail3"]})
    height = backY * s + 0.5
    MC.quad(H, legs, neck=main["neck"], head=main["head"], jaw=main["jaw"], tail=["Tail1", "Tail2", "Tail3"], ears=ears,
            heads=[(h["neck"], h["head"], h["jaw"]) for h in heads], height=height, gait=P["gait"],
            stride=0.4 if LG > 0.7 else 0.5, walk=0.62 * (0.75 + 0.25 * LG) * (s ** 0.3), attack=P["attack"], wag=P["wag"],
            floppy=P["ear"] in ("floppy", "long"))
    if P["mount"] and P.get("mount_len"):
        k = P.get("scale", 1.0)
        MK.scale_hero(H, k)
        fp_, bp_ = fpaw * k, bpaw * k
        soles = {"WristFR": fp_, "WristFL": fp_ * A(-1, 1, 1), "HockBR": bp_, "HockBL": bp_ * A(-1, 1, 1)}
        MK.rig_mount(H, MK.scale_sdf(torso, k), -0.15 * BL * s * k, legs, soles, height * k, P["mount_len"],
                     walk=(1.2 * (s * k) ** 0.3, "walk", "walk", 2.6 * s * k, 0.45 * s * k),
                     run=(0.62 * (s * k) ** 0.3, "bound", "bound", 6.2 * s * k, 0.75 * s * k),
                     neck=main["neck"], head=main["head"], jaw=main["jaw"], tail=["Tail1", "Tail2", "Tail3"], ears=ears,
                     pad_col=P.get("pad_col", "secondary"), ytop=(backY + 3) * s * k, curl=0.7)
    return H


def _canid_head(H, P, sfx, neck_bone, hc, yaw, light, pat, furry):
    """Builds one head (bones Head<sfx>, Jaw<sfx>, Ear#<sfx>) at pivot hc. The skull is sculpted in head-local units
    (1 = one head unit, -Z forward) and placed with W(); bones / prims use hw(). Returns rig names + socket points."""
    s = P["s"]
    hs = P["head"] * s * 1.2
    M, MW, DM, J = P["muzzle"], P["mw"], P["dome"], P["jowls"]
    E = P["eye"]
    hc = A(*hc)
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

    def hw(x, y, z):  # head-local -> model point (yawed for side heads)
        x, z = x * cy + z * sy, -x * sy + z * cy
        return T(hc + A(x, y, z) * hs)

    def W(sd):  # head-local sculpt -> model space
        sd = sd.scale(hs)
        if yaw:
            sd = sd.rot(0, yaw, 0)
        return sd.at(*T(hc))

    hb = H.bone("Head" + sfx, neck_bone, T(hc))
    mz = 0.62 * M  # muzzle length beyond the stop
    # cranium
    head = ellipsoid(0.34 * (1 + 0.15 * DM), 0.31 * (1 + 0.35 * DM), 0.4 * (1 + 0.1 * DM), (0, 0.08 + 0.06 * DM, -0.2))
    head = head.su(sphere(0.18, (0, 0.12, 0.03)), 0.12)                                                      # occiput
    head = head.su(ellipsoid(0.15, 0.14, 0.2, (0.2, -0.04, -0.36)).mirror_x(), 0.12)                          # zygomatic arches
    head = head.su(ellipsoid(0.22 * (1 + 0.2 * DM), 0.18, 0.19, (0, 0.15 + 0.05 * DM, -0.43)), 0.1)           # stop / forehead
    # muzzle (top line slopes gently down from the stop), a little taller than wide
    mt = A(0, -0.02 - 0.04 * M, -0.04 - mz)
    muz = round_cone((0, 0, 0), T(mt), 0.17 * MW, 0.115 * MW * (0.7 + 0.3 * min(M, 1))).scale3(1, 1.15, 1).at(0, -0.075, -0.48)
    head = head.su(muz, 0.1)
    # flews / upper lips (jowls), brows, eye sockets
    head = head.su(ellipsoid(0.1 * MW + 0.03 * J, 0.1 + 0.08 * J, 0.22 * M + 0.12, (0.09 * MW, -0.14 - 0.07 * J, -0.5 - 0.6 * mz)).mirror_x(), 0.07)
    head = head.su(capsule((0.07, 0.2, -0.47), (0.21, 0.17, -0.45), 0.05).mirror_x(), 0.06)
    head = head.ss(sphere(0.07 * E + 0.01, (0.165, 0.1, -0.52)).mirror_x(), 0.04)
    if P["wrinkles"] > 0:
        for i in range(3):
            head = head.su(capsule((-0.15, 0.22 - i * 0.06, -0.5 - 0.02 * i), (0.15, 0.22 - i * 0.06, -0.5 - 0.02 * i), 0.022 * P["wrinkles"]), 0.03)
        head = head.su(ellipsoid(0.24 * MW, 0.055, 0.07, (0, 0.03, -0.55 - 0.6 * mz)), 0.05)              # nose roll
    headW = furry(W(head), 0.35, 12, 30 + len(sfx))
    if light and P["ear"] != "none":  # side heads: ears fused into the skull (saves parts)
        ep = (0.17 + 0.04 * P["ear_w"], 0.31, -0.18)
        esh = _ear_shape(P["ear"], P["ear_size"], P["ear_w"], hs, False)
        for sx in (1, -1):
            e = esh if sx > 0 else _mirror_sdf(esh)
            if yaw:
                e = e.rot(0, yaw, 0)
            headW = headW.su(e.at(*hw(sx * ep[0], ep[1], ep[2])), 0.03 * hs)
    H.piece("HeadP" + sfx, "Head" + sfx, headW, col="primary", tris=2000 if not light else 1500, res=128, role="head", pattern=pat)
    marks = P["marks"] or {}
    oH = 0.022 * s
    reg = None
    mk = None
    if "mask" in marks:  # husky / wolf: pale lower muzzle, cheeks, eyebrow spots, throat
        reg = ellipsoid(0.34 * MW, 0.22, 0.32 + mz, (0, -0.14, -0.6 - 0.4 * mz)) & plane((0, 1, 0), -0.06)
        reg = reg | ellipsoid(0.16, 0.12, 0.2, (0.2, -0.06, -0.42)).mirror_x() | ellipsoid(0.3, 0.22, 0.22, (0, -0.25, -0.15))
        if P.get("points", True):
            reg = reg | sphere(0.045, (0.13, 0.25, -0.53)).mirror_x()
        mk = marks["mask"]
    elif "muzzle" in marks:  # lower muzzle / chin colour (rottweiler rust, beagle white, fox white lips)
        reg = ellipsoid(0.34 * MW, 0.22, 0.3 + mz, (0, -0.14, -0.6 - 0.45 * mz)) & plane((0, 1, 0), -0.085 - 0.03 * M)
        if P.get("points"):
            reg = reg | sphere(0.05, (0.13, 0.25, -0.53)).mirror_x()
        mk = marks["muzzle"]
    elif "blackmask" in marks:  # pug / mastiff dark muzzle
        reg = ellipsoid(0.3 * MW, 0.24, 0.28 + mz, (0, -0.05, -0.62 - 0.45 * mz)) | ellipsoid(0.11, 0.08, 0.11, (0.17, 0.08, -0.5)).mirror_x()
        reg = reg.noise(0.03, 9, 4)
        mk = marks["blackmask"]
    if reg is not None:
        H.piece("Mask" + sfx, "Head" + sfx, overlay(headW, W(reg.noise(0.015, 10, 5)), oH), col=mk, tris=650, role="head", pri=1.3)
    if "blaze" in marks:  # collie / beagle white stripe up the forehead onto the muzzle
        reg = box(0.05, 0.3, 0.5, (0, 0.2, -0.4)) | ellipsoid(0.3 * MW, 0.25, 0.3 + mz, (0, -0.1, -0.62 - 0.45 * mz))
        H.piece("Blaze" + sfx, "Head" + sfx, overlay(headW, W(reg), oH * 0.8), col=marks["blaze"], tris=600, role="head", pri=1.35)
    # nose leather
    nz = -0.54 - mz
    nose = ellipsoid(0.08 * MW + 0.02, 0.06 + 0.01 * MW, 0.07, (0, -0.02 - 0.04 * M, nz))
    nose = nose.ss(sphere(0.022, (0.04 * MW, -0.04 - 0.04 * M, nz - 0.06)).mirror_x(), 0.01)
    H.piece("Nose" + sfx, "Head" + sfx, W(nose), col=NOSE, mat="skin", tris=250, role="nose", pri=1.6, ao=False)
    # jaw
    jb = H.bone("Jaw" + sfx, "Head" + sfx, hw(0, -0.1, -0.3))
    ub = P["underbite"]
    jl = mz * 0.9 + 0.08 + ub
    jaw = ellipsoid(0.11 * MW, 0.065, 0.12 + 0.45 * jl, (0, -0.2 - 0.04 * M, -0.42 - 0.5 * jl))
    jaw = jaw.su(capsule((0.13, -0.12, -0.3), (0.08 * MW, -0.19, -0.42 - 0.6 * jl), 0.055).mirror_x(), 0.06)
    jaw = jaw.su(ellipsoid(0.085 * MW, 0.06, 0.07, (0, -0.22 - 0.04 * M, -0.44 - 0.9 * jl)), 0.05)          # chin
    jcol = marks.get("muzzle", marks.get("mask", marks.get("blackmask", "primary")))
    H.piece("JawP" + sfx, "Jaw" + sfx, furry(W(jaw), 0.2, 14, 40), col=jcol, tris=500, role="jaw", pri=1.4)
    if not light:
        H.prim("Mouth" + sfx, "Jaw" + sfx, "Ellipsoid", (0.16 * MW * hs, 0.05 * hs, (0.15 + 0.85 * jl) * hs), hw(0, -0.135 - 0.03 * M, -0.42 - 0.5 * jl),
               rot=(0, yaw, 0), col="mouth", mat="hard", role="mouth", pri=2.4)
    if P["tongue"] and not light:
        tg = ellipsoid(0.085 * MW, 0.025, 0.12 + 0.35 * jl, (0.02, -0.15 - 0.03 * M, -0.5 - 0.62 * jl))
        tg = tg.su(ellipsoid(0.07, 0.11, 0.035, (0.05, -0.24 - 0.03 * M, -0.5 - 1.05 * jl)), 0.04)     # lolling tip over the lip
        H.piece("Tongue" + sfx, "Jaw" + sfx, W(tg), col="tongue", mat="skin", tris=300, role="tongue", pri=2.0, ao=False)
    fgl = 0.06 + 0.07 * P["fangs"]
    if P["fangs"] > 0 and not light:
        fang = round_cone((0.075 * MW, -0.12 - 0.04 * M, -0.47 - 0.85 * mz), (0.07 * MW, -0.12 - 0.04 * M - fgl, -0.48 - 0.85 * mz), 0.025 * (0.6 + 0.4 * P["fangs"]), 0.006)
        H.mpiece("Fang#" + sfx, "Head" + sfx, W(fang), col="tooth", mat="hard", tris=150, role="tooth", pri=2.2, ao=False, smooth=2)
    if ub > 0 and not light:  # bulldog lower canines poking up
        lf = round_cone((0.055 * MW, -0.17, -0.44 - 0.95 * jl), (0.055 * MW, -0.1, -0.45 - 0.95 * jl), 0.017, 0.005)
        H.mpiece("LowFang#" + sfx, "Jaw" + sfx, W(lf), col="tooth", mat="hard", tris=150, role="tooth", pri=2.2, ao=False, smooth=2)
    # eyes
    ex, ey, ez = 0.165, 0.1, -0.525
    er = 0.065 * E * hs
    if yaw == 0:
        H.eyes("Head" + sfx, hw(ex, ey, ez), er, col=P["eyecol"], pupil=P["pupil"], shine=P.get("shine", True), look=(0.35, 0.08, -1.0))
    else:
        for sx, tag in ((1, "R"), (-1, "L")):
            c = A(*hw(sx * ex, ey, ez))
            H.prim(f"Eye{tag}{sfx}", "Head" + sfx, "Ball", (er * 2,) * 3, T(c), col=P["eyecol"], mat="hard", pri=1.2, role="eye")
            d = A(*hw(sx * ex * 1.6, ey, ez - 1.0)) - A(*hw(sx * ex, ey, ez))
            d = d / np.linalg.norm(d)
            if P["pupil"]:
                H.prim(f"Pupil{tag}{sfx}", "Head" + sfx, "Ball", (er * 1.05,) * 3, T(c + d * er * 0.8), col="pupil", mat="hard", pri=1.3, role="pupil")
    # ears
    et = P["ear"]
    ES, EW = P["ear_size"], P["ear_w"]
    ears = []
    if et != "none" and not light:
        epos = {"floppy": (0.27, 0.22, -0.22), "long": (0.27, 0.2, -0.22), "rose": (0.25, 0.27, -0.2), "fold": (0.21, 0.32, -0.2)}.get(
            et, (0.17 + 0.04 * EW, 0.31, -0.18))
        shape = _ear_shape(et, ES, EW, hs, P["fluff"] > 0.01)
        for sx, tag in ((1, "R"), (-1, "L")):
            bpos = A(*hw(sx * epos[0], epos[1] + 0.05 * DM, epos[2]))
            bn = H.bone(f"Ear{tag}{sfx}", "Head" + sfx, T(bpos))
            ears.append(bn)
            sh = shape if sx > 0 else _mirror_sdf(shape)
            if yaw:
                sh = sh.rot(0, yaw, 0)
            H.piece(f"Ear{tag}{sfx}", bn, sh.at(*T(bpos)), col=P.get("earcol") or "primary", tris=380 if et != "long" else 450, role="ear", pri=1.5,
                    key=f"h_{H.id}_ear{sfx}".lower().replace(" ", "_") + ("" if sx > 0 else "_l"), mirrored=sx < 0)
    if P["poodle"] and not light:  # topknot
        tk = sphere(0.3, (0, 0.34, -0.2)).noise(0.03, 12, 50) | ellipsoid(0.24, 0.32, 0.2, (0, 0.15, 0.0)).noise(0.03, 12, 51)
        H.piece("Topknot" + sfx, "Head" + sfx, W(tk), col="primary", tris=700, role="hair", pri=1.4)
    return {"neck": neck_bone, "head": hb, "jaw": jb, "ears": ears, "mouth": hw(0, -0.15, -0.6 - mz), "top": hw(0, 0.45, -0.25)}


def _ear_shape(et, ES, EW, hs, fluffy):
    """Right ear (local to its bone at the ear base)."""
    if et in ("erect", "bat", "big", "round"):
        L = {"erect": 0.38, "bat": 0.36, "big": 0.66, "round": 0.22}[et] * ES * hs
        w = {"erect": 0.17, "bat": 0.19, "big": 0.24, "round": 0.16}[et] * EW * ES * hs
        tipr = {"erect": 0.025, "bat": 0.08, "big": 0.045, "round": 0.11}[et] * ES * hs
        th = 0.055 * hs * (1 + 0.25 * (et == "big"))
        outer = round_cone((0, 0, 0), (0, L, 0), w, tipr).scale3(1, 1, th / w)
        outer = outer.su(ellipsoid(w * 0.9, w * 0.5, th * 1.6, (0, w * 0.15, th * 0.3)), 0.03 * hs)      # thick base
        inner = round_cone((0, 0.05 * hs, 0), (0, L * 0.88, 0), w * 0.68, tipr * 0.5).scale3(1, 1, th * 0.6 / w).at(0, 0, -th * 0.85)
        ear = outer.ss(inner, 0.012 * hs)
        if fluffy:
            ear = ear.noise(0.012 * hs, 16 / hs, 61)
        tilt = {"erect": -12, "bat": -26, "big": -22, "round": -18}[et]
        ear = ear.rot(6 if et != "round" else 0, -22, tilt)
        return ear
    if et == "fold":  # terrier button ear: erect base, tip folds forward
        base = round_cone((0, 0, 0), (0, 0.14 * hs * ES, -0.02 * hs), 0.12 * hs * ES, 0.08 * hs * ES).scale3(1, 1, 0.4)
        tip = round_cone((0, 0.14 * hs * ES, -0.02 * hs), (0.03 * hs, 0.04 * hs * ES, -0.12 * hs * ES), 0.08 * hs * ES, 0.035 * hs).scale3(1, 1, 0.45)
        return base.su(tip, 0.03 * hs).rot(0, -15, -22)
    # floppy / long / rose: a flap hanging along the side of the head (thin in x, wide in z)
    Lh = {"floppy": 0.44, "long": 0.85, "rose": 0.2}[et] * ES * hs
    wd = {"floppy": 0.16, "long": 0.19, "rose": 0.12}[et] * EW * ES * hs
    flap = ellipsoid(0.04 * hs, Lh * 0.55, wd, (0.0, -Lh * 0.45, 0.02 * hs))
    flap = flap.su(ellipsoid(0.08 * hs, 0.08 * hs, wd * 0.8, (0, 0, 0)), 0.06 * hs)    # fold at the root
    if fluffy:
        flap = flap.noise(0.02 * hs, 14 / hs, 60)
    if et == "rose":
        return flap.rot(35, 0, 32).at(0.02 * hs, 0, 0.0)
    return flap.rot(8, 0, 9).at(0.03 * hs, 0, 0.0)


# ====================================================================================================== heroes: canids
def PV(primary, secondary, iris="#6B4423", **k):
    d = {"primary": primary, "secondary": secondary, "iris": iris}
    d.update(k)
    return d


@hero("dog", "canines")
def dog():
    return _canid("dog", ear="floppy", tail="up", tail_len=0.95, tongue=True, wag=0.45, collar="tag", head=1.05, muzzle=0.85,
                  marks={"bib": "secondary", "muzzle": "secondary"}, preview=PV("#C08A52", "#F2E3CC"))


@hero("wolf", "canines")
def wolf():
    return _canid("wolf", scale=1.4, mount=True, mount_len=8.4, pad_col=[0.3, 0.36, 0.5], ear="erect", ear_size=1.12, tail="hang", tail_thick=1.25, ruff=0.6, fluff=0.012, girth=0.95, leg=1.08, muzzle=1.05, belly=0.75,
                  marks={"bib": "secondary", "mask": "secondary"}, eyecol="gold", wag=0.0, preview=PV("#6E6E70", "#D6D2CC", "#D9A13B", gold="#D9A13B"))


@hero("fox", "canines")
def fox():
    return _canid("fox", ear="erect", ear_size=1.25, ear_w=1.1, tail="brush", tail_len=1.25, tail_thick=1.05, muzzle=1.1, mw=0.8, head=0.95,
                  girth=0.82, leg=0.8, body=0.95, fluff=0.008, stock=0.75, socks=None, pupil="slit",
                  marks={"bib": "secondary", "muzzle": "secondary", "tailtip": "secondary"}, eyecol="gold",
                  preview=PV("#D8642A", "#FFFFFF", gold="#D9A13B"))


@hero("pug", "canines")
def pug():
    return _canid("pug", s=0.8, ear="rose", ear_size=1.2, tail="curl", tail_len=0.6, tail_thick=0.8, muzzle=0.18, mw=1.15, head=1.45, dome=0.6,
                  eye=1.45, wrinkles=1.0, neck=0.55, girth=1.1, hips=0.9, leg=0.7, body=0.8, chest=0.85, tuck=1.25, lt=1.15, tongue=True, wag=0.3,
                  marks={"blackmask": "secondary"}, earcol="secondary", preview=PV("#D9B98A", "#2B2420"))


@hero("dachshund", "canines")
def dachshund():
    return _canid("dachshund", ear="long", ear_size=0.75, tail="whip", tail_len=0.85, tail_thick=1.4, muzzle=1.2, mw=0.85, head=1.0, eye=1.1,
                  leg=0.38, body=1.35, chest=0.95, tuck=1.3, lt=1.15, girth=0.85, wag=0.4, collar="tag", preview=PV("#8A4A22", "#3A1E10"))


@hero("husky", "canines")
def husky():
    return _canid("husky", ear="erect", ear_size=0.95, tail="curl", tail_thick=1.35, ruff=0.5, fluff=0.012, belly=0.8,
                  marks={"bib": "secondary", "mask": "secondary"}, socks="secondary", eyecol=[0.45, 0.7, 0.95], wag=0.25,
                  preview=PV("#6E7480", "#F2F2F2"))


@hero("puppy", "canines")
def puppy():
    return _canid("puppy", s=0.75, head=1.55, dome=0.55, muzzle=0.55, mw=1.05, eye=1.45, ear="floppy", ear_size=1.15, leg=0.72, body=0.72,
                  chest=0.9, tuck=1.3, paws=1.45, lt=1.2, neck=0.6, tail="up", tail_len=0.7, tail_thick=1.1, tongue=True, wag=0.7,
                  marks={"bib": "secondary", "muzzle": "secondary"}, preview=PV("#D9A56B", "#FFF1DE"))


@hero("golden retriever", "canines")
def golden_retriever():
    return _canid("golden retriever", ear="floppy", ear_size=1.1, tail="hang", tail_thick=1.35, tail_len=1.05, fluff=0.014, ruff=0.35,
                  head=1.05, muzzle=0.9, mw=1.05, girth=1.02, tongue=True, wag=0.45, marks={"bib": "secondary"}, collar="tag",
                  preview=PV("#E0A84A", "#F5DEB0"))


@hero("labrador", "canines")
def labrador():
    return _canid("labrador", ear="floppy", ear_size=0.9, tail="otter", tail_len=1.05, head=1.08, muzzle=0.85, mw=1.12, girth=1.08, lt=1.08,
                  tongue=True, wag=0.45, collar="tag", preview=PV("#2E2016", "#E2C08A"))


@hero("german shepherd", "canines")
def german_shepherd():
    return _canid("german shepherd", ear="erect", ear_size=1.32, ear_w=1.05, tail="hang", tail_thick=1.2, tail_len=1.1, slope=0.18, fluff=0.008,
                  muzzle=1.05, head=1.05, leg=1.02, body=1.05, marks={"saddle": "secondary", "blackmask": "secondary"}, belly=0.95,
                  preview=PV("#B07A40", "#1E1610"))


@hero("bulldog", "canines")
def bulldog():
    return _canid("bulldog", s=0.85, ear="rose", ear_size=1.0, tail="bob", tail_thick=0.8, muzzle=0.15, mw=1.5, head=1.65, dome=0.25, jowls=1.0,
                  wrinkles=1.2, underbite=0.12, eye=1.0, girth=1.22, hips=0.72, chest=0.95, leg=0.62, body=0.8, tuck=1.2, lt=1.65, paws=1.3, slope=-0.12, neck=0.4,
                  marks={"bib": "secondary"}, tongue=False, preview=PV("#C8996A", "#F2E8DC"))


@hero("french bulldog", "canines")
def french_bulldog():
    return _canid("french bulldog", s=0.72, ear="bat", ear_size=1.25, tail="bob", tail_thick=0.7, muzzle=0.16, mw=1.25, head=1.5, dome=0.5,
                  wrinkles=0.7, eye=1.3, girth=1.05, hips=0.85, chest=0.85, leg=0.7, body=0.76, tuck=1.15, lt=1.4, paws=1.2, neck=0.5,
                  marks={"blackmask": "secondary"}, preview=PV("#CFC0B0", "#2A2420"))


@hero("corgi", "canines")
def corgi():
    return _canid("corgi", s=0.85, ear="erect", ear_size=1.35, ear_w=1.2, tail="bob", leg=0.42, body=1.12, chest=1.0, tuck=1.3, girth=1.05,
                  lt=1.2, head=1.15, muzzle=0.85, fluff=0.01, ruff=0.3, tongue=True, wag=0.35,
                  marks={"bib": "secondary", "muzzle": "secondary", "blaze": "secondary"}, socks="secondary", preview=PV("#D98A3A", "#FFF4E6"))


@hero("chihuahua", "canines")
def chihuahua():
    return _canid("chihuahua", s=0.6, ear="big", ear_size=0.95, ear_w=1.1, head=1.7, dome=1.0, muzzle=0.42, mw=0.85, eye=1.6, leg=0.95,
                  lt=0.82, body=0.76, girth=0.76, chest=0.76, tuck=0.85, neck=0.7, tail="sickle", tail_thick=0.55, tail_len=0.8, wag=0.3,
                  preview=PV("#D9B07A", "#F3E2C8"))


@hero("poodle", "canines")
def poodle():
    return _canid("poodle", s=0.85, poodle=True, ear="long", ear_size=0.75, tail="pom", tail_len=0.8, fluff=0.012, ruff=0.9, leg=1.12, lt=0.8,
                  body=0.82, girth=0.85, tuck=0.8, head=0.95, muzzle=1.15, mw=0.75, neck=1.05, preview=PV("#F2EDE6", "#D8CFC2"))


@hero("great dane", "canines")
def great_dane():
    return _canid("great dane", s=1.15, ear="floppy", ear_size=0.85, tail="whip", tail_len=1.2, tail_thick=1.5, leg=1.25, chest=1.08, tuck=0.8,
                  girth=0.92, lt=1.05, head=1.25, muzzle=0.95, mw=1.0, jowls=0.8, neck=1.0, preview=PV("#7C7F86", "#2C2C30"))


@hero("greyhound", "canines")
def greyhound():
    return _canid("greyhound", ear="rose", ear_size=1.0, tail="whip", tail_len=1.35, leg=1.18, chest=1.12, tuck=0.5, girth=0.76, lt=0.75,
                  head=0.88, muzzle=1.3, mw=0.72, neck=1.15, body=1.02, preview=PV("#9A9A9E", "#E8E6E2"))


@hero("dalmatian", "canines")
def dalmatian():
    return _canid("dalmatian", ear="floppy", ear_size=0.85, tail="whip", tail_thick=1.4, tail_len=1.1, leg=1.05, girth=0.92, pattern="dalmatian",
                  belly=1.0, wag=0.4, collar="tag", preview=PV("#F7F7F5", "#1A1A1A"))


@hero("beagle", "canines")
def beagle():
    return _canid("beagle", s=0.8, ear="long", ear_size=0.62, ear_w=1.05, tail="up", tail_len=0.8, tail_thick=1.2, leg=0.82, body=0.92, girth=1.0,
                  head=1.12, muzzle=0.82, mw=1.05, eye=1.2, pattern="saddle", belly=1.0, wag=0.45,
                  marks={"bib": "secondary", "muzzle": "secondary", "blaze": "secondary", "tailtip": "secondary"}, socks="secondary",
                  preview=PV("#C8823A", "#F2EEE6"))


@hero("bloodhound", "canines")
def bloodhound():
    return _canid("bloodhound", ear="long", ear_size=1.0, tail="sickle", tail_thick=0.8, tail_len=1.1, head=1.15, muzzle=1.05, mw=1.15,
                  jowls=1.3, wrinkles=0.8, eye=0.9, leg=1.0, girth=1.0, marks={"saddle": "secondary"}, preview=PV("#8B5A2B", "#2B1B12"))


@hero("basset hound", "canines")
def basset_hound():
    return _canid("basset hound", ear="long", ear_size=1.05, tail="sickle", tail_thick=0.8, leg=0.42, body=1.2, girth=1.05, lt=1.3, paws=1.25,
                  head=1.15, muzzle=1.0, mw=1.12, jowls=1.1, eye=0.95, pattern="saddle", belly=1.0,
                  marks={"bib": "secondary", "muzzle": "secondary", "blaze": "secondary", "tailtip": "secondary"}, socks="secondary",
                  preview=PV("#B8783A", "#F2EEE6"))


@hero("rottweiler", "canines")
def rottweiler():
    return _canid("rottweiler", ear="floppy", ear_size=0.6, tail="bob", girth=1.15, chest=1.05, lt=1.15, head=1.15, muzzle=0.7, mw=1.22,
                  marks={"muzzle": "secondary"}, points=True, socks="secondary", belly=1.0, preview=PV("#1C1814", "#9A5A2A"))


@hero("doberman", "canines")
def doberman():
    return _canid("doberman", ear="erect", ear_size=1.38, ear_w=0.72, tail="bob", leg=1.1, girth=0.88, tuck=0.75, lt=0.92, head=1.0, muzzle=1.15,
                  mw=0.85, neck=1.1, marks={"muzzle": "secondary"}, points=True, socks="secondary", belly=1.0, preview=PV("#1A1414", "#A0582A"))


@hero("border collie", "canines")
def border_collie():
    return _canid("border collie", ear="fold", ear_size=1.2, tail="hang", tail_thick=1.15, fluff=0.012, ruff=0.45, girth=0.9, muzzle=0.95,
                  marks={"bib": "secondary", "blaze": "secondary", "tailtip": "secondary"}, socks="secondary", wag=0.3,
                  preview=PV("#1E1E1E", "#F2F2F2"))


@hero("samoyed", "canines")
def samoyed():
    return _canid("samoyed", ear="erect", ear_size=0.85, tail="curl", tail_thick=1.6, fluff=0.03, ruff=1.1, girth=1.05, head=1.05, muzzle=0.8,
                  tongue=True, wag=0.3, belly=1.0, preview=PV("#F7F7F4", "#E2E0DA"))


@hero("pomeranian", "canines")
def pomeranian():
    return _canid("pomeranian", s=0.55, ear="erect", ear_size=0.7, tail="curl", tail_thick=1.8, tail_len=0.8, fluff=0.02, ruff=1.0, girth=1.05,
                  head=1.5, dome=0.5, muzzle=0.55, mw=0.85, eye=1.3, leg=0.72, body=0.75, lt=1.1, neck=0.6, tongue=True, wag=0.4,
                  preview=PV("#F2A04A", "#FFE3BC"))


@hero("shiba inu", "canines")
def shiba_inu():
    return _canid("shiba inu", s=0.82, ear="erect", ear_size=1.0, ear_w=1.15, tail="curl", tail_thick=1.25, fluff=0.008, ruff=0.4, head=1.12,
                  muzzle=0.82, marks={"bib": "secondary", "mask": "secondary"}, socks="secondary", wag=0.3, preview=PV("#D98A3A", "#FFF2E0"))


@hero("saint bernard", "canines")
def saint_bernard():
    return _canid("saint bernard", s=1.15, ear="floppy", ear_size=0.95, tail="hang", tail_thick=1.4, fluff=0.016, ruff=0.7, girth=1.18, chest=1.08,
                  lt=1.25, head=1.18, muzzle=0.78, mw=1.32, jowls=1.0, eye=0.9, collar="tag",
                  marks={"bib": "secondary", "blaze": "secondary", "tailtip": "secondary"}, socks="secondary", preview=PV("#B05A2A", "#F7F2EA"))


@hero("terrier", "canines")
def terrier():
    return _canid("terrier", s=0.72, ear="fold", ear_size=1.0, tail="up", tail_len=0.6, tail_thick=1.3, fluff=0.022, girth=0.95, leg=0.95,
                  body=0.82, head=1.15, muzzle=0.9, mw=1.05, jowls=0.5, wag=0.4, marks={"saddle": "secondary"}, preview=PV("#D8C8AE", "#7A5A3A"))


@hero("dire wolf", "canines")
def dire_wolf():
    return _canid("dire wolf", s=1.12, ear="erect", ear_size=1.0, tail="hang", tail_thick=1.4, ruff=1.0, fluff=0.02, girth=1.15, chest=1.05,
                  lt=1.2, head=1.15, mw=1.15, fangs=2.0, paws=1.15, mane=0.5, marks={"bib": "secondary"}, eyecol="gold",
                  preview=PV("#4E4A46", "#B0A898", gold="#D9A13B"))


@hero("warg", "canines")
def warg():
    return _canid("warg", s=1.2, scale=1.4, mount_len=10.0, pad_col=[0.35, 0.25, 0.18], ear="erect", ear_size=0.9, tail="hang", tail_thick=1.35, ruff=0.9, fluff=0.024, girth=1.25, chest=1.1, slope=0.1,
                  lt=1.3, head=1.22, mw=1.25, fangs=2.4, paws=1.2, mane=0.9, eyecol="red", mount=True, saddle="goblin",
                  preview=PV("#44403C", "#A8A29E", red="#D9372B"))


@hero("coyote", "canines")
def coyote():
    return _canid("coyote", ear="erect", ear_size=1.32, tail="hang", tail_thick=1.25, girth=0.85, leg=1.0, lt=0.88, head=0.95, muzzle=1.15,
                  mw=0.82, fluff=0.01, stock=0.3, marks={"bib": "secondary", "muzzle": "secondary"}, eyecol="gold",
                  preview=PV("#B08E64", "#E8D8C0", gold="#D9A13B"))


@hero("jackal", "canines")
def jackal():
    return _canid("jackal", ear="erect", ear_size=1.42, ear_w=0.95, tail="hang", tail_thick=1.05, girth=0.8, leg=1.05, lt=0.82, head=0.92,
                  muzzle=1.15, mw=0.78, marks={"saddle": "secondary"}, eyecol="gold", preview=PV("#C08A50", "#2E2A26", gold="#D9A13B"))


@hero("hyena", "canines")
def hyena():
    return _canid("hyena", ear="round", ear_size=1.25, tail="whip", tail_len=0.7, tail_thick=1.6, slope=0.55, mane=0.7, girth=1.08, chest=1.08,
                  leg=1.02, lt=1.15, head=1.25, muzzle=0.8, mw=1.3, fangs=1.5, pattern="hyena", belly=0.9, attack="bite", eyecol="gold",
                  preview=PV("#A88E66", "#3A2E22", gold="#C99A3A"))


@hero("arctic fox", "canines")
def arctic_fox():
    return _canid("arctic fox", s=0.95, ear="round", ear_size=0.95, tail="brush", tail_len=1.05, tail_thick=1.3, fluff=0.025, ruff=0.8, muzzle=0.75,
                  mw=0.85, head=1.0, girth=0.95, leg=0.72, body=0.88, lt=1.1, pupil="slit", eyecol="gold", belly=1.0,
                  preview=PV("#F4F4F2", "#C8D4E0", gold="#C99A3A"))


@hero("fennec fox", "canines")
def fennec_fox():
    return _canid("fennec fox", s=0.72, ear="big", ear_size=1.4, ear_w=1.15, tail="brush", tail_len=1.0, tail_thick=0.95, head=1.45, dome=0.4,
                  muzzle=0.7, mw=0.75, eye=1.35, girth=0.72, chest=0.85, leg=0.9, body=0.8, lt=0.8, neck=0.7, fluff=0.008, pupil="round",
                  marks={"bib": "secondary", "muzzle": "secondary"}, preview=PV("#EED2A8", "#F8EEDC"))


@hero("cerberus", "canines")
def cerberus():
    return _canid("cerberus", s=1.2, heads=3, ear="erect", ear_size=0.9, tail="snake", tail_len=1.2, tail_thick=1.1, girth=1.2, chest=1.1,
                  lt=1.25, head=0.95, mw=1.15, fangs=2.0, paws=1.2, neck=1.05, collar="spiked", mane=0.6, eyecol="eyeGlow", pupil=None, shine=False,
                  preview=PV("#1F1F1F", "#DC2626", eyeGlow="#FF5A2A"))


DOG = {"cat": ["Creature", "Abstract", "Element", "Machine", "Weather", "Object"], "bp": ["Quadruped", "Biped", "Blob", "Swarm", "Humanoid"]}
MAP = [
    ("dog", "dog, dogs, doggy, doggo, mutt, mongrel, canine, pooch, zombie dog, ghost dog, skeleton dog, blink dog, robot dog, mutant dog, "
            "space dog, cadejo, dog knight, !hot dog, !sea dog, !prairie dog, !raccoon dog, !foo dog, !corn dog", DOG),
    ("puppy", "puppy, puppies, doggie, lava pup, three-eyed puppy, sheepdog puppy, golden retriever puppy, labrador puppy, siberian husky puppy, "
              "dalmatian puppy, puppy dog", DOG),
    ("wolf", "wolf, wolves, gray wolf, grey wolf, timber wolf, arctic wolf, red wolf, ethiopian wolf, maned wolf, shadow wolf, winter wolf, "
             "thunder wolf, lunar wolf, fire wolf, frost wolf, ice wolf, spirit wolf, wolf pup, baby wolf, raiju, dhole, dingo, lone wolf, werewolf pup", DOG),
    ("dire wolf", "dire wolf, direwolf, fenrir, fenris, black dog, garm, cu sith, hellhound, hell hound, hellfire hound, lava hound, barghest, "
                  "beast of the moor, shuck", DOG),
    ("warg", "warg, wargs, worg, goblin rider, beast rider, wolf rider, war wolf", {"bp": ["Quadruped", "Biped", "Humanoid"], "cat": ["Creature", "Person", "Abstract", "Element", "Machine"]}),
    ("fox", "fox, foxes, red fox, gray fox, grey fox, kit fox, fox kit, baby fox, swift fox, corsac fox, silver fox, vixen, "
            "spirit fox, nebula fox, firefox, firefox spirit, frost fox, fire fox, fox ninja", DOG),
    ("arctic fox", "arctic fox, snow fox, polar fox", DOG),
    ("fennec fox", "fennec, fennec fox, fennec kit, bat-eared fox, bat eared fox", DOG),
    ("coyote", "coyote, coyotes", DOG),
    ("jackal", "jackal, jackals, golden jackal, african wild dog, painted dog, bush dog, thylacine, tasmanian tiger", DOG),
    ("hyena", "hyena, hyenas, hyaena, spotted hyena, striped hyena, aardwolf, hyaenodon, andrewsarchus", DOG),
    ("husky", "husky, huskies, siberian husky, malamute, alaskan malamute, alaskan klee kai, sled dog", DOG),
    ("golden retriever", "golden retriever, retriever, setter, irish setter, cocker spaniel, spaniel, cavalier king charles spaniel, springer spaniel", DOG),
    ("labrador", "labrador, labrador retriever, lab dog, pointer, weimaraner, vizsla, chesapeake bay retriever, !laser pointer", DOG),
    ("german shepherd", "german shepherd, alsatian, belgian malinois, malinois, police dog, shepherd dog", DOG),
    ("bulldog", "bulldog, english bulldog, british bulldog, shar pei, bull dog", DOG),
    ("french bulldog", "french bulldog, frenchie, boston terrier", DOG),
    ("pug", "pug, pugs, pekingese", DOG),
    ("dachshund", "dachshund, wiener dog, sausage dog, doxie", DOG),
    ("corgi", "corgi, corgis, welsh corgi, pembroke corgi", DOG),
    ("chihuahua", "chihuahua, papillon, xoloitzcuintli, toy dog", DOG),
    ("poodle", "poodle, poodles, bichon frise, bichon, labradoodle, goldendoodle, !poodle moth", DOG),
    ("great dane", "great dane, dane, irish wolfhound, wolfhound", DOG),
    ("greyhound", "greyhound, whippet, saluki, borzoi, afghan hound, italian greyhound", DOG),
    ("dalmatian", "dalmatian, dalmatians", DOG),
    ("beagle", "beagle, foxhound, harrier", DOG),
    ("bloodhound", "bloodhound, hound, hounds, coonhound, tracking dog", DOG),
    ("basset hound", "basset hound, basset", DOG),
    ("rottweiler", "rottweiler, mastiff, bullmastiff, dogue de bordeaux, boxer dog, pitbull, pit bull, cane corso, gwyllgi, guard dog", DOG),
    ("doberman", "doberman, dobermann, doberman pinscher, pinscher, miniature pinscher", DOG),
    ("border collie", "border collie, collie, sheepdog, australian shepherd, shetland sheepdog, sheltie, old english sheepdog", DOG),
    ("samoyed", "samoyed, chow chow, chow, puli, komondor, spitz, great pyrenees, akbash", DOG),
    ("pomeranian", "pomeranian, maltese, shih tzu, lhasa apso, havanese, coton de tulear, yorkie dog", DOG),
    ("shiba inu", "shiba inu, shiba, akita, basenji, inugami", DOG),
    ("saint bernard", "saint bernard, st bernard, bernese mountain dog, newfoundland, leonberger, tibetan mastiff", DOG),
    ("terrier", "terrier, yorkshire terrier, bull terrier, jack russell, jack russell terrier, cairn terrier, westie, scottie, airedale, "
                "schnauzer, miniature schnauzer, wire fox terrier", DOG),
    ("cerberus", "cerberus, cerberus pup, kerberos, orthrus, three-headed dog, three headed dog, two-headed dog", DOG),
]
