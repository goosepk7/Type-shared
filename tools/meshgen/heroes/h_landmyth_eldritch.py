"""Landmyth eldritch things: eldritch horror, void creature, planet eater, star eater, ophanim, black hole beast, taotie.

Part of the landmyth family (see h_landmyth.py for the shared helpers and the MAP). NOTE: build.py hashes only this
file + kit.py: after a change in h_landmyth.py helpers / h_monsters / mythic_geo rebuild with --force.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF
from kit import Hero, hero, stripes, spots, gradient, combine
import motion
import motion_landmyth as ml
import mythic_geo as mg
import h_monsters as HM
from h_landmyth import A, T, nrm, hard, feathers, feather_mask, feather_wing, tail_fan, bird_legs, human_ctx, human_head, crest_plumes, crown

# ================================================================================================ eldritch
def reach(H, c, r):
    """Unused pivot bones at the corners of the model: build.py searches pieces inside the bones' bounding box, so
    rings / debris / disks far from every bone need it widened."""
    c = A(*c)
    H.bone("ReachLo", "Body", T(c - A(r, r, r)))
    H.bone("ReachHi", "Body", T(c + A(r, r, r)))


def tentacle(H, name, parent, pts, radii, col="primary", tris=500, pri=1.4, pattern=None, suckers=0.0, tip=None, mat="skin"):
    """A tentacle along pts (one bone per segment: name1, name2 ...). Returns the bone names."""
    pts = [A(*p) for p in pts]
    bones = []
    for i in range(len(pts) - 1):
        b = f"{name}{i + 1}"
        H.bone(b, parent if i == 0 else bones[-1], T(pts[i]))
        bones.append(b)
        a = pts[i] - (pts[i + 1] - pts[i]) * (0.12 if i else 0.25)
        sg = round_cone(T(a), T(pts[i + 1]), radii[i], radii[i + 1])
        if suckers:
            sg = sg.noise(suckers, 1.0 / max(radii[i], 0.05) * 1.2, 30 + i)
        if tip is not None and i == len(pts) - 2:
            sg = sg | tip
        H.piece(f"{name}P{i + 1}", b, sg, col=col, mat=mat, tris=tris, role="tentacle", pri=pri + 0.1 * i, pattern=pattern)
    return bones


def eye_cluster(H, bone, center, eyes, name="Eyes", col="iris", pupil="slit", lid=None, glow=False):
    """Many eyes as two pieces: bulbs (iris colour) and pupils standing proud of them."""
    c = A(*center)
    bulbs, pups = [], []
    for p, r in eyes:
        p = A(*p)
        n = nrm(p - c)
        bulbs.append(sphere(r, T(p)))
        q = p + n * r * 0.82
        R = mg.frame(n, (0, 1, 0))
        rad = (r * 0.25, r * 0.12, r * 0.55) if pupil == "slit" else (r * 0.25, r * 0.4, r * 0.4)
        pups.append(mg.oell(q, R, rad))
        if lid:
            pass
    H.piece(name, bone, hard(bulbs), col=col, mat="glass" if glow else "hard", tris=900, role="eye", pri=1.2, ao=False)
    H.piece(name + "Pupils", bone, hard(pups), col="pupil", mat="hard", tris=700, role="pupil", pri=1.3, ao=False)


def surface_points(shape, center, dirs, step=0.02, rmax=6.0):
    """Points on shape's surface along rays from center."""
    c = A(*center)
    out = []
    for d in dirs:
        d = nrm(d)
        ts = np.arange(0, rmax, step)
        P = c + ts[:, None] * d
        val = shape(P)
        idx = np.argmax(val > 0)
        out.append(c + d * ts[max(idx - 1, 0)])
    return out


def fib_dirs(n, seed=0, ymin=-1.0, ymax=1.0, front=None):
    out = []
    g = math.pi * (3 - math.sqrt(5))
    rng = np.random.default_rng(seed)
    for i in range(n * 4):
        y = 1 - 2 * (i + 0.5) / (n * 4)
        r = math.sqrt(max(0, 1 - y * y))
        a = g * i + rng.uniform(-0.2, 0.2)
        d = A(r * math.cos(a), y, r * math.sin(a))
        if ymin <= y <= ymax and (front is None or d[2] <= front):
            out.append(d)
    idx = np.linspace(0, len(out) - 1, n).astype(int)
    return [out[i] for i in idx]


