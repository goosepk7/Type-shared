"""Spacecraft (flying mounts): rocket, space shuttle (orbiter on its tank and boosters), spaceship, starfighter, ufo
(flying saucer), space capsule, moon lander.

Hard-surface direct meshes (airsea_kit): revolved bodies, lofted hulls, airfoil wings and fins, separate glass,
small thruster glows (lights only, never glowing bodies). Gait "fly" (bank, pitch) or "hover" (saucer, capsule,
lander). Model space: -Z is the nose, landing gear / legs / fins on y = 0.
"""
import math

import numpy as np

from kit import Hero, hero
import airsea_kit as A
from airsea_kit import Fus, dpiece, dmpiece, box, cyl, rev, tube, merge, xform, mirror, sphere, wheel, window_row

TAU = 2 * math.pi
TINT = [0.13, 0.17, 0.22]
CANOPY = [0.55, 0.75, 0.88]
B = {"cat": ["Vehicle", "Machine", "Object"]}


def S(hid, gait="fly"):
    return Hero(hid, plan="Vehicle", gait=gait, tags=["vehicle", "spacecraft"])


def common(H, seat_pos, seat_size, nose, tail, top_y, muzzle=None):
    A.mount(H, "Seat", seat_pos, seat_size)
    H.socket("head", (0, top_y, seat_pos[2]), "Body")
    H.socket("mouth", nose, "Body")
    H.socket("exhaust", tail, "Body")
    if muzzle is not None:
        H.socket("muzzle", muzzle, "Body")


def bucket_seat(pos, w=0.8, rake=-14):
    x, y, z = pos
    return merge(box((w, 0.22, 0.8), (x, y, z), r=0.08), box((w, 0.9, 0.18), (x, y + 0.45, z + 0.42), r=0.08, rot=(rake, 0, 0)))


def canopy(z0, z1, r, y, sx=1.0, sy=1.0):
    L = z1 - z0
    m = rev([(z0, 0), (z0 + L * 0.12, r * 0.55), (z0 + L * 0.4, r), (z0 + L * 0.75, r * 0.85), (z1, 0)], axis=2, segs=16)
    return xform(m, (0, y, 0), (0, 0, 0), (sx, sy, 1))


def bell(pos, r, L, axis_dir=1):
    """Rocket engine bell along +Z (axis_dir) from pos."""
    x, y, z = pos
    d = axis_dir
    return A.lathe([(z, r * 0.35), (z + d * L * 0.2, r * 0.4), (z + d * L, r), (z + d * L, r * 0.88), (z + d * L * 0.25, r * 0.3)], axis=2, segs=16, pos=(x, y, 0), closed=True)


def thrust_clips(H, size, spinners=(), extra=None, hover=False, attack="dive", bank=0.35):
    A.air_clips(H, size=size, spinners=spinners, extra=extra, attack=attack, hover=hover, bank=bank)


