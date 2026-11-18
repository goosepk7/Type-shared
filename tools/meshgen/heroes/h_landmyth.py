"""Land myths, cryptids, prehistoric oddities and eldritch things (family "landmyth").

* Bird-folk: harpy, harpy queen, harpy archer (a woman's torso and fierce face, big feathered wings for arms or on the
  back, feathered hips, scaly bird legs with talons, a feather crest and tail fan; hover + dive-claw), sirin (a big bird
  body with a crowned human head: sirin, alkonost, gamayun), tengu (long-nosed winged mountain goblin in robes on
  tall sandals with a feather fan) and kenku (hooded crow-headed wanderer with a staff).
* Cryptids: chupacabra, jersey devil, displacer beast (a six-legged panther with two shoulder tentacles), hodag,
  squonk, ahuizotl.
* Prehistoric land mammals: chalicotherium, gorgonopsid, lystrosaurus, macrauchenia.
* Eldritch: eldritch horror, void creature, planet eater, star eater (tentacled masses with many eyes and orbiting
  debris), ophanim (interlocking eyed rings), black hole beast, taotie (a horned mask-face with a maw), ammit.
* dullahan: a headless armoured rider holding its own head on a dark horse (mount: the pillion seat behind him).
* Insect folk: bee knight, beetle knight, dragonfly knight (armoured insect humanoids), drider, alien queen, face
  grabber (original designs).

The humanoid parts reuse the monsters kit (h_monsters: torso, arms, hands, human head) with this family's own rigs;
the horse of the dullahan is hoofkit.ungulate. NOTE: build.py hashes only this file + kit.py: after a change in
h_monsters / hoofkit / mythic_geo rebuild this family with --force.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF
from kit import Hero, hero, stripes, spots, gradient, combine
from map import NOTFOOD
import motion
import motion_landmyth as ml
import mythic_geo as mg
import h_monsters as HM

T = HM.T


def A(*x):
    return np.array(x, float)


def nrm(v):
    v = np.asarray(v, float)
    return v / max(np.linalg.norm(v), 1e-9)


def hard(shapes):
    return mg.union_hard([s for s in shapes if s is not None])


def seg_dist(P, a, b):
    a, b = A(*a), A(*b)
    ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


def feather_mask(a, b, start=0.35, span=1.0, dark=0.45, bars=0.0, freq=3.0):
    """Feathers darken toward their tips (distance from the arm line a-b), optional barring."""
    def f(P):
        d = seg_dist(P, a, b)
        t = np.clip((d - start) / span, 0, 1)
        m = 1 - dark * t
        if bars:
            u = np.mod(d * freq, 1.0)
            m = m * (1 - bars * np.clip(1 - np.abs(u - 0.5) / 0.18, 0, 1) * (d > start))
        return m
    return f


def feathers(items, normal, th=0.035, curl=0.04):
    """items: (p0, dir, length, half width) feathers, face normal `normal`; a crisp overlapping union."""
    out = []
    for p0, d, L, w in items:
        f = mg.feather(A(*p0), nrm(d), L, w, A(*normal), th=th, curl=curl)
        p0 = A(*p0)
        e = p0 + nrm(d) * L
        out.append(mg.bounded(f, np.minimum(p0, e), np.maximum(p0, e), w + 0.15))
    return hard(out)


# ================================================================================================ wings
def feather_wing(H, side_bones, pts, span_dirs, lens, col="primary", tris=(900, 900, 1100), up=(0, 1, 0.65), wid=0.17,
                 n=(6, 6, 7), thick=(0.12, 0.09, 0.065), names=("WingA#", "WingB#", "WingC#"), hand_claw=True, mat="cloth"):
    """A feathered wing along a 3-bone chain (right side; mirrored). pts: shoulder, elbow, wrist, tip. Secondaries
    hang from the arm and forearm along span_dirs[0] / [1] (back and down), primaries fan from the wrist between
    span_dirs[2] and span_dirs[3]. lens: (secondary min, secondary max, primary min, primary max)."""
    Sh, El, Wr, Tp = (A(*p) for p in pts)
    b0, b1, b2 = side_bones
    l0, l1, p0_, p1_ = lens
    out = []
    segs = [(Sh, El, span_dirs[0], span_dirs[0], l0, l0 + (l1 - l0) * 0.5, n[0]),
            (El, Wr, span_dirs[0], span_dirs[1], l0 + (l1 - l0) * 0.5, l1, n[1])]
    for si, (a, b, d0, d1, L0, L1, cnt) in enumerate(segs):
        items = []
        for i in range(cnt):
            u = (i + 0.4) / cnt
            p = a + (b - a) * u
            d = nrm(A(*d0) * (1 - u) + A(*d1) * u)
            items.append((p + A(0, -0.02, 0.02), d, L0 + (L1 - L0) * u, wid))
        fe = feathers(items, up)
        arm = round_cone(T(a - (b - a) * 0.08), T(b), thick[si], thick[si + 1])
        ad = nrm(b - a)
        mid = (a + b) / 2 + A(0, 0, 0.12)
        R = mg.frame(ad, up)
        cov = mg.oell(mid, R, (np.linalg.norm(b - a) * 0.55, 0.32, 0.06))     # covert plate (along, side, normal)
        sh = arm.su(cov, 0.06) | fe
        out.append(sh)
    # hand: primaries fan from the wrist to the tip
    items = []
    cnt = n[2]
    for i in range(cnt):
        u = i / (cnt - 1)
        p = Wr + (Tp - Wr) * (0.05 + 0.85 * u)
        d = nrm(A(*span_dirs[2]) * (1 - u) + A(*span_dirs[3]) * u)
        items.append((p, d, p0_ + (p1_ - p0_) * math.sin(u * math.pi * 0.62), wid * 0.95))
    fe = feathers(items, up, curl=0.08)
    hand = round_cone(T(Wr), T(Tp), thick[2], thick[2] * 0.55)
    hd = nrm(Tp - Wr)
    cov2 = mg.oell((Wr + Tp) / 2 + A(0, 0, 0.08), mg.frame(hd, up), (np.linalg.norm(Tp - Wr) * 0.5, 0.22, 0.05))
    hs = hand.su(cov2, 0.05) | fe
    if hand_claw:   # little clawed thumb at the wrist (wings were arms)
        th = round_cone(T(Wr + A(0, 0.02, -0.02)), T(Wr + A(0.12, 0.1, -0.22)), 0.05, 0.03)
        th = th | round_cone(T(Wr + A(0.12, 0.1, -0.22)), T(Wr + A(0.15, 0.03, -0.34)), 0.03, 0.008)
        hs = hs | th
    out.append(hs)
    pats = [feather_mask(T(Sh), T(El), bars=0.12), feather_mask(T(El), T(Wr), bars=0.12), feather_mask(T(Wr), T(Tp), start=0.3, span=1.4, bars=0.12)]
    for nm, b, sh, tr, pt in zip(names, side_bones, out, tris, pats):
        H.mpiece(nm, b, sh, col=col, mat=mat, tris=tr, res=128, role="wing", pri=1.2, pattern=pt)


def tail_fan(H, bone, root, n, length, spread, down=0.45, wid=0.13, col="primary", name="TailFan", tris=1300, eye_spots=False, up=(0, 1, 0)):
    root = A(*root)
    items = []
    for i in range(n):
        u = i / (n - 1) - 0.5
        d = nrm(A(spread * u * 2, -down, 1.0))
        L = length * (1 - 0.18 * abs(u) * 2)
        items.append((root + A(0.06 * u, 0, -0.1), d, L, wid))
    fe = feathers(items, up, th=0.04, curl=0.06)
    fe = fe.su(ellipsoid(0.22, 0.14, 0.3, T(root)), 0.06)
    pat = feather_mask(T(root), T(root + A(0, 0, 0.01)), start=0.4, span=length, dark=0.4, bars=0.12, freq=2.5)
    if eye_spots:
        tip_c = [root + nrm(A(spread * (i / (n - 1) - 0.5) * 2, -down, 1.0)) * length * 0.82 for i in range(n)]

        def pat(P, base=pat, tc=tip_c):
            m = base(P)
            for c in tc:
                d = np.linalg.norm(P - c, axis=1)
                ring = np.clip(1 - np.abs(d - 0.1) / 0.04, 0, 1)
                m = m * (1 - 0.6 * np.clip((0.07 - d) / 0.03, 0, 1)) * (1 - 0.35 * ring)
            return m
    H.piece(name, bone, fe, col=col, mat="cloth", tris=tris, res=128, role="tail", pri=1.3, pattern=pat)


# ================================================================================================ bird legs
def bird_legs(H, hip, knee, heel, toe, thick=1.0, col="beak", fcol="primary", talon=1.0, cuff=True, toe_len=0.45, pat=None):
    """Feathered thigh (with a cuff over the knee), scaly shank, foot with three forward toes and a hind toe; talons
    are their own piece. Bones Hip#, Knee#, Foot# (right side; mirrored)."""
    Hp, Kn, Hl, Tb = A(*hip), A(*knee), A(*heel), A(*toe)
    H.mbone("Hip#", "Body", T(Hp))
    H.mbone("Knee#", "Hip#", T(Kn))
    H.mbone("Foot#", "Knee#", T(Hl))
    k = thick
    th = round_cone(T(Hp + A(0, 0.12, 0)), T(Kn), 0.22 * k, 0.15 * k)
    th = th.su(ellipsoid(0.2 * k, 0.32, 0.22 * k, T((Hp + Kn) / 2 + A(0.02, 0, 0.02))), 0.1)
    if cuff:
        th = th.su(round_cone(T(Kn + A(0, 0.1, 0)), T(Kn + (Hl - Kn) * 0.42), 0.16 * k, 0.12 * k), 0.06)
    th = th.noise(0.025 * k, 9.0, 21)
    H.mpiece("Thigh#", "Hip#", th, col=fcol, mat="cloth", tris=800, role="limb", pattern=pat)
    sh = round_cone(T(Kn), T(Hl), 0.13 * k, 0.09 * k).su(sphere(0.1 * k, T(Hl)), 0.04)
    H.mpiece("Shank#", "Knee#", sh, col=col, mat="skin", tris=450, role="limb")
    ft = round_cone(T(Hl), T(Tb + A(0, 0.06, 0)), 0.075 * k, 0.07 * k)
    ft = ft.su(sphere(0.09 * k, T(Tb + A(0, 0.05, 0))), 0.04)
    claws = []
    tl = toe_len * k
    for ang in (-28, 0, 28):
        a = math.radians(ang)
        d = A(math.sin(a), 0, -math.cos(a))
        p1 = Tb + A(0, 0.06, 0) + d * tl * 0.55
        p2 = Tb + A(0, 0.045, 0) + d * tl
        ft = ft.su(tube([T(Tb + A(0, 0.07, 0)), T(p1), T(p2)], [0.06 * k, 0.05 * k, 0.04 * k], k=0.01), 0.03)
        claws.append(mg.curved_horn([p2 + d * 0.01, p2 + d * 0.12 * talon * k + A(0, 0.0, 0), p2 + d * 0.2 * talon * k + A(0, -0.06 * talon * k, 0)], 0.04 * k, 0.008))
    hb = Tb + A(0, 0.06, 0.24 * k)
    ft = ft.su(round_cone(T(Tb + A(0, 0.08, 0.02)), T(hb), 0.055 * k, 0.04 * k), 0.03)
    claws.append(mg.curved_horn([hb, hb + A(0, -0.0, 0.1 * talon * k), hb + A(0, -0.06 * talon * k, 0.16 * talon * k)], 0.035 * k, 0.008))
    gnd = plane((0, -1, 0), 0.0)
    H.mpiece("FootP#", "Foot#", (ft.noise(0.008, 25.0, 3)) & gnd, col=col, mat="skin", tris=800, role="foot")
    H.mpiece("Talons#", "Foot#", hard(claws) & gnd, col="claw", mat="hard", tris=400, role="claw", pri=1.7, ao=False)
    return ("HipR", "KneeR", "FootR"), ("HipL", "KneeL", "FootL")


