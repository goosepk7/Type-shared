"""Summon set: generic sea creatures (Plans/SeaFish, SeaMammal, Cephalopod, Serpent, Worms).

Every piece is a "unit" sculpt authored in its lead primitive's local frame in studs at a reference lead size
(`lead=`), so one piece fits every profile of a kind: s_aq_fish_body is a tuna, a discus or a gar depending on the
Body ellipsoid the plan builds. Fins are flat 2D outlines (a polygon in the fin's plane) given a thickness that
thins to the rim and ripples along fin rays. Faces stay the builder's parts: heads and bodies keep the lead
ellipsoid untouched on the front where Face puts eyes and mouths.
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF, smax, smin
from . import piece

S = "summon"


# ------------------------------------------------------------------------------------------------ 2D helpers
def poly2d(V):
    """Signed distance (negative inside) to a closed polygon V [(u, v), ...] for arrays u, v."""
    V = np.asarray(V, float)

    def f(u, v):
        P = np.stack([u, v], 1)
        d = np.full(len(u), np.inf)
        s = np.ones(len(u))
        n = len(V)
        for i in range(n):
            a, b = V[i], V[(i + 1) % n]
            e = b - a
            w = P - a
            t = np.clip((w @ e) / (e @ e), 0, 1)
            q = w - t[:, None] * e
            d = np.minimum(d, (q * q).sum(1))
            c1 = P[:, 1] >= a[1]
            c2 = P[:, 1] < b[1]
            c3 = e[0] * w[:, 1] > e[1] * w[:, 0]
            flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
            s = np.where(flip, -s, s)
        return s * np.sqrt(d)

    return f


def bez(p0, p1, p2, n=10):
    """Quadratic Bezier points (excluding the last) for building smooth outlines."""
    p0, p1, p2 = (np.asarray(x, float) for x in (p0, p1, p2))
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    return list((1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2)


def flat_fin(outline, plane="zy", t0=0.05, rim=0.12, rays=0, root=(0.0, 0.0), ray_amp=0.35, tmin=0.25, k=0.02):
    """A fin: 2D outline in `plane` (pair of axes, the third is the thickness axis), thickness t0 at the core
    thinning toward the rim over `rim` studs; optional fin rays fanning from `root`."""
    ax = {"x": 0, "y": 1, "z": 2}
    iu, iv = ax[plane[0]], ax[plane[1]]
    iw = 3 - iu - iv
    d2f = poly2d(outline)

    def f(p):
        u, v = p[:, iu], p[:, iv]
        d2 = d2f(u, v)
        th = t0 * np.clip(-d2 / rim, tmin, 1.0)
        if rays:
            a = np.arctan2(v - root[1], u - root[0])
            th = th * (1 + ray_amp * np.cos(a * rays * 2))
        return smax(d2, np.abs(p[:, iw]) - th, k)

    return SDF(f)


def loft(prof, z0, z1, rx, ry, cy=None):
    """Body of elliptic cross sections along z from z0 to z1: semi-axes rx*prof(u), ry*prof(u), u in 0..1;
    cy(u) shifts the section centre in y. Ends are capped and rounded by the profile itself."""

    def f(p):
        z = p[:, 2]
        u = np.clip((z - z0) / (z1 - z0), 0, 1)
        k = np.maximum(prof(u), 1e-3)
        a, b = rx * k, ry * k
        y = p[:, 1] - (cy(u) if cy else 0)
        d = (np.sqrt((p[:, 0] / a) ** 2 + (y / b) ** 2) - 1) * np.minimum(a, b)
        dz = np.maximum(z0 - z, z - z1)
        return smax(d, dz, 0.04)

    return SDF(f)


def groove(base, fn, depth, width):
    """Push the surface of `base` in by depth * exp(-(fn(p)/width)^2): fn is a signed distance-like field
    whose zero set is the groove line on the surface."""
    return SDF(lambda p: base(p) + depth * np.exp(-(fn(p) / width) ** 2))


# ------------------------------------------------------------------------------------------------ fish body
FB = (0.85, 1.3, 1.68)  # reference Body: W, H, front length (Plans/SeaFish PROFILE.fish)


@piece("s_aq_fish_body", (0.5, 0.72, 0.92), tris=900, kind="unit", lead=FB, set=S, smooth=3)
def s_aq_fish_body():
    """Fish front mass (lead Body): the lead ellipsoid with a gill cover (an arc groove behind a raised cheek
    plate), a dorsal keel toward the back and a soft belly line; the front stays the lead for the face."""
    rx, ry, rz = FB[0] / 2, FB[1] / 2, FB[2] / 2
    base = ellipsoid(rx, ry, rz)

    def gill(p):
        y = p[:, 1] / ry
        zc = -0.12 * rz + 0.18 * rz * y * y
        return (p[:, 2] - zc) * (np.abs(p[:, 0]) > rx * 0.35)

    def cheek(p):
        y = p[:, 1] / ry
        zc = -0.32 * rz + 0.18 * rz * y * y
        return p[:, 2] - zc

    s = groove(base, gill, 0.022, 0.035)
    s = SDF(lambda p, s=s: s(p) - 0.018 * np.exp(-(cheek(p) / 0.12) ** 2) * np.clip(np.abs(p[:, 0]) / rx - 0.4, 0, 1) * (p[:, 1] < ry * 0.5))
    # dorsal keel over the back half
    keel = SDF(lambda p: s(p) - 0.03 * np.exp(-(p[:, 0] / 0.06) ** 2) * np.clip(p[:, 1] / ry, 0, 1) * np.clip((p[:, 2] + 0.2) / rz, 0, 1))
    return keel


@piece("s_aq_fish_head", (0.5, 0.72, 0.92), tris=900, kind="unit", lead=FB, set=S, smooth=3)
def s_aq_fish_head():
    """Big-headed fish front (deep-sea, puffers, lumpy fish, lead Body): a heavy brow over the eyes, lumpy
    tubercles on the crown and cheeks, a deep gill arc."""
    rx, ry, rz = FB[0] / 2, FB[1] / 2, FB[2] / 2
    base = ellipsoid(rx, ry, rz)

    def gill(p):
        y = p[:, 1] / ry
        return (p[:, 2] - (0.05 * rz + 0.15 * rz * y * y)) * (np.abs(p[:, 0]) > rx * 0.3)

    s = groove(base, gill, 0.03, 0.04)
    rng = np.random.default_rng(3)
    for _ in range(9):
        a = rng.uniform(0.25, 1.2)
        y = rng.uniform(-0.1, 0.8)
        z = rng.uniform(-0.2, 0.7)
        q = np.array([np.sin(a) * rx, y * ry, z * rz])
        n = q / np.linalg.norm(q / np.array([rx, ry, rz]))
        for sx in (1, -1):
            c = (sx * n[0] * 0.97, n[1] * 0.97, n[2] * 0.97)
            s = s.su(sphere(0.045, c), 0.05)
    # brow ridge over the eye line
    s = s.su(ellipsoid(rx * 0.55, 0.06, 0.1, (0, ry * 0.62, -rz * 0.55)).mirror_x().at(0, 0, 0), 0.06)
    return s


R_REAR = (0.714, 1.144, 1.79)  # reference Rear: W*0.84, H*0.88, L*0.64


def _rear_prof(u):
    return 0.27 + 0.73 * np.sqrt(np.clip(1 - u ** 1.7, 0, 1)) * (1 - 0.15 * u)


@piece("s_aq_fish_tail", (0.42, 0.62, 1.0), tris=700, kind="unit", lead=R_REAR, set=S, smooth=3)
def s_aq_fish_tail():
    """Fish tail half (lead Rear, member Peduncle): tapers from the girth to a narrow, laterally flattened
    caudal peduncle with keels, so the body reads as one spindle with the front sculpt."""
    rx, ry, rz = R_REAR[0] / 2, R_REAR[1] / 2, R_REAR[2] / 2
    body = loft(lambda u: np.where(u < 0.12, np.sqrt(np.clip(1 - ((0.12 - u) / 0.12) ** 2, 0, 1)) * _rear_prof(0.12), _rear_prof(u)),
                -rz * 0.98, rz * 1.02, rx * 0.95, ry * 0.95)
    # lateral keels on the peduncle
    keel = SDF(lambda p: body(p) - 0.03 * np.exp(-(p[:, 1] / 0.05) ** 2) * np.clip((p[:, 2] - rz * 0.4) / (rz * 0.5), 0, 1))
    return keel


# ------------------------------------------------------------------------------------------------ fins
CF = (0.16, 0.546, 0.39)  # reference forked-tail root: t*1.6, h*0.42, l*0.5 (h = 1.3, l = 0.84)


def _fork(h, l, sweep, notch, lobe_w):
    """Forked caudal outline in (z, y): root at the front, two lobes sweeping back."""
    top = (l * 0.75, h * 0.5)
    bot = (l * 0.72, -h * 0.47)
    pts = []
    pts += bez((-l * 0.12, -h * 0.13), (l * 0.25, -h * 0.2), bot, 8)
    pts += bez(bot, (l * 0.5 - lobe_w * 0.2, -h * 0.25), (l * notch, 0.0), 8)
    pts += bez((l * notch, 0.0), (l * 0.5 - lobe_w * 0.2, h * 0.27), top, 8)
    pts += bez(top, (l * sweep, h * 0.2), (-l * 0.12, h * 0.13), 8)
    return pts


@piece("s_aq_caudal_fork", (0.12, 0.8, 0.75), tris=500, kind="unit", lead=CF, set=S, smooth=2)
def s_aq_caudal_fork():
    """Forked tail fin (lead TailFin root, members the two lobes): a fleshy root, two swept lobes with a V
    notch, rays fanning from the root, rims thinning out."""
    h, l = 1.3, 0.84
    o = _fork(h, l, 0.28, 0.42, 0.3)
    fin = flat_fin(o, "zy", t0=0.05, rim=0.1, rays=9, root=(-l * 0.2, 0.0), ray_amp=0.3, tmin=0.3)
    return fin.su(ellipsoid(0.07, h * 0.16, l * 0.22, (0, 0, -l * 0.05)), 0.05)


@piece("s_aq_caudal_lunate", (0.12, 1.0, 0.8), tris=500, kind="unit", lead=CF, set=S, smooth=2)
def s_aq_caudal_lunate():
    """Crescent tail of fast swimmers (tuna, marlin, ichthyosaurs; lead TailFin root): narrow stiff
    sickle lobes, a shallow notch."""
    h, l = 1.75, 0.84
    o = _fork(h, l, 0.45, 0.32, 0.18)
    fin = flat_fin(o, "zy", t0=0.055, rim=0.08, rays=7, root=(-l * 0.2, 0.0), ray_amp=0.2, tmin=0.35)
    return fin.su(ellipsoid(0.07, 0.2, l * 0.2, (0, 0, -l * 0.05)), 0.05)


CFAN = (0.1, 1.24, 0.76)  # reference fan tail: t, h*0.95, l*0.9


@piece("s_aq_caudal_fan", (0.1, 0.85, 0.65), tris=500, kind="unit", lead=CFAN, set=S, smooth=2)
def s_aq_caudal_fan():
    """Rounded fan tail (lead TailFin): a broad fan from a narrow root, scalloped trailing edge, strong rays."""
    h, l = CFAN[1], CFAN[2]
    root = (-l * 0.5, 0.0)
    pts = []
    n = 40
    for i in range(n + 1):
        a = -1.0 + 2.0 * i / n
        R = l * 1.0 * (1 + 0.05 * np.cos(a * 22)) * (1 - 0.08 * a * a)
        pts.append((root[0] + np.cos(a) * R, np.sin(a) * h * 0.62))
    pts.append((root[0] + 0.02, -h * 0.06))
    pts.append((root[0] + 0.02, h * 0.06))
    return flat_fin(pts, "zy", t0=0.04, rim=0.12, rays=11, root=root, ray_amp=0.4, tmin=0.25)


DF = (0.1, 0.845, 0.84)  # reference Dorsal: t, h*1.3, l (h = 0.65, l = 0.84)


@piece("s_aq_dorsal", (0.1, 0.5, 0.5), tris=360, kind="unit", lead=DF, set=S, smooth=2)
def s_aq_dorsal():
    """Soft-rayed dorsal fin (lead Dorsal, also the anal fin upside down and whale / dolphin dorsals): base
    sunk in the back, a curved leading edge rising to a swept tip, a concave trailing edge."""
    h, l = DF[1], DF[2]
    b = -h * 0.32
    pts = []
    pts += bez((-l * 0.48, b), (-l * 0.2, h * 0.3), (l * 0.12, h * 0.43), 12)
    pts += bez((l * 0.12, h * 0.43), (l * 0.12, h * 0.05), (l * 0.46, b + 0.02), 10)
    pts += [(l * 0.46, b - 0.1), (-l * 0.48, b - 0.1)]
    return flat_fin(pts, "zy", t0=0.05, rim=0.1, rays=8, root=(0.0, b - 0.3), ray_amp=0.3, tmin=0.3)


@piece("s_aq_dorsal_spiny", (0.1, 0.55, 0.5), tris=500, kind="unit", lead=DF, set=S, smooth=2)
def s_aq_dorsal_spiny():
    """Spiny dorsal fin (perch, bass, lionfish, sailfish; lead Dorsal): a row of stiff spines standing proud
    of a scalloped membrane, tallest in front."""
    h, l = DF[1], DF[2]
    b = -h * 0.32
    n = 8
    pts = [(-l * 0.48, b)]
    for i in range(n):
        z = -l * 0.42 + i * (l * 0.86) / (n - 1)
        top = b + (h * 0.75) * (1 - 0.55 * i / (n - 1))
        pts.append((z - l * 0.03, top - h * 0.1))
        pts.append((z, top))
        pts.append((z + l * 0.03, top - h * 0.13))
    pts += [(l * 0.47, b + 0.08), (l * 0.47, b - 0.1), (-l * 0.48, b - 0.1)]
    fin = flat_fin(pts, "zy", t0=0.035, rim=0.06, tmin=0.4)
    for i in range(n):
        z = -l * 0.42 + i * (l * 0.86) / (n - 1)
        top = b + (h * 0.75) * (1 - 0.55 * i / (n - 1))
        fin = fin.su(round_cone((0, b, z - 0.02), (0, top, z), 0.022, 0.008), 0.015)
    return fin


# ------------------------------------------------------------------------------------------------ flatfish
FF = (1.9, 0.5, 2.52)


@piece("s_aq_flatfish", (1.25, 0.32, 1.42), tris=1000, kind="unit", lead=FF, set=S, smooth=3)
def s_aq_flatfish():
    """Flatfish (halibut, flounder; lead Disc, members the fringe fins and underside): an oval body domed on
    the eyed side, a fringe fin all round with rays, a raised head ridge and a lateral line arching over the
    pectoral."""
    rx, ry, rz = 0.72, 0.22, 1.12
    body = ellipsoid(rx, ry, rz).su(ellipsoid(0.32, 0.26, 0.4, (0.08, 0.04, -0.7)), 0.15)
    # fringe: an outline offset from the body in the xz plane, thin
    outline = []
    for i in range(48):
        a = 2 * np.pi * i / 48
        r = 1 + 0.02 * np.cos(a * 18)
        outline.append((np.cos(a) * (rx + 0.42) * r, np.sin(a) * (rz + 0.18) * r))
    fringe = flat_fin(outline, "xz", t0=0.04, rim=0.18, rays=14, root=(0, 0), ray_amp=0.2, tmin=0.3)
    s = body.su(fringe, 0.1)
    # lateral line: a shallow groove arching up over the pectoral
    s = groove(s, lambda p: p[:, 0] - 0.12 * np.exp(-((p[:, 2] + 0.5) / 0.35) ** 2), 0.012, 0.025)
    return s


@piece("s_aq_flat_tail", (0.7, 0.08, 0.45), tris=360, kind="unit", lead=(1.18, 0.1, 0.66), set=S, smooth=2)
def s_aq_flat_tail():
    """Flatfish tail fan lying flat (lead TailFin, thin in y): a broad fan, rays, a straight-ish edge."""
    w, l = 1.18, 0.66
    pts = bez((-0.08, -l * 0.48), (w * 0.3, -l * 0.3), (w * 0.52, l * 0.46), 10)
    pts += bez((w * 0.52, l * 0.46), (0, l * 0.36), (-w * 0.52, l * 0.46), 10)
    pts += bez((-w * 0.52, l * 0.46), (-w * 0.3, -l * 0.3), (0.08, -l * 0.48), 10)
    return flat_fin(pts, "xz", t0=0.04, rim=0.1, rays=9, root=(0, -l * 0.6), ray_amp=0.35, tmin=0.3)


# ------------------------------------------------------------------------------------------------ rays
RB = (1.68, 0.64, 2.02)


@piece("s_aq_ray_body", (0.9, 0.36, 1.1), tris=900, kind="unit", lead=RB, set=S, smooth=3)
def s_aq_ray_body():
    """Ray body disc (lead Disc, member Underside): a raised dome over the spine with a ridge running back
    into the tail root, eye bosses with spiracle pits behind them, a thin flared rim the wings grow out of."""
    rx, ry, rz = RB[0] / 2, RB[1] / 2, RB[2] / 2
    dome = ellipsoid(rx * 0.75, ry, rz)
    rim = ellipsoid(rx, ry * 0.45, rz * 0.97, (0, -ry * 0.2, 0))
    s = dome.su(rim, 0.15)
    s = s.su(round_cone((0, ry * 0.55, -rz * 0.2), (0, ry * 0.25, rz * 1.0), 0.09, 0.07), 0.12)
    s = s.su(ellipsoid(0.13, 0.1, 0.16, (rx * 0.3, ry * 0.75, -rz * 0.45)).mirror_x(), 0.06)
    s = s.ss(sphere(0.06, (rx * 0.32, ry * 0.88, -rz * 0.22)).mirror_x(), 0.04)
    return s


RW = (2.05, 0.14, 1.68)


def _wing(round_=False):
    w, l = RW[0], RW[2]
    x0 = -w * 0.5
    if round_:
        pts = bez((x0, -l * 0.42), (w * 0.35, -l * 0.6), (w * 0.47, 0.0), 14)
        pts += bez((w * 0.47, 0.0), (w * 0.35, l * 0.6), (x0, l * 0.42), 14)
    else:
        tip = (w * 0.5, l * 0.18)
        pts = bez((x0, -l * 0.46), (w * 0.05, -l * 0.42), tip, 14)
        pts += bez(tip, (w * 0.1, l * 0.18), (x0, l * 0.46), 14)
    return flat_fin(pts, "xz", t0=0.07, rim=0.5, tmin=0.18, k=0.03)


@piece("s_aq_ray_wing", (1.1, 0.1, 0.92), tris=500, kind="unit", lead=RW, set=S, smooth=3, mirror=True)
def s_aq_ray_wing():
    """Ray wing (lead RayWing, right side; _l mirrored): pointed pectoral wing, the leading edge curving
    out to a swept tip, a concave trailing edge, thick at the root and thin at the rim."""
    return _wing(False)


@piece("s_aq_ray_wing_round", (1.1, 0.1, 0.92), tris=500, kind="unit", lead=RW, set=S, smooth=3, mirror=True)
def s_aq_ray_wing_round():
    """Round ray wing (electric rays, river stingrays): half of a round disc."""
    return _wing(True)


# ------------------------------------------------------------------------------------------------ whales, seals
WB = (1.55, 1.6, 2.76)


@piece("s_aq_whale_body", (0.85, 0.88, 1.5), tris=1100, kind="unit", lead=WB, set=S, smooth=3)
def s_aq_whale_body():
    """Whale front (lead Body, members Belly / Melon): the lead ellipsoid with a flatter belly, a mouth line
    sweeping back from the snout under the eye, a blowhole on top and long throat grooves underneath."""
    rx, ry, rz = WB[0] / 2, WB[1] / 2, WB[2] / 2
    s = ellipsoid(rx, ry, rz).su(ellipsoid(rx * 0.92, ry * 0.85, rz * 0.9, (0, -ry * 0.1, rz * 0.08)), 0.2)
    # mouth line: on the side, from near the front down and back
    s = groove(s, lambda p: (p[:, 1] + ry * 0.32 - 0.12 * (p[:, 2] / rz + 1)) * (np.abs(p[:, 0]) > rx * 0.45) * (p[:, 2] > -rz * 0.62) * (p[:, 2] < rz * 0.1) + (1 - (np.abs(p[:, 0]) > rx * 0.45) * (p[:, 2] > -rz * 0.62) * (p[:, 2] < rz * 0.1)) * 9, 0.02, 0.025)
    # throat grooves
    s = SDF(lambda p, s=s: s(p) + 0.012 * np.clip(-(p[:, 1] + ry * 0.45) / (ry * 0.3), 0, 1) * np.clip(-(p[:, 2] - rz * 0.3) / rz, 0, 1) * (0.5 + 0.5 * np.cos(p[:, 0] / 0.07 * np.pi)))
    s = s.ss(ellipsoid(0.07, 0.06, 0.03, (0, ry * 0.97, -rz * 0.25)), 0.03)
    return s


@piece("s_aq_fluke", (1.05, 0.1, 0.5), tris=420, kind="unit", lead=(1.93, 0.14, 0.78), set=S, smooth=2)
def s_aq_fluke():
    """Whale fluke (lead Fluke, flat in y): two lobes with swept pointed tips and a notch in the middle of
    the trailing edge, thick along the leading edge."""
    w, l = 1.93, 0.78
    tip = (w * 0.5, l * 0.32)
    pts = bez((0.0, -l * 0.45), (w * 0.3, -l * 0.25), tip, 12)
    pts += bez(tip, (w * 0.25, l * 0.1), (0.0, l * 0.28), 10)
    pts += bez((0.0, l * 0.28), (-w * 0.25, l * 0.1), (-tip[0], tip[1]), 10)
    pts += bez((-tip[0], tip[1]), (-w * 0.3, -l * 0.25), (0.0, -l * 0.45), 12)
    return flat_fin(pts, "xz", t0=0.07, rim=0.3, tmin=0.18).su(ellipsoid(0.16, 0.06, l * 0.35, (0, 0, -l * 0.2)), 0.08)


@piece("s_aq_paddle", (0.65, 0.1, 0.5), tris=360, kind="unit", lead=(1.14, 0.16, 0.91), set=S, smooth=2)
def s_aq_paddle():
    """Manatee paddle tail (lead Paddle, flat in y): a round spoon with a thick core."""
    w, l = 1.14, 0.91
    pts = []
    for i in range(36):
        a = 2 * np.pi * i / 36
        pts.append((np.cos(a) * w * 0.5, np.sin(a) * l * 0.5 * (1 + 0.15 * np.sin(a))))
    return flat_fin(pts, "xz", t0=0.08, rim=0.35, tmin=0.25)


@piece("s_aq_flipper", (0.68, 0.1, 0.28), tris=400, kind="unit", lead=(1.2, 0.16, 0.4), set=S, smooth=2, mirror=True)
def s_aq_flipper():
    """Flipper (whales, seals, plesiosaurs; lead Flipper, right side, out along +x, flat in y): a rounded
    root, a broad paddle tapering to a soft tip, the leading edge thicker, knuckle bumps of the finger bones."""
    w, l = 1.2, 0.4
    x0 = -w * 0.5
    pts = bez((x0, -l * 0.3), (0.0, -l * 0.62), (w * 0.5, -l * 0.05), 12)
    pts += bez((w * 0.5, -l * 0.05), (w * 0.1, l * 0.55), (x0, l * 0.32), 12)
    s = flat_fin(pts, "xz", t0=0.075, rim=0.22, tmin=0.25)
    for i in range(3):
        x = x0 + w * (0.35 + i * 0.18)
        s = s.su(ellipsoid(0.07, 0.04, 0.05, (x, 0.04, -l * 0.08)), 0.05)
    return s


SB = (1.15, 1.2, 1.98)


@piece("s_aq_seal_body", (0.65, 0.75, 1.25), tris=1000, kind="unit", lead=SB, set=S, smooth=3)
def s_aq_seal_body():
    """Seal chest (lead Body, member Belly): a blubbery barrel with shoulders over the fore flippers, a thick
    neck running up and forward into the head, a fold of fat at the throat. Plesiosaurs use it too."""
    rx, ry, rz = SB[0] / 2, SB[1] / 2, SB[2] / 2
    s = ellipsoid(rx, ry, rz)
    s = s.su(round_cone((0, ry * 0.1, -rz * 0.5), (0, ry * 0.45, -rz * 1.08), rx * 0.78, rx * 0.6), 0.25)
    s = s.su(ellipsoid(rx * 0.35, ry * 0.4, rz * 0.35, (rx * 0.55, -ry * 0.1, -rz * 0.3)).mirror_x(), 0.2)
    s = groove(s, lambda p: (p[:, 2] + rz * 0.7 - 0.25 * p[:, 1]) * (p[:, 1] < 0), 0.025, 0.04)
    return s


SH = (0.94, 0.92, 1.56)


@piece("s_aq_seal_hips", (0.52, 0.52, 0.95), tris=700, kind="unit", lead=SH, set=S, smooth=3)
def s_aq_seal_hips():
    """Seal hindquarters (lead Hips): tapering from the waist to the narrow root of the hind flippers, flat
    underneath, with a slight hip bulge."""
    rx, ry, rz = SH[0] / 2, SH[1] / 2, SH[2] / 2
    body = loft(lambda u: np.where(u < 0.2, np.sqrt(np.clip(1 - ((0.2 - u) / 0.2) ** 2, 0, 1)), 1.0) * (1 - 0.68 * u ** 1.4),
                -rz, rz, rx, ry, cy=lambda u: -ry * 0.12 * u)
    return body.su(ellipsoid(rx * 0.3, ry * 0.4, rz * 0.3, (rx * 0.5, -ry * 0.15, rz * 0.05)).mirror_x(), 0.15)


# ------------------------------------------------------------------------------------------------ cephalopods
SQ = (1.05, 3.4, 1.05)


@piece("s_aq_squid_mantle", (1.25, 1.85, 0.6), tris=1000, kind="unit", lead=SQ, set=S, smooth=3)
def s_aq_squid_mantle():
    """Squid mantle (lead Mantle, local +Y to the tip): a torpedo with an open collar at the head end, tapering
    to a point, and two arrowhead fins at the tip spreading in the x-y plane."""
    r = SQ[0] / 2
    L = SQ[1] / 2
    prof = lambda u: np.clip(1 - u, 0, 1) ** 0.45 * (0.88 + 0.12 * np.sin(np.pi * np.clip(u * 2, 0, 1)))
    lo = loft(prof, -L, L * 1.02, r, r)
    body = SDF(lambda p: lo(p[:, [0, 2, 1]]))
    # collar rim at the head end
    body = body.su(torus(r * 0.9, 0.05).at(0, -L * 0.93, 0), 0.05)
    fins = []
    pts = bez((0.0, L * 0.25), (r * 1.6, L * 0.45), (r * 2.25, L * 0.62), 10)
    pts += bez((r * 2.25, L * 0.62), (r * 1.5, L * 0.85), (0.0, L * 1.02), 10)
    pts += bez((0.0, L * 1.02), (-r * 1.5, L * 0.85), (-r * 2.25, L * 0.62), 10)
    pts += bez((-r * 2.25, L * 0.62), (-r * 1.6, L * 0.45), (0.0, L * 0.25), 10)
    fin = flat_fin(pts, "xy", t0=0.06, rim=0.3, tmin=0.2)
    return body.su(fin, 0.12)


CB = (1.75, 1.05, 3.0)


@piece("s_aq_cuttle_body", (1.3, 0.6, 1.62), tris=1000, kind="unit", lead=CB, set=S, smooth=3)
def s_aq_cuttle_body():
    """Cuttlefish mantle (lead Shield, member Skirt): a broad oval shield, highest over the cuttlebone, with a
    thin wavy fin skirt running all the way round its lower edge."""
    rx, ry, rz = CB[0] / 2, CB[1] / 2, CB[2] / 2
    s = ellipsoid(rx, ry, rz).su(ellipsoid(rx * 0.5, ry * 1.08, rz * 0.8, (0, 0.0, 0.05)), 0.2)
    outline = []
    for i in range(60):
        a = 2 * np.pi * i / 60
        outline.append((np.cos(a) * (rx + 0.35), np.sin(a) * (rz + 0.12)))
    skirt = flat_fin(outline, "xz", t0=0.035, rim=0.25, tmin=0.3)
    skirt = skirt.warp(lambda p: p - np.stack([np.zeros(len(p)), -ry * 0.1 + 0.06 * np.sin(p[:, 2] * 9) * np.clip(np.abs(p[:, 0]) - rx * 0.7, 0, 1) * 3, np.zeros(len(p))], 1))
    return s.su(skirt, 0.08)


def _spiral_shell(ribs=0.03, rib_n=26, keel=False, flare=1.0):
    k = np.log(3.0) / (2 * np.pi)
    turns = 2.6 * np.pi
    c = np.array([0.0, 0.2, 0.2])
    phi_end = np.arctan2(-0.75, -0.65)
    pts, rad = [], []
    n = 40
    R_end = 1.3
    for i in range(n + 1):
        s = i / n
        phi = phi_end + (1 - s) * turns
        r = R_end * np.exp(-k * (1 - s) * turns)
        pts.append(c + np.array([0.0, np.cos(phi) * r, np.sin(phi) * r]))
        rad.append(max(0.47 * r * (1 + (flare - 1) * s ** 6), 0.02))
    shell = tube(pts, rad, k=0.0)

    def f(p):
        d = shell(p)
        q = p - c
        phi = np.arctan2(q[:, 2], q[:, 1])
        d = d - ribs * np.maximum(np.cos(phi * rib_n), 0) ** 4
        if keel:
            d = d - 0.05 * np.exp(-(p[:, 0] / 0.05) ** 2)
        return d

    s = SDF(f)
    # aperture: hollow the open end a little
    end = pts[-1]
    s = s.ss(ellipsoid(0.3, rad[-1] * 0.8, rad[-1] * 0.8, tuple(end + np.array([0, -0.1, -0.15]))), 0.08)
    return s


@piece("s_aq_nautilus_shell", (0.95, 1.6, 1.6), tris=1300, kind="unit", lead=(1.0, 3.0, 3.0), set=S, smooth=3)
def s_aq_nautilus_shell():
    """Nautilus / ammonite shell (lead Shell, coil in the y-z plane): a logarithmic spiral tube coiling up over
    the head, growth ribs, the aperture opening forward and down where the head comes out."""
    return _spiral_shell(0.025, 30)


@piece("s_aq_argonaut_shell", (0.95, 1.6, 1.6), tris=1300, kind="unit", lead=(1.0, 3.0, 3.0), set=S, smooth=3)
def s_aq_argonaut_shell():
    """Argonaut egg case (lead Shell): a papery spiral with strong radial ribs, a keel of knobs and a wide
    flared aperture."""
    return _spiral_shell(0.06, 22, keel=True, flare=1.35)


@piece("s_aq_orthocone", (1.1, 2.6, 1.1), tris=800, kind="unit", lead=(1.9, 4.85, 1.9), set=S, smooth=3)
def s_aq_orthocone():
    """Straight-shelled cephalopod (cameroceras; lead Cone, local +Y to the tip): a long tapering cone with
    septum rings, the open aperture at -Y."""
    L = 4.85 / 2

    def f(p):
        y = p[:, 1]
        u = np.clip((y + L) / (2 * L), 0, 1)
        r = 0.95 * (1 - 0.9 * u) + 0.03 * np.maximum(np.cos(u * 60), 0) ** 3
        d = np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2) - r
        return smax(d, np.maximum(-L - y, y - L), 0.08)

    s = SDF(f)
    return s.ss(cylinder(0.7, 0.3, axis=1).at(0, -L, 0), 0.08)


@piece("s_aq_brain", (1.35, 1.0, 1.3), tris=1300, kind="unit", lead=(2.5, 1.9, 2.4), set=S, smooth=2)
def s_aq_brain():
    """Brain (tentacle aliens; lead Mantle): two hemispheres split by a deep fissure, folded gyri all over."""
    rx, ry, rz = 1.25, 0.95, 1.2
    s = ellipsoid(rx, ry, rz)
    s = s.ss(SDF(lambda p: np.abs(p[:, 0]) - 0.04), 0.1)

    def f(p):
        d = s(p)
        g = np.sin(p[:, 0] * 9 + np.sin(p[:, 2] * 7) * 1.6) * np.sin(p[:, 2] * 8 + np.sin(p[:, 1] * 6) * 1.4)
        return d + 0.035 * np.abs(g) - 0.02

    return SDF(f)
