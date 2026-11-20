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
from airsea_kit import Fus, dpiece, dmpiece, box, cyl, rev, tube, merge, xform, mirror, sphere, wheel, window_row, band, SplitFus, zrange, ride, cockpit, GLASS, SCREEN

TAU = 2 * math.pi
TINT = [0.16, 0.2, 0.26]
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
    """Retro rocket ship lying on its four fins at real game scale (30 studs long): the rider sits in a cockpit in
    the nose section under a bubble canopy (seat, panel, stick), portholes, engine bell with exhaust glows
    (Burner, BurnerCore)."""
    H = S("rocket")
    H.preview = {"primary": "#F2F3F5", "secondary": "#E53935", "dark": "#2B2F36"}
    R, yc = 3.0, 4.5
    hip = (0.0, yc - 0.75, -4.6)
    F = SplitFus([(-15.0, 0.0, 0.0, 0.0, yc), (-14.4, 0.95, 0.95, 0.95, yc), (-12.0, 2.05, 2.05, 2.05, yc), (-9.4, 2.7, 2.7, 2.75, yc),
                  (-7.6, 2.95, 2.95, 3.1, yc), (-5.0, R, R, 3.6, yc), (-2.6, R, R, 3.5, yc), (-0.8, R, R, R + 0.05, yc), (8.0, R, R, R, yc),
                  (10.6, 2.7, 2.7, 2.7, yc), (11.6, 2.2, 2.2, 2.2, yc), (11.8, 0.0, 0.0, 0.0, yc)], n=40, p_lo=2.0, p_up=2.0)
    H.body((0, yc, 0))
    zg0, zg1, zn = -7.9, -1.2, -10.4
    zs = zrange(-15.0, 11.8, 0.8, (zg0, zg1, zn))
    zs = sorted(set(zs + list(np.linspace(-15.0, -13.8, 4)) + [11.6]))
    zh = [z for z in zs if z >= zn]
    dpiece(H, "Hull", "Body", merge(F.lower(zh, n=30), F.upper([z for z in zh if z <= zg0], n=26), F.upper([z for z in zh if z >= zg1], n=26)),
           col="primary", mat="metal", fallback="Ellipsoid")
    dpiece(H, "Nose", "Body", F.shell([z for z in zs if z <= zn], n=30), col="secondary", mat="metal", role="body", pri=1.1)
    dpiece(H, "CanopyGlass", "Body", F.upper([z for z in zs if zg0 <= z <= zg1], th=0.08, n=28), col=GLASS, mat="glass", tr=0.5, role="glass", pri=1.1)
    dpiece(H, "CanopyFrame", "Body", merge(F.ring(zg0, r=0.15, out=0.03), F.ring(zg1, r=0.15, out=0.03), F.line(np.linspace(zg0, zg1, 12), yfn=F.yc, r=0.12, out=0.05),
                                           tube([[0, F.top(z) + 0.05, z] for z in np.linspace(zg0, zg1, 10)], 0.1, 6)), col="dark", role="detail", pri=1.3)
    bands = [A.lathe([(z - 0.3, R + 0.08), (z + 0.3, R + 0.08), (z + 0.3, R - 0.12), (z - 0.3, R - 0.12)], axis=2, segs=40, pos=(0, yc, 0), closed=True) for z in (1.8, 7.6)]
    rivets = [sphere(0.07, (R * math.cos(a), yc + R * math.sin(a), z), segs=6) for z in (1.1, 2.5, 6.9, 8.3) for a in np.linspace(0, TAU, 20, endpoint=False)]
    dpiece(H, "Bands", "Body", merge(*bands), col="secondary", mat="metal", role="detail", pri=1.3)
    dpiece(H, "Rivets", "Body", merge(*rivets), col="metal", mat="metal", role="detail", pri=2.6)
    ports = []
    for z in (0.0, 4.6):
        for s in (1, -1):
            ports.append(A.lathe([(-0.08, 0.0), (-0.08, 0.62), (0.1, 0.62), (0.1, 0.0)], axis=0, segs=18, pos=(s * (R - 0.02), yc + 0.6, z)))
    rims = [A.lathe([(-0.06, 0.82), (0.16, 0.8), (0.16, 0.6), (-0.06, 0.6)], axis=0, segs=18, pos=(s * (R - 0.02), yc + 0.6, z), closed=True) for z in (0.0, 4.6) for s in (1, -1)]
    dpiece(H, "PortGlass", "Body", merge(*ports), col=TINT, mat="glass", tr=0.45, role="glass", pri=1.6)
    dpiece(H, "PortRims", "Body", merge(*rims), col="metal", mat="metal", role="detail", pri=1.9)
    # four fins reaching the ground (X layout), engine bell + glows
    fins = []
    for a in (45, 135, 225, 315):
        f = A.fin(3.25, 7.4, 2.6, 4.2, thick=0.5, pos=(0, R - 0.35, 3.6))
        fins.append(xform(f, (0, yc, 0), (0, 0, a)))
    tips = [xform(rev([(-1.6, 0.0), (-1.3, 0.3), (1.4, 0.32), (1.7, 0.0)], axis=2, segs=12, pos=(0, R - 0.35 + 3.25, 3.6 + 4.2 + 1.2)), (0, yc, 0), (0, 0, a)) for a in (45, 135, 225, 315)]
    dpiece(H, "Fins", "Body", merge(*fins), col="secondary", mat="metal", role="limb", pri=1.0)
    dpiece(H, "FinTips", "Body", merge(*tips), col="metal", mat="metal", role="detail", pri=1.6)
    dpiece(H, "Engine", "Body", merge(bell((0, yc, 11.4), 2.5, 2.6), cyl(1.6, 0.6, (0, yc, 11.6), axis=2, segs=20)), col="gunmetal", mat="metal", role="detail", pri=1.2)
    H.prim("Burner", "Body", "Cylinder", (0.1, 4.2, 4.2), (0, yc, 13.4), rot=(0, math.pi / 2, 0), col="flame", glow=True, role="light", pri=2.2)
    H.prim("BurnerCore", "Body", "Ball", (2.6, 2.6, 3.6), (0, yc, 14.6), col="flameCore", glow=True, role="light", pri=2.5, tr=0.35)
    cockpit(H, F, hip, floor_y=hip[1] - 1.25, panel_z=hip[2] - 2.05, panel_w=4.0, panel_top=hip[1] + 1.15, screens=2)
    ride(H, hip, (-5.0, -4.6), -15.3, 14.0, hip[1] + 3.9, exhaust=(0, yc, 14.2))
    A.craft_clips(H, 30.0, attack="roll", bank=0.35)
    return H


