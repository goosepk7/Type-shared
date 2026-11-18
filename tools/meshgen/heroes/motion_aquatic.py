"""Aquatic family helpers: sculpt helpers (lofted fish bodies, fin plates, overlays) and authored swim / scuttle /
pulse / tentacle cycles for the aquatic heroes (h_fish.py, h_aquatic.py, h_shellfish.py).

NOTE: build.py hashes only the h_*.py file (+ kit.py) for its mesh cache. If a SHAPE helper here changes, rebuild the
affected heroes with --force.

Pose values are (px, py, pz, rx, ry, rz) at each bone pivot in its parent's frame. Model faces -Z. +ry turns the
nose toward -X... for a bone whose children trail behind (+Z), +ry swings them toward +X? (x' = x cos + z sin):
a point behind the pivot (z > 0) moves to +X. +rx on a backward chain moves its tail DOWN, -rx on a jaw opens it.
"""
import math

import numpy as np
from scipy.interpolate import PchipInterpolator

import sdf as S

TAU = 2 * math.pi


# ================================================================================================ sculpt helpers
class Profile:
    """Body outline along z: control rows (t, top, bottom, halfwidth) in units of L, t = 0 at the nose, 1 at the tail
    base. Lengths are scaled by L and placed so the nose is at z0 and the axis at y0."""

    def __init__(self, rows, L, z0, y0):
        r = np.array(rows, float)
        self.L, self.z0, self.y0 = L, z0, y0
        self.top = PchipInterpolator(r[:, 0], r[:, 1], extrapolate=True)
        self.bot = PchipInterpolator(r[:, 0], r[:, 2], extrapolate=True)
        self.wid = PchipInterpolator(r[:, 0], r[:, 3], extrapolate=True)
        self.t0, self.t1 = float(r[0, 0]), float(r[-1, 0])

    def z(self, t):
        return self.z0 + t * self.L

    def t(self, z):
        return (z - self.z0) / self.L

    def at(self, t):
        """(top y, bottom y, half width, centre y, half height) in studs at t."""
        t = float(np.clip(t, self.t0, self.t1))
        tp = self.y0 + float(self.top(t)) * self.L
        bt = self.y0 + float(self.bot(t)) * self.L
        w = float(self.wid(t)) * self.L
        return tp, bt, w, (tp + bt) / 2, (tp - bt) / 2

    def surface(self, t, ang):
        """A point on the body surface at t, around the section (ang 0 = +X side, 90 = top)."""
        tp, bt, w, c, a = self.at(t)
        return (w * math.cos(math.radians(ang)), c + a * math.sin(math.radians(ang)), self.z(t))

    def sdf(self, cap=True, squareness=0.0):
        """Approximate SDF of the lofted elliptic body. squareness > 0 flattens the sides (boxy fish / whale heads)."""
        L, z0, y0 = self.L, self.z0, self.y0
        top, bot, wid = self.top, self.bot, self.wid
        t0, t1 = self.t0, self.t1

        def f(P):
            t = np.clip((P[:, 2] - z0) / L, t0, t1)
            tp = y0 + top(t) * L
            bt = y0 + bot(t) * L
            a = np.maximum((tp - bt) / 2, 1e-3)
            b = np.maximum(wid(t) * L, 1e-3)
            c = (tp + bt) / 2
            # slopes (studs per stud) for the distance correction
            e = 0.004
            ta, tb = np.clip(t - e, t0, t1), np.clip(t + e, t0, t1)
            dt = np.maximum(tb - ta, 1e-6)
            da = ((top(tb) - bot(tb)) - (top(ta) - bot(ta))) / 2 / dt
            db = (wid(tb) - wid(ta)) / dt
            dc = ((top(tb) + bot(tb)) - (top(ta) + bot(ta))) / 2 / dt
            x = P[:, 0] / b
            y = (P[:, 1] - c) / a
            if squareness > 0:
                n = 2 + 6 * squareness
                k0 = (np.abs(x) ** n + np.abs(y) ** n) ** (1 / n)
                d2 = (k0 - 1) * np.minimum(a, b)
            else:
                q = np.column_stack([P[:, 0], P[:, 1] - c])
                r = np.column_stack([b, a])
                k0 = np.linalg.norm(q / r, axis=1)
                k1 = np.linalg.norm(q / (r * r), axis=1)
                d2 = np.where(k1 > 1e-9, k0 * (k0 - 1.0) / np.maximum(k1, 1e-9), -np.minimum(a, b))
            ang = np.arctan2(y, x)
            ca, sa = np.cos(ang), np.sin(ang)
            nx, ny = ca / b, sa / a
            nn = np.sqrt(nx * nx + ny * ny)
            slope = (db * ca * nx + (dc + da * sa) * ny) / np.maximum(nn, 1e-9)
            slope = np.minimum(np.abs(slope), 6.0)
            d = d2 / np.sqrt(1 + slope * slope)
            if cap:
                d = np.maximum(d, np.maximum(z0 + t0 * L - P[:, 2], P[:, 2] - (z0 + t1 * L)))
            return d

        return S.SDF(f)


