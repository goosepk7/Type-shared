"""Summon set: the stone golem hero sculpt.

Modelled in model space on refs.json "sig:golem" (+Y up, -Z front, studs): a body stacked from chiselled rock
chunks (ellipsoids cut by random facet planes, joined with tight creases), cut along the biped rig. The face parts
(eyes, mouth) stay the builder's; the bear ears and nose of the brute head are absorbed. Each piece is a "unit"
sculpt in the frame of one lead primitive. Assigned in Signatures/Creatures.luau (S.golem).
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from . import piece
from .refs import Group
from .s_knight import _def, _ext

W = "sig:golem"


def rock(c, r, seed, n=12, cut=(0.7, 0.92), planes=()):
    """Chiselled rock: an ellipsoid cut by n random facet planes (plus explicit ones: (normal, distance from c))."""
    c, r = np.asarray(c, float), np.asarray(r, float)
    rng = np.random.default_rng(seed)
    N = rng.normal(size=(n, 3))
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    D = np.sqrt(((N * r) ** 2).sum(1)) * rng.uniform(cut[0], cut[1], n)
    if planes:
        N = np.vstack([N, np.array([p[0] for p in planes], float)])
        D = np.concatenate([D, np.array([p[1] for p in planes], float)])
    e = ellipsoid(r[0], r[1], r[2], tuple(c))
    return SDF(lambda p: np.maximum(e(p), ((p - c) @ N.T - D).max(1)))


def _pile(chunks, k=0.06):
    s = None
    for ch in chunks:
        s = ch if s is None else s.su(ch, k)
    return s


GB = Group(W, "Torso", ["Belly"])


@_def("s_golem_body", GB, 2400, 170, "Golem trunk (lead Torso, member Belly): slabs of chiselled rock, flat chest plate for the runes, hunched back, cracks.",
      extra=_ext((-3.6, 3.6, -3.4), (3.6, 11.9, 2.6)), smooth=2)
def body():
    s = _pile([
        rock((0, 8.6, -0.75), (3.15, 2.35, 2.45), 1, planes=[((0, 0, -1), 2.36)]),
        rock((0, 6.1, -0.45), (2.55, 1.75, 2.1), 2, planes=[((0, 0, -1), 1.95)]),
        rock((1.35, 4.95, -0.2), (1.5, 1.1, 1.5), 3).mirror_x(),
        rock((0, 4.6, -0.1), (1.7, 0.95, 1.55), 4),
        rock((0, 10.1, 0.35), (2.7, 1.5, 1.95), 5),
        rock((0, 10.7, -1.35), (1.7, 1.0, 1.45), 6),
        rock((2.3, 7.2, 0.6), (1.2, 1.5, 1.4), 7).mirror_x(),
    ])
    s = s.ss(capsule((-2.3, 7.05, -3.1), (-0.4, 6.55, -3.05), 0.09), 0.05).ss(capsule((-0.4, 6.55, -3.05), (2.4, 6.9, -3.0), 0.09), 0.05)
    s = s.ss(capsule((0.5, 9.4, -3.1), (1.6, 10.3, -2.6), 0.07), 0.04)
    return s


GH = Group(W, "Head", ["Muzzle", "Nose", "ear22", "ear23", "ear24", "ear25"])


@_def("s_golem_head", GH, 1600, 170, "Golem head (lead Head; members Muzzle, Nose, ears): chiselled boulder, heavy brow slab, underbite jaw with two stone "
      "tusks, cheek and crown rocks.", extra=_ext((-2.5, 8.6, -5.25), (2.5, 13.1, -0.7)), smooth=2)
def head():
    c = GH.c("Head")
    rng = np.random.default_rng(11)
    N = rng.normal(size=(16, 3))
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    N = N[(N[:, 2] > -0.35)]                        # leave the face side to the primitives the eyes sit on
    D = np.sqrt(((N * GH.size("Head") / 2) ** 2).sum(1)) * rng.uniform(0.86, 0.97, len(N))
    base = GH.blend(0.2, ["Head", "Muzzle"])
    s = SDF(lambda p: np.maximum(base(p), ((p - c) @ N.T - D).max(1)))
    s = _pile([
        s,
        rock((0, 12.0, -3.8), (1.75, 0.46, 0.8), 12),                                   # brow
        rock((0, 9.35, -3.95), (1.5, 0.52, 1.1), 13),                                   # jaw
        rock((0.78, 9.98, -4.82), (0.2, 0.32, 0.2), 14, n=6).mirror_x(),                # tusks
        rock((1.75, 10.6, -2.6), (0.6, 0.95, 0.95), 15).mirror_x(),                     # cheeks
        rock((0.65, 12.5, -2.3), (1.05, 0.5, 0.95), 16),
        rock((-0.85, 12.4, -2.7), (0.85, 0.46, 0.85), 17),
    ], 0.05)
    return s


GU, GFo = Group(W, "limb9"), Group(W, "limb11", ["hand13"])


@_def("s_golem_arm", GU, 600, 140, "Golem upper arm (lead: arm limb): two rock chunks.", extra=_ext((2.2, 5.9, -3.2), (5.6, 11.6, 0.2)), mirror=True, smooth=2)
def arm():
    return _pile([rock((3.35, 9.7, -1.2), (1.3, 1.45, 1.3), 21), rock((4.3, 7.5, -2.0), (1.1, 1.3, 1.1), 22)])


@_def("s_golem_fist", GFo, 1000, 150, "Golem forearm and fist (lead: forearm limb, member hand): elbow stone, a forearm boulder wider than the upper arm, "
      "a block fist with four knuckles.", extra=_ext((3.2, 2.2, -4.6), (5.95, 7.6, -1.2)), mirror=True, smooth=2)
def fist():
    chunks = [rock((4.5, 6.65, -2.3), (0.95, 0.9, 0.95), 23), rock((4.56, 5.15, -2.7), (1.2, 1.45, 1.2), 24), rock((4.61, 3.45, -3.05), (1.25, 1.05, 1.25), 25)]
    for i in range(4):
        chunks.append(rock((3.98 + i * 0.42, 3.0, -4.05), (0.26, 0.34, 0.3), 26 + i, n=6))
    return _pile(chunks)


GT, GS = Group(W, "limb3"), Group(W, "limb5", ["foot7"])


@_def("s_golem_thigh", GT, 500, 130, "Golem thigh (lead: hip limb): a boulder and a knee stone.", extra=_ext((0.4, 1.7, -1.5), (3.35, 6.3, 1.5)), mirror=True, smooth=2)
def thigh():
    return _pile([rock((1.87, 4.6, 0.05), (1.4, 1.6, 1.4), 31), rock((1.87, 2.6, -0.25), (1.0, 0.8, 1.0), 32)])


@_def("s_golem_foot", GS, 800, 150, "Golem shin and foot (lead: knee limb, member foot): shin stone, slab foot with three toe blocks.",
      extra=_ext((0.7, 0.0, -2.2), (3.05, 2.6, 1.1)), mirror=True, smooth=2)
def foot():
    chunks = [rock((1.87, 1.5, 0.05), (0.95, 1.0, 0.95), 33), rock((1.87, 0.55, -0.45), (1.08, 0.56, 1.3), 34, planes=[((0, -1, 0), 0.52)])]
    for i in range(3):
        chunks.append(rock((1.27 + i * 0.6, 0.36, -1.75), (0.3, 0.34, 0.36), 35 + i, n=6, planes=[((0, -1, 0), 0.33)]))
    s = _pile(chunks)
    return SDF(lambda p: np.maximum(s(p), 0.012 - p[:, 1]))


GCl = Group(W, "Club")


@_def("s_golem_club", GCl, 450, 150, "Golem club (lead Club): an uprooted trunk, thick at the top, knots and two broken branch stubs.",
      extra=_ext((3.6, 2.4, -4.5), (5.6, 9.9, -2.3)), pad=0.12)
def club():
    s = tube([(4.61, 2.65, -3.03), (4.6, 4.8, -3.2), (4.64, 7.2, -3.36), (4.61, 9.2, -3.5)], [0.34, 0.42, 0.62, 0.78], k=0.2)
    s = s.su(round_cone((4.9, 7.6, -3.3), (5.45, 8.3, -3.2), 0.24, 0.16), 0.08)
    s = s.su(round_cone((4.3, 6.5, -3.5), (3.85, 7.0, -3.85), 0.2, 0.13), 0.08)
    for (x, y, z) in [(4.95, 5.6, -3.0), (4.25, 8.4, -3.0), (4.7, 8.9, -4.1)]:
        s = s.su(sphere(0.2, (x, y, z)), 0.1)
    return SDF(lambda p: np.maximum(s(p), p[:, 1] - 9.55))
