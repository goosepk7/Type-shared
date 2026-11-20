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
    d = {"primary": p, "secondary": s, "darker": "#2A2C31", "black": "#16171A"}
    d.update(kw)
    return d


def _new(hid, preview, tags=("vehicle", "truck")):
    H = Hero(hid, plan="Vehicle", gait="drive", tags=list(tags))
    H.preview = preview
    return H


def _finish(H, wheels, steer, height, length, seat_pos, nose, tail, sym=8, attack="ram", seat="Seat", enter=None, hidden=False, bone="Chassis",
            seat_size=(1.5, 0.2, 1.3), clips=True, **kw):
    """Rig: seat (rider hip) + enter sockets and mount length (K.ride), head / mouth / exhaust sockets, clips."""
    if enter is None:
        enter = (seat_pos[0] - 3.2 if seat_pos[0] <= 0 else seat_pos[0] + 3.2, 0, seat_pos[2] - 0.5)
    K.ride(H, seat_pos, enter, bone=bone, seat_part=seat, seat_size=seat_size, hidden=hidden)
    H.socket("head", (0, height + 0.3, 0), bone)
    H.socket("mouth", nose, "Chassis")
    H.socket("exhaust", tail, "Chassis")
    H.rig.update({"head": "Chassis"})
    if clips:
        K.vehicle_clips(H, wheels, susp="Chassis", height=height, length=length, sym=sym, steer=steer, attack=attack, **kw)


def _box_body(W, y0, y1, z0, z1, axles, wr, ag):
    """Box body side profile extruded across X with the wheel arches cut in (axles under the box)."""
    pts = [((z1, y0), 0.15), ((z1, y1), 0.25), ((z0, y1), 0.25), ((z0, y0), 0.15)]
    for z in sorted(axles):
        pts += K.car_arch(z, wr, wr + ag, y0)[::-1]
    return extrude(round_poly(np.array([p for p, _ in pts]), [r for _, r in pts], 2), W, bevel=0.2, seg=2)


def _axle_names(n):
    return ["F"] + (["M"] if n == 3 else ["M", "M2"] if n == 4 else []) + ["B"]


# ==================================================================================================== road trucks
TBASE = dict(
    # real game scale (studs) around a seated R15 rider (hip point (-seat_x, hip, hip_z), facing -Z)
    W=7.2, wr=1.45, ww=1.15, front=-8.0,   # front bumper face z
    axles=(-5.0, 4.8),                      # axle z positions (first steers)
    sill=1.5, floor=1.75, hip=2.95, hip_z=-0.6, seat_x=1.15,
    belt=4.25, hood_y=3.95, nose_y=3.5, ws=-3.7, fw=-3.0, roof0=-1.9, cab_back=1.3, roof_in=None,
    rear="bed", rear_len=6.5, rear_h=3.0, rear_y=None, gap=0.25,
    lamps="rect", grille="truck", rim="truck", rim_col="metal", knobby=0.0, stack=False, bull=False, lightbar=False,
    rear_col="primary", seat_col="darker", lift=0.0, preview={}, tags=("vehicle", "truck"), sym=8, track_x=None, wheel_seg=28,
    tilt=50, arch_gap=0.22, cab_col=None,
)


