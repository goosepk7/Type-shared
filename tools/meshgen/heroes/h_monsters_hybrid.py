"""Hybrids built on the humanoid upper body of h_monsters: centaur (horse lower body: barrel, chest rising into the
human waist, three-segment horse legs with hooves and feathered fetlocks, a hair tail; spear; rideable on the
rump) and mermaid (scaled tail chain ending in a horizontal fluke, hip fins, long flowing hair; swims).

NOTE: this module imports h_monsters helpers; build.py only hashes this file, so after changing the shared humanoid
code in h_monsters rebuild these two with --force --only centaur,mermaid.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF
from kit import Hero, hero, stripes, spots, gradient, combine
import motion
import motion_monsters as mm
import h_monsters as HM
from mon_geo import T, A, U, plate

ANY = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Person", "Plant"],
       "bp": ["Humanoid", "Quadruped", "Fish", "Giant", "Biped", "Serpent"]}


@hero("centaur", "monsters")
def centaur():
    P = HM._P(s=1.0, torso=1.0, W=1.05, arm=1.0, armT=1.05, head=1.0, muscle=0.75, skin="skin", hands="fist", weapon="spear",
              nolegs=True, nopelvis=True, upper_off=(0, -0.05, -1.3), body_at=(0, 2.35, 0.1), gait="trot",
              face=dict(nose="human", ears="human", brow=0.5, jaw=False, iris=[0.35, 0.5, 0.25]),
              preview={"primary": "#8A4A1E", "secondary": "#E8D08A", "skin": "#E0A878", "hair": "#E8D08A"})
    H, C = HM._rig("centaur", P, plan="Quadruped")
    H.tags = ["centaur", "horse", "mount"]
    rib, _ = HM._torso(H, C, P)
    HM._arms(H, C, P)
    head, jaw, h, F = HM._head_human(H, C, P)
    HM._place_head(H, C, P, head, jaw, h, F)
    HM._hair(H, C, "long", col="secondary")
    HM._beard(H, C, "short", col="secondary")
    wa = C["waist"]
    # ------------------------------------------------------------------ horse body
    bar = ellipsoid(0.62, 0.62, 1.3, (0, 2.35, 0.15))
    bar = bar.su(ellipsoid(0.55, 0.62, 0.55, (0, 2.3, -0.9)), 0.35)                              # chest / brisket
    bar = bar.su(ellipsoid(0.6, 0.64, 0.62, (0, 2.42, 1.15)), 0.35)                               # hindquarters
    bar = bar.su(ellipsoid(0.24, 0.5, 0.5, (0.42, 2.3, 1.2)).mirror_x(), 0.2)                     # haunch muscles
    bar = bar.su(ellipsoid(0.24, 0.45, 0.4, (0.4, 2.2, -0.88)).mirror_x(), 0.2)                   # shoulder muscles
    bar = bar.su(round_cone((0, 2.5, -0.95), T(wa + A(0, -0.1, 0.05)), 0.56, 0.44), 0.25)         # rise into the waist
    H.piece("Torso", "Body", bar, col="primary", mat="skin", tris=2600, res=128)
    sash = (bar.round(0.04) | rib.round(0.04)) & HM.slab_y(wa[1] - 0.32, wa[1] - 0.12)
    H.piece("Sash", "Body", sash, col="secondary", mat="cloth", tris=700, role="cloth", pri=1.2)
    H.prim("Clasp", "Body", "Ellipsoid", (0.2, 0.2, 0.08), T(A(0, wa[1] - 0.22, HM._front(bar | rib, wa[1] - 0.22, 1.0)[2] - 0.05)), col="gold", mat="metal", role="detail", pri=2.0)
    # ------------------------------------------------------------------ horse legs
    legs = []
    for sx, nm in ((1, "R"), (-1, "L")):
        sfx = "" if sx > 0 else "_l"
        fs, fk, ff = A(0.38 * sx, 2.15, -0.95), A(0.4 * sx, 1.25, -0.9), A(0.4 * sx, 0.4, -0.95)
        H.bone("FLeg" + nm, "Body", T(fs))
        H.bone("FKnee" + nm, "FLeg" + nm, T(fk))
        H.bone("FFetlock" + nm, "FKnee" + nm, T(ff))
        up = round_cone(T(fs + A(0, 0.25, 0)), T(fk), 0.24, 0.13).su(ellipsoid(0.18, 0.4, 0.2, T((fs + fk) / 2 + A(0, 0.1, -0.03))), 0.1)
        H.piece("FUpper" + nm, "FLeg" + nm, up, col="primary", mat="skin", tris=700, role="limb", key=f"h_centaur_fup{sfx}")
        cn = round_cone(T(fk + A(0, 0.05, 0)), T(ff), 0.12, 0.09).su(ellipsoid(0.12, 0.12, 0.12, T(fk + A(0, 0.0, -0.02))), 0.05)
        H.piece("FCannon" + nm, "FKnee" + nm, cn, col="primary", mat="skin", tris=500, role="limb", key=f"h_centaur_fcan{sfx}")
        hs = A(0.4 * sx, 2.4, 1.2)
        hk = A(0.4 * sx, 1.15, 1.45)
        hf = A(0.4 * sx, 0.4, 1.32)
        H.bone("BLeg" + nm, "Body", T(hs))
        H.bone("BHock" + nm, "BLeg" + nm, T(hk))
        H.bone("BFetlock" + nm, "BHock" + nm, T(hf))
        th = round_cone(T(hs + A(0, 0.1, -0.05)), T(A(0.42 * sx, 1.55, 1.05)), 0.4, 0.2)
        th = th.su(round_cone(T(A(0.42 * sx, 1.6, 1.05)), T(hk), 0.2, 0.12), 0.12)
        H.piece("BThigh" + nm, "BLeg" + nm, th, col="primary", mat="skin", tris=800, role="limb", key=f"h_centaur_bth{sfx}")
        cn2 = round_cone(T(hk + A(0, 0.04, 0.05)), T(hf), 0.12, 0.09).su(sphere(0.12, T(hk + A(0, 0.0, 0.06))), 0.05)
        H.piece("BCannon" + nm, "BHock" + nm, cn2, col="primary", mat="skin", tris=500, role="limb", key=f"h_centaur_bcan{sfx}")
        for pre, bone, f_ in (("F", "FFetlock" + nm, ff), ("B", "BFetlock" + nm, hf)):
            pas = round_cone(T(f_ + A(0, 0.02, 0)), T(f_ + A(0, -0.22, -0.1)), 0.11, 0.1)
            fe = ellipsoid(0.17, 0.14, 0.17, T(f_ + A(0, -0.12, 0.02))).noise(0.02, 14, 3)
            H.piece(pre + "Feather" + nm, bone, pas.su(fe, 0.05), col="secondary", mat="skin", tris=450, role="foot", key=f"h_centaur_{pre.lower()}fea{sfx}")
            hoof = cone(0.15, 0.12, 0.1, axis=1, rr=0.02).at(*T(A(f_[0], 0.1, f_[2] - 0.12))) & plane((0, -1, 0), 0.0)
            H.piece(pre + "Hoof" + nm, bone, hoof, col="hoof", mat="hard", tris=300, role="hoof", pri=1.6, key=f"h_centaur_{pre.lower()}hoof{sfx}")
    # tail
    t0, t1, t2 = A(0, 2.75, 1.7), A(0, 2.25, 2.15), A(0, 1.35, 2.3)
    H.bone("Tail1", "Body", T(t0))
    H.bone("Tail2", "Tail1", T(t1))
    tl = U(round_cone(T(t0 + A(0, 0, -0.1)), T(t1), 0.16, 0.22), ellipsoid(0.2, 0.35, 0.25, T((t0 + t1) / 2 + A(0, -0.05, 0.05))), k=0.08).noise(0.025, 10, 1)
    H.piece("TailA", "Tail1", tl, col="secondary", mat="skin", tris=600, role="tail", pri=1.5)
    tl2 = U(round_cone(T(t1), T(t2), 0.22, 0.12), ellipsoid(0.22, 0.6, 0.2, T((t1 + t2) / 2 + A(0, 0, 0.05))), k=0.1).noise(0.03, 9, 2)
    H.piece("TailB", "Tail2", tl2, col="secondary", mat="skin", tris=700, role="tail", pri=1.6)
    P["wscale"] = 1.0
    HM._weapon(H, C, P, "spear")
    # ------------------------------------------------------------------ rig / motion
    hs_ = C["hs"]
    hc = C["hc"]
    H.socket("mouth", T(hc + A(0, -0.25, -0.5) * hs_), "Head")
    H.socket("head", T(hc + A(0, 0.55, 0) * hs_), "Head")
    H.socket("hand", T(C["grip"]), "HandR")
    H.socket("seat", (0, 2.95, 0.55), "Body")
    H.mount = {"seat": "Torso", "saddle": {"pos": (0, 2.95, 0.55), "size": (1.1, 0.16, 1.2)}}
    qlegs = [("FLegR", "FKneeR", "FFetlockR", 0.75, True), ("FLegL", "FKneeL", "FFetlockL", 0.25, True),
             ("BLegR", "BHockR", "BFetlockR", 0.5, False), ("BLegL", "BHockL", "BFetlockL", 0.0, False)]
    H.rig.update({"head": "Head", "tail": ["Tail1", "Tail2"],
                  "legs": [{"hip": a, "knee": b, "phase": ph, "side": 1 if a.endswith("R") else -1} for a, b, c, ph, f in qlegs]})
    motion.quadruped(H, qlegs, spine="Spine", head="Head", tail=["Tail1", "Tail2"], stride=0.4, walk=1.0, height=4.0, attack="pounce")

    def arm_move(t):
        u = t / 1.0
        sw = math.sin(2 * math.pi * u)
        return {"ShoulderL": (0, 0, 0, 0.25 * sw, 0, -0.1), "ElbowL": (0, 0, 0, 0.35, 0, 0), "ShoulderR": (0, 0, 0, 0.35, 0, 0.05), "ElbowR": (0, 0, 0, 0.6, 0, 0)}

    def arm_attack(t):
        s = t / 0.9
        w = mm.ease(s / 0.3) * (1 - mm.ease((s - 0.3) / 0.2))
        st = mm.bump(s, 0.3, 0.75)
        return {"ShoulderR": (0, 0, 0, 1.2 * w + 1.4 * st, 0, 0.2 * w), "ElbowR": (0, 0, 0, 1.4 * w - 0.2 * st, 0, 0), "Spine": (0, 0, 0, -0.2 * st, 0.3 * w - 0.3 * st, 0)}

    mm.overlay(H, "Move", arm_move)
    mm.overlay(H, "Idle", lambda t: {"ShoulderR": (0, 0, 0, 0.35, 0, 0.05), "ElbowR": (0, 0, 0, 0.6, 0, 0), "ShoulderL": (0, 0, 0, 0.1, 0, -0.12)})
    mm.overlay(H, "Attack", arm_attack)
    return H


@hero("mermaid", "monsters")
def mermaid():
    scales = combine(spots(0.13, 0.055, depth=0.35, ring=True, seed=6), gradient(1, 0.4, 2.2, 0.8, 1.0))
    P = HM._P(s=0.95, torso=0.95, W=0.85, arm=0.95, armT=0.8, head=1.05, muscle=0.2, skin="skin", hands="open", gait="swim",
              nolegs=True, nopelvis=True, upper_off=(0, -0.55, 0.0), body_at=(0, 2.15, 0.0), hipw=0.9,
              face=dict(nose="human", ns=0.8, ears="fin" if False else "human", brow=0.2, jaw=False, iris=[0.2, 0.6, 0.65], eye=1.1),
              preview={"primary": "#14A3A0", "secondary": "#F472B6", "skin": "#F0C29A", "hair": "#C8402A"})
    H, C = HM._rig("mermaid", P, plan="Fish")
    H.tags = ["merfolk", "aquatic"]
    rib, _ = HM._torso(H, C, P)
    HM._arms(H, C, P)
    head, jaw, h, F = HM._head_human(H, C, P)
    HM._place_head(H, C, P, head, jaw, h, F)
    HM._hair(H, C, "long", col="hair")
    s = C["s"]
    hc, hs = C["hc"], C["hs"]
    H.bone("Hair1", "Head", T(hc + A(0, 0.1, 0.4) * hs))
    lock = tube([T(hc + A(0, 0.15, 0.4) * hs), T(hc + A(0, -0.5, 0.75) * hs), T(hc + A(0, -1.3, 0.85) * hs), T(hc + A(0, -1.9, 1.1) * hs)],
                [0.32 * hs, 0.3 * hs, 0.24 * hs, 0.08 * hs], k=0.1).noise(0.015 * s, 14 / s, 3)
    H.piece("HairFlow", "Hair1", lock, col="hair", mat="cloth", tris=900, role="hair", pri=1.3)
    top = rib.round(0.035 * s) & HM.slab_y(C["chest"][1] - 0.05 * s, C["chest"][1] + 0.3 * s) & SDF(lambda p, z0=C["chest"][2]: p[:, 2] - z0 + 0.0)
    top = (rib.round(0.035 * s) & HM.slab_y(C["chest"][1] - 0.02 * s, C["chest"][1] + 0.28 * s))
    H.piece("ScaleTop", "Spine", top, col="secondary", mat="cloth", tris=900, role="cloth", pri=1.1)
    wa = C["waist"]
    # ------------------------------------------------------------------ tail chain
    pts = [A(0, 2.25, 0.0), A(0, 1.45, 0.12), A(0, 0.8, 0.45), A(0, 0.55, 1.05), A(0, 0.65, 1.6)]
    rad = [0.42, 0.34, 0.24, 0.15, 0.09]
    names = []
    hip = ellipsoid(0.44, 0.45, 0.32, (0, 2.35, 0.03)).su(round_cone(T(wa + A(0, 0.05, 0)), (0, 2.2, 0.03), 0.34, 0.42), 0.2)
    H.piece("Hips", "Body", hip, col="primary", mat="skin", tris=1100, pattern=scales)
    frill = plate([(-0.5, 0), (0.5, 0), (0.42, -0.2), (0.2, -0.12), (0, -0.28), (-0.2, -0.12), (-0.42, -0.2)], T(A(0, wa[1] - 0.25, -0.33)), (1, 0, 0), (0, 1, -0.2), 0.025, bulge=-0.1)
    H.piece("Frill", "Body", frill, col="secondary", mat="skin", tris=500, role="fin", pri=1.3)
    for i in range(4):
        nm = f"Tail{i + 1}"
        H.bone(nm, "Body" if i == 0 else f"Tail{i}", T(pts[i]))
        names.append(nm)
        a = pts[i] - (pts[i + 1] - pts[i]) * 0.15
        sg = round_cone(T(a), T(pts[i + 1]), rad[i], rad[i + 1])
        if i == 1:
            fin = plate([(0, 0), (0.35, -0.15), (0.45, -0.45), (0.2, -0.35), (0.0, -0.25)], T(pts[1] + A(0.25, 0.1, 0.05)), (1, 0, 0.2), (0, 1, 0.3), 0.02)
            H.piece("HipFins", nm, (fin | plate([(0, 0), (-0.35, -0.15), (-0.45, -0.45), (-0.2, -0.35), (0.0, -0.25)], T(pts[1] + A(-0.25, 0.1, 0.05)), (1, 0, -0.2), (0, 1, 0.3), 0.02)),
                    col="secondary", mat="skin", tris=500, role="fin", pri=1.4, tr=0.15)
        if i == 3:
            d = pts[4] - pts[3]
            d /= np.linalg.norm(d)
            fl = plate([(0, -0.05), (0.55, 0.35), (0.85, 0.55), (0.7, 0.2), (0.75, 0.0), (0.7, -0.2), (0.85, -0.55), (0.55, -0.35), (0, 0.05)][::1],
                       T(pts[4] - d * 0.1), T(d), (1, 0, 0), 0.03, bulge=0.04)
            H.piece("Fluke", nm, fl, col="secondary", mat="skin", tris=700, role="fin", pri=1.5, tr=0.1)
        H.piece(f"TailP{i + 1}", nm, sg, col="primary", mat="skin", tris=700 if i < 2 else 500, role="tail", pri=1.4 + 0.1 * i, pattern=scales)
    H.socket("mouth", T(hc + A(0, -0.25, -0.5) * hs), "Head")
    H.socket("head", T(hc + A(0, 0.55, 0) * hs), "Head")
    arms = [("ShoulderR", "ElbowR", "HandR", 1), ("ShoulderL", "ElbowL", "HandL", -1)]
    H.rig.update({"head": "Head", "tail": names, "gait": "swim"})
    mm.swimmer(H, names, arms=arms, spine="Spine", head="Head", height=4.2, hair=["Hair1"])
    return H


