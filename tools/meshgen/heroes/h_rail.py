"""Rail vehicles (land-vehicle mounts): steam train (locomotive), train (diesel locomotive), bullet train, tram, mine
cart, handcar, roller coaster car. Flanged rail wheels on their own bones; the steam engine's coupling rods ride a
crank circle on their own bones (they orbit without rotating, like the real thing) while the drivers spin.
"""
import math

import numpy as np

from kit import hero, Hero
from map import VEH
import landveh_kit as K
from landveh_kit import box, cbox, cyl, bar, rod, extrude, warp, merge, mirror, xf, lamp, piece, mpiece, round_poly

FAM = "rail"
TAU = 2 * math.pi
RED_L = [0.85, 0.08, 0.08]
LENS = [1.0, 0.95, 0.8]


def pv(p, s, **kw):
    d = {"primary": p, "secondary": s, "glass": "#33414F", "darker": "#24262B"}
    d.update(kw)
    return d


def _new(hid, preview, tags=("vehicle", "train")):
    H = Hero(hid, plan="Vehicle", gait="drive", tags=list(tags))
    H.preview = preview
    return H


def rail_wheel(r, w=0.22, spokes=0, counter=False, segs=22):
    """Flanged rail wheel about X (outer face +X): tread, inner flange, dished centre (+ spokes / counterweight)."""
    prof = [(w / 2, 0), (w / 2, r * 0.25), (w * 0.3, r * 0.8), (w / 2, r * 0.86), (w / 2, r), (-w / 2, r * 1.02), (-w / 2 - 0.02, r * 1.14), (-w / 2 - 0.08, r * 1.14),
            (-w / 2 - 0.08, r * 0.9), (-w / 2, r * 0.7), (-w / 2, 0)]
    m = K.lathe_profile(prof, segs, "x")
    parts = [m]
    if spokes:
        parts = [K.lathe_profile([(w / 2, r * 0.78), (w / 2, r * 1.0), (-w / 2, r * 1.02), (-w / 2 - 0.02, r * 1.12), (-w / 2 - 0.08, r * 1.12),
                                  (-w / 2 - 0.08, r * 0.78)], segs, "x", closed=True, hard_deg=40),
                 K.lathe_profile([(w * 0.7, 0), (w * 0.7, r * 0.18), (-w / 2, r * 0.2), (-w / 2, 0)], 12, "x")]
        for k in range(spokes):
            a = TAU * k / spokes
            d = np.array([0, math.cos(a), math.sin(a)])
            parts.append(bar(d * r * 0.15, d * r * 0.82, r * 0.08, w * 0.5, r=0.02, up=(1, 0, 0)))
        if counter:
            ang = np.linspace(-0.6, 0.6, 7)
            pts = [(r * 0.78 * math.cos(a), r * 0.78 * math.sin(a)) for a in ang] + [(r * 0.25 * math.cos(a), r * 0.25 * math.sin(a)) for a in ang[::-1]]
            cw = extrude(np.array(pts), w * 0.55, bevel=0.02, axis="x", seg=1)
            parts.append(xf(cw, (0, 0, 0), r=(90, 0, 0)))
    return merge(*parts)


def _wheelset(H, parent, name, z, r, gauge, y=None, spokes=0, counter=False, col="metal"):
    y = r if y is None else y
    out = []
    for s, tag in ((1, "R"), (-1, "L")):
        b = H.bone(name + tag, parent, (s * gauge, y, z))
        m = rail_wheel(r, spokes=spokes, counter=counter)
        if s < 0:
            m = mirror(m)
        piece(H, name + tag, b, xf(m, (s * gauge, y, z)), col=col, mat="metal", role="wheel", pri=1.0, fallback="Cylinder")
        out.append((b, r))
    return out


def _finish(H, wheels, height, length, seat_pos, seat_size, nose, tail, sym=12, **kw):
    K.mount(H, "Seat", seat_pos, seat_size, "Chassis")
    H.socket("head", (0, height + 0.3, 0), "Chassis")
    H.socket("mouth", nose, "Chassis")
    H.socket("exhaust", tail, "Chassis")
    H.rig.update({"head": "Chassis"})
    K.vehicle_clips(H, wheels, susp="Chassis", height=height, length=length, sym=sym, roll=0.4, bob=0.5, **kw)


def _bogie(H, z, r=0.5, gauge=1.25, wb=1.4, col="darker"):
    frame = merge(*[bar((s * (gauge + 0.25), r, z - wb / 2 - 0.5), (s * (gauge + 0.25), r, z + wb / 2 + 0.5), 0.18, 0.5, r=0.05) for s in (-1, 1)],
                  box((2 * gauge + 0.3, 0.3, 0.8), (0, r + 0.2, z), r=0.05),
                  *[cyl(0.3, 0.16, (s * (gauge + 0.4), r + 0.05, z + dz), "y", segs=8) for s in (-1, 1) for dz in (-0.3, 0.3)])
    return frame