# ================================================================================================ human upper body (shared)
def human_ctx(s=1.0, hipY=2.55, torso=1.0, W=0.85, sh_w=0.45, head=0.95, hunch=0.0, **pk):
    """Context for the monsters-kit torso / head helpers: positions of the waist, chest, shoulders, neck and head."""
    def v(x, y, z):
        return np.array((x, y, z), float) * s
    P = HM._P(s=s, W=W, torso=torso, head=head, hunch=hunch, **pk)
    shY = hipY + 1.5 * torso - 0.22 * hunch
    hs = 0.85 * head * s
    headP = v(0, shY + 0.38, -0.02 - 0.9 * hunch)
    C = HM.Ctx(v=v, s=s, P=P, hipY=hipY * s, waist=v(0, hipY + 0.55 * torso, 0.02 - 0.12 * hunch),
               chest=v(0, hipY + 1.08 * torso, -0.04 - 0.38 * hunch), Sh=v(sh_w * W + 0.12, shY, 0.02 - 0.5 * hunch),
               neckB=v(0, shY + 0.06, 0.04 - 0.62 * hunch), headP=headP, hs=hs,
               hc=headP + np.array((0, 0.36 * hs, -0.06 * hs)), Hip=v(0.3 * W, hipY, 0.03), footH=0.3 * s)
    return P, C


