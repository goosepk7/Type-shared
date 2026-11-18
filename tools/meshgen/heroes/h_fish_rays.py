"""Aquatic family: rays, eels and seahorses.

* manta ray / stingray: one flat disc sculpt (wing outline plate + body hump) cut into a body and two wing segments per
  side so a flap wave runs out to the wing tips; whip tail chain (stingray barb), manta cephalic fins.
* eel (moray): the fish builder with a long 8-segment spine and continuous ribbon fins for a travelling S-wave.
* seahorse: upright ringed trunk, horse head with tube snout and coronet, curled prehensile tail chain, fluttering
  dorsal and pectoral fins.

NOTE: the eel uses h_fish._fish: after changing that builder rebuild it with build.py --force --only eel.
"""
import math

import numpy as np

import sdf as S
from kit import Hero, spots, stripes, combine, gradient
from map import NOTFOOD
import motion_aquatic as MA
from motion_aquatic import plate, overlay, slab
from h_fish import _fish, _fins_std, pv, hero, FAM

TAU = 2 * math.pi


def segcut_axis(body, axis, a, b, ov, ck, delta):
    w = 0.5 * ov

    def f(Q):
        x = Q[:, axis]
        ramp = np.clip((a - x) / w, 0, 1) + np.clip((x - b) / w, 0, 1)
        return body(Q) + delta * ramp

    return S.SDF(f).si(slab(axis, a - ov, b + ov), ck)


