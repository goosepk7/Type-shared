"""Trucks, vans, buses and work machines (land-vehicle mounts): pickup truck, monster truck, van, ambulance, ice cream
truck, food truck, delivery truck, fire truck, garbage truck, cement mixer, dump truck, tow truck, semi "truck",
tanker truck, bus, school bus, double decker bus; tractor, bulldozer, excavator, forklift, steamroller; tank,
armored car.

Road trucks share one builder: a cab (side-profile slab with the front wheel arch, glass greenhouse with roof +
pillars, grille, lamps, bumper, big mirrors, steps, fuel tank, exhaust stack) on frame rails, and a rear body by
type (bed, box, tipping bed on its own hinge bone, spinning mixer drum, ladder on a raising bone, tank, compactor,
trailer). Construction and military machines have their own builders (tracks with spinning road wheels and
sprockets, booms on bone chains that swing in the Attack).
"""
import math

import numpy as np

from kit import hero, Hero
from map import VEH
import landveh_kit as K
from landveh_kit import box, cbox, cyl, bar, rod, extrude, warp, merge, mirror, xf, lamp, piece, mpiece, round_poly

FAM = "trucks"
AMBER = [1.0, 0.62, 0.12]
RED_L = [0.85, 0.08, 0.08]
BLUE_L = [0.15, 0.35, 0.95]
LENS = [0.95, 0.96, 0.92]


def pv(p, s, **kw):
    d = {"primary": p, "secondary": s, "glass": "#33414F", "darker": "#24262B"}
    d.update(kw)
    return d


def _new(hid, preview, tags=("vehicle", "truck")):
    H = Hero(hid, plan="Vehicle", gait="drive", tags=list(tags))
    H.preview = preview
    return H


def _finish(H, wheels, steer, height, length, seat_pos, nose, tail, sym=8, attack="ram", seat="Seat", **kw):
    K.mount(H, seat, seat_pos, (0.9, 0.2, 0.85), "Chassis")
    H.socket("head", (0, height + 0.3, 0), "Chassis")
    H.socket("mouth", nose, "Chassis")
    H.socket("exhaust", tail, "Chassis")
    H.rig.update({"head": "Chassis"})
    K.vehicle_clips(H, wheels, susp="Chassis", height=height, length=length, sym=sym, steer=steer, attack=attack, **kw)


# ==================================================================================================== road trucks
TBASE = dict(
    W=4.0, wr=0.95, ww=0.75, front=-5.0,  # front bumper face z
    hood=2.0,          # hood length (0.4 = cab-over)
    cab=2.4,           # cab length (windshield base -> cab back)
    belt=2.7, hood_y=2.5, nose_y=2.2, roofy=4.0, ws_run=0.6,
    axles=(-3.6, 2.4), rear_axles=None,  # axle z positions (first = steering)
    rear="bed", rear_len=4.0, rear_h=2.0, rear_y=None,
    frame_y=1.15, lamps="rect", grille="truck", rim="truck", knobby=0.0, stack=False, bull=False, lightbar=False,
    rear_col="primary", seat_col="darker", wr_scale=1.0, lift=0.0, preview={}, tags=("vehicle", "truck"), sym=8,
)


