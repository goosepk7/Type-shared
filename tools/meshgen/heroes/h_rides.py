"""Rides (land-vehicle mounts the rider sits ON): motorcycle, chopper motorcycle, dirt bike, moped (vespa), kick
scooter, bicycle, bmx, tricycle, unicycle, penny farthing, skateboard, hoverboard, self balancing scooter (segway),
atv (quad bike), snowmobile, sled, sleigh, wagon, covered wagon, cart, horse carriage, chariot, rickshaw, mech walker
(two legs), spider walker (eight legs).

Two-wheelers share a builder: wire / cast wheels on their own bones, a steering Fork bone carrying the front wheel,
fork legs, bars, lamp and fender, a sculpted tank / seat / side panels (side-profile slabs rounded by a warp),
engine with finned cylinders, exhaust, frame and swing arm. The Move clip leans the whole bike into a gentle weave.
"""
import math

import numpy as np

from kit import hero, Hero
from map import VEH
import motion
import landveh_kit as K
from landveh_kit import box, cbox, cyl, bar, rod, extrude, warp, merge, mirror, xf, lamp, piece, mpiece, round_poly

FAM = "rides"
TAU = 2 * math.pi
RED_L = [0.85, 0.08, 0.08]
LENS = [0.95, 0.96, 0.92]
GOLD = "gold"


def pv(p, s, **kw):
    d = {"primary": p, "secondary": s, "glass": "#33414F", "darker": "#24262B"}
    d.update(kw)
    return d


def _new(hid, preview, tags=("vehicle", "ride"), gait="drive", plan="Vehicle"):
    H = Hero(hid, plan=plan, gait=gait, tags=list(tags))
    H.preview = preview
    return H


def _round_x(width, y0, y1, k=0.35):
    """Warp that rounds a slab across X: narrower toward its top and bottom (y0..y1)."""
    def f(V):
        t = np.clip((V[:, 1] - y0) / max(y1 - y0, 1e-6), 0, 1)
        s = 1 - k * (2 * t - 1) ** 2
        return np.column_stack([V[:, 0] * s, V[:, 1], V[:, 2]])
    return f


def _finish(H, wheels, height, length, seat_pos, seat_size, nose, tail, seat="Seat", bone="Chassis", sym=8, steer=(), **kw):
    K.mount(H, seat, seat_pos, seat_size, bone)
    H.socket("head", (0, height + 0.3, 0), bone)
    H.socket("mouth", nose, bone)
    H.socket("exhaust", tail, bone)
    H.rig.update({"head": bone})
    K.vehicle_clips(H, wheels, susp=bone, height=height, length=length, sym=sym, steer=steer, **kw)


# ==================================================================================================== motorbikes
MB = dict(rf=0.62, rb=0.64, wf=0.3, wb=0.4, zf=-1.6, zb=1.45, head=(1.9, -1.05), rake=26.0, rim="alloy", spokes=5, knobby=0.0,
          tank="sport", bars="flat", fender_hi=False, seat_y=1.75, chopper=False, plate=False, sissy=False, fairing=False, preview={})


def _moto(hid, **kw):
    P = dict(MB)
    P.update(kw)
    H = _new(hid, P["preview"])
    rf, rb, zf, zb = P["rf"], P["rb"], P["zf"], P["zb"]
    hy, hz = P["head"]
    H.bone("Chassis", "Body", (0, 0, 0))
    H.bone("Fork", "Chassis", (0, hy, hz))
    wheels, _ = K.add_wheels(H, [dict(name="WheelF", pos=(0, rf, zf), r=rf, w=P["wf"], side=1)], parent="Fork", rim=P["rim"], spokes=P["spokes"],
                             knobby=P["knobby"], lugs=20, grooves=False, rim_col="metal" if P["rim"] != "alloy" else "darker")
    w2, _ = K.add_wheels(H, [dict(name="WheelB", pos=(0, rb, zb), r=rb, w=P["wb"], side=1)], parent="Chassis", rim=P["rim"], spokes=P["spokes"],
                         knobby=P["knobby"], lugs=20, grooves=False, rim_col="metal" if P["rim"] != "alloy" else "darker")
    wheels += w2
    # fork legs + triple clamp + bars + lamp (all steer with the Fork bone)
    fk = []
    for s in (-1, 1):
        fk.append(rod((s * 0.2, hy + 0.15, hz + 0.05), (s * 0.2, rf, zf), 0.065, segs=10))
    fk.append(cbox((0.55, 0.12, 0.25), (0, hy + 0.1, hz), c=0.03))
    fk.append(cbox((0.55, 0.12, 0.25), (0, hy - 0.25, hz - (0.25 * math.tan(math.radians(P["rake"])))), c=0.03))
    by = hy + (0.95 if P["bars"] == "ape" else 0.3)
    bw = 0.75 if P["bars"] != "wide" else 0.9
    if P["bars"] == "ape":
        for s in (-1, 1):
            fk.append(rod((s * 0.12, hy + 0.15, hz), (s * 0.3, by, hz + 0.1), 0.04, segs=6))
            fk.append(rod((s * 0.3, by, hz + 0.1), (s * 0.55, by - 0.1, hz + 0.45), 0.04, segs=6))
        grips = [rod((s * 0.55, by - 0.1, hz + 0.45), (s * 0.75, by - 0.12, hz + 0.5), 0.055, segs=8) for s in (-1, 1)]
    else:
        fk.append(rod((-bw, by, hz + 0.25), (bw, by, hz + 0.25), 0.04, segs=6))
        fk += [rod((s * 0.15, hy + 0.12, hz), (s * 0.25, by, hz + 0.25), 0.04, segs=6) for s in (-1, 1)]
        grips = [rod((s * (bw - 0.2), by, hz + 0.25), (s * (bw + 0.02), by, hz + 0.25), 0.055, segs=8) for s in (-1, 1)]
    piece(H, "Forks", "Fork", merge(*fk), col="metal", mat="metal", role="detail", pri=0.9)
    mir = [merge(rod((s * 0.5, by, hz + 0.25), (s * 0.6, by + 0.35, hz + 0.15), 0.025, segs=5), cbox((0.2, 0.13, 0.05), (s * 0.62, by + 0.4, hz + 0.15), c=0.02)) for s in (-1, 1)]
    piece(H, "Grips", "Fork", merge(*grips, *mir), col="darker", mat="rubber", role="detail", pri=1.4)
    if not P["fairing"]:
        hl = merge(K.lathe_profile([(0.0, 0), (0.0, 0.2), (-0.18, 0.2), (-0.24, 0.12), (-0.25, 0)], 16, "z"))
        hl = xf(hl, (0, hy - 0.05, hz - 0.3))
        piece(H, "LampShell", "Fork", hl, col="metal" if P["chopper"] else "primary", mat="metal", role="detail", pri=1.2)
        piece(H, "Headlight", "Fork", K.lamp((0, hy - 0.05, hz - 0.55), 0.17, 0.08), col=LENS, mat="glass", role="light", pri=1.4, ao=False)
    # front fender
    fa = [(-0.15 if P["fender_hi"] else 15) + 0.0]
    arc_o, arc_i = [], []
    fr = rf + (0.25 if P["fender_hi"] else 0.08)
    a0, a1 = (60, 150) if not P["fender_hi"] else (70, 120)
    for k in range(10):
        a = math.radians(a0 + (a1 - a0) * k / 9)
        arc_o.append((zf - fr * math.cos(a) * -1 * -1 + 0, rf + fr * math.sin(a)))
    arc_o = [(zf + fr * math.cos(math.radians(a0 + (a1 - a0) * k / 9)), rf + fr * math.sin(math.radians(a0 + (a1 - a0) * k / 9))) for k in range(10)]
    arc_i = [(zf + (fr - 0.06) * math.cos(math.radians(a0 + (a1 - a0) * k / 9)), rf + (fr - 0.06) * math.sin(math.radians(a0 + (a1 - a0) * k / 9))) for k in range(9, -1, -1)]
    ff = extrude(np.array(arc_o + arc_i), P["wf"] + 0.14, bevel=0.03, seg=1)
    piece(H, "FenderF", "Fork", ff, col="primary", mat="metal", role="detail", pri=1.2)
    if P["fairing"]:
        fp = round_poly(np.array([(hz - 0.8, hy - 0.7), (hz - 0.85, hy - 0.1), (hz - 0.45, hy + 0.55), (hz + 0.2, hy + 0.55), (hz + 0.35, hy - 0.75)]), [0.2, 0.3, 0.1, 0.1, 0.2], 3)
        fair = warp(extrude(fp, 1.05, bevel=0.2, seg=2), _round_x(1.05, hy - 0.75, hy + 0.6, 0.45))
        piece(H, "Fairing", "Chassis", fair, col="primary", mat="metal", role="body", pri=0.7)
        sc = box((0.65, 0.5, 0.04), (0, hy + 0.75, hz - 0.15), r=0.02, rot_=(-35, 0, 0))
        piece(H, "Screen", "Chassis", sc, col="glass", mat="glass", role="window", pri=1.4, tr=0.3, ao=False)
        piece(H, "Headlight", "Chassis", K.lamp((0, hy - 0.05, hz - 0.88), 0, 0.1, shape="rect", w=0.4, h=0.18), col=LENS, mat="glass", role="light", pri=1.4, ao=False)
    # tank + seat + tail
    sy = P["seat_y"]
    if P["tank"] == "teardrop":
        tk = K.D.revolve([(hz + 0.05, 0), (hz + 0.15, 0.22), (hz + 0.7, 0.3), (hz + 1.4, 0.18), (hz + 1.6, 0)], segs=18, axis=2, spline=3)
        tk = warp(tk, lambda V: np.column_stack([V[:, 0] * 1.05, V[:, 1] * 0.85 + hy - 0.1, V[:, 2]]))
    else:
        tp = round_poly(np.array([(hz + 0.1, hy - 0.45), (hz + 0.05, hy + 0.05), (hz + 0.5, hy + 0.3), (hz + 1.35, hy + 0.12), (hz + 1.55, sy - 0.15), (hz + 1.5, hy - 0.55)]),
                        [0.1, 0.15, 0.3, 0.25, 0.1, 0.1], 3)
        tk = warp(extrude(tp, 0.8, bevel=0.2, seg=2), _round_x(0.8, hy - 0.55, hy + 0.3, 0.4))
    piece(H, "Chassis", "Chassis", tk, col="primary", mat="metal", pri=0.5)
    seat_z0 = hz + 1.45
    seat_z1 = zb - 0.1 if not P["chopper"] else zb - 0.55
    sp = round_poly(np.array([(seat_z0, sy - 0.18), (seat_z0 + 0.05, sy + 0.02), (seat_z0 + 0.5, sy + 0.08), (seat_z1, sy + 0.12 + (0.0 if P["chopper"] else 0.15)),
                              (seat_z1 + 0.1, sy - 0.12), ]), [0.05, 0.1, 0.2, 0.12, 0.05], 3)
    seat = warp(extrude(sp, 0.62, bevel=0.13, seg=2), _round_x(0.62, sy - 0.2, sy + 0.25, 0.3))
    piece(H, "Seat", "Chassis", seat, col="darker", mat="cloth", role="seat", pri=0.8)
    if not P["chopper"]:
        tl_ = round_poly(np.array([(seat_z1 - 0.6, sy - 0.25), (seat_z1 - 0.6, sy - 0.05), (zb + 0.75, sy + 0.25), (zb + 0.85, sy + 0.1), (zb + 0.6, sy - 0.3)]), [0.05, 0.05, 0.1, 0.1, 0.1], 2)
        tail = warp(extrude(tl_, 0.55, bevel=0.12, seg=2), _round_x(0.55, sy - 0.3, sy + 0.25, 0.35))
        piece(H, "Tail", "Chassis", tail, col="primary" if not P["plate"] else "secondary", mat="metal", role="body", pri=0.9)
        piece(H, "Taillight", "Chassis", K.lamp((0, sy + 0.12, zb + 0.84), 0, 0.06, axis="+z", shape="rect", w=0.28, h=0.1), col=RED_L, mat="glass", role="light", pri=1.6, ao=False)
    # rear fender
    rr = rb + (0.12 if not P["fender_hi"] else 0.3)
    a0, a1 = (20, 120) if not P["chopper"] else (0, 130)
    ro = [(zb - rr * math.cos(math.radians(a0 + (a1 - a0) * k / 9)) * -1, rb + rr * math.sin(math.radians(a0 + (a1 - a0) * k / 9))) for k in range(10)]
    ri = [(zb - (rr - 0.06) * math.cos(math.radians(a0 + (a1 - a0) * k / 9)) * -1, rb + (rr - 0.06) * math.sin(math.radians(a0 + (a1 - a0) * k / 9))) for k in range(9, -1, -1)]
    rfm = extrude(np.array(ro + ri), P["wb"] + 0.14, bevel=0.03, seg=1)
    piece(H, "FenderB", "Chassis", rfm, col="primary" if P["chopper"] else "darker", mat="metal", role="detail", pri=1.3)
    # engine
    ey = rf + 0.25
    ez = (hz + zb) / 2 - 0.15
    eng = [box((0.55, 0.6, 1.0), (0, ey + 0.1, ez + 0.1), r=0.12)]
    for k, (dz, ang) in enumerate(((-0.25, -20), (0.3, 20)) if P["chopper"] else ((-0.05, -25),)):
        for j in range(5):
            eng.append(cbox((0.5 - 0.02 * j, 0.06, 0.4), (0, ey + 0.45 + j * 0.1, ez + dz - (j * 0.1) * math.tan(math.radians(-ang))), c=0.015))
        eng.append(cbox((0.35, 0.12, 0.3), (0, ey + 0.98, ez + dz + 0.5 * math.tan(math.radians(ang))), c=0.03))
    eng.append(cyl(0.2, 0.32, (0.3, ey, ez + 0.2), "x", segs=14))
    eng.append(cyl(0.2, 0.32, (-0.3, ey, ez + 0.2), "x", segs=14))
    piece(H, "Engine", "Chassis", merge(*eng), col="metal", mat="metal", role="detail", pri=0.9)
    # exhaust
    ex = []
    for s in ((1,) if not P["chopper"] else (1,)):
        ex.append(rod((0.2, ey + 0.35, ez - 0.25), (0.35, ey - 0.25, ez + 0.2), 0.06, segs=8))
        ex.append(rod((0.35, ey - 0.25, ez + 0.2), (0.4, ey - 0.15, zb - 0.2), 0.06, segs=8))
        if P["chopper"]:
            ex.append(rod((0.15, ey + 0.65, ez + 0.4), (0.42, ey + 0.05, zb - 0.2), 0.06, segs=8))
        mz = zb + (0.3 if P["chopper"] else 0.0)
        ex.append(K.lathe_profile([(zb - 0.7, 0.0), (zb - 0.7, 0.08), (zb - 0.5, 0.13), (mz + 0.25, 0.13), (mz + 0.3, 0.08), (mz + 0.3, 0)], 12, "z"))
        ex[-1] = xf(ex[-1], (0.42, ey - 0.1 + (0.25 if P["fender_hi"] else 0), 0))
    piece(H, "Exhaust", "Chassis", merge(*ex), col="metal", mat="metal", role="detail", pri=1.2)
    # frame + swing arm + pegs
    fr_ = [rod((0, hy - 0.2, hz + 0.1), (0, ey + 0.2, ez - 0.45), 0.07, segs=8), rod((0, hy + 0.05, hz + 0.3), (0, sy - 0.15, seat_z0 + 0.4), 0.06, segs=8),
           rod((0, ey - 0.15, ez + 0.55), (0, sy - 0.2, seat_z0 + 0.7), 0.06, segs=8)]
    for s in (-1, 1):
        fr_.append(bar((s * 0.25, ey - 0.05, ez + 0.6), (s * 0.25, rb, zb), 0.08, 0.16, r=0.03))
        fr_.append(rod((s * 0.24, ey - 0.25, ez + 0.1), (s * 0.55, ey - 0.25, ez + 0.1), 0.05, segs=6))
    if not P["chopper"]:
        fr_ += [rod((s * 0.22, rb + 0.05, zb - 0.1), (s * 0.24, sy - 0.15, seat_z0 + 0.9), 0.07, segs=8) for s in (-1, 1)]
    if P["sissy"]:
        fr_ += [rod((s * 0.3, rb + 0.1, zb - 0.1), (s * 0.25, sy + 1.2, zb - 0.45), 0.04, segs=6) for s in (-1, 1)]
        fr_.append(K.torus(0.25, 0.04, "z", 14, 4, pos=(0, sy + 1.2, zb - 0.45)))
    piece(H, "Frame", "Chassis", merge(*fr_), col="darker" if not P["chopper"] else "metal", mat="metal", role="detail", pri=1.0)
    if P["plate"]:
        npl = box((0.65, 0.5, 0.06), (0, hy - 0.1, hz - 0.45), r=0.08, rot_=(-20, 0, 0))
        piece(H, "NumberPlate", "Fork", npl, col="white", mat="plastic", role="detail", pri=1.5)
    height = max(by, sy) + 0.2
    _finish(H, wheels, height, abs(zf) + zb + 1.0, (0, sy + 0.15, seat_z0 + 0.45), (0.6, 0.2, 0.8), (0, hy, zf - 0.6), (0.42, ey, zb + 0.6),
            sym=P["spokes"] if P["rim"] == "alloy" else 12, steer=("Fork",), roll=2.2, bob=1.0, turns=1.6)
    return H