# ================================================================================================ rays
def _ray(hid, prev, span=4.0, chord=3.0, outline=None, manta=False, tail_len=3.0, barb=False, pattern=None):
    H = Hero(hid, plan="Fish", gait="swim", tags=["fish", "ray"])
    H.preview = prev
    y0 = 1.2
    H.body((0, y0, 0))
    pts = [(x * span, z * chord) for x, z in outline]
    pts = pts + [(-x, z) for x, z in pts[::-1]]
    disc = plate((0, y0, 0), (1, 0, 0), (0, 0, 1), pts, 0.34, taper=0.18, edge=1.1)
    hump = S.ellipsoid(0.75, 0.32, 1.25 * chord / 3, (0, y0 + 0.05, 0.1))
    hump = hump.su(S.ellipsoid(0.5, 0.22, 0.6, (0, y0 + 0.02, -0.75 * chord / 3)), 0.3)
    body = disc.su(hump, 0.4)
    if not manta:  # stingray eye bumps
        body = body.su(S.sphere(0.12, (0.3, y0 + 0.2, -0.55)).mirror_x(), 0.12)
    # wing tips bend down a little
    xs = (0.0, 0.8, 0.6 * span, span * 1.1)
    ov, ck, dl = 0.18, 0.04, 0.02
    pat = combine(pattern, lambda Q: 1 - 0.18 * np.clip((Q[:, 1] - y0) / 0.2 + 0.5, 0, 1) * 0)
    H.piece("Torso", "Body", segcut_axis(body, 0, -xs[1], xs[1], ov, ck, dl), col="primary", tris=2400, res=128, role="body", pattern=pattern)
    H.mbone("WingA#", "Body", (xs[1], y0, 0.0))
    H.mbone("WingB#", "WingA#", (xs[2], y0, 0.2))
    H.mpiece("WingIn#", "WingA#", segcut_axis(body, 0, xs[1], xs[2], ov, ck, dl), col="primary", tris=1500, res=128, role="wing", pattern=pattern)
    H.mpiece("WingOut#", "WingB#", segcut_axis(body, 0, xs[2], xs[3], ov, ck, dl), col="primary", tris=1100, res=128, role="wing", pattern=pattern)
    # belly (pale underside, stands proud below)
    under = lambda Q: Q[:, 1] - (y0 - 0.06)
    H.piece("Belly", "Body", overlay(segcut_axis(body, 0, -xs[1], xs[1], ov, ck, dl), S.SDF(under), t=0.03), col="secondary", tris=900, role="pattern", pri=1.3)
    # eyes / head
    zf = min(z for x, z in pts)
    if manta:
        H.bone("Head", "Body", (0, y0, zf + 0.4))
        for sx in (1, -1):
            pass
        ceph = S.tube([(0.42, y0, zf + 0.5), (0.5, y0 - 0.05, zf - 0.1), (0.42, y0 - 0.2, zf - 0.45)], [0.14, 0.12, 0.06], k=0.05)
        ceph = ceph.scale3(1.0, 1.0, 1.0)
        H.mbone("Ceph#", "Head", (0.42, y0, zf + 0.45))
        H.mpiece("Cephalic#", "Ceph#", ceph, col="primary", tris=500, role="fin", pri=1.5)
        H.prim("Mouth", "Head", "Block", (0.62, 0.08, 0.1), (0, y0 - 0.06, zf + 0.04), col="mouth", mat="hard", role="mouth", pri=2.3)
        H.eyes("Head", (0.5, y0 + 0.02, zf + 0.5), 0.07, col="pupil", pupil=None, look=(1, 0, -0.3))
    else:
        H.bone("Head", "Body", (0, y0, zf + 0.4))
        H.eyes("Head", (0.3, y0 + 0.27, -0.55), 0.075, col="iris", pupil="round", look=(0.4, 1, -0.3))
        H.mprim("Spiracle#", "Head", "Ellipsoid", (0.1, 0.04, 0.16), (0.33, y0 + 0.21, -0.32), col="darker", mat="skin", role="detail", pri=2.2)
    # tail chain
    zt = max(z for x, z in pts) - 0.3
    seg = tail_len / 3
    names = ["Tail1", "Tail2", "Tail3"]
    prevb = "Body"
    for i, nm in enumerate(names):
        H.bone(nm, prevb, (0, y0 + 0.02, zt + i * seg))
        prevb = nm
    for i, nm in enumerate(names):
        a = (0, y0 + 0.02, zt + i * seg - (0.15 if i else 0.3))
        b = (0, y0 + 0.02, zt + (i + 1) * seg + 0.05)
        r0 = 0.14 * (1 - i / 3.4)
        sh = S.round_cone(a, b, r0, r0 * 0.7)
        if barb and i == 1:
            sh = sh.su(S.round_cone((0, y0 + 0.06, zt + i * seg + 0.2), (0, y0 + 0.14, zt + i * seg + 0.75), 0.05, 0.008), 0.03)
        if manta and i == 0:
            sh = sh.su(plate((0, 0, 0), (0, 0, 1), (0, 1, 0), [(zt - 0.4, y0 + 0.05), (zt - 0.1, y0 + 0.35), (zt + 0.15, y0 + 0.3), (zt + 0.3, y0)], 0.05), 0.04)
        H.piece(nm + "P", nm, sh, col="primary", tris=350 if i else 500, role="tail", pri=1.6, res=140)
    if barb:
        pass
    H.socket("mouth", (0, y0, zf - 0.05), "Head")
    H.socket("head", (0, y0 + 0.5, zf + 0.6), "Head")
    H.rig.update({"head": "Head", "tail": names, "swim": True})
    MA.ray_swim(H, [(["WingAR", "WingBR"], ["WingAL", "WingBL"])], tail=names, period=1.8 if manta else 1.2, amp=0.26, length=chord)
    return H


@hero("manta ray", FAM)
def manta():
    outline = [(0.0, -0.36), (0.12, -0.36), (0.35, -0.22), (0.7, -0.02), (1.0, 0.12), (0.92, 0.18), (0.6, 0.22), (0.3, 0.32), (0.14, 0.42), (0.0, 0.45)]
    return _ray("manta ray", pv("manta ray", pupil="#101014"), span=4.2, chord=3.0, outline=outline, manta=True, tail_len=2.2)


@hero("stingray", FAM)
def stingray():
    outline = [(0.0, -0.48), (0.2, -0.42), (0.55, -0.2), (0.9, 0.05), (1.0, 0.15), (0.85, 0.3), (0.5, 0.45), (0.2, 0.52), (0.0, 0.54)]
    return _ray("stingray", pv("stingray", iris="#C8B060"), span=2.4, chord=3.2, outline=outline, tail_len=3.6, barb=True,
                pattern=spots(0.35, 0.09, depth=0.3, seed=4))