def _truck(hid, **kw):
    P = dict(TBASE)
    P.update(kw)
    H = _new(hid, P["preview"], P["tags"])
    u = 1.6  # detail scale vs the old (rider-agnostic) authoring
    W, wr, ww = P["W"], P["wr"], P["ww"]
    hw = W / 2
    lift = P["lift"]
    zn = P["front"]
    sill, floor, hip, belt = (P[k] + lift for k in ("sill", "floor", "hip", "belt"))
    hip_z, ws, fw, zc = P["hip_z"], P["ws"], P["fw"], P["cab_back"]
    roof_in = (P["roof_in"] + lift) if P["roof_in"] else hip + K.ROOF_CLEAR
    roofy = roof_in + 0.28
    bulk = zc - 0.4
    sx = P["seat_x"]
    t = 0.32
    axles = P["axles"]
    ag = P["arch_gap"]
    H.bone("Chassis", "Body", (0, wr + 0.3, (axles[0] + axles[-1]) / 2))
    # ------------------------------------------------------------------ wheels
    specs = []
    xw = P["track_x"] or (hw - ww / 2 - 0.05)
    for tag, z in zip(_axle_names(len(axles)), axles):
        specs.append(dict(name=f"Wheel{tag}R", pos=(xw, wr, z), r=wr, w=ww, side=1, steer=(tag == "F")))
        specs.append(dict(name=f"Wheel{tag}L", pos=(-xw, wr, z), r=wr, w=ww, side=-1, steer=(tag == "F")))
    wheels, steer = K.add_wheels(H, specs, rim=P["rim"], knobby=P["knobby"], rim_col=P["rim_col"], segs=P["wheel_seg"])

    # ------------------------------------------------------------------ cab: front section + floor pan + cab back, door walls
    zf = axles[0]
    cab_bot = sill
    front = [((zn + 0.45, cab_bot), 0.25), ((zn, cab_bot + 0.45), 0.2), ((zn - 0.02, P["nose_y"] + lift), 0.3),
             ((zn + 0.45, P["hood_y"] + lift), 0.45), ((ws, belt), 0.3), ((fw, belt), 0.0), ((fw, cab_bot), 0.0)]
    fra = wr + ag
    cutf = cab_bot < wr + fra - 0.1
    if cutf:
        front += K.car_arch(zf, wr, fra, cab_bot)
    fpoly = round_poly(np.array([p for p, _ in front]), [r for _, r in front], 3)
    back_poly = np.array([(bulk, cab_bot), (zc, cab_bot), (zc, belt), (bulk, belt)])
    pan = np.array([(fw - 0.02, cab_bot), (bulk + 0.02, cab_bot), (bulk + 0.02, floor), (fw - 0.02, floor)])

    def cabwarp(V):
        x, y, z = V[:, 0], V[:, 1], V[:, 2]
        s = 1 - 0.06 * np.clip((zn + 1.2 - z) / 1.2, 0, 1) ** 2
        sy = 1 - 0.03 * np.clip((y - (belt - 0.8)) / 0.8, 0, 1)
        cr = 0.08 * np.clip(1 - (x / hw) ** 2, 0, 1) * np.clip((y - (P["hood_y"] + lift - 0.35)) / 0.35, 0, 1) * (z < ws)
        return np.column_stack([x * s * sy, y + cr, z])

    cabm = warp(merge(extrude(fpoly, W, bevel=0.25, seg=3), extrude(round_poly(back_poly, [0, 0, 0.12, 0], 2), W, bevel=0.25, seg=2),
                      extrude(pan, W - 0.02, bevel=0.08, seg=1)), cabwarp)
    cab_col = P["cab_col"] or "primary"
    piece(H, "Chassis", "Chassis", cabm, col=cab_col, mat="metal", pri=0.5)
    K.door_walls(H, "Chassis", hw, t, fw, bulk, floor, belt, warp_fn=cabwarp, col=cab_col)
    if cutf:
        piece(H, "Liners", "Chassis", K.arch_liner(zf, wr, fra, hw - 0.4), col="black", mat="plastic", role="detail", pri=1.5)
    xg = (hw - t) * 0.97 + 0.04
    xt = K.greenhouse_real(H, "Chassis", ws, belt, P["roof0"], zc - 0.32, zc - 0.22, roof_in, xg, tum=0.05, crown=0.06, rear_pw=0.55,
                           roof_col=cab_col, roof_t=0.26)
    # ------------------------------------------------------------------ interior
    xi = hw - t
    inter = [box((2 * xi - 0.06, 0.12, bulk - fw - 0.06), (0, floor + 0.02, (fw + bulk) / 2), r=0.04, seg=0),
             box((2 * xt - 0.1, 0.07, zc - 0.4 - P["roof0"]), (0, roof_in - 0.015, (P["roof0"] + zc - 0.4) / 2), r=0.03, seg=0),
             box((0.6, hip - floor - 0.1, 1.2), (0, floor + (hip - floor - 0.1) / 2, hip_z - 0.2), r=0.06, seg=0)]
    piece(H, "Interior", "Chassis", merge(*inter), col="darker", mat="cloth", role="detail", pri=1.3)
    piece(H, "DoorCards", "Chassis", K.door_cards(hw, t, [(fw, bulk)], floor, belt, cabwarp), col="darker", mat="cloth", role="detail", pri=1.7)
    dash = K.dash_mesh(ws, fw, floor, belt, xi * 0.95 - 0.02)
    hoodb = K.instruments(H, "Chassis", -sx, belt + 0.12, fw + 0.55, w=1.0)
    swc = (-sx, hip + 1.45, hip_z - 1.45)
    sw = K.steering_mesh(swc, r=0.6, tilt=P["tilt"], col_len=0.0)
    piece(H, "Dash", "Chassis", merge(dash, hoodb, sw, rod(swc, (-sx, belt, fw + 0.5), 0.08, segs=8)), col="black", mat="plastic", role="detail", pri=1.2)
    piece(H, "Seat", "Chassis", K.bucket_seat((-sx, hip, hip_z), floor=floor), col=P["seat_col"], mat="cloth", role="seat", pri=1.0)
    piece(H, "Seat2", "Chassis", K.bucket_seat((sx, hip, hip_z), floor=floor), col=P["seat_col"], mat="cloth", role="seat", pri=1.6)

    # ------------------------------------------------------------------ front end
    ny = P["nose_y"] + lift
    chrome, dark = [], []
    gw = W * 0.5
    gh = (ny - cab_bot) * 0.6
    gy = cab_bot + 0.55 + gh / 2
    gm = [box((gw, gh, 0.18), (0, gy, zn - 0.03), r=0.1)]
    piece(H, "Grille", "Chassis", merge(*gm), col="black", mat="metal", role="detail", pri=1.4)
    chrome.append(box((gw + 0.2, gh + 0.2, 0.08), (0, gy, zn + 0.03), r=0.1))
    for k in range(5):
        chrome.append(cbox((gw * 0.94, 0.08, 0.08), (0, gy - gh * 0.4 + gh * 0.2 * k, zn - 0.13), c=0.02))
    if P["lamps"] == "round":
        K.lamp_pair(H, "Headlight", "Chassis", (hw - 0.85, gy + 0.08, zn - 0.12), r=0.42, depth=0.24)
        chrome += [K.bezel((s * (hw - 0.85), gy + 0.08, zn - 0.08), 0.42, 0.18) for s in (-1, 1)]
    else:
        K.lamp_pair(H, "Headlight", "Chassis", (hw - 0.85, gy + 0.08, zn - 0.08), shape="rect", w=1.1, h=0.5, depth=0.3)
    by = cab_bot + 0.2
    bump = box((W + 0.15, 0.6, 0.6), (0, by, zn - 0.22), r=0.15, seg=1)
    piece(H, "Bumper", "Chassis", bump, col="metal" if P["grille"] == "truck" else "black", mat="metal", role="detail", pri=1.2)
    if P["bull"]:
        bb = [rod((s * 1.3, by, zn - 0.6), (s * 1.3, ny + 0.3, zn - 0.7), 0.13, segs=10) for s in (-1, 1)]
        bb.append(rod((-1.3, ny + 0.3, zn - 0.7), (1.3, ny + 0.3, zn - 0.7), 0.13, ext=0.13, segs=10))
        bb.append(rod((-1.35, (by + ny) / 2, zn - 0.66), (1.35, (by + ny) / 2, zn - 0.66), 0.11, segs=10))
        piece(H, "PushBar", "Chassis", merge(*bb), col="black", mat="metal", role="detail", pri=1.6)
    # mirrors on arms
    mx = hw * 0.97
    mir = merge(rod((mx - 0.05, belt + 0.3, fw + 0.4), (mx + 0.7, belt + 0.7, fw + 0.3), 0.06, segs=6),
                box((0.28, 1.2, 0.55), (mx + 0.8, belt + 0.9, fw + 0.3), r=0.1))
    mpiece(H, "Mirror#", "Chassis", mir, col="black", mat="metal", role="detail", pri=1.8)
    # door handles, cab step
    for s in (-1, 1):
        chrome.append(cbox((0.09, 0.14, 0.6), (s * (hw * 0.97 + 0.05), belt - 0.5, bulk - 0.6), c=0.04))
        dark.append(box((0.6, 0.14, 1.2), (s * (hw - 0.15), cab_bot - 0.45, (fw + bulk) / 2), r=0.04, seg=0))
        dark.append(box((0.12, 0.6, 0.12), (s * (hw - 0.2), cab_bot - 0.2, (fw + bulk) / 2), r=0.03, seg=0))
    # frame rails under everything
    zt = zc + P["gap"] + P["rear_len"]
    fy = sill - 0.05
    for s in (-1, 1):
        dark.append(box((0.35, 0.6, zt - zn - 1.0), (s * 1.25, fy - 0.3, (zn + 0.6 + zt) / 2), r=0.05, seg=0))
    if P["stack"]:
        for s in (-1, 1):
            chrome.append(K.tube_ring(0.24, 0.17, 3.6, axis="y", pos=(s * (hw - 0.5), roofy - 0.6, zc + 0.3)))
            dark.append(cyl(1.2, 0.3, (s * (hw - 0.5), belt - 0.3, zc + 0.3), "y", segs=12))
    if P["rear"] in ("box", "garbage", "ladder", "tanker", "mixer", "dump", "trailer", "ambulance", "icecream", "food"):
        chrome.append(cyl(2.0, 0.6, (hw - 0.75, sill - 0.3, zc + 1.6), "z", segs=18))
    if P["lightbar"]:
        zl = P["roof0"] + 0.7
        lb = box((3.4, 0.2, 0.7), (0, roofy + 0.1, zl), r=0.05)
        lr = box((1.45, 0.38, 0.55), (0.82, roofy + 0.38, zl), r=0.12, seg=2)
        piece(H, "LightBar", "Chassis", lb, col="black", mat="plastic", role="detail", pri=1.3)
        piece(H, "SirenRed", "Chassis", lr, col=RED_L, mat="glass", role="light", pri=1.4, ao=False)
        piece(H, "SirenBlue", "Chassis", mirror(lr), col=BLUE_L if P["lightbar"] != "red" else RED_L, mat="glass", role="light", pri=1.4, ao=False)
    mk = merge(*(cbox((0.3, 0.16, 0.2), (x, roofy + 0.08, P["roof0"] + 0.2), c=0.05) for x in (-1.0, -0.5, 0, 0.5, 1.0)))
    piece(H, "Markers", "Chassis", mk, col=AMBER, mat="glass", role="light", pri=2.4, ao=False)

    # ------------------------------------------------------------------ rear body
    ry = P["rear_y"] + lift if P["rear_y"] is not None else fy + 0.05
    z0, z1 = zc + P["gap"], zt
    rt = P["rear"]
    attack_extra = None
    spinners = ()
    rc = P["rear_col"]
    rear_axles = axles[1:]
    bh = P["rear_h"]
    top = ry + bh
    TL = (hw - 0.3, ry + 0.7, z1 + 0.02)
    box_cut = rt in ("box", "garbage", "trailer", "ladder", "icecream", "food", "ambulance") and ry < 2 * wr + ag - 0.1
    if box_cut:
        piece(H, "RearLiners", "Chassis", merge(*(K.arch_liner(z, wr, wr + ag, hw - 0.3) for z in rear_axles)), col="black", mat="plastic", role="detail", pri=1.6)
    elif rt != "bed":
        fenders = []
        for z in rear_axles:
            rr = wr + 0.3
            ar = [(z + rr * math.cos(math.radians(a)), wr + rr * math.sin(math.radians(a))) for a in np.linspace(5, 175, 12)]
            ar += [(z + (rr - 0.18) * math.cos(math.radians(a)), wr + (rr - 0.18) * math.sin(math.radians(a))) for a in np.linspace(175, 5, 12)]
            for s in (-1, 1):
                fenders.append(xf(extrude(np.array(ar), ww + 0.3, bevel=0.06, seg=1), (s * xw, 0, 0)))
        if ry < 2 * wr + 0.3:
            piece(H, "Fenders", "Chassis", merge(*fenders), col="black", mat="plastic", role="detail", pri=1.6)
    if rt == "bed":
        bf = floor + 0.5
        zr = rear_axles[0]
        bra = wr + ag
        cutb = bf - 0.5 < wr + bra - 0.1
        poly = [(z0, belt), (z0, bf - 0.5)] + ([p for p, _ in K.car_arch(zr, wr, bra, bf - 0.5)][::-1] if cutb else []) + [(z1, bf - 0.5), (z1, belt)]
        poly = round_poly(np.array(poly), [0.12, 0.08] + [0.0] * (len(poly) - 4) + [0.08, 0.12], 2)
        sides = [xf(extrude(poly, 0.35, bevel=0.1, seg=2), (s * (hw - 0.175), 0, 0)) for s in (-1, 1)]
        xfl = xw - ww / 2 - 0.12
        floor_ = box((2 * xfl, 0.2, z1 - z0 - 0.4), (0, bf, (z0 + z1) / 2), r=0.05, seg=0)
        tubs = [] if not (cutb and 2 * wr + 0.3 > bf + 0.2) else [box((hw - 0.35 - xfl + 0.1, 2 * wr + 0.3 - bf + 0.1, 2 * bra + 0.3), (s * (xfl + (hw - 0.35 - xfl) / 2), (bf + 2 * wr + 0.3) / 2, zr), r=0.15, seg=1)
                for s in (-1, 1)]
        frontw = box((W - 0.2, belt - bf + 0.3, 0.32), (0, (belt + bf - 0.3) / 2, z0 + 0.16), r=0.08, seg=1)
        tg = box((W - 0.2, belt - bf + 0.3, 0.28), (0, (belt + bf - 0.3) / 2, z1 - 0.14), r=0.08, seg=1)
        piece(H, "Bed", "Chassis", merge(*sides, floor_, frontw, tg), col=rc, mat="metal", role="body", pri=0.7)
        piece(H, "BedLiner", "Chassis", merge(*tubs, box((2 * xfl - 0.2, 0.06, z1 - z0 - 0.8), (0, bf + 0.12, (z0 + z1) / 2), r=0.02, seg=0)),
              col="black", mat="plastic", role="detail", pri=1.3)
        piece(H, "BedRail", "Chassis", merge(*(bar((s * (hw - 0.175), belt + 0.05, z0), (s * (hw - 0.175), belt + 0.05, z1), 0.4, 0.1, r=0.03) for s in (-1, 1))),
              col="black", mat="plastic", role="detail", pri=2.0)
        TL = (hw - 0.3, belt - 0.7, z1 + 0.02)
        rb = box((W - 0.2, 0.5, 0.5), (0, bf - 0.5, z1 + 0.2), r=0.12)
        hitch = merge(rb, cbox((0.35, 0.35, 0.6), (0, bf - 0.65, z1 + 0.6), c=0.06), cyl(0.3, 0.2, (0, bf - 0.35, z1 + 0.8), "y", segs=12))
        piece(H, "RearBumper", "Chassis", hitch, col="metal", mat="metal", role="detail", pri=1.5)
    elif rt in ("box", "garbage", "trailer", "ladder", "icecream", "food", "ambulance"):
        if rt != "ladder":
            bx = _box_body(W + 0.1, ry, top, z0, z1, rear_axles, wr, ag) if box_cut else box((W + 0.1, bh, z1 - z0), (0, ry + bh / 2, (z0 + z1) / 2), r=0.2, seg=1)
            if rt == "garbage":
                hop = extrude(round_poly(np.array([(z1 - 0.3, ry), (z1 - 0.3, top), (z1 + 1.0, top - 0.3), (z1 + 1.8, ry + 1.0), (z1 + 1.0, ry)]), 0.25, 2), W, bevel=0.15)
                bx = merge(bx, hop)
                bx = merge(bx, *[xf(cbox((0.2, bh, 0.32), (0, 0, 0), c=0.05), (s * (hw + 0.1), ry + bh / 2, z)) for s in (-1, 1) for z in np.linspace(z0 + 1.0, z1 - 1.0, 4)])
            piece(H, "Box", "Chassis", bx, col=rc, mat="metal", role="body", pri=0.6)
            # box trim: top rail, bottom rub rail, rear door frame + hinges
            tr_ = [cbox((W + 0.25, 0.2, z1 - z0 + 0.1), (0, top - 0.05, (z0 + z1) / 2), c=0.05), cbox((W + 0.25, 0.25, z1 - z0 + 0.1), (0, ry + 0.12, (z0 + z1) / 2), c=0.05)]
            if rt != "garbage":
                tr_ += [cbox((0.08, bh * 0.92, 0.12), (0, ry + bh / 2, z1 + 0.04), c=0.02)]
                tr_ += [cbox((0.18, 0.4, 0.12), (s * (hw - 0.2), ry + bh * f, z1 + 0.06), c=0.03) for s in (-1, 1) for f in (0.25, 0.75)]
                tr_ += [cbox((0.12, 0.7, 0.14), (s * 0.3, ry + bh * 0.48, z1 + 0.07), c=0.03) for s in (-1, 1)]
            piece(H, "BoxTrim", "Chassis", merge(*tr_), col="metal", mat="metal", role="detail", pri=1.6)
            TL = (hw - 0.3, ry + 0.8, z1 + (1.8 if rt == "garbage" else 0.02))
        if rt in ("box", "ambulance", "icecream", "food", "trailer"):
            rb = box((W - 0.3, 0.5, 0.5), (0, ry - 0.1, z1 + 0.2), r=0.12)
            piece(H, "RearBumper", "Chassis", merge(rb, box((W - 1.0, 0.12, 0.6), (0, ry - 0.3, z1 + 0.5), r=0.03, seg=0)), col="black", mat="metal", role="detail", pri=1.5)
        if rt == "ladder":
            # equipment body with roller-shutter lockers, hose reel, turntable + ladder on its own bone
            bx = _box_body(W + 0.1, ry, top, z0, z1, rear_axles, wr, ag) if box_cut else box((W + 0.1, bh, z1 - z0), (0, ry + bh / 2, (z0 + z1) / 2), r=0.15, seg=1)
            piece(H, "Box", "Chassis", bx, col=rc, mat="metal", role="body", pri=0.6)
            H.bone("Ladder", "Chassis", (0, top + 0.55, z1 - 0.8))
            lad = []
            ll = z1 - z0 + 4.0
            for s in (-1, 1):
                lad.append(bar((s * 0.9, top + 0.75, z1 - 0.4), (s * 0.9, top + 0.75, z1 - 0.4 - ll), 0.16, 0.36, r=0.05))
                lad.append(bar((s * 0.68, top + 1.15, z1 - 0.8), (s * 0.68, top + 1.15, z1 - 0.8 - ll * 0.85), 0.13, 0.3, r=0.04))
            for k in range(18):
                z = z1 - 0.7 - k * (ll - 0.5) / 18
                lad.append(rod((-0.9, top + 0.75, z), (0.9, top + 0.75, z), 0.06, segs=5))
            turn = merge(cyl(0.55, 1.05, (0, top + 0.28, z1 - 0.8), "y", segs=20), box((1.4, 0.7, 1.2), (0, top + 0.7, z1 - 0.8), r=0.1))
            piece(H, "LadderP", "Ladder", merge(*lad), col="metal", mat="metal", role="detail", pri=1.0)
            piece(H, "Turntable", "Chassis", turn, col="darker", mat="metal", role="detail", pri=1.2)
            lk = []
            nl = 4
            for s in (-1, 1):
                for k in range(nl):
                    seg_ = (z1 - z0 - 1.0) / nl
                    zz = z0 + 0.5 + seg_ * (k + 0.5)
                    lk.append(cbox((0.08, bh * 0.72, seg_ - 0.25), (s * (hw + 0.09), ry + bh * 0.5, zz), c=0.03))
                    lk.append(cbox((0.14, 0.12, seg_ * 0.4), (s * (hw + 0.14), ry + bh * 0.3, zz), c=0.03))
            piece(H, "Lockers", "Chassis", merge(*lk), col="metal", mat="metal", role="detail", pri=1.4)
            reel = merge(cyl(1.1, 0.7, (0, top - 0.3, z0 + 0.6), "x", segs=16), K.torus(0.66, 0.13, "x", 16, 5, pos=(0.0, top - 0.3, z0 + 0.6)))
            piece(H, "HoseReel", "Chassis", reel, col="secondary", mat="cloth", role="detail", pri=1.6)
            rb = box((W - 0.3, 0.5, 0.5), (0, ry - 0.1, z1 + 0.2), r=0.12)
            piece(H, "RearBumper", "Chassis", rb, col="metal", mat="metal", role="detail", pri=1.5)
            TL = (hw - 0.3, ry + 0.8, z1 + 0.02)

            def attack_extra(pose, s):
                up = K._bump(s, 0.05, 0.98)
                K.add(pose, "Ladder", (0, 0, 0, 0.55 * up, 0.25 * up, 0))
        if rt == "garbage":
            H.bone("ArmL", "Chassis", (hw + 0.3, top - 0.5, z1 - 0.3))
            arm = merge(bar((hw + 0.3, top - 0.5, z1 - 0.3), (hw + 0.4, ry + 0.5, z1 + 0.5), 0.3, 0.3), cbox((1.0, 0.8, 0.25), (hw + 0.4, ry + 0.3, z1 + 0.6), c=0.06))
            piece(H, "Arm", "ArmL", arm, col="darker", mat="metal", role="detail", pri=1.3)

            def attack_extra(pose, s):
                up = K._bump(s, 0.05, 0.95)
                K.add(pose, "ArmL", (0, 0, 0, -1.1 * up, 0, 0))
        if rt == "ambulance":
            st = []
            for s in (-1, 1):
                st.append(cbox((0.06, 0.5, z1 - z0 - 0.5), (s * (hw + 0.09), ry + bh * 0.42, (z0 + z1) / 2), c=0.02))
                st.append(cbox((0.06, 1.3, 0.42), (s * (hw + 0.1), ry + bh * 0.72, (z0 + z1) / 2 + 0.6), c=0.02))
                st.append(cbox((0.06, 0.42, 1.3), (s * (hw + 0.1), ry + bh * 0.72, (z0 + z1) / 2 + 0.6), c=0.02))
            st.append(cbox((1.3, 0.42, 0.06), (0, ry + bh * 0.72, z1 + 0.1), c=0.02))
            st.append(cbox((0.42, 1.3, 0.06), (0, ry + bh * 0.72, z1 + 0.1), c=0.02))
            piece(H, "Stripes", "Chassis", merge(*st), col="secondary", mat="plastic", role="detail", pri=1.4)
            lr = merge(*(box((0.5, 0.4, 0.5), (s * (hw - 0.35), top + 0.18, z), r=0.12) for s in (-1, 1) for z in (z0 + 0.35, z1 - 0.35)))
            piece(H, "BeaconRed", "Chassis", lr, col=RED_L, mat="glass", role="light", pri=1.5, ao=False)
            win = merge(*(cbox((0.08, 1.0, 1.2), (s * (hw + 0.06), ry + bh * 0.72, z0 + 1.2), c=0.03) for s in (-1, 1)))
            piece(H, "BoxWindows", "Chassis", win, col="glass", mat="glass", role="window", pri=1.6, tr=0.3)
        if rt in ("icecream", "food"):
            wz0, wz1 = z0 + 0.8, z1 - 1.2
            win = cbox((0.08, bh * 0.4, wz1 - wz0), (hw + 0.08, ry + bh * 0.62, (wz0 + wz1) / 2), c=0.03)
            frame_ = merge(cbox((0.16, 0.16, wz1 - wz0 + 0.3), (hw + 0.14, ry + bh * 0.4, (wz0 + wz1) / 2), c=0.04),
                           cbox((0.18, 0.18, wz1 - wz0 + 0.4), (hw + 0.14, ry + bh * 0.84, (wz0 + wz1) / 2), c=0.04))
            counter = box((0.8, 0.16, wz1 - wz0), (hw + 0.45, ry + bh * 0.4, (wz0 + wz1) / 2), r=0.04)
            piece(H, "ServeWindow", "Chassis", win, col="darker", mat="glass", role="window", pri=1.3)
            piece(H, "Counter", "Chassis", merge(frame_, counter), col="metal", mat="metal", role="detail", pri=1.4)
            aw = []
            n = 8
            for k in range(n):
                zz = wz0 + (wz1 - wz0) * (k + 0.5) / n
                aw.append(cbox((1.6, 0.08, (wz1 - wz0) / n), (hw + 0.8, ry + bh * 0.95 - 0.1, zz), c=0.02, rot_=(0, 0, -18)))
            piece(H, "Awning", "Chassis", merge(*aw[0::2]), col="secondary", mat="cloth", role="detail", pri=1.5)
            piece(H, "Awning2", "Chassis", merge(*aw[1::2]), col="white", mat="cloth", role="detail", pri=1.6)
            if rt == "icecream":
                cz = (z0 + z1) / 2
                cone = xf(K.lathe_profile([(top + 0.1, 0.08), (top + 1.9, 0.68), (top + 2.0, 0)], 18, "y"), (0, 0, cz))
                scoop = K.D.revolve([(top + 1.7, 0), (top + 1.85, 0.8), (top + 2.3, 0.93), (top + 2.85, 0.65), (top + 3.1, 0)], segs=18, axis=1, spline=3)
                scoop = warp(scoop, lambda V: np.column_stack([V[:, 0], V[:, 1] + 0.08 * np.sin(np.arctan2(V[:, 2], V[:, 0]) * 7) * (V[:, 1] < top + 2.1), V[:, 2] + cz]))
                piece(H, "Cone", "Chassis", cone, col=[0.85, 0.62, 0.35], mat="plastic", role="detail", pri=1.2)
                piece(H, "Scoop", "Chassis", scoop, col=[1.0, 0.72, 0.8], mat="plastic", role="detail", pri=1.2)
            else:
                sign = box((0.25, 1.0, (wz1 - wz0) * 0.8), (hw - 0.5, top + 0.6, (wz0 + wz1) / 2), r=0.08)
                piece(H, "Sign", "Chassis", sign, col="secondary", mat="plastic", role="detail", pri=1.4)
    elif rt == "tanker":
        R = 1.8
        tk = K.lathe_profile([(z0 + 0.15, 0), (z0 + 0.15, R * 0.78), (z0 + 0.7, R), (z1 - 0.55, R), (z1, R * 0.78), (z1, 0)], 28, "z")
        tk = xf(warp(tk, lambda V: np.column_stack([V[:, 0] * 1.65, V[:, 1], V[:, 2]])), (0, ry + R + 0.15, 0))
        hoops = merge(*(K.torus(R + 0.03, 0.08, "z", 28, 4, pos=(0, 0, z)) for z in np.linspace(z0 + 1.3, z1 - 1.3, 4)))
        hoops = xf(warp(hoops, lambda V: np.column_stack([V[:, 0] * 1.65, V[:, 1], V[:, 2]])), (0, ry + R + 0.15, 0))
        walk = merge(box((1.3, 0.12, z1 - z0 - 1.6), (0, ry + 2 * R + 0.2, (z0 + z1) / 2), r=0.04, seg=0),
                     *[cyl(0.3, 0.5, (0, ry + 2 * R + 0.25, z), "y", segs=12) for z in np.linspace(z0 + 2, z1 - 2, 3)])
        piece(H, "Box", "Chassis", tk, col=rc, mat="metal", role="body", pri=0.6)
        piece(H, "Hoops", "Chassis", merge(hoops, walk), col="metal", mat="metal", role="detail", pri=1.4)
        top = ry + 2 * R + 0.3
        TL = (hw - 0.3, ry + 0.4, z1 + 0.02)
    elif rt == "dump":
        hz = z1 - 0.3
        H.bone("Bed", "Chassis", (0, ry + 0.3, hz))
        dp = round_poly(np.array([(z0, ry + 0.4), (z0 - 0.3, top + 0.6), (z1 + 0.15, top), (z1, ry + 0.4)]), [0.15] * 4, 2)
        outer = warp(extrude(dp, W + 0.1, bevel=0.15, seg=2), lambda V: np.column_stack([V[:, 0] * (1 + 0.05 * (V[:, 1] - ry) / bh), V[:, 1], V[:, 2]]))
        cano = box((W - 0.3, 0.22, 2.0), (0, top + 0.55, z0 - 1.1), r=0.06)
        ribs = merge(*[xf(cbox((0.2, bh * 0.9, 0.3), (0, 0, 0), c=0.05), (s * (hw + 0.14), ry + bh / 2 + 0.3, z)) for s in (-1, 1) for z in np.linspace(z0 + 0.6, z1 - 0.6, 4)])
        piece(H, "Box", "Bed", merge(outer, cano), col=rc, mat="metal", role="body", pri=0.6)
        piece(H, "BedRibs", "Bed", ribs, col="darker", mat="metal", role="detail", pri=1.6)
        fill = box((W - 0.4, 0.4, z1 - z0 - 0.6), (0, top + 0.2, (z0 + z1) / 2), r=0.18, seg=2)
        fill = warp(fill, lambda V: np.column_stack([V[:, 0], V[:, 1] + 0.4 * np.cos(V[:, 2] * 1.1) * np.cos(V[:, 0] * 0.8) * (V[:, 1] > top + 0.15), V[:, 2]]))
        piece(H, "Load", "Bed", fill, col=[0.55, 0.42, 0.3], mat="stone", role="detail", pri=1.8)
        TL = (hw - 0.3, ry + 0.4, z1 + 0.02)

        def attack_extra(pose, s):
            tip = K._bump(s, 0.1, 0.95)
            K.add(pose, "Bed", (0, 0, 0, 0.75 * tip, 0, 0))
    elif rt == "mixer":
        H.bone("Drum", "Chassis", (0, ry + 2.3, (z0 + z1) / 2))
        dl = z1 - z0
        prof = [(-dl / 2, 0), (-dl / 2, 0.8), (-dl / 2 + 0.5, 1.6), (-dl * 0.1, 2.1), (dl * 0.15, 2.1), (dl / 2 - 0.3, 1.2), (dl / 2, 0.65), (dl / 2 + 0.08, 0)]
        drum = K.lathe_profile(prof, 28, "z")
        spiral = []
        for k in range(36):
            tt = k / 36
            zz = -dl / 2 + 0.6 + (dl - 1.4) * tt
            rr = float(np.interp(zz, [p[0] for p in prof], [p[1] for p in prof])) + 0.03
            an = tt * TAU * 2.0
            spiral.append(cbox((0.3, 0.1, 0.65), (rr * math.cos(an), rr * math.sin(an), zz), c=0.03, rot_=(0, 0, math.degrees(an) + 90)))
        dr = xf(drum, (0, 0, 0), r=(-10, 0, 0))
        sp = xf(merge(*spiral), (0, 0, 0), r=(-10, 0, 0))
        piece(H, "Box", "Drum", xf(dr, (0, ry + 2.3, (z0 + z1) / 2)), col=rc, mat="metal", role="body", pri=0.6)
        piece(H, "DrumStripes", "Drum", xf(sp, (0, ry + 2.3, (z0 + z1) / 2)), col="secondary", mat="metal", role="detail", pri=1.3)
        cradle = merge(box((1.9, 1.0, 0.5), (0, ry + 0.5, z0 + 0.5), r=0.08), box((1.9, 1.5, 0.5), (0, ry + 0.75, z1 - 0.6), r=0.08),
                       box((1.4, 0.4, 1.0), (0, ry + 3.8, z1 + 0.2), r=0.08, rot_=(-35, 0, 0)), box((1.4, 0.2, 2.2), (0, ry + 1.8, z1 + 1.0), r=0.06, rot_=(40, 0, 0)))
        piece(H, "Cradle", "Chassis", cradle, col="darker", mat="metal", role="detail", pri=1.4)
        spinners = (("Drum", "z", 1),)
        top = ry + 4.4
        TL = (hw - 0.3, ry + 0.4, z1 + 0.02)
    TLm = K.lamp(TL, 0, 0.16, axis="+z", shape="rect", w=0.4, h=0.75)
    mpiece(H, "Taillight#", "Chassis", TLm, col=RED_L, mat="glass", role="light", pri=1.7, ao=False)
    piece(H, "Trim", "Chassis", merge(*dark), col="black", mat="plastic", role="detail", pri=1.3)
    piece(H, "Chrome", "Chassis", merge(*chrome), col="metal", mat="metal", role="detail", pri=1.9)
    height = max(roofy, top)
    _finish(H, wheels, steer, height, zt - zn, (-sx, hip, hip_z), (0, ny, zn - 0.6), (hw - 0.5, roofy + 1.2, zc + 0.3),
            sym=P["sym"], spinners=spinners, extra_attack=attack_extra, enter=(-(hw + 1.6), 0, hip_z - 0.6))
    return H


