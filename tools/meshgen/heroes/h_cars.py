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
    L=9.0,            # bumper to bumper
    W=3.7,            # body width
    wr=0.68,          # wheel radius
    ww=0.62,          # tyre width
    wr_rear=None,     # bigger rear wheels (muscle / dragster)
    ww_rear=None,
    track_in=0.12,    # wheel inset from the body side
    wb=5.6,           # wheelbase
    axle_off=0.15,    # wheelbase centre offset (+ = rearward)
    sill=0.5,         # body bottom between the arches
    belt=2.05,        # beltline (window sill)
    hood=1.68,        # hood height at the front edge
    nose=1.25,        # height of the nose face top (above it the hood edge rounds)
    deck=2.0,         # trunk lid height
    ws=-1.2,          # windshield base z
    roof0=-0.15,      # roof front z
    roof1=1.6,        # roof rear z
    back=2.55,        # rear window base z
    roofy=3.05,       # roof height
    cabin="sedan",    # sedan | open | none | fastback | wagon | van
    tumble=0.2,       # greenhouse tumblehome
    gw=0.86,          # greenhouse width factor
    nose_taper=0.1,
    crown=0.08,
    rim="alloy",
    spokes=5,
    rim_col="metal",
    knobby=0.0,
    lamps="rect",     # rect | round | pop
    grille="wide",    # wide | split | none | jeep
    bumper="body",    # body | chrome | black | bull
    exhaust=1,        # 0, 1, 2 (twin)
    spoiler=False,
    scoop=False,
    stripes=False,
    seats=2,          # front seats (rear bench added for sedans)
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
    preview={},
)