def _truck(hid, **kw):
    P = dict(TBASE)
    P.update(kw)
    H = _new(hid, P["preview"], P["tags"])
    W, wr, ww = P["W"], P["wr"], P["ww"]
    hw = W / 2
    zn = P["front"]
    zws = zn + P["hood"]
    zc = zws + P["cab"]
    belt, roofy, lift = P["belt"] + P["lift"], P["roofy"] + P["lift"], P["lift"]
    fy = P["frame_y"] + lift
    axles = P["axles"]
    H.bone("Chassis", "Body", (0, wr + 0.3, (axles[0] + axles[-1]) / 2))
    # ------------------------------------------------------------------ wheels
    specs = []
    xw = P.get("track_x") or (hw - ww / 2 + 0.05)
    for i, z in enumerate(axles):
        tag = "F" if i == 0 else f"B{i}"
        specs.append(dict(name=f"Wheel{tag}R", pos=(xw, wr, z), r=wr, w=ww, side=1, steer=(i == 0)))
        specs.append(dict(name=f"Wheel{tag}L", pos=(-xw, wr, z), r=wr, w=ww, side=-1, steer=(i == 0)))
    wheels, steer = K.add_wheels(H, specs, rim=P["rim"], knobby=P["knobby"], rim_col=P.get("rim_col", "metal"))
    # ------------------------------------------------------------------ cab lower body (front arch cut in)
    zf = axles[0]
    ybot = fy - 0.25
    pts, rad = [], []

    def a(p, r=0.0):
        pts.append(p)
        rad.append(r)

    a((zn + 0.2, ybot), 0.15)
    a((zn, ybot + 0.3), 0.1)
    a((zn - 0.02, P["nose_y"] + lift), 0.2)
    a((zn + 0.3, P["hood_y"] + lift), 0.25)
    a((zws, belt), 0.15)
    a((zc, belt), 0.05)
    a((zc, ybot), 0.1)
    ra = wr + 0.16
    dy = wr - ybot
    if ra > dy:
        dz = math.sqrt(ra * ra - dy * dy)
        a0 = math.atan2(-dy, dz)
        for k in range(15):
            an = a0 + (math.pi - 2 * a0) * k / 14
            a((zf + ra * math.cos(an), wr + ra * math.sin(an)))

    def cabwarp(V):
        x, y, z = V[:, 0], V[:, 1], V[:, 2]
        s = 1 - 0.07 * np.clip((zn + 0.8 - z) / 0.8, 0, 1) ** 2
        cr = 0.06 * np.clip(1 - (x / hw) ** 2, 0, 1) * np.clip((y - (P["hood_y"] + lift - 0.3)) / 0.3, 0, 1) * (z < zws - 0.05)
        return np.column_stack([x * s, y + cr, z])

    cab = warp(extrude(round_poly(np.array(pts), rad, 3), W, bevel=0.14, seg=3), cabwarp)
    piece(H, "Chassis", "Chassis", cab, col="primary", mat="metal", pri=0.5)
    xg = hw * 0.9
    K.greenhouse(H, "Chassis", zws, belt, zws + P["ws_run"], roofy, zc - 0.05, zc - 0.05, xg, tumble=0.06, vertical_back=True,
                 bpillars=(), rear_pw=0.3)
    # ------------------------------------------------------------------ interior
    sx = xg * 0.5
    seat = K.seat_mesh((-sx, belt - 0.15, zc - 0.75), w=0.9, d=0.8, back=1.05)
    piece(H, "Seat", "Chassis", seat, col=P["seat_col"], mat="cloth", role="seat", pri=1.1)
    seat2 = K.seat_mesh((sx, belt - 0.15, zc - 0.75), w=0.9, d=0.8, back=1.05)
    dash = box((2 * xg - 0.3, 0.3, 0.4), (0, belt + 0.05, zws + 0.35), r=0.08)
    sw = K.steering_mesh((-sx, belt + 0.4, zws + 0.75), r=0.3, tilt=40, col_len=0.4)
    piece(H, "Dash", "Chassis", merge(dash, sw, seat2), col="darker", mat="plastic", role="detail", pri=1.5)
    # ------------------------------------------------------------------ front end
    ny = P["nose_y"] + lift
    chrome = []
    gw = W * 0.5
    gh = (ny - ybot) * 0.62
    gy = ybot + 0.35 + gh / 2
    piece(H, "Grille", "Chassis", box((gw, gh, 0.12), (0, gy, zn - 0.02), r=0.06), col="darker", mat="metal", role="detail", pri=1.4)
    chrome.append(box((gw + 0.12, gh + 0.12, 0.05), (0, gy, zn + 0.03), r=0.06))
    for k in range(5):
        chrome.append(cbox((gw * 0.94, 0.05, 0.05), (0, gy - gh * 0.4 + gh * 0.2 * k, zn - 0.08), c=0.015))
    if P["lamps"] == "round":
        K.lamp_pair(H, "Headlight", "Chassis", (hw - 0.55, gy + 0.05, zn - 0.08), r=0.27, depth=0.16)
        chrome += [K.bezel((s * (hw - 0.55), gy + 0.05, zn - 0.06), 0.27, 0.12) for s in (-1, 1)]
    else:
        K.lamp_pair(H, "Headlight", "Chassis", (hw - 0.55, gy + 0.05, zn - 0.06), shape="rect", w=0.7, h=0.32, depth=0.2)
    by = ybot + 0.15
    bump = box((W + 0.1, 0.38, 0.4), (0, by, zn - 0.15), r=0.1, seg=1)
    piece(H, "Bumper", "Chassis", bump, col="metal" if P["grille"] == "truck" else "darker", mat="metal", role="detail", pri=1.2)
    if P["bull"]:
        bb = [rod((s * 0.8, by, zn - 0.4), (s * 0.8, ny + 0.2, zn - 0.45), 0.08) for s in (-1, 1)]
        bb.append(rod((-0.8, ny + 0.2, zn - 0.45), (0.8, ny + 0.2, zn - 0.45), 0.08, ext=0.08))
        piece(H, "PushBar", "Chassis", merge(*bb), col="darker", mat="metal", role="detail", pri=1.6)
    # mirrors on arms
    mir = merge(rod((hw - 0.05, belt + 0.2, zws + 0.3), (hw + 0.45, belt + 0.45, zws + 0.25), 0.04, segs=6),
                box((0.18, 0.75, 0.35), (hw + 0.5, belt + 0.55, zws + 0.25), r=0.06))
    mpiece(H, "Mirror#", "Chassis", mir, col="darker", mat="metal", role="detail", pri=1.8)
    # steps, fuel tank, frame
    dark = []
    for s in (-1, 1):
        dark.append(box((0.35, 0.08, 0.7), (s * (hw - 0.05), ybot - 0.05, zc - 0.6), r=0.03))
        dark.append(box((0.18, fy - 0.25, 0.2), (s * 0.75, (fy - 0.25) / 2 + 0.35, zn + 0.6), r=0.05))
    zt = zc + 0.2 + P["rear_len"]
    for s in (-1, 1):
        dark.append(box((0.22, 0.4, zt - zn - 0.6), (s * 0.75, fy - 0.15, (zn + 0.4 + zt) / 2), r=0.04))
    piece(H, "Frame", "Chassis", merge(*dark), col="darker", mat="metal", role="detail", pri=1.3)
    tank = merge(cyl(1.3, 0.38, (hw - 0.45, ybot + 0.12, zc + 0.75), "z", segs=16), )
    if P["rear"] in ("box", "garbage", "ladder", "tanker", "mixer", "dump", "trailer"):
        chrome.append(tank)
    if P["stack"]:
        st = merge(K.tube_ring(0.14, 0.1, 2.4, axis="y", pos=(hw - 0.35, belt + 0.8, zc + 0.15)), cyl(0.8, 0.2, (hw - 0.35, belt - 0.2, zc + 0.15), "y", segs=12))
        chrome.append(st)
        chrome.append(mirror(st))
    piece(H, "Chrome", "Chassis", merge(*chrome), col="metal", mat="metal", role="detail", pri=1.9)
    if P["lightbar"]:
        lb = box((2.2, 0.14, 0.45), (0, roofy + 0.15, zws + P["ws_run"] + 0.35), r=0.04)
        lr = box((0.95, 0.24, 0.36), (0.55, roofy + 0.33, zws + P["ws_run"] + 0.35), r=0.08, seg=2)
        piece(H, "LightBar", "Chassis", lb, col="darker", mat="plastic", role="detail", pri=1.3)
        piece(H, "SirenRed", "Chassis", lr, col=RED_L, mat="glass", role="light", pri=1.4, ao=False)
        piece(H, "SirenBlue", "Chassis", mirror(lr), col=BLUE_L if P["lightbar"] != "red" else RED_L, mat="glass", role="light", pri=1.4, ao=False)
    # roof marker lights (amber)
    mk = merge(*(cbox((0.18, 0.1, 0.12), (x, roofy + 0.12, zws + P["ws_run"] + 0.05), c=0.03) for x in (-0.6, -0.3, 0, 0.3, 0.6)))
    piece(H, "Markers", "Chassis", mk, col=AMBER, mat="glass", role="light", pri=2.4, ao=False)
    # ------------------------------------------------------------------ rear body
    ry = P["rear_y"] if P["rear_y"] is not None else fy + 0.1
    ry += 0 if P["rear_y"] is None else lift
    z0, z1 = zc + 0.2, zt
    rt = P["rear"]
    attack_extra = None
    spinners = ()
    fenders = []
    for z in axles[1:]:
        if rt in ("bed",):
            continue
        ar = []
        rr = wr + 0.2
        for k in range(11):
            an = math.radians(10 + 160 * k / 10)
            ar.append((z + rr * math.cos(an), wr + rr * math.sin(an)))
        for k in range(10, -1, -1):
            an = math.radians(10 + 160 * k / 10)
            ar.append((z + (rr - 0.12) * math.cos(an), wr + (rr - 0.12) * math.sin(an)))
        for s in (-1, 1):
            fenders.append(xf(extrude(np.array(ar), ww + 0.15, bevel=0.04, seg=1), (s * xw, 0, 0)))
    if fenders:
        piece(H, "Fenders", "Chassis", merge(*fenders), col="darker", mat="plastic", role="detail", pri=1.6)
    rc = P["rear_col"]
    if rt == "bed":
        # pickup bed with the rear arch cut into the sides
        zr = axles[1]
        side = [(z0, ry), (z0, belt - 0.05), (z1, belt - 0.05), (z1, ry)]
        ra = wr + 0.16
        dy = wr - ry
        sp, srd = [], []
        for p in side:
            sp.append(p)
            srd.append(0.08)
        if ra > dy:
            dz = math.sqrt(ra * ra - dy * dy)
            a0 = math.atan2(-dy, dz)
            for k in range(13):
                an = a0 + (math.pi - 2 * a0) * k / 12
                sp.append((zr + ra * math.cos(an), wr + ra * math.sin(an)))
                srd.append(0.0)
        sp = round_poly(np.array(sp), srd, 2)
        sides = [xf(extrude(sp, 0.22, bevel=0.06, seg=2), (s * (hw - 0.11), 0, 0)) for s in (-1, 1)]
        floor = box((W - 0.3, 0.15, z1 - z0 - 0.2), (0, ry + 0.45, (z0 + z1) / 2), r=0.04)
        front = box((W - 0.1, belt - ry - 0.45, 0.2), (0, (belt + ry + 0.4) / 2, z0 + 0.1), r=0.05)
        tg = box((W - 0.1, belt - ry - 0.45, 0.18), (0, (belt + ry + 0.4) / 2, z1 - 0.09), r=0.05)
        piece(H, "Bed", "Chassis", merge(*sides, floor, front, tg), col=rc, mat="metal", role="body", pri=0.7)
        TL = (hw - 0.2, belt - 0.4, z1 + 0.02)
        rb = box((W - 0.2, 0.3, 0.3), (0, ry + 0.15, z1 + 0.1), r=0.08)
        hitch = merge(rb, cbox((0.2, 0.2, 0.4), (0, ry + 0.1, z1 + 0.4), c=0.04), cyl(0.18, 0.13, (0, ry + 0.3, z1 + 0.55), "y", segs=10))
        piece(H, "RearBumper", "Chassis", hitch, col="metal", mat="metal", role="detail", pri=1.5)
    else:
        bh = P["rear_h"]
        top = ry + bh
        if rt in ("box", "garbage", "trailer", "ladder", "icecream", "food", "ambulance"):
            bx = box((W + 0.1, bh, z1 - z0), (0, ry + bh / 2, (z0 + z1) / 2), r=0.12, seg=1)
            if rt == "garbage":
                hop = extrude(round_poly(np.array([(z1 - 0.2, ry), (z1 - 0.2, top), (z1 + 0.6, top - 0.2), (z1 + 1.1, ry + 0.6), (z1 + 0.6, ry)]), 0.15, 2), W, bevel=0.1)
                bx = merge(bx, hop)
                # ribs
                rib = merge(*(cbox((W + 0.25, 0.12, 0.15), (0, ry + bh * f, (z0 + z1) / 2), c=0.03) for f in (0.33, 0.66)))
                bx = merge(bx, *[xf(cbox((0.12, bh, 0.2), (0, 0, 0), c=0.03), (s * (hw + 0.07), ry + bh / 2, z)) for s in (-1, 1) for z in np.linspace(z0 + 0.6, z1 - 0.6, 4)])
            piece(H, "Box", "Chassis", bx, col=rc, mat="metal", role="body", pri=0.6)
            TL = (hw - 0.15, ry + 0.4, z1 + (1.1 if rt == "garbage" else 0.02))
            if rt == "trailer":
                pass
        elif rt == "tanker":
            tk = K.lathe_profile([(z0 + 0.1, 0), (z0 + 0.1, 0.9), (z0 + 0.45, 1.15), (z1 - 0.35, 1.15), (z1, 0.9), (z1, 0)], 24, "z")
            tk = xf(warp(tk, lambda V: np.column_stack([V[:, 0] * 1.5, V[:, 1], V[:, 2]])), (0, ry + 1.2, 0))
            hoops = merge(*(K.torus(1.17, 0.05, "z", 24, 4, pos=(0, 0, z)) for z in np.linspace(z0 + 0.8, z1 - 0.8, 3)))
            hoops = xf(warp(hoops, lambda V: np.column_stack([V[:, 0] * 1.5, V[:, 1], V[:, 2]])), (0, ry + 1.2, 0))
            walk = box((0.8, 0.08, z1 - z0 - 1.0), (0, ry + 2.42, (z0 + z1) / 2), r=0.03)
            piece(H, "Box", "Chassis", tk, col=rc, mat="metal", role="body", pri=0.6)
            piece(H, "Hoops", "Chassis", merge(hoops, walk), col="metal", mat="metal", role="detail", pri=1.4)
            TL = (hw - 0.15, ry + 0.3, z1 + 0.02)
        elif rt == "dump":
            hz = z1 - 0.2
            H.bone("Bed", "Chassis", (0, ry + 0.2, hz))
            dp = round_poly(np.array([(z0, ry + 0.25), (z0 - 0.2, top + 0.4), (z1 + 0.1, top), (z1, ry + 0.25)]), [0.1, 0.1, 0.1, 0.1], 2)
            outer = warp(extrude(dp, W + 0.1, bevel=0.1, seg=2), lambda V: np.column_stack([V[:, 0] * (1 + 0.06 * (V[:, 1] - ry) / bh), V[:, 1], V[:, 2]]))
            cano = box((W - 0.2, 0.15, 1.2), (0, top + 0.35, z0 - 0.7), r=0.05)
            ribs = merge(*[xf(cbox((0.12, bh * 0.9, 0.2), (0, 0, 0), c=0.03), (s * (hw + 0.1 + 0.03 * s * 0), ry + bh / 2 + 0.2, z)) for s in (-1, 1) for z in np.linspace(z0 + 0.4, z1 - 0.4, 4)])
            piece(H, "Box", "Bed", merge(outer, cano), col=rc, mat="metal", role="body", pri=0.6)
            piece(H, "BedRibs", "Bed", ribs, col="darker", mat="metal", role="detail", pri=1.6)
            fill = box((W - 0.2, 0.25, z1 - z0 - 0.4), (0, top + 0.12, (z0 + z1) / 2), r=0.12, seg=2)
            fill = warp(fill, lambda V: np.column_stack([V[:, 0], V[:, 1] + 0.25 * np.cos(V[:, 2] * 1.7) * np.cos(V[:, 0] * 1.3) * (V[:, 1] > top + 0.1), V[:, 2]]))
            piece(H, "Load", "Bed", fill, col=[0.55, 0.42, 0.3], mat="stone", role="detail", pri=1.8)
            TL = (hw - 0.15, ry + 0.3, z1 + 0.02)

            def attack_extra(pose, s):
                tip = K._bump(s, 0.1, 0.95)
                K.add(pose, "Bed", (0, 0, 0, 0.75 * tip, 0, 0))
        elif rt == "mixer":
            H.bone("Drum", "Chassis", (0, ry + 1.45, (z0 + z1) / 2))
            dl = z1 - z0
            prof = [(-dl / 2, 0), (-dl / 2, 0.5), (-dl / 2 + 0.3, 1.0), (-dl * 0.1, 1.3), (dl * 0.15, 1.3), (dl / 2 - 0.2, 0.75), (dl / 2, 0.4), (dl / 2 + 0.05, 0)]
            drum = K.lathe_profile(prof, 24, "z")
            stripes = merge(*[K.torus(1.0, 0.07, "z", 24, 4, pos=(0, 0, 0)) for _ in range(1)])
            spiral = []
            for k in range(36):
                t = k / 36
                zz = -dl / 2 + 0.4 + (dl - 0.9) * t
                rr = float(np.interp(zz, [p[0] for p in prof], [p[1] for p in prof])) + 0.02
                an = t * TAU * 2.0
                spiral.append(cbox((0.18, 0.06, 0.4), (rr * math.cos(an), rr * math.sin(an), zz), c=0.02, rot_=(0, 0, math.degrees(an) + 90)))
            dr = xf(drum, (0, 0, 0), r=(-10, 0, 0))
            sp = xf(merge(*spiral), (0, 0, 0), r=(-10, 0, 0))
            piece(H, "Box", "Drum", xf(dr, (0, ry + 1.45, (z0 + z1) / 2)), col=rc, mat="metal", role="body", pri=0.6)
            piece(H, "DrumStripes", "Drum", xf(sp, (0, ry + 1.45, (z0 + z1) / 2)), col="secondary", mat="metal", role="detail", pri=1.3)
            cradle = merge(box((1.2, 0.6, 0.3), (0, ry + 0.3, z0 + 0.3), r=0.06), box((1.2, 0.9, 0.3), (0, ry + 0.45, z1 - 0.4), r=0.06),
                           box((0.9, 0.25, 0.6), (0, ry + 2.4, z1 + 0.1), r=0.06, rot_=(-35, 0, 0)), box((0.9, 0.12, 1.4), (0, ry + 1.1, z1 + 0.6), r=0.05, rot_=(40, 0, 0)))
            piece(H, "Cradle", "Chassis", cradle, col="darker", mat="metal", role="detail", pri=1.4)
            spinners = (("Drum", "z", 1),)
            TL = (hw - 0.15, ry + 0.3, z1 + 0.02)
        else:
            TL = (hw - 0.15, ry + 0.3, z1 + 0.02)
        if rt == "box" or rt == "ambulance" or rt == "icecream" or rt == "food" or rt == "trailer":
            rb = merge(box((W - 0.2, 0.3, 0.3), (0, ry + 0.0, z1 + 0.12), r=0.08), *[cbox((0.04, bh * 0.9, 0.06), (x, ry + bh / 2, z1 + 0.03), c=0.01) for x in (-0.03,)],
                       *[cbox((0.1, 0.25, 0.08), (s * 0.15, ry + bh * f, z1 + 0.05), c=0.02) for s in (-1, 1) for f in (0.3, 0.7)])
            piece(H, "RearBumper", "Chassis", rb, col="metal", mat="metal", role="detail", pri=1.5)
        if rt == "ladder":
            H.bone("Ladder", "Chassis", (0, top + 0.35, z1 - 0.4))
            lad = []
            ll = z1 - z0 + 1.2
            for s in (-1, 1):
                lad.append(bar((s * 0.55, top + 0.45, z1 - 0.2), (s * 0.55, top + 0.45, z1 - 0.2 - ll), 0.1, 0.22, r=0.03))
                lad.append(bar((s * 0.42, top + 0.7, z1 - 0.4), (s * 0.42, top + 0.7, z1 - 0.4 - ll * 0.85), 0.08, 0.18, r=0.03))
            for k in range(13):
                z = z1 - 0.4 - k * (ll - 0.3) / 13
                lad.append(rod((-0.55, top + 0.45, z), (0.55, top + 0.45, z), 0.035, segs=5))
            turn = cyl(0.35, 0.65, (0, top + 0.18, z1 - 0.4), "y", segs=18)
            piece(H, "Ladder", "Ladder", merge(*lad), col="metal", mat="metal", role="detail", pri=1.0)
            piece(H, "Turntable", "Chassis", turn, col="darker", mat="metal", role="detail", pri=1.2)
            # lockers: shutter doors + hose reel
            lk = []
            for s in (-1, 1):
                for k in range(3):
                    zz = z0 + 0.5 + k * (z1 - z0 - 1.0) / 3 + (z1 - z0 - 1.0) / 6
                    lk.append(cbox((0.05, bh * 0.7, (z1 - z0 - 1.0) / 3 - 0.15), (s * (hw + 0.08), ry + bh * 0.5, zz), c=0.02))
            piece(H, "Lockers", "Chassis", merge(*lk), col="metal", mat="metal", role="detail", pri=1.4)
            reel = merge(cyl(0.7, 0.45, (0, top - 0.2, z0 + 0.35), "x", segs=16), K.torus(0.42, 0.08, "x", 16, 5, pos=(0.0, top - 0.2, z0 + 0.35)))
            piece(H, "HoseReel", "Chassis", reel, col="secondary", mat="cloth", role="detail", pri=1.6)

            def attack_extra(pose, s):
                up = K._bump(s, 0.05, 0.98)
                K.add(pose, "Ladder", (0, 0, 0, 0.55 * up, 0.25 * up, 0))
        if rt == "garbage":
            H.bone("ArmL", "Chassis", (hw + 0.2, top - 0.3, z1 - 0.2))
            arm = merge(bar((hw + 0.2, top - 0.3, z1 - 0.2), (hw + 0.25, ry + 0.3, z1 + 0.3), 0.18, 0.18), cbox((0.6, 0.5, 0.15), (hw + 0.25, ry + 0.2, z1 + 0.35), c=0.04))
            piece(H, "Arm", "ArmL", arm, col="darker", mat="metal", role="detail", pri=1.3)

            def attack_extra(pose, s):
                up = K._bump(s, 0.05, 0.95)
                K.add(pose, "ArmL", (0, 0, 0, -1.1 * up, 0, 0))
        if rt == "ambulance":
            st = []
            for s in (-1, 1):
                st.append(cbox((0.04, 0.32, z1 - z0 - 0.3), (s * (hw + 0.07), ry + bh * 0.45, (z0 + z1) / 2), c=0.01))
                st.append(cbox((0.04, 0.8, 0.26), (s * (hw + 0.08), ry + bh * 0.72, (z0 + z1) / 2 + 0.4), c=0.01))
                st.append(cbox((0.04, 0.26, 0.8), (s * (hw + 0.08), ry + bh * 0.72, (z0 + z1) / 2 + 0.4), c=0.01))
            st.append(cbox((0.8, 0.26, 0.04), (0, ry + bh * 0.7, z1 + 0.07), c=0.01))
            st.append(cbox((0.26, 0.8, 0.04), (0, ry + bh * 0.7, z1 + 0.07), c=0.01))
            piece(H, "Stripes", "Chassis", merge(*st), col="secondary", mat="plastic", role="detail", pri=1.4)
            lr = merge(*(box((0.3, 0.25, 0.3), (s * (hw - 0.2), top + 0.12, z), r=0.08) for s in (-1, 1) for z in (z0 + 0.2, z1 - 0.2)))
            piece(H, "BeaconRed", "Chassis", lr, col=RED_L, mat="glass", role="light", pri=1.5, ao=False)
        if rt in ("icecream", "food"):
            wz0, wz1 = z0 + 0.5, z1 - 0.8
            win = cbox((0.06, bh * 0.4, wz1 - wz0), (hw + 0.07, ry + bh * 0.62, (wz0 + wz1) / 2), c=0.02)
            frame_ = merge(cbox((0.1, 0.1, wz1 - wz0 + 0.2), (hw + 0.1, ry + bh * 0.4, (wz0 + wz1) / 2), c=0.03),
                           cbox((0.12, 0.12, wz1 - wz0 + 0.3), (hw + 0.1, ry + bh * 0.84, (wz0 + wz1) / 2), c=0.03))
            counter = box((0.5, 0.1, wz1 - wz0), (hw + 0.3, ry + bh * 0.4, (wz0 + wz1) / 2), r=0.03)
            piece(H, "ServeWindow", "Chassis", win, col="darker", mat="glass", role="window", pri=1.3)
            piece(H, "Counter", "Chassis", merge(frame_, counter), col="metal", mat="metal", role="detail", pri=1.4)
            aw = []
            n = 8
            for k in range(n):
                zz = wz0 + (wz1 - wz0) * (k + 0.5) / n
                aw.append(cbox((1.0, 0.06, (wz1 - wz0) / n), (hw + 0.5, ry + bh * 0.95 - 0.05, zz), c=0.01, rot_=(0, 0, -18)))
            awn = merge(*aw[0::2])
            awn2 = merge(*aw[1::2])
            piece(H, "Awning", "Chassis", awn, col="secondary", mat="cloth", role="detail", pri=1.5)
            piece(H, "Awning2", "Chassis", awn2, col="white", mat="cloth", role="detail", pri=1.6)
            if rt == "icecream":
                cz = (z0 + z1) / 2
                cone = K.lathe_profile([(top + 0.1, 0.05), (top + 1.2, 0.42), (top + 1.25, 0)], 18, "y")
                cone = xf(cone, (0, 0, cz))
                scoop = K.D.revolve([(top + 1.05, 0), (top + 1.15, 0.5), (top + 1.45, 0.58), (top + 1.8, 0.4), (top + 1.95, 0)], segs=18, axis=1, spline=3)
                scoop = warp(scoop, lambda V: np.column_stack([V[:, 0], V[:, 1] + 0.05 * np.sin(np.arctan2(V[:, 2], V[:, 0]) * 7) * (V[:, 1] < top + 1.3), V[:, 2] + cz]))
                piece(H, "Cone", "Chassis", cone, col=[0.85, 0.62, 0.35], mat="plastic", role="detail", pri=1.2)
                piece(H, "Scoop", "Chassis", scoop, col=[1.0, 0.72, 0.8], mat="plastic", role="detail", pri=1.2)
            else:
                sign = box((0.15, 0.6, (wz1 - wz0) * 0.8), (hw - 0.3, top + 0.4, (wz0 + wz1) / 2), r=0.05)
                piece(H, "Sign", "Chassis", sign, col="secondary", mat="plastic", role="detail", pri=1.4)
        TLm = K.lamp(TL, 0, 0.12, axis="+z", shape="rect", w=0.25, h=0.45)
        mpiece(H, "Taillight#", "Chassis", TLm, col=RED_L, mat="glass", role="light", pri=1.7, ao=False)
    if rt == "bed":
        TLm = K.lamp(TL, 0, 0.12, axis="+z", shape="rect", w=0.25, h=0.45)
        mpiece(H, "Taillight#", "Chassis", TLm, col=RED_L, mat="glass", role="light", pri=1.7, ao=False)
    height = max(roofy, (P["rear_y"] or 0) + P["rear_h"])
    _finish(H, wheels, steer, height, zt - zn, (-sx, belt - 0.05, zc - 0.75), (0, ny, zn - 0.4), (hw - 0.35, belt + 2, zc + 0.15),
            sym=P["sym"], spinners=spinners, extra_attack=attack_extra)
    return H


