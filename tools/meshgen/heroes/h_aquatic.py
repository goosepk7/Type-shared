"""Aquatic family, invertebrates: octopus, squid, nautilus, jellyfish, box jellyfish, crab, fiddler crab, hermit crab,
lobster, shrimp, starfish, sea urchin.

Limbs and tentacles are tapered tube chains with ball joints (each segment starts with a round cap centred on its
pivot, the parent ends with a slightly larger cap there, so nothing gaps or z-fights when a joint bends). Crabs and
lobsters scuttle on two-segment legs and snap a movable dactyl; cephalopods and jellies jet / pulse with curling
tentacle chains (motion_aquatic.tentacles + custom pulses).
"""
import math

import numpy as np

import sdf as S
from kit import Hero, hero, stripes, spots, gradient, combine
from map import NOTFOOD
import motion_aquatic as MA
from motion_aquatic import plate, overlay, slab

FAM = "aquatic"
TAU = 2 * math.pi


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


def V(*a):
    return np.array(a, float)


def limb(H, names, parent, pivots, path, radii, col="primary", tris=400, pattern=None, mat="skin", role="limb", deco=None, flat=None,
         piece_names=None, pri=1.5, mirror=False, res=120):
    """A chain of bones at `pivots` (len n) with tube pieces following `path` (points + radii). The path must pass
    through each pivot; segment i covers the path from pivot i to pivot i+1 (the last to the path end). deco(i, sdf)
    may add detail to segment i. flat=(axis_scale_y) squashes tubes vertically about each segment's mean height."""
    path = [V(*p) for p in path]
    # locate pivots on the path
    idx = []
    for pv_ in pivots:
        d = [np.linalg.norm(p - V(*pv_)) for p in path]
        idx.append(int(np.argmin(d)))
    idx.append(len(path) - 1)
    prev = parent
    bones = []
    for i, nm in enumerate(names):
        b = (H.mbone if mirror else H.bone)(nm, prev, tuple(pivots[i]))
        bones.append(nm)
        prev = nm
    for i, nm in enumerate(names):
        a, c = idx[i], idx[i + 1]
        if c <= a:
            c = a + 1
        pts = path[a:c + 1]
        rr = list(radii[a:c + 1])
        if i < len(names) - 1:
            rr[-1] = rr[-1] * 1.07
        sh = S.tube([tuple(p) for p in pts], rr, k=0.04) if len(pts) > 1 else S.sphere(rr[0], tuple(pts[0]))
        if flat:
            ym = float(np.mean([p[1] for p in pts]))
            base = sh
            sh = S.SDF(lambda Q, base=base, ym=ym: base(np.column_stack([Q[:, 0], ym + (Q[:, 1] - ym) / flat, Q[:, 2]])) * flat)
        if deco:
            sh = deco(i, sh, pts, rr)
        pn = (piece_names[i] if piece_names else nm + "P")
        if mirror:
            H.mpiece(pn, nm, sh, col=col, tris=tris if not isinstance(tris, (list, tuple)) else tris[i], pattern=pattern, mat=mat, role=role, pri=pri, res=res)
        else:
            H.piece(pn, nm, sh, col=col, tris=tris if not isinstance(tris, (list, tuple)) else tris[i], pattern=pattern, mat=mat, role=role, pri=pri, res=res)
    return bones


def suckers(n=5, side=V(0, -1, 0), scale=0.55):
    def deco(i, sh, pts, rr):
        bumps = []
        L = len(pts)
        for k in range(n):
            f = (k + 0.5) / n
            j = f * (L - 1)
            j0 = int(j)
            j1 = min(j0 + 1, L - 1)
            fr = j - j0
            p = pts[j0] * (1 - fr) + pts[j1] * fr
            r = rr[j0] * (1 - fr) + rr[j1] * fr
            bumps.append(S.sphere(r * scale * 0.55, tuple(p + side * r * 0.72)))
        return sh.su(MA.union_all(bumps), r * 0.15)
    return deco


# ================================================================================================ octopus
@hero("octopus", FAM)
def octopus():
    H = Hero("octopus", plan="Octopus", gait="swim", tags=["octopus", "cephalopod"])
    H.preview = pv("octopus", iris="#E8C060")
    H.body((0, 2.0, 0))
    skin = combine(spots(0.35, 0.09, depth=0.25, seed=3), gradient(1, 0.3, 3.5, 0.8, 1.0))
    # mantle (the big "head" sack) on its own bone so it can breathe and sway
    H.bone("Mantle", "Body", (0, 2.5, 0.2))
    mantle = S.ellipsoid(1.15, 1.35, 1.35).rot(-28, 0, 0).at(0, 3.45, 0.85)
    mantle = mantle.su(S.ellipsoid(0.95, 0.8, 0.9, (0, 2.6, 0.3)), 0.4)
    mantle = mantle.noise(0.03, 3.0, 2)
    H.piece("MantleP", "Mantle", mantle, col="primary", tris=2400, res=128, role="body", pattern=skin)
    head = S.ellipsoid(0.95, 0.85, 0.9, (0, 1.95, -0.2))
    head = head.su(S.ellipsoid(0.3, 0.28, 0.3, (0.6, 2.4, -0.45)).mirror_x(), 0.2)  # eye bumps
    head = head.su(S.ellipsoid(1.0, 0.45, 1.0, (0, 1.35, -0.05)), 0.35)  # web / arm crown
    head = head.su(S.round_cone((0.75, 1.95, 0.3), (1.05, 1.75, 0.55), 0.17, 0.12), 0.12)  # siphon
    H.piece("HeadP", "Body", head.noise(0.02, 4.0, 5), col="primary", tris=2200, res=128, role="head", pattern=skin)
    H.eyes("Body", (0.72, 2.5, -0.55), 0.17, col="iris", pupil="round", look=(1, 0.1, -0.5))
    arms = []
    rng = np.random.default_rng(7)
    for i in range(8):
        th = math.radians(22.5 + 45 * i)
        d = V(math.sin(th), 0, -math.cos(th))
        c = V(0, 0, -0.05)
        curl = 0.8 + 0.4 * rng.uniform()
        up = 0.15 if i in (0, 7) else 0.0
        path = [c + d * 0.55 + V(0, 1.35, 0), c + d * 1.15 + V(0, 0.75, 0), c + d * 1.85 + V(0, 0.32 + up, 0), c + d * 2.6 + V(0, 0.27 + up, 0),
                c + d * (3.15 + 0.1 * curl) + V(0, 0.45 + up, 0), c + d * 3.25 + V(0, 0.9 * curl + up, 0), c + d * 2.95 + V(0, 1.15 * curl + up, 0)]
        rad = [0.36, 0.3, 0.23, 0.17, 0.12, 0.08, 0.045]
        nm = [f"Arm{i}A", f"Arm{i}B", f"Arm{i}C"]
        tang = np.cross(d, V(0, 1, 0))
        limb(H, nm, "Body", [path[0], path[2], path[4]], path, rad, tris=[500, 420, 360], pattern=skin, deco=suckers(4, V(0, -1, 0)), role="tentacle")
        arms.append((nm, (float(d[0]), float(d[2]))))
    H.socket("mouth", (0, 1.2, -0.2), "Body")
    H.socket("head", (0, 4.6, 0.9), "Mantle")
    H.rig.update({"head": "Body", "tail": ["Mantle"], "arms": [a[0] for a in arms]})

    def extra(pose, kind, u, s):
        MA._add(pose, "Mantle", (0, 0, 0, 0.06 * math.sin(TAU * u), 0, 0.04 * math.sin(TAU * u * 0.5)))
    MA.tentacles(H, arms, period=1.6, height=4.0, extra=extra)
    return H


