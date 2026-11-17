"""Summon set: the tank hull hero sculpt (hard surface, built directly).

Modelled in model space on refs.json "sig:tank" (+Y up, -Z front, studs): an armoured upper hull whose glacis lies
exactly on the Glacis wedge, the tub between the tracks with sloped nose and tail plates, turret ring, driver's
hatch with periscopes, engine deck grilles, exhausts, tow shackles, a rear access plate and bolt rows. Tracks,
wheels, fenders, skirts, turret, gun, lamps and drums stay the builder's parts. One "unit" sculpt in the frame of
the Hull block (member: the Glacis). Assigned in Signatures/Machines.luau (S.tank).
"""
import numpy as np

import direct
from .refs import Group
from .s_castle import cube, _unit

W = "sig:tank"
G = Group(W, "Hull", ["Glacis"])


def prism(profile, x0, x1):
    """Convex (z, y) profile extruded from x0 to x1, flat shaded."""
    P = np.array(profile, float)
    c = P.mean(0)
    V, N, F = [], [], []

    def tri(a, b, cc):
        n = np.cross(np.subtract(b, a), np.subtract(cc, a))
        ln = np.linalg.norm(n)
        if ln < 1e-12:
            return
        base = len(V)
        V.extend([a, b, cc])
        N.extend([n / ln] * 3)
        F.append([base, base + 1, base + 2])

    def pt(x, q):
        return (x, q[1], q[0])
    n = len(P)
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        mid = pt((x0 + x1) / 2, (a + b) / 2)
        out = np.array(mid) - np.array(pt((x0 + x1) / 2, c))
        quad = [pt(x0, a), pt(x1, a), pt(x1, b), pt(x0, b)]
        if np.cross(np.subtract(quad[1], quad[0]), np.subtract(quad[2], quad[0])) @ out < 0:
            quad = quad[::-1]
        tri(quad[0], quad[1], quad[2])
        tri(quad[0], quad[2], quad[3])
        for x, sg in ((x0, -1), (x1, 1)):
            t = [pt(x, c), pt(x, a), pt(x, b)]
            if np.cross(np.subtract(t[1], t[0]), np.subtract(t[2], t[0]))[0] * sg < 0:
                t = [t[0], t[2], t[1]]
            tri(*t)
    return direct._finish(np.array(V), np.array(N), np.array(F))


def drum(a, b, r, segs=10):
    """Bevelled cylinder from a to b (axis-aligned)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ax = int(np.argmax(np.abs(b - a)))
    return direct.moved(direct.bevel_cylinder(float(np.abs(b - a)[ax]), r, min(0.05, r * 0.3), segs, axis=ax), offset=tuple((a + b) / 2))


@_unit("s_tank_hull", G, 900, "Tank hull (lead Hull, member Glacis): armoured upper hull with the glacis plate, tub between the tracks, turret ring, "
       "driver's hatch and periscopes, engine grilles, exhausts, tow shackles, rear plate, bolt rows.")
def hull():
    HX, TOP = 3.145, 5.245
    m = [prism([(-7.98, 2.72), (-5.18, TOP), (5.97, TOP), (5.97, 2.7), (-7.7, 2.45)], -HX, HX)]
    m.append(prism([(-7.35, 2.6), (-6.3, 1.72), (5.3, 1.72), (5.95, 2.5), (5.95, 2.8), (-7.35, 2.8)], -2.5, 2.5))    # tub
    m.append(drum((0, TOP - 0.05, 0.75), (0, TOP + 0.2, 0.75), 2.55, 20))                                           # turret ring
    # driver's hatch and periscopes, forward of the turret
    m.append(drum((-1.45, TOP - 0.02, -3.75), (-1.45, TOP + 0.13, -3.75), 0.62, 12))
    m.append(cube((0.5, 0.12, 0.16), (-1.45, TOP + 0.19, -3.5)))
    for x in (-1.95, -1.45, -0.95):
        m.append(cube((0.36, 0.2, 0.2), (x, TOP + 0.09, -4.6)))
    m.append(cube((1.3, 0.1, 1.0), (1.4, TOP + 0.04, -3.9)))                                                         # stowage plate
    for x in (0.95, 1.85):
        m.append(cube((0.1, 0.16, 0.9), (x, TOP + 0.1, -3.9)))
    # engine deck: two grilles with slats, between the turret and the fuel drums
    for sx in (-1, 1):
        m.append(cube((1.9, 0.12, 1.05), (sx * 1.45, TOP + 0.05, 4.25)))
        for i in range(5):
            m.append(cube((1.7, 0.07, 0.1), (sx * 1.45, TOP + 0.14, 3.85 + i * 0.2)))
        m.append(drum((sx * 2.05, 4.35, 5.9), (sx * 2.05, 4.35, 6.55), 0.26, 10))                                     # exhausts
        m.append(drum((sx * 2.05, 4.35, 6.5), (sx * 2.05, 4.35, 6.62), 0.33, 10))
        m.append(cube((0.26, 0.42, 0.3), (sx * 1.9, 2.75, -7.75)))                                                    # tow shackles
        m.append(cube((0.26, 0.42, 0.3), (sx * 1.9, 2.95, 6.05)))
        for i in range(6):                                                                                            # bolt rows along the top edges
            m.append(cube((0.12, 0.07, 0.12), (sx * (HX - 0.22), TOP + 0.03, -4.4 + i * 1.9)))
    m.append(cube((3.4, 1.1, 0.12), (0, 4.05, 6.0)))                                                                  # rear access plate
    for x in (-1.4, 1.4):
        for y in (3.65, 4.45):
            m.append(cube((0.12, 0.12, 0.08), (x, y, 6.08)))
    m.append(cube((2.2, 0.16, 0.16), (0, 3.2, 6.05)))                                                                 # tow bar
    # glacis: a raised centre plate on the slope and a splash strip at its top
    sl = np.array((2.8, 2.53))
    sl /= np.linalg.norm(sl)
    for t, wdt, hgt in ((1.9, 3.0, 1.3),):
        z, y = -7.98 + sl[0] * t, 2.72 + sl[1] * t
        ang = np.arctan2(sl[1], sl[0])
        pl = cube((wdt, 0.08, hgt), (0, 0, 0))
        cs, sn = np.cos(ang), np.sin(ang)
        R = np.array([[1, 0, 0], [0, cs, sn], [0, -sn, cs]])
        m.append(direct.moved(pl, rot=R, offset=(0, y + 0.03 * cs, z - 0.03 * sn)))
    m.append(cube((2 * HX - 0.3, 0.14, 0.14), (0, TOP + 0.04, -5.0)))
    return direct.merge(*m)
