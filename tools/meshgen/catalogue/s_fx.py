"""Summon set: hero sculpts for the tornado funnel, asteroid / meteor and the shark."""
import numpy as np

from sdf import *  # noqa: F401,F403
from . import piece
from .refs import Group

import direct


# ------------------------------------------------------------------------------------------------ tornado
@piece("s_funnel", (0.6, 0.6, 0.6), tris=1300, fit=(1.0, 0.6, 1.0))
def s_funnel():
    """Tornado funnel segment (ring ellipsoid frame, spins about Y): a flaring auger of air, three bold helical
    ridges winding up it, so the rotation of each ring reads like a barber pole."""
    m = direct.revolve([(-0.3, 0), (-0.29, 0.2), (-0.2, 0.3), (0.0, 0.36), (0.2, 0.41), (0.28, 0.42), (0.3, 0.3), (0.3, 0)], segs=30, spline=3)

    def fn(V):
        th = np.arctan2(V[:, 2], V[:, 0])
        rxz = np.hypot(V[:, 0], V[:, 2])
        c = np.cos(3 * th + 7.5 * V[:, 1])
        ridge = np.sign(c) * np.abs(c) ** 0.55
        k = 1 + 0.2 * np.clip(rxz / 0.25, 0, 1) * ridge
        V[:, 0] *= k
        V[:, 2] *= k
        V[:, 1] += 0.035 * np.clip(rxz / 0.3, 0, 1) * ridge
        return V
    return direct.deform(m, fn)


@piece("s_streak", (0.6, 0.2, 0.3), tris=200, fit=(1.0, 0.2, 0.3))
def s_streak():
    """Wind streak (long in X): a comet-shaped ribbon of fast air, blunt head, long thin tail."""
    return direct.revolve([(-0.5, 0), (-0.46, 0.09), (-0.34, 0.14), (-0.1, 0.11), (0.2, 0.06), (0.5, 0)], segs=10, axis=0, spline=2)


@piece("s_accretion", (0.6, 0.1, 0.6), tris=900, fit=(1.0, 0.05, 1.0))
def s_accretion():
    """Accretion disc (thin in Y, spins about Y): a pinwheel of two bright spiral arms of infalling matter with
    ragged outer streamers, so the disc visibly turns."""
    m = direct.revolve([(-0.025, 0), (-0.02, 0.3), (-0.008, 0.46), (0.0, 0.5), (0.008, 0.46), (0.02, 0.3), (0.025, 0)], segs=48, spline=2)

    def fn(V):
        th = np.arctan2(V[:, 2], V[:, 0])
        r = np.hypot(V[:, 0], V[:, 2])
        arm = 0.5 + 0.5 * np.cos(2 * th + 11.0 * r)
        edge = np.clip((r - 0.2) / 0.3, 0, 1)
        k = 1 - edge * (0.3 * (1 - arm) + 0.06 * np.cos(9 * th))
        V[:, 0] *= k
        V[:, 2] *= k
        V[:, 1] *= 0.55 + 0.9 * arm * np.clip(r / 0.25, 0.3, 1)
        return V
    return direct.deform(m, fn)


# ------------------------------------------------------------------------------------------------ asteroid / meteor
@piece("s_asteroid", (0.7, 0.7, 0.7), tris=3000, kind="unit", res=160, smooth=3)
def s_asteroid():
    """Cratered asteroid in the unit frame of the first Rock block (members: the other Rock blocks): a battered,
    faceted lump with a dozen rimmed impact craters."""
    rng = np.random.default_rng(7)
    s = ellipsoid(0.52, 0.47, 0.5).noise(0.05, 4.0, 3).noise(0.018, 11.0, 5)
    for _ in range(7):  # chipped facets
        n = rng.normal(size=3)
        n /= np.linalg.norm(n)
        s = s.si(plane(tuple(n), 0.43 + rng.uniform(0, 0.05)), 0.03)
    craters = []
    while len(craters) < 13:
        d = rng.normal(size=3)
        d /= np.linalg.norm(d)
        r = rng.uniform(0.07, 0.17)
        if all(np.linalg.norm(d - c[0]) > (r + c[1]) * 2.4 for c in craters):
            craters.append((d, r))
    for d, r in craters:
        s = s.su(torus(r * 0.95, r * 0.26, axis=1).warp(_align(d, 0.46)), 0.03)
    for d, r in craters:
        s = s.ss(ellipsoid(r * 0.86, r * 0.75, r * 0.86).warp(_align(d, 0.5)), 0.02)
    return s


def _align(d, dist):
    """Warp that puts a shape authored around the origin (axis +Y) at d * dist with its axis along d."""
    d = np.asarray(d, float)
    a = np.cross([0.0, 1.0, 0.0], d)
    if np.linalg.norm(a) < 1e-6:
        a = np.array([1.0, 0.0, 0.0])
    a /= np.linalg.norm(a)
    b = np.cross(d, a)
    R = np.stack([a, d, b])  # rows: local x, y, z in world
    return lambda p: (p - d * dist) @ R.T


@piece("s_blaze", (0.6, 0.6, 0.7), tris=900, fit=(1.0, 1.0, 1.16), res=130)
def s_blaze():
    """Flame shroud / comet tail (front -Z, streams back to +Z): a hot rounded bow with seven tongues of fire
    of uneven length peeling off behind it."""
    s = ellipsoid(0.34, 0.34, 0.3, (0, 0, -0.25))
    rng = np.random.default_rng(3)
    for i in range(7):
        a = i / 7 * 2 * np.pi + 0.3
        ln = 0.25 + 0.5 * rng.uniform()
        s = s.su(round_cone((np.cos(a) * 0.2, np.sin(a) * 0.2, -0.18), (np.cos(a + 0.7) * 0.36, np.sin(a + 0.7) * 0.36, ln), 0.16, 0.012), 0.06)
    return s.su(round_cone((0, 0, -0.1), (0, 0.03, 0.85), 0.2, 0.015), 0.06)


