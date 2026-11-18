"""Apes and monkeys: gorilla (silverback, sagittal crest, knuckle walk), chimpanzee (big ears, pale face), orangutan
(very long shaggy arms, cheek flanges, throat sac), monkey (long curling tail, flat hands) and ring-tailed lemur
(fox snout, orange eyes, ringed tail held high).

One parametric sculpt in a knuckle-walking stance: pitched barrel torso with shoulder humps, long arms planted on
knuckles (or flat palms), short bent legs on grasping feet with an opposable big toe, a skull with brow shelf and
muzzle, a separate skin-coloured face mask, an opening jaw, and fur noise. Motion: motion.quadruped knuckle walk
plus an upright chest-beat (gorilla / orangutan) or double-fist slam / bite attack.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF
from kit import Hero, hero, stripes, spots, gradient, combine
import motion
import motion_monsters as mm
from mon_geo import T, A, U, plate

ANIMALS = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Plant", "Person"],
           "bp": ["Biped", "Quadruped", "Humanoid", "Giant"]}

BASE = dict(s=1.0, G=1.0, AL=1.0, LL=1.0, HS=1.0, muzzle=1.0, crest=0.0, ears=1.0, flange=0.0, fur=0.03, shag=0.0,
            tail=None, hand="knuckle", face=[0.2, 0.18, 0.18], silver=False, beat=True, snout="ape", eye_col="iris",
            preview={}, chest=1.0, mane=0.0, height_tag="ape")


def _ape(hid, **kw):
    P = dict(BASE)
    P.update(kw)
    s, G, AL, LL, HS = P["s"], P["G"], P["AL"], P["LL"], P["HS"]
    H = Hero(hid, plan="Quadruped", gait="trot" if P["hand"] == "palm" else "heavy", tags=["ape", "mammal"])
    H.preview = P["preview"]

    def v(x, y, z):
        return A(x, y, z) * s

    fur = P["fur"] * s

    def furry(sd, k=1.0, seed=0):
        return sd.noise(fur * k, 10.0 / s, seed) if fur > 0 else sd

    shY = 0.3 + 2.1 * AL
    hipY = 0.25 + 1.3 * LL
    sh = v(0.62 * G, shY, -0.6)
    el = v(0.74 * G, 0.3 + 1.05 * AL, -0.55)
    wr = v(0.72 * G, 0.42, -0.7)
    hp = v(0.42 * G, hipY, 0.72)
    kn = v(0.52 * G, hipY * 0.55, 0.22)
    an = v(0.48 * G, 0.3, 0.78)
    hc = v(0, shY + 0.12 * HS, -1.2 - 0.12 * HS)
    hs = 0.6 * HS * s
    H.body(T(v(0, (shY + hipY) / 2 - 0.15, 0.05)))
    H.bone("Neck", "Body", T(v(0, shY - 0.05, -0.75)))
    H.bone("Head", "Neck", T(hc + A(0, -0.1, 0.3) * hs))
    H.mbone("ShoulderF#", "Body", T(sh))
    H.mbone("ElbowF#", "ShoulderF#", T(el))
    H.mbone("WristF#", "ElbowF#", T(wr))
    H.mbone("HipB#", "Body", T(hp))
    H.mbone("KneeB#", "HipB#", T(kn))
    H.mbone("AnkleB#", "KneeB#", T(an))

    # ------------------------------------------------------------------ torso
    ch = v(0, shY - 0.3, -0.45)
    tor = ellipsoid(0.82 * G * s, 0.72 * G * s * P["chest"], 0.72 * s, T(ch))
    tor = tor.su(ellipsoid(0.66 * G * s, 0.6 * G * s, 0.75 * s, T(v(0, (shY + hipY) / 2 - 0.2, 0.15))), 0.35 * s)
    tor = tor.su(ellipsoid(0.56 * G * s, 0.5 * s, 0.5 * s, T(v(0, hipY + 0.02, 0.6))), 0.3 * s)
    tor = tor.su(ellipsoid(0.38 * G * s, 0.42 * s, 0.45 * s, T(sh + v(-0.08, 0.08, 0.05))).mirror_x(), 0.2 * s)
    tor = tor.su(round_cone(T(v(0, shY + 0.02, -0.55)), T(hc + A(0, -0.15, 0.35) * hs), 0.45 * G * s, 0.3 * HS * s), 0.2 * s)
    if P["mane"]:
        tor = tor.su(ellipsoid(0.9 * G * s, 0.55 * s, 0.6 * s, T(v(0, shY + 0.15, -0.55))).noise(0.05 * s, 8 / s, 4), 0.2 * s)
    tor = furry(tor, 1.0, 1)
    if P["shag"]:
        tor = tor.su(ellipsoid(0.7 * G * s, 0.35 * s, 0.85 * s, T(v(0, (shY + hipY) / 2 - 0.7, 0.05))).noise(0.08 * s, 6 / s, 2), 0.25 * s)
    H.piece("Torso", "Body", tor, col="primary", mat="skin", tris=2600, res=128)
    if P["silver"]:
        sad = tor.round(0.02 * s) & SDF(lambda p, y0=(hipY - 0.05) * s: y0 - p[:, 1] + 0.0) & SDF(lambda p: -0.3 * s - (p[:, 2] - 0.0) * -1.0 - 0.0)
        sad = tor.round(0.025 * s) & SDF(lambda p, y0=hipY * s, z0=-0.2 * s: np.maximum(y0 - 0.1 * s - p[:, 1], z0 - p[:, 2]))
        H.piece("Silverback", "Body", sad.noise(0.02 * s, 12 / s, 3), col="secondary", mat="skin", tris=1200, role="fur", pri=1.15)
    # ------------------------------------------------------------------ arms (front legs)
    for sx, nm in ((1, "R"), (-1, "L")):
        def m(p, sx=sx):
            return A(p[0] * sx, p[1], p[2])
        sfx = "" if sx > 0 else "_l"
        S_, E_, W_ = m(sh), m(el), m(wr)
        ua = round_cone(T(S_ + v(0, 0.08, 0)), T(E_), 0.3 * G * s, 0.2 * G * s)
        ua = ua.su(ellipsoid(0.24 * G * s, 0.42 * AL * s, 0.24 * G * s, T((S_ + E_) / 2 + v(0, 0.05, -0.08))), 0.12 * s)
        if P["shag"]:
            ua = ua.su(round_cone(T((S_ + E_) / 2 + v(0, 0, 0.12)), T((S_ + E_) / 2 + v(0.05 * sx, -0.75, 0.25)), 0.22 * s, 0.05 * s).noise(0.04 * s, 9 / s, 7), 0.1 * s)
        H.piece("UpperArm" + nm, "ShoulderF" + nm, furry(ua, 1.0, 2), col="primary", mat="skin", tris=900, role="limb", key=f"h_{hid}_ua{sfx}".replace(" ", "_"))
        fo = round_cone(T(E_ + v(0, 0.04, 0)), T(W_ + v(0, 0.05, 0)), 0.21 * G * s, 0.15 * G * s)
        fo = fo.su(ellipsoid(0.2 * G * s, 0.38 * AL * s, 0.2 * G * s, T(E_ + (W_ - E_) * 0.3 + v(0.02 * sx, 0, -0.03))), 0.1 * s)
        if P["shag"]:
            fo = fo.su(round_cone(T(E_ + (W_ - E_) * 0.3 + v(0, 0, 0.1)), T(E_ + (W_ - E_) * 0.3 + v(0.05 * sx, -0.6, 0.2)), 0.16 * s, 0.04 * s).noise(0.04 * s, 9 / s, 8), 0.08 * s)
        H.piece("Forearm" + nm, "ElbowF" + nm, furry(fo, 0.8, 3), col="primary", mat="skin", tris=800, role="limb", key=f"h_{hid}_fo{sfx}".replace(" ", "_"))
        if P["hand"] == "knuckle":
            hd = round_box(0.15 * G * s, 0.16 * s, 0.2 * G * s, 0.08 * s, T(W_ + v(0, -0.2, -0.08)))
            for i, dz in enumerate((-0.22, -0.08, 0.06, 0.18)):
                hd = hd.su(sphere(0.085 * G * s, T(W_ + v(-0.02 * sx, -0.33, dz - 0.05))), 0.05 * s)
            hd = hd.su(capsule(T(W_ + v(-0.13 * sx, -0.15, -0.2)), T(W_ + v(-0.15 * sx, -0.28, -0.3)), 0.06 * s), 0.04 * s)
        else:  # flat palm with fingers forward
            hd = round_box(0.12 * G * s, 0.06 * s, 0.14 * s, 0.05 * s, T(W_ + v(0, -0.36, -0.1)))
            for i, dx in enumerate((-0.08, -0.025, 0.025, 0.08)):
                hd = hd.su(capsule(T(W_ + v(dx, -0.38, -0.2)), T(W_ + v(dx * 1.3, -0.39, -0.38)), 0.035 * s), 0.02 * s)
            hd = hd.su(capsule(T(W_ + v(-0.12 * sx, -0.36, -0.12)), T(W_ + v(-0.2 * sx, -0.38, -0.22)), 0.035 * s), 0.02 * s)
            hd = hd.su(round_cone(T(W_ + v(0, 0.05, 0)), T(W_ + v(0, -0.32, -0.08)), 0.1 * G * s, 0.08 * s), 0.06 * s)
        hd = hd & plane((0, -1, 0), 0.0)
        H.piece("HandP" + nm, "WristF" + nm, furry(hd, 0.3, 4), col=P["face"], mat="skin", tris=700, role="hand", key=f"h_{hid}_hand{sfx}".replace(" ", "_"))
        Hp, Kn, An = m(hp), m(kn), m(an)
        th = round_cone(T(Hp + v(0, 0.1, 0)), T(Kn), 0.3 * G * s, 0.2 * s)
        th = th.su(ellipsoid(0.24 * G * s, 0.3 * s, 0.38 * s, T((Hp + Kn) / 2 + v(0, 0.05, 0.05))), 0.12 * s)
        H.piece("Thigh" + nm, "HipB" + nm, furry(th, 1.0, 5), col="primary", mat="skin", tris=800, role="limb", key=f"h_{hid}_th{sfx}".replace(" ", "_"))
        sn = round_cone(T(Kn + v(0, 0.04, 0)), T(An + v(0, 0.05, 0)), 0.2 * s, 0.13 * s)
        sn = sn.su(ellipsoid(0.15 * s, 0.25 * s, 0.17 * s, T(Kn + (An - Kn) * 0.35 + v(0, -0.02, 0.06))), 0.08 * s)
        H.piece("Shin" + nm, "KneeB" + nm, furry(sn, 0.8, 6), col="primary", mat="skin", tris=600, role="limb", key=f"h_{hid}_sn{sfx}".replace(" ", "_"))
        ft = round_cone(T(An + v(0, 0.05, 0.02)), T(An + v(0, -0.18, 0.05)), 0.13 * s, 0.13 * s)
        ft = ft.su(ellipsoid(0.16 * s, 0.1 * s, 0.32 * s, T(An + v(0, -0.2, -0.2))), 0.08 * s)
        for i, dx in enumerate((-0.07, -0.02, 0.03, 0.08)):
            ft = ft.su(capsule(T(An + v(dx, -0.23, -0.42)), T(An + v(dx * 1.2, -0.25, -0.55)), 0.04 * s), 0.03 * s)
        ft = ft.su(tube([T(An + v(-0.14 * sx, -0.22, -0.1)), T(An + v(-0.26 * sx, -0.24, -0.25)), T(An + v(-0.3 * sx, -0.25, -0.38))], [0.06 * s, 0.05 * s, 0.045 * s], k=0.02), 0.04 * s)
        ft = ft & plane((0, -1, 0), 0.0)
        H.piece("FootP" + nm, "AnkleB" + nm, ft, col=P["face"], mat="skin", tris=650, role="foot", key=f"h_{hid}_ft{sfx}".replace(" ", "_"))

    # ------------------------------------------------------------------ head
    def h(x, y, z):
        return T(hc + A(x, y, z) * hs)

    mz = P["muzzle"]
    if P["snout"] == "lemur":
        hd = ellipsoid(0.38 * hs, 0.34 * hs, 0.4 * hs, h(0, 0.08, 0.05))
        hd = hd.su(round_cone(h(0, 0.02, -0.2), h(0, -0.12, -0.75 * mz), 0.24 * hs, 0.08 * hs), 0.12 * hs)
        hd = hd.su(ellipsoid(0.3 * hs, 0.22 * hs, 0.25 * hs, h(0.18, -0.05, 0.0)).mirror_x(), 0.1 * hs)
        hd = hd.ss(sphere(0.12 * hs, h(0.17, 0.08, -0.28)).mirror_x(), 0.04 * hs)
        ear = round_cone(h(0.25, 0.25, 0.05), h(0.42, 0.55 * P["ears"], 0.12), 0.12 * hs, 0.05 * hs)
        hd = hd.su(ear.mirror_x(), 0.05 * hs)
        hd = furry(hd, 0.4, 7)
        jaw = ellipsoid(0.13 * hs, 0.06 * hs, 0.3 * mz * hs, h(0, -0.18, -0.45 * mz))
        jb = h(0, -0.1, -0.05)
        eye_p, er, look = h(0.17, 0.08, -0.31), 0.1 * hs, (0.35, 0.05, -1.0)
        H.prim("NoseTip", "Head", "Ellipsoid", (0.1 * hs, 0.07 * hs, 0.06 * hs), h(0, -0.1, -0.77 * mz), col="black", mat="hard", role="nose", pri=2.0)
        face = None
        # white face mask with a dark eye-patch muzzle
        face = (hd.round(0.012 * s) & sphere(0.42 * hs, h(0, -0.05, -0.45)))
    else:
        hd = ellipsoid(0.4 * hs, 0.42 * hs, 0.42 * hs, h(0, 0.1, 0.08))
        hd = hd.su(ellipsoid(0.3 * hs, 0.26 * hs, 0.26 * mz * hs, h(0, -0.18, -0.3 - 0.08 * mz)), 0.14 * hs)
        hd = hd.su(capsule(h(-0.27, 0.1, -0.33), h(0.27, 0.1, -0.33), 0.09 * hs), 0.06 * hs)
        hd = hd.ss(sphere(0.095 * hs, h(0.14, 0.02, -0.37)).mirror_x(), 0.03 * hs)
        hd = hd.ss(ellipsoid(0.035 * hs, 0.03 * hs, 0.05 * hs, h(0.05, -0.12, -0.55 - 0.08 * mz)).mirror_x(), 0.01 * hs)
        if P["crest"]:
            hd = hd.su(round_cone(h(0, 0.45, -0.15), h(0, 0.55 + 0.35 * P["crest"], 0.25), 0.2 * hs, 0.12 * hs), 0.12 * hs)
        e = P["ears"]
        hd = hd.su(ellipsoid(0.06 * hs, 0.14 * e * hs, 0.12 * e * hs, h(0.39 + 0.06 * e, 0.02, 0.06)).mirror_x(), 0.04 * hs)
        hd = hd.ss(ellipsoid(0.04 * hs, 0.09 * e * hs, 0.07 * e * hs, h(0.45 + 0.08 * e, 0.02, 0.04)).mirror_x(), 0.02 * hs)
        hd = hd.ss(box(0.45 * hs, 0.2 * hs, 0.35 * hs, h(0, -0.5, -0.45)), 0.04 * hs)
        if P["flange"]:
            fl = P["flange"]
            hd = hd.su(ellipsoid(0.25 * fl * hs, 0.42 * fl * hs, 0.1 * hs, h(0.38 + 0.15 * fl, -0.02, -0.12)).mirror_x(), 0.08 * hs)
        hd = furry(hd, 0.4, 7)
        jaw = ellipsoid(0.24 * hs, 0.13 * hs, 0.24 * mz * hs, h(0, -0.38, -0.25 - 0.05 * mz))
        jaw = jaw.su(round_cone(h(0.25, -0.1, 0.05), h(0.17, -0.36, -0.2), 0.08 * hs, 0.09 * hs).mirror_x(), 0.07 * hs)
        jb = h(0, -0.2, 0.02)
        eye_p, er, look = h(0.14, 0.02, -0.35), 0.06 * hs, (0.12, 0.0, -1.0)
        face = ellipsoid(0.3 * hs, 0.32 * hs, 0.2 * hs, h(0, -0.05, -0.36)).su(ellipsoid(0.25 * hs, 0.22 * hs, 0.22 * mz * hs, h(0, -0.2, -0.38 - 0.08 * mz)), 0.1 * hs)
        face = face.su(capsule(h(-0.26, 0.1, -0.37), h(0.26, 0.1, -0.37), 0.088 * hs), 0.05 * hs)
        face = face.ss(sphere(0.095 * hs, h(0.14, 0.02, -0.37)).mirror_x(), 0.03 * hs)
        face = face.ss(ellipsoid(0.035 * hs, 0.03 * hs, 0.05 * hs, h(0.05, -0.12, -0.55 - 0.08 * mz)).mirror_x(), 0.01 * hs)
        face = face.ss(box(0.45 * hs, 0.2 * hs, 0.35 * hs, h(0, -0.5, -0.45)), 0.04 * hs)
        if P["flange"]:
            face = face | (ellipsoid(0.25 * P["flange"] * hs, 0.42 * P["flange"] * hs, 0.1 * hs, h(0.38 + 0.15 * P["flange"], -0.02, -0.12)).round(0.012 * s).mirror_x())
    H.piece("HeadP", "Head", hd, col="primary", mat="skin", tris=2200, res=136, role="head")
    H.piece("Face", "Head", face, col=P["face"] if P["snout"] != "lemur" else "white", mat="skin", tris=1000, role="face", pri=1.25)
    H.bone("Jaw", "Head", jb)
    H.piece("JawP", "Jaw", jaw, col=P["face"] if P["snout"] != "lemur" else "white", mat="skin", tris=500, role="jaw", pri=1.3)
    H.prim("Mouth", "Head", "Ellipsoid", (0.36 * hs, 0.08 * hs, 0.4 * hs), h(0, -0.28, -0.32) if P["snout"] != "lemur" else h(0, -0.14, -0.45 * mz),
           col="mouth", mat="hard", role="mouth", pri=2.4)
    fang = round_cone(h(0.1, -0.27, -0.46), h(0.1, -0.37, -0.47), 0.03 * hs, 0.008 * hs) if P["snout"] != "lemur" else round_cone(h(0.06, -0.12, -0.62 * mz), h(0.06, -0.2, -0.62 * mz), 0.025 * hs, 0.006 * hs)
    H.mpiece("Fang#", "Head", fang, col="tooth", mat="hard", tris=150, role="tooth", pri=2.2, ao=False, smooth=2)
    x, y, z = eye_p
    d = np.array(look, float)
    d /= np.linalg.norm(d)
    H.mprim("Eye#", "Head", "Ball", (er * 2,) * 3, (x, y, z), col=P["eye_col"], mat="hard", role="eye", pri=1.3)
    H.mprim("Pupil#", "Head", "Ball", (er * 1.2,) * 3, (x + d[0] * er * 0.5, y, z + d[2] * er * 0.5), col="pupil", mat="hard", role="pupil", pri=1.4)
    H.mprim("Shine#", "Head", "Ball", (er * 0.4,) * 3, (x + d[0] * er * 0.85 + er * 0.1, y + er * 0.35, z + d[2] * er * 0.85), col="shine", mat="hard", role="shine", pri=2.5)
    if P["snout"] == "lemur":
        H.mprim("EyePatch#", "Head", "Ellipsoid", (0.2 * hs, 0.22 * hs, 0.08 * hs), (x + 0.01, y - 0.01, z + 0.05 * hs), rot=(0, 0.3, 0), col="black", mat="skin", role="face", pri=1.27)
    # ------------------------------------------------------------------ tail
    tail = []
    if P["tail"]:
        kind = P["tail"]
        root = v(0, hipY + 0.15, 0.95)
        if kind == "monkey":
            ds, ln, rad = [(0, -0.3, 1), (0, 0.6, 1), (0, 1, 0.1)], [0.75, 0.7, 0.55], [0.08, 0.07, 0.06, 0.04]
        else:  # lemur: long, thick, held up in an S
            ds, ln, rad = [(0, 0.3, 1), (0, 1, 0.5), (0, 1, -0.4)], [0.8, 0.8, 0.75], [0.1, 0.13, 0.13, 0.07]
        pts = [root]
        for dd, L in zip(ds, ln):
            dd = A(*dd)
            pts.append(pts[-1] + dd / np.linalg.norm(dd) * L * s)
        for i in range(3):
            nm = f"Tail{i + 1}"
            H.bone(nm, "Body" if i == 0 else f"Tail{i}", T(pts[i]))
            tail.append(nm)
            a = pts[i] - (pts[i + 1] - pts[i]) * 0.12
            sg = round_cone(T(a), T(pts[i + 1]), rad[i] * s, rad[i + 1] * s)
            if kind == "monkey" and i == 2:
                sg = sg | tube([T(pts[3]), T(pts[3] + v(0, 0.1, -0.25)), T(pts[3] + v(0, -0.12, -0.3))], [rad[3] * s, rad[3] * s, 0.035 * s], k=0.02)
            pat = stripes(lambda Q, o=root: np.linalg.norm(Q - o, axis=1) / s, 4.2, width=0.45, depth=0.88) if kind == "lemur" else None
            H.piece(f"TailP{i + 1}", nm, furry(sg, 0.6, 10 + i), col="primary" if kind == "monkey" else "white", mat="skin", tris=500, role="tail", pri=1.5 + 0.1 * i, pattern=pat)
    # ------------------------------------------------------------------ rig / motion
    H.socket("mouth", h(0, -0.3, -0.55), "Jaw")
    H.socket("head", h(0, 0.6, 0), "Head")
    height = float(hc[1] + 0.5 * hs)
    legs = [("HipBR", "KneeBR", "AnkleBR"), ("HipBL", "KneeBL", "AnkleBL")]
    arms = [("ShoulderFR", "ElbowFR", "WristFR", 1), ("ShoulderFL", "ElbowFL", "WristFL", -1)]
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": tail,
                  "legs": [{"hip": "ShoulderFR", "knee": "ElbowFR", "phase": 0.75, "side": 1}, {"hip": "ShoulderFL", "knee": "ElbowFL", "phase": 0.25, "side": -1},
                           {"hip": "HipBR", "knee": "KneeBR", "phase": 0.5, "side": 1}, {"hip": "HipBL", "knee": "KneeBL", "phase": 0.0, "side": -1}]})
    mm.knuckle(H, legs, arms, neck="Neck", head="Head", jaw="Jaw", tail=tail, height=height, walk=1.15 if P["hand"] == "knuckle" else 0.75,
               stride=0.34 if P["hand"] == "knuckle" else 0.42, beat=P["beat"])
    return H


@hero("gorilla", "apes")
def gorilla():
    return _ape("gorilla", s=1.15, G=1.25, AL=1.12, LL=0.85, HS=0.95, muzzle=0.85, crest=1.0, ears=0.6, fur=0.035, silver=True,
                face=[0.16, 0.15, 0.16], chest=1.1, preview={"primary": "#2A2A2E", "secondary": "#64646C", "iris": "#4A2E1A"})


@hero("chimpanzee", "apes")
def chimpanzee():
    return _ape("chimpanzee", s=0.9, G=0.9, AL=1.05, LL=1.0, HS=1.1, muzzle=1.15, crest=0.0, ears=1.6, fur=0.03,
                face=[0.85, 0.72, 0.6], beat=False, preview={"primary": "#2E2622", "secondary": "#D8B898", "iris": "#5A3A1A"})


@hero("orangutan", "apes")
def orangutan():
    return _ape("orangutan", s=1.05, G=1.15, AL=1.25, LL=0.8, HS=1.05, muzzle=0.9, crest=0.2, ears=0.5, flange=1.0, fur=0.045, shag=1.0,
                face=[0.32, 0.3, 0.32], preview={"primary": "#C0582A", "secondary": "#E89A5A", "iris": "#4A2E1A"})


@hero("monkey", "apes")
def monkey():
    return _ape("monkey", s=0.65, G=0.85, AL=0.8, LL=1.05, HS=1.35, muzzle=0.9, ears=1.4, fur=0.025, tail="monkey", hand="palm",
                face=[0.9, 0.76, 0.62], beat=False, preview={"primary": "#8A5A30", "secondary": "#E8C8A0", "iris": "#4A2E1A"})


@hero("lemur", "apes")
def lemur():
    return _ape("lemur", s=0.62, G=0.8, AL=0.78, LL=1.1, HS=1.25, muzzle=1.1, ears=1.0, fur=0.03, tail="lemur", hand="palm", snout="lemur",
                face="white", beat=False, eye_col=[0.95, 0.55, 0.1], preview={"primary": "#9A9690", "secondary": "#1E1A18", "iris": "#F09020"})


