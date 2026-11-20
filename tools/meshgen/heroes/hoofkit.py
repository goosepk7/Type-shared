"""Shared parametric builder for hoofed animals (h_equines, h_cervids, h_camelids, h_bovids, h_pachyderms).

One anatomy, many animals. Model space: +Y up, -Z front, feet on y = 0; the reference horse stands 3.2 studs at the
withers (s = 1). Everything is driven by a parameter dict (see BASE): body / leg / neck proportions, a head preset
(horse, deer, cow, pig, camel, sheep, goat, giraffe, moose, llama, rhino ...), ears, horns / antlers, mane, tail,
hooves (solid / cloven / pad), humps, wool, patterns, and tack (riding saddle, bridle, reins, stirrups; war barding;
pack / howdah handled in the pachyderm file).

Skeleton (all pivots identity-rotation, parented):
  Body (centre of mass) -> Loin (hindquarters: spine flex) -> HipB# -> StifleB# -> HockB# -> FetB#,  Tail1 -> Tail2 -> Tail3
  Body -> ShoulderF# -> KneeF# -> FetF#;  Body -> Neck -> Head -> Jaw, Ear#, (Trunk1..);  Body -> Stirrup#, Wing#1 -> Wing#2
Pieces overlap generously at every joint (ball ends) so nothing opens when a joint bends; the hindquarters ("Rump")
are a separate piece on Loin, slightly fuller than the Torso and blended in so the gallop can flex the spine.

NOTE: the hero cache hashes only the h_*.py file, so after editing this module rebuild with --force.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import _rotm
from kit import Hero, stripes, spots, gradient, combine
import motion_hoofed
import mountkit as MK

LEATHER = "leather"
BLANKET = [0.55, 0.13, 0.14]

# ------------------------------------------------------------------------------------------------ head presets
# Canonical head frame: origin at the poll (Head bone), muzzle toward -Z, horizontal; scaled by hs.
HEADS = {
    "horse": dict(
        cran=(0.27, 0.27, 0.31, -0.02, -0.15), face=(0.2, 0.21, 0.42, -0.07, -0.6), muz=(0.165, 0.19, 0.2, -0.19, -0.98),
        jowl=(0.13, 0.24, 0.25, 0.11, -0.25, -0.27), brow=(0.08, 0.2, 0.07, -0.38), eye=(0.225, 0.04, -0.43, 0.062),
        nost=(0.048, 0.092, -0.12, -1.13), ear=(0.115, 0.2, -0.04), chin=(0.1, 0.07, 0.15, -0.35, -0.95),
        bar=((0.1, -0.33, -0.32), (0.07, -0.37, -0.85), 0.06), pad=None, snout=None, mouth=(0, -0.3, -1.12),
        roman=0.0, dish=0.0, lip=0.0, length=1.18),
    "deer": dict(
        cran=(0.22, 0.22, 0.25, 0.0, -0.12), face=(0.15, 0.16, 0.38, -0.07, -0.52), muz=(0.105, 0.12, 0.15, -0.15, -0.84),
        jowl=(0.1, 0.17, 0.2, 0.09, -0.18, -0.24), brow=(0.07, 0.17, 0.08, -0.3), eye=(0.19, 0.05, -0.32, 0.06),
        nost=(0.03, 0.05, -0.11, -0.96), ear=(0.13, 0.18, -0.03), chin=(0.065, 0.05, 0.12, -0.25, -0.82),
        bar=((0.08, -0.24, -0.25), (0.05, -0.27, -0.76), 0.045), pad=(0.07, 0.06, 0.05, -0.11, -0.96), snout=None,
        mouth=(0, -0.22, -0.94), roman=0.0, dish=0.02, lip=0.0, length=1.0),
    "cow": dict(
        cran=(0.33, 0.3, 0.3, 0.0, -0.15), face=(0.27, 0.25, 0.36, -0.08, -0.52), muz=(0.24, 0.2, 0.2, -0.2, -0.84),
        jowl=(0.15, 0.24, 0.25, 0.14, -0.22, -0.3), brow=(0.09, 0.24, 0.08, -0.33), eye=(0.27, 0.05, -0.37, 0.065),
        nost=(0.05, 0.11, -0.15, -1.0), ear=(0.27, 0.06, -0.12), chin=(0.15, 0.07, 0.13, -0.36, -0.82),
        bar=((0.13, -0.32, -0.3), (0.1, -0.36, -0.75), 0.07), pad=(0.2, 0.15, 0.08, -0.17, -0.97), snout=None,
        mouth=(0, -0.32, -1.0), roman=0.0, dish=0.0, lip=0.0, length=1.0),
    "pig": dict(
        cran=(0.3, 0.28, 0.32, -0.02, -0.12), face=(0.22, 0.2, 0.33, -0.08, -0.48), muz=(0.15, 0.15, 0.2, -0.14, -0.75),
        jowl=(0.17, 0.22, 0.25, 0.13, -0.22, -0.22), brow=(0.07, 0.2, 0.07, -0.32), eye=(0.22, 0.06, -0.36, 0.05),
        nost=(0.03, 0.05, -0.13, -0.98), ear=(0.18, 0.2, -0.05), chin=(0.11, 0.06, 0.14, -0.3, -0.7),
        bar=((0.12, -0.28, -0.25), (0.08, -0.3, -0.65), 0.07), pad=(0.15, 0.13, 0.07, -0.13, -0.93), snout=None,
        mouth=(0, -0.27, -0.85), roman=0.0, dish=0.03, lip=0.0, length=0.98),
    "camel": dict(
        cran=(0.23, 0.22, 0.27, 0.0, -0.12), face=(0.16, 0.17, 0.4, -0.08, -0.55), muz=(0.15, 0.15, 0.2, -0.15, -0.9),
        jowl=(0.11, 0.17, 0.25, 0.09, -0.2, -0.28), brow=(0.085, 0.17, 0.08, -0.32), eye=(0.19, 0.05, -0.34, 0.06),
        nost=(0.03, 0.08, -0.07, -1.03), ear=(0.13, 0.17, -0.02), chin=(0.11, 0.08, 0.16, -0.32, -0.9),
        bar=((0.08, -0.26, -0.3), (0.07, -0.31, -0.82), 0.055), pad=None, snout=None, mouth=(0, -0.28, -1.05),
        roman=0.03, dish=0.0, lip=0.08, length=1.08),
    "sheep": dict(
        cran=(0.24, 0.25, 0.27, 0.0, -0.12), face=(0.16, 0.19, 0.3, -0.07, -0.45), muz=(0.12, 0.14, 0.15, -0.15, -0.7),
        jowl=(0.1, 0.17, 0.2, 0.09, -0.2, -0.22), brow=(0.06, 0.18, 0.08, -0.3), eye=(0.2, 0.06, -0.31, 0.058),
        nost=(0.03, 0.06, -0.11, -0.84), ear=(0.19, 0.12, -0.08), chin=(0.08, 0.05, 0.1, -0.27, -0.68),
        bar=((0.08, -0.25, -0.24), (0.06, -0.28, -0.6), 0.05), pad=None, snout=None, mouth=(0, -0.24, -0.82),
        roman=0.05, dish=0.0, lip=0.0, length=0.86),
    "goat": dict(
        cran=(0.22, 0.23, 0.26, 0.0, -0.12), face=(0.15, 0.17, 0.32, -0.06, -0.46), muz=(0.11, 0.13, 0.15, -0.15, -0.74),
        jowl=(0.09, 0.16, 0.2, 0.08, -0.18, -0.22), brow=(0.065, 0.17, 0.08, -0.3), eye=(0.19, 0.06, -0.31, 0.058),
        nost=(0.028, 0.055, -0.11, -0.87), ear=(0.16, 0.15, -0.06), chin=(0.07, 0.05, 0.1, -0.27, -0.72),
        bar=((0.07, -0.24, -0.24), (0.05, -0.28, -0.64), 0.045), pad=None, snout=None, mouth=(0, -0.24, -0.86),
        roman=0.0, dish=0.0, lip=0.0, length=0.9),
    "giraffe": dict(
        cran=(0.22, 0.22, 0.27, 0.0, -0.12), face=(0.15, 0.16, 0.4, -0.06, -0.55), muz=(0.13, 0.14, 0.18, -0.14, -0.9),
        jowl=(0.1, 0.16, 0.22, 0.09, -0.18, -0.27), brow=(0.08, 0.17, 0.08, -0.32), eye=(0.19, 0.05, -0.33, 0.065),
        nost=(0.028, 0.07, -0.08, -1.04), ear=(0.15, 0.13, -0.02), chin=(0.09, 0.06, 0.15, -0.28, -0.9),
        bar=((0.08, -0.24, -0.3), (0.06, -0.28, -0.82), 0.05), pad=None, snout=None, mouth=(0, -0.24, -1.05),
        roman=0.0, dish=0.0, lip=0.04, length=1.08),
    "moose": dict(
        cran=(0.27, 0.27, 0.3, 0.0, -0.13), face=(0.2, 0.22, 0.45, -0.06, -0.6), muz=(0.2, 0.24, 0.24, -0.15, -1.0),
        jowl=(0.12, 0.22, 0.25, 0.11, -0.24, -0.3), brow=(0.08, 0.2, 0.08, -0.36), eye=(0.21, 0.07, -0.37, 0.058),
        nost=(0.045, 0.12, -0.12, -1.18), ear=(0.17, 0.2, -0.05), chin=(0.11, 0.07, 0.15, -0.37, -0.95),
        bar=((0.1, -0.33, -0.32), (0.08, -0.37, -0.86), 0.06), pad=None, snout=None, mouth=(0, -0.38, -1.1),
        roman=0.08, dish=0.0, lip=0.12, length=1.22),
}

EARS = {  # length, width, outward tilt (deg), backward tilt (deg), cup
    "horse": (0.3, 0.085, 12, 8, 1.0), "pony": (0.24, 0.085, 14, 8, 1.0), "donkey": (0.62, 0.13, 22, 14, 1.0),
    "mule": (0.48, 0.115, 18, 10, 1.0), "zebra": (0.34, 0.11, 14, 8, 1.0), "deer": (0.36, 0.14, 48, 12, 1.0),
    "cow": (0.27, 0.12, 95, 15, 1.0), "pig": (0.38, 0.19, 40, -38, 0.6), "camel": (0.16, 0.08, 30, 20, 1.0),
    "llama": (0.38, 0.08, 6, 4, 1.0), "sheep": (0.23, 0.08, 100, 25, 0.8), "goat": (0.27, 0.085, 80, 20, 0.8),
    "giraffe": (0.26, 0.09, 70, 10, 1.0), "moose": (0.36, 0.14, 50, 10, 1.0), "lop": (0.42, 0.15, 125, -25, 0.5),
}


def _rot(deg_x=0.0, deg_y=0.0, deg_z=0.0):
    return _rotm(deg_x, deg_y, deg_z)


class Bounded(SDF):
    """Speed wrapper: on the first big query, find the shape's bounding box with a coarse 36^3 pass over the
    query's extent, then evaluate the real SDF only inside that (padded) box and return the box distance outside.
    The build samples every piece over the whole hero's bounds, so this skips most of the work."""

    def __init__(self, inner):
        self.inner = inner
        self.box = None
        super().__init__(self._eval)

    def _find(self, p):
        lo, hi = p.min(0), p.max(0)
        n = 36
        ax = [np.linspace(lo[i], hi[i], n) for i in range(3)]
        g = np.stack(np.meshgrid(*ax, indexing="ij"), -1).reshape(-1, 3)
        d = self.inner(g)
        step = (hi - lo) / (n - 1)
        hd = float(np.linalg.norm(step)) * 0.5
        hit = g[d < hd * 1.6]
        if len(hit) == 0:
            self.box = (lo, hi)
            return
        pad = step * 2.5
        self.box = (hit.min(0) - pad, hit.max(0) + pad)

    def _eval(self, p):
        if self.box is None:
            if len(p) < 50000:
                return self.inner(p)
            self._find(p)
        lo, hi = self.box
        c = (lo + hi) / 2
        h = (hi - lo) / 2
        q = np.abs(p - c) - h
        db = np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0)
        m = db < 0
        out = np.maximum(db, 1e-3) + float(h.min()) * 0.0
        if m.any():
            out = out.copy()
            out[m] = self.inner(p[m])
        return out


def finalize(H):
    """Wrap every sculpted piece in a Bounded SDF and pick a sampling resolution from its triangle budget."""
    for p in H.parts:
        if p["kind"] != "piece":
            continue
        if not isinstance(p["sdf"], Bounded):
            p["sdf"] = Bounded(p["sdf"])
        if p["res"] == 112:
            t = p["tris"]
            p["res"] = 72 if t <= 340 else 84 if t <= 700 else 96 if t <= 1300 else 112


def surf(sd, origin, direction, lo=0.0, hi=4.0, n=40):
    """Distance along `direction` from `origin` to the sdf's zero crossing (bisection; origin inside)."""
    o = np.asarray(origin, float)
    d = np.asarray(direction, float)
    d = d / np.linalg.norm(d)
    a, b = lo, hi
    for _ in range(n):
        m = 0.5 * (a + b)
        if sd(np.array([o + d * m]))[0] < 0:
            a = m
        else:
            b = m
    return 0.5 * (a + b)


