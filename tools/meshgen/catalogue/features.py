"""Hero feature meshes (headwear, held items, back pieces, propulsion).

Anchor-space pieces (no fit) are authored in the units the Luau feature code uses (head radius R,
crown diameter d, ...), relative to the same frame the feature builds from; MeshLibrary.place()
puts them back with the recorded origin. Box pieces fill the Part they replace.
"""
import numpy as np

from sdf import (SDF, box, capsule, cone, cylinder, ellipsoid, half_space, round_box, round_cone, sphere, torus, tube, union)

from . import piece


def tri_mask(slack=0.0):
    """Wedge triangle region in unit box coords."""
    return SDF(lambda p: np.maximum(np.maximum(p[:, 1] - p[:, 2] - slack, -p[:, 1] - 0.5), p[:, 2] - 0.5))


# ===================================================================== headwear (R units, head centre)
@piece("helmet_round", (1.15, 1.4, 1.15), tris=1800)
def helmet_round():
    """Kettle helmet: riveted dome, rolled brim, nose guard, top knob (R units, head centre)."""
    dome = sphere(0.82).at(0, 0.5, 0.06) & half_space(1, -1, 0.36)
    brim = cylinder(1.0, 0.05, axis=1, rr=0.045).at(0, 0.43, 0.04)
    roll = torus(0.97, 0.06).at(0, 0.44, 0.04)
    guard = round_box(0.08, 0.3, 0.05, 0.04).at(0, 0.3, -0.84).rot(-14, 0, 0)
    knob = sphere(0.12).at(0, 1.33, 0.06)
    ridge = torus(0.8, 0.035, axis=0).at(0, 0.5, 0.06) & half_space(1, -1, 0.6)
    rivets = union(*[sphere(0.045).at(0.8 * np.sin(a), 0.62, 0.06 + 0.8 * np.cos(a) * 0.98) for a in np.linspace(0, 2 * np.pi, 11)[:-1]])
    return dome.su(brim, 0.04).su(roll, 0.03).su(guard, 0.05).su(knob, 0.06).su(ridge, 0.03) | rivets


@piece("helmet_cap", (0.56, 0.56, 0.56), tris=900, fit=(1, 1, 1))
def helmet_cap():
    """Box-head helmet cap: bevelled shell with a brow lip and a centre ridge."""
    s = round_box(0.48, 0.42, 0.48, 0.2).at(0, 0.06, 0)
    lip = round_box(0.5, 0.08, 0.5, 0.06).at(0, -0.4, 0)
    ridge = capsule((0, 0.45, -0.4), (0, 0.45, 0.4), 0.05)
    return s.su(lip, 0.04).su(ridge, 0.05)


@piece("crown", (0.62, 0.42, 0.62), tris=1600)
def crown():
    """Royal crown (d units, base at y=0): banded ring, five points with pearls."""
    ring = (cylinder(0.5, 0.15, axis=1, rr=0.02).at(0, 0.15, 0)) - cylinder(0.43, 0.3, axis=1).at(0, 0.15, 0)
    rims = torus(0.49, 0.035).at(0, 0.03, 0) | torus(0.49, 0.03).at(0, 0.28, 0)
    pts = []
    for a in np.linspace(0, 2 * np.pi, 6)[:-1] + np.pi / 2:
        c, s_ = np.cos(a), np.sin(a)
        pts.append(round_cone((0.46 * c, 0.26, -0.46 * s_), (0.47 * c, 0.6, -0.47 * s_), 0.11, 0.025).scale3(1, 1, 1))
        pts.append(sphere(0.045).at(0.47 * c, 0.62, -0.47 * s_))
    pts = union(*pts) - cylinder(0.42, 0.6, axis=1).at(0, 0.5, 0)
    return ring.su(rims, 0.02) | pts


