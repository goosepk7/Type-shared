"""Hero models: whole summons / mounts authored as one sculpted model with their own skeleton and motion.

A hero is modelled in MODEL SPACE in studs (+Y up, -Z front, +X right, feet on y = 0) at any convenient size (the
engine rescales every summon to its size class). It is a list of bones (pure pivots, identity rotation, like the
procedural builder) and a list of parts, each welded to one bone:

* piece: an SDF sculpt meshed by tools/meshgen (marching cubes, smoothing, decimation, baked AO and an optional
  greyscale pattern mask), exported as a "box" piece whose box is the sculpt's own bounding box. The blueprint part
  is that box (Ellipsoid / Block primitive as the fallback when the asset is not loaded).
* prim: a plain primitive (eyes, pupils, glowing cores, flags): never meshed.

Colours are the builder's semantic keys ("primary", "secondary", "belly", "dark", "horn", "claw", "eyeWhite",
"pupil", "metal", "wood" ...): the word's own colours, materials, moods and accents still apply.

Mirrored pairs: `mpiece` / `mprim` / `mbone` take the RIGHT side (+X, names with "#" -> R / L) and add the left copy
(mirrored sculpt `<id>_l`), sharing a `pair` id so the budget keeps or drops them together.

Motion: `clip(name, length, fn)` samples fn(t) -> {bone: (px,py,pz,rx,ry,rz)} at `keys` points; the engine
(Summon/Motion.luau) plays these instead of its generic procedural gait (Idle / Move loop; Attack / Hit one-shots).
Euler angles are model-axis and compose down the chain like Roblox Motor6D.Transform = CFrame.new(p) *
CFrame.Angles(rx, ry, rz).
"""
from __future__ import annotations

import math

import numpy as np

import sdf as S

REG: dict = {}
FAMILY: dict = {}


def hero(hid, family):
    """Decorator: register a hero builder fn() -> Hero under `family` (the Luau data module it is written to)."""

    def deco(fn):
        REG[hid] = fn
        FAMILY[hid] = family
        return fn

    return deco


def _mirror_sdf(s):
    def f(p):
        q = p.copy()
        q[:, 0] = -q[:, 0]
        return s(q)

    return S.SDF(f)


