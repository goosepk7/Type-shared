"""Aircraft and magic rides (flying mounts): propeller plane, biplane, jet (fighter), jumbo jet, airplane (airliner),
private jet, glider, seaplane, helicopter, hot air balloon, blimp, flying carpet, broomstick, cloud surfboard, sleigh,
chariot of fire.

Fuselages are lofted superellipse stations (airsea_kit.Fus), wings / fins are airfoil blades, canopies are separate
glass pieces, propellers and rotors sit on their own bones and spin in every clip. Gait "fly" (banking S-turns,
pitch, propeller spin) or "hover" (helicopter, balloon, blimp). Model space: -Z is the nose, wheels on y = 0.
"""
import math

import numpy as np

from sdf import ellipsoid, sphere as ssphere, capsule, round_cone, tube as stube, round_box, plane, union  # noqa: F401
from kit import Hero, hero
import airsea_kit as A
from airsea_kit import Fus, dpiece, dmpiece, box, cyl, rev, tube, merge, xform, mirror, sphere, wheel, window_row, band, SplitFus, zrange, gear_leg

TAU = 2 * math.pi
TINT = [0.13, 0.17, 0.22]
CANOPY = [0.55, 0.75, 0.88]
B = {"cat": ["Vehicle", "Machine", "Object"]}


def P(hid, gait="fly", tags=("vehicle", "aircraft")):
    return Hero(hid, plan="Vehicle", gait=gait, tags=list(tags))


def cheat(fus, z0, z1, yoff, r=0.07, n=14, out=0.03):
    """Cheat line / stripe hugging both sides of a fuselage at height yc + yoff (fraction of the half height)."""
    pts = []
    for z in np.linspace(z0, z1, n):
        w, h, yc, p = fus.at(z)
        y = yc + yoff * h
        pts.append([fus.x_at(z, y) + out - r * 0.6, y, z])
    m = tube(pts, r, 6)
    return merge(m, mirror(m))


def common(H, seat_pos, seat_size, nose_z, tail_z, top_y, muzzle=None, exhaust=None):
    A.mount(H, "Seat", seat_pos, seat_size)
    H.socket("head", (0, top_y, seat_pos[2]), "Body")
    H.socket("mouth", (0, seat_pos[1] - 0.3, nose_z), "Body")
    H.socket("exhaust", exhaust or (0, seat_pos[1] - 0.5, tail_z), "Body")
    if muzzle is not None:
        H.socket("muzzle", muzzle, "Body")


def bucket_seat(pos, w=0.8, col_back=True, rake=-14):
    x, y, z = pos
    return merge(box((w, 0.22, 0.8), (x, y, z), r=0.08), box((w, 0.9, 0.18), (x, y + 0.45, z + 0.42), r=0.08, rot=(rake, 0, 0)))


def canopy(z0, z1, r, y, x=0.0, sx=1.0, sy=1.0, segs=16):
    """Teardrop bubble canopy along z (front at z0)."""
    L = z1 - z0
    pts = [(z0, 0), (z0 + L * 0.12, r * 0.55), (z0 + L * 0.4, r), (z0 + L * 0.75, r * 0.85), (z1, 0)]
    m = rev(pts, axis=2, segs=segs, spline=3)
    m = xform(m, (x, y, 0), (0, 0, 0), (sx, sy, 1))
    return m


def nacelle(pos, r, L, fan=True):
    """Jet engine pod along z (intake at the front)."""
    x, y, z = pos
    shell = A.lathe([(z - L / 2, r * 0.82), (z - L / 2 - 0.05, r * 0.92), (z - L / 2 + 0.15, r), (z + L * 0.3, r * 0.97), (z + L / 2, r * 0.62),
                     (z + L / 2, r * 0.45), (z + L * 0.2, r * 0.45), (z - L / 2 + 0.2, r * 0.8)], axis=2, segs=18, pos=(x, y, 0), closed=True)
    inner = A.lathe([(z - L / 2 + 0.3, 0.0), (z - L / 2 + 0.3, r * 0.82), (z - L / 2 + 0.4, r * 0.82), (z - L / 2 + 0.4, 0.0)], axis=2, segs=18, pos=(x, y, 0))
    cone = rev([(z - L / 2 + 0.05, 0.0), (z - L / 2 + 0.2, r * 0.25), (z - L / 2 + 0.38, r * 0.3), (z - L / 2 + 0.42, 0)], axis=2, segs=12, pos=(x, y, 0))
    return shell, merge(inner, cone)


# ================================================================================================ propeller planes
def cockpit(H, F, hip, floor_y, panel_z, panel_w, panel_top, ctrl="stick", seat_w=1.9, screens=2, col="darker", side_console=True):
    """Floor, pilot seat, instrument panel (glare shield + glowing screens), control stick / yoke, rudder pedals
    and a throttle for a single pilot whose HIP point is `hip`."""
    x, y, z = hip
    dpiece(H, "Seat", "Body", A.pilot_seat(hip, w=seat_w, floor_y=floor_y), col="dark", mat="cloth", role="detail", pri=1.2)
    pz0 = panel_z - 0.75
    pb = floor_y + 0.6
    panel = merge(xform(box((panel_w, panel_top - pb, 0.75), (0, 0, 0), r=0.15, seg=1), (x, (panel_top + pb) / 2, panel_z - 0.37), (-8, 0, 0)),
                  xform(box((panel_w * 0.96, 0.16, 1.15), (0, 0, 0), r=0.07), (x, panel_top + 0.08, panel_z - 0.45), (-5, 0, 0)))
    dpiece(H, "Panel", "Body", panel, col=col, role="detail", pri=1.3)
    xs = [x] if screens == 1 else list(np.linspace(x - panel_w * 0.24, x + panel_w * 0.24, screens))
    for i, sx in enumerate(xs):
        H.prim(f"Screen{i + 1}", "Body", "Block", (min(1.0, panel_w / (screens + 1.2)), 0.62, 0.06), (sx, panel_top - 0.55, panel_z + 0.035),
               rot=(math.radians(-8), 0, 0), col=SCREEN, glow=True, role="light", pri=2.0)
    ms = []
    if ctrl == "stick":
        ms.append(A.stick(hip, floor_y, dz=-1.85, h=1.05))
    else:
        hn, cl = A.yoke(hip)
        ms += [hn, cl]
    for sx in (x - 0.5, x + 0.5):
        ms.append(xform(box((0.42, 0.62, 0.12), (0, 0, 0), r=0.04), (sx, floor_y + 0.42, z - 2.0), (-38, 0, 0)))
    if side_console:
        ms.append(box((0.35, 0.5, 1.2), (x - seat_w / 2 - 0.3, y + 0.25, z - 0.9), r=0.08))
        ms.append(tube([[x - seat_w / 2 - 0.3, y + 0.45, z - 0.9], [x - seat_w / 2 - 0.3, y + 0.95, z - 1.15]], 0.06, 6))
        ms.append(sphere(0.13, (x - seat_w / 2 - 0.3, y + 1.0, z - 1.17), segs=8))
    dpiece(H, "Controls", "Body", merge(*ms), col="gunmetal", mat="metal", role="detail", pri=1.6)
    dpiece(H, "Floor", "Body", F.floor(z - 2.6, z + 1.1, floor_y), col="darker", role="detail", pri=1.6)


def prop_gear(H, F, nose, mains, wheel_r=(0.7, 0.85), pant=True, col="secondary"):
    """Tricycle gear on bones: GearF (nose leg) and GearR / GearL (mains), each pivoting at the strut top (the game
    folds them about X). nose / mains: ((top), (axle)) with the right main given (+X)."""
    (nt, na), (mt, ma) = nose, mains
    H.bone("GearF", "Body", nt)
    s, t, p = gear_leg(nt, na, wheel_r[0], 0.5, pant=pant)
    dpiece(H, "GearFP", "GearF", merge(s, t) if p is None else merge(s, t), col="metal", mat="metal", role="limb", pri=1.3)
    if p is not None:
        dpiece(H, "GearFPant", "GearF", p, col=col, role="detail", pri=1.5)
    H.mbone("Gear#", "Body", mt)
    s, t, p = gear_leg(mt, ma, wheel_r[1], 0.62, pant=pant)
    dmpiece(H, "GearP#", "Gear#", merge(s, t), col="metal", mat="metal", role="limb", pri=1.2)
    if p is not None:
        dmpiece(H, "GearPant#", "Gear#", p, col=col, role="detail", pri=1.4)


@hero("propeller plane", "aircraft")
def propeller_plane():
    """Single-engine low-wing sport plane at real game scale (22 studs long, 30 stud span): bubble canopy over a
    one-seat cockpit (stick, panel, pedals), 3-blade prop on bone Prop (spins about Z), tricycle gear on GearF /
    GearR / GearL."""
    H = P("propeller plane")
    H.preview = {"primary": "#F4F4F2", "secondary": "#C62828", "dark": "#2B2F36"}
    hip = (0.0, 4.25, -0.9)
    F = SplitFus([(-10.95, 0.0, 0.0, 0.0, 4.75), (-10.7, 1.15, 1.2, 1.05, 4.75), (-9.4, 1.8, 1.85, 1.5, 4.8), (-6.8, 2.25, 2.2, 1.75, 4.9),
                  (-4.4, 2.45, 2.3, 1.95, 4.9), (-3.0, 2.5, 2.3, 2.75, 4.9), (-1.4, 2.5, 2.3, 3.2, 4.9), (0.3, 2.45, 2.25, 3.15, 4.92),
                  (2.2, 2.25, 2.05, 2.35, 4.95), (3.4, 2.05, 1.9, 1.85, 5.0), (6.5, 1.35, 1.35, 1.3, 5.2), (9.8, 0.75, 0.75, 0.82, 5.45),
                  (11.0, 0.32, 0.38, 0.45, 5.55), (11.2, 0.0, 0.0, 0.0, 5.56)], n=36, p_lo=2.5, p_up=2.3)
    H.body((0, 4.9, 0))
    zg0, zg1, zc = -4.3, 2.6, -7.4
    zs = zrange(-10.95, 11.2, 0.55, (zg0, zg1, zc))
    zs = sorted(set(zs + list(np.linspace(-10.95, -10.2, 5))))
    zc_ = [z for z in zs if z >= zc]
    belly = lambda Q: 0.82 + 0.18 * np.clip((Q[:, 1] - 2.6) / 2.0, 0, 1)
    dpiece(H, "Hull", "Body", merge(F.lower(zc_, n=30), F.upper([z for z in zc_ if z <= zg0], n=24), F.upper([z for z in zc_ if z >= zg1], n=24)),
           col="primary", mat="hard", fallback="Ellipsoid", pattern=belly)
    zcw = [z for z in zs if z <= zc]
    dpiece(H, "Cowl", "Body", F.shell(zcw, n=30), col="secondary", mat="hard", role="body", pri=1.1)
    dpiece(H, "CanopyGlass", "Body", F.upper([z for z in zs if zg0 <= z <= zg1], th=0.08, n=28), col=GLASS, mat="glass", tr=0.5, role="glass", pri=1.1)
    frame = merge(F.ring(zg0, r=0.13, out=0.03), F.ring(zg0 + 1.1, r=0.07, out=0.04), F.ring(zg1, r=0.12, out=0.03),
                  F.line(np.linspace(zg0, zg1, 12), yfn=F.yc, r=0.09, out=0.04))
    dpiece(H, "CanopyFrame", "Body", frame, col="dark", role="detail", pri=1.3)
    seams = merge(F.ring(zc, r=0.05, ylo="full", out=0.01), F.ring(6.0, r=0.04, ylo="full", out=0.0, n=24))
    dpiece(H, "Stripe", "Body", merge(F.line(np.linspace(-7.2, 10.6, 20), yfn=lambda z: F.yc(z) - 0.75, r=0.14, out=0.05), seams), col="secondary", role="detail", pri=1.4)

    # ---- wings (low, dihedral), tips with nav lights, flap / aileron lines, tail
    wy, wz, root_x = 2.8, -4.6, 1.9
    wing = A.wing(13.1, 4.4, 2.3, sweep=0.55, thick=0.62, dihedral=5, pos=(root_x, wy, wz), nt=10, nu=8, tip_round=0.35)
    dpiece(H, "Wings", "Body", merge(wing, mirror(wing), box((3.9, 0.5, 3.8), (0, 2.6, wz + 1.9), r=0.22)), col="primary", mat="hard", role="wing")
    dh = math.tan(math.radians(5))
    tipx = root_x + 13.1
    tips = A.wing(0.6, 2.35, 2.1, sweep=0.1, thick=0.24, pos=(tipx - 0.1, wy + 13.0 * dh, wz + 0.5))
    lines = []
    for x0, x1 in ((2.6, 8.0), (8.4, 14.2)):
        zt0 = wz + 4.4 + (2.3 - 4.4) * (x0 - root_x) / 13.1 + 0.55 * (x0 - root_x) / 13.1
        zt1 = wz + 4.4 + (2.3 - 4.4) * (x1 - root_x) / 13.1 + 0.55 * (x1 - root_x) / 13.1
        lines.append(tube([[x0, wy + (x0 - root_x) * dh + 0.12, zt0 - 0.85], [x1, wy + (x1 - root_x) * dh + 0.1, zt1 - 0.75]], 0.04, 4))
        lines.append(tube([[x0, wy + (x0 - root_x) * dh + 0.12, zt0 - 0.85], [x0, wy + (x0 - root_x) * dh + 0.06, zt0 - 0.1]], 0.04, 4))
    lm = merge(*lines)
    dpiece(H, "WingTips", "Body", merge(tips, mirror(tips), lm, mirror(lm)), col="secondary", role="detail", pri=1.5)
    H.prim("NavLightR", "Body", "Ball", (0.28, 0.24, 0.32), (tipx + 0.55, wy + 13.0 * dh + 0.05, wz + 0.75), col=[0.2, 0.95, 0.35], glow=True, role="light", pri=2.4)
    H.prim("NavLightL", "Body", "Ball", (0.28, 0.24, 0.32), (-tipx - 0.55, wy + 13.0 * dh + 0.05, wz + 0.75), col="red", glow=True, role="light", pri=2.4)
    hs = A.wing(4.4, 2.5, 1.45, sweep=0.55, thick=0.3, pos=(0.5, 5.45, 8.3), tip_round=0.4)
    dpiece(H, "Tail", "Body", merge(hs, mirror(hs)), col="primary", mat="hard", role="wing")
    fin = A.fin(4.2, 3.5, 1.7, 2.1, thick=0.32, pos=(0, 5.9, 7.6))
    dors = A.fin(0.9, 3.0, 0.4, 2.6, thick=0.26, pos=(0, 6.0, 5.2))
    dpiece(H, "Fin", "Body", merge(fin, dors), col="secondary", mat="hard", role="detail", pri=1.2)
    H.prim("Beacon", "Body", "Ball", (0.3, 0.22, 0.3), (0, 10.12, 10.6), col="red", glow=True, role="light", pri=2.4)

    # ---- engine: spinner + 3-blade prop on bone Prop, exhausts, intake, cooling louvres
    pz, py = -11.0, 4.75
    H.bone("Prop", "Body", (0, py, pz))
    pr = A.prop(3, 4.15, 0.62, axis="z", pos=(0, py, pz), thick=0.11, pitch=18)
    sp = rev([(pz - 1.25, 0.0), (pz - 1.0, 0.42), (pz - 0.45, 0.82), (pz + 0.15, 0.98), (pz + 0.3, 0.0)], axis=2, segs=20, pos=(0, py, 0))
    dpiece(H, "PropP", "Prop", pr, col="dark", mat="hard", role="detail", pri=1.0)
    dpiece(H, "Spinner", "Prop", sp, col="secondary", mat="hard", role="detail", pri=1.1)
    ex = []
    for z in (-9.3, -8.7, -8.1):
        x = F.x_at(z, 3.6)
        ex.append(cyl(0.17, 0.7, (x + 0.2, 3.55, z), axis=0, segs=10, rot=(0, 0, -20)))
    em = merge(*ex)
    intake = merge(rev([(-0.6, 0.0), (-0.55, 0.62), (0.6, 0.55), (0.9, 0.0)], axis=2, segs=14, pos=(0, 2.85, -9.4), scale=(1.4, 0.7, 1)),
                   box((1.3, 0.45, 0.1), (0, 2.95, -10.0), r=0.08))
    louv = merge(*[box((0.06, 0.12, 0.9), (F.x_at(-8.0, y) + 0.02, y, -8.0), r=0.02) for y in (5.4, 5.7, 6.0)])
    dpiece(H, "Exhaust", "Body", merge(em, mirror(em), intake, louv, mirror(louv)), col="gunmetal", mat="metal", role="detail", pri=1.8)

    # ---- cockpit + gear
    cockpit(H, F, hip, floor_y=2.95, panel_z=-2.95, panel_w=3.8, panel_top=5.55)
    prop_gear(H, F, ((0, 3.0, -8.0), (0, 0.7, -8.2)), ((1.6, 3.0, -2.6), (3.4, 0.85, -2.2)))
    ant = merge(tube([[0, F.top(4.8) - 0.1, 4.8], [0, F.top(4.8) + 0.9, 5.4]], 0.04, 4), tube([[3.2, wy + 0.1 - 0.35, wz + 0.4], [3.2, wy - 0.45, wz - 1.2]], 0.05, 6))
    dpiece(H, "Antenna", "Body", ant, col="dark", role="detail", pri=2.6)
    ride(H, hip, (-4.0, 1.0), -12.3, 11.3, hip[1] + 3.8, exhaust=(0.9, 3.55, -8.7))
    A.craft_clips(H, 22.0, attack="dive", bank=0.35)
    return H


