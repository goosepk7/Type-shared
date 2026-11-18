"""Bats: bat (generic / long-eared), fruit bat (fox face, huge wings), vampire bat (pug nose leaf, fangs).

`_bat`: a furry torso with a fluffy chest, a head with big membranous ears (inner ear panel), snout and a jaw with
fangs, and two membrane wings on a three-bone arm chain: the humerus, a long forearm and the hand whose four long
finger bones fan out from the wrist (plus a hooked thumb claw). The wing membrane is split into three panels
(body-to-elbow, forearm-to-fifth-finger, between the fingers) with a scalloped trailing edge, each on the bone it
moves with, offset slightly so the panels never lie coplanar. Short hind legs with clawed feet trail behind,
joined by a tail membrane. Flies with motion_birds.fly (deep flaps, swoop-and-bite attack).
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from kit import Hero, hero, spots, gradient, combine
from h_birds import U, A, oell, unite, lerp, slab, BIRD
import motion_birds as MB

BASE = dict(body=1.0, girth=1.0, head=1.0, snout=0.5, ear=1.0, ear_w=1.0, noseleaf=False, fangs=0.12, span=1.0, wing_back=1.0,
            fluffy=0.02, eye=0.11, tail=0.5, period=0.55, amp=0.95, cols={}, preview={}, tags=("bat", "mammal"))


def _bat(hid, **kw):
    P = dict(BASE)
    P.update(kw)
    col = dict(body="primary", chest="secondary", head="primary", ear="primary", inner="inner", membrane="membrane", bone="dark", snout="dark")
    col.update(P["cols"])
    H = Hero(hid, plan="Bird", gait="fly", tags=list(P["tags"]))
    H.preview = P["preview"]
    G, HS, sp = P["girth"], P["head"], P["span"]
    BY = 0.75
    H.body((0, BY, 0))
    fz = P["fluffy"]
    furp = spots(0.06, 0.03, depth=0.12, seed=3)

    torso = ellipsoid(0.3 * G, 0.28 * G, 0.55 * P["body"], (0, BY, 0.05)).su(ellipsoid(0.26 * G, 0.24 * G, 0.3, (0, BY + 0.02, -0.3)), 0.15)
    torso = torso.su(ellipsoid(0.12, 0.12, 0.25, (0.2 * G, BY + 0.08, -0.25)).mirror_x(), 0.1)      # pectorals / wing roots
    H.piece("Torso", "Body", torso.noise(fz, 18, 1), col=col["body"], mat="fur", tris=1200, res=104, pattern=furp)
    chest = ellipsoid(0.26 * G, 0.22 * G, 0.4, (0, BY - 0.08, -0.18)).noise(fz * 1.5, 16, 2)
    H.piece("Chest", "Body", chest, col=col["chest"], mat="fur", tris=600, res=96, pri=1.2, pattern=furp)

    # ------------------------------------------------------------------ head
    hr = 0.24 * HS
    hc = A(0, BY + 0.12, -0.55)
    H.bone("Neck", "Body", (0, BY + 0.05, -0.35))
    H.bone("Head", "Neck", tuple(hc + A(0, -0.05, 0.12)))

    def h(x, y, z):
        return tuple(hc + A(x * hr, y * hr, z * hr))

    sn = P["snout"]
    head = ellipsoid(0.95 * hr, 0.85 * hr, 0.9 * hr, h(0, 0, 0))
    head = head.su(round_cone(h(0, -0.1, -0.4), h(0, -0.18, -0.6 - 1.2 * sn), 0.55 * hr, (0.3 + 0.1 * (1 - sn)) * hr), 0.25 * hr)   # snout
    head = head.su(round_cone(h(0, -0.1, 0.6), h(0, -0.3, -0.2), 0.75 * hr, 0.6 * hr), 0.2 * hr)                                  # neck ruff
    epos = hc + A(0.45, 0.22, -0.62 - 0.25 * sn) * hr
    head = head.ss(sphere(P["eye"] * HS * 1.1, tuple(epos)).mirror_x(), 0.03)
    # ears: tall cupped cones flaring out
    E, EW = P["ear"], P["ear_w"]
    eb = A(0.45 * hr, 0.55 * hr, -0.05 * hr)
    etip = eb + A(0.35 * hr * E, 1.35 * hr * E, 0.25 * hr * E)

    def ear_shape(r_scale=1.0, inset=0.0):
        d = U(etip - eb)
        c = hc + (eb + etip) / 2 + A(0, 0, -inset)
        return oell(c, d, A(1, -0.25, 0), np.linalg.norm(etip - eb) * 0.55 * r_scale, 0.42 * hr * EW * r_scale, 0.14 * hr)

    ear_o = ear_shape().ss(ear_shape(0.82, 0.07 * hr), 0.02 * hr)
    head = head.su(ear_o.mirror_x(), 0.06 * hr)
    H.piece("HeadP", "Head", head.noise(fz * 0.6, 20, 4), col=col["head"], mat="fur", tris=1400, res=112, role="head", pri=1.3, pattern=furp)
    inner = ear_shape(0.8, 0.045 * hr) & ear_shape(1.2, -0.04 * hr).round(0.0)
    H.piece("EarInner", "Head", inner.mirror_x(), col=col["inner"], tris=500, res=104, role="ear", pri=1.4)
    nose = ellipsoid(0.32 * hr, 0.22 * hr, 0.18 * hr, h(0, -0.06, -0.72 - 1.2 * sn))
    if P["noseleaf"]:
        nose = nose.su(oell(h(0, 0.25, -0.75 - 1.2 * sn), (0, 1, 0.2), (1, 0, 0), 0.4 * hr, 0.22 * hr, 0.05 * hr), 0.05 * hr)
    H.piece("Nose", "Head", nose, col=col["snout"], tris=300, res=72, role="nose", pri=1.6)
    H.eyes("Head", tuple(epos), P["eye"] * HS, col="pupil", pupil=None, look=(0.6, 0.15, -0.8))
    jw = hc + A(0, -0.35 * hr, -0.2 * hr)
    H.bone("Jaw", "Head", tuple(jw))
    jaw = round_cone(h(0, -0.45, -0.2), h(0, -0.42, -0.5 - 1.1 * sn), 0.38 * hr, 0.18 * hr)
    H.piece("JawP", "Jaw", jaw.noise(fz * 0.4, 20, 5), col=col["head"], mat="fur", tris=400, res=88, role="jaw", pri=1.4)
    H.prim("Mouth", "Jaw", "Ellipsoid", (0.4 * hr, 0.08 * hr, 0.7 * hr * (0.6 + sn)), h(0, -0.3, -0.45 - 0.6 * sn), col="mouth", mat="hard", role="mouth", pri=2.4)
    fl = P["fangs"]
    fang = round_cone(h(0.16, -0.26, -0.62 - 1.15 * sn), h(0.15, -0.26 - fl / hr, -0.64 - 1.15 * sn), 0.06 * hr, 0.012 * hr)
    H.mpiece("Fang#", "Head", fang, col="tooth", mat="hard", tris=150, res=56, role="tooth", pri=2.2, ao=False)

    # ------------------------------------------------------------------ wings
    Sh = A(0.2 * G, BY + 0.1, -0.22)
    El = Sh + A(0.7 * sp, 0.06, 0.28)
    Wr = El + A(1.05 * sp, 0.04, -0.38)
    wb = P["wing_back"]
    f2 = Wr + A(0.95 * sp, 0.0, -0.08)
    f3 = Wr + A(1.75 * sp, -0.02, 0.22 * wb)
    f4 = Wr + A(1.25 * sp, -0.03, 0.95 * wb)
    f5 = Wr + A(0.5 * sp, -0.03, 1.2 * wb)
    hipb = A(0.16 * G, BY - 0.08, 0.38)
    foot = A(0.32 * G, BY - 0.42, 0.72)
    H.mbone("Shoulder#", "Body", tuple(Sh))
    H.mbone("Elbow#", "Shoulder#", tuple(El))
    H.mbone("Wrist#", "Elbow#", tuple(Wr))
    rb = 0.045
    arm = round_cone(tuple(Sh), tuple(El), rb * 2.0, rb * 1.4).su(round_cone(tuple(Sh + A(-0.1, 0, 0)), tuple(El), 0.14, 0.05), 0.05)
    arm = arm.noise(fz * 0.5, 18, 6)
    H.mpiece("Humerus#", "Shoulder#", arm, col=col["body"], mat="fur", tris=400, res=88, role="limb", pri=1.2)
    fa = round_cone(tuple(El), tuple(Wr), rb * 1.4, rb * 1.1).su(sphere(rb * 1.6, tuple(Wr)), 0.03)
    H.mpiece("Forearm#", "Elbow#", fa, col=col["bone"], tris=350, res=96, role="limb", pri=1.3)
    fingers = [sphere(rb * 1.5, tuple(Wr))]
    for tip in (f2, f3, f4, f5):
        mid = lerp(Wr, tip, 0.48) + A(0, 0.02, 0)
        fingers.append(round_cone(tuple(Wr), tuple(mid), rb * 0.95, rb * 0.75) | round_cone(tuple(mid), tuple(tip), rb * 0.75, rb * 0.35))
        fingers.append(sphere(rb * 0.85, tuple(mid)))
    th0 = Wr + A(0.05, 0.03, -0.04)
    fingers.append(tube([tuple(Wr), tuple(th0 + A(0.05, 0.02, -0.15)), tuple(th0 + A(0.08, -0.06, -0.24))], [rb * 0.9, rb * 0.6, rb * 0.15], k=0.01))   # thumb claw
    H.mpiece("Fingers#", "Wrist#", unite(fingers), col=col["bone"], tris=700, res=128, role="limb", pri=1.3)
    # membranes (scalloped trailing edge between finger tips)
    T = 0.022

    def scal(a, b, k=0.16):
        m = (a + b) / 2
        inward = U(np.cross(b - a, A(0, 1, 0)))
        if inward[2] > 0:
            inward = -inward
        return m + inward * k * np.linalg.norm(b - a) * (-1)

    elb_back = El + A(-0.05, -0.03, 0.75 * wb)
    m1 = slab([Sh + A(-0.12, 0.0, -0.05), El + A(0.03, 0, -0.02), elb_back + A(0.08, 0, 0.05), hipb + A(0.12, 0.0, 0.25), hipb + A(-0.06, 0, -0.05)], T)
    m2 = slab([El + A(-0.05, 0.02, 0), Wr + A(0.02, 0.02, -0.03), f5 + A(0, 0.02, 0), scal(elb_back, f5, -0.12) + A(0, 0.02, 0), elb_back + A(-0.08, 0.02, 0.04)], T)
    m3 = slab([Wr + A(-0.06, 0.035, 0.0), f2 + A(0, 0.035, 0), f3 + A(0, 0.035, 0), scal(f3, f4) + A(0, 0.035, 0), f4 + A(0, 0.035, 0),
               scal(f4, f5) + A(0, 0.035, 0), f5 + A(-0.05, 0.035, 0)], T)
    mpat = gradient(0, 0.2, 4.0, 1.0, 0.85)
    H.mpiece("MemInner#", "Shoulder#", m1, col=col["membrane"], tris=400, res=112, role="wing", pri=1.0, pattern=mpat)
    H.mpiece("MemArm#", "Elbow#", m2, col=col["membrane"], tris=500, res=128, role="wing", pri=1.0, pattern=mpat)
    H.mpiece("MemHand#", "Wrist#", m3, col=col["membrane"], tris=700, res=144, role="wing", pri=1.0, pattern=mpat)

    # ------------------------------------------------------------------ legs + tail membrane
    H.mbone("Hip#", "Body", tuple(hipb))
    H.mbone("Foot#", "Hip#", tuple(foot))
    leg = round_cone(tuple(hipb), tuple(foot), 0.07, 0.035).su(ellipsoid(0.08, 0.1, 0.14, tuple(lerp(hipb, foot, 0.3))), 0.05)
    H.mpiece("Leg#", "Hip#", leg.noise(fz * 0.4, 18, 7), col=col["body"], mat="fur", tris=300, res=80, role="limb", pri=1.3)
    claws = [sphere(0.045, tuple(foot))]
    for dx in (-0.04, 0.0, 0.04):
        p0 = foot + A(dx, 0, 0.0)
        claws.append(tube([tuple(p0), tuple(p0 + A(dx * 0.5, -0.03, 0.1)), tuple(p0 + A(dx * 0.6, -0.1, 0.12))], [0.02, 0.016, 0.005], k=0.005))
    H.mpiece("FootClaws#", "Foot#", unite(claws, 0.01), col="claw", mat="hard", tris=250, res=64, role="claw", pri=1.8)
    H.bone("Tail", "Body", (0, BY - 0.02, 0.5))
    tl = P["tail"]
    if tl > 0:
        tm = slab([(0.3 * G, BY - 0.38, 0.68), (0, BY - 0.15, 0.55 + 0.6 * tl), (-0.3 * G, BY - 0.38, 0.68), (-0.12, BY - 0.05, 0.4), (0.12, BY - 0.05, 0.4)], T * 1.2)
        tm = tm.su(round_cone((0, BY - 0.02, 0.45), (0, BY - 0.15, 0.55 + 0.6 * tl), 0.04, 0.015), 0.02)
        H.piece("TailMem", "Tail", tm, col=col["membrane"], tris=400, res=104, role="tail", pri=1.1)

    H.socket("mouth", h(0, -0.3, -0.85 - 1.2 * sn), "Jaw")
    H.socket("head", h(0, 1.2, 0), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": ["Tail"], "neck": "Neck"})
    wings = [("ShoulderR", "ElbowR", "WristR", 1), ("ShoulderL", "ElbowL", "WristL", -1)]
    MB.fly(H, wings, neck="Neck", head="Head", jaw="Jaw", tail="Tail", legs=(), height=1.6, period=P["period"], amp=P["amp"], lift=0.55,
           attack="dive", fold=0.3, idle_amp=0.7, pitch=-0.05, lag=0.3)
    return H


@hero("bat", "birds")
def bat():
    return _bat("bat", snout=0.35, ear=1.15, cols=dict(chest="light"),
                preview={"primary": "#3A2E2A", "secondary": "#8A6A5A", "light": "#5A4A42", "membrane": "#4A3A36", "dark": "#2A201E", "inner": "#B08080"})


@hero("fruit bat", "birds")
def fruit_bat():
    return _bat("fruit bat", snout=0.85, ear=0.6, ear_w=0.8, head=1.1, span=1.2, eye=0.13, fangs=0.06, tail=0.15, period=0.75, amp=0.85,
                cols=dict(chest="secondary", head="secondary"), fluffy=0.025,
                preview={"primary": "#6A3A20", "secondary": "#E8A04A", "membrane": "#4A2E22", "dark": "#2E1E16", "inner": "#7A4A3A"})


@hero("vampire bat", "birds")
def vampire_bat():
    return _bat("vampire bat", snout=0.15, ear=0.95, noseleaf=True, fangs=0.16, span=0.9, eye=0.11, tail=0.0,
                cols=dict(chest="dark", membrane=[0.3, 0.18, 0.18]), fluffy=0.015,
                preview={"primary": "#3A2A28", "secondary": "#B81E2A", "dark": "#24181A", "inner": "#C07070"})