class Hero:
    def __init__(self, hid, plan="Quadruped", gait="trot", seat=None, tags=()):
        self.id = hid
        self.plan = plan
        self.gait = gait
        self.bones = [("Body", None, (0.0, 0.0, 0.0))]
        self.bidx = {"Body": 0}
        self.parts = []
        self.rig = {"gait": gait}
        self.sockets = {}
        self.clips = {}
        self.npair = 0
        self.tags = list(tags)
        self.mount = {}

    # -------------------------------------------------------------------------------------------- skeleton
    def bone(self, name, parent, pos):
        if name in self.bidx:
            return name
        assert parent is None or parent in self.bidx, f"{self.id}: bone {name} parent {parent} unknown"
        self.bidx[name] = len(self.bones)
        self.bones.append((name, parent, tuple(float(v) for v in pos)))
        return name

    def body(self, pos):
        """Move the root Body pivot (call first)."""
        self.bones[0] = ("Body", None, tuple(float(v) for v in pos))

    def mbone(self, name, parent, pos):
        x, y, z = pos
        r = self.bone(name.replace("#", "R"), parent.replace("#", "R") if parent else None, (x, y, z))
        l = self.bone(name.replace("#", "L"), parent.replace("#", "L") if parent else None, (-x, y, z))
        return r, l

    def bpos(self, name):
        return np.array(self.bones[self.bidx[name]][2])

    # -------------------------------------------------------------------------------------------- parts
    def _pair(self):
        self.npair += 1
        return f"h{self.npair}"

    def piece(self, name, bone, shape, col="primary", mat="skin", pri=1.0, tris=900, role="body", key=None, pattern=None,
              res=112, smooth=4, ao=True, fallback="Ellipsoid", tr=0.0, glow=False, pair=None, mirrored=False, needs=None):
        assert bone in self.bidx, f"{self.id}: piece {name} on unknown bone {bone}"
        p = {
            "kind": "piece", "name": name, "bone": bone, "sdf": shape, "col": col, "mat": mat, "pri": pri, "tris": tris,
            "role": role, "key": key or f"h_{self.id}_{name}".lower().replace("#", ""), "pattern": pattern, "res": res,
            "smooth": smooth, "ao": ao, "fallback": fallback, "tr": tr, "glow": glow, "pair": pair, "mirrored": mirrored,
            "needs": needs,
        }
        self.parts.append(p)
        return p

    def mpiece(self, name, bone, shape, key=None, **kw):
        """Right-side piece (+X) and its mirrored left copy. `name` / `bone` contain "#"."""
        pair = self._pair()
        k = key or f"h_{self.id}_{name.replace('#', '')}".lower()
        pat = kw.pop("pattern", None)
        r = self.piece(name.replace("#", "R"), bone.replace("#", "R"), shape, key=k, pair=pair, pattern=pat, **kw)
        lpat = None
        if pat is not None:
            def lpat(P, _p=pat):
                Q = P.copy()
                Q[:, 0] = -Q[:, 0]
                return _p(Q)
        l = self.piece(name.replace("#", "L"), bone.replace("#", "L"), _mirror_sdf(shape), key=k + "_l", pair=pair, mirrored=True, pattern=lpat, **kw)
        return r, l

    def prim(self, name, bone, shape, size, pos, rot=(0, 0, 0), col="primary", mat="skin", pri=2.0, role="detail", tr=0.0,
             glow=False, pair=None, needs=None, trail=False):
        assert bone in self.bidx, f"{self.id}: prim {name} on unknown bone {bone}"
        p = {
            "kind": "prim", "name": name, "bone": bone, "shape": shape, "size": tuple(float(v) for v in size),
            "pos": tuple(float(v) for v in pos), "rot": tuple(float(v) for v in rot), "col": col, "mat": mat, "pri": pri,
            "role": role, "tr": tr, "glow": glow, "pair": pair, "needs": needs, "trail": trail,
        }
        self.parts.append(p)
        return p

    def mprim(self, name, bone, shape, size, pos, rot=(0, 0, 0), **kw):
        pair = self._pair()
        x, y, z = pos
        rx, ry, rz = rot
        r = self.prim(name.replace("#", "R"), bone.replace("#", "R"), shape, size, (x, y, z), (rx, ry, rz), pair=pair, **kw)
        l = self.prim(name.replace("#", "L"), bone.replace("#", "L"), shape, size, (-x, y, z), (rx, -ry, -rz), pair=pair, **kw)
        return r, l

    def eyes(self, bone, pos, r, col="iris", pupil="slit", shine=True, pri=1.2, look=(0.25, 0.0, -1.0)):
        """Animal eyes set into the sculpt's sockets: an iris ball, a pupil (round / slit / none) and a small shine,
        mirrored. `look` is the right eye's outward gaze direction (x out to the side, z forward)."""
        x, y, z = pos
        d = __import__("numpy").array(look, float)
        d = d / __import__("numpy").linalg.norm(d)
        self.mprim("Eye#", bone, "Ball", (r * 2, r * 2, r * 2), (x, y, z), col=col, mat="hard", pri=pri, role="eye")
        if pupil:
            c = (x + d[0] * r * 0.8, y + d[1] * r * 0.8, z + d[2] * r * 0.8)
            size = (r * 0.42, r * 1.25, r * 0.42) if pupil == "slit" else (r * 1.05, r * 1.05, r * 1.05)
            ry = __import__("math").atan2(-d[0], -d[2])
            self.mprim("Pupil#", bone, "Ellipsoid" if pupil == "slit" else "Ball", size, c, rot=(0, ry, 0), col="pupil", mat="hard", pri=pri + 0.1, role="pupil")
        if shine:
            c = (x + d[0] * r * 0.85 + r * 0.05, y + r * 0.4, z + d[2] * r * 0.85)
            self.mprim("Shine#", bone, "Ball", (r * 0.42,) * 3, c, col="shine", mat="hard", pri=pri + 1.4, role="shine")

    # -------------------------------------------------------------------------------------------- rig / motion
    def socket(self, name, pos, bone="Body"):
        self.sockets[name] = (tuple(float(v) for v in pos), bone)

    def clip(self, name, length, fn, keys=16, loop=True):
        """Sample fn(t) -> {bone: (px,py,pz,rx,ry,rz)} at `keys` evenly spaced times (cyclic when loop)."""
        n = keys
        times = [length * i / n for i in range(n)] if loop else [length * i / (n - 1) for i in range(n)]
        tracks = {}
        for i, t in enumerate(times):
            pose = fn(t)
            for b, v in pose.items():
                assert b in self.bidx, f"{self.id}: clip {name} bone {b} unknown"
                v = tuple(float(x) for x in v) + (0.0,) * (6 - len(v))
                tracks.setdefault(b, [None] * n)[i] = v
        for b, vals in tracks.items():
            for i in range(n):
                if vals[i] is None:
                    vals[i] = (0.0,) * 6
        self.clips[name] = {"len": float(length), "loop": loop, "keys": n, "tracks": tracks}

    def bounds_hint(self):
        """Model-space box enclosing every bone (+ margin): the region pieces are searched in."""
        P = np.array([b[2] for b in self.bones])
        lo, hi = P.min(0), P.max(0)
        ext = max(float((hi - lo).max()), 1.0)
        return lo - ext * 0.6 - 0.5, hi + ext * 0.6 + 0.5