@hero("seaplane", "aircraft")
def seaplane():
    """High-wing bush plane on twin floats at real game scale (22 studs long, 30 stud span): the rider flies from
    a cabin with a wrap-around windscreen and side windows under the wing (yoke, panel), 3-blade prop on bone Prop
    (spins about Z), floats on struts (fixed, no gear)."""
    H = P("seaplane")
    H.preview = {"primary": "#FFC107", "secondary": "#1565C0", "dark": "#2B2F36"}
    yc = 5.45
    hip = (0.0, 5.05, -1.6)
    F = SplitFus([(-10.9, 0.0, 0.0, 0.0, 5.3), (-10.65, 1.1, 1.15, 1.05, 5.3), (-9.3, 1.75, 1.8, 1.55, 5.35), (-6.8, 2.3, 2.05, 1.95, yc),
                  (-5.0, 2.45, 2.05, 2.7, yc), (-3.0, 2.5, 2.05, 3.45, yc), (0.5, 2.5, 2.0, 3.45, yc), (2.4, 2.25, 1.85, 2.4, yc + 0.05),
                  (5.5, 1.45, 1.35, 1.35, yc + 0.25), (9.6, 0.7, 0.72, 0.8, yc + 0.5), (10.9, 0.3, 0.36, 0.4, yc + 0.55), (11.1, 0.0, 0.0, 0.0, yc + 0.55)],
                 n=34, p_lo=2.6, p_up=3.2)
    H.body((0, yc, 0))
    zc, zw0, zw1 = -7.4, -5.6, 1.0
    ylo, yhi = hip[1] + 0.85, hip[1] + 2.9
    zs = zrange(-10.9, 11.1, 0.55, (zc, zw0, zw1))
    zs = sorted(set(zs + list(np.linspace(-10.9, -10.2, 4))))
    zh = [z for z in zs if z >= zc]
    zg = [z for z in zh if zw0 <= z <= zw1]
    belly = lambda Q: 0.84 + 0.16 * np.clip((Q[:, 1] - 3.4) / 2.0, 0, 1)
    hull = [F.lower(zh, n=26), F.upper([z for z in zh if z <= zw0], n=22), F.upper([z for z in zh if z >= zw1], n=22),
            band(F.up, zg, ylo=F.yc, yhi=ylo, side=True, th=0.15, n=5), band(F.up, zg, ylo=yhi, th=0.15, n=12)]
    sd = hull.pop(3)
    dpiece(H, "Hull", "Body", merge(*hull, sd, mirror(sd)), col="primary", mat="hard", fallback="Ellipsoid", pattern=belly)
    dpiece(H, "Cowl", "Body", F.shell([z for z in zs if z <= zc], n=26), col="secondary", mat="hard", role="body", pri=1.1)
    gl = band(F.up, zg, ylo=ylo, yhi=yhi, side=True, th=0.08, n=8)
    dpiece(H, "WindowGlass", "Body", merge(gl, mirror(gl)), col=GLASS, mat="glass", tr=0.5, role="glass", pri=1.1)
    posts = []
    for z in (zw0 + 1.7, zw0 + 3.9):
        a0, a1 = A.fus_angle(F.up, z, ylo), A.fus_angle(F.up, z, yhi)
        posts.append(tube([A.fus_point(F.up, z, a, -0.04) for a in np.linspace(a0, a1, 5)], 0.12, 6))
    pm = merge(*posts, F.line(np.linspace(zw0, zw1, 10), ylo, r=0.1, out=0.04, both=False), F.line(np.linspace(zw0 + 1.2, zw1, 8), yhi, r=0.1, out=0.04, both=False))
    dpiece(H, "WindowFrames", "Body", merge(pm, mirror(pm)), col="dark", role="detail", pri=1.3)
    dpiece(H, "Stripe", "Body", merge(F.line(np.linspace(-7.2, 10.6, 20), yfn=lambda z: F.yc(z) - 0.7, r=0.15, out=0.05), F.ring(zc, r=0.05, ylo="full", out=0.01)),
           col="secondary", role="detail", pri=1.4)
    # ---- high wing on the cabin roof, lift struts, tail
    wy = F.top(-2.0) + 0.05
    wing = A.wing(13.3, 3.9, 2.9, sweep=0.2, thick=0.5, dihedral=1.5, pos=(0.3, wy, -4.4), nt=10, nu=8, tip_round=0.4)
    ctr = box((1.4, 0.36, 3.9), (0, wy + 0.05, -2.45), r=0.16)
    dpiece(H, "Wings", "Body", merge(wing, mirror(wing), ctr), col="primary", mat="hard", role="wing")
    tips = A.wing(0.55, 2.95, 2.7, sweep=0.1, thick=0.24, pos=(13.5, wy + 13.3 * math.tan(math.radians(1.5)), -4.2))
    lift = []
    for zz in (-3.9, -2.0):
        lift.append(tube([[F.x_at(-2.8, 4.2) - 0.1, 4.2, -2.8], [6.0, wy + 6.0 * math.tan(math.radians(1.5)) - 0.15, zz]], 0.11, 8))
    lm = merge(tips, *lift)
    dpiece(H, "WingTips", "Body", merge(lm, mirror(lm)), col="secondary", role="detail", pri=1.4)
    H.prim("NavLightR", "Body", "Ball", (0.28, 0.24, 0.32), (14.1, wy + 0.4, -3.0), col=[0.2, 0.95, 0.35], glow=True, role="light", pri=2.4)
    H.prim("NavLightL", "Body", "Ball", (0.28, 0.24, 0.32), (-14.1, wy + 0.4, -3.0), col="red", glow=True, role="light", pri=2.4)
    hs = A.wing(4.4, 2.5, 1.5, sweep=0.5, thick=0.3, pos=(0.4, yc + 0.5, 8.3), tip_round=0.4)
    fin = A.fin(4.3, 3.4, 1.7, 2.0, thick=0.32, pos=(0, yc + 0.95, 7.5))
    dpiece(H, "Tail", "Body", merge(hs, mirror(hs)), col="primary", mat="hard", role="wing")
    dpiece(H, "Fin", "Body", merge(fin, A.fin(0.9, 3.0, 0.4, 2.6, thick=0.26, pos=(0, yc + 1.0, 5.2))), col="secondary", mat="hard", role="detail", pri=1.2)
    # ---- engine + prop
    pz, py = -11.0, 5.3
    H.bone("Prop", "Body", (0, py, pz))
    dpiece(H, "PropP", "Prop", A.prop(3, 4.0, 0.6, axis="z", pos=(0, py, pz), thick=0.11, pitch=18), col="dark", mat="hard", role="detail", pri=1.0)
    dpiece(H, "Spinner", "Prop", rev([(pz - 1.2, 0.0), (pz - 0.95, 0.42), (pz - 0.4, 0.8), (pz + 0.15, 0.95), (pz + 0.3, 0.0)], axis=2, segs=20, pos=(0, py, 0)),
           col="secondary", mat="hard", role="detail", pri=1.1)
    ex = merge(*[cyl(0.17, 0.7, (F.x_at(z, 4.1) + 0.2, 4.1, z), axis=0, segs=10, rot=(0, 0, -20)) for z in (-9.2, -8.5)])
    dpiece(H, "Exhaust", "Body", merge(ex, mirror(ex)), col="gunmetal", mat="metal", role="detail", pri=1.8)
    # ---- floats + struts (they sit on the water at y = 0)
    fl = Fus([(-9.6, 0.0, 0.0, 1.05), (-9.2, 0.45, 0.32, 1.1), (-8.0, 0.78, 0.62, 0.95), (-5.0, 0.85, 0.78, 0.82), (-0.6, 0.85, 0.8, 0.8),
              (0.0, 0.8, 0.72, 0.86), (4.5, 0.55, 0.5, 1.0), (7.0, 0.32, 0.3, 1.12), (7.6, 0.0, 0.0, 1.18)], n=18, p=2.8, smooth=True)
    fm = xform(fl.mesh(samples=np.linspace(-9.6, 7.6, 22)), (3.4, 0, 0))
    keel = tube([[3.4, 0.12, -8.0], [3.4, 0.04, -0.6], [3.4, 0.2, 0.2], [3.4, 0.55, 6.5]], 0.09, 6)
    dpiece(H, "Floats", "Body", merge(fm, mirror(fm)), col="secondary", mat="hard", role="limb", pri=1.0)
    st = [tube([[3.4, 1.5, -6.0], [F.x_at(-6.2, 4.0) - 0.2, 4.0, -6.2]], 0.12, 8), tube([[3.4, 1.5, -1.4], [F.x_at(-1.0, 4.0) - 0.2, 4.0, -1.0]], 0.12, 8),
          tube([[3.4, 1.5, -6.0], [0.9, F.bottom(-1.2) + 0.2, -1.2]], 0.08, 6), keel,
          box((0.9, 0.12, 1.4), (3.4, 1.62, -3.6), r=0.05)]
    sm = merge(*st)
    dpiece(H, "Struts", "Body", merge(sm, mirror(sm), tube([[3.4, 1.4, -6.0], [-3.4, 1.4, -6.0]], 0.08, 6), tube([[3.4, 1.4, -1.4], [-3.4, 1.4, -1.4]], 0.08, 6)),
           col="metal", mat="metal", role="detail", pri=1.3)
    cockpit(H, F, hip, floor_y=hip[1] - 1.25, panel_z=hip[2] - 2.05, panel_w=4.0, panel_top=hip[1] + 1.15, ctrl="yoke", screens=2)
    H.prim("Beacon", "Body", "Ball", (0.3, 0.22, 0.3), (0, yc + 0.95 + 4.3 + 0.12, 9.9), col="red", glow=True, role="light", pri=2.4)
    ride(H, hip, (-5.0, -1.6), -12.2, 11.2, hip[1] + 3.9, exhaust=(1.0, 4.1, -8.8))
    A.craft_clips(H, 22.0, attack="dive", bank=0.3)
    return H


