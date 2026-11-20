"""Shared helpers for rideable creature heroes (mount overhaul, 2026-11): real-scale sockets, the `mount` table, clip
utilities (rename / overlay / re-time), forward kinematics for measuring the stride a Move clip covers, and Euler
solving for folded wing poses.

Conventions match kit.py / preview.py: a bone's pose is (px, py, pz, rx, ry, rz) in its parent's frame, rotations
compose as Rx(rx) @ Ry(ry) @ Rz(rz) (Roblox CFrame.Angles), the model faces -Z, feet on y = 0.

Rider reference (blocky R15, scale 1): 5.2 studs standing, hips 2.0 above the feet, 2 studs across the shoulders;
seated, the head top is ~3.4 above the hip point, the thighs reach ~1.3 forward and the shins ~1.2 down.

NOTE: build.py hashes only the h_*.py module + kit.py: after editing this file rebuild the users with --force.
"""
import math

import numpy as np

TAU = 2 * math.pi

# measured rest-pose Z length (studs) of each built mount (tools: measure after a build, see mount_lengths.json)
import json as _json, os as _os
try:
    LENGTHS = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "mount_lengths.json")))
except FileNotFoundError:
    LENGTHS = {}

# -------------------------------------------------------------------------------------------------- rotations


def euler(rx, ry, rz):
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    X = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return X @ Y @ Z


def to_euler(R):
    """Inverse of euler(): R = Rx(a) Ry(b) Rz(c)."""
    b = math.asin(max(-1.0, min(1.0, R[0, 2])))
    a = math.atan2(-R[1, 2], R[2, 2])
    c = math.atan2(-R[0, 1], R[0, 0])
    return a, b, c


def _nrm(v):
    v = np.asarray(v, float)
    return v / max(np.linalg.norm(v), 1e-9)


def frame_rot(a, b, a2, b2):
    """Rotation taking the orthonormalised frame (a, b) onto (a2, b2) (a -> a2 exactly, b -> b2 as near as it can)."""
    def fr(x, y):
        x = _nrm(x)
        y = _nrm(np.asarray(y, float) - (np.asarray(y, float) @ x) * x)
        return np.stack([x, y, np.cross(x, y)], axis=1)
    return fr(a2, b2) @ fr(a, b).T


# -------------------------------------------------------------------------------------------------- clips


def _add(pose, bone, v):
    if bone is None:
        return
    o = list(pose.get(bone, (0.0,) * 6))
    for i, x in enumerate(v):
        o[i] += x
    pose[bone] = tuple(o)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def win(s, a, b):
    return min(max((s - a) / (b - a), 0.0), 1.0)


def bump(x):
    return math.sin(math.pi * x) if 0 < x < 1 else 0.0


def rename(H, old, new):
    if old in H.clips:
        H.clips[new] = H.clips.pop(old)


def clip_times(c):
    n, L = c["keys"], c["len"]
    return [L * i / n for i in range(n)] if c["loop"] else [L * i / (n - 1) for i in range(n)]


def overlay(H, name, fn):
    """Add fn(t, u) -> {bone: (px..rz)} onto every key of clip `name` (u = t / len)."""
    c = H.clips.get(name)
    if not c:
        return
    n = c["keys"]
    for i, t in enumerate(clip_times(c)):
        for b, v in fn(t, t / c["len"]).items():
            assert b in H.bidx, f"{H.id}: overlay bone {b} unknown"
            tr = c["tracks"].setdefault(b, [(0.0,) * 6 for _ in range(n)])
            v = tuple(float(x) for x in v) + (0.0,) * (6 - len(v))
            tr[i] = tuple(a + b_ for a, b_ in zip(tr[i], v))


def scale_track(H, name, bone, k=(1, 1, 1, 1, 1, 1), off=(0, 0, 0, 0, 0, 0)):
    c = H.clips.get(name)
    if not c or bone not in c["tracks"]:
        return
    c["tracks"][bone] = [tuple(x * kk + oo for x, kk, oo in zip(v, k, off)) for v in c["tracks"][bone]]