# ==================================================================================================== steam
@hero("steam train", FAM)
def steam_train():
    H = _new("steam train", pv("#1C1C1E", "#B22222", darker="#141416"))
    gauge = 1.25
    H.bone("Chassis", "Body", (0, 1.3, 0))
    # drivers (3 per side) + pony truck
    drivers = []
    dz = (-0.7, 1.0, 2.7)
    R = 0.95
    for i, z in enumerate(dz):
        drivers += _wheelset(H, "Body", f"Driver{i}", z, R, gauge, spokes=12, counter=True, col="secondary")
    pony = _wheelset(H, "Body", "Pony", -3.0, 0.5, gauge, col="secondary")
    # boiler
    bz0, bz1 = -4.6, 2.2
    by = 2.75
    boiler = xf(K.lathe_profile([(bz0, 0), (bz0, 0.95), (bz0 + 0.1, 1.05), (bz1, 1.05), (bz1, 0)], 26, "z"), (0, by, 0))
    bands = merge(*[xf(K.torus(1.07, 0.035, "z", 26, 4), (0, by, z)) for z in np.linspace(bz0 + 1.0, bz1 - 0.3, 4)])
    smoke = xf(K.lathe_profile([(bz0 - 0.15, 0), (bz0 - 0.15, 0.8), (bz0 - 0.05, 1.0), (bz0 + 0.9, 1.0), (bz0 + 0.9, 0)], 24, "z"), (0, by, 0))
    piece(H, "Chassis", "Chassis", merge(boiler, smoke), col="primary", mat="metal", pri=0.4)
    piece(H, "Bands", "Chassis", bands, col="gold", mat="metal", role="detail", pri=1.5)
    chim = xf(K.lathe_profile([(0, 0), (0, 0.32), (0.9, 0.26), (1.2, 0.4), (1.35, 0.42), (1.4, 0.3), (1.4, 0)], 18, "y"), (0, by + 0.85, bz0 + 0.45))
    dome = xf(K.D.revolve([(0, 0), (0.05, 0.42), (0.35, 0.42), (0.6, 0.25), (0.7, 0)], segs=16, axis=1, spline=3), (0, by + 0.95, -1.2))
    sand = xf(K.D.revolve([(0, 0), (0.05, 0.34), (0.25, 0.34), (0.45, 0.2), (0.52, 0)], segs=14, axis=1, spline=3), (0, by + 0.95, 0.3))
    piece(H, "Chimney", "Chassis", chim, col="darker", mat="metal", role="detail", pri=0.9)
    piece(H, "Domes", "Chassis", merge(dome, sand), col="gold", mat="metal", role="detail", pri=1.0)
    # front: smokebox door, lamp, buffer beam, cowcatcher, cylinders
    door = xf(K.D.revolve([(0, 0), (0.0, 0.7), (-0.12, 0.6), (-0.2, 0)], segs=20, axis=2, spline=2), (0, by, bz0 - 0.15))
    lampm = merge(cbox((0.45, 0.45, 0.4), (0, by + 1.15, bz0 + 0.1), c=0.05))
    piece(H, "SmokeDoor", "Chassis", merge(door, lampm), col="darker", mat="metal", role="detail", pri=1.1)
    piece(H, "Headlight", "Chassis", K.lamp((0, by + 1.15, bz0 - 0.12), 0.15, 0.08), col=LENS, mat="glass", role="light", pri=1.4, ao=False)
    beam = box((3.2, 0.5, 0.3), (0, 1.1, bz0 - 0.35), r=0.05)
    buffers = merge(*[cyl(0.45, 0.17, (s * 1.0, 1.1, bz0 - 0.7), "z", segs=12) for s in (-1, 1)])
    cc = []
    for k in range(7):
        x = -1.2 + 0.4 * k
        cc.append(bar((x, 1.0, bz0 - 0.5), (x * 0.6, 0.12, bz0 - 1.5), 0.08, 0.08))
    cc.append(bar((-1.2, 0.15, bz0 - 1.45), (1.2, 0.15, bz0 - 1.45), 0.1, 0.12))
    piece(H, "Cowcatcher", "Chassis", merge(beam, *cc), col="secondary", mat="metal", role="detail", pri=0.9)
    piece(H, "Buffers", "Chassis", buffers, col="metal", mat="metal", role="detail", pri=1.5)
    cyls = merge(*[cyl(1.2, 0.42, (s * 1.45, 1.25, -2.0), "z", segs=16) for s in (-1, 1)])
    frame = merge(*[box((0.15, 0.55, 7.6), (s * 1.05, 1.3, -0.9), r=0.03) for s in (-1, 1)], *[box((0.6, 0.1, 6.2), (s * 1.6, 1.85, -0.9), r=0.02) for s in (-1, 1)])
    piece(H, "Cylinders", "Chassis", cyls, col="darker", mat="metal", role="detail", pri=1.0)
    piece(H, "Frame", "Chassis", frame, col="darker", mat="metal", role="detail", pri=1.0)
    # cab
    cz0, cz1 = 2.2, 4.4
    cp = np.array([(cz0, 1.55), (cz0, 4.6), (cz1, 4.6), (cz1, 1.55)])
    cab = extrude(round_poly(cp, [0.05, 0.1, 0.1, 0.05], 2), 3.0, bevel=0.08)
    piece(H, "Cab", "Chassis", cab, col="primary", mat="metal", role="body", pri=0.6)
    roof = K.box((3.4, 0.15, 2.8), (0, 4.72, 3.3), r=0.07)
    roof = warp(roof, lambda V: np.column_stack([V[:, 0], V[:, 1] + 0.18 * (1 - (V[:, 0] / 1.7) ** 2), V[:, 2]]))
    wins = merge(*[cbox((0.05, 0.85, 1.0), (s * 1.51, 3.65, 3.3), c=0.03) for s in (-1, 1)], *[cbox((0.7, 0.7, 0.05), (s * 0.85, 3.85, cz0 - 0.01), c=0.03) for s in (-1, 1)])
    piece(H, "Roof", "Chassis", roof, col="secondary", mat="metal", role="detail", pri=0.8)
    piece(H, "Windows", "Chassis", wins, col="glass", mat="glass", role="window", pri=1.2)
    seat = K.seat_mesh((-0.8, 2.45, 3.6), w=0.8, d=0.7, back=0.8)
    piece(H, "Seat", "Chassis", seat, col="darkWood", mat="wood", role="seat", pri=1.2)
    coal = K.box((2.6, 0.7, 1.2), (0, 2.0, 5.0), r=0.1)
    coal = warp(coal, lambda V: np.column_stack([V[:, 0], V[:, 1] + 0.18 * np.sin(V[:, 0] * 6) * np.sin(V[:, 2] * 7) * (V[:, 1] > 2.2), V[:, 2]]))
    bunker = box((3.0, 1.1, 1.4), (0, 1.75, 5.0), r=0.08)
    piece(H, "Bunker", "Chassis", bunker, col="primary", mat="metal", role="body", pri=0.9)
    piece(H, "Coal", "Chassis", coal, col=[0.12, 0.12, 0.13], mat="stone", role="detail", pri=1.4)
    bell = merge(xf(K.lathe_profile([(-0.25, 0.0), (-0.25, 0.22), (0.05, 0.14), (0.2, 0.08), (0.25, 0)], 12, "y"), (0, by + 1.3, -0.4)),
                 rod((0, by + 1.0, -0.4), (0, by + 1.15, -0.4), 0.04, segs=6), xf(K.lathe_profile([(0, 0.07), (0.45, 0.07), (0.5, 0)], 8, "y"), (0.4, by + 1.0, 1.6)))
    piece(H, "Bell", "Chassis", bell, col="gold", mat="metal", role="detail", pri=1.6)
    # coupling rods on their own bones: they orbit the crank circle without rotating
    cr = 0.35
    rods = []
    for s, tag in ((1, "R"), (-1, "L")):
        b = H.bone("Rod" + tag, "Body", (s * (gauge + 0.28), R, 1.0))
        m = merge(bar((s * (gauge + 0.28), R - cr, -0.7), (s * (gauge + 0.28), R - cr, 2.7), 0.08, 0.16, r=0.03),
                  *[cyl(0.1, 0.1, (s * (gauge + 0.28), R - cr, z), "x", segs=8) for z in dz])
        piece(H, "Rod" + tag, b, m, col="metal", mat="metal", role="detail", pri=1.1)
        rods.append((b, s))
    wheels = drivers + pony

    def mv(pose, u):
        # drivers turn n periods of 12 spokes per loop; the rods follow the crank angle of that turn
        n = max(1, round(1.6 * TAU * R / R / (TAU / 12)))
        ang = n * (TAU / 12) * u
        for b, s in rods:
            ph = ang + (0 if s > 0 else math.pi / 2)
            K.add(pose, b, (0, cr - cr * math.cos(ph), -cr * math.sin(ph) * 1, 0, 0, 0))

    _finish(H, wheels, 4.8, 10.0, (-0.8, 2.55, 3.6), (0.8, 0.2, 0.7), (0, 2.0, bz0 - 1.6), (0, by + 2.3, bz0 + 0.45), sym=12, extra_move=mv, attack="honk")
    return H


