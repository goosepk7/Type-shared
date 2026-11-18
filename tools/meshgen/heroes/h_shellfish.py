"""Shellfish & odd sea critters: bivalves (clam, giant clam, oyster, scallop, mussel, geoduck, shipworm), sea snails and
cap shells (conch, whelk, cowrie, limpet, abalone, chiton), squishy crawlers (sea cucumber, sea pig, sea mouse,
blobfish), colonial / gelatinous drifters (salp, siphonophore, pyrosome), sessile tubes (sea squirt, hydra polyp,
giant tube worm, feather duster worm, christmas tree worm), armoured crawlers (isopod, pill bug, trilobite, opabinia)
and the tadpole.

Bivalve valves are hollow domes cut at the gape plane (ribs, growth ridges and wavy interlocking margins are
displacements of the outer surface), hinged on their own bone so they really open and clap (motion_shellfish).
Spiral shells are helico-spiral tubes of spheres (whorls translate along the spire axis). Armoured crawlers are
chains of overlapping tergite plates pivoted near the dorsal surface so they can enroll into a ball.
"""
import math

import numpy as np

import sdf as S
from sdf import sphere, ellipsoid, capsule, round_cone, tube, torus  # noqa: F401
from kit import Hero, hero, stripes, spots, gradient, combine  # noqa: F401
import motion_shellfish as MS
import motion_aquatic as MA
from motion_aquatic import plate, overlay, union_all

FAM = "shellfish"
TAU = 2 * math.pi


def V(*a):
    if len(a) == 1:
        return np.array(a[0], float)
    return np.array(a, float)


def T(v):
    return tuple(float(x) for x in v)


def frame(sd, o, ex, ey, ez):
    """Place a sculpt authored in a local frame (x, y, z) at origin o with world axes ex, ey, ez (orthonormal)."""
    o, ex, ey, ez = V(o), V(ex), V(ey), V(ez)

    def f(P):
        Q = P - o
        return sd(np.column_stack([Q @ ex, Q @ ey, Q @ ez]))

    return S.SDF(f)


def lpat(fn, o, ex, ey, ez):
    """A pattern authored in the same local frame."""
    o, ex, ey, ez = V(o), V(ex), V(ey), V(ez)

    def f(P):
        Q = P - o
        return fn(np.column_stack([Q @ ex, Q @ ey, Q @ ez]))

    return f


def bounds(H, lo, hi):
    """Explicit sampling box for the hero's pieces (the bone-based hint is too tight for wide shells)."""
    lo, hi = V(lo), V(hi)
    H.bounds_hint = lambda: (lo, hi)


def surface_pts(sd, n, xr, zr, ytop, ybot, seed=0, step=0.01, below=0.0):
    """n points on the top surface of sd: random (x, z) in the ranges, marching down from ytop to the first hit."""
    rng = np.random.default_rng(seed)
    out = []
    ys = np.arange(ytop, ybot, -step)
    tries = 0
    while len(out) < n and tries < n * 30:
        tries += 1
        x, z = rng.uniform(*xr), rng.uniform(*zr)
        P = np.column_stack([np.full(len(ys), x), ys, np.full(len(ys), z)])
        d = sd(P)
        hit = np.argmax(d < 0)
        if d[hit] < 0 and hit > 0:
            out.append(V(x, ys[hit] - below, z))
    return out


def _ell(P, a, b, c):
    q = P / np.array([a, b, c])
    k0 = np.linalg.norm(q, axis=1)
    k1 = np.linalg.norm(P / np.array([a * a, b * b, c * c]), axis=1)
    return np.where(k1 > 1e-9, k0 * (k0 - 1.0) / np.maximum(k1, 1e-9), -min(a, b, c))


# ================================================================================================ bivalve valves
def valve(L, W, D, up=1, taper=0.15, ribs=0, rib_amp=0.0, growth=0.0, growth_amp=0.0, wavy=0, wavy_amp=0.0, thick=0.1,
          gap=0.015, umbo=0.3, bend=0.0, ears=0.0, lining=False, rough=0.0, seed=0, cupped=1.0, shingle=0.0):
    """One valve in its local frame: gape plane y = 0, the valve bulging toward up * y, the hinge at the back (+z),
    the lip at the front (-z). L / W / D: half length (z), half width (x), depth. ribs: radial ribs fanning from the
    hinge; growth: concentric ridges; wavy: margin folds that interlock with the opposite valve (sign from up).
    Returns the shell SDF (or (shell, nacre lining) when lining)."""
    hz = L * 0.92

    def warp(P):
        x, y, z = P[:, 0], P[:, 1] * up, P[:, 2]
        zz = np.clip(z / L, -1.2, 1.2)
        s = 1 + taper * (-zz)
        x = x - bend * (z / L) ** 2 * W
        return x / s, y, z, s

    def fan(x, z):
        ang = np.arctan2(x, (hz - z) + 1e-6)
        dist = np.hypot(x, hz - z)
        return ang, dist

    def outer(P):
        x, y, z, s = warp(P)
        q = np.column_stack([x, y / cupped, z])
        d = _ell(q, W, D, L) * min(1.0, cupped)
        ang, dist = fan(P[:, 0], z)
        fade = np.clip(dist / (0.45 * L), 0, 1)
        if ribs:
            r = np.cos(ribs * ang)
            d = d - rib_amp * fade * (0.5 + 0.5 * np.sign(r) * np.abs(r) ** 0.7)
        if growth:
            d = d - growth_amp * fade * np.abs(np.sin(dist * growth)) ** 3
        if shingle:
            # frilly overlapping growth layers: a sawtooth terrace, each layer's edge lifting away from the next
            w = 0.6 * np.sin(ang * 5 + seed) + 0.4 * np.sin(ang * 11 + 2 * seed)
            fr = np.mod(dist * growth * 0.25 + 0.15 * w, 1.0)
            d = d - shingle * fade * fr
        if rough:
            d = d - rough * (np.sin(P[:, 0] * 5.1 + seed) * np.sin(P[:, 2] * 4.3 + 2 * seed) + 0.5 * np.sin(P[:, 0] * 9.7 - P[:, 2] * 8.1 + seed))
        if umbo:
            u = np.linalg.norm(np.column_stack([x, y - D * 0.38, z - (hz - 0.12 * L)]) / np.array([W * 0.35, D * 0.55, L * 0.22]), axis=1) - 1
            d = S.smin(d, u * min(W * 0.35, D * 0.55, L * 0.22) * umbo / 0.3, 0.12)
        if ears:
            e = np.maximum(np.maximum(np.abs(x) - W * ears, np.abs(y - 0.05) - 0.07), np.maximum(z - (hz + 0.1 * L), (hz - 0.3 * L) - z))
            tri = (np.abs(x) - W * ears) + (hz + 0.1 * L - z) * 0.6
            e = np.maximum(e, tri)
            d = S.smin(d, e, 0.05)
        return d

    def inner(P, t):
        x, y, z, s = warp(P)
        q = np.column_stack([x, y / cupped, z])
        return _ell(q, W - t, max(D - t, 0.05), L - t) * min(1.0, cupped)

    def edge(P):
        if not wavy:
            return np.zeros(len(P))
        ang, dist = fan(P[:, 0], P[:, 2])
        return wavy_amp * np.cos(wavy * ang) * np.clip(dist / (0.6 * L), 0, 1)

    def shell(P):
        y = P[:, 1] * up
        d = np.maximum(outer(P), -inner(P, thick * (0.55 if lining else 1.0)))
        cut = (edge(P) * up + gap) - y
        return np.maximum(d, cut)

    sh = S.SDF(shell)
    if not lining:
        return sh

    def nacre(P):
        y = P[:, 1] * up
        d = np.maximum(inner(P, thick * 0.55 + 0.0) - 0.004, -inner(P, thick))
        cut = (edge(P) * up + gap + 0.03) - y
        return np.maximum(d, cut)

    return sh, S.SDF(nacre)


def growth_pat(L, hz_k=0.92, freq=9.0, depth=0.25, ribs=0, rib_depth=0.0, bands=0.0):
    """Shell colour: concentric growth bands (+ optional rib shading / colour bands), in the valve's local frame."""
    hz = L * hz_k

    def f(Q):
        dist = np.hypot(Q[:, 0], hz - Q[:, 2])
        m = 1 - depth * np.clip(np.sin(dist * freq) * 1.6 - 0.6, 0, 1)
        if ribs:
            ang = np.arctan2(Q[:, 0], hz - Q[:, 2] + 1e-6)
            m = m * (1 - rib_depth * np.clip(-np.cos(ribs * ang), 0, 1))
        if bands:
            m = m * (1 - bands * np.clip(np.sin(dist * freq * 0.33 + 1.0) * 2 - 1.0, 0, 1))
        return m

    return f


def _bivalve(hid, prev, kind="clam"):
    """clam / oyster / scallop / mussel / geoduck: lower valve on Body, upper valve hinged at the back."""
    cfg = {
        "clam": dict(L=1.25, W=1.15, D=0.62, taper=0.12, growth=16.0, growth_amp=0.025, thick=0.11, umbo=0.35),
        "oyster": dict(L=1.35, W=1.0, D=0.5, taper=0.3, growth=7.0, growth_amp=0.0, shingle=0.045, thick=0.2, umbo=0.15, rough=0.05, wavy=7, wavy_amp=0.07),
        "scallop": dict(L=1.2, W=1.25, D=0.42, taper=0.0, ribs=16, rib_amp=0.13, growth=26.0, growth_amp=0.012, thick=0.12, umbo=0.1, ears=0.42, wavy=16, wavy_amp=0.06),
        "mussel": dict(L=1.55, W=0.62, D=0.45, taper=0.55, growth=12.0, growth_amp=0.02, thick=0.1, umbo=0.2, bend=0.25),
        "geoduck": dict(L=0.95, W=0.72, D=0.48, taper=0.1, growth=14.0, growth_amp=0.03, thick=0.1, umbo=0.3),
    }[kind]
    H = Hero(hid, plan="Blob", gait="hop", tags=["mollusc", "bivalve", "shell", "aquatic"])
    H.preview = prev
    L, W, D = cfg["L"], cfg["W"], cfg["D"]
    low = dict(cfg)
    if kind == "oyster":
        low["D"] = D * 1.45              # deep cupped lower valve, flat lid
        cfg["D"] = D * 0.6
        low["seed"], cfg["seed"] = 3, 7
    if kind == "scallop":
        low["D"] = D * 0.75              # the right valve is the flatter one
    y0 = low["D"] + 0.02
    H.body((0, y0, 0))
    bounds(H, (-W * 1.6 - 0.3, -0.3, -L * 1.6 - 0.6), (W * 1.6 + 0.3, y0 + D * 2.6 + (3.8 if kind == "geoduck" else 0.8), L * 1.5 + 0.3))
    hz = L * 0.92
    pat = growth_pat(L, freq=cfg.get("growth", 10) * (0.5 if kind != "scallop" else 0.35), depth=0.18,
                     ribs=cfg.get("ribs", 0), rib_depth=0.3, bands=0.3 if kind in ("clam", "mussel", "scallop") else 0.0)
    o = (0, y0, 0)
    lin = kind in ("oyster",)
    lw = valve(up=-1, lining=lin, **{k: v for k, v in low.items()})
    up = valve(up=1, lining=lin, **{k: v for k, v in cfg.items()})
    if lin:
        lw, lwn = lw
        up, upn = up
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
    smat = "plastic" if kind in ("mussel", "scallop") else "hard"
    vres, vtris = (150, 1800) if kind in ("scallop", "oyster") else (128, 1500)
    H.piece("LowerValve", "Body", frame(lw, o, X, Y, Z), col="primary", mat=smat, tris=vtris, res=vres, role="shell", pattern=lpat(pat, o, X, Y, Z))
    H.bone("Valve", "Body", (0, y0, hz))
    H.piece("UpperValve", "Valve", frame(up, o, X, Y, Z), col="primary", mat=smat, tris=vtris, res=vres, role="shell", pattern=lpat(pat, o, X, Y, Z))
    if lin:
        H.piece("NacreLow", "Body", frame(lwn, o, X, Y, Z), col="secondary", mat="glass", tris=700, res=128, role="detail", pri=1.4)
        H.piece("NacreUp", "Valve", frame(upn, o, X, Y, Z), col="secondary", mat="glass", tris=700, res=128, role="detail", pri=1.4)
    # hinge ligament
    H.piece("Hinge", "Body", capsule((-W * 0.25, y0 + 0.02, hz + 0.02), (W * 0.25, y0 + 0.02, hz + 0.02), 0.07), col="dark", mat="hard", tris=160, role="detail", pri=1.8)
    # soft body: mantle with a frilly edge, filling the gape
    mW, mL = (W - cfg["thick"]) * 0.9, (L - cfg["thick"]) * 0.9
    mant = ellipsoid(mW, min(D, low["D"]) * 0.32, mL, (0, y0, -0.02)).noise(0.025 if kind != "oyster" else 0.04, 9.0, 2)
    H.piece("Mantle", "Body", mant, col="inner", mat="plastic", tris=900, res=120, role="body", pri=1.2,
            pattern=lambda P: 1 - 0.25 * np.clip((np.hypot(P[:, 0] / mW, P[:, 2] / mL) - 0.75) * 5, 0, 1))
    eyes = []
    foot = None
    neck = []
    if kind == "oyster":
        H.prim("Pearl", "Body", "Ball", (0.36, 0.36, 0.36), (0.05, y0 + min(D, low["D"]) * 0.32 + 0.1, -0.35), col=(0.96, 0.94, 0.92), mat="glass", role="gem", pri=1.3)
        H.prim("PearlShine", "Body", "Ball", (0.1, 0.1, 0.1), (0.0, y0 + min(D, low["D"]) * 0.32 + 0.22, -0.46), col="shine", mat="hard", role="shine", pri=2.4)
    if kind == "scallop":
        # a row of bright blue eyes along each mantle rim (upper rim on the valve bone, so they ride the gape)
        for vb, yy, nm in (("Body", y0 - 0.06, "Lo"), ("Valve", y0 + 0.07, "Up")):
            for i in range(7):
                a = math.radians(-62 + i * (124 / 6))
                p = V(math.sin(a) * W * 0.86, yy, hz - math.cos(a) * (hz + L * 0.82))
                H.prim(f"Eye{nm}{i}", vb, "Ball", (0.085, 0.085, 0.085), T(p), col=(0.16, 0.42, 0.95), mat="glass", role="eye", pri=1.9)
        # sensory tentacle fringe
        fr = []
        for i in range(15):
            a = math.radians(-70 + i * 10)
            b0 = V(math.sin(a) * W * 0.8, y0, hz - math.cos(a) * (hz + L * 0.75))
            d = V(math.sin(a), 0, -math.cos(a))
            fr.append(round_cone(T(b0), T(b0 + d * 0.22 + V(0, 0.02 * (i % 2), 0)), 0.03, 0.012))
        H.piece("Fringe", "Body", union_all(fr), col="inner", mat="plastic", tris=600, res=150, role="detail", pri=1.6)
    if kind == "clam":
        # the muscular foot that pokes out of the front gape and pushes off (the hop)
        fb = V(0, y0 - 0.02, -L * 0.55)
        H.bone("Foot", "Body", T(fb))
        ft = round_cone(T(fb), T(fb + V(0, -0.12, -0.75)), 0.24, 0.13).su(sphere(0.16, T(fb + V(0, -0.15, -0.72))), 0.08)
        ft = ft.scale3(1, 0.7, 1).at(0, fb[1] * 0.3, 0)
        H.piece("FootP", "Foot", ft, col="inner", mat="plastic", tris=500, role="limb", pri=1.3)
        foot = "Foot"
        # two little siphon tips at the back gape
        H.bone("Siphon", "Body", (0, y0, L * 0.65))
        sp = union_all([round_cone((sx, y0 + 0.02, L * 0.6), (sx * 1.3, y0 + 0.12, L * 1.05), 0.1, 0.075) for sx in (-0.13, 0.13)], 0.04)
        sp = sp.ss(union_all([sphere(0.05, (sx * 1.3, y0 + 0.13, L * 1.1)) for sx in (-0.13, 0.13)]), 0.02)
        H.piece("SiphonP", "Siphon", sp, col="inner", mat="plastic", tris=400, role="detail", pri=1.5)
        eyes = [("Siphon", 1)]
    if kind == "mussel":
        # byssus threads anchoring it (pull loose as it hops)
        th = []
        for i in range(5):
            sx = -0.2 + 0.1 * i
            a = V(sx * 0.6, y0 - 0.05, -0.3 + 0.08 * i)
            th.append(tube([T(a), T(a + V(sx * 0.6, -0.3, -0.2)), (sx * 2.2, 0.03, -0.35 - 0.12 * i)], [0.025, 0.02, 0.016], k=0.02))
        H.piece("Byssus", "Body", union_all(th), col="leather", mat="cloth", tris=500, res=150, role="detail", pri=1.7)
    if kind == "geoduck":
        # the body is far too big for the shell: a fleshy collar bulging out of the gape, and the huge siphon neck
        bulge = ellipsoid(W * 1.02, D * 0.5, L * 0.85, (0, y0, -0.05)).noise(0.03, 6.0, 4)
        H.piece("Flesh", "Body", bulge, col="secondary", mat="plastic", tris=800, res=120, role="body", pri=1.2,
                pattern=lambda P: 1 - 0.18 * np.clip(np.sin(P[:, 2] * 18 + np.sin(P[:, 0] * 9)) * 2 - 1, 0, 1))
        pts = [V(0, y0 + 0.05, -L * 0.6), V(0, y0 + 0.75, -L * 1.25), V(0, y0 + 1.7, -L * 1.55), V(0, y0 + 2.55, -L * 1.4), V(0, y0 + 3.0, -L * 0.95)]
        rad = [0.42, 0.38, 0.34, 0.31, 0.3]
        names = ["Neck1", "Neck2", "Neck3"]
        piv = [pts[0], pts[1], pts[3]]
        par = "Body"
        for i, nm in enumerate(names):
            H.bone(nm, par, T(piv[i]))
            par = nm
        rings = lambda P: 1 - 0.22 * np.clip(np.sin(P[:, 1] * 26 + P[:, 2] * 12) * 1.8 - 0.8, 0, 1)
        segs = [(0, 2), (1, 4), (3, 5)]
        for i, (a, b) in enumerate(segs):
            pp = pts[a:b]
            rr = rad[a:b]
            if len(pp) == 1:
                pp = [pts[a], pts[a]]
            sh = tube([T(p) for p in pp], rr, k=0.05).noise(0.035, 7.0, 10 + i)
            if i == 2:
                tip = pts[4]
                sh = sh.ss(union_all([sphere(0.11, T(tip + V(sx, 0.06, -0.08))) for sx in (-0.12, 0.12)]), 0.04)
            H.piece(f"NeckP{i + 1}", names[i], sh, col="secondary", mat="plastic", tris=700, res=120, role="neck", pri=1.2, pattern=rings)
        H.prim("NeckTip", names[2], "Cylinder", (0.06, 0.6, 0.62), T(pts[4] + V(0, 0.2, 0.02)), rot=(0, 0, math.pi / 2), col="dark", mat="plastic", role="detail", pri=2.0)
        neck = names
    style = {"clam": "hop", "oyster": "rock", "scallop": "swim", "mussel": "hop", "geoduck": "neck"}[kind]
    rest = {"clam": 0.24, "oyster": 0.2, "scallop": 0.3, "mussel": 0.18, "geoduck": 0.28}[kind]
    MS.bivalve(H, [("Valve", 1)], height=1.6, rest=rest, style=style, foot=foot, neck=neck, eyes=eyes, period=0.8 if style == "swim" else 1.0)
    H.socket("mouth", (0, y0, -L - 0.1), "Body")
    H.socket("head", (0, y0 + D + 0.4 if kind != "geoduck" else y0 + 3.4, 0), "Body")
    H.rig.update({"head": "Valve" if kind != "geoduck" else "Neck3"})
    return H