def _profile(P):
    """Side profile (z, y) of the lower body with the wheel arches cut in."""
    L, wr, sill = P["L"], P["wr"], P["sill"]
    zn, zt = -L / 2, L / 2
    zc = P["axle_off"]
    zf, zr = zc - P["wb"] / 2, zc + P["wb"] / 2
    wrr = P["wr_rear"] or wr
    belt, hood, nose, deck = P["belt"], P["hood"], P["nose"], P["deck"]
    ybf = sill + 0.1
    pts = []
    radii = []

    def add(p, r=0.0):
        pts.append(p)
        radii.append(r)

    add((zn + 0.35, ybf), 0.25)
    add((zn, ybf + 0.35), 0.15)
    add((zn - 0.05, nose), 0.25)
    add((zn + 0.35, hood), 0.3)
    add((P["ws"], belt), 0.25)
    if P["cabin"] in ("sedan", "open", "none", "fastback"):
        add((P["back"], belt - 0.02), 0.2)
        add((zt - 0.35, deck), 0.3)
    else:
        add((zt - 0.5, belt - 0.02), 0.3)
        add((zt - 0.05, deck), 0.2)
    add((zt, sill + 0.65), 0.2)
    add((zt - 0.25, sill + 0.05), 0.15)

    def arch(zc_, rr, ra):
        yw = rr
        dy = yw - sill
        dz = math.sqrt(max(ra * ra - dy * dy, 0.01))
        a0 = math.atan2(-dy, dz)
        a1 = math.pi - a0
        for k in range(15):
            a = a0 + (a1 - a0) * k / 14
            add((zc_ + ra * math.cos(a), yw + ra * math.sin(a)), 0.0)

    arch(zr, wrr, wrr + 0.14)
    arch(zf, wr, wr + 0.14)
    return np.array(pts), radii


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
    belt, roofy = P["belt"], P["roofy"]
    hw = W / 2

    # ------------------------------------------------------------------ skeleton
    H.bone("Chassis", "Body", (0, wr + 0.1, (zf + zr) / 2))
    xw = hw - P["track_in"] - ww / 2 + 0.05
    xwr = hw - P["track_in"] - wwr / 2 + 0.05
    H.bone("SteerFR", "Body", (xw, wr, zf))
    H.bone("SteerFL", "Body", (-xw, wr, zf))
    H.bone("WheelFR", "SteerFR", (xw, wr, zf))
    H.bone("WheelFL", "SteerFL", (-xw, wr, zf))
    H.bone("WheelBR", "Body", (xwr, wrr, zr))
    H.bone("WheelBL", "Body", (-xwr, wrr, zr))

    # ------------------------------------------------------------------ body warp
    tz0, tz1 = zn + 1.3, zt - 1.0

    def bodywarp(V, crown=P["crown"], tum=0.05, top=belt):
        x, y, z = V[:, 0], V[:, 1], V[:, 2]
        sz = 1 - P["nose_taper"] * np.clip((tz0 - z) / 1.3, 0, 1) ** 2 - 0.06 * np.clip((z - tz1) / 1.0, 0, 1) ** 2
        sy = 1 - tum * np.clip((y - (top - 0.7)) / 0.7, 0, 1) - 0.05 * np.clip((P["sill"] + 0.3 - y) / 0.3, 0, 1)
        x2 = x * sz * sy
        cr = crown * np.clip(1 - (x / hw) ** 2, 0, 1) * np.clip((y - (top - 0.45)) / 0.45, 0, 1)
        return np.column_stack([x2, y + cr, z])

    def surf_x(y, z, off=0.0):
        """x of the body side surface (right) at (y, z) plus an outward offset."""
        v = bodywarp(np.array([[hw, y, z]], float))
        return float(v[0, 0]) + off

    prof, radii = _profile(P)
    prof = round_poly(prof, radii, seg=3)
    body = warp(extrude(prof, W, bevel=0.14, seg=3), bodywarp)
    piece(H, "Chassis", "Chassis", body, col="primary", mat="metal", role="body", pri=0.5)

    # skin panels (doors in a second colour, stripes) follow the body: same profile region, slightly wider, same warp
    if P["doors_col"]:
        dz0, dz1 = P["ws"] + 0.1, P["back"] - 0.45
        door = np.array([(dz0, P["sill"] + 0.32), (dz1, P["sill"] + 0.32), (dz1, belt - 0.12), (dz0, belt - 0.12)])
        dm_ = warp(extrude(round_poly(door, 0.12, 2), W + 0.05, bevel=0.03, seg=1), bodywarp)
        piece(H, "Doors", "Chassis", dm_, col=P["doors_col"], mat="metal", role="detail", pri=1.6)
    if P["stripes"]:
        top = []
        for k in range(30):
            z = zn + 0.3 + (L - 0.6) * k / 29
            top.append(z)
        # stripe band hugging the hood -> roof -> deck: sample the body top by casting down the profile
        def top_y(z):
            ys = []
            for i in range(len(prof)):
                a, b = prof[i], prof[(i + 1) % len(prof)]
                if (a[0] - z) * (b[0] - z) <= 0 and abs(b[0] - a[0]) > 1e-9:
                    ys.append(a[1] + (b[1] - a[1]) * (z - a[0]) / (b[0] - a[0]))
            return max(ys) if ys else belt

        upper = [(z, top_y(z) + 0.035) for z in top]
        lower = [(z, top_y(z) - 0.12) for z in top[::-1]]
        poly = np.array(upper + lower)
        s = merge(*(xf(extrude(poly, 0.32, bevel=0.02, seg=1), (sx, 0, 0)) for sx in (-0.3, 0.3)))
        s = warp(s, bodywarp)
        piece(H, "Stripes", "Chassis", s, col="secondary", mat="metal", role="detail", pri=1.7)

    # ------------------------------------------------------------------ greenhouse: glass + roof + pillars
    xg = hw * P["gw"]
    cab = P["cabin"]
    seat_y = belt - 0.25
    if cab in ("sedan", "fastback", "wagon", "van"):
        r0, r1 = P["roof0"], P["roof1"]
        gpoly = np.array([(P["ws"] - 0.05, belt - 0.08), (r0, roofy), (r1, roofy), (P["back"] + 0.05, belt - 0.08)])
        gpoly = round_poly(gpoly, [0.0, 0.2, 0.2, 0.0], 3)
        tum = P["tumble"]

        def gwarp(V):
            x, y, z = V[:, 0], V[:, 1], V[:, 2]
            t = np.clip((y - belt) / (roofy - belt), 0, 1)
            return np.column_stack([x * (1 - tum * t), y + 0.05 * np.clip(1 - (x / xg) ** 2, 0, 1) * t ** 4, z])

        glass = warp(extrude(gpoly, 2 * xg, bevel=0.1, seg=2), gwarp)
        piece(H, "Glass", "Chassis", glass, col="glass", mat="glass", role="window", pri=0.8, tr=0.22, ao=False)
        xt = xg * (1 - tum)
        # roof skin (proud) + pillars
        rpoly = np.array([(r0 - 0.06, roofy - 0.12), (r0 + 0.12, roofy + 0.07), (r1 - 0.12, roofy + 0.07), (r1 + 0.06, roofy - 0.12)])
        roof = warp(extrude(round_poly(rpoly, 0.05, 2), 2 * xt + 0.12, bevel=0.06, seg=2),
                    lambda V: np.column_stack([V[:, 0], V[:, 1] + 0.05 * np.clip(1 - (V[:, 0] / (xt + 0.06)) ** 2, 0, 1), V[:, 2]]))
        pil = []
        pw = 0.16
        for s in (-1, 1):
            a0 = np.array([s * (xg + 0.02), belt - 0.02, P["ws"] + 0.08])
            a1 = np.array([s * (xt + 0.03), roofy - 0.02, r0 + 0.06])
            pil.append(bar(a0, a1, pw, pw * 0.8, r=0.04))
            zb = (P["ws"] + P["back"]) / 2 + 0.25 if cab != "van" else r0 + 1.0
            b0 = np.array([s * (xg + 0.03), belt - 0.02, zb])
            b1 = np.array([s * (xt + 0.035), roofy - 0.03, zb])
            pil.append(bar(b0, b1, pw * 1.3, pw * 0.8, r=0.04))
            for zb2 in P["extra_b"]:
                pil.append(bar((s * (xg + 0.03), belt - 0.02, zb2), (s * (xt + 0.035), roofy - 0.03, zb2), pw * 1.3, pw * 0.8, r=0.04))
            c0 = np.array([s * (xg + 0.02), belt - 0.02, P["back"] - 0.02])
            c1 = np.array([s * (xt + 0.03), roofy - 0.02, r1 - 0.04])
            pil.append(bar(c0, c1, pw * (2.2 if cab == "fastback" else 1.6), pw * 0.8, r=0.04))
        frame = merge(roof, *pil)
        piece(H, "Roof", "Chassis", frame, col="primary", mat="metal", role="body", pri=0.9)
        # belt trim (chrome window sill)
        trim = merge(*(bar((s * (xg + 0.035), belt + 0.0, P["ws"] + 0.1), (s * (xg + 0.035), belt + 0.0, P["back"] - 0.05), 0.06, 0.05, r=0.02)
                       for s in (-1, 1)))
        piece(H, "BeltTrim", "Chassis", trim, col="metal", mat="metal", role="detail", pri=2.2)
    elif cab == "open":
        # windshield frame + glass only
        a = np.array([0, belt - 0.05, P["ws"] + 0.05])
        top = np.array([0, belt + 0.85, P["ws"] + 0.45])
        wsg = bar(a + (0, 0.42, 0.2), a + (0, 0.42, 0.2) + (0, 0, 0.001), 2 * xg - 0.25, 0.85, r=0.03)
        d = top - a
        ang = math.degrees(math.atan2(d[2], d[1]))
        wsg = box((2 * xg - 0.25, 0.9, 0.05), (0, 0, 0), r=0.02)
        wsg = xf(xf(wsg, (0, 0.45, 0)), a, r=(ang, 0, 0))
        piece(H, "Glass", "Chassis", wsg, col="glass", mat="glass", role="window", pri=0.8, tr=0.22, ao=False)
        fr = []
        for s in (-1, 1):
            fr.append(bar(a + (s * (xg - 0.1), 0, 0), top + (s * (xg - 0.1), 0, 0), 0.1, 0.1, r=0.03))
        fr.append(bar(top + (-(xg - 0.1), 0, 0), top + ((xg - 0.1), 0, 0), 0.1, 0.1, r=0.03))
        frm = merge(*fr)
        if P["rollbar"]:
            zb = P["back"] - 0.6
            rb = [rod((s * (xg - 0.15), belt - 0.1, zb), (s * (xg - 0.25), belt + 1.1, zb - 0.1), 0.08) for s in (-1, 1)]
            rb.append(rod((-(xg - 0.25), belt + 1.1, zb - 0.1), ((xg - 0.25), belt + 1.1, zb - 0.1), 0.08))
            rb += [rod((s * (xg - 0.25), belt + 1.1, zb - 0.1), (s * (xg - 0.2), belt - 0.05, zb + 1.1), 0.07) for s in (-1, 1)]
            frm = merge(frm, *rb)
        piece(H, "Roof", "Chassis", frm, col="metal" if not P["rollbar"] else "dark", mat="metal", role="detail", pri=0.9)
        # cockpit tub (dark interior) sunk into the top so the open cabin reads
        tub = box((2 * xg - 0.1, 0.12, P["back"] - P["ws"] - 0.3), (0, belt + 0.0, (P["ws"] + P["back"]) / 2 + 0.05), r=0.05)
        piece(H, "Cockpit", "Chassis", tub, col="darker", mat="cloth", role="detail", pri=1.3)
        seat_y = belt + 0.05

    # ------------------------------------------------------------------ interior
    zs = P["ws"] + 1.35 if cab != "van" else P["ws"] + 1.2
    sx = xg * 0.47
    seats = [K.seat_mesh((-sx, seat_y, zs), w=0.85, d=0.8, back=1.0 if cab != "open" else 0.85), K.seat_mesh((sx, seat_y, zs), w=0.85, d=0.8, back=1.0 if cab != "open" else 0.85)]
    piece(H, "Seat", "Chassis", seats[0], col=P["seat_col"], mat="cloth", role="seat", pri=1.1)
    piece(H, "Seat2", "Chassis", seats[1], col=P["seat_col"], mat="cloth", role="seat", pri=1.8)
    dash = box((2 * xg - 0.3, 0.3, 0.45), (0, belt + 0.05, P["ws"] + 0.45), r=0.08)
    sw = K.steering_mesh((-sx, belt + 0.35, P["ws"] + 0.75), r=0.26, tilt=62, col_len=0.4)
    piece(H, "Dash", "Chassis", merge(dash, sw), col="darker", mat="plastic", role="detail", pri=1.5)

    # ------------------------------------------------------------------ front: lamps, grille, bumper
    ylamp = P["nose"] - 0.16
    xl = hw - 0.55
    if P["lamps"] == "round":
        hl = lamp((xl, ylamp, zn - 0.08), 0.24, 0.16)
        bz = bezel((xl, ylamp, zn - 0.06), 0.24, 0.12)
    else:
        hl = K.lamp((xl - 0.05, ylamp, zn - 0.06), 0, 0.2, shape="rect", w=0.75, h=0.26)
        hl = warp(hl, lambda V: np.column_stack([V[:, 0], V[:, 1], V[:, 2] + 0.12 * ((V[:, 0] - (xl - 0.45)) / 0.75) ** 2]))
        bz = None
    mpiece(H, "Headlight#", "Chassis", hl, col=LENS, mat="glass", role="light", pri=1.4, ao=False)
    chrome = []
    if bz is not None:
        chrome.append(bz)
        chrome.append(mirror(bz))
    gw = (xl - 0.45) * 2 if P["lamps"] != "round" else (xl - 0.38) * 2
    if P["grille"] != "none":
        gh = 0.42 if P["grille"] != "jeep" else 0.75
        gy = ylamp - 0.05 if P["grille"] != "jeep" else ylamp + 0.0
        g = box((gw, gh, 0.1), (0, gy, zn - 0.0), r=0.06)
        piece(H, "Grille", "Chassis", g, col="darker", mat="metal", role="detail", pri=1.6)
        if P["grille"] == "jeep":
            for k in range(7):
                gx = -gw / 2 + gw * (k + 0.5) / 7
                chrome.append(K.cbox((0.07, gh * 0.85, 0.06), (gx, gy, zn - 0.06), c=0.02))
        else:
            for k in range(3):
                chrome.append(K.cbox((gw * 0.94, 0.045, 0.05), (0, gy - gh * 0.3 + gh * 0.3 * k, zn - 0.06), c=0.015))
            chrome.append(box((gw + 0.08, gh + 0.08, 0.04), (0, gy, zn + 0.02), r=0.05))
    by = P["sill"] + 0.3
    if P["bumper"] == "body":
        fb = box((W * 0.96, 0.34, 0.4), (0, by, zn + 0.12), r=0.15, seg=2)
        rb = box((W * 0.96, 0.34, 0.4), (0, by, zt - 0.12), r=0.15, seg=2)
        bcol, bmat = "primary", "metal"
        lower = box((W * 0.8, 0.12, 0.3), (0, by - 0.22, zn + 0.2), r=0.04)
        chrome_b = None
    else:
        fb = box((W * 0.98, 0.3, 0.32), (0, by, zn - 0.08), r=0.1, seg=2)
        rb = box((W * 0.98, 0.3, 0.32), (0, by, zt + 0.08), r=0.1, seg=2)
        bcol, bmat = ("metal", "metal") if P["bumper"] == "chrome" else ("dark", "plastic")
        lower = None
    piece(H, "Bumpers", "Chassis", merge(fb, rb), col=bcol, mat=bmat, role="detail", pri=1.2)
    if P["bumper"] == "bull":
        bb = []
        for s in (-1, 1):
            bb.append(rod((s * 0.7, by - 0.1, zn - 0.2), (s * 0.7, P["nose"] + 0.15, zn - 0.35), 0.07))
        bb.append(rod((-0.7, P["nose"] + 0.15, zn - 0.35), (0.7, P["nose"] + 0.15, zn - 0.35), 0.07, ext=0.07))
        bb.append(rod((-0.75, by + 0.25, zn - 0.3), (0.75, by + 0.25, zn - 0.3), 0.06))
        bb.append(box((1.7, 0.26, 0.18), (0, by, zn - 0.25), r=0.06))
        piece(H, "PushBar", "Chassis", merge(*bb), col="darker", mat="metal", role="detail", pri=1.5)

    # ------------------------------------------------------------------ rear lamps, plate, exhaust
    yt = P["deck"] - 0.28
    tl = K.lamp((hw - 0.5, yt, zt - 0.02), 0, 0.14, axis="+z", shape="rect", w=0.65, h=0.24)
    mpiece(H, "Taillight#", "Chassis", tl, col=RED_L, mat="glass", role="light", pri=1.5, ao=False)
    plates = merge(box((0.8, 0.28, 0.05), (0, by + 0.0, zt + 0.06 + (0.12 if P["bumper"] != "body" else 0.0)), r=0.03),
                   box((0.8, 0.22, 0.05), (0, by + 0.0, zn - 0.06 - (0.12 if P["bumper"] != "body" else 0.0)), r=0.03))
    piece(H, "Plates", "Chassis", plates, col="white", mat="plastic", role="detail", pri=2.4)
    dark = []
    for k in range(P["exhaust"]):
        ex = hw - 0.7 - 0.3 * k
        chrome.append(K.tube_ring(0.1, 0.07, 0.4, axis="z", pos=(ex, P["sill"] + 0.05, zt + 0.0)))
        if P["exhaust"] == 2:
            chrome.append(K.tube_ring(0.1, 0.07, 0.4, axis="z", pos=(-ex, P["sill"] + 0.05, zt + 0.0)))
    if P["exhaust"] == 2:
        pass
    # mirrors
    mz = P["ws"] + 0.25
    mx = surf_x(belt - 0.1, mz)
    mir = merge(bar((mx - 0.05, belt - 0.05, mz), (mx + 0.25, belt + 0.05, mz + 0.05), 0.08, 0.06, r=0.02),
                box((0.22, 0.24, 0.32), (mx + 0.3, belt + 0.12, mz + 0.06), r=0.08, seg=2))
    mpiece(H, "Mirror#", "Chassis", mir, col="primary", mat="metal", role="detail", pri=2.0)
    # door seams + handles (stand proud of the skin)
    if cab in ("sedan", "fastback", "wagon", "van", "open"):
        zs_list = [P["ws"] + 0.15, (P["ws"] + P["back"]) / 2 + 0.25] + ([P["back"] - 0.3] if cab in ("sedan", "wagon") else [])
        off = 0.035 if not P["doors_col"] else 0.06
        for s in (1, -1):
            for z in zs_list:
                yb, yt_ = P["sill"] + 0.18, belt - 0.12
                dark.append(bar((s * surf_x(yb, z, off), yb, z), (s * surf_x(yt_, z, off), yt_, z), 0.03, 0.04, r=0.01))
            for z in zs_list[:-1]:
                hz = z + 0.55
                hy = belt - 0.3
                chrome.append(K.cbox((0.05, 0.07, 0.3), (s * surf_x(hy, hz, off + 0.01), hy, hz), c=0.02))
    if P["sidepipes"]:
        for s in (-1, 1):
            chrome.append(rod((s * (hw + 0.08), P["sill"] + 0.1, zf + 1.0), (s * (hw + 0.08), P["sill"] + 0.1, zr - 1.0), 0.09, ext=0.0))
    if dark:
        piece(H, "Seams", "Chassis", merge(*dark), col="darker", mat="plastic", role="detail", pri=2.6)

    # ------------------------------------------------------------------ extras
    if P["spoiler"]:
        sy = P["deck"] + 0.45
        sp = merge(box((W * 0.92, 0.07, 0.55), (0, sy, zt - 0.35), r=0.03, rot_=(-8, 0, 0)),
                   box((0.08, 0.5, 0.4), (W * 0.32, sy - 0.25, zt - 0.38), r=0.03), box((0.08, 0.5, 0.4), (-W * 0.32, sy - 0.25, zt - 0.38), r=0.03),
                   box((0.06, 0.25, 0.6), (W * 0.46, sy + 0.05, zt - 0.35), r=0.02), box((0.06, 0.25, 0.6), (-W * 0.46, sy + 0.05, zt - 0.35), r=0.02))
        piece(H, "Spoiler", "Chassis", sp, col="secondary", mat="metal", role="detail", pri=1.3)
    if P["scoop"]:
        sc = K.box((0.9, 0.3, 1.2), (0, P["hood"] + 0.2, (zn + P["ws"]) / 2 + 0.3), r=0.08, seg=2)
        sc = merge(sc, box((0.7, 0.18, 0.06), (0, P["hood"] + 0.22, (zn + P["ws"]) / 2 - 0.3), r=0.03))
        piece(H, "Scoop", "Chassis", sc, col="darker", mat="metal", role="detail", pri=1.4)
    if P["lightbar"]:
        ly = roofy + 0.15
        base = box((2.0, 0.12, 0.42), (0, ly, (P["roof0"] + P["roof1"]) / 2 - 0.2), r=0.04)
        piece(H, "LightBar", "Chassis", base, col="darker", mat="plastic", role="detail", pri=1.3)
        lr = box((0.85, 0.22, 0.34), (0.48, ly + 0.15, (P["roof0"] + P["roof1"]) / 2 - 0.2), r=0.08, seg=2)
        piece(H, "SirenRed", "Chassis", lr, col=RED_L, mat="glass", role="light", pri=1.4, ao=False)
        piece(H, "SirenBlue", "Chassis", mirror(lr), col=BLUE_L, mat="glass", role="light", pri=1.4, ao=False)
    if P["taxi"]:
        ty = roofy + 0.1
        zc = (P["roof0"] + P["roof1"]) / 2
        sign = extrude(round_poly(np.array([(-0.75, 0), (-0.55, 0.42), (0.55, 0.42), (0.75, 0)]), [0, 0.1, 0.1, 0], 2), 0.32, bevel=0.04, axis="z")
        sign = xf(sign, (0, ty, zc), r=(0, 90, 0))
        piece(H, "TaxiSign", "Chassis", sign, col="white", mat="plastic", role="detail", pri=1.3)
        # checker band along both sides
        chk = []
        for s in (1, -1):
            for k in range(12):
                z = P["ws"] + 0.1 + k * 0.31
                for row in (0, 1):
                    if (k + row) % 2:
                        continue
                    y = belt - 0.45 - row * 0.2
                    chk.append(K.cbox((0.04, 0.19, 0.3), (s * surf_x(y, z + 0.15, 0.03), y, z + 0.15), c=0.01))
        piece(H, "Checker", "Chassis", merge(*chk), col="secondary", mat="plastic", role="detail", pri=1.9)
    if P["spare"]:
        sw_ = K.tyre(0.62, 0.42, ri=0.36, segs=24, knobby=P["knobby"])
        sw_ = merge(sw_, K.rim(0.36, 0.42, "steel", segs=18))
        sw_ = xf(sw_, (0, P["deck"] - 0.25, zt + 0.25), r=(0, 90, 0))
        piece(H, "Spare", "Chassis", sw_, col="tyre", mat="rubber", role="detail", pri=1.6)
    if P["flares"]:
        fl = []
        for z, rr in ((zf, wr), (zr, wrr)):
            arc = []
            ra = rr + 0.22
            for k in range(13):
                a = math.radians(10 + 160 * k / 12)
                arc.append((z + ra * math.cos(a), rr + ra * math.sin(a)))
            for k in range(12, -1, -1):
                a = math.radians(10 + 160 * k / 12)
                arc.append((z + (ra - 0.2) * math.cos(a), rr + (ra - 0.2) * math.sin(a)))
            for s in (-1, 1):
                fl.append(xf(extrude(np.array(arc), 0.35, bevel=0.05, seg=1), (s * (hw - 0.05), 0, 0)))
        piece(H, "Flares", "Chassis", merge(*fl), col="darker", mat="plastic", role="detail", pri=1.5)
    if P["roofrack"]:
        rr_ = []
        for s in (-1, 1):
            rr_.append(rod((s * (xg * (1 - P["tumble"]) - 0.15), roofy + 0.2, P["roof0"] + 0.2), (s * (xg * (1 - P["tumble"]) - 0.15), roofy + 0.2, P["roof1"] - 0.2), 0.05))
        for z in np.linspace(P["roof0"] + 0.4, P["roof1"] - 0.4, 3):
            rr_.append(rod((-(xg * (1 - P["tumble"]) - 0.15), roofy + 0.2, z), ((xg * (1 - P["tumble"]) - 0.15), roofy + 0.2, z), 0.04))
        piece(H, "RoofRack", "Chassis", merge(*rr_), col="darker", mat="metal", role="detail", pri=1.8)
    if P["boot"]:
        bt = box((2 * xg - 0.2, 0.42, 0.9), (0, belt + 0.12, P["back"] - 0.2), r=0.18, seg=2)
        piece(H, "SoftTop", "Chassis", bt, col="secondary", mat="cloth", role="detail", pri=1.4)
    if P["roof_lights"]:
        rl = [box((2 * xg * (1 - P["tumble"]) - 0.2, 0.1, 0.12), (0, roofy + 0.12, P["roof0"] + 0.15), r=0.03)]
        lens = []
        for k in range(4):
            x = -0.75 + 0.5 * k
            rl.append(box((0.36, 0.34, 0.16), (x, roofy + 0.3, P["roof0"] + 0.05), r=0.06))
            lens.append(K.lamp((x, roofy + 0.3, P["roof0"] - 0.04), 0.13, 0.06))
        piece(H, "RoofLamps", "Chassis", merge(*rl), col="darker", mat="plastic", role="detail", pri=1.6)
        piece(H, "RoofLens", "Chassis", merge(*lens), col=LENS, mat="glass", role="light", pri=1.9, ao=False)
    if P["mudflaps"]:
        mf = []
        for s_ in (-1, 1):
            for z in (zf + wr + 0.25, zr + wrr + 0.25):
                mf.append(box((0.55, 0.6, 0.05), (s_ * xw, 0.42, z), r=0.03))
        piece(H, "Mudflaps", "Chassis", merge(*mf), col="darker", mat="rubber", role="detail", pri=2.2)
    if chrome:
        piece(H, "Chrome", "Chassis", merge(*chrome), col="metal", mat="metal", role="detail", pri=2.0)

    # ------------------------------------------------------------------ wheels
    for nm, bone, pos, rr, w_, side in (("WheelFR", "WheelFR", (xw, wr, zf), wr, ww, 1), ("WheelFL", "WheelFL", (-xw, wr, zf), wr, ww, -1),
                                        ("WheelBR", "WheelBR", (xwr, wrr, zr), wrr, wwr, 1), ("WheelBL", "WheelBL", (-xwr, wrr, zr), wrr, wwr, -1)):
        K.wheel_pieces(H, nm, bone, pos, rr, w_, style=P["rim"], spokes=P["spokes"], knobby=P["knobby"], side=side, rim_col=P["rim_col"])

    # ------------------------------------------------------------------ rig
    seat_pos = (-sx, seat_y + 0.1, zs)
    K.mount(H, "Seat", seat_pos, (0.85, 0.2, 0.8), "Chassis")
    H.socket("head", (0, roofy + 0.3, 0), "Chassis")
    H.socket("mouth", (0, P["nose"], zn - 0.3), "Chassis")
    H.socket("exhaust", (hw - 0.7, P["sill"] + 0.05, zt + 0.3), "Chassis")
    H.rig.update({"head": "Chassis"})
    K.vehicle_clips(H, [("WheelFR", wr), ("WheelFL", wr), ("WheelBR", wrr), ("WheelBL", wrr)], susp="Chassis", height=roofy, length=L,
                    sym=P["spokes"] if P["rim"] in ("alloy", "mag") else 8, steer=("SteerFR", "SteerFL"),
                    attack=P.get("attack", "ram"))
    return H


