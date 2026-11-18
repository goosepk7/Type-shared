"""Flying birds: raptors (eagle, hawk, falcon, vulture, condor, osprey), owls (owl, barn owl, snowy owl), parrots
(parrot, macaw, cockatoo), toucan, hornbill, songbirds (bird / sparrow, robin, cardinal, blue jay, bluebird, finch,
swallow), crow / raven, magpie, pigeon / dove, seagull, albatross, pelican, hummingbird, woodpecker, kingfisher.

One parametric sculpt (`_flyer`): a feathered torso with a separate breast panel, a neck and head with a chosen
beak (hooked raptor, cone, dagger, parrot hook, toucan, pouch, needle, chisel ...) on its own lower-mandible bone,
crests / ear tufts / facial disc / ruffs, and two big three-bone wings built from LAYERED feather fans:
scapulars + tertials on the arm, a row of secondaries with greater and median coverts on the forearm, fanned
primaries (separated "fingers" on soaring birds) with primary coverts and an alula on the hand. The tail is two
mirrored half fans that spread apart. Legs: feathered thigh, scaled tarsus, three forward toes + hallux with talons.

The model is authored standing with spread wings (feet on y = 0); the fly clips (motion_birds.fly) carry it up,
flap the wing chains, fan the tail and tuck the legs. Shared sculpt helpers (oriented ellipsoids, feathers, polygon
slabs) live here and are used by h_birds_ground.py and h_birds_bats.py too.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF
from kit import Hero, hero, stripes, spots, gradient, combine
from map import NOTFOOD
import motion_birds as MB

BIRD = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Plant", "Weather", "Structure"],
        "bp": ["Bird", "Quadruped", "Biped", "Blob", "Dragon", "Humanoid", "Ghost", "Giant", "Swarm", "Fish"]}


# ======================================================================================================== helpers
def U(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def A(*v):
    return np.array(v, float)


def bounded(sd, c, r):
    """Tag an SDF with a bounding sphere so unite() can skip far points."""
    sd.bc = np.asarray(c, float)
    sd.br = float(r)
    return sd


def oell(c, u, v, ra, rb, rc):
    """Oriented ellipsoid: centre c, long axis u (radius ra), width axis v (rb), normal u x v (rc)."""
    c = np.asarray(c, float)
    u = U(u)
    v = np.asarray(v, float)
    v = U(v - (v @ u) * u)
    w = np.cross(u, v)
    R = np.stack([u, v, w])
    r = np.array([ra, rb, rc], float)

    def f(p):
        q = (p - c) @ R.T
        k0 = np.linalg.norm(q / r, axis=1)
        k1 = np.linalg.norm(q / (r * r), axis=1)
        return np.where(k1 > 1e-9, k0 * (k0 - 1.0) / np.maximum(k1, 1e-9), -r.min())

    return bounded(SDF(f), c, float(r.max()) * 1.02)


def feather(base, d, length, width, thick, side, roll=0.0, over=0.15, droop=0.0):
    """One feather vane: a long flat ellipsoid from slightly before `base` along direction d. side: rough width
    axis (in the wing plane); roll tilts the vane about its shaft so neighbours overlap like shingles."""
    d = U(d)
    side = np.asarray(side, float)
    v = U(side - (side @ d) * d)
    w = np.cross(d, v)
    if roll:
        v, w = math.cos(roll) * v + math.sin(roll) * w, -math.sin(roll) * v + math.cos(roll) * w
    if droop:
        d = U(d - droop * w)
    base = np.asarray(base, float)
    c = base + d * length * (1 - over) * 0.5
    ra = length * (1 + over) * 0.5
    return bounded(oell(c, d, v, ra, width * 0.5, thick * 0.5), c, ra * 1.02)


def lerp(a, b, t):
    return np.asarray(a, float) + (np.asarray(b, float) - np.asarray(a, float)) * t


def slerp_dir(a, b, t):
    a, b = U(a), U(b)
    om = math.acos(max(-1.0, min(1.0, float(a @ b))))
    if om < 1e-4:
        return a
    return U((math.sin((1 - t) * om) * a + math.sin(t * om) * b) / math.sin(om))


def rot_y(d, ang):
    c, s = math.cos(ang), math.sin(ang)
    return np.array([c * d[0] + s * d[2], d[1], -s * d[0] + c * d[2]])


def unite(shapes, k=0.0):
    bnd = [x for x in shapes if hasattr(x, "bc")]
    if k == 0 and len(bnd) > 2:
        rest = [x for x in shapes if not hasattr(x, "bc")]
        items = [(x, x.bc, x.br) for x in bnd]
        C = np.array([c for _, c, _ in items])
        R = np.array([r for _, _, r in items])

        def f(p):
            out = np.full(len(p), np.inf)
            for (sd, c, r) in items:
                dc = np.linalg.norm(p - c, axis=1) - r
                near = dc < 0.15 * r + 0.02
                out = np.minimum(out, np.where(near, np.inf, dc))
                if near.any():
                    out[near] = np.minimum(out[near], sd(p[near]))
            return out

        res = SDF(f)
        lo = (C - R[:, None]).min(0)
        hi = (C + R[:, None]).max(0)
        res = bounded(res, (lo + hi) / 2, float(np.linalg.norm(hi - lo) / 2))
        if rest:
            return unite([res] + rest) if len(rest) > 1 else (res | rest[0])
        return res
    s = shapes[0]
    for o in shapes[1:]:
        s = s.su(o, k) if k > 0 else (s | o)
    return s


def poly2d(P, V):
    """Signed distance from 2D points P (N,2) to polygon V (M,2) (iq), negative inside."""
    d = np.sum((P - V[0]) ** 2, axis=1)
    s = np.ones(len(P))
    M = len(V)
    j = M - 1
    for i in range(M):
        e = V[j] - V[i]
        w = P - V[i]
        h = np.clip((w @ e) / (e @ e), 0, 1)
        b = w - h[:, None] * e
        d = np.minimum(d, np.sum(b * b, axis=1))
        c1 = P[:, 1] >= V[i][1]
        c2 = P[:, 1] < V[j][1]
        c3 = e[0] * w[:, 1] > e[1] * w[:, 0]
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
        j = i
    return s * np.sqrt(d)


def slab(pts, thick, n=None):
    """A thin flat plate whose outline is the 3D polygon pts (nearly planar), thickness `thick`."""
    P = np.asarray(pts, float)
    c = P.mean(0)
    _, _, Vt = np.linalg.svd(P - c)
    e1, e2, nn = Vt[0], Vt[1], Vt[2]
    if n is not None and nn @ np.asarray(n, float) < 0:
        nn = -nn
    Q = np.column_stack([(P - c) @ e1, (P - c) @ e2])

    def f(p):
        r = p - c
        d2 = poly2d(np.column_stack([r @ e1, r @ e2]), Q)
        dz = np.abs(r @ nn) - thick * 0.5
        return np.minimum(np.maximum(d2, dz), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(dz, 0) ** 2)

    return SDF(f)


def scallop(cell, depth=0.12, seed=2):
    """Subtle feather-edge scallops baked into the vertex colour."""
    return spots(cell, cell * 0.5, depth=depth, ring=True, seed=seed)


def band_mask(origin, axis, freq, width=0.35, depth=0.5, region=None):
    o = np.asarray(origin, float)
    a = U(axis)
    return stripes(lambda Q: (Q - o) @ a, freq, width=width, depth=depth, region=region)


def dist_shade(origin, near, far, a=1.0, b=0.6):
    """Darken with distance from a point (wing / tail feather tips)."""
    o = np.asarray(origin, float)

    def f(P):
        t = np.clip((np.linalg.norm(P - o, axis=1) - near) / max(far - near, 1e-6), 0, 1)
        return a + (b - a) * t

    return f


# ---------------------------------------------------------------------------------------------------- beaks
def beak_shapes(kind, L, D, W):
    """(upper, lower) beak SDFs in a local frame: base centre at the origin, pointing -Z, +Y up."""
    if kind == "hook":       # raptor: deep base, tip hooks down over the lower mandible
        up = tube([(0, 0.06 * D, 0.1 * L), (0, 0.04 * D, -0.35 * L), (0, -0.05 * D, -0.7 * L), (0, -0.35 * D, -0.98 * L), (0, -0.7 * D, -0.95 * L)],
                  [0.5 * D, 0.44 * D, 0.32 * D, 0.17 * D, 0.05 * D], k=0.06 * D)
        lo = round_cone((0, -0.3 * D, 0.05 * L), (0, -0.38 * D, -0.62 * L), 0.33 * D, 0.1 * D)
    elif kind == "parrot":   # deep curved upper, deep scoop lower
        up = tube([(0, 0.15 * D, 0.1 * L), (0, 0.25 * D, -0.3 * L), (0, 0.05 * D, -0.75 * L), (0, -0.45 * D, -0.95 * L), (0, -0.95 * D, -0.78 * L)],
                  [0.58 * D, 0.55 * D, 0.42 * D, 0.24 * D, 0.06 * D], k=0.1 * D)
        lo = round_cone((0, -0.42 * D, 0.0), (0, -0.62 * D, -0.45 * L), 0.42 * D, 0.2 * D)
    elif kind == "toucan":   # enormous, laterally flat, slightly decurved
        up = tube([(0, 0.05 * D, 0.1 * L), (0, 0.08 * D, -0.35 * L), (0, -0.05 * D, -0.75 * L), (0, -0.3 * D, -1.0 * L)],
                  [0.5 * D, 0.46 * D, 0.32 * D, 0.08 * D], k=0.05 * D)
        lo = tube([(0, -0.35 * D, 0.05 * L), (0, -0.4 * D, -0.5 * L), (0, -0.38 * D, -0.92 * L)], [0.32 * D, 0.22 * D, 0.06 * D], k=0.04 * D)
    elif kind == "pouch":    # pelican: long flat upper with a hooked nail, lower with a hanging pouch
        up = tube([(0, 0.02 * D, 0.1 * L), (0, 0.0, -0.6 * L), (0, -0.04 * D, -0.98 * L), (0, -0.3 * D, -1.03 * L)], [0.42 * D, 0.32 * D, 0.24 * D, 0.1 * D], k=0.04 * D)
        lo = tube([(0, -0.28 * D, 0.05 * L), (0, -0.3 * D, -0.6 * L), (0, -0.28 * D, -0.96 * L)], [0.34 * D, 0.24 * D, 0.14 * D], k=0.04 * D)
        lo = lo.su(ellipsoid(0.5 * D, 1.1 * D, 0.38 * L, (0, -1.0 * D, -0.38 * L)), 0.25 * D)
    elif kind == "needle":   # hummingbird / kiwi
        up = round_cone((0, 0.02 * D, 0.1 * L), (0, -0.08 * D, -1.0 * L), 0.42 * D, 0.12 * D)
        lo = round_cone((0, -0.25 * D, 0.05 * L), (0, -0.2 * D, -0.95 * L), 0.3 * D, 0.1 * D)
    elif kind == "decurve":  # ibis / curlew: long, curving down
        up = tube([(0, 0.0, 0.1 * L), (0, -0.05 * L, -0.4 * L), (0, -0.2 * L, -0.78 * L), (0, -0.42 * L, -0.98 * L)], [0.42 * D, 0.32 * D, 0.22 * D, 0.1 * D], k=0.03 * D)
        lo = tube([(0, -0.3 * D, 0.05 * L), (0, -0.05 * L - 0.28 * D, -0.38 * L), (0, -0.19 * L - 0.25 * D, -0.72 * L)], [0.3 * D, 0.22 * D, 0.12 * D], k=0.03 * D)
    elif kind == "cone":     # finch / sparrow: short thick cone
        up = round_cone((0, 0.08 * D, 0.1 * L), (0, -0.05 * D, -1.0 * L), 0.5 * D, 0.06 * D)
        lo = round_cone((0, -0.3 * D, 0.05 * L), (0, -0.2 * D, -0.85 * L), 0.4 * D, 0.06 * D)
    elif kind == "crow":     # strong, slightly arched culmen
        up = tube([(0, 0.08 * D, 0.1 * L), (0, 0.1 * D, -0.45 * L), (0, -0.08 * D, -0.88 * L), (0, -0.28 * D, -1.0 * L)], [0.48 * D, 0.38 * D, 0.2 * D, 0.06 * D], k=0.05 * D)
        lo = round_cone((0, -0.3 * D, 0.05 * L), (0, -0.3 * D, -0.85 * L), 0.36 * D, 0.06 * D)
    elif kind == "gull":     # straight with a hooked tip and a gonys angle below
        up = tube([(0, 0.05 * D, 0.1 * L), (0, 0.02 * D, -0.6 * L), (0, -0.05 * D, -0.92 * L), (0, -0.3 * D, -1.0 * L)], [0.42 * D, 0.32 * D, 0.24 * D, 0.08 * D], k=0.04 * D)
        lo = tube([(0, -0.3 * D, 0.05 * L), (0, -0.42 * D, -0.7 * L), (0, -0.3 * D, -0.9 * L)], [0.32 * D, 0.24 * D, 0.08 * D], k=0.04 * D)
    else:                    # "dagger" / "chisel" / "short": straight and pointed
        up = round_cone((0, 0.05 * D, 0.1 * L), (0, -0.08 * D, -1.0 * L), 0.48 * D, 0.05 * D)
        lo = round_cone((0, -0.28 * D, 0.05 * L), (0, -0.22 * D, -0.94 * L), 0.36 * D, 0.05 * D)
    wf = W / D
    return up.scale3(wf, 1.0, 1.0), lo.scale3(wf * 0.95, 1.0, 1.0)


def beak_tip(kind, L, D):
    if kind in ("hook", "parrot"):
        return np.array((0, -0.6 * D, -0.95 * L))
    if kind == "decurve":
        return np.array((0, -0.42 * L, -0.98 * L))
    return np.array((0, -0.1 * D, -1.0 * L))


# ---------------------------------------------------------------------------------------------------- wings
def wing_geo(Sh, El, Wr, Tip, P):
    """Feathered wing (right side) -> dict of SDFs: arm, sec, cov, prim, pcov (+ shading origins)."""
    C = P["chord"]
    th = P["fthick"] * C
    out = {}
    fold_up = A(0, 1, 0)
    # ---- arm: humerus, scapulars and tertials
    arm = oell(lerp(Sh, El, 0.5) + A(0, 0.0, 0.05 * C), El - Sh, A(0, 0, 1), np.linalg.norm(El - Sh) * 0.55 + 0.1 * C, 0.28 * C, 0.1 * C)
    fs = [arm]
    nt = 4
    for i in range(nt):
        t = 0.12 + 0.82 * i / (nt - 1)
        b = lerp(Sh, El, t) + A(0, 0.01 * C, 0.08 * C)
        d = U(A(0.05 + 0.15 * t, -0.08, 1))
        fs.append(feather(b, d, C * (0.72 + 0.2 * t), C * 0.36, th * 1.1, A(1, 0, 0), roll=0.14))
    for i in range(4):  # scapular coverts on top
        t = 0.05 + 0.85 * i / 3
        b = lerp(Sh, El, t) + A(0, 0.06 * C, 0.02 * C)
        fs.append(feather(b, U(A(0.12, -0.12, 1)), C * 0.5, C * 0.3, th * 1.2, A(1, 0, 0), roll=0.18))
    out["arm"] = unite(fs)
    # ---- secondaries (flight feathers on the forearm)
    ns = P["nsec"]
    fe = []
    for i in range(ns):
        t = i / (ns - 1)
        b = lerp(El - A(0.04 * C, 0, 0), Wr, t) + A(0, -0.01 * C, 0.04 * C)
        d = U(A(0.04 + 0.32 * t, -0.07, 1))
        ln = C * (1.0 - 0.06 * t) * (1 + 0.05 * math.sin(i * 2.1))
        fe.append(feather(b, d, ln, C * 0.26 * 7.0 / ns * 1.25, th, Wr - El, roll=-0.16, droop=0.04))
    out["sec"] = unite(fe)
    # ---- forearm coverts: leading edge (patagium) + greater + median rows
    fc = [oell(lerp(El, Wr, 0.5) + A(0, 0.03 * C, -0.04 * C), Wr - El, A(0, 0, 1), np.linalg.norm(Wr - El) * 0.56 + 0.06 * C, 0.2 * C, 0.085 * C)]
    fc.append(oell(lerp(Sh, Wr, 0.35) + A(0, 0.04 * C, -0.1 * C), Wr - Sh, A(0, 0, 1), np.linalg.norm(Wr - Sh) * 0.45, 0.11 * C, 0.07 * C))  # patagium
    ng = ns
    for i in range(ng):
        t = i / (ng - 1)
        b = lerp(El - A(0.02 * C, 0, 0), Wr, t) + A(0, 0.035 * C, 0.0)
        d = U(A(0.06 + 0.3 * t, -0.08, 1))
        fc.append(feather(b, d, C * 0.52, C * 0.3 * 7.0 / ng * 1.25, th * 1.05, Wr - El, roll=-0.2))
    nm = max(ns - 2, 5)
    for i in range(nm):
        t = i / (nm - 1)
        b = lerp(El, Wr, t) + A(0, 0.07 * C, -0.04 * C)
        d = U(A(0.08 + 0.28 * t, -0.1, 1))
        fc.append(feather(b, d, C * 0.3, C * 0.3 * 7.0 / nm * 1.2, th * 1.1, Wr - El, roll=-0.22))
    out["cov"] = unite(fc)
    # ---- primaries (fanned on the hand)
    h = Tip - Wr
    hl = np.linalg.norm(h)
    npm = P["nprim"]
    fing = P["fingers"]
    d_in = U(A(0.4, -0.07, 1))
    d_out = U(h)
    fp = []
    for i in range(npm):
        t = i / (npm - 1)
        b = Wr + h * (0.02 + 0.32 * t) + A(0, -0.012 * C * i, 0.02 * C)
        tt = t ** P["fan_pow"]
        d = slerp_dir(d_in, d_out, tt)
        outer = i >= npm - fing
        k = (i - (npm - fing)) if outer else 0
        if outer:
            d = rot_y(d, 0.06 * (k - fing * 0.5) * P["spread"])
        if P["pointed"]:
            ln = C * 1.0 + (hl * 0.95 - C) * (t ** 1.2)
            if i == npm - 1:
                ln *= 0.93
        else:
            ln = C * 1.02 + (hl * 0.86 - C) * (t ** 0.9)
            if outer:
                ln *= 1.0 - 0.06 * max(0, k - fing + 2)
        wd = C * P["pwidth"] * (0.55 if outer else 1.0)
        fp.append(feather(b, d, ln, wd, th * (1.1 if outer else 1.0), A(0, 0, 1) if abs(d[2]) < 0.5 else A(1, 0, 0), roll=0.12 * (1 if d[0] > 0.6 else -1), droop=0.05 if outer else 0.02))
    out["prim"] = unite(fp)
    # ---- primary coverts + alula + hand leading edge
    fk = [oell(Wr + h * 0.22 + A(0, 0.03 * C, -0.03 * C), h, A(0, 0, 1), hl * 0.3 + 0.08 * C, 0.16 * C, 0.08 * C)]
    nk = max(npm - 2, 5)
    for i in range(nk):
        t = i / (nk - 1)
        b = Wr + h * (0.0 + 0.3 * t) + A(0, 0.035 * C, 0.0)
        d = slerp_dir(d_in, d_out, (t ** P["fan_pow"]) * 0.85)
        fk.append(feather(b, d, C * 0.42, C * 0.25, th * 1.1, A(0, 0, 1) if abs(d[2]) < 0.5 else A(1, 0, 0), roll=0.15))
    fk.append(feather(Wr + A(0, 0.06 * C, -0.05 * C), U(A(1, 0.05, -0.25)), C * 0.32, C * 0.1, th * 1.2, A(0, 0, 1), roll=0.2))  # alula
    out["pcov"] = unite(fk)
    return out


def tail_half(base, P, side_sign=1):
    """Right half of the tail fan (feathers fanning from straight back to outward)."""
    n = P["ntail"]
    Lt, Wt = P["tail_len"], P["tail_w"]
    th = P["fthick"] * P["chord"] * 0.95
    kind = P["tail"]
    fs = []
    for k in range(n):
        t = k / max(n - 1, 1)
        ang = 0.07 + P["tail_spread"] * t
        d = U(A(math.sin(ang), -0.06 - 0.04 * t, math.cos(ang)))
        if kind == "fork":
            ln = Lt * (0.6 + 0.75 * t ** 2.2)
        elif kind == "long":          # central pair longest (magpie, macaw, quetzal)
            ln = Lt * (1.0 - 0.55 * t ** 0.7)
        elif kind == "wedge":
            ln = Lt * (1.0 - 0.3 * t)
        elif kind == "square":
            ln = Lt * (1.0 + 0.04 * t)
        elif kind == "stub":
            ln = Lt * (1.0 - 0.15 * t)
        else:                         # rounded fan
            ln = Lt * (1.0 - 0.14 * t ** 2)
        b = np.asarray(base, float) + A(0.025 + 0.06 * Wt * k, 0.012 * (n - k), -0.04 * Lt * t)
        fs.append(feather(b, d, ln, Wt * (0.85 if kind == "fork" and k == n - 1 else 1.0), th, A(1, 0, 0), roll=-0.12, over=0.2))
    return unite(fs)


# ====================================================================================================== builder
BASE = dict(
    body=1.0, girth=1.0, neck=0.35, head=1.0, upright=0.0,
    beak="hook", beak_len=0.42, beak_depth=0.26, beak_w=0.2, beak_col="beak", cere=False,
    span=1.0, l1=0.95, l2=1.15, l3=1.55, chord=1.0, nsec=9, nprim=9, fingers=0, spread=1.0, pointed=False,
    pwidth=0.3, fan_pow=0.85, fthick=0.06, sweep=0.15,
    tail="fan", tail_len=1.0, tail_w=0.3, ntail=4, tail_spread=0.55,
    leg=0.9, leg_r=0.075, trousers=False, toe=0.32, talon=0.0, foot_col="beak", zygo=False,
    crest=None, tufts=0.0, disc=None, ruff=None, casque=False, cap=False, mask=False, wattle=False,
    eye=0.17, eye_col="iris", eye_fwd=False, brow=0.0,
    cols={}, pat=None, gait="fly", attack="talon", period=0.85, amp=0.8, hover_pitch=0.0, buzz=0, lift=0.35,
    idle_amp=0.55, fold=0.55, preview={}, tags=("bird",),
)

COLS = dict(back="primary", belly="secondary", head="primary", neck=None, wing="primary", flight="primary", tail="primary",
            leg="beak", crest="secondary", face="secondary", ruff="secondary", cap="secondary", mask="dark", throat=None,
            cere="beak", rump=None)


def _flyer(hid, *presets, **kw):
    P = dict(BASE)
    for pr in presets:
        P.update(pr)
    P.update(kw)
    col = dict(COLS)
    col.update(P["cols"])
    if col["neck"] is None:
        col["neck"] = col["head"]
    H = Hero(hid, plan="Bird", gait=P["gait"], tags=list(P["tags"]))
    H.preview = P["preview"]
    BL, G, HS, NK = P["body"], P["girth"], P["head"], P["neck"]
    LL = P["leg"]
    BY = LL + 0.36 * G
    H.body((0, BY, 0))

    # ------------------------------------------------------------------ patterns
    fine = scallop(0.13 * G, depth=0.1)
    pat_body = fine
    if P["pat"] == "streaks":
        pat_body = combine(fine, stripes(lambda Q: Q[:, 0] * 3.0 + 0.4 * np.sin(Q[:, 1] * 11), 1.4, width=0.22, depth=0.35, wobble=0.05, seed=4,
                                         region=lambda Q: (Q[:, 1] < BY + 0.1).astype(float)))
    elif P["pat"] == "bars":
        pat_body = combine(fine, stripes(lambda Q: Q[:, 1] + 0.15 * np.abs(Q[:, 0]), 7.0, width=0.3, depth=0.32, wobble=0.02, seed=6))
    elif P["pat"] == "spots":
        pat_body = combine(fine, spots(0.16 * G, 0.045, depth=0.6, seed=8))
    elif P["pat"] == "flecks":
        pat_body = combine(fine, spots(0.2 * G, 0.04, depth=0.55, seed=9))

    # ------------------------------------------------------------------ torso
    up = P["upright"]
    zf, zb = -0.75 * BL, 0.85 * BL
    torso = oell((0, BY + 0.02, 0.0), (0, 0.18 * up, 1), (1, 0, 0), 0.95 * BL, 0.5 * G, 0.47 * G)
    torso = torso.su(ellipsoid(0.46 * G, 0.44 * G, 0.5 * BL, (0, BY + 0.08 + 0.1 * up, zf + 0.2)), 0.25)       # chest / crop
    torso = torso.su(round_cone((0, BY + 0.06, 0.4 * BL), (0, BY + 0.06 - 0.1 * up, zb + 0.05), 0.36 * G, 0.17 * G), 0.25)  # rump to tail
    torso = torso.su(ellipsoid(0.3 * G, 0.18 * G, 0.42 * BL, (0.24 * G, BY + 0.28 * G, -0.15)).mirror_x(), 0.2)    # wing roots / mantle
    H.piece("Torso", "Body", torso, col=col["back"], tris=1500, res=112, pattern=combine(pat_body, gradient(1, BY - 0.4, BY + 0.5, 0.92, 1.0)))
    breast = oell((0, BY - 0.1 * G, -0.18 * BL), (0, -0.1 + 0.25 * up, 1), (1, 0, 0), 0.78 * BL, 0.43 * G, 0.4 * G)
    breast = breast.su(ellipsoid(0.49 * G, 0.46 * G, 0.53 * BL, (0, BY + 0.03 + 0.1 * up, zf + 0.16)), 0.2)   # chest / crop front
    H.piece("Breast", "Body", breast, col=col["belly"], tris=700, res=96, role="body", pri=1.2, pattern=pat_body)

    # ------------------------------------------------------------------ neck + head
    hr = 0.3 * HS
    nb = A(0, BY + 0.18 * G + 0.1 * up, zf + 0.05)
    hc = nb + A(0, 0.12 + 0.55 * NK * (0.6 + 0.5 * up), -0.25 - 0.55 * NK * (1 - 0.4 * up) - 0.25 * hr)
    H.bone("Neck", "Body", tuple(nb))
    H.bone("Head", "Neck", tuple(hc + A(0, -0.3 * hr, 0.35 * hr)))
    neck = round_cone(tuple(nb + A(0, -0.08, 0.15)), tuple(hc + A(0, -0.25 * hr, 0.2 * hr)), 0.34 * G, 0.82 * hr)
    H.piece("NeckP", "Neck", neck, col=col["neck"], tris=600, res=96, role="limb", pri=1.1, pattern=fine)

    def h(x, y, z):
        return tuple(hc + A(x * hr, y * hr, z * hr))

    head = ellipsoid(0.86 * hr, 0.84 * hr, 1.0 * hr, h(0, 0, 0.05))
    head = head.su(ellipsoid(0.74 * hr, 0.7 * hr, 0.85 * hr, h(0, -0.15, -0.3)), 0.25 * hr)       # cheeks / face
    head = head.su(ellipsoid(0.75 * hr, 0.5 * hr, 0.8 * hr, h(0, 0.25, 0.3)), 0.25 * hr)          # crown / nape
    head = head.su(round_cone(h(0, -0.05, -0.3), h(0, -0.08, -0.82), 0.62 * hr, min(0.5 * hr, 0.62 * P["beak_depth"] * HS + 0.12 * hr)), 0.2 * hr)  # face tapers into the beak
    if P["brow"] > 0:  # raptor brow ridge shading the eye
        head = head.su(capsule(h(0.3, 0.38, -0.55), h(0.62, 0.32, -0.25), 0.16 * hr * P["brow"]).mirror_x(), 0.12 * hr)
    ey = P["eye"]
    if P["eye_fwd"]:
        epos = A(0.38, 0.12, -0.78)
        look = (0.22, 0.02, -1.0)
    else:
        epos = A(0.66, 0.16, -0.48)
        look = (0.85, 0.12, -0.45)
    epos_w = hc + epos * hr
    head = head.ss(sphere(ey * hr * 1.08, tuple(epos_w)).mirror_x(), 0.05 * hr)
    if P["tufts"] > 0:
        tf = P["tufts"]
        for i, (dx, dz) in enumerate(((0.0, 0.0), (0.12, 0.1))):
            head = head.su(round_cone(h(0.42 + dx, 0.62, -0.25 + dz), h(0.72 + dx, 0.62 + 0.75 * tf, -0.05 + dz + 0.2 * tf), 0.17 * hr, 0.03 * hr).mirror_x(), 0.08 * hr)
    H.piece("HeadP", "Head", head, col=col["head"], tris=1100, res=104, role="head", pri=1.3, pattern=fine)
    H.eyes("Head", tuple(epos_w), ey * hr, col=("iris" if P["eye_col"] == "iris" else "pupil"), pupil=("round" if P["eye_col"] == "iris" else None), look=look)

    # beak
    bk = P["beak"]
    BLn, BD, BW = P["beak_len"] * HS, P["beak_depth"] * HS, P["beak_w"] * HS
    b0 = hc + A(0, -0.05 * hr, -0.78 * hr)
    upb, lob = beak_shapes(bk, BLn, BD, BW)
    H.piece("Beak", "Head", upb.at(*b0), col=P["beak_col"], mat="hard", tris=500, res=96, role="beak", pri=1.6)
    jw = b0 + A(0, -0.2 * BD, 0.15 * hr)
    H.bone("Jaw", "Head", tuple(jw))
    H.piece("LowerBeak", "Jaw", lob.at(*b0), col=P["beak_col"], mat="hard", tris=320, res=88, role="jaw", pri=1.6)
    H.prim("Mouth", "Jaw", "Ellipsoid", (BW * 0.7, BD * 0.12, BLn * 0.5), tuple(b0 + A(0, -0.24 * BD, -0.25 * BLn)), col="mouth", mat="hard", role="mouth", pri=2.4)
    if P["cere"]:
        cere = ellipsoid(0.62 * BW, 0.45 * BD, 0.22 * BLn, tuple(b0 + A(0, 0.1 * BD, 0.02)))
        H.piece("Cere", "Head", cere, col=col["cere"], mat="skin", tris=250, res=72, role="beak", pri=1.7)
    if P["casque"]:  # hornbill casque riding on the upper bill
        cq = tube([tuple(b0 + A(0, 0.45 * BD, 0.05)), tuple(b0 + A(0, 0.6 * BD, -0.35 * BLn)), tuple(b0 + A(0, 0.4 * BD, -0.6 * BLn))], [0.35 * BD, 0.32 * BD, 0.1 * BD], k=0.05)
        H.piece("Casque", "Head", cq.scale3(1.0, 1.0, 1.0), col="secondary", mat="hard", tris=400, res=88, role="horn", pri=1.7)
    if P["mask"]:   # dark face mask / moustache stripe (cardinal, falcon, shrike)
        mk2 = (ellipsoid(0.32 * hr, 0.4 * hr, 0.3 * hr, h(0.6, -0.02, -0.55)) if P["mask"] != "moustache" else capsule(h(0.66, 0.0, -0.45), h(0.6, -0.62, -0.45), 0.12 * hr))
        shell_ = head.round(0.035 * hr) & mk2.mirror_x().round(0.0)
        shell_ = shell_.ss(sphere(ey * hr * 1.3, tuple(epos_w)).mirror_x(), 0.02 * hr)
        H.piece("Mask", "Head", shell_, col=col["mask"], tris=400, res=96, role="detail", pri=1.5)
    if col.get("throat"):   # throat / gorget patch (hummingbird, swallow, sparrow bib)
        tp = head.round(0.035 * hr) & ellipsoid(0.62 * hr, 0.48 * hr, 0.6 * hr, h(0, -0.62, -0.42))
        H.piece("Throat", "Head", tp, col=col["throat"], tris=400, res=96, role="detail", pri=1.5)
    if P["cap"]:    # coloured crown cap (woodpecker red, chickadee black)
        cp = head.round(0.04 * hr) & ellipsoid(0.75 * hr, 0.5 * hr, 0.85 * hr, h(0, 0.72, 0.15))
        H.piece("Cap", "Head", cp, col=col["cap"], tris=400, res=96, role="crest", pri=1.5)
    if P["disc"]:   # owl facial disc: two shallow cups around the eyes, a ruff rim
        heart = P["disc"] == "heart"
        disc = ellipsoid(0.98 * hr, (1.12 if heart else 0.95) * hr, 0.42 * hr, h(0, -0.08, -0.62))
        disc = disc.ss(sphere(0.55 * hr, h(0.38, 0.06, -1.33)).mirror_x(), 0.12 * hr)
        if heart:
            disc = disc.ss(sphere(0.32 * hr, h(0, 1.12, -0.7)), 0.15 * hr)
        disc = disc.ss(sphere(ey * hr * 1.12, tuple(epos_w)).mirror_x(), 0.03 * hr)
        H.piece("Face", "Head", disc, col=col["face"], tris=900, res=104, role="detail", pri=1.4, pattern=gradient(2, hc[2] - 1.0 * hr, hc[2] - 0.3 * hr, 1.0, 0.78))
    if P["ruff"]:   # vulture / condor neck ruff
        rf = torus(0.42 * G, 0.16 * G, axis=2).rot(-35, 0, 0).at(*(nb + A(0, 0.02, 0.08)))
        rf = rf.noise(0.035, 9.0, 3)
        H.piece("Ruff", "Body", rf, col=col["ruff"], tris=900, res=96, role="mane", pri=1.2)
    if P["crest"]:
        ck = P["crest"]
        cb = hc + A(0, 0.62 * hr, 0.05 * hr)
        H.bone("Crest", "Head", tuple(cb))
        if ck == "cockatoo":
            fs = []
            for i in range(6):
                a = math.radians(-25 + i * 17)
                tip = cb + A(0, math.cos(a) * 1.75 * hr, math.sin(a) * 1.6 * hr + 0.45 * hr)
                fs.append(tube([tuple(cb + A(0, 0, -0.45 * hr + 0.14 * hr * i)), tuple(lerp(cb, tip, 0.6) + A(0, 0.15 * hr, -0.35 * hr)), tuple(tip)],
                               [0.16 * hr, 0.12 * hr, 0.03 * hr], k=0.02))
            cr = unite(fs, 0.03 * hr)
        elif ck == "harpy":
            cr = unite([round_cone(tuple(cb + A(sx * 0.18 * hr, 0, 0.1 * hr)), tuple(cb + A(sx * 0.42 * hr, 0.75 * hr, 0.7 * hr)), 0.16 * hr, 0.04 * hr) for sx in (-1, 1)], 0.06 * hr)
        elif ck == "tuft":   # small rounded tuft (titmouse, waxwing, lark)
            cr = round_cone(tuple(cb + A(0, -0.05 * hr, -0.2 * hr)), tuple(cb + A(0, 0.55 * hr, 0.55 * hr)), 0.32 * hr, 0.06 * hr)
        else:  # "pointed" (cardinal, blue jay, quail)
            cr = round_cone(tuple(cb + A(0, -0.1 * hr, -0.35 * hr)), tuple(cb + A(0, 0.8 * hr, 0.6 * hr)), 0.42 * hr, 0.05 * hr)
            cr = cr.su(round_cone(tuple(cb + A(0, 0.0, 0.0)), tuple(cb + A(0, 0.65 * hr, 0.75 * hr)), 0.3 * hr, 0.03 * hr), 0.05 * hr)
        H.piece("CrestP", "Crest", cr, col=col["crest"], tris=500, res=88, role="crest", pri=1.4)
    if P["wattle"]:
        H.piece("Throat", "Head", ellipsoid(0.42 * hr, 0.4 * hr, 0.35 * hr, h(0, -0.8, -0.2)), col="red", tris=250, res=64, role="detail", pri=1.5)

    # ------------------------------------------------------------------ wings
    sp = P["span"]
    L1, L2, L3, C = P["l1"] * sp, P["l2"] * sp, P["l3"] * sp, P["chord"]
    Sh = A(0.34 * G, BY + 0.24 * G, -0.32 * BL)
    El = Sh + A(L1, 0.05, 0.1)
    Wr = El + A(L2, 0.04, -0.14)
    Tip = Wr + A(L3, -0.02, P["sweep"] * L3)
    H.mbone("Shoulder#", "Body", tuple(Sh))
    H.mbone("Elbow#", "Shoulder#", tuple(El))
    H.mbone("Wrist#", "Elbow#", tuple(Wr))
    wg = wing_geo(Sh, El, Wr, Tip, P)
    wpat = scallop(0.1 * C, depth=0.1, seed=3)
    H.mpiece("Arm#", "Shoulder#", wg["arm"], col=col["wing"], tris=700, res=120, role="wing", pri=1.1, pattern=wpat)
    H.mpiece("Coverts#", "Elbow#", wg["cov"], col=col["wing"], tris=900, res=128, role="wing", pri=1.15, pattern=wpat)
    sec_pat = combine(gradient(2, El[2], El[2] + C, 1.0, 1.0 - 0.35 * P.get("tipdark", 1.0)), P.get("wing_pat_sec"))
    H.mpiece("Secondaries#", "Elbow#", wg["sec"], col=col["flight"], tris=900, res=128, role="wing", pri=1.0, pattern=sec_pat)
    prim_pat = combine(dist_shade(Wr, 0.3 * L3, L3 * 1.05, 1.0, 1.0 - 0.45 * P.get("tipdark", 1.0)), P.get("wing_pat_prim"))
    H.mpiece("Primaries#", "Wrist#", wg["prim"], col=col["flight"], tris=1100, res=136, role="wing", pri=1.0, pattern=prim_pat)
    H.mpiece("HandCoverts#", "Wrist#", wg["pcov"], col=col["wing"], tris=600, res=120, role="wing", pri=1.15, pattern=wpat)

    # ------------------------------------------------------------------ tail
    tb = A(0, BY + 0.06 - 0.1 * up, zb - 0.05)
    H.bone("Tail", "Body", tuple(tb))
    H.mbone("TailFan#", "Tail", tuple(tb + A(0.03, 0, 0.05)))
    tpat = combine(gradient(2, tb[2], tb[2] + P["tail_len"], 1.0, 1.0 - 0.3 * P.get("tipdark", 1.0)), P.get("tail_pat"))
    H.mpiece("TailHalf#", "TailFan#", tail_half(tb, P), col=col["tail"], tris=650, res=120, role="tail", pri=1.2, pattern=tpat)
    rump = oell(tuple(tb + A(0, 0.06, 0.12)), (0, -0.1, 1), (1, 0, 0), 0.38 * P["tail_len"] + 0.15, 0.22 * G, 0.08 * G)
    H.piece("TailCoverts", "Tail", rump, col=col["rump"] or col["back"], tris=300, res=80, role="tail", pri=1.3, pattern=fine)

    # ------------------------------------------------------------------ legs
    hip = A(0.2 * G, BY - 0.18 * G, 0.12 * BL)
    ank = A(0.22 * G, 0.42 * LL, 0.2 * BL)
    ft = A(0.22 * G, 0.07, 0.02)
    H.mbone("Hip#", "Body", tuple(hip))
    H.mbone("Ankle#", "Hip#", tuple(ank))
    H.mbone("Foot#", "Ankle#", tuple(ft))
    if P["trousers"]:
        th_ = oell(lerp(hip, ank, 0.45), hip - ank, A(1, 0, 0), np.linalg.norm(hip - ank) * 0.62, 0.17 * G, 0.2 * G).noise(0.012, 14, 5)
        th_ = th_.su(ellipsoid(0.13 * G, 0.14, 0.16, tuple(ank + A(0, 0.03, 0.03))), 0.05)
        H.mpiece("Thigh#", "Hip#", th_, col=col.get("thigh", col["belly"]), tris=450, res=88, role="limb", pri=1.2, pattern=pat_body)
    else:
        th_ = round_cone(tuple(hip + A(0, 0.08, 0)), tuple(ank), 0.15 * G, P["leg_r"] * 1.15)
        H.mpiece("Thigh#", "Hip#", th_, col=col["belly"], tris=350, res=80, role="limb", pri=1.2)
    lr = P["leg_r"]
    sh_ = round_cone(tuple(ank), tuple(ft + A(0, 0.03, 0.02)), lr, lr * 0.85)
    sh_ = sh_.su(sphere(lr * 1.15, tuple(ank)), 0.03)
    H.mpiece("Shank#", "Ankle#", sh_, col=col["leg"], tris=300, res=80, role="limb", pri=1.3)
    T = P["toe"]
    tr_ = lr * 0.62
    toes = [sphere(lr * 1.05, tuple(ft + A(0, 0.0, 0)))]
    tips = []
    dirs = [(-0.42, -1), (0.0, -1), (0.42, -1), (0.0, 1.0)]
    if P["zygo"]:
        dirs = [(-0.3, -1), (0.3, -1), (-0.35, 1.0), (0.35, 1.0)]
    for i, (dx, dz) in enumerate(dirs):
        ln = T * (0.62 if dz > 0 and not P["zygo"] else 1.0) * (1.08 if dx == 0 and dz < 0 else 1.0)
        d = U(A(dx, 0, dz))
        mid = ft + d * ln * 0.55 + A(0, -0.0, 0)
        tip = ft + d * ln + A(0, -0.035, 0)
        toes.append(tube([tuple(ft), tuple(mid), tuple(tip)], [tr_, tr_ * 0.95, tr_ * 0.75], k=0.02))
        tips.append((tip, d))
    H.mpiece("Toes#", "Foot#", unite(toes, 0.03), col=col["leg"], tris=420, res=88, role="foot", pri=1.4)
    tl = max(P["talon"], 0.06) * T
    tal = []
    for tip, d in tips:
        tal.append(tube([tuple(tip - d * 0.02 + A(0, 0.02, 0)), tuple(tip + d * tl * 0.7 + A(0, 0.0, 0)), tuple(tip + d * tl * 0.9 + A(0, -tl * 0.65, 0))],
                        [tr_ * 0.72, tr_ * 0.45, tr_ * 0.1], k=0.01))
    H.mpiece("Talons#", "Foot#", unite(tal), col="claw", mat="hard", tris=300, res=80, role="claw", pri=1.8, ao=False)

    # ------------------------------------------------------------------ rig, sockets, motion
    tip_w = b0 + beak_tip(bk, BLn, BD)
    H.socket("mouth", tuple(tip_w), "Jaw")
    H.socket("head", h(0, 1.0, 0), "Head")
    height = BY + 0.6
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": ["Tail"], "neck": "Neck",
                  "wings": [{"shoulder": "Shoulder" + s, "elbow": "Elbow" + s, "wrist": "Wrist" + s} for s in "RL"]})
    wings = [("ShoulderR", "ElbowR", "WristR", 1), ("ShoulderL", "ElbowL", "WristL", -1)]
    legs = [("HipR", "AnkleR", "FootR"), ("HipL", "AnkleL", "FootL")]
    MB.fly(H, wings, neck="Neck", head="Head", jaw="Jaw", tail="Tail", fans=[("TailFanR", 1), ("TailFanL", -1)], legs=legs,
           height=height, period=P["period"], amp=P["amp"], lift=P["lift"], attack=P["attack"], hover_pitch=P["hover_pitch"],
           buzz=P["buzz"], idle_amp=P["idle_amp"], fold=P["fold"], crest=["Crest"] if P["crest"] else ())
    return H


# ====================================================================================================== heroes
RAPTOR = dict(beak="hook", cere=True, brow=1.0, trousers=True, talon=0.55, toe=0.36, leg_r=0.085, eye_col="iris", attack="talon")


@hero("eagle", "birds")
def eagle():
    return _flyer("eagle", RAPTOR, body=1.0, girth=1.05, head=1.05, neck=0.32, beak_len=0.5, beak_depth=0.3, beak_w=0.22,
                  l1=1.0, l2=1.2, l3=1.6, chord=1.15, nprim=9, fingers=6, spread=1.3, tail="fan", tail_len=1.05, tail_w=0.32,
                  cols=dict(head="secondary", tail="secondary", belly="primary", thigh="primary"),
                  preview={"primary": "#4A3020", "secondary": "#F7F7F2", "beak": "#F2C02A", "iris": "#E8C030"})


@hero("hawk", "birds")
def hawk():
    return _flyer("hawk", RAPTOR, body=0.92, girth=0.95, head=0.95, neck=0.3, beak_len=0.4, beak_depth=0.26, beak_w=0.19,
                  l1=0.9, l2=1.05, l3=1.45, chord=1.0, nprim=9, fingers=5, spread=1.0, tail="fan", tail_len=1.0, tail_w=0.3,
                  pat="streaks", cols=dict(tail="accent", thigh="secondary"), period=0.75,
                  tail_pat=band_mask((0, 0, 1.0), (0, 0, 1), 6.0, width=0.2, depth=0.4),
                  preview={"primary": "#8A5A30", "secondary": "#F2E6D2", "accent": "#C85A2A", "beak": "#E8C040", "iris": "#C8702A"})


@hero("falcon", "birds")
def falcon():
    return _flyer("falcon", RAPTOR, body=0.88, girth=0.9, head=0.95, neck=0.25, beak_len=0.32, beak_depth=0.26, beak_w=0.19,
                  l1=0.85, l2=1.05, l3=1.75, chord=0.8, nprim=10, fingers=0, pointed=True, pwidth=0.26, fan_pow=0.6, sweep=0.38,
                  tail="square", tail_len=1.0, tail_w=0.24, tail_spread=0.3, mask="moustache", pat="bars",
                  cols=dict(head="primary", belly="secondary", thigh="secondary", mask="darker"), attack="dive", period=0.6, amp=0.85,
                  wing_pat_prim=band_mask((0, 0, 0), (1, 0, 0.3), 5.0, width=0.25, depth=0.2),
                  tail_pat=band_mask((0, 0, 1.0), (0, 0, 1), 7.0, width=0.25, depth=0.35),
                  preview={"primary": "#4A5462", "secondary": "#F2EEE6", "beak": "#E8C040", "iris": "#2A2020"})


@hero("vulture", "birds")
def vulture():
    return _flyer("vulture", {**RAPTOR, "trousers": False, "talon": 0.3, "brow": 0.6}, body=1.05, girth=1.1, head=0.78, neck=0.55,
                  beak_len=0.48, beak_depth=0.26, beak_w=0.2, l1=1.05, l2=1.3, l3=1.75, chord=1.25, nprim=9, fingers=7, spread=1.5,
                  tail="square", tail_len=0.85, tail_w=0.34, ruff="secondary", hover_pitch=0.15,
                  cols=dict(head="inner", ruff="light", belly="primary", leg="nail"), beak_col="horn", attack="peck", period=1.0,
                  preview={"primary": "#2A2420", "secondary": "#E8A0A0", "inner": "#D98A86", "light": "#8A7E74", "horn": "#E8DCC0"})


@hero("condor", "birds")
def condor():
    return _flyer("condor", {**RAPTOR, "trousers": False, "talon": 0.25, "brow": 0.5}, body=1.12, girth=1.15, head=0.75, neck=0.55,
                  beak_len=0.45, beak_depth=0.26, beak_w=0.2, l1=1.2, l2=1.45, l3=2.0, chord=1.25, nprim=9, fingers=7, spread=1.7,
                  tail="square", tail_len=0.85, tail_w=0.34, ruff=True, hover_pitch=0.1, tipdark=0.2,
                  cols=dict(head=[0.72, 0.42, 0.38], ruff="secondary", belly="primary", leg="nail", wing="secondary"), beak_col="horn",
                  attack="peck", period=1.1,
                  preview={"primary": "#1E1C1A", "secondary": "#F2F2F0", "horn": "#D8C8A8"})


@hero("osprey", "birds")
def osprey():
    return _flyer("osprey", RAPTOR, body=0.95, girth=0.92, head=0.95, neck=0.3, beak_len=0.42, beak_depth=0.26, beak_w=0.18,
                  l1=1.0, l2=1.2, l3=1.6, chord=0.95, nprim=9, fingers=4, spread=0.9, sweep=0.3, tail="square", tail_len=0.95,
                  tail_w=0.28, mask="stripe", attack="dive",
                  cols=dict(head="secondary", belly="secondary", thigh="secondary", mask="primary"), beak_col="darker",
                  tail_pat=band_mask((0, 0, 1.0), (0, 0, 1), 6.0, width=0.25, depth=0.3),
                  preview={"primary": "#5A4434", "secondary": "#F7F7F2", "iris": "#E8C030"})


@hero("owl", "birds")
def owl():
    return _flyer("owl", beak="hook", beak_len=0.22, beak_depth=0.2, beak_w=0.15, beak_col="horn", body=0.85, girth=1.2, head=1.45, neck=0.05,
                  eye=0.24, eye_fwd=True, eye_col="iris", tufts=0.75, disc=True, trousers=True, talon=0.45, toe=0.3, leg_r=0.1, zygo=True,
                  l1=0.9, l2=1.0, l3=1.25, chord=1.1, nprim=9, fingers=4, spread=0.7, tail="fan", tail_len=0.75, tail_w=0.32,
                  pat="streaks", hover_pitch=0.35, upright=0.35, period=0.9, foot_col="secondary",
                  cols=dict(face="secondary", thigh="secondary", leg="secondary"),
                  wing_pat_prim=band_mask((0, 0, 0), (1, 0, 0.25), 5.0, width=0.3, depth=0.25),
                  preview={"primary": "#8A6A4A", "secondary": "#F2E6D2", "horn": "#3A3530", "iris": "#F2B02A"})


@hero("barn owl", "birds")
def barn_owl():
    return _flyer("barn owl", beak="hook", beak_len=0.2, beak_depth=0.17, beak_w=0.13, beak_col="nail", body=0.85, girth=1.05, head=1.35, neck=0.1,
                  eye=0.2, eye_fwd=True, eye_col="dark", disc="heart", trousers=True, talon=0.4, toe=0.3, leg_r=0.08, leg=1.05, zygo=True,
                  l1=1.0, l2=1.1, l3=1.35, chord=1.05, nprim=9, fingers=3, spread=0.6, tail="square", tail_len=0.7, tail_w=0.3,
                  pat="flecks", hover_pitch=0.35, upright=0.3, period=0.95, tipdark=0.3,
                  cols=dict(face="secondary", belly="secondary", thigh="secondary", leg="secondary", flight="light"),
                  preview={"primary": "#E8C890", "secondary": "#FFFFFF", "light": "#F0DDB8", "nail": "#E8D8C8"})


@hero("snowy owl", "birds")
def snowy_owl():
    return _flyer("snowy owl", beak="hook", beak_len=0.2, beak_depth=0.18, beak_w=0.14, beak_col="darker", body=0.9, girth=1.3, head=1.4, neck=0.05,
                  eye=0.22, eye_fwd=True, eye_col="iris", disc=True, trousers=True, talon=0.4, toe=0.3, leg_r=0.12, zygo=True,
                  l1=0.95, l2=1.05, l3=1.3, chord=1.1, nprim=9, fingers=4, spread=0.7, tail="fan", tail_len=0.75, tail_w=0.32,
                  pat="spots", hover_pitch=0.35, upright=0.35, period=0.95, tipdark=0.1,
                  cols=dict(face="primary", belly="primary", thigh="primary", leg="primary", flight="primary"),
                  preview={"primary": "#F7F7F4", "secondary": "#2A2A2A", "darker": "#2A2A2A", "iris": "#F2D02A"})


PARROT = dict(beak="parrot", beak_col="horn", zygo=True, toe=0.28, talon=0.2, leg_r=0.07, leg=0.75, foot_col="nail", eye=0.17,
              eye_col="dark", attack="peck", brow=0.0)


@hero("parrot", "birds")
def parrot():
    return _flyer("parrot", PARROT, body=0.85, girth=0.95, head=1.25, neck=0.2, beak_len=0.3, beak_depth=0.26, beak_w=0.2,
                  l1=0.8, l2=0.95, l3=1.3, chord=0.85, nprim=9, fingers=0, pointed=True, fan_pow=0.75, tail="long", tail_len=1.5,
                  tail_w=0.22, tail_spread=0.35, cols=dict(belly="primary", flight="secondary", head="primary", leg="nail"), tipdark=0.2,
                  preview={"primary": "#2AB04A", "secondary": "#E8301E", "horn": "#E8E0D0", "nail": "#8A8A8A"})


@hero("macaw", "birds")
def macaw():
    return _flyer("macaw", PARROT, body=0.95, girth=0.95, head=1.25, neck=0.22, beak_len=0.38, beak_depth=0.32, beak_w=0.24,
                  l1=0.9, l2=1.1, l3=1.55, chord=0.9, nprim=9, pointed=True, fan_pow=0.75, tail="long", tail_len=2.6, tail_w=0.22,
                  tail_spread=0.25, ntail=4, cols=dict(belly="primary", flight="secondary", head="primary", wing="gold", leg="nail"),
                  tipdark=0.15,
                  preview={"primary": "#E8201E", "secondary": "#2A6AD8", "gold": "#F2C82A", "horn": "#E8E0D0", "nail": "#6A6A6A"})


@hero("cockatoo", "birds")
def cockatoo():
    return _flyer("cockatoo", {**PARROT, "beak_col": "darker"}, body=0.9, girth=1.0, head=1.3, neck=0.22, beak_len=0.32,
                  beak_depth=0.28, beak_w=0.22, l1=0.85, l2=1.0, l3=1.35, chord=0.95, nprim=9, fingers=3, spread=0.6, tail="fan",
                  tail_len=1.1, tail_w=0.28, crest="cockatoo", tipdark=0.05,
                  cols=dict(belly="primary", flight="primary", head="primary", crest="secondary", leg="dark"),
                  preview={"primary": "#F7F7F2", "secondary": "#F2D82A", "darker": "#2A2A2E", "dark": "#5A5A60"})


@hero("toucan", "birds")
def toucan():
    return _flyer("toucan", beak="toucan", beak_col="secondary", beak_len=1.3, beak_depth=0.5, beak_w=0.26, body=0.85, girth=0.95,
                  head=1.05, neck=0.25, eye=0.17, eye_col="iris", zygo=True, toe=0.28, talon=0.15, leg_r=0.07, leg=0.75,
                  l1=0.7, l2=0.8, l3=0.95, chord=0.85, nprim=8, fingers=0, tail="square", tail_len=1.0, tail_w=0.28, attack="peck",
                  cols=dict(belly="white", head="primary", leg=[0.35, 0.5, 0.75]), tipdark=0.0, period=0.65,
                  preview={"primary": "#1E1E1E", "secondary": "#F2A01E", "white": "#F7F2E0", "iris": "#5AC85A"})


@hero("hornbill", "birds")
def hornbill():
    return _flyer("hornbill", beak="decurve", beak_col="secondary", beak_len=1.0, beak_depth=0.42, beak_w=0.22, casque=True, body=1.0,
                  girth=1.0, head=1.0, neck=0.4, eye=0.15, eye_col="iris", toe=0.3, talon=0.15, leg=0.8, l1=1.0, l2=1.1, l3=1.35,
                  chord=1.05, nprim=9, fingers=4, spread=0.8, tail="long", tail_len=1.7, tail_w=0.3, attack="peck",
                  cols=dict(belly="white", leg="dark", tail="white"), tipdark=0.0,
                  preview={"primary": "#1E1E1E", "secondary": "#F2C02A", "white": "#F2F2EE", "dark": "#3A3A3A"})


SONG = dict(beak="cone", beak_col="beak", eye=0.2, eye_col="dark", leg=0.7, leg_r=0.05, toe=0.3, talon=0.15, attack="peck",
            body=0.8, girth=1.0, head=1.25, neck=0.12, l1=0.72, l2=0.85, l3=1.05, chord=0.8, nprim=9, fingers=0, pointed=True,
            fan_pow=0.75, tail="square", tail_len=0.95, tail_w=0.22, tail_spread=0.35, period=0.45, amp=0.9, tipdark=0.3)


@hero("bird", "birds")
def bird():
    return _flyer("bird", {**SONG, "beak_len": 0.3, "beak_depth": 0.18, "beak_w": 0.15}, cols=dict(belly="secondary", leg="dark"),
                  preview={"primary": "#4A8AC8", "secondary": "#F2C84A", "beak": "#E89A2A", "dark": "#5A4A40"})


@hero("sparrow", "birds")
def sparrow():
    return _flyer("sparrow", {**SONG, "beak_len": 0.26, "beak_depth": 0.2, "beak_w": 0.17}, beak_col="darker", pat="streaks",
                  cols=dict(belly="secondary", head="dark", throat="black", leg="nail", wing="primary", flight="dark"),
                  wing_pat_prim=band_mask((0, 0, 0), (1, 0, 0.2), 6.0, width=0.2, depth=0.25),
                  preview={"primary": "#8A6440", "secondary": "#D8C4A8", "dark": "#6A6A6A", "darker": "#3A3430", "nail": "#C8A890"})


@hero("robin", "birds")
def robin():
    return _flyer("robin", {**SONG, "beak_len": 0.3, "beak_depth": 0.15, "beak_w": 0.13, "beak": "dagger"}, girth=1.15, beak_col="gold",
                  cols=dict(belly="secondary", head="primary", leg="nail", flight="dark"),
                  preview={"primary": "#6E5A4A", "secondary": "#E8601E", "gold": "#E8B040", "dark": "#4A3E34", "nail": "#9A7A60"})


@hero("cardinal", "birds")
def cardinal():
    return _flyer("cardinal", {**SONG, "beak_len": 0.3, "beak_depth": 0.26, "beak_w": 0.22}, beak_col="red", crest="pointed", mask=True,
                  cols=dict(belly="primary", crest="primary", mask="secondary", flight="dark", leg="nail"),
                  preview={"primary": "#D8201E", "secondary": "#1E1E1E", "red": "#F2683A", "dark": "#8A1A16", "nail": "#B08070"})


@hero("blue jay", "birds")
def blue_jay():
    return _flyer("blue jay", {**SONG, "beak": "crow", "beak_len": 0.36, "beak_depth": 0.18, "beak_w": 0.15}, beak_col="black", crest="pointed",
                  body=0.9, tail_len=1.25, cols=dict(belly="secondary", crest="primary", leg="black"),
                  wing_pat_prim=band_mask((0, 0, 0), (1, 0, 0.2), 7.0, width=0.2, depth=0.5),
                  tail_pat=band_mask((0, 0, 1.0), (0, 0, 1), 8.0, width=0.18, depth=0.45),
                  preview={"primary": "#3A6AC8", "secondary": "#F2F2F2", "black": "#1E1E22"})


@hero("bluebird", "birds")
def bluebird():
    return _flyer("bluebird", {**SONG, "beak": "dagger", "beak_len": 0.26, "beak_depth": 0.14, "beak_w": 0.12}, girth=1.12, beak_col="black",
                  cols=dict(belly="secondary", leg="black"), tipdark=0.2,
                  preview={"primary": "#3A6AD8", "secondary": "#E87A3A", "black": "#2A2A30"})


@hero("finch", "birds")
def finch():
    return _flyer("finch", {**SONG, "beak_len": 0.26, "beak_depth": 0.22, "beak_w": 0.2}, beak_col="nail", girth=1.05, cap=True,
                  cols=dict(belly="primary", cap="secondary", wing="secondary", flight="secondary", tail="secondary", leg="nail"),
                  wing_pat_prim=band_mask((0, 0, 0), (1, 0, 0.2), 5.0, width=0.2, depth=0.0),
                  preview={"primary": "#F2C82A", "secondary": "#1E1E1E", "nail": "#E8C8A8"})


@hero("swallow", "birds")
def swallow():
    return _flyer("swallow", {**SONG, "beak": "short", "beak_len": 0.16, "beak_depth": 0.13, "beak_w": 0.16}, beak_col="black",
                  l1=0.7, l2=0.9, l3=1.55, chord=0.6, nprim=9, pwidth=0.24, fan_pow=0.55, sweep=0.55, tail="fork", tail_len=1.7,
                  tail_w=0.16, tail_spread=0.5, ntail=4, leg=0.5, attack="dive", period=0.42,
                  cols=dict(belly="secondary", throat="secondary", leg="black"),
                  preview={"primary": "#2A3A6A", "secondary": "#E8A07A", "black": "#1E1E22"})


@hero("crow", "birds")
def crow():
    return _flyer("crow", beak="crow", beak_col="black", beak_len=0.5, beak_depth=0.25, beak_w=0.2, body=0.95, girth=1.0, head=1.05,
                  neck=0.3, eye=0.15, eye_col="dark", leg=0.85, leg_r=0.065, toe=0.32, talon=0.25, l1=0.95, l2=1.1, l3=1.45,
                  chord=1.0, nprim=9, fingers=5, spread=0.9, tail="fan", tail_len=1.1, tail_w=0.28, attack="peck", period=0.7,
                  cols=dict(belly="primary", leg="black"), tipdark=0.15,
                  preview={"primary": "#1E1E24", "secondary": "#3A3A48", "black": "#121216"})


@hero("raven", "birds")
def raven():
    return _flyer("raven", beak="crow", beak_col="black", beak_len=0.62, beak_depth=0.3, beak_w=0.22, body=1.05, girth=1.05, head=1.1,
                  neck=0.35, eye=0.14, eye_col="dark", leg=0.9, leg_r=0.07, toe=0.34, talon=0.3, l1=1.05, l2=1.25, l3=1.6,
                  chord=1.05, nprim=9, fingers=6, spread=1.1, tail="wedge", tail_len=1.3, tail_w=0.3, attack="dive", period=0.75,
                  wattle=False, cols=dict(belly="primary", leg="black"), tipdark=0.1,
                  preview={"primary": "#1A1A20", "secondary": "#3A3A50", "black": "#101014"})


@hero("magpie", "birds")
def magpie():
    return _flyer("magpie", beak="crow", beak_col="black", beak_len=0.44, beak_depth=0.22, beak_w=0.18, body=0.88, girth=0.95, head=1.05,
                  neck=0.25, eye=0.15, eye_col="dark", leg=0.85, leg_r=0.055, toe=0.3, talon=0.2, l1=0.8, l2=0.95, l3=1.15,
                  chord=0.9, nprim=9, fingers=3, spread=0.6, tail="long", tail_len=2.4, tail_w=0.24, tail_spread=0.3, attack="peck",
                  cols=dict(belly="secondary", leg="black", wing="primary", rump="primary", flight="primary"),
                  wing_pat_prim=lambda Q: np.where(np.abs(Q[:, 0]) > 2.3, 1.0, 1.0), tipdark=0.0,
                  preview={"primary": "#1E1E24", "secondary": "#F2F2F2", "black": "#121216"})


@hero("pigeon", "birds")
def pigeon():
    return _flyer("pigeon", beak="short", beak_col="dark", beak_len=0.3, beak_depth=0.13, beak_w=0.12, body=0.95, girth=1.15, head=0.88,
                  neck=0.3, eye=0.16, eye_col="iris", leg=0.65, leg_r=0.06, toe=0.32, talon=0.12, l1=0.9, l2=1.05, l3=1.35,
                  chord=0.9, nprim=9, pointed=True, fan_pow=0.7, tail="square", tail_len=1.0, tail_w=0.28, attack="peck",
                  cols=dict(belly="primary", neck="secondary", leg=[0.85, 0.35, 0.4], flight="dark"), period=0.55, tipdark=0.4,
                  wing_pat_sec=band_mask((0, 0, 0), (0, 0, 1), 2.5, width=0.15, depth=0.45),
                  preview={"primary": "#8A8E98", "secondary": "#6AB09A", "dark": "#5A5E68", "iris": "#E87A2A"})


@hero("dove of peace", "birds")
def dove():
    return _flyer("dove of peace", beak="short", beak_col="nail", beak_len=0.26, beak_depth=0.12, beak_w=0.11, body=0.9, girth=1.05, head=0.9,
                  neck=0.28, eye=0.17, eye_col="dark", leg=0.6, leg_r=0.055, toe=0.3, talon=0.1, l1=0.95, l2=1.1, l3=1.45,
                  chord=0.95, nprim=9, fingers=2, spread=0.5, tail="fan", tail_len=1.1, tail_w=0.3, attack="peck", period=0.6,
                  cols=dict(belly="primary", leg=[0.9, 0.55, 0.6]), tipdark=0.05,
                  preview={"primary": "#FFFFFF", "secondary": "#E8E8EC", "nail": "#F2B8A0"})


@hero("seagull", "birds")
def seagull():
    return _flyer("seagull", beak="gull", beak_col="gold", beak_len=0.5, beak_depth=0.2, beak_w=0.15, body=1.0, girth=1.0, head=1.0,
                  neck=0.3, eye=0.14, eye_col="iris", leg=0.8, leg_r=0.06, toe=0.34, talon=0.05, l1=1.05, l2=1.25, l3=1.6,
                  chord=0.8, nprim=10, pointed=True, fan_pow=0.65, sweep=0.3, tail="square", tail_len=0.9, tail_w=0.28, attack="peck",
                  cols=dict(belly="primary", head="primary", wing="secondary", flight="secondary", leg=[0.95, 0.75, 0.55]),
                  wing_pat_prim=lambda Q: np.where(np.abs(Q[:, 0]) > 4.0, 0.25, 1.0), tipdark=0.1, period=0.8,
                  preview={"primary": "#F7F7F4", "secondary": "#8A9098", "gold": "#F2C83A", "iris": "#E8D88A"})


@hero("albatross", "birds")
def albatross():
    return _flyer("albatross", beak="gull", beak_col="nail", beak_len=0.62, beak_depth=0.22, beak_w=0.16, body=1.05, girth=1.0, head=0.95,
                  neck=0.3, eye=0.13, eye_col="dark", leg=0.75, leg_r=0.07, toe=0.4, talon=0.05, l1=1.3, l2=1.9, l3=2.1,
                  chord=0.7, nprim=10, nsec=13, pointed=True, fan_pow=0.6, sweep=0.2, tail="square", tail_len=0.75, tail_w=0.28,
                  attack="dive", amp=0.55, idle_amp=0.25, period=1.2,
                  cols=dict(belly="primary", head="primary", wing="secondary", flight="secondary", leg=[0.85, 0.75, 0.75]), tipdark=0.2,
                  preview={"primary": "#F7F7F2", "secondary": "#4E4E54", "nail": "#F0B8A8"})


@hero("pelican", "birds")
def pelican():
    return _flyer("pelican", beak="pouch", beak_col="gold", beak_len=1.6, beak_depth=0.24, beak_w=0.26, body=1.15, girth=1.15, head=0.9,
                  neck=0.6, eye=0.14, eye_col="iris", leg=0.75, leg_r=0.09, toe=0.42, talon=0.05, l1=1.1, l2=1.3, l3=1.6,
                  chord=1.05, nprim=9, fingers=4, spread=0.8, tail="square", tail_len=0.6, tail_w=0.3, attack="peck",
                  cols=dict(belly="primary", head="primary", flight="darker", leg=[0.9, 0.6, 0.3]), period=1.0, tipdark=0.0,
                  preview={"primary": "#F2F2EE", "secondary": "#F2A03A", "gold": "#F2A03A", "darker": "#2A2A2E", "iris": "#E8D07A"})


@hero("hummingbird", "birds")
def hummingbird():
    return _flyer("hummingbird", beak="needle", beak_col="black", beak_len=1.1, beak_depth=0.1, beak_w=0.09, body=0.72, girth=0.9,
                  head=1.0, neck=0.12, eye=0.2, eye_col="dark", leg=0.45, leg_r=0.035, toe=0.18, talon=0.1, l1=0.4, l2=0.55,
                  l3=1.35, chord=0.48, nprim=10, pointed=True, pwidth=0.26, fan_pow=0.5, sweep=0.15, tail="fan", tail_len=0.7,
                  tail_w=0.22, gait="buzz", buzz=6, period=0.5, amp=0.85, idle_amp=0.85, hover_pitch=0.65, upright=0.2,
                  attack="peck", fold=0.1, cols=dict(belly="primary", throat="secondary", leg="black", flight="dark"),
                  wattle=False, tipdark=0.0,
                  preview={"primary": "#2AA06A", "secondary": "#D8204A", "dark": "#2A3A34", "black": "#1E1E22"})


@hero("woodpecker", "birds")
def woodpecker():
    return _flyer("woodpecker", beak="dagger", beak_col="darker", beak_len=0.62, beak_depth=0.2, beak_w=0.15, body=0.92, girth=0.95,
                  head=1.05, neck=0.3, eye=0.15, eye_col="dark", leg=0.65, leg_r=0.06, toe=0.32, talon=0.3, zygo=True,
                  l1=0.8, l2=0.95, l3=1.2, chord=0.85, nprim=9, fingers=2, spread=0.4, tail="wedge", tail_len=1.0, tail_w=0.24,
                  cap=True, attack="peck", pat="spots", cols=dict(belly="white", cap="secondary", leg="dark", head="primary"),
                  wing_pat_prim=band_mask((0, 0, 0), (1, 0, 0.2), 7.0, width=0.18, depth=-1.2), tipdark=0.0,
                  preview={"primary": "#1E1E1E", "secondary": "#D8201E", "white": "#F2F2EE", "darker": "#3A3A40", "dark": "#4A4A50"})


@hero("kingfisher", "birds")
def kingfisher():
    return _flyer("kingfisher", beak="dagger", beak_col="black", beak_len=0.85, beak_depth=0.24, beak_w=0.18, body=0.78, girth=1.05,
                  head=1.3, neck=0.12, eye=0.16, eye_col="dark", leg=0.45, leg_r=0.05, toe=0.24, talon=0.1, l1=0.62, l2=0.75,
                  l3=0.95, chord=0.75, nprim=9, pointed=False, fingers=0, tail="square", tail_len=0.7, tail_w=0.22,
                  attack="dive", period=0.4, cols=dict(belly="secondary", leg=[0.9, 0.35, 0.25], flight="dark"), tipdark=0.0,
                  preview={"primary": "#2A8AD8", "secondary": "#E8701E", "dark": "#1E5A8A", "black": "#1E1E22"})