@hero("clam", FAM)
def clam():
    return _bivalve("clam", {"primary": "#D8C8B0", "secondary": "#9A8A70", "inner": "#F0B8A8"}, "clam")


@hero("oyster", FAM)
def oyster():
    return _bivalve("oyster", {"primary": "#9E9488", "secondary": "#E8E4DC", "inner": "#E8DCCB"}, "oyster")


@hero("scallop", FAM)
def scallop():
    return _bivalve("scallop", {"primary": "#E8A87A", "secondary": "#F2E0C8", "inner": "#F6E2CC"}, "scallop")


@hero("mussel", FAM)
def mussel():
    return _bivalve("mussel", {"primary": "#2A2E3A", "secondary": "#8A7AA8", "inner": "#E89A5A"}, "mussel")


@hero("geoduck", FAM)
def geoduck():
    return _bivalve("geoduck", {"primary": "#B8A890", "secondary": "#E8C8A8", "inner": "#E8C8A8"}, "geoduck")


# ================================================================================================ giant clam
@hero("giant clam", FAM)
def giant_clam():
    """Hinge down, gape up: two huge valves with five deep interlocking folds, the gaudy mantle lips spilling out over
    the top with iridescent spots and a big inhalant siphon."""
    H = Hero("giant clam", plan="Blob", gait="heavy", tags=["mollusc", "bivalve", "shell", "aquatic"])
    H.preview = {"primary": "#3AA0A8", "secondary": "#8A5AC8", "cream": "#E2D8C4"}
    L, W, D = 1.15, 2.0, 0.85
    hy = 0.3
    yc = hy + L * 0.92
    H.body((0, hy, 0))
    bounds(H, (-2.4, -0.3, -2.7), (2.4, 4.4, 2.7))
    o = (0, yc, 0)
    ex, ez = (0, 0, 1), (0, -1, 0)
    vk = dict(L=L, W=W, D=D, taper=0.05, ribs=5, rib_amp=0.45, growth=20.0, growth_amp=0.0, wavy=5, wavy_amp=0.34, thick=0.14,
              umbo=0.0, gap=0.02)
    # outward = +x for the right valve; flutes (scale-like frills) along each fold
    vR = valve(up=1, **vk)

    def frills(base, sgn):
        def f(P):
            d = base(P)
            ang = np.arctan2(P[:, 0], (L * 0.92 - P[:, 2]) + 1e-6)
            dist = np.hypot(P[:, 0], L * 0.92 - P[:, 2])
            on = np.clip(np.cos(5 * ang) - 0.55, 0, 1) * 2.2
            fl = np.abs(np.sin(dist * 7.5)) ** 6 * on * np.clip(dist / L - 0.25, 0, 1)
            return d - 0.07 * fl
        return S.SDF(f)
    gp = growth_pat(L, freq=7.0, depth=0.3, ribs=5, rib_depth=0.3, bands=0.2)
    H.mbone("Valve#", "Body", (0.0, hy, 0))
    H.mpiece("ValveP#", "Valve#", frame(frills(vR, 1), o, ex, (1, 0, 0), ez), col="cream", mat="hard", tris=1700, res=136, role="shell",
             pattern=lpat(gp, o, ex, (1, 0, 0), ez))
    # mantle lips: a thick wavy roll filling the gape, bulging over the rims
    ly = yc + L * 0.92

    def lipf(P):
        q = P - V(0, ly, 0)
        wav = 0.13 * np.sin(q[:, 2] * 3.0) + 0.06 * np.sin(q[:, 2] * 7.0 + 1)
        # two fat lobes (one over each valve rim) with a groove between them
        r = np.column_stack([np.abs(q[:, 0] - wav * 0.5) - 0.42, q[:, 1] - wav, q[:, 2]])
        return _ell(r, 0.5, 0.36, W * 0.95)
    lips = S.SDF(lipf).su(ellipsoid(0.75, L * 0.75, W * 0.85, (0, yc - 0.05, 0)), 0.25)
    lips = lips.ss(ellipsoid(0.2, 0.16, 0.34, (0, ly + 0.32, -0.6)), 0.06)    # inhalant siphon
    lips = lips.ss(ellipsoid(0.12, 0.1, 0.16, (0, ly + 0.3, 0.8)), 0.04)      # exhalant
    wavyp = lambda P: 1 - 0.3 * np.clip(np.sin(P[:, 2] * 9 + np.sin(P[:, 0] * 14) * 1.5) * np.sin(P[:, 0] * 11) - 0.2, 0, 1)
    H.piece("Lips", "Body", lips.noise(0.02, 9.0, 3), col="primary", mat="plastic", tris=1500, res=128, role="body", pri=1.1, pattern=wavyp)
    rng = np.random.default_rng(5)
    dots = [sphere(rng.uniform(0.05, 0.09), T(p)) for p in surface_pts(lips, 40, (-0.95, 0.95), (-W * 0.9, W * 0.9), ly + 1.0, yc, seed=5)]
    H.piece("LipSpots", "Body", overlay(lips, union_all(dots), t=0.025), col="glow", mat="plastic", tris=700, res=150, role="detail", pri=1.6, glow=True)
    H.prim("SiphonRim", "Body", "Cylinder", (0.06, 0.34, 0.5), (0, ly + 0.36, -0.6), rot=(0, 0, math.pi / 2), col="secondary", mat="plastic", role="detail", pri=1.7)

    def extra(pose, kind, u, a):
        return
    MS.bivalve(H, [("ValveR", -1), ("ValveL", 1)], height=2.2, rest=0.12, style="rock", hinge_axis=5, period=1.4, extra=extra)
    H.socket("mouth", (0, yc + L * 0.6, -0.8), "Body")
    H.socket("head", (0, yc + L + 0.6, 0), "Body")
    H.rig.update({"head": "Body"})
    return H


# ================================================================================================ shipworm
@hero("shipworm", FAM)
def shipworm():
    """A wormy clam boring through driftwood: a bored log with the pale body arching out of a hole, the tiny ridged
    two-valve drill head at its tip, and a siphon pair peeking from another hole."""
    H = Hero("shipworm", plan="Worm", gait="slither", tags=["mollusc", "bivalve", "worm", "wood"])
    H.preview = {"primary": "#E8E0D0", "secondary": "#C8B8A0", "bark": "#6B4A2E"}
    H.body((0, 0.55, 0))
    lg = capsule((0, 0.55, -1.45), (0, 0.55, 1.45), 0.55)
    lg = lg.su(capsule((0.35, 0.75, 0.6), (0.85, 1.15, 1.0), 0.12), 0.08)                     # broken branch stub
    bark = lambda P: 1 - 0.3 * np.clip(np.sin(np.arctan2(P[:, 1] - 0.55, P[:, 0]) * 14 + np.sin(P[:, 2] * 3) * 1.2) * 2 - 1.2, 0, 1)
    lg = lg.noise(0.025, 8.0, 5)
    holes = [(0, 1.1, -0.65), (0.3, 1.0, 0.85), (-0.45, 0.85, 0.1), (0.48, 0.6, -0.9), (-0.25, 0.5, 1.5)]
    for h in holes:
        lg = lg.ss(sphere(0.17, h), 0.04)
    H.piece("Log", "Body", lg, col="bark", mat="wood", tris=1500, res=128, role="body",
            pattern=combine(bark, lambda P: 1 - 0.35 * np.clip((np.abs(P[:, 2]) - 1.5) * 8, 0, 1)))
    # end grain rings (lighter caps)
    for sz in (-1, 1):
        cap = S.SDF(lambda P, sz=sz: np.maximum(np.hypot(P[:, 0], P[:, 1] - 0.55) - 0.5, np.abs(P[:, 2] - sz * 1.62) - 0.06))
        H.piece(f"EndGrain{'F' if sz < 0 else 'B'}", "Body", cap.si(lg.round(0.012), 0.01), col="wood", mat="wood", tris=300, role="detail", pri=1.8,
                pattern=lambda P: 1 - 0.3 * np.clip(np.sin(np.hypot(P[:, 0], P[:, 1] - 0.55) * 40) - 0.5, 0, 1))
    pts = [V(0, 1.0, -0.65), V(0, 1.65, -0.95), V(0, 2.05, -1.55), V(0, 1.85, -2.15), V(0, 1.45, -2.45)]
    rad = [0.24, 0.25, 0.25, 0.24, 0.22]
    names = ["Worm1", "Worm2", "Worm3"]
    piv = [pts[0], pts[1], pts[3]]
    par = "Body"
    for i, nm in enumerate(names):
        H.bone(nm, par, T(piv[i]))
        par = nm
    ann = lambda P: 1 - 0.15 * np.clip(np.sin((P[:, 1] * 0.8 - P[:, 2]) * 30) - 0.4, 0, 1)
    for i, (a, b) in enumerate([(0, 2), (1, 4), (3, 5)]):
        sh = tube([T(p) for p in pts[a:b]], rad[a:b], k=0.04)
        H.piece(f"WormP{i + 1}", names[i], sh, col="primary", mat="plastic", tris=600, res=120, role="body", pri=1.2, pattern=ann)
    # drill head: two ridged mini valves clasping the tip
    tip = pts[4]
    dirv = (pts[4] - pts[3]) / np.linalg.norm(pts[4] - pts[3])
    H.bone("Drill", names[2], T(tip))
    hd = []
    for sx in (-1, 1):
        c = tip + V(sx * 0.13, 0, 0) + dirv * 0.08
        hd.append(ellipsoid(0.19, 0.28, 0.28, T(c)))
    head = union_all(hd, 0.04)
    ridges = lambda P: 1 - 0.4 * np.clip(np.sin((P - tip) @ dirv * 60) - 0.2, 0, 1)
    H.piece("DrillHead", "Drill", head, col="secondary", mat="hard", tris=500, res=150, role="head", pri=1.2, pattern=ridges)
    H.prim("Mouth", "Drill", "Ball", (0.1, 0.1, 0.1), T(tip + dirv * 0.34), col="mouth", mat="hard", role="mouth", pri=2.0)
    # siphon pair from the back hole
    sb = V(0.3, 1.0, 0.85)
    H.bone("Siphons", "Body", T(sb))
    sp = union_all([round_cone(T(sb + V(sx, -0.05, 0)), T(sb + V(sx * 1.6 + 0.05, 0.45, 0.1)), 0.07, 0.055) for sx in (-0.05, 0.06)], 0.03)
    sp = sp.ss(union_all([sphere(0.035, T(sb + V(sx * 1.6 + 0.05, 0.5, 0.1))) for sx in (-0.05, 0.06)]), 0.01)
    H.piece("SiphonP", "Siphons", sp, col="primary", mat="plastic", tris=300, role="detail", pri=1.6)

    def extra(pose, kind, u, k):
        if kind in ("move", "idle"):
            MS._add(pose, "Drill", (0, 0, 0, 0, 0, 0.5 * math.sin(TAU * u * 2)))   # the drill head grinds
            MS._add(pose, "Siphons", (0, 0, 0, 0.15 * math.sin(TAU * u * 2), 0, 0.1 * math.sin(TAU * u)))
        if kind == "attack":
            MS._add(pose, "Drill", (0, 0, 0, 0, 0, 3.0 * k))
    MS.sessile(H, stalks=[names], crowns=[], retract=[("Siphons", 0.35)], height=2.0, period=1.3, attack="lash", hop=0.04, extra=extra)
    H.socket("mouth", T(tip + dirv * 0.3), "Drill")
    H.socket("head", (0, 2.4, -1.5), "Worm3")
    H.rig.update({"head": "Worm3", "tail": names})
    return H


# ================================================================================================ sea snails
def spiral(origin, axis, ref, turns=4.0, R0=0.5, r0=0.6, shrink=0.5, rise=1.5, steps=60, knobs=0, knob_r=0.35, knob_turns=None,
           cords=0.0, cord_freq=0.0, flatten=1.0):
    """Helico-spiral shell: spheres along a conical spiral (biggest whorl = body whorl at theta 0, apex at the end),
    smooth-unioned. axis: the spire direction (apex side); ref: where the body whorl's centre sits from the axis.
    knobs: knobs per turn on the shoulder of each whorl (conch / whelk crowns). Returns (sdf, pattern, frame)."""
    a = V(axis) / np.linalg.norm(axis)
    e1 = V(ref) - a * (V(ref) @ a)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(a, e1)
    o = V(origin)
    k = math.log(1 / shrink) / TAU
    th_max = turns * TAU
    e_min = math.exp(-k * th_max)
    sd = None
    pts = []
    for i in range(steps):
        th = th_max * i / (steps - 1)
        e = math.exp(-k * th)
        R, r = R0 * e, r0 * e
        h = rise * (1 - e) / (1 - e_min)
        c = o + e1 * R * math.cos(th) + e2 * R * math.sin(th) + a * h
        pts.append((c, r, th))
        sp = ellipsoid(r, r * flatten, r, T(c)) if flatten != 1.0 else sphere(r, T(c))
        sd = sp if sd is None else sd.su(sp, r * 0.35)
    if knobs:
        kt = knob_turns if knob_turns is not None else turns
        nk = int(knobs * kt)
        kn = []
        for j in range(nk):
            th = (j + 0.5) / knobs * TAU
            e = math.exp(-k * th)
            R, r = R0 * e, r0 * e
            h = rise * (1 - e) / (1 - e_min)
            radial = e1 * math.cos(th) + e2 * math.sin(th)
            c = o + radial * R + a * h
            base = c + a * r * 0.45 + radial * r * 0.55
            kn.append(round_cone(T(base), T(base + (a * 0.55 + radial * 0.85) * r * knob_r * 2.2), r * knob_r, r * knob_r * 0.25))
        sd = sd.su(union_all(kn), 0.06)
    if cords:
        base = sd

        def f(P):
            q = P - o
            hh = q @ a
            return base(P) - cords * np.abs(np.sin(hh * cord_freq)) ** 4
        sd = S.SDF(f)

    def pat(P):
        q = P - o
        x, y = q @ e1, q @ e2
        th = np.arctan2(y, x)
        rr = np.maximum(np.hypot(x, y), 1e-3)
        band = 1 - 0.35 * np.clip(np.sin((np.log(rr / R0) / (-k) - th) * 1.0 + q @ a * 6.0) * 2 - 1.0, 0, 1)
        growth = 1 - 0.12 * np.clip(1 - np.abs(np.mod(th * 7 / math.pi, 1) - 0.5) / 0.12, 0, 1)
        return band * growth

    return sd, pat, (o, a, e1, e2, pts)


