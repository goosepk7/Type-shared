"""Summon set: arthropod sculpts (Plans/Insect, Plans/Arachnid, Plans/Crustacean via Plans/Arthro).

Unit pieces authored in studs in the local frame of their lead primitive (`lead=`), at the reference sizes the
Luau builders use, so proportions survive the per-axis fit:

* Leg pieces stand in for ONE straight ellipsoid from hip to foot (Arthro.segFrame: local +Y hip -> foot, local +Z
  rolled to world up, local X = Y x Z). A whole leg (`s_arthro_leg` ...) bends up into a knee above that line; a
  comb (`s_bug_legs3`, `s_arachnid_legs4`, `s_crab_legs4`, `s_bug_legs2`, + `_l` twins) carries every leg of one
  side. They are modelled in a reference "world" (+X out, +Y up, -Z front) and moved into the primitive's frame.
  The lead width is length x Arthro.LEG_RATIO (0.085) x the builder's `thick`, so the knee height of a sculpt
  scales with the leg's width: each piece is authored at the `thick` its callers use.
* Body, head, shell and claw pieces are authored around the lead ellipsoid (size = lead, centred at 0).
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from . import piece

RATIO = 0.085


# ------------------------------------------------------------------------------------------------ frames
def seg_frame(a, b, up=(0, 1, 0)):
    """Arthro.segFrame: centre, R (columns = local X, Y, Z in world), length."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    y = (b - a) / np.linalg.norm(b - a)
    u = np.asarray(up, float)
    z = u - (u @ y) * y
    z /= np.linalg.norm(z)
    x = np.cross(y, z)
    return (a + b) / 2, np.column_stack([x, y, z]), float(np.linalg.norm(b - a))


def to_local(shape, C, R):
    """World-space SDF -> SDF in the local frame (C, R)."""
    return SDF(lambda q: shape(q @ R.T + C))


def local_pts(pts, C, R):
    return (np.asarray(pts, float) - C) @ R


def region_of(pts, pad):
    m = np.abs(np.asarray(pts, float)).max(0) + pad
    return tuple(float(v) for v in m)


# ------------------------------------------------------------------------------------------------ legs
def leg_joints(H, F, rise, out=0.38, ankle=0.55, kick=0.1):
    """Hip, knee, ankle, foot of a jointed leg from H to F with the knee `rise` x length above the higher end."""
    H, F = np.asarray(H, float), np.asarray(F, float)
    L = np.linalg.norm(F - H)
    K = H + (F - H) * out
    K[1] = max(H[1], F[1]) + rise * L
    A = K + (F - K) * ankle
    hor = F - H
    hor[1] = 0
    n = np.linalg.norm(hor)
    if n > 1e-6:
        A = A + hor / n * kick * L
    return H, K, A, F, L


def leg_sdf(H, K, A, F, r, flat=1.0, spines=0, hair=0.0, claw=True, seed=0):
    """A jointed leg: coxa, femur to the knee, patella, tibia, metatarsus tapering to a clawed tip."""
    s = sphere(r * 1.15, H)
    s = s.su(round_cone(H, K, r * 1.0, r * 0.82), r * 0.45)
    s = s.su(sphere(r * 0.92, K), r * 0.35)
    s = s.su(round_cone(K, A, r * 0.8, r * 0.58), r * 0.3)
    s = s.su(sphere(r * 0.6, A), r * 0.2)
    s = s.su(round_cone(A, F, r * 0.55, r * 0.22), r * 0.25)
    if claw:
        d = F - A
        d = d / np.linalg.norm(d)
        s = s.su(round_cone(F - d * r * 0.4, F + d * r * 0.8 + np.array([0, -r * 0.2, 0]), r * 0.2, r * 0.05), r * 0.1)
    if spines:
        rng = np.random.default_rng(seed)
        for i in range(spines):
            t = (i + 0.5) / spines
            seg = (K, A) if t < 0.6 else (A, F)
            u = (t / 0.6) if t < 0.6 else ((t - 0.6) / 0.4)
            p = seg[0] + (seg[1] - seg[0]) * u
            d = seg[1] - seg[0]
            d = d / np.linalg.norm(d)
            side = np.cross(d, np.array([0, 1.0, 0]))
            if np.linalg.norm(side) < 1e-6:
                side = np.array([1.0, 0, 0])
            side /= np.linalg.norm(side)
            sgn = 1 if i % 2 == 0 else -1
            tip = p + side * sgn * r * 1.6 + d * r * 1.2 + np.array([0, -r * 0.4, 0]) * rng.uniform(0.5, 1)
            s = s.su(round_cone(p, tip, r * 0.22, r * 0.04), r * 0.08)
    if hair > 0:
        s = s.noise(hair, freq=1.0 / max(r, 1e-3) * 1.6, seed=seed)
    return s


def flatten(shape, C, R, k):
    """Squash a world-space shape across the leg (local X) by k: crab legs are blades, not tubes."""
    def f(p):
        q = (p - C) @ R
        q[:, 0] /= k
        return shape(q @ R.T + C) * k
    return SDF(f)


def leg_piece(pid, legs, prim, thick, rise, note, tris=400, mirror=False, flat=None, spines=0, hair=0.0, out=0.38, kick=0.1, res=130, rscale=1.0, radius=None):
    """Register a leg sculpt. legs: [(hip, foot)] in the reference world; prim: (hip, foot) of the primitive."""
    C, R, plen = seg_frame(prim[0], prim[1])
    w = plen * RATIO * thick
    lead = (w, plen * 1.06, w)
    joints = []
    for (h, f) in legs:
        joints.append(leg_joints(h, f, rise, out=out, kick=kick))
    r = (radius if radius is not None else w * 0.5) * rscale
    pts = []
    for (H, K, A, F, L) in joints:
        pts += [H, K, A, F]
    reg = region_of(local_pts(pts, C, R), r * 3.2)

    @piece(pid, reg, tris=tris, kind="unit", lead=lead, mirror=mirror, res=res, smooth=3, note=note)
    def build():
        s = None
        for i, (H, K, A, F, L) in enumerate(joints):
            leg = leg_sdf(H, K, A, F, r, spines=spines, hair=hair, seed=i)
            if flat:
                Ci, Ri, _ = seg_frame(H, F)
                leg = flatten(leg, Ci, Ri, flat)
            s = leg if s is None else (s | leg)
        return to_local(s, C, R)

    return build


# single legs: canonical hip / foot, the knee above
_H, _F = (0.0, 1.0, 0.0), (1.85, 0.04, 0.0)
leg_piece("s_arthro_leg", [(_H, _F)], (_H, _F), 1.0, 0.36,
          "Arthropod leg, whole (lead: the straight hip-foot ellipsoid, local +Z up): coxa, femur rising to a high knee, tibia, metatarsus and a clawed tip.")
leg_piece("s_arthro_leg_hairy", [(_H, _F)], (_H, _F), 1.35, 0.3,
          "Hairy arthropod leg (tarantula, wolf spider, jumping spider): stout segments with a bristly surface.", hair=0.012, tris=700, res=150)
leg_piece("s_arthro_leg_spiny", [(_H, _F)], (_H, _F), 1.0, 0.3,
          "Spiny insect leg (cockroach, water bug): tibia and tarsus lined with spines.", spines=6, tris=520, res=150)
leg_piece("s_arthro_leg_long", [((0, 1, 0), (1.7, 0.0, 0))], ((0, 1, 0), (1.7, 0.0, 0)), 0.65, 0.62,
          "Stilt leg (harvestman, cellar spider, crane fly, stick insect): thin, the knee far above the body.", out=0.36, kick=0.06)
leg_piece("s_crab_leg", [(_H, _F)], (_H, _F), 1.15, 0.36,
          "Crab walking leg: flattened segments, a pointed dactyl.", flat=0.62, tris=420)
leg_piece("s_crab_leg_hairy", [(_H, _F)], (_H, _F), 1.35, 0.34,
          "Hairy crab leg (yeti crab): flattened segments in a shaggy coat.", flat=0.7, hair=0.02, tris=700, res=150)
leg_piece("s_finger_leg", [(_H, _F)], (_H, _F), 1.0, 0.3,
          "Bony finger-like leg (face grabber): knuckled segments.", tris=420)
leg_piece("s_mech_leg", [(_H, _F)], (_H, _F), 1.6, 0.34,
          "Mech walker leg (spider tank): thick armoured segments with joint collars, a flat foot pad.", spines=0, tris=460, res=120)

# combs ----------------------------------------------------------------------------------------------------
# insect (beetle reference: Insect.Beetle sixLegs at detail 0)
_bh = [(0.42, 0.64, -0.198), (0.42, 0.64, 0.27), (0.42, 0.64, 0.558)]
_bf = [(1.754, 0.04, -1.2275), (2.0035, 0.04, 0.36), (1.816, 0.04, 1.775)]
leg_piece("s_bug_legs3", list(zip(_bh, _bf)), (_bh[1], _bf[1]), 1.1, 0.3,
          "Insect legs, one side (detail 0; lead: the middle leg): front leg reaching forward, middle out, hind back, each with a knee.",
          tris=900, mirror=True)
