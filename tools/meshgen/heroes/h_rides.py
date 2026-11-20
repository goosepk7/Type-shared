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
from kit import stripes as kit_stripes
from map import VEH
import motion
import landveh_kit as K
from landveh_kit import box, cbox, cyl, bar, rod, extrude, warp, merge, mirror, xf, lamp, piece, mpiece, round_poly
import rides_kit as R
from rides_kit import loft, sweep, ball

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
    return sport_bike()


@hero("chopper motorcycle", FAM)
def chopper():
    return _moto("chopper motorcycle", zf=-2.55, rf=0.6, rb=0.62, wb=0.55, head=(2.15, -1.25), rake=45, rim="wire", spokes=28, tank="teardrop",
                 bars="ape", seat_y=1.35, chopper=True, sissy=True, preview=pv("#1A1A1A", "#C0C0C0"))


@hero("dirt bike", FAM)
def dirt_bike():
    return dirt_bike_real()


def _old_dirt_bike():
    return _moto("dirt bike", rf=0.72, rb=0.7, wf=0.26, wb=0.34, zf=-1.65, zb=1.4, head=(2.15, -1.0), rim="wire", spokes=28, knobby=0.06,
                 bars="wide", fender_hi=True, seat_y=2.05, plate=True, preview=pv("#FF7A00", "#F5F5F5"))


@hero("moped", FAM)
def moped():
    return moped_real()


def _old_moped():
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
    return kick_scooter_real()


def _old_kick_scooter():
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
    return _cycle("bicycle", "city", preview=pv("#1E88E5", "#F5F5F5", wood="#C8A165", darkWood="#8A6A3E"))


@hero("bmx", FAM)
def bmx():
    return _cycle("bmx", "bmx", preview=pv("#FF2E63", "#252A34"))


@hero("tandem bicycle", FAM)
def tandem():
    return _cycle("tandem bicycle", "tandem", preview=pv("#2A9D8F", "#F4F1DE"))


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
    return skateboard_real()


def _old_skateboard():
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
    return hoverboard_real()


def _old_hoverboard():
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
    return atv_real()


def _old_atv():
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
    return snowmobile_real()


def _old_snowmobile():
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
    return mech_suit_real()


def _old_mech_walker():
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
    return spider_walker_real()


def _old_spider_walker():
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