def _snail_soft(H, y_foot, z0, z1, width, head_z, col="secondary", stalk_len=0.7, eye_col="pupil", eye_r=0.09, snout=0.0,
                tail_bone=True, tent_len=0.0, ring_iris=False, pat=None):
    """Foot (Body + Tail), head with eye stalks (and optional lower tentacles / snout). Returns (stalks, head, foot)."""
    foot = ellipsoid(width, 0.24, (z1 - z0) * 0.5, (0, y_foot, (z0 + z1) * 0.5)) & S.SDF(lambda P: -P[:, 1])
    foot = foot.su(ellipsoid(width * 1.08, 0.06, (z1 - z0) * 0.52, (0, 0.05, (z0 + z1) * 0.5)), 0.05)
    tub = pat or (lambda P: 1 - 0.18 * np.clip(np.sin(P[:, 2] * 20 + np.sin(P[:, 0] * 16) * 2) * np.sin(P[:, 0] * 18) - 0.3, 0, 1))
    H.piece("Foot", "Body", foot.noise(0.01, 14, 1), col=col, mat="plastic", tris=1000, res=120, role="body", pattern=tub)
    fb = []
    if tail_bone:
        H.bone("Tail", "Body", (0, 0.15, z1 - (z1 - z0) * 0.25))
        tl = round_cone((0, 0.16, z1 - (z1 - z0) * 0.3), (0, 0.06, z1 + 0.45), width * 0.75, 0.08) & S.SDF(lambda P: -P[:, 1])
        H.piece("TailP", "Tail", tl.noise(0.01, 14, 2), col=col, mat="plastic", tris=500, role="tail", pattern=tub)
        fb = ["Tail"]
    hc = V(0, 0.42, head_z)
    H.bone("Head", "Body", (0, 0.3, head_z + 0.35))
    nk = tube([(0, 0.2, head_z + 0.5), (0, 0.32, head_z + 0.15), T(hc)], [width * 0.75, width * 0.62, width * 0.5], k=0.06)
    if snout:
        nk = nk.su(round_cone(T(hc), T(hc + V(0, -0.12, -snout)), width * 0.42, width * 0.28), 0.05)
    nk = nk & S.SDF(lambda P: 0.02 - P[:, 1])
    H.piece("HeadP", "Head", nk.noise(0.01, 14, 3), col=col, mat="plastic", tris=800, role="head", pattern=tub)
    sb = hc + V(width * 0.3, 0.12, -0.05)
    H.mbone("Stalk#", "Head", T(sb))
    tip = sb + V(0.22, 0.85, -0.35) * stalk_len
    st = round_cone(T(sb), T(tip), 0.07, 0.045).su(sphere(eye_r * 0.85, T(tip)), 0.03)
    H.mpiece("StalkP#", "Stalk#", st, col=col, mat="plastic", tris=260, role="detail", pri=1.4)
    if ring_iris:
        H.mprim("Eye#", "Stalk#", "Ball", (eye_r * 2,) * 3, T(tip + V(0.0, 0.02, -0.05)), col="iris", mat="hard", pri=1.4, role="eye")
        H.mprim("Pupil#", "Stalk#", "Ball", (eye_r * 1.1,) * 3, T(tip + V(0.01, 0.03, -0.05 - eye_r * 0.65)), col="pupil", mat="hard", pri=1.5, role="pupil")
    else:
        H.mprim("Eye#", "Stalk#", "Ball", (eye_r * 2,) * 3, T(tip + V(0.0, 0.02, -0.04)), col=eye_col, mat="hard", pri=1.5, role="eye")
    H.mprim("Shine#", "Stalk#", "Ball", (eye_r * 0.7,) * 3, T(tip + V(0.02, eye_r * 0.7, -eye_r * 0.9)), col="shine", mat="hard", pri=2.4, role="shine")
    stalks = [("StalkR", 1), ("StalkL", -1)]
    if tent_len:
        tb = hc + V(width * 0.38, -0.08, -0.1)
        H.mbone("Feeler#", "Head", T(tb))
        H.mpiece("FeelerP#", "Feeler#", round_cone(T(tb), T(tb + V(0.25, -0.05, -0.45) * tent_len), 0.06, 0.03), col=col, mat="plastic", tris=200, role="detail", pri=1.5)
        stalks += [("FeelerR", 1), ("FeelerL", -1)]
    return stalks, "Head", fb


@hero("conch", FAM)
def conch():
    """Queen conch: a heavy crowned spiral with a huge flared pink lip, the animal peeking out with long eye stalks
    (gold-ringed eyes) and a snout; it moves in heaving lurches."""
    H = Hero("conch", plan="Blob", gait="hop", tags=["mollusc", "gastropod", "shell", "aquatic"])
    H.preview = {"primary": "#F2C8B0", "secondary": "#E87A6A", "inner": "#F59A8A", "iris": "#E8C030"}
    H.body((0, 0.3, 0))
    bounds(H, (-2.8, -0.3, -2.6), (2.8, 4.0, 3.6))
    yc = 1.25
    H.bone("Shell", "Body", (0, 0.6, 0.2))
    sh, sp, (o, a, e1, e2, pts) = spiral((0, yc, 0.15), (0, 0.42, 1), (0, -0.2, -1), turns=4.5, R0=0.4, r0=0.82, shrink=0.55, rise=2.1,
                                         steps=70, knobs=7, knob_r=0.42, knob_turns=2.6)
    # siphonal canal forward and the stromboid lip: a thick flaring wing on the right
    sh = sh.su(round_cone((0.1, yc - 0.15, -0.5), (0.05, yc - 0.35, -1.75), 0.55, 0.14), 0.25)
    wing = plate((0.6, yc - 0.2, -0.2), (0, 0.15, -1), (1, 1.1, 0), [(-1.0, -0.1), (1.2, -0.1), (1.15, 0.8), (0.4, 1.6), (-0.4, 1.35), (-1.0, 0.5)],
                 0.26, taper=0.5, bend=0.12)
    sh = sh.su(wing, 0.15)
    aperture = ellipsoid(0.32, 0.4, 1.05, (0.45, yc - 0.55, -0.35)).rot(0, 0, 0)
    shell = sh.ss(aperture, 0.12) & S.SDF(lambda P: 0.06 - P[:, 1])
    H.piece("ShellP", "Shell", shell, col="primary", mat="hard", tris=1800, res=140, role="shell",
            pattern=combine(sp, lambda P: 1 - 0.25 * np.clip((P[:, 1] - (yc + 0.6)) * -1.5, 0, 1) * 0))
    # glossy pink inner lip (the underside of the wing and the aperture lining)
    lip = sh.round(0.0).si(S.SDF(lambda P: (yc - 0.05) - P[:, 1] + 0.25 * P[:, 0]), 0.05) & ellipsoid(1.6, 0.9, 1.5, (0.7, yc - 0.6, -0.4))
    lip = lip.si(sh.round(0.035), 0.0).ss(sh.round(-0.0001), 0.0) if False else overlay(sh, S.SDF(lambda P: np.maximum(P[:, 1] - (yc - 0.32) - 0.22 * P[:, 0], -P[:, 1] + 0.07)), t=0.03)
    H.piece("Lip", "Shell", lip, col="inner", mat="plastic", tris=900, res=140, role="detail", pri=1.3)
    stalks, head, foot = _snail_soft(H, 0.24, -1.0, 0.7, 0.42, -1.1, col="secondary", stalk_len=1.1, eye_r=0.12, snout=0.55, ring_iris=True,
                                     pat=spots(0.12, 0.035, depth=0.35, seed=4))
    # operculum: the claw-like horny sickle at the back of the foot
    H.piece("Operculum", foot[0], round_cone((0, 0.28, 1.0), (0.05, 0.12, 1.35), 0.12, 0.04).scale3(1.6, 1, 1), col="leather", mat="hard", tris=200, role="claw", pri=1.6)
    MS.gastropod(H, foot=foot, head=head, stalks=stalks, shell="Shell", height=2.2, period=1.4, style="lurch")
    H.socket("mouth", (0, 0.3, -1.8), "Head")
    H.socket("head", (0, 3.4, 1.0), "Shell")
    H.rig.update({"head": "Head"})
    return H


@hero("whelk", FAM)
def whelk():
    """A tall pointed spire with spiral cords and a crown of shoulder knobs, a long siphonal canal with the animal's
    snorkel siphon raised out of it, a broad foot and a head with eye tentacles."""
    H = Hero("whelk", plan="Blob", gait="slither", tags=["mollusc", "gastropod", "shell", "aquatic"])
    H.preview = {"primary": "#C8A07A", "secondary": "#8A6A4A", "inner": "#F2DCC0"}
    H.body((0, 0.3, 0))
    bounds(H, (-2.2, -0.3, -2.8), (2.2, 3.6, 3.6))
    yc = 1.1
    H.bone("Shell", "Body", (0, 0.6, 0.3))
    sh, sp, _ = spiral((0, yc, 0.25), (0, 0.55, 1), (0, -0.3, -1), turns=5.5, R0=0.3, r0=0.72, shrink=0.6, rise=2.6, steps=80,
                       knobs=9, knob_r=0.16, knob_turns=3.0, cords=0.025, cord_freq=14.0)
    sh = sh.su(round_cone((0, yc - 0.2, -0.35), (0, yc - 0.15, -1.55), 0.42, 0.13), 0.2)       # siphonal canal
    shell = sh.ss(ellipsoid(0.3, 0.38, 0.75, (0.3, yc - 0.5, -0.25)), 0.1) & S.SDF(lambda P: 0.06 - P[:, 1])
    H.piece("ShellP", "Shell", shell, col="primary", mat="hard", tris=1800, res=144, role="shell",
            pattern=combine(sp, stripes(lambda P: P[:, 1] * 0.55 + P[:, 2] * 0.85, 3.2, width=0.3, depth=0.25)))
    H.piece("Lip", "Shell", overlay(sh, S.SDF(lambda P: np.maximum(P[:, 1] - (yc - 0.4) - 0.2 * P[:, 0], -P[:, 1] + 0.07)), t=0.03),
            col="inner", mat="plastic", tris=600, res=140, role="detail", pri=1.3)
    stalks, head, foot = _snail_soft(H, 0.24, -1.05, 0.95, 0.55, -1.1, col="secondary", stalk_len=0.75, eye_r=0.07,
                                     pat=combine(spots(0.14, 0.04, depth=0.4, seed=2), gradient(1, 0.0, 0.3, 0.75, 1.0)))
    # the snorkel siphon raised out of the canal
    sb = V(0, yc - 0.05, -1.3)
    H.bone("Siphon", "Shell", T(sb))
    sph = tube([T(sb), T(sb + V(0, 0.45, -0.3)), T(sb + V(0, 0.85, -0.35))], [0.12, 0.11, 0.1], k=0.03)
    sph = sph.ss(sphere(0.07, T(sb + V(0, 0.92, -0.35))), 0.02)
    H.piece("SiphonP", "Siphon", sph, col="secondary", mat="plastic", tris=300, role="detail", pri=1.4)
    MS.gastropod(H, foot=foot, head=head, stalks=stalks + [("Siphon", 1)], shell="Shell", height=2.4, period=1.8, style="glide")
    H.socket("mouth", (0, 0.4, -1.8), "Head")
    H.socket("head", (0, 3.4, 1.5), "Shell")
    H.rig.update({"head": "Head"})
    return H


@hero("cowrie", FAM)
def cowrie():
    """A glossy egg-dome shell with tiger spots, the soft mantle sliding up over its flanks in two frilly papillate
    lobes, a broad foot and a little head with eye tentacles."""
    H = Hero("cowrie", plan="Blob", gait="slither", tags=["mollusc", "gastropod", "shell", "aquatic"])
    H.preview = {"primary": "#C8703A", "secondary": "#F2E0C0", "inner": "#8A5A3A"}
    H.body((0, 0.3, 0))
    bounds(H, (-1.8, -0.5, -2.4), (1.8, 2.4, 2.4))
    H.bone("Shell", "Body", (0, 0.6, 0))
    dome = ellipsoid(0.95, 0.78, 1.45, (0, 0.82, 0)).su(ellipsoid(1.02, 0.3, 1.5, (0, 0.42, 0)), 0.25) & S.SDF(lambda P: 0.2 - P[:, 1])
    dome = dome.su(capsule((0, 0.5, -1.45), (0, 0.42, -1.62), 0.18), 0.12).su(capsule((0, 0.5, 1.45), (0, 0.42, 1.62), 0.18), 0.12)
    tiger = combine(spots(0.36, 0.15, depth=0.85, seed=6, region=lambda P: np.clip((P[:, 1] - 0.55) * 4, 0, 1)),
                    lambda P: 1 - 0.55 * np.clip(1 - np.abs(P[:, 0]) / 0.07, 0, 1) * (P[:, 1] > 1.2),
                    gradient(1, 0.3, 1.6, 0.75, 1.0))
    H.piece("ShellP", "Shell", dome, col="primary", mat="glass", tris=1300, res=128, role="shell", pattern=tiger)
    H.piece("Base", "Shell", ellipsoid(0.98, 0.18, 1.48, (0, 0.33, 0)).ss(S.SDF(lambda P: np.maximum(np.abs(P[:, 0]) - 0.07, np.abs(P[:, 2]) - 1.3)), 0.03),
            col="secondary", mat="plastic", tris=500, role="detail", pri=1.4,
            pattern=lambda P: 1 - 0.5 * np.clip(np.sin(P[:, 2] * 30) * 2 - 1, 0, 1) * (np.abs(P[:, 0]) < 0.25))
    # mantle lobes creeping up the flanks
    mant = []
    for side in (1,):
        pass
    H.mbone("Mantle#", "Body", (0.85, 0.35, 0))

    def lobe(P):
        q = P - V(0, 0.82, 0)
        d = _ell(q, 1.0, 0.83, 1.5) - 0.0
        shellv = np.abs(d) - 0.05
        hgt = 0.35 + 0.22 * np.sin(P[:, 2] * 4.5) + 0.12 * np.sin(P[:, 2] * 9 + 1)
        cut = np.maximum(P[:, 1] - (0.45 + hgt), -P[:, 0])
        return np.maximum(np.maximum(shellv, cut), 0.12 - P[:, 1])
    papil = S.SDF(lobe)
    pp = surface_pts(S.SDF(lambda P: np.maximum(_ell(P - V(0, 0.82, 0), 1.06, 0.88, 1.56), np.maximum(P[:, 1] - 0.95, -P[:, 0] + 0.45))), 16,
                     (0.5, 1.1), (-1.3, 1.3), 1.3, 0.3, seed=8)
    pap = union_all([round_cone(T(p - V(0.04, 0, 0)), T(p + V(0.12, 0.06, 0)), 0.04, 0.015) for p in pp]) if pp else None
    mantle = papil.su(pap, 0.03) if pap is not None else papil
    H.mpiece("MantleP#", "Mantle#", mantle, col="inner", mat="plastic", tris=700, res=140, role="body", pri=1.3, tr=0.15)
    stalks, head, foot = _snail_soft(H, 0.24, -1.35, 1.25, 0.6, -1.25, col="inner", stalk_len=0.55, eye_r=0.06, tent_len=0.0)
    MS.gastropod(H, foot=foot, head=head, stalks=stalks, shell="Shell", height=1.6, period=1.8, style="glide", mantle=[("MantleR", 1), ("MantleL", -1)])
    H.socket("mouth", (0, 0.3, -1.7), "Head")
    H.socket("head", (0, 2.0, 0), "Shell")
    H.rig.update({"head": "Head"})
    return H


@hero("limpet", FAM)
def limpet():
    """A ribbed conical cap shell clamped to the ground; it lifts a crack to peek (head tentacles) and slams down."""
    H = Hero("limpet", plan="Blob", gait="slither", tags=["mollusc", "gastropod", "shell", "aquatic"])
    H.preview = {"primary": "#C8B89A", "secondary": "#8A7A60", "inner": "#E8D8B8"}
    H.body((0, 0.15, 0))
    bounds(H, (-1.9, -0.3, -2.2), (1.9, 2.2, 2.2))
    H.bone("Shell", "Body", (0, 0.2, 0))
    ax, az = 1.25, 1.5
    apex = V(0, 1.55, -0.25)

    def cone(P):
        q = P - V(0, 0.2, 0)
        # elliptic cone from an oval base to an off-centre apex, slightly concave flanks
        h = np.clip(q[:, 1] / (apex[1] - 0.2), 0, 1)
        cx = apex[0] * h
        cz = apex[2] * h
        rx = ax * (1 - h) ** 1.15 + 0.04
        rz = az * (1 - h) ** 1.15 + 0.04
        r = np.hypot((P[:, 0] - cx) / np.maximum(rx, 1e-3), (P[:, 2] - cz) / np.maximum(rz, 1e-3))
        ang = np.arctan2(P[:, 0] - cx, P[:, 2] - cz)
        rib = 0.07 * np.abs(np.cos(ang * 9)) ** 0.6 * (1 - h)
        d = (r - 1) * np.minimum(rx, rz) * 0.85 - rib
        d = np.maximum(d, -q[:, 1])
        d = np.maximum(d, q[:, 1] - (apex[1] - 0.2))
        return d
    shell = S.SDF(cone).round(0.04)
    shell = shell.ss(ellipsoid(ax - 0.12, 0.28, az - 0.12, (0, 0.16, 0)), 0.05)
    rays = lambda P: 1 - 0.3 * np.clip(np.cos(np.arctan2(P[:, 0], P[:, 2] + 0.25) * 9) * 1.6 - 0.6, 0, 1)
    rings = lambda P: 1 - 0.2 * np.clip(np.sin(P[:, 1] * 18) * 2 - 1, 0, 1)
    H.piece("ShellP", "Shell", shell.noise(0.012, 9, 3), col="primary", mat="stone", tris=1300, res=128, role="shell", pattern=combine(rays, rings))
    H.prim("Apex", "Shell", "Ball", (0.2, 0.14, 0.2), T(apex + V(0, -0.15, 0.02)), col="secondary", mat="stone", role="detail", pri=1.8)
    stalks, head, foot = _snail_soft(H, 0.22, -1.1, 1.1, 0.95, -1.15, col="inner", stalk_len=0.45, eye_r=0.06, tail_bone=False, tent_len=0.0)
    # the mantle fringe showing under the rim
    H.piece("Fringe", "Body", torus(1.08, 0.08).scale3(1, 1, 1.2).at(0, 0.2, 0), col="secondary", mat="plastic", tris=500, role="detail", pri=1.6)
    MS.gastropod(H, foot=foot, head=head, stalks=stalks, shell="Shell", height=1.5, period=2.0, style="clamp")
    H.socket("mouth", (0, 0.3, -1.6), "Head")
    H.socket("head", (0, 1.9, 0), "Shell")
    H.rig.update({"head": "Head"})
    return H


