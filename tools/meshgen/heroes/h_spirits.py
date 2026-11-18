"""Spirits and elementals: ghost (sheet ghost), wraith (hooded tattered shade), banshee (wailing ghost woman), grim
reaper, fire / water / earth / ice / lightning elementals, wisp, slime, mud monster, treant.

Bodies are SOLID sculpts, never glowing balls: cloth hems cut with ragged scallops, flame tongues as tapered S-curved
tubes, water as twisted columns with curling crests, rock as noisy boulders, ice as faceted hexagonal prisms,
lightning as jagged zig-zag plates on a storm-cloud body. Only eyes / tiny cores glow.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF
from kit import Hero, hero, stripes, spots, gradient, combine
import motion
import motion_monsters as mm

ANY = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Person", "Plant", "Weather", "Structure", "Place"],
       "bp": ["Humanoid", "Giant", "Ghost", "Biped", "Blob", "Quadruped", "Robot", "Cloud", "Orb", "Swarm", "Plant", "Wave", "Crystal"]}
BLOBBY = {"cat": ["Creature", "Element", "Abstract", "Object", "Plant"], "bp": ["Blob", "Humanoid", "Orb", "Swarm", "Cloud", "Ghost"]}
BONE = [0.86, 0.83, 0.74]


def T(a):
    return tuple(float(x) for x in a)


def A(*x):
    return np.array(x, float)


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


def U(*shapes, k=0.0):
    out = None
    for s_ in shapes:
        if s_ is None:
            continue
        out = s_ if out is None else (out.su(s_, k) if k > 0 else out | s_)
    return out


def flame(base, up, length, r, side=(1, 0, 0), curl=0.25, n=6):
    """A stylised flame tongue: S-curved tapered tube from base along `up`."""
    base, up, side = (np.asarray(x, float) for x in (base, up, side))
    up = up / np.linalg.norm(up)
    pts, radii = [], []
    for i in range(n):
        t = i / (n - 1)
        off = side * curl * length * math.sin(t * math.pi * 1.3) * (1 - 0.3 * t)
        pts.append(T(base + up * length * t + off))
        radii.append(max(r * (1 - t) ** 0.9 * (1 + 0.35 * math.sin(t * math.pi)), 0.012))
    return tube(pts, radii, k=0.03)


def crystal(a, b, r, tip=0.35, sides=6, twist=0.0):
    """Faceted crystal prism from a to b with a pyramidal point at b."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ax = b - a
    L = np.linalg.norm(ax)
    ax = ax / L
    t0 = np.cross(ax, (0, 0, 1) if abs(ax[2]) < 0.9 else (1, 0, 0))
    t0 /= np.linalg.norm(t0)
    t1 = np.cross(ax, t0)
    ns = [math.cos(i * math.tau / sides + twist) * t0 + math.sin(i * math.tau / sides + twist) * t1 for i in range(sides)]
    tl = L * tip

    def f(p):
        q = p - a
        h = q @ ax
        d = -h  # bottom cap
        for n in ns:
            rad = q @ n
            d = np.maximum(d, rad - r)
            # pyramid tip: plane through the apex
            d = np.maximum(d, (rad * tl + (h - L) * r) / math.hypot(tl, r))
        return d

    return SDF(f)


def bolt(o, u, v, length, width, zigs=4, t=0.04):
    """Zig-zag lightning-bolt plate from o along u (v is the zig direction)."""
    left, right = [], []
    for i in range(zigs + 1):
        f = i / zigs
        x = (0.35 if i % 2 else -0.35) * width * (1 - 0.5 * f)
        y = -length * f
        w = width * 0.5 * (1 - 0.85 * f)
        left.append((x - w, y))
        right.append((x + w, y))
    tip = (0.0, -length * 1.12)
    poly = right + [tip] + left[::-1]
    poly = [(p[0], p[1]) for p in poly]
    return plate(poly, o, v, u, t)


def ragged_cut(y0, amp, n, phase=0.0, center=(0, 0), jag=True, seed=0):
    """Half-space y >= y0 + amp * wave(angle): a ragged hem around the vertical axis through center."""
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6.28, 3)

    def f(p):
        a = np.arctan2(p[:, 0] - center[0], p[:, 2] - center[1])
        if jag:
            w = 2 * np.abs(((a * n / math.tau + phase) % 1.0) - 0.5)  # triangle wave 0..1
        else:
            w = 0.5 + 0.5 * np.cos(a * n + phase)
        w = w + 0.25 * np.sin(a * 3 + ph[0]) + 0.15 * np.sin(a * 5 + ph[1])
        return (y0 + amp * w) - p[:, 1]

    return SDF(f)


def eyes_glow(H, bone, pos, r, col, sock=True, shape="Ball", size=None, rot=(0, 0, 0)):
    x, y, z = pos
    for sx, nm in ((1, "R"), (-1, "L")):
        sz = size or (r * 2, r * 2, r * 2)
        H.prim("Eye" + nm, bone, shape, sz, (x * sx, y, z), rot=(rot[0], rot[1] * sx, rot[2] * sx), col=col, mat="hard", glow=True, role="eye", pri=1.6)


def cute_eyes(H, bone, pos, r, look=(0.1, 0, -1)):
    d = np.array(look, float)
    d /= np.linalg.norm(d)
    x, y, z = pos
    H.mprim("Eye#", bone, "Ball", (r * 2, r * 2.3, r * 2), (x, y, z), col="pupil", mat="hard", role="eye", pri=1.3)
    H.mprim("Shine#", bone, "Ball", (r * 0.7,) * 3, (x + r * 0.3, y + r * 0.55, z + d[2] * r * 0.85), col="shine", mat="hard", role="shine", pri=2.5)
    H.mprim("Shine2#", bone, "Ball", (r * 0.32,) * 3, (x - r * 0.3, y - r * 0.4, z + d[2] * r * 0.9), col="shine", mat="hard", role="shine", pri=2.6)


def _arm_bones(H, sh, el, wr, parent="Spine"):
    H.mbone("Shoulder#", parent, T(sh))
    H.mbone("Elbow#", "Shoulder#", T(el))
    H.mbone("Hand#", "Elbow#", T(wr))
    return [("ShoulderR", "ElbowR", "HandR", 1), ("ShoulderL", "ElbowL", "HandL", -1)]


def bony_hand(w, s=1.0, out=(1, 0, 0), down=(0, -1, 0), fwd=(0, 0, -1), length=1.0, r=1.0):
    """Long skeletal / gaunt fingers from the wrist w, hanging along `down`, spread along `fwd`."""
    w, out, down, fwd = (np.asarray(x, float) for x in (w, out, down, fwd))
    h = ellipsoid(0.05 * s * r, 0.11 * s, 0.1 * s, T(w + down * 0.1 * s))
    for i, dz in enumerate((-0.075, -0.025, 0.025, 0.075)):
        ln = (0.3, 0.34, 0.32, 0.26)[i] * length
        a = w + down * 0.18 * s + fwd * dz * s * 1.3
        b = a + down * ln * 0.55 * s - out * 0.04 * s + fwd * dz * 0.3 * s
        c = b + down * ln * 0.45 * s - out * 0.12 * s
        h = h | tube([T(a), T(b), T(c)], [0.028 * s * r, 0.024 * s * r, 0.012 * s], k=0.01)
    h = h | tube([T(w + down * 0.08 * s + fwd * 0.08 * s), T(w + down * 0.2 * s + fwd * 0.17 * s - out * 0.05 * s), T(w + down * 0.3 * s + fwd * 0.2 * s - out * 0.12 * s)],
                 [0.03 * s * r, 0.025 * s * r, 0.012 * s], k=0.01)
    return h


# ================================================================================================ ghost
@hero("ghost", "spirits")
def ghost():
    """Classic sheet ghost: domed head, sleeve arms with stubby fingers, a ragged flared hem that sweeps back into a
    curling tail, hollow eyes and an 'O' mouth."""
    H = Hero("ghost", plan="Ghost", gait="float", tags=["ghost", "undead"])
    H.preview = {"primary": "#E8EAF0", "secondary": "#A5B4FC"}
    H.body((0, 2.2, 0))
    H.bone("Spine", "Body", (0, 2.5, 0))
    H.bone("Head", "Spine", (0, 3.15, 0))
    H.bone("Tail1", "Body", (0, 1.55, 0.1))
    H.bone("Tail2", "Tail1", (0, 0.95, 0.75))
    H.bone("Tail3", "Tail2", (0, 0.95, 1.5))
    arms = _arm_bones(H, A(0.68, 2.85, 0.0), A(1.08, 2.4, -0.2), A(1.25, 2.0, -0.45))
    hd = sphere(0.78, (0, 3.5, 0.02))
    hd = hd.su(ellipsoid(0.8, 0.5, 0.75, (0, 3.05, 0.04)), 0.25)
    hd = hd.ss(ellipsoid(0.13, 0.2, 0.12, (0.27, 3.55, -0.73)).mirror_x(), 0.06)
    hd = hd.ss(ellipsoid(0.12, 0.16, 0.12, (0, 3.13, -0.73)), 0.05)
    hd = hd.su(ellipsoid(0.12, 0.08, 0.08, (0.43, 3.32, -0.6)).mirror_x(), 0.08)  # cheeks
    H.piece("HeadP", "Head", hd, col="primary", mat="cloth", tris=1800, res=128, role="head")
    H.mprim("Eye#", "Head", "Ellipsoid", (0.2, 0.32, 0.12), (0.27, 3.55, -0.66), rot=(0.1, 0.15, 0), col="black", mat="hard", role="eye", pri=1.5)
    H.mprim("Shine#", "Head", "Ball", (0.07, 0.07, 0.07), (0.3, 3.62, -0.72), col="shine", mat="hard", role="shine", pri=2.5)
    H.prim("Mouth", "Head", "Ellipsoid", (0.2, 0.26, 0.12), (0, 3.13, -0.67), col="black", mat="hard", role="mouth", pri=1.5)
    bd = round_cone((0, 3.0, 0.03), (0, 1.75, 0.12), 0.8, 1.02)
    bd = bd.noise(0.015, 5, 1)
    H.piece("Sheet", "Spine", bd, col="primary", mat="cloth", tris=1500, res=120)
    hem = round_cone((0, 1.95, 0.12), (0, 0.85, 0.35), 1.0, 1.18)
    hem = hem & ragged_cut(0.68, 0.38, 6, jag=False, center=(0, 0.2), seed=2)
    hem = hem.ss(round_cone((0, 1.6, 0.12), (0, 0.55, 0.4), 0.88, 1.06), 0.04)
    def folds(p, h=hem):
        a = np.arctan2(p[:, 0], p[:, 2] - 0.2)
        return h(p) + 0.035 * np.sin(a * 9) * np.clip((1.9 - p[:, 1]) / 1.0, 0, 1)
    H.piece("Hem", "Tail1", SDF(folds), col="primary", mat="cloth", tris=1800, res=128, role="cloth")
    tl = tube([(0, 1.25, 0.55), (0, 0.95, 1.0), (0, 0.95, 1.5)], [0.6, 0.42, 0.3], k=0.15)
    H.piece("TailA", "Tail2", tl.noise(0.015, 5, 3), col="primary", mat="cloth", tris=700, role="tail", pri=1.4)
    tl2 = tube([(0, 0.95, 1.4), (0, 1.05, 1.95), (0, 1.45, 2.25), (0, 1.75, 2.1)], [0.3, 0.2, 0.11, 0.03], k=0.08)
    H.piece("TailB", "Tail3", tl2, col="primary", mat="cloth", tris=600, role="tail", pri=1.5)
    for sx, nm in ((1, "R"), (-1, "L")):
        def m(p, sx=sx):
            return A(p[0] * sx, p[1], p[2])
        up = round_cone(T(m((0.55, 2.95, 0.0))), T(m((1.08, 2.4, -0.2))), 0.28, 0.21)
        H.piece("Sleeve" + nm, "Shoulder" + nm, up, col="primary", mat="cloth", tris=600, role="limb", key=f"h_ghost_sleeve{'' if sx > 0 else '_l'}")
        lo = round_cone(T(m((1.08, 2.42, -0.2))), T(m((1.24, 2.0, -0.45))), 0.21, 0.25)
        lo = lo.su(ellipsoid(0.24, 0.14, 0.26, T(m((1.25, 1.88, -0.47)))), 0.08)
        drape = plate([(-0.2, 0), (0.22, 0), (0.15, -0.28), (0.05, -0.42), (-0.08, -0.3)], T(m((1.24, 1.9, -0.32))), (0, 0, -1), (0, 1, 0), 0.03)
        lo = lo | drape
        H.piece("Cuff" + nm, "Elbow" + nm, lo, col="primary", mat="cloth", tris=600, role="limb", key=f"h_ghost_cuff{'' if sx > 0 else '_l'}")
        fg = None
        w = m((1.26, 1.85, -0.5))
        for i, dz in enumerate((-0.11, 0.0, 0.11)):
            a = w + A(0, 0, dz)
            b = a + A(-0.03 * sx, -0.22, -0.06 + dz * 0.3)
            c = b + A(-0.06 * sx, -0.12, 0.02)
            one = tube([T(a), T(b), T(c)], [0.075, 0.065, 0.05], k=0.03)
            fg = one if fg is None else fg.su(one, 0.03)
        H.piece("Fingers" + nm, "Hand" + nm, fg, col="primary", mat="cloth", tris=500, role="hand", key=f"h_ghost_fingers{'' if sx > 0 else '_l'}")
    H.socket("mouth", (0, 3.13, -0.75), "Head")
    H.socket("head", (0, 4.25, 0), "Head")
    H.rig.update({"head": "Head", "tail": ["Tail1", "Tail2", "Tail3"]})
    mm.floater(H, arms=arms, spine="Spine", head="Head", tail=["Tail1", "Tail2", "Tail3"], height=4.3, hover=0.3)
    return H


