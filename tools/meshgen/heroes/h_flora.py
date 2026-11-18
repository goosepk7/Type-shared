"""Flora and sky spirits: plant folk (mushroom king, mushroom sprite, cactus walker), carved pumpkins (jack o lantern,
pumpkin head) and weather / sky spirits (cloud spirit, smoke wraith, star spirit, sun spirit) plus two cosmic
quadrupeds (comet beast, moon beast).

Bodies are sculpted solids with readable silhouettes: a domed toadstool cap with raised warts and a gill skirt, a
ribbed saguaro with spine tufts, a lobed pumpkin shell carved through to a glowing core, cumulus puffs, twisted smoke
ropes, a bevelled five-point star, a sun disc ringed by flame rays, an ice-crystal beast with a flaming tail.
Only cores / eyes glow. Mapping rules for the gap words are the MAP list at the bottom.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF
from kit import Hero, hero, spots, gradient, combine
import motion_flora as mf
import motion_monsters as mm
from map import NOTFOOD

PLANT = {"cat": ["Creature", "Plant", "Object", "Element", "Abstract"],
         "bp": ["Plant", "Humanoid", "Blob", "Orb", "Biped", "Quadruped", "Ghost", "Cloud", "Swarm"]}
SKY = {"cat": ["Creature", "Element", "Weather", "Abstract", "Object", "Plant"],
       "bp": ["Cloud", "Orb", "Blob", "Ghost", "Humanoid", "Swarm", "Wave"]}
BEAST = {"cat": ["Creature", "Element", "Abstract"], "bp": ["Quadruped", "Dragon", "Giant", "Blob"]}
WALKER = {"cat": ["Creature", "Person", "Plant", "Object"], "bp": ["Humanoid", "Biped", "Giant", "Plant", "Ghost"]}


def T(a):
    return tuple(float(x) for x in a)


def A(*x):
    return np.array(x, float)


def U(*shapes, k=0.0):
    out = None
    for s_ in shapes:
        if s_ is None:
            continue
        out = s_ if out is None else (out.su(s_, k) if k > 0 else out | s_)
    return out


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


def plate(poly, o, u, v, t):
    """Flat polygon slab (poly in the (u, v) plane at o, half-thickness t)."""
    o = np.asarray(o, float)
    u = np.asarray(u, float)
    u = u / np.linalg.norm(u)
    v = np.asarray(v, float)
    v = v - (v @ u) * u
    v = v / np.linalg.norm(v)
    n = np.cross(u, v)
    pv = np.asarray(poly, float)

    def f(p):
        q = p - o
        d2 = poly2d(np.column_stack([q @ u, q @ v]), pv)
        dz = np.abs(q @ n) - t
        return np.minimum(np.maximum(d2, dz), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(dz, 0) ** 2)

    return SDF(f)


def flame(base, up, length, r, side=(1, 0, 0), curl=0.25, n=6):
    """Stylised flame tongue: S-curved tapered tube from base along `up`."""
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
    """Faceted prism from a to b with a pyramidal point at b."""
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
        d = -h
        for n in ns:
            rad = q @ n
            d = np.maximum(d, rad - r)
            d = np.maximum(d, (rad * tl + (h - L) * r) / math.hypot(tl, r))
        return d

    return SDF(f)


def ragged_cut(y0, amp, n, phase=0.0, center=(0, 0), jag=True, seed=0):
    """Half-space y >= y0 + amp * wave(angle) around the vertical axis through center (x, z)."""
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6.28, 3)

    def f(p):
        a = np.arctan2(p[:, 0] - center[0], p[:, 2] - center[1])
        if jag:
            w = 2 * np.abs(((a * n / math.tau + phase) % 1.0) - 0.5)
        else:
            w = 0.5 + 0.5 * np.cos(a * n + phase)
        w = w + 0.25 * np.sin(a * 3 + ph[0]) + 0.15 * np.sin(a * 5 + ph[1])
        return (y0 + amp * w) - p[:, 1]

    return SDF(f)


def cute_eyes(H, bone, pos, r, look=(0.1, 0, -1), tall=1.15):
    d = np.array(look, float)
    d /= np.linalg.norm(d)
    x, y, z = pos
    H.mprim("Eye#", bone, "Ball", (r * 2, r * 2 * tall, r * 2), (x, y, z), col="pupil", mat="hard", role="eye", pri=1.3)
    H.mprim("Shine#", bone, "Ball", (r * 0.7,) * 3, (x + r * 0.3, y + r * 0.55, z + d[2] * r * 0.85), col="shine", mat="hard", role="shine", pri=2.5)
    H.mprim("Shine2#", bone, "Ball", (r * 0.32,) * 3, (x - r * 0.3, y - r * 0.4, z + d[2] * r * 0.9), col="shine", mat="hard", role="shine", pri=2.6)


def glow_eyes(H, bone, pos, size, col, rot=(0, 0, 0), shape="Ellipsoid"):
    x, y, z = pos
    for sx, nm in ((1, "R"), (-1, "L")):
        H.prim("Eye" + nm, bone, shape, size, (x * sx, y, z), rot=(rot[0], rot[1] * sx, rot[2] * sx), col=col, mat="hard", glow=True, role="eye", pri=1.6)


def arm_bones(H, sh, el, wr, parent="Spine"):
    H.mbone("Shoulder#", parent, T(sh))
    H.mbone("Elbow#", "Shoulder#", T(el))
    H.mbone("Hand#", "Elbow#", T(wr))
    return [("ShoulderR", "ElbowR", "HandR", 1), ("ShoulderL", "ElbowL", "HandL", -1)]


def leg_bones(H, hip, knee, foot, parent="Body"):
    H.mbone("Hip#", parent, T(hip))
    H.mbone("Knee#", "Hip#", T(knee))
    H.mbone("Foot#", "Knee#", T(foot))
    return [("HipR", "KneeR", "FootR", 0.0), ("HipL", "KneeL", "FootL", 0.5)]


def sides():
    """(sign, name suffix, key suffix) for the right then left copy of a hand-built pair."""
    return ((1, "R", ""), (-1, "L", "_l"))


def mx(p, sx):
    return A(p[0] * sx, p[1], p[2])


def warts(surface, pts, rad, lift=0.045, seed=0):
    """Raised flat-topped patches (toadstool warts) on `surface`: spheres sunk into it, clipped to a thin skin
    `lift` above it, so they read as separate scabs instead of balls."""
    rng = np.random.default_rng(seed)
    sk = surface.round(lift)
    out = None
    for c in pts:
        r = rad * rng.uniform(0.75, 1.25)
        out = U(out, sphere(r, T(c)))
    return (out & sk).round(0.006)


def project(surface, pts, iters=6):
    """Slide points onto the zero level of `surface` along its numeric gradient."""
    P = np.array(pts, float).reshape(-1, 3)
    e = 1e-3
    for _ in range(iters):
        d = surface(P)
        g = np.stack([(surface(P + A(*v) * e) - d) / e for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))], 1)
        g /= np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-6)
        P = P - g * d[:, None]
    return list(P)


def on_dome(c, rx, ry, rz, n, lat=(0.3, 1.25), seed=0, avoid=None):
    """n points scattered over the upper part of an ellipsoid (c, radii), polar angle within `lat`."""
    rng = np.random.default_rng(seed)
    pts = []
    tries = 0
    while len(pts) < n and tries < 2000:
        tries += 1
        th = rng.uniform(*lat)
        ph = rng.uniform(0, math.tau)
        p = A(c[0] + rx * math.sin(th) * math.sin(ph), c[1] + ry * math.cos(th), c[2] + rz * math.sin(th) * math.cos(ph))
        if avoid is not None and avoid(p):
            continue
        if all(np.linalg.norm(p - q) > 0.42 * (rx + rz) / 2.6 for q in pts):
            pts.append(p)
    return pts


# ================================================================================================ mushrooms
@hero("mushroom king", "flora")
def mushroom_king():
    """A pot-bellied toadstool monarch: a broad red cap studded with raised white warts and a gill skirt beneath, a
    frilled annulus ruff for a royal collar, a gold crown worn askew on the cap, a curling moustache on a friendly
    stem face, stubby arms with a little mushroom-topped sceptre and two stumpy feet. Waddles; the cap lags and
    jiggles; attacks with a cap head-butt."""
    H = Hero("mushroom king", plan="Biped", gait="waddle", tags=["plant", "mushroom"])
    H.preview = {"primary": "#DC2626", "secondary": "#FACC15"}
    H.body((0, 0.95, 0))
    H.bone("Spine", "Body", (0, 1.25, 0))
    H.bone("Cap", "Spine", (0, 2.45, 0))
    legs = leg_bones(H, A(0.36, 0.85, 0.0), A(0.4, 0.48, -0.02), A(0.42, 0.16, -0.06))
    arms = arm_bones(H, A(0.62, 1.62, -0.05), A(0.88, 1.32, -0.15), A(0.95, 1.05, -0.28))
    stem = ellipsoid(0.74, 0.72, 0.7, (0, 1.32, 0.02)).su(round_cone((0, 1.6, 0.0), (0, 2.4, 0.02), 0.58, 0.46), 0.3)
    stem = stem.ss(ellipsoid(0.1, 0.13, 0.08, (0.21, 1.86, -0.6)).mirror_x(), 0.05)   # eye sockets
    stem = stem.su(ellipsoid(0.16, 0.1, 0.1, (0.0, 1.66, -0.6)), 0.07)                 # button nose
    stem = stem.noise(0.012, 7, 3)
    H.piece("Stem", "Spine", stem, col="cream", mat="skin", tris=1200, res=128, role="body",
            pattern=gradient(1, 0.6, 2.3, 0.86, 1.0))
    cute_eyes(H, "Spine", (0.21, 1.87, -0.55), 0.085)
    H.mprim("Blush#", "Spine", "Ellipsoid", (0.16, 0.08, 0.06), (0.38, 1.7, -0.5), rot=(0, 0.6, 0), col="blush", mat="hard", role="mouth", pri=2.4, tr=0.3)
    H.prim("Mouth", "Spine", "Ellipsoid", (0.2, 0.09, 0.08), (0, 1.47, -0.66), col="mouth", mat="hard", role="mouth", pri=2.0)
    mo = None
    for sx in (1, -1):
        mo = U(mo, tube([(0.02 * sx, 1.6, -0.66), (0.18 * sx, 1.56, -0.66), (0.33 * sx, 1.6, -0.6), (0.42 * sx, 1.71, -0.52), (0.38 * sx, 1.78, -0.5)],
                        [0.06, 0.075, 0.06, 0.035, 0.02], k=0.03), k=0.03)
    H.piece("Moustache", "Spine", mo, col="white", mat="cloth", tris=400, role="hair", pri=1.6)
    # annulus ruff: a frilled skirt hanging off the top of the stem
    ruff = round_cone((0, 2.36, 0.0), (0, 2.02, 0.0), 0.52, 0.86)
    ruff = ruff - round_cone((0, 2.42, 0.0), (0, 1.96, 0.0), 0.47, 0.8)
    def frill(p, r=ruff):
        a = np.arctan2(p[:, 0], p[:, 2])
        return r(p) - 0.03 * np.cos(a * 16) * np.clip((2.3 - p[:, 1]) / 0.3, 0, 1)
    ruff = SDF(frill) & ragged_cut(2.0, 0.07, 16, jag=False, seed=4)
    H.piece("Ruff", "Spine", ruff, col="belly", mat="cloth", tris=700, res=128, role="cloth", pri=1.3)
    # cap: dome with a rounded rim and a hollow underside filled by a gill disc
    cc = (0, 2.42, 0.0)
    dome = ellipsoid(1.5, 1.02, 1.45, cc).si(plane((0, -1, 0), -2.5), 0.14)
    dome = dome.ss(ellipsoid(1.22, 0.3, 1.18, (0, 2.42, 0)), 0.08)
    dome = dome.noise(0.012, 4, 8)
    H.piece("CapP", "Cap", dome, col="primary", mat="skin", tris=1200, res=128, role="head",
            pattern=gradient(1, 2.55, 3.4, 0.82, 1.0))
    gil = ellipsoid(1.19, 0.27, 1.15, (0, 2.42, 0)) & plane((0, -1, 0), -2.52)
    def gills(p, g=gil):
        a = np.arctan2(p[:, 0], p[:, 2])
        return g(p) + 0.025 * np.abs(np.sin(a * 22))
    H.piece("Gills", "Cap", SDF(gills) - capsule((0, 2.0, 0), (0, 2.9, 0), 0.4), col="belly", mat="skin", tris=600, res=120, role="detail", pri=1.4)
    crown_at = A(0.18, 3.3, 0.05)
    pts = on_dome(cc, 1.5, 1.02, 1.45, 13, lat=(0.45, 1.3), seed=5, avoid=lambda p: np.linalg.norm((p - crown_at)[[0, 2]]) < 0.62)
    H.piece("Warts", "Cap", warts(dome, pts, 0.21, lift=0.05, seed=6), col="white", mat="skin", tris=700, res=128, role="detail", pri=1.5)
    # crown worn askew
    band = (cylinder(0.46, 0.13, rr=0.02) - cylinder(0.41, 0.3)).at(0, 0.12, 0)
    for i in range(5):
        a = i / 5 * math.tau
        tip = A(0.44 * math.sin(a), 0.62, 0.44 * math.cos(a))
        band = band | U(round_cone(T(tip * A(1, 0, 1) + A(0, 0.2, 0)), T(tip), 0.1, 0.025), sphere(0.055, T(tip + A(0, 0.04, 0))))
    band = band - cylinder(0.395, 0.9)
    crown = band.rot(0.0, 0.0, -0.18).at(*T(crown_at))
    H.piece("Crown", "Cap", crown, col="gold", mat="metal", tris=600, res=112, role="horn", pri=1.2)
    for i, a in enumerate((-0.45, 0.0, 0.45)):
        H.prim(f"Gem{i}", "Cap", "Ball", (0.1, 0.1, 0.06), T(crown_at + A(0.46 * math.sin(a) - 0.03, 0.12 + 0.46 * math.sin(a) * 0.18 * -1, -0.46 * math.cos(a))),
               col="gem", mat="glass", role="detail", pri=2.2, glow=True)
    for sx, nm, sfx in sides():
        sh, el, wr = mx(A(0.62, 1.62, -0.05), sx), mx(A(0.88, 1.32, -0.15), sx), mx(A(0.95, 1.05, -0.28), sx)
        H.piece("Arm" + nm, "Shoulder" + nm, tube([T(sh - A(0.12 * sx, 0, 0)), T(el), T(wr)], [0.15, 0.12, 0.11], k=0.04), col="cream", mat="skin", tris=350,
                role="limb", key=f"h_mking_arm{sfx}")
        mit = ellipsoid(0.15, 0.14, 0.13, T(wr + A(0, -0.08, -0.02))).su(ellipsoid(0.06, 0.08, 0.06, T(wr + A(-0.1 * sx, -0.02, -0.1))), 0.04)
        H.piece("Hand" + nm, "Hand" + nm, mit, col="cream", mat="skin", tris=300, role="hand", key=f"h_mking_hand{sfx}")
        hp, kn, ft = mx(A(0.36, 0.85, 0.0), sx), mx(A(0.4, 0.48, -0.02), sx), mx(A(0.42, 0.16, -0.06), sx)
        H.piece("Thigh" + nm, "Hip" + nm, round_cone(T(hp), T(kn), 0.2, 0.16), col="cream", mat="skin", tris=300, role="limb", key=f"h_mking_th{sfx}")
        foot = ellipsoid(0.24, 0.17, 0.32, T(ft + A(0, 0.0, -0.08))).su(round_cone(T(kn), T(ft), 0.16, 0.18), 0.06) & plane((0, -1, 0), 0.0)
        H.piece("Foot" + nm, "Knee" + nm, foot, col="belly", mat="skin", tris=300, role="foot", key=f"h_mking_foot{sfx}")
    # sceptre: a little toadstool on a wooden rod in the right hand
    w = A(0.95, 1.0, -0.32)
    rod = capsule(T(w + A(0, -0.55, 0)), T(w + A(0, 0.95, 0)), 0.045)
    H.piece("Sceptre", "HandR", rod.su(sphere(0.08, T(w + A(0, -0.55, 0))), 0.03), col="wood", mat="wood", tris=250, role="weapon", pri=1.6)
    top = (ellipsoid(0.24, 0.17, 0.24, T(w + A(0, 1.0, 0))) & plane((0, -1, 0), -(w[1] + 0.98))).su(sphere(0.06, T(w + A(0, 0.98, 0))), 0.02)
    H.piece("SceptreCap", "HandR", top, col="primary", mat="skin", tris=300, role="weapon", pri=1.7)
    H.socket("mouth", (0, 1.47, -0.7), "Spine")
    H.socket("head", (0, 4.0, 0), "Cap")
    H.socket("hand", T(w + A(0, 1.1, 0)), "HandR")
    H.rig.update({"head": "Cap"})
    mf.waddle(H, legs, arms, spine="Spine", head=None, cap="Cap", height=3.9, walk=0.62, stride=0.4, roll=0.13,
              attack="butt", weapon_arm="ShoulderR")
    return H


@hero("mushroom sprite", "flora")
def mushroom_sprite():
    """A tiny hopping toadstool: a tall bell-shaped liberty cap whose tip flops over, polka warts, a chubby stem with
    huge eyes and an open grin, two nubby feet and leaf-sprout arms. Springs along; the cap squashes on landing."""
    H = Hero("mushroom sprite", plan="Blob", gait="hop", tags=["plant", "mushroom"])
    H.preview = {"primary": "#DC2626", "secondary": "#F8FAFC"}
    H.body((0, 0.55, 0))
    H.bone("Top", "Body", (0, 0.75, 0))
    H.bone("Cap", "Top", (0, 1.2, 0))
    H.bone("FootR", "Body", (0.24, 0.2, -0.05))
    H.bone("FootL", "Body", (-0.24, 0.2, -0.05))
    H.bone("SproutR", "Top", (0.45, 0.85, 0))
    H.bone("SproutL", "Top", (-0.45, 0.85, 0))
    st = ellipsoid(0.46, 0.5, 0.44, (0, 0.72, 0)).su(round_cone((0, 0.8, 0), (0, 1.25, 0), 0.36, 0.3), 0.2)
    st = st.ss(ellipsoid(0.15, 0.18, 0.1, (0.17, 0.9, -0.44)).mirror_x(), 0.04)
    st = st.ss(ellipsoid(0.14, 0.09, 0.12, (0.0, 0.62, -0.47)), 0.04)  # open grin
    H.piece("Stem", "Top", st, col="cream", mat="skin", tris=1100, res=112, role="body", pattern=gradient(1, 0.2, 1.2, 0.85, 1.0))
    cute_eyes(H, "Top", (0.17, 0.91, -0.4), 0.11, tall=1.3)
    H.prim("Mouth", "Top", "Ellipsoid", (0.24, 0.13, 0.08), (0, 0.62, -0.43), col="mouth", mat="hard", role="mouth", pri=2.0)
    H.prim("Tongue", "Top", "Ellipsoid", (0.12, 0.05, 0.06), (0, 0.58, -0.46), col="tongue", mat="hard", role="mouth", pri=2.2)
    H.mprim("Blush#", "Top", "Ellipsoid", (0.12, 0.06, 0.05), (0.3, 0.74, -0.38), rot=(0, 0.6, 0), col="blush", mat="hard", role="mouth", pri=2.4, tr=0.3)
    # liberty cap: wide bell, flopped tip
    bell = round_cone((0, 1.32, 0.02), (0, 1.95, 0.12), 0.78, 0.26).si(plane((0, -1, 0), -1.15), 0.08)
    bell = bell.su(tube([(0, 1.95, 0.12), (0, 2.2, 0.3), (0, 2.18, 0.55), (0, 2.02, 0.68)], [0.25, 0.17, 0.1, 0.05], k=0.08), 0.12)
    bell = bell.ss(ellipsoid(0.62, 0.2, 0.62, (0, 1.15, 0.02)), 0.06)
    H.piece("CapP", "Cap", bell.noise(0.01, 5, 2), col="primary", mat="skin", tris=1300, res=120, role="head",
            pattern=gradient(1, 1.2, 2.1, 0.82, 1.0))
    pts = [A(0.55 * math.sin(a), 1.42 + 0.1 * (i % 2), 0.55 * math.cos(a) + 0.03) for i, a in enumerate(np.linspace(0, math.tau, 7, endpoint=False) + 0.3)]
    pts += [A(0.32, 1.78, -0.05), A(-0.28, 1.72, 0.25), A(0.05, 1.86, -0.18)]
    H.piece("Warts", "Cap", warts(bell, project(bell, pts), 0.15, lift=0.04, seed=3), col="secondary", mat="skin", tris=700, res=112, role="detail", pri=1.5)
    for sx, nm, sfx in sides():
        ft = A(0.24 * sx, 0.1, -0.08)
        H.piece("Foot" + nm, "Foot" + nm, (ellipsoid(0.17, 0.12, 0.22, T(ft)) & plane((0, -1, 0), 0.0)), col="belly", mat="skin", tris=250, role="foot",
                key=f"h_msprite_foot{sfx}")
        b = A(0.45 * sx, 0.85, 0)
        sp = tube([T(b - A(0.08 * sx, 0, 0)), T(b + A(0.12 * sx, 0.12, -0.02)), T(b + A(0.2 * sx, 0.3, -0.04))], [0.05, 0.04, 0.025], k=0.02)
        leaf = ellipsoid(0.16, 0.035, 0.08, (0, 0, 0)).rot(0, 0, 0.7 * sx).at(*T(b + A(0.3 * sx, 0.4, -0.04)))
        H.piece("Sprout" + nm, "Sprout" + nm, sp.su(leaf, 0.03), col="leaf", mat="leaf", tris=300, role="limb", key=f"h_msprite_sprout{sfx}")
    H.socket("mouth", (0, 0.62, -0.5), "Top")
    H.socket("head", (0, 2.3, 0), "Cap")
    H.rig.update({"head": "Top"})
    mf.hopper(H, top="Top", lid="Cap", tendrils=["SproutR", "SproutL", "FootR", "FootL"], height=2.3, period=0.62)
    return H


# ================================================================================================ cactus
def saguaro(a, b, r, ribs=10, depth=0.06):
    """Ribbed column from a to b (radius r, domed ends)."""
    base = capsule(T(a), T(b), r)
    a_, b_ = np.asarray(a, float), np.asarray(b, float)
    ax = (b_ - a_) / np.linalg.norm(b_ - a_)
    t0 = np.cross(ax, (0, 0, 1) if abs(ax[2]) < 0.9 else (1, 0, 0))
    t0 /= np.linalg.norm(t0)
    t1 = np.cross(ax, t0)

    def f(p):
        q = p - a_
        ang = np.arctan2(q @ t0, q @ t1)
        return base(p) + depth * (0.5 - 0.5 * np.cos(ang * ribs)) ** 1.5

    return SDF(f)


def spine_tufts(segs, ribs, n_along, r, seed=0, length=0.12, skip=None):
    """Little cones of spines sprouting on the rib crests of capsule segments [(a, b, r)]."""
    rng = np.random.default_rng(seed)
    out = None
    for a, b, rad in segs:
        a, b = np.asarray(a, float), np.asarray(b, float)
        ax = (b - a) / np.linalg.norm(b - a)
        t0 = np.cross(ax, (0, 0, 1) if abs(ax[2]) < 0.9 else (1, 0, 0))
        t0 /= np.linalg.norm(t0)
        t1 = np.cross(ax, t0)
        for i in range(n_along):
            h = (i + 0.5) / n_along
            for k in range(ribs):
                if (i + k) % 2:
                    continue
                ang = (k / ribs) * math.tau + rng.uniform(-0.05, 0.05)
                d = math.sin(ang) * t0 + math.cos(ang) * t1
                c = a + (b - a) * h + d * rad
                if skip is not None and skip(c):
                    continue
                tip = c + d * length + ax * length * 0.4
                out = U(out, round_cone(T(c - d * 0.02), T(tip), r, 0.004))
    return out


@hero("cactus creature", "flora")
def cactus_creature():
    """A saguaro that walks: a ribbed column body with two upturned arms, spine tufts on every rib, a carved face
    with a big toothy grin, a blooming flower worn as a hat and two stumpy root feet. Waddles with arms swinging
    and the flower bobbing; head-butts with a prickly lunge."""
    H = Hero("cactus creature", plan="Biped", gait="waddle", tags=["plant", "cactus"])
    H.preview = {"primary": "#15803D", "secondary": "#F472B6"}
    H.body((0, 0.9, 0))
    H.bone("Spine", "Body", (0, 1.2, 0))
    H.bone("Hat", "Spine", (0, 3.0, 0))
    legs = leg_bones(H, A(0.3, 0.8, 0.0), A(0.33, 0.45, -0.02), A(0.35, 0.14, -0.05))
    sh, el, wr = A(0.55, 1.75, 0.0), A(1.05, 1.82, 0.0), A(1.1, 2.4, 0.0)
    arms = arm_bones(H, sh, el, wr)
    body_a, body_b, R = A(0, 0.75, 0.02), A(0, 2.7, 0.02), 0.56
    bd = saguaro(body_a, body_b, R, ribs=12, depth=0.07)
    bd = bd.ss(ellipsoid(0.11, 0.13, 0.12, (0.2, 2.3, -0.54)).mirror_x(), 0.04)
    bd = bd.ss(ellipsoid(0.3, 0.13, 0.15, (0, 1.95, -0.55)), 0.05)
    H.piece("BodyP", "Spine", bd, col="primary", mat="skin", tris=1700, res=128, role="body", pattern=gradient(1, 0.7, 2.8, 0.8, 1.05))
    cute_eyes(H, "Spine", (0.2, 2.3, -0.48), 0.08)
    H.prim("Mouth", "Spine", "Ellipsoid", (0.5, 0.2, 0.14), (0, 1.95, -0.47), col="mouth", mat="hard", role="mouth", pri=2.0)
    H.prim("Teeth", "Spine", "Block", (0.36, 0.06, 0.06), (0, 2.02, -0.55), col="tooth", mat="hard", role="mouth", pri=2.2)
    H.mprim("Blush#", "Spine", "Ellipsoid", (0.14, 0.07, 0.05), (0.36, 2.12, -0.45), rot=(0, 0.6, 0), col="blush", mat="hard", role="mouth", pri=2.4, tr=0.3)
    face = lambda c: c[2] < -0.2 and 1.75 < c[1] < 2.55 and abs(c[0]) < 0.45
    tufts = spine_tufts([(body_a + A(0, 0.15, 0), body_b, R)], 12, 7, 0.03, seed=1, skip=face)
    H.piece("Spines", "Spine", tufts, col="cream", mat="hard", tris=1100, res=128, role="detail", pri=1.8, ao=False)
    # flower hat: five petals and a centre on the crown
    top = A(0, 3.18, 0.02)
    pet = None
    for i in range(6):
        a = i / 6 * math.tau
        d = A(math.sin(a), 0, math.cos(a))
        pet = U(pet, ellipsoid(0.26, 0.07, 0.15, (0, 0, 0)).rot(0, -a + math.pi / 2, 0).rot(0, 0, 0).at(*T(top + d * 0.26 + A(0, 0.06, 0))), k=0.04)
        pet = U(pet, ellipsoid(0.2, 0.06, 0.12, (0, 0, 0)).rot(0, -a + math.pi / 2 + 0.5, 0).at(*T(top + A(math.sin(a + 0.5), 0, math.cos(a + 0.5)) * 0.18 + A(0, 0.16, 0))), k=0.04)
    H.piece("Flower", "Hat", pet, col="secondary", mat="cloth", tris=1000, res=112, role="hair", pri=1.3)
    H.prim("FlowerHeart", "Hat", "Ball", (0.22, 0.14, 0.22), T(top + A(0, 0.2, 0)), col="gold", mat="hard", role="detail", pri=1.6)
    for sx, nm, sfx in sides():
        s, e, w = mx(sh, sx), mx(el, sx), mx(wr, sx)
        up = saguaro(s - A(0.1 * sx, 0, 0), e, 0.2, ribs=8, depth=0.03)
        H.piece("ArmLow" + nm, "Shoulder" + nm, up, col="primary", mat="skin", tris=500, role="limb", key=f"h_cactus_arml{sfx}")
        fo = saguaro(e, w, 0.19, ribs=8, depth=0.03)
        fo = fo | spine_tufts([(e + A(0, 0.1, 0), w, 0.19)], 8, 3, 0.022, seed=2 if sx > 0 else 3, length=0.09)
        H.piece("ArmUp" + nm, "Elbow" + nm, fo, col="primary", mat="skin", tris=600, role="limb", key=f"h_cactus_armu{sfx}")
        hp, kn, ft = mx(A(0.3, 0.8, 0.0), sx), mx(A(0.33, 0.45, -0.02), sx), mx(A(0.35, 0.14, -0.05), sx)
        foot = ellipsoid(0.22, 0.17, 0.3, T(ft + A(0, 0.0, -0.06))).su(round_cone(T(hp), T(ft), 0.2, 0.17), 0.08)
        for j, (dx, dz) in enumerate(((-0.12, -0.32), (0.0, -0.36), (0.12, -0.3))):
            foot = foot.su(sphere(0.07, T(ft + A(dx, -0.07, dz))), 0.04)
        foot = foot & plane((0, -1, 0), 0.0)
        H.piece("Foot" + nm, "Knee" + nm, foot, col="dark", mat="skin", tris=500, role="foot", key=f"h_cactus_foot{sfx}")
    H.socket("mouth", (0, 1.95, -0.6), "Spine")
    H.socket("head", (0, 3.5, 0), "Hat")
    H.socket("hand", T(wr + A(0, 0.3, 0)), "HandR")
    H.rig.update({"head": "Spine"})
    mf.waddle(H, legs, arms, spine="Spine", head=None, cap="Hat", height=3.4, walk=0.66, stride=0.38, roll=0.1, attack="butt")
    return H


# ================================================================================================ pumpkins
def pumpkin(c, rx, ry, rz, lobes=8, depth=0.07):
    """Lobed pumpkin: squat ellipsoid with grooves between lobes and dimpled poles."""
    c = np.asarray(c, float)
    e = ellipsoid(rx, ry, rz, T(c))

    def f(p):
        q = p - c
        a = np.arctan2(q[:, 0], q[:, 2])
        rr = np.sqrt(q[:, 0] ** 2 + q[:, 2] ** 2) / rx
        w = np.abs(np.cos(a * lobes / 2))
        return e(p) + depth * (1 - w) ** 2.2 * np.clip(rr * 1.2, 0, 1)

    s = SDF(f)
    s = s.ss(sphere(rx * 0.25, T(c + A(0, ry * 1.05, 0))), rx * 0.12)
    s = s.ss(sphere(rx * 0.2, T(c + A(0, -ry * 1.05, 0))), rx * 0.1)
    return s


def carved_face(c, R, s=1.0, z=None, grin="jagged"):
    """Cutters for triangle eyes, a nose and a toothy grin, pushed through the front (-Z) of a pumpkin at c."""
    c = np.asarray(c, float)
    o = c + A(0, 0, -R)
    cut = None
    eye = [(0.12, 0.06), (0.4, 0.08), (0.27, 0.3)]
    for sx in (1, -1):
        cut = U(cut, plate([(sx * x * s, y * s) for x, y in eye], T(o), (1, 0, 0), (0, 1, 0), 0.6 * R))
    cut = U(cut, plate([(-0.06 * s, -0.04 * s), (0.06 * s, -0.04 * s), (0, 0.08 * s)], T(o), (1, 0, 0), (0, 1, 0), 0.6 * R))
    mouth = [(-0.42, -0.12), (-0.28, -0.2), (-0.22, -0.13), (-0.14, -0.22), (-0.04, -0.15), (0.04, -0.24), (0.14, -0.16), (0.22, -0.24),
             (0.3, -0.17), (0.43, -0.11), (0.36, -0.3), (0.2, -0.42), (0.12, -0.33), (0.02, -0.44), (-0.08, -0.34), (-0.18, -0.43), (-0.3, -0.33)]
    mouth = [(x * s, y * s) for x, y in mouth][::-1]
    cut = U(cut, plate(mouth, T(o), (1, 0, 0), (0, 1, 0), 0.6 * R))
    return cut


@hero("jack o lantern", "flora")
def jack_o_lantern():
    """A carved pumpkin come alive: a deep-lobed shell carved through to a glowing core (triangle eyes, a nose and a
    jagged toothy grin), a zig-zag cut lid with a curly stem that pops up as it bounces, two curling vine tendrils
    and a leaf. Hops; the lid flips open on the attack."""
    H = Hero("jack o lantern", plan="Blob", gait="hop", tags=["plant", "pumpkin"])
    H.preview = {"primary": "#E67E22", "secondary": "#FFB020"}
    H.body((0, 0.7, 0))
    H.bone("Top", "Body", (0, 0.9, 0))
    H.bone("Lid", "Top", (0, 1.55, 0))
    H.bone("VineR", "Top", (0.45, 1.5, 0.2))
    H.bone("VineL", "Lid", (-0.2, 1.75, 0.1))
    c, rx, ry, rz = A(0, 0.95, 0), 1.0, 0.82, 0.95
    pk = pumpkin(c, rx, ry, rz, lobes=10, depth=0.09)
    inner = SDF(lambda p, pk=pk: pk(p) + 0.1)
    def lid_plug(p):
        a = np.arctan2(p[:, 0], p[:, 2])
        r = 0.44 + 0.07 * (2 * np.abs(((a * 7 / math.tau) % 1.0) - 0.5))
        return np.maximum(np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2) - r, 1.35 - p[:, 1])
    lid_cut = SDF(lid_plug)
    shell = (pk - inner) - carved_face(c + A(0, -0.04, 0), rz, s=1.5) - lid_cut.round(0.02)
    H.piece("Shell", "Top", shell, col="primary", mat="skin", tris=2400, res=144, role="body",
            pattern=combine(gradient(1, 0.15, 1.6, 0.78, 1.0)))
    lid = (pk - inner) & lid_cut
    stem = tube([(0, 1.62, 0.02), (0.02, 1.92, 0.04), (0.12, 2.08, 0.1), (0.22, 2.06, 0.18)], [0.12, 0.1, 0.085, 0.07], k=0.04).noise(0.012, 9, 4)
    H.piece("LidP", "Lid", lid, col="primary", mat="skin", tris=900, res=128, role="head", pattern=gradient(1, 1.5, 1.8, 0.85, 1.0))
    H.piece("Stem", "Lid", stem.su(cylinder(0.16, 0.05).at(0, 1.66, 0.02), 0.04), col="darkWood", mat="wood", tris=400, role="horn", pri=1.4)
    H.prim("Core", "Top", "Ball", (1.55, 1.2, 1.45), T(c + A(0, -0.02, 0)), col="secondary", mat="hard", glow=True, role="core", pri=1.1)
    vr = tube([(0.4, 1.55, 0.25), (0.75, 1.75, 0.35), (0.95, 1.6, 0.4), (0.92, 1.42, 0.3), (0.8, 1.45, 0.25)], [0.045, 0.04, 0.032, 0.025, 0.018], k=0.02)
    H.piece("TendrilR", "VineR", vr, col="leaf", mat="leaf", tris=350, role="tail", pri=1.6)
    vl = tube([(-0.15, 1.8, 0.08), (-0.45, 2.05, 0.15), (-0.7, 1.95, 0.2), (-0.72, 1.78, 0.12), (-0.6, 1.8, 0.08)], [0.04, 0.035, 0.028, 0.022, 0.016], k=0.02)
    leaf = ellipsoid(0.34, 0.035, 0.2, (0, 0, 0)).rot(0, 0.4, 0.35).at(-0.35, 1.9, 0.35)
    def veined(p, l=leaf):
        return l(p) + 0.015 * np.abs(np.sin((p[:, 0] + 0.35) * 22))
    H.piece("TendrilL", "VineL", vl.su(SDF(veined), 0.03), col="leaf", mat="leaf", tris=500, role="tail", pri=1.6)
    H.socket("mouth", T(c + A(0, -0.3, -1.0)), "Top")
    H.socket("head", (0, 2.2, 0), "Lid")
    H.rig.update({"head": "Top"})
    mf.hopper(H, top="Top", lid="Lid", tendrils=["VineR", "VineL"], height=2.2, period=0.72, spin=0.25)
    return H


def bony_hand(w, s=1.0, out=(1, 0, 0), down=(0, -1, 0), fwd=(0, 0, -1), length=1.0, r=1.0):
    """Long twiggy fingers from the wrist w, hanging along `down`, spread along `fwd`."""
    w, out, down, fwd = (np.asarray(x, float) for x in (w, out, down, fwd))
    h = ellipsoid(0.06 * s * r, 0.11 * s, 0.1 * s, T(w + down * 0.1 * s))
    for i, dz in enumerate((-0.075, -0.025, 0.025, 0.075)):
        ln = (0.3, 0.34, 0.32, 0.26)[i] * length
        a = w + down * 0.18 * s + fwd * dz * s * 1.3
        b = a + down * ln * 0.55 * s - out * 0.04 * s + fwd * dz * 0.3 * s
        c = b + down * ln * 0.45 * s - out * 0.12 * s
        h = h | tube([T(a), T(b), T(c)], [0.03 * s * r, 0.025 * s * r, 0.012 * s], k=0.01)
    h = h | tube([T(w + down * 0.08 * s + fwd * 0.08 * s), T(w + down * 0.2 * s + fwd * 0.17 * s - out * 0.05 * s), T(w + down * 0.3 * s + fwd * 0.2 * s - out * 0.12 * s)],
                 [0.032 * s * r, 0.026 * s * r, 0.012 * s], k=0.01)
    return h


def straw(c, axis, n, r, length, seed=0):
    """A tuft of straw sticking out around point c along `axis`."""
    rng = np.random.default_rng(seed)
    c, axis = np.asarray(c, float), np.asarray(axis, float)
    axis = axis / np.linalg.norm(axis)
    t0 = np.cross(axis, (0, 0, 1) if abs(axis[2]) < 0.9 else (1, 0, 0))
    t0 /= np.linalg.norm(t0)
    t1 = np.cross(axis, t0)
    out = None
    for i in range(n):
        a = i / n * math.tau + rng.uniform(-0.2, 0.2)
        rad = math.cos(a) * t0 + math.sin(a) * t1
        b = c + rad * r
        tip = b + axis * length * rng.uniform(0.7, 1.2) + rad * length * 0.5
        out = U(out, round_cone(T(b), T(tip), 0.025, 0.006))
    return out


@hero("pumpkin head", "flora")
def pumpkin_head():
    """A lanky scarecrow with a carved jack-o'-lantern for a head: a glowing grin, a tattered long coat with a
    ragged hem and patches, a vine scarf, straw bursting from the cuffs and ankles, twig fingers and patched
    trousers above heavy boots. Lurches along loose-limbed; claws with a long-armed swipe."""
    H = Hero("pumpkin head", plan="Biped", gait="biped", tags=["plant", "pumpkin", "undead"])
    H.preview = {"primary": "#EA580C", "secondary": "#166534"}
    H.body((0, 2.4, 0))
    H.bone("Spine", "Body", (0, 2.75, 0))
    H.bone("Chest", "Spine", (0, 3.55, 0))
    H.bone("Head", "Chest", (0, 4.45, -0.05))
    H.bone("CoatTail", "Body", (0, 2.2, 0.15))
    legs = leg_bones(H, A(0.28, 2.35, 0.0), A(0.32, 1.28, -0.05), A(0.34, 0.2, 0.0))
    sh, el, wr = A(0.68, 4.05, 0.0), A(0.95, 3.25, -0.05), A(1.08, 2.45, -0.18)
    arms = arm_bones(H, sh, el, wr, parent="Chest")
    # pumpkin head
    hc, hr = A(0, 4.85, -0.05), 0.62
    pk = pumpkin(hc, hr, hr * 0.8, hr * 0.95, lobes=8, depth=0.06)
    inner = SDF(lambda p, pk=pk: pk(p) + 0.07)
    shell = (pk - inner) - carved_face(hc + A(0, 0.02, 0), hr * 0.95, s=0.95)
    H.piece("HeadP", "Head", shell, col="primary", mat="skin", tris=1500, res=144, role="head", pattern=gradient(1, 4.3, 5.3, 0.8, 1.0))
    H.prim("Core", "Head", "Ball", (0.98, 0.78, 0.92), T(hc), col="secondary", mat="hard", glow=True, role="core", pri=1.1)
    stem = tube([(0, 5.25, -0.05), (0.03, 5.45, -0.02), (0.12, 5.55, 0.05)], [0.08, 0.065, 0.05], k=0.03).noise(0.01, 9, 2)
    H.piece("Stem", "Head", stem, col="darkWood", mat="wood", tris=250, role="horn", pri=1.5)
    # coat: torso + flared tattered skirt
    coat = round_cone((0, 3.15, 0.02), (0, 3.95, 0.0), 0.5, 0.56).su(capsule((-0.62, 4.0, 0.02), (0.62, 4.0, 0.02), 0.2), 0.2)
    coat = coat.su(round_cone((0, 2.4, 0.04), (0, 3.2, 0.02), 0.5, 0.48), 0.1)
    coat = coat.ss(capsule((0, 3.0, -0.6), (0, 4.1, -0.62), 0.08), 0.05)   # front opening crease
    coat = coat - capsule((0, 4.1, 0), (0, 4.6, 0), 0.22)
    H.piece("Coat", "Chest", coat.noise(0.012, 7, 4), col="leather", mat="cloth", tris=1100, res=128, role="body")
    skirt = round_cone((0, 2.55, 0.04), (0, 1.45, 0.12), 0.52, 0.72) - round_cone((0, 2.6, 0.04), (0, 1.3, 0.12), 0.45, 0.65)
    skirt = skirt & ragged_cut(1.45, 0.32, 9, jag=True, seed=7)
    skirt = skirt - plate([(-0.12, 0.0), (0.12, 0.0), (0.0, -1.4)], (0, 2.45, -0.6), (1, 0, 0), (0, 1, 0), 0.4)  # front split
    def skirt_folds(p, s_=skirt):
        a = np.arctan2(p[:, 0], p[:, 2] - 0.1)
        return s_(p) + 0.025 * np.sin(a * 11) * np.clip((2.4 - p[:, 1]) / 0.8, 0, 1)
    H.piece("CoatSkirt", "CoatTail", SDF(skirt_folds), col="leather", mat="cloth", tris=1000, res=128, role="cloth", pri=1.2)
    scarf = torus(0.4, 0.11).at(0, 4.22, -0.02).noise(0.02, 8, 1)
    scarf = scarf.su(tube([(0.2, 4.15, -0.35), (0.28, 3.85, -0.42), (0.25, 3.5, -0.4)], [0.1, 0.08, 0.07], k=0.04), 0.06)
    H.piece("Scarf", "Chest", scarf, col="secondary", mat="cloth", tris=500, role="cloth", pri=1.3)
    H.prim("Patch", "Chest", "Block", (0.22, 0.22, 0.04), (-0.3, 3.5, -0.5), rot=(0.05, 0.3, 0.2), col="cloth2", mat="cloth", role="detail", pri=2.3)
    for sx, nm, sfx in sides():
        s, e, w = mx(sh, sx), mx(el, sx), mx(wr, sx)
        sl = round_cone(T(s), T(e), 0.17, 0.14)
        H.piece("Sleeve" + nm, "Shoulder" + nm, sl, col="leather", mat="cloth", tris=250, role="limb", key=f"h_phead_sl{sfx}")
        fa = round_cone(T(e), T(w + A(0, 0.12, 0)), 0.14, 0.17)
        fa = fa - (sphere(0.13, T(w + A(0, 0.05, 0))))
        H.piece("Cuff" + nm, "Elbow" + nm, fa, col="leather", mat="cloth", tris=250, role="limb", key=f"h_phead_cuff{sfx}")
        H.piece("StrawW" + nm, "Hand" + nm, straw(w + A(0, 0.06, 0), (0.1 * sx, -1, -0.1), 9, 0.09, 0.2, seed=1 if sx > 0 else 2), col="gold", mat="cloth", tris=200, role="detail",
                key=f"h_phead_strw{sfx}", pri=1.9, ao=False)
        H.piece("Twigs" + nm, "Hand" + nm, bony_hand(w, s=1.0, out=(sx, 0, 0), length=1.1), col="wood", mat="wood", tris=350, role="hand", key=f"h_phead_hand{sfx}")
        hp, kn, ft = mx(A(0.28, 2.35, 0.0), sx), mx(A(0.32, 1.28, -0.05), sx), mx(A(0.34, 0.2, 0.0), sx)
        th = round_cone(T(hp), T(kn), 0.2, 0.15)
        H.piece("Thigh" + nm, "Hip" + nm, th, col="dark", mat="cloth", tris=300, role="limb", key=f"h_phead_th{sfx}")
        sn = round_cone(T(kn), T(ft + A(0, 0.4, 0)), 0.15, 0.16)
        sn = sn.su(straw(ft + A(0, 0.48, 0), (0, -0.3, -1), 8, 0.12, 0.12, seed=4 if sx > 0 else 5), 0.01)
        boot = ellipsoid(0.17, 0.17, 0.32, T(ft + A(0, 0.05, -0.12))).su(round_cone(T(ft + A(0, 0.4, 0)), T(ft + A(0, 0.1, 0)), 0.17, 0.17), 0.05)
        boot = boot & plane((0, -1, 0), 0.0)
        H.piece("Shin" + nm, "Knee" + nm, sn, col="dark", mat="cloth", tris=350, role="limb", key=f"h_phead_shin{sfx}")
        H.piece("Boot" + nm, "Foot" + nm, boot, col="black", mat="skin", tris=300, role="foot", key=f"h_phead_boot{sfx}")
    H.socket("mouth", T(hc + A(0, -0.25, -0.62)), "Head")
    H.socket("head", T(hc + A(0, 0.75, 0)), "Head")
    H.socket("hand", T(wr + A(0, -0.4, -0.1)), "HandR")
    H.rig.update({"head": "Head", "tail": ["CoatTail"]})
    mm.biped_extra(H, legs, arms, spine="Spine", head="Head", tail=["CoatTail"], stride=0.45, walk=1.05, height=5.6,
                   attack="punch", shamble=0.7, weapon_arm="ShoulderR")
    return H


# ================================================================================================ clouds and smoke
def puff_cluster(rng, center, spread, n, rmin, rmax, k=0.12, flat=None):
    """A cumulus mass: n spheres scattered in an ellipsoidal volume, smooth-unioned; flat = y below which it is
    softly flattened (the cloud base)."""
    out = None
    c = np.asarray(center, float)
    for i in range(n):
        p = c + A(*(rng.uniform(-1, 1, 3) * np.asarray(spread, float)))
        out = U(out, sphere(rng.uniform(rmin, rmax), T(p)), k=k)
    if flat is not None:
        out = out.si(plane((0, -1, 0), -flat), 0.15)
    return out


@hero("cloud spirit", "flora")
def cloud_spirit():
    """A stormy-tempered cumulus: a billowing body of rounded puffs with a soft flat grey underside, a scowling face
    (heavy slanted brows, round eyes, a pouting mouth between two puffable cheeks), puffy cloud arms ending in
    cloud fists, and wisps trailing beneath. The puffs swell and settle like breathing; attacks with a huge inhale
    and a gust."""
    H = Hero("cloud spirit", plan="Ghost", gait="float", tags=["cloud", "elemental", "weather"])
    H.preview = {"primary": "#F1F5F9", "secondary": "#64748B"}
    H.body((0, 2.2, 0))
    H.bone("Spine", "Body", (0, 2.4, 0))
    H.bone("PuffTop", "Spine", (0, 3.2, 0.1))
    H.mbone("Puff#", "Spine", (1.05, 2.45, 0.15))
    H.mbone("Cheek#", "Spine", (0.42, 2.05, -0.82))
    H.bone("Tail1", "Body", (0, 1.4, 0.2))
    H.bone("Tail2", "Tail1", (0, 0.9, 0.45))
    arms = arm_bones(H, A(1.25, 2.3, -0.2), A(1.75, 1.9, -0.35), A(2.0, 1.6, -0.55))
    rng = np.random.default_rng(21)
    shade = gradient(1, 1.4, 2.6, 0.72, 1.0)
    core = ellipsoid(1.15, 0.85, 0.85, (0, 2.4, 0.05)).su(puff_cluster(rng, (0, 2.5, 0.1), (0.7, 0.35, 0.45), 9, 0.38, 0.55), 0.2)
    core = core.si(plane((0, -1, 0), -1.55), 0.25)
    core = core.ss(ellipsoid(0.15, 0.17, 0.1, (0.3, 2.62, -0.86)).mirror_x(), 0.05)
    H.piece("Core", "Spine", core, col="primary", mat="cloth", tris=1600, res=128, role="body", pattern=shade)
    top = puff_cluster(rng, (0, 3.25, 0.15), (0.55, 0.2, 0.35), 6, 0.35, 0.52)
    H.piece("PuffTopP", "PuffTop", top, col="primary", mat="cloth", tris=900, role="body", pri=1.2)
    side = puff_cluster(np.random.default_rng(5), (1.15, 2.45, 0.2), (0.25, 0.3, 0.35), 5, 0.32, 0.45, flat=1.75)
    H.mpiece("PuffSide#", "Puff#", side, col="primary", mat="cloth", tris=700, role="body", pri=1.3, pattern=shade)
    H.mpiece("CheekP#", "Cheek#", sphere(0.26, (0.45, 2.05, -0.72)), col="primary", mat="cloth", tris=300, role="detail", pri=1.6)
    H.mprim("Eye#", "Spine", "Ball", (0.22, 0.26, 0.16), (0.3, 2.62, -0.82), col="pupil", mat="hard", role="eye", pri=1.3)
    H.mprim("Shine#", "Spine", "Ball", (0.08, 0.08, 0.08), (0.34, 2.68, -0.9), col="shine", mat="hard", role="shine", pri=2.5)
    H.mprim("Brow#", "Spine", "Ellipsoid", (0.42, 0.11, 0.12), (0.3, 2.86, -0.86), rot=(0, 0.25, 0.42), col="secondary", mat="cloth", role="detail", pri=1.5)
    H.prim("Mouth", "Spine", "Ellipsoid", (0.26, 0.12, 0.1), (0, 2.1, -0.92), rot=(0, 0, 0), col="mouth", mat="hard", role="mouth", pri=2.0)
    wis = U(sphere(0.38, (0, 1.45, 0.25)), sphere(0.3, (0.22, 1.25, 0.45)), tube([(0, 1.35, 0.3), (0, 1.05, 0.6), (0, 0.9, 0.85)], [0.3, 0.2, 0.14], k=0.1), k=0.12)
    H.piece("WispA", "Tail1", wis, col="primary", mat="cloth", tris=600, role="tail", pri=1.4, pattern=shade)
    H.piece("WispB", "Tail2", tube([(0, 0.95, 0.75), (0.05, 0.75, 1.1), (-0.05, 0.75, 1.4), (0, 0.9, 1.6)], [0.15, 0.12, 0.08, 0.03], k=0.05),
            col="primary", mat="cloth", tris=400, role="tail", pri=1.5, pattern=shade)
    for sx, nm, sfx in sides():
        s, e, w = mx(A(1.25, 2.3, -0.2), sx), mx(A(1.75, 1.9, -0.35), sx), mx(A(2.0, 1.6, -0.55), sx)
        ua = U(sphere(0.3, T(s)), sphere(0.26, T((s + e) / 2 + A(0, 0.05, 0))), sphere(0.24, T(e)), k=0.1)
        H.piece("Arm" + nm, "Shoulder" + nm, ua, col="primary", mat="cloth", tris=500, role="limb", key=f"h_cloudsp_arm{sfx}", pattern=shade)
        r2 = np.random.default_rng(3)
        fist = U(sphere(0.3, T(w)), *(sphere(0.17, T(w + A(*(r2.uniform(-0.2, 0.2, 3))) * A(1, 1, 1) + A(0, 0, -0.1))) for _ in range(4)), k=0.08)
        fist = fist.su(round_cone(T(e), T(w), 0.2, 0.24), 0.1)
        H.piece("Fist" + nm, "Elbow" + nm, fist, col="primary", mat="cloth", tris=500, role="hand", key=f"h_cloudsp_fist{sfx}", pattern=shade)
    H.socket("mouth", (0, 2.1, -1.0), "Spine")
    H.socket("head", (0, 3.8, 0), "PuffTop")
    H.socket("hand", (2.0, 1.5, -0.6), "HandR")
    H.rig.update({"head": "Spine", "tail": ["Tail1", "Tail2"]})
    mf.puffer(H, arms=arms, spine="Spine", head=None, tail=["Tail1", "Tail2"], height=4.0, hover=0.45, lean=0.12,
              puffs=[("PuffTop", (0, 1, 0.2)), ("PuffR", (1, 0.2, 0)), ("PuffL", (-1, 0.2, 0))], cheeks=["CheekR", "CheekL"])
    return H


def smoke_rope(a, b, r0, r1, strands=3, wind=1.6, spread=0.18, seed=0):
    """Twisted rope of smoke strands from a (bottom) to b (top) around a vertical axis through a (x, z)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    out = None
    n = 7
    for k in range(strands):
        pts, rad = [], []
        for i in range(n):
            t = i / (n - 1)
            ang = k / strands * math.tau + wind * t * math.tau
            r = r0 + (r1 - r0) * t
            c = a + (b - a) * t + A(math.sin(ang), 0, math.cos(ang)) * spread * (0.6 + r / max(r0, r1))
            pts.append(T(c))
            rad.append(r * 0.75)
        out = U(out, tube(pts, rad, k=0.06), k=0.08)
    return out


