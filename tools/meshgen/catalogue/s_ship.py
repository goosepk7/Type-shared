"""Summon set: the pirate ship hero sculpt.

Modelled in model space on refs.json "sig:pirate ship" (+Y up, -Z front, studs): a carvel hull with a raked stem,
keel, two wales, bulwarks round a sunken deck, gun port frames, bowsprit and rudder (it contains the bow wedges
and the gunwale); a stern castle with rail, windows and lantern (built directly: crisp); billowing square sails
and a jib (thin two-sided sheets, built directly). Mast, yards, cannons, crow's nest and flags stay the builder's
parts. Each piece is a "unit" sculpt in the frame of one lead primitive. Assigned in Signatures/Machines.luau.
"""
import numpy as np

import direct
from sdf import *  # noqa: F401,F403
from .refs import Group
from .s_knight import _def, _ext
from .s_castle import cube, _unit

W = "sig:pirate ship"
GH = Group(W, "Hull", ["BowR", "BowL", "Gunwale"])
Z0, Z1, ZM, BM = -7.3, 5.2, -1.0, 2.62      # stem, transom, widest station, half breadth there


def _lines(z):
    f = np.clip((ZM - z) / (ZM - Z0), 0, 1)          # 0 at midship .. 1 at the stem
    a = np.clip((z - ZM) / (Z1 - ZM), 0, 1)          # 0 at midship .. 1 at the transom
    b = BM * (1 - f ** 2.2) - 0.45 * a ** 2
    top = 4.4 + 1.0 * f ** 2 + 0.3 * a ** 2
    bot = 1.55 + 1.5 * f ** 3 + 0.45 * a ** 3
    return b, top, bot


def _hull(p):
    x, y, z = np.abs(p[:, 0]), p[:, 1], p[:, 2]
    b, top, bot = _lines(z)
    h = np.clip((y - bot) / (top - bot), 0, 1)
    s = 0.3 + 0.7 * h ** 0.35
    wale = 0.09 * np.exp(-((y - (top - 0.8)) / 0.11) ** 2) + 0.09 * np.exp(-((y - (top - 1.55)) / 0.11) ** 2) + 0.07 * np.clip((y - top + 0.16) / 0.1, 0, 1)
    side = x - (b * s + wale)
    d = np.maximum(np.maximum(np.maximum(side, bot - y), np.maximum(y - top, z - Z1)), Z0 - z) * 0.55
    well = np.maximum(np.maximum((top - 0.42) - y, x - (b * s - 0.24)), np.maximum(z - (Z1 - 0.25), (Z0 + 0.9) - z)) * 0.55
    return np.maximum(d, -well)


@_def("s_ship_hull", GH, 2800, 200, "Pirate ship hull (lead Hull; members: bow wedges, gunwale): carvel hull, raked stem and keel, two wales, bulwarks "
      "round the sunken deck, gun port frames, bowsprit, rudder.", extra=_ext((-3.0, 1.3, -9.6), (3.0, 6.2, 5.9)), smooth=2)
def hull():
    s = SDF(_hull)
    s = s.su(tube([(0, 1.52, 5.1), (0, 1.5, -1.0), (0, 2.0, -5.0), (0, 3.7, -7.05), (0, 5.75, -7.5)], [0.15, 0.15, 0.15, 0.16, 0.12], k=0.1), 0.05)
    s = s.su(capsule((0, 5.0, -6.7), (0, 6.0, -9.4), 0.13), 0.05)                                  # bowsprit
    s = s.su(round_box(0.07, 1.05, 0.38, 0.04, (0, 2.5, 5.5)), 0.03)                               # rudder
    for z in (-0.77, 0.92, 2.61):                                                                  # gun port frames
        fr = round_box(0.3, 0.42, 0.42, 0.05, (2.3, 3.2, z)).ss(round_box(0.5, 0.28, 0.28, 0.02, (2.5, 3.2, z)), 0.02)
        s = s.su(fr.mirror_x(), 0.03)
    return s


GS = Group(W, "SternCastle")


@_unit("s_ship_stern", GS, 500, "Pirate ship stern castle (lead SternCastle): cabin with an overhanging quarterdeck, rail on turned posts, three "
       "framed stern windows, side windows, a lantern.")
