"""Summon set: generic biped pieces (Plans/Biped.luau): primate torso and face, theropod body, skull and thigh.

Unit pieces are authored in the lead primitive's local frame in studs at the reference size the generator gives
it (`lead=`); members named in a note are primitives the sculpt contains (B:sculpt in Biped.luau).
"""
import numpy as np

import direct
from sdf import *  # noqa: F401,F403
from . import piece


def _pair(fn):
    return fn().mirror_x()


@piece("s_ape_torso", (1.2, 1.3, 1.0), tris=1300, kind="unit", res=120, lead=(1.85, 2.05, 1.5))
def s_ape_torso():
    """Great ape / baboon torso (lead: Torso, +Y up the spine, -Z = chest): massive trapezius and shoulder caps,
    deep pectorals, a pot belly, narrow waist into broad hips, a hunched upper back."""
    s = ellipsoid(0.86, 0.98, 0.7)
    s = s.su(ellipsoid(0.95, 0.42, 0.62, (0, 0.62, 0.05)), 0.3)                       # shoulder girdle
    s = s.su(_pair(lambda: sphere(0.36, (0.74, 0.6, 0.0))), 0.25)                     # shoulder caps
    s = s.su(ellipsoid(0.42, 0.34, 0.34, (0, 0.82, 0.25)), 0.25)                      # trapezius / neck hump
    s = s.su(_pair(lambda: ellipsoid(0.36, 0.26, 0.2, (0.3, 0.42, -0.5))), 0.18)      # pectorals
    s = s.su(ellipsoid(0.58, 0.5, 0.5, (0, -0.35, -0.24)), 0.3)                       # belly
    s = s.su(ellipsoid(0.72, 0.36, 0.58, (0, -0.72, 0.05)), 0.3)                      # hips
    s = s.su(ellipsoid(0.62, 0.55, 0.42, (0, 0.38, 0.36)), 0.3)                       # upper back
    s = s.ss(capsule((0, 0.7, 0.75), (0, -0.6, 0.7), 0.06), 0.12)                     # spine groove
    return s.noise(0.012, 8, seed=7)


def _mask():
    return ellipsoid(0.37, 0.36, 0.24)


def _brow():
    return ellipsoid(0.34, 0.075, 0.13, (0, 0.225, -0.15)).rot(-12, 0, 0).su(_pair(lambda: ellipsoid(0.13, 0.07, 0.1, (0.17, 0.23, -0.17))), 0.05)


@piece("s_primate_face", (0.5, 0.5, 0.6), tris=900, kind="unit", res=120, lead=(0.74, 0.72, 0.48))
def s_primate_face():
    """Primate face (lead: FaceMask; members: Muzzle, BrowRidge): heavy brow ridge, cheekbones, a muzzle with a
    philtrum groove, flat nose with nostril wings, full lips and a chin. The eye zones stay on the mask."""
    s = _mask().su(_brow(), 0.06)
    s = s.su(_pair(lambda: ellipsoid(0.12, 0.08, 0.1, (0.26, -0.06, -0.16))), 0.07)   # cheekbones
    mu = ellipsoid(0.25, 0.17, 0.216, (0, -0.17, -0.276))
    s = s.su(mu, 0.1)
    s = s.su(ellipsoid(0.12, 0.06, 0.06, (0, -0.07, -0.47)), 0.05)                    # nose pad
    s = s.su(_pair(lambda: ellipsoid(0.06, 0.05, 0.05, (0.07, -0.09, -0.46))), 0.03)  # nostril wings
    s = s.ss(capsule((0, -0.13, -0.5), (0, -0.2, -0.49), 0.016), 0.02)                # philtrum
    s = s.su(ellipsoid(0.2, 0.05, 0.08, (0, -0.24, -0.44)), 0.04)                     # upper lip
    s = s.su(ellipsoid(0.17, 0.05, 0.08, (0, -0.31, -0.4)), 0.04)                     # lower lip
    s = s.su(ellipsoid(0.13, 0.08, 0.1, (0, -0.36, -0.3)), 0.06)                      # chin
    return s


@piece("s_primate_mask", (0.5, 0.45, 0.4), tris=700, kind="unit", res=110, lead=(0.74, 0.72, 0.48))
def s_primate_mask():
    """Primate face without the muzzle (baboon, mandrill: their long muzzle stays its own part). Members: BrowRidge."""
    s = _mask().su(_brow(), 0.06)
    return s.su(_pair(lambda: ellipsoid(0.12, 0.08, 0.1, (0.26, -0.06, -0.16))), 0.07)


