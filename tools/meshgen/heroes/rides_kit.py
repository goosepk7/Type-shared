"""Extra hard-surface helpers for the rides family (h_rides.py), on top of landveh_kit.

* loft: a smooth sculpted shell lofted through superellipse cross-sections along Z (tanks, fairings, cowls, seats,
  cockpit pods, armour), Catmull-Rom interpolated so a handful of sections gives a flowing form.
* sweep: a round tube along a Catmull-Rom path (frame tubes, exhaust headers, handlebars, cables, rails).
* moto wheels: round-crowned tyre (road or knobby), cast split-spoke / wire / disc rims, wave brake rotors.
* finish: the rider-relative mount table (real game scale: H.mount length / stand / seat), enter socket.

All builders return direct meshes (landveh_kit DMesh path), positioned in model space (studs).
"""
from __future__ import annotations

import math

import numpy as np

import direct as D
import landveh_kit as K
from landveh_kit import merge, xf, rod, cbox, piece, mirror

TAU = 2 * math.pi


# ================================================================================================ smooth normals
def _smooth(V, F):
    V = np.asarray(V, float)
    F = np.asarray(F, int)
    tri = V[F]
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    key = np.round(V * 1e5).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    acc = np.zeros((inv.max() + 1, 3))
    for c in range(3):
        np.add.at(acc, inv[F[:, c]], fn)
    N = acc[inv]
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return N


def _cr(P, sub):
    """Catmull-Rom resample of control rows P (K, d) with `sub` samples per span (end points kept)."""
    P = np.asarray(P, float)
    if len(P) < 3 or sub <= 1:
        return P
    ext = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for k in range(sub):
            u = k / sub
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    out.append(P[-1])
    return np.array(out)


# ================================================================================================ loft
def loft(secs, n=28, sub=4, cap=True, x0=0.0):
    """Smooth shell through cross-sections along Z.
    secs: rows (z, y, hw, ht, hb[, ex]) = section centre z / y, half width, half height above / below y, superellipse
    exponent (2 ellipse .. 4 boxy, default 2.6). Sections are spline-interpolated (`sub` per span). cap: close both
    ends with flat caps (hard normals); give the end sections a small size for a rounded nose instead."""
    S = []
    for s in secs:
        s = list(s) + [2.6] * (6 - len(s))
        S.append(s[:6])
    S = _cr(np.array(S, float), sub)
    th = np.linspace(0, TAU, n, endpoint=False)
    c, s_ = np.cos(th), np.sin(th)
    V, F = [], []
    for z, y, hw, ht, hb, ex in S:
        e = 2.0 / max(ex, 0.5)
        xs = x0 + hw * np.sign(c) * np.abs(c) ** e
        ys = y + np.where(s_ >= 0, ht, hb) * np.sign(s_) * np.abs(s_) ** e
        V += [(xs[i], ys[i], z) for i in range(n)]
    m = len(S)
    for k in range(m - 1):
        for i in range(n):
            j = (i + 1) % n
            a, b, cc, d = k * n + i, k * n + j, (k + 1) * n + j, (k + 1) * n + i
            F += [[a, b, cc], [a, cc, d]]
    V = np.array(V)
    F = np.array(F)
    N = _smooth(V, F)
    mesh = D._finish(V, N, F)
    if cap:
        caps = []
        for k, sgn in ((0, -1.0), (m - 1, 1.0)):
            ring = V[k * n:(k + 1) * n]
            ctr = ring.mean(0)
            Vc = np.vstack([ring, ctr])
            Nc = np.tile([0, 0, sgn], (n + 1, 1))
            Fc = np.array([[i, (i + 1) % n, n] for i in range(n)])
            caps.append(D._finish(Vc, Nc, Fc))
        mesh = merge(mesh, *caps)
    return K._orient(mesh)


def loft_y(secs, n=24, sub=4, cap=True):
    """Loft along Y (vertical: legs, posts, cockpit tubs). secs rows (y, z, hw, hd_front, hd_back[, ex]):
    centre y / z, half width, half depth toward -Z (front) and +Z (back)."""
    m = loft([(y, -z, hw, hf, hb, *ex) for (y, z, hw, hf, hb, *ex) in secs], n=n, sub=sub, cap=cap)
    # (x, y', z') = (x, -z_sec ... ) : rotate so the loft axis Z -> +Y and section "up" -> -Z (front)
    V = m.vertices
    Nn = m.direct_normals
    R = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)
    out = D._finish(V @ R.T, Nn @ R.T, m.faces)
    return K._orient(out)