# ================================================================================================ wraith / reaper / banshee
def _robed_spirit(hid, face="void", weapon=None, preview=None, eyecol="secondary", tall=1.0, tattered=1.0, crown=False, hood=True,
                  chains=False, collar=False, pauldrons=False):
    H = Hero(hid, plan="Ghost", gait="float", tags=["ghost", "undead"])
    H.preview = preview or {}
    s = tall
    H.body((0, 2.4 * s, 0))
    H.bone("Spine", "Body", (0, 3.0 * s, 0))
    H.bone("Head", "Spine", (0, 4.15 * s, -0.12))
    H.bone("Tail1", "Body", (0, 1.4 * s, 0.35))
    H.bone("Tail2", "Tail1", (0, 0.9 * s, 1.0))
    H.bone("Tail3", "Tail2", (0, 0.75 * s, 1.75))
    sh, el, wr = A(0.62, 3.9 * s, 0.0), A(0.98, 3.2 * s, -0.25), A(1.08, 2.55 * s, -0.6)
    arms = _arm_bones(H, sh, el, wr)
    # torso + shoulder mantle with a tattered edge
    tor = round_cone((0, 3.95 * s, 0.05), (0, 2.6 * s, 0.1), 0.55, 0.5)
    tor = tor.su(ellipsoid(0.75, 0.32, 0.45, (0, 3.85 * s, 0.05)), 0.2)
    tor = tor.noise(0.012, 6, 1)
    H.piece("Torso", "Spine", tor, col="primary", mat="cloth", tris=1300, role="body")
    man = round_cone((0, 4.15 * s, 0.05), (0, 3.4 * s, 0.08), 0.45, 0.95)
    man = man & ragged_cut(3.3 * s, 0.35, 9, center=(0, 0.05), seed=4)
    man = man.ss(round_cone((0, 3.95 * s, 0.05), (0, 3.2 * s, 0.08), 0.38, 0.86), 0.03)
    H.piece("Mantle", "Spine", man, col="primary", mat="cloth", tris=1400, res=128, role="cloth", pri=1.1)
    # lower robe: flares to a ragged hem, hollow underneath, sweeping into a tattered tail
    rb = round_cone((0, 2.9 * s, 0.1), (0, 0.7 * s, 0.35), 0.52, 0.95)
    rb = rb & ragged_cut(0.35 * s, 0.7 * tattered, 8, center=(0, 0.3), seed=5)
    rb = rb.ss(round_cone((0, 2.3 * s, 0.1), (0, 0.3 * s, 0.38), 0.42, 0.86), 0.04)
    def rfold(p, r=rb):
        a = np.arctan2(p[:, 0], p[:, 2] - 0.3)
        return r(p) + 0.03 * np.sin(a * 8 + p[:, 1] * 1.5) * np.clip((2.8 * s - p[:, 1]) / 2.0, 0, 1)
    H.piece("Robe", "Body", SDF(rfold), col="primary", mat="cloth", tris=2000, res=128, role="cloth")
    strips = None
    for i, (dx, ln, w) in enumerate(((-0.35, 1.0, 0.2), (0.0, 1.2, 0.26), (0.35, 0.95, 0.2))):
        poly = [(-w, 0), (w, 0), (w * 0.6, -ln * 0.6), (w * 0.2, -ln), (-w * 0.3, -ln * 0.75), (-w * 0.7, -ln * 0.5)]
        one = plate(poly, (dx, 1.25 * s, 0.75), (1, 0, 0), (0, 0.35, -1), 0.03, bulge=0.05)
        strips = one if strips is None else strips | one
    H.piece("Tatters", "Tail2", strips, col="primary", mat="cloth", tris=800, role="tail", pri=1.4)
    tail = tube([(0, 1.1 * s, 0.6), (0, 0.95 * s, 1.2), (0, 0.8 * s, 1.75)], [0.45, 0.3, 0.16], k=0.1)
    H.piece("TailA", "Tail1", tail.noise(0.02, 6, 2), col="primary", mat="cloth", tris=700, role="tail", pri=1.3)
    t3 = plate([(-0.18, 0), (0.18, 0), (0.12, -0.5), (0.0, -0.95), (-0.1, -0.6)], (0, 0.8 * s, 1.7), (1, 0, 0), (0, 0.3, -1), 0.03, bulge=0.06)
    H.piece("TailB", "Tail3", t3, col="primary", mat="cloth", tris=400, role="tail", pri=1.5)
    # hood
    hc = A(0, 4.5 * s, -0.12)
    hood = ellipsoid(0.48, 0.55, 0.55, T(hc + A(0, 0.05, 0.05)))
    hood = hood.su(round_cone(T(hc + A(0, 0.3, 0.25)), T(hc + A(0, 0.75, 0.55)), 0.28, 0.04), 0.15)  # peak
    hood = hood.su(round_cone(T(hc + A(0, -0.35, 0.1)), T(hc + A(0, -0.5, 0.25)), 0.45, 0.6), 0.1)
    hood = hood.ss(ellipsoid(0.34, 0.44, 0.5, T(hc + A(0, -0.05, -0.38))), 0.05)    # face opening
    hood = hood.noise(0.01, 7, 3)
    if hood:
        H.piece("Hood", "Head", hood, col="primary", mat="cloth", tris=1500, res=128, role="head")
    ks = 1.0 if hood else 1.3  # a bare lich skull is larger and sits a little lower and further forward
    if not hood:
        hc = hc + A(0, -0.12, 0.02)
    if face == "skull":
        sk = ellipsoid(0.27 * ks, 0.3 * ks, 0.31 * ks, T(hc + A(0, 0.05, -0.08)))
        sk = sk.su(ellipsoid(0.2 * ks, 0.18 * ks, 0.18 * ks, T(hc + A(0, -0.15, -0.2) * ks)), 0.08)
        if not hood:  # brow ridge, cheekbones and temples for a bare skull
            sk = sk.su(capsule(T(hc + A(-0.2, 0.1, -0.33) * ks), T(hc + A(0.2, 0.1, -0.33) * ks), 0.05), 0.05)
            sk = sk.su(ellipsoid(0.07, 0.05, 0.1, T(hc + A(0.2, -0.06, -0.25) * ks)).mirror_x(), 0.04)
        sk = sk.ss(ellipsoid(0.085 * ks, 0.08 * ks, 0.1 * ks, T(hc + A(0.1, 0.02, -0.33) * ks)).mirror_x(), 0.03)
        sk = sk.ss(round_cone(T(hc + A(0, -0.08, -0.38) * ks), T(hc + A(0, -0.17, -0.36) * ks), 0.015 * ks, 0.04 * ks), 0.02)
        for i in range(6):
            x = -0.1 + i * 0.04
            sk = sk | round_box(0.016 * ks, 0.035 * ks, 0.02 * ks, 0.008, T(hc + A(x, -0.27, -0.33 + abs(x) * 0.5) * ks))
        H.piece("Skull", "Head", sk, col=BONE, mat="hard", tris=1400 if not hood else 1200, role="face", pri=1.3)
        eyes_glow(H, "Head", T(hc + A(0.1, 0.02, -0.3) * ks), 0.045 * ks, eyecol)
    else:
        H.prim("Void", "Head", "Ellipsoid", (0.62, 0.78, 0.5), T(hc + A(0, -0.05, -0.18)), col="black", mat="hard", role="face", pri=1.2)
        eyes_glow(H, "Head", T(hc + A(0.12, 0.02, -0.42)), 0.05, eyecol, shape="Ellipsoid", size=(0.16, 0.07, 0.06), rot=(0, 0, -0.25))
    if crown:
        cr = None
        R, cy = (0.44, 0.35) if hood else (0.36, 0.36)
        for i in range(7):
            a = math.pi * (0.15 + 0.7 * i / 6) if hood else math.tau * i / 7
            p0 = hc + A(R * math.cos(a), cy, -0.05 - R * math.sin(a) * (0.6 if hood else 1.0))
            one = crystal(T(p0), T(p0 + A(0, 0.35 + 0.15 * (i % 2), 0)), 0.06, tip=0.4)
            cr = one if cr is None else cr | one
        cr = cr | torus(R + 0.01, 0.04).scale3(1, 1, 0.9 if hood else 1.0).at(*T(hc + A(0, cy - 0.02, 0.02 if hood else -0.05)))
        H.piece("Crown", "Head", cr, col="gold", mat="metal", tris=800, role="hat", pri=1.4)
    if collar:
        # tall flared sorcerer's collar standing up behind the bare skull, open at the front
        co = round_cone((0, 3.95 * s, 0.1), (0, 4.95 * s, 0.35), 0.5, 0.85).shell(0.04)
        co = co & SDF(lambda p: -(p[:, 2] - 0.0)) & SDF(lambda p: 3.9 * s - p[:, 1]) & SDF(lambda p: p[:, 1] - 4.75 * s)
        H.piece("Collar", "Spine", co, col="darker", mat="cloth", tris=900, role="cloth", pri=1.2)
    if pauldrons:
        for sx, nm in ((1, "R"), (-1, "L")):
            c0 = A(0.68 * sx, 4.05 * s, 0.02)
            pd = ellipsoid(0.36, 0.22, 0.34, T(c0)) & SDF(lambda p, y0=c0[1] - 0.08: y0 - p[:, 1])
            for k in range(3):
                pd = pd | crystal(T(c0 + A((0.05 + 0.1 * k) * sx, 0.12, -0.15 + 0.15 * k)), T(c0 + A((0.25 + 0.1 * k) * sx, 0.5 - 0.08 * k, -0.15 + 0.2 * k)), 0.05, tip=0.5, sides=4)
            H.piece("Pauldron" + nm, "Shoulder" + nm, pd, col="gold", mat="metal", tris=600, role="armor", pri=1.3,
                    key=f"h_{hid}_pauldron{'' if sx > 0 else '_l'}".replace(" ", "_"))
    # bell sleeves with bony hands
    for sx, nm in ((1, "R"), (-1, "L")):
        def m(p, sx=sx):
            return A(p[0] * sx, p[1], p[2])
        up = round_cone(T(m(sh) + A(0, 0.05, 0)), T(m(el)), 0.24, 0.22)
        H.piece("Sleeve" + nm, "Shoulder" + nm, up.noise(0.01, 7, 1), col="primary", mat="cloth", tris=600, role="limb", key=f"h_{hid}_sleeve{'' if sx > 0 else '_l'}".replace(" ", "_"))
        cuff = round_cone(T(m(el)), T(m(wr) + A(0, 0.1, 0)), 0.22, 0.36)
        cuff = cuff & ragged_cut(wr[1] - 0.18, 0.25, 5, center=(wr[0] * sx, wr[2] - 0.05), seed=7 + sx)
        cuff = cuff.ss(round_cone(T(m(el) + A(0, -0.25, -0.1)), T(m(wr) + A(0, -0.05, 0)), 0.12, 0.28), 0.03)
        H.piece("Cuff" + nm, "Elbow" + nm, cuff, col="primary", mat="cloth", tris=700, role="limb", key=f"h_{hid}_cuff{'' if sx > 0 else '_l'}".replace(" ", "_"))
        hand = bony_hand(m(wr) + A(0, 0.02, 0), 1.1, out=(sx, 0, 0), down=(0, -1, -0.25), fwd=(0, 0, -1), length=1.25)
        hand = hand | capsule(T(m(wr) + A(0, 0.25, 0.05)), T(m(wr) + A(0, -0.02, 0)), 0.05)
        H.piece("Hand" + nm + "P", "Hand" + nm, hand, col=BONE, mat="hard", tris=700, role="hand", key=f"h_{hid}_hand{'' if sx > 0 else '_l'}".replace(" ", "_"))
        if chains:
            # an iron shackle on each wrist trailing a broken chain
            w0 = m(wr) + A(0, 0.18, 0.02)
            ch = torus(0.17, 0.05).at(*T(w0))
            for k in range(6):
                c = w0 + A(0.04 * sx * k, -0.2 - 0.17 * k, 0.1 + 0.03 * k)
                link = torus(0.085, 0.028).rot(math.pi / 2, 0, 0) if k % 2 == 0 else torus(0.085, 0.028).rot(0, 0, math.pi / 2)
                ch = ch | link.scale3(1, 1.4, 1).at(*T(c))
            H.piece("Chain" + nm, "Hand" + nm, ch, col="gunmetal", mat="metal", tris=700, role="detail", pri=1.5,
                    key=f"h_{hid}_chain{'' if sx > 0 else '_l'}".replace(" ", "_"))
    if weapon == "scythe":
        g = wr + A(-0.02, -0.15, -0.05)
        sh_ = tube([T(g + A(0, -1.3, 0.25)), T(g), T(g + A(0, 2.1, -0.3))], [0.055, 0.055, 0.05], k=0.02)
        H.piece("Snath", "HandR", sh_.noise(0.006, 12, 2), col="darkWood", mat="wood", tris=500, role="weapon", pri=1.4)
        top = g + A(0, 2.05, -0.28)
        bl = plate([(0, 0.05), (0.25, 0.08), (0.75, 0.0), (1.25, -0.22), (1.55, -0.55), (1.15, -0.3), (0.6, -0.12), (0.05, -0.12)], T(top), (0, -0.05, -1), (0, 1, 0), 0.025)
        bl = bl | round_box(0.07, 0.12, 0.09, 0.03, T(top))
        H.piece("Blade", "HandR", bl, col="steel", mat="metal", tris=600, role="weapon", pri=1.5, ao=False)
    elif weapon == "staff":
        g = wr + A(-0.02, -0.15, -0.05)
        st = tube([T(g + A(0, -1.9, 0.1)), T(g), T(g + A(0, 1.5, -0.05))], [0.05, 0.055, 0.05], k=0.02)
        top = g + A(0, 1.55, -0.05)
        claw = None
        for i in range(4):
            a = math.tau * i / 4 + 0.4
            one = tube([T(top + A(0, -0.1, 0)), T(top + A(0.16 * math.cos(a), 0.15, 0.16 * math.sin(a))), T(top + A(0.06 * math.cos(a), 0.42, 0.06 * math.sin(a)))], [0.04, 0.035, 0.015], k=0.01)
            claw = one if claw is None else claw | one
        H.piece("Staff", "HandR", st.noise(0.006, 12, 2) | claw, col="darkWood", mat="wood", tris=800, role="weapon", pri=1.4)
        H.prim("Phylactery", "HandR", "Ball", (0.2, 0.2, 0.2), T(top + A(0, 0.2, 0)), col="secondary", mat="hard", glow=True, role="orb", pri=1.6)
    H.socket("mouth", T(hc + A(0, -0.1, -0.5)), "Head")
    H.socket("head", T(hc + A(0, 0.6, 0)), "Head")
    H.socket("hand", T(wr + A(0, -0.2, 0)), "HandR")
    H.rig.update({"head": "Head", "tail": ["Tail1", "Tail2", "Tail3"]})
    mm.floater(H, arms=arms, spine="Spine", head="Head", tail=["Tail1", "Tail2", "Tail3"], height=4.8 * s, hover=0.35,
               attack="cast" if weapon else "lunge", weapon_arm="ShoulderR" if weapon else None)
    if weapon:
        def swing(t):
            sN = t / 1.0
            w = mm.ease(sN / 0.35) * (1 - mm.ease((sN - 0.35) / 0.15))
            st = mm.bump(sN, 0.3, 0.8)
            return {"Spine": (0, 0, 0, 0, 0.5 * w - 0.8 * st, 0), "ShoulderR": (0, 0, 0, 0.6 * w, 0, 0.6 * w - 0.4 * st)}
        mm.overlay(H, "Attack", swing)
    return H