@hero("motorcycle", FAM)
def motorcycle():
    return _moto("motorcycle", fairing=True, preview=pv("#C1121F", "#1F1F1F"))


@hero("chopper motorcycle", FAM)
def chopper():
    return _moto("chopper motorcycle", zf=-2.55, rf=0.6, rb=0.62, wb=0.55, head=(2.15, -1.25), rake=45, rim="wire", spokes=28, tank="teardrop",
                 bars="ape", seat_y=1.35, chopper=True, sissy=True, preview=pv("#1A1A1A", "#C0C0C0"))


@hero("dirt bike", FAM)
def dirt_bike():
    return _moto("dirt bike", rf=0.72, rb=0.7, wf=0.26, wb=0.34, zf=-1.65, zb=1.4, head=(2.15, -1.0), rim="wire", spokes=28, knobby=0.06,
                 bars="wide", fender_hi=True, seat_y=2.05, plate=True, preview=pv("#FF7A00", "#F5F5F5"))


@hero("moped", FAM)
def moped():
    """Vespa-style step-through: leg shield, floorboard, rounded rear cowl over the engine, small disc wheels."""
    H = _new("moped", pv("#A7D7C5", "#F5F0E1"))
    H.bone("Chassis", "Body", (0, 0, 0))
    H.bone("Fork", "Chassis", (0, 1.9, -1.15))
    wheels, _ = K.add_wheels(H, [dict(name="WheelF", pos=(0, 0.45, -1.35), r=0.45, w=0.3, side=1)], parent="Fork", rim="disc", rim_col="metal", grooves=False)
    w2, _ = K.add_wheels(H, [dict(name="WheelB", pos=(0, 0.45, 1.15), r=0.45, w=0.3, side=1)], parent="Chassis", rim="disc", rim_col="metal", grooves=False)
    wheels += w2
    shield = round_poly(np.array([(-1.0, 0.45), (-1.25, 1.2), (-1.3, 1.95), (-1.05, 2.0), (-0.85, 1.3), (-0.6, 0.62), (0.4, 0.62), (0.4, 0.45)]), [0.1, 0.3, 0.15, 0.1, 0.3, 0.15, 0.05, 0.05], 3)
    sh = warp(extrude(shield, 1.0, bevel=0.12, seg=2), lambda V: np.column_stack([V[:, 0] * (1 - 0.3 * np.clip((V[:, 1] - 1.2) / 0.8, 0, 1)), V[:, 1], V[:, 2]]))
    cowl = K.D.revolve([(0.15, 0), (0.25, 0.4), (0.75, 0.55), (1.4, 0.45), (1.75, 0.2), (1.8, 0)], segs=20, axis=2, spline=3)
    cowl = warp(cowl, lambda V: np.column_stack([V[:, 0] * 1.25, V[:, 1] * 0.85 + 1.05, V[:, 2]]))
    piece(H, "Chassis", "Chassis", merge(sh, cowl), col="primary", mat="metal", pri=0.5)
    seat = warp(extrude(round_poly(np.array([(0.05, 1.45), (0.1, 1.68), (1.3, 1.72), (1.45, 1.5)]), 0.12, 2), 0.6, bevel=0.12, seg=2), _round_x(0.6, 1.45, 1.75, 0.3))
    piece(H, "Seat", "Chassis", seat, col="secondary", mat="cloth", role="seat", pri=0.8)
    fk = merge(rod((0, 1.9, -1.15), (0, 0.45, -1.35), 0.07, segs=8), rod((-0.65, 2.35, -1.05), (0.65, 2.35, -1.05), 0.045, segs=6), cbox((0.4, 0.3, 0.3), (0, 2.25, -1.1), c=0.06))
    piece(H, "Forks", "Fork", fk, col="primary", mat="metal", role="detail", pri=0.9)
    hl = xf(K.lathe_profile([(0.0, 0), (0.0, 0.17), (-0.15, 0.17), (-0.2, 0)], 14, "z"), (0, 2.25, -1.25))
    piece(H, "LampShell", "Fork", hl, col="metal", mat="metal", role="detail", pri=1.2)
    piece(H, "Headlight", "Fork", K.lamp((0, 2.25, -1.47), 0.14, 0.06), col=LENS, mat="glass", role="light", pri=1.4, ao=False)
    ff = K.D.revolve([(-0.5, 0), (-0.45, 0.3), (0.0, 0.36), (0.45, 0.3), (0.5, 0)], segs=12, axis=2, spline=2)
    ff = xf(warp(ff, lambda V: np.column_stack([V[:, 0] * 0.6, np.maximum(V[:, 1], 0.0) * 1.0, V[:, 2]])), (0, 0.85, -1.35))
    piece(H, "FenderF", "Fork", ff, col="primary", mat="metal", role="detail", pri=1.2)
    det = merge(K.lamp((0, 1.35, 1.82), 0, 0.06, axis="+z", shape="rect", w=0.3, h=0.14), )
    piece(H, "Taillight", "Chassis", det, col=RED_L, mat="glass", role="light", pri=1.6, ao=False)
    ex = merge(K.lathe_profile([(0.6, 0), (0.6, 0.1), (1.45, 0.1), (1.5, 0)], 10, "z"))
    piece(H, "Exhaust", "Chassis", xf(ex, (0.4, 0.4, 0)), col="metal", mat="metal", role="detail", pri=1.4)
    grips = merge(*(rod((s * 0.5, 2.35, -1.05), (s * 0.72, 2.35, -1.05), 0.055, segs=8) for s in (-1, 1)), *(merge(rod((s * 0.45, 2.35, -1.05), (s * 0.55, 2.7, -1.1), 0.02, segs=5), cbox((0.18, 0.12, 0.04), (s * 0.57, 2.75, -1.1), c=0.02)) for s in (-1, 1)))
    piece(H, "Grips", "Fork", grips, col="darker", mat="rubber", role="detail", pri=1.5)
    rack = merge(*(rod((s * 0.3, 1.6, 1.4), (s * 0.3, 1.6, 2.0), 0.03, segs=5) for s in (-1, 1)), rod((-0.3, 1.6, 2.0), (0.3, 1.6, 2.0), 0.03, segs=5))
    piece(H, "Rack", "Chassis", rack, col="metal", mat="metal", role="detail", pri=1.8)
    _finish(H, wheels, 2.6, 4.0, (0, 1.75, 0.6), (0.6, 0.2, 0.8), (0, 2.2, -1.6), (0.4, 0.4, 1.6), steer=("Fork",), roll=2.0, sym=8)
    return H


@hero("scooter", FAM)
def kick_scooter():
    H = _new("scooter", pv("#7B2CBF", "#E0E0E0"))
    H.bone("Chassis", "Body", (0, 0, 0))
    H.bone("Fork", "Chassis", (0, 0.55, -1.15))
    wheels, _ = K.add_wheels(H, [dict(name="WheelF", pos=(0, 0.3, -1.3), r=0.3, w=0.18, side=1)], parent="Fork", rim="alloy", spokes=6, rim_col="secondary", grooves=False)
    w2, _ = K.add_wheels(H, [dict(name="WheelB", pos=(0, 0.3, 1.1), r=0.3, w=0.18, side=1)], parent="Chassis", rim="alloy", spokes=6, rim_col="secondary", grooves=False)
    wheels += w2
    deck = round_poly(np.array([(-1.0, 0.25), (-1.05, 0.42), (0.95, 0.42), (1.35, 0.55), (1.4, 0.45), (1.0, 0.25)]), [0.05, 0.08, 0.1, 0.08, 0.05, 0.08], 2)
    dk = extrude(deck, 0.5, bevel=0.06, seg=2)
    piece(H, "Chassis", "Chassis", dk, col="primary", mat="metal", pri=0.5)
    grip = cbox((0.42, 0.03, 1.7), (0, 0.43, -0.1), c=0.01)
    piece(H, "Seat", "Chassis", grip, col="darker", mat="rubber", role="seat", pri=0.9)
    stem = merge(rod((0, 0.3, -1.3), (0, 0.55, -1.15), 0.05, segs=8), rod((0, 0.5, -1.18), (0, 3.2, -0.95), 0.06, segs=10), rod((-0.45, 3.2, -0.95), (0.45, 3.2, -0.95), 0.045, segs=8),
                 cbox((0.2, 0.3, 0.15), (0, 0.65, -1.15), c=0.04))
    piece(H, "Stem", "Fork", stem, col="metal", mat="metal", role="detail", pri=0.8)
    grips = merge(*(rod((s * 0.3, 3.2, -0.95), (s * 0.55, 3.2, -0.95), 0.06, segs=8) for s in (-1, 1)))
    piece(H, "Grips", "Fork", grips, col="darker", mat="rubber", role="detail", pri=1.2)
    brake = K.D.revolve([(0.85, 0), (0.9, 0.2), (1.25, 0.24), (1.45, 0.15), (1.5, 0)], segs=10, axis=2, spline=2)
    brake = warp(brake, lambda V: np.column_stack([V[:, 0] * 0.7, np.maximum(V[:, 1], 0) * 0.5 + 0.55, V[:, 2]]))
    piece(H, "Brake", "Chassis", brake, col="secondary", mat="plastic", role="detail", pri=1.4)
    _finish(H, wheels, 3.2, 2.8, (0, 0.5, -0.1), (0.45, 0.1, 1.6), (0, 0.4, -1.6), (0, 0.4, 1.5), steer=("Fork",), roll=1.5, sym=6, attack="honk")
    return H


