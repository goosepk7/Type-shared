"""Summon set: generic quadruped sub-kinds (Plans/Quadruped.luau): bodies, heads, armour coats and small parts for
mustelids, badgers, ant-eaters, aardvarks, armadillos / pangolins / glyptodonts, hedgehogs / porcupines, elephants,
rhinos, hippos, camelids and hopping marsupials.

Unit pieces are authored in the lead ellipsoid's unit frame (sphere of radius 0.5, -Z front):
* bodies lead the Torso; the Chest member sits at (0, 0.05, -0.384), radii (0.53, 0.56, 0.267), pitched -10 deg,
  the detail-3 Haunch at (0, 0.04, 0.35), radii (0.5, 0.51, 0.256) (Plans/Quadruped: W / H / L*0.86 layout).
* heads lead the Head; the Snout member is placed from the archetype row of Heads.Arch (cran, snout) by `_snout`,
  so nose, mouth and eyes built on the primitives sit on the sculpt for every seed.
Box pieces (trunk segments, ears, horns, humps, tails, pillar legs) fill their part's box.
"""
import numpy as np

from sdf import *  # noqa: F401,F403
import direct
from . import piece

HEAD = sphere(0.5)
TORSO = sphere(0.5)
CHEST = ellipsoid(0.53, 0.56, 0.267).rot(-10, 0, 0).at(0, 0.05, -0.384)
HAUNCH = ellipsoid(0.5, 0.51, 0.256, (0, 0.04, 0.35))


def _snout(cran, sn):
    """The Snout primitive of Heads.beast in the head's unit frame (cran / sn rows of Heads.Arch)."""
    c = (0, sn[0] / (2 * cran[1]), sn[1] / (2 * cran[2]))
    r = (sn[2] / (2 * cran[0]), sn[3] / (2 * cran[1]), sn[4] / (2 * cran[2]))
    return ellipsoid(*r).rot(-sn[5], 0, 0).at(*c), c, r


def _groove(shape, axis, at, width, depth):
    """A soft ring groove (skin fold) across the whole surface at `axis` = at."""
    return SDF(lambda p: shape(p) + depth * np.exp(-((p[:, axis] - at) / width) ** 2))


def _rings(shape, axis, lo, hi, n, depth):
    """n evenly spaced shallow grooves between lo and hi along `axis` (wrinkles, armour bands)."""
    def f(p):
        t = np.clip((p[:, axis] - lo) / (hi - lo), 0, 1)
        inside = (p[:, axis] > lo) & (p[:, axis] < hi)
        return shape(p) + depth * inside * np.clip(np.cos(t * np.pi * 2 * n), 0, 1) ** 6
    return SDF(f)


def _fur(shape, amp=0.008, freq=14, seed=0):
    return shape.noise(amp, freq, seed)


def _pair(fn):
    return fn().mirror_x()


# ------------------------------------------------------------------------------------------------------ bodies
def _base(k=0.1, haunch=True):
    s = TORSO.su(CHEST, k)
    return s.su(HAUNCH, k) if haunch else s


@piece("s_body_mustelid", (0.7, 0.75, 0.75), tris=1300, kind="unit", res=128)
def s_body_mustelid():
    """Weasel / otter / mongoose trunk: long supple tube, arched loins, sloping shoulders, slim waist."""
    s = _base(0.14)
    s = s.su(ellipsoid(0.36, 0.26, 0.34, (0, 0.24, 0.12)), 0.14)  # arched loins
    s = s.su(_pair(lambda: ellipsoid(0.16, 0.26, 0.12, (0.34, 0.12, -0.36))), 0.08)  # shoulders
    s = s.ss(ellipsoid(0.7, 0.14, 0.12, (0, -0.52, -0.02)), 0.1)  # waist tuck
    return _fur(s, 0.006, 16, 1)