def chain(pts, r0, r1, k=0.03, ridges=0.0):
    """Smooth chain of round cones through pts, radius tapering r0 -> r1 (optionally ringed)."""
    pts = [np.asarray(p, float) for p in pts]
    n = len(pts) - 1
    s = None
    for i in range(n):
        ra = r0 + (r1 - r0) * i / n
        rb = r0 + (r1 - r0) * (i + 1) / n
        if ridges:
            ra *= 1 + ridges * (i % 2)
        seg = round_cone(tuple(pts[i]), tuple(pts[i + 1]), ra, rb)
        s = seg if s is None else s.su(seg, k)
    return s


def curve(fn, n):
    return [fn(i / n) for i in range(n + 1)]


def voronoi_net(cells, line=0.18, depth=0.55, seed=0, region=None):
    """Giraffe-style patches: dark polygons separated by light lines (F2 - F1 cellular distance)."""
    rng = np.random.default_rng(seed)
    jit = rng.uniform(-0.38, 0.38, (64, 3))

    def f(P):
        g = P / cells
        c = np.floor(g)
        d1 = np.full(len(P), 9.0)
        d2 = np.full(len(P), 9.0)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    cc = c + (dx, dy, dz)
                    h = (np.abs(cc[:, 0] * 73856093 + cc[:, 1] * 19349663 + cc[:, 2] * 83492791).astype(np.int64)) % 64
                    d = np.linalg.norm(g - (cc + 0.5 + jit[h]), axis=1)
                    nd2 = np.where(d < d1, d1, np.minimum(d2, d))
                    d1 = np.minimum(d1, d)
                    d2 = nd2
        e = d2 - d1
        v = np.clip((e - line) / (line * 0.6), 0, 1)
        m = 1 - depth * v
        if region is not None:
            m = 1 - (1 - m) * np.clip(region(P), 0, 1)
        return m

    return f


def patches(cells, radius, depth=0.9, seed=0, region=None):
    """Big irregular patches (cow / pinto / paint): two overlapping spot lattices."""
    a = spots(cells, radius, depth=depth, seed=seed)
    b = spots(cells * 1.37, radius * 1.1, depth=depth, seed=seed + 7)

    def f(P):
        m = np.minimum(a(P), b(P))
        if region is not None:
            m = 1 - (1 - m) * np.clip(region(P), 0, 1)
        return m

    return f


def light_spots(cells, radius, depth=0.4, seed=0, region=None):
    """Pale spots on a darkened coat (fawn, axis deer): everything is darkened by `depth` except the spots."""
    sp = spots(cells, radius, depth=1.0, seed=seed)

    def f(P):
        v = 1 - sp(P)              # 1 inside a spot
        w = np.ones(len(P)) if region is None else np.clip(region(P), 0, 1)
        return 1 - depth * w * (1 - v)

    return f


def band(axis, lo, hi, depth=0.6, soft=0.05, region=None):
    """A dark band where lo < P[axis] < hi (flank stripe, socks, saddle patch)."""
    def f(P):
        x = P[:, axis]
        v = np.clip((x - lo) / soft, 0, 1) * np.clip((hi - x) / soft, 0, 1)
        if region is not None:
            v = v * np.clip(region(P), 0, 1)
        return 1 - depth * v

    return f


BASE = dict(
    s=1.0, leg=1.0, depth=1.0, body=0.92, girth=1.0, lt=1.0, hoof_r=1.0,
    slope=0.0,            # croup lower than withers (giraffe, hyena-like)
    withers=0.25,         # withers ridge height
    belly=0.0,            # extra belly sag (cows, pregnant mares)
    hump=(),              # [(z, height, radius_z)] dorsal humps (camel, bison)
    neck_len=1.0, neck_ang=52.0, neck_thick=1.0, neck_flat=0.72, arch=0.12, dewlap=0.0,
    head="horse", hs=1.0, head_ang=48.0, head_over=None,
    ears="horse", ear_scale=1.0,
    horns=None, horn_scale=1.0,
    mane=None, forelock=False, beard=0.0, bell=0.0,
    tail="horse", tail_len=1.0,
    hoof="solid", feather=0.0,
    wool=0.0, shaggy=0.0, skirt=0.0,
    pattern=None, shade=0.88, legs_dark=0.0,
    tack=None,            # None | "riding" | "barding" | "bridle"
    wings=None,           # None | "spread"
    horn_unicorn=False,
    eye_col=[0.2, 0.12, 0.07], pupil="round", eye_glow=False,
    hoof_col="hoof", mane_col="secondary", face_col=None, leg_col=None, horn_col="horn",
    gait="gallop", attack="rear", stride=1.0, fold=1.0, heavy=0.0, move_len=None, flap=1.0,
    tags=("ungulate",), plan="Quadruped", rig_gait="trot", preview={},
    udder=False, tusks=None, tris=1.0, bit=True, blanket=True, extra=None, head_mod=None,
    tuck=0.0, knee_h=0.545, stifle_h=1.0, stifle_fwd=1.0, hock_h=0.62, folds=(), rump_col="primary",
    # ---- mount overhaul (all off by default: bovids / camelids / cervids are unchanged)
    hq=False,             # hero-quality mane, tail, fitted riding tack (saddle pad, saddle, fenders, bags), hoof detail
    mount=None,           # {"length": studs} -> seat + enter sockets and the mount table (length, stride, walkStride)
    walk_clip=False,      # also author a "Walk" clip (four-beat walk) next to Move
    wing_fold=False,      # feathered wings fold along the flanks on the ground; adds "Fly" (flap) and "Glide"
    bags=True,            # hq riding tack: bedroll + saddlebags behind the cantle
)


