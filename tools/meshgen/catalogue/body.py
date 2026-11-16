"""Body-plan pieces: each fills the box of the primitive Part it replaces (see catalogue/__init__)."""
import numpy as np

from sdf import (SDF, box, capsule, cone, cylinder, ellipsoid, half_space, round_box, round_cone, sphere, torus, tube, union)

from . import piece


def ring_grooves(shape, axis, positions, radius_fn, r=0.018, k=0.02):
    """Carve shallow rings (segment lines) around `axis` at the given positions."""
    for t in positions:
        R = radius_fn(t)
        ax = [0, 0, 0]
        ax[axis] = t
        g = torus(R, r, axis=axis).at(*ax)
        shape = shape.ss(g, k)
    return shape


# =====================================================================================  BIPED
@piece("biped_torso", (0.95, 0.9, 0.62), tris=1800, fit=(1.78, 1.62, 1.12))
def biped_torso():
    """Tunic torso: broad chest, tucked waist, flared hem, collar roll."""
    base = round_box(0.8, 0.72, 0.5, 0.3)
    chest = ellipsoid(0.86, 0.42, 0.52).at(0, 0.3, -0.01)
    pecs = ellipsoid(0.3, 0.2, 0.14).at(-0.3, 0.3, -0.42) | ellipsoid(0.3, 0.2, 0.14).at(0.3, 0.3, -0.42)
    hem = ellipsoid(0.89, 0.26, 0.56).at(0, -0.55, 0)
    collar = torus(0.3, 0.09).at(0, 0.73, -0.02) | ellipsoid(0.32, 0.08, 0.3).at(0, 0.74, -0.02)
    s = base.su(chest, 0.18).su(pecs, 0.12).su(hem, 0.2).su(collar, 0.1)
    s = s.ss(torus(0.84, 0.016).scale3(1, 1, 0.64).at(0, -0.5, 0), 0.02)  # hem line
    return s


@piece("biped_torso_hard", (0.95, 0.9, 0.62), tris=1400, fit=(1.78, 1.62, 1.12))
def biped_torso_hard():
    """Robot chassis: bevelled box, raised chest plate, vents, shoulder sockets."""
    base = round_box(0.84, 0.78, 0.5, 0.14)
    plate = round_box(0.58, 0.32, 0.06, 0.05).at(0, 0.22, -0.5)
    sockets = sphere(0.24).at(-0.82, 0.5, 0) | sphere(0.24).at(0.82, 0.5, 0)
    s = base.su(plate, 0.04).su(sockets, 0.06)
    for i in range(3):
        s = s.ss(round_box(0.32, 0.022, 0.08, 0.015).at(0, -0.3 - i * 0.11, -0.52), 0.01)
    s = s.ss(box(0.9, 0.018, 0.6).at(0, -0.08, 0) - box(0.8, 0.1, 0.47).at(0, -0.08, 0), 0.01)
    return s


@piece("biped_head", (0.56, 0.56, 0.56), tris=2000, fit=(1, 1, 1))
def biped_head():
    """Round character head: full cranium, soft cheeks and jowls (front stays spherical for eyes/mouth)."""
    cran = sphere(0.48).at(0, 0.02, 0.01)
    cheeks = ellipsoid(0.47, 0.3, 0.41).at(0, -0.16, -0.02)
    occiput = ellipsoid(0.4, 0.36, 0.3).at(0, 0.05, 0.18)
    return cran.su(cheeks, 0.14).su(occiput, 0.1)


@piece("biped_head_hard", (0.52, 0.47, 0.49), tris=1400, fit=(0.92, 0.82, 0.86))
def biped_head_hard():
    """Robot head: bevelled box, visor recess, ear bolts, jaw grille."""
    base = round_box(0.42, 0.4, 0.42, 0.13)
    bolts = cylinder(0.13, 0.46, axis=0, rr=0.03).at(0, 0.0, 0.02)
    s = base.su(bolts, 0.04)
    s = s.ss(round_box(0.34, 0.1, 0.08, 0.05).at(0, 0.06, -0.44), 0.03)
    for i in range(3):
        s = s.ss(round_box(0.2, 0.016, 0.06, 0.012).at(0, -0.2 - i * 0.07, -0.43), 0.008)
    return s


@piece("biped_arm", (0.34, 0.7, 0.36), tris=900, fit=(0.56, 1.28, 0.6))
def biped_arm():
    """Tapered arm: round shoulder, bicep, slight elbow bend, forearm swell, narrow wrist."""
    core = tube([(0, 0.5, 0), (0, -0.02, -0.03), (0, -0.56, -0.01)], [0.27, 0.19, 0.17], k=0.08)
    bicep = ellipsoid(0.21, 0.25, 0.21).at(0, 0.18, -0.05)
    fore = ellipsoid(0.22, 0.22, 0.21).at(0, -0.26, -0.05)
    return core.su(bicep, 0.1).su(fore, 0.1)


def _fist(side):
    palm = round_box(0.37, 0.33, 0.35, 0.2).at(0, 0.0, 0.02)
    knuckles = union(*[sphere(0.115).at(x, 0.11, -0.3) for x in (-0.22, -0.075, 0.075, 0.22)])
    fingers = capsule((-0.24, -0.06, -0.3), (0.24, -0.06, -0.3), 0.15)
    tx = -side * 0.3  # thumb on the inner side (toward the body)
    thumb = capsule((tx, -0.06, 0.02), (tx * 0.62, 0.06, -0.33), 0.13)
    cuff = cylinder(0.3, 0.07, axis=1, rr=0.04).at(0, 0.38, 0.03)
    return palm.su(knuckles, 0.06).su(fingers, 0.08).su(thumb, 0.08).su(cuff, 0.08)


@piece("biped_hand_r", (0.56, 0.56, 0.56), tris=1100, fit=(1, 1, 1))
def biped_hand_r():
    """Chunky fist (right): knuckle row, curled fingers, thumb on the inner side."""
    return _fist(1)


@piece("biped_hand_l", (0.56, 0.56, 0.56), tris=1100, fit=(1, 1, 1))
def biped_hand_l():
    """Chunky fist (left)."""
    return _fist(-1)