# ==================================================================================================== real-scale motorbikes
# Rider-relative layout (preview avatar, seated): hip = seat socket; thighs run 1.3 forward, feet rest 1.2 below the hip
# and ~0.7 forward; hands reach ~1.45 forward at hip + 1.3, 1.5 out to each side.
def _arc(zc, yc, r, a0, a1, n=12):
    """Points on a circle in the (z, y) side plane; angle 0 = +Z (back), 90 = up."""
    return [(zc + r * math.cos(math.radians(a)), yc + r * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]


def _fender(zc, yc, r_in, thick, a0, a1, width, dome=0.35, n=14):
    """Fender / mudguard shell over a wheel: an arc band extruded across X, domed so it hugs the tyre."""
    poly = np.array(_arc(zc, yc, r_in + thick, a0, a1, n) + _arc(zc, yc, r_in, a1, a0, n))
    m = extrude(poly, width, bevel=min(0.05, thick * 0.4), seg=1)

    def f(V):
        x = V[:, 0] / (width / 2)
        d = np.hypot(V[:, 2] - zc, V[:, 1] - yc)
        k = 1 - dome * x ** 2 * 0.5
        return np.column_stack([V[:, 0], yc + (V[:, 1] - yc) * k, zc + (V[:, 2] - zc) * k])

    return warp(m, f)


def _chain(x, p0, r0, p1, r1, w=0.05):
    """Drive chain on the side plane x: top and bottom runs tangent to two sprockets (z, y) of radii r0, r1."""
    (z0, y0), (z1, y1) = p0, p1
    return merge(sweep([(x, y0 + r0, z0), (x, y1 + r1, z1)], w, segs=6), sweep([(x, y0 - r0, z0), (x, y1 - r1, z1)], w, segs=6))


def _sprocket(r, teeth, x, thick=0.05):
    ring = K.tube_ring(r, r * 0.55, thick, axis="x", segs=teeth * 2)

    def f(V):
        rad = np.hypot(V[:, 1], V[:, 2])
        a = np.arctan2(V[:, 2], V[:, 1])
        k = np.clip((rad - r * 0.8) / (r * 0.2), 0, 1)
        s = (rad - r * 0.08 * k * (np.cos(a * teeth) < 0)) / np.maximum(rad, 1e-9)
        return np.column_stack([V[:, 0], V[:, 1] * s, V[:, 2] * s])

    return xf(warp(ring, f), (x, 0, 0))


def sport_bike():
    """Sport-naked roadster at real scale (7.4 studs): inverted gold forks with twin wave rotors and radial calipers,
    sculpted fuel tank with knee recesses and a raised centre stripe, half fairing with twin LED headlights and a
    smoked screen, side scoops over the radiator, twin-spar frame, inline-four with finned block and four headers
    sweeping into an under-tail-style silencer, banana swing arm with mono shock, chain drive, split seat, tail
    cowl with LED tail light, plate hanger with indicators."""
    H = _new("motorcycle", pv("#C1121F", "#1C1D21", white="#F4F4F4", metal="#B9C0C8", gold="#D9A441"))
    seat = (0.0, 2.55, 0.45)
    hy, hz = 3.42, -1.5            # top of the steering head
    rake = math.radians(25)
    dax = np.array([0, -math.cos(rake), -math.sin(rake)])
    zf, zb, rf, rb = -2.66, 2.42, 1.05, 1.08
    H.bone("Chassis", "Body", (0, 0, 0))
    H.bone("Steer", "Chassis", (0, 2.95, -1.72))
    H.bone("WheelF", "Steer", (0, rf, zf))
    H.bone("WheelB", "Chassis", (0, rb, zb))
    wheels = [R.moto_wheel(H, "WheelF", "WheelF", (0, rf, zf), rf, 0.46, style="cast", spokes=3, rim_col="darker", discs=(0.3, -0.3), disc_r=0.6),
              R.moto_wheel(H, "WheelB", "WheelB", (0, rb, zb), rb, 0.66, style="cast", spokes=3, rim_col="darker", discs=(0.36,), disc_r=0.42)]
    # rear sprocket spins with the wheel
    piece(H, "Sprocket", "WheelB", xf(_sprocket(0.46, 21, -0.4), (0, rb, zb)), col="steel", mat="metal", role="wheel", pri=1.6)

    # ---------------------------------------------------------------- steering: inverted forks, clamps, bars, fender
    def on_axis(y):
        t = (hy - y) / math.cos(rake)
        return hz - math.sin(rake) * t
    fk = []
    for s in (-1, 1):
        x = s * 0.4
        top, mid = (x, hy + 0.12, on_axis(hy + 0.12)), (x, 1.95, on_axis(1.95))
        fk.append(sweep([top, mid], 0.11, segs=14))
        fk.append(sweep([(x, 2.05, on_axis(2.05)), (x, 1.82, on_axis(1.82))], 0.125, segs=14))  # seal collar
        fk.append(cbox((0.16, 0.3, 0.3), (x, rf + 0.05, zf), c=0.04))                          # axle foot
        fk.append(R.caliper((x, rf, zf), 0.6, tilt=20) if False else K.box((0.14, 0.44, 0.22), (x * 0.92, rf + 0.35, zf + 0.48), r=0.04, rot_=(35, 0, 0)))
    fk.append(K.box((1.0, 0.13, 0.42), (0, hy + 0.04, on_axis(hy) + 0.05), r=0.05))           # top clamp
    fk.append(K.box((1.0, 0.16, 0.4), (0, 2.78, on_axis(2.78) + 0.05), r=0.05))               # bottom clamp
    fk.append(sweep([(-0.4, rf, zf), (0.4, rf, zf)], 0.05, segs=8))                            # axle
    piece(H, "Forks", "Steer", merge(*fk[:2], *fk[2:4], *fk[4:]), col="gold", mat="metal", role="detail", pri=0.8)
    stanch = merge(*[sweep([(s * 0.4, 1.95, on_axis(1.95)), (s * 0.4, rf + 0.15, on_axis(rf + 0.15))], 0.085, segs=12) for s in (-1, 1)])
    piece(H, "Stanchions", "Steer", stanch, col="metal", mat="metal", role="detail", pri=1.0)
    bars = []
    for s in (-1, 1):
        bars.append(sweep([(s * 0.18, hy + 0.12, hz + 0.05), (s * 0.6, hy + 0.2, hz + 0.3), (s * 1.0, hy + 0.27, hz + 0.5)], 0.055, segs=8))
        bars.append(cbox((0.1, 0.06, 0.42), (s * 1.0, hy + 0.3, hz + 0.25), c=0.02, rot_=(0, -s * 12, 0)))   # levers
        bars.append(K.box((0.22, 0.2, 0.22), (s * 0.72, hy + 0.27, hz + 0.42), r=0.05))                     # switch / master cylinder
    piece(H, "Bars", "Steer", merge(*bars), col="darker", mat="metal", role="detail", pri=1.0)
    grips = merge(*[sweep([(s * 0.86, hy + 0.27, hz + 0.5), (s * 1.3, hy + 0.27, hz + 0.56)], 0.075, segs=10) for s in (-1, 1)],
                  *[K.cyl(0.08, 0.085, (s * 1.36, hy + 0.27, hz + 0.57), "x", segs=10) for s in (-1, 1)])
    piece(H, "Grips", "Steer", grips, col="tyre", mat="rubber", role="detail", pri=1.2)
    ff = R.merge(_fender(zf, rf, rf + 0.08, 0.07, 30, 140, 0.56, dome=0.5))
    piece(H, "FenderF", "Steer", ff, col="primary", mat="plastic", role="detail", pri=1.1)

    # ---------------------------------------------------------------- frame, swing arm, shock
    pivot = (0.55, 1.78, 0.6)
    fr = [sweep([(0, hy + 0.08, hz + 0.02), (0, 2.66, on_axis(2.66))], 0.16, segs=14)]       # steering head
    for s in (-1, 1):
        fr.append(sweep([(s * 0.26, 3.25, hz + 0.12), (s * 0.66, 3.0, -0.75), (s * 0.66, 2.55, 0.1), (s * pivot[0], pivot[1] + 0.1, pivot[2])], 0.15, segs=12))
        fr.append(sweep([(s * 0.2, 2.7, hz - 0.05), (s * 0.55, 2.45, -0.9), (s * 0.62, 2.4, -0.3)], 0.08, segs=8))   # down brace
        fr.append(sweep([(s * 0.6, 2.62, 0.05), (s * 0.36, 2.48, 1.4), (s * 0.3, 2.6, 2.4)], 0.06, segs=8))          # subframe
        fr.append(sweep([(s * 0.6, 1.95, 0.55), (s * 0.34, 2.38, 1.6)], 0.05, segs=8))
        fr.append(K.cyl(0.18, 0.17, (s * 0.62, pivot[1], pivot[2]), "x", segs=14))                               # pivot boss
    piece(H, "Frame", "Chassis", merge(*fr), col="metal", mat="metal", role="body", pri=0.7)
    sw = []
    for s in (-1, 1):
        sw.append(sweep([(s * 0.5, pivot[1], pivot[2]), (s * 0.52, 1.52, 1.5), (s * 0.48, rb, zb)], [0.13, 0.12, 0.08], segs=10))
    sw.append(sweep([(-0.5, 1.6, 1.15), (0.5, 1.6, 1.15)], 0.07, segs=8))
    sw.append(sweep([(-0.5, rb, zb), (0.5, rb, zb)], 0.05, segs=8))
    piece(H, "Swingarm", "Chassis", merge(*sw), col="darker", mat="metal", role="detail", pri=0.9)
    shock = merge(R.spring((0, 2.45, 0.75), (0, 1.62, 1.1), 0.13, wire=0.035, turns=6), sweep([(0, 2.5, 0.73), (0, 1.58, 1.12)], 0.06, segs=8))
    piece(H, "Shock", "Chassis", shock, col="gold", mat="metal", role="detail", pri=1.6)

    # ---------------------------------------------------------------- engine: inline four
    eng = [K.box((1.12, 0.62, 1.55), (0, 1.25, -0.3), r=0.18, seg=1),            # crankcase
           K.box((0.8, 0.3, 1.0), (0, 0.85, -0.25), r=0.1),                     # sump
           xf(K.box((1.04, 0.7, 0.62), (0, 0, 0), r=0.12, seg=1), (0, 1.86, -0.92), r=(-28, 0, 0))]  # cylinder block
    for i in range(5):                                                          # cooling fins
        eng.append(xf(cbox((1.14, 0.05, 0.7), (0, 0, 0), c=0.015), (0, 1.62 + 0.1 * i, -0.8 - 0.055 * i), r=(-28, 0, 0)))
    piece(H, "Engine", "Chassis", merge(*eng), col="gunmetal", mat="metal", role="body", pri=0.8)
    cov = [xf(K.box((0.98, 0.26, 0.6), (0, 0, 0), r=0.1, seg=1), (0, 2.3, -1.12), r=(-28, 0, 0)),   # cam cover
           K.cyl(0.12, 0.42, (0.6, 1.3, -0.15), "x", segs=20), K.cyl(0.12, 0.34, (-0.6, 1.32, -0.55), "x", segs=20),
           K.cyl(0.1, 0.2, (-0.6, 1.25, 0.3), "x", segs=14)]
    for k in range(4):
        cov.append(K.cyl(0.04, 0.05, (-0.36 + 0.24 * k, 2.47, -1.2), "y", segs=8))                  # plug caps
    piece(H, "EngineCovers", "Chassis", merge(*cov), col="metal", mat="metal", role="detail", pri=1.1)
    rad = [K.box((1.1, 1.0, 0.16), (0, 0, 0), r=0.05)]
    for k in range(6):
        rad.append(cbox((1.0, 0.04, 0.06), (0, -0.4 + 0.16 * k, -0.09), c=0.012))
    piece(H, "Radiator", "Chassis", xf(merge(*rad), (0, 2.18, -1.42), r=(-18, 0, 0)), col="darker", mat="metal", role="detail", pri=1.2)

    # ---------------------------------------------------------------- exhaust: four headers -> collector -> silencer
    ex = []
    for k in range(4):
        x = -0.36 + 0.24 * k
        ex.append(sweep([(x, 2.0, -1.22), (x * 0.95, 1.55, -1.55), (x * 0.7, 0.75, -1.4), (x * 0.3 + 0.1, 0.42, -0.6), (0.18, 0.45, 0.2)], 0.065, segs=8))
    ex.append(sweep([(0.18, 0.45, 0.1), (0.3, 0.55, 0.75), (0.5, 0.95, 1.2)], 0.12, segs=12))
    muff = sweep([(0.5, 0.95, 1.15), (0.56, 1.25, 1.75), (0.6, 1.58, 2.35)], [0.17, 0.22, 0.2], segs=16, sub=4)
    tip = sweep([(0.6, 1.58, 2.33), (0.61, 1.62, 2.45)], 0.13, segs=14)
    piece(H, "Exhaust", "Chassis", merge(*ex, tip), col="metal", mat="metal", role="detail", pri=1.0)
    piece(H, "Silencer", "Chassis", muff, col="darker", mat="metal", role="detail", pri=1.1)

    # ---------------------------------------------------------------- bodywork: tank, half fairing, scoops, seat, tail
    tank = loft([(-1.48, 3.1, 0.3, 0.18, 0.32, 2.2), (-1.25, 3.2, 0.64, 0.3, 0.52, 2.7), (-0.7, 3.22, 0.74, 0.34, 0.6, 3.0),
                 (-0.15, 3.0, 0.6, 0.3, 0.5, 2.7), (0.2, 2.72, 0.4, 0.14, 0.3, 2.3)], n=32, sub=5)
    piece(H, "Tank", "Chassis", tank, col="primary", mat="metal", role="body", pri=0.5)
    stripe = loft([(-1.42, 3.27, 0.09, 0.03, 0.05), (-1.25, 3.48, 0.1, 0.035, 0.06), (-0.7, 3.54, 0.1, 0.035, 0.06), (-0.15, 3.28, 0.09, 0.035, 0.06), (0.15, 2.86, 0.07, 0.03, 0.05)], n=12, sub=5)
    piece(H, "Stripe", "Chassis", stripe, col="white", mat="plastic", role="detail", pri=1.5)
    cap = K.cyl(0.05, 0.13, (0, 3.555, -0.95), "y", segs=14)
    nose = loft([(-2.6, 2.86, 0.1, 0.05, 0.08, 2.4), (-2.48, 2.9, 0.36, 0.18, 0.26, 3.0), (-2.2, 3.0, 0.56, 0.34, 0.5, 3.2), (-1.85, 3.1, 0.66, 0.46, 0.66, 3.2),
                 (-1.58, 3.14, 0.64, 0.46, 0.7, 3.0)], n=30, sub=4)
    piece(H, "Fairing", "Chassis", merge(nose, cap), col="primary", mat="plastic", role="body", pri=0.6)
    scoop_p = round_poly(np.array([(-1.62, 2.0), (-1.62, 2.75), (-1.3, 3.08), (-0.75, 3.02), (-0.95, 2.5), (-1.25, 1.95)]), [0.12, 0.2, 0.2, 0.15, 0.25, 0.15], 3)
    scoop = warp(extrude(scoop_p, 0.08, bevel=0.03, seg=1), lambda V: np.column_stack([V[:, 0] + 0.72 - 0.16 * np.clip((V[:, 1] - 2.0) / 1.0, 0, 1) ** 2, V[:, 1], V[:, 2]]))
    mpiece(H, "Shroud#", "Chassis", scoop, col="primary", mat="plastic", role="body", pri=0.8)
    vent = merge(*[xf(cbox((0.05, 0.05, 0.5), (0, 0, 0), c=0.012), (0.8 - 0.16 * ((2.25 + 0.15 * k - 2.0) / 1.0) ** 2, 2.25 + 0.15 * k, -1.18 - 0.08 * k)) for k in range(3)])
    piece(H, "ShroudVents", "Chassis", K.mirrored_pair(vent), col="secondary", mat="plastic", role="detail", pri=1.8)
    belly = loft([(-1.6, 0.62, 0.15, 0.12, 0.08), (-1.2, 0.55, 0.5, 0.22, 0.14), (-0.3, 0.52, 0.5, 0.2, 0.12), (0.25, 0.6, 0.3, 0.12, 0.08)], n=20, sub=3)
    piece(H, "BellyPan", "Chassis", belly, col="secondary", mat="plastic", role="detail", pri=1.3)
    screen = warp(K.box((0.8, 0.55, 0.04), (0, 0, 0), r=0.02, seg=1), lambda V: np.column_stack([V[:, 0], V[:, 1], V[:, 2] + 0.25 * (V[:, 0] / 0.43) ** 2]))
    screen = xf(screen, (0, 3.5, -1.95), r=(-55, 0, 0))
    piece(H, "WindscreenGlass", "Chassis", screen, col="glass", mat="glass", role="window", pri=1.2, tr=0.5, ao=False)
    lamps = merge(*[xf(K.box((0.3, 0.12, 0.08), (0, 0, 0), r=0.05, seg=1), (s * 0.2, 2.95, -2.5), r=(0, s * 22, s * -10)) for s in (-1, 1)],
                  xf(K.box((0.3, 0.05, 0.06), (0, 0, 0), r=0.02), (0, 2.74, -2.48)))
    R.glow_lamp(H, "Headlight", "Chassis", lamps, R.WARM)
    dash = merge(xf(K.box((0.5, 0.32, 0.12), (0, 0, 0), r=0.05, seg=1), (0, 3.62, -1.68), r=(-35, 0, 0)))
    piece(H, "Dash", "Chassis", dash, col="darker", mat="plastic", role="detail", pri=1.6)
    mir = []
    for s in (-1, 1):
        mir.append(sweep([(s * 0.62, 3.4, -1.85), (s * 0.82, 3.7, -1.82), (s * 0.95, 3.82, -1.78)], 0.03, segs=6))
        mir.append(xf(loft([(-0.05, 0, 0.17, 0.09, 0.09), (0.04, 0, 0.19, 0.1, 0.1), (0.1, 0, 0.12, 0.06, 0.06)], n=14, sub=2), (s * 1.05, 3.86, -1.78)))
    piece(H, "Mirrors", "Chassis", merge(*mir), col="secondary", mat="plastic", role="detail", pri=1.7)
    st = loft([(0.0, 2.48, 0.34, 0.06, 0.16), (0.35, 2.47, 0.48, 0.08, 0.2), (0.95, 2.52, 0.44, 0.08, 0.18), (1.3, 2.6, 0.34, 0.07, 0.14)], n=26, sub=4)
    pil = loft([(1.4, 2.76, 0.28, 0.05, 0.12), (1.7, 2.82, 0.3, 0.07, 0.14), (2.05, 2.86, 0.22, 0.05, 0.1)], n=20, sub=3)
    piece(H, "Seat", "Chassis", merge(st, pil), col="secondary", mat="cloth", role="seat", pri=0.7)
    tail = loft([(0.95, 2.32, 0.46, 0.16, 0.34), (1.6, 2.56, 0.4, 0.2, 0.34), (2.45, 2.76, 0.27, 0.13, 0.22), (3.08, 2.86, 0.12, 0.06, 0.1)], n=26, sub=4)
    piece(H, "Tail", "Chassis", tail, col="primary", mat="plastic", role="body", pri=0.7)
    R.glow_lamp(H, "Taillight", "Chassis", xf(K.box((0.22, 0.08, 0.08), (0, 0, 0), r=0.03), (0, 2.85, 3.07)), R.TAIL, pri=1.4)
    hang = merge(sweep([(0, 2.55, 2.75), (0, 2.25, 3.2), (0, 1.95, 3.42)], 0.07, segs=8), xf(K.box((0.7, 0.42, 0.04), (0, 0, 0), r=0.04), (0, 1.86, 3.5), r=(-20, 0, 0)))
    hang = merge(hang, *[sweep([(s * 0.05, 2.3, 3.15), (s * 0.42, 2.32, 3.2)], 0.025, segs=6) for s in (-1, 1)])
    piece(H, "PlateHanger", "Chassis", hang, col="darker", mat="plastic", role="detail", pri=1.4)
    ind = merge(*[xf(K.box((0.1, 0.07, 0.14), (0, 0, 0), r=0.03), (s * 0.48, 2.32, 3.22)) for s in (-1, 1)],
                *[xf(K.box((0.07, 0.06, 0.2), (0, 0, 0), r=0.025), (s * 0.68, 3.0, -2.08), r=(0, s * 20, 0)) for s in (-1, 1)])
    R.glow_lamp(H, "Indicators", "Chassis", ind, R.AMBER, pri=1.8)
    hug = _fender(zb, rb, rb + 0.07, 0.06, 70, 150, 0.7, dome=0.5)
    piece(H, "Hugger", "Chassis", hug, col="darker", mat="plastic", role="detail", pri=1.3)
    # ---------------------------------------------------------------- drive + controls
    drv = [_chain(-0.4, (0.15, 1.28), 0.18, (zb, rb), 0.44), K.cyl(0.08, 0.2, (-0.42, 1.28, 0.15), "x", segs=12)]
    for s in (-1, 1):
        drv.append(sweep([(s * 0.56, 1.45, -0.05), (s * 0.62, 1.32, -0.3), (s * 0.95, 1.32, -0.32)], 0.05, segs=8))   # rider pegs
        drv.append(sweep([(s * 0.5, 1.95, 0.75), (s * 0.55, 1.75, 1.15), (s * 0.82, 1.75, 1.18)], 0.04, segs=8))     # pillion pegs
        drv.append(sweep([(s * 0.66, 1.34, -0.42), (s * 0.7, 1.45, -0.85)], 0.03, segs=6))                           # shift / brake lever
    piece(H, "Drive", "Chassis", merge(*drv), col="darker", mat="metal", role="detail", pri=1.3)

    seat_size = (0.9, 0.2, 1.2)
    K.vehicle_clips(H, wheels, susp="Chassis", height=4.0, length=7.4, sym=3, steer=("Steer",), roll=2.0, bob=0.8, turns=1.4)
    H.socket("head", (0, 4.2, -1.6), "Chassis")
    H.socket("mouth", (0, 2.9, -2.6), "Chassis")
    H.socket("exhaust", (0.61, 1.62, 2.5), "Chassis")
    H.rig.update({"head": "Chassis"})
    R.finish_mount(H, "Seat", seat, (-1.6, 0.4), seat_size=seat_size)
    return H


def dirt_bike_real():
    """Motocross bike at real scale (7.3 studs): tall knobby wire wheels (21" / 18"), long-travel inverted forks,
    beak front fender and number plate, flat bench seat running up onto the tank, orange radiator shrouds and side
    plates, white high rear fender, single-cylinder engine with fins and an upswept silencer, cradle frame, alloy
    swing arm with linkage shock, wide braced bars."""
    H = _new("dirt bike", pv("#FF6A00", "#F4F4F4", white="#F4F4F4", metal="#C2C8CF", gold="#E0A030", darker="#1E2024"))
    seat = (0.0, 2.95, 0.35)
    hy, hz = 3.85, -1.45
    rake = math.radians(26)
    zf, zb, rf, rb = -2.85, 2.2, 1.16, 1.1
    H.bone("Chassis", "Body", (0, 0, 0))
    H.bone("Steer", "Chassis", (0, 3.2, -1.75))
    H.bone("WheelF", "Steer", (0, rf, zf))
    H.bone("WheelB", "Chassis", (0, rb, zb))
    wheels = [R.moto_wheel(H, "WheelF", "WheelF", (0, rf, zf), rf, 0.34, style="wire", spokes=32, rim_col="darker", knobby=0.07, ri=rf * 0.74, discs=(0.24,), disc_r=0.5, lugs=26),
              R.moto_wheel(H, "WheelB", "WheelB", (0, rb, zb), rb, 0.46, style="wire", spokes=32, rim_col="darker", knobby=0.08, ri=rb * 0.7, discs=(0.3,), disc_r=0.38, lugs=24)]
    piece(H, "Sprocket", "WheelB", xf(_sprocket(0.5, 24, -0.3), (0, rb, zb)), col="steel", mat="metal", role="wheel", pri=1.6)

    def on_axis(y):
        return hz - math.sin(rake) * (hy - y) / math.cos(rake)
    fk = []
    for s in (-1, 1):
        x = s * 0.33
        fk.append(sweep([(x, hy + 0.1, on_axis(hy + 0.1)), (x, 2.0, on_axis(2.0))], 0.11, segs=14))
        fk.append(sweep([(x, 2.1, on_axis(2.1)), (x, 1.9, on_axis(1.9))], 0.125, segs=14))
        fk.append(cbox((0.15, 0.32, 0.32), (x, rf + 0.05, zf), c=0.04))
    fk += [K.box((0.86, 0.14, 0.4), (0, hy + 0.02, on_axis(hy) + 0.04), r=0.05), K.box((0.86, 0.16, 0.38), (0, 3.15, on_axis(3.15) + 0.04), r=0.05),
           sweep([(-0.34, rf, zf), (0.34, rf, zf)], 0.05, segs=8), K.box((0.12, 0.4, 0.2), (0.28, rf + 0.32, zf + 0.42), r=0.04, rot_=(35, 0, 0))]
    piece(H, "Forks", "Steer", merge(*fk), col="gold", mat="metal", role="detail", pri=0.8)
    stanch = merge(*[sweep([(s * 0.33, 2.0, on_axis(2.0)), (s * 0.33, rf + 0.15, on_axis(rf + 0.15))], 0.085, segs=12) for s in (-1, 1)])
    piece(H, "Stanchions", "Steer", stanch, col="metal", mat="metal", role="detail", pri=1.0)
    gy, gz = 4.2, -1.05
    bars = [sweep([(-1.3, gy, gz), (-0.75, gy - 0.05, gz - 0.12), (-0.3, gy - 0.2, gz - 0.3), (0.3, gy - 0.2, gz - 0.3), (0.75, gy - 0.05, gz - 0.12), (1.3, gy, gz)], 0.05, segs=8),
            sweep([(-0.55, gy + 0.02, gz - 0.16), (0.55, gy + 0.02, gz - 0.16)], 0.03, segs=6), K.box((0.3, 0.12, 0.12), (0, gy - 0.02, gz - 0.2), r=0.04)]
    bars += [sweep([(s * 0.2, hy + 0.08, hz + 0.02), (s * 0.3, gy - 0.2, gz - 0.3)], 0.06, segs=8) for s in (-1, 1)]
    bars += [cbox((0.1, 0.05, 0.45), (s * 1.0, gy + 0.04, gz - 0.25), c=0.02, rot_=(0, -s * 15, 0)) for s in (-1, 1)]
    piece(H, "Bars", "Steer", merge(*bars), col="darker", mat="metal", role="detail", pri=1.0)
    grips = merge(*[sweep([(s * 0.9, gy - 0.01, gz - 0.06), (s * 1.38, gy, gz)], 0.075, segs=10) for s in (-1, 1)])
    piece(H, "Grips", "Steer", grips, col="tyre", mat="rubber", role="detail", pri=1.2)
    beak = loft([(-3.85, 2.55, 0.12, 0.03, 0.03, 2.2), (-3.5, 2.6, 0.36, 0.05, 0.05), (-2.8, 2.65, 0.4, 0.07, 0.07), (-2.25, 2.62, 0.36, 0.06, 0.06), (-2.0, 2.66, 0.2, 0.05, 0.05)], n=16, sub=3)
    beak = warp(beak, lambda V: np.column_stack([V[:, 0], V[:, 1] + 0.14 * (1 - (V[:, 0] / 0.4) ** 2) - 0.25 * np.clip((-V[:, 2] - 3.0) / 0.85, 0, 1) ** 2, V[:, 2]]))
    piece(H, "FenderF", "Steer", beak, col="white", mat="plastic", role="detail", pri=1.0)
    plate = merge(xf(loft([(-0.05, 0, 0.45, 0.45, 0.4, 3.0), (0.05, 0, 0.42, 0.42, 0.38, 3.0)], n=20, sub=1), (0, 3.25, -2.1)))
    plate = xf(plate, (0, 0, 0)) if False else D_rot(plate, (0, 3.25, -2.1), -22)
    piece(H, "NumberPlate", "Steer", plate, col="primary", mat="plastic", role="detail", pri=1.0)
    R.glow_lamp(H, "Headlight", "Steer", D_rot(K.box((0.36, 0.2, 0.06), (0, 3.1, -2.2), r=0.06, seg=1), (0, 3.25, -2.1), -22), R.WARM)
    num = D_rot(merge(cbox((0.1, 0.36, 0.04), (-0.14, 3.34, -2.17), c=0.01), cbox((0.1, 0.36, 0.04), (0.14, 3.34, -2.17), c=0.01)), (0, 3.25, -2.1), -22)
    piece(H, "Number", "Steer", num, col="darker", mat="plastic", role="detail", pri=1.8)
    # frame + swing arm
    pivot = (0.42, 1.95, 0.55)
    fr = [sweep([(0, hy + 0.06, hz), (0, 3.1, on_axis(3.1))], 0.15, segs=14)]
    for s in (-1, 1):
        fr.append(sweep([(s * 0.2, 3.7, hz + 0.15), (s * 0.45, 3.2, -0.6), (s * 0.45, 2.55, 0.3), (s * pivot[0], pivot[1], pivot[2])], 0.075, segs=10))
        fr.append(sweep([(s * 0.1, 3.2, hz - 0.15), (s * 0.3, 1.6, -1.25), (s * 0.35, 0.72, -0.6), (s * 0.4, 0.8, 0.3), (s * pivot[0], pivot[1], pivot[2])], 0.06, segs=8))
        fr.append(sweep([(s * 0.45, 2.9, 0.0), (s * 0.3, 2.95, 1.6), (s * 0.25, 3.1, 2.4)], 0.055, segs=8))
        fr.append(sweep([(s * 0.42, 2.1, 0.55), (s * 0.3, 2.85, 1.5)], 0.045, segs=8))
    fr.append(K.box((0.66, 0.08, 1.4), (0, 0.66, -0.4), r=0.03))   # skid plate
    piece(H, "Frame", "Chassis", merge(*fr), col="metal", mat="metal", role="body", pri=0.7)
    sw = [sweep([(s * 0.38, pivot[1], pivot[2]), (s * 0.4, 1.55, 1.4), (s * 0.36, rb, zb)], [0.12, 0.11, 0.08], segs=10) for s in (-1, 1)]
    sw += [sweep([(-0.38, 1.7, 1.2), (0.38, 1.7, 1.2)], 0.06, segs=8), sweep([(-0.38, rb, zb), (0.38, rb, zb)], 0.05, segs=8)]
    piece(H, "Swingarm", "Chassis", merge(*sw), col="metal", mat="metal", role="detail", pri=0.9)
    shock = merge(R.spring((0, 2.85, 0.5), (0, 1.55, 0.95), 0.15, wire=0.04, turns=7), sweep([(0, 2.95, 0.48), (0, 1.5, 0.97)], 0.07, segs=8),
                  xf(K.cyl(0.32, 0.12, (0, 0, 0), "y", segs=12), (0.2, 2.75, 0.6)))
    piece(H, "Shock", "Chassis", shock, col="gold", mat="metal", role="detail", pri=1.6)
    eng = [K.box((0.72, 0.85, 1.1), (0, 1.25, -0.25), r=0.16, seg=1), xf(K.box((0.62, 0.75, 0.6), (0, 0, 0), r=0.1, seg=1), (0, 2.0, -0.55), r=(-15, 0, 0))]
    for i in range(6):
        eng.append(xf(cbox((0.8, 0.045, 0.72), (0, 0, 0), c=0.012), (0, 1.75 + 0.1 * i, -0.5 - 0.027 * i), r=(-15, 0, 0)))
    piece(H, "Engine", "Chassis", merge(*eng), col="gunmetal", mat="metal", role="body", pri=0.8)
    cov = [K.cyl(0.1, 0.4, (0.4, 1.2, -0.15), "x", segs=18), K.cyl(0.1, 0.3, (-0.4, 1.3, -0.4), "x", segs=16), xf(K.box((0.55, 0.22, 0.5), (0, 0, 0), r=0.08), (0, 2.45, -0.62), r=(-15, 0, 0)),
           K.cyl(0.1, 0.32, (0.0, 2.25, 0.2), "z", segs=14)]
    piece(H, "EngineCovers", "Chassis", merge(*cov), col="metal", mat="metal", role="detail", pri=1.1)
    ex = [sweep([(0.05, 2.0, -0.9), (0.1, 1.7, -1.3), (0.35, 1.05, -1.25), (0.45, 1.0, -0.4), (0.42, 1.6, 0.4), (0.42, 2.35, 1.1)], [0.08, 0.09, 0.1, 0.1, 0.09, 0.08], segs=10)]
    piece(H, "Exhaust", "Chassis", merge(*ex), col="metal", mat="metal", role="detail", pri=1.0)
    muff = sweep([(0.42, 2.3, 1.0), (0.44, 2.6, 1.7), (0.46, 2.85, 2.35)], [0.16, 0.19, 0.17], segs=14)
    piece(H, "Silencer", "Chassis", merge(muff, sweep([(0.46, 2.84, 2.33), (0.47, 2.88, 2.48)], 0.09, segs=10)), col="white", mat="metal", role="detail", pri=1.1)
    rad = merge(*[K.box((0.16, 0.85, 0.65), (s * 0.4, 2.55, -1.15), r=0.04) for s in (-1, 1)])
    piece(H, "Radiator", "Chassis", rad, col="darker", mat="metal", role="detail", pri=1.2)
    # bodywork
    tank = loft([(-1.5, 3.45, 0.2, 0.15, 0.3, 2.4), (-1.2, 3.5, 0.48, 0.25, 0.5), (-0.55, 3.3, 0.5, 0.25, 0.5), (0.0, 3.05, 0.4, 0.12, 0.3)], n=26, sub=4)
    piece(H, "Tank", "Chassis", tank, col="primary", mat="plastic", role="body", pri=0.6)
    sh_p = round_poly(np.array([(-1.95, 2.2), (-1.85, 3.3), (-1.55, 3.7), (-0.9, 3.55), (-0.4, 3.15), (-0.75, 2.3)]), [0.12, 0.2, 0.25, 0.2, 0.2, 0.15], 3)
    shroud = warp(extrude(sh_p, 0.08, bevel=0.03, seg=1), lambda V: np.column_stack([V[:, 0] + 0.55 + 0.18 * np.clip((-V[:, 2] - 1.0) / 0.9, 0, 1), V[:, 1], V[:, 2]]))
    mpiece(H, "Shroud#", "Chassis", shroud, col="primary", mat="plastic", role="body", pri=0.8)
    gfx = warp(extrude(round_poly(np.array([(-1.78, 2.95), (-1.62, 3.3), (-0.75, 3.05), (-0.9, 2.78)]), 0.08, 2), 0.04, bevel=0.015, seg=1),
               lambda V: np.column_stack([V[:, 0] + 0.6 + 0.18 * np.clip((-V[:, 2] - 1.0) / 0.9, 0, 1) + 0.03, V[:, 1], V[:, 2]]))
    piece(H, "Graphics", "Chassis", K.mirrored_pair(gfx), col="darker", mat="plastic", role="detail", pri=1.6)
    st = loft([(-1.25, 3.42, 0.22, 0.05, 0.12), (-0.6, 3.22, 0.36, 0.08, 0.15), (0.3, 3.0, 0.42, 0.1, 0.16), (1.4, 3.08, 0.36, 0.09, 0.15), (2.3, 3.2, 0.24, 0.06, 0.1)], n=22, sub=4)
    piece(H, "Seat", "Chassis", st, col="darker", mat="cloth", role="seat", pri=0.7)
    side_p = round_poly(np.array([(0.3, 2.3), (0.4, 2.95), (2.1, 3.12), (2.0, 2.65), (1.0, 2.25)]), [0.1, 0.1, 0.2, 0.15, 0.15], 3)
    side = warp(extrude(side_p, 0.08, bevel=0.03, seg=1), lambda V: np.column_stack([V[:, 0] + 0.45 - 0.1 * np.clip((V[:, 2] - 0.3) / 1.8, 0, 1), V[:, 1], V[:, 2]]))
    mpiece(H, "SidePlate#", "Chassis", side, col="white", mat="plastic", role="body", pri=0.9)
    rfend = loft([(1.6, 3.0, 0.38, 0.06, 0.08), (2.4, 3.18, 0.36, 0.06, 0.07), (3.3, 3.25, 0.26, 0.04, 0.05), (3.55, 3.22, 0.12, 0.03, 0.03)], n=16, sub=3)
    rfend = warp(rfend, lambda V: np.column_stack([V[:, 0], V[:, 1] + 0.1 * (1 - (V[:, 0] / 0.38) ** 2), V[:, 2]]))
    piece(H, "FenderB", "Chassis", rfend, col="white", mat="plastic", role="body", pri=0.9)
    R.glow_lamp(H, "Taillight", "Chassis", K.box((0.22, 0.08, 0.1), (0, 3.15, 3.3), r=0.03), R.TAIL, pri=1.5)
    drv = [_chain(-0.3, (0.1, 1.25), 0.17, (zb, rb), 0.48)]
    for s in (-1, 1):
        drv.append(merge(K.box((0.42, 0.08, 0.2), (s * 0.68, 1.62, -0.15), r=0.02), *[cbox((0.04, 0.06, 0.2), (s * (0.52 + 0.1 * k), 1.68, -0.15), c=0.01) for k in range(4)]))
        drv.append(sweep([(s * 0.45, 1.6, -0.35), (s * 0.55, 1.7, -0.8)], 0.03, segs=6))
    piece(H, "Drive", "Chassis", merge(*drv), col="darker", mat="metal", role="detail", pri=1.3)
    K.vehicle_clips(H, wheels, susp="Chassis", height=4.4, length=7.3, sym=8, steer=("Steer",), roll=2.0, bob=1.2, turns=1.4)
    H.socket("head", (0, 4.6, -1.6), "Chassis")
    H.socket("mouth", (0, 3.2, -2.4), "Chassis")
    H.socket("exhaust", (0.47, 2.88, 2.5), "Chassis")
    H.rig.update({"head": "Chassis"})
    R.finish_mount(H, "Seat", seat, (-1.6, 0.4), seat_size=(0.8, 0.2, 1.6))
    return H


def D_rot(m, pivot, deg):
    """Rotate a mesh about X through pivot by deg (pitch)."""
    p = np.asarray(pivot, float)
    return xf(xf(m, -p), tuple(p), r=(deg, 0, 0))


def moped_real():
    """Classic step-through scooter at real scale (6 studs): pressed leg shield with a chrome centre trim, flat
    floorboard for the feet, bulbous side cowls over the engine, cream bench seat, swept handlebar casing with a
    round glowing headlamp and speedo, deep front mudguard on the steering, small disc wheels, chrome rear rack,
    round mirrors, tail lamp and a short exhaust."""
    H = _new("moped", pv("#8FD3C1", "#F2E8CF", leather="#7A4E2D", metal="#D6DCE2"))
    seat = (0.0, 2.38, 0.55)
    zf, zb, rf, rb = -2.15, 1.9, 0.62, 0.62
    H.bone("Chassis", "Body", (0, 0, 0))
    H.bone("Steer", "Chassis", (0, 2.6, -1.62))
    H.bone("WheelF", "Steer", (0, rf, zf))
    H.bone("WheelB", "Chassis", (0, rb, zb))
    wheels = [R.moto_wheel(H, "WheelF", "WheelF", (0, rf, zf), rf, 0.4, style="disc", rim_col="metal", ri=rf * 0.62),
              R.moto_wheel(H, "WheelB", "WheelB", (0, rb, zb), rb, 0.42, style="disc", rim_col="metal", ri=rb * 0.62)]
    # steering: column, front link, mudguard, bar casing with headlamp
    col = [sweep([(0, 3.35, -1.6), (0, 2.2, -1.75), (0, 1.25, -1.95)], 0.09, segs=10), sweep([(-0.08, 1.3, -1.95), (-0.25, rf, zf), (0.0, rf, zf)], 0.07, segs=8),
           K.cyl(0.1, 0.14, (-0.25, rf, zf), "x", segs=12)]
    piece(H, "Fork", "Steer", merge(*col), col="darker", mat="metal", role="detail", pri=1.0)
    guard = loft([(-2.8, 1.05, 0.12, 0.05, 0.05), (-2.65, 1.3, 0.34, 0.25, 0.08), (-2.25, 1.45, 0.4, 0.3, 0.1), (-1.7, 1.4, 0.38, 0.25, 0.1), (-1.5, 1.2, 0.3, 0.15, 0.08)], n=22, sub=3)
    guard = warp(guard, lambda V: np.column_stack([V[:, 0], V[:, 1] + 0.0, V[:, 2]]))
    piece(H, "FenderF", "Steer", guard, col="primary", mat="metal", role="body", pri=0.8)
    hb = loft([(-1.95, 3.42, 0.08, 0.06, 0.08), (-1.85, 3.45, 0.34, 0.18, 0.2), (-1.55, 3.5, 0.62, 0.12, 0.16, 3.0), (-1.3, 3.5, 0.6, 0.1, 0.12, 3.0), (-1.18, 3.48, 0.2, 0.08, 0.08)], n=24, sub=3)
    piece(H, "BarCasing", "Steer", hb, col="primary", mat="metal", role="detail", pri=0.9)
    ring = K.tube_ring(0.26, 0.2, 0.1, axis="z", pos=(0, 3.45, -1.95), segs=20)
    piece(H, "LampRing", "Steer", merge(ring, K.box((0.3, 0.16, 0.08), (0, 3.62, -1.45), r=0.04)), col="metal", mat="metal", role="detail", pri=1.2)
    R.glow_lamp(H, "Headlight", "Steer", K.lamp((0, 3.45, -1.98), 0.21, 0.08), R.WARM)
    grips = merge(*[sweep([(s * 0.6, 3.5, -1.35), (s * 0.95, 3.52, -1.12), (s * 1.25, 3.52, -1.02)], 0.07, segs=10) for s in (-1, 1)])
    mir = merge(*[merge(sweep([(s * 0.55, 3.55, -1.3), (s * 0.75, 3.95, -1.35)], 0.025, segs=6), xf(K.cyl(0.06, 0.16, (0, 0, 0), "z", segs=16), (s * 0.78, 4.05, -1.35))) for s in (-1, 1)])
    piece(H, "Grips", "Steer", merge(grips), col="tyre", mat="rubber", role="detail", pri=1.2)
    piece(H, "Mirrors", "Steer", mir, col="metal", mat="metal", role="detail", pri=1.7)
    # body: leg shield, floorboard, tunnel, rear cowl
    shield = loft_y_shell = R.loft_y([(1.0, -1.42, 0.72, 0.08, 0.06), (1.7, -1.58, 0.72, 0.09, 0.06), (2.5, -1.68, 0.62, 0.09, 0.06), (3.2, -1.66, 0.38, 0.08, 0.06), (3.35, -1.62, 0.18, 0.06, 0.05)], n=24, sub=3)
    shield = warp(shield, lambda V: np.column_stack([V[:, 0], V[:, 1], V[:, 2] - 0.18 * (1 - (V[:, 0] / 0.72) ** 2)]))
    floor = K.box((1.08, 0.18, 1.6), (0, 1.0, -0.6), r=0.08, seg=1)
    tunnel = loft([(-1.4, 1.1, 0.22, 0.25, 0.1), (-0.6, 1.1, 0.2, 0.18, 0.1), (0.1, 1.2, 0.3, 0.3, 0.12)], n=16, sub=3)
    cowl = loft([(-0.05, 1.6, 0.4, 0.5, 0.45), (0.6, 1.62, 0.68, 0.6, 0.58), (1.45, 1.68, 0.72, 0.58, 0.6), (2.2, 1.82, 0.52, 0.42, 0.42), (2.62, 1.92, 0.18, 0.14, 0.16)], n=30, sub=4)
    piece(H, "Body", "Chassis", merge(shield, floor, tunnel, cowl), col="primary", mat="metal", role="body", pri=0.5)
    mats = merge(*[cbox((0.05, 0.04, 1.35), (x, 1.1, -0.6), c=0.01) for x in (-0.36, -0.18, 0, 0.18, 0.36)])
    piece(H, "FloorMats", "Chassis", mats, col="darker", mat="rubber", role="detail", pri=1.6)
    trim = merge(sweep([(0, 1.05, -1.62), (0, 1.9, -1.84), (0, 2.7, -1.92), (0, 3.3, -1.82)], 0.05, segs=8), *[sweep([(s * 0.73, 2.05, -0.5), (s * 0.76, 1.95, 1.4)], 0.025, segs=6) for s in (-1, 1)],
                 K.box((0.32, 0.22, 0.06), (0, 2.85, -1.92), r=0.04))
    piece(H, "Chrome", "Chassis", trim, col="metal", mat="metal", role="detail", pri=1.3)
    st = loft([(-0.1, 2.25, 0.32, 0.06, 0.12), (0.4, 2.3, 0.44, 0.1, 0.14), (1.2, 2.34, 0.42, 0.1, 0.14), (1.75, 2.36, 0.32, 0.08, 0.12)], n=22, sub=3)
    piece(H, "Seat", "Chassis", st, col="leather", mat="cloth", role="seat", pri=0.7)
    rack = merge(*[sweep([(s * 0.3, 2.3, 1.75), (s * 0.32, 2.4, 2.25), (s * 0.22, 2.32, 2.55)], 0.03, segs=6) for s in (-1, 1)],
                 *[sweep([(-0.3, 2.38, z), (0.3, 2.38, z)], 0.025, segs=6) for z in (1.95, 2.2)], sweep([(-0.22, 2.32, 2.55), (0.22, 2.32, 2.55)], 0.03, segs=6))
    piece(H, "Rack", "Chassis", rack, col="metal", mat="metal", role="detail", pri=1.5)
    R.glow_lamp(H, "Taillight", "Chassis", K.lamp((0, 2.05, 2.66), 0, 0.06, axis="+z", shape="rect", w=0.28, h=0.14), R.TAIL, pri=1.5)
    ex = merge(sweep([(0.3, 0.9, 0.9), (0.45, 0.7, 1.3), (0.48, 0.72, 2.2)], [0.08, 0.12, 0.12], segs=12), sweep([(0.48, 0.72, 2.18), (0.48, 0.74, 2.32)], 0.06, segs=10))
    piece(H, "Exhaust", "Chassis", ex, col="metal", mat="metal", role="detail", pri=1.4)
    eng = merge(K.box((0.5, 0.45, 1.0), (-0.1, 0.85, 1.4), r=0.1), sweep([(-0.3, rb, zb), (-0.3, 0.8, 1.0)], 0.1, segs=10))
    piece(H, "Engine", "Chassis", eng, col="gunmetal", mat="metal", role="detail", pri=1.2)
    K.vehicle_clips(H, wheels, susp="Chassis", height=3.6, length=6.0, sym=5, steer=("Steer",), roll=1.6, bob=0.8, turns=1.6, attack="honk")
    H.socket("head", (0, 4.0, -1.6), "Chassis")
    H.socket("mouth", (0, 3.0, -2.0), "Chassis")
    H.socket("exhaust", (0.48, 0.74, 2.35), "Chassis")
    H.rig.update({"head": "Chassis"})
    R.finish_mount(H, "Seat", seat, (-1.5, 0.4), seat_size=(0.8, 0.2, 1.6))
    return H


# ==================================================================================================== real-scale pedal cycles
def _crank_set(H, bone_parent, bb, ring_r=0.36, arm=0.55, side=0.3, col="darker", ring_col="metal", teeth=36):
    """Pedal crank on its own spinning bone "Crank": chainring (right) + two arms + pedals with tread blocks."""
    b = H.bone("Crank", bone_parent, bb)
    x, y, z = bb
    ring = xf(_sprocket(ring_r, teeth, side - 0.08), (0, y, z))
    ring = xf(ring, (x, 0, z * 0)) if False else ring
    arms = [K.bar((x + side, y, z), (x + side, y - arm, z + 0.04), 0.07, 0.11, r=0.03), K.bar((x - side, y, z), (x - side, y + arm, z - 0.04), 0.07, 0.11, r=0.03)]
    ped = []
    for sx, py, pz in ((1, y - arm, z + 0.04), (-1, y + arm, z - 0.04)):
        px = x + sx * (side + 0.2)
        ped.append(K.box((0.3, 0.07, 0.2), (px, py, pz), r=0.025))
        ped += [cbox((0.3, 0.03, 0.03), (px, py + 0.05, pz + d), c=0.008) for d in (-0.07, 0.07)]
    axle = sweep([(x - side, y, z), (x + side, y, z)], 0.06, segs=10)
    piece(H, "Crank", b, merge(*arms, *ped, axle), col=col, mat="metal", role="detail", pri=1.1)
    piece(H, "Chainring", b, ring, col=ring_col, mat="metal", role="detail", pri=1.3)
    return b


def _cycle(hid, kind="city", preview=None):
    """Bicycle family at real scale. kind: city (6 studs, swept bars, basket, fenders, rack), bmx (5 studs, 20" wheels,
    riser bars, pegs, no fenders), tandem (8.6 studs, two seats / cranks, the captain's seat is the mount seat)."""
    H = _new(hid, preview)
    bmx, tandem = kind == "bmx", kind == "tandem"
    r = 0.84 if bmx else 1.12
    tw = 0.3 if bmx else 0.2
    zf, zb = (-1.75, 1.55) if bmx else ((-3.0, 2.65) if tandem else (-1.85, 1.6))
    bb = (0.0, 0.98 if bmx else 0.98, 0.2 if bmx else (-1.25 if tandem else 0.1))
    H.bone("Chassis", "Body", (0, 0, 0))
    ht_top = (0, 2.6 if bmx else 3.05, zf + (0.55 if bmx else 0.66))
    ht_bot = (0, ht_top[1] - (0.45 if bmx else 0.55), ht_top[2] - (0.15 if bmx else 0.17))
    H.bone("Steer", "Chassis", ht_top)
    H.bone("WheelF", "Steer", (0, r, zf))
    H.bone("WheelB", "Chassis", (0, r, zb))
    rim_col = "primary" if bmx else "metal"
    wheels = [R.moto_wheel(H, "WheelF", "WheelF", (0, r, zf), r, tw, style="wire", spokes=36 if bmx else 32, rim_col=rim_col, knobby=0.05 if bmx else 0.0,
                           ri=r - tw * (1.0 if bmx else 0.9), lugs=30, segs=28),
              R.moto_wheel(H, "WheelB", "WheelB", (0, r, zb), r, tw, style="wire", spokes=36 if bmx else 32, rim_col=rim_col, knobby=0.05 if bmx else 0.0,
                           ri=r - tw * (1.0 if bmx else 0.9), lugs=30, segs=28)]
    cog = merge(_sprocket(0.2 if not bmx else 0.14, 14, 0.2), K.cyl(0.25, 0.1, (0.05, 0, 0), "x", segs=12))
    piece(H, "Cog", "WheelB", xf(cog, (0, r, zb)), col="steel", mat="metal", role="wheel", pri=1.7)
    # frame
    st_dir = np.array([0, 0.956, 0.292])
    seat_top = np.array(bb) + st_dir * ((2.1 if bmx else 2.55) - bb[1]) / st_dir[1]
    tube = 0.075 if bmx else 0.065
    fr = [sweep([ht_top, ht_bot], 0.09, segs=12), sweep([ht_bot, bb], tube * 1.15, segs=10), sweep([bb, tuple(seat_top)], tube, segs=10),
          sweep([(0, ht_top[1] - 0.08, ht_top[2] + 0.05), tuple(seat_top - st_dir * (0.25 if bmx else 0.15))], tube, segs=10),
          K.cyl(0.36, 0.11, bb, "x", segs=14)]
    for s in (-1, 1):
        fr.append(sweep([(s * 0.06, bb[1], bb[2] + 0.05), (s * 0.18, r + 0.04, zb - 0.6), (s * 0.2, r, zb)], 0.04, segs=8))
        fr.append(sweep([tuple(seat_top - st_dir * 0.2 + np.array([s * 0.05, 0, 0])), (s * 0.18, r + 0.6, zb - 0.45), (s * 0.2, r, zb)], 0.035, segs=8))
        fr.append(cbox((0.06, 0.16, 0.2), (s * 0.21, r, zb), c=0.02))
    seats = [tuple(seat_top)]
    if tandem:
        bb2 = (0.0, 0.98, 0.95)
        st2 = np.array(bb2) + st_dir * (2.55 - bb2[1]) / st_dir[1]
        fr += [sweep([bb, bb2], tube, segs=10), sweep([bb2, tuple(st2)], tube, segs=10), sweep([tuple(seat_top - st_dir * 0.15), tuple(st2 - st_dir * 0.15)], tube, segs=10),
               sweep([tuple(seat_top - st_dir * 0.7), bb2], tube * 0.9, segs=10), K.cyl(0.36, 0.11, bb2, "x", segs=14)]
        seats.append(tuple(st2))
    piece(H, "Frame", "Chassis", merge(*fr), col="primary", mat="metal", role="body", pri=0.5)
    # fork + stem + bars
    fk = [sweep([(0, ht_top[1] + 0.1, ht_top[2] + 0.03), (0, ht_bot[1] - 0.05, ht_bot[2] - 0.02)], 0.055, segs=10), K.box((0.42, 0.12, 0.2), (0, ht_bot[1] - 0.12, ht_bot[2] - 0.04), r=0.04)]
    for s in (-1, 1):
        fk.append(sweep([(s * 0.17, ht_bot[1] - 0.12, ht_bot[2] - 0.04), (s * 0.18, (ht_bot[1] + r) / 2, (ht_bot[2] + zf) / 2 - 0.05), (s * 0.18, r, zf)],
                        0.05 if not bmx else 0.06, segs=8))
    piece(H, "Fork", "Steer", merge(*fk), col="primary" if not bmx else "darker", mat="metal", role="detail", pri=0.9)
    if bmx:
        gy, gz, gx = seat_top[1] + 1.35, seat_top[2] - 1.4, 1.25
        top = (0, ht_top[1] + 0.25, ht_top[2] + 0.1)
        bars = [K.box((0.3, 0.2, 0.3), top, r=0.05), sweep([(-gx, gy, gz), (-0.45, gy, gz - 0.08), (-0.3, top[1], top[2]), (0.3, top[1], top[2]), (0.45, gy, gz - 0.08), (gx, gy, gz)], 0.05, segs=8),
                sweep([(-0.4, gy - 0.25, gz - 0.06), (0.4, gy - 0.25, gz - 0.06)], 0.04, segs=8)]
    else:
        gy, gz, gx = seat_top[1] + 1.15, seat_top[2] - 1.38, 1.22
        top = (0, ht_top[1] + 0.32, ht_top[2] - 0.08)
        bars = [sweep([(0, ht_top[1] + 0.05, ht_top[2] + 0.02), (0, top[1], top[2])], 0.05, segs=8), K.box((0.18, 0.16, 0.2), top, r=0.04),
                sweep([(-gx, gy, gz), (-0.75, gy - 0.02, gz - 0.12), (-0.25, top[1], top[2] - 0.05), (0.25, top[1], top[2] - 0.05), (0.75, gy - 0.02, gz - 0.12), (gx, gy, gz)], 0.042, segs=8)]
        bars += [sweep([(s * 0.75, gy - 0.02, gz - 0.12), (s * 0.95, gy - 0.05, gz - 0.38)], 0.02, segs=5) for s in (-1, 1)]   # brake levers
    piece(H, "Bars", "Steer", merge(*bars), col="metal" if not bmx else "darker", mat="metal", role="detail", pri=1.0)
    grips = merge(*[sweep([(s * (gx - 0.42), gy - (0.0 if bmx else 0.01), gz - (0.06 if bmx else 0.04)), (s * (gx + 0.03), gy, gz)], 0.065, segs=10) for s in (-1, 1)])
    piece(H, "Grips", "Steer", grips, col="tyre" if not bmx else "secondary", mat="rubber", role="detail", pri=1.2)
    # saddles
    sd = []
    for p in seats:
        x, y, z = p
        sd.append(sweep([(0, y - 0.35, z - 0.1), (0, y + 0.12, z + 0.04)], 0.04, segs=8))
        sd.append(loft([(z - 0.42, y + 0.16, 0.06, 0.04, 0.04), (z - 0.3, y + 0.18, 0.11, 0.05, 0.06), (z - 0.05, y + 0.18, 0.18, 0.06, 0.07), (z + 0.18, y + 0.18, 0.3, 0.07, 0.08),
                        (z + 0.3, y + 0.16, 0.26, 0.05, 0.07)], n=18, sub=3))
    piece(H, "Seat", "Chassis", merge(*sd), col="darker" if not bmx else "secondary", mat="cloth", role="seat", pri=0.7)
    # cranks + chain
    _crank_set(H, "Chassis", bb, ring_r=0.3 if bmx else 0.36, arm=0.5 if bmx else 0.55, side=0.28)
    chain = [_chain(0.2, (bb[2], bb[1]), 0.3 if bmx else 0.36, (zb, r), 0.14 if bmx else 0.2, w=0.025)]
    if tandem:
        b2 = H.bone("Crank2", "Chassis", bb2)
        c2 = [K.bar((-0.28, bb2[1], bb2[2]), (-0.28, bb2[1] - 0.55, bb2[2]), 0.07, 0.11, r=0.03), K.bar((0.28, bb2[1], bb2[2]), (0.28, bb2[1] + 0.55, bb2[2]), 0.07, 0.11, r=0.03),
              K.box((0.3, 0.07, 0.2), (-0.48, bb2[1] - 0.55, bb2[2]), r=0.025), K.box((0.3, 0.07, 0.2), (0.48, bb2[1] + 0.55, bb2[2]), r=0.025), sweep([(-0.28, bb2[1], bb2[2]), (0.28, bb2[1], bb2[2])], 0.06)]
        piece(H, "Crank2", b2, merge(*c2), col="darker", mat="metal", role="detail", pri=1.2)
        chain = [_chain(-0.22, (bb[2], bb[1]), 0.33, (bb2[2], bb2[1]), 0.33, w=0.025), _chain(0.2, (bb2[2], bb2[1]), 0.36, (zb, r), 0.2, w=0.025)]
        stoker = [sweep([tuple(seats[0] - st_dir * 0.1), (0, seats[0][1] + 0.35, seats[0][2] + 0.35)], 0.04, segs=8),
                  sweep([(-0.6, seats[0][1] + 0.35, seats[0][2] + 0.45), (0.6, seats[0][1] + 0.35, seats[0][2] + 0.45)], 0.04, segs=8)]
        stoker += [sweep([(s * 0.35, seats[0][1] + 0.35, seats[0][2] + 0.45), (s * 0.68, seats[0][1] + 0.35, seats[0][2] + 0.45)], 0.06, segs=8) for s in (-1, 1)]
        piece(H, "StokerBars", "Chassis", merge(*stoker), col="metal", mat="metal", role="detail", pri=1.2)
    piece(H, "Chain", "Chassis", merge(*chain), col="steel", mat="metal", role="detail", pri=1.5)
    if bmx:
        pegs = merge(*[K.cyl(0.4, 0.07, (s * 0.38, r, z), "x", segs=10) for s in (-1, 1) for z in (zb,)])
        piece(H, "Pegs", "WheelB", pegs, col="metal", mat="metal", role="detail", pri=1.4)
        pf = merge(*[K.cyl(0.4, 0.07, (s * 0.38, r, zf), "x", segs=10) for s in (-1, 1)])
        piece(H, "PegsF", "WheelF", pf, col="metal", mat="metal", role="detail", pri=1.5)
        pad = loft([(-0.32, 0, 0.1, 0.08, 0.08), (0.32, 0, 0.1, 0.08, 0.08)], n=12, sub=1)
        pad = xf(pad, (0, top[1] - 0.24, top[2] - 0.06 + 0.0))
        piece(H, "BarPad", "Steer", xf(pad, (0, 0, 0)) if False else xf(R.loft([(-0.08, gy - 0.25, 0.4, 0.07, 0.07), (0.08, gy - 0.25, 0.4, 0.07, 0.07)], n=12, sub=1), (0, 0, gz - 0.06)),
              col="primary", mat="cloth", role="detail", pri=1.6)
    else:
        ff = _fender(zf, r, r + 0.06, 0.04, 20, 150, tw + 0.16, dome=0.6)
        piece(H, "FenderF", "Steer", ff, col="metal", mat="metal", role="detail", pri=1.3)
        rfz = _fender(zb, r, r + 0.06, 0.04, 15, 165 if not tandem else 150, tw + 0.16, dome=0.6)
        rack = [sweep([(s * 0.2, r, zb), (s * 0.24, r + 1.05, zb + 0.05)], 0.03, segs=6) for s in (-1, 1)]
        rack += [sweep([(s * 0.22, r + 1.08, zb - 0.6), (s * 0.22, r + 1.08, zb + 0.45)], 0.03, segs=6) for s in (-1, 1)]
        rack += [sweep([(-0.22, r + 1.08, z), (0.22, r + 1.08, z)], 0.025, segs=6) for z in (zb - 0.6, zb - 0.2, zb + 0.2, zb + 0.45)]
        rack += [sweep([(0, r + 1.08, zb - 0.6), tuple(seats[-1] - st_dir * 0.4)], 0.025, segs=6)]
        piece(H, "Rack", "Chassis", merge(rfz, *rack), col="metal", mat="metal", role="detail", pri=1.2)
        guard = loft([(bb[2] - 0.3, bb[1] + 0.36, 0.04, 0.08, 0.06), (bb[2] + 0.1, bb[1] + 0.43, 0.05, 0.1, 0.08), (zb - 0.3, r + 0.26, 0.05, 0.08, 0.07), (zb - 0.15, r + 0.24, 0.04, 0.06, 0.05)], n=12, sub=3)
        piece(H, "ChainGuard", "Chassis", xf(guard, (0.32, 0, 0)), col="primary", mat="metal", role="detail", pri=1.5)
        R.glow_lamp(H, "Taillight", "Chassis", K.box((0.16, 0.12, 0.06), (0, r + 1.0, zb + 0.5), r=0.03), R.TAIL, pri=1.6)
        if not tandem:
            by0, bz = ht_top[1] - 0.2, ht_top[2] - 0.75
            bk = R.loft_y([(by0, bz, 0.46, 0.34, 0.34, 4.0), (by0 + 0.2, bz, 0.5, 0.37, 0.37, 4.0), (by0 + 0.4, bz, 0.53, 0.4, 0.4, 4.0), (by0 + 0.6, bz, 0.56, 0.42, 0.42, 4.0)],
                          n=28, sub=3, cap=True)
            lip = R.loft_y([(by0 + 0.58, bz, 0.6, 0.46, 0.46, 4.0), (by0 + 0.68, bz, 0.6, 0.46, 0.46, 4.0)], n=28, sub=1)
            weave = kit_stripes(lambda P: P[:, 1], 7.5, width=0.4, depth=0.35)
            piece(H, "Basket", "Steer", merge(bk, sweep([(0, ht_top[1] + 0.2, ht_top[2] - 0.32), (0, top[1] - 0.05, top[2] - 0.05)], 0.03, segs=6)), col="wood", mat="wood", role="detail",
                  pri=1.0, pattern=weave, ao=False)
            piece(H, "BasketRim", "Steer", lip, col="darkWood", mat="wood", role="detail", pri=1.6)
            R.glow_lamp(H, "Headlight", "Steer", K.lamp((0, ht_top[1] - 0.35, ht_top[2] - 1.12), 0.1, 0.06), R.WARM)
        else:
            R.glow_lamp(H, "Headlight", "Steer", K.lamp((0, ht_bot[1] - 0.1, ht_bot[2] - 0.16), 0.1, 0.06), R.WARM)
        bell = merge(K.cyl(0.07, 0.1, (-0.55, gy + 0.03, gz - 0.12), "y", segs=12), K.D.revolve([(0, 0), (0.02, 0.09), (0.09, 0.08), (0.11, 0)], segs=12, axis=1, spline=2))
        bell = merge(K.cyl(0.05, 0.03, (-0.55, gy + 0.03, gz - 0.12), "y", segs=8), xf(K.D.revolve([(0, 0), (0.02, 0.09), (0.09, 0.08), (0.11, 0)], segs=12, axis=1, spline=2), (-0.55, gy + 0.05, gz - 0.12)))
        piece(H, "Bell", "Steer", bell, col="metal", mat="metal", role="detail", pri=2.0)
        stand = sweep([(-0.15, bb[1] - 0.05, bb[2] + 0.45), (-0.38, 0.05, bb[2] + 0.75)], 0.035, segs=6)
        piece(H, "Kickstand", "Chassis", stand, col="darker", mat="metal", role="detail", pri=1.9)

    def mv(pose, u):
        K.add(pose, "Crank", (0, 0, 0, -TAU * u, 0, 0))
        if tandem:
            K.add(pose, "Crank2", (0, 0, 0, -TAU * u, 0, 0))

    K.vehicle_clips(H, wheels, susp="Chassis", height=3.6, length=zb - zf + 2 * r, sym=12, steer=("Steer",), roll=1.8, bob=0.4, turns=1.0, attack="honk", extra_move=mv)
    H.socket("head", (0, 4.6, 0), "Chassis")
    H.socket("mouth", (0, 2.5, zf - r), "Chassis")
    H.socket("exhaust", (0, r, zb + r), "Chassis")
    H.rig.update({"head": "Chassis"})
    hip = (0.0, seats[0][1] + 0.2, seats[0][2] + 0.06)
    extra = None
    if tandem:
        H.socket("seat2", (0.0, seats[1][1] + 0.2, seats[1][2] + 0.06), "Chassis")
        extra = {"seats": 2}
    R.finish_mount(H, "Seat", hip, (-1.4, hip[2]), extra=extra, seat_size=(0.5, 0.15, 0.7))
    return H


# ==================================================================================================== real-scale boards (stand rides)
def _deck_shape(L, W, t, kick, kick_len, y_top, ex=5.0):
    """Board deck lofted along Z: rounded popsicle nose / tail, kicktails bent up over kick_len at both ends,
    rails rounded by a boxy superellipse section. Top surface at y_top in the middle."""
    e = L / 2 - W / 2
    zs = list(np.linspace(-L / 2, -e, 5)) + list(np.linspace(-e * 0.6, e * 0.6, 3)) + list(np.linspace(e, L / 2, 5))
    secs = []
    for z in zs:
        a = abs(z)
        hw = W / 2 * math.sqrt(max(1 - ((a - e) / (W / 2)) ** 2, 0.0)) if a > e else W / 2
        hw = max(hw, W * 0.06)
        u = min(max((a - (L / 2 - kick_len)) / kick_len, 0), 1)
        secs.append((z, y_top - t / 2 + kick * u * u, hw, t / 2, t / 2, ex))
    return loft(secs, n=28, sub=2)


def skateboard_real():
    """Skateboard at real scale (2.9 studs): concave maple deck with kicked nose and tail, grip tape with a printed
    band, deck bolts, two cast trucks (baseplate, kingpin with bushings, hanger and axle) and four urethane wheels
    with bearing cores on their own Wheel bones. Stand ride: the seat socket is the deck top (feet)."""
    H = _new("skateboard", pv("#E76F51", "#F4D35E", darker="#1C1C1F", metal="#B8BEC6"))
    H.bone("Chassis", "Body", (0, 0, 0))
    L, W, top, t = 2.9, 0.92, 0.42, 0.08
    deck = _deck_shape(L, W, t, 0.2, 0.42, top)
    stripe = kit_stripes(lambda P: P[:, 2], 2.2, width=0.18, depth=0.35)
    piece(H, "Deck", "Chassis", deck, col="primary", mat="wood", role="body", pri=0.5, pattern=stripe)
    grip = _deck_shape(L - 0.06, W - 0.06, 0.012, 0.2, 0.41, top + 0.008)
    piece(H, "Seat", "Chassis", grip, col="darker", mat="rubber", role="seat", pri=0.9)
    bolts = merge(*[K.cyl(0.012, 0.028, (x, top + 0.016, z), "y", segs=8) for x in (-0.1, 0.1) for z in (-0.88, -1.02, 0.88, 1.02)])
    piece(H, "Bolts", "Chassis", bolts, col="metal", mat="metal", role="detail", pri=2.0)
    wheels = []
    for z, tag in ((-0.95, "F"), (0.95, "B")):
        ay = 0.14
        sg = -1 if z < 0 else 1
        tr = [K.box((0.34, 0.05, 0.42), (0, top - t - 0.025, z), r=0.015),                                   # baseplate
              sweep([(0, top - t - 0.05, z + sg * 0.05), (0, ay + 0.05, z - sg * 0.06)], 0.035, segs=8),     # kingpin
              K.cyl(0.07, 0.07, (0, ay + 0.12, z - sg * 0.02), "y", segs=12),                              # bushing seat
              loft([(-0.08, 0, 0.42, 0.07, 0.05, 3.2), (0.08, 0, 0.42, 0.07, 0.05, 3.2)], n=16, sub=1),     # hanger (placed below)
              sweep([(-0.54, ay, z), (0.54, ay, z)], 0.025, segs=8)]
        tr[3] = xf(tr[3], (0, ay + 0.03, z))
        piece(H, "Truck" + tag, "Chassis", merge(*tr), col="metal", mat="metal", role="detail", pri=0.9)
        bush = merge(K.cyl(0.05, 0.065, (0, ay + 0.18, z - sg * 0.03), "y", segs=10), K.cyl(0.05, 0.065, (0, ay + 0.07, z - sg * 0.03), "y", segs=10))
        piece(H, "Bushings" + tag, "Chassis", bush, col="secondary", mat="plastic", role="detail", pri=1.8)
        for s, sd in ((1, "R"), (-1, "L")):
            pos = (s * 0.42, ay, z)
            b = H.bone(f"Wheel{tag}{sd}", "Chassis", pos)
            wm = K.lathe_profile([(-0.07, 0.05), (-0.075, 0.1), (-0.06, 0.135), (0.06, 0.14), (0.075, 0.11), (0.07, 0.05)], 18, "x")
            core = K.lathe_profile([(-0.075, 0.0), (-0.075, 0.05), (0.072, 0.05), (0.072, 0.0)], 12, "x")
            piece(H, f"Wheel{tag}{sd}", b, xf(wm, pos), col="white", mat="plastic", role="wheel", pri=1.0, fallback="Cylinder")
            piece(H, f"Hub{tag}{sd}", b, xf(core, pos), col="secondary", mat="plastic", role="wheel", pri=1.6, fallback="Cylinder")
            wheels.append((b, 0.14))

    def atk(pose, s):  # ollie: tail snap, pop, level out, land
        up = K._bump(s, 0.12, 0.8)
        K.add(pose, "Chassis", (0, 0.9 * up, 0, 0.32 * K._bump(s, 0.08, 0.4) - 0.12 * K._bump(s, 0.4, 0.75), 0, 0))

    K.vehicle_clips(H, wheels, susp="Chassis", height=0.6, length=L, sym=8, roll=0.8, bob=0.6, turns=2.0, attack="honk", extra_attack=atk)
    H.socket("head", (0, 2.6, 0), "Chassis")
    H.socket("mouth", (0, top, -1.45), "Chassis")
    H.socket("exhaust", (0, top, 1.45), "Chassis")
    H.rig.update({"head": "Chassis"})
    R.finish_mount(H, "Seat", (0, top + 0.02, 0), (-1.4, 0.0), stand=True, extra={"stance": "side"}, seat_size=(0.8, 0.05, 2.2))
    return H


def hoverboard_real():
    """Hoverboard at real scale (4.2 studs): sculpted board with an upturned nose and a raised tail kick, inset grip
    pad, a glowing trim line around the rails, two thruster nacelles underneath with glowing intakes and exhaust
    rings (Thruster* glow pieces), twin tail fins and a stabiliser keel. Hovers ~1 stud up (deck top 1.0)."""
    H = _new("hoverboard", pv("#3A86FF", "#E8ECF2", darker="#1B1E26", metal="#AEB7C2"), gait="hover")
    H.bone("Chassis", "Body", (0, 1.0, 0))
    L, W, top, t = 4.2, 1.3, 1.0, 0.16
    body = loft([(-2.1, top + 0.32, 0.12, 0.04, 0.05, 2.4), (-1.9, top + 0.12, 0.45, 0.06, 0.08, 2.6), (-1.4, top - 0.02, 0.62, 0.07, 0.11, 3.0), (-0.3, top - 0.07, 0.66, 0.07, 0.12, 3.2),
                 (0.8, top - 0.07, 0.64, 0.07, 0.12, 3.2), (1.7, top - 0.0, 0.52, 0.07, 0.1, 3.0), (2.08, top + 0.12, 0.3, 0.05, 0.07, 2.6)], n=32, sub=5)
    piece(H, "Deck", "Chassis", body, col="primary", mat="plastic", role="body", pri=0.5)
    pad = loft([(-1.55, top + 0.025, 0.45, 0.025, 0.02, 3.0), (-0.3, top + 0.0, 0.52, 0.03, 0.02, 3.4), (0.9, top + 0.0, 0.5, 0.03, 0.02, 3.4), (1.6, top + 0.07, 0.38, 0.025, 0.02, 3.0)], n=24, sub=4)
    piece(H, "Seat", "Chassis", pad, col="darker", mat="rubber", role="seat", pri=0.8)
    rail = loft([(-2.0, top + 0.18, 0.36, 0.015, 0.015, 2.4), (-1.6, top + 0.0, 0.63, 0.016, 0.016, 2.8), (-0.3, top - 0.075, 0.675, 0.016, 0.016, 3.2), (0.8, top - 0.075, 0.655, 0.016, 0.016, 3.2),
                 (1.7, top - 0.01, 0.535, 0.016, 0.016, 3.0), (2.02, top + 0.1, 0.34, 0.015, 0.015, 2.6)], n=32, sub=5)
    R.glow_lamp(H, "TrimGlow", "Chassis", rail, R.CYAN, pri=1.5)
    belly = loft([(-1.6, top - 0.16, 0.42, 0.06, 0.08), (0.0, top - 0.2, 0.48, 0.08, 0.1), (1.5, top - 0.17, 0.38, 0.06, 0.08)], n=22, sub=4)
    piece(H, "Belly", "Chassis", belly, col="secondary", mat="metal", role="detail", pri=1.0)
    nac = []
    glow_in, glow_out = [], []
    for z in (-1.05, 1.05):
        nac.append(R.loft_y([(top - 0.62, z, 0.36, 0.36, 0.36, 2.0), (top - 0.5, z, 0.44, 0.44, 0.44, 2.0), (top - 0.3, z, 0.42, 0.42, 0.42, 2.0), (top - 0.18, z, 0.3, 0.3, 0.3, 2.0)], n=26, sub=3))
        glow_out.append(K.tube_ring(0.33, 0.2, 0.04, axis="y", segs=26, pos=(0, top - 0.64, z)))
        glow_out.append(K.cyl(0.03, 0.2, (0, top - 0.63, z), "y", segs=20))
        glow_in += [K.box((0.06, 0.05, 0.3), (s * 0.43, top - 0.42, z), r=0.02) for s in (-1, 1)]
    piece(H, "Nacelles", "Chassis", merge(*nac), col="metal", mat="metal", role="detail", pri=0.9)
    R.glow_lamp(H, "ThrusterJets", "Chassis", merge(*glow_out), R.CYAN, pri=1.2)
    R.glow_lamp(H, "ThrusterVents", "Chassis", merge(*glow_in), R.CYAN, pri=1.7)
    fins = []
    for s in (-1, 1):
        fp = round_poly(np.array([(1.35, top - 0.1), (1.95, top - 0.05), (2.05, top - 0.42), (1.75, top - 0.45)]), [0.05, 0.08, 0.06, 0.1], 2)
        fins.append(xf(extrude(fp, 0.05, bevel=0.02, seg=1), (s * 0.42, 0, 0)))
    keel = extrude(round_poly(np.array([(-0.5, top - 0.18), (0.5, top - 0.18), (0.3, top - 0.38), (-0.3, top - 0.38)]), 0.06, 2), 0.06, bevel=0.02, seg=1)
    piece(H, "Fins", "Chassis", merge(*fins, keel), col="primary", mat="plastic", role="detail", pri=1.2)
    lamps = merge(K.box((0.3, 0.05, 0.05), (0, top + 0.22, -2.03), r=0.02, rot_=(30, 0, 0)))
    R.glow_lamp(H, "Headlight", "Chassis", lamps, R.WARM, pri=1.8)
    R.glow_lamp(H, "Taillight", "Chassis", K.box((0.32, 0.05, 0.05), (0, top + 0.08, 2.07), r=0.02), R.TAIL, pri=1.8)
    K.mount(H, "Seat", (0, top + 0.03, 0), (0.9, 0.05, 3.0), "Chassis")
    H.socket("head", (0, top + 3.4, 0), "Chassis")
    H.socket("mouth", (0, top, -2.1), "Chassis")
    H.socket("exhaust", (0, top - 0.64, 1.05), "Chassis")
    H.rig.update({"head": "Chassis"})

    def move(t):
        u = t / 1.2
        return {"Chassis": (0, 0.06 * math.sin(TAU * u * 2), 0, -0.05 + 0.015 * math.sin(TAU * u * 2), 0, 0.07 * math.sin(TAU * u))}

    def idle(t):
        u = t / 2.4
        return {"Chassis": (0, 0.1 * math.sin(TAU * u), 0, 0.02 * math.sin(TAU * u * 2), 0.04 * math.sin(TAU * u), 0.025 * math.sin(TAU * u + 1))}

    def atk(t):
        s = t / 0.8
        return {"Chassis": (0, 0.7 * K._bump(s, 0.0, 0.75), -0.8 * K._bump(s, 0.2, 0.8), 0.3 * K._bump(s, 0.0, 0.4), TAU * K._ease((s - 0.1) / 0.6), 0)}

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1))
        return {"Chassis": (0, -0.1 * k, 0.3 * k, 0.2 * k, 0, 0.2 * math.sin(t * 30) * k)}

    H.clip("Move", 1.2, move, keys=20)
    H.clip("Idle", 2.4, idle, keys=20)
    H.clip("Attack", 0.8, atk, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=10, loop=False)
    H.rig["height"] = 1.4
    R.finish_mount(H, "Seat", (0, top + 0.03, 0), (-1.5, 0.0), stand=True, extra={"stance": "side", "hover": 1.0}, seat_size=(0.9, 0.05, 3.0))
    return H