@piece("s_body_badger", (0.75, 0.75, 0.75), tris=1300, kind="unit", res=128)
def s_body_badger():
    """Badger / skunk / raccoon / wolverine trunk: broad flat back, heavy shoulders, shaggy fur skirt on the flanks."""
    s = _base(0.12)
    s = s.su(ellipsoid(0.52, 0.2, 0.46, (0, 0.3, 0.02)), 0.12)  # flat broad back
    s = s.su(_pair(lambda: ellipsoid(0.2, 0.28, 0.16, (0.36, 0.14, -0.34))), 0.08)  # shoulders
    s = s.su(_pair(lambda: ellipsoid(0.14, 0.16, 0.42, (0.43, -0.2, 0.02))), 0.1)  # fur skirt
    for i, z in enumerate((-0.25, -0.08, 0.1, 0.27)):
        s = s.su(_pair(lambda z=z: round_cone((0.4, -0.18, z), (0.48, -0.4, z + 0.05), 0.08, 0.035)), 0.06)  # fringe locks
    return _fur(s, 0.01, 13, 2)


@piece("s_body_anteater", (0.7, 0.85, 0.75), tris=1300, kind="unit", res=128)
def s_body_anteater():
    """Giant anteater trunk: deep narrow body, high withers and a coarse dorsal crest of long hair."""
    s = _base(0.12)
    s = s.su(ellipsoid(0.32, 0.3, 0.26, (0, 0.22, -0.3)), 0.12)  # withers
    s = s.su(ellipsoid(0.16, 0.14, 0.44, (0, 0.42, 0.04)), 0.1)  # dorsal crest
    s = s.su(_pair(lambda: ellipsoid(0.1, 0.12, 0.4, (0.4, -0.3, 0.0))), 0.08)  # belly fringe
    return _fur(s, 0.012, 12, 3)


@piece("s_body_aardvark", (0.7, 0.8, 0.75), tris=1200, kind="unit", res=128)
def s_body_aardvark():
    """Aardvark / bilby trunk: small shoulders, strongly arched back, big rounded haunches."""
    s = TORSO.su(CHEST.at(0, -0.04, 0.03), 0.12)
    s = s.su(ellipsoid(0.55, 0.58, 0.3, (0, 0.08, 0.3)), 0.14)  # haunches
    s = s.su(ellipsoid(0.36, 0.26, 0.34, (0, 0.26, 0.12)), 0.14)  # arched back
    return _fur(s, 0.005, 14, 4)


@piece("s_body_pachy", (0.75, 0.85, 0.8), tris=1500, kind="unit", res=132)
def s_body_pachy():
    """Elephant trunk: domed high shoulders, back sloping to the rump, heavy sagging belly, skin wrinkles."""
    s = TORSO.su(ellipsoid(0.56, 0.62, 0.3, (0, 0.1, -0.33)), 0.12)
    s = s.su(ellipsoid(0.4, 0.26, 0.32, (0, 0.34, -0.22)), 0.14)  # shoulder dome
    s = s.su(ellipsoid(0.5, 0.48, 0.27, (0, -0.0, 0.33)), 0.12)  # rump
    s = s.su(ellipsoid(0.47, 0.3, 0.42, (0, -0.28, -0.02)), 0.12)  # sagging belly
    s = s.su(_pair(lambda: ellipsoid(0.16, 0.3, 0.14, (0.38, 0.0, -0.36))), 0.1)  # shoulders over the legs
    s = s.su(_pair(lambda: ellipsoid(0.17, 0.3, 0.15, (0.36, -0.02, 0.36))), 0.1)  # thighs
    s = _groove(s, 2, -0.17, 0.025, 0.012)  # skin fold behind the shoulder
    s = _groove(s, 2, 0.22, 0.025, 0.01)  # flank fold
    s = _rings(s, 2, -0.1, 0.15, 3, 0.006)  # wrinkles
    return s.noise(0.004, 22, 5)


@piece("s_body_rhino", (0.75, 0.8, 0.8), tris=1400, kind="unit", res=132)
def s_body_rhino():
    """Rhino trunk: barrel with a shoulder hump and the armour-plate skin folds at shoulder and hip."""
    s = _base(0.12)
    s = s.su(ellipsoid(0.38, 0.26, 0.3, (0, 0.3, -0.26)), 0.14)  # shoulder hump
    s = s.su(ellipsoid(0.48, 0.28, 0.4, (0, -0.24, 0.0)), 0.12)  # belly
    s = _groove(s, 2, -0.15, 0.022, 0.022)  # shoulder plate fold
    s = _groove(s, 2, 0.24, 0.022, 0.02)  # hip plate fold
    s = s.su(_pair(lambda: ellipsoid(0.08, 0.32, 0.05, (0.44, -0.05, -0.12)).rot(0, 0, 8)), 0.06)  # fold lips
    s = s.su(_pair(lambda: ellipsoid(0.08, 0.3, 0.05, (0.44, -0.05, 0.27))), 0.06)
    return s.noise(0.005, 26, 6)


