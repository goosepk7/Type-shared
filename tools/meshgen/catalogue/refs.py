"""Reference blueprints (tools/meshgen/refs.json, written by export_refs.luau) for "unit" sculpts.

A unit sculpt is modelled in the reference blueprint's own model space (+Y up, -Z front, studs), on top of
the primitives the generator emitted, and then expressed in the unit frame of its lead part:

    G = group("wolf", "Head", ["Snout"])       # lead part + the primitives the sculpt contains
    G.sdf("Head")                               # that primitive as an SDF in model space
    G.blend(k)                                  # smooth union of lead + members
    G.c("Snout"), G.size("Snout"), G.axes("Head")   # centre, size, rotation columns (model space)
    G.unit(shape)                               # model-space SDF -> lead unit frame (what gets meshed)
    G.region(pad)                               # sampling half extents in unit coordinates

The lead's primitive stays part of the sculpt wherever the builder puts eyes or a mouth on it, so those
parts sit exactly on the sculpted surface for every seed and size (they are placed in the same unit frame).
"""
import json
import os

import numpy as np

import sdf as S

HERE = os.path.dirname(os.path.abspath(__file__))
_REFS = None


def refs():
    global _REFS
    if _REFS is None:
        _REFS = json.load(open(os.path.join(os.path.dirname(HERE), "refs.json")))
    return _REFS


def _prim(part):
    """Primitive as a model-space SDF."""
    pos = np.array(part["cf"][:3], float)
    R = np.array(part["cf"][3:], float).reshape(3, 3)
    sx, sy, sz = part["size"]
    shape = part["shape"]
    if shape in ("Ellipsoid", "Ball"):
        local = S.ellipsoid(sx / 2, sy / 2, sz / 2)
    elif shape == "Cylinder":
        r = min(sy, sz) / 2
        local = S.cylinder(r, sx / 2, axis=0)
    elif shape == "Wedge":
        n = np.array([0.0, sz, -sy])
        n /= np.linalg.norm(n)
        local = S.box(sx / 2, sy / 2, sz / 2) & S.plane(n, 0.0)
    else:
        local = S.box(sx / 2, sy / 2, sz / 2)
    return S.SDF(lambda p: local((p - pos) @ R))


class Group:
    def __init__(self, word, lead, members=()):
        bp = refs()[word]
        self.parts = {p["name"]: p for p in bp["parts"]}
        if lead not in self.parts:
            raise KeyError(f"{word}: no part {lead}; have {sorted(self.parts)}")
        self.lead = self.parts[lead]
        self.names = [lead] + [m for m in members]
        for m in members:
            if m not in self.parts:
                raise KeyError(f"{word}: no part {m}; have {sorted(self.parts)}")
        self.pos = np.array(self.lead["cf"][:3], float)
        self.R = np.array(self.lead["cf"][3:], float).reshape(3, 3)
        self.s = np.array(self.lead["size"], float)

    def part(self, name):
        return self.parts[name]

    def has(self, name):
        return name in self.parts

    def sdf(self, name):
        return _prim(self.parts[name])

    def c(self, name):
        return np.array(self.parts[name]["cf"][:3], float)

    def size(self, name):
        return np.array(self.parts[name]["size"], float)

    def axes(self, name):
        return np.array(self.parts[name]["cf"][3:], float).reshape(3, 3)

    def pt(self, name, ux, uy, uz):
        """Point given in a part's unit box coordinates (-0.5..0.5) -> model space."""
        return self.c(name) + self.axes(name) @ (np.array([ux, uy, uz]) * self.size(name))

    def blend(self, k, names=None):
        names = names or self.names
        s = self.sdf(names[0])
        for n in names[1:]:
            s = s.su(self.sdf(n), k)
        return s

    def unit(self, shape):
        pos, R, s = self.pos, self.R, self.s
        m = float(np.mean(s))
        return S.SDF(lambda u: shape((u * s) @ R.T + pos) / m)

    def to_unit(self, pts):
        return ((np.asarray(pts, float) - self.pos) @ self.R) / self.s

    def region(self, pad=0.12, extra=()):
        """Half extents (unit coords) of the group's boxes plus `extra` model-space points."""
        pts = []
        for n in self.names:
            p = self.parts[n]
            c, A, sz = self.c(n), self.axes(n), self.size(n)
            for sx in (-0.5, 0.5):
                for sy in (-0.5, 0.5):
                    for szz in (-0.5, 0.5):
                        pts.append(c + A @ (np.array([sx, sy, szz]) * sz))
        pts += [np.asarray(e, float) for e in extra]
        u = np.abs(self.to_unit(np.array(pts)))
        return tuple(float(v) for v in (u.max(0) + pad))


def group(word, lead, members=()):
    return Group(word, lead, members)