# ==================================================================================================== pedal cycles
def _wire_wheel(H, name, bone, pos, r, w=0.12, spokes=28, tyre_col="tyre", rim_col="metal", knobby=0.0):
    t = K.tyre(r, w * 1.5, ri=r - w * 1.1, segs=28, knobby=knobby, grooves=False, lugs=24)
    rimr = K.lathe_profile([(-w * 0.4, r - w * 1.3), (w * 0.4, r - w * 1.3), (w * 0.4, r - w * 1.0), (-w * 0.4, r - w * 1.0)], 28, "x", closed=True, hard_deg=40)
    hubm = K.lathe_profile([(-w * 1.1, 0), (-w * 1.1, r * 0.07), (w * 1.1, r * 0.07), (w * 1.1, 0)], 10, "x")
    sp = []
    for k in range(spokes):
        a = TAU * k / spokes
        sx = w * 0.9 if k % 2 else -w * 0.9
        sp.append(rod((sx, math.cos(a) * r * 0.06, math.sin(a) * r * 0.06), (0, math.cos(a + 0.3) * (r - w * 1.2), math.sin(a + 0.3) * (r - w * 1.2)), 0.012, segs=3, bevel=0.002))
    piece(H, name + "Tyre", bone, xf(t, pos), col=tyre_col, mat="rubber", role="wheel", pri=1.0, fallback="Cylinder")
    piece(H, name + "Rim", bone, xf(merge(rimr, hubm, *sp), pos), col=rim_col, mat="metal", role="wheel", pri=1.3, fallback="Cylinder")


def _crank(H, bone_parent, pos, r=0.42, side_x=0.35, col="darker"):
    """Pedal crank on its own spinning bone: chainring + two arms + pedals."""
    b = H.bone("Crank", bone_parent, pos)
    x, y, z = pos
    ring = K.lathe_profile([(0.06, 0), (0.06, r * 0.55), (0.1, r * 0.55), (0.1, 0)], 18, "x")
    arms = [bar((x + side_x, y, z), (x + side_x, y - r, z), 0.07, 0.1), bar((x - side_x, y, z), (x - side_x, y + r, z), 0.07, 0.1)]
    ped = [cbox((0.3, 0.06, 0.18), (x + side_x + 0.18, y - r, z), c=0.02), cbox((0.3, 0.06, 0.18), (x - side_x - 0.18, y + r, z), c=0.02)]
    axle = rod((x - side_x, y, z), (x + side_x, y, z), 0.05, segs=8)
    piece(H, "Crank", b, merge(xf(ring, pos), *arms, *ped, axle), col=col, mat="metal", role="detail", pri=1.2)
    return b


def _bicycle(hid, r=0.72, wb=2.15, frame_h=1.0, bmx=False, preview=None, tandem=False):
    H = _new(hid, preview)
    H.bone("Chassis", "Body", (0, 0, 0))
    zf, zb = -wb / 2, wb / 2
    if tandem:
        zf, zb = -1.9, 1.9
    head = (0, r + frame_h + 0.15, zf + 0.42)
    H.bone("Fork", "Chassis", head)
    H.bone("WheelF", "Fork", (0, r, zf))
    H.bone("WheelB", "Chassis", (0, r, zb))
    w = 0.15 if bmx else 0.11
    _wire_wheel(H, "WheelF", "WheelF", (0, r, zf), r, w=w, spokes=24 if bmx else 32, knobby=0.03 if bmx else 0.0)
    _wire_wheel(H, "WheelB", "WheelB", (0, r, zb), r, w=w, spokes=24 if bmx else 32, knobby=0.03 if bmx else 0.0)
    bb = (0, r - 0.05, (zf + zb) / 2 + 0.1 + (0.0 if not tandem else 0.6))
    seat_t = (0, r + frame_h + 0.05, bb[2] + 0.4)
    fr = [rod(head, bb, 0.06, segs=8), rod(bb, seat_t, 0.06, segs=8), rod(head, (0, seat_t[1] - 0.05, seat_t[2] - 0.05), 0.055, segs=8)]
    for s in (-1, 1):
        fr.append(rod((s * 0.08, bb[1], bb[2]), (s * 0.1, r, zb), 0.035, segs=6))
        fr.append(rod((s * 0.08, seat_t[1] - 0.05, seat_t[2]), (s * 0.1, r, zb), 0.035, segs=6))
    if tandem:
        bb2 = (0, r - 0.05, -0.75)
        st2 = (0, r + frame_h + 0.05, -0.35)
        fr += [rod(head, bb2, 0.06, segs=8), rod(bb2, st2, 0.06, segs=8), rod(st2, seat_t, 0.055, segs=8), rod(bb2, bb, 0.055, segs=8)]
    piece(H, "Chassis", "Chassis", merge(*fr), col="primary", mat="metal", pri=0.5)
    fork = [rod((0, head[1] + 0.25, head[2] + 0.08), (0, head[1] - 0.1, head[2]), 0.05, segs=8)]
    fork += [rod((s * 0.08, head[1] - 0.1, head[2]), (s * 0.09, r, zf), 0.035, segs=6) for s in (-1, 1)]
    hb_y = head[1] + (0.45 if bmx else 0.3)
    if bmx:
        fork += [rod((s * 0.1, head[1] + 0.2, head[2] + 0.05), (s * 0.35, hb_y, head[2] + 0.2), 0.03, segs=6) for s in (-1, 1)]
        fork.append(rod((-0.35, hb_y, head[2] + 0.2), (0.35, hb_y, head[2] + 0.2), 0.03, segs=6))
        fork.append(rod((-0.15, head[1] + 0.3, head[2] + 0.12), (0.15, head[1] + 0.3, head[2] + 0.12), 0.03, segs=6))
        hbw = 0.65
    else:
        fork.append(rod((0, head[1] + 0.25, head[2] + 0.08), (0, hb_y, head[2] + 0.25), 0.035, segs=6))
        fork.append(rod((-0.4, hb_y, head[2] + 0.25), (0.4, hb_y, head[2] + 0.25), 0.03, segs=6))
        hbw = 0.55
    piece(H, "Forks", "Fork", merge(*fork), col="primary" if bmx else "metal", mat="metal", role="detail", pri=0.9)
    grips = merge(*(rod((s * (hbw - 0.2), hb_y, head[2] + 0.2 + (0 if bmx else 0.05)), (s * (hbw + 0.02), hb_y, head[2] + 0.2 + (0 if bmx else 0.05)), 0.045, segs=8) for s in (-1, 1)),
                  cyl(0.06, 0.07, (0.25, hb_y + 0.05, head[2] + 0.25), "y", segs=10))
    piece(H, "Grips", "Fork", grips, col="darker", mat="rubber", role="detail", pri=1.3)
    saddles = [seat_t] + ([(0, r + frame_h + 0.05, -0.35)] if tandem else [])
    sd = []
    for p in saddles:
        sp = round_poly(np.array([(p[2] - 0.35, p[1] + 0.1), (p[2] - 0.3, p[1] + 0.16), (p[2] + 0.2, p[1] + 0.2), (p[2] + 0.28, p[1] + 0.08), (p[2] - 0.1, p[1] + 0.05)]), 0.05, 2)
        s_ = warp(extrude(sp, 0.32, bevel=0.07, seg=2), lambda V, pz=p[2]: np.column_stack([V[:, 0] * (0.45 + 0.55 * np.clip((V[:, 2] - pz + 0.35) / 0.5, 0, 1)), V[:, 1], V[:, 2]]))
        sd.append(merge(s_, rod((0, p[1] - 0.15, p[2]), (0, p[1] + 0.08, p[2] - 0.02), 0.035, segs=6)))
    piece(H, "Seat", "Chassis", sd[0], col="darker", mat="cloth", role="seat", pri=0.8)
    if tandem:
        piece(H, "Seat2", "Chassis", sd[1], col="darker", mat="cloth", role="seat", pri=0.9)
    crank = _crank(H, "Chassis", bb, r=0.3, side_x=0.22)
    cranks = [crank]
    if tandem:
        cranks.append(None)
    chain = merge(rod((0.2, bb[1] + 0.22, bb[2]), (0.2, r + 0.1, zb), 0.02, segs=4), rod((0.2, bb[1] - 0.22, bb[2]), (0.2, r - 0.1, zb), 0.02, segs=4))
    extra = [chain]
    if not bmx:
        bell = cyl(0.06, 0.08, (-0.3, hb_y + 0.06, head[2] + 0.25), "y", segs=10)
        piece(H, "Bell", "Fork", bell, col="metal", mat="metal", role="detail", pri=2.0)
        rf = [(zb + (r + 0.08) * math.cos(math.radians(a)), r + (r + 0.08) * math.sin(math.radians(a))) for a in np.linspace(10, 130, 9)]
        ri = [(zb + (r + 0.03) * math.cos(math.radians(a)), r + (r + 0.03) * math.sin(math.radians(a))) for a in np.linspace(130, 10, 9)]
        extra.append(extrude(np.array(rf + ri), 0.18, bevel=0.02, seg=1))
        extra.append(K.lamp((0, r + 0.5, zb + 0.7), 0, 0.05, axis="+z", shape="rect", w=0.12, h=0.18))
    else:
        extra += [cyl(0.35, 0.05, (s * 0.2, r, zb), "x", segs=8) for s in (-1, 1)]
    piece(H, "Chain", "Chassis", merge(*extra), col="darker", mat="metal", role="detail", pri=1.5)

    def mv(pose, u):
        K.add(pose, "Crank", (0, 0, 0, -TAU * u, 0, 0))

    _finish(H, [("WheelF", r), ("WheelB", r)], seat_t[1] + 0.3, wb + 2 * r, (0, seat_t[1] + 0.2, seat_t[2]), (0.35, 0.15, 0.55), (0, head[1], zf - r),
            (0, r, zb + r), steer=("Fork",), roll=2.0, bob=0.4, sym=12, attack="honk", extra_move=mv)
    return H


@hero("bicycle", FAM)
def bicycle():
    return _bicycle("bicycle", preview=pv("#1E88E5", "#F5F5F5"))


@hero("bmx", FAM)
def bmx():
    return _bicycle("bmx", r=0.55, wb=1.8, frame_h=0.75, bmx=True, preview=pv("#FF2E63", "#252A34"))


@hero("tandem bicycle", FAM)
def tandem():
    return _bicycle("tandem bicycle", tandem=True, preview=pv("#2A9D8F", "#F4F1DE"))


@hero("tricycle", FAM)
def tricycle():
    H = _new("tricycle", pv("#E63946", "#F1FAEE"))
    H.bone("Chassis", "Body", (0, 0, 0))
    H.bone("Fork", "Chassis", (0, 1.25, -0.85))
    H.bone("WheelF", "Fork", (0, 0.58, -1.0))
    _wire_wheel(H, "WheelF", "WheelF", (0, 0.58, -1.0), 0.58, w=0.12, spokes=16)
    wheels = [("WheelF", 0.58)]
    for s, tag in ((1, "R"), (-1, "L")):
        b = H.bone("WheelB" + tag, "Chassis", (s * 0.7, 0.35, 0.7))
        _wire_wheel(H, "WheelB" + tag, b, (s * 0.7, 0.35, 0.7), 0.35, w=0.1, spokes=12)
        wheels.append((b, 0.35))
    fr = merge(rod((0, 1.1, -0.85), (0, 0.85, 0.5), 0.07, segs=8), rod((-0.7, 0.35, 0.7), (0.7, 0.35, 0.7), 0.05, segs=8), cbox((0.9, 0.12, 0.6), (0, 0.55, 0.8), c=0.04),
               rod((0, 0.85, 0.5), (0, 0.5, 0.7), 0.06, segs=8))
    piece(H, "Chassis", "Chassis", fr, col="primary", mat="metal", pri=0.5)
    seat = K.seat_mesh((0, 1.0, 0.3), w=0.6, d=0.5, back=0.45, bucket=False)
    piece(H, "Seat", "Chassis", seat, col="secondary", mat="plastic", role="seat", pri=0.8)
    fk = merge(*(rod((s * 0.08, 1.3, -0.85), (s * 0.09, 0.58, -1.0), 0.035, segs=6) for s in (-1, 1)), rod((0, 1.3, -0.85), (0, 1.6, -0.75), 0.04, segs=6),
               rod((-0.45, 1.6, -0.7), (0.45, 1.6, -0.7), 0.035, segs=6))
    piece(H, "Forks", "Fork", fk, col="primary", mat="metal", role="detail", pri=0.9)
    tass = merge(*(merge(rod((s * 0.45, 1.6, -0.7), (s * 0.62, 1.6, -0.7), 0.06, segs=8), *[rod((s * 0.63, 1.6, -0.7), (s * (0.72 + 0.04 * k), 1.35, -0.7 + 0.04 * (k - 1)), 0.012, segs=3) for k in range(3)]) for s in (-1, 1)))
    piece(H, "Grips", "Fork", tass, col="secondary", mat="cloth", role="detail", pri=1.3)
    b = H.bone("Crank", "WheelF", (0, 0.58, -1.0))
    ped = merge(bar((0.2, 0.58, -1.0), (0.2, 0.3, -1.0), 0.06, 0.08), bar((-0.2, 0.58, -1.0), (-0.2, 0.86, -1.0), 0.06, 0.08),
                cbox((0.22, 0.05, 0.14), (0.32, 0.3, -1.0), c=0.02), cbox((0.22, 0.05, 0.14), (-0.32, 0.86, -1.0), c=0.02))
    piece(H, "Pedals", "WheelF", ped, col="darker", mat="plastic", role="detail", pri=1.2)
    H.bones = [x for x in H.bones if x[0] != "Crank"]
    H.bidx = {n[0]: i for i, n in enumerate(H.bones)}
    _finish(H, wheels, 1.7, 2.6, (0, 1.05, 0.3), (0.55, 0.15, 0.45), (0, 1.0, -1.6), (0, 0.5, 1.1), steer=("Fork",), roll=0.6, sym=12, attack="honk")
    return H