def _tricorn_brim():
    def f(p):
        r = np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2)
        th = np.arctan2(p[:, 0], -p[:, 2])
        lift = 0.42 * np.clip((r - 0.45) / 0.72, 0, 1) ** 1.6 * (0.45 + 0.55 * np.cos(3 * th + np.pi))
        q = p.copy()
        q[:, 1] = p[:, 1] - lift
        return q

    return cylinder(1.17, 0.05, axis=1, rr=0.045).warp(f)


@piece("hat_tricorn", (1.25, 0.9, 1.25), tris=1800)
def hat_tricorn():
    """Pirate tricorn (R units, base frame): three upturned brim corners, domed crown, band."""
    brim = _tricorn_brim().at(0, 0.08, 0)
    crown_ = (ellipsoid(0.74, 0.64, 0.72).at(0, 0.12, 0.05) & half_space(1, -1, 0.08))
    band = cylinder(0.75, 0.05, axis=1, rr=0.03).at(0, 0.17, 0.05)
    dent = ellipsoid(0.12, 0.2, 0.5).at(0, 0.82, 0.05)
    return brim.su(crown_, 0.08).su(band, 0.02).ss(dent, 0.08)


@piece("bandana_round", (1.25, 0.8, 1.6), tris=1300)
def bandana_round():
    """Head bandana (R units, head centre): snug band at the brow, knot and trailing tails at the back."""
    band = (torus(0.93, 0.1).scale3(1, 1.25, 1).at(0, 0.42, 0)) - sphere(0.9).at(0, 0, 0)
    knot = sphere(0.17).at(0, 0.38, 0.95)
    tails = round_cone((0.05, 0.36, 1.0), (0.22, 0.0, 1.3), 0.11, 0.07).scale3(1, 1, 1) | round_cone((-0.05, 0.36, 1.0), (-0.18, -0.06, 1.24), 0.11, 0.07)
    tails = tails.scale3(1, 1, 1)
    return band.su(knot, 0.06).su(tails.warp(lambda p: p * np.array([1, 1, 1])), 0.05)


@piece("mask_tribal", (0.9, 0.8, 1.2), tris=1600)
def mask_tribal():
    """Bone war mask (R units, head centre): curved plate following the face, eye holes, fangs."""
    shell = sphere(1.08) - sphere(0.98)
    front = half_space(2, 1, -0.55)
    shape = round_box(0.75, 0.6, 1.2, 0.3).at(0, 0.05, 0)
    s = (shell & front & shape)
    for x in (-0.36, 0.36):
        s = s.ss(ellipsoid(0.24, 0.2, 0.6).at(x, 0.12, -0.9), 0.04)
    s = s.ss(capsule((-0.22, -0.36, -0.95), (0.22, -0.36, -0.95), 0.05), 0.03)
    brow = capsule((-0.5, 0.36, -0.94), (0.5, 0.36, -0.94), 0.06).bend(0.4, axis=0, toward=2)
    return s.su(brow & SDF(lambda p: np.linalg.norm(p, axis=1) - 1.16), 0.04)


@piece("skull_jaw", (0.56, 0.24, 0.3), tris=800, fit=(1.0, 0.36, 0.5))
def skull_jaw():
    """Skeletal lower jaw with a row of blunt teeth."""
    s = round_box(0.48, 0.12, 0.24, 0.1).bend(0.5, axis=0, toward=2)
    teeth = union(*[round_box(0.045, 0.07, 0.05, 0.03).at(x, 0.13, -0.2 + 0.5 * x * x) for x in np.linspace(-0.36, 0.36, 7)])
    return s.su(teeth, 0.02)


@piece("mushroom_cap", (1.5, 1.3, 1.5), tris=2000)
def mushroom_cap():
    """Toadstool cap (R units, cap frame): wide domed cap, wavy rim, gills underneath."""
    return _cap_sdf()