@hero("smoke wraith", "flora")
def smoke_wraith():
    """A hunched figure of rolling bonfire smoke (enenra): a torso of twisted smoke ropes, heavy billowed shoulders,
    a hood-like curl of smoke over ember eyes and a glowing maw, long sinuous arms ending in hooked wisp claws, and
    a lower body that spirals down to a curling point. Sways in a slow corkscrew; lunges with both claws."""
    H = Hero("smoke wraith", plan="Ghost", gait="float", tags=["smoke", "elemental", "spirit"])
    H.preview = {"primary": "#57534E", "secondary": "#A8A29E", "eyeGlow": "#FB923C"}
    H.body((0, 2.2, 0))
    H.bone("Spine", "Body", (0, 2.6, 0))
    H.bone("Head", "Spine", (0, 4.0, -0.25))
    H.mbone("Billow#", "Spine", (0.75, 3.6, 0.1))
    H.bone("Tail1", "Body", (0, 2.0, 0.05))
    H.bone("Tail2", "Tail1", (0, 1.3, 0.25))
    H.bone("Tail3", "Tail2", (0, 0.7, 0.55))
    sh, el, wr = A(0.95, 3.55, -0.1), A(1.45, 2.85, -0.45), A(1.6, 2.15, -0.9)
    arms = arm_bones(H, sh, el, wr)
    shade = gradient(1, 0.6, 4.0, 0.7, 1.05)
    tor = smoke_rope((0, 2.0, 0.05), (0, 3.55, -0.05), 0.42, 0.55, strands=3, wind=0.7, spread=0.2, seed=1)
    tor = tor.su(ellipsoid(0.75, 0.45, 0.5, (0, 3.5, 0.05)), 0.2)
    H.piece("Torso", "Spine", tor.noise(0.02, 5, 3), col="primary", mat="cloth", tris=1700, res=128, role="body", pattern=shade)
    bil = U(sphere(0.38, (0.85, 3.7, 0.1)), sphere(0.3, (0.6, 3.95, 0.25)), sphere(0.26, (1.05, 3.5, 0.3)), k=0.12).noise(0.02, 6, 5)
    H.mpiece("BillowP#", "Billow#", bil, col="primary", mat="cloth", tris=600, role="body", pri=1.3, pattern=shade)
    hc = A(0, 4.15, -0.35)
    hood = ellipsoid(0.42, 0.45, 0.45, T(hc)).su(tube([T(hc + A(0, 0.3, 0.0)), T(hc + A(0, 0.6, 0.35)), T(hc + A(0, 0.5, 0.75)), T(hc + A(0, 0.25, 0.85)), T(hc + A(0, 0.15, 0.7))],
                                                    [0.36, 0.3, 0.2, 0.12, 0.06], k=0.1), 0.15)
    hood = hood.ss(ellipsoid(0.32, 0.36, 0.3, T(hc + A(0, -0.06, -0.28))), 0.08)   # deep face hollow
    H.piece("Hood", "Head", hood.noise(0.015, 7, 2), col="secondary", mat="cloth", tris=1100, res=120, role="head", pattern=gradient(1, 3.8, 4.8, 0.75, 1.0))
    glow_eyes(H, "Head", T(hc + A(0.13, 0.05, -0.27)), (0.13, 0.06, 0.06), "eyeGlow", rot=(0, 0, -0.35))
    H.prim("Maw", "Head", "Ellipsoid", (0.16, 0.08, 0.05), T(hc + A(0, -0.18, -0.25)), col="eyeGlow", mat="hard", glow=True, role="mouth", pri=1.7)
    low = smoke_rope((0, 0.9, 0.45), (0, 2.1, 0.05), 0.12, 0.42, strands=3, wind=-0.9, spread=0.16, seed=2)
    H.piece("Swirl", "Tail1", low.noise(0.02, 6, 6), col="primary", mat="cloth", tris=1100, role="tail", pattern=shade)
    curl = tube([(0, 1.0, 0.45), (0.1, 0.6, 0.7), (0.0, 0.35, 1.0), (-0.2, 0.4, 1.2), (-0.25, 0.65, 1.15)], [0.16, 0.12, 0.08, 0.05, 0.02], k=0.05)
    H.piece("Curl", "Tail3", curl, col="primary", mat="cloth", tris=450, role="tail", pri=1.5, pattern=shade)
    for sx, nm, sfx in sides():
        s, e, w = mx(sh, sx), mx(el, sx), mx(wr, sx)
        ua = smoke_rope(s, e, 0.24, 0.17, strands=2, wind=0.6, spread=0.06)
        H.piece("UpperArm" + nm, "Shoulder" + nm, ua, col="primary", mat="cloth", tris=600, role="limb", key=f"h_smoke_ua{sfx}", pattern=shade)
        fa = smoke_rope(e, w, 0.17, 0.13, strands=2, wind=0.6, spread=0.05)
        H.piece("Forearm" + nm, "Elbow" + nm, fa, col="primary", mat="cloth", tris=500, role="limb", key=f"h_smoke_fa{sfx}", pattern=shade)
        cl = sphere(0.14, T(w))
        for i, dz in enumerate((-0.12, 0.0, 0.12)):
            a_ = w + A(0.02 * sx, -0.05, dz - 0.05)
            b_ = a_ + A(0.05 * sx, -0.3, -0.12 + dz * 0.4)
            c_ = b_ + A(-0.1 * sx, -0.18, -0.15)
            cl = cl.su(tube([T(a_), T(b_), T(c_)], [0.07, 0.045, 0.012], k=0.03), 0.04)
        H.piece("Claw" + nm, "Hand" + nm, cl, col="secondary", mat="cloth", tris=450, role="hand", key=f"h_smoke_claw{sfx}")
    H.prim("Ember1", "Spine", "Ball", (0.07, 0.07, 0.07), (0.3, 3.0, -0.48), col="eyeGlow", mat="hard", glow=True, role="detail", pri=2.6)
    H.prim("Ember2", "Spine", "Ball", (0.05, 0.05, 0.05), (-0.25, 2.55, -0.42), col="eyeGlow", mat="hard", glow=True, role="detail", pri=2.7)
    H.socket("mouth", T(hc + A(0, -0.18, -0.35)), "Head")
    H.socket("head", T(hc + A(0, 0.75, 0)), "Head")
    H.socket("hand", T(wr + A(0, -0.4, -0.2)), "HandR")
    H.rig.update({"head": "Head", "tail": ["Tail1", "Tail2", "Tail3"]})
    mf.puffer(H, arms=arms, spine="Spine", head="Head", tail=["Tail1", "Tail2", "Tail3"], height=4.8, hover=0.3, lean=0.25,
              puffs=[("BillowR", (1, 0.4, 0)), ("BillowL", (-1, 0.4, 0))], swirl=1.0)
    return H