def human_head(H, C, P, hair="wild", hair_col="secondary", jaw=True):
    head, jw, h, F = HM._head_human(H, C, P)
    if not jaw:
        jw = None
    HM._place_head(H, C, P, head, jw, h, F, tris=1800)
    if hair:
        HM._hair(H, C, hair, col=hair_col)
    return h, F


def crest_plumes(H, C, n=5, length=0.9, col="secondary", bone="Head", spread=0.12, name="Crest", lean=0.55):
    hc, hs = C["hc"], C["hs"]
    items = []
    for i in range(n):
        u = i / max(n - 1, 1) - 0.5
        p0 = hc + A(u * spread * 2, 0.42, 0.0 + abs(u) * 0.1) * hs
        d = nrm(A(u * 0.9, 1.0, lean + abs(u) * 0.3))
        items.append((p0, d, length * hs * (1 - 0.3 * abs(u) * 2), 0.09 * hs))
    fe = feathers(items, (0, 0, 1) if True else (1, 0, 0), th=0.03, curl=-0.08)
    H.piece(name, bone, fe, col=col, mat="cloth", tris=900, role="crest", pri=1.3,
            pattern=feather_mask(T(hc + A(0, 0.4, 0) * hs), T(hc + A(0, 0.41, 0) * hs), start=0.2, span=length * hs, dark=0.35))


def crown(H, C, kind="queen", bone="Head", col="gold"):
    hc, hs = C["hc"], C["hs"]

    def hh(x, y, z):
        return T(hc + np.array((x, y, z)) * hs)

    if kind == "kokoshnik":  # tall rounded halo crown (sirin)
        cr = plate_halo(hc + A(0, 0.38, -0.06) * hs, 0.62 * hs, 0.05 * hs)
        for i in range(7):
            a = math.radians(-70 + i * 140 / 6)
            c = hc + A(0, 0.38, -0.1) * hs + A(math.sin(a), math.cos(a), 0) * 0.58 * hs
            cr = cr | sphere(0.06 * hs, T(c))
        cr = cr.su(torus(0.4 * hs, 0.05 * hs).scale3(1, 1, 1.1).at(*hh(0, 0.3, 0.04)), 0.04)
    else:
        cr = cylinder(0.38 * hs, 0.07 * hs, rr=0.02 * hs).at(*hh(0, 0.45, 0.04)) - cylinder(0.33 * hs, 0.2 * hs).at(*hh(0, 0.45, 0.04))
        for i in range(8):
            a = i / 8 * math.tau
            r = 0.36
            ln = 0.42 if i % 2 == 0 else 0.26
            cr = cr | round_cone(hh(r * math.sin(a), 0.48, 0.04 - r * math.cos(a)), hh((r + 0.05) * math.sin(a), 0.48 + ln, 0.04 - (r + 0.05) * math.cos(a)), 0.05 * hs, 0.012 * hs)
    H.piece("Crown", bone, cr, col=col, mat="metal", tris=800, role="hat", pri=1.4)


def plate_halo(c, R, t):
    """A vertical half-disc ring (kokoshnik) facing -Z."""
    c = A(*c)
    ring = cylinder(R, t, axis=2, rr=t * 0.5).at(*T(c)) - cylinder(R * 0.7, t * 3, axis=2).at(*T(c - A(0, 0.08 * R, 0)))
    return ring & half_space(1, -1, float(c[1] - 0.05 * R))


