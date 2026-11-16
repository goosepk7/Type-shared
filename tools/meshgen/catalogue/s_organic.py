"""Summon set: organic limb / tail / horn / claw pieces that stand in for single primitives.

Frames (see README "Summon piece frames"):
* segment pieces run along +Y from the root (thick, -Y) to the far end (+Y), like Builder.limb;
* wedge pieces fill the WedgePart triangle (y=-.5,z=-.5) (y=-.5,z=+.5) (y=+.5,z=+.5): full height at +Z;
* everything is symmetric in x unless registered with mirror=True.
"""
import numpy as np

from sdf import *  # noqa: F401,F403
import direct
from . import piece


def _ridges(shape, n, amp, lo, hi):
    """Growth rings around the Y axis between y=lo and y=hi."""
    return SDF(lambda p: shape(p) - amp * np.clip(np.sin((p[:, 1] - lo) / (hi - lo) * np.pi * n) - 0.2, 0, 1))


@piece("s_limb", (0.3, 0.6, 0.3), tris=260, fit=(0.42, 1.0, 0.42))
def s_limb():
    """Limb segment (+Y = far end): full shoulder, muscle belly, narrower wrist."""
    return direct.revolve([(-0.5, 0), (-0.44, 0.13), (-0.3, 0.2), (-0.1, 0.215), (0.12, 0.17), (0.32, 0.135), (0.45, 0.11), (0.5, 0)], segs=12, spline=2)


@piece("s_tail_seg", (0.3, 0.6, 0.3), tris=200, fit=(0.5, 1.0, 0.5))
def s_tail_seg():
    """Tail / tentacle segment (+Y = toward the tip): tapers by the same ratio as the next segment."""
    return direct.revolve([(-0.5, 0), (-0.44, 0.17), (-0.25, 0.245), (0.1, 0.215), (0.38, 0.175), (0.47, 0.11), (0.5, 0)], segs=10, spline=2)


@piece("s_tail_tip", (0.3, 0.6, 0.3), tris=200, fit=(0.5, 1.0, 0.5))
def s_tail_tip():
    """Last tail segment: tapers to a soft point at +Y."""
    return direct.revolve([(-0.5, 0), (-0.44, 0.17), (-0.25, 0.245), (0.05, 0.19), (0.3, 0.1), (0.46, 0.035), (0.5, 0)], segs=10, spline=2)


@piece("s_horn_seg", (0.3, 0.6, 0.3), tris=300, fit=(0.5, 1.0, 0.5))
def s_horn_seg():
    """Horn segment (+Y = toward the tip) with growth rings."""
    return direct.revolve([(-0.5, 0), (-0.46, 0.16), (-0.36, 0.225), (-0.27, 0.2), (-0.16, 0.215), (-0.07, 0.185), (0.05, 0.2), (0.14, 0.17),
                           (0.26, 0.182), (0.36, 0.15), (0.46, 0.1), (0.5, 0)], segs=12, spline=2)


@piece("s_horn_tip", (0.3, 0.65, 0.3), tris=300, fit=(0.5, 1.0, 0.5))
def s_horn_tip():
    """Horn tip: ringed at the base, drawn out to a sharp point at +Y, tip curling slightly to -Z."""
    m = direct.revolve([(-0.5, 0), (-0.46, 0.16), (-0.36, 0.225), (-0.27, 0.2), (-0.16, 0.21), (-0.06, 0.17), (0.1, 0.125), (0.3, 0.06), (0.5, 0)], segs=12, spline=2)

    def bend(V):
        V[:, 2] -= 0.12 * np.clip(V[:, 1] + 0.1, 0, 1) ** 2
        return V

    return direct.deform(m, bend)


def _thorn(profile, path, flat, segs=10):
    """Cone revolved about Y then swept along `path(t)` -> (y, z) offsets for t in 0..1; flat = x scale."""
    m = direct.revolve(profile, segs=segs, spline=3)

    def f(V):
        t = np.clip(V[:, 1] + 0.5, 0, 1)
        dy, dz = path(t)
        V[:, 0] *= flat
        V[:, 2] += dz
        V[:, 1] += dy
        return V

    return direct.deform(m, f)