def debris(H, name, parent, center, radius, n, size, seed=0, tilt=(0, 0, 0), col="stone", mat="stone", y=0.0):
    """A ring of rocks on its own bone (swings around the centre)."""
    H.bone(name, parent, T(center))
    rng = np.random.default_rng(seed)
    rocks = []
    for i in range(n):
        a = i / n * math.tau + rng.uniform(-0.3, 0.3)
        p = A(math.cos(a) * radius, y + rng.uniform(-0.25, 0.25) * radius * 0.2, math.sin(a) * radius)
        r = size * rng.uniform(0.6, 1.3)
        rk = ellipsoid(r, r * rng.uniform(0.6, 0.9), r * rng.uniform(0.7, 1.0)).rot(*rng.uniform(0, 90, 3)).noise(r * 0.18, 3.0 / r, i)
        rocks.append(rk.at(*T(p)))
    rk = hard(rocks).rot(*tilt).at(*T(center))
    H.piece(name + "P", name, rk, col=col, mat=mat, tris=900, role="debris", pri=1.6)


def cosmic_specks(H, name, bone, center, radius, n, seed=0, col="secondary"):
    rng = np.random.default_rng(seed)
    sp = []
    for i in range(n):
        d = nrm(rng.normal(size=3))
        p = A(*center) + d * radius * rng.uniform(0.95, 1.05)
        sp.append(sphere(0.05 * rng.uniform(0.8, 1.6), T(p)))
    H.piece(name, bone, hard(sp), col=col, mat="hard", tris=500, role="detail", pri=2.0, ao=False)


@hero("eldritch horror", "landmyth")
def eldritch_horror():
    H = Hero("eldritch horror", plan="Blob", gait="hover", tags=["cosmic", "eldritch", "boss"])
    H.preview = {"primary": "#2A2560", "secondary": "#3FA34D", "iris": "#C8E04A"}
    c = A(0, 3.2, 0)
    H.body(T(c))
    H.bone("Core", "Body", T(c))
    core = ellipsoid(1.75, 1.6, 1.65, T(c))
    rng = np.random.default_rng(3)
    for i in range(9):
        d = nrm(rng.normal(size=3) * A(1, 0.7, 1) + A(0, 0.3, 0))
        core = core.su(sphere(rng.uniform(0.55, 0.9), T(c + d * 1.4)), 0.4)
    # maw: a vertical slit with folded lips on the front
    maw = ellipsoid(0.32, 0.95, 0.6, T(c + A(0, -0.25, -1.65)))
    core = core.ss(maw, 0.15)
    # crown of hooked spines on top
    for i in range(7):
        a = i / 7 * math.tau
        b = c + A(math.cos(a) * 0.9, 1.35, math.sin(a) * 0.9)
        core = core | mg.curved_horn([b, b + A(math.cos(a) * 0.3, 0.55, math.sin(a) * 0.3), b + A(math.cos(a) * 0.65, 0.75, math.sin(a) * 0.65)], 0.15, 0.02)
    core = core.noise(0.05, 2.2, 5)
    H.piece("CoreP", "Core", core, col="primary", mat="skin", tris=2600, res=136, role="body",
            pattern=combine(spots(0.5, 0.18, depth=0.35, seed=4), gradient(1, 1.6, 4.8, 0.7, 1.0)))
    H.bone("Maw", "Core", T(c + A(0, -0.25, -1.5)))
    teeth = []
    for i in range(7):
        y = -0.85 + i * 0.28
        for sx in (1, -1):
            b = c + A(sx * 0.32, -0.25 + y, -1.55 + 0.1 * abs(y))
            teeth.append(round_cone(T(b), T(b + A(-sx * 0.22, 0.0, -0.05)), 0.07, 0.01))
    H.piece("MawTeeth", "Maw", hard(teeth), col="tooth", mat="hard", tris=500, role="tooth", pri=1.6, ao=False)
    H.prim("MawDark", "Core", "Ellipsoid", (0.45, 1.7, 0.4), T(c + A(0, -0.25, -1.35)), col="mouth", mat="hard", role="mouth", pri=2.2)
    # eyes all over the front and sides
    dirs = fib_dirs(12, seed=5, ymin=-0.3, ymax=0.85, front=0.35)
    pts = surface_points(core, c, dirs)
    eye_cluster(H, "Core", c, [(p - nrm(p - c) * 0.08, 0.16 + 0.12 * ((i * 7) % 5) / 4) for i, p in enumerate(pts) if abs((p - c)[0]) > 0.45 or (p - c)[1] > 0.4])
    H.bone("BigEye", "Core", T(c + A(0, 0.75, -1.35)))
    H.prim("BigEyeBall", "BigEye", "Ball", (0.62, 0.62, 0.62), T(c + A(0, 0.75, -1.35)), col="iris", mat="hard", role="eye", pri=1.1)
    H.prim("BigPupil", "BigEye", "Ellipsoid", (0.14, 0.46, 0.14), T(c + A(0, 0.75, -1.64)), col="pupil", mat="hard", role="pupil", pri=1.2)
    # tentacles hanging to the ground
    chains = []
    for i in range(6):
        a = math.radians(30 + i * 60)
        r0 = c + A(math.cos(a) * 1.15, -1.05, math.sin(a) * 1.15)
        d = A(math.cos(a), 0, math.sin(a))
        pts = [r0, r0 + d * 0.7 + A(0, -0.9, 0), r0 + d * 1.5 + A(0, -1.6, 0), r0 + d * 2.4 + A(0, -1.6, 0) + A(0, 0.35, 0)]
        chains.append(tentacle(H, f"T{i}", "Core", pts, [0.36, 0.27, 0.18, 0.05], col="primary", tris=380, suckers=0.025,
                               pattern=gradient(1, 0.0, 3.0, 0.75, 1.0)))
    cosmic_specks(H, "Stars", "Core", c, 1.95, 26, seed=2)
    H.socket("mouth", T(c + A(0, -0.25, -1.8)), "Maw")
    H.socket("head", T(c + A(0, 2.0, 0)), "Core")
    H.rig.update({"head": "Core", "tail": []})
    ml.mass_float(H, tentacles=chains, eyes=["BigEye"], swirl=[], core="Core", jaw=None, height=5.5, hover=0.1, attack="lash",
                  extra=lambda nm, u, pose: ml._add(pose, "Maw", (0, 0, 0, 0, 0, 0)))
    return H