def _arm_hand(side):
    arm = biped_arm()
    fist = _fist(side).scale(0.8).at(side * 0.08, -0.76, -0.02)
    return arm.su(fist, 0.07)


@piece("biped_armhand_r", (0.45, 1.0, 0.45), tris=1800)
def biped_armhand_r():
    """Right arm + fist as one sculpt (same colour region; saves a part). Arm-centre origin, studs."""
    return _arm_hand(1)


@piece("biped_armhand_l", (0.45, 1.0, 0.45), tris=1800)
def biped_armhand_l():
    """Left arm + fist as one sculpt."""
    return _arm_hand(-1)


@piece("biped_pauldron", (0.56, 0.62, 0.56), tris=900, fit=(1, 1, 1))
def biped_pauldron():
    """Layered shoulder pad: dome + two overlapping lames + rivets."""
    dome = sphere(0.47) & half_space(1, -1, -0.04)
    lame1 = ellipsoid(0.5, 0.2, 0.46).at(0, -0.17, 0)
    lame2 = ellipsoid(0.46, 0.17, 0.42).at(0, -0.37, 0)
    rivets = union(*[sphere(0.05).at(0.36 * np.cos(a), 0.18, 0.36 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 7)[:-1]])
    return dome.su(lame1, 0.03).su(lame2, 0.03) | rivets


@piece("biped_leg", (0.36, 0.88, 0.38), tris=900, fit=(0.64, 1.63, 0.67))
def biped_leg():
    """Tapered leg: thick thigh, knee cap, slimmer shin down into the boot."""
    core = tube([(0, 0.72, 0), (0, 0.02, -0.02), (0, -0.74, 0.0)], [0.31, 0.22, 0.19], k=0.08)
    thigh = ellipsoid(0.3, 0.32, 0.31).at(0, 0.42, -0.02)
    knee = sphere(0.13).at(0, 0.02, -0.19)
    return core.su(thigh, 0.12).su(knee, 0.08)


@piece("biped_boot", (0.48, 0.24, 0.6), tris=1000, fit=(0.84, 0.4, 1.1))
def biped_boot():
    """Chunky boot: round toe cap, welt sole, heel, cuff."""
    sole = round_box(0.41, 0.07, 0.54, 0.06).at(0, -0.13, 0)
    toe = ellipsoid(0.38, 0.19, 0.32).at(0, -0.03, -0.2)
    shaft = round_box(0.36, 0.17, 0.27, 0.15).at(0, 0.03, 0.22)
    s = toe.su(shaft, 0.14).su(sole, 0.05)
    s = s.ss(box(0.5, 0.012, 0.6).at(0, -0.055, 0), 0.01)  # welt line
    return s


@piece("biped_belt", (1.0, 0.18, 0.7), tris=900, fit=(1.92, 0.28, 1.26))
def biped_belt():
    """Leather belt with a chunky square buckle at the front."""
    band = round_box(0.93, 0.12, 0.6, 0.12)
    buckle = round_box(0.2, 0.14, 0.06, 0.035).at(0, 0, -0.6)
    hole = round_box(0.1, 0.06, 0.2, 0.02).at(0, 0, -0.62)
    prong = capsule((0, 0, -0.66), (0.08, 0.0, -0.66), 0.025)
    return band.su(buckle, 0.03).ss(hole, 0.01) | prong


@piece("nose_bulb", (0.56, 0.56, 0.56), tris=700, fit=(1, 1, 1))
def nose_bulb():
    """Bulbous cartoon nose with nostrils."""
    bridge = ellipsoid(0.3, 0.32, 0.42).at(0, 0.06, 0.05)
    tip = sphere(0.3).at(0, -0.12, -0.18)
    s = bridge.su(tip, 0.2)
    for x in (-0.13, 0.13):
        s = s.ss(sphere(0.075).at(x, -0.36, -0.22), 0.04)
    return s


# =====================================================================================  TOY
@piece("toy_torso", (0.56, 0.56, 0.56), tris=1500, fit=(1, 1, 1))
def toy_torso():
    """Plush pear body with a stitched centre seam."""
    s = sphere(0.45).at(0, 0.04, 0).su(ellipsoid(0.5, 0.36, 0.48).at(0, -0.15, 0), 0.16)
    s = s.ss(torus(0.47, 0.016, axis=0), 0.02)
    return s


@piece("toy_torso_hard", (0.56, 0.56, 0.56), tris=1300, fit=(1, 1, 1))
def toy_torso_hard():
    """Tin-toy drum body (cylinder along X): rolled rims, rivet band."""
    s = cylinder(0.46, 0.44, axis=0, rr=0.08)
    s = s.su(torus(0.46, 0.05, axis=0).at(0.4, 0, 0), 0.03).su(torus(0.46, 0.05, axis=0).at(-0.4, 0, 0), 0.03)
    rivets = union(*[sphere(0.035).at(0.2, 0.47 * np.cos(a), 0.47 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 13)[:-1]])
    return s | rivets


@piece("toy_arm", (0.62, 0.34, 0.34), tris=800, fit=(1.15, 0.6, 0.6))
def toy_arm():
    """Plush sausage arm along X (+X = paw end) with a cuff seam."""
    s = round_cone((-0.3, 0, 0), (0.28, 0, 0), 0.26, 0.3)
    s = s.ss(torus(0.29, 0.014, axis=0).at(0.06, 0, 0), 0.015)
    return s


@piece("toy_leg", (0.62, 0.44, 0.44), tris=900, fit=(1.15, 0.78, 0.78))
def toy_leg():
    """Stubby plush leg along X (-X = sole, foot bulges to local -Z)."""
    col = round_cone((-0.2, 0, 0), (0.5, 0, 0), 0.34, 0.3)
    foot = ellipsoid(0.2, 0.38, 0.42).at(-0.36, 0, -0.03)
    s = col.su(foot, 0.12)
    s = s.ss(torus(0.33, 0.014, axis=0).at(-0.12, 0, 0), 0.015)
    return s