# ================================================================================================ rocket
@hero("rocket", "spacecraft")
def rocket():
    H = S("rocket")
    H.preview = {"primary": "#F5F5F5", "secondary": "#E53935"}
    R, yc = 1.5, 2.3
    H.body((0, yc, 0))
    body = rev([(-7.0, 0.0), (-6.4, 0.55), (-5.0, 1.15), (-3.0, R), (3.5, R), (4.6, 1.3), (5.2, 0.0)], axis=2, segs=24, pos=(0, yc, 0), spline=4)
    dpiece(H, "Hull", "Body", body, col="primary", mat="metal", fallback="Ellipsoid")
    nose = rev([(-7.05, 0.0), (-6.4, 0.57), (-5.3, 1.08), (-5.25, 0.0)], axis=2, segs=24, pos=(0, yc, 0), spline=3)
    bands = merge(*[A.lathe([(z - 0.18, R + 0.03), (z + 0.18, R + 0.03), (z + 0.18, R - 0.1), (z - 0.18, R - 0.1)], axis=2, segs=24, pos=(0, yc, 0), closed=True) for z in (-2.2, 2.6)])
    dpiece(H, "Nose", "Body", merge(nose, bands), col="secondary", mat="metal", role="detail")
    # portholes along the side
    ports = []
    for z in (-3.6, -1.4, 0.8):
        ports.append(A.lathe([(-0.06, 0.0), (-0.06, 0.38), (0.06, 0.38), (0.06, 0.0)], axis=0, segs=16, pos=(R - 0.02, yc + 0.35, z)))
    pm = merge(*ports)
    dpiece(H, "Ports", "Body", merge(pm, mirror(pm)), col=CANOPY, mat="glass", role="glass", pri=1.5)
    rims = merge(*[A.lathe([(-0.07, 0.38), (0.08, 0.42), (0.08, 0.32), (-0.07, 0.32)], axis=0, segs=16, pos=(R - 0.02, yc + 0.35, z), closed=True) for z in (-3.6, -1.4, 0.8)])
    dpiece(H, "PortRims", "Body", merge(rims, mirror(rims)), col="metal", mat="metal", role="detail", pri=2)
    # open cockpit on top with a windscreen; the rider's seat
    dpiece(H, "Cockpit", "Body", A.lathe([(yc + R - 0.4, 0.0), (yc + R - 0.4, 0.75), (yc + R + 0.12, 0.75), (yc + R + 0.12, 0.62), (yc + R - 0.25, 0.62), (yc + R - 0.25, 0.0)],
                                         axis=1, segs=18, pos=(0, 0, -0.6), scale=(1, 1, 1.3)), col="secondary", mat="metal", role="detail")
    dpiece(H, "Windshield", "Body", A.quad_sheet((-0.6, yc + R + 0.1, -1.55), (0.6, yc + R + 0.1, -1.55), (-0.5, yc + R + 0.7, -1.25), (0.5, yc + R + 0.7, -1.25), nt=5, nu=3, bulge=(0, 0, -0.15), thick=0.03),
           col=CANOPY, mat="glass", tr=0.4, role="glass", pri=1.5)
    dpiece(H, "Seat", "Body", bucket_seat((0, yc + R - 0.2, -0.5), w=0.75), col="dark", mat="cloth", role="detail")
    # four swept fins reaching the ground, engine bell + flame
    fins = []
    for a in (45, 135, 225, 315):
        f = A.fin(2.3, 3.0, 1.2, 1.8, thick=0.22, pos=(0, R - 0.3, 2.0))
        fins.append(xform(f, (0, yc, 0), (0, 0, a)))
    dpiece(H, "Fins", "Body", merge(*fins), col="secondary", mat="metal", role="detail")
    dpiece(H, "Engine", "Body", merge(bell((0, yc, 4.9), 1.0, 1.4), cyl(0.7, 0.4, (0, yc, 5.0), axis=2, segs=16)), col="gunmetal", mat="metal", role="detail")
    H.prim("Flame", "Body", "Ball", (1.1, 1.1, 1.6), (0, yc, 6.7), col="flame", glow=True, role="light", pri=2.3)
    H.prim("FlameCore", "Body", "Ball", (0.6, 0.6, 1.0), (0, yc, 6.4), col="flameCore", glow=True, role="light", pri=2.4)
    common(H, (0, yc + R, -0.5), (0.8, 0.15, 0.8), (0, yc, -7.2), (0, yc, 6.8), yc + R + 1.6)
    thrust_clips(H, 1.4, attack="roll", bank=0.4)
    return H