TAU = 2 * math.pi


@hero("pickup truck", FAM)
def pickup_truck():
    return _truck("pickup truck", W=3.9, wr=0.85, ww=0.7, front=-4.9, hood=2.3, cab=2.3, belt=2.55, hood_y=2.35, nose_y=2.05, roofy=3.75,
                  axles=(-3.3, 2.45), rear="bed", rear_len=3.4, frame_y=1.05, rim="alloy", rim_col="metal", sym=5, knobby=0.03,
                  preview=pv("#9B2226", "#2E2E2E"))


@hero("monster truck", FAM)
def monster_truck():
    H = _truck("monster truck", W=4.2, wr=1.9, ww=1.5, front=-4.6, hood=2.0, cab=2.3, belt=2.4, hood_y=2.2, nose_y=1.9, roofy=3.5,
               axles=(-3.2, 3.0), track_x=2.6, rear="bed", rear_len=3.1, frame_y=1.0, lift=2.4, rim="steel", rim_col="secondary", knobby=0.16,
               bull=True, sym=8, preview=pv("#39B54A", "#FF6B00"), tags=("vehicle", "truck", "monster"))
    # giant wheels stick out: shocks + axles + roll cage hoop
    sh = []
    for z in (-2.9, 2.6):
        sh.append(rod((-2.5, 1.9, z), (2.5, 1.9, z), 0.16, segs=10))
        for s in (-1, 1):
            sh.append(rod((s * 1.3, 1.95, z), (s * 1.0, 3.6, z + 0.35 * (1 if z > 0 else -1)), 0.14, segs=10))
    piece(H, "Shocks", "Body", merge(*sh), col="secondary", mat="metal", role="detail", pri=1.3)
    return H


@hero("van", FAM)
def van():
    return _truck("van", W=3.9, wr=0.75, ww=0.62, front=-4.4, hood=0.9, cab=1.8, belt=2.5, hood_y=2.25, nose_y=1.75, roofy=4.0, ws_run=1.0,
                  axles=(-3.0, 2.5), rear="box", rear_len=4.0, rear_h=3.2, rear_y=0.95, frame_y=0.95, grille="van", rim="steel",
                  rim_col="white", preview=pv("#F2F2F2", "#4A4A4A"))