def pv(p, s, **kw):
    d = {"primary": p, "secondary": s, "glass": "#33414F", "darker": "#24262B"}
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
    return _car("police car", lightbar=True, doors_col="secondary", bumper="bull", rim="steel", preview=pv("#1B2A49", "#F5F5F5"))


@hero("sports car", FAM)
def sports_car():
    return _car("sports car", L=9.2, W=3.95, wr=0.72, ww=0.7, wr_rear=0.74, ww_rear=0.82, wb=5.5, axle_off=0.2, sill=0.4, belt=1.55, hood=1.2,
                nose=0.9, deck=1.55, ws=-0.75, roof0=0.35, roof1=1.25, back=3.15, roofy=2.3, cabin="fastback", gw=0.8, tumble=0.26,
                nose_taper=0.16, spoiler=True, exhaust=2, grille="none", bumper="body", spokes=5, rim_col="darker",
                preview=pv("#FFC300", "#1A1A1A"))


@hero("muscle car", FAM)
def muscle_car():
    return _car("muscle car", L=9.6, W=3.9, wr=0.7, ww=0.64, wr_rear=0.8, ww_rear=0.86, wb=5.9, axle_off=0.15, sill=0.48, belt=1.8, hood=1.62,
                nose=1.25, deck=1.78, ws=-0.55, roof0=0.45, roof1=1.55, back=2.85, roofy=2.7, cabin="fastback", gw=0.82, tumble=0.22,
                nose_taper=0.04, scoop=True, stripes=True, exhaust=2, lamps="round", grille="wide", bumper="chrome", rim="mag", spokes=6,
                preview=pv("#1F3A93", "#F2F2F2"))