# ==================================================================================================== diesel + bullet + tram
@hero("train", FAM)
def diesel():
    H = _new("train", pv("#C1121F", "#F2C200", darker="#1E1E22"))
    H.bone("Chassis", "Body", (0, 1.4, 0))
    gauge = 1.25
    wheels = []
    for zc, tag in ((-3.6, "A"), (3.6, "B")):
        for i, dz in enumerate((-0.75, 0.75)):
            wheels += _wheelset(H, "Body", f"W{tag}{i}", zc + dz, 0.55, gauge)
    piece(H, "Bogies", "Body", merge(_bogie(H, -3.6, 0.55, gauge, 1.5), _bogie(H, 3.6, 0.55, gauge, 1.5)), col="darker", mat="metal", role="detail", pri=0.9)
    deck = box((3.6, 0.45, 12.0), (0, 1.55, 0), r=0.08)
    hood = round_poly(np.array([(-4.2, 1.75), (-4.3, 3.6), (-4.0, 3.9), (5.9, 3.9), (5.95, 1.75)]), [0.05, 0.2, 0.2, 0.15, 0.05], 3)
    hd = extrude(hood, 2.6, bevel=0.15, seg=2)
    nose = round_poly(np.array([(-5.9, 1.75), (-5.95, 2.9), (-5.3, 3.1), (-5.2, 1.75)]), [0.05, 0.2, 0.1, 0.05], 2)
    nz = extrude(nose, 2.6, bevel=0.15, seg=2)
    piece(H, "Chassis", "Chassis", merge(deck, hd, nz), col="primary", mat="metal", pri=0.4)
    # cab with glass
    K.greenhouse(H, "Chassis", -5.15, 3.0, -5.0, 4.75, -4.1, -4.1, 1.55, tumble=0.05, vertical_back=True, roof_col="primary", crown=0.03)
    cabl = round_poly(np.array([(-5.25, 1.75), (-5.25, 3.0), (-4.1, 3.0), (-4.1, 1.75)]), 0.05, 1)
    piece(H, "CabLower", "Chassis", extrude(cabl, 3.2, bevel=0.1), col="primary", mat="metal", role="body", pri=0.6)
    stripes = merge(*[cbox((0.05, 0.3, 11.6), (s * 1.82, 1.6, 0), c=0.02) for s in (-1, 1)], *[cbox((0.05, 0.25, 9.9), (s * 1.32, 2.4, 0.85), c=0.02) for s in (-1, 1)],
                    *[bar((-1.3 + 0.0, 2.0 - 0.0, -5.98), (0.0, 2.9, -5.98), 0.25, 0.04), bar((1.3, 2.0, -5.98), (0.0, 2.9, -5.98), 0.25, 0.04)])
    piece(H, "Stripes", "Chassis", stripes, col="secondary", mat="metal", role="detail", pri=1.2)
    rail = []
    for s in (-1, 1):
        rail.append(rod((s * 1.72, 2.85, -3.9), (s * 1.72, 2.85, 5.8), 0.035, segs=5))
        for z in np.linspace(-3.9, 5.8, 8):
            rail.append(rod((s * 1.72, 1.75, z), (s * 1.72, 2.85, z), 0.035, segs=5))
    grilles = merge(*[cbox((0.05, 1.2, 1.2), (s * 1.32, 3.0, z), c=0.02) for s in (-1, 1) for z in (0.0, 2.0, 4.0)], *[cyl(0.1, 0.45, (0, 3.95, z), "y", segs=14) for z in (1.0, 3.0)],
                   cyl(0.5, 0.18, (0.5, 4.2, -2.5), "y", segs=10))
    piece(H, "Railings", "Chassis", merge(*rail), col="secondary", mat="metal", role="detail", pri=1.4)
    piece(H, "Grilles", "Chassis", grilles, col="darker", mat="metal", role="detail", pri=1.3)
    K.lamp_pair(H, "Headlight", "Chassis", (0.75, 2.6, -5.97), r=0.15, depth=0.1)
    plows = merge(box((3.4, 0.5, 0.35), (0, 1.0, -6.1), r=0.05, rot_=(-25, 0, 0)), box((3.4, 0.5, 0.35), (0, 1.0, 6.1), r=0.05, rot_=(25, 0, 0)),
                  *[cyl(0.4, 0.15, (s * 1.0, 1.55, z), "z", segs=10) for s in (-1, 1) for z in (-6.1, 6.1)])
    piece(H, "Plows", "Chassis", plows, col="darker", mat="metal", role="detail", pri=1.2)
    seat = K.seat_mesh((-0.7, 3.1, -4.55), w=0.75, d=0.6, back=0.9)
    piece(H, "Seat", "Chassis", seat, col="darker", mat="cloth", role="seat", pri=1.2)
    _finish(H, wheels, 4.8, 12.0, (-0.7, 3.2, -4.55), (0.75, 0.2, 0.6), (0, 2.0, -6.4), (0, 4.3, -2.5), sym=8, attack="honk")
    return H


