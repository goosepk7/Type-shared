"""Cars (land-vehicle mounts): sedan "car", taxi, police car, sports car, muscle car, convertible, limousine, hot rod,
off roader (jeep), monster truck lives in h_trucks. One parametric road-car builder: a side-profile body slab with
real wheel arches, warped for plan taper / tumblehome / hood crown (hard edges kept), a glass greenhouse with
proud roof + A/B/C pillars (glass reads recessed between them, translucent so the seats and wheel show), chrome
belt trim, bumpers, grille, lamps, mirrors, door seams + handles, exhausts and four tyre + rim wheels on their own
bones. Themed bodies (banana, hot dog, bathtub, couch, shoe ...) sit on the same rolling chassis.
"""
import math

import numpy as np

from kit import hero
from map import VEH
import landveh_kit as K
from landveh_kit import box, cyl, bar, rod, extrude, warp, merge, mirror, xf, lamp, bezel, piece, mpiece, round_poly

FAM = "cars"

AMBER = [1.0, 0.62, 0.12]
RED_L = [0.85, 0.08, 0.08]
BLUE_L = [0.15, 0.35, 0.95]
LENS = [0.95, 0.96, 0.92]

BASE = dict(
    # real game scale (studs) around a seated R15 rider: hip point (seat_x, hip, hip_z), rider faces -Z
    L=14.0,           # bumper to bumper
    W=6.8,            # body width
    wr=1.2,           # wheel radius
    ww=0.95,          # tyre width
    wr_rear=None,     # bigger rear wheels (muscle / sports)
    ww_rear=None,
    track_in=0.1,     # wheel inset from the body side
    wb=8.75,          # wheelbase
    axle_off=-0.08,   # wheelbase centre offset (+ = rearward)
    sill=0.5,         # body bottom between the arches
    floor=0.8,        # cabin floor top
    hip=2.0,          # rider hip y (cushion top = hip - 0.1); hip - floor = shin length unless the footwell is sunk
    hip_z=-0.7,       # driver hip z
    seat_x=1.05,      # driver at -seat_x (left-hand drive), passenger at +seat_x
    rear_hip_z=1.6,   # rear bench (None = two-seater)
    belt=3.25,        # beltline (window sill / door top)
    hood=2.75,        # hood height at the front edge
    nose=2.3,         # height of the nose face top
    deck=3.3,         # trunk lid height
    ws=-3.55,         # windshield base z (cowl)
    fw=-2.95,         # firewall z (front of the cabin tub)
    bulk=2.75,        # rear bulkhead z (back of the cabin tub)
    roof0=-1.55,      # roof front z
    roof1=2.1,        # roof rear z
    back=4.5,         # rear window base z
    roof_in=None,     # roof underside (default hip + ROOF_CLEAR)
    cabin="sedan",    # sedan | fastback | wagon | open
    doors=4,
    tumble=0.12,      # greenhouse tumblehome
    nose_taper=0.1,
    crown=0.1,
    bpillar=0.35,
    quarter=None,     # extra quarter-window pillar z (wagons)
    rim="alloy",
    spokes=5,
    rim_col="metal",
    knobby=0.0,
    lamps="rect",     # rect | round
    grille="wide",    # wide | split | none | jeep
    bumper="body",    # body | chrome | black
    bull=False,       # push bar
    exhaust=1,        # 0, 1, 2 (twin)
    spoiler=False,
    scoop=False,
    stripes=False,
    lightbar=False,
    taxi=False,
    doors_col=None,   # police: doors in secondary
    rollbar=False,
    spare=False,
    flares=False,
    roofrack=False,
    sidepipes=False,
    boot=False,       # convertible: folded soft top behind the seats
    extra_b=(),       # extra B pillars (limousine)
    roof_lights=False,
    mudflaps=False,
    seat_col="darker",
    trim_col="darker",
    header=None,      # open cabins: windshield header height above the belt
    attack="ram",
    arch_gap=0.2,
    haunch=False,
    preview={},
)