def kick_scooter_real():
    """Kick scooter at real scale (3.3 studs): aluminium deck with grip and a kicked tail over the rear wheel
    (foot brake fender), headset with folding clamp, tall T-bar with grips, small spoked urethane wheels."""
    H = _new("scooter", pv("#7B2CBF", "#E0E0E0", metal="#C4CAD2", darker="#1C1D22"))
    top = 0.38
    zf, zb, r = -1.25, 1.3, 0.32
    H.bone("Chassis", "Body", (0, 0, 0))
    H.bone("Steer", "Chassis", (0, 0.9, -1.12))
    H.bone("WheelF", "Steer", (0, r, zf))
    H.bone("WheelB", "Chassis", (0, r, zb))
    wheels = [R.moto_wheel(H, "WheelF", "WheelF", (0, r, zf), r, 0.18, style="cast", spokes=5, rim_col="secondary", ri=r * 0.66, segs=24),
              R.moto_wheel(H, "WheelB", "WheelB", (0, r, zb), r, 0.18, style="cast", spokes=5, rim_col="secondary", ri=r * 0.66, segs=24)]
    deck = loft([(-1.0, top - 0.06, 0.3, 0.06, 0.06, 4.0), (-0.85, top - 0.06, 0.38, 0.06, 0.07, 4.0), (0.8, top - 0.06, 0.38, 0.06, 0.07, 4.0), (1.0, top - 0.04, 0.3, 0.05, 0.06, 4.0)], n=20, sub=3)
    neck = sweep([(0, top - 0.08, -0.9), (0, 0.62, -1.05), (0, 0.78, -1.1)], 0.08, segs=10)
    tailarm = merge(*[sweep([(s * 0.18, top - 0.08, 0.85), (s * 0.15, r, zb)], 0.05, segs=8) for s in (-1, 1)])
    piece(H, "Chassis", "Chassis", merge(deck, neck, tailarm), col="primary", mat="metal", role="body", pri=0.5)
    grip = loft([(-0.82, top + 0.005, 0.33, 0.012, 0.01, 4.0), (0.78, top + 0.005, 0.33, 0.012, 0.01, 4.0)], n=20, sub=1)
    piece(H, "Seat", "Chassis", grip, col="darker", mat="rubber", role="seat", pri=0.8)
    brake = loft([(0.95, top + 0.08, 0.14, 0.03, 0.02), (1.3, r + 0.38, 0.2, 0.04, 0.03), (1.62, r + 0.2, 0.15, 0.03, 0.02)], n=14, sub=3)
    piece(H, "Brake", "Chassis", brake, col="darker", mat="metal", role="detail", pri=1.2)
    gy, gz = top + 2.0 + 1.15, -1.0
    stem = [sweep([(0, 0.75, -1.12), (0, gy - 0.05, gz - 0.12)], 0.065, segs=12), sweep([(0, 1.1, -1.11), (0, 1.35, -1.1)], 0.085, segs=12),
            K.box((0.22, 0.12, 0.2), (0, 1.48, -1.08), r=0.04), sweep([(0, gy, gz - 0.12), (-0.85, gy, gz - 0.12)], 0.045, segs=8), sweep([(0, gy, gz - 0.12), (0.85, gy, gz - 0.12)], 0.045, segs=8)]
    for s in (-1, 1):
        stem.append(sweep([(s * 0.1, 0.78, -1.12), (s * 0.1, r, zf)], 0.04, segs=8))
    piece(H, "Stem", "Steer", merge(*stem), col="metal", mat="metal", role="detail", pri=0.8)
    grips = merge(*[sweep([(s * 0.5, gy, gz - 0.12), (s * 0.92, gy, gz - 0.12)], 0.07, segs=10) for s in (-1, 1)])
    piece(H, "Grips", "Steer", grips, col="darker", mat="rubber", role="detail", pri=1.2)
    clamp = merge(K.box((0.2, 0.12, 0.22), (0, 0.95, -1.12), r=0.04), K.box((0.12, 0.08, 0.3), (0.12, 0.95, -1.0), r=0.03))
    piece(H, "Clamp", "Steer", clamp, col="secondary", mat="plastic", role="detail", pri=1.5)
    ffend = _fender(zf, r, r + 0.04, 0.03, 40, 150, 0.22, dome=0.5)
    piece(H, "FenderF", "Steer", ffend, col="primary", mat="plastic", role="detail", pri=1.5)
    K.vehicle_clips(H, wheels, susp="Chassis", height=3.6, length=3.3, sym=5, steer=("Steer",), roll=1.2, bob=0.4, turns=2.0, attack="honk")
    H.socket("head", (0, top + 3.4, 0), "Chassis")
    H.socket("mouth", (0, 0.6, -1.6), "Chassis")
    H.socket("exhaust", (0, 0.5, 1.6), "Chassis")
    H.rig.update({"head": "Chassis"})
    R.finish_mount(H, "Seat", (0, top + 0.02, 0.3), (-1.3, 0.3), stand=True, extra={"stance": "forward"}, seat_size=(0.6, 0.05, 1.6))
    return H