@hero("convertible", FAM)
def convertible():
    return _car("convertible", cabin="open", boot=True, L=9.2, belt=1.85, hood=1.6, deck=1.8, ws=-0.9, back=2.6, bumper="chrome", lamps="round",
                rim="wire", spokes=24, seat_col=[0.82, 0.72, 0.55], preview=pv("#D7263D", "#F2E8CF"))


@hero("limousine", FAM)
def limousine():
    return _car("limousine", L=14.0, wb=10.2, axle_off=0.2, ws=-3.4, roof0=-2.4, roof1=4.2, back=5.0, extra_b=(-0.2, 2.0), bumper="chrome",
                tumble=0.16, rim="steel", preview=pv("#151515", "#C0C0C0", glass="#151A20"))


@hero("station wagon", FAM)
def station_wagon():
    return _car("station wagon", cabin="wagon", L=9.4, ws=-1.3, roof0=-0.3, roof1=3.65, back=4.1, deck=2.0, roofrack=True, doors_col="secondary",
                bumper="chrome", rim="steel", preview=pv("#8A6E4B", "#E8DCC2"))


@hero("rally car", FAM)
def rally_car():
    return _car("rally car", cabin="wagon", L=8.4, wb=5.2, wr=0.72, ww=0.68, sill=0.62, belt=2.0, hood=1.7, nose=1.3, deck=2.1, ws=-1.2,
                roof0=-0.25, roof1=3.0, back=3.55, knobby=0.03, roof_lights=True, mudflaps=True, spoiler=True, stripes=True, rim="alloy",
                spokes=6, rim_col="white", bumper="black", preview=pv("#1E5BC6", "#F5F5F5"))