def _car(hid, **kw):
    P = dict(BASE)
    P.update(kw)
    from kit import Hero

    H = Hero(hid, plan="Vehicle", gait="drive", tags=["vehicle", "car"])
    H.preview = P["preview"]
    L, W, wr, ww = P["L"], P["W"], P["wr"], P["ww"]
    wrr, wwr = P["wr_rear"] or wr, P["ww_rear"] or ww
    zn, zt = -L / 2, L / 2
    zf, zr = P["axle_off"] - P["wb"] / 2, P["axle_off"] + P["wb"] / 2
    sill, floor, hip, hip_z, belt = P["sill"], P["floor"], P["hip"], P["hip_z"], P["belt"]
    ws, fw, bulk, back = P["ws"], P["fw"], P["bulk"], P["back"]
    cab = P["cabin"]
    roof_in = P["roof_in"] or hip + K.ROOF_CLEAR
    hw = W / 2
    t = 0.3
    sx = P["seat_x"]

    # ------------------------------------------------------------------ skeleton
    H.bone("Chassis", "Body", (0, wr + 0.1, (zf + zr) / 2))
    xw = hw - P["track_in"] - ww / 2
    xwr = hw - P["track_in"] - wwr / 2
    H.bone("SteerFR", "Body", (xw, wr, zf))
    H.bone("SteerFL", "Body", (-xw, wr, zf))
    H.bone("WheelFR", "SteerFR", (xw, wr, zf))
    H.bone("WheelFL", "SteerFL", (-xw, wr, zf))
    H.bone("WheelBR", "Body", (xwr, wrr, zr))
    H.bone("WheelBL", "Body", (-xwr, wrr, zr))

    # ------------------------------------------------------------------ body warp (plan taper, tumblehome, crown)
    tz0, tz1 = zn + 1.8, zt - 1.4
    hood_y = P["hood"]

    def bodywarp(V):
        x, y, z = V[:, 0], V[:, 1], V[:, 2]
        sz = 1 - P["nose_taper"] * np.clip((tz0 - z) / 1.8, 0, 1) ** 2 - 0.06 * np.clip((z - tz1) / 1.4, 0, 1) ** 2
        sy = 1 - 0.05 * np.clip((y - (belt - 0.8)) / 0.8, 0, 1) - 0.05 * np.clip((sill + 0.45 - y) / 0.45, 0, 1)
        x2 = x * sz * sy
        cr = P["crown"] * np.clip(1 - (x / hw) ** 2, 0, 1) * np.clip((y - (hood_y - 0.4)) / 0.4, 0, 1)
        return np.column_stack([x2, y + cr, z])

    def surf_x(y, z, off=0.0):
        """x of the body side surface (right) at (y, z) plus an outward offset."""
        return float(bodywarp(np.array([[hw, y, z]], float))[0, 0]) + off

    # ------------------------------------------------------------------ lower body: side profile with the cabin notch
    front = [((zn + 0.75, sill), 0.4), ((zn + 0.02, sill + 0.7), 0.35), ((zn - 0.06, P["nose"]), 0.55), ((zn + 0.85, hood_y), 0.75),
             ((ws, belt), 0.35)]
    if cab == "wagon":
        tail = [((back, belt), 0.25), ((zt - 0.12, P["deck"]), 0.3), ((zt + 0.02, P["deck"] - 0.7), 0.3)]
    else:
        tail = [((back, belt), 0.3), ((zt - 0.8, P["deck"]), 0.7), ((zt + 0.04, P["deck"] - 0.65), 0.4)]
    tail += [((zt, sill + 0.75), 0.35), ((zt - 0.6, sill), 0.35)]
    ag = P["arch_gap"]
    # split at the cabin: front section (nose -> firewall), rear section (bulkhead -> tail), thin floor pan between
    fpts = front + [((fw, belt), 0.0), ((fw, sill), 0.0)] + K.car_arch(zf, wr, wr + ag, sill)
    rpts = [((bulk, sill), 0.0), ((bulk, belt), 0.0)] + tail + K.car_arch(zr, wrr, wrr + ag, sill)
    profs = [round_poly(np.array([p for p, _ in q]), [r for _, r in q], seg=3) for q in (fpts, rpts)]
    pan = np.array([(fw - 0.02, sill), (bulk + 0.02, sill), (bulk + 0.02, floor), (fw - 0.02, floor)])
    body = warp(merge(*(extrude(q, W, bevel=0.3, seg=3) for q in profs), extrude(pan, W - 0.02, bevel=0.1, seg=1)), bodywarp)
    piece(H, "Chassis", "Chassis", body, col="primary", mat="metal", role="body", pri=0.5)
    # doors: the cabin tub's side walls (shut lines between the slabs)
    splits = ((P["bpillar"],) + tuple(P["extra_b"])) if P["doors"] == 4 else ()
    K.door_walls(H, "Chassis", hw, t, fw, bulk, floor, belt, splits=splits, warp_fn=bodywarp, col=P["doors_col"] or "primary")
    liners = merge(K.arch_liner(zf, wr, wr + ag, hw - 0.35), K.arch_liner(zr, wrr, wrr + ag, hw - 0.35))
    piece(H, "Liners", "Chassis", liners, col="black", mat="plastic", role="detail", pri=1.4)

    if P["stripes"]:
        def top_y(z):
            ys = []
            for prof in profs:
                for i in range(len(prof)):
                    a, b = prof[i], prof[(i + 1) % len(prof)]
                    if (a[0] - z) * (b[0] - z) <= 0 and abs(b[0] - a[0]) > 1e-9:
                        ys.append(a[1] + (b[1] - a[1]) * (z - a[0]) / (b[0] - a[0]))
            return max(ys) if ys else belt
        segs_ = []
        for z0_, z1_ in ((zn + 0.25, ws - 0.15), (back + 0.15, zt - 0.2)):
            zz = np.linspace(z0_, z1_, 16)
            upper = [(z, top_y(z) + 0.05) for z in zz]
            lower = [(z, top_y(z) - 0.2) for z in zz[::-1]]
            poly = np.array(upper + lower)
            segs_ += [xf(extrude(poly, 0.5, bevel=0.02, seg=1), (sx_, 0, 0)) for sx_ in (-0.45, 0.45)]
        s = warp(merge(*segs_), bodywarp)
        piece(H, "Stripes", "Chassis", s, col="secondary", mat="metal", role="detail", pri=1.7)

    # ------------------------------------------------------------------ greenhouse
    xg = (hw - t) * 0.95 + 0.04
    tum = P["tumble"]
    if cab == "open":
        hdr = belt + (P["header"] or 1.55)
        xt = K.greenhouse_real(H, "Chassis", ws, belt, ws + (hdr - belt) * 0.62, None, None, hdr, xg, tum=0.04, open_=True,
                               roof_col="primary", frame_col="metal" if P["bumper"] == "chrome" else P["trim_col"], pw=0.3)
        roofy = hdr + 0.2
    else:
        xt = K.greenhouse_real(H, "Chassis", ws, belt, P["roof0"], P["roof1"], back, roof_in, xg, tum=tum, crown=P["crown"],
                               bpillars=tuple(([P["bpillar"]] if P["doors"] == 4 or cab != "wagon" else [])) + tuple(P["extra_b"]),
                               quarter=P["quarter"], rear_pw=0.55 if cab == "fastback" else 0.42)
        roofy = roof_in + 0.22 + P["crown"]
        trim = merge(*(bar((s * (surf_x(belt, 0) + 0.0), belt + 0.01, fw + 0.1), (s * (surf_x(belt, 0) + 0.0), belt + 0.01, back - 0.15), 0.1, 0.08, r=0.03)
                       for s in (-1, 1)))
        piece(H, "BeltTrim", "Chassis", trim, col="metal" if P["bumper"] == "chrome" else "black", mat="metal", role="detail", pri=2.2)

    # ------------------------------------------------------------------ interior
    xi = hw - t
    zs_ = [fw] + list(splits) + [bulk]
    spans = list(zip(zs_[:-1], zs_[1:]))
    inter = [box((2 * xi - 0.06, 0.12, bulk - fw - 0.06), (0, floor + 0.02, (fw + bulk) / 2), r=0.04, seg=0)]
    piece(H, "DoorCards", "Chassis", K.door_cards(hw, t, spans, floor, belt, bodywarp), col=P["trim_col"], mat="cloth", role="detail", pri=1.6)
    con_z0, con_z1 = fw + 0.65, hip_z + 0.45
    inter.append(box((0.5, hip - floor + 0.1, con_z1 - con_z0), (0, floor + (hip - floor + 0.1) / 2, (con_z0 + con_z1) / 2), r=0.08, seg=0))
    inter.append(rod((0, hip + 0.05, hip_z - 0.9), (0, hip + 0.45, hip_z - 1.0), 0.04, segs=6))
    inter.append(K.cbox((0.16, 0.2, 0.16), (0, hip + 0.5, hip_z - 1.0), c=0.05))
    if cab != "open":
        inter.append(box((2 * xt - 0.1, 0.07, P["roof1"] - P["roof0"] - 0.1), (0, roof_in - 0.015, (P["roof0"] + P["roof1"]) / 2), r=0.03, seg=0))
        if back - bulk > 0.4:
            inter.append(box((2 * xg - 0.4, 0.07, back - bulk - 0.25), (0, belt + 0.02, (bulk + back - 0.1) / 2), r=0.03, seg=0))
    piece(H, "Interior", "Chassis", merge(*inter), col=P["trim_col"], mat="cloth", role="detail", pri=1.3)
    dash = K.dash_mesh(ws, fw, floor, belt, xi * 0.93 - 0.02)
    hoodb = K.instruments(H, "Chassis", -sx, belt + 0.12, fw + 0.55, w=1.0)
    swc = (-sx, hip + 1.45, hip_z - 1.45)
    sw = K.steering_mesh(swc, r=0.5, tilt=62, col_len=0.0)
    col_ = rod(swc, (-sx, belt + 0.0, fw + 0.5), 0.07, segs=8)
    piece(H, "Dash", "Chassis", merge(dash, hoodb, sw, col_), col="black", mat="plastic", role="detail", pri=1.2)
    seat = K.bucket_seat((-sx, hip, hip_z), floor=floor)
    piece(H, "Seat", "Chassis", seat, col=P["seat_col"], mat="cloth", role="seat", pri=1.0)
    piece(H, "Seat2", "Chassis", K.bucket_seat((sx, hip, hip_z), floor=floor), col=P["seat_col"], mat="cloth", role="seat", pri=1.5)
    if P["rear_hip_z"] is not None:
        bench = K.bucket_seat((0, hip + 0.05, P["rear_hip_z"]), w=2 * xi - 0.5, bolster=False, headrest=False, floor=floor, back=2.2)
        piece(H, "RearSeat", "Chassis", bench, col=P["seat_col"], mat="cloth", role="seat", pri=1.7)

    # ------------------------------------------------------------------ front: lamps, grille, bumper
    chrome, dark = [], []
    ylamp = P["nose"] - 0.3
    xl = hw * 0.6
    if P["lamps"] == "round":
        hl = lamp((xl, ylamp, zn - 0.12), 0.36, 0.22)
        chrome += [K.bezel((xl, ylamp, zn - 0.1), 0.36, 0.16), K.bezel((-xl, ylamp, zn - 0.1), 0.36, 0.16)]
    else:
        hl = K.lamp((xl, ylamp, zn - 0.06), 0, 0.26, shape="rect", w=1.5, h=0.52)
        hl = warp(hl, lambda V: np.column_stack([V[:, 0], V[:, 1], V[:, 2] + 0.3 * np.clip((V[:, 0] - (xl - 0.4)) / 1.1, 0, 1) ** 2]))
    mpiece(H, "Headlight#", "Chassis", hl, col=LENS, mat="glass", role="light", pri=1.3, ao=False)
    ind = K.lamp((xl + 0.5, ylamp - 0.45, zn + 0.05), 0, 0.12, shape="rect", w=0.42, h=0.16)
    mpiece(H, "Indicator#", "Chassis", ind, col=AMBER, mat="glass", role="light", pri=2.2, ao=False)
    gw = 2 * (xl - (0.72 if P["lamps"] != "round" else 0.5))
    if P["grille"] != "none":
        gh = 0.72 if P["grille"] != "jeep" else 1.1
        gy = ylamp - 0.05
        gm = [box((gw, gh, 0.14), (0, gy, zn - 0.03), r=0.08)]
        if P["grille"] == "jeep":
            for k in range(7):
                gx = -gw / 2 + gw * (k + 0.5) / 7
                gm.append(K.cbox((0.12, gh * 0.82, 0.06), (gx, gy, zn - 0.1), c=0.03))
        piece(H, "Grille", "Chassis", merge(*gm), col="black", mat="metal", role="detail", pri=1.5)
        if P["grille"] != "jeep":
            for k in range(4):
                chrome.append(K.cbox((gw * 0.92, 0.05, 0.05), (0, gy - gh * 0.33 + gh * 0.22 * k, zn - 0.11), c=0.015))
            chrome.append(box((gw + 0.14, 0.08, 0.08), (0, gy + gh / 2 + 0.02, zn - 0.08), r=0.03))
    by = sill + 0.55
    if P["bumper"] == "body":
        fb = box((W * 0.9, 0.55, 0.5), (0, by, zn + 0.12), r=0.24, seg=2)
        rb = box((W * 0.9, 0.55, 0.5), (0, by, zt - 0.12), r=0.24, seg=2)
        bcol, bmat = "primary", "metal"
        dark.append(box((W * 0.5, 0.3, 0.12), (0, by - 0.05, zn - 0.14), r=0.06))  # lower intake
        for s_ in (-1, 1):
            dark.append(box((0.62, 0.34, 0.12), (s_ * W * 0.36, by - 0.05, zn - 0.08), r=0.08))
        fog = lamp((W * 0.36, by - 0.05, zn - 0.16), 0.13, 0.08)
        mpiece(H, "Fog#", "Chassis", fog, col=LENS, mat="glass", role="light", pri=2.3, ao=False)
        dark.append(box((W * 0.7, 0.14, 0.4), (0, sill + 0.05, zt - 0.1), r=0.05))  # rear diffuser lip
    else:
        fb = box((W * 0.96, 0.46, 0.42), (0, by, zn - 0.12), r=0.16, seg=2)
        rb = box((W * 0.96, 0.46, 0.42), (0, by, zt + 0.12), r=0.16, seg=2)
        bcol, bmat = ("metal", "metal") if P["bumper"] == "chrome" else ("black", "plastic")
    piece(H, "Bumpers", "Chassis", merge(fb, rb), col=bcol, mat=bmat, role="detail", pri=1.1)
    if P["bull"]:
        bb = []
        for s in (-1, 1):
            bb.append(rod((s * 1.1, by - 0.1, zn - 0.3), (s * 1.1, P["nose"] + 0.2, zn - 0.5), 0.1, segs=10))
        bb.append(rod((-1.1, P["nose"] + 0.2, zn - 0.5), (1.1, P["nose"] + 0.2, zn - 0.5), 0.1, ext=0.1, segs=10))
        bb.append(rod((-1.15, by + 0.4, zn - 0.45), (1.15, by + 0.4, zn - 0.45), 0.09, segs=10))
        bb.append(box((2.6, 0.38, 0.26), (0, by, zn - 0.4), r=0.08))
        piece(H, "PushBar", "Chassis", merge(*bb), col="black", mat="metal", role="detail", pri=1.5)

    # ------------------------------------------------------------------ rear lamps, plate, exhaust
    yt = P["deck"] - 0.45
    tl = K.lamp((hw * 0.6, yt, zt - 0.02), 0, 0.2, axis="+z", shape="rect", w=1.5, h=0.5)
    tl = warp(tl, lambda V: np.column_stack([V[:, 0], V[:, 1], V[:, 2] - 0.25 * np.clip((V[:, 0] - hw * 0.45) / 1.0, 0, 1) ** 2]))
    mpiece(H, "Taillight#", "Chassis", tl, col=RED_L, mat="glass", role="light", pri=1.4, ao=False)
    pz = 0.16 if P["bumper"] == "body" else 0.36
    plates = merge(box((1.25, 0.42, 0.06), (0, by + 0.42 if P["bumper"] == "body" else by, zt + pz), r=0.04),
                   box((1.25, 0.34, 0.06), (0, by, zn - pz - (0.0 if P["bumper"] == "body" else 0.0)), r=0.04))
    piece(H, "Plates", "Chassis", plates, col="white", mat="plastic", role="detail", pri=2.4)
    for k in range(P["exhaust"]):
        ex = hw - 1.1 - 0.4 * k
        chrome.append(K.tube_ring(0.15, 0.1, 0.5, axis="z", pos=(ex, sill + 0.08, zt + 0.0)))
        if P["exhaust"] == 2:
            chrome.append(K.tube_ring(0.15, 0.1, 0.5, axis="z", pos=(-ex, sill + 0.08, zt + 0.0)))
    # mirrors on the doors at the A pillar
    mz = fw + 0.35
    mx = surf_x(belt - 0.1, mz)
    mir = merge(bar((mx - 0.08, belt - 0.05, mz), (mx + 0.4, belt + 0.12, mz + 0.05), 0.12, 0.09, r=0.03),
                box((0.3, 0.38, 0.5), (mx + 0.46, belt + 0.22, mz + 0.08), r=0.12, seg=2))
    mpiece(H, "Mirror#", "Chassis", mir, col="primary" if not P["doors_col"] else P["doors_col"], mat="metal", role="detail", pri=1.9)
    # door handles + fuel flap + rocker seam (proud of the skin)
    for s in (1, -1):
        for a, b in spans:
            hz, hy = b - 0.55, belt - 0.4
            chrome.append(K.cbox((0.07, 0.11, 0.48), (s * surf_x(hy, hz, 0.04), hy, hz), c=0.03))
    # side character line (body colour, proud) above the arches, black rocker strip below the doors
    ytop_arch = max(2 * wr, 2 * wrr) + ag + 0.18
    cy_ = max(belt - 0.62, ytop_arch)
    if cy_ < belt - 0.3:
        cl = extrude(np.array([(zn + 1.7, cy_), (zt - 1.1, cy_), (zt - 1.1, cy_ + 0.08), (zn + 1.7, cy_ + 0.08)]), 0.16, bevel=0.03, seg=1)
        cl = warp(xf(cl, (hw - 0.03, 0, 0)), bodywarp)
        piece(H, "SideLine", "Chassis", merge(cl, mirror(cl)), col=P["doors_col"] or "primary", mat="metal", role="detail", pri=2.3)
    for s_ in (-1, 1):
        dark.append(bar((s_ * surf_x(sill + 0.22, 0, 0.03), sill + 0.22, zf + wr + ag + 0.15), (s_ * surf_x(sill + 0.22, 0, 0.03), sill + 0.22, zr - wrr - ag - 0.15), 0.12, 0.2, r=0.04))
    fz = (zr + back) / 2 + 0.2
    dark.append(K.cbox((0.06, 0.45, 0.45), (surf_x(belt - 0.5, fz, 0.02), belt - 0.5, fz), c=0.08))
    if P["sidepipes"]:
        for s in (-1, 1):
            chrome.append(rod((s * (hw + 0.12), sill + 0.15, zf + 1.6), (s * (hw + 0.12), sill + 0.15, zr - 1.6), 0.14, ext=0.0))
    piece(H, "Trim", "Chassis", merge(*dark), col="black", mat="plastic", role="detail", pri=2.1)

    # ------------------------------------------------------------------ extras
    if P["spoiler"]:
        sy_ = P["deck"] + 0.7
        sp = merge(box((W * 0.9, 0.1, 0.85), (0, sy_, zt - 0.5), r=0.04, rot_=(-8, 0, 0)),
                   box((0.12, 0.75, 0.55), (W * 0.3, sy_ - 0.38, zt - 0.55), r=0.04), box((0.12, 0.75, 0.55), (-W * 0.3, sy_ - 0.38, zt - 0.55), r=0.04),
                   box((0.08, 0.4, 0.9), (W * 0.45, sy_ + 0.08, zt - 0.5), r=0.03), box((0.08, 0.4, 0.9), (-W * 0.45, sy_ + 0.08, zt - 0.5), r=0.03))
        piece(H, "Spoiler", "Chassis", sp, col="secondary", mat="metal", role="detail", pri=1.3)
    if P["scoop"]:
        hz = (zn + ws) / 2 + 0.2
        sc = box((1.4, 0.45, 1.8), (0, hood_y + 0.38, hz), r=0.14, seg=2)
        sc = merge(sc, box((1.1, 0.26, 0.08), (0, hood_y + 0.4, hz - 0.9), r=0.04))
        piece(H, "Scoop", "Chassis", sc, col="black", mat="metal", role="detail", pri=1.4)
    if P["lightbar"]:
        ly = roofy + 0.05
        zc_ = (P["roof0"] + P["roof1"]) / 2 - 0.3
        base = box((3.4, 0.16, 0.62), (0, ly + 0.05, zc_), r=0.05)
        for s in (-1, 1):
            base = merge(base, box((0.3, 0.2, 0.3), (s * 1.4, ly - 0.05, zc_), r=0.04))
        piece(H, "LightBar", "Chassis", base, col="black", mat="plastic", role="detail", pri=1.3)
        lr = box((1.45, 0.34, 0.52), (0.8, ly + 0.28, zc_), r=0.12, seg=2)
        piece(H, "SirenRed", "Chassis", lr, col=RED_L, mat="glass", role="light", pri=1.4, ao=False)
        piece(H, "SirenBlue", "Chassis", mirror(lr), col=BLUE_L, mat="glass", role="light", pri=1.4, ao=False)
        lr2 = box((0.5, 0.3, 0.5), (0, ly + 0.26, zc_), r=0.1, seg=1)
        piece(H, "SirenWhite", "Chassis", lr2, col=LENS, mat="glass", role="light", pri=1.9, ao=False)
    if P["taxi"]:
        ty = roofy - 0.02
        zc_ = (P["roof0"] + P["roof1"]) / 2
        sign = extrude(round_poly(np.array([(-1.15, 0), (-0.85, 0.62), (0.85, 0.62), (1.15, 0)]), [0, 0.14, 0.14, 0], 2), 0.5, bevel=0.06, axis="z")
        sign = xf(sign, (0, ty, zc_), r=(0, 90, 0))
        piece(H, "TaxiSign", "Chassis", sign, col="white", mat="plastic", role="detail", pri=1.3)
        chk = []
        for s in (1, -1):
            for k in range(14):
                z = fw + 0.25 + k * 0.4
                if z > bulk - 0.2:
                    break
                for row in (0, 1):
                    if (k + row) % 2:
                        continue
                    y = belt - 0.85 - row * 0.3
                    chk.append(K.cbox((0.05, 0.29, 0.39), (s * surf_x(y, z + 0.2, 0.05), y, z + 0.2), c=0.012))
        piece(H, "Checker", "Chassis", merge(*chk), col="secondary", mat="plastic", role="detail", pri=1.9)
    if P["spare"]:
        sw_ = K.tyre(1.0, 0.7, ri=0.6, segs=24, knobby=P["knobby"])
        sw_ = merge(sw_, K.rim(0.6, 0.7, "steel", segs=18))
        sw_ = xf(sw_, (0, P["deck"] - 0.4, zt + 0.4), r=(0, 90, 0))
        piece(H, "Spare", "Chassis", sw_, col="tyre", mat="rubber", role="detail", pri=1.6)
    if P["flares"]:
        fl = []
        for z, rr in ((zf, wr), (zr, wrr)):
            arc = []
            ra = rr + 0.38
            for k in range(13):
                a = math.radians(8 + 164 * k / 12)
                arc.append((z + ra * math.cos(a), rr + ra * math.sin(a)))
            for k in range(12, -1, -1):
                a = math.radians(8 + 164 * k / 12)
                arc.append((z + (ra - 0.3) * math.cos(a), rr + (ra - 0.3) * math.sin(a)))
            for s in (-1, 1):
                fl.append(xf(extrude(np.array(arc), 0.5, bevel=0.07, seg=1), (s * (hw - 0.05), 0, 0)))
        piece(H, "Flares", "Chassis", merge(*fl), col="black", mat="plastic", role="detail", pri=1.5)
    if P["roofrack"]:
        rr_ = []
        rx = xt - 0.25
        for s in (-1, 1):
            rr_.append(rod((s * rx, roofy + 0.25, P["roof0"] + 0.4), (s * rx, roofy + 0.25, P["roof1"] - 0.3), 0.07, segs=8))
            for z in (P["roof0"] + 0.5, P["roof1"] - 0.4):
                rr_.append(K.cbox((0.16, 0.3, 0.3), (s * rx, roofy + 0.1, z), c=0.04))
        for z in np.linspace(P["roof0"] + 0.9, P["roof1"] - 0.8, 3):
            rr_.append(rod((-rx, roofy + 0.25, z), (rx, roofy + 0.25, z), 0.06, segs=8))
        piece(H, "RoofRack", "Chassis", merge(*rr_), col="black", mat="metal", role="detail", pri=1.8)
    if P["rollbar"]:
        zb = bulk - 0.25
        rb_ = [rod((s * (xi - 0.15), belt - 0.1, zb), (s * (xi - 0.35), hip + 3.75, zb - 0.1), 0.13, segs=10) for s in (-1, 1)]
        rb_.append(rod((-(xi - 0.35), hip + 3.75, zb - 0.1), ((xi - 0.35), hip + 3.75, zb - 0.1), 0.13, ext=0.1, segs=10))
        rb_ += [rod((s * (xi - 0.35), hip + 3.75, zb - 0.1), (s * (xi - 0.2), belt - 0.05, zb + 1.7), 0.11, segs=10) for s in (-1, 1)]
        piece(H, "RollBar", "Chassis", merge(*rb_), col="black", mat="metal", role="detail", pri=1.2)
        roofy = max(roofy, hip + 3.9)
    if P["boot"]:
        bt = box((2 * xg - 0.5, 0.55, 1.3), (0, belt + 0.18, back - 0.3), r=0.25, seg=2)
        piece(H, "SoftTop", "Chassis", bt, col="secondary", mat="cloth", role="detail", pri=1.4)
    if P["roof_lights"]:
        rl = [box((2.6, 0.14, 0.18), (0, roofy + 0.1, P["roof0"] + 0.3), r=0.04)]
        lens = []
        for k in range(4):
            x = -1.1 + 0.73 * k
            rl.append(box((0.55, 0.5, 0.26), (x, roofy + 0.38, P["roof0"] + 0.2), r=0.08))
            lens.append(K.lamp((x, roofy + 0.38, P["roof0"] + 0.05), 0.2, 0.08))
        piece(H, "RoofLamps", "Chassis", merge(*rl), col="black", mat="plastic", role="detail", pri=1.6)
        piece(H, "RoofLens", "Chassis", merge(*lens), col=LENS, mat="glass", role="light", pri=1.9, ao=False)
    if P["haunch"]:
        # sculpted body-colour fender bulges over the wheels (wide-body sports look) + side intakes + hood vents
        hs = []
        for z, rr, ww_ in ((zf, wr, ww), (zr, wrr, wwr)):
            ra = rr + ag
            arc = [(z + (ra + 0.42) * math.cos(math.radians(a)), rr + (ra + 0.42) * math.sin(math.radians(a))) for a in np.linspace(-8, 188, 15)]
            arc += [(z + (ra + 0.0) * math.cos(math.radians(a)), rr + (ra + 0.0) * math.sin(math.radians(a))) for a in np.linspace(188, -8, 15)]
            f_ = extrude(np.array(arc), 0.6, bevel=0.2, seg=2)
            f_ = warp(xf(f_, (hw - 0.12, 0, 0)), lambda V: np.column_stack([V[:, 0] + 0.12 * np.clip(1 - ((V[:, 1] - rr) / (ra + 0.4)) ** 2, 0, 1), V[:, 1], V[:, 2]]))
            hs += [f_, mirror(f_)]
        piece(H, "Haunches", "Chassis", warp(merge(*hs), bodywarp), col="primary", mat="metal", role="body", pri=0.9)
        for s_ in (-1, 1):
            iz = bulk + 0.6
            dark.append(K.cbox((0.12, 0.7, 1.1), (s_ * surf_x(belt - 0.85, iz, 0.03), belt - 0.85, iz), c=0.12))
        for s_ in (-1, 1):
            for k in range(3):
                dark.append(K.cbox((0.5, 0.06, 0.1), (s_ * 1.3, hood_y + 0.28 + 0.06 * k, zn + 2.3 + 0.28 * k), c=0.02))
    if P["mudflaps"]:
        mf = []
        for s_ in (-1, 1):
            for z, rr in ((zf, wr), (zr, wrr)):
                mf.append(box((0.8, 0.8, 0.07), (s_ * xw, 0.55, z + rr + 0.3), r=0.04))
        piece(H, "Mudflaps", "Chassis", merge(*mf), col="black", mat="rubber", role="detail", pri=2.2)
    if chrome:
        piece(H, "Chrome", "Chassis", merge(*chrome), col="metal", mat="metal", role="detail", pri=2.0)

    # ------------------------------------------------------------------ wheels
    for nm, pos, rr, w_, side in (("WheelFR", (xw, wr, zf), wr, ww, 1), ("WheelFL", (-xw, wr, zf), wr, ww, -1),
                                  ("WheelBR", (xwr, wrr, zr), wrr, wwr, 1), ("WheelBL", (-xwr, wrr, zr), wrr, wwr, -1)):
        K.wheel_pieces(H, nm, nm, pos, rr, w_, style=P["rim"], spokes=P["spokes"], knobby=P["knobby"], side=side, rim_col=P["rim_col"], segs=30)

    # ------------------------------------------------------------------ rig
    K.ride(H, (-sx, hip, hip_z), (-(hw + 1.6), 0, hip_z - 0.6), seat_size=(1.5, 0.2, 1.3))
    H.socket("head", (0, roofy + 0.3, 0), "Chassis")
    H.socket("mouth", (0, P["nose"], zn - 0.4), "Chassis")
    H.socket("exhaust", (hw - 1.1, sill + 0.08, zt + 0.4), "Chassis")
    H.rig.update({"head": "Chassis"})
    K.vehicle_clips(H, [("WheelFR", wr), ("WheelFL", wr), ("WheelBR", wrr), ("WheelBL", wrr)], susp="Chassis", height=roofy, length=L,
                    sym=P["spokes"] if P["rim"] in ("alloy", "mag") else 8, steer=("SteerFR", "SteerFL"), attack=P["attack"])
    return H