@piece("s_spike_w", (0.2, 0.6, 0.6), tris=160, fit=(0.24, 1.0, 0.9))
def s_spike_w():
    """Back spike (wedge frame): thorn rising from the base to a point at the top-back, leading edge swept."""
    return _thorn([(-0.5, 0), (-0.47, 0.3), (-0.2, 0.26), (0.15, 0.14), (0.4, 0.05), (0.5, 0)], lambda t: (0 * t, 0.42 * t ** 1.6), 0.4)


@piece("s_tooth_w", (0.3, 0.6, 0.4), tris=160, fit=(0.45, 1.0, 0.5))
def s_tooth_w():
    """Tooth (wedge frame, the generator turns it point-down): conical fang, point at the top-back."""
    return _thorn([(-0.5, 0), (-0.47, 0.22), (-0.2, 0.2), (0.15, 0.12), (0.4, 0.045), (0.5, 0)], lambda t: (0 * t, 0.16 * t ** 1.5), 0.9)


@piece("s_claw_w", (0.2, 0.4, 0.6), tris=160, fit=(0.42, 0.75, 1.0))
def s_claw_w():
    """Claw (wedge frame): thick root at the back (+Z), hooking down to a point at the front-bottom."""
    m = _thorn([(-0.5, 0), (-0.46, 0.27), (-0.2, 0.25), (0.1, 0.17), (0.35, 0.07), (0.5, 0)], lambda t: (0 * t, -0.3 * t ** 2), 0.75)
    # lay it along -Z: root (+Z) -> tip (-Z, low)
    R = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)  # y -> -z, z -> y
    return direct.moved(m, rot=R)


@piece("s_fin_w", (0.12, 0.6, 0.65), tris=260, fit=(0.14, 1.0, 1.1), res=110)
def s_fin_w():
    """Fin (wedge frame): shark-fin blade, swept leading edge, tip at the top-back, concave trailing edge, thick root."""
    def f(p):
        y, z = p[:, 1], p[:, 2]
        t = np.clip((y + 0.5), 0, 1)  # 0 root .. 1 tip
        lead = -0.52 + 0.98 * t ** 0.75  # leading edge z
        trail = 0.5 - 0.16 * np.sin(np.pi * t) * (1 - t * 0.3)  # concave trailing edge
        mid = (lead + trail) / 2
        half = np.maximum((trail - lead) / 2, 1e-3)
        prof = np.abs(z - mid) - half
        top = y - 0.47
        bot = -0.5 - y
        d2 = np.maximum(np.maximum(prof, top), bot)
        th = 0.065 * (1 - 0.72 * t) * np.sqrt(np.clip(1 - ((z - mid) / (half + 0.02)) ** 2, 0.02, 1))
        return np.maximum(d2 * 0.7, np.abs(p[:, 0]) - th)
    return SDF(f).round(0.012)


@piece("s_ear_w", (0.14, 0.6, 0.5), tris=260, fit=(0.2, 1.0, 0.72), res=110)
def s_ear_w():
    """Pointed ear (wedge frame: upright edge at +Z, tip at the top): leaf-shaped shell, cupped on its -X face."""
    def f(p):
        y, z = p[:, 1], p[:, 2]
        t = np.clip(y + 0.5, 0, 1)
        back = 0.46 - 0.05 * t
        front = -0.46 + 0.86 * t ** 0.85
        mid = (front + back) / 2
        half = np.maximum((back - front) / 2, 1e-3)
        prof = np.maximum(np.maximum(np.abs(z - mid) - half, y - 0.47), -0.5 - y)
        u = np.clip((z - mid) / (half + 0.03), -1, 1)
        bow = 0.05 * (1 - u * u) * (1 - 0.6 * t)  # shell bows toward +X, leaving a cup on -X
        th = 0.035 + 0.03 * (1 - t)
        return np.maximum(prof * 0.7, np.abs(p[:, 0] - bow + 0.02) - th)
    return SDF(f).round(0.015)