@piece("toy_ear", (0.56, 0.56, 0.3), tris=600, fit=(1, 1, 0.44))
def toy_ear():
    """Round plush ear: thick disc with a cupped inner face."""
    s = ellipsoid(0.5, 0.5, 0.22)
    s = s.ss(ellipsoid(0.34, 0.34, 0.12).at(0, -0.03, -0.2), 0.06)
    return s


# =====================================================================================  QUADRUPED
@piece("quad_chest", (0.6, 0.6, 0.6), tris=1500, fit=(1, 1, 1))
def quad_chest():
    """Chest/shoulder mass with a raised neck root."""
    s = ellipsoid(0.47, 0.46, 0.49).at(0, -0.02, 0.01)
    sh = sphere(0.22).at(-0.3, 0.1, -0.14) | sphere(0.22).at(0.3, 0.1, -0.14)
    neck = ellipsoid(0.3, 0.3, 0.3).at(0, 0.18, -0.26)
    return s.su(sh, 0.14).su(neck, 0.14)


@piece("quad_rump", (0.6, 0.6, 0.6), tris=1300, fit=(1, 1, 1))
def quad_rump():
    """Haunches: two muscular hips blended into the rump."""
    s = ellipsoid(0.47, 0.45, 0.5)
    hips = sphere(0.27).at(-0.24, 0.0, 0.08) | sphere(0.27).at(0.24, 0.0, 0.08)
    return s.su(hips, 0.15)


@piece("quad_head", (0.56, 0.56, 0.56), tris=1600, fit=(1, 1, 1))
def quad_head():
    """Beast head: rounded skull, cheek ruffs, brow ridge."""
    s = sphere(0.46).at(0, 0.02, 0.02)
    cheeks = ellipsoid(0.2, 0.2, 0.22).at(-0.31, -0.13, -0.04) | ellipsoid(0.2, 0.2, 0.22).at(0.31, -0.13, -0.04)
    brow = capsule((-0.2, 0.2, -0.36), (0.2, 0.2, -0.36), 0.06)
    return s.su(cheeks, 0.12).su(brow, 0.1)


@piece("quad_snout", (0.42, 0.34, 0.46), tris=1000, fit=(0.74, 0.58, 0.82))
def quad_snout():
    """Muzzle: rounded box with lip lobes, nostrils and a mouth line."""
    s = round_box(0.34, 0.26, 0.38, 0.2)
    lips = sphere(0.15).at(-0.11, -0.13, -0.3) | sphere(0.15).at(0.11, -0.13, -0.3)
    s = s.su(lips, 0.08)
    for x in (-0.11, 0.11):
        s = s.ss(sphere(0.05).at(x, 0.12, -0.39), 0.03)
    s = s.ss(capsule((-0.3, -0.1, -0.15), (0.3, -0.1, -0.15), 0.012).bend(0.3, axis=0, toward=1), 0.02)
    return s


@piece("quad_leg", (0.34, 0.78, 0.38), tris=900, fit=(0.6, 1.42, 0.67))
def quad_leg():
    """Animal leg: muscled upper, knee, slim fetlock, hoof/paw socket."""
    s = tube([(0, 0.62, 0.03), (0, 0.06, -0.04), (0, -0.5, 0.02), (0, -0.68, -0.02)], [0.3, 0.2, 0.16, 0.19], k=0.06)
    s = s.su(ellipsoid(0.28, 0.3, 0.3).at(0, 0.38, 0.02), 0.12)
    return s


@piece("quad_paw", (0.42, 0.2, 0.55), tris=900, fit=(0.74, 0.3, 0.97))
def quad_paw():
    """Paw: pad with three toe beans."""
    s = ellipsoid(0.34, 0.14, 0.4).at(0, -0.01, 0.06)
    toes = union(*[sphere(0.13).at(x, -0.03, z) for x, z in ((-0.21, -0.32), (0, -0.38), (0.21, -0.32))])
    return s.su(toes, 0.05)


@piece("tail_tuft", (0.62, 0.22, 0.22), tris=800, fit=(1.15, 0.36, 0.36))
def tail_tuft():
    """Tapered tail along X (root at -X) ending in a fur tuft."""
    s = round_cone((-0.52, 0, 0), (0.25, 0, 0), 0.15, 0.09)
    tuft = ellipsoid(0.24, 0.17, 0.17).at(0.34, 0, 0).noise(0.012, 14, 3)
    return s.su(tuft, 0.1)


# =====================================================================================  GOLEM (rock)
def rock(s, amp=0.05, freq=3.2, seed=1):
    return s.noise(amp, freq, seed)


@piece("golem_torso", (1.35, 1.35, 0.98), tris=2200, fit=(2.5, 2.5, 1.75))
def golem_torso():
    """Craggy stone torso: heavy chest slab, fissures."""
    base = round_box(1.15, 1.15, 0.8, 0.45)
    chest = ellipsoid(1.2, 0.62, 0.85).at(0, 0.45, -0.04)
    s = rock(base.su(chest, 0.25), 0.06, 2.6, 2)
    s = s.ss(capsule((-0.7, 0.2, -0.86), (-0.2, -0.5, -0.86), 0.03), 0.05)
    s = s.ss(capsule((0.5, 0.7, -0.86), (0.85, 0.0, -0.8), 0.03), 0.05)
    return s


@piece("golem_head", (0.72, 0.62, 0.64), tris=1300, fit=(1.3, 1.12, 1.15))
def golem_head():
    """Boulder head with a heavy brow shelf."""
    s = round_box(0.6, 0.5, 0.52, 0.22).su(ellipsoid(0.62, 0.16, 0.3).at(0, 0.3, -0.3), 0.1)
    return rock(s, 0.04, 3.4, 3)


@piece("golem_arm", (0.54, 1.2, 0.56), tris=1200, fit=(0.95, 2.2, 1.0))
def golem_arm():
    """Stacked rock arm: shoulder stone, elbow stone, forearm."""
    a = ellipsoid(0.46, 0.55, 0.48).at(0, 0.5, 0)
    b = ellipsoid(0.4, 0.42, 0.42).at(0, -0.12, -0.02)
    c = ellipsoid(0.44, 0.48, 0.46).at(0, -0.6, 0)
    return rock(a.su(b, 0.12).su(c, 0.12), 0.04, 3.6, 4)