# ================================================================================================ squid
@hero("squid", FAM)
def squid():
    H = Hero("squid", plan="Octopus", gait="swim", tags=["squid", "cephalopod"])
    H.preview = pv("squid", iris="#1A1A1A", eyeWhite="#E8E8F0")
    y = 1.8
    H.body((0, y, 0))
    skin = combine(spots(0.25, 0.06, depth=0.35, seed=8), gradient(1, y - 0.8, y + 0.8, 0.85, 1.0))
    H.bone("Mantle", "Body", (0, y, 0.4))
    m = S.tube([(0, y, 0.2), (0, y + 0.05, 1.2), (0, y + 0.1, 2.6), (0, y + 0.12, 4.0)], [0.62, 0.66, 0.5, 0.12], k=0.2)
    fin = plate((0, y + 0.1, 0), (1, 0, 0), (0, 0, 1), [(0, 2.4), (0.6, 2.9), (1.25, 3.5), (0.9, 3.8), (0.2, 4.15), (-0.2, 4.15), (-0.9, 3.8), (-1.25, 3.5), (-0.6, 2.9)], 0.1, taper=0.35, edge=0.3)
    H.piece("MantleP", "Mantle", m.su(fin, 0.12), col="primary", tris=2400, res=128, role="body", pattern=skin)
    head = S.ellipsoid(0.55, 0.5, 0.6, (0, y, -0.25)).su(S.sphere(0.36, (0.38, y + 0.08, -0.25)).mirror_x(), 0.15)
    head = head.su(S.round_cone((0, y - 0.3, 0.25), (0, y - 0.45, 0.6), 0.14, 0.1), 0.1)  # funnel
    H.piece("HeadP", "Body", head, col="primary", tris=1800, res=128, role="head", pattern=skin)
    H.eyes("Body", (0.52, y + 0.1, -0.3), 0.26, col="iris", pupil="round", look=(1, 0.05, -0.2))
    arms = []
    for i in range(8):
        a = TAU * (i + 0.5) / 8
        off = V(0.32 * math.cos(a), 0.3 * math.sin(a), 0)
        d = V(0.35 * math.cos(a), 0.3 * math.sin(a) - 0.1, -1.0)
        d /= np.linalg.norm(d)
        p0 = V(0, y, -0.65) + off
        path = [p0 + d * k for k in (0.0, 0.6, 1.2, 1.8, 2.3)]
        path[-1] = path[-1] + V(0, -0.1, 0)
        rad = [0.17, 0.14, 0.1, 0.06, 0.03]
        nm = [f"Arm{i}A", f"Arm{i}B"]
        limb(H, nm, "Body", [path[0], path[2]], path, rad, tris=[380, 300], pattern=skin, role="tentacle")
        arms.append((nm, (float(d[0]), -1.0)))
    for sx in (1, -1):
        p0 = V(sx * 0.12, y - 0.1, -0.65)
        d = V(sx * 0.12, -0.08, -1.0)
        d /= np.linalg.norm(d)
        path = [p0 + d * k for k in (0.0, 0.9, 1.8, 2.7, 3.2, 3.6)]
        rad = [0.1, 0.075, 0.06, 0.06, 0.13, 0.05]
        nm = [f"Tent{'R' if sx > 0 else 'L'}A", f"Tent{'R' if sx > 0 else 'L'}B", f"Tent{'R' if sx > 0 else 'L'}C"]
        club = lambda i, sh, pts, rr: sh.su(S.ellipsoid(0.15, 0.08, 0.35, tuple(pts[-2])), 0.06) if i == 2 else sh
        limb(H, nm, "Body", [path[0], path[2], path[3]], path, rad, tris=[300, 300, 400], pattern=skin, role="tentacle", deco=club)
        arms.append((nm, (sx * 0.12, -1.0)))
    H.socket("mouth", (0, y, -0.8), "Body")
    H.socket("head", (0, y + 0.7, -0.2), "Body")
    H.rig.update({"head": "Body", "tail": ["Mantle"]})

    def extra(pose, kind, u, s):
        MA._add(pose, "Mantle", (0, 0, 0, 0.05 * math.sin(TAU * u + 1), 0.06 * math.sin(TAU * u * 0.5), 0))
    MA.tentacles(H, arms, period=1.3, height=3.0, extra=extra)
    return H


# ================================================================================================ nautilus
@hero("nautilus", FAM)
def nautilus():
    H = Hero("nautilus", plan="Octopus", gait="swim", tags=["nautilus", "cephalopod", "shell"])
    H.preview = pv("nautilus", iris="#2A2A2A", dark="#C89070")
    c = V(0, 2.4, 0.5)
    H.body(tuple(c))
    # logarithmic spiral in the YZ plane, whorls coiling over the top, aperture facing forward
    pts, rad = [], []
    b = 0.19
    for k in range(46):
        phi = -0.2 + k * (3.0 * math.pi) / 45
        R = 0.18 * math.exp(b * phi)
        ang = phi + math.pi * 0.5
        pts.append(c + V(0, R * math.sin(-ang + math.pi), R * math.cos(-ang + math.pi)))
        rad.append(0.62 * R)
    pts = pts[::-1]
    rad = rad[::-1]
    shell = S.tube([tuple(p) for p in pts], rad, k=0.05)
    sx = 0.72
    base = shell
    shell = S.SDF(lambda Q: base(np.column_stack([Q[:, 0] / sx, Q[:, 1], Q[:, 2]])) * sx)
    ap = pts[0]
    shell = shell.ss(S.ellipsoid(rad[0] * 0.62, rad[0] * 0.88, rad[0] * 0.55, tuple(ap + V(0, 0, -0.25))), 0.08)
    ribs = lambda Q: 1 - 0.12 * (np.abs(np.sin(np.arctan2(Q[:, 1] - c[1], Q[:, 2] - c[2]) * 9)) < 0.15)
    H.piece("Shell", "Body", shell, col="primary", mat="hard", tris=2600, res=136, role="shell", pattern=ribs)

    def tiger(Q):
        a = np.arctan2(Q[:, 1] - c[1], Q[:, 2] - c[2])
        band = np.sin(a * 7 + 0.8 * np.linalg.norm(Q[:, 1:] - c[1:], axis=1)) - 0.3
        back = (Q[:, 2] - (c[2] - 0.6))
        return np.maximum(band * 0.4, -back)
    H.piece("Stripes", "Body", overlay(shell, S.SDF(tiger), t=0.03), col="secondary", mat="hard", tris=1800, res=136, role="pattern", pri=1.3)
    # head + hood in the aperture
    hc = ap + V(0, -0.05, -0.15)
    H.bone("Head", "Body", tuple(hc))
    hood = S.ellipsoid(rad[0] * 0.6, rad[0] * 0.45, rad[0] * 0.55, tuple(hc + V(0, rad[0] * 0.45, -0.15))).noise(0.02, 5.0, 1)
    body = S.ellipsoid(rad[0] * 0.5, rad[0] * 0.55, rad[0] * 0.5, tuple(hc + V(0, -0.1, -0.2)))
    H.piece("Hood", "Head", hood.su(body, 0.15), col="dark", tris=1400, role="head", pattern=spots(0.18, 0.05, 0.35, seed=4))
    H.eyes("Head", tuple(hc + V(rad[0] * 0.45, 0.05, -0.25)), 0.13, col="pupil", pupil=None, look=(1, 0, -0.3))
    arms = []
    for i in range(6):
        a = math.radians(-70 + i * 28)
        d = V(math.sin(a) * 0.6, -0.55, -1.0)
        d /= np.linalg.norm(d)
        p0 = hc + V(math.sin(a) * 0.35, -0.25, -0.35)
        nm = f"Tent{i}"
        H.bone(nm, "Head", tuple(p0))
        strands = []
        for j in range(3):
            o = V((j - 1) * 0.09, (j % 2) * 0.07, 0)
            pp = [p0 + o, p0 + o + d * 0.6 + V(0, 0.05, 0), p0 + o * 1.6 + d * 1.15 + V(0, -0.05 + 0.1 * j, 0)]
            strands.append(S.tube([tuple(p) for p in pp], [0.06, 0.045, 0.025], k=0.03))
        H.piece(nm + "P", nm, MA.union_all(strands, 0.03), col="dark", tris=420, role="tentacle", pri=1.6)
        arms.append(([nm], (float(d[0]), -1.0)))
    H.socket("mouth", tuple(hc + V(0, -0.2, -0.8)), "Head")
    H.socket("head", tuple(c + V(0, 1.4, 0)), "Body")
    H.rig.update({"head": "Head"})

    def extra(pose, kind, u, s):
        MA._add(pose, "Head", (0, 0, -0.08 * math.sin(TAU * u), 0.05 * math.sin(TAU * u), 0, 0))
    MA.tentacles(H, arms, period=1.5, height=3.5, extra=extra)
    return H


