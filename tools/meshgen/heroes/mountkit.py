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
    m["length"] = round(float(length), 2)
    if stride is not None:
        m["stride"] = stride
    if walk is not None:
        m["walkStride"] = walk
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