def ungulate(hid, **kw):
    P = dict(BASE)
    P.update(kw)
    s = P["s"]
    G, D, BL, LG = P["girth"], P["depth"], P["body"], P["leg"]
    LT = P["lt"]
    TR = P["tris"]
    H = Hero(hid, plan=P["plan"], gait=P["rig_gait"], tags=list(P["tags"]))
    H.preview = P["preview"]

    def v(x, y, z):
        return (x * s, y * s, z * s)

    def V(x, y, z):
        return np.array(v(x, y, z))

    def T(n):
        return int(max(150, min(2600, n * TR)))

    yb = 1.8 * LG                     # belly line / elbow height
    Dp = 1.35 * D                     # body depth
    top = yb + Dp                     # withers / back line
    cy = yb + Dp / 2
    sl = P["slope"]
    zc = 0.5 * BL                     # torso / rump split
    H.body(v(0, cy, -0.2 * BL))

    # ------------------------------------------------------------------ patterns
    def back_shade(Q):
        t = np.clip((Q[:, 1] / s - (yb + 0.1 * Dp)) / (Dp * 0.9), 0, 1)
        return 1.0 - (1.0 - P["shade"]) * t

    pat = P["pattern"]
    if callable(pat):
        body_pat = pat
    else:
        body_pat = None

    def legshade(Q):
        if not P["legs_dark"]:
            return np.ones(len(Q))
        t = np.clip((0.62 * yb * s - Q[:, 1]) / (0.35 * yb * s), 0, 1)
        return 1.0 - P["legs_dark"] * t

    def skin(extra=None):
        return combine(back_shade, body_pat, extra)

    def fluff(sd, amp=1.0, freq=5.0, seed=0):
        if P["wool"] > 0:
            return sd.noise(P["wool"] * amp * s, freq * 2.2 / s, seed).noise(P["wool"] * amp * 0.5 * s, freq * 5 / s, seed + 1)
        if P["shaggy"] > 0:
            return sd.noise(P["shaggy"] * amp * s, freq * 1.6 / s, seed)
        return sd

    # ------------------------------------------------------------------ body
    core = ellipsoid(0.6 * G * s, Dp / 2 * s, 1.3 * BL * s, v(0, cy, -0.25 * BL))
    chest = ellipsoid(0.52 * G * s, 0.44 * Dp * s, 0.55 * s, v(0, cy - 0.04 * Dp, -1.32 * BL))
    brisket = ellipsoid(0.36 * G * s, 0.3 * Dp * s, 0.42 * s, v(0, yb + 0.22 * Dp, -1.22 * BL))
    wit = ellipsoid(0.27 * G * s, 0.3 * s, 0.75 * BL * s, v(0, top - 0.3 + P["withers"] * 0.6, -0.95 * BL))
    scap = ellipsoid(0.16 * G * s, 0.42 * Dp * s, 0.3 * s, (0, 0, 0)).rot(-28, 0, 0).at(*v(0.44 * G, cy + 0.08 * Dp, -1.05 * BL)).mirror_x()
    belly = ellipsoid(0.55 * G * s * (1 + 0.2 * P["belly"]), (0.36 * Dp + 0.12 * P["belly"]) * s, 0.85 * BL * s, v(0, yb + 0.4 * Dp - 0.12 * P["belly"], 0.0 * BL))
    loin = ellipsoid(0.46 * G * s, 0.32 * Dp * s, 0.8 * BL * s, v(0, top - 0.3 * Dp - 0.4 * sl, 0.45 * BL))
    croup = ellipsoid(0.55 * G * s, 0.42 * Dp * s, 0.66 * BL * s, v(0, top - 0.37 * Dp - sl, 1.2 * BL))
    haunch = ellipsoid(0.3 * G * s, 0.46 * Dp * s, 0.46 * BL * s, v(0.3 * G, cy - 0.02 * Dp - sl, 1.42 * BL)).mirror_x()
    hipb = sphere(0.13 * s * G, v(0.43 * G, top - 0.24 * Dp - 0.75 * sl, 0.82 * BL)).mirror_x()
    tailhead = ellipsoid(0.24 * G * s, 0.24 * Dp * s, 0.28 * s, v(0, top - 0.26 * Dp - sl, 1.72 * BL))
    body = core.su(chest, 0.3).su(brisket, 0.25).su(wit, 0.35).su(scap, 0.2).su(belly, 0.4).su(loin, 0.4)
    body = body.su(croup, 0.4).su(haunch, 0.3).su(hipb, 0.2).su(tailhead, 0.25)
    for (hz, hh, hr) in P["hump"]:
        hz_ = hz * BL
        yh = top - 0.15 + (0 if hz_ < zc else -sl)
        body = body.su(ellipsoid(0.42 * G * s * min(1.0, hr / 0.6 + 0.3), (hh + 0.15) * s, hr * s, v(0, yh, hz_)), 0.35)
    if P["udder"]:
        ud = ellipsoid(0.24 * s, 0.17 * s, 0.24 * s, v(0, yb + 0.02, 1.0 * BL))
        for x in (-0.08, 0.08):
            for z in (-0.08, 0.08):
                ud = ud.su(round_cone(v(x, yb - 0.05, 1.0 * BL + z), v(x * 1.15, yb - 0.24, 1.0 * BL + z * 1.1), 0.04 * s, 0.025 * s), 0.04)
        body = body.su(ud, 0.12)
    if P["tuck"]:
        # tucked-up flank: carve the underside behind the ribcage (deer, antelopes, greyhound-lean horses)
        tk = ellipsoid(1.2 * G * s, 0.42 * Dp * s * P["tuck"], 0.72 * BL * s, v(0, yb - 0.08 * Dp, 0.62 * BL))
        body = body.ss(tk, 0.25 * s)
    for fz in P["folds"]:
        slab = box(3 * s, 3 * s, 0.035 * s, v(0, 0, fz * BL))
        body = body.ss(body.shell(0.05 * s) & slab, 0.03 * s)
    body = fluff(body, 1.0, 4.5, 1)
    torso = body.round(-0.025 * s).si(half_space(2, 1, (zc + 0.35) * s), 0.15)
    rump = body.si(half_space(2, -1, (zc - 0.3) * s), 0.25)
    H.piece("Torso", "Body", torso, col="primary", tris=T(2300), res=128, pattern=skin(), role="body")
    H.bone("Loin", "Body", v(0, top - 0.35 * Dp - 0.3 * sl, zc))
    H.piece("Rump", "Loin", rump, col=P["rump_col"], tris=T(1700), res=120, pattern=skin(), role="body")

    # ------------------------------------------------------------------ legs
    xf = 0.36 * G
    xh = 0.37 * G
    zf = -1.1 * BL
    zh = 1.4 * BL
    yh_scale = (yb - 0.55 * sl) / yb    # hinds shorter when the back slopes
    ybh = yb * yh_scale
    hr = 0.135 * P["hoof_r"] * max(0.8, LT ** 0.85)
    style = P["hoof"]
    leg_col = P["leg_col"] or "primary"
    yfet = 0.19 * yb if style != "pad" else 0.15 * yb
    ycor = 0.12 * yb if style != "pad" else 0.0
    fS = V(xf + 0.06, yb + 0.45 * Dp, zf - 0.12)
    fE = V(xf + 0.04, yb + 0.02, zf + 0.06)
    fK = V(xf, P["knee_h"] * yb, zf)
    fF = V(xf, yfet, zf - 0.02)
    fC = V(xf, max(ycor, 0.001), zf - 0.09 * (style != "pad"))
    bH = V(xh + 0.05, top - 0.42 * Dp - sl, zh - 0.08)
    bS = V(xh + 0.02, P["stifle_h"] * ybh + 0.08, zh - 0.4 * P["stifle_fwd"])
    bK = V(xh, P["hock_h"] * ybh, zh + 0.12 * P["stifle_fwd"])
    bF = V(xh, yfet, zh + 0.03)
    bC = V(xh, max(ycor, 0.001), zh - 0.05 * (style != "pad"))
    H.mbone("ShoulderF#", "Body", tuple(fS))
    H.mbone("KneeF#", "ShoulderF#", tuple(fK))
    H.mbone("FetF#", "KneeF#", tuple(fF))
    H.mbone("HipB#", "Loin", tuple(bH))
    H.mbone("StifleB#", "HipB#", tuple(bS))
    H.mbone("HockB#", "StifleB#", tuple(bK))
    H.mbone("FetB#", "HockB#", tuple(bF))
    lt = LT * s

    up = round_cone(tuple(fS), tuple(fE), 0.27 * lt * 1.1, 0.21 * lt)
    up = up.su(round_cone(tuple(fE + V(0, 0.05, -0.03)), tuple(fK + V(0, 0.04, 0)), 0.2 * lt, 0.1 * lt), 0.12)
    up = up.su(ellipsoid(0.13 * lt, 0.3 * (fE[1] - fK[1]) / s * s, 0.15 * lt, tuple(fE + (fK - fE) * 0.28 + V(0.01, 0, -0.03))), 0.1)
    H.mpiece("UpperF#", "ShoulderF#", fluff(up, 0.7, 5, 2), col="primary", tris=T(650), role="limb", pattern=skin(legshade))
    kn = ellipsoid(0.115 * lt, 0.13 * lt, 0.115 * lt, tuple(fK))
    can = kn.su(round_cone(tuple(fK), tuple(fF), 0.082 * lt, 0.075 * lt), 0.06)
    can = can.su(capsule(tuple(fK + V(0, -0.08, 0.035 * LT)), tuple(fF + V(0, 0.1, 0.035 * LT)), 0.05 * lt), 0.04)
    can = can.su(ellipsoid(0.095 * lt, 0.1 * lt, 0.11 * lt, tuple(fF + V(0, 0, 0.02))), 0.05)
    H.mpiece("CannonF#", "KneeF#", can, col=leg_col, tris=T(420), role="limb", pattern=skin(legshade))

    def pastern(F, C):
        if style == "pad":
            foot = round_cone(tuple(F + V(0, 0.08, 0)), tuple(C + V(0, 0.14, -0.02)), 0.12 * lt, 0.15 * lt)
            foot = foot.su(cylinder(0.155 * lt, 0.1 * s).at(*(C + V(0, 0.1, -0.02))), 0.08)
            return foot & plane((0, -1, 0), 0.0)
        pa = round_cone(tuple(F), tuple(C + V(0, 0.03, 0)), 0.085 * lt, 0.08 * lt)
        if P["feather"]:
            fe = ellipsoid(0.105 * lt * (1 + 0.45 * P["feather"]), 0.17 * s, 0.115 * lt * (1 + 0.45 * P["feather"]), tuple(C + V(0, 0.12, 0.03)))
            fe = fe.su(round_cone(tuple(F + V(0, 0.05, 0.03)), tuple(C + V(0, 0.07, 0.08)), 0.09 * lt, 0.11 * lt * (1 + 0.4 * P["feather"])), 0.08)
            pa = pa.su(fe.noise(0.03 * s, 14 / s, 4), 0.06) & plane((0, -1, 0), -0.02 * s)
        return pa

    def hoof(C):
        if style == "pad":
            nails = None
            for a in (-40, 0, 40):
                ang = math.radians(a)
                c = C + V(math.sin(ang) * 0.145 * LT, 0.06, -math.cos(ang) * 0.145 * LT - 0.02)
                n_ = ellipsoid(0.055 * lt, 0.05 * s, 0.035 * lt, tuple(c))
                nails = n_ if nails is None else nails | n_
            return nails & plane((0, -1, 0), -0.003)
        hh = C[1]
        if style == "cloven":
            toe = None
            for sx in (1, -1):
                t = round_cone(tuple(C + V(sx * hr * 0.42, 0.0, 0.03)), tuple(C + V(sx * hr * 0.5, -hh / s + 0.04, -hr * 0.9)), hr * 0.42 * s, hr * 0.38 * s)
                toe = t if toe is None else toe | t
            dew = sphere(0.035 * s, tuple(C + V(0.06, 0.05, 0.12))) | sphere(0.035 * s, tuple(C + V(-0.06, 0.05, 0.12)))
            return (toe | dew) & plane((0, -1, 0), 0.0)
        h_ = round_cone(tuple(C + V(0, 0.0, 0.03)), tuple(np.array([C[0], 0.07 * s, C[2] - 0.06 * s])), hr * 0.8 * s, hr * s)
        return h_ & plane((0, -1, 0), 0.0)

    def leg_end(name, bone, F, C):
        H.mpiece(name.replace("Hoof", "Pastern"), bone, pastern(F, C), col=("secondary" if P["feather"] else leg_col), tris=T(300),
                 role="limb", pattern=None if P["feather"] else skin(legshade))
        H.mpiece(name, bone, hoof(C), col=("nail" if style == "pad" else P["hoof_col"]), mat="hard", tris=T(300), role="foot", pri=1.3)

    leg_end("HoofF#", "FetF#", fF, fC)

    th = round_cone(tuple(bH), tuple(bS), 0.3 * lt, 0.19 * lt)
    th = th.su(ellipsoid(0.2 * G * s, 0.45 * (bH[1] - bS[1]) / s * s, 0.34 * s, tuple((bH + bS) / 2 + V(-0.03, 0.0, 0.16))), 0.2)
    H.mpiece("Thigh#", "HipB#", fluff(th, 0.8, 5, 4), col="primary", tris=T(700), role="limb", pattern=skin(legshade))
    ga = round_cone(tuple(bS), tuple(bK), 0.2 * lt, 0.1 * lt)
    ga = ga.su(ellipsoid(0.12 * lt, 0.28 * (bS[1] - bK[1]) / s * s, 0.14 * lt, tuple(bS + (bK - bS) * 0.38 + V(0, 0, 0.07))), 0.1)
    H.mpiece("Gaskin#", "StifleB#", fluff(ga, 0.6, 6, 5), col="primary", tris=T(480), role="limb", pattern=skin(legshade))
    hk = ellipsoid(0.1 * lt, 0.13 * lt, 0.12 * lt, tuple(bK)).su(sphere(0.075 * lt, tuple(bK + V(0, 0.06, 0.1 * LT))), 0.05)
    hk = hk.su(round_cone(tuple(bK), tuple(bF), 0.085 * lt, 0.077 * lt), 0.06)
    hk = hk.su(ellipsoid(0.095 * lt, 0.1 * lt, 0.11 * lt, tuple(bF + V(0, 0, 0.02))), 0.05)
    H.mpiece("CannonB#", "HockB#", hk, col=leg_col, tris=T(420), role="limb", pattern=skin(legshade))
    leg_end("HoofB#", "FetB#", bF, bC)

    # ------------------------------------------------------------------ neck
    na = math.radians(P["neck_ang"])
    NL = 1.95 * P["neck_len"]
    NT = P["neck_thick"]
    nb = V(0, cy + 0.05 * Dp, -1.22 * BL)
    dn = np.array([0, math.sin(na), -math.cos(na)])
    nperp = np.array([0, math.cos(na), math.sin(na)])
    poll = nb + dn * NL * s
    nmid = nb + dn * NL * s * 0.5 + nperp * P["arch"] * s
    r0, r1, r2 = 0.6 * NT * s * min(1.0, D ** 0.5), 0.38 * NT * s, 0.25 * NT * s * P["hs"]
    neck_c = [nb - dn * 0.15 * s, nmid, poll - dn * 0.05 * s - nperp * 0.06 * s]
    neck = tube([tuple(p) for p in neck_c], [r0, r1, r2], k=0.25)
    neck = neck.su(capsule(tuple(nb + nperp * r0 * 0.55 - dn * 0.05 * s), tuple(nmid + nperp * r1 * 0.55), r1 * 0.6), 0.25)  # crest
    if P["dewlap"]:
        dl = ellipsoid(0.12 * s, 0.35 * P["dewlap"] * s, 0.4 * s, tuple(nb + dn * 0.25 * s - nperp * (r0 + 0.1 * P["dewlap"]) * 1.0))
        neck = neck.su(dl, 0.2)
    flat = P["neck_flat"]
    neck = neck.scale3(flat, 1.0, 1.0)
    neck = fluff(neck, 0.9, 5, 7)
    H.bone("Neck", "Body", tuple(nb + dn * 0.2 * s))
    H.piece("NeckP", "Neck", neck, col="primary", tris=T(1300), role="neck", pattern=skin())

    def neck_pt(t):
        """Point on the neck centreline (t: 0 base .. 1 poll) and radius there."""
        if t < 0.5:
            a, b, u = neck_c[0], neck_c[1], t / 0.5
            r = r0 + (r1 - r0) * u
        else:
            a, b, u = neck_c[1], neck_c[2], (t - 0.5) / 0.5
            r = r1 + (r2 - r1) * u
        return a + (b - a) * u, r

    # ------------------------------------------------------------------ head
    hs = P["hs"] * s
    HP = dict(HEADS[P["head"]])
    if P["head_over"]:
        HP.update(P["head_over"])
    ha = P["head_ang"]
    Rh = _rot(-ha, 0, 0)
    H.bone("Head", "Neck", tuple(poll))

    def hp(x, y, z):
        return poll + Rh @ (np.array([x, y, z]) * hs)

    def hx(sd):
        return sd.rot(-ha, 0, 0).at(*poll)

    def L(x, y, z):
        return (x * hs, y * hs, z * hs)

    c = HP["cran"]
    hc = ellipsoid(c[0] * hs, c[1] * hs, c[2] * hs, L(0, c[3], c[4]))
    f = HP["face"]
    face = ellipsoid(f[0] * hs, f[1] * hs, f[2] * hs, L(0, f[3], f[4]))
    m = HP["muz"]
    muz = ellipsoid(m[0] * hs, m[1] * hs, m[2] * hs, L(0, m[3], m[4]))
    j = HP["jowl"]
    jowl = ellipsoid(j[0] * hs, j[1] * hs, j[2] * hs, L(j[3], j[4], j[5])).mirror_x()
    head = hc.su(face, 0.2).su(muz, 0.15).su(jowl, 0.15)
    head = head.su(round_cone(L(0, c[3] + c[1] * 0.55, c[4] - 0.1), L(0, f[3] + f[1] * 0.6 + HP["roman"], f[4] - 0.1), 0.09 * hs, 0.08 * hs), 0.15)  # forehead / nasal line
    if HP["dish"]:
        head = head.ss(sphere(0.12 * hs, L(0, f[3] + f[1] + 0.06, f[4] + 0.05)), 0.08)
    b_ = HP["brow"]
    head = head.su(sphere(b_[0] * hs, L(b_[1], b_[2], b_[3])).mirror_x(), 0.07)
    e = HP["eye"]
    head = head.ss(sphere(e[3] * 1.12 * hs, L(e[0] + 0.012, e[1], e[2])).mirror_x(), 0.03)
    n_ = HP["nost"]
    if HP["snout"] is None:
        head = head.su(ellipsoid(n_[0] * 1.6 * hs, n_[0] * 1.6 * hs, n_[0] * 1.6 * hs, L(n_[1] * 0.95, n_[2] + 0.01, n_[3] + 0.03)).mirror_x(), 0.05)
        head = head.ss(ellipsoid(n_[0] * 0.75 * hs, n_[0] * 1.15 * hs, n_[0] * 1.2 * hs, L(n_[1] * 1.05, n_[2], n_[3] - 0.02)).mirror_x(), 0.02)
    else:
        sn = HP["snout"]
        disc = cylinder(sn[0] * hs, sn[1] * 0.5 * hs, axis=2, rr=0.03 * hs).at(*L(0, sn[2], sn[3]))
        head = head.su(round_cone(L(0, sn[2] + 0.02, sn[3] + 0.32), L(0, sn[2], sn[3]), sn[0] * 0.9 * hs, sn[0] * 0.95 * hs), 0.08).su(disc, 0.03)
        head = head.ss(ellipsoid(0.03 * hs, 0.045 * hs, 0.05 * hs, L(0.05, sn[2], sn[3] - sn[1] * 0.5)).mirror_x(), 0.015)
    if HP["lip"]:
        head = head.su(ellipsoid((m[0] + 0.01) * hs, 0.07 * hs, 0.12 * hs, L(0, m[3] - m[1] * 0.6 - HP["lip"] * 0.5, m[4] - m[2] * 0.25)), 0.06)
    if P["head"] == "moose":
        head = head.su(ellipsoid(m[0] * 1.15 * hs, 0.1 * hs, 0.17 * hs, L(0, m[3] + 0.05, m[4] - 0.12)), 0.1)
    if P.get("head_mod"):
        head = P["head_mod"](head, L, hs, HP)
    head_can = head
    # ears are separate pieces; horns separate; jaw separate
    head_w = hx(fluff(head, 0.25, 9, 8)) if P["wool"] == 0 else hx(head)
    face_col = P["face_col"] or "primary"
    hpat = body_pat if (face_col == "primary" and P.get("head_pat", True)) else None
    if P["hq"] and face_col == "primary" and P.get("muzzle_dark", 0.35):
        _mz = poll + _rot(-P["head_ang"], 0, 0) @ (np.array([0.0, HP["muz"][3], HP["muz"][4] - 0.05]) * P["hs"] * s)
        _mr = 0.42 * P["hs"] * s
        _md = P.get("muzzle_dark", 0.35)
        hpat = combine(hpat, lambda Q: 1 - _md * np.clip(1 - np.linalg.norm(Q - _mz, axis=1) / _mr, 0, 1) ** 0.7)
    H.piece("HeadP", "Head", head_w, col=face_col, tris=T(2300), res=136, role="head", pattern=hpat)
    if HP["pad"]:
        pd = HP["pad"]
        pad = ellipsoid(pd[0] * hs, pd[1] * hs, pd[2] * hs, L(0, pd[3], pd[4]))
        pad = pad.ss(ellipsoid(0.025 * hs, 0.035 * hs, 0.04 * hs, L(pd[0] * 0.5, pd[3], pd[4] - pd[2] * 0.9)).mirror_x(), 0.01)
        H.piece("NosePad", "Head", hx(pad), col="nose", tris=T(260), role="nose", pri=1.6, ao=False)
    # jaw
    ch = HP["chin"]
    jb = HP["bar"]
    jaw = ellipsoid(ch[0] * hs, ch[1] * hs, ch[2] * hs, L(0, ch[3], ch[4]))
    jaw = jaw.su(capsule(L(*jb[0]), L(*jb[1]), jb[2] * hs).mirror_x(), 0.07)
    if P["bell"]:
        jaw = jaw.su(round_cone(L(0, ch[3] + 0.02, jb[0][2] - 0.05), L(0, ch[3] - 0.5 * P["bell"], jb[0][2] + 0.02), 0.08 * hs, 0.06 * hs).noise(0.015 * hs, 12 / hs, 5), 0.06)
    if P["beard"]:
        jaw = jaw.su(round_cone(L(0, ch[3] - 0.02, ch[4] + 0.08), L(0, ch[3] - 0.32 * P["beard"], ch[4] + 0.18), 0.07 * hs, 0.025 * hs).noise(0.012 * hs, 18 / hs, 3), 0.05)
    jpos = hp(0, jb[0][1] + 0.06, jb[0][2] + 0.05)
    H.bone("Jaw", "Head", tuple(jpos))
    H.piece("JawP", "Jaw", hx(jaw), col=face_col, tris=T(450), role="jaw", pri=1.4, pattern=hpat)
    mo = HP["mouth"]
    H.socket("mouth", tuple(hp(*mo)), "Jaw")
    H.socket("head", tuple(hp(0, c[3] + c[1] + 0.1, c[4])), "Head")
    # eyes
    ex, ey, ez, er = HP["eye"]
    ec = hp(ex, ey, ez)
    look = Rh @ np.array([0.85, 0.08, -0.55])
    r = er * hs
    H.mprim("Eye#", "Head", "Ball", (2 * r,) * 3, tuple(ec), col=P["eye_col"], mat="hard", pri=1.2, role="eye", glow=P["eye_glow"])
    d = look / np.linalg.norm(look)
    if P["pupil"]:
        pc = ec + d * r * 0.78
        ry = math.atan2(-d[0], -d[2])
        size = (r * 1.15, r * 0.42, r * 0.5) if P["pupil"] == "bar" else (r * 0.9, r * 0.9, r * 0.5)
        H.mprim("Pupil#", "Head", "Ellipsoid", size, tuple(pc), rot=(0, ry, 0), col="pupil", mat="hard", pri=1.3, role="pupil")
    sc = ec + d * r * 0.82 + Rh @ np.array([0, r * 0.38, -r * 0.1])
    H.mprim("Shine#", "Head", "Ball", (r * 0.36,) * 3, tuple(sc), col="shine", mat="hard", pri=2.6, role="shine")

    # ears
    if P["ears"]:
        el_, ew, eo, eb, cup = EARS[P["ears"]]
        el_ *= P["ear_scale"]
        ew *= P["ear_scale"] ** 0.7
        ear = ellipsoid(ew * hs, el_ * 0.5 * hs, ew * 0.42 * hs, L(0, el_ * 0.45, 0))
        ear = ear.su(sphere(ew * 0.55 * hs, L(0, 0.02, 0.0)), 0.05)
        if P["ears"] not in ("lop",):
            ear = ear & plane((0, 1, 0), el_ * 0.95 * hs)  # keep the tip
        ear = ear.ss(ellipsoid(ew * 0.72 * hs * cup, el_ * 0.42 * hs, ew * 0.3 * hs, L(0, el_ * 0.5, -ew * 0.3)), 0.02)
        if P["ears"] in ("horse", "pony", "zebra", "mule", "donkey", "llama"):
            # pointed, slightly in-curved tips
            ear = ear.su(round_cone(L(0, el_ * 0.6, 0), L(-0.01, el_ * 1.02, -0.01), ew * 0.45 * hs, 0.012 * hs), 0.04)
        ex_, ey_, ez_ = HP["ear"]
        ear = ear.rot(-eb, 0, -eo).at(*L(ex_, ey_, ez_))
        eb_w = hp(ex_, ey_, ez_)
        H.mbone("Ear#", "Head", tuple(eb_w))
        H.mpiece("Ear#", "Ear#", hx(fluff(ear, 0.2, 10, 9)), col=face_col, tris=T(320), role="ear", pri=1.5, pattern=hpat)

    # horns / antlers
    if P["horns"]:
        hn = horn_shape(P["horns"], HP, P["horn_scale"], hs)
        if P["horns"] == "ossicones":
            H.mpiece("Ossicone#", "Head", hx(hn), col="primary", tris=T(400), role="horn", pri=1.4)
        else:
            H.mpiece("Horn#", "Head", hx(hn), col=P["horn_col"], mat="hard", tris=T(1200 if P["horns"] in ("antler", "reindeer", "palmate", "elk") else 700), role="horn", pri=1.4)
    if P["horn_unicorn"]:
        hl = 0.82
        hrn = cone(0.09 * hs, 0.008 * hs, hl * 0.5 * hs, axis=1).at(0, hl * 0.5 * hs, 0)
        for k_ in (0, 1):
            rid = round_cone((0.075 * hs, 0.02 * hs, 0), (0.01 * hs, hl * 0.97 * hs, 0), 0.026 * hs, 0.005 * hs)
            if k_:
                rid = rid.rot(0, 180, 0)
            hrn = hrn.su(rid.twist(8.0 / hs, axis=1), 0.01)
        hrn = hrn.rot(-38, 0, 0).at(*L(0, c[3] + c[1] * 0.8, c[4] - 0.22))
        H.piece("UniHorn", "Head", hx(hrn), col=P["horn_col"], mat="hard", tris=T(900), res=128, role="horn", pri=1.3)

    # ------------------------------------------------------------------ mane / forelock / beard
    mt = P["mane"]
    if mt == "horse" and P["hq"]:
        H.piece("Mane", "Neck", mane_hq(neck, neck_c, [r0, r1, r2], flat, s, P.get("mane_len", 1.0)), col=P["mane_col"], tris=T(2200),
                res=128, role="mane", pri=1.2, pattern=mane_pattern(s))
    elif mt:
        mane = None
        n = 24 if mt != "shaggy" else 18
        if mt in ("horse", "flame", "brush"):
            cr_pts = []
            for i in range(9):
                p0, rr = neck_pt(0.03 + 0.94 * i / 8)
                cr_pts.append(p0 + nperp * rr * 0.92)
            mane = chain(cr_pts, 0.1 * s, 0.075 * s, k=0.05)
        for i in range(n + 1):
            t = 0.04 + 0.92 * i / n
            p0, rr = neck_pt(t)
            crest = p0 + nperp * rr * (0.95 if mt != "shaggy" else 0.7)
            if mt in ("horse", "flame"):
                ln = (0.36 + 0.18 * math.sin(i * 2.3)) * s * (1.0 if mt == "horse" else 0.8)
                if mt == "horse":
                    tip = crest + np.array([0.2 * s + 0.25 * rr, 0, 0]) - nperp * ln * 1.0 + dn * 0.04 * s
                    seg = round_cone(tuple(crest + np.array([0.04 * s, 0, 0])), tuple(tip), 0.09 * s, 0.035 * s)
                else:
                    tip = crest + nperp * ln * 1.2 + np.array([0.08 * s * math.sin(i * 1.9), 0, 0]) + np.array([0, 0, 0.12 * s])
                    seg = round_cone(tuple(crest), tuple(tip), 0.085 * s, 0.012 * s)
            elif mt == "brush":
                bh = P.get("brush_h", 0.2) * (0.75 + 0.25 * math.sin(i * 2.1))
                tip = crest + nperp * bh * s - dn * 0.04 * s
                seg = round_cone(tuple(crest - nperp * 0.03 * s), tuple(tip), 0.06 * s, 0.035 * s)
            else:  # shaggy ruff under/around the neck (bison, reindeer, elk, llama)
                seg = sphere(rr * 1.06, tuple(p0 - nperp * rr * 0.25))
            mane = seg if mane is None else mane.su(seg, 0.06 if mt != "shaggy" else 0.12)
        if mt == "horse":
            mane = mane.noise(0.022 * s, 13 / s, 11)
        elif mt == "shaggy":
            mane = (mane & half_space(1, -1, (nb[1] - 0.6 * s))).noise(0.05 * s, 7 / s, 12)
        H.piece("Mane", "Neck", mane, col=P["mane_col"], tris=T(1600 if mt != "brush" else 900), res=104, role="mane", pri=1.2)
    if P["forelock"]:
        fl = None
        for i, x in enumerate((-0.06, 0.0, 0.06)):
            seg = round_cone(L(x * 0.6, c[3] + c[1] * 0.9, c[4] + 0.05), L(x * 1.4, c[3] + c[1] * 0.45, c[4] - c[2] * 0.85 - 0.05 * (i == 1)), 0.06 * hs, 0.025 * hs)
            fl = seg if fl is None else fl.su(seg, 0.04)
        H.piece("Forelock", "Head", hx(fl.noise(0.012 * hs, 18 / hs, 13)), col=P["mane_col"], tris=T(350), role="mane", pri=1.6)

    # ------------------------------------------------------------------ tail
    tt = P["tail"]
    TLn = P["tail_len"]
    troot = V(0, top - 0.24 * Dp - sl, 1.82 * BL)
    tail_bones = []
    if tt:
        if tt == "horse":
            t1 = troot + V(0, -0.15, 0.22) * TLn
            t2 = t1 + V(0, -0.6, 0.22) * TLn
            t3 = t2 + V(0, -0.65, 0.08) * TLn
        elif tt in ("tuft", "rope"):
            t1 = troot + V(0, -0.35, 0.14) * TLn
            t2 = t1 + V(0, -0.5, 0.05) * TLn
            t3 = t2 + V(0, -0.45, 0.0) * TLn
        elif tt == "flag":
            t1 = troot + V(0, 0.05, 0.12) * TLn
            t2 = t1 + V(0, -0.12, 0.12) * TLn
            t3 = t2 + V(0, -0.15, 0.05) * TLn
        elif tt == "curl":
            t1 = troot + V(0, -0.05, 0.1)
            t2 = t1 + V(0, -0.08, 0.1)
            t3 = t2 + V(0, -0.12, 0.02)
        else:  # stub
            t1 = troot + V(0, -0.1, 0.12) * TLn
            t2 = t1 + V(0, -0.15, 0.08) * TLn
            t3 = t2 + V(0, -0.15, 0.03) * TLn
        H.bone("Tail1", "Loin", tuple(troot))
        H.bone("Tail2", "Tail1", tuple(t1))
        H.bone("Tail3", "Tail2", tuple(t2))
        tail_bones = ["Tail1", "Tail2", "Tail3"]
        if tt == "horse" and P["hq"]:
            tail_hq(H, P, s, troot, t1, t2, t3, T, skin)
        elif tt == "horse":
            dock = round_cone(tuple(troot - V(0, 0, 0.12)), tuple(t1 + V(0, -0.05, 0.02)), 0.11 * s, 0.085 * s)
            H.piece("TailDock", "Tail1", dock, col="primary", tris=T(300), role="tail", pri=1.5, pattern=skin())
            h1 = round_cone(tuple(troot + V(0, 0.0, 0.04)), tuple(t2 + V(0, -0.05, 0.03)), 0.12 * s, 0.17 * s)
            h1 = h1.su(ellipsoid(0.12 * s, 0.28 * s, 0.12 * s, tuple((t1 + t2) / 2 + V(0, 0, 0.04))), 0.1)
            H.piece("TailHair1", "Tail2", h1.noise(0.025 * s, 12 / s, 14), col=P["mane_col"], tris=T(500), role="tail", pri=1.6)
            h2 = round_cone(tuple(t2), tuple(t3), 0.17 * s, 0.13 * s)
            for k_ in range(6):
                a = k_ / 6 * math.tau
                h2 = h2.su(round_cone(tuple(t2 + V(0.04 * math.cos(a), 0, 0.04 * math.sin(a))), tuple(t3 + V(0.09 * math.cos(a), -0.12 - 0.06 * (k_ % 2), 0.08 * math.sin(a))), 0.08 * s, 0.03 * s), 0.05)
            H.piece("TailHair2", "Tail3", h2.noise(0.025 * s, 12 / s, 15), col=P["mane_col"], tris=T(600), role="tail", pri=1.7)
        elif tt in ("tuft", "rope"):
            tr_ = 0.06 * s
            H.piece("TailA", "Tail1", round_cone(tuple(troot - V(0, 0, 0.08)), tuple(t1), tr_ * 1.3, tr_), col="primary", tris=T(260), role="tail", pri=1.5, pattern=skin())
            H.piece("TailB", "Tail2", round_cone(tuple(t1), tuple(t2), tr_, tr_ * 0.8), col="primary", tris=T(240), role="tail", pri=1.6, pattern=skin())
            tuft = round_cone(tuple(t2), tuple(t3), tr_ * 0.8, tr_ * 0.7)
            tuft = tuft.su(ellipsoid(0.09 * s, 0.22 * s, 0.09 * s, tuple(t3 + V(0, -0.08, 0))).noise(0.02 * s, 14 / s, 16), 0.06)
            H.piece("TailC", "Tail3", tuft, col=P["mane_col"], tris=T(300), role="tail", pri=1.7)
        elif tt == "flag":
            fl_ = ellipsoid(0.11 * s, 0.07 * s, 0.2 * s, tuple((troot + t1) / 2))
            H.piece("TailA", "Tail1", fluff(fl_, 0.4, 8, 17), col="primary", tris=T(260), role="tail", pri=1.5, pattern=skin())
            fl2 = ellipsoid(0.1 * s, 0.07 * s, 0.17 * s, tuple((t1 + t2) / 2 + V(0, 0, -0.02)))
            H.piece("TailB", "Tail2", fluff(fl2, 0.4, 8, 18), col=P["mane_col"] if P["mane_col"] != "secondary" else "secondary", tris=T(240), role="tail", pri=1.6)
        elif tt == "curl":
            pts = curve(lambda u: troot + V(0.0 + 0.07 * math.sin(u * 4.4), -0.05 - 0.1 * u + 0.07 * (1 - math.cos(u * 4.4)), 0.06 + 0.06 * u + 0.07 * math.sin(u * 4.4 + 1.2)), 12)
            H.piece("TailA", "Tail1", chain(pts, 0.035 * s, 0.022 * s, k=0.02), col="primary", tris=T(300), role="tail", pri=1.5)
            tail_bones = ["Tail1"]
        else:
            st = round_cone(tuple(troot - V(0, 0, 0.06)), tuple(t2), 0.12 * s, 0.08 * s)
            H.piece("TailA", "Tail1", fluff(st, 0.6, 7, 19), col="primary", tris=T(300), role="tail", pri=1.5, pattern=skin())
            tail_bones = ["Tail1"]

    # ------------------------------------------------------------------ wings
    wing_bones = []
    if P["wings"]:
        wing_bones = build_wings(H, P, V, s, G, top, BL)

    # ------------------------------------------------------------------ tack
    zs = -0.5 * BL * s
    seat_y = (top + 0.1) * s
    if P["hq"] and P["tack"] in ("riding", "barding"):
        seat_y = riding_tack_hq(H, P, s, torso, head_can, hx, hp, L, neck_pt, nperp, nb, top * s, Dp * s, yb * s, BL, zs, HP, hs, rump, neck, G)
    elif P["tack"] in ("riding", "barding"):
        seat_y = riding_tack(H, P, s, torso, head_can, hx, hp, L, neck_pt, nperp, nb, top * s, Dp * s, yb * s, BL, zs, HP, hs, rump, neck)
    elif P["tack"] == "bridle":
        bridle(H, head_can, hx, hp, L, HP, hs, s, neck_pt, nperp, zs, top * s, reins=False)
    if P["hq"] and P["tack"] in ("riding", "barding"):
        H.socket("seat", (0, seat_y, zs), "Body")     # the rider's hip point, on the saddle seat
    else:
        H.socket("seat", (0, seat_y + 0.05 * s, zs), "Body")
    sad_w = 2 * surf(torso, (0, (top - 0.25) * s, zs), (1, 0, 0)) / s
    H.mount = {"seat": "Torso", "saddle": {"pos": (0, seat_y, zs), "size": v(min(1.3, sad_w * 0.9), 0.18, 1.1 * BL)}}

    # ------------------------------------------------------------------ rig + motion
    legs_rig = [{"hip": "ShoulderFR", "knee": "KneeFR", "phase": 0.75, "side": 1}, {"hip": "ShoulderFL", "knee": "KneeFL", "phase": 0.25, "side": -1},
                {"hip": "HipBR", "knee": "StifleBR", "phase": 0.5, "side": 1}, {"hip": "HipBL", "knee": "StifleBL", "phase": 0.0, "side": -1}]
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": tail_bones, "legs": legs_rig, "spine": "Loin", "neck": "Neck"})
    body_pos = H.bpos("Body")
    R = {
        "FR": ("ShoulderFR", "KneeFR", "FetFR"), "FL": ("ShoulderFL", "KneeFL", "FetFL"),
        "HR": ("HipBR", "StifleBR", "HockBR", "FetBR"), "HL": ("HipBL", "StifleBL", "HockBL", "FetBL"),
        "loin": "Loin", "neck": "Neck", "head": "Head", "jaw": "Jaw", "tail": tail_bones,
        "ears": ["EarR", "EarL"] if P["ears"] else [], "wings": wing_bones,
        "hip_rel": (bH[1] - body_pos[1], bH[2] - body_pos[2]),
        "stirrups": [b for b in ("StirrupR", "StirrupL") if b in H.bidx],
        "graze": P.get("graze", 1.0),
    }
    H._R = R
    H._ctx = dict(P=P, s=s, top=top, yb=yb, Dp=Dp, G=G, BL=BL, poll=poll, hp=hp, hx=hx, L=L, HP=HP, hs=hs, torso=torso,
                  rump=rump, neck=neck, head_can=head_can, zs=zs, nb=nb, nperp=nperp, dn=dn, neck_pt=neck_pt, cy=cy, V=V,
                  fF=fF, bF=bF, R=R, T=T, body=body)
    if P.get("extra"):
        P["extra"](H, H._ctx)
    finalize(H)
    if P.get("clips", True):
        kw_ = dict(attack=P["attack"], height=(top + 0.6) * s, fold=P["fold"], heavy=P["heavy"], flap=P["flap"])
        fly = walk = None
        if P["wing_fold"]:
            motion_hoofed.ungulate_clips(H, R, gait="fly", stride=P["stride"], **kw_)
            fly = H.clips.pop("Move")
        if P["walk_clip"]:
            motion_hoofed.ungulate_clips(H, R, gait=P.get("walk_gait", "walk"), stride=P.get("walk_stride", 1.0), length=P.get("walk_len"), **kw_)
            walk = H.clips.pop("Move")
        motion_hoofed.ungulate_clips(H, R, gait=P["gait"], stride=P["stride"], length=P["move_len"], **kw_)
        if walk:
            H.clips["Walk"] = walk
        if fly:
            H.clips["Fly"] = fly
        if P["wing_fold"]:
            wing_clips(H, R, (top + 0.6) * s)
    if P["mount"]:
        mount_table(H, P, s, torso, zs, fF, bF)
    return H