@hero("void creature", "landmyth")
def void_creature():
    H = Hero("void creature", plan="Ghost", gait="hover", tags=["cosmic", "spooky"])
    H.preview = {"primary": "#14142E", "secondary": "#B9A6FF", "white": "#F4F4FF"}
    H.body((0, 2.6, 0))
    H.bone("Torso", "Body", (0, 2.6, 0))
    H.bone("Head", "Torso", (0, 4.0, -0.05))
    body = round_cone((0, 1.05, 0.1), (0, 3.35, 0.0), 0.32, 0.72)
    body = body.su(ellipsoid(0.95, 0.5, 0.5, (0, 3.45, 0.0)), 0.3)
    body = body.su(round_cone((0, 3.6, 0), (0, 3.95, -0.05), 0.35, 0.22), 0.15)
    rng = np.random.default_rng(7)
    for i in range(6):   # ragged wisps trailing from the hem
        a = i / 6 * math.tau
        b = A(math.cos(a) * 0.3, 1.25, math.sin(a) * 0.3 + 0.1)
        body = body.su(round_cone(T(b), T(b + A(math.cos(a) * 0.35, -0.9 - 0.2 * (i % 2), math.sin(a) * 0.35 + 0.25)), 0.16, 0.02), 0.12)
    H.piece("BodyP", "Torso", body.noise(0.02, 4.0, 3), col="primary", mat="skin", tris=1800, res=128, role="body",
            pattern=gradient(1, 0.6, 3.0, 0.55, 1.0))
    hd = ellipsoid(0.48, 0.58, 0.48, (0, 4.4, -0.05))
    for i in range(5):   # crown of horn-like spikes
        a = math.radians(-60 + i * 30)
        b = A(math.sin(a) * 0.38, 4.75, 0.05 + 0.1 * abs(math.sin(a)))
        hd = hd.su(round_cone(T(b), T(b + A(math.sin(a) * 0.45, 0.65 - 0.1 * abs(i - 2), 0.25)), 0.1, 0.012), 0.05)
    hd = hd.ss(ellipsoid(0.16, 0.1, 0.12, (0.18, 4.42, -0.48)).mirror_x(), 0.04)
    H.piece("HeadP", "Head", hd, col="primary", mat="skin", tris=1200, role="head")
    for sx, nm in ((1, "R"), (-1, "L")):
        H.prim("Eye" + nm, "Head", "Ellipsoid", (0.22, 0.13, 0.12), (sx * 0.18, 4.42, -0.43), rot=(0, 0, -sx * 0.25), col="white", mat="hard", glow=True, role="eye", pri=1.1)
    cosmic_specks(H, "Stars", "Torso", (0, 2.9, 0), 0.62, 30, seed=4, col="secondary")
    chains = []
    for sx, nm in ((1, "R"), (-1, "L")):
        sh = A(sx * 0.82, 3.45, 0.0)
        pts = [sh, sh + A(sx * 0.35, -0.75, -0.1), sh + A(sx * 0.45, -1.55, -0.3), sh + A(sx * 0.4, -2.2, -0.6)]
        claw = hard([round_cone(T(pts[-1]), T(pts[-1] + A(sx * dx, -0.35, -0.25)), 0.05, 0.008) for dx in (-0.12, 0.0, 0.12)])
        chains.append(tentacle(H, "Arm" + nm, "Torso", pts, [0.2, 0.14, 0.1, 0.06], col="primary", tris=380, tip=claw,
                               pattern=gradient(1, 0.8, 3.4, 0.7, 1.0)))
    H.socket("mouth", (0, 4.3, -0.5), "Head")
    H.socket("head", (0, 5.0, 0), "Head")
    H.rig.update({"head": "Head", "tail": []})
    ml.mass_float(H, tentacles=chains, eyes=["Head"], core="Torso", height=5.0, hover=0.12, attack="lash", pulse=0.015)
    return H