def pv(p, s, **kw):
    d = {"primary": p, "secondary": s, "darker": "#2A2C31", "black": "#16171A"}
    d.update(kw)
    return d


@hero("car", FAM)
def car():
    return _car("car", preview=pv("#C8102E", "#2B2D33"))


@hero("taxi", FAM)
def taxi():
    return _car("taxi", taxi=True, bumper="black", rim="steel", preview=pv("#F7C600", "#1A1A1A"))


@hero("police car", FAM)
def police_car():
    return _car("police car", lightbar=True, doors_col="secondary", bull=True, bumper="black", rim="steel",
                preview=pv("#1B2A49", "#F5F5F5"))


@hero("sports car", FAM)
def sports_car():
    # low two-seater: the footwell is sunk (legs reach under the dash), wide fastback greenhouse, mid-engine deck
    return _car("sports car", L=14.5, W=7.3, haunch=True, wr=1.05, ww=1.0, wr_rear=1.1, ww_rear=1.25, wb=8.9, axle_off=0.1, sill=0.32, floor=0.4,
                hip=1.45, hip_z=-0.3, seat_x=1.1, rear_hip_z=None, seat_col=[0.11, 0.11, 0.12], belt=2.6, hood=2.05, nose=1.6, deck=2.75, arch_gap=0.12, ws=-3.9, fw=-2.6, bulk=1.15,
                roof0=-1.05, roof1=0.85, back=5.0, cabin="fastback", doors=2, tumble=0.2, nose_taper=0.16, crown=0.12, spoiler=True,
                exhaust=2, grille="none", bumper="body", spokes=5, rim_col="black", preview=pv("#FFC300", "#1A1A1A"))


