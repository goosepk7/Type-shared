"""Shared SDF helpers for the monsters / spirits / constructs / apes families (plates, crystals, flames, bolts,
ragged hems). Not an h_ module: hero files import it. NOTE: build.py's mesh cache hashes only the h_ file, so after
changing a helper here rebuild the dependent families with --force."""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF


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