def poly2d(P2, pts):
    """Signed distance from 2D points P2 (N,2) to a polygon (list of (a, b)); negative inside."""
    V = np.asarray(pts, float)
    d = ((P2 - V[0]) ** 2).sum(1)
    s = np.ones(len(P2))
    n = len(V)
    j = n - 1
    for i in range(n):
        e = V[j] - V[i]
        w = P2 - V[i]
        h = np.clip((w @ e) / max(e @ e, 1e-12), 0, 1)
        b = w - h[:, None] * e
        d = np.minimum(d, (b * b).sum(1))
        c1 = P2[:, 1] >= V[i, 1]
        c2 = P2[:, 1] < V[j, 1]
        c3 = e[0] * w[:, 1] > e[1] * w[:, 0]
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
        j = i
    return s * np.sqrt(d)


def chaikin(pts, it=2):
    P = [tuple(p) for p in pts]
    for _ in range(it):
        Q = []
        n = len(P)
        for i in range(n):
            a, b = np.array(P[i]), np.array(P[(i + 1) % n])
            Q.append(tuple(a * 0.75 + b * 0.25))
            Q.append(tuple(a * 0.25 + b * 0.75))
        P = Q
    return P


def plate(origin, u, v, pts, thick, taper=0.45, edge=None, bend=0.0, smooth=2):
    """A thin fin plate: polygon `pts` (a along u, b along v) in the plane through origin, thickness `thick` (full),
    thinning to `taper` x at the rim over `edge` studs. bend: cups the plate along its normal by bend * a^2."""
    o = np.asarray(origin, float)
    u = np.asarray(u, float)
    u = u / np.linalg.norm(u)
    v = np.asarray(v, float)
    v = v - u * (v @ u)
    v = v / np.linalg.norm(v)
    n = np.cross(u, v)
    pts = chaikin(pts, smooth if len(pts) < 12 else 1) if (smooth and len(pts) <= 24) else [tuple(p) for p in pts]
    ext = np.ptp(np.asarray(pts, float), axis=0).max()
    edge = edge or ext * 0.25

    def f(P):
        Q = P - o
        a = Q @ u
        b = Q @ v
        h = Q @ n - bend * a * a
        d2 = poly2d(np.column_stack([a, b]), pts)
        t = thick * 0.5 * (taper + (1 - taper) * np.clip(-d2 / edge, 0, 1))
        dh = np.abs(h) - t
        return np.minimum(np.maximum(d2, dh), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(dh, 0) ** 2)

    return S.SDF(f)


def ray_lines(origin, u, v, n=9, spread=(-80, 80), depth=0.22, width=0.3):
    """Pattern: fin rays radiating from origin in the (u, v) plane (darkening lines)."""
    o = np.asarray(origin, float)
    u = np.asarray(u, float) / np.linalg.norm(u)
    v = np.asarray(v, float)
    v = v - u * (v @ u)
    v = v / np.linalg.norm(v)
    a0, a1 = math.radians(spread[0]), math.radians(spread[1])

    def f(P):
        Q = P - o
        ang = np.arctan2(Q @ v, Q @ u)
        k = (ang - a0) / (a1 - a0) * (n - 1)
        fr = np.abs(k - np.round(k))
        line = np.clip(1 - fr / (width * 0.5), 0, 1)
        return 1 - depth * line

    return f