# ================================================================================================ space shuttle
@hero("space shuttle", "spacecraft")
def space_shuttle():
    """Orbiter riding its external tank and two boosters at real game scale (48 studs long stack): the rider flies
    from the orbiter's nose cockpit behind a wrap-around windscreen (seat, panel, yoke), delta wings with dark
    heat-shield undersides, payload bay doors, three main engines + OMS pods, exhaust glows (Burner*)."""
    H = S("space shuttle")
    H.preview = {"primary": "#F2F3F5", "secondary": "#22262C", "dark": "#2B2F36"}
    Rt, yt = 3.5, 3.6
    R = 2.9
    yc = yt + Rt + 0.55 + R
    z0, z1 = -17.0, 17.0
    H.body((0, yc, 0))
    F = Fus([(z0, 0.0, 0.0, yc - 0.6 * R), (z0 + 0.4, 0.42 * R, 0.36 * R, yc - 0.55 * R), (z0 + 1.8, 0.72 * R, 0.66 * R, yc - 0.32 * R),
             (z0 + 3.6, 0.9 * R, 0.88 * R, yc - 0.12 * R), (z0 + 5.6, 0.99 * R, 0.99 * R, yc - 0.01 * R), (z0 + 7.4, R, R, yc), (z1 - 1.0, R, 0.98 * R, yc + 0.05),
             (z1, 0.97 * R, 0.9 * R, yc + 0.05)], n=36, p=2.6, smooth=True)
    hip = (0.0, yc + R - 3.95, z0 + 6.8)
    ylo, yhi = hip[1] + 0.9, hip[1] + 2.75
    zw0, zw1 = z0 + 2.8, z0 + 8.6
    zs = zrange(z0, z1, 0.75, (zw0, zw1))
    zs = sorted(set(zs + list(np.linspace(z0, z0 + 1.8, 5))))
    zc = [z for z in zs if zw0 <= z <= zw1]
    tiles = lambda Q: np.where(Q[:, 1] < yc - 0.45 * R, 0.16, 1.0)
    hull = [band(F, [z for z in zs if z <= zw0], th=0.2, n=34), band(F, [z for z in zs if z >= zw1], th=0.2, n=34),
            band(F, zc, yhi=ylo, th=0.2, n=24), band(F, zc, ylo=yhi, th=0.2, n=16)]
    dpiece(H, "Hull", "Body", merge(*hull), col="primary", mat="hard", fallback="Ellipsoid", pattern=tiles)
    gl = band(F, zc, ylo=ylo, yhi=yhi, side=True, th=0.08, n=8)
    dpiece(H, "CockpitGlass", "Body", merge(gl, mirror(gl)), col=[0.3, 0.38, 0.46], mat="glass", tr=0.45, role="glass", pri=1.1)
    posts = []
    for z in (zw0 + 2.0, zw0 + 4.0):
        a0, a1 = A.fus_angle(F, z, ylo), A.fus_angle(F, z, yhi)
        posts.append(tube([A.fus_point(F, z, a, -0.04) for a in np.linspace(a0, a1, 6)], 0.14, 6))
    pm = merge(*posts)
    frames = merge(pm, mirror(pm), A.surface_line(F, np.linspace(zw0, zw1, 10), ylo, r=0.12, out=0.04),
                   tube([[0, min(F.y_top(z), yhi) + 0.05, z] for z in np.linspace(zw0, zw0 + 2.6, 5)], 0.12, 6))
    nose = Fus([(z0 - 0.03, 0.0, 0.0, yc - 0.6 * R), (z0 + 0.4, 0.44 * R, 0.38 * R, yc - 0.55 * R), (z0 + 1.2, 0.62 * R, 0.56 * R, yc - 0.42 * R)], n=36, p=2.6).mesh()
    dpiece(H, "NoseCap", "Body", merge(nose, frames), col="secondary", role="detail", pri=1.2)
    # payload bay doors (panel seams), OMS pods, fin, engines
    bay = merge(tube([[0, F.y_top(z) + 0.03, z] for z in np.linspace(zw1 + 0.5, z1 - 4.0, 8)], 0.06, 4),
                *[A.ring_line(F, z, r=0.06, ylo=yc + 0.5 * R, out=0.0, n=12) for z in np.linspace(zw1 + 0.5, z1 - 4.0, 5)])
    dpiece(H, "BayDoors", "Body", bay, col=[0.62, 0.64, 0.66], role="detail", pri=2.0)
    oms = Fus([(z1 - 9.0, 0.0, 0.0, yc + 0.6 * R), (z1 - 7.4, 0.8, 0.7, yc + 0.66 * R), (z1 + 0.3, 0.95, 0.85, yc + 0.66 * R), (z1 + 0.5, 0.0, 0.0, yc + 0.66 * R)], n=16, smooth=True)
    om = xform(oms.mesh(samples=np.linspace(z1 - 9.0, z1 + 0.5, 8)), (1.55, 0, 0))
    dpiece(H, "OMS", "Body", merge(om, mirror(om)), col="primary", mat="hard", role="detail", pri=1.3)
    fin = A.fin(7.0, 8.5, 3.2, 6.0, thick=0.7, pos=(0, yc + 0.85 * R, z1 - 9.5))
    dpiece(H, "Fin", "Body", fin, col="primary", mat="hard", role="detail", pri=1.1)
    w = A.wing(8.6, 18.0, 2.6, sweep=13.5, thick=1.0, dihedral=2, pos=(1.4, yc - 0.65 * R, z0 + 13.5), nt=9, nu=8)
    st = A.wing(1.8, 9.0, 0.6, sweep=7.5, thick=0.5, pos=(1.4, yc - 0.6 * R, z0 + 7.0))
    dpiece(H, "Wings", "Body", merge(w, mirror(w), st, mirror(st)), col="primary", mat="hard", role="wing", pattern=lambda Q: np.where(Q[:, 1] < yc - 0.65 * R - 0.05, 0.16, 1.0))
    eng = merge(bell((0, yc + 0.9, z1 - 0.2), 1.25, 2.4), bell((1.5, yc - 1.0, z1 - 0.2), 1.25, 2.4), bell((-1.5, yc - 1.0, z1 - 0.2), 1.25, 2.4),
                bell((1.55, yc + 0.66 * R, z1 + 0.3), 0.55, 1.0), bell((-1.55, yc + 0.66 * R, z1 + 0.3), 0.55, 1.0))
    dpiece(H, "Engines", "Body", eng, col="gunmetal", mat="metal", role="detail", pri=1.2)
    # external tank + boosters (the stack rests on them)
    tank = rev([(-23.0, 0.0), (-21.6, 1.6), (-19.0, 3.0), (-16.0, Rt), (20.5, Rt), (21.6, 2.4), (22.0, 0.0)], axis=2, segs=32, pos=(0, yt, 0), spline=3)
    dpiece(H, "Tank", "Body", tank, col=[0.82, 0.45, 0.2], mat="foil", role="body", pattern=lambda Q: 0.88 + 0.12 * np.cos(np.arctan2(Q[:, 1] - yt, Q[:, 0]) * 18))
    srb = []
    bx, by, br = Rt + 1.75, yt - 0.6, 1.7
    for s in (1, -1):
        srb.append(rev([(-22.0, 0.0), (-21.0, 0.8), (-19.6, br), (18.6, br), (19.6, br * 1.15), (20.2, 0.0)], axis=2, segs=24, pos=(s * bx, by, 0), spline=3))
        srb.append(bell((s * bx, by, 19.8), br * 1.1, 1.6))
    dpiece(H, "Boosters", "Body", merge(*srb), col="white", role="body", pri=1.0)
    sm = merge(*[A.lathe([(z - 0.3, br + 0.06), (z + 0.3, br + 0.06), (z + 0.3, br - 0.1), (z - 0.3, br - 0.1)], axis=2, segs=24, pos=(bx, by, 0), closed=True) for z in (-12.0, 0.0, 12.0)])
    struts = merge(cyl(0.45, 1.3, (0, yt + Rt + 0.35, -11.5), axis=1, segs=12), cyl(0.35, 1.3, (1.0, yt + Rt + 0.35, 12.0), axis=1, segs=12), cyl(0.35, 1.3, (-1.0, yt + Rt + 0.35, 12.0), axis=1, segs=12),
                   tube([[Rt - 0.2, yt - 0.3, -15.0], [bx - br + 0.2, by, -15.0]], 0.3, 8), tube([[Rt - 0.2, yt - 0.3, 15.0], [bx - br + 0.2, by, 15.0]], 0.3, 8))
    dpiece(H, "Struts", "Body", merge(sm, mirror(sm), struts, mirror(struts)), col="dark", mat="metal", role="detail", pri=1.6)
    for nm, (x, y, r_) in (("BurnerR", (bx, by, br * 1.6)), ("BurnerL", (-bx, by, br * 1.6)), ("BurnerC", (0, yc + 0.9, 1.9))):
        H.prim(nm, "Body", "Cylinder", (0.1, r_ * 1.25, r_ * 1.25), (x, y, (21.5 if nm != "BurnerC" else z1 + 2.3)), rot=(0, math.pi / 2, 0), col="flame", glow=True, role="light", pri=2.2)
    cockpit(H, SplitFus([(z, *F.at(z)[:2], F.at(z)[1], F.at(z)[2]) for z in np.linspace(z0, zw1 + 1, 12)], n=12), hip,
            floor_y=hip[1] - 1.25, panel_z=hip[2] - 2.05, panel_w=4.2, panel_top=hip[1] + 1.15, ctrl="yoke", screens=3)
    dpiece(H, "CockpitWall", "Body", A.bulkhead(F, hip[2] + 2.2, ylo=hip[1] - 1.3), col="darker", role="detail", pri=1.7)
    ride(H, hip, (-7.0, z0 + 6.8), -23.2, 22.0, hip[1] + 4.0, exhaust=(0, yc + 0.9, z1 + 2.6))
    A.craft_clips(H, 45.0, attack="dive", bank=0.25)
    return H