# ------------------------------------------------------------------------------------------------ horns
def horn_shape(kind, HP, sc, hs):
    """Right-side (+X) horn / antler in the canonical head frame."""
    c = HP["cran"]
    bx, by, bz = HP["ear"][0] * 0.75, c[3] + c[1] * 0.85, c[4] - 0.02

    def L(x, y, z):
        return np.array([x, y, z]) * hs

    base = L(bx, by, bz)
    S = sc

    if kind in ("antler", "elk", "reindeer"):
        big = {"antler": 1.0, "elk": 1.35, "reindeer": 1.3}[kind]
        S *= big
        # main beam: up, back, out, then sweeping forward at the top
        beam = curve(lambda u: base + L(0.12 * S * math.sin(u * 2.2) + 0.08 * u * S, 0.95 * S * u, 0.35 * S * math.sin(u * 2.6) - 0.18 * S * u ** 2), 10)
        ant = chain(beam, 0.072 * hs * min(S, 1.3), 0.03 * hs, k=0.03)
        ant = ant.su(sphere(0.07 * hs, tuple(base + L(0, 0.02, 0))), 0.03)  # pedicle burr
        tines = [(0.12, (0.0, 0.12, -0.3)), (0.32, (0.04, 0.2, -0.24)), (0.55, (0.02, 0.22, -0.18)), (0.78, (0.05, 0.18, -0.1))]
        if kind == "reindeer":
            tines = [(0.1, (-0.05, 0.05, -0.35)), (0.25, (0.08, 0.18, -0.2)), (0.5, (0.05, 0.22, -0.2)), (0.72, (0.12, 0.16, 0.05)), (0.9, (0.0, 0.15, -0.2))]
        if kind == "elk":
            tines = [(0.08, (0.02, 0.1, -0.36)), (0.2, (0.03, 0.12, -0.32)), (0.45, (0.06, 0.25, -0.22)), (0.65, (0.05, 0.25, -0.15)), (0.85, (0.04, 0.2, -0.08))]
        for u, (dx, dy, dz) in tines:
            i = min(int(u * 10), 9)
            p = beam[i]
            q = p + L(dx * S, dy * S, dz * S)
            mid = (p + q) / 2 + L(0, 0.04 * S, 0)
            ant = ant.su(chain([p, mid, q], 0.048 * hs * min(S, 1.2), 0.018 * hs, k=0.02), 0.025)
        if kind == "reindeer":  # brow shovel
            sh = ellipsoid(0.03 * hs, 0.09 * S * hs, 0.08 * S * hs, tuple(beam[1] + L(-0.06, 0.02, -0.3 * S)))
            ant = ant.su(sh, 0.03)
        return ant
    if kind == "palmate":
        beam = curve(lambda u: base + L(0.4 * S * u, 0.12 * S * u, 0.05 * S * u), 4)
        pal = chain(beam, 0.07 * hs, 0.055 * hs, k=0.03)
        pc = beam[-1] + L(0.32 * S, 0.12 * S, 0.0)
        palm = ellipsoid(0.42 * S * hs, 0.06 * hs, 0.3 * S * hs, (0, 0, 0)).rot(0, 0, 32).at(*pc)
        for k in range(7):
            a = -0.5 + k / 6 * 1.9
            tip = pc + L(math.cos(a) * 0.42 * S + 0.05, math.sin(max(0.0, a)) * 0.25 * S + 0.12 * S + 0.22 * S * math.cos(a), -math.sin(a) * 0.32 * S)
            pal = pal.su(round_cone(tuple(pc + (tip - pc) * 0.6), tuple(tip), 0.05 * hs, 0.015 * hs), 0.03)
        brow = beam[1] + L(0.02, 0.05, -0.28 * S)
        pal = pal.su(chain([beam[1], (beam[1] + brow) / 2 + L(0, 0.05, 0), brow], 0.04 * hs, 0.015 * hs), 0.03)
        return pal.su(palm, 0.08).su(sphere(0.08 * hs, tuple(base)), 0.03)
    if kind == "bull":
        pts = curve(lambda u: base + L(0.1 + 0.4 * S * u, 0.02 + 0.42 * S * u ** 1.7, -0.32 * S * u ** 2), 8)
        return chain(pts, 0.085 * hs, 0.018 * hs, k=0.03)
    if kind == "longhorn":
        pts = curve(lambda u: base + L(0.1 + 1.1 * S * u, 0.02 + 0.3 * S * u ** 3, -0.1 * S * u), 10)
        return chain(pts, 0.08 * hs, 0.015 * hs, k=0.03)
    if kind == "cow":
        pts = curve(lambda u: base + L(0.08 + 0.2 * S * u, 0.03 + 0.12 * S * u ** 2, -0.06 * S * u), 6)
        return chain(pts, 0.055 * hs, 0.02 * hs, k=0.02)
    if kind == "bison":
        pts = curve(lambda u: base + L(0.1 + 0.2 * S * u, 0.0 + 0.2 * S * u ** 1.5, 0.0 - 0.04 * u), 6)
        return chain(pts, 0.07 * hs, 0.018 * hs, k=0.02)
    if kind == "buffalo":
        pts = curve(lambda u: base + L(0.05 + 0.7 * S * math.sin(u * 1.9), 0.05 + 0.25 * S * u - 0.05 * u, 0.4 * S * u ** 1.5), 10)
        h = chain(pts, 0.11 * hs, 0.02 * hs, k=0.03, ridges=0.08)
        return h.su(ellipsoid(0.2 * hs, 0.08 * hs, 0.14 * hs, tuple(base + L(-0.02, 0.0, 0))), 0.05)  # boss
    if kind == "cape":
        pts = curve(lambda u: base + L(0.05 + 0.55 * S * u, 0.08 - 0.25 * S * math.sin(u * 2.4) + 0.25 * S * u ** 2, 0.05 - 0.12 * S * u), 10)
        h = chain(pts, 0.1 * hs, 0.02 * hs, k=0.03)
        return h.su(ellipsoid(0.2 * hs, 0.09 * hs, 0.18 * hs, tuple(base + L(-0.06, 0.02, 0.0))), 0.06)
    if kind == "ram":
        # thick spiral curling back, down and forward around the ear
        def sp(u):
            a = u * 1.75 * math.tau * 0.62
            rad = (0.3 - 0.12 * u) * S
            return base + L(0.06 + 0.36 * S * u, -rad * (1 - math.cos(a)) * 0.9 + 0.04, rad * math.sin(a) * 0.9)
        pts = curve(sp, 16)
        return chain(pts, 0.11 * hs * min(1.0, S + 0.2), 0.03 * hs, k=0.03, ridges=0.08)
    if kind in ("goat", "ibex", "markhor"):
        big = {"goat": 1.0, "ibex": 1.7, "markhor": 1.6}[kind]
        S2 = S * big
        pts = curve(lambda u: base + L(0.02 + 0.12 * S2 * u, 0.45 * S2 * math.sin(u * 1.4), 0.55 * S2 * (1 - math.cos(u * 1.6)) + 0.32 * S2 * u + 0.05), 10)
        return chain(pts, 0.065 * hs * min(1.4, big ** 0.6), 0.015 * hs, k=0.02, ridges=0.12 if kind == "ibex" else 0.04)
    if kind == "mountain":
        pts = curve(lambda u: base + L(0.02 + 0.05 * u, 0.32 * S * u, 0.16 * S * u ** 2), 6)
        return chain(pts, 0.045 * hs, 0.012 * hs, k=0.02)
    if kind == "oryx":
        pts = curve(lambda u: base + L(0.0 + 0.06 * u, 1.05 * S * u * math.cos(0.5), 1.05 * S * u * math.sin(0.5) + 0.02 * u), 12)
        return chain(pts, 0.045 * hs, 0.012 * hs, k=0.015, ridges=0.12)
    if kind == "gazelle":
        pts = curve(lambda u: base + L(0.02 + 0.06 * u, 0.55 * S * u, 0.28 * S * math.sin(u * 2.0) - 0.12 * S * u ** 3), 10)
        return chain(pts, 0.04 * hs, 0.01 * hs, k=0.015, ridges=0.14)
    if kind == "impala":
        pts = curve(lambda u: base + L(0.02 + 0.32 * S * math.sin(u * 2.2) * 0.8 - 0.06 * u, 0.75 * S * u, 0.35 * S * math.sin(u * 2.2) - 0.25 * S * u ** 3), 12)
        return chain(pts, 0.045 * hs, 0.01 * hs, k=0.015, ridges=0.12)
    if kind in ("tusk", "bigtusk"):
        m = HP["muz"]
        b0 = L(m[0] * 0.75, m[3] - m[1] * 0.35, m[4] + m[2] * 0.4)
        big = 1.0 if kind == "tusk" else 1.7
        pts = curve(lambda u: b0 + L(0.1 * S * big * u, 0.26 * S * big * math.sin(u * 1.6), 0.12 * S * big * u - 0.1 * S * big * u ** 2), 8)
        return chain(pts, 0.04 * hs * big ** 0.5, 0.01 * hs, k=0.02)
    if kind == "ossicones":
        p0 = base + L(-0.02, -0.02, 0.0)
        p1 = p0 + L(0.03, 0.28 * S, 0.02)
        return round_cone(tuple(p0), tuple(p1), 0.05 * hs, 0.04 * hs).su(sphere(0.06 * hs, tuple(p1 + L(0, 0.02, 0))), 0.03)
    raise ValueError(kind)