@hero("ambulance", FAM)
def ambulance():
    return _truck("ambulance", W=4.0, wr=0.85, ww=0.66, front=-4.7, hood=1.4, cab=1.9, belt=2.55, hood_y=2.35, nose_y=1.95, roofy=3.9,
                  axles=(-3.2, 2.6), rear="ambulance", rear_len=4.3, rear_h=3.4, rear_y=1.05, frame_y=1.05, grille="van", lightbar="red",
                  rim="steel", preview=pv("#F5F5F5", "#D7263D"))


@hero("ice cream truck", FAM)
def ice_cream_truck():
    return _truck("ice cream truck", W=4.0, wr=0.85, ww=0.66, front=-4.7, hood=1.3, cab=1.9, belt=2.55, hood_y=2.35, nose_y=1.95, roofy=3.9,
                  axles=(-3.2, 2.7), rear="icecream", rear_len=4.4, rear_h=3.0, rear_y=1.05, frame_y=1.05, lamps="round", rim="steel",
                  rim_col="white", rear_col="white", preview=pv("#F7A8C8", "#5BC0EB"))


@hero("food truck", FAM)
def food_truck():
    return _truck("food truck", W=4.1, wr=0.9, ww=0.7, front=-4.9, hood=1.7, cab=2.0, belt=2.65, hood_y=2.45, nose_y=2.05, roofy=4.0,
                  axles=(-3.3, 2.9), rear="food", rear_len=4.8, rear_h=3.3, rear_y=1.1, frame_y=1.1, rim="steel",
                  preview=pv("#F2C24A", "#D72B2B"))


@hero("delivery truck", FAM)
def delivery_truck():
    return _truck("delivery truck", W=4.1, wr=0.9, ww=0.7, front=-4.9, hood=1.5, cab=2.1, belt=2.65, hood_y=2.45, nose_y=2.0, roofy=4.0,
                  axles=(-3.4, 2.8), rear="box", rear_len=5.0, rear_h=3.6, rear_y=1.15, frame_y=1.15, rim="steel", rear_col="secondary",
                  preview=pv("#6B4F2A", "#EFE6D2"))


@hero("fire truck", FAM)
def fire_truck():
    return _truck("fire truck", W=4.2, wr=1.0, ww=0.8, front=-6.6, hood=0.7, cab=2.6, belt=2.8, hood_y=2.6, nose_y=2.2, roofy=4.2, ws_run=0.5,
                  axles=(-5.2, 2.6, 4.2), rear="ladder", rear_len=7.0, rear_h=2.2, rear_y=1.25, frame_y=1.25, lightbar="red", rim="truck",
                  preview=pv("#D22B2B", "#F2F2F2"))


@hero("garbage truck", FAM)
def garbage_truck():
    return _truck("garbage truck", W=4.2, wr=1.0, ww=0.8, front=-6.0, hood=0.6, cab=2.4, belt=2.8, hood_y=2.6, nose_y=2.2, roofy=4.2, ws_run=0.5,
                  axles=(-4.7, 2.0, 3.6), rear="garbage", rear_len=5.4, rear_h=3.4, rear_y=1.25, frame_y=1.25, rim="truck",
                  preview=pv("#2E8B57", "#E8E8E8"))


@hero("cement mixer", FAM)
def cement_mixer():
    return _truck("cement mixer", W=4.1, wr=1.0, ww=0.8, front=-6.0, hood=1.9, cab=2.1, belt=2.8, hood_y=2.6, nose_y=2.2, roofy=4.2,
                  axles=(-4.5, 1.9, 3.5), rear="mixer", rear_len=5.2, rear_h=2.4, frame_y=1.25, rim="truck", stack=True,
                  preview=pv("#F2F2F2", "#E86A17"))


@hero("dump truck", FAM)
def dump_truck():
    return _truck("dump truck", W=4.4, wr=1.15, ww=0.95, front=-5.6, hood=1.9, cab=2.2, belt=3.0, hood_y=2.75, nose_y=2.35, roofy=4.4,
                  axles=(-4.0, 2.0, 3.6), rear="dump", rear_len=5.0, rear_h=1.9, frame_y=1.4, rim="truck", knobby=0.05, stack=True,
                  preview=pv("#F2B705", "#3A3A3A"))


@hero("truck", FAM)
def semi_truck():
    """Tractor unit with a long box trailer (fifth wheel, landing legs, tandem trailer axle)."""
    return _truck("truck", W=4.2, wr=1.0, ww=0.8, front=-9.0, hood=2.6, cab=2.5, belt=3.0, hood_y=2.7, nose_y=2.3, roofy=4.6,
                  axles=(-7.3, -2.6, 6.3), rear="trailer", rear_len=11.0, rear_h=3.8, rear_y=1.6, frame_y=1.3, rim="truck",
                  stack=True, rear_col="secondary", preview=pv("#2F5D8A", "#C9CED6"))


@hero("tanker truck", FAM)
def tanker_truck():
    return _truck("tanker truck", W=4.2, wr=1.0, ww=0.8, front=-8.0, hood=2.4, cab=2.4, belt=3.0, hood_y=2.7, nose_y=2.3, roofy=4.5,
                  axles=(-6.4, -2.4, 4.0, 5.5), rear="tanker", rear_len=9.0, rear_h=2.5, frame_y=1.3, rim="truck", stack=True,
                  rear_col="metal", preview=pv("#D9D9D9", "#C8102E"))


# ==================================================================================================== buses
def _bus(hid, L=13.0, W=4.2, H_=4.2, wr=0.95, school=False, decker=False, preview=None):
    """Bus: one box body (rounded), a raked windshield (translucent glass, driver seat visible), side window band
    with black pillars, folding front doors, destination sign; school bus has the hood, stop arm and black rub rails."""
    H = _new(hid, preview, ("vehicle", "bus"))
    hw = W / 2
    zn = -L / 2
    zt = L / 2
    hood = 1.6 if school else 0.0
    zb = zn + hood
    floor = 1.25
    H.bone("Chassis", "Body", (0, wr + 0.3, 0))
    axles = (zb + 1.6 if school else zn + 2.4, zt - 2.6)
    specs = []
    for i, z in enumerate(axles):
        tag = "F" if i == 0 else "B"
        specs.append(dict(name=f"Wheel{tag}R", pos=(hw - 0.42, wr, z), r=wr, w=0.75, side=1, steer=(i == 0)))
        specs.append(dict(name=f"Wheel{tag}L", pos=(-hw + 0.42, wr, z), r=wr, w=0.75, side=-1, steer=(i == 0)))
    wheels, steer = K.add_wheels(H, specs, rim="truck")
    top = floor + H_ + (2.4 if decker else 0)
    win_y0 = floor + 1.25
    # body side profile with arches, windshield notch at the front (glass fills it)
    pts, rad = [], []

    def a(p, r=0.0):
        pts.append(p)
        rad.append(r)

    a((zb + 0.1, floor - 0.6), 0.15)
    a((zb, floor + 0.6), 0.2)
    a((zb + 0.05, win_y0), 0.0)
    a((zb + 0.6, win_y0), 0.0)
    a((zb + 0.9, top - 0.35), 0.0)
    a((zb + 1.3, top), 0.35)
    a((zt - 0.4, top), 0.4)
    a((zt, top - 0.4), 0.15)
    a((zt, floor - 0.4), 0.15)
    a((zt - 0.3, floor - 0.6), 0.1)
    for z in axles[::-1]:
        ra = wr + 0.16
        dy = wr - (floor - 0.6)
        dz = math.sqrt(max(ra * ra - dy * dy, 0.01))
        a0 = math.atan2(-dy, dz)
        for k in range(13):
            an = a0 + (math.pi - 2 * a0) * k / 12
            a((z + ra * math.cos(an), wr + ra * math.sin(an)))
    body = extrude(round_poly(np.array(pts), rad, 3), W, bevel=0.2, seg=3)
    body = warp(body, lambda V: np.column_stack([V[:, 0] * (1 - 0.05 * np.clip((V[:, 1] - (top - 0.5)) / 0.5, 0, 1)), V[:, 1], V[:, 2]]))
    piece(H, "Chassis", "Chassis", body, col="primary", mat="metal", pri=0.5)
    if school:
        hp = round_poly(np.array([(zn + 0.1, floor - 0.6), (zn, floor + 0.2), (zn + 0.2, floor + 0.9), (zb + 0.3, floor + 1.2), (zb + 0.3, floor - 0.6)]), [0.1, 0.15, 0.3, 0.0, 0.0], 3)
        hoodm = warp(extrude(hp, W * 0.75, bevel=0.15, seg=2), lambda V: np.column_stack([V[:, 0] * np.interp(V[:, 2], [zn, zb], [0.85, 1.0]), V[:, 1], V[:, 2]]))
        fend = [xf(extrude(round_poly(np.array([(zn + 0.6, floor - 0.2), (zn + 0.8, floor + 0.55), (zb + 0.3, floor + 0.8), (zb + 0.3, floor - 0.3)]), 0.2, 2), 0.7, bevel=0.1), (s * (hw - 0.4), 0, 0)) for s in (-1, 1)]
        piece(H, "Hood", "Chassis", merge(hoodm, *fend), col="primary", mat="metal", pri=0.7)
        gr = merge(box((1.4, 0.8, 0.1), (0, floor + 0.35, zn - 0.02), r=0.05))
        piece(H, "Grille", "Chassis", gr, col="metal", mat="metal", role="detail", pri=1.4)
        K.lamp_pair(H, "Headlight", "Chassis", (1.05, floor + 0.45, zn + 0.05), r=0.2, depth=0.14)
        # stop arm (folds out in the Attack)
        H.bone("StopArm", "Chassis", (-hw - 0.05, floor + 1.5, zb + 1.2))
        sign = K.lathe_profile([(-0.04, 0), (-0.04, 0.42), (0.04, 0.42), (0.04, 0)], 8, "x")
        sign = xf(sign, (-hw - 0.12, floor + 1.5, zb + 1.2), r=(22.5, 0, 0))
        piece(H, "StopSign", "StopArm", sign, col="red", mat="plastic", role="detail", pri=1.4)
        rails = merge(*[cbox((0.05, 0.12, L - hood - 0.5), (s * (hw + 0.02), y, (zb + zt) / 2 + 0.1), c=0.02) for s in (-1, 1) for y in (floor + 0.3, floor + 1.0, win_y0 + 1.55)])
        piece(H, "Rails", "Chassis", rails, col="black", mat="plastic", role="detail", pri=1.5)
    else:
        K.lamp_pair(H, "Headlight", "Chassis", (hw - 0.5, floor + 0.2, zb - 0.06), shape="rect", w=0.6, h=0.3, depth=0.16)
        gr = box((2.0, 0.4, 0.08), (0, floor + 0.2, zb - 0.03), r=0.04)
        piece(H, "Grille", "Chassis", gr, col="darker", mat="metal", role="detail", pri=1.4)
    # windshield glass block filling the notch (translucent: driver seat shows)
    wp = np.array([(zb - 0.0, win_y0 - 0.05), (zb + 0.75, win_y0 - 0.05), (zb + 1.05, top - 0.3), (zb + 0.95, top - 0.3)])
    wsg = extrude(np.array([(zb + 0.02, win_y0 - 0.1), (zb + 0.95, win_y0 - 0.1), (zb + 1.25, top - 0.25), (zb + 0.92, top - 0.25)]), W - 0.25, bevel=0.06, seg=1)
    piece(H, "Glass", "Chassis", wsg, col="glass", mat="glass", role="window", pri=0.8, tr=0.25, ao=False)
    # side windows: dark glass band proud of the skin, black pillars over it
    rows = [(win_y0, win_y0 + 1.3)] + ([(floor + H_ + 0.6, floor + H_ + 1.8)] if decker else [])
    wins, pills = [], []
    zw0, zw1 = zb + 1.6, zt - 0.6
    for y0, y1 in rows:
        for s in (-1, 1):
            wins.append(cbox((0.05, y1 - y0, zw1 - zw0), (s * (hw + 0.01), (y0 + y1) / 2, (zw0 + zw1) / 2), c=0.02))
            for z in np.linspace(zw0, zw1, 7 if not school else 8):
                pills.append(cbox((0.08, y1 - y0 + 0.06, 0.16), (s * (hw + 0.035), (y0 + y1) / 2, z), c=0.02))
        wins.append(cbox((W - 0.6, y1 - y0 - 0.2, 0.05), (0, (y0 + y1) / 2 + 0.1, zt + 0.01), c=0.02))
    # door (right side, front): glass panels + frame
    dz = zb + 0.95 if not school else zb + 0.9
    wins.append(cbox((0.05, 2.3, 0.95), (hw + 0.01, floor + 1.2, dz + 0.0), c=0.02))
    pills.append(cbox((0.08, 2.4, 0.08), (hw + 0.035, floor + 1.2, dz), c=0.02))
    piece(H, "Windows", "Chassis", merge(*wins), col="glass", mat="glass", role="window", pri=1.0)
    piece(H, "Pillars", "Chassis", merge(*pills), col="darker", mat="plastic", role="detail", pri=1.3)
    sign = box((W * 0.6, 0.4, 0.08), (0, top - 0.32, zb + 1.08), r=0.04, rot_=(-18, 0, 0))
    piece(H, "DestSign", "Chassis", sign, col=AMBER if not school else "black", mat="glass", role="light", pri=1.7, ao=False)
    bump = merge(box((W + 0.1, 0.35, 0.35), (0, floor - 0.45, zn - 0.1), r=0.1), box((W + 0.1, 0.35, 0.35), (0, floor - 0.45, zt + 0.1), r=0.1))
    piece(H, "Bumpers", "Chassis", bump, col="black" if school else "darker", mat="plastic", role="detail", pri=1.3)
    tl = K.lamp((hw - 0.3, floor + 0.4, zt + 0.02), 0, 0.1, axis="+z", shape="rect", w=0.3, h=0.6)
    mpiece(H, "Taillight#", "Chassis", tl, col=RED_L, mat="glass", role="light", pri=1.6, ao=False)
    mir = merge(rod((hw, top - 1.0, zb + 0.4), (hw + 0.45, top - 0.9, zb - 0.2), 0.04, segs=6), box((0.15, 0.6, 0.3), (hw + 0.5, top - 1.25, zb - 0.25), r=0.05))
    mpiece(H, "Mirror#", "Chassis", mir, col="darker", mat="metal", role="detail", pri=1.8)
    seat = K.seat_mesh((-hw + 0.9, floor + 0.55, zb + 1.5), w=0.85, d=0.8, back=1.1)
    piece(H, "Seat", "Chassis", seat, col="darker", mat="cloth", role="seat", pri=1.1)
    sw = K.steering_mesh((-hw + 0.9, floor + 1.15, zb + 0.75), r=0.38, tilt=25, col_len=0.4)
    piece(H, "Steering", "Chassis", sw, col="darker", mat="plastic", role="detail", pri=1.6)

    def extra(pose, s):
        if school:
            K.add(pose, "StopArm", (0, 0, 0, 0, -1.45 * K._bump(s, 0.05, 0.95), 0))

    _finish(H, wheels, steer, top, L, (-hw + 0.9, floor + 0.65, zb + 1.5), (0, floor, zn - 0.4), (hw - 0.5, floor - 0.5, zt + 0.3),
            sym=8, attack="honk" if school else "ram", extra_attack=extra if school else None)
    return H