@piece("golem_fist", (0.74, 0.68, 0.74), tris=1200, fit=(1.32, 1.19, 1.32))
def golem_fist():
    """Rock fist with knuckle stones."""
    s = round_box(0.6, 0.54, 0.6, 0.28)
    kn = union(*[sphere(0.2).at(x, 0.14, -0.52) for x in (-0.36, -0.12, 0.12, 0.36)])
    return rock(s.su(kn, 0.08), 0.035, 4.0, 5)


@piece("golem_leg", (0.54, 1.0, 0.6), tris=1100, fit=(0.95, 1.75, 1.05))
def golem_leg():
    """Pillar leg: thigh stone over a wide foot stone."""
    a = ellipsoid(0.46, 0.5, 0.48).at(0, 0.4, 0.02)
    b = round_box(0.46, 0.34, 0.52, 0.22).at(0, -0.48, -0.02)
    return rock(a.su(b, 0.15), 0.04, 3.4, 6)


@piece("boulder", (0.56, 0.56, 0.56), tris=900, fit=(1, 1, 1))
def boulder():
    """Weathered boulder."""
    return rock(sphere(0.46).su(ellipsoid(0.45, 0.32, 0.4).at(0.05, -0.12, 0.05), 0.15), 0.05, 3.6, 7)


@piece("gem", (0.56, 0.56, 0.56), tris=400, fit=(1, 1, 1), smooth=0, res=44)
def gem():
    """Cut gem: octahedral crystal with a table."""
    f = SDF(lambda p: (np.abs(p[:, 0]) + np.abs(p[:, 1]) * 0.8 + np.abs(p[:, 2]) - 0.5) * 0.57)
    return f & half_space(1, 1, 0.3)


@piece("bevel_box", (0.56, 0.56, 0.56), tris=700, fit=(1, 1, 1))
def bevel_box():
    """Machined block: bevelled edges and a panel seam (generic hard-surface block)."""
    s = round_box(0.5, 0.5, 0.5, 0.1)
    s = s.ss(box(0.6, 0.012, 0.6) - box(0.47, 0.1, 0.47), 0.008)
    return s


# =====================================================================================  DINO
@piece("dino_head", (0.66, 0.58, 0.95), tris=1800, fit=(1.18, 1.02, 1.75))
def dino_head():
    """Reptile head: cranium, long snout, brow ridges, nostril bumps."""
    cran = ellipsoid(0.56, 0.46, 0.5).at(0, 0.06, 0.32)
    snout = round_box(0.42, 0.3, 0.52, 0.26).at(0, -0.06, -0.33)
    brows = ellipsoid(0.15, 0.1, 0.26).at(-0.33, 0.34, 0.02) | ellipsoid(0.15, 0.1, 0.26).at(0.33, 0.34, 0.02)
    nos = sphere(0.09).at(-0.15, 0.2, -0.76) | sphere(0.09).at(0.15, 0.2, -0.76)
    s = cran.su(snout, 0.28).su(brows, 0.1).su(nos, 0.06)
    for x in (-0.15, 0.15):
        s = s.ss(sphere(0.045).at(x, 0.24, -0.84), 0.02)
    return s


@piece("dino_jaw", (0.56, 0.22, 0.86), tris=1000, fit=(1.01, 0.36, 1.575))
def dino_jaw():
    """Lower jaw: U-shaped, rounded chin, jaw-muscle bulges at the back."""
    s = round_box(0.46, 0.15, 0.74, 0.14)
    s = s.su(ellipsoid(0.2, 0.17, 0.25).at(-0.32, 0.0, 0.45) | ellipsoid(0.2, 0.17, 0.25).at(0.32, 0.0, 0.45), 0.08)
    return s


@piece("dino_leg", (0.4, 1.45, 0.52), tris=1100, fit=(0.72, 2.7, 0.95))
def dino_leg():
    """Powerful hind leg: big thigh, reverse knee hint, sturdy shin."""
    thigh = ellipsoid(0.36, 0.62, 0.44).at(0, 0.66, 0.02)
    shin = round_cone((0, 0.12, 0.06), (0, -1.22, -0.04), 0.25, 0.2)
    return thigh.su(shin, 0.22)


@piece("dino_foot", (0.5, 0.25, 0.8), tris=1100, fit=(0.88, 0.42, 1.45))
def dino_foot():
    """Three-toed foot with blunt claws."""
    pad = ellipsoid(0.4, 0.17, 0.42).at(0, -0.02, 0.18)
    toes = union(*[capsule((x * 0.4, -0.04, 0.1), (x, -0.06, -0.48), 0.13) for x in (-0.26, 0, 0.26)])
    claws = union(*[round_cone((x, -0.04, -0.5), (x, -0.12, -0.7), 0.1, 0.03) for x in (-0.26, 0, 0.26)])
    return pad.su(toes, 0.1).su(claws, 0.04)


@piece("dino_arm", (0.16, 0.36, 0.16), tris=500, fit=(0.26, 0.62, 0.26))
def dino_arm():
    """Tiny forelimb with a two-claw hand."""
    s = round_cone((0, 0.26, 0), (0, -0.14, 0), 0.12, 0.085)
    hand = union(round_cone((0, -0.16, 0), (-0.04, -0.3, -0.02), 0.08, 0.025), round_cone((0, -0.16, 0), (0.04, -0.3, -0.02), 0.08, 0.025))
    return s.su(hand, 0.04)


@piece("dino_tail1", (1.05, 0.66, 0.66), tris=1100, fit=(2.0, 1.2, 1.2))
def dino_tail1():
    """Tail base along X (root at +X, toward the hips), tapering back, dorsal ridge."""
    s = round_cone((0.55, 0, 0), (-0.75, -0.02, 0), 0.58, 0.4)
    ridge = capsule((0.4, 0.5, 0), (-0.8, 0.34, 0), 0.06)
    return s.su(ridge, 0.12)


@piece("dino_tail2", (0.42, 0.44, 1.2), tris=900, fit=(0.78, 0.82, 2.3))
def dino_tail2():
    """Tail tip (wedge box): thick at +Z, tapering to a point at front-bottom."""
    return round_cone((0, 0.02, 0.85), (0, -0.3, -1.12), 0.38, 0.04)