def _devourer(hid, kind, preview):
    H = Hero(hid, plan="Blob", gait="hover", tags=["cosmic", "boss", "alien"])
    H.preview = preview
    c = A(0, 3.4, 0)
    H.body(T(c))
    reach(H, c, 4.5)
    H.bone("Core", "Body", T(c))
    R = 2.0
    if kind == "planet":
        # a cratered moon whose lower half is a hinged jaw
        sph = sphere(R, T(c))
        cr = sph
        rng = np.random.default_rng(11)
        for i in range(10):
            d = nrm(rng.normal(size=3))
            if d[2] < -0.2 and d[1] < 0.3:
                continue
            cr = cr.ss(sphere(rng.uniform(0.3, 0.55), T(c + d * (R + 0.15))), 0.12)
        cr = cr.noise(0.05, 1.8, 3)
        top = cr & plane((0, -1, 0), -float(c[1] - 0.15))
        top = top.ss(ellipsoid(1.55, 0.7, 1.4, T(c + A(0, -0.15, -0.75))), 0.2)   # mouth cavity
        H.piece("Shell", "Core", top, col="primary", mat="stone", tris=2400, res=136, role="body",
                pattern=combine(spots(0.7, 0.3, depth=0.3, ring=True, seed=3), gradient(1, 1.4, 5.4, 0.8, 1.0)))
        H.bone("Jaw", "Core", T(c + A(0, -0.1, 1.1)))
        low = (cr & plane((0, 1, 0), float(c[1] - 0.25))).ss(ellipsoid(1.5, 0.75, 1.35, T(c + A(0, -0.25, -0.75))), 0.2)
        H.piece("JawP", "Jaw", low, col="primary", mat="stone", tris=1800, res=128, role="jaw", pri=1.2,
                pattern=combine(spots(0.7, 0.3, depth=0.3, ring=True, seed=5), gradient(1, 1.4, 5.4, 0.8, 1.0)))
        up_t, lo_t = [], []
        for i in range(13):
            a = math.radians(-80 + i * 160 / 12)
            p = c + A(math.sin(a) * 1.55, -0.12, -math.cos(a) * 1.4 - 0.4)
            up_t.append(round_cone(T(p + A(0, 0.15, 0)), T(p + A(0, -0.35, 0)), 0.13, 0.015))
            q = c + A(math.sin(a) * 1.45, -0.32, -math.cos(a) * 1.3 - 0.4)
            lo_t.append(round_cone(T(q - A(0, 0.1, 0)), T(q + A(0, 0.28, 0)), 0.11, 0.015))
        H.piece("TeethUp", "Core", hard(up_t), col="tooth", mat="hard", tris=700, role="tooth", pri=1.5, ao=False)
        H.piece("TeethLow", "Jaw", hard(lo_t), col="tooth", mat="hard", tris=600, role="tooth", pri=1.5, ao=False)
        H.prim("Throat", "Core", "Ellipsoid", (2.4, 0.5, 2.0), T(c + A(0, -0.2, -0.3)), col="mouth", mat="hard", role="mouth", pri=2.2)
        H.bone("Eye", "Core", T(c + A(0, 1.05, -1.55)))
        H.prim("EyeBall", "Eye", "Ball", (0.9, 0.9, 0.9), T(c + A(0, 1.05, -1.55)), col="secondary", mat="hard", role="eye", pri=1.1)
        H.prim("EyePupil", "Eye", "Ellipsoid", (0.2, 0.62, 0.2), T(c + A(0, 1.05, -1.98)), col="pupil", mat="hard", role="pupil", pri=1.2)
        eyes = [(c + nrm(A(sx * 0.55, 0.5, -0.8)) * (R - 0.05), 0.2) for sx in (1, -1)] + [(c + nrm(A(sx * 0.8, 0.9, -0.5)) * (R - 0.05), 0.15) for sx in (1, -1)]
        eye_cluster(H, "Core", c, eyes, col="secondary")
        jaw = "Jaw"
        troots = [(math.radians(a), e) for a, e in ((150, 0.1), (210, 0.1), (110, -0.4), (250, -0.4))]
    else:
        # star eater: a lamprey funnel maw at the front with rings of teeth, the body tapering back into tentacles
        body = round_cone(T(c + A(0, 0, -1.2)), T(c + A(0, 0.1, 1.6)), R * 1.05, 0.7)
        body = body.su(sphere(R * 0.95, T(c + A(0, 0, -0.5))), 0.5)
        funnel = cone(R * 0.95, 0.25, 1.2, axis=2).at(*T(c + A(0, 0, -1.6)))
        body = body.ss(funnel, 0.15)
        rings = []
        for k, (rr, zz) in enumerate(((1.75, -2.1), (1.25, -1.75), (0.8, -1.4))):
            for i in range(16 - 4 * k):
                a = i / (16 - 4 * k) * math.tau
                p = c + A(math.cos(a) * rr, math.sin(a) * rr, zz)
                rings.append(round_cone(T(p), T(p + A(-math.cos(a) * 0.35, -math.sin(a) * 0.35, 0.15)), 0.1, 0.012))
        body = body.noise(0.04, 2.0, 9)
        rib = stripes(lambda Q: Q[:, 2], 2.2, width=0.25, depth=0.3, seed=1)
        H.piece("Shell", "Core", body, col="primary", mat="skin", tris=2400, res=136, role="body", pattern=combine(rib, gradient(1, 1.2, 5.6, 0.75, 1.0)))
        H.bone("Jaw", "Core", T(c + A(0, 0, -1.7)))
        H.piece("TeethRings", "Jaw", hard(rings), col="tooth", mat="hard", tris=1200, role="tooth", pri=1.4, ao=False)
        H.prim("Throat", "Core", "Ball", (1.5, 1.5, 0.6), T(c + A(0, 0, -0.95)), col="mouth", mat="hard", role="mouth", pri=2.2)
        dirs = [nrm(A(math.cos(a), math.sin(a), -0.55)) for a in np.linspace(0, math.tau, 9)[:-1]]
        pts = [c + A(math.cos(a) * 2.05, math.sin(a) * 2.05, -1.5) for a in np.linspace(0.2, math.tau + 0.2, 9)[:-1]]
        eye_cluster(H, "Core", c + A(0, 0, -1.5), [(p, 0.2) for p in pts], col="secondary")
        jaw = None
        troots = [(math.radians(a), e) for a, e in ((45, 0.0), (135, 0.0), (225, 0.0), (315, 0.0))]
    chains = []
    for i, (a, e) in enumerate(troots):
        d = A(math.cos(a), math.sin(a) * 0.8 + e, 0)
        r0 = c + d * (R * 0.55) + A(0, 0, 1.3)
        pts = [r0, r0 + d * 0.6 + A(0, 0, 1.0), r0 + d * 1.1 + A(0, -0.2, 1.9), r0 + d * 1.3 + A(0, -0.5, 2.8)]
        chains.append(tentacle(H, f"T{i}", "Core", pts, [0.4, 0.3, 0.2, 0.06], col="primary", tris=380, suckers=0.02))
    debris(H, "DebrisA", "Body", c, 3.1, 7, 0.32, seed=1, tilt=(18, 0, 10))
    debris(H, "DebrisB", "Body", c, 3.7, 5, 0.25, seed=2, tilt=(-25, 0, -15), col="secondary" if kind == "star" else "stone", mat="stone")
    H.socket("mouth", T(c + A(0, -0.1, -2.2)), "Jaw" if jaw else "Core")
    H.socket("head", T(c + A(0, 2.2, 0)), "Core")
    H.rig.update({"head": "Core", "tail": []})
    if jaw:
        H.rig["jaw"] = jaw
    ml.mass_float(H, tentacles=chains, eyes=["Eye"] if kind == "planet" else [], core="Core", jaw=jaw, height=6.5, hover=0.15,
                  swirl=[("DebrisA", 4, 0.9, 1), ("DebrisB", 4, -1.1, 1)], attack="lash")
    return H