TAU = 2 * math.pi


@hero("pickup truck", FAM)
def pickup_truck():
    return _truck("pickup truck", rim="alloy", rim_col="metal", sym=5, knobby=0.03, preview=pv("#9B2226", "#2E2E2E"))


@hero("monster truck", FAM)
def monster_truck():
    # pickup body lifted on huge knobby tyres: the cab floor sits above the tyre tops, rider climbs up a ladder
    H = _truck("monster truck", W=7.6, wr=3.1, ww=2.5, front=-8.4, axles=(-5.1, 5.1), track_x=4.6, lift=4.9, sill=1.5, floor=1.75, hip=2.95,
               belt=4.25, hood_y=3.95, nose_y=3.5, rear="bed", rear_len=6.6, rim="steel", rim_col="secondary", knobby=0.32, bull=True, sym=8,
               wheel_seg=32, preview=pv("#39B54A", "#FF6B00"), tags=("vehicle", "truck", "monster"))
    # chassis tube frame, axles, long-travel shocks, ladder under the driver's door
    sh = []
    for z in (-5.1, 5.1):
        sh.append(rod((-4.0, 3.1, z), (4.0, 3.1, z), 0.3, segs=12))
        sh.append(cyl(1.4, 0.75, (0, 3.1, z), "x", segs=16))
        for s in (-1, 1):
            sh.append(rod((s * 2.6, 3.2, z), (s * 1.6, 6.2, z + 0.7 * (1 if z > 0 else -1)), 0.24, segs=10))
            sh.append(rod((s * 2.0, 3.2, z + 0.5 * (1 if z > 0 else -1)), (s * 1.1, 6.0, z + 1.3 * (1 if z > 0 else -1)), 0.2, segs=10))
    for s in (-1, 1):
        sh.append(rod((s * 1.2, 5.6, -7.0), (s * 1.2, 5.6, 7.0), 0.22, segs=10))
    piece(H, "Shocks", "Body", merge(*sh), col="secondary", mat="metal", role="detail", pri=1.3)
    lad = [rod((-3.7, 0.4, z), (-3.75, 6.0, z), 0.1, segs=8) for z in (-2.2, -1.2)]
    lad += [rod((-3.72, y, -2.2), (-3.72, y, -1.2), 0.08, segs=6) for y in np.arange(1.0, 6.0, 0.8)]
    piece(H, "Ladder", "Chassis", merge(*lad), col="black", mat="metal", role="detail", pri=1.6)
    H.socket("enter", (-5.2, 0.0, -1.7), "Body")
    return H


