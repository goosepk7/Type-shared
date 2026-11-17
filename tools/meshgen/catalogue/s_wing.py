"""Summon set: the large feathered wing (eagle, phoenix and every other bird with flight feathers).

Modelled in model space on refs.json "sig:phoenix" (+Y up, -Z front, studs; right wing, the left is the mirror):
the wing rises from the shoulder to the wrist and the hand, the feather plane tilts back and down so its face shows
from the front as well as from above. Two "unit" pieces so the wing keeps its two colours: the arm with three rows
of coverts (lead: the covert ellipsoid) and the flight feathers - ten fanned primaries, secondaries, tertials -
(lead: the first primary feather part, members: the other feather parts). Built directly: every feather is a thin
two-sided leaf with a raised quill. Assigned in Parts.wings.
"""
import numpy as np

import direct
from .refs import Group
from .s_castle import _unit, local  # noqa: F401

from . import NO_AO

NO_AO.update({"s_wing_arm", "s_wing_arm_l", "s_wing_flight", "s_wing_flight_l", "s_wing_full", "s_wing_full_l"})

W = "sig:phoenix"
GA = Group(W, "wing21")
GF = Group(W, "wing23", ["wing25", "wing27"])

S = np.array((1.04, 4.47, -0.65))                 # shoulder (the wing bone pivot)
E = S + (2.1, 0.95, 0.2)                          # elbow
WR = E + (2.1, 0.85, -0.5)                        # wrist
H = WR + (1.3, 0.3, -0.15)                        # hand tip
CH = np.array((0.0, -0.5, 0.87))                  # chord: trailing edge back and down
CH /= np.linalg.norm(CH)


def _n(v):
    return v / np.linalg.norm(v)


def feather(p0, d, L, w, n, lift=0.0, ns=5):
    """Leaf from p0 along d (length L, half width w), facing n; a raised quill down the middle."""
    d = _n(d)
    t = _n(np.cross(n, d))
    n = _n(np.cross(d, t))
    rows = []
    for i in range(ns + 1):
        s = i / ns
        hw = w * (np.sin(np.pi * min(s * 0.62 + 0.1, 1.0)) ** 0.8) * (1.0 if i < ns else 0.25)
        c = p0 + d * (L * s) + n * (lift - 0.1 * L * s * s)          # tips droop a little
        rows.append([c - t * hw, c + n * 0.035, c + t * hw])
    P = np.array(rows)
    V, N, F = [], [], []
    for side in (1, -1):
        base = len(V)
        for i in range(ns + 1):
            for j in range(3):
                nn = _n(n * 1.0 + t * (j - 1) * 0.35) * side
                V.append(P[i, j] - n * (0.025 if side < 0 else 0))
                N.append(nn)
        for i in range(ns):
            for j in range(2):
                a, b, c, e = base + i * 3 + j, base + (i + 1) * 3 + j, base + (i + 1) * 3 + j + 1, base + i * 3 + j + 1
                F += [[a, b, c], [a, c, e]] if side > 0 else [[a, c, b], [a, e, c]]
    return direct._finish(np.array(V), np.array(N), np.array(F))


def spindle(a, b, r0, r1, segs=8):
    """Rounded limb from a to b."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    L = np.linalg.norm(b - a)
    u = (b - a) / L
    prof = [(-r0 * 0.8, 0, -1, 0), (-r0 * 0.4, r0 * 0.8, -1, 1), (0.1 * L, r0, 0, 1), (L, r1, 0, 1), (L + r1 * 0.7, r1 * 0.6, 1, 1), (L + r1, 0, 1, 0)]
    m = direct.lathe(prof, segs, axis=0)
    h = np.array((0, 0, 1.0)) if abs(u[2]) < 0.9 else np.array((1.0, 0, 0))
    v = _n(np.cross(h, u))
    w = np.cross(u, v)
    R = np.stack([u, v, w], axis=1)
    return direct.moved(m, rot=R, offset=tuple(a))


def _along(pts, s):
    """Point at fraction s of the polyline."""
    pts = [np.asarray(p, float) for p in pts]
    seg = [np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)]
    t = s * sum(seg)
    for i, ln in enumerate(seg):
        if t <= ln or i == len(seg) - 1:
            return pts[i] + (pts[i + 1] - pts[i]) * min(t / ln, 1.0)
        t -= ln


SPAN = _n(H - S)
NRM = _n(np.cross(CH, SPAN))                      # wing face normal (up and forward)


def _dir(deg):
    a = np.radians(deg)
    return np.cos(a) * SPAN + np.sin(a) * CH


@_unit("s_wing_arm", GA, 1100, "Feathered wing, arm and coverts (lead: the covert ellipsoid of a feather wing): shoulder, forearm and hand along the "
       "leading edge, three overlapping rows of covert feathers.", mirror=True)
def arm():
    m = [spindle(S - SPAN * 0.3, E, 0.5, 0.36), spindle(E, WR, 0.36, 0.26), spindle(WR, H, 0.26, 0.12)]
    for row, (n, L, w, lift, off) in enumerate([(9, 1.25, 0.34, 0.2, 0.1), (10, 1.7, 0.36, 0.13, 0.5), (11, 2.2, 0.38, 0.06, 0.85)]):
        for i in range(n):
            s = (i + 0.5 * (row % 2)) / n
            p = _along([S, E, WR, H], 0.04 + 0.94 * s) + CH * off * (0.25 if row == 0 else 0.5)
            m.append(feather(p, _dir(96 - 78 * s ** 1.5), L * (1.0 - 0.15 * s), w, NRM, lift, ns=3))
    return direct.merge(*m)


@_unit("s_wing_flight", GF, 1100, "Feathered wing, flight feathers (lead: the first primary feather part; members: the other feather parts): ten "
       "fanned primaries from the hand, nine secondaries, five tertials at the body.", mirror=True)
def flight():
    m = []
    for i in range(10):                                   # primaries: the fan at the wing tip
        s = i / 9
        p = WR + (H - WR) * (1 - s) + CH * 0.3
        m.append(feather(p, _dir(-6 + 62 * s), 4.5 - 0.9 * s, 0.4, NRM, -0.02 - 0.012 * i, ns=5))
    for i in range(9):                                    # secondaries along the forearm
        s = i / 8
        p = WR + (E - WR) * (0.08 + 0.92 * s) + CH * 0.45
        m.append(feather(p, _dir(62 + 24 * s), 3.5 - 0.5 * s, 0.42, NRM, -0.14 - 0.008 * i, ns=4))
    for i in range(5):                                    # tertials
        s = i / 4
        p = E + (S - E) * (0.1 + 0.8 * s) + CH * 0.45
        m.append(feather(p, _dir(88 + 14 * s), 3.0 - 0.9 * s, 0.42, NRM, -0.2, ns=4))
    return direct.merge(*m)


G1 = Group("eagle@1", "wing11")
_S1, _K1 = np.array((0.64, 2.80, -0.40)), 4.505 / 7.29      # shoulder and span scale of the low-detail eagle


@_unit("s_wing_full", G1, 2000, "Feathered wing in one piece (lead: the single wing ellipsoid of low detail): the arm, coverts and flight feathers of "
       "s_wing_arm + s_wing_flight together.", mirror=True)
def full():
    m = direct.merge(arm(), flight())
    return direct.moved(direct.moved(m, offset=tuple(-S), ), scale=(_K1, _K1, _K1), offset=tuple(_S1))