@hero("muscle car", FAM)
def muscle_car():
    return _car("muscle car", L=15.0, W=7.0, wr=1.15, ww=1.0, wr_rear=1.2, ww_rear=1.25, wb=9.0, axle_off=0.15, sill=0.45, floor=0.65,
                hip=1.8, hip_z=-0.2, rear_hip_z=None, belt=2.95, hood=2.6, nose=2.15, deck=2.85, ws=-3.0, fw=-2.45, bulk=1.4,
                roof0=-0.95, roof1=1.0, back=4.6, cabin="fastback", doors=2, tumble=0.16, nose_taper=0.04, scoop=True, stripes=True,
                exhaust=2, lamps="round", grille="wide", bumper="chrome", rim="mag", spokes=6, preview=pv("#1F3A93", "#F2F2F2"))


@hero("convertible", FAM)
def convertible():
    return _car("convertible", cabin="open", boot=True, L=14.5, doors=2, rear_hip_z=None, bulk=1.5, back=3.4, hip_z=-0.3, fw=-2.55,
                ws=-3.2, bumper="chrome", lamps="round", rim="wire", spokes=24, header=1.5, seat_col=[0.82, 0.72, 0.55],
                preview=pv("#D7263D", "#F2E8CF"))


@hero("limousine", FAM)
def limousine():
    return _car("limousine", L=24.0, wb=18.0, axle_off=0.3, ws=-7.8, fw=-7.2, hip_z=-4.95, bulk=7.6, rear_hip_z=6.45, roof0=-5.8,
                roof1=6.6, back=8.8, bpillar=-3.9, extra_b=(-0.5, 3.0), bumper="chrome", tumble=0.1, rim="steel",
                preview=pv("#151515", "#C0C0C0", glass="#151A20"))


@hero("station wagon", FAM)
def station_wagon():
    return _car("station wagon", cabin="wagon", L=14.8, roof1=6.4, back=6.85, bulk=2.75, deck=3.3, quarter=4.6, roofrack=True,
                doors_col="secondary", bumper="chrome", rim="steel", preview=pv("#8A6E4B", "#E8DCC2"))


@hero("rally car", FAM)
def rally_car():
    return _car("rally car", cabin="wagon", L=13.4, wb=8.2, wr=1.2, ww=1.0, sill=0.62, floor=0.9, hip=2.1, belt=3.3, hood=2.85, nose=2.4,
                deck=3.4, fw=-2.75, ws=-3.35, hip_z=-0.5, roof0=-1.35, bulk=2.5, rear_hip_z=1.4, roof1=4.6, back=5.9, doors=4, knobby=0.04, roof_lights=True, mudflaps=True, spoiler=True, stripes=True,
                rim="alloy", spokes=6, rim_col="white", bumper="black", preview=pv("#1E5BC6", "#F5F5F5"))


@hero("off roader", FAM)
def off_roader():
    return _car("off roader", cabin="open", rollbar=True, L=13.6, W=7.0, wb=8.3, axle_off=0.1, wr=1.45, ww=1.15, track_in=-0.25, sill=1.25,
                floor=1.45, hip=2.65, hip_z=0.15, rear_hip_z=None, belt=3.75, hood=3.65, nose=3.2, deck=3.7, ws=-2.9, fw=-2.2, bulk=2.4,
                back=4.4, doors=2, nose_taper=0.02, crown=0.04, lamps="round", grille="jeep", bumper="black", flares=True, spare=True,
                knobby=0.08, rim="steel", exhaust=1, header=1.6, preview=pv("#4B5D3A", "#2A2A2A"))


@hero("suv", FAM)
def suv():
    return _car("suv", cabin="wagon", L=16.0, W=7.0, wr=1.35, ww=1.05, wb=9.6, axle_off=0.0, sill=0.95, floor=1.25, hip=2.45, hip_z=-0.5, belt=3.75,
                hood=3.45, nose=2.95, deck=3.8, ws=-3.8, fw=-3.1, bulk=2.9, rear_hip_z=1.75, roof0=-1.6, roof1=6.5, back=7.15, quarter=5.0,
                roofrack=True, bumper="black", flares=True, rim="alloy", spokes=6, preview=pv("#2E3B4E", "#9AA3AD"))