# mantis walking legs (two a side)
leg_piece("s_bug_legs2", [((0.2, 0.93, 0.05), (1.45, 0.04, -0.6)), ((0.22, 0.93, 0.3), (1.55, 0.04, 1.6))], ((0.2, 0.93, 0.05), (1.55, 0.04, 0.5)), 0.8, 0.32,
          "Mantis walking legs, one side (detail 0; lead: a mid leg): two long legs, knees high.", tris=600, mirror=True)


def _fan(hipx, hipy, zs, angles, R):
    out = []
    for z, a in zip(zs, angles):
        a = np.radians(a)
        out.append(((hipx, hipy, z), (hipx + R * np.cos(a), 0.04, z - R * np.sin(a))))
    return out


_sl = _fan(0.418, 1.06, (-0.375, -0.125, 0.125, 0.375), (52, 18, -14, -46), 2.5)
leg_piece("s_arachnid_legs4", _sl, ((0.418, 1.06, -0.125), (0.418 + 2.5 * np.cos(np.radians(30)), 0.04, -0.125 - 2.5 * np.sin(np.radians(8)))), 1.0, 0.42,
          "Spider legs, one side (detail 0; lead: a reference leg): four legs fanned from front to back, knees high above the body.",
          tris=1100, mirror=True)
_cl = _fan(0.9, 0.844, (-0.333, -0.012, 0.308, 0.629), (28, 8, -12, -32), 1.85)
leg_piece("s_crab_legs4", _cl, ((0.9, 0.844, 0.148), (0.9 + 1.85 * 0.95, 0.04, 0.148)), 1.265, 0.38,
          "Crab legs, one side (detail 0; lead: a reference leg): four flattened walking legs spread sideways.", tris=1100, mirror=True, flat=0.62)


# ------------------------------------------------------------------------------------------------ segments
@piece("s_arthro_seg", (0.2, 0.62, 0.2), tris=360, kind="unit", lead=(0.25, 1.0, 0.25), res=110)
def s_arthro_seg():
    """Arthropod limb / tail segment (lead 0.25 x 1.0 x 0.25, +Y root -> tip): a hard tapered tube with a joint collar at
    the root and a rim at the tip."""
    s = round_cone((0, -0.4, 0), (0, 0.42, 0), 0.125, 0.1)
    s = s.su(torus(0.11, 0.025).at(0, -0.36, 0), 0.03)
    s = s.ss(torus(0.105, 0.012).at(0, 0.3, 0), 0.012)
    return s


@piece("s_arthro_tibia", (0.12, 0.6, 0.12), tris=320, kind="unit", lead=(0.14, 1.0, 0.14), res=110)
def s_arthro_tibia():
    """Arthropod lower leg (lead 0.14 x 1.0 x 0.14, +Y root -> tip): tapering to a clawed tarsus."""
    s = round_cone((0, -0.44, 0), (0, 0.3, 0), 0.07, 0.04)
    s = s.su(round_cone((0, 0.3, 0), (0, 0.5, 0.02), 0.035, 0.01), 0.02)
    s = s.ss(torus(0.065, 0.008).at(0, -0.1, 0), 0.008)
    return s


# ------------------------------------------------------------------------------------------------ insect bodies
@piece("s_bug_thorax", (0.6, 0.6, 0.6), tris=800, kind="unit", res=120)
def s_bug_thorax():
    """Insect thorax (unit frame): a pronotum collar at the front, the meso / metathorax plates, leg sockets underneath."""
    s = ellipsoid(0.5, 0.5, 0.5)
    s = s.su(ellipsoid(0.47, 0.22, 0.2, (0, 0.18, -0.3)), 0.08)          # pronotum collar
    s = s.ss(torus(0.44, 0.025).rot(90, 0, 0).at(0, 0.02, -0.12), 0.03)  # plate seam
    s = s.ss(torus(0.42, 0.02).rot(90, 0, 0).at(0, 0.0, 0.16), 0.02)
    for z in (-0.22, 0.02, 0.22):                                         # coxae sockets
        s = s.su(sphere(0.1, (0.22, -0.4, z)).mirror_x(), 0.06)
    return s


@piece("s_bug_abdomen", (0.6, 0.6, 0.62), tris=900, kind="unit", res=120)
def s_bug_abdomen():
    """Insect abdomen (unit frame, rear +Z): overlapping tergite rings tapering to a rounded tip."""
    s = ellipsoid(0.5, 0.5, 0.5).su(round_cone((0, -0.02, 0.15), (0, -0.04, 0.52), 0.28, 0.07), 0.12)
    for i, z in enumerate((-0.28, -0.1, 0.08, 0.25)):
        rr = 0.5 * np.sqrt(max(0.02, 1 - (z / 0.5) ** 2))
        s = s.su(torus(rr * 0.97, 0.03, axis=2).at(0, 0, z), 0.04)
    return s


@piece("s_beetle_pronotum", (0.82, 0.5, 0.56), tris=900, kind="unit", lead=(1.4, 0.82, 0.9), res=130)
def s_beetle_pronotum():
    """Beetle pronotum (lead: Thorax 1.4 x 0.82 x 0.9): a domed shield with raised side margins, a notch at the front
    where the head sits and a lobe over the elytra at the back."""
    s = ellipsoid(0.7, 0.41, 0.45)
    s = s.su(ellipsoid(0.72, 0.12, 0.44, (0, -0.05, 0.02)), 0.08)               # flared margin
    s = s.ss(ellipsoid(0.28, 0.22, 0.2, (0, 0.05, -0.47)), 0.1)                  # head notch
    s = s.su(ellipsoid(0.36, 0.2, 0.18, (0, 0.18, 0.32)), 0.12)                   # rear lobe
    s = s.ss(capsule((0, 0.42, -0.3), (0, 0.42, 0.3), 0.025), 0.03)              # mid-line groove
    return s


@piece("s_beetle_elytra", (1.0, 0.7, 1.15), tris=1400, kind="unit", lead=(1.7, 1.15, 2.0), res=140)
def s_beetle_elytra():
    """Beetle elytra (lead: Abdomen 1.7 x 1.15 x 2.0): two hard wing cases meeting at a sutural seam, longitudinal
    striae, a scutellum triangle at the front and a lip round the lower edge."""
    s = ellipsoid(0.85, 0.575, 1.0)
    s = s.su(ellipsoid(0.88, 0.14, 0.98, (0, -0.12, 0.0)), 0.06)                 # epipleural lip
    s = s.ss(capsule((0, 0.6, -0.9), (0, 0.6, 0.95), 0.03), 0.025)                # suture
    for x in (0.22, 0.42, 0.6):                                                  # striae
        y = 0.575 * np.sqrt(max(0.05, 1 - (x / 0.85) ** 2))
        s = s.ss(capsule((x, y + 0.02, -0.6), (x, y - 0.05, 0.7), 0.014).mirror_x(), 0.018)
    s = s.su(ellipsoid(0.16, 0.06, 0.18, (0, 0.53, -0.82)), 0.05)                 # scutellum
    return s


@piece("s_beetle_dome", (1.08, 0.82, 1.0), tris=1300, kind="unit", lead=(1.95, 1.45, 1.85), res=140)
def s_beetle_dome():
    """Ladybug / tortoise-beetle dome (lead: Abdomen 1.95 x 1.45 x 1.85): a near-hemispherical shell split by the
    sutural seam, with a rolled rim."""
    s = ellipsoid(0.975, 0.725, 0.925)
    s = s.su(torus(0.9, 0.06).scale3(1.0, 1.0, 0.95).at(0, -0.2, 0), 0.08)
    s = s.ss(capsule((0, 0.75, -0.85), (0, 0.75, 0.9), 0.035), 0.03)
    return s


@piece("s_bug_head_jaw", (0.65, 0.62, 0.72), tris=850, kind="unit", res=120)
def s_bug_head_jaw():
    """Chewing insect head (unit frame, -Z face): smooth capsule, clypeus and labrum, mandible bases, antennal sockets."""
    s = sphere(0.5)
    s = s.su(ellipsoid(0.26, 0.12, 0.12, (0, -0.22, -0.42)), 0.06)                # clypeus
    s = s.su(ellipsoid(0.18, 0.07, 0.08, (0, -0.34, -0.47)), 0.04)                # labrum
    s = s.su(sphere(0.12, (0.2, -0.3, -0.36)).mirror_x(), 0.06)                   # mandible bases
    s = s.su(torus(0.06, 0.03).rot(80, 0, 0).at(0.2, 0.3, -0.38).mirror_x(), 0.03)  # antennal sockets
    s = s.su(torus(0.33, 0.06, axis=2).at(0, 0, 0.36), 0.06)                       # neck collar
    return s


