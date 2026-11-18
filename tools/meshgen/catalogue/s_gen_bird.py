"""Summon set: generic bird pieces (Plans/Bird.luau).

Unit pieces are authored in the lead primitive's local frame (+Y up, -Z front) in studs at the reference size the
generator gives that primitive with head / body scale 1 (`lead=`), so they keep their proportions; box pieces fill
their part's box (`fit`). Beaks run from the root at +Z (in the face) to the tip at -Z. Members named in a note are
primitives the sculpt replaces (B:sculpt in Bird.luau).
"""
import numpy as np

import direct
from sdf import *  # noqa: F401,F403
from . import piece


def _pair(fn):
    return fn().mirror_x()


def _fib(n):
    """n roughly even directions on the unit sphere."""
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = np.pi * (1 + 5 ** 0.5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.cos(phi), np.sin(th) * np.sin(phi)], 1)


def _scallops(base, amp, freq, front_only=True):
    """Rows of feather scallops across the surface (front half only by default)."""
    def f(p):
        d = base(p)
        w = np.clip(np.sin(p[:, 1] * freq + 2.5 * np.cos(p[:, 0] * freq * 0.33)), 0, 1)
        if front_only:
            w = w * np.clip(-p[:, 2] * 4 + 0.5, 0, 1)
        return d - amp * w
    return SDF(f)


# ------------------------------------------------------------------------------------------------ bodies
@piece("s_bird_body", (0.85, 0.9, 1.45), tris=1300, kind="unit", res=120, lead=(1.25, 1.35, 2.0))
def s_bird_body():
    """Bird body (lead: the Body ellipsoid, -Z = breast): full keeled breast, scapular shoulders, back sloping into
    the rump and upper tail coverts at +Z, vent, a neck stub at the front top, layered flank feathers."""
    s = ellipsoid(0.6, 0.66, 0.98)
    s = s.su(ellipsoid(0.56, 0.58, 0.6, (0, -0.1, -0.4)), 0.25)                       # breast
    s = s.su(_pair(lambda: ellipsoid(0.24, 0.2, 0.5, (0.36, 0.28, -0.12))), 0.18)     # scapulars
    s = s.su(round_cone((0, 0.05, 0.5), (0, 0.16, 1.15), 0.42, 0.15), 0.22)           # rump + tail coverts
    s = s.su(ellipsoid(0.32, 0.24, 0.36, (0, -0.32, 0.6)), 0.15)                      # vent
    s = s.su(ellipsoid(0.36, 0.38, 0.36, (0, 0.42, -0.74)), 0.22)                     # neck stub
    s = _scallops(s, 0.012, 22, front_only=False)
    return s.noise(0.01, 7, seed=3)


@piece("s_bird_fluff", (0.75, 0.75, 0.75), tris=1000, kind="unit", res=110, lead=(1.0, 1.0, 1.0))
def s_bird_fluff():
    """Fluffball (lead: any round mass of down - owl and chick bodies, ratite plumage, ruffs, pom crests, stub
    wings): a ball of soft down, shallow overlapping tufts and a few wisps round the lower rim."""
    s = sphere(0.48)
    for i, d in enumerate(_fib(60)):
        r = 0.1 + 0.015 * ((i * 7) % 3)
        s = s.su(sphere(r, d * 0.42), 0.12)
    for a in np.linspace(0, 2 * np.pi, 11, endpoint=False):
        p = np.array((np.cos(a) * 0.4, -0.16, np.sin(a) * 0.4))
        s = s.su(round_cone(p, p * 1.2 + (0, -0.1, 0), 0.07, 0.025), 0.07)
    return s.noise(0.008, 11, seed=5)


@piece("s_bird_breast", (0.7, 0.7, 0.85), tris=800, kind="unit", res=110, lead=(1.05, 1.03, 1.32))
def s_bird_breast():
    """Breast / belly patch (lead: the Breast ellipsoid): rounded, rows of scalloped feathers down the front."""
    s = ellipsoid(0.52, 0.51, 0.66)
    return _scallops(s, 0.018, 26)