# ------------------------------------------------------------------------------------------------ extras
def skirt(H, X, length=0.45, col="primary", top_frac=0.6, amp=0.03, name="Skirt", bone="Body"):
    """Long hanging coat (yak, musk ox, mammoth): the barrel's cross-section extruded down past the belly line,
    with vertical strands and a ragged hem."""
    s, yb, Dp, body = X["s"], X["yb"], X["Dp"], X["body"]
    lvl = (yb + 0.42 * Dp) * s
    zc = 0.0

    def warp(p):
        q = p.copy()
        q[:, 1] = np.maximum(p[:, 1], lvl)
        return q

    base = body.round(0.035 * s).warp(warp)
    hem = (yb - length) * s

    def f(p):
        below = np.clip((lvl - p[:, 1]) / (0.6 * s), 0, 1)
        d = base(p) - 0.12 * s * below                      # hair flares out as it hangs
        a = np.arctan2(p[:, 0], p[:, 2] - zc)
        d = d + amp * s * (np.sin(a * 57) + 0.6 * np.sin(a * 31 + 1.3)) * below
        cut = hem + 0.08 * s * np.sin(a * 23) + 0.06 * s * np.sin(a * 11 + 1) - p[:, 1]
        return np.maximum(d, cut)

    sk = SDF(f) & half_space(1, 1, (yb + top_frac * Dp) * s)
    H.piece(name, bone, sk, col=col, tris=X["T"](1800), res=128, role="body", pri=1.1)


