"""Summon set: generic Blob creatures (Plans/Blob.luau creature builders).

Every piece is a "unit" sculpt authored in its lead primitive's local frame in studs (`lead=` the reference size the
plan builds; the plan scales the lead per word and the piece follows). Where the builder puts a face, the lead
ellipsoid is left untouched so eyes and mouths sit on the sculpt exactly as on the primitive. Member primitives
(skirts, mantles, tails, arms ...) are modelled in at the positions the plan gives them.

  s_blob_slime   slime: dome with a soft peak, a puddle skirt with lobed rim and drips   (lead Body 2.9x2.3x2.7)
  s_blob_slug    slug / sea slug: foot with a flared sole, mantle with wrinkles and breathing pore, rounded head,
                 keeled tapering tail                                                    (lead Body 1.5x0.9x4.0)
  s_blob_coil    snail shell, coiled about X (garden snail, periwinkle, moon snail)      (lead Shell 1.6x1.9x1.9)
  s_blob_spire   high-spired shell with a flared lip (conch, whelk, african snail)       (lead Shell 1.7x1.6x3.0)
  s_blob_valve   bivalve half: ribbed fan-shaped cap, hollow inside, umbo at the hinge   (lead Valve 3.0x0.9x2.5)
  s_blob_bell    jellyfish bell: dome, scalloped rim, hollow under-bell                   (lead Bell 3.0x2.2x3.0)
  s_blob_star    upright sea star: disc + five tapering arms with rows of tubercles      (lead Disc 1.7x1.7x0.8)
  s_blob_urchin  sea urchin: ball of spines with a clear face patch                      (lead Core 2.4 ball)
  s_blob_fluff   fluff ball: clumped tufts all round, smooth face patch                   (lead Fluff 2.6 ball)
  s_blob_heap    abomination heap: fused lumps with stitched seams, clean face zone      (lead Body 3.4x2.4x3.0)
  s_blob_ghost   sheet ghost: round head, flaring sheet with folds and a wavy hem        (lead Body 2.2x2.6x2.0)
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from . import piece


def _keep_above(s, y, k=0.04):
    """Cut the shape flat at y (ground contact), softly."""
    return s.si(half_space(1, -1, y), k)


def _fib(n):
    """n roughly even unit directions."""
    out = []
    g = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(max(0.0, 1 - y * y))
        out.append((math.cos(g * i) * r, y, math.sin(g * i) * r))
    return out


def _off_face(d, cone=38.0, ymin=-0.7):
    """Direction outside the face cone (front is -Z, the face sits a little above centre) and above the ground."""
    f = np.array([0.0, 0.18, -1.0])
    f /= np.linalg.norm(f)
    return np.degrees(np.arccos(np.clip(np.dot(d, f), -1, 1))) > cone and d[1] > ymin


# ------------------------------------------------------------------------------------------------ slime
@piece("s_blob_slime", (1.9, 1.5, 1.8), tris=1400, kind="unit", res=128, lead=(2.9, 2.3, 2.7))
def s_blob_slime():
    s = ellipsoid(1.45, 1.15, 1.35)
    s = s.su(ellipsoid(0.62, 0.6, 0.62, (0.04, 0.68, 0.18)), 0.42)  # soft peak, set back off the face
    s = s.su(ellipsoid(1.72, 0.34, 1.6, (0, -0.86, 0.02)), 0.3)  # puddle skirt (the Base primitive)
    for i in range(11):
        a = math.radians(40 + i * 28)
        r = 0.36 + 0.08 * math.sin(i * 2.3)
        s = s.su(ellipsoid(r, 0.22, r, (math.sin(a) * 1.62, -0.98, -math.cos(a) * 1.5)), 0.14)
    for a_deg, top, bot in ((72, 0.45, -0.62), (128, 0.62, -0.5), (180, 0.3, -0.7), (232, 0.55, -0.55), (290, 0.4, -0.66), (205, 0.85, -0.2)):
        a = math.radians(a_deg)

        def on(y, push=0.0):
            k = math.sqrt(max(0.0, 1 - (y / 1.15) ** 2))
            return (math.sin(a) * (1.45 * k + push), y, -math.cos(a) * (1.35 * k + push))

        s = s.su(round_cone(on(top, -0.02), on(bot, 0.12), 0.09, 0.17), 0.12)
        s = s.su(sphere(0.2, on(bot - 0.06, 0.16)), 0.1)
    return _keep_above(s, -1.15)


# ------------------------------------------------------------------------------------------------ slug
@piece("s_blob_slug", (1.0, 0.9, 2.7), tris=1300, kind="unit", res=128, lead=(1.5, 0.9, 4.0))
def s_blob_slug():
    s = ellipsoid(0.75, 0.45, 2.0)
    mantle = ellipsoid(0.65, 0.5, 0.95, (0, 0.37, -0.5))
    for i in range(4):  # mantle wrinkles
        z = -1.05 + i * 0.3
        mantle = mantle.ss(capsule((-0.7, 0.62 - abs(i - 1.5) * 0.04, z), (0.7, 0.62 - abs(i - 1.5) * 0.04, z + 0.06), 0.035), 0.05)
    s = s.su(mantle, 0.22)
    s = s.ss(sphere(0.09, (0.6, 0.38, -0.2)), 0.04)  # breathing pore
    s = s.su(ellipsoid(0.5, 0.45, 0.5, (0, 0.27, -1.65)), 0.18)  # head (face)
    s = s.su(ellipsoid(0.425, 0.3, 1.0, (0, -0.13, 1.45)), 0.3)  # tail
    s = s.su(round_cone((0, -0.02, 1.0), (0, -0.28, 2.5), 0.34, 0.05), 0.22)  # tapering tail tip
    s = s.su(capsule((0, 0.22, 0.4), (0, -0.2, 2.35), 0.04), 0.12)  # keel
    s = s.su(ellipsoid(0.84, 0.12, 2.2, (0, -0.36, 0.05)), 0.12)  # flared sole
    s = s.noise(0.012, 7, 3)
    return _keep_above(s, -0.45)


# ------------------------------------------------------------------------------------------------ shells
def _spiral_chain(points, radii):
    """Union of spheres along a sampled spiral (sutures stay creased where whorls touch)."""
    P = np.asarray(points, float)
    R = np.asarray(radii, float)

    def f(p):
        d = np.full(len(p), 1e9)
        for c, r in zip(P, R):
            d = np.minimum(d, np.linalg.norm(p - c, axis=1) - r)
        return d

    return SDF(f)


@piece("s_blob_coil", (1.2, 1.3, 1.3), tris=1200, kind="unit", res=120, lead=(1.6, 1.9, 1.9))
def s_blob_coil():
    # log spiral in the YZ plane, axis X, growing outward; the last whorl ends low at the front (aperture)
    pts, rad = [], []
    n = 160
    t1 = 3.4 * 2 * math.pi
    for i in range(n):
        t = t1 * i / (n - 1)
        R = 0.03 * math.exp(0.142 * t)
        a = -t + 2.4  # winds so the aperture ends low at the front
        r = 0.52 * R * (1 + 0.03 * math.sin(t * 7))
        Rend = 0.03 * math.exp(0.142 * t1)
        pts.append((-0.62 * (1 - R / Rend) ** 1.3, math.sin(a) * R, math.cos(a) * R))
        rad.append(r)
    s = _spiral_chain(pts, rad)
    c, r = np.array(pts[-1]), rad[-1]
    tang = np.array(pts[-1]) - np.array(pts[-4])
    tang /= np.linalg.norm(tang)
    s = s.ss(ellipsoid(r * 0.78, r * 0.86, r * 0.78, tuple(c + tang * r * 0.55)), 0.06)  # aperture
    # centre it on the lead box
    return s.at(0.3, 0.0, 0.0)


@piece("s_blob_spire", (1.3, 1.2, 2.0), tris=1300, kind="unit", res=128, lead=(1.7, 1.6, 3.0))
def s_blob_spire():
    # whorls winding about an axis that runs from the apex (back, +Z, raised) to the body whorl (front)
    ax0, ax1 = np.array([0.0, 0.55, 1.45]), np.array([0.0, -0.05, -0.45])
    u = ax1 - ax0
    L = np.linalg.norm(u)
    u /= L
    v = np.array([1.0, 0.0, 0.0])
    w = np.cross(u, v)
    pts, rad = [], []
    n = 110
    turns = 5.0
    for i in range(n):
        t = i / (n - 1)
        R = 0.05 + 0.5 * t ** 1.35
        a = t * turns * 2 * math.pi
        c = ax0 + u * (L * t ** 1.1) + (v * math.cos(a) + w * math.sin(a)) * R
        pts.append(tuple(c))
        rad.append((0.06 + 0.5 * t ** 1.45) * (1 + 0.05 * max(0.0, math.sin(a * 2)) ** 4))  # shoulder knobs
    s = _spiral_chain(pts, rad)
    s = s.su(round_cone(tuple(ax1 + u * 0.15), tuple(ax1 + u * 0.75 + np.array([0, -0.12, 0])), 0.28, 0.1), 0.15)  # siphonal canal
    # flared lip on the right of the body whorl, hollow aperture under it
    s = s.su(ellipsoid(0.62, 0.55, 0.95, (0.62, -0.18, -0.2)).rot(0, 0, 0), 0.18)
    s = s.ss(ellipsoid(0.35, 0.3, 0.75, (0.48, -0.42, -0.25)), 0.08)
    return s.at(-0.1, -0.1, -0.35)


@piece("s_blob_valve", (1.7, 0.6, 1.5), tris=1100, kind="unit", res=128, lead=(3.0, 0.9, 2.5))
def s_blob_valve():
    def fan(p):
        q = p.copy()
        k = 1 - 0.28 * np.clip(p[:, 2] / 1.25, 0, 1) ** 1.3
        q[:, 0] = p[:, 0] / k
        return q

    outer = ellipsoid(1.5, 0.62, 1.25, (0, -0.2, 0)).warp(fan)
    inner = ellipsoid(1.4, 0.52, 1.15, (0, -0.25, -0.02)).warp(fan)

    def ribs(p):
        phi = np.arctan2(p[:, 0], 1.2 - p[:, 2])
        dist = np.hypot(p[:, 0], 1.2 - p[:, 2])
        rib = np.clip(np.sin(phi * 15), 0, 1) ** 0.8 * np.clip((dist - 0.25) / 0.8, 0, 1)
        ring = 0.006 * np.sin(dist * 26)
        return outer(p) - 0.045 * rib - ring

    s = SDF(ribs).ss(inner, 0.04)
    s = _keep_above(s, -0.2, 0.02)
    s = s.su(ellipsoid(0.32, 0.2, 0.26, (0, 0.2, 0.98)), 0.12)  # umbo
    return s.at(0, 0.0, 0)


# ------------------------------------------------------------------------------------------------ jellyfish
@piece("s_blob_bell", (1.8, 1.3, 1.8), tris=1300, kind="unit", res=128, lead=(3.0, 2.2, 3.0))
def s_blob_bell():
    s = _keep_above(ellipsoid(1.5, 1.1, 1.5), -0.25, 0.08)
    s = s.su(torus(1.36, 0.17).at(0, -0.3, 0), 0.12)
    for i in range(16):
        a = 2 * math.pi * i / 16
        s = s.su(ellipsoid(0.22, 0.13, 0.22, (math.sin(a) * 1.45, -0.42, -math.cos(a) * 1.45)), 0.08)
    s = s.ss(ellipsoid(1.22, 0.82, 1.22, (0, -0.62, 0)), 0.1)  # under-bell hollow
    for i in range(8):  # radial canals on the back half only (the face is on the front)
        a = math.radians(70 + i * 31)
        x, z = math.sin(a), -math.cos(a)
        s = s.ss(capsule((x * 0.35, 1.02, z * 0.35), (x * 1.38, 0.05, z * 1.38), 0.035), 0.05)
    return _keep_above(s, -0.55, 0.03)


# ------------------------------------------------------------------------------------------------ sea star / urchin
@piece("s_blob_star", (2.4, 2.4, 0.6), tris=1400, kind="unit", res=128, lead=(1.7, 1.7, 0.8))
def s_blob_star():
    s = ellipsoid(0.85, 0.85, 0.4)
    arms = None
    for k in range(5):
        a = math.radians(90 + 72 * k)
        d = np.array([math.cos(a), math.sin(a), 0.0])
        arm = round_cone((0, 0, 0), tuple(d * 1.95), 0.5, 0.13)
        arm = arm.warp(lambda p: p * np.array([1.0, 1.0, 1.0 / 0.62]))
        for j in range(5):  # tubercles along the arm, on the front
            t = 0.55 + j * 0.27
            r = 0.13 - j * 0.014
            w = (0.5 - (0.5 - 0.13) * t / 1.95) * 0.62
            for off in (-0.16, 0.0, 0.16) if j < 3 else (0.0,):
                n = np.array([-d[1], d[0], 0.0]) * off * (1 - t / 2.4)
                c = d * t + n + np.array([0, 0, -w * 0.82])
                arm = arm.su(sphere(r * (0.8 if off else 1.0), tuple(c)), 0.05)
        arm = arm.ss(capsule(tuple(d * 0.4 + np.array([0, 0, 0.32])), tuple(d * 1.85 + np.array([0, 0, 0.1])), 0.05), 0.05)  # groove
        arms = arm if arms is None else arms.su(arm, 0.12)
    return s.su(arms, 0.1)


@piece("s_blob_urchin", (2.4, 2.4, 2.4), tris=1500, kind="unit", res=120, lead=(2.4, 2.4, 2.4))
def s_blob_urchin():
    s = sphere(1.2).noise(0.02, 8, 5)
    spines = []
    for d in _fib(90):
        d = np.array(d)
        if not _off_face(d, 40, -0.75):
            continue
        ln = 0.75 + 0.35 * ((hash(tuple(np.round(d, 3))) % 7) / 6.0)
        spines.append(round_cone(tuple(d * 1.1), tuple(d * (1.1 + ln)), 0.075, 0.012))
    for i in range(0, len(spines), 8):
        grp = spines[i:i + 8]
        g = grp[0]
        for o in grp[1:]:
            g = g | o
        s = s.su(g, 0.05)
    return s


# ------------------------------------------------------------------------------------------------ fluff / heap / ghost
@piece("s_blob_fluff", (1.8, 1.8, 1.8), tris=1400, kind="unit", res=120, lead=(2.6, 2.6, 2.6))
def s_blob_fluff():
    s = sphere(1.3)
    for i, d in enumerate(_fib(46)):
        d = np.array(d)
        if not _off_face(d, 34, -0.95):
            continue
        r = 0.34 + 0.06 * math.sin(i * 1.7)
        tuft = ellipsoid(r, r, r * 1.5).rot(0, 0, 0)
        # orient each tuft radially: build in a frame whose z is d
        z = d
        x = np.cross([0, 1, 0], z) if abs(z[1]) < 0.95 else np.cross([1, 0, 0], z)
        x /= np.linalg.norm(x)
        y = np.cross(z, x)
        M = np.stack([x, y, z])
        c = d * 1.18

        def f(p, M=M, c=c, r=r):
            q = (p - c) @ M.T
            return ellipsoid(r, r, r * 1.45)(q)

        s = s.su(SDF(f), 0.16)
    return s.noise(0.03, 10, 7)


@piece("s_blob_heap", (2.3, 1.6, 2.1), tris=1500, kind="unit", res=128, lead=(3.4, 2.4, 3.0))
def s_blob_heap():
    s = ellipsoid(1.7, 1.2, 1.5)
    lumps = [((1.25, 0.25, 0.45), (0.85, 0.8, 0.9)), ((-1.2, 0.05, 0.6), (0.9, 0.75, 0.85)), ((0.3, 0.75, 0.75), (1.0, 0.7, 0.85)),
             ((-0.55, 0.85, 0.35), (0.65, 0.55, 0.65)), ((0.9, -0.75, -0.6), (0.75, 0.5, 0.7)), ((-1.0, -0.75, -0.5), (0.7, 0.5, 0.7)),
             ((0.0, -0.8, 1.05), (1.2, 0.55, 0.7)), ((1.5, -0.55, 0.0), (0.55, 0.6, 0.6))]
    for c, r in lumps:
        s = s.su(ellipsoid(*r, c), 0.22)
    # stitched seams: grooves with cross stitches standing proud
    seams = [((-0.15, 1.25, 0.2), (1.1, 0.75, 0.95)), ((-1.6, 0.4, 0.2), (-0.7, 0.95, 0.95)), ((1.65, 0.3, -0.35), (1.5, -0.6, 0.6))]
    for a, b in seams:
        a, b = np.array(a), np.array(b)
        s = s.ss(capsule(tuple(a), tuple(b), 0.05), 0.04)
        dvec = b - a
        n = np.cross(dvec, [0, 1, 0.3])
        n /= np.linalg.norm(n)
        for j in range(5):
            m = a + dvec * (0.12 + j * 0.19)
            s = s.su(capsule(tuple(m - n * 0.16), tuple(m + n * 0.16), 0.035), 0.015)
    s = s.noise(0.03, 5, 11)
    return _keep_above(s, -1.2)


@piece("s_blob_ghost", (1.6, 2.0, 1.5), tris=1400, kind="unit", res=128, lead=(2.2, 2.6, 2.0))
def s_blob_ghost():
    head = ellipsoid(1.1, 1.3, 1.0)
    skirt = round_cone((0, -0.2, 0.0), (0, -1.75, 0.08), 0.98, 1.3).warp(lambda p: p * np.array([1.0, 1.0, 1.08]))
    s = head.su(skirt, 0.35)
    for i in range(7):  # vertical folds
        a = math.radians(55 + i * 41)
        x, z = math.sin(a), -math.cos(a)
        s = s.su(capsule((x * 0.95, -0.45, z * 0.88), (x * 1.32, -1.7, z * 1.25), 0.1), 0.18)
    s = s.su(ellipsoid(0.32, 0.5, 0.32, (1.12, -0.35, -0.1)).mirror_x(), 0.2)  # arm nubs

    def hem(p):
        a = np.arctan2(p[:, 0], -p[:, 2])
        return -(p[:, 1] - (-1.72 + 0.2 * np.sin(a * 6)))

    s = s.si(SDF(hem), 0.06)
    s = s.ss(round_cone((0, -2.2, 0.05), (0, -0.9, 0.05), 1.05, 0.5), 0.12)  # hollow under the sheet
    return s