def _cap_sdf():
    dome = ellipsoid(1.38, 0.62, 1.38).at(0, 0.12, 0) & half_space(1, -1, -0.02)
    top = sphere(1.02).at(0, 0.12, 0) & half_space(1, -1, 0.0)
    rim = torus(1.28, 0.1).at(0, 0.06, 0)
    s = dome.su(top, 0.25).su(rim, 0.1)
    s = s.ss(ellipsoid(1.1, 0.2, 1.1).at(0, -0.08, 0), 0.08)  # underside hollow
    for a in np.linspace(0, 2 * np.pi, 19)[:-1]:  # gills
        s = s.ss(box(0.55, 0.06, 0.015).rot(0, np.degrees(a), 0).at(0.75 * np.cos(a), 0.02, -0.75 * np.sin(a)), 0.01)
    return s


@piece("mushroom_spots", (1.5, 1.3, 1.5), tris=1200)
def mushroom_spots():
    """White spots that wrap the toadstool cap (proud of it by ~0.02R)."""
    cap = _cap_sdf()
    layer = SDF(lambda p: np.abs(cap(p) - 0.035) - 0.03)
    spots = []
    for (x, y, z, r) in ((-0.55, 0.65, -0.45, 0.28), (0.6, 0.62, 0.2, 0.3), (0.0, 0.78, 0.15, 0.22), (-0.3, 0.55, 0.75, 0.24), (0.85, 0.32, -0.6, 0.2), (-0.95, 0.3, 0.2, 0.2), (0.25, 0.55, -0.85, 0.2)):
        spots.append(sphere(r).at(x, y, z))
    return layer & union(*spots, k=0.02)


# ===================================================================== held items (box fill)
@piece("propeller", (0.98, 0.1, 0.18), tris=900, fit=(1.8, 0.1, 0.26))
def propeller():
    """Two-blade twisted propeller with a hub (spins about Y)."""
    blade = ellipsoid(0.46, 0.025, 0.12).at(0.45, 0, 0) | ellipsoid(0.46, 0.025, 0.12).at(-0.45, 0, 0)
    blade = blade.twist(0.7, axis=0)
    hub = cylinder(0.1, 0.05, axis=1, rr=0.02)
    return blade.su(hub, 0.04)


@piece("staff", (1.9, 0.14, 0.14), tris=1200, fit=(3.5, 0.2, 0.2))
def staff():
    """Gnarled wooden staff along X (+X = head end): twisting grain, knots, flared crook."""
    s = round_cone((-1.72, 0, 0), (1.62, 0, 0), 0.075, 0.09)
    knots = union(*[sphere(0.075).at(x, 0.04 * np.cos(i * 2.1), 0.04 * np.sin(i * 2.1)) for i, x in enumerate((-1.1, -0.3, 0.5, 1.15))])
    crook = round_cone((1.5, 0, 0), (1.74, 0, 0), 0.08, 0.1)
    s = s.su(knots, 0.06).su(crook, 0.05)
    for i in range(5):
        s = s.ss(capsule((-1.5, 0.0, 0.0), (1.4, 0.0, 0.0), 0.006).twist(2.2, axis=0).at(0, 0.075 * np.cos(i * 1.25), 0.075 * np.sin(i * 1.25)), 0.008)
    return s


@piece("club", (1.25, 0.3, 0.3), tris=1200, fit=(2.3, 0.5, 0.5))
def club():
    """Caveman club along X (+X = business end): thin grip swelling into a knobbly head."""
    s = round_cone((-1.1, 0, 0), (0.75, 0, 0), 0.1, 0.24)
    knobs = union(*[sphere(0.07).at(x, 0.22 * np.cos(a), 0.22 * np.sin(a)) for x, a in ((0.3, 0.3), (0.55, 2.0), (0.7, 4.1), (0.15, 3.3), (0.45, 5.4), (0.8, 1.1))])
    return s.su(knobs, 0.05).noise(0.008, 9, 11)


@piece("club_head", (0.75, 0.44, 0.44), tris=1100, fit=(1.35, 0.78, 0.78))
def club_head():
    """Knobbly club head along X."""
    s = round_cone((-0.55, 0, 0), (0.4, 0, 0), 0.26, 0.36)
    knobs = union(*[sphere(0.09).at(x, 0.33 * np.cos(a), 0.33 * np.sin(a)) for x, a in ((-0.2, 0.3), (0.05, 2.0), (0.3, 4.1), (-0.05, 3.3), (0.25, 5.4), (0.4, 1.1), (-0.3, 4.9))])
    return s.su(knobs, 0.06).noise(0.01, 7, 12)