def sample(H, name, t):
    """Linear sample of a clip (enough for measuring)."""
    c = H.clips[name]
    n, L = c["keys"], c["len"]
    if c["loop"]:
        u = (t % L) / L * n
        i0 = int(math.floor(u)) % n
        i1 = (i0 + 1) % n
    else:
        u = min(max(t / L, 0), 1) * (n - 1)
        i0 = min(int(u), n - 2)
        i1 = i0 + 1
    f = u - math.floor(u) if c["loop"] else u - i0
    return {b: tuple(a + (bb - a) * f for a, bb in zip(v[i0], v[i1])) for b, v in c["tracks"].items()}


def fk(H, pose):
    """bone -> (R, P) world frame."""
    W = {}
    for name, parent, pos in H.bones:
        pos = np.array(pos)
        v = pose.get(name)
        Rl = euler(*v[3:6]) if v is not None else np.eye(3)
        Tl = np.array(v[:3]) if v is not None else np.zeros(3)
        if parent is None:
            R0, P0 = np.eye(3), pos
        else:
            Rp, Pp = W[parent]
            R0, P0 = Rp, Pp + Rp @ (pos - np.array(H.bones[H.bidx[parent]][2]))
        W[name] = (R0 @ Rl, P0 + R0 @ Tl)
    return W


def world_pt(H, W, bone, p):
    R, P = W[bone]
    return P + R @ (np.asarray(p, float) - np.array(H.bones[H.bidx[bone]][2]))


def measure_stride(H, name, feet, n=240):
    """Studs the ground moves under the animal per cycle of clip `name`: the planted feet's backward speed during
    contact x the cycle length. feet: [(bone, model-space point on the sole)]."""
    c = H.clips[name]
    L = c["len"]
    speeds = []
    for bone, p in feet:
        ys, zs = [], []
        for i in range(n):
            W = fk(H, sample(H, name, L * i / n))
            q = world_pt(H, W, bone, p)
            ys.append(q[1])
            zs.append(q[2])
        ys, zs = np.array(ys), np.array(zs)
        lo = ys.min()
        band = lo + 0.06 * max(1e-3, ys.max() - lo) + 0.02
        dz = (np.roll(zs, -1) - zs) / (L / n)
        st = (ys < band) & (np.roll(ys, -1) < band)
        if st.sum() >= 3:
            speeds.append(float(np.median(dz[st])))
    if not speeds:
        return 0.0
    return round(max(0.0, float(np.mean(speeds))) * L, 2)


# -------------------------------------------------------------------------------------------------- mount table


def set_mount(H, length, seat, enter, stride=None, walk=None, extra=None, seat_bone="Body"):
    """Seat (rider hip point) + enter sockets and the mount table. Keeps any existing saddle / seat keys."""
    H.socket("seat", tuple(float(v) for v in seat), seat_bone)
    H.socket("enter", (float(enter[0]), 0.0, float(enter[2])))
    m = dict(H.mount or {})
    m["length"] = round(float(LENGTHS.get(H.id, length)), 2)
    if stride is not None:
        m["stride"] = round(float(stride), 2)
    if walk is not None:
        m["walkStride"] = round(float(walk), 2)
    if extra:
        m.update(extra)
    H.mount = m


def ray_down(sd, x, z, ytop, ybot, n=600):
    """First y (from above) where sd < 0 along the vertical line (x, z)."""
    ys = np.linspace(ytop, ybot, n)
    P = np.column_stack([np.full(n, x), ys, np.full(n, z)])
    d = sd(P)
    k = np.argmax(d < 0)
    if d[k] >= 0:
        return None
    return float(ys[k])


def ray_side(sd, y, z, xmax, n=600):
    """Largest x where sd < 0 on the horizontal line (y, z) (half width of the shape there)."""
    xs = np.linspace(xmax, 0, n)
    P = np.column_stack([xs, np.full(n, y), np.full(n, z)])
    d = sd(P)
    k = np.argmax(d < 0)
    if d[k] >= 0:
        return 0.0
    return float(xs[k])


