"""Constructs: golems and robots. golem (chiselled stone blocks, carved glowing rune, moss), clay golem (soft
pear-shaped lumps with thumb marks), iron golem (riveted plates, furnace grille chest, visor helm), lava golem
(obsidian plates split by deep cracks over a molten core), robot (clunky boxy tin robot: panel chest with dials,
visor head and antenna, cylinder limbs, pincer hands, piston legs) and android (sleek white shell plates over dark
joints, egg helmet with a dark visor).
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF
from kit import Hero, hero, stripes, spots, gradient, combine
import motion_monsters as mm
from mon_geo import T, A, U, plate, crystal

ANY = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Person", "Plant", "Weather", "Structure", "Food", "Place"],
       "bp": ["Humanoid", "Giant", "Ghost", "Biped", "Blob", "Robot", "Orb", "Cloud", "Swarm", "Crystal", "Structure"]}


def blk(c, h, r=0.08, rot=(0, 0, 0)):
    return round_box(h[0], h[1], h[2], r).rot(*rot).at(*T(c))


def _rig(H, pts):
    H.body(T(pts["body"]))
    H.bone("Spine", "Body", T(pts["waist"]))
    H.bone("Head", "Spine", T(pts["neck"]))
    H.mbone("Shoulder#", "Spine", T(pts["sh"]))
    H.mbone("Elbow#", "Shoulder#", T(pts["el"]))
    H.mbone("Hand#", "Elbow#", T(pts["wr"]))
    H.mbone("Hip#", "Body", T(pts["hip"]))
    H.mbone("Knee#", "Hip#", T(pts["kn"]))
    H.mbone("Foot#", "Knee#", T(pts["an"]))


def _m(p, sx):
    return A(p[0] * sx, p[1], p[2])


def _sides(fn):
    for sx, nm in ((1, "R"), (-1, "L")):
        fn(sx, nm, "" if sx > 0 else "_l")


def _finish(H, pts, height, attack="slam", stride=0.35, walk=1.3, stomp=1.0, lean=0.0, weapon=None):
    hc = pts["hc"]
    H.socket("mouth", T(hc + A(0, -0.2, -0.45)), "Head")
    H.socket("head", T(hc + A(0, 0.5, 0)), "Head")
    H.socket("hand", T(pts["wr"] + A(0, -0.4, 0)), "HandR")
    H.rig.update({"head": "Head", "legs": [{"hip": "HipR", "knee": "KneeR", "phase": 0.0, "side": 1}, {"hip": "HipL", "knee": "KneeL", "phase": 0.5, "side": -1}],
                  "arms": [{"shoulder": "ShoulderR", "elbow": "ElbowR", "side": 1}, {"shoulder": "ShoulderL", "elbow": "ElbowL", "side": -1}]})
    legs = [("HipR", "KneeR", "FootR", 0.0), ("HipL", "KneeL", "FootL", 0.5)]
    arms = [("ShoulderR", "ElbowR", "HandR", 1), ("ShoulderL", "ElbowL", "HandL", -1)]
    mm.biped_extra(H, legs, arms, spine="Spine", head="Head", stride=stride, walk=walk, height=height, attack=attack, lean=lean,
                   stomp=stomp, weapon_arm=weapon)


# ================================================================================================ golems
def _golem(hid, kind, preview):
    H = Hero(hid, plan="Giant", gait="stomp", tags=["golem", "construct"])
    H.preview = preview
    s = 1.0
    pts = dict(body=A(0, 2.45, 0.05), waist=A(0, 2.85, 0.05), neck=A(0, 4.45, -0.35), sh=A(1.35, 4.25, 0.0), el=A(1.6, 3.15, -0.05),
               wr=A(1.66, 2.1, -0.22), hip=A(0.6, 2.35, 0.05), kn=A(0.66, 1.25, -0.05), an=A(0.66, 0.4, 0.05), hc=A(0, 4.75, -0.5))
    if kind == "clay":
        pts.update(sh=A(1.2, 3.95, 0.0), el=A(1.45, 2.95, -0.05), wr=A(1.5, 1.95, -0.2), neck=A(0, 4.2, -0.2), hc=A(0, 4.6, -0.3))
    _rig(H, pts)
    rng = np.random.default_rng({"stone": 1, "clay": 2, "iron": 3, "lava": 4}[kind])
    mat = {"stone": "stone", "clay": "skin", "iron": "metal", "lava": "stone"}[kind]
    col = "primary"
    bev = {"stone": 0.1, "clay": 0.3, "iron": 0.05, "lava": 0.08}[kind]

    def finish(sd, amp=1.0, seed=0):
        if kind == "stone":
            return sd.noise(0.022 * amp, 6, seed)
        if kind == "clay":
            return sd.noise(0.035 * amp, 2.5, seed)
        if kind == "lava":
            return sd.noise(0.03 * amp, 5, seed)
        return sd

    # torso
    if kind == "clay":
        tor = ellipsoid(1.1, 1.0, 0.85, (0, 3.2, 0.05)).su(ellipsoid(0.95, 0.55, 0.75, (0, 3.85, 0.0)), 0.4)
        tor = tor.su(sphere(0.55, (0.95, 3.85, 0.0)).mirror_x(), 0.3)
        for i in range(9):
            c = A(rng.uniform(-0.8, 0.8), rng.uniform(2.6, 4.0), -0.8)
            tor = tor.ss(ellipsoid(0.09, 0.13, 0.08, T(c)), 0.05)
        tor = tor.ss(ellipsoid(0.09, 0.13, 0.08, (0.5, 3.0, 0.82)), 0.05)
    elif kind == "iron":
        # rounded boiler-plate barrel chest with a riveted belly band: reads as armour, not stacked blocks
        tor = ellipsoid(1.12, 0.85, 0.72, (0, 3.75, 0.0)).su(ellipsoid(0.82, 0.5, 0.58, (0, 3.0, 0.05)), 0.25)
        tor = tor.su(ellipsoid(0.8, 0.28, 0.5, (0, 4.3, 0.12)), 0.15)
        tor = tor | (torus(0.86, 0.06).scale3(1.0, 1.0, 0.72).at(0, 3.12, 0.05))
        tor = tor.ss(torus(1.0, 0.04).scale3(1.0, 1.0, 0.7).at(0, 3.62, 0.0), 0.01)
    else:
        tor = blk((0, 3.75, 0.0), (1.05, 0.62, 0.62), bev)
        tor = tor.su(blk((0, 3.0, 0.05), (0.78, 0.42, 0.52), bev), 0.06)
        tor = tor.su(blk((0, 4.25, 0.15), (0.75, 0.22, 0.45), bev), 0.06)
        tor = tor.su(blk((0, 3.8, -0.58), (0.7, 0.42, 0.12), bev), 0.04)  # breastplate slab
    rune_c = A(0, 3.75, -0.7) if kind != "clay" else A(0, 3.6, -0.86)
    if kind in ("stone", "clay"):
        rune = plate([(-0.15, 0.25), (0.15, 0.25), (0.05, 0.05), (0.2, -0.05), (0.0, -0.3), (-0.2, -0.05), (-0.05, 0.05)], T(rune_c), (1, 0, 0), (0, 1, 0), 0.08)
        tor = tor.ss(rune, 0.01)
        H.prim("Rune", "Spine", "Ellipsoid", (0.32, 0.5, 0.08), T(rune_c + A(0, -0.02, 0.06)), col="secondary", mat="hard", glow=True, role="rune", pri=1.1)
    if kind == "iron":
        tor = tor.ss(blk(rune_c + A(0, -0.05, 0.05), (0.42, 0.3, 0.15), 0.04), 0.02)
        bars = U(*(capsule(T(rune_c + A(-0.42, y, 0.0)), T(rune_c + A(0.42, y, 0.0)), 0.035) for y in (-0.2, -0.07, 0.06, 0.19)))
        H.piece("Grille", "Spine", bars, col="gunmetal", mat="metal", tris=500, role="detail", pri=1.4)
        H.prim("Furnace", "Spine", "Block", (0.8, 0.55, 0.06), T(rune_c + A(0, -0.05, 0.12)), col="secondary", mat="hard", glow=True, role="core", pri=1.1)
        riv = None
        for x in (-0.75, -0.4, 0.4, 0.75):
            for y in (3.3, 4.1):
                riv = U(riv, sphere(0.06, (x, y, -0.62 + 0.2 * abs(x) ** 2)))
        tor = tor | riv
        tor = tor.su(cylinder(0.14, 0.4, axis=1).at(0.55, 4.5, 0.5).mirror_x(), 0.03)  # smoke stacks
        H.prim("Smoke1", "Spine", "Cylinder", (0.08, 0.2, 0.2), (0.55, 4.92, 0.5), rot=(0, 0, math.pi / 2), col="darker", mat="metal", role="detail", pri=1.6)
    tor = finish(tor, 1.0, 1)
    if kind == "lava":
        rock, core = _crack(tor, 11, 0.07, centre=(0, 3.5, 0), spread=0.5)
        H.piece("Torso", "Spine", rock, col=col, mat=mat, tris=2400, res=136)
        H.piece("TorsoCore", "Spine", core, col="secondary", mat="hard", tris=900, role="core", pri=1.0)
    else:
        H.piece("Torso", "Spine", tor, col=col, mat=mat, tris=2200, res=128)
    pel = blk((0, 2.45, 0.05), (0.85, 0.4, 0.5), bev) if kind != "clay" else ellipsoid(1.0, 0.6, 0.75, (0, 2.45, 0.05))
    pel = finish(pel, 1.0, 2)
    H.piece("Hips", "Body", pel, col=col, mat=mat, tris=900)
    if kind == "stone":
        moss = (tor.round(0.04) & SDF(lambda p: 4.35 - p[:, 1] + 0.1 * np.sin(p[:, 0] * 6) + 0.08 * np.cos(p[:, 2] * 7))).noise(0.03, 12, 3)
        H.piece("Moss", "Spine", moss, col="leaf", mat="leaf", tris=900, role="moss", pri=1.2)
    # head
    hc = pts["hc"]
    if kind == "clay":
        hd = ellipsoid(0.42, 0.45, 0.4, T(hc)).su(ellipsoid(0.3, 0.2, 0.25, T(hc + A(0, -0.25, -0.1))), 0.15)
        hd = hd.ss(ellipsoid(0.1, 0.13, 0.12, T(hc + A(0.16, 0.05, -0.38))).mirror_x(), 0.04)
        hd = hd.ss(ellipsoid(0.15, 0.06, 0.12, T(hc + A(0, -0.22, -0.38))), 0.04)
        hd = finish(hd, 0.6, 3)
        H.piece("HeadP", "Head", hd, col=col, mat=mat, tris=1000, role="head")
        for sx, nm in ((1, "R"), (-1, "L")):
            H.prim("Eye" + nm, "Head", "Ball", (0.12, 0.12, 0.12), T(hc + A(0.16 * sx, 0.05, -0.33)), col="secondary", mat="hard", glow=True, role="eye", pri=1.6)
        H.prim("MouthP", "Head", "Ellipsoid", (0.26, 0.08, 0.1), T(hc + A(0, -0.22, -0.34)), col="black", mat="hard", role="mouth", pri=1.5)
    elif kind == "iron":
        # great-helm: round bucket with a domed top, a nose ridge and a flared gorget
        hd = cylinder(0.38, 0.36, axis=1, rr=0.06).at(*T(hc)).su(ellipsoid(0.38, 0.22, 0.38, T(hc + A(0, 0.36, 0))), 0.05)
        hd = hd.su(round_box(0.04, 0.32, 0.05, 0.02).at(*T(hc + A(0, 0.12, -0.38))), 0.02)
        hd = hd.su(cone(0.52, 0.36, 0.18, axis=1, rr=0.03).at(*T(hc + A(0, -0.42, 0.02))), 0.04)
        hd = hd.ss(blk(hc + A(0, 0.02, -0.38), (0.3, 0.05, 0.1), 0.02), 0.01)
        H.piece("HeadP", "Head", hd, col=col, mat=mat, tris=900, role="head")
        H.prim("Visor", "Head", "Block", (0.5, 0.06, 0.06), T(hc + A(0, 0.02, -0.32)), col="secondary", mat="hard", glow=True, role="eye", pri=1.5)
    else:
        hd = blk(hc, (0.38, 0.36, 0.38), bev).su(blk(hc + A(0, 0.15, -0.3), (0.4, 0.09, 0.12), 0.04), 0.04)
        hd = hd.ss(blk(hc + A(0.16, 0.0, -0.4), (0.1, 0.045, 0.1), 0.02).mirror_x(), 0.01)
        hd = hd.su(blk(hc + A(0, -0.3, -0.12), (0.3, 0.12, 0.26), bev * 0.6), 0.05)
        hd = finish(hd, 0.8, 3)
        if kind == "lava":
            rock, core = _crack(hd, 13, 0.05, n=3, centre=hc, spread=0.15)
            H.piece("HeadP", "Head", rock, col=col, mat=mat, tris=1000, role="head")
            H.piece("HeadCore", "Head", core, col="secondary", mat="hard", tris=400, role="core", pri=1.0)
        else:
            H.piece("HeadP", "Head", hd, col=col, mat=mat, tris=1000, role="head")
        for sx, nm in ((1, "R"), (-1, "L")):
            H.prim("Eye" + nm, "Head", "Block", (0.17, 0.06, 0.05), T(hc + A(0.16 * sx, 0.0, -0.34)), col="secondary", mat="hard", glow=True, role="eye", pri=1.6)
        if kind == "lava":
            horns = U(*(crystal(T(hc + A(0.25 * sx, 0.3, -0.05)), T(hc + A(0.5 * sx, 0.85, 0.1)), 0.1, tip=0.4) for sx in (1, -1)))
            H.piece("Horns", "Head", horns, col="darker", mat="stone", tris=400, role="horn", pri=1.4, smooth=1)

    def limbs(sx, nm, sfx):
        sh, el, wr = _m(pts["sh"], sx), _m(pts["el"], sx), _m(pts["wr"], sx)
        hp, kn, an = _m(pts["hip"], sx), _m(pts["kn"], sx), _m(pts["an"], sx)
        mid = (sh + el) / 2
        if kind == "clay":
            ua = round_cone(T(sh + A(0, 0.05, 0)), T(el), 0.42, 0.36)
            fo = round_cone(T(el), T(wr), 0.38, 0.42)
            fist = ellipsoid(0.42, 0.42, 0.45, T(wr + A(0, -0.3, -0.05)))
            for i, dz in enumerate((-0.25, -0.05, 0.15)):
                fist = fist.su(round_cone(T(wr + A(-0.05 * sx, -0.45, dz)), T(wr + A(-0.12 * sx, -0.75, dz - 0.05)), 0.13, 0.11), 0.08)
            th = round_cone(T(hp + A(0, 0.1, 0)), T(kn), 0.48, 0.42)
            sn = round_cone(T(kn), T(an + A(0, 0.05, 0)), 0.42, 0.45)
            ft = ellipsoid(0.48, 0.32, 0.62, T(an + A(0, -0.12, -0.15))) & plane((0, -1, 0), 0.0)
        else:
            ua = blk(mid, (0.36, 0.55, 0.36), bev, rot=(0, 0, -8 * sx)).su(blk(sh + A(0.08 * sx, 0.1, 0.0), (0.55, 0.42, 0.5), bev, rot=(0, 0, -15 * sx)), 0.05)
            fo = blk((el + wr) / 2 + A(0, 0.05, 0), (0.45, 0.6, 0.45), bev, rot=(0, 0, -3 * sx))
            fist = blk(wr + A(0, -0.32, -0.05), (0.42, 0.34, 0.45), bev)
            for i, dz in enumerate((-0.3, -0.1, 0.1, 0.3)):
                fist = fist.su(blk(wr + A(-0.08 * sx, -0.72, dz), (0.11, 0.12, 0.09), bev * 0.6), 0.03)
            th = blk((hp + kn) / 2 + A(0, 0.05, 0), (0.42, 0.62, 0.45), bev)
            sn = blk((kn + an) / 2 + A(0, 0.05, 0), (0.4, 0.48, 0.42), bev).su(blk(kn + A(0, 0, -0.35), (0.25, 0.2, 0.12), bev), 0.04)
            ft = blk(an + A(0, -0.17, -0.15), (0.48, 0.23, 0.65), bev) & plane((0, -1, 0), 0.0)
            if kind == "iron":
                # round armour tubes, domed pauldrons, flared gauntlets and knee cops instead of blocks
                ua = round_cone(T(sh), T(el), 0.36, 0.32).su(ellipsoid(0.6, 0.45, 0.55, T(sh + A(0.1 * sx, 0.12, 0))), 0.06)
                ua = ua | torus(0.6, 0.04).rot(0, 0, -0.25 * sx).at(*T(sh + A(0.1 * sx, -0.05, 0)))
                fo = round_cone(T(el + A(0, -0.05, 0)), T(wr + A(0, 0.1, 0)), 0.34, 0.44)
                fo = fo.su(torus(0.44, 0.06).at(*T(wr + A(0, 0.08, 0))), 0.02)
                th = round_cone(T(hp + A(0, 0.1, 0)), T(kn), 0.44, 0.38)
                sn = round_cone(T(kn), T(an + A(0, 0.1, 0)), 0.36, 0.42).su(sphere(0.27, T(kn + A(0, 0, -0.3))), 0.05)
                riv = U(*(sphere(0.05, T(mid + A(dx * sx, dy, -0.33))) for dx in (-0.16, 0.16) for dy in (-0.3, 0.3)))
                ua = ua | riv
        parts = [("UpperArm", "Shoulder", ua, 900), ("Forearm", "Elbow", fo, 800), ("Fist", "Hand", fist, 900),
                 ("Thigh", "Hip", th, 800), ("Shin", "Knee", sn, 700), ("Foot", "Foot", ft, 600)]
        for i, (pn, bn, sd, tr) in enumerate(parts):
            sd = finish(sd, 1.0, 20 + i)
            if kind == "lava" and pn in ("UpperArm", "Forearm", "Thigh", "Shin"):
                rock, core = _crack(sd, 30 + i, 0.06, n=3, centre=(sh + el) / 2 if bn == "Shoulder" else (el + wr) / 2 if bn == "Elbow" else (hp + kn) / 2 if bn == "Hip" else (kn + an) / 2, spread=0.2)
                H.piece(pn + nm, bn + nm, rock, col=col, mat=mat, tris=tr, role="limb", key=f"h_{hid}_{pn}{sfx}".lower().replace(" ", "_"))
                H.piece(pn + "Core" + nm, bn + nm, core, col="secondary", mat="hard", tris=300, role="core", pri=1.0, key=f"h_{hid}_{pn}core{sfx}".lower().replace(" ", "_"))
            else:
                H.piece(pn + nm, bn + nm, sd, col=col, mat=mat, tris=tr, role="limb", key=f"h_{hid}_{pn}{sfx}".lower().replace(" ", "_"))
    _sides(limbs)
    if kind == "stone":
        cry = U(*(crystal(T(A(1.15 * sx, 4.55, 0.2) + A(rng.uniform(-0.2, 0.2), 0, rng.uniform(-0.2, 0.2))),
                          T(A(1.15 * sx, 4.55, 0.2) + A(0.3 * sx + rng.uniform(-0.1, 0.1), 0.55 + rng.uniform(0, 0.3), rng.uniform(-0.2, 0.3))),
                          0.1, tip=0.35, twist=rng.uniform(0, 1)) for sx in (1, -1) for _ in range(3)))
        H.piece("Crystals", "Spine", cry, col="secondary", mat="glass", tris=700, role="crystal", pri=1.3, smooth=1)
    if kind == "clay":
        H.prim("ScrollP", "Spine", "Cylinder", (0.12, 0.35, 0.12), (0, 4.2, -0.62), rot=(0, 0, math.pi / 2), col="cream", mat="cloth", role="detail", pri=1.8)
    _finish(H, pts, 5.4, attack="slam", stride=0.3 if kind != "clay" else 0.36, walk=1.4, stomp=1.0)
    return H


def _crack(sd, seed, depth, n=5, centre=(0, 0, 0), spread=0.35):
    """Split a rock SDF with deep planar cracks near `centre`; return (rock, core). The core is the rock shrunk by
    `depth` so it only shows at the bottom of the cracks (molten seams, no glow needed)."""
    r_ = np.random.default_rng(seed)
    c0 = np.asarray(centre, float)
    cuts = []
    for i in range(n):
        nv = r_.normal(size=3)
        nv[1] *= 0.6
        nv /= np.linalg.norm(nv)
        cuts.append((nv, float(nv @ c0) + r_.uniform(-spread, spread), r_.uniform(0.03, 0.05)))

    g = depth + 0.08  # grooves stop short of the middle so the rock stays one solid body over the core

    def rock_f(p):
        d0 = sd(p)
        d = d0
        for nv, off, w in cuts:
            d = np.maximum(d, np.minimum(w - np.abs(p @ nv - off), d0 + g))
        return d

    return SDF(rock_f), SDF(lambda p: sd(p) + depth + 0.02)


@hero("golem", "constructs")
def golem():
    return _golem("golem", "stone", {"primary": "#B5A07E", "secondary": "#38BDF8", "leaf": "#6B8E3A"})


@hero("clay golem", "constructs")
def clay_golem():
    return _golem("clay golem", "clay", {"primary": "#B07A45", "secondary": "#FDE68A"})


@hero("iron golem", "constructs")
def iron_golem():
    return _golem("iron golem", "iron", {"primary": "#6B7280", "secondary": "#F06A2A"})


@hero("lava golem", "constructs")
def lava_golem():
    return _golem("lava golem", "lava", {"primary": "#2E2626", "secondary": "#F97316", "darker": "#1A1515"})


# ================================================================================================ robots
@hero("robot", "constructs")
def robot():
    """Clunky retro robot: boxy chest with a recessed panel of dials and buttons, accordion waist, box head with a
    glowing visor, antenna and ear bolts, cylinder arms with ball joints and pincer hands, piston legs, big boots."""
    H = Hero("robot", plan="Biped", gait="biped", tags=["robot", "machine"])
    H.preview = {"primary": "#9AA6B6", "secondary": "#3B82F6"}
    pts = dict(body=A(0, 2.3, 0.0), waist=A(0, 2.75, 0.0), neck=A(0, 4.2, -0.02), sh=A(0.98, 3.95, 0.0), el=A(1.1, 3.0, -0.02),
               wr=A(1.14, 2.15, -0.15), hip=A(0.42, 2.2, 0.0), kn=A(0.44, 1.2, -0.05), an=A(0.44, 0.35, 0.03), hc=A(0, 4.55, -0.02))
    _rig(H, pts)
    met = dict(col="primary", mat="metal")
    tor = blk((0, 3.5, 0.0), (0.82, 0.62, 0.52), 0.1).ss(blk((0, 3.45, -0.55), (0.48, 0.38, 0.1), 0.04), 0.02)
    tor = tor.su(cylinder(0.24, 0.2, axis=0, rr=0.04).at(0.82, 3.95, 0.0).mirror_x(), 0.03)
    tor = tor | U(*(sphere(0.045, (x, y, -0.53)) for x in (-0.72, 0.72) for y in (3.0, 4.0)))
    H.piece("Chest", "Spine", tor, tris=1600, **met)
    H.prim("Panel", "Spine", "Block", (0.86, 0.66, 0.05), (0, 3.45, -0.52), col="gunmetal", mat="metal", role="detail", pri=1.2)
    for i, (x, y, c) in enumerate(((-0.25, 3.62, "red"), (-0.05, 3.62, [0.2, 0.9, 0.3]), (0.15, 3.62, [1.0, 0.85, 0.2]))):
        H.prim(f"Button{i}", "Spine", "Ball", (0.11, 0.11, 0.08), (x, y, -0.56), col=c, mat="hard", glow=True, role="light", pri=2.0)
    H.prim("Dial", "Spine", "Cylinder", (0.06, 0.26, 0.26), (0.22, 3.3, -0.56), rot=(0, math.pi / 2, 0), col="white", mat="hard", role="detail", pri=2.0)
    H.prim("Needle", "Spine", "Block", (0.03, 0.12, 0.02), (0.22, 3.33, -0.6), rot=(0, 0, 0.6), col="black", mat="hard", role="detail", pri=2.2)
    H.prim("Grille", "Spine", "Block", (0.3, 0.14, 0.04), (-0.17, 3.24, -0.55), col="darker", mat="metal", role="detail", pri=2.0)
    acc = U(*(torus(0.42 - 0.02 * i, 0.07).at(0, 2.55 + 0.13 * i, 0.0) for i in range(4)), cylinder(0.38, 0.28).at(0, 2.75, 0))
    H.piece("Waist", "Spine", acc, col="gunmetal", mat="metal", tris=900, role="joint", pri=1.3)
    pel = blk((0, 2.2, 0.0), (0.62, 0.25, 0.42), 0.08)
    H.piece("Pelvis", "Body", pel, tris=600, **met)
    hc = pts["hc"]
    hd = blk(hc, (0.48, 0.4, 0.42), 0.08).ss(blk(hc + A(0, 0.05, -0.42), (0.38, 0.1, 0.08), 0.03), 0.01)
    hd = hd.su(cylinder(0.12, 0.08, axis=0, rr=0.02).at(*T(hc + A(0.5, 0.0, 0))).mirror_x(), 0.02)
    hd = hd | capsule(T(hc + A(0, 0.38, 0.05)), T(hc + A(0, 0.85, 0.05)), 0.03)
    hd = hd.su(cylinder(0.16, 0.12).at(*T(hc + A(0, -0.45, 0))), 0.03)
    H.piece("HeadP", "Head", hd, tris=1100, role="head", **met)
    H.prim("Visor", "Head", "Block", (0.72, 0.15, 0.05), T(hc + A(0, 0.05, -0.37)), col="secondary", mat="hard", glow=True, role="eye", pri=1.6)
    H.prim("AntBall", "Head", "Ball", (0.13, 0.13, 0.13), T(hc + A(0, 0.88, 0.05)), col="red", mat="hard", glow=True, role="light", pri=2.0)
    H.prim("Mouthgrille", "Head", "Block", (0.36, 0.08, 0.04), T(hc + A(0, -0.2, -0.42)), col="darker", mat="metal", role="mouth", pri=1.8)

    def limbs(sx, nm, sfx):
        sh, el, wr = _m(pts["sh"], sx), _m(pts["el"], sx), _m(pts["wr"], sx)
        hp, kn, an = _m(pts["hip"], sx), _m(pts["kn"], sx), _m(pts["an"], sx)
        ua = U(sphere(0.22, T(sh)), cylinder(0.14, 0.38).at(*T((sh + el) / 2)), k=0.0)
        H.piece("UpperArm" + nm, "Shoulder" + nm, ua, tris=500, role="limb", key=f"h_robot_ua{sfx}", **met)
        fo = U(sphere(0.17, T(el)), cylinder(0.19, 0.32, rr=0.04).at(*T((el + wr) / 2 + A(0, 0.03, 0))), k=0.0)
        fo = fo | U(*(torus(0.2, 0.025).at(*T((el + wr) / 2 + A(0, y, 0))) for y in (-0.2, 0.2)))
        H.piece("Forearm" + nm, "Elbow" + nm, fo, tris=700, role="limb", key=f"h_robot_fo{sfx}", **met)
        cl = cylinder(0.15, 0.08).at(*T(wr + A(0, -0.08, 0)))
        for dz in (-1, 1):
            cl = cl | tube([T(wr + A(0, -0.12, 0.06 * dz)), T(wr + A(0, -0.35, 0.16 * dz)), T(wr + A(0, -0.5, 0.06 * dz))], [0.055, 0.05, 0.035], k=0.02)
        H.piece("Pincer" + nm, "Hand" + nm, cl, col="gunmetal", mat="metal", tris=600, role="hand", key=f"h_robot_pin{sfx}")
        th = U(sphere(0.2, T(hp)), cylinder(0.15, 0.4).at(*T((hp + kn) / 2)), sphere(0.17, T(kn)))
        H.piece("Thigh" + nm, "Hip" + nm, th, tris=500, role="limb", key=f"h_robot_th{sfx}", **met)
        sn = U(cylinder(0.2, 0.36, rr=0.04).at(*T((kn + an) / 2 + A(0, 0.08, 0))), cylinder(0.1, 0.12).at(*T(an + A(0, 0.08, 0))))
        H.piece("Shin" + nm, "Knee" + nm, sn, tris=500, role="limb", key=f"h_robot_sn{sfx}", **met)
        bt = blk(an + A(0, -0.17, -0.12), (0.26, 0.18, 0.42), 0.08) & plane((0, -1, 0), 0.0)
        H.piece("Boot" + nm, "Foot" + nm, bt, col="gunmetal", mat="metal", tris=500, role="foot", key=f"h_robot_boot{sfx}")
    _sides(limbs)
    _finish(H, pts, 5.0, attack="punch", stride=0.4, walk=1.0, stomp=0.4)
    return H


@hero("android", "constructs")
def android():
    """Sleek android: smooth white shell plates (chest, abdomen plate, pelvis) over dark joints, slim limbs with
    separate shell sleeves, an egg helmet with a dark glass face visor and two eye lights, seam grooves."""
    H = Hero("android", plan="Biped", gait="biped", tags=["robot", "machine"])
    H.preview = {"primary": "#ECEFF3", "secondary": "#22D3EE"}
    pts = dict(body=A(0, 2.85, 0.0), waist=A(0, 3.3, 0.0), neck=A(0, 4.62, -0.02), sh=A(0.72, 4.35, 0.02), el=A(0.86, 3.35, 0.05),
               wr=A(0.9, 2.45, -0.07), hip=A(0.33, 2.75, 0.0), kn=A(0.34, 1.5, -0.06), an=A(0.34, 0.3, 0.05), hc=A(0, 5.05, -0.05))
    _rig(H, pts)
    shell = dict(col="primary", mat="plastic")
    joint = dict(col="gunmetal", mat="metal")
    tor = ellipsoid(0.55, 0.55, 0.34, (0, 3.95, 0.0)).su(ellipsoid(0.3, 0.2, 0.15, (0.2, 4.08, -0.22)).mirror_x(), 0.1)
    tor = tor.su(capsule((-0.55, 4.32, 0.02), (0.55, 4.32, 0.02), 0.17), 0.15)
    tor = tor.ss(capsule((0, 4.35, -0.36), (0, 3.55, -0.34), 0.02), 0.01)
    tor = tor.ss(capsule((-0.45, 3.7, -0.25), (0.45, 3.7, -0.25), 0.015), 0.01)
    H.piece("ChestShell", "Spine", tor, tris=1500, **shell)
    core = U(round_cone((0, 3.6, 0.02), (0, 3.0, 0.02), 0.3, 0.28), round_cone((0, 4.5, 0.0), (0, 4.95, -0.02), 0.12, 0.1), k=0.05)
    for i in range(4):
        core = core.su(torus(0.31, 0.03).at(0, 3.05 + 0.13 * i, 0.02), 0.02)
    H.piece("Core", "Spine", core, tris=900, role="joint", pri=1.2, **joint)
    ab = ellipsoid(0.33, 0.3, 0.26, (0, 3.35, -0.06)) & SDF(lambda p: -0.05 - p[:, 2])
    H.piece("AbPlate", "Spine", ab, tris=500, role="armor", pri=1.3, **shell)
    H.prim("Light", "Spine", "Ball", (0.14, 0.14, 0.06), (0, 4.05, -0.33), col="secondary", mat="hard", glow=True, role="light", pri=2.0)
    pel = ellipsoid(0.44, 0.3, 0.3, (0, 2.85, 0.0)).su(ellipsoid(0.18, 0.2, 0.18, (0.3, 2.75, 0.0)).mirror_x(), 0.1)
    H.piece("Pelvis", "Body", pel, tris=800, **shell)
    hc = pts["hc"]
    hd = ellipsoid(0.33, 0.4, 0.37, T(hc + A(0, 0.03, 0.02))).su(ellipsoid(0.24, 0.18, 0.2, T(hc + A(0, -0.22, -0.1))), 0.12)
    hd = hd.ss(capsule(T(hc + A(-0.34, 0.02, 0.05)), T(hc + A(0.34, 0.02, 0.05)), 0.015), 0.01)
    H.piece("HeadP", "Head", hd, tris=1200, role="head", **shell)
    visor = ellipsoid(0.28, 0.22, 0.2, T(hc + A(0, 0.0, -0.22))) & SDF(lambda p, z0=hc[2]: (z0 - 0.15) - p[:, 2] * 1.0 - 0.0)
    H.piece("Visor", "Head", visor, col="black", mat="glass", tris=600, role="face", pri=1.3)
    for sx, nm in ((1, "R"), (-1, "L")):
        H.prim("Eye" + nm, "Head", "Ellipsoid", (0.1, 0.05, 0.05), T(hc + A(0.11 * sx, 0.03, -0.41)), col="secondary", mat="hard", glow=True, role="eye", pri=1.8)
    H.piece("Neck", "Head", U(*(torus(0.11, 0.025).at(*T(hc + A(0, -0.42 - 0.07 * i, 0.03))) for i in range(3)), capsule(T(hc + A(0, -0.62, 0.03)), T(hc + A(0, -0.3, 0.03)), 0.08)),
            tris=400, role="joint", pri=1.3, **joint)

    def limbs(sx, nm, sfx):
        sh, el, wr = _m(pts["sh"], sx), _m(pts["el"], sx), _m(pts["wr"], sx)
        hp, kn, an = _m(pts["hip"], sx), _m(pts["kn"], sx), _m(pts["an"], sx)
        H.piece("ShJoint" + nm, "Shoulder" + nm, U(sphere(0.17, T(sh)), capsule(T(sh), T(el), 0.08), sphere(0.12, T(el))), tris=500, role="joint", key=f"h_android_shj{sfx}", **joint)
        ua = ellipsoid(0.17, 0.42, 0.17, T((sh + el) / 2 + A(0, 0.05, 0))).su(ellipsoid(0.22, 0.18, 0.22, T(sh + A(0.04 * sx, 0.03, 0))), 0.06)
        H.piece("UpperArm" + nm, "Shoulder" + nm, ua, tris=600, role="limb", key=f"h_android_ua{sfx}", **shell)
        fo = U(capsule(T(el), T(wr), 0.07), sphere(0.08, T(wr)))
        H.piece("ForeJoint" + nm, "Elbow" + nm, fo, tris=300, role="joint", key=f"h_android_foj{sfx}", **joint)
        H.piece("Forearm" + nm, "Elbow" + nm, ellipsoid(0.14, 0.38, 0.15, T((el + wr) / 2 + A(0, 0.03, 0))), tris=500, role="limb", key=f"h_android_fo{sfx}", **shell)
        hand = round_box(0.05, 0.11, 0.1, 0.04).at(*T(wr + A(0, -0.13, -0.01)))
        for dz in (-0.07, -0.025, 0.025, 0.07):
            hand = hand | tube([T(wr + A(0, -0.22, dz)), T(wr + A(-0.03 * sx, -0.36, dz - 0.01)), T(wr + A(-0.08 * sx, -0.44, dz - 0.02))], [0.028, 0.025, 0.02], k=0.01)
        hand = hand | tube([T(wr + A(-0.04 * sx, -0.1, -0.09)), T(wr + A(-0.09 * sx, -0.2, -0.15))], [0.03, 0.025], k=0.01)
        H.piece("Hand" + nm + "P", "Hand" + nm, hand, tris=600, role="hand", key=f"h_android_hand{sfx}", **joint)
        H.piece("HipJoint" + nm, "Hip" + nm, U(sphere(0.16, T(hp)), capsule(T(hp), T(kn), 0.09), sphere(0.13, T(kn))), tris=500, role="joint", key=f"h_android_hj{sfx}", **joint)
        th = ellipsoid(0.2, 0.52, 0.21, T((hp + kn) / 2 + A(0, 0.05, -0.02)))
        H.piece("Thigh" + nm, "Hip" + nm, th, tris=600, role="limb", key=f"h_android_th{sfx}", **shell)
        H.piece("ShinJoint" + nm, "Knee" + nm, capsule(T(kn), T(an + A(0, 0.05, 0)), 0.08), tris=300, role="joint", key=f"h_android_snj{sfx}", **joint)
        sn = ellipsoid(0.17, 0.5, 0.19, T((kn + an) / 2 + A(0, 0.1, -0.02))).su(ellipsoid(0.12, 0.12, 0.08, T(kn + A(0, 0, -0.12))), 0.04)
        H.piece("Shin" + nm, "Knee" + nm, sn, tris=600, role="limb", key=f"h_android_sn{sfx}", **shell)
        ft = U(ellipsoid(0.16, 0.14, 0.36, T(an + A(0, -0.15, -0.15))), sphere(0.1, T(an))) & plane((0, -1, 0), 0.0)
        H.piece("Foot" + nm + "P", "Foot" + nm, ft, tris=500, role="foot", key=f"h_android_ft{sfx}", **shell)
    _sides(limbs)
    _finish(H, pts, 5.5, attack="punch", stride=0.5, walk=0.95, stomp=0.0)
    return H


