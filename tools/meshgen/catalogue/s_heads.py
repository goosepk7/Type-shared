"""Summon set: head sculpts ("unit" pieces).

Each is authored in the unit frame of the Head primitive (the head ellipsoid is the sphere of radius 0.5 at the
origin, -Z is the face) at the positions Heads.luau gives the snout, eyes and mouth in that frame (measured in
refs.json). The sculpt contains the head ellipsoid itself, untouched where the builder puts the eyes, so eyes,
lids and brows sit on the surface for every seed and size. Members listed in a note are primitives the
sculpt replaces (B:sculpt in Heads.luau).
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from . import piece

HEAD = sphere(0.5)


def _pair(fn):
    """Mirror a right-side (+x) feature to both sides."""
    return fn().mirror_x()


def _tuft(root, tip, r0, r1=0.055):
    return round_cone(root, tip, r0, r1)


@piece("s_head_canine", (0.6, 0.6, 1.1), tris=1100, kind="unit", res=120)
def s_head_canine():
    """Canine head (wolf, fox, dog): skull blended into a long muzzle, stop, brow, cheek ruffs. Members: Snout."""
    snout = ellipsoid(0.24, 0.215, 0.41, (0, -0.19, -0.57)).rot(4, 0, 0)
    s = HEAD.su(snout, 0.13)
    s = s.su(_pair(lambda: _tuft((0.36, -0.12, 0.02), (0.56, -0.34, 0.12), 0.14)), 0.08)  # cheek ruff
    s = s.su(_pair(lambda: _tuft((0.34, -0.22, 0.1), (0.46, -0.48, 0.22), 0.12)), 0.08)
    s = s.su(ellipsoid(0.1, 0.05, 0.3, (0, -0.02, -0.62)).rot(6, 0, 0), 0.06)  # nose bridge
    s = s.ss(_pair(lambda: capsule((0.1, -0.33, -0.93), (0.26, -0.3, -0.5), 0.022)), 0.03)  # lip line
    return s


@piece("s_head_feline", (0.75, 0.65, 0.65), tris=1000, kind="unit", res=120)
def s_head_feline():
    """Feline head (cat, tiger, lion): broad skull, flared cheek ruffs, soft brow, chin tuft."""
    s = HEAD
    for (a, b, r) in (((0.38, -0.05, 0.0), (0.64, -0.12, 0.08), 0.15), ((0.36, -0.18, 0.02), (0.6, -0.36, 0.1), 0.15), ((0.3, -0.3, 0.05), (0.42, -0.52, 0.12), 0.12)):
        s = s.su(_pair(lambda a=a, b=b, r=r: _tuft(a, b, r)), 0.09)
    s = s.su(ellipsoid(0.12, 0.08, 0.1, (0, -0.44, -0.2)), 0.08)
    return s


@piece("s_head_round", (0.65, 0.65, 0.65), tris=900, kind="unit", res=110)
def s_head_round():
    """Round beast head (bear, cow, pig, mouse, gorilla ...): skull with full cheeks, jowls and a low crown ridge.
    Nothing is added on the front of the face, so it suits every eye and muzzle placement."""
    s = HEAD
    s = s.su(_pair(lambda: ellipsoid(0.2, 0.22, 0.24, (0.36, -0.2, 0.0))), 0.12)
    s = s.su(_pair(lambda: _tuft((0.4, -0.22, 0.08), (0.56, -0.4, 0.18), 0.12)), 0.08)
    s = s.su(ellipsoid(0.2, 0.08, 0.26, (0, 0.44, 0.1)), 0.1)
    s = s.su(ellipsoid(0.3, 0.14, 0.24, (0, -0.42, 0.06)), 0.1)
    return s


@piece("s_head_equine", (0.6, 1.0, 1.3), tris=1200, kind="unit", res=120)
def s_head_equine():
    """Horse head: narrow skull flowing into a long sloping face, round jaw discs, forehead. Members: Snout."""
    snout = ellipsoid(0.34, 0.325, 0.69, (0, 0, 0)).rot(-32, 0, 0).at(0, -0.46, -0.62)
    s = HEAD.su(snout, 0.16)
    s = s.su(_pair(lambda: ellipsoid(0.12, 0.26, 0.26, (0.3, -0.34, -0.12))), 0.1)  # jaw disc
    s = s.su(ellipsoid(0.16, 0.1, 0.34, (0, 0.0, 0.0)).rot(-32, 0, 0).at(0, -0.14, -0.62), 0.1)  # nasal ridge
    return s


@piece("s_head_reptile", (0.6, 0.6, 1.2), tris=1300, kind="unit", res=128)
def s_head_reptile():
    """Reptile head (lizard, raptor, dragon, snake): wedge skull, heavy brow ridges, nostril bumps, cheek plates,
    scaly crown bumps. Members: Snout."""
    snout = ellipsoid(0.36, 0.305, 0.48, (0, -0.06, -0.66)).rot(4, 0, 0)
    s = HEAD.su(snout, 0.14)
    s = s.su(_pair(lambda: capsule((0.2, 0.4, -0.2), (0.42, 0.3, 0.12), 0.085)), 0.07)  # brow ridge (behind the eyes)
    s = s.su(_pair(lambda: sphere(0.075, (0.14, 0.12, -1.02))), 0.05)  # nostril bump
    s = s.ss(_pair(lambda: sphere(0.035, (0.17, 0.15, -1.09))), 0.02)
    s = s.su(_pair(lambda: ellipsoid(0.1, 0.16, 0.2, (0.4, -0.12, 0.06))), 0.08)  # cheek plate
    for z in (-0.02, 0.18, 0.36):
        s = s.su(ellipsoid(0.07, 0.06, 0.09, (0, 0.5 - (z + 0.02) ** 2 * 0.5, z)), 0.04)  # crown bumps
    s = s.su(ellipsoid(0.11, 0.05, 0.36, (0, 0.2, -0.72)), 0.06)  # snout ridge
    return s


@piece("s_head_bird", (0.65, 0.7, 0.7), tris=900, kind="unit", res=110)
def s_head_bird():
    """Bird head: round crown, cheek puffs, swept feather tufts at the nape."""
    s = HEAD
    s = s.su(_pair(lambda: ellipsoid(0.18, 0.2, 0.22, (0.36, -0.16, 0.02))), 0.1)
    for (x, y) in ((0.0, 0.3), (0.2, 0.2), (0.0, 0.05), (0.26, -0.02)):
        s = s.su(_pair(lambda x=x, y=y: _tuft((x, y, 0.3), (x * 1.2, y - 0.06, 0.62), 0.13)), 0.07)
    return s


@piece("s_beak", (0.6, 0.9, 0.7), tris=600, kind="unit", res=110)
def s_beak():
    """Beak, in the unit frame of the upper Beak ellipsoid: hooked upper mandible with a cere, shorter lower
    mandible underneath. Members: BeakLow."""
    up = tube([(0, 0.02, 0.42), (0, 0.1, 0.05), (0, 0.0, -0.3), (0, -0.3, -0.49)], [0.44, 0.4, 0.26, 0.05], k=0.1)
    cere = ellipsoid(0.36, 0.2, 0.16, (0, 0.2, 0.18))
    low = tube([(0, -0.42, 0.4), (0, -0.48, 0.0), (0, -0.44, -0.3)], [0.3, 0.24, 0.08], k=0.08).scale3(1, 0.7, 1)
    s = up.su(cere, 0.08).su(low, 0.04)
    return s.ss(_pair(lambda: sphere(0.045, (0.2, 0.22, 0.05))), 0.02)


@piece("s_head_bug", (0.65, 0.65, 0.7), tris=800, kind="unit", res=110)
def s_head_bug():
    """Insect head: rounded capsule, clypeus plate low on the face, neck collar at the back."""
    s = HEAD
    s = s.su(ellipsoid(0.22, 0.14, 0.12, (0, -0.3, -0.36)), 0.06)
    s = s.su(torus(0.33, 0.07, axis=2).at(0, 0, 0.36), 0.06)
    s = s.su(_pair(lambda: ellipsoid(0.1, 0.12, 0.14, (0.42, -0.14, 0.02))), 0.06)
    return s


@piece("s_head_person", (0.7, 0.7, 0.7), tris=1100, kind="unit", res=120)
def s_head_person():
    """Person head: skull with a chin and jawline, ears, a small nose and neck stub. Members: the nose."""
    s = HEAD
    s = s.su(ellipsoid(0.26, 0.16, 0.24, (0, -0.4, -0.14)), 0.12)  # chin / jaw
    s = s.su(_pair(lambda: ellipsoid(0.07, 0.13, 0.1, (0.5, -0.02, 0.03))), 0.04)  # ears
    s = s.ss(_pair(lambda: ellipsoid(0.03, 0.07, 0.05, (0.57, -0.02, 0.0))), 0.03)
    s = s.su(ellipsoid(0.07, 0.085, 0.09, (0, -0.08, -0.48)), 0.04)  # nose
    s = s.su(cylinder(0.2, 0.12, axis=1, rr=0.04).at(0, -0.5, 0.06), 0.08)
    return s


@piece("s_jaw", (0.6, 0.6, 0.6), tris=500, fit=(1.0, 0.5, 1.5), res=100)
def s_jaw():
    """Lower jaw (fills the Jaw ellipsoid's box, front -Z): U-shaped mandible, rounded chin, jaw muscles at the back."""
    s = ellipsoid(0.46, 0.2, 0.72, (0, 0.02, 0))
    s = s.ss(ellipsoid(0.3, 0.2, 0.55, (0, 0.24, -0.05)), 0.08)
    s = s.su(_pair(lambda: ellipsoid(0.13, 0.17, 0.2, (0.33, 0.06, 0.5))), 0.08)
    return s.su(ellipsoid(0.2, 0.1, 0.12, (0, -0.08, -0.6)), 0.08)