@hero("planet eater", "landmyth")
def planet_eater():
    return _devourer("planet eater", "planet", {"primary": "#3A3466", "secondary": "#DC2626", "stone": "#6E6A78", "tooth": "#EDE6D6"})


@hero("star eater", "landmyth")
def star_eater():
    return _devourer("star eater", "star", {"primary": "#1E1E3A", "secondary": "#F97316", "stone": "#5A5868", "tooth": "#F2E8D8"})


@hero("ophanim", "landmyth")
def ophanim():
    H = Hero("ophanim", plan="Orb", gait="hover", tags=["holy", "angel"])
    H.preview = {"primary": "#E8B53A", "secondary": "#E0F2FE", "iris": "#4A90D9"}
    c = A(0, 3.2, 0)
    H.body(T(c))
    reach(H, c, 2.6)
    swirl = []
    for k, (R, rot) in enumerate(((1.9, (90, 0, 0)), (1.6, (90, 90, 0)), (1.3, (0, 0, 0)))):
        nm = f"Ring{k + 1}"
        H.bone(nm, "Body", T(c))
        ring = torus(R, 0.17, axis=1).scale3(1, 1.5, 1)
        ring = ring.su(torus(R, 0.1, axis=1).at(0, 0.18, 0) | torus(R, 0.1, axis=1).at(0, -0.18, 0), 0.04)
        Rm = np.array(__import__("sdf")._rotm(*rot))
        eyes = []
        n = 10 - 2 * k
        for i in range(n):
            a = (i + 0.5) / n * math.tau
            p_loc = A(math.cos(a) * (R + 0.18), 0, math.sin(a) * (R + 0.18))
            eyes.append((c + Rm @ p_loc, 0.18))
        H.piece(nm + "P", nm, ring.rot(*rot).at(*T(c)), col="primary", mat="metal", tris=1100, res=128, role="body", pri=1.0 + 0.05 * k,
                pattern=stripes(lambda Q: np.arctan2(Q[:, 1] - c[1], Q[:, 0]) * 3, 1.0, width=0.1, depth=0.2))
        bulbs, pups = [], []
        for p, r in eyes:
            nrm_ = nrm(p - c)
            bulbs.append(sphere(r, T(p)))
            q = p + nrm_ * r * 0.9
            pups.append(mg.oell(q, mg.frame(nrm_, (0, 1, 0)), (r * 0.18, r * 0.45, r * 0.45)))
        H.piece(nm + "Eyes", nm, hard(bulbs), col="eyeWhite", mat="hard", tris=700, role="eye", pri=1.3, ao=False)
        H.piece(nm + "Irises", nm, hard(pups), col="iris", mat="hard", tris=600, role="pupil", pri=1.4, ao=False)
        swirl.append((nm, 3 + (k % 3), (1.0 - 0.15 * k) * (1 if k % 2 == 0 else -1), 1))
    # the heart: a great eye in a glowing sphere of feathers
    H.bone("Heart", "Body", T(c))
    core = sphere(0.75, T(c))
    items = []
    for i, d in enumerate(fib_dirs(14, seed=3)):
        items.append((c + d * 0.55, d, 0.55, 0.14))
    H.piece("Plumes", "Heart", core.su(feathers(items, (0, 1, 0), th=0.03), 0.05), col="secondary", mat="cloth", tris=1500, role="body", pri=1.1)
    H.prim("HeartEye", "Heart", "Ball", (0.62, 0.62, 0.62), T(c + A(0, 0, -0.62)), col="eyeWhite", mat="hard", role="eye", pri=1.2)
    H.prim("HeartIris", "Heart", "Ball", (0.4, 0.4, 0.4), T(c + A(0, 0, -0.84)), col="iris", mat="hard", role="eye", pri=1.25)
    H.prim("HeartPupil", "Heart", "Ball", (0.2, 0.2, 0.2), T(c + A(0, 0, -0.98)), col="pupil", mat="hard", role="pupil", pri=1.3)
    H.prim("Glint", "Heart", "Ball", (0.1, 0.1, 0.1), T(c + A(0.1, 0.12, -1.03)), col="shine", mat="hard", role="shine", pri=2.0)
    H.socket("mouth", T(c + A(0, 0, -1.0)), "Heart")
    H.socket("head", T(c + A(0, 2.2, 0)), "Body")
    H.rig.update({"head": "Heart", "tail": []})
    ml.mass_float(H, eyes=["Heart"], swirl=swirl, height=5.0, hover=0.15, attack="gaze", pulse=0.0)
    return H