@piece("s_body_hippo", (0.75, 0.8, 0.75), tris=1300, kind="unit", res=128)
def s_body_hippo():
    """Hippo trunk: round barrel, belly sagging to the ground line, thick neck fold, smooth skin."""
    s = _base(0.16)
    s = s.su(ellipsoid(0.52, 0.32, 0.42, (0, -0.24, 0.02)), 0.14)  # belly
    s = s.su(ellipsoid(0.46, 0.4, 0.16, (0, 0.04, -0.47)), 0.12)  # neck roll
    s = _groove(s, 2, -0.38, 0.02, 0.012)
    return s.noise(0.003, 18, 7)


@piece("s_body_wool", (0.8, 0.8, 0.8), tris=1500, kind="unit", res=128)
def s_body_wool():
    """Llama / alpaca fleece: the trunk wrapped in thick cauliflower wool."""
    s = _base(0.12)
    rng = np.random.default_rng(8)
    for i in range(34):
        y = 1 - 2 * (i + 0.5) / 34
        rad = np.sqrt(1 - y * y)
        a = i * 2.399963 + rng.uniform(-0.3, 0.3)
        c = np.array([np.cos(a) * rad * 0.5, y * 0.5 + 0.02, np.sin(a) * rad * 0.6 - 0.02])
        if c[1] < -0.38:
            continue
        s = s.su(sphere(0.12 * rng.uniform(0.85, 1.15), c), 0.06)
    return s


@piece("s_body_macropod", (0.7, 0.85, 0.7), tris=1200, kind="unit", res=128)
def s_body_macropod():
    """Kangaroo / wallaby trunk (upright, leaning): narrow chest on top, broad hips and belly below. Members: Chest."""
    s = TORSO.su(ellipsoid(0.41, 0.32, 0.38, (0, 0.54, 0.046)), 0.14)
    s = s.su(ellipsoid(0.55, 0.32, 0.48, (0, -0.24, 0.04)), 0.14)  # hips
    s = s.su(ellipsoid(0.3, 0.3, 0.2, (0, -0.06, -0.3)), 0.1)  # belly / pouch
    return _fur(s, 0.005, 15, 9)


# ------------------------------------------------------------------------------------------------ armour coats
@piece("s_shell_armadillo", (0.62, 0.62, 0.62), tris=1300, kind="unit", res=128)
def s_shell_armadillo():
    """Armadillo carapace (Shell ellipsoid frame): shoulder and hip shields of pebbled scutes, flexible bands
    across the middle, a flared rim along the flanks; open underneath (the body shows below)."""
    s = sphere(0.5)
    s = s.si(SDF(lambda p: -0.16 - p[:, 1]), 0.04)
    s = s.su(_pair(lambda: ellipsoid(0.07, 0.07, 0.46, (0.44, -0.13, 0))), 0.05)  # flared rim
    s = _rings(s, 2, -0.17, 0.17, 4.5, 0.03)  # bands
    # pebbled scutes on the two shields
    def peb(p):
        d = s(p)
        shield = np.abs(p[:, 2]) > 0.18
        return d - 0.008 * shield * np.cos(p[:, 0] * 60) * np.cos(p[:, 1] * 60) * np.cos(p[:, 2] * 60)
    return SDF(peb)


@piece("s_shell_glyptodon", (0.62, 0.62, 0.62), tris=1400, kind="unit", res=128)
def s_shell_glyptodon():
    """Glyptodont carapace: a high one-piece dome tiled with raised rosettes, thick rolled rim."""
    s = sphere(0.5).si(SDF(lambda p: -0.22 - p[:, 1]), 0.05)
    s = s.su(ellipsoid(0.5, 0.07, 0.5, (0, -0.19, 0)), 0.04)
    def ros(p):
        d = s(p)
        a = np.arctan2(p[:, 0], p[:, 2])
        e = np.arcsin(np.clip(p[:, 1] / 0.5, -1, 1))
        return d - 0.012 * np.clip(np.cos(a * 9) * np.cos(e * 14), 0, 1) ** 0.5
    return SDF(ros)