# ================================================================================================ jellyfish
def _jelly(hid, prev, box=False):
    H = Hero(hid, plan="Blob", gait="float", tags=["jellyfish"])
    H.preview = prev
    yb = 4.2
    H.body((0, yb, 0))
    if box:
        outer = S.round_box(1.15, 0.95, 1.15, 0.45, (0, yb + 0.05, 0))
        inner = S.round_box(1.02, 0.85, 1.02, 0.4, (0, yb - 0.12, 0))
        rr = 1.1
    else:
        outer = S.ellipsoid(1.6, 1.1, 1.6, (0, yb - 0.2, 0))
        inner = S.ellipsoid(1.46, 0.92, 1.46, (0, yb - 0.38, 0))
        rr = 1.52
    bell = outer.ss(inner, 0.05) & S.SDF(lambda Q: (yb - 0.85) - Q[:, 1])
    if not box:
        # scalloped margin
        sc = S.SDF(lambda Q: (yb - 0.75 + 0.07 * np.cos(np.arctan2(Q[:, 2], Q[:, 0]) * 16)) - Q[:, 1])
        bell = (outer.ss(inner, 0.05)) & sc
    ycut = yb - 0.2

    def rings(Q):
        out = np.ones(len(Q))
        for k in range(4):
            a = TAU * (k + 0.5) / 4
            cc = np.array((0.45 * math.cos(a), 0.45 * math.sin(a)))
            d = np.hypot(Q[:, 0] - cc[0], Q[:, 2] - cc[1])
            out *= 1 - 0.35 * np.clip(1 - np.abs(d - 0.28) / 0.07, 0, 1) * (Q[:, 1] > yb)
        return out
    capr = bell.si(S.SDF(lambda Q: ycut - 0.15 - Q[:, 1]), 0.05)
    H.piece("Cap", "Body", capr, col="primary", mat="glass", tris=2000, res=128, role="body", tr=0.35, pattern=None if box else rings)
    n = 8
    ov, dl = 0.12, 0.012
    rims = []
    for i in range(n):
        a0 = TAU * i / n
        a1 = TAU * (i + 1) / n
        am = (a0 + a1) / 2
        pv_ = (rr * 0.95 * math.cos(am), ycut, rr * 0.95 * math.sin(am))
        nm = f"Rim{i}"
        H.bone(nm, "Body", pv_)

        def f(Q, a0=a0, a1=a1, am=am):
            ang = np.arctan2(Q[:, 2], Q[:, 0])
            da = np.angle(np.exp(1j * (ang - am)))
            half = (a1 - a0) / 2
            r = np.hypot(Q[:, 0], Q[:, 2])
            arc = (np.abs(da) - half) * np.maximum(r, 0.5)
            ramp = np.clip(arc / (0.5 * ov), 0, 1) + np.clip((Q[:, 1] - ycut) / (0.5 * ov), 0, 1)
            return np.maximum(bell(Q) + dl * ramp, np.maximum(arc - ov, Q[:, 1] - ycut - ov))
        H.piece(f"Skirt{i}", nm, S.SDF(f), col="primary", mat="glass", tris=380, res=110, role="body", tr=0.35, pri=1.3)
        rims.append((nm, am))
    # oral arms (frilly) and tentacles
    arms = []
    for k in range(4):
        a = TAU * (k + 0.25) / 4
        d = V(math.cos(a), 0, math.sin(a))
        p0 = V(0, yb - 0.5, 0) + d * 0.18
        path = [p0, p0 + d * 0.25 + V(0, -0.9, 0), p0 + d * 0.32 + V(0, -1.8, 0), p0 + d * 0.2 + V(0, -2.7, 0), p0 + d * 0.05 + V(0, -3.4, 0)]
        rad = [0.12, 0.13, 0.11, 0.08, 0.04]
        frill = lambda i, sh, pts, rr, k=k: sh.su(S.tube([tuple(p) for p in pts], [r * 1.5 for r in rr], k=0.05).noise(0.07, 7.0, k + i).si(sh.round(0.09), 0.04), 0.04)
        nm = [f"Oral{k}A", f"Oral{k}B"]
        limb(H, nm, "Body", [path[0], path[2]], path, rad, col="secondary", tris=[650, 550], role="tentacle", deco=frill)
        for p_ in H.parts[-2:]:
            p_["tr"] = 0.25
        arms.append((nm, (float(d[0]), float(d[2]))))
    nt = 4 if box else 8
    for k in range(nt):
        a = TAU * (k + (0.5 if box else 0.0)) / nt
        d = V(math.cos(a), 0, math.sin(a))
        p0 = d * (rr * (1.12 if box else 0.97)) + V(0, ycut - (0.55 if box else 0.6), 0)
        path = [p0, p0 + V(0, -1.0, 0) + d * 0.12, p0 + V(0, -2.0, 0) + d * 0.1, p0 + V(0, -3.0, 0), p0 + V(0, -3.55, 0) - d * 0.12]
        nm = [f"Tent{k}A", f"Tent{k}B"]
        if box:
            def bundle(i, sh, pts, rr):
                out = [sh]
                for j in (-1, 1):
                    o = np.cross(d, V(0, 1, 0)) * 0.12 * j
                    out.append(S.tube([tuple(p + o * (1 + 0.5 * q)) for q, p in enumerate(pts)], [r * 0.8 for r in rr], k=0.03))
                return MA.union_all(out, 0.03)
            limb(H, nm, "Body", [path[0], path[2]], path, [0.07, 0.06, 0.05, 0.04, 0.025], col="secondary", tris=[420, 380], role="tentacle", deco=bundle)
        else:
            limb(H, nm, "Body", [path[0], path[2]], path, [0.07, 0.06, 0.05, 0.04, 0.025], col="primary", tris=[220, 200], role="tentacle")
        arms.append((nm, (float(d[0]), float(d[2]))))
    H.socket("mouth", (0, yb - 0.8, 0), "Body")
    H.socket("head", (0, yb + 1.0, 0), "Body")
    H.rig.update({"head": "Body"})

    def extra(pose, kind, u, s):
        # bell pulse: the skirt flaps flare out then snap in (the tangent-axis rotation)
        if kind in ("move", "idle"):
            k = (0.28 if kind == "move" else 0.12) * math.sin(TAU * u)
        elif kind == "attack":
            k = 0.4 * s
        else:
            k = -0.2 * s
        for nm, am in rims:
            MA._add(pose, nm, (0, 0, 0, -k * math.sin(am), 0, k * math.cos(am)))
    MA.tentacles(H, arms, period=1.6, height=4.5, jet=True, extra=extra)
    return H