@piece("sword_blade", (0.1, 1.2, 0.26), tris=700, fit=(0.14, 2.2, 0.44))
def sword_blade():
    """Broad blade along +Y: fuller groove, leaf swell, pointed tip, ricasso at the base."""
    def f(p):
        y = p[:, 1]
        t = np.clip((y + 1.1) / 2.2, 0, 1)
        half_w = 0.2 * (1 + 0.15 * np.sin(t * np.pi)) * np.clip((1.0 - t) / 0.18, 0, 1) ** 0.7
        half_t = 0.05 * (1 - 0.6 * t) + 0.012
        dx = np.abs(p[:, 0]) - half_t * np.clip(1 - np.abs(p[:, 2]) / np.maximum(half_w, 1e-3), 0.2, 1)
        dz = np.abs(p[:, 2]) - half_w
        dy = np.abs(y) - 1.1
        return np.maximum(np.maximum(dx, dz), dy) * 0.8

    s = SDF(f)
    s = s.ss(box(0.02, 0.7, 0.025).at(0.06, -0.3, 0) | box(0.02, 0.7, 0.025).at(-0.06, -0.3, 0), 0.01)
    return s


@piece("sword_guard", (0.18, 0.12, 0.55), tris=700, fit=(0.3, 0.18, 0.95))
def sword_guard():
    """Crossguard with curled quillons and a central langet."""
    bar = capsule((0, 0, -0.38), (0, 0, 0.38), 0.06)
    curls = sphere(0.09).at(0, 0.05, -0.44) | sphere(0.09).at(0, 0.05, 0.44)
    mid = round_box(0.12, 0.09, 0.12, 0.05)
    return bar.su(curls, 0.06).su(mid, 0.05)


@piece("shield_round", (0.2, 0.9, 0.9), tris=1500, fit=(0.22, 1.65, 1.65))
def shield_round():
    """Round wooden shield (axis X, +X = outer face): domed face, planks, iron rim."""
    face = (sphere(2.2).at(-1.98, 0, 0) & cylinder(0.78, 0.5, axis=0)) & half_space(0, -1, -0.12)
    back = cylinder(0.78, 0.06, axis=0, rr=0.02).at(-0.08, 0, 0)
    rim = torus(0.79, 0.07, axis=0).at(0.0, 0, 0)
    s = face.su(back, 0.05).su(rim, 0.03)
    for z in (-0.4, -0.13, 0.13, 0.4):
        s = s.ss(box(0.4, 0.75, 0.012).at(0.2, 0, z), 0.008)
    return s


@piece("tower_shield", (0.85, 1.2, 0.18), tris=1400, fit=(1.55, 2.25, 0.24))
def tower_shield():
    """Heater/tower shield (front -Z): rounded top, pointed base, convex face, raised rim."""
    def outline(p):
        x, y = p[:, 0], p[:, 1]
        top = np.sqrt(x ** 2 + np.maximum(y - 0.35, 0) ** 2 * 0.0) - 0.75
        body = np.maximum(np.abs(x) - 0.75, y - 1.1)
        tip = (np.abs(x) * 1.0 - (y + 1.1) * 0.62)
        d = np.maximum(body, np.where(y < -0.1, tip, body))
        return d

    plate = SDF(lambda p: np.maximum(outline(p), np.abs(p[:, 2] + 0.03 * (1 - (p[:, 0] / 0.8) ** 2)) - 0.05))
    plate = plate.round(0.03)
    rim = SDF(lambda p: np.maximum(np.abs(outline(p) + 0.07) - 0.05, np.abs(p[:, 2]) - 0.1)).round(0.02)
    boss = ellipsoid(0.18, 0.18, 0.06).at(0, 0.15, -0.08)
    return plate.su(rim, 0.03).su(boss, 0.05)