# ================================================================================================ harpies
def _harpy(hid, s=1.0, back_wings=False, queen=False, archer=False, span=1.0, crest=1.0, tail=1.0, hair="wild",
           preview=None):
    P, C = human_ctx(s=s, hipY=2.55, torso=0.98, W=0.78, head=0.98, armT=0.75, legT=0.8, muscle=0.2, depth=0.85,
                     skin="skin", nopelvis=True, hands="fist",
                     face=dict(brow=0.7, angry=0.8, nose="human", ns=0.8, ears="pointed", es=0.7, cheek=0.7, cw=0.95, jw=0.9,
                               chin=0.85, iris=[0.95, 0.72, 0.12], sclera=None, eye=1.15, fangs=0.0, lips=0.2))
    H = Hero(hid, plan="Bird", gait="hover", tags=["harpy", "flying", "myth"])
    H.preview = preview or {}
    v = C["v"]
    H.body(T(v(0, 2.65, 0.02)))
    H.bone("Spine", "Body", T(C["waist"]))
    H.bone("Head", "Spine", T(C["headP"]))
    rib, _ = HM._torso(H, C, P, tris=2000)
    # feather bodice over the lower ribs + belly, and a feathered collar
    bod = rib.round(0.045 * s) & half_space(1, 1, float(C["chest"][1] - 0.02 * s))
    bod = bod.noise(0.02 * s, 11.0 / s, 4)
    if queen:
        coll = torus(0.42 * s, 0.13 * s).scale3(1.15, 0.7, 1.0).at(*T(C["neckB"] + v(0, -0.08, 0.04)))
        bod = bod | coll.noise(0.03 * s, 10 / s, 5)
    H.piece("Bodice", "Spine", bod, col="primary", mat="cloth", tris=1300, res=128, role="body", pri=1.1,
            pattern=gradient(1, float(C["waist"][1] - 0.4 * s), float(C["chest"][1]), 0.8, 1.0))
    # feathered hips with a short skirt of feathers over the thighs
    hy = C["hipY"]
    pel = ellipsoid(0.44 * s, 0.36 * s, 0.32 * s, T(v(0, 2.62, 0.04)))
    pel = pel.su(ellipsoid(0.36 * s, 0.3 * s, 0.28 * s, T(C["waist"] + v(0, -0.2, 0))), 0.15)
    items = []
    for i in range(9):
        a = math.radians(-120 + i * 30)
        p0 = v(0.42 * math.sin(a), 2.55, 0.04 - 0.32 * math.cos(a))
        d = nrm(A(0.35 * math.sin(a), -1.0, -0.35 * math.cos(a)))
        items.append((p0, d, 0.5 * s, 0.12 * s))
    pel = pel.su(feathers(items, (0, 0, -1), th=0.035 * s), 0.03)
    H.piece("Hips", "Body", pel.noise(0.015 * s, 12 / s, 6), col="primary", mat="cloth", tris=1300, res=128, role="body", pri=1.05,
            pattern=feather_mask(T(v(0, 2.7, 0.04)), T(v(0, 2.71, 0.04)), start=0.35 * s, span=0.5 * s, dark=0.35))
    # legs
    lg = bird_legs(H, v(0.27, 2.5, 0.05), v(0.31, 1.82, -0.3), v(0.31, 0.88, 0.28), v(0.31, 0.0, -0.05), thick=s * 1.0, talon=1.3)
    # head, hair, crest
    human_head(H, C, P, hair=hair, hair_col="secondary")
    if crest:
        crest_plumes(H, C, n=5 if not queen else 7, length=1.0 * crest, col="secondary", spread=0.14 if not queen else 0.2)
    if queen:
        crown(H, C, "queen")
    # wings
    sh = C["Sh"]
    if not back_wings:
        pts = [sh + v(-0.05, 0.02, 0.0), sh + v(0.85 * span, 0.22 * span, 0.12), sh + v(1.65 * span, 0.4 * span, 0.08), sh + v(2.55 * span, 0.62 * span, 0.25)]
        H.mbone("Shoulder#", "Spine", T(pts[0]))
        H.mbone("Elbow#", "Shoulder#", T(pts[1]))
        H.mbone("Hand#", "Elbow#", T(pts[2]))
        feather_wing(H, ("Shoulder#", "Elbow#", "Hand#"), [T(p) for p in pts],
                     [(0.05, -0.7, 1.0), (0.3, -0.75, 1.0), (0.45, -0.6, 1.0), (1.0, -0.15, 0.45)],
                     (0.85 * span * s, 1.25 * span * s, 1.3 * span * s, 1.75 * span * s), up=(0, 1, 0.75))
        wings = [("ShoulderR", "ElbowR", "HandR", 1), ("ShoulderL", "ElbowL", "HandL", -1)]
        arms = ()
    else:
        root = C["chest"] + v(0.16, 0.38, 0.3)
        pts = [root, root + v(0.8 * span, 0.62 * span, 0.32), root + v(1.5 * span, 0.95 * span, 0.42), root + v(2.25 * span, 1.05 * span, 0.62)]
        H.mbone("Wing#", "Spine", T(pts[0]))
        H.mbone("WingEl#", "Wing#", T(pts[1]))
        H.mbone("WingHd#", "WingEl#", T(pts[2]))
        feather_wing(H, ("Wing#", "WingEl#", "WingHd#"), [T(p) for p in pts],
                     [(0.1, -1.0, 0.45), (0.35, -1.0, 0.5), (0.6, -0.9, 0.5), (1.0, -0.1, 0.35)],
                     (0.7 * span * s, 1.0 * span * s, 1.1 * span * s, 1.5 * span * s), up=(0, 0.45, -1.0),
                     n=(4, 5, 6), tris=(750, 750, 950), hand_claw=False)
        wings = [("WingR", "WingElR", "WingHdR", 1), ("WingL", "WingElL", "WingHdL", -1)]
        # arms
        C["El"] = C["Sh"] + v(0.14, -0.82, 0.08)
        C["Wr"] = C["El"] + v(0.02, -0.75, -0.1)
        H.mbone("Shoulder#", "Spine", T(C["Sh"]))
        H.mbone("Elbow#", "Shoulder#", T(C["El"]))
        H.mbone("Hand#", "Elbow#", T(C["Wr"]))
        HM._arms(H, C, P, upper_tris=600)
        arms = (("ShoulderR", "ElbowR", "HandR", 1), ("ShoulderL", "ElbowL", "HandL", -1))
    if archer:
        P["wscale"] = 1.0 * s
        HM._weapon(H, C, P, "bow", side="L")
        q0 = C["chest"] + v(-0.12, 0.05, 0.36)
        qv = round_cone(T(q0 + v(0.25, -0.55, 0.06)), T(q0 + v(-0.2, 0.35, 0.0)), 0.13 * s, 0.15 * s)
        qv = qv - round_cone(T(q0 + v(0.21, -0.45, 0.06)), T(q0 + v(-0.25, 0.5, 0.0)), 0.1 * s, 0.12 * s)
        for i, dx in enumerate((-0.06, 0.0, 0.06)):
            base = q0 + v(-0.15 + dx, 0.22, 0.0 + dx * 0.5)
            tip = base + v(-0.12, 0.42, 0.0)
            qv = qv | capsule(T(base), T(tip), 0.018 * s) | mg.feather(tip - v(-0.04, 0.15, 0), nrm(A(-0.28, 1, 0)), 0.2 * s, 0.05 * s, A(0, 0, 1), th=0.015)
        H.piece("Quiver", "Spine", qv, col="leather", mat="cloth", tris=900, role="detail", pri=1.4)
    H.bone("Tail", "Body", T(v(0, 2.62, 0.3)))
    tail_fan(H, "Tail", T(v(0, 2.62, 0.3)), 7, 1.15 * tail * s, 0.55, down=0.55, wid=0.13 * s)
    # sockets + rig
    hc, hs = C["hc"], C["hs"]
    H.socket("mouth", T(hc + A(0, -0.25, -0.5) * hs), "Jaw")
    H.socket("head", T(hc + A(0, 0.6, 0) * hs), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": ["Tail"],
                  "legs": [{"hip": "HipR", "knee": "KneeR", "phase": 0.0, "side": 1}, {"hip": "HipL", "knee": "KneeL", "phase": 0.5, "side": -1}]})
    height = float(hc[1] + 0.5 * hs)
    ml.wing_hover(H, wings, legs=lg, arms=arms, spine="Spine", head="Head", jaw="Jaw", tail=["Tail"], height=height,
                  rate=1.0, amp=0.55 if not back_wings else 0.5, attack="shoot" if archer else "dive")
    return H