# ==================================================================================================== real-scale quad + snowmobile
def atv_real():
    """Quad bike at real scale (6.8 studs): fat knobby tyres on steel wheels with steering knuckles, A-arm front
    suspension with coil-over shocks, sculpted front and rear plastics with flared fenders, twin glowing headlights in
    the nose, tubular front and rear racks, bumper, footboards with tread plates, straddle seat on a fuel tank,
    handlebar with a centre pod on its own Bars bone, engine block and a rear silencer."""
    H = _new("atv", pv("#C1121F", "#1B1B1F", darker="#1B1B1F", metal="#B6BDC6", steel="#4A5059"))
    seat = (0.0, 2.6, 0.45)
    H.bone("Chassis", "Body", (0, 0, 0))
    xw, zf, zb, rf, rb = 1.45, -2.1, 2.05, 0.85, 0.9
    wheels, steer = [], []
    wk = dict(rim="steel", rim_col="steel", knobby=0.1, lugs=14, rim_r=0.55, segs=24)
    for s, tag in ((1, "R"), (-1, "L")):
        steer.append(H.bone("SteerF" + tag, "Chassis", (s * (xw - 0.4), rf, zf)))
        wheels += K.add_wheels(H, [dict(name="WheelF" + tag, pos=(s * xw, rf, zf), r=rf, w=0.78, side=s)], parent="SteerF" + tag, **wk)[0]
    for s, tag in ((1, "R"), (-1, "L")):
        wheels += K.add_wheels(H, [dict(name="WheelB" + tag, pos=(s * xw, rb, zb), r=rb, w=0.95, side=s)], parent="Chassis", **wk)[0]
    # suspension: A-arms + shocks (front), rear axle + shocks
    sus = []
    for s in (-1, 1):
        for dy in (-0.18, 0.2):
            sus.append(sweep([(s * 0.35, rf + dy, zf - 0.35), (s * (xw - 0.42), rf + dy * 0.6, zf), (s * 0.35, rf + dy, zf + 0.35)], 0.05, segs=8))
        sus.append(R.spring((s * 0.55, 2.0, zf + 0.2), (s * (xw - 0.55), rf + 0.25, zf + 0.05), 0.12, wire=0.035, turns=6))
        sus.append(sweep([(s * 0.55, 2.05, zf + 0.2), (s * (xw - 0.55), rf + 0.2, zf + 0.05)], 0.05, segs=8))
        sus.append(R.spring((s * 0.45, 2.05, zb - 0.55), (s * 0.8, rb + 0.1, zb - 0.1), 0.11, wire=0.035, turns=6))
    sus.append(sweep([(-xw + 0.4, rb, zb), (xw - 0.4, rb, zb)], 0.09, segs=10))
    piece(H, "Suspension", "Chassis", merge(*sus), col="primary", mat="metal", role="detail", pri=1.1)
    knuck = []
    for s, tag in ((1, "R"), (-1, "L")):
        k = merge(K.box((0.2, 0.5, 0.3), (s * (xw - 0.48), rf, zf), r=0.05), K.cyl(0.2, 0.2, (s * (xw - 0.35), rf, zf), "x", segs=12))
        piece(H, "Knuckle" + tag, "SteerF" + tag, k, col="steel", mat="metal", role="detail", pri=1.5)
    # frame + footboards + bumper + racks
    fr = [sweep([(s * 0.42, 0.75, -2.7), (s * 0.45, 0.62, -1.2), (s * 0.45, 0.62, 1.4), (s * 0.4, 0.9, 2.55)], 0.07, segs=8) for s in (-1, 1)]
    fr += [sweep([(s * 0.42, 0.75, -2.7), (s * 0.4, 2.05, -1.9), (s * 0.4, 2.3, -0.9), (s * 0.35, 2.15, 1.6), (s * 0.4, 1.9, 2.55)], 0.06, segs=8) for s in (-1, 1)]
    fr.append(sweep([(-0.6, 0.85, -3.25), (-0.65, 1.55, -3.3), (0.65, 1.55, -3.3), (0.6, 0.85, -3.25)], 0.07, segs=8))   # bumper
    fr += [sweep([(s * 0.6, 0.85, -3.25), (s * 0.42, 0.78, -2.65)], 0.06, segs=8) for s in (-1, 1)]
    for z0, z1, y in ((-3.05, -1.75, 2.4), (1.45, 3.05, 2.45)):
        for x in (-0.95, 0.95):
            fr.append(sweep([(x, y, z0), (x, y, z1)], 0.04, segs=6))
        fr += [sweep([(-0.95, y, z), (0.95, y, z)], 0.035, segs=6) for z in np.linspace(z0, z1, 4)]
        fr += [sweep([(x * 0.5, y - 0.3, z0 + 0.2), (x, y, (z0 + z1) / 2)], 0.035, segs=6) for x in (-0.95, 0.95)]
    piece(H, "Frame", "Chassis", merge(*fr), col="darker", mat="metal", role="detail", pri=0.9)
    boards = []
    for s in (-1, 1):
        boards.append(K.box((0.62, 0.1, 2.0), (s * 0.95, 1.22, -0.05), r=0.03))
        boards += [cbox((0.58, 0.05, 0.06), (s * 0.95, 1.29, z), c=0.01) for z in np.linspace(-0.9, 0.8, 7)]
    piece(H, "Footboards", "Chassis", merge(*boards), col="steel", mat="metal", role="detail", pri=1.0)
    # plastics: front hood + flared fenders, rear deck + fenders
    hood = loft([(-3.0, 1.75, 0.55, 0.12, 0.2, 2.6), (-2.75, 1.95, 0.82, 0.22, 0.3), (-2.0, 2.15, 0.9, 0.25, 0.35), (-1.25, 2.2, 0.8, 0.2, 0.35), (-0.75, 2.15, 0.55, 0.12, 0.3)], n=28, sub=4)
    rear = loft([(1.0, 2.05, 0.6, 0.12, 0.3), (1.6, 2.15, 0.95, 0.15, 0.3), (2.6, 2.2, 0.95, 0.15, 0.3), (3.05, 2.1, 0.75, 0.1, 0.25)], n=28, sub=4)
    piece(H, "Body", "Chassis", merge(hood, rear), col="primary", mat="plastic", role="body", pri=0.5)
    fF = merge(_fender(zf, rf, rf + 0.16, 0.08, 15, 170, 1.05, dome=0.35), K.box((0.75, 0.08, 1.3), (-0.45, 1.85, zf + 0.3), r=0.03, rot_=(0, 0, -10)))
    fB = merge(_fender(zb, rb, rb + 0.16, 0.08, 10, 165, 1.2, dome=0.35), K.box((0.65, 0.08, 1.2), (-0.45, 1.95, zb - 0.25), r=0.03, rot_=(0, 0, -10)))
    mpiece(H, "FenderF#", "Chassis", xf(fF, (xw, 0, 0)), col="primary", mat="plastic", role="body", pri=0.6)
    mpiece(H, "FenderB#", "Chassis", xf(fB, (xw, 0, 0)), col="primary", mat="plastic", role="body", pri=0.6)
    tank = loft([(-1.35, 2.35, 0.3, 0.15, 0.25), (-1.0, 2.5, 0.55, 0.3, 0.35), (-0.3, 2.45, 0.6, 0.25, 0.4), (0.1, 2.3, 0.45, 0.1, 0.3)], n=24, sub=3)
    piece(H, "Tank", "Chassis", tank, col="primary", mat="plastic", role="body", pri=0.7)
    st = loft([(-0.3, 2.42, 0.35, 0.08, 0.2), (0.3, 2.5, 0.52, 0.12, 0.22), (1.3, 2.55, 0.5, 0.12, 0.22), (1.8, 2.52, 0.4, 0.1, 0.18)], n=24, sub=3)
    piece(H, "Seat", "Chassis", st, col="secondary", mat="cloth", role="seat", pri=0.7)
    R.glow_lamp(H, "Headlight", "Chassis", merge(*[xf(K.box((0.36, 0.16, 0.06), (0, 0, 0), r=0.05, seg=1), (s * 0.42, 2.0, -3.0), r=(10, s * 15, 0)) for s in (-1, 1)]), R.WARM)
    R.glow_lamp(H, "Taillight", "Chassis", K.box((0.36, 0.12, 0.05), (0, 2.1, 3.08), r=0.03), R.TAIL, pri=1.6)
    eng = merge(K.box((0.8, 0.8, 1.1), (0, 1.2, 0.1), r=0.15, seg=1), *[cbox((0.86, 0.04, 0.9), (0, 1.0 + 0.1 * k, 0.1), c=0.01) for k in range(5)],
                K.cyl(0.1, 0.32, (0.42, 1.2, 0.0), "x", segs=16))
    piece(H, "Engine", "Chassis", eng, col="gunmetal", mat="metal", role="detail", pri=1.0)
    ex = merge(sweep([(0.2, 1.5, -0.35), (0.45, 1.4, 0.5), (0.6, 1.8, 1.6), (0.65, 1.95, 2.5)], 0.08, segs=10), sweep([(0.65, 1.95, 2.3), (0.66, 1.97, 3.0)], 0.16, segs=14))
    piece(H, "Exhaust", "Chassis", ex, col="metal", mat="metal", role="detail", pri=1.2)
    gy, gz = seat[1] + 1.12, seat[2] - 1.42
    H.bone("Bars", "Chassis", (0, gy - 0.6, gz - 0.3))
    bars = [sweep([(0, 2.4, gz - 0.45), (0, gy - 0.15, gz - 0.3)], 0.07, segs=10), K.box((0.55, 0.28, 0.32), (0, gy - 0.05, gz - 0.25), r=0.08, seg=1),
            sweep([(-1.25, gy, gz), (-0.6, gy + 0.02, gz - 0.12), (0.6, gy + 0.02, gz - 0.12), (1.25, gy, gz)], 0.05, segs=8),
            sweep([(-0.4, gy + 0.12, gz - 0.2), (0.4, gy + 0.12, gz - 0.2)], 0.035, segs=6)]
    bars += [cbox((0.1, 0.05, 0.42), (s * 0.95, gy + 0.05, gz - 0.3), c=0.02, rot_=(0, -s * 15, 0)) for s in (-1, 1)]
    piece(H, "Handlebars", "Bars", merge(*bars), col="darker", mat="metal", role="detail", pri=1.0)
    grips = merge(*[sweep([(s * 0.85, gy, gz - 0.02), (s * 1.32, gy, gz)], 0.075, segs=10) for s in (-1, 1)])
    piece(H, "Grips", "Bars", grips, col="tyre", mat="rubber", role="detail", pri=1.3)
    K.vehicle_clips(H, wheels, susp="Chassis", height=3.8, length=6.6, sym=5, steer=steer + ["Bars"], roll=1.0, bob=1.0, turns=1.4)
    H.socket("head", (0, 4.5, 0), "Chassis")
    H.socket("mouth", (0, 1.4, -3.3), "Chassis")
    H.socket("exhaust", (0.66, 1.97, 3.05), "Chassis")
    H.rig.update({"head": "Chassis"})
    R.finish_mount(H, "Seat", seat, (-2.6, 0.4), seat_size=(1.0, 0.2, 1.6))
    return H