@hero("unicycle", FAM)
def unicycle():
    H = _new("unicycle", pv("#F4D35E", "#1D3557"))
    H.bone("Chassis", "Body", (0, 0, 0))
    H.bone("Wheel", "Chassis", (0, 0.7, 0))
    _wire_wheel(H, "Wheel", "Wheel", (0, 0.7, 0), 0.7, w=0.13, spokes=24)
    fork = merge(*(rod((s * 0.12, 0.7, 0), (s * 0.12, 1.65, 0), 0.04, segs=6) for s in (-1, 1)), cbox((0.32, 0.1, 0.12), (0, 1.68, 0), c=0.03), rod((0, 1.7, 0), (0, 2.6, 0.02), 0.05, segs=8))
    piece(H, "Chassis", "Chassis", fork, col="secondary", mat="metal", pri=0.5)
    sp = round_poly(np.array([(-0.35, 2.6), (-0.3, 2.75), (0.25, 2.78), (0.35, 2.62), (0.0, 2.58)]), 0.06, 2)
    seat = warp(extrude(sp, 0.38, bevel=0.08, seg=2), lambda V: np.column_stack([V[:, 0] * (0.55 + 0.45 * np.clip((V[:, 2] + 0.35) / 0.5, 0, 1)), V[:, 1], V[:, 2]]))
    piece(H, "Seat", "Chassis", seat, col="primary", mat="cloth", role="seat", pri=0.8)
    ped = merge(bar((0.22, 0.7, 0), (0.22, 0.35, 0), 0.06, 0.08), bar((-0.22, 0.7, 0), (-0.22, 1.05, 0), 0.06, 0.08),
                cbox((0.25, 0.05, 0.16), (0.36, 0.35, 0), c=0.02), cbox((0.25, 0.05, 0.16), (-0.36, 1.05, 0), c=0.02))
    piece(H, "Pedals", "Wheel", ped, col="darker", mat="plastic", role="detail", pri=1.2)

    def mv(pose, u):
        K.add(pose, "Chassis", (0, 0, 0, 0.05 * math.sin(TAU * u), 0, 0.06 * math.sin(TAU * u + 1)))

    _finish(H, [("Wheel", 0.7)], 2.8, 1.6, (0, 2.8, 0), (0.35, 0.12, 0.55), (0, 2.0, -0.7), (0, 1.0, 0.7), roll=1.5, sym=12, attack="honk", extra_move=mv)
    return H


@hero("penny farthing", FAM)
def penny_farthing():
    H = _new("penny farthing", pv("#2B2D42", "#8D99AE"))
    H.bone("Chassis", "Body", (0, 0, 0))
    H.bone("Fork", "Chassis", (0, 3.05, -0.6))
    H.bone("WheelF", "Fork", (0, 1.45, -0.7))
    H.bone("WheelB", "Chassis", (0, 0.38, 1.6))
    _wire_wheel(H, "WheelF", "WheelF", (0, 1.45, -0.7), 1.45, w=0.12, spokes=36)
    _wire_wheel(H, "WheelB", "WheelB", (0, 0.38, 1.6), 0.38, w=0.09, spokes=12)
    bb = merge(K.D.revolve([(0, 0), (0.0, 0.07), (1.0, 0.06), (2.0, 0.045), (2.4, 0)], segs=8, axis=2, spline=2))
    spine = []
    pts = [(0, 3.0, -0.45), (0, 2.9, 0.4), (0, 2.2, 1.2), (0, 0.6, 1.62)]
    for a, b in zip(pts[:-1], pts[1:]):
        spine.append(rod(a, b, 0.07, segs=8))
    piece(H, "Chassis", "Chassis", merge(*spine), col="primary", mat="metal", pri=0.5)
    sp = round_poly(np.array([(-0.15, 3.1), (-0.1, 3.25), (0.45, 3.27), (0.55, 3.1), (0.2, 3.05)]), 0.06, 2)
    seat = warp(extrude(sp, 0.4, bevel=0.08, seg=2), lambda V: np.column_stack([V[:, 0] * (0.55 + 0.45 * np.clip((V[:, 2] + 0.15) / 0.5, 0, 1)), V[:, 1], V[:, 2]]))
    piece(H, "Seat", "Chassis", seat, col="darker", mat="cloth", role="seat", pri=0.8)
    fk = merge(*(rod((s * 0.12, 3.1, -0.62), (s * 0.13, 1.45, -0.7), 0.04, segs=6) for s in (-1, 1)), rod((-0.6, 3.35, -0.5), (0.6, 3.35, -0.5), 0.04, segs=6),
               rod((0, 3.1, -0.62), (0, 3.35, -0.5), 0.05, segs=6))
    piece(H, "Forks", "Fork", fk, col="metal", mat="metal", role="detail", pri=0.9)
    ped = merge(bar((0.2, 1.45, -0.7), (0.2, 1.15, -0.7), 0.06, 0.08), bar((-0.2, 1.45, -0.7), (-0.2, 1.75, -0.7), 0.06, 0.08),
                cbox((0.22, 0.05, 0.14), (0.32, 1.15, -0.7), c=0.02), cbox((0.22, 0.05, 0.14), (-0.32, 1.75, -0.7), c=0.02))
    piece(H, "Pedals", "WheelF", ped, col="darker", mat="metal", role="detail", pri=1.2)
    _finish(H, [("WheelF", 1.45), ("WheelB", 0.38)], 3.4, 3.8, (0, 3.3, 0.2), (0.35, 0.12, 0.5), (0, 2.0, -2.2), (0, 0.5, 2.0), steer=("Fork",), roll=1.2, sym=12, attack="honk")
    return H


# ==================================================================================================== boards
def _deck(L=3.0, W=0.85, t=0.1, kick=0.35, y=0.45):
    plan = round_poly(np.array([(-W / 2, -L / 2), (W / 2, -L / 2), (W / 2, L / 2), (-W / 2, L / 2)]), W * 0.48, 6)
    d = extrude(plan, t, bevel=0.03, axis="y", seg=1)

    def f(V):
        z = V[:, 2]
        lift = kick * np.clip((np.abs(z) - (L / 2 - 0.55)) / 0.55, 0, 1) ** 2
        return np.column_stack([V[:, 0], V[:, 1] + y + lift, z])

    return warp(d, f)


@hero("skateboard", FAM)
def skateboard():
    H = _new("skateboard", pv("#E76F51", "#264653"))
    H.bone("Chassis", "Body", (0, 0.0, 0))
    deck = _deck()
    piece(H, "Chassis", "Chassis", deck, col="primary", mat="wood", pri=0.5)
    grip = xf(_deck(2.8, 0.75, 0.02, 0.33, 0.0), (0, 0.51, 0))
    piece(H, "Seat", "Chassis", grip, col="darker", mat="rubber", role="seat", pri=0.9)
    wheels = []
    for z, tag in ((-1.0, "F"), (1.0, "B")):
        tr = merge(cbox((0.5, 0.08, 0.35), (0, 0.36, z), c=0.02), K.lathe_profile([(-0.12, 0), (-0.12, 0.09), (0.12, 0.09), (0.12, 0)], 8, "y"),
                   rod((-0.5, 0.18, z), (0.5, 0.18, z), 0.04, segs=6))
        tr = merge(cbox((0.5, 0.08, 0.35), (0, 0.38, z), c=0.02), cbox((0.22, 0.15, 0.2), (0, 0.27, z), c=0.04), rod((-0.48, 0.18, z), (0.48, 0.18, z), 0.04, segs=6))
        piece(H, "Truck" + tag, "Chassis", tr, col="metal", mat="metal", role="detail", pri=1.0)
        for s, sd in ((1, "R"), (-1, "L")):
            b = H.bone(f"Wheel{tag}{sd}", "Chassis", (s * 0.42, 0.18, z))
            wm = K.lathe_profile([(-0.08, 0.0), (-0.08, 0.15), (-0.05, 0.18), (0.05, 0.18), (0.08, 0.15), (0.08, 0.0)], 14, "x")
            piece(H, f"Wheel{tag}{sd}", b, xf(wm, (s * 0.42, 0.18, z)), col="secondary", mat="plastic", role="wheel", pri=1.1, fallback="Cylinder")
            wheels.append((b, 0.18))

    def atk(pose, s):  # ollie
        up = K._bump(s, 0.1, 0.8)
        K.add(pose, "Chassis", (0, 0.8 * up, 0, 0.35 * K._bump(s, 0.1, 0.45) - 0.2 * K._bump(s, 0.45, 0.8), 0, 0))

    _finish(H, wheels, 0.6, 3.0, (0, 0.55, 0), (0.7, 0.1, 2.2), (0, 0.5, -1.5), (0, 0.5, 1.5), roll=0.8, sym=8, attack="honk", extra_attack=atk)
    return H


@hero("hoverboard", FAM)
def hoverboard():
    H = _new("hoverboard", pv("#3A86FF", "#E0E0E0"), gait="hover")
    H.bone("Chassis", "Body", (0, 0.6, 0))
    deck = _deck(3.2, 1.0, 0.16, 0.3, 0.8)
    piece(H, "Chassis", "Chassis", deck, col="primary", mat="plastic", pri=0.5)
    grip = xf(_deck(2.9, 0.85, 0.02, 0.28, 0.0), (0, 0.89, 0))
    piece(H, "Seat", "Chassis", grip, col="darker", mat="rubber", role="seat", pri=0.9)
    pods = merge(*[K.lathe_profile([(0.0, 0), (0.0, 0.32), (0.12, 0.3), (0.2, 0.2), (0.22, 0)], 18, "y") for _ in range(1)])
    pd = merge(*[xf(K.lathe_profile([(0.0, 0), (0.0, 0.3), (-0.12, 0.28), (-0.2, 0.2), (-0.22, 0)], 18, "y"), (0, 0.73, z)) for z in (-0.95, 0.95)])
    piece(H, "Pods", "Chassis", pd, col="secondary", mat="metal", role="detail", pri=1.0)
    glow = merge(*[cyl(0.04, 0.2, (0, 0.5, z), "y", segs=14) for z in (-0.95, 0.95)])
    piece(H, "Thrusters", "Chassis", glow, col=[0.45, 0.85, 1.0], mat="glass", role="light", pri=1.4, glow=True, ao=False)
    stripe = merge(*[cbox((0.04, 0.05, 2.4), (s * 0.5, 0.82, 0), c=0.01) for s in (-1, 1)])
    piece(H, "Trim", "Chassis", stripe, col="secondary", mat="metal", role="detail", pri=1.6)
    K.mount(H, "Seat", (0, 0.95, 0), (0.8, 0.1, 2.4), "Chassis")
    H.socket("head", (0, 1.3, 0), "Chassis")
    H.socket("mouth", (0, 0.8, -1.7), "Chassis")
    H.socket("exhaust", (0, 0.4, 0.95), "Chassis")
    H.rig.update({"head": "Chassis"})

    def move(t):
        u = t / 1.2
        return {"Chassis": (0, 0.08 * math.sin(TAU * u * 2), 0, -0.06 + 0.02 * math.sin(TAU * u * 2), 0, 0.08 * math.sin(TAU * u))}

    def idle(t):
        u = t / 2.4
        return {"Chassis": (0, 0.12 * math.sin(TAU * u), 0, 0.02 * math.sin(TAU * u * 2), 0.05 * math.sin(TAU * u), 0.03 * math.sin(TAU * u + 1))}

    def atk(t):
        s = t / 0.8
        return {"Chassis": (0, 0.6 * K._bump(s, 0.0, 0.7), -1.0 * K._bump(s, 0.2, 0.8), 0.3 * K._bump(s, 0.0, 0.4), TAU * K._ease((s - 0.1) / 0.6), 0)}

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1))
        return {"Chassis": (0, -0.1 * k, 0.3 * k, 0.2 * k, 0, 0.2 * math.sin(t * 30) * k)}

    H.clip("Move", 1.2, move, keys=20)
    H.clip("Idle", 2.4, idle, keys=20)
    H.clip("Attack", 0.8, atk, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=10, loop=False)
    H.rig["height"] = 1.0
    return H


@hero("self balancing scooter", FAM)
def segway():
    H = _new("self balancing scooter", pv("#E0E0E0", "#222222"))
    H.bone("Chassis", "Body", (0, 0.55, 0))
    wheels, _ = K.add_wheels(H, [dict(name="WheelR", pos=(0.95, 0.55, 0), r=0.55, w=0.35, side=1), dict(name="WheelL", pos=(-0.95, 0.55, 0), r=0.55, w=0.35, side=-1)],
                             parent="Body", rim="alloy", spokes=5, rim_col="darker", grooves=False)
    plat = merge(box((1.4, 0.22, 0.95), (0, 0.45, 0), r=0.08), *[box((0.3, 0.75, 1.2), (s * 0.95, 0.75, 0), r=0.12) for s in (-1, 1)])
    plat = merge(box((1.4, 0.22, 0.95), (0, 0.45, 0), r=0.08), *[K.D.revolve([(-0.62, 0), (-0.6, 0.3), (0.0, 0.66), (0.6, 0.3), (0.62, 0)], segs=14, axis=2, spline=2) for _ in range(0)])
    fend = []
    for s in (-1, 1):
        ar = [(0.7 * math.cos(math.radians(a)), 0.55 + 0.7 * math.sin(math.radians(a))) for a in np.linspace(10, 170, 12)]
        ai = [(0.62 * math.cos(math.radians(a)), 0.55 + 0.62 * math.sin(math.radians(a))) for a in np.linspace(170, 10, 12)]
        fend.append(xf(extrude(np.array(ar + ai), 0.42, bevel=0.04, seg=1), (s * 0.95, 0, 0)))
    piece(H, "Chassis", "Chassis", merge(plat, *fend), col="primary", mat="plastic", pri=0.5)
    mat_ = cbox((1.2, 0.04, 0.8), (0, 0.57, 0), c=0.01)
    piece(H, "Seat", "Chassis", mat_, col="darker", mat="rubber", role="seat", pri=0.9)
    post = merge(rod((0, 0.5, -0.25), (0, 3.2, -0.35), 0.08, segs=10), box((1.1, 0.14, 0.18), (0, 3.25, -0.35), r=0.06),
                 *[rod((s * 0.5, 3.25, -0.35), (s * 0.7, 3.25, -0.35), 0.06, segs=8) for s in (-1, 1)])
    piece(H, "Post", "Chassis", post, col="secondary", mat="metal", role="detail", pri=0.8)
    piece(H, "Headlight", "Chassis", K.lamp((0, 0.45, -0.5), 0, 0.05, shape="rect", w=0.6, h=0.1), col=LENS, mat="glass", role="light", pri=1.6, ao=False)

    def mv(pose, u):
        K.add(pose, "Chassis", (0, 0, 0, -0.12, 0, 0))

    _finish(H, wheels, 3.3, 1.6, (0, 0.6, 0), (1.0, 0.1, 0.7), (0, 1.0, -0.8), (0, 0.5, 0.6), roll=0.3, sym=5, attack="honk", extra_move=mv)
    return H