def par_lines(u, freq, depth=0.2, width=0.3, origin=(0, 0, 0)):
    """Pattern: parallel darkening lines across direction u (fin rays of long median fins)."""
    u = np.asarray(u, float) / np.linalg.norm(u)
    o = np.asarray(origin, float)

    def f(P):
        k = ((P - o) @ u) * freq
        fr = np.abs(k - np.round(k))
        return 1 - depth * np.clip(1 - fr / (width * 0.5), 0, 1)

    return f


def slab(axis, lo, hi):
    return S.SDF(lambda P: np.maximum(lo - P[:, axis], P[:, axis] - hi))


def segment(body, z0, z1, k=0.05):
    """The part of `body` between z0 and z1 (rounded cut)."""
    return body.si(slab(2, z0, z1), k)


def overlay(body, region, t=0.035, k=0.02):
    """A decal that stands proud of `body` by t inside `region` (an SDF): for belly patches, bands, eye patches."""
    return body.round(t).si(region, k)


def cone_pts(base, tip, r):
    return S.round_cone(tuple(base), tuple(tip), r, r * 0.12)


def union_all(shapes, k=0.0):
    s = shapes[0]
    for o in shapes[1:]:
        s = s.su(o, k) if k > 0 else (s | o)
    return s


def region_fn(fn):
    return S.SDF(fn)


# ================================================================================================ motion
def _add(pose, bone, v):
    if bone is None:
        return
    o = list(pose.get(bone, (0.0,) * 6))
    for i, x in enumerate(v):
        o[i] += x
    pose[bone] = tuple(o)


def _ease(x):
    return 0.5 - 0.5 * math.cos(math.pi * min(max(x, 0.0), 1.0))


def _env(s, a, b):
    """0 -> 1 -> 0 bump between s = a and s = b."""
    return math.sin(math.pi * min(max((s - a) / (b - a), 0.0), 1.0))


