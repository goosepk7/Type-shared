"""Bugs (orthopterans and long-bodied insects): grasshopper, cricket, flea (hop gait: crouch, kick the big hind legs
straight, arc, land); praying mantis (raised raptorial arms that strike), stick insect, water strider."""
import math

import numpy as np

import sdf as S
from sdf import sphere, ellipsoid, capsule, round_cone, tube, torus  # noqa: F401
from kit import Hero, hero, stripes, spots, gradient, combine  # noqa: F401
import motion_bugs as MB
from bugkit import *  # noqa: F401,F403
from h_bugs_fly import flat_wing


def _jump_leg(H, hip, knee, ankle, tip, femr, col, pat=None):
    """Hind jumping leg: a massive drumstick femur with a herringbone pattern, a thin spiny tibia folded under it."""
    hip, knee, ankle, tip = A(hip), A(knee), A(ankle), A(tip)
    d = knee - hip
    fm = round_cone(T(hip), T(knee), femr * 0.8, femr * 0.35)
    fm = fm.su(ellipsoid(femr * 0.85, femr * 1.25, np.linalg.norm(d) * 0.36).rot(-math.degrees(math.atan2(d[1], d[2])), 0, 0).at(*T(hip + d * 0.38)), femr * 0.4)
    L = np.linalg.norm(d)
    u = d / L

    def herring(P, hip=hip, u=u):
        q = P - hip
        t = q @ u
        side = q[:, 1] * u[2] - q[:, 2] * u[1]
        v = np.mod(t / 0.12 + np.abs(side) / 0.12, 1.0)
        return 1 - 0.35 * np.clip(1 - np.abs(v - 0.5) / 0.12, 0, 1) * (np.abs(P[:, 0]) > hip[0] + 0.05)

    tb = round_cone(T(knee), T(ankle), femr * 0.32, femr * 0.24)
    tb = tb.su(sphere(femr * 0.36, T(knee)), femr * 0.1)
    for i in range(6):
        c = knee + (ankle - knee) * (0.2 + 0.13 * i)
        tb = tb.su(round_cone(T(c), T(c + A(0.02, -0.04, 0.07)), 0.025, 0.006), 0.012)
    return fm, tb, herring