# ------------------------------------------------------------------------------------------------ wings
def _feather(c, d, length, width, thick, s):
    """Flattened ellipsoid feather centred at c, its long axis along d (in the XZ plane, + a little Y)."""
    d = np.asarray(d, float)
    d = d / np.linalg.norm(d)
    ry = math.degrees(math.atan2(d[0], d[2]))
    rx = -math.degrees(math.asin(np.clip(d[1], -1, 1)))
    return ellipsoid(width * s, thick * s, length * 0.5 * s, (0, 0, 0)).rot(rx, ry, 0).at(*c)


def build_wings(H, P, V, s, G, top, BL):
    """Feathered spread wings (pegasus): arm + covert plate + overlapping secondaries on Wing#1, hand + covert plate +
    fanned primaries on Wing#2. Feathers overlap into one continuous scalloped surface."""
    sp = P.get("wing_span", 1.0)
    root = V(0.3 * G, top - 0.06, -0.78 * BL)
    wrist = root + V(1.1 * sp, 0.36 * sp, 0.12)
    tip = wrist + V(1.0 * sp, 0.22 * sp, 0.32)
    H.mbone("Wing#1", "Body", tuple(root))
    H.mbone("Wing#2", "Wing#1", tuple(wrist))
    ad = (wrist - root) / np.linalg.norm(wrist - root)
    arm = round_cone(tuple(root - V(0.12, 0, 0)), tuple(wrist), 0.13 * s, 0.075 * s)
    cov = ellipsoid(0.6 * sp * s, 0.06 * s, 0.26 * sp * s, (0, 0, 0)).rot(0, 0, math.degrees(math.atan2(ad[1], ad[0]))).at(*((root + wrist) / 2 + V(0, 0.0, 0.2)))
    w1 = arm.su(cov, 0.06)
    n = 8
    for i in range(n):
        u = (i + 0.5) / n
        p = root + (wrist - root) * u
        ln = (0.7 + 0.18 * math.sin(u * 3.0)) * sp
        d = np.array([0.1 + 0.25 * u, -0.08, 1.0])
        c = p + V(0, -0.02, 0) + d / np.linalg.norm(d) * ln * 0.5 * s
        w1 = w1.su(_feather(c, d, ln, 0.11 * sp, 0.04, s), 0.03)
    H.mpiece("Wing#1", "Wing#1", w1, col="primary", tris=1400, res=120, role="wing", pri=1.2)
    hd = (tip - wrist) / np.linalg.norm(tip - wrist)
    hand = round_cone(tuple(wrist), tuple(tip), 0.075 * s, 0.035 * s)
    cov2 = ellipsoid(0.52 * sp * s, 0.055 * s, 0.2 * sp * s, (0, 0, 0)).rot(0, -math.degrees(math.atan2(hd[2], hd[0])), math.degrees(math.atan2(hd[1], hd[0]))).at(*((wrist + tip) / 2 + V(0.0, 0.0, 0.14)))
    w2 = hand.su(cov2, 0.05)
    n = 8
    for i in range(n):
        u = i / (n - 1)
        p = wrist + (tip - wrist) * (0.08 + 0.92 * u)
        ang = math.radians(14 + 64 * u)
        ln = (0.72 + 0.42 * math.sin(u * 2.4)) * sp
        d = np.array([math.sin(ang), -0.06, math.cos(ang)])
        c = p + d / np.linalg.norm(d) * ln * 0.5 * s
        w2 = w2.su(_feather(c, d, ln, 0.105 * sp, 0.035, s), 0.025)
    H.mpiece("Wing#2", "Wing#2", w2, col="primary", tris=1400, res=120, role="wing", pri=1.25)
    return [("WingR1", "WingR2"), ("WingL1", "WingL2")]


# ------------------------------------------------------------------------------------------------ tack
def bridle(H, head_can, hx, hp, L, HP, hs, s, neck_pt, nperp, zs, top, reins=True, col=LEATHER, bit=True, hands=None):
    """Headstall + browband + noseband + cheek straps + bit rings (Head), reins to the pommel (Neck)."""
    c = HP["cran"]
    m = HP["muz"]
    shell = head_can.shell(0.028 * hs)
    zh = c[4] - 0.02
    band = shell & box(0.6 * hs, 0.6 * hs, 0.04 * hs, L(0, 0, zh + 0.06))                                   # headstall behind the eyes
    nz = m[4] + m[2] * 0.55
    band = band | (shell & box(0.6 * hs, 0.6 * hs, 0.045 * hs, L(0, 0, nz)))                              # noseband
    ex = HP["eye"]
    cheek_a = L(ex[0] + 0.04, ex[1] - 0.08, zh + 0.06)
    cheek_b = L(m[0] * 0.95, m[3] - 0.03, m[4] + 0.1)
    band = band | (shell & capsule(tuple(cheek_a), tuple(cheek_b), 0.04 * hs).mirror_x())
    brow = shell & capsule(L(0.18, c[3] + c[1] * 0.55, zh - 0.07), L(-0.18, c[3] + c[1] * 0.55, zh - 0.07), 0.035 * hs)
    band = band | brow
    mo = HP["mouth"]
    # bit rings at the corners of the mouth
    ring_c = np.array([0.0, mo[1] + 0.05, mo[2] + 0.2])
    rx_ = surf(head_can, L(0, ring_c[1], ring_c[2]), (1, 0, 0), hi=1.0 * hs) / hs + 0.03
    ring = torus(0.055 * hs, 0.014 * hs, axis=0).at(*L(rx_, ring_c[1], ring_c[2])).mirror_x()
    H.piece("Bridle", "Head", hx(band), col=col, tris=900, res=112, role="detail", pri=1.6, ao=False)
    if bit:
        H.piece("Bit", "Head", hx(ring), col="metal", mat="metal", tris=320, res=140, role="detail", pri=2.0, ao=False)
    if not reins:
        return
    bit_w = hp(rx_, ring_c[1], ring_c[2])
    rs = None
    for sx in (1, -1):
        a = bit_w * np.array([sx, 1, 1])
        p1, r1 = neck_pt(0.62)
        p2, r2 = neck_pt(0.25)
        m1 = p1 + np.array([sx * (r1 * 0.72 + 0.06 * s), 0, 0]) - nperp * r1 * 0.35
        m2 = p2 + np.array([sx * (r2 * 0.7 + 0.08 * s), 0, 0]) - nperp * r2 * 0.1
        e = np.array([sx * 0.16 * s, top + 0.22 * s, zs - 0.42 * s]) if hands is None else np.array([sx * hands[0], hands[1], hands[2]])
        pts = [a, (a + m1) / 2 - np.array([0, 0.06 * s, 0]), m1, m2, e]
        seg = chain(pts, 0.022 * s, 0.022 * s, k=0.02)
        rs = seg if rs is None else rs | seg
    H.piece("Reins", "Neck", rs, col=col, tris=500, role="detail", pri=1.8, ao=False)