# ================================================================================================ star and sun
def star_prism(center, R, r_in, depth, points=5, rot=0.0, bevel=0.03):
    """Bevelled n-point star facing -Z: the classic ridged star (each arm a low pyramid), centred at `center`."""
    c = np.asarray(center, float)
    outer = [(R * math.cos(rot + math.pi / 2 + i * math.tau / points), R * math.sin(rot + math.pi / 2 + i * math.tau / points)) for i in range(points)]
    inner = [(r_in * math.cos(rot + math.pi / 2 + (i + 0.5) * math.tau / points), r_in * math.sin(rot + math.pi / 2 + (i + 0.5) * math.tau / points)) for i in range(points)]
    poly = []
    for i in range(points):
        poly.append(outer[i])
        poly.append(inner[i])
    pv = np.asarray(poly, float)

    def f(p):
        q = p - c
        d2 = poly2d(q[:, :2], pv)                     # < 0 inside the outline
        rr = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
        # height falls off toward the outline: a ridge field (distance to the outline) gives pyramid facets
        h = np.clip(-d2, 0, None) / r_in * depth * 1.6
        h = np.minimum(h, depth) + 0.02 * R
        dz = np.abs(q[:, 2]) - h
        return np.maximum(d2, dz * 0.6)

    return SDF(f).round(bevel)