def snowmobile_real():
    """Snowmobile at real scale (10 studs): sculpted hood with air intakes and a tinted windshield, twin headlights,
    long straddle seat over the tunnel, rubber drive track with cleats on drive / idler wheels and bogies, running
    boards for the feet, two skis on spindles with shocks (SkiR / SkiL steer), handlebar on its own Bars bone with
    hand guards, rear bumper, tail light and side exhaust."""
    H = _new("snowmobile", pv("#FFD60A", "#1B1B1F", darker="#1B1B1F", metal="#B6BDC6", steel="#4A5059"))
    seat = (0.0, 2.25, 0.7)
    H.bone("Chassis", "Body", (0, 0, 0))
    wheels = []
    belt = K.track_loop(-0.6, 3.6, 0.0, 0.5, 0.42, 1.5, cleats=30)
    piece(H, "Track", "Chassis", belt, col="tyre", mat="rubber", role="wheel", pri=0.8)
    for z, r, nm in ((-0.6, 0.48, "Drive"), (3.6, 0.4, "Idler")):
        b = H.bone(nm, "Chassis", (0, r + 0.02, z))
        piece(H, nm, b, K.road_wheel(r * 0.85, 1.35, (0, r + 0.02, z)), col="steel", mat="metal", role="wheel", pri=1.4)
        wheels.append((b, r))
    bog = merge(*[K.cyl(0.18, 0.18, (s * 0.45, 0.22, z), "x", segs=12) for s in (-1, 1) for z in (0.5, 1.4, 2.4)], *[sweep([(s * 0.45, 0.22, -0.3), (s * 0.45, 0.22, 3.3)], 0.05, segs=6) for s in (-1, 1)])
    piece(H, "Bogies", "Chassis", bog, col="steel", mat="metal", role="detail", pri=1.4)
    tunnel = loft([(-0.9, 1.4, 0.88, 0.3, 0.38, 4.0), (1.0, 1.45, 0.9, 0.3, 0.38, 4.0), (3.4, 1.4, 0.85, 0.25, 0.3, 4.0), (4.0, 1.4, 0.7, 0.2, 0.25, 4.0)], n=24, sub=3)
    rb = []
    for s in (-1, 1):
        rb.append(K.box((0.55, 0.08, 2.4), (s * 1.12, 0.98, 0.55), r=0.03))
        rb += [cbox((0.5, 0.04, 0.05), (s * 1.12, 1.04, z), c=0.01) for z in np.linspace(-0.5, 1.6, 8)]
        rb.append(K.box((0.12, 0.45, 2.4), (s * 1.38, 1.15, 0.55), r=0.04))
    piece(H, "Tunnel", "Chassis", merge(tunnel, *rb), col="darker", mat="metal", role="body", pri=0.7)
    hood = loft([(-4.25, 1.05, 0.25, 0.12, 0.2, 2.4), (-4.0, 1.3, 0.7, 0.3, 0.4, 2.8), (-3.2, 1.6, 1.0, 0.55, 0.65, 3.0), (-2.2, 1.8, 1.1, 0.7, 0.8, 3.0), (-1.4, 1.85, 1.0, 0.6, 0.85, 3.0),
                 (-0.9, 1.75, 0.85, 0.45, 0.75, 3.0)], n=32, sub=4)
    piece(H, "Hood", "Chassis", hood, col="primary", mat="plastic", role="body", pri=0.5)
    side = merge(*[xf(K.box((0.08, 0.5, 1.3), (0, 0, 0), r=0.03), (s * 1.08, 1.75, -2.0), r=(0, 0, s * 12)) for s in (-1, 1)],
                 *[cbox((0.04, 0.04, 1.0), (s * 1.13, 1.6 + 0.12 * k, -2.0), c=0.01) for s in (-1, 1) for k in range(3)], K.box((1.0, 0.1, 0.9), (0, 2.5, -2.5), r=0.05, rot_=(-12, 0, 0)))
    piece(H, "Vents", "Chassis", side, col="darker", mat="plastic", role="detail", pri=1.3)
    ws = loft([(-1.95, 2.55, 0.85, 0.02, 0.02), (-1.6, 3.0, 0.75, 0.02, 0.02), (-1.35, 3.35, 0.55, 0.02, 0.02)], n=20, sub=3)
    piece(H, "WindshieldGlass", "Chassis", ws, col="glass", mat="glass", role="window", pri=1.1, tr=0.45, ao=False)
    R.glow_lamp(H, "Headlight", "Chassis", merge(*[xf(K.box((0.45, 0.16, 0.06), (0, 0, 0), r=0.05, seg=1), (s * 0.42, 1.65, -3.88), r=(-25, s * 18, 0)) for s in (-1, 1)]), R.WARM)
    st = loft([(-0.55, 2.05, 0.4, 0.1, 0.25), (0.0, 2.15, 0.55, 0.12, 0.3), (1.6, 2.2, 0.55, 0.12, 0.3), (2.7, 2.25, 0.45, 0.12, 0.28), (3.0, 2.15, 0.3, 0.08, 0.2)], n=24, sub=3)
    piece(H, "Seat", "Chassis", st, col="secondary", mat="cloth", role="seat", pri=0.7)
    bump = merge(sweep([(-0.85, 1.6, 3.9), (-0.85, 1.6, 4.4), (0.85, 1.6, 4.4), (0.85, 1.6, 3.9)], 0.06, segs=8), K.box((1.4, 0.4, 0.06), (0, 1.15, 4.1), r=0.03))
    piece(H, "Bumper", "Chassis", bump, col="metal", mat="metal", role="detail", pri=1.4)
    R.glow_lamp(H, "Taillight", "Chassis", K.box((0.6, 0.1, 0.06), (0, 1.75, 4.02), r=0.03), R.TAIL, pri=1.6)
    ex = merge(sweep([(0.6, 1.4, -1.2), (0.95, 1.5, -0.5), (1.0, 1.55, 0.2)], 0.1, segs=10), sweep([(1.0, 1.55, 0.15), (1.02, 1.56, 0.35)], 0.07, segs=10))
    piece(H, "Exhaust", "Chassis", ex, col="metal", mat="metal", role="detail", pri=1.6)
    for s, tag in ((1, "R"), (-1, "L")):
        x = s * 1.35
        b = H.bone("Ski" + tag, "Chassis", (x, 0.6, -2.4))
        ski = loft([(-4.3, 0.55, 0.06, 0.04, 0.04), (-4.0, 0.25, 0.22, 0.04, 0.05), (-3.4, 0.08, 0.25, 0.04, 0.05), (-1.4, 0.07, 0.24, 0.04, 0.05), (-1.15, 0.1, 0.2, 0.03, 0.04)], n=16, sub=3)
        ski = xf(ski, (x, 0, 0))
        spindle = merge(sweep([(x, 0.15, -2.4), (x, 0.8, -2.35), (s * 0.95, 1.3, -2.2)], 0.07, segs=8), K.box((0.18, 0.25, 0.4), (x, 0.25, -2.4), r=0.04))
        shock = merge(R.spring((x, 0.4, -2.3), (s * 0.9, 1.4, -1.9), 0.11, wire=0.03, turns=6), sweep([(x, 0.35, -2.3), (s * 0.9, 1.45, -1.88)], 0.045, segs=8))
        piece(H, "Ski" + tag, b, ski, col="darker", mat="plastic", role="detail", pri=0.9)
        piece(H, "Spindle" + tag, b, merge(spindle, shock), col="steel", mat="metal", role="detail", pri=1.2)
    gy, gz = seat[1] + 1.12, seat[2] - 1.42
    H.bone("Bars", "Chassis", (0, gy - 0.6, gz - 0.25))
    bars = [sweep([(0, 2.15, gz - 0.6), (0, gy - 0.12, gz - 0.25)], 0.07, segs=10), sweep([(-1.2, gy, gz), (-0.5, gy + 0.03, gz - 0.2), (0.5, gy + 0.03, gz - 0.2), (1.2, gy, gz)], 0.05, segs=8),
            K.box((0.45, 0.2, 0.28), (0, gy - 0.02, gz - 0.25), r=0.06)]
    for s in (-1, 1):
        bars.append(loft([(gz - 0.55, gy + 0.05, 0.08, 0.15, 0.15), (gz - 0.35, gy + 0.05, 0.12, 0.2, 0.2), (gz - 0.1, gy + 0.02, 0.06, 0.12, 0.12)], n=12, sub=2))
        bars[-1] = xf(bars[-1], (s * 1.18, 0, 0))
    piece(H, "Handlebars", "Bars", merge(*bars), col="darker", mat="metal", role="detail", pri=1.0)
    grips = merge(*[sweep([(s * 0.75, gy + 0.01, gz - 0.12), (s * 1.25, gy, gz)], 0.075, segs=10) for s in (-1, 1)])
    piece(H, "Grips", "Bars", grips, col="tyre", mat="rubber", role="detail", pri=1.3)
    K.vehicle_clips(H, wheels, susp="Chassis", height=3.6, length=8.7, sym=8, steer=("SkiR", "SkiL", "Bars"), roll=1.2, bob=0.8, turns=1.4)
    H.socket("head", (0, 4.2, 0), "Chassis")
    H.socket("mouth", (0, 1.4, -4.3), "Chassis")
    H.socket("exhaust", (1.02, 1.56, 0.4), "Chassis")
    H.rig.update({"head": "Chassis"})
    R.finish_mount(H, "Seat", seat, (-2.4, 0.6), seat_size=(1.0, 0.2, 2.0))
    return H


