"""Bugs (arachnids): spider, tarantula, black widow, jumping spider, tick, scorpion.

Cephalothorax (Torso) + abdomen on a pedicel, chelicerae with curved fangs, pedipalps, an eye cluster (eight eyes,
the jumping spider's front pair huge), and eight three-segment legs walking in alternating tetrapods (R1 L2 R3 L4
against L1 R2 L3 R4). The scorpion adds big pincers (arm, forearm, chela with a movable finger) and a five-segment
tail arching over the back to a bulbous telson and stinger that strikes forward.
"""
import math

import numpy as np

import sdf as S
from sdf import sphere, ellipsoid, capsule, round_cone, tube, torus  # noqa: F401
from kit import Hero, hero, stripes, spots, gradient, combine  # noqa: F401
import motion_bugs as MB
from bugkit import *  # noqa: F401,F403


def _spider(hid, kind="spider", s=1.0, preview=None):
    tar, widow, jump, tick = kind == "tarantula", kind == "widow", kind == "jumping", kind == "tick"
    H = Hero(hid, plan="Spider", gait="scuttle", tags=["arachnid", "bug", "spider"] + (["venomous"] if not tick else []))
    H.preview = preview or {}
    y = {"spider": 0.95, "tarantula": 1.0, "widow": 1.05, "jumping": 0.85, "tick": 0.55}[kind]
    hair = 0.035 if tar else (0.02 if jump else 0.0)
    H.body((0, y, -0.3))
    # ---------------------------------------------------------------- cephalothorax
    if tick:
        ct = ellipsoid(0.42, 0.18, 0.36, (0, y, -0.45))
        ct = ct.su(round_cone((0, y - 0.02, -0.75), (0, y - 0.08, -1.05), 0.12, 0.06), 0.06)        # capitulum (mouthparts)
        ct = ct.su(sphere(0.07, (0.06, y - 0.08, -1.0)).mirror_x(), 0.03)
    else:
        cw = {"spider": 0.5, "tarantula": 0.62, "widow": 0.4, "jumping": 0.55}[kind]
        ch = 0.4 if jump else 0.3
        ct = ellipsoid(cw, ch, cw * 1.18, (0, y, -0.4))
        if jump:
            ct = ct.su(round_box(cw * 0.8, ch * 0.9, 0.35, 0.2, (0, y + 0.1, -0.62)), 0.15)     # tall square face
        ct = ct.su(ellipsoid(cw * 0.55, ch * 0.7, 0.3, (0, y + ch * 0.35, -0.7)), 0.12)         # eye mound
        ct = ct.ss(ellipsoid(0.05, 0.08, 0.12, (0, y + ch * 0.95, -0.25)), 0.04)               # fovea
        ct = ct.su(ellipsoid(cw * 0.7, 0.18, cw, (0, y - 0.18, -0.38)), 0.1)                    # sternum
        if hair:
            ct = ct.noise(hair, 22, 1)
    H.piece("Torso", "Body", ct, col="primary", mat="fur" if hair else "hard", tris=1500, res=124,
            pattern=(lambda P: 1 - 0.35 * np.clip(1 - np.abs(np.abs(P[:, 0]) - 0.25) / 0.08, 0, 1)) if kind == "spider" else None)
    # ---------------------------------------------------------------- abdomen
    H.bone("Abdomen", "Body", (0, y + 0.02, 0.18))
    if tick:
        abd = ellipsoid(0.72, 0.32, 0.9, (0, y + 0.02, 0.35))
        abd = surface_cut(abd, zgrooves(0.35, 0.3, 0.012, y + 0.1), 0.03, 0.01)
        apat = lambda P: 1 - 0.55 * np.clip((0.55 - np.hypot(P[:, 0] / 0.75, (P[:, 2] + 0.15) / 0.55)) * 5, 0, 1)  # dark scutum
        acol = "primary"
    else:
        R = {"spider": (0.72, 0.6, 0.85), "tarantula": (0.8, 0.7, 0.92), "widow": (0.88, 0.85, 0.88), "jumping": (0.6, 0.5, 0.75)}[kind]
        c = A(0, y + R[1] * 0.35, 0.3 + R[2] * 0.95)
        abd = ellipsoid(*R).rot(-8, 0, 0).at(*T(c))
        abd = abd.su(capsule((0, y, -0.05), (0, y + 0.05, 0.35), 0.12), 0.08)                  # pedicel
        abd = abd.su(round_cone(T(c + A(0, -R[1] * 0.4, R[2] * 0.8)), T(c + A(0, -R[1] * 0.55, R[2] * 1.02)), 0.12, 0.06), 0.06)  # spinnerets
        if hair:
            abd = abd.noise(hair * 1.2, 20, 2)
        if kind == "spider":
            apat = combine(lambda P: 1 - 0.7 * np.clip(1 - np.abs(P[:, 0]) / 0.12, 0, 1) * (P[:, 1] > c[1]),
                           spots(0.3, 0.07, depth=0.5, seed=3, region=lambda P: (P[:, 1] > c[1]).astype(float)))
        elif kind == "jumping":
            apat = combine(lambda P: 1 - 0.85 * np.clip((np.abs(P[:, 0]) - 0.2) * 6, 0, 1) * (P[:, 1] > c[1] - 0.2),
                           spots(0.35, 0.08, depth=0.0, seed=1))
        elif tar:
            apat = lambda P: 1 - 0.0 * P[:, 0]
        else:
            apat = None
        acol = "primary"
    H.piece("AbdomenP", "Abdomen", abd, col=acol, mat="fur" if hair else ("plastic" if widow else "hard"), tris=1600, res=124, pattern=apat)
    if widow:
        base = ellipsoid(*R).rot(-8, 0, 0).at(*T(c))
        hg = poly2([(0.0, -0.05), (0.22, -0.35), (-0.22, -0.35)]) | poly2([(0.0, 0.05), (0.2, 0.32), (-0.2, 0.32)])
        hg = hg.at(0, 0, c[2] + 0.1).round(0.03)
        mark = S.SDF(lambda p: np.maximum(np.abs(base(p) - 0.0) - 0.025, hg(p))) & S.SDF(lambda p: p[:, 1] - c[1] + 0.4)
        dors = circ_y(0.0, c[2] + 0.55, 0.11)
        mark = mark | (S.SDF(lambda p: np.abs(base(p)) - 0.025) & dors & S.SDF(lambda p: c[1] - p[:, 1]))
        H.piece("Hourglass", "Abdomen", mark, col="secondary", mat="hard", tris=300, res=140, role="detail", pri=1.4)
    if tar:
        H.piece("Rump", "Abdomen", ellipsoid(0.42, 0.25, 0.4).rot(-30, 0, 0).at(0, y + R[1] * 0.35 + 0.55, 0.3 + R[2] * 1.1).noise(0.03, 22, 4),
                col="secondary", mat="fur", tris=400, role="detail", pri=1.4)
    # ---------------------------------------------------------------- chelicerae + fangs, palps, eyes
    fz = -0.88 if not tick else -0.95
    if not tick:
        fb = A(0.13 * (1.3 if tar else 1.0), y - 0.02, fz)
        H.mbone("Fang#", "Body", T(fb))
        ch_ = ellipsoid(0.13 * (1.3 if tar else 1.0), 0.22, 0.13, T(fb + A(0, -0.12, -0.04)))
        if hair:
            ch_ = ch_.noise(hair, 24, 5)
        fang = tube([T(fb + A(0, -0.3, -0.05)), T(fb + A(-0.02, -0.42, -0.06)), T(fb + A(-0.1, -0.5, 0.02))], [0.05, 0.035, 0.012], k=0.02)
        H.mpiece("Chelicera#", "Fang#", ch_, col="primary" if not jump else "secondary", mat="fur" if hair else "hard", tris=400, role="jaw", pri=1.3)
        H.mpiece("FangP#", "Fang#", fang, col="darker", mat="hard", tris=160, role="tooth", pri=1.5)
        mand = [("FangR", 1), ("FangL", -1)]
    else:
        mand = []
    pb = A(0.25 if not tick else 0.15, y - 0.12, fz + 0.12)
    H.mbone("Palp#", "Body", T(pb))
    plen = 0.5 if not tick else 0.25
    pp = [pb, pb + A(0.12, 0.2, -0.25) * plen * 2, pb + A(0.15, 0.0, -0.45) * plen * 2, pb + A(0.12, -0.35, -0.55) * plen * 2]
    palp = tube([T(p) for p in pp], [0.07, 0.06, 0.055, 0.05], k=0.03)
    if jump:
        palp = palp.su(sphere(0.08, T(pp[-1])), 0.03)
    if hair:
        palp = palp.noise(hair, 24, 6)
    H.mpiece("Palp#", "Palp#", palp, col="primary", mat="fur" if hair else "hard", tris=400, role="limb", pri=1.4)
    if not tick:
        ey = y + (0.32 if jump else 0.22)
        ez = -0.95 if jump else -0.85
        if jump:
            big, mid, small = 0.22, 0.09, 0.05
            H.mprim("EyeAM#", "Body", "Ball", (big * 2,) * 3, (0.15, ey - 0.08, ez + 0.06), col="black", mat="hard", pri=1.2, role="eye")
            H.mprim("ShineAM#", "Body", "Ball", (0.07,) * 3, (0.19, ey + 0.02, ez - 0.08), col="shine", mat="hard", pri=2.4, role="shine")
            H.mprim("EyeAL#", "Body", "Ball", (mid * 2,) * 3, (0.38, ey - 0.02, ez + 0.12), col="black", mat="hard", pri=1.3, role="eye")
            H.mprim("EyePL#", "Body", "Ball", (mid * 2,) * 3, (0.42, ey + 0.12, ez + 0.6), col="black", mat="hard", pri=1.3, role="eye")
        else:
            big, mid = (0.075, 0.06) if not tar else (0.08, 0.065)
            H.mprim("EyeAM#", "Body", "Ball", (big * 2,) * 3, (0.07, ey + 0.02, ez + 0.05), col="black", mat="hard", pri=1.2, role="eye")
            H.mprim("ShineAM#", "Body", "Ball", (0.03,) * 3, (0.09, ey + 0.06, ez - 0.01), col="shine", mat="hard", pri=2.4, role="shine")
            H.mprim("EyeAL#", "Body", "Ball", (mid * 2,) * 3, (0.19, ey - 0.02, ez + 0.09), col="black", mat="hard", pri=1.3, role="eye")
            H.mprim("EyePM#", "Body", "Ball", (mid * 2,) * 3, (0.09, ey + 0.09, ez + 0.2), col="black", mat="hard", pri=1.3, role="eye")
            H.mprim("EyePL#", "Body", "Ball", (mid * 2,) * 3, (0.22, ey + 0.05, ez + 0.24), col="black", mat="hard", pri=1.3, role="eye")
    else:
        H.mprim("Eye#", "Body", "Ball", (0.06,) * 3, (0.3, y + 0.08, -0.62), col="black", mat="hard", pri=1.3, role="eye")
    # ---------------------------------------------------------------- legs
    LS = {"spider": 1.0, "tarantula": 0.95, "widow": 1.15, "jumping": 0.75, "tick": 0.42}[kind]
    th = {"spider": 1.0, "tarantula": 1.75, "widow": 0.8, "jumping": 1.25, "tick": 1.35}[kind]
    r = tuple(x * th for x in (0.08, 0.065, 0.05, 0.035))
    hx = {"spider": 0.4, "tarantula": 0.5, "widow": 0.32, "jumping": 0.45, "tick": 0.38}[kind]
    hy = y - 0.08
    zs = (-0.68, -0.48, -0.28, -0.08) if not tick else (-0.62, -0.45, -0.28, -0.1)
    yaws = (62, 22, -18, -55)
    lens = (1.05, 0.95, 0.85, 1.05)
    names = []
    for i in range(4):
        L = lens[i] * LS
        ky = y + (0.75 if not tick else 0.3) * LS * (1.0 if not jump else 1.1)
        sp = legspec((hx * (0.9 if i in (0, 3) else 1.0), hy, zs[i]), yaws[i], 0.75 * L, ky, 1.65 * L, 0.42 * LS, 2.25 * L, 0.035 * th)
        names.append(leg(H, str(i + 1), *sp, r=r, col="primary" if not jump else ("primary" if i else "dark"), hair=hair, beads=2,
                         tris=(320, 280, 220) if not tar else (420, 380, 260), spines=0 if (hair or widow or tick) else 2, spine_len=0.1))
    legs = legs_rig(names, [0.0, 0.5, 0.0, 0.5])
    MB.walker(H, legs, head=None, abd="Abdomen", ants=[("PalpR", 1), ("PalpL", -1)], mand=mand, height=1.3 * LS + 0.4,
              stride=0.3, lift=0.3, period=0.7 if not tick else 0.8, attack="bite")
    finish(H, head="Body", mouth=(0, y - 0.4, fz - 0.15), top=(0, y + 0.5, -0.5), legs=legs)
    return H


