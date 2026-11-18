"""Aquatic family, bony fish: one parametric fish (lofted body from a side/top profile, split into a head and four
spine segments that carry a travelling body wave, a lower jaw that opens, fin plates with baked fin rays, eyes, teeth,
barbels, spines, lures, bills and patch overlays) yielding the generic fish archetypes: perch-like fish, bass,
goldfish, koi, angelfish, discus, clownfish, blue tang, betta, salmon, trout, catfish, piranha, barracuda, tuna,
swordfish, marlin, pufferfish, anglerfish, flounder, sunfish.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
import sdf as S
from kit import Hero, hero, stripes, spots, gradient, combine
from map import NOTFOOD
import motion_aquatic as MA
from motion_aquatic import Profile, plate, ray_lines, par_lines, segment, overlay, slab

FAM = "aquatic"


# ------------------------------------------------------------------------------------------------ word colours
def _wordcols():
    out = {}
    try:
        import os
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "words.tsv")
        for line in open(os.path.normpath(p)):
            f = line.rstrip("\n").split("\t")
            if len(f) > 6 and f[5].startswith("#"):
                out[f[0]] = (f[5], f[6])
    except OSError:
        pass
    return out


WC = _wordcols()


def pv(word, **kw):
    c = WC.get(word, ("#9AA5B1", "#E4E7EB"))
    d = {"primary": c[0], "secondary": c[1]}
    d.update(kw)
    return d


def teardrop(length, width, n=16, root=0.55, tip=0.0, skew=0.0):
    """Fin outline along +a (root at a=0, half width `width`*root there), rounded tip at a = length."""
    pts = []
    for i in range(n + 1):
        th = math.pi * i / n
        a = length * (1 - math.cos(th)) / 2
        s = math.sin(th)
        w = width * (root + (1 - root) * s) * (1 - tip * (a / length) ** 2)
        pts.append((a - 0.04 * length, w * 0.5 + skew * a))
    for i in range(n, -1, -1):
        th = math.pi * i / n
        a = length * (1 - math.cos(th)) / 2
        s = math.sin(th)
        w = width * (root + (1 - root) * s) * (1 - tip * (a / length) ** 2)
        pts.append((a - 0.04 * length, -w * 0.5 + skew * a))
    # drop duplicates at the tips
    out = []
    for p in pts:
        if not out or abs(out[-1][0] - p[0]) + abs(out[-1][1] - p[1]) > 1e-6:
            out.append(p)
    return out


# caudal fin outlines: (dz, dy) in L units from the tail base, root first (forward), free edge after
def caudal(kind, span=0.24, length=0.22):
    if isinstance(kind, list):
        return kind
    s, l = span, length
    if kind == "forked":
        return [(-0.05, 0.05), (0.04, 0.09), (l * 0.7, s * 0.85), (l, s), (l * 0.98, s * 0.92), (l * 0.6, s * 0.3), (l * 0.42, 0.0),
                (l * 0.6, -s * 0.3), (l * 0.98, -s * 0.92), (l, -s), (l * 0.7, -s * 0.85), (0.04, -0.09), (-0.05, -0.05)]
    if kind == "lunate":  # tuna / swordfish / marlin: stiff sickle
        return [(-0.05, 0.035), (0.03, 0.05), (l * 0.55, s * 0.75), (l, s), (l * 0.96, s * 0.93), (l * 0.42, s * 0.18), (l * 0.3, 0.0),
                (l * 0.42, -s * 0.18), (l * 0.96, -s * 0.93), (l, -s), (l * 0.55, -s * 0.75), (0.03, -0.05), (-0.05, -0.035)]
    if kind == "round":
        pts = [(-0.05, 0.05)]
        for i in range(13):
            a = math.radians(70 - i * 140 / 12)
            pts.append((l * 0.45 + l * 0.55 * math.cos(a), s * math.sin(a)))
        pts.append((-0.05, -0.05))
        return pts
    if kind == "square":
        return [(-0.05, 0.05), (0.03, 0.08), (l * 0.85, s), (l, s * 0.9), (l * 1.02, s * 0.3), (l, 0), (l * 1.02, -s * 0.3),
                (l, -s * 0.9), (l * 0.85, -s), (0.03, -0.08), (-0.05, -0.05)]
    if kind == "veil":  # goldfish / betta: long flowing lobes that droop
        return [(-0.05, 0.05), (0.06, 0.12), (l * 0.5, s * 0.95), (l * 0.85, s * 0.85), (l, s * 0.5), (l * 0.9, s * 0.15), (l * 0.75, 0.0),
                (l * 1.02, -s * 0.25), (l * 1.08, -s * 0.75), (l * 0.85, -s * 1.15), (l * 0.5, -s * 1.05), (0.06, -0.12), (-0.05, -0.05)]
    if kind == "fan":  # betta: huge round fan
        pts = [(-0.05, 0.05)]
        for i in range(17):
            a = math.radians(80 - i * 170 / 16)
            r = 1.0 + 0.06 * math.sin(i * 2.3)
            pts.append((l * 0.35 + l * 0.65 * r * math.cos(a), s * r * math.sin(a) - 0.05 * s))
        pts.append((-0.05, -0.05))
        return pts
    if kind == "shark":  # heterocercal: long upper lobe
        return [(-0.06, 0.05), (0.02, 0.06), (l * 0.75, s * 0.95), (l, s * 1.05), (l * 0.97, s * 0.93), (l * 0.62, s * 0.38), (l * 0.5, s * 0.12),
                (l * 0.45, -s * 0.05), (l * 0.6, -s * 0.48), (l * 0.52, -s * 0.55), (0.03, -0.08), (-0.06, -0.05)]
    raise ValueError(kind)


FBASE = dict(
    L=6.0,
    prof=None,             # (t, top, bot, halfwidth) rows in L units
    square=0.0,
    seg=(0.3, 0.5, 0.68, 0.84),
    lift=0.35,
    eye=(0.12, 30, 0.042),  # t, angle on the section (deg above side), radius (L units)
    eye_col="iris", pupil="round",
    mouth=(0.0, -0.1, 0.1, 0.0, 0.5),  # y frac at the nose (-1 bottom .. 1 top), unused, jaw length (t), slope, jaw depth frac
    teeth=0, tooth_len=0.02,
    fins=(),               # dicts
    caudal=("forked", 0.24, 0.22),
    caudal_col=None,
    fin_col="primary", fin_tr=0.0, fin_th=0.012,
    pecs=dict(t=0.3, ang=-25, len=0.17, wid=0.08, splay=35, droop=15, roll=-35),
    pelvic=dict(t=0.36, ang=-75, len=0.1, wid=0.045, splay=20, droop=40, roll=10),
    pattern=None, back=0.72, scales=0.1, gill=True,
    overlays=(),           # (t1, t2, region(pr) -> SDF, col)
    extra=None,            # fn(H, ctx)
    sculpt=None,           # fn(body, pr) -> body
    attack="bite", amp=0.3, period=0.9,
    mat="skin",
    preview={},
    tags=("fish",),
    gait="swim",
    caudal_plane="v",
    mode="yaw",
    eye_look=None,
)


def segcut(body, za, zb, ov, ck, delta):
    """Body between za and zb, extended by ov at each cut where the surface sinks inward by delta (so the overlap with
    the neighbouring segment is never coincident: no z-fighting) with a rounded cut."""
    w = 0.5 * ov

    def f(Q):
        z = Q[:, 2]
        ramp = np.clip((za - z) / w, 0, 1) + np.clip((z - zb) / w, 0, 1)
        return body(Q) + delta * ramp

    return S.SDF(f).si(slab(2, za - ov, zb + ov), ck)


def _fish(hid, **kw):
    P = dict(FBASE)
    P.update(kw)
    L = P["L"]
    rows = P["prof"]
    ymin = min(r[2] for r in rows)
    y0 = -ymin * L + P["lift"]
    z0 = -0.45 * L
    pr = Profile(rows, L, z0, y0)
    H = Hero(hid, plan="Fish", gait=P["gait"], tags=list(P["tags"]))
    H.preview = P["preview"]
    body = pr.sdf(squareness=P["square"])
    if P["sculpt"]:
        body = P["sculpt"](body, pr)
    seg = P["seg"]
    ov = 0.03 * L
    ck = 0.012 * L

    # ---------------------------------------------------------------- bones
    tb = 0.42
    _, _, _, cb, _ = pr.at(tb)
    H.body((0, cb, pr.z(tb)))

    def axis(t):
        return (0.0, pr.at(t)[3], pr.z(t))

    H.bone("Head", "Body", axis(seg[0]))
    nsp = len(seg) - 1
    spines = [f"Spine{i}" for i in range(1, nsp + 1)]
    prev = "Body"
    for i, b in enumerate(spines):
        H.bone(b, prev, axis(seg[i + 1]))
        prev = b
    H.bone("Tail", prev, axis(1.0))
    segbones = [("Head", -9, seg[0]), ("Body", seg[0], seg[1])] + [(spines[i], seg[i + 1], seg[i + 2] if i + 2 < len(seg) else 9) for i in range(nsp)]

    def bone_at(t):
        for b, a, c in segbones:
            if a <= t < c:
                return b
        return spines[-1]

    # ---------------------------------------------------------------- patterns
    def back_shade(Q):
        c = np.array([pr.at(t)[3] for t in np.linspace(0, 1, 32)])
        tt = np.clip((Q[:, 2] - z0) / L, 0, 1)
        cy = np.interp(tt, np.linspace(0, 1, 32), c)
        k = np.clip((Q[:, 1] - cy) / (0.12 * L) + 0.3, 0, 1)
        return 1 - (1 - P["back"]) * k

    def gill_line(Q):
        if not P["gill"]:
            return np.ones(len(Q))
        tg = P["gill"] if isinstance(P["gill"], float) else seg[0] - 0.06
        tp, bt, w, c, a = pr.at(tg)
        yy = (Q[:, 1] - c) / max(a, 1e-3)
        zl = pr.z(tg) - 0.06 * L * yy * yy
        d = np.abs(Q[:, 2] - zl)
        m = np.clip(1 - d / (0.007 * L), 0, 1) * (np.abs(Q[:, 0]) > 0.25 * w) * (np.abs(yy) < 0.9)
        return 1 - 0.45 * m

    def scale_pat(Q):
        if not P["scales"]:
            return np.ones(len(Q))
        f = 1 / (0.035 * L)
        a = np.abs(np.sin(math.pi * (Q[:, 2] + 0.7 * Q[:, 1]) * f))
        b = np.abs(np.sin(math.pi * (Q[:, 2] - 0.7 * Q[:, 1]) * f))
        m = np.clip(1 - np.minimum(a, b) / 0.25, 0, 1)
        nose = np.clip((Q[:, 2] - pr.z(seg[0] - 0.04)) / (0.05 * L), 0, 1) * np.clip((pr.z(0.97) - Q[:, 2]) / (0.04 * L), 0, 1)
        return 1 - P["scales"] * m * nose

    extra_pat = P["pattern"](pr, L) if P["pattern"] else None
    pat = combine(back_shade, gill_line, scale_pat, extra_pat)

    # ---------------------------------------------------------------- mouth / jaw regions
    my, _u, jl, slope, jd = P["mouth"]
    tpn, btn, wn, cn, an = pr.at(0.02)
    ym = cn + my * an
    zj = pr.z(jl)
    _, _, _, cj, aj = pr.at(jl)
    jdepth = jd * (aj * 2)

    def jaw_region(g):
        def f(Q):
            lip = ym + slope * (Q[:, 2] - z0)
            return np.maximum.reduce([Q[:, 2] - zj, Q[:, 1] - lip, (lip - jdepth) - Q[:, 1]]) - g
        return S.SDF(f)

    gap = 0.006 * L
    dl = 0.006 * L
    body_head = segcut(body, z0 - L, pr.z(seg[0]), ov, ck, dl)
    head_piece = body_head.ss(jaw_region(gap), 0.006 * L)
    jaw_piece = body.si(jaw_region(-gap), 0.006 * L)

    # ---------------------------------------------------------------- body pieces
    H.piece("HeadP", "Head", head_piece, col="primary", mat=P["mat"], tris=2200, res=128, role="head", pattern=pat)
    if nsp == 3:
        names = [("Trunk", "Body", seg[0], seg[1], 2400), ("Mid", "Spine1", seg[1], seg[2], 1700), ("Rear", "Spine2", seg[2], seg[3], 1100),
                 ("Peduncle", "Spine3", seg[3], 1.2, 700)]
    else:
        names = [("Trunk", "Body", seg[0], seg[1], 2000)] + [(f"Seg{i + 1}", spines[i], seg[i + 1], seg[i + 2] if i + 2 < len(seg) else 1.2,
                                                              max(500, int(1800 * (1 - i / nsp)))) for i in range(nsp)]
    for nm, b, a, c, tr in names:
        H.piece(nm, b, segcut(body, pr.z(a), pr.z(c), ov, ck, dl), col="primary", mat=P["mat"], tris=tr, res=120, role="body", pattern=pat)
    jb = H.bone("Jaw", "Head", (0, ym + slope * (zj - z0), zj))
    H.piece("JawP", "Jaw", jaw_piece, col="primary", mat=P["mat"], tris=600, role="jaw", pri=1.3, pattern=pat)
    # mouth interior (inside the lower lip; shows when the jaw opens)
    mz = (z0 + zj) / 2
    mw = pr.at(jl * 0.5)[2] * 1.3
    _tpm, _btm, _wm, _cm, _am = pr.at(max(jl * 0.5, 0.03))
    H.prim("Mouth", "Head", "Ellipsoid", (min(mw * 0.8, 1.2 * _wm), min(jdepth * 0.9, 0.8 * _am), (zj - z0) * 0.7), (0, ym - jdepth * 0.2, mz + 0.06 * (zj - z0) + 0.01 * L), col="mouth", mat="hard", role="mouth", pri=2.4)

    # ---------------------------------------------------------------- teeth
    if P["teeth"]:
        n = P["teeth"]
        up, lo = [], []
        tl = P["tooth_len"] * L
        t0 = P.get("teeth_t0", 0.015)
        for i in range(n):
            f = (i + 0.5) / n
            t = t0 + f * (jl - t0 - 0.02)
            z = pr.z(t)
            tp_, bt_, w_, c_, a_ = pr.at(t)
            y = ym + slope * (z - z0)
            yy = np.clip((y - c_) / max(a_, 1e-3), -0.97, 0.97)
            w = w_ * math.sqrt(1 - yy * yy) * 0.86
            r = tl * 0.32
            for sx in (1, -1):
                x = sx * max(w, 0.01 * L)
                k = 1.0 - 0.4 * f
                up.append(MA.cone_pts((x, y + tl * 0.6, z), (x * 0.98, y - tl * k, z), r))
                lo.append(MA.cone_pts((x * 0.95, y - tl * 0.6, z + 0.01 * L), (x * 0.93, y + tl * k * 0.9, z + 0.01 * L), r))
        H.piece("TeethUp", "Head", MA.union_all(up), col="tooth", mat="hard", tris=500, role="tooth", pri=2.0, ao=False, smooth=1, res=140)
        H.piece("TeethLo", "Jaw", MA.union_all(lo), col="tooth", mat="hard", tris=500, role="tooth", pri=2.0, ao=False, smooth=1, res=140)

    # ---------------------------------------------------------------- eyes
    te, ea, er = P["eye"] or (0.1, 0, 0.01)
    tp, bt, w, c, a = pr.at(te)
    th = math.radians(ea)
    nx, ny = math.cos(th) / w, math.sin(th) / a
    nn = math.hypot(nx, ny)
    nx, ny = nx / nn, ny / nn
    R = er * L
    ex = w * math.cos(th) - nx * R * 0.55
    ey = c + a * math.sin(th) - ny * R * 0.55
    if P["eye"]:
        H.eyes("Head", (ex, ey, pr.z(te)), R, col=P["eye_col"], pupil=P["pupil"], look=P["eye_look"] or (nx, ny * 0.6, -0.35))

    # ---------------------------------------------------------------- median fins
    fth = P["fin_th"] * L
    fcol = P["fin_col"]
    for i, F in enumerate(P["fins"]):
        kind = F["kind"]
        t1, t2 = F["t"]
        edge = F["edge"]  # (t, h) free edge, front to back
        top = kind in ("dorsal", "adipose", "sail")
        pts = []
        for t, hgt in edge:
            tc = float(np.clip(t, t1, t2))
            tp, bt, w, c, a = pr.at(tc)
            base = tp if top else bt
            pts.append((pr.z(t), base + (hgt if top else -hgt) * L))
        for k in range(8, -1, -1):
            t = t1 + (t2 - t1) * k / 8
            tp, bt, w, c, a = pr.at(t)
            base = (tp - 0.35 * a) if top else (bt + 0.35 * a)
            pts.append((pr.z(t), base))
        # polygon orientation: a = z, b = y in the x = 0 plane
        sh = plate((0, 0, 0), (0, 0, 1), (0, 1, 0), pts, F.get("th", 1.0) * fth, taper=0.4, edge=0.05 * L)
        bone = F.get("bone") or bone_at((t1 + t2) / 2)
        ry = (0, pr.at((t1 + t2) / 2)[0 if top else 1], pr.z(t1))
        fp = par_lines((0, 0, 1), 1 / (F.get("ray", 0.025) * L), depth=0.25, width=0.35) if F.get("ray", 0.025) else None
        if F.get("edgecol"):
            fp = combine(fp, F["edgecol"](pr, L))
        H.piece(F.get("name", f"Fin{i}"), bone, sh, col=F.get("col", fcol), mat="skin", tris=F.get("tris", 500), role="fin", pri=1.6,
                pattern=fp, tr=F.get("tr", P["fin_tr"]), res=130, smooth=3)

    # ---------------------------------------------------------------- caudal fin
    if P["caudal"]:
        kind, span, clen = P["caudal"][:3]
        pts = [(pr.z(1.0) + dz * L, pr.at(1.0)[3] + dy * L) for dz, dy in caudal(kind, span, clen)]
        cy = pr.at(1.0)[3]
        if P["caudal_plane"] == "h":
            pts = [(z, y - cy) for z, y in pts]
            sh = plate((0, cy, 0), (0, 0, 1), (1, 0, 0), pts, fth * 1.1, taper=0.35, edge=0.06 * L)
            cp = ray_lines((0, cy, pr.z(1.0) - 0.05 * L), (0, 0, 1), (1, 0, 0), n=15, spread=(-75, 75), depth=0.25, width=0.3)
        else:
            sh = plate((0, 0, 0), (0, 0, 1), (0, 1, 0), pts, fth * 1.1, taper=0.35, edge=0.06 * L)
            cp = ray_lines((0, cy, pr.z(1.0) - 0.05 * L), (0, 0, 1), (0, 1, 0), n=15, spread=(-75, 75), depth=0.25, width=0.3)
        if P.get("caudal_pat"):
            cp = combine(cp, P["caudal_pat"](pr, L))
        H.piece("Caudal", "Tail", sh, col=P["caudal_col"] or fcol, mat="skin", tris=900, role="fin", pri=1.5, pattern=cp, tr=P["fin_tr"], res=130, smooth=3)

    # ---------------------------------------------------------------- paired fins
    def paired(name, F, bone_parent):
        t = F["t"]
        tp, bt, w, c, a = pr.at(t)
        th = math.radians(F["ang"])
        root = np.array((w * math.cos(th) * 0.8, c + a * math.sin(th) * 0.8, pr.z(t)))
        H.mbone(name + "#", bone_parent, tuple(root))
        sp, dr, rl = math.radians(F["splay"]), math.radians(F["droop"]), math.radians(F["roll"])
        u = np.array((math.sin(sp), -math.sin(dr), math.cos(sp)))
        u /= np.linalg.norm(u)
        v0 = np.array((math.sin(rl), math.cos(rl), 0.0))
        pts = F.get("pts") or teardrop(F["len"] * L, F["wid"] * L, root=F.get("rootw", 0.6), tip=F.get("tipk", 0.0))
        o = root - u * 0.03 * L
        sh = plate(tuple(o), tuple(u), tuple(v0), pts, fth * F.get("th", 0.9), taper=0.35, edge=0.03 * L, bend=F.get("bend", 0.0))
        rp = ray_lines(tuple(o), tuple(u), tuple(v0), n=9, spread=(-60, 60), depth=0.22)
        H.mpiece(name + "P#", name + "#", sh, col=F.get("col", fcol), mat="skin", tris=F.get("tris", 450), role="fin", pri=1.6, pattern=rp,
                 tr=P["fin_tr"], res=120, smooth=3)
        return (name + "R", name + "L")

    pecs = []
    if P["pecs"]:
        pecs.append(paired("Pec", P["pecs"], bone_at(P["pecs"]["t"])))
    if P["pelvic"]:
        pecs.append(paired("Pelvic", P["pelvic"], bone_at(P["pelvic"]["t"])))

    # ---------------------------------------------------------------- overlays (bands, patches, bellies)
    for j, (t1, t2, region, col) in enumerate(P["overlays"]):
        reg = region(pr, L)
        for b, a, c in segbones:
            nm = {"Head": "H", "Body": "T", "Spine1": "M", "Spine2": "R", "Spine3": "P"}.get(b, b[-1])
            lo, hi = max(a, t1), min(c, t2)
            if hi - lo <= 0.03:
                continue
            base = head_piece if b == "Head" else segcut(body, pr.z(max(a, -1)), pr.z(min(c, 1.3)), ov, ck, dl)
            sh = overlay(base, reg, t=0.006 * L + 0.01)
            if lo > a or hi < c:
                sh = sh.si(slab(2, pr.z(lo) - (0.01 * L if lo > a else 2 * ov), pr.z(hi) + (0.01 * L if hi < c else 2 * ov)), ck)
            H.piece(f"Patch{j}{nm}", b, sh, col=col, mat=P["mat"], tris=700 if (hi - lo) > 0.12 else 450, role="pattern", pri=1.4, res=120)

    ctx = dict(pr=pr, L=L, body=body, z0=z0, ym=ym, zj=zj, bone_at=bone_at, fth=fth, head_piece=head_piece)
    if P["extra"]:
        P["extra"](H, ctx)

    # ---------------------------------------------------------------- rig, sockets, motion
    tp, bt, w, c, a = pr.at(te)
    H.socket("mouth", (0, ym, z0 - 0.02 * L), "Jaw")
    H.socket("head", (0, tp + 0.05 * L, pr.z(te)), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": spines + ["Tail"], "swim": True})
    MA.swim(H, spines + ["Tail"], head="Head", jaw="Jaw", pecs=pecs, mode=P["mode"], period=P["period"], amp=P["amp"],
            length=L, attack=P["attack"], extra=ctx.get("motion_extra"))
    return H


# ================================================================================================ species
def _bands(*specs):
    """White vertical bands (clownfish / convict): specs (t_centre, half width)."""
    out = []
    for tc, hw in specs:
        def reg(pr, L, tc=tc, hw=hw):
            return S.SDF(lambda Q: np.abs(Q[:, 2] - pr.z(tc) - 0.03 * L * np.sin(Q[:, 1] * 2.2 / L * 6)) - hw * L)
        out.append((tc - hw - 0.04, tc + hw + 0.04, reg, "secondary"))
    return out


def _belly(t1, t2, frac=0.15, col="belly", wav=0.0, taper=0.0):
    def reg(pr, L):
        ts = np.linspace(0, 1, 40)
        cs = np.array([pr.at(t)[3] - frac * pr.at(t)[4] - (1.3 * pr.at(t)[4] * np.clip((t - (t2 - taper)) / max(taper, 1e-6), 0, 1) ** 1.5 if taper else 0.0)
                       for t in ts])

        def f(Q):
            tt = np.clip((Q[:, 2] - pr.z0) / L, 0, 1)
            cy = np.interp(tt, ts, cs) + wav * L * np.sin(Q[:, 2] / L * 25)
            return Q[:, 1] - cy
        return S.SDF(f)
    return (t1, t2, reg, col)


PERCH = [(0, 0.02, -0.03, 0.012), (0.05, 0.085, -0.07, 0.04), (0.15, 0.155, -0.12, 0.068), (0.3, 0.195, -0.148, 0.085),
         (0.45, 0.185, -0.145, 0.08), (0.65, 0.125, -0.1, 0.058), (0.82, 0.07, -0.058, 0.034), (0.93, 0.052, -0.046, 0.024), (1.0, 0.06, -0.055, 0.02)]


def _spiny(t1, t2, h, n=9):
    """Spiny dorsal edge: zigzag spine tips."""
    pts = []
    for i in range(n + 1):
        f = i / n
        t = t1 + (t2 - t1) * f
        hh = h * (0.55 + 0.45 * math.sin(math.pi * min(1, f * 1.4))) * (1 - 0.35 * f)
        pts.append((t + 0.012, hh))
        if i < n:
            pts.append((t + (t2 - t1) / n * 0.6, hh * 0.72))
    return pts


@hero("fish", FAM)
def fish():
    return _fish("fish", prof=PERCH, mouth=(0.05, 0, 0.09, 0.0, 0.45),
                 fins=[dict(kind="dorsal", name="Dorsal1", t=(0.3, 0.55), edge=_spiny(0.3, 0.55, 0.13)),
                       dict(kind="dorsal", name="Dorsal2", t=(0.57, 0.8), edge=[(0.57, 0.06), (0.62, 0.1), (0.72, 0.085), (0.8, 0.05), (0.84, 0.01)]),
                       dict(kind="anal", name="Anal", t=(0.6, 0.8), edge=[(0.6, 0.05), (0.66, 0.085), (0.76, 0.07), (0.82, 0.02)])],
                 caudal=("forked", 0.2, 0.2), pattern=lambda pr, L: stripes(lambda Q: Q[:, 2] / L, 7.0, width=0.3, depth=0.25, wobble=0.02),
                 overlays=[_belly(0.0, 0.9, 0.2, "secondary")], fin_tr=0.1, preview=pv("fish", iris="#E8C04A"))


# ------------------------------------------------------------------------------------------------ species helpers
def edge_dark(thr, depth=0.7):
    """Fin pattern: darken the outer rim (beyond thr * L from the body surface)."""
    def mk(pr, L):
        ts = np.linspace(-0.2, 1.4, 60)
        cs = np.array([pr.at(t)[3] for t in ts])
        as_ = np.array([pr.at(t)[4] for t in ts])

        def f(Q):
            tt = (Q[:, 2] - pr.z0) / L
            c = np.interp(tt, ts, cs)
            a = np.interp(tt, ts, as_)
            ext = np.maximum(np.abs(Q[:, 1] - c) - a, (tt - 1.0) * L)
            return 1 - depth * np.clip((ext - thr * L) / (0.015 * L), 0, 1)
        return f
    return mk


def patches(specs, col="secondary"):
    """Koi-style patches: specs (t, angle deg, radius L, squash) ellipsoid blobs on the body surface."""
    def reg(pr, L):
        sh = []
        for t, ang, r, sq in specs:
            p = pr.surface(t, ang)
            sh.append(S.ellipsoid(r * L * 0.8, r * L * sq, r * L, p))
        return MA.union_all(sh).noise(0.01 * L, 3.0 / L, 4)
    t1 = min(s[0] - s[2] for s in specs) - 0.02
    t2 = max(s[0] + s[2] for s in specs) + 0.02
    return (t1, t2, reg, col)


def barbels(specs, col="primary"):
    """specs: (t, ang, bone 'Head'/'Jaw', direction (dx, dy, dz), length L, radius L). Each a curved whisker."""
    def ex(H, ctx):
        pr, L = ctx["pr"], ctx["L"]
        for bone in ("Head", "Jaw"):
            parts = []
            for t, ang, b, d, ln, r in specs:
                if b != bone:
                    continue
                p0 = np.array(pr.surface(t, ang)) * 1.0
                p0[0] *= 0.9
                d = np.array(d, float)
                d /= np.linalg.norm(d)
                p1 = p0 + d * ln * L * 0.5
                p2 = p1 + (d + np.array((0, -0.6, 0.4))) / 1.4 * ln * L * 0.5
                for sx in (1, -1):
                    m = np.array((sx, 1, 1))
                    parts.append(S.tube([tuple(p0 * m), tuple(p1 * m), tuple(p2 * m)], [r * L, r * L * 0.7, r * L * 0.3], k=0.01 * L))
            if parts:
                H.piece("Barbels" + bone[0], bone, MA.union_all(parts), col=col, tris=500, role="whisker", pri=2.0, res=150, smooth=2)
    return ex


def chain(*fns):
    def ex(H, ctx):
        for f in fns:
            if f:
                f(H, ctx)
    return ex


def spines_sculpt(n=90, ln=0.07, r=0.012, t_rng=(0.06, 0.82)):
    def sc(body, pr):
        L = pr.L
        cones = []
        g = (1 + 5 ** 0.5) / 2
        for i in range(n):
            f = (i + 0.5) / n
            t = t_rng[0] + (t_rng[1] - t_rng[0]) * f
            ang = (i * 360 / g) % 360
            tp, bt, w, c, a = pr.at(t)
            th = math.radians(ang)
            p = np.array((w * math.cos(th), c + a * math.sin(th), pr.z(t)))
            nrm = np.array((math.cos(th) / w, math.sin(th) / a, -0.15 / L))
            nrm /= np.linalg.norm(nrm)
            nrm = nrm + np.array((0, 0, 0.35))
            nrm /= np.linalg.norm(nrm)
            cones.append(S.round_cone(tuple(p - nrm * 0.01 * L), tuple(p + nrm * ln * L), r * L, 0.002 * L))
        return body.su(MA.union_all(cones), 0.008 * L)
    return sc


def finlets(t1, t2, n=6, h=0.035, col="gold"):
    def ex(H, ctx):
        pr, L, fth = ctx["pr"], ctx["L"], ctx["fth"]
        for top in (True, False):
            ps = []
            for i in range(n):
                t = t1 + (t2 - t1) * i / max(n - 1, 1)
                tp, bt, w, c, a = pr.at(t)
                y = tp - 0.3 * a if top else bt + 0.3 * a
                sg = 1 if top else -1
                z = pr.z(t)
                pts = [(z - 0.012 * L, y), (z + 0.03 * L, y + sg * h * L * 1.4), (z + 0.03 * L, y + sg * h * L * 0.8), (z + 0.018 * L, y)]
                if not top:
                    pts = pts[::-1]
                ps.append(plate((0, 0, 0), (0, 0, 1), (0, 1, 0), pts, fth * 0.9, taper=0.5, edge=0.01 * L))
            H.piece("Finlets" + ("T" if top else "B"), ctx["bone_at"]((t1 + t2) / 2), MA.union_all(ps), col=col, mat="skin", tris=400, role="fin", pri=1.8, res=150, smooth=2)
    return ex


def bill(length, r, flat=1.0, col="primary"):
    def ex(H, ctx):
        pr, L, z0 = ctx["pr"], ctx["L"], ctx["z0"]
        tp, bt, w, c, a = pr.at(0.04)
        y = c + 0.25 * a
        b = S.round_cone((0, 0, 0), (0, 0, -length * L), r * L, 0.004 * L).scale3(flat, 1.0, 1.0).at(0, y, z0 + 0.06 * L)
        H.piece("Bill", "Head", b, col=col, mat="hard", tris=500, role="horn", pri=1.5, res=150, smooth=3)
    return ex


def lure(H, ctx):
    pr, L, z0 = ctx["pr"], ctx["L"], ctx["z0"]
    tp, bt, w, c, a = pr.at(0.1)
    base = np.array((0, tp - 0.01 * L, pr.z(0.1)))
    mid = base + np.array((0, 0.16 * L, -0.06 * L))
    tip = mid + np.array((0, 0.02 * L, -0.15 * L))
    H.bone("Lure1", "Head", tuple(base))
    H.bone("Lure2", "Lure1", tuple(mid))
    H.piece("LureA", "Lure1", S.tube([tuple(base), tuple(base + (mid - base) * 0.6), tuple(mid)], [0.018 * L, 0.014 * L, 0.012 * L], k=0.01 * L), col="primary", tris=300, role="lure", pri=1.8)
    H.piece("LureB", "Lure2", S.tube([tuple(mid), tuple(mid + (tip - mid) * 0.5 + np.array((0, 0.03 * L, 0))), tuple(tip)], [0.012 * L, 0.01 * L, 0.009 * L], k=0.01 * L)
            .su(S.sphere(0.03 * L, tuple(tip + np.array((0, -0.02 * L, 0)))), 0.01 * L), col="primary", tris=350, role="lure", pri=1.8)
    H.prim("Esca", "Lure2", "Ball", (0.05 * L,) * 3, tuple(tip + np.array((0, -0.035 * L, 0))), col="secondary", mat="hard", glow=True, role="light", pri=2.5)

    def mx(pose, kind, u, s):
        sw = math.sin(MA.TAU * u)
        MA._add(pose, "Lure1", (0, 0, 0, 0.12 * sw, 0.1 * math.cos(MA.TAU * u), 0))
        MA._add(pose, "Lure2", (0, 0, 0, 0.25 * math.sin(MA.TAU * u - 0.8), 0.2 * math.sin(MA.TAU * u * 2), 0))
    ctx["motion_extra"] = mx


def fringe(H, ctx):
    pass


def _fins_std(d1, d2=None, an=None, adip=None):
    f = []
    if d1:
        f.append(dict(kind="dorsal", name="Dorsal", **d1))
    if d2:
        f.append(dict(kind="dorsal", name="Dorsal2", **d2))
    if an:
        f.append(dict(kind="anal", name="Anal", **an))
    if adip:
        f.append(dict(kind="adipose", name="Adipose", th=1.6, **adip))
    return f


# ================================================================================================ more species
def _bass_like(hid, prev, **kw):
    prof = [(0, 0.035, -0.045, 0.02), (0.05, 0.09, -0.08, 0.05), (0.15, 0.14, -0.13, 0.075), (0.3, 0.175, -0.15, 0.09),
            (0.48, 0.17, -0.145, 0.085), (0.68, 0.115, -0.095, 0.06), (0.84, 0.065, -0.055, 0.033), (0.94, 0.05, -0.045, 0.024), (1.0, 0.058, -0.052, 0.02)]
    d = dict(prof=prof, mouth=(0.1, 0, 0.17, -0.12, 0.42), eye=(0.12, 35, 0.04),
             fins=_fins_std(dict(t=(0.3, 0.52), edge=_spiny(0.3, 0.52, 0.12)),
                            dict(t=(0.53, 0.78), edge=[(0.53, 0.07), (0.58, 0.11), (0.7, 0.1), (0.78, 0.06), (0.82, 0.01)]),
                            dict(t=(0.62, 0.8), edge=[(0.62, 0.05), (0.67, 0.09), (0.77, 0.07), (0.83, 0.02)])),
             caudal=("square", 0.19, 0.19), overlays=[_belly(0.0, 0.95, 0.25, "secondary")],
             pattern=lambda pr, L: spots(0.06 * L, 0.03 * L, depth=0.45, region=lambda Q: np.clip((np.abs(Q[:, 1] - pr.y0 - 0.0 * L) < 0.05 * L) * 1.0, 0, 1)),
             fin_tr=0.08, preview=prev)
    d.update(kw)
    return _fish(hid, **d)


@hero("bass", FAM)
def bass():
    return _bass_like("bass", pv("bass", iris="#C8A030"))


@hero("goldfish", FAM)
def goldfish():
    prof = [(0, 0.035, -0.04, 0.03), (0.06, 0.13, -0.11, 0.08), (0.2, 0.24, -0.2, 0.135), (0.4, 0.255, -0.215, 0.14), (0.6, 0.18, -0.15, 0.1),
            (0.8, 0.09, -0.075, 0.05), (0.92, 0.06, -0.05, 0.03), (1.0, 0.065, -0.055, 0.025)]
    return _fish("goldfish", prof=prof, lift=0.9, mouth=(0.05, 0, 0.07, 0.0, 0.4), eye=(0.12, 30, 0.055), seg=(0.3, 0.52, 0.7, 0.86),
                 fins=_fins_std(dict(t=(0.3, 0.68), edge=[(0.3, 0.06), (0.36, 0.2), (0.48, 0.24), (0.62, 0.2), (0.72, 0.12), (0.75, 0.03)], tr=0.2),
                                None, dict(t=(0.66, 0.82), edge=[(0.66, 0.06), (0.74, 0.17), (0.84, 0.2), (0.88, 0.14), (0.86, 0.02)])),
                 caudal=("veil", 0.4, 0.55), fin_tr=0.25, scales=0.18, amp=0.26, period=1.1,
                 pecs=dict(t=0.3, ang=-35, len=0.2, wid=0.1, splay=40, droop=20, roll=-30),
                 pelvic=dict(t=0.42, ang=-80, len=0.2, wid=0.07, splay=20, droop=50, roll=10),
                 overlays=[_belly(0.0, 0.8, 0.35, "secondary")], back=0.85,
                 preview=pv("goldfish", iris="#2A2A2A", eyeWhite="#FFFFFF"))


@hero("koi", FAM)
def koi():
    prof = [(0, 0.03, -0.035, 0.03), (0.06, 0.09, -0.075, 0.06), (0.2, 0.145, -0.115, 0.09), (0.4, 0.155, -0.12, 0.09), (0.65, 0.11, -0.085, 0.062),
            (0.85, 0.062, -0.048, 0.034), (1.0, 0.055, -0.05, 0.022)]
    return _fish("koi", prof=prof, L=7.0, mouth=(-0.2, 0, 0.07, 0.0, 0.4), eye=(0.1, 25, 0.035),
                 fins=_fins_std(dict(t=(0.38, 0.75), edge=[(0.38, 0.07), (0.42, 0.13), (0.55, 0.1), (0.75, 0.06), (0.78, 0.01)], tr=0.15),
                                None, dict(t=(0.7, 0.82), edge=[(0.7, 0.05), (0.75, 0.08), (0.85, 0.05), (0.86, 0.01)])),
                 caudal=("veil", 0.26, 0.3), fin_tr=0.2, scales=0.14, back=0.95, amp=0.3, period=1.2,
                 pecs=dict(t=0.24, ang=-40, len=0.17, wid=0.09, splay=40, droop=20, roll=-30),
                 pelvic=dict(t=0.45, ang=-80, len=0.11, wid=0.05, splay=20, droop=45, roll=10),
                 overlays=[patches([(0.08, 80, 0.07, 0.7), (0.3, 70, 0.11, 0.9), (0.55, 50, 0.09, 0.8), (0.47, 110, 0.07, 0.8), (0.8, 85, 0.06, 0.9)])],
                 extra=barbels([(0.02, -20, "Head", (1, -0.3, 0.2), 0.06, 0.006), (0.05, -40, "Head", (1, -0.6, 0.6), 0.035, 0.005)], col="secondary"),
                 preview=pv("koi", iris="#2A2A2A"))


@hero("angelfish", FAM)
def angelfish():
    prof = [(0, 0.03, -0.03, 0.015), (0.1, 0.17, -0.15, 0.04), (0.3, 0.29, -0.26, 0.052), (0.5, 0.26, -0.23, 0.047), (0.75, 0.13, -0.11, 0.03),
            (0.92, 0.065, -0.06, 0.018), (1.0, 0.06, -0.06, 0.014)]
    return _fish("angelfish", prof=prof, L=5.0, lift=3.0, mouth=(0.05, 0, 0.06, 0.0, 0.4), eye=(0.13, 25, 0.05), seg=(0.3, 0.5, 0.68, 0.85),
                 fins=_fins_std(dict(t=(0.28, 0.85), edge=[(0.28, 0.04), (0.45, 0.2), (0.65, 0.45), (0.82, 0.62), (0.9, 0.6), (0.92, 0.3), (0.95, 0.04)], tr=0.15, ray=0.03),
                                None, dict(t=(0.4, 0.88), edge=[(0.4, 0.04), (0.55, 0.22), (0.75, 0.48), (0.88, 0.62), (0.94, 0.58), (0.94, 0.3), (0.96, 0.04)], ray=0.03)),
                 caudal=("square", 0.22, 0.28), caudal_col="primary", fin_tr=0.15, fin_th=0.01, amp=0.2, period=1.3, back=0.9,
                 pecs=dict(t=0.3, ang=-25, len=0.14, wid=0.07, splay=35, droop=15, roll=-35),
                 pelvic=dict(t=0.25, ang=-85, len=0.55, wid=0.035, splay=8, droop=60, roll=5, rootw=0.9, tipk=0.6, tris=400),
                 pattern=lambda pr, L: stripes(lambda Q: Q[:, 2] / L + 0.08 * (Q[:, 1] - pr.y0) / L, 3.3, width=0.22, depth=0.6, wobble=0.0),
                 preview=pv("angelfish", iris="#C83020"))


@hero("discus fish", FAM)
def discus():
    prof = [(0, 0.04, -0.04, 0.015), (0.08, 0.2, -0.19, 0.045), (0.3, 0.32, -0.31, 0.06), (0.55, 0.31, -0.3, 0.056), (0.8, 0.2, -0.19, 0.036),
            (0.95, 0.085, -0.08, 0.02), (1.0, 0.065, -0.062, 0.016)]
    wavy = lambda pr, L: stripes(lambda Q: (Q[:, 1] - pr.y0) / L + 0.02 * np.sin(Q[:, 2] / L * 30), 14.0, width=0.3, depth=0.35, wobble=0.0)
    return _fish("discus fish", prof=prof, L=5.0, mouth=(0.0, 0, 0.05, 0.0, 0.4), eye=(0.12, 22, 0.045), seg=(0.3, 0.52, 0.7, 0.88),
                 fins=_fins_std(dict(t=(0.25, 0.95), edge=[(0.25, 0.02), (0.4, 0.06), (0.7, 0.09), (0.92, 0.1), (1.0, 0.03)], ray=0.02, tr=0.1),
                                None, dict(t=(0.3, 0.95), edge=[(0.3, 0.02), (0.45, 0.06), (0.75, 0.09), (0.94, 0.09), (1.0, 0.03)], ray=0.02)),
                 caudal=("round", 0.14, 0.17), fin_tr=0.15, fin_th=0.01, amp=0.18, period=1.3, pattern=wavy, back=0.95, scales=0.0,
                 fin_col="secondary", caudal_col="primary",
                 pecs=dict(t=0.33, ang=-15, len=0.12, wid=0.07, splay=35, droop=10, roll=-35),
                 pelvic=dict(t=0.3, ang=-85, len=0.16, wid=0.03, splay=8, droop=55, roll=5, tipk=0.5),
                 preview=pv("discus fish", iris="#D02A20"))


@hero("clownfish", FAM)
def clownfish():
    prof = [(0, 0.045, -0.045, 0.035), (0.07, 0.125, -0.105, 0.08), (0.25, 0.2, -0.17, 0.11), (0.5, 0.19, -0.16, 0.1), (0.75, 0.12, -0.1, 0.065),
            (0.9, 0.072, -0.062, 0.04), (1.0, 0.068, -0.062, 0.03)]
    ed = edge_dark(0.06)
    return _fish("clownfish", prof=prof, L=4.5, mouth=(0.0, 0, 0.07, 0.0, 0.4), eye=(0.13, 25, 0.05), seg=(0.32, 0.5, 0.7, 0.86),
                 fins=[dict(kind="dorsal", name="Dorsal", t=(0.3, 0.52), edge=_spiny(0.3, 0.52, 0.1, 6), edgecol=edge_dark(0.04)),
                       dict(kind="dorsal", name="Dorsal2", t=(0.53, 0.82), edge=[(0.53, 0.08), (0.6, 0.15), (0.72, 0.15), (0.82, 0.08), (0.85, 0.01)], edgecol=edge_dark(0.08)),
                       dict(kind="anal", name="Anal", t=(0.62, 0.82), edge=[(0.62, 0.06), (0.68, 0.13), (0.78, 0.12), (0.84, 0.02)], edgecol=edge_dark(0.07))],
                 caudal=("round", 0.17, 0.2), caudal_pat=lambda pr, L: (lambda Q: 1 - 0.75 * np.clip((Q[:, 2] - pr.z(1.0) - 0.15 * L) / (0.02 * L), 0, 1)),
                 overlays=_bands((0.2, 0.035), (0.5, 0.045), (0.92, 0.025)), scales=0.05, back=0.92, amp=0.3, period=0.7,
                 pecs=dict(t=0.33, ang=-20, len=0.15, wid=0.1, splay=40, droop=15, roll=-35),
                 pelvic=dict(t=0.36, ang=-80, len=0.11, wid=0.05, splay=20, droop=40, roll=10, col="primary"),
                 preview=pv("clownfish", iris="#2A1A10"))


@hero("blue tang", FAM)
def blue_tang():
    prof = [(0, 0.03, -0.035, 0.02), (0.08, 0.15, -0.13, 0.05), (0.3, 0.25, -0.22, 0.065), (0.55, 0.24, -0.2, 0.06), (0.8, 0.13, -0.1, 0.04),
            (0.94, 0.065, -0.055, 0.022), (1.0, 0.06, -0.055, 0.018)]
    mark = lambda pr, L: (lambda Q: 1 - 0.75 * np.clip(1 - np.abs((Q[:, 1] - pr.y0) / L - 0.12 + 0.35 * ((Q[:, 2] - pr.z(0.55)) / L) ** 2) / 0.035, 0, 1)
                          * ((Q[:, 2] > pr.z(0.2)) & (Q[:, 2] < pr.z(0.95))))
    return _fish("blue tang", prof=prof, L=5.0, mouth=(0.0, 0, 0.05, 0.0, 0.4), eye=(0.12, 30, 0.045),
                 fins=_fins_std(dict(t=(0.18, 0.92), edge=[(0.18, 0.03), (0.3, 0.07), (0.6, 0.08), (0.88, 0.08), (0.96, 0.02)], ray=0.022, edgecol=edge_dark(0.04, 0.8)),
                                None, dict(t=(0.45, 0.92), edge=[(0.45, 0.03), (0.55, 0.07), (0.85, 0.07), (0.96, 0.02)], ray=0.022, edgecol=edge_dark(0.04, 0.8))),
                 caudal=("square", 0.2, 0.2), caudal_col="secondary", pattern=mark, scales=0.0, back=0.9, amp=0.25,
                 pecs=dict(t=0.3, ang=-10, len=0.15, wid=0.08, splay=35, droop=10, roll=-35, col="secondary"),
                 pelvic=dict(t=0.3, ang=-85, len=0.09, wid=0.04, splay=15, droop=45, roll=5),
                 preview=pv("blue tang", iris="#1A1A1A"))


@hero("betta fish", FAM)
def betta():
    prof = [(0, 0.03, -0.035, 0.025), (0.06, 0.08, -0.07, 0.05), (0.2, 0.12, -0.11, 0.065), (0.42, 0.125, -0.115, 0.062), (0.7, 0.09, -0.08, 0.045),
            (0.88, 0.06, -0.055, 0.03), (1.0, 0.06, -0.06, 0.022)]
    return _fish("betta fish", prof=prof, L=4.5, lift=2.2, mouth=(0.25, 0, 0.06, 0.1, 0.4), eye=(0.12, 25, 0.045), seg=(0.3, 0.5, 0.68, 0.84),
                 fins=_fins_std(dict(t=(0.5, 0.88), edge=[(0.5, 0.05), (0.62, 0.22), (0.85, 0.32), (1.05, 0.3), (1.0, 0.1), (0.95, 0.02)], tr=0.15, ray=0.02),
                                None, dict(t=(0.35, 0.95), edge=[(0.35, 0.05), (0.5, 0.3), (0.75, 0.42), (1.0, 0.46), (1.08, 0.3), (1.0, 0.04)], ray=0.02)),
                 caudal=("fan", 0.42, 0.5), fin_tr=0.18, fin_th=0.009, amp=0.22, period=1.4, back=0.85, scales=0.12,
                 pecs=dict(t=0.27, ang=-20, len=0.12, wid=0.07, splay=40, droop=15, roll=-35),
                 pelvic=dict(t=0.32, ang=-85, len=0.3, wid=0.05, splay=10, droop=55, roll=5, tipk=0.4),
                 caudal_pat=edge_dark(0.4, 0.0), preview=pv("betta fish", iris="#1A1A1A"))


def _salmonid(hid, prev, trout=False):
    prof = [(0, 0.025, -0.032, 0.02), (0.06, 0.075, -0.065, 0.045), (0.2, 0.13, -0.11, 0.072), (0.4, 0.14, -0.115, 0.076), (0.65, 0.1, -0.08, 0.054),
            (0.85, 0.055, -0.045, 0.03), (1.0, 0.052, -0.047, 0.02)]
    over = [_belly(0.0, 0.98, 0.3, "belly")]
    if trout:
        over = [(0.18, 0.98, lambda pr, L: S.SDF(lambda Q: np.abs(Q[:, 1] - pr.y0 + 0.005 * L) - 0.028 * L), "secondary")]
    return _fish(hid, prof=prof, L=6.5, mouth=(-0.05, 0, 0.11, -0.05, 0.42), eye=(0.1, 30, 0.035), teeth=0,
                 fins=_fins_std(dict(t=(0.38, 0.53), edge=[(0.38, 0.06), (0.41, 0.13), (0.5, 0.1), (0.56, 0.03)]), None,
                                dict(t=(0.7, 0.8), edge=[(0.7, 0.05), (0.72, 0.09), (0.8, 0.05), (0.83, 0.01)]),
                                dict(t=(0.76, 0.82), edge=[(0.76, 0.02), (0.79, 0.04), (0.84, 0.02), (0.84, 0.005)])),
                 caudal=("square", 0.18, 0.18), fin_tr=0.05, scales=0.08, back=0.6,
                 pattern=lambda pr, L: spots(0.035 * L, 0.009 * L, depth=0.8, region=lambda Q: np.clip((Q[:, 1] - pr.y0 + (0.05 if trout else -0.02) * L) / (0.03 * L), 0, 1), seed=3),
                 pecs=dict(t=0.25, ang=-50, len=0.12, wid=0.05, splay=30, droop=25, roll=-40),
                 pelvic=dict(t=0.52, ang=-80, len=0.09, wid=0.04, splay=15, droop=40, roll=10),
                 overlays=over, attack="bite", preview=prev)


@hero("salmon", FAM)
def salmon():
    return _salmonid("salmon", pv("salmon", primary="#9AA4AE", belly="#F2E8E4", iris="#C8A050"))


@hero("trout", FAM)
def trout():
    return _salmonid("trout", pv("trout", iris="#C8A050"), trout=True)


@hero("catfish", FAM)
def catfish():
    prof = [(0, 0.02, -0.03, 0.06), (0.06, 0.065, -0.07, 0.105), (0.2, 0.1, -0.1, 0.11), (0.35, 0.12, -0.1, 0.095), (0.6, 0.1, -0.08, 0.062),
            (0.85, 0.06, -0.05, 0.034), (1.0, 0.052, -0.05, 0.02)]
    return _fish("catfish", prof=prof, L=7.0, square=0.25, mouth=(-0.1, 0, 0.09, 0.0, 0.4), eye=(0.12, 40, 0.022),
                 fins=_fins_std(dict(t=(0.3, 0.4), edge=[(0.3, 0.05), (0.31, 0.12), (0.38, 0.08), (0.42, 0.02)]), None,
                                dict(t=(0.55, 0.95), edge=[(0.55, 0.03), (0.6, 0.06), (0.9, 0.06), (0.97, 0.02)], ray=0.018),
                                dict(t=(0.62, 0.85), edge=[(0.62, 0.02), (0.68, 0.04), (0.84, 0.035), (0.88, 0.005)])),
                 caudal=("round", 0.14, 0.17), scales=0.0, back=0.7, amp=0.3, period=1.2,
                 pecs=dict(t=0.24, ang=-40, len=0.13, wid=0.06, splay=50, droop=20, roll=-55),
                 pelvic=dict(t=0.5, ang=-75, len=0.09, wid=0.04, splay=20, droop=35, roll=10),
                 overlays=[_belly(0.0, 0.7, 0.2, "secondary")],
                 extra=barbels([(0.03, 5, "Head", (1, -0.05, 0.3), 0.32, 0.009), (0.025, -60, "Jaw", (0.6, -0.8, -0.1), 0.1, 0.006),
                                (0.04, -80, "Jaw", (0.3, -0.9, 0.1), 0.08, 0.005)], col="primary"),
                 preview=pv("catfish", iris="#C8B050"))


@hero("piranha", FAM)
def piranha():
    prof = [(0, 0.0, -0.075, 0.035), (0.06, 0.11, -0.14, 0.065), (0.2, 0.2, -0.22, 0.085), (0.4, 0.2, -0.21, 0.08), (0.65, 0.12, -0.12, 0.055),
            (0.85, 0.062, -0.06, 0.03), (1.0, 0.058, -0.058, 0.022)]
    chin = lambda b, pr: b.su(S.ellipsoid(0.05 * pr.L, 0.045 * pr.L, 0.06 * pr.L, (0, pr.at(0.04)[1] + 0.035 * pr.L, pr.z(0.04))), 0.02 * pr.L)
    return _fish("piranha", prof=prof, L=4.5, sculpt=chin, mouth=(-0.35, 0, 0.12, 0.05, 0.45), eye=(0.15, 25, 0.04), teeth=5, tooth_len=0.03,
                 fins=_fins_std(dict(t=(0.45, 0.6), edge=[(0.45, 0.06), (0.5, 0.13), (0.6, 0.09), (0.63, 0.02)]), None,
                                dict(t=(0.6, 0.86), edge=[(0.6, 0.04), (0.65, 0.1), (0.8, 0.09), (0.88, 0.02)]),
                                dict(t=(0.8, 0.86), edge=[(0.8, 0.02), (0.83, 0.04), (0.88, 0.01)])),
                 caudal=("forked", 0.19, 0.18), caudal_pat=edge_dark(0.15, 0.6), scales=0.15, back=0.7,
                 pattern=lambda pr, L: spots(0.03 * L, 0.008 * L, depth=0.35, seed=9),
                 pecs=dict(t=0.3, ang=-50, len=0.11, wid=0.05, splay=30, droop=20, roll=-40, col="secondary"),
                 pelvic=dict(t=0.42, ang=-80, len=0.08, wid=0.04, splay=15, droop=40, roll=10, col="secondary"),
                 overlays=[_belly(0.04, 0.6, 0.3, "secondary")], amp=0.32, period=0.6,
                 preview=pv("piranha", iris="#C8282A"))


@hero("barracuda", FAM)
def barracuda():
    prof = [(0, 0.012, -0.022, 0.012), (0.08, 0.05, -0.05, 0.038), (0.2, 0.075, -0.075, 0.053), (0.45, 0.08, -0.075, 0.054), (0.7, 0.06, -0.055, 0.04),
            (0.88, 0.036, -0.032, 0.022), (1.0, 0.036, -0.033, 0.016)]
    return _fish("barracuda", prof=prof, L=8.0, mouth=(-0.1, 0, 0.13, -0.03, 0.5), eye=(0.11, 30, 0.022), teeth=7, tooth_len=0.016,
                 seg=(0.27, 0.48, 0.68, 0.85),
                 fins=_fins_std(dict(t=(0.38, 0.46), edge=[(0.38, 0.03), (0.4, 0.07), (0.46, 0.04), (0.49, 0.01)]),
                                dict(t=(0.68, 0.76), edge=[(0.68, 0.03), (0.7, 0.06), (0.77, 0.04), (0.8, 0.01)]),
                                dict(t=(0.7, 0.78), edge=[(0.7, 0.03), (0.72, 0.06), (0.79, 0.04), (0.82, 0.01)])),
                 caudal=("forked", 0.13, 0.16), caudal_col="secondary", scales=0.08, back=0.6,
                 pattern=lambda pr, L: stripes(lambda Q: Q[:, 2] / L, 14, width=0.25, depth=0.35, region=lambda Q: np.clip((Q[:, 1] - pr.y0) / (0.02 * L), 0, 1)),
                 pecs=dict(t=0.24, ang=-30, len=0.08, wid=0.035, splay=30, droop=20, roll=-35),
                 pelvic=dict(t=0.42, ang=-80, len=0.06, wid=0.03, splay=15, droop=40, roll=10),
                 amp=0.32, period=0.8, preview=pv("barracuda", iris="#D0D040"))


@hero("tuna", FAM)
def tuna():
    prof = [(0, 0.02, -0.025, 0.02), (0.08, 0.09, -0.085, 0.07), (0.3, 0.16, -0.15, 0.12), (0.5, 0.155, -0.14, 0.115), (0.75, 0.08, -0.075, 0.06),
            (0.92, 0.03, -0.028, 0.025), (1.0, 0.026, -0.024, 0.024)]
    return _fish("tuna", prof=prof, L=7.0, mouth=(-0.05, 0, 0.08, 0.0, 0.4), eye=(0.11, 25, 0.03), seg=(0.28, 0.52, 0.7, 0.84),
                 fins=_fins_std(dict(t=(0.3, 0.45), edge=_spiny(0.3, 0.45, 0.08, 6)),
                                dict(t=(0.55, 0.64), edge=[(0.55, 0.05), (0.6, 0.18), (0.62, 0.17), (0.64, 0.04)], col="gold"),
                                dict(t=(0.58, 0.67), edge=[(0.58, 0.05), (0.63, 0.18), (0.65, 0.17), (0.67, 0.04)], col="gold")),
                 caudal=("lunate", 0.3, 0.2), scales=0.0, back=0.75,
                 pecs=dict(t=0.27, ang=10, len=0.2, wid=0.05, splay=25, droop=15, roll=-60, tipk=0.5),
                 pelvic=dict(t=0.33, ang=-80, len=0.06, wid=0.03, splay=15, droop=40, roll=10),
                 overlays=[_belly(0.0, 0.98, 0.0, "secondary")], extra=finlets(0.72, 0.94),
                 amp=0.18, period=0.6, attack="ram", preview=pv("tuna", gold="#E8C030", iris="#202020"))


def _billfish(hid, prev, sail=False):
    prof = [(0, 0.02, -0.025, 0.02), (0.08, 0.075, -0.07, 0.05), (0.3, 0.12, -0.115, 0.075), (0.5, 0.115, -0.105, 0.07), (0.75, 0.065, -0.06, 0.042),
            (0.92, 0.03, -0.028, 0.022), (1.0, 0.026, -0.024, 0.02)]
    if sail:
        d1 = dict(t=(0.18, 0.62), edge=[(0.18, 0.1), (0.24, 0.35), (0.34, 0.4), (0.46, 0.35), (0.58, 0.2), (0.64, 0.03)], ray=0.022, tr=0.1, col="secondary")
    else:
        d1 = dict(t=(0.18, 0.32), edge=[(0.18, 0.08), (0.2, 0.25), (0.26, 0.22), (0.33, 0.06), (0.4, 0.02)])
    return _fish(hid, prof=prof, L=7.0, mouth=(-0.2, 0, 0.07, 0.0, 0.4), eye=(0.11, 20, 0.032), seg=(0.28, 0.52, 0.7, 0.84),
                 fins=_fins_std(d1, None, dict(t=(0.66, 0.74), edge=[(0.66, 0.04), (0.68, 0.12), (0.73, 0.1), (0.76, 0.02)])),
                 caudal=("lunate", 0.32, 0.2), scales=0.0, back=0.6,
                 pecs=dict(t=0.24, ang=-30, len=0.17, wid=0.04, splay=30, droop=25, roll=-50, tipk=0.5),
                 pelvic=dict(t=0.3, ang=-85, len=0.18, wid=0.02, splay=10, droop=60, roll=5) if sail else None,
                 overlays=[_belly(0.0, 0.98, 0.05, "secondary")],
                 pattern=(lambda pr, L: stripes(lambda Q: Q[:, 2] / L, 12, width=0.2, depth=0.3)) if sail else None,
                 extra=bill(0.42 if sail else 0.5, 0.03, flat=1.0 if sail else 1.8),
                 amp=0.2, period=0.7, attack="ram", preview=prev)


@hero("swordfish", FAM)
def swordfish():
    return _billfish("swordfish", pv("swordfish", iris="#3A6AA0"))


@hero("marlin", FAM)
def marlin():
    return _billfish("marlin", pv("marlin", iris="#202020"), sail=True)


@hero("pufferfish", FAM)
def pufferfish():
    prof = [(0, 0.06, -0.06, 0.05), (0.05, 0.19, -0.19, 0.19), (0.22, 0.34, -0.33, 0.34), (0.45, 0.34, -0.33, 0.34), (0.68, 0.2, -0.2, 0.2),
            (0.85, 0.075, -0.075, 0.075), (1.0, 0.05, -0.05, 0.035)]
    return _fish("pufferfish", prof=prof, L=4.0, mouth=(0.0, 0, 0.05, 0.0, 0.5), eye=(0.13, 30, 0.06), seg=(0.3, 0.5, 0.7, 0.86),
                 sculpt=spines_sculpt(64, 0.09, 0.015, (0.07, 0.78)),
                 fins=_fins_std(dict(t=(0.78, 0.88), edge=[(0.78, 0.04), (0.82, 0.1), (0.88, 0.08), (0.9, 0.01)]), None,
                                dict(t=(0.78, 0.88), edge=[(0.78, 0.04), (0.82, 0.1), (0.88, 0.08), (0.9, 0.01)])),
                 caudal=("round", 0.12, 0.15), scales=0.0, back=0.75, gill=False, fin_tr=0.15,
                 pattern=lambda pr, L: spots(0.07 * L, 0.022 * L, depth=0.55, region=lambda Q: np.clip((Q[:, 1] - pr.y0) / (0.1 * L) + 0.5, 0, 1), seed=2),
                 pecs=dict(t=0.42, ang=0, len=0.12, wid=0.1, splay=60, droop=0, roll=-20),
                 pelvic=None, overlays=[_belly(0.03, 0.82, 0.2, "belly")], amp=0.15, period=0.9, attack="spin",
                 preview=pv("pufferfish", iris="#2A6A40", belly="#F7F2E2"))


@hero("anglerfish", FAM)
def anglerfish():
    prof = [(0, 0.1, -0.12, 0.1), (0.05, 0.22, -0.2, 0.2), (0.2, 0.28, -0.25, 0.24), (0.4, 0.25, -0.21, 0.19), (0.65, 0.13, -0.11, 0.1),
            (0.85, 0.07, -0.06, 0.05), (1.0, 0.06, -0.05, 0.03)]
    return _fish("anglerfish", prof=prof, L=5.0, mouth=(0.25, 0, 0.3, -0.15, 0.4), eye=(0.17, 55, 0.03), teeth=7, tooth_len=0.07, seg=(0.36, 0.55, 0.72, 0.87),
                 fins=_fins_std(dict(t=(0.62, 0.78), edge=[(0.62, 0.04), (0.66, 0.1), (0.78, 0.08), (0.82, 0.01)]), None,
                                dict(t=(0.66, 0.8), edge=[(0.66, 0.04), (0.7, 0.09), (0.8, 0.07), (0.84, 0.01)])),
                 caudal=("round", 0.14, 0.16), scales=0.0, back=0.8, gill=False,
                 sculpt=lambda b, pr: b.noise(0.006 * pr.L, 8.0 / pr.L, 5),
                 pecs=dict(t=0.42, ang=-30, len=0.12, wid=0.08, splay=50, droop=20, roll=-35),
                 pelvic=None, extra=lure, amp=0.22, period=1.2, preview=pv("anglerfish", iris="#D8D8C0"))


@hero("flounder", FAM)
def flounder():
    prof = [(0, 0.02, -0.012, 0.04), (0.08, 0.04, -0.022, 0.16), (0.3, 0.058, -0.03, 0.235), (0.55, 0.054, -0.03, 0.225), (0.8, 0.035, -0.02, 0.13),
            (0.92, 0.022, -0.016, 0.055), (1.0, 0.02, -0.015, 0.04)]

    def fr(body, pr):
        L = pr.L
        pts = []
        for i in range(25):
            t = 0.1 + 0.85 * i / 24
            w = pr.at(t)[2] + 0.06 * L * math.sin(math.pi * min(1, (t - 0.08) / 0.85)) ** 0.6
            pts.append((pr.z(t), w))
        pts = pts + [(z, -w) for z, w in pts[::-1]]
        y = pr.y0 - 0.005 * L
        fin = plate((0, y, 0), (0, 0, 1), (1, 0, 0), pts, 0.012 * L, taper=0.4, edge=0.04 * L)
        return body.su(fin, 0.02 * L)
    return _fish("flounder", prof=prof, L=5.5, sculpt=fr, mouth=(0.0, 0, 0.05, 0.0, 0.5), eye=(0.1, 65, 0.035), eye_look=(0.3, 1.0, -0.3),
                 fins=(), caudal=("round", 0.14, 0.15), caudal_plane="h", mode="pitch", scales=0.0, back=1.0, gill=False, lift=0.15,
                 pattern=lambda pr, L: spots(0.06 * L, 0.02 * L, depth=0.4, seed=11), pecs=None, pelvic=None, amp=0.22, period=1.2,
                 preview=pv("flounder", iris="#C8C080"))


@hero("sunfish", FAM)
def sunfish():
    prof = [(0, 0.06, -0.06, 0.04), (0.1, 0.25, -0.24, 0.075), (0.35, 0.33, -0.32, 0.095), (0.65, 0.3, -0.29, 0.085), (0.9, 0.22, -0.21, 0.06),
            (1.0, 0.18, -0.17, 0.045)]
    return _fish("sunfish", prof=prof, L=6.0, lift=2.6, mouth=(0.0, 0, 0.04, 0.0, 0.5), eye=(0.13, 20, 0.03), seg=(0.3, 0.5, 0.7, 0.86),
                 fins=_fins_std(dict(t=(0.62, 0.85), edge=[(0.62, 0.05), (0.75, 0.38), (0.82, 0.42), (0.88, 0.3), (0.9, 0.05)], ray=0.03, th=1.6), None,
                                dict(t=(0.62, 0.85), edge=[(0.62, 0.05), (0.75, 0.38), (0.82, 0.42), (0.88, 0.3), (0.9, 0.05)], ray=0.03, th=1.6)),
                 caudal=("round", 0.3, 0.09), scales=0.0, back=0.8, gill=False,
                 sculpt=lambda b, pr: b.noise(0.004 * pr.L, 6.0 / pr.L, 7),
                 pecs=dict(t=0.33, ang=0, len=0.09, wid=0.06, splay=40, droop=0, roll=-30), pelvic=None,
                 pattern=lambda pr, L: spots(0.08 * L, 0.03 * L, depth=0.15, seed=13), amp=0.12, period=1.6, attack="slap",
                 preview=pv("sunfish", iris="#303030"))


CRE = {"cat": ["Creature", "Machine"]}
MAP = [
    ("fish", "fish, fishes, perch, tilapia, herring, sardine, anchovy, minnow, shad, smelt, mullet, pollock, haddock, cod, snapper, "
             "cardinalfish, goby, blenny, killifish, pupfish, mosquitofish, danio, zebrafish, barb, tetra, platy, molly, swordtail, "
             "loach, icefish, archerfish, remora, mudskipper, halfbeak, flying fish, lanternfish, flashlight fish, hatchetfish, "
             "tripod fish, cave fish, elephantnose fish, jawfish, kun peng, tiktaalik, !fishman, !jelly fish, !star fish, !fishing, !shellfish", CRE),
    ("bass", "bass, sea bass, largemouth bass, grouper, zander, walleye, bluegill, crappie, sheepshead, giant trevally, bowfin, coelacanth, "
             "humphead wrasse, cichlid, oscar fish, flowerhorn, convict cichlid", CRE),
    ("goldfish", "goldfish, gold fish, fantail, oranda, guppy, garibaldi", CRE),
    ("koi", "koi, koi fish, carp, grass carp, arowana", CRE),
    ("angelfish", "angelfish, angel fish, moorish idol, batfish", CRE),
    ("discus fish", "discus, discus fish, butterflyfish, butterfly fish, opah, spadefish, pomfret", CRE),
    ("clownfish", "clownfish, clown fish, anemonefish, nemo", CRE),
    ("blue tang", "blue tang, tang, surgeonfish, damselfish, triggerfish, parrotfish, rabbitfish, mandarinfish, dragonet, wrasse, cleaner wrasse, "
                  "hawkfish, squirrelfish, filefish", CRE),
    ("betta fish", "betta, betta fish, siamese fighting fish, gourami, lionfish, lion fish", CRE),
    ("salmon", "salmon, sockeye, chinook, steelhead, arctic char, tarpon, bonefish, arapaima, leedsichthys", CRE),
    ("trout", "trout, rainbow trout, brook trout, fur-bearing trout, fur bearing trout, grayling", CRE),
    ("catfish", "catfish, cat fish, wels catfish, mekong giant catfish, electric catfish, pleco, namazu, sturgeon, paddlefish, bullhead", CRE),
    ("piranha", "piranha, piranhas, tiger fish, tigerfish, payara, wolf fish, wolffish, dunkleosteus, placoderm, xiphactinus, helicoprion", CRE),
    ("barracuda", "barracuda, pike, northern pike, muskellunge, muskie, gar, alligator gar, needlefish", CRE),
    ("tuna", "tuna, bluefin tuna, skipjack, bonito, mackerel, wahoo, amberjack, cobia, mahi-mahi, mahi mahi, kingfish, yellowtail", CRE),
    ("swordfish", "swordfish, sword fish", CRE),
    ("marlin", "marlin, sailfish, spearfish", CRE),
    ("pufferfish", "pufferfish, puffer fish, puffer, blowfish, porcupinefish, boxfish, lumpfish, cowfish, fugu, globefish", CRE),
    ("anglerfish", "anglerfish, angler fish, angler, monkfish, abyssal angler, frogfish, stonefish, scorpionfish, viperfish, fangtooth, "
                   "coffinfish, barreleye, sculpin, toadfish, stargazer fish", CRE),
    ("flounder", "flounder, halibut, sole, plaice, turbot, flatfish", CRE),
    ("sunfish", "sunfish, mola, mola mola, ocean sunfish", CRE),
]