# -------------------------------------------------------------------------------------------------- generic saddle
def saddle(H, torso, zs, bone="Body", pad_col=(0.55, 0.13, 0.14), leather="leather", metal="metal", fenders=True, stirrups=True,
           bags=False, girth=True, pad_len=(1.5, 1.25), sad_len=(1.25, 1.0), pad_drop=1.45, horn=True, pri=1.4, ytop=None,
           width=None, tris=1.0, name=""):
    """Fitted riding tack on any creature torso SDF, sized for the R15 rider (studs): saddle pad with stitched piping,
    a dished leather saddle with pommel (+ horn) and a tall cantle, fenders hanging under the rider's thighs, a girth,
    stirrup leathers + irons on Stirrup# bones (children of `bone`) and optional bedroll + saddlebags.
    Returns (seat_y, half_width_at_seat)."""
    from sdf import SDF, ellipsoid, round_box, half_space, round_cone, cylinder, sphere, torus, capsule, box
    from kit import combine
    hi_y = ytop if ytop is not None else 40.0
    by = ray_down(torso, 0.0, zs, hi_y, -5.0, n=1600)
    # widest line of the body below the back at the seat
    ys = np.linspace(by - 0.2, by - 6.0, 60)
    ws = [ray_side(torso, y, zs, 12.0, n=400) for y in ys]
    k = int(np.argmax(ws))
    yw, half_w = float(ys[k]), float(ws[k])
    zp, zc_ = zs - 1.05, zs + 0.78

    def rr2(z0, z1, y0, y1, r):
        return round_box(50.0, (y1 - y0) / 2, (z1 - z0) / 2, r, (0, (y0 + y1) / 2, (z0 + z1) / 2))

    def stitch(region, inset, width_, depth=0.45, dash=None):
        def f(P):
            d = region(P)
            line = np.clip(1 - np.abs(d + inset) / width_, 0, 1)
            if dash:
                line = line * (np.sin((P[:, 2] + P[:, 1]) * dash) > -0.2)
            edge = np.clip(1 - np.abs(d) / (width_ * 1.6), 0, 1) * 0.5
            return 1 - depth * np.maximum(line, edge)
        return f

    xcut = (lambda sd: sd & box(width, 50, 50)) if width else (lambda sd: sd)
    pad_reg = rr2(zs - pad_len[0], zs + pad_len[1], by - pad_drop - 0.05, by + 3.0, 0.35)
    pad = xcut(torso.round(0.075).shell(0.045) & pad_reg & half_space(1, -1, by - pad_drop))
    H.piece(name + "Blanket", bone, pad, col=pad_col, mat="cloth", tris=int(1300 * tris), res=136, role="detail", pri=pri,
            pattern=stitch(lambda Q: np.maximum(pad_reg(Q), by - pad_drop - Q[:, 1]), 0.12, 0.03, 0.4, dash=60))
    sreg = rr2(zs - sad_len[0], zs + sad_len[1], by - 0.95, by + 3.0, 0.45)
    sad = (torso.round(0.3) - torso.round(0.1)) & sreg
    sad = sad.ss(ellipsoid(0.62, 0.16, 0.75, (0, by + 0.43, zs + 0.05)), 0.12)
    sad = sad.su(ellipsoid(0.36, 0.3, 0.26, (0, by + 0.3, zp + 0.05)) & half_space(1, -1, by), 0.14)
    if horn:
        hn = round_cone((0, by + 0.42, zp - 0.02), (0, by + 0.72, zp - 0.12), 0.085, 0.07)
        sad = sad.su(hn.su(cylinder(0.15, 0.04, rr=0.03).at(0, by + 0.74, zp - 0.13), 0.03), 0.04)
    cant = None
    for i in range(9):
        x = -0.62 + 1.24 * i / 8
        seg = sphere(0.1, (x, by + 0.62 - 0.55 * x * x, zc_ + 0.1 * abs(x)))
        cant = seg if cant is None else cant.su(seg, 0.12)
    sad = sad.su(cant.su(ellipsoid(0.62, 0.36, 0.3, (0, by + 0.3, zc_ + 0.02)) & half_space(1, -1, by), 0.15), 0.1)

    def hang(p):
        q = p.copy()
        q[:, 1] = np.maximum(p[:, 1], yw)
        return q
    ext = torso.warp(hang)
    fen_reg = rr2(zs - 0.85, zs + 0.3, by - 1.55, by + 0.2, 0.28)
    pats = [stitch(sreg, 0.1, 0.025, 0.35, dash=70), lambda Q: 1 - 0.18 * np.clip((by + 0.25 - Q[:, 1]) / 0.6, 0, 1)]
    if fenders:
        fen = ((ext.round(0.2) - ext.round(0.1)) & fen_reg & half_space(0, -1, 0.35 * half_w)).mirror_x()
        sad = sad.su(fen, 0.06)
        pats.append(stitch(fen_reg, 0.08, 0.022, 0.35, dash=70))
    sad = xcut(sad)
    H.piece(name + "Saddle", bone, sad, col=leather, tris=int(2600 * tris), res=144, role="detail", pri=pri + 0.1, pattern=combine(*pats))
    if girth:
        zg = zs - 0.5
        g = torso.round(0.03).shell(0.035) & box(40.0, (by - 1.3 + 40.0) / 2, 0.14, (0, (by - 1.3 - 40.0) / 2, zg))
        H.piece(name + "Girth", bone, g, col=leather, tris=500, res=120, role="detail", pri=pri + 0.3, ao=False)
    if stirrups:
        sz_ = zs - 0.55
        fx = ray_side(ext.round(0.2), by - 0.9, sz_, 12.0) + 0.05
        sy0 = by + 0.05
        H.mbone(name + "Stirrup#", bone, (fx, sy0, sz_))
        yi = by - 1.62
        strap = round_box(0.03, (sy0 - yi - 0.2) / 2, 0.075, 0.015, (fx, (sy0 + yi + 0.2) / 2, sz_))
        iron = torus(0.2, 0.04, axis=0).at(fx + 0.02, yi + 0.2, sz_) & half_space(1, 1, yi + 0.2)
        iron = iron | round_box(0.22, 0.035, 0.18, 0.03, (fx + 0.02, yi + 0.02, sz_))
        iron = iron | capsule((fx + 0.02, yi + 0.02, sz_ - 0.2), (fx + 0.02, yi + 0.2, sz_ - 0.2), 0.04) | capsule((fx + 0.02, yi + 0.02, sz_ + 0.2), (fx + 0.02, yi + 0.2, sz_ + 0.2), 0.04)
        H.mpiece(name + "Stirrup#", name + "Stirrup#", strap, col=leather, tris=200, res=100, role="detail", pri=pri + 0.4, ao=False, smooth=1)
        H.mpiece(name + "Iron#", name + "Stirrup#", iron, col=metal, mat="metal", tris=420, res=110, role="detail", pri=pri + 0.5, ao=False)
    if bags:
        zb = zc_ + 0.55
        byb = ray_down(torso, 0.0, zb, hi_y, -5.0, n=1600)
        roll = capsule((-0.62, byb + 0.22, zb), (0.62, byb + 0.22, zb), 0.22)
        roll = roll.ss(torus(0.23, 0.035, axis=0).at(0.35, byb + 0.22, zb).mirror_x(), 0.01)
        roll = roll.su(torus(0.215, 0.035, axis=0).at(0.35, byb + 0.22, zb).mirror_x(), 0.005)
        H.piece(name + "Bedroll", bone, roll, col=[0.62, 0.55, 0.42], mat="cloth", tris=600, res=110, role="detail", pri=pri + 0.5,
                pattern=lambda Q: 1 - 0.55 * (np.abs(np.abs(Q[:, 0]) - 0.35) < 0.05))
    seat_y = ray_down(sad, 0.0, zs, by + 1.5, by - 0.5) or by + 0.28
    return seat_y, half_w


