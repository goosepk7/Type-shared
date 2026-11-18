"""Mythic birds: phoenix (sculpted flame feathers, flowing tail plumes, flame crest), thunderbird (storm eagle with a
swept crest and bright primaries), roc (colossal eagle, huge talons) and cockatrice (rooster head with comb and
wattles, bat wings, serpent tail).

`_bird`: a pitched teardrop torso with layered breast feathers, a feathered neck, an eagle / rooster head (hooked
two-part beak that opens, brow, crest), feathered "trousers" over scaly tarsi and four-toed taloned feet, big
feathered wings on two bones per side (h_mythic.feather_wing; flame-curled feathers for the phoenix) or bat wings,
and a tail (eagle fan, phoenix plumes on a three-bone chain, serpent tail). Motion: motion_mythic.flyer.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from kit import Hero, hero, stripes, combine
import motion_mythic as mm
from mythic_geo import (V, nrm, tri, fan, membrane, scallop, union_hard, bounded, frame, oell, squash, flat_tube, spike, curved_horn,
                        blade_fin, outside, band_y, feather)
from h_mythic import feather_wing

BASE = dict(s=1.0, head=1.0, kind="eagle", wings="feather", wing=1.0, tail="fan", crest=None, talon=1.0, flame=0.0,
            arm_col="primary", hand_col="primary", tail_col="primary", head_col="primary", breast_col="primary", preview={})


def _bird(hid, **kw):
    P = dict(BASE)
    P.update(kw)
    s = P["s"]
    H = Hero(hid, plan="Bird", gait="fly", tags=["bird", "mythic"])
    H.preview = P["preview"]
    fl = P["flame"]

    def v(x, y, z):
        return V(x, y, z) * s

    bodyY = 2.55
    H.body(v(0, bodyY, 0))
    R = frame(V(0, 0.55, -1.0))       # torso axis pitched nose-up
    torso = oell(v(0, bodyY + 0.15, -0.25), R, (1.15 * s, 0.85 * s, 0.82 * s))
    torso = torso.su(oell(v(0, bodyY - 0.15, 0.55), frame(V(0, 0.2, -1.0)), (0.95 * s, 0.65 * s, 0.7 * s)), 0.35)
    torso = torso.su(round_cone(v(0, bodyY - 0.05, 0.9), v(0, bodyY - 0.2, 1.55), 0.45 * s, 0.25 * s), 0.25)
    torso = torso.su(ellipsoid(0.4 * s, 0.4 * s, 0.5 * s, v(0.45, bodyY + 0.45, -0.45)).mirror_x(), 0.3)     # flight muscles
    core = torso
    # breast feathers: overlapping scalloped tufts (flame tongues for the phoenix)
    tufts = []
    for row in range(4):
        for k in range(5 - (row % 2)):
            x = (-0.5 + k * 0.25 + 0.125 * (row % 2)) * (1 - 0.1 * row)
            q = V(x, bodyY + 0.65 - 0.38 * row, -0.95 + 0.12 * row) * s
            d = nrm(V(x * 0.3, -1.0, 0.35))
            nr_ = nrm(V(x, 0.2, -1.0))
            ln = (0.55 + 0.25 * fl) * s
            tufts.append(feather(q, d, ln, 0.17 * s, nr_, th=0.05 * s, curl=(0.05 + 0.18 * fl) * s))
    for f_ in tufts:
        torso = torso.su(f_, 0.03 * s)
    H.piece("Torso", "Body", torso, col=P["breast_col"], tris=2200, res=128,
            pattern=combine(band_y((bodyY - 0.8) * s, (bodyY + 1.0) * s, 1.0, 0.85), outside(core, 0.03, 0.85, 0.08)))

    # legs: feathered trousers on the thigh, scaly tarsus, four taloned toes
    tk = P["talon"]
    hp = v(0.45, bodyY - 0.25, 0.1)
    kn = v(0.5, 1.15, 0.3)
    ft = v(0.5, 0.0, 0.0)
    H.mbone("Hip#", "Body", tuple(hp))
    H.mbone("Knee#", "Hip#", tuple(kn))
    H.mbone("Foot#", "Knee#", tuple(ft + v(0, 0.3, 0.05)))
    th = round_cone(hp + v(0, 0.2, 0), kn + v(0, 0.15, 0), 0.38 * s, 0.25 * s).noise(0.03 * s, 7 / s, 2)
    for k in range(4):
        q = kn + v(0.08 * (k - 1.5), 0.25, 0.02)
        th = th.su(feather(q, V(0.05 * (k - 1.5), -1, 0.25), 0.4 * s, 0.12 * s, V(0, 0.2, -1), th=0.045 * s), 0.03)
    H.mpiece("Thigh#", "Hip#", th, col=P["breast_col"], tris=600, role="limb")
    tar = round_cone(kn, ft + v(0, 0.3, 0.05), 0.13 * s * tk, 0.1 * s * tk)
    H.mpiece("Tarsus#", "Knee#", tar, col="beak", tris=300, role="limb", pattern=stripes(lambda Q: Q[:, 1] / s, 8.0, width=0.25, depth=0.18))
    k_ = s * tk
    c = ft + v(0, 0.3, 0.05)
    foot = sphere(0.14 * k_, c)
    core_f = foot
    tal = []
    for a in (-0.45, 0.0, 0.45, math.pi):
        d = nrm(V(math.sin(a), 0, -math.cos(a)))
        ln = 0.55 if a != math.pi else 0.35
        p1 = V(c[0], 0.08 * k_, c[2]) + d * ln * k_
        toe = tube([c, V(c[0], 0.12 * k_, c[2]) + d * ln * 0.5 * k_, p1], [0.1 * k_, 0.08 * k_, 0.065 * k_])
        core_f = core_f.su(toe, 0.04 * k_)
        tal.append(curved_horn([p1, p1 + d * 0.15 * k_ + V(0, 0.03, 0) * k_, p1 + d * 0.25 * k_ - V(0, 0.07, 0) * k_], 0.06 * k_, 0.01 * k_))
    foot = core_f
    for t_ in tal:
        foot = foot.su(t_, 0.015 * k_)
    H.mpiece("Talons#", "Foot#", foot & plane((0, -1, 0), 0.0), col="beak", tris=650, role="foot", pattern=outside(core_f, 0.02, 0.22, 0.04))

    # neck + head
    n0 = v(0, bodyY + 0.75, -0.85)
    hc = v(0, bodyY + 1.55, -1.25)
    H.bone("Neck", "Body", tuple(n0))
    H.bone("Head", "Neck", tuple(hc))
    neck = tube([n0 + v(0, -0.25, 0.3), (n0 + hc) / 2 + v(0, 0, 0.05), hc + v(0, -0.05, 0.2)], [0.55 * s, 0.42 * s, 0.36 * s], k=0.15)
    hs = s * P["head"]
    for k in range(6):   # hackles
        a = -1.0 + 0.4 * k
        q = hc + V(0.3 * math.sin(a), 0.1 * math.cos(a), 0.15) * hs
        neck = neck.su(feather(q, V(0.25 * math.sin(a), -0.3, 1.0), (0.6 + 0.3 * fl) * s, 0.16 * s, V(math.sin(a), math.cos(a), 0.1), th=0.045 * s,
                               curl=0.1 * fl * s), 0.03)
    H.piece("NeckP", "Neck", neck, col=P["head_col"], tris=900, role="limb")

    def h(x, y, z):
        return hc + V(x, y, z) * hs
    kind = P["kind"]
    head = ellipsoid(0.38 * hs, 0.38 * hs, 0.44 * hs, h(0, 0.12, -0.2))
    head = head.su(ellipsoid(0.28 * hs, 0.25 * hs, 0.3 * hs, h(0, 0.02, -0.42)), 0.15)
    if kind == "eagle":
        head = head.su(capsule(h(0.12, 0.29, -0.43), h(0.27, 0.27, -0.28), 0.08 * hs).mirror_x(), 0.07)
    head = head.ss(sphere(0.1 * hs, h(0.24, 0.16, -0.43)).mirror_x(), 0.04)
    H.piece("HeadP", "Head", head, col=P["head_col"], tris=1200, res=120, role="head")
    if kind == "eagle":
        beak = tube([h(0, 0.08, -0.45), h(0, 0.04, -0.75), h(0, -0.1, -0.97), h(0, -0.3, -0.95)], [0.21 * hs, 0.15 * hs, 0.08 * hs, 0.015 * hs], k=0.05)
    else:
        beak = tube([h(0, 0.02, -0.45), h(0, -0.04, -0.68), h(0, -0.12, -0.8)], [0.17 * hs, 0.1 * hs, 0.02 * hs], k=0.05)
    beak = squash(beak, h(0, 0, -0.7), (1, 0, 0), 0.72).su(ellipsoid(0.23 * hs, 0.13 * hs, 0.11 * hs, h(0, 0.04, -0.47)), 0.05)
    H.piece("Beak", "Head", beak, col="beak", mat="hard", tris=600, role="beak", pri=1.3)
    H.bone("Jaw", "Head", tuple(h(0, -0.08, -0.43)))
    lb = squash(tube([h(0, -0.1, -0.47), h(0, -0.13, -0.7), h(0, -0.17, -0.83)], [0.14 * hs, 0.09 * hs, 0.03 * hs]), h(0, 0, -0.7), (1, 0, 0), 0.75)
    H.piece("JawP", "Jaw", lb, col="beak", mat="hard", tris=320, role="jaw", pri=1.4)
    H.eyes("Head", h(0.24, 0.16, -0.45), 0.085 * hs, col="iris", pupil="round", look=(0.7, 0.05, -0.8))
    crest = None
    cc = P["crest"]
    if cc == "flame":
        for k in range(7):
            a = -0.6 + 0.2 * k
            q = h(0.18 * a, 0.42, -0.2 + 0.1 * abs(a))
            d = nrm(V(a * 0.5, 1.0, 0.6 + 0.3 * abs(a)))
            f_ = flat_tube([q, q + d * 0.5 * hs, q + d * 0.9 * hs + V(0, 0, 0.35) * hs, q + d * 1.1 * hs + V(0, -0.1, 0.75) * hs],
                           [0.1 * hs, 0.09 * hs, 0.06 * hs, 0.01 * hs], (1, 0, 0), 0.4)
            crest = f_ if crest is None else crest.su(f_, 0.04)
    elif cc == "storm":
        for k in range(5):
            a = -0.4 + 0.2 * k
            q = h(0.15 * a, 0.42, -0.1)
            d = nrm(V(a * 0.6, 0.55, 1.0))
            f_ = flat_tube([q, q + d * 0.7 * hs, q + d * 1.25 * hs + V(0, 0.25, 0) * hs], [0.1 * hs, 0.08 * hs, 0.01 * hs], (1, 0, 0), 0.4)
            crest = f_ if crest is None else crest.su(f_, 0.04)
    elif cc == "comb":
        for k in range(5):
            q = h(0, 0.45, -0.45 + 0.17 * k)
            crest = sphere(0.13 * hs, q + V(0, 0.12, 0) * hs) if crest is None else crest.su(sphere((0.13 - 0.01 * k) * hs, q + V(0, 0.1 + 0.03 * math.sin(k * 2), 0) * hs), 0.05)
        crest = squash(crest.su(ellipsoid(0.08 * hs, 0.12 * hs, 0.42 * hs, h(0, 0.42, -0.1)), 0.06), h(0, 0.5, 0), (1, 0, 0), 0.4)
        wattle = ellipsoid(0.07 * hs, 0.17 * hs, 0.09 * hs, h(0.06, -0.32, -0.55)).mirror_x()
        H.piece("Wattle", "Jaw", wattle, col="red", tris=250, role="detail", pri=1.6)
    if crest is not None:
        H.piece("Crest", "Head", crest, col="secondary" if cc != "comb" else "red", tris=1000 if cc != "comb" else 500, res=128, role="horn", pri=1.3)

    # wings
    if P["wings"] == "feather":
        wings = feather_wing(H, v(0.5, bodyY + 0.75, -0.45), 1.15 * s * P["wing"], raise_=0.6, sweep=-0.05, col_arm=P["arm_col"], col_hand=P["hand_col"],
                             flame=fl, tris=(1500, 1500))
    else:   # bat wings (cockatrice)
        S0 = v(0.45, bodyY + 0.7, -0.4)
        WS = s * P["wing"]
        E = S0 + V(1.1, 0.9, 0.5) * WS
        W = S0 + V(2.4, 1.8, -0.25) * WS
        F = [S0 + V(5.0, 1.0, 0.3) * WS, S0 + V(4.6, -0.1, 1.5) * WS, S0 + V(3.5, -0.75, 2.3) * WS, S0 + V(2.1, -0.75, 2.4) * WS]
        B1 = v(0.4, bodyY + 0.2, 0.8)
        upn = nrm(np.cross(F[1] - W, F[3] - W))
        if upn[1] < 0:
            upn = -upn
        t = 0.045 * s
        _pts = [S0, E, W, B1] + F
        H.mbone("Wing#", "Body", tuple(S0))
        H.mbone("Hand#", "Wing#", tuple(W))
        arm = round_cone(S0, E, 0.16 * s, 0.11 * s).su(round_cone(E, W, 0.11 * s, 0.08 * s), 0.05 * s)
        inner = [W, F[3]] + scallop(F[3], B1, E + (S0 - E) * 0.3, 0.2, 0.2 * s, upn, 5) + [S0 + (B1 - S0) * 0.1]
        mem_in = bounded(union_hard([fan(E, inner, t), tri(S0, E, W, t)]), np.min(_pts, 0), np.max(_pts, 0), 0.4 * s)
        H.mpiece("WingArm#", "Wing#", arm.su(mem_in, 0.025 * s), col="membrane", tris=900, res=140, role="wing", pri=1.2, smooth=2)
        hand = sphere(0.11 * s, W)
        for i, f in enumerate(F):
            hand = hand.su(round_cone(W, f, (0.075 - 0.008 * i) * s, 0.02 * s), 0.03 * s)
        mem_out = bounded(membrane(W, F, t=t, depth=0.24, sag=0.2 * s, up=upn, n=5), np.min(_pts, 0), np.max(_pts, 0), 0.4 * s)
        H.mpiece("WingHand#", "Hand#", hand.su(mem_out, 0.025 * s), col="membrane", tris=1100, res=140, role="wing", pri=1.25, smooth=2)
        wings = [("WingR", "HandR", 1), ("WingL", "HandL", -1)]

    # tail
    tail_b = []
    t0 = v(0, bodyY - 0.1, 1.35)
    tk_ = P["tail"]
    if tk_ == "fan":
        H.bone("Tail1", "Body", tuple(t0))
        tail_b = ["Tail1"]
        fanp = None
        for k in range(9):
            a = math.radians(-36 + 9 * k)
            d = nrm(V(math.sin(a), -0.35, math.cos(a)))
            f_ = feather(t0 + V(0, 0.02 * abs(k - 4), 0) * s, d, 2.0 * s, 0.26 * s, V(0, 1, 0.3), th=0.05 * s, curl=0.1 * s)
            fanp = f_ if fanp is None else fanp.su(f_, 0.02 * s)
        H.piece("TailFan", "Tail1", fanp, col=P["tail_col"], tris=1100, res=140, role="tail", pri=1.4,
                pattern=stripes(lambda Q: (Q[:, 2] - t0[2]) / s, 2.0, width=0.18, depth=0.3))
    elif tk_ == "plumes":
        pts = [t0, t0 + v(0, -0.55, 1.6), t0 + v(0, -1.0, 3.3), t0 + v(0, -0.75, 5.1)]
        for i in range(3):
            H.bone(f"Tail{i + 1}", "Body" if i == 0 else f"Tail{i}", tuple(pts[i]))
            tail_b.append(f"Tail{i + 1}")
        # root fan of flame feathers (Tail1), then the long plumes in two halves (Tail2, Tail3)
        rootf = None
        for k in range(7):
            a = math.radians(-40 + 13.3 * k)
            d = nrm(V(math.sin(a), -0.25, math.cos(a)))
            f_ = feather(t0, d, 1.5 * s, 0.26 * s, V(0, 1, 0.2), th=0.05 * s, curl=0.25 * s)
            rootf = f_ if rootf is None else rootf.su(f_, 0.02)
        H.piece("TailA", "Tail1", rootf, col=P["tail_col"], tris=900, res=130, role="tail", pri=1.4)
        for half in range(2):
            plume = None
            for k in range(5):
                off = (k - 2) * 0.4
                wig = 0.35 * (1 if k % 2 else -1)
                a0 = pts[1 + half] + V(off * (0.6 + 0.6 * half), 0.05 * abs(k - 2), 0) * s
                a1 = pts[2 + half] + V(off * (1.0 + 0.8 * half) + wig, -0.1 * abs(k - 2) + 0.15 * half * (2 - abs(k - 2)), 0.1 * k * half) * s
                mid = (a0 + a1) / 2 + V(-wig * 0.6, 0.2, 0) * s
                rr = [0.2, 0.28, 0.22] if half == 0 else [0.22, 0.34, 0.03]
                f_ = flat_tube([a0 - (a1 - a0) * 0.12, mid, a1], [r * s for r in rr], V(0, 1, 0.1), flat=0.3)
                if half == 1:   # eye-spot flame tip
                    f_ = f_.su(squash(sphere(0.42 * s, a1 - (a1 - a0) * 0.22), a1, V(0, 1, 0.1), 0.3), 0.1)
                plume = f_ if plume is None else plume.su(f_, 0.04)
            H.piece("Plume" + "AB"[half], tail_b[1 + half], plume, col="secondary" if half else P["tail_col"], tris=1200, res=150, role="tail",
                    pri=1.5 + 0.1 * half, pattern=stripes(lambda Q: Q[:, 2] / s, 1.4, width=0.2, depth=0.25) if half else None)
    elif tk_ == "serpent":
        pts = [t0, t0 + v(0, -0.5, 1.0), t0 + v(0.5, -1.2, 1.9), t0 + v(0.2, -1.6, 2.9), t0 + v(-0.6, -1.9, 3.5)]
        for i in range(4):
            H.bone(f"Tail{i + 1}", "Body" if i == 0 else f"Tail{i}", tuple(pts[i]))
            tail_b.append(f"Tail{i + 1}")
            r0, r1 = 0.32 - 0.07 * i, 0.32 - 0.07 * (i + 1)
            seg = round_cone(pts[i] - (pts[i + 1] - pts[i]) * 0.15, pts[i + 1], r0 * s, max(r1, 0.04) * s)
            if i == 3:
                seg = seg.su(spike(pts[4], pts[4] - pts[3], 0.35 * s, 0.07 * s), 0.03)
            H.piece(f"Tail{'ABCD'[i]}", f"Tail{i + 1}", seg, col="secondary", tris=450, role="tail", pri=1.4 + 0.1 * i,
                    pattern=stripes(lambda Q: Q[:, 2] / s, 3.0, width=0.2, depth=0.25))

    H.socket("mouth", h(0, -0.1, -0.95), "Jaw")
    H.socket("head", h(0, 0.55, -0.2), "Head")
    H.socket("seat", v(0, bodyY + 1.0, -0.1), "Body")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": tail_b, "neck": ["Neck"],
                  "legs": [{"hip": "HipR", "knee": "KneeR", "side": 1}, {"hip": "HipL", "knee": "KneeL", "side": -1}]})
    legs = [("HipR", "KneeR", "FootR", False, 1), ("HipL", "KneeL", "FootL", False, -1)]
    mm.flyer(H, legs, wings, neck=["Neck"], head="Head", jaw="Jaw", tail=tail_b, height=bodyY + 1.5 * s, hipz=0.1 * s, flap=1.0, lift=0.3,
             period=0.95, tuck=1.25, idle_wing=2.2)
    return H


@hero("phoenix", "mythic")
def phoenix():
    return _bird("phoenix", flame=1.0, crest="flame", tail="plumes", arm_col="primary", hand_col="secondary", tail_col="primary", head_col="primary",
                 breast_col="secondary", head=0.95,
                 preview={"primary": "#EA580C", "secondary": "#FACC15", "beak": "#F2C23B", "iris": "#FFE7A3"})


@hero("thunderbird", "mythic")
def thunderbird():
    return _bird("thunderbird", crest="storm", tail="fan", wing=1.15, arm_col="primary", hand_col="secondary", tail_col="primary", head_col="primary",
                 head=1.1, preview={"primary": "#1E3A8A", "secondary": "#FDE047", "beak": "#E8C23B", "iris": "#FDE047"})


@hero("roc", "mythic")
def roc():
    return _bird("roc", crest=None, tail="fan", wing=1.1, talon=1.35, head=1.1, head_col="secondary", arm_col="primary", hand_col="primary",
                 preview={"primary": "#78350F", "secondary": "#FDE68A", "beak": "#E8B23B", "iris": "#E8821E"})


@hero("cockatrice", "mythic")
def cockatrice():
    return _bird("cockatrice", kind="rooster", wings="bat", crest="comb", tail="serpent", wing=0.85, head=1.1, talon=1.1,
                 preview={"primary": "#F59E0B", "secondary": "#4D7C0F", "membrane": "#A86A2A", "beak": "#F2C23B", "iris": "#E83A1E", "red": "#D9372B"})