# ================================================================================================ biplane
@hero("biplane", "aircraft")
def biplane():
    """Open-cockpit biplane at real game scale (21 studs long, 26 stud span): the rider sits in the rear cockpit
    behind a small windscreen (torso inside the fuselage, head above the leather coaming), radial engine with a
    2-blade wooden prop on bone Prop (spins about Z), N-struts and bracing wires, fixed taildragger gear."""
    H = P("biplane")
    H.preview = {"primary": "#C62828", "secondary": "#F2E3B3", "dark": "#2B2F36"}
    hip = (0.0, 4.05, 1.0)
    yc = 4.6
    F = SplitFus([(-9.6, 1.85, 1.85, 1.6, 4.55), (-8.6, 2.15, 2.1, 1.75, 4.58), (-5.5, 2.45, 2.2, 1.75, yc), (-1.5, 2.55, 2.2, 1.7, yc),
                  (2.2, 2.45, 2.05, 1.6, 4.65), (5.5, 1.65, 1.5, 1.2, 4.6), (9.6, 0.55, 0.6, 0.55, 4.3), (10.6, 0.25, 0.3, 0.3, 4.25), (10.75, 0.0, 0.0, 0.0, 4.25)],
                 n=32, p_lo=3.0, p_up=2.4)
    H.body((0, yc, 0))
    zo0, zo1, coam = -1.0, 2.3, hip[1] + 1.35
    zs = zrange(-9.6, 10.75, 0.6, (zo0, zo1, -7.6))
    fab = lambda Q: 0.88 + 0.12 * np.abs(np.cos(Q[:, 2] * 3.1))  # fabric over stringers
    zh = [z for z in zs if z >= -7.6]
    hull = [F.lower(zh, n=26), F.upper([z for z in zh if z <= zo0], n=22), F.upper([z for z in zh if z >= zo1], n=22)]
    sides = band(F.up, [z for z in zs if zo0 <= z <= zo1], ylo=F.yc, yhi=coam, side=True, th=0.15, n=6)
    dpiece(H, "Hull", "Body", merge(*hull, sides, mirror(sides)), col="primary", mat="cloth", fallback="Block", pattern=fab)
    dpiece(H, "Cowl", "Body", F.shell([z for z in zs if z <= -7.6], n=26), col="metal", mat="metal", role="body", pri=1.1)
    rim = [F.point(z, coam, 0.04) for z in np.linspace(zo0, zo1, 8)]
    a_c = A.fus_angle(F.up, zo1, coam)
    rim += [A.fus_point(F.up, zo1, a, -0.04) for a in np.linspace(a_c, math.pi - a_c, 9)[1:]]
    rim += [F.point(z, coam, 0.04, side=-1) for z in np.linspace(zo1, zo0, 8)[1:]]
    a_c = A.fus_angle(F.up, zo0, coam)
    rim += [A.fus_point(F.up, zo0, a, -0.04) for a in np.linspace(math.pi - a_c, a_c, 9)[1:]]
    dpiece(H, "Coaming", "Body", tube(rim, 0.15, 8), col="leather", mat="cloth", role="detail", pri=1.2)
    ws = A.quad_sheet((-1.1, coam - 0.05, zo0 - 0.15), (1.1, coam - 0.05, zo0 - 0.15), (-0.95, coam + 1.25, zo0 + 0.15), (0.95, coam + 1.25, zo0 + 0.15), nt=4, nu=3, bulge=(0, 0, -0.18), thick=0.03)
    dpiece(H, "WindscreenGlass", "Body", ws, col=GLASS, mat="glass", tr=0.5, role="glass", pri=1.3)
    # ---- wings: upper over the front cockpit, lower through the belly; N-struts, cabane, wires
    uy, ly = 8.55, 2.75
    uw = A.wing(12.6, 4.3, 4.0, sweep=0.0, thick=0.42, dihedral=0.5, pos=(0.4, uy, -3.9), nt=9, nu=8, tip_round=0.55)
    lw = A.wing(11.4, 3.9, 3.6, sweep=0.0, thick=0.4, dihedral=3.0, pos=(1.6, ly, -3.0), nt=9, nu=8, tip_round=0.55)
    ctr = box((1.0, 0.36, 4.1), (0, uy, -1.85), r=0.15)
    dpiece(H, "Wings", "Body", merge(uw, mirror(uw), lw, mirror(lw), ctr), col="primary", mat="cloth", role="wing", pattern=lambda Q: 0.9 + 0.1 * np.abs(np.cos(np.abs(Q[:, 0]) * 2.4)))
    st = []
    sx = 8.2
    for x in (sx,):
        yl, yu = ly + (x - 1.6) * math.tan(math.radians(3)), uy + x * math.tan(math.radians(0.5))
        st += [tube([[x, yl + 0.1, -2.4], [x, yu - 0.1, -3.2]], 0.12, 8), tube([[x, yl + 0.1, 0.2], [x, yu - 0.1, -0.6]], 0.12, 8),
               tube([[x, yl + 0.1, -2.4], [x, yu - 0.1, -0.6]], 0.09, 6)]
    for z in (-3.2, -0.9):
        st.append(tube([[0.7, F.top(z) - 0.1, z + 0.2], [0.9, uy - 0.1, z]], 0.1, 6))
    stm = merge(*st)
    wires = merge(tube([[sx, uy, -1.9], [1.0, ly + 0.2, -1.6]], 0.03, 4), tube([[sx, ly + 0.4, -1.4], [1.0, uy - 0.1, -2.0]], 0.03, 4),
                  tube([[sx - 0.1, uy - 0.1, -0.6], [2.0, ly + 0.15, 0.2]], 0.03, 4))
    dpiece(H, "Struts", "Body", merge(stm, mirror(stm), wires, mirror(wires)), col="wood", mat="wood", role="detail", pri=1.3)
    ail = []
    for y0, x0, x1, ztr in ((uy + 0.18, 7.0, 12.4, 0.1), (ly + 0.2 + 0.4, 7.5, 12.4, 0.6)):
        ail.append(tube([[x0, y0, ztr - 1.0], [x1, y0 + 0.05, ztr - 1.0]], 0.04, 4))
    am = merge(*ail)
    dpiece(H, "WingTrim", "Body", merge(am, mirror(am)), col="secondary", role="detail", pri=2.0)
    # ---- tail: stabiliser, fin + rudder
    hs = A.wing(3.8, 2.4, 1.6, sweep=0.3, thick=0.26, pos=(0.3, 4.45, 7.7), tip_round=0.6)
    fin = A.fin(3.6, 2.6, 1.4, 1.3, thick=0.28, pos=(0, 4.85, 7.6))
    dpiece(H, "Tail", "Body", merge(hs, mirror(hs)), col="primary", mat="cloth", role="wing")
    dpiece(H, "Fin", "Body", fin, col="secondary", mat="cloth", role="detail", pri=1.2)
    # ---- radial engine + wooden prop on bone Prop
    ez = -9.7
    cyls = [xform(merge(cyl(0.38, 1.0, (0, 0, 0), axis=0, segs=10), *[cyl(0.46, 0.07, (dx, 0, 0), axis=0, segs=10) for dx in (-0.25, -0.05, 0.15)]),
                  (1.55 * math.cos(a), yc - 0.05 + 1.55 * math.sin(a), ez - 0.15), (0, 0, math.degrees(a))) for a in np.linspace(0, TAU, 9, endpoint=False)]
    ring = A.lathe([(ez - 0.55, 2.0), (ez + 0.6, 2.15), (ez + 0.6, 1.95), (ez - 0.45, 1.85)], axis=2, segs=28, closed=True, pos=(0, yc - 0.05, 0))
    crank = cyl(0.9, 0.6, (0, yc - 0.05, ez - 0.1), axis=2, segs=16, bevel=0.15)
    dpiece(H, "Engine", "Body", merge(*cyls, crank), col="gunmetal", mat="metal", role="detail", pri=1.2)
    dpiece(H, "CowlRing", "Body", ring, col="secondary", mat="metal", role="detail", pri=1.2)
    H.bone("Prop", "Body", (0, yc - 0.05, ez - 0.75))
    pr = A.prop(2, 4.0, 0.55, axis="z", pos=(0, yc - 0.05, ez - 0.75), thick=0.1, pitch=15, hub=(0.32, 0.6))
    dpiece(H, "PropP", "Prop", merge(pr, rev([(ez - 1.35, 0.0), (ez - 1.2, 0.2), (ez - 0.9, 0.3), (ez - 0.6, 0.0)], axis=2, segs=10, pos=(0, yc - 0.05, 0))),
           col="wood", mat="wood", role="detail", pri=1.0)
    ex = merge(tube([[1.5, yc - 1.3, -9.4], [1.95, 3.2, -8.0], [2.0, 3.0, -4.5]], 0.14, 8))
    dpiece(H, "Exhaust", "Body", merge(ex, mirror(ex)), col="gunmetal", mat="metal", role="detail", pri=1.9)
    # ---- fixed taildragger gear (spoked wheels behind hub discs), tail skid
    g = []
    for s in (1, -1):
        ax_ = (s * 2.6, 1.25, -3.6)
        g += [tube([[s * 0.9, F.bottom(-4.6) + 0.2, -4.6], ax_], 0.12, 8), tube([[s * 0.9, F.bottom(-2.4) + 0.2, -2.4], ax_], 0.12, 8)]
    g.append(cyl(0.1, 5.6, (0, 1.25, -3.6), axis=0, segs=8))
    g.append(tube([[0, F.bottom(8.3) + 0.15, 8.3], [0, 1.6, 9.1], [0, 0.62, 9.9]], 0.15, 8))
    g.append(box((0.5, 0.12, 0.8), (0, 0.62, 10.0), r=0.04))
    tyres = [wheel(1.25, 0.55, (s * 2.75, 1.25, -3.6), axis=0, segs=20) for s in (1, -1)]
    hubs = [cyl(0.85, 0.62, (s * 2.75, 1.25, -3.6), axis=0, segs=16, bevel=0.2) for s in (1, -1)]
    dpiece(H, "Gear", "Body", merge(*g, *hubs), col="secondary", mat="metal", role="limb", pri=1.1)
    dpiece(H, "Tyres", "Body", merge(*tyres, A.wheel(0.36, 0.28, (0, 0.36, 10.15), axis=0)), col="tyre", mat="rubber", role="detail", pri=1.2)
    # ---- open cockpit interior: seat, panel, stick, front (empty) cockpit coaming
    dpiece(H, "Seat", "Body", A.pilot_seat(hip, w=1.8, floor_y=2.75, back_h=2.0), col="leather", mat="cloth", role="detail", pri=1.2)
    panel = xform(box((3.4, 1.0, 0.4), (0, 0, 0), r=0.12), (0, coam - 0.25, hip[2] - 2.15), (-10, 0, 0))
    dpiece(H, "Panel", "Body", merge(panel, A.stick(hip, 2.75, dz=-1.85, h=1.0), F.floor(hip[2] - 2.6, hip[2] + 1.0, 2.75)), col="darkWood", mat="wood", role="detail", pri=1.4)
    for i, x in enumerate((-0.8, 0.0, 0.8)):
        H.prim(f"Gauge{i + 1}", "Body", "Cylinder", (0.06, 0.48, 0.48), (x, coam - 0.2, hip[2] - 1.93), rot=(0, math.pi / 2, math.radians(-10)), col="cream", role="detail", pri=2.3)
    H.prim("Beacon", "Body", "Ball", (0.25, 0.25, 0.3), (0, 8.65, -5.9), col="red", glow=True, role="light", pri=2.6)
    ride(H, hip, (-4.0, 2.0), -11.0, 10.8, hip[1] + 3.6, exhaust=(2.0, 3.0, -4.5))
    A.craft_clips(H, 21.0, attack="roll", bank=0.4)
    return H


# ================================================================================================ jet fighter
def jet_gear(H, nose, mains, wr=(0.75, 1.0), door=True):
    """Gear legs with doors on GearF / GearR / GearL (pivots at the strut tops; the game folds them about X)."""
    (nt, na), (mt, ma) = nose, mains
    H.bone("GearF", "Body", nt)
    s, t, _ = gear_leg(nt, na, wr[0], 0.55, pant=False)
    ms = [s, t, cyl(0.12, 1.3, (na[0], na[1], na[2]), axis=0, segs=8)]
    if door:
        ms.append(box((0.08, (nt[1] - na[1]) * 0.75, 1.5), (nt[0] + 0.62, (nt[1] + na[1]) / 2 + 0.3, nt[2] + 0.25), r=0.03))
    dpiece(H, "GearFP", "GearF", merge(*ms), col="metal", mat="metal", role="limb", pri=1.3)
    H.mbone("Gear#", "Body", mt)
    s, t, _ = gear_leg(mt, ma, wr[1], 0.7, pant=False)
    ms = [s, t]
    if door:
        ms.append(xform(box((0.1, (mt[1] - ma[1]) * 0.8, 1.9), (0, 0, 0), r=0.04), (ma[0] + 0.55, (mt[1] + ma[1]) / 2 + 0.25, (mt[2] + ma[2]) / 2), (0, 0, -12)))
    dmpiece(H, "GearP#", "Gear#", merge(*ms), col="metal", mat="metal", role="limb", pri=1.2)


@hero("jet", "aircraft")
def jet():
    """Generic single-seat jet at real game scale (34 studs long, 24 stud span): bubble canopy over the cockpit
    (ejection seat, stick, panel), side intakes, swept wings, twin canted fins, twin nozzles with Burner glow
    discs (BurnerR / BurnerL), tricycle gear on GearF / GearR / GearL."""
    H = P("jet")
    H.preview = {"primary": "#9AA6B2", "secondary": "#4A5562", "dark": "#2B3036"}
    hip = (0.0, 4.1, -7.2)
    yc = 4.8
    F = SplitFus([(-17.2, 0.0, 0.0, 0.0, 4.45), (-16.7, 0.42, 0.42, 0.42, 4.47), (-14.6, 1.12, 1.1, 1.08, 4.55), (-12.2, 1.75, 1.75, 1.55, 4.68),
                  (-10.6, 2.12, 2.1, 2.15, 4.78), (-8.6, 2.38, 2.25, 3.0, yc), (-6.5, 2.38, 2.25, 3.15, yc), (-4.4, 2.32, 2.22, 2.6, yc),
                  (-2.0, 2.5, 2.15, 1.7, yc), (3.0, 2.95, 1.95, 1.48, yc), (8.0, 3.15, 1.7, 1.3, 4.85), (12.0, 2.95, 1.5, 1.2, 4.9),
                  (14.6, 2.75, 1.42, 1.15, 4.9), (14.85, 0.0, 0.0, 0.0, 4.9)], n=36, p_lo=2.8, p_up=2.4)
    H.body((0, yc, 0))
    zg0, zg1, zr = -10.9, -3.4, -13.4
    zs = zrange(-17.2, 14.85, 0.85, (zg0, zg1, zr))
    zs = sorted(set(zs + list(np.linspace(-17.2, -16.0, 4)) + list(np.linspace(14.3, 14.85, 3))))
    under = lambda Q: 0.78 + 0.22 * np.clip((Q[:, 1] - 2.8) / 2.0, 0, 1)
    zh = [z for z in zs if z >= zr]
    dpiece(H, "Hull", "Body", merge(F.lower(zh, n=26), F.upper([z for z in zh if z <= zg0], n=22), F.upper([z for z in zh if z >= zg1], n=22)),
           col="primary", mat="metal", fallback="Ellipsoid", pattern=under)
    dpiece(H, "Nose", "Body", F.shell([z for z in zs if z <= zr], n=30), col="secondary", mat="hard", role="body", pri=1.1)
    dpiece(H, "CanopyGlass", "Body", F.upper([z for z in zs if zg0 <= z <= zg1], th=0.08, n=28), col=[0.62, 0.72, 0.8], mat="glass", tr=0.45, role="glass", pri=1.1)
    frame = merge(F.ring(zg0, r=0.14, out=0.03), F.ring(zg0 + 1.7, r=0.1, out=0.04), F.ring(zg1, r=0.14, out=0.03),
                  F.line(np.linspace(zg0, zg1, 12), yfn=F.yc, r=0.1, out=0.05))
    dpiece(H, "CanopyFrame", "Body", frame, col="dark", role="detail", pri=1.3)
    seams = merge(*[F.ring(z, r=0.045, ylo="full", out=0.0, n=28) for z in (-1.0, 6.0, 11.5)])
    pitot = merge(tube([[0, 4.45, -17.0], [0, 4.45, -18.6]], 0.06, 6), cyl(0.12, 0.5, (0, 4.45, -17.1), axis=2, segs=8))
    dpiece(H, "Seams", "Body", merge(seams, pitot), col="secondary", role="detail", pri=2.0)
    # ---- side intakes (hollow, dark compressor face), LERX strakes
    ink = Fus([(-6.3, 0.95, 1.15, 3.85, 3.0), (-3.5, 1.0, 1.2, 3.85, 3.0), (2.5, 0.92, 1.12, 3.95, 3.0), (7.0, 0.45, 0.8, 4.2, 2.8), (8.2, 0.0, 0.0, 4.3)], n=20, smooth=True)
    duct = xform(band(ink, zrange(-6.3, 8.2, 0.9), th=0.16, n=20), (2.75, 0, 0))
    face = merge(xform(A.lathe([(-0.06, 0.0), (-0.06, 0.62), (0.06, 0.62), (0.06, 0.0)], axis=2, segs=16), (2.75, 3.85, -5.1), (0, 0, 0), (1.0, 1.15, 1.0)),
                 sphere(0.28, (2.75, 3.85, -5.25), scale=(1, 1, 0.7), segs=10))
    dpiece(H, "Intakes", "Body", merge(duct, mirror(duct)), col="primary", mat="metal", role="body", pri=1.1)
    dpiece(H, "IntakeFaces", "Body", merge(face, mirror(face)), col="gunmetal", mat="metal", role="detail", pri=1.9)
    lerx = A.wing(1.5, 8.8, 0.3, sweep=8.0, thick=0.16, pos=(2.1, 4.85, -10.4), nt=6, nu=6)
    # ---- wings, tip rails, fins, stabilisers, ventrals
    wing = A.wing(9.9, 10.6, 2.3, sweep=7.7, thick=0.75, dihedral=-3, pos=(2.3, 4.35, -2.6), nt=9, nu=8)
    dpiece(H, "Wings", "Body", merge(wing, mirror(wing), lerx, mirror(lerx)), col="primary", mat="metal", role="wing", pattern=under)
    tx, ty_ = 2.3 + 9.9, 4.35 - 9.9 * math.tan(math.radians(3))
    rail = merge(rev([(-1.6, 0.0), (-1.4, 0.2), (1.8, 0.2), (2.0, 0.0)], axis=2, segs=10, pos=(tx + 0.05, ty_, -2.6 + 7.7 + 1.0)),
                 box((0.12, 0.3, 2.6), (tx + 0.05, ty_ - 0.2, -2.6 + 7.7 + 1.0), r=0.04))
    flaps = []
    for x0, x1 in ((3.0, 7.2), (7.5, 11.3)):
        z0 = -2.6 + 10.6 + (7.7 + 2.3 - 10.6) * (x0 - 2.3) / 9.9
        z1 = -2.6 + 10.6 + (7.7 + 2.3 - 10.6) * (x1 - 2.3) / 9.9
        dy0, dy1 = -(x0 - 2.3) * math.tan(math.radians(3)), -(x1 - 2.3) * math.tan(math.radians(3))
        flaps.append(tube([[x0, 4.35 + dy0 + 0.17, z0 - 1.5], [x1, 4.35 + dy1 + 0.1, z1 - 0.95]], 0.045, 4))
    fm = merge(rail, *flaps)
    dpiece(H, "WingDetail", "Body", merge(fm, mirror(fm)), col="secondary", role="detail", pri=1.6)
    H.prim("NavLightR", "Body", "Ball", (0.22, 0.22, 0.3), (tx + 0.05, ty_ + 0.22, 6.5), col=[0.2, 0.95, 0.35], glow=True, role="light", pri=2.4)
    H.prim("NavLightL", "Body", "Ball", (0.22, 0.22, 0.3), (-tx - 0.05, ty_ + 0.22, 6.5), col="red", glow=True, role="light", pri=2.4)
    fin = A.fin(6.0, 5.2, 1.7, 4.3, thick=0.38, pos=(0, 0, 0))
    fin = xform(fin, (2.0, 6.0, 8.2), (0, 0, -16))
    rud = xform(tube([[0, 1.0, 4.4], [0, 5.4, 5.6]], 0.05, 4), (2.0, 6.0, 8.2), (0, 0, -16))
    dpiece(H, "Fins", "Body", merge(fin, mirror(fin), rud, mirror(rud)), col="secondary", mat="metal", role="detail", pri=1.1)
    hs = A.wing(4.9, 4.2, 1.5, sweep=3.2, thick=0.32, dihedral=-4, pos=(2.4, 4.55, 11.0))
    ven = xform(A.fin(1.5, 2.2, 1.0, 1.0, thick=0.18, pos=(0, 0, 0)), (1.6, 3.4, 10.5), (0, 0, 180 - 20))
    dpiece(H, "Tail", "Body", merge(hs, mirror(hs), ven, mirror(ven)), col="primary", mat="metal", role="wing")
    # ---- twin nozzles + afterburner glow (Burner*)
    noz = []
    for s in (1, -1):
        noz.append(A.lathe([(13.6, 1.28), (14.6, 1.3), (16.9, 1.08), (16.9, 0.96), (14.8, 1.02), (14.2, 0.9)], axis=2, segs=24, pos=(s * 1.32, 4.75, 0), closed=True))
        noz.append(A.lathe([(15.3, 0.0), (15.3, 1.0), (15.45, 1.0), (15.45, 0.0)], axis=2, segs=20, pos=(s * 1.32, 4.75, 0)))
    dpiece(H, "Nozzles", "Body", merge(*noz), col="gunmetal", mat="metal", role="detail", pattern=lambda Q: 0.82 + 0.18 * np.cos(np.arctan2(Q[:, 1] - 4.75, np.abs(Q[:, 0]) - 1.32) * 16))
    for s, nm in ((1, "R"), (-1, "L")):
        H.prim(f"Burner{nm}", "Body", "Cylinder", (0.08, 1.9, 1.9), (s * 1.32, 4.75, 15.55), rot=(0, math.pi / 2, 0), col="flame", glow=True, role="light", pri=2.2)
        H.prim(f"BurnerCore{nm}", "Body", "Ball", (1.2, 1.2, 1.6), (s * 1.32, 4.75, 15.9), col="flameCore", glow=True, role="light", pri=2.5, tr=0.35)
    # ---- cockpit, gear, antennas
    cockpit(H, F, hip, floor_y=2.85, panel_z=-9.25, panel_w=3.7, panel_top=5.45)
    jet_gear(H, ((0, 2.75, -11.6), (0, 0.75, -11.8)), ((1.9, 3.1, 2.4), (2.95, 1.0, 2.9)))
    H.prim("Beacon", "Body", "Ball", (0.28, 0.2, 0.4), (0, F.top(4.0) + 0.05, 4.0), col="red", glow=True, role="light", pri=2.5)
    ant = merge(xform(A.fin(0.8, 0.6, 0.25, 0.45, thick=0.07, pos=(0, 0, 0)), (0, F.bottom(-2.0) + 0.05, -2.0), (180, 0, 0)),
                xform(A.fin(0.7, 0.55, 0.25, 0.4, thick=0.07, pos=(0, 0, 0)), (0, F.top(1.5) - 0.05, 1.5)))
    dpiece(H, "Antennas", "Body", ant, col="dark", role="detail", pri=2.6)
    ride(H, hip, (-4.5, -7.2), -18.7, 17.0, hip[1] + 3.9, muzzle=(1.6, 5.3, -12.0), exhaust=(0, 4.75, 17.0))
    A.craft_clips(H, 34.0, attack="roll", bank=0.5)
    return H


