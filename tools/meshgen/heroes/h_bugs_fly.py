"""Bugs (flying): bee, bumblebee, wasp, hornet; butterfly, monarch butterfly, moth, luna moth; fly, mosquito,
dragonfly, cicada. All use gait "buzz": fast wing flutter (slow flapping for butterflies and moths), legs tucked in
flight, stinging / diving attacks. Wing patterns are pattern masks evaluated in each wing's own flat frame."""
import math

import numpy as np

import sdf as S
from sdf import sphere, ellipsoid, capsule, round_cone, tube, torus  # noqa: F401
from kit import Hero, hero, stripes, spots, gradient, combine  # noqa: F401
import motion_bugs as MB
from bugkit import *  # noqa: F401,F403


def _wing_local(root, yaw, lift, roll):
    """Model point -> the wing's flat frame (x along the span, z chord, y normal) for patterns."""
    R = S._rotm(0, yaw, 0) @ S._rotm(0, 0, lift) @ S._rotm(roll, 0, 0)
    root = A(root)

    def f(P):
        return (P - root) @ R

    return f


def seg2(a, b, r):
    """2D capsule in the XZ plane (infinite along Y): distance to the segment a-b minus r."""
    a, b = np.array(a, float), np.array(b, float)
    ba = b - a
    L = ba @ ba

    def f(p):
        q = p[:, [0, 2]] - a
        h = np.clip((q @ ba) / L, 0, 1)
        return np.linalg.norm(q - h[:, None] * ba, axis=1) - r

    return S.SDF(f)


def circ2(c, r):
    return S.SDF(lambda p: np.hypot(p[:, 0] - c[0], p[:, 2] - c[1]) - r)


def wing_frame(poly, plan, border=0.12, vein_r=0.022, vein_root=(0.05, 0.02), veins=True, dots=0.0, rings=(), spots=(), extra=None):
    """Raised frame region of a wing (2D, local coords): a border band, veins from the root to the outline's
    vertices, optional eyespot rings / solid spots; dots punched out of the border. Returns a Y-prism SDF."""
    reg = None
    if border:
        reg = S.SDF(lambda p: -(plan(p) + border))
    if veins:
        for v in poly:
            if np.hypot(v[0] - vein_root[0], v[1] - vein_root[1]) < 0.3:
                continue
            sg = seg2(vein_root, (v[0] * 0.97, v[1] * 0.97), vein_r)
            reg = sg if reg is None else reg | sg
    for cx, cz, r, w in rings:
        ri = S.SDF(lambda p, cx=cx, cz=cz, r=r, w=w: np.abs(np.hypot(p[:, 0] - cx, p[:, 2] - cz) - r) - w)
        reg = ri if reg is None else reg | ri
    for cx, cz, r in spots:
        reg = circ2((cx, cz), r) if reg is None else reg | circ2((cx, cz), r)
    if extra is not None:
        reg = extra if reg is None else reg | extra
    if dots and border:
        holes = None
        # dots along the border band: sample the outline and step inward
        P = np.array(poly, float)
        n = len(P)
        for i in range(n):
            a, b = P[i], P[(i + 1) % n]
            L = np.linalg.norm(b - a)
            k = max(int(L / (dots * 3.2)), 1)
            nrm = np.array([-(b - a)[1], (b - a)[0]]) / max(L, 1e-6)
            c0 = P.mean(0)
            if nrm @ ((a + b) / 2 - c0) > 0:
                nrm = -nrm
            for j in range(k):
                c = a + (b - a) * (j + 0.5) / k + nrm * border * 0.45
                h = circ2(c, dots)
                holes = h if holes is None else holes | h
        if holes is not None:
            reg = reg - holes
    return reg


def flat_wing(H, tag, root, poly, yaw=0.0, lift=0.0, roll=0.0, t=0.024, col="primary", mat="skin", tr=0.0, pat2d=None,
              parent="Body", tris=500, pri=1.6, camber=0.02, rnd=0.06, res=170, frame=None):
    """An opaque or glassy wing from a 2D polygon planform [(x, z)] (x out along the span from the root, z back),
    corners rounded by rnd, oriented by yaw / lift / roll at root. pat2d(x, z, d) -> 0..1 multiplier where d is the
    planform's signed distance (negative inside). frame: dict(col=..., tris=..., **wing_frame kwargs): a second
    piece, the raised (0.02 proud on both faces) border / veins / eyespots in a contrasting colour."""
    root = A(root)
    H.mbone(f"{tag}#", parent, T(root))
    pl = poly2(poly)
    plan = pl.round(rnd) if rnd else pl
    sd = orient(membrane(plan, t, camber), yaw, lift, roll, T(root))
    pat = None
    if pat2d is not None:
        loc = _wing_local(root, yaw, lift, roll)

        def pat(P, loc=loc, pl=pl):
            Q = loc(P)
            d = pl(np.column_stack([Q[:, 0], np.zeros(len(Q)), Q[:, 2]])) - rnd
            return pat2d(Q[:, 0], Q[:, 2], d)

    H.mpiece(f"{tag}P#", f"{tag}#", sd, col=col, mat=mat, tr=tr, tris=tris, role="wing", pattern=pat, pri=pri, res=res, smooth=2, ao=False)
    if frame:
        fr = dict(frame)
        fcol = fr.pop("col", "secondary")
        ftris = fr.pop("tris", 900)
        fmat = fr.pop("mat", "skin")
        region = wing_frame(poly, plan, **fr)
        fsd = (region & plan).si(slab(t + 0.022), 0.01)
        if camber:
            fsd = fsd.warp(lambda p: np.column_stack([p[:, 0], p[:, 1] - camber * (p[:, 0] ** 2 + 0.3 * p[:, 2] ** 2), p[:, 2]]))
        H.mpiece(f"{tag}F#", f"{tag}#", orient(fsd, yaw, lift, roll, T(root)), col=fcol, mat=fmat, tris=ftris, role="wing", pri=pri + 0.05,
                 res=res, smooth=1, ao=False)
    return f"{tag}R", f"{tag}L"