@hero("bus", FAM)
def bus():
    return _bus("bus", preview=pv("#2B6CB0", "#F2F2F2"))


@hero("school bus", FAM)
def school_bus():
    return _bus("school bus", L=13.5, school=True, preview=pv("#F7B500", "#1A1A1A"))


@hero("double decker bus", FAM)
def double_decker():
    return _bus("double decker bus", L=12.0, decker=True, preview=pv("#C8102E", "#F2E8CF"))


# ==================================================================================================== tracked + work machines
def _clips_tracked(H, wheels, height, length, extra_attack=None, extra_idle=None, extra_move=None, attack="ram"):
    K.vehicle_clips(H, wheels, susp="Chassis", height=height, length=length, sym=10, attack=attack, roll=0.4, bob=0.6,
                    extra_attack=extra_attack, extra_idle=extra_idle, extra_move=extra_move, turns=1.0)


def _cab_box(H, bone, x0, x1, y0, y1, z0, z1, col="primary", post=0.14, glass_tr=0.22, name="Cab"):
    """Boxy machine cab: translucent glass block + corner posts + roof slab (seat inside shows)."""
    g = box((x1 - x0 - 0.1, y1 - y0 - 0.05, z1 - z0 - 0.1), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), r=0.05)
    piece(H, name + "Glass", bone, g, col="glass", mat="glass", role="window", pri=0.9, tr=glass_tr, ao=False)
    posts = [cbox((post, y1 - y0, post), (x, (y0 + y1) / 2, z), c=0.03) for x in (x0 + post / 2 - 0.02, x1 - post / 2 + 0.02) for z in (z0 + post / 2 - 0.02, z1 - post / 2 + 0.02)]
    roof = box((x1 - x0 + 0.2, 0.16, z1 - z0 + 0.25), ((x0 + x1) / 2, y1 + 0.06, (z0 + z1) / 2), r=0.06)
    piece(H, name, bone, merge(roof, *posts), col=col, mat="metal", role="body", pri=0.8)


@hero("bulldozer", FAM)
def bulldozer():
    H = _new("bulldozer", pv("#F2A900", "#2B2B2B"), ("vehicle", "construction"))
    H.bone("Chassis", "Body", (0, 1.2, 0))
    wheels = K.tracks(H, "Body", 1.75, -2.6, 2.4, 1.0, r_end=0.7, n_road=5, r_road=0.32)
    frame = box((2.4, 0.7, 5.0), (0, 0.9, -0.1), r=0.1)
    piece(H, "Frame", "Body", frame, col="darker", mat="metal", role="detail", pri=1.0)
    eng = round_poly(np.array([(-2.6, 1.3), (-2.6, 2.75), (-2.3, 2.9), (0.0, 2.9), (0.0, 1.3)]), [0.1, 0.1, 0.25, 0.0, 0.0], 3)
    body = merge(extrude(eng, 2.6, bevel=0.12, seg=2), box((3.9, 0.15, 5.0), (0, 1.55, -0.1), r=0.05), box((2.8, 1.3, 2.0), (0, 2.0, 1.4), r=0.12))
    piece(H, "Chassis", "Chassis", body, col="primary", mat="metal", pri=0.5)
    grille = merge(*[cbox((1.9, 0.07, 0.06), (0, 1.6 + 0.18 * k, -2.64), c=0.015) for k in range(7)])
    stack = merge(K.tube_ring(0.15, 0.11, 1.4, axis="y", pos=(0.7, 3.5, -1.6)), cyl(0.06, 0.2, (0.7, 4.2, -1.6), "y", segs=10))
    piece(H, "Grille", "Chassis", merge(grille, stack), col="darker", mat="metal", role="detail", pri=1.3)
    _cab_box(H, "Chassis", -1.25, 1.25, 2.7, 4.7, 0.3, 2.3)
    seat = K.seat_mesh((0, 3.05, 1.45), w=1.0, d=0.85, back=1.1)
    piece(H, "Seat", "Chassis", seat, col="darker", mat="cloth", role="seat", pri=1.1)
    levers = merge(*(rod((x, 2.8, 0.75), (x, 3.5, 0.6), 0.04, segs=6) for x in (-0.3, 0.3)))
    piece(H, "Levers", "Chassis", levers, col="darker", mat="metal", role="detail", pri=1.8)
    # blade on push arms (raises/slams in the Attack)
    H.bone("Blade", "Chassis", (0, 1.2, -1.0))
    bp = round_poly(np.array([(-4.0, 0.05), (-3.6, 0.05), (-3.35, 0.6), (-3.35, 1.9), (-3.6, 2.4), (-4.0, 2.45)]), [0, 0.05, 0.4, 0.4, 0.05, 0], 4)
    blade = extrude(bp, 4.6, bevel=0.06, seg=1)
    arms = merge(*[bar((s * 1.6, 0.9, -0.8), (s * 1.6, 0.8, -3.55), 0.25, 0.35) for s in (-1, 1)],
                 *[rod((s * 0.6, 2.8, -2.6), (s * 0.7, 1.6, -3.5), 0.12, segs=10) for s in (-1, 1)])
    edge = cbox((4.6, 0.12, 0.2), (0, 0.08, -3.95), c=0.03)
    piece(H, "Blade", "Blade", blade, col="primary", mat="metal", role="body", pri=0.7)
    piece(H, "BladeArms", "Blade", merge(arms, edge), col="darker", mat="metal", role="detail", pri=1.2)
    rip = merge(bar((0, 1.5, 2.4), (0, 1.0, 3.3), 0.3, 0.3), bar((0, 1.0, 3.3), (0, 0.1, 3.1), 0.25, 0.4), cbox((1.6, 0.3, 0.3), (0, 1.2, 2.6), c=0.05))
    piece(H, "Ripper", "Chassis", rip, col="darker", mat="metal", role="detail", pri=1.4)
    K.lamp_pair(H, "Worklight", "Chassis", (0.95, 4.65, 0.2), r=0.14, depth=0.12)
    K.mount(H, "Seat", (0, 3.15, 1.45), (1.0, 0.2, 0.85), "Chassis")
    H.socket("head", (0, 5.0, 1.3), "Chassis")
    H.socket("mouth", (0, 1.0, -4.1), "Blade")
    H.socket("exhaust", (0.7, 4.3, -1.6), "Chassis")
    H.rig.update({"head": "Chassis"})

    def atk(pose, s):
        up = K._bump(s, 0.0, 0.4)
        slam = K._bump(s, 0.35, 0.8)
        K.add(pose, "Blade", (0, 0.5 * up - 0.15 * slam, 0, 0.12 * up - 0.06 * slam, 0, 0))

    def mv(pose, u):
        K.add(pose, "Blade", (0, 0.04 * math.sin(TAU * u * 2), 0, 0, 0, 0))

    _clips_tracked(H, wheels, 4.7, 7.5, extra_attack=atk, extra_move=mv)
    return H


