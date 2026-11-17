"""Summon set: the horse family hero sculpt (horse, pony, zebra, donkey, unicorn, pegasus).

Modelled in model space on refs.json "sig:unicorn" (the equine archetype of Plans/Quadruped with long legs: +Y up,
-Z front, studs) and cut along the quadruped rig: muscled trunk, arched neck, a mane of locks falling to one side,
fore and hind legs with knee, hock and fetlock, a flowing two-piece tail, the spiral horn and the pastel locks of
the unicorn. The head keeps s_head_equine and its ears; hooves keep s_hoof (their own colour). Each piece is a
"unit" sculpt in the frame of one lead primitive, so the shorter-legged horse uses the same pieces. Assigned at the
end of Plans/Quadruped.luau.
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from .refs import Group
from .s_knight import _def, _ext

W = "sig:unicorn"


def _lock(a, b, r0, r1=0.06):
    return round_cone(tuple(a), tuple(b), r0, r1)


GB = Group(W, "Torso", ["Chest", "Haunch", "Belly"])


@_def("s_horse_body", GB, 2200, 170, "Horse trunk (lead Torso; members Chest, Haunch, Belly): deep chest, barrel, rounded croup, withers, shoulder and "
      "stifle muscle, breast, tail dock.", extra=_ext((-1.35, 4.9, -3.4), (1.35, 7.9, 3.4)), smooth=4)
def body():
    s = ellipsoid(0.95, 1.08, 1.9, (0, 6.2, 0.1))
    s = s.su(ellipsoid(1.0, 1.3, 1.3, (0, 6.3, -1.75)), 0.5)
    s = s.su(ellipsoid(1.02, 1.22, 1.3, (0, 6.42, 1.8)), 0.5)
    s = s.su(ellipsoid(0.4, 0.5, 0.85, (0, 7.2, -1.45)), 0.3)                        # withers
    s = s.su(ellipsoid(0.36, 0.95, 0.7, (0.8, 6.2, -1.85)).mirror_x(), 0.2)          # shoulders
    s = s.su(ellipsoid(0.42, 0.95, 0.85, (0.74, 6.25, 1.9)).mirror_x(), 0.2)         # stifle and hip
    s = s.su(round_cone((0, 6.5, -2.0), (0, 7.4, -2.75), 0.85, 0.62), 0.35)          # neck root
    s = s.su(ellipsoid(0.4, 0.5, 0.3, (0.34, 6.0, -2.68)).mirror_x(), 0.3)       # breast muscles
    s = s.su(round_cone((0, 6.95, 2.6), (0, 6.95, 3.02), 0.36, 0.28), 0.25)          # dock
    return s


GN = Group(W, "Neck")


@_def("s_horse_neck", GN, 800, 150, "Horse neck (lead Neck): deep and arched, crest along the top, throat line, jowl.",
      extra=_ext((-1.0, 6.0, -5.0), (1.0, 10.6, -1.4)), smooth=4)
def neck():
    s = tube([(0, 6.6, -2.3), (0, 8.3, -3.35), (0, 9.9, -4.3)], [0.78, 0.52, 0.46], k=0.25)
    s = s.su(tube([(0, 6.9, -1.75), (0, 8.6, -2.95), (0, 10.1, -3.9)], [0.5, 0.36, 0.3], k=0.25), 0.3)   # crest
    s = s.su(tube([(0, 6.3, -2.85), (0, 8.0, -3.75), (0, 9.5, -4.6)], [0.55, 0.36, 0.34], k=0.25), 0.3)  # throat
    return s


GM = Group(W, "Mane")


@_def("s_horse_mane", GM, 800, 160, "Horse mane (lead Mane): a ridge along the crest and eight locks falling to the off side.",
      extra=_ext((-0.5, 6.2, -4.3), (1.25, 10.9, -1.5)))
def mane():
    a, b = np.array((0, 7.05, -1.8)), np.array((0, 10.55, -3.95))
    s = tube([tuple(a), tuple((a + b) / 2 + (0, 0.05, 0.05)), tuple(b)], [0.2, 0.24, 0.2], k=0.2)
    n = 8
    for i in range(n):
        u = (i + 0.3) / n
        c = a + (b - a) * u
        ln = 1.25 - 0.5 * u + 0.12 * (i % 2)
        tip = c + np.array((0.62 + 0.08 * (i % 3), -ln, 0.38 + 0.1 * (i % 2)))
        mid = c + np.array((0.5, -ln * 0.4, 0.12))
        s = s.su(tube([tuple(c), tuple(mid), tuple(tip)], [0.2, 0.19, 0.06], k=0.15), 0.1)
    return s


# ------------------------------------------------------------------------------------------------ legs
GTF, GSF = Group(W, "limb5"), Group(W, "limb7")
GTH, GSH = Group(W, "limb11"), Group(W, "limb13")


@_def("s_horse_thigh_f", GTF, 400, 130, "Horse foreleg, upper (lead: front hip limb): forearm muscle tapering to the knee.",
      extra=_ext((0.0, 2.0, -2.6), (1.2, 6.4, -1.3)), mirror=True)
def thigh_f():
    s = round_cone((0.6, 6.0, -1.85), (0.59, 2.4, -2.12), 0.4, 0.22)
    s = s.su(ellipsoid(0.34, 0.95, 0.5, (0.64, 4.9, -1.85)), 0.2)
    s = s.su(ellipsoid(0.22, 0.6, 0.3, (0.6, 3.6, -1.82)), 0.15)
    return s.su(ellipsoid(0.27, 0.34, 0.3, (0.59, 2.3, -2.18)), 0.1)


@_def("s_horse_shin_f", GSF, 350, 130, "Horse foreleg, lower (lead: front knee limb): slim cannon, fetlock with a feather, sloping pastern.",
      extra=_ext((0.2, 0.25, -2.5), (1.0, 2.7, -1.45)), mirror=True)
def shin_f():
    s = round_cone((0.59, 2.3, -2.14), (0.59, 0.8, -1.9), 0.21, 0.17).su(ellipsoid(0.26, 0.3, 0.28, (0.59, 2.3, -2.16)), 0.08)
    s = s.su(sphere(0.25, (0.59, 0.74, -1.86)), 0.08)
    s = s.su(round_cone((0.59, 0.72, -1.86), (0.59, 0.36, -1.92), 0.2, 0.24), 0.06)
    return s.su(_lock((0.59, 0.78, -1.7), (0.59, 0.42, -1.56), 0.13, 0.04), 0.08)


@_def("s_horse_thigh_h", GTH, 450, 130, "Horse hind leg, upper (lead: back hip limb): broad thigh and gaskin down to the hock point.",
      extra=_ext((0.0, 2.0, 1.2), (1.3, 6.5, 3.0)), mirror=True)
def thigh_h():
    s = round_cone((0.64, 5.9, 1.95), (0.62, 2.45, 2.42), 0.46, 0.23)
    s = s.su(ellipsoid(0.44, 1.2, 0.75, (0.68, 5.1, 2.0)), 0.25)
    s = s.su(ellipsoid(0.24, 0.7, 0.36, (0.62, 3.5, 2.36)), 0.15)
    return s.su(round_cone((0.62, 2.4, 2.42), (0.62, 2.5, 2.68), 0.24, 0.15), 0.08)


@_def("s_horse_shin_h", GSH, 350, 130, "Horse hind leg, lower (lead: back knee limb): cannon from the hock, fetlock with a feather, pastern.",
      extra=_ext((0.2, 0.25, 1.5), (1.05, 2.8, 2.8)), mirror=True)
def shin_h():
    s = round_cone((0.62, 2.35, 2.44), (0.62, 0.8, 2.06), 0.22, 0.17).su(sphere(0.26, (0.62, 2.35, 2.46)), 0.08)
    s = s.su(sphere(0.25, (0.62, 0.74, 2.04)), 0.08)
    s = s.su(round_cone((0.62, 0.72, 2.04), (0.62, 0.36, 1.98), 0.2, 0.24), 0.06)
    return s.su(_lock((0.62, 0.78, 2.2), (0.62, 0.42, 2.36), 0.13, 0.04), 0.08)


# ------------------------------------------------------------------------------------------------ tail
G1, G2 = Group(W, "tail38"), Group(W, "tail39")
_TAIL = [(0, 6.95, 2.75), (0, 6.85, 3.3), (0, 6.2, 3.75), (0, 5.3, 3.95), (0, 4.4, 4.25), (0, 3.5, 4.75), (0, 2.9, 5.2)]


@_def("s_horse_tail1", G1, 500, 150, "Horse tail, upper (lead: first tail segment): hair arching off the dock in three strands.",
      extra=_ext((-0.7, 4.6, 2.5), (0.7, 7.4, 4.5)))
def tail1():
    s = tube(_TAIL[:5], [0.26, 0.34, 0.42, 0.44, 0.42], k=0.25)
    for dx in (-0.22, 0.22):
        s = s.su(tube([(dx * 0.5, 6.8, 3.35), (dx, 6.0, 3.95), (dx * 1.2, 5.0, 4.15), (dx, 4.5, 4.3)], [0.18, 0.26, 0.28, 0.26], k=0.2), 0.08)
    return SDF(lambda p: np.maximum(s(p), 4.75 - p[:, 1] + 0.0 * p[:, 0]))


@_def("s_horse_tail2", G2, 500, 150, "Horse tail, lower (lead: second tail segment): the strands thin out to wispy points.",
      extra=_ext((-0.75, 2.5, 3.3), (0.75, 5.7, 5.6)))
def tail2():
    s = tube(_TAIL[3:], [0.42, 0.42, 0.3, 0.07], k=0.25)
    for dx, end in ((-0.24, (-0.36, 3.2, 4.7)), (0.24, (0.4, 3.0, 4.95)), (0.0, (0.05, 3.4, 5.25))):
        s = s.su(tube([(dx * 0.8, 5.3, 4.05), (dx, 4.4, 4.35 + abs(dx) * 0.3), end], [0.26, 0.26, 0.05], k=0.2), 0.1)
    return s


# ------------------------------------------------------------------------------------------------ unicorn
GHn = Group(W, "horn35", ["horn36"])


@_def("s_unicorn_horn", GHn, 400, 170, "Unicorn horn (lead: first horn segment, member: second): a long cone with a twisted double groove.",
      extra=_ext((-0.4, 10.3, -7.3), (0.4, 13.0, -4.8)), pad=0.1, smooth=2)
def horn():
    a, b = np.array((0, 10.45, -5.0)), np.array((0, 12.89, -7.15))
    L = np.linalg.norm(b - a)
    u = (b - a) / L
    e1 = np.array((1.0, 0, 0))
    e2 = np.cross(u, e1)

    def f(p):
        pa = p - a
        t = pa @ u
        x, y = pa @ e1, pa @ e2
        rad = np.hypot(x, y)
        r = 0.27 + (0.035 - 0.27) * np.clip(t / L, 0, 1)
        r = r * (1 + 0.17 * np.cos(2 * np.arctan2(y, x) - 10.5 * t))
        return np.maximum(np.maximum(rad - r, -t), t - L) * 0.6
    return SDF(f).su(sphere(0.035, tuple(b)), 0.01)


GL = Group(W, "Mane2")


@_def("s_unicorn_lock", GL, 260, 140, "Unicorn mane lock (lead: a mane ellipsoid; also the forelock): a fat wavy lock with a curled tip.",
      extra=_ext((-0.5, 8.6, -3.2), (0.6, 10.2, -1.7)), pad=0.1)
def lock():
    s = tube([(0, 9.95, -2.98), (0.06, 9.75, -2.62), (0.1, 9.35, -2.3), (0.22, 8.95, -2.08), (0.34, 8.78, -1.95)], [0.2, 0.3, 0.27, 0.16, 0.05], k=0.2)
    s = s.su(tube([(-0.12, 9.85, -2.8), (-0.2, 9.5, -2.45), (-0.16, 9.15, -2.25)], [0.16, 0.2, 0.06], k=0.15), 0.08)
    return s