def swim(H, chain, head=None, jaw=None, pecs=(), flutter=(), mode="yaw", period=1.0, amp=0.32, length=6.0, attack="bite",
         wave=0.9, body_amp=0.06, extra=None, idle_period=3.2, pec_axis="rz"):
    """Fish / shark / whale swimming. chain: spine bones from the body to the tail fin (local angles accumulate, so
    the wave travels and grows toward the tail). mode "yaw" = side-to-side (fish), "pitch" = up-down (whales,
    seals). pecs: list of (right, left) pectoral bones that scull. flutter: (bone, axis, amount) small fins that
    ripple. attack: "bite" (lunge + jaw snap), "ram" (bill / head charge), "slap" (tail slam), "spin".
    extra(pose, kind, u, s) may add more motion (kind = "move"/"idle"/"attack"/"hit")."""
    n = max(len(chain), 1)
    ax = 4 if mode == "yaw" else 3  # index in the pose tuple: ry or rx

    def wave_pose(pose, u, a, ph0=0.0):
        for i, b in enumerate(chain):
            k = 0.45 + 0.55 * (i / max(n - 1, 1))
            v = [0.0] * 6
            v[ax] = a * k * math.sin(TAU * u - wave * (i + 1) + ph0) / (1.0 if mode == "yaw" else 1.0)
            _add(pose, b, tuple(v))
        v = [0.0] * 6
        v[ax] = -body_amp * (a / amp) * math.sin(TAU * u + ph0)
        _add(pose, "Body", tuple(v))
        if head:
            v = [0.0] * 6
            v[ax] = 0.5 * body_amp * (a / amp) * math.sin(TAU * u + ph0 + 0.4)
            _add(pose, head, tuple(v))

    def fins(pose, u, k=1.0):
        for j, (r, l) in enumerate(pecs):
            w = math.sin(TAU * u * 2 + j)
            if pec_axis == "rz":
                _add(pose, r, (0, 0, 0, 0.1 * k * w, 0.22 * k * w, 0.18 * k * math.sin(TAU * u * 2 + 1.2 + j)))
                _add(pose, l, (0, 0, 0, 0.1 * k * w, -0.22 * k * w, -0.18 * k * math.sin(TAU * u * 2 + 1.2 + j)))
            else:  # whale flippers: slow up-down sweep
                _add(pose, r, (0, 0, 0, 0.12 * k * w, 0, 0.2 * k * math.sin(TAU * u + j)))
                _add(pose, l, (0, 0, 0, 0.12 * k * w, 0, -0.2 * k * math.sin(TAU * u + j)))
        for j, (b, axis, a) in enumerate(flutter):
            v = [0.0] * 6
            v[{"rx": 3, "ry": 4, "rz": 5}[axis]] = a * k * math.sin(TAU * u * 3 - j * 0.9)
            _add(pose, b, tuple(v))

    def move(t):
        u = t / period
        pose = {}
        wave_pose(pose, u, amp)
        fins(pose, u, 1.0)
        _add(pose, "Body", (0, 0.015 * length * math.sin(TAU * u * (2 if mode == "yaw" else 1) + 0.5), 0, 0, 0, 0))
        if mode == "pitch":
            _add(pose, "Body", (0, 0, 0, 0.04 * math.sin(TAU * u + 0.8), 0, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.06 * (0.5 + 0.5 * math.sin(TAU * u)), 0, 0))
        if extra:
            extra(pose, "move", u, 0.0)
        return pose

    def idle(t):
        u = t / idle_period
        pose = {}
        wave_pose(pose, u, amp * 0.35)
        fins(pose, u * 1.5, 0.8)
        _add(pose, "Body", (0, 0.02 * length * math.sin(TAU * u), 0, 0.02 * math.sin(TAU * u + 1), 0, 0.02 * math.sin(TAU * u * 2)))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.12 * max(0.0, math.sin(TAU * u * 2)) ** 2, 0, 0))
        if extra:
            extra(pose, "idle", u, 0.0)
        return pose

    AL = 0.9

    def attack_fn(t):
        s = t / AL
        pose = {}
        wind = _env(s, 0.0, 0.5)
        strike = _env(s, 0.28, 0.8)
        rec = 1 - _ease((s - 0.75) / 0.25) if s > 0.75 else 1.0
        beat = math.sin(TAU * s * 2.5)
        if attack == "bite":
            _add(pose, "Body", (0, 0.02 * length * wind, 0.12 * length * wind - 0.32 * length * strike, 0.06 * wind - 0.04 * strike, 0, 0))
            for i, b in enumerate(chain):
                v = [0.0] * 6
                v[ax] = (0.25 + 0.15 * i) * beat * (wind + strike) * 0.6
                _add(pose, b, tuple(v))
            if jaw:
                op = _env(s, 0.12, 0.62)
                _add(pose, jaw, (0, 0, 0, -0.75 * op, 0, 0))
            if head:
                _add(pose, head, (0, 0, 0, 0.1 * wind - 0.1 * strike, 0, 0))
        elif attack == "ram":
            _add(pose, "Body", (0, -0.03 * length * strike, 0.15 * length * wind - 0.45 * length * strike, 0.1 * wind - 0.12 * strike, 0, 0))
            for i, b in enumerate(chain):
                v = [0.0] * 6
                v[ax] = (0.3 + 0.12 * i) * math.sin(TAU * s * 3) * strike
                _add(pose, b, tuple(v))
            if head:
                v = [0.0] * 6
                v[4] = 0.35 * math.sin(TAU * s * 2) * strike  # bill slash
                _add(pose, head, tuple(v))
            if jaw:
                _add(pose, jaw, (0, 0, 0, -0.3 * strike, 0, 0))
        elif attack == "slap":
            # pitch up, then slam the tail down (whales) / sideways (fish with mode yaw)
            _add(pose, "Body", (0, 0.06 * length * wind, -0.1 * length * strike, (0.25 * wind - 0.2 * strike) if mode == "pitch" else 0.0,
                                0.4 * wind - 0.3 * strike if mode == "yaw" else 0.0, 0))
            for i, b in enumerate(chain):
                v = [0.0] * 6
                v[ax] = (-0.45 * wind + 0.7 * strike) * (0.5 + 0.5 * i / max(n - 1, 1))
                _add(pose, b, tuple(v))
            if jaw:
                _add(pose, jaw, (0, 0, 0, -0.4 * strike, 0, 0))
        else:  # spin / puff
            _add(pose, "Body", (0, 0.05 * length * strike, -0.15 * length * strike, 0, 0, TAU * _ease(min(max((s - 0.2) / 0.6, 0), 1))))
            if jaw:
                _add(pose, jaw, (0, 0, 0, -0.5 * strike, 0, 0))
        fins(pose, s * 2, 1.5)
        if extra:
            extra(pose, "attack", s, strike)
        for k, v in list(pose.items()):
            pose[k] = tuple(x * rec for x in v)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0.03 * length * k, 0.12 * length * k, 0.15 * k if mode == "pitch" else 0.05 * k, 0, 0.2 * k * math.sin(s * 9)))
        for i, b in enumerate(chain):
            v = [0.0] * 6
            v[ax] = 0.35 * k * (1 if i % 2 == 0 else 0.6)
            _add(pose, b, tuple(v))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.35 * k, 0, 0))
        if head:
            _add(pose, head, (0, 0, 0, 0.15 * k, 0, 0))
        fins(pose, s, 1.6)
        if extra:
            extra(pose, "hit", s, k)
        return pose

    H.clip("Move", period, move, keys=20)
    H.clip("Idle", idle_period, idle, keys=24)
    H.clip("Attack", AL, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"swimAuthored": True, "length": length})