@hero("abalone", FAM)
def abalone():
    """A flat ear-shaped shell with a tiny spire at the back and a row of breathing holes, rough outside with a
    rainbow nacre rim; underneath, the frilly epipodium skirt bristling with tentacles all round the foot."""
    H = Hero("abalone", plan="Blob", gait="slither", tags=["mollusc", "gastropod", "shell", "aquatic"])
    H.preview = {"primary": "#8A6A5A", "secondary": "#8AE0C8", "inner": "#3A3A2E", "gem": "#8AE0C8"}
    H.body((0, 0.25, 0))
    bounds(H, (-2.0, -0.3, -2.4), (2.0, 2.0, 2.4))
    H.bone("Shell", "Body", (0, 0.5, 0))
    ax, az, hy = 1.25, 1.75, 0.55
    spx, spz = 0.55, 1.05                     # the spire sits back and to the right

    def ear(P):
        q = P - V(0, hy, 0)
        # low dome, highest near the spire, slightly flat on the hole side
        dome = _ell(q - V(0.1, -0.15, 0.1), ax, 0.62, az)
        sp = np.linalg.norm((P - V(spx, hy + 0.32, spz)) / np.array([0.38, 0.22, 0.38]), axis=1) - 1
        d = S.smin(dome, sp * 0.22, 0.2)
        return np.maximum(d, (hy - 0.12) - P[:, 1])
    shell = S.SDF(ear)
    # the line of respiratory holes (raised rims, open pores) along the left side
    holes = []
    hl = []
    for i in range(6):
        t = i / 5
        p = V(-0.85 + 0.25 * t * t, hy + 0.32 + 0.06 * t, -1.0 + 1.85 * t)
        holes.append(ellipsoid(0.17 - 0.012 * i, 0.12, 0.17 - 0.012 * i, T(p + V(0, 0.1, 0))))
        hl.append(sphere(0.1 - 0.008 * i, T(p + V(0, 0.2, 0))))
    shell = shell.su(union_all(holes), 0.06).ss(union_all(hl), 0.02)
    growth = lambda P: 1 - 0.28 * np.clip(np.sin(np.hypot(P[:, 0] - spx, P[:, 2] - spz) * 14 + np.sin(np.arctan2(P[:, 0] - spx, P[:, 2] - spz) * 3)) * 2 - 1, 0, 1)
    H.piece("ShellP", "Shell", shell.noise(0.03, 6.0, 9), col="primary", mat="stone", tris=1500, res=128, role="shell",
            pattern=combine(growth, spots(0.3, 0.12, depth=0.25, seed=3)))
    # nacre rim: the iridescent inner layer showing as a band round the lip
    rim = S.SDF(lambda P: np.maximum(np.abs(ear(P) + 0.0) - 0.035, np.maximum(P[:, 1] - (hy - 0.02), (hy - 0.12) - P[:, 1] - 0.0)))
    H.piece("Nacre", "Shell", rim, col="gem", mat="glass", tris=700, res=150, role="detail", pri=1.4,
            pattern=lambda P: 0.75 + 0.25 * np.sin(np.arctan2(P[:, 0], P[:, 2]) * 7))
    stalks, head, foot = _snail_soft(H, 0.24, -1.4, 1.4, 1.0, -1.3, col="inner", stalk_len=0.5, eye_r=0.07, tail_bone=False, tent_len=0.9)
    # epipodium: a frilly skirt round the foot with tentacles poking out all round
    sk = torus(1.0, 0.1).scale3(1.15, 1, 1.45).at(0, 0.36, 0).noise(0.03, 10, 4)
    tents = []
    for i in range(22):
        a = TAU * i / 22
        b = V(1.12 * math.sin(a), 0.36, 1.42 * math.cos(a))
        d = V(math.sin(a), 0.15 * (i % 2), math.cos(a))
        tents.append(round_cone(T(b), T(b + d * (0.32 + 0.1 * (i % 3))), 0.04, 0.015))
    H.piece("Epipodium", "Body", sk.su(union_all(tents), 0.03), col="inner", mat="plastic", tris=1000, res=150, role="detail", pri=1.3,
            pattern=lambda P: 1 - 0.35 * np.clip(np.sin(np.arctan2(P[:, 0], P[:, 2]) * 22) * 2 - 1, 0, 1))
    MS.gastropod(H, foot=foot, head=head, stalks=stalks, shell="Shell", height=1.4, period=2.0, style="clamp")
    H.socket("mouth", (0, 0.3, -1.8), "Head")
    H.socket("head", (0, 1.5, 0), "Shell")
    H.rig.update({"head": "Head"})
    return H


@hero("chiton", FAM)
def chiton():
    """Eight overlapping butterfly plates in a row, set in a leathery spiny girdle; each plate (with its slice of
    girdle) rides its own bone so the chiton can curl up like a pill bug."""
    H = Hero("chiton", plan="Blob", gait="slither", tags=["mollusc", "shell", "armour", "aquatic"])
    H.preview = {"primary": "#6A5A4A", "secondary": "#A8987A", "inner": "#3A3028"}
    hb = 0.42
    H.body((0, hb, 0))
    bounds(H, (-1.6, -0.4, -2.6), (1.6, 2.0, 2.6))
    n = 8
    Lz = 3.6
    zs = [-Lz / 2 + Lz * (i + 0.5) / n for i in range(n)]
    W = 0.95

    def wfun(z):
        return W * math.sqrt(max(0.05, 1 - (z / (Lz * 0.56)) ** 2))
    # bones: Body sits at plate 4; plates 3..0 chain forward, plates 5..7 chain back
    names = [f"Plate{i}" for i in range(n)]
    front = []
    par = "Body"
    for i in range(3, -1, -1):
        H.bone(names[i], par, (0, hb + 0.35, zs[i] + Lz / n * 0.5))
        front.append(names[i])
        par = names[i]
    back = []
    par = "Body"
    for i in range(4, n):
        if i == 4:
            H.bone(names[i], "Body", (0, hb + 0.35, zs[i] - Lz / n * 0.5))
        else:
            H.bone(names[i], par, (0, hb + 0.35, zs[i] - Lz / n * 0.5))
        back.append(names[i])
        par = names[i]
    seg = Lz / n
    for i in range(n):
        z = zs[i]
        w = wfun(z)
        # an arched plate (butterfly-shaped with a beaked keel), overlapping the next one back
        pl = ellipsoid(w * 0.78, 0.36, seg * 0.72, (0, hb + 0.05, z + seg * 0.08))
        pl = pl.ss(ellipsoid(w * 0.72, 0.3, seg * 0.8, (0, hb - 0.02, z + seg * 0.08)), 0.03)
        pl = pl.su(capsule((0, hb + 0.38, z - seg * 0.3), (0, hb + 0.38, z + seg * 0.45), 0.06), 0.06) & S.SDF(lambda P: hb - 0.02 - P[:, 1])
        if i == 0 or i == n - 1:
            pl = ellipsoid(w * 0.8, 0.36, seg * 0.85, (0, hb + 0.05, z)).ss(ellipsoid(w * 0.72, 0.3, seg * 0.8, (0, hb - 0.02, z)), 0.03) & S.SDF(lambda P: hb - 0.02 - P[:, 1])
        pat = combine(lambda P, z=z: 1 - 0.3 * np.clip(np.abs(P[:, 0]) / 0.25 - 1, 0, 1) * 0.6, lambda P, z=z: 1 - 0.25 * np.clip(np.sin((P[:, 2] - z) * 40) - 0.3, 0, 1))
        H.piece(f"PlateP{i}", names[i], pl, col="primary", mat="hard", tris=420, res=128, role="shell", pri=1.1 + 0.02 * i, pattern=pat)
        # girdle slice for this plate (leathery, spiky texture)
        gz0, gz1 = z - seg * 0.55, z + seg * 0.55

        def gird(P, z=z, gz0=gz0, gz1=gz1):
            q = P - V(0, hb - 0.05, 0)
            outer = _ell(q, W * 1.05, 0.2, Lz * 0.6)
            inner = _ell(q, W * 0.55, 0.3, Lz * 0.45)
            d = np.maximum(outer, -inner)
            d = np.maximum(d, np.maximum(gz0 - P[:, 2], P[:, 2] - gz1))
            return np.maximum(d, 0.04 - P[:, 1])
        H.piece(f"Girdle{i}", names[i], S.SDF(gird).noise(0.012, 30, i), col="secondary", mat="plastic", tris=260, res=128, role="body", pri=1.4,
                pattern=spots(0.08, 0.025, depth=0.4, seed=i))
    # head under the front plate
    H.prim("Mouth", names[0], "Ball", (0.22, 0.08, 0.16), (0, 0.06, zs[0] - 0.05), col="mouth", mat="hard", role="mouth", pri=2.0)
    for i in range(3):
        H.mprim(f"Ocellus{i}#", names[i + 2], "Ball", (0.06,) * 3, (0.16, hb + 0.36, zs[i + 2] + 0.05), col="black", mat="hard", role="eye", pri=2.2)

    def extra(pose, kind, u, k):
        if kind == "move":
            for i, b in enumerate(front + back):
                MS._add(pose, b, (0, 0.015 * math.sin(TAU * (u * 2 - i / 8)), 0, 0, 0, 0))
    MS.armour(H, front=front, back=back, legs=(), ants=(), height=1.0, period=2.0, curl=TAU * 0.55, extra=extra)
    H.socket("mouth", (0, 0.2, -Lz / 2 - 0.1), front[-1])
    H.socket("head", (0, hb + 0.8, 0), "Body")
    H.rig.update({"head": front[-1]})
    return H


# ================================================================================================ helpers: tube chains
def chain(H, names, parent, pts, rads, col="primary", mat="plastic", tris=500, pattern=None, role="body", tr=0.0, res=120, deco=None,
          pri=1.2, first_cap=True, glow=False):
    """Bones at pts[i] (each parented to the previous, the first to `parent`), piece i a tapered tube from pts[i] to
    pts[i+1] with a ball joint (the parent's end cap slightly bigger, so bends never gap)."""
    par = parent
    for i, nm in enumerate(names):
        H.bone(nm, par, T(pts[i]))
        par = nm
    for i, nm in enumerate(names):
        a, b = V(pts[i]), V(pts[i + 1])
        rb = rads[i + 1] * (1.07 if i < len(names) - 1 else 1.0)
        sh = round_cone(T(a), T(b), rads[i], rb)
        if first_cap or i:
            sh = sh | sphere(rads[i], T(a))
        if deco:
            sh = deco(i, sh, a, b)
        H.piece(nm + "P", nm, sh, col=col, mat=mat, tris=tris if not isinstance(tris, (list, tuple)) else tris[i], pattern=pattern,
                role=role, tr=tr, res=res, pri=pri, glow=glow)
    return list(names)


def bumps(sd, n, xr, zr, ytop, ybot, r0, r1, seed=0, cone=0.0):
    """Papillae / warts on the top surface of sd (spheres, or little cones of height `cone`)."""
    out = []
    rng = np.random.default_rng(seed + 100)
    for p in surface_pts(sd, n, xr, zr, ytop, ybot, seed=seed):
        r = rng.uniform(r0, r1)
        if cone:
            out.append(round_cone(T(p - V(0, r * 0.5, 0)), T(p + V(0, cone * rng.uniform(0.7, 1.3), 0)), r, r * 0.25))
        else:
            out.append(sphere(r, T(p - V(0, r * 0.35, 0))))
    return union_all(out) if out else None


# ================================================================================================ sea cucumber / sea pig / sea mouse
def _holo(hid, prev, kind="cucumber"):
    pig, mouse = kind == "pig", kind == "mouse"
    H = Hero(hid, plan="Worm" if mouse else "Blob", gait="slither", tags=["echinoderm" if not mouse else "worm", "aquatic", "squishy"])
    H.preview = prev
    if pig:
        y, R, Lz, flat = 0.95, 0.62, 2.4, 0.85
    elif mouse:
        y, R, Lz, flat = 0.42, 0.72, 2.5, 0.5
    else:
        y, R, Lz, flat = 0.52, 0.55, 3.4, 0.9
    H.body((0, y, -Lz * 0.25))
    bounds(H, (-2.2, -0.4, -Lz * 0.5 - 1.6), (2.2, y + 2.2, Lz * 0.5 + 1.2))
    zs = [-Lz * 0.25, Lz * 0.0, Lz * 0.25, Lz * 0.5]
    prof = lambda z: R * math.sqrt(max(0.08, 1 - (z / (Lz * 0.55)) ** 2)) ** 0.6

    def segsd(z0, z1):
        def f(P):
            q = P - V(0, y, 0)
            r = np.array([prof(z) for z in np.clip(P[:, 2], -Lz * 0.55, Lz * 0.55)]) if False else R * np.sqrt(np.maximum(0.08, 1 - (P[:, 2] / (Lz * 0.55)) ** 2)) ** 0.6
            d = np.hypot(q[:, 0], q[:, 1] / flat) - r
            ends = _ell(q, R * 1.02, R * flat * 1.02, Lz * 0.55)
            d = np.maximum(d * flat, ends)
            return np.maximum(d, np.maximum(z0 - P[:, 2], P[:, 2] - z1))
        return S.SDF(f)
    full = segsd(-9, 9)
    if mouse:
        skin = lambda P: 1 - 0.3 * np.clip(np.sin(P[:, 0] * 37 + np.sin(P[:, 2] * 23) * 2) * np.sin(P[:, 2] * 41) - 0.1, 0, 1)
    elif pig:
        skin = combine(gradient(1, y - R, y + R * 0.8, 0.85, 1.0), spots(0.25, 0.08, depth=0.12, seed=4))
    else:
        skin = combine(gradient(1, y - R * 0.6, y + R * 0.8, 0.7, 1.0), spots(0.22, 0.06, depth=0.3, seed=2))
    # Head (front) on Body, then Seg1..3 chained backwards
    names = ["Seg1", "Seg2", "Seg3"]
    par = "Body"
    for i, nm in enumerate(names):
        H.bone(nm, par, (0, y, zs[i + 0] + (Lz * 0.25 if i else 0.0)))
        par = nm
    cuts = [(-9, -Lz * 0.25 + 0.05)] + [(-Lz * 0.25 + Lz * 0.25 * i - 0.05 + (0.1 if i == 0 else 0), -Lz * 0.25 + Lz * 0.25 * (i + 1) + 0.05) for i in range(3)]
    cuts = [(-9, -Lz * 0.22), (-Lz * 0.26, Lz * 0.03), (Lz * -0.01, Lz * 0.28), (Lz * 0.24, 9)]
    bones = ["Body", "Seg1", "Seg2", "Seg3"]
    # bones: Body at the front quarter; Seg1 at the middle; Seg2 at the back quarter; Seg3 near the tail
    H.bones[H.bidx["Seg1"]] = ("Seg1", "Body", (0.0, y, -Lz * 0.24))
    H.bones[H.bidx["Seg2"]] = ("Seg2", "Seg1", (0.0, y, Lz * 0.02))
    H.bones[H.bidx["Seg3"]] = ("Seg3", "Seg2", (0.0, y, Lz * 0.26))
    deco_all = None
    if not mouse:
        deco_all = bumps(full, 26 if not pig else 10, (-R * 0.8, R * 0.8), (-Lz * 0.5, Lz * 0.5), y + R + 0.3, y - R * 0.2,
                         0.07, 0.13, seed=5, cone=0.12 if not pig else 0.0)
    for i, (z0, z1) in enumerate(cuts):
        sd = segsd(z0, z1)
        if deco_all is not None:
            sd = sd.su(deco_all & S.SDF(lambda P, z0=z0, z1=z1: np.maximum(z0 - P[:, 2], P[:, 2] - z1)), 0.04)
        if mouse:
            sd = sd.noise(0.035, 22.0, i)
        nm = "Head" if i == 0 else f"BodyP{i}"
        H.piece(nm if i else "HeadP", bones[i] if i else "Body", sd, col="primary", mat="fur" if mouse else "plastic", tris=1000 if i in (1, 2) else 800,
                res=124, role="body" if i else "head", pattern=skin, tr=0.12 if pig else 0.0)
    legpairs = []
    zf = -Lz * 0.5
    if not mouse:
        # feeding tentacles round the mouth: a ring of little branched bushes
        tc = V(0, y - (0.05 if not pig else 0.25), zf - 0.05)
        bush = []
        nt = 10 if not pig else 8
        for i in range(nt):
            a = TAU * i / nt
            d = V(math.cos(a) * 0.8, math.sin(a) * 0.8, -0.6)
            d /= np.linalg.norm(d)
            b0 = tc + V(math.cos(a), math.sin(a), 0) * R * 0.45
            b1 = b0 + d * (0.35 if not pig else 0.25)
            bush.append(round_cone(T(b0), T(b1), 0.06, 0.04))
            for j in range(3):
                aa = a + (j - 1) * 0.6
                bush.append(round_cone(T(b1), T(b1 + V(math.cos(aa) * 0.12, math.sin(aa) * 0.12, -0.12)), 0.035, 0.022))
        H.bone("Tentacles", "Body", T(tc))
        H.piece("TentaclesP", "Tentacles", union_all(bush, 0.02), col="secondary", mat="plastic", tris=900, res=150, role="detail", pri=1.4)
    if pig:
        # walking tube-legs (pairs on their own bones) and the dorsal 'antennae' papillae
        for i in range(5):
            z = -Lz * 0.38 + i * Lz * 0.19
            bn = f"Legs{i}"
            H.bone(bn, bones[min(3, max(0, int((z + Lz * 0.5) / (Lz * 0.26))))], (0, y - R * 0.5, z))
            lp = []
            for sx in (-1, 1):
                b0 = V(sx * R * 0.55, y - R * 0.6, z)
                lp.append(tube([T(b0), T(b0 + V(sx * 0.18, -0.4, -0.05)), (sx * R * 0.85, 0.06, z - 0.08)], [0.12, 0.1, 0.075], k=0.03))
            H.piece(f"LegsP{i}", bn, union_all(lp), col="primary", mat="plastic", tris=360, res=130, role="limb", pri=1.5, tr=0.12)
            legpairs.append(bn)
        H.bone("Papillae", "Body", (0, y + R * 0.7, -Lz * 0.32))
        pap = []
        for sx in (-1, 1):
            for k, (zz, ln) in enumerate(((-Lz * 0.36, 1.0), (-Lz * 0.22, 0.75))):
                b0 = V(sx * 0.16, y + R * 0.75, zz)
                pap.append(tube([T(b0), T(b0 + V(sx * 0.12, 0.45 * ln, -0.1)), T(b0 + V(sx * 0.25, 0.8 * ln, -0.32))], [0.09, 0.07, 0.04], k=0.03))
        H.piece("PapillaeP", "Papillae", union_all(pap, 0.02), col="primary", mat="plastic", tris=500, res=140, role="detail", pri=1.4, tr=0.12)
    if mouse:
        # iridescent bristle fans along both flanks + a felt of short setae on top, little parapodia legs below
        for k, bn in enumerate(("Body", "Seg2")):
            zr = (-Lz * 0.5, -Lz * 0.02) if k == 0 else (-Lz * 0.02, Lz * 0.48)
            for sx in (1,):
                pass
            br = []
            for i in range(14):
                z = zr[0] + (zr[1] - zr[0]) * (i + 0.5) / 14
                rr = R * math.sqrt(max(0.08, 1 - (z / (Lz * 0.55)) ** 2)) ** 0.6
                b0 = V(rr * 0.9, y - 0.05, z)
                for j in range(3):
                    br.append(round_cone(T(b0), T(b0 + V(0.55 + 0.1 * j, 0.15 * j - 0.1, (j - 1) * 0.12 + 0.15)), 0.03, 0.008))
            fan = union_all(br)
            H.mbone(f"Bristle{k}#", bn, (R * 0.85, y, (zr[0] + zr[1]) / 2))
            H.mpiece(f"BristleP{k}#", f"Bristle{k}#", fan, col="gem", mat="glass", tris=700, res=160, role="detail", pri=1.5)
        for i in range(4):
            z = -Lz * 0.36 + i * Lz * 0.24
            bn = f"Legs{i}"
            H.bone(bn, bones[min(3, i)], (0, y - R * flat * 0.6, z))
            lp = [round_cone((sx * R * 0.6, y - R * flat * 0.7, z), (sx * R * 0.95, 0.04, z + 0.05), 0.08, 0.05) for sx in (-1, 1)]
            H.piece(f"LegsP{i}", bn, union_all(lp), col="secondary", mat="plastic", tris=240, role="limb", pri=1.6)
            legpairs.append(bn)
    import motion_bugs as MB
    MB.crawler(H, ["Body", "Seg1", "Seg2", "Seg3"], legpairs=legpairs, head="Body", mode="inch" if not mouse else "slither",
               period=1.8 if not pig else 1.1, height=1.2, amp=0.1 if not mouse else 0.12, leg_amp=0.35, attack="rear")
    if not mouse:
        def ext(pose):
            return pose
    H.socket("mouth", (0, y, zf - 0.3), "Body")
    H.socket("head", (0, y + R + 0.5, -Lz * 0.25), "Body")
    H.rig.update({"head": "Body", "tail": ["Seg1", "Seg2", "Seg3"]})
    return H