@hero("black hole beast", "landmyth")
def black_hole_beast():
    H = Hero("black hole beast", plan="Orb", gait="hover", tags=["cosmic", "boss"])
    H.preview = {"primary": "#08080C", "secondary": "#7C3AED", "tooth": "#EDE6F6", "iris": "#E8D8FF"}
    c = A(0, 3.3, 0)
    H.body(T(c))
    reach(H, c, 4.2)
    H.bone("Core", "Body", T(c))
    sph = sphere(1.55, T(c)).ss(ellipsoid(1.0, 1.0, 0.6, T(c + A(0, 0, -1.55))), 0.2)
    H.piece("Sphere", "Core", sph, col="primary", mat="hard", tris=1600, role="body")
    teeth = []
    for k, rr in enumerate((1.12, 0.82)):
        n = 18 - 6 * k
        for i in range(n):
            a = (i + 0.5 * k) / n * math.tau
            p = c + A(math.cos(a) * rr, math.sin(a) * rr, -1.15 + 0.2 * k)
            teeth.append(round_cone(T(p), T(p + A(-math.cos(a) * 0.4, -math.sin(a) * 0.4, 0.2)), 0.11 - 0.02 * k, 0.012))
    H.bone("Maw", "Core", T(c + A(0, 0, -1.2)))
    H.piece("ToothRing", "Maw", hard(teeth), col="tooth", mat="hard", tris=1100, role="tooth", pri=1.3, ao=False)
    H.prim("Void", "Core", "Ball", (1.7, 1.7, 0.4), T(c + A(0, 0, -1.0)), col="black", mat="hard", role="mouth", pri=2.0)
    # accretion disk in two counter-swinging bands, cut in spiral arms
    for k, (R0, R1, tilt) in enumerate(((2.0, 2.9, 12), (3.0, 3.8, -8))):
        nm = f"Disk{k + 1}"
        H.bone(nm, "Body", T(c))

        def disk(p, R0=R0, R1=R1):
            r = np.linalg.norm(p[:, [0, 2]], axis=1)
            a = np.arctan2(p[:, 2], p[:, 0])
            arm = 0.09 * np.sin(3 * a + r * 2.2)
            th = 0.06 + 0.05 * np.clip((R1 - r) / (R1 - R0), 0, 1) + arm * 0.6
            return np.maximum(np.maximum(R0 - r, r - R1), np.abs(p[:, 1]) - np.maximum(th, 0.03))
        dk = mg.bounded(SDF(disk), (-R1, -0.4, -R1), (R1, 0.4, R1)).rot(tilt, 0, 6 * (1 if k else -1)).at(*T(c))
        H.piece(nm + "P", nm, dk, col="secondary", mat="hard", tris=1400, res=128, role="body", pri=1.2 + 0.1 * k,
                pattern=stripes(lambda Q: np.arctan2(Q[:, 2], Q[:, 0]) * 3 / math.tau + np.linalg.norm(Q[:, [0, 2]], axis=1) * 0.35, 1.0, width=0.35, depth=0.45))
    # three eyes over the maw and grasping tendrils
    eye_cluster(H, "Core", c, [(c + nrm(A(0, 0.95, -0.7)) * 1.48, 0.24), (c + nrm(A(0.7, 0.75, -0.6)) * 1.48, 0.17), (c + nrm(A(-0.7, 0.75, -0.6)) * 1.48, 0.17)], col="iris", pupil="slit")
    chains = []
    for i, a in enumerate((200, 270, 340)):
        q = math.radians(a)
        d = A(math.cos(q), math.sin(q), 0)
        r0 = c + d * 1.25 + A(0, 0, 0.5)
        pts = [r0, r0 + d * 0.9 + A(0, 0, 0.5), r0 + d * 1.6 + A(0, 0, 0.3), r0 + d * 2.1 + A(0, 0, -0.3)]
        chains.append(tentacle(H, f"T{i}", "Core", pts, [0.3, 0.22, 0.14, 0.04], col="primary", tris=350))
    cosmic_specks(H, "Sparks", "Disk1", c, 3.0, 20, seed=8, col="white")
    H.socket("mouth", T(c + A(0, 0, -1.6)), "Maw")
    H.socket("head", T(c + A(0, 1.8, 0)), "Core")
    H.rig.update({"head": "Core", "tail": []})
    ml.mass_float(H, tentacles=chains, core="Core", swirl=[("Disk1", 4, 1.2, 1), ("Disk2", 4, -0.9, 2)], height=5.5, hover=0.15, attack="lash",
                  extra=lambda nm, u, pose: ml._add(pose, "Maw", (0, 0, 0, 0, 0, 0.6 * math.sin(math.tau * u * (2 if nm != "Attack" else 3)))))
    return H