# ------------------------------------------------------------------------------------------------ shark
SW = "sig:shark"
GSB, GSR = Group(SW, "Body", ["Belly"]), Group(SW, "Rear")
GST, GSD = Group(SW, "TailTop", ["TailLow"]), Group(SW, [p["name"] for p in GSB.parts.values() if p.get("role") == "fin" and p["shape"] == "Wedge" and p.get("bone") == "Body"][0])


def _unit(pid, G, tris, res, note, extra=(), pad=0.3):
    def deco(fn):
        piece(pid, G.region_local(pad, extra), tris=tris, kind="unit", res=res, note=note, lead=tuple(G.s), smooth=4)(lambda: G.local(fn()))
        return fn
    return deco


def _fin(parts, thick):
    s = None
    for (a, b, r0, r1) in parts:
        c = round_cone(a, b, r0, r1)
        s = c if s is None else s.su(c, 0.25)
    return s.si(box(thick, 99, 99), thick * 0.9)


@_unit("s_shark_body", GSB, 2600, 170, "Shark body (lead Body): torpedo trunk, pointed overhanging snout, brow, gill bulge, dorsal ridge, pectoral roots.",
       extra=[(0, 5.0, -7.7), (1.6, 4.7, -2)])
def shark_body():
    s = GSB.sdf("Body")
    s = s.su(round_cone((0, 5.05, -5.4), (0, 4.78, -7.45), 0.66, 0.2), 0.22)  # snout
    s = s.su(ellipsoid(0.5, 0.2, 1.0, (0, 5.2, -6.2)), 0.2)
    s = s.su(ellipsoid(0.22, 0.75, 2.6, (0, 6.45, -1.2)), 0.3)  # dorsal ridge
    s = s.su(ellipsoid(0.5, 0.45, 0.9, (1.05, 3.95, -1.9)).mirror_x(), 0.25)  # pectoral roots
    s = s.su(ellipsoid(0.3, 0.9, 0.9, (1.2, 4.85, -3.6)).mirror_x(), 0.3)  # gill bulge
    s = s.su(round_cone((0, 4.7, 0.6), (0, 4.68, 2.6), 1.15, 0.95), 0.3)  # flows into the tail stock
    # the pale Belly primitive stays a separate part: recess the trunk around it so the two surfaces never run
    # coincident (the belly stands 0.12 proud of the sculpt everywhere they meet)
    belly = GSB.sdf("Belly")
    return s.ss(SDF(lambda p: belly(p) - 0.12), 0.06)


@_unit("s_shark_rear", GSR, 1300, 150, "Shark tail stock (lead Rear): tapering peduncle, lateral keels, second dorsal and anal fins.",
       extra=[(0, 6.6, 4.4), (0, 2.8, 4.4), (1.2, 4.7, 5)])
def shark_rear():
    s = GSR.sdf("Rear")
    s = s.su(round_cone((0, 4.68, 0.4), (0, 4.68, 2.2), 1.1, 0.95), 0.25)
    s = s.su(round_cone((0, 4.68, 4.4), (0, 4.75, 6.3), 0.55, 0.3), 0.2)
    s = s.su(ellipsoid(0.42, 0.1, 0.9, (0.3, 4.7, 5.6)).mirror_x(), 0.1)  # caudal keels
    s = s.su(_fin([((0, 5.75, 3.6), (0, 6.5, 4.6), 0.3, 0.06), ((0, 5.7, 3.7), (0, 5.75, 4.5), 0.3, 0.2)], 0.07), 0.12)
    s = s.su(_fin([((0, 3.7, 3.7), (0, 3.0, 4.6), 0.28, 0.06), ((0, 3.75, 3.8), (0, 3.7, 4.5), 0.28, 0.2)], 0.07), 0.12)
    return s


@_unit("s_shark_tail", GST, 900, 150, "Shark caudal fin (lead TailTop, member TailLow): tall crescent, long upper lobe, notched trailing edge.",
       extra=[(0.3, 5, 6)])
def shark_tail():
    up = _fin([((0, 4.75, 6.0), (0, 6.3, 7.4), 0.55, 0.38), ((0, 6.3, 7.4), (0, 7.35, 8.85), 0.38, 0.08)], 0.09)
    lo = _fin([((0, 4.7, 6.0), (0, 3.6, 7.0), 0.5, 0.3), ((0, 3.6, 7.0), (0, 2.7, 8.2), 0.3, 0.07)], 0.09)
    s = up.su(lo, 0.2)
    return s.ss(ellipsoid(1.0, 1.05, 0.75, (0, 4.95, 8.15)), 0.15)


@_unit("s_shark_dorsal", GSD, 600, 140, "Shark dorsal fin (lead: the dorsal fin wedge): swept-back sail, thick leading edge, hooked tip.",
       extra=[(0.4, 7, 0)])
def shark_dorsal():
    s = _fin([((0, 6.3, -2.2), (0, 8.6, -0.1), 0.6, 0.3), ((0, 8.6, -0.1), (0, 9.55, 1.0), 0.3, 0.07), ((0, 6.3, -1.6), (0, 6.3, 0.5), 0.6, 0.5),
              ((0, 6.9, -0.9), (0, 8.1, 0.2), 0.75, 0.4)], 0.12)
    return s.ss(ellipsoid(1.0, 1.25, 0.9, (0, 7.95, 1.45)), 0.15)