@hero("excavator", FAM)
def excavator():
    H = _new("excavator", pv("#F2B705", "#2B2B2B"), ("vehicle", "construction"))
    H.bone("Chassis", "Body", (0, 1.2, 0))
    wheels = K.tracks(H, "Body", 1.65, -2.4, 2.4, 1.0, r_end=0.6, n_road=5, r_road=0.3)
    under = merge(box((2.2, 0.6, 4.4), (0, 0.85, 0), r=0.08), cyl(0.4, 1.0, (0, 1.35, 0), "y", segs=20))
    piece(H, "Undercarriage", "Body", under, col="darker", mat="metal", role="detail", pri=0.9)
    H.bone("Turret", "Chassis", (0, 1.6, 0))
    house = merge(box((3.4, 1.5, 3.6), (0, 2.3, 0.6), r=0.12), extrude(round_poly(np.array([(1.8, 1.55), (1.8, 3.0), (2.8, 2.95), (3.0, 1.55)]), [0, 0.1, 0.5, 0.2], 4), 3.4, bevel=0.12))
    piece(H, "Chassis", "Turret", house, col="primary", mat="metal", pri=0.5)
    _cab_box(H, "Turret", -1.65, -0.15, 3.05, 5.0, -1.3, 0.6)
    seat = K.seat_mesh((-0.9, 3.35, -0.2), w=0.9, d=0.8, back=1.0)
    piece(H, "Seat", "Turret", seat, col="darker", mat="cloth", role="seat", pri=1.1)
    det = merge(K.tube_ring(0.12, 0.09, 1.0, axis="y", pos=(1.2, 3.5, 1.6)), cbox((1.5, 0.08, 1.2), (0.85, 3.07, 1.0), c=0.02),
                *[cbox((0.06, 0.6, 1.0), (1.72, 2.4, z), c=0.02) for z in (1.0, 1.4)])
    piece(H, "EngineDeck", "Turret", det, col="darker", mat="metal", role="detail", pri=1.5)
    # boom chain
    H.bone("Boom", "Turret", (0.5, 2.6, -1.2))
    H.bone("Stick", "Boom", (0.5, 5.4, -4.2))
    H.bone("Bucket", "Stick", (0.5, 2.6, -5.4))
    boomp = round_poly(np.array([(-1.0, 2.4), (-1.4, 3.3), (-4.4, 5.75), (-4.2, 5.05), (-1.6, 2.6)]), [0.15, 0.3, 0.25, 0.2, 0.2], 3)
    boom = xf(extrude(boomp, 0.55, bevel=0.06, seg=1), (0.5, 0, 0))
    piece(H, "BoomArm", "Boom", boom, col="primary", mat="metal", role="limb", pri=0.7)
    stick = bar((0.5, 5.4, -4.35), (0.5, 2.6, -5.45), 0.45, 0.5, r=0.06)
    piece(H, "StickArm", "Stick", stick, col="primary", mat="metal", role="limb", pri=0.8)
    rams = merge(rod((0.5, 2.7, -0.9), (0.5, 4.3, -2.5), 0.1, segs=8), rod((0.5, 5.75, -3.7), (0.5, 5.6, -4.6), 0.09, segs=8))
    piece(H, "Rams", "Boom", rams, col="metal", mat="metal", role="detail", pri=1.4)
    bk = round_poly(np.array([(-5.2, 2.75), (-6.3, 2.2), (-6.4, 1.35), (-5.6, 1.15), (-5.15, 2.0)]), [0, 0.2, 0.3, 0.2, 0.1], 3)
    bucket = xf(extrude(bk, 1.2, bevel=0.06, seg=1), (0.5, 0, 0))
    teeth = merge(*[xf(K.lathe_profile([(0, 0.08), (0.3, 0.0)], 6, "z"), (0.5 + dx, 1.2, -6.45), r=(15, 0, 0)) for dx in (-0.45, -0.15, 0.15, 0.45)])
    piece(H, "BucketP", "Bucket", bucket, col="darker", mat="metal", role="detail", pri=0.9)
    piece(H, "Teeth", "Bucket", teeth, col="metal", mat="metal", role="detail", pri=1.7)
    K.mount(H, "Seat", (-0.9, 3.45, -0.2), (0.9, 0.2, 0.8), "Turret")
    H.socket("head", (0, 5.3, 0), "Turret")
    H.socket("mouth", (0.5, 1.5, -6.4), "Bucket")
    H.socket("exhaust", (1.2, 4.0, 1.6), "Turret")
    H.rig.update({"head": "Turret"})

    def atk(pose, s):
        sw = K._bump(s, 0.0, 1.0)
        dig = K._bump(s, 0.25, 0.75)
        K.add(pose, "Turret", (0, 0, 0, 0, 0.35 * math.sin(math.pi * s) * (1 - s), 0))
        K.add(pose, "Boom", (0, 0, 0, 0.25 * sw - 0.45 * dig, 0, 0))
        K.add(pose, "Stick", (0, 0, 0, -0.5 * dig, 0, 0))
        K.add(pose, "Bucket", (0, 0, 0, 0.9 * dig, 0, 0))

    def idl(pose, u):
        K.add(pose, "Boom", (0, 0, 0, 0.03 * math.sin(TAU * u), 0, 0))
        K.add(pose, "Bucket", (0, 0, 0, 0.08 * math.sin(TAU * u + 1), 0, 0))

    def mv(pose, u):
        K.add(pose, "Stick", (0, 0, 0, 0.05 * math.sin(TAU * u * 2), 0, 0))

    _clips_tracked(H, wheels, 5.0, 7.0, extra_attack=atk, extra_idle=idl, extra_move=mv)
    return H


@hero("tank", FAM)
def tank():
    """Main battle tank: sloped hull with fenders and side skirts over the tracks, turret with mantlet and long
    fume-extracted gun (recoils), commander's cupola with an open hatch and seat, MG, smoke launchers, tow hooks."""
    H = _new("tank", pv("#5B6B3A", "#3A4428"), ("vehicle", "military"))
    H.bone("Chassis", "Body", (0, 1.3, 0))
    wheels = K.tracks(H, "Body", 1.75, -3.0, 3.0, 1.05, r_end=0.62, n_road=6, r_road=0.42, wheel_col="secondary", cleats=30)
    hp = round_poly(np.array([(-4.0, 1.25), (-3.6, 0.6), (3.6, 0.6), (3.95, 1.0), (3.9, 2.0), (1.8, 2.15), (-2.3, 2.15)]), [0.05, 0.1, 0.1, 0.1, 0.08, 0.05, 0.08], 2)
    hull = extrude(hp, 3.2, bevel=0.1, seg=2)
    fend = merge(*[xf(extrude(round_poly(np.array([(-4.1, 1.7), (-3.4, 1.98), (3.85, 1.98), (4.0, 1.75), (3.85, 1.6), (-3.4, 1.6)]), 0.05, 1), 1.25, bevel=0.04), (s * 1.9, 0, 0)) for s in (-1, 1)])
    piece(H, "Chassis", "Chassis", merge(hull, fend), col="primary", mat="metal", pri=0.5)
    skirts = merge(*[xf(extrude(round_poly(np.array([(-3.3, 1.05), (-3.5, 1.65), (3.7, 1.65), (3.7, 1.05)]), 0.08, 1), 0.08, bevel=0.02), (s * 2.55, 0, 0)) for s in (-1, 1)])
    bolts = merge(*[cbox((0.06, 0.12, 0.12), (s * 2.6, 1.5, z), c=0.02) for s in (-1, 1) for z in np.linspace(-3.0, 3.4, 9)])
    piece(H, "Skirts", "Chassis", merge(skirts, bolts), col="secondary", mat="metal", role="detail", pri=0.9)
    dets = merge(*[cyl(0.5, 0.12, (s * 1.2, 1.5, -3.9), "x", segs=8) for s in (-1, 1)], box((1.4, 0.4, 0.6), (0, 2.25, 3.3), r=0.05),
                 *[cbox((0.5, 0.1, 0.8), (x, 2.2, 2.6), c=0.02) for x in (-0.9, 0.9)], rod((-1.4, 2.2, -2.6), (1.4, 2.2, -2.6), 0.06, segs=6))
    piece(H, "HullDetail", "Chassis", dets, col="darker", mat="metal", role="detail", pri=1.6)
    # driver's hatch periscopes
    H.bone("Turret", "Chassis", (0, 2.15, 0.3))
    tp = round_poly(np.array([(-2.0, 2.15), (-2.1, 2.55), (-1.6, 3.15), (1.4, 3.2), (2.6, 3.0), (2.7, 2.15)]), [0.05, 0.15, 0.2, 0.15, 0.2, 0.05], 2)
    tur = warp(extrude(tp, 2.9, bevel=0.15, seg=2), lambda V: np.column_stack([V[:, 0] * np.interp(V[:, 2], [-2.1, -1.4, 2.7], [0.7, 1.0, 0.92]), V[:, 1], V[:, 2]]))
    piece(H, "TurretP", "Turret", tur, col="primary", mat="metal", role="body", pri=0.6)
    H.bone("Gun", "Turret", (0, 2.7, -2.0))
    mant = box((1.1, 0.75, 0.5), (0, 2.7, -2.15), r=0.12, seg=1)
    gun = merge(K.lathe_profile([(-2.2, 0), (-2.2, 0.17), (-5.0, 0.15), (-6.4, 0.13), (-6.4, 0.0)], 14, "z"),
                K.lathe_profile([(-4.6, 0), (-4.6, 0.18), (-4.5, 0.24), (-3.9, 0.24), (-3.8, 0.17), (-3.8, 0)], 14, "z"),
                K.tube_ring(0.18, 0.09, 0.4, axis="z", pos=(0, 0, -6.25)))
    gun = xf(gun, (0, 2.7, 0))
    piece(H, "Mantlet", "Gun", mant, col="secondary", mat="metal", role="detail", pri=0.9)
    piece(H, "Barrel", "Gun", gun, col="primary", mat="metal", role="detail", pri=0.7)
    cup = merge(cyl(0.35, 0.5, (0.75, 3.35, 0.7), "y", segs=16), *[cbox((0.18, 0.12, 0.1), (0.75 + 0.45 * math.cos(a), 3.4, 0.7 + 0.45 * math.sin(a)), c=0.02) for a in np.linspace(0, TAU, 6, endpoint=False)])
    hatch = cyl(0.08, 0.48, (0.75, 3.95, 1.25), "z", segs=16, r=(75, 0, 0))
    mg = merge(rod((-0.7, 3.45, 0.6), (-0.7, 3.45, -0.6), 0.05, segs=6), cbox((0.18, 0.25, 0.5), (-0.7, 3.42, 0.7), c=0.03), rod((-0.7, 3.2, 0.7), (-0.7, 3.4, 0.7), 0.05, segs=6))
    smoke = merge(*[xf(cyl(0.35, 0.08, (0, 0, 0), "z", segs=8), (s * (1.3 + 0.12 * k), 2.75 + 0.15 * (k % 2), -1.55), r=(25, s * 20, 0)) for s in (-1, 1) for k in range(3)])
    bustle = box((2.4, 0.08, 0.5), (0, 3.15, 2.55), r=0.02)
    piece(H, "Cupola", "Turret", merge(cup, hatch, bustle), col="secondary", mat="metal", role="detail", pri=1.1)
    piece(H, "TurretGear", "Turret", merge(mg, smoke), col="darker", mat="metal", role="detail", pri=1.6)
    seat = K.seat_mesh((0.75, 3.45, 0.75), w=0.55, d=0.45, back=0.4, bucket=False)
    piece(H, "Seat", "Turret", seat, col="darker", mat="cloth", role="seat", pri=1.3)
    ant = rod((-1.0, 3.1, 2.3), (-1.05, 5.2, 2.5), 0.02, segs=4)
    piece(H, "Antenna", "Turret", ant, col="darker", mat="metal", role="detail", pri=2.4)
    star = K.lathe_profile([(-0.02, 0), (-0.02, 0.32), (0.02, 0.32), (0.02, 0)], 5, "x")
    piece(H, "Star", "Turret", xf(star, (1.38, 2.7, 0.6), r=(0, 0, 0)), col="white", mat="plastic", role="detail", pri=2.0)
    K.mount(H, "Seat", (0.75, 3.55, 0.75), (0.55, 0.2, 0.45), "Turret")
    H.socket("head", (0, 3.6, 0.3), "Turret")
    H.socket("mouth", (0, 2.7, -6.5), "Gun")
    H.socket("muzzle", (0, 2.7, -6.5), "Gun")
    H.socket("exhaust", (0, 2.0, 4.0), "Chassis")
    H.rig.update({"head": "Turret"})

    def atk(pose, s):
        aim = K._ease(s / 0.3) if s < 0.3 else 1.0
        rec = K._bump(s, 0.35, 0.7)
        back = 1 - K._ease((s - 0.75) / 0.25) if s > 0.75 else 1.0
        K.add(pose, "Gun", (0, 0, 0.7 * rec, 0.06 * aim * back, 0, 0))
        K.add(pose, "Chassis", (0, 0, 0.15 * rec, 0.05 * rec, 0, 0))

    def idl(pose, u):
        K.add(pose, "Turret", (0, 0, 0, 0, 0.25 * math.sin(TAU * u), 0))

    _clips_tracked(H, wheels, 3.4, 8.0, extra_attack=atk, extra_idle=idl)
    return H