def glass_wing(H, tag, root, poly, yaw=0.0, lift=0.0, roll=0.0, veins_n=7, tris=380, frame=True, vein_r=0.016, **kw):
    """Clear membrane wing with raised dark veins (a separate frame piece: leading edge + veins from the root)."""
    fr = dict(col="dark", border=0.0, vein_r=vein_r, tris=500, mat="hard",
              extra=seg2((0.0, poly[0][1]), (max(p[0] for p in poly) * 0.92, min(p[1] for p in poly) * 0.6), vein_r * 1.4)) if frame else None
    return flat_wing(H, tag, root, poly, yaw, lift, roll, col=kw.pop("col", "wingGlass"), mat="glass", tr=kw.pop("tr", 0.45),
                     tris=tris, frame=fr, **kw)


def _flyer_legs(H, specs, r, col="dark", hair=0.0, spines=0, tris=(240, 220, 180)):
    names = [leg(H, tg, *sp, r=r, col=col, hair=hair, spines=spines, tris=tris) for tg, sp in specs]
    return legs_rig(names, [0.0, 0.5, 0.0][: len(names)])


def _wingrig(*pairs):
    """[(R, L), phase, amp] -> flyer wing tuples."""
    out = []
    for (r, l), ph, a in pairs:
        out.append((r, 1, ph, a))
        out.append((l, -1, ph, a))
    return out