def _hopper(hid, kind="grasshopper", preview=None):
    cricket, flea = kind == "cricket", kind == "flea"
    H = Hero(hid, plan="Insect", gait="hop", tags=["insect", "bug", "hopper"])
    H.preview = preview or {}
    y = 0.85 if not flea else 0.9
    H.body((0, y, -0.2))
    # ---------------------------------------------------------------- thorax (+ saddle pronotum)
    if flea:
        th = ellipsoid(0.32, 0.5, 0.4, (0, y + 0.05, -0.3))
        for i in range(3):
            th = th.su(ellipsoid(0.33, 0.52, 0.12, (0, y + 0.06, -0.5 + 0.17 * i)), 0.03)
    else:
        th = ellipsoid(0.28, 0.3, 0.45, (0, y, -0.25))
        pn = ellipsoid(0.34 if not cricket else 0.36, 0.34, 0.36, (0, y + 0.06, -0.38))
        pn = pn & S.SDF(lambda p: (y - 0.12) - p[:, 1])
        th = th.su(pn, 0.04)
        th = th.ss(capsule((0, y + 0.42, -0.3), (0, y + 0.42, -0.5), 0.02).mirror_x(), 0.01)
    H.piece("Torso", "Body", th, col="primary", mat="hard", tris=1100, res=124,
            pattern=gradient(1, y - 0.3, y + 0.4, 1.0, 0.82) if not flea else None)
    # ---------------------------------------------------------------- head (vertical face)
    hb = (0, y + 0.05, -0.62)
    H.bone("Head", "Body", hb)
    if flea:
        hc = A(0, y + 0.0, -0.78)
        hd = ellipsoid(0.24, 0.3, 0.25, T(hc)).su(round_cone(T(hc + A(0, -0.15, -0.1)), T(hc + A(0, -0.45, -0.05)), 0.05, 0.02), 0.03)
    elif cricket:
        hc = A(0, y + 0.0, -0.82)
        hd = ellipsoid(0.32, 0.33, 0.28, T(hc)).su(round_cone(T(hc + A(0, 0, 0.1)), (0, y + 0.0, -0.55), 0.2, 0.22), 0.06)
    else:
        hc = A(0, y + 0.02, -0.82)
        hd = ellipsoid(0.24, 0.36, 0.26).rot(-18, 0, 0).at(*T(hc + A(0, -0.04, 0)))
        hd = hd.su(round_cone(T(hc + A(0, 0.05, 0.1)), (0, y + 0.0, -0.55), 0.18, 0.22), 0.06)
        hd = hd.su(ellipsoid(0.16, 0.12, 0.12, T(hc + A(0, -0.34, -0.1))), 0.05)           # labrum
    H.piece("HeadP", "Head", hd, col="primary", mat="hard", tris=900, role="head", pri=1.1)
    if flea:
        H.mprim("Eye#", "Head", "Ball", (0.08,) * 3, T(hc + A(0.2, 0.08, -0.12)), col="black", mat="hard", pri=1.3, role="eye")
    else:
        bug_eyes(H, "Head", T(hc + A(0.2, 0.14, -0.08)), 0.1, flat=0.7)
    mb = A(0.1, hc[1] - 0.32, hc[2] - 0.15)
    H.mbone("Mand#", "Head", T(mb))
    H.mpiece("Mandible#", "Mand#", tube([T(mb), T(mb + A(0.04, -0.06, -0.06)), T(mb + A(-0.06, -0.1, -0.06))], [0.05, 0.04, 0.018]),
             col="dark", mat="hard", tris=180, role="jaw", pri=1.5)
    base = hc + A(0.09, 0.22, -0.2)
    if cricket:
        pts = [base, base + A(0.2, 0.25, -0.4), base + A(0.7, 0.35, -1.5), base + A(1.4, 0.1, -2.8)]
        antenna(H, "", T(base), pts, 0.035, 0.012, col="dark", kind="thread", tris=320)
    elif flea:
        pts = [base, base + A(0.08, 0.05, -0.05), base + A(0.15, 0.0, -0.08)]
        antenna(H, "", T(base), pts, 0.03, 0.035, col="dark", kind="thread", club=0.04)
    else:
        pts = [base, base + A(0.12, 0.2, -0.3), base + A(0.3, 0.35, -0.7), base + A(0.45, 0.4, -1.05)]
        antenna(H, "", T(base), pts, 0.035, 0.022, col="dark", kind="thread")
    # ---------------------------------------------------------------- abdomen (+ cerci / ovipositor)
    H.bone("Abdomen", "Body", (0, y, 0.15))
    if flea:
        ab = ellipsoid(0.36, 0.6, 0.72, (0, y + 0.05, 0.45))
        for i in range(5):  # overlapping tergite plates
            ab = ab.su(ellipsoid(0.37 - 0.01 * i, 0.6 - 0.04 * i, 0.12, (0, y + 0.06, 0.0 + 0.2 * i)), 0.03)
        ab = surface_cut(ab, zgrooves(0.1, 0.2, 0.012), 0.03, 0.01)
        for i in range(6):  # short backward bristles lying along the back
            ab = ab.su(round_cone((0.0, y + 0.6 - 0.05 * i, -0.05 + 0.2 * i), (0.0, y + 0.62 - 0.05 * i, 0.08 + 0.2 * i), 0.025, 0.008), 0.02)
    else:
        ab = round_cone((0, y - 0.02, 0.1), (0, y - 0.12 if not cricket else y - 0.05, 1.45 if not cricket else 1.1), 0.27 if not cricket else 0.33, 0.14 if not cricket else 0.2)
        ab = surface_cut(ab, zgrooves(0.1, 0.17, 0.01, y - 0.1), 0.03, 0.01)
        if cricket:
            for sx in (1, -1):
                ab = ab.su(round_cone((0.08 * sx, y - 0.02, 1.2), (0.3 * sx, y + 0.05, 1.85), 0.04, 0.012), 0.03)   # cerci
            ab = ab.su(round_cone((0, y - 0.05, 1.2), (0, y + 0.05, 2.0), 0.035, 0.015), 0.03)                       # ovipositor
    H.piece("Gaster", "Abdomen", ab, col="primary" if not cricket else "dark", mat="hard", tris=1000, res=124,
            pattern=stripes(lambda Q: Q[:, 2], 1 / 0.17, width=0.15, depth=0.3))
    # ---------------------------------------------------------------- wings (tegmina folded along the back)
    wings = []
    if not flea:
        if cricket:
            tw = [(0, -0.12), (0.3, -0.18), (1.05, -0.12), (1.15, 0.0), (1.0, 0.16), (0.2, 0.14)]
            w = flat_wing(H, "Wing", (0.08, y + 0.3, -0.05), tw, yaw=-90, lift=-2, roll=-12, col="secondary", mat="hard", rnd=0.05, tris=400,
                          pat2d=lambda x, z, d: 1 - 0.4 * np.clip(1 - np.abs(np.mod(x * 6, 1) - 0.5) / 0.1, 0, 1))
        else:
            tw = [(0, -0.08), (0.4, -0.12), (1.55, -0.1), (1.7, 0.0), (1.5, 0.12), (0.3, 0.1)]
            w = flat_wing(H, "Wing", (0.1, y + 0.22, -0.08), tw, yaw=-92, lift=-4, roll=-55, col="primary", mat="hard", rnd=0.04, tris=400,
                          pat2d=lambda x, z, d: 1 - 0.45 * np.clip((np.sin(x * 14) * np.sin(z * 30) - 0.6) * 4, 0, 1))
        wings = [(w[0], 1), (w[1], -1)]
    # ---------------------------------------------------------------- legs
    r = (0.06, 0.05, 0.04, 0.03)
    hy = y - 0.2
    F = legspec((0.15, hy, -0.4), 50, 0.35, y + 0.05, 0.7, 0.3, 0.95, 0.03)
    M = legspec((0.18, hy, -0.12), -5, 0.4, y + 0.05, 0.85, 0.3, 1.1, 0.03)
    names = [leg(H, "F", *F, r=r, col="primary", spines=1), leg(H, "M", *M, r=r, col="primary", spines=1)]
    # hind jumping legs
    if flea:
        hip, knee, ankle, tip = A(0.3, y - 0.3, 0.15), A(0.42, y + 0.25, 0.75), A(0.45, 0.3, 0.15), A(0.48, 0.03, 0.55)
        femr = 0.16
    elif cricket:
        hip, knee, ankle, tip = A(0.24, hy, 0.15), A(0.45, y + 0.55, 1.1), A(0.5, 0.18, 0.55), A(0.52, 0.03, 0.95)
        femr = 0.22
    else:
        hip, knee, ankle, tip = A(0.22, hy, 0.12), A(0.42, y + 0.65, 1.15), A(0.47, 0.15, 0.4), A(0.5, 0.03, 0.82)
        femr = 0.2
    fm, tb, herring = _jump_leg(H, hip, knee, ankle, tip, femr, "primary")
    names_j = leg(H, "B", hip, knee, ankle, tip, r=(femr * 0.5, femr * 0.32, 0.04, 0.03), col="primary", femur=fm, tibia=tb, pat=herring if not flea else None,
                  tris=(700, 350, 220))
    legs = legs_rig(names, [0.0, 0.5])
    jump = [("LegBR", "KneeBR", "FootBR", 1), ("LegBL", "KneeBL", "FootBL", -1)]
    MB.hopper(H, legs, jump, head="Head", abd="Abdomen", ants=[("AntR", 1), ("AntL", -1)], mand=[("MandR", 1), ("MandL", -1)], wings=wings,
              height=1.3, period=0.9 if not flea else 0.7, hop_h=0.9 if not flea else 1.4)
    rl = legs + [{"hip": "LegBR", "knee": "KneeBR", "phase": 0.0, "side": 1}, {"hip": "LegBL", "knee": "KneeBL", "phase": 0.0, "side": -1}]
    finish(H, mouth=T(hc + A(0, -0.4, -0.15)), top=T(hc + A(0, 0.35, 0)), legs=rl)
    return H