@hero("jellyfish", FAM)
def jellyfish():
    return _jelly("jellyfish", pv("jellyfish"))


@hero("box jellyfish", FAM)
def box_jellyfish():
    return _jelly("box jellyfish", pv("box jellyfish"), box=True)


# ================================================================================================ crabs
def _crab(hid, prev, width=1.6, depth=1.15, legs_len=1.0, claw=1.0, claw_l=None, spiky=0.0, hermit=False, flat=0.55):
    H = Hero(hid, plan="Crab", gait="scuttle", tags=["crab", "crustacean"])
    H.preview = prev
    y = 1.05 * max(1.0, legs_len * 0.9)
    H.body((0, y, 0))
    pat = combine(spots(0.35, 0.07, depth=0.2, seed=5), gradient(1, y - 0.6, y + 0.6, 0.85, 1.0))
    if hermit:
        # spiral shell instead of a carapace, soft abdomen hidden inside
        shell = S.SDF(lambda Q: 0)
        parts = []
        ax = V(0, 0.55, 0.85)
        ax /= np.linalg.norm(ax)
        e1 = V(1, 0, 0)
        e2 = np.cross(ax, e1)
        c0 = V(0, y + 0.45, 0.35)
        for k in range(30):
            phi = k * 0.5
            R = 0.95 * math.exp(-0.07 * k)
            p = c0 + ax * 1.7 * (1 - math.exp(-0.07 * k)) + (e1 * math.cos(phi) + e2 * math.sin(phi)) * R * 0.5
            parts.append(S.sphere(0.85 * R, tuple(p)))
        shell = MA.union_all(parts, 0.12)
        shell = shell.ss(S.ellipsoid(0.6, 0.55, 0.5, (0, y + 0.35, -0.35)), 0.1)
        H.piece("Shell", "Body", shell.noise(0.025, 3.0, 2), col="secondary", mat="hard", tris=2400, res=128, role="shell",
                pattern=stripes(lambda Q: np.arctan2(Q[:, 2] - 0.6, Q[:, 0]) / TAU + Q[:, 1] * 0.25, 4, width=0.25, depth=0.3))
        cara = S.ellipsoid(0.55, 0.42, 0.55, (0, y + 0.1, -0.45))
    else:
        cara = S.ellipsoid(width, flat * 1.0, depth, (0, y + 0.1, 0))
        cara = cara.su(S.ellipsoid(width * 0.75, flat * 0.5, depth * 0.8, (0, y + 0.35, -0.05)), 0.3)  # domed top
        cara = cara.ss(S.ellipsoid(0.12, 0.2, 0.5, (0.35, y + 0.6, 0.2)).mirror_x(), 0.15)  # grooves
        teeth = []
        for k in range(5):
            a = math.radians(-82 + k * 15)
            p = V(width * math.sin(a + math.pi / 2) * 0.98, y + 0.12, -depth * math.cos(a + math.pi / 2) * 0.98)
            p = V(width * 0.98 * math.cos(math.radians(30 + k * 13)), y + 0.12, -depth * 0.98 * math.sin(math.radians(30 + k * 13)))
            dd = (p - V(0, y, 0))
            dd[1] = 0
            dd /= np.linalg.norm(dd)
            teeth.append(S.round_cone(tuple(p - dd * 0.1), tuple(p + dd * (0.22 + spiky * 0.3)), 0.12, 0.02))
        cara = cara.su(MA.union_all(teeth).mirror_x(), 0.06)
        if spiky:
            rng = np.random.default_rng(2)
            sp = []
            for k in range(26):
                a = rng.uniform(0, TAU)
                r = rng.uniform(0.1, 0.85)
                p = V(width * r * math.cos(a), 0, depth * r * math.sin(a))
                hgt = flat * math.sqrt(max(0.0, 1 - r * r)) + y + 0.1
                sp.append(S.round_cone((p[0], hgt - 0.05, p[2]), (p[0] * 1.05, hgt + 0.25 * spiky, p[2] * 1.05), 0.08, 0.01))
            cara = cara.su(MA.union_all(sp), 0.04)
        cara = cara.noise(0.015, 5.0, 3)
        H.piece("Carapace", "Body", cara, col="primary", mat="hard", tris=2600, res=136, role="body", pattern=pat)
        cara = S.ellipsoid(width * 0.8, 0.35, depth * 0.8, (0, y - 0.18, 0.05))
    H.piece("Under", "Body", cara if hermit else cara.su(S.ellipsoid(0.5, 0.15, 0.45, (0, y - 0.3, 0.3)), 0.1), col="primary" if hermit else "secondary",
            mat="hard", tris=1000, role="body")
    fz = -depth if not hermit else -0.95
    H.piece("Mouthparts", "Body", S.round_box(0.32, 0.22, 0.12, 0.08, (0, y - 0.05, fz + 0.05)).su(S.round_box(0.12, 0.25, 0.08, 0.05, (0.1, y - 0.1, fz)).mirror_x(), 0.03),
            col="secondary", mat="hard", tris=400, role="mouth", pri=1.6)
    # eye stalks
    es = V(0.32, y + 0.25, fz + 0.12)
    et = es + V(0.08, 0.45, -0.05)
    H.mbone("Eye#", "Body", tuple(es))
    H.mpiece("Stalk#", "Eye#", S.round_cone(tuple(es), tuple(et), 0.08, 0.07), col="primary", mat="hard", tris=200, role="eye", pri=1.6)
    H.mprim("EyeBall#", "Eye#", "Ball", (0.22, 0.22, 0.22), tuple(et + V(0, 0.07, 0)), col="pupil", mat="hard", role="eye", pri=2.0)
    H.mprim("EyeShine#", "Eye#", "Ball", (0.07, 0.07, 0.07), tuple(et + V(0.05, 0.14, -0.07)), col="shine", mat="hard", role="shine", pri=2.4)
    # claws
    claws = []
    for sd in (1, -1):
        cs = claw if sd > 0 else (claw_l if claw_l is not None else claw)
        S_ = "R" if sd > 0 else "L"
        sh = V(sd * width * 0.6, y - 0.05, fz + 0.3)
        el = V(sd * (width * 0.6 + 0.7 * cs), y + 0.15, fz - 0.25 * cs)
        wr = V(sd * (width * 0.45 + 0.55 * cs), y + 0.22, fz - 0.75 * cs)
        tip = wr + V(-sd * 0.25 * cs, -0.12 * cs, -1.25 * cs)
        hinge = wr + V(-sd * 0.05 * cs, 0.22 * cs, -0.55 * cs)
        H.bone("Claw" + S_ + "1", "Body", tuple(sh))
        H.bone("Claw" + S_ + "2", "Claw" + S_ + "1", tuple(el))
        H.bone("Claw" + S_ + "3", "Claw" + S_ + "2", tuple(wr))
        H.bone("Finger" + S_, "Claw" + S_ + "3", tuple(hinge))
        r = 0.17 * max(cs, 0.5)
        H.piece("Arm" + S_ + "P", "Claw" + S_ + "1", S.round_cone(tuple(sh), tuple(el), r, r * 1.05), col="primary", mat="hard", tris=450, role="limb", pattern=pat)
        H.piece("Wrist" + S_ + "P", "Claw" + S_ + "2", S.round_cone(tuple(el), tuple(wr), r * 1.0, r * 1.15).su(S.sphere(r * 0.6, tuple(el + (wr - el) * 0.5 + V(0, r * 0.5, 0))), 0.05),
                col="primary", mat="hard", tris=450, role="limb", pattern=pat)
        palm = S.ellipsoid(0.38 * cs, 0.32 * cs, 0.55 * cs, tuple(wr + V(-sd * 0.05 * cs, 0.05 * cs, -0.42 * cs)))
        palm = palm.su(S.round_cone(tuple(wr + V(-sd * 0.1 * cs, -0.12 * cs, -0.75 * cs)), tuple(tip), 0.17 * cs, 0.03 * cs), 0.1 * cs)  # fixed finger
        tooth = [S.sphere(0.05 * cs, tuple(wr + V(-sd * 0.15 * cs, -0.02 * cs, -(0.85 + 0.15 * k) * cs))) for k in range(3)]
        palm = palm.su(MA.union_all(tooth), 0.02)
        H.piece("Hand" + S_ + "P", "Claw" + S_ + "3", palm, col="primary", mat="hard", tris=800, role="claw", pattern=combine(pat, lambda Q, tip=tip: 1 - 0.6 * np.clip(1 - np.linalg.norm(Q - tip, axis=1) / (0.45 * cs), 0, 1)))
        dtip = tip + V(sd * 0.05 * cs, 0.32 * cs, 0.0)
        dac = S.tube([tuple(hinge), tuple(hinge + (dtip - hinge) * 0.5 + V(0, 0.1 * cs, 0)), tuple(dtip)], [0.15 * cs, 0.12 * cs, 0.03 * cs], k=0.05)
        H.piece("Dactyl" + S_ + "P", "Finger" + S_, dac, col="primary", mat="hard", tris=450, role="claw",
                pattern=lambda Q, dtip=dtip, cs=cs: 1 - 0.6 * np.clip(1 - np.linalg.norm(Q - dtip, axis=1) / (0.45 * cs), 0, 1))
        claws.append(("Claw" + S_ + "1", "Claw" + S_ + "2", "Finger" + S_, sd))
    # legs
    legs = []
    zs = (-0.45, 0.0, 0.42, 0.8) if not hermit else (-0.6, -0.25, 0.1, 0.4)
    for i, z in enumerate(zs):
        spread = (i - 1.2) * 0.35
        hip = V(width * 0.82 if not hermit else 0.45, y - 0.08, z * depth / 1.15)
        knee = hip + V(0.95 * legs_len, 0.38 * legs_len, spread * 0.6)
        tip = V(hip[0] + 1.85 * legs_len, 0.04, hip[2] + spread * 1.3)
        mid = knee + (tip - knee) * 0.45 + V(0.22 * legs_len, 0.12 * legs_len, 0)
        path = [hip, hip + (knee - hip) * 0.5, knee, mid, tip]
        rad = [0.15, 0.15, 0.13, 0.1, 0.025]
        nm = [f"Leg{i}#", f"Knee{i}#"]
        H.mbone(nm[0], "Body", tuple(hip))
        H.mbone(nm[1], nm[0], tuple(knee))
        up = S.tube([tuple(p) for p in path[:3]], [rad[0], rad[1], rad[2] * 1.07], k=0.03)
        lo = S.tube([tuple(p) for p in path[2:]], rad[2:], k=0.03)
        fl = lambda sh: S.SDF(lambda Q, sh=sh: sh(Q))
        H.mpiece(f"Femur{i}#", nm[0], up, col="primary", mat="hard", tris=380, role="limb", pattern=pat)
        H.mpiece(f"Tibia{i}#", nm[1], lo, col="primary", mat="hard", tris=380, role="limb",
                 pattern=lambda Q, tip=tip: 1 - 0.35 * np.clip(1 - Q[:, 1] / 0.5, 0, 1))
        ph = (0.0 if i % 2 == 0 else 0.5)
        legs.append((f"Leg{i}R", f"Knee{i}R", 1, ph))
        legs.append((f"Leg{i}L", f"Knee{i}L", -1, ph + 0.5))
    H.socket("mouth", (0, y, fz - 0.3), "Body")
    H.socket("head", (0, y + 0.9, 0), "Body")
    H.rig.update({"head": "Body", "legs": [{"hip": l[0], "knee": l[1], "phase": l[3], "side": l[2]} for l in legs]})
    MA.scuttle(H, legs, claws=claws, eyes=["EyeR", "EyeL"], period=0.7, height=y)
    return H


