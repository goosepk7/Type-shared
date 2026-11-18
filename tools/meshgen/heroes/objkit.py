"""Shared helpers for the living-object / toy (h_objects) and robot-critter (h_bots) hero families: vector helpers,
eyes (googly, button, LED, cartoon), clip plumbing and small easing tools. Not an h_ module: build.py's mesh cache
hashes only the h_ file + kit.py, so after changing a helper here rebuild those two families with --force."""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF

TAU = 2 * math.pi


def T(a):
    return tuple(float(x) for x in a)


def A(*x):
    return np.array(x, float)


def U(*shapes, k=0.0):
    out = None
    for s_ in shapes:
        if s_ is None:
            continue
        out = s_ if out is None else (out.su(s_, k) if k > 0 else out | s_)
    return out


def add(pose, bone, v):
    if bone is None:
        return
    o = list(pose.get(bone, (0.0,) * 6))
    for i, x in enumerate(v):
        o[i] += x
    pose[bone] = tuple(o)


def ease(x):
    return 0.5 - 0.5 * math.cos(math.pi * min(max(x, 0.0), 1.0))


def bump(s, a, b):
    """0 -> 1 -> 0 between a and b (sine bump)."""
    if s <= a or s >= b:
        return 0.0
    return math.sin(math.pi * (s - a) / (b - a))


def env(s, wind_end=0.35, strike=(0.3, 0.8), rec_start=0.72):
    """Attack envelope: (wind, strike, recover-multiplier) for s in 0..1."""
    wind = ease(s / wind_end) * (1 - ease((s - wind_end) / 0.12))
    st = bump(s, strike[0], strike[1])
    rec = 1 - ease((s - rec_start) / (1 - rec_start))
    return wind, st, rec


def scaled(pose, k):
    for b, v in list(pose.items()):
        pose[b] = tuple(x * k for x in v)
    return pose


def hitk(t, L=0.45):
    s = t / L
    return math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)


def clips(H, idle, move, attack, hit, height, idle_len=2.4, move_len=0.8, attack_len=0.9, hit_len=0.45, keys=20):
    H.clip("Idle", idle_len, idle, keys=keys)
    H.clip("Move", move_len, move, keys=keys)
    H.clip("Attack", attack_len, attack, keys=16, loop=False)
    H.clip("Hit", hit_len, hit, keys=8, loop=False)
    H.rig.update({"height": height})


def spin(pose, bone, axis, t_keys, sym, sgn=1, speed=1.0):
    """Rotor / wheel spin: ~0.42 of the blade symmetry angle per key so Catmull-Rom between keys turns forward."""
    v = [0, 0, 0, 0, 0, 0]
    v[3 + "xyz".index(axis)] = sgn * sym * 0.42 * speed * t_keys
    add(pose, bone, v)


# ------------------------------------------------------------------------------------------------ eyes
def cartoon_eye(H, name, bone, pos, r, look=(0.0, 0.0, -1.0), white=True, pupil_r=0.55, pri=1.2, iris=None):
    """Big cartoon eye: white ball, dark pupil set toward `look`, two shines. name has '#' for a mirrored pair."""
    d = np.array(look, float)
    d /= np.linalg.norm(d)
    x, y, z = pos
    mk = H.mprim if "#" in name else H.prim
    if white:
        mk(name, bone, "Ellipsoid", (r * 2, r * 2.2, r * 2), (x, y, z), col="eyeWhite", mat="hard", role="eye", pri=pri)
    c = (x + d[0] * r * 0.62, y + d[1] * r * 0.62 + 0.0, z + d[2] * r * 0.62)
    pr = r * pupil_r * 2
    if iris:
        mk(name.replace("Eye", "Iris"), bone, "Ball", (pr * 1.35,) * 3, (x + d[0] * r * 0.55, y + d[1] * r * 0.55, z + d[2] * r * 0.55),
           col=iris, mat="hard", role="eye", pri=pri + 0.05)
    mk(name.replace("Eye", "Pupil"), bone, "Ellipsoid", (pr, pr * 1.1, pr), c, col="pupil", mat="hard", role="pupil", pri=pri + 0.1)
    mk(name.replace("Eye", "Shine"), bone, "Ball", (r * 0.36,) * 3, (c[0] + r * 0.18, c[1] + r * 0.28, c[2] + d[2] * r * 0.3),
       col="shine", mat="hard", role="shine", pri=pri + 1.2)