# ==================================================================================================== quad + snow
@hero("atv", FAM)
def atv():
    H = _new("atv", pv("#C1121F", "#1B1B1B"))
    H.bone("Chassis", "Body", (0, 0.9, 0))
    wheels, steer = K.add_wheels(H, K.four_wheels(1.15, -1.35, 1.15, 1.35, 0.62, 0.6, 0.66, 0.7), rim="steel", rim_col="metal", knobby=0.08, lugs=14)
    bp = round_poly(np.array([(-2.1, 1.0), (-2.0, 1.5), (-1.2, 1.75), (-0.6, 1.5), (0.7, 1.55), (1.3, 1.8), (2.1, 1.6), (2.1, 1.0)]), [0.1, 0.2, 0.3, 0.2, 0.2, 0.3, 0.15, 0.1], 3)
    body = warp(extrude(bp, 1.5, bevel=0.15, seg=2), _round_x(1.5, 1.0, 1.8, 0.25))
    fends = []
    for z in (-1.35, 1.35):
        for s in (-1, 1):
            ar = [(z + 0.85 * math.cos(math.radians(a)), 0.65 + 0.85 * math.sin(math.radians(a))) for a in np.linspace(15, 165, 12)]
            ai = [(z + 0.75 * math.cos(math.radians(a)), 0.65 + 0.75 * math.sin(math.radians(a))) for a in np.linspace(165, 15, 12)]
            fends.append(xf(extrude(np.array(ar + ai), 0.8, bevel=0.06, seg=1), (s * 1.1, 0, 0)))
    piece(H, "Chassis", "Chassis", merge(body, *fends), col="primary", mat="plastic", pri=0.5)
    sp = round_poly(np.array([(-0.55, 1.5), (-0.5, 1.8), (0.9, 1.85), (1.05, 1.55)]), 0.12, 2)
    seat = warp(extrude(sp, 0.75, bevel=0.15, seg=2), _round_x(0.75, 1.5, 1.85, 0.3))
    piece(H, "Seat", "Chassis", seat, col="secondary", mat="cloth", role="seat", pri=0.8)
    H.bone("Bars", "Chassis", (0, 1.9, -0.8))
    bars = merge(rod((0, 1.6, -0.75), (0, 2.1, -0.85), 0.06, segs=8), rod((-0.7, 2.15, -0.75), (0.7, 2.15, -0.75), 0.045, segs=6),
                 *[rod((s * 0.5, 2.15, -0.75), (s * 0.75, 2.15, -0.75), 0.06, segs=8) for s in (-1, 1)])
    piece(H, "Handlebars", "Bars", bars, col="darker", mat="metal", role="detail", pri=1.0)
    racks = []
    for z0, z1 in ((-2.2, -1.2), (1.3, 2.2)):
        for x in (-0.6, 0.6):
            racks.append(rod((x, 1.85, z0), (x, 1.85, z1), 0.035, segs=5))
        for z in np.linspace(z0, z1, 3):
            racks.append(rod((-0.6, 1.85, z), (0.6, 1.85, z), 0.03, segs=5))
    eng = merge(box((0.7, 0.55, 0.8), (0, 0.85, 0.0), r=0.08), K.tube_ring(0.08, 0.06, 0.8, axis="z", pos=(0.45, 1.2, 2.0)))
    piece(H, "Racks", "Chassis", merge(*racks), col="darker", mat="metal", role="detail", pri=1.4)
    piece(H, "Engine", "Chassis", eng, col="metal", mat="metal", role="detail", pri=1.3)
    K.lamp_pair(H, "Headlight", "Chassis", (0.4, 1.45, -2.08), r=0.14, depth=0.1)
    _finish(H, wheels, 2.2, 4.4, (0, 1.9, 0.25), (0.7, 0.2, 1.0), (0, 1.2, -2.3), (0.45, 1.2, 2.4), steer=steer + ["Bars"], roll=1.0, sym=8)
    return H


@hero("snowmobile", FAM)
def snowmobile():
    H = _new("snowmobile", pv("#FFD60A", "#1B1B1B"))
    H.bone("Chassis", "Body", (0, 0.7, 0))
    wheels = []
    belt = K.track_loop(0.0, 2.4, 0.0, 0.32, 0.35, 1.1, cleats=22)
    piece(H, "Track", "Chassis", belt, col="tyre", mat="rubber", role="wheel", pri=0.9)
    for z, r, nm in ((0.0, 0.3, "Drive"), (2.4, 0.33, "Idler")):
        b = H.bone(nm, "Chassis", (0, r + 0.02, z))
        piece(H, nm, b, K.road_wheel(r * 0.85, 1.0, (0, r + 0.02, z)), col="steel", mat="metal", role="wheel", pri=1.4)
        wheels.append((b, r))
    hood = round_poly(np.array([(-2.3, 0.75), (-2.35, 0.95), (-1.4, 1.5), (-0.6, 1.75), (0.0, 1.45), (0.0, 0.7)]), [0.15, 0.3, 0.4, 0.2, 0.1, 0.1], 3)
    hd = warp(extrude(hood, 1.5, bevel=0.2, seg=2), lambda V: np.column_stack([V[:, 0] * np.interp(V[:, 2], [-2.4, -1.4, 0], [0.55, 0.95, 1.0]) * (1 - 0.15 * np.clip((V[:, 1] - 1.2) / 0.5, 0, 1)), V[:, 1], V[:, 2]]))
    tail = round_poly(np.array([(0.0, 0.75), (0.0, 1.1), (2.6, 1.0), (2.7, 0.8)]), 0.1, 2)
    tl = extrude(tail, 1.3, bevel=0.1, seg=2)
    piece(H, "Chassis", "Chassis", merge(hd, tl), col="primary", mat="plastic", pri=0.5)
    ws = box((1.0, 0.55, 0.04), (0, 1.95, -0.55), r=0.08, rot_=(-40, 0, 0))
    piece(H, "Glass", "Chassis", ws, col="glass", mat="glass", role="window", pri=1.3, tr=0.3, ao=False)
    sp = round_poly(np.array([(0.05, 1.05), (0.1, 1.4), (2.0, 1.4), (2.15, 1.05)]), 0.12, 2)
    seat = warp(extrude(sp, 0.8, bevel=0.15, seg=2), _round_x(0.8, 1.05, 1.4, 0.3))
    piece(H, "Seat", "Chassis", seat, col="secondary", mat="cloth", role="seat", pri=0.8)
    for s, tag in ((1, "R"), (-1, "L")):
        b = H.bone("Ski" + tag, "Chassis", (s * 0.85, 0.5, -1.6))
        ski = merge(xf(extrude(round_poly(np.array([(-2.4, 0.35), (-2.1, 0.08), (-0.9, 0.03), (-0.9, 0.11), (-2.05, 0.16), (-2.3, 0.42)]), [0.1, 0.15, 0.03, 0.03, 0.1, 0.05], 3), 0.3, bevel=0.03, seg=1), (s * 0.85, 0, 0)),
                    rod((s * 0.85, 0.15, -1.6), (s * 0.55, 0.85, -1.4), 0.06, segs=8))
        piece(H, "Ski" + tag, b, ski, col="darker", mat="plastic", role="detail", pri=1.0)
    H.bone("Bars", "Chassis", (0, 1.7, -0.3))
    bars = merge(rod((0, 1.45, -0.4), (0, 1.85, -0.3), 0.06, segs=8), rod((-0.65, 1.9, -0.25), (0.65, 1.9, -0.25), 0.045, segs=6),
                 *[rod((s * 0.45, 1.9, -0.25), (s * 0.7, 1.9, -0.25), 0.06, segs=8) for s in (-1, 1)])
    piece(H, "Handlebars", "Bars", bars, col="darker", mat="metal", role="detail", pri=1.0)
    K.lamp_pair(H, "Headlight", "Chassis", (0.35, 1.2, -1.85), shape="rect", w=0.35, h=0.15, depth=0.12)
    piece(H, "Taillight", "Chassis", K.lamp((0, 0.95, 2.7), 0, 0.06, axis="+z", shape="rect", w=0.5, h=0.12), col=RED_L, mat="glass", role="light", pri=1.6, ao=False)
    _finish(H, wheels, 2.2, 5.0, (0, 1.45, 0.8), (0.75, 0.2, 1.4), (0, 0.9, -2.5), (0.4, 0.8, 2.7), steer=("SkiR", "SkiL", "Bars"), roll=1.2, sym=8)
    return H


def _runner_clips(H, height, length, bone="Chassis"):
    """Runner vehicles (no wheels): glide with a gentle sway; ram lunge attack."""
    def move(t):
        u = t / 1.0
        return {bone: (0, 0.03 * math.sin(TAU * u * 2), 0, 0.02 * math.sin(TAU * u * 2), 0.03 * math.sin(TAU * u), 0.05 * math.sin(TAU * u))}

    def idle(t):
        u = t / 3.0
        return {bone: (0, 0.01 * math.sin(TAU * u), 0, 0.01 * math.sin(TAU * u), 0, 0.01 * math.sin(TAU * u * 2))}

    def atk(t):
        s = t / 0.8
        return {bone: (0, 0.3 * K._bump(s, 0.2, 0.6), length * (0.08 * K._bump(s, 0, 0.3) - 0.25 * K._bump(s, 0.25, 0.7)), -0.1 * K._bump(s, 0.25, 0.65), 0, 0)}

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1))
        return {bone: (0, 0.05 * k, 0.1 * length * k, 0.1 * k, 0, 0.1 * math.sin(t * 35) * k)}

    H.clip("Move", 1.0, move, keys=16)
    H.clip("Idle", 3.0, idle, keys=16)
    H.clip("Attack", 0.8, atk, keys=14, loop=False)
    H.clip("Hit", 0.45, hit, keys=10, loop=False)
    H.rig["height"] = height


def _runners(z0, z1, x, curl=0.7, h=0.12, col_y=0.0, w=0.12, posts=3, top=0.8):
    m = []
    for s in (-1, 1):
        pts = [(z0 + 0.4, col_y), (z1, col_y), (z1 + 0.2, col_y + 0.15)]
        outer = [(z0 + 0.4, col_y)] + [(z0 + 0.4 - curl * math.sin(a) * 0.9, col_y + curl - curl * math.cos(a)) for a in np.linspace(0.3, math.pi * 0.95, 8)] + [(z0 + 0.55, col_y + curl * 1.9)]
        outer = [(z1 + 0.15, col_y + 0.12), (z1, col_y)] + [(z0 + 0.4, col_y)]
        arc = [(z0 + 0.4 - curl * math.sin(a), col_y + curl - curl * math.cos(a)) for a in np.linspace(0.2, math.pi * 1.1, 9)]
        path = [(z1 + 0.15, col_y + 0.15), (z1, col_y)] + arc
        for a, b in zip(path[:-1], path[1:]):
            m.append(rod((s * x, a[1] + w, a[0]), (s * x, b[1] + w, b[0]), w, segs=8, ext=w * 0.5))
        for z in np.linspace(z0 + 0.6, z1 - 0.3, posts):
            m.append(rod((s * x, col_y + w, z), (s * x * 0.95, top, z), w * 0.7, segs=6))
    return merge(*m)


@hero("sled", FAM)
def sled():
    H = _new("sled", pv("#9C6644", "#C1121F"), gait="drive")
    H.bone("Chassis", "Body", (0, 0.4, 0))
    run = _runners(-1.6, 1.6, 0.65, curl=0.35, w=0.06, posts=3, top=0.55)
    piece(H, "Runners", "Chassis", run, col="red", mat="metal", role="detail", pri=0.8)
    slats = merge(*[box((1.55, 0.08, 0.3), (0, 0.58, z), r=0.03) for z in np.linspace(-1.35, 1.35, 7)], *[cbox((0.12, 0.1, 3.0), (s * 0.55, 0.5, 0), c=0.02) for s in (-1, 1)],
                  box((1.6, 0.12, 0.2), (0, 0.6, -1.65), r=0.04))
    piece(H, "Chassis", "Chassis", slats, col="primary", mat="wood", pri=0.5)
    rope = merge(rod((-0.6, 0.62, -1.7), (0, 0.5, -2.4), 0.03, segs=4), rod((0.6, 0.62, -1.7), (0, 0.5, -2.4), 0.03, segs=4))
    piece(H, "Rope", "Chassis", rope, col=[0.85, 0.75, 0.55], mat="cloth", role="detail", pri=1.6)
    seat = cbox((1.2, 0.05, 1.6), (0, 0.65, 0.4), c=0.02)
    piece(H, "Seat", "Chassis", seat, col="secondary", mat="cloth", role="seat", pri=1.0)
    K.mount(H, "Seat", (0, 0.7, 0.4), (1.2, 0.1, 1.6), "Chassis")
    H.socket("head", (0, 1.0, 0), "Chassis")
    H.socket("mouth", (0, 0.5, -2.0), "Chassis")
    H.socket("exhaust", (0, 0.5, 1.7), "Chassis")
    H.rig.update({"head": "Chassis"})
    _runner_clips(H, 1.0, 3.4)
    return H


