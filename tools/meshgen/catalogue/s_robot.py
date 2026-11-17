"""Summon set: the robot hero sculpt (retro panelled automaton).

Modelled in model space on refs.json "sig:robot" (+Y up, -Z front, studs) and cut along the humanoid rig: a
panelled chest box with a bezel round the chest light, shoulder housings and exhaust stacks, piston limbs with
ribbed joints, bell boots, clamp hands and a bezelled head. Eyes, mouth, chest light, reactor, vents, antennas and
ear discs stay the builder's parts. Each piece is a "unit" sculpt in the frame of one lead primitive. Assigned in
Signatures/Heroes.luau (S.robot).
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from .refs import Group
from .s_knight import _def, _ext

W = "sig:robot"


def cyl(a, b, r, rnd=0.04):
    """Capped cylinder from a to b (flat ends, edges rounded by rnd)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    L = np.linalg.norm(b - a)
    u = (b - a) / L

    def f(p):
        pa = p - a
        t = pa @ u
        rad = np.linalg.norm(pa - np.outer(t, u), axis=1)
        dx, dy = rad - (r - rnd), np.abs(t - L / 2) - (L / 2 - rnd)
        return np.minimum(np.maximum(dx, dy), 0) + np.hypot(np.maximum(dx, 0), np.maximum(dy, 0)) - rnd
    return SDF(f)


def groove(s, cut, d=0.07):
    """Panel seam: remove `cut` from s, but only d deep below the surface."""
    return SDF(lambda p: np.maximum(s(p), -np.maximum(cut(p), -(s(p) + d))))


def slab(axis, at, h):
    return SDF(lambda p: np.abs(p[:, axis] - at) - h)


def bezel(c, hx, hy, bar, z0, z1):
    """Raised rectangular frame facing -Z: outer half size (hx, hy), bar width, from z0 (inside) to z1 (proud)."""
    zc, hz = (z0 + z1) / 2, abs(z1 - z0) / 2
    o = round_box(hx, hy, hz, 0.04, (c[0], c[1], zc))
    i = box(hx - bar, hy - bar, hz * 3).at(c[0], c[1], zc)
    return o.ss(i, 0.02)