@hero("bullet train", FAM)
def bullet_train():
    H = _new("bullet train", pv("#F5F5F5", "#1E5BC6"))
    H.bone("Chassis", "Body", (0, 1.4, 0))
    gauge = 1.2
    wheels = []
    for zc, tag in ((-2.5, "A"), (4.5, "B")):
        for i, dz in enumerate((-0.7, 0.7)):
            wheels += _wheelset(H, "Body", f"W{tag}{i}", zc + dz, 0.5, gauge)
    piece(H, "Bogies", "Body", merge(_bogie(H, -2.5, 0.5, gauge, 1.4), _bogie(H, 4.5, 0.5, gauge, 1.4)), col="darker", mat="metal", role="detail", pri=1.0)
    # long pointed nose + body: a revolve along z flattened at the bottom
    prof = [(-7.0, 0), (-6.9, 0.35), (-6.2, 0.9), (-5.0, 1.45), (-3.4, 1.75), (-1.5, 1.8), (6.0, 1.8), (6.4, 1.6), (6.5, 0)]
    body = K.D.revolve(prof, segs=28, axis=2, spline=3)
    body = warp(body, lambda V: np.column_stack([V[:, 0] * 1.0, np.maximum(V[:, 1], -1.0) * np.where(V[:, 1] > 0, 1.0, 0.75) + 2.9 - 0.25 * np.clip((-V[:, 2] - 3.0) / 4.0, 0, 1), V[:, 2]]))
    piece(H, "Chassis", "Chassis", body, col="primary", mat="metal", pri=0.4)
    # cockpit glass + window band + livery stripe (proud skins following the hull)
    def skin(z0, z1, a0, a1, off, col, name, pri, mat="metal", tr=0.0):
        segs = 22
        V = []
        pts = []
        for i in range(segs + 1):
            z = z0 + (z1 - z0) * i / segs
            rr = float(np.interp(z, [p[0] for p in prof], [p[1] for p in prof])) + off
            pts.append((z, rr))
        return pts

    band = []
    for s in (-1, 1):
        band.append(cbox((0.05, 0.6, 9.0), (s * 1.81, 3.55, 1.0), c=0.02))
        band.append(cbox((0.05, 0.22, 12.5), (s * 1.81, 2.55, -0.2), c=0.02))
    piece(H, "Livery", "Chassis", merge(*band[1::2]), col="secondary", mat="metal", role="detail", pri=1.1)
    piece(H, "Windows", "Chassis", merge(*band[0::2]), col="glass", mat="glass", role="window", pri=1.1)
    can = K.D.revolve([(-1.2, 0), (-1.1, 0.4), (0.0, 0.6), (1.0, 0.4), (1.1, 0)], segs=16, axis=2, spline=3)
    can = xf(warp(can, lambda V: np.column_stack([V[:, 0] * 1.7, np.maximum(V[:, 1], 0) * 0.9, V[:, 2]])), (0, 3.95, -4.4))
    can = warp(can, lambda V: np.column_stack([V[:, 0], V[:, 1] - 0.3 * np.clip((-V[:, 2] - 4.4) / 1.1, 0, 1), V[:, 2]]))
    piece(H, "Glass", "Chassis", can, col="glass", mat="glass", role="window", pri=0.8, tr=0.3, ao=False)
    seat = K.seat_mesh((0, 3.85, -4.2), w=0.8, d=0.6, back=0.7)
    piece(H, "Seat", "Chassis", seat, col="darker", mat="cloth", role="seat", pri=1.2)
    K.lamp_pair(H, "Headlight", "Chassis", (0.55, 2.35, -6.65), shape="rect", w=0.3, h=0.1, depth=0.12)
    skirt = merge(*[cbox((0.08, 0.7, 12.0), (s * 1.65, 1.55, -0.3), c=0.03) for s in (-1, 1)])
    piece(H, "Skirts", "Chassis", skirt, col="secondary", mat="metal", role="detail", pri=1.0)
    _finish(H, wheels, 4.6, 13.5, (0, 3.95, -4.2), (0.8, 0.2, 0.6), (0, 2.5, -7.2), (0, 3.5, 6.5), sym=8, attack="ram")
    return H