@hero("sea cucumber", FAM)
def sea_cucumber():
    return _holo("sea cucumber", {"primary": "#7A4A3A", "secondary": "#C88A6A"}, "cucumber")


@hero("sea pig", FAM)
def sea_pig():
    return _holo("sea pig", {"primary": "#F2B8C0", "secondary": "#F7D8E0"}, "pig")


@hero("sea mouse", FAM)
def sea_mouse():
    return _holo("sea mouse", {"primary": "#C8A07A", "secondary": "#8A6A4A", "gem": "#6AE8C0"}, "mouse")


# ================================================================================================ blobfish
@hero("blobfish", FAM)
def blobfish():
    """A droopy pink jelly: a big sagging head with a huge drooping nose, a glum down-turned mouth and tiny eyes, the
    body tapering to a little tail; it wobbles like jelly as it swims."""
    H = Hero("blobfish", plan="Fish", gait="swim", tags=["fish", "aquatic", "deepsea", "squishy"])
    H.preview = {"primary": "#E8B0B0", "secondary": "#F2D0D0"}
    y = 1.3
    H.body((0, y, 0))
    bounds(H, (-2.2, -0.3, -2.4), (2.2, 3.0, 3.6))
    sag = lambda P: np.column_stack([P[:, 0], P[:, 1] + 0.25 * np.clip(1 - np.abs(P[:, 0]) / 1.1, 0, 1) ** 2 * np.clip(-(P[:, 2]) / 1.2, 0, 1), P[:, 2]])
    head = ellipsoid(1.12, 0.92, 1.15, (0, y + 0.05, -0.15)).warp(sag)
    head = head.su(ellipsoid(0.9, 0.62, 0.8, (0, y - 0.45, -0.35)), 0.35)                       # jowls / sagging chin
    head = head.su(ellipsoid(0.75, 0.65, 0.9, (0, y - 0.05, 0.75)), 0.4)                        # body behind the head
    # the nose: a fat droop hanging over the mouth
    nose = round_cone((0, y + 0.25, -1.05), (0, y - 0.32, -1.32), 0.3, 0.36)
    head = head.su(nose, 0.25)
    mouth = S.SDF(lambda P: np.maximum(np.abs(np.hypot(P[:, 0] * 0.9, (P[:, 1] - (y - 0.95)) * 1.0) - 0.48) - 0.035, np.maximum(-P[:, 1] + y - 0.65, P[:, 2] + 0.85)))
    head = head.ss(mouth, 0.03)
    wr = lambda P: 1 - 0.18 * np.clip(np.sin(P[:, 1] * 16 + np.sin(P[:, 0] * 5) * 1.5) * 2 - 1.2, 0, 1)
    H.piece("BodyP", "Body", head.noise(0.025, 4.0, 2), col="primary", mat="plastic", tris=1500, res=128, role="body",
            pattern=combine(wr, gradient(1, y - 1.0, y + 0.9, 0.85, 1.0)))
    H.prim("Lip", "Body", "Ball", (0.7, 0.12, 0.2), (0, y - 0.68, -1.02), rot=(0.25, 0, 0), col="mouth", mat="plastic", role="mouth", pri=1.8)
    H.eyes("Body", (0.48, y + 0.32, -1.02), 0.07, col="pupil", pupil=None, look=(0.5, 0.1, -1.0))
    tail = []
    pts = [V(0, y, 1.2), V(0, y + 0.02, 1.95), V(0, y + 0.05, 2.6)]
    names = ["Tail1", "Tail2"]
    chain(H, names, "Body", pts, [0.48, 0.28, 0.14], col="primary", tris=500, res=120,
          deco=lambda i, sh, a, b: sh if i == 0 else sh.su(plate(T(b), (0, 0, 1), (0, 1, 0), [(-0.15, -0.5), (0.55, -0.6), (0.4, 0), (0.55, 0.6), (-0.15, 0.5)], 0.06), 0.06))
    H.mpiece("Pec#", "Body", plate((0.85, y - 0.3, 0.35), (1, -0.3, 0.6), (0, 1, 0), [(0, -0.2), (0.55, -0.3), (0.6, 0.15), (0, 0.25)], 0.06, bend=0.3),
             col="secondary", mat="plastic", tris=260, role="fin", pri=1.5, tr=0.15)
    H.mbone("Pec#", "Body", (0.85, y - 0.3, 0.35))
    for p_ in H.parts:
        if p_["name"] in ("PecR", "PecL"):
            p_["bone"] = p_["name"]

    def extra(pose, kind, u, s):
        if kind in ("move", "idle"):
            MS._add(pose, "Body", (0, 0, 0, 0.03 * math.sin(TAU * u * 2), 0, 0))  # jelly wobble
    MA.swim(H, names, head=None, pecs=[("PecR", "PecL")], mode="yaw", period=1.6, amp=0.3, length=3.5, attack="bite", body_amp=0.05, extra=extra, idle_period=4.0)
    H.socket("mouth", (0, y - 0.7, -1.2), "Body")
    H.socket("head", (0, y + 1.2, -0.1), "Body")
    H.rig.update({"head": "Body", "tail": names})
    return H


# ================================================================================================ salp / siphonophore / pyrosome
@hero("salp", FAM)
def salp():
    """A chain of clear jelly barrels hooked side by side, each ringed with muscle bands and holding an orange gut
    nucleus; the chain drifts on a slow wave, the barrels pulsing one after another."""
    H = Hero("salp", plan="Blob", gait="float", tags=["tunicate", "aquatic", "jelly", "colony"])
    H.preview = {"primary": "#E8F4F8", "secondary": "#C8E8F0"}
    y = 1.7
    H.body((0, y, -1.8))
    bounds(H, (-1.8, -0.2, -3.2), (1.8, 3.6, 3.4))
    n = 6
    names = [f"Zooid{i}" for i in range(n)]
    par = "Body"
    pulses = []
    for i in range(n):
        z = -1.8 + i * 0.72
        sx = 0.18 * (1 if i % 2 else -1)
        H.bone(names[i], par if i else "Body", (sx * 0.3, y, z - 0.36))
        par = names[i]
        c = V(sx, y, z)
        ax = V(0.55 * (1 if i % 2 else -1), 0.0, 0.25)
        brl = capsule(T(c - ax * 0.55), T(c + ax * 0.55), 0.42).scale3(1, 1, 1) if False else ellipsoid(0.62, 0.42, 0.36, T(c)).rot(0, 0, 0)
        brl = ellipsoid(0.68, 0.42, 0.38, (0, 0, 0)).rot(0, math.degrees(math.atan2(ax[2], ax[0])) * 0.0 + (20 if i % 2 else -20), 0).at(*T(c))
        brl = brl.ss(sphere(0.12, T(c + V(0.66 * (1 if i % 2 else -1), 0, 0))), 0.05)       # siphon openings
        bands = lambda P, c=c: 1 - 0.4 * np.clip(np.sin((P[:, 0] - c[0]) * 22) * 2 - 1.2, 0, 1)
        H.piece(f"BarrelP{i}", names[i], brl, col="primary", mat="glass", tr=0.4, tris=500, res=120, role="body", pri=1.1, pattern=bands)
        H.prim(f"Gut{i}", names[i], "Ball", (0.2, 0.2, 0.2), T(c + V(0, -0.12, 0.05)), col=(0.92, 0.52, 0.28), mat="plastic", role="gem", pri=1.6)
        pulses.append((names[i], (0, 0.05, 0)))
    MS.drift(H, names, height=2.0, period=2.6, amp=0.14, axis="yaw", pulses=pulses, bob=0.06, attack="lash")
    H.socket("mouth", (0, y, -2.3), "Body")
    H.socket("head", (0, y + 0.8, -1.8), "Body")
    H.rig.update({"head": "Body", "tail": names[1:]})
    return H


@hero("siphonophore", FAM)
def siphonophore():
    """A drifting colony: a gas float up front, a cluster of clear swimming bells, then a long stem strung with glowing
    feeding clusters and trailing stinging tentacles."""
    H = Hero("siphonophore", plan="Blob", gait="float", tags=["jelly", "aquatic", "colony", "venomous"])
    H.preview = {"primary": "#F2C8E0", "secondary": "#8AD0F0", "glow": "#FFB0E0"}
    y = 2.6
    H.body((0, y, -2.4))
    bounds(H, (-1.8, -0.2, -3.6), (1.8, 4.2, 4.6))
    flt = ellipsoid(0.28, 0.42, 0.28, (0, y + 0.55, -2.75)).su(capsule((0, y, -2.6), (0, y + 0.3, -2.7), 0.1), 0.08)
    H.piece("Float", "Body", flt, col="primary", mat="glass", tr=0.25, tris=400, role="head", pri=1.1,
            pattern=gradient(1, y + 0.4, y + 0.95, 1.0, 0.55))
    H.prim("FloatTip", "Body", "Ball", (0.16, 0.16, 0.16), (0, y + 0.95, -2.75), col="red", mat="plastic", role="detail", pri=1.6)
    pulses = []
    for k in range(3):
        bn = f"Bells{k}"
        H.bone(bn, "Body", (0, y, -2.25 + k * 0.42))
        bl = []
        for sx in (-1, 1):
            c = V(sx * 0.32, y - 0.05 + 0.05 * k, -2.25 + k * 0.42)
            b = ellipsoid(0.3, 0.26, 0.24, T(c)).ss(ellipsoid(0.18, 0.16, 0.2, T(c + V(sx * 0.12, 0, 0.06))), 0.03)
            bl.append(b)
        H.piece(f"BellsP{k}", bn, union_all(bl), col="secondary", mat="glass", tr=0.4, tris=500, role="body", pri=1.2)
        pulses.append((bn, (0, 0, 0.08)))
    names = [f"Stem{i}" for i in range(4)]
    pts = [V(0, y, -1.0), V(0, y - 0.1, 0.0), V(0, y - 0.2, 1.0), V(0, y - 0.25, 2.0), V(0, y - 0.25, 3.0)]
    par = "Body"
    tents = []
    rng = np.random.default_rng(3)
    for i, nm in enumerate(names):
        H.bone(nm, par, T(pts[i]))
        par = nm
        a, b = pts[i], pts[i + 1]
        stem = round_cone(T(a), T(b), 0.06, 0.055) | sphere(0.065, T(a))
        if i == 0:
            stem = stem | round_cone((0, y, -2.4), T(a), 0.07, 0.06)
        brs = []
        gl = []
        for j in range(2):
            c = a + (b - a) * (0.3 + 0.45 * j)
            for q in range(3):
                ang = TAU * q / 3 + j
                d = V(math.cos(ang), math.sin(ang), 0.4)
                brs.append(ellipsoid(0.16, 0.06, 0.22, (0, 0, 0)).rot(0, 0, math.degrees(ang)).at(*T(c + d * 0.16)))
            gl.append(sphere(0.09, T(c + V(0, -0.12, 0))))
            gl.append(sphere(0.06, T(c + V(0.1, -0.05, 0.08))))
        H.piece(f"StemP{i}", nm, stem.su(union_all(brs), 0.04), col="primary", mat="glass", tr=0.3, tris=600, res=140, role="body", pri=1.2)
        H.piece(f"Glow{i}", nm, union_all(gl), col="glow", mat="plastic", tris=200, res=140, role="detail", pri=1.6, glow=True)
        tb = f"Tent{i}"
        c = a + (b - a) * 0.5
        H.bone(tb, nm, T(c + V(0, -0.1, 0)))
        th = []
        for j in range(2):
            o = c + V((j - 0.5) * 0.15, -0.1, (j - 0.5) * 0.3)
            pp = [o, o + V(0.05, -0.7, 0.15), o + V(-0.05, -1.4, 0.35), o + V(0.02, -1.9, 0.6)]
            th.append(tube([T(p) for p in pp], [0.03, 0.025, 0.02, 0.012], k=0.02))
            for kk in range(3):
                pk = pp[1] + (pp[3] - pp[1]) * (kk / 3)
                th.append(sphere(0.035, T(pk + V(0.03, 0, 0))))
        H.piece(f"TentP{i}", tb, union_all(th), col="secondary", mat="plastic", tris=400, res=150, role="tentacle", pri=1.7, tr=0.2)
        tents.append((tb, 1 if i % 2 else -1))
    MS.drift(H, names, height=2.6, period=3.0, amp=0.15, axis="yaw", pulses=pulses, tents=tents, bob=0.05, attack="lash")
    H.socket("mouth", (0, y - 0.5, -1.0), "Body")
    H.socket("head", (0, y + 1.2, -2.6), "Body")
    H.rig.update({"head": "Body", "tail": names})
    return H


@hero("pyrosome", FAM)
def pyrosome():
    """A glowing hollow sea-pickle: a long tube closed at the front and open at the back, its wall packed with spiky
    zooids whose tips glow; it drifts and ripples along its length."""
    H = Hero("pyrosome", plan="Blob", gait="float", tags=["tunicate", "aquatic", "colony", "glow"])
    H.preview = {"primary": "#E8D8F8", "secondary": "#8AE8F0", "glow": "#8AE8F0"}
    y = 1.5
    H.body((0, y, -1.0))
    bounds(H, (-1.6, -0.2, -2.8), (1.6, 3.2, 2.8))
    names = ["Tube1", "Tube2", "Tube3"]
    zs = [-1.0, 0.0, 1.0]
    Lz = 1.95
    par = "Body"
    for i, nm in enumerate(names):
        H.bone(nm, par, (0, y, zs[i] - (0.0 if i == 0 else 0.0)))
        par = nm

    def wall(P):
        q = P - V(0, y, 0)
        r = 0.62 - 0.08 * np.clip(q[:, 2] / Lz, -1, 1)
        rho = np.hypot(q[:, 0], q[:, 1])
        d = np.abs(rho - r + 0.08) - 0.09
        cap = _ell(q - V(0, 0, -0.2), 0.7, 0.7, Lz + 0.2)
        return np.maximum(d, np.maximum(cap, q[:, 2] - Lz))
    wsd = S.SDF(wall)
    pts = []
    for i in range(8):
        for j in range(16):
            z = -Lz * 0.85 + i * Lz * 1.8 / 7
            a = TAU * j / 16 + i * 0.4
            r = 0.62 - 0.08 * z / Lz + 0.02
            pts.append(V(r * math.cos(a), y + r * math.sin(a), z))
    for i, nm in enumerate(names):
        z0 = -Lz - 0.5 if i == 0 else zs[i] - 0.5
        z1 = zs[i] + 0.5 if i < 2 else Lz + 0.1
        cut = S.SDF(lambda P, z0=z0, z1=z1: np.maximum(z0 - P[:, 2], P[:, 2] - z1))
        mine = [p for p in pts if z0 + 0.06 < p[2] < z1 - 0.06]
        spikes = []
        tips = []
        for p in mine:
            nrm = V(p[0], p[1] - y, 0)
            nrm /= np.linalg.norm(nrm)
            spikes.append(round_cone(T(p - nrm * 0.08), T(p + nrm * 0.14 + V(0, 0, 0.04)), 0.1, 0.045))
            tips.append(sphere(0.06, T(p + nrm * 0.15 + V(0, 0, 0.04))))
        H.piece(f"WallP{i}", nm, (wsd & cut).su(union_all(spikes) & cut, 0.04), col="primary", mat="glass", tr=0.08, tris=1400, res=150, role="body", pri=1.1)
        H.piece(f"Glow{i}", nm, union_all(tips), col="glow", mat="plastic", tris=500, res=160, role="detail", pri=1.6, glow=True)
    pulses = [(nm, (0, 0.04, 0)) for nm in names]
    MS.drift(H, names, height=1.8, period=2.8, amp=0.12, axis="pitch", pulses=pulses, bob=0.06, attack="lash")
    H.socket("mouth", (0, y, Lz + 0.2), names[-1])
    H.socket("head", (0, y + 1.0, -1.0), "Body")
    H.rig.update({"head": "Body", "tail": names[1:]})
    return H