# ================================================================================================ bees & wasps
def _bee(hid, kind="honey", s=1.0, preview=None):
    H = Hero(hid, plan="Insect", gait="buzz", tags=["insect", "bug", "flying", "venomous"])
    H.preview = preview or {}
    wasp = kind in ("wasp", "hornet")
    bumble = kind == "bumble"
    fz = 0.0 if wasp else (0.035 if bumble else 0.022)
    y = 1.35
    H.body((0, y, 0))
    # ---------------------------------------------------------------- thorax
    tw = 0.56 if bumble else (0.4 if wasp else 0.46)
    th = ellipsoid(tw, tw * 0.95, tw * 1.05, (0, y + 0.03, 0))
    th = th.su(ellipsoid(tw * 0.7, 0.25, tw * 0.6, (0, y - 0.25, -0.05)), 0.12)
    if wasp:
        th = th.su(ellipsoid(0.3, 0.2, 0.18, (0, y + 0.25, 0.32)), 0.1)                      # scutellum
    th = hairy(th, fz, 42, 1)
    if bumble:
        tpat = lambda P: 1 - 0.92 * np.clip(1 - np.abs(P[:, 2] - 0.05) / 0.22, 0, 1) * np.clip((P[:, 1] - y + 0.2) * 4, 0, 1)
        tcol = "primary"
    elif wasp:
        tpat = lambda P: 1 - 0.0 * P[:, 0]
        tcol = "secondary"
    else:
        tpat = gradient(1, y - 0.4, y + 0.4, 0.75, 0.55)
        tcol = "primary"
    H.piece("Torso", "Body", th, col=tcol, mat="fur" if not wasp else "hard", tris=1500, res=124, pattern=tpat)
    # ---------------------------------------------------------------- head
    hb = (0, y - 0.02, -tw * 0.85)
    H.bone("Head", "Body", hb)
    hz = -tw - 0.25
    hd = ellipsoid(0.36, 0.36, 0.22, (0, y - 0.05, hz))
    hd = hd.su(ellipsoid(0.24, 0.24, 0.18, (0, y - 0.3, hz - 0.04)), 0.1)                     # face / clypeus
    hd = hd.su(round_cone((0, y, hz + 0.1), (0, y, -tw * 0.7), 0.14, 0.18), 0.05)           # neck
    hd = hairy(hd, fz * 0.6, 30, 2)
    H.piece("HeadP", "Head", hd, col="primary" if kind == "hornet" else ("secondary" if not wasp else "primary"), mat="hard", tris=1000, role="head",
            pattern=(lambda P: 1 - 0.85 * np.clip((P[:, 1] - y + 0.05) * 6, 0, 1)) if kind == "wasp" else None)
    H.mprim("Eye#", "Head", "Ellipsoid", (0.16, 0.44, 0.3), (0.29, y - 0.03, hz - 0.02), rot=(0, -0.35, 0), col="bugEye", mat="hard", pri=1.25, role="eye")
    H.mprim("Shine#", "Head", "Ball", (0.07, 0.07, 0.07), (0.36, y + 0.08, hz - 0.12), col="shine", mat="hard", pri=2.4, role="shine")
    for i, (dx, dy) in enumerate(((0.0, 0.25), (0.07, 0.21))):
        if i == 0:
            H.prim("Ocellus", "Head", "Ball", (0.06,) * 3, (0, y + dy, hz - 0.12), col="bugEye", mat="hard", pri=2.0, role="eye")
        else:
            H.mprim("Ocel#", "Head", "Ball", (0.05,) * 3, (dx, y + dy, hz - 0.1), col="bugEye", mat="hard", pri=2.0, role="eye")
    # mandibles
    mb = A(0.1, y - 0.42, hz - 0.08)
    H.mbone("Mand#", "Head", T(mb))
    md = tube([T(mb), T(mb + A(0.03, -0.08, -0.08)), T(mb + A(-0.08, -0.12, -0.1))], [0.05, 0.04, 0.018], k=0.02)
    H.mpiece("Mandible#", "Mand#", md, col="primary" if wasp else "dark", mat="hard", tris=200, role="jaw", pri=1.5)
    # antennae (elbowed)
    base = A(0.08, y + 0.02, hz - 0.2)
    el = base + A(0.06, 0.3, -0.12)
    antenna(H, "", T(base), [base, el, el + A(0.15, 0.08, -0.25), el + A(0.28, -0.05, -0.45)], 0.035, 0.03,
            col="secondary" if not wasp else "dark", kind="elbow")
    # ---------------------------------------------------------------- abdomen
    ab = A(0, y - 0.05, tw * 0.8)
    H.bone("Abdomen", "Body", T(ab))
    if wasp:
        big = 1.15 if kind == "hornet" else 1.0
        ga = capsule((0, y - 0.05, tw * 0.7), (0, y - 0.12, tw + 0.3), 0.08)                  # petiole
        c = A(0, y - 0.22, tw + 0.95 * big)
        ga = ga.su(ellipsoid(0.42 * big, 0.4 * big, 0.68 * big).rot(14, 0, 0).at(*T(c)), 0.08)
        ga = ga.su(round_cone(T(c), T(c + A(0, -0.25, 0.85) * big), 0.36 * big, 0.06), 0.25)
        tip = c + A(0, -0.27, 0.9) * big
        axis = lambda Q: (Q[:, 2] - c[2]) + 0.25 * (Q[:, 1] - c[1])
        apat = stripes(axis, 1 / (0.33 * big), width=0.42, depth=0.9, region=lambda Q: np.clip((Q[:, 2] - tw - 0.5) * 3, 0, 1))
        apat = combine(apat, lambda Q: 1 - 0.9 * np.clip((tw + 0.55 - Q[:, 2]) * 4, 0, 1))
    else:
        R = (0.56, 0.52, 0.72) if bumble else (0.43, 0.41, 0.74)
        c = A(0, y - 0.2, tw + R[2] * 0.85)
        ga = ellipsoid(*R).rot(16, 0, 0).at(*T(c))
        ga = ga.su(ellipsoid(0.24, 0.22, 0.2, (0, y - 0.05, tw * 0.8)), 0.12)
        ga = hairy(ga, fz * 0.7, 40, 3)
        tip = c + A(0, -0.22, R[2] * 0.95)
        axis = lambda Q: (Q[:, 2] - c[2]) + 0.3 * (Q[:, 1] - c[1])
        if bumble:
            apat = lambda Q: np.where((axis(Q) > -0.25) & (axis(Q) < 0.3), 0.08, 1.0) * np.where(axis(Q) > 0.55, 0.92, 1.0)
        else:
            apat = stripes(axis, 1 / 0.3, width=0.4, depth=0.86, region=lambda Q: np.clip((Q[:, 2] - c[2] + R[2] * 0.75) * 4, 0, 1))
    H.piece("Gaster", "Abdomen", ga, col="primary", mat="fur" if not wasp else "hard", tris=1500, res=124, pattern=apat)
    d = A(0, -0.3, 1.0)
    d = d / np.linalg.norm(d)
    H.piece("Stinger", "Abdomen", round_cone(T(tip - d * 0.08), T(tip + d * 0.32), 0.055, 0.008), col="darker", mat="hard", tris=160, role="detail", pri=1.6)
    # ---------------------------------------------------------------- legs
    hy = y - 0.3
    r = (0.07, 0.06, 0.045, 0.032)
    specs = [("F", legspec((0.13, hy, -0.25), 45, 0.38, hy - 0.05, 0.75, 0.38, 1.0, 0.035)),
             ("M", legspec((0.16, hy, 0.0), -10, 0.48, hy - 0.02, 0.92, 0.36, 1.22, 0.035)),
             ("B", legspec((0.16, hy, 0.2), -50, 0.52, hy - 0.02, 1.0, 0.36, 1.35, 0.035))]
    names = []
    for tg, sp in specs:
        tib = None
        if tg == "B" and kind == "honey":
            hip, kn, an, tp = sp
            tib = round_cone(T(kn), T(an), 0.055, 0.05).su(ellipsoid(0.11, 0.17, 0.09, T((kn + an) / 2 + A(0.02, -0.03, 0))), 0.05)  # pollen basket
        names.append(leg(H, tg, *sp, r=r, col="secondary" if not wasp else ("primary" if kind == "wasp" else "secondary"), hair=fz * 0.4,
                         tibia=tib, tris=(240, 240, 180)))
    legs = legs_rig(names, [0.0, 0.5, 0.0])
    # ---------------------------------------------------------------- wings
    fw = [(0, -0.08), (0.5, -0.2), (1.25, -0.22), (1.6, -0.08), (1.45, 0.12), (0.8, 0.22), (0.15, 0.12)]
    hw = [(0, -0.04), (0.55, -0.1), (1.0, -0.08), (1.05, 0.05), (0.6, 0.18), (0.1, 0.1)]
    big = 1.15 if bumble else 1.0
    fw = [(x * big, z * big) for x, z in fw]
    w1 = glass_wing(H, "Wing", (0.18, y + tw * 0.75, -0.12), fw, yaw=-28, lift=22, rnd=0.05, tr=0.5)
    w2 = glass_wing(H, "HWing", (0.18, y + tw * 0.72 - 0.06, 0.12), hw, yaw=-42, lift=20, rnd=0.04, tr=0.5, tris=300)
    wings = _wingrig((w1, 0.0, 1.0), (w2, 0.06, 0.9))
    MB.flyer(H, wings, legs=legs, head="Head", abd="Abdomen", ants=[("AntR", 1), ("AntL", -1)], mand=[("MandR", 1), ("MandL", -1)],
             height=1.6, flaps=8, period=0.5, amp=0.85, attack="sting")
    finish(H, mouth=(0, y - 0.45, hz - 0.2), top=(0, y + 0.4, hz), legs=legs)
    H.socket("sting", T(tip + d * 0.32), "Abdomen")
    return H


@hero("bee", "bugs")
def bee():
    return _bee("bee", "honey", preview={"primary": "#F2C02A", "secondary": "#2A1E14", "bugEye": "#17110B", "wingGlass": "#D8DCE0"})


@hero("bumblebee", "bugs")
def bumblebee():
    return _bee("bumblebee", "bumble", preview={"primary": "#F2C82A", "secondary": "#1E1E1E", "bugEye": "#111111", "wingGlass": "#C8CCD4", "dark": "#1E1E1E"})


@hero("wasp", "bugs")
def wasp():
    return _bee("wasp", "wasp", preview={"primary": "#F2D82A", "secondary": "#1E1E1E", "bugEye": "#111111", "wingGlass": "#C8C0A8", "dark": "#1E1E1E"})