# -------------------------------------------------------------------------------------------------- folding wings
def fold_euler(H, arm_bone, hand_bone, side, back=(0.0, 0.12, 1.0), down=(0.25, -1.0, 0.0), trail=(0, 0, 1)):
    """Euler (rx, ry, rz) for a wing arm bone so the spread wing (arm along +-X, membrane trailing +Z) lies back along
    the flank with the membrane hanging down. side: +1 right / -1 left (mirrored)."""
    ad = (H.bpos(hand_bone) - H.bpos(arm_bone)) * np.array([side, 1, 1])
    a, b, c = to_euler(frame_rot(ad, trail, back, down))
    return (a, b * side, c * side)


# -------------------------------------------------------------------------------------------------- IK gaits
def _ang(u, v):
    """Signed rotation (rx convention, CCW in the (y, z) plane) taking 2-vector u onto v's direction."""
    return math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1])


def _rot2(v, a):
    c, s_ = math.cos(a), math.sin(a)
    return np.array([v[0] * c - v[1] * s_, v[0] * s_ + v[1] * c])


def ik_leg(H, W, bones, sole, target, foot_pitch=0.0):
    """Sagittal two-bone IK + foot: returns rx for (upper, lower, foot) so the sole point (rest model space, on the
    foot bone) lands on `target` (model space) with the foot at `foot_pitch` relative to the upper bone's parent.
    W = fk frames of the pose so far (body / spine already posed). The rest knee bend direction is kept."""
    b0, b1, b2 = bones
    par = H.bones[H.bidx[b0]][1]
    Rp, Pp = W[par]
    prest = np.array(H.bones[H.bidx[par]][2])
    T = prest + Rp.T @ (np.asarray(target, float) - Pp)
    yz = lambda p: np.array([p[1], p[2]], float)
    H0, K, A, S = yz(H.bpos(b0)), yz(H.bpos(b1)), yz(H.bpos(b2)), yz(np.asarray(sole, float))
    foot_pitch = foot_pitch - math.atan2(Rp[2, 1], Rp[1, 1])        # world pitch -> the parent's frame
    At = yz(T) + _rot2(A - S, foot_pitch)
    l1, l2 = np.linalg.norm(K - H0), np.linalg.norm(A - K)
    d_ = At - H0
    d = float(np.clip(np.linalg.norm(d_), abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3))
    ca = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    al = math.acos(max(-1.0, min(1.0, ca)))
    rest_c = (A - H0)[0] * (K - H0)[1] - (A - H0)[1] * (K - H0)[0]
    sg = 1.0 if rest_c >= 0 else -1.0
    dirn = d_ / max(np.linalg.norm(d_), 1e-9)
    K2 = H0 + l1 * _rot2(dirn, sg * al)
    A2 = H0 + dirn * d
    r0 = _ang(K - H0, K2 - H0)
    r1 = _ang(A - K, A2 - K2) - r0
    r2 = foot_pitch - r0 - r1
    return r0, r1, r2