# =====================================================================================  WEDGE-BOX SPIKES
# all fill the wedge triangle; base face = bottom (y=-.5), apex at (y=+.5, z=+.5)
def _spike_tube(pts, radii, k=0.06):
    return tube(pts, radii, k)


@piece("horn", (0.32, 0.56, 0.56), tris=900, fit=(0.32, 1.0, 0.46))
def horn():
    """Curved ram/demon horn with growth ridges."""
    s = _spike_tube([(0, -0.48, -0.06), (0, -0.12, 0.0), (0, 0.22, 0.18), (0, 0.48, 0.44)], [0.3, 0.24, 0.14, 0.03])
    for y in (-0.3, -0.12, 0.06):
        s = s.ss(torus(0.29 - (y + 0.3) * 0.45, 0.012).at(0, y, (y + 0.48) * 0.12), 0.012)
    return s


@piece("spike", (0.3, 0.56, 0.56), tris=500, fit=(0.3, 1.0, 0.62))
def spike_():
    """Back spike: slightly swept cone."""
    return _spike_tube([(0, -0.5, 0.0), (0, 0.0, 0.14), (0, 0.48, 0.42)], [0.3, 0.17, 0.02])


@piece("claw", (0.26, 0.56, 0.56), tris=500, fit=(0.26, 1.0, 0.55))
def claw():
    """Hooked claw."""
    return _spike_tube([(0, -0.5, -0.12), (0, -0.05, -0.08), (0, 0.3, 0.12), (0, 0.48, 0.46)], [0.26, 0.19, 0.1, 0.02])


@piece("tusk", (0.3, 0.56, 0.56), tris=600, fit=(0.3, 1.0, 0.38))
def tusk():
    """Ivory tusk: rounded root, smooth upward curve."""
    return _spike_tube([(0, -0.48, -0.1), (0, -0.05, -0.08), (0, 0.3, 0.12), (0, 0.48, 0.42)], [0.28, 0.24, 0.15, 0.04])


@piece("fang", (0.3, 0.56, 0.56), tris=400, fit=(0.16, 0.3, 0.22))
def fang():
    """Fang: tapered, slightly curved tooth."""
    return _spike_tube([(0, -0.5, -0.02), (0, 0.1, 0.12), (0, 0.48, 0.42)], [0.32, 0.18, 0.02])


@piece("ear_long", (0.2, 0.56, 0.56), tris=700, fit=(0.16, 1.0, 0.45))
def ear_long():
    """Long pointed goblin ear: leaf blade with a cupped inner groove."""
    blade = _spike_tube([(0, -0.46, -0.08), (0, -0.05, 0.02), (0, 0.48, 0.46)], [0.36, 0.3, 0.02]).scale3(0.4, 1, 1)
    groove = _spike_tube([(-0.12, -0.32, -0.06), (-0.12, 0.0, 0.03), (-0.12, 0.36, 0.34)], [0.18, 0.15, 0.02]).scale3(0.4, 1, 1)
    return blade.ss(groove, 0.03)


@piece("fin", (0.2, 0.56, 0.56), tris=900, fit=(0.16, 1.0, 1.1))
def fin():
    """Fin membrane: swept triangle with a concave trailing edge and rays."""
    tri = SDF(lambda p: np.maximum(np.maximum(p[:, 1] - p[:, 2] - 0.02, -p[:, 1] - 0.5), p[:, 2] - 0.5))
    plate = tri.round(0.02) & box(0.04, 0.6, 0.6)
    plate = plate.ss(sphere(0.62).at(0, 0.62, -0.3), 0.04)  # concave leading curve
    rays = union(*[capsule((0, -0.48, z0), (0, 0.4, 0.46), 0.035) for z0 in (-0.35, -0.05, 0.25)]) & tri.round(0.0)
    return plate.su(rays, 0.03)


@piece("crest", (0.2, 0.56, 0.56), tris=700, fit=(0.14, 0.6, 0.65))
def crest():
    """Feathered crest: three rounded plumes."""
    plumes = union(*[round_cone((0, -0.45, z), (0, 0.45 - i * 0.25, 0.45 - i * 0.1), 0.16, 0.06) for i, z in enumerate((0.2, -0.05, -0.3))], k=0.06)
    return plumes.scale3(0.4, 1, 1)


@piece("stinger", (0.3, 0.56, 0.56), tris=500, fit=(0.16, 0.55, 0.24))
def stinger():
    """Stinger: bulb base, needle tip."""
    return sphere(0.3).at(0, -0.3, 0).su(round_cone((0, -0.25, 0.02), (0, 0.48, 0.42), 0.22, 0.01), 0.1)


@piece("mandible", (0.3, 0.56, 0.56), tris=500, fit=(0.14, 0.2, 0.62))
def mandible():
    """Curved pincer (base at the back face, tip at the front-bottom)."""
    return _spike_tube([(0, 0.15, 0.5), (0, 0.05, 0.0), (0, -0.2, -0.32), (0, -0.48, -0.5)], [0.32, 0.26, 0.15, 0.02])


@piece("crystal", (0.32, 0.56, 0.56), tris=500, fit=(0.42, 0.95, 0.75), smooth=0, res=48)
def crystal():
    """Hexagonal crystal shard with a point, leaning back."""
    def hexp(p):
        q = np.abs(p[:, [0, 2]])
        d = np.maximum(q[:, 0] * 0.866 + q[:, 1] * 0.5, q[:, 1]) - 0.24
        return d

    prism = SDF(lambda p: np.maximum(hexp(p), np.abs(p[:, 1]) - 0.4))
    tip = SDF(lambda p: hexp(p) + (p[:, 1] - 0.3) * 0.8)
    s = (prism & tip).rot(28, 0, 0).at(0, -0.04, 0.1)
    return s & half_space(1, -1, -0.5)