# ------------------------------------------------------------------------------------------------ heads
@piece("s_head_raptor", (0.65, 0.7, 0.7), tris=1000, kind="unit", res=120)
def s_head_raptor():
    """Raptor head (lead: Head, unit sphere): heavy brow shelves over the eyes (the fierce eagle look), flat crown,
    full cheeks, swept hackles at the nape."""
    s = sphere(0.5)
    s = s.su(_pair(lambda: capsule((0.08, 0.31, -0.37), (0.36, 0.3, -0.18), 0.075)), 0.08)   # brow shelf
    s = s.su(ellipsoid(0.36, 0.12, 0.34, (0, 0.38, 0.02)), 0.12)                             # flat crown
    s = s.su(_pair(lambda: ellipsoid(0.17, 0.2, 0.22, (0.34, -0.2, 0.0))), 0.1)              # cheeks
    for (x, y) in ((0.0, 0.32), (0.18, 0.22), (0.0, 0.08), (0.28, 0.02), (0.14, -0.1)):
        s = s.su(_pair(lambda x=x, y=y: round_cone((x, y, 0.28), (x * 1.25, y - 0.1, 0.68), 0.12, 0.03)), 0.06)
    return s


@piece("s_owl_disc", (0.6, 0.55, 0.4), tris=900, kind="unit", res=120, lead=(0.99, 0.8, 0.52))
def s_owl_disc():
    """Owl facial disc (lead: FaceDisc): the dished face with a heart-shaped rim of stiff feathers, a ridge down
    the middle between the eyes to the beak. The eye zones stay on the disc ellipsoid."""
    s = ellipsoid(0.495, 0.4, 0.26)
    for th in np.linspace(0, 2 * np.pi, 30, endpoint=False):
        y = 0.38 * np.sin(th) - 0.08 * np.exp(-np.cos(th) ** 2 / 0.04) * (np.sin(th) > 0)
        x = 0.47 * np.cos(th)
        s = s.su(sphere(0.062, (x, y, -0.06)), 0.05)
    s = s.su(capsule((0, 0.26, -0.21), (0, 0.0, -0.255), 0.04), 0.04)
    return s.noise(0.006, 12, seed=2)


# ------------------------------------------------------------------------------------------------ beaks
def _gape(l, y, x):
    return _pair(lambda: capsule((x, y, l * 0.48), (0.02, y - 0.01, -l * 0.42), 0.012))


@piece("s_beak_cone", (0.3, 0.3, 0.36), tris=420, kind="unit", res=100, lead=(0.42, 0.38, 0.46))
def s_beak_cone():
    """Seed-eater cone beak (finch, sparrow, grosbeak, puffin): deep conical upper mandible over a shorter lower
    one, gape line, nostril. Members: BeakLow."""
    up = round_cone((0, 0.03, 0.2), (0, -0.03, -0.23), 0.19, 0.018).scale3(1.05, 0.95, 1)
    low = round_cone((0, -0.08, 0.17), (0, -0.09, -0.14), 0.13, 0.02)
    s = up.su(low, 0.05).ss(_gape(0.46, -0.06, 0.19), 0.015)
    return s.ss(_pair(lambda: sphere(0.025, (0.08, 0.1, 0.12))), 0.015)


@piece("s_beak_probe", (0.15, 0.15, 0.55), tris=360, kind="unit", res=100, lead=(0.2, 0.18, 0.9))
def s_beak_probe():
    """Slender probing beak (warbler, robin, hummingbird, snipe, kiwi): a needle with a gentle droop."""
    s = round_cone((0, 0.0, 0.43), (0, -0.03, -0.45), 0.095, 0.011).scale3(1.05, 0.92, 1)
    s = s.warp(lambda p: p + np.column_stack([np.zeros(len(p)), 0.04 * np.clip(-p[:, 2], 0, 1) ** 2, np.zeros(len(p))]))
    return s.ss(_gape(0.9, -0.02, 0.07), 0.01)


@piece("s_beak_curve", (0.16, 0.25, 0.75), tris=420, kind="unit", res=110, lead=(0.2, 0.2, 1.35))
def s_beak_curve():
    """Down-curved beak (ibis, curlew, sunbird, hoopoe; flamingo when deep and short)."""
    s = tube([(0, 0.02, 0.66), (0, 0.02, 0.22), (0, -0.04, -0.2), (0, -0.16, -0.52), (0, -0.28, -0.68)], [0.1, 0.08, 0.06, 0.035, 0.012], k=0.04)
    return s.ss(_pair(lambda: capsule((0.08, -0.02, 0.6), (0.02, -0.06, -0.1), 0.01)), 0.01)


@piece("s_beak_dagger", (0.2, 0.2, 0.65), tris=420, kind="unit", res=110, lead=(0.27, 0.27, 1.15))
def s_beak_dagger():
    """Dagger beak (heron, stork, kingfisher, loon, crow, pterosaur): straight and strong, a ridge along the
    culmen, gape line. Members: BeakLow."""
    s = round_cone((0, 0.0, 0.52), (0, -0.01, -0.57), 0.135, 0.012).scale3(0.92, 1, 1)
    s = s.su(capsule((0, 0.1, 0.5), (0, 0.02, -0.4), 0.03), 0.04)
    return s.ss(_gape(1.15, -0.02, 0.11), 0.012)