HARPY_PREV = {"primary": "#7B5B3E", "secondary": "#2E2420", "skin": "#E7C3A0", "beak": "#D9A632", "claw": "#2A2522", "iris": "#E8B423"}


@hero("harpy", "landmyth")
def harpy():
    return _harpy("harpy", preview=HARPY_PREV)


@hero("harpy queen", "landmyth")
def harpy_queen():
    return _harpy("harpy queen", s=1.12, queen=True, span=1.15, crest=1.25, tail=1.3, hair="long",
                  preview={"primary": "#5B3F6E", "secondary": "#1E1A2A", "skin": "#E7C3A0", "beak": "#D9A632", "gold": "#E8B53A"})


@hero("harpy archer", "landmyth")
def harpy_archer():
    return _harpy("harpy archer", back_wings=True, archer=True, span=1.0, crest=0.8, hair="topknot",
                  preview={"primary": "#8A7048", "secondary": "#3A2A1C", "skin": "#E2B892", "beak": "#D9A632", "leather": "#6B4423"})


# ================================================================================================ sirin (bird body, crowned human head)
@hero("sirin", "landmyth")
def sirin():
    H = Hero("sirin", plan="Bird", gait="hover", tags=["bird", "myth", "flying", "music"])
    H.preview = {"primary": "#2B2A5E", "secondary": "#FDE68A", "skin": "#F0CFB0", "hair": "#3A2418", "beak": "#C9A040", "gold": "#E8B53A"}
    s = 1.0
    H.body((0, 2.35, 0.2))
    # plump bird body with a puffed breast and a feather ruff at the neck
    bd = ellipsoid(0.72, 0.74, 1.15, (0, 2.35, 0.3))
    bd = bd.su(ellipsoid(0.66, 0.72, 0.62, (0, 2.55, -0.38)), 0.3)
    bd = bd.su(ellipsoid(0.5, 0.42, 0.6, (0, 2.0, -0.1)), 0.3)
    bd = bd.su(ellipsoid(0.42, 0.35, 0.55, (0, 2.45, 1.1)), 0.25)
    ruff = torus(0.36, 0.14).scale3(1.0, 0.8, 1.0).rot(-25, 0, 0).at(0, 3.0, -0.55)
    bd = bd.su(ruff, 0.12).noise(0.02, 10.0, 7)
    breast = lambda P: 1.0 - 0.25 * np.clip((P[:, 1] - 2.2) / 1.0, 0, 1)
    scal = spots(0.16, 0.05, depth=0.25, seed=2)
    H.piece("Torso", "Body", bd, col="primary", mat="cloth", tris=2200, res=128, role="body", pattern=combine(breast, scal))
    # neck + human head
    H.bone("Neck", "Body", (0, 2.95, -0.6))
    nk = round_cone((0, 2.85, -0.55), (0, 3.45, -0.72), 0.17, 0.13)
    H.piece("NeckP", "Neck", nk, col="skin", mat="skin", tris=500, role="limb", pri=1.2)
    hs = 0.72
    hp = A(0, 3.48, -0.74)
    C = HM.Ctx(v=lambda x, y, z: np.array((x, y, z), float), s=s, hs=hs, headP=hp, hc=hp + A(0, 0.36 * hs, -0.06 * hs))
    P = HM._P(s=s, skin="skin", face=dict(brow=0.2, nose="human", ns=0.75, ears="human", es=0.8, cheek=0.5, cw=0.92, jw=0.85, chin=0.8,
                                          iris=[0.25, 0.45, 0.75], eye=1.1, lips=0.35, mouthw=0.85))
    H.bone("Head", "Neck", T(hp))
    human_head(H, C, P, hair="long", hair_col="hair")
    crown(H, C, "kokoshnik")
    # half-raised display wings
    sh = A(0.5, 2.75, -0.1)
    pts = [sh, sh + A(0.55, 0.45, 0.45), sh + A(0.75, 0.95, 1.05), sh + A(1.05, 0.85, 1.95)]
    H.mbone("Shoulder#", "Body", T(pts[0]))
    H.mbone("Elbow#", "Shoulder#", T(pts[1]))
    H.mbone("Hand#", "Elbow#", T(pts[2]))
    feather_wing(H, ("Shoulder#", "Elbow#", "Hand#"), [T(p) for p in pts],
                 [(0.35, -1.0, 0.25), (0.45, -1.0, 0.45), (0.3, -1.0, 0.6), (0.2, -0.2, 1.0)],
                 (0.8, 1.15, 1.2, 1.7), up=(1.0, 0.1, -0.25), n=(5, 6, 7), tris=(900, 900, 1100), hand_claw=False, col="primary")
    # long ornate tail with eye spots
    H.bone("Tail", "Body", (0, 2.45, 1.3))
    tail_fan(H, "Tail", (0, 2.5, 1.25), 9, 2.3, 0.85, down=-0.45, wid=0.24, col="secondary", tris=1600, eye_spots=True, up=(0, 0.45, 1.0))
    lg = bird_legs(H, (0.32, 2.0, 0.3), (0.38, 1.45, 0.0), (0.38, 0.72, 0.36), (0.38, 0.0, 0.02), thick=1.2, talon=1.1, fcol="primary", cuff=True)
    hc = C["hc"]
    H.socket("mouth", T(hc + A(0, -0.25, -0.5) * hs), "Jaw")
    H.socket("head", T(hc + A(0, 0.95, 0) * hs), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": ["Tail"],
                  "legs": [{"hip": "HipR", "knee": "KneeR", "phase": 0.0, "side": 1}, {"hip": "HipL", "knee": "KneeL", "phase": 0.5, "side": -1}]})
    wings = [("ShoulderR", "ElbowR", "HandR", 1), ("ShoulderL", "ElbowL", "HandL", -1)]
    ml.wing_hover(H, wings, legs=lg, spine="Neck", head="Head", jaw="Jaw", tail=["Tail"], height=4.3, amp=0.5, rate=0.8)
    return H