@piece("s_shell_pangolin", (0.62, 0.62, 0.62), tris=1500, kind="unit", res=136)
def s_shell_pangolin():
    """Pangolin scale coat (Shell frame): rows of overlapping leaf scales, each row's free edge stepped back."""
    base = sphere(0.5).si(SDF(lambda p: -0.3 - p[:, 1]), 0.05)

    def f(p):
        d = base(p)
        a = np.arctan2(p[:, 0], p[:, 1] + 0.2)
        row = p[:, 2] * 9.0
        u = row + 0.35 * np.abs(np.sin(a * 4.5 + np.floor(row) * 1.57))
        saw = u - np.floor(u)
        return d - 0.03 * saw
    return SDF(f)


def _quills(n, length, rad, sweep, seed):
    rng = np.random.default_rng(seed)
    base = sphere(0.44).si(ellipsoid(0.62, 0.5, 0.62, (0, 0.24, 0)), 0.05)
    cones = []
    for i in range(n):
        y = 1 - 1.3 * (i + 0.5) / n
        r = np.sqrt(max(0.0, 1 - y * y))
        a = i * 2.399963 + rng.uniform(-0.2, 0.2)
        d = np.array([np.cos(a) * r, y, np.sin(a) * r])
        if d[1] < -0.25:
            continue
        root = d * 0.4
        tip_dir = d + np.array([0, 0.15, sweep])
        tip_dir /= np.linalg.norm(tip_dir)
        tip = root + tip_dir * length * rng.uniform(0.85, 1.1)
        cones.append(round_cone(tuple(root), tuple(tip), rad, 0.006))
    def f(p):
        d = base(p)
        for c in cones:
            d = np.minimum(d, c(p))
        return d
    return SDF(f)


@piece("s_quills", (0.75, 0.75, 0.8), tris=1500, kind="unit", res=140)
def s_quills():
    """Hedgehog / echidna coat (Quills ellipsoid frame): a dome bristling with short spines swept back."""
    return _quills(90, 0.16, 0.035, 0.55, 10)


@piece("s_quills_long", (0.85, 0.85, 0.95), tris=1500, kind="unit", res=140)
def s_quills_long():
    """Porcupine coat: fewer, long quills raised in a crest and swept back."""
    return _quills(60, 0.3, 0.035, 0.75, 11)


# --------------------------------------------------------------------------------------------------------- heads
def _beast_head(cran, sn, k=0.13, extra=None):
    snout, c, r = _snout(cran, sn)
    s = HEAD.su(snout, k)
    if extra:
        s = extra(s, c, r)
    return s


@piece("s_head_mustelid", (0.65, 0.6, 0.85), tris=1000, kind="unit", res=120)
def s_head_mustelid():
    """Weasel / otter / mongoose head: flat wide crown, short blunt muzzle, whisker pads, cheek fur. Members: Snout."""
    def ex(s, c, r):
        s = s.su(_pair(lambda: ellipsoid(0.1, 0.09, 0.1, (0.1, c[1] - 0.02, c[2] - r[2] * 0.4))), 0.06)  # whisker pads
        s = s.su(_pair(lambda: round_cone((0.36, -0.12, 0.06), (0.5, -0.3, 0.16), 0.12, 0.04)), 0.08)  # cheek fur
        return s.ss(ellipsoid(0.6, 0.1, 0.5, (0, 0.55, 0.05)), 0.12)  # flattened crown
    return _beast_head((0.44, 0.36, 0.46), (-0.12, -0.42, 0.2, 0.16, 0.25, 4), extra=ex)


@piece("s_head_badger", (0.65, 0.6, 0.9), tris=1000, kind="unit", res=120)
def s_head_badger():
    """Badger / raccoon / devil head: wedge skull, strong jaw, ruffled cheeks. Members: Snout."""
    def ex(s, c, r):
        s = s.su(_pair(lambda: round_cone((0.36, -0.1, 0.04), (0.54, -0.3, 0.14), 0.15, 0.05)), 0.08)
        s = s.su(_pair(lambda: ellipsoid(0.16, 0.12, 0.2, (0.24, -0.34, -0.16))), 0.08)  # jaw muscles
        return s
    return _beast_head((0.47, 0.39, 0.46), (-0.15, -0.46, 0.21, 0.17, 0.3, 8), extra=ex)