@piece("s_beak_parrot", (0.3, 0.42, 0.38), tris=520, kind="unit", res=110, lead=(0.44, 0.62, 0.56))
def s_beak_parrot():
    """Parrot beak: a deep upper mandible curling down over a scoop-shaped lower one, cere at the root. Members:
    BeakLow."""
    up = tube([(0, 0.17, 0.24), (0, 0.2, 0.04), (0, 0.1, -0.16), (0, -0.12, -0.27), (0, -0.29, -0.2)], [0.2, 0.19, 0.14, 0.07, 0.02], k=0.05)
    up = up.scale3(1.05, 1, 1)
    low = ellipsoid(0.17, 0.14, 0.17, (0, -0.1, 0.08)).su(ellipsoid(0.12, 0.08, 0.1, (0, -0.16, -0.02)), 0.05)
    s = up.su(low, 0.04).su(ellipsoid(0.2, 0.08, 0.08, (0, 0.25, 0.22)), 0.06)
    return s.ss(_pair(lambda: sphere(0.03, (0.08, 0.27, 0.16))), 0.015)


@piece("s_beak_duck", (0.36, 0.18, 0.52), tris=420, kind="unit", res=110, lead=(0.52, 0.22, 0.85))
def s_beak_duck():
    """Duck bill (also goose, swan, ostrich, spoonbill): flat and broad, widening a little to a rounded tip with a
    nail, nostrils near the root."""
    s = tube([(0, 0.02, 0.38), (0, 0.0, 0.0), (0, -0.01, -0.34)], [0.17, 0.15, 0.17], k=0.05).scale3(1.5, 0.55, 1)
    s = s.su(ellipsoid(0.2, 0.09, 0.1, (0, 0.04, 0.38)), 0.06)
    s = s.su(ellipsoid(0.06, 0.03, 0.05, (0, 0.03, -0.43)), 0.03)                    # nail
    s = s.ss(_pair(lambda: ellipsoid(0.02, 0.02, 0.04, (0.06, 0.06, 0.18))), 0.012)  # nostrils
    return s.ss(_pair(lambda: capsule((0.25, -0.01, 0.35), (0.25, -0.01, -0.35), 0.01)), 0.01)


@piece("s_beak_pouch", (0.3, 0.42, 1.05), tris=620, kind="unit", res=120, lead=(0.44, 0.5, 1.9))
def s_beak_pouch():
    """Pelican bill: a long flat upper bill with a hooked tip over a deep throat pouch. Members: BeakLow, Pouch."""
    bill = tube([(0, 0.17, 0.88), (0, 0.16, 0.0), (0, 0.14, -0.86)], [0.13, 0.12, 0.1], k=0.04).scale3(1.55, 0.45, 1)
    bill = bill.su(round_cone((0, 0.15, -0.86), (0, 0.06, -0.96), 0.05, 0.03), 0.04)
    pouch = ellipsoid(0.19, 0.23, 0.74, (0, -0.13, 0.1)).su(ellipsoid(0.15, 0.12, 0.3, (0, -0.28, 0.25)), 0.12)
    return bill.su(pouch, 0.06).noise(0.004, 14, seed=4)


@piece("s_beak_huge", (0.25, 0.48, 0.8), tris=620, kind="unit", res=120, lead=(0.5, 0.82, 1.45))
def s_beak_huge():
    """Huge beak (toucan, hornbill, terror bird, shoebill, dodo): a deep, narrow, curved bill with a hooked tip, a
    cutting edge and a gape groove. Members: BeakLow."""
    s = tube([(0, 0.06, 0.66), (0, 0.08, 0.2), (0, 0.0, -0.3), (0, -0.16, -0.62), (0, -0.28, -0.66)], [0.37, 0.34, 0.25, 0.1, 0.03], k=0.06)
    s = s.scale3(0.62, 1, 1)
    s = s.ss(_pair(lambda: tube([(0.2, -0.08, 0.6), (0.14, -0.1, 0.0), (0.05, -0.2, -0.5)], [0.018, 0.016, 0.012])), 0.02)
    return s.su(capsule((0, 0.38, 0.55), (0, 0.24, -0.25), 0.04), 0.05)


