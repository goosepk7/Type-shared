"""Dinosaurs and prehistoric reptiles.

Builders:
  _theropod   tyrannosaurus rex / velociraptor (feathered) / allosaurus / carnotaurus / spinosaurus / dilophosaurus /
              pachycephalosaurus: horizontal trunk balanced over pillar hips, drumstick thighs, digitigrade three-bone legs
              with three clawed toes, a lofted skull with a deep opening jaw and tooth rows, tiny (or long, feathered) arms,
              a five-bone counterweight tail. Extras: sail, brow horns, twin crests, bone dome, sickle claw, feather plumes.
  _quaddino   triceratops / styracosaurus / stegosaurus / ankylosaurus / parasaurolophus / iguanodon / brachiosaurus /
              diplodocus: barrel trunk on four columnar legs with hoof-toed feet, neck, head (frill + horns, beak, crest,
              plates, spikes, armour, tail club), mount dicts for the big ones.
  _pterosaur  pteranodon / pterodactyl: membrane wings on a two-bone arm, crest, toothless or toothed beak (flies).
  _marine     plesiosaurus (four flippers, long neck) / mosasaurus (long body, fluked tail) (swim).
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from kit import Hero, hero, stripes, spots, gradient, combine
import motion
import motion_reptiles as MR
import mountkit as MK
from motion_reptiles import eloft, squash, grid_bumps, spikes

FAM = "dinosaurs"
DINO = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Plant", "Weather", "Structure", "Vehicle"]}


def _v(a):
    return np.asarray(a, float)


def _interp(z, zs, vs):
    zs = np.asarray(zs, float)
    vs = np.asarray(vs, float)
    o = np.argsort(zs)
    return np.interp(z, zs[o], vs[o])


SKULLS = {
    "rex": dict(z=[0.35, 0.0, -0.4, -0.8, -1.2, -1.5], w=[0.56, 0.64, 0.55, 0.44, 0.36, 0.25], t=[0.66, 0.74, 0.62, 0.48, 0.37, 0.22],
                jz=[0.42, 0.0, -0.6, -1.1, -1.45], jw=[0.54, 0.56, 0.44, 0.33, 0.22], jd=[0.5, 0.52, 0.4, 0.3, 0.19]),
    "allo": dict(z=[0.3, 0.0, -0.4, -0.8, -1.2, -1.45], w=[0.38, 0.42, 0.36, 0.29, 0.23, 0.15], t=[0.46, 0.5, 0.43, 0.35, 0.27, 0.14],
                 jz=[0.35, 0.0, -0.6, -1.05, -1.4], jw=[0.36, 0.38, 0.3, 0.22, 0.13], jd=[0.32, 0.33, 0.26, 0.19, 0.11]),
    "raptor": dict(z=[0.25, 0.0, -0.35, -0.75, -1.1, -1.32], w=[0.27, 0.29, 0.24, 0.18, 0.13, 0.07], t=[0.31, 0.34, 0.27, 0.2, 0.15, 0.07],
                   jz=[0.28, 0.0, -0.5, -0.95, -1.27], jw=[0.25, 0.26, 0.2, 0.13, 0.06], jd=[0.2, 0.21, 0.15, 0.1, 0.05]),
    "carno": dict(z=[0.3, 0.0, -0.35, -0.7, -0.95, -1.1], w=[0.42, 0.46, 0.42, 0.34, 0.26, 0.15], t=[0.55, 0.6, 0.5, 0.4, 0.3, 0.15],
                  jz=[0.35, 0.0, -0.45, -0.85, -1.05], jw=[0.4, 0.42, 0.34, 0.24, 0.13], jd=[0.36, 0.36, 0.26, 0.18, 0.1]),
    "spino": dict(z=[0.3, 0.0, -0.4, -0.85, -1.35, -1.8, -2.0], w=[0.32, 0.34, 0.26, 0.17, 0.14, 0.18, 0.1], t=[0.4, 0.42, 0.32, 0.2, 0.15, 0.15, 0.08],
                  jz=[0.33, 0.0, -0.6, -1.3, -1.95], jw=[0.3, 0.32, 0.17, 0.13, 0.1], jd=[0.28, 0.27, 0.15, 0.11, 0.07]),
    "cera": dict(z=[0.3, 0.0, -0.35, -0.7, -1.0, -1.22], w=[0.45, 0.5, 0.44, 0.33, 0.22, 0.1], t=[0.55, 0.62, 0.52, 0.42, 0.3, 0.12],
                 jz=[0.3, 0.0, -0.5, -0.95, -1.18], jw=[0.4, 0.42, 0.32, 0.18, 0.07], jd=[0.3, 0.32, 0.25, 0.16, 0.06]),
    "stego": dict(z=[0.2, 0.0, -0.3, -0.6, -0.8], w=[0.22, 0.25, 0.21, 0.15, 0.07], t=[0.22, 0.25, 0.2, 0.14, 0.06],
                  jz=[0.22, 0.0, -0.4, -0.76], jw=[0.2, 0.22, 0.16, 0.06], jd=[0.16, 0.15, 0.1, 0.04]),
    "ankylo": dict(z=[0.25, 0.0, -0.3, -0.55, -0.72], w=[0.5, 0.52, 0.47, 0.36, 0.2], t=[0.3, 0.33, 0.28, 0.2, 0.1],
                   jz=[0.25, 0.0, -0.35, -0.68], jw=[0.42, 0.44, 0.36, 0.16], jd=[0.2, 0.2, 0.15, 0.06]),
    "hadro": dict(z=[0.25, 0.0, -0.35, -0.7, -1.0, -1.18], w=[0.3, 0.32, 0.26, 0.2, 0.24, 0.17], t=[0.42, 0.44, 0.33, 0.22, 0.15, 0.08],
                  jz=[0.28, 0.0, -0.45, -0.9, -1.12], jw=[0.27, 0.29, 0.22, 0.2, 0.15], jd=[0.26, 0.26, 0.18, 0.1, 0.05]),
    "sauro": dict(z=[0.2, 0.0, -0.25, -0.5, -0.64], w=[0.22, 0.25, 0.21, 0.16, 0.12], t=[0.3, 0.32, 0.22, 0.15, 0.1],
                  jz=[0.22, 0.0, -0.3, -0.6], jw=[0.2, 0.22, 0.17, 0.11], jd=[0.16, 0.15, 0.1, 0.05]),
    "ptero": dict(z=[0.2, 0.0, -0.3, -0.7, -1.2, -1.7], w=[0.2, 0.2, 0.14, 0.09, 0.05, 0.015], t=[0.26, 0.27, 0.18, 0.1, 0.06, 0.02],
                  jz=[0.2, 0.0, -0.6, -1.2, -1.68], jw=[0.17, 0.17, 0.09, 0.05, 0.012], jd=[0.12, 0.11, 0.07, 0.04, 0.012]),
    "plesio": dict(z=[0.2, 0.0, -0.25, -0.5, -0.7], w=[0.2, 0.22, 0.18, 0.12, 0.06], t=[0.2, 0.21, 0.16, 0.1, 0.05],
                   jz=[0.22, 0.0, -0.35, -0.67], jw=[0.18, 0.2, 0.14, 0.05], jd=[0.12, 0.11, 0.08, 0.03]),
    "mosa": dict(z=[0.3, 0.0, -0.4, -0.85, -1.3, -1.55], w=[0.38, 0.4, 0.33, 0.25, 0.17, 0.09], t=[0.36, 0.4, 0.32, 0.24, 0.17, 0.09],
                 jz=[0.33, 0.0, -0.6, -1.15, -1.5], jw=[0.35, 0.37, 0.28, 0.18, 0.08], jd=[0.26, 0.26, 0.2, 0.13, 0.06]),
    "pachy": dict(z=[0.25, 0.0, -0.3, -0.55, -0.72], w=[0.36, 0.4, 0.33, 0.22, 0.1], t=[0.5, 0.55, 0.42, 0.28, 0.13],
                  jz=[0.28, 0.0, -0.35, -0.68], jw=[0.33, 0.35, 0.26, 0.09], jd=[0.26, 0.24, 0.16, 0.06]),
}


def _skull(H, hc, hs, sk, bone="Head", col="primary", tris=1800, pattern=None, teeth=0, brow=0.0, eye_r=0.08, pupil="slit",
           fenestra=True, extra=None, beak=False, jaw_tris=900):
    """Station-lofted skull with a deep lower jaw on bone Jaw. Returns helpers (h, stations)."""
    HD = SKULLS[sk]
    zs, ws, ts = HD["z"], HD["w"], HD["t"]

    def h(x, y, z):
        return tuple(hc + _v((x * hs, y * hs, z * hs)))

    my = -0.06
    head = eloft([h(0, my, z) for z in zs], [w * hs for w in ws], [t * hs for t in ts], k=0.14 * hs)
    head = head & half_space(1, -1, hc[1] + (my - 0.005) * hs)
    ez = zs[1] - 0.12
    ew = float(_interp(ez, zs, ws))
    et = float(_interp(ez, zs, ts))
    if brow > 0:  # brow ridge over the eye
        head = head.su(ellipsoid(0.12 * hs, 0.07 * hs, 0.2 * hs, h(ew * 0.72, my + et * 0.95, ez - 0.05)).mirror_x(), brow * hs)
    if fenestra:  # antorbital hollow
        fz = (zs[2] + zs[3]) / 2
        fw = float(_interp(fz, zs, ws))
        ft = float(_interp(fz, zs, ts))
        head = head.ss(ellipsoid(0.08 * hs, ft * 0.28 * hs, abs(zs[3] - zs[2]) * 0.55 * hs, h(fw * 1.02, my + ft * 0.5, fz)).mirror_x(), 0.05 * hs)
    if extra is not None:
        head = extra(head, h)
    H.piece("HeadP", bone, head, col=col, tris=tris, res=136, role="head", pattern=pattern)
    jz, jws, jd = HD["jz"], HD["jw"], HD["jd"]
    H.bone("Jaw", bone, h(0, my - 0.03, zs[0] - 0.05))
    jaw = eloft([h(0, my + 0.01, z) for z in jz], [w * hs for w in jws], [d * hs for d in jd], k=0.1 * hs)
    jaw = jaw & half_space(1, 1, hc[1] + (my + 0.025) * hs)
    H.piece("JawP", "Jaw", jaw, col=col, tris=jaw_tris, role="jaw", pri=1.3, pattern=pattern)
    H.prim("Mouth", "Jaw", "Ellipsoid", (jws[1] * 1.55 * hs, 0.05 * hs, abs(jz[-1] - jz[0]) * 0.88 * hs), h(0, my + 0.005, (jz[0] + jz[-1]) / 2),
           col="mouth", mat="hard", role="mouth", pri=2.4)
    if teeth:
        tzz = np.linspace(zs[1] - 0.25, zs[-1] + 0.1, teeth)
        tb = [h(float(_interp(z, zs, ws)) * 0.88, my + 0.01, z) for z in tzz]
        tl = 0.14 if sk in ("rex", "carno") else 0.1
        tt = [(b[0] - 0.005 * hs, b[1] - (tl * (0.7 + 0.3 * math.sin(i * 2.1) ** 2)) * hs, b[2] + 0.01 * hs) for i, b in enumerate(tb)]
        H.piece("TeethU", bone, spikes(tb, tt, 0.04 * hs, 0.008 * hs).mirror_x(), col="tooth", mat="hard", tris=800, role="tooth", pri=1.8, ao=False, smooth=2)
        lzz = np.linspace(jz[1] - 0.3, jz[-1] + 0.1, max(3, teeth - 2))
        lb = [h(float(_interp(z, jz, jws)) * 0.8, my + 0.02, z) for z in lzz]
        lt = [(b[0], b[1] + tl * 0.85 * hs, b[2]) for b in lb]
        H.piece("TeethL", "Jaw", spikes(lb, lt, 0.035 * hs, 0.008 * hs).mirror_x(), col="tooth", mat="hard", tris=600, role="tooth", pri=1.9, ao=False, smooth=2)
    if beak:
        bk = eloft([h(0, my, zs[-2]), h(0, my - 0.02, zs[-1] - 0.06)], [ws[-2] * 0.9 * hs, 0.05 * hs], [ts[-2] * 0.7 * hs, 0.06 * hs])
        H.piece("Beak", bone, bk & half_space(1, -1, hc[1] + (my - 0.003) * hs), col="beak", mat="hard", tris=400, role="beak", pri=1.5)
    H.eyes(bone, h(ew * 0.86, my + et * 0.66, ez), eye_r * hs, col="iris", pupil=pupil, look=(0.75, 0.15, -0.6))
    return h, HD, my


# ==================================================================================================== theropods
TBASE = dict(s=1.0, leg=1.0, legr=1.0, body=1.0, girth=1.0, neck=1.0, hs=1.0, skull="rex", arms=0.45, fingers=2, tail=1.0, tailr=1.0,
             teeth=12, brow=0.06, horns=0.0, crests=0.0, dome=False, sail=0.0, feathers=False, sickle=False, bumps=False,
             pattern=None, pat_depth=0.5, shade=0.75, beak=False, eye_r=0.075, attack="bite", stride=0.42, walk=1.25, heavy=1.0,
             paddle=False, mount=True, preview={})


def _theropod(hid, **kw):
    P = dict(TBASE)
    P.update(kw)
    s = P["s"]
    LG, G, BL = P["leg"] * s, P["girth"] * s, P["body"] * s
    H = Hero(hid, plan="Biped", gait="stomp" if P["heavy"] >= 0.8 else "biped", tags=["dinosaur", "reptile"])
    H.preview = P["preview"]

    # leg chain (digitigrade): hip -> knee (forward) -> ankle (back) -> ball of foot
    thigh = _v((0.12, -1.28, -0.55)) * LG
    shin = _v((0.0, -1.15, 0.72)) * LG
    meta = _v((0.0, -0.62, -0.32)) * LG
    hipY = -(thigh[1] + shin[1] + meta[1]) + 0.13 * s
    hipZ = 0.25 * s
    H.body((0, hipY, hipZ))

    def shade(Q):
        return 1 - (1 - P["shade"]) * np.clip((Q[:, 1] - (hipY - 1.0 * G)) / (1.9 * G), 0, 1)

    pat = None
    if P["pattern"] == "stripes":
        pat = stripes(lambda Q: Q[:, 2] / s + 0.25 * np.abs(Q[:, 1] / s - hipY), 1.1, width=0.3, depth=P["pat_depth"], wobble=0.1, seed=3)
    elif P["pattern"] == "spots":
        pat = spots(0.4 * s, 0.13 * s, depth=P["pat_depth"], seed=4)
    elif P["pattern"] == "bands":
        pat = stripes(lambda Q: Q[:, 2] / s, 0.75, width=0.35, depth=P["pat_depth"], seed=2)

    def skin(extra=None):
        return combine(shade, pat, extra)

    tex = (lambda sd, a=1.0, seed=0: sd.noise(0.012 * a * s, 7.0 / s, seed)) if not P["feathers"] else (lambda sd, a=1.0, seed=0: sd.noise(0.02 * a * s, 10.0 / s, seed))

    # ------------------------------------------------------------------ trunk
    tp = [(0, hipY - 0.12 * G, -2.1 * BL + hipZ), (0, hipY - 0.2 * G, -1.35 * BL + hipZ), (0, hipY - 0.04 * G, -0.3 * BL + hipZ),
          (0, hipY + 0.12 * s, 0.55 * BL + hipZ), (0, hipY + 0.12 * s, 1.3 * BL + hipZ)]
    trx = [0.48 * G, 0.78 * G, 0.78 * G, 0.64 * G, 0.5 * G]
    try_ = [0.58 * G, 0.86 * G, 0.84 * G, 0.72 * G, 0.58 * G]
    torso = eloft(tp, trx, try_, k=0.35 * s)
    torso = torso.su(ellipsoid(0.42 * G, 0.6 * G, 0.85 * BL, (0.4 * G, hipY + 0.05 * s, hipZ + 0.25 * BL)).mirror_x(), 0.3 * s)   # hip muscles
    if P["bumps"]:  # osteoderm rows (carnotaurus)
        def topy(z, x):
            return _interp(z, [p[2] for p in tp], [p[1] + r * 0.9 for p, r in zip(tp, try_)]) - np.abs(x) * 0.25
        torso = torso.su(grid_bumps([0.35 * G, 0.62 * G], -1.9 * BL + hipZ, 1.3 * BL + hipZ, 0.32 * s, topy, 0.09 * s, ry=0.08 * s).mirror_x(), 0.04 * s)
    if P["sail"] > 0:
        sh_ = P["sail"] * s
        z0, z1 = -1.7 * BL + hipZ, 1.25 * BL + hipZ

        def sail_h(z):
            u = np.clip((z - z0) / (z1 - z0), 0, 1)
            return sh_ * np.sin(np.pi * u ** 0.85) ** 0.9

        def top(z):
            return _interp(z, [p[2] for p in tp], [p[1] + r for p, r in zip(tp, try_)]) - 0.12 * s

        def sail_f(p):
            z = np.clip(p[:, 2], z0, z1)
            y0 = top(z)
            hh = sail_h(z)
            dy = np.maximum(p[:, 1] - (y0 + hh), y0 - p[:, 1])
            return np.maximum(np.maximum(dy, np.abs(p[:, 2] - z)), np.abs(p[:, 0]) - 0.05 * s * (1.4 - (p[:, 1] - y0) / max(sh_, 1e-3)))

        zz = np.linspace(z0 + 0.15 * s, z1 - 0.15 * s, 12)
        rays = spikes([(0, float(top(z)), z) for z in zz], [(0, float(top(z) + sail_h(z)) + 0.03 * s, z) for z in zz], 0.08 * s, 0.04 * s)
        H.bone("Sail", "Body", (0, hipY + 1.0 * s, hipZ - 0.2 * BL))
        H.piece("SailP", "Sail", SDF(sail_f).su(rays, 0.04 * s), col="secondary", tris=1600, res=136, role="body", pri=1.15,
                pattern=combine(stripes(lambda Q: Q[:, 2] / s, 1.3, width=0.2, depth=0.25), lambda Q: 1 - 0.35 * np.clip((Q[:, 1] - hipY - 1.0 * s) / (sh_ * 0.9), 0, 1)))
    H.piece("Torso", "Body", tex(torso, 1, 1), col="primary", tris=2600, res=136, pattern=skin())
    if P["feathers"]:  # back / shoulder plumage
        fz = np.linspace(-1.9 * BL + hipZ, 1.0 * BL + hipZ, 8)
        base = [(0, float(_interp(z, [p[2] for p in tp], [p[1] + r for p, r in zip(tp, try_)])) - 0.05 * s, z) for z in fz]
        tips = [(0, b[1] + 0.18 * s, b[2] + 0.28 * s) for b in base]
        H.piece("Plumage", "Body", spikes(base, tips, 0.1 * s, 0.03 * s), col="secondary", tris=700, role="mane", pri=1.3)

    # ------------------------------------------------------------------ legs
    legs = []
    rig_legs = []
    hp = _v((0.66 * G, hipY - 0.05 * s, hipZ + 0.15 * BL))
    kn = hp + thigh
    an = kn + shin
    ba = an + meta
    H.mbone("Hip#", "Body", tuple(hp))
    H.mbone("Knee#", "Hip#", tuple(kn))
    H.mbone("Ankle#", "Knee#", tuple(an))
    H.mbone("Toe#", "Ankle#", tuple(ba))
    LR = P["legr"] * G
    th = round_cone(tuple(hp + _v((-0.05 * s, 0.3 * s, 0.1 * s))), tuple(kn), 0.5 * LR, 0.28 * LR)
    th = th.su(ellipsoid(0.36 * LR, 0.85 * LG, 0.62 * LR, tuple(hp + thigh * 0.45 + _v((0.06 * s, 0, 0.14 * s)))), 0.25 * s)      # drumstick
    H.mpiece("Thigh#", "Hip#", tex(th, 0.8, 2), col="primary", tris=1100, role="limb", pattern=skin())
    sn = round_cone(tuple(kn), tuple(an), 0.28 * LR, 0.15 * LR)
    sn = sn.su(ellipsoid(0.2 * LR, 0.45 * LG, 0.25 * LR, tuple(kn + shin * 0.32 + _v((0, 0, 0.08 * s)))), 0.12 * s)                # calf
    H.mpiece("Shin#", "Knee#", tex(sn, 0.6, 3), col="primary", tris=700, role="limb", pattern=skin())
    mt = round_cone(tuple(an), tuple(ba), 0.14 * LR, 0.12 * LR)
    H.mpiece("Meta#", "Ankle#", tex(mt, 0.5, 4), col="primary", tris=450, role="limb", pattern=skin())
    # foot: three forward toes (+ hallux)
    ft = ellipsoid(0.17 * LR, 0.1 * s, 0.2 * LR, tuple(ba + _v((0, -0.04 * s, -0.05 * s))))
    claws = None
    toe_len = 0.62 * LG
    for i, a in enumerate((-22, 0, 20)):
        ar = math.radians(a)
        d = _v((math.sin(ar), 0, -math.cos(ar)))
        L = toe_len * (1.0 if a == 0 else 0.82)
        tb = ba + _v((0, -0.04 * s, 0))
        tt = _v((tb[0] + d[0] * L, 0.07 * s, tb[2] + d[2] * L))
        if P["sickle"] and a == 20 - 40:  # (unused)
            pass
        ft = ft.su(round_cone(tuple(tb), tuple(tt), 0.1 * LR, 0.065 * LR), 0.05 * s)
        c = round_cone(tuple(tt + _v((0, 0.01 * s, 0))), tuple(tt + d * 0.2 * LG + _v((0, -0.06 * s, 0))), 0.05 * LR, 0.012 * s)
        claws = c if claws is None else (claws | c)
    if P["sickle"]:  # raised killing claw on the inner toe
        sb = ba + _v((-0.06 * s, 0.02 * s, -0.12 * s))
        sk = tube([tuple(sb), tuple(sb + _v((0, 0.2 * s, -0.12 * s)) * 1.0), tuple(sb + _v((0, 0.25 * s, -0.32 * s))), tuple(sb + _v((0, 0.12 * s, -0.42 * s)))],
                  [0.07 * s, 0.06 * s, 0.035 * s, 0.01 * s], k=0.02 * s)
        claws = claws | sk
    ft = ft.su(round_cone(tuple(ba + _v((-0.1 * s, 0.05 * s, 0.05 * s))), tuple(ba + _v((-0.15 * s, -0.02 * s, 0.25 * s))), 0.05 * s, 0.03 * s), 0.03 * s)
    H.mpiece("Foot#", "Toe#", tex(ft, 0.4, 5) & plane((0, -1, 0), 0.0), col="primary", tris=700, role="foot", pattern=skin())
    H.mpiece("Claws#", "Toe#", claws & plane((0, -1, 0), 0.0), col="claw", mat="hard", tris=320, role="claw", pri=1.9, ao=False)
    legs = [("HipR", "KneeR", "AnkleR", "ToeR", 0.0), ("HipL", "KneeL", "AnkleL", "ToeL", 0.5)]
    rig_legs = [{"hip": "HipR", "knee": "KneeR", "phase": 0.0, "side": 1}, {"hip": "HipL", "knee": "KneeL", "phase": 0.5, "side": -1}]

    # ------------------------------------------------------------------ arms
    A = P["arms"]
    arms = []
    if A > 0:
        sh = _v((0.48 * G, hipY - 0.55 * G, -1.55 * BL + hipZ))
        el = sh + _v((0.12 * s, -0.42 * s, -0.12 * s)) * A
        wr = el + _v((-0.02 * s, -0.12 * s, -0.42 * s)) * A
        H.mbone("Arm#", "Body", tuple(sh))
        H.mbone("Elbow#", "Arm#", tuple(el))
        up = round_cone(tuple(sh), tuple(el), 0.16 * s * max(A, 0.6), 0.1 * s * max(A, 0.6))
        H.mpiece("ArmP#", "Arm#", tex(up, 0.4, 6), col="primary", tris=350, role="limb", pattern=skin())
        fo = round_cone(tuple(el), tuple(wr), 0.1 * s * max(A, 0.6), 0.07 * s * max(A, 0.6))
        for i in range(P["fingers"]):
            off = (i - (P["fingers"] - 1) / 2) * 0.07 * s
            d = _v((off, -0.1 * s, -0.2 * s)) * max(A, 0.6)
            fo = fo.su(round_cone(tuple(wr + _v((off, 0, 0))), tuple(wr + d), 0.04 * s * max(A, 0.6), 0.015 * s), 0.03 * s)
        H.mpiece("ForeP#", "Elbow#", tex(fo, 0.3, 7), col="primary", tris=420, role="limb", pattern=skin())
        if P["feathers"]:  # wing-like plumes off the forearm
            pl = None
            for i in range(6):
                u = i / 5
                b0 = el + (wr - el) * u
                tip = b0 + _v((0.04 * s, -0.25 * s - 0.15 * s * u, 0.35 * s - 0.1 * s * u)) * A
                f_ = eloft([tuple(b0), tuple(tip)], [0.03 * s, 0.015 * s], [0.08 * s, 0.03 * s])
                pl = f_ if pl is None else (pl | f_)
            H.mpiece("Plume#", "Elbow#", pl, col="secondary", tris=500, role="wing", pri=1.4)
        arms = [("ArmR", "ElbowR", 1), ("ArmL", "ElbowL", -1)]

    # ------------------------------------------------------------------ neck + head
    NL = P["neck"]
    nb = _v(tp[0]) + _v((0, 0.1 * s, 0.25 * s))
    hc = _v((0, tp[0][1] + 0.62 * s * NL + 0.2 * s, tp[0][2] - 0.95 * s * NL))
    H.bone("Neck", "Body", tuple(nb))
    H.bone("Head", "Neck", tuple(hc))
    nk = eloft([tuple(nb + _v((0, -0.1 * s, 0.35 * s))), tuple((nb + hc) / 2 + _v((0, 0.08 * s, 0.05 * s))), tuple(hc + _v((0, -0.12 * s, 0.1 * s)))],
               [trx[0] * 1.05, trx[0] * 0.85, SKULLS[P["skull"]]["w"][0] * P["hs"] * s * 0.95],
               [try_[0] * 1.0, try_[0] * 0.8, SKULLS[P["skull"]]["t"][0] * P["hs"] * s * 0.9], k=0.2 * s)
    if P["feathers"]:
        nk = nk.su(spikes([tuple((nb + hc) / 2 + _v((0, try_[0] * 0.6, 0)))], [tuple((nb + hc) / 2 + _v((0, try_[0] * 0.6 + 0.2 * s, 0.25 * s)))], 0.12 * s, 0.03 * s), 0.05 * s)
    H.piece("NeckP", "Neck", tex(nk, 0.8, 8), col="primary", tris=900, role="neck", pattern=skin())
    hs = P["hs"] * s

    def extra(head, h):
        sk = SKULLS[P["skull"]]
        if P["horns"] > 0:  # brow horns (carnotaurus) / lacrimal hornlets (allosaurus)
            head = head.su(round_cone(h(sk["w"][1] * 0.55, sk["t"][1] * 0.9 - 0.06, sk["z"][1] - 0.05),
                                      h(sk["w"][1] * 0.75 + P["horns"] * 0.6, sk["t"][1] + P["horns"] * 0.8 - 0.06, sk["z"][1] + 0.05), 0.09, 0.025).mirror_x(), 0.05 * hs)
        if P["crests"] > 0:  # dilophosaurus twin crests
            def cr(p):
                q = (p - _v(h(0, 0, 0))) / hs
                z = np.clip(q[:, 2], sk["z"][4], sk["z"][1])
                u = (z - sk["z"][4]) / (sk["z"][1] - sk["z"][4])
                top = _interp(z, sk["z"], sk["t"]) - 0.06 + P["crests"] * np.sin(np.pi * u) ** 0.7
                dy = np.maximum(q[:, 1] - top, (_interp(z, sk["z"], sk["t"]) - 0.12) - q[:, 1])
                return (np.maximum(np.maximum(dy, np.abs(q[:, 2] - z)), np.abs(np.abs(q[:, 0]) - 0.1) - 0.025)) * hs
            head = head.su(SDF(cr), 0.03 * hs)
        if P["dome"]:  # pachycephalosaurus bone dome + knobs
            head = head.su(sphere(0.48 * hs, h(0, 0.22, -0.05)), 0.12 * hs)
            for a in range(7):
                ang = math.radians(-60 + a * 20)
                head = head.su(sphere(0.055 * hs, h(0.42 * math.sin(ang), 0.2 + 0.05 * math.cos(ang), 0.15 + 0.12 * math.cos(ang))), 0.02 * hs)
            head = head.su(spikes([h(0.12, 0.05, -0.58)], [h(0.14, 0.12, -0.75)], 0.035 * hs, 0.01 * hs).mirror_x(), 0.02 * hs)
        return head

    domepat = None
    if P["dome"]:
        domepat = lambda Q: 1 - 0.0 * Q[:, 0]
    h, HD, my = _skull(H, hc, hs, P["skull"], teeth=P["teeth"], brow=P["brow"], eye_r=P["eye_r"], extra=extra,
                       pattern=skin(), beak=P["beak"], fenestra=not P["dome"])
    if P["dome"]:
        H.piece("Dome", "Head", sphere(0.47 * hs, h(0, 0.24, -0.05)) & half_space(1, -1, hc[1] + 0.32 * hs), col="secondary", mat="hard",
                tris=500, role="horn", pri=1.3)
    if P["feathers"]:
        H.piece("HeadTuft", "Head", spikes([h(0, HD["t"][0] - 0.05, HD["z"][0] - 0.05), h(0.08, HD["t"][0] - 0.1, HD["z"][0])],
                                           [h(0, HD["t"][0] + 0.15, HD["z"][0] + 0.25), h(0.15, HD["t"][0] + 0.05, HD["z"][0] + 0.25)], 0.06 * hs, 0.015 * hs),
                col="secondary", tris=300, role="mane", pri=1.6)

    # ------------------------------------------------------------------ tail (counterweight)
    T, TR = P["tail"], P["tailr"]
    tb = [_v(tp[-1]) + _v((0, 0, -0.1 * s))]
    for i in range(5):
        seglen = (1.15 - 0.08 * i) * s * T
        tb.append(tb[-1] + _v((0, -0.1 * s - 0.03 * s * i, seglen)))
    rad = [trx[-1] * 1.05 * TR, 0.38 * G * TR, 0.27 * G * TR, 0.18 * G * TR, 0.1 * G * TR, 0.04 * s]
    ryf = 1.2 if not P["paddle"] else 1.8
    tails = []
    for i in range(5):
        H.bone(f"Tail{i + 1}", "Body" if i == 0 else f"Tail{i}", tuple(tb[i]))
        tails.append(f"Tail{i + 1}")
    for i in range(5):
        a = tb[i] - _v((0, 0, 0.18 * s))
        b = tb[i + 1]
        ry0 = rad[i] * (ryf if i > 0 else 1.25)
        ry1 = rad[i + 1] * ryf
        st = 0.93 if i > 0 else 1.0  # start slightly inside the previous segment: no coincident surfaces at the joint
        sd = eloft([tuple(a), tuple(b)], [rad[i] * st * (0.9 if not P["paddle"] else 0.6), rad[i + 1] * (0.9 if not P["paddle"] else 0.5)], [ry0 * st, ry1])
        if P["feathers"] and i >= 3:
            fan = None
            for j in range(5):
                ang = math.radians(-40 + 20 * j)
                c = a + (b - a) * 0.5
                tip = c + _v((math.sin(ang) * 0.45 * s, 0.02 * s, 0.35 * s + math.cos(ang) * 0.3 * s))
                f_ = eloft([tuple(c), tuple(tip)], [0.07 * s, 0.03 * s], [0.025 * s, 0.015 * s])
                fan = f_ if fan is None else (fan | f_)
            sd = sd | fan
        H.piece(f"TailP{i + 1}", f"Tail{i + 1}", tex(sd, 0.6, 10 + i), col="primary", tris=max(320, 900 - 120 * i), role="tail",
                pri=1.3 + 0.1 * i, pattern=skin())

    # ------------------------------------------------------------------ rig + motion
    H.socket("mouth", h(0, my, HD["z"][-1] - 0.05), "Head")
    H.socket("head", h(0, max(HD["t"]) + 0.15, HD["z"][1]), "Head")
    seat = (0, hipY + try_[2] * 0.95, -0.55 * BL + hipZ)
    H.socket("seat", seat, "Body")
    if P["mount"]:
        H.mount = {"seat": "Torso", "saddle": {"pos": seat, "size": (1.3 * G, 0.22 * s, 1.5 * s)}}
    H.rig.update({"head": "Head", "jaw": "Jaw", "neck": "Neck", "tail": tails, "legs": rig_legs})
    MR.theropod(H, legs, arms=arms, neck="Neck", head="Head", jaw="Jaw", tail=tails, stride=P["stride"], walk=P["walk"],
                height=hipY + 1.2 * s, attack=P["attack"], heavy=P["heavy"])
    if P.get("mount_len"):
        sole = np.array([ba[0], 0.0, ba[2] - 0.1 * s])
        ws, wp, rs, rp = P["mount_gait"]
        MK.rig_mount(H, torso, -0.55 * BL + hipZ, [("HipR", "KneeR", "AnkleR", False, 1), ("HipL", "KneeL", "AnkleL", False, -1)],
                     {"AnkleR": sole, "AnkleL": sole * np.array([-1, 1, 1])}, hipY + 1.2 * s, P["mount_len"],
                     walk=(wp, "biped", "biped", ws, 0.55 * LG), run=(rp, "biprun", "biprun", rs, 0.9 * LG),
                     neck="Neck", head="Head", jaw="Jaw", tail=tails, pad_col=P.get("pad_col", [0.5, 0.2, 0.12]),
                     ytop=hipY + 4 * s, curl=0.6)
    return H


@hero("tyrannosaurus rex", FAM)
def t_rex():
    return _theropod("tyrannosaurus rex", s=2.4, mount_len=26.0, mount_gait=(7.5, 1.7, 15.0, 1.05), skull="rex", hs=1.35, girth=1.12, legr=1.12, neck=1.05, arms=0.42, teeth=12, brow=0.07, pattern="stripes",
                     pat_depth=0.22, shade=0.72, heavy=1.0, walk=1.35, stride=0.4,
                     preview={"primary": "#6A5A3A", "secondary": "#B8A07A", "iris": "#E8A030"})


# ==================================================================================================== quadrupedal dinosaurs
QBASE = dict(s=1.0, body=1.0, girth=1.0, shY=2.4, hipY=2.5, fleg=1.0, bleg=1.0, legr=1.0, skull="cera", hs=1.0, neck=1.0,
             neck_up=0.2, neck_bones=1, tail=1.0, tailr=1.0, tail_up=0.0, frill=0.0, frill_spikes=0, brow_horns=0.0, nose_horn=0.0,
             plates=0.0, thago=False, armour=False, side_spikes=0.0, club=0.0, crest=0.0, thumb=False, nasal=0.0, pattern=None,
             pat_depth=0.4, shade=0.78, attack="gore", walk=1.4, stride=0.36, mount=True, preview={})


def _quaddino(hid, **kw):
    P = dict(QBASE)
    P.update(kw)
    s = P["s"]
    BL, G = P["body"] * s, P["girth"] * s
    shY, hipY = P["shY"] * s, P["hipY"] * s
    H = Hero(hid, plan="Quadruped", gait="heavy", tags=["dinosaur", "reptile"])
    H.preview = P["preview"]
    midY = (shY + hipY) / 2
    H.body((0, midY, 0))

    def shade(Q):
        return 1 - (1 - P["shade"]) * np.clip((Q[:, 1] - (midY - 0.9 * G)) / (1.9 * G), 0, 1)

    pat = None
    if P["pattern"] == "stripes":
        pat = stripes(lambda Q: Q[:, 2] / s + 0.3 * np.abs(Q[:, 1] / s - midY), 0.9, width=0.3, depth=P["pat_depth"], wobble=0.1, seed=3)
    elif P["pattern"] == "spots":
        pat = spots(0.5 * s, 0.17 * s, depth=P["pat_depth"], seed=4)
    elif P["pattern"] == "blotch":
        pat = spots(0.7 * s, 0.28 * s, depth=P["pat_depth"], seed=6)

    def skin(extra=None):
        return combine(shade, pat, extra)

    def tex(sd, a=1.0, seed=0):
        return sd.noise(0.014 * a * s, 6.0 / s, seed)

    # ------------------------------------------------------------------ trunk (barrel)
    tp = [(0, shY - 0.05 * G, -1.75 * BL), (0, shY + 0.05 * G, -0.9 * BL), (0, midY + 0.12 * G, 0.1 * BL), (0, hipY + 0.05 * G, 1.0 * BL),
          (0, hipY - 0.1 * G, 1.75 * BL)]
    trx = [0.62 * G, 0.95 * G, 1.02 * G, 0.92 * G, 0.6 * G]
    try_ = [0.68 * G, 1.0 * G, 1.08 * G, 1.0 * G, 0.68 * G]
    torso = eloft(tp, trx, try_, k=0.4 * s)

    def top_y(z, x=0.0):
        return _interp(z, [p[2] for p in tp], [p[1] + r for p, r in zip(tp, try_)]) - np.abs(x) * 0.35

    if P["armour"]:
        torso = torso.su(grid_bumps([0.0, 0.32 * G, 0.62 * G, 0.88 * G], -1.6 * BL, 1.65 * BL, 0.34 * s,
                                    lambda z, x: top_y(z, x) - 0.08 * s - (0.25 * s if x > 0.8 * G else 0.0), 0.14 * s, ry=0.1 * s, rz=0.14 * s, jitter=1.0).mirror_x(), 0.04 * s)
    if P["side_spikes"] > 0:
        zz = np.linspace(-1.5 * BL, 1.5 * BL, 7)
        base = [(float(_interp(z, [p[2] for p in tp], trx)) * 0.92, float(_interp(z, [p[2] for p in tp], [p[1] for p in tp])) - 0.05 * s, z) for z in zz]
        tips = [(b[0] + P["side_spikes"] * s, b[1] - 0.05 * s, b[2] + 0.1 * s) for b in base]
        torso = torso.su(spikes(base, tips, 0.13 * s, 0.03 * s).mirror_x(), 0.05 * s)
    H.piece("Torso", "Body", tex(torso, 1, 1), col="primary", tris=2600, res=136, pattern=skin())
    if P["plates"] > 0:  # stegosaurus: two alternating rows of kite plates along neck, back and tail base
        zz = np.linspace(-1.9 * BL, 1.85 * BL, 9)
        pl = None
        for i, z in enumerate(zz):
            u = (z - zz[0]) / (zz[-1] - zz[0])
            hgt = P["plates"] * s * (0.35 + 0.65 * math.sin(math.pi * min(u * 1.05, 1.0)) ** 0.8)
            x = 0.12 * s * (1 if i % 2 == 0 else -1)
            y0 = float(top_y(z)) - 0.15 * s
            plate = ellipsoid(0.05 * s, hgt * 0.55, hgt * 0.42, (0, 0, 0)).rot(0, 0, (8 if x > 0 else -8)).at(x, y0 + hgt * 0.45, z + 0.08 * s)
            plate = plate & half_space(1, -1, y0 - 0.1 * s).at(0, 0, 0) if False else plate
            pl = plate if pl is None else (pl | plate)
        H.piece("Plates", "Body", pl, col="secondary", mat="hard", tris=1800, res=128, role="horn", pri=1.15,
                pattern=lambda Q: 1 - 0.3 * np.clip((Q[:, 1] - shY) / (P["plates"] * s * 1.2), 0, 1))

    # ------------------------------------------------------------------ legs (columns, hoof-toed feet)
    legs = []
    rig_legs = []
    LR = P["legr"] * G
    for front in (True, False):
        tag = "F" if front else "B"
        L_ = P["fleg"] if front else P["bleg"]
        z0 = (-1.3 if front else 1.15) * BL
        top = (shY if front else hipY) - 0.35 * G
        sh = _v((0.66 * G, top, z0))
        footy = 0.3 * s
        el = _v((0.7 * G, footy + (top - footy) * 0.5, z0 + (0.12 if front else -0.25) * s))
        wr = _v((0.68 * G, footy, z0 + (-0.05 if front else 0.08) * s))
        H.mbone(f"Up{tag}#", "Body", tuple(sh))
        H.mbone(f"Lo{tag}#", f"Up{tag}#", tuple(el))
        H.mbone(f"Ft{tag}#", f"Lo{tag}#", tuple(wr))
        r0 = (0.42 if front else 0.52) * LR
        up = round_cone(tuple(sh + _v((-0.1 * s, 0.25 * s, 0))), tuple(el), r0, r0 * 0.62)
        up = up.su(ellipsoid(r0 * 0.85, (top - el[1]) * 0.55, r0 * 1.1, tuple((sh + el) / 2 + _v((0.02 * s, 0.1 * s, 0.05 * s)))), 0.2 * s)
        H.mpiece(f"Upper{tag}#", f"Up{tag}#", tex(up, 0.8, 2), col="primary", tris=900, role="limb", pattern=skin())
        lo = round_cone(tuple(el), tuple(wr), r0 * 0.62, r0 * 0.52)
        H.mpiece(f"Lower{tag}#", f"Lo{tag}#", tex(lo, 0.6, 3), col="primary", tris=600, role="limb", pattern=skin())
        ft = cylinder(r0 * 0.62, 0.17 * s).at(wr[0], 0.17 * s, wr[2] - 0.05 * s).su(sphere(r0 * 0.55, tuple(wr)), 0.1 * s)
        nails = None
        for a in ((-35, 0, 35) if not front else (-45, -15, 15, 45)):
            ar = math.radians(a)
            c = _v((wr[0] + math.sin(ar) * r0 * 0.6, 0.1 * s, wr[2] - math.cos(ar) * r0 * 0.62))
            nl = ellipsoid(0.11 * s, 0.1 * s, 0.1 * s, tuple(c))
            nails = nl if nails is None else (nails | nl)
        H.mpiece(f"Foot{tag}#", f"Ft{tag}#", (ft & plane((0, -1, 0), 0.0)), col="primary", tris=500, role="foot", pattern=skin(lambda Q: np.ones(len(Q)) * 0.88))
        H.mpiece(f"Nails{tag}#", f"Ft{tag}#", nails & plane((0, -1, 0), 0.0), col="hoof", mat="hard", tris=260, role="claw", pri=2.0, ao=False)
        ph = 0.25 if front else 0.0
        legs += [(f"Up{tag}R", f"Lo{tag}R", f"Ft{tag}R", ph + 0.5, front), (f"Up{tag}L", f"Lo{tag}L", f"Ft{tag}L", ph, front)]
        rig_legs += [{"hip": f"Up{tag}R", "knee": f"Lo{tag}R", "phase": ph + 0.5, "side": 1}, {"hip": f"Up{tag}L", "knee": f"Lo{tag}L", "phase": ph, "side": -1}]
        if front and P["thumb"]:
            H.mpiece("Thumb#", f"Ft{tag}#", round_cone(tuple(wr + _v((-0.25 * s, 0.25 * s, -0.1 * s))), tuple(wr + _v((-0.35 * s, 0.45 * s, -0.35 * s))), 0.08 * s, 0.02 * s),
                     col="horn", mat="hard", tris=200, role="claw", pri=2.0)

    # ------------------------------------------------------------------ neck (1..3 bones) + head
    NL, nb_ = P["neck"], P["neck_bones"]
    n0 = _v(tp[0]) + _v((0, 0.05 * s, 0.35 * s))
    up_ = P["neck_up"]
    nd = _v((0, math.sin(up_), -math.cos(up_)))
    seglen = 1.25 * s * NL / nb_
    prev = "Body"
    npts = [n0]
    for i in range(nb_):
        # sauropod necks curve upward more toward the head
        a = up_ + (0.18 * i if nb_ > 1 else 0.0)
        d = _v((0, math.sin(a), -math.cos(a)))
        npts.append(npts[-1] + d * seglen)
    nr = [trx[0] * 0.95] + [trx[0] * (0.82 - 0.45 * (i + 1) / nb_) + 0.12 * s for i in range(nb_)]
    nry = [try_[0] * 0.95] + [try_[0] * (0.85 - 0.45 * (i + 1) / nb_) + 0.12 * s for i in range(nb_)]
    nbones = []
    for i in range(nb_):
        nm = "Neck" if nb_ == 1 else f"Neck{i + 1}"
        H.bone(nm, prev, tuple(npts[i]))
        nbones.append(nm)
        a = npts[i] - (npts[i + 1] - npts[i]) * (0.25 if i == 0 else 0.12)
        st = 0.94 if i > 0 else 1.0
        sd = eloft([tuple(a), tuple(npts[i + 1])], [nr[i] * st, nr[i + 1]], [nry[i] * st, nry[i + 1]])
        H.piece(f"NeckP{i + 1}" if nb_ > 1 else "NeckP", nm, tex(sd, 0.6, 4 + i), col="primary", tris=900 if nb_ == 1 else 650, role="neck", pattern=skin())
        prev = nm
    hs = P["hs"] * s
    sk = P["skull"]
    hc = npts[-1] + _v((0, 0.02 * s, -0.05 * s))
    H.bone("Head", prev, tuple(hc))
    HD = SKULLS[sk]

    def extra(head, h):
        if P["nasal"] > 0:  # brachiosaurus nasal arch
            head = head.su(ellipsoid(0.17, 0.2 + P["nasal"], 0.22, h(0, HD["t"][1] - 0.02, HD["z"][1] - 0.05)).scale(1.0), 0.08 * hs) if False else \
                head.su(ellipsoid(0.17 * hs, (0.16 + P["nasal"]) * hs, 0.22 * hs, h(0, HD["t"][1] + 0.02, HD["z"][1] - 0.08)), 0.1 * hs)
        if sk == "ankylo":  # squamosal horns at the back corners
            head = head.su(spikes([h(0.42, 0.18, 0.2), h(0.45, -0.02, 0.1)], [h(0.62, 0.3, 0.35), h(0.66, -0.1, 0.25)], 0.09 * hs, 0.02 * hs).mirror_x(), 0.04 * hs)
        return head

    h, HD, my = _skull(H, hc, hs, sk, pattern=skin(), teeth=0, brow=0.04, eye_r=0.07, pupil="round", fenestra=False, extra=extra, beak=True,
                       tris=1500, jaw_tris=700)
    if P["frill"] > 0:  # ceratopsian frill (+ epoccipital spikes) and horns
        fr = P["frill"] * hs
        c0 = _v(h(0, 0.45, 0.25))
        TILT = 42.0
        fc = c0 + _v((0, fr * 0.55, fr * 0.5))
        frill = ellipsoid(fr * 1.0, fr * 0.85, 0.07 * hs, (0, 0, 0)).rot(TILT, 0, 0).at(*fc)
        frill = frill.su(ellipsoid(fr * 0.35, fr * 0.6, 0.16 * hs, (0, -fr * 0.25, 0.04 * hs)).rot(TILT, 0, 0).at(*fc), 0.08 * hs)  # midline ridge / base
        knobs = []
        ca, sa = math.cos(math.radians(TILT)), math.sin(math.radians(TILT))
        for i in range(11):
            a = math.radians(-100 + i * 20)
            rr = _v((math.sin(a) * fr * 0.98, math.cos(a) * fr * 0.83, 0))
            knobs.append(_v((rr[0], rr[1] * ca, rr[1] * sa)) + fc)
        if P["frill_spikes"]:
            tips = [k_ + (k_ - fc) * (0.6 if abs(i - 5) <= 2 else 0.25) for i, k_ in enumerate(knobs)]
            frill = frill.su(spikes([tuple(k_) for k_ in knobs], [tuple(t_) for t_ in tips], 0.1 * hs, 0.025 * hs), 0.04 * hs)
        else:
            for k_ in knobs:
                frill = frill.su(sphere(0.08 * hs, tuple(k_)), 0.03 * hs)
        H.piece("Frill", "Head", frill, col="secondary", tris=1500, res=128, role="mane", pri=1.1,
                pattern=lambda Q: 1 - 0.35 * np.clip(np.linalg.norm(Q - c0, axis=1) / (P["frill"] * hs * 1.2), 0, 1))
        hb, ht = [], []
        if P["brow_horns"] > 0:
            L = P["brow_horns"]
            hb += [h(0.2, 0.5, -0.25), h(-0.2, 0.5, -0.25)]
            ht += [h(0.32, 0.85 + 0.35 * L, -0.5 - 0.95 * L), h(-0.32, 0.85 + 0.35 * L, -0.5 - 0.95 * L)]
        if P["nose_horn"] > 0:
            L = P["nose_horn"]
            hb += [h(0, 0.3, -0.85)]
            ht += [h(0, 0.4 + 0.8 * L, -0.95 - 0.2 * L)]
        if hb:
            H.piece("Horns", "Head", spikes(hb, ht, 0.12 * hs, 0.02 * hs), col="horn", mat="hard", tris=700, role="horn", pri=1.2)
    if P["crest"] > 0:  # parasaurolophus tube crest
        cr = tube([h(0, 0.3, -0.45), h(0, 0.55, 0.0), h(0, 0.85, 0.75 * P["crest"]), h(0, 1.0, 1.35 * P["crest"])],
                  [0.13 * hs, 0.13 * hs, 0.12 * hs, 0.09 * hs], k=0.05 * hs)
        H.piece("Crest", "Head", cr, col="secondary", tris=700, role="horn", pri=1.2)

    # ------------------------------------------------------------------ tail
    T, TR = P["tail"], P["tailr"]
    tb = [_v(tp[-1]) + _v((0, 0.05 * s, -0.25 * s))]
    for i in range(5):
        seglen = (1.0 - 0.06 * i) * s * T
        tb.append(tb[-1] + _v((0, -0.18 * s + P["tail_up"] * s - 0.02 * s * i, seglen)))
    rad = [trx[-1] * 0.98 * TR, 0.42 * G * TR, 0.3 * G * TR, 0.2 * G * TR, 0.12 * G * TR, 0.05 * s]
    tails = []
    for i in range(5):
        H.bone(f"Tail{i + 1}", "Body" if i == 0 else f"Tail{i}", tuple(tb[i]))
        tails.append(f"Tail{i + 1}")
    for i in range(5):
        a = tb[i] - _v((0, 0, 0.2 * s))
        b = tb[i + 1]
        st = 0.93 if i > 0 else 1.0
        sd = eloft([tuple(a), tuple(b)], [rad[i] * 0.95 * st, rad[i + 1] * 0.95], [rad[i] * 1.08 * st, rad[i + 1] * 1.08])
        if P["plates"] > 0 and i < 2:
            for j, u in enumerate((0.3, 0.8)):
                c = a + (b - a) * u
                r_ = rad[i] + (rad[i + 1] - rad[i]) * u
                hgt = P["plates"] * s * (0.5 - 0.15 * i - 0.08 * j)
                x = 0.1 * s * (1 if j % 2 == 0 else -1)
                sd = sd | ellipsoid(0.045 * s, hgt * 0.55, hgt * 0.42, tuple(c + _v((x, r_ * 0.8 + hgt * 0.4, 0))))
        if P["thago"] and i == 4:
            base = [tuple(a + (b - a) * u + _v((0.05 * s, 0.05 * s, 0))) for u in (0.25, 0.7)]
            tips = [tuple(_v(bb) + _v((0.55 * s, 0.35 * s, 0.25 * s))) for bb in base]
            H.piece("Thagomizer", "Tail5", spikes(base, tips, 0.08 * s, 0.015 * s).mirror_x(), col="horn", mat="hard", tris=500, role="horn", pri=1.3)
        if P["armour"] and i < 4:
            sd = sd.su(spikes([tuple(a + (b - a) * 0.5 + _v((rad[i] * 0.8, 0, 0)))], [tuple(a + (b - a) * 0.5 + _v((rad[i] * 0.8 + 0.25 * s, 0.05 * s, 0.05 * s)))],
                              0.09 * s, 0.02 * s).mirror_x(), 0.03 * s)
        if P["club"] > 0 and i == 4:
            c = b - (b - a) * 0.15
            club = ellipsoid(P["club"] * s * 1.1, P["club"] * s * 0.6, P["club"] * s * 0.85, tuple(c))
            club = club.su(ellipsoid(P["club"] * s * 0.6, P["club"] * s * 0.5, P["club"] * s * 0.6, tuple(c + _v((P["club"] * s * 0.6, 0, 0)))).mirror_x(), 0.1 * s)
            H.piece("Club", "Tail5", tex(club, 0.8, 30), col="secondary", mat="hard", tris=700, role="tail", pri=1.2)
        H.piece(f"TailP{i + 1}", f"Tail{i + 1}", tex(sd, 0.6, 10 + i), col="primary", tris=max(320, 900 - 120 * i), role="tail", pri=1.3 + 0.1 * i, pattern=skin())

    # ------------------------------------------------------------------ rig + motion
    height = max(shY, hipY) + 0.8 * G
    H.socket("mouth", h(0, my, HD["z"][-1] - 0.05), "Head")
    H.socket("head", h(0, max(HD["t"]) + 0.15, HD["z"][1]), "Head")
    seat = (0, float(top_y(-0.3 * BL)) + 0.05 * s, -0.3 * BL)
    H.socket("seat", seat, "Body")
    if P["mount"]:
        H.mount = {"seat": "Torso", "saddle": {"pos": seat, "size": (1.4 * G, 0.22 * s, 1.6 * s)}}
    H.rig.update({"head": "Head", "jaw": "Jaw", "neck": nbones[0], "tail": tails, "legs": rig_legs})
    neck_bone = nbones[-1] if nb_ > 1 else nbones[0]
    motion.quadruped(H, legs, neck=nbones[0], head="Head", jaw="Jaw", tail=tails, stride=P["stride"], walk=P["walk"], height=height,
                     attack="gore" if P["attack"] == "gore" else "bite")
    if nb_ > 1:  # sway the whole neck chain a little in Idle / Move
        idle = H.clips["Idle"]
    if P["attack"] == "tailswing":
        def atk(t):
            s_ = t / 1.1
            pose = {}
            sw = MR._win(s_, 0.1, 0.85)
            wind = MR._win(s_, 0.0, 0.35)
            MR._add(pose, "Body", (0, 0, 0, 0, -0.5 * sw + 0.15 * wind, 0.05 * sw))
            for i, b in enumerate(tails):
                MR._add(pose, b, (0, 0.0, 0, 0.05 * sw, 0.28 * math.sin(math.pi * min(max((s_ - 0.08 * i) / 0.75, 0), 1)) - 0.12 * wind, 0))
            MR._add(pose, nbones[0], (0, 0, 0, -0.1 * sw, 0.2 * sw, 0))
            return pose

        H.clip("Attack", 1.1, atk, keys=16, loop=False)
    elif P["attack"] == "stomp":
        def atk(t):
            s_ = t / 1.3
            pose = {}
            rear = MR._win(s_, 0.0, 0.75) ** 0.8
            slam = MR._win(s_, 0.55, 0.85)
            MR._add(pose, "Body", (0, 0.35 * height * rear * 0.4, 0.35 * height * 0.15 * rear, 0.32 * rear, 0, 0))
            for up, lo, ft, ph, fr in legs:
                if fr:
                    MR._add(pose, up, (0, 0, 0, 0.5 * rear, 0, 0))
                    MR._add(pose, lo, (0, 0, 0, -0.6 * rear, 0, 0))
                else:
                    MR._add(pose, up, (0, 0, 0, -0.3 * rear, 0, 0))
            for b in nbones:
                MR._add(pose, b, (0, 0, 0, -0.12 * rear + 0.1 * slam, 0, 0))
            for i, b in enumerate(tails):
                MR._add(pose, b, (0, 0, 0, -0.08 * rear, 0, 0))
            return pose

        H.clip("Attack", 1.3, atk, keys=16, loop=False)
    if nb_ > 1:
        # neck chain idle / move sway (quadruped() only drives the first neck bone)
        for clip, L, amp in (("Idle", 4.8, 0.06), ("Move", P["walk"], 0.03)):
            c = H.clips[clip]
            n = c["keys"]
            for i, b in enumerate(nbones[1:]):
                vals = []
                for k in range(n):
                    t = c["len"] * k / n
                    vals.append((0, 0, 0, amp * 0.5 * math.sin(2 * math.pi * t / c["len"] - i * 0.6), amp * math.sin(2 * math.pi * t / c["len"] - 0.8 - i * 0.6), 0))
                c["tracks"][b] = vals
    return H


@hero("triceratops", FAM)
def triceratops():
    return _quaddino("triceratops", skull="cera", hs=1.35, shY=2.0, hipY=2.3, body=0.95, girth=1.05, neck=0.45, neck_up=-0.1, frill=1.05,
                     brow_horns=1.0, nose_horn=0.3, tail=0.8, attack="gore", pattern="stripes", pat_depth=0.15,
                     preview={"primary": "#6A7A4A", "secondary": "#A8885A", "horn": "#EDE3C8", "beak": "#3A3530", "iris": "#C9A03A"})


@hero("styracosaurus", FAM)
def styracosaurus():
    return _quaddino("styracosaurus", skull="cera", hs=1.3, shY=2.0, hipY=2.3, body=0.95, girth=1.0, neck=0.45, neck_up=-0.1, frill=0.9,
                     frill_spikes=1, nose_horn=0.95, tail=0.8, attack="gore", pattern="blotch", pat_depth=0.25,
                     preview={"primary": "#8A6A3A", "secondary": "#C8783A", "horn": "#EDE3C8", "beak": "#3A3530", "iris": "#C9A03A"})


@hero("stegosaurus", FAM)
def stegosaurus():
    return _quaddino("stegosaurus", skull="stego", hs=1.2, shY=1.85, hipY=2.75, body=1.0, girth=0.95, fleg=0.75, neck=0.75, neck_up=-0.32,
                     plates=1.25, thago=True, tail=1.05, tail_up=0.12, attack="tailswing", pattern="spots", pat_depth=0.2,
                     preview={"primary": "#6A7A5A", "secondary": "#B8603A", "horn": "#E8DCC0", "beak": "#3A3530", "iris": "#C9A03A"})


@hero("ankylosaurus", FAM)
def ankylosaurus():
    return _quaddino("ankylosaurus", skull="ankylo", hs=1.35, shY=1.55, hipY=1.65, body=1.0, girth=1.3, legr=0.9, neck=0.35, neck_up=-0.15,
                     armour=True, side_spikes=0.38, club=0.42, tail=1.0, tail_up=0.12, attack="tailswing",
                     preview={"primary": "#7A6A4A", "secondary": "#5A4A30", "horn": "#D8CBA8", "beak": "#3A3530", "iris": "#C9A03A"})


@hero("parasaurolophus", FAM)
def parasaurolophus():
    return _quaddino("parasaurolophus", skull="hadro", hs=1.3, shY=2.0, hipY=2.8, body=0.95, girth=0.9, fleg=0.7, legr=0.85, neck=0.95, neck_up=0.35,
                     crest=1.0, tail=1.15, tail_up=0.1, attack="gore", pattern="stripes", pat_depth=0.25, walk=1.2,
                     preview={"primary": "#7A8A5A", "secondary": "#C86A3A", "beak": "#C8B070", "iris": "#C9A03A"})


@hero("iguanodon", FAM)
def iguanodon():
    return _quaddino("iguanodon", skull="hadro", hs=1.25, shY=2.1, hipY=2.85, body=1.0, girth=0.95, fleg=0.75, legr=0.9, neck=0.85, neck_up=0.3,
                     thumb=True, tail=1.1, tail_up=0.1, attack="gore", pattern="blotch", pat_depth=0.2, walk=1.25,
                     preview={"primary": "#5A7A4A", "secondary": "#A89A6A", "beak": "#4A4030", "horn": "#E8DCC0", "iris": "#C9A03A"})


@hero("brachiosaurus", FAM)
def brachiosaurus():
    return _quaddino("brachiosaurus", skull="sauro", hs=1.45, shY=3.6, hipY=3.0, body=1.0, girth=1.0, legr=0.8, neck=4.6, neck_up=0.95,
                     neck_bones=3, nasal=0.15, tail=0.85, attack="stomp", walk=1.8, stride=0.3,
                     preview={"primary": "#7A8A7A", "secondary": "#A8A890", "beak": "#5A5A50", "iris": "#2A2A2A"})


@hero("diplodocus", FAM)
def diplodocus():
    return _quaddino("diplodocus", skull="sauro", hs=1.25, shY=2.55, hipY=2.95, body=1.05, girth=0.95, legr=0.75, neck=4.2, neck_up=0.25,
                     neck_bones=3, tail=2.0, tailr=0.9, tail_up=0.12, attack="stomp", walk=1.7, stride=0.3, pattern="stripes", pat_depth=0.2,
                     preview={"primary": "#8A7A5A", "secondary": "#B8A884", "beak": "#5A5040", "iris": "#2A2A2A"})


# ==================================================================================================== pterosaurs
def _membrane(x0, x1, y_fn, zle_fn, zte_fn, th):
    """Thin wing membrane spanning x0..x1 (right side): leading edge z = zle(x), trailing edge z = zte(x), mid-surface y(x)."""

    def f(p):
        x = p[:, 0]
        xc = np.clip(x, x0, x1)
        d = np.abs(p[:, 1] - y_fn(xc)) - th
        d = np.maximum(d, zle_fn(xc) - p[:, 2])
        d = np.maximum(d, p[:, 2] - zte_fn(xc))
        d = np.maximum(d, np.maximum(x0 - x, x - x1))
        return d

    return SDF(f)


def _pterosaur(hid, s=1.0, span=1.0, crest=1.0, crest_kind="back", hs=1.0, teeth=False, preview=None):
    H = Hero(hid, plan="Bird", gait="fly", tags=["dinosaur", "reptile", "flying"])
    H.preview = preview or {}
    by = 1.45 * s
    H.body((0, by, 0))
    torso = eloft([(0, by + 0.02 * s, -0.55 * s), (0, by, -0.1 * s), (0, by - 0.02 * s, 0.4 * s), (0, by - 0.02 * s, 0.75 * s)],
                  [0.22 * s, 0.32 * s, 0.26 * s, 0.1 * s], [0.25 * s, 0.32 * s, 0.24 * s, 0.09 * s], k=0.15 * s)
    torso = torso.noise(0.01 * s, 10 / s, 1)
    H.piece("Torso", "Body", torso, col="primary", tris=1300, pattern=lambda Q: 1 - 0.25 * np.clip((Q[:, 1] - by + 0.1 * s) / (0.4 * s), 0, 1))
    # wings: arm (shoulder -> wrist) and hand (wrist -> long wing finger tip)
    S_ = span * s
    sh = _v((0.22 * s, by + 0.12 * s, -0.4 * s))
    wr = _v((1.55 * S_, by + 0.22 * s, -0.42 * s))
    tip = _v((3.9 * S_, by + 0.05 * s, 0.35 * s))
    H.mbone("Arm#", "Body", tuple(sh))
    H.mbone("Hand#", "Arm#", tuple(wr))
    arm = round_cone(tuple(sh), tuple(wr), 0.11 * s, 0.07 * s)
    arm = arm.su(sphere(0.09 * s, tuple(wr)), 0.03 * s)
    inner = _membrane(sh[0], wr[0] + 0.05 * s, lambda x: sh[1] + (wr[1] - sh[1]) * (x - sh[0]) / (wr[0] - sh[0]) - 0.01 * s,
                      lambda x: sh[2] + (wr[2] - sh[2]) * (x - sh[0]) / (wr[0] - sh[0]),
                      lambda x: 0.55 * s + (0.25 * s - 0.55 * s) * ((x - sh[0]) / (wr[0] - sh[0])) ** 1.3, 0.025 * s)
    H.mpiece("WingIn#", "Arm#", arm | inner, col="primary", tris=900, res=128, role="wing",
             pattern=lambda Q: 1 - 0.3 * np.clip((Q[:, 2] - Q[:, 2].min()) / (0.8 * s), 0, 1) * 0.6)
    fing = tube([tuple(wr), tuple(wr + (tip - wr) * 0.5 + _v((0, 0.05 * s, -0.05 * s))), tuple(tip)], [0.06 * s, 0.045 * s, 0.02 * s], k=0.02 * s)
    claws = spikes([tuple(wr + _v((0.02 * s, 0.0, -0.05 * s)))], [tuple(wr + _v((0.0, 0.05 * s, -0.22 * s)))], 0.03 * s, 0.008 * s)
    span_x = tip[0] - wr[0]

    def te(x):
        u = np.clip((x - wr[0]) / span_x, 0, 1)
        return 0.25 * s + (tip[2] - 0.25 * s) * u ** 0.7 + 0.15 * s * np.sin(np.pi * u)

    def le(x):
        u = np.clip((x - wr[0]) / span_x, 0, 1)
        return wr[2] + (tip[2] - wr[2]) * u + 0.05 * s * np.sin(np.pi * u) * 0

    outer = _membrane(wr[0] - 0.05 * s, tip[0], lambda x: wr[1] + (tip[1] - wr[1]) * (x - wr[0]) / span_x - 0.01 * s, le, te, 0.022 * s)
    H.mpiece("WingOut#", "Hand#", fing | outer | claws, col="primary", tris=1100, res=136, role="wing",
             pattern=lambda Q: 1 - 0.35 * np.clip((Q[:, 0] - wr[0]) / span_x, 0, 1) ** 2)
    # legs (trailing back in flight)
    H.mbone("Leg#", "Body", (0.15 * s, by - 0.15 * s, 0.45 * s))
    lg = round_cone((0.15 * s, by - 0.15 * s, 0.45 * s), (0.22 * s, by - 0.3 * s, 0.95 * s), 0.07 * s, 0.04 * s)
    lg = lg.su(spikes([(0.22 * s, by - 0.3 * s, 0.95 * s)] * 3, [(0.17 * s + 0.05 * s * i, by - 0.32 * s, 1.15 * s) for i in range(3)], 0.03 * s, 0.01 * s), 0.02 * s)
    H.mpiece("LegP#", "Leg#", lg, col="primary", tris=350, role="limb")
    # neck + head + crest
    H.bone("Neck", "Body", (0, by + 0.05 * s, -0.5 * s))
    hc = _v((0, by + 0.35 * s, -1.05 * s))
    H.bone("Head", "Neck", tuple(hc))
    nk = round_cone((0, by + 0.0 * s, -0.4 * s), tuple(hc + _v((0, -0.05 * s, 0.1 * s))), 0.17 * s, 0.11 * s)
    H.piece("NeckP", "Neck", nk, col="primary", tris=600, role="neck")
    hs_ = hs * s

    h, HD, my = _skull(H, hc, hs_, "ptero", teeth=8 if teeth else 0, brow=0.0, eye_r=0.06, pupil="round", fenestra=False, beak=not teeth,
                       tris=1300, jaw_tris=600, pattern=lambda Q: 1 - 0.2 * np.clip((Q[:, 1] - hc[1]) / (0.4 * s), 0, 1))
    if crest_kind == "back":
        cr = eloft([h(0, 0.12, -0.05), h(0, 0.32, 0.55 * crest), h(0, 0.44, 1.1 * crest)], [0.05 * hs_, 0.04 * hs_, 0.02 * hs_],
                   [0.17 * hs_, 0.13 * hs_, 0.05 * hs_], k=0.05 * hs_)
    else:  # rounded head crest
        cr = ellipsoid(0.04 * hs_, 0.22 * crest * hs_, 0.4 * crest * hs_, h(0, 0.24, -0.15))
    H.piece("Crest", "Head", cr, col="secondary", tris=500, role="horn", pri=1.2,
            pattern=lambda Q: 1 - 0.3 * np.clip((Q[:, 2] - hc[2]) / (1.0 * s), 0, 1))
    tl = round_cone((0, by, 0.6 * s), (0, by + 0.02 * s, 1.15 * s), 0.07 * s, 0.02 * s)
    H.bone("Tail1", "Body", (0, by, 0.65 * s))
    H.piece("TailP", "Tail1", tl, col="primary", tris=200, role="tail", pri=1.8)
    H.mprim("Toe#", "Leg#", "Ellipsoid", (0.06 * s, 0.04 * s, 0.14 * s), (0.2 * s, by - 0.32 * s, 1.08 * s), col="claw", mat="hard", pri=2.2)
    H.socket("mouth", h(0, my, HD["z"][-1]), "Head")
    H.socket("head", h(0, 0.4, 0), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "neck": "Neck", "wings": ["ArmR", "ArmL"], "tail": ["Tail1"]})
    MR.fly(H, [("ArmR", "HandR", 1), ("ArmL", "HandL", -1)], head="Head", neck="Neck", jaw="Jaw", legs=[], walk=1.3, height=by + 0.5 * s,
           flap=0.42)
    return H


@hero("pteranodon", FAM)
def pteranodon():
    return _pterosaur("pteranodon", crest=1.0, hs=1.15, preview={"primary": "#8A7A6A", "secondary": "#E8701E", "beak": "#D8B070", "iris": "#2A2A2A"})


@hero("pterodactyl", FAM)
def pterodactyl():
    return _pterosaur("pterodactyl", span=0.85, crest=0.45, crest_kind="round", hs=1.0, teeth=True,
                      preview={"primary": "#7A6A5A", "secondary": "#D8B88A", "iris": "#C9A03A"})


# ==================================================================================================== marine reptiles
def _marine(hid, kind, s=1.0, preview=None):
    H = Hero(hid, plan="Fish", gait="swim", tags=["dinosaur", "reptile", "aquatic"])
    H.preview = preview or {}
    by = 1.2 * s
    H.body((0, by, 0))
    countershade = lambda Q: 1 - 0.45 * np.clip((Q[:, 1] - by + 0.3 * s) / (0.8 * s), 0, 1)
    if kind == "plesio":
        torso = eloft([(0, by, -1.5 * s), (0, by + 0.05 * s, -0.5 * s), (0, by + 0.05 * s, 0.6 * s), (0, by, 1.5 * s)],
                      [0.5 * s, 0.95 * s, 0.9 * s, 0.35 * s], [0.42 * s, 0.6 * s, 0.58 * s, 0.3 * s], k=0.3 * s)
        H.piece("Torso", "Body", torso.noise(0.008 * s, 8 / s, 1), col="primary", tris=2200, res=128, pattern=countershade)
        fl = []
        for front in (True, False):
            tag = "F" if front else "B"
            sh = _v((0.75 * s, by - 0.15 * s, (-0.8 if front else 0.75) * s))
            wr = sh + _v((0.9 * s, -0.15 * s, 0.25 * s))
            tip = wr + _v((1.0 * s, -0.08 * s, 0.6 * s))
            H.mbone(f"Fl{tag}#", "Body", tuple(sh))
            H.mbone(f"FlT{tag}#", f"Fl{tag}#", tuple(wr))
            inn = eloft([tuple(sh - _v((0.25 * s, 0, 0))), tuple(wr)], [0.24 * s, 0.26 * s], [0.12 * s, 0.07 * s])
            out = eloft([tuple(wr), tuple(wr + (tip - wr) * 0.5), tuple(tip)], [0.26 * s, 0.22 * s, 0.05 * s], [0.07 * s, 0.05 * s, 0.03 * s], k=0.05 * s)
            H.mpiece(f"Flip{tag}#", f"Fl{tag}#", inn, col="primary", tris=500, role="limb", pattern=countershade)
            H.mpiece(f"FlipT{tag}#", f"FlT{tag}#", out, col="primary", tris=550, role="limb", pattern=countershade)
            fl.append((f"Fl{tag}R", f"FlT{tag}R", 1))
            fl.append((f"Fl{tag}L", f"FlT{tag}L", -1))
        # long neck: 4 bones
        prev = "Body"
        npts = [_v((0, by + 0.05 * s, -1.35 * s))]
        for i in range(4):
            a = 0.25 + 0.06 * i
            npts.append(npts[-1] + _v((0, math.sin(a), -math.cos(a))) * 0.9 * s)
        necks = []
        for i in range(4):
            nm = f"Neck{i + 1}"
            H.bone(nm, prev, tuple(npts[i]))
            necks.append(nm)
            r0 = 0.42 * s - 0.07 * s * i
            r1 = 0.42 * s - 0.07 * s * (i + 1)
            st = 0.93 if i else 1.0
            sd = eloft([tuple(npts[i] - (npts[i + 1] - npts[i]) * (0.3 if i == 0 else 0.15)), tuple(npts[i + 1])], [r0 * st, r1], [r0 * 0.9 * st, r1 * 0.9])
            H.piece(f"NeckP{i + 1}", nm, sd, col="primary", tris=550, role="neck", pattern=countershade)
            prev = nm
        hc = npts[-1] + _v((0, 0.02 * s, -0.05 * s))
        H.bone("Head", prev, tuple(hc))
        h, HD, my = _skull(H, hc, 1.3 * s, "plesio", teeth=8, brow=0.03, eye_r=0.06, pupil="round", fenestra=False, tris=1200, jaw_tris=500,
                           pattern=countershade)
        tb = [_v((0, by, 1.35 * s))]
        for i in range(3):
            tb.append(tb[-1] + _v((0, -0.03 * s, 0.6 * s)))
        tails = []
        for i in range(3):
            H.bone(f"Tail{i + 1}", "Body" if i == 0 else f"Tail{i}", tuple(tb[i]))
            tails.append(f"Tail{i + 1}")
            r0, r1 = (0.32 - 0.1 * i) * s, (0.22 - 0.1 * i) * s if i < 2 else 0.03 * s
            st = 0.93 if i else 1.0
            H.piece(f"TailP{i + 1}", f"Tail{i + 1}", eloft([tuple(tb[i] - _v((0, 0, 0.15 * s))), tuple(tb[i + 1])], [r0 * st, r1], [r0 * 0.9 * st, r1 * 0.9]),
                    col="primary", tris=400, role="tail", pattern=countershade)
        H.socket("mouth", h(0, my, HD["z"][-1]), "Head")
        H.socket("head", h(0, 0.3, 0), "Head")
        H.rig.update({"head": "Head", "jaw": "Jaw", "neck": "Neck1", "tail": tails})
        MR.flipper(H, [f for f in fl if "FlF" in f[0]], [f for f in fl if "FlB" in f[0]], head="Head", neck=necks, jaw="Jaw", tail=tails,
                   walk=1.8, height=by + 0.6 * s, fl_amp=0.55)
        return H
    # mosasaur: long lizard body, paddle limbs, shark-like tail fluke
    spine = []
    pts = [_v((0, by, -1.6 * s)), _v((0, by, -0.3 * s)), _v((0, by, 1.0 * s))]
    H.bone("Hips", "Body", tuple(pts[2]))
    torso = eloft([(0, by, -2.3 * s), (0, by + 0.05 * s, -1.3 * s), (0, by + 0.05 * s, 0.0), (0, by, 1.0 * s)],
                  [0.45 * s, 0.7 * s, 0.68 * s, 0.5 * s], [0.5 * s, 0.75 * s, 0.72 * s, 0.55 * s], k=0.3 * s)
    H.piece("Torso", "Body", torso.noise(0.008 * s, 9 / s, 1), col="primary", tris=2200, res=128, pattern=countershade)
    hip = eloft([(0, by, 0.5 * s), (0, by, 1.4 * s), (0, by - 0.02 * s, 2.0 * s)], [0.48 * s, 0.42 * s, 0.32 * s], [0.53 * s, 0.46 * s, 0.36 * s], k=0.2 * s)
    H.piece("HipP", "Hips", hip, col="primary", tris=1000, pattern=countershade)
    tb = [_v((0, by - 0.02 * s, 1.95 * s))]
    for i in range(4):
        tb.append(tb[-1] + _v((0, -0.02 * s, 0.8 * s)))
    tails = []
    rad = [0.34, 0.27, 0.2, 0.13, 0.07]
    for i in range(4):
        H.bone(f"Tail{i + 1}", "Hips" if i == 0 else f"Tail{i}", tuple(tb[i]))
        tails.append(f"Tail{i + 1}")
        st = 0.93 if i else 1.0
        sd = eloft([tuple(tb[i] - _v((0, 0, 0.18 * s))), tuple(tb[i + 1])], [rad[i] * 0.8 * s * st, rad[i + 1] * 0.75 * s], [rad[i] * 1.1 * s * st, rad[i + 1] * 1.15 * s])
        if i == 3:  # downturned tail with a crescent fluke
            fl = eloft([tuple(tb[i] + _v((0, -0.05 * s, 0.3 * s))), tuple(tb[i + 1] + _v((0, -0.45 * s, 0.25 * s)))], [0.05 * s, 0.03 * s], [0.12 * s, 0.05 * s])
            fl = fl | eloft([tuple(tb[i] + _v((0, 0.0, 0.4 * s))), tuple(tb[i + 1] + _v((0, 0.6 * s, 0.45 * s)))], [0.05 * s, 0.02 * s], [0.15 * s, 0.06 * s])
            fl = fl.su(ellipsoid(0.045 * s, 0.55 * s, 0.3 * s, tuple(tb[i + 1] + _v((0, 0.05 * s, 0.15 * s)))), 0.1 * s)
            sd = sd.su(fl, 0.08 * s)
        H.piece(f"TailP{i + 1}", f"Tail{i + 1}", sd, col="primary", tris=max(400, 800 - 100 * i), role="tail", pattern=countershade)
    limbs = []
    for front in (True, False):
        tag = "F" if front else "B"
        sh = _v((0.5 * s, by - 0.3 * s, (-1.4 if front else 0.9) * s))
        tip = sh + _v((0.75 * s, -0.25 * s, 0.55 * s)) * (1.0 if front else 0.8)
        H.mbone(f"Pad{tag}#", "Body" if front else "Hips", tuple(sh))
        H.mpiece(f"Paddle{tag}#", f"Pad{tag}#", eloft([tuple(sh - _v((0.15 * s, 0, 0))), tuple(sh + (tip - sh) * 0.5), tuple(tip)],
                                                      [0.2 * s, 0.24 * s, 0.06 * s], [0.08 * s, 0.06 * s, 0.03 * s], k=0.05 * s),
                 col="primary", tris=500, role="limb", pattern=countershade)
        limbs += [(f"Pad{tag}R", 1), (f"Pad{tag}L", -1)]
    hc = _v((0, by + 0.08 * s, -2.25 * s))
    H.bone("Neck", "Body", (0, by, -1.9 * s))
    H.bone("Head", "Neck", tuple(hc))
    h, HD, my = _skull(H, hc, 1.4 * s, "mosa", teeth=12, brow=0.05, eye_r=0.06, pupil="round", fenestra=False, tris=1600, jaw_tris=800,
                       pattern=countershade)
    H.socket("mouth", h(0, my, HD["z"][-1]), "Head")
    H.socket("head", h(0, 0.4, 0), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "neck": "Neck", "tail": tails})
    MR.swimtail(H, ["Neck", "Hips"], tails, head="Head", jaw="Jaw", limbs=limbs, walk=1.6, height=by + 0.6 * s, amp=0.2)
    return H


@hero("plesiosaurus", FAM)
def plesiosaurus():
    return _marine("plesiosaurus", "plesio", preview={"primary": "#4A6A7A", "secondary": "#D8E0E4", "iris": "#2A2A2A"})


@hero("mosasaurus", FAM)
def mosasaurus():
    return _marine("mosasaurus", "mosa", preview={"primary": "#3A5A6A", "secondary": "#C8D0D8", "iris": "#C9A03A"})


# ==================================================================================================== more theropods
@hero("velociraptor", FAM)
def velociraptor():
    return _theropod("velociraptor", skull="raptor", hs=1.25, leg=0.62, legr=0.55, girth=0.48, body=0.55, neck=0.8, arms=1.25, fingers=3,
                     tail=0.85, tailr=0.75, teeth=10, brow=0.04, feathers=True, sickle=True, pattern="stripes", pat_depth=0.25, shade=0.75,
                     heavy=0.2, walk=0.8, stride=0.55, attack="slash", eye_r=0.085, mount=True,
                     preview={"primary": "#8A6A3A", "secondary": "#5A3A20", "iris": "#E8A030"})


@hero("raptor", FAM)
def raptor():
    return _theropod("raptor", s=2.2, mount_len=11.0, mount_gait=(4.6, 1.05, 11.0, 0.62), pad_col=[0.3, 0.2, 0.12], skull="raptor", hs=1.3, leg=0.68, legr=0.6, girth=0.52, body=0.6, neck=0.85, arms=1.15, fingers=3,
                     tail=0.9, tailr=0.8, teeth=10, brow=0.05, sickle=True, pattern="stripes", pat_depth=0.35, shade=0.7,
                     heavy=0.25, walk=0.8, stride=0.55, attack="bite", eye_r=0.085,
                     preview={"primary": "#6B8E23", "secondary": "#D2B48C", "iris": "#E8C030"})


@hero("allosaurus", FAM)
def allosaurus():
    return _theropod("allosaurus", skull="allo", hs=1.2, girth=0.92, body=1.0, arms=0.75, fingers=3, teeth=12, horns=0.1, brow=0.08,
                     pattern="stripes", pat_depth=0.3, heavy=0.7, walk=1.2, stride=0.45,
                     preview={"primary": "#8A6A3A", "secondary": "#E8B87A", "iris": "#E8A030"})


@hero("carnotaurus", FAM)
def carnotaurus():
    return _theropod("carnotaurus", skull="carno", hs=1.15, leg=1.08, girth=0.85, body=0.95, arms=0.3, fingers=2, teeth=10, horns=0.32,
                     brow=0.06, bumps=True, pattern="bands", pat_depth=0.2, heavy=0.6, walk=1.05, stride=0.5,
                     preview={"primary": "#B8401E", "secondary": "#3A2A1E", "iris": "#E8C030"})


@hero("spinosaurus", FAM)
def spinosaurus():
    return _theropod("spinosaurus", skull="spino", hs=1.3, leg=0.82, girth=0.95, body=1.15, neck=1.15, arms=0.95, fingers=3, teeth=14,
                     brow=0.05, sail=2.1, tail=1.15, paddle=True, pattern="bands", pat_depth=0.15, heavy=0.9, walk=1.35, stride=0.4,
                     preview={"primary": "#8A4A2A", "secondary": "#D8783A", "iris": "#E8C030"})


@hero("dilophosaurus", FAM)
def dilophosaurus():
    return _theropod("dilophosaurus", skull="allo", hs=1.05, leg=0.92, legr=0.85, girth=0.72, body=0.9, neck=1.1, arms=0.8, fingers=3,
                     teeth=10, crests=0.62, brow=0.03, pattern="spots", pat_depth=0.3, heavy=0.4, walk=1.0, stride=0.5,
                     preview={"primary": "#6A8A3A", "secondary": "#F2C82A", "iris": "#E8C030"})


@hero("pachycephalosaurus", FAM)
def pachycephalosaurus():
    return _theropod("pachycephalosaurus", skull="pachy", hs=1.35, leg=0.88, legr=0.9, girth=0.85, body=0.85, neck=0.75, arms=0.6, fingers=3,
                     teeth=0, beak=True, dome=True, brow=0.0, pattern="spots", pat_depth=0.2, heavy=0.6, walk=1.1, stride=0.45,
                     attack="headbutt", eye_r=0.07,
                     preview={"primary": "#6A5A4A", "secondary": "#D8B08A", "iris": "#C9A03A", "beak": "#3A3530"})


# word -> hero rules (tools/meshgen/heroes/map.py)
DN = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Plant", "Weather"]}
MAP = [
    ("tyrannosaurus rex", "tyrannosaurus rex, tyrannosaurus, tyrannosaur, t rex, trex, dinosaur, dinosaurs, dino, dinos, tarbosaurus, daspletosaurus, "
                          "gorgosaurus, albertosaurus, giganotosaurus, carcharodontosaurus, mapusaurus, nanotyrannus, qianzhousaurus, yutyrannus, "
                          "theropod", DN),
    ("velociraptor", "velociraptor, velociraptors, deinonychus, dromaeosaurus, utahraptor, dakotaraptor, microraptor, pyroraptor, austroraptor, "
                     "unenlagia, troodon, halszkaraptor, oviraptor, citipati, gigantoraptor, sinosauropteryx, dilong, therizinosaurus, "
                     "nothronychus, segnosaurus, alxasaurus, yi qi, shuvuuia, mononykus, archaeopteryx", DN),
    ("raptor", "raptor, raptors, compsognathus, gallimimus, ornithomimus, struthiomimus, deinocheirus, eoraptor, coelophysis", DN),
    ("allosaurus", "allosaurus, allosaurs, megalosaurus, torvosaurus, acrocanthosaurus, concavenator, herrerasaurus, sinraptor", DN),
    ("carnotaurus", "carnotaurus, majungasaurus, rajasaurus, abelisaurus, rugops, skorpiovenator, ceratosaurus", DN),
    ("spinosaurus", "spinosaurus, spino, baryonyx, suchomimus, irritator", DN),
    ("dilophosaurus", "dilophosaurus, cryolophosaurus, monolophosaurus, guanlong", DN),
    ("pachycephalosaurus", "pachycephalosaurus, pachy, stygimoloch, dracorex, bonehead", DN),
    ("triceratops", "triceratops, torosaurus, chasmosaurus, centrosaurus, pachyrhinosaurus, protoceratops, leptoceratops, psittacosaurus, "
                    "nasutoceratops, sinoceratops, zuniceratops, ceratopsian", DN),
    ("styracosaurus", "styracosaurus, kosmoceratops, regaliceratops, diabloceratops, einiosaurus", DN),
    ("stegosaurus", "stegosaurus, stego, kentrosaurus, huayangosaurus, tuojiangosaurus, miragaia", DN),
    ("ankylosaurus", "ankylosaurus, ankylo, ankylosaur, euoplocephalus, nodosaurus, edmontonia, borealopelta, gastonia, polacanthus, minmi, "
                     "scelidosaurus", DN),
    ("parasaurolophus", "parasaurolophus, parasaur, corythosaurus, lambeosaurus, olorotitan, hypacrosaurus, tsintaosaurus, saurolophus", DN),
    ("iguanodon", "iguanodon, hadrosaurus, hadrosaur, edmontosaurus, maiasaura, shantungosaurus, muttaburrasaurus, tenontosaurus, ouranosaurus, "
                  "dryosaurus, hypsilophodon, leaellynasaura, heterodontosaurus, plateosaurus, duckbill, duck billed dinosaur", DN),
    ("brachiosaurus", "brachiosaurus, brachio, giraffatitan, sauroposeidon, camarasaurus, europasaurus, argentinosaurus, patagotitan, "
                      "dreadnoughtus, saltasaurus, sauropod, longneck, long neck dinosaur", DN),
    ("diplodocus", "diplodocus, apatosaurus, brontosaurus, supersaurus, mamenchisaurus, dicraeosaurus, amargasaurus, nigersaurus, shunosaurus, "
                   "brachytrachelopan, thunder lizard", DN),
    ("pteranodon", "pteranodon, pteranodons, quetzalcoatlus, hatzegopteryx, ornithocheirus, anhanguera, tupandactylus, tapejara, nyctosaurus", DN),
    ("pterodactyl", "pterodactyl, pterodactyls, pterodactyl hatchling, pterosaur, pterosaurs, rhamphorhynchus, dimorphodon, pterodaustro", DN),
    ("plesiosaurus", "plesiosaurus, plesiosaur, elasmosaurus, nothosaurus, placodus, nessie, loch ness", DN),
    ("mosasaurus", "mosasaurus, mosasaur, tylosaurus, prognathodon", DN),
]