# ================================================================================================ spaceship
@hero("spaceship", "spacecraft")
def spaceship():
    """Sci-fi shuttle at real game scale (30 studs long, 22 stud span): wedge hull with a bubble canopy over the
    cockpit (seat, panel with screens, stick), swept wings with drooping tips, twin fins, three thrusters with glow
    discs (Glow*), nose cannons, landing legs on GearF / GearR / GearL."""
    H = S("spaceship")
    H.preview = {"primary": "#E8ECF0", "secondary": "#2979FF", "dark": "#2B2F36"}
    yc = 4.7
    hip = (0.0, 4.0, -5.6)
    F = SplitFus([(-15.2, 0.0, 0.0, 0.0, 4.2), (-14.6, 0.75, 0.38, 0.32, 4.22), (-12.4, 1.75, 0.95, 0.85, 4.35), (-9.8, 2.35, 1.8, 1.9, 4.55),
                  (-7.6, 2.5, 2.25, 3.0, yc), (-5.0, 2.55, 2.3, 3.15, yc), (-2.6, 2.75, 2.2, 2.6, yc), (0.0, 3.3, 2.05, 1.75, yc),
                  (5.0, 3.9, 1.95, 1.6, yc), (10.0, 3.8, 1.85, 1.5, yc), (12.6, 3.5, 1.75, 1.4, yc), (12.9, 0.0, 0.0, 0.0, yc)], n=36, p_lo=3.2, p_up=2.6)
    H.body((0, yc, 0))
    zg0, zg1, zn = -9.6, -1.9, -12.0
    zs = zrange(-15.2, 12.9, 0.8, (zg0, zg1, zn))
    zs = sorted(set(zs + list(np.linspace(-15.2, -14.0, 4)) + [12.7]))
    zh = [z for z in zs if z >= zn]
    sh = lambda Q: 0.8 + 0.2 * np.clip((Q[:, 1] - 2.9) / 1.8, 0, 1)
    dpiece(H, "Hull", "Body", merge(F.lower(zh, n=26), F.upper([z for z in zh if z <= zg0], n=22), F.upper([z for z in zh if z >= zg1], n=22)),
           col="primary", mat="metal", fallback="Ellipsoid", pattern=sh)
    dpiece(H, "Nose", "Body", F.shell([z for z in zs if z <= zn], n=26), col="secondary", mat="metal", role="body", pri=1.1)
    dpiece(H, "CanopyGlass", "Body", F.upper([z for z in zs if zg0 <= z <= zg1], th=0.08, n=28), col=[0.35, 0.65, 0.95], mat="glass", tr=0.45, role="glass", pri=1.1)
    dpiece(H, "CanopyFrame", "Body", merge(F.ring(zg0, r=0.14, out=0.03), F.ring(zg0 + 2.0, r=0.1, out=0.04), F.ring(zg1, r=0.14, out=0.03),
                                           F.line(np.linspace(zg0, zg1, 12), yfn=F.yc, r=0.1, out=0.05)), col="dark", role="detail", pri=1.3)
    spine = merge(box((0.9, 0.35, 10.5), (0, F.top(5.0) + 0.05, 5.4), r=0.15),
                  *[F.ring(z, r=0.05, ylo="full", out=0.0, n=28) for z in (1.5, 7.5)])
    dpiece(H, "Trim", "Body", merge(spine, F.line(np.linspace(-11.8, 12.4, 22), yfn=lambda z: F.yc(z) - 0.2, r=0.14, out=0.05)), col="secondary", role="detail", pri=1.3)
    # wings with drooping tips, twin fins
    w = A.wing(7.6, 9.0, 2.6, sweep=6.2, thick=0.6, dihedral=-3, pos=(3.1, 4.1, -1.2), nt=9, nu=8)
    tx, ty_ = 3.1 + 7.6, 4.1 - 7.6 * math.tan(math.radians(3))
    tip = xform(A.fin(2.0, 2.7, 1.4, 1.0, thick=0.24, pos=(0, 0, 0)), (tx - 0.05, ty_, -1.2 + 6.2 + 0.1), (0, 0, 155))
    dpiece(H, "Wings", "Body", merge(w, mirror(w)), col="primary", mat="metal", role="wing", pattern=sh)
    stripe = box((3.6, 0.08, 0.6), (6.9, 4.1 - 3.8 * math.tan(math.radians(3)) + 0.32, 4.6), r=0.03, rot=(0, -32, -3))
    dpiece(H, "WingTips", "Body", merge(tip, mirror(tip), stripe, mirror(stripe)), col="secondary", role="detail", pri=1.3)
    f = A.fin(4.2, 4.6, 1.6, 3.4, thick=0.34, pos=(0, 0, 0))
    f = xform(f, (2.4, F.top(7.0) - 0.2, 6.8), (0, 0, -18))
    dpiece(H, "Fins", "Body", merge(f, mirror(f)), col="primary", mat="metal", role="detail", pri=1.2)
    # thrusters + glow discs
    th_ = []
    for x, y in ((1.75, 4.55), (-1.75, 4.55), (0.0, 5.75)):
        th_.append(A.lathe([(11.6, 1.2), (12.4, 1.24), (14.2, 1.05), (14.2, 0.9), (12.6, 0.95), (12.2, 0.75)], axis=2, segs=22, pos=(x, y, 0), closed=True))
    dpiece(H, "Thrusters", "Body", merge(*th_), col="gunmetal", mat="metal", role="detail", pri=1.2)
    for i, (x, y) in enumerate(((1.75, 4.55), (-1.75, 4.55), (0.0, 5.75))):
        H.prim(f"Glow{i}", "Body", "Cylinder", (0.08, 1.8, 1.8), (x, y, 13.2), rot=(0, math.pi / 2, 0), col="secondary", glow=True, role="light", pri=2.2)
    # nose cannons
    gn = []
    for s in (1, -1):
        gn += [cyl(0.35, 2.6, (s * 2.6, 3.6, -7.0), axis=2, segs=12, bevel=0.1), cyl(0.14, 3.0, (s * 2.6, 3.6, -9.6), axis=2, segs=10), cyl(0.22, 0.4, (s * 2.6, 3.6, -11.0), axis=2, segs=10)]
    dpiece(H, "Guns", "Body", merge(*gn), col="gunmetal", mat="metal", role="detail", pri=1.6)
    H.prim("NavLightR", "Body", "Ball", (0.3, 0.3, 0.3), (tx + 0.2, ty_ - 0.2, 5.5), col=[0.2, 0.95, 0.35], glow=True, role="light", pri=2.4)
    H.prim("NavLightL", "Body", "Ball", (0.3, 0.3, 0.3), (-tx - 0.2, ty_ - 0.2, 5.5), col="red", glow=True, role="light", pri=2.4)
    cockpit(H, F, hip, floor_y=hip[1] - 1.25, panel_z=hip[2] - 2.05, panel_w=3.8, panel_top=hip[1] + 1.15, screens=3)
    legs3(H, [("GearF", (0, F.bottom(-9.0) + 0.3, -9.0), (0, 0.0, -9.6)), ("GearR", (2.6, F.bottom(4.0) + 0.4, 4.0), (3.4, 0.0, 4.6)),
              ("GearL", (-2.6, F.bottom(4.0) + 0.4, 4.0), (-3.4, 0.0, 4.6))], r=0.22, pad=0.6)
    ride(H, hip, (-5.0, -5.6), -15.5, 14.3, hip[1] + 3.9, muzzle=(2.6, 3.6, -11.3), exhaust=(0, 4.8, 14.3))
    A.craft_clips(H, 30.0, attack="dive", bank=0.45)
    return H