@hero("horse sleigh", FAM)
def sleigh():
    H = _new("horse sleigh", pv("#B5121B", "#E9C46A"))
    H.bone("Chassis", "Body", (0, 0.6, 0))
    run = _runners(-2.4, 2.2, 1.0, curl=0.9, w=0.08, posts=3, top=0.85)
    piece(H, "Runners", "Chassis", run, col="gold", mat="metal", role="detail", pri=0.8)
    bp = round_poly(np.array([(-2.0, 0.85), (-2.5, 1.6), (-2.75, 2.3), (-2.45, 2.55), (-2.2, 2.1), (-1.6, 1.55), (0.5, 1.55), (1.2, 2.6), (2.0, 3.1), (2.45, 2.85),
                              (2.3, 2.3), (2.0, 0.85)]), [0.1, 0.4, 0.3, 0.25, 0.3, 0.2, 0.3, 0.4, 0.3, 0.25, 0.2, 0.1], 3)
    body = warp(extrude(bp, 2.2, bevel=0.15, seg=2), lambda V: np.column_stack([V[:, 0] * (1 + 0.1 * np.clip((V[:, 1] - 1.0) / 1.5, 0, 1)), V[:, 1], V[:, 2]]))
    piece(H, "Chassis", "Chassis", body, col="primary", mat="wood", pri=0.5)
    trim = merge(*[K.torus(0.25, 0.05, "x", 14, 4, pos=(s * 1.18, 2.35, -2.45)) for s in (-1, 1)], *[K.torus(0.3, 0.05, "x", 14, 4, pos=(s * 1.24, 2.75, 2.15)) for s in (-1, 1)],
                 *[cbox((0.05, 0.08, 3.6), (s * 1.12, 1.55, 0.0), c=0.02) for s in (-1, 1)])
    piece(H, "Trim", "Chassis", trim, col="gold", mat="metal", role="detail", pri=1.2)
    seat = merge(box((2.0, 0.35, 1.3), (0, 1.75, 0.95), r=0.12), box((2.0, 1.1, 0.3), (0, 2.25, 1.55), r=0.12, rot_=(10, 0, 0)),
                 box((1.9, 0.3, 1.0), (0, 1.75, -0.8), r=0.12))
    piece(H, "Seat", "Chassis", seat, col="secondary", mat="cloth", role="seat", pri=0.9)
    bells = merge(*[K.D.revolve([(0, 0), (0.02, 0.12), (0.15, 0.14), (0.2, 0)], segs=10, axis=1, spline=2) for _ in range(0)])
    bl = merge(*[xf(K.lathe_profile([(-0.12, 0), (-0.12, 0.14), (0.02, 0.13), (0.1, 0.06), (0.12, 0)], 10, "y"), (s * 1.25, 1.2, z)) for s in (-1, 1) for z in (-1.4, -0.6)])
    piece(H, "Bells", "Chassis", bl, col="gold", mat="metal", role="detail", pri=1.8)
    K.mount(H, "Seat", (0, 1.95, 0.95), (1.8, 0.2, 1.1), "Chassis")
    H.socket("head", (0, 3.2, 0), "Chassis")
    H.socket("mouth", (0, 1.5, -2.8), "Chassis")
    H.socket("exhaust", (0, 1.5, 2.5), "Chassis")
    H.rig.update({"head": "Chassis"})
    _runner_clips(H, 3.1, 5.0)
    return H


# ==================================================================================================== drawn vehicles
def _shafts(z0, length=2.6, x=0.7, y=1.1):
    return merge(*[rod((s * x, y, z0), (s * x * 0.85, y - 0.1, z0 - length), 0.06, segs=6) for s in (-1, 1)], rod((-x * 0.85, y - 0.1, z0 - length + 0.3), (x * 0.85, y - 0.1, z0 - length + 0.3), 0.05, segs=6))


def _cart_wheels(H, specs, spokes=12, rim_col="darkWood", tyre_col="metal"):
    wheels = []
    for nm, pos, r, w in specs:
        b = H.bone(nm, "Body", pos)
        side = 1 if pos[0] >= 0 else -1
        m = K.rim(r, w, "cart", spokes, segs=24)
        band = K.lathe_profile([(-w * 0.55, r * 0.98), (w * 0.55, r * 0.98), (w * 0.55, r * 1.06), (-w * 0.55, r * 1.06)], 24, "x", closed=True, hard_deg=40)
        if side < 0:
            m, band = mirror(m), mirror(band)
        piece(H, nm + "Rim", b, xf(m, pos), col=rim_col, mat="wood", role="wheel", pri=1.0, fallback="Cylinder")
        piece(H, nm + "Tyre", b, xf(band, pos), col=tyre_col, mat="metal", role="wheel", pri=1.2, fallback="Cylinder")
        wheels.append((nm, r))
    return wheels


@hero("wagon", FAM)
def wagon():
    """Kid's red pull wagon."""
    H = _new("wagon", pv("#C1121F", "#F5F5F5"))
    H.bone("Chassis", "Body", (0, 0.35, 0))
    wheels, steer = K.add_wheels(H, K.four_wheels(0.85, -1.1, 0.85, 1.1, 0.33, 0.22), rim="disc", rim_col="white", grooves=False)
    tub = merge(box((1.6, 0.12, 3.0), (0, 0.72, 0), r=0.04), *[box((0.1, 0.55, 3.0), (s * 0.8, 1.0, 0), r=0.04) for s in (-1, 1)],
                *[box((1.6, 0.55, 0.1), (0, 1.0, z), r=0.04) for z in (-1.5, 1.5)])
    piece(H, "Chassis", "Chassis", tub, col="primary", mat="metal", pri=0.5)
    rim_ = merge(*[cbox((0.16, 0.06, 3.1), (s * 0.82, 1.3, 0), c=0.02) for s in (-1, 1)], *[cbox((1.7, 0.06, 0.16), (0, 1.3, z), c=0.02) for z in (-1.52, 1.52)])
    piece(H, "Trim", "Chassis", rim_, col="secondary", mat="metal", role="detail", pri=1.3)
    H.bone("Handle", "Chassis", (0, 0.4, -1.55))
    hd = merge(rod((0, 0.4, -1.55), (0, 1.1, -3.0), 0.04, segs=6), K.torus(0.15, 0.04, "x", 12, 4, pos=(0, 1.2, -3.1)))
    piece(H, "HandleP", "Handle", hd, col="darker", mat="metal", role="detail", pri=1.2)
    seat = cbox((1.4, 0.04, 2.6), (0, 0.8, 0), c=0.01)
    piece(H, "Seat", "Chassis", seat, col="darker", mat="cloth", role="seat", pri=1.4)

    def mv(p, u):
        K.add(p, "Handle", (0, 0, 0, 0.05 * math.sin(TAU * u * 2), 0.1 * math.sin(TAU * u), 0))

    _finish(H, wheels, 1.3, 3.2, (0, 0.85, 0), (1.4, 0.1, 2.6), (0, 0.8, -1.7), (0, 0.8, 1.6), steer=steer, sym=8, attack="honk", extra_move=mv)
    return H


@hero("cart", FAM)
def cart():
    H = _new("cart", pv("#8B5A2B", "#5A3820"))
    H.bone("Chassis", "Body", (0, 1.2, 0))
    wheels = _cart_wheels(H, [("WheelR", (1.25, 1.1, 0.2), 1.1, 0.16), ("WheelL", (-1.25, 1.1, 0.2), 1.1, 0.16)], spokes=10)
    bed = merge(box((2.2, 0.15, 3.0), (0, 1.35, 0.2), r=0.04), *[box((0.12, 0.6, 3.0), (s * 1.05, 1.7, 0.2), r=0.03) for s in (-1, 1)],
                box((2.2, 0.6, 0.12), (0, 1.7, 1.65), r=0.03), box((2.2, 0.6, 0.12), (0, 1.7, -1.25), r=0.03))
    piece(H, "Chassis", "Chassis", bed, col="primary", mat="wood", pri=0.5)
    planks = merge(*[cbox((0.04, 0.03, 2.9), (s * 1.12, y, 0.2), c=0.01) for s in (-1, 1) for y in (1.55, 1.8)], rod((-1.25, 1.1, 0.2), (1.25, 1.1, 0.2), 0.08, segs=8), _shafts(-1.3, 2.6, 0.7, 1.35))
    piece(H, "Shafts", "Chassis", planks, col="secondary", mat="wood", role="detail", pri=1.0)
    seat = box((2.0, 0.15, 0.6), (0, 2.05, -0.9), r=0.05)
    piece(H, "Seat", "Chassis", seat, col="secondary", mat="wood", role="seat", pri=0.9)
    hay = K.box((1.8, 0.5, 1.6), (0, 1.75, 0.65), r=0.2, seg=1)
    hay = warp(hay, lambda V: np.column_stack([V[:, 0], V[:, 1] + 0.12 * np.sin(V[:, 0] * 5) * np.sin(V[:, 2] * 4) * (V[:, 1] > 1.8), V[:, 2]]))
    piece(H, "Load", "Chassis", hay, col=[0.86, 0.74, 0.4], mat="cloth", role="detail", pri=1.6)
    _finish(H, wheels, 2.3, 5.5, (0, 2.2, -0.9), (1.8, 0.15, 0.5), (0, 1.3, -3.9), (0, 1.3, 1.8), sym=10)
    return H


@hero("covered wagon", FAM)
def covered_wagon():
    H = _new("covered wagon", pv("#8B5A2B", "#F3ECDD"))
    H.bone("Chassis", "Body", (0, 1.2, 0))
    wheels = _cart_wheels(H, [("WheelFR", (1.35, 0.85, -1.9), 0.85, 0.16), ("WheelFL", (-1.35, 0.85, -1.9), 0.85, 0.16),
                              ("WheelBR", (1.4, 1.15, 1.9), 1.15, 0.16), ("WheelBL", (-1.4, 1.15, 1.9), 1.15, 0.16)], spokes=12)
    bed = merge(box((2.4, 0.15, 5.0), (0, 1.45, 0), r=0.04), *[box((0.12, 0.85, 5.0), (s * 1.15, 1.95, 0), r=0.03) for s in (-1, 1)],
                box((2.4, 0.85, 0.12), (0, 1.95, 2.45), r=0.03), box((2.4, 0.85, 0.12), (0, 1.95, -2.45), r=0.03))
    piece(H, "Chassis", "Chassis", bed, col="primary", mat="wood", pri=0.5)
    # canvas bonnet: an arch extruded along z, flared at the ends
    arch = [(1.2 * math.cos(a), 2.35 + 1.75 * math.sin(a)) for a in np.linspace(0, math.pi, 14)]
    arch_i = [(1.12 * math.cos(a), 2.35 + 1.67 * math.sin(a)) for a in np.linspace(math.pi, 0, 14)]
    cov = extrude(np.array(arch + arch_i), 4.4, bevel=0.03, axis="z", seg=1)
    cov = warp(cov, lambda V: np.column_stack([V[:, 0] * (1 + 0.12 * (np.abs(V[:, 2]) / 2.2) ** 2), 2.35 + (V[:, 1] - 2.35) * (1 + 0.1 * (np.abs(V[:, 2]) / 2.2) ** 2), V[:, 2]]))
    piece(H, "Canvas", "Chassis", cov, col="secondary", mat="cloth", role="body", pri=0.6)
    hoops = merge(*[xf(K.torus(1.2, 0.05, "z", 16, 4), (0, 2.35, z)) for z in (-2.2, 0.0, 2.2)])
    hoops = warp(hoops, lambda V: np.column_stack([V[:, 0] * (1 + 0.12 * (np.abs(V[:, 2]) / 2.2) ** 2) * 1.02, np.maximum(V[:, 1], 2.3) + (np.maximum(V[:, 1], 2.3) - 2.35) * 0.5, V[:, 2]]))
    seat = box((2.2, 0.15, 0.6), (0, 2.5, -2.75), r=0.05)
    piece(H, "Seat", "Chassis", merge(seat, cbox((2.2, 0.6, 0.1), (0, 2.75, -2.45), c=0.03)), col="secondary", mat="wood", role="seat", pri=0.9)
    gear = merge(_shafts(-2.5, 2.5, 0.25, 1.1), rod((-1.4, 0.85, -1.9), (1.4, 0.85, -1.9), 0.08, segs=8), rod((-1.45, 1.15, 1.9), (1.45, 1.15, 1.9), 0.08, segs=8),
                 cyl(0.5, 0.3, (1.3, 2.0, 2.0), "y", segs=12))
    piece(H, "Shafts", "Chassis", gear, col="darkWood", mat="wood", role="detail", pri=1.1)
    _finish(H, wheels, 4.1, 7.5, (0, 2.65, -2.75), (2.0, 0.15, 0.5), (0, 1.3, -5.0), (0, 1.5, 2.6), sym=12)
    return H