@hero("hornet", "bugs")
def hornet():
    return _bee("hornet", "hornet", preview={"primary": "#B8702A", "secondary": "#1E1E1E", "bugEye": "#111111", "wingGlass": "#C8A878"})


# ================================================================================================ butterflies & moths
def _monarch(x, z, d, fore=True):
    """Monarch-like wing: dark veins, a black border with two rows of pale dots, a dark apex."""
    ang = np.arctan2(z + 0.15, x + 0.15)
    u = np.mod(ang / (math.pi / 2) * (6 if fore else 5), 1.0)
    vein = np.clip(1 - np.abs(u - 0.5) / 0.08, 0, 1) * np.clip(x * 2.5, 0, 1)
    rr = np.hypot(x + 0.15, z + 0.15)
    cross = np.clip(1 - np.abs(rr - (0.95 if fore else 0.7)) / 0.035, 0, 1)
    bord = np.clip((d + 0.2) / 0.03, 0, 1)
    dots = 0.5 + 0.5 * np.sin((x - z) * 30) * np.sin((x + z) * 30)
    dots = np.clip((dots - 0.82) * 8, 0, 1) * np.clip(1 - np.abs(d + 0.1) / 0.06, 0, 1)
    dark = np.maximum(np.maximum(vein, cross * 0.9), bord * (1 - dots))
    if fore:
        apex = np.clip((x - 1.2) * 4, 0, 1) * np.clip((-z + 0.0) * 3 + 0.6, 0, 1) * (1 - dots)
        dark = np.maximum(dark, apex)
    return 1 - 0.9 * np.clip(dark, 0, 1)


def _moth_pat(x, z, d, fore=True, eyespot=True):
    """Dusty moth wing: wavy cross bands, a dark eyespot with a pale ring, a darker margin."""
    band = np.sin(x * 7 + np.sin(z * 9) * 0.8) * 0.5 + 0.5
    band = np.clip((band - 0.75) * 4, 0, 1) * 0.45
    spot = 0.0
    if eyespot:
        c = (0.85, 0.05) if fore else (0.55, 0.45)
        rr = np.hypot(x - c[0], z - c[1])
        spot = np.clip((0.12 - rr) / 0.03, 0, 1) * 0.85 + np.clip(1 - np.abs(rr - 0.17) / 0.025, 0, 1) * 0.5
    edge = np.clip((d + 0.1) / 0.05, 0, 1) * 0.35
    root = np.clip(0.4 - np.hypot(x, z), 0, 1) * 0.8
    return 1 - np.clip(np.maximum(np.maximum(band, spot), np.maximum(edge, root)), 0, 0.92)


def _luna_pat(x, z, d, fore=True):
    lead = np.clip((-(z) - 0.0) * 6 - 0.5, 0, 1) * np.clip(1 - x * 0.3, 0, 1) * (0.75 if fore else 0.0)
    c = (0.7, 0.12) if fore else (0.45, 0.42)
    rr = np.hypot(x - c[0], z - c[1])
    spot = np.clip((0.09 - rr) / 0.03, 0, 1) * 0.7 + np.clip(1 - np.abs(rr - 0.13) / 0.025, 0, 1) * 0.6
    edge = np.clip((d + 0.04) / 0.03, 0, 1) * 0.3
    return 1 - np.clip(np.maximum(np.maximum(lead, spot), edge), 0, 0.9)