def circ_y(cx, cz, r):
    return S.SDF(lambda p: np.hypot(p[:, 0] - cx, p[:, 2] - cz) - r)


def round_box(hx, hy, hz, r, c):
    return S.round_box(hx, hy, hz, r, c)


@hero("spider", "bugs")
def spider():
    return _spider("spider", "spider", preview={"primary": "#4A3A2A", "secondary": "#8A6A4A", "darker": "#140E0A"})


@hero("tarantula", "bugs")
def tarantula():
    return _spider("tarantula", "tarantula", preview={"primary": "#3A2A20", "secondary": "#E8701E", "darker": "#140E0A"})


@hero("black widow", "bugs")
def black_widow():
    return _spider("black widow", "widow", preview={"primary": "#1E1E1E", "secondary": "#D8201E", "darker": "#0A0A0A"})


@hero("jumping spider", "bugs")
def jumping_spider():
    return _spider("jumping spider", "jumping", preview={"primary": "#3A3A30", "secondary": "#8AE0E8", "darker": "#140E0A", "cream": "#F2E8D0", "dark": "#1E1E1A"})


@hero("tick", "bugs")
def tick():
    return _spider("tick", "tick", preview={"primary": "#6A3A1E", "secondary": "#3A2A1A", "darker": "#140E0A"})