# ================================================================================================ tengu + kenku
def crow_head(H, C, P, col="primary", beak="beak", scruff=True):
    """Crow skull with a long sharp beak (upper on Head, lower on a Jaw bone) and round bird eyes."""
    hc, hs = C["hc"], C["hs"]

    def h(x, y, z):
        return T(hc + A(x, y, z) * hs)

    sk = ellipsoid(0.36 * hs, 0.38 * hs, 0.42 * hs, h(0, 0.06, 0.05))
    sk = sk.su(ellipsoid(0.24 * hs, 0.22 * hs, 0.25 * hs, h(0, 0.0, -0.22)), 0.12)
    sk = sk.su(ellipsoid(0.3 * hs, 0.36 * hs, 0.3 * hs, h(0, -0.3, 0.12)), 0.15)   # throat
    if scruff:
        for i in range(5):
            a = math.radians(-50 + i * 25)
            sk = sk.su(round_cone(h(0.1 * math.sin(a), 0.3, 0.25), h(0.25 * math.sin(a), 0.42 + 0.05 * math.cos(a), 0.62), 0.09 * hs, 0.02 * hs), 0.05)
    sk = sk.ss(sphere(0.09 * hs, h(0.25, 0.1, -0.2)).mirror_x(), 0.03)
    sk = sk.noise(0.012 * hs, 18 / hs, 3)
    H.piece("HeadP", "Head", sk, col=col, mat="cloth", tris=1500, res=128, role="head")
    ub = tube([h(0, 0.06, -0.25), h(0, 0.02, -0.55), h(0, -0.06, -0.85), h(0, -0.16, -0.97)], [0.15 * hs, 0.1 * hs, 0.05 * hs, 0.015 * hs], k=0.02)
    ub = ub.scale3(1, 1, 1) & plane((0, -1, 0), -float(hc[1] - 0.09 * hs))
    H.piece("Beak", "Head", ub.su(sphere(0.001, h(0, 0.06, -0.25)), 0.001), col=beak, mat="hard", tris=500, role="beak", pri=1.3)
    H.bone("Jaw", "Head", h(0, -0.08, -0.2))
    lb = tube([h(0, -0.08, -0.25), h(0, -0.12, -0.6), h(0, -0.15, -0.82)], [0.11 * hs, 0.06 * hs, 0.015 * hs], k=0.02) & plane((0, 1, 0), float(hc[1] - 0.095 * hs))
    H.piece("BeakLow", "Jaw", lb, col=beak, mat="hard", tris=350, role="jaw", pri=1.35)
    H.eyes("Head", h(0.25, 0.1, -0.2), 0.075 * hs, col="iris", pupil="round", look=(0.7, 0.05, -0.7))