@hero("van", FAM)
def van():
    # cab-forward panel van: short hood, the cargo box runs at roof height straight behind the cab
    return _truck("van", W=7.0, wr=1.3, ww=1.0, front=-8.5, axles=(-6.6, 4.9), sill=1.3, floor=1.55, hip=2.75, hip_z=-3.05, belt=4.0,
                  hood_y=3.6, nose_y=3.0, ws=-5.85, fw=-5.0, roof0=-4.35, cab_back=-1.6, gap=0.0, rear="box", rear_len=10.1,
                  rear_h=5.35, rear_y=1.15, grille="van", rim="steel", rim_col="white", preview=pv("#F2F2F2", "#4A4A4A"))


def _boxtruck(hid, rear, preview, L=19.0, rear_h=5.6, **kw):
    a = dict(W=7.4, wr=1.45, ww=1.1, front=-L / 2, axles=(-L / 2 + 2.9, L / 2 - 4.0), hip_z=-L / 2 + 4.6, ws=-L / 2 + 2.3, fw=-L / 2 + 2.95,
             roof0=-L / 2 + 3.5, cab_back=-L / 2 + 6.0, rear=rear, rear_len=L - 6.25, rear_h=rear_h, rear_y=1.5, hood_y=3.85, nose_y=3.4,
             grille="van", rim="steel")
    a.update(kw)
    return _truck(hid, preview=preview, **a)