# ================================================================================================ scorpion
def _scorpion(hid, s=1.0, claw=1.0, tailk=1.0, preview=None):
    H = Hero(hid, plan="Spider", gait="scuttle", tags=["arachnid", "bug", "scorpion", "venomous"])
    H.preview = preview or {}
    y = 0.62
    H.body((0, y, -0.2))
    # prosoma + mesosoma (7 tergites)
    bd = ellipsoid(0.42, 0.2, 0.42, (0, y + 0.02, -0.55))
    for i in range(7):
        z = -0.18 + i * 0.17
        w = 0.48 - 0.018 * i - (0.06 if i == 6 else 0.0)
        bd = bd.su(ellipsoid(w, 0.19, 0.13, (0, y + 0.02, z)), 0.04)
    bd = bd.su(ellipsoid(0.36, 0.13, 0.85, (0, y - 0.09, 0.0)), 0.08)                            # sternites
    bd = bd.ss(ellipsoid(0.04, 0.05, 0.3, (0, y + 0.22, -0.55)), 0.03)
    H.piece("Torso", "Body", bd, col="primary", mat="hard", tris=1700, res=128,
            pattern=stripes(lambda P: P[:, 2], 1 / 0.17, width=0.18, depth=0.3, region=lambda P: (P[:, 2] > -0.25).astype(float)))
    H.mprim("Eye#", "Body", "Ball", (0.08,) * 3, (0.06, y + 0.21, -0.62), col="black", mat="hard", pri=1.3, role="eye")
    H.mprim("Shine#", "Body", "Ball", (0.03,) * 3, (0.08, y + 0.25, -0.65), col="shine", mat="hard", pri=2.4, role="shine")
    # tail: five segments arching up and forward, then the telson
    K = tailk
    P = [A(0, y + 0.03, 0.95), A(0, y + 0.25, 1.4), A(0, y + 0.7, 1.75), A(0, y + 1.3, 1.85), A(0, y + 1.85, 1.65), A(0, y + 2.15, 1.25)]
    P = [P[0] + (p - P[0]) * K for p in P]
    tail = []
    par = "Body"
    for i in range(5):
        b = H.bone(f"Tail{i + 1}", par, T(P[i]))
        tail.append(b)
        par = b
        r0 = 0.17 - 0.012 * i
        seg = round_cone(T(P[i]), T(P[i + 1]), r0, r0 * 0.92).su(sphere(r0 * 1.02, T(P[i + 1])), 0.04)
        d = P[i + 1] - P[i]
        seg = seg.su(round_cone(T(P[i] + d * 0.15 + A(0.08, 0.06, 0)), T(P[i] + d * 0.85 + A(0.08, 0.06, 0)), 0.04, 0.035).mirror_x(), 0.04)  # keels
        H.piece(f"TailP{i + 1}", b, seg, col="primary", mat="hard", tris=420, role="tail", pri=1.2 + 0.05 * i)
    sb = H.bone("Sting", par, T(P[5]))
    tc = P[5] + A(0, 0.02, -0.12) * K
    tel = ellipsoid(0.17, 0.17, 0.24, T(tc))
    tel = tel.su(tube([T(tc + A(0, -0.05, -0.18)), T(tc + A(0, -0.18, -0.38)), T(tc + A(0, -0.42, -0.42))], [0.08, 0.04, 0.008], k=0.03), 0.04)
    H.piece("Telson", sb, tel, col="secondary", mat="hard", tris=500, role="tail", pri=1.4)
    tail.append(sb)
    # pincers: arm (femur) -> forearm (patella) -> chela (hand + fixed finger) -> movable finger
    C = claw
    a0 = A(0.25, y - 0.02, -0.85)
    a1 = a0 + A(0.5, 0.18, -0.25) * C
    a2 = a1 + A(-0.05, -0.05, -0.55) * C
    a3 = a2 + A(-0.1, 0.0, -0.55) * C
    H.mbone("Arm#", "Body", T(a0))
    H.mbone("Elbow#", "Arm#", T(a1))
    H.mbone("Hand#", "Elbow#", T(a2))
    H.mpiece("ArmP#", "Arm#", round_cone(T(a0), T(a1), 0.08, 0.075).su(sphere(0.1, T(a1)), 0.03), col="primary", mat="hard", tris=300, role="limb", pri=1.3)
    H.mpiece("Forearm#", "Elbow#", round_cone(T(a1), T(a2), 0.09, 0.12).su(sphere(0.12, T(a2)), 0.04), col="primary", mat="hard", tris=320, role="limb", pri=1.3)
    hand = ellipsoid(0.22 * C, 0.17 * C, 0.33 * C, T(a2 + A(-0.02, 0, -0.22) * C))
    fx = tube([T(a2 + A(0.05, 0, -0.42) * C), T(a2 + A(0.04, 0, -0.75) * C), T(a2 + A(-0.04, 0, -0.95) * C)], [0.08 * C, 0.05 * C, 0.015 * C], k=0.03)
    hand = hand.su(fx, 0.06)
    H.mpiece("Chela#", "Hand#", hand, col="secondary", mat="hard", tris=700, role="claw", pri=1.2, pattern=gradient(2, -2.5, -1.2, 0.55, 1.0))
    fb = a2 + A(-0.12, 0.0, -0.4) * C
    H.mbone("Finger#", "Hand#", T(fb))
    fg = tube([T(fb), T(fb + A(-0.08, 0.0, -0.3) * C), T(fb + A(-0.02, 0.0, -0.55) * C)], [0.08 * C, 0.05 * C, 0.015 * C], k=0.03)
    H.mpiece("FingerP#", "Finger#", fg, col="secondary", mat="hard", tris=300, role="claw", pri=1.3, pattern=lambda P: np.full(len(P), 0.6))
    # legs
    r = (0.07, 0.06, 0.045, 0.032)
    hy = y - 0.1
    zs = (-0.62, -0.42, -0.2, 0.02)
    yaws = (40, 10, -25, -55)
    names = []
    for i in range(4):
        L = (0.8, 0.88, 0.95, 1.05)[i]
        sp = legspec((0.32, hy, zs[i]), yaws[i], 0.55 * L, y + 0.4, 1.15 * L, 0.3, 1.6 * L, 0.035)
        names.append(leg(H, str(i + 1), *sp, r=r, col="primary", beads=2, tris=(280, 240, 200), spines=1, spine_len=0.08))
    legs = legs_rig(names, [0.0, 0.5, 0.0, 0.5])
    MB.walker(H, legs, head=None, abd=None, ants=[], mand=[("FingerR", 1), ("FingerL", -1), ("ArmR", 1, 0.45), ("ArmL", -1, 0.45)],
              tail=tail, height=1.4, stride=0.26, lift=0.28, period=0.75, attack="tail")
    finish(H, head="Body", mouth=T(P[5] + A(0, -0.4, -0.6)), top=(0, y + 0.4, -0.55), legs=legs, tail=tail)
    H.socket("sting", T(tc + A(0, -0.42, -0.42)), "Sting")
    return H


@hero("scorpion", "bugs")
def scorpion():
    return _scorpion("scorpion", preview={"primary": "#6A4A1E", "secondary": "#E8A84A"})


@hero("emperor scorpion", "bugs")
def emperor_scorpion():
    return _scorpion("emperor scorpion", claw=1.35, tailk=0.85, preview={"primary": "#1A1A20", "secondary": "#2A2A34"})