def _jaw(L, w, curve, teeth, tine=False):
    """A curved jaw in a limb frame (studs; root at -L/2, tip at +L/2), bowing out (+X) and hooking in (-X)."""
    h = L / 2
    pts = [(0.0, -h * 0.92, 0), (0.25 * curve * w, -h * 0.4, 0.0), (0.33 * curve * w, h * 0.2, 0.0), (0.1 * curve * w, h * 0.66, 0.0), (-0.4 * curve * w, h * 0.95, 0.0)]
    rad = [w * 0.48, w * 0.42, w * 0.34, w * 0.24, w * 0.08]
    s = tube(pts, rad, k=w * 0.1)
    for i in range(teeth):
        y = -h * 0.35 + i * h * 1.1 / max(teeth, 1)
        x = 0.28 * curve * w - w * 0.3
        s = s.su(round_cone((x + w * 0.1, y, 0), (x - w * 0.22, y + w * 0.05, 0), w * 0.11, w * 0.03), w * 0.04)
    if tine:
        s = s.su(round_cone((0.3 * curve * w, h * 0.05, 0.0), (0.1 * curve * w, h * 0.3, w * 0.45), w * 0.15, w * 0.05), w * 0.06)
    return s


@piece("s_bug_mandible", (0.3, 0.62, 0.2), tris=360, kind="unit", lead=(0.32, 1.08, 0.224), mirror=True, res=110)
def s_bug_mandible():
    """Insect mandible (lead 0.32 x 1.08 x 0.22, root -Y, local X outward; left twin mirrored): a curved pincer hooking
    inward with a toothed inner edge."""
    return _jaw(1.08, 0.32, 1.0, 3).scale3(1, 1, 0.7)


@piece("s_stag_jaw", (0.3, 0.82, 0.25), tris=480, kind="unit", lead=(0.28, 1.5, 0.2), mirror=True, res=120)
def s_stag_jaw():
    """Stag beetle jaw (lead 0.28 x 1.5 x 0.2, root -Y, local X outward; left twin mirrored): a long antler-like
    mandible bowing out and hooking in, an inner tine rising from it, a row of teeth."""
    return _jaw(1.5, 0.28, 1.4, 4, tine=True)


@piece("s_beetle_horn", (0.25, 0.75, 0.42), tris=420, kind="unit", lead=(0.32, 1.35, 0.32), res=120)
def s_beetle_horn():
    """Rhinoceros beetle head horn (lead 0.32 x 1.35 x 0.32, local +Z rolled to the back): stout at the root, curving
    back, a forked tip."""
    pts = [(0, -0.62, -0.05), (0, -0.2, -0.04), (0, 0.2, 0.04), (0, 0.48, 0.2), (0, 0.6, 0.38)]
    s = tube(pts, [0.16, 0.13, 0.095, 0.06, 0.025], k=0.03)
    s = s.su(round_cone((0, 0.5, 0.22), (0.07, 0.66, 0.32), 0.04, 0.015).mirror_x(), 0.02)
    return s


@piece("s_beetle_horn_long", (0.22, 1.12, 0.45), tris=480, kind="unit", lead=(0.3, 2.1, 0.3), res=120)
def s_beetle_horn_long():
    """Hercules beetle thoracic horn (lead 0.3 x 2.1 x 0.3, local +Z rolled down): a long arch with a bristly underside and
    an inner tooth, bending down at the tip."""
    pts = [(0, -1.0, -0.02), (0, -0.4, -0.02), (0, 0.2, 0.02), (0, 0.7, 0.14), (0, 1.0, 0.36)]
    s = tube(pts, [0.15, 0.12, 0.095, 0.065, 0.03], k=0.03)
    s = s.su(round_cone((0, 0.0, 0.08), (0, 0.08, 0.28), 0.04, 0.012), 0.02)
    return s.noise(0.004, freq=60, seed=3)


@piece("s_fly_thorax", (0.62, 0.6, 0.6), tris=800, kind="unit", res=120)
def s_fly_thorax():
    """Fly / bee thorax (unit frame): a domed scutum with a scutellum lip at the back, wing bases, leg sockets."""
    s = ellipsoid(0.5, 0.5, 0.5)
    s = s.su(ellipsoid(0.28, 0.12, 0.14, (0, 0.28, 0.38)), 0.06)                  # scutellum
    s = s.su(sphere(0.09, (0.42, 0.22, -0.02)).mirror_x(), 0.06)                  # wing bases
    s = s.ss(capsule((0.12, 0.49, -0.3), (0.12, 0.42, 0.3), 0.018).mirror_x(), 0.02)  # scutum lines
    for z in (-0.18, 0.04, 0.24):
        s = s.su(sphere(0.09, (0.2, -0.41, z)).mirror_x(), 0.05)
    return s


@piece("s_fly_thorax_fuzz", (0.64, 0.62, 0.62), tris=1100, kind="unit", res=140)
def s_fly_thorax_fuzz():
    """Fuzzy thorax (bee, bumblebee, moth, butterfly; unit frame): the fly thorax in a coat of pile."""
    return s_fly_thorax().noise(0.02, freq=26, seed=7)


@piece("s_fly_head", (0.66, 0.62, 0.66), tris=800, kind="unit", res=120)
def s_fly_head():
    """Fly / dragonfly head (unit frame, -Z face): a broad head with a face plate, three ocelli on the crown and a sponging
    mouth below."""
    s = ellipsoid(0.5, 0.48, 0.5)
    s = s.su(ellipsoid(0.22, 0.24, 0.1, (0, -0.08, -0.44)), 0.08)                 # face plate
    s = s.su(round_cone((0, -0.32, -0.3), (0, -0.52, -0.36), 0.1, 0.07), 0.06)    # proboscis base
    for x, z in ((0, -0.12), (0.09, 0.02), (-0.09, 0.02)):
        s = s.su(sphere(0.045, (x, 0.47, z)), 0.02)                              # ocelli
    return s


@piece("s_bee_abdomen", (0.62, 0.6, 0.62), tris=1000, kind="unit", res=130)
def s_bee_abdomen():
    """Bee abdomen (unit frame, rear +Z): plump, banded segments under a light pile, a tapered tip."""
    s = ellipsoid(0.5, 0.5, 0.5).su(round_cone((0, -0.04, 0.2), (0, -0.08, 0.52), 0.26, 0.05), 0.12)
    for z in (-0.22, 0.0, 0.2):
        rr = 0.5 * np.sqrt(max(0.02, 1 - (z / 0.5) ** 2))
        s = s.ss(torus(rr, 0.022, axis=2).at(0, 0, z), 0.02)
    return s.noise(0.012, freq=30, seed=2)


@piece("s_ant_gaster", (0.62, 0.6, 0.62), tris=900, kind="unit", res=120)
def s_ant_gaster():
    """Ant gaster (unit frame, rear +Z): a glossy oval with four overlapping tergites and a pointed tip."""
    s = ellipsoid(0.5, 0.48, 0.5).su(round_cone((0, -0.05, 0.25), (0, -0.1, 0.52), 0.2, 0.04), 0.1)
    for z in (-0.18, 0.04, 0.24):
        rr = 0.49 * np.sqrt(max(0.02, 1 - (z / 0.5) ** 2))
        s = s.su(torus(rr, 0.03, axis=2).at(0, 0.01, z - 0.02), 0.03)
        s = s.ss(torus(rr, 0.02, axis=2).at(0, 0.01, z + 0.03), 0.02)
    return s


@piece("s_ant_thorax", (0.62, 0.6, 0.62), tris=800, kind="unit", res=120)
def s_ant_thorax():
    """Ant mesosoma (unit frame, -Z front): a slim waisted trunk, the pronotum hump at the front, propodeum bumps at the
    back."""
    s = ellipsoid(0.42, 0.42, 0.5)
    s = s.su(ellipsoid(0.48, 0.48, 0.24, (0, 0.04, -0.28)), 0.12)                 # pronotum
    s = s.ss(ellipsoid(0.6, 0.12, 0.1, (0, 0.46, 0.02)), 0.06)                    # waist dip
    s = s.su(sphere(0.12, (0.14, 0.32, 0.36)).mirror_x(), 0.05)                   # propodeal spines
    return s


@piece("s_xeno_head", (0.62, 0.62, 0.62), tris=900, kind="unit", res=130)
def s_xeno_head():
    """Xeno head (unit frame, -Z face): a long smooth domed skull sweeping back to a ribbed crest, a narrow snout with bare
    teeth."""
    s = ellipsoid(0.4, 0.38, 0.5)
    s = s.su(round_cone((0, 0.05, 0.1), (0, 0.18, 0.5), 0.34, 0.18), 0.1)
    for z in (0.1, 0.22, 0.34):
        s = s.ss(torus(0.3 - z * 0.25, 0.02, axis=2).at(0, 0.1, z), 0.02)
    for x in (0.06, 0.13):
        s = s.su(round_cone((x, -0.28, -0.42), (x, -0.36, -0.44), 0.03, 0.012).mirror_x(), 0.01)
    return s