@hero("tram", FAM)
def tram():
    H = _new("tram", pv("#E9C46A", "#2A9D8F"))
    H.bone("Chassis", "Body", (0, 1.2, 0))
    gauge = 1.2
    wheels = []
    for zc, tag in ((-3.0, "A"), (3.0, "B")):
        for i, dz in enumerate((-0.6, 0.6)):
            wheels += _wheelset(H, "Body", f"W{tag}{i}", zc + dz, 0.45, gauge)
    piece(H, "Bogies", "Body", merge(_bogie(H, -3.0, 0.45, gauge, 1.2), _bogie(H, 3.0, 0.45, gauge, 1.2)), col="darker", mat="metal", role="detail", pri=1.0)
    L = 11.0
    bp = round_poly(np.array([(-L / 2, 1.2), (-L / 2 - 0.2, 2.2), (-L / 2 + 0.1, 4.6), (L / 2 - 0.1, 4.6), (L / 2 + 0.2, 2.2), (L / 2, 1.2)]), [0.2, 0.5, 0.4, 0.4, 0.5, 0.2], 3)
    body = warp(extrude(bp, 3.4, bevel=0.2, seg=2), lambda V: np.column_stack([V[:, 0] * np.interp(np.abs(V[:, 2]), [0, L / 2 - 0.8, L / 2 + 0.2], [1.0, 1.0, 0.8]), V[:, 1], V[:, 2]]))
    piece(H, "Chassis", "Chassis", body, col="primary", mat="metal", pri=0.4)
    roof = K.box((3.0, 0.3, L - 0.6), (0, 4.7, 0), r=0.12, seg=1)
    roof = warp(roof, lambda V: np.column_stack([V[:, 0], V[:, 1] + 0.2 * (1 - (V[:, 0] / 1.5) ** 2), V[:, 2]]))
    piece(H, "Roof", "Chassis", roof, col="secondary", mat="metal", role="body", pri=0.7)
    wins, pills = [], []
    for s in (-1, 1):
        wins.append(cbox((0.05, 1.4, L - 2.2), (s * 1.71, 3.55, 0), c=0.03))
        for z in np.linspace(-(L - 2.2) / 2, (L - 2.2) / 2, 8):
            pills.append(cbox((0.08, 1.45, 0.16), (s * 1.74, 3.55, z), c=0.02))
    for zz in (-L / 2 - 0.05, L / 2 + 0.05):
        wins.append(cbox((2.3, 1.4, 0.05), (0, 3.55, zz), c=0.03))
    piece(H, "Windows", "Chassis", merge(*wins), col="glass", mat="glass", role="window", pri=1.0)
    piece(H, "Pillars", "Chassis", merge(*pills, *[cbox((0.05, 0.25, L - 0.6), (s * 1.73, 2.45, 0), c=0.02) for s in (-1, 1)]), col="secondary", mat="metal", role="detail", pri=1.2)
    H.bone("Pole", "Chassis", (0, 5.0, 2.5))
    pole = merge(rod((0, 5.0, 2.5), (0, 8.0, -1.5), 0.05, segs=6), cyl(0.15, 0.12, (0, 8.0, -1.5), "x", segs=10), cbox((0.6, 0.25, 0.6), (0, 5.0, 2.5), c=0.05))
    piece(H, "TrolleyPole", "Pole", pole, col="darker", mat="metal", role="detail", pri=1.1)
    K.lamp_pair(H, "Headlight", "Chassis", (0.9, 1.9, -L / 2 - 0.15), r=0.17, depth=0.1)
    bell = xf(K.lathe_profile([(-0.2, 0.0), (-0.2, 0.18), (0.05, 0.12), (0.18, 0.06), (0.2, 0)], 10, "y"), (0, 1.6, -L / 2 - 0.2))
    piece(H, "Bell", "Chassis", merge(bell, box((3.0, 0.3, 0.3), (0, 1.2, -L / 2 - 0.1), r=0.08), box((3.0, 0.3, 0.3), (0, 1.2, L / 2 + 0.1), r=0.08)), col="gold", mat="metal", role="detail", pri=1.3)
    seat = K.seat_mesh((0, 2.2, -L / 2 + 1.0), w=0.8, d=0.7, back=0.9)
    piece(H, "Seat", "Chassis", seat, col="darkWood", mat="wood", role="seat", pri=1.1)

    def mv(pose, u):
        K.add(pose, "Pole", (0, 0, 0, 0.03 * math.sin(TAU * u * 2), 0, 0))

    _finish(H, wheels, 5.0, L, (0, 2.3, -L / 2 + 1.0), (0.8, 0.2, 0.7), (0, 2.0, -L / 2 - 0.5), (0, 8.0, -1.5), sym=8, attack="honk", extra_move=mv)
    return H