def ray_swim(H, wings, tail=(), head=None, period=1.6, amp=0.42, length=6.0, extra=None):
    """Rays: wings = list of (right bones chain, left bones chain); a flap wave runs from the root to the tip."""

    def flap(pose, u, a):
        for rch, lch in wings:
            for i, (r, l) in enumerate(zip(rch, lch)):
                w = a * (0.6 + 0.4 * i) * math.sin(TAU * u - 0.9 * i)
                _add(pose, r, (0, 0, 0, 0.12 * a * math.sin(TAU * u - 0.9 * i - 1.2), 0, w))
                _add(pose, l, (0, 0, 0, 0.12 * a * math.sin(TAU * u - 0.9 * i - 1.2), 0, -w))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.08 * math.sin(TAU * u - i * 0.8), 0.12 * math.sin(TAU * u * 0.5 - i * 0.9), 0))
        _add(pose, "Body", (0, -0.04 * length * a * math.sin(TAU * u + 0.3), 0, 0.04 * math.sin(TAU * u + 1.5), 0, 0))

    def move(t):
        pose = {}
        flap(pose, t / period, amp)
        if extra:
            extra(pose, "move", t / period, 0)
        return pose

    def idle(t):
        u = t / 3.2
        pose = {}
        flap(pose, u, amp * 0.35)
        _add(pose, "Body", (0, 0, 0, 0, 0.05 * math.sin(TAU * u * 0.5), 0.03 * math.sin(TAU * u)))
        return pose

    def attack(t):
        s = t / 0.9
        pose = {}
        st = _env(s, 0.2, 0.85)
        wd = _env(s, 0.0, 0.4)
        flap(pose, s * 1.5, amp * (0.6 + 0.8 * st))
        _add(pose, "Body", (0, 0.12 * length * wd, -0.25 * length * st, 0.35 * wd - 0.3 * st, 0, 0))
        for i, b in enumerate(tail):  # tail barb whips forward over the back
            _add(pose, b, (0, 0, 0, -0.55 * st * (1 + 0.3 * i), 0.0, 0))
        if extra:
            extra(pose, "attack", s, st)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0.04 * length * k, 0.1 * length * k, 0.2 * k, 0, 0.25 * k * math.sin(s * 9)))
        for rch, lch in wings:
            for r, l in zip(rch, lch):
                _add(pose, r, (0, 0, 0, 0, 0, 0.3 * k))
                _add(pose, l, (0, 0, 0, 0, 0, -0.3 * k))
        return pose

    H.clip("Move", period, move, keys=20)
    H.clip("Idle", 3.2, idle, keys=20)
    H.clip("Attack", 0.9, attack, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"swimAuthored": True, "length": length})


