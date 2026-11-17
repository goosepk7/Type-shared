"""Summon set: the kraken / octopus hero sculpt.

Modelled on refs.json "sig:kraken" (+Y up, -Z front, studs). Mantle and arm segments are authored in the local
frame of their lead primitive (local +Y along the part; for arms local +Z is the under side: Plans/Fish rolls every
arm that way, and the kraken's rearing arms turn it to the viewer), the head in model space. Each piece is a "unit"
sculpt, so the octopus (wider mantle, other arm sizes) uses the same pieces. Eyes, brows, mouth, fins and spots
stay the builder's parts. Assigned in Signatures/Creatures.luau (octoSculpt).
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from .refs import Group
from .s_knight import _def, _ext

W = "sig:kraken"


def _in(G, f):
    """Local-frame SDF of the lead -> model space."""
    return SDF(lambda p: f((p - G.pos) @ G.R))


def _box(G, lo, hi):
    """Region corners (model space) of a local-frame box."""
    pts = []
    for x in (lo[0], hi[0]):
        for y in (lo[1], hi[1]):
            for z in (lo[2], hi[2]):
                pts.append(tuple(G.pos + G.R @ np.array((x, y, z), float)))
    return pts


def _suckers(s, y0, y1, n, r, rad, dx):
    """Two staggered rows of n suckers on the +Z side; rad(y) is the arm radius there."""
    for i in range(n):
        for side in (-1, 1):
            y = y0 + (y1 - y0) * (i + (0.25 if side > 0 else 0.0)) / max(n - 1, 1) * 0.92
            k = 1 - 0.35 * i / n
            z = np.sqrt(max(rad(y) ** 2 - (dx * k) ** 2, 0.0)) * 0.96
            c = (side * dx * k, y, z)
            s = s.su(ellipsoid(r * k, r * k, r * k * 0.6, c), r * 0.3)
    return s


# ------------------------------------------------------------------------------------------------ arms
G1, G2, G3 = Group(W, "tentacle14"), Group(W, "tentacle15"), Group(W, "tentacle16")


def _arm1():
    s = round_cone((0, -1.75, 0), (0, 1.75, 0), 0.56, 0.4)
    return _suckers(s, -1.3, 1.7, 4, 0.2, lambda y: 0.56 - 0.16 * (y + 1.75) / 3.5, 0.19)


def _arm2():
    s = round_cone((0, -1.15, 0), (0, 1.15, 0), 0.4, 0.29)
    return _suckers(s, -0.9, 1.1, 4, 0.125, lambda y: 0.4 - 0.11 * (y + 1.15) / 2.3, 0.14)


def _arm3():
    s = tube([(0, -0.95, 0), (0, 0, 0), (0, 0.7, 0.03), (0, 1.12, 0.22), (0, 1.26, 0.52), (0, 1.1, 0.76), (0, 0.86, 0.7)],
             [0.29, 0.25, 0.2, 0.15, 0.11, 0.07, 0.04], k=0.08)
    return _suckers(s, -0.75, 0.6, 3, 0.09, lambda y: 0.27 - 0.07 * (y + 0.95) / 1.6, 0.1)


@_def("s_octo_arm1", G1, 400, 150, "Octopus arm, root segment (lead: tentacle part, local +Z under side): muscular taper, two rows of suckers.",
      extra=_box(G1, (-0.7, -2.2, -0.7), (0.7, 2.2, 0.85)), pad=0.05, smooth=2)
def arm1():
    return _in(G1, _arm1())


@_def("s_octo_rear", G1, 560, 160, "Kraken rearing arm (lead: Rear tentacle, local +Z to the viewer): the root segment at a higher budget, its suckers "
      "are in plain view.", extra=_box(G1, (-0.7, -2.2, -0.7), (0.7, 2.2, 0.85)), pad=0.05, smooth=2)
def rear():
    return _in(G1, _arm1())


G23 = Group(W, "tentacle15", ["tentacle16"])


@_def("s_octo_arm2", G23, 480, 160, "Octopus arm, middle and tip segments in one (lead: second tentacle part, member: third): taper with suckers, a tip "
      "that curls under.", extra=_box(G3, (-0.36, -1.15, -0.36), (0.36, 1.45, 0.95)) + _box(G2, (-0.5, -1.45, -0.5), (0.5, 1.45, 0.62)), pad=0.05, smooth=2)
def arm2():
    return _in(G2, _arm2()).su(_in(G3, _arm3()), 0.1)


@_def("s_octo_arm3", G3, 320, 150, "Octopus arm, tip segment (the last segment of two-part arms and of the rearing arms): thins to a point that curls "
      "under, small suckers.", extra=_box(G3, (-0.36, -1.15, -0.36), (0.36, 1.45, 0.95)), pad=0.05, smooth=2)
def arm3():
    return _in(G3, _arm3())


# ------------------------------------------------------------------------------------------------ mantle
GM = Group(W, "Mantle")


@_def("s_octo_mantle", GM, 1500, 170, "Octopus mantle (lead Mantle, local +Y to the tip): swollen sac with lobes, folds near the base, a soft point "
      "and warts.", extra=_box(GM, (-2.4, -4.4, -2.4), (2.4, 4.9, 2.4)), pad=0.05, smooth=4)
def mantle():
    body = ellipsoid(2.08, 4.25, 2.08).su(ellipsoid(2.2, 2.5, 2.2, (0, 0.9, 0)), 0.6).su(round_cone((0, 3.0, 0), (0, 4.45, 0), 1.25, 0.45), 0.7)
    rng = np.random.default_rng(5)
    for _ in range(7):
        a, y = rng.uniform(0, 2 * np.pi), rng.uniform(-0.5, 2.6)
        r = 2.15 * np.sqrt(max(1 - ((y - 0.9) / 3.4) ** 2, 0.05))
        body = body.su(sphere(0.2, (r * np.cos(a), y, r * np.sin(a))), 0.3)

    def f(q):
        phi = np.arctan2(q[:, 2], q[:, 0])
        up = np.clip((q[:, 1] + 2.0) / 3.0, 0, 1)
        low = np.clip((0.5 - q[:, 1]) / 2.5, 0, 1)
        off = np.clip(np.hypot(q[:, 0], q[:, 2]) / 1.2, 0, 1)                # no lobes at the pole
        return body(q) - 0.075 * np.cos(5 * phi) * up * off - 0.06 * np.cos(q[:, 1] * 3.2) * low
    return _in(GM, SDF(f))


# ------------------------------------------------------------------------------------------------ head
GH = Group(W, "Head")
_ARMS = [("tentacle14", 1), ("tentacle17", 1), ("tentacle20", 1), ("tentacle23", 1), ("tentacle26", 1), ("tentacle29", 1), ("tentacle32", 1), ("tentacle35", 1)]


@_def("s_octo_head", GH, 1700, 170, "Octopus head (lead Head): eye turrets, the crown of arm roots with webbing between them, siphon, warts on the "
      "cheeks.", extra=_ext((-3.0, 3.0, -3.0), (3.0, 7.9, 2.6)), smooth=4)
def head():
    s = GH.sdf("Head")
    for name, _ in _ARMS:
        A = Group(W, name)
        a = A.pos - A.R[:, 1] * A.s[1] / 2.6
        b = A.pos - A.R[:, 1] * A.s[1] / 2.6 * 0.1
        s = s.su(round_cone(tuple(a), tuple(b), 0.66, 0.54), 0.4)
    s = s.su(ellipsoid(0.74, 0.8, 0.5, (0.93, 6.16, -1.52)).mirror_x(), 0.3)          # eye turrets
    s = s.su(round_cone((1.5, 5.0, -0.9), (2.25, 4.45, -1.45), 0.42, 0.32), 0.2)      # siphon
    s = s.ss(round_cone((1.9, 4.75, -1.15), (2.6, 4.2, -1.7), 0.2, 0.2), 0.05)
    for (x, y, z) in [(1.95, 6.3, -1.0), (2.15, 5.9, -0.3), (1.7, 7.0, -0.9), (2.0, 6.7, 0.1)]:
        s = s.su(sphere(0.17, (x, y, z)).mirror_x(), 0.1)
    return s


GFn = Group(W, "MantleFinR")


@_def("s_octo_fin", GFn, 260, 130, "Kraken mantle fin (lead: mantle fin): a soft rounded lobe, thick at the root, thin at the rim.",
      extra=_ext((1.2, 9.2, 0.8), (3.5, 12.6, 1.55)), mirror=True, pad=0.05)
def fin():
    tip = (3.25, 11.05, 1.17)
    s = round_cone((1.55, 12.25, 1.12), tip, 0.26, 0.09).su(round_cone((1.7, 9.75, 1.2), tip, 0.26, 0.09), 0.25)
    s = s.su(ellipsoid(0.85, 1.15, 0.1, (2.15, 11.0, 1.17)), 0.15)
    return s.su(ellipsoid(0.4, 1.3, 0.24, (1.65, 11.0, 1.17)), 0.2)