@piece("s_theropod_body", (0.9, 0.95, 1.8), tris=1400, kind="unit", res=128, lead=(1.25, 1.35, 2.6))
def s_theropod_body():
    """Theropod trunk (lead: Torso, -Z = chest, nearly level): deep chest and furcula at the front, ribcage
    flanks, belly line, the pelvis and big hip muscles at the back where the thighs attach, a spine ridge, the
    neck root rising at the front and the tail root tapering out at the back."""
    s = ellipsoid(0.6, 0.66, 1.25)
    s = s.su(ellipsoid(0.5, 0.56, 0.6, (0, -0.16, -0.62)), 0.3)                        # chest
    s = s.su(_pair(lambda: ellipsoid(0.3, 0.42, 0.55, (0.36, 0.0, 0.42))), 0.25)       # hip muscles
    s = s.su(ellipsoid(0.36, 0.3, 0.55, (0, 0.34, 0.35)), 0.2)                         # pelvis
    s = s.su(round_cone((0, 0.1, 0.7), (0, 0.04, 1.6), 0.46, 0.26), 0.25)              # tail root
    s = s.su(round_cone((0, 0.2, -0.85), (0, 0.55, -1.35), 0.4, 0.3), 0.25)            # neck root
    s = s.su(capsule((0, 0.62, -0.6), (0, 0.6, 0.9), 0.05), 0.08)                      # spine ridge
    for i in range(5):                                                                 # ribs
        z = -0.6 + i * 0.22
        s = s.su(_pair(lambda z=z: capsule((0.5, 0.25, z), (0.54, -0.25, z - 0.06), 0.035)), 0.05)
    return s.noise(0.008, 9, seed=11)


@piece("s_head_theropod", (0.6, 0.55, 1.3), tris=1300, kind="unit", res=128, lead=(0.86, 0.72, 1.0))
def s_head_theropod():
    """Theropod skull (lead: Head; member: Snout): deep, narrow and boxy, an antorbital hollow and the nasal ridge
    along the snout, brow bosses over the eyes, cheek and jaw muscles behind them, a scalloped lip line."""
    head = ellipsoid(0.43, 0.36, 0.5)
    snout = ellipsoid(0.31, 0.24, 0.5, (0, 0, 0)).rot(4, 0, 0).at(0, -0.04, -0.66)
    s = head.su(snout, 0.18)
    s = s.su(ellipsoid(0.3, 0.12, 0.6, (0, 0.17, -0.6)), 0.12)                          # roof of the snout
    s = s.su(_pair(lambda: sphere(0.1, (0.25, 0.3, -0.24))), 0.07)                      # brow bosses
    s = s.su(_pair(lambda: ellipsoid(0.14, 0.2, 0.24, (0.33, -0.12, 0.12))), 0.1)       # jaw muscles
    s = s.ss(_pair(lambda: ellipsoid(0.07, 0.08, 0.17, (0.33, 0.04, -0.7))), 0.05)      # antorbital hollow
    s = s.su(capsule((0, 0.26, -0.3), (0, 0.22, -1.02), 0.05), 0.06)                    # nasal ridge
    s = s.ss(_pair(lambda: sphere(0.04, (0.12, 0.12, -1.1))), 0.02)                     # nostrils
    lip = SDF(lambda p: np.abs(p[:, 1] + 0.18 + 0.025 * np.sin(p[:, 2] * 40)) - 0.012)
    side = SDF(lambda p: 0.27 - np.abs(p[:, 0]))
    s = s.ss(lip.si(side, 0.01).si(SDF(lambda p: p[:, 2] + 0.15), 0.01), 0.015)         # lip line
    return s


@piece("s_drumstick", (0.55, 0.6, 0.6), tris=420, fit=(0.85, 1.0, 1.0), res=110)
def s_drumstick():
    """Theropod thigh (limb frame: hip at -Y, knee at +Y): a great muscle mass at the hip with the tail muscle
    bulging behind, tapering hard into a bony knee."""
    s = round_cone((0, -0.18, 0.02), (0, 0.4, 0.0), 0.36, 0.12)
    s = s.su(ellipsoid(0.33, 0.36, 0.42, (0, -0.15, 0.08)), 0.15)
    s = s.su(ellipsoid(0.22, 0.3, 0.22, (0, -0.05, 0.3)), 0.12)                         # caudofemoralis
    return s.su(sphere(0.1, (0, 0.44, -0.02)), 0.06)