@piece("drill", (0.48, 0.48, 0.8), tris=1500, fit=(0.85, 0.85, 1.45))
def drill():
    """Spiral drill bit (spin axis Z, tip at -Z) on a ribbed collar."""
    bit = cone(0.03, 0.42, 0.52, axis=2).at(0, 0, -0.18)
    flutes = union(*[capsule((0.0, 0, -0.7), (0.0, 0, 0.3), 0.05).at(0.3 * np.cos(a), 0.3 * np.sin(a), 0) for a in np.linspace(0, 2 * np.pi, 4)[:-1]])
    bit = bit.ss(flutes.twist(5.0, axis=2), 0.03)
    collar = cylinder(0.46, 0.12, axis=2, rr=0.04).at(0, 0, 0.55)
    ring = torus(0.44, 0.04, axis=2).at(0, 0, 0.4)
    return bit.su(collar, 0.05).su(ring, 0.03)


@piece("cannon_barrel", (0.95, 0.3, 0.3), tris=1300, fit=(1.7, 0.5, 0.5))
def cannon_barrel():
    """Bronze cannon barrel along X (+X = muzzle): reinforce rings, flared muzzle, bore, cascabel."""
    tube_ = round_cone((-0.62, 0, 0), (0.78, 0, 0), 0.22, 0.17)
    rings = union(torus(0.22, 0.035, axis=0).at(-0.35, 0, 0), torus(0.2, 0.03, axis=0).at(0.15, 0, 0))
    muzzle = cylinder(0.24, 0.07, axis=0, rr=0.03).at(0.78, 0, 0)
    knob = sphere(0.08).at(-0.82, 0, 0).su(round_cone((-0.62, 0, 0), (-0.8, 0, 0), 0.2, 0.06), 0.04)
    s = tube_.su(rings, 0.02).su(muzzle, 0.04).su(knob, 0.04)
    return s.ss(cylinder(0.11, 0.3, axis=0).at(0.85, 0, 0), 0.02)


# ===================================================================== body add-ons
@piece("tentacle", (0.8, 0.2, 0.2), tris=1000, fit=(1.45, 0.3, 0.3))
def tentacle():
    """Tapered tentacle along X (root at -X), curling up at the tip, sucker row underneath."""
    s = tube([(-0.72, 0, 0), (-0.1, -0.01, 0), (0.42, 0.02, 0), (0.66, 0.08, 0)], [0.15, 0.115, 0.07, 0.03], k=0.04)
    for i, x in enumerate((-0.55, -0.35, -0.15, 0.05, 0.25, 0.42)):
        r = 0.04 - i * 0.004
        s = s.ss(sphere(r).at(x, -0.15 + i * 0.016, 0), 0.015)
    return s


@piece("tail_seg", (0.58, 0.25, 0.25), tris=800, fit=(1.05, 0.44, 0.44))
def tail_seg():
    """Tail segment along X (root at -X): tapered with a dorsal ridge."""
    s = round_cone((-0.5, 0, 0), (0.5, 0, 0), 0.2, 0.15)
    ridge = capsule((-0.42, 0.19, 0), (0.42, 0.15, 0), 0.025)
    return s.su(ridge, 0.04)


@piece("antenna", (0.68, 0.08, 0.08), tris=500, fit=(1.25, 0.13, 0.13))
def antenna():
    """Segmented antenna stalk along X (root at -X)."""
    s = round_cone((-0.6, 0, 0), (0.6, 0, 0), 0.055, 0.03)
    for x in (-0.3, 0.0, 0.3):
        s = s.su(sphere(0.05 - (x + 0.3) * 0.02).at(x, 0, 0), 0.02)
    return s