# ================================================================================================ space shuttle
@hero("space shuttle", "spacecraft")
def space_shuttle():
    H = S("space shuttle")
    H.preview = {"primary": "#F5F5F5", "secondary": "#1A1A1A"}
    yc = 4.6
    H.body((0, yc, 0))
    fus = Fus([(-8.0, 0.0, 0.0, yc - 0.3), (-7.6, 0.6, 0.55, yc - 0.25), (-6.6, 1.15, 1.05, yc - 0.05), (-5.0, 1.35, 1.3, yc + 0.1), (4.0, 1.35, 1.2, yc), (6.2, 1.3, 1.1, yc + 0.05)], n=22, p=2.8)
    dpiece(H, "Hull", "Body", fus.mesh(), col="primary", mat="hard", fallback="Ellipsoid", pattern=lambda Q: np.where(Q[:, 1] < yc - 0.55, 0.18, 1.0))
    dpiece(H, "NoseCap", "Body", Fus([(-8.03, 0.0, 0.0, yc - 0.3), (-7.6, 0.62, 0.57, yc - 0.25), (-7.1, 0.92, 0.84, yc - 0.15)], n=22, p=2.8).mesh(), col="secondary", role="detail")
    ck = []
    for s in (1, -1):
        for k in range(3):
            ck.append(box((0.5, 0.34, 0.4), (s * (0.35 + 0.45 * k) * 0.95, yc + 1.1 - 0.12 * k, -6.2 + 0.2 * k), r=0.04, rot=(-35, s * (10 + 22 * k), 0)))
    dpiece(H, "CockpitGlass", "Body", merge(*ck), col="secondary", mat="glass", role="glass", pri=1.5)
    # double delta wing with black leading edges, fin, OMS pods, engines
    w = A.wing(5.6, 9.0, 1.4, sweep=7.0, thick=0.5, dihedral=2, pos=(1.0, yc - 0.85, -3.6))
    strake = A.wing(1.6, 4.0, 0.5, sweep=3.0, thick=0.3, pos=(1.0, yc - 0.8, -6.0))
    dpiece(H, "Wings", "Body", merge(w, mirror(w), strake, mirror(strake)), col="primary", role="wing", pattern=lambda Q: np.where(Q[:, 1] < yc - 0.85, 0.18, 1.0))
    dpiece(H, "Fin", "Body", A.fin(4.0, 3.6, 1.6, 2.6, thick=0.3, pos=(0, yc + 1.0, 2.6)), col="primary", role="detail")
    oms = Fus([(2.5, 0.0, 0.0, yc + 0.9), (3.4, 0.45, 0.4, yc + 0.95), (6.2, 0.5, 0.45, yc + 0.95)], n=14)
    om = xform(oms.mesh(), (0.75, 0, 0))
    dpiece(H, "OMS", "Body", merge(om, mirror(om)), col="primary", role="detail")
    eng = merge(bell((0, yc + 0.5, 6.2), 0.55, 1.1), bell((0.65, yc - 0.35, 6.2), 0.55, 1.1), bell((-0.65, yc - 0.35, 6.2), 0.55, 1.1))
    dpiece(H, "Engines", "Body", eng, col="gunmetal", mat="metal", role="detail")
    dpiece(H, "BayDoors", "Body", merge(box((0.06, 0.08, 8.0), (0, fus.y_top(0) + 0.0, 0.0)), box((1.6, 0.06, 0.06), (0, fus.y_top(-3.8) + 0.0, -3.8))), col=[0.5, 0.5, 0.5], role="detail", pri=2.4)
    # external tank + solid boosters underneath (they carry the stack on the ground)
    tank = rev([(-9.0, 0.0), (-8.0, 0.9), (-6.0, 1.6), (-4.0, 1.75), (6.5, 1.75), (6.7, 0.0)], axis=2, segs=22, pos=(0, yc - 3.0, 0), spline=3)
    dpiece(H, "Tank", "Body", tank, col=[0.85, 0.45, 0.2], mat="foil", role="body")
    srb = []
    for s in (1, -1):
        srb.append(rev([(-8.5, 0.0), (-7.8, 0.45), (-7.0, 0.62), (5.6, 0.62), (6.4, 0.75), (6.8, 0.0)], axis=2, segs=18, pos=(s * 2.3, yc - 3.1, 0), spline=3))
        srb.append(bell((s * 2.3, yc - 3.1, 6.6), 0.62, 0.6))
    dpiece(H, "Boosters", "Body", merge(*srb), col="white", role="detail")
    dpiece(H, "Struts", "Body", merge(tube([[0, yc - 1.25, -5.0], [0, yc - 1.4, -5.0]], 0.25, 6), tube([[0.8, yc - 1.2, 3.5], [0.6, yc - 1.4, 3.6]], 0.15, 6), tube([[-0.8, yc - 1.2, 3.5], [-0.6, yc - 1.4, 3.6]], 0.15, 6),
                                      tube([[1.75, yc - 3.05, -2.0], [1.68, yc - 3.05, -2.0]], 0.2, 6), tube([[-1.75, yc - 3.05, -2.0], [-1.68, yc - 3.05, -2.0]], 0.2, 6)), col="metal", mat="metal", role="detail", pri=2.4)
    for i, (x, y, r) in enumerate(((2.3, yc - 3.1, 0.75), (-2.3, yc - 3.1, 0.75), (0.0, yc + 0.5, 0.5))):
        H.prim(f"Flame{i}", "Body", "Ball", (r * 1.6, r * 1.6, r * 3.0), (x, y, 8.0 if i < 2 else 7.8), col="flame", glow=True, role="light", pri=2.3)
    # rider: open hatch seat on the crown behind the cockpit
    sz = -4.4
    ty = fus.y_top(sz)
    dpiece(H, "Seat", "Body", merge(A.lathe([(ty - 0.15, 0.0), (ty - 0.15, 0.6), (ty + 0.1, 0.6), (ty + 0.1, 0.0)], axis=1, segs=16, pos=(0, 0, sz)), bucket_seat((0, ty + 0.2, sz), w=0.7)),
           col="secondary", mat="cloth", role="detail")
    common(H, (0, ty + 0.4, sz), (0.7, 0.15, 0.8), (0, yc - 0.3, -8.2), (0, yc, 8.0), ty + 1.6)
    thrust_clips(H, 1.6, attack="dive", bank=0.3)
    return H