@piece("s_fist", (0.6, 0.6, 0.6), tris=520, fit=(1.0, 1.0, 1.0), res=96)
def s_fist():
    """Fist (front -Z): rounded palm, four knuckles across the front, finger grooves, wrist stub at the top-back."""
    palm = ellipsoid(0.44, 0.4, 0.42, (0, -0.02, 0.03))
    s = palm
    for i, x in enumerate((-0.27, -0.09, 0.09, 0.27)):
        s = s.su(sphere(0.125, (x, 0.12 - abs(x) * 0.15, -0.3)), 0.07)
        s = s.su(capsule((x, 0.1, -0.32), (x, -0.24, -0.26), 0.105), 0.05)
    for x in (-0.18, 0.0, 0.18):
        s = s.ss(capsule((x, 0.2, -0.42), (x, -0.3, -0.36), 0.03), 0.03)
    s = s.su(ellipsoid(0.26, 0.2, 0.26, (0, 0.3, 0.14)), 0.12)
    return s


@piece("s_hoof", (0.5, 0.6, 0.6), tris=260, fit=(0.6, 1.0, 1.0))
def s_hoof():
    """Hoof (cylinder frame: axis X, +X up): flared wall, coronet band at the top, slightly domed sole."""
    return direct.revolve([(-0.3, 0), (-0.27, 0.4), (-0.2, 0.5), (-0.05, 0.47), (0.12, 0.41), (0.2, 0.44), (0.27, 0.4), (0.3, 0)], segs=12, axis=0, spline=2)


@piece("s_wing_feather", (0.6, 0.2, 0.4), tris=400, fit=(1.0, 0.16, 0.42), mirror=True)
def s_wing_feather():
    """Feathered wing blade (root -X, tip +X, leading edge -Z): thick leading arm, layered flight feathers with
    scalloped trailing tips."""
    lead = lambda t: -0.2 + 0.05 * np.sin(t * np.pi) - 0.02 * t
    trail = lambda t: lead(t) + 0.42 * (0.72 + 0.4 * np.sin(np.pi * min(t * 0.9 + 0.05, 1))) * (1 - 0.3 * t ** 3) - 0.04 * abs(np.sin(t * np.pi * 6))
    thick = lambda t, u: (0.03 + 0.075 * (1 - u) ** 1.6) * (1 - 0.45 * t) + 0.012 * (np.cos(t * np.pi * 12) > 0) * (u > 0.3)
    return direct.blade(lead, trail, thick, camber=lambda t, u: 0.02 * (1 - u), nt=25, nu=7)


# ------------------------------------------------------------------------------------------------ bodies
@piece("s_body_quad", (0.7, 0.75, 0.75), tris=1500, kind="unit", res=128)
def s_body_quad():
    """Quadruped body in the Torso ellipsoid's unit frame (front -Z): barrel, deep chest with shoulder blades,
    tucked waist, haunches with hip muscles, a soft spine line. Members: Chest, Haunch."""
    torso = sphere(0.5)
    chest = ellipsoid(0.53, 0.56, 0.265).rot(-10, 0, 0).at(0, 0.05, -0.35)
    haunch = ellipsoid(0.5, 0.51, 0.255, (0, 0.04, 0.33))
    s = torso.su(chest, 0.1).su(haunch, 0.1)
    s = s.su(ellipsoid(0.17, 0.3, 0.1, (0.36, 0.2, -0.36)).mirror_x(), 0.07)  # shoulder blades
    s = s.su(ellipsoid(0.19, 0.3, 0.11, (0.36, 0.12, 0.35)).mirror_x(), 0.07)  # hips
    s = s.su(ellipsoid(0.05, 0.06, 0.42, (0, 0.5, 0.0)), 0.07)  # spine
    s = s.ss(ellipsoid(0.7, 0.14, 0.09, (0, -0.52, 0.04)), 0.08)  # waist tuck under the belly
    return s


@piece("s_torso", (0.7, 0.7, 0.7), tris=1100, kind="unit", res=120)
def s_torso():
    """Upright / biped torso in the Torso ellipsoid's unit frame: rounded shoulders, chest swell, hip roll,
    spine groove down the back."""
    s = sphere(0.5)
    s = s.su(ellipsoid(0.56, 0.2, 0.3, (0, 0.27, 0.0)), 0.2)  # shoulder girdle
    s = s.su(ellipsoid(0.36, 0.22, 0.2, (0, 0.14, -0.33)), 0.2)  # chest
    s = s.su(ellipsoid(0.5, 0.2, 0.36, (0, -0.3, 0.03)), 0.2)  # hips
    s = s.ss(capsule((0, 0.3, 0.54), (0, -0.3, 0.54), 0.04), 0.1)
    return s


