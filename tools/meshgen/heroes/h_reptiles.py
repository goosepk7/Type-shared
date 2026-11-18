"""Reptiles and amphibians: crocodilians, lizards, turtles, snakes, frogs, salamanders.

Builders:
  _sprawler   crocodile / alligator / gharial / komodo / monitor / lizard / iguana / gecko / chameleon / frilled lizard /
              horned lizard / bearded dragon / salamander / newt / axolotl / dimetrodon: a three-piece trunk that bends
              in an S (Front / Body / Hips bones), sprawled three-segment legs with splayed toes, a station-lofted head
              with an opening jaw, and a five-bone tail. Options add scutes, crests, dewlaps, frills, horns, sails,
              gills, casques and turret eyes.
  _turtle     turtle / tortoise / sea turtle / snapping turtle: scute-plated carapace + plastron, retractable-looking
              head on a two-bone neck, column legs or flippers.
  _snake      snake / python / cobra / king cobra / rattlesnake / viper / sea snake: a 12-bone body chain with a
              travelling-wave slither, hood, rattle, paddle tail, forked tongue.
  _frog       frog / toad / tree frog: crouched body, folded jumping legs, wide mouth, bulging eyes, sticky tongue.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from kit import Hero, hero, stripes, spots, gradient, combine
from map import NOTFOOD
import motion
import motion_reptiles as MR
from motion_reptiles import eloft, squash, grid_bumps, spikes

FAM = "reptiles"
ANIM = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Plant", "Weather", "Structure"]}
LIZ = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Plant", "Weather", "Structure"],
       "bp": ["Quadruped", "Biped", "Serpent", "Blob", "Fish", "Swarm"]}


def _v(a):
    return np.asarray(a, float)


def _interp(z, zs, vs):
    zs = np.asarray(zs, float)
    vs = np.asarray(vs, float)
    o = np.argsort(zs)
    return np.interp(z, zs[o], vs[o])


# ==================================================================================================== heads
# station heads: z (forward is -), half width, height above the mouth line; jaw: half width, depth below.
HEADS = {
    "croc": dict(z=[0.25, -0.15, -0.55, -1.0, -1.45, -1.8, -2.02], w=[0.42, 0.5, 0.42, 0.3, 0.24, 0.21, 0.12],
                 t=[0.24, 0.32, 0.27, 0.17, 0.14, 0.15, 0.08],
                 jz=[0.32, -0.15, -0.8, -1.4, -1.98], jw=[0.36, 0.4, 0.26, 0.2, 0.11], jd=[0.2, 0.2, 0.13, 0.1, 0.06]),
    "gator": dict(z=[0.25, -0.15, -0.55, -1.0, -1.45, -1.75, -1.92], w=[0.45, 0.52, 0.46, 0.38, 0.34, 0.3, 0.18],
                  t=[0.24, 0.32, 0.26, 0.17, 0.14, 0.14, 0.08],
                  jz=[0.32, -0.15, -0.8, -1.4, -1.85], jw=[0.4, 0.44, 0.35, 0.3, 0.17], jd=[0.2, 0.2, 0.13, 0.1, 0.06]),
    "gharial": dict(z=[0.25, -0.1, -0.45, -0.75, -1.3, -1.9, -2.15, -2.4, -2.55], w=[0.38, 0.44, 0.34, 0.14, 0.1, 0.09, 0.1, 0.17, 0.1],
                    t=[0.22, 0.3, 0.24, 0.1, 0.08, 0.08, 0.08, 0.13, 0.07],
                    jz=[0.32, -0.15, -0.7, -1.5, -2.45], jw=[0.34, 0.36, 0.13, 0.09, 0.08], jd=[0.2, 0.18, 0.08, 0.07, 0.05]),
    "lizard": dict(z=[0.2, -0.1, -0.4, -0.7, -0.92, -1.02], w=[0.28, 0.31, 0.27, 0.19, 0.12, 0.06],
                   t=[0.25, 0.31, 0.27, 0.19, 0.12, 0.06],
                   jz=[0.22, -0.1, -0.5, -0.85, -0.98], jw=[0.26, 0.28, 0.21, 0.12, 0.06], jd=[0.2, 0.19, 0.13, 0.08, 0.04]),
    "monitor": dict(z=[0.25, -0.1, -0.45, -0.85, -1.15, -1.3], w=[0.27, 0.29, 0.25, 0.19, 0.14, 0.08],
                    t=[0.22, 0.27, 0.22, 0.16, 0.12, 0.06],
                    jz=[0.28, -0.1, -0.6, -1.05, -1.25], jw=[0.25, 0.27, 0.2, 0.13, 0.07], jd=[0.2, 0.18, 0.12, 0.08, 0.04]),
    "gecko": dict(z=[0.15, -0.15, -0.45, -0.72, -0.85], w=[0.36, 0.4, 0.36, 0.24, 0.1],
                  t=[0.24, 0.3, 0.26, 0.16, 0.07],
                  jz=[0.18, -0.15, -0.5, -0.8], jw=[0.34, 0.37, 0.3, 0.1], jd=[0.17, 0.16, 0.11, 0.05]),
    "salamander": dict(z=[0.15, -0.15, -0.42, -0.62, -0.72], w=[0.3, 0.34, 0.32, 0.24, 0.1],
                       t=[0.2, 0.22, 0.19, 0.13, 0.06],
                       jz=[0.18, -0.15, -0.45, -0.68], jw=[0.29, 0.33, 0.29, 0.1], jd=[0.14, 0.14, 0.1, 0.05]),
    "axolotl": dict(z=[0.15, -0.12, -0.38, -0.55, -0.62], w=[0.42, 0.48, 0.46, 0.38, 0.18],
                    t=[0.24, 0.26, 0.22, 0.15, 0.07],
                    jz=[0.18, -0.15, -0.42, -0.6], jw=[0.4, 0.46, 0.42, 0.2], jd=[0.15, 0.14, 0.1, 0.05]),
    "chameleon": dict(z=[0.2, -0.1, -0.35, -0.55, -0.68], w=[0.24, 0.26, 0.22, 0.15, 0.07],
                      t=[0.3, 0.32, 0.26, 0.16, 0.07],
                      jz=[0.22, -0.1, -0.4, -0.65], jw=[0.22, 0.24, 0.18, 0.07], jd=[0.22, 0.2, 0.12, 0.05]),
    "horned": dict(z=[0.15, -0.1, -0.35, -0.55, -0.65], w=[0.34, 0.36, 0.3, 0.2, 0.08],
                   t=[0.18, 0.22, 0.18, 0.11, 0.05],
                   jz=[0.18, -0.1, -0.4, -0.62], jw=[0.32, 0.33, 0.25, 0.08], jd=[0.14, 0.13, 0.09, 0.04]),
    "dimetrodon": dict(z=[0.25, -0.1, -0.45, -0.8, -1.05, -1.18], w=[0.3, 0.32, 0.27, 0.2, 0.15, 0.08],
                       t=[0.34, 0.42, 0.38, 0.28, 0.2, 0.1],
                       jz=[0.28, -0.1, -0.6, -1.0, -1.15], jw=[0.28, 0.3, 0.22, 0.14, 0.07], jd=[0.24, 0.22, 0.15, 0.1, 0.05]),
}


# ==================================================================================================== sprawler
SBASE = dict(
    s=1.0, body=1.0, girth=1.0, tall=1.0, bodyY=0.78, leg=1.0, legr=1.0, head="croc", hs=1.0, neck=0.45,
    tail=1.0, tailr=1.0, tail_flat=0.75, tail_crest=False, tail_curl=False, scutes=False, spines=0.0, dewlap=0.0,
    frill=0.0, horns=False, beard=False, casque=False, turret=False, gills=False, sail=0.0, crest=0.0, toe_pads=False,
    zygo=False, teeth=0, eyes="side", eye_r=0.085, pupil="slit", warts=0.0, rough=0.0, cheek=False,
    pattern=None, pat_depth=0.75, shade=0.75, spots2=None, attack="snap", tongue=None, gait="sprawl",
    walk=1.0, stride=0.5, swim=False, belly=True, tags=(), preview={},
)


def _sprawler(hid, **kw):
    P = dict(SBASE)
    P.update(kw)
    s = P["s"]
    BL, G, TALL = P["body"] * s, P["girth"] * s, P["tall"]
    LG = P["leg"] * s
    bodyY = P["bodyY"] * s
    H = Hero(hid, plan="Quadruped", gait=P["gait"], tags=["reptile"] + list(P["tags"]))
    H.preview = P["preview"]
    H.body((0, bodyY, 0))

    # ------------------------------------------------------------------ trunk stations
    tz = [-1.85 * BL, -1.45 * BL, -0.7 * BL, 0.2 * BL, 1.1 * BL, 1.75 * BL]
    trx = [0.36 * G, 0.6 * G, 0.72 * G, 0.75 * G, 0.62 * G, 0.42 * G]
    try_ = [0.27 * G * TALL, 0.34 * G * TALL, 0.37 * G * TALL, 0.38 * G * TALL, 0.34 * G * TALL, 0.27 * G * TALL]
    tyc = [bodyY + 0.04 * s, bodyY + 0.02 * s, bodyY, bodyY, bodyY + 0.02 * s, bodyY + 0.03 * s]

    def rx_at(z):
        return _interp(z, tz, trx)

    def ry_at(z):
        return _interp(z, tz, try_)

    def yc_at(z):
        return _interp(z, tz, tyc)

    def top_y(z, x):
        rx, ry = rx_at(z), ry_at(z)
        return yc_at(z) + ry * np.sqrt(np.clip(1 - (x / np.maximum(rx, 1e-3)) ** 2, 0.02, 1)) - 0.035 * s

    def back_shade(Q):
        t = np.clip((Q[:, 1] - (bodyY - 0.35 * G)) / (0.75 * G * TALL), 0, 1)
        return 1.0 - (1.0 - P["shade"]) * t

    pat = None
    pt = P["pattern"]
    if pt == "bands":
        pat = stripes(lambda Q: Q[:, 2] / s, 1.25, width=0.3, depth=P["pat_depth"], wobble=0.05, seed=2)
    elif pt == "spots":
        pat = spots(0.26 * s, 0.075 * s, depth=P["pat_depth"], seed=4)
    elif pt == "blotch":
        pat = spots(0.42 * s, 0.15 * s, depth=P["pat_depth"], seed=6)
    elif pt == "rings":
        pat = spots(0.4 * s, 0.13 * s, depth=P["pat_depth"], ring=True, seed=8)
    elif pt == "scutegrid":
        def pat(Q):
            gz = np.abs(np.mod(Q[:, 2] / (0.24 * s), 1.0) - 0.5)
            gx = np.abs(np.mod(Q[:, 0] / (0.2 * s) + 0.5, 1.0) - 0.5)
            g = np.clip((0.5 - np.minimum(gz, gx)) * 6 - 2.2, 0, 1)
            top = np.clip((Q[:, 1] - bodyY + 0.1 * s) / (0.3 * s), 0, 1)
            return 1 - P["pat_depth"] * 0.35 * g * top

    def skin(extra=None):
        return combine(back_shade, pat, extra)

    def rough(sd, amp=1.0, seed=0):
        return sd.noise(P["rough"] * amp * s, 11.0 / s, seed) if P["rough"] > 0 else sd

    def warty(sd, seed=0):
        if P["warts"] <= 0:
            return sd
        w = P["warts"] * s
        return sd.su(S_bumps(sd, w, seed), 0.02 * s)

    def S_bumps(sd, w, seed):
        rng = np.random.default_rng(seed)
        ph = rng.uniform(0, 6.28, 3)
        f = 1.0 / (w * 1.6)

        def g(p):
            d = sd(p)
            cell = np.sin(p[:, 0] * f * 6.28 + ph[0]) * np.sin(p[:, 1] * f * 6.28 + ph[1]) * np.sin(p[:, 2] * f * 6.28 + ph[2])
            return d - w * np.clip(cell, 0, 1) ** 2

        return SDF(g)

    # ------------------------------------------------------------------ bones
    zF, zH = -1.15 * BL, 1.15 * BL
    H.bone("Front", "Body", (0, bodyY, zF))
    H.bone("Hips", "Body", (0, bodyY, zH))

    pts = [(0, tyc[i], tz[i]) for i in range(len(tz))]
    # three overlapping trunk pieces: the chest and hip pieces swell 3% past the middle one at the shoulders / hips and
    # taper away inside it, so their surfaces cross at an angle (no coplanar seams) and the trunk can bend.
    mid = eloft(pts[1:5], trx[1:5], try_[1:5], k=0.3 * s)
    chest = eloft(pts[:3], [trx[0], trx[1] * 1.035, trx[2] * 0.8], [try_[0], try_[1] * 1.035, try_[2] * 0.8], k=0.25 * s)
    hip = eloft(pts[3:], [trx[3] * 0.8, trx[4] * 1.035, trx[5]], [try_[3] * 0.8, try_[4] * 1.035, try_[5]], k=0.25 * s)
    zc1, zc2 = -1.2 * BL, 0.95 * BL
    if P["scutes"]:
        sc = grid_bumps([0.08 * G, 0.22 * G, 0.36 * G, 0.5 * G], -1.7 * BL, 1.75 * BL, 0.22 * s, top_y, 0.07 * s, ry=0.06 * s, rz=0.085 * s, jitter=1.0)
        sc = sc.mirror_x()
        chest = chest.su(sc & half_space(2, 1, zc1), 0.025 * s)
        mid = mid.su(sc & half_space(2, -1, zc1) & half_space(2, 1, zc2), 0.025 * s)
        hip = hip.su(sc & half_space(2, -1, zc2), 0.025 * s)
    if P["spines"] > 0:
        sp = P["spines"] * s
        zs = np.linspace(-1.95 * BL, 1.7 * BL, 15)
        base = [(0, float(top_y(z, 0)) - 0.02 * s, z) for z in zs]
        tips = [(0, b[1] + sp * (0.55 + 0.45 * math.sin(math.pi * (i + 1) / 16)), b[2] + 0.08 * s) for i, b in enumerate(base)]
        sps = spikes(base, tips, 0.06 * s, 0.012 * s)
        chest = chest.su(sps & half_space(2, 1, zc1), 0.03 * s)
        mid = mid.su(sps & half_space(2, -1, zc1) & half_space(2, 1, zc2), 0.03 * s)
        hip = hip.su(sps & half_space(2, -1, zc2), 0.03 * s)
    if P["crest"] > 0:  # newt: wavy skin crest along the spine
        cr = P["crest"] * s

        def crest_sdf(z0, z1):
            zz = np.linspace(z0, z1, 6)
            pts_ = [(0, float(top_y(z, 0)) + cr * 0.25, z) for z in zz]
            return eloft(pts_, [0.045 * s] * 6, [cr * (0.7 + 0.3 * math.sin(i * 1.3)) for i in range(6)], k=0.05 * s)

        chest = chest.su(crest_sdf(-1.7 * BL, zc1), 0.03 * s)
        mid = mid.su(crest_sdf(zc1, zc2), 0.03 * s)
        hip = hip.su(crest_sdf(zc2, 1.7 * BL), 0.03 * s)
    if P["beard"]:  # side fringe of spikes
        zs = np.linspace(-1.2 * BL, 1.2 * BL, 9)
        base = [(float(rx_at(z)) * 0.92, float(yc_at(z)), z) for z in zs]
        tips = [(b[0] + 0.14 * s, b[1] + 0.02 * s, b[2]) for b in base]
        fr = spikes(base, tips, 0.045 * s, 0.01 * s).mirror_x()
        mid = mid.su(fr & half_space(2, -1, zc1) & half_space(2, 1, zc2), 0.03 * s)
    if P["sail"] > 0:  # dimetrodon: tall spined sail on Body
        sh_ = P["sail"] * s

        def sail_h(z):
            u = np.clip((z + 1.3 * BL) / (2.6 * BL), 0, 1)
            return sh_ * np.sin(np.pi * u) ** 0.8

        def sail_f(p):
            z = np.clip(p[:, 2], -1.3 * BL, 1.3 * BL)
            y0 = top_y(z, 0) - 0.08 * s
            h = sail_h(z)
            # rounded top edge: distance in the y/z plane to the sail outline (approx), thickness in x
            dy = np.maximum(p[:, 1] - (y0 + h), y0 - p[:, 1])
            dz = np.abs(p[:, 2] - z)
            inside = np.maximum(dy, dz)
            return np.maximum(inside, np.abs(p[:, 0]) - 0.03 * s)

        sail = SDF(sail_f)
        zs = np.linspace(-1.2 * BL, 1.2 * BL, 13)
        rays = spikes([(0, float(top_y(z, 0)) - 0.1 * s, z) for z in zs],
                      [(0, float(top_y(z, 0)) + float(sail_h(z)) + 0.04 * s, z) for z in zs], 0.06 * s, 0.035 * s)
        sail = sail.su(rays, 0.03 * s)
        H.bone("Sail", "Body", (0, bodyY + 0.4 * s, 0))
        H.piece("SailP", "Sail", sail, col="secondary", tris=1500, res=128, role="body", pri=1.2,
                pattern=stripes(lambda Q: Q[:, 1] / s, 1.4, width=0.25, depth=0.35, seed=3))
    H.piece("ChestP", "Front", warty(rough(chest, 1, 1), 1), col="primary", tris=1400, res=112, pattern=skin())
    H.piece("Torso", "Body", warty(rough(mid, 1, 2), 2), col="primary", tris=2000, res=128, pattern=skin())
    H.piece("HipP", "Hips", warty(rough(hip, 1, 3), 3), col="primary", tris=1400, res=112, pattern=skin())
    if P["belly"]:
        bel = eloft(pts[1:5], [r * 1.025 for r in trx[1:5]], [r * 1.03 for r in try_[1:5]], k=0.3 * s)
        bel = bel & SDF(lambda p: p[:, 1] - (yc_at(p[:, 2]) - 0.42 * ry_at(p[:, 2])))
        H.piece("Belly", "Body", bel, col="secondary", tris=700, role="body", pri=1.4,
                pattern=stripes(lambda Q: Q[:, 2] / s, 4.2, width=0.12, depth=0.18, seed=1) if P["scutes"] else None)

    # ------------------------------------------------------------------ legs
    legs = []
    rig_legs = []
    LR = P["legr"]
    for front in (True, False):
        zc = zF - 0.1 * BL if front else zH + 0.05 * BL
        par = "Front" if front else "Hips"
        tag = "F" if front else "B"
        sx = float(rx_at(zc)) * 0.78
        sh = _v((sx, bodyY - 0.06 * s, zc))
        reach = (0.42 if front else 0.5) * LG
        el = sh + _v((reach, -0.1 * LG, 0.06 * s if front else -0.12 * s))
        if P["zygo"]:  # chameleon: upright legs under the body
            el = sh + _v((0.12 * s, -0.42 * LG, -0.05 * s if front else 0.05 * s))
        wr = _v((el[0] + (0.06 * s if not P["zygo"] else 0.0), 0.13 * s * max(LG / s, 0.6), el[2] + (-0.06 * s if front else 0.12 * s)))
        H.mbone(f"Up{tag}#", par, tuple(sh))
        H.mbone(f"Lo{tag}#", f"Up{tag}#", tuple(el))
        H.mbone(f"Ft{tag}#", f"Lo{tag}#", tuple(wr))
        r0 = (0.2 if front else 0.25) * s * LR
        up = round_cone(tuple(sh - _v((0.12 * s, 0, 0))), tuple(el), r0, r0 * 0.68)
        up = up.su(ellipsoid(r0 * 1.0, r0 * 0.85, r0 * 1.1, tuple((sh + el) / 2 + _v((0, 0.02 * s, 0.02 * s)))), 0.08 * s)
        H.mpiece(f"Upper{tag}#", f"Up{tag}#", warty(rough(up, 0.6, 5)), col="primary", tris=550, role="limb", pattern=skin())
        lo = round_cone(tuple(el), tuple(wr + _v((0, 0.03 * s, 0))), r0 * 0.7, r0 * 0.48)
        lo = lo.su(sphere(r0 * 0.72, tuple(el)), 0.04 * s)
        H.mpiece(f"Lower{tag}#", f"Lo{tag}#", warty(rough(lo, 0.5, 6)), col="primary", tris=420, role="limb", pattern=skin())
        # foot: palm + splayed toes, flat sole
        ft = ellipsoid(r0 * 0.85, r0 * 0.42, r0 * 1.05, tuple(wr + _v((0.03 * s, -0.06 * s, -0.08 * s))))
        ft = ft.su(round_cone(tuple(wr + _v((0, 0.04 * s, 0))), tuple(wr + _v((0.02 * s, -0.05 * s, -0.05 * s))), r0 * 0.5, r0 * 0.55), 0.05 * s)
        toes = []
        if P["zygo"]:  # chameleon: two mitten bundles gripping
            for ang in (-35, 145):
                a = math.radians(ang)
                d = _v((math.sin(a), 0, -math.cos(a)))
                tip = wr + _v((0, -0.09 * s, 0)) + d * 0.22 * s
                toes.append(round_cone(tuple(wr + _v((0, -0.05 * s, 0))), tuple(tip), 0.07 * s, 0.045 * s))
        else:
            n = 5
            spread = (-20, 75) if front else (-12, 70)
            lens = [0.6, 0.85, 1.0, 1.05, 0.75] if not front else [0.6, 0.85, 1.0, 0.9, 0.7]
            for i in range(n):
                ang = math.radians(spread[0] + (spread[1] - spread[0]) * i / (n - 1))
                d = _v((math.sin(ang), 0, -math.cos(ang)))
                L = (0.3 if front else 0.4) * s * lens[i] * max(LG / s, 0.7) * (0.9 if P["toe_pads"] else 1.0)
                base = wr + _v((0.03 * s, -0.08 * s, -0.08 * s)) + d * 0.06 * s
                tip = base + d * L + _v((0, -0.03 * s, 0))
                toe = round_cone(tuple(base), tuple(tip), 0.055 * s * LR, 0.032 * s * LR)
                if P["toe_pads"]:
                    toe = toe.su(ellipsoid(0.07 * s, 0.035 * s, 0.07 * s, tuple(tip + _v((0, 0.0, 0)))), 0.02 * s)
                toes.append(toe)
        for t_ in toes:
            ft = ft.su(t_, 0.035 * s)
        ft = ft & plane((0, -1, 0), 0.0)
        H.mpiece(f"Foot{tag}#", f"Ft{tag}#", ft, col="primary", tris=650, role="foot", pattern=skin(lambda Q: np.ones(len(Q)) * 0.9))
        ph = 0.0 if front else 0.5
        legs.append((f"Up{tag}R", f"Lo{tag}R", f"Ft{tag}R", ph, 1, front))
        legs.append((f"Up{tag}L", f"Lo{tag}L", f"Ft{tag}L", (ph + 0.5) % 1.0, -1, front))
        rig_legs += [{"hip": f"Up{tag}R", "knee": f"Lo{tag}R", "phase": ph, "side": 1}, {"hip": f"Up{tag}L", "knee": f"Lo{tag}L", "phase": (ph + 0.5) % 1.0, "side": -1}]

    # ------------------------------------------------------------------ neck + head
    HD = HEADS[P["head"]]
    hs = P["hs"] * s
    nz0 = tz[0] + 0.15 * BL
    hc = _v((0, bodyY + 0.06 * s + (0.12 * s if P["zygo"] else 0), tz[0] - P["neck"] * s))
    H.bone("Neck", "Front", (0, bodyY + 0.02 * s, nz0))
    H.bone("Head", "Neck", tuple(hc))
    neck = eloft([(0, bodyY + 0.02 * s, nz0 + 0.25 * BL), (0, bodyY + 0.03 * s, nz0 - 0.1 * s), tuple(hc + _v((0, -0.04 * s, 0.05 * s)))],
                 [trx[1] * 0.9, trx[0] * 0.95, HD["w"][0] * hs * 0.95], [try_[1] * 0.9, try_[0], (HD["t"][0] + HD["jd"][0]) * hs * 0.5], k=0.15 * s)
    if P["dewlap"] > 0:
        dw = P["dewlap"] * s

        def dew(p):
            # thin flap below the throat, fan shaped
            q = p - (hc + _v((0, -0.18 * hs, 0.05 * s)))
            r = np.sqrt(q[:, 1] ** 2 + (q[:, 2] * 0.9) ** 2)
            ang_ok = np.maximum(q[:, 1], -0.0)  # keep lower half
            return np.maximum(np.maximum(r - dw, ang_ok - 0.02 * s), np.abs(q[:, 0]) - 0.025 * s)

        neck = neck.su(SDF(dew), 0.04 * s)
    H.piece("NeckP", "Neck", warty(rough(neck, 0.7, 7), 7), col="primary", tris=800, role="neck", pattern=skin())

    def h(x, y, z):
        return tuple(hc + _v((x * hs, y * hs, z * hs)))

    mouth_y = -0.04
    zs, ws, ts = HD["z"], HD["w"], HD["t"]
    up_pts = [h(0, mouth_y, z) for z in zs]
    head = eloft(up_pts, [w * hs for w in ws], [t * hs for t in ts], k=0.12 * hs)
    head = head & half_space(1, -1, hc[1] + (mouth_y - 0.005) * hs)
    zmid = zs[1]
    if P["eyes"] == "top":  # crocodilian eye turrets + brow
        head = head.su(sphere(0.12 * hs, h(0.19, 0.26, zmid - 0.3)).mirror_x(), 0.08 * hs)
        head = head.su(ellipsoid(0.07 * hs, 0.06 * hs, 0.05 * hs, h(0.0, ts[-2] - 0.0, zs[-2])), 0.04 * hs)  # nostril dome
        eye_pos = (0.19 * hs, 0.31 * hs, (zmid - 0.3) * hs)
    else:
        ez = zmid - 0.18 * (zs[0] - zs[-1]) / 1.0
        ew = float(_interp(ez, zs, ws))
        et = float(_interp(ez, zs, ts))
        eye_pos = (ew * 0.82 * hs, (mouth_y + et * 0.62) * hs, ez * hs)
        head = head.su(ellipsoid(0.07 * hs, 0.05 * hs, 0.14 * hs, h(ew * 0.6, mouth_y + et * 0.98, ez)).mirror_x(), 0.06 * hs)  # brow
    if P["cheek"]:  # iguana subtympanic shield (a round plate bump)
        head = head.su(cylinder(0.11 * hs, 0.03 * hs, axis=0).at(*h(ws[0] * 0.95, mouth_y + 0.02, zs[0] - 0.15)).mirror_x(), 0.03 * hs)
    if P["casque"]:  # chameleon helmet
        head = head.su(round_cone(h(0, ts[1] * 0.8, zs[1]), h(0, ts[1] + 0.26, zs[0] + 0.22), 0.17 * hs, 0.06 * hs), 0.12 * hs)
        head = head.su(capsule(h(0.15, ts[2] * 0.9, zs[2]), h(0.08, ts[1] + 0.2, zs[0] + 0.05), 0.04 * hs).mirror_x(), 0.05 * hs)
    if P["horns"]:  # horned lizard crown
        hb = [h(0.12, 0.15, 0.12), h(0.24, 0.12, 0.08), h(0.33, 0.06, 0.0), h(0.37, 0.0, -0.1)]
        ht = [h(0.17, 0.42, 0.42), h(0.36, 0.34, 0.35), h(0.5, 0.18, 0.18), h(0.53, 0.05, 0.02)]
        hr = spikes(hb, ht, 0.06 * hs, 0.012 * hs).mirror_x()
        H.piece("Horns", "Head", hr, col="horn", mat="hard", tris=700, role="horn", pri=1.3)
    if P["beard"]:
        bb = [h(0.24, -0.02, 0.05), h(0.3, 0.06, 0.15), h(0.2, 0.2, 0.2)]
        bt = [h(0.4, -0.05, 0.12), h(0.45, 0.12, 0.25), h(0.3, 0.32, 0.3)]
        head = head.su(spikes(bb, bt, 0.04 * hs, 0.01 * hs).mirror_x(), 0.02 * hs)
    head = rough(head, 0.5, 9)
    H.piece("HeadP", "Head", head, col="primary", tris=2000 if P["head"] in ("croc", "gator", "gharial") else 1500, res=128, role="head", pattern=skin())
    # lower jaw: hinge at the back of the skull
    jw = _v(h(0, mouth_y - 0.02, zs[0] - 0.05))
    H.bone("Jaw", "Head", tuple(jw))
    jz, jws, jd = HD["jz"], HD["jw"], HD["jd"]
    jaw = eloft([h(0, mouth_y + 0.01, z) for z in jz], [w * hs for w in jws], [d * hs for d in jd], k=0.1 * hs)
    jaw = jaw & half_space(1, 1, hc[1] + (mouth_y + 0.025) * hs)
    if P["dewlap"] > 0:  # iguana dewlap hangs from the jaw
        dw = P["dewlap"] * s
        dc = _v(h(0, mouth_y - 0.1, (jz[1] + jz[2]) * 0.5))

        def dew2(p):
            q = p - dc
            r = np.sqrt((q[:, 1] / 1.0) ** 2 + (q[:, 2] / 0.85) ** 2)
            return np.maximum(np.maximum(r - dw, q[:, 1] - 0.02 * s), np.abs(q[:, 0]) - 0.03 * s * (1 - 0.5 * np.clip(-q[:, 1] / dw, 0, 1)))

        jaw = jaw.su(SDF(dew2), 0.05 * s)
    if P["beard"]:
        bb = [h(x, mouth_y - 0.12, z) for x in (-0.18, -0.06, 0.06, 0.18) for z in (jz[1], jz[2])]
        bt = [(b[0] * 1.2, b[1] - 0.16 * hs, b[2] + 0.04 * hs) for b in bb]
        jaw = jaw.su(spikes(bb, bt, 0.035 * hs, 0.008 * hs), 0.02 * hs)
    H.piece("JawP", "Jaw", rough(jaw, 0.4, 10), col="primary", tris=900, role="jaw", pri=1.3,
            pattern=combine(lambda Q: np.ones(len(Q)) * 1.0, None))
    H.prim("Mouth", "Jaw", "Ellipsoid", (float(_interp(-0.4, jz, jws)) * 1.5 * hs, 0.05 * hs, abs(jz[-1] - jz[0]) * 0.85 * hs),
           h(0, mouth_y + 0.0, (jz[0] + jz[-1]) * 0.5), col="mouth", mat="hard", role="mouth", pri=2.4)
    if P["teeth"]:
        n = P["teeth"]
        tzz = np.linspace(zs[1] - 0.25, zs[-1] + 0.12, n)
        tb = [h(float(_interp(z, zs, ws)) * 0.9, mouth_y + 0.01, z) for z in tzz]
        tt = [(b[0] + 0.01 * hs, b[1] - (0.09 + 0.05 * math.sin(i * 1.7) ** 2) * hs, b[2]) for i, b in enumerate(tb)]
        H.piece("TeethU", "Head", spikes(tb, tt, 0.028 * hs, 0.006 * hs).mirror_x(), col="tooth", mat="hard", tris=700, role="tooth", pri=1.8, ao=False, smooth=2)
        lzz = np.linspace(jz[1] - 0.3, jz[-1] + 0.1, max(3, n // 2))
        lb = [h(float(_interp(z, jz, jws)) * 0.82, mouth_y + 0.02, z) for z in lzz]
        lt = [(b[0], b[1] + 0.08 * hs, b[2]) for b in lb]
        H.piece("TeethL", "Jaw", spikes(lb, lt, 0.025 * hs, 0.006 * hs).mirror_x(), col="tooth", mat="hard", tris=450, role="tooth", pri=1.9, ao=False, smooth=2)
    # eyes
    if P["turret"]:
        ex, ey, ez = eye_pos
        ex += 0.05 * hs
        tur = sphere(0.13 * hs, (ex + 0.03 * hs + hc[0], ey + hc[1], ez + hc[2]))
        H.mpiece("Turret#", "Head", tur.su(sphere(0.09 * hs, (ex - 0.04 * hs + hc[0], ey + hc[1], ez + hc[2])), 0.04 * hs),
                 col="primary", tris=380, role="eye", pri=1.3, pattern=stripes(lambda Q: np.arctan2(Q[:, 1] - (ey + hc[1]), Q[:, 2] - (ez + hc[2])), 1.6, width=0.3, depth=0.3))
        H.mprim("Pupil#", "Head", "Ball", (0.06 * hs,) * 3, (ex + 0.15 * hs, ey + hc[1], ez + hc[2] - 0.035 * hs), col="pupil", mat="hard", role="pupil", pri=1.5)
    else:
        er = P["eye_r"] * hs
        look = (0.55, 0.65, -0.5) if P["eyes"] == "top" else (0.85, 0.15, -0.45)
        H.eyes("Head", (eye_pos[0] + hc[0] - (0.0 if P["eyes"] == "top" else er * 0.25), eye_pos[1] + hc[1], eye_pos[2] + hc[2]), er,
               col="iris", pupil=P["pupil"], look=look)
    # forked tongue / sticky tongue (hidden in the mouth, slides out on Attack)
    tongue = None
    if P["tongue"] == "fork":
        H.bone("Tongue", "Jaw", h(0, mouth_y - 0.02, zs[1]))
        L = abs(zs[-1] - zs[1]) * 0.85
        tg = round_cone(h(0, mouth_y - 0.02, zs[1] + 0.05), h(0, mouth_y - 0.02, zs[1] - L), 0.05 * hs, 0.035 * hs)
        tg = tg.su(round_cone(h(0, mouth_y - 0.02, zs[1] - L), h(0.06, mouth_y - 0.02, zs[1] - L - 0.18), 0.03 * hs, 0.012 * hs).mirror_x(), 0.02 * hs)
        H.piece("TongueP", "Tongue", tg, col="tongue", tris=300, role="tongue", pri=2.0, ao=False)
        tongue = ("Tongue", (L + 0.35) * hs, (0, 0, 1))
    elif P["tongue"]:  # chameleon: telescoping ballistic tongue with a sticky club
        L = abs(zs[-1] - zs[1]) * 0.8
        reach = 2.2 * s
        tongue = []
        for k in range(5):
            nm = "Tongue" if k == 0 else f"Tongue{k}"
            H.bone(nm, "Jaw", h(0, mouth_y - 0.02, zs[1]))
            sd = round_cone(h(0, mouth_y - 0.02, zs[1] + 0.03), h(0, mouth_y - 0.02, zs[1] - L), 0.045 * hs, 0.04 * hs)
            if k == 4:
                sd = sd.su(sphere(0.085 * hs, h(0, mouth_y - 0.02, zs[1] - L)), 0.02 * hs)
            H.piece(f"TongueP{k}", nm, sd, col="tongue", tris=180 if k < 4 else 280, role="tongue", pri=2.0 + 0.05 * k, ao=False)
            if k:
                tongue.append((nm, reach * k / 4, (0, 0, 1)))
    # frill (frilled lizard): two big fans, ribbed, open around the neck
    frill_bones = []
    if P["frill"] > 0:
        fr = P["frill"] * s
        H.mbone("Frill#", "Head", h(0.2, mouth_y, zs[0] + 0.1))
        c0 = _v(h(0.0, mouth_y + 0.02, zs[0] + 0.12))

        def frill_f(p):
            q = p - c0
            ang = np.arctan2(q[:, 1], q[:, 0])
            r = np.sqrt(q[:, 0] ** 2 + q[:, 1] ** 2)
            scal = fr * (0.92 + 0.08 * np.cos(ang * 9))
            # cone-shaped (dish) membrane opening forward
            zt = q[:, 2] - 0.25 * r
            d = np.maximum(r - scal, -(r - 0.12 * s))
            d = np.maximum(d, np.abs(zt) - 0.03 * s)
            return np.maximum(d, -q[:, 0] + 0.0)

        frill = SDF(frill_f)
        ribs = spikes([tuple(c0 + _v((math.cos(a) * 0.15 * s, math.sin(a) * 0.15 * s, 0.04 * s))) for a in np.linspace(-1.35, 1.35, 7)],
                      [tuple(c0 + _v((math.cos(a) * fr * 0.95, math.sin(a) * fr * 0.95, 0.25 * fr * 0.95))) for a in np.linspace(-1.35, 1.35, 7)], 0.03 * s, 0.015 * s)
        H.mpiece("Frill#", "Frill#", frill.su(ribs, 0.02 * s), col="secondary", tris=1300, res=112, role="mane", pri=1.1,
                 pattern=combine(lambda Q: 1 - 0.45 * np.clip((np.linalg.norm(Q[:, :2] - c0[:2], axis=1) - 0.5 * fr) / (0.5 * fr), 0, 1),
                                 stripes(lambda Q: np.arctan2(Q[:, 1] - c0[1], np.abs(Q[:, 0])), 2.5, width=0.2, depth=0.25)))
        frill_bones = [("FrillR", 1), ("FrillL", -1)]
    # gills (axolotl): three feathery fronds per side
    gill_bones = []
    if P["gills"]:
        H.mbone("Gill#", "Head", h(ws[0] * 0.8, 0.1, zs[0]))
        g = None
        for i, (a, L) in enumerate(((35, 0.42), (0, 0.48), (-35, 0.4))):
            ar = math.radians(a)
            b0 = _v(h(ws[0] * 0.85, 0.1 + 0.08 * math.sin(ar), zs[0] + 0.02))
            d = _v((math.cos(ar) * 0.7, math.sin(ar) * 0.9 + 0.35, 0.45))
            d /= np.linalg.norm(d)
            tip = b0 + d * L * hs
            stalk = round_cone(tuple(b0), tuple(tip), 0.045 * hs, 0.025 * hs)
            for j in range(5):
                u = 0.25 + 0.15 * j
                c = b0 + d * L * hs * u
                stalk = stalk.su(ellipsoid(0.03 * hs, 0.09 * hs, 0.03 * hs, tuple(c + _v((0, 0, 0.04 * hs)))).rot(0, 0, 0), 0.02 * hs)
            g = stalk if g is None else (g | stalk)
        H.mpiece("Gills#", "Gill#", g, col="secondary", tris=900, res=112, role="mane", pri=1.2)
        gill_bones = [("GillR", 1), ("GillL", -1)]

    # ------------------------------------------------------------------ tail
    T = P["tail"]
    TR = P["tailr"]
    n = 5
    tb_ = [_v((0, tyc[-1] + 0.01 * s, tz[-1] - 0.25 * BL))]
    seg = 0.8 * s * T
    tails = []
    curl = P["tail_curl"]
    for i in range(n):
        p = tb_[-1]
        if curl and i >= 2:
            a = math.radians(-20 + 75 * (i - 1))
            d = _v((0, -math.sin(a), math.cos(a)))
            tb_.append(p + d * seg * (0.62 - 0.1 * i))
        else:
            tb_.append(p + _v((0, -0.07 * s - (0.06 * s if i == 0 else 0.03 * s), seg * (1.0 - 0.05 * i))))
    rad = [0.36 * G * TR, 0.27 * G * TR, 0.19 * G * TR, 0.12 * G * TR, 0.075 * G * TR, 0.035 * s]
    for i in range(n):
        H.bone(f"Tail{i + 1}", "Hips" if i == 0 else f"Tail{i}", tuple(tb_[i]))
        tails.append(f"Tail{i + 1}")
    for i in range(n):
        a = tb_[i] - (_v((0, 0, 0.12 * s)) if not (curl and i >= 3) else (tb_[i + 1] - tb_[i]) * 0.15)
        b = tb_[i + 1]
        fl = P["tail_flat"]
        st = 0.93 if i > 0 else 1.0
        sd = eloft([tuple(a), tuple(b)], [rad[i] * fl * st, rad[i + 1] * fl], [rad[i] * st, rad[i + 1]])
        if P["tail_crest"]:  # crocodilian double row of keeled plates merging into one row
            m = 4
            for j in range(m):
                u = (j + 0.5) / m
                c = a + (b - a) * u
                r_ = rad[i] + (rad[i + 1] - rad[i]) * u
                hgt = 0.06 * s + r_ * 0.45
                x = r_ * 0.38 * P["tail_flat"] if i < 2 else 0.0
                pl = ellipsoid(0.028 * s, hgt, 0.085 * s, tuple(c + _v((x, r_ * 0.8 + hgt * 0.35, 0.0))))
                sd = sd.su(pl.mirror_x() if x > 0 else pl, 0.025 * s)
        if P["spines"] > 0 and i < 3:
            sp = P["spines"] * s * (1 - 0.3 * i)
            base = [tuple(a + (b - a) * u + _v((0, rad[i] * 0.8, 0))) for u in (0.2, 0.6)]
            tips = [(x, y + sp * 0.7, z + 0.08 * s) for x, y, z in base]
            sd = sd.su(spikes(base, tips, 0.045 * s, 0.01 * s), 0.02 * s)
        if P["crest"] > 0:
            cr = P["crest"] * s
            sd = sd.su(eloft([tuple(a + _v((0, rad[i] * 0.6, 0))), tuple(b + _v((0, rad[i + 1] * 0.5, 0)))], [0.045 * s, 0.035 * s], [cr * 1.4, cr]), 0.03 * s)
            sd = sd.su(eloft([tuple(a + _v((0, -rad[i] * 0.6, 0))), tuple(b + _v((0, -rad[i + 1] * 0.5, 0)))], [0.045 * s, 0.035 * s], [cr * 1.0, cr * 0.8]), 0.03 * s) if i >= 1 else sd
        if P["beard"] and i < 3:
            base = [tuple(a + (b - a) * u + _v((rad[i] * 0.85, 0, 0))) for u in (0.3, 0.75)]
            tips = [(x + 0.1 * s, y, z) for x, y, z in base]
            sd = sd.su(spikes(base, tips, 0.035 * s, 0.008 * s).mirror_x(), 0.02 * s)
        tp = skin(stripes(lambda Q: Q[:, 2] / s, 1.6, width=0.35, depth=0.45, seed=5) if P["pattern"] in ("bands", "ringtail") else None)
        H.piece(f"TailP{i + 1}", f"Tail{i + 1}", warty(rough(sd, 0.6, 20 + i), 20 + i), col="primary", tris=max(260, 620 - 70 * i), role="tail", pri=1.4 + 0.1 * i, pattern=tp)

    # ------------------------------------------------------------------ secondary-colour spots (salamanders)
    if P["spots2"]:
        rng = np.random.default_rng(P["spots2"])

        def blots(z0, z1, k, side_only=False):
            sd = None
            for _ in range(k):
                z = rng.uniform(z0, z1)
                x = rng.uniform(-0.7, 0.7) * float(rx_at(z))
                y = float(top_y(z, x)) + 0.02 * s
                r = rng.uniform(0.12, 0.19) * s
                e = ellipsoid(r, r * 0.45, r * 1.2, (x, y, z))
                sd = e if sd is None else (sd | e)
            return sd

        H.piece("SpotsF", "Front", blots(-1.7 * BL, -0.6 * BL, 5), col="secondary", tris=500, role="detail", pri=1.6)
        H.piece("SpotsM", "Body", blots(-0.5 * BL, 0.6 * BL, 6), col="secondary", tris=550, role="detail", pri=1.6)
        H.piece("SpotsB", "Hips", blots(0.7 * BL, 1.6 * BL, 4), col="secondary", tris=450, role="detail", pri=1.7)

    # ------------------------------------------------------------------ rig + motion
    tipz = float(h(0, 0, zs[-1])[2])
    H.socket("mouth", h(0, mouth_y, zs[-1] - 0.05), "Head")
    H.socket("head", h(0, max(ts) + 0.1, zs[1]), "Head")
    H.socket("seat", (0, bodyY + 0.45 * G * TALL, 0), "Body")
    H.rig.update({"head": "Head", "jaw": "Jaw", "neck": "Neck", "tail": tails, "legs": rig_legs})
    height = bodyY + 0.4 * s
    if P["swim"]:
        MR.swimtail(H, ["Front", "Hips"], tails, head="Head", jaw="Jaw", limbs=[(l[0], l[4]) for l in legs], walk=1.3, height=height,
                    amp=0.22, gills=gill_bones)
    else:
        MR.sprawl(H, legs, front="Front", hips="Hips", neck="Neck", head="Head", jaw="Jaw", tail=tails, stride=P["stride"],
                  walk=P["walk"], height=height, attack=P["attack"], tongue=tongue, frill=frill_bones,
                  bend=0.08 if P["zygo"] else 0.14, tailwave=0.08 if curl else 0.22)
    return H


# ==================================================================================================== crocodilians
@hero("crocodile", FAM)
def crocodile():
    return _sprawler("crocodile", head="croc", hs=1.15, bodyY=0.7, leg=0.9, legr=1.2, scutes=True, tail=1.15, tail_flat=0.6, tail_crest=True, teeth=11,
                     eyes="top", eye_r=0.075, shade=0.72, pattern="scutegrid", pat_depth=0.9, attack="roll", body=1.05,
                     walk=1.2, stride=0.42, preview={"primary": "#5A6A3A", "secondary": "#C8C08A", "iris": "#C9B43A"})


@hero("alligator", FAM)
def alligator():
    return _sprawler("alligator", head="gator", hs=1.12, bodyY=0.68, leg=0.85, legr=1.25, girth=1.08, scutes=True, tail=1.1, tail_flat=0.62,
                     tail_crest=True, teeth=9, eyes="top", eye_r=0.075, shade=0.6, pattern="scutegrid", pat_depth=1.0, attack="roll",
                     walk=1.25, stride=0.4, preview={"primary": "#2A3A2A", "secondary": "#C8C098", "iris": "#B8A030"})


@hero("gharial", FAM)
def gharial():
    return _sprawler("gharial", head="gharial", hs=1.0, bodyY=0.66, leg=0.8, legr=1.1, girth=0.95, scutes=True, tail=1.2, tail_flat=0.55,
                     tail_crest=True, teeth=16, eyes="top", eye_r=0.07, shade=0.75, pattern="bands", pat_depth=0.35, attack="snap",
                     walk=1.25, stride=0.4, preview={"primary": "#6A7A5A", "secondary": "#C8C8A8", "iris": "#B8A030"})


# ==================================================================================================== lizards
@hero("komodo dragon", FAM)
def komodo():
    return _sprawler("komodo dragon", head="monitor", hs=1.4, bodyY=0.85, leg=1.0, legr=1.35, girth=1.0, tall=1.15, neck=0.75, tail=0.95,
                     tail_flat=0.8, rough=0.012, eyes="side", eye_r=0.06, pupil="round", shade=0.85, attack="snap", tongue="fork",
                     walk=1.15, stride=0.45, preview={"primary": "#6E6450", "secondary": "#A89A7A", "iris": "#C8A040", "tongue": "#E8C040"})


@hero("monitor lizard", FAM)
def monitor():
    return _sprawler("monitor lizard", head="monitor", hs=1.3, bodyY=0.82, leg=1.0, legr=1.15, girth=0.88, tall=1.1, neck=0.8, tail=1.15,
                     tail_flat=0.75, pattern="rings", pat_depth=0.5, eyes="side", eye_r=0.06, pupil="round", shade=0.8, attack="snap",
                     tongue="fork", walk=1.0, stride=0.5, preview={"primary": "#4A4A3A", "secondary": "#C8C08A", "iris": "#C8A040", "tongue": "#E8A0B0"})


@hero("lizard", FAM)
def lizard():
    return _sprawler("lizard", head="lizard", hs=1.15, bodyY=0.8, leg=1.05, legr=0.9, girth=0.78, tall=1.15, neck=0.45, tail=1.15,
                     tail_flat=0.95, pattern="spots", pat_depth=0.45, eyes="side", eye_r=0.08, pupil="round", shade=0.75, attack="snap",
                     tongue="fork", walk=0.8, stride=0.55, preview={"primary": "#6AA04A", "secondary": "#E8E07A", "iris": "#D9A13B"})


@hero("iguana", FAM)
def iguana():
    return _sprawler("iguana", head="lizard", hs=1.2, bodyY=0.85, leg=1.05, legr=1.05, girth=0.85, tall=1.25, neck=0.45, tail=1.35,
                     tail_flat=0.85, spines=0.32, dewlap=0.42, cheek=True, pattern="bands", pat_depth=0.3, eyes="side", eye_r=0.085,
                     pupil="round", shade=0.85, attack="tailwhip", walk=1.0, stride=0.5,
                     preview={"primary": "#6AA04A", "secondary": "#3A6A2A", "iris": "#D96A2B"})


@hero("gecko", FAM)
def gecko():
    return _sprawler("gecko", head="gecko", hs=1.4, bodyY=0.72, leg=1.0, legr=0.95, girth=0.8, tall=1.05, neck=0.3, tail=0.85, tailr=1.3,
                     tail_flat=1.0, toe_pads=True, pattern="spots", pat_depth=0.55, eyes="side", eye_r=0.13, pupil="slit", shade=0.85,
                     attack="snap", walk=0.75, stride=0.55, body=0.85,
                     preview={"primary": "#8AC84A", "secondary": "#F2E8A0", "iris": "#C9A03A"})


@hero("chameleon", FAM)
def chameleon():
    return _sprawler("chameleon", head="chameleon", hs=1.5, bodyY=1.1, leg=1.0, legr=1.0, girth=0.62, tall=1.6, neck=0.15, tail=0.8,
                     tail_flat=0.85, tail_curl=True, zygo=True, casque=True, turret=True, spines=0.08, pattern="bands", pat_depth=0.25,
                     shade=0.85, attack="tongue", tongue="ball", walk=1.6, stride=0.35, body=0.8, belly=True,
                     preview={"primary": "#6AC84A", "secondary": "#E8701E", "tongue": "#E8607A"})


@hero("frilled lizard", FAM)
def frilled():
    return _sprawler("frilled lizard", head="lizard", hs=1.1, bodyY=0.85, leg=1.1, legr=0.9, girth=0.75, tall=1.1, neck=0.45, tail=1.3,
                     tail_flat=1.0, frill=1.05, eyes="side", eye_r=0.08, pupil="round", shade=0.8, attack="frill", walk=0.8, stride=0.55,
                     preview={"primary": "#B88A5A", "secondary": "#E8701E", "iris": "#D9A13B"})


@hero("horned lizard", FAM)
def horned():
    return _sprawler("horned lizard", head="horned", hs=1.35, bodyY=0.62, leg=0.8, legr=0.95, girth=1.05, tall=0.75, neck=0.2, tail=0.5,
                     tailr=1.1, tail_flat=1.3, body=0.85, horns=True, beard=True, warts=0.03, pattern="blotch", pat_depth=0.45, eyes="side",
                     eye_r=0.07, pupil="round", shade=0.85, attack="snap", walk=0.8, stride=0.5,
                     preview={"primary": "#C8A06A", "secondary": "#6A4A2A", "iris": "#C9A03A", "horn": "#D8C8A0"})


@hero("bearded dragon", FAM)
def bearded():
    return _sprawler("bearded dragon", head="lizard", hs=1.25, bodyY=0.72, leg=0.95, legr=1.0, girth=1.0, tall=0.85, neck=0.3, tail=0.95,
                     tail_flat=1.1, beard=True, warts=0.025, pattern="blotch", pat_depth=0.25, eyes="side", eye_r=0.075, pupil="round",
                     shade=0.85, attack="snap", walk=0.9, stride=0.5,
                     preview={"primary": "#C8A06A", "secondary": "#8A6A3A", "iris": "#C9A03A"})


# ==================================================================================================== amphibians (sprawlers)
@hero("salamander", FAM)
def salamander():
    return _sprawler("salamander", head="salamander", hs=1.3, bodyY=0.55, leg=0.75, legr=0.95, girth=0.72, tall=1.05, neck=0.25, tail=1.0,
                     tail_flat=0.75, eyes="side", eye_r=0.085, pupil="round", shade=0.95, spots2=11, belly=False, attack="snap",
                     walk=0.9, stride=0.5, preview={"primary": "#1E1E24", "secondary": "#F2D82A", "iris": "#2A2A2A"})


@hero("newt", FAM)
def newt():
    return _sprawler("newt", head="salamander", hs=1.25, bodyY=0.58, leg=0.8, legr=0.9, girth=0.68, tall=1.05, neck=0.25, tail=1.15,
                     tail_flat=0.45, crest=0.12, eyes="side", eye_r=0.085, pupil="round", shade=0.8, pattern="spots", pat_depth=0.55,
                     attack="snap", walk=0.9, stride=0.5, preview={"primary": "#E8701E", "secondary": "#3A3A2A", "iris": "#E8C030"})


@hero("axolotl", FAM)
def axolotl():
    return _sprawler("axolotl", head="axolotl", hs=1.45, bodyY=0.6, leg=0.7, legr=0.85, girth=0.75, tall=1.05, neck=0.2, tail=1.0,
                     tail_flat=0.4, crest=0.16, gills=True, eyes="side", eye_r=0.06, pupil=None, shade=0.95, swim=True, gait="swim",
                     preview={"primary": "#F2A8C0", "secondary": "#E8607A", "iris": "#1A1A1A"})


@hero("dimetrodon", FAM)
def dimetrodon():
    return _sprawler("dimetrodon", head="dimetrodon", hs=1.25, bodyY=0.85, leg=1.0, legr=1.3, girth=0.9, tall=1.15, neck=0.45, tail=1.1,
                     tail_flat=0.85, sail=1.7, teeth=7, eyes="side", eye_r=0.07, pupil="slit", shade=0.8, pattern="bands", pat_depth=0.25,
                     attack="snap", walk=1.1, stride=0.45, tags=("dinosaur",),
                     preview={"primary": "#8A4A2A", "secondary": "#E8902A", "iris": "#E8C030"})


# ==================================================================================================== turtles
TBASE = dict(s=1.0, L=1.25, W=1.0, dome=0.62, bodyY=0.72, plate_h=0.09, pyramid=0.0, keels=0.0, serrate=0.0, flat_back=False,
             flippers=False, column=False, leg=1.0, head=1.0, neck=0.55, beak_hook=0.0, tail=0.35, rings=0.0, rays=False,
             shell_rough=0.0, spiky_tail=False, attack="snap", walk=1.4, preview={})


def _turtle(hid, **kw):
    P = dict(TBASE)
    P.update(kw)
    s = P["s"]
    L, W, D = P["L"] * s, P["W"] * s, P["dome"] * s
    yc = P["bodyY"] * s
    sea = P["flippers"]
    H = Hero(hid, plan="Turtle", gait="swim" if sea else "waddle", tags=["reptile", "turtle"])
    H.preview = P["preview"]
    H.body((0, yc, 0))

    # ------------------------------------------------------------------ carapace: dome + pillowed scute plates + rim
    def shell_rz(x):
        return L

    dome = ellipsoid(W, D, L, (0, yc, 0))
    if sea:  # teardrop: narrow toward the tail
        dome = ellipsoid(W, D, L, (0, yc, 0)) & ellipsoid(W * 1.25, D * 1.3, L * 1.0, (0, yc, -0.25 * L))
    dome = dome & half_space(1, -1, yc - 0.02 * s)

    def surf(x, z):
        u = 1 - (x / W) ** 2 - (z / L) ** 2
        y = yc + D * math.sqrt(max(u, 0.02))
        n = _v((x / W ** 2, (y - yc) / D ** 2, z / L ** 2))
        return _v((x, y, z)), n / np.linalg.norm(n)

    plates = []
    for z in (-0.62, -0.31, 0.0, 0.31, 0.6):
        plates.append((0.0, z * L, 0.24 * s))
    for z in (-0.45, -0.12, 0.2, 0.5):
        plates.append((0.52 * W, z * L, 0.27 * s))
        plates.append((-0.52 * W, z * L, 0.27 * s))
    ph = P["plate_h"] * s
    shell = dome
    for x, z, fp in plates:
        c, n = surf(x, z)
        h_ = ph * (1.6 if P["pyramid"] and x == 0 else 1.0)
        R = (fp ** 2 + h_ ** 2) / (2 * h_)
        cap = sphere(R, tuple(c - n * (R - h_)))
        if sea:  # low plates = huge spheres: keep only the cap above the dome
            cap = cap & ellipsoid(W * 1.01, D + h_ * 1.1, L * 1.01, (0, yc, 0)) & half_space(1, -1, yc + 0.02 * s)
        shell = shell | cap
        if P["pyramid"] > 0:  # tortoise: raised plate centres (growth cones)
            shell = shell.su(sphere(0.09 * s, tuple(c + n * (h_ * 0.6))), 0.12 * s)
        if P["keels"] > 0:  # snapping turtle ridges
            shell = shell.su(round_cone(tuple(c), tuple(c + n * P["keels"] * s + _v((0, 0, 0.12 * s))), 0.08 * s, 0.02 * s), 0.05 * s)
    rim = ellipsoid(W * 1.06, 0.1 * s, L * 1.05, (0, yc - 0.0, 0))
    if sea:
        rim = rim & ellipsoid(W * 1.3, 0.4 * s, L * 1.04, (0, yc, -0.27 * L))
    if P["serrate"] > 0:
        for i in range(7):
            a = math.radians(115 + i * 22)
            c = _v((math.sin(a) * W * 1.0, yc - 0.01 * s, -math.cos(a) * L * 1.0))
            d = _v((math.sin(a), -0.05, -math.cos(a)))
            tip = c + d * P["serrate"] * s
            rim = rim | round_cone(tuple(c), tuple(tip), 0.08 * s, 0.02 * s)
            rim = rim | round_cone(tuple(c * _v((-1, 1, 1))), tuple(tip * _v((-1, 1, 1))), 0.08 * s, 0.02 * s)
    shell = shell.su(rim, 0.06 * s)
    if P["shell_rough"]:
        shell = shell.noise(P["shell_rough"] * s, 9.0 / s, 3)

    def seams(Q):  # darken the grooves between plates + growth rings
        d1 = np.full(len(Q), 9.0)
        d2 = np.full(len(Q), 9.0)
        for x, z, fp in plates:
            d = np.sqrt((Q[:, 0] - x) ** 2 + (Q[:, 2] - z) ** 2)
            m = d < d1
            d2 = np.where(m, d1, np.minimum(d2, d))
            d1 = np.where(m, d, d1)
        edge = np.clip(1 - (d2 - d1) / (0.07 * s), 0, 1)
        m = 1 - 0.6 * edge
        if P["rings"] > 0:
            m = m * (1 - P["rings"] * 0.5 * (0.5 + 0.5 * np.cos(d1 / (0.07 * s) * 2 * np.pi)) * np.clip(d1 / (0.12 * s), 0, 1))
        if P["rays"]:  # radiated / star tortoise: pale rays on dark plates (inverse: dark everywhere but rays)
            ang = np.arctan2(Q[:, 2], Q[:, 0])
            m = m * 1.0
        rimdark = np.clip((yc + 0.05 * s - Q[:, 1]) / (0.1 * s), 0, 1)
        return m * (1 - 0.25 * rimdark)

    H.piece("Shell", "Body", shell, col="primary", mat="hard", tris=2600, res=136, role="body", pattern=seams)
    plas = ellipsoid(W * 0.88, 0.17 * s, L * 0.93, (0, yc - 0.1 * s, 0.02 * s)) & half_space(1, 1, yc - 0.03 * s)
    H.piece("Plastron", "Body", plas, col="secondary", mat="hard", tris=600, role="body", pri=1.3,
            pattern=lambda Q: 1 - 0.3 * np.clip(1 - np.abs(np.mod(Q[:, 2] / (0.42 * s), 1.0) - 0.5) * 12, 0, 1))

    # ------------------------------------------------------------------ head + neck (on two bones, can retract)
    hs = P["head"] * s
    nb = _v((0, yc - 0.08 * s, -L * 0.82))
    hc = _v((0, yc + (0.02 if not sea else -0.02) * s, -L - P["neck"] * s))
    H.bone("Neck", "Body", tuple(nb))
    H.bone("Head", "Neck", tuple(hc))
    neck = round_cone(tuple(nb + _v((0, 0, 0.25 * s))), tuple(hc + _v((0, -0.04 * s, 0.08 * s))), 0.22 * hs, 0.17 * hs)
    neck = neck.su(ellipsoid(0.2 * hs, 0.14 * hs, 0.3 * s, tuple((nb + hc) / 2 + _v((0, -0.06 * s, 0)))), 0.08 * s)  # throat skin folds
    neck = neck.noise(0.008 * s, 14 / s, 2)
    skinpat = spots(0.12 * s, 0.035 * s, depth=0.35, seed=3) if not sea else spots(0.16 * s, 0.07 * s, depth=0.4, ring=True, seed=3)
    H.piece("NeckP", "Neck", neck, col="secondary", tris=700, role="neck", pattern=skinpat)

    def h(x, y, z):
        return tuple(hc + _v((x * hs, y * hs, z * hs)))

    head = ellipsoid(0.24, 0.22, 0.3, h(0, 0.04, -0.12)).scale(hs) if False else ellipsoid(0.24 * hs, 0.21 * hs, 0.3 * hs, h(0, 0.05, -0.12))
    head = head.su(ellipsoid(0.17 * hs, 0.14 * hs, 0.17 * hs, h(0, 0.03, -0.38)), 0.1 * hs)       # snout
    head = head.su(ellipsoid(0.1 * hs, 0.06 * hs, 0.12 * hs, h(0.12, 0.17, -0.25)).mirror_x(), 0.05 * hs)  # brow
    if P["beak_hook"] > 0:
        head = head.su(round_cone(h(0, 0.05, -0.45), h(0, -0.06 - P["beak_hook"], -0.52), 0.07 * hs, 0.025 * hs), 0.05 * hs)
    head = head & half_space(1, -1, hc[1] - 0.04 * hs)
    H.piece("HeadP", "Head", head, col="secondary", tris=1300, res=112, role="head", pattern=skinpat)
    jw = _v(h(0, -0.04, 0.05))
    H.bone("Jaw", "Head", tuple(jw))
    jaw = ellipsoid(0.2 * hs, 0.12 * hs, 0.32 * hs, h(0, -0.05, -0.2)) & half_space(1, 1, hc[1] - 0.025 * hs)
    H.piece("JawP", "Jaw", jaw, col="secondary", tris=600, role="jaw", pri=1.3)
    H.piece("Beak", "Head", (ellipsoid(0.13 * hs, 0.1 * hs, 0.1 * hs, h(0, 0.0, -0.44)) & half_space(1, -1, hc[1] - 0.035 * hs)),
            col="dark", mat="hard", tris=300, role="beak", pri=1.6)
    H.prim("Mouth", "Jaw", "Ellipsoid", (0.32 * hs, 0.04 * hs, 0.5 * hs), h(0, -0.035, -0.2), col="mouth", mat="hard", role="mouth", pri=2.4)
    H.eyes("Head", h(0.17, 0.12, -0.3), 0.06 * hs, col="iris", pupil="round", look=(0.8, 0.1, -0.6))

    # ------------------------------------------------------------------ limbs
    legs, rig_legs = [], []
    if sea:
        # long front flippers (two bones), short rear paddles
        for front in (True, False):
            tag = "F" if front else "B"
            sh = _v((0.62 * W, yc - 0.08 * s, (-0.55 if front else 0.68) * L))
            wr = sh + _v(((0.75 if front else 0.35) * s, -0.06 * s, (0.15 if front else 0.18) * s))
            tip = wr + _v(((0.85 if front else 0.3) * s, -0.04 * s, (0.55 if front else 0.22) * s))
            H.mbone(f"Fl{tag}#", "Body", tuple(sh))
            H.mbone(f"FlTip{tag}#", f"Fl{tag}#", tuple(wr))
            th = 0.07 * s
            inner = eloft([tuple(sh - _v((0.15 * s, 0, 0))), tuple(wr)], [0.17 * s, 0.26 * s if front else 0.16 * s], [th * 1.4, th])
            outer = eloft([tuple(wr), tuple(wr + (tip - wr) * 0.55 + _v((0, 0, -0.05 * s))), tuple(tip)],
                          [0.26 * s if front else 0.16 * s, 0.22 * s if front else 0.13 * s, 0.06 * s], [th, th * 0.8, th * 0.5], k=0.05 * s)
            H.mpiece(f"Flip{tag}#", f"Fl{tag}#", inner, col="secondary", tris=500, role="limb", pattern=skinpat)
            H.mpiece(f"FlipTip{tag}#", f"FlTip{tag}#", outer, col="secondary", tris=600, role="limb", pattern=skinpat)
            legs.append((f"Fl{tag}R", f"FlTip{tag}R", 1))
            legs.append((f"Fl{tag}L", f"FlTip{tag}L", -1))
    else:
        LG = P["leg"] * s
        for front in (True, False):
            tag = "F" if front else "B"
            z0 = (-0.55 if front else 0.6) * L
            sh = _v((0.6 * W, yc - 0.1 * s, z0))
            el = sh + _v((0.3 * s, -0.12 * s, (-0.05 if front else 0.05) * s))
            ft = _v((el[0] + 0.03 * s, 0.1 * s, el[2] + (-0.08 if front else 0.05) * s))
            H.mbone(f"Up{tag}#", "Body", tuple(sh))
            H.mbone(f"Lo{tag}#", f"Up{tag}#", tuple(el))
            H.mbone(f"Ft{tag}#", f"Lo{tag}#", tuple(ft))
            r0 = (0.2 if not P["column"] else 0.24) * LG
            up = round_cone(tuple(sh - _v((0.15 * s, 0, 0))), tuple(el), r0 * 1.05, r0 * 0.95)
            H.mpiece(f"Upper{tag}#", f"Up{tag}#", up.noise(0.01 * s, 14 / s, 3), col="secondary", tris=450, role="limb", pattern=skinpat)
            lo = round_cone(tuple(el), tuple(ft), r0 * 0.95, r0 * (1.0 if P["column"] else 0.8))
            pad = ellipsoid(r0 * 1.15, r0 * 0.6, r0 * 1.2, tuple(ft + _v((0, -0.04 * s, -0.04 * s)))) & plane((0, -1, 0), 0.0)
            claws = spikes([tuple(ft + _v((dx * s, -0.05 * s, -r0 * 0.9))) for dx in (-0.08, 0.0, 0.08)],
                           [tuple(ft + _v((dx * 1.2 * s, -0.08 * s, -r0 * 1.35))) for dx in (-0.08, 0.0, 0.08)], 0.035 * s, 0.012 * s)
            H.mpiece(f"Lower{tag}#", f"Lo{tag}#", lo.su(pad, 0.06 * s).noise(0.008 * s, 14 / s, 4), col="secondary", tris=550, role="foot", pattern=skinpat)
            H.mpiece(f"Claw{tag}#", f"Ft{tag}#", claws & plane((0, -1, 0), 0.0), col="claw", mat="hard", tris=200, role="claw", pri=2.0, ao=False)
            ph = 0.0 if front else 0.5
            legs.append((f"Up{tag}R", f"Lo{tag}R", f"Ft{tag}R", ph, 1, front))
            legs.append((f"Up{tag}L", f"Lo{tag}L", f"Ft{tag}L", (ph + 0.5) % 1.0, -1, front))
            rig_legs += [{"hip": f"Up{tag}R", "knee": f"Lo{tag}R", "phase": ph, "side": 1}, {"hip": f"Up{tag}L", "knee": f"Lo{tag}L", "phase": (ph + 0.5) % 1.0, "side": -1}]
    # tail
    tb = _v((0, yc - 0.05 * s, L * 0.9))
    H.bone("Tail1", "Body", tuple(tb))
    tl = P["tail"] * s
    tail = round_cone(tuple(tb - _v((0, 0, 0.1 * s))), tuple(tb + _v((0, -0.12 * s, tl))), 0.12 * s, 0.03 * s)
    if P["spiky_tail"]:
        tail = tail.su(spikes([tuple(tb + _v((0, 0.08 * s - 0.03 * s * i, 0.12 * s * (i + 1)))) for i in range(4)],
                              [tuple(tb + _v((0, 0.2 * s - 0.04 * s * i, 0.12 * s * (i + 1) + 0.05 * s))) for i in range(4)], 0.04 * s, 0.01 * s), 0.02 * s)
    H.piece("TailP", "Tail1", tail, col="secondary", tris=300, role="tail", pri=1.6, pattern=skinpat)

    H.socket("mouth", h(0, 0.0, -0.5), "Head")
    H.socket("head", (0, yc + D + 0.1 * s, 0), "Body")
    H.socket("seat", (0, yc + D, 0), "Body")
    H.rig.update({"head": "Head", "jaw": "Jaw", "neck": "Neck", "tail": ["Tail1"]})
    height = yc + D
    if sea:
        MR.flipper(H, [l for l in legs if "FlF" in l[0]], [l for l in legs if "FlB" in l[0]], head="Head", neck=["Neck"], jaw="Jaw",
                   tail=["Tail1"], walk=1.8, height=height, fl_amp=0.6)
    else:
        H.rig["legs"] = rig_legs
        MR.sprawl(H, legs, neck="Neck", head="Head", jaw="Jaw", tail=["Tail1"], stride=0.38, lift=0.5, walk=P["walk"],
                  height=height, attack=P["attack"], bend=0.0, tailwave=0.2)

    # Hit: duck into the shell (neck slides back, legs pull in)
    def hit(t):
        sx = t / 0.6
        k = MR._win(sx, 0.0, 1.0) ** 0.5
        pose = {"Body": (0, -0.04 * height * k, 0.04 * height * k, 0.05 * k, 0, 0.04 * math.sin(t * 40) * k),
                "Neck": (0, -0.02 * s * k, 0.45 * L * k, 0, 0, 0), "Head": (0, 0, 0, 0.2 * k, 0, 0)}
        for l in legs:
            pose[l[0]] = (-0.12 * s * k * (1 if l[-1] in (1, True) else 1), 0.05 * s * k, 0, 0, 0, 0)
        return pose

    H.clip("Hit", 0.6, hit, keys=10, loop=False)
    return H


@hero("turtle", FAM)
def turtle():
    return _turtle("turtle", dome=0.6, plate_h=0.09, tail=0.3, preview={"primary": "#5A7A3A", "secondary": "#8A9A5A", "iris": "#C9A03A"})


@hero("tortoise", FAM)
def tortoise():
    return _turtle("tortoise", dome=0.95, W=0.95, plate_h=0.1, pyramid=1.0, rings=0.5, column=True, leg=1.15, bodyY=0.78, neck=0.6,
                   tail=0.2, walk=1.8, head=0.95, preview={"primary": "#8A6A3A", "secondary": "#A89470", "iris": "#2A2A2A"})


@hero("sea turtle", FAM)
def sea_turtle():
    return _turtle("sea turtle", dome=0.36, W=0.95, L=1.3, plate_h=0.03, flippers=True, bodyY=0.9, neck=0.42, head=1.15, tail=0.2,
                   preview={"primary": "#6A8A4A", "secondary": "#D8C88A", "iris": "#2A2A2A"})


@hero("snapping turtle", FAM)
def snapping_turtle():
    return _turtle("snapping turtle", dome=0.5, plate_h=0.08, keels=0.22, serrate=0.22, shell_rough=0.015, head=1.35, neck=0.65,
                   beak_hook=0.1, tail=0.85, spiky_tail=True, leg=1.1, attack="snap",
                   preview={"primary": "#4A4A30", "secondary": "#6A6A48", "iris": "#C9A03A"})


# ==================================================================================================== snakes
NBASE = dict(s=1.0, n=13, seg=0.62, r=0.3, waves=1.25, amp=0.7, raised=0, head="snake", hs=1.0, hood=0.0, rattle=False,
             paddle=False, fangs=False, pattern=None, pat_depth=0.7, shade=0.8, belly=0.85, brow=False, horns=False, eye_r=0.06,
             pupil="round", walk=1.3, swim=False, coil=False, preview={})

SNAKEHEADS = {
    "snake": dict(z=[0.12, -0.1, -0.32, -0.52, -0.64], w=[0.2, 0.23, 0.21, 0.15, 0.07], t=[0.13, 0.15, 0.14, 0.1, 0.05],
                  jz=[0.14, -0.1, -0.4, -0.6], jw=[0.18, 0.2, 0.16, 0.06], jd=[0.1, 0.09, 0.07, 0.03]),
    "python": dict(z=[0.12, -0.12, -0.38, -0.6, -0.74], w=[0.22, 0.26, 0.22, 0.16, 0.08], t=[0.13, 0.16, 0.14, 0.1, 0.05],
                   jz=[0.14, -0.1, -0.45, -0.7], jw=[0.2, 0.23, 0.17, 0.07], jd=[0.11, 0.1, 0.08, 0.03]),
    "viper": dict(z=[0.15, -0.05, -0.3, -0.5, -0.6], w=[0.3, 0.33, 0.25, 0.15, 0.07], t=[0.13, 0.15, 0.13, 0.09, 0.05],
                  jz=[0.17, -0.05, -0.35, -0.56], jw=[0.27, 0.29, 0.19, 0.06], jd=[0.11, 0.1, 0.07, 0.03]),
    "cobra": dict(z=[0.12, -0.1, -0.32, -0.5, -0.6], w=[0.22, 0.24, 0.21, 0.15, 0.08], t=[0.14, 0.16, 0.14, 0.1, 0.05],
                  jz=[0.14, -0.1, -0.38, -0.57], jw=[0.2, 0.21, 0.17, 0.07], jd=[0.1, 0.09, 0.07, 0.03]),
}


def _snake(hid, **kw):
    P = dict(NBASE)
    P.update(kw)
    s = P["s"]
    n, seg, R = P["n"], P["seg"] * s, P["r"] * s
    raised = P["raised"]
    H = Hero(hid, plan="Serpent", gait="swim" if P["swim"] else "slither", tags=["reptile", "snake"])
    H.preview = P["preview"]

    # ------------------------------------------------------------------ path from the head backwards (S-curve on the ground)
    def radius(i):
        u = i / (n - 1)
        if u < 0.08:
            return R * (0.72 + 0.28 * u / 0.08)
        if u < 0.55:
            return R
        return R * max(0.13, 1 - (u - 0.55) / 0.45 * 0.88)

    pts = []
    ry_fac = 0.86
    if raised:
        # raised fore body: from the head down to the ground in `raised` segments, then the S-curve behind
        top = 2.0 * s * (raised / 4.0)
        pts.append(_v((0, top + 0.15 * s, -0.35 * s)))
        for j in range(1, raised + 1):
            u = j / raised
            y = top * (1 - u) ** 1.25 + R * ry_fac * u ** 0.6
            z = -0.35 * s + 0.15 * s * math.sin(math.pi * u) + 0.55 * s * u ** 2
            pts.append(_v((0.0, y, z)))
        th = 0.0
        x, z = 0.0, float(pts[-1][2])
        for j in range(raised + 1, n):
            u = (j - raised) / (n - raised)
            th = 0.95 * math.sin(math.pi * 2 * u * 1.0 + 0.4)
            x += seg * math.sin(th)
            z += seg * math.cos(th)
            pts.append(_v((x, R * ry_fac * (0.98 if j < n - 1 else 0.9) if radius(j) > 0 else R, z)))
    else:
        x, z = 0.0, -0.3 * s
        for j in range(n):
            u = j / (n - 1)
            th = P["amp"] * math.sin(math.pi * 2 * u * P["waves"] + 0.3)
            if j:
                x += seg * math.sin(th)
                z += seg * math.cos(th)
            pts.append(_v((x, 0, z)))
        for j in range(n):
            pts[j][1] = radius(j) * ry_fac
        pts[0][1] = R * ry_fac * 0.95
    # re-centre: body root a third of the way back, keep the head near z = -?
    b = max(3, raised + 1) if raised else 4
    shift = _v((pts[0][0], 0, 0))  # head on x = 0 (mirrored eyes / fangs / hood are mirrored about x = 0)
    pts = [p - shift for p in pts]

    def shade(Q):  # dorsal darkening + paler belly side
        t = np.clip(Q[:, 1] / (2.0 * R * ry_fac), 0, 1)
        return 1 - (1 - P["shade"]) * t if not raised else 1 - (1 - P["shade"]) * np.clip((Q[:, 1] - 0.0) / (3 * R), 0, 1)

    # arc-length + lateral coordinate of model points along the rest path (for snake patterns)
    segs = [(pts[i], pts[i + 1]) for i in range(n - 1)]
    cum = np.concatenate([[0], np.cumsum([np.linalg.norm(b_ - a_) for a_, b_ in segs])])

    def arc(Q):
        best = np.full(len(Q), 1e9)
        S_ = np.zeros(len(Q))
        lat = np.zeros(len(Q))
        for i, (a_, b_) in enumerate(segs):
            d = b_ - a_
            L2 = d @ d
            t = np.clip(((Q - a_) @ d) / L2, 0, 1)
            c = a_ + t[:, None] * d
            dist = np.linalg.norm(Q - c, axis=1)
            m = dist < best
            best = np.where(m, dist, best)
            S_ = np.where(m, cum[i] + t * math.sqrt(L2), S_)
            side = np.cross(np.array([0, 1.0, 0]), d / math.sqrt(L2))
            lat = np.where(m, (Q - c) @ side, lat)
        return S_, lat, Q[:, 1]

    pt = P["pattern"]
    dep = P["pat_depth"]

    def pat(Q):
        S_, lat, y = arc(Q)
        top = np.clip((y - R * 0.3) / (R * 0.9), 0, 1) if not raised else np.ones(len(Q))
        m = np.ones(len(Q))
        if pt == "diamond":  # rattlesnake: dark diamond outlines with paler centres
            u = np.mod(S_ / (0.7 * s), 1.0) - 0.5
            dd = np.abs(u) * 2 + np.abs(lat) / (R * 0.9)
            ring = np.clip(1 - np.abs(dd - 0.8) / 0.26, 0, 1)
            m = 1 - dep * (0.45 * np.clip(1 - dd, 0, 1) + 0.9 * ring) * top
        elif pt == "zigzag":  # viper: zigzag stripe along the spine
            u = np.mod(S_ / (0.38 * s), 1.0)
            tri = (np.abs(u - 0.5) * 4 - 1) * R * 0.45
            m = 1 - dep * np.clip(1 - np.abs(lat - tri) / (R * 0.22), 0, 1) * top
        elif pt == "blotch":  # python: saddles and blotches
            u = np.mod(S_ / (0.7 * s) + 0.15 * np.sin(lat / R * 3), 1.0)
            sad = np.clip(1 - np.abs(u - 0.5) / 0.3, 0, 1) * np.clip(1.3 - np.abs(lat) / (R * 1.0), 0, 1)
            side = np.clip(1 - np.hypot(np.mod(S_ / (0.7 * s) + 0.5, 1.0) - 0.5, (np.abs(lat) - R * 0.85) / (R * 1.4)) / 0.2, 0, 1)
            m = 1 - dep * np.clip(sad * 2.2 + side * 1.4, 0, 1) * (0.5 + 0.5 * top)
        elif pt == "bands":  # sea snake / krait bands all round
            u = np.mod(S_ / (0.5 * s), 1.0)
            m = 1 - dep * np.clip(1 - np.abs(u - 0.5) / 0.18, 0, 1)
        elif pt == "chevron":  # cobra: faint cross bars
            u = np.mod(S_ / (0.45 * s) + np.abs(lat) / (R * 3), 1.0)
            m = 1 - dep * np.clip(1 - np.abs(u - 0.5) / 0.12, 0, 1) * top
        elif pt == "scales":
            u = np.mod(S_ / (0.09 * s), 1.0)
            m = 1 - 0.12 * np.clip(1 - np.abs(u - 0.5) / 0.15, 0, 1)
        return m * shade(Q)

    # ------------------------------------------------------------------ bones (Body at index b)
    H.body(tuple(pts[b]))
    fore = []
    prev = "Body"
    for j in range(1, b):
        nm = f"Fwd{j}"
        H.bone(nm, prev, tuple(pts[b - j]))
        fore.append(nm)
        prev = nm
    H.bone("Head", prev, tuple(pts[0]))
    chain = []
    prev = "Body"
    for j in range(b + 1, n - 1):
        nm = f"Seg{j - b}"
        H.bone(nm, prev, tuple(pts[j]))
        chain.append(nm)
        prev = nm

    def owner(i):  # bone that carries segment [i, i+1]
        if i < b:
            return "Body" if i + 1 == b else f"Fwd{b - (i + 1)}"
        return "Body" if i == b else f"Seg{i - b}"

    # ------------------------------------------------------------------ body segments
    flat = ry_fac
    for i in range(n - 1):
        a_, b_ = pts[i], pts[i + 1]
        ra, rb = radius(i), radius(i + 1)
        d = b_ - a_
        a2 = a_ - d * 0.12 if i > 0 else a_ + d * 0.18
        b2 = b_ + d * 0.12 if i < n - 2 else b_
        if i == n - 2:
            rb = 0.03 * s
        st = 0.94 if i > 0 else 1.0
        sd = eloft([tuple(a2), tuple(b2)], [ra * st, rb], [ra * flat * st, rb * flat])
        if P["hood"] > 0 and i < b and i >= 1 and i <= 2:
            # cobra hood: wide flat flaps on the raised neck, facing forward
            hw = P["hood"] * s * (1.0 if i == 1 else 0.8)
            c = (a_ + b_) / 2 + (_v((0, -0.12 * s, 0)) if i == 1 else _v((0, 0.1 * s, 0)))
            hood = ellipsoid(hw, seg * 0.85, 0.08 * s, tuple(c + _v((0, 0, 0.03 * s))))
            hood = hood.ss(ellipsoid(hw * 0.8, seg * 0.7, 0.06 * s, tuple(c + _v((0, 0, -0.07 * s)))), 0.03 * s)  # slightly dished front
            sd = sd.su(hood, 0.06 * s)
        if P["paddle"] and i >= n - 4:  # sea snake: tall flat paddle tail
            k = (i - (n - 4)) / 3
            sd = eloft([tuple(a2), tuple(b2)], [ra * (1 - 0.5 * k), rb * 0.5], [ra * (1.0 + 0.9 * k), max(rb, 0.06 * s) * (1.9 + 0.6 * k)])
            sd = sd & half_space(1, -1, -0.0)
        elif not raised or i >= b:
            sd = sd & half_space(1, -1, 0.0)
        H.piece(f"Seg{i + 1}P", owner(i), sd, col="primary", tris=max(420, 1000 - 45 * i), res=112, role="body" if i < n - 3 else "tail",
                pri=1.0 + 0.04 * i, pattern=pat)
    if raised and P["hood"] > 0:  # hood front: pale spectacle / scales on the ventral side
        c = (pts[1] + pts[2]) / 2
        hm = ellipsoid(P["hood"] * s * 0.6, seg * 0.66, 0.05 * s, tuple(c + _v((0, -0.1 * s, -0.04 * s))))
        H.piece("HoodFront", owner(1), hm, col="secondary", tris=400, role="detail", pri=1.4,
                pattern=stripes(lambda Q: Q[:, 1] / s, 7.0, width=0.2, depth=0.3))
    if P["rattle"]:
        tipb = chain[-1] if chain else "Body"
        H.bone("Rattle", tipb, tuple(pts[-1]))
        d = pts[-1] - pts[-2]
        d = d / np.linalg.norm(d)
        rt = None
        for k in range(5):
            c = pts[-1] + d * (0.02 + 0.085 * k) * s
            e = ellipsoid(0.085 * s * (1 - 0.06 * k), 0.06 * s * (1 - 0.06 * k), 0.06 * s, tuple(c))
            rt = e if rt is None else rt.su(e, 0.015 * s)
        H.piece("RattleP", "Rattle", rt, col="horn", mat="hard", tris=500, role="tail", pri=1.5,
                pattern=stripes(lambda Q: (Q - pts[-1]) @ d / s, 1 / 0.085, width=0.25, depth=0.35))

    # ------------------------------------------------------------------ head
    HD = SNAKEHEADS[P["head"]]
    hs = P["hs"] * s
    hc = pts[0] + _v((0, 0.02 * s, 0))

    def h(x, y, z):
        return tuple(hc + _v((x * hs, y * hs, z * hs)))

    my = -0.02
    zs, ws, ts = HD["z"], HD["w"], HD["t"]
    head = eloft([h(0, my, z) for z in zs], [w * hs for w in ws], [t * hs for t in ts], k=0.08 * hs)
    head = head & half_space(1, -1, hc[1] + (my - 0.004) * hs)
    if P["brow"]:  # supraocular shields
        head = head.su(ellipsoid(0.08 * hs, 0.035 * hs, 0.12 * hs, h(ws[1] * 0.62, ts[1] * 0.92 + my, zs[1] - 0.12)).mirror_x(), 0.03 * hs)
    if P["horns"]:
        head = head.su(round_cone(h(ws[1] * 0.55, ts[1] + my, zs[1] - 0.12), h(ws[1] * 0.6, ts[1] + my + 0.16, zs[1] - 0.05), 0.04 * hs, 0.01 * hs).mirror_x(), 0.02 * hs)
    H.piece("HeadP", "Head", head, col="primary", tris=1200, res=112, role="head", pattern=lambda Q: shade(Q) * (pat(Q) * 0 + 1) if raised else shade(Q))
    jw = _v(h(0, my - 0.01, zs[0]))
    H.bone("Jaw", "Head", tuple(jw))
    jz, jws, jd = HD["jz"], HD["jw"], HD["jd"]
    jaw = eloft([h(0, my + 0.01, z) for z in jz], [w * hs for w in jws], [d_ * hs for d_ in jd], k=0.06 * hs)
    jaw = jaw & half_space(1, 1, hc[1] + (my + 0.02) * hs)
    H.piece("JawP", "Jaw", jaw, col="secondary" if P["belly"] < 0.95 else "primary", tris=500, role="jaw", pri=1.3)
    H.prim("Mouth", "Jaw", "Ellipsoid", (jws[1] * 1.6 * hs, 0.04 * hs, abs(jz[-1] - jz[0]) * 0.9 * hs), h(0, my + 0.005, (jz[0] + jz[-1]) / 2),
           col="mouth", mat="hard", role="mouth", pri=2.4)
    if P["fangs"]:
        fz = zs[-2] + 0.02
        fx = float(_interp(fz, zs, ws)) * 0.55
        H.mpiece("Fang#", "Head", round_cone(h(fx, my + 0.02, fz), h(fx, my - 0.13, fz - 0.03), 0.022 * hs, 0.006 * hs),
                 col="tooth", mat="hard", tris=150, role="tooth", pri=2.2, ao=False, smooth=2)
    ez = zs[1] - 0.14
    ew = float(_interp(ez, zs, ws))
    et = float(_interp(ez, zs, ts))
    H.eyes("Head", h(ew * 0.8, my + et * 0.62, ez), P["eye_r"] * hs, col="iris", pupil=P["pupil"], look=(0.8, 0.25, -0.5))
    # forked tongue
    H.bone("Tongue", "Jaw", h(0, my - 0.01, zs[1]))
    L = abs(zs[-1] - zs[1]) * 0.8
    tg = round_cone(h(0, my - 0.01, zs[1] + 0.05), h(0, my - 0.01, zs[1] - L), 0.025 * hs, 0.018 * hs)
    tg = tg.su(round_cone(h(0, my - 0.01, zs[1] - L), h(0.05, my - 0.03, zs[1] - L - 0.16), 0.016 * hs, 0.006 * hs).mirror_x(), 0.01 * hs)
    H.piece("TongueP", "Tongue", tg, col="tongue", tris=220, role="tongue", pri=2.0, ao=False)

    H.socket("mouth", h(0, my, zs[-1] - 0.05), "Head")
    H.socket("head", h(0, max(ts) + 0.1, zs[1]), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": chain, "spine": fore[::-1] + ["Body"] + chain})
    MR.slither(H, chain, fore=fore, head="Head", jaw="Jaw", tongue=("Tongue", (L + 0.22) * hs, (0, 0, 1)), amp=0.3, waves=1.2,
               walk=P["walk"], height=max(R * 3, float(pts[0][1]) + 0.2 * s), raised=bool(raised), rattle="Rattle" if P["rattle"] else None,
               swim=P["swim"])
    return H


@hero("snake", FAM)
def snake():
    return _snake("snake", pattern="scales", shade=0.75, preview={"primary": "#4A7A3A", "secondary": "#C8B860", "iris": "#E8C030", "tongue": "#C8304A"})


@hero("python", FAM)
def python_():
    return _snake("python", r=0.36, seg=0.66, head="python", hs=1.2, pattern="blotch", pat_depth=0.9, shade=0.85, walk=1.6,
                  preview={"primary": "#8A7A4A", "secondary": "#D8C08A", "iris": "#C9A03A", "tongue": "#2A2A2A"})


@hero("cobra", FAM)
def cobra():
    return _snake("cobra", raised=4, hood=0.72, head="cobra", hs=1.15, fangs=True, pattern="chevron", pat_depth=0.25, shade=0.8, brow=True,
                  preview={"primary": "#3A3020", "secondary": "#E8C87A", "iris": "#C9A03A", "tongue": "#1A1A1A"})


@hero("king cobra", FAM)
def king_cobra():
    return _snake("king cobra", raised=4, hood=0.6, r=0.3, seg=0.7, n=14, head="cobra", hs=1.2, fangs=True, pattern="chevron",
                  pat_depth=0.45, shade=0.85, brow=True,
                  preview={"primary": "#4A4A2A", "secondary": "#D8C87A", "iris": "#C9A03A", "tongue": "#1A1A1A"})


@hero("rattlesnake", FAM)
def rattlesnake():
    return _snake("rattlesnake", r=0.3, head="viper", hs=1.15, fangs=True, rattle=True, pattern="diamond", pat_depth=0.9, shade=0.9,
                  brow=True, pupil="slit", preview={"primary": "#B8986A", "secondary": "#E0D0A8", "iris": "#C9A03A", "tongue": "#2A2A2A", "horn": "#D8C090"})


@hero("viper", FAM)
def viper():
    return _snake("viper", r=0.3, n=12, head="viper", hs=1.2, fangs=True, pattern="zigzag", pat_depth=0.7, shade=0.9, brow=True, horns=True,
                  pupil="slit", preview={"primary": "#8A6A3A", "secondary": "#C8A87A", "iris": "#E8A030", "tongue": "#2A2A2A"})


@hero("sea snake", FAM)
def sea_snake():
    return _snake("sea snake", r=0.24, head="snake", paddle=True, pattern="bands", pat_depth=0.75, shade=0.9, swim=True, walk=1.1,
                  preview={"primary": "#5A7AA8", "secondary": "#F2F2F0", "iris": "#2A2A2A", "tongue": "#2A2A2A"})


# ==================================================================================================== frogs and toads
FBASE = dict(s=1.0, W=1.0, leg=1.0, eye=0.16, warts=0.0, glands=False, pads=False, pattern=None, pat_depth=0.5, shade=0.8,
             eyecol="iris", pupil="round", padcol="primary", jump=1.0, preview={})


def _frog(hid, **kw):
    P = dict(FBASE)
    P.update(kw)
    s, W, LG = P["s"], P["W"], P["leg"]
    H = Hero(hid, plan="Quadruped", gait="hop", tags=["amphibian", "frog"])
    H.preview = P["preview"]
    by = 0.72 * s
    H.body((0, by, 0.1 * s))

    def shade(Q):
        return 1 - (1 - P["shade"]) * np.clip((Q[:, 1] - 0.45 * s) / (0.6 * s), 0, 1)

    pat = None
    if P["pattern"] == "spots":
        pat = spots(0.3 * s, 0.1 * s, depth=P["pat_depth"], seed=2)
    elif P["pattern"] == "blotch":
        pat = spots(0.4 * s, 0.14 * s, depth=P["pat_depth"], seed=5)

    def skin(extra=None):
        return combine(shade, pat, extra)

    def warty(sd, seed):
        if P["warts"] <= 0:
            return sd
        w = P["warts"] * s
        rng = np.random.default_rng(seed)
        ph = rng.uniform(0, 6.28, 3)
        f = 6.28 / (w * 4.2)

        def g(p):
            d = sd(p)
            c = np.sin(p[:, 0] * f + ph[0]) * np.sin(p[:, 1] * f * 1.1 + ph[1]) * np.sin(p[:, 2] * f * 0.9 + ph[2])
            return d - w * np.clip(c, 0, 1) ** 2

        return SDF(g)

    # ------------------------------------------------------------------ body (pear-shaped, tilted nose-up)
    body = ellipsoid(0.62 * W * s, 0.46 * s, 0.78 * s, (0, by, 0.12 * s)).rot(-14, 0, 0).at(0, 0, 0)
    body = ellipsoid(0.62 * W * s, 0.46 * s, 0.78 * s, (0, 0, 0)).rot(-14, 0, 0).at(0, by, 0.12 * s)
    body = body.su(ellipsoid(0.5 * W * s, 0.32 * s, 0.45 * s, (0, by - 0.15 * s, 0.55 * s)), 0.2 * s)        # rump
    body = body.su(ellipsoid(0.38 * W * s, 0.22 * s, 0.4 * s, (0.3 * W * s, by - 0.2 * s, 0.45 * s)).mirror_x(), 0.15 * s)  # haunches
    body = body & plane((0, -1, 0), -0.12 * s)
    H.piece("Torso", "Body", warty(body, 1), col="primary", tris=1800, res=120, pattern=skin())
    belly = ellipsoid(0.5 * W * s, 0.3 * s, 0.7 * s, (0, by - 0.2 * s, 0.05 * s)) & half_space(1, 1, by - 0.22 * s)
    H.piece("Belly", "Body", belly, col="secondary" if not P["pads"] else "cream", tris=500, role="body", pri=1.4)

    # ------------------------------------------------------------------ head + jaw (wide mouth)
    hc = _v((0, by + 0.18 * s, -0.42 * s))
    H.bone("Head", "Body", tuple(hc))

    def h(x, y, z):
        return tuple(hc + _v((x * s, y * s, z * s)))

    my = -0.08
    head = ellipsoid(0.56 * W * s, 0.3 * s, 0.5 * s, h(0, 0.02, -0.12))
    head = head.su(ellipsoid(0.36 * W * s, 0.2 * s, 0.25 * s, h(0, 0.0, -0.42)), 0.12 * s)                 # snout
    er = P["eye"] * s
    ex, ey, ez = 0.33 * W, 0.24, -0.16
    head = head.su(sphere(er * 1.12, h(ex, ey - 0.04, ez)).mirror_x(), 0.1 * s)                             # eye bulges
    if P["glands"]:
        head = head.su(ellipsoid(0.13 * s, 0.09 * s, 0.24 * s, h(0.35 * W, 0.16, 0.18)).mirror_x(), 0.06 * s)
    head = head & half_space(1, -1, hc[1] + my * s)
    H.piece("HeadP", "Head", warty(head, 2), col="primary", tris=1500, res=120, role="head", pattern=skin())
    jw = _v(h(0, my - 0.02, 0.15))
    H.bone("Jaw", "Head", tuple(jw))
    jaw = ellipsoid(0.53 * W * s, 0.17 * s, 0.5 * s, h(0, my - 0.02, -0.15))
    jaw = jaw.su(ellipsoid(0.32 * W * s, 0.11 * s, 0.24 * s, h(0, my - 0.02, -0.42)), 0.1 * s)
    jaw = jaw.su(ellipsoid(0.4 * W * s, 0.2 * s, 0.35 * s, h(0, my - 0.12, 0.0)), 0.1 * s)                  # throat
    jaw = jaw & half_space(1, 1, hc[1] + (my + 0.015) * s)
    H.piece("JawP", "Jaw", jaw, col="secondary" if not P["pads"] else "cream", tris=800, role="jaw", pri=1.3)
    H.prim("Mouth", "Jaw", "Ellipsoid", (0.95 * W * s, 0.05 * s, 0.82 * s), h(0, my - 0.005, -0.18), col="mouth", mat="hard", role="mouth", pri=2.4)
    H.eyes("Head", h(ex + 0.03, ey + 0.02, ez - 0.03), er, col=P["eyecol"], pupil=P["pupil"], look=(0.7, 0.35, -0.6))
    # telescoping sticky tongue: a fixed root + three segments that slide out by 1/3, 2/3, 3/3 of the reach
    tongue = []
    reach = 1.6 * s
    for k in range(4):
        nm = "Tongue" if k == 0 else f"Tongue{k}"
        H.bone(nm, "Jaw", h(0, my - 0.03, -0.1))
        z0, z1 = 0.08, -0.5
        r0_ = 0.05 * s
        sd = round_cone(h(0, my - 0.03, z0), h(0, my - 0.03, z1), r0_, r0_ * 0.95)
        if k == 3:
            sd = sd.su(sphere(0.1 * s, h(0, my - 0.03, z1)), 0.03 * s)
        H.piece(f"TongueP{k}", nm, sd, col="tongue", tris=200 if k < 3 else 300, role="tongue", pri=2.0 + 0.05 * k, ao=False)
        if k:
            tongue.append((nm, reach * k / 3, (0, 0, 1)))
    # ------------------------------------------------------------------ hind legs (folded Z)
    hind, fore = [], []
    for side in (1,):
        hp = _v((0.42 * W * s, by - 0.1 * s, 0.55 * s))
        kn = _v((0.88 * W * s, 0.32 * s * LG, 0.05 * s))
        an = _v((0.62 * W * s, 0.16 * s, 0.72 * s))
        H.mbone("Thigh#", "Body", tuple(hp))
        H.mbone("Shin#", "Thigh#", tuple(kn))
        H.mbone("Foot#", "Shin#", tuple(an))
        th = round_cone(tuple(hp), tuple(kn), 0.26 * s * LG, 0.15 * s)
        th = th.su(ellipsoid(0.22 * s, 0.2 * s, 0.38 * s, tuple(hp * 0.5 + kn * 0.5 + _v((0, 0.04 * s, 0.02 * s)))), 0.1 * s)
        H.mpiece("ThighP#", "Thigh#", warty(th, 3), col="primary", tris=650, role="limb", pattern=skin())
        sh = round_cone(tuple(kn), tuple(an), 0.15 * s, 0.09 * s)
        H.mpiece("ShinP#", "Shin#", warty(sh, 4), col="primary", tris=450, role="limb", pattern=skin())
        # long foot along the ground pointing forward, webbed toes
        heel = an
        ball = _v((0.78 * W * s, 0.06 * s, -0.05 * s))
        ft = round_cone(tuple(heel), tuple(ball), 0.08 * s, 0.07 * s)
        web = None
        for i, a in enumerate((-30, -10, 10, 30, 50)):
            ar = math.radians(a)
            tip = ball + _v((math.sin(ar) * 0.4 * s, -0.03 * s, -math.cos(ar) * 0.42 * s * (0.75 + 0.1 * i if i < 4 else 0.7)))
            t_ = round_cone(tuple(ball), tuple(tip), 0.04 * s, 0.03 * s)
            if P["pads"]:
                t_ = t_.su(sphere(0.06 * s, tuple(tip)), 0.02 * s)
            ft = ft.su(t_, 0.03 * s)
            if i < 4:
                ar2 = math.radians(a + 20)
                tip2 = ball + _v((math.sin(ar2) * 0.32 * s, -0.04 * s, -math.cos(ar2) * 0.32 * s))
                tri = eloft([tuple(ball), tuple((tip + tip2) / 2)], [0.12 * s, 0.07 * s], [0.015 * s, 0.012 * s])
                ft = ft | tri
        ft = ft & plane((0, -1, 0), 0.0)
        H.mpiece("FootP#", "Foot#", ft, col=P["padcol"] if P["pads"] else "primary", tris=750, res=112, role="foot", pattern=skin())
        hind = [("ThighR", "ShinR", "FootR", 1), ("ThighL", "ShinL", "FootL", -1)]
        # front arms
        shp = _v((0.38 * W * s, by - 0.12 * s, -0.32 * s))
        el = _v((0.5 * W * s, 0.3 * s, -0.38 * s))
        hd = _v((0.52 * W * s, 0.07 * s, -0.48 * s))
        H.mbone("Arm#", "Body", tuple(shp))
        H.mbone("Fore#", "Arm#", tuple(el))
        H.mbone("Hand#", "Fore#", tuple(hd))
        H.mpiece("ArmP#", "Arm#", round_cone(tuple(shp), tuple(el), 0.13 * s, 0.09 * s), col="primary", tris=350, role="limb", pattern=skin())
        H.mpiece("ForeP#", "Fore#", round_cone(tuple(el), tuple(hd), 0.09 * s, 0.07 * s), col="primary", tris=300, role="limb", pattern=skin())
        hand = ellipsoid(0.08 * s, 0.04 * s, 0.08 * s, tuple(hd + _v((0, -0.03 * s, -0.03 * s))))
        for a in (-50, -15, 20, 55):
            ar = math.radians(a)
            tip = hd + _v((math.sin(ar) * 0.2 * s, -0.05 * s, -math.cos(ar) * 0.2 * s))
            f_ = round_cone(tuple(hd + _v((0, -0.03 * s, 0))), tuple(tip), 0.035 * s, 0.03 * s)
            if P["pads"]:
                f_ = f_.su(sphere(0.055 * s, tuple(tip)), 0.02 * s)
            hand = hand.su(f_, 0.02 * s)
        H.mpiece("HandP#", "Hand#", hand & plane((0, -1, 0), 0.0), col=P["padcol"] if P["pads"] else "primary", tris=450, role="foot", pattern=skin())
        fore = [("ArmR", "ForeR", "HandR", 1), ("ArmL", "ForeL", "HandL", -1)]

    H.socket("mouth", h(0, my, -0.5), "Head")
    H.socket("head", h(0, 0.4, -0.1), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw"})
    MR.hop(H, hind, fore, head="Head", jaw="Jaw", tongue=tongue, walk=0.9, height=1.2 * s, jump=P["jump"])
    return H


@hero("frog", FAM)
def frog():
    return _frog("frog", pattern="spots", pat_depth=0.35, preview={"primary": "#4AA03A", "secondary": "#E8E07A", "iris": "#C9A03A", "tongue": "#E8607A"})


@hero("toad", FAM)
def toad():
    return _frog("toad", W=1.12, leg=0.85, eye=0.14, warts=0.035, glands=True, pattern="blotch", pat_depth=0.35, shade=0.75, jump=0.6,
                 preview={"primary": "#8A7A4A", "secondary": "#C8B07A", "iris": "#C98A2A", "tongue": "#E8607A"})


@hero("tree frog", FAM)
def tree_frog():
    return _frog("tree frog", W=0.88, leg=1.12, eye=0.2, pads=True, padcol="secondary", shade=0.92, eyecol=[0.86, 0.12, 0.1], pupil="slit",
                 jump=1.25, preview={"primary": "#4AD84A", "secondary": "#E8702A", "tongue": "#E8607A"})


# word -> hero rules (tools/meshgen/heroes/map.py)
CRE = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Plant", "Weather"]}
MAP = [
    ("crocodile", "crocodile, crocodiles, croc, crocs, saltie, sarcosuchus, deinosuchus, postosuchus, crocodilian, !crocodile monitor", LIZ),
    ("alligator", "alligator, alligators, gator, gators, caiman, caimans, !alligator lizard, !alligator snapping turtle, !caiman lizard", LIZ),
    ("gharial", "gharial, gharials, gavial, tomistoma", LIZ),
    ("komodo dragon", "komodo dragon, komodo, komodos, komodo dragons, megalania", LIZ),
    ("monitor lizard", "monitor lizard, monitor, monitors, goanna, nile monitor, lace monitor, crocodile monitor, tegu, gila monster, gila", {"cat": ["Creature"]}),
    ("lizard", "lizard, lizards, skink, skinks, anole, tuatara, uromastyx, chuckwalla, basilisk lizard, water dragon, chinese water dragon, "
               "flying dragon lizard, reptile, reptiles, slowworm, glass lizard", LIZ),
    ("iguana", "iguana, iguanas, marine iguana, blue iguana", LIZ),
    ("gecko", "gecko, geckos, geckoes", LIZ),
    ("chameleon", "chameleon, chameleons, chamaeleon", LIZ),
    ("frilled lizard", "frilled lizard, frill necked lizard, frillneck", LIZ),
    ("horned lizard", "horned lizard, horned toad, horny toad, thorny devil, armadillo lizard, moloch", LIZ),
    ("bearded dragon", "bearded dragon, beardie, beardies", LIZ),
    ("salamander", "salamander, salamanders, hellbender, mudpuppy, olm, amphiuma, siren salamander, amphibian, caecilian", LIZ),
    ("newt", "newt, newts, eft, crested newt", LIZ),
    ("axolotl", "axolotl, axolotls, mexican walking fish", LIZ),
    ("dimetrodon", "dimetrodon, dimetrodons, edaphosaurus", LIZ),
    ("turtle", "turtle, turtles, terrapin, terrapins, box turtle, mud turtle, musk turtle, map turtle, painted turtle, mata mata, henodus", CRE),
    ("tortoise", "tortoise, tortoises, megalochelys", CRE),
    ("sea turtle", "sea turtle, sea turtles, leatherback turtle, leatherback, loggerhead, loggerhead turtle, olive ridley, hawksbill, "
                   "green sea turtle, archelon", CRE),
    ("snapping turtle", "snapping turtle, snapper turtle, alligator snapping turtle", CRE),
    ("snake", "snake, snakes, serpent, serpents, boomslang, krait, taipan, mamba, black mamba, green mamba, slither, snek", LIZ),
    ("python", "python, pythons, boa, boas, boa constrictor, anaconda, anacondas, titanoboa", {"cat": ["Creature"], "bp": ["Serpent", "Quadruped", "Blob"]}),
    ("cobra", "cobra, cobras, spitting cobra, naja", LIZ),
    ("king cobra", "king cobra, king cobras", LIZ),
    ("rattlesnake", "rattlesnake, rattlesnakes, rattler, rattlers, rattle snake, sidewinder, diamondback", LIZ),
    ("viper", "viper, vipers, adder, adders, puff adder, bushmaster, copperhead, cottonmouth, fer de lance, asp", LIZ),
    ("sea snake", "sea snake, sea snakes, sea krait", LIZ),
    ("frog", "frog, frogs, froggy, bullfrog, bullfrogs, coqui, spring peeper, mantella, ribbit", CRE),
    ("toad", "toad, toads, cane toad, natterjack", CRE),
    ("tree frog", "tree frog, tree frogs, treefrog, red eyed tree frog, glass frog, reed frog, flying frog, waxy monkey frog", CRE),
]