@hero("ambulance", FAM)
def ambulance():
    return _boxtruck("ambulance", "ambulance", pv("#F5F5F5", "#D7263D"), lightbar="red")


@hero("ice cream truck", FAM)
def ice_cream_truck():
    return _boxtruck("ice cream truck", "icecream", pv("#F7A8C8", "#5BC0EB"), lamps="round", rim_col="white", rear_col="white", rear_h=5.0)


@hero("food truck", FAM)
def food_truck():
    return _boxtruck("food truck", "food", pv("#F2C24A", "#D72B2B"), L=20.0)


@hero("delivery truck", FAM)
def delivery_truck():
    return _boxtruck("delivery truck", "box", pv("#6B4F2A", "#EFE6D2"), L=20.0, rear_h=6.0, rear_col="secondary")


def _bigtruck(hid, rear, preview, L=24.0, cabover=True, axles=None, **kw):
    """Heavy truck: tall cab (rider climbs to hip ~4.4), cab-over or long-hood."""
    zn = -L / 2
    hood = 0.6 if cabover else 3.4
    a = dict(W=8.0, wr=1.75, ww=1.25, front=zn, axles=axles or (zn + 3.0, L / 2 - 5.0, L / 2 - 2.6), sill=3.0, floor=3.25, hip=4.45,
             hip_z=zn + hood + 2.9, belt=5.8, hood_y=5.3 if cabover else 5.0, nose_y=4.6 if cabover else 4.6, ws=zn + hood + 0.45,
             fw=zn + hood + 1.25, roof0=zn + hood + 1.6, cab_back=zn + hood + 4.4, rear=rear, rear_y=2.4, rim="truck", tilt=38, arch_gap=0.25)
    a["rear_len"] = L / 2 - a["cab_back"] - 0.3
    a.update(kw)
    return _truck(hid, preview=preview, **a)


@hero("fire truck", FAM)
def fire_truck():
    return _bigtruck("fire truck", "ladder", pv("#D22B2B", "#F2F2F2"), L=26.0, rear_h=3.4, lightbar="red")


@hero("garbage truck", FAM)
def garbage_truck():
    return _bigtruck("garbage truck", "garbage", pv("#2E8B57", "#E8E8E8"), L=23.0, rear_h=5.2, gap=0.35)


@hero("cement mixer", FAM)
def cement_mixer():
    return _bigtruck("cement mixer", "mixer", pv("#F2F2F2", "#E86A17"), L=24.0, cabover=False, stack=True, gap=0.5)


@hero("dump truck", FAM)
def dump_truck():
    return _bigtruck("dump truck", "dump", pv("#F2B705", "#3A3A3A"), L=22.0, cabover=False, stack=True, knobby=0.06, rear_h=2.6, gap=0.6)


@hero("truck", FAM)
def semi_truck():
    """Long-hood heavy lorry with a tall box body, twin stacks and a sleeper roof."""
    return _bigtruck("truck", "box", pv("#2F5D8A", "#C9CED6"), L=22.0, cabover=False, stack=True, rear_h=6.6, rear_col="secondary", gap=0.4)


@hero("tanker truck", FAM)
def tanker_truck():
    return _bigtruck("tanker truck", "tanker", pv("#D9D9D9", "#C8102E"), L=26.0, cabover=False, stack=True, rear_col="metal", gap=0.5,
                     axles=(-9.6, 3.6, 6.0, 9.2))