@piece("hood", (0.2, 0.56, 0.56), tris=700, fit=(0.16, 1.0, 0.75))
def hood():
    """Cobra hood flap: rounded leaf plate with a rib."""
    s = ellipsoid(0.05, 0.5, 0.36).at(0, 0, 0.1).bend(0.4, axis=1, toward=0)
    rib = capsule((0.02, -0.45, 0.15), (0.02, 0.4, 0.2), 0.04)
    return s.su(rib, 0.04)


# =====================================================================================  INSECT / SPIDER
@piece("insect_thorax", (0.56, 0.56, 0.56), tris=1000, fit=(1, 1, 1))
def insect_thorax():
    """Thorax with a pronotum shield and a neck collar."""
    s = sphere(0.45).su(ellipsoid(0.46, 0.22, 0.4).at(0, 0.25, -0.02), 0.1)
    s = s.ss(torus(0.38, 0.02, axis=2).at(0, 0, -0.3), 0.02)
    return s


@piece("insect_abdomen", (0.56, 0.56, 0.62), tris=1400, fit=(1, 0.98, 1))
def insect_abdomen():
    """Segmented abdomen tapering to a rear point."""
    s = ellipsoid(0.48, 0.46, 0.42).at(0, 0, -0.05).su(round_cone((0, 0, 0.1), (0, -0.02, 0.48), 0.3, 0.06), 0.15)

    def rad(z):
        return 0.47 * np.sqrt(max(0.0, 1 - ((z + 0.05) / 0.44) ** 2))

    return ring_grooves(s, 2, (-0.18, 0.02, 0.2), rad, r=0.02, k=0.025)


@piece("insect_head", (0.56, 0.56, 0.56), tris=1000, fit=(1, 1, 1))
def insect_head():
    """Insect head: rounded, slightly forward-tapering face with a clypeus plate."""
    s = sphere(0.46).su(ellipsoid(0.3, 0.22, 0.24).at(0, -0.16, -0.26), 0.12)
    return s


@piece("insect_leg", (0.1, 0.1, 0.86), tris=500, fit=(0.17, 0.17, 1.6))
def insect_leg():
    """Jointed leg segment along Z (root knuckle at +Z: builders aim the part's -Z at the foot)."""
    s = round_cone((0, 0, 0.72), (0, 0, -0.75), 0.075, 0.045)
    s = s.su(sphere(0.085).at(0, 0, 0.72), 0.03).su(sphere(0.06).at(0, 0, 0.0), 0.03)
    return s


@piece("spider_ceph", (0.56, 0.56, 0.56), tris=1100, fit=(1, 0.96, 1))
def spider_ceph():
    """Cephalothorax: domed head region with a fovea groove."""
    s = ellipsoid(0.5, 0.42, 0.5).su(sphere(0.32).at(0, 0.12, -0.2), 0.15)
    s = s.ss(capsule((0, 0.42, 0.05), (0, 0.38, 0.25), 0.03), 0.03)
    return s


@piece("spider_abdomen", (0.56, 0.56, 0.62), tris=1400, fit=(1, 0.97, 1))
def spider_abdomen():
    """Big bulbous spider abdomen with spinnerets."""
    s = ellipsoid(0.48, 0.46, 0.48).at(0, 0.01, -0.02).su(ellipsoid(0.36, 0.34, 0.3).at(0, -0.06, 0.2), 0.15)
    spin = round_cone((0, -0.12, 0.38), (0, -0.16, 0.52), 0.09, 0.05)
    return s.su(spin, 0.06)


# =====================================================================================  SERPENT
@piece("serpent_head", (0.56, 0.56, 0.56), tris=1500, fit=(1, 0.78, 1.1))
def serpent_head():
    """Snake head: flat broad skull with brow scales."""
    s = ellipsoid(0.5, 0.36, 0.52).su(ellipsoid(0.42, 0.28, 0.4).at(0, -0.06, -0.15), 0.1)
    brows = ellipsoid(0.15, 0.08, 0.2).at(-0.24, 0.27, -0.12) | ellipsoid(0.15, 0.08, 0.2).at(0.24, 0.27, -0.12)
    return s.su(brows, 0.08)


@piece("serpent_snout", (0.38, 0.24, 0.34), tris=800, fit=(0.68, 0.42, 0.6))
def serpent_snout():
    """Rounded snout with nostril pits and a mouth line."""
    s = round_box(0.33, 0.2, 0.29, 0.16)
    for x in (-0.12, 0.12):
        s = s.ss(sphere(0.035).at(x, 0.14, -0.28), 0.02)
    s = s.ss(box(0.4, 0.012, 0.35).at(0, -0.06, -0.05), 0.012)
    return s


@piece("serpent_seg", (0.56, 0.56, 0.56), tris=900, fit=(1, 1, 1))
def serpent_seg():
    """Body segment: round with a dorsal scale ridge and belly flat."""
    s = sphere(0.47).su(capsule((0, 0.44, -0.28), (0, 0.44, 0.28), 0.06), 0.08)
    s = s.ss(torus(0.47, 0.014, axis=2).at(0, 0, 0.1), 0.015)
    return s


# =====================================================================================  BIRD
@piece("bird_body", (0.56, 0.56, 0.6), tris=1500, fit=(1, 1, 1))
def bird_body():
    """Plump bird body: puffed chest, tapered rump."""
    s = ellipsoid(0.46, 0.46, 0.48).su(sphere(0.38).at(0, -0.06, -0.14), 0.15).su(round_cone((0, 0.05, 0.15), (0, 0.15, 0.5), 0.3, 0.1), 0.16)
    return s


@piece("bird_head", (0.56, 0.56, 0.56), tris=1300, fit=(1, 1, 1))
def bird_head():
    """Bird head: round crown with cheek puffs."""
    s = sphere(0.46).at(0, 0.03, 0.02)
    cheeks = ellipsoid(0.18, 0.2, 0.2).at(-0.3, -0.16, -0.1) | ellipsoid(0.18, 0.2, 0.2).at(0.3, -0.16, -0.1)
    return s.su(cheeks, 0.12)