@hero("armored car", FAM)
def armored_car():
    H = _new("armored car", pv("#55603F", "#2E3324"), ("vehicle", "military"))
    W, wr = 3.9, 0.9
    H.bone("Chassis", "Body", (0, wr + 0.3, 0))
    specs = []
    for i, z in enumerate((-2.6, 0.0, 2.6)):
        specs += [dict(name=f"W{i}R", pos=(1.6, wr, z), r=wr, w=0.75, side=1, steer=(i == 0)), dict(name=f"W{i}L", pos=(-1.6, wr, z), r=wr, w=0.75, side=-1, steer=(i == 0))]
    wheels, steer = K.add_wheels(H, specs, rim="truck", knobby=0.06, rim_col="secondary")
    hp = round_poly(np.array([(-4.0, 1.1), (-4.2, 1.7), (-2.6, 2.6), (-1.4, 3.4), (2.6, 3.4), (3.8, 2.9), (3.9, 1.1), (3.4, 0.8), (-3.4, 0.8)]),
                    [0.05, 0.08, 0.05, 0.1, 0.1, 0.08, 0.05, 0.08, 0.08], 2)
    hull = warp(extrude(hp, W, bevel=0.1, seg=1), lambda V: np.column_stack([V[:, 0] * (1 - 0.18 * np.clip((V[:, 1] - 2.0) / 1.4, 0, 1)), V[:, 1], V[:, 2]]))
    piece(H, "Chassis", "Chassis", hull, col="primary", mat="metal", pri=0.5)
    slits = merge(*[cbox((0.7, 0.12, 0.06), (x, 2.95, -1.95), c=0.02, rot_=(-34, 0, 0)) for x in (-0.6, 0.6)],
                  *[cbox((0.06, 0.14, 0.7), (s * 1.62, 2.75, z), c=0.02) for s in (-1, 1) for z in (-0.8, 0.6)])
    piece(H, "Slits", "Chassis", slits, col="glass", mat="glass", role="window", pri=1.4)
    H.bone("Turret", "Chassis", (0, 3.4, 0.4))
    tur = merge(cyl(0.8, 0.85, (0, 3.75, 0.4), "y", segs=18), cyl(0.1, 0.95, (0, 3.42, 0.4), "y", segs=18))
    piece(H, "TurretP", "Turret", tur, col="secondary", mat="metal", role="body", pri=0.8)
    H.bone("Gun", "Turret", (0, 3.85, -0.4))
    gun = merge(K.lathe_profile([(-0.3, 0), (-0.3, 0.12), (-2.4, 0.08), (-2.4, 0)], 10, "z"), box((0.5, 0.4, 0.4), (0, 0, -0.2), r=0.06))
    piece(H, "Barrel", "Gun", xf(gun, (0, 3.85, 0)), col="darker", mat="metal", role="detail", pri=0.9)
    # open roof hatch with seat behind the turret
    seat = K.seat_mesh((0, 3.45, 1.7), w=0.7, d=0.6, back=0.6, bucket=False)
    hatch = merge(K.torus(0.42, 0.06, "y", 16, 4, pos=(0, 3.42, 1.7)), cyl(0.08, 0.42, (0, 3.85, 2.2), "z", segs=14, r=(70, 0, 0)))
    piece(H, "Seat", "Chassis", seat, col="darker", mat="cloth", role="seat", pri=1.2)
    piece(H, "Hatch", "Chassis", hatch, col="secondary", mat="metal", role="detail", pri=1.4)
    gear = merge(*[box((0.8, 0.2, 0.25), (0, 1.1, z), r=0.05) for z in (-4.2, 3.95)], *[cyl(0.3, 0.17, (s * 1.0, 1.7, -4.12), "z", segs=10) for s in (-1, 1)],
                 cbox((0.25, 1.4, 0.25), (1.5, 1.3, 3.7), c=0.04))
    piece(H, "Bumpers", "Chassis", gear, col="darker", mat="metal", role="detail", pri=1.4)
    lens = merge(*[K.lamp((s * 1.0, 1.7, -4.28), 0.13, 0.06) for s in (-1, 1)])
    piece(H, "Lamps", "Chassis", lens, col=LENS, mat="glass", role="light", pri=1.8, ao=False)
    _finish(H, wheels, steer, 4.2, 8.2, (0, 3.55, 1.7), (0, 3.85, -2.6), (1.5, 2.0, 3.9))
    H.socket("muzzle", (0, 3.85, -2.5), "Gun")

    def atk(pose, s):
        K.add(pose, "Gun", (0, 0, 0.3 * K._bump(s, 0.3, 0.55) + 0.3 * K._bump(s, 0.55, 0.8), 0, 0, 0))
    K.vehicle_clips(H, wheels, susp="Chassis", height=4.2, length=8.2, sym=8, steer=steer, extra_attack=atk,
                    extra_idle=lambda p, u: K.add(p, "Turret", (0, 0, 0, 0, 0.3 * math.sin(TAU * u), 0)))
    return H


@hero("forklift", FAM)
def forklift():
    H = _new("forklift", pv("#F2A900", "#2B2B2B"), ("vehicle", "construction"))
    H.bone("Chassis", "Body", (0, 0.7, 0))
    specs = [dict(name="WheelFR", pos=(1.05, 0.6, -1.0), r=0.6, w=0.5, side=1), dict(name="WheelFL", pos=(-1.05, 0.6, -1.0), r=0.6, w=0.5, side=-1),
             dict(name="WheelBR", pos=(0.95, 0.45, 1.6), r=0.45, w=0.4, side=1, steer=True), dict(name="WheelBL", pos=(-0.95, 0.45, 1.6), r=0.45, w=0.4, side=-1, steer=True)]
    wheels, steer = K.add_wheels(H, specs, rim="steel", grooves=False)
    bp = round_poly(np.array([(-1.5, 0.35), (-1.5, 1.5), (0.6, 1.55), (1.0, 2.0), (2.35, 2.0), (2.4, 0.35)]), [0.1, 0.1, 0.1, 0.25, 0.3, 0.15], 3)
    body = extrude(bp, 2.2, bevel=0.14, seg=2)
    piece(H, "Chassis", "Chassis", body, col="primary", mat="metal", pri=0.5)
    cw = box((2.25, 1.2, 0.5), (0, 1.25, 2.3), r=0.15, seg=1)
    piece(H, "Counterweight", "Chassis", cw, col="darker", mat="metal", role="detail", pri=0.9)
    guard = [rod((s * 0.95, 1.5, -1.0), (s * 0.95, 3.6, -0.75), 0.07, segs=8) for s in (-1, 1)] + [rod((s * 0.95, 2.0, 1.6), (s * 0.95, 3.6, 1.4), 0.07, segs=8) for s in (-1, 1)]
    guard.append(box((2.05, 0.1, 2.35), (0, 3.62, 0.33), r=0.03))
    guard += [cbox((0.06, 0.06, 2.2), (x, 3.7, 0.33), c=0.01) for x in (-0.6, -0.2, 0.2, 0.6)]
    piece(H, "Guard", "Chassis", merge(*guard), col="darker", mat="metal", role="detail", pri=0.9)
    seat = K.seat_mesh((0, 2.0, 0.85), w=0.9, d=0.8, back=0.9)
    piece(H, "Seat", "Chassis", seat, col="darker", mat="cloth", role="seat", pri=1.0)
    sw = K.steering_mesh((0, 2.35, -0.15), r=0.25, tilt=35, col_len=0.5)
    piece(H, "Steering", "Chassis", sw, col="darker", mat="plastic", role="detail", pri=1.4)
    mast = merge(*[bar((s * 0.75, 0.35, -1.7), (s * 0.75, 4.3, -1.75), 0.18, 0.25, r=0.03) for s in (-1, 1)], cbox((1.7, 0.18, 0.2), (0, 4.25, -1.75), c=0.03),
                 cbox((1.7, 0.18, 0.2), (0, 2.2, -1.75), c=0.03))
    piece(H, "Mast", "Chassis", mast, col="darker", mat="metal", role="detail", pri=0.8)
    H.bone("Forks", "Chassis", (0, 0.5, -1.9))
    car_ = merge(box((1.6, 1.1, 0.12), (0, 1.0, -1.95), r=0.03), *[cbox((0.06, 1.0, 0.06), (x, 1.0, -2.02), c=0.01) for x in (-0.6, -0.2, 0.2, 0.6)])
    forks = merge(*[merge(cbox((0.18, 1.0, 0.1), (x, 0.9, -2.05), c=0.02), cbox((0.18, 0.09, 1.9), (x, 0.42, -2.95), c=0.02)) for x in (-0.45, 0.45)])
    piece(H, "Carriage", "Forks", car_, col="darker", mat="metal", role="detail", pri=1.0)
    piece(H, "ForkTines", "Forks", forks, col="metal", mat="metal", role="detail", pri=1.0)
    beacon = merge(cyl(0.15, 0.13, (0, 3.75, 1.2), "y", segs=10))
    piece(H, "Beacon", "Chassis", beacon, col=AMBER, mat="glass", role="light", pri=2.0, ao=False)
    K.lamp_pair(H, "Worklight", "Chassis", (0.85, 3.4, -0.9), r=0.12, depth=0.1)

    def atk(pose, s):
        K.add(pose, "Forks", (0, 1.4 * K._bump(s, 0.0, 0.7), 0, -0.1 * K._bump(s, 0.4, 0.8), 0, 0))

    def mv(pose, u):
        K.add(pose, "Forks", (0, 0.03 * math.sin(TAU * u * 2), 0, 0, 0, 0))

    _finish(H, wheels, steer, 3.7, 5.0, (0, 2.1, 0.85), (0, 0.5, -3.9), (0.8, 2.0, 2.5), extra_attack=atk, extra_move=mv)
    return H