def fan_prop(H, C, P, bone="HandR", col="secondary"):
    s = C["s"]
    g = C["grip"].copy()
    hd = capsule(T(g + A(0, -0.25, 0) * s), T(g + A(0, 0.35, 0) * s), 0.04 * s) | sphere(0.07 * s, T(g + A(0, 0.38, 0) * s))
    items = []
    for i in range(9):
        a = math.radians(-60 + i * 15)
        items.append((g + A(0, 0.38, 0) * s, A(math.sin(a), math.cos(a), 0.0), 0.75 * s, 0.13 * s))
    fe = feathers(items, (0, 0, 1), th=0.025 * s, curl=0.0)
    H.piece("FanHandle", bone, hd, col="darkWood", mat="wood", tris=300, role="weapon", pri=1.5)
    H.piece("Fan", bone, fe, col=col, mat="cloth", tris=900, role="weapon", pri=1.4,
            pattern=feather_mask(T(g + A(0, 0.38, 0) * s), T(g + A(0, 0.39, 0) * s), start=0.3 * s, span=0.5 * s, dark=0.4))


@hero("tengu", "landmyth")
def tengu():
    P = HM._P(s=1.0, leg=0.95, torso=1.0, W=1.0, arm=1.0, armT=0.95, legT=0.95, head=1.05, muscle=0.5, hands="fist", feet="boot",
              gait="hover", weapon="fan", tags=["yokai", "flying", "myth"],
              face=dict(nose="long", ns=1.9, ears="human", brow=1.0, angry=0.9, cheek=0.7, jw=1.0, iris=[0.95, 0.75, 0.15], eye=0.95),
              preview={"primary": "#C8302A", "secondary": "#1F2937", "cloth": "#ECE6D8", "cloth2": "#ECE6D8", "white": "#F2F2F2"})
    H, C = HM._rig("tengu", P, plan="Humanoid")
    rib, pel = HM._torso(H, C, P, tris=1500)
    HM._arms(H, C, P)
    HM._legs(H, C, P, foot_col="white")
    head, jaw, h, F = HM._head_human(H, C, P)
    HM._place_head(H, C, P, head, jaw, h, F, tris=1800)
    HM._hair(H, C, "short", col="white")
    hs = C["hs"]
    # tokin: the small black pillbox cap on the brow
    cap = cylinder(0.17 * hs, 0.11 * hs, rr=0.04 * hs).rot(-15, 0, 0).at(*h(0, 0.55, -0.15))
    cap = cap.su(round_box(0.08 * hs, 0.02 * hs, 0.25 * hs, 0.015 * hs, h(0, 0.45, -0.05)), 0.03)
    H.piece("Tokin", "Head", cap, col="black", mat="cloth", tris=400, role="hat", pri=1.4)
    # robe (knee length) with the yamabushi pom-pom sash
    v, s = C["v"], C["s"]
    top = C["Sh"][1]
    rb = round_cone(T(A(0, top - 0.1, 0.02)), T(A(0, C["Knee"][1] + 0.1, 0.05)), 0.64 * s, 0.78 * s)
    rb = rb.su(ellipsoid(0.82 * s, 0.4 * s, 0.5 * s, T(A(0, top - 0.12, 0.02))), 0.15)
    rb = rb & plane((0, -1, 0), -float(C["Knee"][1] - 0.05))
    folds = lambda p: 0.02 * np.sin(np.arctan2(p[:, 0], p[:, 2]) * 9) * np.clip((top - p[:, 1]) / 2.0, 0, 1)
    rb0 = rb
    rb = SDF(lambda p: rb0(p) + folds(p))
    H.piece("Robe", "Spine", rb, col="cloth", mat="cloth", tris=1600, res=128, role="cloth", pri=1.05)
    pom = None
    for i in range(6):
        y = top - 0.25 - i * 0.2
        x = -0.3 + i * 0.12
        z = -0.5 - 0.03 * (2.5 - abs(i - 2.5))
        b = sphere(0.075 * s, (x, y, z))
        pom = b if pom is None else pom | b
    pom = pom | capsule((-0.45, top - 0.05, -0.44), (0.42, top - 1.3, -0.5), 0.025)
    H.piece("Pompoms", "Spine", pom.noise(0.01, 30, 2), col="secondary", mat="cloth", tris=600, role="detail", pri=1.6)
    wings = HM._feather_wings(H, C, P, span=1.45, col="secondary")
    fan_prop(H, C, P)
    legs, arms, height = HM._finish(H, C, P)
    import motion_monsters as mm
    H.rig["gait"] = "hover"
    mm.hoverer(H, wings, arms=arms, legs=[(a, b, c, 1 if i == 0 else -1) for i, (a, b, c, _) in enumerate(legs)], spine="Spine", head="Head",
               jaw="Jaw", height=height, rate=0.9, amp=0.55, weapon_arm="ShoulderR")
    return H