@hero("off roader", FAM)
def off_roader():
    return _car("off roader", cabin="open", rollbar=True, L=8.2, W=3.8, wb=5.0, axle_off=0.1, wr=0.9, ww=0.75, track_in=-0.05, sill=0.95,
                belt=2.35, hood=2.2, nose=1.95, deck=2.3, ws=-0.95, back=3.1, nose_taper=0.02, crown=0.03, lamps="round", grille="jeep",
                bumper="black", flares=True, spare=True, knobby=0.07, rim="steel", exhaust=1, preview=pv("#4B5D3A", "#2A2A2A"))


@hero("suv", FAM)
def suv():
    return _car("suv", cabin="wagon", L=9.4, W=3.9, wr=0.82, ww=0.7, wb=5.8, sill=0.75, belt=2.35, hood=2.1, nose=1.7, deck=2.4, ws=-1.2,
                roof0=-0.25, roof1=3.7, back=4.15, roofy=3.45, roofrack=True, bumper="black", flares=True, rim="alloy", spokes=6,
                preview=pv("#2E3B4E", "#9AA3AD"))


# ==================================================================================================== special cars
def _rig_common(H, wheels, steer, height, length, seat_part, seat_pos, seat_size, nose, tail, sym=5, attack="ram", **kw):
    K.mount(H, seat_part, seat_pos, seat_size, "Chassis")
    H.socket("head", (0, height + 0.3, 0), "Chassis")
    H.socket("mouth", nose, "Chassis")
    H.socket("exhaust", tail, "Chassis")
    H.rig.update({"head": "Chassis"})
    K.vehicle_clips(H, wheels, susp="Chassis", height=height, length=length, sym=sym, steer=steer, attack=attack, **kw)


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
    _rig_common(H, wheels, steer, 2.0, 9.0, "Seat", (0, 1.1, -0.35), (0.7, 0.2, 0.7), (0, 0.5, -5.2), (0, 0.8, 3.7), sym=10)
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
    seat = K.seat_mesh((0, 0.55, 0.45), w=0.8, d=0.7, back=0.95, recline=18)
    piece(H, "Seat", "Chassis", seat, col="secondary", mat="plastic", role="seat", pri=0.9)
    sw = K.steering_mesh((0, 1.05, -0.55), r=0.24, tilt=55, col_len=0.0)
    col = rod((0, 1.0, -0.6), (0, 0.32, -1.35), 0.04, segs=8)
    piece(H, "Steering", "Chassis", merge(sw, col), col="darker", mat="plastic", role="detail", pri=1.3)
    eng = merge(K.box((0.55, 0.5, 0.55), (0.55, 0.65, 1.55), r=0.06), cyl(0.5, 0.18, (0.55, 1.0, 1.55), "y", segs=12),
                K.tube_ring(0.07, 0.05, 0.6, axis="z", pos=(0.85, 0.65, 2.05)))
    piece(H, "Engine", "Chassis", eng, col="metal", mat="metal", role="detail", pri=1.4)
    num = K.lamp((0, 0.6, -2.5), 0, 0.05, shape="rect", w=0.5, h=0.32)
    piece(H, "NumberPlate", "Chassis", num, col="white", mat="plastic", role="detail", pri=2.0)
    _rig_common(H, wheels, steer, 1.6, 5.0, "Seat", (0, 0.65, 0.45), (0.8, 0.2, 0.7), (0, 0.5, -2.7), (0.85, 0.65, 2.4), sym=6)
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
        posts.append(rod((s * 1.15, 1.45, -1.55), (s * 1.12, 3.15, -1.15), 0.06, segs=8))
        posts.append(rod((s * 1.15, 0.8, 1.0), (s * 1.12, 3.15, 1.05), 0.06, segs=8))
    ws = box((2.2, 1.05, 0.05), (0, 2.2, -1.42), r=0.03, rot_=(-14, 0, 0))
    piece(H, "Posts", "Chassis", merge(*posts), col="darker", mat="metal", role="detail", pri=1.2)
    piece(H, "Glass", "Chassis", ws, col="glass", mat="glass", role="window", pri=1.6, tr=0.3, ao=False)
    roof = K.box((2.75, 0.14, 3.1), (0, 3.2, -0.1), r=0.07, seg=1)
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
    _rig_common(H, wheels, steer, 3.2, 5.6, "Seat", (-0.55, 1.3, 0.3), (0.9, 0.2, 0.8), (0, 0.8, -3.0), (0, 0.5, 2.9), sym=8)
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
        cage.append(rod((s * 1.05, 1.2, -1.45), (s * 0.85, 2.85, -0.4), 0.07, segs=8))
        cage.append(rod((s * 0.85, 2.85, -0.4), (s * 0.85, 2.85, 0.75), 0.07, segs=8))
        cage.append(rod((s * 0.85, 2.85, 0.75), (s * 1.05, 1.25, 1.2), 0.07, segs=8))
        cage.append(rod((s * 0.85, 2.85, 0.75), (s * 0.6, 1.5, 2.4), 0.06, segs=8))
    cage.append(rod((-0.85, 2.85, -0.4), (0.85, 2.85, -0.4), 0.07, segs=8))
    cage.append(rod((-0.85, 2.85, 0.75), (0.85, 2.85, 0.75), 0.07, segs=8))
    cage.append(rod((-0.85, 2.85, 0.75), (0.85, 2.85, -0.4), 0.06, segs=8))
    piece(H, "Cage", "Chassis", merge(*cage), col="darker", mat="metal", role="detail", pri=0.9)
    seats = merge(K.seat_mesh((-0.5, 1.35, 0.25), w=0.75, d=0.7, back=1.0), K.seat_mesh((0.5, 1.35, 0.25), w=0.75, d=0.7, back=1.0))
    piece(H, "Seat", "Chassis", seats, col="secondary", mat="cloth", role="seat", pri=0.9)
    eng = merge(K.box((1.2, 0.7, 0.9), (0, 1.3, 2.25), r=0.1), cyl(0.9, 0.25, (0, 1.75, 2.3), "x", segs=12))
    for s in (-1, 1):
        eng = merge(eng, K.tube_ring(0.09, 0.065, 0.9, axis="z", pos=(s * 0.45, 1.0, 2.9)))
    piece(H, "Engine", "Chassis", eng, col="metal", mat="metal", role="detail", pri=1.2)
    sw = K.steering_mesh((-0.5, 1.95, -0.75), r=0.24, tilt=60, col_len=0.5)
    lights = merge(*(K.lamp((s * 0.55, 3.05, -0.45), 0.15, 0.12) for s in (-1, 1)))
    lb = merge(*(K.cbox((0.38, 0.32, 0.22), (s * 0.55, 3.05, -0.33), c=0.04) for s in (-1, 1)))
    piece(H, "Steering", "Chassis", merge(sw, lb), col="darker", mat="plastic", role="detail", pri=1.4)
    piece(H, "Lamps", "Chassis", lights, col=LENS, mat="glass", role="light", pri=1.7, ao=False)
    _rig_common(H, wheels, steer, 2.9, 6.6, "Seat", (-0.5, 1.45, 0.25), (0.75, 0.2, 0.7), (0, 1.2, -3.3), (0.45, 1.0, 3.3), sym=8)
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
    _rig_common(H, wheels, steer, 2.0, 4.5, "Seat", (0, 1.4, 0.45), (1.2, 0.2, 0.8), (0, 0.6, -2.4), (0, 0.6, 2.2), sym=8, attack="honk")
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
    _rig_common(H, wheels, steer, 2.6, 4.0, "Seat", (0, 1.1, 0.35), (1.0, 0.2, 0.7), (0, 1.0, -2.1), (0.4, 0.6, 2.0), sym=8, attack="honk")
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
    _rig_common(H, wheels, steer, 3.0, 6.5, "Seat", (0, seat_y + 0.1, seat_z), (0.9, 0.2, 0.8), (0, 1.5, -3.6), (0, 0.8, 3.0), sym=5, attack="honk")
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