# ==================================================================================================== small rail
@hero("mine cart", FAM)
def mine_cart():
    H = _new("mine cart", pv("#6B4E3D", "#3A3A3A"))
    H.bone("Chassis", "Body", (0, 0.6, 0))
    wheels = []
    for z, tag in ((-0.8, "F"), (0.8, "B")):
        wheels += _wheelset(H, "Body", "W" + tag, z, 0.35, 0.95, col="darker")
    tub = K.box((2.0, 1.2, 2.8), (0, 1.35, 0), r=0.12, seg=1)
    tub = warp(tub, lambda V: np.column_stack([V[:, 0] * (0.85 + 0.15 * (V[:, 1] - 0.75) / 1.2), V[:, 1], V[:, 2] * (0.88 + 0.12 * (V[:, 1] - 0.75) / 1.2)]))
    piece(H, "Chassis", "Chassis", tub, col="primary", mat="metal", pri=0.4)
    bands = merge(*[cbox((2.12, 0.12, 0.1), (0, 1.35, z), c=0.02) for z in (-1.0, 0.0, 1.0)], K.box((2.1, 0.12, 2.9), (0, 1.97, 0), r=0.05),
                  *[cbox((0.08, 0.08, 0.08), (s * 1.0, 1.7, z), c=0.02) for s in (-1, 1) for z in np.linspace(-1.2, 1.2, 7)])
    piece(H, "Bands", "Chassis", bands, col="secondary", mat="metal", role="detail", pri=1.0)
    ore = K.box((1.8, 0.4, 2.5), (0, 1.95, 0.55), r=0.15, seg=1)
    ore = warp(ore, lambda V: np.column_stack([V[:, 0], V[:, 1] + 0.2 * np.sin(V[:, 0] * 5 + 1) * np.sin(V[:, 2] * 4) * (V[:, 1] > 1.9), V[:, 2]]))
    gems = merge(*[xf(K.lathe_profile([(-0.12, 0), (0, 0.12), (0.15, 0)], 5, "y"), (x, 2.2, z)) for x, z in ((0.4, 1.0), (-0.5, 0.6), (0.1, 1.3))])
    piece(H, "Ore", "Chassis", ore, col=[0.25, 0.23, 0.22], mat="stone", role="detail", pri=1.3)
    piece(H, "Gems", "Chassis", gems, col=[0.95, 0.75, 0.2], mat="metal", role="detail", pri=1.8)
    seat = cbox((1.6, 0.05, 0.9), (0, 1.9, -0.75), c=0.02)
    piece(H, "Seat", "Chassis", seat, col="darkWood", mat="wood", role="seat", pri=1.2)
    axl = merge(rod((-0.95, 0.35, -0.8), (0.95, 0.35, -0.8), 0.06, segs=6), rod((-0.95, 0.35, 0.8), (0.95, 0.35, 0.8), 0.06, segs=6), box((1.6, 0.18, 2.4), (0, 0.65, 0), r=0.04))
    piece(H, "Axles", "Chassis", axl, col="darker", mat="metal", role="detail", pri=1.1)
    _finish(H, wheels, 2.2, 3.0, (0, 2.0, -0.75), (1.4, 0.1, 0.8), (0, 1.3, -1.5), (0, 1.0, 1.5), sym=8)
    return H