def riding_tack(H, P, s, torso, head_can, hx, hp, L, neck_pt, nperp, nb, top, Dp, yb, BL, zs, HP, hs, rump, neck):
    """Saddle blanket, saddle (seat, pommel, cantle, skirts, girth), stirrups (own bones), bridle + reins.
    Barding adds a chanfron, crinet, peytral and a caparison. All lengths in studs. Returns the seat height."""
    sz0, sz1 = zs - 0.55 * s, zs + 0.5 * s
    blk = torso.shell(0.055 * s) & round_box(1.5 * s, 0.6 * Dp, (sz1 - sz0) / 2 + 0.14 * s, 0.3 * s, (0, top - 0.02 * s, zs + 0.02 * s)).rot(0, 0, 0)
    blk = blk & half_space(1, -1, top - 0.52 * Dp)
    if P["blanket"]:
        H.piece("Blanket", "Body", blk, col=BLANKET if P["tack"] == "riding" else "secondary", mat="cloth", tris=800, res=104, role="detail", pri=1.4)
    sad = torso.shell(0.13 * s) & ellipsoid(1.4 * s, 0.46 * Dp, (sz1 - sz0) / 2, (0, top + 0.02 * s, zs))   # rounded skirts
    sad = sad & half_space(1, -1, top - 0.45 * Dp)
    ty = top + 0.1 * s
    sad = sad.su(ellipsoid(0.15 * s, 0.17 * s, 0.12 * s, (0, ty + 0.1 * s, sz0 + 0.14 * s)), 0.09)          # pommel
    sad = sad.su(ellipsoid(0.27 * s, 0.13 * s, 0.09 * s, (0, ty + 0.1 * s, sz1 - 0.12 * s)), 0.09)          # cantle
    sad = sad.ss(ellipsoid(0.2 * s, 0.05 * s, 0.26 * s, (0, ty + 0.1 * s, zs + 0.02 * s)), 0.06)            # seat dip
    gh = top - 0.4 * Dp
    girth = torso.shell(0.035 * s) & box(1.5 * s, gh / 2, 0.08 * s, (0, gh / 2 - 0.1 * s, zs - 0.3 * s))
    sad = sad | girth
    H.piece("Saddle", "Body", sad, col=LEATHER, tris=1100, res=104, role="detail", pri=1.5)
    side = surf(torso, (0, top - 0.42 * Dp, zs - 0.05 * s), (1, 0, 0)) + 0.2 * s
    sy = top - 0.3 * Dp
    H.mbone("Stirrup#", "Body", (side, sy, zs - 0.05 * s))
    hang = 0.6 * Dp
    strap = round_box(0.03 * s, hang / 2, 0.05 * s, 0.015 * s, (side, sy - hang / 2, zs - 0.05 * s))
    iron = torus(0.11 * s, 0.022 * s, axis=2).at(side, sy - hang - 0.08 * s, zs - 0.05 * s)
    iron = (iron & half_space(1, 1, sy - hang - 0.02 * s)) | round_box(0.11 * s, 0.022 * s, 0.06 * s, 0.015 * s, (side, sy - hang - 0.18 * s, zs - 0.05 * s))
    H.mpiece("Stirrup#", "Stirrup#", strap, col=LEATHER, tris=150, res=100, role="detail", pri=1.8, ao=False, smooth=1)
    H.mpiece("Iron#", "Stirrup#", iron, col="metal", mat="metal", tris=320, role="detail", pri=1.9, ao=False)
    bridle(H, head_can, hx, hp, L, HP, hs, s, neck_pt, nperp, zs, top, reins=True, bit=P["bit"])
    if P["tack"] == "barding":
        barding(H, P, s, torso, rump, neck, head_can, hx, L, HP, hs, top, Dp, yb, BL, nb, nperp)
    return top + 0.2 * s


def barding(H, P, s, torso, rump, neck, head_can, hx, L, HP, hs, top, Dp, yb, BL, nb, nperp):
    c = HP["cran"]
    m = HP["muz"]
    e = HP["eye"]
    ch = head_can.shell(0.045 * hs) & half_space(1, -1, (m[3] - 0.02) * hs) & half_space(2, 1, (c[4] - 0.05) * hs) & half_space(2, -1, (m[4] - m[2] * 0.3) * hs)
    ch = ch.ss(sphere(e[3] * 1.9 * hs, L(e[0] + 0.03, e[1], e[2])).mirror_x(), 0.02)
    ch = ch.su(capsule(L(0, c[3] + c[1] + 0.03, c[4] - 0.1), L(0, m[3] + m[1] + 0.05, m[4] + 0.05), 0.03 * hs), 0.03)
    ch = ch.su(cone(0.06 * hs, 0.005 * hs, 0.12 * hs).rot(-50, 0, 0).at(*L(0, c[3] + c[1] + 0.06, c[4] - 0.25)), 0.02)
    H.piece("Chanfron", "Head", hx(ch), col="steel", mat="metal", tris=950, res=136, role="detail", pri=1.4)
    py = torso.shell(0.07 * s) & half_space(2, 1, -1.0 * BL * s) & half_space(1, -1, yb + 0.1 * s) & half_space(1, 1, top - 0.3 * Dp)
    py = py.ss(box(1.5 * s, 0.02 * s, 3 * s, (0, yb + 0.55 * Dp, 0)), 0.01)
    H.piece("Peytral", "Body", py, col="steel", mat="metal", tris=950, res=128, role="detail", pri=1.4)
    cr = neck.shell(0.06 * s) & plane(tuple(-nperp), float(-(nb @ nperp)))
    H.piece("Crinet", "Neck", cr, col="steel", mat="metal", tris=900, res=128, role="detail", pri=1.5)
    cp = rump.shell(0.06 * s) & half_space(2, -1, 0.35 * BL * s) & half_space(1, -1, yb + 0.25 * Dp)
    H.piece("Caparison", "Loin", cp, col="secondary", mat="cloth", tris=1000, res=128, role="detail", pri=1.4)


# ------------------------------------------------------------------------------------------------ hero-quality (hq) mount parts
def mane_hq(neck, neck_c, radii, flat, s, length=1.0):
    """A real mane: a layer of hair lying on the neck, from just over the crest (left) down the right side, with
    locks of different lengths, strand grooves running down the neck and a thicker roll along the crest."""
    A = [np.asarray(p, float) for p in neck_c]
    # smooth centreline through the three neck points (quadratic through A1 at u = 0.5), 10 short segments
    C1 = 2 * A[1] - 0.5 * (A[0] + A[2])
    Q = [(1 - u) ** 2 * A[0] + 2 * u * (1 - u) * C1 + u ** 2 * A[2] for u in np.linspace(0, 1, 11)]
    segs = [(Q[i], Q[i + 1], 0, 0) for i in range(10)]
    seg_len = [float(np.linalg.norm(b - a)) for a, b, _, _ in segs]
    total = sum(seg_len)
    frames = []
    for a, b, _, _ in segs:
        d = (b - a) / np.linalg.norm(b - a)
        up = np.array([0.0, d[2], -d[1]])      # perpendicular to d in the YZ plane, pointing up / back (crest side)
        if up[1] < 0:
            up = -up
        frames.append((d, up))

    def f(P):
        best = np.full(len(P), 1e9)
        along = np.zeros(len(P))
        upc = np.zeros(len(P))
        sidec = np.zeros(len(P))
        acc = 0.0
        for k, ((a, b, ra, rb), (d, up)) in enumerate(zip(segs, frames)):
            ab = b - a
            t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
            c = a + t[:, None] * ab
            rel = P - c
            dist = np.linalg.norm(rel - ((rel @ d)[:, None] * d), axis=1)
            m = dist < best
            best = np.where(m, dist, best)
            along = np.where(m, acc + t * seg_len[k], along)
            upc = np.where(m, rel @ up, upc)
            sidec = np.where(m, rel[:, 0] / flat, sidec)
            acc += seg_len[k]
        u = along / total                                      # 0 at the withers .. 1 at the poll
        th = np.arctan2(sidec, upc)                            # 0 on the crest, + down the right side
        r_ = np.sqrt(upc ** 2 + sidec ** 2)
        a_s = along / s
        thmax = (0.95 + 0.2 * np.sin(a_s * 6.1) + 0.12 * np.sin(a_s * 15.7 + 1.0) + 0.08 * np.sin(a_s * 31.0 + 2.0)) * length
        thmax = thmax * (0.55 + 0.45 * np.clip(u / 0.12, 0, 1)) * (0.75 + 0.25 * np.clip((1 - u) / 0.15, 0, 1))
        thmin = -0.26 - 0.05 * np.sin(a_s * 9.0)
        prog = np.clip(th / np.maximum(thmax, 0.2), 0, 1)
        left = np.clip(-th / 0.26, 0, 1)
        thick = s * (0.12 - 0.075 * prog ** 1.5 - 0.05 * left) * (1 + 0.28 * np.sin(a_s * 34.0) * np.clip(prog * 3, 0, 1))
        nd = neck(P)
        d_shell = np.maximum(nd - thick, -nd - 0.05 * s)
        d_ang = np.maximum(th - thmax, thmin - th) * np.maximum(r_, 0.2 * s)
        d_al = np.maximum(0.03 * total - along, along - 0.97 * total)
        return np.maximum(np.maximum(d_shell, d_ang), d_al)

    return SDF(f).noise(0.012 * s, 16 / s, 21)


def mane_pattern(s):
    """Darker strand grooves / roots so the mane reads as hair."""
    def f(P):
        return 0.86 + 0.14 * np.sin(P[:, 2] * 28 / s + P[:, 1] * 9 / s) ** 2
    return f


def tail_hq(H, P, s, troot, t1, t2, t3, T, skin):
    """Full horse tail: a muscular dock, then a fall of hair that arcs out, widens into a broad fan and ends in
    ragged locks above the hocks."""
    V_ = lambda x, y, z: np.array([x * s, y * s, z * s])
    dock = round_cone(tuple(troot - V_(0, 0.02, 0.14)), tuple(t1 + V_(0, -0.02, 0.0)), 0.12 * s, 0.095 * s)
    H.piece("TailDock", "Tail1", dock, col="primary", tris=T(320), role="tail", pri=1.5, pattern=skin())
    rng = np.random.default_rng(7)
    core = round_cone(tuple(troot + V_(0, 0.02, 0.06)), tuple(t2), 0.13 * s, 0.19 * s)
    h1 = core
    for k in range(9):
        a = k / 9 * math.tau
        p0 = troot + V_(0.05 * math.cos(a), 0.04 + 0.03 * math.sin(a), 0.06)
        p1 = t2 + V_(0.15 * math.cos(a), -0.02, 0.1 * math.sin(a))
        h1 = h1.su(round_cone(tuple(p0), tuple(p1), 0.075 * s, 0.085 * s), 0.05 * s)
    H.piece("TailHair1", "Tail2", h1.noise(0.014 * s, 22 / s, 14), col=P["mane_col"], tris=T(900), res=120, role="tail", pri=1.6,
            pattern=mane_pattern(s))
    end = t3 + V_(0, -0.25, 0.06)
    h2 = round_cone(tuple(t2 - V_(0, -0.05, 0.02)), tuple(end + V_(0, 0.25, 0)), 0.19 * s, 0.13 * s)
    for k in range(12):
        a = k / 12 * math.tau + rng.uniform(-0.2, 0.2)
        p0 = t2 + V_(0.12 * math.cos(a), 0.02, 0.08 * math.sin(a))
        dl = rng.uniform(-0.28, 0.12)
        p1 = end + V_(0.2 * math.cos(a) + rng.uniform(-0.03, 0.03), dl + 0.1 * (k % 2), 0.13 * math.sin(a) + 0.05)
        h2 = h2.su(round_cone(tuple(p0), tuple(p1), 0.085 * s, 0.028 * s), 0.045 * s)
    H.piece("TailHair2", "Tail3", h2.noise(0.014 * s, 22 / s, 15), col=P["mane_col"], tris=T(1100), res=120, role="tail", pri=1.7,
            pattern=mane_pattern(s))


CANVAS = [0.62, 0.55, 0.42]
BRASS = "gold"


def _rr2(z0, z1, y0, y1, r):
    """Side-projection rounded rectangle (z0..z1, y0..y1), infinite in x."""
    return round_box(50.0, (y1 - y0) / 2, (z1 - z0) / 2, r, (0, (y0 + y1) / 2, (z0 + z1) / 2))


def _edge_stitch(region, inset, width, depth=0.45, dash=None):
    """Pattern: a darker stitched line `inset` inside the region outline (region SDF < 0 inside)."""
    def f(P):
        d = region(P)
        line = np.clip(1 - np.abs(d + inset) / width, 0, 1)
        if dash:
            line = line * (np.sin((P[:, 2] + P[:, 1]) * dash) > -0.2)
        edge = np.clip(1 - np.abs(d) / (width * 1.6), 0, 1) * 0.5
        return 1 - depth * np.maximum(line, edge)
    return f