# ==================================================================================================== buses
def _bus(hid, L=32.0, W=8.2, wr=1.6, school=False, decker=False, preview=None):
    """Bus at real scale, hollow: floor pan, side walls with the wheel arches cut in, a long glass band between
    window pillars, roof, big windshield, folding door on the right, a driver's seat + dash + big flat wheel and rows
    of passenger seats inside."""
    H = _new(hid, preview, ("vehicle", "bus"))
    hw = W / 2
    zn, zt = -L / 2, L / 2
    hood = 4.0 if school else 0.0
    zb = zn + hood                    # front wall of the passenger body
    sill, floor = 1.05, 1.85
    t = 0.3
    hip = floor + 1.25 + 0.4          # driver on a platform
    belt = floor + 2.35
    win_top = floor + 5.2
    roof_in = max(win_top + 0.2, hip + K.ROOF_CLEAR)
    deck_h = 4.4 if decker else 0.0
    top = roof_in + deck_h + 0.35
    H.bone("Chassis", "Body", (0, wr + 0.3, 0))
    axles = (zb + 3.4 if school else zn + 4.6, zt - 6.5)
    specs = []
    for tag, z in zip(("F", "B"), axles):
        for side, x in ((1, hw - 0.85), (-1, -hw + 0.85)):
            specs.append(dict(name=f"Wheel{tag}{'R' if side > 0 else 'L'}", pos=(x, wr, z), r=wr, w=1.2, side=side, steer=(tag == "F")))
    wheels, steer = K.add_wheels(H, specs, rim="truck", segs=28)
    ra = wr + 0.25

    # side walls with arches (right + mirrored), front + rear walls, floor pan, roof
    def wall_poly(y0, y1):
        out = [(zt, y0), (zt, y1), (zb, y1), (zb, y0)]
        for z in sorted(axles):
            out += [p for p, _ in K.car_arch(z, wr, ra, y0)][::-1]
        return np.array(out)

    lower = wall_poly(sill, belt)
    wl = extrude(round_poly(lower, [0.25, 0.1, 0.1, 0.25] + [0.0] * (len(lower) - 4), 2), t, bevel=0.1, seg=2)
    wl = xf(wl, (hw - t / 2, 0, 0))
    upper = np.array([(zb + 0.3, win_top), (zt - 0.3, win_top), (zt - 0.3, roof_in + 0.02), (zb + 0.3, roof_in + 0.02)])
    walls = [wl, mirror(wl)]
    for s in (-1, 1):
        walls.append(xf(extrude(upper, t, bevel=0.08, seg=1), (s * (hw - t / 2), 0, 0)))
    pan = box((2 * (hw - 1.55), floor - sill + 0.05, zt - zb - 0.3), (0, (floor + sill) / 2, (zb + zt) / 2), r=0.1, seg=0)
    fwall = box((W, belt - 0.4 - sill, 0.4), (0, (belt - 0.4 + sill) / 2, zb + 0.2), r=0.2, seg=1)
    rwall = box((W, top - 0.2 - sill, 0.4), (0, (top - 0.2 + sill) / 2, zt - 0.2), r=0.25, seg=1)
    roofp = round_poly(np.array([(zb + 0.0, roof_in), (zb + 0.0, top - 0.1), (zb + 0.6, top), (zt - 0.4, top), (zt, top - 0.4), (zt, roof_in)]), [0, 0.1, 0.5, 0.4, 0.1, 0], 3)
    roof = warp(extrude(roofp, W, bevel=0.3, seg=2), lambda V: np.column_stack([V[:, 0] * (1 - 0.04 * np.clip((V[:, 1] - (top - 0.6)) / 0.6, 0, 1)), V[:, 1], V[:, 2]]))
    piece(H, "Chassis", "Chassis", merge(*walls[:2], pan, fwall, rwall), col="primary", mat="metal", pri=0.5)
    piece(H, "Roof", "Chassis", merge(roof, *walls[2:]), col="primary" if not school else "primary", mat="metal", pri=0.6)
    if decker:
        # upper deck: second window band + floor between decks hidden in the walls
        y0d = roof_in + 0.1
        mid = np.array([(zb + 0.3, y0d), (zt - 0.3, y0d), (zt - 0.3, y0d + 1.6), (zb + 0.3, y0d + 1.6)])
        md = [xf(extrude(mid, t, bevel=0.08, seg=1), (s * (hw - t / 2), 0, 0)) for s in (-1, 1)]
        md.append(box((W - 0.1, 0.3, zt - zb - 0.6), (0, y0d + 0.15, (zb + zt) / 2), r=0.05, seg=0))
        md.append(box((W, y0d + 1.6 - belt + 0.4, 0.4), (0, (y0d + 1.6 + belt - 0.4) / 2, zb + 0.2), r=0.2, seg=1))
        piece(H, "UpperDeck", "Chassis", merge(*md), col="primary", mat="metal", pri=0.7)
    piece(H, "Liners", "Chassis", merge(*(K.arch_liner(z, wr, ra, hw - 0.4) for z in axles)), col="black", mat="plastic", role="detail", pri=1.5)
    # glass: side bands (+ upper deck), windshield, rear window
    g = []
    gth = 0.08
    bands = [(belt - 0.05, win_top + 0.05)]
    if decker:
        bands.append((roof_in + 1.65, top - 0.45))
    for y0, y1 in bands:
        for s in (-1, 1):
            g.append(cbox((gth, y1 - y0, zt - zb - 0.8), (s * (hw - t / 2), (y0 + y1) / 2, (zb + zt) / 2 + 0.2), c=0.02))
        g.append(cbox((W - 1.0, y1 - y0 - 0.3, gth), (0, (y0 + y1) / 2, zt - 0.2), c=0.02))
    wsh = (roof_in + (deck_h if decker else 0) + 0.05) - (belt - 0.45)
    wsg = xf(box((W - 0.5, wsh, gth), (0, wsh / 2, 0), r=0.03, seg=0), (0, belt - 0.45, zb + 0.15), r=(-6, 0, 0))
    g.append(wsg)
    piece(H, "Glass", "Chassis", merge(*g), col="glass", mat="glass", role="window", pri=0.8, tr=0.45, ao=False)
    # window pillars + rub rails + front door frame
    pil = []
    n = int((zt - zb - 1.5) / 2.6)
    for y0, y1 in bands:
        for s in (-1, 1):
            for z in np.linspace(zb + 0.6, zt - 0.6, n + 1):
                pil.append(cbox((0.14, y1 - y0 + 0.1, 0.28), (s * (hw + 0.02), (y0 + y1) / 2, z), c=0.04))
    dz0 = zb + 0.7
    pil += [cbox((0.16, win_top - floor + 0.2, 0.18), (hw + 0.05, (win_top + floor) / 2, z), c=0.04) for z in (dz0, dz0 + 1.2, dz0 + 2.4)]
    piece(H, "Pillars", "Chassis", merge(*pil), col="black", mat="plastic", role="detail", pri=1.2)
    door = merge(cbox((0.08, win_top - floor - 0.3, 2.3), (hw + 0.03, (win_top + floor) / 2, dz0 + 1.2), c=0.02))
    piece(H, "DoorGlass", "Chassis", door, col="glass", mat="glass", role="window", pri=1.4, tr=0.4, ao=False)
    rails = [cbox((0.1, 0.2, zt - zb - 0.6), (s * (hw + 0.04), y, (zb + zt) / 2), c=0.04) for s in (-1, 1) for y in ((sill + 0.5, belt - 0.15) if not school else (sill + 0.5, floor + 1.1, belt - 0.15))]
    piece(H, "Rails", "Chassis", merge(*rails), col="black", mat="plastic", role="detail", pri=1.6)
    # front: hood (school) or flat face
    if school:
        hp = round_poly(np.array([(zn + 0.15, sill), (zn, sill + 0.6), (zn + 0.1, floor + 1.4), (zn + 0.6, floor + 1.9), (zb + 0.2, floor + 2.0), (zb + 0.2, sill)]),
                        [0.15, 0.2, 0.4, 0.4, 0.0, 0.0], 3)
        hoodm = warp(extrude(hp, W * 0.62, bevel=0.25, seg=2), lambda V: np.column_stack([V[:, 0] * np.interp(V[:, 2], [zn, zb], [0.9, 1.0]), V[:, 1], V[:, 2]]))
        fend = []
        for z in axles[:1]:
            fp = [(zn + 0.9, sill + 0.3), (zn + 1.1, floor + 0.9), (z - 0.3, floor + 1.25), (zb + 0.2, floor + 1.25), (zb + 0.2, sill + 0.3)]
            fend = [xf(extrude(round_poly(np.array(fp), 0.3, 2), 1.3, bevel=0.2), (s * (hw - 0.65), 0, 0)) for s in (-1, 1)]
        piece(H, "Hood", "Chassis", merge(hoodm, *fend), col="primary", mat="metal", pri=0.7)
        piece(H, "Grille", "Chassis", box((2.6, 1.5, 0.15), (0, floor + 0.35, zn - 0.02), r=0.08), col="metal", mat="metal", role="detail", pri=1.4)
        K.lamp_pair(H, "Headlight", "Chassis", (1.9, floor + 0.5, zn + 0.1), r=0.34, depth=0.2)
        H.bone("StopArm", "Chassis", (-hw - 0.08, belt - 0.2, zb + 2.2))
        sign = K.lathe_profile([(-0.06, 0), (-0.06, 0.7), (0.06, 0.7), (0.06, 0)], 8, "x")
        sign = xf(sign, (-hw - 0.2, belt - 0.2, zb + 2.2), r=(22.5, 0, 0))
        piece(H, "StopSign", "StopArm", sign, col="red", mat="plastic", role="detail", pri=1.4)
        fl = merge(*(lamp((s * (hw - 0.6), top - 0.4, zb - 0.05), 0.25, 0.12) for s in (-1, 1)))
        piece(H, "Flashers", "Chassis", fl, col=AMBER, mat="glass", role="light", pri=1.8, ao=False)
    else:
        K.lamp_pair(H, "Headlight", "Chassis", (hw - 0.9, sill + 0.9, zb - 0.06), shape="rect", w=1.1, h=0.5, depth=0.24)
        piece(H, "Grille", "Chassis", box((3.2, 0.6, 0.12), (0, sill + 0.9, zb - 0.04), r=0.06), col="black", mat="metal", role="detail", pri=1.4)
    sign = box((W * 0.62, 0.6, 0.12), (0, roof_in + (deck_h if decker else 0) - 0.3, zb + 0.05), r=0.06)
    piece(H, "DestSign", "Chassis", sign, col=AMBER if not school else "black", mat="glass", role="light", pri=1.7, ao=False)
    bz = zn if school else zb
    bump = merge(box((W + 0.15, 0.55, 0.55), (0, sill - 0.05, bz - 0.2), r=0.15), box((W + 0.15, 0.55, 0.55), (0, sill - 0.05, zt + 0.2), r=0.15))
    piece(H, "Bumpers", "Chassis", bump, col="black" if school else "darker", mat="plastic", role="detail", pri=1.3)
    tl = K.lamp((hw - 0.5, sill + 1.2, zt + 0.02), 0, 0.14, axis="+z", shape="rect", w=0.5, h=1.0)
    mpiece(H, "Taillight#", "Chassis", tl, col=RED_L, mat="glass", role="light", pri=1.6, ao=False)
    mir = merge(rod((hw, top - 1.6 - deck_h, zb + 0.5), (hw + 0.8, top - 1.5 - deck_h, zb - 0.4), 0.07, segs=6),
                box((0.25, 1.0, 0.5), (hw + 0.85, top - 2.0 - deck_h, zb - 0.45), r=0.08))
    mpiece(H, "Mirror#", "Chassis", mir, col="black", mat="metal", role="detail", pri=1.8)
    # interior: driver platform + seat + dash + wheel; passenger rows; wheel tubs
    dx = -hw + 1.75
    hip_z = zb + 2.6
    piece(H, "Seat", "Chassis", K.bucket_seat((dx, hip, hip_z), floor=floor), col="darker", mat="cloth", role="seat", pri=1.0)
    dash = box((W - 0.8, 1.0, 0.9), (0, belt - 0.1, zb + 0.75), r=0.15, seg=1)
    swc = (dx, hip + 1.35, hip_z - 1.45)
    sw = K.steering_mesh(swc, r=0.75, tilt=30, col_len=0.0)
    plat = box((2.4, hip - floor - 1.2, 3.0), (dx, floor + (hip - floor - 1.2) / 2, hip_z - 0.5), r=0.05, seg=0)
    piece(H, "Dash", "Chassis", merge(dash, sw, rod(swc, (dx, belt - 0.2, zb + 1.0), 0.09, segs=8), plat), col="darker", mat="plastic", role="detail", pri=1.2)
    tubs = merge(*(box((1.9, 2 * wr + 0.3 - floor, 2 * ra + 0.3), (s * (hw - 0.3 - 0.95), (floor + 2 * wr + 0.3) / 2, z), r=0.2, seg=1) for s in (-1, 1) for z in axles),
                 box((W - 0.7, 0.1, zt - zb - 1.0), (0, floor + 0.02, (zb + zt) / 2), r=0.03, seg=0))
    piece(H, "Interior", "Chassis", tubs, col="darker", mat="cloth", role="detail", pri=1.4)
    rows = []
    zr0 = hip_z + 2.6
    zz = zr0
    while zz < zt - 1.6:
        if not any(abs(zz - z) < ra + 0.6 for z in axles):
            for s in (-1, 1):
                x = s * (hw - 0.3 - 1.05)
                rows.append(box((2.0, 0.35, 1.1), (x, floor + 1.05, zz), r=0.08, seg=0))
                rows.append(box((2.0, 1.6, 0.3), (x, floor + 1.9, zz + 0.6), r=0.08, seg=0, rot_=(8, 0, 0)))
                rows.append(box((0.3, 1.0, 0.3), (x, floor + 0.45, zz), r=0.03, seg=0))
        zz += 2.3
    half = len(rows) // 2 // 3 * 3
    piece(H, "Rows", "Chassis", merge(*rows[:half]), col="secondary" if not school else [0.25, 0.3, 0.45], mat="cloth", role="seat", pri=1.8)
    piece(H, "Rows2", "Chassis", merge(*rows[half:]), col="secondary" if not school else [0.25, 0.3, 0.45], mat="cloth", role="seat", pri=1.9)

    def extra(pose, s):
        if school:
            K.add(pose, "StopArm", (0, 0, 0, 0, -1.45 * K._bump(s, 0.05, 0.95), 0))

    _finish(H, wheels, steer, top, L, (dx, hip, hip_z), (0, floor, zn - 0.6), (hw - 0.8, sill - 0.3, zt + 0.4), sym=8,
            attack="honk" if school else "ram", extra_attack=extra if school else None, enter=(hw + 1.8, 0, zb + 1.9))
    return H