GAITS = {
    # name: duty, {(front, side): touchdown phase}
    "walk": (0.68, {(False, -1): 0.0, (True, -1): 0.25, (False, 1): 0.5, (True, 1): 0.75}),
    "amble": (0.56, {(False, -1): 0.0, (True, -1): 0.18, (False, 1): 0.5, (True, 1): 0.68}),
    "trot": (0.55, {(False, -1): 0.5, (True, -1): 0.0, (False, 1): 0.0, (True, 1): 0.5}),
    "gallop": (0.36, {(False, -1): 0.0, (False, 1): 0.12, (True, -1): 0.42, (True, 1): 0.54}),
    "bound": (0.34, {(False, -1): 0.0, (False, 1): 0.06, (True, -1): 0.46, (True, 1): 0.52}),
    "biped": (0.62, {(False, -1): 0.0, (False, 1): 0.5}),
    "biprun": (0.4, {(False, -1): 0.0, (False, 1): 0.5}),
}


def gait_clip(H, name, legs, period, gait, stride, lift, body_fn=None, extra_fn=None, keys=24, curl=0.5, toe_off=0.25):
    """Author a locomotion clip with grounded feet. legs: dicts {bones: (upper, lower, foot), sole: rest model point
    under the foot, front: bool, side: +1/-1}. Feet in stance slide back exactly `stride * duty` (so the model covers
    `stride` studs per cycle), swing feet arc up `lift` studs and curl. body_fn(u, pose) poses Body / spine / neck
    first; extra_fn(u, pose) adds anything after the legs."""
    duty, offs = GAITS[gait]

    def fn(t):
        u = t / period
        pose = {}
        if body_fn:
            body_fn(u, pose)
        W = fk(H, pose)
        for lg in legs:
            ph = (u - offs[(lg["front"], lg["side"])]) % 1.0
            sole = np.asarray(lg["sole"], float)
            if ph < duty:
                s_ = ph / duty
                dz = stride * duty * (s_ - 0.5)
                y = 0.0
                fp = -toe_off * max(0.0, (s_ - 0.8) / 0.2) ** 2 * (1 if lg["front"] else 1)
            else:
                s_ = (ph - duty) / (1 - duty)
                dz = stride * duty * (0.5 - ease(s_))
                y = lift * math.sin(math.pi * s_) ** 0.8 * lg.get("lift", 1.0)
                fp = -curl * math.sin(math.pi * min(1.0, s_ * 1.15))
            tgt = sole + np.array([0.0, y, dz])
            r = ik_leg(H, W, lg["bones"], sole, tgt, fp)
            for b, a in zip(lg["bones"], r):
                _add(pose, b, (0, 0, 0, a, 0, 0))
        if extra_fn:
            extra_fn(u, pose)
        return pose

    H.clip(name, period, fn, keys=keys)