@piece("bat_wing", (0.12, 0.6, 0.6), tris=1300, fit=(0.12, 2.0, 1.3))
def bat_wing():
    """Membrane wing (wedge frame, root at y=-.5): finger bones, scalloped trailing edge."""
    plate = tri_mask(0.06).round(0.02) & box(0.03, 0.6, 0.6)
    for y, z, r in ((-0.25, 0.62, 0.22), (0.1, 0.62, 0.2), (0.38, 0.6, 0.12)):
        plate = plate.ss(sphere(r).at(0, y, z), 0.02)
    bones = union(*[capsule((0, -0.48, -0.45), (0, y, z), 0.04) for y, z in ((0.48, 0.47), (0.25, 0.48), (-0.05, 0.48))])
    arm = capsule((0, -0.48, -0.45), (0, 0.48, 0.42), 0.06)
    return plate.su(bones & box(0.2, 0.6, 0.6), 0.03).su(arm, 0.03)


@piece("insect_wing", (0.12, 0.6, 0.6), tris=900, fit=(0.12, 1.6, 0.9))
def insect_wing():
    """Teardrop insect wing (wedge frame) with raised veins."""
    blade = ellipsoid(0.025, 0.52, 0.3).rot(-36, 0, 0).at(0, 0.0, 0.08) & tri_mask(0.25).round(0.05)
    veins = union(*[capsule((0.02, -0.46, -0.3), (0.02, y, z), 0.014) for y, z in ((0.42, 0.42), (0.15, 0.4), (-0.15, 0.35))])
    return blade.su(veins & blade.round(0.01), 0.01)


@piece("shell_dome", (0.56, 0.56, 0.56), tris=1600, fit=(1, 1, 1))
def shell_dome():
    """Turtle/beetle shell (ball box): domed scutes separated by grooves, rim ridge."""
    s = sphere(0.48)
    for a in np.linspace(0, 2 * np.pi, 7)[:-1]:
        s = s.ss(torus(0.48, 0.016, axis=2).rot(0, np.degrees(a), 0), 0.02)
    s = s.ss(torus(0.33, 0.016).at(0, 0.35, 0), 0.02)
    return s


# ===================================================================== armour / cloth / packs (box fill)
@piece("chest_plate", (0.75, 0.6, 0.2), tris=1100, fit=(1.4, 0.94, 0.22))
def chest_plate():
    """Breastplate (front -Z): convex, centre ridge, rolled rim, two rivets."""
    def f(p):
        x, y = p[:, 0], p[:, 1]
        bulge = 0.09 * (1 - (x / 0.72) ** 2) * (1 - 0.4 * (y / 0.48) ** 2)
        return np.maximum(np.abs(p[:, 2] + bulge) - 0.03, np.maximum(np.abs(x) - 0.68, np.abs(y) - 0.45))

    plate = SDF(f).round(0.025)
    ridge = capsule((0, -0.4, -0.1), (0, 0.4, -0.1), 0.03)
    rivets = sphere(0.035).at(-0.52, 0.3, -0.06) | sphere(0.035).at(0.52, 0.3, -0.06)
    return plate.su(ridge, 0.04) | rivets


@piece("armor_plate", (0.6, 0.15, 0.4), tris=700, fit=(1.0, 0.2, 0.6))
def armor_plate():
    """Segment plate (top +Y): arched across X, rolled front edge."""
    def f(p):
        x = p[:, 0]
        arch = 0.07 * (1 - (x / 0.5) ** 2)
        return np.maximum(np.abs(p[:, 1] - arch) - 0.03, np.maximum(np.abs(x) - 0.48, np.abs(p[:, 2]) - 0.28))

    plate = SDF(f).round(0.02)
    roll = capsule((-0.46, 0.0, -0.28), (0.46, 0.0, -0.28), 0.04).bend(-0.3, axis=0, toward=1)
    return plate.su(roll, 0.03)


@piece("backpack", (0.56, 0.62, 0.38), tris=1200, fit=(1.0, 1.1, 0.62))
def backpack():
    """Rucksack (outer face +Z): puffy body, top flap, front pocket with a buckle."""
    body = round_box(0.46, 0.5, 0.24, 0.18)
    flap = round_box(0.47, 0.2, 0.27, 0.12).at(0, 0.38, 0.03)
    pocket = round_box(0.3, 0.2, 0.08, 0.07).at(0, -0.18, 0.25)
    buckle = round_box(0.06, 0.05, 0.03, 0.015).at(0, 0.18, 0.31)
    return body.su(flap, 0.06).su(pocket, 0.05) | buckle