@hero("bus", FAM)
def bus():
    return _bus("bus", preview=pv("#2B6CB0", "#F2F2F2"))


@hero("school bus", FAM)
def school_bus():
    return _bus("school bus", L=32.0, school=True, preview=pv("#F7B500", "#1A1A1A"))


@hero("double decker bus", FAM)
def double_decker():
    return _bus("double decker bus", L=30.0, decker=True, preview=pv("#C8102E", "#F2E8CF"))


# ==================================================================================================== tracked + work machines
def _clips_tracked(H, wheels, height, length, extra_attack=None, extra_idle=None, extra_move=None, attack="ram"):
    K.vehicle_clips(H, wheels, susp="Chassis", height=height, length=length, sym=10, attack=attack, roll=0.4, bob=0.6,
                    extra_attack=extra_attack, extra_idle=extra_idle, extra_move=extra_move, turns=1.0)


def _cab_box(H, bone, x0, x1, y0, y1, z0, z1, col="primary", post=0.14, glass_tr=0.45, name="Cab"):
    """Boxy machine cab: thin glass panes on all four sides (the seated rider shows through), corner posts, roof slab
    with a sun visor and a beacon base."""
    th = 0.035
    xc, yc, zc = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    h = y1 - y0 - 0.02
    g = [cbox((th, h, z1 - z0 - post), (x, yc, zc), c=0.01) for x in (x0 + post / 2, x1 - post / 2)]
    g += [cbox((x1 - x0 - post, h, th), (xc, yc, z), c=0.01) for z in (z0 + post / 2, z1 - post / 2)]
    piece(H, name + "Glass", bone, merge(*g), col="glass", mat="glass", role="window", pri=0.9, tr=glass_tr, ao=False)
    posts = [cbox((post, y1 - y0, post), (x, yc, z), c=0.03) for x in (x0 + post / 2 - 0.02, x1 - post / 2 + 0.02) for z in (z0 + post / 2 - 0.02, z1 - post / 2 + 0.02)]
    rails = [cbox((post * 0.8, post * 0.8, z1 - z0), (x, y0 + (y1 - y0) * 0.45, zc), c=0.02) for x in (x0 + post / 2 - 0.02, x1 - post / 2 + 0.02)]
    roof = box((x1 - x0 + 0.2, 0.16, z1 - z0 + 0.25), (xc, y1 + 0.06, zc), r=0.06)
    visor = cbox((x1 - x0, 0.05, 0.25), (xc, y1 - 0.05, z0 - 0.12), c=0.02)
    piece(H, name, bone, merge(roof, visor, *posts, *rails), col=col, mat="metal", role="body", pri=0.8)


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
    K.finish_scaled(H, 2.35)  # real scale: hull ~18 studs, rider seated in the glazed cab
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
    K.finish_scaled(H, 2.35)
    return H