@hero("handcar", FAM)
def handcar():
    H = _new("handcar", pv("#8A5A33", "#B22222"))
    H.bone("Chassis", "Body", (0, 0.6, 0))
    wheels = []
    for z, tag in ((-1.0, "F"), (1.0, "B")):
        wheels += _wheelset(H, "Body", "W" + tag, z, 0.42, 1.0, col="secondary")
    deck = merge(box((2.6, 0.15, 3.4), (0, 0.95, 0), r=0.04), *[cbox((2.62, 0.04, 0.05), (0, 1.03, z), c=0.01) for z in np.linspace(-1.5, 1.5, 9)])
    piece(H, "Chassis", "Chassis", deck, col="primary", mat="wood", pri=0.4)
    tower = merge(*[bar((s * 0.35, 1.0, z), (s * 0.15, 2.3, 0), 0.12, 0.12) for s in (-1, 1) for z in (-0.5, 0.5)], cyl(0.6, 0.12, (0, 2.3, 0), "x", segs=10),
                  K.lathe_profile([(0.06, 0), (0.06, 0.55), (0.12, 0.55), (0.12, 0)], 16, "x"))
    piece(H, "Tower", "Chassis", tower, col="secondary", mat="metal", role="detail", pri=0.9)
    H.bone("Pump", "Chassis", (0, 2.3, 0))
    pump = merge(bar((0, 2.3, -1.4), (0, 2.3, 1.4), 0.14, 0.14), *[rod((-0.6, 2.3, z), (0.6, 2.3, z), 0.05, segs=6) for z in (-1.4, 1.4)])
    piece(H, "PumpHandle", "Pump", pump, col="darker", mat="metal", role="detail", pri=0.9)
    seat = cbox((1.2, 0.08, 0.6), (0, 1.1, 1.2), c=0.02)
    piece(H, "Seat", "Chassis", seat, col="darkWood", mat="wood", role="seat", pri=1.2)

    def mv(pose, u):
        K.add(pose, "Pump", (0, 0, 0, 0.35 * math.sin(TAU * u), 0, 0))

    _finish(H, wheels, 2.6, 3.6, (0, 1.2, 1.2), (1.0, 0.1, 0.6), (0, 1.0, -1.8), (0, 1.0, 1.8), sym=8, extra_move=mv, attack="honk")
    return H