# ================================================================================================ spaceship
@hero("spaceship", "spacecraft")
def spaceship():
    H = S("spaceship")
    H.preview = {"primary": "#ECEFF1", "secondary": "#2979FF"}
    yc = 1.9
    H.body((0, yc, 0))
    fus = Fus([(-7.0, 0.0, 0.0, yc - 0.1), (-6.4, 0.45, 0.25, yc - 0.08), (-4.5, 1.1, 0.55, yc), (-1.5, 1.6, 0.8, yc + 0.1), (2.5, 1.9, 0.85, yc + 0.1), (4.5, 1.7, 0.7, yc + 0.05), (5.2, 1.5, 0.6, yc)], n=22, p=2.6)
    dpiece(H, "Hull", "Body", fus.mesh(), col="primary", mat="metal", fallback="Ellipsoid")
    dpiece(H, "Stripe", "Body", merge(box((0.5, 0.08, 9.0), (0, fus.y_top(0.0) + 0.0, 0.3), r=0.03), A.fin(0.6, 1.2, 0.6, 0.5, thick=0.12, pos=(0, fus.y_top(3.0) - 0.05, 3.0))), col="secondary", role="detail")
    dpiece(H, "Canopy", "Body", canopy(-5.2, -1.6, 0.7, yc + 0.45, sx=0.95, sy=0.8), col=[0.25, 0.55, 0.85], mat="glass", tr=0.35, role="glass", pri=1.3)
    dpiece(H, "Seat", "Body", bucket_seat((0, yc + 0.2, -3.3), w=0.7, rake=-20), col="dark", role="detail")
    # swept wings with drooping tips, twin fins, engine block with three thrusters
    w = A.wing(4.6, 4.8, 1.2, sweep=3.8, thick=0.3, dihedral=-4, pos=(1.4, yc - 0.2, -1.0))
    tip = A.fin(1.2, 1.3, 0.7, 0.5, thick=0.14, pos=(6.0, yc - 0.55, 2.8), rot=(0, 0, 160))
    dpiece(H, "Wings", "Body", merge(w, mirror(w)), col="primary", role="wing")
    dpiece(H, "WingTips", "Body", merge(tip, mirror(tip), *[box((0.08, 0.06, 3.8), (s * (2.0 + 2.2), yc - 0.25 - 2.2 * math.tan(math.radians(4)) + 0.03, 1.4 + 0.9), r=0.02) for s in (1, -1)]), col="secondary", role="detail")
    f = A.fin(2.0, 2.0, 0.8, 1.6, thick=0.16, pos=(1.2, yc + 0.5, 2.6), rot=(0, 0, -15))
    dpiece(H, "Fins", "Body", merge(f, mirror(f)), col="primary", role="detail")
    eng = []
    for x, y in ((1.0, yc), (-1.0, yc), (0.0, yc + 0.45)):
        eng.append(A.lathe([(4.6, 0.55), (6.0, 0.5), (6.0, 0.4), (4.8, 0.38)], axis=2, segs=16, pos=(x, y, 0), closed=True))
        eng.append(A.lathe([(5.6, 0.0), (5.6, 0.42), (5.7, 0.42), (5.7, 0.0)], axis=2, segs=16, pos=(x, y, 0)))
    dpiece(H, "Thrusters", "Body", merge(*eng), col="gunmetal", mat="metal", role="detail")
    for i, (x, y) in enumerate(((1.0, yc), (-1.0, yc), (0.0, yc + 0.45))):
        H.prim(f"Glow{i}", "Body", "Cylinder", (0.06, 0.78, 0.78), (x, y, 5.78), rot=(0, math.pi / 2, 0), col="secondary", glow=True, role="light", pri=2.3)
    # nose cannons + landing skids
    gn = merge(*[tube([[s * 1.2, yc - 0.25, -3.0], [s * 1.2, yc - 0.25, -5.6]], 0.1, 8) for s in (1, -1)], *[box((0.3, 0.3, 1.2), (s * 1.2, yc - 0.25, -2.6), r=0.06) for s in (1, -1)])
    dpiece(H, "Guns", "Body", gn, col="gunmetal", mat="metal", role="detail")
    legs = []
    for x, z in ((1.4, 1.8), (-1.4, 1.8), (0.0, -4.0)):
        legs += [tube([[x, yc - 0.6, z], [x * 1.1, 0.25, z]], 0.1, 6), cyl(0.35, 0.16, (x * 1.1, 0.08, z), axis=1, segs=12)]
    dpiece(H, "Legs", "Body", merge(*legs), col="metal", mat="metal", role="detail")
    common(H, (0, yc + 0.4, -3.3), (0.7, 0.15, 0.8), (0, yc, -7.2), (0, yc, 6.3), yc + 1.8, muzzle=(1.2, yc - 0.25, -5.7))
    thrust_clips(H, 1.4, attack="dive", bank=0.5)
    return H