@hero("star spirit", "flora")
def star_spirit():
    """A plump five-point star with ridged bevelled arms and a sweet face (big shiny eyes, a smile, blush), trailing
    three tumbling little stars like a shooting-star tail, with two sparkles orbiting. Bobs, tilts and twinkles;
    attacks with a spinning dash."""
    H = Hero("star spirit", plan="Ghost", gait="hover", tags=["star", "spirit", "celestial"])
    H.preview = {"primary": "#FEF08A", "secondary": "#93C5FD"}
    c = A(0, 1.9, 0)
    H.body(T(c))
    H.bone("Face", "Body", T(c + A(0, 0.05, -0.2)))
    H.bone("Tail1", "Body", T(c + A(0.35, -0.3, 0.6)))
    H.bone("Tail2", "Tail1", T(c + A(0.7, -0.55, 1.2)))
    H.bone("Tail3", "Tail2", T(c + A(0.95, -0.75, 1.75)))
    H.bone("SparkA", "Body", T(c + A(1.25, 0.6, -0.1)))
    H.bone("SparkB", "Body", T(c + A(-1.15, -0.2, 0.1)))
    star = star_prism(c, 1.35, 0.6, 0.22, bevel=0.06)
    star = star.ss(ellipsoid(0.11, 0.14, 0.12, T(c + A(0.22, 0.1, -0.36))).mirror_x().at(0, 0, 0), 0.04)
    H.piece("Star", "Body", star, col="primary", mat="glass", tr=0.05, tris=1800, res=144, role="body", pattern=gradient(1, 0.6, 3.2, 0.82, 1.0))
    cute_eyes(H, "Face", T(c + A(0.22, 0.1, -0.31)), 0.1, tall=1.3)
    H.prim("Smile", "Face", "Ellipsoid", (0.22, 0.08, 0.06), T(c + A(0, -0.17, -0.31)), col="mouth", mat="hard", role="mouth", pri=2.0)
    H.mprim("Blush#", "Face", "Ellipsoid", (0.14, 0.07, 0.05), T(c + A(0.4, -0.08, -0.27)), rot=(0, 0.3, 0), col="blush", mat="hard", role="mouth", pri=2.4, tr=0.3)
    for i, (b, s, col) in enumerate((("Tail1", 0.42, "secondary"), ("Tail2", 0.3, "primary"), ("Tail3", 0.2, "secondary"))):
        p = H.bpos(b)
        H.piece(f"Mini{i + 1}", b, star_prism(p, s, s * 0.45, s * 0.35, rot=0.4 * (i + 1), bevel=0.03), col=col, mat="glass", tr=0.1, tris=400, role="tail", pri=1.5 + i * 0.2)
    for b in ("SparkA", "SparkB"):
        p = H.bpos(b)
        sp = U(*(crystal(T(p), T(p + A(*d) * 0.22), 0.05, tip=0.9, sides=4) for d in ((0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0))))
        H.piece(b + "P", b, sp, col="white", mat="glass", tris=200, role="detail", pri=2.2)
    H.socket("mouth", T(c + A(0, -0.17, -0.55)), "Face")
    H.socket("head", T(c + A(0, 1.5, 0)), "Body")
    H.rig.update({"head": "Face", "tail": ["Tail1", "Tail2", "Tail3"]})
    mf.twinkle(H, points=[("Tail1", 1), ("Tail2", -1), ("Tail3", 1)], face="Face", height=3.2, hover=0.5,
               extra=[("SparkA", 0.0), ("SparkB", 2.0)])
    return H


