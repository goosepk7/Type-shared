"""Serpentine dragons: chinese (lung) dragon, sea serpent, leviathan, lindworm, amphiptere, and the basilisk.

One parametric builder (`_serpent`): a spline spine resampled into a chain of bones; every chain link is its own
sculpted segment (overlapping round cones with dorsal spines / fins / mane tufts, belly scutes as a darkening
mask); a reptile head with style switches (lung: upturned snout, antlers, flowing whiskers on their own bones, mane
and beard; sea: cheek fin-frills; levi: armoured brow plates and a crest of spikes; basilisk: crown crest; wyrm:
swept horns); optional small legs (two or four) and feathered wings (amphiptere). Motion: motion_mythic.serpent
(travelling waves: vertical for flying / swimming, lateral for slithering).
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from kit import Hero, hero, stripes, combine
from map import NOTFOOD
import motion_mythic as mm
from mythic_geo import (V, nrm, tri, fan, union_hard, bounded, frame, oell, squash, flat_tube, spike, curved_horn, blade_fin,
                        outside, band_y, feather, Shift)


def spline(ctrl, n):
    """Catmull-Rom through ctrl, resampled to n points equally spaced by arc length."""
    c = [V(p) for p in ctrl]
    c = [c[0] * 2 - c[1]] + c + [c[-1] * 2 - c[-2]]
    dense = []
    for i in range(1, len(c) - 2):
        p0, p1, p2, p3 = c[i - 1], c[i], c[i + 1], c[i + 2]
        for k in range(40):
            t = k / 40
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    dense.append(c[-2])
    D = np.array(dense)
    seg = np.linalg.norm(np.diff(D, axis=0), axis=1)
    acc = np.concatenate([[0], np.cumsum(seg)])
    out = []
    for i in range(n):
        L = acc[-1] * i / (n - 1)
        j = min(np.searchsorted(acc, L), len(D) - 1)
        if j == 0:
            out.append(D[0])
            continue
        f = (L - acc[j - 1]) / max(acc[j] - acc[j - 1], 1e-9)
        out.append(D[j - 1] + (D[j] - D[j - 1]) * f)
    return out


BASE = dict(
    s=1.0,
    ctrl=None,          # spine control points head base -> tail tip
    n=10,               # spine points (links = n - 1)
    r0=0.5, rmax=0.62, rtail=0.08,
    style="lung",
    head=1.0, snout=1.0,
    legs=4,             # 0 / 2 / 4
    leg=1.0,
    wings=False,        # feathered wings (amphiptere)
    dorsal="spines",    # "spines" | "fin" | "mane" | "plates" | None
    mode="fly",         # fly | swim | slither
    tuft=True,
    gait="fly",
    preview={},
)


def _serpent(hid, plan="Serpent", **kw):
    P = dict(BASE)
    P.update(kw)
    s = P["s"]
    H = Hero(hid, plan=plan, gait=P["gait"], tags=["dragon", "reptile", "serpent"])
    H.preview = P["preview"]
    pts = [V(p) * s for p in spline(P["ctrl"], P["n"])]
    n = len(pts)
    # radius profile: neck r0 -> rmax at ~25% -> tail
    rad = []
    for i in range(n):
        u = i / (n - 1)
        if u < 0.22:
            r = P["r0"] + (P["rmax"] - P["r0"]) * (u / 0.22)
        else:
            r = P["rmax"] + (P["rtail"] - P["rmax"]) * ((u - 0.22) / 0.78) ** 1.15
        rad.append(r * s)

    H.body(tuple(pts[2]))
    H.bone("Neck1", "Body", tuple(pts[2]))
    H.bone("Neck2", "Neck1", tuple(pts[1]))
    H.bone("Head", "Neck2", tuple(pts[0]))
    chain = []
    for k in range(3, n - 1):
        b = f"Seg{k}"
        H.bone(b, "Body" if k == 3 else f"Seg{k - 1}", tuple(pts[k]))
        chain.append(b)

    def link_bone(i):
        return {0: "Neck2", 1: "Neck1", 2: "Body"}.get(i, f"Seg{i}")

    st = P["style"]
    dorsal = P["dorsal"]
    for i in range(n - 1):
        a, b = pts[i], pts[i + 1]
        d = nrm(b - a)
        ext = 0.35 if i > 0 else 0.15
        seg = round_cone(a - d * rad[i] * ext, b + d * rad[i + 1] * 0.35, rad[i], rad[i + 1])
        core = seg
        up = nrm(np.cross(np.cross(d, (0, 1, 0)), d))
        if up[1] < 0:
            up = -up
        side = nrm(np.cross(up, d))
        if dorsal == "spines":
            for j in range(2):
                u = (j + 0.5) / 2
                base = a + (b - a) * u + up * (rad[i] + (rad[i + 1] - rad[i]) * u - 0.1 * s)
                seg = seg.su(blade_fin(base, up, (0.42 * rad[i] / P["rmax"] + 0.08) * s, 0.12 * s * rad[i] / P["rmax"] + 0.03 * s, side, flat=0.3, back=d), 0.04)
        elif dorsal in ("fin", "mane"):
            hgt = (0.55 if dorsal == "fin" else 0.45) * (rad[i] / P["rmax"]) ** 0.7 * s
            pa_ = a + up * rad[i] * 0.7
            pb_ = b + up * rad[i + 1] * 0.7
            if dorsal == "fin":
                fin = union_hard([tri(pa_, pb_, (pa_ + pb_) / 2 + up * hgt + d * 0.15 * s, 0.035 * s),
                                  tri(pa_, pa_ + up * hgt * 0.7 + d * 0.05 * s, (pa_ + pb_) / 2 + up * hgt + d * 0.15 * s, 0.035 * s)])
                for j in range(3):
                    q = pa_ + (pb_ - pa_) * (j / 3 + 0.1)
                    fin = fin.su(round_cone(q, q + up * hgt * 0.95 + d * 0.15 * s, 0.05 * s, 0.015 * s), 0.02)
                seg = seg.su(fin, 0.04)
            else:
                for j in range(3):
                    q = a + (b - a) * (j / 3 + 0.15) + up * (rad[i] - 0.05 * s)
                    seg = seg.su(flat_tube([q, q + up * hgt * 0.6 + d * 0.15 * s, q + up * hgt * 0.8 + d * hgt * 0.8 - side * 0.05 * s],
                                           [0.12 * s, 0.07 * s, 0.015 * s], side, flat=0.35), 0.04)
        elif dorsal == "plates":
            for j in range(2):
                u = (j + 0.5) / 2
                base = a + (b - a) * u + up * (rad[i] - 0.12 * s)
                seg = seg.su(blade_fin(base, up + d * 0.2, 0.5 * (rad[i] / P["rmax"]) * s + 0.05 * s, 0.2 * s * rad[i] / P["rmax"] + 0.03, side, flat=0.25, back=d), 0.05)
                for sx in (1, -1):
                    seg = seg.su(spike(a + (b - a) * u + side * sx * rad[i] * 0.75 + up * rad[i] * 0.45, side * sx + up * 0.6, 0.22 * s * rad[i] / P["rmax"], 0.07 * s), 0.04)
        if i == n - 2 and P["tuft"]:
            tuft = None
            for j in range(5):
                ang = -0.9 + 0.45 * j
                dd = nrm(d + up * math.sin(ang) * 0.9 + side * math.cos(ang) * 0.35 * (1 if j % 2 else -1))
                f_ = flat_tube([b - d * 0.3 * s, b + dd * 0.55 * s, b + dd * 1.0 * s + up * 0.15 * s], [0.14 * s, 0.1 * s, 0.015 * s], side, flat=0.4)
                tuft = f_ if tuft is None else tuft.su(f_, 0.04)
            H.piece("TailTuft", link_bone(i), tuft, col="secondary", mat="skin", tris=700, role="tail", pri=1.6)
        # belly scutes: dark bands on the underside, back darker
        pat = combine(stripes(lambda Q, a_=a, d_=d: (Q - a_) @ d_ / s, 3.0, width=0.18, depth=0.3,
                              region=lambda Q, a_=a, up_=up, r_=rad[i]: np.clip(-((Q - a_) @ up_) / (r_ * 0.5) - 0.2, 0, 1)),
                      lambda Q, a_=a, up_=up, r_=rad[i]: 1 - 0.16 * np.clip(((Q - a_) @ up_) / r_, 0, 1),
                      outside(core, 0.04, 0.5, 0.08))
        nm = "Torso" if i == 2 else f"Link{i}"
        H.piece(nm, link_bone(i), seg, col="primary", tris=900 if i < 4 else max(380, int(900 - 70 * i)), res=120,
                role="body" if i == 2 else ("limb" if i < 2 else "tail"), pri=1.0 + 0.04 * i, pattern=pat)

    # ------------------------------------------------------------------ head
    hc = pts[0]
    hs = s * P["head"]
    SN = P["snout"]
    hd = nrm(pts[0] - pts[1])
    hd = nrm(V(0, hd[1] * 0.25, hd[2]))  # head mostly level

    def h(x, y, z):
        return hc + V(x, y, z) * hs

    head = ellipsoid(0.42 * hs, 0.36 * hs, 0.48 * hs, h(0, 0.1, -0.25))
    snout = tube([h(0, 0.05, -0.5), h(0, 0.0, -0.5 - 0.55 * SN), h(0, -0.02, -0.5 - 1.0 * SN)], [0.3 * hs, 0.26 * hs, 0.22 * hs], k=0.08)
    head = head.su(snout, 0.16)
    head = head.su(ellipsoid(0.28 * hs, 0.24 * hs, 0.3 * hs, h(0.24, -0.02, -0.38)).mirror_x(), 0.14)
    head = head.su(capsule(h(0.18, 0.3, -0.68), h(0.3, 0.36, -0.28), 0.09 * hs).mirror_x(), 0.1)
    if st == "lung":
        head = head.su(ellipsoid(0.32 * hs, 0.22 * hs, 0.22 * hs, h(0, 0.12, -0.45 - 1.0 * SN)), 0.1)      # upturned nose bulb
        head = head.su(sphere(0.13 * hs, h(0.14, 0.2, -0.5 - 1.0 * SN)).mirror_x(), 0.06)
        head = head.ss(sphere(0.07 * hs, h(0.15, 0.24, -0.6 - 1.0 * SN)).mirror_x(), 0.02)
    else:
        head = head.su(sphere(0.09 * hs, h(0.12, 0.08, -0.48 - 1.0 * SN)).mirror_x(), 0.06)
        head = head.ss(sphere(0.04 * hs, h(0.13, 0.1, -0.56 - 1.0 * SN)).mirror_x(), 0.02)
    head = head.ss(sphere(0.11 * hs, h(0.27, 0.18, -0.62)).mirror_x(), 0.05)
    if st == "levi":
        for k in range(4):
            head = head.su(blade_fin(h(0, 0.36 - 0.02 * k, -0.6 + 0.28 * k), (0, 1, 0.6), (0.3 + 0.08 * k) * hs, 0.1 * hs, (1, 0, 0), flat=0.3, back=(0, 0, 1)), 0.05)
        head = head.su(ellipsoid(0.16 * hs, 0.1 * hs, 0.5 * hs, h(0.3, 0.3, -0.45)).mirror_x(), 0.08)
    head = head.si(plane((0, -1, 0), -(hc[1] - 0.15 * hs)), 0.03)
    H.piece("HeadP", "Head", head, col="primary", tris=2000, res=140, role="head", pattern=band_y(hc[1] - 0.3 * hs, hc[1] + 0.5 * hs, 1.0, 0.86))

    H.bone("Jaw", "Head", tuple(h(0, -0.1, -0.15)))
    jaw = tube([h(0, -0.22, -0.2), h(0, -0.25, -0.6 - 0.4 * SN), h(0, -0.23, -0.45 - 0.92 * SN)], [0.25 * hs, 0.19 * hs, 0.15 * hs], k=0.08)
    jaw = jaw.su(capsule(h(0.23, -0.17, -0.15), h(0.16, -0.22, -0.5 - 0.5 * SN), 0.075 * hs).mirror_x(), 0.08)
    if st == "lung":   # beard
        for k in range(5):
            x = -0.2 + 0.1 * k
            q = h(x, -0.3, -0.35 - 0.12 * abs(x))
            jaw = jaw.su(flat_tube([q, q + V(x * 0.4, -0.3, 0.2) * hs, q + V(x * 0.6, -0.5, 0.5) * hs], [0.07 * hs, 0.05 * hs, 0.012 * hs], (1, 0, 0), flat=0.5), 0.04)
    jaw = jaw.si(plane((0, 1, 0), hc[1] - 0.16 * hs), 0.03)
    H.piece("JawP", "Jaw", jaw, col="primary", tris=900, role="jaw", pri=1.3)
    H.prim("Mouth", "Head", "Ellipsoid", (0.38 * hs, 0.05 * hs, (0.3 + 0.9 * SN) * hs), h(0, -0.175, -0.25 - 0.5 * SN), col="mouth", mat="hard", role="mouth", pri=2.3)
    tu = []
    for i in range(5):
        u = (i + 0.5) / 5
        z = -0.5 - u * 0.9 * SN
        wx = 0.22 - 0.08 * u
        ln = 0.12 if i != 3 else (0.24 if st in ("levi", "sea", "basilisk") else 0.18)
        tu.append(round_cone(h(wx, -0.12, z), h(wx - 0.01, -0.12 - ln, z - 0.01), 0.04 * hs, 0.008 * hs))
        tu.append(round_cone(h(wx - 0.04, -0.21, z + 0.06), h(wx - 0.05, -0.21 + ln * 0.75, z + 0.05), 0.034 * hs, 0.008 * hs))
    # (lower teeth ride with the head here: one part; they sit inside the closed mouth line)
    H.piece("Teeth", "Head", union_hard(tu[0::2]).mirror_x(), col="tooth", mat="hard", tris=380, role="tooth", pri=2.0, ao=False, smooth=2)
    H.piece("TeethL", "Jaw", union_hard(tu[1::2]).mirror_x(), col="tooth", mat="hard", tris=340, role="tooth", pri=2.1, ao=False, smooth=2)
    H.eyes("Head", h(0.29, 0.19, -0.64), 0.1 * hs * (1.15 if st == "lung" else 1.0), col="iris", pupil="slit", look=(0.55, 0.05, -1.0))

    # head ornaments
    orn = None
    ocol = "horn"
    if st == "lung":   # antlers
        ant = []
        base = [h(0.2, 0.32, -0.2), h(0.3, 0.75, 0.15), h(0.38, 1.0, 0.65), h(0.36, 1.12, 1.1)]
        ant.append(curved_horn(base, 0.09 * hs, 0.02 * hs))
        ant.append(curved_horn([h(0.3, 0.75, 0.15), h(0.45, 1.0, -0.05), h(0.5, 1.18, -0.08)], 0.06 * hs, 0.015 * hs))
        ant.append(curved_horn([h(0.37, 0.98, 0.6), h(0.55, 1.2, 0.55), h(0.62, 1.38, 0.6)], 0.05 * hs, 0.012 * hs))
        orn = union_hard(ant).mirror_x()
    elif st == "wyrm":
        orn = union_hard([curved_horn([h(0.2, 0.33, -0.25), h(0.32, 0.5, 0.12), h(0.36, 0.58, 0.55), h(0.3, 0.8, 0.95)], 0.12 * hs, 0.015 * hs),
                          curved_horn([h(0.34, 0.1, -0.12), h(0.55, 0.05, 0.2), h(0.68, 0.12, 0.5)], 0.075 * hs, 0.012 * hs)]).mirror_x()
    elif st == "levi":
        hl = []
        for k in range(4):
            hl.append(curved_horn([h(0.3, 0.25 - 0.05 * k, -0.2 + 0.12 * k), h(0.55 + 0.05 * k, 0.32 - 0.1 * k, 0.15 + 0.15 * k), h(0.75 + 0.1 * k, 0.45 - 0.15 * k, 0.55 + 0.15 * k)],
                                  0.09 * hs, 0.012 * hs))
        orn = union_hard(hl).mirror_x()
    elif st == "basilisk":
        ocol = "secondary"
        cr = []
        for k in range(7):
            a = math.radians(-70 + k * 23.3)
            base = h(0.3 * math.sin(a), 0.3, -0.15 + 0.12 * (1 - math.cos(a)))
            tip = base + V(math.sin(a) * 0.35, 0.55 + 0.25 * math.cos(a), 0.25) * hs
            cr.append(round_cone(base, tip, 0.09 * hs, 0.015 * hs))
        crest = union_hard(cr)
        crest = crest.su(squash(ellipsoid(0.38 * hs, 0.32 * hs, 0.12 * hs, h(0, 0.55, 0.0)), h(0, 0.55, 0.0), (0, 0, 1), 0.5), 0.06)
        orn = crest
    elif st == "sea":
        ocol = "secondary"
        fr = []
        for k in range(4):
            a = math.radians(-35 + 25 * k)
            q0 = h(0.3, 0.05, -0.1)
            tip = q0 + V(math.cos(a) * 0.6, math.sin(a) * 0.65, 0.45) * hs
            fr.append(round_cone(q0, tip, 0.05 * hs, 0.015 * hs))
        tips = [h(0.3, 0.05, -0.1) + V(math.cos(math.radians(-35 + 25 * k)) * 0.6, math.sin(math.radians(-35 + 25 * k)) * 0.65, 0.45) * hs for k in range(4)]
        fr.append(fan(h(0.28, 0.05, -0.15), tips, 0.025 * hs))
        crest = union_hard([round_cone(h(0, 0.3, -0.5 + 0.25 * k), h(0, 0.75 - 0.05 * k, -0.25 + 0.3 * k), 0.04 * hs, 0.015 * hs) for k in range(4)]
                           + [fan(h(0, 0.3, -0.55), [h(0, 0.75 - 0.05 * k, -0.25 + 0.3 * k) for k in range(4)] + [h(0, 0.3, 0.6)], 0.025 * hs)])
        orn = union_hard(fr).mirror_x().su(crest, 0.03)
    if orn is not None:
        H.piece("Crest", "Head", orn, col=ocol, mat="hard" if ocol == "horn" else "skin", tris=1000, res=130, role="horn", pri=1.3)
    whisk = []
    if st == "lung":
        # mane: flowing tufts behind the cheeks and down the nape
        mane = None
        for k in range(9):
            a = math.radians(-60 + k * 20)
            q = h(0.32 * math.cos(a) * (1 if k % 2 else 0.9), 0.15 + 0.32 * math.sin(a), 0.0)
            for sx in (1, -1):
                qq = hc + (q - hc) * V(sx, 1, 1)
                tip = qq + V(sx * (0.25 + 0.2 * math.cos(a)), 0.15 * math.sin(a) - 0.05, 0.85 + 0.15 * math.sin(k)) * hs
                f_ = flat_tube([qq, (qq + tip) / 2 + V(0, 0.08, 0) * hs, tip], [0.14 * hs, 0.1 * hs, 0.015 * hs], (sx, 0.2, 0), flat=0.45)
                mane = f_ if mane is None else mane.su(f_, 0.05)
        H.piece("Mane", "Head", mane, col="secondary", mat="skin", tris=1400, res=130, role="mane", pri=1.2)
        # whiskers on their own bones so they trail
        wb = h(0.24, 0.02, -0.38 - 1.0 * SN)
        H.mbone("Whisker#", "Head", tuple(wb))
        wpts = [wb, wb + V(0.35, -0.05, -0.2) * hs, wb + V(0.85, -0.2, 0.25) * hs, wb + V(1.2, -0.45, 1.1) * hs, wb + V(1.35, -0.75, 1.9) * hs]
        H.mpiece("Whisker#", "Whisker#", tube(wpts, [0.05 * hs, 0.045 * hs, 0.035 * hs, 0.025 * hs, 0.01 * hs]), col="secondary", mat="skin", tris=380, role="detail", pri=1.6)
        whisk = [("WhiskerR", 1), ("WhiskerL", -1)]

    # ------------------------------------------------------------------ legs
    legs = []
    nl = P["legs"]
    if nl:
        idx = [3] if nl == 2 else [3, int(n * 0.55)]
        for li, k in enumerate(idx):
            c = (pts[k - 1] + pts[k]) / 2 if li == 0 else pts[k]
            r = rad[k]
            LG = P["leg"]
            sh = c + V(r * 0.7, -r * 0.2, 0)
            kn = sh + V(0.45, -0.75, -0.25) * s * LG
            ft = kn + V(0.1, -0.7, -0.2) * s * LG
            nm = "F" if li == 0 else "B"
            H.mbone(f"Leg{nm}#", link_bone(k - 1) if li == 0 else link_bone(k), tuple(sh))
            H.mbone(f"Low{nm}#", f"Leg{nm}#", tuple(kn))
            up = round_cone(sh, kn, 0.26 * s * LG, 0.16 * s * LG).su(ellipsoid(0.2 * s, 0.32 * s, 0.24 * s, sh + (kn - sh) * 0.4), 0.1)
            if st == "lung":
                up = up.su(flat_tube([kn + V(0, 0.05, 0.05) * s, kn + V(0.1, 0.0, 0.35) * s, kn + V(0.12, -0.12, 0.6) * s],
                                     [0.1 * s, 0.07 * s, 0.015 * s], (1, 0, 0), flat=0.4), 0.04)   # elbow flame tuft
            H.mpiece(f"Leg{nm}#", f"Leg{nm}#", up, col="primary", tris=450, role="limb")
            lo = round_cone(kn, ft, 0.16 * s * LG, 0.12 * s * LG)
            pc = ft + V(0, -0.05, -0.08) * s
            lo = lo.su(ellipsoid(0.2 * s, 0.12 * s, 0.22 * s, pc), 0.06)
            core = lo
            tal = []
            for j, a in enumerate((-0.5, -0.15, 0.2, 0.55)):
                dd = nrm(V(math.sin(a), -0.15, -math.cos(a)))
                p1 = pc + dd * 0.3 * s
                lo = lo.su(round_cone(pc, p1, 0.07 * s, 0.05 * s), 0.03)
                lo = lo.su(curved_horn([p1, p1 + dd * 0.1 * s, p1 + dd * 0.16 * s - V(0, 0.09, 0) * s], 0.045 * s, 0.01 * s), 0.015)
            H.mpiece(f"Foot{nm}#", f"Low{nm}#", lo, col="primary", tris=550, role="foot", pattern=outside(core, 0.03, 0.3, 0.05))
            legs += [(f"Leg{nm}R", f"Low{nm}R", 1), (f"Leg{nm}L", f"Low{nm}L", -1)]

    # ------------------------------------------------------------------ feathered wings (amphiptere)
    wings = []
    if P["wings"]:
        S0 = pts[3] + V(rad[3] * 0.6, rad[3] * 0.55, 0)
        WS = P["wings"] if isinstance(P["wings"], float) else 1.0
        E = S0 + V(1.4, 0.9, 0.3) * s * WS
        Wr = E + V(1.6, 0.7, -0.3) * s * WS
        H.mbone("Wing#", link_bone(3), tuple(S0))
        H.mbone("Hand#", "Wing#", tuple(Wr))
        nrmv = nrm(V(0.1, 1.0, 0.25))
        arm = round_cone(S0, E, 0.2 * s, 0.14 * s).su(round_cone(E, Wr, 0.14 * s, 0.1 * s), 0.06)
        for k in range(13):
            u = k / 12
            p0 = S0 + (E - S0) * (u * 2) if u < 0.5 else E + (Wr - E) * ((u - 0.5) * 2)
            arm = arm.su(feather(p0 - nrmv * 0.015 * k * s, V(-0.1 * u, -0.15, 1.0), (1.9 - 0.4 * u) * s * WS, 0.5 * s, nrmv, th=0.05 * s), 0.03)
        for k in range(6):
            u = k / 5
            p0 = S0 + (E - S0) * (0.1 + u * 0.9)
            arm = arm.su(feather(p0 + V(0, 0.06, 0.1) * s, V(0.1, -0.1, 1.0), 0.9 * s * WS, 0.4 * s, nrmv, th=0.05 * s), 0.03)
        H.mpiece("WingArm#", "Wing#", arm, col="secondary", mat="skin", tris=1500, res=150, role="wing", pri=1.2, smooth=2,
                 pattern=stripes(lambda Q: Q[:, 2] / s, 1.0, width=0.2, depth=0.2))
        hand = round_cone(Wr - (Wr - E) * 0.2, Wr + V(0.8, 0.1, -0.05) * s * WS, 0.1 * s, 0.05 * s)
        for k in range(7):
            a = math.radians(-8 + k * 13)
            d = nrm(V(math.cos(a), -0.12, math.sin(a) * 1.1))
            hand = hand.su(feather(Wr + V(0.12 * (6 - k) / 6, 0.0, 0) * s - nrmv * 0.015 * k * s, d, (2.6 - 0.15 * k) * s * WS, 0.42 * s, nrmv, th=0.05 * s, curl=0.2 * s), 0.03)
        H.mpiece("WingHand#", "Hand#", hand, col="secondary", mat="skin", tris=1400, res=150, role="wing", pri=1.25, smooth=2)
        wings = [("WingR", "HandR", 1), ("WingL", "HandL", -1)]

    # ------------------------------------------------------------------ sockets, rig, motion
    H.socket("mouth", h(0, -0.15, -0.6 - 1.0 * SN), "Jaw")
    H.socket("head", h(0, 0.5, -0.3), "Head")
    H.socket("seat", tuple(pts[3] + V(0, rad[3] + 0.15 * s, 0)), "Body")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": chain[-4:], "neck": ["Neck1", "Neck2"], "spine": chain})
    height = float(max(p[1] for p in pts)) + 0.5 * s
    mode = P["mode"]
    mm.serpent(H, chain, head="Head", jaw="Jaw", height=height, mode=mode, amp=0.3 if mode != "slither" else 0.26, lat=0.08,
               period=1.6 if mode != "slither" else 1.4, legs=legs, lift=0.15 if mode == "fly" else 0.0, fins=[], whiskers=whisk, neck=["Neck1", "Neck2"])
    if wings:
        def flap(t):
            pose = {}
            mm.wing_flap(pose, wings, t / 0.9, 0.9)
            return pose
        mm.overlay(H, "Move", flap)
        mm.overlay(H, "Idle", lambda t: (lambda p: (mm.wing_flap(p, wings, t / 2.0, 0.35), p)[1])({}))
        H.rig["wings"] = [{"bone": a, "side": sd} for a, hb, sd in wings]
    return H


LUNG = [(0, 3.4, -3.2), (0, 3.0, -2.2), (0, 2.1, -1.0), (0, 1.5, 0.6), (0, 2.1, 2.2), (0, 2.6, 3.8), (0, 2.0, 5.4), (0, 1.2, 6.8), (0, 1.0, 8.4), (0, 1.5, 9.8)]


@hero("chinese dragon", "dragons")
def chinese_dragon():
    H = _serpent("chinese dragon", ctrl=LUNG, n=12, r0=0.55, rmax=0.76, rtail=0.14, style="lung", head=1.5, snout=0.95, legs=4, leg=1.0,
                 dorsal="mane", mode="fly", gait="fly",
                 preview={"primary": "#DC2626", "secondary": "#FACC15", "horn": "#F4E2B0", "iris": "#FACC15"})
    H.mount = {"seat": "Torso", "saddle": {"pos": H.sockets["seat"][0], "size": (0.8, 0.2, 1.0)}}
    return H


SEA = [(0, 4.2, -3.0), (0, 3.6, -2.2), (0, 2.2, -1.3), (0, 0.6, -0.6), (0, 0.3, 0.6), (0, 1.6, 1.6), (0, 2.0, 2.8), (0, 1.0, 3.9),
       (0, 0.4, 4.8), (0, 0.6, 6.0), (0, 1.3, 6.9), (0, 1.0, 7.8), (0, 0.5, 8.6)]


@hero("sea serpent", "dragons")
def sea_serpent():
    return _serpent("sea serpent", ctrl=SEA, n=13, r0=0.55, rmax=0.78, rtail=0.12, style="sea", head=1.4, snout=1.0, legs=0, dorsal="fin",
                    mode="swim", gait="swim", tuft=True,
                    preview={"primary": "#0F766E", "secondary": "#99F6E4", "iris": "#FDE047"})


LEVI = [(0, 4.8, -3.6), (0, 4.2, -2.6), (0, 2.6, -1.6), (0, 0.9, -0.6), (0, 0.6, 0.9), (0, 2.0, 2.2), (0, 2.4, 3.6), (0, 1.2, 4.9),
        (0, 0.6, 6.0), (0, 0.9, 7.3), (0, 1.8, 8.3), (0, 1.6, 9.4), (0, 0.8, 10.2)]


@hero("leviathan", "dragons")
def leviathan():
    return _serpent("leviathan", ctrl=LEVI, n=13, r0=0.85, rmax=1.15, rtail=0.16, style="levi", head=1.9, snout=1.1, legs=0, dorsal="plates",
                    mode="swim", gait="swim", tuft=True,
                    preview={"primary": "#1E3A8A", "secondary": "#38BDF8", "horn": "#D9E4EC", "iris": "#38BDF8"})


LIND = [(0, 3.2, -3.0), (0, 2.6, -2.2), (0, 1.4, -1.3), (0, 0.75, 0.0), (0.6, 0.6, 1.4), (-0.2, 0.55, 2.8), (-1.0, 0.5, 3.9), (-0.6, 0.45, 5.2),
        (0.6, 0.4, 6.0), (1.4, 0.35, 6.8)]


@hero("lindworm", "dragons")
def lindworm():
    return _serpent("lindworm", ctrl=LIND, n=11, r0=0.52, rmax=0.7, rtail=0.1, style="wyrm", head=1.4, snout=1.0, legs=2, leg=1.0,
                    dorsal="spines", mode="slither", gait="slither", tuft=False,
                    preview={"primary": "#4D7C0F", "secondary": "#D9F99D", "horn": "#EFE3C8", "iris": "#F2C230"})


AMPH = [(0, 3.6, -2.6), (0, 3.1, -1.9), (0, 2.3, -1.0), (0, 1.9, 0.2), (0, 2.2, 1.4), (0, 2.0, 2.6), (0, 1.3, 3.6), (0, 0.9, 4.8), (0, 1.2, 6.0)]


@hero("amphiptere", "dragons")
def amphiptere():
    return _serpent("amphiptere", ctrl=AMPH, n=10, r0=0.36, rmax=0.46, rtail=0.08, style="wyrm", head=1.0, snout=0.9, legs=0, wings=1.0,
                    dorsal="spines", mode="fly", gait="fly", tuft=True,
                    preview={"primary": "#0F766E", "secondary": "#5EEAD4", "horn": "#EFE3C8", "iris": "#FDE047"})


BASI = [(0, 4.4, -1.6), (0, 3.9, -0.9), (0, 2.6, -0.4), (0, 1.0, 0.1), (0.9, 0.55, 1.0), (1.4, 0.5, 2.3), (0.6, 0.45, 3.4), (-0.8, 0.45, 3.6),
        (-1.6, 0.4, 2.6), (-1.5, 0.35, 1.2), (-0.6, 0.3, 0.2), (0.4, 0.3, -0.6)]


@hero("basilisk", "mythic")
def basilisk():
    return _serpent("basilisk", ctrl=BASI, n=13, r0=0.5, rmax=0.66, rtail=0.1, style="basilisk", head=1.25, snout=0.85, legs=0, dorsal="spines",
                    mode="slither", gait="slither", tuft=False,
                    preview={"primary": "#365314", "secondary": "#FACC15", "iris": "#FACC15"})




# ====================================================================================================== hydra
def _hydra_head(H, hb, hc, hs, sfx, center):
    def h(x, y, z):
        return hc + V(x, y, z) * hs
    head = ellipsoid(0.38 * hs, 0.34 * hs, 0.46 * hs, h(0, 0.1, -0.25))
    head = head.su(tube([h(0, 0.05, -0.5), h(0, 0.0, -1.0), h(0, -0.03, -1.35)], [0.28 * hs, 0.24 * hs, 0.18 * hs], k=0.08), 0.15)
    head = head.su(capsule(h(0.17, 0.28, -0.65), h(0.28, 0.34, -0.25), 0.08 * hs).mirror_x(), 0.08)
    head = head.ss(sphere(0.1 * hs, h(0.26, 0.17, -0.6)).mirror_x(), 0.04)
    head = head.ss(sphere(0.04 * hs, h(0.11, 0.08, -1.38)).mirror_x(), 0.02)
    for sx in (1, -1):
        head = head.su(curved_horn([h(0.18 * sx, 0.3, -0.25), h(0.3 * sx, 0.45, 0.1), h(0.32 * sx, 0.5, 0.45)], 0.08 * hs, 0.012 * hs), 0.03)
        head = head.su(blade_fin(h(0.32 * sx, 0.0, -0.1), (sx * 0.8, 0.1, 1.0), 0.4 * hs, 0.07 * hs, (0, 1, 0), 0.4), 0.04)
    head = head.si(plane((0, -1, 0), -(hc[1] - 0.15 * hs)), 0.03)
    H.piece("HeadP" + sfx, hb, head, col="primary", tris=1200, res=120, role="head")
    jb = "Jaw" + sfx
    H.bone(jb, hb, tuple(h(0, -0.1, -0.15)))
    jaw = tube([h(0, -0.21, -0.2), h(0, -0.24, -0.8), h(0, -0.21, -1.3)], [0.24 * hs, 0.18 * hs, 0.13 * hs], k=0.08)
    jaw = jaw.si(plane((0, 1, 0), hc[1] - 0.16 * hs), 0.03)
    H.piece("JawP" + sfx, jb, jaw, col="primary", tris=500, role="jaw", pri=1.4)
    tu = []
    for i in range(5):
        u = (i + 0.5) / 5
        z = -0.5 - u * 0.85
        wx = 0.21 - 0.08 * u
        ln = 0.12 if i != 3 else 0.22
        tu.append(round_cone(h(wx, -0.12, z), h(wx - 0.01, -0.12 - ln, z - 0.01), 0.04 * hs, 0.008 * hs))
    H.piece("Teeth" + sfx, hb, union_hard(tu).mirror_x(), col="tooth", mat="hard", tris=260, role="tooth", pri=2.0, ao=False, smooth=2)
    if center:
        H.prim("Mouth" + sfx, hb, "Ellipsoid", (0.36 * hs, 0.05 * hs, 1.0 * hs), h(0, -0.175, -0.8), col="mouth", mat="hard", role="mouth", pri=2.3)
        H.eyes(hb, h(0.28, 0.17, -0.62), 0.09 * hs, col="iris", pupil="slit", look=(0.55, 0.05, -1.0))
    else:
        H.mprim("Eye" + sfx + "#", hb, "Ball", (0.19 * hs,) * 3, h(0.28, 0.17, -0.62), col="iris", mat="hard", pri=1.8, role="eye")
    return jb, h(0, -0.15, -1.35)


@hero("hydra", "dragons")
def hydra():
    s = 1.0
    H = Hero("hydra", plan="Serpent", gait="heavy", tags=["dragon", "reptile", "hydra"])
    H.preview = {"primary": "#166534", "secondary": "#84CC16", "belly": "#C9E39A", "iris": "#F2E23A"}
    bodyY = 2.3
    H.body((0, bodyY, 0))
    torso = ellipsoid(1.25, 1.0, 1.9, (0, bodyY + 0.1, 0.2))
    torso = torso.su(ellipsoid(1.0, 0.9, 1.0, (0, bodyY + 0.35, -1.2)), 0.5)
    torso = torso.su(ellipsoid(0.5, 0.7, 0.8, (0.85, bodyY, 1.1)).mirror_x(), 0.35)
    torso = torso.su(ellipsoid(0.5, 0.7, 0.75, (0.9, bodyY + 0.1, -1.1)).mirror_x(), 0.35)
    torso = torso.su(round_cone((0, bodyY + 0.2, 1.6), (0, bodyY - 0.1, 2.5), 0.8, 0.55), 0.4)
    core = torso
    for i, z in enumerate(np.linspace(-0.6, 2.0, 6)):
        y = float(np.max([0])) + bodyY + 0.95 - 0.12 * max(0, z - 0.8)
        torso = torso.su(blade_fin(V(0, y, z), (0, 1, 0.4), 0.45 + 0.08 * math.sin(i), 0.17, (1, 0, 0), flat=0.32, back=(0, 0, 1)), 0.06)
    H.piece("Torso", "Body", torso, col="primary", tris=2200, res=128,
            pattern=combine(band_y(bodyY - 0.9, bodyY + 1.0, 1.0, 0.82), outside(core, 0.05, 0.45, 0.12),
                            stripes(lambda Q: Q[:, 2], 2.6, width=0.16, depth=0.3, region=lambda Q: np.clip((bodyY - 0.4 - Q[:, 1]) * 3, 0, 1))))
    legs = []
    for front, z in ((True, -1.1), (False, 1.1)):
        nm = "F" if front else "B"
        sh = V(1.0, bodyY - 0.05, z)
        kn = V(1.45, 0.9, z + (0.05 if front else -0.2))
        H.mbone(f"Leg{nm}#", "Body", tuple(sh))
        H.mbone(f"Low{nm}#", f"Leg{nm}#", tuple(kn))
        up = round_cone(sh + V(-0.15, 0.2, 0), kn, 0.55, 0.32).su(ellipsoid(0.42, 0.55, 0.5, sh + V(0.15, -0.3, 0)), 0.2)
        H.mpiece(f"Leg{nm}#", f"Leg{nm}#", up, col="primary", tris=600, role="limb", pattern=band_y(0, bodyY, 1.0, 0.85))
        c = V(1.5, 0.0, z - 0.25)
        lo = round_cone(kn, c + V(0, 0.3, 0.1), 0.32, 0.26)
        lo = lo.su(ellipsoid(0.38, 0.22, 0.42, c + V(0, 0.2, -0.05)), 0.1)
        fc = lo
        for a in (-0.5, 0.0, 0.5):
            d = nrm(V(math.sin(a), 0, -math.cos(a)))
            p1 = c + V(0, 0.12, 0) + d * 0.55
            lo = lo.su(round_cone(c + V(0, 0.18, 0) + d * 0.1, p1, 0.12, 0.09), 0.04)
            lo = lo.su(curved_horn([p1, p1 + d * 0.15, p1 + d * 0.25 - V(0, 0.12, 0)], 0.075, 0.012), 0.015)
        H.mpiece(f"Foot{nm}#", f"Low{nm}#", lo & plane((0, -1, 0), 0.0), col="primary", tris=600, role="foot", pattern=outside(fc, 0.04, 0.3, 0.05))
        legs += [(f"Leg{nm}R", f"Low{nm}R", 1), (f"Leg{nm}L", f"Low{nm}L", -1)]
    t0, t1, t2 = V(0, bodyY - 0.1, 2.4), V(0, bodyY - 0.7, 3.9), V(0.3, bodyY - 1.3, 5.2)
    H.bone("Tail1", "Body", tuple(t0))
    H.piece("TailA", "Tail1", round_cone(t0 - V(0, 0, 0.3), t1, 0.6, 0.38).su(round_cone(t1, t2, 0.38, 0.1), 0.1).su(spike(t2, t2 - t1, 0.35, 0.1), 0.05),
            col="primary", tris=750, role="tail", pri=1.4)
    # five necks fanning up from the chest, the centre one tallest
    necks, heads, jaws = [], [], []
    mouth = None
    for i in range(5):
        a = (i - 2) / 2.0
        base = V(0.42 * a, bodyY + 0.55, -1.5)
        top = V(2.5 * a, bodyY + 3.3 - 0.9 * abs(a) ** 1.5, -2.9 + 1.0 * abs(a))
        mid = (base + top) / 2 + V(-0.25 * a, 0.35, -0.45)
        nb, hb = f"Neck{i + 1}", f"Head{i + 1}"
        H.bone(nb, "Body", tuple(base))
        H.bone(hb, nb, tuple(top))
        neck = tube([base + V(0, -0.2, 0.35), mid, top + V(0, -0.05, 0.25)], [0.46, 0.33, 0.27], k=0.1)
        H.piece(f"NeckP{i + 1}", nb, neck, col="primary", tris=650, role="limb", pattern=band_y(bodyY, bodyY + 3, 1.0, 0.85))
        hc_ = top + V(0, 0.05, -0.05)
        jb, mth = _hydra_head(Shift(H, hc_[0]), hb, V(0, hc_[1], hc_[2]), 0.82, str(i + 1), i == 2)
        mth = mth + V(hc_[0], 0, 0)
        necks.append(nb)
        heads.append(hb)
        jaws.append(jb)
        if i == 2:
            mouth = mth
    H.socket("mouth", tuple(mouth), "Jaw3")
    H.socket("head", tuple(H.bpos("Head3") + V(0, 0.6, -0.2)), "Head3")
    H.socket("seat", (0, bodyY + 1.2, 0.3), "Body")
    H.rig.update({"head": "Head3", "jaw": "Jaw3", "tail": ["Tail1"], "neck": necks,
                  "legs": [{"hip": a, "knee": b, "side": sd} for a, b, sd in legs]})
    TAU = 2 * math.pi
    ql = []
    for a, b, sd in legs:
        front = "F" in a
        ph = (0.75 if sd > 0 else 0.25) if front else (0.5 if sd > 0 else 0.0)
        ql.append((a, b, None, ph, front))
    import motion
    motion.quadruped(H, ql, neck=None, head=None, jaw=None, tail=["Tail1"], stride=0.3, walk=1.4, height=bodyY + 1.0, attack="bite")

    def heads_f(rate, amp, strike=False):
        def f(t):
            pose = {}
            for j, (nb, hb, jb) in enumerate(zip(necks, heads, jaws)):
                ph = j * 1.3
                if strike:
                    k = math.sin(math.pi * min(max((t / 1.0) - 0.08 * abs(j - 2), 0) / 0.8, 1))
                    mm._add(pose, nb, (0, 0, 0, -0.45 * k + 0.15 * (1 - k) * 0, 0.1 * (j - 2) * k, 0))
                    mm._add(pose, hb, (0, 0, 0, -0.2 * k, 0, 0))
                    mm._add(pose, jb, (0, 0, 0, -0.6 * k, 0, 0))
                else:
                    mm._add(pose, nb, (0, 0, 0, amp * 0.6 * math.sin(t * rate + ph), amp * math.sin(t * rate * 0.5 + ph), amp * 0.5 * math.sin(t * rate * 0.7 + ph)))
                    mm._add(pose, hb, (0, 0, 0, amp * 0.6 * math.sin(t * rate * 1.3 + ph + 1), amp * 1.2 * math.sin(t * rate * 0.6 + ph), 0))
                    mm._add(pose, jb, (0, 0, 0, -0.15 * max(0.0, math.sin(t * rate * 0.5 + ph * 2)) ** 4, 0, 0))
            return pose
        return f
    mm.overlay(H, "Move", heads_f(TAU / 1.4 * 1.0, 0.14))
    mm.overlay(H, "Idle", heads_f(TAU / 4.8 * 2, 0.16))
    mm.overlay(H, "Attack", heads_f(0, 0, strike=True))
    return H