def riding_tack_hq(H, P, s, torso, head_can, hx, hp, L, neck_pt, nperp, nb, top, Dp, yb, BL, zs, HP, hs, rump, neck, G):
    """Fitted riding tack, sized for the R15 rider (lengths in studs, rider-relative where the rider touches it):
    a saddle pad with piping and stitching, a dished saddle with a raised pommel + horn and a tall cantle, leather
    fenders hanging under the rider's legs, a girth with brass buckles, stirrup leathers + irons on swinging
    Stirrup# bones, a bedroll and saddlebags behind the cantle, and the bridle with reins up to the rider's hands.
    Returns the seat (rider hip) height."""
    by = MK.ray_down(torso, 0.0, zs, top + 2.0, top - Dp)                 # back line at the seat
    yw = top - 0.62 * Dp                                                  # widest line of the barrel (fender hang)
    half_w = MK.ray_side(torso, yw, zs, 4.0 * s)
    zp, zc_ = zs - 1.05, zs + 0.78                                       # pommel / cantle
    # ---- pad: follows the back, big rounded outline, piping + stitching baked in
    pad_reg = _rr2(zs - 1.5, zs + 1.25, by - 1.5, by + 2.0, 0.35)
    pad = torso.round(0.075).shell(0.045) & pad_reg
    pad = pad & half_space(1, -1, by - 1.45)
    bl = P.get("blanket_col", BLANKET if P["tack"] == "riding" else "secondary")
    H.piece("Blanket", "Body", pad, col=bl, mat="cloth", tris=1300, res=136, role="detail", pri=1.4,
            pattern=_edge_stitch(lambda Q: np.maximum(pad_reg(Q), by - 1.45 - Q[:, 1]), 0.12, 0.03, 0.4, dash=60))
    # ---- saddle body: a leather shell over the pad, dished seat, pommel + horn, tall cantle
    sreg = _rr2(zs - 1.25, zs + 1.0, by - 0.95, by + 2.0, 0.45)
    sad = (torso.round(0.3) - torso.round(0.1)) & sreg
    seat_dip = ellipsoid(0.62, 0.16, 0.75, (0, by + 0.43, zs + 0.05))
    sad = sad.ss(seat_dip, 0.12)
    pom = ellipsoid(0.36, 0.3, 0.26, (0, by + 0.3, zp + 0.05)) & half_space(1, -1, by)
    sad = sad.su(pom, 0.14)
    horn = round_cone((0, by + 0.42, zp - 0.02), (0, by + 0.72, zp - 0.12), 0.085, 0.07)
    horn = horn.su(cylinder(0.15, 0.04, rr=0.03).at(0, by + 0.74, zp - 0.13), 0.03)
    sad = sad.su(horn, 0.04)
    cant = None
    for i in range(9):
        x = -0.62 + 1.24 * i / 8
        p0 = (x, by + 0.62 - 0.55 * x * x, zc_ + 0.1 * abs(x))
        seg = sphere(0.1, p0)
        cant = seg if cant is None else cant.su(seg, 0.12)
    back_fill = ellipsoid(0.62, 0.36, 0.3, (0, by + 0.3, zc_ + 0.02)) & half_space(1, -1, by)
    sad = sad.su(cant.su(back_fill, 0.15), 0.1)
    # fenders: leather flaps hanging straight down from the seat under the rider's thighs
    def hang(p):
        q = p.copy()
        q[:, 1] = np.maximum(p[:, 1], yw)
        return q
    ext = torso.warp(hang)
    fen_reg = _rr2(zs - 0.85, zs + 0.3, by - 1.55, by + 0.2, 0.28)
    fen = (ext.round(0.2) - ext.round(0.1)) & fen_reg & half_space(0, -1, 0.35 * half_w)
    fen = fen.mirror_x()
    sad = sad.su(fen, 0.06)
    sad_pat = combine(_edge_stitch(sreg, 0.1, 0.025, 0.35, dash=70), _edge_stitch(fen_reg, 0.08, 0.022, 0.35, dash=70),
                      lambda Q: 1 - 0.18 * np.clip((by + 0.25 - Q[:, 1]) / 0.6, 0, 1))
    H.piece("Saddle", "Body", sad, col="leather", tris=2600, res=144, role="detail", pri=1.5, pattern=sad_pat)
    # ---- girth with brass buckles at the fender bottom
    zg = zs - 0.5
    girth = torso.round(0.03).shell(0.035) & box(4.0, (by - 1.3 + 4.0) / 2, 0.14, (0, (by - 1.3 - 4.0) / 2, zg))
    H.piece("Girth", "Body", girth, col="leather", tris=500, res=120, role="detail", pri=1.7, ao=False)
    # ---- stirrups: leathers outside the fenders, irons where the rider's feet are
    sz_ = zs - 0.55
    fx = MK.ray_side(ext.round(0.2), by - 0.9, sz_, 4.0 * s) + 0.05
    sy0 = by + 0.05
    H.mbone("Stirrup#", "Body", (fx, sy0, sz_))
    yi = by - 1.62                                                         # iron tread height
    strap = round_box(0.03, (sy0 - yi - 0.2) / 2, 0.075, 0.015, (fx, (sy0 + yi + 0.2) / 2, sz_))
    iron = torus(0.2, 0.04, axis=0).at(fx + 0.02, yi + 0.2, sz_) & half_space(1, 1, yi + 0.2)
    iron = iron | round_box(0.22, 0.035, 0.18, 0.03, (fx + 0.02, yi + 0.02, sz_))
    iron = iron | capsule((fx + 0.02, yi + 0.02, sz_ - 0.2), (fx + 0.02, yi + 0.2, sz_ - 0.2), 0.04) | capsule((fx + 0.02, yi + 0.02, sz_ + 0.2), (fx + 0.02, yi + 0.2, sz_ + 0.2), 0.04)
    H.mpiece("Stirrup#", "Stirrup#", strap, col="leather", tris=200, res=100, role="detail", pri=1.8, ao=False, smooth=1)
    H.mpiece("Iron#", "Stirrup#", iron, col="metal", mat="metal", tris=420, res=110, role="detail", pri=1.9, ao=False)
    # ---- bedroll + saddlebags behind the cantle
    if P["bags"]:
        zb = zc_ + 0.55
        byb = MK.ray_down(torso, 0.0, zb, top + 2.0, top - Dp)
        roll = capsule((-0.62, byb + 0.22, zb), (0.62, byb + 0.22, zb), 0.22)
        roll = roll.ss(torus(0.23, 0.035, axis=0).at(0.35, byb + 0.22, zb).mirror_x(), 0.01)
        roll = roll.su(torus(0.215, 0.035, axis=0).at(0.35, byb + 0.22, zb).mirror_x(), 0.005)       # strap ridges
        H.piece("Bedroll", "Body", roll, col=CANVAS, mat="cloth", tris=600, res=110, role="detail", pri=1.9,
                pattern=lambda Q: 1 - 0.55 * (np.abs(np.abs(Q[:, 0]) - 0.35) < 0.05))
        bw = MK.ray_side(torso, byb - 0.45, zb + 0.1, 4.0 * s)
        bag = round_box(0.14, 0.36, 0.34, 0.1, (bw + 0.1, byb - 0.42, zb + 0.12))
        bag = bag.su(round_box(0.16, 0.14, 0.36, 0.06, (bw + 0.12, byb - 0.2, zb + 0.12)), 0.03)       # flap
        bag = bag.su(capsule((bw - 0.05, byb + 0.05, zb + 0.12), (bw + 0.02, byb - 0.15, zb + 0.12), 0.05), 0.04)
        H.mpiece("Bag#", "Body", bag, col="leather", tris=500, res=110, role="detail", pri=2.0,
                 pattern=lambda Q, _y=byb - 0.32: 1 - 0.35 * (np.abs(Q[:, 1] - _y) < 0.025))
    # ---- bridle + reins to the hands
    seat_y = MK.ray_down(sad, 0.0, zs, by + 1.5, by - 0.5) or by + 0.28
    hands = (0.38, seat_y + 1.05, zs - 1.45)
    bridle(H, head_can, hx, hp, L, HP, hs, s, neck_pt, nperp, zs, top, reins=True, bit=P["bit"], hands=hands)
    if P["tack"] == "barding":
        barding(H, P, s, torso, rump, neck, head_can, hx, L, HP, hs, top, Dp, yb, BL, nb, nperp)
    H._half_w = half_w
    return seat_y


def wing_fold_pose(H, side, k=1.0):
    """Euler for Wing#1 / Wing#2 that folds a spread feathered wing back along the flank (k = 0 spread .. 1 folded)."""
    sfx = "R" if side > 0 else "L"
    root, wrist = H.bpos("Wing" + sfx + "1"), H.bpos("Wing" + sfx + "2")
    ad = (wrist - root) * np.array([side, 1, 1])
    Rf = MK.frame_rot(ad, (0, 0, 1), (0.0, -0.32, 1.0), (0.18, -1.0, 0.1))
    a, b, c = MK.to_euler(Rf)
    w1 = (a * k, b * k * side, c * k * side)
    w2 = (0.0, -0.12 * k * side, 0.06 * k * side)
    return w1, w2


def wing_clips(H, R, h):
    """Pegasus wings: folded along the flanks in every ground clip (half open while rearing), spread for Fly and Glide."""
    wings = R["wings"]

    def fold(k):
        out = {}
        for side, (w1, w2) in zip((1, -1), wings):
            a, b = wing_fold_pose(H, side, k)
            out[w1] = (0, 0, 0) + a
            out[w2] = (0, 0, 0) + b
        return out

    for name in ("Idle", "Walk", "Move", "Hit"):
        if name in H.clips:
            # replace the authored small wing motion with the folded pose + a breathing shuffle
            for b in [w for pair in wings for w in pair]:
                H.clips[name]["tracks"].pop(b, None)
            MK.overlay(H, name, lambda t, u: fold(1.0 - 0.03 * (1 + math.sin(TAU_ * u * (3 if name == "Idle" else 1)))))
    if "Attack" in H.clips:
        MK.overlay(H, "Attack", lambda t, u: fold(1.0 - 0.75 * MK.bump(MK.win(u, 0.05, 0.85))))
    if "Fly" in H.clips:
        # the clip hovers the body 0.35 h up for the summon: a ridden flyer is placed by the game, keep only the bob
        MK.scale_track(H, "Fly", "Body", off=(0, -0.35 * h, 0, 0, 0, 0))

    def glide(t):
        u = t / 3.0
        pose = {}
        w = math.sin(TAU_ * u)
        MK._add(pose, "Body", (0, 0.03 * h * w, 0, -0.06 + 0.015 * math.sin(TAU_ * u + 1), 0, 0.03 * math.sin(TAU_ * u * 0.5 * 2)))
        for side, (w1, w2) in zip((1, -1), wings):
            MK._add(pose, w1, (0, 0, 0, 0.0, 0.0, side * (0.12 + 0.03 * w)))
            MK._add(pose, w2, (0, 0, 0, 0.0, 0.0, side * (-0.08 + 0.025 * math.sin(TAU_ * u - 0.8))))
        FR, FL, HR, HL = R["FR"], R["FL"], R["HR"], R["HL"]
        for bones in (FR, FL):
            MK._add(pose, bones[0], (0, 0, 0, 0.6, 0, 0))
            MK._add(pose, bones[1], (0, 0, 0, -1.6, 0, 0))
            MK._add(pose, bones[2], (0, 0, 0, -0.6, 0, 0))
        for bones in (HR, HL):
            MK._add(pose, bones[0], (0, 0, 0, -0.45, 0, 0))
            MK._add(pose, bones[1], (0, 0, 0, -0.2, 0, 0))
            MK._add(pose, bones[2], (0, 0, 0, 0.5, 0, 0))
            MK._add(pose, bones[3], (0, 0, 0, -0.4, 0, 0))
        MK._add(pose, R["neck"], (0, 0, 0, -0.18 + 0.03 * w, 0, 0))
        MK._add(pose, R["head"], (0, 0, 0, 0.12, 0, 0))
        for i, b in enumerate(R["tail"]):
            MK._add(pose, b, (0, 0, 0, -0.3 * (i == 0) + 0.06 * math.sin(TAU_ * u * 2 - i), 0.05 * math.sin(TAU_ * u - i), 0))
        for b in R["ears"]:
            MK._add(pose, b, (0, 0, 0, -0.4, 0, 0))
        return pose

    H.clip("Glide", 3.0, glide, keys=16)


TAU_ = 2 * math.pi


def mount_table(H, P, s, torso, zs, fF, bF):
    """Seat + enter sockets and H.mount (length, stride per Move cycle, walkStride per Walk cycle)."""
    m = P["mount"]
    seat = H.sockets["seat"][0]
    hw = getattr(H, "_half_w", None) or MK.ray_side(torso, seat[1] - 1.0, zs, 4.0 * s)
    feet = [("FetFR", (fF[0], 0.02, fF[2] - 0.05 * s)), ("FetBR", (bF[0], 0.02, bF[2] - 0.05 * s))]
    stride = MK.measure_stride(H, "Move", feet) if "Move" in H.clips and P["gait"] != "fly" else None
    walk = MK.measure_stride(H, "Walk", feet) if "Walk" in H.clips else None
    MK.set_mount(H, m["length"], seat, (-(hw + 1.6), 0, seat[2]), stride=stride, walk=walk, extra=m.get("extra"))