@piece("s_bfly_body", (0.62, 0.6, 0.62), tris=700, kind="unit", res=120)
def s_bfly_body():
    """Butterfly / moth abdomen (unit frame, rear +Z): slender, ringed, a soft furry pile."""
    s = ellipsoid(0.5, 0.5, 0.5)
    for z in (-0.25, -0.08, 0.08, 0.25):
        rr = 0.5 * np.sqrt(max(0.02, 1 - (z / 0.5) ** 2))
        s = s.ss(torus(rr, 0.03, axis=2).at(0, 0, z), 0.025)
    return s.noise(0.015, freq=26, seed=4)


@piece("s_bug_frond", (0.16, 0.42, 0.06), tris=420, kind="unit", lead=(0.255, 0.78, 0.0375), res=120)
def s_bug_frond():
    """Moth feather antenna (lead 0.26 x 0.78 x 0.04, root -Y, flat in X-Y): a shaft with comb-like side branches."""
    s = round_cone((0, -0.38, 0), (0, 0.38, 0), 0.02, 0.01)
    for i in range(10):
        y = -0.32 + i * 0.07
        L = 0.13 * np.sin(np.pi * (i + 1) / 11)
        s = s.su(round_cone((0, y, 0), (L, y + 0.06, 0), 0.01, 0.004).mirror_x(), 0.006)
    return s


# wings (the primitive is a flat ellipsoid; local X = span with the root at -X, Z = chord with the front at -Z)
def _sheet(outline_fn, thick=0.035):
    """A thin sheet: |y| < thick inside the 2D outline in X-Z."""
    def f(p):
        d2 = outline_fn(p[:, 0], p[:, 2])
        return np.maximum(d2, np.abs(p[:, 1]) - thick)
    return SDF(f)


def _veins(s, lines, r=0.012):
    for a, b in lines:
        s = s.su(capsule((a[0], 0, a[1]), (b[0], 0, b[1]), r), 0.01)
    return s


def _wing(Wx, Wz, outline, veins, thick=0.012, vr=0.014):
    """A thin wing sheet in studs (span Wx along X with the root at -X, chord Wz along Z, front -Z): the outline is given
    in unit coordinates (x, z in -0.5..0.5)."""
    def f(p):
        d2 = outline(p[:, 0] / Wx, p[:, 2] / Wz) * min(Wx, Wz)
        return np.maximum(d2, np.abs(p[:, 1]) - thick)
    s = SDF(f)
    for a, b in veins:
        s = s.su(capsule((a[0] * Wx, 0, a[1] * Wz), (b[0] * Wx, 0, b[1] * Wz), vr), vr * 0.6)
    return s


def _glass_outline(x, z):
    zz = np.where(z < 0, z / 0.42, z / 0.5)
    return (np.sqrt((x / 0.5) ** 2 + zz ** 2) - 1.0) * 0.45


@piece("s_wing_vein", (1.0, 0.06, 0.4), tris=500, kind="unit", lead=(1.92, 0.07, 0.72), mirror=True, res=150, smooth=2)
def s_wing_vein():
    """Glassy insect wing (lead 1.92 x 0.07 x 0.72, root -X, front -Z; left twin mirrored): a long blade with a stout
    leading-edge vein, a stigma and branching veins."""
    s = _wing(1.92, 0.72, _glass_outline, [((-0.48, -0.1), (0.42, -0.36)), ((-0.45, 0.0), (0.45, 0.02)), ((-0.4, 0.05), (0.3, 0.3)), ((0.0, 0.0), (0.2, 0.42)), ((-0.2, -0.04), (0.35, -0.2))])
    return s.su(ellipsoid(0.12, 0.02, 0.04, (0.6, 0.0, -0.24)), 0.01)


def _bfly_fore(x, z):
    ang = np.arctan2(z, x + 0.5)
    r = np.hypot(x + 0.5, z)
    edge = 0.98 - 0.3 * np.clip((ang - 0.15) / 1.3, 0, 1) ** 1.4 + 0.015 * np.sin(ang * 22)
    lead = -0.45 + 0.02 * (x + 0.5)
    return np.maximum(np.maximum(r - edge, lead - z), z - 0.5) * 0.5


@piece("s_wing_bfly_f", (1.4, 0.07, 0.75), tris=500, kind="unit", lead=(2.65, 0.095, 1.4), mirror=True, res=160, smooth=2)
def s_wing_bfly_f():
    """Butterfly forewing (lead 2.65 x 0.1 x 1.4, root -X, front -Z; left twin mirrored): a broad triangle with a straight
    leading edge, a scalloped outer margin and raised veins."""
    return _wing(2.65, 1.4, _bfly_fore, [((-0.48, -0.42), (0.45, -0.42)), ((-0.48, -0.3), (0.38, 0.0)), ((-0.45, -0.25), (0.15, 0.3)), ((-0.45, -0.2), (-0.1, 0.45))], 0.016, 0.02)


def _bfly_hind(x, z, tail=False):
    r = np.hypot((x + 0.45) / 0.92, (z + 0.02) / 0.5)
    ang = np.arctan2(z, x + 0.5)
    d = (r - 1.0 + 0.03 * np.sin(ang * 16)) * 0.5
    d = np.maximum(d, -(x + 0.5))
    if tail:
        t = (np.hypot((x - 0.32) / 0.07, (z - 0.42) / 0.2) - 1.0) * 0.07
        d = np.minimum(d, t)
    return d


@piece("s_wing_bfly_h", (1.05, 0.07, 0.72), tris=450, kind="unit", lead=(1.96, 0.095, 1.33), mirror=True, res=160, smooth=2)
def s_wing_bfly_h():
    """Butterfly hindwing (lead 1.96 x 0.1 x 1.33, root -X; left twin mirrored): a rounded fan with a scalloped margin."""
    return _wing(1.96, 1.33, _bfly_hind, [((-0.45, -0.1), (0.4, 0.0)), ((-0.45, -0.05), (0.2, 0.35)), ((-0.45, 0.0), (-0.05, 0.45))], 0.016, 0.02)


@piece("s_wing_bfly_tail", (1.05, 0.07, 0.95), tris=480, kind="unit", lead=(1.96, 0.095, 1.33), mirror=True, res=160, smooth=2)
def s_wing_bfly_tail():
    """Swallowtail / luna hindwing (root -X; left twin mirrored): the rounded hindwing with a long tail streamer."""
    return _wing(1.96, 1.33, lambda x, z: _bfly_hind(x, z * 1.2, tail=True), [((-0.45, -0.1), (0.4, 0.0)), ((-0.45, -0.05), (0.3, 0.4))], 0.016, 0.02)


@piece("s_wing_dfly", (1.45, 0.06, 0.6), tris=600, kind="unit", lead=(2.7, 0.095, 1.1), mirror=True, res=160, smooth=2)
def s_wing_dfly():
    """Dragonfly wings, one side (detail 0; lead 2.7 x 0.1 x 1.1, root -X; left twin mirrored): fore and hind wing as
    two long veined blades from one root."""
    def outline(x, z):
        a = np.hypot(x / 0.5, (z + 0.22) / 0.2) - 1.0
        b = np.hypot(x / 0.48, (z - 0.2) / 0.24) - 1.0
        return np.minimum(a, b) * 0.2
    return _wing(2.7, 1.1, outline, [((-0.48, -0.36), (0.45, -0.38)), ((-0.48, 0.04), (0.45, 0.06))], 0.012, 0.018)


@piece("s_leaf_wing", (0.26, 0.08, 1.0), tris=450, kind="unit", lead=(0.42, 0.08, 1.85), mirror=True, res=140, smooth=2)
def s_leaf_wing():
    """Leaf-like folded wing (mantis tegmen, katydid; lead 0.42 x 0.08 x 1.85, long along Z; left twin mirrored): a leaf
    with a midrib and side veins."""
    def outline(x, z):
        return (np.hypot(x / 0.5, z / 0.5) - 1.0) * 0.2
    s = _wing(0.42, 1.85, outline, [((0.0, -0.48), (0.0, 0.48)), ((0.0, -0.25), (0.4, -0.05)), ((0.0, 0.0), (0.4, 0.2)), ((0.0, 0.25), (0.35, 0.42))], 0.02, 0.015)
    return s


@piece("s_leaf_body", (1.05, 0.16, 1.4), tris=600, kind="unit", lead=(1.9, 0.18, 2.6), res=150, smooth=2)
def s_leaf_body():
    """Leaf insect abdomen (lead 1.9 x 0.18 x 2.6): a broad flat leaf with a raised midrib, side veins and a ragged edge."""
    def outline(x, z):
        return (np.hypot(x / 0.5, z / 0.5) - 1.0 + 0.04 * np.sin(z * 30)) * 0.5
    s = _wing(1.9, 2.6, outline, [((0.0, -0.48), (0.0, 0.48)), ((0.0, -0.3), (0.35, -0.1)), ((0.0, -0.05), (0.38, 0.15)), ((0.0, 0.2), (0.3, 0.38))], 0.05, 0.04)
    return s