@hero("crab", FAM)
def crab():
    return _crab("crab", pv("crab"))


@hero("king crab", FAM)
def king_crab():
    return _crab("king crab", pv("crab", primary="#B8402A", secondary="#E8B090"), width=1.2, depth=1.1, legs_len=1.6, claw=0.8, spiky=0.6, flat=0.6)


@hero("fiddler crab", FAM)
def fiddler():
    return _crab("fiddler crab", pv("fiddler crab"), width=1.25, depth=0.95, claw=1.7, claw_l=0.45, legs_len=0.9)


@hero("hermit crab", FAM)
def hermit():
    return _crab("hermit crab", pv("hermit crab"), claw=0.95, claw_l=0.7, legs_len=0.85, hermit=True)


# ================================================================================================ lobster / shrimp
def _decapod(hid, prev, shrimp=False):
    H = Hero(hid, plan="Crab", gait="swim" if shrimp else "scuttle", tags=["crustacean", "shrimp" if shrimp else "lobster"])
    H.preview = prev
    y = 1.4 if not shrimp else 1.9
    H.body((0, y, 0))
    pat = combine(spots(0.3, 0.05, depth=0.25, seed=9), gradient(1, y - 0.5, y + 0.5, 0.82, 1.0))
    # cephalothorax
    r0 = 0.6 if not shrimp else 0.42
    cara = S.ellipsoid(r0 * 0.9, r0, 1.25, (0, y + 0.05, -0.7))
    cara = cara.su(S.round_cone((0, y + 0.2, -1.6), (0, y + 0.3 if shrimp else y + 0.15, -2.6 if shrimp else -2.2), 0.14, 0.02), 0.1)  # rostrum
    if shrimp:
        cara = cara.su(MA.union_all([S.round_cone((0, y + 0.3 + 0.02 * k, -1.7 - 0.18 * k), (0, y + 0.45, -1.75 - 0.18 * k), 0.04, 0.01) for k in range(5)]), 0.02)
    cara = cara.ss(S.ellipsoid(0.08, 0.3, 0.6, (r0 * 0.7, y + 0.3, -0.55)).mirror_x(), 0.1)
    H.piece("Carapace", "Body", cara, col="primary", mat="hard", tris=2000, res=128, role="body", pattern=pat)
    # abdomen chain
    if shrimp:
        pts = [V(0, y + 0.1, 0.4), V(0, y + 0.2, 0.9), V(0, y + 0.08, 1.4), V(0, y - 0.25, 1.8), V(0, y - 0.7, 1.98), V(0, y - 1.12, 1.85), V(0, y - 1.45, 1.55)]
    else:
        pts = [V(0, y + 0.05, 0.4), V(0, y + 0.05, 0.95), V(0, y, 1.5), V(0, y - 0.05, 2.0), V(0, y - 0.12, 2.5), V(0, y - 0.2, 2.95), V(0, y - 0.25, 3.3)]
    rads = [0.55, 0.52, 0.48, 0.42, 0.36, 0.3, 0.22] if not shrimp else [0.38, 0.37, 0.34, 0.3, 0.25, 0.2, 0.15]
    tails = []
    prev = "Body"
    for i in range(5):
        nm = f"Tail{i + 1}"
        H.bone(nm, prev, tuple(pts[i]))
        prev = nm
        tails.append(nm)
        a, b = pts[i], pts[i + 1]
        d = (b - a) / np.linalg.norm(b - a)
        segm = S.round_cone(tuple(a - d * 0.05), tuple(b + d * 0.12), rads[i], rads[i + 1] * 1.05)
        segm = segm.scale3(1.0, 1.0, 1.0)
        # pleura (side plates) hanging down
        nrm = np.cross(d, V(1, 0, 0))
        pl = S.ellipsoid(0.1, rads[i] * 0.55, 0.25, tuple((a + b) / 2 - nrm * rads[i] * 0.55 + V(rads[i] * 0.72, 0, 0))).mirror_x()
        segm = segm.su(pl, 0.08)
        if shrimp:  # swimmerets
            segm = segm.su(S.round_cone(tuple((a + b) / 2 - nrm * rads[i] * 0.7 + V(0.15, 0, 0)), tuple((a + b) / 2 - nrm * (rads[i] + 0.45) + V(0.2, 0, 0.1)), 0.05, 0.02).mirror_x(), 0.03)
        H.piece(f"Seg{i + 1}", nm, segm, col="primary", mat="hard", tris=650, role="body", pattern=pat)
    # tail fan
    H.bone("Fan", "Tail5", tuple(pts[5]))
    d = pts[6] - pts[5]
    d /= np.linalg.norm(d)
    side = V(1, 0, 0)
    up_ = np.cross(side, d)
    fan = []
    for k, (ang, ln, w) in enumerate(((0, 0.95, 0.32), (28, 0.85, 0.28), (-28, 0.85, 0.28), (52, 0.75, 0.24), (-52, 0.75, 0.24))):
        a = math.radians(ang)
        dir_ = d * math.cos(a) + side * math.sin(a)
        c = pts[5] + dir_ * ln * 0.55
        fan.append(plate(tuple(pts[5]), tuple(dir_), tuple(np.cross(up_, dir_)), [(-0.1, -w * 0.4), (ln * 0.5, -w * 0.5), (ln, -w * 0.25), (ln * 1.05, 0), (ln, w * 0.25), (ln * 0.5, w * 0.5), (-0.1, w * 0.4)], 0.07, taper=0.5, edge=0.1))
    H.piece("FanP", "Fan", MA.union_all(fan, 0.03), col="primary", mat="hard", tris=700, role="tail", pattern=gradient(2, pts[5][2], pts[5][2] + 0.9, 1.0, 0.7))
    # eyes
    for sd in (1, -1):
        pass
    es = V(0.22, y + 0.2, -1.55)
    H.mprim("EyeBall#", "Body", "Ball", (0.2, 0.2, 0.2), tuple(es + V(0.05, 0.05, -0.05)), col="pupil", mat="hard", role="eye", pri=2.0)
    H.mprim("EyeShine#", "Body", "Ball", (0.06, 0.06, 0.06), tuple(es + V(0.09, 0.12, -0.1)), col="shine", mat="hard", role="shine", pri=2.4)
    H.piece("EyeStalks", "Body", S.round_cone(tuple(es + V(-0.1, -0.08, 0.15)), tuple(es), 0.07, 0.07).mirror_x(), col="primary", mat="hard", tris=200, role="eye", pri=1.7)
    # antennae
    ants = []
    for sd in (1, -1):
        S_ = "R" if sd > 0 else "L"
        base = V(sd * 0.28, y - 0.05, -1.55)
        ln = 4.2 if shrimp else 3.4
        p1 = base + V(sd * 0.35, 0.5, -0.9)
        p2 = p1 + V(sd * 0.6, 0.4, 0.2) * ln / 3.4
        p3 = p2 + V(sd * 0.5, 0.0, 1.4) * ln / 3.4
        p4 = p3 + V(sd * 0.25, -0.2, 1.4) * ln / 3.4
        H.bone("Ant" + S_, "Body", tuple(base))
        H.piece("Antenna" + S_, "Ant" + S_, S.tube([tuple(base), tuple(p1), tuple(p2), tuple(p3), tuple(p4)], [0.08, 0.05, 0.035, 0.025, 0.015], k=0.05),
                col="primary", mat="hard", tris=420, role="antenna", pri=1.8)
        ants.append("Ant" + S_)
    H.piece("Antennules", "Body", S.tube([(0.1, y - 0.1, -1.55), (0.18, y + 0.1, -2.2), (0.25, y + 0.35, -2.7)], [0.04, 0.03, 0.015], k=0.03).mirror_x(),
            col="primary", mat="hard", tris=300, role="antenna", pri=1.8)
    # claws (lobster crushers / shrimp tiny pincers)
    claws = []
    cs = 1.35 if not shrimp else 0.35
    for sd in (1, -1):
        S_ = "R" if sd > 0 else "L"
        sh = V(sd * 0.4, y - 0.3, -1.25)
        el = sh + V(sd * 0.55, 0.15, -0.75) * max(cs, 0.6)
        wr = el + V(-sd * 0.05, 0.05, -0.7) * max(cs, 0.6)
        tip = wr + V(-sd * 0.15 * cs, -0.05, -1.6 * cs)
        hinge = wr + V(-sd * 0.12 * cs, 0.2 * cs, -0.75 * cs)
        H.bone("Claw" + S_ + "1", "Body", tuple(sh))
        H.bone("Claw" + S_ + "2", "Claw" + S_ + "1", tuple(el))
        H.bone("Claw" + S_ + "3", "Claw" + S_ + "2", tuple(wr))
        H.bone("Finger" + S_, "Claw" + S_ + "3", tuple(hinge))
        r = 0.16 if not shrimp else 0.08
        H.piece("Arm" + S_ + "P", "Claw" + S_ + "1", S.round_cone(tuple(sh), tuple(el), r, r * 1.08), col="primary", mat="hard", tris=380, role="limb", pattern=pat)
        H.piece("Wrist" + S_ + "P", "Claw" + S_ + "2", S.round_cone(tuple(el), tuple(wr), r, r * 1.2), col="primary", mat="hard", tris=380, role="limb", pattern=pat)
        palm = S.ellipsoid(0.36 * cs + 0.05, 0.3 * cs + 0.04, 0.7 * cs + 0.05, tuple(wr + V(0, 0.02, -0.55 * cs)))
        palm = palm.su(S.round_cone(tuple(wr + V(-sd * 0.05, -0.08 * cs, -1.0 * cs)), tuple(tip), 0.16 * cs, 0.03 * cs), 0.08 * cs)
        H.piece("Hand" + S_ + "P", "Claw" + S_ + "3", palm, col="primary", mat="hard", tris=700, role="claw", pattern=pat)
        dtip = tip + V(0, 0.28 * cs, 0.05)
        H.piece("Dactyl" + S_ + "P", "Finger" + S_, S.tube([tuple(hinge), tuple(hinge + (dtip - hinge) * 0.5 + V(0, 0.08 * cs, 0)), tuple(dtip)],
                                                         [0.14 * cs + 0.02, 0.11 * cs + 0.015, 0.03 * cs], k=0.04), col="primary", mat="hard", tris=380, role="claw")
        claws.append(("Claw" + S_ + "1", "Claw" + S_ + "2", "Finger" + S_, sd))
    # walking legs: one bent piece each
    legs = []
    for i, z in enumerate((-1.05, -0.75, -0.45, -0.15)):
        hip = V(0.35, y - 0.35, z)
        knee = hip + V(0.75, 0.3 if not shrimp else 0.1, 0.05)
        tip = V(1.75 if not shrimp else 1.1, 0.03 if not shrimp else y - 1.4, z + 0.3)
        H.mbone(f"Leg{i}#", "Body", tuple(hip))
        lg = S.tube([tuple(hip), tuple(knee), tuple(knee + (tip - knee) * 0.5 + V(0.1, 0, 0)), tuple(tip)], [0.075, 0.065, 0.05, 0.015], k=0.03)
        H.mpiece(f"LegP{i}#", f"Leg{i}#", lg, col="primary", mat="hard", tris=300, role="limb")
        legs.append((f"Leg{i}R", None, 1, 0.5 * (i % 2)))
        legs.append((f"Leg{i}L", None, -1, 0.5 * (i % 2) + 0.5))
    H.socket("mouth", (0, y - 0.1, -1.9), "Body")
    H.socket("head", (0, y + 0.8, -0.8), "Body")
    H.rig.update({"head": "Body", "tail": tails + ["Fan"]})

    def extra(pose, kind, u, s):
        if shrimp and kind == "move":  # swimmerets row + tail flick
            for i, b in enumerate(tails):
                MA._add(pose, b, (0, 0, 0, 0.1 * math.sin(TAU * u - i * 0.6), 0, 0))
            MA._add(pose, "Body", (0, 0.1 * math.sin(TAU * u), 0, 0.05 * math.sin(TAU * u + 1), 0, 0))
        if kind == "attack" and not shrimp:
            for i, b in enumerate(tails):
                MA._add(pose, b, (0, 0, 0, 0.15 * s, 0, 0))
    MA.scuttle(H, legs, claws=claws, tail=tails + ["Fan"], antennae=ants, period=0.9 if not shrimp else 1.0, height=y, side=False, extra=extra)
    return H