@piece("bird_beak", (0.3, 0.56, 0.56), tris=700, fit=(0.42, 0.3, 0.62))
def bird_beak():
    """Hooked beak: base at the back face, tip at the front-bottom, split mouth line."""
    s = _spike_tube([(0, 0.0, 0.45), (0, 0.04, 0.05), (0, -0.12, -0.3), (0, -0.46, -0.5)], [0.4, 0.3, 0.17, 0.03])
    s = s.ss(box(0.5, 0.012, 0.4).at(0, -0.12, 0.2).rot(-12, 0, 0), 0.01)
    return s


@piece("bird_wing", (0.12, 0.6, 0.6), tris=1300, fit=(0.16, 1.0, 1.0))
def bird_wing():
    """Feathered wing (wedge frame: root at y=-.5, tip at y=+.5/z=+.5); scalloped primaries."""
    tri = SDF(lambda p: np.maximum(np.maximum(p[:, 1] - p[:, 2] - 0.06, -p[:, 1] - 0.5), p[:, 2] - 0.5))
    plate = tri.round(0.03) & box(0.05, 0.6, 0.6)
    plate = plate.ss(sphere(0.6).at(0, 0.62, -0.35), 0.05)  # rounded leading edge
    for i in range(6):  # primary feather notches along the trailing edge (z=+.5)
        y = -0.3 + i * 0.15
        plate = plate.ss(sphere(0.07).at(0, y, 0.52), 0.02)
    covert = ellipsoid(0.07, 0.3, 0.32).at(0, -0.28, -0.1)
    return plate.su(covert, 0.05)


@piece("bird_feathers", (0.56, 0.12, 0.56), tris=700, fit=(1.05, 0.12, 0.69))
def bird_feathers():
    """Feather layer: overlapping rounded feather tips."""
    feathers = union(*[ellipsoid(0.16, 0.04, 0.42).rot(0, a, 0).at(x, 0, 0.05) for x, a in zip(np.linspace(-0.38, 0.38, 5), np.linspace(-14, 14, 5))], k=0.03)
    return feathers


@piece("bird_tailfan", (0.56, 0.12, 0.56), tris=800, fit=(0.95, 0.14, 0.95))
def bird_tailfan():
    """Tail fan: five feathers spreading backward (+Z)."""
    fs = []
    for a in np.linspace(-38, 38, 5):
        fs.append(ellipsoid(0.12, 0.05, 0.42).at(0, 0, 0.4).rot(0, a, 0))
    return union(*fs, k=0.04)


@piece("bird_foot", (0.3, 0.12, 0.36), tris=600, fit=(0.5, 0.16, 0.6))
def bird_foot():
    """Three-toed bird foot (toes toward local +Z) with a rear spur."""
    toes = union(*[capsule((0, 0, -0.1), (np.sin(np.radians(a)) * 0.38, -0.01, -0.1 + np.cos(np.radians(a)) * 0.38), 0.07) for a in (-35, 0, 35)])
    spur = capsule((0, 0, -0.1), (0, 0.0, -0.3), 0.06)
    return toes.su(spur, 0.04).su(sphere(0.1).at(0, 0.02, -0.1), 0.05)


# =====================================================================================  FISH
@piece("fish_body", (0.56, 0.56, 0.56), tris=1500, fit=(1, 1, 1))
def fish_body():
    """Fish body with gill arcs and a ventral keel."""
    s = ellipsoid(0.44, 0.48, 0.5)
    for x in (-1, 1):
        s = s.ss(torus(0.32, 0.016, axis=2).at(0, 0, -0.02).warp(lambda p, x=x: p) & half_space(0, -x, 0.2 * x) & half_space(2, 1, 0.1), 0.015)
    return s


@piece("fish_rear", (0.56, 0.56, 0.62), tris=900, fit=(1, 1, 1))
def fish_rear():
    """Tail stock: tapering toward the tail (+Z)."""
    return round_cone((0, 0, -0.18), (0, 0.02, 0.36), 0.42, 0.14).scale3(0.85, 1, 1)


@piece("fish_tail", (0.12, 0.6, 0.6), tris=900, fit=(0.16, 0.95, 0.95))
def fish_tail():
    """Tail lobe: crescent fin with rays (wedge frame)."""
    tri = SDF(lambda p: np.maximum(np.maximum(p[:, 1] - p[:, 2] - 0.05, -p[:, 1] - 0.5), p[:, 2] - 0.5))
    plate = tri.round(0.03) & box(0.04, 0.6, 0.6)
    plate = plate.ss(sphere(0.48).at(0, -0.2, 0.75), 0.05)  # crescent bite out of the trailing edge
    rays = union(*[capsule((0, -0.45, -0.4), (0, y, 0.48), 0.03) for y in (-0.42, 0.0, 0.42)]) & tri
    return plate.su(rays, 0.03)


@piece("fish_lips", (0.36, 0.2, 0.2), tris=600, fit=(0.62, 0.3, 0.3))
def fish_lips():
    """Pouty fish lips."""
    up = capsule((-0.22, 0.05, 0), (0.22, 0.05, 0), 0.1).bend(-0.6, axis=0, toward=1)
    lo = capsule((-0.2, -0.07, 0.01), (0.2, -0.07, 0.01), 0.1).bend(0.5, axis=0, toward=1)
    return up.su(lo, 0.04)


# =====================================================================================  FLOATER / BLOB
@piece("ghost_body", (0.56, 0.6, 0.56), tris=1500, fit=(1, 1, 1))
def ghost_body():
    """Ghost head: soft dome with a gently peaked crown."""
    s = sphere(0.47).su(round_cone((0, 0.2, 0.05), (0.04, 0.48, 0.1), 0.26, 0.05), 0.2)
    return s


@piece("ghost_skirt", (0.62, 0.62, 0.62), tris=1400, fit=(1, 1, 1))
def ghost_skirt():
    """Flowing sheet below the head (cylinder axis X = up): flared, swirling, scalloped hem at -X."""
    s = cone(0.5, 0.42, 0.45, axis=0, rr=0.04)
    for a in np.linspace(0, 2 * np.pi, 8)[:-1]:
        s = s.ss(sphere(0.16).at(-0.5, 0.5 * np.cos(a), 0.5 * np.sin(a)), 0.06)
    return s.twist(1.0, axis=0)