@piece("s_head_spiny", (0.65, 0.65, 0.9), tris=1100, kind="unit", res=124)
def s_head_spiny():
    """Hedgehog / porcupine head: pointed face, a fringe of short spines over the crown. Members: Snout."""
    def ex(s, c, r):
        rng = np.random.default_rng(12)
        spines = []
        for i in range(16):
            a = np.radians(-80 + i * 160 / 15)
            d = np.array([np.sin(a), np.cos(a) * 0.9, 0.55])
            d /= np.linalg.norm(d)
            root = np.array([np.sin(a) * 0.38, 0.32 * np.cos(a) - 0.02, 0.18])
            spines.append(round_cone(tuple(root), tuple(root + d * 0.24 * rng.uniform(0.85, 1.1)), 0.05, 0.008))
        def f(p):
            dd = s(p)
            for q in spines:
                dd = np.minimum(dd, q(p))
            return dd
        return SDF(f)
    return _beast_head((0.42, 0.4, 0.46), (-0.13, -0.48, 0.17, 0.14, 0.3, 6), extra=ex)


@piece("s_head_macropod", (0.62, 0.6, 0.85), tris=1000, kind="unit", res=120)
def s_head_macropod():
    """Kangaroo / wallaby head: long deer-like face, soft muzzle, full cheeks. Members: Snout."""
    def ex(s, c, r):
        s = s.su(_pair(lambda: ellipsoid(0.16, 0.2, 0.22, (0.3, -0.2, -0.02))), 0.1)
        return s.su(ellipsoid(0.12, 0.08, 0.3, (0, 0.0, -0.42)).rot(-8, 0, 0), 0.08)  # nasal bridge
    return _beast_head((0.4, 0.38, 0.44), (-0.12, -0.38, 0.2, 0.17, 0.28, 6), extra=ex)


@piece("s_head_anteater", (0.55, 0.55, 2.0), tris=1100, kind="unit", res=150)
def s_head_anteater():
    """Anteater head: small skull drawn out into a long tapering tube snout, tiny mouth at the tip. Members: Snout."""
    snout, c, r = _snout((0.34, 0.34, 0.44), (-0.13, -0.92, 0.12, 0.12, 0.7, 6))
    tube_ = round_cone((0, -0.06, -0.3), (0, -0.18, -1.74), 0.3, 0.085)
    s = HEAD.su(tube_, 0.2).su(snout, 0.08)
    return s.ss(capsule((0, -0.3, -1.78), (0, -0.25, -1.5), 0.02), 0.02)


@piece("s_head_aardvark", (0.6, 0.6, 1.45), tris=1100, kind="unit", res=140)
def s_head_aardvark():
    """Aardvark / bilby head: long tubular snout ending in a blunt pig-like disc. Members: Snout."""
    def ex(s, c, r):
        tipz = c[2] - r[2] * 0.9
        s = s.su(ellipsoid(r[0] * 1.1, r[1] * 1.05, 0.08, (0, c[1] + 0.06, tipz)), 0.06)  # blunt nose disc
        return s.su(_pair(lambda: ellipsoid(0.16, 0.18, 0.22, (0.28, -0.18, -0.1))), 0.1)
    return _beast_head((0.36, 0.36, 0.44), (-0.14, -0.68, 0.16, 0.15, 0.48, 10), k=0.16, extra=ex)


@piece("s_head_armadillo", (0.6, 0.6, 1.3), tris=1100, kind="unit", res=136)
def s_head_armadillo():
    """Armadillo / pangolin head: narrow pointed face under a scaly head shield. Members: Snout."""
    def ex(s, c, r):
        cap = ellipsoid(0.3, 0.13, 0.48, (0, 0.38, -0.06)).rot(-8, 0, 0)
        s = s.su(cap, 0.04)
        return _rings(s, 2, -0.5, 0.35, 4, 0.01)
    return _beast_head((0.34, 0.34, 0.44), (-0.13, -0.6, 0.15, 0.13, 0.42, 10), extra=ex)