@hero("lobster", FAM)
def lobster():
    return _decapod("lobster", pv("lobster"))


@hero("shrimp", FAM)
def shrimp():
    return _decapod("shrimp", pv("shrimp"), shrimp=True)


# ================================================================================================ starfish
@hero("starfish", FAM)
def starfish():
    H = Hero("starfish", plan="Blob", gait="scuttle", tags=["starfish", "echinoderm"])
    H.preview = pv("starfish")
    y = 0.42
    H.body((0, y, 0))
    pat = combine(spots(0.28, 0.07, depth=0.3, seed=12), gradient(1, 0.05, 0.8, 0.85, 1.0))
    disc = S.ellipsoid(0.85, 0.42, 0.85, (0, y, 0))
    bumps = [S.sphere(0.11, (0.4 * math.cos(a), y + 0.35, 0.4 * math.sin(a))) for a in np.linspace(0, TAU, 9)[:-1]] + [S.sphere(0.12, (0, y + 0.42, 0))]
    disc = disc.su(MA.union_all(bumps), 0.06)
    stubs = []
    arms = []
    for i in range(5):
        a = math.radians(-90 + 72 * i)
        d = V(math.cos(a), 0, math.sin(a))
        stubs.append(S.round_cone((0, y, 0), tuple(d * 0.9 + V(0, y, 0)), 0.42, 0.36).scale3(1, 1, 1))
    flat = 0.58

    def squash(sh):
        return S.SDF(lambda Q: sh(np.column_stack([Q[:, 0], y + (Q[:, 1] - y) / flat, Q[:, 2]])) * flat)
    H.piece("Disc", "Body", squash(MA.union_all(stubs, 0.2)).su(disc, 0.15), col="primary", tris=2200, res=128, role="body", pattern=pat)
    for i in range(5):
        a = math.radians(-90 + 72 * i)
        d = V(math.cos(a), 0, math.sin(a))
        path = [d * 0.85 + V(0, y, 0), d * 1.35 + V(0, y - 0.02, 0), d * 1.85 + V(0, y - 0.06, 0), d * 2.35 + V(0, y - 0.1, 0), d * 2.75 + V(0, y - 0.1, 0)]
        rad = [0.38, 0.33, 0.27, 0.19, 0.08]

        def deco(j, sh, pts, rr):
            bb = []
            for k in range(len(pts) - 1):
                p = (pts[k] + pts[k + 1]) / 2
                r = (rr[k] + rr[k + 1]) / 2
                bb.append(S.sphere(r * 0.3, tuple(p + V(0, r * flat * 0.95, 0))))
                tg = np.cross(pts[k + 1] - pts[k], V(0, 1, 0))
                tg /= np.linalg.norm(tg)
                bb.append(S.sphere(r * 0.22, tuple(p + tg * r * 0.6 + V(0, r * flat * 0.7, 0))))
                bb.append(S.sphere(r * 0.22, tuple(p - tg * r * 0.6 + V(0, r * flat * 0.7, 0))))
            return sh.su(MA.union_all(bb), 0.03)
        nm = [f"Arm{i}A", f"Arm{i}B"]
        limb(H, nm, "Body", [path[0], path[2]], path, rad, tris=[800, 650], pattern=pat, flat=flat, deco=deco, role="limb")
        arms.append((nm, (float(d[0]), float(d[2]))))
        H.prim(f"EyeSpot{i}", nm[1], "Ball", (0.07, 0.07, 0.07), tuple(path[-1] + d * 0.06 + V(0, 0.0, 0)), col="red", mat="hard", role="eye", pri=2.2)
    H.socket("mouth", (0, y - 0.2, 0), "Body")
    H.socket("head", (0, y + 0.6, 0), "Body")
    H.rig.update({"head": "Body", "arms": [a[0] for a in arms]})

    def curl(pose, u, a):
        for j, (chain, (dx, dz)) in enumerate(arms):
            for k, b in enumerate(chain):
                w = a * math.sin(TAU * u - j * TAU / 5 - k * 0.7)
                MA._add(pose, b, (0, 0, 0, w * dz, 0, -w * dx))

    def move(t):
        u = t / 1.6
        pose = {}
        curl(pose, u, 0.12)
        MA._add(pose, "Body", (0, 0.04 * abs(math.sin(TAU * u)), 0, 0, 0.06 * math.sin(TAU * u), 0))
        return pose

    def idle(t):
        u = t / 4.0
        pose = {}
        curl(pose, u, 0.05)
        MA._add(pose, "Body", (0, 0, 0, 0, 0.1 * math.sin(TAU * u), 0))
        return pose

    def attack(t):
        s = t / 0.8
        pose = {}
        wind = MA._env(s, 0.0, 0.5)
        st = MA._env(s, 0.35, 0.8)
        for j, (chain, (dx, dz)) in enumerate(arms):
            for k, b in enumerate(chain):
                w = -0.55 * wind + 0.35 * st  # arms curl up (negative = tips up) then slam down
                MA._add(pose, b, (0, 0, 0, w * dz, 0, -w * dx))
        MA._add(pose, "Body", (0, 0.6 * wind - 0.1 * st, -0.6 * st, 0, 0.8 * st, 0))
        return pose

    def hit(t):
        s = t / 0.4
        k = math.sin(math.pi * min(s, 1))
        pose = {}
        MA._add(pose, "Body", (0, 0.2 * k, 0.25 * k, 0.2 * k, 0, 0.1 * k))
        return pose
    H.clip("Move", 1.6, move, keys=20)
    H.clip("Idle", 4.0, idle, keys=20)
    H.clip("Attack", 0.8, attack, keys=14, loop=False)
    H.clip("Hit", 0.4, hit, keys=8, loop=False)
    return H