@hero("tank", FAM)
def tank():
    """Main battle tank: sloped hull with fenders and side skirts over the tracks, turret with mantlet and long
    fume-extracted gun (recoils), commander's cupola with an open hatch and seat, MG, smoke launchers, tow hooks."""
    H = _new("tank", pv("#5B6B3A", "#3A4428"), ("vehicle", "military"))
    H.bone("Chassis", "Body", (0, 1.3, 0))
    wheels = K.tracks(H, "Body", 1.75, -3.0, 3.0, 1.05, r_end=0.62, n_road=6, r_road=0.42, wheel_col="secondary", cleats=30, wheel_names=True)
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
    H.bone("Barrel", "Turret", (0, 2.7, -2.0))
    mant = box((1.1, 0.75, 0.5), (0, 2.7, -2.15), r=0.12, seg=1)
    gun = merge(K.lathe_profile([(-2.2, 0), (-2.2, 0.17), (-5.0, 0.15), (-6.4, 0.13), (-6.4, 0.0)], 14, "z"),
                K.lathe_profile([(-4.6, 0), (-4.6, 0.18), (-4.5, 0.24), (-3.9, 0.24), (-3.8, 0.17), (-3.8, 0)], 14, "z"),
                K.tube_ring(0.18, 0.09, 0.4, axis="z", pos=(0, 0, -6.25)))
    gun = xf(gun, (0, 2.7, 0))
    piece(H, "Mantlet", "Barrel", mant, col="secondary", mat="metal", role="detail", pri=0.9)
    piece(H, "Gun", "Barrel", gun, col="primary", mat="metal", role="detail", pri=0.7)
    cup = merge(cyl(0.35, 0.5, (0.75, 3.35, 0.7), "y", segs=16), *[cbox((0.18, 0.12, 0.1), (0.75 + 0.45 * math.cos(a), 3.4, 0.7 + 0.45 * math.sin(a)), c=0.02) for a in np.linspace(0, TAU, 6, endpoint=False)])
    hatch = cyl(0.08, 0.48, (0.75, 3.95, 1.25), "z", segs=16, r=(75, 0, 0))
    mg = merge(rod((-0.7, 3.45, 0.6), (-0.7, 3.45, -0.6), 0.05, segs=6), cbox((0.18, 0.25, 0.5), (-0.7, 3.42, 0.7), c=0.03), rod((-0.7, 3.2, 0.7), (-0.7, 3.4, 0.7), 0.05, segs=6))
    smoke = merge(*[xf(cyl(0.35, 0.08, (0, 0, 0), "z", segs=8), (s * (1.3 + 0.12 * k), 2.75 + 0.15 * (k % 2), -1.55), r=(25, s * 20, 0)) for s in (-1, 1) for k in range(3)])
    bustle = box((2.4, 0.08, 0.5), (0, 3.15, 2.55), r=0.02)
    piece(H, "Cupola", "Turret", merge(cup, hatch, bustle), col="secondary", mat="metal", role="detail", pri=1.1)
    piece(H, "TurretGear", "Turret", merge(mg, smoke), col="darker", mat="metal", role="detail", pri=1.6)
    # crew seat inside the turret basket (the rider rides hidden inside; seat stays out of sight)
    seat = K.seat_mesh((0.0, 1.72, 0.35), w=0.6, d=0.5, back=0.5, bucket=False)
    piece(H, "Seat", "Turret", seat, col="darker", mat="cloth", role="seat", pri=2.6)
    dh = merge(cyl(0.06, 0.32, (-0.9, 2.18, -2.75), "y", segs=14), *[cbox((0.16, 0.12, 0.1), (-0.9 + dx, 2.24, -3.02), c=0.02) for dx in (-0.2, 0.0, 0.2)])
    piece(H, "DriverHatch", "Chassis", dh, col="secondary", mat="metal", role="detail", pri=1.5)
    ant = rod((-1.0, 3.1, 2.3), (-1.05, 5.2, 2.5), 0.02, segs=4)
    piece(H, "Antenna", "Turret", ant, col="darker", mat="metal", role="detail", pri=2.4)
    star = K.lathe_profile([(-0.02, 0), (-0.02, 0.32), (0.02, 0.32), (0.02, 0)], 5, "x")
    piece(H, "Star", "Turret", xf(star, (1.38, 2.7, 0.6), r=(0, 0, 0)), col="white", mat="plastic", role="detail", pri=2.0)
    K.mount(H, "Seat", (0.0, 1.77, 0.35), (0.6, 0.2, 0.5), "Turret")
    H.socket("head", (0, 3.6, 0.3), "Turret")
    H.socket("mouth", (0, 2.7, -6.5), "Barrel")
    H.socket("muzzle", (0, 2.7, -6.5), "Barrel")
    H.socket("exhaust", (0, 2.0, 4.0), "Chassis")
    H.rig.update({"head": "Turret"})

    def atk(pose, s):
        aim = K._ease(s / 0.3) if s < 0.3 else 1.0
        rec = K._bump(s, 0.35, 0.7)
        back = 1 - K._ease((s - 0.75) / 0.25) if s > 0.75 else 1.0
        K.add(pose, "Barrel", (0, 0, 0.7 * rec, 0.06 * aim * back, 0, 0))
        K.add(pose, "Chassis", (0, 0, 0.15 * rec, 0.05 * rec, 0, 0))

    def idl(pose, u):
        K.add(pose, "Turret", (0, 0, 0, 0, 0.25 * math.sin(TAU * u), 0))

    _clips_tracked(H, wheels, 3.4, 8.0, extra_attack=atk, extra_idle=idl)
    # real scale: hull ~21 studs; the rider is hidden inside the turret (head below the roof, enters by the left track)
    K.finish_scaled(H, 2.6, hidden=True, enter=(-7.6, 0, 0.0))
    return H


@hero("armored car", FAM)
def armored_car():
    H = _new("armored car", pv("#55603F", "#2E3324"), ("vehicle", "military"))
    W, wr = 3.9, 0.9
    H.bone("Chassis", "Body", (0, wr + 0.3, 0))
    specs = []
    for tag, z in zip(("F", "M", "B"), (-2.6, 0.0, 2.6)):
        specs += [dict(name=f"Wheel{tag}R", pos=(1.6, wr, z), r=wr, w=0.75, side=1, steer=(tag == "F")),
                  dict(name=f"Wheel{tag}L", pos=(-1.6, wr, z), r=wr, w=0.75, side=-1, steer=(tag == "F"))]
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
    H.bone("Barrel", "Turret", (0, 3.85, -0.4))
    gun = merge(K.lathe_profile([(-0.3, 0), (-0.3, 0.12), (-2.4, 0.08), (-2.4, 0)], 10, "z"), box((0.5, 0.4, 0.4), (0, 0, -0.2), r=0.06))
    piece(H, "Gun", "Barrel", xf(gun, (0, 3.85, 0)), col="darker", mat="metal", role="detail", pri=0.9)
    # roof hatch behind the turret; the crew seat sits inside under the turret (rider hidden)
    seat = K.seat_mesh((0, 1.95, 0.4), w=0.6, d=0.5, back=0.5, bucket=False)
    hatch = merge(K.torus(0.42, 0.06, "y", 16, 4, pos=(0, 3.42, 1.7)), cyl(0.08, 0.42, (0, 3.85, 2.2), "z", segs=14, r=(70, 0, 0)))
    piece(H, "Seat", "Turret", seat, col="darker", mat="cloth", role="seat", pri=2.6)
    piece(H, "Hatch", "Chassis", hatch, col="secondary", mat="metal", role="detail", pri=1.4)
    gear = merge(*[box((0.8, 0.2, 0.25), (0, 1.1, z), r=0.05) for z in (-4.2, 3.95)], *[cyl(0.3, 0.17, (s * 1.0, 1.7, -4.12), "z", segs=10) for s in (-1, 1)],
                 cbox((0.25, 1.4, 0.25), (1.5, 1.3, 3.7), c=0.04))
    piece(H, "Bumpers", "Chassis", gear, col="darker", mat="metal", role="detail", pri=1.4)
    lens = merge(*[K.lamp((s * 1.0, 1.7, -4.28), 0.13, 0.06) for s in (-1, 1)])
    piece(H, "Lamps", "Chassis", lens, col=LENS, mat="glass", role="light", pri=1.8, ao=False)
    # hull detail: side + rear doors, stowage bins, rivet rows, grab rails, periscopes, exhaust; turret smoke dischargers
    det, tdet = [], []
    for s_ in (-1, 1):
        det.append(cbox((0.06, 0.95, 0.85), (s_ * 1.72, 1.95, 1.35), c=0.03))
        det.append(cbox((0.08, 0.08, 0.3), (s_ * 1.77, 2.0, 1.6), c=0.02))
        det.append(box((0.35, 0.45, 1.3), (s_ * 1.75, 1.45, -1.3), r=0.05, seg=0))
        det += [cbox((0.05, 0.07, 0.07), (s_ * 1.75 - s_ * 0.0, 2.45, z), c=0.015) for z in np.linspace(-2.0, 3.0, 9)]
        det.append(rod((s_ * 1.4, 3.42, -0.8), (s_ * 1.4, 3.42, 2.4), 0.035, segs=6))
        det += [cbox((0.2, 0.14, 0.12), (s_ * 0.45, 3.0, -1.65), c=0.03)]
        tdet += [xf(cyl(0.3, 0.07, (0, 0, 0), "z", segs=8), (s_ * (0.55 + 0.14 * k), 4.0, -0.15), r=(25, s_ * 15, 0)) for k in range(3)]
    det.append(cbox((1.6, 1.3, 0.06), (0, 2.0, 3.92), c=0.03))
    det.append(K.tube_ring(0.14, 0.1, 0.6, axis="y", pos=(1.2, 3.2, 3.2)))
    tdet.append(box((0.65, 0.5, 0.6), (0, 3.85, -0.45), r=0.08, seg=0))
    piece(H, "Details", "Chassis", merge(*det), col="secondary", mat="metal", role="detail", pri=1.5)
    piece(H, "Mantlet", "Turret", merge(*tdet), col="secondary", mat="metal", role="detail", pri=1.2)

    def atk(pose, s):
        K.add(pose, "Barrel", (0, 0, 0.3 * K._bump(s, 0.3, 0.55) + 0.3 * K._bump(s, 0.55, 0.8), 0, 0, 0))

    _finish(H, wheels, steer, 4.2, 8.2, (0, 2.0, 0.4), (0, 3.85, -2.6), (1.5, 2.0, 3.9), bone="Turret", seat_size=(0.6, 0.2, 0.5), extra_attack=atk,
            extra_idle=lambda p, u: K.add(p, "Turret", (0, 0, 0, 0, 0.3 * math.sin(TAU * u), 0)))
    H.socket("muzzle", (0, 3.85, -2.5), "Barrel")
    # real scale (~19 studs): six-wheeled armoured car, rider hidden under the turret
    K.finish_scaled(H, 2.25, hidden=True, enter=(-6.0, 0, -1.0))
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
    K.finish_scaled(H, 2.4)
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
    K.finish_scaled(H, 1.9)
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
    K.finish_scaled(H, 2.2)
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