def leg_specs(H, legs, soles):
    """legs: (upper, lower, foot, front, side) tuples; soles: {foot bone: rest model point under the foot}."""
    return [{"bones": (u, l, f), "sole": np.asarray(soles[f], float), "front": fr, "side": sd} for u, l, f, fr, sd in legs]


def body_motion(style, h, neck=(), head=None, jaw=None, tail=(), ears=(), spine=None, k=1.0):
    """Body / spine / neck / tail motion for a gait style: walk | amble (lumbering bear) | gallop (rotary) | bound
    (wolf: big spine flex) | biped (dinosaur walk) | biprun. Small seat motion: the rider sits on Body."""
    neck = [neck] if isinstance(neck, str) else list(neck)

    def fn(u, pose):
        w = TAU * u
        if style == "walk":
            _add(pose, "Body", (0, (-0.018 * abs(math.sin(w * 2)) + 0.009) * h, 0, 0.012 * math.sin(w * 2 + 0.5), 0.03 * math.sin(w), 0.025 * math.sin(w + 0.4)))
            for i, b in enumerate(neck):
                _add(pose, b, (0, 0, 0, -0.035 * math.sin(w * 2 + 0.8 + i), -0.03 * math.sin(w + 0.5 * i), 0))
            _add(pose, head, (0, 0, 0, 0.04 * math.sin(w * 2 + 1.3), 0.02 * math.sin(w), 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0.03 * math.sin(w * 2 - i), 0.12 * math.sin(w - 0.9 * i - 1.0), 0))
            if spine:
                _add(pose, spine, (0, 0, 0, 0, -0.04 * math.sin(w), -0.03 * math.sin(w)))
        elif style == "amble":
            roll = math.sin(w + 0.3)
            _add(pose, "Body", (0, (-0.03 * abs(math.sin(w * 2)) + 0.015) * h, 0, 0.02 * math.sin(w * 2 + 0.4), 0.05 * math.sin(w), 0.065 * roll))
            if spine:
                _add(pose, spine, (0, 0, 0, 0.03 * math.sin(w * 2), -0.06 * math.sin(w), -0.05 * roll))
            for i, b in enumerate(neck):
                _add(pose, b, (0, 0, 0, -0.06 * math.sin(w * 2 + 1.0) - 0.04, -0.07 * math.sin(w + 0.4 * i), 0))
            _add(pose, head, (0, 0, 0, 0.05 * math.sin(w * 2 + 1.5), 0.06 * math.sin(w + 0.6), -0.04 * roll))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0.05 * math.sin(w * 2 - i), 0.08 * math.sin(w - i), 0))
        elif style in ("gallop", "bound"):
            big = 1.6 if style == "bound" else 1.0
            rock = math.cos(w - 0.9)
            _add(pose, "Body", (0, (0.04 * big * max(0.0, math.sin(w - 1.9)) - 0.015) * h, 0, 0.05 * rock * k, 0.012 * math.sin(w), 0.015 * math.sin(w)))
            if spine:
                _add(pose, spine, (0, 0, 0, -0.16 * big * math.cos(w - 0.2) * k, 0, 0))
            for i, b in enumerate(neck):
                _add(pose, b, (0, 0, 0, -0.07 * rock * (0.6 + 0.4 * i) - 0.05, 0, 0))
            _add(pose, head, (0, 0, 0, 0.06 * rock + 0.04, 0, 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0.1 * math.cos(w - 0.6 - 0.5 * i) + 0.05, 0.05 * math.sin(w - i), 0))
            _add(pose, jaw, (0, 0, 0, -0.06 - 0.05 * math.sin(w), 0, 0))
            for b in ears:
                _add(pose, b, (0, 0, 0, -0.25, 0, 0))
        elif style in ("biped", "biprun"):
            run = style == "biprun"
            a = 1.6 if run else 1.0
            _add(pose, "Body", (0, (-0.02 * a * abs(math.sin(w)) + 0.01 * a) * h, 0, (-0.08 if run else -0.02) + 0.02 * math.sin(w * 2),
                                0.05 * math.sin(w), 0.035 * a * math.sin(w)))
            for i, b in enumerate(neck):
                _add(pose, b, (0, 0, 0, (0.06 if run else 0.0) - 0.04 * math.sin(w * 2 + 0.7), -0.05 * math.sin(w + 0.4 * i), 0))
            _add(pose, head, (0, 0, 0, (0.06 if run else 0.0) + 0.04 * math.sin(w * 2 + 1.2), -0.03 * math.sin(w), 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, (0.06 if run else 0.0) + 0.03 * math.sin(w * 2 - i), -0.09 * math.sin(w - 0.7 * i), 0))
            _add(pose, jaw, (0, 0, 0, (-0.08 - 0.04 * math.sin(w * 2)) if run else 0.0, 0, 0))
    return fn