@piece("s_stick_seg", (0.6, 0.6, 0.6), tris=420, kind="unit", res=120)
def s_stick_seg():
    """Stick insect segment (unit frame, long along Z): a twig with bark nodes."""
    s = round_cone((0, 0, -0.48), (0, 0, 0.48), 0.42, 0.36)
    for z in (-0.25, 0.1, 0.38):
        s = s.su(torus(0.4, 0.06, axis=2).at(0, 0, z), 0.05)
    return s.noise(0.02, freq=14, seed=8)


@piece("s_mantis_head", (0.62, 0.6, 0.6), tris=700, kind="unit", res=120)
def s_mantis_head():
    """Mantis head (unit frame, -Z face): a wide triangle with eye bulges at the upper corners and a narrow jaw."""
    # a triangle: the ellipsoid cut by two planes that narrow it toward the jaw
    cut = SDF(lambda p: np.abs(p[:, 0]) * 0.8 - 0.32 - (p[:, 1] + 0.1) * 0.55)
    s = ellipsoid(0.5, 0.42, 0.42).si(cut, 0.06)
    s = s.su(ellipsoid(0.16, 0.18, 0.14, (0, -0.4, -0.12)), 0.08)
    s = s.su(sphere(0.18, (0.38, 0.12, -0.05)).mirror_x(), 0.08)
    return s


@piece("s_mantis_abdomen", (0.62, 0.6, 0.62), tris=800, kind="unit", res=120)
def s_mantis_abdomen():
    """Mantis abdomen (unit frame, rear +Z): long, flattened, ringed, curling up a little at the tip."""
    s = ellipsoid(0.5, 0.42, 0.5).bend(-0.3, axis=2, toward=1)
    for z in (-0.3, -0.1, 0.1, 0.3):
        rr = 0.48 * np.sqrt(max(0.02, 1 - (z / 0.5) ** 2))
        s = s.ss(torus(rr, 0.02, axis=2).scale3(1, 0.85, 1).at(0, 0, z), 0.02)
    return s


@piece("s_mantis_arm", (0.3, 0.7, 0.4), tris=600, kind="unit", lead=(0.24, 0.97, 0.24), mirror=True, res=130)
def s_mantis_arm():
    """Raptorial foreleg (lead 0.24 x 0.97 x 0.24 studs, the femur from shoulder to knee, local +Z up; left twin
    mirrored): a spined femur with the tibia folded back underneath it, ending in a hook."""
    s = round_cone((0, -0.45, 0), (0, 0.42, -0.02), 0.11, 0.085)
    s = s.su(round_cone((0, 0.42, -0.04), (0, -0.22, -0.17), 0.065, 0.045), 0.04)    # tibia folded back
    s = s.su(round_cone((0, -0.22, -0.17), (0, -0.3, -0.07), 0.04, 0.012), 0.02)    # hook
    for i in range(5):
        y = -0.3 + i * 0.14
        s = s.su(round_cone((0, y, -0.06), (0, y - 0.03, -0.14), 0.022, 0.006), 0.01)  # femur spines
    return s


@piece("s_hopper_head", (0.62, 0.62, 0.62), tris=800, kind="unit", res=120)
def s_hopper_head():
    """Grasshopper head (unit frame, -Z face): a tall face with a vertical frons, cheek plates and chewing mouthparts."""
    s = ellipsoid(0.46, 0.5, 0.48)
    s = s.su(ellipsoid(0.3, 0.38, 0.1, (0, -0.05, -0.42)), 0.08)                  # frons
    s = s.su(ellipsoid(0.24, 0.12, 0.14, (0, -0.44, -0.3)), 0.06)                 # mouthparts
    s = s.ss(capsule((0.18, -0.15, -0.46), (0.22, -0.4, -0.38), 0.02).mirror_x(), 0.02)
    return s


@piece("s_hopper_pronotum", (0.62, 0.62, 0.62), tris=800, kind="unit", res=120)
def s_hopper_pronotum():
    """Grasshopper pronotum (unit frame): a saddle shield drooping over the sides, with a keel and cross grooves."""
    s = ellipsoid(0.5, 0.5, 0.5)
    s = s.su(ellipsoid(0.52, 0.42, 0.46, (0, 0.04, 0.02)), 0.05)
    s = s.su(capsule((0, 0.52, -0.42), (0, 0.5, 0.42), 0.035), 0.03)
    for z in (-0.15, 0.12):
        s = s.ss(torus(0.47, 0.02, axis=2).at(0, 0.05, z), 0.02)
    return s


def _hop_femur():
    s = round_cone((0, -0.66, 0), (0, 0.66, 0.0), 0.2, 0.095)
    for i in range(7):
        y = -0.45 + i * 0.15
        s = s.ss(capsule((0.2, y - 0.04, 0.0), (0.0, y + 0.05, 0.19), 0.012).mirror_x(), 0.015)   # herringbone
    return s


@piece("s_hopper_leg", (0.4, 1.0, 0.8), tris=600, kind="unit", lead=(0.42, 1.52, 0.42), mirror=True, res=140)
def s_hopper_leg():
    """Grasshopper jumping leg (lead 0.42 x 1.52 x 0.42 studs, the thigh from hip to knee, local +Z down; left twin
    mirrored): a muscular femur with herringbone ridges, the thin spined tibia folded down and forward to the foot."""
    s = _hop_femur()
    s = s.su(round_cone((0, 0.68, 0.0), (0, -0.12, 1.22), 0.06, 0.035), 0.04)     # tibia
    s = s.su(round_cone((0, -0.12, 1.22), (0, -0.3, 1.28), 0.035, 0.02), 0.02)    # tarsus
    for i in range(5):
        t = 0.15 + i * 0.16
        y, z = 0.68 - 0.8 * t, 1.22 * t
        s = s.su(round_cone((0, y, z), (0, y + 0.08, z + 0.02), 0.018, 0.005), 0.008)  # tibial spines
    return s


@piece("s_hopper_femur", (0.4, 1.0, 0.4), tris=420, kind="unit", lead=(0.42, 1.52, 0.42), mirror=True, res=120)
def s_hopper_femur():
    """Grasshopper jumping femur alone (detail 3, lead 0.42 x 1.52 x 0.42 studs; the tibia is its own part)."""
    return _hop_femur()


@piece("s_roach_pronotum", (0.62, 0.6, 0.62), tris=700, kind="unit", res=120)
def s_roach_pronotum():
    """Cockroach pronotum (unit frame): a flat oval shield with a raised rim, overhanging the head."""
    s = ellipsoid(0.5, 0.5, 0.5)
    s = s.su(ellipsoid(0.52, 0.18, 0.52, (0, -0.06, -0.04)), 0.06)
    s = s.ss(ellipsoid(0.32, 0.12, 0.3, (0, 0.47, 0.0)), 0.04)
    return s


@piece("s_roach_body", (0.62, 0.6, 0.62), tris=900, kind="unit", res=130)
def s_roach_body():
    """Cockroach / flat bug body (unit frame, rear +Z): flat oval wings overlapping at the midline with a raised edge."""
    s = ellipsoid(0.5, 0.5, 0.5)
    s = s.ss(capsule((0.02, 0.5, -0.4), (-0.06, 0.48, 0.46), 0.018), 0.02)          # overlap seam
    s = s.su(ellipsoid(0.51, 0.14, 0.5, (0, -0.1, 0.0)), 0.05)
    s = s.ss(capsule((0.28, 0.4, -0.35), (0.3, 0.32, 0.3), 0.012).mirror_x(), 0.015)
    return s


@piece("s_silverfish_body", (0.6, 0.6, 0.62), tris=800, kind="unit", res=130)
def s_silverfish_body():
    """Silverfish body (unit frame, rear +Z): a tapering carrot of overlapping scaly plates."""
    s = ellipsoid(0.5, 0.5, 0.5).su(round_cone((0, 0, -0.1), (0, 0, 0.5), 0.4, 0.06), 0.15)
    for z in (-0.3, -0.15, 0.0, 0.15, 0.3):
        rr = 0.48 * np.sqrt(max(0.05, 1 - ((z + 0.05) / 0.55) ** 2))
        s = s.su(torus(rr, 0.025, axis=2).scale3(1, 0.6, 1).at(0, 0.02, z), 0.03)
    return s


@piece("s_centipede_seg", (0.6, 0.6, 0.6), tris=600, kind="unit", res=120)
def s_centipede_seg():
    """Centipede segment (unit frame): a flat tergite plate with a rim over a softer ring."""
    s = ellipsoid(0.5, 0.5, 0.5)
    s = s.su(ellipsoid(0.5, 0.18, 0.4, (0, 0.18, -0.04)), 0.06)
    s = s.ss(capsule((0.3, 0.4, -0.25), (0.3, 0.4, 0.25), 0.02).mirror_x(), 0.02)
    return s


@piece("s_larva_seg", (0.6, 0.6, 0.6), tris=600, kind="unit", res=120)
def s_larva_seg():
    """Larva segment (unit frame): a fat soft ring with creases and a pair of stubby prolegs."""
    s = ellipsoid(0.5, 0.5, 0.5)
    s = s.ss(torus(0.47, 0.03, axis=2).at(0, 0, -0.18), 0.04).ss(torus(0.47, 0.03, axis=2).at(0, 0, 0.18), 0.04)
    s = s.su(sphere(0.12, (0.2, -0.42, 0.0)).mirror_x(), 0.06)
    return s