# ==================================================================================================== armed encased walkers
def _walker_clips(H, legs, body_rest, walk, move, idle_extra=None, move_extra=None, attack=None, hit_bone="Body", flat_feet=True):
    """Walk / Move / Idle / Attack / Hit for a legged walker with IK-planted feet.
    legs: dicts {root, mid, end, p0, p1, p2 (rest pivots), phase, bend, yaw, foot (optional end bone to keep flat)}.
    walk / move: dicts {len, stride, lift, duty, bob, roll, yaw, pitch}."""
    def gait(spec, extra):
        L = spec["len"]

        def fn(t):
            u = t / L
            pose = {}
            bob = -spec["bob"] * (0.5 + 0.5 * math.cos(TAU * u * spec.get("beats", 2)))
            rz = spec["roll"] * math.sin(TAU * u)
            ry = spec["yaw"] * math.sin(TAU * u)
            rxp = spec.get("pitch", 0.0) * math.sin(TAU * u * 2)
            bpos = np.array([0.0, bob, 0.0])
            Rb = R.axis_rot((1, 0, 0), rxp) @ R.axis_rot((0, 1, 0), ry) @ R.axis_rot((0, 0, 1), rz)
            pose["Body"] = (0.0, bob, 0.0, *R.euler_xyz(Rb))
            for lg in legs:
                w = (u + lg["phase"]) % 1.0
                dz, dy = R.foot_path(w, spec["stride"], spec["lift"], spec["duty"])
                tw = np.array(lg["p2"], float) + np.array([0.0, dy, dz])
                # into the body frame (Body pivot rest = body_rest)
                q = Rb.T @ (tw - (np.array(body_rest) + bpos)) + np.array(body_rest)
                R1, R2, R3 = R.leg_ik(lg["p0"], lg["p1"], lg["p2"], q, bend=lg["bend"], yaw=lg.get("yaw", False))
                pose[lg["root"]] = R.pose_entry(R1)
                pose[lg["mid"]] = R.pose_entry(R2)
                if lg.get("foot"):
                    # keep the sole level in the world: undo the body tilt too, tip the toe up in swing
                    toe = -0.25 * math.sin(math.pi * (w - spec["duty"]) / (1 - spec["duty"])) if w >= spec["duty"] else 0.0
                    Rf = (R1 @ R2).T @ Rb.T @ R.axis_rot((1, 0, 0), toe) if not lg.get("yaw") else R3
                    pose[lg["foot"]] = R.pose_entry(Rf)
            if extra:
                extra(pose, u)
            return pose
        return fn

    H.clip("Walk", walk["len"], gait(walk, move_extra), keys=24)
    H.clip("Move", move["len"], gait(move, move_extra), keys=24)

    def idle(t):
        u = t / 4.0
        pose = {"Body": (0, 0.04 * math.sin(TAU * u * 2), 0, 0.01 * math.sin(TAU * u), 0.02 * math.sin(TAU * u), 0)}
        b = pose["Body"]
        Rb = R.axis_rot((1, 0, 0), b[3]) @ R.axis_rot((0, 1, 0), b[4])
        for lg in legs:
            q = Rb.T @ (np.array(lg["p2"], float) - (np.array(body_rest) + np.array([0, b[1], 0]))) + np.array(body_rest)
            R1, R2, R3 = R.leg_ik(lg["p0"], lg["p1"], lg["p2"], q, bend=lg["bend"], yaw=lg.get("yaw", False))
            pose[lg["root"]] = R.pose_entry(R1)
            pose[lg["mid"]] = R.pose_entry(R2)
            if lg.get("foot"):
                pose[lg["foot"]] = R.pose_entry((R1 @ R2).T @ Rb.T if not lg.get("yaw") else R3)
        if idle_extra:
            idle_extra(pose, u)
        return pose

    H.clip("Idle", 4.0, idle, keys=24)
    if attack:
        H.clip("Attack", attack[0], attack[1], keys=18, loop=False)

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        return {hit_bone: (0, -0.08 * k, 0.25 * k, 0.08 * k, 0, 0.05 * math.sin(t * 38) * k)}

    H.clip("Hit", 0.45, hit, keys=10, loop=False)


