"""Small mammals: rodents (rat, mouse, hamster, guinea pig, squirrel, chipmunk, groundhog, beaver, capybara, porcupine),
hedgehog, mustelids and friends (otter, weasel, badger, skunk, wolverine, raccoon, red panda, mongoose), opossum,
armadillo, anteater, sloth, and the hoppers (rabbit, kangaroo).

_critter(): one parametric small-quadruped sculpt. A two-piece body (chest on Body, haunch on a Spine bone; each hides
a shrunken extension inside the other so the back can flex in a bounding gait without opening a gap), a short neck,
a rodent / mustelid skull with a snout of any length and bluntness, nose leather, incisors, beady eyes, whiskers,
ears on bones (round discs, nubs, points, tufts), three-segment legs with fingered paws / long hind feet / claws,
and a three-bone tail (bald, bushy S-curve, ringed, plume, paddle, thick rudder, giant flag, armoured).
Features: cheek pouches, porcupine quills, hedgehog spines, armadillo shell bands, face masks / stripes / belly
overlays in the word's secondary colour.

_hopper(): rabbits and kangaroos: hunched or upright body, huge folded hind legs with long feet, small forelegs,
long ears, a cotton or a long balancing tail; hop gait and kick attacks.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from kit import hero, stripes, spots, gradient, combine, _mirror_sdf
from map import NOTFOOD
import motion_canines as MC

NOSE = [0.13, 0.11, 0.11]
PINK = [0.9, 0.6, 0.62]
INCISOR = [0.97, 0.94, 0.86]
ORANGE_TOOTH = [0.92, 0.55, 0.18]


def A(*a):
    return np.array(a, float)


def T(a):
    return tuple(float(x) for x in a)


def overlay(base, region, off):
    return base.round(off) & region


def cones(base_pts, dirs, length, r0, r1=0.004):
    """Union of many tapered spikes (quills / spines): evaluated vectorised point x spike."""
    B = np.asarray(base_pts, float)
    D = np.asarray(dirs, float)
    D = D / np.linalg.norm(D, axis=1, keepdims=True)
    L = np.broadcast_to(np.asarray(length, float), (len(B),)).copy()
    E = B + D * L[:, None]

    def f(p):
        out = np.full(len(p), 1e9)
        for i in range(0, len(B), 16):  # chunks of spikes
            b = B[i:i + 16][None]
            e = E[i:i + 16][None]
            ba = e - b
            pa = p[:, None, :] - b
            h = np.clip((pa * ba).sum(-1) / (ba * ba).sum(-1), 0, 1)
            d = np.linalg.norm(pa - ba * h[..., None], axis=-1) - (r0 + (r1 - r0) * h)
            out = np.minimum(out, d.min(1))
        return out * 0.8

    return SDF(f)


def fib_dirs(n, seed=0):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = math.pi * (1 + 5 ** 0.5) * i + seed
    return np.column_stack([np.cos(th) * np.sin(phi), np.cos(phi), np.sin(th) * np.sin(phi)])


CR = dict(
    s=1.0, leg=1.0, body=1.0, girth=1.0, pear=1.15, arch=0.0, neck=0.4, head=1.0, snout=1.0, sw=1.0, blunt=0.3, dome=0.0,
    cheeks=0.0, ear="round", ear_size=1.0, eye=1.0, eyecol="pupil", nose=None, teeth="incisor", whiskers=True,
    tail="bald", tail_len=1.0, tail_thick=1.0, tail_col="primary", claws=0.0, foot=1.0, fluff=0.0, belly=0.9,
    marks=None, pattern=None, quills=False, spines=False, shell=False, front_up=0.0, legcol=None,
    gait="bound", attack="bite", wag=0.0, preview=None, tags=(),
)


def _critter(hid, **kw):
    P = dict(CR)
    P.update(kw)
    s, LG, BL, G = P["s"], P["leg"], P["body"], P["girth"]
    PR, AR = P["pear"], P["arch"]
    H = MC.FastHero(hid, plan="Quadruped", gait="trot" if P["gait"] != "walk" else "trot", tags=["smallmammal"] + list(P["tags"]))
    H.preview = P["preview"] or {}
    marks = P["marks"] or {}
    fl = P["fluff"]

    def v(x, y, z):
        return A(x * s, y * s, z * s)

    def furry(sd, amp=1.0, freq=8.0, seed=0):
        return sd.noise(fl * amp * s, freq / s, seed) if fl > 0 else sd

    R = 0.55 * G
    legH = 0.42 * LG
    zc, zr = -0.62 * BL, 0.55 * BL
    yc = legH + 0.88 * R + P["front_up"] * 0.3
    yr = legH + R * PR + AR
    backY = max(yc + 0.88 * R, yr + R * PR)
    H.body(T(v(0, yc, 0)))

    def back_shade(Q):
        t = np.clip((Q[:, 1] / s - legH) / (2.2 * R), 0, 1)
        return 1.0 - (1.0 - P["belly"]) * t

    pat = None
    if P["pattern"] == "chipmunk":
        def pat(Q):
            x = Q[:, 0] / s
            on = np.clip((Q[:, 1] / s - (yr + 0.05)) / 0.15, 0, 1)
            band = np.zeros(len(Q))
            for c, w in ((0.0, 0.1), (0.26, 0.09), (-0.26, 0.09), (0.46, 0.08), (-0.46, 0.08)):
                band = np.maximum(band, np.clip(1 - np.abs(x - c) / w, 0, 1))
            return 1 - 0.75 * band * on
    elif P["pattern"] == "brindle":
        pat = stripes(lambda Q: Q[:, 2] / s, 3.0, width=0.3, depth=0.35, wobble=0.1, seed=2)
    elif P["pattern"] == "spots":
        pat = spots(0.25 * s, 0.07 * s, depth=0.6, seed=3)

    def skin(extra=None):
        return combine(back_shade, pat, extra)

    # ---------------------------------------------------------------- body (two pieces)
    chest = ellipsoid(0.85 * R, 0.88 * R, 0.95 * BL, T(v(0, yc, zc)))
    rump = ellipsoid(R * PR, R * PR, 1.0 * BL, T(v(0, yr, zr)))
    torso = chest.su(rump, 0.5 * R * s)
    if P["cheeks"] > 0:  # hamster: whole front is a round ball
        torso = torso.su(sphere(0.9 * R * s, T(v(0, yc + 0.05, zc - 0.25 * BL))), 0.3)
    torso = furry(torso, 1.0, 7, 1)
    zs = 0.12 * BL
    H.bone("Spine", "Body", T(v(0, (yc + yr) / 2, zs)))
    chestP = (torso & plane((0, 0, 1), zs * s)) | (torso.round(-0.05 * s) & plane((0, 0, 1), (zs + 0.45 * BL) * s))
    infl = SDF(lambda p: torso(p) - 0.018 * s * np.clip((p[:, 2] - zs * s) / (0.3 * s), 0, 1))
    rumpP = (infl & plane((0, 0, -1), -zs * s)) | (torso.round(-0.05 * s) & plane((0, 0, -1), (0.35 * BL - zs) * s))
    H.piece("Torso", "Body", chestP, col="primary", tris=1800, res=120, pattern=skin())
    H.piece("Haunch", "Spine", rumpP, col="primary", tris=1800, res=120, pattern=skin())
    oT = 0.04 * s
    if "belly" in marks:
        reg = (ellipsoid(1.2 * R, 0.55 * R, 1.9 * BL, T(v(0, legH + 0.05, -0.1))) | ellipsoid(0.8 * R, 0.7 * R, 0.5, T(v(0, yc - 0.1, zc - 0.7 * BL)))).noise(0.03 * s, 8 / s, 2)
        H.piece("Belly", "Body", overlay(chestP, reg, oT), col=marks["belly"], tris=700, role="body", pri=1.2)
    if "stripe" in marks:  # skunk: twin white stripes from the head down the back
        def reg_fn(z0, z1):
            b = box(0.55 * R * s, 2 * R * s, (z1 - z0) / 2 * s, T(v(0, backY, (z0 + z1) / 2)))
            return b - box(0.18 * R * s, 2 * R * s, (z1 - z0) / 2 * s + 0.1, T(v(0, backY + 0.25 * R, (z0 + z1) / 2)))
        H.piece("Stripe", "Body", overlay(chestP, reg_fn(-2.5 * BL, zs + 0.1) & plane((0, -1, 0), -(yc + 0.15 * R) * s), oT), col=marks["stripe"], tris=700, role="body", pri=1.2)
        H.piece("Stripe2", "Spine", overlay(rumpP, reg_fn(zs - 0.1, 2.5 * BL) & plane((0, -1, 0), -(yr + 0.2 * R) * s), oT), col=marks["stripe"], tris=700, role="body", pri=1.2)
    if "side" in marks:  # wolverine pale side band
        reg = (plane((0, 1, 0), (yr + 0.42 * R) * s) & plane((0, -1, 0), -(yr + 0.08 * R) * s) & plane((0, 0, -1), -(zc + 0.1 * BL) * s)).noise(0.03 * s, 7 / s, 5)
        H.piece("SideBand", "Body", overlay(chestP, reg, oT), col=marks["side"], tris=700, role="body", pri=1.2)
        H.piece("SideBand2", "Spine", overlay(rumpP, reg, oT), col=marks["side"], tris=700, role="body", pri=1.2)
    if "diag" in marks:  # anteater: dark band from the throat up and back over the shoulder
        n = A(0, 0.86, -0.5)
        p0 = A(0, yc - 0.05 * R, zc + 0.1 * BL) * s
        wd = 0.2 * R * s

        def band(p):
            u = (p - p0) @ n
            return np.abs(u) - wd

        reg = (SDF(band) & plane((0, -1, 0), -(legH + 0.2 * R) * s)).noise(0.02 * s, 7 / s, 6)
        H.piece("DiagBand", "Body", overlay(chestP, reg, oT), col=marks["diag"], tris=700, role="body", pri=1.2)
        H.piece("DiagBand2", "Spine", overlay(rumpP, reg, oT), col=marks["diag"], tris=700, role="body", pri=1.2)
    if P["quills"]:
        rng = np.random.default_rng(7)
        D = fib_dirs(160, 0.3)
        D = D[(D[:, 1] > -0.15)]
        base_c = A(0, yr, zr * 0.6) * s
        rad = A(R * PR * 0.98, R * PR * 0.98, 1.25 * BL) * s
        pts = base_c + D * rad
        pts = pts[pts[:, 2] > (zc - 0.2 * BL) * s]
        dirs = (pts - base_c) / rad ** 2 + A(0, 0.2, 1.4) / s
        dirs[:, 1] += 0.2
        Ls = (0.75 + 0.5 * rng.random(len(pts))) * s * (0.6 + 0.6 * np.clip((pts[:, 2] / s + 0.5) / 2.0, 0, 1))
        q = cones(pts, dirs, Ls, 0.045 * s)
        H.piece("Quills", "Spine", q, col="secondary", mat="hard", tris=2400, res=128, role="quills", pri=1.3,
                pattern=lambda Q: np.clip(0.35 + 0.65 * (np.linalg.norm((Q - base_c) / rad, axis=1) - 0.95) * 2.2, 0.3, 1.0))
    if P["spines"]:
        D = fib_dirs(300, 0.1)
        D = D[(D[:, 1] > -0.05)]
        cc = A(0, (yc + yr) / 2, (zc + zr) / 2 + 0.1) * s
        rad = A(R * 0.98, R * PR * 0.95, 1.28 * BL) * s
        D = D * A(1.0, 1.0, 1.6)
        D = D / np.linalg.norm(D, axis=1, keepdims=True)
        lo_t, hi_t = np.zeros(len(D)), np.full(len(D), 4.0 * s)
        for _ in range(30):  # bisection onto the (furry) torso surface
            mid = (lo_t + hi_t) / 2
            inside = torso(cc + D * mid[:, None]) < 0
            lo_t = np.where(inside, mid, lo_t)
            hi_t = np.where(inside, hi_t, mid)
        surf = cc + D * lo_t[:, None]
        e = 0.01 * s
        nrm = np.column_stack([(torso(surf + A(*dd) * e) - torso(surf - A(*dd) * e)) for dd in ((1, 0, 0), (0, 1, 0), (0, 0, 1))])
        nrm = nrm / np.linalg.norm(nrm, axis=1, keepdims=True)
        pts = surf + nrm * 0.02 * s
        keep = pts[:, 2] > (zc - 0.35 * BL) * s
        pts, nrm = pts[keep], nrm[keep]
        dirs = nrm + A(0, 0.05, 0.7)  # lie back toward the tail but stand clear of the coat
        coat = torso.round(0.04 * s) & plane((0, -1, 0), -(yc - 0.15 * R) * s)
        coat = coat & plane((0, 0, -1), -(zc - 0.45 * BL) * s)
        spat = lambda Q: np.clip(0.3 + 0.7 * (np.linalg.norm((Q - cc) / rad, axis=1) - 0.95) * 3.0, 0.3, 1.0)
        # two pieces so each spike keeps enough triangles after decimation
        sp1 = cones(pts[0::2], dirs[0::2], 0.36 * s, 0.1 * s, 0.012 * s)
        sp2 = cones(pts[1::2], dirs[1::2], 0.36 * s, 0.1 * s, 0.012 * s)
        H.piece("Spines", "Spine", (coat | sp1), col="primary", mat="hard", tris=2600, res=136, role="spines", pri=1.3, pattern=spat)
        H.piece("Spines2", "Spine", sp2 & coat.round(0.5 * s), col="primary", mat="hard", tris=2600, res=136, role="spines", pri=1.3, pattern=spat)
    if P["shell"]:  # armadillo carapace: front shield, banded middle, rear shield
        sh_ = ellipsoid(R * 1.08, R * PR * 1.08, 1.6 * BL, T(v(0, (yc + yr) / 2 + 0.05, (zc + zr) / 2)))
        sh_ = sh_ & plane((0, -1, 0), -(legH + 0.45 * R) * s)
        bands = None
        for i in range(6):
            z = (-0.25 + i * 0.13) * BL * s
            g = box(2 * R * s, 2 * R * s, 0.018 * s, (0, (yc + yr) / 2 * s, z))
            bands = g if bands is None else bands | g
        sh_ = sh_ - bands
        H.piece("Shell", "Body", sh_ & plane((0, 0, 1), (zs + 0.15) * s), col="secondary", mat="hard", tris=1600, role="shell", pri=1.25,
                pattern=stripes(lambda Q: Q[:, 2] / s, 7.7, width=0.18, depth=0.3))
        H.piece("ShellB", "Spine", sh_.round(0.02 * s) & plane((0, 0, -1), -(zs + 0.05) * s), col="secondary", mat="hard", tris=1400, role="shell", pri=1.25,
                pattern=stripes(lambda Q: Q[:, 2] / s, 7.7, width=0.18, depth=0.3))

    # ---------------------------------------------------------------- legs
    lc = P["legcol"] or "primary"
    lpat = None if P["legcol"] else skin()
    CL = P["claws"]
    FT = P["foot"]

    def paw(c, front, k=1.0):
        c = A(*c)
        k = k * s * (0.8 + 0.2 * G)
        p = ellipsoid(0.12 * k, 0.07 * k, (0.14 if front else 0.28 * FT) * k, T(c + A(0, 0.06, (-0.04 if front else 0.0)) * k))
        tz = -0.16 if front else -0.28 * FT - 0.04
        for dx in (-0.08, -0.027, 0.027, 0.08):
            p = p.su(ellipsoid(0.04 * k, 0.04 * k, 0.07 * k, T(c + A(dx * 1.1, 0.04, tz + abs(dx) * 0.5) * k)), 0.03 * k)
        if CL > 0:
            for dx in (-0.08, -0.027, 0.027, 0.08):
                b = c + A(dx * 1.1, 0.05, tz - 0.04 + abs(dx) * 0.5) * k
                p = p | round_cone(T(b), T(b + A(0, -0.05, -0.12 * CL) * k), 0.022 * k, 0.006 * k)
        return p & plane((0, -1, 0), 0.0)

    Wd = 0.85 * R
    sh = v(0.62 * Wd, yc + 0.25 * R, zc - 0.4 * BL)
    el = v(0.68 * Wd, legH + 0.1 + 0.12 * LG, zc - 0.32 * BL)
    wr = v(0.62 * Wd, 0.1 * LG + 0.05, zc - 0.42 * BL)
    fpaw = A(wr[0], 0, wr[2] - 0.03 * s)
    H.mbone("ShoulderF#", "Body", T(sh))
    H.mbone("ElbowF#", "ShoulderF#", T(el))
    H.mbone("WristF#", "ElbowF#", T(wr))
    lr = 0.13 * s * (0.7 + 0.3 * G)
    up = round_cone(T(sh + v(0, 0.15, 0.1)), T(el), lr * 1.6, lr)
    H.mpiece("UpperF#", "ShoulderF#", furry(up, 0.6, 9, 2), col=lc, tris=500, role="limb", pattern=lpat)
    fo = round_cone(T(el), T(wr), lr, lr * 0.75)
    fo = fo.su(paw(fpaw, True), 0.05 * s)
    H.mpiece("ForeF#", "ElbowF#", furry(fo, 0.4, 10, 3), col=lc, tris=650, role="limb", pattern=lpat)

    hp = v(0.6 * R * PR, yr + 0.05, zr + 0.2 * BL)
    kn = v(0.75 * R * PR, legH + 0.22 * LG + 0.1, zr - 0.12 * BL)
    an = v(0.62 * R * PR, 0.09 * LG + 0.06, zr + 0.25 * BL)
    bpaw = A(an[0], 0, an[2] - 0.12 * FT * s)
    H.mbone("HipB#", "Spine", T(hp))
    H.mbone("KneeB#", "HipB#", T(kn))
    H.mbone("HockB#", "KneeB#", T(an))
    th = round_cone(T(hp + v(0, 0.1, 0.05)), T(kn), lr * 2.4 * PR, lr * 1.3)
    th = th.su(ellipsoid(lr * 1.8 * PR / s, R * 0.7, lr * 2.2 / s, T((hp + kn) / 2 + v(0, 0.02, 0.12))), 0.1 * s)
    H.mpiece("Thigh#", "HipB#", furry(th, 0.8, 8, 5), col=lc if P["legcol"] else "primary", tris=650, role="limb", pattern=lpat)
    sn = round_cone(T(kn), T(an), lr * 1.15, lr * 0.75)
    H.mpiece("Shin#", "KneeB#", furry(sn, 0.5, 10, 6), col=lc, tris=450, role="limb", pattern=lpat)
    ftp = round_cone(T(an), T(bpaw + v(0, 0.06, -0.1 * FT)), lr * 0.75, lr * 0.6).su(paw(bpaw, False), 0.05 * s)
    H.mpiece("PawB#", "HockB#", furry(ftp, 0.3, 12, 7), col=lc, tris=550, role="foot", pattern=lpat)

    # ---------------------------------------------------------------- head
    NK = P["neck"]
    nb = v(0, yc + 0.3 * R, zc - 0.7 * BL)
    H.bone("Neck", "Body", T(nb))
    hs = P["head"] * s * 0.95
    hc = nb + v(0, 0.25 * NK + 0.05 + 0.4 * P["front_up"], -0.45 * NK - 0.1)
    if NK > 0.25:
        neck = round_cone(T(nb + v(0, -0.1, 0.25)), T(hc + v(0, -0.05, 0.05)), 0.7 * R * s, 0.33 * hs)
        H.piece("NeckP", "Neck", furry(neck, 0.8, 8, 8), col="primary", tris=600, role="limb", pattern=skin())
    H.bone("Head", "Neck", T(hc))
    SN, SW, BLU, DM = P["snout"], P["sw"], P["blunt"], P["dome"]

    def hw(x, y, z):
        return T(hc + A(x, y, z) * hs)

    def W(sd):
        return sd.scale(hs).at(*T(hc))

    sl = 0.5 * SN
    head = ellipsoid(0.36, 0.32 * (1 + 0.3 * DM), 0.4, (0, 0.05 + 0.05 * DM, -0.12))
    head = head.su(ellipsoid(0.2 + 0.1 * P["cheeks"], 0.18 + 0.08 * P["cheeks"], 0.22 + 0.06 * P["cheeks"], (0.18 + 0.08 * P["cheeks"], -0.08, -0.25)).mirror_x(), 0.12)
    tipr = 0.05 + 0.1 * BLU
    head = head.su(round_cone((0, -0.02, -0.38), (0, -0.08 - 0.03 * SN, -0.42 - sl), 0.25 * SW, tipr * SW), 0.12)
    head = head.ss(sphere(0.075 * P["eye"] + 0.01, (0.2, 0.08, -0.36)).mirror_x(), 0.03)
    headW = furry(W(head), 0.3, 12, 9)
    H.piece("HeadP", "Head", headW, col="primary", tris=1600, res=120, role="head", pattern=pat)
    regs = []
    if "face" in marks:  # pale face (red panda, opossum, sloth) incl. muzzle and brows
        reg = ellipsoid(0.32 * SW, 0.24, 0.25 + sl, (0, -0.06, -0.45 - 0.4 * sl)) | ellipsoid(0.08, 0.06, 0.06, (0.16, 0.2, -0.36)).mirror_x()
        reg = reg | ellipsoid(0.15, 0.12, 0.15, (0.26, -0.1, -0.25)).mirror_x()
        regs.append(("Face", reg, marks["face"], 0.03))
    if "facestripe" in marks:  # badger: white stripe over the crown + cheeks
        reg = box(0.07, 0.4, 0.8, (0, 0.3, -0.15)) | (ellipsoid(0.5, 0.12, 0.35, (0, -0.1, -0.25)) - ellipsoid(0.24, 0.3, 0.5, (0, -0.2, -0.45)))
        regs.append(("Face", reg, marks["facestripe"], 0.03))
    if "muzzle" in marks:
        reg = ellipsoid(0.3 * SW, 0.2, 0.25 + sl, (0, -0.12, -0.45 - 0.4 * sl)) & plane((0, 1, 0), -0.05)
        regs.append(("Muzzle", reg, marks["muzzle"], 0.03))
    if "mask" in marks:  # bandit mask band across the eyes (raccoon, ferret, sloth eye stripe)
        reg = ellipsoid(0.42, 0.11, 0.18, (0, 0.07, -0.33)).noise(0.01, 12, 3)
        regs.append(("Mask", reg, marks["mask"], 0.05 if regs else 0.03))
    for nm, reg, col, off in regs:
        H.piece(nm, "Head", overlay(headW, W(reg), off * s), col=col, tris=500, role="head", pri=1.3 + (0.05 if nm == "Mask" else 0))
    nosec = P["nose"] or NOSE
    nz = -0.42 - sl - tipr * SW * 0.6
    H.piece("Nose", "Head", W(ellipsoid(tipr * SW * 0.75 + 0.02, tipr * SW * 0.6 + 0.02, 0.05, (0, -0.06 - 0.03 * SN, nz))), col=nosec, mat="skin", tris=200,
            role="nose", pri=1.6, ao=False)
    jb = H.bone("Jaw", "Head", hw(0, -0.12, -0.2))
    jaw = ellipsoid(0.12 * SW, 0.06, 0.12 + 0.35 * sl, (0, -0.2 - 0.02 * SN, -0.32 - 0.5 * sl))
    H.piece("JawP", "Jaw", W(jaw), col=marks.get("face", marks.get("muzzle", "primary")), tris=300, role="jaw", pri=1.4)
    if P["teeth"]:
        tc = ORANGE_TOOTH if P["teeth"] == "orange" else INCISOR
        big = 1.6 if P["teeth"] == "orange" else 1.0
        inc = round_box(0.022 * big, 0.05 * big, 0.012, 0.008).at(0.024 * big, -0.14 - 0.03 * SN - 0.03 * big, nz + 0.07)
        H.mpiece("Incisor#", "Head", W(inc), col=tc, mat="hard", tris=150, role="tooth", pri=2.2, ao=False, smooth=1)
    er = 0.07 * P["eye"] * hs
    H.eyes("Head", hw(0.2, 0.08, -0.37), er, col=P["eyecol"], pupil="round" if P["eyecol"] != "pupil" else None, look=(0.55, 0.1, -1.0))
    if P["whiskers"]:
        wb = A(*hw(0.08 * SW + 0.06, -0.06 - 0.03 * SN, nz + 0.1))
        for i, (ang, el_) in enumerate(((18, 4), (30, -6))):
            L = 0.55 * hs
            H.mprim(f"Whisker{i}#", "Head", "Cylinder", (L, 0.012 * hs, 0.012 * hs), T(wb + A(L * 0.5 * math.cos(math.radians(ang)), math.sin(math.radians(el_)) * L * 0.5, L * 0.5 * math.sin(math.radians(ang)))),
                    rot=(0, -math.radians(ang), math.radians(el_)), col="white", mat="hard", pri=3.0, role="whisker")
    # ears
    et, ES = P["ear"], P["ear_size"]
    ears = []
    if et != "none":
        if et == "round":
            r = 0.2 * ES
            e = sphere(r).scale3(1, 1, 0.28).ss(sphere(r * 0.78).scale3(1, 1, 0.22).at(0, 0, -r * 0.18), 0.02)
            e = e.at(0, r * 0.75, 0).rot(-5, -25, -25)
            ep = (0.2, 0.26, -0.08)
        elif et == "small":
            r = 0.1 * ES
            e = sphere(r).scale3(1, 0.85, 0.5).at(0, r * 0.4, 0).rot(0, -30, -30)
            ep = (0.26, 0.24, -0.06)
        elif et in ("point", "tuft"):
            Lh = 0.3 * ES
            e = round_cone((0, 0, 0), (0, Lh, 0), 0.12 * ES, 0.025).scale3(1, 1, 0.45)
            e = e.ss(round_cone((0, 0.03, 0), (0, Lh * 0.9, 0), 0.08 * ES, 0.015).scale3(1, 1, 0.35).at(0, 0, -0.04), 0.01)
            if et == "tuft":
                e = e.su(round_cone((0, Lh * 0.8, 0), (0.0, Lh * 1.45, 0.02), 0.05, 0.01), 0.03)
            e = e.rot(5, -20, -18)
            ep = (0.2, 0.28, -0.08)
        e = e.scale(hs)
        for sx, tag in ((1, "R"), (-1, "L")):
            bpos = A(*hw(sx * ep[0], ep[1] + 0.04 * DM, ep[2]))
            bn = H.bone(f"Ear{tag}", "Head", T(bpos))
            ears.append(bn)
            sh_ = e if sx > 0 else _mirror_sdf(e)
            H.piece(f"Ear{tag}", bn, sh_.at(*T(bpos)), col=P.get("earcol") or "primary", tris=300, role="ear", pri=1.5,
                    key=f"h_{H.id}_ear".replace(" ", "_") + ("" if sx > 0 else "_l"), mirrored=sx < 0)

    # ---------------------------------------------------------------- tail
    tt, TL, TT = P["tail"], P["tail_len"], P["tail_thick"]
    t0 = v(0, yr + 0.3 * R * PR, zr + 0.9 * BL)
    tcol = P["tail_col"]
    tfl = 0.0
    tpat = None
    D = {
        "bald": ([(0, -0.15, 0.9), (0, -0.3, 0.85), (0.1, -0.05, 0.9)], [0.1, 0.07, 0.045, 0.015]),
        "bushy": ([(0, 0.45, 0.45), (0, 0.75, 0.0), (0, 0.4, -0.4)], [0.16, 0.4, 0.5, 0.36]),
        "plume": ([(0, 0.6, 0.35), (0, 0.6, -0.15), (0, 0.15, -0.55)], [0.18, 0.4, 0.46, 0.3]),
        "ringed": ([(0, -0.15, 0.6), (0, -0.2, 0.6), (0, -0.15, 0.55)], [0.17, 0.24, 0.22, 0.12]),
        "flat": ([(0, -0.12, 0.35), (0, -0.04, 0.55), (0, 0, 0.4)], [0.13, 0.1, 0.1, 0.1]),
        "thick": ([(0, -0.2, 0.6), (0, -0.15, 0.6), (0, -0.05, 0.55)], [0.26, 0.19, 0.12, 0.05]),
        "long": ([(0, -0.2, 0.6), (0, -0.25, 0.6), (0, -0.1, 0.55)], [0.13, 0.12, 0.1, 0.05]),
        "flag": ([(0, 0.0, 0.6), (0, -0.1, 0.65), (0, -0.1, 0.6)], [0.25, 0.3, 0.3, 0.18]),
        "armour": ([(0, -0.25, 0.5), (0, -0.25, 0.5), (0, -0.1, 0.45)], [0.17, 0.13, 0.09, 0.03]),
        "nub": ([(0, -0.02, 0.14), (0, -0.02, 0.06), (0, -0.02, 0.04)], [0.12, 0.08, 0.05, 0.03]),
    }
    if tt != "none":
        dirs, radii = D[tt]
        pts = [t0]
        for d in dirs:
            pts.append(pts[-1] + A(*d) * TL * s)
        H.bone("Tail1", "Spine", T(pts[0]))
        H.bone("Tail2", "Tail1", T(pts[1]))
        H.bone("Tail3", "Tail2", T(pts[2]))
        r = [x * TT * s for x in radii]
        if tt in ("bushy", "plume", "ringed"):
            tfl = (0.03 if tt in ("bushy", "plume") else 0.02) * s
        if tt == "ringed":
            ax = pts[3] - pts[0]
            L = np.linalg.norm(ax)
            ax = ax / L
            tpat = stripes(lambda Q: ((Q - pts[0]) @ ax) / L, 5.0, width=0.42, depth=0.8)
        segs = []
        for i in range(3):
            a, b = pts[i], pts[i + 1]
            if i == 0:
                a = a - (pts[1] - pts[0]) * 0.3
            sg = round_cone(T(a), T(b), r[i], r[i + 1])
            if tt == "flat":
                sg = ellipsoid(0.36 * s * TT, 0.06 * s * TT, 0.5 * s * TL, T((pts[1] + pts[3]) / 2)) if i == 1 else (sg if i == 0 else None)
            if tt in ("bushy", "plume"):  # fluffy, a little flattened sideways
                c = (A(*a) + A(*b)) / 2
                sg = round_cone(T(a - c), T(b - c), r[i], r[i + 1]).scale3(0.72, 1, 1).at(*T(c))
            if tt == "flag":  # vertical flag (anteater): flatten sideways
                c = (A(*a) + A(*b)) / 2
                sg = round_cone(T(a - c), T(b - c), r[i], r[i + 1]).scale3(0.45, 1.4, 1).at(*T(c))
            if tt == "armour" and sg is not None:
                for k in range(4):
                    q = A(*a) + (A(*b) - A(*a)) * (k + 0.5) / 4
                    sg = sg - box(1.0, 1.0, 0.012 * s, T(q))
            if sg is not None and tfl:
                sg = sg.noise(tfl, 13 / s, 20 + i)
            segs.append(sg)
        names = ["TailA", "TailB", "TailC"]
        for i, sg in enumerate(segs):
            if sg is None:
                continue
            H.piece(names[i], f"Tail{i + 1}", sg, col=tcol if not (tt == "flat" and i == 0) else "primary", mat="skin", tris=500 if tt != "flat" else 600,
                    role="tail", pri=1.5 + 0.2 * i, pattern=tpat if tpat else (stripes(lambda Q: Q[:, 0] * 8 + Q[:, 2] * 8, 1.0, width=0.2, depth=0.25) if tt == "flat" and i == 1 else None))
        tails = ["Tail1", "Tail2", "Tail3"]
    else:
        tails = []

    # ---------------------------------------------------------------- rig + motion
    H.socket("mouth", hw(0, -0.12, -0.5 - sl), "Jaw")
    H.socket("head", hw(0, 0.45, -0.15), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": tails})
    legs = [("ShoulderFR", "ElbowFR", "WristFR", True, 1), ("ShoulderFL", "ElbowFL", "WristFL", True, -1),
            ("HipBR", "KneeBR", "HockBR", False, 1), ("HipBL", "KneeBL", "HockBL", False, -1)]
    g = P["gait"]
    MC.quad(H, legs, neck="Neck", head="Head", jaw="Jaw", tail=tails, ears=ears, height=backY * s + 0.3, gait=g if g in ("trot", "walk", "bound") else "trot",
            stride=0.55 if g == "bound" else 0.45, lift=1.1, walk=(0.5 if g == "bound" else 0.6 if g == "trot" else 1.3) * s ** 0.3,
            attack=P["attack"], wag=P["wag"], spine="Spine", bounce=1.4 if g == "bound" else 1.0)
    if g == "walk":
        H.gait = "heavy"
        H.rig["gait"] = "heavy"
    return H


# ====================================================================================================== hoppers
def _hopper(hid, roo=False, **kw):
    P = dict(s=1.0, ears=1.0, ear_w=1.0, lop=False, fluff=0.01, head=1.0, body=1.0, girth=1.0, tail=1.0, belly=0.9, marks=None,
             antlers=False, preview=None, foot=1.0)
    P.update(kw)
    s, G, BL = P["s"], P["girth"], P["body"]
    H = MC.FastHero(hid, plan="Quadruped", gait="hop", tags=["hopper"])
    H.preview = P["preview"] or {}
    marks = P["marks"] or {}
    fl = P["fluff"]

    def v(x, y, z):
        return A(x * s, y * s, z * s)

    def furry(sd, amp=1.0, freq=8.0, seed=0):
        return sd.noise(fl * amp * s, freq / s, seed) if fl > 0 else sd

    def shade(Q):
        t = np.clip((Q[:, 1] / s - 0.3) / 2.0, 0, 1)
        return 1.0 - (1.0 - P["belly"]) * t

    if roo:  # kangaroo: upright, tilted torso, chest high
        hipC = v(0, 1.55, 0.55)
        chestC = v(0, 2.85, -0.05)
        torso = ellipsoid(0.62 * G, 0.85, 0.7, T(hipC + v(0, 0.1, 0)))
        torso = torso.su(round_cone(T(hipC + v(0, 0.35, 0)), T(chestC), 0.6 * G * s, 0.42 * G * s), 0.4)
        torso = torso.su(ellipsoid(0.42 * G, 0.5, 0.42, T(chestC + v(0, -0.25, -0.05))), 0.3)
        nb = chestC + v(0, 0.35, -0.05)
        H.body(T(hipC))
    else:  # rabbit: hunched egg body, haunch high at the back
        hipC = v(0, 0.95, 0.55 * BL)
        chestC = v(0, 0.95, -0.45 * BL)
        torso = ellipsoid(0.62 * G, 0.72, 0.85 * BL, T(hipC + v(0, 0.1, 0)))
        torso = torso.su(ellipsoid(0.48 * G, 0.55, 0.65 * BL, T(chestC)), 0.45)
        nb = chestC + v(0, 0.5, -0.25)
        H.body(T((hipC + chestC) / 2))
    torso = furry(torso, 1.0, 7, 1)
    H.piece("Torso", "Body", torso, col="primary", tris=2200, res=120, pattern=shade)
    if "belly" in marks:
        reg = ellipsoid(0.75 * G, 0.6, 0.65, T(chestC + v(0, -0.3 if not roo else 0.0, -0.3 if not roo else -0.35))) | ellipsoid(0.5 * G, 0.3, 0.8, T(hipC + v(0, -0.65, -0.2)))
        H.piece("Belly", "Body", overlay(torso, reg.noise(0.03 * s, 8 / s, 2), 0.04 * s), col=marks["belly"], tris=700, role="body", pri=1.2)
    # hind legs: big folded thigh, shin, long foot flat on the ground
    hp = hipC + v(0.48 * G, -0.05, 0.05)
    kn = hp + (v(0.1, -0.42, -0.45) if not roo else v(0.08, -0.55, -0.5))
    hk = A(hp[0], (0.22 if not roo else 0.3) * s, hp[2] + (0.3 if not roo else 0.35) * s)
    toe = A(hk[0], 0, hk[2] - (0.95 if not roo else 1.5) * P["foot"] * s)
    H.mbone("HipB#", "Body", T(hp))
    H.mbone("KneeB#", "HipB#", T(kn))
    H.mbone("HockB#", "KneeB#", T(hk))
    th = ellipsoid(0.32 * G, 0.55, 0.55, T((hp + kn) / 2 + v(0.0, 0.08, 0.1))).su(round_cone(T(hp), T(kn), 0.3 * s, 0.17 * s), 0.12)
    H.mpiece("Thigh#", "HipB#", furry(th, 0.8, 8, 2), col="primary", tris=800, role="limb", pattern=shade)
    sn = round_cone(T(kn), T(hk), 0.16 * s, 0.09 * s)
    H.mpiece("Shin#", "KneeB#", furry(sn, 0.6, 9, 3), col="primary", tris=500, role="limb", pattern=shade)
    ft = round_cone(T(hk + v(0, 0.02, 0)), T(toe + v(0, 0.08, 0)), 0.1 * s, 0.075 * s)
    ft = ft.su(ellipsoid(0.13, 0.07, (0.5 if not roo else 0.75) * P["foot"], T((hk + toe) / 2 + v(0, 0.02, 0))), 0.06 * s)
    ft = (ft & plane((0, -1, 0), 0.0))
    H.mpiece("FootB#", "HockB#", furry(ft, 0.5, 10, 4), col="primary" if not roo else "primary", tris=600, role="foot", pattern=shade)
    # forelegs (rabbit: short columns to the ground; kangaroo: small arms)
    if roo:
        sh = chestC + v(0.35 * G, 0.05, -0.2)
        el = sh + v(0.08, -0.45, -0.25)
        wr = el + v(-0.05, -0.35, -0.15)
    else:
        sh = chestC + v(0.32 * G, -0.1, -0.15)
        el = A(sh[0] + 0.02 * s, 0.4 * s, sh[2] - 0.05 * s)
        wr = A(sh[0], 0.1 * s, sh[2] - 0.12 * s)
    H.mbone("ShoulderF#", "Body", T(sh))
    H.mbone("ElbowF#", "ShoulderF#", T(el))
    H.mbone("WristF#", "ElbowF#", T(wr))
    H.mpiece("UpperF#", "ShoulderF#", furry(round_cone(T(sh + v(0, 0.12, 0.05)), T(el), 0.17 * s, 0.09 * s), 0.6, 9, 5), col="primary", tris=450, role="limb", pattern=shade)
    if roo:
        hand = round_cone(T(el), T(wr), 0.08 * s, 0.06 * s).su(ellipsoid(0.08, 0.06, 0.08, T(wr + v(0, -0.03, -0.03))), 0.04 * s)
        for dx in (-0.04, 0.0, 0.04):
            hand = hand | round_cone(T(wr + v(dx, -0.05, -0.05)), T(wr + v(dx, -0.12, -0.1)), 0.018 * s, 0.006 * s)
    else:
        hand = round_cone(T(el), T(wr + v(0, 0.02, 0)), 0.08 * s, 0.065 * s).su(ellipsoid(0.08, 0.06, 0.14, T(A(wr[0], 0.05 * s, wr[2] - 0.06 * s))), 0.04 * s)
        hand = hand & plane((0, -1, 0), 0.0)
    H.mpiece("ForeF#", "ElbowF#", furry(hand, 0.5, 10, 6), col="primary", tris=450, role="limb", pattern=shade)
    # neck / head
    H.bone("Neck", "Body", T(nb))
    hc = nb + (v(0, 0.35, -0.2) if roo else v(0, 0.28, -0.22))
    H.bone("Head", "Neck", T(hc))
    hs = P["head"] * s * (0.85 if not roo else 0.75)

    def hw(x, y, z):
        return T(hc + A(x, y, z) * hs)

    def W(sd):
        return sd.scale(hs).at(*T(hc))

    neck = round_cone(T(nb + v(0, -0.2, 0.15)), T(hc + v(0, -0.05, 0.05)), 0.4 * G * s, 0.3 * hs)
    H.piece("NeckP", "Neck", furry(neck, 0.8, 8, 7), col="primary", tris=500, role="limb", pattern=shade)
    if roo:  # long deer-like head
        head = ellipsoid(0.33, 0.32, 0.38, (0, 0.05, -0.15))
        head = head.su(round_cone((0, -0.02, -0.35), (0, -0.12, -0.9), 0.24, 0.13), 0.12)
        nz = -0.98
    else:
        head = ellipsoid(0.38, 0.36, 0.42, (0, 0.04, -0.2))
        head = head.su(ellipsoid(0.24, 0.22, 0.24, (0.16, -0.1, -0.4)).mirror_x(), 0.12)                     # muzzle pads
        head = head.su(ellipsoid(0.2, 0.2, 0.24, (0, -0.06, -0.45)), 0.1)
        nz = -0.66
    head = head.ss(sphere(0.085, (0.24, 0.1, -0.33 if not roo else -0.3)).mirror_x(), 0.03)
    headW = furry(W(head), 0.3, 12, 8)
    H.piece("HeadP", "Head", headW, col="primary", tris=1600, role="head")
    if "muzzle" in marks:
        H.piece("Mask", "Head", overlay(headW, W(ellipsoid(0.3, 0.2, 0.3, (0, -0.16, -0.5 if not roo else -0.75))), 0.03 * s), col=marks["muzzle"], tris=450,
                role="head", pri=1.3)
    H.piece("Nose", "Head", W(ellipsoid(0.07, 0.05, 0.04, (0, -0.02 if not roo else -0.1, nz))), col=PINK if not roo else NOSE, tris=200, role="nose", pri=1.6, ao=False)
    jb = H.bone("Jaw", "Head", hw(0, -0.15, -0.25))
    H.piece("JawP", "Jaw", W(ellipsoid(0.13, 0.07, 0.15 if not roo else 0.3, (0, -0.24, -0.5 if not roo else -0.65))), col=marks.get("muzzle", "primary"), tris=250, role="jaw", pri=1.4)
    if not roo:
        inc = round_box(0.022, 0.05, 0.012, 0.008).at(0.024, -0.2, nz + 0.1)
        H.mpiece("Incisor#", "Head", W(inc), col=INCISOR, mat="hard", tris=120, role="tooth", pri=2.2, ao=False, smooth=1)
    er = 0.085 * hs
    H.eyes("Head", hw(0.25, 0.1, -0.34 if not roo else -0.31), er, col="pupil" if not roo else "iris", pupil=None if not roo else "round", look=(0.7, 0.1, -1.0))
    # ears
    EL = (0.95 if not roo else 0.6) * P["ears"]
    ew = (0.17 if not roo else 0.15) * P["ear_w"]
    ear = round_cone((0, 0, 0), (0, EL, 0), ew * 0.8, ew).scale3(1, 1, 0.32)
    ear = ear.su(ellipsoid(ew, EL * 0.45, ew * 0.4, (0, EL * 0.55, 0)), 0.05)
    ear = ear.ss(ellipsoid(ew * 0.7, EL * 0.42, ew * 0.25, (0, EL * 0.55, -ew * 0.25)), 0.03)
    if P["lop"]:
        ear = ear.rot(170, 0, -15)
    else:
        ear = ear.rot(18, -15, -12)
    ear = ear.scale(hs)
    ears = []
    for sx, tag in ((1, "R"), (-1, "L")):
        bpos = A(*hw(sx * (0.14 if not P["lop"] else 0.3), 0.32, -0.12))
        bn = H.bone(f"Ear{tag}", "Head", T(bpos))
        ears.append(bn)
        e = ear if sx > 0 else _mirror_sdf(ear)
        H.piece(f"Ear{tag}", bn, e.at(*T(bpos)), col="primary", tris=400, role="ear", pri=1.5, key=f"h_{hid}_ear".replace(" ", "_") + ("" if sx > 0 else "_l"), mirrored=sx < 0)
    if P["antlers"]:  # wolpertinger / jackalope
        for sx, tag in ((1, "R"), (-1, "L")):
            b = A(*hw(sx * 0.12, 0.3, -0.25))
            an = round_cone(T(b), T(b + v(sx * 0.15, 0.45, 0.05)), 0.035 * s, 0.02 * s)
            an = an | round_cone(T(b + v(sx * 0.08, 0.25, 0.03)), T(b + v(sx * 0.02, 0.45, -0.12)), 0.022 * s, 0.01 * s)
            H.piece(f"Antler{tag}", "Head", an, col="horn", mat="hard", tris=250, role="horn", pri=1.8)
    # tail
    if roo:
        t0 = hipC + v(0, -0.35, 0.55)
        pts = [t0, t0 + v(0, -0.45, 0.65), t0 + v(0, -0.85, 1.25), t0 + v(0, -1.0, 1.85)]
        radii = [0.32, 0.22, 0.14, 0.06]
    else:
        t0 = hipC + v(0, 0.2, 0.8 * BL)
        pts = [t0, t0 + v(0, 0.12, 0.12), t0 + v(0, 0.16, 0.18), t0 + v(0, 0.17, 0.2)]
        radii = [0.2, 0.22, 0.12, 0.05]
    H.bone("Tail1", "Body", T(pts[0]))
    tails = ["Tail1"]
    if roo:
        H.bone("Tail2", "Tail1", T(pts[1]))
        H.bone("Tail3", "Tail2", T(pts[2]))
        tails = ["Tail1", "Tail2", "Tail3"]
        for i in range(3):
            a = pts[i] - ((pts[1] - pts[0]) * 0.3 if i == 0 else 0)
            H.piece("Tail" + "ABC"[i], tails[i], round_cone(T(a), T(pts[i + 1]), radii[i] * s, radii[i + 1] * s), col="primary", tris=450, role="tail", pri=1.5 + 0.1 * i,
                    pattern=shade)
    else:
        H.piece("TailA", "Tail1", sphere(0.24 * s, T(pts[1])).noise(0.03 * s, 12 / s, 9), col=P.get("tailcol", "white"), tris=350, role="tail", pri=1.5)
    H.socket("mouth", hw(0, -0.15, nz), "Jaw")
    H.socket("head", hw(0, 0.45, -0.2), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": tails})
    legs = [("ShoulderFR", "ElbowFR", "WristFR", True, 1), ("ShoulderFL", "ElbowFL", "WristFL", True, -1),
            ("HipBR", "KneeBR", "HockBR", False, 1), ("HipBL", "KneeBL", "HockBL", False, -1)]
    MC.hop(H, legs, neck="Neck", head="Head", jaw="Jaw", tail=tails, ears=ears, height=(2.0 if not roo else 3.6) * s, walk=0.6 if not roo else 0.8,
           kangaroo=roo, arms=["ShoulderFR", "ShoulderFL"])
    return H


# ====================================================================================================== heroes
def PV(primary, secondary, **k):
    d = {"primary": primary, "secondary": secondary}
    d.update(k)
    return d


@hero("rat", "smallmammals")
def rat():
    return _critter("rat", body=1.05, girth=0.95, pear=1.2, snout=1.15, blunt=0.15, ear="round", ear_size=0.75, tail="bald", tail_len=1.45,
                    tail_col="secondary", nose=PINK, earcol="secondary", attack="bite", preview=PV("#7A7470", "#E8B0B0"))


@hero("mouse", "smallmammals")
def mouse():
    return _critter("mouse", s=0.8, body=0.85, girth=0.92, pear=1.25, head=1.15, snout=0.9, blunt=0.1, ear="round", ear_size=1.25, eye=1.25,
                    tail="bald", tail_len=1.35, tail_thick=0.75, tail_col="secondary", nose=PINK, earcol="secondary", marks={"belly": "white"},
                    preview=PV("#A8A098", "#F2C4C4"))


@hero("hamster", "smallmammals")
def hamster():
    return _critter("hamster", s=0.8, body=0.6, girth=1.0, pear=1.0, leg=0.6, head=1.55, snout=0.45, blunt=0.6, cheeks=1.0, ear="round",
                    ear_size=0.6, eye=1.15, tail="nub", nose=PINK, marks={"belly": "secondary", "muzzle": "secondary"}, fluff=0.008,
                    preview=PV("#E2B87A", "#FFF8EE"))


@hero("guinea pig", "smallmammals")
def guinea_pig():
    return _critter("guinea pig", s=0.85, body=0.9, girth=1.12, pear=1.0, leg=0.55, head=1.15, snout=0.55, blunt=0.75, ear="small", ear_size=1.4,
                    tail="none", nose=PINK, gait="trot", pattern="spots", marks={"face": "secondary"}, fluff=0.01, earcol=[0.85, 0.6, 0.55],
                    preview=PV("#D8924A", "#F7F2EA"))


@hero("squirrel", "smallmammals")
def squirrel():
    return _critter("squirrel", s=0.85, body=0.85, girth=0.88, pear=1.18, leg=1.0, head=1.05, snout=0.75, blunt=0.3, ear="tuft", ear_size=0.9,
                    eye=1.2, tail="bushy", tail_len=1.35, tail_thick=1.05, front_up=0.5, claws=0.5, marks={"belly": "secondary"},
                    preview=PV("#A8562A", "#F2D8B8"))


@hero("chipmunk", "smallmammals")
def chipmunk():
    return _critter("chipmunk", s=0.75, body=0.82, girth=0.9, pear=1.15, head=1.12, snout=0.7, cheeks=0.5, ear="small", ear_size=1.3, eye=1.2,
                    tail="bushy", tail_len=1.0, tail_thick=0.65, front_up=0.35, pattern="chipmunk", marks={"belly": "cream"},
                    preview=PV("#B87A3E", "#2A2420"))


@hero("groundhog", "smallmammals")
def groundhog():
    return _critter("groundhog", body=1.0, girth=1.18, pear=1.15, leg=0.75, head=1.05, snout=0.55, blunt=0.65, ear="small", ear_size=1.0,
                    tail="long", tail_len=0.75, tail_thick=1.1, claws=0.6, fluff=0.016, gait="trot", marks={"muzzle": "cream"},
                    preview=PV("#8A6A48", "#5A4632"))


@hero("beaver", "smallmammals")
def beaver():
    return _critter("beaver", s=1.0, body=1.05, girth=1.2, pear=1.25, leg=0.65, head=1.05, snout=0.6, blunt=0.7, ear="small", ear_size=0.8,
                    tail="flat", tail_len=1.0, tail_thick=1.2, tail_col="secondary", teeth="orange", gait="walk", claws=0.4, fluff=0.008,
                    preview=PV("#6A4428", "#2A1E16"))


@hero("capybara", "smallmammals")
def capybara():
    return _critter("capybara", s=1.2, body=1.1, girth=1.3, pear=1.05, leg=0.85, head=1.35, snout=1.0, sw=1.25, blunt=0.95, dome=0.2, ear="small",
                    ear_size=0.75, eye=0.8, tail="none", gait="walk", whiskers=False, fluff=0.012, preview=PV("#9A6E44", "#C8A07A"))


@hero("porcupine", "smallmammals")
def porcupine():
    return _critter("porcupine", body=0.95, girth=1.12, pear=1.25, leg=0.75, head=0.95, snout=0.55, blunt=0.7, ear="small", ear_size=0.7,
                    tail="thick", tail_len=0.55, tail_thick=0.8, quills=True, gait="walk", attack="bristle", claws=0.5, fluff=0.01,
                    preview=PV("#5E5248", "#E8E0D4"))


@hero("hedgehog", "smallmammals")
def hedgehog():
    return _critter("hedgehog", s=0.75, body=0.85, girth=1.1, pear=1.05, leg=0.55, head=0.95, snout=0.85, blunt=0.15, ear="small", ear_size=0.8,
                    eye=1.15, tail="none", spines=True, gait="trot", attack="charge", nose=NOSE, legcol="secondary", marks={"belly": "secondary"},
                    earcol="secondary", preview=PV("#8A7460", "#F2E6D2"))


@hero("otter", "smallmammals")
def otter():
    return _critter("otter", body=1.45, girth=0.9, pear=1.1, arch=0.15, leg=0.7, neck=0.9, head=0.95, snout=0.55, sw=1.15, blunt=0.6, ear="small",
                    ear_size=0.6, tail="thick", tail_len=1.5, gait="bound", marks={"muzzle": "secondary", "belly": "secondary"}, teeth=None,
                    preview=PV("#6A4A30", "#A8886A"))


@hero("weasel", "smallmammals")
def weasel():
    return _critter("weasel", s=0.85, body=1.65, girth=0.7, pear=1.05, arch=0.3, leg=0.75, neck=1.0, head=0.85, snout=0.6, blunt=0.3, ear="small",
                    ear_size=1.0, tail="long", tail_len=1.0, teeth=None, gait="bound", marks={"belly": "secondary", "muzzle": "secondary"},
                    preview=PV("#8A5A30", "#F2E6CC"))


@hero("ferret", "smallmammals")
def ferret():
    return _critter("ferret", s=0.9, body=1.6, girth=0.78, pear=1.08, arch=0.25, leg=0.72, neck=0.9, head=0.9, snout=0.6, blunt=0.35, ear="small",
                    ear_size=1.05, tail="long", tail_len=0.95, tail_col="secondary", teeth=None, gait="bound", legcol="secondary",
                    marks={"mask": "secondary"}, preview=PV("#E2D2BA", "#4A3A2C"))


@hero("badger", "smallmammals")
def badger():
    return _critter("badger", body=1.15, girth=1.3, pear=1.05, leg=0.6, head=1.0, snout=0.95, sw=0.9, blunt=0.25, ear="small", ear_size=0.75,
                    tail="nub", claws=1.4, legcol="black", gait="walk", teeth=None, marks={"facestripe": "secondary"}, fluff=0.016,
                    preview=PV("#7A7672", "#F2F2F0"))


@hero("skunk", "smallmammals")
def skunk():
    return _critter("skunk", s=0.9, body=1.0, girth=1.0, pear=1.2, arch=0.1, leg=0.7, head=0.95, snout=0.75, blunt=0.3, ear="small", tail="plume",
                    tail_len=1.25, tail_thick=1.1, tail_col="primary", teeth=None, gait="trot", attack="spray", fluff=0.014,
                    marks={"stripe": "secondary"}, preview=PV("#1A1A1C", "#F2F2F2"))


@hero("wolverine", "smallmammals")
def wolverine():
    return _critter("wolverine", s=1.1, body=1.1, girth=1.2, pear=1.1, arch=0.12, leg=0.95, head=1.05, snout=0.75, sw=1.1, blunt=0.45, ear="small",
                    tail="ringed", tail_len=0.7, tail_thick=0.9, claws=1.0, fluff=0.02, gait="bound", teeth=None, attack="bite",
                    marks={"side": "secondary"}, preview=PV("#3E2C1E", "#C89A5A"))


@hero("raccoon", "smallmammals")
def raccoon():
    return _critter("raccoon", body=1.0, girth=1.08, pear=1.2, arch=0.12, leg=0.9, head=1.05, snout=0.8, blunt=0.2, ear="point", ear_size=0.85,
                    tail="ringed", tail_len=1.15, tail_thick=0.95, fluff=0.016, gait="trot", teeth=None, legcol="secondary",
                    marks={"mask": "secondary", "muzzle": "white"}, preview=PV("#7A7670", "#1E1C1A"))


@hero("red panda", "smallmammals")
def red_panda():
    return _critter("red panda", body=1.0, girth=1.0, pear=1.1, leg=0.85, head=1.12, snout=0.55, blunt=0.4, ear="point", ear_size=0.95,
                    tail="ringed", tail_len=1.45, tail_thick=1.0, fluff=0.016, gait="trot", teeth=None, legcol="secondary",
                    marks={"face": "white"}, earcol="primary", preview=PV("#C24A1A", "#2E1A12"))


@hero("mongoose", "smallmammals")
def mongoose():
    return _critter("mongoose", s=0.9, body=1.35, girth=0.78, pear=1.05, arch=0.1, leg=0.9, neck=0.8, head=0.88, snout=0.85, blunt=0.15, ear="small",
                    ear_size=0.9, tail="long", tail_len=1.35, tail_thick=1.15, teeth=None, gait="bound", pattern="brindle", eyecol="iris",
                    preview=PV("#9E8E74", "#5A4E40", iris="#C98A2A"))


@hero("opossum", "smallmammals")
def opossum():
    return _critter("opossum", body=1.05, girth=1.0, pear=1.15, leg=0.8, head=1.0, snout=1.25, blunt=0.12, ear="round", ear_size=0.7, earcol=NOSE,
                    tail="bald", tail_len=1.3, tail_col=PINK, nose=PINK, teeth=None, gait="trot", fluff=0.016, legcol="black",
                    marks={"face": "secondary"}, preview=PV("#B0AAA4", "#F2EEE8"))


@hero("armadillo", "smallmammals")
def armadillo():
    return _critter("armadillo", body=1.0, girth=1.05, pear=1.05, leg=0.6, head=0.85, snout=1.2, blunt=0.15, ear="point", ear_size=0.8,
                    tail="armour", tail_len=1.1, tail_col="secondary", shell=True, claws=0.9, whiskers=False, teeth=None, gait="trot",
                    attack="charge", preview=PV("#B8A08E", "#8A7462"))


@hero("anteater", "smallmammals")
def anteater():
    return _critter("anteater", s=1.1, body=1.25, girth=1.05, pear=1.05, leg=1.15, neck=0.7, head=0.8, snout=3.2, sw=0.55, blunt=0.0, ear="small",
                    ear_size=0.8, eye=0.7, tail="flag", tail_len=1.25, tail_thick=1.2, claws=1.6, whiskers=False, teeth=None, gait="walk",
                    attack="swipe", fluff=0.02, marks={"diag": "secondary"}, preview=PV("#6E6056", "#2A2420"))


@hero("sloth", "smallmammals")
def sloth():
    return _critter("sloth", s=1.0, body=0.95, girth=1.05, pear=1.0, leg=1.6, neck=0.6, head=1.15, snout=0.25, blunt=0.8, dome=0.3, ear="none",
                    tail="nub", claws=2.2, whiskers=False, teeth=None, gait="walk", attack="swipe", fluff=0.03, marks={"face": "secondary", "mask": "dark"},
                    preview=PV("#9A8A6E", "#D8C8A8"))


@hero("rabbit", "smallmammals")
def rabbit():
    return _hopper("rabbit", s=0.85, head=1.3, body=0.85, ear_w=1.2, fluff=0.012, marks={"belly": "secondary"}, preview=PV("#C8B8A8", "#F7F4EE"))


@hero("kangaroo", "smallmammals")
def kangaroo():
    return _hopper("kangaroo", roo=True, s=1.0, fluff=0.006, ears=1.0, marks={"belly": "secondary", "muzzle": "secondary"}, preview=PV("#B8784A", "#E8C8A8"))


@hero("wolpertinger", "smallmammals")
def wolpertinger():
    return _hopper("wolpertinger", s=0.85, head=1.3, body=0.85, ear_w=1.2, ears=0.75, antlers=True, fluff=0.012, marks={"belly": "secondary"},
                   preview=PV("#9A7A5A", "#F2E6D2"))


ANIM = {"cat": ["Creature", "Abstract", "Element", "Machine", "Weather"], "bp": ["Quadruped", "Biped", "Blob", "Swarm", "Bird", "Humanoid"]}
MAP = [
    ("rat", "rat, rats, fancy rat, pack rat, sewer rat, giant rat, rat king, naked mole rat, mole rat, kangaroo rat, bandicoot, muskrat, nutria, "
            "hutia, degu, rodent, plague rat", ANIM),
    ("mouse", "mouse, mice, harvest mouse, deer mouse, spiny mouse, field mouse, house mouse, dormouse, gerbil, jerboa, shrew, elephant shrew, "
              "lab mouse, mouse knight, !sea mouse, !mouse deer, !computer mouse", ANIM),
    ("hamster", "hamster, hamsters, dwarf hamster, syrian hamster, space hamster, hamster knight, vole, lemming, pika, chinchilla", ANIM),
    ("guinea pig", "guinea pig, cavy, agouti, paca, mara", ANIM),
    ("squirrel", "squirrel, squirrels, red squirrel, gray squirrel, grey squirrel, flying squirrel, ratatoskr, sugar glider", ANIM),
    ("chipmunk", "chipmunk, chipmunks", ANIM),
    ("groundhog", "groundhog, woodchuck, marmot, prairie dog, gopher, wombat, wombat joey, hyrax, rock hyrax, mole, star-nosed mole, star nosed mole, "
                  "marsupial mole, springhare, !mole person, !mole sauce, !mole machine, !mole cricket", ANIM),
    ("beaver", "beaver, beavers, castoroides, giant beaver", ANIM),
    ("capybara", "capybara, capybaras, josephoartigasia, phoberomys", ANIM),
    ("porcupine", "porcupine, crested porcupine, echidna", ANIM),
    ("hedgehog", "hedgehog, hoglet, tenrec, hedgehog tenrec, solenodon", ANIM),
    ("otter", "otter, otters, sea otter, river otter, giant otter, baby otter", ANIM),
    ("weasel", "weasel, stoat, ermine, mink, marten, pine marten, sable, fisher, polecat, tayra, grison, kamaitachi, !sable antelope", ANIM),
    ("ferret", "ferret, ferrets, black-footed ferret, black footed ferret", ANIM),
    ("badger", "badger, honey badger, hog badger, ratel", ANIM),
    ("skunk", "skunk, skunk kit, zorilla, !skunk ape", ANIM),
    ("wolverine", "wolverine, tasmanian devil, glutton, thylacoleo", ANIM),
    ("raccoon", "raccoon, raccoons, racoon, raccoon kit, raccoon dog, tanuki, coati, ringtail, trash panda", ANIM),
    ("red panda", "red panda, red panda cub, kinkajou, olinguito, binturong, lesser panda", ANIM),
    ("mongoose", "mongoose, banded mongoose, dwarf mongoose, meerkat, meerkats, civet, genet, fossa, numbat, quoll, dunnart, bilby", ANIM),
    ("opossum", "opossum, possum, honey possum, cuscus, greater glider", ANIM),
    ("armadillo", "armadillo, giant armadillo, pink fairy armadillo, three-banded armadillo, three banded armadillo, pangolin, glyptodon, doedicurus", ANIM),
    ("anteater", "anteater, giant anteater, tamandua, silky anteater, aardvark", ANIM),
    ("sloth", "sloth, baby sloth, giant ground sloth, ground sloth, megalonyx, three-toed sloth, two-toed sloth, megatherium", ANIM),
    ("rabbit", "rabbit, rabbits, bunny, bunnies, baby rabbit, lop rabbit, angora rabbit, cottontail, flemish giant, netherland dwarf, hare, hares, "
               "arctic hare, snowshoe hare, jackrabbit, thunder bunny, easter bunny, bunny warrior, pooka, !dust bunny, !sea bunny, !sea hare",
     {"cat": ["Creature", "Person", "Abstract", "Element", "Machine"], "bp": ["Quadruped", "Biped", "Blob", "Swarm"]}),
    ("wolpertinger", "wolpertinger, jackalope, jackalope warrior, antlered rabbit", ANIM),
    ("kangaroo", "kangaroo, kangaroos, red kangaroo, tree kangaroo, wallaby, rock wallaby, joey, quokka, quokka joey, pademelon, potoroo, "
                 "procoptodon, bettong, diprotodon", ANIM),
]