@hero("taotie", "landmyth")
def taotie():
    H = Hero("taotie", plan="Blob", gait="hover", tags=["myth", "chinese"])
    H.preview = {"primary": "#7A3A1C", "secondary": "#C9962A", "horn": "#C9962A", "tooth": "#F2EAD4", "iris": "#E8B423"}
    c = A(0, 3.3, 0)
    H.body(T(c))
    reach(H, c, 3.0)
    H.bone("Face", "Body", T(c))
    # a broad mask: brow shelf, bulging eye mounds, flared nose, cheeks swept back; no body behind
    f = ellipsoid(1.75, 1.3, 0.85, T(c + A(0, 0.1, 0.1)))
    f = f.su(capsule(T(c + A(-1.25, 0.55, -0.55)), T(c + A(1.25, 0.55, -0.55)), 0.3), 0.25)              # brow shelf
    f = f.su(ellipsoid(0.42, 0.36, 0.3, T(c + A(0.62, 0.15, -0.72))).mirror_x(), 0.15)                    # eye mounds
    f = f.su(ellipsoid(0.45, 0.42, 0.45, T(c + A(0, -0.15, -0.85))), 0.2)                                 # nose
    f = f.ss(sphere(0.12, T(c + A(0.2, -0.3, -1.22))).mirror_x(), 0.05)                                  # nostrils
    f = f.su(ellipsoid(0.55, 0.75, 0.5, T(c + A(1.55, -0.2, -0.1))).mirror_x(), 0.3)                     # cheeks
    for sx in (1, -1):   # flame-like scrolls at the sides
        for i in range(3):
            b = c + A(sx * (1.6 + 0.2 * i), 0.65 - 0.55 * i, 0.15)
            f = f.su(mg.curved_horn([b, b + A(sx * 0.45, 0.25, 0.1), b + A(sx * 0.65, 0.05, 0.2), b + A(sx * 0.55, -0.15, 0.25)], 0.17, 0.04), 0.08)
    f = f & plane((0, -1, 0), -float(c[1] - 0.75))
    f = f.ss(ellipsoid(1.0, 0.25, 0.6, T(c + A(0, -0.72, -0.75))), 0.08)
    spiral = stripes(lambda Q: np.sqrt((Q[:, 0] - np.sign(Q[:, 0]) * 0.62) ** 2 + (Q[:, 1] - c[1] - 0.15) ** 2) + 0.12 * np.arctan2(Q[:, 1] - c[1] - 0.15, np.abs(Q[:, 0]) - 0.62),
                     3.2, width=0.18, depth=0.3, seed=2)
    H.piece("Mask", "Face", f.noise(0.012, 6.0, 4), col="primary", mat="metal", tris=2600, res=140, role="head", pattern=spiral)
    # horns: thick, curling outward and up (gold bronze)
    for sx, nm in ((1, "R"), (-1, "L")):
        pass
    horn = mg.curved_horn([c + A(0.75, 1.0, -0.2), c + A(1.35, 1.75, -0.1), c + A(2.1, 2.0, 0.2), c + A(2.45, 1.55, 0.35), c + A(2.25, 1.15, 0.25)], 0.36, 0.06)
    H.mpiece("Horn#", "Face", horn, col="horn", mat="metal", tris=900, role="horn", pri=1.3,
             pattern=stripes(lambda Q: np.linalg.norm(Q - (c + A(0.75, 1.0, -0.2)), axis=1), 4.0, width=0.2, depth=0.3))
    # jaw with fangs
    H.bone("Jaw", "Face", T(c + A(0, -0.6, 0.2)))
    jw = ellipsoid(1.2, 0.45, 0.7, T(c + A(0, -1.0, -0.3))) & plane((0, 1, 0), float(c[1] - 0.78))
    jw = jw.su(ellipsoid(0.45, 0.3, 0.3, T(c + A(0.95, -0.95, -0.55))).mirror_x(), 0.15)
    H.piece("JawP", "Jaw", jw.noise(0.012, 6.0, 5), col="primary", mat="metal", tris=1200, role="jaw", pri=1.2)
    H.prim("Throat", "Face", "Ellipsoid", (1.9, 0.35, 1.0), T(c + A(0, -0.78, -0.45)), col="mouth", mat="hard", role="mouth", pri=2.2)
    up = []
    for i, x in enumerate((-0.75, -0.45, -0.15, 0.15, 0.45, 0.75)):
        ln = 0.42 if abs(x) > 0.6 else 0.22
        up.append(round_cone(T(c + A(x, -0.65, -0.98 + 0.12 * abs(x))), T(c + A(x * 0.95, -0.65 - ln, -1.0 + 0.12 * abs(x))), 0.09, 0.015))
    H.piece("Fangs", "Face", hard(up), col="tooth", mat="hard", tris=500, role="tooth", pri=1.5, ao=False)
    lo = [round_cone(T(c + A(x, -0.85, -0.85 + 0.15 * abs(x))), T(c + A(x * 0.9, -0.62, -0.9 + 0.15 * abs(x))), 0.08, 0.015) for x in (-0.95, -0.55, 0.55, 0.95)]
    H.piece("JawTeeth", "Jaw", hard(lo), col="tooth", mat="hard", tris=400, role="tooth", pri=1.6, ao=False)
    H.eyes("Face", T(c + A(0.62, 0.17, -0.98)), 0.24, col="iris", pupil="round", look=(0.2, 0.0, -1.0))
    # two clawed forelegs under the jaw (the bronze-vessel taotie)
    for sx, nm in ((1, "R"), (-1, "L")):
        sh = c + A(sx * 1.1, -0.5, 0.2)
        pts = [sh, sh + A(sx * 0.35, -0.7, -0.3), sh + A(sx * 0.3, -1.3, -0.6)]
        cl = hard([mg.curved_horn([pts[-1] + A(dx, 0, 0), pts[-1] + A(dx * 1.4, -0.15, -0.3), pts[-1] + A(dx * 1.5, -0.35, -0.35)], 0.06, 0.01) for dx in (-0.14, 0.0, 0.14)])
        tentacle(H, "Leg" + nm, "Face", pts, [0.26, 0.18, 0.15], col="primary", tris=450, tip=cl, mat="metal")
    H.socket("mouth", T(c + A(0, -0.8, -1.2)), "Jaw")
    H.socket("head", T(c + A(0, 1.5, 0)), "Face")
    H.rig.update({"head": "Face", "jaw": "Jaw", "tail": []})
    ml.mass_float(H, tentacles=[["LegR1", "LegR2"], ["LegL1", "LegL2"]], core=None, jaw="Jaw", height=5.0, hover=0.15, attack="lash",
                  drift_pitch=-0.08)
    return H