# ------------------------------------------------------------------------------------------------ wings, tails, crests
@piece("s_wing_folded", (0.2, 0.55, 0.95), tris=600, fit=(0.25, 0.84, 1.56), res=110, mirror=True)
def s_wing_folded():
    """Folded wing lying along the right flank (box of the Wing ellipsoid, -Z = shoulder): covert shield at the
    shoulder, a row of secondaries, long primaries crossing back to a point over the rump, outer face convex."""
    cov = ellipsoid(0.1, 0.34, 0.46, (0.02, 0.1, -0.32))
    sec = ellipsoid(0.09, 0.28, 0.5, (0.0, -0.06, 0.06))
    pri = tube([(0, -0.06, -0.05), (0, -0.12, 0.42), (0, -0.2, 0.76)], [0.24, 0.15, 0.025]).scale3(0.38, 1, 1)
    s = cov.su(sec, 0.06).su(pri, 0.06)
    # feather steps: three overlapping rows (each a shell slightly proud of the one behind)
    for i, z in enumerate((-0.1, 0.2, 0.48)):
        s = s.su(ellipsoid(0.095 - i * 0.012, 0.3 - i * 0.07, 0.2, (0.025, -0.05 - i * 0.04, z)), 0.02)
    return s.warp(lambda p: p + np.column_stack([0.12 * (p[:, 1] ** 2 + 0.3 * p[:, 2] ** 2), np.zeros(len(p)), np.zeros(len(p))]))


def _fan(n, spread, lens, w, t, root=(0, 0, -0.5), lift=0.012):
    """Fan of flat feathers from root toward +Z: angles across `spread` degrees, lens per feather."""
    s = None
    for i in range(n):
        a = np.radians(-spread / 2 + spread * i / max(n - 1, 1))
        L = lens[i]
        tip = (np.sin(a) * L + root[0], root[1] + lift * (n - abs(i - (n - 1) / 2)), np.cos(a) * L + root[2])
        f = round_cone(np.array(root) + (0, 0, 0.05), tip, w * 0.35, w)
        f = SDF(lambda p, f=f: f(p * np.array((1, w / t, 1))) * (t / w))
        s = f if s is None else s.su(f, 0.008)
    return s


@piece("s_bird_tail", (0.45, 0.12, 0.6), tris=520, fit=(0.7, 0.1, 1.0), res=120)
def s_bird_tail():
    """Fanned tail (box of the Tail ellipsoid, root at -Z): seven overlapping tail feathers with rounded tips, the
    middle pair on top. Members: the two side feathers."""
    return _fan(7, 44, [0.86, 0.9, 0.94, 0.96, 0.94, 0.9, 0.86], 0.1, 0.022)


@piece("s_bird_tail_fork", (0.45, 0.12, 0.6), tris=520, fit=(0.62, 0.1, 1.0), res=120)
def s_bird_tail_fork():
    """Forked tail (swallow, tern, frigatebird, drongo): long outer streamers, short inner feathers."""
    return _fan(6, 30, [1.0, 0.8, 0.6, 0.6, 0.8, 1.0], 0.085, 0.02)


@piece("s_bird_train", (0.6, 0.08, 0.45), tris=900, fit=(1.0, 0.058, 0.62), res=130)
def s_bird_train():
    """Upright display train (peacock, turkey, lyrebird, fantail): a half-wheel of long feathers from the root,
    each tipped with a raised eye-spot."""
    root = (0, 0, -0.2)
    s = None
    for i in range(15):
        a = np.radians(-84 + 168 * i / 14)
        L = 0.5 - 0.02 * abs(i - 7) / 7
        tip = np.array((np.sin(a) * L, 0, np.cos(a) * L - 0.2))
        f = SDF(lambda p, r=np.array(root) + (0, 0, 0.02), tip=tip: round_cone(r, tip, 0.012, 0.065)(p * np.array((1, 2.5, 1))) / 2.5)
        f = f.su(ellipsoid(0.04, 0.022, 0.04, tuple(tip * 0.94 + np.array((0, 0.012, 0)))), 0.01)
        s = f if s is None else s.su(f, 0.006)
    return s


@piece("s_crest_feather", (0.08, 0.6, 0.25), tris=220, fit=(0.1, 1.0, 0.32), res=100)
def s_crest_feather():
    """Crest / sickle feather (limb frame: root at -Y, tip at +Y): a flat vane on a quill, curving back (+Z)."""
    cone = round_cone((0, -0.45, 0.0), (0, 0.3, 0.06), 0.03, 0.13)
    vane = SDF(lambda p: cone(p * np.array((4.0, 1, 1))) / 4.0)
    s = vane.su(capsule((0, -0.5, 0.0), (0, 0.42, 0.05), 0.022), 0.01)
    return s.warp(lambda p: p - np.column_stack([np.zeros(len(p)), np.zeros(len(p)), 0.16 * (p[:, 1] + 0.5) ** 2]))