def _lepid(hid, kind="butterfly", preview=None):
    moth = kind in ("moth", "luna")
    H = Hero(hid, plan="Insect", gait="buzz", tags=["insect", "bug", "flying"] + (["moth"] if moth else ["butterfly"]))
    H.preview = preview or {}
    y = 1.15
    fz = 0.03 if moth else 0.012
    H.body((0, y, 0))
    tr_ = 0.26 if moth else 0.2
    th = ellipsoid(tr_, tr_ * 1.1, 0.34, (0, y, 0))
    th = hairy(th, fz, 30, 1)
    H.piece("Torso", "Body", th, col="secondary" if not moth else "primary", mat="fur", tris=900, pattern=gradient(1, y - 0.3, y + 0.3, 0.9, 0.7))
    # head
    H.bone("Head", "Body", (0, y, -0.28))
    hc = A(0, y - 0.02, -0.45)
    hd = sphere(0.17 if not moth else 0.2, T(hc))
    hd = hd.su(ellipsoid(0.1, 0.12, 0.1, T(hc + A(0, -0.1, -0.08))), 0.05)                   # palps
    hd = hairy(hd, fz * 0.7, 30, 2)
    H.piece("HeadP", "Head", hd, col="secondary" if not moth else "primary", mat="fur", tris=600, role="head")
    H.mprim("Eye#", "Head", "Ball", (0.2, 0.2, 0.2), T(hc + A(0.12, 0.03, -0.06)), col="bugEye", mat="hard", pri=1.25, role="eye")
    H.mprim("Shine#", "Head", "Ball", (0.05,) * 3, T(hc + A(0.18, 0.1, -0.12)), col="shine", mat="hard", pri=2.4, role="shine")
    H.piece("Proboscis", "Head", torus(0.07, 0.018, axis=0).at(*T(hc + A(0, -0.2, -0.12))), col="dark", mat="hard", tris=200, role="detail", pri=1.6)
    base = hc + A(0.06, 0.13, -0.08)
    if moth:
        pts = [base, base + A(0.15, 0.25, -0.2), base + A(0.32, 0.38, -0.5)]
        antenna(H, "", T(base), pts, 0.025, 0.018, col="secondary" if kind == "moth" else "cream", kind="thread", feather=0.1)
    else:
        pts = [base, base + A(0.12, 0.3, -0.3), base + A(0.3, 0.55, -0.75), base + A(0.42, 0.68, -1.05)]
        antenna(H, "", T(base), pts, 0.022, 0.018, col="dark", kind="thread", club=0.05)
    # abdomen
    H.bone("Abdomen", "Body", (0, y - 0.02, 0.28))
    ab = round_cone((0, y - 0.02, 0.25), (0, y - 0.18, 1.25 if not moth else 1.05), 0.17 if not moth else 0.24, 0.07 if not moth else 0.1)
    ab = hairy(ab, fz, 30, 3)
    H.piece("Gaster", "Abdomen", ab, col="secondary" if not moth else "primary", mat="fur", tris=700,
            pattern=stripes(lambda Q: Q[:, 2], 1 / 0.16, width=0.2, depth=0.3))
    # legs (thin, the front pair is small)
    hy = y - 0.15
    r = (0.04, 0.035, 0.028, 0.022)
    specs = [("F", legspec((0.08, hy, -0.15), 50, 0.3, hy + 0.05, 0.6, 0.35, 0.82, 0.03)),
             ("M", legspec((0.09, hy, 0.0), -5, 0.42, hy + 0.15, 0.82, 0.3, 1.1, 0.03)),
             ("B", legspec((0.09, hy, 0.12), -45, 0.45, hy + 0.15, 0.9, 0.3, 1.2, 0.03))]
    legs = _flyer_legs(H, specs, r, col="dark", tris=(180, 170, 150))
    # wings: forewing over hindwing, both raised in a V at rest (parallel planes 0.07 apart: no overlap)
    if kind == "butterfly":
        fw = [(0, -0.12), (0.6, -0.42), (1.45, -0.72), (1.75, -0.58), (1.55, 0.05), (1.05, 0.42), (0.35, 0.42), (0.02, 0.18)]
        hw = [(0, 0.05), (0.6, 0.12), (1.15, 0.42), (1.25, 0.85), (0.95, 1.25), (0.45, 1.25), (0.08, 0.7)]
        f1 = dict(col="secondary", border=0.16, vein_r=0.03, dots=0.035, spots=[(1.45, -0.5, 0.2)])
        f2 = dict(col="secondary", border=0.15, vein_r=0.028, dots=0.035)
        lift, col = 38, "primary"
    elif kind == "luna":
        fw = [(0, -0.1), (0.6, -0.32), (1.25, -0.5), (1.6, -0.62), (1.5, -0.3), (1.2, 0.2), (0.7, 0.4), (0.05, 0.2)]
        hw = [(0, 0.05), (0.55, 0.1), (1.0, 0.35), (1.0, 0.75), (0.75, 1.3), (0.55, 2.1), (0.42, 2.15), (0.35, 1.3), (0.08, 0.7)]
        f1 = dict(col="dark", border=0.0, veins=False, rings=[(0.72, 0.1, 0.12, 0.035)], spots=[(0.72, 0.1, 0.05)],
                  extra=seg2((0.0, -0.1), (1.45, -0.5), 0.05))
        f2 = dict(col="dark", border=0.0, veins=False, rings=[(0.5, 0.45, 0.12, 0.035)], spots=[(0.5, 0.45, 0.05)])
        lift, col = 22, "primary"
    else:  # moth: broad triangular wings held lower
        fw = [(0, -0.12), (0.7, -0.4), (1.55, -0.55), (1.7, -0.35), (1.4, 0.35), (0.6, 0.48), (0.02, 0.2)]
        hw = [(0, 0.05), (0.6, 0.15), (1.1, 0.4), (1.05, 0.8), (0.6, 0.95), (0.1, 0.6)]
        wav = lambda off: S.SDF(lambda p, off=off: np.abs(p[:, 0] - off - 0.08 * np.sin(p[:, 2] * 9)) - 0.035)
        f1 = dict(col="secondary", border=0.07, veins=False, rings=[(0.95, 0.05, 0.13, 0.035)], extra=wav(0.45) | wav(1.25))
        f2 = dict(col="secondary", border=0.07, veins=False, rings=[(0.55, 0.45, 0.12, 0.035)], spots=[(0.55, 0.45, 0.05)], extra=wav(0.3))
        lift, col = 14, "primary"
    sh = lambda x, z, d: 1 - 0.25 * np.clip(0.45 - np.hypot(x, z), 0, 1)
    wr = 0.16 if kind == "luna" else (0.13 if kind == "moth" else 0.08)
    w1 = flat_wing(H, "Wing", (0.12, y + 0.12, -0.12), fw, yaw=0, lift=lift, col=col, mat="skin", pat2d=sh, rnd=wr, tris=700, frame=f1)
    w2 = flat_wing(H, "HWing", (0.12, y + 0.0, 0.0), hw, yaw=0, lift=lift, col=col, mat="skin", pat2d=sh, rnd=wr, tris=700, pri=1.65, frame=f2)
    wings = _wingrig((w1, 0.0, 1.0), (w2, 0.04, 1.0))
    MB.flyer(H, wings, legs=legs, head="Head", abd="Abdomen", ants=[("AntR", 1), ("AntL", -1)], height=1.4, flaps=2, period=0.7,
             amp=0.75, slow=True, hover_idle=False, attack="dive", sweep=0.05, rest=0.0)
    finish(H, mouth=T(hc + A(0, -0.2, -0.2)), top=T(hc + A(0, 0.3, 0)), legs=legs)
    return H


@hero("butterfly", "bugs")
def butterfly():
    return _lepid("butterfly", "butterfly", preview={"primary": "#F2901E", "secondary": "#1E1E1E", "bugEye": "#111111", "dark": "#1E1E1E"})


@hero("moth", "bugs")
def moth():
    return _lepid("moth", "moth", preview={"primary": "#B8A88A", "secondary": "#6A5A44", "bugEye": "#1A1410", "dark": "#3A3024"})


@hero("luna moth", "bugs")
def luna_moth():
    return _lepid("luna moth", "luna", preview={"primary": "#B8E8A8", "secondary": "#E8F0D8", "bugEye": "#1A1410", "dark": "#6A4A3A", "cream": "#F2E8C8"})