# ================================================================================================ starfighter
@hero("starfighter", "spacecraft")
def starfighter():
    H = S("starfighter")
    H.preview = {"primary": "#ECEFF1", "secondary": "#E53935"}
    yc = 2.4
    H.body((0, yc, 0))
    fus = Fus([(-7.0, 0.0, 0.0, yc - 0.1), (-6.6, 0.25, 0.22, yc - 0.1), (-3.5, 0.5, 0.42, yc - 0.02), (-1.2, 0.68, 0.6, yc + 0.05), (1.5, 0.9, 0.75, yc + 0.05), (3.8, 0.9, 0.75, yc + 0.05), (4.2, 0.7, 0.6, yc)], n=20, p=3.0)
    dpiece(H, "Hull", "Body", fus.mesh(), col="primary", mat="metal", fallback="Ellipsoid")
    dpiece(H, "NoseStripe", "Body", merge(*[box((0.06, 0.12, 3.0), (s * (fus.x_at(-4.5, yc) - 0.0), yc, -4.5), r=0.02) for s in (1, -1)]), col="secondary", role="detail")
    dpiece(H, "Canopy", "Body", canopy(-2.6, 0.6, 0.6, yc + 0.5, sx=0.9, sy=0.9), col=TINT, mat="glass", tr=0.3, role="glass", pri=1.3)
    dpiece(H, "Seat", "Body", bucket_seat((0, yc + 0.25, -0.9), w=0.6, rake=-18), col="dark", role="detail")
    # four wings in an X on two bones per side (the foils open for the attack)
    eng, cannons = [], []
    for nm, sy_ in (("U", 1), ("D", -1)):
        H.mbone(f"Foil{nm}#", "Body", (0.6, yc + 0.15 * sy_, 2.3))
        w = A.wing(4.2, 2.6, 1.2, sweep=1.2, thick=0.18, pos=(0.6, yc + 0.15 * sy_, 1.2))
        w = xform(A.direct.moved(w, (-0.6, -(yc + 0.15 * sy_), -2.3)), (0.6, yc + 0.15 * sy_, 2.3), (0, 0, 12 * sy_))
        stripe = xform(A.direct.moved(box((2.0, 0.1, 0.35), (2.4, yc + 0.15 * sy_ + 0.02 * sy_, 1.9), r=0.02), (-0.6, -(yc + 0.15 * sy_), -2.3)), (0.6, yc + 0.15 * sy_, 2.3), (0, 0, 12 * sy_))
        tipx, tipy = 0.6 + 4.2 * math.cos(math.radians(12)), yc + 0.15 * sy_ + 4.2 * math.sin(math.radians(12)) * sy_
        can = merge(tube([[tipx, tipy, 1.4], [tipx, tipy, -3.4]], 0.07, 6), cyl(0.14, 1.4, (tipx, tipy, 1.6), axis=2, segs=8), cyl(0.12, 0.3, (tipx, tipy, -3.3), axis=2, segs=8))
        en = merge(rev([(-1.0, 0.0), (-0.9, 0.42), (2.2, 0.45), (2.5, 0.3), (2.55, 0.0)], axis=2, segs=14, pos=(1.25, yc + 0.55 * sy_, 1.0)))
        dmpiece(H, f"Wing{nm}#", f"Foil{nm}#", merge(w, en), col="primary", role="wing")
        dmpiece(H, f"WingDeco{nm}#", f"Foil{nm}#", merge(stripe, can), col="secondary" if nm == "U" else "gunmetal", mat="metal", role="detail")
        H.mprim(f"Glow{nm}#", f"Foil{nm}#", "Cylinder", (0.06, 0.7, 0.7), (1.25, yc + 0.55 * sy_, 3.56), rot=(0, math.pi / 2, 0), col="secondary", glow=True, role="light", pri=2.3)
    dpiece(H, "Rear", "Body", merge(box((2.2, 1.4, 1.2), (0, yc, 3.4), r=0.15), cyl(0.38, 0.5, (0, yc + 0.85, 1.4), axis=1, segs=12), sphere(0.4, (0, yc + 1.1, 1.4), scale=(1, 0.7, 1))),
           col="primary", mat="metal", role="detail")
    dpiece(H, "Dome", "Body", sphere(0.36, (0, yc + 1.12, 1.4), scale=(1, 0.75, 1)), col="secondary", mat="metal", role="detail", pri=1.8)
    legs = merge(*[tube([[x, yc - 0.5, z], [x, 0.15, z]], 0.08, 6) for x, z in ((0.5, 2.8), (-0.5, 2.8), (0.0, -4.0))], *[cyl(0.25, 0.15, (x, 0.08, z), axis=1, segs=10) for x, z in ((0.5, 2.8), (-0.5, 2.8), (0.0, -4.0))])
    dpiece(H, "Legs", "Body", legs, col="metal", mat="metal", role="detail")
    common(H, (0, yc + 0.45, -0.9), (0.6, 0.15, 0.8), (0, yc, -7.2), (0, yc, 4.4), yc + 1.6, muzzle=(4.7, yc + 1.0, -3.5))

    def extra(name, u, pose):
        if name == "Attack":
            k = A.pulse(u, 0.0, 1.0) * 1.0
            for nm, sgn in (("UR", 1), ("UL", -1), ("DR", -1), ("DL", 1)):
                A._add(pose, f"Foil{nm}", (0, 0, 0, 0, 0, 0.22 * k * sgn))
        elif name == "Move":
            for nm, sgn in (("UR", 1), ("UL", -1), ("DR", -1), ("DL", 1)):
                A._add(pose, f"Foil{nm}", (0, 0, 0, 0, 0, 0.12 * sgn))

    thrust_clips(H, 1.3, extra=extra, attack="roll", bank=0.55)
    return H