# ------------------------------------------------------------------------------------------------ helpers
def rx(a):
    return (0, 0, 0, a, 0, 0)


def lerp(a, b, t):
    return a + (b - a) * t


def smooth_wave(t):
    return 0.5 - 0.5 * math.cos(2 * math.pi * t)


def add(pose, bone, v):
    o = list(pose.get(bone, (0.0,) * 6))
    for i, x in enumerate(v):
        o[i] += x
    pose[bone] = tuple(o)


# ------------------------------------------------------------------------------------------------ pattern masks
# A pattern fn(P) takes model-space points (N, 3) and returns a multiplier in 0..1 baked into the vertex colour.
def stripes(axis_fn, freq, width=0.35, depth=0.82, wobble=0.0, region=None, seed=0):
    """Dark bands: d = axis_fn(P) (a scalar field, e.g. z along the body), bands where frac(d * freq) < width."""
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6.28, 4)

    def f(P):
        d = axis_fn(P)
        if wobble:
            d = d + wobble * (np.sin(P[:, 1] * 3.1 + ph[0]) + 0.6 * np.sin(P[:, 0] * 4.7 + ph[1]))
        u = np.mod(d * freq, 1.0)
        band = np.clip(1 - np.abs(u - 0.5) / (width * 0.5), 0, 1)
        band = np.clip(band * 3, 0, 1)
        m = 1 - depth * band
        if region is not None:
            m = 1 - (1 - m) * np.clip(region(P), 0, 1)
        return m

    return f


def spots(cells, radius, depth=0.8, ring=False, region=None, seed=0):
    """Random spots (or rosette rings) on a jittered 3D lattice with `cells` spacing."""
    rng = np.random.default_rng(seed)
    jit = rng.uniform(-0.35, 0.35, (64, 3))

    def f(P):
        g = P / cells
        c = np.floor(g)
        best = np.full(len(P), 9.0)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    cc = c + (dx, dy, dz)
                    h = (np.abs(cc[:, 0] * 73856093 + cc[:, 1] * 19349663 + cc[:, 2] * 83492791).astype(np.int64)) % 64
                    pt = cc + 0.5 + jit[h]
                    best = np.minimum(best, np.linalg.norm(g - pt, axis=1))
        d = best * cells
        if ring:
            v = np.clip(1 - np.abs(d - radius * 0.75) / (radius * 0.3), 0, 1)
        else:
            v = np.clip((radius - d) / (radius * 0.25), 0, 1)
        m = 1 - depth * v
        if region is not None:
            m = 1 - (1 - m) * np.clip(region(P), 0, 1)
        return m

    return f


def gradient(axis, lo, hi, a=1.0, b=0.75):
    """Linear shade along an axis (e.g. darker legs): a at lo, b at hi."""

    def f(P):
        t = np.clip((P[:, axis] - lo) / (hi - lo), 0, 1)
        return a + (b - a) * t

    return f


def combine(*fs):
    def f(P):
        m = np.ones(len(P))
        for g in fs:
            if g is not None:
                m = m * g(P)
        return m

    return f