@piece("s_mech_pod", (0.6, 0.6, 0.6), tris=900, kind="unit", res=130)
def s_mech_pod():
    """Walker / robot crab pod (unit frame): a domed armoured hull with panel lines, a belt of leg sockets and a hatch."""
    s = ellipsoid(0.5, 0.5, 0.5)
    s = s.su(torus(0.47, 0.05).at(0, -0.05, 0), 0.03)
    s = s.ss(torus(0.38, 0.015).at(0, 0.3, 0), 0.015)
    s = s.ss(capsule((0, 0.47, -0.3), (0, 0.47, 0.3), 0.015), 0.015)
    s = s.su(cylinder(0.16, 0.03, axis=1, rr=0.02).at(0, 0.49, 0.1), 0.02)
    return s


# ------------------------------------------------------------------------------------------------ arachnids
@piece("s_spider_ceph", (0.62, 0.48, 0.72), tris=1100, kind="unit", lead=(1.1, 0.72, 1.25), res=140)
def s_spider_ceph():
    """Spider cephalothorax (lead: Ceph 1.1 x 0.72 x 1.25): a shield-shaped carapace with a central fovea and radiating
    grooves, a raised eye mound at the front, chelicerae below it."""
    s = ellipsoid(0.55, 0.36, 0.625)
    s = s.su(ellipsoid(0.36, 0.2, 0.24, (0, 0.18, -0.38)), 0.12)                   # eye mound / head region
    s = s.ss(ellipsoid(0.07, 0.04, 0.12, (0, 0.36, 0.1)), 0.03)                    # fovea
    for a in (35, 75, 115):
        r = np.radians(a)
        s = s.ss(capsule((0.08 * np.cos(r), 0.34, 0.1 - 0.08 * np.sin(r)), (0.45 * np.cos(r), 0.2, 0.1 - 0.42 * np.sin(r) * 0.8 + 0.2), 0.016).mirror_x(), 0.02)
    s = s.su(round_cone((0.12, -0.12, -0.52), (0.1, -0.32, -0.62), 0.12, 0.08).mirror_x(), 0.06)   # chelicerae
    return s


@piece("s_spider_fang", (0.2, 0.3, 0.16), tris=320, kind="unit", lead=(0.264, 0.43, 0.185), mirror=True, res=110)
def s_spider_fang():
    """Spider chelicera with its fang (lead 0.26 x 0.43 x 0.19; left twin mirrored): a stout basal segment, a curved fang."""
    s = round_cone((0, -0.2, 0), (0, 0.04, 0.0), 0.12, 0.09)
    s = s.su(tube([(0, 0.04, 0.0), (-0.03, 0.15, -0.02), (-0.09, 0.22, 0.0)], [0.055, 0.03, 0.008], k=0.015), 0.02)
    return s


@piece("s_spider_abdomen", (0.9, 0.78, 1.0), tris=1100, kind="unit", lead=(1.65, 1.42, 1.85), res=140)
def s_spider_abdomen():
    """Spider abdomen (lead: Abdomen 1.65 x 1.42 x 1.85): a rounded bulb, slightly pear-shaped, with muscle dimples on the
    back and spinnerets at the rear tip."""
    s = ellipsoid(0.825, 0.71, 0.925)
    s = s.su(ellipsoid(0.7, 0.62, 0.6, (0, 0.05, 0.25)), 0.2)
    for z in (-0.3, 0.0, 0.3):
        s = s.ss(sphere(0.06, (0.22, 0.69 - abs(z) * 0.2, z)).mirror_x(), 0.04)
    s = s.su(round_cone((0.06, -0.1, 0.85), (0.08, -0.15, 1.0), 0.08, 0.05).mirror_x(), 0.05)
    return s


@piece("s_tick_body", (1.05, 0.55, 1.15), tris=1000, kind="unit", lead=(1.9, 0.95, 2.1), res=140)
def s_tick_body():
    """Tick / mite body (lead: Abdomen 1.9 x 0.95 x 2.1): a flat engorged oval with a scutum shield at the front, festoon
    grooves round the rear rim."""
    s = ellipsoid(0.95, 0.475, 1.05)
    s = s.su(ellipsoid(0.55, 0.12, 0.45, (0, 0.38, -0.55)), 0.08)
    for i in range(9):
        a = np.radians(-60 + i * 15)
        s = s.ss(capsule((0.95 * np.sin(a), -0.05, 1.05 * np.cos(a) * 0.92), (0.8 * np.sin(a), 0.1, 0.9 * np.cos(a) * 0.92), 0.02), 0.02)
    return s


@piece("s_scorpion_body", (0.75, 0.42, 1.35), tris=1300, kind="unit", lead=(1.35, 0.6, 2.5), res=150)
def s_scorpion_body():
    """Scorpion prosoma + mesosoma (lead: Mesosoma 1.35 x 0.6 x 2.5): a carapace with median eyes and seven overlapping
    tergite plates with a keel."""
    s = ellipsoid(0.675, 0.3, 1.25)
    s = s.su(ellipsoid(0.55, 0.26, 0.45, (0, 0.03, -0.75)), 0.1)                  # carapace
    s = s.su(sphere(0.08, (0.07, 0.28, -0.85)).mirror_x(), 0.04)                   # median eyes
    for i in range(7):
        z = -0.3 + i * 0.22
        rr = np.sqrt(max(0.05, 1 - (z / 1.25) ** 2))
        s = s.su(ellipsoid(0.67 * rr, 0.07, 0.07, (0, 0.27 * rr - 0.01, z)), 0.04)
    s = s.su(capsule((0, 0.3, -0.4), (0, 0.27, 1.0), 0.03), 0.03)
    return s


@piece("s_scorpion_seg", (0.32, 0.66, 0.32), tris=420, kind="unit", lead=(0.45, 1.2, 0.45), res=120)
def s_scorpion_seg():
    """Scorpion tail (metasoma) segment (lead 0.45 x 1.2 x 0.45): a barrel with four keels and a joint knob."""
    s = round_cone((0, -0.42, 0), (0, 0.38, 0), 0.2, 0.18)
    for a in (45, 135):
        r = np.radians(a)
        s = s.su(capsule((0.19 * np.cos(r), -0.38, 0.19 * np.sin(r)), (0.17 * np.cos(r), 0.36, 0.17 * np.sin(r)), 0.03).mirror_x(), 0.02)
    s = s.su(sphere(0.13, (0, 0.46, 0)), 0.05)
    return s


@piece("s_scorpion_sting", (0.34, 0.6, 0.5), tris=480, kind="unit", lead=(0.5, 1.0, 0.5), res=130)
def s_scorpion_sting():
    """Scorpion telson (lead 0.5 x 1.0 x 0.5, local +Z rolled up): a swollen venom bulb and a curved aculeus hooking
    down."""
    s = ellipsoid(0.25, 0.32, 0.24, (0, -0.15, 0.03))
    s = s.su(tube([(0, 0.12, 0.0), (0, 0.32, -0.05), (0, 0.48, -0.18), (0, 0.5, -0.32)], [0.11, 0.065, 0.035, 0.012], k=0.03), 0.04)
    return s


def _chela(W, L, D, palm=1.0, finger=1.0, teeth=4, spiky=False):
    """A pincer in a limb frame (studs, root at -L/2, tip at +L/2, local X = outward, Z = up): a swollen palm, the fixed
    finger on the inside (-X), the movable dactyl on the outside, toothed cutting edges."""
    h = L / 2
    s = ellipsoid(W * 0.5 * palm, h * 0.62, D * 0.5 * palm, (0, -h * 0.3, 0))
    s = s.su(round_cone((0, -h * 0.95, 0), (0, -h * 0.6, 0), W * 0.2, W * 0.3), W * 0.1)
    fixed = tube([(-W * 0.18, h * 0.1, 0), (-W * 0.2, h * 0.55, 0), (-W * 0.06, h * 0.97, 0)], [W * 0.17 * finger, W * 0.11 * finger, W * 0.03], k=W * 0.05)
    dact = tube([(W * 0.2, 0.0, 0), (W * 0.24, h * 0.5, D * 0.05), (W * 0.06, h * 0.95, 0)], [W * 0.18 * finger, W * 0.12 * finger, W * 0.03], k=W * 0.05)
    s = s.su(fixed, W * 0.1).su(dact, W * 0.06)
    for i in range(teeth):
        y = h * 0.2 + i * h * 0.16
        s = s.su(sphere(W * 0.04, (-W * 0.06, y, 0)), W * 0.02).su(sphere(W * 0.035, (W * 0.1, y + h * 0.06, 0)), W * 0.02)
    if spiky:
        rng = np.random.default_rng(11)
        for _ in range(10):
            a = rng.uniform(0, 2 * np.pi)
            y = rng.uniform(-h * 0.75, 0.0)
            p = np.array([W * 0.48 * palm * np.cos(a), y, D * 0.48 * palm * np.sin(a)])
            s = s.su(round_cone(tuple(p * 0.9), tuple(p * 1.25 + np.array([0, h * 0.08, 0])), W * 0.05, W * 0.012), W * 0.02)
    return s