# ================================================================================================ ufo
@hero("ufo", "spacecraft")
def ufo():
    H = S("ufo", gait="hover")
    H.preview = {"primary": "#B0BEC5", "secondary": "#76FF03"}
    yc = 2.2
    H.body((0, yc, 0))
    disc = A.lathe([(yc - 0.9, 0.0), (yc - 0.9, 1.4), (yc - 0.75, 2.3), (yc - 0.45, 3.6), (yc - 0.12, 4.6), (yc, 4.75), (yc + 0.12, 4.6), (yc + 0.45, 3.4), (yc + 0.65, 2.2), (yc + 0.72, 0.0)], axis=1, segs=32)
    dpiece(H, "Hull", "Body", disc, col="primary", mat="metal", fallback="Ellipsoid", pattern=lambda Q: np.where(np.abs(Q[:, 1] - yc) < 0.05, 0.6, 1.0))
    # spinning ring of small lights around the rim (own bone)
    H.bone("Ring", "Body", (0, yc, 0))
    ring = A.lathe([(yc - 0.16, 4.62), (yc + 0.16, 4.62), (yc + 0.16, 4.45), (yc - 0.16, 4.45)], axis=1, segs=32, closed=True)
    dpiece(H, "RingP", "Ring", ring, col="gunmetal", mat="metal", role="detail")
    lights = merge(*[sphere(0.16, (4.75 * math.cos(a), yc, 4.75 * math.sin(a)), segs=8) for a in np.linspace(0, TAU, 12, endpoint=False)])
    dpiece(H, "Lights", "Ring", lights, col="secondary", mat="hard", role="light", glow=True, pri=2.2)
    # glass dome over the pilot seat + a little alien-free cockpit console
    dome = rev([(-2.0, 0.0), (-1.85, 0.8), (-1.1, 1.75), (-0.2, 2.05), (0.0, 2.08)], axis=1, segs=24, pos=(0, yc + 2.6, 0))
    dome = xform(rev([(0.0, 2.05), (0.8, 1.85), (1.5, 1.2), (1.85, 0.4), (1.9, 0.0)], axis=1, segs=24), (0, yc + 0.6, 0))
    dpiece(H, "Dome", "Body", dome, col=[0.6, 0.85, 0.75], mat="glass", tr=0.5, role="glass", pri=1.2)
    dpiece(H, "DomeRim", "Body", A.lathe([(yc + 0.55, 2.2), (yc + 0.75, 2.2), (yc + 0.75, 1.95), (yc + 0.55, 1.95)], axis=1, segs=28, closed=True), col="secondary", mat="metal", role="detail")
    dpiece(H, "Seat", "Body", merge(bucket_seat((0, yc + 0.85, 0.2), w=0.8), box((1.2, 0.5, 0.4), (0, yc + 0.95, -1.1), r=0.12)), col="dark", mat="hard", role="detail")
    # underside: beam emitter + three landing legs
    dpiece(H, "Emitter", "Body", merge(A.lathe([(yc - 1.15, 0.0), (yc - 1.15, 0.9), (yc - 0.85, 1.25), (yc - 0.85, 0.0)], axis=1, segs=20),
                                       A.lathe([(yc - 0.5, 3.0), (yc - 0.38, 3.0), (yc - 0.38, 2.86), (yc - 0.5, 2.86)], axis=1, segs=32, closed=True)), col="gunmetal", mat="metal", role="detail")
    H.prim("Beam", "Body", "Cylinder", (0.12, 1.5, 1.5), (0, yc - 1.2, 0), rot=(0, 0, math.pi / 2), col="secondary", glow=True, role="light", pri=2.2)
    legs = []
    for a in (90, 210, 330):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        legs += [tube([[1.6 * c, yc - 0.85, 1.6 * s], [2.6 * c, 0.2, 2.6 * s]], 0.11, 6), cyl(0.38, 0.14, (2.6 * c, 0.07, 2.6 * s), axis=1, segs=12)]
    dpiece(H, "Legs", "Body", merge(*legs), col="metal", mat="metal", role="detail")
    common(H, (0, yc + 1.05, 0.2), (0.8, 0.15, 0.8), (0, yc, -4.9), (0, yc - 1.2, 0), yc + 2.9, muzzle=(0, yc - 1.3, 0))
    spins = [("Ring", "y", 1, TAU / 12)]

    def extra(name, u, pose):
        if name == "Move":
            A._add(pose, "Body", (0, 0, 0, -0.08, 0, 0))

    thrust_clips(H, 1.2, spinners=spins, extra=extra, hover=True, attack="ram", bank=0.2)
    return H