# ================================================================================================ airliners
def bogie(top, axle_y, wr, ww, xs, zs, extra_len=0.0):
    """Strut from `top` down to a bogie / axle carrying wheels at (x, z) offsets."""
    top = np.asarray(top, float)
    ms = [tube([top, [top[0], (top[1] + axle_y) / 2, top[2]], [top[0], axle_y + wr * 0.5, top[2]]], 0.2, 10),
          cyl(0.3, 1.0, (top[0], top[1] - (top[1] - axle_y) * 0.3, top[2]), axis=1, segs=12, bevel=0.06)]
    if len(zs) > 1:
        ms.append(box((0.35, 0.3, max(zs) - min(zs) + 0.6), (top[0], axle_y, top[2] + (max(zs) + min(zs)) / 2), r=0.1))
    tyres = []
    for dx in xs:
        for dz in zs:
            p = (top[0] + dx, axle_y, top[2] + dz)
            tyres += [wheel(wr, ww, p, axis=0, segs=18), cyl(wr * 0.55, ww + 0.08, p, axis=0, segs=14, bevel=0.05)]
    ms.append(cyl(0.12, (max(xs) - min(xs)) + ww + 0.3, (top[0] + (max(xs) + min(xs)) / 2, axle_y, top[2] + zs[0]), axis=0, segs=8))
    if len(zs) > 1:
        ms.append(cyl(0.12, (max(xs) - min(xs)) + ww + 0.3, (top[0] + (max(xs) + min(xs)) / 2, axle_y, top[2] + zs[-1]), axis=0, segs=8))
    return merge(*ms), merge(*tyres)


def _airliner(hid, L=44.0, R=2.9, engines=2, hump=False, rear=False, prev=None, gear_h=2.5, tail_col="secondary", span_k=0.95):
    """Airliner / business jet at real game scale (Z length L studs). The rider flies from a centred captain's
    seat in the nose cockpit behind a wrap-around windscreen; cabin portholes, doors, swept wings with winglets
    and flap fairings, podded engines (under the wings or on the tail), gear on GearF / GearR / GearL."""
    H = P(hid)
    H.preview = prev or {"primary": "#F5F6F8", "secondary": "#1E5AA8", "dark": "#2B2F36"}
    yc = R + gear_h
    z0, z1 = -L / 2, L / 2
    tc = z1 - 0.36 * L
    F = Fus([(z0, 0.0, 0.0, yc - 0.42 * R), (z0 + 0.35, 0.36 * R, 0.33 * R, yc - 0.4 * R), (z0 + 1.6, 0.66 * R, 0.6 * R, yc - 0.24 * R),
             (z0 + 3.3, 0.88 * R, 0.86 * R, yc - 0.08 * R), (z0 + 5.2, 0.98 * R, 0.98 * R, yc - 0.01 * R), (z0 + 7.0, R, R, yc), (tc, R, R, yc),
             (z1 - 0.17 * L, 0.66 * R, 0.68 * R, yc + 0.3 * R), (z1 - 0.03 * L, 0.24 * R, 0.26 * R, yc + 0.6 * R), (z1, 0.0, 0.0, yc + 0.66 * R)], n=36, p=2.05, smooth=True)
    H.body((0, yc, 0))
    hip = (0.0, yc + R - 3.95, z0 + 6.6)
    ylo, yhi = hip[1] + 0.9, hip[1] + 2.75
    zw0, zw1 = z0 + 2.4, z0 + 8.4
    zs = zrange(z0, z1, L / 46, (zw0, zw1))
    zs = sorted(set(zs + list(np.linspace(z0, z0 + 1.6, 5))))
    zc = [z for z in zs if zw0 <= z <= zw1]
    belly = lambda Q: np.where(Q[:, 1] < yc - R * 0.45, 0.84, 1.0)
    hull = [band(F, [z for z in zs if z <= zw0], th=0.2, n=34), band(F, [z for z in zs if z >= zw1], th=0.2, n=34),
            band(F, zc, yhi=ylo, th=0.2, n=24), band(F, zc, ylo=yhi, th=0.2, n=16)]
    dpiece(H, "Hull", "Body", merge(*hull), col="primary", mat="metal", fallback="Ellipsoid", pattern=belly)
    gl = band(F, zc, ylo=ylo, yhi=yhi, side=True, th=0.08, n=8)
    dpiece(H, "CockpitGlass", "Body", merge(gl, mirror(gl)), col=GLASS, mat="glass", tr=0.5, role="glass", pri=1.1)
    posts = []
    for z in (zw0 + 2.0, zw0 + 3.9):
        a0, a1 = A.fus_angle(F, z, ylo), A.fus_angle(F, z, yhi)
        posts.append(tube([A.fus_point(F, z, a, -0.04) for a in np.linspace(a0, a1, 6)], 0.13, 6))
    pm = merge(*posts)
    sill = A.surface_line(F, np.linspace(zw0, zw1, 10), ylo, r=0.1, out=0.04)
    head = A.surface_line(F, [z for z in np.linspace(zw0, zw1, 10) if F.y_top(z) > yhi + 0.1], yhi, r=0.1, out=0.04)
    ctr = tube([[0, min(F.y_top(z), yhi) + 0.04, z] for z in np.linspace(zw0, zw0 + 2.6, 5)], 0.1, 6)
    dpiece(H, "WindowFrames", "Body", merge(pm, mirror(pm), sill, head, ctr), col="dark", role="detail", pri=1.3)
    # cabin portholes + doors + cheat line
    zp = np.arange(zw1 + 2.6, tc + 0.12 * L, 1.15)
    ports = window_row(F, zp, yc + R * 0.22, w=0.42, h=0.62, th=0.12, r=0.18)
    doors = []
    for z in (zw1 + 1.1, tc + 0.12 * L + 1.4):
        x = F.x_at(z, yc - 0.3)
        q = []
        for k in range(21):
            t = TAU * k / 20
            dz, dy = 0.75 * math.copysign(abs(math.cos(t)) ** 0.25, math.cos(t)), 1.5 * math.copysign(abs(math.sin(t)) ** 0.25, math.sin(t))
            q.append([0, yc - 0.05 + dy, z + dz])
        doors.append(tube([[F.x_at(p[2], p[1]) + 0.02, p[1], p[2]] for p in q], 0.05, 4))
    dm = merge(*doors)
    dpiece(H, "Portholes", "Body", merge(ports, dm, mirror(dm)), col=TINT, mat="hard", role="detail", pri=1.5)
    dpiece(H, "Cheat", "Body", A.surface_line(F, np.linspace(z0 + 2.5, z1 - 4.0, 24), yc - R * 0.12, r=0.16, out=0.06,
                                              yfn=lambda z: yc - R * 0.12 + R * 0.3 * max(0, (z - tc) / (z1 - tc))), col="secondary", role="detail", pri=1.4)
    if hump:
        hf = Fus([(zw1 - 0.6, 0.0, 0.0, yc + R * 0.62), (zw1 + 0.9, R * 0.5, R * 0.42, yc + R * 0.7), (zw1 + 3.5, R * 0.68, R * 0.62, yc + R * 0.74),
                  (zw1 + 13.0, R * 0.7, R * 0.6, yc + R * 0.72), (zw1 + 17.0, R * 0.45, R * 0.32, yc + R * 0.82), (zw1 + 19.0, 0.0, 0.0, yc + R * 0.9)], n=26, smooth=True)
        dpiece(H, "Hump", "Body", hf.mesh(samples=np.linspace(zw1 - 0.6, zw1 + 19.0, 20)), col="primary", mat="metal", role="body")
        hw = window_row(hf, np.arange(zw1 + 3.0, zw1 + 14.0, 1.15), yc + R * 1.02, w=0.4, h=0.55, th=0.12, r=0.16)
        hg = band(hf, np.linspace(zw1 + 0.9, zw1 + 2.2, 4), ylo=yc + R * 0.95, yhi=yc + R * 1.25, side=True, th=0.06, out=0.06, n=6)
        dpiece(H, "HumpGlass", "Body", merge(hw, hg, mirror(hg)), col=TINT, mat="glass", tr=0.45, role="glass", pri=1.6)
    # ---- wings, winglets, flap fairings
    span = span_k * L / 2 - R * 0.55
    rc, tcd = 0.21 * L, 0.055 * L
    wz = -0.12 * L
    wy = yc - 0.6 * R
    sw = span * 0.62
    dh = math.tan(math.radians(6))
    w = A.wing(span, rc, tcd, sweep=sw, thick=0.11 * rc, dihedral=6, pos=(R * 0.5, wy, wz), nt=10, nu=8)
    wl = A.fin(0.07 * L, tcd * 0.95, tcd * 0.45, tcd * 0.6, thick=0.22, pos=(R * 0.5 + span - 0.05, wy + span * dh - 0.1, wz + sw + 0.1), rot=(0, 0, -12))
    root = box((2 * R * 0.85, R * 0.5, rc * 0.9), (0, wy + 0.1, wz + rc * 0.48), r=R * 0.2)
    dpiece(H, "Wings", "Body", merge(w, mirror(w), wl, mirror(wl), root), col="primary", mat="metal", role="wing", pattern=belly)
    ff = []
    for f in (0.25, 0.5, 0.72):
        x = R * 0.5 + span * f
        zt = wz + sw * f + rc + (tcd - rc) * f
        ff.append(rev([(-2.2, 0.0), (-1.6, 0.32), (0.8, 0.3), (1.6, 0.0)], axis=2, segs=10, pos=(x, wy + span * f * dh - 0.25, zt - 0.6), scale=(0.9, 1.0, 1.0)))
    fm = merge(*ff)
    dpiece(H, "FlapFairings", "Body", merge(fm, mirror(fm)), col="primary", mat="metal", role="detail", pri=2.0)
    # ---- engines
    sh, fan = [], []
    if not rear:
        stations = [0.33] if engines == 2 else [0.27, 0.58]
        for f in stations:
            rn = 0.52 * R if engines == 2 else 0.44 * R
            Ln = 0.17 * L if engines == 2 else 0.14 * L
            x = R * 0.5 + span * f
            y = wy + span * f * dh - rn - 0.35
            z = wz + sw * f - Ln * 0.25
            a, b = nacelle((x, y, z), rn, Ln)
            sh += [a, box((0.35, rn * 0.9, Ln * 0.7), (x, y + rn * 0.95, z + Ln * 0.3), r=0.12)]
            fan.append(b)
    else:
        for s in (1, -1):
            rn, Ln = 0.42 * R, 0.2 * L
            x, y, z = R + rn * 0.75, yc + R * 0.35, z1 - 0.3 * L
            a, b = nacelle((x, y, z), rn, Ln)
            sh += [a, box((rn * 1.4, 0.3, Ln * 0.55), (x - rn * 0.9, y, z + 0.1), r=0.1)]
            fan.append(b)
    shm, fm2 = merge(*sh), merge(*fan)
    dpiece(H, "Engines", "Body", merge(shm, mirror(shm)), col="secondary" if rear else "primary", mat="metal", role="detail", pri=1.1)
    dpiece(H, "Fans", "Body", merge(fm2, mirror(fm2)), col="gunmetal", mat="metal", role="detail", pri=1.6)
    # ---- tail
    fin_h = R * (2.2 if not rear else 2.0)
    fz = z1 - 0.2 * L
    fin = A.fin(fin_h, 0.17 * L, 0.07 * L, 0.13 * L, thick=0.32 * R / 2.9 * 1.4, pos=(0, yc + R * 0.55, fz))
    dpiece(H, "Fin", "Body", fin, col=tail_col, mat="metal", role="detail", pri=1.1)
    if rear:
        hs = A.wing(R * 2.2, 0.09 * L, 0.045 * L, sweep=0.06 * L, thick=0.22, pos=(0.05, yc + R * 0.55 + fin_h - 0.25, fz + 0.13 * L - 0.2))
    else:
        hs = A.wing(R * 3.1, 0.11 * L, 0.045 * L, sweep=R * 1.9, thick=0.32, dihedral=6, pos=(R * 0.22, yc + R * 0.42, z1 - 0.16 * L))
    apu = A.lathe([(z1 - 0.3, 0.0), (z1 - 0.3, 0.3), (z1 + 0.25, 0.26), (z1 + 0.25, 0.0)], axis=2, segs=12, pos=(0, yc + 0.66 * R, 0))
    dpiece(H, "Tail", "Body", merge(hs, mirror(hs), apu), col="primary", mat="metal", role="wing")
    H.prim("NavLightR", "Body", "Ball", (0.32, 0.32, 0.4), (R * 0.5 + span + 0.1, wy + span * dh + 0.15, wz + sw + tcd * 0.5), col=[0.2, 0.95, 0.35], glow=True, role="light", pri=2.4)
    H.prim("NavLightL", "Body", "Ball", (0.32, 0.32, 0.4), (-(R * 0.5 + span + 0.1), wy + span * dh + 0.15, wz + sw + tcd * 0.5), col="red", glow=True, role="light", pri=2.4)
    H.prim("Beacon", "Body", "Ball", (0.4, 0.25, 0.6), (0, yc + R + 0.08, -0.05 * L), col="red", glow=True, role="light", pri=2.5)
    # ---- gear
    wr = max(0.55, 0.32 * gear_h)
    nz = z0 + 4.4
    H.bone("GearF", "Body", (0, F.at(nz)[2] - F.at(nz)[1] + 0.3, nz))
    st, ty_ = bogie((0, F.at(nz)[2] - F.at(nz)[1] + 0.3, nz), wr * 0.85, wr * 0.85, 0.5, (-0.45, 0.45), (0.0,))
    dpiece(H, "GearFP", "GearF", merge(st, ty_), col="metal", mat="metal", role="limb", pri=1.3)
    mz = wz + rc * 0.62
    mx = R * 0.72
    H.mbone("Gear#", "Body", (mx, wy - 0.2, mz))
    st, ty_ = bogie((mx, wy - 0.2, mz), wr, wr, 0.6, (-0.4, 0.4) if L > 30 else (0.0,), (-0.85, 0.85) if L > 40 else (0.0,))
    dmpiece(H, "GearP#", "Gear#", merge(st, ty_), col="metal", mat="metal", role="limb", pri=1.2)
    # ---- cockpit: centred captain's seat, panel, yoke, side consoles, back wall
    cockpit(H, SplitFus([(z, *F.at(z)[:2], F.at(z)[1], F.at(z)[2]) for z in np.linspace(z0, zw1 + 1, 12)], n=12), hip,
            floor_y=hip[1] - 1.25, panel_z=hip[2] - 2.05, panel_w=4.2, panel_top=hip[1] + 1.15, ctrl="yoke", screens=3)
    dpiece(H, "CockpitWall", "Body", bulkhead(F, hip[2] + 2.2, ylo=hip[1] - 1.3), col="darker", role="detail", pri=1.7)
    ride(H, hip, (-R - 2.5, zw1 + 1.1), z0 - 0.5, z1 + 0.5, hip[1] + 4.0, exhaust=(0, yc + 0.66 * R, z1 + 0.5))
    A.craft_clips(H, L, attack="dive", bank=0.2)
    return H