# ================================================================================================ sessile: sea squirt / hydra / tube worms
@hero("sea squirt", FAM)
def sea_squirt():
    """A squishy translucent vase on a holdfast with two lobed siphons (one on top, one to the side) that pucker and
    squirt; the gut shows through the tunic."""
    H = Hero("sea squirt", plan="Blob", gait="hop", tags=["tunicate", "aquatic", "squishy"])
    H.preview = {"primary": "#E8A04A", "secondary": "#F2D07A"}
    H.body((0, 0.2, 0))
    bounds(H, (-1.8, -0.3, -1.8), (1.8, 3.6, 1.8))
    base = ellipsoid(0.75, 0.22, 0.7, (0, 0.15, 0)).noise(0.04, 6, 1) & S.SDF(lambda P: -P[:, 1])
    H.piece("Holdfast", "Body", base, col="secondary", mat="plastic", tris=400, role="foot", pri=1.4)
    H.bone("Bag", "Body", (0, 0.35, 0))
    H.bone("Bag2", "Bag", (0, 1.25, 0))
    bag = round_cone((0, 0.5, 0), (0, 1.55, 0.05), 0.55, 0.68).su(ellipsoid(0.6, 0.5, 0.58, (0, 1.75, 0.05)), 0.3)
    bag = bag.noise(0.02, 5.0, 3)
    lower = bag & S.SDF(lambda P: P[:, 1] - 1.3)
    upper = bag & S.SDF(lambda P: 1.22 - P[:, 1])
    ridges = lambda P: 1 - 0.15 * np.clip(np.sin(np.arctan2(P[:, 0], P[:, 2]) * 8 + P[:, 1] * 2) * 2 - 1.2, 0, 1)
    H.piece("BagLow", "Bag", lower.su(base.round(-0.05), 0.15) & S.SDF(lambda P: P[:, 1] - 1.3), col="primary", mat="glass", tr=0.15, tris=800, res=124, role="body", pattern=ridges)
    H.piece("BagUp", "Bag2", upper, col="primary", mat="glass", tr=0.15, tris=800, res=124, role="body", pattern=ridges)
    H.prim("Gut", "Bag", "Ball", (0.55, 0.7, 0.5), (0, 0.95, 0.05), col="dark", mat="plastic", role="detail", pri=2.0)
    crowns = []
    for nm, b0, d, r in (("Oral", V(0, 2.1, 0.0), V(0, 1, -0.15), 0.26), ("Atrial", V(0.45, 1.65, 0.1), V(1, 0.75, 0.1), 0.2)):
        d = d / np.linalg.norm(d)
        H.bone(nm, "Bag2", T(b0))
        sp = round_cone(T(b0 - d * 0.1), T(b0 + d * 0.45), r, r * 0.95)
        lobes = union_all([sphere(r * 0.42, T(b0 + d * 0.48 + (V(math.cos(a), 0, math.sin(a)) - d * (V(math.cos(a), 0, math.sin(a)) @ d)) * r * 0.85))
                           for a in (TAU * k / (4 if nm == "Oral" else 6) for k in range(4 if nm == "Oral" else 6))])
        sp = sp.su(lobes, 0.06).ss(round_cone(T(b0 + d * 0.15), T(b0 + d * 0.8), r * 0.55, r * 0.55), 0.04)
        H.piece(nm + "P", nm, sp, col="secondary", mat="plastic", tris=500, res=140, role="detail", pri=1.3)
        crowns.append((nm, (float(d[0]), float(d[2])), 1.0))
    MS.sessile(H, stalks=[["Bag", "Bag2"]], crowns=crowns, retract=[], height=2.4, period=1.2, attack="squirt", hop=0.06)
    H.socket("mouth", (0, 2.6, 0), "Oral")
    H.socket("head", (0, 2.7, 0), "Bag2")
    H.rig.update({"head": "Bag2"})
    return H


@hero("hydra polyp", FAM)
def hydra_polyp():
    """A slender green polyp on a sticky basal disc: a stalk and body column, a domed mouth cone and a crown of six long
    wavy tentacles studded with stinging knobs, a little bud growing from its side."""
    H = Hero("hydra polyp", plan="Blob", gait="hop", tags=["cnidarian", "aquatic", "polyp", "venomous"])
    H.preview = {"primary": "#8AC87A", "secondary": "#D8F0C8"}
    H.body((0, 0.1, 0))
    bounds(H, (-2.4, -0.3, -2.4), (2.4, 4.6, 2.4))
    H.piece("Disc", "Body", ellipsoid(0.42, 0.12, 0.42, (0, 0.08, 0)) & S.SDF(lambda P: -P[:, 1]), col="secondary", mat="plastic", tris=300, role="foot", pri=1.4)
    stalk = chain(H, ["Stalk1", "Stalk2"], "Body", [V(0, 0.12, 0), V(0.05, 1.05, 0.05), V(0, 2.0, 0)], [0.17, 0.2, 0.3], col="primary", tris=500,
                  pattern=gradient(1, 0.1, 2.5, 0.7, 1.0))
    H.bone("Crown", "Stalk2", (0, 2.0, 0))
    col_ = round_cone((0, 2.0, 0), (0, 2.65, 0), 0.32, 0.36).su(ellipsoid(0.3, 0.28, 0.3, (0, 2.82, 0)), 0.12)
    col_ = col_.su(round_cone((0, 2.8, 0), (0, 3.1, 0), 0.18, 0.08), 0.1)                       # hypostome
    H.piece("ColumnP", "Crown", col_, col="primary", mat="plastic", tris=700, role="head", pri=1.1)
    H.prim("Mouth", "Crown", "Ball", (0.08, 0.05, 0.08), (0, 3.12, 0), col="mouth", mat="hard", role="mouth", pri=2.0)
    crowns = []
    for i in range(6):
        a = TAU * i / 6 + 0.3
        d = V(math.cos(a), 0, math.sin(a))
        b0 = V(0, 2.82, 0) + d * 0.24
        nm = f"Tentacle{i}"
        H.bone(nm, "Crown", T(b0))
        pp = [b0, b0 + d * 0.45 + V(0, 0.5, 0), b0 + d * 1.0 + V(0, 0.65, 0), b0 + d * 1.5 + V(0, 0.35, 0), b0 + d * 1.85 + V(0, -0.15, 0)]
        sh = tube([T(p) for p in pp], [0.07, 0.06, 0.05, 0.04, 0.028], k=0.03)
        kn = [sphere(0.045, T(pp[1] + (pp[4] - pp[1]) * t + V(0, 0.03, 0))) for t in np.linspace(0.05, 0.95, 6)]
        H.piece(nm + "P", nm, sh.su(union_all(kn), 0.02), col="primary", mat="plastic", tris=400, res=150, role="tentacle", pri=1.4)
        crowns.append((nm, (float(d[0]), float(d[2])), 1.0))
    # a bud on the stalk
    H.bone("Bud", "Stalk1", (0.15, 0.9, 0.0))
    bud = round_cone((0.15, 0.9, 0), (0.55, 1.25, 0.05), 0.11, 0.13)
    bud = bud.su(union_all([round_cone((0.58, 1.33, 0.05), T(V(0.58, 1.33, 0.05) + V(math.cos(a) * 0.25, 0.22, math.sin(a) * 0.25)), 0.03, 0.015) for a in (0, 2.1, 4.2)]), 0.02)
    H.piece("BudP", "Bud", bud, col="secondary", mat="plastic", tris=300, role="detail", pri=1.6)
    MS.sessile(H, stalks=[stalk + ["Crown"]], crowns=crowns, retract=[], height=3.0, period=1.6, attack="lash", hop=0.05)
    H.socket("mouth", (0, 3.15, 0), "Crown")
    H.socket("head", (0, 3.4, 0), "Crown")
    H.rig.update({"head": "Crown"})
    return H


@hero("giant tube worm", FAM)
def giant_tube_worm():
    """A clump of tall white chitin tubes rising from a dark vent rock, each crowned with a blood-red gill plume that
    sways and snaps back into its tube."""
    H = Hero("giant tube worm", plan="Worm", gait="slither", tags=["worm", "aquatic", "deepsea"])
    H.preview = {"primary": "#E8302A", "secondary": "#F2EEE6", "darkStone": "#3A3634"}
    H.body((0, 0.3, 0))
    bounds(H, (-2.2, -0.3, -2.2), (2.2, 4.8, 2.2))
    rock = ellipsoid(1.2, 0.5, 1.0, (0, 0.2, 0)).su(ellipsoid(0.6, 0.45, 0.6, (0.7, 0.25, 0.4)), 0.2).noise(0.07, 4.0, 3) & S.SDF(lambda P: -P[:, 1])
    H.piece("Rock", "Body", rock, col="darkStone", mat="stone", tris=800, role="foot", pri=1.3, pattern=spots(0.3, 0.1, depth=0.4, seed=2))
    spec = [(0.0, 0.0, 3.6, 0.0), (0.55, 0.3, 2.9, 0.25), (-0.55, 0.25, 2.5, -0.2), (0.2, -0.55, 2.2, 0.1), (-0.3, -0.35, 3.1, -0.15), (0.85, -0.2, 1.7, 0.3)]
    stalks, retract, crowns = [], [], []
    for i, (x, z, h, lean) in enumerate(spec):
        b0 = V(x, 0.3, z)
        top = b0 + V(lean * h * 0.25, h, -0.1 * h * 0.2)
        mid = b0 + (top - b0) * 0.5 + V(lean * 0.15, 0, 0)
        nm = [f"Tube{i}a", f"Tube{i}b"]
        r = 0.17 - 0.01 * i

        def deco(j, sh, a, b, r=r, top=top):
            if j == 1:
                sh = sh.ss(capsule(T(top - (top - a) * 0.15), T(top + (top - a) * 0.3), r * 0.7), 0.02)
            return sh
        chain(H, nm, "Body", [b0, mid, top], [r, r * 1.02, r * 1.08], col="secondary", tris=[350, 400], res=130, deco=deco,
              pattern=stripes(lambda P: P[:, 1], 6.0, width=0.12, depth=0.2))
        pb = top - V(0, 0.15, 0)
        pn = f"Plume{i}"
        H.bone(pn, nm[1], T(pb))
        d = (top - mid) / np.linalg.norm(top - mid)
        plume = round_cone(T(pb), T(pb + d * 0.75), r * 1.0, r * 1.25).su(sphere(r * 1.2, T(pb + d * 0.78)), 0.08)
        plume = plume.su(union_all([sphere(r * 0.42, T(pb + d * (0.2 + 0.12 * k) + V(math.cos(k * 2.4) * r, 0, math.sin(k * 2.4) * r))) for k in range(6)]), 0.05)
        H.piece(f"PlumeP{i}", pn, plume, col="primary", mat="plastic", tris=400, res=140, role="detail", pri=1.3,
                pattern=stripes(lambda P: P[:, 1], 14.0, width=0.25, depth=0.3))
        stalks.append(nm)
        retract.append((pn, 0.55))
        crowns.append((pn, (float(d[0]) + 0.01, float(d[2]) + 0.01), 0.6))
    MS.sessile(H, stalks=stalks, crowns=crowns, retract=retract, height=3.6, period=2.0, attack="retract", hop=0.0)
    H.socket("mouth", (0, 4.0, 0), "Plume0")
    H.socket("head", (0, 4.4, 0), "Tube0b")
    H.rig.update({"head": "Tube0b"})
    return H


@hero("feather duster worm", FAM)
def feather_duster_worm():
    """A leathery tube rising from a little rock, topped by a banded funnel of feathery radioles (each fringed with
    pinnules) that fans open and whips back into the tube."""
    H = Hero("feather duster worm", plan="Worm", gait="slither", tags=["worm", "aquatic", "reef"])
    H.preview = {"primary": "#E8701E", "secondary": "#F2D8A0", "stone": "#9A9488"}
    H.body((0, 0.2, 0))
    bounds(H, (-2.6, -0.3, -2.6), (2.6, 4.8, 2.6))
    H.piece("Rock", "Body", ellipsoid(0.8, 0.35, 0.7, (0, 0.12, 0)).noise(0.06, 4, 2) & S.SDF(lambda P: -P[:, 1]), col="stone", mat="stone", tris=500, role="foot", pri=1.4)
    tube_ = chain(H, ["Tube1", "Tube2"], "Body", [V(0, 0.2, 0), V(0.08, 1.2, 0.0), V(0.05, 2.3, -0.05)], [0.24, 0.23, 0.25], col="secondary", tris=[400, 450],
                  deco=lambda i, sh, a, b: sh if i == 0 else sh.ss(capsule(T(b - (b - a) * 0.12), T(b + (b - a) * 0.3), 0.17), 0.02),
                  pattern=lambda P: 1 - 0.25 * np.clip(np.sin(P[:, 1] * 12 + np.sin(P[:, 0] * 30) * 0.6) * 2 - 1, 0, 1))
    H.bone("Crown", "Tube2", (0.05, 2.15, -0.05))
    H.piece("Collar", "Crown", torus(0.2, 0.06).at(0.05, 2.3, -0.05), col="primary", mat="plastic", tris=200, role="detail", pri=1.6)
    crowns = []
    groups = 5
    per = 4
    for g in range(groups):
        nm = f"Fan{g}"
        am = TAU * (g + 0.5) / groups
        dm = V(math.cos(am), 0, math.sin(am))
        H.bone(nm, "Crown", T(V(0.05, 2.3, -0.05) + dm * 0.12))
        rads = []
        for k in range(per):
            a = TAU * (g * per + k + 0.5) / (groups * per)
            d = V(math.cos(a), 0, math.sin(a))
            b0 = V(0.05, 2.3, -0.05) + d * 0.14
            pp = [b0, b0 + d * 0.35 + V(0, 0.6, 0), b0 + d * 0.85 + V(0, 1.15, 0), b0 + d * 1.25 + V(0, 1.45, 0)]
            rads.append(tube([T(p) for p in pp], [0.045, 0.04, 0.032, 0.02], k=0.02))
            side = np.cross(d, V(0, 1, 0))
            pins = []
            for t in np.linspace(0.12, 0.95, 9):
                j = t * 3
                i0 = min(int(j), 2)
                c = pp[i0] + (pp[i0 + 1] - pp[i0]) * (j - i0)
                for sg in (1, -1):
                    pins.append(round_cone(T(c), T(c + side * sg * 0.17 * (1.1 - t * 0.5) + d * 0.08 + V(0, 0.06, 0)), 0.02, 0.008))
            rads.append(union_all(pins))
        bands = lambda P: 1 - 0.55 * np.clip(np.sin(np.hypot(P[:, 0] - 0.05, P[:, 2] + 0.05) * 11) * 2 - 0.6, 0, 1)
        H.piece(nm + "P", nm, union_all(rads), col="primary", mat="plastic", tris=900, res=160, role="detail", pri=1.2, pattern=bands)
        crowns.append((nm, (float(dm[0]), float(dm[2])), 1.0))
    MS.sessile(H, stalks=[tube_], crowns=crowns, retract=[("Crown", 1.2)], height=3.8, period=1.8, attack="retract")
    H.socket("mouth", (0, 3.4, 0), "Crown")
    H.socket("head", (0, 4.0, 0), "Crown")
    H.rig.update({"head": "Crown"})
    return H


@hero("christmas tree worm", FAM)
def christmas_tree_worm():
    """Two worms bored into a lumpy brain-coral head, each showing a pair of spiral 'christmas trees' (one worm red, one
    blue) and a spiky operculum; the trees twirl and snap back into the coral."""
    H = Hero("christmas tree worm", plan="Worm", gait="slither", tags=["worm", "aquatic", "reef", "holiday"])
    H.preview = {"primary": "#E8301E", "secondary": "#2A6AE8", "stone": "#C8B89A"}
    H.body((0, 0.3, 0))
    bounds(H, (-2.2, -0.3, -2.2), (2.2, 3.6, 2.2))
    coral = ellipsoid(1.35, 0.85, 1.2, (0, 0.35, 0)).noise(0.05, 3.5, 2) & S.SDF(lambda P: -P[:, 1])
    maze = lambda P: 1 - 0.35 * np.clip(np.sin(P[:, 0] * 9 + np.sin(P[:, 2] * 7) * 2.2) * np.sin(P[:, 2] * 8 + np.sin(P[:, 0] * 5) * 1.5) * 3 - 0.2, 0, 1)
    tops = [V(-0.42, 0, -0.2), V(0.5, 0, 0.25)]
    for t in tops:
        coral = coral.ss(sphere(0.2, T(t + V(0, 1.12, 0))), 0.05)
    H.piece("Coral", "Body", coral, col="stone", mat="stone", tris=1300, res=128, role="foot", pri=1.2, pattern=maze)
    crowns, retract = [], []
    for w, t in enumerate(tops):
        col = "primary" if w == 0 else "secondary"
        base_y = 1.05 + (0.02 if w else 0.0)
        for sx in (-1, 1):
            c = t + V(sx * 0.2, base_y, 0)
            nm = f"Tree{w}{'R' if sx > 0 else 'L'}"
            H.bone(nm, "Body", T(c))
            parts = []
            turns, Ht, R0 = 4.5, 1.25, 0.36
            for i in range(70):
                f = i / 69
                th = turns * TAU * f * sx
                rr = R0 * (1 - f) + 0.03
                p = c + V(rr * math.cos(th), Ht * f + 0.05, rr * math.sin(th))
                parts.append(ellipsoid(0.07 + 0.07 * (1 - f), 0.045, 0.07 + 0.07 * (1 - f), T(p)))
            tree = union_all(parts, 0.025).su(capsule(T(c), T(c + V(0, Ht * 0.9, 0)), 0.05), 0.03)
            H.piece(nm + "P", nm, tree, col=col, mat="plastic", tris=900, res=160, role="detail", pri=1.2,
                    pattern=lambda P: 1 - 0.3 * np.clip(np.sin(P[:, 1] * 30) - 0.4, 0, 1))
            crowns.append((nm, (sx * 1.0, 0.01), 0.5))
            retract.append((nm, 1.0))
        on = f"Operc{w}"
        oc = t + V(0, base_y + 0.05, 0.28)
        H.bone(on, "Body", T(oc))
        op = ellipsoid(0.17, 0.05, 0.17, T(oc)).su(union_all([round_cone(T(oc), T(oc + V(math.cos(a) * 0.12, 0.28, math.sin(a) * 0.12)), 0.035, 0.008) for a in (0.0, 2.1, 4.2)]), 0.02)
        H.piece(on + "P", on, op, col="dark", mat="hard", tris=250, role="detail", pri=1.6)
        retract.append((on, 0.2))

    def extra(pose, kind, u, k):
        if kind in ("move", "idle"):
            for w in range(2):
                for sd in ("R", "L"):
                    MS._add(pose, f"Tree{w}{sd}", (0, 0, 0, 0, (0.35 if sd == "R" else -0.35) * math.sin(TAU * u + w), 0))
    MS.sessile(H, stalks=[], crowns=crowns, retract=retract, height=2.6, period=1.6, attack="retract", extra=extra)
    H.socket("mouth", (0, 2.2, 0), "Body")
    H.socket("head", (0, 2.8, 0), "Body")
    H.rig.update({"head": "Body"})
    return H