@hero("sun spirit", "flora")
def sun_spirit():
    """A beaming sun: a round puffed disc with a carved happy face (closed smiling eyes, a wide grin, rosy cheeks),
    ringed by a short inner crown of points and an outer corona of twelve curling flame rays that slowly turns.
    Floats and bobs; attacks with a spinning flare."""
    H = Hero("sun spirit", plan="Ghost", gait="hover", tags=["sun", "spirit", "celestial", "fire"])
    H.preview = {"primary": "#FDE047", "secondary": "#F97316"}
    c = A(0, 2.0, 0)
    H.body(T(c))
    H.bone("Face", "Body", T(c + A(0, 0, -0.3)))
    H.bone("Rays", "Body", T(c))
    disc = ellipsoid(1.0, 1.0, 0.6, T(c))
    disc = disc.su(ellipsoid(0.24, 0.16, 0.12, T(c + A(0.48, -0.2, -0.45))).mirror_x(), 0.12)   # apple cheeks
    smile = torus(0.42, 0.065, axis=2).at(*T(c + A(0, 0.1, -0.56))) & plane((0, 1, 0), c[1] - 0.12)
    disc = disc.ss(smile, 0.03)
    H.piece("Disc", "Body", disc, col="primary", mat="skin", tris=1500, res=128, role="body", pattern=gradient(2, -0.7, 0.4, 1.0, 0.85))
    eyes = None
    for sx in (1, -1):
        arc = torus(0.13, 0.035, axis=2).at(*T(c + A(0.33 * sx, 0.2, -0.56))) & plane((0, -1, 0), -(c[1] + 0.22))
        eyes = U(eyes, arc)
    H.piece("Eyes", "Face", eyes, col="mouth", mat="hard", tris=300, role="eye", pri=1.3)
    H.prim("Grin", "Face", "Ellipsoid", (0.62, 0.12, 0.06), T(c + A(0, -0.3, -0.5)), col="mouth", mat="hard", role="mouth", pri=2.0)
    H.mprim("Blush#", "Face", "Ellipsoid", (0.2, 0.1, 0.05), T(c + A(0.5, -0.17, -0.55)), rot=(0, 0.35, 0), col="blush", mat="hard", role="mouth", pri=2.4, tr=0.3)
    crown = None
    for i in range(12):
        a = (i + 0.5) / 12 * math.tau
        d = A(math.sin(a), math.cos(a), 0)
        crown = U(crown, round_cone(T(c + d * 0.85), T(c + d * 1.32), 0.17, 0.03).scale3(1, 1, 1) & SDF(lambda p, c=c: np.abs(p[:, 2] - c[2]) - 0.12))
    H.piece("Crown", "Body", crown, col="secondary", mat="skin", tris=900, res=120, role="horn", pri=1.3)
    rays = None
    for i in range(12):
        a = i / 12 * math.tau
        d = A(math.sin(a), math.cos(a), 0)
        side = A(math.cos(a), -math.sin(a), 0)
        rays = U(rays, flame(T(c + d * 0.95), T(d), 1.0, 0.2, side=T(side), curl=0.22))
    H.piece("Corona", "Rays", rays, col="secondary", mat="glass", tr=0.05, tris=1800, res=144, role="flame", pri=1.2)
    H.socket("mouth", T(c + A(0, -0.3, -0.6)), "Face")
    H.socket("head", T(c + A(0, 2.2, 0)), "Body")
    H.rig.update({"head": "Face"})
    mf.twinkle(H, rays="Rays", ray_step=math.tau / 12, face="Face", height=4.2, hover=0.5)
    return H