@hero("jumbo jet", "aircraft")
def jumbo_jet():
    return _airliner("jumbo jet", L=50.0, R=3.25, engines=4, hump=True, gear_h=2.9, span_k=0.98)


@hero("airplane", "aircraft")
def airplane():
    return _airliner("airplane", L=44.0, R=2.95, engines=2, gear_h=2.5)


@hero("private jet", "aircraft")
def private_jet():
    return _airliner("private jet", L=32.0, R=2.8, rear=True, gear_h=1.7, prev={"primary": "#F5F6F8", "secondary": "#C9A227", "dark": "#2B2F36"}, tail_col="primary", span_k=0.9)


# ================================================================================================ glider
@hero("glider", "aircraft")
def glider():
    """Sailplane at real game scale (20 studs long, 36 stud span): slim pod-and-boom fuselage, long canopy over the
    cockpit (stick, panel), high-aspect wings with tip skids, T-tail, single fixed main wheel + nose skid."""
    H = P("glider")
    H.preview = {"primary": "#F5F6F8", "secondary": "#1E88E5", "dark": "#2B2F36"}
    yc = 3.9
    hip = (0.0, 3.25, -3.6)
    F = SplitFus([(-9.0, 0.0, 0.0, 0.0, 3.2), (-8.75, 0.55, 0.55, 0.5, 3.25), (-7.6, 1.45, 1.4, 1.2, 3.55), (-6.0, 2.1, 1.95, 1.75, 3.8),
                  (-4.6, 2.3, 2.2, 2.85, yc), (-3.2, 2.3, 2.2, 3.4, yc), (-1.6, 2.25, 2.15, 3.25, yc), (0.2, 2.0, 1.95, 2.2, 4.0),
                  (2.4, 1.2, 1.25, 1.1, 4.25), (6.0, 0.62, 0.64, 0.6, 4.6), (10.0, 0.45, 0.48, 0.46, 4.85), (10.9, 0.3, 0.32, 0.3, 4.9), (11.05, 0.0, 0.0, 0.0, 4.9)],
                 n=32, p_lo=2.3, p_up=2.2)
    H.body((0, yc, 0))
    zg0, zg1 = -7.0, 0.4
    zs = zrange(-9.0, 11.05, 0.55, (zg0, zg1))
    zs = sorted(set(zs + list(np.linspace(-9.0, -8.2, 4))))
    dpiece(H, "Hull", "Body", merge(F.lower(zs, n=26), F.upper([z for z in zs if z <= zg0], n=20), F.upper([z for z in zs if z >= zg1], n=20)),
           col="primary", mat="hard", fallback="Ellipsoid")
    dpiece(H, "CanopyGlass", "Body", F.upper([z for z in zs if zg0 <= z <= zg1], th=0.07, n=26), col=GLASS, mat="glass", tr=0.5, role="glass", pri=1.1)
    dpiece(H, "CanopyFrame", "Body", merge(F.ring(zg0, r=0.1, out=0.03), F.ring(zg1, r=0.11, out=0.03), F.line(np.linspace(zg0, zg1, 12), yfn=F.yc, r=0.08, out=0.04)),
           col="dark", role="detail", pri=1.3)
    dpiece(H, "Stripe", "Body", F.line(np.linspace(-8.4, 10.6, 22), yfn=lambda z: F.yc(z) - 0.25, r=0.1, out=0.04), col="secondary", role="detail", pri=1.4)
    wy = F.top(1.0) - 0.15
    w = A.wing(16.6, 3.0, 1.2, sweep=0.5, thick=0.36, dihedral=3.0, pos=(0.6, wy, -0.4), nt=12, nu=8, tip_round=0.5)
    dpiece(H, "Wings", "Body", merge(w, mirror(w), box((1.6, 0.4, 3.0), (0, wy - 0.05, 1.1), r=0.15)), col="primary", mat="hard", role="wing")
    dh = math.tan(math.radians(3))
    tipx = 0.6 + 16.6
    wl = A.fin(1.1, 1.15, 0.5, 0.45, thick=0.1, pos=(tipx - 0.05, wy + 16.6 * dh, 0.2), rot=(0, 0, -8))
    brakes = merge(*[box((2.2, 0.06, 0.18), (s * 5.5, wy + 5.0 * dh + 0.2, 0.8), r=0.03) for s in (1, -1)])
    wlm = merge(wl, tube([[tipx - 0.6, wy + 16.0 * dh - 0.2, 0.2], [tipx - 0.6, wy + 16.0 * dh - 0.5, 0.9]], 0.05, 4))
    dpiece(H, "WingTips", "Body", merge(wlm, mirror(wlm), brakes), col="secondary", role="detail", pri=1.4)
    fin = A.fin(3.4, 2.4, 1.3, 1.2, thick=0.28, pos=(0, F.top(8.6) - 0.1, 8.5))
    hs = A.wing(3.0, 1.35, 0.75, sweep=0.35, thick=0.16, pos=(0.0, F.top(8.6) - 0.1 + 3.35, 9.65))
    dpiece(H, "Tail", "Body", merge(fin, hs, mirror(hs)), col="secondary", role="detail", pri=1.1)
    H.prim("NavLightR", "Body", "Ball", (0.22, 0.22, 0.28), (tipx + 0.05, wy + 16.6 * dh + 0.05, 0.4), col=[0.2, 0.95, 0.35], glow=True, role="light", pri=2.5)
    H.prim("NavLightL", "Body", "Ball", (0.22, 0.22, 0.28), (-tipx - 0.05, wy + 16.6 * dh + 0.05, 0.4), col="red", glow=True, role="light", pri=2.5)
    gear = merge(wheel(0.85, 0.5, (0, 0.85, -2.6), axis=0, segs=18), cyl(0.5, 0.58, (0, 0.85, -2.6), axis=0, segs=12, bevel=0.06))
    skid = merge(tube([[0, F.bottom(-7.6) + 0.15, -7.6], [0, 1.05, -6.7], [0, 0.95, -5.0]], 0.16, 8), sphere(0.3, (0, F.bottom(10.5) - 0.15, 10.5), segs=10),
                 box((0.12, 1.1, 1.4), (0.34, 1.3, -2.6), r=0.05), box((0.12, 1.1, 1.4), (-0.34, 1.3, -2.6), r=0.05))
    dpiece(H, "Wheel", "Body", gear, col="tyre", mat="rubber", role="detail", pri=1.2)
    dpiece(H, "Skid", "Body", skid, col="dark", role="detail", pri=1.4)
    cockpit(H, F, hip, floor_y=hip[1] - 1.25, panel_z=hip[2] - 2.05, panel_w=3.4, panel_top=hip[1] + 1.15, screens=1, side_console=False)
    ride(H, hip, (-4.0, -3.6), -9.2, 11.1, hip[1] + 3.8)
    A.craft_clips(H, 20.0, attack="dive", bank=0.45)
    return H


# ================================================================================================ helicopter
GLASS = [0.62, 0.8, 0.92]
SCREEN = [0.35, 0.75, 1.0]


def ride(H, hip, enter, nose_z, tail_z, top_y, seat_size=(1.8, 0.15, 1.5), muzzle=None, exhaust=None, length="auto"):
    """Real-scale rideable craft: seat socket at the rider's hip, enter socket on the ground, measured length."""
    A.mount(H, "Seat", hip, seat_size, length=length, enter=enter)
    H.socket("head", (hip[0], top_y, hip[2]), "Body")
    H.socket("mouth", (0, hip[1] - 0.3, nose_z), "Body")
    H.socket("exhaust", exhaust or (0, hip[1] - 0.5, tail_z), "Body")
    if muzzle is not None:
        H.socket("muzzle", muzzle, "Body")


def slab_floor(fus, z0, z1, y, inset=0.25, th=0.14, nz=10):
    """Cabin floor plate following the inside of a Fus at height y."""
    rings = []
    for z in np.linspace(z0, z1, nz):
        hw = max(fus.x_at(z, y) - inset, 0.05)
        rings.append(np.array([[-hw, y - th, z], [hw, y - th, z], [hw, y, z], [-hw, y, z]]))
    return A.loft(rings, "fan", "fan", crease=30)


def bulkhead(fus, z, th=0.12, inset=0.1, ylo=None):
    r = fus.ring(z, 32)
    w, h, yc, p = fus.at(z)
    r[:, 0] *= (w - inset) / w
    r[:, 1] = yc + (r[:, 1] - yc) * (h - inset) / h
    if ylo is not None:
        r[:, 1] = np.maximum(r[:, 1], ylo)
    a, b = r.copy(), r.copy()
    a[:, 2] = z - th / 2
    b[:, 2] = z + th / 2
    return A.loft([a, b], "fan", "fan", crease=40)