# ================================================================================================ sea urchin
@hero("sea urchin", FAM)
def sea_urchin():
    H = Hero("sea urchin", plan="Blob", gait="scuttle", tags=["urchin", "echinoderm"])
    H.preview = pv("sea urchin")
    y = 1.0
    H.body((0, y, 0))
    test = S.ellipsoid(1.0, 0.78, 1.0, (0, y, 0))
    rows = lambda Q: 1 - 0.22 * (np.abs(np.sin(np.arctan2(Q[:, 2], Q[:, 0]) * 5)) < 0.25)
    knobs = []
    rng = np.random.default_rng(1)
    g = (1 + 5 ** 0.5) / 2
    dirs = []
    N = 150
    for i in range(N):
        zz = 1 - 2 * (i + 0.5) / N
        r = math.sqrt(1 - zz * zz)
        a = TAU * i / g
        dv = V(r * math.cos(a), zz, r * math.sin(a))
        if dv[1] < -0.55:
            continue
        dirs.append(dv)
    H.piece("Test", "Body", test.su(MA.union_all([S.sphere(0.06, tuple(V(0, y, 0) + d * V(1.0, 0.78, 1.0))) for d in dirs[::2]]), 0.03),
            col="secondary", mat="hard", tris=2000, res=128, role="body", pattern=rows)
    groups = 8
    spine_bones = []
    for gi in range(groups):
        a0 = TAU * gi / groups
        nm = f"Spines{gi}"
        mid = V(math.cos(a0 + TAU / groups / 2), 0, math.sin(a0 + TAU / groups / 2))
        H.bone(nm, "Body", tuple(V(0, y, 0) + mid * 0.5))
        cones = []
        for dv in dirs:
            ang = math.atan2(dv[2], dv[0]) % TAU
            if not (a0 <= ang < a0 + TAU / groups):
                continue
            base = V(0, y, 0) + dv * V(0.95, 0.74, 0.95)
            ln = rng.uniform(1.0, 1.45) * (0.8 if dv[1] < -0.2 else 1.0)
            tip = base + dv * ln
            if tip[1] < 0.05:
                tip[1] = 0.05
            cones.append(S.round_cone(tuple(base), tuple(tip), 0.055, 0.008))
        H.piece(f"SpineP{gi}", nm, MA.union_all(cones), col="primary", mat="hard", tris=1300, res=150, role="spike", pri=1.4,
                pattern=lambda Q: 1 - 0.3 * np.clip((np.linalg.norm(Q - V(0, y, 0), axis=1) - 1.1) / 1.0, 0, 1))
        spine_bones.append((nm, mid))
    H.prim("Mouth", "Body", "Ball", (0.35, 0.12, 0.35), (0, y - 0.74, 0), col="mouth", mat="hard", role="mouth", pri=2.0)
    H.socket("mouth", (0, y - 0.6, -0.8), "Body")
    H.socket("head", (0, y + 1.9, 0), "Body")
    H.rig.update({"head": "Body"})

    def wave(pose, u, a):
        for j, (b, m) in enumerate(spine_bones):
            w = a * math.sin(TAU * u - j * TAU / groups)
            MA._add(pose, b, (0, 0, 0, w * m[2], 0, -w * m[0]))

    def move(t):
        u = t / 1.2
        pose = {}
        wave(pose, u * 2, 0.08)
        MA._add(pose, "Body", (0, 0.06 * abs(math.sin(TAU * u)), 0, -0.25 * math.sin(TAU * u) * 0.3, 0, 0.05 * math.sin(TAU * u)))
        return pose

    def idle(t):
        u = t / 3.0
        pose = {}
        wave(pose, u, 0.06)
        return pose

    def attack(t):
        s = t / 0.7
        pose = {}
        wind = MA._env(s, 0.0, 0.4)
        st = MA._env(s, 0.3, 0.75)
        for b, m in spine_bones:  # spines bristle out (burst)
            MA._add(pose, b, (m[0] * 0.45 * st, 0.15 * st, m[2] * 0.45 * st, 0, 0, 0))
        MA._add(pose, "Body", (0, 0.35 * wind, -0.5 * st, 0, 1.2 * st, 0))
        return pose

    def hit(t):
        s = t / 0.4
        k = math.sin(math.pi * min(s, 1))
        pose = {}
        MA._add(pose, "Body", (0, 0.1 * k, 0.2 * k, 0.2 * k, 0, 0))
        wave(pose, s, -0.15 * k)
        return pose
    H.clip("Move", 1.2, move, keys=20)
    H.clip("Idle", 3.0, idle, keys=20)
    H.clip("Attack", 0.7, attack, keys=14, loop=False)
    H.clip("Hit", 0.4, hit, keys=8, loop=False)
    return H