@piece("s_head_pachy", (0.7, 0.7, 0.7), tris=1200, kind="unit", res=124)
def s_head_pachy():
    """Elephant head: high domed forehead, temple hollows, heavy trunk root flowing down the face, lower lip,
    cheek bulges (the trunk segments and ear flaps are separate parts)."""
    s = HEAD.su(ellipsoid(0.36, 0.24, 0.3, (0, 0.34, -0.1)), 0.14)  # dome
    s = s.su(ellipsoid(0.22, 0.28, 0.16, (0, -0.16, -0.38)), 0.12)  # trunk root
    s = s.su(ellipsoid(0.12, 0.08, 0.12, (0, -0.42, -0.22)), 0.06)  # lower lip
    s = s.su(_pair(lambda: ellipsoid(0.18, 0.22, 0.2, (0.3, -0.24, -0.08))), 0.1)  # cheeks
    s = s.ss(_pair(lambda: sphere(0.09, (0.46, 0.12, -0.1))), 0.08)  # temples
    s = _rings(s, 1, -0.45, -0.1, 3, 0.006)
    return s.noise(0.003, 22, 13)


@piece("s_head_rhino", (0.65, 0.65, 1.3), tris=1200, kind="unit", res=136)
def s_head_rhino():
    """Rhino head: long sloping skull, horn bosses on the nose, broad square lips, heavy jowls. Members: Snout."""
    def ex(s, c, r):
        s = s.su(ellipsoid(0.17, 0.08, 0.16, (0, -0.03, -0.85)), 0.06)  # front horn boss
        s = s.su(ellipsoid(0.14, 0.07, 0.13, (0, 0.0, -0.6)), 0.06)  # rear horn boss
        s = s.su(ellipsoid(0.3, 0.2, 0.14, (0, c[1] - r[1] * 0.45, c[2] - r[2] * 0.72)), 0.08)  # square lips
        s = s.su(_pair(lambda: ellipsoid(0.2, 0.26, 0.28, (0.3, -0.26, -0.18))), 0.12)  # jowls
        return _groove(s, 2, -0.15, 0.02, 0.012).noise(0.004, 24, 14)
    return _beast_head((0.4, 0.38, 0.46), (-0.24, -0.56, 0.28, 0.27, 0.46, 16), k=0.15, extra=ex)


@piece("s_head_hippo", (0.75, 0.65, 1.1), tris=1200, kind="unit", res=132)
def s_head_hippo():
    """Hippo head: huge broad muzzle with nostril knobs on top, flared lips and jowls, brow knobs behind the eyes.
    Members: Snout."""
    def ex(s, c, r):
        s = s.su(_pair(lambda: sphere(0.09, (0.17, c[1] + r[1] * 0.82, c[2] - r[2] * 0.5))), 0.06)  # nostril knobs
        s = s.su(_pair(lambda: ellipsoid(0.24, 0.24, 0.3, (0.32, c[1] - r[1] * 0.3, c[2] + 0.02))), 0.12)  # jowls
        s = s.su(_pair(lambda: sphere(0.1, (0.24, 0.36, 0.12))), 0.08)  # brow knobs behind the eyes
        return s.ss(_pair(lambda: capsule((0.08, c[1] - r[1] * 0.35, c[2] - r[2] * 0.98), (0.5, c[1] - r[1] * 0.4, c[2] - r[2] * 0.1), 0.02)), 0.02)  # lip line
    return _beast_head((0.46, 0.4, 0.44), (-0.2, -0.5, 0.44, 0.32, 0.36, 0), k=0.15, extra=ex)


@piece("s_head_camelid", (0.62, 0.65, 1.0), tris=1000, kind="unit", res=124)
def s_head_camelid():
    """Camel / llama head: long face, drooping split upper lip, heavy-lidded brow, rounded jaw. Members: Snout."""
    def ex(s, c, r):
        s = s.su(ellipsoid(r[0] * 0.9, r[1] * 0.5, r[2] * 0.5, (0, c[1] - r[1] * 0.4, c[2] - r[2] * 0.62)), 0.06)  # droopy lip
        s = s.ss(capsule((0, c[1] - r[1] * 0.1, c[2] - r[2] * 1.1), (0, c[1] - r[1] * 0.75, c[2] - r[2] * 1.0), 0.025), 0.02)  # split lip
        s = s.su(_pair(lambda: ellipsoid(0.12, 0.22, 0.2, (0.26, -0.3, 0.02))), 0.1)  # jaw
        return s
    return _beast_head((0.36, 0.36, 0.42), (-0.2, -0.42, 0.2, 0.21, 0.32, 14), k=0.15, extra=ex)


