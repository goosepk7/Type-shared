"""Big cats and cats: lion, lioness, tiger, white tiger, leopard, snow leopard, jaguar, black panther, cheetah, puma,
lynx, sabertooth, house cat. One parametric sculpt: deep ribcage, tucked waist, muscled haunch and shoulder blades,
three-segment legs with toed paws, a short-muzzled cat skull with whisker pads, brow and cheek ruffs, a separate
jaw that opens, fangs, rounded ears, and a lagging three-piece tail. Patterns (stripes, rosettes, spots) and the
pale belly are baked into the vertex colour.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from kit import Hero, hero, stripes, spots, gradient, combine
from map import NOTFOOD
import motion

BASE = dict(
    s=1.0,           # overall size (studs per lion unit)
    leg=1.0,         # leg length factor
    body=1.0,        # body length factor
    girth=1.0,       # body thickness
    head=1.0,        # head size
    muzzle=1.0,      # muzzle length
    ear=1.0,         # ear size
    ear_tuft=False,
    mane=False,
    ruff=0.0,        # cheek ruff size (lynx, snow leopard)
    tail=1.0,        # tail length
    tail_thick=1.0,
    tuft=False,      # lion tail tuft
    fangs=0.0,       # sabertooth fang length (0 = normal fangs)
    pattern=None,    # "stripes" | "rosettes" | "spots" | None
    belly=0.8,       # back darkening for countershading
    fluffy=0.0,      # fur noise amplitude
    preview={},
)


def _feline(hid, **kw):
    P = dict(BASE)
    P.update(kw)
    s, LG, BL, G, HS = P["s"], P["leg"], P["body"], P["girth"], P["head"]
    H = Hero(hid, plan="Quadruped", gait="trot", tags=["feline"])
    H.preview = P["preview"]
    fur = P["fluffy"]

    def v(x, y, z):
        return (x * s, y * s, z * s)

    # leg geometry: ground at 0, the body sits on top of the legs
    lift = 3.0 * LG  # shoulder height
    bodyY = lift + 0.05
    zc, zr = -1.5 * BL, 1.45 * BL  # chest / rump centres
    H.body(v(0, bodyY, 0))

    # ------------------------------------------------------------------ pattern masks
    def back_shade(P_):
        t = np.clip((P_[:, 1] - (bodyY - 0.9) * s) / (1.6 * s), 0, 1)
        return 1.0 - (1.0 - P["belly"]) * t

    pat = None
    if P["pattern"] == "stripes":
        pat = stripes(lambda Q: Q[:, 2] / s + 0.35 * np.abs(Q[:, 1] / s - bodyY) ** 1.3, 1.7, width=0.26, depth=0.86, wobble=0.12, seed=3)
    elif P["pattern"] == "rosettes":
        pat = spots(0.42 * s, 0.17 * s, depth=0.82, ring=True, seed=5)
    elif P["pattern"] == "spots":
        pat = spots(0.3 * s, 0.085 * s, depth=0.9, seed=7)
    elif P["pattern"] == "ghost":  # black panther: faint rosettes in the black
        pat = spots(0.42 * s, 0.17 * s, depth=0.3, ring=True, seed=5)

    def skin(extra=None):
        return combine(back_shade, pat, extra)

    def furry(sd, amp=1.0, freq=9.0, seed=0):
        return sd.noise(fur * amp * s, freq / s, seed) if fur > 0 else sd

    # ------------------------------------------------------------------ torso
    torso = ellipsoid(0.84 * G, 1.0 * G, 1.35 * BL, v(0, bodyY + 0.05, zc + 0.55 * BL))              # ribcage
    torso = torso.su(ellipsoid(0.66 * G, 0.74 * G, 1.2 * BL, v(0, bodyY + 0.12, 0.45 * BL)), 0.45)    # waist (tucked)
    torso = torso.su(ellipsoid(0.78 * G, 0.86 * G, 0.95 * BL, v(0, bodyY + 0.2, zr)), 0.45)           # haunch
    torso = torso.su(ellipsoid(0.33 * G, 0.62, 0.55, v(0.6 * G, bodyY + 0.32, zc + 0.15)).mirror_x(), 0.25)  # scapulae
    torso = torso.su(ellipsoid(0.62 * G, 0.72 * G, 0.6, v(0, bodyY - 0.45, zc - 0.25)), 0.4)          # brisket
    torso = torso.su(ellipsoid(0.42 * G, 0.7, 0.75, v(0.58 * G, bodyY + 0.05, zr + 0.1)).mirror_x(), 0.3)    # hip muscle
    torso = torso.su(round_cone(v(0, bodyY + 0.35, zc - 0.25), v(0, bodyY + 0.85, zc - 0.85), 0.62 * G, 0.5 * G), 0.35)  # neck root
    torso = furry(torso, 1.0, 7.0, 1)
    H.piece("Torso", "Body", torso, col="primary", tris=2600, res=128, pattern=skin())

    # ------------------------------------------------------------------ legs
    sh = np.array(v(0.6 * G, bodyY + 0.05, zc + 0.15))
    el = np.array(v(0.6 * G, lift * 0.6, zc + 0.35))
    wr = np.array(v(0.58 * G, 0.42 * s, zc + 0.15))
    H.mbone("ShoulderF#", "Body", tuple(sh))
    H.mbone("ElbowF#", "ShoulderF#", tuple(el))
    H.mbone("WristF#", "ElbowF#", tuple(wr))
    up = round_cone(tuple(sh + np.array(v(0, 0.15, 0))), tuple(el), 0.44 * G * s, 0.27 * s)
    up = up.su(ellipsoid(0.32 * G, 0.72 * LG, 0.48, tuple(sh + np.array(v(0.02, -0.5 * LG, -0.02)))), 0.25)   # deltoid / triceps
    up = up.su(ellipsoid(0.26, 0.36, 0.28, tuple(el + np.array(v(0, 0.05, 0.12)))), 0.12)                    # elbow
    H.mpiece("UpperF#", "ShoulderF#", furry(up, 0.8, 9, 2), col="primary", tris=900, role="limb", pattern=skin())
    fo = round_cone(tuple(el), tuple(wr + np.array(v(0, 0.05, 0))), 0.27 * s, 0.17 * s)
    fo = fo.su(ellipsoid(0.22, 0.55 * LG, 0.27, tuple(el + np.array(v(0.01, -0.45 * LG, -0.05)))), 0.15)
    H.mpiece("ForeF#", "ElbowF#", furry(fo, 0.6, 10, 3), col="primary", tris=700, role="limb", pattern=skin())

    def paw(c, fwd=-1):
        c = np.array(c)
        p = round_cone(tuple(c + np.array(v(0, 0.08, 0))), tuple(c + np.array(v(0, -0.22, -0.12))), 0.18 * s, 0.2 * s)
        p = p.su(ellipsoid(0.26, 0.15, 0.3, tuple(c + np.array(v(0, -0.3, -0.2)))), 0.1)
        for i, dx in enumerate((-0.15, -0.05, 0.05, 0.15)):
            p = p.su(sphere(0.095 * s, tuple(c + np.array(v(dx, -0.33, -0.43 + 0.05 * abs(dx) * 4)))), 0.05)
        p = p.su(sphere(0.08 * s, tuple(c + np.array(v(-0.2, -0.22, -0.12)))), 0.05)   # dew claw side
        return p & plane((0, -1, 0), 0.0)

    H.mpiece("PawF#", "WristF#", paw(wr), col="primary", tris=600, role="foot", pattern=skin(lambda Q: np.ones(len(Q)) * 0.97))

    hp = np.array(v(0.56 * G, bodyY + 0.15, zr + 0.05))
    kn = np.array(v(0.62 * G, lift * 0.62, zr - 0.45))
    hk = np.array(v(0.6 * G, lift * 0.33, zr + 0.42))
    H.mbone("HipB#", "Body", tuple(hp))
    H.mbone("KneeB#", "HipB#", tuple(kn))
    H.mbone("HockB#", "KneeB#", tuple(hk))
    th = round_cone(tuple(hp + np.array(v(0, 0.2, 0.05))), tuple(kn), 0.55 * G * s, 0.3 * s)
    th = th.su(ellipsoid(0.4 * G, 0.85 * LG, 0.72, tuple(hp + np.array(v(0.02, -0.45 * LG, 0.0)))), 0.3)      # thigh mass
    H.mpiece("Thigh#", "HipB#", furry(th, 0.8, 9, 4), col="primary", tris=1000, role="limb", pattern=skin())
    sn = round_cone(tuple(kn), tuple(hk), 0.29 * s, 0.17 * s)
    sn = sn.su(ellipsoid(0.24, 0.42 * LG, 0.3, tuple(kn + np.array(v(0, -0.32 * LG, 0.22)))), 0.15)                 # calf
    sn = sn.su(sphere(0.15 * s, tuple(hk + np.array(v(0, 0.02, 0.1)))), 0.08)                                       # hock point
    H.mpiece("Shin#", "KneeB#", furry(sn, 0.6, 10, 5), col="primary", tris=700, role="limb", pattern=skin())
    ft = round_cone(tuple(hk), tuple(np.array(v(0.6 * G, 0.42, zr + 0.18))), 0.16 * s, 0.17 * s)
    ft = ft.su(paw(np.array(v(0.6 * G, 0.42, zr + 0.18))), 0.08)
    H.mpiece("PawB#", "HockB#", ft, col="primary", tris=650, role="foot", pattern=skin(lambda Q: np.ones(len(Q)) * 0.97))

    # ------------------------------------------------------------------ neck + head
    nk = np.array(v(0, bodyY + 0.65, zc - 0.7))
    H.bone("Neck", "Body", tuple(nk))
    neck = tube([v(0, bodyY + 0.35, zc - 0.35), v(0, bodyY + 0.75, zc - 0.95), v(0, bodyY + 1.0, zc - 1.3)], [0.6 * G * s, 0.48 * s, 0.4 * s], k=0.2)
    neck = neck.su(ellipsoid(0.42, 0.55, 0.45, v(0, bodyY + 0.3, zc - 0.85)), 0.25)  # dewlap / throat
    H.piece("NeckP", "Neck", furry(neck, 1.0, 8, 6), col="primary", tris=900, role="limb", pattern=skin())

    hc = np.array(v(0, bodyY + 1.15, zc - 1.65))  # head pivot (atlas)
    H.bone("Head", "Neck", tuple(hc))
    hs = HS * s
    M = P["muzzle"]

    def h(x, y, z):
        return tuple(hc + np.array((x * hs, y * hs, z * hs)))

    head = ellipsoid(0.5 * hs, 0.45 * hs, 0.52 * hs, h(0, 0.18, -0.3))                                          # cranium
    head = head.su(ellipsoid(0.3 * hs, 0.28 * hs, 0.32 * hs, h(0.3, 0.02, -0.5)).mirror_x(), 0.18)             # cheeks / zygoma
    head = head.su(round_cone(h(0, 0.28, -0.55), h(0, 0.12, -0.55 - 0.42 * M), 0.2 * hs, 0.16 * hs), 0.15)     # nasal bridge
    head = head.su(ellipsoid(0.32 * hs, 0.24 * hs, 0.3 * M * hs, h(0, -0.04, -0.62 - 0.22 * M)), 0.15)          # muzzle
    head = head.su(sphere(0.15 * hs, h(0.13, -0.08, -0.78 - 0.24 * M)).mirror_x(), 0.07)                        # whisker pads
    head = head.su(capsule(h(0.12, 0.36, -0.6), h(0.3, 0.3, -0.62), 0.08 * hs).mirror_x(), 0.08)               # brow ridge
    head = head.ss(sphere(0.105 * hs, h(0.24, 0.2, -0.72)).mirror_x(), 0.05)                                    # eye sockets
    head = head.su(ellipsoid(0.12 * hs, 0.08 * hs, 0.08 * hs, h(0, 0.06, -0.79 - 0.3 * M)), 0.04)               # nose pad base
    # ears
    er = P["ear"]
    ear = ellipsoid(0.17 * er * hs, 0.2 * er * hs, 0.07 * hs).ss(ellipsoid(0.12 * er * hs, 0.15 * er * hs, 0.05 * hs, (0, -0.02 * hs, -0.045 * hs)), 0.02)
    if P["ear_tuft"]:
        ear = ear.su(round_cone((0, 0.15 * er * hs, 0), (0.02 * hs, 0.45 * er * hs, 0.02 * hs), 0.04 * hs, 0.012 * hs), 0.03)
    ear = ear.rot(-15, 0, -22).at(*h(0.34, 0.56, -0.15))
    head = head.su(ear.mirror_x(), 0.06)
    if P["ruff"] > 0:
        rf = P["ruff"]
        for sx in (1, -1):
            for i in range(4):
                a = math.radians(-60 + i * 30)
                c0 = np.array(h(0.38 * sx, -0.05, -0.32))
                tip = c0 + np.array((sx * math.cos(a) * 0.32 * rf * hs, math.sin(a) * 0.3 * rf * hs, 0.12 * hs))
                head = head.su(round_cone(tuple(c0), tuple(tip), 0.13 * hs, 0.03 * hs), 0.07)
    head = furry(head, 0.35, 12, 7)
    H.piece("HeadP", "Head", head, col="primary", tris=2200, res=136, role="head",
            pattern=combine(pat, lambda Q: 1.0 - 0.0 * Q[:, 0]))
    # nose leather
    H.piece("Nose", "Head", ellipsoid(0.11 * hs, 0.07 * hs, 0.07 * hs, h(0, 0.08, -0.87 - 0.3 * M)).su(
        round_cone(h(0, 0.03, -0.9 - 0.3 * M), h(0, -0.1, -0.88 - 0.3 * M), 0.025 * hs, 0.02 * hs), 0.02),
        col="nose", tris=220, role="nose", pri=1.6, ao=False)
    # jaw
    jw = np.array(h(0, -0.12, -0.3))
    H.bone("Jaw", "Head", tuple(jw))
    jaw = ellipsoid(0.22 * hs, 0.11 * hs, 0.33 * M * hs, h(0, -0.25, -0.62 - 0.12 * M))
    jaw = jaw.su(capsule(h(0.2, -0.2, -0.35), h(0.12, -0.25, -0.65 - 0.1 * M), 0.07 * hs).mirror_x(), 0.08)
    jaw = jaw.su(ellipsoid(0.16 * hs, 0.09 * hs, 0.13 * hs, h(0, -0.3, -0.78 - 0.18 * M)), 0.06)     # chin
    H.piece("JawP", "Jaw", furry(jaw, 0.2, 14, 8), col="primary", tris=600, role="jaw", pri=1.4, pattern=pat)
    H.prim("Mouth", "Jaw", "Ellipsoid", (0.3 * hs, 0.06 * hs, 0.42 * M * hs), h(0, -0.15, -0.62 - 0.12 * M), col="mouth", mat="hard", role="mouth", pri=2.4)
    fl = 0.1 + P["fangs"]
    fang = round_cone(h(0.12, -0.12, -0.84 - 0.24 * M), h(0.115, -0.12 - fl, -0.86 - 0.24 * M), 0.035 * hs, 0.008 * hs)
    H.mpiece("Fang#", "Head", fang, col="tooth", mat="hard", tris=160, role="tooth", pri=2.2, ao=False, smooth=2)
    H.eyes("Head", h(0.24, 0.2, -0.735), 0.085 * hs, col="iris", pupil="slit", look=(0.45, 0.05, -1.0))
    if P["mane"]:
        mane = ellipsoid(0.78 * hs, 0.8 * hs, 0.62 * hs, h(0, 0.12, 0.05))
        for ring, (rad, zoff, n) in enumerate(((0.62, -0.1, 22), (0.72, 0.2, 18))):
            for i in range(n):
                a = (i + 0.5 * ring) / n * math.tau
                r0 = np.array(h(0, 0.15, zoff))
                d = np.array((math.cos(a), math.sin(a) * 1.05, 0.0))
                ln = 0.95 + 0.12 * math.sin(i * 1.7 + ring) - 0.15 * max(0.0, math.sin(a))
                tip = r0 + d * ln * hs + np.array((0, -0.22 * hs, 0.32 * hs))
                mane = mane.su(round_cone(tuple(r0 + d * rad * hs), tuple(tip), 0.17 * hs, 0.035 * hs), 0.07)
        mane = mane.su(ellipsoid(0.55 * hs, 0.85 * hs, 0.5 * hs, h(0, -0.65, 0.35)), 0.35)                    # chest mane
        mane = mane.su(ellipsoid(0.62 * hs, 0.7 * hs, 0.9 * hs, h(0, 0.4, 0.6)), 0.35)                        # nape mane
        mane = mane.ss(ellipsoid(0.5 * hs, 0.5 * hs, 0.9 * hs, h(0, 0.08, -0.72)), 0.15)                      # face opening
        mane = mane.noise(0.045 * hs, 9.0 / hs, 11)
        H.piece("Mane", "Head", mane, col="secondary", tris=2400, res=128, role="mane", pri=1.1)
    # ------------------------------------------------------------------ tail
    T, TT = P["tail"], P["tail_thick"]
    t0 = np.array(v(0, bodyY + 0.42, zr + 0.85 * BL))
    t1 = t0 + np.array(v(0, -0.25, 0.85)) * T
    t2 = t1 + np.array(v(0, -0.75, 0.55)) * T
    t3 = t2 + np.array(v(0, -0.6, 0.3)) * T
    H.bone("Tail1", "Body", tuple(t0))
    H.bone("Tail2", "Tail1", tuple(t1))
    H.bone("Tail3", "Tail2", tuple(t2))
    tr = 0.17 * TT * s
    H.piece("TailA", "Tail1", furry(round_cone(tuple(t0 - np.array(v(0, 0, 0.15))), tuple(t1), tr, tr * 0.85), 0.5, 10, 9), col="primary", tris=400, role="tail", pri=1.5, pattern=pat)
    H.piece("TailB", "Tail2", furry(round_cone(tuple(t1), tuple(t2), tr * 0.85, tr * 0.75), 0.5, 10, 10), col="primary", tris=400, role="tail", pri=1.7, pattern=pat)
    if T > 0.45:
        tip = round_cone(tuple(t2), tuple(t3), tr * 0.75, tr * 0.65)
        if P["tuft"]:
            tip = tip.su(ellipsoid(0.24 * s, 0.38 * s, 0.24 * s, tuple(t3 + np.array(v(0, -0.15, 0.05)))).noise(0.05 * s, 9 / s, 12), 0.08)
            H.piece("TailC", "Tail3", tip, col="secondary", tris=500, role="tail", pri=1.9)
        else:
            H.piece("TailC", "Tail3", furry(tip, 0.5, 10, 13), col="primary", tris=350, role="tail", pri=1.9,
                    pattern=combine(pat, (lambda Q: np.where(np.linalg.norm(Q - t3, axis=1) < 0.35 * s, 0.35, 1.0)) if P["pattern"] in ("stripes", "rosettes", "spots") else None))
    # ------------------------------------------------------------------ rig, sockets, motion
    H.socket("mouth", h(0, -0.15, -1.0), "Jaw")
    H.socket("head", h(0, 0.7, -0.3), "Head")
    H.socket("seat", v(0, bodyY + 0.95, 0), "Body")
    H.mount = {"seat": "Torso", "saddle": {"pos": v(0, bodyY + 0.95, -0.1 * BL), "size": v(1.25 * G, 0.18, 1.5)}}
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": ["Tail1", "Tail2", "Tail3"],
                  "legs": [{"hip": "ShoulderFR", "knee": "ElbowFR", "phase": 0.75, "side": 1}, {"hip": "ShoulderFL", "knee": "ElbowFL", "phase": 0.25, "side": -1},
                           {"hip": "HipBR", "knee": "KneeBR", "phase": 0.5, "side": 1}, {"hip": "HipBL", "knee": "KneeBL", "phase": 0.0, "side": -1}]})
    legs = [("ShoulderFR", "ElbowFR", "WristFR", 0.75, True), ("ShoulderFL", "ElbowFL", "WristFL", 0.25, True),
            ("HipBR", "KneeBR", "HockBR", 0.5, False), ("HipBL", "KneeBL", "HockBL", 0.0, False)]
    motion.quadruped(H, legs, neck="Neck", head="Head", jaw="Jaw", tail=["Tail1", "Tail2", "Tail3"], stride=0.42, walk=1.1,
                     height=bodyY + 1.0, attack="pounce", swipe="ShoulderFR")
    return H


@hero("lion", "felines")
def lion():
    return _feline("lion", mane=True, tuft=True, girth=1.05, head=1.08, belly=0.85, fluffy=0.0,
                   preview={"primary": "#C8963E", "secondary": "#6B4423", "nose": "#5A3A33", "iris": "#D9A13B"})


@hero("lioness", "felines")
def lioness():
    return _feline("lioness", tuft=True, girth=0.95, body=1.02, belly=0.85, preview={"primary": "#C9A06A", "secondary": "#6B4423", "nose": "#8A5A50", "iris": "#D9A13B"})


@hero("tiger", "felines")
def tiger():
    return _feline("tiger", pattern="stripes", girth=1.05, body=1.08, head=1.05, ruff=0.7, belly=0.9, fluffy=0.0,
                   preview={"primary": "#E07A1F", "secondary": "#1C1C1C", "nose": "#C46A6A", "iris": "#E3B13A"})


@hero("leopard", "felines")
def leopard():
    return _feline("leopard", pattern="rosettes", girth=0.88, leg=0.92, body=1.05, head=0.95, tail=1.25, belly=0.85,
                   preview={"primary": "#D7A85A", "secondary": "#2A2118", "nose": "#B07A6A", "iris": "#C9C04A"})


@hero("snow leopard", "felines")
def snow_leopard():
    return _feline("snow leopard", pattern="rosettes", girth=0.95, leg=0.85, body=1.0, head=0.95, tail=1.45, tail_thick=1.6, ruff=0.8,
                   fluffy=0.008, belly=0.9, preview={"primary": "#DCDAD2", "secondary": "#3A3A3A", "nose": "#9A7A80", "iris": "#9FC6C9"})


@hero("cheetah", "felines")
def cheetah():
    return _feline("cheetah", pattern="spots", girth=0.78, leg=1.18, body=1.05, head=0.85, muzzle=0.85, tail=1.2, belly=0.85,
                   preview={"primary": "#E3B868", "secondary": "#1E1A16", "nose": "#2B2422", "iris": "#C99A3A"})


@hero("black panther", "felines")
def panther():
    return _feline("black panther", pattern="ghost", girth=0.9, leg=0.95, body=1.05, tail=1.25, belly=0.95,
                   preview={"primary": "#26262B", "secondary": "#121214", "nose": "#1A1A1C", "iris": "#E3D43A"})


@hero("puma", "felines")
def puma():
    return _feline("puma", girth=0.9, leg=1.02, body=1.0, head=0.9, tail=1.25, tail_thick=1.1, belly=0.85,
                   preview={"primary": "#B88F5E", "secondary": "#EDE0C8", "nose": "#B07A6A", "iris": "#C9A04A"})


@hero("lynx", "felines")
def lynx():
    return _feline("lynx", pattern="spots", girth=0.95, leg=1.05, body=0.82, head=1.05, ear=1.15, ear_tuft=True, ruff=1.1, tail=0.32,
                   fluffy=0.0, belly=0.9, preview={"primary": "#B9A07E", "secondary": "#3A2F27", "nose": "#8A6A60", "iris": "#C9B04A"})


@hero("sabertooth", "felines")
def sabertooth():
    return _feline("sabertooth", girth=1.15, leg=0.9, body=0.95, head=1.1, fangs=0.42, tail=0.35, tail_thick=1.3, belly=0.85,
                   preview={"primary": "#B79562", "secondary": "#6B4E30", "nose": "#5A3A33", "iris": "#D9A13B"})


@hero("cat", "felines")
def cat():
    return _feline("cat", pattern="stripes", girth=0.85, leg=0.85, body=0.85, head=1.35, muzzle=0.72, ear=1.3, tail=1.25, tail_thick=0.9,
                   belly=0.88, fluffy=0.0, preview={"primary": "#E09A4A", "secondary": "#F6E7D2", "nose": "#E39A9A", "iris": "#7BC96A"})


# word -> hero rules (tools/meshgen/heroes/map.py)
MAP = [
    ("lion", "lion, lions, king of the jungle, !sea lion, !ant lion, !lion fish, !lionfish", NOTFOOD),
    ("lioness", "lioness, lionesses", NOTFOOD),
    ("tiger", "tiger, tigers, tigress, bengal tiger, siberian tiger", NOTFOOD),
    ("leopard", "leopard, leopards", NOTFOOD),
    ("snow leopard", "snow leopard, ounce", NOTFOOD),
    ("cheetah", "cheetah, cheetahs", NOTFOOD),
    ("black panther", "panther, panthers, black panther, jaguar, jaguars", NOTFOOD),
    ("puma", "puma, cougar, mountain lion, catamount, ocelot, serval, caracal", NOTFOOD),
    ("lynx", "lynx, bobcat", NOTFOOD),
    ("sabertooth", "sabertooth, saber tooth, sabretooth, smilodon, saber toothed tiger, sabre tooth", NOTFOOD),
    ("cat", "cat, cats, kitten, kitty, kittens, tabby, housecat, tomcat, siamese, persian cat, calico", {"cat": ["Creature", "Machine", "Object", "Abstract", "Element"], "bp": ["Quadruped", "Biped", "Blob"]}),
]