# ==================================================================================================== special cars
def _rig_common(H, wheels, steer, height, length, seat_part, seat_pos, seat_size, nose, tail, sym=5, attack="ram", scale=1.0, **kw):
    """Rig in the authoring units, then K.finish_scaled brings the whole model to real game scale (x scale) and
    writes the ride data (seat = rider hip, enter on the left flank, mount length)."""
    K.mount(H, seat_part, seat_pos, seat_size, "Chassis")
    H.socket("head", (0, height + 0.3, 0), "Chassis")
    H.socket("mouth", nose, "Chassis")
    H.socket("exhaust", tail, "Chassis")
    H.rig.update({"head": "Chassis"})
    K.vehicle_clips(H, wheels, susp="Chassis", height=height, length=length, sym=sym, steer=steer, attack=attack, **kw)
    K.finish_scaled(H, scale)


def _new(hid, tags=("vehicle", "car"), preview=None):
    from kit import Hero
    H = Hero(hid, plan="Vehicle", gait="drive", tags=list(tags))
    H.preview = preview or {}
    return H


@hero("race car", FAM)
def race_car():
    """Open-wheel single seater: needle nose, cockpit with halo, sidepods, airbox, front + rear wings, fat slicks."""
    H = _new("race car", preview=pv("#E10600", "#F5F5F5", darker="#1C1C20"))
    H.bone("Chassis", "Body", (0, 0.7, 0))
    zf, zr = -2.9, 2.35
    wheels, steer = K.add_wheels(H, K.four_wheels(1.55, zf, 1.5, zr, 0.62, 0.62, 0.68, 0.85), rim="alloy", spokes=10, rim_col="darker", grooves=False)
    # monocoque: side profile, then a plan warp (needle nose, wide cockpit, tapering tail)
    prof = round_poly(np.array([(-5.0, 0.42), (-5.05, 0.6), (-2.6, 0.95), (-1.0, 1.2), (-0.3, 1.22), (0.25, 1.95), (0.9, 1.95), (3.3, 1.05),
                                (3.6, 0.95), (3.6, 0.45), (-1.0, 0.25), (-4.0, 0.3)]), [0.05, 0.1, 0.4, 0.2, 0.25, 0.15, 0.3, 0.5, 0.1, 0.1, 0.4, 0.3], 3)

    def mw(V):
        x, y, z = V[:, 0], V[:, 1], V[:, 2]
        s = np.interp(z, [-5.1, -3.0, -1.2, 0.2, 2.0, 3.7], [0.32, 0.55, 0.95, 1.0, 0.7, 0.5])
        return np.column_stack([x * s, y + 0.06 * np.clip(1 - (x * s / 0.6) ** 2, 0, 1) * np.clip((y - 0.6) / 0.4, 0, 1), z])

    body = warp(extrude(prof, 1.25, bevel=0.18, seg=3), mw)
    # cockpit opening as a dark tub
    piece(H, "Chassis", "Chassis", body, col="primary", mat="metal", pri=0.5)
    pods = []
    for s in (-1, 1):
        pp = round_poly(np.array([(-1.2, 0.3), (-1.25, 0.95), (0.4, 1.05), (2.6, 0.75), (2.7, 0.3)]), [0.1, 0.35, 0.5, 0.25, 0.1], 3)
        pods.append(xf(warp(extrude(pp, 0.75, bevel=0.2, seg=2), lambda V: np.column_stack([V[:, 0] * np.interp(V[:, 2], [-1.3, 0, 2.7], [0.8, 1, 0.6]), V[:, 1], V[:, 2]])), (s * 0.85, 0, 0)))
    piece(H, "Sidepods", "Chassis", merge(*pods), col="primary", mat="metal", pri=0.8)
    # wings
    fw = merge(box((3.9, 0.08, 0.7), (0, 0.32, -4.75), r=0.03), box((3.6, 0.07, 0.4), (0, 0.48, -4.55), r=0.03, rot_=(-12, 0, 0)),
               box((0.06, 0.45, 0.85), (1.95, 0.42, -4.7), r=0.02), box((0.06, 0.45, 0.85), (-1.95, 0.42, -4.7), r=0.02))
    rw = merge(box((2.9, 0.08, 0.75), (0, 2.2, 3.55), r=0.03, rot_=(8, 0, 0)), box((2.9, 0.07, 0.4), (0, 2.45, 3.75), r=0.03, rot_=(22, 0, 0)),
               box((0.07, 1.05, 1.1), (1.45, 2.05, 3.6), r=0.03), box((0.07, 1.05, 1.1), (-1.45, 2.05, 3.6), r=0.03),
               box((2.6, 0.07, 0.45), (0, 0.85, 3.55), r=0.03))
    piece(H, "FrontWing", "Chassis", fw, col="secondary", mat="metal", pri=0.9)
    piece(H, "RearWing", "Chassis", merge(rw, bar((0, 1.05, 3.1), (0, 2.15, 3.45), 0.1, 0.25, r=0.03)), col="secondary", mat="metal", pri=0.9)
    # suspension arms (front + rear wishbones) and halo
    arms = []
    for s in (-1, 1):
        for zz, x0, r_, z0 in ((zf, 0.32, 0.62, -2.6), (zr, 0.55, 0.68, 2.0)):
            arms.append(rod((s * x0, 0.55, z0 - 0.35), (s * 1.3, r_ - 0.05, zz), 0.035, segs=6))
            arms.append(rod((s * x0, 0.55, z0 + 0.35), (s * 1.3, r_ - 0.05, zz), 0.035, segs=6))
            arms.append(rod((s * x0, 0.85, z0), (s * 1.3, r_ + 0.15, zz), 0.035, segs=6))
    halo = merge(K.torus(0.55, 0.06, axis="y", segs=20, rsegs=6, pos=(0, 1.62, -0.35)), rod((0, 1.25, -1.15), (0, 1.62, -0.92), 0.07, segs=8))
    halo = merge(*[h for h in [halo]])
    piece(H, "Arms", "Chassis", merge(*arms), col="darker", mat="metal", role="detail", pri=1.6)
    piece(H, "Halo", "Chassis", halo, col="darker", mat="metal", role="detail", pri=1.2)
    seat = K.seat_mesh((0, 1.0, -0.35), w=0.7, d=0.7, back=0.6, recline=30)
    piece(H, "Seat", "Chassis", seat, col="darker", mat="cloth", role="seat", pri=1.0)
    sw = K.steering_mesh((0, 1.32, -0.95), r=0.18, tilt=75, col_len=0.3)
    mirrors = merge(*(merge(bar((s * 0.45, 1.2, -1.2), (s * 0.75, 1.35, -1.25), 0.04, 0.04), K.cbox((0.25, 0.14, 0.1), (s * 0.8, 1.38, -1.25), c=0.03)) for s in (-1, 1)))
    piece(H, "Cockpit", "Chassis", merge(sw, mirrors), col="darker", mat="plastic", role="detail", pri=1.5)
    num = merge(K.cbox((0.05, 0.5, 0.7), (0.66, 1.25, 0.45), c=0.02), K.cbox((0.05, 0.5, 0.7), (-0.66, 1.25, 0.45), c=0.02),
                K.cbox((0.8, 0.05, 0.25), (0, 1.995, 0.6), c=0.02))
    piece(H, "Livery", "Chassis", num, col="white", mat="plastic", role="detail", pri=2.2)
    tl = K.lamp((0, 0.75, 3.62), 0, 0.08, axis="+z", shape="rect", w=0.3, h=0.18)
    piece(H, "RainLight", "Chassis", tl, col=RED_L, mat="glass", role="light", pri=2.3, ao=False)
    _rig_common(H, wheels, steer, 2.0, 9.0, "Seat", (0, 1.1, -0.35), (0.7, 0.2, 0.7), (0, 0.5, -5.2), (0, 0.8, 3.7), sym=10, scale=1.75)
    return H


@hero("go kart", FAM)
def go_kart():
    H = _new("go kart", preview=pv("#2BA84A", "#F2C200", darker="#222226"))
    H.bone("Chassis", "Body", (0, 0.45, 0))
    wheels, steer = K.add_wheels(H, K.four_wheels(1.25, -1.6, 1.35, 1.45, 0.4, 0.42, 0.44, 0.55), rim="alloy", spokes=6, rim_col="metal", grooves=False)
    # tube frame
    fr = []
    for s in (-1, 1):
        fr.append(rod((s * 0.55, 0.3, -2.2), (s * 0.65, 0.3, 1.7), 0.06, segs=8))
        fr.append(rod((s * 0.65, 0.3, 1.45), (s * 1.2, 0.42, 1.45), 0.05, segs=8))
        fr.append(rod((s * 0.6, 0.3, -1.6), (s * 1.1, 0.4, -1.6), 0.05, segs=8))
    fr.append(rod((-0.55, 0.3, -2.2), (0.55, 0.3, -2.2), 0.06, segs=8))
    fr.append(rod((-1.0, 0.45, 2.1), (1.0, 0.45, 2.1), 0.07, segs=8))
    for s in (-1, 1):
        fr.append(rod((s * 1.0, 0.45, 2.1), (s * 0.65, 0.3, 1.6), 0.06, segs=8))
    fr.append(K.box((1.25, 0.06, 3.6), (0, 0.26, -0.2), r=0.03))
    piece(H, "Frame", "Chassis", merge(*fr), col="darker", mat="metal", role="detail", pri=1.0)
    nose = round_poly(np.array([(-2.55, 0.25), (-2.6, 0.55), (-1.9, 0.75), (-1.2, 0.75), (-1.2, 0.3)]), [0.1, 0.2, 0.2, 0.05, 0.05], 3)
    nb = warp(extrude(nose, 1.5, bevel=0.12, seg=2), lambda V: np.column_stack([V[:, 0] * np.interp(V[:, 2], [-2.6, -1.2], [0.75, 1.0]), V[:, 1], V[:, 2]]))
    pods = []
    for s in (-1, 1):
        sp = round_poly(np.array([(-0.9, 0.25), (-0.9, 0.55), (0.9, 0.6), (1.0, 0.25)]), 0.12, 2)
        pods.append(xf(extrude(sp, 0.4, bevel=0.1, seg=2), (s * 1.0, 0, 0)))
    piece(H, "Chassis", "Chassis", merge(nb, *pods), col="primary", mat="plastic", pri=0.6)
    # seat raised on a frame so the (upright) rider's feet reach the floor tray
    seat = merge(K.seat_mesh((0, 1.0, 0.45), w=0.8, d=0.7, back=0.95, recline=18), box((0.5, 0.65, 0.5), (0, 0.6, 0.45), r=0.05, seg=0))
    piece(H, "Seat", "Chassis", seat, col="secondary", mat="plastic", role="seat", pri=0.9)
    sw = K.steering_mesh((0, 2.05, -0.62), r=0.3, tilt=55, col_len=0.0)
    col = rod((0, 2.0, -0.66), (0, 0.32, -1.35), 0.05, segs=8)
    piece(H, "Steering", "Chassis", merge(sw, col), col="darker", mat="plastic", role="detail", pri=1.3)
    eng = merge(K.box((0.55, 0.5, 0.55), (0.55, 0.65, 1.55), r=0.06), cyl(0.5, 0.18, (0.55, 1.0, 1.55), "y", segs=12),
                K.tube_ring(0.07, 0.05, 0.6, axis="z", pos=(0.85, 0.65, 2.05)))
    piece(H, "Engine", "Chassis", eng, col="metal", mat="metal", role="detail", pri=1.4)
    num = K.lamp((0, 0.6, -2.5), 0, 0.05, shape="rect", w=0.5, h=0.32)
    piece(H, "NumberPlate", "Chassis", num, col="white", mat="plastic", role="detail", pri=2.0)
    _rig_common(H, wheels, steer, 1.6, 5.0, "Seat", (0, 1.08, 0.45), (0.8, 0.2, 0.7), (0, 0.5, -2.7), (0.85, 0.65, 2.4), sym=6, scale=1.2)
    return H