# ------------------------------------------------------------------------------------------------- small parts
@piece("s_trunk_seg", (0.3, 0.6, 0.3), tris=320, fit=(0.5, 1.0, 0.5))
def s_trunk_seg():
    """Elephant trunk segment (+Y = toward the tip): tapering tube ringed with skin wrinkles."""
    pts = [(-0.5, 0)]
    n = 9
    for i in range(n + 1):
        t = -0.46 + 0.92 * i / n
        base = 0.245 - 0.06 * (t + 0.5)
        pts.append((t, base - (0.018 if i % 2 else 0)))
    pts.append((0.5, 0))
    return direct.revolve(pts, segs=12, spline=1)


@piece("s_ear_elephant", (0.12, 0.7, 0.62), tris=500, fit=(0.14, 1.15, 0.95), res=110)
def s_ear_elephant():
    """Elephant ear flap (thin in X): broad upper lobe tapering to a hanging point, rolled rim, veined cup."""
    s = ellipsoid(0.055, 0.42, 0.46, (0, 0.13, 0.0))
    s = s.su(ellipsoid(0.05, 0.3, 0.24, (0, -0.25, 0.1)), 0.12)  # hanging lower lobe
    s = s.su(ellipsoid(0.06, 0.08, 0.36, (0, 0.5, 0.0)), 0.06)  # rolled top rim
    s = s.ss(ellipsoid(0.03, 0.3, 0.33, (0.05, 0.1, -0.02)), 0.03)  # cup (outer face)
    return s


@piece("s_rhino_horn", (0.3, 0.6, 0.3), tris=300, fit=(0.42, 1.0, 0.42))
def s_rhino_horn():
    """Rhino horn (+Y = tip): broad fibrous base, curving back to a blunt point."""
    s = round_cone((0, -0.42, 0), (0, 0.3, 0.06), 0.2, 0.04).bend(0.25, axis=1, toward=2)
    return _rings(s, 1, -0.4, 0.0, 3, 0.008)


@piece("s_hump", (0.6, 0.6, 0.6), tris=500, fit=(1.0, 1.0, 1.0), res=100)
def s_hump():
    """Camel hump: a firm mound, peaked a little forward, with a shaggy top."""
    s = ellipsoid(0.5, 0.5, 0.5).su(ellipsoid(0.3, 0.2, 0.28, (0, 0.28, -0.06)), 0.12)
    return s.noise(0.012, 14, 15)


@piece("s_tail_pangolin", (0.3, 0.6, 0.3), tris=500, fit=(0.5, 1.0, 0.5), res=110)
def s_tail_pangolin():
    """Pangolin tail segment (+Y = tip): flattened, covered in rows of overlapping scales with stepped edges."""
    base = ellipsoid(0.24, 0.5, 0.2)

    def f(p):
        d = base(p)
        u = (0.5 - p[:, 1]) * 6 + 0.3 * np.abs(np.sin(p[:, 0] * 14))
        return d - 0.025 * (u - np.floor(u))
    return SDF(f)


@piece("s_tail_banded", (0.3, 0.6, 0.3), tris=320, fit=(0.5, 1.0, 0.5))
def s_tail_banded():
    """Armoured tail segment (+Y = tip): tapering cone of bony rings."""
    pts = [(-0.5, 0)]
    n = 10
    for i in range(n + 1):
        t = -0.46 + 0.92 * i / n
        base = 0.24 - 0.1 * (t + 0.5)
        pts.append((t, base + (0.02 if i % 2 else 0)))
    pts.append((0.5, 0))
    return direct.revolve(pts, segs=12, spline=1)


@piece("s_leg_pillar", (0.3, 0.6, 0.3), tris=420, fit=(0.42, 1.0, 0.42), res=110)
def s_leg_pillar():
    """Pillar leg in one piece (+Y = foot): heavy upper leg, straight column, round foot pad with toenails at front."""
    s = round_cone((0, -0.4, 0), (0, 0.38, 0), 0.2, 0.17)
    s = s.su(ellipsoid(0.2, 0.08, 0.2, (0, 0.42, 0)), 0.05)  # foot pad
    for x in (-0.09, 0.0, 0.09):
        s = s.su(ellipsoid(0.045, 0.04, 0.03, (x, 0.42, -0.19)), 0.015)  # toenails
    return _rings(s, 1, 0.0, 0.3, 3, 0.005)