@hero("horse carriage", FAM)
def horse_carriage():
    H = _new("horse carriage", pv("#1D1F3A", "#E9C46A"))
    H.bone("Chassis", "Body", (0, 1.2, 0))
    wheels = _cart_wheels(H, [("WheelFR", (1.35, 0.85, -1.9), 0.85, 0.14), ("WheelFL", (-1.35, 0.85, -1.9), 0.85, 0.14),
                              ("WheelBR", (1.45, 1.2, 1.9), 1.2, 0.14), ("WheelBL", (-1.45, 1.2, 1.9), 1.2, 0.14)], spokes=14, rim_col="gold", tyre_col="darker")
    cp = round_poly(np.array([(-1.4, 1.6), (-1.6, 2.6), (-1.45, 4.3), (1.45, 4.3), (1.6, 2.6), (1.4, 1.6)]), [0.3, 0.3, 0.25, 0.25, 0.3, 0.3], 4)
    coach = warp(extrude(cp, 2.4, bevel=0.15, seg=2), lambda V: np.column_stack([V[:, 0] * (1 - 0.1 * ((V[:, 1] - 2.8) / 1.5) ** 2), V[:, 1], V[:, 2]]))
    roof = K.box((2.6, 0.2, 3.4), (0, 4.4, 0), r=0.1, seg=1)
    piece(H, "Chassis", "Chassis", merge(coach, roof), col="primary", mat="wood", pri=0.5)
    wins = merge(*[cbox((0.05, 0.9, 0.9), (s * 1.22, 3.35, 0.0), c=0.03) for s in (-1, 1)], cbox((1.4, 0.8, 0.05), (0, 3.4, -1.62), c=0.03))
    piece(H, "Glass", "Chassis", wins, col="glass", mat="glass", role="window", pri=1.2)
    trim = merge(*[cbox((0.06, 0.08, 3.0), (s * 1.24, y, 0), c=0.02) for s in (-1, 1) for y in (2.3, 3.95)], *[cbox((0.06, 1.1, 1.1), (s * 1.215, 3.35, 0.0), c=0.03) for s in (-1, 1)],
                 xf(K.lathe_profile([(0, 0.25), (0.25, 0.15), (0.45, 0.0)], 10, "y"), (0, 4.5, 0)), *[K.torus(0.12, 0.03, "z", 10, 4, pos=(x, 4.62, z)) for x in (-1.1, 1.1) for z in (-1.5, 1.5)])
    piece(H, "Trim", "Chassis", trim, col="gold", mat="metal", role="detail", pri=1.0)
    lant = merge(*[merge(cbox((0.22, 0.35, 0.22), (s * 1.4, 3.6, -1.55), c=0.04), rod((s * 1.25, 3.4, -1.55), (s * 1.4, 3.45, -1.55), 0.03, segs=4)) for s in (-1, 1)])
    piece(H, "Lanterns", "Chassis", lant, col=[1.0, 0.85, 0.45], mat="glass", role="light", pri=1.6, ao=False)
    seat = merge(box((2.2, 0.2, 0.7), (0, 3.0, -2.25), r=0.06), box((2.2, 0.6, 0.12), (0, 3.25, -1.9), r=0.05), box((1.8, 0.8, 1.0), (0, 2.5, -2.2), r=0.1))
    piece(H, "Seat", "Chassis", seat, col="secondary", mat="cloth", role="seat", pri=0.9)
    gear = merge(_shafts(-2.6, 2.3, 0.3, 1.2), rod((-1.4, 0.85, -1.9), (1.4, 0.85, -1.9), 0.08, segs=8), rod((-1.5, 1.2, 1.9), (1.5, 1.2, 1.9), 0.08, segs=8),
                 *[bar((s * 0.9, 1.4, -2.0), (s * 0.9, 1.6, 1.8), 0.12, 0.15) for s in (-1, 1)])
    piece(H, "Shafts", "Chassis", gear, col="darker", mat="metal", role="detail", pri=1.1)
    _finish(H, wheels, 4.6, 7.0, (0, 3.15, -2.25), (2.0, 0.2, 0.6), (0, 1.4, -5.0), (0, 1.5, 2.2), sym=14)
    return H


@hero("chariot", FAM)
def chariot():
    H = _new("chariot", pv("#C9A227", "#8B1E1E"))
    H.bone("Chassis", "Body", (0, 1.1, 0))
    wheels = _cart_wheels(H, [("WheelR", (1.35, 1.05, 0.5), 1.05, 0.16), ("WheelL", (-1.35, 1.05, 0.5), 1.05, 0.16)], spokes=6, rim_col="gold", tyre_col="darker")
    spikes = merge(*[xf(K.lathe_profile([(0, 0.12), (0.7, 0.0)], 8, "x"), (s * 1.55, 1.05, 0.5)) for s in (1,)])
    sp = merge(xf(K.lathe_profile([(0.0, 0.14), (0.75, 0.0)], 8, "x"), (1.5, 1.05, 0.5)), xf(K.lathe_profile([(-0.75, 0.0), (0.0, 0.14)], 8, "x"), (-1.5, 1.05, 0.5)))
    piece(H, "Spikes", "Chassis", sp, col="metal", mat="metal", role="detail", pri=1.2)
    bp = round_poly(np.array([(-0.9, 1.3), (-1.2, 2.2), (-0.9, 2.6), (0.2, 2.1), (1.0, 1.9), (1.1, 1.3)]), [0.1, 0.3, 0.2, 0.2, 0.1, 0.1], 3)
    body = warp(extrude(bp, 2.2, bevel=0.12, seg=2), lambda V: np.column_stack([V[:, 0] * np.interp(V[:, 2], [-1.2, -0.3, 1.1], [0.6, 1.0, 1.0]), V[:, 1], V[:, 2]]))
    piece(H, "Chassis", "Chassis", body, col="primary", mat="metal", pri=0.5)
    orn = merge(*[cbox((0.05, 0.12, 1.6), (s * 1.08, 1.9, 0.2), c=0.02) for s in (-1, 1)], cyl(0.06, 0.35, (0, 2.0, -1.05), "z", segs=14, r=(-25, 0, 0)))
    piece(H, "Trim", "Chassis", orn, col="secondary", mat="metal", role="detail", pri=1.2)
    floor = box((2.0, 0.12, 2.0), (0, 1.35, 0.15), r=0.04)
    piece(H, "Seat", "Chassis", floor, col="darkWood", mat="wood", role="seat", pri=0.9)
    pole = merge(rod((0, 1.3, -0.9), (0, 1.6, -3.8), 0.08, segs=8), rod((-1.0, 1.6, -3.6), (1.0, 1.6, -3.6), 0.06, segs=6), rod((-1.4, 1.05, 0.5), (1.4, 1.05, 0.5), 0.08, segs=8))
    piece(H, "Pole", "Chassis", pole, col="darkWood", mat="wood", role="detail", pri=1.1)
    _finish(H, wheels, 2.6, 5.0, (0, 1.45, 0.15), (1.6, 0.1, 1.5), (0, 1.5, -4.0), (0, 1.5, 1.2), sym=6)
    return H


@hero("rickshaw", FAM)
def rickshaw():
    H = _new("rickshaw", pv("#2A9D8F", "#E9C46A"))
    H.bone("Chassis", "Body", (0, 1.1, 0))
    H.bone("Fork", "Chassis", (0, 2.1, -2.35))
    H.bone("WheelF", "Fork", (0, 0.65, -2.5))
    _wire_wheel(H, "WheelF", "WheelF", (0, 0.65, -2.5), 0.65, w=0.1, spokes=28)
    wheels = [("WheelF", 0.65)]
    for s, tag in ((1, "R"), (-1, "L")):
        b = H.bone("WheelB" + tag, "Body", (s * 1.25, 0.65, 0.6))
        _wire_wheel(H, "WheelB" + tag, b, (s * 1.25, 0.65, 0.6), 0.65, w=0.1, spokes=28)
        wheels.append((b, 0.65))
    fr = merge(rod((0, 2.0, -2.3), (0, 1.0, -1.0), 0.07, segs=8), rod((0, 1.0, -1.0), (0, 2.25, -1.2), 0.06, segs=8), rod((0, 1.0, -1.0), (0, 0.9, 0.2), 0.07, segs=8),
               rod((-1.25, 0.65, 0.6), (1.25, 0.65, 0.6), 0.06, segs=8))
    piece(H, "Frame", "Chassis", fr, col="darker", mat="metal", role="detail", pri=0.9)
    bp = round_poly(np.array([(-0.3, 0.9), (-0.6, 1.4), (-0.2, 1.55), (0.9, 1.55), (1.0, 2.6), (1.25, 2.6), (1.2, 0.9)]), [0.1, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1], 3)
    body = extrude(bp, 2.1, bevel=0.12, seg=2)
    piece(H, "Chassis", "Chassis", body, col="primary", mat="metal", pri=0.5)
    bench = merge(box((1.9, 0.25, 0.85), (0, 1.7, 0.45), r=0.1), box((1.9, 0.9, 0.2), (0, 2.15, 0.95), r=0.08, rot_=(10, 0, 0)))
    piece(H, "Bench", "Chassis", bench, col="secondary", mat="cloth", role="seat", pri=0.9)
    hood = [(1.15 * math.cos(a), 2.6 + 1.1 * math.sin(a)) for a in np.linspace(0, math.pi, 12)]
    hood_i = [(1.08 * math.cos(a), 2.6 + 1.03 * math.sin(a)) for a in np.linspace(math.pi, 0, 12)]
    hd = xf(extrude(np.array(hood + hood_i), 1.2, bevel=0.03, axis="z", seg=1), (0, 0, 0.6))
    piece(H, "Canopy", "Chassis", hd, col="secondary", mat="cloth", role="detail", pri=0.8)
    sd = K.D.revolve([(-0.3, 0), (-0.25, 0.1), (0.2, 0.15), (0.3, 0.05), (0.32, 0)], segs=10, axis=2, spline=2)
    sd = xf(warp(sd, lambda V: np.column_stack([V[:, 0] * 1.6, V[:, 1], V[:, 2]])), (0, 2.3, -1.15))
    piece(H, "Seat", "Chassis", merge(sd, rod((0, 2.0, -1.15), (0, 2.28, -1.15), 0.04, segs=6)), col="darker", mat="cloth", role="seat", pri=0.9)
    fk = merge(*(rod((s * 0.08, 2.1, -2.35), (s * 0.09, 0.65, -2.5), 0.035, segs=6) for s in (-1, 1)), rod((0, 2.1, -2.35), (0, 2.55, -2.2), 0.04, segs=6),
               rod((-0.45, 2.55, -2.1), (0.45, 2.55, -2.1), 0.035, segs=6))
    piece(H, "Forks", "Fork", fk, col="darker", mat="metal", role="detail", pri=0.9)
    crank = _crank(H, "Chassis", (0, 0.6, -1.0), r=0.28, side_x=0.22)

    def mv(pose, u):
        K.add(pose, "Crank", (0, 0, 0, -TAU * u, 0, 0))

    _finish(H, wheels, 3.7, 4.5, (0, 2.45, -1.15), (0.4, 0.15, 0.5), (0, 1.5, -3.2), (0, 1.0, 1.4), steer=("Fork",), sym=12, attack="honk", extra_move=mv)
    return H