@piece("s_scorpion_claw", (0.45, 0.75, 0.32), tris=600, kind="unit", lead=(0.62, 1.31, 0.42), mirror=True, res=130)
def s_scorpion_claw():
    """Scorpion chela (lead 0.62 x 1.31 x 0.42, local X outward; left twin mirrored): a long swollen hand, slender fingers."""
    return _chela(0.62, 1.31, 0.42, 1.0, 0.8, teeth=3).noise(0.003, freq=60, seed=5)


@piece("s_eurypterid_body", (0.86, 0.32, 1.65), tris=1200, kind="unit", lead=(1.6, 0.5, 3.2), res=150)
def s_eurypterid_body():
    """Sea scorpion body (lead: Mesosoma 1.6 x 0.5 x 3.2): a rounded head shield with compound eyes, a broad plated trunk
    tapering to the tail."""
    s = ellipsoid(0.8, 0.25, 1.6)
    s = s.su(ellipsoid(0.75, 0.2, 0.5, (0, 0.02, -1.15)), 0.1)
    s = s.su(ellipsoid(0.14, 0.08, 0.2, (0.4, 0.2, -1.2)).mirror_x(), 0.05)
    for i in range(8):
        z = -0.55 + i * 0.26
        rr = np.sqrt(max(0.05, 1 - (z / 1.6) ** 2))
        s = s.su(ellipsoid(0.8 * rr, 0.05, 0.08, (0, 0.21 * rr, z)), 0.04)
    return s


# ------------------------------------------------------------------------------------------------ crustaceans
def _carapace(W, H, L, spiky=False, egg=False):
    s = ellipsoid(W / 2, H / 2, L / 2)
    # flatter top, a sharp lateral rim with teeth along the front sides, a notched front between the eye sockets
    s = s.su(ellipsoid(W / 2 * 1.02, H * 0.12, L / 2 * 0.92, (0, -H * 0.05, -L * 0.03)), 0.08)
    if not egg:
        for i in range(5):
            a = np.radians(-70 + i * 16)
            p = (W / 2 * np.sin(-a) * 1.0, -H * 0.02, -L / 2 * np.cos(a) * 0.85)
            s = s.su(round_cone(p, (p[0] * 1.08, p[1], p[2] * 1.04 - 0.05), 0.07, 0.02).mirror_x(), 0.04)
        s = s.ss(sphere(0.12, (0.15, H * 0.15, -L / 2 * 0.98)).mirror_x(), 0.05)        # eye sockets
        s = s.su(round_cone((0, H * 0.1, -L * 0.45), (0, H * 0.05, -L * 0.53), 0.1, 0.04), 0.05)  # rostrum
    # regions: gastric and branchial swellings with grooves between
    s = s.su(ellipsoid(W * 0.18, H * 0.2, L * 0.18, (0, H * 0.32, -L * 0.1)), 0.15)
    s = s.ss(capsule((W * 0.16, H * 0.46, -L * 0.25), (W * 0.2, H * 0.4, L * 0.2), 0.02).mirror_x(), 0.03)
    if spiky:
        rng = np.random.default_rng(9)
        for _ in range(16):
            u, v = rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8)
            if u * u + v * v > 0.7:
                continue
            y = H / 2 * np.sqrt(max(0.0, 1 - u * u - v * v))
            p = np.array([W / 2 * u, y, L / 2 * v])
            n = np.array([u / (W / 2), y / (H / 2) ** 2 * 0.25, v / (L / 2)])
            n = n / np.linalg.norm(n)
            s = s.su(round_cone(tuple(p - n * 0.05), tuple(p + n * 0.22), 0.07, 0.015), 0.03)
    return s


@piece("s_crab_carapace", (1.4, 0.55, 1.08), tris=1300, kind="unit", lead=(2.5, 0.88, 1.85), res=150)
def s_crab_carapace():
    """Crab carapace (lead: Carapace 2.5 x 0.88 x 1.85): broad and flat-topped, a sharp rim with teeth along the front
    sides, a notched front with eye sockets and rostrum, raised gastric and branchial regions."""
    return _carapace(2.5, 0.88, 1.85)


@piece("s_crab_carapace_spiky", (1.3, 0.68, 1.12), tris=1500, kind="unit", lead=(2.0, 0.95, 1.95), res=150)
def s_crab_carapace_spiky():
    """King crab carapace (lead 2.0 x 0.95 x 1.95): a rounder shield studded with spines."""
    return _carapace(2.0, 0.95, 1.95, spiky=True)


@piece("s_sand_crab", (0.9, 0.62, 1.2), tris=1000, kind="unit", lead=(1.6, 1.0, 2.2), res=140)
def s_sand_crab():
    """Sand (mole) crab (lead 1.6 x 1.0 x 2.2): an egg-shaped shell with smooth bands, for digging backwards."""
    s = ellipsoid(0.8, 0.5, 1.1)
    for z in (0.2, 0.45, 0.68):
        s = s.ss(torus(0.8 * np.sqrt(max(0.05, 1 - (z / 1.1) ** 2)), 0.02, axis=2).scale3(1, 0.62, 1).at(0, 0, z), 0.02)
    return s


@piece("s_crab_claw", (0.48, 0.75, 0.36), tris=700, kind="unit", lead=(0.62, 1.3, 0.45), mirror=True, res=130)
def s_crab_claw():
    """Crab chela (lead 0.62 x 1.3 x 0.45, root -Y, local X outward, +Z up; left twin mirrored): a deep swollen palm, a
    fixed finger and a hinged dactyl with toothed edges."""
    return _chela(0.62, 1.3, 0.45, 1.15, 1.1, teeth=4)


@piece("s_crab_claw_spiky", (0.5, 0.75, 0.4), tris=900, kind="unit", lead=(0.62, 1.3, 0.45), mirror=True, res=140)
def s_crab_claw_spiky():
    """Spiny crab chela (king crab, yeti crab; left twin mirrored): the crab claw studded with spines."""
    return _chela(0.62, 1.3, 0.45, 1.1, 1.05, teeth=4, spiky=True)


@piece("s_spiral_shell", (1.35, 1.3, 1.45), tris=1500, kind="unit", lead=(2.4, 2.3, 2.6), res=160)
def s_spiral_shell():
    """Spiral gastropod shell (lead: Shell 2.4 x 2.3 x 2.6, aperture forward-down): a fat body whorl and a conical spire
    rising back and up, wound by a deep helical suture, with a flared lip around the aperture."""
    base = np.array([0.0, -0.2, -0.15])
    tip = np.array([0.0, 0.95, 1.2])
    ax = tip - base
    L = np.linalg.norm(ax)
    ax = ax / L
    u = np.cross(ax, [1.0, 0, 0])
    u /= np.linalg.norm(u)
    v = np.cross(ax, u)
    R0, R1 = 0.98, 0.05
    s = round_cone(tuple(base), tuple(tip), R0, R1)
    s = s.su(ellipsoid(1.12, 0.95, 1.05, (0.0, -0.2, -0.2)), 0.25)                 # body whorl
    # helical suture: a groove winding up the spire
    pts, rads = [], []
    turns, n = 3.6, 90
    for k in range(n):
        t = 0.08 + 0.9 * k / (n - 1)
        rr = (R0 + (R1 - R0) * t) * (1.06 if t < 0.3 else 1.0)
        a = turns * 2 * np.pi * t
        c = base + ax * (L * t)
        pts.append(tuple(c + rr * (np.cos(a) * u + np.sin(a) * v)))
        rads.append(0.1 * (1 - t) + 0.025)
    s = s.ss(tube(pts, rads, k=0.05), 0.06)
    s = s.noise(0.008, freq=22, seed=6)                                            # growth lines
    # aperture with a flared lip, facing forward and down
    s = s.su(torus(0.52, 0.09, axis=2).scale3(1.0, 0.85, 1).at(0, -0.55, -1.05), 0.12)
    s = s.ss(ellipsoid(0.5, 0.4, 0.5, (0, -0.55, -1.15)), 0.06)
    return s


@piece("s_lobster_body", (0.6, 0.5, 1.05), tris=1100, kind="unit", lead=(1.05, 0.88, 1.9), res=140)
def s_lobster_body():
    """Lobster cephalothorax (lead 1.05 x 0.88 x 1.9): a cylinder-ish carapace with the cervical groove, a toothed rostrum
    between the eyes and a fringe over the legs."""
    s = ellipsoid(0.525, 0.44, 0.95)
    s = s.ss(torus(0.47, 0.03, axis=2).scale3(1, 0.85, 1).at(0, 0.02, -0.15), 0.03)
    s = s.su(tube([(0, 0.2, -0.85), (0, 0.22, -1.0), (0, 0.18, -1.12)], [0.09, 0.06, 0.02], k=0.03), 0.05)
    for z in (-0.95, -1.03):
        s = s.su(round_cone((0, 0.25, z), (0, 0.31, z - 0.03), 0.02, 0.005), 0.01)
    s = s.su(ellipsoid(0.54, 0.12, 0.85, (0, -0.25, 0.05)), 0.06)
    return s.noise(0.005, freq=30, seed=1)