# ================================================================================================ starfighter
@hero("starfighter", "spacecraft")
def starfighter():
    """Space fighter at real game scale (26 studs long, 18 stud span): dart hull with a canopy cockpit (seat, panel,
    stick), canards, straight wings carrying two engine pods with cannons, dorsal fin, glow discs (Glow*), landing
    legs on GearF / GearR / GearL."""
    H = S("starfighter")
    H.preview = {"primary": "#DDE2E6", "secondary": "#E53935", "dark": "#2B2F36"}
    yc = 4.5
    hip = (0.0, 3.85, -3.4)
    F = SplitFus([(-13.6, 0.0, 0.0, 0.0, 4.2), (-13.0, 0.5, 0.42, 0.35, 4.22), (-10.4, 1.35, 1.15, 1.0, 4.3), (-7.6, 2.1, 1.85, 1.75, 4.42),
                  (-5.6, 2.45, 2.2, 2.9, yc), (-3.0, 2.5, 2.25, 3.15, yc), (-0.6, 2.5, 2.15, 2.6, yc), (2.0, 2.4, 1.95, 1.6, yc),
                  (7.0, 2.2, 1.75, 1.4, yc), (11.0, 2.0, 1.55, 1.3, yc), (12.2, 1.6, 1.3, 1.1, yc), (12.4, 0.0, 0.0, 0.0, yc)], n=36, p_lo=2.8, p_up=2.5)
    H.body((0, yc, 0))
    zg0, zg1, zn = -7.3, -0.5, -9.6
    zs = zrange(-13.6, 12.4, 0.8, (zg0, zg1, zn))
    zs = sorted(set(zs + list(np.linspace(-13.6, -12.4, 4)) + [12.2]))
    zh = [z for z in zs if z >= zn]
    sh = lambda Q: 0.8 + 0.2 * np.clip((Q[:, 1] - 2.6) / 1.8, 0, 1)
    dpiece(H, "Hull", "Body", merge(F.lower(zh, n=26), F.upper([z for z in zh if z <= zg0], n=22), F.upper([z for z in zh if z >= zg1], n=22)),
           col="primary", mat="metal", fallback="Ellipsoid", pattern=sh)
    dpiece(H, "Nose", "Body", F.shell([z for z in zs if z <= zn], n=26), col="secondary", mat="metal", role="body", pri=1.1)
    dpiece(H, "CanopyGlass", "Body", F.upper([z for z in zs if zg0 <= z <= zg1], th=0.08, n=28), col=[0.45, 0.55, 0.66], mat="glass", tr=0.45, role="glass", pri=1.1)
    dpiece(H, "CanopyFrame", "Body", merge(F.ring(zg0, r=0.14, out=0.03), F.ring(zg0 + 1.8, r=0.1, out=0.04), F.ring(zg1, r=0.14, out=0.03),
                                           F.line(np.linspace(zg0, zg1, 12), yfn=F.yc, r=0.1, out=0.05)), col="dark", role="detail", pri=1.3)
    dpiece(H, "Trim", "Body", merge(F.line(np.linspace(-9.4, 12.0, 20), yfn=lambda z: F.yc(z) - 0.35, r=0.15, out=0.05), *[F.ring(z, r=0.05, ylo="full", n=28) for z in (3.0, 8.0)]),
           col="secondary", role="detail", pri=1.3)
    # canards, wings + pods, fin, ventrals
    can = A.wing(2.6, 2.4, 0.9, sweep=1.6, thick=0.22, pos=(1.6, 4.25, -9.4))
    w = A.wing(5.6, 6.2, 3.4, sweep=1.2, thick=0.5, dihedral=0, pos=(2.1, 4.2, 1.0), nt=8, nu=8)
    dpiece(H, "Wings", "Body", merge(w, mirror(w), can, mirror(can)), col="primary", mat="metal", role="wing", pattern=sh)
    px, py = 7.4, 4.2
    pod = Fus([(-3.4, 0.0, 0.0, py), (-3.0, 0.75, 0.75, py), (-1.0, 1.15, 1.15, py), (5.0, 1.2, 1.2, py), (7.6, 1.05, 1.05, py), (7.75, 0.0, 0.0, py)], n=20, smooth=True)
    pm = xform(pod.mesh(samples=np.linspace(-3.4, 7.75, 12)), (px, 0, 0))
    nzl = A.lathe([(7.4, 1.08), (8.6, 0.95), (8.6, 0.82), (7.6, 0.85)], axis=2, segs=20, pos=(px, py, 0), closed=True)
    gun = merge(cyl(0.18, 4.2, (px, py + 0.2, -5.4), axis=2, segs=10), cyl(0.32, 0.8, (px, py + 0.2, -3.6), axis=2, segs=12, bevel=0.08), cyl(0.26, 0.5, (px, py + 0.2, -7.4), axis=2, segs=10))
    dmpiece(H, "Pod#", "Body", pm, col="primary", mat="metal", role="body", pri=1.1)
    dmpiece(H, "PodDetail#", "Body", merge(nzl, gun, A.lathe([(-1.6, 1.2), (-1.0, 1.2), (-1.0, 1.06), (-1.6, 1.06)], axis=2, segs=20, pos=(px, py, 0), closed=True)),
            col="gunmetal", mat="metal", role="detail", pri=1.3)
    fin = A.fin(4.4, 5.4, 1.8, 4.0, thick=0.36, pos=(0, F.top(6.0) - 0.15, 5.6))
    ven = xform(A.fin(1.6, 2.4, 1.2, 1.2, thick=0.22, pos=(0, 0, 0)), (1.5, F.bottom(8.5) + 0.2, 8.0), (0, 0, 180 - 25))
    dpiece(H, "Fins", "Body", merge(fin, ven, mirror(ven)), col="secondary", mat="metal", role="detail", pri=1.2)
    for i, (x, y) in enumerate(((px, py), (-px, py))):
        H.prim(f"Glow{i}", "Body", "Cylinder", (0.08, 1.65, 1.65), (x, y, 8.0), rot=(0, math.pi / 2, 0), col="secondary", glow=True, role="light", pri=2.2)
    H.prim("Glow2", "Body", "Cylinder", (0.08, 2.4, 2.4), (0, yc, 12.25), rot=(0, math.pi / 2, 0), col="secondary", glow=True, role="light", pri=2.3)
    cockpit(H, F, hip, floor_y=hip[1] - 1.25, panel_z=hip[2] - 2.05, panel_w=3.8, panel_top=hip[1] + 1.15, screens=2)
    legs3(H, [("GearF", (0, F.bottom(-7.0) + 0.3, -7.0), (0, 0.0, -7.6)), ("GearR", (px, py - 1.0, 2.0), (px + 0.4, 0.0, 2.6)),
              ("GearL", (-px, py - 1.0, 2.0), (-px - 0.4, 0.0, 2.6))], r=0.22, pad=0.6)
    ride(H, hip, (-4.6, -3.4), -13.8, 12.5, hip[1] + 3.9, muzzle=(px, py + 0.2, -7.7), exhaust=(0, yc, 12.6))
    A.craft_clips(H, 26.0, attack="roll", bank=0.55)
    return H