def button_eye(r, c, n=(0, 0, -1), holes=4, thick=0.35):
    """SDF of a sewing button facing n: a domed disc with a raised rim and thread holes."""
    n = np.asarray(n, float)
    n = n / np.linalg.norm(n)
    c = np.asarray(c, float)
    up = np.array([0.0, 1.0, 0.0]) if abs(n[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(up, n)
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    t = r * thick

    def f(p):
        q = p - c
        a, b, w = q @ u, q @ v, q @ n
        rr = np.sqrt(a * a + b * b)
        disc = np.maximum(rr - r, np.abs(w) - t)
        rim = np.sqrt((rr - r * 0.82) ** 2 + (w - t * 0.6) ** 2) - t * 0.55
        d = np.minimum(disc, rim)
        # dish between the rim and the holes
        dish = np.maximum(rr - r * 0.7, -(w - t * 0.85))
        d = np.maximum(d, -dish)
        for i in range(holes):
            ang = i / holes * TAU + math.pi / 4
            hx, hy = math.cos(ang) * r * 0.28, math.sin(ang) * r * 0.28
            hole = np.sqrt((a - hx) ** 2 + (b - hy) ** 2) - r * 0.1
            d = np.maximum(d, -hole)
        return d

    return SDF(f)


def led_eye(H, name, bone, pos, size, rot=(0, 0, 0), col="glow", pri=1.4, shape="Ellipsoid"):
    mk = H.mprim if "#" in name else H.prim
    mk(name, bone, shape, size, pos, rot=rot, col=col, mat="hard", glow=True, role="eye", pri=pri)


def googly(H, nm, bone, pos, r, n=(0, 0, -1), pupil_bone=None, pri=1.2):
    """Googly eye: white dome (piece-free prim) and a loose black pupil on its own bone so clips can jiggle it."""
    n = np.asarray(n, float)
    n /= np.linalg.norm(n)
    x, y, z = pos
    H.prim("Googly" + nm, bone, "Cylinder", (r * 0.5, r * 2, r * 2), (x, y, z), rot=(0, math.atan2(-n[0], -n[2]) + math.pi / 2, 0),
           col="eyeWhite", mat="plastic", role="eye", pri=pri)
    pb = pupil_bone or bone
    c = (x + n[0] * r * 0.2, y - r * 0.25, z + n[2] * r * 0.2)
    H.prim("Pupil" + nm, pb, "Cylinder", (r * 0.3, r * 1.05, r * 1.05), c, rot=(0, math.atan2(-n[0], -n[2]) + math.pi / 2, 0),
           col="pupil", mat="hard", role="pupil", pri=pri + 0.1)


def helix_rings(c, R, r, y0, y1, n, axis_tilt=0.0, flat=False):
    """Stack of n slightly tilted rings (reads as a coil spring) from y0 to y1 around centre c (x, z). flat: a
    ribbon-wire band (rectangular section) instead of a round wire."""
    out = None
    for i in range(n):
        y = y0 + (y1 - y0) * (i + 0.5) / n
        if flat:
            band = SDF(lambda p, R=R, r=r: np.maximum(np.abs(np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2) - R) - r * 0.9, np.abs(p[:, 1]) - r * 0.75) - r * 0.25)
            ring = band.rot(axis_tilt, 0, 0).at(c[0], y, c[1])
        else:
            ring = torus(R, r).scale3(1.0, 0.75, 1.0).rot(axis_tilt, 0, 0).at(c[0], y, c[1])
        out = ring if out is None else (out | ring)
    return out


def teeth_row(base, along, n, w, h, up=False):
    """A row of n cone teeth spread along `along` from `base`, pointing down (or up)."""
    base, along = np.asarray(base, float), np.asarray(along, float)
    out = None
    for i in range(n):
        p = base + along * (i - (n - 1) / 2) * w
        tooth = (cone(w * 0.5, 0.0, h * 0.5) if up else cone(0.0, w * 0.5, h * 0.5)).at(*(p + np.array([0, h * 0.5 if up else -h * 0.5, 0])))
        out = tooth if out is None else (out | tooth)
    return out


from kit import Hero  # noqa: E402


class OH(Hero):
    """Hero whose piece keys never carry spaces / dashes (ids like "teapot spirit" -> h_teapot_spirit_belly)."""

    def piece(self, name, bone, shape, key=None, **kw):
        key = (key or f"h_{self.id}_{name}").lower().replace("#", "").replace(" ", "_").replace("-", "_")
        return super().piece(name, bone, shape, key=key, **kw)