CRE = {"cat": ["Creature", "Machine"]}
MAP = [
    ("octopus", "octopus, octopi, octopuses, giant pacific octopus, blue-ringed octopus, blue ringed octopus, mimic octopus, dumbo octopus, "
                "baby octopus, coconut octopus, wonderpus, robot octopus, space octopus, sea witch octopus", CRE),
    ("squid", "squid, giant squid, colossal squid, vampire squid, firefly squid, humboldt squid, glass squid, bobtail squid, bigfin squid, "
              "cuttlefish, cameroceras, kraken spawn, baby kraken pet", CRE),
    ("nautilus", "nautilus, chambered nautilus, ammonite, argonaut", CRE),
    ("jellyfish", "jellyfish, jelly fish, moon jellyfish, lion's mane jellyfish, comb jelly, immortal jellyfish, cassiopea, fried egg jellyfish, "
                  "sea gooseberry, space jellyfish, moon jelly giant, robot jellyfish, portuguese man o war, man o war", CRE),
    ("box jellyfish", "box jellyfish, sea wasp, irukandji", CRE),
    ("crab", "crab, crabs, blue crab, red crab, ghost crab, sand crab, porcelain crab, decorator crab, pom pom crab, yeti crab, robot crab, "
             "crystal crab, magma crab, karkinos, giant crab monster, alien invader, horseshoe crab, !crab cake, !crab spider, !crab apple", CRE),
    ("king crab", "king crab, spider crab, coconut crab, sea spider, japanese spider crab", CRE),
    ("fiddler crab", "fiddler crab, pistol shrimp", CRE),
    ("hermit crab", "hermit crab", CRE),
    ("lobster", "lobster, lobsters, crayfish, crawfish, crawdad, spiny lobster, slipper lobster, anomalocaris, !lobster roll", CRE),
    ("shrimp", "shrimp, prawn, prawns, shrimps, mantis shrimp, peacock mantis shrimp, cleaner shrimp, harlequin shrimp, krill, amphipod, sea monkey", CRE),
    ("starfish", "starfish, star fish, sea star, crown-of-thorns starfish, crown of thorns starfish, brittle star, sea lily", CRE),
    ("sea urchin", "sea urchin, urchin, urchins, sand dollar", CRE),
]