# ================================================================================================ ufo
def legs3(H, pts, r=0.18, pad=0.55, col="metal"):
    """Landing legs on bones GearF / GearR / GearL (pivot at the hull end; the game folds them in flight).
    pts: [(name, top, foot)]."""
    for nm, top, foot in pts:
        H.bone(nm, "Body", top)
        top, foot = np.asarray(top, float), np.asarray(foot, float)
        knee = (top + foot) / 2 + np.array([0, 0.25, 0]) + (foot - top) * np.array([0.08, 0, 0.08])
        m = merge(tube([top, knee, foot + np.array([0, pad * 0.35, 0])], r, 8), cyl(r * 1.6, 0.9, tuple(top + (knee - top) * 0.35), axis=1, segs=10, bevel=0.06),
                  A.lathe([(0.0, 0.0), (0.0, pad), (0.12, pad * 0.95), (0.3, pad * 0.45), (0.32, 0.0)], axis=1, segs=14, pos=tuple(foot - np.array([0, foot[1], 0]))))
        dpiece(H, nm + "P", nm, m, col=col, mat="metal", role="limb", pri=1.3)


@hero("ufo", "spacecraft")
def ufo():
    """Flying saucer at real game scale (18 stud disc): the rider sits in a sunken cockpit well in the middle under
    a glass dome (console ring, screens, stick), a light ring on bone Ring, beam emitter, three landing legs on
    GearF / GearR / GearL."""
    H = S("ufo", gait="hover")
    H.preview = {"primary": "#B8C4CE", "secondary": "#76FF03", "dark": "#2B2F36"}
    Rr, yb, yr, ytop, rd, yf = 9.0, 2.3, 3.75, 5.05, 3.25, 3.05
    H.body((0, yr, 0))
    hip = (0.0, yf + 1.25, 0.25)
    prof = [(0.0, yb + 0.25), (1.6, yb), (4.2, yb + 0.25), (6.6, yb + 0.75), (8.3, yr - 0.4), (Rr, yr - 0.08), (Rr, yr + 0.08), (8.3, yr + 0.45),
            (6.4, ytop - 0.6), (rd + 0.45, ytop), (rd, ytop), (rd - 0.08, ytop - 0.15), (rd - 0.15, yf + 0.25), (rd - 0.35, yf), (0.0, yf)]
    P_ = [(y, r) for r, y in prof]
    disc = A.lathe(P_, axis=1, segs=48)
    rings = lambda Q: np.where(np.abs(np.hypot(Q[:, 0], Q[:, 2]) - 6.3) < 0.12, 0.7, 1.0) * np.where(np.abs(np.hypot(Q[:, 0], Q[:, 2]) - 4.6) < 0.1, 0.75, 1.0)
    dpiece(H, "Hull", "Body", disc, col="primary", mat="metal", fallback="Ellipsoid", pattern=rings)
    up_r, up_y = [8.3, 6.4, rd + 0.45], [yr + 0.45, ytop - 0.6, ytop]
    ytop_at = lambda r: float(np.interp(r, up_r[::-1], up_y[::-1]))
    panels = []
    for a in np.linspace(0, TAU, 16, endpoint=False):
        c, s_ = math.cos(a), math.sin(a)
        panels.append(tube([[r * c, ytop_at(r) + 0.05, r * s_] for r in np.r_[np.linspace(3.9, 4.75, 3), np.linspace(6.65, 8.15, 5)]], 0.07, 4))
    band_ = A.lathe([(ytop_at(5.2) + 0.08, 5.2), (ytop_at(5.2) + 0.08, 4.8), (ytop_at(4.8) - 0.1, 4.8), (ytop_at(6.6) - 0.1, 6.6), (ytop_at(6.6) + 0.08, 6.6), (ytop_at(6.2) + 0.1, 6.2)],
                    axis=1, segs=48, closed=True)
    vents = [xform(box((0.9, 0.14, 0.32), (0, 0, 0), r=0.05), (7.2 * math.cos(a), ytop_at(7.2) + 0.06, 7.2 * math.sin(a)), (0, -math.degrees(a), 0)) for a in np.linspace(TAU / 32, TAU + TAU / 32, 8, endpoint=False)]
    panels += [band_, *vents]
    dpiece(H, "Seams", "Body", merge(*panels, A.lathe([(ytop - 0.03, rd + 0.45), (ytop + 0.18, rd + 0.45), (ytop + 0.18, rd + 0.1), (ytop - 0.03, rd + 0.1)], axis=1, segs=40, closed=True)),
           col="dark", mat="metal", role="detail", pri=1.6)
    # dome (glass) over the well
    dome = A.lathe([(ytop + 0.12, rd + 0.12), (ytop + 1.3, rd + 0.02), (ytop + 2.35, rd * 0.78), (ytop + 3.0, rd * 0.45), (ytop + 3.22, 0.0),
                    (ytop + 3.14, 0.0), (ytop + 2.92, rd * 0.43), (ytop + 2.28, rd * 0.75), (ytop + 1.25, rd - 0.06), (ytop + 0.12, rd + 0.04)], axis=1, segs=40)
    dpiece(H, "CanopyGlass", "Body", dome, col=[0.6, 0.88, 0.78], mat="glass", tr=0.5, role="glass", pri=1.1)
    # light ring (bone Ring) round the rim
    H.bone("Ring", "Body", (0, yr, 0))
    ring = A.lathe([(yr - 0.24, Rr - 0.05), (yr + 0.24, Rr - 0.05), (yr + 0.24, Rr - 0.32), (yr - 0.24, Rr - 0.32)], axis=1, segs=48, closed=True)
    dpiece(H, "RingP", "Ring", ring, col="gunmetal", mat="metal", role="detail", pri=1.2)
    lights = merge(*[sphere(0.24, ((Rr + 0.05) * math.cos(a), yr, (Rr + 0.05) * math.sin(a)), segs=8) for a in np.linspace(0, TAU, 16, endpoint=False)])
    dpiece(H, "Lights", "Ring", lights, col="secondary", mat="hard", role="light", glow=True, pri=2.2)
    # underside: emitter + beam glow
    em = merge(A.lathe([(yb - 0.35, 0.0), (yb - 0.35, 1.0), (yb - 0.05, 1.5), (yb + 0.3, 1.6), (yb + 0.3, 0.0)], axis=1, segs=24),
               A.lathe([(yb + 0.42, 3.35), (yb + 0.58, 3.35), (yb + 0.58, 3.15), (yb + 0.42, 3.15)], axis=1, segs=40, closed=True))
    dpiece(H, "Emitter", "Body", em, col="gunmetal", mat="metal", role="detail", pri=1.4)
    H.prim("Beam", "Body", "Cylinder", (0.1, 1.9, 1.9), (0, yb - 0.38, 0), rot=(0, 0, math.pi / 2), col="secondary", glow=True, role="light", pri=2.2)
    # cockpit: seat, console ring, screens, stick
    dpiece(H, "Seat", "Body", A.pilot_seat(hip, w=1.8, floor_y=yf), col="dark", mat="cloth", role="detail", pri=1.2)
    # keep only the front arc of the console (in front of the rider)
    cm = []
    for a in np.linspace(-150, -30, 6):
        ar = math.radians(a)
        cm.append(xform(box((1.3, 1.25, 0.65), (0, 0, 0), r=0.15), (2.45 * math.cos(ar), yf + 1.55, 2.45 * math.sin(ar)), (0, -a - 90, 0), ))
    dpiece(H, "Panel", "Body", merge(*cm), col="darker", role="detail", pri=1.3)
    for i, a in enumerate((-115, -90, -65)):
        ar = math.radians(a)
        H.prim(f"Screen{i + 1}", "Body", "Block", (0.9, 0.6, 0.05), (2.1 * math.cos(ar), yf + 1.7, 2.1 * math.sin(ar)), rot=(0, math.radians(-a - 90), 0),
               col=SCREEN, glow=True, role="light", pri=2.0)
    dpiece(H, "Controls", "Body", merge(A.stick(hip, yf, dz=-1.85, h=1.05), A.lathe([(yf - 0.02, 0.0), (yf - 0.02, 2.95), (yf + 0.06, 2.95), (yf + 0.06, 0.0)], axis=1, segs=32)),
           col="gunmetal", mat="metal", role="detail", pri=1.5)
    legs3(H, [("GearF", (0, yb + 0.3, -4.0), (0, 0.0, -5.6)), ("GearR", (3.46, yb + 0.3, 2.0), (4.85, 0.0, 2.8)), ("GearL", (-3.46, yb + 0.3, 2.0), (-4.85, 0.0, 2.8))])
    ride(H, hip, (-10.5, 0.0), -9.6, 9.6, hip[1] + 3.8, muzzle=(0, yb - 0.5, 0), exhaust=(0, yb - 0.4, 0))
    A.craft_clips(H, 18.0, hover=True, attack="ram", bank=0.15)
    return H