@piece("s_body_seg", (0.4, 0.6, 0.4), tris=300, fit=(0.6, 1.0, 0.6))
def s_body_seg():
    """Body / neck segment along Y: a barrel with two soft rings (serpent coils, necks)."""
    return direct.revolve([(-0.5, 0), (-0.45, 0.17), (-0.3, 0.27), (-0.17, 0.285), (-0.08, 0.27), (0.0, 0.29), (0.08, 0.27), (0.17, 0.285), (0.3, 0.27),
                           (0.45, 0.17), (0.5, 0)], segs=12, spline=1)


@piece("s_ear_cup", (0.6, 0.6, 0.3), tris=360, fit=(1.0, 1.0, 0.36), res=96)
def s_ear_cup():
    """Round / long ear (front -Z): thick rounded rim around a cupped hollow, thicker at the root."""
    s = ellipsoid(0.5, 0.5, 0.17)
    s = s.ss(ellipsoid(0.33, 0.35, 0.16, (0, 0.04, -0.17)), 0.06)
    return s.su(ellipsoid(0.26, 0.16, 0.15, (0, -0.4, 0.02)), 0.08)


@piece("s_feather", (0.6, 0.1, 0.25), tris=200, fit=(1.0, 0.09, 0.26))
def s_feather():
    """Single flight feather (root -X, tip +X): pointed vane with a raised shaft; the same from both sides."""
    half = lambda t: 0.125 * np.sin(np.pi * min(t * 0.86 + 0.1, 1)) ** 0.7
    return direct.blade(lambda t: -half(t), half, lambda t, u: 0.012 + 0.03 * np.exp(-((u - 0.5) / 0.14) ** 2) * (1 - 0.7 * t), nt=12, nu=7)


@piece("s_fin_side", (0.6, 0.12, 0.4), tris=300, fit=(1.0, 0.1, 0.36), mirror=True)
def s_fin_side():
    """Pectoral fin / flipper (root -X, tip +X, swept toward +Z): thick rounded leading edge, thin trailing edge, rays."""
    lead = lambda t: -0.17 + 0.22 * t ** 1.6
    trail = lambda t: lead(t) + (0.33 - 0.05 * abs(np.sin(t * np.pi * 4))) * np.sqrt(max(1 - t ** 4, 0.03))
    return direct.blade(lead, trail, lambda t, u: (0.012 + 0.04 * (1 - u) ** 1.5) * (1 - 0.55 * t), nt=17, nu=6)


# ------------------------------------------------------------------------------------- clouds, plants, fire
def _lumps(base, n, r, amp, seed, k=0.12, squash=1.0):
    """Cauliflower surface: n lobes of radius r set on the unit sphere (Fibonacci), blended."""
    rng = np.random.default_rng(seed)
    s = base
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        rad = np.sqrt(1 - y * y)
        a = i * 2.399963 + rng.uniform(-0.25, 0.25)
        c = np.array([np.cos(a) * rad, y * squash, np.sin(a) * rad]) * amp
        s = s.su(sphere(r * rng.uniform(0.85, 1.15), c), k)
    return s


@piece("s_puff", (0.7, 0.7, 0.7), tris=900, fit=(1.0, 1.0, 1.0), res=110)
def s_puff():
    """Cloud / smoke puff: billowing cluster of rounded lobes (looks the same from every side)."""
    return _lumps(sphere(0.34), 14, 0.2, 0.3, 3, k=0.1)


@piece("s_canopy", (0.7, 0.7, 0.7), tris=1100, fit=(1.0, 1.0, 1.0), res=120)
def s_canopy():
    """Leafy canopy / bush clump: many small leaf clusters over a full crown."""
    return _lumps(sphere(0.37), 30, 0.125, 0.35, 11, k=0.07)