# ================================================================================================ isopod / pill bug
def _tergite(y0, w, h, za, zb, tilt=0.07, flare=0.0, tips=0.0):
    """A solid armour slice between za (front) and zb (back): elliptic arch cross-section of half width w and height h
    on the base plane y0, swelling slightly toward its back edge so it rides over the next slice (no coplanar faces).
    flare: the lateral edges (epimera) bend down; tips: the side corners pull back into points."""
    L = zb - za

    def f(P):
        t = np.clip((P[:, 2] - za) / L, 0, 1)
        k = 1 + tilt * t
        x = P[:, 0] / (w * k * (1 + tips * t * 0.15))
        yy = (P[:, 1] - y0 + flare * x * x * 0.0) / (h * k)
        r = np.hypot(x, yy) - 1
        d = r * min(w, h)
        d = np.maximum(d, y0 - 0.02 - P[:, 1] - flare * np.abs(P[:, 0]))
        zc = (za + zb) / 2
        back = zb + tips * np.clip(np.abs(P[:, 0]) / w - 0.6, 0, 1) * L * 0.8
        d = np.maximum(d, np.maximum(za - P[:, 2], P[:, 2] - back))
        return d
    return S.SDF(f).round(0.025)


def _isopod(hid, prev, kind="isopod"):
    pill = kind == "pill"
    H = Hero(hid, plan="Crab", gait="scuttle", tags=["crustacean", "bug", "armour", "aquatic" if not pill else "bug"])
    H.preview = prev
    if pill:
        y0, Lz, W, Hh, nseg = 0.3, 2.3, 0.72, 0.68, 7
    else:
        y0, Lz, W, Hh, nseg = 0.34, 3.4, 0.95, 0.6, 7
    bounds(H, (-2.2, -0.4, -Lz * 0.5 - 1.8), (2.2, 2.6, Lz * 0.5 + 1.2))
    head_len = Lz * 0.13
    tail_len = Lz * (0.1 if pill else 0.2)
    per_len = (Lz - head_len - tail_len) / nseg
    z_head = -Lz / 2
    zs = [z_head + head_len + i * per_len for i in range(nseg + 1)]
    wf = lambda z: W * (1 - 0.55 * max(0.0, abs(z / (Lz * 0.5)) - 0.35) ** 1.6 / 0.65 ** 1.6) if not pill else W * math.sqrt(max(0.15, 1 - (z / (Lz * 0.56)) ** 2))
    hf = lambda z: Hh * (0.75 + 0.25 * math.sqrt(max(0.0, 1 - (z / (Lz * 0.5)) ** 2))) if not pill else Hh * math.sqrt(max(0.25, 1 - (z / (Lz * 0.58)) ** 2))
    mid = nseg // 2
    pv = lambda i: (0, y0 + hf(zs[i]) * 0.97, zs[i])
    H.body(pv(mid))
    # front chain: pereonites mid-1 .. 0 then Head; back chain: mid+1 .. nseg-1 then Tail
    segb = {mid: "Body"}
    front, back = [], []
    par = "Body"
    for i in range(mid - 1, -1, -1):
        nm = f"Seg{i}"
        H.bone(nm, par, pv(i + 1))
        segb[i] = nm
        front.append(nm)
        par = nm
    H.bone("Head", par, (0, y0 + hf(zs[0]) * 0.97, zs[0]))
    front.append("Head")
    par = "Body"
    for i in range(mid + 1, nseg):
        nm = f"Seg{i}"
        H.bone(nm, par, pv(i))
        segb[i] = nm
        back.append(nm)
        par = nm
    H.bone("Tail", par, (0, y0 + hf(zs[nseg]) * 0.97, zs[nseg]))
    back.append("Tail")
    plate_pat = lambda P: 1 - 0.35 * np.clip(np.abs(P[:, 0]) / W - 0.75, 0, 1) * 3 - 0.0
    for i in range(nseg):
        za, zb = zs[i], zs[i + 1] + per_len * 0.25
        zm = (zs[i] + zs[i + 1]) / 2
        tg = _tergite(y0, wf(zm), hf(zm), za, zb, tilt=0.045, tips=0.0 if pill else 0.6)
        H.piece(f"Tergite{i}", segb[i], tg, col="primary", mat="hard", tris=420, res=128, role="shell", pri=1.1,
                pattern=combine(plate_pat, spots(0.2, 0.05, depth=0.25 if pill else 0.12, seed=i), gradient(2, za, zb, 1.0, 0.82)))
    # head shield + eyes + antennae
    hz0, hz1 = z_head, zs[0] + per_len * 0.25
    hw, hh = wf(zs[0]) * 0.85, hf(zs[0]) * 0.85
    hd = _tergite(y0, hw, hh, hz0 + 0.12, hz1, tilt=0.12)
    hd = hd.su(ellipsoid(hw * 0.75, hh * 0.65, head_len * 0.75, (0, y0 + hh * 0.2, hz0 + 0.18)), 0.08)
    H.piece("HeadP", "Head", hd, col="primary", mat="hard", tris=700, res=128, role="head", pri=1.0, pattern=gradient(2, hz0, hz1, 0.85, 1.0))
    er = 0.12 if pill else 0.2
    ep = V(hw * 0.78, y0 + hh * 0.42, hz0 + head_len * 0.55)
    H.mprim("Eye#", "Head", "Ball", (er * 1.2, er * 1.6, er * 2.0) if not pill else (er * 2,) * 3, T(ep), col="bugEye" if not pill else "black", mat="glass", role="eye", pri=1.3)
    H.mprim("Shine#", "Head", "Ball", (er * 0.55,) * 3, T(ep + V(er * 0.35, er * 0.45, -er * 0.4)), col="shine", mat="hard", role="shine", pri=2.4)
    ants = []
    ab = V(hw * 0.4, y0 + hh * 0.15, hz0 + 0.08)
    H.mbone("Antenna#", "Head", T(ab))
    if pill:
        pts = [ab, ab + V(0.22, 0.12, -0.25), ab + V(0.42, 0.0, -0.42), ab + V(0.55, -0.15, -0.55)]
        rr = [0.05, 0.04, 0.035, 0.03]
    else:
        pts = [ab, ab + V(0.3, 0.1, -0.35), ab + V(0.8, 0.05, -0.75), ab + V(1.25, -0.05, -0.85), ab + V(1.6, -0.2, -0.7)]
        rr = [0.07, 0.055, 0.045, 0.035, 0.022]
    an = tube([T(p) for p in pts], rr, k=0.02).su(union_all([sphere(rr[min(j, len(rr) - 1)] * 1.25, T(pts[j])) for j in range(1, len(pts))]), 0.01)
    if not pill:
        an = an.su(tube([T(ab + V(-0.12, 0.05, 0)), T(ab + V(0.0, 0.15, -0.3)), T(ab + V(0.1, 0.2, -0.45))], [0.04, 0.03, 0.02], k=0.02), 0.02)
    H.mpiece("AntennaP#", "Antenna#", an, col="secondary" if not pill else "dark", mat="hard", tris=300, res=150, role="detail", pri=1.4)
    ants = [("AntennaR", 1), ("AntennaL", -1)]
    # tail: pleon + pleotelson shield (+ uropods)
    tz0 = zs[nseg]
    if pill:
        tl = _tergite(y0, wf(tz0) * 0.85, hf(tz0) * 0.8, tz0, Lz / 2, tilt=0.0)
    else:
        tl = _tergite(y0, wf(tz0) * 0.95, hf(tz0) * 0.85, tz0, tz0 + tail_len * 0.35, tilt=0.05)
        tl = tl.su(_tergite(y0, wf(tz0) * 0.85, hf(tz0) * 0.7, tz0 + tail_len * 0.3, Lz / 2, tilt=-0.1).su(
            capsule((0, y0 + hf(tz0) * 0.6, tz0 + 0.1), (0, y0 + 0.15, Lz / 2 - 0.05), 0.08), 0.05), 0.04)
        for sx in (1, -1):
            u0 = V(sx * wf(tz0) * 0.55, y0 + 0.02, tz0 + tail_len * 0.4)
            tl = tl.su(plate(T(u0), (sx * 0.4, -0.05, 1), (sx * 1, 0, -0.35), [(0, -0.12), (0.55, -0.16), (0.7, 0.0), (0.55, 0.14), (0, 0.1)], 0.07), 0.03)
    H.piece("TailP", "Tail", tl, col="primary", mat="hard", tris=600, res=128, role="tail", pri=1.2, pattern=gradient(2, tz0, Lz / 2, 1.0, 0.8))
    # belly fill (keeps the underside closed when viewed low; rides the middle segment)
    if not pill:
        H.piece("Belly", "Body", ellipsoid(W * 0.6, 0.12, Lz * 0.32, (0, y0 + 0.03, zs[mid])), col="belly", mat="plastic", tris=300, role="body", pri=1.7)
    # legs: one pair per pereonite, own bones
    legs = []
    for i in range(nseg):
        zm = (zs[i] + zs[i + 1]) / 2
        w = wf(zm)
        hip = V(w * 0.62, y0 + 0.02, zm)
        nm = f"Leg{i}#"
        H.mbone(nm, segb[i], T(hip))
        fwd = -0.25 + 0.5 * i / (nseg - 1)
        knee = hip + V(w * 0.38 + 0.12, 0.12 if not pill else 0.06, fwd * 0.3)
        foot = V(w + (0.35 if not pill else 0.12), 0.02, zm + fwd * 0.6)
        lg = tube([T(hip), T(knee), T(foot)], [0.07 if not pill else 0.05, 0.055 if not pill else 0.042, 0.025], k=0.02).su(sphere(0.07 if not pill else 0.05, T(knee)), 0.02)
        H.mpiece(f"LegP{i}#", nm, lg, col="secondary" if not pill else "dark", mat="hard", tris=200, res=150, role="limb", pri=1.5)
        legs += [(nm.replace("#", "R"), 1, i), (nm.replace("#", "L"), -1, i)]
    MS.armour(H, front=front, back=back, legs=legs, ants=ants, height=Hh + y0, period=0.7 if pill else 0.9, curl=TAU * (0.92 if pill else 0.45),
              roll=pill, stride=0.32, lift=0.25)
    H.socket("mouth", (0, y0, z_head - 0.15), "Head")
    H.socket("head", (0, y0 + Hh + 0.4, 0), "Body")
    H.rig.update({"head": "Head", "tail": back})
    return H


@hero("isopod", FAM)
def isopod():
    return _isopod("isopod", {"primary": "#B8B0A0", "secondary": "#E8E0D0", "bugEye": "#2A2A30", "belly": "#E8E0D0"}, "isopod")


@hero("pill bug", FAM)
def pill_bug():
    return _isopod("pill bug", {"primary": "#6A6E74", "secondary": "#9AA0A6", "dark": "#2E3034", "belly": "#9AA0A6"}, "pill")