# ================================================================================================ space capsule
def upright(m):
    """Rotate a mesh built along +Z (height) so +Z becomes +Y and the section's +Y faces the front (-Z)."""
    return xform(m, (0, 0, 0), (-90, 0, 0))


@hero("space capsule", "spacecraft")
def space_capsule():
    """Crew capsule at real game scale (10 stud base, 9 studs tall) standing on its heat shield: the rider sits
    inside facing a large front window (seat, panel with screens, stick), hatch, RCS thruster quads, docking
    nose, a packed parachute canister on bone Chute and three landing legs on GearF / GearR / GearL."""
    H = S("space capsule", gait="hover")
    H.preview = {"primary": "#ECEFF1", "secondary": "#22262C", "dark": "#2B2F36"}
    H.body((0, 4.0, 0))
    hip = (0.0, 2.55, 0.55)
    cone = Fus([(0.9, 4.75, 4.75, 0.0), (1.25, 4.9, 4.9, 0.0), (1.6, 4.72, 4.72, 0.0), (7.4, 1.95, 1.95, 0.0), (8.0, 1.55, 1.55, 0.0), (8.15, 0.0, 0.0, 0.0)], n=40, p=2.0)
    zs = zrange(0.9, 8.15, 0.45, (2.95, 5.6, 1.25, 1.6, 7.4, 8.0))
    zw = [z for z in zs if 2.95 <= z <= 5.6]
    win = lambda z: 0.42 * cone.at(z)[0]
    hull = [band(cone, [z for z in zs if z <= 2.95], th=0.22, n=44), band(cone, [z for z in zs if z >= 5.6], th=0.22, n=44), band(cone, zw, yhi=win, th=0.22, n=40)]
    ribs = lambda Q: 0.9 + 0.1 * (np.cos(np.arctan2(Q[:, 2], Q[:, 0]) * 24) > 0.6)
    dpiece(H, "Hull", "Body", upright(merge(*hull)), col="primary", mat="foil", fallback="Ellipsoid", pattern=ribs)
    dpiece(H, "WindowGlass", "Body", upright(band(cone, zw, ylo=win, th=0.08, n=16)), col=GLASS, mat="glass", tr=0.5, role="glass", pri=1.1)
    fr = []
    for z in (2.95, 5.6):
        a0 = A.fus_angle(cone, z, win(z))
        fr.append(tube([A.fus_point(cone, z, a, -0.05) for a in np.linspace(a0, math.pi - a0, 10)], 0.14, 6))
    side = [A.fus_point(cone, z, A.fus_angle(cone, z, win(z)), -0.05) for z in np.linspace(2.95, 5.6, 5)]
    fr.append(tube(side, 0.14, 6))
    fr.append(mirror(tube(side, 0.14, 6)))
    fr.append(tube([A.fus_point(cone, z, math.pi / 2, -0.05) for z in np.linspace(2.95, 5.6, 5)], 0.1, 6))
    dpiece(H, "WindowFrame", "Body", upright(merge(*fr)), col="dark", role="detail", pri=1.3)
    shield = A.lathe([(0.0, 0.0), (0.0, 3.6), (0.25, 4.55), (0.75, 4.92), (1.15, 4.95), (1.15, 4.0), (0.9, 0.0)], axis=1, segs=48)
    dpiece(H, "Shield", "Body", shield, col=[0.42, 0.3, 0.22], mat="hard", role="detail", pri=1.1)
    rcs, rim = [], []
    for a in (45, 135, 225, 315):
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        r_ = cone.at(6.2)[0]
        rcs.append(xform(merge(box((0.7, 0.6, 0.4), (0, 0, 0), r=0.08), *[cyl(0.1, 0.35, (dx, dy, -0.3), axis=2, segs=6) for dx, dy in ((0.2, 0.15), (-0.2, 0.15), (0.2, -0.15), (-0.2, -0.15))]),
                         (c * (r_ + 0.15), 6.2, s_ * (r_ + 0.15)), (0, -a - 90, 0)))
    nose = merge(A.lathe([(8.1, 0.0), (8.1, 1.0), (8.7, 0.85), (8.7, 0.0)], axis=1, segs=20), A.lathe([(8.65, 0.95), (8.85, 0.95), (8.85, 0.7), (8.65, 0.7)], axis=1, segs=20, closed=True))
    hatch = xform(box((0.14, 2.0, 1.6), (0, 0, 0), r=0.12), (-(cone.at(4.0)[0] - 0.02), 4.0, 0.9), (0, 0, -24))
    dpiece(H, "RCS", "Body", merge(*rcs, nose, hatch), col="secondary", mat="metal", role="detail", pri=1.3)
    H.bone("Chute", "Body", (0, 8.9, 0))
    dpiece(H, "ChuteCan", "Chute", merge(A.lathe([(8.8, 0.0), (8.8, 0.62), (9.6, 0.6), (9.75, 0.0)], axis=1, segs=18), cyl(0.68, 0.12, (0, 9.2, 0), axis=1, segs=18)),
           col=[0.95, 0.45, 0.15], mat="cloth", role="detail", pri=1.6)
    # inside: seat, panel (curved to the window), stick
    dpiece(H, "Seat", "Body", A.pilot_seat(hip, w=1.8, floor_y=1.3), col="dark", mat="cloth", role="detail", pri=1.2)
    dpiece(H, "Floor", "Body", A.lathe([(1.15, 0.0), (1.15, 4.3), (1.3, 4.3), (1.3, 0.0)], axis=1, segs=32), col="darker", role="detail", pri=1.6)
    dpiece(H, "Panel", "Body", merge(xform(box((3.6, 1.0, 0.5), (0, 0, 0), r=0.14), (0, hip[1] + 0.65, hip[2] - 2.2), (-25, 0, 0)),
                                     box((0.8, hip[1] + 0.2 - 1.3, 0.6), (0, (hip[1] + 0.2 + 1.3) / 2, hip[2] - 2.2), r=0.1)), col="darker", role="detail", pri=1.3)
    for i, x in enumerate((-0.9, 0.9)):
        H.prim(f"Screen{i + 1}", "Body", "Block", (1.0, 0.6, 0.05), (x, hip[1] + 0.7, hip[2] - 1.93), rot=(math.radians(-25), 0, 0), col=SCREEN, glow=True, role="light", pri=2.0)
    dpiece(H, "Controls", "Body", A.stick(hip, 1.3, dz=-1.8, h=1.0), col="gunmetal", mat="metal", role="detail", pri=1.6)
    legs3(H, [("GearF", (0, 1.5, -3.6), (0, 0.0, -5.0)), ("GearR", (3.1, 1.5, 1.8), (4.3, 0.0, 2.5)), ("GearL", (-3.1, 1.5, 1.8), (-4.3, 0.0, 2.5))], r=0.2, pad=0.6)
    ride(H, hip, (-6.0, 0.0), -5.0, 5.0, hip[1] + 3.9, exhaust=(0, 0.2, 0))

    def extra(name, u, pose):
        A._add(pose, "Chute", (0, 0, 0, 0.01 * math.sin(TAU * u), 0, 0.01 * math.sin(TAU * u + 1)))

    A.craft_clips(H, 10.0, hover=True, attack="ram", bank=0.08, extra=extra)
    return H