@piece("s_trunk_x", (0.7, 0.5, 0.5), tris=700, fit=(1.0, 0.5, 0.5), res=120)
def s_trunk_x():
    """Tree trunk (cylinder frame: axis X, -X = ground): flared root buttresses, bark ridges, slight lean."""
    def f(p):
        x = p[:, 0]
        a = np.arctan2(p[:, 2], p[:, 1])
        r = np.sqrt(p[:, 1] ** 2 + p[:, 2] ** 2)
        t = np.clip(x + 0.5, 0, 1)
        rad = 0.17 + 0.075 * np.exp(-t * 7) * (1 + 0.5 * np.cos(a * 5)) + 0.012 * np.cos(a * 9 + x * 6) + 0.02 * (t > 0.85) * (t - 0.85) / 0.15
        return np.maximum((r - rad) * 0.7, np.abs(x) - 0.5)
    return SDF(f).round(0.01)


@piece("s_trunk_y", (0.5, 0.7, 0.5), tris=700, fit=(0.5, 1.0, 0.5), res=120)
def s_trunk_y():
    """Tree trunk for an upright ellipsoid (-Y = ground): root flare, bark ridges, tapering into the crown."""
    def f(p):
        y = p[:, 1]
        a = np.arctan2(p[:, 2], p[:, 0])
        r = np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2)
        t = np.clip(y + 0.5, 0, 1)
        rad = (0.19 - 0.05 * t) + 0.07 * np.exp(-t * 7) * (1 + 0.5 * np.cos(a * 5)) + 0.012 * np.cos(a * 9 + y * 6)
        rad = rad * np.sqrt(np.clip(1 - np.clip((t - 0.8) / 0.2, 0, 1) ** 2 * 0.6, 0.1, 1))
        return np.maximum((r - rad) * 0.7, np.abs(y) - 0.5)
    return SDF(f).round(0.012)


@piece("s_petal", (0.4, 0.15, 0.65), tris=260, fit=(0.62, 0.14, 1.1))
def s_petal():
    """Petal / leaf blade (long axis Z): cupped teardrop with a centre crease, pointed at both ends."""
    half = lambda t: 0.3 * np.sin(np.pi * t) ** 0.75
    return direct.blade(lambda t: -half(t), half, lambda t, u: 0.022, camber=lambda t, u: 0.12 * abs(2 * u - 1) ** 1.5 * np.sin(np.pi * t), nt=13, nu=7, axes=(2, 1, 0))


@piece("s_flame_lick", (0.35, 0.6, 0.35), tris=260, fit=(0.5, 1.0, 0.5))
def s_flame_lick():
    """Flame tongue along +Y: fat base, wavering to a point."""
    m = direct.revolve([(-0.5, 0), (-0.44, 0.15), (-0.25, 0.23), (0.0, 0.17), (0.25, 0.09), (0.5, 0)], segs=10, spline=3)

    def wave(V):
        t = np.clip(V[:, 1] + 0.5, 0, 1)
        V[:, 0] += 0.07 * np.sin(t * 5.5) * t
        V[:, 2] += 0.05 * np.sin(t * 4.0 + 1.3) * t
        return V

    return direct.deform(m, wave)


@piece("s_wing_bat", (0.6, 0.1, 0.4), tris=700, fit=(1.0, 0.06, 0.62), mirror=True)
def s_wing_bat():
    """Dragon / bat wing membrane (root -X, tip +X, leading edge -Z, thin in Y): thick leading arm, four finger
    ribs, taut skin scalloped between the rib ends."""
    ribs = [0.0, 0.3, 0.55, 0.78, 1.0]

    def scallop(t):
        for a, b in zip(ribs[:-1], ribs[1:]):
            if a <= t <= b:
                return np.sin(np.pi * (t - a) / (b - a))
        return 0.0
    lead = lambda t: -0.31 + 0.1 * t ** 2 + 0.04 * np.sin(np.pi * t)
    reach = lambda t: 0.62 * (0.62 + 0.38 * np.sin(np.pi * min(0.15 + t * 0.8, 1))) * (1 - 0.72 * t ** 2.5)
    trail = lambda t: lead(t) + max(reach(t) * (1 - 0.3 * scallop(t)), 0.012)
    rib = lambda t: sum(np.exp(-((t - r) / 0.022) ** 2) for r in ribs[1:-1])
    thick = lambda t, u: 0.004 + 0.022 * (1 - u) ** 3 * (1 - 0.6 * t) + 0.012 * rib(t) * (1 - 0.5 * u)
    return direct.blade(lead, trail, thick, camber=lambda t, u: 0.008 * np.sin(np.pi * u) * scallop(t), nt=41, nu=6)
