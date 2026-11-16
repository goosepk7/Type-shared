"""Summon set: hard-surface stand-ins (bevelled blocks, cylinders, wedges, wheels).

Their flat faces lie exactly on the faces of the primitive they replace, so the z-fighting checker's verdict on
the primitive also covers the mesh (docs/SUMMON.md).
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from . import piece

import direct

# Bevelled blocks: one variant per proportion class (each axis 1, 3 or 9 units long, at least one axis 1), so
# the bevel keeps an even width when MeshMap stretches the closest variant to the part's Size.
_DIMS = {"1": 1.0, "3": 3.0, "9": 9.0}


def _block(a, b, c):
    return lambda: direct.rounded_box((a, b, c), 0.09, seg=1)


for _a in "139":
    for _b in "139":
        for _c in "139":
            if "1" in (_a, _b, _c):
                dims = (_DIMS[_a], _DIMS[_b], _DIMS[_c])
                piece(f"s_block_{_a}{_b}{_c}", tuple(d / 2 + 0.1 for d in dims), tris=300, fit=dims, note=f"Bevelled block, proportions {dims}.")(_block(*dims))

for _name, _len in (("disc", 0.3), ("drum", 1.0), ("rod", 3.0), ("pole", 9.0)):
    piece(f"s_cyl_{_name}", (_len / 2 + 0.1, 0.6, 0.6), tris=300, fit=(_len, 1.0, 1.0), note=f"Bevelled cylinder along X, length {_len} diameters.")(
        (lambda L: lambda: direct.bevel_cylinder(L, 0.5, 0.075, segs=20 if L >= 3 else 24))(_len))


@piece("s_hubcap", (0.3, 0.6, 0.6), tris=400, fit=(0.4, 1.0, 1.0))
def s_hubcap():
    """Wheel hub (axis X, same on both sides): rolled rim, dished face, domed centre cap."""
    h = 0.2
    half = [(h * 0.72, 0.0, 1, 0), (h * 0.7, 0.1, 1, 0.5), (h * 0.6, 0.17, 0.4, 1), (h * 0.58, 0.2, 1, 0.2), (h * 0.55, 0.36, 1, -0.3),
            (h * 0.85, 0.42, 0.6, -1), (h, 0.46, 1, 0.3), (h * 0.8, 0.5, 0.2, 1)]
    prof = [(-t, r, -nt, nr) for (t, r, nt, nr) in half] + [(t, r, nt, nr) for (t, r, nt, nr) in reversed(half)]
    return direct.lathe(prof, 16, axis=0)


@piece("s_turret", (0.7, 0.7, 0.7), tris=520, fit=(1.0, 0.62, 1.0))
def s_turret():
    """Cast tank turret (replaces the Turret ellipsoid; front -Z): turned dome with a hard shoulder line, gun
    mantlet block at the front, stowage bustle at the back, commander's cupola."""
    dome = direct.lathe([(-0.31, 0, -1, 0), (-0.31, 0.4, -1, 0), (-0.27, 0.47, -0.7, 0.7), (-0.12, 0.5, -0.1, 1), (-0.06, 0.49, 0.3, 1), (0.14, 0.38, 0.6, 0.8),
                         (0.25, 0.24, 0.85, 0.5), (0.3, 0.1, 1, 0.15), (0.31, 0, 1, 0)], 20, axis=1)
    mantlet = direct.moved(direct.rounded_box((0.34, 0.3, 0.16), 0.05, seg=0), (0, -0.07, -0.41))
    bustle = direct.moved(direct.rounded_box((0.5, 0.26, 0.24), 0.05, seg=0), (0, -0.1, 0.37))
    cupola = direct.moved(direct.bevel_cylinder(0.1, 0.13, 0.03, segs=12, axis=1), (0.17, 0.27, 0.1))
    return direct.merge(dome, mantlet, bustle, cupola)


@piece("s_tower_drum", (0.6, 0.6, 0.6), tris=500, fit=(1.0, 1.0, 1.0))
def s_tower_drum():
    """Round stone tower body (cylinder frame, axis X): stone courses as shallow rings, flat ends on the box faces."""
    n = 4
    prof = [(-0.5, 0, -1, 0), (-0.5, 0.47, -1, 0)]
    for i in range(n):
        a, b = -0.5 + i / n, -0.5 + (i + 1) / n
        g = 0.012
        prof += [(a + g, 0.5, -0.4, 1), (a + 2.5 * g, 0.5, 0, 1), (b - 2.5 * g, 0.5, 0, 1), (b - g, 0.5, 0.4, 1)]
        if i < n - 1:
            prof += [(b, 0.475, 0, 1)]
    prof += [(0.5, 0.47, 1, 0), (0.5, 0, 1, 0)]
    return direct.lathe(prof, 16, axis=0)
