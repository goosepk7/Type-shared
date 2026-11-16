"""Summon set: hero pieces for the signature words (rocket, ufo, cannon, tank, castle, octopus / kraken, wizard,
knight, sword). Each fills the box of ONE named primitive of the signature build (MeshMap.NAMED), in
that primitive's own frame, so it follows every seed, size and animation of the part it replaces.
Cylinder frames run along X (the builder points +X up for towers and rockets, toward the muzzle for guns).
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from . import piece

import direct


def _rings(t0, t1, r, n, depth=0.02, gap=0.012):
    """Lathe profile points for n panels between t0 and t1 at radius r, separated by shallow grooves."""
    out = []
    for i in range(n):
        a, b = t0 + (t1 - t0) * i / n, t0 + (t1 - t0) * (i + 1) / n
        out += [(a + gap, r, -0.4, 1), (a + 2.5 * gap, r, 0, 1), (b - 2.5 * gap, r, 0, 1), (b - gap, r, 0.4, 1)]
        if i < n - 1:
            out += [(b, r - depth, 0, 1)]
    return out


def _prism(poly, y0, y1):
    """Flat-shaded prism of a convex XZ polygon between y0 and y1."""
    import trimesh
    V, N, F = [], [], []
    n = len(poly)
    for i in range(n):
        (x0, z0), (x1, z1) = poly[i], poly[(i + 1) % n]
        nn = np.array([z1 - z0, 0, -(x1 - x0)], float)
        nn /= np.linalg.norm(nn)
        b = len(V)
        V += [(x0, y0, z0), (x1, y0, z1), (x1, y1, z1), (x0, y1, z0)]
        N += [nn] * 4
        F += [(b, b + 2, b + 1), (b, b + 3, b + 2)]
    for y, s in ((y0, -1), (y1, 1)):
        b = len(V)
        V += [(x, y, z) for x, z in poly]
        N += [(0, s, 0)] * n
        for i in range(1, n - 1):
            F.append((b, b + i, b + i + 1) if s < 0 else (b, b + i + 1, b + i))
    m = trimesh.Trimesh(np.array(V, float), np.array(F), process=False)
    if m.volume < 0:
        F = [f[::-1] for f in F]
    return direct._finish(np.array(V, float), np.array(N, float), np.array(F))


@piece("s_rocket_body", (1.5, 0.6, 0.6), tris=420, fit=(2.8, 1.0, 1.0))
def s_rocket_body():
    """Rocket fuselage (cylinder frame, +X up): riveted hull panels, a boat-tail above the nozzle, flat ends."""
    prof = [(-1.4, 0, -1, 0), (-1.4, 0.4, -1, 0), (-1.38, 0.42, -0.7, 0.7), (-1.1, 0.5, -0.3, 1)]
    prof += _rings(-1.1, 1.4, 0.5, 2, depth=0.018, gap=0.014)
    prof += [(1.4, 0.48, 1, 0), (1.4, 0, 1, 0)]
    return direct.lathe(prof, 16, axis=0)


@piece("s_nose_cone", (0.6, 0.75, 0.6), tris=300, fit=(1.0, 1.3, 1.0))
def s_nose_cone():
    """Rocket nose (ellipsoid frame, +Y up): ogive with a collar at the base and a ball tip."""
    return direct.revolve([(-0.65, 0), (-0.6, 0.42), (-0.4, 0.5), (-0.1, 0.45), (0.25, 0.3), (0.5, 0.12), (0.65, 0)], segs=14, spline=2)


@piece("s_nozzle", (0.4, 0.6, 0.6), tris=320, fit=(0.6, 1.0, 1.0))
def s_nozzle():
    """Engine bell (cylinder frame, +X = toward the body): flared skirt with a hollow throat and a stiffening ring."""
    prof = [(-0.12, 0, 1, 0), (-0.12, 0.2, 1, 0), (-0.3, 0.4, 0.8, -0.6), (-0.3, 0.5, -1, 0), (-0.27, 0.5, 0, 1), (-0.05, 0.4, 0.45, 1), (0.02, 0.4, 0, 1),
            (0.04, 0.44, -0.6, 0.7), (0.08, 0.44, 0.6, 0.7), (0.1, 0.33, 0.4, 1), (0.3, 0.3, 0.2, 1), (0.3, 0, 1, 0)]
    return direct.lathe(prof, 18, axis=0)


@piece("s_gun_barrel", (1.7, 0.6, 0.6), tris=420, fit=(3.2, 1.0, 1.0))
def s_gun_barrel():
    """Cannon barrel (cylinder frame, +X = muzzle): thick breech, reinforce rings, taper toward the muzzle."""
    prof = [(-1.6, 0, -1, 0), (-1.6, 0.44, -1, 0), (-1.56, 0.5, -0.6, 0.8), (-1.3, 0.5, 0, 1), (-1.26, 0.455, 0.5, 0.8), (-0.6, 0.44, 0.03, 1),
            (-0.58, 0.49, -0.6, 0.8), (-0.44, 0.49, 0.6, 0.8), (-0.42, 0.43, 0.03, 1), (0.5, 0.4, 0.03, 1), (0.52, 0.45, -0.6, 0.8), (0.64, 0.45, 0.6, 0.8),
            (0.66, 0.39, 0.03, 1), (1.6, 0.36, 0.03, 1), (1.6, 0, 1, 0)]
    return direct.lathe(prof, 20, axis=0)


@piece("s_muzzle", (0.3, 0.6, 0.6), tris=320, fit=(0.3, 1.0, 1.0))
def s_muzzle():
    """Muzzle swell (cylinder frame, +X = out): rolled lip around a recessed bore."""
    prof = [(-0.15, 0, -1, 0), (-0.15, 0.4, -1, 0), (-0.12, 0.46, -0.6, 0.8), (0.02, 0.5, 0, 1), (0.1, 0.5, 0.3, 1), (0.15, 0.44, 1, 0.2), (0.15, 0.34, 1, 0),
            (0.1, 0.3, 0.6, -0.8), (-0.08, 0.27, 0.2, -1), (-0.08, 0, 1, 0)]
    return direct.lathe(prof, 20, axis=0)


@piece("s_tread_run", (0.5, 0.6, 2.0), tris=560, fit=(0.63, 1.0, 3.6))
def s_tread_run():
    """Track run (block frame, long in Z, ground on -Y): belt with raised grousers on the top and bottom runs."""
    parts = [direct.rounded_box((0.63, 0.9, 3.6), 0.04, seg=0)]
    n = 6
    for i in range(n):
        z = -1.8 + 3.6 * (i + 0.5) / n
        for y in (-0.455, 0.455):
            parts.append(direct.moved(_prism([(-0.315, -0.15), (0.315, -0.15), (0.315, 0.15), (-0.315, 0.15)], -0.045, 0.045), (0, y, z)))
    return direct.merge(*parts)


@piece("s_tread_end", (0.4, 0.6, 0.6), tris=520, fit=(0.62, 1.0, 1.0))
def s_tread_end():
    """Track end / sprocket (cylinder frame, axis X): belt wrap with grousers around the rim."""
    parts = [direct.bevel_cylinder(0.62, 0.45, 0.04, segs=16)]
    for i in range(8):
        a = (i + 0.5) / 8 * 2 * np.pi
        c, s = np.cos(a), np.sin(a)
        rot = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
        parts.append(direct.moved(_prism([(-0.31, -0.085), (0.31, -0.085), (0.31, 0.085), (-0.31, 0.085)], -0.045, 0.045), (0, 0.455 * c, 0.455 * s), rot=rot))
    return direct.merge(*parts)


@piece("s_saucer", (0.6, 0.15, 0.6), tris=520, fit=(1.0, 0.18, 1.0))
def s_saucer():
    """Flying saucer disc (ellipsoid frame, +Y up): lens hull with a hard rim band, stepped upper deck, belly ring."""
    prof = [(-0.09, 0, -1, 0), (-0.085, 0.2, -1, 0.1), (-0.07, 0.3, -1, 0.3), (-0.075, 0.33, -1, 0), (-0.055, 0.36, -0.8, 0.5), (-0.02, 0.47, -0.9, 0.4),
            (-0.012, 0.5, -0.5, 1), (0.012, 0.5, 0.5, 1), (0.02, 0.47, 0.9, 0.4), (0.045, 0.38, 0.9, 0.35), (0.05, 0.34, 1, 0.1), (0.062, 0.33, 0.6, 0.8),
            (0.07, 0.26, 1, 0.25), (0.085, 0.16, 1, 0.15), (0.09, 0, 1, 0)]
    return direct.lathe(prof, 28, axis=1)


@piece("s_roof_cone", (0.6, 1.0, 0.6), tris=300, fit=(1.0, 1.9, 1.0))
def s_roof_cone():
    """Conical tower roof (ellipsoid frame, +Y up; the eave sits a little under the centre, where the ellipsoid
    left the tower): flared eave, concave witch-hat slope, finial ball. The stem below the eave is inside the tower."""
    prof = [(-0.95, 0, -1, 0), (-0.95, 0.3, -1, 0), (-0.2, 0.36, -1, 0.1), (-0.17, 0.5, -1, 0.2), (-0.13, 0.5, 0.4, 1), (0.0, 0.42, 0.5, 1), (0.3, 0.29, 0.42, 1),
            (0.75, 0.06, 0.4, 1), (0.82, 0.03, -0.5, 1), (0.87, 0.07, 0, 1), (0.92, 0.05, 0.7, 0.7), (0.95, 0, 1, 0)]
    return direct.lathe(prof, 16, axis=1)


@piece("s_mantle", (0.65, 0.7, 0.65), tris=1000, fit=(1.0, 1.08, 0.96), res=120)
def s_mantle():
    """Cephalopod mantle (ellipsoid frame, front -Z): bulbous sac with brain-like lobes and soft creases."""
    s = ellipsoid(0.5, 0.54, 0.48)
    s = s.su(ellipsoid(0.26, 0.32, 0.32, (0.22, 0.2, 0.06)).mirror_x(), 0.08)
    s = s.ss(capsule((0, 0.66, -0.3), (0, 0.42, 0.6), 0.05), 0.12)
    return s


@piece("s_beard", (0.6, 0.7, 0.45), tris=600, fit=(1.0, 1.37, 0.68), res=110)
def s_beard():
    """Wizard beard (ellipsoid frame, front -Z, chin at the top): full at the jaw, three combed locks ending in a point."""
    s = ellipsoid(0.48, 0.3, 0.32, (0, 0.36, 0))
    s = s.su(round_cone((0, 0.3, -0.02), (0, -0.68, -0.08), 0.3, 0.05), 0.12)
    s = s.su(round_cone((0.26, 0.3, 0.02), (0.14, -0.4, -0.02), 0.2, 0.05).mirror_x(), 0.07)
    s = s.ss(capsule((0.13, 0.5, -0.36), (0.07, -0.5, -0.2), 0.03).mirror_x(), 0.05)
    return s


@piece("s_blade", (0.6, 3.2, 0.2), tris=40, fit=(1.0, 6.0, 0.2))
def s_blade():
    """Sword blade (block frame, long in Y, thin in Z): flat spine band with ground bevels to both edges."""
    return _prism([(-0.5, 0), (-0.2, -0.1), (0.2, -0.1), (0.5, 0), (0.2, 0.1), (-0.2, 0.1)], -3.0, 3.0)


@piece("s_hat_mid", (0.6, 0.7, 0.6), tris=260, fit=(1.0, 1.25, 1.0))
def s_hat_mid():
    """Wizard hat cone, middle (ellipsoid frame, +Y up): soft slumped cone."""
    return direct.revolve([(-0.625, 0), (-0.58, 0.44), (-0.35, 0.5), (0.1, 0.38), (0.5, 0.26), (0.625, 0)], segs=14, spline=2)


@piece("s_hat_tip", (0.6, 1.2, 0.6), tris=220, fit=(1.0, 2.2, 1.0))
def s_hat_tip():
    """Wizard hat tip (ellipsoid frame, +Y up): tapering point with a soft end."""
    return direct.revolve([(-1.1, 0), (-1.0, 0.42), (-0.6, 0.5), (0.0, 0.33), (0.7, 0.13), (1.02, 0.07), (1.1, 0)], segs=12, spline=2)


@piece("s_robe", (0.6, 0.7, 0.5), tris=500, fit=(1.0, 1.19, 0.72))
def s_robe():
    """Robe skirt (ellipsoid frame; the builder runs it waist at -Y to hem at +Y): bell with hanging folds that
    deepen toward the hem."""
    m = direct.revolve([(-0.6, 0), (-0.57, 0.2), (-0.4, 0.29), (0.0, 0.38), (0.4, 0.46), (0.56, 0.49), (0.6, 0.4), (0.6, 0)], segs=21, spline=2)

    def fn(V):
        y = np.clip((V[:, 1] + 0.6) / 1.2, 0, 1)
        th = np.arctan2(V[:, 2], V[:, 0])
        k = 1 + 0.1 * y ** 1.5 * np.cos(7 * th)
        V[:, 0] *= k
        V[:, 2] *= k * 0.72
        return V
    return direct.deform(m, fn)


@piece("s_helmet", (0.62, 0.62, 0.62), tris=420, fit=(1.0, 0.8, 1.0))
def s_helmet():
    """Knight's helm (ellipsoid frame, +Y up; the part under the brim sits inside the head): skull dome with a
    rolled brim, a brow band and a top knob."""
    prof = [(-0.4, 0, -1, 0), (-0.4, 0.3, -1, 0), (-0.12, 0.42, -1, 0.3), (-0.1, 0.5, -0.7, 0.7), (-0.05, 0.5, 0.7, 0.7), (-0.03, 0.455, 0.3, 1), (0.03, 0.45, 0.1, 1),
            (0.05, 0.43, 0.5, 0.9), (0.2, 0.36, 0.5, 0.86), (0.3, 0.24, 0.8, 0.6), (0.355, 0.09, 0.95, 0.3), (0.36, 0.05, 0, 1), (0.39, 0.05, 0.5, 0.8), (0.4, 0, 1, 0)]
    return direct.lathe(prof, 20, axis=1)