@piece("s_crest_sail", (0.08, 0.6, 0.6), tris=360, fit=(0.07, 1.0, 1.0), res=110)
def s_crest_sail():
    """Pterosaur head sail (tapejara, tupandactylus): a thin rounded sail with ribs fanning from its root."""
    s = ellipsoid(0.03, 0.48, 0.48)
    for a in np.linspace(-60, 60, 6):
        r = np.radians(a)
        s = s.su(capsule((0, -0.4, 0.0), (0, -0.4 + 0.85 * np.cos(r), 0.85 * np.sin(r) * 0.6), 0.018), 0.012)
    return s & ellipsoid(0.06, 0.5, 0.5)


# ------------------------------------------------------------------------------------------------ feet, neck
F_TIPS = [(0.436, -0.02, -0.32), (-0.436, -0.02, -0.32)]


def _foot(thick, claw, curl, web=False):
    s = tube([(0, -0.03, 0.38), (0, 0.0, 0.0), (0, -0.03, -0.44)], [0.1 * thick, 0.078 * thick, 0.05 * thick], k=0.04)
    tips = [(0, -0.03, -0.44)]
    for tip in F_TIPS:
        s = s.su(tube([(0, 0.0, 0.28), (tip[0] * 0.5, 0.0, tip[2] * 0.5 + 0.14), tip], [0.085 * thick, 0.065 * thick, 0.045 * thick], k=0.03), 0.04)
        tips.append(tip)
    s = s.su(tube([(0, 0.0, 0.3), (0, -0.04, 0.6)], [0.07 * thick, 0.042 * thick]), 0.04)        # hallux
    tips.append((0, -0.04, 0.6))
    for (x, y, z) in tips:
        d = np.array((x, 0, z)) - np.array((0, 0, 0.28))
        d = d / max(np.linalg.norm(d), 1e-6)
        a = np.array((x, y, z))
        b = a + d * claw + np.array((0, -claw * curl, 0))
        s = s.su(round_cone(a, b, 0.04 * thick, 0.006), 0.02)
    # knuckle pads
    for (x, y, z) in tips[:3]:
        s = s.su(sphere(0.06 * thick, (x * 0.55, -0.02, z * 0.55 + 0.12)), 0.03)
    if web:
        w = ellipsoid(0.44, 0.022, 0.42, (0, -0.05, -0.12))
        w = w.ss(_pair(lambda: sphere(0.2, (0.24, -0.05, -0.62))), 0.04).ss(sphere(0.24, (0, -0.05, 0.36)), 0.04)
        s = s.su(w, 0.03)
    return s


@piece("s_bird_foot", (0.55, 0.2, 0.85), tris=520, kind="unit", res=120, lead=(0.3, 0.22, 1.0))
def s_bird_foot():
    """Perching foot (lead: the centre toe; members: the side toes): three slim toes forward, hallux back, small
    claws and knuckle pads."""
    return _foot(1.0, 0.1, 0.5)


@piece("s_bird_foot_talon", (0.6, 0.3, 0.9), tris=620, kind="unit", res=120, lead=(0.3, 0.22, 1.0))
def s_bird_foot_talon():
    """Raptor foot: thick scaly toes with big hooked talons."""
    return _foot(1.3, 0.22, 1.1)


@piece("s_bird_foot_web", (0.6, 0.2, 0.85), tris=560, kind="unit", res=120, lead=(0.3, 0.22, 1.0))
def s_bird_foot_web():
    """Webbed foot (duck, goose, gull, penguin): three toes joined by a scalloped web. Members: side toes, web."""
    return _foot(1.0, 0.07, 0.4, web=True)


@piece("s_bird_neck", (0.4, 0.6, 0.4), tris=280, fit=(0.6, 1.0, 0.6))
def s_bird_neck():
    """Bird neck segment (limb frame, root at -Y): a smooth feathered column, fuller at the root."""
    return direct.revolve([(-0.5, 0), (-0.46, 0.2), (-0.32, 0.29), (-0.1, 0.27), (0.15, 0.235), (0.36, 0.2), (0.47, 0.13), (0.5, 0)], segs=12, spline=2)