@hero("golf cart", FAM)
def golf_cart():
    H = _new("golf cart", preview=pv("#F4F4F0", "#2E7D32"))
    H.bone("Chassis", "Body", (0, 0.5, 0))
    wheels, steer = K.add_wheels(H, K.four_wheels(1.25, -1.9, 1.25, 1.75, 0.45, 0.4), rim="steel", rim_col="white")
    prof = round_poly(np.array([(-2.8, 0.45), (-2.85, 1.15), (-2.3, 1.45), (-1.5, 1.6), (-1.35, 0.75), (2.4, 0.75), (2.75, 1.0), (2.75, 0.45)]),
                      [0.15, 0.25, 0.3, 0.1, 0.1, 0.15, 0.1, 0.1], 3)
    body = warp(extrude(prof, 2.7, bevel=0.14, seg=2), lambda V: np.column_stack([V[:, 0] * np.interp(V[:, 2], [-2.9, -2.0, 2.8], [0.82, 1.0, 1.0]), V[:, 1], V[:, 2]]))
    piece(H, "Chassis", "Chassis", body, col="primary", mat="plastic", pri=0.5)
    bench = merge(K.box((2.3, 0.25, 0.85), (0, 1.15, 0.35), r=0.1), K.box((2.3, 0.75, 0.2), (0, 1.62, 0.82), r=0.08, rot_=(10, 0, 0)),
                  K.box((2.4, 0.4, 0.95), (0, 0.92, 0.35), r=0.06))
    piece(H, "Seat", "Chassis", bench, col="secondary", mat="cloth", role="seat", pri=0.9)
    posts = []
    for s in (-1, 1):
        posts.append(rod((s * 1.15, 1.45, -1.55), (s * 1.12, 3.6, -1.05), 0.06, segs=8))
        posts.append(rod((s * 1.15, 0.8, 1.0), (s * 1.12, 3.6, 1.05), 0.06, segs=8))
    ws = box((2.2, 1.6, 0.05), (0, 2.45, -1.36), r=0.03, rot_=(-13, 0, 0))
    piece(H, "Posts", "Chassis", merge(*posts), col="darker", mat="metal", role="detail", pri=1.2)
    piece(H, "Glass", "Chassis", ws, col="glass", mat="glass", role="window", pri=1.6, tr=0.3, ao=False)
    roof = K.box((2.75, 0.14, 3.1), (0, 3.66, -0.1), r=0.07, seg=1)
    piece(H, "Roof", "Chassis", roof, col="primary", mat="plastic", pri=0.8)
    sw = K.steering_mesh((-0.55, 1.75, -1.1), r=0.25, tilt=40, col_len=0.4)
    piece(H, "Steering", "Chassis", sw, col="darker", mat="plastic", role="detail", pri=1.3)
    bag = merge(cyl(1.25, 0.32, (0, 1.55, 2.25), "y", segs=14, r=(-12, 0, 0)), K.torus(0.32, 0.05, "y", 14, 5, pos=(0, 2.15, 2.12)))
    clubs = merge(*(merge(rod((dx, 2.0, 2.1), (dx * 1.3, 2.75, 2.0), 0.03, segs=5), K.cbox((0.12, 0.1, 0.22), (dx * 1.3, 2.78, 1.95), c=0.02))
                    for dx in (-0.15, 0.0, 0.15)))
    piece(H, "GolfBag", "Chassis", bag, col="secondary", mat="cloth", role="detail", pri=1.5)
    piece(H, "Clubs", "Chassis", clubs, col="metal", mat="metal", role="detail", pri=2.0)
    hl = K.lamp((0.75, 1.1, -2.88), 0.15, 0.1)
    mpiece(H, "Headlight#", "Chassis", hl, col=LENS, mat="glass", role="light", pri=1.6, ao=False)
    bump = merge(K.box((2.6, 0.22, 0.25), (0, 0.55, -2.95), r=0.08), K.box((2.6, 0.22, 0.25), (0, 0.55, 2.85), r=0.08))
    piece(H, "Bumpers", "Chassis", bump, col="darker", mat="rubber", role="detail", pri=1.5)
    _rig_common(H, wheels, steer, 3.2, 5.6, "Seat", (-0.55, 1.3, 0.3), (0.9, 0.2, 0.8), (0, 0.8, -3.0), (0, 0.5, 2.9), sym=8, scale=1.6)
    return H


@hero("dune buggy", FAM)
def dune_buggy():
    H = _new("dune buggy", preview=pv("#F28C28", "#202020"))
    H.bone("Chassis", "Body", (0, 0.8, 0))
    wheels, steer = K.add_wheels(H, K.four_wheels(1.55, -2.2, 1.55, 1.9, 0.62, 0.5, 0.82, 0.82), rim="steel", rim_col="metal", knobby=0.08, lugs=16)
    # fibreglass tub
    prof = round_poly(np.array([(-3.2, 0.95), (-3.25, 1.35), (-1.6, 1.65), (-1.4, 1.2), (1.1, 1.2), (1.3, 1.5), (2.4, 1.5), (2.6, 0.75), (-2.6, 0.7)]),
                      [0.15, 0.3, 0.12, 0.1, 0.1, 0.12, 0.2, 0.2, 0.3], 3)
    tub = warp(extrude(prof, 2.4, bevel=0.2, seg=2), lambda V: np.column_stack([V[:, 0] * np.interp(V[:, 2], [-3.3, -1.5, 2.6], [0.7, 1.0, 1.0]), V[:, 1], V[:, 2]]))
    piece(H, "Chassis", "Chassis", tub, col="primary", mat="plastic", pri=0.5)
    cage = []
    for s in (-1, 1):
        cage.append(rod((s * 1.05, 1.2, -1.45), (s * 0.85, 3.5, -0.4), 0.07, segs=8))
        cage.append(rod((s * 0.85, 3.5, -0.4), (s * 0.85, 3.5, 0.75), 0.07, segs=8))
        cage.append(rod((s * 0.85, 3.5, 0.75), (s * 1.05, 1.25, 1.2), 0.07, segs=8))
        cage.append(rod((s * 0.85, 3.5, 0.75), (s * 0.6, 1.5, 2.4), 0.06, segs=8))
    cage.append(rod((-0.85, 3.5, -0.4), (0.85, 3.5, -0.4), 0.07, segs=8))
    cage.append(rod((-0.85, 3.5, 0.75), (0.85, 3.5, 0.75), 0.07, segs=8))
    cage.append(rod((-0.85, 3.5, 0.75), (0.85, 3.5, -0.4), 0.06, segs=8))
    piece(H, "Cage", "Chassis", merge(*cage), col="darker", mat="metal", role="detail", pri=0.9)
    seats = merge(K.seat_mesh((-0.5, 1.35, 0.25), w=0.75, d=0.7, back=1.0), K.seat_mesh((0.5, 1.35, 0.25), w=0.75, d=0.7, back=1.0))
    piece(H, "Seat", "Chassis", seats, col="secondary", mat="cloth", role="seat", pri=0.9)
    eng = merge(K.box((1.2, 0.7, 0.9), (0, 1.3, 2.25), r=0.1), cyl(0.9, 0.25, (0, 1.75, 2.3), "x", segs=12))
    for s in (-1, 1):
        eng = merge(eng, K.tube_ring(0.09, 0.065, 0.9, axis="z", pos=(s * 0.45, 1.0, 2.9)))
    piece(H, "Engine", "Chassis", eng, col="metal", mat="metal", role="detail", pri=1.2)
    sw = K.steering_mesh((-0.5, 2.25, -0.6), r=0.24, tilt=60, col_len=0.5)
    lights = merge(*(K.lamp((s * 0.55, 3.7, -0.45), 0.15, 0.12) for s in (-1, 1)))
    lb = merge(*(K.cbox((0.38, 0.32, 0.22), (s * 0.55, 3.7, -0.33), c=0.04) for s in (-1, 1)))
    piece(H, "Steering", "Chassis", merge(sw, lb), col="darker", mat="plastic", role="detail", pri=1.4)
    piece(H, "Lamps", "Chassis", lights, col=LENS, mat="glass", role="light", pri=1.7, ao=False)
    _rig_common(H, wheels, steer, 2.9, 6.6, "Seat", (-0.5, 1.45, 0.25), (0.75, 0.2, 0.7), (0, 1.2, -3.3), (0.45, 1.0, 3.3), sym=8, scale=1.8)
    return H