@piece("bedroll", (0.62, 0.24, 0.24), tris=800, fit=(1.15, 0.42, 0.42))
def bedroll():
    """Rolled blanket (axis X) with a spiral end and two straps."""
    s = cylinder(0.2, 0.52, axis=0, rr=0.08)
    s = s.ss(torus(0.12, 0.01, axis=0).at(0.53, 0, 0), 0.01)
    straps = torus(0.205, 0.022, axis=0).at(-0.28, 0, 0) | torus(0.205, 0.022, axis=0).at(0.28, 0, 0)
    return s | straps


@piece("jet_tank", (0.62, 0.28, 0.28), tris=800, fit=(1.15, 0.48, 0.48))
def jet_tank():
    """Rocket tank (axis X): capsule body, two bands, nozzle at -X."""
    s = capsule((-0.3, 0, 0), (0.33, 0, 0), 0.22)
    bands = torus(0.22, 0.025, axis=0).at(-0.1, 0, 0) | torus(0.22, 0.025, axis=0).at(0.2, 0, 0)
    nozzle = cone(0.16, 0.1, 0.07, axis=0).at(-0.5, 0, 0)
    return s.su(bands, 0.02).su(nozzle, 0.03)


@piece("cape", (0.6, 0.6, 0.15), tris=1300, fit=(1.0, 1.0, 0.16))
def cape():
    """Draped cape: folds deepening toward the hem, slight flare, scalloped hem."""
    def f(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        t = np.clip((0.5 - y), 0, 1)  # 0 at the top, 1 at the hem
        wave = 0.06 * t * np.sin(x * 14.0)
        halfw = 0.42 + 0.08 * t
        return np.maximum(np.abs(z - wave) - 0.022, np.maximum(np.abs(x) - halfw, np.abs(y) - 0.5))

    s = SDF(f).round(0.01)
    for x in np.linspace(-0.42, 0.42, 5):
        s = s.ss(sphere(0.08).at(x, -0.56, 0), 0.03)
    return s


@piece("banner_flag", (0.15, 0.45, 0.58), tris=1000, fit=(0.24, 0.8, 1.05))
def banner_flag():
    """Waving flag (thin X, flies toward +Z) with a swallowtail."""
    def f(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        t = np.clip((z + 0.5), 0, 1)
        wave = 0.07 * t * np.sin(z * 9.0 + y * 2.0)
        cut = np.maximum(0.0, (z - 0.25)) * 2.2 - np.abs(y) * 1.0  # swallowtail notch
        return np.maximum(np.maximum(np.abs(x - wave) - 0.018, np.maximum(np.abs(y) - 0.4, np.abs(z) - 0.5)), -(-cut))

    return SDF(lambda p: f(p)).round(0.01)


@piece("band_ring", (0.3, 0.6, 0.6), tris=900, fit=(0.42, 1.0, 1.0))
def band_ring():
    """Hollow band (axis X) with rolled edges: stripes, shell bands, horn rings (no flat end caps)."""
    outer = cylinder(0.5, 0.2, axis=0, rr=0.08)
    return outer - cylinder(0.42, 0.4, axis=0)


@piece("wind_key", (0.6, 0.26, 0.1), tris=900, fit=(1.05, 0.42, 0.12))
def wind_key():
    """Wind-up key bow: two rounded loops either side of a hub (flat in Z)."""
    loops = (torus(0.17, 0.045, axis=2).scale3(1.25, 1, 1).at(-0.3, 0, 0)) | (torus(0.17, 0.045, axis=2).scale3(1.25, 1, 1).at(0.3, 0, 0))
    hub = cylinder(0.08, 0.045, axis=2, rr=0.02)
    bar = capsule((-0.12, 0, 0), (0.12, 0, 0), 0.05)
    return loops.su(bar, 0.04).su(hub, 0.03)