# ================================================================================================ cosmic beasts
def quad_bones(H, fs, fe, fw, hh, hk, hc):
    """Leg chains: front shoulder / elbow / wrist and hind hip / knee / hock (right side given, mirrored)."""
    H.mbone("ShoulderF#", "Body", T(fs))
    H.mbone("ElbowF#", "ShoulderF#", T(fe))
    H.mbone("WristF#", "ElbowF#", T(fw))
    H.mbone("HipB#", "Body", T(hh))
    H.mbone("KneeB#", "HipB#", T(hk))
    H.mbone("HockB#", "KneeB#", T(hc))
    return [("HipBL", "KneeBL", "HockBL", 0.0, False), ("ShoulderFL", "ElbowFL", "WristFL", 0.25, True),
            ("HipBR", "KneeBR", "HockBR", 0.5, False), ("ShoulderFR", "ElbowFR", "WristFR", 0.75, True)]


@hero("comet beast", "flora")
def comet_beast():
    """A lean ice-wolf of the void: a deep-chested frosted body, a wedge head with a crest of swept-back ice horns,
    jagged crystal shards running down the spine and ruffing the neck, glowing eyes, long legs with crystal-clawed
    paws, and a blazing comet tail of streaming flame tongues that ripples behind it."""
    H = Hero("comet beast", plan="Quadruped", gait="trot", tags=["beast", "ice", "celestial"])
    H.preview = {"primary": "#BAE6FD", "secondary": "#F8FAFC", "glow": "#7DD3FC", "eyeGlow": "#E0F2FE"}
    H.body((0, 2.1, 0))
    H.bone("Chest", "Body", (0, 2.2, -0.7))
    H.bone("Neck", "Chest", (0, 2.6, -1.3))
    H.bone("Head", "Neck", (0, 3.05, -1.75))
    H.bone("Jaw", "Head", (0, 2.9, -1.9))
    H.bone("Tail1", "Body", (0, 2.35, 1.2))
    H.bone("Tail2", "Tail1", (0, 2.6, 2.1))
    H.bone("Tail3", "Tail2", (0, 2.85, 3.0))
    fs, fe, fw = A(0.42, 2.0, -0.85), A(0.46, 1.2, -0.75), A(0.46, 0.38, -0.82)
    hh, hk, hc = A(0.42, 2.05, 0.9), A(0.48, 1.3, 0.6), A(0.46, 0.68, 1.05)
    legs = quad_bones(H, fs, fe, fw, hh, hk, hc)
    tor = ellipsoid(0.62, 0.72, 0.85, (0, 2.15, -0.6)).su(ellipsoid(0.5, 0.55, 0.75, (0, 2.2, 0.75)), 0.5)
    tor = tor.ss(ellipsoid(0.7, 0.3, 0.6, (0, 1.4, 0.3)), 0.3)  # tucked belly
    H.piece("Torso", "Body", tor.noise(0.01, 6, 2), col="primary", mat="skin", tris=1200, res=128, role="body",
            pattern=combine(gradient(1, 1.5, 2.8, 0.78, 1.0), gradient(2, -1.2, 1.4, 1.0, 0.85)))
    neck = round_cone((0, 2.35, -1.0), (0, 2.95, -1.6), 0.45, 0.3)
    H.piece("NeckP", "Neck", neck, col="primary", mat="skin", tris=400, role="neck")
    ruff = None
    rng = np.random.default_rng(4)
    for i in range(9):
        a = (i / 8 - 0.5) * 3.6
        d = A(math.sin(a), math.cos(a) * 0.9, 0.35)
        base = A(0, 2.65, -1.15) + A(math.sin(a) * 0.38, math.cos(a) * 0.32, 0)
        ruff = U(ruff, crystal(T(base), T(base + d * rng.uniform(0.45, 0.65) + A(0, 0, 0.3)), 0.09, tip=0.45, sides=5))
    H.piece("IceRuff", "Neck", ruff, col="secondary", mat="glass", tr=0.1, tris=500, role="mane", pri=1.3)
    hd = ellipsoid(0.38, 0.34, 0.46, (0, 3.1, -1.8)).su(round_cone((0, 3.0, -2.0), (0, 2.92, -2.45), 0.24, 0.13), 0.15)
    hd = hd.ss(ellipsoid(0.09, 0.06, 0.1, (0.2, 3.13, -2.05)).mirror_x(), 0.03)
    H.piece("HeadP", "Head", hd, col="primary", mat="skin", tris=800, role="head")
    jaw = round_cone((0, 2.85, -1.85), (0, 2.8, -2.35), 0.16, 0.09)
    H.piece("JawP", "Jaw", jaw, col="primary", mat="skin", tris=250, role="jaw")
    horns = None
    for sx in (1, -1):
        horns = U(horns, crystal((0.18 * sx, 3.3, -1.75), (0.45 * sx, 3.75, -1.1), 0.08, tip=0.5, sides=5),
                  crystal((0.25 * sx, 3.2, -1.65), (0.6 * sx, 3.35, -1.15), 0.06, tip=0.5, sides=5))
    horns = U(horns, crystal((0, 3.35, -1.9), (0, 3.85, -1.45), 0.08, tip=0.45, sides=5))
    H.piece("Horns", "Head", horns, col="secondary", mat="glass", tr=0.1, tris=500, role="horn", pri=1.2)
    glow_eyes(H, "Head", (0.2, 3.13, -2.04), (0.12, 0.06, 0.06), "eyeGlow", rot=(0, 0.4, -0.2))
    H.prim("Nose", "Head", "Ellipsoid", (0.14, 0.09, 0.09), (0, 2.98, -2.55), col="nose", mat="hard", role="detail", pri=2.0)
    shards = None
    for i, (z, h) in enumerate(((-0.9, 0.75), (-0.45, 0.65), (0.0, 0.55), (0.45, 0.45), (0.85, 0.35))):
        y = 2.8 - 0.05 * i
        shards = U(shards, crystal((0, y - 0.15, z), (0, y + h, z + 0.35), 0.11, tip=0.45, sides=5, twist=0.3 * i))
        shards = U(shards, crystal((0.12, y - 0.2, z + 0.1), (0.22, y + h * 0.55, z + 0.35), 0.07, tip=0.5, sides=5))
    H.piece("Shards", "Body", shards, col="secondary", mat="glass", tr=0.1, tris=600, role="horn", pri=1.3)
    # comet tail: a glowing root, then fans of streaming flame tongues
    root = U(sphere(0.32, (0, 2.35, 1.3)), round_cone((0, 2.35, 1.3), (0, 2.55, 2.1), 0.3, 0.38), k=0.1)
    H.piece("TailRoot", "Tail1", root, col="glow", mat="glass", tr=0.1, tris=350, role="tail", pri=1.2)
    fan = None
    for i in range(6):
        a = i / 6 * math.tau
        off = A(math.sin(a) * 0.22, math.cos(a) * 0.22, 0)
        fan = U(fan, flame(T(A(0, 2.6, 2.1) + off), (off[0] * 1.5, 0.25 + off[1] * 1.5, 1), 1.3, 0.22, side=(math.cos(a), -math.sin(a), 0), curl=0.18))
    H.piece("TailFlames", "Tail2", fan, col="glow", mat="glass", tr=0.15, tris=800, role="tail", pri=1.3)
    tip = None
    for i in range(4):
        a = i / 4 * math.tau + 0.4
        off = A(math.sin(a) * 0.15, math.cos(a) * 0.15, 0)
        tip = U(tip, flame(T(A(0, 2.85, 3.0) + off), (off[0], 0.2 + off[1], 1), 1.0, 0.13, side=(math.cos(a), -math.sin(a), 0), curl=0.3))
    H.piece("TailTips", "Tail3", tip, col="secondary", mat="glass", tr=0.2, tris=450, role="tail", pri=1.5)
    for sx, nm, sfx in sides():
        s, e, w = mx(fs, sx), mx(fe, sx), mx(fw, sx)
        H.piece("UpperF" + nm, "ShoulderF" + nm, round_cone(T(s + A(0, 0.15, 0)), T(e), 0.31, 0.19), col="primary", mat="skin", tris=250, role="limb", key=f"h_comet_uf{sfx}")
        H.piece("LowerF" + nm, "ElbowF" + nm, round_cone(T(e), T(w), 0.18, 0.13), col="primary", mat="skin", tris=200, role="limb", key=f"h_comet_lf{sfx}")
        paw = ellipsoid(0.16, 0.12, 0.22, T(w + A(0, -0.27, -0.08))).su(round_cone(T(w), T(w + A(0, -0.25, -0.05)), 0.13, 0.15), 0.06)
        for dx in (-0.08, 0.0, 0.08):
            paw = paw | crystal(T(w + A(dx, -0.3, -0.22)), T(w + A(dx, -0.35, -0.38)), 0.03, tip=0.6, sides=4)
        H.piece("PawF" + nm, "WristF" + nm, paw & plane((0, -1, 0), 0.0), col="primary", mat="skin", tris=250, role="foot", key=f"h_comet_pf{sfx}")
        hp, kn, hk_ = mx(hh, sx), mx(hk, sx), mx(hc, sx)
        H.piece("Thigh" + nm, "HipB" + nm, round_cone(T(hp + A(0, 0.1, -0.1)), T(kn), 0.42, 0.21), col="primary", mat="skin", tris=300, role="limb", key=f"h_comet_th{sfx}")
        H.piece("Shank" + nm, "KneeB" + nm, round_cone(T(kn), T(hk_), 0.2, 0.13), col="primary", mat="skin", tris=200, role="limb", key=f"h_comet_sh{sfx}")
        hp_ = round_cone(T(hk_), T(hk_ + A(0, -0.55, -0.12)), 0.13, 0.13).su(ellipsoid(0.15, 0.12, 0.22, T(hk_ + A(0, -0.58, -0.2))), 0.06)
        H.piece("PawB" + nm, "HockB" + nm, hp_ & plane((0, -1, 0), 0.0), col="primary", mat="skin", tris=250, role="foot", key=f"h_comet_pb{sfx}")
    H.socket("mouth", (0, 2.85, -2.45), "Jaw")
    H.socket("head", (0, 3.9, -1.6), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": ["Tail1", "Tail2", "Tail3"]})
    mf.beast(H, legs, spine="Chest", neck="Neck", head="Head", jaw="Jaw", tail=["Tail1", "Tail2", "Tail3"], height=3.3,
             walk=0.75, stride=0.5, stream=1.0)
    return H


@hero("moon beast", "flora")
def moon_beast():
    """A round grey moon-rock beast built for low gravity: a boulder body pocked with craters, huge springy hind legs
    with long rabbit feet, stubby forepaws, a broad head with big glowing eyes, a wide toothy mouth and two long
    swept-back ears. Bounds in slow floating leaps."""
    H = Hero("moon beast", plan="Quadruped", gait="hop", tags=["beast", "celestial"])
    H.preview = {"primary": "#D1D5DB", "secondary": "#94A3B8", "eyeGlow": "#FEF9C3"}
    H.body((0, 1.7, 0.1))
    H.bone("Chest", "Body", (0, 1.8, -0.5))
    H.bone("Head", "Chest", (0, 2.3, -1.05))
    H.bone("Jaw", "Head", (0, 1.95, -1.35))
    H.mbone("Ear#", "Head", (0.32, 2.85, -0.85))
    H.bone("Tail1", "Body", (0, 1.7, 1.15))
    fs, fe, fw = A(0.55, 1.3, -0.75), A(0.6, 0.8, -0.95), A(0.6, 0.32, -0.95)
    hh, hk, hc = A(0.7, 1.55, 0.6), A(0.8, 0.95, 0.05), A(0.78, 0.45, 0.85)
    legs = quad_bones(H, fs, fe, fw, hh, hk, hc)
    craters = [A(0.62, 2.25, 0.35), A(-0.5, 2.4, -0.1), A(0.2, 2.55, 0.6), A(-0.75, 1.75, 0.55), A(0.85, 1.6, -0.2),
               A(-0.15, 2.3, 1.05), A(0.45, 1.25, 0.95), A(-0.6, 1.2, -0.4)]
    bd = ellipsoid(1.0, 0.88, 1.1, (0, 1.75, 0.15)).su(ellipsoid(0.85, 0.7, 0.6, (0, 1.75, -0.55)), 0.3)
    craters = project(bd, craters)
    for i, p in enumerate(craters):
        r = 0.2 + 0.08 * (i % 3)
        n = p - A(0, 1.75, 0.1)
        n /= np.linalg.norm(n)
        bd = bd.su(torus(r, 0.05, axis=1).rot(*(0, 0, 0)).warp(lambda q, n=n, p=p: _frame(q, p, n)), 0.04)
        bd = bd.ss(sphere(r, T(p + n * r * 0.75)), 0.05)
    def crater_shade(P, cs=craters):
        m = np.ones(len(P))
        for p in cs:
            d = np.linalg.norm(P - p, axis=1)
            m = m * (1 - 0.3 * np.clip(1 - d / 0.3, 0, 1))
        return m
    H.piece("Torso", "Body", bd.noise(0.025, 5, 3), col="primary", mat="stone", tris=1500, res=144, role="body",
            pattern=combine(crater_shade, gradient(1, 0.9, 2.6, 0.8, 1.0)))
    hd = ellipsoid(0.62, 0.48, 0.5, (0, 2.3, -1.1)).noise(0.02, 6, 4)
    hd = hd.ss(sphere(0.17, (0.28, 2.4, -1.55)).mirror_x(), 0.04)
    H.piece("HeadP", "Head", hd, col="primary", mat="stone", tris=900, role="head", pattern=gradient(1, 1.9, 2.8, 0.85, 1.0))
    for sx in (1, -1):
        H.prim("Eye" + ("R" if sx > 0 else "L"), "Head", "Ball", (0.26, 0.26, 0.2), (0.28 * sx, 2.4, -1.47), col="eyeGlow", mat="hard", glow=True, role="eye", pri=1.4)
        H.prim("Pupil" + ("R" if sx > 0 else "L"), "Head", "Ball", (0.11, 0.13, 0.08), (0.28 * sx, 2.4, -1.57), col="pupil", mat="hard", role="pupil", pri=1.5)
    jaw = ellipsoid(0.5, 0.2, 0.4, (0, 1.95, -1.2)) - ellipsoid(0.42, 0.14, 0.34, (0, 2.05, -1.22))
    for i, x in enumerate((-0.3, -0.1, 0.1, 0.3)):
        jaw = jaw | crystal((x, 1.98, -1.52), (x, 2.12, -1.53), 0.04, tip=0.6, sides=4)
    H.piece("JawP", "Jaw", jaw, col="secondary", mat="stone", tris=600, role="jaw")
    for sx, nm, sfx in sides():
        b = A(0.32 * sx, 2.75, -0.95)
        ear = tube([T(b), T(b + A(0.15 * sx, 0.45, 0.3)), T(b + A(0.25 * sx, 0.7, 0.85)), T(b + A(0.28 * sx, 0.65, 1.25))], [0.11, 0.15, 0.12, 0.04], k=0.06)
        ear = ear.scale3(1, 1, 1)
        H.piece("Ear" + nm, "Ear" + nm, ear, col="secondary", mat="stone", tris=450, role="ear", key=f"h_moonb_ear{sfx}")
        s, e, w = mx(fs, sx), mx(fe, sx), mx(fw, sx)
        H.piece("ArmF" + nm, "ShoulderF" + nm, round_cone(T(s), T(e), 0.25, 0.18), col="primary", mat="stone", tris=300, role="limb", key=f"h_moonb_af{sfx}")
        paw = round_cone(T(e), T(w), 0.17, 0.16).su(ellipsoid(0.21, 0.14, 0.25, T(w + A(0, -0.17, -0.08))), 0.06) & plane((0, -1, 0), 0.0)
        H.piece("PawF" + nm, "ElbowF" + nm, paw, col="primary", mat="stone", tris=400, role="foot", key=f"h_moonb_pf{sfx}")
        hp, kn, hk_ = mx(hh, sx), mx(hk, sx), mx(hc, sx)
        H.piece("Haunch" + nm, "HipB" + nm, ellipsoid(0.42, 0.6, 0.62, T(A(0.58 * sx, 1.4, 0.45))).noise(0.02, 6, 7), col="primary", mat="stone", tris=600,
                role="limb", key=f"h_moonb_hn{sfx}")
        H.piece("Shank" + nm, "KneeB" + nm, round_cone(T(kn), T(hk_), 0.25, 0.17), col="primary", mat="stone", tris=300, role="limb", key=f"h_moonb_sk{sfx}")
        foot = round_cone(T(hk_), T(hk_ + A(0, -0.32, -0.75)), 0.17, 0.15).su(ellipsoid(0.17, 0.1, 0.45, T(hk_ + A(0, -0.36, -0.45))), 0.08) & plane((0, -1, 0), 0.0)
        H.piece("Foot" + nm, "HockB" + nm, foot, col="secondary", mat="stone", tris=400, role="foot", key=f"h_moonb_ft{sfx}")
    H.piece("Tuft", "Tail1", sphere(0.25, (0, 1.75, 1.25)).noise(0.03, 8, 2), col="secondary", mat="stone", tris=300, role="tail", pri=1.6)
    H.socket("mouth", (0, 2.0, -1.55), "Jaw")
    H.socket("head", (0, 3.2, -1.0), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": ["Tail1"]})
    mf.beast(H, legs, spine="Chest", neck=None, head="Head", jaw="Jaw", tail=["Tail1"], ears=["EarR", "EarL"], height=2.8,
             walk=0.8, stride=0.4, low=True)
    return H


def _frame(q, p, n):
    """Map points into a frame centred on p with local +Y along n (for laying a ring flat on a surface)."""
    n = n / np.linalg.norm(n)
    t0 = np.cross(n, (0, 0, 1) if abs(n[2]) < 0.9 else (1, 0, 0))
    t0 /= np.linalg.norm(t0)
    t1 = np.cross(n, t0)
    d = q - p
    return np.column_stack([d @ t0, d @ n, d @ t1])


# ================================================================================================ word -> hero rules
STARRY = {"cat": ["Creature", "Element"], "bp": ["Orb", "Cloud", "Blob", "Ghost", "Humanoid", "Swarm"]}
MAP = [
    ("mushroom king", "mushroom king, mushroom queen, mushroom lord, toadstool king, fungus king, fungal lord, shroom king, myconid, "
                      "mushroom man, mushroom person, mushroom folk, mushroom knight, mushroom warrior, mushroom elder", WALKER),
    ("mushroom sprite", "mushroom sprite, mushroom, toadstool, shroom, mushroom creature, mushroom monster, mushroom baby, sporeling, "
                        "fungus creature, puffball, mushling, toadstool sprite", PLANT),
    ("cactus creature", "cactus creature, cactus, cactus man, cactus monster, cactus walker, saguaro, cactus buddy, prickly pear monster, "
                        "living cactus", PLANT),
    ("jack o lantern", "jack o lantern, jack-o-lantern, jackolantern, jack o' lantern, haunted pumpkin, pumpkin spirit, pumpkin monster, "
                       "evil pumpkin, living pumpkin, pumpkin creature, pumpkin", PLANT),
    ("pumpkin head", "pumpkin head, pumpkinhead, pumpkin king, pumpkin man, pumpkin knight, jack the pumpkin king", WALKER),
    ("cloud spirit", "cloud spirit, cloud elemental, cloud monster, cloud creature, angry cloud, raincloud, rain cloud, air elemental, "
                     "steam elemental, steam spirit, mist elemental, fog elemental, fog spirit, mist spirit, nebula spirit, nebula elemental", SKY),
    ("lightning elemental", "storm cloud spirit, storm cloud, thundercloud, thunder cloud spirit", SKY),
    ("smoke wraith", "smoke wraith, smoke elemental, smoke spirit, smoke monster, smoke demon, enenra, ash wraith, soot spirit, "
                     "smog monster, fume spirit, ash elemental", SKY),
    ("star spirit", "star spirit, star, shooting star, wishing star, star sprite, starlight spirit, star child, little star, twinkle star, "
                    "falling star, aurora spirit", STARRY),
    ("sun spirit", "sun spirit, sun, sun face, solar spirit, sunshine spirit, sun sprite, sun elemental", STARRY),
    ("comet beast", "comet beast, comet, comet wolf, meteor beast, star beast, astral beast, cosmic wolf, astral wolf", BEAST),
    ("moon beast", "moon beast, lunar beast, moon monster, crater beast, moon hound, moon calf", BEAST),
    ("rabbit", "moon spirit, moon rabbit, jade rabbit", BEAST),
    # these words were caught by broader rules elsewhere (wisp: "sprite" / "pumpkin spirit", treant: "myconid")
    ("wisp", "!mushroom, !pumpkin", NOTFOOD),
    ("treant", "!myconid", NOTFOOD),
]