@hero("bumper car", FAM)
def bumper_car():
    H = _new("bumper car", preview=pv("#E53935", "#FDD835"))
    H.bone("Chassis", "Body", (0, 0.4, 0))
    wheels, steer = K.add_wheels(H, K.four_wheels(0.9, -1.2, 0.9, 1.2, 0.22, 0.2), rim="steel", grooves=False)
    plan = round_poly(np.array([(-1.6, -2.1), (1.6, -2.1), (1.75, 1.9), (-1.75, 1.9)]), 0.9, 6)  # (x, z)
    tubp = extrude(plan, 0.75, bevel=0.2, axis="y", seg=2)
    tub = xf(tubp, (0, 0.85, 0))
    back = K.box((2.6, 1.0, 0.7), (0, 1.55, 1.35), r=0.3, seg=2)
    piece(H, "Chassis", "Chassis", merge(tub, back), col="primary", mat="plastic", pri=0.5)
    ring = K.lathe_profile([(0, 0)], 4) if False else None
    rp = round_poly(np.array([(-1.85, -2.35), (1.85, -2.35), (2.0, 2.15), (-2.0, 2.15)]), 1.05, 6)
    inner = round_poly(np.array([(-1.55, -2.05), (1.55, -2.05), (1.7, 1.85), (-1.7, 1.85)]), 0.85, 6)
    # rubber bumper ring: a slab band between the two outlines (outline - inner done as a loft of 2 rings)
    rr_ = extrude(rp, 0.42, bevel=0.18, axis="y", seg=2)
    piece(H, "Bumper", "Chassis", xf(rr_, (0, 0.42, 0)), col="darker", mat="rubber", role="body", pri=0.7)
    seat = K.seat_mesh((0, 1.3, 0.45), w=1.4, d=0.8, back=0.9, bucket=False)
    piece(H, "Seat", "Chassis", seat, col="secondary", mat="cloth", role="seat", pri=0.9)
    sw = K.steering_mesh((0, 1.75, -0.75), r=0.28, tilt=50, col_len=0.6)
    piece(H, "Steering", "Chassis", sw, col="darker", mat="plastic", role="detail", pri=1.2)
    pole = merge(rod((0, 1.8, 1.55), (0, 5.2, 1.65), 0.05, segs=8), K.box((0.3, 0.12, 0.4), (0, 5.25, 1.65), r=0.04))
    piece(H, "Pole", "Chassis", pole, col="metal", mat="metal", role="detail", pri=1.4)
    flag = K.lamp((0, 1.3, -2.12), 0, 0.06, shape="rect", w=1.0, h=0.45)
    piece(H, "Badge", "Chassis", flag, col="secondary", mat="plastic", role="detail", pri=2.0)
    _rig_common(H, wheels, steer, 2.0, 4.5, "Seat", (0, 1.4, 0.45), (1.2, 0.2, 0.8), (0, 0.6, -2.4), (0, 0.6, 2.2), sym=8, attack="honk", scale=1.55)
    return H


@hero("bubble car", FAM)
def bubble_car():
    """Egg-shaped one-seater: front-opening door, bubble glass, two front wheels + one rear."""
    H = _new("bubble car", preview=pv("#7EC8E3", "#F5F5F5"))
    H.bone("Chassis", "Body", (0, 0.5, 0))
    specs = [dict(name="WheelFR", pos=(1.15, 0.42, -0.9), r=0.42, w=0.3, side=1, steer=True), dict(name="WheelFL", pos=(-1.15, 0.42, -0.9), r=0.42, w=0.3, side=-1, steer=True),
             dict(name="WheelB", pos=(0.0, 0.42, 1.35), r=0.42, w=0.3, side=1)]
    wheels, steer = K.add_wheels(H, specs, rim="disc", rim_col="white", grooves=False)
    egg = K.D.revolve([(-2.0, 0), (-1.95, 0.6), (-1.4, 1.05), (0.0, 1.2), (1.3, 1.0), (1.85, 0.55), (1.9, 0)], segs=28, axis=2, spline=3)
    egg = warp(egg, lambda V: np.column_stack([V[:, 0] * 1.05, V[:, 1] * 1.05 + 1.35, V[:, 2]]))
    # lower body = egg below the belt; glass = egg above (slightly inside) so the belt reads as a seam
    low = warp(egg, lambda V: np.column_stack([V[:, 0] * 1.02, 0.1 + (V[:, 1] - 0.1) * 0.62, V[:, 2] * 1.02]))
    piece(H, "Chassis", "Chassis", low, col="primary", mat="metal", pri=0.5)
    gl = warp(egg, lambda V: np.column_stack([V[:, 0] * 0.96, V[:, 1], V[:, 2] * 0.96]))
    piece(H, "Glass", "Chassis", gl, col="glass", mat="glass", role="window", pri=0.8, tr=0.3, ao=False)
    trim = merge(K.torus(1.0, 0.05, axis="y", segs=26, rsegs=5, pos=(0, 1.55, 0)))
    trim = warp(trim, lambda V: np.column_stack([V[:, 0] * 1.2, V[:, 1] - 0.05, V[:, 2] * 1.82]))
    piece(H, "Trim", "Chassis", trim, col="secondary", mat="metal", role="detail", pri=1.4)
    seat = K.seat_mesh((0, 1.0, 0.35), w=1.2, d=0.7, back=0.9, bucket=False)
    piece(H, "Seat", "Chassis", seat, col="darker", mat="cloth", role="seat", pri=0.9)
    sw = K.steering_mesh((0, 1.45, -0.7), r=0.22, tilt=55, col_len=0.4)
    hl = K.lamp((0.85, 1.25, -1.95), 0.16, 0.12)
    piece(H, "Steering", "Chassis", sw, col="darker", mat="plastic", role="detail", pri=1.4)
    mpiece(H, "Headlight#", "Chassis", hl, col=LENS, mat="glass", role="light", pri=1.6, ao=False)
    bump = K.torus(1.0, 0.07, axis="y", segs=24, rsegs=5)
    bump = warp(bump, lambda V: np.column_stack([V[:, 0] * 1.5, V[:, 1] + 0.75, V[:, 2] * 1.95]))
    piece(H, "Bumper", "Chassis", bump, col="metal", mat="metal", role="detail", pri=1.5)
    _rig_common(H, wheels, steer, 2.6, 4.0, "Seat", (0, 1.1, 0.35), (1.0, 0.2, 0.7), (0, 1.0, -2.1), (0.4, 0.6, 2.0), sym=8, attack="honk", scale=2.3)
    return H


# ==================================================================================================== novelty bodies
import sdf as SD  # noqa: E402