# ================================================================================================ sweep
def sweep(pts, radius, segs=10, sub=4, cap=True, up=(0, 1, 0)):
    """Round tube along a Catmull-Rom path through `pts`; radius is a number or one per control point."""
    P = np.asarray(pts, float)
    R = np.full(len(P), float(radius)) if np.isscalar(radius) else np.asarray(radius, float)
    C = _cr(np.column_stack([P, R]), sub if len(P) > 2 else 1)
    if len(P) == 2:
        k = 2
        C = np.array([C[0] + (C[1] - C[0]) * t for t in np.linspace(0, 1, k)])
    Q, rr = C[:, :3], C[:, 3]
    T = np.gradient(Q, axis=0)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-12)
    u = np.asarray(up, float)
    if abs(T[0] @ u) > 0.9:
        u = np.array([1.0, 0, 0]) if abs(T[0][0]) < 0.9 else np.array([0, 0, 1.0])
    nrm = np.cross(T[0], u)
    nrm /= np.linalg.norm(nrm)
    frames = []
    for i in range(len(Q)):
        if i > 0:
            nrm = nrm - T[i] * (nrm @ T[i])
            nrm /= max(np.linalg.norm(nrm), 1e-12)
        b = np.cross(T[i], nrm)
        frames.append((nrm.copy(), b))
    th = np.linspace(0, TAU, segs, endpoint=False)
    V, N, F = [], [], []
    for i, (q, r) in enumerate(zip(Q, rr)):
        a, b = frames[i]
        for t in th:
            d = a * math.cos(t) + b * math.sin(t)
            V.append(q + d * r)
            N.append(d)
    m = len(Q)
    for k in range(m - 1):
        for i in range(segs):
            j = (i + 1) % segs
            a0, a1, b0, b1 = k * segs + i, k * segs + j, (k + 1) * segs + i, (k + 1) * segs + j
            F += [[a0, b0, b1], [a0, b1, a1]]
    mesh = D._finish(np.array(V), np.array(N), np.array(F))
    if cap:
        caps = []
        for k, sgn in ((0, -1.0), (m - 1, 1.0)):
            ring = np.array(V[k * segs:(k + 1) * segs])
            Vc = np.vstack([ring, Q[k]])
            Nc = np.tile(T[k] * sgn, (segs + 1, 1))
            Fc = np.array([[i, (i + 1) % segs, segs] for i in range(segs)])
            caps.append(D._finish(Vc, Nc, Fc))
        mesh = merge(mesh, *caps)
    return K._orient(mesh)


def ball(r, pos, segs=12):
    return xf(D.revolve([(-r, 0), (-r * 0.7, r * 0.72), (0, r), (r * 0.7, r * 0.72), (r, 0)], segs=segs, axis=1, spline=2), pos)