@hero("wraith", "spirits")
def wraith():
    return _robed_spirit("wraith", face="void", chains=True, tattered=1.3, preview={"primary": "#30353F", "secondary": "#9AA4FF"})


@hero("grim reaper", "spirits")
def reaper():
    return _robed_spirit("grim reaper", face="skull", weapon="scythe", tall=1.08, preview={"primary": "#1A1A1E", "secondary": "#E5E7EB"},
                         eyecol=[1.0, 0.35, 0.2])


@hero("lich", "spirits")
def lich():
    return _robed_spirit("lich", face="skull", crown=True, hood=False, collar=True, pauldrons=True, weapon="staff", tattered=0.7,
                         preview={"primary": "#3B2A5A", "secondary": "#7CF0C0"})


@hero("banshee", "spirits")
def banshee():
    """Wailing ghost woman: gaunt face with a gaping mouth, long hair streaming back in two lagging locks, thin bare
    arms with long fingers, a fitted bodice flowing into a gown that dissolves into a tattered tail."""
    H = Hero("banshee", plan="Ghost", gait="float", tags=["ghost", "undead"])
    H.preview = {"primary": "#C9D2E0", "secondary": "#6366F1", "skin": "#D8DEE8", "hair": "#EEF1F6"}
    H.body((0, 2.3, 0))
    H.bone("Spine", "Body", (0, 2.9, 0))
    H.bone("Head", "Spine", (0, 4.15, -0.08))
    H.bone("Jaw", "Head", (0, 4.33, -0.12))
    H.bone("Hair1", "Head", (0, 4.6, 0.25))
    H.bone("Hair2", "Hair1", (0, 4.1, 1.05))
    H.bone("Tail1", "Body", (0, 1.5, 0.3))
    H.bone("Tail2", "Tail1", (0, 0.9, 1.0))
    sh, el, wr = A(0.45, 3.8, 0.0), A(0.72, 3.15, -0.2), A(0.85, 2.55, -0.5)
    arms = _arm_bones(H, sh, el, wr)
    skin = [0.84, 0.87, 0.92]
    tor = ellipsoid(0.36, 0.42, 0.25, (0, 3.55, 0.0))
    tor = tor.su(ellipsoid(0.13, 0.12, 0.1, (0.13, 3.62, -0.2)).mirror_x(), 0.08)
    tor = tor.su(round_cone((0, 3.1, 0.02), (0, 2.6, 0.04), 0.26, 0.3), 0.15)
    tor = tor.su(capsule((-0.42, 3.82, 0.02), (0.42, 3.82, 0.02), 0.12), 0.12)
    tor = tor.su(round_cone((0, 3.85, 0.0), (0, 4.3, -0.06), 0.12, 0.09), 0.08)
    H.piece("Torso", "Spine", tor, col=skin, mat="skin", tris=1400)
    bod = (tor.round(0.04) & SDF(lambda p: np.maximum(2.55 - p[:, 1], p[:, 1] - (3.6 - 0.15 * np.cos(p[:, 0] * 6)))))
    H.piece("Bodice", "Spine", bod, col="primary", mat="cloth", tris=1000, role="cloth", pri=1.1)
    gown = round_cone((0, 2.75, 0.04), (0, 0.9, 0.35), 0.34, 0.85)
    gown = gown & ragged_cut(0.5, 0.6, 7, center=(0, 0.35), jag=True, seed=9)
    gown = gown.ss(round_cone((0, 2.2, 0.04), (0, 0.4, 0.38), 0.26, 0.76), 0.04)
    def gf(p, g=gown):
        a = np.arctan2(p[:, 0], p[:, 2] - 0.3)
        return g(p) + 0.03 * np.sin(a * 10 + p[:, 1] * 2) * np.clip((2.6 - p[:, 1]) / 1.8, 0, 1)
    H.piece("Gown", "Body", SDF(gf), col="primary", mat="cloth", tris=1800, res=128, role="cloth")
    tl = U(tube([(0, 1.25, 0.6), (0, 0.95, 1.2), (0, 0.9, 1.9)], [0.35, 0.22, 0.05], k=0.1),
           plate([(-0.25, 0), (0.25, 0), (0.15, -0.6), (0.0, -1.1), (-0.12, -0.7)], (0, 1.0, 1.0), (1, 0, 0), (0, 0.2, -1), 0.03, bulge=0.06))
    H.piece("Trail", "Tail2", tl, col="primary", mat="cloth", tris=800, role="tail", pri=1.4)
    # gaunt head, gaping mouth
    hc = A(0, 4.5, -0.1)
    hd = ellipsoid(0.27, 0.32, 0.31, T(hc + A(0, 0.05, 0.0)))
    hd = hd.su(ellipsoid(0.2, 0.25, 0.22, T(hc + A(0, -0.12, -0.08))), 0.1)
    hd = hd.su(ellipsoid(0.07, 0.06, 0.06, T(hc + A(0.13, -0.02, -0.24))).mirror_x(), 0.05)
    hd = hd.ss(ellipsoid(0.08, 0.07, 0.07, T(hc + A(0.1, 0.02, -0.27))).mirror_x(), 0.04)
    hd = hd.su(round_cone(T(hc + A(0, 0.02, -0.28)), T(hc + A(0, -0.08, -0.32)), 0.025, 0.035), 0.03)
    hd = hd.ss(box(0.3, 0.15, 0.3, T(hc + A(0, -0.32, -0.25))), 0.04)
    H.piece("HeadP", "Head", hd, col=skin, mat="skin", tris=1600, role="head")
    jaw = ellipsoid(0.16, 0.08, 0.17, T(hc + A(0, -0.24, -0.1))).su(sphere(0.07, T(hc + A(0, -0.27, -0.22))), 0.06)
    jaw = jaw.ss(ellipsoid(0.1, 0.05, 0.12, T(hc + A(0, -0.17, -0.15))), 0.02)
    H.piece("JawP", "Jaw", jaw, col=skin, mat="skin", tris=500, role="jaw", pri=1.3)
    H.prim("Mouth", "Head", "Ellipsoid", (0.16, 0.22, 0.16), T(hc + A(0, -0.19, -0.2)), col="mouth", mat="hard", role="mouth", pri=2.3)
    H.mprim("Socket#", "Head", "Ellipsoid", (0.13, 0.1, 0.06), T(hc + A(0.1, 0.02, -0.26)), col="black", mat="hard", role="eye", pri=1.4)
    eyes_glow(H, "Head", T(hc + A(0.1, 0.02, -0.29)), 0.03, "secondary")
    # hair: crown cap + two long streaming locks
    hr = ellipsoid(0.31, 0.34, 0.34, T(hc + A(0, 0.1, 0.04))).ss(ellipsoid(0.26, 0.3, 0.3, T(hc + A(0, -0.04, -0.2))), 0.04)
    hr = hr.su(round_cone(T(hc + A(0, 0.1, 0.25)), T(hc + A(0, 0.05, 0.55)), 0.27, 0.25), 0.1)
    hr = hr.noise(0.01, 18, 2)
    H.piece("HairCap", "Head", hr, col="hair", mat="cloth", tris=1200, role="hair", pri=1.2)
    lock1 = tube([(0, 4.65, 0.35), (0.05, 4.55, 0.8), (0.0, 4.25, 1.15)], [0.25, 0.2, 0.16], k=0.08).noise(0.015, 14, 3)
    lock1 = lock1.su(tube([(0.22, 4.4, 0.2), (0.32, 4.1, 0.55), (0.3, 3.8, 0.85)], [0.12, 0.09, 0.03], k=0.04).mirror_x(), 0.05)
    H.piece("HairA", "Hair1", lock1, col="hair", mat="cloth", tris=900, role="hair", pri=1.3)
    lock2 = tube([(0, 4.2, 1.0), (0.05, 3.95, 1.5), (-0.05, 3.85, 2.0), (0.05, 3.95, 2.35)], [0.17, 0.13, 0.07, 0.02], k=0.06).noise(0.012, 14, 4)
    H.piece("HairB", "Hair2", lock2, col="hair", mat="cloth", tris=700, role="hair", pri=1.4)
    for sx, nm in ((1, "R"), (-1, "L")):
        def m(p, sx=sx):
            return A(p[0] * sx, p[1], p[2])
        H.piece("UpperArm" + nm, "Shoulder" + nm, round_cone(T(m(sh) + A(0, 0.04, 0)), T(m(el)), 0.1, 0.07), col=skin, mat="skin", tris=400, role="limb", key=f"h_banshee_up{'' if sx > 0 else '_l'}")
        fo = round_cone(T(m(el)), T(m(wr)), 0.07, 0.05)
        fo = fo | plate([(-0.12, 0), (0.12, 0), (0.08, -0.45), (0.0, -0.6), (-0.06, -0.4)], T(m(el) + A(0.03 * sx, -0.02, 0.06)), (0, 0, 1), (0.1 * sx, 1, 0), 0.02)  # trailing sleeve rag
        H.piece("Forearm" + nm, "Elbow" + nm, fo, col=skin, mat="skin", tris=450, role="limb", key=f"h_banshee_fo{'' if sx > 0 else '_l'}")
        H.piece("HandP" + nm, "Hand" + nm, bony_hand(m(wr), 0.9, out=(sx, 0, 0), down=(0, -1, -0.3), fwd=(0, 0, -1), length=1.2, r=1.2), col=skin, mat="skin", tris=600, role="hand", key=f"h_banshee_hand{'' if sx > 0 else '_l'}")
    H.socket("mouth", T(hc + A(0, -0.2, -0.32)), "Jaw")
    H.socket("head", T(hc + A(0, 0.45, 0)), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": ["Tail1", "Tail2"]})
    mm.floater(H, arms=arms, spine="Spine", head="Head", jaw="Jaw", tail=["Tail1", "Tail2"], hair=["Hair1", "Hair2"], height=4.9, hover=0.35)
    mm.overlay(H, "Idle", lambda t: {"Jaw": (0, 0, 0, -0.25, 0, 0)})
    mm.overlay(H, "Move", lambda t: {"Jaw": (0, 0, 0, -0.25, 0, 0), "Hair1": (0, 0, 0, -0.15, 0, 0)})
    return H


# ================================================================================================ elementals
def _elem_arms(H, sh, el, wr, parent="Spine"):
    return _arm_bones(H, sh, el, wr, parent)


@hero("fire elemental", "spirits")
def fire_elemental():
    """A muscled body of sculpted flame on a narrowing vortex, charred rock plates on chest / shoulders / forearms, a
    rock mask with ember eye slits crowned by tall flame hair, flame tongues trailing from elbows and back."""
    H = Hero("fire elemental", plan="Ghost", gait="float", tags=["elemental", "fire"])
    H.preview = {"primary": "#EA580C", "secondary": "#FDE047", "dark": "#2B2524"}
    H.body((0, 2.3, 0))
    H.bone("Spine", "Body", (0, 2.75, 0))
    H.bone("Head", "Spine", (0, 4.25, -0.1))
    H.bone("Tail1", "Body", (0, 1.9, 0.05))
    H.bone("Tail2", "Tail1", (0, 1.0, 0.15))
    sh, el, wr = A(0.95, 3.95, 0.0), A(1.3, 3.1, -0.1), A(1.4, 2.35, -0.35)
    arms = _elem_arms(H, sh, el, wr)
    tor = ellipsoid(0.75, 0.62, 0.48, (0, 3.6, 0.0))
    tor = tor.su(ellipsoid(0.32, 0.22, 0.18, (0.32, 3.75, -0.32)).mirror_x(), 0.12)
    tor = tor.su(capsule((-0.85, 3.9, 0.02), (0.85, 3.9, 0.02), 0.32), 0.25)
    tor = tor.su(round_cone((0, 3.15, 0.0), (0, 2.45, 0.05), 0.5, 0.42), 0.2)
    back = None
    for i, (x, y, z, ln) in enumerate(((0.35, 3.9, 0.35, 0.9), (-0.35, 3.85, 0.35, 0.95), (0, 3.5, 0.45, 0.8), (0.55, 3.4, 0.3, 0.6), (-0.55, 3.45, 0.3, 0.6))):
        back = U(back, flame((x, y, z), (x * 0.4, 0.9, 0.7), ln, 0.17, side=(1 if i % 2 else -1, 0, 0), curl=0.2))
    tor = tor.su(back, 0.08)
    H.piece("Torso", "Spine", tor, col="primary", mat="plastic", tris=2400, res=128)
    plates = U(ellipsoid(0.42, 0.28, 0.14, (0.28, 3.72, -0.4)).mirror_x(), ellipsoid(0.3, 0.2, 0.32, (0.95, 4.1, 0.0)).mirror_x(), k=0.0).noise(0.03, 8, 3)
    plates = plates.ss(sphere(0.17, (0, 3.6, -0.55)), 0.04)
    H.piece("RockPlates", "Spine", plates, col="dark", mat="stone", tris=1100, role="armor", pri=1.2)
    H.prim("Core", "Spine", "Ball", (0.26, 0.26, 0.26), (0, 3.58, -0.43), col="secondary", mat="hard", glow=True, role="core", pri=1.6)
    vortex = None
    for i in range(6):
        a = i / 6 * math.tau
        b = A(0.35 * math.cos(a), 2.6, 0.35 * math.sin(a))
        vortex = U(vortex, flame(T(b), (-0.35 * math.cos(a + 0.6), -1, -0.35 * math.sin(a + 0.6)), 1.9 - 0.2 * (i % 2), 0.32, side=(math.sin(a), 0, -math.cos(a)), curl=0.25), k=0.1)
    vortex = vortex.su(round_cone((0, 2.7, 0.03), (0, 1.3, 0.1), 0.48, 0.2), 0.15)
    H.piece("Vortex", "Tail1", vortex, col="primary", mat="plastic", tris=2200, res=128, role="tail")
    inner = U(*(flame((0.18 * math.cos(a), 2.9, 0.18 * math.sin(a) - 0.2), (0.25 * math.cos(a), 1, 0.25 * math.sin(a) - 0.1), 0.75, 0.15,
                      side=(math.cos(a + 1.5), 0, math.sin(a + 1.5)), curl=0.3) for a in (0.3, 1.9, 3.6, 5.0)))
    H.piece("Licks", "Spine", inner, col="secondary", mat="plastic", tris=900, role="flame", pri=1.3)
    tip = U(flame((0, 1.4, 0.1), (0.15, -1, 0.3), 0.9, 0.22, side=(1, 0, 0), curl=0.35), flame((0.1, 1.5, 0.05), (-0.3, -1, 0.1), 0.6, 0.12, side=(0, 0, 1), curl=0.3))
    H.piece("VortexTip", "Tail2", tip, col="primary", mat="plastic", tris=600, role="tail", pri=1.4)
    # head: rock mask + flame hair
    hc = A(0, 4.55, -0.12)
    mask = ellipsoid(0.32, 0.36, 0.32, T(hc))
    mask = mask.su(capsule(T(hc + A(-0.25, 0.08, -0.26)), T(hc + A(0.25, 0.08, -0.26)), 0.08), 0.06)
    mask = mask.su(ellipsoid(0.22, 0.14, 0.2, T(hc + A(0, -0.25, -0.12))), 0.1)
    mask = mask.ss(capsule(T(hc + A(0.08, 0.0, -0.3)), T(hc + A(0.22, 0.04, -0.27)), 0.05).mirror_x(), 0.02)
    mask = mask.ss(capsule(T(hc + A(-0.12, -0.25, -0.3)), T(hc + A(0.12, -0.25, -0.3)), 0.04), 0.02)
    H.piece("Mask", "Head", mask.noise(0.025, 9, 4), col="dark", mat="stone", tris=1200, role="head")
    eyes_glow(H, "Head", T(hc + A(0.15, 0.02, -0.25)), 0.05, "secondary", shape="Ellipsoid", size=(0.17, 0.07, 0.07), rot=(0, 0, -0.2))
    H.prim("MouthGlow", "Head", "Ellipsoid", (0.22, 0.07, 0.08), T(hc + A(0, -0.25, -0.26)), col="secondary", mat="hard", glow=True, role="mouth", pri=1.6)
    hair = None
    for i, (x, z, ln) in enumerate(((0, -0.1, 1.2), (0.2, 0.05, 1.0), (-0.2, 0.05, 1.0), (0.12, 0.25, 0.85), (-0.12, 0.25, 0.85), (0.3, -0.12, 0.7), (-0.3, -0.12, 0.7))):
        hair = U(hair, flame(T(hc + A(x, 0.2, z)), (x * 0.8, 1, 0.45 + z), ln, 0.17, side=(1 if i % 2 else -1, 0, 0.3), curl=0.22), k=0.05)
    H.piece("FlameHair", "Head", hair, col="primary", mat="plastic", tris=1500, res=128, role="hair", pri=1.2)
    for sx, nm in ((1, "R"), (-1, "L")):
        def m(p, sx=sx):
            return A(p[0] * sx, p[1], p[2])
        ua = round_cone(T(m(sh) + A(0, 0.05, 0)), T(m(el)), 0.3, 0.22).su(ellipsoid(0.32, 0.36, 0.32, T(m(sh) + A(0.05, -0.15, 0))), 0.12)
        ua = ua.su(flame(T(m(el) + A(0, 0.1, 0.12)), (0.2 * sx, 0.6, 1), 0.7, 0.13, side=(0, 1, 0), curl=0.25), 0.05)
        H.piece("UpperArm" + nm, "Shoulder" + nm, ua, col="primary", mat="plastic", tris=900, role="limb", key=f"h_fireel_up{'' if sx > 0 else '_l'}")
        fo = round_cone(T(m(el)), T(m(wr)), 0.22, 0.17)
        H.piece("Forearm" + nm, "Elbow" + nm, fo, col="primary", mat="plastic", tris=500, role="limb", key=f"h_fireel_fo{'' if sx > 0 else '_l'}")
        br = round_cone(T(m(el) + 0.45 * (m(wr) - m(el))), T(m(wr) + A(0, 0.05, 0)), 0.25, 0.22).noise(0.025, 9, 5 + sx)
        H.piece("Bracer" + nm, "Elbow" + nm, br, col="dark", mat="stone", tris=600, role="armor", pri=1.3, key=f"h_fireel_br{'' if sx > 0 else '_l'}")
        fist = round_box(0.18, 0.2, 0.22, 0.09, T(m(wr) + A(0, -0.22, -0.02))).su(capsule(T(m(wr) + A(-0.06 * sx, -0.36, 0.12)), T(m(wr) + A(-0.06 * sx, -0.36, -0.18)), 0.09), 0.05)
        fist = fist.su(flame(T(m(wr) + A(0, -0.1, 0.1)), (0, 0.4, 1), 0.55, 0.12, side=(0, 1, 0), curl=0.2), 0.04)
        H.piece("Fist" + nm, "Hand" + nm, fist, col="primary", mat="plastic", tris=700, role="hand", key=f"h_fireel_fist{'' if sx > 0 else '_l'}")
    H.socket("mouth", T(hc + A(0, -0.25, -0.35)), "Head")
    H.socket("head", T(hc + A(0, 0.5, 0)), "Head")
    H.socket("hand", T(wr + A(0, -0.25, 0)), "HandR")
    H.rig.update({"head": "Head", "tail": ["Tail1", "Tail2"]})
    mm.floater(H, arms=arms, spine="Spine", head="Head", tail=["Tail1", "Tail2"], height=5.0, hover=0.25, lean=0.15)
    return H


@hero("water elemental", "spirits")
def water_elemental():
    """A smooth translucent body on a twisting water spout, wave-crest head curling forward with foam, arms that
    end in curling wave hands, foam caps."""
    H = Hero("water elemental", plan="Ghost", gait="float", tags=["elemental", "water"])
    H.preview = {"primary": "#2B8CD6", "secondary": "#E6FAFF"}
    H.body((0, 2.3, 0))
    H.bone("Spine", "Body", (0, 2.75, 0))
    H.bone("Head", "Spine", (0, 4.2, -0.05))
    H.bone("Tail1", "Body", (0, 1.9, 0.05))
    H.bone("Tail2", "Tail1", (0, 1.0, 0.15))
    sh, el, wr = A(0.85, 3.9, 0.0), A(1.2, 3.1, -0.15), A(1.3, 2.4, -0.45)
    arms = _elem_arms(H, sh, el, wr)
    tor = ellipsoid(0.68, 0.6, 0.45, (0, 3.55, 0.0)).su(capsule((-0.75, 3.88, 0.02), (0.75, 3.88, 0.02), 0.26), 0.25)
    tor = tor.su(round_cone((0, 3.15, 0.0), (0, 2.4, 0.05), 0.48, 0.38), 0.2)
    tor = tor.ss(sphere(0.18, (0, 3.55, -0.5)), 0.1)
    H.piece("Torso", "Spine", tor, col="primary", mat="glass", tr=0.15, tris=1800)
    H.prim("Core", "Spine", "Ball", (0.28, 0.28, 0.28), (0, 3.55, -0.32), col="secondary", mat="glass", role="core", pri=1.5)
    spout = SDF(lambda p: (cone(0.2, 0.55, 0.75, axis=1).at(0, 1.95, 0.08))(p))
    def sp(p):
        q = p.copy()
        y = q[:, 1]
        ang = (y - 1.2) * 2.4
        c, s_ = np.cos(ang), np.sin(ang)
        x = q[:, 0]
        z = q[:, 2] - 0.08
        r = np.sqrt(x * x + z * z)
        a = np.arctan2(z, x)
        R = 0.2 + 0.35 * np.clip((y - 1.0) / 1.7, 0, 1) ** 1.2
        d = r - R * (1 + 0.18 * np.sin(3 * a + ang))
        d = np.maximum(d, np.maximum(1.0 - y, y - 2.75))
        return d * 0.7
    spout = SDF(sp).su(sphere(0.25, (0, 1.05, 0.08)), 0.15)
    H.piece("Spout", "Tail1", spout, col="primary", mat="glass", tr=0.15, tris=1800, res=128, role="tail")
    # a thin current that coils up the spout and breaks into a curl near the waist (replaces the stacked rings)
    pts, rad = [], []
    for i in range(14):
        t = i / 13
        a = t * 1.5 * math.tau + 0.6
        r = 0.32 + 0.3 * t
        pts.append((r * math.cos(a), 1.15 + 1.45 * t, r * math.sin(a) + 0.08))
        rad.append(0.03 + 0.05 * math.sin(math.pi * min(1.0, t * 1.15)))
    ring = tube(pts, rad, k=0.03)
    H.piece("SprayRings", "Tail1", ring, col="secondary", mat="glass", tris=800, role="detail", pri=1.3)
    drop = U(sphere(0.18, (0, 0.85, 0.12)), round_cone((0, 0.85, 0.12), (0.05, 0.45, 0.2), 0.15, 0.03), k=0.05)
    H.piece("Drip", "Tail2", drop, col="primary", mat="glass", tr=0.15, tris=400, role="tail", pri=1.4)
    hc = A(0, 4.5, -0.08)
    hd = ellipsoid(0.32, 0.36, 0.33, T(hc)).su(capsule(T(hc + A(-0.2, 0.08, -0.26)), T(hc + A(0.2, 0.08, -0.26)), 0.06), 0.08)
    hd = hd.su(ellipsoid(0.22, 0.16, 0.2, T(hc + A(0, -0.22, -0.12))), 0.1)
    crest = tube([T(hc + A(0, 0.15, 0.3)), T(hc + A(0, 0.55, 0.25)), T(hc + A(0, 0.75, -0.1)), T(hc + A(0, 0.6, -0.38)), T(hc + A(0, 0.42, -0.35))],
                 [0.24, 0.22, 0.16, 0.1, 0.04], k=0.08)
    crest = crest.scale3(1.0, 1.0, 1.0)
    hd = hd.su(crest, 0.12)
    hd = hd.su(tube([T(hc + A(0.25, 0.1, 0.1)), T(hc + A(0.38, 0.3, 0.35)), T(hc + A(0.32, 0.5, 0.55))], [0.12, 0.08, 0.02], k=0.05).mirror_x(), 0.06)
    H.piece("HeadP", "Head", hd, col="primary", mat="glass", tr=0.12, tris=1600, role="head")
    foam = U(sphere(0.1, T(hc + A(0, 0.47, -0.36))), sphere(0.08, T(hc + A(0.08, 0.55, -0.3))), sphere(0.08, T(hc + A(-0.08, 0.57, -0.28))),
             sphere(0.09, T(hc + A(0, 0.72, -0.12))), k=0.04).noise(0.01, 20, 2)
    H.piece("Foam", "Head", foam, col="secondary", mat="cloth", tris=400, role="detail", pri=1.4)
    eyes_glow(H, "Head", T(hc + A(0.13, 0.02, -0.28)), 0.05, "secondary", shape="Ellipsoid", size=(0.14, 0.09, 0.06), rot=(0, 0, -0.15))
    for sx, nm in ((1, "R"), (-1, "L")):
        def m(p, sx=sx):
            return A(p[0] * sx, p[1], p[2])
        ua = round_cone(T(m(sh) + A(0, 0.05, 0)), T(m(el)), 0.26, 0.19).su(ellipsoid(0.28, 0.32, 0.28, T(m(sh) + A(0.04, -0.12, 0))), 0.12)
        H.piece("UpperArm" + nm, "Shoulder" + nm, ua, col="primary", mat="glass", tr=0.15, tris=700, role="limb", key=f"h_waterel_up{'' if sx > 0 else '_l'}")
        fo = round_cone(T(m(el)), T(m(wr)), 0.19, 0.15)
        H.piece("Forearm" + nm, "Elbow" + nm, fo, col="primary", mat="glass", tr=0.15, tris=500, role="limb", key=f"h_waterel_fo{'' if sx > 0 else '_l'}")
        w = m(wr)
        wave = tube([T(w + A(0, 0.05, 0)), T(w + A(0.05 * sx, -0.3, -0.05)), T(w + A(0.0, -0.55, -0.3)), T(w + A(-0.05 * sx, -0.45, -0.55)), T(w + A(-0.05 * sx, -0.25, -0.55))],
                    [0.17, 0.2, 0.16, 0.1, 0.03], k=0.06)
        wave = wave.su(tube([T(w + A(0, -0.3, 0.05)), T(w + A(0.1 * sx, -0.5, 0.25)), T(w + A(0.12 * sx, -0.4, 0.45))], [0.12, 0.08, 0.02], k=0.04), 0.05)
        H.piece("WaveHand" + nm, "Hand" + nm, wave, col="primary", mat="glass", tr=0.12, tris=800, role="hand", key=f"h_waterel_hand{'' if sx > 0 else '_l'}")
        fm = U(sphere(0.08, T(w + A(-0.05 * sx, -0.25, -0.55))), sphere(0.07, T(w + A(-0.0 * sx, -0.32, -0.6))), sphere(0.06, T(w + A(-0.08 * sx, -0.2, -0.6))), k=0.03)
        H.piece("HandFoam" + nm, "Hand" + nm, fm, col="secondary", mat="cloth", tris=200, role="detail", pri=1.5, key=f"h_waterel_foam{'' if sx > 0 else '_l'}")
    H.socket("mouth", T(hc + A(0, -0.2, -0.35)), "Head")
    H.socket("head", T(hc + A(0, 0.8, 0)), "Head")
    H.socket("hand", T(wr + A(0, -0.4, -0.2)), "HandR")
    H.rig.update({"head": "Head", "tail": ["Tail1", "Tail2"]})
    mm.floater(H, arms=arms, spine="Spine", head="Head", tail=["Tail1", "Tail2"], height=5.0, hover=0.25, lean=0.15)
    return H


def _boulders(center, rad, n, seed, spread=1.0, squash=(1, 1, 1)):
    rng = np.random.default_rng(seed)
    out = None
    c = np.asarray(center, float)
    for i in range(n):
        o = rng.normal(size=3) * np.asarray(rad) * 0.45 * spread
        r = np.asarray(rad) * rng.uniform(0.45, 0.7)
        b = round_box(r[0] * squash[0], r[1] * squash[1], r[2] * squash[2], min(r) * 0.35).rot(*rng.uniform(-25, 25, 3)).at(*T(c + o))
        out = b if out is None else out.su(b, 0.06)
    return out


@hero("earth elemental", "spirits")
def earth_elemental():
    """Hulking, hunched heap of rough boulders: huge stacked shoulders with crystal clusters and moss, a low boulder
    head with glowing eye cracks, long rock-mass arms with knuckle stones, short pillar legs."""
    H = Hero("earth elemental", plan="Giant", gait="stomp", tags=["elemental", "earth"])
    H.preview = {"primary": "#7A736C", "secondary": "#C8913A", "leaf": "#5E8A3A"}
    H.body((0, 2.0, 0.1))
    H.bone("Spine", "Body", (0, 2.4, 0.1))
    H.bone("Head", "Spine", (0, 3.75, -0.7))
    sh, el, wr = A(1.25, 3.5, -0.2), A(1.55, 2.4, -0.35), A(1.6, 1.35, -0.6)
    arms = _arm_bones(H, sh, el, wr)
    H.mbone("Hip#", "Body", (0.55, 1.9, 0.15))
    H.mbone("Knee#", "Hip#", (0.6, 1.05, 0.05))
    H.mbone("Foot#", "Knee#", (0.62, 0.35, 0.1))
    stone = "primary"
    tor = U(_boulders((0, 3.2, 0.05), (0.85, 0.65, 0.65), 7, 11), ellipsoid(0.95, 0.75, 0.7, (0, 3.15, 0.0)),
            _boulders((0, 2.4, 0.1), (0.6, 0.5, 0.5), 4, 12), k=0.08).noise(0.04, 5, 1)
    tor = tor.su(_boulders((0, 3.55, 0.35), (0.7, 0.4, 0.4), 4, 13), 0.08)
    H.piece("Torso", "Spine", tor, col=stone, mat="stone", tris=2400, res=128)
    pel = _boulders((0, 1.95, 0.12), (0.6, 0.45, 0.45), 4, 14).noise(0.03, 6, 2)
    H.piece("Hips", "Body", pel, col=stone, mat="stone", tris=1000)
    moss = (tor.round(0.05) & SDF(lambda p: 3.65 - p[:, 1] + 0.12 * np.sin(p[:, 0] * 5) * np.cos(p[:, 2] * 4))).noise(0.03, 12, 3)
    H.piece("Moss", "Spine", moss, col="leaf", mat="leaf", tris=1000, role="moss", pri=1.2)
    cry = None
    rng = np.random.default_rng(5)
    for sx in (1, -1):
        base = A(1.05 * sx, 3.9, 0.15)
        for i in range(4):
            d = A(0.4 * sx + rng.uniform(-0.2, 0.2), 1.0, rng.uniform(-0.3, 0.4))
            d /= np.linalg.norm(d)
            ln = rng.uniform(0.45, 0.8)
            cry = U(cry, crystal(T(base + A(rng.uniform(-0.15, 0.15), -0.1, rng.uniform(-0.2, 0.2))), T(base + d * ln), rng.uniform(0.09, 0.14), tip=0.3, twist=rng.uniform(0, 1)))
    H.piece("Crystals", "Spine", cry, col="secondary", mat="glass", tris=900, role="crystal", pri=1.3, smooth=1)
    hc = A(0, 3.8, -0.95)
    hd = _boulders(T(hc), (0.42, 0.36, 0.4), 3, 17).su(ellipsoid(0.4, 0.34, 0.38, T(hc)), 0.08)
    hd = hd.su(capsule(T(hc + A(-0.3, 0.12, -0.3)), T(hc + A(0.3, 0.12, -0.3)), 0.11), 0.05)
    hd = hd.ss(capsule(T(hc + A(0.1, 0.0, -0.4)), T(hc + A(0.25, 0.02, -0.36)), 0.055).mirror_x(), 0.02)
    hd = hd.ss(capsule(T(hc + A(-0.18, -0.2, -0.4)), T(hc + A(0.18, -0.22, -0.38)), 0.05), 0.02)
    H.piece("HeadP", "Head", hd.noise(0.025, 7, 4), col=stone, mat="stone", tris=1200, role="head")
    eyes_glow(H, "Head", T(hc + A(0.17, 0.01, -0.36)), 0.05, "secondary", shape="Ellipsoid", size=(0.18, 0.07, 0.07))
    for sx, nm in ((1, "R"), (-1, "L")):
        def m(p, sx=sx):
            return A(p[0] * sx, p[1], p[2])
        sfx = '' if sx > 0 else '_l'
        ua = U(_boulders(T(m(sh) + A(0.1 * sx, 0.05, 0)), (0.55, 0.5, 0.5), 3, 20), round_cone(T(m(sh)), T(m(el)), 0.42, 0.33),
               _boulders(T((m(sh) + m(el)) / 2), (0.38, 0.4, 0.38), 2, 21), k=0.08).noise(0.03, 6, 5)
        H.piece("UpperArm" + nm, "Shoulder" + nm, ua, col=stone, mat="stone", tris=1100, role="limb", key=f"h_earthel_up{sfx}")
        fo = U(round_cone(T(m(el)), T(m(wr)), 0.34, 0.36), _boulders(T((m(el) + m(wr)) / 2), (0.4, 0.45, 0.4), 3, 22), k=0.08).noise(0.03, 6, 6)
        H.piece("Forearm" + nm, "Elbow" + nm, fo, col=stone, mat="stone", tris=1000, role="limb", key=f"h_earthel_fo{sfx}")
        fist = _boulders(T(m(wr) + A(0, -0.32, -0.05)), (0.48, 0.42, 0.5), 4, 23).su(ellipsoid(0.42, 0.38, 0.45, T(m(wr) + A(0, -0.3, -0.05))), 0.06)
        for i, dz in enumerate((-0.28, -0.08, 0.12)):
            fist = fist.su(round_box(0.12, 0.12, 0.1, 0.05, T(m(wr) + A(-0.12 * sx, -0.65, dz))), 0.04)
        H.piece("Fist" + nm, "Hand" + nm, fist.noise(0.025, 7, 7), col=stone, mat="stone", tris=1000, role="hand", key=f"h_earthel_fist{sfx}")
        hp, kn, ft = A(0.55 * sx, 1.9, 0.15), A(0.6 * sx, 1.05, 0.05), A(0.62 * sx, 0.35, 0.1)
        th = U(round_cone(T(hp), T(kn), 0.42, 0.36), _boulders(T((hp + kn) / 2), (0.42, 0.4, 0.42), 2, 24), k=0.08).noise(0.03, 6, 8)
        H.piece("Thigh" + nm, "Hip" + nm, th, col=stone, mat="stone", tris=800, role="limb", key=f"h_earthel_th{sfx}")
        lg = U(round_cone(T(kn), T(ft + A(0, 0.1, 0)), 0.36, 0.4), round_box(0.42, 0.25, 0.55, 0.12, T(ft + A(0, -0.1, -0.15))), k=0.1).noise(0.03, 6, 9)
        lg = lg & plane((0, -1, 0), 0.0)
        H.piece("Leg" + nm, "Knee" + nm, lg, col=stone, mat="stone", tris=900, role="foot", key=f"h_earthel_leg{sfx}")
    H.socket("mouth", T(hc + A(0, -0.2, -0.45)), "Head")
    H.socket("head", T(hc + A(0, 0.45, 0)), "Head")
    H.socket("hand", T(wr + A(0, -0.4, 0)), "HandR")
    H.rig.update({"head": "Head", "legs": [{"hip": "HipR", "knee": "KneeR", "phase": 0.0, "side": 1}, {"hip": "HipL", "knee": "KneeL", "phase": 0.5, "side": -1}]})
    mm.biped_extra(H, [("HipR", "KneeR", "FootR", 0.0), ("HipL", "KneeL", "FootL", 0.5)], list(arms), spine="Spine", head="Head",
                   stride=0.32, walk=1.4, height=4.3, attack="slam", lean=0.1, stomp=1.0)
    return H


@hero("ice elemental", "spirits")
def ice_elemental():
    """Angular figure of faceted ice: crystal-plated torso, shard crown and back spikes, long arms ending in icicle
    blades, the lower body a cluster of downward icicles over a swirl of snow."""
    H = Hero("ice elemental", plan="Ghost", gait="float", tags=["elemental", "ice"])
    H.preview = {"primary": "#A9DDF7", "secondary": "#F4FBFF"}
    H.body((0, 2.3, 0))
    H.bone("Spine", "Body", (0, 2.75, 0))
    H.bone("Head", "Spine", (0, 4.25, -0.08))
    H.bone("Tail1", "Body", (0, 1.9, 0.05))
    sh, el, wr = A(0.85, 3.95, 0.0), A(1.22, 3.15, -0.12), A(1.32, 2.45, -0.4)
    arms = _arm_bones(H, sh, el, wr)
    ice = dict(col="primary", mat="glass", tr=0.08, smooth=1)
    tor = U(crystal((0, 2.3, 0.02), (0, 4.0, 0.0), 0.5, tip=0.25), crystal((0, 3.2, 0.0), (0.85, 4.05, 0.0), 0.3, tip=0.2),
            crystal((0, 3.2, 0.0), (-0.85, 4.05, 0.0), 0.3, tip=0.2), crystal((0, 3.0, 0.15), (0, 3.9, -0.2), 0.42, tip=0.2, twist=0.5), k=0.04)
    spikes = None
    rng = np.random.default_rng(3)
    for i in range(7):
        x = rng.uniform(-0.55, 0.55)
        b = A(x, 3.4 + rng.uniform(0, 0.5), 0.25)
        spikes = U(spikes, crystal(T(b), T(b + A(x * 0.6, 0.6 + rng.uniform(0, 0.4), 0.7 + rng.uniform(0, 0.3))), 0.09 + rng.uniform(0, 0.04), tip=0.45, twist=rng.uniform(0, 1)))
    for sx in (1, -1):
        spikes = U(spikes, crystal((0.85 * sx, 3.9, 0.0), (1.2 * sx, 4.6, 0.1), 0.13, tip=0.45), crystal((0.75 * sx, 3.95, 0.1), (0.9 * sx, 4.5, 0.4), 0.1, tip=0.45))
    H.piece("Torso", "Spine", tor, tris=1600, **ice)
    H.piece("Spikes", "Spine", spikes, col="secondary", mat="glass", tris=1300, role="crystal", pri=1.2, smooth=1)
    low = None
    for i in range(7):
        a = i / 7 * math.tau
        top = A(0.32 * math.cos(a), 2.45, 0.32 * math.sin(a))
        bot = A(0.18 * math.cos(a + 0.4), 0.8 + 0.35 * (i % 3), 0.18 * math.sin(a + 0.4) + 0.1)
        low = U(low, crystal(T(top), T(bot), 0.18, tip=0.5, twist=a))
    low = U(low, crystal((0, 2.5, 0.05), (0, 0.55, 0.12), 0.26, tip=0.45))
    H.piece("Icicles", "Tail1", low, tris=1500, role="tail", **ice)
    # a spiralling drift of snow that thins out as it winds down around the icicles (not a ring of balls)
    pts, rad = [], []
    for i in range(15):
        t = i / 14
        a = t * 1.6 * math.tau
        r = 0.62 - 0.22 * t
        pts.append((r * math.cos(a), 2.2 - 1.2 * t, r * math.sin(a) + 0.05))
        rad.append(0.11 * (1 - t) + 0.025)
    snow = tube(pts, rad, k=0.04).scale3(1.0, 0.7, 1.0).at(0, 0.6, 0)
    H.piece("Flurry", "Tail1", snow.noise(0.018, 14, 2), col="secondary", mat="cloth", tris=900, role="detail", pri=1.3)
    hc = A(0, 4.55, -0.1)
    hd = U(crystal(T(hc + A(0, -0.4, 0)), T(hc + A(0, 0.35, -0.05)), 0.27, tip=0.35, twist=0.26), crystal(T(hc + A(0, -0.1, 0.0)), T(hc + A(0, -0.42, -0.3)), 0.16, tip=0.3), k=0.03)
    crown = None
    for i, (x, h_, z) in enumerate(((0, 0.75, 0.05), (0.2, 0.55, 0.1), (-0.2, 0.55, 0.1), (0.32, 0.4, 0.15), (-0.32, 0.4, 0.15))):
        crown = U(crown, crystal(T(hc + A(x * 0.5, 0.15, z)), T(hc + A(x, 0.2 + h_, z + 0.15)), 0.07, tip=0.5, twist=0.3 * i))
    H.piece("HeadP", "Head", hd, tris=700, role="head", **ice)
    H.piece("Crown", "Head", crown, col="secondary", mat="glass", tris=700, role="hat", pri=1.3, smooth=1)
    eyes_glow(H, "Head", T(hc + A(0.11, 0.05, -0.25)), 0.04, "secondary", shape="Ellipsoid", size=(0.13, 0.05, 0.05), rot=(0, 0, -0.3))
    for sx, nm in ((1, "R"), (-1, "L")):
        def m(p, sx=sx):
            return A(p[0] * sx, p[1], p[2])
        sfx = '' if sx > 0 else '_l'
        ua = crystal(T(m(sh) + A(0, 0.15, 0)), T(m(el) + A(0, -0.08, 0)), 0.2, tip=0.15, twist=0.3)
        H.piece("UpperArm" + nm, "Shoulder" + nm, ua, tris=400, role="limb", key=f"h_iceel_up{sfx}", **ice)
        fo = crystal(T(m(el) + A(0, 0.12, 0)), T(m(wr)), 0.17, tip=0.15, twist=0.6)
        H.piece("Forearm" + nm, "Elbow" + nm, fo, tris=400, role="limb", key=f"h_iceel_fo{sfx}", **ice)
        bl = U(crystal(T(m(wr) + A(0, 0.05, 0)), T(m(wr) + A(0.05 * sx, -0.95, -0.25)), 0.13, tip=0.6),
               crystal(T(m(wr) + A(0, -0.05, 0)), T(m(wr) + A(0.2 * sx, -0.55, -0.05)), 0.07, tip=0.6),
               crystal(T(m(wr) + A(0, -0.05, 0)), T(m(wr) + A(-0.12 * sx, -0.5, -0.35)), 0.07, tip=0.6))
        H.piece("Blade" + nm, "Hand" + nm, bl, tris=600, role="hand", key=f"h_iceel_blade{sfx}", **ice)
    H.socket("mouth", T(hc + A(0, -0.2, -0.3)), "Head")
    H.socket("head", T(hc + A(0, 0.9, 0)), "Head")
    H.socket("hand", T(wr + A(0, -0.8, -0.2)), "HandR")
    H.rig.update({"head": "Head", "tail": ["Tail1"]})
    mm.floater(H, arms=arms, spine="Spine", head="Head", tail=["Tail1"], height=5.0, hover=0.25, lean=0.12)
    return H


@hero("lightning elemental", "spirits")
def lightning_elemental():
    """Storm-cloud body (puffed cloud masses) split by jagged lightning-bolt fins: bolt horns, bolt shoulder blades,
    forearm bolts, and a forked bolt for a lower body."""
    H = Hero("lightning elemental", plan="Ghost", gait="float", tags=["elemental", "lightning"])
    H.preview = {"primary": "#FACC15", "secondary": "#46557A"}
    H.body((0, 2.3, 0))
    H.bone("Spine", "Body", (0, 2.75, 0))
    H.bone("Head", "Spine", (0, 4.2, -0.08))
    H.bone("Tail1", "Body", (0, 2.0, 0.05))
    H.bone("Tail2", "Tail1", (0, 1.2, 0.1))
    sh, el, wr = A(0.9, 3.9, 0.0), A(1.25, 3.1, -0.15), A(1.35, 2.4, -0.4)
    arms = _arm_bones(H, sh, el, wr)
    cloud = "secondary"
    rng = np.random.default_rng(9)
    tor = ellipsoid(0.7, 0.6, 0.45, (0, 3.5, 0.0)).su(capsule((-0.8, 3.85, 0.0), (0.8, 3.85, 0.0), 0.28), 0.25)
    for i in range(10):
        c = A(rng.uniform(-0.7, 0.7), rng.uniform(2.5, 4.0), rng.uniform(-0.2, 0.35))
        tor = tor.su(sphere(rng.uniform(0.22, 0.34), T(c)), 0.12)
    tor = tor.su(round_cone((0, 3.0, 0.05), (0, 2.2, 0.08), 0.5, 0.42), 0.2)
    H.piece("Torso", "Spine", tor, col=cloud, mat="cloth", tris=2200, res=128)
    fins = U(bolt((0.25, 4.0, 0.35), (0.3, 1, 0.6), (1, 0, 0), 1.1, 0.35, 4), bolt((-0.25, 4.0, 0.35), (-0.3, 1, 0.6), (1, 0, 0), 1.0, 0.32, 4),
             bolt((0, 3.4, 0.45), (0, 0.8, 1), (1, 0, 0), 0.9, 0.3, 3))
    chest = plate([(-0.08, 0.35), (0.12, 0.35), (0.02, 0.05), (0.15, 0.05), (-0.06, -0.38), (0.0, -0.08), (-0.14, -0.08)], (0, 3.5, -0.47), (1, 0, 0), (0, 1, 0), 0.05)
    H.piece("Bolts", "Spine", U(fins, chest), col="primary", mat="hard", tris=1200, role="bolt", pri=1.2)
    low = None
    for i in range(7):
        c = A(rng.uniform(-0.5, 0.5), rng.uniform(1.6, 2.4), rng.uniform(-0.3, 0.4))
        low = U(low, sphere(rng.uniform(0.25, 0.38), T(c)), k=0.12)
    H.piece("CloudLow", "Tail1", low, col=cloud, mat="cloth", tris=1300, role="tail")
    fork = U(bolt((0, 1.75, 0.05), (0.15, -1, 0.1), (1, 0, 0), 1.25, 0.4, 4, t=0.05), bolt((0.05, 1.5, 0.05), (-0.6, -1, 0.2), (0, 0, 1), 0.7, 0.22, 3, t=0.04))
    H.piece("Fork", "Tail2", fork, col="primary", mat="hard", tris=700, role="bolt", pri=1.3)
    hc = A(0, 4.55, -0.1)
    hd = ellipsoid(0.3, 0.33, 0.3, T(hc)).su(capsule(T(hc + A(-0.22, 0.08, -0.25)), T(hc + A(0.22, 0.08, -0.25)), 0.07), 0.06)
    hd = hd.su(ellipsoid(0.2, 0.15, 0.2, T(hc + A(0, -0.22, -0.1))), 0.1)
    for i in range(5):
        hd = hd.su(sphere(0.15, T(hc + A(rng.uniform(-0.25, 0.25), rng.uniform(0.15, 0.3), rng.uniform(0.0, 0.3)))), 0.08)
    H.piece("HeadP", "Head", hd, col=cloud, mat="cloth", tris=1300, role="head")
    horns = U(bolt(T(hc + A(0.2, 0.2, -0.05)), (0.5, 1, 0.3), (0, 0, 1), 0.8, 0.22, 3), bolt(T(hc + A(-0.2, 0.2, -0.05)), (-0.5, 1, 0.3), (0, 0, 1), 0.8, 0.22, 3))
    H.piece("BoltHorns", "Head", horns, col="primary", mat="hard", tris=600, role="horn", pri=1.3)
    eyes_glow(H, "Head", T(hc + A(0.12, 0.03, -0.27)), 0.04, "primary", shape="Ellipsoid", size=(0.15, 0.06, 0.06), rot=(0, 0, -0.3))
    for sx, nm in ((1, "R"), (-1, "L")):
        def m(p, sx=sx):
            return A(p[0] * sx, p[1], p[2])
        sfx = '' if sx > 0 else '_l'
        ua = round_cone(T(m(sh) + A(0, 0.05, 0)), T(m(el)), 0.27, 0.2).su(sphere(0.32, T(m(sh) + A(0.05, 0.0, 0))), 0.1)
        ua = ua.su(sphere(0.2, T((m(sh) + m(el)) / 2 + A(0.08 * sx, 0, 0.05))), 0.08)
        H.piece("UpperArm" + nm, "Shoulder" + nm, ua, col=cloud, mat="cloth", tris=700, role="limb", key=f"h_boltel_up{sfx}")
        H.piece("ShoulderBolt" + nm, "Shoulder" + nm, bolt(T(m(sh) + A(0.1 * sx, 0.15, 0.1)), (0.6 * sx, 1, 0.4), (0, 0, 1), 0.7, 0.24, 3), col="primary", mat="hard", tris=300, role="bolt", pri=1.3, key=f"h_boltel_sb{sfx}")
        fo = round_cone(T(m(el)), T(m(wr)), 0.2, 0.17).su(sphere(0.17, T(m(el) + 0.5 * (m(wr) - m(el)) + A(0.06 * sx, 0, 0.06))), 0.07)
        H.piece("Forearm" + nm, "Elbow" + nm, fo, col=cloud, mat="cloth", tris=600, role="limb", key=f"h_boltel_fo{sfx}")
        hb = U(bolt(T(m(wr) + A(0, 0.1, 0)), (0.1 * sx, -1, -0.35), (0, 0, 1), 0.9, 0.28, 4), sphere(0.18, T(m(wr) + A(0, -0.05, 0))))
        H.piece("HandBolt" + nm, "Hand" + nm, hb, col="primary", mat="hard", tris=500, role="hand", key=f"h_boltel_hb{sfx}")
    H.socket("mouth", T(hc + A(0, -0.2, -0.3)), "Head")
    H.socket("head", T(hc + A(0, 0.7, 0)), "Head")
    H.socket("hand", T(wr + A(0, -0.8, -0.2)), "HandR")
    H.rig.update({"head": "Head", "tail": ["Tail1", "Tail2"]})
    mm.floater(H, arms=arms, spine="Spine", head="Head", tail=["Tail1", "Tail2"], height=5.0, hover=0.25, lean=0.15)
    return H


# ================================================================================================ wisp, slime, mud
@hero("wisp", "spirits")
def wisp():
    """A small sculpted spirit: a teardrop flame body that curls into a long swirling tail, big dark eyes, a little
    smile, stubby arms and a flame tuft on top."""
    H = Hero("wisp", plan="Ghost", gait="hover", tags=["spirit"])
    H.preview = {"primary": "#67E8F9", "secondary": "#E0FBFF"}
    H.body((0, 1.6, 0))
    H.bone("Head", "Body", (0, 1.7, 0))
    H.bone("Tail1", "Body", (0, 1.2, 0.3))
    H.bone("Tail2", "Tail1", (0, 1.0, 0.95))
    H.bone("Tail3", "Tail2", (0, 1.25, 1.5))
    arms = _arm_bones(H, A(0.45, 1.55, 0.0), A(0.62, 1.35, -0.1), A(0.7, 1.15, -0.2), parent="Body")
    bd = sphere(0.62, (0, 1.75, 0.0)).su(round_cone((0, 1.9, 0.05), (0, 2.75, 0.25), 0.4, 0.03), 0.25)
    bd = bd.su(round_cone((0, 1.4, 0.15), (0, 1.15, 0.5), 0.45, 0.3), 0.2)
    bd = bd.ss(ellipsoid(0.11, 0.15, 0.1, (0.2, 1.8, -0.6)).mirror_x(), 0.04)
    bd = bd.ss(ellipsoid(0.12, 0.06, 0.1, (0, 1.53, -0.6)), 0.03)
    H.piece("BodyP", "Head", bd, col="primary", mat="glass", tr=0.1, tris=1500, res=128, role="head")
    tuft = U(flame((0.12, 2.25, 0.05), (0.4, 1, 0.3), 0.55, 0.1, side=(0, 0, 1), curl=0.3), flame((-0.12, 2.25, 0.05), (-0.4, 1, 0.3), 0.5, 0.1, side=(0, 0, 1), curl=0.3))
    H.piece("Tufts", "Head", tuft, col="secondary", mat="glass", tris=500, role="flame", pri=1.3)
    cute_eyes(H, "Head", (0.2, 1.8, -0.53), 0.1)
    H.prim("Smile", "Head", "Ellipsoid", (0.2, 0.08, 0.1), (0, 1.53, -0.55), col="mouth", mat="hard", role="mouth", pri=2.0)
    H.piece("TailA", "Tail1", tube([(0, 1.25, 0.35), (0, 1.0, 0.7), (0, 1.0, 1.0)], [0.3, 0.22, 0.17], k=0.06), col="primary", mat="glass", tr=0.1, tris=500, role="tail", pri=1.4)
    H.piece("TailB", "Tail2", tube([(0, 1.0, 0.95), (0, 1.05, 1.35), (0, 1.3, 1.6)], [0.17, 0.12, 0.09], k=0.04), col="primary", mat="glass", tr=0.1, tris=400, role="tail", pri=1.5)
    H.piece("TailC", "Tail3", tube([(0, 1.3, 1.55), (0, 1.6, 1.6), (0, 1.75, 1.35), (0, 1.62, 1.2)], [0.09, 0.07, 0.04, 0.015], k=0.03), col="secondary", mat="glass", tris=350, role="tail", pri=1.6)
    for sx, nm in ((1, "R"), (-1, "L")):
        sfx = '' if sx > 0 else '_l'
        a = tube([(0.45 * sx, 1.55, 0.0), (0.62 * sx, 1.35, -0.1), (0.72 * sx, 1.15, -0.22)], [0.12, 0.09, 0.1], k=0.04)
        H.piece("Arm" + nm, "Shoulder" + nm, a, col="primary", mat="glass", tr=0.1, tris=400, role="limb", key=f"h_wisp_arm{sfx}")
    H.socket("mouth", (0, 1.55, -0.65), "Head")
    H.socket("head", (0, 2.6, 0), "Head")
    H.rig.update({"head": "Head", "tail": ["Tail1", "Tail2", "Tail3"]})
    mm.floater(H, arms=arms, head="Head", tail=["Tail1", "Tail2", "Tail3"], height=2.5, hover=0.5, lean=0.25)
    return H


@hero("slime", "spirits")
def slime():
    """Wobbling jelly dome with a wide base lip, two big glossy eyes on the front, a mouth, a nucleus inside, drips
    running down the sides and a gloss highlight. Hops."""
    H = Hero("slime", plan="Blob", gait="hop", tags=["slime", "blob"])
    H.preview = {"primary": "#4ADE80", "secondary": "#BBF7D0"}
    H.body((0, 0.6, 0))
    H.bone("Top", "Body", (0, 0.9, 0))
    H.bone("Face", "Top", (0, 1.4, -0.9))
    drips = []
    jel = dict(col="primary", mat="glass", tr=0.25)
    base = ellipsoid(1.55, 0.5, 1.5, (0, 0.4, 0.05))
    for i in range(7):
        a = i / 7 * math.tau + 0.4
        base = base.su(ellipsoid(0.45, 0.22, 0.45, (1.45 * math.sin(a), 0.12, 1.4 * math.cos(a) + 0.05)), 0.25)
    base = base & plane((0, -1, 0), 0.0)
    H.piece("Base", "Body", base, tris=1400, res=120, **jel)
    dome = ellipsoid(1.3, 0.95, 1.22, (0, 1.05, 0.05)).su(ellipsoid(1.45, 0.5, 1.38, (0, 0.65, 0.05)), 0.35)
    dome = dome.su(round_cone((0, 1.75, 0.15), (0.15, 2.2, 0.35), 0.35, 0.06), 0.3)
    dome = dome.ss(ellipsoid(0.35, 0.18, 0.2, (0, 1.05, -1.1)), 0.08)
    H.piece("Dome", "Top", dome, tris=2000, res=128, **jel)
    H.prim("Nucleus", "Top", "Ball", (0.55, 0.55, 0.55), (0.25, 1.15, 0.35), col="secondary", mat="glass", role="core", pri=1.0, tr=0.1)
    H.prim("Gloss", "Top", "Ellipsoid", (0.35, 0.18, 0.12), (-0.6, 1.7, -0.72), rot=(0.6, 0.6, 0.5), col="white", mat="hard", role="shine", pri=2.5, tr=0.2)
    cute_eyes(H, "Face", (0.38, 1.3, -1.05), 0.2, look=(0.1, 0, -1))
    H.prim("MouthP", "Face", "Ellipsoid", (0.42, 0.16, 0.14), (0, 1.05, -1.05), col="mouth", mat="hard", role="mouth", pri=2.0)
    H.prim("Tongue", "Face", "Ellipsoid", (0.2, 0.06, 0.1), (0, 0.99, -1.1), col="tongue", mat="hard", role="mouth", pri=2.2)
    for i, (a, y) in enumerate(((0.6, 1.0), (2.2, 0.95), (3.6, 1.05), (5.0, 0.9))):
        c = A(1.25 * math.sin(a), y, 1.2 * -math.cos(a) + 0.05)
        out = A(math.sin(a), 0, -math.cos(a))
        nm = f"Drip{i + 1}"
        H.bone(nm, "Top", T(c))
        d = U(round_cone(T(c + A(0, 0.3, 0) - out * 0.08), T(c + A(0, -0.35, 0) + out * 0.06), 0.13, 0.08), sphere(0.12, T(c + A(0, -0.42, 0) + out * 0.07)), k=0.06)
        H.piece(nm + "P", nm, d, tris=300, role="drip", pri=1.6, **jel)
        drips.append(nm)
    H.socket("mouth", (0, 1.05, -1.15), "Face")
    H.socket("head", (0, 2.5, 0), "Top")
    H.rig.update({"head": "Top"})
    mm.blob(H, top="Top", eyes=["Face"], drips=drips, height=2.4)
    return H


@hero("mud monster", "spirits")
def mud_monster():
    """A slumped hulk of dripping mud rising from its own puddle: lumpy head with hollow eyes and a sagging mouth,
    heavy arms with drooping drips and stubby fingers, moss and reeds on its shoulders."""
    H = Hero("mud monster", plan="Blob", gait="slither", tags=["blob", "swamp"])
    H.preview = {"primary": "#6B4A2B", "secondary": "#6E8A2E"}
    H.body((0, 1.2, 0))
    H.bone("Spine", "Body", (0, 1.7, 0.0))
    H.bone("Head", "Spine", (0, 3.2, -0.45))
    H.bone("Jaw", "Head", (0, 3.25, -0.5))
    sh, el, wr = A(1.0, 2.95, -0.1), A(1.35, 2.1, -0.3), A(1.4, 1.35, -0.6)
    arms = _arm_bones(H, sh, el, wr)
    mud = dict(col="primary", mat="skin")
    pud = (ellipsoid(1.9, 0.3, 1.8, (0, 0.05, 0.1)) & plane((0, -1, 0), 0.0))
    for i in range(7):
        a = i / 7 * math.tau + 0.3
        pud = pud.su(ellipsoid(0.5, 0.18, 0.5, (1.75 * math.sin(a), 0.03, 1.6 * math.cos(a) + 0.1)), 0.2)
    pud = (pud & plane((0, -1, 0), 0.0)).noise(0.02, 4, 2)
    H.piece("Puddle", "Body", pud, tris=1200, **mud)
    low = (round_cone((0, 0.3, 0.1), (0, 1.7, 0.0), 1.2, 0.95) & plane((0, -1, 0), -0.05)).noise(0.05, 3, 3)
    H.piece("Mound", "Body", low, tris=1600, **mud)
    tor = ellipsoid(1.0, 0.95, 0.8, (0, 2.35, 0.0)).su(capsule((-0.9, 2.8, 0.0), (0.9, 2.8, 0.0), 0.42), 0.35)
    tor = tor.su(ellipsoid(0.6, 0.4, 0.5, (0, 2.95, 0.25)), 0.3)
    for i, (x, y, z) in enumerate(((0.5, 2.1, -0.75), (-0.3, 1.9, -0.8), (0.8, 2.2, -0.4), (-0.75, 2.4, -0.45))):
        tor = tor.su(round_cone((x, y + 0.2, z * 0.95), (x * 1.05, y - 0.35, z * 1.05), 0.14, 0.07), 0.12)
        tor = tor.su(sphere(0.09, (x * 1.05, y - 0.42, z * 1.06)), 0.06)
    tor = tor.noise(0.04, 4, 4)
    H.piece("Torso", "Spine", tor, tris=2200, res=128, **mud)
    moss = (tor.round(0.05) & SDF(lambda p: 3.05 - p[:, 1] + 0.15 * np.sin(p[:, 0] * 4 + 1) * np.cos(p[:, 2] * 5))).noise(0.03, 10, 5)
    reeds = None
    for i, (x, z, h_, lean) in enumerate(((0.75, 0.3, 0.9, 0.2), (0.62, 0.45, 0.7, -0.1), (-0.8, 0.2, 0.8, -0.25), (0.88, 0.1, 0.6, 0.35))):
        reeds = U(reeds, round_cone((x, 3.0, z), (x + lean, 3.0 + h_, z + 0.1), 0.04, 0.015))
    H.piece("Moss", "Spine", U(moss, reeds), col="secondary", mat="leaf", tris=1100, role="moss", pri=1.2)
    hc = A(0, 3.3, -0.55)
    hd = ellipsoid(0.55, 0.48, 0.5, T(hc)).su(ellipsoid(0.42, 0.25, 0.35, T(hc + A(0, 0.3, 0.1))), 0.2)
    hd = hd.ss(ellipsoid(0.13, 0.15, 0.12, T(hc + A(0.2, 0.05, -0.45))).mirror_x(), 0.06)
    hd = hd.ss(box(0.5, 0.2, 0.3, T(hc + A(0, -0.42, -0.35))), 0.06)
    hd = hd.su(round_cone(T(hc + A(0.35, -0.1, -0.3)), T(hc + A(0.38, -0.55, -0.32)), 0.08, 0.05).mirror_x(), 0.06)
    H.piece("HeadP", "Head", hd.noise(0.03, 5, 6), tris=1500, role="head", **mud)
    jaw = ellipsoid(0.38, 0.17, 0.3, T(hc + A(0, -0.35, -0.2))).su(round_cone(T(hc + A(0.1, -0.45, -0.4)), T(hc + A(0.12, -0.8, -0.4)), 0.07, 0.04), 0.06)
    H.piece("JawP", "Jaw", jaw.noise(0.02, 6, 7), tris=600, role="jaw", pri=1.3, **mud)
    H.prim("Mouth", "Head", "Ellipsoid", (0.55, 0.16, 0.4), T(hc + A(0, -0.25, -0.25)), col="mouth", mat="hard", role="mouth", pri=2.3)
    for sx, nm in ((1, "R"), (-1, "L")):
        H.prim("Socket" + nm, "Head", "Ellipsoid", (0.22, 0.26, 0.12), T(hc + A(0.2 * sx, 0.05, -0.39)), col="black", mat="hard", role="eye", pri=1.4)
        H.prim("Eye" + nm, "Head", "Ball", (0.09, 0.09, 0.09), T(hc + A(0.2 * sx, 0.05, -0.43)), col=[1.0, 0.85, 0.35], mat="hard", glow=True, role="eye", pri=1.6)
    for sx, nm in ((1, "R"), (-1, "L")):
        def m(p, sx=sx):
            return A(p[0] * sx, p[1], p[2])
        sfx = '' if sx > 0 else '_l'
        ua = round_cone(T(m(sh) + A(0, 0.05, 0)), T(m(el)), 0.42, 0.32).noise(0.04, 5, 8)
        H.piece("UpperArm" + nm, "Shoulder" + nm, ua, tris=800, role="limb", key=f"h_mud_up{sfx}", **mud)
        fo = round_cone(T(m(el)), T(m(wr)), 0.32, 0.3)
        fo = fo.su(round_cone(T((m(el) + m(wr)) / 2 + A(0, 0, 0.2)), T((m(el) + m(wr)) / 2 + A(0.05 * sx, -0.5, 0.25)), 0.12, 0.06), 0.1)
        fo = fo.su(sphere(0.09, T((m(el) + m(wr)) / 2 + A(0.05 * sx, -0.58, 0.26))), 0.05)
        H.piece("Forearm" + nm, "Elbow" + nm, fo.noise(0.03, 5, 9), tris=800, role="limb", key=f"h_mud_fo{sfx}", **mud)
        w = m(wr)
        hand = ellipsoid(0.3, 0.3, 0.32, T(w + A(0, -0.15, -0.05)))
        for i, dz in enumerate((-0.22, -0.05, 0.12)):
            hand = hand.su(round_cone(T(w + A(-0.03 * sx, -0.3, dz - 0.05)), T(w + A(-0.1 * sx, -0.65, dz - 0.15)), 0.1, 0.06), 0.06)
        hand = hand.su(round_cone(T(w + A(0, -0.3, 0.2)), T(w + A(0, -0.8, 0.25)), 0.08, 0.03), 0.05)
        H.piece("HandP" + nm, "Hand" + nm, hand.noise(0.02, 7, 10), tris=700, role="hand", key=f"h_mud_hand{sfx}", **mud)
    H.socket("mouth", T(hc + A(0, -0.3, -0.5)), "Jaw")
    H.socket("head", T(hc + A(0, 0.6, 0)), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw"})
    mm.floater(H, arms=arms, spine="Spine", head="Head", jaw="Jaw", height=4.0, hover=0.0, lean=0.1)
    def settle(t):
        return {"Body": (0, -0.12, 0, 0, 0, 0)}
    for c in ("Idle", "Move", "Attack", "Hit"):
        mm.overlay(H, c, settle)
    return H


# ================================================================================================ treant
@hero("treant", "spirits")
def treant():
    """Walking tree: a ridged bark trunk torso with a carved face (deep brow, knot eyes, mossy beard), branch arms
    with twig fingers, root legs with splayed root toes, and a canopy of leaf clusters on its head and shoulders."""
    H = Hero("treant", plan="Giant", gait="stomp", tags=["plant", "tree"])
    H.preview = {"primary": "#6B4A2E", "secondary": "#4D7C0F", "leaf": "#4E9A3A"}
    H.body((0, 2.4, 0.05))
    H.bone("Spine", "Body", (0, 2.9, 0.05))
    H.bone("Head", "Spine", (0, 5.0, -0.05))
    sh, el, wr = A(0.95, 4.4, 0.0), A(1.45, 3.4, -0.1), A(1.6, 2.4, -0.4)
    arms = _arm_bones(H, sh, el, wr)
    H.mbone("Hip#", "Body", (0.45, 2.3, 0.05))
    H.mbone("Knee#", "Hip#", (0.5, 1.25, -0.05))
    H.mbone("Foot#", "Knee#", (0.52, 0.3, 0.05))
    bark = dict(col="primary", mat="wood")

    def ridges(sd, amp=0.04, n=14):
        def f(p):
            a = np.arctan2(p[:, 0], p[:, 2])
            return sd(p) + amp * np.abs(np.sin(a * n * 0.5 + 0.6 * np.sin(p[:, 1] * 2.2)))
        return SDF(f)

    tr = round_cone((0, 2.4, 0.05), (0, 4.7, 0.0), 0.85, 0.72).su(capsule((-0.85, 4.4, 0.0), (0.85, 4.4, 0.0), 0.35), 0.3)
    tr = tr.su(ellipsoid(0.75, 0.4, 0.55, (0, 2.35, 0.05)), 0.2)
    tr = ridges(tr, 0.05).noise(0.02, 6, 1)
    tr = tr.ss(ellipsoid(0.2, 0.28, 0.15, (0.25, 3.2, -0.62)), 0.08)  # knot hollow
    H.piece("Trunk", "Spine", tr, tris=2400, res=128, **bark)
    hc = A(0, 5.25, -0.05)
    hd = round_cone(T(hc + A(0, -0.5, 0.05)), T(hc + A(0, 0.5, 0.0)), 0.55, 0.48)
    hd = hd.su(capsule(T(hc + A(-0.38, 0.12, -0.45)), T(hc + A(0.38, 0.12, -0.45)), 0.13), 0.1)          # heavy brow
    hd = hd.su(round_cone(T(hc + A(0, 0.05, -0.5)), T(hc + A(0, -0.2, -0.68)), 0.1, 0.12), 0.08)          # nose knot
    hd = hd.ss(sphere(0.13, T(hc + A(0.2, -0.02, -0.5))).mirror_x(), 0.04)
    hd = hd.ss(capsule(T(hc + A(-0.22, -0.38, -0.52)), T(hc + A(0.22, -0.38, -0.52)), 0.06), 0.04)
    for i in range(4):
        a = i * 1.6
        hd = hd.su(round_cone(T(hc + A(0.3 * math.cos(a), 0.4, 0.3 * math.sin(a))), T(hc + A(0.6 * math.cos(a), 1.05, 0.55 * math.sin(a))), 0.13, 0.04), 0.06)
    H.piece("HeadP", "Head", ridges(hd, 0.03, 18).noise(0.015, 8, 2), tris=2000, res=128, role="head", **bark)
    for sx, nm in ((1, "R"), (-1, "L")):
        H.prim("Eye" + nm, "Head", "Ball", (0.13, 0.13, 0.13), T(hc + A(0.2 * sx, -0.02, -0.47)), col=[1.0, 0.82, 0.3], mat="hard", glow=True, role="eye", pri=1.6)
    H.prim("MouthP", "Head", "Ellipsoid", (0.44, 0.08, 0.1), T(hc + A(0, -0.38, -0.5)), col="mouth", mat="hard", role="mouth", pri=2.0)
    beard = U(*(round_cone(T(hc + A(x, -0.45, -0.45)), T(hc + A(x * 1.3, -1.05 - 0.15 * (i % 2), -0.5)), 0.13, 0.04) for i, x in enumerate((-0.25, -0.08, 0.08, 0.25))), k=0.06)
    H.piece("MossBeard", "Head", beard.noise(0.02, 10, 3), col="secondary", mat="leaf", tris=800, role="beard", pri=1.3)
    rng = np.random.default_rng(4)

    def leaves(center, rad, n, seed):
        r_ = np.random.default_rng(seed)
        out = None
        for i in range(n):
            c = np.asarray(center) + r_.normal(size=3) * np.asarray(rad) * 0.5
            one = ellipsoid(*(np.asarray(rad) * r_.uniform(0.4, 0.6)), T(c))
            out = one if out is None else out.su(one, 0.12)
        return out.noise(0.05, 7, seed)

    can = U(leaves(T(hc + A(0, 1.45, 0.25)), (1.9, 1.1, 1.6), 11, 7), leaves(T(hc + A(1.05, 1.0, 0.35)), (1.1, 0.8, 1.0), 5, 8),
            leaves(T(hc + A(-1.05, 1.05, 0.3)), (1.1, 0.8, 1.0), 5, 9), leaves(T(hc + A(0, 1.0, 0.95)), (1.2, 0.8, 0.8), 4, 12), k=0.15)
    H.piece("Canopy", "Head", can, col="leaf", mat="leaf", tris=2200, res=120, role="leaves", pri=1.1)
    sl = U(leaves((0.95, 4.75, 0.15), (0.6, 0.35, 0.55), 4, 10), leaves((-0.95, 4.75, 0.15), (0.6, 0.35, 0.55), 4, 11), k=0.1)
    H.piece("ShoulderLeaves", "Spine", sl, col="leaf", mat="leaf", tris=1200, role="leaves", pri=1.2)
    for sx, nm in ((1, "R"), (-1, "L")):
        def m(p, sx=sx):
            return A(p[0] * sx, p[1], p[2])
        sfx = '' if sx > 0 else '_l'
        ua = tube([T(m(sh) + A(0, 0.05, 0)), T((m(sh) + m(el)) / 2 + A(0.12 * sx, 0, 0)), T(m(el))], [0.32, 0.27, 0.23], k=0.05)
        ua = ua.su(round_cone(T((m(sh) + m(el)) / 2 + A(0.15 * sx, 0.0, 0.05)), T((m(sh) + m(el)) / 2 + A(0.55 * sx, 0.45, 0.25)), 0.08, 0.02), 0.04)
        H.piece("UpperArm" + nm, "Shoulder" + nm, ridges(ua, 0.025, 10), tris=800, role="limb", key=f"h_treant_up{sfx}", **bark)
        fo = tube([T(m(el)), T((m(el) + m(wr)) / 2 + A(0.05 * sx, 0, 0.05)), T(m(wr))], [0.23, 0.2, 0.18], k=0.05)
        H.piece("Forearm" + nm, "Elbow" + nm, ridges(fo, 0.02, 10), tris=700, role="limb", key=f"h_treant_fo{sfx}", **bark)
        w = m(wr)
        hand = sphere(0.2, T(w + A(0, -0.1, 0)))
        for i, (dz, ln) in enumerate(((-0.15, 0.7), (0.0, 0.8), (0.15, 0.7), (-0.25, 0.45))):
            a = w + A(0, -0.15, dz)
            b = a + A(-0.05 * sx, -ln * 0.55, dz * 0.6 - 0.1)
            c = b + A(-0.12 * sx, -ln * 0.45, -0.12)
            hand = hand.su(tube([T(a), T(b), T(c)], [0.08, 0.06, 0.02], k=0.03), 0.05)
        H.piece("Twigs" + nm, "Hand" + nm, hand, tris=800, role="hand", key=f"h_treant_hand{sfx}", **bark)
        hp, kn, ft = A(0.45 * sx, 2.3, 0.05), A(0.5 * sx, 1.25, -0.05), A(0.52 * sx, 0.3, 0.05)
        th = round_cone(T(hp + A(0, 0.15, 0)), T(kn), 0.36, 0.3)
        H.piece("Thigh" + nm, "Hip" + nm, ridges(th, 0.025, 12), tris=700, role="limb", key=f"h_treant_th{sfx}", **bark)
        lg = round_cone(T(kn), T(ft + A(0, 0.1, 0)), 0.3, 0.34)
        for i, a in enumerate((-0.9, -0.2, 0.5, 2.6)):
            d = A(math.sin(a), 0, -math.cos(a))
            lg = lg.su(tube([T(ft + A(0, 0.15, 0)), T(ft + d * 0.35 + A(0, 0.0, 0)), T(ft + d * 0.65 + A(0, -0.1, 0))], [0.18, 0.12, 0.05], k=0.04), 0.08)
        lg = lg & plane((0, -1, 0), 0.0)
        H.piece("RootLeg" + nm, "Knee" + nm, ridges(lg, 0.02, 12), tris=1000, role="foot", key=f"h_treant_leg{sfx}", **bark)
    H.socket("mouth", T(hc + A(0, -0.38, -0.6)), "Head")
    H.socket("head", T(hc + A(0, 2.0, 0)), "Head")
    H.socket("hand", T(wr + A(0, -0.5, 0)), "HandR")
    H.rig.update({"head": "Head", "legs": [{"hip": "HipR", "knee": "KneeR", "phase": 0.0, "side": 1}, {"hip": "HipL", "knee": "KneeL", "phase": 0.5, "side": -1}]})
    mm.biped_extra(H, [("HipR", "KneeR", "FootR", 0.0), ("HipL", "KneeL", "FootL", 0.5)], list(arms), spine="Spine", head="Head",
                   stride=0.3, walk=1.5, height=6.0, attack="slam", stomp=0.8)
    return H