@piece("s_lobster_body_spiny", (0.62, 0.52, 1.05), tris=1300, kind="unit", lead=(1.05, 0.88, 1.9), res=140)
def s_lobster_body_spiny():
    """Spiny lobster cephalothorax (lead 1.05 x 0.88 x 1.9): the lobster carapace covered in forward-pointing spines, two
    big horns over the eyes."""
    s = s_lobster_body()
    rng = np.random.default_rng(4)
    for _ in range(18):
        a = rng.uniform(-1.3, 1.3)
        z = rng.uniform(-0.75, 0.75)
        rr = np.sqrt(max(0.05, 1 - (z / 0.95) ** 2))
        p = np.array([0.52 * rr * np.sin(a), 0.44 * rr * np.cos(a), z])
        s = s.su(round_cone(tuple(p * 0.95), tuple(p * 1.05 + np.array([0, 0.04, -0.12])), 0.04, 0.01), 0.02)
    s = s.su(round_cone((0.18, 0.3, -0.8), (0.24, 0.42, -1.05), 0.08, 0.02).mirror_x(), 0.03)
    return s


@piece("s_lobster_seg", (0.55, 0.62, 0.42), tris=420, kind="unit", lead=(0.9, 1.0, 0.65), res=120)
def s_lobster_seg():
    """Lobster / shrimp tail segment (lead 0.9 x 1.0 x 0.65, +Y backward): an arched tergite with side pleura flanges and
    a hinge groove."""
    s = ellipsoid(0.45, 0.52, 0.325)
    s = s.su(ellipsoid(0.48, 0.3, 0.12, (0, 0.0, -0.2)), 0.06)
    s = s.ss(ellipsoid(0.5, 0.025, 0.36, (0, -0.25, 0.02)), 0.03)
    return s


@piece("s_lobster_fan", (0.7, 0.14, 0.6), tris=500, kind="unit", lead=(1.2, 0.16, 1.0), res=130, smooth=2)
def s_lobster_fan():
    """Tail fan (lead 1.2 x 0.16 x 1.0, flat in X-Z, rear +Z): the telson and four uropods fanned out, ribbed."""
    s = None
    for a, w in ((0, 0.18), (26, 0.19), (-26, 0.19), (52, 0.17), (-52, 0.17)):
        r = np.radians(a)
        c = (0.36 * np.sin(r), 0.0, -0.15 + 0.4 * np.cos(r))
        e = ellipsoid(w, 0.05, 0.36).rot(0, a, 0).at(*c)
        s = e if s is None else s.su(e, 0.04)
    s = s.su(ellipsoid(0.24, 0.07, 0.16, (0, 0, -0.4)), 0.05)
    return s


@piece("s_shrimp_body", (0.52, 0.56, 0.86), tris=900, kind="unit", lead=(0.85, 0.9, 1.35), res=140)
def s_shrimp_body():
    """Shrimp carapace (lead 0.85 x 0.9 x 1.35): smooth and laterally compressed, a long serrated rostrum sweeping up from
    between the eyes."""
    s = ellipsoid(0.38, 0.45, 0.675)
    s = s.su(tube([(0, 0.25, -0.5), (0, 0.32, -0.75), (0, 0.42, -0.95)], [0.07, 0.04, 0.012], k=0.04), 0.05)
    for i in range(4):
        z = -0.55 - i * 0.1
        s = s.su(round_cone((0, 0.3 + i * 0.025, z), (0, 0.36 + i * 0.025, z - 0.02), 0.02, 0.005), 0.01)
    return s


@piece("s_mantis_shrimp_body", (0.6, 0.4, 0.75), tris=1000, kind="unit", lead=(1.0, 0.65, 1.3), res=140)
def s_mantis_shrimp_body():
    """Mantis shrimp carapace (lead 1.0 x 0.65 x 1.3): a flat shield with a keel, the plated thorax behind it."""
    s = ellipsoid(0.5, 0.325, 0.65)
    s = s.su(capsule((0, 0.3, -0.5), (0, 0.3, 0.5), 0.03), 0.03)
    for z in (0.15, 0.32, 0.48):
        s = s.ss(torus(0.47 * np.sqrt(max(0.05, 1 - (z / 0.65) ** 2)), 0.02, axis=2).scale3(1, 0.65, 1).at(0, 0, z), 0.02)
    return s


def _banded_oval(W, H, L, n, lobes=False):
    s = ellipsoid(W / 2, H / 2, L / 2)
    s = s.su(ellipsoid(W / 2 * 1.02, H * 0.1, L / 2 * 0.98, (0, -H * 0.2, 0)), 0.06)      # rim
    for i in range(n):
        z = -L * 0.38 + i * L * 0.76 / (n - 1)
        rr = np.sqrt(max(0.05, 1 - (z / (L / 2)) ** 2))
        s = s.su(ellipsoid(W / 2 * rr * 1.01, H / 2 * rr * 1.01, 0.05, (0, 0, z)), 0.03)
        s = s.ss(ellipsoid(W / 2 * rr * 1.05, H / 2 * rr * 1.05, 0.015, (0, 0, z + 0.07)), 0.015)
    if lobes:
        s = s.ss(capsule((W * 0.16, H * 0.5, -L * 0.4), (W * 0.14, H * 0.45, L * 0.45), 0.04).mirror_x(), 0.05)
    return s


@piece("s_isopod_body", (1.05, 0.6, 1.62), tris=1400, kind="unit", lead=(1.9, 1.0, 3.0), res=150)
def s_isopod_body():
    """Isopod / pill bug shell (lead: Shell 1.9 x 1.0 x 3.0): a domed oval of overlapping plates with a flared rim."""
    return _banded_oval(1.9, 1.0, 3.0, 8)


@piece("s_trilobite_body", (1.1, 0.45, 1.5), tris=1400, kind="unit", lead=(2.0, 0.7, 2.8), res=150)
def s_trilobite_body():
    """Trilobite (lead: Shell 2.0 x 0.7 x 2.8): a half-moon head shield with genal spines, a three-lobed segmented thorax
    and a tail shield."""
    s = _banded_oval(2.0, 0.7, 2.8, 9, lobes=True)
    s = s.su(ellipsoid(0.95, 0.22, 0.45, (0, 0.05, -1.05)), 0.08)
    s = s.su(round_cone((0.85, -0.02, -0.95), (1.0, -0.05, -0.3), 0.08, 0.02).mirror_x(), 0.04)
    return s


@piece("s_horseshoe_shell", (1.5, 0.58, 1.4), tris=1300, kind="unit", lead=(2.8, 1.0, 2.6), res=150)
def s_horseshoe_shell():
    """Horseshoe crab (lead: Shell 2.8 x 1.0 x 2.6): a horseshoe-shaped domed prosoma with ridges and compound eye bumps,
    a hinged spiny opisthosoma behind."""
    s = ellipsoid(1.4, 0.5, 0.85, (0, 0, -0.35))
    s = s.su(ellipsoid(0.95, 0.38, 0.62, (0, -0.02, 0.7)), 0.12)
    s = s.su(capsule((0, 0.48, -0.9), (0, 0.42, 0.9), 0.05), 0.05)
    s = s.su(capsule((0.5, 0.36, -0.7), (0.4, 0.3, 0.1), 0.04).mirror_x(), 0.05)
    s = s.su(sphere(0.08, (0.55, 0.38, -0.5)).mirror_x(), 0.04)
    for i in range(4):
        z = 0.45 + i * 0.16
        s = s.su(round_cone((0.88 - i * 0.05, 0.0, z), (1.0 - i * 0.05, 0.0, z + 0.05), 0.04, 0.01).mirror_x(), 0.02)
    return s


@piece("s_anomalocaris_body", (0.72, 0.36, 1.9), tris=1100, kind="unit", lead=(1.3, 0.62, 3.6), res=150)
def s_anomalocaris_body():
    """Anomalocaris body (lead 1.3 x 0.62 x 3.6): a long flattened segmented trunk with a head shield."""
    return _banded_oval(1.3, 0.62, 3.6, 10)


@piece("s_snail_foot", (0.8, 0.45, 1.9), tris=900, kind="unit", lead=(1.4, 0.75, 3.6), res=140)
def s_snail_foot():
    """Snail foot (lead: Foot 1.4 x 0.75 x 3.6): a long muscle with a flat sole, wrinkled skin and a tapering tail."""
    s = ellipsoid(0.7, 0.375, 1.8)
    s = s & half_space(1, -1, -0.3)
    s = s.round(0.0)
    return s.noise(0.012, freq=12, seed=12)