def scuttle(H, legs, claws=(), eyes=(), tail=(), antennae=(), period=0.7, height=1.0, side=True, extra=None):
    """Crab / lobster walk. legs: (hip, knee, side(+1 right / -1 left), phase). Alternating tetrapod gait: each leg
    swings fore-aft (ry about the hip, sideways-walking crabs swing in z too) and lifts (rz) during its swing.
    claws: (shoulder, elbow, finger, side) - the finger (movable dactyl) snaps in the attack."""

    def legpose(pose, u, k=1.0):
        for hip, knee, sd, ph in legs:
            w = (u + ph) % 1.0
            sw = math.sin(TAU * w)
            lift = max(0.0, math.cos(TAU * w)) ** 1.5
            _add(pose, hip, (0, 0, 0, 0, 0.28 * k * sw * sd, sd * 0.32 * k * lift))
            _add(pose, knee, (0, 0, 0, 0, 0, -sd * 0.25 * k * lift))

    def move(t):
        u = t / period
        pose = {}
        legpose(pose, u)
        _add(pose, "Body", (0.03 * height * math.sin(TAU * u) if side else 0, 0.035 * height * abs(math.sin(TAU * u * 2)), 0, 0, 0, 0.03 * math.sin(TAU * u)))
        for sh, el, fi, sd in claws:
            _add(pose, sh, (0, 0, 0, 0.08 * math.sin(TAU * u), 0, 0))
            _add(pose, fi, (0, 0, 0, 0.15 * max(0.0, math.sin(TAU * u * 2)), 0, 0))
        for i, b in enumerate(eyes):
            _add(pose, b, (0, 0, 0, 0.1 * math.sin(TAU * u * 2 + i), 0, 0))
        for i, b in enumerate(antennae):
            _add(pose, b, (0, 0, 0, 0.08 * math.sin(TAU * u * 2 + i), 0.15 * math.sin(TAU * u + i * 1.7), 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.05 * math.sin(TAU * u - i), 0, 0))
        if extra:
            extra(pose, "move", u, 0)
        return pose

    def idle(t):
        u = t / 3.0
        pose = {}
        _add(pose, "Body", (0, 0.015 * height * math.sin(TAU * u * 2), 0, 0, 0.04 * math.sin(TAU * u), 0))
        for sh, el, fi, sd in claws:
            _add(pose, sh, (0, 0, 0, 0.1 * math.sin(TAU * u + sd), 0, 0))
            _add(pose, el, (0, 0, 0, 0, sd * 0.08 * math.sin(TAU * u * 2), 0))
            snap = max(0.0, math.sin(TAU * (u * 2 + (0.3 if sd > 0 else 0.8)))) ** 8
            _add(pose, fi, (0, 0, 0, 0.45 * snap, 0, 0))
        for i, b in enumerate(eyes):
            _add(pose, b, (0, 0, 0, 0.12 * math.sin(TAU * u * 3 + i * 2), 0.1 * math.sin(TAU * u * 2 + i), 0))
        for i, b in enumerate(antennae):
            _add(pose, b, (0, 0, 0, 0.1 * math.sin(TAU * u * 2 + i), 0.2 * math.sin(TAU * u * 1.5 + i * 1.7), 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.04 * math.sin(TAU * u * 2 - i), 0, 0))
        legpose(pose, u * 2, 0.08)
        if extra:
            extra(pose, "idle", u, 0)
        return pose

    def attack(t):
        s = t / 0.8
        pose = {}
        wind = _env(s, 0.0, 0.45)
        strike = _env(s, 0.3, 0.8)
        _add(pose, "Body", (0, 0.06 * height * wind, -0.15 * height * strike, 0.12 * wind - 0.05 * strike, 0, 0))
        for sh, el, fi, sd in claws:
            _add(pose, sh, (0, 0, 0, 0.6 * wind - 0.2 * strike, -sd * 0.35 * strike, 0))
            _add(pose, el, (0, 0, 0, 0, sd * (0.3 * wind - 0.4 * strike), 0))
            op = _env(s, 0.05, 0.5)
            _add(pose, fi, (0, 0, 0, 0.6 * op, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, -0.25 * strike, 0, 0))
        if extra:
            extra(pose, "attack", s, strike)
        return pose

    def hit(t):
        s = t / 0.4
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0.05 * height * k, 0.12 * height * k, 0.2 * k, 0, 0.1 * k * math.sin(s * 12)))
        for sh, el, fi, sd in claws:
            _add(pose, sh, (0, 0, 0, 0.4 * k, sd * 0.3 * k, 0))
        for hip, knee, sd, ph in legs:
            _add(pose, hip, (0, 0, 0, 0, 0, sd * 0.25 * k))
        if extra:
            extra(pose, "hit", s, k)
        return pose

    H.clip("Move", period, move, keys=20)
    H.clip("Idle", 3.0, idle, keys=20)
    H.clip("Attack", 0.8, attack, keys=14, loop=False)
    H.clip("Hit", 0.4, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})