@piece("ghost_hand", (0.56, 0.56, 0.56), tris=700, fit=(1, 1, 1))
def ghost_hand():
    """Wispy mitten hand."""
    return ellipsoid(0.42, 0.38, 0.45).su(ellipsoid(0.16, 0.24, 0.16).at(0, 0.28, -0.2), 0.1).su(round_cone((0, 0, 0.2), (0, 0.1, 0.5), 0.25, 0.06), 0.1)


@piece("slime_body", (0.6, 0.62, 0.6), tris=1800, fit=(1, 1, 1))
def slime_body():
    """Gumdrop slime: wide base, soft shoulders, curled drip on top."""
    base = ellipsoid(0.5, 0.36, 0.5).at(0, -0.12, 0)
    top = sphere(0.4).at(0, 0.06, 0)
    curl = round_cone((0, 0.3, 0), (0.06, 0.52, 0.08), 0.18, 0.05)
    return base.su(top, 0.22).su(curl, 0.14)


@piece("slime_puddle", (0.2, 0.62, 0.62), tris=900, fit=(0.24, 1.12, 1.12))
def slime_puddle():
    """Wavy slime puddle (disc, axis X)."""
    s = cylinder(0.45, 0.07, axis=0, rr=0.06)
    lobes = union(*[sphere(0.14).at(0, 0.45 * np.cos(a), 0.45 * np.sin(a)).scale3(0.5, 1, 1) for a in np.linspace(0, 2 * np.pi, 10)[:-1]])
    return s.su(lobes, 0.06)


@piece("droplet", (0.56, 0.62, 0.56), tris=500, fit=(1, 1, 1))
def droplet():
    """Liquid droplet."""
    return sphere(0.4).at(0, -0.1, 0).su(round_cone((0, -0.05, 0), (0, 0.5, 0), 0.3, 0.02), 0.15)


# =====================================================================================  VEHICLE / SHIP
@piece("veh_chassis", (1.22, 0.46, 1.74), tris=1600, fit=(2.3, 0.82, 3.3))
def veh_chassis():
    """Car body: bevelled tub with wheel arches, bumpers, panel line."""
    s = round_box(1.12, 0.39, 1.62, 0.18)
    for z in (-1.12, 1.12):
        s = s.ss(cylinder(0.66, 1.3, axis=0).at(0, -0.45, z), 0.08)
    s = s.su(round_box(1.05, 0.12, 0.08, 0.06).at(0, -0.12, -1.6), 0.05).su(round_box(1.05, 0.12, 0.08, 0.06).at(0, -0.12, 1.6), 0.05)
    s = s.ss(box(1.2, 0.012, 1.7).at(0, 0.12, 0), 0.01)
    return s


@piece("veh_cabin", (0.92, 0.56, 0.88), tris=1200, fit=(1.72, 1.0, 1.65))
def veh_cabin():
    """Cabin: rounded cab with a raked windscreen and roof lip."""
    s = round_box(0.84, 0.48, 0.8, 0.16)
    # raked windscreen: cut the front-top edge with a sloped plane
    s = s.ss(SDF(lambda p: -((p[:, 1] - 0.2) * 0.6 - (p[:, 2] + 0.82) * 0.8)), 0.08)
    s = s.su(round_box(0.86, 0.04, 0.82, 0.03).at(0, 0.46, 0.0), 0.02)
    return s


@piece("wheel", (0.32, 0.62, 0.62), tris=1400, fit=(0.55, 1.15, 1.15))
def wheel():
    """Chunky tyre with tread blocks and a recessed rim (axis X)."""
    tyre = torus(0.37, 0.19, axis=0).scale3(1.25, 1, 1)
    treads = union(*[round_box(0.24, 0.05, 0.08, 0.03).rot(np.degrees(a), 0, 0).at(0, 0.53 * np.cos(a), 0.53 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 15)[:-1]])
    rim = cylinder(0.4, 0.16, axis=0, rr=0.05)
    return tyre.su(treads, 0.03).su(rim, 0.05)


@piece("ship_hull", (1.16, 0.64, 1.6), tris=1800, fit=(2.15, 1.15, 3.0))
def ship_hull():
    """Wooden hull: curved bilge, rail lip, recessed deck, strake lines."""
    s = round_box(1.04, 0.55, 1.48, 0.28).si(cylinder(1.65, 2.0, axis=2).at(0, 1.08, 0), 0.15)
    rail = round_box(1.075, 0.07, 1.5, 0.06).at(0, 0.5, 0)
    s = s.su(rail, 0.03)
    s = s.ss(round_box(0.92, 0.12, 1.36, 0.08).at(0, 0.6, 0), 0.03)
    for y in (-0.08, 0.18):
        s = s.ss(box(1.2, 0.012, 1.7).at(0, y, 0) - box(0.9, 0.2, 1.3).at(0, y, 0), 0.01)
    return s


@piece("ship_sail", (1.08, 0.92, 0.32), tris=1000, fit=(2.0, 1.7, 0.5))
def ship_sail():
    """Billowing square sail (bulges forward, -Z), hemmed edges."""
    s = round_box(1.0, 0.85, 0.035, 0.03)
    s = s.warp(lambda p: p + np.column_stack([0 * p[:, 0], 0 * p[:, 0], 0.32 * (1 - (p[:, 0] / 1.0) ** 2) * (1 - 0.5 * (p[:, 1] / 0.85) ** 2)]))
    return s


@piece("ship_crowsnest", (0.22, 0.46, 0.46), tris=800, fit=(0.36, 0.8, 0.8))
def ship_crowsnest():
    """Barrel basket (axis X) with rims and staves."""
    s = cylinder(0.38, 0.17, axis=0, rr=0.03)
    s = s.su(torus(0.38, 0.03, axis=0).at(0.15, 0, 0), 0.02).su(torus(0.38, 0.03, axis=0).at(-0.15, 0, 0), 0.02)
    for a in np.linspace(0, 2 * np.pi, 13)[:-1]:
        s = s.ss(box(0.12, 0.008, 0.03).rot(np.degrees(a), 0, 0).at(0, 0.39 * np.cos(a), 0.39 * np.sin(a)), 0.006)
    return s