@hero("grasshopper", "bugs")
def grasshopper():
    return _hopper("grasshopper", "grasshopper", preview={"primary": "#6AA03A", "secondary": "#C8D84A", "dark": "#2A4A1A", "bugEye": "#3A2A14"})


@hero("cricket", "bugs")
def cricket():
    return _hopper("cricket", "cricket", preview={"primary": "#4A3A2A", "secondary": "#8A6A44", "dark": "#2A1E14", "bugEye": "#140E0A"})


@hero("flea", "bugs")
def flea():
    return _hopper("flea", "flea", preview={"primary": "#6A4A2A", "secondary": "#3A2A1A", "dark": "#2A1A0E"})


# ================================================================================================ mantis, stick insect, water strider
def _mantis(hid, kind="mantis", preview=None):
    stick, strider = kind == "stick", kind == "strider"
    H = Hero(hid, plan="Insect", gait="scuttle", tags=["insect", "bug"])
    H.preview = preview or {}
    y = {"mantis": 1.0, "stick": 0.9, "strider": 0.55}[kind]
    H.body((0, y, 0))
    tw = (lambda P: 1 - 0.0 * P[:, 0])
    # ---------------------------------------------------------------- thorax
    if kind == "mantis":
        th = tube([(0, y, 0.25), (0, y + 0.05, -0.1), (0, y + 0.35, -0.45), (0, y + 0.75, -0.8)], [0.17, 0.16, 0.11, 0.1], k=0.05)
        th = th.su(ellipsoid(0.16, 0.06, 0.2, (0, y + 0.75, -0.75)).rot(0, 0, 0), 0.04)
        hc = A(0, y + 0.88, -0.98)
        neck = (0, y + 0.78, -0.85)
    elif stick:
        th = tube([(0, y, 0.4), (0, y + 0.02, -0.3), (0, y + 0.04, -1.2)], [0.11, 0.1, 0.08], k=0.05).noise(0.012, 18, 2)
        for z in (-1.0, -0.3, 0.3):
            th = th.su(sphere(0.12, (0, y + 0.0, z)), 0.06)
        hc = A(0, y + 0.06, -1.42)
        neck = (0, y + 0.05, -1.25)
    else:
        th = ellipsoid(0.17, 0.12, 0.45, (0, y, -0.1)).su(ellipsoid(0.2, 0.13, 0.18, (0, y, 0.2)), 0.08)
        hc = A(0, y + 0.03, -0.66)
        neck = (0, y + 0.02, -0.5)
    H.piece("Torso", "Body", th, col="primary", mat="hard" if not stick else "wood", tris=900, res=124)
    # ---------------------------------------------------------------- head
    H.bone("Head", "Body", neck)
    if kind == "mantis":
        hd = ellipsoid(0.28, 0.16, 0.12, T(hc)).su(round_cone(T(hc + A(0, -0.05, -0.02)), T(hc + A(0, -0.3, -0.04)), 0.12, 0.05), 0.08)
        hd = hd.su(round_cone(T(hc + A(0, 0, 0.05)), neck, 0.06, 0.06), 0.03)
        H.piece("HeadP", "Head", hd, col="primary", mat="hard", tris=800, role="head", pri=1.1)
        H.mprim("Eye#", "Head", "Ellipsoid", (0.2, 0.24, 0.2), T(hc + A(0.25, 0.04, 0.0)), col="bugEye", mat="hard", pri=1.25, role="eye")
        H.mprim("Pupil#", "Head", "Ball", (0.05,) * 3, T(hc + A(0.29, 0.03, -0.09)), col="black", mat="hard", pri=2.0, role="pupil")
        H.mprim("Shine#", "Head", "Ball", (0.04,) * 3, T(hc + A(0.3, 0.12, -0.06)), col="shine", mat="hard", pri=2.4, role="shine")
        base = hc + A(0.07, 0.1, -0.1)
        antenna(H, "", T(base), [base, base + A(0.2, 0.4, -0.3), base + A(0.5, 0.7, -0.75), base + A(0.75, 0.75, -1.2)], 0.022, 0.01, col="primary")
        mouth = hc + A(0, -0.3, -0.06)
    elif stick:
        hd = ellipsoid(0.12, 0.11, 0.2, T(hc)).su(round_cone(T(hc + A(0, 0, 0.1)), neck, 0.08, 0.08), 0.03)
        H.piece("HeadP", "Head", hd, col="primary", mat="wood", tris=500, role="head", pri=1.1)
        bug_eyes(H, "Head", T(hc + A(0.1, 0.04, -0.06)), 0.055, flat=0.8)
        base = hc + A(0.05, 0.05, -0.18)
        antenna(H, "", T(base), [base, base + A(0.1, 0.05, -0.5), base + A(0.2, 0.08, -1.2), base + A(0.28, 0.05, -1.8)], 0.025, 0.012, col="primary", mat="wood")
        mouth = hc + A(0, -0.08, -0.2)
    else:
        hd = ellipsoid(0.14, 0.11, 0.18, T(hc)).su(round_cone(T(hc + A(0, -0.04, -0.12)), T(hc + A(0, -0.15, -0.2)), 0.04, 0.02), 0.03)
        hd = hd.su(round_cone(T(hc + A(0, 0, 0.1)), neck, 0.08, 0.1), 0.03)
        H.piece("HeadP", "Head", hd, col="primary", mat="hard", tris=500, role="head", pri=1.1)
        bug_eyes(H, "Head", T(hc + A(0.12, 0.05, -0.02)), 0.07, flat=0.8)
        base = hc + A(0.05, 0.04, -0.16)
        antenna(H, "", T(base), [base, base + A(0.12, 0.08, -0.25), base + A(0.2, 0.06, -0.55)], 0.022, 0.014, col="dark")
        mouth = hc + A(0, -0.12, -0.2)
    # ---------------------------------------------------------------- abdomen
    H.bone("Abdomen", "Body", (0, y, 0.35))
    if kind == "mantis":
        ab = ellipsoid(0.26, 0.22, 1.05).rot(-6, 0, 0).at(0, y + 0.0, 1.2)
        ab = ab.su(ellipsoid(0.14, 0.12, 0.2, (0, y, 0.3)), 0.1)
    elif stick:
        ab = tube([(0, y, 0.3), (0, y, 1.3), (0, y + 0.03, 2.3), (0, y + 0.1, 2.8)], [0.1, 0.09, 0.07, 0.04], k=0.03)
        for i in range(8):
            ab = ab.su(sphere(0.105 - 0.005 * i, (0, y, 0.45 + i * 0.3)), 0.05)
        ab = ab.noise(0.01, 18, 4)
    else:
        ab = ellipsoid(0.16, 0.12, 0.38, (0, y + 0.0, 0.62))
    H.piece("Gaster", "Abdomen", ab, col="primary", mat="hard" if not stick else "wood", tris=900, res=124,
            pattern=stripes(lambda Q: Q[:, 2], 1 / 0.2, width=0.15, depth=0.25))
    wings = []
    if kind == "mantis":
        tw = [(0, -0.12), (0.4, -0.2), (1.6, -0.15), (1.8, 0.0), (1.6, 0.16), (0.3, 0.14)]
        w = flat_wing(H, "Wing", (0.08, y + 0.18, 0.15), tw, yaw=-92, lift=-3, roll=-30, col="secondary", mat="leaf", rnd=0.05, tris=400,
                      pat2d=lambda x, z, d: 1 - 0.25 * np.clip(1 - np.abs(z) / 0.02, 0, 1))
        wings = [(w[0], 1), (w[1], -1)]
    # ---------------------------------------------------------------- legs
    strike = []
    if kind == "mantis":
        hip = A(0.1, y + 0.62, -0.68)
        cox = A(0.16, y + 0.2, -0.85)       # coxa hangs down
        knee = A(0.2, y + 0.6, -1.2)        # femur rises forward
        ankle = A(0.2, y + 0.22, -0.95)     # tibia folds back down
        tip = A(0.2, y + 0.05, -1.08)
        fm = round_cone(T(hip), T(cox), 0.07, 0.065).su(round_cone(T(cox), T(knee), 0.085, 0.06), 0.03)
        for i in range(5):
            c = cox + (knee - cox) * (0.2 + 0.15 * i)
            fm = fm.su(round_cone(T(c), T(c + A(0, -0.06, 0.06)), 0.02, 0.005), 0.01)
        tb = round_cone(T(knee), T(ankle), 0.05, 0.035)
        for i in range(4):
            c = knee + (ankle - knee) * (0.2 + 0.18 * i)
            tb = tb.su(round_cone(T(c), T(c + A(0, 0.03, -0.06)), 0.016, 0.004), 0.008)
        nm = leg(H, "F", hip, knee, ankle, tip, r=(0.07, 0.06, 0.035, 0.025), col="primary", femur=fm, tibia=tb, tris=(500, 300, 160))
        strike = [("LegFR", "KneeFR", "FootFR", 1), ("LegFL", "KneeFL", "FootFL", -1)]
        r = (0.05, 0.04, 0.03, 0.025)
        M = legspec((0.13, y - 0.08, -0.05), 10, 0.55, y + 0.35, 1.2, 0.3, 1.6)
        B = legspec((0.13, y - 0.08, 0.2), -40, 0.65, y + 0.35, 1.45, 0.3, 1.9)
        names = [leg(H, "M", *M, r=r, col="primary", tris=(220, 220, 160)), leg(H, "B", *B, r=r, col="primary", tris=(220, 220, 160))]
        legs = legs_rig(names, [0.5, 0.0])
        attack = "strike"
    elif stick:
        r = (0.045, 0.04, 0.03, 0.022)
        F = legspec((0.08, y - 0.04, -1.15), 80, 0.5, y + 0.15, 1.5, 0.25, 2.0)     # front legs reach forward
        M = legspec((0.09, y - 0.05, -0.35), 15, 0.75, y + 0.35, 1.5, 0.25, 1.95)
        B = legspec((0.09, y - 0.05, 0.25), -40, 0.85, y + 0.35, 1.7, 0.25, 2.2)
        names = [leg(H, t, *sp, r=r, col="primary", mat="wood", tris=(220, 220, 160), spines=0) for t, sp in (("F", F), ("M", M), ("B", B))]
        legs = legs_rig(names, [0.0, 0.5, 0.0])
        attack = "bite"
    else:
        r = (0.04, 0.032, 0.025, 0.02)
        F = legspec((0.1, y - 0.08, -0.4), 55, 0.3, y + 0.05, 0.6, 0.15, 0.75, 0.03)
        M = legspec((0.15, y - 0.08, -0.15), 30, 0.9, y + 0.5, 2.2, 0.06, 3.3, 0.025, ank_yaw=20, tip_yaw=12)
        B = legspec((0.15, y - 0.08, 0.05), -35, 0.9, y + 0.45, 2.1, 0.06, 3.0, 0.025, ank_yaw=-28, tip_yaw=-24)
        names = [leg(H, t, *sp, r=r, col="primary", tris=(200, 220, 200), beads=2) for t, sp in (("F", F), ("M", M), ("B", B))]
        legs = legs_rig(names, [0.0, 0.5, 0.0])
        attack = "bite"
    MB.walker(H, legs, head="Head", abd="Abdomen", ants=[("AntR", 1), ("AntL", -1)], wings=wings, strike=strike, height=1.5,
              stride=0.25 if not strider else 0.35, lift=0.25, period=0.75 if not strider else 0.6, attack=attack)
    rl = legs + ([{"hip": "LegFR", "knee": "KneeFR", "phase": 0.0, "side": 1}, {"hip": "LegFL", "knee": "KneeFL", "phase": 0.5, "side": -1}] if strike else [])
    finish(H, mouth=T(mouth), top=T(hc + A(0, 0.25, 0)), legs=rl)
    return H


@hero("praying mantis", "bugs")
def praying_mantis():
    return _mantis("praying mantis", "mantis", preview={"primary": "#6AC84A", "secondary": "#C8E87A", "bugEye": "#A8D85A"})


@hero("stick insect", "bugs")
def stick_insect():
    return _mantis("stick insect", "stick", preview={"primary": "#8A6A3A", "secondary": "#C8A86A", "bugEye": "#3A2A14", "wood": "#8A6A3A"})


@hero("water strider", "bugs")
def water_strider():
    return _mantis("water strider", "strider", preview={"primary": "#3A3A3A", "secondary": "#8A9098", "bugEye": "#141414", "dark": "#1E1E1E"})