def tentacles(H, arms, mantle=(), period=1.6, height=3.0, jet=True, attack="grab", extra=None, idle_period=3.6):
    """Octopus / squid / jellyfish: arms = list of bone chains, each with an outward direction (dx, dz) so curls bend
    them out and up. Move: a jet pulse (arms open then snap together, mantle squeezes) with trailing curls."""

    def curl(pose, u, a, spread, k_open):
        for j, (chain, (dx, dz)) in enumerate(arms):
            ph = j * 0.37
            for i, b in enumerate(chain):
                lag = i * 0.55
                w = math.sin(TAU * u - lag + ph)
                # rotate about the axis perpendicular to the arm's outward direction: rx for z-out arms, rz for x-out
                bend = a * (0.35 + 0.25 * i) * w + spread * (0.8 if i == 0 else 0.2) * k_open
                _add(pose, b, (0, 0, 0, bend * dz, 0.05 * a * math.sin(TAU * u * 2 - lag + ph), -bend * dx))

    def move(t):
        u = t / period
        pose = {}
        pulse = math.sin(TAU * u)
        curl(pose, u, 0.22, 0.35, pulse if jet else 0.0)
        for i, b in enumerate(mantle):
            sq = 0.1 * pulse
            _add(pose, b, (0, 0, 0, 0.04 * math.sin(TAU * u - i), 0, 0))
        _add(pose, "Body", (0, 0.06 * height * math.sin(TAU * u - 1.2), 0, 0.05 * math.sin(TAU * u), 0, 0))
        if extra:
            extra(pose, "move", u, pulse)
        return pose

    def idle(t):
        u = t / idle_period
        pose = {}
        curl(pose, u, 0.14, 0.12, math.sin(TAU * u))
        _add(pose, "Body", (0, 0.03 * height * math.sin(TAU * u), 0, 0.02 * math.sin(TAU * u * 2), 0.05 * math.sin(TAU * u), 0))
        if extra:
            extra(pose, "idle", u, math.sin(TAU * u))
        return pose

    def attack_fn(t):
        s = t / 0.9
        pose = {}
        wind = _env(s, 0.0, 0.45)
        strike = _env(s, 0.3, 0.85)
        for j, (chain, (dx, dz)) in enumerate(arms):
            front = max(0.0, -dz)  # arms that point forward lash hardest
            for i, b in enumerate(chain):
                bend = (0.9 * wind - 1.2 * strike) * (0.4 + 0.3 * i) * (0.4 + 0.6 * front)
                _add(pose, b, (0, 0, 0, bend * dz + 0.3 * strike * front * (1 if i else 0), 0, -bend * dx))
        _add(pose, "Body", (0, 0.08 * height * wind, -0.22 * height * strike, 0.15 * wind - 0.2 * strike, 0, 0))
        if extra:
            extra(pose, "attack", s, strike)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0.05 * height * k, 0.1 * height * k, 0.15 * k, 0, 0.12 * k * math.sin(s * 10)))
        for chain, (dx, dz) in arms:
            for i, b in enumerate(chain):
                _add(pose, b, (0, 0, 0, -0.3 * k * dz, 0, 0.3 * k * dx))
        if extra:
            extra(pose, "hit", s, k)
        return pose

    H.clip("Move", period, move, keys=20)
    H.clip("Idle", idle_period, idle, keys=24)
    H.clip("Attack", 0.9, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"swimAuthored": True, "height": height})