# ================================================================================================ flies, mosquitoes, dragonflies, cicadas
def _flyer(hid, kind="fly", preview=None):
    H = Hero(hid, plan="Insect", gait="buzz", tags=["insect", "bug", "flying"])
    H.preview = preview or {}
    mosq, dragon, cicada = kind == "mosquito", kind == "dragonfly", kind == "cicada"
    y = {"fly": 1.0, "mosquito": 1.45, "dragonfly": 1.05, "cicada": 1.0}[kind]
    H.body((0, y, 0))
    # ---------------------------------------------------------------- thorax
    if kind == "fly":
        th = ellipsoid(0.42, 0.42, 0.5, (0, y + 0.05, 0))
        th = th.noise(0.012, 40, 3)
        tpat = lambda P: 1 - 0.55 * np.clip(1 - np.abs(np.abs(P[:, 0]) - np.array(0.0)) / 0.06, 0, 1) * (P[:, 1] > y + 0.2) - \
            0.5 * np.clip(1 - np.abs(np.abs(P[:, 0]) - 0.2) / 0.05, 0, 1) * (P[:, 1] > y + 0.15)
        tcol = "primary"
    elif mosq:
        th = ellipsoid(0.22, 0.27, 0.3, (0, y + 0.05, 0)).su(ellipsoid(0.18, 0.18, 0.2, (0, y - 0.12, -0.05)), 0.08)
        tpat, tcol = gradient(1, y - 0.2, y + 0.3, 1.0, 0.7), "primary"
    elif dragon:
        th = ellipsoid(0.27, 0.36, 0.4).rot(-25, 0, 0).at(0, y + 0.02, 0)
        tpat = lambda P: 1 - 0.75 * np.clip(1 - np.abs(np.mod((P[:, 2] + 0.4 * P[:, 1]) / 0.16, 1) - 0.5) / 0.12, 0, 1) * (np.abs(P[:, 0]) > 0.18)
        tcol = "primary"
    else:
        th = ellipsoid(0.5, 0.42, 0.48, (0, y + 0.05, -0.05)).su(ellipsoid(0.36, 0.25, 0.3, (0, y + 0.3, 0.15)), 0.15)
        tpat = lambda P: 1 - 0.6 * np.clip((P[:, 1] - y - 0.25) * 5, 0, 1) * np.clip(1 - np.abs(P[:, 0]) / 0.2, 0, 1)
        tcol = "primary"
    H.piece("Torso", "Body", th, col=tcol, mat="hard", tris=1300, res=124, pattern=tpat)
    # ---------------------------------------------------------------- head
    if kind == "fly":
        hc = A(0, y - 0.02, -0.62)
        H.bone("Head", "Body", (0, y, -0.4))
        hd = ellipsoid(0.36, 0.34, 0.22, T(hc)).su(round_cone(T(hc + A(0, 0, 0.1)), (0, y, -0.35), 0.15, 0.2), 0.05)
        hd = hd.su(round_cone(T(hc + A(0, -0.2, -0.08)), T(hc + A(0, -0.48, -0.15)), 0.08, 0.05), 0.05)
        hd = hd.su(ellipsoid(0.12, 0.05, 0.1, T(hc + A(0, -0.52, -0.16))), 0.04)                    # sponge pad
        H.piece("HeadP", "Head", hd, col="primary", mat="hard", tris=900, role="head")
        H.mprim("Eye#", "Head", "Ellipsoid", (0.34, 0.52, 0.44), T(hc + A(0.22, 0.05, -0.04)), rot=(0, -0.3, 0), col="bugEye", mat="hard", pri=1.25, role="eye")
        H.mprim("Shine#", "Head", "Ball", (0.08,) * 3, T(hc + A(0.33, 0.2, -0.2)), col="shine", mat="hard", pri=2.4, role="shine")
        base = hc + A(0.05, 0.08, -0.2)
        antenna(H, "", T(base), [base, base + A(0.04, -0.06, -0.08), base + A(0.08, -0.15, -0.12)], 0.03, 0.035, col="dark", kind="thread", club=0.04)
        mouth = hc + A(0, -0.52, -0.16)
    elif mosq:
        hc = A(0, y - 0.05, -0.42)
        H.bone("Head", "Body", (0, y - 0.03, -0.28))
        hd = sphere(0.16, T(hc)).su(round_cone(T(hc + A(0, 0, 0.05)), (0, y - 0.05, -0.22), 0.08, 0.1), 0.04)
        pr = [hc + A(0, -0.05, -0.1), hc + A(0, -0.3, -0.5), hc + A(0, -0.62, -0.85)]
        hd = hd.su(tube([T(p) for p in pr], [0.035, 0.022, 0.01]), 0.03)                          # needle proboscis
        H.piece("HeadP", "Head", hd, col="primary", mat="hard", tris=700, role="head")
        H.mprim("Eye#", "Head", "Ball", (0.2, 0.2, 0.2), T(hc + A(0.1, 0.02, -0.05)), col="bugEye", mat="hard", pri=1.25, role="eye")
        H.mprim("Shine#", "Head", "Ball", (0.05,) * 3, T(hc + A(0.16, 0.09, -0.11)), col="shine", mat="hard", pri=2.4, role="shine")
        base = hc + A(0.04, 0.05, -0.12)
        antenna(H, "", T(base), [base, base + A(0.12, 0.15, -0.25), base + A(0.25, 0.22, -0.55)], 0.022, 0.012, col="dark", kind="thread", feather=0.06)
        mouth = pr[-1]
    elif dragon:
        hc = A(0, y + 0.1, -0.52)
        H.bone("Head", "Body", (0, y + 0.05, -0.36))
        hd = ellipsoid(0.24, 0.2, 0.18, T(hc + A(0, -0.08, -0.04))).su(round_cone(T(hc + A(0, -0.05, 0.1)), (0, y + 0.06, -0.3), 0.1, 0.13), 0.05)
        H.piece("HeadP", "Head", hd, col="primary", mat="hard", tris=600, role="head")
        H.mprim("Eye#", "Head", "Ball", (0.42, 0.42, 0.42), T(hc + A(0.15, 0.06, -0.02)), col="bugEye", mat="hard", pri=1.25, role="eye")
        H.mprim("Shine#", "Head", "Ball", (0.09,) * 3, T(hc + A(0.26, 0.2, -0.14)), col="shine", mat="hard", pri=2.4, role="shine")
        base = hc + A(0.04, 0.0, -0.2)
        antenna(H, "", T(base), [base, base + A(0.04, 0.05, -0.1), base + A(0.08, 0.06, -0.18)], 0.016, 0.01, col="dark", kind="thread", tris=150)
        mouth = hc + A(0, -0.2, -0.2)
    else:  # cicada: broad blunt head, wide-set eyes
        hc = A(0, y + 0.0, -0.55)
        H.bone("Head", "Body", (0, y, -0.4))
        hd = ellipsoid(0.48, 0.28, 0.24, T(hc)).su(ellipsoid(0.2, 0.25, 0.18, T(hc + A(0, -0.12, -0.15))), 0.08)
        hd = surface_cut(hd, S.SDF(lambda p: np.maximum(np.abs(np.abs(np.mod(p[:, 1] - hc[1], 0.08) - 0.04) - 0.04) - 0.01, np.abs(p[:, 0]) - 0.14)), 0.03, 0.008)  # ribbed face
        hd = hd.su(round_cone(T(hc + A(0, -0.2, -0.15)), T(hc + A(0, -0.45, 0.1)), 0.05, 0.03), 0.04)  # beak
        H.piece("HeadP", "Head", hd, col="primary", mat="hard", tris=900, role="head")
        H.mprim("Eye#", "Head", "Ball", (0.22, 0.22, 0.22), T(hc + A(0.45, 0.08, 0.0)), col="bugEye", mat="hard", pri=1.25, role="eye")
        H.mprim("Shine#", "Head", "Ball", (0.06,) * 3, T(hc + A(0.5, 0.17, -0.07)), col="shine", mat="hard", pri=2.4, role="shine")
        H.mprim("Ocel#", "Head", "Ball", (0.05,) * 3, T(hc + A(0.08, 0.27, 0.0)), col="bugEye", mat="hard", pri=2.0, role="eye")
        base = hc + A(0.22, 0.05, -0.2)
        antenna(H, "", T(base), [base, base + A(0.08, 0.06, -0.08), base + A(0.15, 0.08, -0.16)], 0.02, 0.012, col="dark", kind="thread", tris=150)
        mouth = hc + A(0, -0.3, -0.2)
    # ---------------------------------------------------------------- abdomen (+ tail for the dragonfly)
    tail = []
    if kind == "fly":
        H.bone("Abdomen", "Body", (0, y, 0.38))
        c = A(0, y - 0.08, 0.85)
        ab = ellipsoid(0.42, 0.32, 0.52).rot(8, 0, 0).at(*T(c)).su(ellipsoid(0.25, 0.2, 0.2, (0, y, 0.42)), 0.1)
        apat = combine(stripes(lambda Q: Q[:, 2], 1 / 0.22, width=0.25, depth=0.4), lambda Q: 1 - 0.3 * (np.mod(np.floor(Q[:, 0] / 0.15) + np.floor(Q[:, 2] / 0.22), 2)))
    elif mosq:
        H.bone("Abdomen", "Body", (0, y - 0.05, 0.25))
        ab = round_cone((0, y - 0.05, 0.25), (0, y - 0.45, 1.5), 0.13, 0.07)
        apat = stripes(lambda Q: Q[:, 2], 1 / 0.18, width=0.3, depth=0.55)
    elif dragon:
        H.bone("Abdomen", "Body", (0, y - 0.05, 0.3))
        ab = round_cone((0, y - 0.05, 0.25), (0, y - 0.12, 1.65), 0.13, 0.075).su(ellipsoid(0.15, 0.15, 0.25, (0, y - 0.07, 0.45)), 0.08)
        apat = stripes(lambda Q: Q[:, 2], 1 / 0.28, width=0.16, depth=0.7)
        H.bone("Tail", "Abdomen", (0, y - 0.12, 1.6))
        tl = round_cone((0, y - 0.12, 1.55), (0, y - 0.18, 3.0), 0.08, 0.065)
        for sx in (1, -1):
            tl = tl.su(round_cone((0.03 * sx, y - 0.18, 2.95), (0.1 * sx, y - 0.22, 3.2), 0.035, 0.015), 0.02)
        H.piece("TailP", "Tail", tl, col="primary", mat="hard", tris=600, role="tail", pattern=stripes(lambda Q: Q[:, 2], 1 / 0.28, width=0.16, depth=0.7), pri=1.4)
        tail = ["Abdomen", "Tail"]
    else:
        H.bone("Abdomen", "Body", (0, y, 0.3))
        c = A(0, y - 0.05, 0.85)
        ab = ellipsoid(0.42, 0.36, 0.62).rot(8, 0, 0).at(*T(c))
        apat = stripes(lambda Q: Q[:, 2], 1 / 0.2, width=0.2, depth=0.45)
    H.piece("Gaster", "Abdomen", ab, col="primary" if not cicada else "dark", mat="hard", tris=1000 if not mosq else 600, pattern=apat)
    # ---------------------------------------------------------------- legs
    if kind == "fly":
        hy, r = y - 0.3, (0.06, 0.05, 0.04, 0.03)
        specs = [("F", legspec((0.12, hy, -0.2), 45, 0.4, hy + 0.1, 0.8, 0.3, 1.05)), ("M", legspec((0.15, hy, 0.0), -10, 0.5, hy + 0.1, 0.95, 0.3, 1.25)),
                 ("B", legspec((0.15, hy, 0.18), -45, 0.55, hy + 0.1, 1.05, 0.3, 1.35))]
        legs = _flyer_legs(H, specs, r, col="dark", hair=0.008, spines=2)
    elif mosq:
        hy, r = y - 0.2, (0.035, 0.028, 0.02, 0.016)
        specs = [("F", legspec((0.08, hy, -0.1), 50, 0.7, y + 0.35, 1.6, 0.6, 2.1)), ("M", legspec((0.09, hy, 0.0), -5, 0.75, y + 0.4, 1.75, 0.55, 2.3)),
                 ("B", legspec((0.09, hy, 0.08), -50, 0.8, y + 0.45, 1.9, 0.6, 2.5))]
        legs = _flyer_legs(H, specs, r, col="secondary", tris=(160, 160, 150))
    elif dragon:
        hy, r = y - 0.3, (0.04, 0.035, 0.025, 0.02)
        specs = [("F", legspec((0.08, hy, -0.22), 40, 0.3, hy - 0.05, 0.6, 0.3, 0.8)), ("M", legspec((0.1, hy, -0.1), 5, 0.38, hy - 0.05, 0.75, 0.25, 0.95)),
                 ("B", legspec((0.1, hy, 0.02), -30, 0.42, hy - 0.05, 0.85, 0.25, 1.1))]
        legs = _flyer_legs(H, specs, r, col="dark", spines=2, tris=(160, 160, 150))
    else:
        hy, r = y - 0.3, (0.07, 0.06, 0.045, 0.032)
        specs = [("F", legspec((0.15, hy, -0.25), 45, 0.4, hy + 0.05, 0.75, 0.3, 1.0)), ("M", legspec((0.18, hy, 0.0), -10, 0.48, hy + 0.05, 0.9, 0.3, 1.2)),
                 ("B", legspec((0.18, hy, 0.18), -45, 0.52, hy + 0.05, 0.98, 0.3, 1.3))]
        legs = _flyer_legs(H, specs, r, col="dark", spines=1)
    # ---------------------------------------------------------------- wings
    if kind == "fly":
        w = [(0, -0.05), (0.6, -0.2), (1.3, -0.22), (1.55, -0.05), (1.3, 0.2), (0.6, 0.32), (0.1, 0.18)]
        w1 = glass_wing(H, "Wing", (0.16, y + 0.32, -0.1), w, yaw=-38, lift=12, rnd=0.05, tr=0.5)
        wings = _wingrig((w1, 0.0, 1.0))
        flaps, amp = 9, 0.8
    elif mosq:
        w = [(0, -0.03), (0.6, -0.1), (1.35, -0.1), (1.5, 0.0), (1.3, 0.1), (0.5, 0.12), (0.05, 0.06)]
        w1 = glass_wing(H, "Wing", (0.1, y + 0.2, -0.05), w, yaw=-60, lift=10, rnd=0.03, tr=0.45, tris=300)
        wings = _wingrig((w1, 0.0, 1.0))
        flaps, amp = 10, 0.7
    elif dragon:
        fw = [(0, -0.04), (0.8, -0.14), (2.1, -0.15), (2.3, -0.05), (2.1, 0.12), (0.8, 0.14), (0.05, 0.08)]
        hw = [(0, -0.06), (0.8, -0.15), (2.0, -0.15), (2.2, -0.04), (2.0, 0.12), (0.6, 0.25), (0.05, 0.2)]
        w1 = glass_wing(H, "Wing", (0.12, y + 0.3, -0.16), fw, yaw=8, lift=4, rnd=0.05, tr=0.5, veins_n=10, tris=420)
        w2 = glass_wing(H, "HWing", (0.12, y + 0.26, 0.12), hw, yaw=-12, lift=2, rnd=0.05, tr=0.5, veins_n=10, tris=420)
        wings = _wingrig((w1, 0.0, 1.0), (w2, 0.25, 1.0))
        flaps, amp = 6, 0.45
    else:  # cicada: wings roofed over the abdomen
        fw = [(0, -0.08), (0.7, -0.18), (1.6, -0.2), (1.9, -0.05), (1.6, 0.2), (0.7, 0.3), (0.05, 0.15)]
        hw = [(0, -0.05), (0.5, -0.1), (1.0, -0.08), (1.05, 0.08), (0.6, 0.2), (0.05, 0.12)]
        w1 = glass_wing(H, "Wing", (0.25, y + 0.28, -0.15), fw, yaw=-65, lift=-12, roll=-25, rnd=0.05, tr=0.4, veins_n=8,
                        col="wingGlass")
        w2 = glass_wing(H, "HWing", (0.22, y + 0.18, 0.05), hw, yaw=-62, lift=-14, roll=-25, rnd=0.04, tr=0.4, tris=300)
        wings = _wingrig((w1, 0.0, 1.0), (w2, 0.05, 1.0))
        flaps, amp = 7, 0.6
    MB.flyer(H, wings, legs=legs, head="Head", abd="Abdomen", ants=[("AntR", 1), ("AntL", -1)], height=1.4, flaps=flaps, period=0.5,
             amp=amp, attack="dive" if not mosq else "dive")
    finish(H, mouth=T(mouth), top=T(hc + A(0, 0.3, 0)), legs=legs, tail=tail)
    return H


@hero("fly", "bugs")
def fly():
    return _flyer("fly", "fly", preview={"primary": "#3A3A3A", "secondary": "#C82A2A", "bugEye": "#8A1A14", "dark": "#1E1E1E", "wingGlass": "#C8CCD0"})


@hero("mosquito", "bugs")
def mosquito():
    return _flyer("mosquito", "mosquito", preview={"primary": "#3A3430", "secondary": "#8A7A6A", "bugEye": "#1A1410", "dark": "#2A2420", "wingGlass": "#D0D4D8"})


@hero("dragonfly", "bugs")
def dragonfly():
    return _flyer("dragonfly", "dragonfly", preview={"primary": "#2A9AD8", "secondary": "#6AE0A0", "bugEye": "#1E5A6A", "dark": "#1E2A30", "wingGlass": "#D8F0F0"})


@hero("cicada", "bugs")
def cicada():
    return _flyer("cicada", "cicada", preview={"primary": "#3A4A2A", "secondary": "#E8701E", "bugEye": "#8A3A10", "dark": "#1E2414", "wingGlass": "#C8E0C0"})
