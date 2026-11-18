"""Humanoid monsters and fantasy folk: goblin, orc, troll, ogre, giant, cyclops, minotaur, satyr, elf, dwarf, gnome,
demon, imp, angel, vampire, werewolf, lizardman, fishman, alien, zombie, mummy, skeleton, yeti, scarecrow, fairy,
centaur, mermaid.

One parametric humanoid: pelvis + chest on a spine (hunch, belly, shoulder width, muscle), three-segment arms and
legs (plantigrade or digitigrade / hooved), hands (fist around a weapon, open, clawed, bony), feet (bare, boot,
clawed, hoof, paw), and a choice of heads (human-like face with brow / nose / ears / jaw / tusks presets, animal
snout heads for bull / wolf / lizard / fish, skull, alien), plus kit: horns, hair, beards, hats, wings (bat, feather,
fairy), tails, cloth (belt, loincloth, tunic, robe, cape) and weapons (club, axe, spear, sword, bow, pitchfork, staff).
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF
from kit import Hero, hero, stripes, spots, gradient, combine
import motion
import motion_monsters as mm

LEATHER = [0.42, 0.27, 0.15]
DLEATHER = [0.28, 0.18, 0.11]
ROPE = [0.62, 0.5, 0.32]
IRON = [0.42, 0.43, 0.46]

CREATURE = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Person", "Plant", "Weather", "Structure"],
            "bp": ["Humanoid", "Giant", "Ghost", "Biped", "Blob", "Quadruped", "Robot", "Cloud", "Orb", "Swarm", "Plant"]}
HUMANOID = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Person", "Plant", "Structure"],
            "bp": ["Humanoid", "Giant", "Ghost", "Biped", "Blob", "Robot", "Orb", "Cloud"]}


def T(a):
    return tuple(float(x) for x in a)


# ------------------------------------------------------------------------------------------------ 2D plates
def poly2d(Q, poly):
    v = np.asarray(poly, float)
    d = ((Q - v[0]) ** 2).sum(1)
    sg = np.ones(len(Q))
    j = len(v) - 1
    for i in range(len(v)):
        e = v[j] - v[i]
        w = Q - v[i]
        b = w - e * np.clip((w @ e) / (e @ e), 0, 1)[:, None]
        d = np.minimum(d, (b * b).sum(1))
        c1 = Q[:, 1] >= v[i][1]
        c2 = Q[:, 1] < v[j][1]
        c3 = e[0] * w[:, 1] > e[1] * w[:, 0]
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        sg = np.where(flip, -sg, sg)
        j = i
    return sg * np.sqrt(d)


def plate(poly, o, u, v, t, bulge=0.0):
    """Thin plate: 2D polygon (in u, v coordinates from origin o) extruded +-t along the normal. bulge cups it."""
    o = np.asarray(o, float)
    u = np.asarray(u, float)
    u = u / np.linalg.norm(u)
    v = np.asarray(v, float)
    v = v - (v @ u) * u
    v = v / np.linalg.norm(v)
    n = np.cross(u, v)
    pv = np.asarray(poly, float)
    cen = pv.mean(0)
    rad = np.max(np.linalg.norm(pv - cen, axis=1))

    def f(p):
        q = p - o
        a = q @ u
        b = q @ v
        c = q @ n
        if bulge:
            r2 = ((a - cen[0]) ** 2 + (b - cen[1]) ** 2) / (rad * rad)
            c = c - bulge * (1 - np.clip(r2, 0, 1))
        d2 = poly2d(np.column_stack([a, b]), pv)
        dz = np.abs(c) - t
        return np.minimum(np.maximum(d2, dz), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(dz, 0) ** 2)

    return SDF(f)


def slab_y(lo, hi):
    return SDF(lambda p: np.maximum(lo - p[:, 1], p[:, 1] - hi))


def curve(p0, p1, p2, n=6):
    """Quadratic bezier points."""
    p0, p1, p2 = (np.asarray(x, float) for x in (p0, p1, p2))
    return [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2 for t in np.linspace(0, 1, n)]


def horn_sdf(pts, r0, r1, k=0.02):
    n = len(pts)
    radii = [r0 + (r1 - r0) * (i / (n - 1)) ** 0.8 for i in range(n)]
    return tube([T(p) for p in pts], radii, k=k)


# ------------------------------------------------------------------------------------------------ parameters
BASE = dict(
    s=1.0, leg=1.0, torso=1.0, W=1.0, arm=1.0, armT=1.0, legT=1.0, head=1.0, hunch=0.0, belly=0.0, neck=1.0,
    hipw=1.0, depth=1.0, muscle=0.5, hand=1.0, foot=1.0,
    skin="primary", skinmat="skin", digi=False,
    hands="open", feet="bare", head_kind="human", face={},
    gait="biped", tags=["monster"], preview={},
    attack="punch", weapon=None, stride=0.5, walk=1.0, lean=0.0, shamble=0.0, arms_out=0.0, stomp=0.0,
    skin_pattern=None, claws=False,
)

FACE = dict(
    cw=1.0, ch=1.0, cd=1.0, jw=1.0, jl=1.0, brow=0.3, angry=0.0, nose="human", ns=1.0, ears="human", es=1.0,
    chin=1.0, cheek=0.5, under=0.0, tusks=0.0, fangs=0.0, teeth=False, eye=1.0, eyesep=1.0, eyey=0.0, iris="iris",
    glow=False, pupil=True, jaw=True, lips=0.0, mouthw=1.0, one_eye=False, sclera="eyeWhite", eyecol=None,
)


class Ctx(dict):
    pass


# ------------------------------------------------------------------------------------------------ skeleton + body
def _rig(hid, P, plan="Biped"):
    H = Hero(hid, plan=plan, gait=P["gait"], tags=P["tags"])
    H.preview = P["preview"]
    s = P["s"]
    LG, TL, W, AL, AT, LT, HS, hu = P["leg"], P["torso"], P["W"], P["arm"], P["armT"], P["legT"], P["head"], P["hunch"]
    bel = P["belly"]

    def v(x, y, z):
        return np.array((x, y, z), float) * s

    C = Ctx(v=v, s=s, P=P)
    footH = 0.3
    hipY = footH + 2.35 * LG
    hipX = 0.34 * W * P["hipw"]
    if P["digi"]:
        Hip = v(hipX, hipY, 0.05)
        Knee = v(hipX * 1.05, footH + 1.45 * LG, -0.32 * LG)
        Ank = v(hipX * 1.05, footH + 0.62 * LG, 0.38 * LG)
    else:
        Hip = v(hipX, hipY, 0.02)
        Knee = v(hipX * 1.02, footH + 1.15 * LG, -0.07)
        Ank = v(hipX * 1.02, footH, 0.06)
    waist = v(0, hipY + 0.55 * TL, 0.02 - 0.12 * hu)
    chest = v(0, hipY + 1.08 * TL, -0.04 - 0.38 * hu)
    shY = hipY + 1.5 * TL - 0.22 * hu
    Sh = v(0.6 * W + 0.12, shY, 0.02 - 0.5 * hu)
    neckB = v(0, shY + 0.06, 0.04 - 0.62 * hu)
    headP = v(0, shY + 0.3 + 0.08 * P["neck"], -0.02 - 0.9 * hu)
    hs = 0.85 * HS * s
    hc = headP + np.array((0, 0.36 * hs, -0.06 * hs))
    elx = max(Sh[0] / s + 0.06, 0.5 * W + 0.17 * AT + 0.3 * bel + 0.1)
    El = v(elx, shY - 1.0 * AL, 0.08 - 0.3 * hu)
    Wr = El + v(0.03, -0.9 * AL, -0.12)
    off = np.asarray(P.get("upper_off", (0, 0, 0)), float) * s
    if off.any():
        waist, chest, Sh, neckB, headP, hc, El, Wr = (x + off for x in (waist, chest, Sh, neckB, headP, hc, El, Wr))
        hipY = hipY + off[1] / s
    C.update(hipY=hipY * s, Hip=Hip, Knee=Knee, Ank=Ank, waist=waist, chest=chest, Sh=Sh, El=El, Wr=Wr, neckB=neckB,
             headP=headP, hc=hc, hs=hs, footH=footH * s)
    H.body(T(np.asarray(P["body_at"], float) * s) if P.get("body_at") else T(v(0, hipY + 0.1, 0.02) + np.array((0, 0, off[2]))))
    H.bone("Spine", "Body", T(waist))
    H.bone("Head", "Spine", T(headP))
    H.mbone("Shoulder#", "Spine", T(Sh))
    H.mbone("Elbow#", "Shoulder#", T(El))
    H.mbone("Hand#", "Elbow#", T(Wr))
    if not P.get("nolegs"):
        H.mbone("Hip#", "Body", T(Hip))
        H.mbone("Knee#", "Hip#", T(Knee))
        H.mbone("Foot#", "Knee#", T(Ank))
    return H, C


def _fur(P, sd, k=1.0):
    w = P.get("wrap")
    if w:
        sd = _wrap(sd, w * P["s"], 13.0 / P["s"])
    f = P.get("fur", 0.0)
    if not f:
        return sd
    return sd.noise(f * k * P["s"], 9.0 / P["s"], 17)


def _wrap_u(p, freq):
    return (p[:, 1] + 0.35 * p[:, 0] + 0.12 * np.sin(p[:, 2] * 5.0)) * freq


def _wrap(sd, amp, freq):
    """Raised, slightly skewed bandage bands with deep grooves between them (mummy wraps)."""
    def f(p):
        d = sd(p)
        u = _wrap_u(p, freq)
        band = np.tanh(4.0 * np.sin(u)) * 0.5 + 0.5
        tear = 0.3 * np.sin(p[:, 0] * 13.0 + p[:, 2] * 11.0) * np.sin(u * 0.5)
        return d - amp * (band + tear)
    return SDF(f)


def _wrap_pat(freq):
    """Colour to match _wrap: the grooves between bands go dusty brown."""
    def f(p):
        band = np.tanh(4.0 * np.sin(_wrap_u(p, freq))) * 0.5 + 0.5
        return 0.62 + 0.38 * band
    return f


def _skinpat(P):
    return P.get("skin_pattern")


def _torso(H, C, P, tris=2300):
    v, s = C["v"], C["s"]
    W, TL, AT, bel, mu, D, hu = P["W"], P["torso"], P["armT"], P["belly"], P["muscle"], P["depth"], P["hunch"]
    ch, wa, Sh, nb, hp = C["chest"], C["waist"], C["Sh"], C["neckB"], C["headP"]
    rib = ellipsoid(0.55 * W * s, 0.6 * TL * s, 0.38 * D * s, T(ch))
    sl, sr = Sh * np.array((-1, 1, 1)), Sh
    rib = rib.su(capsule(T(sl + v(0.12, -0.08, 0.04)), T(sr + v(-0.12, -0.08, 0.04)), 0.24 * AT * s), 0.22)
    pec = ellipsoid(0.27 * W * s, 0.19 * s, 0.14 * s, T(ch + v(0.23 * W, 0.16 * TL, -0.3 * D + 0.04)))
    rib = rib.su(pec.mirror_x(), 0.1 + 0.08 * (1 - mu))
    lat = ellipsoid(0.2 * s, 0.45 * TL * s, 0.26 * s, T(ch + v(0.42 * W, -0.12, 0.08)))
    rib = rib.su(lat.mirror_x(), 0.15)
    scap = ellipsoid(0.22 * W * s, 0.26 * s, 0.12 * s, T(ch + v(0.22 * W, 0.2, 0.3 * D)))
    rib = rib.su(scap.mirror_x(), 0.15)
    ab = ellipsoid((0.43 + 0.22 * bel) * W * s, (0.48 + 0.25 * bel) * TL * s, (0.32 + 0.42 * bel) * D * s, T(wa + v(0, 0.05, -0.04 - 0.28 * bel)))
    rib = rib.su(ab, 0.25)
    if mu > 0.55 and bel < 0.3:
        for i in range(3):
            for sx in (1, -1):
                rib = rib.su(ellipsoid(0.1 * s, 0.075 * s, 0.05 * s, T(wa + v(0.09 * sx * W, 0.32 - i * 0.19, -0.3 * D - 0.02))), 0.05)
    tr = round_cone(T(nb + v(0.1, -0.05, 0.02)), T(sr + v(-0.15, 0.02, 0.05)), 0.17 * W ** 0.5 * s, 0.14 * s)
    rib = rib.su(tr.mirror_x(), 0.12)
    nk = round_cone(T(nb + v(0, -0.15, 0.02)), T(hp + v(0, 0.12, 0.02)), 0.22 * P["neck"] ** 0.3 * W ** 0.5 * s, 0.17 * s)
    rib = rib.su(nk, 0.12)
    rib = rib.su(ellipsoid(0.42 * W * s, 0.3 * s, 0.3 * D * s, T(wa + v(0, -0.32, 0.0))), 0.2)
    H.piece("Chest", "Spine", _fur(P, rib), col=P["skin"], mat=P["skinmat"], tris=tris, res=128, pattern=_skinpat(P))
    if P.get("nopelvis"):
        return rib, None
    # pelvis
    Hp = C["Hip"]
    pel = ellipsoid(0.48 * W * P["hipw"] * s, 0.36 * s, 0.33 * D * s, T(np.array((0, C["hipY"] + 0.1 * s, 0.03 * s))))
    pel = pel.su(ellipsoid(0.24 * W * s, 0.26 * s, 0.2 * s, T(np.array((0.17 * W * s, C["hipY"], 0.18 * s)))).mirror_x(), 0.12)
    pel = pel.su(sphere(0.25 * P["legT"] * s, T(Hp + v(0, 0.02, 0))).mirror_x(), 0.15)
    pel = pel.su(ellipsoid((0.42 + 0.2 * bel) * W * s, 0.3 * s, (0.3 + 0.3 * bel) * D * s, T(wa + v(0, -0.25, -0.02 - 0.15 * bel))), 0.2)
    H.piece("Pelvis", "Body", _fur(P, pel), col=P["skin"], mat=P["skinmat"], tris=1100, pattern=_skinpat(P))
    return rib, pel


def _arms(H, C, P, col=None, upper_tris=650):
    v, s = C["v"], C["s"]
    AT, AL, mu = P["armT"], P["arm"], P["muscle"]
    Sh, El, Wr = C["Sh"], C["El"], C["Wr"]
    col = col or P["skin"]
    up = round_cone(T(Sh + v(0, 0.06, 0)), T(El), 0.2 * AT * s, 0.135 * AT * s)
    up = up.su(ellipsoid(0.23 * AT * s, 0.32 * s, 0.24 * AT * s, T(Sh + v(0.05, -0.12, 0))), 0.12)  # deltoid
    mid = (Sh + El) / 2
    up = up.su(ellipsoid(0.13 * AT * s, 0.28 * AL * s, 0.13 * AT * s * (1 + 0.3 * mu), T(mid + v(0, -0.02, -0.08 * AT))), 0.1)  # biceps
    up = up.su(ellipsoid(0.13 * AT * s, 0.3 * AL * s, 0.13 * AT * s, T(mid + v(0.01, 0.05, 0.09 * AT))), 0.1)  # triceps
    H.mpiece("UpperArm#", "Shoulder#", _fur(P, up), col=col, mat=P["skinmat"], tris=upper_tris, role="limb", pattern=_skinpat(P))
    fo = round_cone(T(El + v(0, 0.04, 0)), T(Wr), 0.135 * AT * s, 0.09 * AT * s)
    fo = fo.su(ellipsoid(0.13 * AT * s, 0.3 * AL * s, 0.13 * AT * s, T(El + (Wr - El) * 0.3 + v(0.02, 0, -0.03))), 0.12)
    H.mpiece("Forearm#", "Elbow#", _fur(P, fo), col=col, mat=P["skinmat"], tris=550, role="limb", pattern=_skinpat(P))
    _hand(H, C, P, col)


def _hand(H, C, P, col):
    v, s = C["v"], C["s"]
    Wr = C["Wr"]
    k = P["hand"] * P["armT"] ** 0.4
    kind = P["hands"]

    def hv(x, y, z):
        return Wr + v(x * k, y * k, z * k)

    if kind == "fist":
        h = round_box(0.085 * k * s, 0.12 * k * s, 0.13 * k * s, 0.06 * k * s, T(hv(0, -0.2, -0.03)))
        h = h.su(capsule(T(hv(-0.02, -0.28, 0.08)), T(hv(-0.02, -0.28, -0.14)), 0.065 * k * s), 0.04)          # knuckle row
        h = h.su(capsule(T(hv(-0.07, -0.16, -0.1)), T(hv(-0.1, -0.24, -0.14)), 0.045 * k * s), 0.03)           # thumb
        h = h.su(round_cone(T(hv(0, 0.04, 0)), T(hv(0, -0.12, -0.02)), 0.085 * k * s, 0.09 * k * s), 0.05)
        C["grip"] = hv(-0.01, -0.2, -0.03)
    elif kind == "bone":
        h = round_box(0.03 * k * s, 0.08 * k * s, 0.09 * k * s, 0.025 * k * s, T(hv(0, -0.1, -0.02)))
        for i, dz in enumerate((-0.08, -0.03, 0.02, 0.07)):
            h = h | tube([T(hv(0, -0.15, dz)), T(hv(-0.01, -0.3, dz - 0.02)), T(hv(-0.05, -0.42, dz - 0.04))], [0.025 * k * s, 0.022 * k * s, 0.018 * k * s], k=0.01)
        h = h | capsule(T(hv(-0.03, -0.08, -0.08)), T(hv(-0.08, -0.2, -0.16)), 0.024 * k * s)
        h = h | sphere(0.05 * k * s, T(hv(0, 0.0, 0)))
        C["grip"] = hv(-0.02, -0.25, -0.02)
    else:  # open / claw
        h = round_box(0.055 * k * s, 0.12 * k * s, 0.12 * k * s, 0.05 * k * s, T(hv(0, -0.14, -0.02)))
        h = h.su(round_cone(T(hv(0, 0.04, 0)), T(hv(0, -0.08, -0.01)), 0.085 * k * s, 0.08 * k * s), 0.05)
        tips = []
        for i, dz in enumerate((-0.09, -0.03, 0.03, 0.09)):
            ln = (0.2, 0.22, 0.2, 0.16)[i]
            a = hv(0, -0.24, dz)
            b = hv(-0.04, -0.24 - ln * 0.6, dz - 0.015)
            c = hv(-0.1, -0.24 - ln, dz - 0.03)
            h = h.su(tube([T(a), T(b), T(c)], [0.04 * k * s, 0.034 * k * s, 0.028 * k * s], k=0.01), 0.025)
            tips.append((c, (c - b) / max(np.linalg.norm(c - b), 1e-6)))
        h = h.su(tube([T(hv(-0.05, -0.1, -0.1)), T(hv(-0.1, -0.18, -0.16)), T(hv(-0.13, -0.25, -0.18))], [0.042 * k * s, 0.035 * k * s, 0.03 * k * s], k=0.01), 0.03)
        if P["claws"]:
            cl = None
            for c, d in tips:
                d = d + np.array((-0.4, -0.3, 0))
                d = d / np.linalg.norm(d)
                one = round_cone(T(c - d * 0.02 * s), T(c + d * 0.17 * k * s), 0.045 * k * s, 0.012 * s)
                cl = one if cl is None else cl | one
            H.mpiece("Claws#", "Hand#", cl, col="claw", mat="hard", tris=300, role="claw", pri=1.8, ao=False)
        C["grip"] = hv(-0.03, -0.22, -0.02)
    H.mpiece("HandP#", "Hand#", h, col=col, mat=P["skinmat"], tris=650, role="hand", pattern=_skinpat(P))


def _legs(H, C, P, col=None, foot_col=None):
    v, s = C["v"], C["s"]
    LT, LG = P["legT"], P["leg"]
    Hp, Kn, An = C["Hip"], C["Knee"], C["Ank"]
    col = col or P["skin"]
    th = round_cone(T(Hp + v(0, 0.14, 0.01)), T(Kn), 0.27 * LT * s, 0.165 * LT * s)
    mid = (Hp + Kn) / 2
    th = th.su(ellipsoid(0.2 * LT * s, 0.5 * LG * s, 0.2 * LT * s, T(mid + v(0.02, 0.05, -0.07))), 0.12)  # quads
    th = th.su(ellipsoid(0.17 * LT * s, 0.45 * LG * s, 0.17 * LT * s, T(mid + v(-0.02, 0.1, 0.1))), 0.12)  # hamstring
    H.mpiece("Thigh#", "Hip#", _fur(P, th), col=col, mat=P["skinmat"], tris=700, role="limb", pattern=_skinpat(P))
    sn = round_cone(T(Kn + v(0, 0.04, 0)), T(An + v(0, 0.06, 0)), 0.165 * LT * s, 0.1 * LT * s)
    if P["digi"]:
        sn = sn.su(ellipsoid(0.15 * LT * s, 0.3 * s, 0.15 * LT * s, T(Kn + (An - Kn) * 0.3 + v(0, 0, 0.06))), 0.1)
    else:
        sn = sn.su(ellipsoid(0.15 * LT * s, 0.38 * LG * s, 0.15 * LT * s, T(Kn + v(0, -0.38 * LG, 0.08))), 0.12)  # calf
        sn = sn.su(sphere(0.12 * LT * s, T(Kn + v(0, 0.02, -0.08))), 0.06)  # kneecap
    H.mpiece("Shin#", "Knee#", _fur(P, sn), col=col, mat=P["skinmat"], tris=600, role="limb", pattern=_skinpat(P))
    _foot(H, C, P, foot_col or col)


def _foot(H, C, P, col):
    v, s = C["v"], C["s"]
    An = C["Ank"]
    k = P["foot"] * P["legT"] ** 0.5
    kind = P["feet"]
    gnd = plane((0, -1, 0), 0.0)
    mat = P["skinmat"]
    if P["digi"]:
        # hock -> toes on the ground in front of it
        toe = np.array((An[0], 0.0, An[2] - 0.45 * s * P["leg"]))
        f = round_cone(T(An + v(0, 0.04, 0)), T(toe + v(0, 0.13 * k, 0.02)), 0.11 * k * s, 0.1 * k * s)
        if kind == "hoof":
            hf = cone(0.15 * k * s, 0.12 * k * s, 0.1 * k * s, axis=1, rr=0.02 * s).at(*T(toe + v(0, 0.1 * k, -0.02)))
            hf = hf.ss(box(0.012 * s, 0.2 * s, 0.12 * s, T(toe + v(0, 0.08, -0.16))), 0.01)
            H.mpiece("Hoof#", "Foot#", hf & gnd, col="hoof", mat="hard", tris=300, role="hoof", pri=1.6)
            f = f.su(ellipsoid(0.13 * k * s, 0.1 * k * s, 0.13 * k * s, T(toe + v(0, 0.24 * k, 0.0))), 0.05)
        else:  # paw / clawed toes
            f = f.su(ellipsoid(0.15 * k * s, 0.1 * k * s, 0.2 * k * s, T(toe + v(0, 0.1 * k, -0.06))), 0.06)
            cl = None
            for dx in (-0.08, 0.0, 0.08):
                f = f.su(sphere(0.07 * k * s, T(toe + v(dx * k, 0.07 * k, -0.24 * k))), 0.04)
                one = round_cone(T(toe + v(dx * k, 0.08 * k, -0.28 * k)), T(toe + v(dx * k * 1.2, 0.01, -0.42 * k)), 0.045 * k * s, 0.012 * s)
                cl = one if cl is None else cl | one
            H.mpiece("ToeClaws#", "Foot#", cl & gnd, col="claw", mat="hard", tris=260, role="claw", pri=1.8, ao=False)
        H.mpiece("FootP#", "Foot#", f & gnd, col=col, mat=mat, tris=600, role="foot", pattern=_skinpat(P))
        return
    heel = An + v(0, -0.13, 0.06)
    if kind == "boot":
        f = round_cone(T(An + v(0, 0.35, 0.02)), T(An + v(0, -0.12, 0.03)), 0.15 * k * s, 0.15 * k * s)
        f = f.su(round_box(0.15 * k * s, 0.13 * s, 0.32 * k * s, 0.1 * s, T(An + v(0, -0.17, -0.18 * k))), 0.1)
        f = f.su(ellipsoid(0.15 * k * s, 0.12 * s, 0.14 * s, T(An + v(0, -0.17, -0.42 * k))), 0.06)
        f = f.su(cylinder(0.185 * k * s, 0.06 * s, rr=0.02 * s).at(*T(An + v(0, 0.33, 0.02))), 0.02)  # cuff
        H.mpiece("Boot#", "Foot#", f & gnd, col=col, mat="cloth", tris=600, role="foot")
        return
    f = sphere(0.12 * k * s, T(heel))
    f = f.su(round_cone(T(An + v(0, 0.06, 0)), T(heel), 0.11 * k * s, 0.11 * k * s), 0.06)
    f = f.su(ellipsoid(0.14 * k * s, 0.1 * s, 0.24 * k * s, T(An + v(0, -0.18, -0.16 * k))), 0.1)
    if kind == "claw":
        cl = None
        for dx, ln in ((-0.09, 0.3), (0.0, 0.36), (0.09, 0.3)):
            a = An + v(dx * k, -0.2, -0.2 * k)
            b = An + v(dx * 1.6 * k, -0.24, -(0.2 + ln) * k)
            f = f.su(round_cone(T(a), T(b), 0.07 * k * s, 0.055 * k * s), 0.05)
            d = b - a
            d = d / np.linalg.norm(d)
            one = round_cone(T(b), T(b + d * 0.14 * k * s + v(0, -0.06, 0)), 0.045 * k * s, 0.012 * s)
            cl = one if cl is None else cl | one
        H.mpiece("ToeClaws#", "Foot#", cl & gnd, col="claw", mat="hard", tris=260, role="claw", pri=1.8, ao=False)
    elif kind == "big":  # bigfoot / ogre: broad flat feet with stubby toes
        f = f.su(ellipsoid(0.2 * k * s, 0.12 * s, 0.34 * k * s, T(An + v(0, -0.18, -0.2 * k))), 0.12)
        for i, dx in enumerate((-0.13, -0.05, 0.03, 0.1, 0.16)):
            f = f.su(sphere((0.075 if i == 0 else 0.06) * k * s, T(An + v(dx * k, -0.22, -0.5 * k + abs(dx + 0.05) * 0.3))), 0.04)
    else:  # bare human-ish foot with toes
        for i, dx in enumerate((-0.08, -0.025, 0.025, 0.07, 0.11)):
            f = f.su(sphere((0.05 if i == 0 else 0.04) * k * s, T(An + v(dx * k, -0.24, -0.38 * k + abs(dx) * 0.4))), 0.035)
    H.mpiece("FootP#", "Foot#", f & gnd, col=col, mat=mat, tris=550, role="foot", pattern=_skinpat(P))


# ------------------------------------------------------------------------------------------------ eyes
def _eye(H, bone, pos, r, F, look=(0.18, 0.0, -1.0), name="Eye#", mirror=True):
    d = np.array(look, float)
    d = d / np.linalg.norm(d)
    x, y, z = pos
    add = H.mprim if mirror else H.prim
    nm = name if mirror else name.replace("#", "")
    if F["sclera"]:
        add(nm, bone, "Ball", (r * 2, r * 2, r * 2), (x, y, z), col=F["sclera"], mat="hard", pri=1.2, role="eye")
    ic = (x + d[0] * r * 0.62, y + d[1] * r * 0.62, z + d[2] * r * 0.62)
    ir = r * (0.66 if F["sclera"] else 1.0)
    add(nm.replace("Eye", "Iris"), bone, "Ball", (ir * 2,) * 3, ic, col=F["iris"], mat="hard", pri=1.3, role="eye", glow=F["glow"])
    if F["pupil"]:
        pc = (x + d[0] * r * 0.93, y + d[1] * r * 0.93, z + d[2] * r * 0.93)
        add(nm.replace("Eye", "Pupil"), bone, "Ball", (r * 0.62,) * 3, pc, col="pupil", mat="hard", pri=1.4, role="pupil")
    if not F["glow"]:
        sc = (x + d[0] * r * 0.9 + r * 0.12, y + r * 0.35, z + d[2] * r * 0.9)
        add(nm.replace("Eye", "Shine"), bone, "Ball", (r * 0.3,) * 3, sc, col="shine", mat="hard", pri=2.6, role="shine")


# ------------------------------------------------------------------------------------------------ heads
def _head_human(H, C, P, col=None):
    """Human-like face; presets through FACE keys. Returns (head sdf, jaw sdf or None, h())."""
    F = dict(FACE)
    F.update(P["face"])
    hc, hs = C["hc"], C["hs"]
    col = col or P["skin"]

    def h(x, y, z):
        return T(hc + np.array((x, y, z)) * hs)

    cw, chh, cd = F["cw"], F["ch"], F["cd"]
    head = ellipsoid(0.4 * cw * hs, 0.42 * chh * hs, 0.46 * cd * hs, h(0, 0.1, 0.05))
    head = head.su(ellipsoid(0.33 * cw * F["jw"] * hs, 0.4 * hs, 0.34 * hs, h(0, -0.12, -0.13)), 0.12)
    head = head.su(ellipsoid(0.13 * hs, 0.09 * hs, 0.12 * hs, h(0.24 * cw, -0.05, -0.29)).mirror_x(), 0.08 + 0.05 * F["cheek"])
    if F["cheek"] > 0.6:
        head = head.su(ellipsoid(0.16 * hs, 0.14 * hs, 0.14 * hs, h(0.25 * cw, -0.2, -0.24)).mirror_x(), 0.1)
    # brow ridge (angry slants the inner end down)
    bw = F["brow"]
    b0 = h(0.06, 0.12 - 0.08 * F["angry"], -0.4 - 0.04 * bw)
    b1 = h(0.3 * cw, 0.16, -0.32 - 0.03 * bw)
    head = head.su(capsule(b0, b1, (0.045 + 0.05 * bw) * hs).mirror_x(), 0.07)
    es = F["eye"]
    ex, ey, ez = 0.15 * F["eyesep"] * cw, 0.02 + F["eyey"], -0.37
    if F["one_eye"]:
        head = head.ss(sphere(0.2 * es * hs, h(0, ey + 0.02, ez + 0.02)), 0.05)
    else:
        head = head.ss(sphere(0.1 * es * hs, h(ex, ey, ez + 0.01)).mirror_x(), 0.04)
    nose = F["nose"]
    ns = F["ns"]
    if nose == "human":
        nz = round_cone(h(0, 0.06, -0.43), h(0, -0.12, -0.52 - 0.04 * ns), 0.045 * hs, 0.065 * ns * hs)
        nz = nz.su(ellipsoid(0.1 * ns * hs, 0.05 * hs, 0.06 * hs, h(0, -0.14, -0.47)), 0.04)
        head = head.su(nz, 0.05)
    elif nose == "long":
        head = head.su(tube([h(0, 0.06, -0.42), h(0, -0.08, -0.58 - 0.08 * ns), h(0, -0.24 * ns, -0.66 - 0.16 * ns)],
                            [0.065 * hs, 0.09 * hs * ns, 0.12 * hs * ns], k=0.05), 0.06)
    elif nose == "pointy":
        head = head.su(round_cone(h(0, 0.04, -0.42), h(0, -0.1 * ns, -0.45 - 0.42 * ns), 0.075 * hs, 0.022 * hs), 0.06)
    elif nose == "pig":
        sn = ellipsoid(0.13 * ns * hs, 0.1 * ns * hs, 0.12 * hs, h(0, -0.08, -0.47))
        sn = sn.ss(ellipsoid(0.035 * hs, 0.045 * hs, 0.06 * hs, h(0.05 * ns, -0.12, -0.58)).mirror_x(), 0.02)
        head = head.su(sn, 0.06)
    elif nose == "button":
        head = head.su(sphere(0.1 * ns * hs, h(0, -0.09, -0.5)), 0.05)
    elif nose == "hook":
        head = head.su(tube([h(0, 0.06, -0.42), h(0, -0.05, -0.6 - 0.05 * ns), h(0, -0.22 * ns, -0.58 - 0.08 * ns)],
                            [0.06 * hs, 0.07 * hs, 0.03 * hs], k=0.04), 0.05)
    elif nose == "skull":
        head = head.ss(ellipsoid(0.05 * hs, 0.08 * hs, 0.1 * hs, h(0, -0.12, -0.45)), 0.02)
    # ears
    ears = F["ears"]
    er = F["es"]
    ear = None
    if ears == "human":
        ear = ellipsoid(0.05 * hs, 0.12 * er * hs, 0.08 * er * hs, h(0.4 * cw, -0.02, 0.02))
    elif ears == "elf":
        ear = tube([h(0.37 * cw, -0.02, 0.02), h(0.5 * cw, 0.12 * er, 0.1), h(0.62 * cw, 0.34 * er, 0.22 * er)],
                   [0.075 * hs, 0.05 * hs, 0.012 * hs], k=0.04)
        ear = ear.scale3(1.0, 1.0, 1.0)
    elif ears == "goblin":
        ear = plate([(0, -0.1), (0.2, -0.13), (0.55 * er, -0.02), (0.75 * er, 0.12 * er), (0.4, 0.13), (0.05, 0.1)],
                    h(0.36 * cw, 0.0, 0.02), (1, 0.18, 0.25), (0, 1, 0.1), 0.03 * hs, bulge=-0.035 * hs)
        ear = ear.su(capsule(h(0.38 * cw, 0.0, 0.02), h(0.45 * cw, 0.0, 0.05), 0.06 * hs), 0.03)
    elif ears == "pointed":
        ear = round_cone(h(0.36 * cw, 0.02, 0.04), h(0.5 * cw, 0.28 * er, 0.12), 0.08 * hs, 0.015 * hs)
    if ear is not None:
        head = head.su(ear.mirror_x(), 0.04)
    # mouth: cut the face below the mouth line when the jaw is separate
    jaw = None
    my = -0.27
    if F["jaw"]:
        cut = box(0.5 * hs, 0.25 * hs, 0.4 * hs, h(0, my - 0.25, -0.38))
        head = head.ss(cut, 0.04)
        jw, jl, ub = F["jw"], F["jl"], F["under"]
        jaw = ellipsoid(0.27 * cw * jw * hs, 0.13 * hs, (0.26 + 0.04 * jl) * hs, h(0, -0.36, -0.2 - 0.06 * ub))
        jaw = jaw.su(sphere(0.12 * F["chin"] * hs, h(0, -0.42, -0.36 - 0.1 * ub)), 0.1)
        jaw = jaw.su(round_cone(h(0.3 * cw * jw, -0.12, 0.02), h(0.2 * cw * jw, -0.38, -0.22), 0.08 * hs, 0.09 * hs).mirror_x(), 0.08)
        if F["lips"] > 0:
            jaw = jaw.su(capsule(h(-0.16 * F["mouthw"], -0.28, -0.4 - 0.08 * ub), h(0.16 * F["mouthw"], -0.28, -0.4 - 0.08 * ub), 0.05 * F["lips"] * hs), 0.04)
        jaw = jaw.ss(ellipsoid(0.2 * F["mouthw"] * hs, 0.06 * hs, 0.25 * hs, h(0, -0.25, -0.3)), 0.03)
    else:
        head = head.ss(capsule(h(-0.11 * F["mouthw"], -0.29, -0.47), h(0.11 * F["mouthw"], -0.29, -0.47), 0.016 * hs), 0.012)
    return head, jaw, h, F


def _place_head(H, C, P, head, jaw, h, F, col=None, tris=2400, eyes=True, tooth_col="tooth"):
    col = col or P["skin"]
    hs = C["hs"]
    H.piece("HeadP", "Head", head, col=col, mat=P["skinmat"], tris=tris, res=136, role="head", pattern=_skinpat(P))
    if jaw is not None:
        H.bone("Jaw", "Head", h(0, -0.2, 0.02))
        H.piece("JawP", "Jaw", jaw, col=col, mat=P["skinmat"], tris=650, role="jaw", pri=1.3, pattern=_skinpat(P))
        H.prim("Mouth", "Head", "Ellipsoid", (0.36 * F["mouthw"] * hs, 0.1 * hs, 0.36 * hs), h(0, -0.27, -0.25), col="mouth", mat="hard", role="mouth", pri=2.4)
        tk = F["tusks"]
        if tk > 0:
            ub = F["under"]
            tu = round_cone(h(0.15 * F["mouthw"], -0.32, -0.38 - 0.08 * ub), h(0.19 * F["mouthw"], -0.32 + 0.22 * tk, -0.42 - 0.1 * ub), 0.05 * hs, 0.014 * hs)
            H.mpiece("Tusk#", "Jaw", tu, col="tooth", mat="hard", tris=200, role="tooth", pri=2.0, ao=False, smooth=2)
        if F["fangs"] > 0:
            fg = round_cone(h(0.1, -0.24, -0.4), h(0.1, -0.24 - 0.12 * F["fangs"], -0.41), 0.035 * hs, 0.008 * hs)
            H.mpiece("Fang#", "Head", fg, col=tooth_col, mat="hard", tris=160, role="tooth", pri=2.2, ao=False, smooth=2)
        if F["teeth"]:
            tt = None
            for i in range(5):
                x = -0.14 + i * 0.07
                one = round_cone(h(x, -0.25, -0.41 + abs(x) * 0.35), h(x, -0.31, -0.42 + abs(x) * 0.35), 0.035 * hs, 0.02 * hs)
                tt = one if tt is None else tt | one
            H.piece("Teeth", "Head", tt, col=tooth_col, mat="hard", tris=260, role="tooth", pri=2.1, ao=False, smooth=2)
    if eyes:
        es = F["eye"]
        r = 0.075 * es * hs
        if F["one_eye"]:
            _eye(H, "Head", h(0, 0.04 + F["eyey"], -0.34), r * 2.3, F, look=(0, 0, -1), name="Eye#", mirror=False)
        else:
            ex = 0.15 * F["eyesep"] * F["cw"]
            _eye(H, "Head", h(ex, 0.02 + F["eyey"], -0.355), r, F, look=(0.15, 0.0, -1.0))


def _snout_head(H, C, P, kind, col=None, mz=1.0, ear="pointed", es=1.0, horns=None):
    """Animal-headed humanoids: wolf, bull, lizard, fish, ape. Upper skull + muzzle on Head, a lower jaw bone."""
    hc, hs = C["hc"], C["hs"]
    col = col or P["skin"]

    def h(x, y, z):
        return T(hc + np.array((x, y, z)) * hs)

    F = dict(FACE)
    F.update(P["face"])
    if kind == "wolf":
        head = ellipsoid(0.38 * hs, 0.36 * hs, 0.42 * hs, h(0, 0.08, 0.05))
        head = head.su(ellipsoid(0.3 * hs, 0.28 * hs, 0.3 * hs, h(0.18, -0.08, -0.12)).mirror_x(), 0.12)      # cheeks
        head = head.su(round_cone(h(0, 0.08, -0.25), h(0, -0.04, -0.7 * mz - 0.15), 0.21 * hs, 0.12 * hs), 0.14)  # muzzle top
        head = head.su(ellipsoid(0.18 * hs, 0.1 * hs, 0.36 * mz * hs, h(0, -0.1, -0.5 * mz - 0.05)), 0.08)
        head = head.su(capsule(h(0.08, 0.17, -0.3), h(0.22, 0.18, -0.22), 0.06 * hs).mirror_x(), 0.06)        # brow
        head = head.ss(sphere(0.085 * hs, h(0.17, 0.11, -0.33)).mirror_x(), 0.04)
        nose = ellipsoid(0.08 * hs, 0.06 * hs, 0.07 * hs, h(0, -0.02, -0.72 * mz - 0.16))
        H.piece("NoseP", "Head", nose, col="dark", mat="hard", tris=200, role="nose", pri=1.7, ao=False)
        for sx in (1,):
            e = round_cone(h(0.22, 0.32, 0.08), h(0.32, 0.72 * es, 0.16), 0.12 * hs, 0.02 * hs)
            e = e.ss(ellipsoid(0.06 * hs, 0.2 * hs, 0.05 * hs, h(0.26, 0.45 * es, 0.06)), 0.03)
            head = head.su(e.mirror_x(), 0.06)
        # fur ruff around the head
        ruff = None
        for i in range(9):
            a = -1.2 + i * 0.3
            c0 = np.array(h(0.3 * math.cos(a) * 1.1, -0.12 + 0.12 * math.sin(a), 0.1))
            tip = c0 + np.array((math.cos(a) * 0.35, -0.12 + 0.2 * math.sin(a), 0.2)) * hs
            one = round_cone(T(c0), T(tip), 0.12 * hs, 0.03 * hs)
            ruff = one if ruff is None else ruff.su(one, 0.04)
        head = head.su(ruff.mirror_x(), 0.06)
        jaw = ellipsoid(0.17 * hs, 0.08 * hs, 0.34 * mz * hs, h(0, -0.22, -0.42 * mz - 0.05))
        jaw = jaw.su(round_cone(h(0.17, -0.1, -0.05), h(0.1, -0.22, -0.5 * mz), 0.07 * hs, 0.06 * hs).mirror_x(), 0.06)
        jbone = h(0, -0.12, -0.02)
        mouth = (h(0, -0.15, -0.42 * mz), (0.26 * hs, 0.07 * hs, 0.6 * mz * hs))
        fang = [(h(0.1, -0.13, -0.62 * mz - 0.05), 0.13)]
        eyep = h(0.17, 0.11, -0.335)
        look = (0.45, 0.05, -1.0)
        er = 0.06 * hs
    elif kind == "bull":
        head = ellipsoid(0.4 * hs, 0.38 * hs, 0.42 * hs, h(0, 0.1, 0.02))
        head = head.su(round_cone(h(0, 0.15, -0.2), h(0, -0.18, -0.58 * mz), 0.3 * hs, 0.25 * hs), 0.15)        # long face
        head = head.su(ellipsoid(0.27 * hs, 0.2 * hs, 0.2 * hs, h(0, -0.25, -0.62 * mz)), 0.1)                    # muzzle pad
        head = head.su(ellipsoid(0.22 * hs, 0.18 * hs, 0.2 * hs, h(0.24, 0.15, -0.2)).mirror_x(), 0.1)
        head = head.su(sphere(0.09 * hs, h(0.18, 0.18, -0.34)).mirror_x(), 0.05)
        head = head.ss(ellipsoid(0.045 * hs, 0.06 * hs, 0.07 * hs, h(0.1, -0.25, -0.8 * mz)).mirror_x(), 0.02)  # nostrils
        head = head.su(ellipsoid(0.42 * hs, 0.25 * hs, 0.28 * hs, h(0, 0.3, 0.05)).noise(0.03 * hs, 10 / hs, 3), 0.1)  # poll curls
        e = plate([(0, -0.08), (0.22, -0.1), (0.36 * es, 0.0), (0.2, 0.09), (0, 0.07)], h(0.36, 0.22, 0.05), (1, -0.25, 0.3), (0, 1, 0), 0.025 * hs, bulge=-0.03 * hs)
        head = head.su(e.mirror_x(), 0.04)
        jaw = ellipsoid(0.2 * hs, 0.1 * hs, 0.28 * mz * hs, h(0, -0.38, -0.4 * mz))
        jaw = jaw.su(round_cone(h(0.2, -0.15, 0.0), h(0.14, -0.35, -0.4 * mz), 0.08 * hs, 0.08 * hs).mirror_x(), 0.08)
        jbone = h(0, -0.2, -0.0)
        mouth = (h(0, -0.3, -0.45 * mz), (0.3 * hs, 0.06 * hs, 0.45 * mz * hs))
        fang = []
        eyep = h(0.26, 0.15, -0.3)
        look = (0.8, 0.05, -0.6)
        er = 0.065 * hs
        ring = torus(0.1 * hs, 0.022 * hs, axis=2).at(*h(0, -0.38, -0.82 * mz))
        H.piece("NoseRing", "Head", ring, col="gold", mat="metal", tris=220, role="detail", pri=2.2, ao=False)
    elif kind == "lizard":
        head = ellipsoid(0.32 * hs, 0.3 * hs, 0.42 * hs, h(0, 0.06, 0.05))
        head = head.su(round_cone(h(0, 0.05, -0.2), h(0, -0.05, -0.85 * mz), 0.26 * hs, 0.13 * hs), 0.14)
        head = head.su(capsule(h(0.14, 0.2, -0.3), h(0.2, 0.2, -0.05), 0.07 * hs).mirror_x(), 0.06)
        head = head.ss(sphere(0.08 * hs, h(0.2, 0.13, -0.2)).mirror_x(), 0.03)
        head = head.ss(sphere(0.025 * hs, h(0.06, 0.02, -0.92 * mz)).mirror_x(), 0.01)
        crest = None
        for i in range(5):
            z = -0.1 + i * 0.17
            one = round_cone(h(0, 0.3 - i * 0.04, z), h(0, 0.55 - i * 0.06, z + 0.12), 0.06 * hs, 0.015 * hs)
            crest = one if crest is None else crest | one
        H.piece("Crest", "Head", crest.su(capsule(h(0, 0.3, -0.12), h(0, 0.15, 0.6), 0.05 * hs), 0.04), col="secondary", tris=500, role="crest", pri=1.6)
        jaw = ellipsoid(0.22 * hs, 0.08 * hs, 0.4 * mz * hs, h(0, -0.15, -0.45 * mz))
        jaw = jaw.su(round_cone(h(0.2, -0.05, 0.05), h(0.1, -0.15, -0.6 * mz), 0.07 * hs, 0.06 * hs).mirror_x(), 0.06)
        jbone = h(0, -0.06, 0.05)
        mouth = (h(0, -0.08, -0.45 * mz), (0.32 * hs, 0.05 * hs, 0.75 * mz * hs))
        fang = [(h(0.12, -0.06, -0.6 * mz), 0.09), (h(0.1, -0.06, -0.78 * mz), 0.07)]
        eyep = h(0.21, 0.13, -0.18)
        look = (0.9, 0.1, -0.4)
        er = 0.075 * hs
        F["iris"] = F.get("iris", "iris")
    elif kind == "fish":
        head = ellipsoid(0.4 * hs, 0.38 * hs, 0.46 * hs, h(0, 0.02, 0.02))
        head = head.su(ellipsoid(0.36 * hs, 0.24 * hs, 0.3 * hs, h(0, -0.12, -0.3)), 0.12)
        head = head.su(sphere(0.14 * hs, h(0.3, 0.12, -0.18)).mirror_x(), 0.08)  # bulging eye mounds
        fin = plate([(0, 0), (0.25, 0.12), (0.45, 0.35), (0.3, 0.38), (0.1, 0.2), (-0.05, 0.12)], h(0.32, -0.05, 0.05), (1, 0.2, 0.4), (0, 1, 0), 0.025 * hs)
        head = head.su(fin.mirror_x(), 0.04)
        crest = plate([(-0.35, 0), (-0.2, 0.25), (0.05, 0.38), (0.35, 0.3), (0.55, 0.05), (0.6, -0.1)], h(0, 0.3, 0.0), (0, 0, 1), (0, 1, 0), 0.025 * hs)
        H.piece("Crest", "Head", crest.su(capsule(h(0, 0.3, -0.3), h(0, 0.25, 0.55), 0.04 * hs), 0.03), col="secondary", tris=400, role="fin", pri=1.6)
        for i in range(3):
            head = head.ss(capsule(h(0.36, -0.1 - i * 0.08, 0.12 + i * 0.03), h(0.38, -0.05 - i * 0.08, 0.28 + i * 0.03), 0.018 * hs).mirror_x(), 0.01)
        jaw = ellipsoid(0.33 * hs, 0.11 * hs, 0.3 * hs, h(0, -0.32, -0.22))
        jaw = jaw.su(capsule(h(-0.25, -0.3, -0.42), h(0.25, -0.3, -0.42), 0.06 * hs), 0.06)
        jbone = h(0, -0.2, 0.05)
        mouth = (h(0, -0.25, -0.3), (0.5 * hs, 0.08 * hs, 0.35 * hs))
        fang = []
        eyep = h(0.33, 0.14, -0.24)
        look = (0.9, 0.15, -0.5)
        er = 0.1 * hs
    elif kind == "ape":
        head = ellipsoid(0.36 * hs, 0.38 * hs, 0.38 * hs, h(0, 0.1, 0.08))
        head = head.su(ellipsoid(0.27 * hs, 0.24 * hs, 0.24 * mz * hs, h(0, -0.18, -0.3 - 0.06 * mz)), 0.14)     # muzzle
        head = head.su(capsule(h(-0.25, 0.1, -0.33), h(0.25, 0.1, -0.33), 0.08 * hs), 0.06)                    # brow shelf
        head = head.ss(sphere(0.09 * hs, h(0.13, 0.02, -0.36)).mirror_x(), 0.03)
        head = head.ss(ellipsoid(0.03 * hs, 0.03 * hs, 0.05 * hs, h(0.05, -0.1, -0.52 - 0.06 * mz)).mirror_x(), 0.01)
        head = head.su(ellipsoid(0.06 * hs, 0.11 * es * hs, 0.09 * es * hs, h(0.36, 0.0, 0.05)).mirror_x(), 0.03)
        jaw = ellipsoid(0.22 * hs, 0.12 * hs, 0.22 * mz * hs, h(0, -0.36, -0.25 - 0.04 * mz))
        jaw = jaw.su(round_cone(h(0.24, -0.1, 0.05), h(0.16, -0.34, -0.2), 0.07 * hs, 0.08 * hs).mirror_x(), 0.07)
        jbone = h(0, -0.2, 0.0)
        mouth = (h(0, -0.28, -0.3), (0.32 * hs, 0.07 * hs, 0.4 * hs))
        fang = [(h(0.09, -0.27, -0.44), 0.08)]
        eyep = h(0.13, 0.02, -0.33)
        look = (0.15, 0.0, -1.0)
        er = 0.06 * hs
    H.piece("HeadP", "Head", head, col=col, mat=P["skinmat"], tris=2400, res=136, role="head", pattern=_skinpat(P))
    H.bone("Jaw", "Head", jbone)
    H.piece("JawP", "Jaw", jaw, col=col, mat=P["skinmat"], tris=650, role="jaw", pri=1.3, pattern=_skinpat(P))
    H.prim("Mouth", "Head", "Ellipsoid", mouth[1], mouth[0], col="mouth", mat="hard", role="mouth", pri=2.4)
    if fang:
        fg = None
        for c, ln in fang:
            one = round_cone(c, T(np.array(c) + np.array((0, -ln, -0.01)) * hs), 0.035 * hs, 0.009 * hs)
            fg = one if fg is None else fg | one
        H.mpiece("Fang#", "Head", fg, col="tooth", mat="hard", tris=200, role="tooth", pri=2.2, ao=False, smooth=2)
    F2 = dict(F)
    F2["sclera"] = None if kind in ("wolf", "lizard", "fish", "bull") else F["sclera"]
    _eye(H, "Head", eyep, er, F2, look=look)
    return h


def _skull_head(H, C, P, crown=False):
    hc, hs = C["hc"], C["hs"]

    def h(x, y, z):
        return T(hc + np.array((x, y, z)) * hs)

    sk = ellipsoid(0.38 * hs, 0.4 * hs, 0.45 * hs, h(0, 0.12, 0.05))
    sk = sk.su(ellipsoid(0.3 * hs, 0.28 * hs, 0.26 * hs, h(0, -0.1, -0.2)), 0.1)
    sk = sk.su(ellipsoid(0.12 * hs, 0.08 * hs, 0.14 * hs, h(0.26, -0.08, -0.22)).mirror_x(), 0.05)   # cheekbones
    sk = sk.su(capsule(h(-0.28, 0.1, -0.36), h(0.28, 0.1, -0.36), 0.05 * hs), 0.05)
    sk = sk.ss(ellipsoid(0.12 * hs, 0.11 * hs, 0.16 * hs, h(0.14, 0.0, -0.38)).mirror_x(), 0.03)      # orbits
    sk = sk.ss(round_cone(h(0, -0.06, -0.48), h(0, -0.2, -0.44), 0.025 * hs, 0.055 * hs), 0.02)       # nasal hole
    sk = sk.ss(ellipsoid(0.12 * hs, 0.06 * hs, 0.08 * hs, h(0.36, -0.06, 0.1)).mirror_x(), 0.03)       # temples
    sk = sk.ss(box(0.5 * hs, 0.2 * hs, 0.35 * hs, h(0, -0.48, -0.35)), 0.03)
    teeth = None
    for i in range(8):
        x = -0.17 + i * 0.0485
        one = round_box(0.022 * hs, 0.045 * hs, 0.03 * hs, 0.012 * hs, h(x, -0.27, -0.38 + abs(x) * 0.55))
        teeth = one if teeth is None else teeth | one
    sk = sk.su(capsule(h(-0.18, -0.24, -0.3), h(0.18, -0.24, -0.3), 0.04 * hs), 0.03)
    sk = sk | teeth
    jaw = ellipsoid(0.24 * hs, 0.08 * hs, 0.2 * hs, h(0, -0.4, -0.25))
    jaw = jaw.su(round_cone(h(0.27, -0.12, 0.0), h(0.22, -0.38, -0.2), 0.05 * hs, 0.06 * hs).mirror_x(), 0.04)
    jaw = jaw.ss(ellipsoid(0.18 * hs, 0.1 * hs, 0.18 * hs, h(0, -0.33, -0.18)), 0.03)
    lt = None
    for i in range(7):
        x = -0.15 + i * 0.05
        one = round_box(0.021 * hs, 0.04 * hs, 0.028 * hs, 0.012 * hs, h(x, -0.33, -0.36 + abs(x) * 0.5))
        lt = one if lt is None else lt | one
    jaw = jaw | lt
    H.piece("HeadP", "Head", sk, col=P["skin"], mat="hard", tris=2400, res=136, role="head")
    H.bone("Jaw", "Head", h(0, -0.18, 0.0))
    H.piece("JawP", "Jaw", jaw, col=P["skin"], mat="hard", tris=700, role="jaw", pri=1.3)
    for sx in (1, -1):
        H.prim("EyeGlow" + ("R" if sx > 0 else "L"), "Head", "Ball", (0.07 * hs,) * 3, h(0.14 * sx, 0.0, -0.36), col=P.get("eyeglow", "red"), mat="hard", glow=True, role="eye", pri=1.5)
        H.prim("Socket" + ("R" if sx > 0 else "L"), "Head", "Ellipsoid", (0.2 * hs, 0.18 * hs, 0.1 * hs), h(0.14 * sx, 0.0, -0.3), col="black", mat="hard", role="detail", pri=1.4)
    return h


def _alien_head(H, C, P):
    hc, hs = C["hc"], C["hs"]

    def h(x, y, z):
        return T(hc + np.array((x, y, z)) * hs)

    hd = ellipsoid(0.52 * hs, 0.5 * hs, 0.55 * hs, h(0, 0.25, 0.05))
    hd = hd.su(round_cone(h(0, 0.05, -0.15), h(0, -0.42, -0.28), 0.32 * hs, 0.08 * hs), 0.2)
    hd = hd.ss(ellipsoid(0.17 * hs, 0.09 * hs, 0.14 * hs, h(0.19, 0.04, -0.37)).rot(0, 0, 0).mirror_x(), 0.04)
    hd = hd.ss(capsule(h(-0.06, -0.33, -0.38), h(0.06, -0.33, -0.38), 0.012 * hs), 0.01)
    hd = hd.ss(sphere(0.012 * hs, h(0.025, -0.16, -0.44)).mirror_x(), 0.01)
    H.piece("HeadP", "Head", hd, col=P["skin"], mat=P["skinmat"], tris=2200, res=136, role="head")
    for sx in (1, -1):
        H.prim("Eye" + ("R" if sx > 0 else "L"), "Head", "Ellipsoid", (0.3 * hs, 0.15 * hs, 0.16 * hs), h(0.19 * sx, 0.05, -0.35),
               rot=(0, -0.35 * sx, 0.45 * sx), col="black", mat="glass", role="eye", pri=1.4)
        H.prim("Shine" + ("R" if sx > 0 else "L"), "Head", "Ball", (0.05 * hs,) * 3, h(0.22 * sx, 0.1, -0.42), col="shine", mat="hard", role="shine", pri=2.5)
    if P.get("antenna"):
        ant = None
        for sx in (1, -1):
            one = tube([h(0.15 * sx, 0.65, 0.0), h(0.25 * sx, 0.95, 0.05), h(0.3 * sx, 1.15, -0.05)], [0.035 * hs, 0.028 * hs, 0.025 * hs], k=0.02)
            one = one | sphere(0.07 * hs, h(0.3 * sx, 1.17, -0.06))
            ant = one if ant is None else ant | one
        H.piece("Antennae", "Head", ant, col=P["skin"], mat=P["skinmat"], tris=400, role="antenna", pri=1.6)
    return h


# ------------------------------------------------------------------------------------------------ kit: hair, hats, horns
def _hair(H, C, kind, col="hair", h=None):
    hc, hs = C["hc"], C["hs"]

    def hh(x, y, z):
        return T(hc + np.array((x, y, z)) * hs)

    cap = ellipsoid(0.44 * hs, 0.46 * hs, 0.5 * hs, hh(0, 0.12, 0.06))
    if kind == "long":
        hr = cap.su(round_box(0.38 * hs, 0.5 * hs, 0.2 * hs, 0.15 * hs, hh(0, -0.35, 0.28)), 0.15)
        hr = hr.su(round_box(0.13 * hs, 0.45 * hs, 0.12 * hs, 0.1 * hs, hh(0.36, -0.3, 0.0)).mirror_x(), 0.1)
        hr = hr.ss(ellipsoid(0.36 * hs, 0.42 * hs, 0.5 * hs, hh(0, -0.14, -0.3)), 0.06)
        hr = hr.ss(box(hs, 0.2 * hs, 0.45 * hs, hh(0, 0.0, -0.85)), 0.1)
        hr = hr.noise(0.012 * hs, 22 / hs, 4)
    elif kind == "mohawk":
        hr = None
        for i in range(6):
            z = -0.25 + i * 0.13
            one = round_cone(hh(0, 0.45 - 0.06 * abs(i - 2), z), hh(0, 0.75 - 0.05 * abs(i - 2), z + 0.15), 0.07 * hs, 0.02 * hs)
            hr = one if hr is None else hr.su(one, 0.03)
    elif kind == "wild":
        hr = cap
        for i in range(12):
            a = i / 12 * math.tau
            c0 = np.array(hh(0.3 * math.cos(a), 0.35, 0.3 * math.sin(a) + 0.1))
            tip = c0 + np.array((math.cos(a) * 0.35, 0.18, math.sin(a) * 0.35 + 0.1)) * hs
            hr = hr.su(round_cone(T(c0), T(tip), 0.11 * hs, 0.025 * hs), 0.06)
        hr = hr.ss(ellipsoid(0.36 * hs, 0.4 * hs, 0.5 * hs, hh(0, -0.15, -0.3)), 0.06)
        hr = hr.noise(0.02 * hs, 14 / hs, 5)
    elif kind == "topknot":
        hr = cap.ss(ellipsoid(0.38 * hs, 0.45 * hs, 0.5 * hs, hh(0, -0.08, -0.25)), 0.06)
        hr = hr.su(tube([hh(0, 0.5, 0.25), hh(0, 0.62, 0.42), hh(0, 0.45, 0.62), hh(0, 0.1, 0.72)], [0.1 * hs, 0.09 * hs, 0.07 * hs, 0.04 * hs], k=0.04), 0.05)
    else:  # short
        hr = cap.ss(ellipsoid(0.38 * hs, 0.45 * hs, 0.5 * hs, hh(0, -0.1, -0.22)), 0.06)
        hr = hr.noise(0.012 * hs, 20 / hs, 6)
    H.piece("Hair", "Head", hr, col=col, mat="cloth", tris=1300, res=128, role="hair", pri=1.2)


def _beard(H, C, kind="full", col="hair", bone="Head", braid=True):
    hc, hs = C["hc"], C["hs"]

    def hh(x, y, z):
        return T(hc + np.array((x, y, z)) * hs)

    if kind == "full":
        b = ellipsoid(0.33 * hs, 0.3 * hs, 0.22 * hs, hh(0, -0.36, -0.3))
        b = b.su(round_cone(hh(0, -0.45, -0.36), hh(0, -1.05, -0.42), 0.27 * hs, 0.1 * hs), 0.15)
        b = b.su(ellipsoid(0.12 * hs, 0.3 * hs, 0.14 * hs, hh(0.3, -0.18, -0.12)).mirror_x(), 0.08)
        b = b.su(capsule(hh(0.04, -0.2, -0.47), hh(0.26, -0.27, -0.4), 0.06 * hs).mirror_x(), 0.04)  # moustache
        b = b.ss(ellipsoid(0.09 * hs, 0.04 * hs, 0.1 * hs, hh(0, -0.3, -0.5)), 0.02)
        if braid:
            for sx in (1, -1):
                b = b.su(tube([hh(0.1 * sx, -0.9, -0.4), hh(0.12 * sx, -1.15, -0.38), hh(0.1 * sx, -1.3, -0.36)], [0.07 * hs, 0.05 * hs, 0.04 * hs], k=0.02), 0.03)
        b = b.noise(0.018 * hs, 18 / hs, 2)
    elif kind == "goatee":
        b = round_cone(hh(0, -0.4, -0.38), hh(0, -0.75, -0.36), 0.1 * hs, 0.02 * hs)
    else:  # short scruffy
        b = ellipsoid(0.33 * hs, 0.22 * hs, 0.22 * hs, hh(0, -0.33, -0.27)).ss(ellipsoid(0.08 * hs, 0.05 * hs, 0.1 * hs, hh(0, -0.28, -0.48)), 0.02)
        b = b.noise(0.015 * hs, 20 / hs, 3)
    H.piece("Beard", bone, b, col=col, mat="cloth", tris=1200, res=120, role="beard", pri=1.25)


def _horns(H, C, kind="ram", col="horn", size=1.0):
    hc, hs = C["hc"], C["hs"]

    def hh(x, y, z):
        return np.array(hc) + np.array((x, y, z)) * hs

    k = size
    if kind == "bull":
        pts = curve(hh(0.3, 0.3, -0.02), hh(0.75 * k, 0.4, -0.05), hh(0.8 * k, 0.85 * k, -0.25), 7)
        r0, r1 = 0.11 * hs, 0.02 * hs
    elif kind == "ram":
        pts = []
        for i in range(10):
            a = i / 9 * 1.6 * math.pi
            rr = (0.32 - 0.16 * i / 9) * k
            pts.append(hh(0.3 + 0.12 * i / 9 * k, 0.32 + rr * math.sin(a) * 0.9, 0.05 + rr * (1 - math.cos(a))) + np.array((0, 0, 0)))
        pts = [p + np.array((0, -0.1 * hs, 0)) for p in pts]
        r0, r1 = 0.1 * hs, 0.035 * hs
    elif kind == "devil":
        pts = curve(hh(0.2, 0.36, -0.15), hh(0.3, 0.6 * k, -0.15), hh(0.24, 0.82 * k, 0.05), 6)
        r0, r1 = 0.08 * hs, 0.012 * hs
    elif kind == "demon":
        pts = curve(hh(0.22, 0.34, -0.1), hh(0.55 * k, 0.55 * k, 0.05), hh(0.5 * k, 0.95 * k, 0.4 * k), 7)
        r0, r1 = 0.1 * hs, 0.015 * hs
    elif kind == "goat":
        pts = curve(hh(0.15, 0.36, -0.15), hh(0.22, 0.75 * k, 0.05), hh(0.3, 0.75 * k, 0.45 * k), 7)
        r0, r1 = 0.075 * hs, 0.015 * hs
    elif kind == "stub":
        pts = curve(hh(0.2, 0.35, -0.15), hh(0.25, 0.5 * k, -0.15), hh(0.28, 0.6 * k, -0.1), 4)
        r0, r1 = 0.07 * hs, 0.02 * hs
    elif kind == "oni":
        pts = curve(hh(0.16, 0.38, -0.2), hh(0.2, 0.6 * k, -0.22), hh(0.22, 0.8 * k, -0.15), 5)
        r0, r1 = 0.08 * hs, 0.015 * hs
    hn = horn_sdf(pts, r0, r1)
    if kind in ("ram", "goat", "bull"):
        rid = None
        for i, p in enumerate(pts[1:-1]):
            pass
    H.mpiece("Horn#", "Head", hn, col=col, mat="hard", tris=500, role="horn", pri=1.5)


def _hat(H, C, kind, col="primary", col2="secondary"):
    hc, hs = C["hc"], C["hs"]

    def hh(x, y, z):
        return T(hc + np.array((x, y, z)) * hs)

    if kind == "pointy":   # gnome hat: tall slouched cone
        hat = cone(0.5 * hs, 0.05 * hs, 0.55 * hs, axis=1, rr=0.03 * hs).at(*hh(0, 0.75, 0.06))
        hat = hat.bend(0.35 / hs, axis=1, toward=2) if False else hat
        hat = hat.su(torus(0.44 * hs, 0.07 * hs).at(*hh(0, 0.25, 0.06)), 0.04)
        hat = hat.su(sphere(0.07 * hs, hh(0, 1.3, 0.06)), 0.03)
        H.piece("Hat", "Head", hat, col=col, mat="cloth", tris=900, role="hat", pri=1.3)
    elif kind == "helmet":  # dwarf iron helm with nasal and rim
        hm = ellipsoid(0.47 * hs, 0.44 * hs, 0.52 * hs, hh(0, 0.2, 0.05)) & plane((0, -1, 0), -(hc[1] + 0.12 * hs))
        hm = hm.su(torus(0.47 * hs, 0.05 * hs).scale3(1, 1, 1.08).at(*hh(0, 0.12, 0.05)), 0.03)
        hm = hm.su(round_box(0.04 * hs, 0.22 * hs, 0.04 * hs, 0.02 * hs, hh(0, 0.06, -0.49)), 0.02)
        hm = hm.su(capsule(hh(0, 0.64, -0.35), hh(0, 0.64, 0.45), 0.04 * hs), 0.04)
        H.piece("Helmet", "Head", hm, col="steel", mat="metal", tris=900, role="hat", pri=1.3)
    elif kind == "hood":
        hd = ellipsoid(0.52 * hs, 0.55 * hs, 0.6 * hs, hh(0, 0.1, 0.08)).ss(ellipsoid(0.42 * hs, 0.52 * hs, 0.55 * hs, hh(0, 0.0, -0.18)), 0.04)
        hd = hd.su(round_cone(hh(0, 0.25, 0.4), hh(0, -0.2, 0.75), 0.2 * hs, 0.06 * hs), 0.1)
        H.piece("Hood", "Head", hd, col=col, mat="cloth", tris=1000, role="hat", pri=1.3)
    elif kind == "strawhat":
        hat = cylinder(0.8 * hs, 0.025 * hs, rr=0.02 * hs).at(*hh(0, 0.3, 0.05))
        hat = hat.su(cone(0.4 * hs, 0.25 * hs, 0.25 * hs, rr=0.06 * hs).at(*hh(0, 0.55, 0.05)), 0.06)
        hat = hat.noise(0.01 * hs, 30 / hs, 2)
        H.piece("Hat", "Head", hat, col=col, mat="wood", tris=900, role="hat", pri=1.3)
    elif kind == "crown":
        cr = cylinder(0.36 * hs, 0.09 * hs, rr=0.02 * hs).at(*hh(0, 0.5, 0.05)) - cylinder(0.31 * hs, 0.2 * hs).at(*hh(0, 0.5, 0.05))
        for i in range(6):
            a = i / 6 * math.tau
            cr = cr | round_cone(hh(0.34 * math.cos(a), 0.55, 0.05 + 0.34 * math.sin(a)), hh(0.36 * math.cos(a), 0.78, 0.05 + 0.36 * math.sin(a)), 0.05 * hs, 0.015 * hs)
        H.piece("Crown", "Head", cr, col="gold", mat="metal", tris=700, role="hat", pri=1.4)


def _ear_pair(H, C, kind, col):
    pass


# ------------------------------------------------------------------------------------------------ kit: cloth
def _belt(H, C, P, pel, col=LEATHER, buckle=True, loin=None, loin2=None):
    v, s = C["v"], C["s"]
    by = C["waist"][1] - 0.32 * s
    b = pel.round(0.045 * s) & slab_y(by - 0.08 * s, by + 0.08 * s)
    H.piece("Belt", "Body", b, col=col, mat="cloth", tris=600, role="cloth", pri=1.4)
    if buckle:
        z = None
        H.prim("Buckle", "Body", "Block", (0.2 * s, 0.16 * s, 0.05 * s), T(np.array((0, by, 0)) + _front(pel, by, s) + v(0, 0, -0.03)), col="gold", mat="metal", role="detail", pri=2.0)
    if loin:
        fz = _front(pel, by, s)[2]
        flap = plate([(-0.24, 0), (0.24, 0), (0.2, -0.75), (0.0, -0.82), (-0.2, -0.75)], T(np.array((0, by - 0.02 * s, fz - 0.03 * s))), (1, 0, 0), (0, 1, -0.08), 0.025 * s)
        flap = flap.scale(1.0)
        H.bone("Loin", "Body", T(np.array((0, by, fz))))
        H.piece("LoinF", "Loin", flap.noise(0.008 * s, 12 / s, 1), col=loin, mat="cloth", tris=300, role="cloth", pri=1.5)
        bz = _back(pel, by, s)[2]
        flap2 = plate([(-0.3, 0), (0.3, 0), (0.26, -0.7), (0.0, -0.76), (-0.26, -0.7)], T(np.array((0, by - 0.02 * s, bz + 0.03 * s))), (1, 0, 0), (0, 1, 0.08), 0.025 * s)
        H.piece("LoinB", "Body", flap2.noise(0.008 * s, 12 / s, 2), col=loin2 or loin, mat="cloth", tris=300, role="cloth", pri=1.5)


def _front(sdf_, y, s):
    """Front surface z of an SDF at x=0, height y (marches from the front)."""
    zs = np.linspace(-3 * s, 3 * s, 600)
    P_ = np.column_stack([np.zeros_like(zs), np.full_like(zs, y), zs])
    d = sdf_(P_)
    i = np.argmax(d < 0)
    return np.array((0.0, 0.0, zs[i]))


def _back(sdf_, y, s):
    zs = np.linspace(3 * s, -3 * s, 600)
    P_ = np.column_stack([np.zeros_like(zs), np.full_like(zs, y), zs])
    d = sdf_(P_)
    i = np.argmax(d < 0)
    return np.array((0.0, 0.0, zs[i]))


def _tunic(H, C, P, rib, pel, col="primary", lo=None, hi=None, skirt=0.0, sleeves=False, name="Tunic", bone="Spine", off=0.05):
    """Garment = the body grown by `off` and cut to a height band (no coplanar faces with the skin)."""
    s = C["s"]
    lo = C["hipY"] - 0.1 * s if lo is None else lo
    hi = C["Sh"][1] + 0.3 * s if hi is None else hi
    g = rib.round(off * s) | pel.round((off + 0.01) * s)
    if skirt > 0:
        skirt_sdf = cone((0.62 * P["W"] + 0.25 * skirt) * s, 0.5 * P["W"] * s, 0.5 * skirt * s, axis=1, rr=0.02 * s).at(0, C["hipY"] - 0.35 * skirt * s, 0.03 * s)
        g = g.su(skirt_sdf, 0.15 * s)
        lo = C["hipY"] - 0.85 * skirt * s
    g = g & slab_y(lo, hi)
    g = g.ss(sphere(0.2 * s, T(C["neckB"] + C["v"](0, 0.12, -0.12))), 0.06 * s)
    H.piece(name, bone, g, col=col, mat="cloth", tris=1800, res=128, role="cloth", pri=1.1)
    return g


def _robe(H, C, P, col="primary", length=1.0, flare=0.4, hood=False, bone="Body"):
    """Floor-length robe hanging from the shoulders (legs are hidden)."""
    v, s = C["v"], C["s"]
    W = P["W"]
    top = C["Sh"][1]
    r = round_cone(T(v(0, 0, 0) + np.array((0, top, 0.02 * s))), T(np.array((0, top - (top - 0.05 * s) * length, 0.05 * s))), 0.46 * W * s, (0.55 + flare) * W * s)
    r = r.su(ellipsoid(0.7 * W * s, 0.3 * s, 0.4 * s, T(np.array((0, top - 0.15 * s, 0.02 * s)))), 0.15)
    r = r & plane((0, -1, 0), -0.04 * s)
    # vertical folds
    def folds(p):
        a = np.arctan2(p[:, 0], p[:, 2])
        return 0.02 * s * np.sin(a * 9) * np.clip((top - p[:, 1]) / (top * 0.6), 0, 1)
    rr = r
    r = SDF(lambda p: rr(p) + folds(p))
    H.piece("Robe", bone, r, col=col, mat="cloth", tris=1800, res=128, role="cloth", pri=1.05)
    return r


def _cape(H, C, P, col="secondary", length=1.0, collar=False, tattered=False, bone="Spine", name="Cape", inner=None):
    v, s = C["v"], C["s"]
    W = P["W"]
    sh = C["Sh"]
    top = sh[1] + 0.05 * s
    bot = max(0.15 * s, top - (top - 0.15 * s) * length)
    zb = sh[2] + 0.42 * s * P["depth"]
    pts = [(-0.75 * W - 0.1, 0.0), (0.75 * W + 0.1, 0.0)]
    hgt = (top - bot) / s
    n = 9
    bottom = []
    for i in range(n + 1):
        x = (0.95 * W + 0.3) * (1 - 2 * i / n)
        y = -hgt - (0.12 * ((i % 2) * 2 - 1) if tattered else 0.0) - (0.1 if tattered and i % 3 == 0 else 0)
        bottom.append((x, y))
    poly = [pts[1]] + bottom + [pts[0]]
    cp = plate(poly, T(np.array((0, top, zb))), (1, 0, 0), (0, 1, 0.18), 0.03 * s, bulge=0.18 * s)
    cp = cp.ss(ellipsoid(0.62 * W * s, 0.5 * s, 0.3 * s, T(C["chest"] + v(0, 0.1, 0.0))), 0.05 * s)
    def ripple(p):
        return 0.03 * s * np.sin(p[:, 0] / s * 6.0) * np.clip((top - p[:, 1]) / (hgt * s), 0, 1)
    c0 = cp
    cp = SDF(lambda p: c0(p) + ripple(p))
    if collar:
        cl = plate([(-0.5, 0), (0.5, 0), (0.62, 0.62), (0.2, 0.42), (-0.2, 0.42), (-0.62, 0.62)], T(np.array((0, top - 0.02 * s, zb - 0.12 * s))), (1, 0, 0), (0, 1, 0.35), 0.03 * s, bulge=0.15 * s)
        cp = cp | cl
    H.bone("CapeB", bone, T(np.array((0, top, zb))))
    H.piece(name, "CapeB", cp, col=col, mat="cloth", tris=1500, res=128, role="cloth", pri=1.1)
    if inner:
        pass
    return "CapeB"


# ------------------------------------------------------------------------------------------------ kit: wings / tail
def _bat_wings(H, C, P, span=1.0, col="secondary", mcol=None, bone="Spine"):
    v, s = C["v"], C["s"]
    root = C["chest"] + v(0.22, 0.35, 0.32 * P["depth"])
    H.mbone("Wing#", bone, T(root))
    tip_b = root + v(1.1 * span, 0.65 * span, 0.25)
    H.mbone("WingTip#", "Wing#", T(tip_b))
    k = span * s
    arm = tube([T(root), T(root + v(0.55 * span, 0.4 * span, 0.18)), T(tip_b)], [0.09 * s, 0.075 * s, 0.06 * s], k=0.03)
    poly = [(0, 0), (0.65, 0.38), (1.2, 0.72), (1.15, 0.3), (0.95, -0.15), (0.7, -0.42), (0.35, -0.55), (0.12, -0.5), (0.0, -0.3)]
    poly = [(x * span, y * span) for x, y in poly]
    mem = plate(poly, T(root + v(0, -0.02, 0.06)), (1, 0, 0.1), (0, 1, 0.35), 0.025 * s, bulge=0.06 * k)
    H.mpiece("WingArm#", "Wing#", arm.su(mem, 0.03 * s), col=mcol or col, mat="skin", tris=900, role="wing", pri=1.2)
    fingers = None
    base = tip_b
    for a, ln in ((-0.3, 1.0), (-0.9, 0.95), (-1.4, 0.75)):
        d = np.array((math.cos(a) * 0.4, math.sin(a), 0.1))
        e = base + d * ln * k * 0.9
        one = round_cone(T(base), T(e), 0.05 * s, 0.025 * s)
        fingers = one if fingers is None else fingers | one
    poly2 = [(0, 0), (0.15, 0.25), (0.45, 0.05), (0.7, -0.25), (0.62, -0.75), (0.35, -0.95), (0.05, -0.75), (-0.2, -0.45)]
    poly2 = [(x * span, y * span) for x, y in poly2]
    mem2 = plate(poly2, T(tip_b + v(0, -0.02, 0.04)), (1, 0, 0.12), (0, 1, 0.3), 0.022 * s, bulge=0.04 * k)
    claw = round_cone(T(tip_b), T(tip_b + v(0.05, 0.25, -0.05)), 0.05 * s, 0.012 * s)
    H.mpiece("WingTipP#", "WingTip#", fingers.su(mem2, 0.03 * s) | claw, col=mcol or col, mat="skin", tris=900, role="wing", pri=1.25)
    return [("WingR", "WingTipR", 1), ("WingL", "WingTipL", -1)]


def _feather_wings(H, C, P, span=1.0, col="white", bone="Spine", pair=2):
    v, s = C["v"], C["s"]
    root = C["chest"] + v(0.2, 0.3, 0.33 * P["depth"])
    H.mbone("Wing#", bone, T(root))
    mid = root + v(0.95 * span, 0.55 * span, 0.3)
    H.mbone("WingTip#", "Wing#", T(mid))
    k = span * s

    def feathers(o, u, vdir, rows, t=0.035):
        """rows: list of (count, start(u), end(u), length, width). Feathers hang along -v and rake toward +u."""
        out = None
        for (n, a, b, ln, wd, yoff) in rows:
            for i in range(n):
                f = i / max(n - 1, 1)
                uu = a + (b - a) * f
                L = ln * (0.85 + 0.3 * f)
                poly = [(-wd, 0), (wd, 0), (wd * 0.8, -L * 0.85), (0.15 * wd, -L), (-wd * 0.7, -L * 0.9)]
                ang = 0.25 + 0.55 * f
                du = np.array(u) * math.sin(ang) - np.array(vdir) * math.cos(ang)
                pos = np.array(o) + np.array(u) * uu * k + np.array(vdir) * yoff * k
                one = plate(poly, T(pos), T(np.array(u) * math.cos(ang) + np.array(vdir) * math.sin(ang)), T(-du), t * s, bulge=0.01 * s)
                out = one if out is None else out | one
        return out

    u = np.array((1, 0.55, 0.32))
    u = u / np.linalg.norm(u)
    vd = np.array((0, 1, -0.05))
    arm = tube([T(root), T(root + v(0.5 * span, 0.35 * span, 0.15)), T(mid)], [0.11 * s, 0.1 * s, 0.08 * s], k=0.04)
    cov = plate([(0, 0.1), (1.05, 0.12), (1.05, -0.35), (0.6, -0.45), (0.0, -0.4)], T(root), T(u), T(vd), 0.05 * s, bulge=0.04 * s).scale(1.0)
    cov = SDF(lambda p, c=cov: c(p))
    covk = plate([(0, 0.1 * span), (1.08 * span, 0.12 * span), (1.08 * span, -0.38 * span), (0.6 * span, -0.48 * span), (0.0, -0.42 * span)], T(root), T(u), T(vd), 0.05 * s, bulge=0.04 * s)
    fe = feathers(T(root), T(u), T(vd), [(6, 0.05, 0.95, 0.75 * span, 0.09, -0.25)])
    H.mpiece("WingArm#", "Wing#", arm.su(covk, 0.05 * s) | fe, col=col, mat="cloth", tris=1500, res=128, role="wing", pri=1.2)
    u2 = np.array((1, 0.25, 0.3))
    u2 = u2 / np.linalg.norm(u2)
    arm2 = tube([T(mid), T(mid + v(0.5 * span, 0.15 * span, 0.12)), T(mid + v(0.95 * span, 0.18 * span, 0.2))], [0.08 * s, 0.06 * s, 0.04 * s], k=0.03)
    cov2 = plate([(-0.05 * span, 0.08 * span), (0.95 * span, 0.12 * span), (0.9 * span, -0.2 * span), (0.0, -0.3 * span)], T(mid), T(u2), T(vd), 0.04 * s, bulge=0.02 * s)
    fe2 = feathers(T(mid), T(u2), T(vd), [(6, 0.0, 1.0, 0.95 * span, 0.09, -0.12)])
    H.mpiece("WingTipP#", "WingTip#", arm2.su(cov2, 0.04 * s) | fe2, col=col, mat="cloth", tris=1500, res=128, role="wing", pri=1.25)
    return [("WingR", "WingTipR", 1), ("WingL", "WingTipL", -1)]


def _fairy_wings(H, C, P, span=1.0, col="secondary", bone="Spine"):
    v, s = C["v"], C["s"]
    root = C["chest"] + v(0.12, 0.25, 0.34 * P["depth"])
    H.mbone("Wing#", bone, T(root))
    up = plate([(0, 0), (0.35, 0.45), (0.8, 0.95), (1.1, 1.05), (1.15, 0.75), (0.9, 0.35), (0.4, 0.05)], T(root), (1, 0, 0.45), (0, 1, 0.1), 0.02 * s)
    lo = plate([(0, -0.02), (0.45, -0.2), (0.72, -0.55), (0.6, -0.78), (0.35, -0.7), (0.12, -0.35)], T(root), (1, 0, 0.5), (0, 1, 0.15), 0.02 * s)
    w = (up | lo).scale(1.0)
    w = SDF(lambda p, w=w, r=root, k=span: w((p - r) / k + r) * k)
    vein = None
    for a in ((0.9, 0.9), (1.05, 0.8), (0.6, -0.6)):
        one = capsule(T(root), T(root + v(a[0] * span * 0.95, a[1] * span * 0.95, a[0] * 0.45 * span)), 0.022 * s)
        vein = one if vein is None else vein | one
    H.mpiece("WingP#", "Wing#", w, col=col, mat="glass", tris=700, role="wing", pri=1.2, tr=0.35, ao=False)
    H.mpiece("WingVein#", "Wing#", vein, col="white", mat="hard", tris=300, role="wing", pri=1.3, ao=False)
    return [("WingR", None, 1), ("WingL", None, -1)]


def _tail(H, C, P, kind="devil", length=1.0, col=None, n=3, thick=1.0):
    v, s = C["v"], C["s"]
    col = col or P["skin"]
    root = np.array((0, C["hipY"] + 0.05 * s, 0.32 * s))
    names = []
    pts = [root]
    if kind == "lizard":
        dirs = [(0, -0.25, 1.0), (0, -0.5, 1.0), (0, -0.35, 1.0), (0, -0.1, 1.0)]
        seg = [0.75, 0.7, 0.65, 0.6]
        rad = [0.32, 0.24, 0.16, 0.09, 0.03]
    elif kind == "monkey":
        dirs = [(0, -0.2, 1.0), (0, 0.5, 1.0), (0, 1.0, 0.2), (0, 0.6, -0.8)]
        seg = [0.6, 0.6, 0.55, 0.45]
        rad = [0.09, 0.08, 0.07, 0.06, 0.05]
    elif kind == "lemur":
        dirs = [(0, -0.3, 1.0), (0, 0.6, 1.0), (0, 1.0, 0.4), (0, 1.0, -0.2)]
        seg = [0.65, 0.65, 0.6, 0.55]
        rad = [0.13, 0.15, 0.15, 0.14, 0.08]
    else:  # devil: thin whip with a spade
        dirs = [(0, -0.6, 1.0), (0, -0.1, 1.0), (0, 0.5, 1.0)]
        seg = [0.7, 0.7, 0.6]
        rad = [0.08, 0.06, 0.05, 0.04]
    n = len(dirs)
    for i in range(n):
        d = np.array(dirs[i], float)
        d = d / np.linalg.norm(d)
        pts.append(pts[-1] + d * seg[i] * length * s)
    for i in range(n):
        nm = f"Tail{i + 1}"
        H.bone(nm, "Body" if i == 0 else f"Tail{i}", T(pts[i]))
        names.append(nm)
        a = pts[i] - (pts[i + 1] - pts[i]) * (0.12 if i else 0.3)
        sg = round_cone(T(a), T(pts[i + 1]), rad[i] * thick * s, rad[i + 1] * thick * s)
        if kind == "devil" and i == n - 1:
            d = (pts[-1] - pts[-2])
            d = d / np.linalg.norm(d)
            sp = plate([(0, -0.02), (0.16, 0.08), (0.0, 0.32), (-0.16, 0.08)], T(pts[-1] - d * 0.02 * s), (1, 0, 0), T(d), 0.03 * s)
            sg = sg | sp
        pat = None
        if kind == "lemur":
            pat = stripes(lambda Q, o=root: np.linalg.norm(Q - o, axis=1) / s, 3.2, width=0.45, depth=0.85)
        H.piece(f"TailP{i + 1}", nm, sg, col=col, mat=P["skinmat"], tris=420 if kind != "lizard" else 600, role="tail", pri=1.5 + 0.1 * i, pattern=pat)
    return names


# ------------------------------------------------------------------------------------------------ kit: weapons
def _weapon(H, C, P, kind, side="R", col=None):
    """Weapon held in the fist: shaft along Z (forward) through the grip point, bone = Hand<side>."""
    v, s = C["v"], C["s"]
    g = C["grip"].copy()
    if side == "L":
        g[0] = -g[0]
    bone = "Hand" + side
    k = P.get("wscale", 1.0) * s

    def at(dy, dz):
        return T(g + np.array((0, dy * k, dz * k)))

    if kind == "club":
        h = round_cone(at(0.05, 0.35), at(-0.05, -1.35), 0.065 * k, 0.24 * k)
        h = h.su(sphere(0.27 * k, at(-0.08, -1.35)), 0.15)
        for i in range(5):
            a = i * 1.3
            h = h.su(sphere(0.09 * k, at(-0.08 + 0.2 * math.sin(a), -1.2 - 0.18 * math.cos(a))), 0.05)
        h = h.noise(0.025 * k, 8 / k, 3)
        H.piece("Club", bone, h, col=col or "wood", mat="wood", tris=900, role="weapon", pri=1.4)
        spikes = None
        for i in range(6):
            a = i / 6 * math.tau
            base = np.array(at(-0.08, -1.25 + 0.1 * (i % 2))) + np.array((math.cos(a) * 0.24, math.sin(a) * 0.24, 0)) * k
            tip = base + np.array((math.cos(a), math.sin(a), 0.1)) * 0.17 * k
            one = round_cone(T(base), T(tip), 0.045 * k, 0.01 * k)
            spikes = one if spikes is None else spikes | one
        H.piece("ClubSpikes", bone, spikes, col=IRON, mat="metal", tris=400, role="weapon", pri=1.6)
    elif kind == "axe":
        H.piece("Haft", bone, capsule(at(0, 0.45), at(0, -1.25), 0.05 * k), col="wood", mat="wood", tris=300, role="weapon", pri=1.4)
        bl = plate([(0, 0.0), (0.12, 0.16), (0.48, 0.32), (0.56, 0.0), (0.48, -0.32), (0.12, -0.16)], at(0.04, -1.08), (0, 1, 0), (0, 0, 1), 0.035 * k)
        bl = bl.su(round_box(0.07 * k, 0.12 * k, 0.12 * k, 0.03 * k, at(0.0, -1.08)), 0.03 * k)
        H.piece("AxeHead", bone, bl, col="steel", mat="metal", tris=600, role="weapon", pri=1.5)
    elif kind == "spear":
        H.piece("Haft", bone, capsule(at(0, 1.1), at(0, -1.6), 0.045 * k), col="wood", mat="wood", tris=300, role="weapon", pri=1.4)
        tip = plate([(-0.09, 0), (0.09, 0), (0.02, 0.45), (0, 0.5), (-0.02, 0.45)], at(0, -1.58), (1, 0, 0), (0, 0, -1), 0.025 * k)
        tip = tip.su(round_cone(at(0, -1.5), at(0, -1.62), 0.06 * k, 0.05 * k), 0.02)
        H.piece("SpearTip", bone, tip, col="steel", mat="metal", tris=400, role="weapon", pri=1.5)
    elif kind == "trident" or kind == "pitchfork":
        H.piece("Haft", bone, capsule(at(0, 1.0), at(0, -1.5), 0.045 * k), col="darkWood" if kind == "pitchfork" else "gold", mat="wood" if kind == "pitchfork" else "metal", tris=300, role="weapon", pri=1.4)
        f = capsule(T(g + np.array((-0.2 * k, 0, -1.5 * k))), T(g + np.array((0.2 * k, 0, -1.5 * k))), 0.04 * k)
        for dx in (-0.2, 0.0, 0.2):
            f = f | round_cone(T(g + np.array((dx * k, 0, -1.5 * k))), T(g + np.array((dx * k, 0, -2.0 * k))), 0.04 * k, 0.012 * k)
        H.piece("Tines", bone, f, col="steel" if kind == "pitchfork" else "gold", mat="metal", tris=500, role="weapon", pri=1.5)
    elif kind == "sword":
        bl = plate([(-0.07, 0), (0.07, 0), (0.06, 1.25), (0, 1.4), (-0.06, 1.25)], at(0, -0.2), (1, 0, 0), (0, 0, -1), 0.022 * k)
        H.piece("Blade", bone, bl, col="steel", mat="metal", tris=300, role="weapon", pri=1.5, ao=False)
        hilt = capsule(at(0, 0.25), at(0, -0.12), 0.04 * k) | round_box(0.25 * k, 0.04 * k, 0.05 * k, 0.02 * k, at(0, -0.17)) | sphere(0.06 * k, at(0, 0.28))
        H.piece("Hilt", bone, hilt, col="gold", mat="metal", tris=400, role="weapon", pri=1.6)
    elif kind == "staff":
        sh = capsule(at(-0.9, 0.0), at(1.6, 0.0), 0.05 * k)
        H.piece("Staff", bone, tube([at(-1.2, 0.0), at(0.5, 0.0), at(1.7, 0.02), at(1.9, -0.12)], [0.05 * k, 0.055 * k, 0.06 * k, 0.05 * k], k=0.03).noise(0.008 * k, 15 / k, 1), col="wood", mat="wood", tris=500, role="weapon", pri=1.4)
        H.prim("Orb", bone, "Ball", (0.22 * k,) * 3, at(1.95, -0.05), col=P.get("orb", "gem"), mat="glass", glow=True, role="detail", pri=2.0)
    elif kind == "bow":
        pts = [at(1.0, -0.1), at(0.5, -0.25), at(0.0, -0.05), at(-0.5, -0.25), at(-1.0, -0.1)]
        H.piece("Bow", bone, tube(pts, [0.03 * k, 0.045 * k, 0.05 * k, 0.045 * k, 0.03 * k], k=0.03), col="wood", mat="wood", tris=500, role="weapon", pri=1.4)
        H.piece("String", bone, capsule(at(1.0, -0.1), at(-1.0, -0.1), 0.012 * k).round(0.0), col="white", mat="cloth", tris=150, role="weapon", pri=1.6, ao=False)
    elif kind == "scythe":
        H.piece("Haft", bone, tube([at(-0.6, 0.0), at(1.0, 0.02), at(2.2, -0.05)], [0.05 * k, 0.05 * k, 0.045 * k], k=0.02), col="darkWood", mat="wood", tris=400, role="weapon", pri=1.4)
        bl = plate([(0, 0), (0.12, 0.05), (0.5, 0.0), (1.0, -0.25), (1.3, -0.6), (0.95, -0.38), (0.45, -0.18), (0.05, -0.12)], at(2.1, -0.02), (0, 0, -1), (0, 1, 0), 0.02 * k)
        H.piece("ScytheBlade", bone, bl, col="steel", mat="metal", tris=500, role="weapon", pri=1.5, ao=False)


# ------------------------------------------------------------------------------------------------ finishing
def _finish(H, C, P, tail=(), wings=(), hair=(), jaw=True, mouth_bone=None):
    hs = C["hs"]
    hc = C["hc"]
    H.socket("mouth", T(hc + np.array((0, -0.25, -0.5)) * hs), "Jaw" if "Jaw" in H.bidx else "Head")
    H.socket("head", T(hc + np.array((0, 0.55, 0)) * hs), "Head")
    if "HandR" in H.bidx:
        H.socket("hand", T(C["grip"] if "grip" in C else C["Wr"]), "HandR")
    legs = [("HipR", "KneeR", "FootR", 0.0), ("HipL", "KneeL", "FootL", 0.5)]
    arms = [("ShoulderR", "ElbowR", "HandR", 1), ("ShoulderL", "ElbowL", "HandL", -1)]
    height = float(hc[1] + 0.5 * hs)
    H.rig.update({"head": "Head", "jaw": "Jaw" if "Jaw" in H.bidx else None, "tail": list(tail),
                  "legs": [{"hip": "HipR", "knee": "KneeR", "phase": 0.0, "side": 1}, {"hip": "HipL", "knee": "KneeL", "phase": 0.5, "side": -1}],
                  "arms": [{"shoulder": "ShoulderR", "elbow": "ElbowR", "side": 1}, {"shoulder": "ShoulderL", "elbow": "ElbowL", "side": -1}]})
    if H.rig["jaw"] is None:
        del H.rig["jaw"]
    return legs, arms, height


def _animate_biped(H, C, P, tail=(), wings=(), hair=()):
    legs, arms, height = _finish(H, C, P, tail, wings, hair)
    mm.biped_extra(H, legs, arms, spine="Spine", head="Head", jaw="Jaw" if "Jaw" in H.bidx else None, tail=tail,
                   stride=P["stride"], walk=P["walk"], height=height, attack=P["attack"], lean=P["lean"],
                   weapon_arm="ShoulderR" if P["weapon"] else None, shamble=P["shamble"], arms_out=P["arms_out"],
                   stomp=P["stomp"], wings=wings, hair=hair)
    return height


def _P(**kw):
    P = dict(BASE)
    face = dict(kw.pop("face", {}))
    P.update(kw)
    P["face"] = face
    return P


# ================================================================================================ heroes
@hero("goblin", "monsters")
def goblin():
    P = _P(s=0.8, leg=0.8, torso=0.85, W=0.78, arm=1.05, armT=0.72, legT=0.72, head=1.45, hunch=0.35, belly=0.25, muscle=0.2,
           hands="fist", feet="bare", foot=1.25, hand=1.15, weapon="club", attack="punch", stride=0.6, walk=0.75,
           face=dict(nose="pointy", ns=0.9, ears="goblin", es=1.1, brow=0.5, angry=0.8, jw=1.05, lips=0.6, mouthw=1.2, teeth=True,
                     cheek=0.7, iris=[0.95, 0.75, 0.1], eye=1.25),
           preview={"primary": "#65A30D", "secondary": "#92400E", "iris": "#E8C020"})
    H, C = _rig("goblin", P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    _legs(H, C, P)
    head, jaw, h, F = _head_human(H, C, P)
    _place_head(H, C, P, head, jaw, h, F)
    _belt(H, C, P, pel, col=LEATHER, buckle=False, loin="secondary")
    _tunic(H, C, P, rib, pel, col="secondary", lo=C["waist"][1] - 0.2 * C["s"], hi=C["Sh"][1] + 0.4 * C["s"], name="Vest", off=0.04)
    P["wscale"] = 0.75
    _weapon(H, C, P, "club")
    _animate_biped(H, C, P)
    return H


@hero("orc", "monsters")
def orc():
    P = _P(s=1.05, leg=0.95, torso=1.05, W=1.25, arm=1.0, armT=1.35, legT=1.25, head=1.0, hunch=0.18, muscle=0.9,
           hands="fist", feet="boot", weapon="axe", attack="punch", stride=0.5, walk=1.0, stomp=0.5,
           face=dict(nose="pig", ns=1.0, ears="pointed", es=0.8, brow=1.0, angry=1.0, jw=1.25, under=1.0, tusks=0.9, chin=1.3,
                     cheek=0.8, iris=[0.85, 0.2, 0.1]),
           preview={"primary": "#4D7C0F", "secondary": "#57534E", "iris": "#D03020"})
    H, C = _rig("orc", P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    _legs(H, C, P, foot_col=DLEATHER)
    head, jaw, h, F = _head_human(H, C, P)
    _place_head(H, C, P, head, jaw, h, F)
    _hair(H, C, "mohawk", col="black")
    _belt(H, C, P, pel, col=DLEATHER, loin="secondary")
    _tunic(H, C, P, rib, pel, col="secondary", lo=C["hipY"] - 0.45 * C["s"], hi=C["hipY"] + 0.25 * C["s"], name="Kilt", bone="Body", off=0.07)
    _weapon(H, C, P, "axe")
    _animate_biped(H, C, P)
    return H


@hero("ogre", "monsters")
def ogre():
    P = _P(s=1.3, leg=0.72, torso=1.1, W=1.55, arm=1.08, armT=1.7, legT=1.6, head=0.82, hunch=0.3, belly=1.0, muscle=0.3, depth=1.2,
           hands="fist", feet="big", foot=1.2, weapon="club", attack="slam", stride=0.38, walk=1.25, stomp=1.0, neck=0.5,
           face=dict(nose="human", ns=1.6, ears="human", es=1.4, brow=0.9, angry=0.4, jw=1.45, jl=1.2, under=0.6, tusks=0.4, chin=1.2,
                     cheek=1.0, eye=0.75, lips=1.0, mouthw=1.3),
           preview={"primary": "#9DB85A", "secondary": "#78350F", "iris": "#6B4A20"})
    H, C = _rig("ogre", P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    _legs(H, C, P)
    head, jaw, h, F = _head_human(H, C, P)
    _place_head(H, C, P, head, jaw, h, F)
    _belt(H, C, P, pel, col=ROPE, buckle=False)
    _tunic(H, C, P, rib, pel, col="secondary", lo=C["hipY"] - 0.5 * C["s"], hi=C["hipY"] + 0.3 * C["s"], name="Loincloth", bone="Body", off=0.06)
    P["wscale"] = 1.15
    _weapon(H, C, P, "club")
    _animate_biped(H, C, P)
    return H


@hero("troll", "monsters")
def troll():
    P = _P(s=1.2, leg=0.85, torso=1.0, W=1.15, arm=1.4, armT=1.2, legT=1.1, head=0.95, hunch=0.65, belly=0.35, muscle=0.4,
           hands="open", claws=True, feet="claw", foot=1.2, hand=1.35, attack="slam", stride=0.45, walk=1.2, stomp=0.6, neck=0.6,
           face=dict(nose="long", ns=1.25, ears="pointed", es=1.2, brow=1.0, angry=0.3, jw=1.15, under=0.5, tusks=0.5, cheek=0.6, eye=0.8,
                     lips=0.8, iris=[0.95, 0.8, 0.2]),
           skin_pattern=spots(0.35, 0.12, depth=0.25, seed=3),
           preview={"primary": "#6E7E5A", "secondary": "#4A5E2E", "iris": "#E8C020"})
    H, C = _rig("troll", P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    _legs(H, C, P)
    head, jaw, h, F = _head_human(H, C, P)
    _place_head(H, C, P, head, jaw, h, F)
    _hair(H, C, "long", col="secondary")
    _tunic(H, C, P, rib, pel, col=LEATHER, lo=C["hipY"] - 0.4 * C["s"], hi=C["hipY"] + 0.2 * C["s"], name="Loincloth", bone="Body", off=0.06)
    _animate_biped(H, C, P)
    return H



# ------------------------------------------------------------------------------------------------ extra kit
def _face_mask(H, C, head, col, region_c, region_r, name="Face"):
    """Coloured face / muzzle patch: the head grown a hair and cut to a sphere region (never coplanar)."""
    s = C["s"]
    m = head.round(0.012 * s) & sphere(region_r, T(region_c))
    H.piece(name, "Head", m, col=col, mat="skin", tris=900, role="face", pri=1.25)


def _shield(H, C, P, col="wood", rim=IRON):
    s = C["s"]
    g = C["grip"].copy()
    g[0] = -g[0]
    c = g + np.array((-0.12 * s, 0.0, 0.0))
    disk = cylinder(0.5 * s, 0.04 * s, axis=0, rr=0.02 * s).at(*T(c))
    disk = disk.su(sphere(0.12 * s, T(c + np.array((-0.06 * s, 0, 0)))), 0.03 * s)
    H.piece("Shield", "HandL", disk, col=col, mat="wood", tris=500, role="shield", pri=1.4)
    H.piece("ShieldRim", "HandL", torus(0.5 * s, 0.045 * s, axis=0).at(*T(c)), col=rim, mat="metal", tris=400, role="shield", pri=1.5)


def _fins(H, C, col="secondary"):
    s, v = C["s"], C["v"]
    ch = C["chest"]
    back = plate([(-0.5, 0), (-0.3, 0.3), (0.0, 0.42), (0.3, 0.38), (0.6, 0.12), (0.75, -0.25), (0.4, -0.15), (0.0, -0.1)],
                 T(ch + v(0, 0.25, 0.3)), (0, -0.85, 0.5), (0, 0.5, 0.85), 0.03 * s)
    H.piece("BackFin", "Spine", back, col=col, mat="skin", tris=500, role="fin", pri=1.3)
    for sx, nm in ((1, "R"), (-1, "L")):
        El, Wr = C["El"].copy(), C["Wr"].copy()
        El[0] *= sx
        Wr[0] *= sx
        f = plate([(0, 0), (0.55, 0.0), (0.45, 0.22), (0.1, 0.15)], T(El + (Wr - El) * 0.15 + v(0.05 * sx, 0, 0.06)), T(Wr - El), (0, 0, 1), 0.025 * s)
        H.piece("ArmFin" + nm, "Elbow" + nm, f, col=col, mat="skin", tris=250, role="fin", pri=1.4, key=f"h_{H.id}_armfin{'' if sx > 0 else '_l'}".replace(" ", "_"))


def _skeleton_body(H, C, P):
    v, s = C["v"], C["s"]
    col, W = P["skin"], P["W"]
    ch, wa, Sh, nb, hp = C["chest"], C["waist"], C["Sh"], C["neckB"], C["headP"]
    y0 = ch[1]
    rc = ellipsoid(0.42 * W * s, 0.5 * s, 0.32 * s, T(ch + v(0, 0.02, 0.0)))
    shell = rc.shell(0.032 * s)
    ribs = shell & SDF(lambda p: (np.abs(np.sin((p[:, 1] - y0) / s * np.pi / 0.14)) - 0.5) * 0.06 * s)
    ribs = ribs & plane((0, -1, 0), -(y0 - 0.4 * s))
    ribs = ribs - ellipsoid(0.2 * s, 0.32 * s, 0.4 * s, T(ch + v(0, -0.42, -0.3)))
    ribs = ribs - box(0.06 * s, 0.6 * s, 0.2 * s, T(ch + v(0, -0.1, -0.3)))
    ribs = ribs | capsule(T(ch + v(0, 0.42, -0.31)), T(ch + v(0, -0.12, -0.31)), 0.045 * s)
    ribs = ribs | capsule(T(ch + v(0.05, 0.43, -0.3)), T(Sh + v(-0.08, 0.02, -0.04)), 0.04 * s).mirror_x()
    ribs = ribs | ellipsoid(0.2 * s, 0.25 * s, 0.04 * s, T(ch + v(0.25, 0.15, 0.33))).mirror_x()
    ribs = ribs | sphere(0.09 * s, T(Sh + v(-0.04, 0, 0))).mirror_x()
    sp = None
    a0, a1 = wa + v(0, -0.15, 0.2), hp + v(0, 0.05, 0.06)
    for i in range(10):
        t = i / 9
        c = a0 + (a1 - a0) * t + v(0, 0, 0.08 * math.sin(t * math.pi))
        one = round_box(0.07 * s, 0.045 * s, 0.06 * s, 0.02 * s, T(c)) | round_cone(T(c), T(c + v(0, -0.04, 0.09)), 0.03 * s, 0.015 * s)
        sp = one if sp is None else sp | one
    sp = sp | capsule(T(a0), T(a1), 0.03 * s)
    H.piece("Ribcage", "Spine", ribs | sp, col=col, mat="hard", tris=2400, res=144, role="body")
    Hp = C["Hip"]
    py = C["hipY"]
    pel = ellipsoid(0.24 * s, 0.2 * s, 0.07 * s, T(np.array((0.2 * s, py + 0.18 * s, 0.03 * s)))).rot(0, 0, 0)
    pel = pel.shell(0.025 * s).su(ellipsoid(0.24 * s, 0.2 * s, 0.07 * s, T(np.array((0.2 * s, py + 0.18 * s, 0.03 * s)))) & SDF(lambda p: 0.02 * s - np.abs(p[:, 2] - 0.03 * s)), 0.01)
    pel = pel.mirror_x() | ellipsoid(0.1 * s, 0.16 * s, 0.07 * s, T(np.array((0, py + 0.12 * s, 0.12 * s))))
    pel = pel | torus(0.17 * s, 0.035 * s).rot(70, 0, 0).at(0, py - 0.02 * s, -0.04 * s)
    pel = pel | sphere(0.075 * s, T(Hp)).mirror_x()
    lum = None
    for i in range(4):
        c = np.array((0, py + 0.3 * s + i * 0.12 * s, 0.17 * s))
        one = round_box(0.08 * s, 0.045 * s, 0.07 * s, 0.02 * s, T(c))
        lum = one if lum is None else lum | one
    H.piece("PelvisBone", "Body", pel | lum | capsule(T(np.array((0, py + 0.25 * s, 0.17 * s))), T(wa + v(0, -0.05, 0.2)), 0.03 * s), col=col, mat="hard", tris=1500, res=128)

    def lbone(a, b, r, ka=1.6, kb=1.4):
        return capsule(T(a), T(b), r).su(sphere(r * ka, T(a)), 0.03 * s).su(sphere(r * kb, T(b)), 0.03 * s)

    El, Wr, Kn, An = C["El"], C["Wr"], C["Knee"], C["Ank"]
    H.mpiece("Humerus#", "Shoulder#", lbone(Sh + v(0, -0.05, 0), El, 0.045 * s), col=col, mat="hard", tris=400, role="limb")
    fo = capsule(T(El + v(0.025, 0, 0)), T(Wr + v(0.025, 0, 0)), 0.03 * s) | capsule(T(El + v(-0.025, 0, 0.02)), T(Wr + v(-0.02, 0, 0.02)), 0.028 * s) | sphere(0.055 * s, T(El)) | sphere(0.05 * s, T(Wr))
    H.mpiece("Radius#", "Elbow#", fo, col=col, mat="hard", tris=400, role="limb")
    _hand(H, C, dict(P, hands="bone"), col)
    H.mpiece("Femur#", "Hip#", lbone(Hp + v(0, 0.02, 0), Kn, 0.055 * s, 1.5, 1.6), col=col, mat="hard", tris=450, role="limb")
    sh_ = capsule(T(Kn), T(An + v(0, 0.05, 0)), 0.045 * s) | capsule(T(Kn + v(0.05, -0.05, 0.03)), T(An + v(0.05, 0.06, 0.02)), 0.025 * s)
    sh_ = sh_ | sphere(0.07 * s, T(Kn + v(0, 0, -0.05))) | sphere(0.06 * s, T(An + v(0, 0.04, 0)))
    H.mpiece("Tibia#", "Knee#", sh_, col=col, mat="hard", tris=400, role="limb")
    ft = sphere(0.07 * s, T(An + v(0, -0.15, 0.06)))
    for i, dx in enumerate((-0.07, -0.025, 0.02, 0.065)):
        ft = ft | tube([T(An + v(0, -0.12, 0.0)), T(An + v(dx, -0.2, -0.2)), T(An + v(dx * 1.1, -0.25, -0.38))], [0.03 * s, 0.025 * s, 0.022 * s], k=0.01)
    H.mpiece("FootBone#", "Foot#", ft & plane((0, -1, 0), 0.0), col=col, mat="hard", tris=450, role="foot")


def _mane(H, C, P, col=None, size=1.0):
    """Shaggy fur mane over the shoulders / chest (werewolf, yeti)."""
    v, s = C["v"], C["s"]
    col = col or P["skin"]
    ch, Sh, nb = C["chest"], C["Sh"], C["neckB"]
    m = ellipsoid(0.62 * P["W"] * s * size, 0.38 * s, 0.45 * s * size, T(nb + v(0, -0.12, 0.08)))
    rng = np.random.default_rng(3)
    for i in range(16):
        a = rng.uniform(0, math.tau)
        c0 = nb + v(0.45 * math.cos(a) * P["W"] * size, -0.15 + 0.15 * math.sin(a * 2), 0.35 * math.sin(a) * size + 0.05)
        tip = c0 + v(0.25 * math.cos(a), -0.32, 0.25 * math.sin(a) + 0.1)
        m = m.su(round_cone(T(c0), T(tip), 0.13 * s, 0.03 * s), 0.05)
    m = m.su(ellipsoid(0.35 * s * size, 0.4 * s, 0.2 * s, T(ch + v(0, 0.15, -0.3))).noise(0.03 * s, 9 / s, 2), 0.1)
    H.piece("Mane", "Spine", m.noise(0.025 * s, 11 / s, 5), col=col, mat="skin", tris=1600, res=128, role="fur", pri=1.15)


def _tuft_tail(H, C, P, col=None, tuft_col=None, length=1.0, bushy=False):
    s = C["s"]
    col = col or P["skin"]
    root = np.array((0, C["hipY"] + 0.05 * s, 0.32 * s))
    p1 = root + np.array((0, -0.35, 0.45)) * s * length
    p2 = p1 + np.array((0, -0.55, 0.3)) * s * length
    H.bone("Tail1", "Body", T(root))
    H.bone("Tail2", "Tail1", T(p1))
    if bushy:
        a = ellipsoid(0.18 * s, 0.18 * s, 0.4 * s * length, T((root + p1) / 2)).rot(0, 0, 0).noise(0.03 * s, 10 / s, 2)
        a = a.su(round_cone(T(root), T(p1), 0.14 * s, 0.2 * s), 0.08)
        b = round_cone(T(p1), T(p2), 0.22 * s, 0.08 * s).noise(0.035 * s, 10 / s, 3)
        H.piece("TailP1", "Tail1", a, col=col, mat="skin", tris=600, role="tail", pri=1.5)
        H.piece("TailP2", "Tail2", b, col=tuft_col or col, mat="skin", tris=600, role="tail", pri=1.6)
    else:
        H.piece("TailP1", "Tail1", round_cone(T(root), T(p1), 0.05 * s, 0.04 * s), col=col, mat="skin", tris=250, role="tail", pri=1.5)
        b = round_cone(T(p1), T(p2), 0.04 * s, 0.035 * s).su(ellipsoid(0.11 * s, 0.22 * s, 0.11 * s, T(p2 + np.array((0, -0.08, 0.02)) * s)).noise(0.02 * s, 12 / s, 4), 0.04 * s)
        H.piece("TailP2", "Tail2", b, col=tuft_col or col, mat="skin", tris=450, role="tail", pri=1.6)
    return ["Tail1", "Tail2"]


def _strips(H, C, col, n=3, bone_side="R", seed=1):
    """Loose hanging bandage strips from the forearms (mummy)."""
    s, v = C["s"], C["v"]
    rng = np.random.default_rng(seed)
    for sx, nm in ((1, "R"), (-1, "L")):
        El, Wr = C["El"].copy(), C["Wr"].copy()
        El[0] *= sx
        Wr[0] *= sx
        out = None
        for i in range(2):
            c = El + (Wr - El) * (0.35 + 0.35 * i) + v(0.08 * sx, 0, 0.08)
            ln = rng.uniform(0.35, 0.6)
            one = plate([(-0.06, 0), (0.06, 0), (0.05, -ln), (-0.01, -ln - 0.06), (-0.05, -ln)], T(c), (0, 0, 1), (0.25 * sx, 1, 0), 0.018 * s)
            out = one if out is None else out | one
        H.piece("Strip" + nm, "Elbow" + nm, out, col=col, mat="cloth", tris=300, role="cloth", pri=1.6, key=f"h_{H.id}_strip{'' if sx > 0 else '_l'}")


# ================================================================================================ more heroes
@hero("cyclops", "monsters")
def cyclops():
    P = _P(s=1.4, leg=0.95, torso=1.1, W=1.45, arm=1.1, armT=1.6, legT=1.5, head=1.05, hunch=0.25, belly=0.45, muscle=0.7, depth=1.1,
           hands="fist", feet="bare", foot=1.2, weapon="club", attack="slam", stride=0.38, walk=1.3, stomp=1.0, neck=0.7,
           face=dict(one_eye=True, nose="human", ns=1.3, ears="human", es=1.3, brow=1.2, angry=0.6, jw=1.25, chin=1.3, cheek=0.8, eye=1.0,
                     lips=0.7, teeth=True, iris=[0.35, 0.55, 0.2]),
           preview={"primary": "#C08A5A", "secondary": "#7A5A3A", "iris": "#5A8A30", "hair": "#3A2A1C"})
    H, C = _rig("cyclops", P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    _legs(H, C, P)
    head, jaw, h, F = _head_human(H, C, P)
    head = head.su(round_cone(h(0, 0.42, -0.3), h(0, 0.62, -0.32), 0.09 * C["hs"], 0.02 * C["hs"]), 0.04)
    _place_head(H, C, P, head, jaw, h, F)
    _beard(H, C, "short", col="hair", bone="Jaw")
    _hair(H, C, "topknot", col="hair")
    _belt(H, C, P, pel, col=DLEATHER, buckle=False)
    g = _tunic(H, C, P, rib, pel, col="secondary", lo=C["hipY"] - 0.55 * C["s"], hi=C["hipY"] + 0.3 * C["s"], name="FurKilt", bone="Body", off=0.08)
    P["wscale"] = 1.25
    _weapon(H, C, P, "club")
    _animate_biped(H, C, P)
    return H


@hero("minotaur", "monsters")
def minotaur():
    P = _P(s=1.3, leg=1.0, torso=1.1, W=1.5, arm=1.0, armT=1.6, legT=1.4, head=1.15, hunch=0.25, muscle=1.0, depth=1.1, digi=True,
           hands="fist", feet="hoof", weapon="axe", attack="slam", stride=0.45, walk=1.1, stomp=0.8, neck=0.6, fur=0.012,
           face=dict(iris=[0.85, 0.15, 0.1]),
           preview={"primary": "#7C3D1E", "secondary": "#E7E5E4", "horn": "#EFE3C8"})
    H, C = _rig("minotaur", P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    _legs(H, C, P)
    _snout_head(H, C, P, "bull", mz=1.0, es=1.0)
    _horns(H, C, "bull", size=1.0)
    _mane(H, C, P, size=0.85)
    _belt(H, C, P, pel, col=DLEATHER)
    _tunic(H, C, P, rib, pel, col=LEATHER, lo=C["hipY"] - 0.4 * C["s"], hi=C["hipY"] + 0.25 * C["s"], name="Kilt", bone="Body", off=0.09)
    tail = _tuft_tail(H, C, P, tuft_col="dark")
    P["wscale"] = 1.3
    _weapon(H, C, P, "axe")
    _animate_biped(H, C, P, tail=tail)
    return H


@hero("satyr", "monsters")
def satyr():
    P = _P(s=0.95, leg=1.0, torso=0.95, W=0.95, arm=0.95, armT=0.95, legT=1.05, head=1.05, muscle=0.6, digi=True, skin="skin",
           hands="open", feet="hoof", attack="punch", stride=0.6, walk=0.8,
           face=dict(nose="human", ears="pointed", es=1.0, brow=0.4, cheek=0.7, jaw=False, iris=[0.75, 0.55, 0.2]),
           preview={"primary": "#8A5A30", "secondary": "#5B7A1E", "skin": "#E8B68A", "hair": "#4A2E1A"})
    H, C = _rig("satyr", P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    Pf = dict(P, fur=0.035, skin="primary")
    _legs(H, C, Pf)
    H.piece("FurHips", "Body", _fur(Pf, pel.round(0.06 * C["s"]) & slab_y(C["hipY"] - 0.5 * C["s"], C["waist"][1] - 0.15 * C["s"]), 1.3), col="primary", mat="skin", tris=1200, role="fur", pri=1.1)
    head, jaw, h, F = _head_human(H, C, P)
    _place_head(H, C, P, head, jaw, h, F)
    _hair(H, C, "wild", col="hair")
    _beard(H, C, "goatee", col="hair")
    _horns(H, C, "ram", size=0.85)
    tail = _tuft_tail(H, C, P, col="primary", length=0.6)
    leaves = None
    for i in range(9):
        a = (i / 9) * math.tau
        c = C["hc"] + np.array((0.43 * math.cos(a), 0.32, 0.45 * math.sin(a) + 0.05)) * C["hs"]
        one = ellipsoid(0.11 * C["hs"], 0.04 * C["hs"], 0.16 * C["hs"], T(c)).rot(0, 0, 0)
        leaves = one if leaves is None else leaves | one
    H.piece("Wreath", "Head", leaves | torus(0.44 * C["hs"], 0.03 * C["hs"]).at(*h(0, 0.32, 0.05)), col="secondary", mat="leaf", tris=700, role="hat", pri=1.4)
    _animate_biped(H, C, P, tail=tail)
    return H


@hero("demon", "monsters")
def demon():
    P = _P(s=1.35, leg=1.0, torso=1.1, W=1.45, arm=1.05, armT=1.45, legT=1.35, head=1.0, hunch=0.2, muscle=1.0, depth=1.05, digi=True,
           hands="open", claws=True, feet="hoof", attack="slam", stride=0.45, walk=1.05, stomp=0.6,
           face=dict(nose="human", ns=0.9, ears="pointed", es=1.1, brow=1.0, angry=1.0, jw=1.15, chin=1.2, cheek=0.9, fangs=0.9, teeth=True,
                     iris=[1.0, 0.75, 0.1], glow=True, sclera=None, pupil=False),
           preview={"primary": "#9B1C1C", "secondary": "#2A1A1A", "horn": "#2B2622"})
    H, C = _rig("demon", P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    _legs(H, C, dict(P, skin="secondary"))
    head, jaw, h, F = _head_human(H, C, P)
    _place_head(H, C, P, head, jaw, h, F)
    _horns(H, C, "demon", col="horn", size=1.1)
    wings = _bat_wings(H, C, P, span=1.45, col="secondary")
    tail = _tail(H, C, P, "devil", length=1.3)
    _belt(H, C, P, pel, col=IRON, buckle=False, loin="secondary")
    _animate_biped(H, C, P, tail=tail, wings=wings)
    return H


@hero("imp", "monsters")
def imp():
    P = _P(s=0.75, leg=0.75, torso=0.85, W=0.8, arm=0.95, armT=0.75, legT=0.75, head=1.5, hunch=0.15, belly=0.3, muscle=0.2, digi=True,
           hands="fist", feet="paw", foot=0.9, gait="hover", weapon="pitchfork",
           face=dict(nose="pointy", ns=0.55, ears="goblin", es=0.75, brow=0.6, angry=0.7, cheek=0.8, jw=1.1, lips=0.4, mouthw=1.3, fangs=0.7,
                     teeth=True, iris=[1.0, 0.8, 0.15], eye=1.25),
           preview={"primary": "#D02A22", "secondary": "#1F2937", "horn": "#2B2622"})
    H, C = _rig("imp", P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    _legs(H, C, P)
    head, jaw, h, F = _head_human(H, C, P)
    _place_head(H, C, P, head, jaw, h, F)
    _horns(H, C, "devil", col="horn", size=0.9)
    wings = _bat_wings(H, C, P, span=1.0, col="secondary")
    tail = _tail(H, C, P, "devil", length=0.9)
    P["wscale"] = 0.75
    _weapon(H, C, P, "pitchfork")
    legs, arms, height = _finish(H, C, P, tail)
    H.rig["gait"] = "hover"
    mm.hoverer(H, wings, arms=arms, legs=[(a, b, c, 1 if i == 0 else -1) for i, (a, b, c, _) in enumerate(legs)], spine="Spine", head="Head", jaw="Jaw",
               tail=tail, height=height, rate=1.6, amp=0.6, weapon_arm="ShoulderR")
    return H


@hero("werewolf", "monsters")
def werewolf():
    P = _P(s=1.25, leg=1.0, torso=1.05, W=1.35, arm=1.15, armT=1.4, legT=1.3, head=1.05, hunch=0.55, muscle=0.9, depth=1.1, digi=True,
           hands="open", claws=True, hand=1.25, feet="paw", foot=1.15, attack="slam", stride=0.55, walk=0.9, lean=0.1, fur=0.03,
           face=dict(iris=[0.95, 0.75, 0.15], glow=False),
           preview={"primary": "#6B655E", "secondary": "#3A4A6A", "dark": "#1E1C1B", "iris": "#F0C030"})
    H, C = _rig("werewolf", P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    _legs(H, C, P)
    _snout_head(H, C, P, "wolf", mz=1.05, es=1.0)
    _mane(H, C, P, size=1.0)
    _tunic(H, C, P, rib, pel, col="secondary", lo=C["hipY"] - 0.5 * C["s"], hi=C["hipY"] + 0.2 * C["s"], name="TornPants", bone="Body", off=0.08)
    tail = _tuft_tail(H, C, P, length=1.1, bushy=True)
    _animate_biped(H, C, P, tail=tail)
    return H


@hero("lizardman", "monsters")
def lizardman():
    P = _P(s=1.05, leg=0.95, torso=1.0, W=1.05, arm=1.0, armT=1.05, legT=1.15, head=1.0, hunch=0.3, muscle=0.6, digi=False,
           hands="fist", feet="claw", foot=1.15, weapon="spear", attack="punch", stride=0.5, walk=0.95, lean=0.05,
           skin_pattern=combine(spots(0.16, 0.06, depth=0.3, seed=4), gradient(1, 2.5, 4.5, 1.0, 0.85)),
           face=dict(iris=[0.95, 0.65, 0.1]),
           preview={"primary": "#4D7C0F", "secondary": "#E0B040", "iris": "#E8A020"})
    H, C = _rig("lizardman", P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    _legs(H, C, P)
    _snout_head(H, C, P, "lizard", mz=1.0)
    belly = (rib.round(0.025 * C["s"]) & SDF(lambda p, z0=C["chest"][2]: p[:, 2] - (z0 - 0.12 * C["s"])) & slab_y(C["waist"][1] - 0.4 * C["s"], C["chest"][1] + 0.35 * C["s"]))
    belly = belly & SDF(lambda p: np.abs(p[:, 0]) - 0.32 * C["s"])
    H.piece("BellyScales", "Spine", SDF(lambda p, b=belly: b(p)) , col="secondary", mat="skin", tris=800, role="belly", pri=1.2,
            pattern=stripes(lambda Q: Q[:, 1] / C["s"], 7.0, width=0.18, depth=0.35))
    tail = _tail(H, C, P, "lizard", length=1.1)
    _belt(H, C, P, pel, col=LEATHER, loin=LEATHER)
    _weapon(H, C, P, "spear")
    _animate_biped(H, C, P, tail=tail)
    return H


@hero("fishman", "monsters")
def fishman():
    P = _P(s=1.0, leg=0.9, torso=1.0, W=1.05, arm=1.05, armT=0.95, legT=1.0, head=1.15, hunch=0.45, belly=0.25, muscle=0.4,
           hands="open", claws=True, hand=1.2, feet="claw", foot=1.2, attack="slam", stride=0.45, walk=0.95, shamble=0.4,
           skin_pattern=combine(spots(0.12, 0.05, depth=0.25, ring=True, seed=8), gradient(1, 1.5, 4.0, 1.0, 0.8)),
           face=dict(iris=[0.95, 0.85, 0.3]),
           preview={"primary": "#1F8A80", "secondary": "#A3E635", "iris": "#E8D040"})
    H, C = _rig("fishman", P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    _legs(H, C, P)
    _snout_head(H, C, P, "fish")
    _fins(H, C)
    _belt(H, C, P, pel, col=[0.35, 0.45, 0.25], buckle=False, loin=[0.3, 0.42, 0.22])
    _animate_biped(H, C, P)
    return H


@hero("alien", "monsters")
def alien():
    P = _P(s=0.95, leg=0.95, torso=0.85, W=0.72, arm=1.1, armT=0.55, legT=0.55, head=1.55, neck=1.1, muscle=0.0,
           hands="open", hand=1.25, feet="bare", attack="punch", stride=0.45, walk=0.9, antenna=True,
           preview={"primary": "#8FD18A", "secondary": "#2E3440"})
    H, C = _rig("alien", P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    _legs(H, C, P)
    _alien_head(H, C, P)
    _tunic(H, C, P, rib, pel, col="secondary", lo=C["hipY"] - 0.3 * C["s"], hi=C["Sh"][1] + 0.35 * C["s"], name="Suit", off=0.035)
    H.prim("Badge", "Spine", "Ball", (0.22, 0.22, 0.08), T(_front(rib, C["chest"][1] + 0.1 * C["s"], C["s"]) + np.array((0.0, C["chest"][1] + 0.1 * C["s"], -0.05))),
           col="gem", mat="glass", glow=True, role="detail", pri=2.0)
    _belt(H, C, P, pel, col="metal", buckle=True)
    _animate_biped(H, C, P)
    return H


@hero("mummy", "monsters")
def mummy():
    wrap = combine(_wrap_pat(13.0), stripes(lambda Q: Q[:, 1] - 0.4 * Q[:, 0], 4.0, width=0.08, depth=0.2, seed=3))
    P = _P(s=1.0, leg=1.0, torso=1.0, W=0.95, arm=1.0, armT=0.9, legT=0.95, head=1.0, hunch=0.15, muscle=0.1, skinmat="cloth", wrap=0.055,
           hands="open", feet="bare", attack="slam", stride=0.3, walk=1.3, shamble=1.0, arms_out=1.2, skin_pattern=wrap,
           face=dict(nose="human", ns=0.6, ears="none", brow=0.5, jaw=False, eye=0.8, iris=[0.3, 0.95, 0.85], glow=True, sclera=None, pupil=False),
           preview={"primary": "#D6CFB8", "secondary": "#A16207"})
    H, C = _rig("mummy", P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    _legs(H, C, P)
    head, jaw, h, F = _head_human(H, C, P)
    head = head.ss(capsule(h(-0.25, 0.03, -0.38), h(0.25, 0.03, -0.38), 0.06 * C["hs"]), 0.03)
    head = _wrap(head, 0.045 * C["hs"], 13.0 / C["hs"])
    _place_head(H, C, P, head, jaw, h, F)
    H.prim("EyeSlit", "Head", "Ellipsoid", (0.5 * C["hs"], 0.1 * C["hs"], 0.1 * C["hs"]), h(0, 0.03, -0.34), col="black", mat="hard", role="eye", pri=1.25)
    _strips(H, C, "primary")
    _belt(H, C, P, pel, col=[0.7, 0.64, 0.5], buckle=False, loin=[0.62, 0.56, 0.42])
    H.prim("Amulet", "Spine", "Ellipsoid", (0.22, 0.28, 0.08), T(_front(rib, C["chest"][1] + 0.2, 1.0) + np.array((0, C["chest"][1] + 0.2, -0.03))), col="gold", mat="metal", role="detail", pri=2.0)
    _animate_biped(H, C, P)
    return H


@hero("skeleton", "monsters")
def skeleton():
    P = _P(s=1.0, leg=1.0, torso=1.0, W=0.95, arm=1.0, armT=1.0, legT=1.0, head=1.05, hunch=0.05, hands="fist", weapon="sword",
           attack="punch", stride=0.55, walk=0.85, eyeglow=[1.0, 0.35, 0.2],
           preview={"primary": "#EDE8DA", "secondary": "#6B5A40"})
    H, C = _rig("skeleton", P)
    _skeleton_body(H, C, P)
    _hand(H, C, dict(P, hands="fist"), P["skin"]) if False else None
    C["grip"] = C["Wr"] + C["v"](-0.02, -0.25, -0.02)
    _skull_head(H, C, P)
    _weapon(H, C, P, "sword")
    _shield(H, C, P, col="secondary")
    _animate_biped(H, C, P)
    return H


def _ape_man(hid, P, crest=False, face_col=None, horns=None, mop=False):
    H, C = _rig(hid, P)
    rib, pel = _torso(H, C, P)
    _arms(H, C, P)
    _legs(H, C, P)
    h = _snout_head(H, C, P, "ape", mz=0.9, es=0.8)
    _mane(H, C, P, size=1.05)
    if crest:
        hs = C["hs"]
        cr = round_cone(h(0, 0.4, -0.15), h(0, 0.72, 0.15), 0.22 * hs, 0.1 * hs).su(ellipsoid(0.25 * hs, 0.3 * hs, 0.35 * hs, h(0, 0.4, 0.2)), 0.1)
        H.piece("Crest", "Head", _fur(P, cr, 0.6), col=P["skin"], mat="skin", tris=600, role="head", pri=1.2)
    if mop:
        hs = C["hs"]
        mp = ellipsoid(0.5 * hs, 0.3 * hs, 0.5 * hs, h(0, 0.38, 0.0)).su(ellipsoid(0.42 * hs, 0.12 * hs, 0.2 * hs, h(0, 0.24, -0.36)), 0.12)
        mp = mp.su(ellipsoid(0.12 * hs, 0.32 * hs, 0.3 * hs, h(0.46, 0.05, 0.05)).mirror_x(), 0.12)
        H.piece("Mop", "Head", _fur(P, mp, 1.1), col=P["skin"], mat="skin", tris=800, role="hair", pri=1.2)
    if face_col is not None:
        hs = C["hs"]
        face = ellipsoid(0.3 * hs, 0.32 * hs, 0.2 * hs, h(0, -0.05, -0.35)).su(ellipsoid(0.24 * hs, 0.2 * hs, 0.2 * hs, h(0, -0.22, -0.42)), 0.1)
        face = face.su(capsule(h(-0.25, 0.1, -0.36), h(0.25, 0.1, -0.36), 0.085 * hs), 0.05)
        face = face.ss(sphere(0.095 * hs, h(0.13, 0.02, -0.37)).mirror_x(), 0.03)
        face = face.ss(box(0.4 * hs, 0.2 * hs, 0.3 * hs, h(0, -0.47, -0.4)), 0.03)
        H.piece("Face", "Head", face, col=face_col, mat="skin", tris=900, role="face", pri=1.25)
    return H, C


@hero("yeti", "monsters")
def yeti():
    P = _P(s=1.35, leg=0.85, torso=1.1, W=1.5, arm=1.25, armT=1.55, legT=1.45, head=1.35, hunch=0.35, belly=0.2, muscle=0.5, depth=1.15,
           hands="open", claws=True, hand=1.35, feet="big", foot=1.35, attack="slam", stride=0.38, walk=1.2, stomp=0.9, fur=0.05, neck=0.8,
           face=dict(iris=[0.4, 0.7, 0.95]),
           preview={"primary": "#EEF2F6", "secondary": "#93C5FD"})
    H, C = _ape_man("yeti", P, face_col=[0.55, 0.65, 0.78], mop=True)
    _animate_biped(H, C, P)
    return H


@hero("bigfoot", "monsters")
def bigfoot():
    P = _P(s=1.25, leg=1.05, torso=1.05, W=1.25, arm=1.15, armT=1.3, legT=1.3, head=1.25, hunch=0.2, muscle=0.6, depth=1.05,
           hands="open", hand=1.25, feet="big", foot=1.55, attack="slam", stride=0.62, walk=1.05, lean=0.05, fur=0.04, neck=0.8,
           face=dict(iris=[0.45, 0.3, 0.15]),
           preview={"primary": "#5A3A22", "secondary": "#A16207"})
    H, C = _ape_man("bigfoot", P, crest=True, face_col=[0.28, 0.22, 0.2])
    _animate_biped(H, C, P)
    return H