# ================================================================================================ eel
@hero("eel", FAM)
def eel():
    prof = [(0, 0.008, -0.014, 0.011), (0.025, 0.028, -0.027, 0.024), (0.06, 0.04, -0.038, 0.032), (0.12, 0.042, -0.04, 0.033), (0.5, 0.037, -0.034, 0.028),
            (0.8, 0.027, -0.024, 0.02), (0.95, 0.014, -0.012, 0.009), (1.0, 0.009, -0.008, 0.006)]

    def ribbon(b, pr):
        L = pr.L
        top, bot = [], []
        for t in np.linspace(0.18, 1.04, 14):
            tp, bt, w, c, a = pr.at(t)
            h = 0.026 * math.sin(math.pi * min(1, (t - 0.16) / 0.3)) ** 0.5
            top.append((pr.z(t), tp + h * L))
        for t in np.linspace(1.04, 0.45, 10):
            tp, bt, w, c, a = pr.at(t)
            h = 0.02 * math.sin(math.pi * min(1, (t - 0.43) / 0.25)) ** 0.5
            bot.append((pr.z(t), bt - h * L))
        fin = plate((0, 0, 0), (0, 0, 1), (0, 1, 0), top + bot + [(pr.z(0.45), pr.at(0.45)[3]), (pr.z(0.18), pr.at(0.18)[3])], 0.012 * L, taper=0.35, edge=0.03 * L)
        return b.su(fin, 0.008 * L)

    seg = (0.13, 0.24, 0.36, 0.48, 0.6, 0.72, 0.84, 0.93)
    return _fish("eel", prof=prof, L=12.0, lift=0.5, sculpt=ribbon, seg=seg, mouth=(0.0, 0, 0.1, -0.02, 0.5), eye=(0.045, 40, 0.009), teeth=6, teeth_t0=0.02,
                 tooth_len=0.012, fins=(), caudal=None, gill=0.11, scales=0.0, back=0.75, fin_th=0.01,
                 pattern=lambda pr, L: spots(0.03 * L, 0.011 * L, depth=0.45, seed=31),
                 pecs=dict(t=0.12, ang=-10, len=0.03, wid=0.025, splay=50, droop=10, roll=-30), pelvic=None, amp=0.3, period=1.3,
                 tags=("fish", "eel"), preview=pv("eel", iris="#D8C040"))