@hero("kenku", "landmyth")
def kenku():
    P = HM._P(s=0.9, leg=0.9, torso=0.95, W=0.8, arm=1.05, armT=0.7, legT=0.75, head=1.2, hunch=0.35, muscle=0.2, hands="open", claws=True,
              feet="claw", foot=1.1, weapon="staff", attack="punch", stride=0.45, walk=0.85, lean=0.1, tags=["bird", "trickster"],
              orb="gem", preview={"primary": "#20242C", "secondary": "#8A8F99", "beak": "#2E2E33", "iris": "#E0B030", "claw": "#2A2522"})
    H, C = HM._rig("kenku", P, plan="Humanoid")
    rib, pel = HM._torso(H, C, P, tris=1300)
    HM._arms(H, C, P, upper_tris=550)
    HM._legs(H, C, dict(P, skin="beak"))
    crow_head(H, C, P, col="primary", beak="beak")
    # hooded cloak over a ragged mantle of feathers
    hs = C["hs"]
    hc = C["hc"]
    hd = ellipsoid(0.5 * hs, 0.52 * hs, 0.56 * hs, T(hc + A(0, 0.1, 0.12) * hs)).ss(ellipsoid(0.4 * hs, 0.5 * hs, 0.5 * hs, T(hc + A(0, 0.0, -0.18) * hs)), 0.04)
    hd = hd.su(round_cone(T(hc + A(0, 0.3, 0.45) * hs), T(hc + A(0, 0.05, 0.85) * hs), 0.18 * hs, 0.05 * hs), 0.08)
    HM._cape(H, C, P, col="secondary", length=0.82, collar=False, tattered=True)
    v, s = C["v"], C["s"]
    items = []
    for i in range(9):
        a = math.radians(-100 + i * 25)
        p0 = C["neckB"] + v(0.45 * math.sin(a), -0.05, -0.38 * math.cos(a) + 0.05)
        items.append((p0, nrm(A(0.5 * math.sin(a), -1.0, -0.45 * math.cos(a))), 0.55 * s, 0.13 * s))
    H.piece("Mantle", "Spine", feathers(items, (0, 0, -1), th=0.03 * s).su(torus(0.42 * s, 0.1 * s).at(*T(C["neckB"] + v(0, -0.02, 0.04))), 0.05),
            col="primary", mat="cloth", tris=1100, role="cloth", pri=1.2)
    HM._belt(H, C, P, pel, col=HM.LEATHER, buckle=True, loin="secondary")
    P["wscale"] = 0.95
    HM._weapon(H, C, P, "staff")
    HM._animate_biped(H, C, P)
    return H


# word -> hero rules (tools/meshgen/heroes/map.py): every landmyth hero (the other h_landmyth_*.py files hold the builders)
CRE = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Plant", "Weather", "Structure"]}
ONLYCRE = {"cat": ["Creature"]}
MAP = [
    ("harpy", "harpy, harpies, harpie, aello, celaeno, ocypete, harpy warrior, harpy chick", CRE),
    ("harpy queen", "harpy queen, harpy matriarch, harpy empress", CRE),
    ("harpy archer", "harpy archer, harpy hunter, harpy scout", CRE),
    ("sirin", "sirin, alkonost, gamayun, sirin bird, alkonost bird, gamayun bird, bird of paradise spirit", CRE),
    ("tengu", "tengu, karasu tengu, yamabushi tengu, daitengu", CRE),
    ("kenku", "kenku, crowfolk, crow folk, aarakocra", CRE),
    ("chupacabra", "chupacabra, chupacabras, goatsucker, goat sucker", CRE),
    ("jersey devil", "jersey devil, leeds devil", CRE),
    ("displacer beast", "displacer beast, displacer, phase panther, blink panther", CRE),
    ("hodag", "hodag", CRE),
    ("squonk", "squonk", CRE),
    ("ahuizotl", "ahuizotl, ahuitzotl", CRE),
    ("chalicotherium", "chalicotherium, chalicothere, chalicotheres, moropus", CRE),
    ("gorgonopsid", "gorgonopsid, gorgonopsian, gorgonops, inostrancevia", CRE),
    ("lystrosaurus", "lystrosaurus, dicynodont, placerias", CRE),
    ("macrauchenia", "macrauchenia", CRE),
    ("eldritch horror", "eldritch horror, eldritch abomination, eldritch beast, abomination, elder god, outer god, great old one, shoggoth, "
                        "cosmic horror, tentacled horror", ONLYCRE),
    ("void creature", "void creature, void beast, void walker, void spawn, voidling, void horror, star shadow", ONLYCRE),
    ("planet eater", "planet eater, planet devourer, moon eater, world eater, world devourer", ONLYCRE),
    ("star eater", "star eater, star devourer, sun eater, galaxy eater", ONLYCRE),
    ("ophanim", "ophanim, ophan, ophanin, throne angel, wheel angel, biblically accurate angel, wheel of eyes", ONLYCRE),
    ("black hole beast", "black hole beast, black hole monster, singularity beast, black hole creature", ONLYCRE),
    ("taotie", "taotie, tao tie, taowu", CRE),
    ("ammit", "ammit, ammut, ammut the devourer, devourer of the dead", CRE),
    ("bee knight", "bee knight, bee warrior, bee soldier, wasp knight, hornet knight", CRE),
    ("beetle knight", "beetle knight, beetle warrior, scarab knight, beetle soldier", CRE),
    ("dragonfly knight", "dragonfly knight, dragonfly rider, dragonfly warrior", CRE),
    ("drider", "drider, driders, arachne, spider centaur, spider woman centaur", CRE),
    ("alien queen", "alien queen, hive queen, xeno queen, insect queen alien, brood queen", CRE),
    ("face grabber", "face grabber, face grabbers, skull crab", CRE),
]
