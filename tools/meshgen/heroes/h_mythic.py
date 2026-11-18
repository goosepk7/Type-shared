"""Mythic beasts on four legs: griffin (saddled mount), hippogriff, manticore, chimera, cerberus, sphinx, kitsune,
qilin and behemoth.

One parametric chimera-builder (`_beast`): a torso archetype (lion, hound, fox, horse, colossus), front and hind legs
by foot type (lion paw, eagle talon, hoof, pillar foot), one or more heads from a head library (eagle with a hooked
two-part beak and ear tufts, lion with jaw and mane, hound, fox, goat, human pharaoh face with nemes headdress, qilin
with a single horn and flowing mane, horned behemoth), wings (feathered on two bones with fanned primaries, or bat
wings shared with the dragons), and tails (tufted lion tail, scorpion stinger, snake with its own head, nine fox
tails, flame tail, horse tail). Motion: motion.quadruped for the walk / attack, motion_mythic.flyer for winged
mounts (they fly when moving), with wing flutter overlays.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from kit import Hero, hero, stripes, spots, combine
import motion
import motion_mythic as mm
from mythic_geo import (V, nrm, tri, fan, membrane, scallop, union_hard, bounded, frame, oell, squash, flat_tube, spike, curved_horn,
                        blade_fin, surface_y, outside, band_y, feather, Shift)


def _rotz(p, c, a):
    """Rotate point p about the Z axis through c by a (radians): +a raises a +X point."""
    q = V(p) - c
    ca, sa = math.cos(a), math.sin(a)
    return c + V(q[0] * ca - q[1] * sa, q[0] * sa + q[1] * ca, q[2])


def feather_wing(H, S0, sc, raise_=0.55, sweep=0.0, col_arm="primary", col_hand="primary", flame=0.0, tris=(1500, 1500), bone_parent="Body",
                 coverts_col=None, span=1.0, basis=None):
    """Big feathered wing (right side, mirrored): arm bone at S0 with the arm, coverts, secondaries and tertials;
    hand bone at the wrist with ten fanned primaries. flame > 0 makes flame-shaped curling feathers (phoenix)."""
    S0 = V(S0)

    def L(x, y, z):
        if basis is not None:     # explicit local -> model axes (columns: span, normal, chord)
            return S0 + basis @ V(x * span, y, z) * sc
        p = S0 + V(x * span, y, z) * sc
        p = _rotz(p, S0, raise_)
        if sweep:
            q = p - S0
            cb, sb = math.cos(sweep), math.sin(sweep)
            p = S0 + V(q[0] * cb + q[2] * sb, q[1], -q[0] * sb + q[2] * cb)
        return p

    def D(x, y, z):
        return nrm(L(x, y, z) - L(0, 0, 0))

    E, W, Tp = L(1.5, 0.2, 0.3), L(3.0, 0.3, -0.12), L(4.3, 0.25, 0.0)
    up = nrm(np.cross(D(0, 0, 1), D(1, 0, 0)))
    if up[1] < 0:
        up = -up
    th = 0.05 * sc
    cf = 0.22 * flame
    arm = round_cone(S0 - (E - S0) * 0.15, E, 0.26 * sc, 0.17 * sc).su(round_cone(E, W, 0.17 * sc, 0.12 * sc), 0.08 * sc)
    arm = arm.su(ellipsoid(0.5 * sc, 0.2 * sc, 0.35 * sc, (S0 + E) / 2 + up * 0.05 * sc), 0.1 * sc)
    fe = []
    for k in range(9):                                    # secondaries / tertials along the arm
        u = k / 8
        p0 = E + (W - E) * (1 - u / 0.55) if u < 0.55 else S0 + (E - S0) * (1 - (u - 0.55) / 0.45) * 0.95
        d = nrm(D(0.12 - 0.15 * u, -0.25, 1.0))
        fe.append(feather(p0 - up * 0.02 * k * sc, d, (2.0 - 0.35 * u) * sc, (0.46 + 0.04 * flame) * sc, up, th=th, curl=(0.15 + cf) * sc))
    for row, (n_, ln, off) in enumerate(((8, 1.0, 0.12), (7, 0.6, 0.2))):     # coverts
        for k in range(n_):
            u = (k + 0.5) / n_
            p0 = S0 + (W - S0) * (0.08 + 0.9 * u) + up * off * sc
            fe.append(feather(p0, nrm(D(0.05, -0.2, 1.0)), ln * sc * (1.0 - 0.2 * u), 0.36 * sc, up, th=th))
    arm_core = arm
    for f_ in fe:
        arm = arm.su(f_, 0.025 * sc)
    lo, hi = np.min([S0, E, W, Tp], 0) - 0.5 * sc, np.max([S0, E, W, Tp], 0) + 2.6 * sc
    H.mbone("Wing#", bone_parent, tuple(S0))
    H.mbone("Hand#", "Wing#", tuple(W))
    H.mpiece("WingArm#", "Wing#", bounded(arm, lo - 2.2 * sc, hi, 0.3 * sc), col=col_arm, mat="skin", tris=tris[0], res=150, role="wing", pri=1.2, smooth=2,
             pattern=combine(outside(arm_core, 0.02, 0.86, 0.1), stripes(lambda Q: np.linalg.norm(Q - S0, axis=1) / sc, 2.2, width=0.1, depth=0.12)))
    hand = round_cone(W - (W - E) * 0.15, Tp, 0.13 * sc, 0.06 * sc)
    for k in range(10):
        s_ = k / 9
        p0 = Tp + (W - Tp) * (s_ * 0.92)
        d = nrm(D(math.cos(math.radians(-4 + 70 * s_)), -0.1 - 0.15 * s_, math.sin(math.radians(-4 + 70 * s_))))
        hand = hand.su(feather(p0 - up * 0.02 * k * sc, d, (2.7 - 0.7 * s_) * sc, (0.4 + 0.05 * flame) * sc, up, th=th, curl=(0.25 + cf * 1.3) * sc), 0.025 * sc)
    H.mpiece("WingHand#", "Hand#", bounded(hand, lo - 2.5 * sc, hi + 1.0 * sc, 0.3 * sc), col=col_hand, mat="skin", tris=tris[1], res=150, role="wing", pri=1.25, smooth=2,
             pattern=stripes(lambda Q: np.linalg.norm(Q - W, axis=1) / sc, 1.3, width=0.12, depth=0.14))
    return [("WingR", "HandR", 1), ("WingL", "HandL", -1)]


BASE = dict(
    s=1.0, leg=1.0, body=1.0, girth=1.0, neck=1.0, head=1.0,
    torso="lion",          # lion | hound | fox | horse | colossus
    front="paw",           # paw | talon | hoof | pillar
    hind="paw",
    heads=("lion",),       # head kinds; several = multi-headed
    mane=False,
    wings=None,            # None | "feather" | "bat" | "folded"
    wing=1.0,
    tail="lion",           # lion | scorpion | snake | fox9 | flame | horse | stub
    saddle=False,
    goat=False,            # chimera: goat head rising from the back
    collar=False,
    pattern=None,
    front_col="primary", head_col="primary", wing_col="primary",
    gait="trot",
    flyer=False,
    preview={},
)


def _beast(hid, plan="Quadruped", **kw):
    P = dict(BASE)
    P.update(kw)
    s, LG, BL, G = P["s"], P["leg"], P["body"], P["girth"]
    H = Hero(hid, plan=plan, gait=P["gait"], tags=["mythic"])
    H.preview = P["preview"]
    tk = P["torso"]

    def v(x, y, z):
        return V(x, y, z) * s

    lift = 3.0 * LG
    if tk == "horse":
        lift = 3.3 * LG
    if tk == "colossus":
        lift = 2.6 * LG
    bodyY = lift + 0.05
    zc, zr = -1.5 * BL, 1.45 * BL
    H.body(v(0, bodyY, 0))

    # ------------------------------------------------------------------ torso
    if tk in ("lion", "hound", "fox"):
        g2 = G * (0.82 if tk == "fox" else 1.0)
        torso = ellipsoid(0.84 * g2 * s, 1.0 * g2 * s, 1.35 * BL * s, v(0, bodyY + 0.05, zc + 0.55 * BL))
        waist = 0.74 if tk == "lion" else 0.62
        torso = torso.su(ellipsoid(0.66 * g2 * s, waist * g2 * s, 1.2 * BL * s, v(0, bodyY + 0.15, 0.45 * BL)), 0.45)
        torso = torso.su(ellipsoid(0.76 * g2 * s, 0.84 * g2 * s, 0.95 * BL * s, v(0, bodyY + 0.2, zr)), 0.45)
        torso = torso.su(ellipsoid(0.33 * g2 * s, 0.62 * s, 0.55 * s, v(0.6 * g2, bodyY + 0.32, zc + 0.15)).mirror_x(), 0.25)
        torso = torso.su(ellipsoid(0.62 * g2 * s, 0.75 * g2 * s, 0.6 * s, v(0, bodyY - 0.42, zc - 0.25)), 0.4)
        torso = torso.su(ellipsoid(0.42 * g2 * s, 0.7 * s, 0.75 * s, v(0.58 * g2, bodyY + 0.05, zr + 0.1)).mirror_x(), 0.3)
        torso = torso.su(round_cone(v(0, bodyY + 0.35, zc - 0.25), v(0, bodyY + 0.85, zc - 0.85), 0.62 * g2 * s, 0.5 * g2 * s), 0.35)
        G = g2
    elif tk == "horse":
        torso = ellipsoid(0.78 * G * s, 0.92 * G * s, 1.5 * BL * s, v(0, bodyY + 0.2, zc + 0.6))
        torso = torso.su(ellipsoid(0.74 * G * s, 0.85 * G * s, 1.4 * BL * s, v(0, bodyY + 0.2, 0.4 * BL)), 0.5)
        torso = torso.su(ellipsoid(0.78 * G * s, 0.85 * G * s, 0.95 * BL * s, v(0, bodyY + 0.3, zr)), 0.45)
        torso = torso.su(ellipsoid(0.42 * G * s, 0.75 * s, 0.8 * s, v(0.5 * G, bodyY + 0.15, zr + 0.15)).mirror_x(), 0.3)
        torso = torso.su(round_cone(v(0, bodyY + 0.4, zc - 0.3), v(0, bodyY + 1.1, zc - 0.95), 0.6 * G * s, 0.42 * G * s), 0.35)
    else:  # colossus
        torso = ellipsoid(1.35 * G * s, 1.3 * G * s, 1.7 * BL * s, v(0, bodyY + 0.3, zc + 0.6))
        torso = torso.su(ellipsoid(1.25 * G * s, 1.2 * G * s, 1.5 * BL * s, v(0, bodyY + 0.2, zr - 0.2)), 0.6)
        torso = torso.su(ellipsoid(0.5 * G * s, 0.8 * s, 1.0 * s, v(1.0 * G, bodyY + 0.1, zr)).mirror_x(), 0.35)
        torso = torso.su(ellipsoid(0.5 * G * s, 0.8 * s, 0.9 * s, v(1.0 * G, bodyY + 0.2, zc + 0.1)).mirror_x(), 0.35)
        hump = ellipsoid(0.9 * G * s, 0.7 * s, 1.0 * s, v(0, bodyY + 1.25, zc + 0.3))
        torso = torso.su(hump, 0.5)
        torso = torso.su(round_cone(v(0, bodyY + 0.5, zc - 0.4), v(0, bodyY + 0.7, zc - 1.0), 1.0 * G * s, 0.85 * G * s), 0.4)
    core = torso
    if tk == "colossus":   # armour plates and dorsal horns
        for i, z in enumerate(np.linspace(zc - 0.2, zr + 0.8, 7)):
            y = surface_y(core, 0.0, z * s, (bodyY + 3) * s, bodyY * s) / s
            torso = torso.su(blade_fin(V(0, y - 0.15, z) * s, (0, 1, 0.3), (0.6 + 0.15 * math.sin(i * 1.3)) * s, 0.22 * s, (1, 0, 0), flat=0.45, back=(0, 0, 1)), 0.08)
    pat = None
    if P["pattern"] == "scales":
        pat = spots(0.22 * s, 0.1 * s, depth=0.25, ring=True, seed=4)
    elif P["pattern"] == "plates":
        pat = stripes(lambda Q: Q[:, 2] / s, 1.5, width=0.12, depth=0.35)

    def back_shade(Q):
        return 1.0 - 0.15 * np.clip((Q[:, 1] - (bodyY - 0.9) * s) / (1.6 * s), 0, 1)

    H.piece("Torso", "Body", torso, col="primary", tris=2400, res=128, pattern=combine(back_shade, pat, outside(core, 0.05, 0.55, 0.1)))

    # ------------------------------------------------------------------ legs
    def paw(c, big=1.0):
        c = V(c)
        k = s * big
        p = round_cone(c + V(0, 0.08, 0) * k, c + V(0, -0.22, -0.12) * k, 0.18 * k, 0.2 * k)
        p = p.su(ellipsoid(0.26 * k, 0.15 * k, 0.3 * k, c + V(0, -0.3, -0.2) * k), 0.1 * k)
        cr = p
        for dx in (-0.15, -0.05, 0.05, 0.15):
            p = p.su(sphere(0.095 * k, c + V(dx, -0.33, -0.43 + 0.2 * abs(dx)) * k), 0.05 * k)
            cr = cr.su(sphere(0.095 * k, c + V(dx, -0.33, -0.43 + 0.2 * abs(dx)) * k), 0.05 * k)
            p = p.su(curved_horn([c + V(dx, -0.3, -0.48 + 0.2 * abs(dx)) * k, c + V(dx, -0.33, -0.56) * k, c + V(dx, -0.39, -0.6) * k], 0.035 * k, 0.008 * k), 0.01)
        return p & plane((0, -1, 0), 0.0), outside(cr, 0.02, 0.35, 0.04)

    def talon(c, big=1.0):
        c = V(c)
        k = s * big
        p = round_cone(c + V(0, 0.15, 0.02) * k, c + V(0, -0.25, -0.05) * k, 0.15 * k, 0.15 * k)
        cr = p
        tal = []
        for a in (-0.5, 0.0, 0.5):
            d = nrm(V(math.sin(a), 0, -math.cos(a)))
            p1 = c + V(0, -0.3, 0) * k + d * 0.45 * k
            toe = tube([c + V(0, -0.25, 0) * k, c + V(0, -0.3, 0) * k + d * 0.25 * k, p1], [0.09 * k, 0.075 * k, 0.06 * k])
            cr = cr.su(toe, 0.04 * k)
            tal.append(curved_horn([p1, p1 + d * 0.12 * k + V(0, 0.02, 0) * k, p1 + d * 0.2 * k - V(0, 0.1, 0) * k], 0.055 * k, 0.01 * k))
        p1 = c + V(0, -0.3, 0.38) * k
        cr = cr.su(round_cone(c + V(0, -0.25, 0) * k, p1, 0.08 * k, 0.06 * k), 0.03 * k)
        tal.append(curved_horn([p1, p1 + V(0, -0.0, 0.12) * k, p1 + V(0, -0.1, 0.18) * k], 0.05 * k, 0.01 * k))
        p = cr
        for t_ in tal:
            p = p.su(t_, 0.015 * k)
        sc_ = stripes(lambda Q: Q[:, 1] / k, 7.0, width=0.25, depth=0.15)
        return p & plane((0, -1, 0), 0.0), combine(outside(cr, 0.02, 0.25, 0.04), sc_)

    def hoof(c, big=1.0, feather_=False):
        c = V(c)
        k = s * big
        p = round_cone(c + V(0, 0.55, 0.05) * k, c + V(0, 0.12, 0.0) * k, 0.12 * k, 0.17 * k)       # pastern
        hf = cone(0.22 * k, 0.17 * k, 0.12 * k).at(*(c + V(0, 0.12, -0.02) * k))
        return p, hf.round(0.02 * k) & plane((0, -1, 0), 0.0)

    def pillar(c, big=1.0):
        c = V(c)
        k = s * big
        p = cylinder(0.42 * k, 0.3 * k, rr=0.1 * k).at(*(c + V(0, 0.3, 0) * k))
        cr = p
        for a in (-0.7, -0.25, 0.25, 0.7):
            p = p.su(ellipsoid(0.12 * k, 0.1 * k, 0.08 * k, c + V(math.sin(a) * 0.42, 0.1, -math.cos(a) * 0.42) * k), 0.03)
        return p & plane((0, -1, 0), 0.0), outside(cr, 0.02, 0.6, 0.05)

    legs4 = []
    thick = 1.55 if tk == "colossus" else (0.8 if tk == "fox" else (0.85 if tk == "horse" else 1.0))
    for front in (True, False):
        ft = P["front"] if front else P["hind"]
        x = (0.6 if front else 0.56) * G * (1.35 if tk == "colossus" else 1.0)
        if front:
            a = v(x, bodyY + 0.05, zc + 0.15)
            b = v(x, lift * 0.6, zc + 0.35)
            c = v(x * 0.97, 0.42 * (1.3 if ft == "hoof" else 1.0), zc + 0.15)
            names = ("ShoulderF#", "ElbowF#", "WristF#", "UpperF#", "ForeF#", "PawF#")
        else:
            a = v(x, bodyY + 0.15, zr + 0.05)
            b = v(x * 1.08, lift * 0.62, zr - 0.45)
            c = v(x * 1.05, lift * (0.36 if ft == "hoof" else 0.33), zr + 0.42)
            names = ("HipB#", "KneeB#", "HockB#", "Thigh#", "Shin#", "PawB#")
        if ft == "pillar":   # elephantine: straight columns
            b = V(a[0], lift * 0.5 * s, a[2] + 0.05 * s)
            c = V(a[0], 0.75 * s, a[2])
        H.mbone(names[0], "Body", tuple(a))
        H.mbone(names[1], names[0], tuple(b))
        H.mbone(names[2], names[1], tuple(c))
        r0 = (0.44 if front else 0.55) * G * s * thick
        up_ = round_cone(a + v(0, 0.15 if front else 0.2, 0), b, r0, 0.27 * s * thick)
        up_ = up_.su(ellipsoid(r0 * 0.75, 0.75 * LG * s, r0 * 1.15, a + v(0.02, -0.5 * LG, 0)), 0.25)
        colu = P["front_col"] if front else "primary"
        H.mpiece(names[3], names[0], up_, col=colu, tris=650 if tk != "colossus" else 800, role="limb", pattern=pat)
        lo_ = round_cone(b, c + v(0, 0.05, 0), 0.27 * s * thick, 0.17 * s * thick)
        lo_ = lo_.su(ellipsoid(0.22 * s * thick, 0.45 * LG * s, 0.27 * s * thick, b + v(0.01, -0.35 * LG, (-0.05 if front else 0.2))), 0.15)
        colf = colu
        if ft == "talon":
            lo_ = round_cone(b, c + v(0, 0.05, 0), 0.24 * s * thick, 0.13 * s)
            colf = "beak"
        H.mpiece(names[4], names[1], lo_, col=colu if ft != "talon" else colu, tris=520, role="limb", pattern=pat)
        if ft == "paw":
            pc = c if front else v(x * 1.05, 0.42, zr + 0.18)
            shape, fp = paw(pc, 1.0 * thick ** 0.5)
            if not front:
                shape = shape.su(round_cone(c, pc, 0.16 * s * thick, 0.17 * s * thick), 0.08)
            H.mpiece(names[5], names[2], shape, col=colu, tris=550, role="foot", pattern=fp)
        elif ft == "talon":
            pc = c + v(0, -0.12, -0.05) if front else v(x * 1.05, 0.42, zr + 0.1)
            shape, fp = talon(pc, 1.1)
            shape = shape.su(round_cone(c + v(0, 0.1, 0), pc, 0.13 * s, 0.13 * s), 0.06)
            H.mpiece(names[5], names[2], shape, col="beak", mat="skin", tris=650, role="foot", pattern=fp)
        elif ft == "hoof":
            pc = V(c[0], 0.0, c[2] - (0.05 if front else 0.35) * s)
            can, hf = hoof(pc, 1.0 * thick ** 0.4)
            can = can.su(round_cone(c, pc + v(0, 0.55, 0.05), 0.15 * s, 0.12 * s), 0.06)
            can = can.su(sphere(0.17 * s, c), 0.05)
            if tk == "horse" and hid in ("qilin",):   # fetlock flame tufts
                can = can.su(flat_tube([pc + v(0, 0.5, 0.1), pc + v(0, 0.3, 0.35), pc + v(0, 0.15, 0.5)], [0.1 * s, 0.07 * s, 0.015 * s], (1, 0, 0), 0.4), 0.04)
            H.mpiece(names[5], names[2], can, col=colu, tris=450, role="foot", pattern=pat)
            H.mpiece("Hoof" + ("F#" if front else "B#"), names[2], hf, col="hoof", mat="hard", tris=220, role="foot", pri=1.6)
        else:
            shape, fp = pillar(V(c[0], 0, c[2]), 1.0)
            shape = shape.su(round_cone(c + v(0, 0.2, 0), V(c[0], 0.5 * s, c[2]), 0.38 * s, 0.42 * s), 0.1)
            H.mpiece(names[5], names[2], shape, col="primary", tris=600, role="foot", pattern=fp)
        legs4.append((names[0].replace("#", "R"), names[1].replace("#", "R"), names[2].replace("#", "R"), front))
        legs4.append((names[0].replace("#", "L"), names[1].replace("#", "L"), names[2].replace("#", "L"), front))

    # ------------------------------------------------------------------ necks + heads
    heads = P["heads"]
    nh = len(heads)
    jaws, headbones, necks = [], [], []
    mouth = None
    for i, kind in enumerate(heads):
        off = (i - (nh - 1) / 2)
        sx = off * 1.05 * s
        yaw = off * 0.45
        NK = P["neck"]
        if tk == "horse":
            n0 = v(0, bodyY + 0.75, zc - 0.7)
            hc = n0 + v(0, 1.1, -0.95) * NK
        elif tk == "colossus":
            n0 = v(0, bodyY + 0.6, zc - 0.9)
            hc = n0 + v(0, 0.1, -0.75) * NK
        else:
            n0 = v(0, bodyY + 0.65, zc - 0.7)
            hc = n0 + v(0, 0.55, -0.95) * NK
        hc = hc + V(sx * 1.25, -abs(off) * 0.25 * s, abs(off) * 0.35 * s) + (v(0, 0.35, -0.25) if nh > 1 and off == 0 else V(0, 0, 0))
        nb = "Neck" if nh == 1 else f"Neck{i + 1}"
        hb = "Head" if nh == 1 else f"Head{i + 1}"
        H.bone(nb, "Body", tuple(n0 + V(sx * 0.4, 0, 0)))
        H.bone(hb, nb, tuple(hc))
        headbones.append(hb)
        necks.append(nb)
        nr = (0.5 if tk != "colossus" else 0.85) * G * s
        if tk == "horse":
            neck = tube([n0 + v(0, -0.25, 0.3), (n0 + hc) / 2 + v(0, 0.05, 0.1), hc + v(0, -0.1, 0.25)], [0.7 * G * s, 0.55 * s, 0.45 * s], k=0.15)
            neck = neck.su(ellipsoid(0.3 * s, 0.8 * s, 0.4 * s, (n0 + hc) / 2 + v(0, -0.25, -0.25)), 0.3)
        else:
            neck = tube([n0 + v(0, -0.3, 0.35) + V(sx * 0.3, 0, 0), (n0 + hc) / 2 + V(sx * 0.4, 0.05 * s, 0), hc + v(0, -0.1, 0.25)],
                        [nr * 1.2, nr * 0.95, nr * 0.8], k=0.15)
        hk = kind
        ncol = P["head_col"] if hk in ("eagle",) else "primary"
        if hk == "eagle":   # feathered ruff on the neck
            neck = neck.noise(0.03 * s, 6 / s, 3)
        H.piece("NeckP" if nh == 1 else f"NeckP{i + 1}", nb, neck, col=ncol, tris=800 if nh == 1 else 600, role="limb",
                pattern=pat if hk != "eagle" else stripes(lambda Q: Q[:, 1] / s, 3.0, width=0.15, depth=0.12))
        hs = s * P["head"]
        jaw, mth = HEADS[hk](Shift(H, hc[0]), hb, V(0, hc[1], hc[2]), hs, "" if nh == 1 else str(i + 1), P)
        mth = (mth[0] + hc[0], mth[1], mth[2])
        if jaw:
            jaws.append(jaw)
        if mouth is None or i == nh // 2:
            mouth = mth

    # ------------------------------------------------------------------ chimera goat head
    if P["goat"]:
        g0 = v(0, bodyY + 0.75, -0.2)
        gh = g0 + v(0.15, 1.35, -0.25)
        H.bone("GoatNeck", "Body", tuple(g0))
        H.bone("GoatHead", "GoatNeck", tuple(gh))
        H.piece("GoatNeckP", "GoatNeck", tube([g0 - v(0, 0.4, 0), (g0 + gh) / 2, gh + v(0, -0.1, 0.15)], [0.42 * s, 0.32 * s, 0.26 * s], k=0.1),
                col="light", tris=600, role="limb")
        head_goat(Shift(H, gh[0]), "GoatHead", V(0, gh[1], gh[2]), s * 0.85, "G", P)

    # ------------------------------------------------------------------ tail
    tail_b = []
    tkind = P["tail"]
    t0 = v(0, bodyY + 0.42, zr + 0.85 * BL)
    if tk == "horse":
        t0 = v(0, bodyY + 0.65, zr + 0.8 * BL)
    if tk == "colossus":
        t0 = v(0, bodyY + 0.3, zr + 1.2 * BL)
    if tkind in ("lion", "scorpion", "snake", "flame", "stub"):
        if tkind == "scorpion":
            dirs = [v(0, 0.5, 0.75), v(0, 1.0, 0.25), v(0, 0.75, -0.55), v(0, 0.2, -0.6)]
        elif tkind == "snake":
            dirs = [v(0, 0.05, 0.9), v(0, 0.5, 0.6), v(0, 0.7, 0.1), v(0, 0.25, -0.35)]
        elif tkind == "stub":
            dirs = [v(0, -0.3, 0.7), v(0, -0.5, 0.5), v(0, -0.3, 0.3)]
        else:
            dirs = [v(0, -0.25, 0.85), v(0, -0.75, 0.55), v(0, -0.6, 0.3)]
        if tkind == "flame":
            dirs = [v(0, 0.2, 0.85), v(0, -0.2, 0.75), v(0, -0.45, 0.55)]
        pts_ = [t0]
        for d in dirs:
            pts_.append(pts_[-1] + d)
        nseg = len(dirs)
        tr = (0.17 if tkind != "snake" else 0.24) * s * (1.6 if tk == "colossus" else 1.0)
        for i in range(nseg):
            b = f"Tail{i + 1}"
            H.bone(b, "Body" if i == 0 else f"Tail{i}", tuple(pts_[i]))
            tail_b.append(b)
            a_, b_ = pts_[i], pts_[i + 1]
            r0_, r1_ = tr * (1 - 0.15 * i), tr * (1 - 0.15 * (i + 1))
            if tkind == "scorpion":
                r0_, r1_ = tr * (1.25 - 0.1 * i), tr * (1.25 - 0.1 * (i + 1))
            seg = round_cone(a_ - (b_ - a_) * 0.12, b_, r0_, r1_)
            col = "primary"
            if tkind == "scorpion":
                seg = seg.su(sphere(r0_ * 1.15, a_), 0.05)                 # segmented carapace
                col = "secondary" if i > 0 else "primary"
            if tkind == "snake":
                col = "secondary"
            last = i == nseg - 1
            if last and tkind == "lion" and not P.get("plain_tail"):
                seg = seg.su(ellipsoid(0.24 * s, 0.38 * s, 0.24 * s, b_ + v(0, -0.15, 0.05)).noise(0.05 * s, 9 / s, 12), 0.08)
                H.piece(f"Tail{'ABCD'[i]}", b, seg, col="secondary", tris=500, role="tail", pri=1.4 + 0.15 * i)
                continue
            if last and tkind == "scorpion":
                bulb = ellipsoid(0.26 * s, 0.24 * s, 0.32 * s, b_ + v(0, 0.0, -0.1))
                sting = curved_horn([b_ + v(0, -0.05, -0.3), b_ + v(0, -0.3, -0.55), b_ + v(0, -0.6, -0.55)], 0.1 * s, 0.01 * s)
                seg = seg.su(bulb, 0.06).su(sting, 0.04)
            if last and tkind == "flame":
                for j in range(5):
                    ang = -0.8 + 0.4 * j
                    dd = nrm(V(math.sin(ang) * 0.6, 0.4 * math.cos(ang * 2), 1.0))
                    seg = seg.su(flat_tube([b_ - v(0, 0, 0.1), b_ + dd * 0.5 * s + v(0, 0.2, 0), b_ + dd * 1.0 * s + v(0, 0.45, 0)],
                                           [0.14 * s, 0.1 * s, 0.015 * s], (1, 0, 0), 0.4), 0.05)
                col = "secondary"
            H.piece(f"Tail{'ABCD'[i]}", b, seg, col=col, tris=[550, 450, 450, 520][i] if not last else 650, role="tail", pri=1.4 + 0.15 * i,
                    pattern=stripes(lambda Q: Q[:, 1] / s + Q[:, 2] / s, 3.0, width=0.2, depth=0.35) if tkind == "snake" else None)
        if tkind == "snake":
            sh_ = pts_[-1]
            H.bone("SnakeHead", tail_b[-1], tuple(sh_))
            head_snake(H, "SnakeHead", sh_, s * 0.75, "S", P)
    elif tkind == "fox9":
        for i in range(9):
            a = math.radians(-80 + 20 * i)
            b = f"Tail{i + 1}"
            base = t0 + v(0, -0.05, 0.0)
            H.bone(b, "Body", tuple(base))
            tail_b.append(b)
            dd = nrm(V(math.sin(a) * 1.0, 0.75 + 0.35 * math.cos(a), 0.55))
            mid = base + dd * 1.1 * s + v(0, 0.25, 0.25)
            tip = base + dd * 2.1 * s + v(math.sin(a) * 0.2, 0.25 + 0.2 * math.cos(a), 0.65)
            tl = tube([base + dd * 0.1 * s, mid, tip + (tip - mid) * 0.1], [0.12 * s, 0.33 * s, 0.07 * s], k=0.1)
            tl = tl.su(sphere(0.2 * s, tip - (tip - mid) * 0.25), 0.15)
            H.piece(f"Tail{i + 1}P", b, tl, col="primary", tris=380, role="tail", pri=1.4 + 0.05 * i)
    elif tkind == "horse":
        b = "Tail1"
        H.bone(b, "Body", tuple(t0))
        H.bone("Tail2", "Tail1", tuple(t0 + v(0, -0.6, 0.55)))
        tail_b = ["Tail1", "Tail2"]
        tl = tube([t0 - v(0, 0, 0.1), t0 + v(0, -0.15, 0.35), t0 + v(0, -0.65, 0.6)], [0.2 * s, 0.2 * s, 0.24 * s], k=0.1)
        H.piece("TailA", "Tail1", tl.noise(0.03 * s, 8 / s, 2), col="secondary", tris=400, role="tail", pri=1.5)
        hair = None
        for j in range(6):
            ang = -0.5 + 0.2 * j
            q0 = t0 + v(0, -0.6, 0.55)
            q1 = q0 + v(math.sin(ang) * 0.35, -1.0, 0.35 + 0.1 * math.cos(j))
            q2 = q0 + v(math.sin(ang) * 0.45, -1.9, 0.25 + 0.15 * math.sin(j))
            f_ = tube([q0, q1, q2], [0.16 * s, 0.13 * s, 0.03 * s], k=0.05)
            hair = f_ if hair is None else hair.su(f_, 0.08)
        H.piece("TailB", "Tail2", hair.noise(0.03 * s, 8 / s, 3), col="secondary", tris=900, role="tail", pri=1.6)

    # ------------------------------------------------------------------ wings
    wings = []
    if P["wings"] == "feather":
        S0 = v(0.55 * G, bodyY + 0.75, zc + 0.35)
        wings = feather_wing(H, S0, 1.0 * s * P["wing"], raise_=0.55, sweep=-0.1, col_arm=P["wing_col"], col_hand=P["wing_col"], tris=(1400, 1400))
    elif P["wings"] == "folded":   # sphinx: wings folded along the flanks, tips up
        S0 = v(0.6 * G, bodyY + 0.65, zc + 0.3)
        xs = nrm(V(0.12, 0.42, 0.9))
        zs = nrm(V(0.12, 1.0, -0.35))
        zs = nrm(zs - (zs @ xs) * xs)
        ys = np.cross(zs, xs)
        S0 = v(0.72 * G, bodyY + 0.2, zc + 0.2)
        wings = feather_wing(H, S0, 0.62 * s * P["wing"], col_arm=P["wing_col"], col_hand=P["wing_col"], tris=(1200, 1200),
                             basis=np.stack([xs, ys, zs], axis=1))
    elif P["wings"] == "bat":
        S0 = v(0.55 * G, bodyY + 0.75, zc + 0.35)
        WS = s * P["wing"]
        E = S0 + V(1.3, 1.0, 0.65) * WS
        W = S0 + V(2.8, 2.1, -0.3) * WS
        F = [S0 + V(6.0, 1.3, 0.3) * WS, S0 + V(5.6, 0.0, 1.8) * WS, S0 + V(4.3, -0.8, 2.7) * WS, S0 + V(2.6, -0.8, 2.9) * WS]
        B1 = v(0.5 * G, bodyY + 0.45, zr - 0.2)
        upn = nrm(np.cross(F[1] - W, F[3] - W))
        if upn[1] < 0:
            upn = -upn
        t = 0.05 * s
        _pts = [S0, E, W, B1] + F
        H.mbone("Wing#", "Body", tuple(S0))
        H.mbone("Hand#", "Wing#", tuple(W))
        arm = round_cone(S0, E, 0.2 * s, 0.14 * s).su(round_cone(E, W, 0.14 * s, 0.1 * s), 0.06 * s)
        inner = [W, F[3]] + scallop(F[3], B1, E + (S0 - E) * 0.3, 0.2, 0.22 * s, upn, 5) + [S0 + (B1 - S0) * 0.1]
        mem_in = bounded(union_hard([fan(E, inner, t), tri(S0, E, W, t)]), np.min(_pts, 0), np.max(_pts, 0), 0.4 * s)
        H.mpiece("WingArm#", "Wing#", arm.su(mem_in, 0.03 * s), col="membrane", tris=1000, res=150, role="wing", pri=1.2, smooth=2)
        hand = sphere(0.14 * s, W)
        for i, f in enumerate(F):
            hand = hand.su(round_cone(W, f, (0.09 - 0.01 * i) * s, 0.025 * s), 0.04 * s)
        hand = hand.su(curved_horn([W, W + nrm(W - E) * 0.25 * s + v(0, 0.1, 0), W + nrm(W - E) * 0.4 * s], 0.06 * s, 0.01 * s), 0.03)
        mem_out = bounded(membrane(W, F, t=t, depth=0.24, sag=0.25 * s, up=upn, n=5), np.min(_pts, 0), np.max(_pts, 0), 0.4 * s)
        H.mpiece("WingHand#", "Hand#", hand.su(mem_out, 0.03 * s), col="membrane", tris=1200, res=150, role="wing", pri=1.25, smooth=2)
        wings = [("WingR", "HandR", 1), ("WingL", "HandL", -1)]

    # ------------------------------------------------------------------ saddle / collar
    if P["saddle"]:
        zs0 = zc + 0.95 * BL
        top = surface_y(core, 0.0, zs0 * s, (bodyY + 2.5) * s, bodyY * s) / s
        cloth = core.round(0.06 * s) & box(0.9 * G * s, 0.7 * s, 0.7 * s, v(0, top - 0.35, zs0))
        cloth = cloth.su(core.round(0.05 * s) & box(1.4 * s, 1.6 * s, 0.11 * s, v(0, bodyY, zs0 + 0.3)), 0.02)
        H.piece("SaddleCloth", "Body", cloth, col="secondary", mat="cloth", tris=700, res=120, role="detail", pri=1.3)
        seat = core.round(0.17 * s) & box(0.48 * G * s, 0.5 * s, 0.5 * s, v(0, top - 0.1, zs0))
        seat = seat.su(ellipsoid(0.22 * s, 0.22 * s, 0.13 * s, v(0, top + 0.2, zs0 - 0.46)), 0.08)
        seat = seat.su(ellipsoid(0.4 * s, 0.19 * s, 0.12 * s, v(0, top + 0.18, zs0 + 0.48)), 0.08)
        seat = seat.su(capsule(v(0.5 * G, top - 0.3, zs0 + 0.05), v(0.56 * G, top - 0.95, zs0 + 0.05), 0.045 * s).mirror_x(), 0.02)
        seat = seat.su(torus(0.1 * s, 0.033 * s, axis=2).at(*v(0.58 * G, top - 1.03, zs0 + 0.05)).mirror_x(), 0.02)
        H.piece("Saddle", "Body", seat, col="leather", mat="cloth", tris=800, res=128, role="detail", pri=1.2)
        H.socket("seat", v(0, top + 0.22, zs0), "Body")
        H.mount = {"seat": "Torso", "saddle": {"pos": tuple(v(0, top + 0.22, zs0)), "size": tuple(v(0.85 * G, 0.25, 1.0))}}
    else:
        H.socket("seat", v(0, bodyY + 1.05, zc + 0.9), "Body")
    if P["collar"]:
        for nb_, hb_ in zip(necks, headbones):
            hc_ = H.bpos(hb_)
            n0_ = H.bpos(nb_)
            c = n0_ + (hc_ - n0_) * 0.5
            d = nrm(hc_ - n0_)
            R = frame(d)
            col_ = torus(0.48 * s, 0.1 * s, axis=0)
            q = col_
            for k in range(8):
                a = k / 8 * math.tau
                q = q.su(spike(V(0, math.cos(a) * 0.55, math.sin(a) * 0.55) * s, (0, math.cos(a), math.sin(a)), 0.25 * s, 0.07 * s), 0.02)
            shape = (lambda q_, c_, R_: __import__("sdf").SDF(lambda p: q_((p - c_) @ R_)))(q, c, R)
            H.piece("Collar" + nb_[4:], nb_, shape, col="secondary", mat="metal", tris=700, role="detail", pri=1.4)

    # ------------------------------------------------------------------ rig, sockets, motion
    mb = jaws[len(jaws) // 2] if jaws else headbones[0]
    H.socket("mouth", mouth, mb)
    H.socket("head", tuple(H.bpos(headbones[nh // 2]) + v(0, 0.7, -0.3)), headbones[nh // 2])
    H.rig.update({"head": headbones[nh // 2], "tail": tail_b[:4]})
    if jaws:
        H.rig["jaw"] = jaws[len(jaws) // 2]
    H.rig["legs"] = [{"hip": a, "knee": b, "side": (1 if a.endswith("R") else -1)} for a, b, c, f in legs4]
    ql = []
    for a, b, c, f in legs4:
        side = a.endswith("R")
        ph = (0.75 if side else 0.25) if f else (0.5 if side else 0.0)
        ql.append((a, b, c, ph, f))
    height = bodyY + 1.0 * s
    tailb = tail_b if tkind != "fox9" else []
    if P["flyer"] and wings:
        fl = [(a, b, c, f, 1 if a.endswith("R") else -1) for a, b, c, f in legs4]
        mm.flyer(H, fl, wings, neck=necks[:1], head=headbones[0], jaw=jaws[0] if jaws else None, tail=tailb, height=height, hipz=zr * s,
                 flap=0.9, lift=0.25, period=1.0)
        # attack for a beaked mount: rear, strike with the talons and peck
    else:
        atk = P.get("attack", "pounce")
        motion.quadruped(H, ql, neck=necks[0], head=headbones[0], jaw=jaws[0] if jaws else None, tail=tailb, stride=0.42 if tk != "colossus" else 0.3,
                         walk=1.1 if tk != "colossus" else 1.5, height=height, attack=atk, swipe="ShoulderFR" if atk in ("pounce", "swipe") else None)
        extra_heads = list(zip(necks[1:], headbones[1:]))
        if extra_heads or wings or tkind == "fox9" or P["goat"]:
            def ov(name, rate):
                def f(t):
                    pose = {}
                    for j, (nb_, hb_) in enumerate(extra_heads):
                        ph = (j + 1) * 1.7
                        mm._add(pose, nb_, (0, 0, 0, 0.06 * math.sin(t * rate + ph), 0.15 * math.sin(t * rate * 0.5 + ph), 0))
                        mm._add(pose, hb_, (0, 0, 0, 0.08 * math.sin(t * rate * 1.3 + ph), 0.2 * math.sin(t * rate * 0.7 + ph), 0))
                    if wings:
                        mm.wing_flap(pose, wings, t * rate / (2 * math.pi) * 0.35, 0.22, base=0.0, sweep=0.03, fold=0.1)
                    if tkind == "fox9":
                        for j, b in enumerate(tail_b):
                            mm._add(pose, b, (0, 0, 0, 0.08 * math.sin(t * rate + j * 0.7), 0.12 * math.sin(t * rate * 0.5 + j * 0.9), 0))
                    if P["goat"]:
                        mm._add(pose, "GoatNeck", (0, 0, 0, 0.06 * math.sin(t * rate + 2), 0.15 * math.sin(t * rate * 0.5 + 1), 0))
                    return pose
                return f
            L = H.clips["Move"]["len"]
            mm.overlay(H, "Move", ov("Move", 2 * math.pi / L))
            mm.overlay(H, "Idle", ov("Idle", 2 * math.pi / 4.8))
            if extra_heads:
                def snap(t):
                    pose = {}
                    k = math.sin(math.pi * min(t / 0.9, 1))
                    for j, (nb_, hb_) in enumerate(extra_heads):
                        jb = jaws[j + 1] if j + 1 < len(jaws) else None
                        mm._add(pose, nb_, (0, 0, 0, -0.25 * k, 0, 0))
                        if jb:
                            mm._add(pose, jb, (0, 0, 0, -0.5 * k, 0, 0))
                    return pose
                mm.overlay(H, "Attack", snap)
        if wings:
            H.rig["wings"] = [{"bone": a, "side": sd} for a, hb, sd in wings]
    return H


# ====================================================================================================== head library
def _jaw_bone(H, hb, pos, sfx):
    nm = "Jaw" + sfx
    H.bone(nm, hb, tuple(pos))
    return nm


def head_lion(H, hb, hc, hs, sfx, P, mane=None, fangs=0.0, human=False):
    def h(x, y, z):
        return hc + V(x, y, z) * hs
    M = 0.95
    head = ellipsoid(0.5 * hs, 0.45 * hs, 0.52 * hs, h(0, 0.18, -0.3))
    head = head.su(ellipsoid(0.3 * hs, 0.28 * hs, 0.32 * hs, h(0.3, 0.02, -0.5)).mirror_x(), 0.18)
    head = head.su(round_cone(h(0, 0.28, -0.55), h(0, 0.12, -0.55 - 0.42 * M), 0.2 * hs, 0.16 * hs), 0.15)
    head = head.su(ellipsoid(0.32 * hs, 0.24 * hs, 0.3 * M * hs, h(0, -0.04, -0.62 - 0.22 * M)), 0.15)
    head = head.su(sphere(0.15 * hs, h(0.13, -0.08, -0.78 - 0.24 * M)).mirror_x(), 0.07)
    head = head.su(capsule(h(0.12, 0.36, -0.6), h(0.3, 0.3, -0.62), 0.08 * hs).mirror_x(), 0.08)
    head = head.ss(sphere(0.105 * hs, h(0.24, 0.2, -0.72)).mirror_x(), 0.05)
    ear = ellipsoid(0.17 * hs, 0.2 * hs, 0.07 * hs).ss(ellipsoid(0.12 * hs, 0.15 * hs, 0.05 * hs, (0, -0.02 * hs, -0.045 * hs)), 0.02)
    head = head.su(ear.rot(-15, 0, -22).at(*h(0.34, 0.56, -0.15)).mirror_x(), 0.06)
    H.piece("HeadP" + sfx, hb, head, col="primary", tris=1900, res=130, role="head")
    H.piece("Nose" + sfx, hb, ellipsoid(0.11 * hs, 0.07 * hs, 0.07 * hs, h(0, 0.08, -0.87 - 0.3 * M)), col="nose", tris=200, role="nose", pri=1.6, ao=False)
    jb = _jaw_bone(H, hb, h(0, -0.12, -0.3), sfx)
    jaw = ellipsoid(0.22 * hs, 0.11 * hs, 0.33 * M * hs, h(0, -0.25, -0.62 - 0.12 * M))
    jaw = jaw.su(capsule(h(0.2, -0.2, -0.35), h(0.12, -0.25, -0.65 - 0.1 * M), 0.07 * hs).mirror_x(), 0.08)
    jaw = jaw.su(ellipsoid(0.16 * hs, 0.09 * hs, 0.13 * hs, h(0, -0.3, -0.78 - 0.18 * M)), 0.06)
    H.piece("JawP" + sfx, jb, jaw, col="primary", tris=550, role="jaw", pri=1.4)
    H.prim("Mouth" + sfx, jb, "Ellipsoid", (0.3 * hs, 0.06 * hs, 0.42 * M * hs), h(0, -0.15, -0.62 - 0.12 * M), col="mouth", mat="hard", role="mouth", pri=2.4)
    fl = 0.12 + fangs
    fang = round_cone(h(0.12, -0.12, -0.84 - 0.24 * M), h(0.115, -0.12 - fl, -0.86 - 0.24 * M), 0.035 * hs, 0.008 * hs)
    H.piece("Fangs" + sfx, hb, fang.mirror_x(), col="tooth", mat="hard", tris=200, role="tooth", pri=2.2, ao=False, smooth=2)
    H.eyes(hb, h(0.24, 0.2, -0.735), 0.085 * hs, col="iris", pupil="slit", look=(0.45, 0.05, -1.0))
    if mane:
        mn = ellipsoid(0.78 * hs, 0.8 * hs, 0.62 * hs, h(0, 0.12, 0.05))
        for ring, (rad, zoff, n) in enumerate(((0.62, -0.1, 18), (0.72, 0.2, 14))):
            for i in range(n):
                a = (i + 0.5 * ring) / n * math.tau
                r0 = V(h(0, 0.15, zoff))
                d = V(math.cos(a), math.sin(a) * 1.05, 0.0)
                ln = 0.95 + 0.12 * math.sin(i * 1.7 + ring) - 0.15 * max(0.0, math.sin(a))
                tip = r0 + d * ln * hs + V(0, -0.22 * hs, 0.32 * hs)
                mn = mn.su(round_cone(r0 + d * rad * hs, tip, 0.17 * hs, 0.035 * hs), 0.07)
        mn = mn.su(ellipsoid(0.55 * hs, 0.85 * hs, 0.5 * hs, h(0, -0.65, 0.35)), 0.35)
        mn = mn.su(ellipsoid(0.62 * hs, 0.7 * hs, 0.9 * hs, h(0, 0.4, 0.6)), 0.35)
        mn = mn.ss(ellipsoid(0.5 * hs, 0.5 * hs, 0.9 * hs, h(0, 0.08, -0.72)), 0.15)
        mn = mn.noise(0.045 * hs, 9.0 / hs, 11)
        H.piece("Mane" + sfx, hb, mn, col=mane, tris=2000, res=120, role="mane", pri=1.1)
    return jb, tuple(h(0, -0.15, -1.0))


def head_hound(H, hb, hc, hs, sfx, P, fox=False):
    def h(x, y, z):
        return hc + V(x, y, z) * hs
    M = 1.25 if not fox else 1.35
    head = ellipsoid(0.42 * hs, 0.4 * hs, 0.46 * hs, h(0, 0.15, -0.25))
    head = head.su(ellipsoid(0.27 * hs, 0.25 * hs, 0.3 * hs, h(0.25, 0.0, -0.45)).mirror_x(), 0.15)
    mz = round_cone(h(0, 0.12, -0.55), h(0, 0.03, -0.55 - 0.55 * M), (0.22 if not fox else 0.18) * hs, (0.15 if not fox else 0.09) * hs)
    head = head.su(mz, 0.14)
    head = head.su(capsule(h(0.12, 0.33, -0.55), h(0.26, 0.3, -0.55), 0.07 * hs).mirror_x(), 0.08)
    head = head.ss(sphere(0.09 * hs, h(0.22, 0.2, -0.64)).mirror_x(), 0.04)
    er = 0.3 if not fox else 0.5
    ear = round_cone(V(0, 0, 0), V(0.05, er, 0.03) * hs, (0.13 if not fox else 0.17) * hs, 0.02 * hs)
    ear = squash(ear, V(0, 0, 0), (0, 0, 1), 0.45).ss(squash(round_cone(V(0, 0.03, -0.04) * hs, V(0.04, er * 0.85, -0.02) * hs, 0.09 * hs, 0.015 * hs), V(0, 0, 0), (0, 0, 1), 0.4), 0.02)
    head = head.su(ear.rot(-10, 0, -18).at(*h(0.25, 0.48, -0.15)).mirror_x(), 0.05)
    if fox:   # cheek ruffs
        for sx in (1, -1):
            for i in range(3):
                a = math.radians(-50 + 30 * i)
                q = h(0.32 * sx, -0.05, -0.3)
                head = head.su(round_cone(q, q + V(sx * math.cos(a) * 0.3, math.sin(a) * 0.25, 0.15) * hs, 0.1 * hs, 0.02 * hs), 0.05)
    H.piece("HeadP" + sfx, hb, head, col="primary", tris=1500, res=128, role="head",
            pattern=(lambda Q, c=hc, k=hs: np.where((Q[:, 1] < c[1] + 0.02 * k) & (Q[:, 2] < c[2] - 0.35 * k), 1.0, 1.0)))
    lite = sfx not in ("", "2")
    if not sfx:
        H.piece("Nose" + sfx, hb, ellipsoid(0.08 * hs, 0.06 * hs, 0.06 * hs, h(0, 0.06, -0.62 - 0.55 * M)), col="nose", tris=160, role="nose", pri=1.6, ao=False)
    jb = _jaw_bone(H, hb, h(0, -0.08, -0.3), sfx)
    jaw = round_cone(h(0, -0.15, -0.35), h(0, -0.13, -0.5 - 0.5 * M), 0.17 * hs, 0.08 * hs)
    H.piece("JawP" + sfx, jb, jaw, col="primary", tris=400, role="jaw", pri=1.4)
    if not lite:
        H.prim("Mouth" + sfx, jb, "Ellipsoid", (0.22 * hs, 0.05 * hs, 0.5 * M * hs), h(0, -0.07, -0.35 - 0.3 * M), col="mouth", mat="hard", role="mouth", pri=2.4)
    tt = union_hard([round_cone(h(0.1, 0.0, -0.4 - 0.45 * M), h(0.1, -0.2, -0.41 - 0.45 * M), 0.05 * hs, 0.01 * hs)]).mirror_x()
    H.piece("Fangs" + sfx, hb, tt, col="tooth", mat="hard", tris=160, role="tooth", pri=2.2, ao=False, smooth=2)
    H.eyes(hb, h(0.22, 0.2, -0.66), 0.075 * hs, col="iris", pupil="round" if not fox else "slit", look=(0.45, 0.05, -1.0), shine=not sfx)
    return jb, tuple(h(0, -0.1, -0.6 - 0.55 * M))


def head_eagle(H, hb, hc, hs, sfx, P):
    def h(x, y, z):
        return hc + V(x, y, z) * hs
    head = ellipsoid(0.4 * hs, 0.4 * hs, 0.46 * hs, h(0, 0.12, -0.2))
    head = head.su(ellipsoid(0.3 * hs, 0.26 * hs, 0.3 * hs, h(0, 0.02, -0.45)), 0.15)
    head = head.su(capsule(h(0.12, 0.3, -0.45), h(0.28, 0.28, -0.3), 0.08 * hs).mirror_x(), 0.07)      # stern brow
    head = head.ss(sphere(0.1 * hs, h(0.25, 0.17, -0.45)).mirror_x(), 0.04)
    for sx in (1, -1):    # ear tufts and nape feathers
        q = h(0.22 * sx, 0.4, -0.05)
        head = head.su(flat_tube([q, q + V(0.12 * sx, 0.35, 0.25) * hs, q + V(0.18 * sx, 0.55, 0.55) * hs], [0.11 * hs, 0.07 * hs, 0.015 * hs], (sx, 0, 0), 0.45), 0.05)
    for i in range(5):
        a = -0.6 + 0.3 * i
        q = h(0.25 * math.sin(a), 0.1 + 0.2 * math.cos(a), 0.15)
        head = head.su(flat_tube([q, q + V(0.15 * math.sin(a), 0.0, 0.4) * hs, q + V(0.2 * math.sin(a), -0.15, 0.7) * hs], [0.12 * hs, 0.08 * hs, 0.015 * hs], (0, 1, 0), 0.4), 0.05)
    H.piece("HeadP" + sfx, hb, head, col=P["head_col"], tris=1500, res=128, role="head")
    beak = tube([h(0, 0.08, -0.48), h(0, 0.04, -0.78), h(0, -0.1, -1.0), h(0, -0.32, -0.98)], [0.22 * hs, 0.16 * hs, 0.08 * hs, 0.015 * hs], k=0.05)
    beak = squash(beak, h(0, 0, -0.7), (1, 0, 0), 0.72)
    beak = beak.su(ellipsoid(0.24 * hs, 0.14 * hs, 0.12 * hs, h(0, 0.05, -0.5)), 0.06)   # cere
    beak = beak.ss(sphere(0.03 * hs, h(0.08, 0.1, -0.62)).mirror_x(), 0.01)
    H.piece("Beak" + sfx, hb, beak, col="beak", mat="hard", tris=700, role="beak", pri=1.3)
    jb = _jaw_bone(H, hb, h(0, -0.08, -0.45), sfx)
    lb = squash(tube([h(0, -0.1, -0.5), h(0, -0.13, -0.75), h(0, -0.18, -0.88)], [0.15 * hs, 0.1 * hs, 0.03 * hs]), h(0, 0, -0.7), (1, 0, 0), 0.75)
    H.piece("JawP" + sfx, jb, lb, col="beak", mat="hard", tris=350, role="jaw", pri=1.4)
    H.eyes(hb, h(0.25, 0.17, -0.47), 0.085 * hs, col="iris", pupil="round", look=(0.7, 0.05, -0.8))
    return jb, tuple(h(0, -0.12, -0.95))


def head_human(H, hb, hc, hs, sfx, P):
    """Sphinx: a regal human face framed by a striped nemes headdress (secondary) with a gold uraeus and a braided beard."""
    def h(x, y, z):
        return hc + V(x, y, z) * hs
    face = ellipsoid(0.36 * hs, 0.46 * hs, 0.4 * hs, h(0, 0.15, -0.35))
    face = face.su(ellipsoid(0.2 * hs, 0.14 * hs, 0.18 * hs, h(0, -0.18, -0.55)), 0.12)                 # chin / jaw
    face = face.su(round_cone(h(0, 0.22, -0.72), h(0, 0.05, -0.8), 0.06 * hs, 0.08 * hs), 0.05)          # nose
    face = face.su(capsule(h(0.08, 0.32, -0.7), h(0.22, 0.32, -0.65), 0.05 * hs).mirror_x(), 0.05)        # brows
    face = face.ss(sphere(0.07 * hs, h(0.15, 0.22, -0.72)).mirror_x(), 0.03)
    face = face.su(ellipsoid(0.1 * hs, 0.035 * hs, 0.05 * hs, h(0, -0.07, -0.73)), 0.02)                 # lips
    H.piece("HeadP" + sfx, hb, face, col="primary", tris=1500, res=128, role="head")
    nem = ellipsoid(0.46 * hs, 0.44 * hs, 0.5 * hs, h(0, 0.35, -0.22))
    lap = round_box(0.6 * hs, 0.55 * hs, 0.12 * hs, 0.08 * hs, h(0, -0.25, -0.1))
    lap = lap.ss(ellipsoid(0.38 * hs, 0.8 * hs, 0.6 * hs, h(0, 0.0, -0.45)), 0.05)
    nem = nem.su(lap, 0.12).su(round_cone(h(0, 0.25, 0.1), h(0, -0.2, 0.55), 0.35 * hs, 0.18 * hs), 0.1)
    nem = nem.ss(ellipsoid(0.37 * hs, 0.42 * hs, 0.45 * hs, h(0, 0.1, -0.62)), 0.04)
    H.piece("Nemes" + sfx, hb, nem, col="secondary", mat="cloth", tris=1500, res=128, role="hair", pri=1.2,
            pattern=stripes(lambda Q: Q[:, 1] / hs, 6.0, width=0.4, depth=0.55))
    gold = union_hard([torus(0.43 * hs, 0.04 * hs, axis=1).scale3(1.0, 1.0, 1.1).at(*h(0, 0.42, -0.22)),
                       curved_horn([h(0, 0.55, -0.62), h(0, 0.75, -0.62), h(0, 0.85, -0.52)], 0.05 * hs, 0.03 * hs)])
    gold = gold.su(sphere(0.07 * hs, h(0, 0.86, -0.54)), 0.03)
    H.piece("Uraeus" + sfx, hb, gold, col="gold", mat="metal", tris=600, role="detail", pri=1.5)
    jb = _jaw_bone(H, hb, h(0, -0.1, -0.4), sfx)
    beard = round_box(0.07 * hs, 0.28 * hs, 0.07 * hs, 0.04 * hs, h(0, -0.48, -0.58))
    H.piece("Beard" + sfx, jb, beard, col="secondary", tris=300, role="jaw", pri=1.5, pattern=stripes(lambda Q: Q[:, 1] / hs, 9.0, width=0.3, depth=0.4))
    H.eyes(hb, h(0.15, 0.22, -0.68), 0.055 * hs, col="iris", pupil="round", look=(0.2, 0.0, -1.0))
    return jb, tuple(h(0, -0.1, -0.8))


def head_goat(H, hb, hc, hs, sfx, P):
    def h(x, y, z):
        return hc + V(x, y, z) * hs
    head = ellipsoid(0.3 * hs, 0.32 * hs, 0.38 * hs, h(0, 0.1, -0.2))
    head = head.su(round_cone(h(0, 0.08, -0.4), h(0, -0.12, -0.85), 0.2 * hs, 0.13 * hs), 0.12)
    for sx in (1, -1):
        head = head.su(squash(round_cone(h(0.3 * sx, 0.18, -0.1), h(0.55 * sx, 0.12, 0.0), 0.08 * hs, 0.03 * hs), h(0.4 * sx, 0.15, 0), (0, 1, 0), 0.5), 0.04)
    head = head.su(flat_tube([h(0, -0.25, -0.65), h(0, -0.45, -0.6), h(0, -0.6, -0.5)], [0.08 * hs, 0.06 * hs, 0.015 * hs], (1, 0, 0), 0.5), 0.04)  # beard
    H.piece("HeadP" + sfx, hb, head, col="light", tris=1000, res=120, role="head")
    horn = curved_horn([h(0.12, 0.35, -0.2), h(0.18, 0.62, 0.05), h(0.25, 0.65, 0.45), h(0.32, 0.38, 0.6), h(0.36, 0.22, 0.45)], 0.1 * hs, 0.02 * hs)
    H.piece("Horns" + sfx, hb, horn.mirror_x(), col="horn", mat="hard", tris=700, role="horn", pri=1.3,
            pattern=stripes(lambda Q: np.linalg.norm(Q - hc, axis=1) / hs, 9.0, width=0.3, depth=0.2))
    H.eyes(hb, h(0.22, 0.17, -0.35), 0.06 * hs, col="iris", pupil="slit", look=(0.8, 0.0, -0.6))
    return None, tuple(h(0, -0.15, -0.85))


def head_snake(H, hb, hc, hs, sfx, P):
    def h(x, y, z):
        return hc + V(x, y, z) * hs
    head = ellipsoid(0.32 * hs, 0.2 * hs, 0.45 * hs, h(0, 0.02, -0.35))
    head = head.su(ellipsoid(0.38 * hs, 0.18 * hs, 0.3 * hs, h(0, 0.0, -0.2)), 0.12)
    head = head.ss(sphere(0.07 * hs, h(0.24, 0.1, -0.45)).mirror_x(), 0.03)
    H.piece("HeadP" + sfx, hb, head, col="secondary", tris=700, res=110, role="head")
    jb = _jaw_bone(H, hb, h(0, -0.05, -0.1), sfx)
    H.piece("JawP" + sfx, jb, ellipsoid(0.28 * hs, 0.08 * hs, 0.4 * hs, h(0, -0.13, -0.38)), col="secondary", tris=300, role="jaw", pri=1.4)
    H.piece("Fangs" + sfx, hb, round_cone(h(0.13, -0.06, -0.62), h(0.13, -0.22, -0.64), 0.03 * hs, 0.006 * hs).mirror_x(), col="tooth", mat="hard", tris=120, role="tooth", pri=2.3, ao=False)
    H.mprim("Eye" + sfx + "#", hb, "Ball", (0.11 * hs,) * 3, h(0.24, 0.1, -0.47), col="iris", mat="hard", pri=1.8, role="eye")
    return jb, tuple(h(0, -0.05, -0.75))


def head_qilin(H, hb, hc, hs, sfx, P):
    """Qilin / kirin: a dragon-like head on a deer-horse neck: short snout with whisker barbels, a single swept horn,
    a flowing flame mane (secondary)."""
    def h(x, y, z):
        return hc + V(x, y, z) * hs
    head = ellipsoid(0.36 * hs, 0.36 * hs, 0.45 * hs, h(0, 0.12, -0.25))
    head = head.su(tube([h(0, 0.06, -0.5), h(0, 0.0, -0.85), h(0, -0.04, -1.05)], [0.26 * hs, 0.22 * hs, 0.2 * hs]), 0.12)
    head = head.su(sphere(0.1 * hs, h(0.12, 0.07, -1.05)).mirror_x(), 0.05)
    head = head.ss(sphere(0.05 * hs, h(0.13, 0.08, -1.13)).mirror_x(), 0.02)
    head = head.su(capsule(h(0.15, 0.3, -0.62), h(0.28, 0.32, -0.3), 0.08 * hs).mirror_x(), 0.08)
    head = head.ss(sphere(0.1 * hs, h(0.25, 0.17, -0.58)).mirror_x(), 0.04)
    ear = squash(round_cone(V(0, 0, 0), V(0.25, 0.08, 0.1) * hs, 0.09 * hs, 0.02 * hs), V(0, 0, 0), (0, 1, 0), 0.5)
    head = head.su(ear.at(*h(0.3, 0.25, -0.05)).mirror_x(), 0.04)
    head = head.si(plane((0, -1, 0), -(hc[1] - 0.15 * hs)), 0.03)
    H.piece("HeadP" + sfx, hb, head, col="primary", tris=1500, res=128, role="head")
    jb = _jaw_bone(H, hb, h(0, -0.1, -0.2), sfx)
    jaw = tube([h(0, -0.22, -0.25), h(0, -0.22, -0.7), h(0, -0.2, -0.98)], [0.22 * hs, 0.17 * hs, 0.14 * hs])
    jaw = jaw.si(plane((0, 1, 0), hc[1] - 0.16 * hs), 0.03)
    for k in range(3):
        x = -0.12 + 0.12 * k
        q = h(x, -0.3, -0.5)
        jaw = jaw.su(flat_tube([q, q + V(x * 0.3, -0.25, 0.15) * hs, q + V(x * 0.5, -0.45, 0.4) * hs], [0.06 * hs, 0.05 * hs, 0.012 * hs], (1, 0, 0), 0.5), 0.03)
    H.piece("JawP" + sfx, jb, jaw, col="primary", tris=550, role="jaw", pri=1.4)
    H.prim("Mouth" + sfx, hb, "Ellipsoid", (0.34 * hs, 0.05 * hs, 0.75 * hs), h(0, -0.17, -0.62), col="mouth", mat="hard", role="mouth", pri=2.4)
    horn = curved_horn([h(0, 0.4, -0.45), h(0, 0.7, -0.3), h(0, 0.95, 0.05), h(0, 1.08, 0.45)], 0.1 * hs, 0.015 * hs)
    H.piece("Horn" + sfx, hb, horn, col="horn", mat="hard", tris=500, role="horn", pri=1.3,
            pattern=stripes(lambda Q: Q[:, 1] / hs, 10.0, width=0.25, depth=0.2))
    mane = None
    for k in range(11):
        u = k / 10
        q = h(0, 0.42 - 0.65 * u, -0.1 + 0.55 * u)
        for sx in (1, -1):
            tip = q + V(sx * (0.35 + 0.15 * math.sin(k)), 0.3 - 0.25 * u, 0.55) * hs
            f_ = flat_tube([q, (q + tip) / 2 + V(0, 0.12, 0) * hs, tip], [0.13 * hs, 0.1 * hs, 0.015 * hs], (sx, 0.3, 0), 0.4)
            mane = f_ if mane is None else mane.su(f_, 0.05)
    H.piece("Mane" + sfx, hb, mane, col="secondary", tris=1600, res=130, role="mane", pri=1.2)
    wb = h(0.18, 0.0, -0.95)
    H.mbone("Whisker#", hb, tuple(wb))
    H.mpiece("Whisker#", "Whisker#", tube([wb, wb + V(0.35, -0.05, -0.1) * hs, wb + V(0.7, -0.25, 0.3) * hs, wb + V(0.9, -0.5, 0.9) * hs],
                                          [0.035 * hs, 0.03 * hs, 0.02 * hs, 0.008 * hs]), col="secondary", tris=260, role="detail", pri=1.7)
    H.eyes(hb, h(0.26, 0.17, -0.6), 0.085 * hs, col="iris", pupil="slit", look=(0.6, 0.05, -1.0))
    return jb, tuple(h(0, -0.15, -1.05))


def head_behemoth(H, hb, hc, hs, sfx, P):
    """Behemoth: a massive armoured bull-boar head, huge forward-sweeping horns, lower tusks."""
    def h(x, y, z):
        return hc + V(x, y, z) * hs
    head = ellipsoid(0.62 * hs, 0.58 * hs, 0.6 * hs, h(0, 0.15, -0.3))
    head = head.su(round_box(0.42 * hs, 0.38 * hs, 0.45 * hs, 0.2 * hs, h(0, -0.05, -0.85)), 0.25)
    head = head.su(capsule(h(0.25, 0.42, -0.65), h(0.48, 0.4, -0.35), 0.13 * hs).mirror_x(), 0.1)     # heavy brow
    head = head.ss(sphere(0.12 * hs, h(0.36, 0.22, -0.68)).mirror_x(), 0.05)
    for k in range(4):
        head = head.su(blade_fin(h(0, 0.6 - 0.04 * k, -0.6 + 0.25 * k), (0, 1, 0.5), (0.25 + 0.06 * k) * hs, 0.14 * hs, (1, 0, 0), 0.4, back=(0, 0, 1)), 0.06)
    head = head.ss(sphere(0.07 * hs, h(0.15, 0.0, -1.3)).mirror_x(), 0.03)
    head = head.si(plane((0, -1, 0), -(hc[1] - 0.32 * hs)), 0.04)
    H.piece("HeadP" + sfx, hb, head, col="primary", tris=1800, res=128, role="head", pattern=stripes(lambda Q: Q[:, 2] / hs, 3.0, width=0.1, depth=0.25))
    horn = curved_horn([h(0.5, 0.35, -0.2), h(1.0, 0.45, -0.05), h(1.35, 0.75, -0.35), h(1.35, 1.1, -0.85)], 0.24 * hs, 0.03 * hs)
    horn = horn.su(curved_horn([h(0.15, -0.35, -1.0), h(0.3, -0.35, -1.25), h(0.38, 0.0, -1.45)], 0.09 * hs, 0.015 * hs), 0.02)
    H.piece("Horns" + sfx, hb, horn.mirror_x(), col="horn", mat="hard", tris=1000, role="horn", pri=1.3,
            pattern=stripes(lambda Q: np.linalg.norm(Q - hc, axis=1) / hs, 5.0, width=0.25, depth=0.2))
    jb = _jaw_bone(H, hb, h(0, -0.25, -0.3), sfx)
    jaw = round_box(0.36 * hs, 0.15 * hs, 0.5 * hs, 0.12 * hs, h(0, -0.42, -0.75))
    H.piece("JawP" + sfx, jb, jaw, col="primary", tris=500, role="jaw", pri=1.4)
    H.prim("Mouth" + sfx, hb, "Ellipsoid", (0.62 * hs, 0.06 * hs, 0.9 * hs), h(0, -0.31, -0.8), col="mouth", mat="hard", role="mouth", pri=2.4)
    H.eyes(hb, h(0.36, 0.22, -0.72), 0.075 * hs, col="iris", pupil="round", look=(0.7, 0.0, -0.8))
    return jb, tuple(h(0, -0.3, -1.3))


HEADS = {"lion": lambda H, hb, hc, hs, sfx, P: head_lion(H, hb, hc, hs, sfx, P, mane=(P.get("mane_col", "secondary") if P["mane"] else None), fangs=P.get("fangs", 0.0)),
         "hound": head_hound, "fox": lambda H, hb, hc, hs, sfx, P: head_hound(H, hb, hc, hs, sfx, P, fox=True),
         "eagle": head_eagle, "human": head_human, "qilin": head_qilin, "behemoth": head_behemoth}


# ====================================================================================================== heroes
@hero("griffin", "mythic")
def griffin():
    return _beast("griffin", torso="lion", front="talon", hind="paw", heads=("eagle",), wings="feather", tail="lion", saddle=True, flyer=True,
                  gait="fly", head=1.15, front_col="secondary", head_col="secondary", wing_col="primary",
                  preview={"primary": "#B45309", "secondary": "#F5F5F4", "beak": "#F2B33B", "iris": "#E8A21E", "leather": "#6B4423"})


@hero("hippogriff", "mythic")
def hippogriff():
    return _beast("hippogriff", torso="horse", front="talon", hind="hoof", heads=("eagle",), wings="feather", tail="horse", saddle=False, flyer=True,
                  gait="fly", head=1.1, front_col="secondary", head_col="secondary", wing_col="primary",
                  preview={"primary": "#A8A29E", "secondary": "#F8FAFC", "beak": "#E8B23B", "iris": "#E8821E", "hoof": "#3B2F2A"})


@hero("manticore", "mythic")
def manticore():
    return _beast("manticore", torso="lion", heads=("lion",), mane=True, wings="bat", tail="scorpion", fangs=0.1, girth=1.05,
                  preview={"primary": "#991B1B", "secondary": "#F59E0B", "membrane": "#B85A3A", "nose": "#3A1A18", "iris": "#F5C23A"})


@hero("chimera", "mythic")
def chimera():
    return _beast("chimera", torso="lion", heads=("lion",), mane=True, mane_col="dark", goat=True, tail="snake", girth=1.05,
                  preview={"primary": "#B45309", "secondary": "#65A30D", "horn": "#D9C9A8", "nose": "#3A2A28", "iris": "#F2C230"})


@hero("sphinx", "mythic")
def sphinx():
    return _beast("sphinx", torso="lion", heads=("human",), wings="folded", tail="lion", head=1.25, wing_col="secondary", mane_col="dark",
                  preview={"primary": "#D6A35A", "secondary": "#1E3A8A", "iris": "#2A1A10", "gold": "#E8B53A"})


@hero("kitsune", "mythic")
def kitsune():
    return _beast("kitsune", torso="fox", heads=("fox",), tail="fox9", leg=0.9, body=0.95, head=1.25, attack="pounce",
                  preview={"primary": "#F59E0B", "secondary": "#FFFFFF", "nose": "#2A1A18", "iris": "#F2C230"})


@hero("qilin", "mythic")
def qilin():
    return _beast("qilin", torso="horse", front="hoof", hind="hoof", heads=("qilin",), tail="flame", pattern="scales", head=1.3,
                  attack="gore", preview={"primary": "#0F766E", "secondary": "#FCD34D", "horn": "#F4E2B0", "hoof": "#3B2F2A", "iris": "#FCD34D"})


@hero("behemoth", "mythic")
def behemoth():
    return _beast("behemoth", torso="colossus", front="pillar", hind="pillar", heads=("behemoth",), tail="stub", pattern="plates", head=1.15,
                  gait="stomp", attack="gore", preview={"primary": "#57534E", "secondary": "#92400E", "horn": "#E6DCC8", "iris": "#F59E0B"})