def mech_suit_real():
    """Armed bipedal mech suit (13.5 studs tall), pilot ENCASED: armoured cockpit tub with the pilot's seat, control
    sticks and a glowing console under a wrap-around canopy (glass), roof armour, back reactor pack with a glowing
    core and vents, shoulder pauldrons, a right-arm rotary cannon (spinning Barrel bone, `muzzle` socket) and a
    left-arm missile pod, heavy legs (hip / knee / ankle bones) with hydraulic pistons, knee guards and broad
    three-toed feet. Walk / Move clips plant the feet with two-bone IK (no sliding); Attack fires the cannon."""
    H = Hero("mech suit", plan="Biped", gait="stomp", tags=["vehicle", "mech", "ride"])
    H.preview = pv("#7D8794", "#E36414", darker="#23262C", metal="#A9B2BD", steel="#4D545E", gunmetal="#33383F")
    body_rest = (0.0, 7.6, 0.3)
    H.body(body_rest)
    seat = (0.0, 9.15, 0.35)
    # ---------------------------------------------------------------- cockpit tub, back pack, canopy, roof
    tub = loft([(-2.9, 8.55, 1.5, 0.45, 0.6, 3.0), (-2.5, 8.5, 2.35, 0.65, 0.95, 3.2), (-1.0, 8.45, 2.65, 0.7, 1.15, 3.4), (1.0, 8.5, 2.65, 0.7, 1.15, 3.4),
                (2.5, 8.6, 2.4, 0.6, 1.0, 3.2), (2.95, 8.7, 1.9, 0.45, 0.7, 3.0)], n=32, sub=4)
    piece(H, "Hull", "Body", tub, col="primary", mat="metal", role="body", pri=0.4)
    belly = loft([(-2.4, 7.25, 1.8, 0.35, 0.35, 3.0), (2.4, 7.3, 1.8, 0.35, 0.35, 3.0)], n=24, sub=1)
    joints = merge(belly, *[K.cyl(0.9, 0.85, (s * 2.25, 7.45, 0.25), "x", segs=20) for s in (-1, 1)])
    piece(H, "Pelvis", "Body", joints, col="gunmetal", mat="metal", role="body", pri=0.6)
    back = loft([(1.35, 10.7, 2.3, 2.3, 1.75, 3.6), (2.0, 10.8, 2.4, 2.4, 1.85, 3.8), (2.9, 10.8, 2.2, 2.2, 1.7, 3.6), (3.35, 10.7, 1.6, 1.8, 1.4, 3.0)], n=28, sub=3)
    piece(H, "BackPack", "Body", back, col="primary", mat="metal", role="body", pri=0.5)
    vents = merge(*[cbox((2.6, 0.08, 0.1), (0, 9.7 + 0.28 * k, 3.38), c=0.02) for k in range(6)], *[K.cyl(0.5, 0.32, (s * 1.2, 12.55, 2.4), "y", segs=16) for s in (-1, 1)],
                  *[K.tube_ring(0.36, 0.26, 0.2, axis="y", pos=(s * 1.2, 12.85, 2.4), segs=16) for s in (-1, 1)])
    piece(H, "Vents", "Body", vents, col="gunmetal", mat="metal", role="detail", pri=1.2)
    core = merge(K.cyl(0.12, 0.55, (0, 11.6, 3.36), "z", segs=20), *[K.box((0.12, 1.2, 0.08), (s * 2.18, 10.6, 1.9), r=0.03) for s in (-1, 1)])
    R.glow_lamp(H, "ReactorGlow", "Body", core, R.CYAN, pri=1.3)
    roof = loft([(-0.2, 13.05, 1.7, 0.18, 0.12, 3.0), (0.6, 13.1, 2.1, 0.25, 0.15, 3.2), (1.5, 13.0, 2.2, 0.22, 0.15, 3.2)], n=24, sub=3)
    piece(H, "Roof", "Body", roof, col="secondary", mat="metal", role="detail", pri=0.8)
    can = loft([(-2.75, 9.15, 1.4, 0.4, 0.05, 2.4), (-2.5, 9.25, 2.05, 1.5, 0.15, 2.6), (-1.6, 9.2, 2.3, 3.0, 0.2, 2.8), (-0.4, 9.2, 2.35, 3.75, 0.2, 2.8),
                (0.6, 9.2, 2.35, 3.85, 0.2, 2.8), (1.4, 9.2, 2.3, 3.75, 0.2, 2.8)], n=32, sub=4)
    piece(H, "CanopyGlass", "Body", can, col="glass", mat="glass", role="window", pri=0.7, tr=0.55, ao=False)
    frame = []
    for z in (-1.2, 0.3):
        top = 9.2 + (3.0 if z < -1 else 3.8)
        frame.append(sweep([(-2.33, 9.3, z), (-2.2, top - 0.6, z), (-1.0, top + 0.02, z), (1.0, top + 0.02, z), (2.2, top - 0.6, z), (2.33, 9.3, z)], 0.1, segs=8))
    frame.append(sweep([(0, 12.95, 1.3), (0, 12.6, -0.6), (0, 11.4, -1.85), (0, 9.9, -2.55)], 0.09, segs=8))
    piece(H, "CanopyFrame", "Body", merge(*frame), col="gunmetal", mat="metal", role="detail", pri=1.0)
    # ---------------------------------------------------------------- interior
    st = R.merge(K.seat_mesh(seat, w=1.6, d=1.2, back=2.4, cushion=0.3, recline=8.0), K.box((1.2, 0.5, 0.25), (0, seat[1] + 2.45, seat[2] + 0.75), r=0.1))
    piece(H, "Seat", "Body", st, col="darker", mat="cloth", role="seat", pri=0.9)
    con = [K.box((3.2, 0.7, 0.8), (0, 9.15, -2.1), r=0.12, rot_=(-20, 0, 0))]
    for s in (-1, 1):
        con.append(K.box((0.55, 0.85, 1.3), (s * 1.6, 9.3, -1.1), r=0.1))
        con.append(sweep([(s * 1.55, 9.75, -1.25), (s * 1.52, 10.25, -1.32)], 0.07, segs=8))
        con.append(K.box((0.18, 0.32, 0.18), (s * 1.52, 10.35, -1.33), r=0.06))
    piece(H, "Console", "Body", merge(*con), col="gunmetal", mat="metal", role="detail", pri=1.0)
    scr = merge(xf(K.box((1.5, 0.45, 0.04), (0, 0, 0), r=0.04), (0, 9.62, -2.37), r=(-20, 0, 0)), *[K.box((0.04, 0.3, 0.5), (s * 1.89, 9.55, -1.1), r=0.02) for s in (-1, 1)])
    R.glow_lamp(H, "Screens", "Body", scr, R.CYAN, pri=1.6)
    lamps = merge(*[xf(K.box((0.5, 0.22, 0.08), (0, 0, 0), r=0.06, seg=1), (s * 1.35, 8.35, -3.0), r=(0, s * 15, 0)) for s in (-1, 1)])
    R.glow_lamp(H, "Headlight", "Body", lamps, R.WARM, pri=1.4)
    trim = merge(*[cbox((0.1, 0.12, 4.4), (s * 2.66, 8.85, 0.0), c=0.03) for s in (-1, 1)], cbox((3.0, 0.12, 0.1), (0, 7.95, -2.85), c=0.03))
    piece(H, "Trim", "Body", trim, col="secondary", mat="metal", role="detail", pri=1.5)
    # ---------------------------------------------------------------- legs
    legs = []
    for s, tag in ((1, "R"), (-1, "L")):
        p0, p1, p2 = (s * 2.3, 7.45, 0.25), (s * 2.45, 4.5, -0.55), (s * 2.45, 1.35, 0.25)
        H.bone("Hip" + tag, "Body", p0)
        H.bone("Knee" + tag, "Hip" + tag, p1)
        H.bone("Ankle" + tag, "Knee" + tag, p2)
        x = s * 2.42
        th = merge(loft([(-0.65, 0, 0.62, 0.55, 0.55, 3.0), (0.5, 0, 0.7, 0.62, 0.62, 3.0)], n=20, sub=1) if False else
                   R.loft_y([(4.6, -0.5, 0.68, 0.62, 0.68, 3.0), (5.6, -0.25, 0.82, 0.78, 0.84, 3.2), (6.6, 0.05, 0.84, 0.8, 0.86, 3.2), (7.3, 0.2, 0.72, 0.7, 0.7, 3.0)], n=24, sub=3))
        th = xf(th, (x, 0, 0))
        piece(H, "Thigh" + tag, "Hip" + tag, th, col="primary", mat="metal", role="limb", pri=0.6)
        kn = merge(K.cyl(1.25, 0.7, (x, 4.5, -0.55), "x", segs=20), xf(loft([(-0.4, 0, 0.66, 0.66, 0.36, 3.0), (0.4, 0, 0.6, 0.55, 0.3, 3.0)], n=18, sub=1), (x, 4.65, -1.35)))
        piece(H, "KneeGuard" + tag, "Knee" + tag, kn, col="secondary", mat="metal", role="limb", pri=0.8)
        sh = R.loft_y([(1.5, 0.25, 0.58, 0.58, 0.52, 3.0), (2.4, 0.0, 0.74, 0.85, 0.66, 3.2), (3.5, -0.3, 0.8, 0.9, 0.66, 3.2), (4.3, -0.5, 0.64, 0.62, 0.5, 3.0)], n=24, sub=3)
        piece(H, "Shin" + tag, "Knee" + tag, xf(sh, (x, 0, 0)), col="primary", mat="metal", role="limb", pri=0.6)
        pis = merge(sweep([(x + s * 0.55, 6.6, 0.55), (x + s * 0.62, 4.9, 0.1)], 0.16, segs=10), sweep([(x + s * 0.62, 5.2, 0.18), (x + s * 0.66, 3.4, 0.55)], 0.1, segs=10))
        piece(H, "Piston" + tag, "Hip" + tag, pis, col="metal", mat="metal", role="detail", pri=1.4)
        ank = merge(K.cyl(1.0, 0.45, (x, 1.35, 0.25), "x", segs=18))
        foot = loft([(-2.0, 0.42, 0.75, 0.2, 0.42, 3.0), (-1.4, 0.52, 0.95, 0.35, 0.52, 3.4), (-0.3, 0.68, 1.0, 0.6, 0.68, 3.6), (0.8, 0.6, 0.9, 0.5, 0.6, 3.4), (1.45, 0.45, 0.6, 0.3, 0.45, 3.0)], n=26, sub=3)
        toes = merge(*[xf(loft([(-0.45, 0, 0.18, 0.15, 0.2), (0.0, 0, 0.22, 0.2, 0.22), (0.45, 0, 0.16, 0.12, 0.16)], n=12, sub=2), (x + dx, 0.22, -2.15 + 0.15 * abs(dx)), r=(0, -dx * 18, 0))
                       for dx in (-0.55, 0.0, 0.55)])
        piece(H, "Foot" + tag, "Ankle" + tag, merge(xf(foot, (x, 0, 0)), ank), col="gunmetal", mat="metal", role="foot", pri=0.7)
        piece(H, "Toes" + tag, "Ankle" + tag, toes, col="steel", mat="metal", role="foot", pri=1.2)
        legs.append(dict(root="Hip" + tag, mid="Knee" + tag, end="Ankle" + tag, foot="Ankle" + tag, p0=p0, p1=p1, p2=p2, phase=0.0 if s > 0 else 0.5, bend=(0, 0, -1)))
    # ---------------------------------------------------------------- arms: right rotary cannon, left missile pod
    for s, tag in ((1, "R"), (-1, "L")):
        sh_p, el_p = (s * 3.35, 11.2, 0.4), (s * 3.75, 9.5, 0.3)
        H.bone("Arm" + tag, "Body", sh_p)
        H.bone("Forearm" + tag, "Arm" + tag, el_p)
        pad = R.loft_y([(10.3, 0.4, 0.95, 1.2, 1.1, 3.0), (11.3, 0.4, 1.05, 1.35, 1.2, 3.2), (12.0, 0.4, 0.8, 1.0, 0.95, 3.0), (12.25, 0.4, 0.45, 0.6, 0.55, 2.6)], n=24, sub=3)
        pad = warp(xf(pad, (s * 3.45, 0, 0)), lambda V, s=s: np.column_stack([V[:, 0], V[:, 1] - 0.25 * (s * V[:, 0] - 3.45), V[:, 2]]))
        piece(H, "Pauldron" + tag, "Arm" + tag, pad, col="secondary", mat="metal", role="limb", pri=0.6)
        ua = merge(K.cyl(0.9, 0.55, (s * 3.0, 11.2, 0.4), "x", segs=18), R.loft_y([(9.5, 0.3, 0.42, 0.45, 0.45, 3.0), (10.8, 0.4, 0.5, 0.5, 0.5, 3.0)], n=18, sub=1))
        ua = merge(K.cyl(0.9, 0.55, (s * 3.0, 11.2, 0.4), "x", segs=18), xf(R.loft_y([(9.5, 0.3, 0.42, 0.45, 0.45, 3.0), (10.8, 0.4, 0.5, 0.5, 0.5, 3.0)], n=18, sub=1), (s * 3.75, 0, 0)),
                   K.cyl(0.9, 0.45, el_p, "x", segs=18))
        piece(H, "UpperArm" + tag, "Arm" + tag, ua, col="gunmetal", mat="metal", role="limb", pri=0.8)
    # right: rotary cannon housing on the forearm + spinning barrel cluster
    cx, cy = 3.75, 9.25
    hous = merge(R.loft([(-1.6, cy, 0.62, 0.62, 0.62, 3.0), (-0.6, cy, 0.7, 0.7, 0.7, 3.2), (0.6, cy, 0.62, 0.62, 0.62, 3.0)], n=24, sub=2), K.box((0.5, 0.5, 1.0), (0, cy + 0.75, -0.3), r=0.1),
                 K.tube_ring(0.62, 0.5, 0.3, axis="z", pos=(0, cy, -1.75), segs=22))
    piece(H, "CannonHousing", "ForearmR", xf(hous, (cx, 0, 0)), col="secondary", mat="metal", role="limb", pri=0.6)
    belt = sweep([(cx - 0.5, cy + 0.2, 0.3), (cx - 1.2, cy + 0.6, 0.9), (cx - 1.9, cy + 1.2, 1.3), (cx - 2.0, cy + 1.8, 1.4)], 0.13, segs=8)
    piece(H, "AmmoFeed", "ForearmR", belt, col="gold", mat="metal", role="detail", pri=1.5)
    H.bone("Barrel", "ForearmR", (cx, cy, -2.0))
    brl = [K.cyl(0.3, 0.42, (cx, cy, -2.05), "z", segs=18)]
    for k in range(6):
        a = TAU * k / 6
        brl.append(sweep([(cx + 0.27 * math.cos(a), cy + 0.27 * math.sin(a), -1.9), (cx + 0.27 * math.cos(a), cy + 0.27 * math.sin(a), -4.0)], 0.09, segs=8))
    brl += [K.tube_ring(0.42, 0.34, 0.14, axis="z", pos=(cx, cy, z), segs=18) for z in (-3.0, -3.9)]
    piece(H, "Barrels", "Barrel", merge(*brl), col="steel", mat="metal", role="detail", pri=0.9)
    H.socket("muzzle", (cx, cy, -4.15), "Barrel")
    # left: missile pod
    lx, ly = -3.8, 9.35
    pod = merge(K.box((1.5, 1.4, 2.4), (lx, ly, -0.9), r=0.18, seg=1), K.box((1.6, 0.18, 2.5), (lx, ly + 0.8, -0.9), r=0.06))
    piece(H, "MissilePod", "ForearmL", pod, col="secondary", mat="metal", role="limb", pri=0.7)
    tips = merge(*[xf(K.D.revolve([(0, 0), (0.12, 0.16), (0.35, 0.17), (0.37, 0)], segs=12, axis=2, spline=2), (lx + dx, ly + dy, -2.42)) for dx in (-0.4, 0.0, 0.4) for dy in (-0.35, 0.05, 0.45)])
    piece(H, "Missiles", "ForearmL", xf(tips, (0, 0, 0)), col="red", mat="metal", role="detail", pri=1.2)
    H.socket("muzzle2", (lx, ly, -2.6), "ForearmL")
    # ---------------------------------------------------------------- motion
    arm_rest = {"ArmR": 0.0, "ArmL": 0.0}

    def arms(pose, u):
        K.add(pose, "ArmR", (0, 0, 0, 0.06 * math.sin(TAU * u), 0, 0))
        K.add(pose, "ArmL", (0, 0, 0, -0.06 * math.sin(TAU * u), 0, 0))

    def idle_x(pose, u):
        K.add(pose, "ArmR", (0, 0, 0, 0.02 * math.sin(TAU * u * 2), 0, 0))
        K.add(pose, "ArmL", (0, 0, 0, 0.02 * math.sin(TAU * u * 2 + 1), 0, 0))

    def atk(t):
        s = t / 1.0
        aim = K._ease(s / 0.2) if s < 0.2 else (1 - K._ease((s - 0.8) / 0.2) if s > 0.8 else 1.0)
        p = {"Body": (0, -0.12 * aim, 0, 0, -0.1 * aim, 0)}
        kick = sum(K._bump(s, 0.22 + 0.1 * k, 0.32 + 0.1 * k) for k in range(5))
        K.add(p, "ArmR", (0, 0, 0, 0.12 * aim, 0.12 * aim, 0))
        K.add(p, "ForearmR", (0, 0, 0.12 * kick, 0.05 * kick, 0, 0))
        K.add(p, "Barrel", (0, 0, 0, 0, 0, TAU * 2 * K._ease((s - 0.15) / 0.7)))
        K.add(p, "ArmL", (0, 0, 0, 0.08 * aim, 0, 0))
        for lg in legs:
            R1, R2, R3 = R.leg_ik(lg["p0"], lg["p1"], lg["p2"], np.array(lg["p2"]) + np.array([0, 0.12 * aim, 0]), bend=lg["bend"])
            p[lg["root"]] = R.pose_entry(R1)
            p[lg["mid"]] = R.pose_entry(R2)
            p[lg["foot"]] = R.pose_entry(R3)
        return p

    walk = dict(len=1.7, stride=3.2, lift=0.9, duty=0.62, bob=0.18, roll=0.035, yaw=0.04, pitch=0.01)
    move = dict(len=1.15, stride=4.6, lift=1.3, duty=0.55, bob=0.3, roll=0.05, yaw=0.05, pitch=0.015)
    _walker_clips(H, legs, body_rest, walk, move, idle_extra=idle_x, move_extra=arms, attack=(1.0, atk))
    H.socket("head", (0, 13.6, 0), "Body")
    H.socket("mouth", (cx, cy, -4.15), "Barrel")
    H.socket("exhaust", (0, 12.9, 2.4), "Body")
    H.rig.update({"head": "Body", "legsAuthored": True, "height": 13.5})
    R.finish_mount(H, "Seat", seat, (-3.2, 1.5), bone="Body", seat_size=(1.6, 0.3, 1.2),
                   extra={"stride": move["stride"], "walkStride": walk["stride"], "encased": True})
    return H