# ================================================================================================ space capsule
@hero("space capsule", "spacecraft")
def space_capsule():
    H = S("space capsule", gait="hover")
    H.preview = {"primary": "#ECEFF1", "secondary": "#1A1A1A"}
    H.body((0, 2.0, 0))
    # cone capsule standing on its heat shield
    cap = A.lathe([(0.35, 0.0), (0.35, 2.15), (0.55, 2.3), (0.75, 2.25), (3.3, 0.85), (3.45, 0.8), (3.6, 0.6), (3.6, 0.0)], axis=1, segs=28)
    dpiece(H, "Hull", "Body", cap, col="primary", mat="foil", fallback="Ellipsoid", pattern=lambda Q: 0.9 + 0.1 * np.cos(np.arctan2(Q[:, 2], Q[:, 0]) * 14))
    dpiece(H, "Shield", "Body", A.lathe([(0.0, 0.0), (0.0, 1.6), (0.12, 2.2), (0.35, 2.3), (0.45, 2.25), (0.45, 0.0)], axis=1, segs=28), col=[0.42, 0.3, 0.2], mat="hard", role="detail")
    # windows, hatch, RCS quads, docking nose
    win = []
    for a in (-35, 35):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        r_ = 2.1 - (1.8 - 0.35) * (2.25 - 0.85) / (3.3 - 0.75) * 0 - 0.62
        win.append(xform(box((0.5, 0.45, 0.08), (0, 0, 0), r=0.06), (s * 1.63, 1.9, -c * 1.63), (29, -a, 0)))
    dpiece(H, "Windows", "Body", merge(*win), col=TINT, mat="glass", role="glass", pri=1.5)
    dpiece(H, "Hatch", "Body", xform(box((0.9, 1.0, 0.1), (0, 0, 0), r=0.08), (0, 1.75, -1.74), (29, 0, 0)), col="secondary", role="detail")
    rcs = []
    for a in (45, 135, 225, 315):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        rcs.append(xform(box((0.35, 0.3, 0.2), (0, 0, 0), r=0.04), (c * 1.2, 2.75, s * 1.2), (0, -a + 90, 0)))
    dpiece(H, "RCS", "Body", merge(*rcs, A.lathe([(3.55, 0.0), (3.55, 0.45), (3.95, 0.35), (3.95, 0.0)], axis=1, segs=16)), col="gunmetal", mat="metal", role="detail")
    # parachute (packed open canopy above on a bone) with shroud lines
    H.bone("Chute", "Body", (0, 4.0, 0))
    ch = A.lathe([(8.2, 0.0), (8.15, 0.9), (7.8, 2.0), (7.1, 3.0), (6.4, 3.4), (6.55, 3.4), (7.25, 3.0), (7.95, 2.0), (8.3, 0.9), (8.35, 0.0)], axis=1, segs=20)
    lines = merge(*[tube([[0, 4.0, 0], [3.3 * math.cos(a), 6.45, 3.3 * math.sin(a)]], 0.025, 3) for a in np.linspace(0, TAU, 8, endpoint=False)])
    dpiece(H, "Canopy", "Chute", ch, col=[0.95, 0.45, 0.15], mat="cloth", role="wing", pattern=lambda Q: np.where(np.cos(np.arctan2(Q[:, 2], Q[:, 0]) * 4) > 0, 1.0, 0.55))
    dpiece(H, "Lines", "Chute", lines, col="white", mat="cloth", role="detail", pri=2.5)
    # the rider sits in an open seat on the docking deck
    dpiece(H, "Seat", "Body", merge(bucket_seat((0, 4.05, 0.1), w=0.75)), col="secondary", mat="cloth", role="detail")
    common(H, (0, 4.25, 0.1), (0.8, 0.15, 0.8), (0, 2.0, -2.0), (0, 0.0, 0), 5.5)

    def extra(name, u, pose):
        A._add(pose, "Chute", (0, 0, 0, 0.05 * math.sin(TAU * u), 0.15 * math.sin(TAU * u * 0.5), 0.05 * math.sin(TAU * u + 1)))

    thrust_clips(H, 0.8, extra=extra, hover=True, attack="ram", bank=0.1)
    return H