@hero("helicopter", "aircraft")
def helicopter():
    """Civilian light helicopter at real game scale (~28 studs nose to tail, 30 stud rotor): glass bubble cabin with
    two front seats (the rider flies from the right-hand pilot seat), rear bench, T-bar cyclic, instrument panel,
    skids, engine fairing, 4-blade main rotor (bone Rotor, spins about Y) and a 2-blade tail rotor (bone TailRotor,
    spins about X)."""
    H = P("helicopter", gait="hover")
    H.preview = {"primary": "#ECEFF3", "secondary": "#C62828", "dark": "#2B2F36"}
    hip = (1.1, 3.25, -3.4)
    cab = Fus([(-9.7, 0.0, 0.0, 3.55), (-9.45, 1.25, 1.25, 3.6), (-8.8, 2.25, 2.05, 3.8), (-7.6, 3.05, 2.65, 4.1), (-5.8, 3.5, 2.9, 4.4), (-3.0, 3.65, 2.98, 4.55),
               (0.0, 3.6, 2.95, 4.6), (2.4, 3.25, 2.72, 4.75), (4.4, 2.3, 1.95, 5.2), (6.0, 1.2, 1.1, 5.6), (6.5, 0.0, 0.0, 5.75)], n=36, p=2.6, smooth=True)
    H.body((0, 4.6, 0))

    def yb(z):  # beltline: the glass runs down into a chin bubble at the nose
        return float(np.interp(z, [-9.7, -8.7, -6.3, 10], [3.15, 3.15, 4.4, 4.4]))

    zs_all = np.r_[np.linspace(-9.7, -8.8, 4), np.linspace(-8.5, 6.5, 26)]
    zs_glass = [z for z in zs_all if z <= -0.6] + [-0.6]
    zs_roof = [-0.6] + [z for z in zs_all if z > -0.6]
    belly = lambda Q: 0.8 + 0.2 * np.clip((Q[:, 1] - 1.6) / 1.6, 0, 1)
    dpiece(H, "Hull", "Body", band(cab, zs_all, yhi=yb, th=0.2, n=36), col="primary", mat="hard", fallback="Ellipsoid", pattern=belly)
    dpiece(H, "Roof", "Body", band(cab, zs_roof, ylo=yb, th=0.2, n=28), col="primary", mat="hard", role="body")
    dpiece(H, "CanopyGlass", "Body", band(cab, zs_glass, ylo=yb, th=0.08, n=28), col=GLASS, mat="glass", tr=0.5, role="glass", pri=1.1)
    # frames: B-pillar ring, roof spine, windscreen centre post, beltline trim
    frame = [A.ring_line(cab, -0.6, r=0.14, ylo=4.4, out=0.02, n=20),
             tube([A.fus_point(cab, z, math.pi / 2, -0.03) for z in np.linspace(-8.9, -0.6, 10)], 0.11, 8)]
    dpiece(H, "Frame", "Body", merge(*frame), col="dark", mat="hard", role="detail", pri=1.4)
    dpiece(H, "Beltline", "Body", A.surface_line(cab, np.linspace(-9.55, 6.2, 26), 0, r=0.1, out=0.03, yfn=yb), col="secondary", role="detail", pri=1.3)
    dpiece(H, "Stripe", "Body", A.surface_line(cab, np.linspace(-9.0, 5.8, 22), 2.75, r=0.16, out=0.04), col="secondary", role="detail", pri=1.5)
    # doors: seams, handles, rear windows
    seams = [A.ring_line(cab, z, r=0.05, ylo=2.35, yhi=4.38, out=0.01, n=10) for z in (-6.2, -0.75)]
    seams.append(A.ring_line(cab, 2.5, r=0.05, ylo=2.4, yhi=6.4, out=0.01, n=14))
    sm = merge(*seams)
    hz = [box((0.12, 0.12, 0.55), (cab.x_at(z, 3.9) + 0.06, 3.9, z), r=0.04) for z in (-1.35, 1.9)]
    dpiece(H, "DoorSeams", "Body", merge(sm, mirror(sm), *hz, *[mirror(m) for m in hz]), col="dark", role="detail", pri=1.9)
    rw = band(cab, np.linspace(-0.2, 2.1, 6), ylo=4.75, yhi=6.4, side=True, th=0.04, out=0.06, n=8)
    dpiece(H, "WindowGlass", "Body", merge(rw, mirror(rw)), col=TINT, mat="glass", tr=0.45, role="glass", pri=1.6)

    # ---- interior: floor, two pilot seats, rear bench, bulkhead, panel + screens, T-bar cyclic, pedals
    dpiece(H, "Floor", "Body", slab_floor(cab, -7.6, 2.2, 2.05), col="darker", role="detail", pri=1.6)
    seats = [A.pilot_seat(hip, w=1.75, floor_y=2.05), A.pilot_seat((-hip[0], hip[1], hip[2]), w=1.75, floor_y=2.05)]
    bench = merge(box((5.2, 0.45, 1.5), (0, 2.95, 0.55), r=0.15, seg=1), xform(box((5.2, 2.6, 0.4), (0, 1.3, 0), r=0.15, seg=1), (0, 2.95, 1.45), (8, 0, 0)))
    dpiece(H, "Seat", "Body", merge(*seats), col="dark", mat="cloth", role="detail", pri=1.2)
    dpiece(H, "RearBench", "Body", merge(bench, bulkhead(cab, 2.15, ylo=2.0)), col="darker", mat="cloth", role="detail", pri=1.7)
    panel = merge(xform(box((5.4, 1.15, 0.9), (0, 0, 0), r=0.2, seg=1), (0, 4.3, -5.75), (-12, 0, 0)),
                  xform(box((5.2, 0.16, 1.2), (0, 0, 0), r=0.07), (0, 4.95, -5.8), (-6, 0, 0)),
                  box((0.95, 2.3, 0.75), (0, 3.15, -5.75), r=0.12))
    dpiece(H, "Panel", "Body", panel, col="darker", role="detail", pri=1.3)
    for i, x in enumerate((1.1, -1.1)):
        H.prim(f"Screen{i + 1}", "Body", "Block", (1.0, 0.62, 0.06), (x, 4.32, -5.24), rot=(math.radians(-12), 0, 0), col=SCREEN, glow=True, role="light", pri=2.0)
    cyc = merge(tube([[0, 2.05, -5.15], [0, 3.6, -5.12], [0.0, 4.5, -5.02]], 0.08, 8), tube([[-0.55, 4.55, -5.02], [2.7, 4.55, -5.02]], 0.07, 8),
                cyl(0.12, 0.5, (2.75, 4.55, -5.02), axis=0, segs=8), cyl(0.12, 0.5, (-0.6, 4.55, -5.02), axis=0, segs=8),
                tube([[-0.25, 2.1, -2.0], [-0.25, 2.55, -3.2]], 0.06, 6),
                *[xform(box((0.45, 0.6, 0.12), (0, 0, 0), r=0.04), (x, 2.4, -5.25), (-35, 0, 0)) for x in (0.6, 1.6, -0.6, -1.6)])
    dpiece(H, "Controls", "Body", cyc, col="gunmetal", mat="metal", role="detail", pri=1.6)

    # ---- engine fairing, exhaust, intakes, mast + rotor
    fair = Fus([(-0.9, 0.0, 0.0, 7.35), (-0.4, 1.0, 0.65, 7.45), (1.0, 1.55, 1.0, 7.7), (4.0, 1.5, 0.95, 7.65), (6.2, 0.95, 0.7, 7.25), (7.4, 0.0, 0.0, 6.95)], n=24, p=2.8, smooth=True)
    dpiece(H, "Fairing", "Body", fair.mesh(samples=np.linspace(-0.9, 7.4, 16)), col="primary", mat="hard", role="body")
    grill = []
    for z in np.linspace(1.4, 3.0, 5):
        x = fair.x_at(z, 7.75)
        grill.append(box((0.08, 0.7, 0.18), (x - 0.01, 7.75, z), r=0.03))
    gm = merge(*grill)
    exh = merge(A.lathe([(0, 0.42), (1.1, 0.4), (1.1, 0.3), (0.05, 0.32)], axis=2, segs=14, closed=True, pos=(0.65, 7.75, 5.4), rot=(-20, 0, 0)),
                A.lathe([(0.5, 0.0), (0.5, 0.32), (0.6, 0.32), (0.6, 0.0)], axis=2, segs=14, pos=(0.65, 7.75, 5.4), rot=(-20, 0, 0)))
    dpiece(H, "Intakes", "Body", merge(gm, mirror(gm), exh), col="gunmetal", mat="metal", role="detail", pri=1.8)
    rz, ry = 0.6, 9.85
    mast = merge(cyl(0.32, 1.6, (0, 9.0, rz), axis=1, segs=14, bevel=0.05), cyl(0.7, 0.16, (0, 9.05, rz), axis=1, segs=18, bevel=0.04),
                 cyl(0.85, 0.3, (0, 8.62, rz), axis=1, segs=18, bevel=0.1))
    dpiece(H, "Mast", "Body", mast, col="metal", mat="metal", role="detail", pri=1.4)
    H.bone("Rotor", "Body", (0, ry, rz))
    R = 15.0
    blades, tips = [], []
    for k in range(4):
        b = A.blade(R * 0.9 - 1.1, lambda t: -0.52, lambda t: 0.5, lambda t, u: 0.09 * math.sin(math.pi * u) ** 0.7, pos=(1.1, 0, 0), nt=8, nu=6)
        tp = A.blade(R * 0.1, lambda t: -0.52, lambda t: 0.5 - 0.35 * t ** 2, lambda t, u: 0.09 * math.sin(math.pi * u) ** 0.7, pos=(R * 0.9, 0, 0), nt=4, nu=6)
        grip = box((0.9, 0.3, 0.55), (0.95, 0, 0), r=0.1)
        rot = (0, 90 * k + 45, 0)
        blades.append(xform(merge(b, grip), (0, ry, rz), rot))
        tips.append(xform(tp, (0, ry, rz), rot))
    hub = merge(cyl(0.75, 0.42, (0, ry, rz), axis=1, segs=18, bevel=0.12), rev([(ry + 0.2, 0.0), (ry + 0.25, 0.45), (ry + 0.55, 0.3), (ry + 0.65, 0.0)], axis=1, segs=14, pos=(0, 0, rz)))
    dpiece(H, "RotorP", "Rotor", merge(*blades, hub), col="dark", mat="hard", role="detail", pri=1.0)
    dpiece(H, "RotorTips", "Rotor", merge(*tips), col="secondary", mat="hard", role="detail", pri=2.2)

    # ---- tail boom, fins, stabiliser, tail rotor
    boom = Fus([(5.2, 1.05, 1.0, 5.75), (9.0, 0.8, 0.78, 6.05), (14.0, 0.6, 0.58, 6.4), (17.4, 0.48, 0.48, 6.65), (18.2, 0.34, 0.34, 6.72), (18.45, 0.0, 0.0, 6.75)], n=20, p=2.2, smooth=True)
    dpiece(H, "Boom", "Body", boom.mesh(samples=np.linspace(5.2, 18.45, 14)), col="primary", mat="hard", role="body", pattern=belly)
    dpiece(H, "BoomStripe", "Body", A.surface_line(boom, np.linspace(5.6, 17.0, 10), 6.0, r=0.1, out=0.03, yfn=lambda z: float(np.interp(z, [5.6, 17], [5.6, 6.6]))), col="secondary", role="detail", pri=1.8)
    fin = A.fin(3.3, 2.1, 1.0, 1.5, thick=0.3, pos=(0, 6.75, 16.3))
    ventral = A.fin(1.7, 1.5, 0.8, 0.9, thick=0.24, pos=(0, -6.5, 16.6), rot=(0, 0, 0))
    ventral = xform(ventral, (0, 0, 0), (0, 0, 180))
    skid = tube([[0, 4.9, 17.6], [0, 4.6, 18.3], [0, 4.7, 18.8]], 0.07, 6)
    dpiece(H, "TailFin", "Body", merge(fin, ventral), col="secondary", mat="hard", role="detail", pri=1.2)
    hs = A.wing(2.5, 1.35, 0.95, sweep=0.3, thick=0.16, pos=(0.35, 6.3, 14.4))
    ep = A.fin(1.2, 1.0, 0.7, 0.3, thick=0.12, pos=(2.85, 5.95, 14.6))
    dpiece(H, "Stabiliser", "Body", merge(hs, mirror(hs), ep, mirror(ep)), col="primary", mat="hard", role="wing", pri=1.4)
    gb = merge(rev([(-0.15, 0.0), (-0.1, 0.42), (0.35, 0.4), (0.55, 0.0)], axis=0, segs=12, pos=(-0.35, 8.25, 17.75)), skid)
    dpiece(H, "TailGearbox", "Body", gb, col="metal", mat="metal", role="detail", pri=1.8)
    tz, tyy, tx = 17.75, 8.25, -0.75
    H.bone("TailRotor", "Body", (tx, tyy, tz))
    tr = A.prop(2, 2.2, 0.36, axis="z", thick=0.05, hub=(0.22, 0.3), pitch=12)
    trm = xform(tr, (tx, tyy, tz), (0, 90, 0))
    dpiece(H, "TailRotorP", "TailRotor", trm, col="dark", role="detail", pri=1.3)

    # ---- skids (on the ground), cross tubes, steps
    sk = []
    for s in (1, -1):
        sk.append(tube([[s * 3.0, 1.15, -8.5], [s * 3.0, 0.62, -7.9], [s * 3.0, 0.28, -7.0], [s * 3.0, 0.28, 3.4], [s * 3.0, 0.34, 4.1]], 0.22, 10))
    for z in (-4.7, 1.8):
        sk.append(tube([[-3.0, 0.28, z], [-3.0, 0.85, z], [-2.55, 1.55, z], [-1.6, 1.9, z], [0, 1.95, z], [1.6, 1.9, z], [2.55, 1.55, z], [3.0, 0.85, z], [3.0, 0.28, z]], 0.17, 10))
    dpiece(H, "Skids", "Body", merge(*sk), col="metal", mat="metal", role="limb", pri=1.0)
    steps = [box((0.8, 0.1, 1.1), (s * 3.0, 0.62, -3.3), r=0.04) for s in (1, -1)] + [box((0.12, 0.35, 0.12), (s * 3.0, 0.42, z), r=0.03) for s in (1, -1) for z in (-3.75, -2.85)]
    dpiece(H, "Steps", "Body", merge(*steps), col="gunmetal", mat="metal", role="detail", pri=2.2)

    # ---- lights, antennas
    H.prim("NavLightR", "Body", "Ball", (0.22, 0.22, 0.22), (2.85, 7.22, 15.25), col=[0.2, 0.95, 0.35], glow=True, role="light", pri=2.4)
    H.prim("NavLightL", "Body", "Ball", (0.22, 0.22, 0.22), (-2.85, 7.22, 15.25), col="red", glow=True, role="light", pri=2.4)
    H.prim("Beacon", "Body", "Ball", (0.32, 0.22, 0.32), (0, 8.75, 3.8), col="red", glow=True, role="light", pri=2.3)
    H.prim("Strobe", "Body", "Ball", (0.22, 0.22, 0.22), (0, 10.08, 18.5), col="white", glow=True, role="light", pri=2.6)
    H.prim("LandingLight", "Body", "Cylinder", (0.1, 0.5, 0.5), (0, 1.88, -6.6), rot=(0, 0, math.pi / 2), col="cream", glow=True, role="light", pri=2.3)
    ant = merge(A.fin(0.7, 0.5, 0.2, 0.35, thick=0.06, pos=(0, -1.75, 0.5)), tube([[0, 7.2, 3.0], [0, 8.4, 3.6]], 0.03, 4))
    ant = merge(xform(A.fin(0.7, 0.5, 0.2, 0.35, thick=0.06, pos=(0, 0, 0)), (0, 1.7, -0.2), (180, 0, 0)), tube([[0.9, 7.6, 4.4], [0.9, 8.6, 5.2]], 0.03, 4))
    dpiece(H, "Antennas", "Body", ant, col="dark", role="detail", pri=2.6)

    ride(H, hip, (5.0, -3.4), -9.8, 18.5, 11.0, exhaust=(0.65, 8.1, 6.4))
    A.craft_clips(H, 28.0, hover=True, attack="ram", bank=0.2)
    return H


# ================================================================================================ hot air balloon
@hero("hot air balloon", "aircraft")
def hot_air_balloon():
    H = P("hot air balloon", gait="hover")
    H.preview = {"primary": "#E53935", "secondary": "#FFC107"}
    H.body((0, 2.0, 0))
    prof = [(4.4, 0.95), (5.0, 1.35), (6.2, 2.6), (7.6, 3.7), (9.4, 4.35), (11.0, 4.3), (12.4, 3.6), (13.4, 2.4), (13.95, 1.0), (14.1, 0.0)]
    ys = np.linspace(prof[0][0], prof[-1][0], 22)
    rs = np.interp(ys, [p[0] for p in prof], [p[1] for p in prof])
    # smooth the profile a little (cubic through the points)
    from scipy.interpolate import PchipInterpolator  # noqa
    rs = PchipInterpolator([p[0] for p in prof], [p[1] for p in prof])(ys)
    ng, per = 12, 5
    gores = [[], []]
    for g in range(ng):
        rings = []
        for y, r in zip(ys, rs):
            pts = []
            for k in range(per):
                u = k / (per - 1)
                a = TAU * (g + u) / ng
                rr = r * (1 + 0.045 * math.sin(math.pi * u))
                pts.append([rr * math.cos(a), y, rr * math.sin(a)])
            rings.append(pts)
        # an open strip (one gore), single surface lofted along y
        V, F = [], []
        for i, ring in enumerate(rings):
            V += ring
        for i in range(len(rings) - 1):
            for k in range(per - 1):
                a_, b_ = i * per + k, (i + 1) * per + k
                F += [[a_, b_ + 1, b_], [a_, a_ + 1, b_ + 1]]
        gores[g % 2].append(A.finish(np.array(V), np.array(F), 50))
    dpiece(H, "Hull", "Body", merge(*gores[0]), col="primary", mat="cloth", fallback="Ellipsoid", pri=0.9)
    dpiece(H, "Envelope2", "Body", merge(*gores[1]), col="secondary", mat="cloth", role="body", pri=0.9)
    dpiece(H, "Crown", "Body", merge(A.lathe([(14.05, 0.0), (14.05, 0.7), (14.2, 0.6), (14.2, 0.0)], axis=1, segs=16),
                                     A.lathe([(4.3, 0.92), (4.6, 1.02), (4.6, 0.9), (4.3, 0.84)], axis=1, segs=20, closed=True)), col="darker", mat="cloth", role="detail")
    # basket on a bone (swings under the envelope), ropes, burner
    H.bone("Basket", "Body", (0, 3.3, 0))
    bw, bh = 1.0, 1.25
    basket = [box((2 * bw, bh, 2 * bw), (0, bh / 2, 0), r=0.12, seg=2)]
    for y in np.linspace(0.15, bh - 0.1, 5):
        basket.append(A.lathe([(y - 0.04, bw * 1.2), (y + 0.04, bw * 1.2), (y + 0.04, bw * 1.05), (y - 0.04, bw * 1.05)], axis=1, segs=4, rot=(0, 45, 0), closed=True))
    dpiece(H, "Seat", "Basket", merge(*basket), col="wood", mat="wood", role="detail", fallback="Block")
    dpiece(H, "Rim", "Basket", merge(A.lathe([(bh - 0.08, bw * 1.42), (bh + 0.08, bw * 1.42), (bh + 0.08, bw * 1.26), (bh - 0.08, bw * 1.26)], axis=1, segs=4, rot=(0, 45, 0), closed=True),
                                     A.lathe([(-0.02, bw * 1.42), (0.12, bw * 1.42), (0.12, bw * 1.3), (-0.02, bw * 1.3)], axis=1, segs=4, rot=(0, 45, 0), closed=True)), col="leather", mat="cloth", role="detail")
    ropes = []
    for sx in (1, -1):
        for sz in (1, -1):
            ropes.append(tube([[sx * bw * 0.95, bh, sz * bw * 0.95], [sx * 0.55, 3.0, sz * 0.55], [sx * 0.66, 4.4, sz * 0.66]], 0.035, 4))
    frame = merge(*ropes, A.lathe([(2.95, 0.66), (3.05, 0.66), (3.05, 0.56), (2.95, 0.56)], axis=1, segs=4, rot=(0, 45, 0), closed=True),
                  cyl(0.24, 0.55, (0.22, 3.0, 0), axis=1, segs=10), cyl(0.24, 0.55, (-0.22, 3.0, 0), axis=1, segs=10))
    dpiece(H, "Rigging", "Basket", frame, col="metal", mat="metal", role="detail")
    H.prim("Flame", "Basket", "Ball", (0.35, 0.7, 0.35), (0, 3.5, 0), col="flame", glow=True, role="light", pri=2.3)
    dpiece(H, "Sandbags", "Basket", merge(*[rev([(-0.22, 0), (-0.18, 0.15), (0.12, 0.16), (0.24, 0)], axis=1, segs=8, pos=(x * bw * 1.45, bh * 0.55, z * bw * 1.45)) for x, z in ((1, 0.3), (-1, -0.3), (0.3, -1), (-0.3, 1))]),
           col=[0.75, 0.66, 0.48], mat="cloth", role="detail")
    common(H, (0, 3.3 + 0.35, 0), (1.6, 0.15, 1.6), -4.5, 4.5, 14.5)
    H.socket("seat", (0, 3.6, 0), "Basket")

    def extra(name, u, pose):
        A._add(pose, "Basket", (0, 0, 0, 0.04 * math.sin(TAU * u + 0.5), 0, 0.05 * math.sin(TAU * u)))
        A._add(pose, "Body", (0, 0, 0, 0, 0.1 * math.sin(TAU * u * 0.5), 0))

    A.air_clips(H, size=1.0, extra=extra, attack="ram", hover=True, bank=0.06)
    return H