def ground_clips(H, legs, h, walk, run, neck=(), head=None, jaw=None, tail=(), ears=(), spine=None, curl=0.5):
    """Replace Move with an IK run and add Walk. walk / run = (period, gait, style, stride, lift)."""
    for name, (per, gait, style, stride, lift) in (("Walk", walk), ("Move", run)):
        H.clips.pop(name, None)
        gait_clip(H, name, legs, per, gait, stride, lift, body_motion(style, h, neck, head, jaw, tail, ears, spine), keys=24,
                  curl=curl if name == "Move" else curl * 0.6)
    return walk[3], run[3]


def rig_mount(H, torso, zs, legs, soles, h, length, walk, run, neck=(), head=None, jaw=None, tail=(), ears=(), spine=None,
              pad_col="secondary", bags=False, ytop=None, extra=None, curl=0.5, saddle_kw=None):
    """One call for a four-legged (or two-legged) creature mount: fitted saddle on `torso` at seat z `zs`, seat +
    enter sockets, IK Walk / Move clips (see ground_clips) and the mount table."""
    seat_y, hw = saddle(H, torso, zs, pad_col=pad_col, bags=bags, ytop=ytop, **(saddle_kw or {}))
    H.socket("seat", (0, seat_y, zs), "Body")
    H.mount = {"seat": "Torso", "saddle": {"pos": (0, seat_y, zs), "size": (1.5, 0.3, 2.2)}}
    ws, rs = ground_clips(H, leg_specs(H, legs, soles), h, walk, run, neck, head, jaw, tail, ears, spine, curl)
    set_mount(H, length, (0, seat_y, zs), (-(hw + 1.8), 0, zs), stride=rs, walk=ws, extra=extra)
    return seat_y


# -------------------------------------------------------------------------------------------------- uniform rescale
def scale_sdf(sd, k):
    from sdf import SDF
    return SDF(lambda p: sd(p / k) * k)


def scale_hero(H, k):
    """Uniformly rescale a finished hero by k (sculpts, prims, bones, sockets, clip translations, rig height): for
    families whose sculpt radii do not follow their `s` parameter (felines, canines)."""
    H.bones = [(n, p, tuple(float(v) * k for v in pos)) for n, p, pos in H.bones]
    for p in H.parts:
        if p["kind"] == "piece":
            p["sdf"] = scale_sdf(p["sdf"], k)
            if p.get("pattern") is not None:
                p["pattern"] = (lambda f: (lambda P: f(P / k)))(p["pattern"])
        else:
            p["pos"] = tuple(v * k for v in p["pos"])
            p["size"] = tuple(v * k for v in p["size"])
    H.sockets = {n: (tuple(v * k for v in pos), b) for n, (pos, b) in H.sockets.items()}
    for c in H.clips.values():
        for b, vals in c["tracks"].items():
            c["tracks"][b] = [tuple(x * k if i < 3 else x for i, x in enumerate(v)) for v in vals]
    if "height" in H.rig:
        H.rig["height"] = H.rig["height"] * k
    if H.mount and "saddle" in H.mount:
        sd = H.mount["saddle"]
        H.mount["saddle"] = {"pos": tuple(v * k for v in sd["pos"]), "size": tuple(v * k for v in sd["size"])}
    H.bounds_scale = k