def _novelty(hid, theme, preview):
    """A themed body (sculpted SDF) on a rolling platform: four wheels, seat and steering wheel inside the shape."""
    H = _new(hid, ("vehicle", "car", "silly"), preview)
    H.bone("Chassis", "Body", (0, 0.75, 0))
    wheels, steer = K.add_wheels(H, K.four_wheels(1.55, -2.1, 1.55, 2.0, 0.62, 0.5), rim="alloy", spokes=5, rim_col="secondary" if theme != "bathtub" else "gold", grooves=False)
    plat = merge(box((2.4, 0.3, 5.6), (0, 0.72, 0), r=0.08), *[rod((-1.55, 0.62, z), (1.55, 0.62, z), 0.08, segs=8) for z in (-2.1, 2.0)])
    piece(H, "Chassis", "Chassis", plat, col="darker", mat="metal", pri=0.6)
    seat_y, seat_z, sw_y, sw_z = 1.6, 0.3, 2.15, -0.6
    if theme == "banana":
        sh = SD.tube([(0, 2.2, -3.4), (0, 1.35, -1.8), (0, 1.15, 0), (0, 1.35, 1.8), (0, 2.1, 3.2)], [0.18, 0.95, 1.1, 0.95, 0.22], k=0.3)
        sh = sh.ss(SD.round_box(0.75, 0.8, 1.3, 0.25, (0, 2.35, 0.2)), 0.2)
        H.piece("Shell", "Chassis", sh, col="primary", mat="plastic", tris=2400, res=120,
                pattern=lambda Q: 1 - 0.25 * np.clip((np.abs(Q[:, 2]) - 2.6) / 0.6, 0, 1))
        tips = SD.round_cone((0, 2.15, -3.35), (0, 2.45, -3.75), 0.2, 0.12) | SD.round_cone((0, 2.05, 3.15), (0, 2.3, 3.5), 0.22, 0.1)
        H.piece("Tips", "Chassis", tips, col="secondary", mat="plastic", tris=300, role="detail", pri=1.3)
        seat_y = 1.65
    elif theme == "hotdog":
        bun = SD.ellipsoid(1.5, 0.85, 3.3, (0, 1.45, 0)).ss(SD.round_box(0.6, 0.9, 3.6, 0.3, (0, 2.25, 0)), 0.25)
        H.piece("Bun", "Chassis", bun, col=[0.86, 0.6, 0.32], mat="plastic", tris=2200, res=120, pattern=lambda Q: 1 - 0.15 * np.clip((Q[:, 1] - 1.6) / 0.6, 0, 1))
        sau = SD.capsule((0, 1.95, -3.5), (0, 1.95, 3.5), 0.6).ss(SD.round_box(0.7, 0.6, 0.9, 0.2, (0, 2.6, 0.4)), 0.2)
        H.piece("Sausage", "Chassis", sau, col="primary", mat="plastic", tris=1600, res=110)
        pts = [(0.25 * math.sin(i * 1.3), 2.5 + 0.02 * math.cos(i), -3.0 + i * 0.32) for i in range(8)] + [(0.25 * math.sin(i * 1.3), 2.5, -3.0 + i * 0.32) for i in range(13, 20)]
        must = SD.tube(pts[:8], [0.09] * 8, k=0.05) | SD.tube(pts[8:], [0.09] * 7, k=0.05)
        H.piece("Mustard", "Chassis", must, col="secondary", mat="plastic", tris=700, role="detail", pri=1.4)
        seat_y, seat_z = 2.1, 0.5
        sw_y = 2.6
    elif theme == "bathtub":
        tub = SD.round_box(1.45, 0.95, 2.7, 0.55, (0, 1.9, 0.2)).shell(0.14) & SD.half_space(1, 1, 2.5)
        rim_ = SD.torus(1.0, 0.13, axis=1).scale3(1.38, 1.0, 2.62).at(0, 2.5, 0.2)
        tub = tub.su(rim_, 0.06)
        H.piece("Tub", "Chassis", tub, col="white", mat="plastic", tris=2400, res=128)
        feet = SD.union(*[SD.round_cone((sx * 1.15, 1.35, sz), (sx * 1.3, 0.95, sz * 1.08), 0.2, 0.14) for sx in (-1, 1) for sz in (-2.0, 2.3)])
        H.piece("Feet", "Chassis", feet, col="gold", mat="metal", tris=700, role="detail", pri=1.3)
        tap = SD.capsule((0, 2.6, 2.75), (0, 3.25, 2.75), 0.08) | SD.capsule((0, 3.25, 2.75), (0, 3.2, 2.35), 0.08) | SD.sphere(0.12, (0.35, 3.0, 2.75)) | SD.sphere(0.12, (-0.35, 3.0, 2.75))
        H.piece("Taps", "Chassis", tap, col="metal", mat="metal", tris=500, role="detail", pri=1.5)
        foam = SD.union(*[SD.sphere(0.32 + 0.1 * (i % 3), (0.75 * math.sin(i * 2.3), 2.45, -1.8 + i * 0.5)) for i in range(8)], k=0.15)
        H.piece("Foam", "Chassis", foam, col="cream", mat="plastic", tris=900, role="detail", pri=1.6)
        seat_y, seat_z = 1.7, 0.6
        sw_y, sw_z = 2.5, -0.7
    elif theme == "couch":
        base = SD.round_box(1.5, 0.35, 1.1, 0.15, (0, 1.25, 0.2))
        back = SD.round_box(1.5, 0.75, 0.3, 0.2, (0, 2.1, 1.15))
        arms = SD.round_box(0.25, 0.45, 1.15, 0.18, (1.35, 1.75, 0.2)) | SD.round_box(0.25, 0.45, 1.15, 0.18, (-1.35, 1.75, 0.2))
        H.piece("Couch", "Chassis", base.su(back, 0.1).su(arms, 0.1), col="primary", mat="cloth", tris=1800, res=120)
        cush = SD.round_box(0.55, 0.16, 0.95, 0.14, (0.57, 1.72, 0.0)) | SD.round_box(0.55, 0.16, 0.95, 0.14, (-0.57, 1.72, 0.0))
        cush = cush | SD.round_box(0.55, 0.45, 0.14, 0.12, (0.57, 2.35, 0.85)).rot(-10, 0, 0) | SD.round_box(0.55, 0.45, 0.14, 0.12, (-0.57, 2.35, 0.85))
        H.piece("Cushions", "Chassis", cush, col="secondary", mat="cloth", tris=1200, role="detail", pri=1.2)
        lamp_ = SD.capsule((1.0, 1.0, -2.6), (1.0, 2.6, -2.6), 0.05) | SD.cone(0.35, 0.18, 0.45).at(1.0, 2.8, -2.6)
        H.piece("FloorLamp", "Chassis", lamp_, col="cream", mat="plastic", tris=500, role="detail", pri=1.6)
        seat_y, seat_z = 1.9, 0.0
        sw_y, sw_z = 2.35, -1.3
        piece(H, "Column", "Chassis", rod((0, 0.85, -2.0), (0, 2.25, -1.3), 0.06, segs=8), col="darker", mat="metal", role="detail", pri=1.4)
    elif theme == "shoe":
        sole = SD.round_box(1.35, 0.25, 3.3, 0.22, (0, 1.2, 0.0)) & SD.half_space(1, -1, 0.95)
        H.piece("Sole", "Chassis", sole, col="white", mat="rubber", tris=1200, res=120)
        up = SD.ellipsoid(1.3, 0.9, 2.0, (0, 1.6, -1.3)).su(SD.round_box(1.25, 1.1, 1.4, 0.6, (0, 2.1, 1.4)), 0.6)
        up = up.ss(SD.ellipsoid(0.95, 0.9, 1.25, (0, 3.0, 1.0)), 0.2) & SD.half_space(1, -1, 1.25)
        H.piece("Upper", "Chassis", up, col="primary", mat="cloth", tris=2400, res=128,
                pattern=lambda Q: np.where(np.abs(Q[:, 1] - 1.75) < 0.12, 0.6, 1.0))
        lace = SD.union(*[SD.capsule((-0.55, 2.35 - 0.15 * i, -0.2 - 0.35 * i), (0.55, 2.35 - 0.15 * i, -0.2 - 0.35 * i), 0.07) for i in range(4)])
        H.piece("Laces", "Chassis", lace, col="white", mat="cloth", tris=600, role="detail", pri=1.3)
        swoosh = SD.capsule((1.27, 1.7, -1.5), (1.25, 2.2, 1.4), 0.12) & SD.half_space(0, -1, 1.15)
        H.piece("Swoosh", "Chassis", swoosh | swoosh.mirror_x(), col="secondary", mat="plastic", tris=600, role="detail", pri=1.5)
        seat_y, seat_z = 2.2, 1.0
        sw_y, sw_z = 2.75, 0.0
    elif theme == "duck":
        body = SD.ellipsoid(1.55, 1.0, 2.6, (0, 1.75, 0.5)).su(SD.ellipsoid(0.8, 0.7, 0.8, (0, 2.5, 2.7)).rot(0, 0, 0), 0.5)
        body = body.ss(SD.ellipsoid(1.05, 0.8, 1.2, (0, 2.85, 0.6)), 0.25)
        head = SD.sphere(0.95, (0, 3.25, -1.65))
        H.piece("Shell", "Chassis", body.su(head, 0.35), col="primary", mat="plastic", tris=2400, res=128)
        beak = SD.ellipsoid(0.55, 0.2, 0.55, (0, 3.05, -2.65)) | SD.ellipsoid(0.48, 0.14, 0.45, (0, 2.85, -2.55))
        H.piece("Beak", "Chassis", beak, col="secondary", mat="plastic", tris=600, role="detail", pri=1.2)
        H.eyes("Chassis", (0.55, 3.55, -2.3), 0.16, col="pupil", pupil=None, look=(0.6, 0.1, -1.0))
        seat_y, seat_z = 2.0, 0.6
        sw_y, sw_z = 2.75, -0.45
    seat = K.seat_mesh((0, seat_y, seat_z), w=0.9, d=0.8, back=0.85)
    piece(H, "Seat", "Chassis", seat, col="darker", mat="cloth", role="seat", pri=1.0)
    sw = K.steering_mesh((0, sw_y, sw_z), r=0.28, tilt=55, col_len=0.4)
    piece(H, "Steering", "Chassis", sw, col="darker", mat="plastic", role="detail", pri=1.3)
    K.lamp_pair(H, "Headlight", "Chassis", (0.9, 0.85, -2.85), r=0.15, depth=0.1)
    _rig_common(H, wheels, steer, 3.0, 6.5, "Seat", (0, seat_y + 0.1, seat_z), (0.9, 0.2, 0.8), (0, 1.5, -3.6), (0, 0.8, 3.0), sym=5, attack="honk", scale=1.85)
    return H


@hero("banana car", FAM)
def banana_car():
    return _novelty("banana car", "banana", pv("#F7D84A", "#5A3A1E"))


@hero("hot dog car", FAM)
def hot_dog_car():
    return _novelty("hot dog car", "hotdog", pv("#B5442B", "#F2C200"))


@hero("bathtub car", FAM)
def bathtub_car():
    return _novelty("bathtub car", "bathtub", pv("#F5F5F5", "#E9C46A"))


@hero("couch car", FAM)
def couch_car():
    return _novelty("couch car", "couch", pv("#6D597A", "#E5989B"))


@hero("shoe car", FAM)
def shoe_car():
    return _novelty("shoe car", "shoe", pv("#E63946", "#1D3557"))


@hero("duck car", FAM)
def duck_car():
    return _novelty("duck car", "duck", pv("#FFD60A", "#F77F00"))


# word -> hero rules (tools/meshgen/heroes/map.py); K.LAND = Vehicle words (+ toy / robot vehicles)
L = K.LAND
MAP = [
    ("car", "car, cars, sedan, sedans, automobile, motorcar, vehicle, stock car, toy car, remote control car, car pile up, amphibious car, ghost car, "
            "!cable car, !roller coaster car, !rail car, !cloud car", L),
    ("taxi", "taxi, taxis, cab, taxicab, cabbie car, !sky taxi", L),
    ("police car", "police car, cop car, patrol car, squad car, police cruiser", L),
    ("sports car", "sports car, supercar, hypercar, hovercar, rocket car, dinosaur car, shark car, coupe, time machine", L),
    ("muscle car", "muscle car, hot rod, hotrod, drag racer, dragster", L),
    ("race car", "race car, racecar, racing car, formula one, f1 car, indy car", L),
    ("convertible", "convertible, cabriolet, roadster, lowrider", L),
    ("limousine", "limousine, limo, hearse", L),
    ("station wagon", "station wagon, estate car", L),
    ("rally car", "rally car, rallycar", L),
    ("off roader", "off roader, offroader, jeep, 4x4, military truck, scout car, safari truck", L),
    ("suv", "suv, crossover", L),
    ("go kart", "go kart, gokart, kart, soapbox car, cardboard box car, go cart, rainbow road ride", L),
    ("golf cart", "golf cart, golf buggy, baggage cart, milk float", L),
    ("dune buggy", "dune buggy, beach buggy, buggy, lunar rover, mars rover, moon buggy, rover, land yacht, sand yacht", L),
    ("bumper car", "bumper car, dodgem, teacup ride", L),
    ("bubble car", "bubble car, clown car, three wheeler, giant hamster ball, hamster ball, cupcake car, snail mobile, microcar", L),
    ("banana car", "banana car", L),
    ("hot dog car", "hot dog car, hotdog car", L),
    ("bathtub car", "bathtub car", L),
    ("couch car", "couch car, bed car, sofa car", L),
    ("shoe car", "shoe car, sneaker car", L),
    ("duck car", "duck car", L),
]