def ribs(a, b, r, n, h=0.07):
    """n ring flanges along the axis a..b."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    u = (b - a) / np.linalg.norm(b - a)
    s = None
    for i in range(n):
        c = a + (b - a) * (i + 0.5) / n
        d = cyl(c - u * h, c + u * h, r, 0.03)
        s = d if s is None else s.su(d, 0.0)
    return s


# ------------------------------------------------------------------------------------------------ chest, pelvis
GC = Group(W, "Torso")


@_def("s_robot_chest", GC, 1500, 170, "Robot chest (lead Torso): panelled box, bezel round the chest light and vents, shoulder housings, neck collar, "
      "back pack with two exhaust stacks, seam lines and rivets.", extra=_ext((-2.5, 4.3, -1.6), (2.5, 9.3, 2.1)))
def chest():
    s = round_box(1.89, 2.11, 1.36, 0.16, (0, 6.54, 0))
    s = groove(s, slab(1, 5.02, 0.05))
    s = groove(s, SDF(lambda p: np.maximum(np.abs(np.abs(p[:, 0]) - 1.0) - 0.045, -p[:, 2])))      # two back seams
    s = s.su(bezel((0, 6.52), 1.6, 1.42, 0.3, -1.3, -1.5), 0.02)
    for x in (-1.45, 1.45):
        for y in (5.25, 7.79):
            s = s.su(sphere(0.1, (x, y, -1.5)), 0.01)
    s = s.su(cyl((1.75, 8.0, 0.04), (2.3, 8.0, 0.04), 0.82, 0.08).mirror_x(), 0.03)                 # shoulder housings
    s = s.su(cyl((0, 8.5, 0), (0, 8.85, 0), 0.95, 0.06), 0.03)                                      # collar
    s = s.su(round_box(1.25, 1.35, 0.3, 0.1, (0, 6.75, 1.5)), 0.03)                                 # back pack
    s = s.su(cyl((0.7, 7.6, 1.72), (0.7, 9.15, 1.72), 0.27).mirror_x(), 0.04)                       # exhaust stacks
    s = s.ss(cyl((0.7, 8.85, 1.72), (0.7, 9.4, 1.72), 0.16, 0.02).mirror_x(), 0.02)
    s = s.su(ribs((0.7, 8.3, 1.72), (0.7, 9.0, 1.72), 0.33, 2, 0.05).mirror_x(), 0.0)
    for y in (6.2, 6.6, 7.0):                                                                       # side louvres
        s = s.ss(round_box(0.08, 0.09, 0.6, 0.03, (1.92, y, 0.1)).mirror_x(), 0.02)
    return s


GP = Group(W, "Pelvis")


@_def("s_robot_pelvis", GP, 700, 150, "Robot hips (lead Pelvis): waist bellows, hip block, ball joints, front plate.",
      extra=_ext((-2.0, 3.3, -1.4), (2.0, 5.3, 1.4)))
def pelvis():
    s = round_box(1.3, 0.6, 0.95, 0.2, (0, 4.2, 0.03))
    s = s.su(cyl((0, 4.3, 0.03), (0, 5.0, 0.03), 1.0, 0.05), 0.03)
    s = s.su(ribs((0, 4.45, 0.03), (0, 5.05, 0.03), 1.12, 3, 0.06), 0.0)
    s = s.su(cyl((0.75, 4.15, 0.0), (1.72, 4.15, 0.0), 0.72, 0.1).mirror_x(), 0.03)
    s = s.su(round_box(0.5, 0.5, 0.12, 0.06, (0, 4.0, -1.0)), 0.03)
    return s


# ------------------------------------------------------------------------------------------------ legs
GT, GS = Group(W, "limb4"), Group(W, "limb6", ["foot8"])


@_def("s_robot_thigh", GT, 600, 150, "Robot thigh (lead: hip limb): piston sleeve with ring flanges, knee hinge drum.",
      extra=_ext((0.2, 1.4, -0.8), (1.7, 5.2, 0.75)), mirror=True, smooth=2)
def thigh():
    s = cyl((0.91, 4.7, 0.0), (0.91, 2.9, -0.1), 0.56, 0.06)
    s = s.su(cyl((0.91, 3.0, -0.1), (0.91, 2.1, -0.14), 0.36), 0.03)
    s = s.su(ribs((0.91, 4.4, -0.02), (0.91, 3.0, -0.09), 0.66, 2, 0.13), 0.0)
    s = s.su(cyl((0.36, 2.02, -0.14), (1.46, 2.02, -0.14), 0.47, 0.06), 0.03)                       # knee drum
    s = s.su(cyl((0.28, 2.02, -0.14), (1.54, 2.02, -0.14), 0.2, 0.03), 0.0)
    return s


@_def("s_robot_shin", GS, 900, 160, "Robot shin and boot (lead: knee limb, member foot): bell shin, ankle ring, boot with toe cap and heel.",
      extra=_ext((0.15, 0.0, -1.25), (1.7, 2.3, 0.75)), mirror=True, smooth=2)
def shin():
    s = round_cone((0.91, 1.75, -0.12), (0.91, 0.75, -0.02), 0.42, 0.62)
    s = SDF(lambda p, s=s: np.maximum(s(p), p[:, 1] - 2.0))
    s = s.su(cyl((0.91, 0.5, -0.02), (0.91, 0.66, -0.02), 0.74, 0.04), 0.02)
    s = s.su(round_box(0.6, 0.235, 0.84, 0.09, (0.91, 0.26, -0.19)), 0.03)
    s = s.su(ellipsoid(0.6, 0.36, 0.42, (0.91, 0.3, -0.78)), 0.05)                                  # toe cap
    s = s.su(round_box(0.5, 0.2, 0.2, 0.06, (0.91, 0.24, 0.62)), 0.03)                              # heel
    return SDF(lambda p: np.maximum(s(p), 0.012 - p[:, 1]))


# ------------------------------------------------------------------------------------------------ arms
GA, GF = Group(W, "limb10"), Group(W, "limb12", ["hand14"])


@_def("s_robot_arm", GA, 600, 150, "Robot upper arm (lead: arm limb): shoulder ball, sleeve with ring flanges.",
      extra=_ext((1.5, 5.3, -1.1), (3.6, 8.9, 0.8)), mirror=True, smooth=2)
def arm():
    a, b = np.array((2.05, 7.95, 0.02)), np.array((2.93, 5.95, -0.4))
    s = sphere(0.66, (2.2, 8.0, 0.03))
    s = s.su(cyl(a, b, 0.4, 0.05), 0.04)
    s = s.su(ribs(a + (b - a) * 0.4, b, 0.52, 2, 0.12), 0.0)
    return s


@_def("s_robot_fore", GF, 1000, 160, "Robot forearm and clamp hand (lead: forearm limb, member hand): elbow ball, gauntlet sleeve, wrist ring, palm block "
      "and three clamp fingers.", extra=_ext((2.1, 2.5, -1.9), (3.9, 6.5, 0.2)), mirror=True, smooth=2)
def fore():
    a, b = np.array((2.9, 5.85, -0.4)), np.array((2.98, 4.25, -0.82))
    s = sphere(0.5, (2.9, 5.92, -0.39))
    s = s.su(cyl(a + (b - a) * 0.2, b, 0.55, 0.07), 0.03)
    s = s.su(cyl(b, b + (b - a) * 0.12, 0.64, 0.04), 0.0)                                           # wrist ring
    s = s.su(round_box(0.5, 0.38, 0.5, 0.1, (2.98, 3.68, -0.93)), 0.03)
    for (x, z) in ((2.62, -1.2), (3.34, -1.2), (2.98, -0.52)):                                      # clamp fingers
        s = s.su(round_box(0.15, 0.36, 0.17, 0.06, (x, 3.08, z)), 0.03)
        s = s.su(round_box(0.15, 0.13, 0.17, 0.05, (x, 2.8, z + (0.16 if z < -1 else -0.16))), 0.03)
    return s


# ------------------------------------------------------------------------------------------------ head
GH = Group(W, "Head")


@_def("s_robot_head", GH, 1100, 170, "Robot head (lead Head): rounded box, face bezel round eyes and mouth, jaw seam, ribbed neck, top hatch, rear grille.",
      extra=_ext((-1.8, 8.0, -1.65), (1.8, 11.5, 1.6)))
def head():
    s = round_box(1.55, 1.335, 1.385, 0.2, (0, 9.9, 0))
    s = s.su(bezel((0, 9.87), 1.42, 1.18, 0.2, -1.33, -1.55), 0.02)
    s = groove(s, SDF(lambda p: np.maximum(np.abs(p[:, 1] - 9.0) - 0.045, -(p[:, 2] + 1.0))))        # jaw seam, sides and back
    s = s.su(round_box(0.8, 0.07, 0.8, 0.05, (0, 11.26, 0.1)), 0.02)                                # top hatch
    for x in (-1.3, 1.3):
        for y in (8.83, 10.92):
            s = s.su(sphere(0.085, (x, y, -1.55)), 0.01)
    for y in (9.5, 9.9, 10.3):                                                                      # rear grille
        s = s.ss(round_box(0.8, 0.08, 0.08, 0.03, (0, y, 1.4)), 0.02)
    s = s.su(cyl((0, 8.15, 0), (0, 8.7, 0), 0.6, 0.04), 0.02)                                       # neck
    s = s.su(ribs((0, 8.2, 0), (0, 8.62, 0), 0.72, 2, 0.05), 0.0)
    return s