# ==================================================================================================== walkers
@hero("mech suit", FAM)
def mech_walker():
    """Two-legged mech walker: armoured cockpit pod with a canopy (pilot seat shows), reverse-jointed legs with
    pistons and three-toed feet, arm cannons; biped gait with a heavy stomp, cannon recoil attack."""
    H = Hero("mech suit", plan="Biped", gait="stomp", tags=["vehicle", "mech"])
    H.preview = pv("#7D8590", "#E36414")
    H.body((0, 5.4, 0))
    cp = round_poly(np.array([(-1.9, 4.9), (-2.0, 5.9), (-1.2, 6.9), (1.2, 6.9), (1.7, 6.0), (1.5, 4.7), (-1.0, 4.5)]), [0.3, 0.4, 0.5, 0.4, 0.3, 0.3, 0.3], 3)
    pod = warp(extrude(cp, 2.8, bevel=0.3, seg=3), lambda V: np.column_stack([V[:, 0] * (1 - 0.18 * ((V[:, 1] - 5.7) / 1.2) ** 2), V[:, 1], V[:, 2]]))
    piece(H, "Hull", "Body", pod, col="primary", mat="metal", pri=0.4)
    can = K.D.revolve([(-0.9, 0), (-0.85, 0.5), (0.0, 0.75), (0.8, 0.5), (0.9, 0)], segs=20, axis=2, spline=3)
    can = xf(warp(can, lambda V: np.column_stack([V[:, 0] * 1.4, np.maximum(V[:, 1], 0) * 1.1, V[:, 2]])), (0, 6.75, -0.6))
    piece(H, "Glass", "Body", can, col="glass", mat="glass", role="window", pri=0.8, tr=0.3, ao=False)
    seat = K.seat_mesh((0, 6.8, -0.4), w=0.8, d=0.7, back=0.8)
    piece(H, "Seat", "Body", seat, col="darker", mat="cloth", role="seat", pri=1.0)
    armor = merge(*[box((0.5, 1.0, 2.2), (s * 1.45, 5.6, 0.0), r=0.15, seg=1) for s in (-1, 1)], box((1.8, 0.5, 0.4), (0, 5.0, -1.95), r=0.1),
                  *[cbox((0.08, 0.3, 0.9), (s * 1.75, 5.9, -0.2), c=0.02) for s in (-1, 1)], cbox((0.7, 0.9, 0.6), (0, 6.2, 1.8), c=0.1))
    piece(H, "Armor", "Body", armor, col="secondary", mat="metal", role="detail", pri=0.9)
    lights = merge(*[K.lamp((s * 0.6, 5.0, -2.17), 0.12, 0.08) for s in (-1, 1)])
    piece(H, "Lamps", "Body", lights, col=[1.0, 0.75, 0.3], mat="glass", role="light", pri=1.6, ao=False)
    # legs (digitigrade): hip -> knee (forward) -> ankle (back) -> foot
    legs = []
    for s, tag in ((1, "R"), (-1, "L")):
        H.bone("Hip" + tag, "Body", (s * 1.5, 4.9, 0.2))
        H.bone("Knee" + tag, "Hip" + tag, (s * 1.6, 3.2, -0.9))
        H.bone("Ankle" + tag, "Knee" + tag, (s * 1.6, 1.2, 0.6))
        H.bone("Foot" + tag, "Ankle" + tag, (s * 1.6, 0.35, 0.3))
        th = merge(bar((s * 1.55, 5.0, 0.25), (s * 1.6, 3.15, -0.9), 0.55, 0.75, r=0.12, round_=True), cyl(0.6, 0.55, (s * 1.5, 4.9, 0.2), "x", segs=16),
                   cyl(0.5, 0.42, (s * 1.6, 3.2, -0.9), "x", segs=14))
        sh = merge(bar((s * 1.6, 3.2, -0.9), (s * 1.6, 1.2, 0.6), 0.45, 0.6, r=0.1, round_=True), cyl(0.45, 0.32, (s * 1.6, 1.2, 0.6), "x", segs=12))
        pist = rod((s * 1.95, 4.4, 0.4), (s * 1.95, 2.7, -0.5), 0.09, segs=8)
        foot = merge(*[bar((s * 1.6, 0.35, 0.3), (s * 1.6 + s * dx, 0.12, -1.0 + 0.2 * abs(dx)), 0.3, 0.22, r=0.06) for dx in (-0.45, 0.0, 0.45)],
                     bar((s * 1.6, 0.35, 0.3), (s * 1.6, 0.12, 1.0), 0.3, 0.22, r=0.06), cyl(0.5, 0.3, (s * 1.6, 0.35, 0.3), "x", segs=12))
        piece(H, "Thigh" + tag, "Hip" + tag, th, col="primary", mat="metal", role="limb", pri=0.6)
        piece(H, "Shin" + tag, "Knee" + tag, merge(sh, ), col="primary", mat="metal", role="limb", pri=0.7)
        piece(H, "Piston" + tag, "Hip" + tag, pist, col="metal", mat="metal", role="detail", pri=1.4)
        piece(H, "Foot" + tag, "Ankle" + tag, foot, col="darker", mat="metal", role="foot", pri=0.8)
        legs.append(("Hip" + tag, "Knee" + tag, "Ankle" + tag, 0.0 if s > 0 else 0.5))
        # arm cannon
        H.bone("Arm" + tag, "Body", (s * 2.1, 6.0, -0.2))
        arm = merge(cyl(0.6, 0.38, (s * 2.15, 6.0, -0.2), "x", segs=14), box((0.6, 0.7, 1.6), (s * 2.45, 5.6, -0.7), r=0.12),
                    K.lathe_profile([(-2.6, 0), (-2.6, 0.18), (-1.4, 0.2), (-1.4, 0)], 12, "z"))
        arm = merge(cyl(0.6, 0.38, (s * 2.15, 6.0, -0.2), "x", segs=14), box((0.6, 0.7, 1.6), (s * 2.45, 5.6, -0.7), r=0.12, seg=1),
                    xf(K.lathe_profile([(-1.5, 0), (-1.5, 0.2), (-1.4, 0.24), (0.0, 0.24), (0.0, 0)], 12, "z"), (s * 2.45, 5.55, -1.45)),
                    xf(K.tube_ring(0.26, 0.14, 0.3, axis="z"), (s * 2.45, 5.55, -2.9)))
        piece(H, "Cannon" + tag, "Arm" + tag, arm, col="secondary", mat="metal", role="limb", pri=0.8)
    K.mount(H, "Seat", (0, 6.9, -0.4), (0.8, 0.2, 0.7), "Body")
    H.socket("head", (0, 7.6, 0), "Body")
    H.socket("mouth", (2.45, 5.55, -3.0), "ArmR")
    H.socket("muzzle", (2.45, 5.55, -3.0), "ArmR")
    H.socket("exhaust", (0, 6.5, 2.1), "Body")
    H.rig.update({"head": "Body"})
    motion.biped(H, legs, arms=[("ArmR", None, None, 1), ("ArmL", None, None, -1)], stride=0.38, walk=1.4, height=7.0, attack="punch", weapon_arm="ArmR")
    # replace the attack with a double cannon recoil + stomp
    def atk(t):
        s = t / 0.9
        p = {}
        aim = K._ease(s / 0.25) if s < 0.25 else (1 - K._ease((s - 0.75) / 0.25) if s > 0.75 else 1.0)
        K.add(p, "ArmR", (0, 0, 0.35 * K._bump(s, 0.3, 0.5), 0.15 * aim, 0, 0))
        K.add(p, "ArmL", (0, 0, 0.35 * K._bump(s, 0.5, 0.7), 0.15 * aim, 0, 0))
        K.add(p, "Body", (0, -0.15 * aim, 0.15 * K._bump(s, 0.3, 0.75), 0.04 * aim, 0, 0))
        for tag in ("R", "L"):
            K.add(p, "Knee" + tag, (0, 0, 0, -0.15 * aim, 0, 0))
            K.add(p, "Hip" + tag, (0, 0, 0, 0.08 * aim, 0, 0))
        return p

    H.clip("Attack", 0.9, atk, keys=14, loop=False)
    return H


@hero("spider walker", FAM)
def spider_walker():
    """Eight-legged walker: rounded cockpit body with a canopy and seat, four leg pairs (coxa / femur / tibia) on
    their own bones walking an alternating tetrapod gait."""
    H = Hero("spider walker", plan="Spider", gait="scuttle", tags=["vehicle", "mech"])
    H.preview = pv("#3D3D45", "#C1121F")
    H.body((0, 2.6, 0))
    bod = K.D.revolve([(-2.2, 0), (-2.0, 0.9), (-0.8, 1.35), (0.8, 1.3), (2.0, 0.9), (2.4, 0)], segs=24, axis=2, spline=3)
    bod = xf(warp(bod, lambda V: np.column_stack([V[:, 0] * 1.25, V[:, 1] * 0.75, V[:, 2]])), (0, 2.8, 0.2))
    piece(H, "Hull", "Body", bod, col="primary", mat="metal", pri=0.4)
    can = K.D.revolve([(-0.9, 0), (-0.85, 0.5), (0.0, 0.7), (0.8, 0.45), (0.9, 0)], segs=18, axis=2, spline=3)
    can = xf(warp(can, lambda V: np.column_stack([V[:, 0] * 1.2, np.maximum(V[:, 1], 0), V[:, 2]])), (0, 3.65, -0.9))
    piece(H, "Glass", "Body", can, col="glass", mat="glass", role="window", pri=0.8, tr=0.3, ao=False)
    seat = K.seat_mesh((0, 3.7, -0.7), w=0.75, d=0.65, back=0.75)
    piece(H, "Seat", "Body", seat, col="darker", mat="cloth", role="seat", pri=1.0)
    ring = merge(K.torus(1.55, 0.12, "y", 28, 5, pos=(0, 2.6, 0.2)))
    ring = warp(ring, lambda V: np.column_stack([V[:, 0] * 1.2, V[:, 1], (V[:, 2] - 0.2) * 1.3 + 0.2]))
    eyes = merge(*[K.lamp((x, 2.9, -2.1 + 0.05 * abs(x)), 0.13, 0.08) for x in (-0.6, -0.25, 0.25, 0.6)])
    piece(H, "Ring", "Body", ring, col="secondary", mat="metal", role="detail", pri=0.9)
    piece(H, "Eyes", "Body", eyes, col=[1.0, 0.25, 0.2], mat="glass", role="eye", pri=1.4, ao=False)
    legs = []
    for i, (z, ang) in enumerate(((-1.3, -50), (-0.4, -15), (0.6, 15), (1.5, 50))):
        for s, tag in ((1, "R"), (-1, "L")):
            nm = f"{i}{tag}"
            a = math.radians(ang)
            dx, dz = math.cos(a), math.sin(a)
            p0 = np.array([s * 1.5, 2.6, z])
            p1 = p0 + np.array([s * dx * 1.6, 1.1, dz * 1.6])
            p2 = p0 + np.array([s * dx * 3.3, -2.55, dz * 3.3])
            H.bone("Coxa" + nm, "Body", tuple(p0))
            H.bone("Femur" + nm, "Coxa" + nm, tuple(p1))
            fem = merge(bar(tuple(p0), tuple(p1), 0.3, 0.38, r=0.08, round_=True), cyl(0.35, 0.3, tuple(p0), "x", segs=10))
            tib = merge(bar(tuple(p1), tuple(p2 + np.array([0, 0.3, 0])), 0.24, 0.3, r=0.06, round_=True), cyl(0.3, 0.26, tuple(p1), "x", segs=10),
                        xf(K.lathe_profile([(0.0, 0.14), (0.35, 0.0)], 8, "y"), tuple(p2 + np.array([0, -0.05, 0]))))
            piece(H, "Femur" + nm, "Coxa" + nm, fem, col="primary", mat="metal", role="limb", pri=0.7 + 0.05 * i)
            piece(H, "Tibia" + nm, "Femur" + nm, tib, col="secondary", mat="metal", role="limb", pri=0.8 + 0.05 * i)
            legs.append(("Coxa" + nm, "Femur" + nm, (i + (0 if s > 0 else 1)) % 2, s))
    K.mount(H, "Seat", (0, 3.8, -0.7), (0.75, 0.2, 0.65), "Body")
    H.socket("head", (0, 4.4, 0), "Body")
    H.socket("mouth", (0, 2.8, -2.4), "Body")
    H.socket("exhaust", (0, 3.0, 2.6), "Body")
    H.rig.update({"head": "Body"})

    def move(t):
        L = 0.9
        u = t / L
        p = {}
        for cx, fe, grp, s in legs:
            ph = TAU * (u + 0.5 * grp)
            lift = max(0.0, math.sin(ph))
            K.add(p, cx, (0, 0, 0, 0, 0.28 * math.cos(ph) * s, 0))
            K.add(p, cx, (0, 0, 0, 0, 0, s * 0.3 * lift))
            K.add(p, fe, (0, 0, 0, 0, 0, -s * 0.15 * lift))
        K.add(p, "Body", (0, 0.06 * math.sin(TAU * u * 2), 0, 0, 0.03 * math.sin(TAU * u), 0.02 * math.sin(TAU * u * 2)))
        return p

    def idle(t):
        u = t / 3.0
        p = {"Body": (0, 0.05 * math.sin(TAU * u), 0, 0.02 * math.sin(TAU * u), 0, 0)}
        for cx, fe, grp, s in legs:
            K.add(p, fe, (0, 0, 0, 0, 0, s * 0.03 * math.sin(TAU * u)))
        return p

    def atk(t):
        s = t / 0.9
        rear = K._bump(s, 0.0, 0.6)
        stab = K._bump(s, 0.4, 0.85)
        p = {"Body": (0, 0.4 * rear, -0.5 * stab, 0.25 * rear - 0.15 * stab, 0, 0)}
        for cx, fe, grp, sd in legs[:2]:
            K.add(p, cx, (0, 0, 0, 0, 0, sd * (0.8 * rear - 0.4 * stab)))
            K.add(p, fe, (0, 0, 0, 0, 0, -sd * 0.5 * rear))
        return p

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1))
        return {"Body": (0, -0.2 * k, 0.3 * k, 0.15 * k, 0, 0.1 * math.sin(t * 35) * k)}

    H.clip("Move", 0.9, move, keys=20)
    H.clip("Idle", 3.0, idle, keys=16)
    H.clip("Attack", 0.9, atk, keys=14, loop=False)
    H.clip("Hit", 0.45, hit, keys=10, loop=False)
    H.rig["height"] = 4.4
    return H


L = K.LAND
MAP = [
    ("motorcycle", "motorcycle, motorbike, sidecar, hoverbike, superbike, sport bike", L),
    ("chopper motorcycle", "chopper motorcycle, chopper bike, harley", L),
    ("dirt bike", "dirt bike, motocross bike, pit bike, trail bike", L),
    ("moped", "moped, vespa, pizza scooter, motor scooter", L),
    ("scooter", "scooter, kick scooter, electric scooter, razor scooter", L),
    ("bicycle", "bicycle, bike, bikes, mountain bike, road bike, cycle, push bike, !sky bike", L),
    ("bmx", "bmx, bmx bike", L),
    ("tandem bicycle", "tandem bicycle, tandem", L),
    ("tricycle", "tricycle, trike, ice cream bike", L),
    ("unicycle", "unicycle", L),
    ("penny farthing", "penny farthing, velocipede, high wheeler", L),
    ("skateboard", "skateboard, longboard, roller skates, ice skates, skate board", L),
    # you stand on a surfboard: the hover deck (no wheels), not the canoe it used to map to
    ("hoverboard", "hoverboard, hover board, surfboard, surf board, bodyboard, boogie board, paddleboard, wakeboard", L),
    ("self balancing scooter", "self balancing scooter, segway", L),
    ("atv", "atv, quad bike, quad, four wheeler", L),
    ("snowmobile", "snowmobile, snow mobile, skidoo", L),
    ("sled", "sled, sledge, toboggan, bobsled, bobsleigh, dog sled, rocket sled, ice yacht", L),
    ("horse sleigh", "horse sleigh, troika", L),
    ("wagon", "wagon, red wagon, shopping cart, shopping cart rocket, baby stroller, stroller, pram, wheelbarrow, lemonade cart, popcorn cart, rolling cart", L),
    ("cart", "cart, oxcart, ox cart, hay wagon, catapult cart, battering ram, siege tower, handcart", L),
    ("covered wagon", "covered wagon, war wagon, vardo wagon, prairie schooner", L),
    ("horse carriage", "horse carriage, carriage, carriage pumpkin, royal carriage, steampunk carriage, stagecoach, coach and horses, pumpkin carriage, sedan chair", L),
    ("chariot", "chariot, chariot of fire, crystal chariot, dragon chariot", L),
    ("rickshaw", "rickshaw, pedicab, tuk tuk, cycle rickshaw", L),
    ("mech suit", "mech suit, mech, walker, walking house, moving castle, farmer mech, battle mech, robot suit", L),
    ("spider walker", "spider walker, crab tank, robot spider tank, spider tank", L),
]