# ================================================================================================ blimp
@hero("blimp", "aircraft")
def blimp():
    H = P("blimp", gait="hover")
    H.preview = {"primary": "#ECEFF1", "secondary": "#E53935"}
    yc, R, L = 4.6, 3.1, 20.0
    env = Fus([(-L / 2, 0, 0, yc), (-L / 2 + 0.6, R * 0.5, R * 0.5, yc), (-L / 2 + 2.5, R * 0.86, R * 0.86, yc), (-2.0, R, R, yc), (2.0, R, R, yc),
               (L / 2 - 4.5, R * 0.72, R * 0.72, yc), (L / 2 - 1.5, R * 0.3, R * 0.3, yc), (L / 2, 0, 0, yc)], n=26)
    H.body((0, yc, 0))
    dpiece(H, "Hull", "Body", env.mesh(), col="primary", mat="cloth", fallback="Ellipsoid")
    dpiece(H, "Stripe", "Body", cheat(env, -L / 2 + 1.2, L / 2 - 1.5, 0.0, r=0.3, out=0.08), col="secondary", role="detail")
    dpiece(H, "NoseCap", "Body", Fus([(-L / 2 - 0.02, 0, 0, yc), (-L / 2 + 0.6, R * 0.52, R * 0.52, yc), (-L / 2 + 1.0, R * 0.64, R * 0.64, yc)], n=26).mesh(), col="secondary", role="detail")
    fins = []
    for a in (0, 90, 180, 270):
        f = A.fin(2.2, 3.4, 1.8, 1.4, thick=0.2, pos=(0, R * 0.42, L / 2 - 4.2))
        fins.append(xform(f, (0, yc, 0), (0, 0, a)))
    dpiece(H, "Fins", "Body", merge(*fins), col="secondary", mat="hard", role="detail")
    # gondola with windows, open front cockpit seat
    g = Fus([(-3.0, 0.0, 0.0, 1.0), (-2.6, 0.6, 0.55, 0.95), (-1.6, 0.9, 0.8, 0.9), (1.8, 0.9, 0.8, 0.95), (2.8, 0.4, 0.45, 1.15), (3.1, 0.0, 0.0, 1.3)], n=18, p=3.0)
    dpiece(H, "Gondola", "Body", merge(g.mesh(), box((1.0, 0.8, 3.0), (0, 1.9, 0.0), r=0.2)), col="secondary", mat="hard", role="body")
    dpiece(H, "Windows", "Body", merge(window_row(g, [-1.4, -0.5, 0.4, 1.3], 1.2, w=0.6, h=0.42), box((1.0, 0.4, 0.07), (0, 1.3, -2.55), r=0.04, rot=(-40, 0, 0))), col=TINT, mat="glass", role="glass", pri=1.5)
    dpiece(H, "Seat", "Body", merge(bucket_seat((0, 1.75, -1.2), w=0.7)), col="dark", mat="cloth", role="detail")
    # engine pods with props on bones
    ex, ey, ez = 1.8, 1.4, 1.0
    H.mbone("Prop#", "Body", (ex, ey, ez + 1.3))
    pod = merge(rev([(-1.0, 0), (-0.8, 0.32), (0.4, 0.34), (1.2, 0.0)], axis=2, segs=12, pos=(ex, ey, ez)), tube([[0.8, ey, ez], [ex, ey, ez]], 0.08, 6))
    dmpiece(H, "Pod#", "Body", pod, col="metal", mat="metal", role="detail")
    dmpiece(H, "PropP#", "Prop#", A.prop(3, 0.75, 0.2, axis="z", pos=(ex, ey, ez + 1.25), thick=0.03), col="dark", role="detail")
    dpiece(H, "Cables", "Body", merge(*[tube([[s * 0.8, 2.2, z], [s * 1.6, yc - R * 0.85, z * 1.3]], 0.03, 4) for s in (1, -1) for z in (-2.0, 2.0)]), col="steel", mat="metal", role="detail", pri=2.5)
    common(H, (0, 2.1, -1.2), (0.7, 0.15, 0.8), -L / 2 - 0.5, L / 2 + 0.5, yc + R + 0.5)
    A.air_clips(H, size=1.5, spinners=[("PropR", "z", 1, TAU / 3), ("PropL", "z", -1, TAU / 3)], attack="ram", hover=True, bank=0.08)
    return H


# ================================================================================================ flying carpet
@hero("flying carpet", "aircraft")
def flying_carpet():
    H = P("flying carpet", tags=("vehicle", "magic"))
    H.preview = {"primary": "#7B1FA2", "secondary": "#FFC107"}
    y0 = 1.2
    H.body((0, y0, 0))
    W, L, n = 2.4, 6.0, 4
    seg = L / n
    zs = [-L / 2 + i * seg for i in range(n + 1)]
    prev = "Body"
    for i in range(n):
        za, zb = zs[i], zs[i + 1]
        b = H.bone(f"Seg{i + 1}", prev, (0, y0, za + (0 if i == 0 else 0)))
        prev = b
        ov = 0.08  # overlap into the next segment so the joint never gaps

        def sheet(t, u, za=za, zb=zb):
            z = za - (ov if i > 0 else 0) + (zb - za + (ov if i > 0 else 0) + (ov if i < n - 1 else 0)) * t
            x = -W / 2 + W * u
            y = y0 + 0.06 * math.sin(u * math.pi * 2 + z) * 0.5
            return (x, y, z), (0, 1, 0)
        rug = A.slab(sheet, 7, 9, 0.07, crease=60)
        deco = []
        # border bands (stand proud of the top) and a diamond motif
        for x in (-W / 2 + 0.18, W / 2 - 0.18):
            deco.append(box((0.14, 0.04, zb - za + (0.02 if i in (0, n - 1) else 0.0)), (x, y0 + 0.05, (za + zb) / 2), r=0.01))
        if i == 0:
            deco.append(box((W - 0.2, 0.04, 0.14), (0, y0 + 0.05, za + 0.18), r=0.01))
        if i == n - 1:
            deco.append(box((W - 0.2, 0.04, 0.14), (0, y0 + 0.05, zb - 0.18), r=0.01))
        deco.append(box((0.55, 0.04, 0.55), (0, y0 + 0.05, (za + zb) / 2), r=0.01, rot=(0, 45, 0)))
        deco.append(box((0.08, 0.04, 0.08 + zb - za - 0.4), (0, y0 + 0.055, (za + zb) / 2), r=0.01))
        if i in (0, n - 1):
            ze = za - 0.02 if i == 0 else zb + 0.02
            d = -1 if i == 0 else 1
            for x in np.linspace(-W / 2 + 0.15, W / 2 - 0.15, 7):
                deco.append(tube([[x, y0, ze], [x, y0 - 0.05, ze + d * 0.35]], 0.03, 4))
                deco.append(sphere(0.08, (x, y0 - 0.08, ze + d * 0.42), segs=8))
        name = "Hull" if i == 1 else f"Rug{i + 1}"
        dpiece(H, name, b, rug, col="primary", mat="cloth", role="body" if i == 1 else "tail", fallback="Block",
               pattern=lambda Q: 0.82 + 0.18 * np.cos((np.abs(Q[:, 0]) + np.abs(Q[:, 2] % 1.5 - 0.75)) * 9.0))
        dpiece(H, f"Pattern{i + 1}", b, merge(*deco), col="secondary", mat="cloth", role="detail")
    dpiece(H, "Seat", "Seg3", merge(box((1.3, 0.4, 1.1), (0, y0 + 0.25, 0.6), r=0.18), sphere(0.12, (0.6, y0 + 0.42, 0.1), segs=8), sphere(0.12, (-0.6, y0 + 0.42, 0.1), segs=8)),
           col=[0.75, 0.12, 0.2], mat="cloth", role="detail")
    dpiece(H, "Pillow", "Seg4", rev([(-0.6, 0), (-0.5, 0.25), (0.5, 0.25), (0.6, 0)], axis=0, segs=10, pos=(0, y0 + 0.3, 1.9), scale=(1, 1, 1.3)), col="secondary", mat="cloth", role="detail")
    common(H, (0, y0 + 0.5, 0.6), (1.3, 0.15, 1.1), -L / 2 - 0.5, L / 2 + 0.5, y0 + 2.5)
    segs = [f"Seg{i + 1}" for i in range(n)]
    H.rig["tail"] = segs[2:]

    def extra(name, u, pose):
        amp = 0.12 if name == "Move" else 0.07
        for i, b in enumerate(segs):
            if i == 0:
                continue
            A._add(pose, b, (0, 0, 0, amp * math.sin(TAU * (u * (2 if name == "Move" else 1) - i * 0.22)), 0, 0))

    A.air_clips(H, size=0.8, extra=extra, attack="ram", bank=0.3)
    return H


# ================================================================================================ broomstick
@hero("broomstick", "aircraft")
def broomstick():
    H = P("broomstick", tags=("vehicle", "magic"))
    H.preview = {"primary": "#8D6E63", "secondary": "#FFB300"}
    y0 = 1.6
    H.body((0, y0, 0))
    pts = [[0, y0 + 0.3, -3.3], [0.05, y0 + 0.22, -2.4], [-0.04, y0 + 0.1, -1.2], [0.03, y0 + 0.02, 0.0], [0.0, y0, 1.2]]
    handle = tube(pts, [0.07, 0.08, 0.085, 0.09, 0.09], 8)
    knob = merge(sphere(0.12, (0, y0 + 0.31, -3.35), segs=10), A.lathe([(-2.8, 0.0), (-2.8, 0.11), (-2.7, 0.11), (-2.7, 0.0)], axis=2, segs=10, pos=(0, y0 + 0.26, 0)))
    dpiece(H, "Hull", "Body", merge(handle, knob), col="primary", mat="wood", fallback="Block")
    # bristle bundle (straw sculpt) on a bone so it sways
    H.bone("Bristles", "Body", (0, y0, 1.2))
    rng = np.random.default_rng(3)
    br = round_cone((0, y0, 1.35), (0, y0 - 0.12, 3.15), 0.28, 0.62)
    for k in range(70):
        a = rng.uniform(0, TAU)
        rr = rng.uniform(0.55, 1.0)
        c0 = (0.24 * rr * math.cos(a), y0 + 0.24 * rr * math.sin(a), 1.45)
        L = rng.uniform(3.2, 3.55)
        tip = (0.72 * rr * math.cos(a) + rng.normal(0, 0.04), y0 - 0.12 + 0.68 * rr * math.sin(a) + rng.normal(0, 0.04), L)
        br = br | round_cone(c0, tip, 0.06, 0.03)
    H.piece("BristleP", "Bristles", br, col=[0.86, 0.68, 0.32], mat="wood", tris=2600, res=150, role="tail", smooth=2,
            pattern=lambda Q: 0.8 + 0.2 * np.cos(np.arctan2(Q[:, 1] - y0, Q[:, 0]) * 23.0))
    dpiece(H, "Binding", "Body", merge(A.lathe([(1.15, 0.0), (1.15, 0.27), (1.45, 0.3), (1.45, 0.0)], axis=2, segs=14, pos=(0, y0, 0)),
                                       A.lathe([(1.55, 0.31), (1.68, 0.33), (1.68, 0.25), (1.55, 0.23)], axis=2, segs=14, pos=(0, y0, 0), closed=True)), col="secondary", mat="cloth", role="detail")
    # rider's saddle, foot pegs, a hanging lantern
    dpiece(H, "Seat", "Body", merge(rev([(-0.55, 0), (-0.45, 0.2), (0.3, 0.24), (0.55, 0)], axis=2, segs=10, pos=(0, y0 + 0.14, -0.1), scale=(1.2, 0.6, 1))),
           col="leather", mat="cloth", role="detail")
    dpiece(H, "Pegs", "Body", merge(tube([[-0.45, y0 - 0.35, 0.6], [0, y0 - 0.02, 0.55], [0.45, y0 - 0.35, 0.6]], 0.04, 6), box((0.2, 0.05, 0.2), (0.48, y0 - 0.37, 0.6), r=0.02), box((0.2, 0.05, 0.2), (-0.48, y0 - 0.37, 0.6), r=0.02)),
           col="metal", mat="metal", role="detail")
    H.bone("Lantern", "Body", (0, y0 + 0.2, -2.6))
    dpiece(H, "LanternP", "Lantern", merge(tube([[0, y0 + 0.2, -2.6], [0, y0 - 0.25, -2.6]], 0.02, 4), A.lathe([(y0 - 0.3, 0.0), (y0 - 0.3, 0.16), (y0 - 0.65, 0.16), (y0 - 0.7, 0.0)], axis=1, segs=6, pos=(0, 0, -2.6))),
           col="dark", mat="metal", role="detail")
    H.prim("LanternGlow", "Lantern", "Ball", (0.2, 0.25, 0.2), (0, y0 - 0.48, -2.6), col="glow", glow=True, role="light", pri=2.4)
    common(H, (0, y0 + 0.35, -0.1), (0.5, 0.15, 0.9), -3.6, 3.5, y0 + 2.5)
    H.rig["tail"] = ["Bristles"]

    def extra(name, u, pose):
        k = 1.0 if name == "Move" else 0.4
        A._add(pose, "Bristles", (0, 0, 0, 0.06 * k * math.sin(TAU * u * 2), 0.1 * k * math.sin(TAU * u), 0))
        A._add(pose, "Lantern", (0, 0, 0, 0.25 * k * math.sin(TAU * u + 1), 0, 0.15 * math.sin(TAU * u)))

    A.air_clips(H, size=0.6, extra=extra, attack="roll", bank=0.5)
    return H