def spring(p0, p1, r, wire=0.04, turns=7, segs=5):
    """Coil spring from p0 to p1 (shock absorbers)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    Rm, c, L = K._frame(p0, p1)
    k = turns * 7
    pts = [(r * math.cos(TAU * turns * i / k), r * math.sin(TAU * turns * i / k), -L / 2 + L * i / k) for i in range(k + 1)]
    m = sweep(pts, wire, segs=segs, sub=1)
    return D.moved(m, offset=c, rot=Rm)


# ================================================================================================ wheels
def moto_tyre(ro, w, ri, segs=30, knobby=0.0, lugs=22, axis="x"):
    """Motorbike / bicycle tyre: round crown, bulging sidewalls. knobby > 0: staggered block lugs."""
    h = ro - ri
    hw = w / 2
    pts = [(-hw * 0.7, ri), (-hw * 0.98, ri + h * 0.35), (-hw * 0.95, ri + h * 0.62), (-hw * 0.72, ri + h * 0.86), (-hw * 0.38, ro - h * 0.02),
           (0.0, ro), (hw * 0.38, ro - h * 0.02), (hw * 0.72, ri + h * 0.86), (hw * 0.95, ri + h * 0.62), (hw * 0.98, ri + h * 0.35), (hw * 0.7, ri),
           (0.0, ri * 0.985)]
    m = K.lathe_profile(pts, segs, "x", closed=True, hard_deg=70)
    if knobby > 0:
        def f(V):
            r = np.hypot(V[:, 1], V[:, 2])
            a = np.arctan2(V[:, 2], V[:, 1])
            lug = (np.cos(a * lugs) > 0.0).astype(float)
            lug2 = (np.cos(a * lugs + math.pi) > 0.0).astype(float)
            row = np.where(np.abs(V[:, 0]) > hw * 0.45, lug2, lug)
            k = np.clip((r - (ro - h * 0.5)) / (h * 0.5), 0, 1) * row * knobby
            s = (r + k) / np.maximum(r, 1e-9)
            return np.column_stack([V[:, 0], V[:, 1] * s, V[:, 2] * s])
        m = K.warp(m, f)
    return m


def cast_rim(r, w, spokes=3, split=True, segs=30):
    """Sport cast rim about X: thin lip ring, hub and (split) curved spokes."""
    parts = [K.lathe_profile([(-w * 0.5, r * 0.9), (w * 0.5, r * 0.9), (w * 0.55, r * 1.0), (-w * 0.55, r * 1.0)], segs, "x", closed=True, hard_deg=40)]
    hub = K.lathe_profile([(-w * 0.75, 0), (-w * 0.75, r * 0.16), (-w * 0.4, r * 0.2), (w * 0.4, r * 0.2), (w * 0.75, r * 0.16), (w * 0.75, 0)], 16, "x")
    parts.append(hub)
    for k in range(spokes):
        a0 = TAU * k / spokes
        offs = (-0.13, 0.13) if split else (0.0,)
        for o in offs:
            pts = []
            for t in np.linspace(0, 1, 5):
                a = a0 + o * t + 0.12 * math.sin(math.pi * t)
                rad = r * (0.17 + 0.76 * t)
                pts.append((0.0, math.cos(a) * rad, math.sin(a) * rad))
            parts.append(sweep(pts, r * 0.045, segs=6, sub=2))
    return merge(*parts)


def wire_rim(r, w, spokes=32, hub_w=None, segs=30, spoke_r=0.016):
    hw = (hub_w or w * 1.4) / 2
    parts = [K.lathe_profile([(-w * 0.45, r * 0.9), (w * 0.45, r * 0.9), (w * 0.5, r * 1.0), (-w * 0.5, r * 1.0)], segs, "x", closed=True, hard_deg=40),
             K.lathe_profile([(-hw, 0), (-hw, r * 0.1), (-hw * 0.6, r * 0.07), (hw * 0.6, r * 0.07), (hw, r * 0.1), (hw, 0)], 12, "x")]
    for k in range(spokes):
        a = TAU * k / spokes
        sx = hw * 0.9 if k % 2 else -hw * 0.9
        a2 = a + (0.35 if k % 4 < 2 else -0.35)
        parts.append(rod((sx, math.cos(a) * r * 0.09, math.sin(a) * r * 0.09), (0.0, math.cos(a2) * r * 0.9, math.sin(a2) * r * 0.9), spoke_r, segs=3, bevel=0.002))
    return merge(*parts)


def rotor(r, x, thick=0.04, wave=10, holes=True):
    """Wave brake disc about X at offset x (+ carrier to the hub)."""
    ri = r * 0.72
    ring = K.tube_ring(r, ri, thick, axis="x", segs=32)
    if wave:
        def f(V):
            rad = np.hypot(V[:, 1], V[:, 2])
            a = np.arctan2(V[:, 2], V[:, 1])
            k = np.clip((rad - ri) / (r - ri), 0, 1)
            s = (rad - r * 0.05 * k * (0.5 + 0.5 * np.cos(a * wave))) / np.maximum(rad, 1e-9)
            return np.column_stack([V[:, 0], V[:, 1] * s, V[:, 2] * s])
        ring = K.warp(ring, f)
    parts = [ring]
    for k in range(5):
        a = TAU * k / 5
        parts.append(K.bar((0, math.cos(a) * r * 0.2, math.sin(a) * r * 0.2), (0, math.cos(a) * ri * 1.02, math.sin(a) * ri * 1.02), r * 0.12, thick * 1.2, r=0.01, up=(1, 0, 0)))
    return xf(merge(*parts), (x, 0, 0))


def caliper(pos, r, side=1, tilt=0.0):
    """Brake caliper hugging a rotor of radius r at `pos` (hub centre), sitting at angle tilt (deg, 0 = behind)."""
    a = math.radians(tilt)
    c = np.array([pos[0], pos[1] + math.sin(a) * r * 0.86, pos[2] + math.cos(a) * r * 0.86])
    body = K.box((0.16, r * 0.42, r * 0.24), c, r=0.04, rot_=(-math.degrees(a), 0, 0))
    return body


def moto_wheel(H, name, bone, pos, ro, w, style="cast", spokes=3, knobby=0.0, rim_col="darker", discs=(), disc_r=None, tyre_col="tyre",
               rotor_col="steel", pri=1.0, ri=None, segs=30, lugs=22):
    """Tyre + rim (+ brake rotors) pieces on `bone` for a bike wheel centred at pos. discs: x offsets of rotors."""
    ri = ri if ri is not None else ro * 0.7
    t = xf(moto_tyre(ro, w, ri, segs=segs, knobby=knobby, lugs=lugs), pos)
    piece(H, name + "Tyre", bone, t, col=tyre_col, mat="rubber", role="wheel", pri=pri, fallback="Cylinder")
    if style == "cast":
        rm = cast_rim(ri, w * 0.8, spokes=spokes, segs=segs)
    elif style == "wire":
        rm = wire_rim(ri, w * 0.75, spokes=spokes, segs=segs)
    else:  # disc / scooter
        rm = merge(K.lathe_profile([(-w * 0.45, ri * 0.88), (w * 0.45, ri * 0.88), (w * 0.5, ri * 1.0), (-w * 0.5, ri * 1.0)], segs, "x", closed=True, hard_deg=40),
                   K.lathe_profile([(-w * 0.4, 0), (-w * 0.4, ri * 0.9), (-w * 0.1, ri * 0.85), (w * 0.3, ri * 0.55), (w * 0.45, ri * 0.25), (w * 0.48, 0)], segs, "x"),
                   *[xf(K.cyl(w * 0.15, ri * 0.06, (0, 0, 0), "x", segs=6, bevel=0.005), (w * 0.38, math.cos(TAU * k / 5) * ri * 0.33, math.sin(TAU * k / 5) * ri * 0.33)) for k in range(5)])
    piece(H, name + "Rim", bone, xf(rm, pos), col=rim_col, mat="metal", role="wheel", pri=pri + 0.2, fallback="Cylinder")
    if discs:
        dr = disc_r or ri * 0.85
        dm = merge(*[rotor(dr, x) for x in discs])
        piece(H, name + "Disc", bone, xf(dm, pos), col=rotor_col, mat="metal", role="wheel", pri=pri + 0.8)
    return (bone, ro)


# ================================================================================================ lights
def glow_lamp(H, name, bone, mesh, col=(1.0, 0.97, 0.85), pri=1.3):
    """An emissive light piece (Neon in game): headlights, tail lights, thrusters."""
    return piece(H, name, bone, mesh, col=list(col), mat="glass", role="light", pri=pri, ao=False, glow=True)


WARM = (1.0, 0.95, 0.78)
COOL = (0.78, 0.92, 1.0)
TAIL = (1.0, 0.12, 0.1)
AMBER = (1.0, 0.62, 0.12)
CYAN = (0.35, 0.9, 1.0)


# ================================================================================================ mount table
def finish_mount(H, seat_part, seat, enter, stand=False, bone="Chassis", length=None, extra=None, seat_size=(0.8, 0.2, 0.8)):
    """Real-scale ride contract: seat socket = rider HIP point (stand: the feet point on the deck), enter socket on
    the ground at the rider's left, H.mount.length = model Z length in studs (from the built pieces' bounds)."""
    if length is None:
        lo = H.bpos("BoundLo") if "BoundLo" in H.bidx else np.zeros(3)
        hi = H.bpos("BoundHi") if "BoundHi" in H.bidx else np.zeros(3)
        length = float(hi[2] - lo[2])
    K.mount(H, seat_part, seat, seat_size, bone)
    H.mount["length"] = round(float(length), 2)
    if stand:
        H.mount["stand"] = True
    if extra:
        H.mount.update(extra)
    H.socket("enter", (enter[0], 0.0, enter[1]))
    return H.mount


# ================================================================================================ walker IK
def axis_rot(axis, ang):
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    x, y, z = a
    c, s = math.cos(ang), math.sin(ang)
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


def euler_xyz(Rm):
    """Decompose Rm = Rx(a) @ Ry(b) @ Rz(c) (Roblox CFrame.Angles order, as kit clips use) -> (a, b, c)."""
    b = math.asin(max(-1.0, min(1.0, Rm[0, 2])))
    a = math.atan2(-Rm[1, 2], Rm[2, 2])
    c = math.atan2(-Rm[0, 1], Rm[0, 0])
    return a, b, c


def leg_ik(root, mid, end, target, bend=(0, 0, -1), yaw=False):
    """Two-bone IK for a leg whose bones have identity rest rotations.
    root / mid / end: rest positions (body frame) of the hip, knee and ankle pivots; target: wanted ankle position
    (body frame). bend: preferred direction for the knee (forward (0,0,-1) for a biped, up (0,1,0) for a spider).
    yaw: also yaw the root about Y so the leg plane points at the target (spider coxa).
    Returns (R_root, R_mid, R_end_flat): local rotation matrices; R_end_flat keeps the foot at its rest attitude."""
    root, mid, end, target = (np.asarray(v, float) for v in (root, mid, end, target))
    Ry = np.eye(3)
    d1, d2 = mid - root, end - mid
    T = target - root
    if yaw:
        h0 = np.array([end[0] - root[0], 0.0, end[2] - root[2]])
        h1 = np.array([T[0], 0.0, T[2]])
        psi = math.atan2(h0[2], h0[0]) - math.atan2(h1[2], h1[0])
        Ry = axis_rot((0, 1, 0), psi)
        T = Ry.T @ T
    # plane basis: h = horizontal direction of the rest leg (or forward), v = up
    hv = np.array([end[0] - root[0] + d1[0] * 0, 0.0, end[2] - root[2]])
    if np.linalg.norm(hv) < 1e-6 or not yaw:
        hv = np.array([0.0, 0.0, -1.0])
    h = hv / np.linalg.norm(hv)
    v = np.array([0.0, 1.0, 0.0])
    t = np.cross(h, v)

    def p2(w):
        return np.array([w @ h, w @ v])

    a1, a2, tt = p2(d1), p2(d2), p2(T)
    L1, L2 = np.linalg.norm(a1), np.linalg.norm(a2)
    D = float(np.clip(np.linalg.norm(tt), abs(L1 - L2) + 1e-4, L1 + L2 - 1e-4))
    phiT = math.atan2(tt[1], tt[0])
    alpha = math.acos(max(-1.0, min(1.0, (L1 * L1 + D * D - L2 * L2) / (2 * L1 * D))))
    pb = p2(np.asarray(bend, float))
    best = None
    for sgn in (1, -1):
        ph1 = phiT + sgn * alpha
        M = L1 * np.array([math.cos(ph1), math.sin(ph1)])
        score = M @ pb
        if best is None or score > best[0]:
            best = (score, ph1, M)
    _, ph1, M = best
    tgt = tt / max(np.linalg.norm(tt), 1e-9) * D
    ph2 = math.atan2(*(tgt - M)[::-1])
    th1 = ph1 - math.atan2(a1[1], a1[0])
    th2 = ph2 - math.atan2(a2[1], a2[0]) - th1
    R1 = Ry @ axis_rot(t, th1)
    R2 = axis_rot(t, th2)
    R3 = axis_rot(t, -(th1 + th2))
    return R1, R2, R3


def foot_path(w, stride, lift, duty=0.6):
    """Foot offset (dz, dy) over a gait phase w in [0, 1): planted and sliding back during stance (front -> back,
    the body moves forward over it), then lifted and swung forward."""
    if w < duty:
        s = w / duty
        return -stride / 2 + stride * s, 0.0
    s = (w - duty) / (1 - duty)
    e = 0.5 - 0.5 * math.cos(math.pi * s)
    return stride / 2 - stride * e, lift * math.sin(math.pi * s) ** 0.8


def pose_entry(Rm, pos=(0.0, 0.0, 0.0)):
    a, b, c = euler_xyz(Rm)
    return (pos[0], pos[1], pos[2], a, b, c)


# ================================================================================================ rescale
def rescale(H, k):
    """Uniformly rescale a finished hero authored at the old arbitrary size (bones, direct / SDF pieces, prims,
    sockets, clip translations, rig sizes, saddle) by k, about the ground origin."""
    import sdf as S
    H.bones = [(n, p, tuple(float(v) * k for v in pos)) for n, p, pos in H.bones]
    for p in H.parts:
        if p["kind"] == "piece":
            m = p["sdf"]
            if isinstance(m, K.DMesh):
                p["sdf"] = K.dm(D.moved(m, scale=(k, k, k)))
            else:
                f = m
                p["sdf"] = S.SDF(lambda q, f=f: f(q / k) * k)
        else:
            p["pos"] = tuple(v * k for v in p["pos"])
            p["size"] = tuple(v * k for v in p["size"])
    H.sockets = {n: (tuple(v * k for v in pos), b) for n, (pos, b) in H.sockets.items()}
    for c in H.clips.values():
        for b, vals in c["tracks"].items():
            c["tracks"][b] = [(v[0] * k, v[1] * k, v[2] * k, v[3], v[4], v[5]) for v in vals]
    if "height" in H.rig:
        H.rig["height"] = H.rig["height"] * k
    if "wheels" in H.rig:
        H.rig["wheels"] = [{"bone": w["bone"], "r": round(w["r"] * k, 3)} for w in H.rig["wheels"]]
    sd = (H.mount or {}).get("saddle")
    if sd:
        sd["pos"] = tuple(v * k for v in sd["pos"])
        sd["size"] = tuple(v * k for v in sd["size"])
    return H