@hero("roller coaster car", FAM)
def coaster_car():
    H = _new("roller coaster car", pv("#E63946", "#F1FAEE"))
    H.bone("Chassis", "Body", (0, 0.6, 0))
    wheels = []
    for z, tag in ((-1.1, "F"), (1.1, "B")):
        wheels += _wheelset(H, "Body", "W" + tag, z, 0.3, 1.05, col="metal")
    bp = round_poly(np.array([(-2.2, 0.75), (-2.3, 1.2), (-1.6, 1.9), (-1.2, 1.9), (-1.0, 1.5), (1.8, 1.5), (2.0, 2.1), (2.25, 2.1), (2.3, 0.75)]),
                    [0.1, 0.3, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1], 3)
    body = warp(extrude(bp, 2.4, bevel=0.2, seg=2), lambda V: np.column_stack([V[:, 0] * np.interp(V[:, 2], [-2.3, -1.0, 2.3], [0.7, 1.0, 1.0]), V[:, 1], V[:, 2]]))
    piece(H, "Chassis", "Chassis", body, col="primary", mat="metal", pri=0.4)
    seats = merge(*[K.seat_mesh((0, 1.5, z), w=1.9, d=0.8, back=0.9, bucket=False) for z in (-0.4, 1.0)])
    piece(H, "Seat", "Chassis", seats, col="darker", mat="cloth", role="seat", pri=0.9)
    bars = merge(*[merge(rod((0, 1.6, z - 0.6), (0, 2.2, z - 0.3), 0.06, segs=6), rod((-0.8, 2.2, z - 0.3), (0.8, 2.2, z - 0.3), 0.06, segs=6)) for z in (-0.4, 1.0)])
    piece(H, "LapBars", "Chassis", bars, col="secondary", mat="metal", role="detail", pri=1.0)
    under = merge(box((1.6, 0.25, 3.6), (0, 0.65, 0), r=0.05), *[cbox((0.3, 0.3, 0.6), (s * 1.05, 0.3, z), c=0.04) for s in (-1, 1) for z in (-1.1, 1.1)])
    stripe = merge(*[cbox((0.05, 0.18, 3.6), (s * 1.21, 1.2, 0.1), c=0.02) for s in (-1, 1)])
    piece(H, "Undercarriage", "Chassis", under, col="darker", mat="metal", role="detail", pri=1.1)
    piece(H, "Stripe", "Chassis", stripe, col="secondary", mat="metal", role="detail", pri=1.3)
    K.lamp_pair(H, "Headlight", "Chassis", (0.6, 1.25, -2.28), r=0.13, depth=0.08)
    _finish(H, wheels, 2.3, 4.6, (0, 1.6, -0.4), (1.6, 0.2, 0.8), (0, 1.3, -2.5), (0, 1.0, 2.4), sym=8)
    return H


L = K.LAND
MAP = [
    ("steam train", "steam train, steam locomotive, steam engine, locomotive, ghost locomotive, cog railway, choo choo", L),
    ("train", "train, trains, freight train, diesel train, diesel locomotive, armored train, sleeper train, toy train", L),
    ("bullet train", "bullet train, monorail, maglev, subway train, high speed train, metro train", L),
    ("tram", "tram, trolley, streetcar, horse drawn tram, cable car", L),
    ("mine cart", "mine cart, minecart, ore cart, ghost train", L),
    ("handcar", "handcar, hand car, pump trolley", L),
    ("roller coaster car", "roller coaster car, roller coaster, coaster car, log flume", L),
]