# ================================================================================================ moon lander
@hero("moon lander", "spacecraft")
def moon_lander():
    H = S("moon lander", gait="hover")
    H.preview = {"primary": "#FFD54F", "secondary": "#C0C0C0"}
    H.body((0, 2.4, 0))
    # descent stage: gold-foil octagonal box
    ds = A.lathe([(1.4, 0.0), (1.4, 2.0), (2.9, 2.0), (2.9, 0.0)], axis=1, segs=8, rot=(0, 22.5, 0))
    dpiece(H, "Hull", "Body", ds, col="primary", mat="foil", fallback="Block", pattern=lambda Q: 0.85 + 0.15 * np.sin(Q[:, 0] * 7.0 + Q[:, 1] * 5.0) * np.cos(Q[:, 2] * 6.0))
    dpiece(H, "Engine", "Body", merge(A.lathe([(1.4, 0.45), (0.8, 0.95), (0.8, 0.85), (1.3, 0.38)], axis=1, segs=16, closed=True)), col="gunmetal", mat="metal", role="detail")
    # ascent stage: faceted cabin with triangular windows, antenna dish, porch + ladder
    asc = merge(box((2.8, 1.6, 2.4), (0, 3.7, 0.2), r=0.1), box((2.2, 1.0, 1.0), (0, 3.6, -1.1), r=0.1, rot=(0, 0, 0)), cyl(0.7, 0.5, (0, 4.6, 0.3), axis=1, segs=12))
    dpiece(H, "Cabin", "Body", asc, col="secondary", mat="metal", role="body")
    win = merge(*[xform(box((0.5, 0.5, 0.08), (0, 0, 0), r=0.04), (s * 0.55, 3.9, -1.62), (0, s * 25, 0)) for s in (1, -1)])
    dpiece(H, "Windows", "Body", win, col=TINT, mat="glass", role="glass", pri=1.5)
    dish = merge(tube([[1.1, 4.4, 0.8], [1.6, 5.4, 1.0]], 0.05, 5), A.lathe([(0.0, 0.0), (0.05, 0.5), (0.15, 0.6), (0.18, 0.6), (0.08, 0.5), (0.03, 0.0)], axis=1, segs=14, pos=(1.65, 5.35, 1.0), rot=(30, 0, 0)))
    dpiece(H, "Dish", "Body", dish, col="white", mat="metal", role="detail")
    dpiece(H, "Porch", "Body", merge(box((1.2, 0.08, 0.9), (0, 2.05, -2.0), r=0.02), tube([[-0.5, 2.0, -2.4], [-0.5, 0.4, -3.1]], 0.04, 4), tube([[0.5, 2.0, -2.4], [0.5, 0.4, -3.1]], 0.04, 4),
                                     *[tube([[-0.5, y, -2.4 - (2.0 - y) * 0.44], [0.5, y, -2.4 - (2.0 - y) * 0.44]], 0.03, 4) for y in np.linspace(0.6, 1.8, 5)]), col="metal", mat="metal", role="detail")
    # four spidery legs with foot pads
    legs = []
    for a in (45, 135, 225, 315):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        foot = np.array([3.6 * c, 0.2, 3.6 * s])
        legs += [tube([[2.3 * c, 2.2, 2.3 * s], foot], 0.12, 6), tube([[2.6 * c, 1.0, 2.6 * s], foot * np.array([0.92, 1, 0.92]) + np.array([0, 0.6, 0])], 0.06, 5),
                 A.lathe([(0.0, 0.0), (0.0, 0.55), (0.18, 0.5), (0.25, 0.2), (0.25, 0.0)], axis=1, segs=12, pos=tuple(foot - np.array([0, 0.2, 0])))]
    dpiece(H, "Legs", "Body", merge(*legs), col="primary", mat="foil", role="limb")
    dpiece(H, "Seat", "Body", bucket_seat((0, 4.95, 0.3), w=0.8), col="dark", mat="cloth", role="detail")
    H.prim("Flame", "Body", "Ball", (1.0, 0.8, 1.0), (0, 0.55, 0), col="flame", glow=True, role="light", pri=2.4)
    common(H, (0, 5.15, 0.3), (0.8, 0.15, 0.8), (0, 3.5, -2.0), (0, 0.4, 0), 6.5)
    thrust_clips(H, 0.8, hover=True, attack="ram", bank=0.1)
    return H


# ================================================================================================ word map
MAP = [
    ("rocket", "rocket, rocket ship, rocketship, space rocket, rocket sled, model rocket", B),
    ("space shuttle", "space shuttle, shuttle, orbiter, space plane", B),
    ("spaceship", "spaceship, space ship, starship, spacecraft, star cruiser, starship cruiser, warp ship, generation ship, space tug, alien warlord ship, mothership, space station", B),
    ("spaceship", "alien warlord ship, alien warship", None),
    ("starfighter", "starfighter, space fighter, space jet", B),
    ("ufo", "ufo, flying saucer, saucer, alien spaceship, alien ship, alien saucer fleet", B),
    ("space capsule", "!time capsule, space capsule, capsule, space pod, escape pod, satellite, probe, solar sail", B),
    ("moon lander", "moon lander, lunar lander, lunar module", B),
]
