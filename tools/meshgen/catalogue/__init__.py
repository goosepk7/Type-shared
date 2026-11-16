"""Mesh catalogue registry.

Each piece is registered with @piece(id, region, tris=..., fit=..., kind=..., note=...):

* region : half extents of the sampling box in authoring units (the sculpt must lie inside it).
* fit    : final native size (full extents). "Box" pieces replace a primitive Part and fill the Part's
           box exactly, so fit = the canonical Part size and the MeshPart is simply resized to the
           Part's Size at runtime. Omit fit for "anchor-space" pieces (hats, faces, held items) that
           are authored in anchor units (head radius, eye radius, ...): their native size and the
           authoring-space origin are recorded and Luau places them with MeshLibrary.place().
* kind   : "box" | "anchor" | "unit"  ("unit" pieces are authored in the unit frame of the primitive part they
           replace: the part's box is [-0.5, 0.5]^3, native size and origin are recorded in those units and
           MeshLibrary.fit() scales them per axis by the part's Size, so a sculpt can reach outside the box of
           its lead part, e.g. a head that also contains the snout)
* mirror : also register "<id>_l", the same sculpt mirrored in x, for the left copy of a mirrored pair
           (Builder.mirror keeps a right-handed frame, so an asymmetric piece needs a mirrored mesh)

Conventions: +Y up, -Z = front, +X = right. Cylinder replacements use the Part's own axis (X).
Wedge replacements fill the wedge's triangle: (y=-.5, z=-.5), (y=-.5, z=+.5), (y=+.5, z=+.5) in
unit box coordinates (the vertical edge is at +Z).
"""
from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple

REGISTRY: dict = {}


@dataclass
class Piece:
    id: str
    fn: Callable
    region: Tuple[float, float, float]
    tris: int = 1200
    fit: Optional[Tuple[float, float, float]] = None
    kind: str = "box"
    note: str = ""
    res: int = 120
    smooth: int = 6
    pivot: str = "center"
    tags: list = field(default_factory=list)
    set: str = "td"
    lead: Optional[Tuple[float, float, float]] = None


def piece(id, region, tris=1200, fit=None, kind=None, note="", res=120, smooth=6, pivot="center", mirror=False, set=None, lead=None):
    """Same signature as the Type-defend copy plus three optional keywords: mirror, set, lead.
    lead (unit pieces): size in studs of the reference lead primitive. The sculpt is then authored in the lead's
    local frame in STUDS (true proportions, so normals survive the stretch) and the manifest size / origin are
    divided by it to give unit-frame values."""

    def deco(fn):
        k = kind or ("box" if fit else "anchor")
        doc = note or (fn.__doc__ or "").strip()
        group = set or _CURRENT_SET[0]
        REGISTRY[id] = Piece(id, fn, tuple(region), tris, tuple(fit) if fit else None, k, doc, res, smooth, pivot, [], group, tuple(lead) if lead else None)
        if mirror:
            REGISTRY[id + "_l"] = Piece(id + "_l", lambda: _mirrored(fn()), tuple(region), tris, tuple(fit) if fit else None, k, doc + " (left: mirrored in x)", res, smooth, pivot, [], group, tuple(lead) if lead else None)
        return fn

    return deco


def _mirrored(shape):
    """x-mirror of an SDF or of a direct mesh (winding flipped so it stays outward-facing)."""
    if hasattr(shape, "warp"):
        return shape.warp(_flip_x)
    import direct

    flip = [-1.0, 1.0, 1.0]
    m = direct._finish(shape.vertices * flip, shape.direct_normals * flip, shape.faces[:, ::-1])
    return m


def _flip_x(p):
    q = p.copy()
    q[:, 0] = -q[:, 0]
    return q


_CURRENT_SET = ["td"]
# Modules ported unchanged from Type-defend (set "td", asset ids shared with that game) and the Summon set.
_MODULES = [("td", ["body", "features", "face"]), ("summon", ["s_organic", "s_heads", "s_hard", "s_hero", "s_dragon", "s_fx"])]


def load_all():
    import importlib

    if not REGISTRY:
        for group, mods in _MODULES:
            _CURRENT_SET[0] = group
            for m in mods:
                importlib.import_module("." + m, __name__)
    return REGISTRY
