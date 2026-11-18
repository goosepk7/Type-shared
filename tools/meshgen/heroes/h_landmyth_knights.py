"""Landmyth insect folk: bee knight, beetle knight, dragonfly knight (armoured insect humanoids on the monsters-kit
body with chitin heads, compound eyes, mandibles, antennae, an abdomen behind and wings / elytra), drider (a humanoid
torso on a spider body), alien queen (a crested hive queen with scythe arms and an egg-sac abdomen) and face grabber
(a domed, crab-legged critter with grabbing hooks and a barbed tail). All original designs.

Part of the landmyth family (see h_landmyth.py for the shared helpers and the MAP). NOTE: build.py hashes only this
file + kit.py: after a change in h_landmyth.py helpers / h_monsters / mythic_geo rebuild with --force.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF
from kit import Hero, hero, stripes, spots, gradient, combine
import motion_bugs as mb
import motion_monsters as mm
import motion_landmyth as ml
import mythic_geo as mg
import h_monsters as HM
from h_landmyth import A, T, nrm, hard, human_ctx, human_head

GLASS = "wingGlass"


def glass_wing(H, bone, parent, root, poly, u, v, s=1.0, name="Wing#", tris=400):
    """Glassy membrane wing (right side; mirrored) on its own bone: a thin plate along poly in the (u, v) plane, with a
    darker leading-edge vein."""
    H.mbone(bone, parent, T(root))
    w = HM.plate([(x * s, y * s) for x, y in poly], T(root), u, v, 0.018 * s)
    lead = tube([T(A(*root) + A(*u) * poly[i][0] * s + nrm(A(*v) - (A(*v) @ nrm(A(*u))) * nrm(A(*u))) * poly[i][1] * s) for i in range(0, 3)], [0.035 * s, 0.03 * s, 0.02 * s], k=0.02)
    root_ = A(*root)

    def veins(P):
        d = np.linalg.norm(P - root_, axis=1)
        return 0.75 + 0.25 * np.abs(np.sin(d * 9.0 / s))
    H.mpiece(name, bone, w | lead, col=GLASS, mat="glass", tr=0.4, tris=tris, role="wing", pri=1.5, ao=False, smooth=2, pattern=veins)


def insect_head(H, C, kind, s, col="primary"):
    """Chitin insect head on the Head bone: compound eyes (own piece), mandibles on Jaw, antennae; beetle gets a horn."""
    hc, hs = C["hc"], C["hs"]

    def h(x, y, z):
        return T(hc + A(x, y, z) * hs)

    hd = ellipsoid(0.36 * hs, 0.42 * hs, 0.4 * hs, h(0, 0.05, 0.0))
    hd = hd.su(ellipsoid(0.24 * hs, 0.25 * hs, 0.22 * hs, h(0, -0.2, -0.25)), 0.1)   # clypeus / face plate
    if kind == "beetle":
        hd = hd.su(mg.curved_horn([A(*h(0, 0.0, -0.3)), A(*h(0, 0.35, -0.65)), A(*h(0, 0.85, -0.7)), A(*h(0, 1.15, -0.45))], 0.16 * hs, 0.03 * hs), 0.06)
        hd = hd.su(round_cone(h(0, 0.38, 0.05), h(0, 0.62, -0.18), 0.12 * hs, 0.05 * hs), 0.05)
    eyes_r = {"bee": (0.2, 0.32, 0.2), "dragonfly": (0.32, 0.34, 0.3), "beetle": (0.12, 0.14, 0.12)}[kind]
    ex = {"bee": 0.3, "dragonfly": 0.24, "beetle": 0.3}[kind]
    ey = {"bee": 0.05, "dragonfly": 0.22, "beetle": 0.05}[kind]
    hd = hd.ss(ellipsoid(*(r * hs * 0.85 for r in eyes_r), h(ex, ey, -0.12)).mirror_x(), 0.03)
    H.piece("HeadP", "Head", hd, col=col, mat="hard", tris=1300, role="head",
            pattern=(lambda Q: np.where(Q[:, 1] > hc[1] + 0.25 * hs, 0.8, 1.0)) if kind == "beetle" else None)
    eye = ellipsoid(*(r * hs for r in eyes_r), h(ex, ey, -0.12)).noise(0.006 * hs, 60 / hs, 2)
    H.mpiece("CompoundEye#", "Head", eye, col="bugEye", mat="glass", tris=500, role="eye", pri=1.2, ao=False)
    H.bone("Jaw", "Head", h(0, -0.3, -0.25))
    md = mg.curved_horn([A(*h(0.14, -0.32, -0.3)), A(*h(0.2, -0.4, -0.45)), A(*h(0.1, -0.45, -0.6)), A(*h(0.02, -0.43, -0.62))], 0.05 * hs, 0.012 * hs)
    H.mpiece("Mandible#", "Jaw", md, col="dark", mat="hard", tris=300, role="jaw", pri=1.5)
    if kind == "bee":
        pts = [h(0.1, 0.35, -0.3), h(0.2, 0.7, -0.45), h(0.32, 0.95, -0.35), h(0.42, 1.1, -0.48)]
        r = [0.035, 0.03, 0.03, 0.045]
    elif kind == "dragonfly":
        pts = [h(0.08, 0.3, -0.32), h(0.14, 0.45, -0.45), h(0.2, 0.55, -0.52)]
        r = [0.025, 0.02, 0.012]
    else:
        pts = [h(0.2, 0.15, -0.35), h(0.35, 0.3, -0.55), h(0.5, 0.4, -0.6), h(0.58, 0.5, -0.62)]
        r = [0.03, 0.028, 0.035, 0.06]
    H.mpiece("Antenna#", "Head", tube(pts, [x * hs * 1.6 for x in r], k=0.02), col="dark", mat="hard", tris=300, role="antenna", pri=1.6)


def _knight(hid, kind, P, preview):
    P = HM._P(**P)
    P["preview"] = preview
    H, C = HM._rig(hid, P, plan="Insect")
    v, s = C["v"], C["s"]
    rib, pel = HM._torso(H, C, P, tris=1400)
    HM._arms(H, C, P, upper_tris=550)
    HM._legs(H, C, P, foot_col="steel")
    insect_head(H, C, kind, s, col="primary")
    # armour: breastplate shell, pauldrons, faulds
    bp = rib.round(0.05 * s) & half_space(1, -1, float(C["waist"][1] - 0.2 * s)) & half_space(2, 1, float(C["chest"][2] + 0.05 * s))
    bp = bp | (rib.round(0.05 * s) & half_space(1, -1, float(C["chest"][1] + 0.1 * s)) & half_space(1, 1, float(C["Sh"][1] + 0.1 * s)))
    bp = bp.su(capsule(T(C["chest"] + v(-0.02, 0.2, -0.32 * P["depth"] - 0.08)), T(C["chest"] + v(0.02, -0.45, -0.3 * P["depth"] - 0.06)), 0.04 * s), 0.03)
    H.piece("Breastplate", "Spine", bp, col="steel", mat="metal", tris=1200, role="armor", pri=1.1)
    sh = C["Sh"]
    pd = ellipsoid(0.3 * s, 0.22 * s, 0.32 * s, T(sh + v(0.06, 0.08, 0))).shell(0.035 * s) & half_space(1, -1, float(sh[1] - 0.08 * s))
    pd = pd | (ellipsoid(0.27 * s, 0.19 * s, 0.29 * s, T(sh + v(0.07, -0.05, 0))).shell(0.03 * s) & half_space(1, -1, float(sh[1] - 0.2 * s)) & half_space(1, 1, float(sh[1] - 0.02 * s)))
    H.mpiece("Pauldron#", "Shoulder#", pd, col="secondary" if kind != "beetle" else "steel", mat="metal", tris=600, role="armor", pri=1.3)
    HM._belt(H, C, P, pel, col=HM.LEATHER, buckle=True, loin="secondary")
    # abdomen behind (insect tail end)
    root = A(0, C["hipY"] + 0.1 * s, 0.35 * s)
    H.bone("Abdomen", "Body", T(root))
    wings = []
    if kind == "bee":
        ab = ellipsoid(0.48 * s, 0.5 * s, 0.7 * s, T(root + v(0, -0.15, 0.6))).su(sphere(0.2 * s, T(root)), 0.15)
        ab = ab | round_cone(T(root + v(0, -0.45, 1.15)), T(root + v(0, -0.62, 1.48)), 0.07 * s, 0.01 * s)
        pat = stripes(lambda Q: Q[:, 2] - 0.3 * Q[:, 1], 3.4, width=0.45, depth=0.85, seed=1)
        H.piece("AbdomenP", "Abdomen", ab.noise(0.01 * s, 25 / s, 3), col="primary", mat="cloth", tris=1100, role="body", pri=1.2, pattern=pat)
        ch = C["chest"]
        glass_wing(H, "Wing#", "Spine", T(ch + v(0.18, 0.3, 0.3)), [(0, 0), (0.6, 0.16), (1.35, 0.24), (1.5, 0.0), (1.2, -0.3), (0.4, -0.24)], (1, 0.45, 0.6), (0, 0.6, -0.4), s)
        wings = [("WingR", None, 1), ("WingL", None, -1)]
    elif kind == "dragonfly":
        pts = [root, root + v(0, 0.05, 0.9), root + v(0, 0.2, 1.8), root + v(0, 0.45, 2.6)]
        H.bone("Abdomen2", "Abdomen", T(pts[1]))
        H.bone("Abdomen3", "Abdomen2", T(pts[2]))
        segpat = stripes(lambda Q: Q[:, 2], 3.0, width=0.2, depth=0.45, seed=2)
        H.piece("AbdomenP", "Abdomen", round_cone(T(pts[0] - v(0, 0, 0.15)), T(pts[1]), 0.17 * s, 0.11 * s), col="primary", mat="hard", tris=500, role="tail", pri=1.2, pattern=segpat)
        H.piece("Abdomen2P", "Abdomen2", round_cone(T(pts[1]), T(pts[2]), 0.11 * s, 0.09 * s), col="primary", mat="hard", tris=450, role="tail", pri=1.3, pattern=segpat)
        tip = round_cone(T(pts[2]), T(pts[3]), 0.09 * s, 0.07 * s)
        for sx in (1, -1):
            tip = tip | round_cone(T(pts[3]), T(pts[3] + v(0.1 * sx, 0.05, 0.25)), 0.04 * s, 0.01 * s)
        H.piece("Abdomen3P", "Abdomen3", tip, col="primary", mat="hard", tris=450, role="tail", pri=1.4, pattern=segpat)
        ch = C["chest"]
        long = [(0, 0), (0.6, 0.1), (1.6, 0.14), (2.05, 0.05), (2.0, -0.15), (1.2, -0.2), (0.3, -0.12)]
        glass_wing(H, "Wing#", "Spine", T(ch + v(0.15, 0.32, 0.25)), long, (1, 0.12, -0.25), (0, 0.15, -1), s)
        glass_wing(H, "HindWing#", "Spine", T(ch + v(0.15, 0.28, 0.45)), long, (1, 0.08, 0.35), (0, 0.15, -1), s, name="HindWing#")
        wings = [("WingR", None, 1), ("WingL", None, -1), ("HindWingR", None, 1), ("HindWingL", None, -1)]
    else:  # beetle: elytra shell on the back + a short armoured abdomen
        ch = C["chest"]
        ab = ellipsoid(0.55 * s, 0.5 * s, 0.6 * s, T(root + v(0, -0.1, 0.4)))
        H.piece("AbdomenP", "Abdomen", ab, col="dark", mat="hard", tris=700, role="body", pri=1.2,
                pattern=stripes(lambda Q: Q[:, 2], 4.0, width=0.2, depth=0.4))
        for sx, nm in ((1, "R"), (-1, "L")):
            pass
        el = ellipsoid(0.42 * s, 1.15 * s, 0.32 * s, T(ch + v(0.24, -0.35, 0.42))).shell(0.05 * s) & half_space(2, -1, float(ch[2] + 0.3 * s))
        el = el & half_space(0, -1, 0.012 * s)
        H.mbone("Elytron#", "Spine", T(ch + v(0.05, 0.35, 0.4)))
        H.mpiece("Elytron#", "Elytron#", el, col="primary", mat="hard", tris=900, role="wing", pri=1.15,
                 pattern=stripes(lambda Q: np.abs(Q[:, 0]), 6.0, width=0.12, depth=0.2))
        wings = [("ElytronR", None, 1), ("ElytronL", None, -1)]
    # weapon + shield
    P["wscale"] = 1.1 * s
    if kind == "beetle":
        HM._weapon(H, C, P, "axe")
        HM._shield(H, C, P, col="secondary", rim="steel")
    elif kind == "bee":
        HM._weapon(H, C, P, "spear")
        g = C["grip"].copy()
        g[0] = -g[0]
        c = g + A(-0.12 * s, 0.0, 0.0)
        hexs = cylinder(0.42 * s, 0.035 * s, axis=0, rr=0.015 * s).at(*T(c))
        hexs = hexs.su(sphere(0.1 * s, T(c + A(-0.05 * s, 0, 0))), 0.03 * s)
        H.piece("Shield", "HandL", hexs, col="secondary", mat="metal", tris=500, role="shield", pri=1.4,
                pattern=lambda Q, c=c: 1 - 0.25 * (np.abs(np.sin((Q[:, 1] - c[1]) * 18) * np.sin((Q[:, 2] - c[2]) * 18)) > 0.85))
    else:
        HM._weapon(H, C, P, "spear")
    return H, C, wings


def _flyer_knight(H, C, P, wings, rate):
    legs, arms, height = HM._finish(H, C, P)
    H.rig["gait"] = "buzz"
    mm.hoverer(H, wings, arms=arms, legs=[(a, b, c, 1 if i == 0 else -1) for i, (a, b, c, _) in enumerate(legs)], spine="Spine", head="Head",
               jaw="Jaw", height=height, rate=rate, amp=0.5, weapon_arm="ShoulderR")
    H.rig["gait"] = "buzz"


@hero("bee knight", "landmyth")
def bee_knight():
    P = dict(s=0.8, leg=0.85, torso=0.95, W=0.9, arm=0.95, armT=0.8, legT=0.85, head=1.2, muscle=0.4, hands="fist", feet="boot",
             weapon="spear", gait="buzz", tags=["insect", "warrior", "flying"])
    H, C, wings = _knight("bee knight", "bee", P, {"primary": "#F2C21A", "secondary": "#1C1F2A", "dark": "#15151A", "steel": "#9AA4AE", "bugEye": "#20202A", "wingGlass": "#D8ECF6"})
    _flyer_knight(H, C, HM._P(**P), wings, 4.0)
    return H


@hero("dragonfly knight", "landmyth")
def dragonfly_knight():
    P = dict(s=0.85, leg=0.95, torso=0.95, W=0.75, arm=1.0, armT=0.65, legT=0.7, head=1.15, muscle=0.2, hands="fist", feet="boot",
             weapon="spear", gait="buzz", tags=["insect", "warrior", "flying"])
    H, C, wings = _knight("dragonfly knight", "dragonfly", P, {"primary": "#1FB5CC", "secondary": "#1E3A8A", "dark": "#14202A", "steel": "#A9B8C4", "bugEye": "#1D4ED8", "wingGlass": "#D8ECF6"})
    _flyer_knight(H, C, HM._P(**P), wings, 3.0)
    return H


@hero("beetle knight", "landmyth")
def beetle_knight():
    P = dict(s=0.95, leg=0.85, torso=1.05, W=1.3, arm=1.0, armT=1.2, legT=1.2, head=1.0, hunch=0.1, muscle=0.8, depth=1.1, hands="fist",
             feet="boot", weapon="axe", attack="slam", stride=0.42, walk=1.15, stomp=0.5, tags=["insect", "warrior"])
    H, C, wings = _knight("beetle knight", "beetle", P, {"primary": "#1F3B8A", "secondary": "#15803D", "dark": "#141820", "steel": "#8E99A6", "bugEye": "#C8A040", "wingGlass": "#D8ECF6"})
    P2 = HM._P(**P)
    HM._animate_biped(H, C, P2)
    return H


# ================================================================================================ drider
def spider_legs(H, body_c, specs, s=1.0, col="primary", parent="Body", r0=0.19):
    """Eight legs: specs = [(hip xyz right side, knee, tip)] -> two pieces per leg (femur, tibia+tarsus)."""
    legs = []
    for i, (hip, knee, tip) in enumerate(specs):
        hip, knee, tip = A(*hip), A(*knee), A(*tip)
        b0, b1 = f"Leg{i}#", f"Knee{i}#"
        H.mbone(b0, parent, T(hip))
        H.mbone(b1, b0, T(knee))
        fm = round_cone(T(hip), T(knee), r0 * s, r0 * 0.8 * s).su(sphere(r0 * 1.15 * s, T(hip)), 0.04).su(sphere(r0 * 0.9 * s, T(knee)), 0.03)
        mid = knee + (tip - knee) * 0.55 + A(0, 0.08, 0) * s
        tb = tube([T(knee), T(mid), T(tip + A(0, 0.03, 0))], [r0 * 0.8 * s, r0 * 0.55 * s, r0 * 0.3 * s], k=0.02)
        tb = tb.su(sphere(r0 * 0.6 * s, T(mid)), 0.03) & plane((0, -1, 0), 0.0)
        H.mpiece(f"Femur{i}#", b0, fm, col=col, mat="hard", tris=300, role="limb", pri=1.3)
        H.mpiece(f"Tibia{i}#", b1, tb, col=col, mat="hard", tris=350, role="limb", pri=1.35,
                 pattern=lambda Q, k=knee: np.where(np.linalg.norm(Q - k, axis=1) < 0.18 * s, 0.75, 1.0))
        legs.append((b0, b1))
    out = []
    phases = [0.0, 0.5, 0.0, 0.5]
    for i, (b0, b1) in enumerate(legs):
        for side, ch in ((1, "R"), (-1, "L")):
            ph = (phases[i] + (0.0 if side > 0 else 0.5)) % 1.0
            out.append({"hip": b0.replace("#", ch), "knee": b1.replace("#", ch), "foot": None, "side": side, "phase": ph,
                        "front": 1 if i == 0 else (-1 if i == 3 else 0)})
    return out


def spider_specs(c, spread=1.0, h=1.0, s=1.0):
    cx, cy, cz = c
    out = []
    for i, ang in enumerate((55, 20, -15, -50)):
        a = math.radians(ang)
        d = A(math.cos(a), 0, -math.sin(a))
        hip = A(cx, cy, cz) + d * 0.55 * s + A(0, 0, 0)
        knee = hip + d * 1.05 * spread * s + A(0, 0.9 * h * s, 0)
        tip = hip + d * 2.2 * spread * s
        tip[1] = 0.0
        out.append((hip, knee, tip))
    return out


@hero("drider", "landmyth")
def drider():
    s = 1.0
    H = Hero("drider", plan="Spider", gait="scuttle", tags=["spider", "spooky", "myth"])
    H.preview = {"primary": "#24201E", "secondary": "#7C3AED", "skin": "#9C8FB0", "hair": "#E6E2F0", "steel": "#A8B0BA"}
    cc = A(0, 1.45, 0.2)
    H.body(T(cc))
    ceph = ellipsoid(0.75, 0.5, 0.85, T(cc)).su(ellipsoid(0.55, 0.45, 0.5, T(cc + A(0, 0.25, -0.65))), 0.25)
    H.bone("Abdomen", "Body", T(cc + A(0, 0.1, 0.75)))
    abd = ellipsoid(0.95, 0.85, 1.15, T(cc + A(0, 0.4, 1.85))).su(sphere(0.35, T(cc + A(0, 0.1, 0.8))), 0.2)
    abd = abd | round_cone(T(cc + A(0, 0.1, 2.9)), T(cc + A(0, -0.05, 3.08)), 0.12, 0.05)
    mark = lambda Q: 1.0 - 0.55 * ((np.abs(Q[:, 0]) < 0.12 + 0.25 * np.abs(np.sin((Q[:, 2] - cc[2]) * 3.0))) & (Q[:, 1] > cc[1] + 0.9))
    H.piece("AbdomenP", "Abdomen", abd.noise(0.01, 18, 2), col="primary", mat="hard", tris=1600, res=128, role="body", pattern=mark)
    # humanoid torso rising from the front of the cephalothorax
    P, C = human_ctx(s=s, hipY=1.75, torso=0.95, W=0.85, head=0.95, armT=0.8, muscle=0.45, depth=0.85, skin="skin", nopelvis=True,
                     hands="fist", face=dict(ears="elf", es=1.1, brow=0.6, angry=0.6, nose="human", ns=0.85, cheek=0.6, iris=[0.75, 0.2, 0.9], sclera=None, eye=1.1))
    shift = A(0, 0, -0.85)
    for k in ("waist", "chest", "Sh", "neckB", "headP", "hc", "Hip"):
        C[k] = C[k] + shift
    H.bone("Spine", "Body", T(C["waist"]))
    H.bone("Head", "Spine", T(C["headP"]))
    C["El"] = C["Sh"] + A(0.14, -0.8, 0.1)
    C["Wr"] = C["El"] + A(0.03, -0.72, -0.15)
    H.mbone("Shoulder#", "Spine", T(C["Sh"]))
    H.mbone("Elbow#", "Shoulder#", T(C["El"]))
    H.mbone("Hand#", "Elbow#", T(C["Wr"]))
    rib, _ = HM._torso(H, C, P, tris=1600)
    waist = round_cone(T(cc + A(0, 0.2, -0.6)), T(C["waist"] + A(0, 0.1, 0)), 0.42, 0.34)
    H.piece("Ceph", "Body", ceph.su(waist, 0.15), col="primary", mat="hard", tris=1400, role="body",
            pattern=lambda Q: np.where(Q[:, 1] > cc[1] + 0.55, 1.0, 0.85))
    HM._arms(H, C, P, upper_tris=550)
    human_head(H, C, P, hair="long", hair_col="hair")
    # chitin armour pieces over the chest and shoulders
    bp = rib.round(0.04) & half_space(1, -1, float(C["chest"][1] - 0.15)) & half_space(1, 1, float(C["Sh"][1] + 0.12))
    H.piece("Chitin", "Spine", bp, col="secondary", mat="hard", tris=900, role="armor", pri=1.2)
    P["wscale"] = 1.0
    HM._weapon(H, C, P, "sword")
    legs = spider_legs(H, cc, spider_specs(cc, 1.0, 1.0, s), s=s, col="primary")
    hc, hs = C["hc"], C["hs"]
    H.socket("mouth", T(hc + A(0, -0.25, -0.5) * hs), "Jaw")
    H.socket("head", T(hc + A(0, 0.6, 0) * hs), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": [], "legs": [{"hip": L["hip"], "knee": L["knee"], "phase": L["phase"], "side": L["side"]} for L in legs]})
    mb.walker(H, legs, head="Head", abd="Abdomen", period=0.8, stride=0.28, lift=0.3, height=2.5, attack="strike",
              strike=[("ShoulderR", "ElbowR", "HandR", 1)])
    return H


# ================================================================================================ alien queen
@hero("alien queen", "landmyth")
def alien_queen():
    s = 1.0
    H = Hero("alien queen", plan="Insect", gait="scuttle", tags=["alien", "insect", "boss"])
    H.preview = {"primary": "#24221F", "secondary": "#86C232", "dark": "#121210", "tooth": "#D8D2C0"}
    c = A(0, 2.4, 0.0)
    H.body(T(c))
    # upright thorax
    H.bone("Thorax", "Body", T(c + A(0, 0.4, -0.4)))
    th = ellipsoid(0.75, 1.0, 0.65, T(c + A(0, 0.75, -0.45))).su(ellipsoid(0.62, 0.5, 0.8, T(c + A(0, 0.0, 0.1))), 0.3)
    for i in range(4):   # segment ridges across the back
        th = th.su(torus(0.6 - 0.05 * i, 0.06, axis=1).scale3(1, 1, 0.9).rot(-25, 0, 0).at(*T(c + A(0, 0.1 + 0.32 * i, -0.2 - 0.12 * i))), 0.05)
    H.piece("ThoraxP", "Thorax", th.noise(0.012, 9, 3), col="primary", mat="hard", tris=1800, res=128, role="body",
            pattern=stripes(lambda Q: Q[:, 1] * 1.0, 3.0, width=0.2, depth=0.3))
    # head with a wide fan crest (a frilled half-disc of spines) and four eyes
    hp = c + A(0, 1.75, -0.85)
    H.bone("Head", "Thorax", T(hp))
    hd = ellipsoid(0.42, 0.38, 0.6, T(hp + A(0, 0.05, -0.25))).su(ellipsoid(0.3, 0.25, 0.35, T(hp + A(0, -0.12, -0.7))), 0.15)
    crest = None
    for i in range(9):
        a = math.radians(-80 + i * 20)
        d = A(math.sin(a), math.cos(a) * 0.9 + 0.3, 0.55)
        sp = round_cone(T(hp + A(0, 0.15, 0.15)), T(hp + A(0, 0.15, 0.15) + nrm(d) * (1.35 - 0.25 * abs(math.sin(a)))), 0.12, 0.02)
        crest = sp if crest is None else crest | sp
    web = HM.plate([(-1.25, 0.2), (-0.9, 1.0), (-0.3, 1.35), (0.3, 1.35), (0.9, 1.0), (1.25, 0.2), (0, 0.0)], T(hp + A(0, 0.15, 0.25)), (1, 0, 0), (0, 0.85, 0.5), 0.03)
    H.piece("HeadP", "Head", hd.noise(0.008, 14, 4), col="primary", mat="hard", tris=1100, role="head")
    H.piece("Crest", "Head", (crest | web).su(sphere(0.2, T(hp + A(0, 0.15, 0.2))), 0.08), col="secondary", mat="hard", tris=1300, role="crest", pri=1.2,
            pattern=lambda Q: 0.55 + 0.45 * np.clip(np.linalg.norm(Q - (hp + A(0, 0.15, 0.2)), axis=1) / 1.3, 0, 1))
    eyes = [(hp + A(sx * 0.27, 0.12, -0.45), 0.09) for sx in (1, -1)] + [(hp + A(sx * 0.2, 0.25, -0.3), 0.065) for sx in (1, -1)]
    import h_landmyth_eldritch as LE
    LE.eye_cluster(H, "Head", hp, eyes, col="secondary", pupil="slit")
    # split mandible jaws with drool
    H.mbone("Mand#", "Head", T(hp + A(0.15, -0.2, -0.75)))
    md = mg.curved_horn([hp + A(0.15, -0.2, -0.7), hp + A(0.28, -0.35, -1.0), hp + A(0.15, -0.45, -1.25), hp + A(0.02, -0.4, -1.3)], 0.08, 0.015)
    H.mpiece("Mandible#", "Mand#", md, col="dark", mat="hard", tris=350, role="jaw", pri=1.4)
    dr = hard([round_cone(T(hp + A(dx, -0.35, -0.85)), T(hp + A(dx, -0.75 - 0.1 * i, -0.88)), 0.035, 0.05) for i, dx in enumerate((-0.07, 0.06))])
    H.piece("Drool", "Head", dr, col="secondary", mat="glass", tr=0.25, tris=250, role="detail", pri=2.0, ao=False)
    # scythe arms
    strike = []
    for sx, nm in ((1, "R"), (-1, "L")):
        sh = c + A(sx * 0.6, 1.2, -0.65)
        el = sh + A(sx * 0.35, 0.55, -0.4)
        H.bone("Scythe" + nm, "Thorax", T(sh))
        H.bone("ScytheEl" + nm, "Scythe" + nm, T(el))
        up = round_cone(T(sh), T(el), 0.17, 0.12).su(sphere(0.2, T(sh)), 0.05)
        bl = HM.plate([(0, 0.05), (0.3, 0.12), (1.0, 0.1), (1.55, -0.15), (1.4, -0.05), (0.9, -0.05), (0.2, -0.12)], T(el), T(A(sx * 0.15, -0.65, -0.75)), (0, 0.6, -0.4), 0.035)
        fo = round_cone(T(el), T(el + A(sx * 0.1, -0.6, -0.65)), 0.12, 0.07) | bl
        H.piece("ScytheUp" + nm, "Scythe" + nm, up, col="primary", mat="hard", tris=450, role="limb", pri=1.3, key=f"h_alien queen_scup{'' if sx > 0 else '_l'}")
        H.piece("ScytheBlade" + nm, "ScytheEl" + nm, fo, col="dark", mat="hard", tris=650, role="claw", pri=1.3, key=f"h_alien queen_scbl{'' if sx > 0 else '_l'}")
        strike.append(("Scythe" + nm, "ScytheEl" + nm, None, sx))
    # egg-sac abdomen trailing behind on two bones
    H.bone("Abdomen", "Body", T(c + A(0, 0.0, 0.6)))
    H.bone("Abdomen2", "Abdomen", T(c + A(0, -0.55, 2.3)))
    a1 = round_cone(T(c + A(0, 0.0, 0.4)), T(c + A(0, -0.5, 2.3)), 0.55, 0.85)
    H.piece("AbdomenP", "Abdomen", a1.noise(0.02, 6, 5), col="primary", mat="hard", tris=1100, role="body", pri=1.15,
            pattern=stripes(lambda Q: Q[:, 2], 2.4, width=0.2, depth=0.35))
    a2 = ellipsoid(1.05, 0.95, 1.6, T(c + A(0, -0.9, 3.6))).su(sphere(0.7, T(c + A(0, -0.55, 2.3))), 0.3) & plane((0, -1, 0), -0.0)
    H.piece("EggSac", "Abdomen2", a2.noise(0.03, 4, 6), col="secondary", mat="skin", tris=1400, role="body", pri=1.2,
            pattern=combine(spots(0.45, 0.2, depth=0.35, seed=7), stripes(lambda Q: Q[:, 2], 1.6, width=0.15, depth=0.3)))
    # six walking legs
    specs = []
    for i, ang in enumerate((40, 0, -40)):
        a = math.radians(ang)
        d = A(math.cos(a), 0, -math.sin(a))
        hip = c + A(0.45, -0.2, 0.2 - 0.25 * i) + d * 0.1
        knee = hip + d * 1.2 + A(0, 0.9, 0)
        tip = hip + d * 2.4
        tip[1] = 0.0
        specs.append((hip, knee, tip))
    legs = spider_legs(H, c, specs, s=1.0, col="primary", r0=0.23)
    for L in legs:
        L["phase"] = (0.0 if (L["hip"][3] in "02") == (L["side"] > 0) else 0.5)
    H.socket("mouth", T(hp + A(0, -0.35, -1.1)), "Head")
    H.socket("head", T(hp + A(0, 1.3, 0.3)), "Head")
    H.rig.update({"head": "Head", "tail": ["Abdomen", "Abdomen2"], "legs": [{"hip": L["hip"], "knee": L["knee"], "phase": L["phase"], "side": L["side"]} for L in legs]})
    mb.walker(H, legs, head="Head", abd="Abdomen", mand=[("MandR", 1), ("MandL", -1)], period=0.9, stride=0.24, lift=0.28, height=4.5,
              attack="strike", strike=strike, tail=["Abdomen2"])
    return H


# ================================================================================================ face grabber
@hero("face grabber", "landmyth")
def face_grabber():
    H = Hero("face grabber", plan="Insect", gait="scuttle", tags=["alien", "spooky"])
    H.preview = {"primary": "#CFC6B8", "secondary": "#A16207", "dark": "#4A3A2A"}
    c = A(0, 0.85, 0.0)
    H.body(T(c))
    # a domed, ridged carapace with a flared rim, four eyes on stalk bumps on top
    dome = ellipsoid(1.0, 0.55, 1.1, T(c + A(0, 0.1, 0))) & plane((0, -1, 0), -float(c[1] - 0.05))
    dome = dome.su(torus(0.98, 0.09, axis=1).scale3(1, 1, 1.1).at(*T(c + A(0, 0.08, 0))), 0.05)
    for sx in (1, -1):
        dome = dome.su(capsule(T(c + A(sx * 0.35, 0.55, -0.6)), T(c + A(sx * 0.4, 0.5, 0.7)), 0.07), 0.08)
    for i in range(4):
        x = (-0.27, -0.1, 0.1, 0.27)[i]
        dome = dome.su(sphere(0.12, T(c + A(x, 0.55, -0.62))), 0.06)
    H.piece("Carapace", "Body", dome.noise(0.008, 12, 2), col="primary", mat="hard", tris=1500, role="body",
            pattern=combine(stripes(lambda Q: np.abs(Q[:, 0]), 4.5, width=0.15, depth=0.25), gradient(1, 0.8, 1.5, 0.8, 1.0)))
    under = ellipsoid(0.9, 0.3, 1.0, T(c + A(0, -0.08, 0)))
    for i in range(10):   # ring of feelers around a sucker mouth underneath / at the front
        a = i / 10 * math.tau
        b = c + A(math.cos(a) * 0.28, -0.3, math.sin(a) * 0.28 - 0.35)
        under = under | round_cone(T(b), T(b + A(math.cos(a) * 0.18, -0.2, math.sin(a) * 0.18 - 0.1)), 0.04, 0.012)
    H.piece("Underside", "Body", under, col="secondary", mat="skin", tris=900, role="body", pri=1.2)
    import h_landmyth_eldritch as LE
    LE.eye_cluster(H, "Body", c + A(0, 0.3, -0.3), [(c + A(x, 0.62, -0.68), 0.09) for x in (-0.27, -0.1, 0.1, 0.27)], col="dark", pupil="round")
    # six crab legs
    specs = []
    for i, ang in enumerate((35, 0, -35)):
        a = math.radians(ang)
        d = A(math.cos(a), 0, -math.sin(a))
        hip = c + A(0.7, -0.05, 0.25 - 0.3 * i)
        knee = hip + d * 0.75 + A(0, 0.55, 0)
        tip = hip + d * 1.55
        tip[1] = 0.0
        specs.append((hip, knee, tip))
    legs = spider_legs(H, c, specs, s=1.0, col="primary", r0=0.13)
    for L in legs:
        L["phase"] = (0.0 if (L["hip"][3] in "02") == (L["side"] > 0) else 0.5)
    # two hooked grabbers at the front
    strike = []
    for sx, nm in ((1, "R"), (-1, "L")):
        sh = c + A(sx * 0.45, 0.0, -0.85)
        el = sh + A(sx * 0.3, 0.35, -0.45)
        H.bone("Grab" + nm, "Body", T(sh))
        H.bone("GrabEl" + nm, "Grab" + nm, T(el))
        H.piece("GrabUp" + nm, "Grab" + nm, round_cone(T(sh), T(el), 0.1, 0.075), col="primary", mat="hard", tris=300, role="limb", pri=1.3,
                key=f"h_face grabber_gu{'' if sx > 0 else '_l'}")
        hk = mg.curved_horn([el, el + A(sx * 0.05, 0.1, -0.4), el + A(-sx * 0.05, -0.15, -0.65), el + A(-sx * 0.12, -0.35, -0.55)], 0.075, 0.012)
        H.piece("GrabHook" + nm, "GrabEl" + nm, hk, col="dark", mat="hard", tris=400, role="claw", pri=1.35, key=f"h_face grabber_gh{'' if sx > 0 else '_l'}")
        strike.append(("Grab" + nm, "GrabEl" + nm, None, sx))
    # long segmented tail with a barbed curl
    pts = [c + A(0, 0.0, 0.95), c + A(0, 0.15, 1.85), c + A(0, 0.55, 2.6), c + A(0, 1.25, 2.85)]
    tails = []
    for i in range(3):
        nm = f"Tail{i + 1}"
        H.bone(nm, "Body" if i == 0 else tails[-1], T(pts[i]))
        tails.append(nm)
        sg = round_cone(T(pts[i] - (pts[i + 1] - pts[i]) * 0.15), T(pts[i + 1]), 0.16 - 0.04 * i, 0.12 - 0.04 * i)
        if i == 2:
            sg = sg | mg.curved_horn([pts[3], pts[3] + A(0, 0.25, -0.1), pts[3] + A(0, 0.2, -0.35)], 0.07, 0.01)
        H.piece(f"TailP{i + 1}", nm, sg, col="primary", mat="hard", tris=450, role="tail", pri=1.4 + 0.1 * i,
                pattern=stripes(lambda Q: Q[:, 2] + Q[:, 1], 5.0, width=0.2, depth=0.3))
    H.socket("mouth", T(c + A(0, -0.3, -0.5)), "Body")
    H.socket("head", T(c + A(0, 0.7, 0)), "Body")
    H.rig.update({"head": "Body", "tail": tails, "legs": [{"hip": L["hip"], "knee": L["knee"], "phase": L["phase"], "side": L["side"]} for L in legs]})
    mb.walker(H, legs, period=0.45, stride=0.3, lift=0.3, height=1.2, attack="strike", strike=strike, tail=tails)
    return H