# ================================================================================================ trilobite
@hero("trilobite", FAM)
def trilobite():
    """Three lobes end to end and side to side: a half-moon head shield with a raised glabella, crescent compound eyes
    and long genal spines, nine pointed thorax segments with a raised axial lobe, a tail shield; little legs and
    antennae under the rim. Scuttles on a leg wave and enrolls when hit."""
    H = Hero("trilobite", plan="Crab", gait="scuttle", tags=["arthropod", "fossil", "armour", "aquatic"])
    H.preview = {"primary": "#6A5A4A", "secondary": "#B8A890", "dark": "#2A221A"}
    y0, W, Hh = 0.3, 1.05, 0.38
    bounds(H, (-2.2, -0.4, -2.6), (2.2, 2.0, 3.4))
    nseg = 9
    zh0, zh1 = -1.75, -0.75
    seg = 0.2
    zs = [zh1 + i * seg for i in range(nseg + 1)]
    zp1 = zs[-1] + 0.85
    wf = lambda z: W * (1 - 0.35 * max(0.0, (z - zh1) / (zp1 - zh1)))

    def lobed(za, zb, w, tips=0.6):
        L = zb - za

        def f(P):
            x = P[:, 0]
            ax = np.exp(-(x / (w * 0.26)) ** 2)
            ytop = y0 + Hh * (0.45 * np.sqrt(np.clip(1 - (x / w) ** 2, 0, 1)) + 0.55 * ax) - 0.08 * (np.abs(x) > w * 0.3) * 0
            groove = 0.05 * np.exp(-((np.abs(x) - w * 0.3) / (w * 0.05)) ** 2)
            d = (P[:, 1] - ytop + groove) * 0.7
            d = np.maximum(d, y0 - 0.02 - P[:, 1])
            t = np.clip(np.abs(x) / w, 0, 1.3)
            back = zb + tips * np.clip(t - 0.6, 0, 1) * L * 1.6
            d = np.maximum(d, np.maximum(za - P[:, 2] - (t > 0.7) * (t - 0.7) * 0.0, P[:, 2] - back))
            d = np.maximum(d, np.abs(x) - w * (1 - 0.15 * np.clip((P[:, 2] - zb) / max(L, 1e-3), 0, 1)))
            return d
        return S.SDF(f).round(0.02)
    mid = 4
    pv = lambda i: (0, y0 + Hh * 0.9, zs[i])
    H.body(pv(mid))
    segb = {mid: "Body"}
    front, back = [], []
    par = "Body"
    for i in range(mid - 1, -1, -1):
        nm = f"Seg{i}"
        H.bone(nm, par, pv(i + 1))
        segb[i] = nm
        front.append(nm)
        par = nm
    H.bone("Head", par, (0, y0 + Hh * 0.9, zs[0]))
    front.append("Head")
    par = "Body"
    for i in range(mid + 1, nseg):
        nm = f"Seg{i}"
        H.bone(nm, par, pv(i))
        segb[i] = nm
        back.append(nm)
        par = nm
    H.bone("Tail", par, (0, y0 + Hh * 0.9, zs[nseg]))
    back.append("Tail")
    for i in range(nseg):
        za, zb = zs[i], zs[i + 1] + 0.05
        sd = lobed(za, zb, wf(za) * (1 + 0.04 * (i % 2)))
        H.piece(f"SegP{i}", segb[i], sd, col="primary", mat="hard", tris=380, res=136, role="shell", pri=1.1 + 0.01 * i,
                pattern=combine(lambda P: 1 - 0.3 * np.exp(-((np.abs(P[:, 0]) - 0.3) / 0.05) ** 2), gradient(2, za, zb, 1.0, 0.75)))
    # cephalon: half-moon with glabella, eye ridges, genal spines
    def ceph(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        zc = zh1
        r = np.hypot(x / (W * 1.05), np.minimum(z - zc, 0) / (zc - zh0))
        dome = y0 + Hh * 0.75 * np.sqrt(np.clip(1 - r * r, 0, 1))
        d = np.maximum((y - dome) * 0.7, (r - 1) * 0.6)
        d = np.maximum(d, z - (zc + 0.08))
        d = np.maximum(d, y0 - 0.02 - y)
        return d
    cs = S.SDF(ceph).round(0.02)
    cs = cs.su(ellipsoid(0.32, 0.3, 0.55, (0, y0 + 0.3, zh1 - 0.35)), 0.1)                         # glabella
    for sx in (1, -1):
        cs = cs.su(round_cone((sx * W * 0.95, y0 + 0.04, zh1 - 0.05), (sx * W * 1.0, y0 + 0.02, zh1 + 1.3), 0.09, 0.02), 0.08)   # genal spines
        cs = cs.su(ellipsoid(0.17, 0.16, 0.24, (sx * 0.55, y0 + 0.36, zh1 - 0.3)), 0.06)             # eye mounds
    H.piece("Cephalon", "Head", cs, col="primary", mat="hard", tris=1000, res=136, role="head", pri=1.0,
            pattern=lambda P: 1 - 0.2 * np.clip(np.hypot(P[:, 0] / 1.05, (P[:, 2] - zh1) / 1.0) - 0.75, 0, 1) * 3)
    H.mprim("Eye#", "Head", "Ball", (0.18, 0.2, 0.32), (0.6, y0 + 0.42, zh1 - 0.3), rot=(0, -0.3, 0), col="dark", mat="glass", role="eye", pri=1.3)
    H.mprim("Shine#", "Head", "Ball", (0.06, 0.06, 0.06), (0.66, y0 + 0.53, zh1 - 0.38), col="shine", mat="hard", role="shine", pri=2.4)
    # pygidium
    pz0 = zs[nseg]

    def pyg(P):
        x, y, z = P[:, 0], P[:, 1], P[:, 2]
        w = wf(pz0)
        r = np.hypot(x / w, np.maximum(z - pz0, 0) / (zp1 - pz0))
        ax = np.exp(-(x / (w * 0.26)) ** 2) * np.clip(1 - (z - pz0) / (zp1 - pz0) * 0.8, 0, 1)
        top = y0 + Hh * (0.35 * np.sqrt(np.clip(1 - r * r, 0, 1)) + 0.5 * ax)
        d = np.maximum((y - top) * 0.7, (r - 1) * 0.5)
        d = np.maximum(d, pz0 - 0.02 - z)
        return np.maximum(d, y0 - 0.02 - y)
    H.piece("Pygidium", "Tail", S.SDF(pyg).round(0.02), col="primary", mat="hard", tris=600, res=136, role="tail", pri=1.1,
            pattern=lambda P: 1 - 0.25 * np.clip(np.sin((P[:, 2] - pz0) * 30) - 0.3, 0, 1))
    # antennae and legs peeking out under the rim
    ab = V(0.25, y0 + 0.02, zh0 + 0.2)
    H.mbone("Antenna#", "Head", T(ab))
    H.mpiece("AntennaP#", "Antenna#", tube([T(ab), T(ab + V(0.2, 0.02, -0.45)), T(ab + V(0.5, 0.0, -0.95))], [0.04, 0.03, 0.015], k=0.02),
             col="dark", mat="hard", tris=200, res=150, role="detail", pri=1.4)
    legs = []
    for k, i in enumerate((0, 2, 4, 6, 8)):
        nm = f"Leg{k}#"
        zm = (zs[i] + zs[i + 1]) / 2
        hip = V(wf(zm) * 0.55, y0 + 0.02, zm)
        H.mbone(nm, segb[i], T(hip))
        lg = tube([T(hip), T(hip + V(wf(zm) * 0.45 + 0.12, 0.05, -0.05)), T(V(wf(zm) + 0.28, 0.02, zm + 0.08))], [0.05, 0.04, 0.02], k=0.02)
        H.mpiece(f"LegP{k}#", nm, lg, col="secondary", mat="hard", tris=180, res=150, role="limb", pri=1.6)
        legs += [(nm.replace("#", "R"), 1, k), (nm.replace("#", "L"), -1, k)]
    MS.armour(H, front=front, back=back, legs=legs, ants=[("AntennaR", 1), ("AntennaL", -1)], height=0.8, period=0.8, curl=TAU * 0.75, stride=0.3, lift=0.2)
    H.socket("mouth", (0, y0, zh0 - 0.1), "Head")
    H.socket("head", (0, y0 + 0.9, 0), "Body")
    H.rig.update({"head": "Head", "tail": back})
    return H


# ================================================================================================ opabinia
@hero("opabinia", FAM)
def opabinia():
    """The weird Cambrian swimmer: five mushroom eyes on the head, a long flexible nozzle ending in a spiny grabbing
    claw, a segmented trunk with overlapping swimming flaps along both sides and a tail fan of upturned blades."""
    H = Hero("opabinia", plan="Crab", gait="swim", tags=["arthropod", "fossil", "aquatic", "weird"])
    H.preview = {"primary": "#8A6A4A", "secondary": "#E8A08A", "dark": "#3A2A1E"}
    y = 1.4
    H.body((0, y, -0.9))
    bounds(H, (-2.2, -0.3, -4.0), (2.2, 3.2, 3.4))
    # head
    hd = ellipsoid(0.42, 0.36, 0.5, (0, y, -1.3)).su(ellipsoid(0.36, 0.3, 0.4, (0, y - 0.05, -0.85)), 0.15)
    H.piece("HeadP", "Body", hd, col="primary", mat="skin", tris=800, role="head", pri=1.0)
    eyes = [(0.0, 0.42, -1.52, 0.11), (0.22, 0.4, -1.35, 0.12), (-0.22, 0.4, -1.35, 0.12), (0.28, 0.36, -1.05, 0.1), (-0.28, 0.36, -1.05, 0.1)]
    st = []
    for (ex, ey, ez, er) in eyes:
        b0 = V(ex * 0.6, y + 0.25, ez)
        tip = V(ex, y + ey, ez - 0.02)
        st.append(round_cone(T(b0), T(tip), 0.05, 0.045))
    H.piece("EyeStalks", "Body", union_all(st), col="primary", mat="skin", tris=300, res=150, role="detail", pri=1.4)
    for k, (ex, ey, ez, er) in enumerate(eyes):
        H.prim(f"Eye{k}", "Body", "Ball", (er * 2, er * 1.7, er * 2), (ex, y + ey + er * 0.6, ez - 0.02), col="black", mat="glass", role="eye", pri=1.3)
        H.prim(f"Shine{k}", "Body", "Ball", (er * 0.6,) * 3, (ex + er * 0.3, y + ey + er * 1.0, ez - er * 0.6), col="shine", mat="hard", role="shine", pri=2.4)
    # proboscis
    pn = ["Nozzle1", "Nozzle2", "Nozzle3"]
    pts = [V(0, y - 0.25, -1.65), V(0, y - 0.55, -2.2), V(0, y - 0.6, -2.75), V(0, y - 0.35, -3.15)]
    chain(H, pn, "Body", pts, [0.11, 0.09, 0.08, 0.075], col="secondary", tris=300, res=140, role="limb",
          pattern=lambda P: 1 - 0.3 * np.clip(np.sin(P[:, 2] * 40) - 0.3, 0, 1))
    H.bone("Claw", pn[2], T(pts[3]))
    cl = []
    for sy in (1, -1):
        a = pts[3]
        cl.append(tube([T(a), T(a + V(0, sy * 0.13, -0.15)), T(a + V(0, sy * 0.05, -0.33))], [0.07, 0.05, 0.015], k=0.02))
        for j in range(3):
            c = a + V(0, sy * (0.11 - 0.025 * j), -0.1 - 0.07 * j)
            cl.append(round_cone(T(c), T(c + V(0, -sy * 0.08, -0.02)), 0.022, 0.006))
    H.piece("ClawP", "Claw", union_all(cl), col="dark", mat="hard", tris=300, res=160, role="claw", pri=1.3)
    # trunk: four sections chained backwards
    tn = ["Trunk1", "Trunk2", "Trunk3", "Trunk4"]
    tz = [-0.7, 0.05, 0.8, 1.55, 2.2]
    par = "Body"
    for i, nm in enumerate(tn):
        H.bone(nm, par, (0, y, tz[i]))
        par = nm
        r0, r1 = 0.36 - 0.05 * i, 0.36 - 0.05 * (i + 1)
        sd = round_cone((0, y, tz[i]), (0, y, tz[i + 1]), r0, r1 * (1.07 if i < 3 else 1)) | sphere(r0, (0, y, tz[i]))
        sd = sd.scale3(1.15, 0.8, 1).at(0, y * 0.2, 0)
        H.piece(f"TrunkP{i}", nm, sd, col="primary", mat="skin", tris=500, res=124, role="body", pri=1.1,
                pattern=lambda P: 1 - 0.3 * np.clip(np.sin(P[:, 2] * 4.2 * TAU / 1.0) - 0.4, 0, 1))
    # flaps: 5 per side, overlapping, on their own bones
    flaps = []
    for k in range(5):
        z = -0.55 + k * 0.6
        tb = tn[min(3, int((z + 0.7) / 0.75))]
        nm = f"Flap{k}#"
        rr = 0.36 - 0.05 * min(3, int((z + 0.7) / 0.75))
        H.mbone(nm, tb, (rr * 1.05, y - 0.02, z))
        fl = plate((rr * 1.0, y - 0.02, z), (1, -0.08, 0.35), (0, 0, 1), [(0, -0.28), (0.45, -0.22), (0.62, 0.08), (0.5, 0.42), (0, 0.3)], 0.06, bend=0.15)
        H.mpiece(f"FlapP{k}#", nm, fl, col="secondary", mat="skin", tris=220, res=150, role="fin", pri=1.4, tr=0.1,
                 pattern=lambda P: 1 - 0.25 * np.clip(np.sin(P[:, 0] * 30) - 0.4, 0, 1))
        flaps += [(nm.replace("#", "R"), 1, k), (nm.replace("#", "L"), -1, k)]
    # tail fan: three pairs of upturned blades
    bl = []
    for k in range(3):
        for sx in (1, -1):
            o = V(sx * 0.1, y + 0.05, 2.1 + k * 0.12)
            bl.append(plate(T(o), (sx * 0.6, 0.55 + 0.1 * k, 0.6), (0, 0, 1), [(0, -0.08), (0.7 - 0.1 * k, -0.1), (0.8 - 0.1 * k, 0.05), (0, 0.08)], 0.05))
    H.piece("TailFan", tn[3], union_all(bl, 0.02), col="secondary", mat="skin", tris=500, res=150, role="fin", pri=1.3)

    def extra(pose, kind, u, k):
        if kind in ("move", "idle"):
            for i, b in enumerate(pn):
                MS._add(pose, b, (0, 0, 0, 0.12 * math.sin(TAU * u * (2 if kind == "move" else 1) - i * 0.8), 0.15 * math.sin(TAU * u - i * 0.6), 0))
            MS._add(pose, "Claw", (0, 0, 0, 0.3 * max(0.0, math.sin(TAU * u * 2)), 0, 0))
            MS._add(pose, "Body", (0, 0.15 * math.sin(TAU * u), 0, 0, 0, 0))
        elif kind == "attack":
            for i, b in enumerate(pn):
                MS._add(pose, b, (0, 0, 0, -0.35 * k, 0, 0))
            MS._add(pose, "Claw", (0, 0, 0, 0.6 * k, 0, 0))
    MS.armour(H, front=[], back=tn, legs=[], ants=[], flaps=flaps, height=1.6, period=1.1, curl=0.0, extra=extra)
    H.socket("mouth", T(pts[3] + V(0, 0, -0.3)), "Claw")
    H.socket("head", (0, y + 1.0, -1.2), "Body")
    H.rig.update({"head": "Body", "tail": tn})
    return H


# ================================================================================================ tadpole
@hero("tadpole", FAM)
def tadpole():
    """A round speckled body with bulging eyes on top and a little beaked mouth, a coiled gut showing through the pale
    belly, tiny hind-leg buds and a long finned tail that wiggles in fast S-waves."""
    H = Hero("tadpole", plan="Fish", gait="swim", tags=["amphibian", "aquatic", "frog", "baby"])
    H.preview = {"primary": "#3A3A2A", "secondary": "#6A6A4A", "belly": "#B8B49A"}
    y = 1.0
    H.body((0, y, 0))
    bounds(H, (-1.8, -0.3, -1.8), (1.8, 2.4, 4.2))
    bd = ellipsoid(0.82, 0.72, 0.95, (0, y, -0.1)).su(ellipsoid(0.55, 0.5, 0.6, (0, y + 0.02, 0.6)), 0.3)
    bd = bd.su(ellipsoid(0.62, 0.4, 0.5, (0, y - 0.05, -0.65)), 0.25)                            # snout
    belly = lambda P: 1 - 0.0 * P[:, 0]
    speck = spots(0.16, 0.045, depth=0.45, seed=7, region=lambda P: np.clip((P[:, 1] - y + 0.1) * 4, 0, 1))
    H.piece("BodyP", "Body", bd, col="primary", mat="skin", tris=1300, res=128, role="body", pattern=speck)
    H.piece("Belly", "Body", overlay(bd, S.SDF(lambda P: P[:, 1] - (y - 0.35)), t=0.02), col="belly", mat="glass", tris=600, res=128, role="detail", pri=1.4,
            pattern=lambda P: 1 - 0.45 * np.clip(np.sin(np.hypot(P[:, 0], P[:, 2] + 0.05) * 30 + np.arctan2(P[:, 0], P[:, 2] + 0.05)) - 0.3, 0, 1))
    H.eyes("Body", (0.45, y + 0.42, -0.45), 0.16, col="iris", pupil="round", look=(0.6, 0.35, -0.75))
    H.prim("Mouth", "Body", "Ball", (0.22, 0.1, 0.12), (0, y - 0.15, -1.12), col="mouth", mat="hard", role="mouth", pri=2.0)
    H.mprim("Nostril#", "Body", "Ball", (0.04,) * 3, (0.12, y + 0.08, -1.12), col="pupil", mat="hard", role="detail", pri=2.4)
    H.mbone("Bud#", "Body", (0.4, y - 0.35, 0.75))
    H.mpiece("BudP#", "Bud#", tube([(0.38, y - 0.35, 0.72), (0.55, y - 0.48, 0.85), (0.58, y - 0.55, 1.05)], [0.08, 0.06, 0.05], k=0.02).su(
        sphere(0.07, (0.6, y - 0.56, 1.08)), 0.02), col="secondary", mat="skin", tris=200, role="limb", pri=1.6)
    names = ["Tail1", "Tail2", "Tail3"]
    pts = [V(0, y + 0.02, 0.8), V(0, y + 0.03, 1.55), V(0, y + 0.03, 2.35), V(0, y + 0.02, 3.3)]
    fin_h = [0.55, 0.5, 0.38, 0.05]

    def deco(i, sh, a, b):
        fa, fb = fin_h[i], fin_h[i + 1]
        fin = plate(T(a), (0, 0, 1), (0, 1, 0), [(0.0, -fa * 0.75), (np.linalg.norm(b - a) + 0.02, -fb * 0.8), (np.linalg.norm(b - a) + 0.02, fb), (0.0, fa)], 0.05, taper=0.4)
        return sh.su(fin, 0.06)
    chain(H, names, "Body", pts, [0.32, 0.22, 0.13, 0.04], col="secondary", tris=[600, 550, 450], res=130, deco=deco, tr=0.1,
          pattern=combine(spots(0.14, 0.035, depth=0.4, seed=3), lambda P: 1 - 0.3 * np.clip(np.abs(P[:, 1] - y) - 0.25, 0, 1) * 3))
    MA.swim(H, names, head=None, pecs=[("BudR", "BudL")], mode="yaw", period=0.6, amp=0.55, wave=1.2, length=3.0, attack="bite", body_amp=0.08, idle_period=2.4)
    H.socket("mouth", (0, y - 0.15, -1.2), "Body")
    H.socket("head", (0, y + 0.9, -0.2), "Body")
    H.rig.update({"head": "Body", "tail": names})
    return H


CRE = {"cat": ["Creature", "Machine", "Abstract", "Element"]}
MAP = [
    ("clam", "clam, clams, cockle, cockles, quahog, razor clam, surf clam, venus clam, bivalve, !clam chowder, !steamed clams", CRE),
    ("giant clam", "giant clam, giant clams, giantclam, tridacna, killer clam", CRE),
    ("oyster", "oyster, oysters, pearl oyster, rock oyster, pearl clam, !oyster sauce, !oyster platter, !oystercatcher", CRE),
    ("scallop", "scallop, scallops, bay scallop, flame scallop, fan shell", CRE),
    ("mussel", "mussel, mussels, blue mussel, zebra mussel, green lipped mussel, !steamed mussels", CRE),
    ("geoduck", "geoduck, geoducks, gooey duck", CRE),
    ("shipworm", "shipworm, shipworms, teredo, teredo worm, wood borer", CRE),
    ("conch", "conch, conchs, conches, queen conch, strombus, spider conch, triton shell, helmet shell", CRE),
    ("whelk", "whelk, whelks, murex, triton snail, auger shell, tulip snail, moon snail, turban snail", CRE),
    ("cowrie", "cowrie, cowries, cowry, tiger cowrie, egg cowrie, olive shell", CRE),
    ("limpet", "limpet, limpets, keyhole limpet, slipper limpet", CRE),
    ("abalone", "abalone, abalones, paua, ormer", CRE),
    ("chiton", "chiton, chitons, gumboot chiton, coat of mail shell", CRE),
    ("sea cucumber", "sea cucumber, sea cucumbers, seacucumber, holothurian, sea slug cucumber", CRE),
    ("sea pig", "sea pig, sea pigs, seapig, scotoplanes", CRE),
    ("sea mouse", "sea mouse, sea mice, seamouse, aphrodita", CRE),
    ("blobfish", "blobfish, blob fish, blobfishes, psychrolutes", CRE),
    ("salp", "salp, salps, salp chain", CRE),
    ("siphonophore", "siphonophore, siphonophores, praya, colonial jelly", CRE),
    ("pyrosome", "pyrosome, pyrosomes, sea pickle, fire body", CRE),
    ("sea squirt", "sea squirt, sea squirts, seasquirt, tunicate, tunicates, ascidian", CRE),
    ("hydra polyp", "hydra polyp, hydra polyps, hydrapolyp, freshwater hydra, polyp, polyps, hydroid", CRE),
    ("giant tube worm", "giant tube worm, giant tube worms, gianttubeworm, tube worm, tube worms, riftia, vent worm", CRE),
    ("feather duster worm", "feather duster worm, feather duster worms, featherdusterworm, fan worm, fanworm, featherduster worm", CRE),
    ("christmas tree worm", "christmas tree worm, christmas tree worms, christmastreeworm, spiral worm", CRE),
    ("isopod", "isopod, isopods, giant isopod, sea louse, sea slater, bathynomus", CRE),
    ("pill bug", "pill bug, pill bugs, pillbug, roly poly, roly polies, rolly polly, woodlouse, woodlice, potato bug, sow bug", CRE),
    ("trilobite", "trilobite, trilobites", CRE),
    ("opabinia", "opabinia, opabinias", CRE),
    ("tadpole", "tadpole, tadpoles, polliwog, pollywog, froglet", CRE),
]