def stern():
    c = GS.pos
    w, h, d = GS.s
    m = [direct.moved(direct.rounded_box((w, h, d), 0.05, 0), offset=tuple(c))]
    top = c[1] + h / 2
    m.append(cube((w + 0.3, 0.16, d + 0.3), (c[0], top + 0.02, c[2])))
    zb, zf = c[2] + d / 2 + 0.1, c[2] - d / 2 - 0.1
    for i in range(5):                                                                             # taffrail posts
        x = c[0] + (i - 2) * (w + 0.1) / 4
        m.append(cube((0.14, 0.5, 0.14), (x, top + 0.34, zb - 0.02)))
    for sx in (-1, 1):
        for z in (c[2] - d * 0.05, zf + 0.05):
            m.append(cube((0.14, 0.5, 0.14), (c[0] + sx * (w / 2 + 0.05), top + 0.34, z)))
        m.append(cube((0.1, 0.1, d + 0.3), (c[0] + sx * (w / 2 + 0.05), top + 0.62, c[2])))
        m.append(cube((0.07, h * 0.42, d * 0.36), (c[0] + sx * (w / 2 + 0.02), c[1] + h * 0.08, c[2])))       # side window frame
    m.append(cube((w + 0.3, 0.1, 0.1), (c[0], top + 0.62, zb - 0.02)))
    for i in (-1, 0, 1):                                                                           # stern windows: frame and mullions
        x = c[0] + i * w * 0.29
        m.append(cube((w * 0.22, h * 0.46, 0.07), (x, c[1] + h * 0.08, c[2] + d / 2 + 0.02)))
        m.append(cube((0.05, h * 0.46, 0.11), (x, c[1] + h * 0.08, c[2] + d / 2 + 0.02)))
        m.append(cube((w * 0.22, 0.05, 0.11), (x, c[1] + h * 0.08, c[2] + d / 2 + 0.02)))
    m.append(cube((0.09, 0.6, 0.09), (c[0], top + 0.9, zb)))                                         # lantern
    m.append(direct.moved(direct.bevel_cylinder(0.42, 0.2, 0.05, 8, axis=1), offset=(c[0], top + 1.34, zb)))
    m.append(cube((0.3, 0.07, 0.3), (c[0], top + 1.58, zb)))
    return direct.merge(*m)


def sheet(fn, nu, nv, thick=0.03):
    """Two-sided thin sheet through fn(u, v) -> point (u, v in 0..1); smooth normals from the grid."""
    P = np.array([[fn(i / nu, j / nv) for j in range(nv + 1)] for i in range(nu + 1)], float)
    du = np.gradient(P, axis=0)
    dv = np.gradient(P, axis=1)
    N = np.cross(du, dv)
    N /= np.maximum(np.linalg.norm(N, axis=2, keepdims=True), 1e-9)
    V, Nn, F = [], [], []
    for side in (1, -1):
        base = len(V)
        for i in range(nu + 1):
            for j in range(nv + 1):
                V.append(P[i, j] + N[i, j] * thick * side)
                Nn.append(N[i, j] * side)
        for i in range(nu):
            for j in range(nv):
                a, b, c, d = base + i * (nv + 1) + j, base + (i + 1) * (nv + 1) + j, base + (i + 1) * (nv + 1) + j + 1, base + i * (nv + 1) + j + 1
                F += [[a, b, c], [a, c, d]] if side > 0 else [[a, c, b], [a, d, c]]
    return direct._finish(np.array(V), np.array(Nn), np.array(F))


GSl = Group(W, "Sail")


@_unit("s_ship_sail", GSl, 700, "Square sail (lead: a sail block, thin axis Z, front -Z): bellied forward, scalloped panels, the foot drawn up at the "
       "corners.")
def sail():
    w, h, _ = GSl.s

    def f(u, v):
        x = (u - 0.5) * w * (0.9 + 0.1 * v)                       # a little narrower at the foot
        y = (v - 0.5) * h + 0.07 * h * (1 - v) ** 2 * np.cos(np.pi * (u - 0.5)) ** 2   # foot arches up in the middle
        belly = np.sin(np.pi * u) ** 0.7 * np.sin(np.pi * (0.08 + 0.92 * (1 - v) ** 0.8)) ** 0.9
        z = -0.75 * belly * min(1.0, h / 4.2) - 0.05 * abs(np.sin(4 * np.pi * u)) * np.sin(np.pi * v)
        return GSl.pos + np.array((x, y, z + 0.1))
    return sheet(f, 16, 10)


GJ = Group(W, "Jib")


@_unit("s_ship_jib", GJ, 300, "Jib (lead: the jib wedge, luff to the mast): a bellied triangular staysail from the bowsprit to the masthead.")
def jib():
    _, h, d = GJ.s
    c = GJ.pos
    tack = np.array((0, c[1] - h / 2, c[2] - d / 2))
    head = np.array((0, c[1] + h / 2, c[2] + d / 2 - 0.85))
    clew = np.array((0, c[1] - h / 2 + 0.25, c[2] + d / 2 - 0.85))

    def f(u, v):
        a = tack + (clew - tack) * u
        b = tack + (head - tack) * u
        p = a + (b - a) * v
        p[0] += 0.4 * np.sin(np.pi * min(u * 1.15, 1)) ** 0.8 * np.sin(np.pi * v) * (0.3 + 0.7 * u)
        return p
    return sheet(f, 10, 6)