@hero("tractor", FAM)
def tractor():
    H = _new("tractor", pv("#2E8B3A", "#F2C200"), ("vehicle", "farm"))
    H.bone("Chassis", "Body", (0, 1.3, 0))
    specs = [dict(name="WheelFR", pos=(1.25, 0.7, -2.4), r=0.7, w=0.5, side=1, steer=True), dict(name="WheelFL", pos=(-1.25, 0.7, -2.4), r=0.7, w=0.5, side=-1, steer=True),
             dict(name="WheelBR", pos=(1.5, 1.45, 1.1), r=1.45, w=0.85, side=1), dict(name="WheelBL", pos=(-1.5, 1.45, 1.1), r=1.45, w=0.85, side=-1)]
    wheels, steer = K.add_wheels(H, specs, rim="steel", rim_col="secondary", knobby=0.14, lugs=14)
    hp = round_poly(np.array([(-3.2, 1.0), (-3.25, 2.2), (-2.9, 2.5), (-0.3, 2.55), (-0.3, 1.0)]), [0.1, 0.25, 0.25, 0.0, 0.0], 3)
    hood = warp(extrude(hp, 1.4, bevel=0.12, seg=2), lambda V: np.column_stack([V[:, 0] * (1 + 0.15 * np.clip((V[:, 2] + 3.0) / 2.5, 0, 1)), V[:, 1], V[:, 2]]))
    trans = box((1.3, 1.3, 2.3), (0, 1.6, 0.6), r=0.12)
    piece(H, "Chassis", "Chassis", merge(hood, trans), col="primary", mat="metal", pri=0.5)
    grille = merge(box((1.15, 1.1, 0.1), (0, 1.75, -3.26), r=0.05))
    piece(H, "Grille", "Chassis", grille, col="darker", mat="metal", role="detail", pri=1.4)
    K.lamp_pair(H, "Headlight", "Chassis", (0.55, 2.2, -3.25), r=0.13, depth=0.1)
    fend = []
    for s in (-1, 1):
        arc = []
        for k in range(13):
            a = math.radians(-10 + 145 * k / 12)
            arc.append((1.1 + 1.72 * math.cos(math.pi - a) * -1 + 0.0, 1.45 + 1.72 * math.sin(a)))
        arc2 = [(1.1 - 1.72 * math.cos(math.radians(-10 + 145 * k / 12)), 1.45 + 1.72 * math.sin(math.radians(-10 + 145 * k / 12))) for k in range(13)]
        inner = [(1.1 - 1.55 * math.cos(math.radians(-10 + 145 * k / 12)), 1.45 + 1.55 * math.sin(math.radians(-10 + 145 * k / 12))) for k in range(12, -1, -1)]
        fend.append(xf(extrude(np.array(arc2 + inner), 1.0, bevel=0.05, seg=1), (s * 1.5, 0, 0)))
    piece(H, "Fenders", "Chassis", merge(*fend), col="primary", mat="metal", role="body", pri=0.8)
    _cab_box(H, "Chassis", -1.0, 1.0, 2.25, 4.6, -0.3, 2.0, col="primary")
    seat = K.seat_mesh((0, 2.6, 1.05), w=0.9, d=0.8, back=1.0)
    piece(H, "Seat", "Chassis", seat, col="darker", mat="cloth", role="seat", pri=1.1)
    sw = K.steering_mesh((0, 3.1, 0.15), r=0.3, tilt=35, col_len=0.6)
    stack = merge(K.tube_ring(0.12, 0.08, 1.8, axis="y", pos=(0.45, 3.2, -1.2)), cyl(0.06, 0.18, (0.45, 4.12, -1.2), "y", segs=10))
    piece(H, "Steering", "Chassis", sw, col="darker", mat="plastic", role="detail", pri=1.4)
    piece(H, "Stack", "Chassis", stack, col="metal", mat="metal", role="detail", pri=1.3)
    hitch = merge(cbox((1.6, 0.25, 0.3), (0, 0.8, 2.2), c=0.05), *[bar((s * 0.5, 1.0, 1.8), (s * 0.7, 0.7, 2.7), 0.12, 0.12) for s in (-1, 1)])
    weights = merge(*[cbox((1.3, 0.22, 0.4), (0, 0.95 + 0.25 * k, -3.6), c=0.04) for k in range(3)])
    piece(H, "Hitch", "Chassis", merge(hitch, weights), col="darker", mat="metal", role="detail", pri=1.5)
    _finish(H, wheels, steer, 4.6, 6.5, (0, 2.7, 1.05), (0, 1.5, -3.8), (0.45, 4.2, -1.2), attack="honk")
    return H


@hero("steamroller", FAM)
def steamroller():
    H = _new("steamroller", pv("#2F6E3B", "#C8102E"), ("vehicle", "construction"))
    H.bone("Chassis", "Body", (0, 1.2, 0))
    H.bone("Drum", "Body", (0, 1.05, -2.6))
    drum = merge(K.lathe_profile([(-1.4, 0), (-1.4, 0.95), (-1.35, 1.05), (1.35, 1.05), (1.4, 0.95), (1.4, 0)], 28, "x"),
                 K.lathe_profile([(1.38, 0), (1.38, 0.3), (1.48, 0.25), (1.5, 0)], 12, "x"), mirror(K.lathe_profile([(1.38, 0), (1.38, 0.3), (1.48, 0.25), (1.5, 0)], 12, "x")))
    piece(H, "DrumP", "Drum", xf(drum, (0, 1.05, -2.6)), col="metal", mat="metal", role="wheel", pri=0.6, fallback="Cylinder")
    specs = [dict(name="WheelBR", pos=(1.25, 0.95, 1.6), r=0.95, w=0.7, side=1), dict(name="WheelBL", pos=(-1.25, 0.95, 1.6), r=0.95, w=0.7, side=-1)]
    wheels, steer = K.add_wheels(H, specs, rim="steel", rim_col="secondary", grooves=False)
    yoke = merge(box((3.3, 0.3, 0.5), (0, 2.35, -2.6), r=0.06), *[cbox((0.2, 1.4, 0.4), (s * 1.6, 1.7, -2.6), c=0.04) for s in (-1, 1)], cyl(0.6, 0.35, (0, 2.6, -2.4), "y", segs=14))
    piece(H, "Yoke", "Chassis", yoke, col="secondary", mat="metal", role="detail", pri=0.9)
    bp = round_poly(np.array([(-2.2, 1.2), (-2.2, 2.6), (2.4, 2.6), (2.4, 1.0), (-1.5, 1.0)]), 0.15, 2)
    body = merge(extrude(bp, 2.0, bevel=0.12, seg=2), K.lathe_profile([(-2.0, 0), (-2.0, 0.55), (0.3, 0.55), (0.3, 0)], 18, "z"))
    body = merge(extrude(bp, 2.0, bevel=0.12, seg=2), xf(K.lathe_profile([(-2.0, 0), (-2.0, 0.55), (0.3, 0.55), (0.3, 0)], 18, "z"), (0, 2.9, 0)))
    piece(H, "Chassis", "Chassis", body, col="primary", mat="metal", pri=0.5)
    _cab_box(H, "Chassis", -1.1, 1.1, 2.6, 4.7, 0.6, 2.5, col="primary")
    seat = K.seat_mesh((0, 2.95, 1.7), w=0.9, d=0.8, back=0.9)
    piece(H, "Seat", "Chassis", seat, col="darker", mat="cloth", role="seat", pri=1.1)
    st = merge(K.tube_ring(0.18, 0.13, 1.6, axis="y", pos=(0, 3.9, -1.6)), cyl(0.12, 0.25, (0, 4.7, -1.6), "y", segs=12),
               K.steering_mesh((0, 3.35, 0.9), r=0.3, tilt=30, col_len=0.4))
    piece(H, "Stack", "Chassis", st, col="darker", mat="metal", role="detail", pri=1.3)
    wheels = [("Drum", 1.05)] + wheels
    _finish(H, wheels, steer, 4.7, 6.0, (0, 3.05, 1.7), (0, 1.0, -3.8), (0, 4.8, -1.6), attack="ram")
    return H


L = K.LAND
MAP = [
    ("pickup truck", "pickup truck, pickup, pick up truck, ute, tow truck, rescue truck", L),
    ("monster truck", "monster truck, monster bus, monster limo", L),
    ("van", "van, vans, minivan, camper van, campervan, police van, armored van, armoured van, camper trailer, delivery van", L),
    ("ambulance", "ambulance", L),
    ("ice cream truck", "ice cream truck, ice cream van", L),
    ("food truck", "food truck", L),
    ("delivery truck", "delivery truck, box truck, ice truck, moving truck", L),
    ("fire truck", "fire truck, fire engine, firetruck, ladder truck, crane truck, cherry picker, wrecking ball truck", L),
    ("garbage truck", "garbage truck, trash truck, dustcart, bin lorry, recycling truck", L),
    ("cement mixer", "cement mixer, concrete mixer, cement truck, mixer truck", L),
    ("dump truck", "dump truck, tipper truck, lava truck, mining truck", L),
    ("truck", "truck, trucks, lorry, semi, semi truck, big rig, tractor trailer, car transporter, log truck, convoy, parade float, flatbed", L),
    ("tanker truck", "tanker truck, tanker, water truck, fuel truck, oil truck", L),
    ("bus", "bus, buses, coach bus, party bus, battle bus, mobile library, trolleybus, city bus", L),
    ("school bus", "school bus", L),
    ("double decker bus", "double decker bus, double decker, tour bus", L),
    ("bulldozer", "bulldozer, dozer, snowplow, snow plow, snowcat, road grader, grader, skid steer, drill truck, mole machine", L),
    ("excavator", "excavator, digger, backhoe", L),
    ("tank", "tank, tanks, light tank, tank destroyer, flame tank, amphibious tank, super tank, command tank, snow tank, desert tank, pink tank, "
             "mine roller tank, bridge layer, tracked carrier, half track, turtle tank, robot tank, toy tank, panzer", L),
    ("armored car", "armored car, armoured car, bomb squad truck, rocket launcher truck, artillery truck, anti aircraft truck, humvee", L),
    ("forklift", "forklift, fork lift, scissor lift", L),
    ("tractor", "tractor, combine harvester, combine, crop sprayer, lawn mower, ride on mower, steam tractor, steam wagon", L),
    ("steamroller", "steamroller, steam roller, road roller, paver, ice resurfacer, zamboni", L),
]