# ================================================================================================ moon lander
@hero("moon lander", "spacecraft")
def moon_lander():
    """Lunar lander at real game scale (13 stud footprint, 12 studs tall): gold-foil descent stage on four spidery
    legs (GearFR / GearFL / GearBR / GearBL), faceted ascent cabin the rider sits in behind two front windows (seat,
    panel, stick), antenna dish, porch + ladder, engine bell with a glow."""
    H = S("moon lander", gait="hover")
    H.preview = {"primary": "#E9B949", "secondary": "#C7CCD2", "dark": "#2B2F36"}
    H.body((0, 4.0, 0))
    ds = A.lathe([(1.5, 0.0), (1.5, 4.3), (4.6, 4.3), (4.6, 0.0)], axis=1, segs=8, rot=(0, 22.5, 0))
    foil = lambda Q: 0.8 + 0.2 * np.sin(Q[:, 0] * 5.0 + Q[:, 1] * 3.7) * np.cos(Q[:, 2] * 4.3 + Q[:, 1] * 2.1)
    dpiece(H, "Hull", "Body", ds, col="primary", mat="foil", fallback="Block", pattern=foil)
    dpiece(H, "Engine", "Body", A.lathe([(1.5, 0.75), (0.6, 1.5), (0.6, 1.38), (1.45, 0.65)], axis=1, segs=20, closed=True), col="gunmetal", mat="metal", role="detail", pri=1.3)
    H.prim("Burner", "Body", "Cylinder", (0.1, 2.4, 2.4), (0, 0.75, 0), rot=(0, 0, math.pi / 2), col="flame", glow=True, role="light", pri=2.3)
    # ascent cabin: hollow box (floor, back, sides, roof) + faceted front with two windows
    y0, y1, hw, z0, z1 = 4.6, 10.2, 2.55, -2.3, 2.6
    hip = (0.0, y0 + 0.2 + 1.25, 0.4)
    walls = [box((2 * hw, 0.25, z1 - z0), (0, y0 + 0.12, (z0 + z1) / 2), r=0.06), box((2 * hw, y1 - y0, 0.25), (0, (y0 + y1) / 2, z1 - 0.12), r=0.06),
             box((0.25, y1 - y0, z1 - z0), (hw - 0.12, (y0 + y1) / 2, (z0 + z1) / 2), r=0.06), box((0.25, y1 - y0, z1 - z0), (-hw + 0.12, (y0 + y1) / 2, (z0 + z1) / 2), r=0.06),
             box((2 * hw, 0.25, z1 - z0 + 0.6), (0, y1 - 0.12, (z0 + z1) / 2 - 0.3), r=0.06)]
    wy0, wy1 = hip[1] + 0.9, hip[1] + 2.8
    fz = z0 - 0.4
    walls += [box((2 * hw, wy0 - y0, 0.25), (0, (y0 + wy0) / 2, fz), r=0.06), box((2 * hw, y1 - wy1, 0.25), (0, (wy1 + y1) / 2, fz), r=0.06),
              box((0.5, wy1 - wy0, 0.25), (0, (wy0 + wy1) / 2, fz), r=0.06), box((0.5, wy1 - wy0, 0.25), (hw - 0.25, (wy0 + wy1) / 2, fz), r=0.06),
              box((0.5, wy1 - wy0, 0.25), (-hw + 0.25, (wy0 + wy1) / 2, fz), r=0.06),
              box((0.25, y1 - y0, 0.6), (hw - 0.12, (y0 + y1) / 2, fz + 0.2), r=0.06), box((0.25, y1 - y0, 0.6), (-hw + 0.12, (y0 + y1) / 2, fz + 0.2), r=0.06),
              box((2 * hw, 0.25, 0.6), (0, y0 + 0.12, fz + 0.2), r=0.06)]
    dpiece(H, "Cabin", "Body", merge(*walls), col="secondary", mat="metal", role="body", pri=0.95)
    gl = [box((hw - 0.75, wy1 - wy0 + 0.1, 0.08), (s * (hw / 2), (wy0 + wy1) / 2, fz), r=0.05) for s in (1, -1)]
    dpiece(H, "WindowGlass", "Body", merge(*gl), col=GLASS, mat="glass", tr=0.5, role="glass", pri=1.1)
    panels = [box((0.08, 1.6, 1.6), (s * (hw + 0.03), y0 + 2.2, 0.8), r=0.05) for s in (1, -1)] + [box((1.6, 0.9, 0.08), (0, y1 - 0.9, z1 + 0.03), r=0.05)]
    tank = cyl(0.9, 1.6, (0, y1 + 0.55, 0.9), axis=1, segs=16, bevel=0.2)
    dpiece(H, "CabinDetail", "Body", merge(*panels, tank), col="dark", mat="metal", role="detail", pri=1.6)
    dish = merge(tube([[1.6, y1 + 0.1, 1.6], [2.6, y1 + 1.6, 2.2]], 0.07, 5),
                 A.lathe([(0.0, 0.0), (0.08, 0.8), (0.25, 1.0), (0.3, 1.0), (0.14, 0.8), (0.05, 0.0)], axis=1, segs=16, pos=(2.7, y1 + 1.55, 2.25), rot=(30, 0, 0)))
    porch = merge(box((2.0, 0.12, 1.5), (0, 4.4, -4.5), r=0.03), tube([[-0.8, 4.3, -5.1], [-0.8, 0.5, -6.6]], 0.07, 5), tube([[0.8, 4.3, -5.1], [0.8, 0.5, -6.6]], 0.07, 5),
                  *[tube([[-0.8, y, -5.1 - (4.3 - y) * 0.39], [0.8, y, -5.1 - (4.3 - y) * 0.39]], 0.05, 4) for y in np.linspace(0.9, 3.9, 6)])
    dpiece(H, "Dish", "Body", merge(dish, porch), col="white", mat="metal", role="detail", pri=1.5)
    for a, nm in ((315, "GearFR"), (225, "GearFL"), (45, "GearBR"), (135, "GearBL")):
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        top = (3.8 * c, 3.4, 3.8 * s_)
        foot = np.array([6.4 * c, 0.3, 6.4 * s_])
        H.bone(nm, "Body", top)
        lm = merge(tube([top, foot], 0.18, 8), tube([[4.2 * c, 1.4, 4.2 * s_], foot * np.array([0.93, 1, 0.93]) + np.array([0, 0.9, 0])], 0.09, 6),
                   A.lathe([(0.0, 0.0), (0.0, 0.85), (0.22, 0.8), (0.32, 0.3), (0.34, 0.0)], axis=1, segs=14, pos=(foot[0], 0, foot[2])))
        dpiece(H, nm + "P", nm, lm, col="primary", mat="foil", role="limb", pri=1.2)
    dpiece(H, "Seat", "Body", A.pilot_seat(hip, w=1.8, floor_y=y0 + 0.25), col="dark", mat="cloth", role="detail", pri=1.2)
    dpiece(H, "Panel", "Body", merge(xform(box((4.2, 1.0, 0.6), (0, 0, 0), r=0.14), (0, hip[1] + 0.55, hip[2] - 2.15), (-15, 0, 0)), A.stick(hip, y0 + 0.25, dz=-1.8, h=1.0)),
           col="darker", role="detail", pri=1.3)
    for i, x in enumerate((-1.0, 1.0)):
        H.prim(f"Screen{i + 1}", "Body", "Block", (1.1, 0.6, 0.05), (x, hip[1] + 0.6, hip[2] - 1.82), rot=(math.radians(-15), 0, 0), col=SCREEN, glow=True, role="light", pri=2.0)
    ride(H, hip, (0.0, -7.6), -6.6, 6.6, hip[1] + 3.9, exhaust=(0, 0.6, 0))
    A.craft_clips(H, 13.0, hover=True, attack="ram", bank=0.08)
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