# ================================================================================================ seahorse
@hero("seahorse", FAM)
def seahorse():
    H = Hero("seahorse", plan="Fish", gait="swim", tags=["fish", "seahorse"])
    H.preview = pv("seahorse", iris="#2A2A2A")
    H.body((0, 2.6, 0))
    rings = stripes(lambda Q: Q[:, 1] + 0.3 * Q[:, 2], 4.0, width=0.2, depth=0.38)
    bumps = spots(0.25, 0.05, depth=0.25, seed=2)
    pat = combine(rings, bumps, gradient(2, -1.0, 0.8, 1.0, 0.85))
    # trunk: belly bulges forward, ridged back, slim neck
    tr = S.tube([(0, 1.85, 0.2), (0, 2.35, -0.1), (0, 2.95, -0.1), (0, 3.45, 0.12), (0, 3.85, 0.32)], [0.36, 0.48, 0.46, 0.34, 0.26], k=0.25)
    tr = tr.su(S.ellipsoid(0.36, 0.55, 0.36, (0, 2.5, -0.3)), 0.25)  # belly
    ridge = S.tube([(0, 1.9, 0.55), (0, 2.6, 0.45), (0, 3.4, 0.45), (0, 3.85, 0.55)], [0.07, 0.09, 0.07, 0.05], k=0.1)
    tr = tr.su(ridge, 0.15)
    knobs = [S.sphere(0.06, (0.3 * math.cos(a), y, 0.3 * math.sin(a) + 0.05)) for y in np.linspace(2.0, 3.6, 7) for a in (0.6, 2.3)]
    tr = tr.su(MA.union_all(knobs).mirror_x(), 0.05)
    H.piece("Torso", "Body", tr, col="primary", tris=2400, res=128, role="body", pattern=pat)
    # head: bent forward at the neck, tube snout, coronet
    H.bone("Head", "Body", (0, 3.85, 0.32))
    hd = S.ellipsoid(0.3, 0.38, 0.42, (0, 4.2, 0.2))
    hd = hd.su(S.tube([(0, 4.15, -0.05), (0, 4.02, -0.6), (0, 3.95, -0.95)], [0.18, 0.11, 0.11], k=0.08), 0.12)  # tube snout
    hd = hd.su(S.ellipsoid(0.13, 0.07, 0.05, (0, 3.95, -0.98)), 0.04)
    hd = hd.su(S.tube([(0, 4.45, 0.35), (0, 4.8, 0.42), (0, 4.9, 0.35)], [0.14, 0.11, 0.06], k=0.06), 0.08)  # coronet
    hd = hd.su(MA.union_all([S.round_cone((0, 4.8, 0.42), (0.11 * math.cos(a), 5.0, 0.42 + 0.11 * math.sin(a)), 0.045, 0.02) for a in np.linspace(0, TAU, 6)[:-1]]), 0.03)
    hd = hd.su(S.ellipsoid(0.2, 0.22, 0.2, (0.13, 4.12, 0.1)).mirror_x(), 0.1)  # cheeks
    hd = hd.su(S.round_cone((0, 3.9, 0.5), (0, 4.35, 0.62), 0.11, 0.05), 0.1)  # nape spine
    H.piece("HeadP", "Head", hd, col="primary", tris=2000, res=136, role="head", pattern=pat)
    H.prim("Mouth", "Head", "Ellipsoid", (0.12, 0.06, 0.04), (0, 3.95, -1.02), col="mouth", mat="hard", role="mouth", pri=2.4)
    H.eyes("Head", (0.24, 4.25, 0.02), 0.11, col="iris", pupil="round", look=(1, 0.1, -0.5))
    # dorsal fin (flutters)
    H.bone("Dorsal", "Body", (0, 2.3, 0.5))
    d = plate((0, 0, 0), (0, 1, 0), (0, 0, 1), [(1.95, 0.42), (2.75, 0.42), (2.7, 0.95), (2.35, 1.1), (1.95, 0.95)], 0.05, taper=0.4, edge=0.1)
    H.piece("DorsalP", "Dorsal", d, col="secondary", tris=400, role="fin", tr=0.15, pattern=MA.par_lines((0, 1, 0), 9, 0.3), pri=1.6)
    H.mbone("Pec#", "Head", (0.24, 3.9, 0.4))
    pf = plate((0.24, 3.9, 0.38), (0.6, 0.0, 0.6), (0, 1, 0), [(0, -0.15), (0.35, -0.24), (0.48, 0.0), (0.35, 0.24), (0, 0.15)], 0.04, taper=0.4, edge=0.08)
    H.mpiece("PecP#", "Pec#", pf, col="secondary", tris=300, role="fin", tr=0.15, pri=1.6)
    # tail: down from the belly then curling forward under itself
    pts = [(0, 1.9, 0.2), (0, 1.3, 0.38), (0, 0.78, 0.42), (0, 0.38, 0.28), (0, 0.24, -0.05), (0, 0.38, -0.32), (0, 0.65, -0.28), (0, 0.72, -0.05)]
    bones = ["Tail1", "Tail2", "Tail3", "Tail4"]
    rad = [0.32, 0.22, 0.16, 0.12, 0.1, 0.08, 0.06, 0.045]
    prevb = "Body"
    for i, b in enumerate(bones):
        H.bone(b, prevb, pts[i])
        prevb = b
    ranges = [(0, 1), (1, 2), (2, 3), (3, 7)]
    for i, (a, c) in enumerate(ranges):
        p = pts[a:c + 1]
        r = list(rad[a:c + 1])
        if i < 3:
            r[-1] *= 1.07
        sh = S.tube(p, r, k=0.04)
        H.piece(f"TailP{i + 1}", bones[i], sh, col="primary", tris=500 if i < 3 else 800, role="tail", pri=1.5, pattern=pat, res=128)

    H.socket("mouth", (0, 3.95, -1.05), "Head")
    H.socket("head", (0, 5.0, 0.2), "Head")
    H.rig.update({"head": "Head", "tail": bones, "swim": True})

    def pose_common(pose, u, k):
        MA._add(pose, "Dorsal", (0, 0, 0, 0, 0.35 * math.sin(TAU * u * 6), 0))
        MA._add(pose, "PecR", (0, 0, 0, 0, 0.4 * math.sin(TAU * u * 6 + 1), 0))
        MA._add(pose, "PecL", (0, 0, 0, 0, -0.4 * math.sin(TAU * u * 6 + 1), 0))
        for i, b in enumerate(bones):
            MA._add(pose, b, (0, 0, 0, k * 0.12 * math.sin(TAU * u - i * 0.8), k * 0.06 * math.sin(TAU * u * 0.5 - i), 0))

    def move(t):
        u = t / 1.6
        pose = {}
        pose_common(pose, u, 1.0)
        MA._add(pose, "Body", (0, 0.25 * math.sin(TAU * u), 0, -0.12 + 0.05 * math.sin(TAU * u + 1), 0, 0.03 * math.sin(TAU * u)))
        MA._add(pose, "Head", (0, 0, 0, 0.06 * math.sin(TAU * u + 2), 0, 0))
        return pose

    def idle(t):
        u = t / 3.2
        pose = {}
        pose_common(pose, u, 0.6)
        MA._add(pose, "Body", (0, 0.12 * math.sin(TAU * u), 0, 0.03 * math.sin(TAU * u), 0.15 * math.sin(TAU * u * 0.5), 0))
        MA._add(pose, "Head", (0, 0, 0, 0.05 * math.sin(TAU * u * 2), 0.15 * math.sin(TAU * u), 0))
        return pose

    def attack(t):
        s = t / 0.7
        pose = {}
        wind = MA._env(s, 0.0, 0.5)
        st = MA._env(s, 0.35, 0.75)
        MA._add(pose, "Head", (0, 0, 0, 0.45 * wind - 0.6 * st, 0, 0))  # pivot-feeding snap
        MA._add(pose, "Body", (0, 0, -0.5 * st, 0.1 * wind - 0.2 * st, 0, 0))
        for i, b in enumerate(bones):
            MA._add(pose, b, (0, 0, 0, 0.25 * wind, 0, 0))
        pose_common(pose, s, 0.4)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        MA._add(pose, "Body", (0, 0, 0.3 * k, 0.25 * k, 0, 0.15 * k * math.sin(s * 9)))
        MA._add(pose, "Head", (0, 0, 0, 0.3 * k, 0, 0))
        for b in bones:
            MA._add(pose, b, (0, 0, 0, -0.2 * k, 0, 0))
        return pose

    H.clip("Move", 1.6, move, keys=20)
    H.clip("Idle", 3.2, idle, keys=20)
    H.clip("Attack", 0.7, attack, keys=14, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    return H


MAP = [
    ("manta ray", "manta, manta ray, mobula ray, devil ray, eagle ray, bat ray, cownose ray", NOTFOOD),
    ("stingray", "stingray, sting ray, stingrays, ray, rays, skate, electric ray, freshwater stingray, guitarfish, sawfish, angel shark, "
                 "wobbegong, !x ray, !x-ray, !death ray, !ray gun, !manta, !sun ray, !heat ray, !freeze ray", {"cat": ["Creature"]}),
    ("eel", "eel, eels, moray, moray eel, electric eel, garden eel, ribbon eel, gulper eel, conger, lamprey, hagfish, oarfish, "
            "snakehead, bichir, lungfish, burbot, amphiuma, black dragonfish, wolf eel, basilosaurus", {"cat": ["Creature"]}),
    ("seahorse", "seahorse, sea horse, seahorses, leafy sea dragon, pipefish, ghost pipefish, shrimpfish, !hippocampus", {"cat": ["Creature"]}),
]