def spider_walker_real():
    """Armed eight-legged spider walker (16 studs across the legs), pilot ENCASED: armoured hull with the pilot's
    tub, seat, sticks and console under a bubble canopy (glass) with a roll frame, armoured abdomen with glowing
    vents, a cluster of glowing sensor eyes, a chin turret (Turret yaw / Gun pitch bones) with twin cannons and a
    `muzzle` socket, and eight jointed legs (Coxa yaw + lift / Tibia) walking an alternating tetrapod gait with
    IK-planted feet (Walk / Move)."""
    H = Hero("spider walker", plan="Spider", gait="scuttle", tags=["vehicle", "mech", "ride"])
    H.preview = pv("#3D4048", "#C1121F", darker="#1E2025", metal="#A6AFBA", steel="#4D545E", gunmetal="#2D3138")
    body_rest = (0.0, 4.6, 0.0)
    H.body(body_rest)
    seat = (0.0, 5.7, -0.7)
    hull = loft([(-3.3, 4.6, 1.3, 0.55, 0.7, 2.6), (-2.8, 4.65, 2.3, 0.85, 1.05, 3.0), (-1.2, 4.7, 2.65, 0.95, 1.2, 3.2), (0.6, 4.7, 2.7, 0.95, 1.2, 3.2),
                 (1.6, 4.75, 2.4, 0.95, 1.1, 3.0)], n=32, sub=4)
    piece(H, "Hull", "Body", hull, col="primary", mat="metal", role="body", pri=0.4)
    abd = loft([(0.9, 5.2, 1.8, 1.2, 1.0, 2.4), (1.8, 5.5, 2.5, 1.7, 1.4, 2.6), (3.3, 5.6, 2.6, 1.8, 1.6, 2.6), (4.8, 5.3, 1.9, 1.3, 1.3, 2.4), (5.6, 5.0, 0.6, 0.5, 0.5, 2.2)], n=32, sub=4)
    stripe = kit_stripes(lambda P: P[:, 2], 1.6, width=0.22, depth=0.45, region=lambda P: np.clip((P[:, 2] - 1.6) / 0.6, 0, 1))
    piece(H, "Abdomen", "Body", abd, col="primary", mat="metal", role="body", pri=0.5, pattern=stripe)
    glow = merge(*[K.box((0.1, 0.18, 2.4), (s * 2.6, 5.4, 3.2), r=0.05, rot_=(0, 0, s * -20)) for s in (-1, 1)], K.cyl(0.1, 0.38, (0, 5.2, 5.62), "z", segs=18))
    R.glow_lamp(H, "VentGlow", "Body", glow, (1.0, 0.25, 0.15), pri=1.4)
    can = loft([(-3.25, 5.55, 1.3, 0.35, 0.05, 2.4), (-2.9, 5.6, 1.9, 1.5, 0.1, 2.6), (-1.9, 5.6, 2.15, 3.0, 0.15, 2.8), (-0.6, 5.6, 2.2, 3.75, 0.15, 2.8), (0.6, 5.6, 2.1, 3.7, 0.15, 2.6),
                (1.25, 5.6, 1.7, 3.0, 0.1, 2.4)], n=32, sub=4)
    piece(H, "CanopyGlass", "Body", can, col="glass", mat="glass", role="window", pri=0.7, tr=0.55, ao=False)
    frame = [sweep([(-2.18, 5.65, z), (-2.0, 7.8, z), (-1.0, 9.38, z), (1.0, 9.38, z), (2.0, 7.8, z), (2.18, 5.65, z)], 0.1, segs=8) for z in (-1.0,)]
    frame.append(sweep([(0, 9.3, 1.1), (0, 9.4, -0.6), (0, 8.3, -2.4), (0, 6.0, -3.25)], 0.09, segs=8))
    piece(H, "CanopyFrame", "Body", merge(*frame), col="gunmetal", mat="metal", role="detail", pri=1.0)
    st = merge(K.seat_mesh(seat, w=1.6, d=1.2, back=2.3, cushion=0.3, recline=8.0), K.box((1.2, 0.5, 0.25), (0, seat[1] + 2.35, seat[2] + 0.72), r=0.1))
    piece(H, "Seat", "Body", st, col="darker", mat="cloth", role="seat", pri=0.9)
    con = [K.box((3.0, 0.6, 0.7), (0, 5.75, -2.65), r=0.12, rot_=(-20, 0, 0))]
    for s in (-1, 1):
        con += [K.box((0.5, 0.7, 1.2), (s * 1.55, 5.9, -1.6), r=0.1), sweep([(s * 1.52, 6.2, -1.95), (s * 1.5, 6.75, -2.02)], 0.07, segs=8),
                K.box((0.18, 0.3, 0.18), (s * 1.5, 6.88, -2.03), r=0.06)]
    piece(H, "Console", "Body", merge(*con), col="gunmetal", mat="metal", role="detail", pri=1.0)
    eyes = merge(*[xf(K.lamp((0, 0, 0), r_, 0.1), (x, y, -3.3 + 0.04 * abs(x) * 3)) for x, y, r_ in ((-0.75, 4.55, 0.2), (0.75, 4.55, 0.2), (-0.3, 4.35, 0.13), (0.3, 4.35, 0.13),
                                                                                                  (-1.15, 4.75, 0.1), (1.15, 4.75, 0.1))],
                 xf(K.box((1.2, 0.35, 0.04), (0, 0, 0), r=0.04), (0, 6.25, -3.08), r=(-20, 0, 0)))
    R.glow_lamp(H, "Eyes", "Body", eyes, (1.0, 0.22, 0.15), pri=1.2)
    # chin turret
    H.bone("Turret", "Body", (0, 3.75, -2.6))
    H.bone("Gun", "Turret", (0, 3.55, -3.0))
    tb = merge(R.loft_y([(3.15, -2.6, 0.75, 0.75, 0.75, 2.4), (3.75, -2.6, 0.95, 0.95, 0.95, 2.6), (4.05, -2.6, 0.8, 0.8, 0.8, 2.4)], n=22, sub=2))
    piece(H, "TurretBase", "Turret", tb, col="gunmetal", mat="metal", role="detail", pri=0.8)
    gun = [K.box((1.5, 0.6, 1.0), (0, 3.55, -3.1), r=0.15, seg=1)]
    for s in (-1, 1):
        gun += [sweep([(s * 0.42, 3.55, -3.4), (s * 0.42, 3.55, -5.4)], 0.13, segs=12), K.tube_ring(0.2, 0.12, 0.35, axis="z", pos=(s * 0.42, 3.55, -5.4), segs=14),
                K.cyl(0.6, 0.2, (s * 0.42, 3.55, -4.0), "z", segs=14)]
    piece(H, "Guns", "Gun", merge(*gun), col="steel", mat="metal", role="detail", pri=0.8)
    H.socket("muzzle", (0, 3.55, -5.65), "Gun")
    # legs
    legs = []
    for i, (z0, zf_, a) in enumerate(((-2.0, -4.9, 0), (-0.7, -1.9, 1), (0.6, 1.6, 2), (1.8, 4.9, 3))):
        for s, tag in ((1, "R"), (-1, "L")):
            nm = f"{i}{tag}"
            p0 = np.array([s * 2.35, 4.7, z0])
            p2 = np.array([s * (6.4 if i in (1, 2) else 5.8), 0.0, zf_])
            p1 = p0 + (p2 - p0) * 0.45 + np.array([0, 4.6, 0])
            H.bone("Coxa" + nm, "Body", tuple(p0))
            H.bone("Tibia" + nm, "Coxa" + nm, tuple(p1))
            fem = merge(ball(0.55, tuple(p0), segs=14), sweep([tuple(p0), tuple(p0 + (p1 - p0) * 0.5 + np.array([0, 0.25, 0])), tuple(p1)], [0.38, 0.42, 0.3], segs=12))
            arm_ = sweep([tuple(p0 + (p1 - p0) * 0.2 + np.array([0, 0.45, 0])), tuple(p0 + (p1 - p0) * 0.75 + np.array([0, 0.55, 0]))], 0.16, segs=8)
            tib = merge(ball(0.42, tuple(p1), segs=12), sweep([tuple(p1), tuple(p1 + (p2 - p1) * 0.45 + np.array([0, 0.1, 0]) + (p2 - p0) * np.array([0.04, 0, 0.04])), tuple(p2 + np.array([0, 0.35, 0]))],
                                                          [0.3, 0.26, 0.14], segs=12),
                        xf(K.D.revolve([(0, 0), (0.1, 0.16), (0.35, 0.12), (0.4, 0)], segs=10, axis=1, spline=2), tuple(p2)))
            piece(H, "Femur" + nm, "Coxa" + nm, merge(fem, arm_), col="primary", mat="metal", role="limb", pri=0.6 + 0.04 * i)
            piece(H, "Tibia" + nm, "Tibia" + nm, tib, col="secondary" if i in (0, 3) else "gunmetal", mat="metal", role="limb", pri=0.7 + 0.04 * i)
            grp = (i + (0 if s > 0 else 1)) % 2
            legs.append(dict(root="Coxa" + nm, mid="Tibia" + nm, end=None, p0=tuple(p0), p1=tuple(p1), p2=tuple(p2), phase=0.5 * grp + 0.06 * i, bend=(0, 1, 0), yaw=True))

    def idle_x(pose, u):
        K.add(pose, "Turret", (0, 0, 0, 0, 0.35 * math.sin(TAU * u), 0))
        K.add(pose, "Gun", (0, 0, 0, 0.06 * math.sin(TAU * u * 2), 0, 0))

    def atk(t):
        s = t / 1.0
        aim = K._ease(s / 0.2) if s < 0.2 else (1 - K._ease((s - 0.8) / 0.2) if s > 0.8 else 1.0)
        p = {"Body": (0, 0.15 * aim, 0, -0.06 * aim, 0, 0)}
        kick = sum(K._bump(s, 0.25 + 0.15 * k, 0.37 + 0.15 * k) for k in range(4))
        K.add(p, "Gun", (0, 0, 0.25 * kick, 0.08 * aim + 0.04 * kick, 0, 0))
        b = p["Body"]
        Rb = R.axis_rot((1, 0, 0), b[3])
        for lg in legs:
            q = Rb.T @ (np.array(lg["p2"], float) - (np.array(body_rest) + np.array([0, b[1], 0]))) + np.array(body_rest)
            R1, R2, _ = R.leg_ik(lg["p0"], lg["p1"], lg["p2"], q, bend=lg["bend"], yaw=True)
            p[lg["root"]] = R.pose_entry(R1)
            p[lg["mid"]] = R.pose_entry(R2)
        return p

    walk = dict(len=1.3, stride=2.2, lift=1.0, duty=0.55, bob=0.08, roll=0.02, yaw=0.02, beats=2)
    move = dict(len=0.8, stride=3.4, lift=1.3, duty=0.5, bob=0.12, roll=0.025, yaw=0.025, beats=2)
    _walker_clips(H, legs, body_rest, walk, move, idle_extra=idle_x, attack=(1.0, atk))
    H.socket("head", (0, 9.8, 0), "Body")
    H.socket("mouth", (0, 3.55, -5.65), "Gun")
    H.socket("exhaust", (0, 5.2, 5.7), "Body")
    H.rig.update({"head": "Body", "legsAuthored": True, "height": 9.6})
    R.finish_mount(H, "Seat", seat, (-3.4, -0.5), bone="Body", seat_size=(1.6, 0.3, 1.2), extra={"stride": move["stride"], "walkStride": walk["stride"], "encased": True})
    return H