# ================================================================================================ cloud ride
@hero("cloud surfboard", "aircraft")
def cloud_surfboard():
    H = P("cloud surfboard", gait="hover", tags=("vehicle", "magic"))
    H.preview = {"primary": "#FFFFFF", "secondary": "#40C4FF"}
    y0 = 1.3
    H.body((0, y0, 0))
    rng = np.random.default_rng(7)
    cl = ellipsoid(2.2, 0.75, 3.2, (0, y0, 0))
    puffs = [(1.4, 0.2, -1.8, 0.95), (-1.5, 0.15, -1.2, 1.0), (1.6, 0.1, 1.2, 1.05), (-1.4, 0.2, 1.8, 0.95), (0.0, 0.2, -2.8, 0.9), (0.0, 0.1, 3.0, 0.95),
             (0.8, -0.35, 0.0, 1.0), (-0.9, -0.3, 0.4, 0.95), (2.2, -0.2, -0.2, 0.8), (-2.2, -0.2, -0.3, 0.8), (0.6, 0.45, -0.9, 0.85), (-0.6, 0.4, 1.0, 0.85)]
    for x, y, z, r in puffs:
        cl = cl.su(ssphere(r, (x, y0 + y, z)), 0.35)
    cl = cl & plane((0, -1, 0), -0.05)
    H.piece("Hull", "Body", cl, col="primary", mat="cloth", tris=2400, res=120, role="body",
            pattern=lambda Q: 0.8 + 0.2 * np.clip((Q[:, 1] - y0 + 0.6) / 1.2, 0, 1))
    # wisps trailing behind on bones
    for i, (x, z) in enumerate(((0.9, 3.4), (-0.9, 3.3))):
        b = H.bone(f"Wisp{i + 1}", "Body", (x, y0, z))
        w = stube([(x, y0, z), (x * 1.2, y0 + 0.1, z + 1.0), (x * 1.5, y0 + 0.3, z + 1.9)], [0.6, 0.4, 0.15], k=0.2)
        H.piece(f"WispP{i + 1}", b, w, col="primary", mat="cloth", tris=700, role="tail")
    # surfboard riding on top (the seat)
    def bd(t, u):
        z = -2.5 + 5.0 * t
        hw = 0.62 * math.sin(math.pi * min(max(t, 0.0), 1.0)) ** 0.55 + 0.02
        x = -hw + 2 * hw * u
        y = y0 + 1.05 + 0.25 * max(0, (0.25 - t)) * 4 * 0.35 + 0.02 * math.cos(math.pi * (u - 0.5))
        return (x, y, z), (0, 1, 0)
    dpiece(H, "Seat", "Body", A.slab(bd, 12, 7, 0.14, crease=60), col="secondary", mat="hard", role="detail")
    dpiece(H, "BoardStripe", "Body", merge(box((0.12, 0.05, 4.2), (0, y0 + 1.15, 0.0), r=0.02), A.fin(0.4, 0.5, 0.25, 0.2, thick=0.05, pos=(0, y0 + 1.15, 1.6))), col="white", role="detail")
    H.mprim("Sparkle#", "Body", "Ball", (0.18, 0.18, 0.18), (1.9, y0 + 0.9, -1.5), col="glow", glow=True, role="light", pri=2.6)
    common(H, (0, y0 + 1.25, 0.2), (1.0, 0.15, 3.0), -3.6, 4.2, y0 + 3.0)
    H.rig["tail"] = ["Wisp1", "Wisp2"]

    def extra(name, u, pose):
        for i, b in enumerate(("Wisp1", "Wisp2")):
            A._add(pose, b, (0, 0, 0, 0.12 * math.sin(TAU * u + i), 0.15 * math.sin(TAU * u * (2 if name == "Move" else 1) + i * 1.3), 0))

    A.air_clips(H, size=0.7, extra=extra, attack="ram", hover=True, bank=0.25)
    return H


# ================================================================================================ sleigh
@hero("sleigh", "aircraft")
def sleigh():
    H = P("sleigh", tags=("vehicle", "magic"))
    H.preview = {"primary": "#C62828", "secondary": "#FFD700"}
    H.body((0, 1.6, 0))
    # body: side profile (scroll front, high back) extruded across the width, as stacked rings
    side = [(-2.2, 1.3), (-2.0, 1.0), (-1.2, 0.9), (1.4, 0.9), (1.9, 1.05), (2.0, 1.6), (1.9, 2.9), (1.4, 3.1), (0.9, 2.3), (-0.4, 2.0), (-1.4, 2.1), (-2.0, 2.6), (-2.5, 2.7), (-2.6, 2.3), (-2.35, 2.05)]
    W = 1.35
    rings = []
    for x in (-W, -W + 0.1, W - 0.1, W):
        s = 1.0 if abs(x) < W - 0.05 else 0.96
        rings.append(np.array([[x, y * s + (1 - s) * 1.8, z * s] for z, y in side]))
    body = A.loft(rings, "fan", "fan", crease=40)
    dpiece(H, "Hull", "Body", body, col="primary", mat="wood", fallback="Block")
    # gold trim scrolls on the sides
    trim = []
    for sx in (1, -1):
        trim.append(tube([[sx * (W + 0.03), y, z] for z, y in side[:12]], 0.07, 6, closed_ends=True))
        trim.append(tube([[sx * (W + 0.03), 1.6 + 0.35 * math.sin(a), -0.3 + 0.5 * math.cos(a)] for a in np.linspace(0, TAU * 0.85, 10)], 0.05, 5))
    dpiece(H, "Trim", "Body", merge(*trim), col="secondary", mat="metal", role="detail")
    # curled runners + struts
    run = []
    for sx in (1, -1):
        x = sx * (W - 0.15)
        pts = [[x, 0.12, 2.2], [x, 0.08, 1.0], [x, 0.08, -1.6], [x, 0.3, -2.6], [x, 0.9, -3.1], [x, 1.35, -2.8], [x, 1.25, -2.4], [x, 1.0, -2.5]]
        run.append(tube(pts, 0.09, 7))
        for z in (-1.2, 0.3, 1.6):
            run.append(tube([[x, 0.1, z], [x, 0.95, z]], 0.06, 6))
    dpiece(H, "Runners", "Body", merge(*run), col="secondary", mat="metal", role="detail")
    dpiece(H, "Seat", "Body", merge(box((2.4, 0.4, 1.4), (0, 1.15, 0.6), r=0.18), box((2.4, 1.0, 0.35), (0, 1.75, 1.45), r=0.15, rot=(-10, 0, 0))), col="cream", mat="cloth", role="detail")
    # gift sack + presents in the back, bells on a harness bar
    sack = ellipsoid(0.75, 0.9, 0.7, (0.3, 2.4, 1.7)).su(round_cone((0.3, 3.0, 1.7), (0.35, 3.5, 1.75), 0.25, 0.12), 0.2).noise(0.03, 3.0, 4)
    H.piece("Sack", "Body", sack, col=[0.55, 0.38, 0.22], mat="cloth", tris=900, role="detail")
    dpiece(H, "Presents", "Body", merge(box((0.6, 0.55, 0.6), (-0.65, 2.25, 1.75), r=0.03, rot=(0, 15, 0)), box((0.5, 0.45, 0.5), (-0.6, 2.75, 1.7), r=0.03, rot=(0, -10, 0))), col=[0.2, 0.55, 0.3], role="detail")
    dpiece(H, "Ribbons", "Body", merge(box((0.62, 0.57, 0.12), (-0.65, 2.25, 1.75), r=0.02, rot=(0, 15, 0)), box((0.12, 0.47, 0.52), (-0.6, 2.75, 1.7), r=0.02, rot=(0, -10, 0))), col="secondary", role="detail", pri=2)
    H.bone("Bells", "Body", (0, 1.9, -2.6))
    bells = [tube([[-1.2, 1.9, -2.6], [1.2, 1.9, -2.6]], 0.05, 6)]
    for x in np.linspace(-0.9, 0.9, 5):
        bells.append(A.lathe([(1.82, 0.0), (1.82, 0.14), (1.6, 0.11), (1.5, 0.0)], axis=1, segs=10, pos=(x, 0, -2.6)))
    dpiece(H, "BellsP", "Bells", merge(*bells), col="gold", mat="metal", role="detail")
    common(H, (0, 1.4, 0.6), (2.2, 0.15, 1.3), -3.3, 2.5, 3.5)

    def extra(name, u, pose):
        A._add(pose, "Bells", (0, 0, 0, 0.15 * math.sin(TAU * u * 2), 0, 0.08 * math.sin(TAU * u * 2 + 1)))

    A.air_clips(H, size=0.8, extra=extra, attack="ram", bank=0.3)
    return H


# ================================================================================================ chariot of fire
@hero("chariot of fire", "aircraft")
def chariot_of_fire():
    H = P("chariot of fire", tags=("vehicle", "magic"))
    H.preview = {"primary": "#FF6F00", "secondary": "#FFD54F"}
    H.body((0, 1.5, 0))
    # car: a curved front breastwork open at the back, gold rim
    rings = []
    for k, y in enumerate((0.75, 1.0, 1.9, 2.2)):
        f = 1.0 if k < 3 else 0.92
        pts = []
        for a in np.linspace(math.radians(-100), math.radians(100), 13):
            rr = 1.05 * f + (0.15 * (y - 0.75) if k else 0)
            pts.append([rr * math.sin(a), y, -rr * math.cos(a) * 0.9 + 0.2])
        rings.append(np.array(pts))
    outer = rings
    shell_rings = []
    for r in outer:
        inner = r.copy()
        inner[:, 0] *= 0.9
        inner[:, 2] = (inner[:, 2] - 0.2) * 0.9 + 0.2
        shell_rings.append(np.vstack([r, inner[::-1]]))
    shell = A.loft(shell_rings, "strip", "strip", crease=45)
    floor = box((2.2, 0.15, 1.8), (0, 0.7, 0.35), r=0.05)
    dpiece(H, "Hull", "Body", merge(shell, floor), col="primary", mat="metal", fallback="Block")
    rim = tube([[1.03 * math.sin(a), 2.22, -1.03 * math.cos(a) * 0.9 + 0.2] for a in np.linspace(math.radians(-100), math.radians(100), 13)], 0.07, 6)
    sun = A.lathe([(-0.05, 0.0), (-0.05, 0.42), (0.05, 0.42), (0.05, 0.0)], axis=2, segs=16, pos=(0, 1.55, -0.98))
    dpiece(H, "Trim", "Body", merge(rim, sun, *[tube([[0, 1.55, -1.02], [0.75 * math.cos(a), 1.55 + 0.6 * math.sin(a), -0.95]], 0.04, 4) for a in np.linspace(0, TAU, 10, endpoint=False)]),
           col="secondary", mat="metal", role="detail")
    # two big spoked wheels on bones
    wr = 1.1
    for s, nm in ((1, "R"), (-1, "L")):
        H.bone(f"Wheel{nm}", "Body", (s * 1.35, wr, 0.4))
        sp = [A.lathe([(-0.12, wr), (0.12, wr), (0.12, wr - 0.14), (-0.12, wr - 0.14)], axis=0, segs=20, closed=True), cyl(0.2, 0.4, (0, 0, 0), axis=0, segs=10)]
        for a in np.linspace(0, TAU, 8, endpoint=False):
            sp.append(tube([[0, 0, 0], [0, (wr - 0.1) * math.sin(a), (wr - 0.1) * math.cos(a)]], 0.045, 5))
        dpiece(H, f"WheelP{nm}", f"Wheel{nm}", A.direct.moved(merge(*sp), (s * 1.35, wr, 0.4)), col="secondary", mat="metal", role="detail")
    dpiece(H, "Axle", "Body", merge(cyl(0.08, 2.8, (0, wr, 0.4), axis=0, segs=8), tube([[0, 0.8, -0.6], [0, 1.2, -3.4], [0, 1.45, -3.6]], 0.08, 6), tube([[-0.8, 1.25, -3.2], [0.8, 1.25, -3.2]], 0.06, 6)),
           col="secondary", mat="metal", role="detail")
    # flames: a fiery fringe along the back and wheels (small, flame-coloured sculpts; not glowing bodies)
    def flame(base, up, back, r, wob):
        bx, by, bz = base
        return stube([(bx, by, bz), (bx + wob, by + up * 0.45, bz + back * 0.35), (bx - wob * 0.6, by + up * 0.8, bz + back * 0.75), (bx + wob * 0.3, by + up, bz + back)],
                     [r, r * 0.8, r * 0.45, r * 0.08], k=0.12)
    fl = None
    for i, x in enumerate(np.linspace(-0.85, 0.85, 5)):
        f = flame((x, 0.9, 1.25), 1.1 + 0.4 * math.cos(x * 2.5), 1.3 + 0.2 * (i % 2), 0.28, 0.12 * (-1) ** i)
        fl = f if fl is None else fl.su(f, 0.12)
    H.bone("Flames", "Body", (0, 0.9, 1.2))
    H.piece("FlamesP", "Flames", fl, col="flame", mat="hard", tris=1600, role="tail",
            pattern=lambda Q: 0.75 + 0.25 * np.clip((Q[:, 1] - 0.9) / 1.4, 0, 1))
    for nm, s_ in (("R", 1), ("L", -1)):
        f2 = None
        for k in range(3):
            a_ = 0.9 + k * 0.6
            base = (s_ * 1.42, wr + (wr - 0.1) * math.sin(a_), 0.4 + (wr - 0.1) * math.cos(a_))
            f = flame(base, 0.7, 1.1, 0.2, 0.08 * (-1) ** k)
            f2 = f if f2 is None else f2.su(f, 0.08)
        H.piece(f"WheelFire{nm}", "Body", f2, col="flame", mat="hard", tris=800, role="detail")
    H.prim("Core", "Body", "Ball", (0.4, 0.4, 0.4), (0, 1.55, -1.05), col="flameCore", glow=True, role="light", pri=2.4)
    dpiece(H, "Seat", "Body", merge(box((1.4, 0.5, 0.7), (0, 1.0, 0.7), r=0.12), box((1.5, 0.12, 0.8), (0, 1.3, 0.7), r=0.05)), col="secondary", mat="cloth", role="detail")
    common(H, (0, 1.45, 0.7), (1.4, 0.15, 0.7), -3.8, 2.6, 3.2)
    H.rig["tail"] = ["Flames"]
    spins = [("WheelR", "x", -1, TAU / 8), ("WheelL", "x", -1, TAU / 8)]

    def extra(name, u, pose):
        A._add(pose, "Flames", (0, 0, 0, 0.1 * math.sin(TAU * u * 3), 0.12 * math.sin(TAU * u * 2), 0))

    A.air_clips(H, size=0.8, spinners=spins, extra=extra, attack="ram", bank=0.3)
    return H


# ================================================================================================ word map
MAP = [
    ("propeller plane", "propeller plane, prop plane, bush plane, skywriter plane, stunt plane, microlight, toy airplane, air ambulance plane, water bomber, autogyro", B),
    ("seaplane", "seaplane, float plane, floatplane, flying boat", B),
    ("biplane", "biplane, bi plane, crop duster, triplane, ornithopter", B),
    ("jet", "jet, fighter jet, fighter plane, jet fighter, warplane, stealth bomber, spy plane, hypersonic jet, fighter squadron, stunt plane team", B),
    ("jumbo jet", "jumbo jet, wide body jet, cargo plane", B),
    ("airplane", "!paper airplane, airplane, aeroplane, plane, aircraft, airliner, passenger jet", B),
    ("private jet", "private jet, business jet", B),
    ("glider", "glider, sailplane, hang glider, paraglider, wingsuit", B),
    ("helicopter", "!attack helicopter, helicopter, chopper, copter, heli, rescue helicopter, police helicopter, cargo helicopter, tiltrotor, sky taxi, whirlybird", B),
    ("hot air balloon", "hot air balloon, balloon basket, balloon cluster, lawn chair balloon", B),
    ("blimp", "blimp, airship, zeppelin, dirigible", B),
    ("flying carpet", "flying carpet, magic carpet rug, magic carpet, flying rug, magic rug", B),
    ("broomstick", "broomstick, broom, witch broom, flying broom, witches broom", B),
    ("cloud surfboard", "cloud surfboard, cloud board, sky board, rainbow road ride, cloud ride, cloud car, magic bubble", B),
    ("sleigh", "sleigh, santa sleigh, flying sleigh, reindeer sleigh, enchanted sled", B),
    ("chariot of fire", "chariot of fire, fire chariot, flaming chariot, sun chariot, crystal chariot, dragon chariot", B),
]
