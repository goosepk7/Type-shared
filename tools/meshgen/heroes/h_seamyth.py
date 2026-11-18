"""Sea myths, marine reptiles and serpent folk (family "seamyth").

  kraken            giant squid: tall finned mantle, big-eyed head, eight sucker arms sprawled in a writhing crawl and two
                    long feeding tentacles with sucker clubs that rear up and slam down.
  tentacle monster  a squat bulb of a beast standing on curling tentacles, one huge eye, a lamprey ring mouth and
                    a crown of whipping feelers.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF
from kit import Hero, hero, stripes, spots, gradient, combine
from map import NOTFOOD
from mon_geo import plate
import motion
import motion_seamyth as MS

FAM = "seamyth"


def V(*x):
    return np.array(x, float)


def T(a):
    return tuple(float(x) for x in a)


def unit(a):
    a = np.asarray(a, float)
    return a / np.linalg.norm(a)


def catmull(ctrl, n):
    """Uniform Catmull-Rom through the control points, n samples (end points included)."""
    P = [np.asarray(c, float) for c in ctrl]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    segs = len(P) - 3
    out = []
    for k in range(n):
        u = k / (n - 1) * segs
        i = min(int(u), segs - 1)
        t = u - i
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return out


def taper(n, r0, r1, pw=1.0):
    return [r0 + (r1 - r0) * (i / (n - 1)) ** pw for i in range(n)]


def suckers(pts, radii, lat, every=1, size=0.32, start=0, dimple=True):
    """Cupped sucker bumps along a chain on the side n = lat x tangent."""
    s = None
    for i in range(start, len(pts) - 1, every):
        a, b = pts[i], pts[i + 1]
        t = unit(b - a)
        n = unit(np.cross(lat, t))
        c = (a + b) / 2
        r = (radii[i] + radii[i + 1]) / 2
        for side in ((-0.42, 0.42) if r > 0.12 else (0.0,)):
            cc = c + n * r * 0.82 + unit(np.cross(t, n)) * side * r
            one = sphere(r * size, T(cc))
            if dimple:
                one = one.ss(sphere(r * size * 0.55, T(cc + n * r * size * 0.75)), r * 0.05)
            s = one if s is None else s | one
    return s


def chain(H, name, parent, pts, radii, nseg, col="primary", mat="skin", tris=600, mirror=False, extra=None, pattern=None,
          role="tail", pri=1.5, shrink=0.93, k=0.0, tri_scale=None):
    """Split a dense tube (pts, radii) into nseg rigid segments on a bone chain. Each segment's root ball sits a
    little inside the previous segment's end ball (no coincident surfaces). extra(i, sub_pts, sub_radii) -> SDF or None
    is unioned into segment i. With mirror, `name` has "#" and the left copy is added. Returns the bone list
    (right side names when mirrored)."""
    N = len(pts)
    cuts = [int(round(i * (N - 1) / nseg)) for i in range(nseg + 1)]
    bones = []
    for i in range(nseg):
        bn = f"{name}{i + 1}"
        par = parent if i == 0 else bones[-1]
        if mirror:
            H.mbone(bn, par, T(pts[cuts[i]]))
            bones.append(bn)
        else:
            H.bone(bn, par, T(pts[cuts[i]]))
            bones.append(bn)
    for i in range(nseg):
        a, b = cuts[i], cuts[i + 1]
        sub = pts[a:b + 1]
        rr = list(radii[a:b + 1])
        if i > 0:
            rr[0] *= shrink
        step = max(1, (len(sub) - 1) // 6)
        idx = list(range(0, len(sub) - 1, step)) + [len(sub) - 1]
        sd = tube([T(sub[j]) for j in idx], [rr[j] for j in idx], k=k)
        if extra is not None:
            e = extra(i, sub, rr)
            if e is not None:
                sd = sd.su(e, min(rr) * 0.25)
        tr = tris if tri_scale is None else int(tris * tri_scale[i])
        pn = f"{name}P{i + 1}"
        if mirror:
            H.mpiece(pn, bones[i], sd, col=col, mat=mat, tris=tr, role=role, pri=pri + 0.05 * i, pattern=pattern)
        else:
            H.piece(pn, bones[i], sd, col=col, mat=mat, tris=tr, role=role, pri=pri + 0.05 * i, pattern=pattern)
    return bones


def rbones(bones):
    return [b.replace("#", "R") for b in bones]


def lbones(bones):
    return [b.replace("#", "L") for b in bones]


def mottle(cells, r, depth=0.25, seed=1):
    return spots(cells, r, depth=depth, seed=seed)


def topshade(y0, y1, a=1.0, b=0.72):
    return gradient(1, y0, y1, a, b)


# ================================================================================================ kraken
def _kraken(hid, s=1.0, mantle_len=1.0, eye=1.0, arm_len=1.0, preview=None):
    H = Hero(hid, plan="Octopus", gait="slither", tags=["kraken", "cephalopod", "sea monster"])
    H.preview = preview or {}
    C = V(0, 1.0, -0.45) * s          # arm crown (mouth ring)
    H.body(T(V(0, 1.45, 0) * s))
    H.bone("Head", "Body", T(V(0, 1.6, 0.1) * s))
    ML = mantle_len
    m0 = V(0, 1.95, 0.75) * s
    H.bone("Mantle", "Head", T(m0))
    H.bone("MantleTip", "Mantle", T(V(0, 1.95 + 1.6 * ML, 0.75 + 1.45 * ML) * s))
    pat = combine(mottle(0.32 * s, 0.09 * s, 0.22, 3), topshade(0.4 * s, 3.5 * s, 1.0, 0.8))

    # ------------------------------------------------------------------ mantle: a long tapered cone rising up-back
    ax = unit(V(0, 1.6, 1.45))
    mp = [m0 - ax * 0.55 * s, m0 + ax * 0.6 * s * ML, m0 + ax * 1.5 * s * ML]
    mr = [1.0 * s, 1.2 * s, 1.05 * s]
    mant = tube([T(p) for p in mp], mr, k=0.3 * s)
    mant = mant.su(ellipsoid(0.95 * s, 0.75 * s, 0.9 * s, T(m0 + V(0, -0.2, -0.25) * s)), 0.3 * s)      # collar
    mant = mant.ss(torus(0.95 * s, 0.05 * s, axis=1).rot(-48, 0, 0).at(*T(m0 + ax * 0.05 * s)), 0.04 * s)  # mantle rim groove
    H.piece("MantleP", "Mantle", mant, col="primary", tris=2200, res=128, pattern=pat)
    tip0 = m0 + ax * 1.35 * s * ML
    tipE = m0 + ax * 3.05 * s * ML
    tipm = tube([T(tip0), T(m0 + ax * 2.3 * s * ML), T(tipE)], [1.0 * s, 0.68 * s, 0.1 * s], k=0.2 * s)
    # arrow-head fins
    side = V(1, 0, 0)
    fin = plate([(0.0, -1.1), (1.55, 0.25), (1.2, 0.75), (0.0, 1.35), (-1.2, 0.75), (-1.55, 0.25)],
                T(m0 + ax * 2.45 * s * ML), (1, 0, 0), T(ax), 0.07 * s, bulge=0.0)
    fin = fin.scale(1.0)
    tipm = tipm.su(fin, 0.18 * s)
    H.piece("FinsP", "MantleTip", tipm, col="primary", tris=1600, res=120, pattern=pat)

    # ------------------------------------------------------------------ head, siphon, beak
    hc = V(0, 1.45, 0.05) * s
    head = ellipsoid(1.05 * s, 0.85 * s, 1.0 * s, T(hc))
    head = head.su(ellipsoid(0.45 * s, 0.42 * s, 0.42 * s, T(hc + V(0.72, 0.15, -0.1) * s)).mirror_x(), 0.3 * s)   # eye bulges
    head = head.su(ellipsoid(0.75 * s, 0.5 * s, 0.6 * s, T(C + V(0, 0.15, 0.1) * s)), 0.35 * s)                      # arm crown
    head = head.su(round_cone(T(hc + V(0, -0.45, 0.6) * s), T(hc + V(0, -0.75, 0.95) * s), 0.25 * s, 0.18 * s), 0.15 * s)  # siphon
    head = head.ss(sphere(0.12 * s, T(hc + V(0, -0.8, 1.02) * s)), 0.04 * s)
    head = head.ss(sphere(0.36 * eye * s, T(hc + V(0.86, 0.18, -0.12) * s)).mirror_x(), 0.07 * s)                  # eye sockets
    head = head.su(torus(0.38 * eye * s, 0.06 * s, axis=0).at(*T(hc + V(0.88, 0.18, -0.12) * s)).mirror_x(), 0.05 * s)  # lids
    head = head.ss(sphere(0.3 * s, T(C + V(0, -0.15, -0.35) * s)), 0.12 * s)                                          # mouth pit
    H.piece("HeadP", "Head", head, col="primary", tris=2000, res=128, pattern=pat)
    beak = round_cone(T(C + V(0, 0.0, -0.32) * s), T(C + V(0, -0.22, -0.55) * s), 0.16 * s, 0.035 * s)
    beak = beak | round_cone(T(C + V(0, -0.2, -0.3) * s), T(C + V(0, -0.2, -0.5) * s), 0.12 * s, 0.03 * s)
    H.piece("Beak", "Head", beak, col="darker", mat="hard", tris=260, role="tooth", pri=2.2)
    H.eyes("Head", T(hc + V(0.86, 0.18, -0.12) * s), 0.34 * eye * s, col="iris", pupil="slit", look=(1.0, 0.0, -0.45))

    # ------------------------------------------------------------------ eight arms
    AL = arm_len
    arms = []
    angs = (28, 68, 112, 150)
    for j, a in enumerate(angs):
        th = math.radians(a)
        d = V(math.sin(th), 0, -math.cos(th))
        lat = unit(np.cross(V(0, 1, 0), d))
        ln = AL * (1.0 - 0.08 * j) * s
        wob = 0.35 * (1 if j % 2 else -1) * s
        ctrl = [C + d * 0.35 * s + V(0, -0.05, 0) * s,
                C + d * 1.0 * s + V(0, -0.55, 0) * s + lat * wob * 0.3,
                C + d * 2.0 * ln + V(0, -0.72, 0) * s - lat * wob * 0.6,
                C + d * 3.0 * ln + V(0, -0.72, 0) * s + lat * wob,
                C + d * 3.7 * ln + V(0, -0.4, 0) * s + lat * wob * 0.6,
                C + d * 3.75 * ln + V(0, 0.25, 0) * s - lat * wob * 0.4,
                C + d * 3.35 * ln + V(0, 0.45, 0) * s - lat * wob * 0.6]
        pts = catmull(ctrl, 30)
        rad = taper(30, 0.34 * s, 0.045 * s, 0.85)
        ex = (lambda i, sub, rr, lat=lat: suckers(sub, rr, lat, every=1, size=0.32, start=1 if i == 0 else 0))
        bones = chain(H, f"Arm{j}#_", "Body", pts, rad, 2, col="primary", tris=650, mirror=True, extra=ex, pattern=pat,
                      role="limb", pri=1.4 + 0.1 * j)
        arms.append(([b.replace("#", "R") for b in bones], (d[0], d[2])))
        arms.append(([b.replace("#", "L") for b in bones], (-d[0], d[2])))

    # ------------------------------------------------------------------ two feeding tentacles with clubs
    th = math.radians(10)
    d = V(math.sin(th), 0, -math.cos(th))
    lat = unit(np.cross(V(0, 1, 0), d))
    ctrl = [C + d * 0.3 * s + V(0.12, 0.05, 0) * s, C + d * 1.1 * s + V(0, 0.9, 0) * s, C + d * 1.6 * s + V(0, 2.4, 0) * s,
            C + d * 2.6 * s + V(0, 3.2, 0) * s + lat * 0.3 * s, C + d * 3.6 * s + V(0, 2.8, 0) * s, C + d * 4.0 * s + V(0, 2.0, 0) * s]
    pts = catmull(ctrl, 36)
    rad = taper(36, 0.2 * s, 0.11 * s, 1.0)
    for i in range(26, 36):  # club
        rad[i] = 0.11 * s + 0.12 * s * math.sin(math.pi * (i - 26) / 9.5) ** 0.7
    rad[-1] = 0.05 * s

    def club(i, sub, rr):
        if i != 2:
            return None
        return suckers(sub, rr, -lat, every=1, size=0.36, start=max(0, len(sub) - 11))

    fb = chain(H, "Feed#_", "Body", pts, rad, 3, col="primary", tris=550, mirror=True, extra=club, pattern=pat, role="limb", pri=1.3)
    slam = [([b.replace("#", "R") for b in fb], (d[0], d[2])), ([b.replace("#", "L") for b in fb], (-d[0], d[2]))]

    H.socket("mouth", T(C + V(0, -0.2, -0.6) * s), "Head")
    H.socket("head", T(V(0, 3.2, 1.6) * s), "Mantle")
    H.rig.update({"head": "Head", "tail": ["Mantle", "MantleTip"]})
    MS.writhe(H, arms, slammers=slam, head="Head", mantle=["Mantle", "MantleTip"], height=3.0 * s, walk=1.8)
    return H


@hero("kraken", FAM)
def kraken():
    return _kraken("kraken", preview={"primary": "#8E2F3A", "secondary": "#E9B9A8", "iris": "#E8C23A", "darker": "#1E1416"})



# ================================================================================================ serpent folk
import h_monsters as HM  # noqa: E402


def _tail_ctrl(style, wy, s):
    """Tail centre line from the waist (y = wy) down to the ground and away; returns control points."""
    if style == "coil":   # a full ring of coil around and under the torso, tip flicking out front-left
        pts = [V(0, wy - 0.05, 0.05), V(0, wy - 0.9, 0.12), V(0, 1.0, 0.35)]
        R0, c = 1.05, V(0, 0, 0.25)
        for k in range(10):
            ph = math.pi * (1.0 + 1.75 * k / 9)          # start behind, sweep round the right side to the front
            R = R0 + 0.32 * k / 9
            pts.append(c + V(R * math.sin(ph) * -1, 0.0, -R * math.cos(ph)))
        pts.append(pts[-1] + V(-0.45, 0.0, -0.55))
        return pts
    if style == "fish":   # mermaid-like: curls down and back to a fluke held off the ground
        return [V(0, wy - 0.05, 0.05), V(0, wy - 0.8, 0.12), V(0, wy - 1.55, 0.45), V(0, wy - 2.05, 1.05), V(0, wy - 2.15, 1.75),
                V(0, wy - 1.95, 2.35)]
    if style == "long":   # long lazy S (melusine)
        return [V(0, wy - 0.05, 0.05), V(0, wy - 0.8, 0.2), V(0, 1.05, 0.75), V(0.35, 0.0, 1.55), V(1.3, 0.0, 2.3), V(1.0, 0.0, 3.3),
                V(-0.4, 0.0, 3.8), V(-1.4, 0.0, 4.6), V(-1.0, 0.0, 5.6), V(0.0, 0.1, 6.1)]
    # S on the ground
    return [V(0, wy - 0.05, 0.05), V(0, wy - 0.8, 0.2), V(0, 1.05, 0.75), V(0.35, 0.0, 1.5), V(1.25, 0.0, 2.15), V(0.95, 0.0, 3.05),
            V(-0.3, 0.0, 3.45), V(-1.25, 0.0, 4.1), V(-1.0, 0.0, 4.9), V(-0.2, 0.0, 5.2)]


def _serpfolk(hid, tail="s", hair="long", crest=None, tail_pat=None, fins=False, wings=False, crown=False, hood=False,
              snakehair=False, python=False, fluke=False, beak=False, tri=False, cap=None, top="scale", claws=False,
              iris=None, gait="slither", plan="Serpent", s=1.0, tail_r=0.46, nseg=5, tags=(), preview=None, attack="claw",
              torso=0.95, W=0.85, muscle=0.25, jewelry=False, flowers=False):
    swim = tail in ("fish", "tri")
    face = dict(nose="human", ns=0.75, ears="fin" if fins else "human", brow=0.15, jaw=False, eye=1.1,
                iris=iris or "iris", cheek=0.3)
    if beak:
        face.update(nose="none", jaw=False)
    if face["ears"] == "fin":
        face["ears"] = "elf"
    P = HM._P(s=s, torso=torso, W=W, arm=0.95, armT=0.8, head=1.05, muscle=muscle, skin="skin", hands="open", gait=gait,
              nolegs=True, nopelvis=True, upper_off=(0, -0.45, 0.0), body_at=(0, 2.2, 0.0), claws=claws, face=face,
              preview=preview or {})
    H, C = HM._rig(hid, P, plan=plan)
    H.tags = ["serpentfolk"] + list(tags)
    rib, _ = HM._torso(H, C, P)
    HM._arms(H, C, P)
    head, jaw, h, F = HM._head_human(H, C, P)
    hc, hs = C["hc"], C["hs"]

    def hh(x, y, z):
        return T(hc + V(x, y, z) * hs)

    if beak:  # amabie: a short bird beak instead of nose and mouth
        bk = round_cone(hh(0, -0.08, -0.38), hh(0, -0.2, -0.78), 0.13 * hs, 0.02 * hs)
        bk = bk.su(round_cone(hh(0, -0.2, -0.36), hh(0, -0.26, -0.62), 0.09 * hs, 0.02 * hs), 0.02 * hs)
        H.piece("Beak", "Head", bk, col="beak", mat="hard", tris=300, role="beak", pri=1.6)
    HM._place_head(H, C, P, head, jaw, h, F)
    wa, ch = C["waist"], C["chest"]
    wy = float(wa[1])

    # ------------------------------------------------------------------ hair / headdress
    hairb = []
    if snakehair:
        cap_ = ellipsoid(0.44 * hs, 0.44 * hs, 0.5 * hs, hh(0, 0.14, 0.08)).ss(ellipsoid(0.38 * hs, 0.45 * hs, 0.5 * hs, hh(0, -0.08, -0.22)), 0.06)
        sn = cap_
        heads = []
        for i in range(9):
            a = -2.4 + i * 0.6
            base = V(0.4 * math.sin(a), 0.38 + 0.12 * math.cos(a), 0.12 + 0.35 * math.cos(a) * 0.0 + 0.3 * (abs(a) / 2.4))
            out = V(math.sin(a), 0.6 + 0.5 * math.cos(a) * 0.4, 0.55 + 0.2 * math.cos(a * 1.7))
            out = out / np.linalg.norm(out)
            p0 = hc + base * hs
            p1 = p0 + out * 0.45 * hs + V(0, 0.25, 0) * hs
            p2 = p1 + out * 0.35 * hs + V(0.12 * math.sin(i * 1.9), -0.05, -0.15) * hs
            p3 = p2 + V(0, 0.12, -0.2) * hs
            sn = sn.su(tube([T(p0), T(p1), T(p2), T(p3)], [0.08 * hs, 0.065 * hs, 0.055 * hs, 0.05 * hs], k=0.03 * hs), 0.04 * hs)
            sn = sn.su(ellipsoid(0.075 * hs, 0.06 * hs, 0.11 * hs, T(p3 + V(0, 0.01, -0.07) * hs)), 0.03 * hs)
        H.piece("SnakeHair", "Head", sn, col="secondary", mat="skin", tris=2400, res=144, role="hair", pri=1.2,
                pattern=stripes(lambda Q: Q[:, 1] * 3 + Q[:, 2] * 2, 4.0, width=0.3, depth=0.35))
    elif hair:
        HM._hair(H, C, hair, col="hair")
    if hair == "long" and not snakehair:
        H.bone("Hair1", "Head", hh(0, 0.1, 0.4))
        lock = tube([hh(0, 0.15, 0.42), hh(0, -0.5, 0.75), hh(0, -1.35, 0.9), hh(0, -2.05, 1.15)],
                    [0.34 * hs, 0.31 * hs, 0.25 * hs, 0.07 * hs], k=0.1).noise(0.018 * s, 13 / s, 3)
        H.piece("HairFlow", "Hair1", lock, col="hair", mat="cloth", tris=900, role="hair", pri=1.3)
        hairb.append("Hair1")
    if crest == "fan":     # lamia: a swept fan crest of spines webbed with skin, like a frilled serpent
        cr = None
        for i in range(7):
            a = -0.5 + i * 0.27
            p0 = V(0, 0.42, 0.1 + 0.05 * i)
            p1 = p0 + V(0, math.cos(a) * 0.62, 0.15 + math.sin(a) * 0.62)
            one = round_cone(hh(*p0), hh(*p1), 0.05 * hs, 0.018 * hs)
            cr = one if cr is None else cr | one
        web = plate([(-0.2, 0.0), (0.0, 0.7), (0.35, 0.78), (0.65, 0.62), (0.8, 0.3), (0.62, 0.0)], hh(0, 0.42, 0.0), (0, 0, 1), (0, 1, 0), 0.018 * hs)
        H.piece("Crest", "Head", cr.su(web, 0.02 * hs), col="secondary", mat="skin", tris=800, role="crest", pri=1.3)
    if crown:
        HM._hat(H, C, "crown")
    if cap == "merrow":   # merrow: the red feathered cap (cohuleen druith)
        cp = ellipsoid(0.42 * hs, 0.3 * hs, 0.47 * hs, hh(0, 0.32, 0.08)) & plane((0, -1, 0), -(hc[1] + 0.2 * hs))
        cp = cp.su(round_cone(hh(0, 0.5, 0.15), hh(0, 0.82, 0.55), 0.24 * hs, 0.04 * hs), 0.12 * hs)
        cp = cp.su(torus(0.43 * hs, 0.05 * hs).scale3(1, 1, 1.1).at(*hh(0, 0.22, 0.07)), 0.04 * hs)
        for i in range(5):  # feather tufts
            cp = cp.su(round_cone(hh(0.12 * (i - 2), 0.55, 0.2), hh(0.18 * (i - 2), 0.9, 0.42), 0.05 * hs, 0.012 * hs), 0.03 * hs)
        H.piece("Cap", "Head", cp, col="red", mat="cloth", tris=900, role="hat", pri=1.3)
    if flowers:          # iara: water-lily headdress
        fl = None
        for i, (x, z) in enumerate(((0.36, -0.05), (-0.36, -0.05), (0.25, 0.25), (-0.25, 0.25), (0.0, 0.32))):
            c0 = V(x, 0.42 - 0.08 * abs(x), z)
            pet = None
            for k in range(6):
                a = k / 6 * math.tau
                tip = c0 + V(0.16 * math.cos(a), 0.05, 0.16 * math.sin(a))
                one = round_cone(hh(*c0), hh(*tip), 0.035 * hs, 0.05 * hs)
                pet = one if pet is None else pet | one
            pet = pet | sphere(0.05 * hs, hh(*(c0 + V(0, 0.05, 0))))
            fl = pet if fl is None else fl | pet
        H.piece("Lilies", "Head", fl, col="secondary", mat="skin", tris=900, role="hat", pri=1.4)
    if hood:              # shahmaran: a cobra hood fanned behind the head
        hd = plate([(-0.95, -0.9), (-0.85, -0.1), (-0.55, 0.45), (0.0, 0.7), (0.55, 0.45), (0.85, -0.1), (0.95, -0.9), (0.0, -1.05)],
                   hh(0, -0.05, 0.42), (1, 0, 0), (0, 1, 0.25), 0.04 * hs, bulge=0.12 * hs)
        hd = hd.su(capsule(hh(0, -0.95, 0.45), hh(0, 0.6, 0.48), 0.07 * hs), 0.05 * hs)
        H.piece("Hood", "Spine", hd, col="primary", mat="skin", tris=1000, role="crest", pri=1.25,
                pattern=spots(0.22 * hs, 0.07 * hs, depth=0.6, ring=True, seed=4))

    # ------------------------------------------------------------------ top / jewellery
    if top == "scale":
        tp = rib.round(0.035 * s) & HM.slab_y(ch[1] - 0.05 * s, ch[1] + 0.3 * s)
        H.piece("Top", "Spine", tp, col="secondary", mat="cloth", tris=900, role="cloth", pri=1.1)
    elif top == "full":   # amabie: scales up to the collarbones
        tp = rib.round(0.03 * s) & HM.slab_y(wa[1] - 0.6 * s, ch[1] + 0.32 * s)
        H.piece("Top", "Spine", tp, col="primary", mat="skin", tris=1200, role="cloth", pri=1.1,
                pattern=spots(0.11 * s, 0.05 * s, depth=0.4, ring=True, seed=9))
    elif top == "sash":
        sh = capsule(T(ch + V(0.42, 0.3, 0) * s), T(ch + V(-0.45, -0.42, 0) * s), 0.36 * s) & (rib.round(0.04 * s))
        sh = sh | (rib.round(0.035 * s) & HM.slab_y(ch[1] - 0.02 * s, ch[1] + 0.26 * s))
        H.piece("Top", "Spine", sh, col="cloth", mat="cloth", tris=900, role="cloth", pri=1.1)
    if jewelry:
        nk = torus(0.24 * s, 0.035 * s).rot(18, 0, 0).at(*T(C["neckB"] + V(0, -0.05, -0.04) * s))
        nk = nk | torus(0.3 * s, 0.03 * s).rot(25, 0, 0).at(*T(C["neckB"] + V(0, -0.15, -0.07) * s))
        H.piece("Necklace", "Spine", nk, col="gold", mat="metal", tris=500, role="detail", pri=1.6)

    # ------------------------------------------------------------------ the tail
    ctrl = _tail_ctrl(tail if tail != "tri" else "fish", wy / s, s)
    ctrl = [c * s for c in ctrl]
    n = 48
    pts = catmull(ctrl, n)
    if tail == "fish":
        rad = [tail_r * s * (1.0 - 0.75 * (i / (n - 1)) ** 1.1) for i in range(n)]
    else:
        rad = []
        for i in range(n):
            u = i / (n - 1)
            rad.append(tail_r * s * (1.0 + 0.12 * math.sin(math.pi * min(u / 0.3, 1.0))) * (1 - 0.86 * min(max((u - 0.28) / 0.72, 0.0), 1.0) ** 1.7))
    # ground contact: lying parts rest on y = radius
    for i in range(n):
        if pts[i][1] < rad[i] * 1.0 + 0.02 * s and not swim:
            pts[i][1] = rad[i] * 0.92
        elif not swim:
            pts[i][1] = max(pts[i][1], rad[i] * 0.92)
    tpat = tail_pat

    def tail_extra(i, sub, rr):
        out = None
        if fins and i >= 1:     # a ribbon dorsal fin
            m = len(sub) // 2
            t = unit(sub[-1] - sub[0])
            up = unit(V(0, 1, 0) - t * t[1])
            L = float(np.linalg.norm(sub[-1] - sub[0]))
            hgt = rr[m] * 0.75
            poly = [(-0.5 * L, 0.0), (-0.3 * L, hgt), (0.0, hgt * 0.7), (0.25 * L, hgt * 1.05), (0.5 * L, 0.0)]
            out = plate(poly, T(sub[m] + up * rr[m] * 0.75), T(t), T(up), 0.022 * s)
        if i == nseg - 1 and (fluke or swim):
            t = unit(sub[-1] - sub[-3])
            lat = unit(np.cross(V(0, 1, 0), t)) if abs(t[1]) < 0.95 else V(1, 0, 0)
            sz = 1.15 if swim else 0.8
            poly = [(0, -0.08), (0.45, 0.25), (0.85, 0.6), (0.75, 0.25), (0.8, 0.0), (0.75, -0.2), (0.0, 0.0),
                    (-0.75, -0.2), (-0.8, 0.0), (-0.75, 0.25), (-0.85, 0.6), (-0.45, 0.25)]
            poly = [(x * sz * s, y * sz * s) for x, y in poly]
            fk = plate(poly, T(sub[-1] - t * 0.12 * s), T(lat), T(t), 0.035 * s, bulge=0.03 * s)
            out = fk if out is None else out | fk
        return out

    nb = chain(H, "Tail", "Body", pts, rad, nseg, col="primary", mat="skin", tris=900, extra=tail_extra, pattern=tpat,
               role="tail", pri=1.3, tri_scale=[1.2, 1.0, 0.9, 0.8, 0.7, 0.6, 0.6][:nseg])
    if fins and swim:   # hip fins
        p0 = pts[int(n * 0.18)]
        hf = plate([(0, 0), (0.35, -0.12), (0.5, -0.5), (0.22, -0.38), (0.0, -0.28)], T(p0 + V(0.3, 0.05, 0.05) * s), (1, 0, 0.2), (0, 1, 0.3), 0.02 * s)
        hf = hf | plate([(0, 0), (-0.35, -0.12), (-0.5, -0.5), (-0.22, -0.38), (0.0, -0.28)], T(p0 + V(-0.3, 0.05, 0.05) * s), (1, 0, -0.2), (0, 1, 0.3), 0.02 * s)
        H.piece("HipFins", nb[1], hf, col="secondary", mat="skin", tris=500, role="fin", pri=1.4)
    if tri:   # amabie: two more short scaled tails splayed to the sides as a tripod
        for sx, nm in ((1, "R"), (-1, "L")):
            c2 = [V(0.15 * sx, wy / s - 0.6, 0.0), V(0.55 * sx, 0.9, -0.1), V(0.95 * sx, 0.35, -0.3), V(1.3 * sx, 0.3, -0.75)]
            p2 = catmull([c * s for c in c2], 16)
            r2 = taper(16, 0.3 * s, 0.1 * s)
            sd = tube([T(p2[j]) for j in range(0, 15, 3)] + [T(p2[-1])], [r2[j] for j in range(0, 15, 3)] + [r2[-1]])
            d = unit(p2[-1] - p2[-3])
            latv = unit(np.cross(V(0, 1, 0), d))
            fk = plate([(0, -0.05), (0.35, 0.25), (0.55, 0.45), (0.45, 0.1), (0.0, 0.0), (-0.45, 0.1), (-0.55, 0.45), (-0.35, 0.25)],
                       T(p2[-1] - d * 0.08 * s), T(latv), T(d), 0.03 * s)
            H.bone("Leg" + nm, "Body", T(p2[0]))
            H.piece("LegTail" + nm, "Leg" + nm, sd | fk, col="primary", mat="skin", tris=800, role="limb", pri=1.4, pattern=tpat,
                    key=f"h_{hid}_legtail{'' if sx > 0 else '_l'}")
    if python:   # mami wata: a python draped over the shoulders, head raised on the right
        nb_ = C["neckB"]
        pc = [nb_ + V(-0.75, -0.65, -0.2) * s, nb_ + V(-0.55, -0.05, 0.05) * s, nb_ + V(-0.2, 0.08, 0.3) * s, nb_ + V(0.3, 0.06, 0.28) * s,
              nb_ + V(0.62, -0.1, 0.0) * s, nb_ + V(0.75, -0.35, -0.35) * s, nb_ + V(0.7, 0.05, -0.7) * s, nb_ + V(0.62, 0.32, -0.82) * s]
        pp = catmull(pc, 30)
        pr = [0.11 * s * (1 - 0.35 * (j / 29)) for j in range(30)]
        pr[0] = 0.05 * s
        for j in range(1, 4):
            pr[j] = 0.05 * s + 0.06 * s * j / 3
        sd = tube([T(pp[j]) for j in range(0, 30, 3)] + [T(pp[-1])], [pr[j] for j in range(0, 30, 3)] + [pr[-1]], k=0.02 * s)
        hd_ = pp[-1]
        dd = unit(pp[-1] - pp[-3])
        sd = sd.su(ellipsoid(0.12 * s, 0.09 * s, 0.17 * s, T(hd_ + dd * 0.1 * s)), 0.05 * s)
        H.bone("Python", "Spine", T(nb_ + V(0, 0, 0.1) * s))
        H.piece("PythonP", "Python", sd, col="secondary", mat="skin", tris=1200, res=128, role="tail", pri=1.25,
                pattern=spots(0.16 * s, 0.06 * s, depth=0.55, seed=12))
        for sx in (1, -1):
            pass
        H.prim("PyEyeR", "Python", "Ball", (0.04 * s,) * 3, T(hd_ + dd * 0.14 * s + V(0.07, 0.05, 0) * s), col="pupil", mat="hard", pri=2.2, role="eye")
        H.prim("PyEyeL", "Python", "Ball", (0.04 * s,) * 3, T(hd_ + dd * 0.14 * s + V(-0.07, 0.05, 0) * s), col="pupil", mat="hard", pri=2.2, role="eye")
    wingb = ()
    if wings:
        wingb = HM._bat_wings(H, C, P, span=0.9, col="secondary")
    arms = [("ShoulderR", "ElbowR", "HandR", 1), ("ShoulderL", "ElbowL", "HandL", -1)]
    H.socket("mouth", hh(0, -0.25, -0.5), "Head")
    H.socket("head", hh(0, 0.6, 0), "Head")
    H.socket("hand", T(C.get("grip", C["Wr"])), "HandR")
    H.rig.update({"head": "Head", "tail": nb, "arms": [{"shoulder": "ShoulderR", "elbow": "ElbowR", "side": 1},
                                                      {"shoulder": "ShoulderL", "elbow": "ElbowL", "side": -1}]})
    hairs = hairb + (["Python"] if python else [])
    MS.serpfolk(H, nb, arms=arms, spine="Spine", head="Head", hair=hairs, wings=wingb, height=float(hc[1] + 0.5 * hs),
                swim=swim, attack=attack, amp=0.3 if not swim else 0.35,
                extra=(lambda pose, kind, u, k: [MS._add(pose, b, (0, 0, 0, 0.12 * math.sin(6.283 * u * 2), 0, 0)) for b in ("LegR", "LegL")]) if tri else None)
    return H


SCALES = spots(0.12, 0.05, depth=0.28, ring=True, seed=2)


@hero("lamia", FAM)
def lamia():
    pat = combine(SCALES, spots(0.42, 0.17, depth=0.55, ring=False, seed=5))
    return _serpfolk("lamia", tail="s", crest="fan", hair="long", claws=True, tail_pat=pat, top="scale", attack="claw",
                     iris=[0.95, 0.75, 0.1], tags=["lamia"],
                     preview={"primary": "#4F7A3A", "secondary": "#C9A23A", "skin": "#D9B58E", "hair": "#2A1E1A"})


@hero("melusine", FAM)
def melusine():
    return _serpfolk("melusine", tail="long", hair="long", crown=False, fins=True, wings=True, fluke=True, top="scale", nseg=6,
                     tail_pat=combine(SCALES, gradient(2, 0.0, 6.0, 1.0, 0.75)), tail_r=0.42, attack="whip",
                     iris=[0.3, 0.6, 0.85], tags=["melusine", "dragon"],
                     preview={"primary": "#2F6E8C", "secondary": "#7A3B7E", "skin": "#EBCBB0", "hair": "#E3C67A"})


@hero("shahmaran", FAM)
def shahmaran():
    return _serpfolk("shahmaran", tail="coil", hair="long", crown=True, hood=True, top="sash", nseg=6, tail_r=0.5,
                     tail_pat=combine(SCALES, spots(0.3, 0.1, depth=0.6, seed=8)), attack="whip",
                     iris=[0.9, 0.7, 0.1], tags=["shahmaran", "queen"], jewelry=True,
                     preview={"primary": "#C9A227", "secondary": "#1F6F5A", "skin": "#E2B58C", "hair": "#1E1A18", "cloth": "#1F6F5A"})


@hero("mami wata", FAM)
def mami_wata():
    return _serpfolk("mami wata", tail="fish", hair="long", python=True, fins=True, top="scale", jewelry=True, nseg=4, tail_r=0.44,
                     tail_pat=combine(SCALES, gradient(1, 0.3, 2.6, 0.8, 1.0)), gait="swim", plan="Fish", attack="claw",
                     iris=[0.45, 0.28, 0.12], tags=["merfolk", "water spirit"],
                     preview={"primary": "#1E8C7E", "secondary": "#C08A2A", "skin": "#7A4A2E", "hair": "#141012"})


@hero("medusa", FAM)
def medusa():
    pat = combine(SCALES, stripes(lambda Q: np.linalg.norm(Q[:, [0, 2]], axis=1), 2.2, width=0.25, depth=0.45))
    return _serpfolk("medusa", tail="s", hair=None, snakehair=True, claws=True, top="sash", tail_pat=pat, attack="claw",
                     iris=[0.6, 0.95, 0.3], tags=["gorgon"], jewelry=True,
                     preview={"primary": "#5E7A44", "secondary": "#3E6A2A", "skin": "#A9C29A", "hair": "#3E6A2A", "cloth": "#6E4A8A"})


@hero("iara", FAM)
def iara():
    return _serpfolk("iara", tail="fish", hair="long", flowers=True, fins=True, top="scale", nseg=4, tail_r=0.42,
                     tail_pat=combine(SCALES, gradient(1, 0.3, 2.6, 0.75, 1.0)), gait="swim", plan="Fish",
                     iris=[0.25, 0.55, 0.3], tags=["merfolk", "water spirit"],
                     preview={"primary": "#3E9A5A", "secondary": "#F2B8D0", "skin": "#C98E62", "hair": "#16120F"})


@hero("merrow", FAM)
def merrow():
    return _serpfolk("merrow", tail="fish", hair="long", cap="merrow", fins=True, top="sash", nseg=4, tail_r=0.46, muscle=0.5, W=0.95,
                     tail_pat=combine(SCALES, gradient(1, 0.3, 2.6, 0.75, 1.0)), gait="swim", plan="Fish", claws=False,
                     iris=[0.2, 0.5, 0.45], tags=["merfolk", "irish"],
                     preview={"primary": "#3F7F6E", "secondary": "#8FC4B0", "skin": "#B8C9A8", "hair": "#2E5A3A", "cloth": "#5A4632"})


@hero("amabie", FAM)
def amabie():
    return _serpfolk("amabie", tail="tri", tri=True, hair="long", beak=True, top="full", nseg=4, tail_r=0.36,
                     tail_pat=SCALES, gait="swim", plan="Fish", attack="whip", iris=[0.15, 0.15, 0.2], tags=["yokai", "amabie"],
                     preview={"primary": "#5FA8A0", "secondary": "#E8D9B0", "skin": "#F2E4D0", "hair": "#2F3E5A", "beak": "#E89A3A"})



# ================================================================================================ marine reptiles
import motion_aquatic as MA  # noqa: E402
import motion_reptiles as MR  # noqa: E402


def _cut(body, z0, z1, shrink=0.0, k=0.06):
    b = body.round(-shrink) if shrink else body
    return MA.segment(b, z0, z1, k)


def _teeth_row(p0, p1, n, r, ln, down=True, out=0.0):
    t = None
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    for i in range(n):
        c = p0 + (p1 - p0) * (i + 0.5) / n
        tip = c + V(np.sign(c[0]) * out if c[0] else 0, -ln if down else ln, -ln * 0.15)
        one = round_cone(T(c), T(tip), r, r * 0.2)
        t = one if t is None else t | one
    return t


@hero("ichthyosaurus", FAM)
def ichthyosaurus():
    s = 1.0
    H = Hero("ichthyosaurus", plan="Fish", gait="swim", tags=["marine reptile", "prehistoric"])
    H.preview = {"primary": "#46667E", "secondary": "#DCE3E6", "iris": "#E0B030", "eyeWhite": "#E9E2C8"}
    L, z0, y0 = 6.2, -3.2, 1.5
    rows = [(0.0, 0.004, -0.004, 0.005), (0.06, 0.012, -0.012, 0.012), (0.13, 0.032, -0.03, 0.03), (0.19, 0.066, -0.05, 0.055),
            (0.27, 0.09, -0.07, 0.072), (0.4, 0.105, -0.085, 0.08), (0.55, 0.095, -0.075, 0.07), (0.7, 0.058, -0.045, 0.045),
            (0.84, 0.028, -0.024, 0.022), (0.96, 0.016, -0.02, 0.012), (1.0, 0.012, -0.02, 0.01)]
    pr = MA.Profile(rows, L, z0, y0)
    body = pr.sdf()
    shade = combine(topshade(y0 - 0.3, y0 + 0.4, 1.0, 0.7), mottle(0.25, 0.06, 0.15, 4))
    zs = [z0, -1.9, 0.9, 1.9, 2.35, z0 + L]
    H.body((0, y0, -0.4))
    H.bone("Head", "Body", (0, y0, -1.95))
    H.bone("Jaw", "Head", (0, y0 - 0.12, -2.05))
    H.bone("Tail1", "Body", (0, y0, 0.85))
    H.bone("Tail2", "Tail1", (0, y0, 1.85))
    H.bone("Tail3", "Tail2", (0, y0 - 0.05, 2.3))
    # head: upper rostrum + skull on Head, lower jaw on Jaw, a dark slit between them
    hd = _cut(body, z0, -1.75) & SDF(lambda p: (y0 - 0.02) - p[:, 1] if False else -(p[:, 1] - (y0 - 0.025)) * -1)
    hd = _cut(body, z0, -1.75).si(SDF(lambda p: (y0 - 0.025) - p[:, 1]), 0.01)
    hd = hd.su(_cut(body, -2.55, -1.75), 0.0)
    hd = hd.ss(sphere(0.15, (0.2, y0 + 0.08, -2.35)).mirror_x(), 0.03)
    hd = hd.su(torus(0.145, 0.03, axis=0).at(0.19, y0 + 0.08, -2.35).mirror_x(), 0.02)            # sclerotic ring rim
    hd = hd.su(_teeth_row((0.05, y0 - 0.01, -3.05), (0.12, y0 - 0.03, -2.3), 9, 0.02, 0.07).mirror_x(), 0.0)
    H.piece("HeadP", "Head", hd, col="primary", tris=1800, res=144, role="head", pattern=shade)
    jw = _cut(body.round(-0.012), z0 + 0.06, -2.15).si(SDF(lambda p: p[:, 1] - (y0 - 0.06)), 0.01)
    jw = jw.su(_teeth_row((0.045, y0 - 0.05, -3.0), (0.1, y0 - 0.06, -2.3), 8, 0.018, 0.06, down=False).mirror_x(), 0.0)
    H.piece("JawP", "Jaw", jw, col="secondary", tris=700, role="jaw", pri=1.3)
    H.prim("Mouth", "Head", "Ellipsoid", (0.14, 0.05, 0.9), (0, y0 - 0.04, -2.55), col="mouth", mat="hard", role="mouth", pri=2.4)
    H.eyes("Head", (0.185, y0 + 0.08, -2.35), 0.12, col="iris", pupil="round", look=(1.0, 0.0, -0.2))
    tor = _cut(body, -1.95, 0.95, 0.012)
    dors = MA.plate((0, y0 + 0.5, -0.05), (0, 0, 1), (0, 1, 0), [(-0.55, 0.0), (0.05, 0.75), (0.35, 0.72), (0.6, 0.0)], 0.12)
    tor = tor.su(dors, 0.08)
    H.piece("Torso", "Body", tor, col="primary", tris=2200, res=128, pattern=shade)
    H.piece("TailP1", "Tail1", _cut(body, 0.8, 1.95, 0.02), col="primary", tris=900, role="tail", pattern=shade)
    H.piece("TailP2", "Tail2", _cut(body, 1.8, 2.45, 0.028), col="primary", tris=500, role="tail", pattern=shade)
    # crescent tail: lower lobe carries the spine, upper lobe a fleshy fin
    fl = MA.plate((0, y0 - 0.02, 2.55), (0, 0, 1), (0, 1, 0),
                  [(-0.35, 0.0), (0.0, 0.5), (0.35, 1.05), (0.55, 1.1), (0.35, 0.55), (0.25, 0.0), (0.35, -0.6), (0.5, -1.05), (0.28, -1.0), (0.0, -0.45)], 0.14)
    fl = fl.su(_cut(body, 2.25, z0 + L, 0.035), 0.06)
    H.piece("TailFin", "Tail3", fl, col="primary", tris=900, role="fin", pattern=shade)
    pecs = []
    for tag, z, ln, w in (("F", -1.25, 1.0, 0.36), ("B", 0.45, 0.62, 0.24)):
        root = V(0.38 if tag == "F" else 0.3, y0 - 0.32, z)
        H.mbone(f"Fl{tag}#", "Body", T(root))
        fp = MA.plate(T(root), (1, -0.35, 0.45), (0, 0, 1), [(0, -w * 0.5), (ln * 0.55, -w * 0.45), (ln, 0.0), (ln * 0.8, w * 0.4), (0.0, w * 0.5)], 0.08)
        fp = fp.su(sphere(0.13, T(root - V(0.05, -0.02, 0))), 0.06)
        H.mpiece(f"Flipper{tag}#", f"Fl{tag}#", fp, col="primary", tris=500, role="fin", pattern=shade)
        pecs.append((f"Fl{tag}R", f"Fl{tag}L"))
    H.socket("mouth", (0, y0 - 0.03, -3.2), "Jaw")
    H.socket("head", (0, y0 + 0.45, -1.95), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": ["Tail1", "Tail2", "Tail3"]})
    MA.swim(H, ["Tail1", "Tail2", "Tail3"], head="Head", jaw="Jaw", pecs=pecs, mode="yaw", period=1.1, amp=0.3, length=L, attack="bite")
    return H


@hero("pliosaurus", FAM)
def pliosaurus():
    H = Hero("pliosaurus", plan="Fish", gait="swim", tags=["marine reptile", "prehistoric"])
    H.preview = {"primary": "#4E5E52", "secondary": "#D6D2BE", "iris": "#D0A030", "tooth": "#F2EAD0"}
    y0 = 1.5
    L, z0 = 5.2, -1.6
    rows = [(0.0, 0.07, -0.07, 0.07), (0.1, 0.1, -0.1, 0.1), (0.3, 0.135, -0.13, 0.14), (0.5, 0.12, -0.11, 0.125),
            (0.7, 0.075, -0.07, 0.075), (0.88, 0.035, -0.035, 0.035), (1.0, 0.01, -0.012, 0.01)]
    pr = MA.Profile(rows, L, z0, y0)
    body = pr.sdf()
    shade = combine(topshade(y0 - 0.5, y0 + 0.6, 1.0, 0.68), spots(0.35, 0.09, depth=0.25, seed=6))
    H.body((0, y0, 0.2))
    H.bone("Neck", "Body", (0, y0 + 0.05, -1.4))
    H.bone("Head", "Neck", (0, y0 + 0.1, -2.0))
    H.bone("Jaw", "Head", (0, y0 - 0.08, -2.0))
    H.bone("Tail1", "Body", (0, y0, 2.0))
    H.bone("Tail2", "Tail1", (0, y0 - 0.02, 2.9))
    tor = _cut(body, z0, 2.1)
    tor = tor.su(ellipsoid(0.55, 0.5, 0.5, (0, y0 + 0.05, -1.55)), 0.3)
    H.piece("Torso", "Body", tor, col="primary", tris=2400, res=128, pattern=shade)
    neck = round_cone((0, y0 + 0.02, -1.35), (0, y0 + 0.12, -2.05), 0.56, 0.48)
    H.piece("NeckP", "Neck", neck, col="primary", tris=900, role="limb", pattern=shade)
    # big crocodile-like skull
    hc = V(0, y0 + 0.12, -2.1)
    sk = ellipsoid(0.5, 0.38, 0.6, T(hc + V(0, 0.02, -0.2)))
    sk = sk.su(round_cone(T(hc + V(0, 0.0, -0.55)), T(hc + V(0, -0.06, -1.75)), 0.36, 0.2), 0.25)
    sk = sk.su(ellipsoid(0.23, 0.17, 0.25, T(hc + V(0, -0.04, -1.7))), 0.1)               # rosette at snout tip
    sk = sk.su(capsule(T(hc + V(0.22, 0.25, -0.35)), T(hc + V(0.18, 0.12, -1.0)), 0.07).mirror_x(), 0.1)  # brow ridges
    sk = sk.ss(sphere(0.12, T(hc + V(0.33, 0.2, -0.5))).mirror_x(), 0.04)
    sk = sk.si(SDF(lambda p: (hc[1] - 0.12) - p[:, 1]), 0.03)                              # flat underside / gum line
    up = None
    for i in range(7):
        z = -0.55 - i * 0.18
        w = 0.3 - i * 0.017
        one = round_cone(T(hc + V(w, -0.12, z)), T(hc + V(w + 0.04, -0.4 + 0.02 * i, z - 0.04)), 0.045, 0.01)
        up = one if up is None else up | one
    up = up.mirror_x() | round_cone(T(hc + V(0.08, -0.12, -1.85)), T(hc + V(0.1, -0.4, -1.95)), 0.05, 0.012).mirror_x()
    H.piece("Skull", "Head", sk, col="primary", tris=2200, res=136, role="head", pattern=shade)
    H.piece("UpperTeeth", "Head", up, col="tooth", mat="hard", tris=600, role="tooth", pri=1.8, ao=False, smooth=2)
    jw = ellipsoid(0.44, 0.2, 0.55, T(hc + V(0, -0.3, -0.25)))
    jw = jw.su(round_cone(T(hc + V(0, -0.28, -0.6)), T(hc + V(0, -0.27, -1.75)), 0.3, 0.17), 0.2)
    jw = jw.si(SDF(lambda p: p[:, 1] - (hc[1] - 0.17)), 0.03)
    lo = None
    for i in range(6):
        z = -0.6 - i * 0.19
        w = 0.24 - i * 0.015
        one = round_cone(T(hc + V(w, -0.19, z)), T(hc + V(w + 0.03, 0.05, z + 0.02)), 0.04, 0.01)
        lo = one if lo is None else lo | one
    H.piece("JawP", "Jaw", jw, col="secondary", tris=1100, role="jaw", pri=1.3)
    H.piece("LowerTeeth", "Jaw", lo.mirror_x(), col="tooth", mat="hard", tris=500, role="tooth", pri=1.9, ao=False, smooth=2)
    H.prim("Mouth", "Head", "Ellipsoid", (0.55, 0.06, 1.5), T(hc + V(0, -0.17, -0.95)), col="mouth", mat="hard", role="mouth", pri=2.4)
    H.eyes("Head", T(hc + V(0.33, 0.2, -0.52)), 0.1, col="iris", pupil="round", look=(1.0, 0.25, -0.5))
    H.piece("TailP1", "Tail1", _cut(body, 1.95, 3.0, 0.015), col="primary", tris=700, role="tail", pattern=shade)
    H.piece("TailP2", "Tail2", _cut(body, 2.85, z0 + L, 0.025), col="primary", tris=400, role="tail", pattern=shade)
    fr, br = [], []
    for tag, z, ln, w in (("F", -0.75, 2.1, 0.55), ("B", 1.2, 2.2, 0.6)):
        root = V(0.62, y0 - 0.35, z)
        H.mbone(f"Fl{tag}#", "Body", T(root))
        H.mbone(f"FlT{tag}#", f"Fl{tag}#", T(root + V(ln * 0.5, -0.12, ln * 0.18)))
        u = unit(V(1, -0.2, 0.36))
        base = MA.plate(T(root), T(u), (0, 0, 1), [(0, -w * 0.5), (ln * 0.55, -w * 0.4), (ln * 0.55, w * 0.42), (0.0, w * 0.55)], 0.13, taper=0.6)
        base = base.su(ellipsoid(0.28, 0.24, 0.42, T(root)), 0.12)
        tipp = MA.plate(T(root), T(u), (0, 0, 1), [(ln * 0.48, -w * 0.4), (ln * 0.85, -w * 0.25), (ln, 0.05), (ln * 0.85, w * 0.32), (ln * 0.48, w * 0.42)], 0.1)
        H.mpiece(f"Flipper{tag}#", f"Fl{tag}#", base, col="primary", tris=700, role="fin", pattern=shade)
        H.mpiece(f"FlipTip{tag}#", f"FlT{tag}#", tipp.round(-0.008), col="primary", tris=450, role="fin", pattern=shade)
        (fr if tag == "F" else br).extend([(f"Fl{tag}R", f"FlT{tag}R", 1), (f"Fl{tag}L", f"FlT{tag}L", -1)])
    H.socket("mouth", T(hc + V(0, -0.2, -1.9)), "Jaw")
    H.socket("head", T(hc + V(0, 0.45, -0.2)), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "neck": "Neck", "tail": ["Tail1", "Tail2"]})
    MR.flipper(H, fr, br, head="Head", neck=["Neck"], jaw="Jaw", tail=["Tail1", "Tail2"], walk=1.9, height=y0 + 0.6, fl_amp=0.5)
    return H


# ================================================================================================ low quadrupeds
def _quad(hid, s=1.0, leg=1.0, BL=1.0, G=1.0, sprawl=0.0, LT=1.0, flat=1.0, head="dog", HS=1.0, ML=1.0, neck=1.0,
          tail="thin", TL=1.0, TR=1.0, feet="paw", fur=0.0, tusks=0.0, incisors=False, scutes=False, shell=False,
          horns=False, ears="small", gait="trot", attack="bite", pat=None, eye=1.0, tags=(), preview=None, plan="Quadruped",
          belly=0.8, eye_up=0.0, mane=False, bill_col="dark"):
    H = Hero(hid, plan=plan, gait=gait, tags=list(tags))
    H.preview = preview or {}

    def v(x, y, z):
        return V(x, y, z) * s

    legH = 1.0 * leg
    bodyY = legH * (1 - 0.32 * sprawl) + 0.12
    if shell:
        bodyY = legH * 0.95 + 0.05
    zc, zr = -0.65 * BL, 0.6 * BL
    H.body(T(v(0, bodyY, 0)))
    pat = combine(topshade((bodyY - 0.5 * G) * s, (bodyY + 0.6 * G) * s, 1.0, belly), pat)

    def furry(sd, amp=1.0, seed=0):
        return sd.noise(fur * amp * s, 8.0 / s, seed) if fur > 0 else sd

    # ------------------------------------------------------------------ torso
    tor = ellipsoid(0.6 * G * s, 0.52 * G * flat * s, 0.85 * BL * s, T(v(0, bodyY + 0.04, zc)))
    tor = tor.su(ellipsoid(0.6 * G * s, 0.5 * G * flat * s, 0.82 * BL * s, T(v(0, bodyY + 0.02, zr))), 0.4 * s)
    tor = tor.su(ellipsoid(0.62 * G * s, 0.45 * G * flat * s, 0.7 * BL * s, T(v(0, bodyY - 0.08 * G, 0))), 0.3 * s)  # belly
    tor = tor.su(ellipsoid(0.3 * G * s, 0.36 * G * s, 0.38 * s, T(v(0.48 * G, bodyY - 0.05, zc - 0.25 * BL))).mirror_x(), 0.2 * s)  # shoulders
    tor = tor.su(ellipsoid(0.3 * G * s, 0.38 * G * s, 0.45 * s, T(v(0.45 * G, bodyY - 0.02, zr + 0.2 * BL))).mirror_x(), 0.2 * s)   # haunch
    if scutes:
        sc = None
        for i in range(9):
            z = zc - 0.55 * BL + i * 0.17 * BL * 1.7 / 1.0 * 0.6
            for x in (0.14, 0.34):
                one = ellipsoid(0.09 * s, 0.07 * s, 0.11 * s, T(v(x * G, bodyY + 0.47 * G * flat - 0.12 * x, z)))
                sc = one if sc is None else sc | one
        tor = tor.su(sc.mirror_x(), 0.04 * s)
    if mane:
        tor = tor.su(ellipsoid(0.4 * G * s, 0.4 * s, 0.9 * s, T(v(0, bodyY + 0.42 * G, zc - 0.1))).noise(0.06 * s, 6 / s, 9), 0.2 * s)
    H.piece("Torso", "Body", furry(tor, 1.0, 1), col="primary", tris=2400, res=128, pattern=pat)
    if shell:
        sh = ellipsoid(1.05 * G * s, 0.75 * G * s, 1.25 * BL * s, T(v(0, bodyY + 0.05, 0.05)))
        sh = sh.si(SDF(lambda p, y=(bodyY - 0.12) * s: y - p[:, 1]), 0.08 * s)
        sh = sh.su(torus(1.0 * G * s, 0.08 * s).scale3(1, 1, 1.2 * BL / G).at(*T(v(0, bodyY - 0.1, 0.05))), 0.1 * s)   # marginal rim
        sp = None
        for i, z in enumerate((-0.75, -0.25, 0.25, 0.75)):
            for x in (0.0, 0.5):
                yb = bodyY + 0.05 + 0.75 * G * math.sqrt(max(0.0, 1 - (x / 1.05) ** 2 - (z / 1.25) ** 2)) - 0.05
                base = v(x * G, yb, z * BL)
                tip = base + v(0.12 * x, 0.38 - 0.1 * abs(z), 0.12)
                one = round_cone(T(base), T(tip), 0.15 * s, 0.02 * s)
                sp = one if sp is None else sp | one
        sh = sh.su(sp.mirror_x(), 0.05 * s)
        hexes = spots(0.5 * s, 0.22 * s, depth=0.35, ring=True, seed=3)
        H.piece("Shell", "Body", sh, col="secondary", mat="hard", tris=2600, res=136, role="shell", pattern=hexes)
        pl = ellipsoid(0.85 * G * s, 0.22 * s, 1.05 * BL * s, T(v(0, bodyY - 0.22, 0.05)))
        H.piece("Plastron", "Body", pl, col="belly", mat="hard", tris=700, role="shell", pri=1.4)

    # ------------------------------------------------------------------ legs
    legs = []
    qlegs = []
    for front in (True, False):
        tag = "F" if front else "B"
        z = (zc - 0.3 * BL) if front else (zr + 0.3 * BL)
        if shell:
            z = (-0.75 * BL) if front else (0.8 * BL)
        sh = v(0.48 * G + (0.25 if shell else 0), bodyY - 0.1, z)
        y1 = sh[1] / s
        el = sh + v(0.45 * sprawl, -(y1 * (0.5 - 0.25 * sprawl)), (0.08 if front else -0.12) * (1 - sprawl))
        wr = V(sh[0] + 0.5 * sprawl * s, 0.2 * s, sh[2] + (-0.05 if front else 0.05) * s)
        H.mbone(f"Up{tag}#", "Body", T(sh))
        H.mbone(f"Lo{tag}#", f"Up{tag}#", T(el))
        H.mbone(f"Ft{tag}#", f"Lo{tag}#", T(wr))
        r0 = (0.3 if front else 0.36) * LT * s
        up = round_cone(T(sh + v(0, 0.1, 0)), T(el), r0, 0.18 * LT * s)
        up = up.su(ellipsoid(r0 * 0.9, r0 * 1.2, r0 * 1.1, T(sh + (el - sh) * 0.35)), 0.1 * s)
        H.mpiece(f"Upper{tag}#", f"Up{tag}#", furry(up, 0.7, 2), col="primary", tris=650, role="limb", pattern=pat)
        lo = round_cone(T(el), T(wr + v(0, 0.04, 0)), 0.18 * LT * s, 0.12 * LT * s)
        H.mpiece(f"Lower{tag}#", f"Lo{tag}#", furry(lo, 0.5, 3), col="primary", tris=500, role="limb", pattern=pat)
        # foot
        fc = wr
        gnd = plane((0, -1, 0), 0.0)
        if feet == "web":
            f = ellipsoid(0.16 * LT * s, 0.1 * s, 0.2 * s, T(fc + v(0, -0.1, -0.1)))
            toes = None
            for dx in (-0.16, -0.06, 0.05, 0.15):
                a = fc + v(dx * 0.4, -0.12, -0.15)
                b = fc + v(dx * (2.0 if front else 1.6), -0.15, -0.45 - (0.08 if not front else 0))
                one = round_cone(T(a), T(b), 0.05 * s, 0.035 * s)
                toes = one if toes is None else toes | one
            web = MA.plate(T(fc + v(0, -0.155, -0.1)), (1, 0, 0), (0, 0, -1),
                           [(-0.1, 0.0), (0.1, 0.0), (0.17 * (2.0 if front else 1.6), 0.36), (0.0, 0.3), (-0.17 * (2.0 if front else 1.6), 0.36)], 0.035 * s)
            f = f.su(toes, 0.04 * s).su(web, 0.02 * s)
        elif feet == "flipper":
            f = MA.plate(T(fc + v(0.0, -0.13, -0.05)), (0.3, 0, -1), (1, 0, 0), [(-0.1, -0.15), (0.45, -0.22), (0.6, 0.0), (0.45, 0.22), (-0.1, 0.18)], 0.09 * s)
            f = f.su(sphere(0.13 * s, T(fc)), 0.08 * s)
        elif feet == "column":
            f = cylinder(0.2 * LT * s, 0.14 * s, rr=0.05 * s).at(*T(fc + v(0, -0.06, -0.02)))
            for dx in (-0.12, 0.0, 0.12):
                f = f.su(sphere(0.06 * s, T(fc + v(dx, -0.15, -0.2))), 0.03 * s)
        else:  # paw / claw
            f = ellipsoid(0.15 * LT * s, 0.1 * s, 0.24 * s, T(fc + v(0, -0.1, -0.12)))
            for dx in (-0.1, -0.03, 0.04, 0.11):
                f = f.su(sphere(0.055 * s, T(fc + v(dx * LT, -0.14, -0.32))), 0.03 * s)
                if feet == "claw":
                    f = f | round_cone(T(fc + v(dx * LT, -0.14, -0.36)), T(fc + v(dx * LT * 1.1, -0.19, -0.47)), 0.035 * s, 0.008 * s)
        f = f.su(round_cone(T(fc + v(0, 0.06, 0)), T(fc + v(0, -0.08, -0.05)), 0.12 * LT * s, 0.12 * LT * s), 0.05 * s)
        H.mpiece(f"Foot{tag}#", f"Ft{tag}#", (f & gnd), col="primary" if feet != "web" else "dark", tris=550, role="foot", pattern=pat)
        if sprawl > 0.3:
            legs += [(f"Up{tag}R", f"Lo{tag}R", f"Ft{tag}R", 0.0 if front else 0.5, 1, front), (f"Up{tag}L", f"Lo{tag}L", f"Ft{tag}L", 0.5 if front else 0.0, -1, front)]
        else:
            qlegs += [(f"Up{tag}R", f"Lo{tag}R", f"Ft{tag}R", 0.75 if front else 0.5, front), (f"Up{tag}L", f"Lo{tag}L", f"Ft{tag}L", 0.25 if front else 0.0, front)]

    # ------------------------------------------------------------------ neck + head
    nb = v(0, bodyY + 0.12, zc - 0.65 * BL)
    H.bone("Neck", "Body", T(nb))
    hcz = zc - 0.85 * BL - 0.45 * neck - (0.25 if shell else 0)
    hcy = bodyY + 0.22 + 0.25 * neck * (1 - 0.5 * sprawl) - (0.1 if shell else 0)
    hc = v(0, hcy, hcz)
    nk = round_cone(T(v(0, bodyY + 0.02, zc - 0.35 * BL)), T(hc + v(0, -0.05, 0.25)), 0.42 * G * s * (0.85 if shell else 1), 0.3 * HS * s)
    H.piece("NeckP", "Neck", furry(nk, 0.8, 4), col="primary", tris=900, role="limb", pattern=pat)
    H.bone("Head", "Neck", T(hc))
    hs = HS * s

    def hh(x, y, z):
        return T(hc + V(x, y, z) * hs)

    jaw = None
    if head == "bill":
        hd = ellipsoid(0.3 * hs, 0.26 * hs, 0.33 * hs, hh(0, 0.02, 0.0))
        H.piece("HeadP", "Head", furry(hd, 0.5, 5), col="primary", tris=1100, role="head", pattern=pat)
        bill = round_box(0.2 * hs, 0.045 * hs, 0.4 * hs, 0.04 * hs, hh(0, -0.04, -0.55))
        bill = bill.su(ellipsoid(0.22 * hs, 0.06 * hs, 0.16 * hs, hh(0, -0.04, -0.85)), 0.06 * hs)
        bill = bill.su(ellipsoid(0.27 * hs, 0.12 * hs, 0.06 * hs, hh(0, -0.02, -0.22)), 0.04 * hs)    # shield
        bill = bill.ss(sphere(0.022 * hs, hh(0.06, 0.02, -0.82)).mirror_x(), 0.01 * hs)
        H.piece("Bill", "Head", bill, col=bill_col, mat="skin", tris=800, role="beak", pri=1.3)
        eyep = hh(0.2, 0.1, -0.16)
        er = 0.045 * hs
        mouth = hh(0, -0.08, -0.9)
    else:
        sp = dict(dog=(0.36, 0.3, 0.36, 0.55, 0.2, 0.13, 0.95), croc=(0.36, 0.24, 0.36, 1.1, 0.22, 0.13, 0.75),
                  beaver=(0.42, 0.36, 0.4, 0.3, 0.26, 0.2, 1.0), dragon=(0.34, 0.3, 0.36, 0.45, 0.22, 0.16, 0.9),
                  viper=(0.36, 0.22, 0.4, 0.25, 0.25, 0.14, 0.8))[head]
        cw, chh, cl, mz, m0, m1, fl = sp
        mz *= ML
        hd = ellipsoid(cw * hs, chh * hs, cl * hs, hh(0, 0.05, 0.05))
        hd = hd.su(round_cone(hh(0, 0.0, -0.15), hh(0, -0.05 + (0.04 if head == "croc" else 0), -0.25 - mz), m0 * hs, m1 * hs).scale3(1, 1, 1) if True else None, 0.15 * hs)
        if head == "croc":
            hd = hd.si(SDF(lambda p, y=hc[1] - 0.06 * hs: y - p[:, 1]), 0.04 * hs)
            hd = hd.su(sphere(0.11 * hs, hh(0.16, 0.18, -0.15)).mirror_x(), 0.05 * hs)    # eye turrets
        else:
            hd = hd.si(SDF(lambda p, y=hc[1] - 0.12 * hs: y - p[:, 1]), 0.05 * hs)
        hd = hd.su(sphere(0.08 * hs, hh(0, -0.04 + (0.04 if head == "croc" else 0), -0.27 - mz)), 0.06 * hs)   # nose
        hd = hd.ss(sphere(0.025 * hs, hh(0.05, 0.02, -0.33 - mz)).mirror_x(), 0.01 * hs)
        if head == "beaver":
            hd = hd.su(ellipsoid(0.2 * hs, 0.17 * hs, 0.17 * hs, hh(0.15, -0.08, -0.35)).mirror_x(), 0.1 * hs)   # cheeks
        if ears == "small":
            hd = hd.su(ellipsoid(0.08 * hs, 0.1 * hs, 0.05 * hs, hh(0.28, 0.28, 0.15)).mirror_x(), 0.05 * hs)
        elif ears == "dog":
            hd = hd.su(round_cone(hh(0.25, 0.25, 0.12), hh(0.36, 0.5, 0.22), 0.1 * hs, 0.03 * hs).mirror_x(), 0.05 * hs)
        if horns:
            hn = tube([hh(0.2, 0.25, 0.1), hh(0.32, 0.45, 0.4), hh(0.35, 0.5, 0.8), hh(0.3, 0.7, 1.0)], [0.08 * hs, 0.06 * hs, 0.04 * hs, 0.012 * hs], k=0.02)
            H.piece("Horns", "Head", hn.mirror_x(), col="horn", mat="hard", tris=600, role="horn", pri=1.5)
            fr = None
            for i in range(5):
                a = -0.9 + i * 0.45
                one = round_cone(hh(0.3 * math.sin(a), -0.15 + 0.2 * math.cos(a), 0.25), hh(0.55 * math.sin(a), -0.15 + 0.4 * math.cos(a) - 0.1, 0.45), 0.05 * hs, 0.012 * hs)
                fr = one if fr is None else fr | one
            web = MA.plate(hh(0, -0.05, 0.3), (1, 0, 0), (0, 1, 0.3), [(-0.5, -0.2), (-0.35, 0.2), (0.0, 0.35), (0.35, 0.2), (0.5, -0.2), (0.0, -0.05)], 0.03 * hs)
            H.piece("Frill", "Head", fr.su(web, 0.02 * hs), col="secondary", mat="skin", tris=700, role="crest", pri=1.4)
            hd = hd.su(tube([hh(0.12, -0.12, -0.6), hh(0.2, -0.3, -0.62), hh(0.26, -0.5, -0.55)], [0.035 * hs, 0.025 * hs, 0.012 * hs]).mirror_x(), 0.02 * hs)  # whisker barbels
        H.piece("HeadP", "Head", furry(hd, 0.4, 6), col="primary", tris=1800, res=128, role="head", pattern=pat)
        # jaw
        H.bone("Jaw", "Head", hh(0, -0.1, 0.05))
        jw = round_cone(hh(0, -0.18, 0.0), hh(0, -0.18 + (0.04 if head == "croc" else 0), -0.22 - mz), (m0 * 0.85) * hs, (m1 * 0.8) * hs)
        jw = jw.si(SDF(lambda p, y=hc[1] - (0.08 if head == "croc" else 0.14) * hs: p[:, 1] - y), 0.03 * hs)
        H.piece("JawP", "Jaw", furry(jw, 0.3, 7), col="primary" if head != "croc" else "belly", tris=700, role="jaw", pri=1.3, pattern=pat if head != "croc" else None)
        jaw = "Jaw"
        H.prim("Mouth", "Head", "Ellipsoid", ((m0 + m1) * 1.4 * hs, 0.05 * hs, (mz + 0.15) * hs), hh(0, -0.12 + (0.03 if head == "croc" else 0), -0.12 - mz * 0.5),
               col="mouth", mat="hard", role="mouth", pri=2.4)
        if head in ("croc", "dog", "dragon"):
            n_t = 7 if head == "croc" else 4
            yb = -0.08 if head == "croc" else -0.13
            tt = _teeth_row(hh(m0 * 0.85, yb, -0.2), hh(m1 * 0.9, yb, -0.18 - mz), n_t, 0.035 * hs, 0.09 * hs)
            H.piece("Teeth", "Head", tt.mirror_x(), col="tooth", mat="hard", tris=400, role="tooth", pri=2.0, ao=False, smooth=2)
        if incisors:
            ic = round_box(0.1 * hs, 0.12 * hs, 0.03 * hs, 0.02 * hs, hh(0, -0.2, -0.33 - mz))
            ic = ic.ss(box(0.006 * hs, 0.2 * hs, 0.1 * hs, hh(0, -0.25, -0.33 - mz)), 0.004 * hs)
            H.piece("Incisors", "Head", ic, col="accent", mat="hard", tris=300, role="tooth", pri=1.8, ao=False)
        if tusks > 0:
            tk = tube([hh(0.12, -0.2, -0.2 - mz * 0.6), hh(0.16, -0.45 * tusks, -0.26 - mz * 0.6), hh(0.12, -0.62 * tusks, -0.1 - mz * 0.6)],
                      [0.05 * hs, 0.04 * hs, 0.012 * hs])
            H.piece("Tusks", "Jaw", tk.mirror_x(), col="horn", mat="hard", tris=400, role="tooth", pri=1.8, ao=False)
        eyep = hh(0.16 if head == "croc" else 0.25, 0.2 + eye_up if head == "croc" else 0.12 + eye_up, -0.17 if head == "croc" else -0.2)
        er = 0.075 * eye * hs
        mouth = hh(0, -0.12, -0.35 - mz)
    H.eyes("Head", eyep, er, col="iris", pupil="slit" if head in ("croc", "dragon", "viper") else "round",
           look=(0.7 if head != "croc" else 0.6, 0.2 if head == "croc" else 0.0, -0.8))

    # ------------------------------------------------------------------ tail
    t0 = v(0, bodyY + 0.02, zr + 0.65 * BL)
    tb = []
    if tail == "paddle":
        dirs = [(0, -0.25, 1.0), (0, -0.25, 1.0), (0, -0.05, 1.0)]
        seg = [0.45, 0.5, 0.6]
    elif tail == "horse":
        dirs = [(0, -0.1, 1.0), (0, -0.9, 0.6), (0, -1.0, 0.2)]
        seg = [0.45, 0.4, 0.4]
    elif tail == "croc":
        dirs = [(0, -0.3, 1.0), (0, -0.25, 1.0), (0, -0.05, 1.0)]
        seg = [0.75, 0.75, 0.7]
    elif tail == "spiked":
        dirs = [(0, -0.45, 1.0), (0, -0.3, 1.0), (0.2, -0.1, 1.0)]
        seg = [0.45, 0.45, 0.45]
    else:  # thin long
        dirs = [(0, -0.15, 1.0), (0, -0.6, 1.0), (0, -0.2, 1.0)]
        seg = [0.6, 0.65, 0.65]
    pts = [t0]
    for d, ln in zip(dirs, seg):
        pts.append(pts[-1] + unit(d) * ln * TL * s)
    names = []
    rr = {"paddle": [0.2, 0.17, 0.14, 0.1], "horse": [0.16, 0.13, 0.1, 0.07], "croc": [0.4, 0.3, 0.2, 0.06],
          "spiked": [0.3, 0.22, 0.14, 0.04], "thin": [0.2, 0.15, 0.09, 0.04]}[tail]
    for i in range(3):
        nm = f"Tail{i + 1}"
        H.bone(nm, "Body" if i == 0 else f"Tail{i}", T(pts[i]))
        names.append(nm)
        a = pts[i] - (pts[i + 1] - pts[i]) * (0.35 if i == 0 else 0.08)
        st = 0.93 if i else 1.0
        sg = round_cone(T(a), T(pts[i + 1]), rr[i] * TR * s * st, rr[i + 1] * TR * s)
        col = "primary"
        tpat = pat
        if tail == "paddle" and i == 2:
            pad = ellipsoid(0.38 * TR * s, 0.07 * s, 0.6 * TL * s, T((pts[2] + pts[3]) / 2 + v(0, 0, 0.1)))
            sg = sg.su(pad, 0.06 * s)
            col = "dark"
            tpat = spots(0.09 * s, 0.035 * s, depth=0.35, ring=True, seed=11)
        if tail == "horse" and i == 2:
            sg = sg.su(ellipsoid(0.2 * s, 0.5 * s, 0.18 * s, T(pts[3] + v(0, -0.2, 0.05))).noise(0.05 * s, 8 / s, 2), 0.08 * s)
            col = "secondary"
        if tail == "spiked":
            sg = sg | round_cone(T((pts[i] + pts[i + 1]) / 2 + v(0, rr[i] * 0.6, 0)), T((pts[i] + pts[i + 1]) / 2 + v(0, rr[i] + 0.2, 0.1)), 0.07 * s, 0.01 * s)
        if tail == "croc" and scutes:
            for k in range(3):
                c = pts[i] + (pts[i + 1] - pts[i]) * (k + 0.5) / 3
                sg = sg.su(ellipsoid(0.06 * s, 0.09 * s, 0.1 * s, T(c + v(0, rr[i] * 0.85 * TR, 0))), 0.03 * s)
        H.piece(f"TailP{i + 1}", nm, furry(sg, 0.5, 8 + i), col=col, tris=600 if i == 0 else 450, role="tail", pri=1.5 + 0.1 * i, pattern=tpat)
    H.socket("mouth", mouth, "Jaw" if jaw else "Head")
    H.socket("head", hh(0, 0.45, 0), "Head")
    H.rig.update({"head": "Head", "neck": "Neck", "tail": names})
    if jaw:
        H.rig["jaw"] = jaw
    height = bodyY + 0.6
    if legs:
        H.rig["legs"] = [{"hip": l[0], "knee": l[1], "phase": l[3], "side": l[4]} for l in legs]
        MR.sprawl(H, legs, neck="Neck", head="Head", jaw=jaw, tail=names, stride=0.45, lift=0.5, walk=1.0, height=height,
                  attack=attack if attack in ("snap", "roll", "tailwhip") else "snap")
    else:
        H.rig["legs"] = [{"hip": l[0], "knee": l[1], "phase": l[3], "side": 1 if l[0].endswith("R") else -1} for l in qlegs]
        motion.quadruped(H, qlegs, neck="Neck", head="Head", jaw=jaw, tail=names, stride=0.4, walk=0.9, height=height,
                         attack=attack if attack in ("pounce", "gore", "bite") else "bite")
    return H


@hero("pakicetus", FAM)
def pakicetus():
    return _quad("pakicetus", leg=1.05, BL=0.95, G=0.78, head="dog", HS=1.15, ML=1.4, neck=1.0, tail="thin", TL=1.3, feet="paw",
                 LT=0.8, eye_up=0.08, attack="bite", ears="small", pat=mottle(0.3, 0.08, 0.15, 2), tags=["prehistoric", "whale"],
                 preview={"primary": "#8A7258", "secondary": "#D9C9AE", "iris": "#3A2A1A"})


@hero("ambulocetus", FAM)
def ambulocetus():
    return _quad("ambulocetus", leg=0.72, BL=1.3, G=0.95, sprawl=0.55, head="croc", HS=1.25, ML=1.05, neck=0.6, tail="croc", TL=1.1, TR=0.85,
                 feet="web", LT=1.0, flat=0.85, attack="snap", gait="sprawl", eye_up=0.05, pat=mottle(0.35, 0.1, 0.2, 5),
                 tags=["prehistoric", "whale"], preview={"primary": "#5E5A48", "secondary": "#C9C0A0", "iris": "#C9A030", "belly": "#B8AE90"})


@hero("platypus", FAM)
def platypus():
    return _quad("platypus", s=0.7, leg=0.55, BL=0.95, G=0.85, sprawl=0.65, flat=0.7, head="bill", HS=1.25, neck=0.35, tail="paddle",
                 TL=0.9, TR=1.4, feet="web", LT=0.75, fur=0.006, gait="sprawl", attack="snap", tags=["monotreme", "animal"],
                 preview={"primary": "#6B4A2E", "secondary": "#D7C3A0", "dark": "#2A2622", "iris": "#141414", "belly": "#B89A78"})


@hero("afanc", FAM)
def afanc():
    return _quad("afanc", s=1.15, leg=0.75, BL=1.25, G=1.05, sprawl=0.5, flat=0.85, head="beaver", HS=1.35, ML=1.0, neck=0.55, tail="paddle",
                 TL=1.25, TR=1.5, feet="claw", LT=1.05, incisors=True, scutes=True, fur=0.01, gait="sprawl", attack="roll",
                 pat=mottle(0.3, 0.09, 0.2, 6), tags=["lake monster", "welsh"],
                 preview={"primary": "#4A3A2C", "secondary": "#7A6A4A", "dark": "#2E2A26", "accent": "#D98A2A", "iris": "#C93A1A"})


@hero("bunyip", FAM)
def bunyip():
    return _quad("bunyip", s=1.1, leg=0.85, BL=1.15, G=1.15, head="dog", HS=1.3, ML=0.85, neck=0.7, tail="horse", TL=1.0, feet="flipper",
                 LT=1.15, tusks=1.0, fur=0.03, mane=True, ears="dog", attack="gore", gait="heavy", eye=0.9, belly=0.85,
                 tags=["swamp monster", "australian"],
                 preview={"primary": "#3A3530", "secondary": "#2A2622", "horn": "#E8DCC0", "iris": "#D9A020"})


@hero("dragon turtle", FAM)
def dragon_turtle():
    return _quad("dragon turtle", leg=0.6, BL=0.9, G=0.95, sprawl=0.45, shell=True, head="dragon", HS=1.35, ML=0.9, neck=0.8, tail="spiked",
                 TL=0.9, feet="column", LT=1.1, horns=True, eye=1.3, gait="sprawl", attack="snap", tags=["dragon", "turtle"],
                 preview={"primary": "#4F8A5A", "secondary": "#2F5A4A", "belly": "#E8D8A0", "horn": "#E8DCB0", "iris": "#E8B020"})



# ================================================================================================ helpers: rings
def ring(c, t, R, r):
    c = np.asarray(c, float)
    t = unit(t)

    def f(p):
        q = p - c
        h = q @ t
        rad = np.linalg.norm(q - h[:, None] * t, axis=1) - R
        return np.sqrt(rad * rad + h * h) - r

    return SDF(f)


SAND = [0.80, 0.68, 0.46]


# ================================================================================================ sandworm
@hero("sandworm", FAM)
def sandworm():
    H = Hero("sandworm", plan="Serpent", gait="slither", tags=["worm", "desert", "giant"])
    H.preview = {"primary": "#B08A5E", "secondary": "#6E4E36", "tooth": "#F2E8D2", "mouth": "#5A1E22"}
    H.body((0, 0.3, 0.6))
    ctrl = [V(0, -0.6, 0.7), V(0, 1.2, 0.75), V(0, 2.9, 0.45), V(0, 4.3, -0.25), V(0, 5.05, -1.25), V(0, 5.15, -2.15)]
    n = 50
    pts = catmull(ctrl, n)
    rad = [0.95 + 0.12 * (1 - i / (n - 1)) - 0.05 * math.sin(math.pi * i / (n - 1)) for i in range(n)]
    for i in range(n - 6, n):
        rad[i] = rad[i] * (1 + 0.12 * (i - n + 6) / 5)       # flared lip
    H.bone("Rise", "Body", T(pts[0] + V(0, 0.6, 0)))

    def rings(i, sub, rr):
        out = None
        for j in range(0, len(sub) - 1, 2):
            t = sub[j + 1] - sub[j]
            one = ring((sub[j] + sub[j + 1]) / 2, t, rr[j] * 0.97, 0.075)
            out = one if out is None else out | one
        return out

    end, prev = pts[-1], pts[-4]
    m = unit(end - prev)
    R = rad[-1]

    def rings_cut(i, sub, rr):
        out = rings(i, sub, rr)
        return out

    bones = chain(H, "Seg", "Rise", pts, rad, 5, col="primary", mat="skin", tris=1300, extra=rings_cut, role="body", pri=1.0,
                  pattern=combine(mottle(0.4, 0.12, 0.2, 7), gradient(1, 0.0, 4.0, 0.75, 1.0)), tri_scale=[1.2, 1.1, 1.0, 1.0, 1.4])
    # mouth: hollow the last segment, ring of inward teeth, a throat disc
    segs = [p for p in H.parts if p["name"].startswith("SegP")]
    segs[0]["sdf"] = segs[0]["sdf"] & plane((0, -1, 0), 0.05)
    segs[-1]["sdf"] = segs[-1]["sdf"].ss(capsule(T(end - m * 0.7), T(end + m * 0.6), R * 0.8), 0.08)
    up = unit(np.cross(m, V(1, 0, 0)))
    side = unit(np.cross(up, m))
    teeth = None
    for ringi, (dz, rr_, n_t) in enumerate(((-0.12, 0.88, 14), (-0.45, 0.72, 11), (-0.8, 0.58, 9))):
        for k in range(n_t):
            a = (k + 0.5 * ringi) / n_t * math.tau
            rv = side * math.cos(a) + up * math.sin(a)
            base = end + m * dz + rv * R * rr_
            tip = base - rv * R * 0.32 + m * 0.05 - m * 0.12
            one = round_cone(T(base), T(tip), 0.085, 0.012)
            teeth = one if teeth is None else teeth | one
    H.piece("Teeth", bones[-1], teeth, col="tooth", mat="hard", tris=1600, res=136, role="tooth", pri=1.6, ao=False, smooth=2)
    throat = ellipsoid(R * 0.75, R * 0.75, 0.08, (0, 0, 0))
    H.prim("Throat", bones[-1], "Ball", (R * 1.3, R * 1.3, R * 1.3), T(end - m * 0.75), col="mouth", mat="skin", role="mouth", pri=2.0)
    # three armoured petals hinged on the lip, half open
    petals = []
    for k in range(3):
        a = math.radians(90 + 120 * k)
        rv = side * math.cos(a) + up * math.sin(a)
        hinge = end + rv * R * 0.95 - m * 0.05
        H.bone(f"Petal{k + 1}", bones[-1], T(hinge))
        outward = unit(m * 1.0 + rv * 0.75)
        tip = hinge + outward * 1.35
        tang = unit(np.cross(m, rv))
        pet = MA.plate(T(hinge), T(outward), T(tang), [(-0.05, -0.95), (0.8, -0.9), (1.6, -0.35), (1.85, 0.0), (1.6, 0.35), (0.8, 0.9), (-0.05, 0.95)], 0.16,
                       bend=-0.25)
        pet = pet.su(ring(hinge + outward * 0.05, outward, 0.0001, 0.0001), 0.0) if False else pet
        for j in range(3):  # inner hooks
            c = hinge + outward * (0.45 + 0.35 * j) - rv * 0.06
            pet = pet | round_cone(T(c), T(c - rv * 0.28 - outward * 0.05), 0.06, 0.01)
        H.piece(f"PetalP{k + 1}", f"Petal{k + 1}", pet, col="secondary", mat="hard", tris=600, role="jaw", pri=1.2,
                pattern=stripes(lambda Q, o=hinge, d=outward: (Q - o) @ d, 3.0, width=0.25, depth=0.35))
        ax = unit(np.cross(m, rv))
        petals.append((f"Petal{k + 1}", (ax[0], ax[1], ax[2])))
    # burrow mound + scattered rocks (static on Body)
    mound = ellipsoid(2.1, 0.55, 2.0, (0, 0.0, 0.7)).ss(ellipsoid(1.05, 1.0, 1.05, (0, 0.35, 0.7)), 0.3)
    mound = mound.su(torus(1.35, 0.3).at(0, 0.3, 0.7), 0.3).noise(0.06, 3.0, 4) & plane((0, -1, 0), 0.0)
    H.piece("Mound", "Body", mound, col=SAND, mat="stone", tris=1500, role="ground", pri=0.9,
            pattern=mottle(0.3, 0.1, 0.18, 3))
    rocks = None
    for k, (x, z, r) in enumerate(((1.9, -0.3, 0.28), (-2.0, 0.2, 0.22), (1.5, 2.2, 0.2), (-1.4, 2.4, 0.3), (0.3, -1.4, 0.18))):
        one = sphere(r, (x, r * 0.4, z)).noise(0.04, 6, k)
        rocks = one if rocks is None else rocks | one
    H.piece("Rocks", "Body", rocks & plane((0, -1, 0), 0.0), col="stone", mat="stone", tris=600, role="ground", pri=2.4)
    H.socket("mouth", T(end + m * 0.3), bones[-1])
    H.socket("head", T(end + up * R), bones[-1])
    H.rig.update({"head": bones[-1], "tail": bones})
    MS.worm(H, bones, petals=petals, root="Rise", height=5.0)
    return H


# ================================================================================================ ittan-momen
def twisted_strip(points, twist, W, th):
    """A flat cloth strip along a polyline: half width W, half thickness th, the width axis rotated by twist[i]
    (radians) about the tangent. Rounded edges and ends."""
    P = [np.asarray(p, float) for p in points]
    segs = []
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]
        d = b - a
        L = float(np.linalg.norm(d))
        if L < 1e-6:
            continue
        dr = d / L
        lat = np.cross(V(0, 1, 0), dr)
        if np.linalg.norm(lat) < 1e-4:
            lat = V(1, 0, 0)
        lat = lat / np.linalg.norm(lat)
        ver = np.cross(dr, lat)
        segs.append((a, dr, L, lat, ver, twist[i], twist[i + 1]))

    def f(p):
        out = None
        for a, dr, L, lat, ver, t0, t1 in segs:
            q = p - a
            al = q @ dr
            t = np.clip(al / L, 0, 1)
            ang = t0 + (t1 - t0) * t
            c, s_ = np.cos(ang), np.sin(ang)
            x0, y0 = q @ lat, q @ ver
            x = c * x0 + s_ * y0
            y = -s_ * x0 + c * y0
            over = al - t * L
            dx = np.maximum(np.abs(x) - (W - th), 0)
            d = np.sqrt(dx * dx + y * y + over * over) - th
            out = d if out is None else np.minimum(out, d)
        return out

    return SDF(f)


@hero("ittan-momen", FAM)
def ittan_momen():
    H = Hero("ittan-momen", plan="Serpent", gait="fly", tags=["yokai", "cloth", "flying"])
    H.preview = {"primary": "#F2ECDC", "secondary": "#D8CDB0", "pupil": "#1A1A1A"}
    H.body((0, 2.4, 0.0))
    ctrl = [V(0, 3.7, -1.35), V(0, 2.9, -1.3), V(0, 2.2, -0.75), V(0, 2.05, 0.3), V(0, 2.45, 1.4), V(0, 2.1, 2.6), V(0, 1.55, 3.6), V(0, 1.7, 4.6)]
    n = 56
    pts = catmull(ctrl, n)
    W = 0.62
    tw = {}
    for i in range(n):   # twist (radians about the strip's tangent) so the broad face shows from every side
        u = i / (n - 1)
        tw[i] = 0.0 if u < 0.15 else 0.9 * math.sin(math.pi * (u - 0.15) / 0.85 * 1.6)

    def strip(sub, i0):
        return twisted_strip(sub, [tw[i0 + j] for j in range(len(sub))], W, 0.045)

    N = len(pts)
    nseg = 6
    cuts = [int(round(i * (N - 1) / nseg)) for i in range(nseg + 1)]
    bones = []
    for i in range(nseg):
        b = f"Cloth{i + 1}"
        H.bone(b, "Body" if i == 0 else bones[-1], T(pts[cuts[i]]))
        bones.append(b)
    # Body sits on the 2nd third; Cloth1 is the head end (child bones run toward the tail end)
    weave = stripes(lambda Q: Q[:, 0] * 6 + 0 * Q[:, 2], 1.0, width=0.12, depth=0.08)
    for i in range(nseg):
        a, b = cuts[i], cuts[i + 1]
        a0 = max(0, a - (1 if i else 0))
        sub = pts[a0:b + 1]
        sd = strip(sub, a0)
        if i > 0:
            sd = sd.round(-0.006)
        if i == nseg - 1:   # frayed end
            fr = None
            for k in range(7):
                x = -W * 0.85 + k * W * 0.28
                one = round_cone((x, pts[-1][1], pts[-1][2] - 0.05), (x * 1.05, pts[-1][1] - 0.05, pts[-1][2] + 0.25), 0.03, 0.015)
                fr = one if fr is None else fr | one
            sd = sd | fr
        H.piece(f"ClothP{i + 1}", bones[i], sd, col="primary", mat="cloth", tris=700, role="body", pri=1.0 + 0.05 * i, pattern=weave)
    # little cloth arms near the head end
    arms = []
    base = pts[6]
    for sx, nm in ((1, "R"), (-1, "L")):
        H.bone("Arm" + nm, bones[0], T(base + V(sx * W * 0.8, 0, 0.02)))
        arm = MR.eloft([T(base + V(sx * W * 0.7, 0, 0.03)), T(base + V(sx * (W + 0.35), -0.15, -0.05)), T(base + V(sx * (W + 0.6), -0.4, -0.15))],
                       [0.12, 0.1, 0.08], [0.025, 0.025, 0.025])
        H.piece("ClothArm" + nm, "Arm" + nm, arm, col="primary", mat="cloth", tris=300, role="limb", pri=1.5,
                key=f"h_ittan-momen_arm{'' if sx > 0 else '_l'}")
        arms.append(("Arm" + nm, sx))
    # eyes on the front face of the raised head end
    ep = pts[2]
    t = unit(pts[1] - pts[3])
    fwd = unit(np.cross(V(1, 0, 0), t))
    if fwd[2] > 0:
        fwd = -fwd
    for sx, nm in ((1, "R"), (-1, "L")):
        c = ep + V(sx * 0.17, 0, 0) + fwd * 0.03
        H.prim("Eye" + nm, bones[0], "Ellipsoid", (0.14, 0.09, 0.03), T(c), col="eyeWhite", mat="hard", role="eye", pri=1.2)
        H.prim("Pupil" + nm, bones[0], "Ball", (0.07, 0.07, 0.03), T(c + fwd * 0.012 + V(-sx * 0.01, 0, 0)), col="pupil", mat="hard", role="pupil", pri=1.3)
    H.socket("mouth", T(ep + fwd * 0.2), bones[0])
    H.socket("head", T(pts[0]), bones[0])
    H.rig.update({"head": bones[0], "tail": bones[1:]})
    MS.ribbon(H, bones, arms=arms, height=3.0)
    return H


# ================================================================================================ tsuchinoko
@hero("tsuchinoko", FAM)
def tsuchinoko():
    H = Hero("tsuchinoko", plan="Serpent", gait="slither", tags=["yokai", "snake", "cryptid"])
    H.preview = {"primary": "#7A6440", "secondary": "#3E3222", "belly": "#D8C89A", "iris": "#E0B020"}
    s = 1.0
    ctrl = [V(0, 0.42, -1.25), V(0.08, 0.5, -0.6), V(0, 0.58, 0.1), V(-0.12, 0.5, 0.75), V(0.05, 0.3, 1.3), V(0.3, 0.15, 1.75), V(0.45, 0.1, 2.05)]
    n = 40
    pts = catmull(ctrl, n)
    rad = []
    for i in range(n):
        u = i / (n - 1)
        r = 0.24 + 0.2 * math.sin(math.pi * min(u / 0.68, 1.0)) ** 0.8 if u < 0.68 else 0.24 * (1 - (u - 0.68) / 0.32) ** 1.2 + 0.035
        rad.append(r)
    for i in range(n):
        pts[i][1] = max(pts[i][1], rad[i] * 0.95)
    H.body(T(pts[18]))
    pat = combine(spots(0.24, 0.09, depth=0.6, seed=13), topshade(0.1, 0.9, 1.0, 0.7))
    flat = SDF(lambda p: -p[:, 1] + 0.0)
    H.bone("Neck", "Body", T(pts[10]))
    H.piece("FrontP", "Neck", tube([T(pts[j]) for j in (2, 5, 8, 11, 14, 17)], [rad[j] for j in (2, 5, 8, 11, 14, 17)]) & plane((0, -1, 0), 0.0),
            col="primary", tris=1200, pattern=pat)
    H.piece("BodyP", "Body", tube([T(pts[j]) for j in (16, 19, 22, 25, 27)], [rad[j] * (0.95 if j == 16 else 1) for j in (16, 19, 22, 25, 27)]) & plane((0, -1, 0), 0.0),
            col="primary", tris=1400, pattern=pat)
    tb = chain(H, "Tail", "Body", pts[26:], rad[26:], 3, col="primary", tris=450, pattern=pat, shrink=0.92)
    # wide viper head
    hc = pts[1] + V(0, 0.08, -0.2)
    H.bone("Head", "Neck", T(pts[2]))
    hd = ellipsoid(0.42, 0.24, 0.5, T(hc))
    hd = hd.su(ellipsoid(0.24, 0.15, 0.2, T(hc + V(0, -0.01, -0.35))), 0.12)
    hd = hd.su(capsule(T(hc + V(0.16, 0.12, -0.25)), T(hc + V(0.24, 0.1, 0.05)), 0.06).mirror_x(), 0.06)
    hd = hd.si(SDF(lambda p, y=hc[1] - 0.06: y - p[:, 1]), 0.03)
    hd = hd.ss(sphere(0.02, T(hc + V(0.07, 0.04, -0.52))).mirror_x(), 0.01)
    H.piece("HeadP", "Head", hd, col="primary", tris=1100, role="head", pattern=pat)
    H.bone("Jaw", "Head", T(hc + V(0, -0.06, 0.25)))
    jw = ellipsoid(0.3, 0.1, 0.42, T(hc + V(0, -0.1, -0.05))).si(SDF(lambda p, y=hc[1] - 0.09: p[:, 1] - y), 0.02)
    H.piece("JawP", "Jaw", jw, col="belly", tris=500, role="jaw", pri=1.3)
    H.prim("Mouth", "Head", "Ellipsoid", (0.4, 0.04, 0.6), T(hc + V(0, -0.08, -0.12)), col="mouth", mat="hard", role="mouth", pri=2.4)
    fg = round_cone(T(hc + V(0.12, -0.07, -0.4)), T(hc + V(0.12, -0.2, -0.43)), 0.025, 0.006)
    H.piece("Fangs", "Head", fg.mirror_x(), col="tooth", mat="hard", tris=200, role="tooth", pri=2.2, ao=False)
    H.eyes("Head", T(hc + V(0.3, 0.1, -0.25)), 0.075, col="iris", pupil="slit", look=(1.0, 0.2, -0.6))
    H.bone("Tongue", "Head", T(hc + V(0, -0.06, -0.45)))
    H.piece("TongueP", "Tongue", tube([T(hc + V(0, -0.06, -0.4)), T(hc + V(0, -0.07, -0.62)), T(hc + V(0.04, -0.06, -0.72))], [0.02, 0.016, 0.008]) |
            round_cone(T(hc + V(0, -0.07, -0.62)), T(hc + V(-0.04, -0.06, -0.72)), 0.016, 0.008), col="tongue", tris=200, role="tongue", pri=2.3)
    H.socket("mouth", T(hc + V(0, -0.05, -0.55)), "Head")
    H.socket("head", T(hc + V(0, 0.25, 0)), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": tb})
    MR.slither(H, tb, fore=["Neck"], head="Head", jaw="Jaw", tongue=("Tongue", 0.12, (0, 0, 1)), amp=0.25, waves=0.8, walk=1.0, height=0.8)
    return H


# ================================================================================================ tentacle monster
@hero("tentacle monster", FAM)
def tentacle_monster():
    H = Hero("tentacle monster", plan="Octopus", gait="slither", tags=["tentacle", "monster", "alien"])
    H.preview = {"primary": "#5E3A78", "secondary": "#B8E07A", "iris": "#E8D040", "eyeWhite": "#F4F0E0", "tooth": "#F2EAD0"}
    bc = V(0, 2.55, 0.15)
    H.body(T(bc))
    pat = combine(spots(0.38, 0.13, depth=0.45, seed=21), topshade(1.5, 3.8, 1.0, 0.82))
    bd = ellipsoid(1.2, 1.05, 1.15, T(bc + V(0, 0.15, 0.1)))
    bd = bd.su(ellipsoid(0.9, 0.55, 0.85, T(bc + V(0, -0.65, 0.0))), 0.4)
    for k in range(5):   # lumpy warts
        a = k * 1.3
        bd = bd.su(sphere(0.32, T(bc + V(0.9 * math.sin(a), 0.55 + 0.2 * math.cos(a * 2), 0.6 * math.cos(a) + 0.2))), 0.3)
    bd = bd.ss(sphere(0.62, T(bc + V(0, 0.32, -1.02))), 0.12)                       # eye socket
    bd = bd.ss(sphere(0.34, T(bc + V(0, -0.55, -0.95))), 0.1)                      # mouth hole
    bd = bd.su(ring(bc + V(0, -0.55, -0.98), V(0, -0.2, -1), 0.32, 0.09), 0.06)    # mouth lip
    bd = bd.su(ring(bc + V(0, 0.32, -0.98), V(0, 0, -1), 0.6, 0.11), 0.08)        # eyelid rim
    H.piece("BodyP", "Body", bd, col="primary", tris=2600, res=144, pattern=pat)
    tt = None
    for k in range(10):
        a = k / 10 * math.tau
        rv = V(math.cos(a), math.sin(a) * 0.9, 0)
        c = bc + V(0, -0.55, -1.0) + rv * 0.28
        one = round_cone(T(c), T(c - rv * 0.17 + V(0, 0, 0.12)), 0.05, 0.01)
        tt = one if tt is None else tt | one
    H.piece("Teeth", "Body", tt, col="tooth", mat="hard", tris=500, role="tooth", pri=1.8, ao=False, smooth=2)
    H.prim("Gullet", "Body", "Ball", (0.5, 0.5, 0.3), T(bc + V(0, -0.55, -0.82)), col="mouth", mat="skin", role="mouth", pri=2.0)
    eye = bc + V(0, 0.32, -0.88)
    H.prim("Eye", "Body", "Ball", (1.05, 1.05, 1.05), T(eye), col="eyeWhite", mat="hard", role="eye", pri=1.1)
    H.prim("Iris", "Body", "Ball", (0.62, 0.62, 0.62), T(eye + V(0, 0, -0.26)), col="iris", mat="hard", role="eye", pri=1.2)
    H.prim("Pupil", "Body", "Ellipsoid", (0.16, 0.48, 0.2), T(eye + V(0, 0, -0.45)), col="pupil", mat="hard", role="pupil", pri=1.3)
    H.prim("Shine", "Body", "Ball", (0.14, 0.14, 0.14), T(eye + V(0.14, 0.17, -0.47)), col="shine", mat="hard", role="shine", pri=2.6)
    pat2 = combine(pat, gradient(1, 0.0, 2.0, 0.8, 1.0))
    arms = []
    for j, a in enumerate((35, 90, 145)):
        th = math.radians(a)
        d = V(math.sin(th), 0, -math.cos(th))
        lat = unit(np.cross(V(0, 1, 0), d))
        root = bc + V(0, -0.8, 0.05) + d * 0.55
        ctrl = [root, root + d * 0.7 + V(0, -0.8, 0), root + d * 1.3 + V(0, -1.65, 0) + lat * 0.2, root + d * 2.1 + V(0, -1.6, 0),
                root + d * 2.6 + V(0, -1.2, 0) - lat * 0.2, root + d * 2.5 + V(0, -0.75, 0)]
        pts = catmull(ctrl, 30)
        rad = taper(30, 0.36, 0.06, 0.9)
        for i in range(30):
            pts[i][1] = max(pts[i][1], rad[i] * 0.9)
        ex = (lambda i, sub, rr, lat=lat: suckers(sub, rr, lat, size=0.3, start=2 if i == 0 else 0))
        bns = chain(H, f"Leg{j}#_", "Body", pts, rad, 2, col="primary", tris=700, mirror=True, extra=ex, pattern=pat2, role="limb")
        arms.append(([b.replace("#", "R") for b in bns], (d[0], d[2])))
        arms.append(([b.replace("#", "L") for b in bns], (-d[0], d[2])))
    slam = []
    for j, (x, z, h) in enumerate(((0.5, 0.25, 1.0), (0.75, 0.75, 0.8))):
        root = bc + V(x, 0.85, z)
        d = unit(V(x, 0, -0.6 + z * 0.3))
        dd = V(d[0], 0, d[2])
        ctrl = [root, root + V(0.3 * x, 0.8 * h, -0.1), root + V(0.55 * x, 1.45 * h, -0.45), root + V(0.5 * x, 1.75 * h, -1.0), root + V(0.35 * x, 1.6 * h, -1.4)]
        pts = catmull(ctrl, 26)
        rad = taper(26, 0.2, 0.04)
        bns = chain(H, f"Feel{j}#_", "Body", pts, rad, 2, col="secondary", tris=500, mirror=True, role="limb", pri=1.4,
                    extra=(lambda i, sub, rr: sphere(rr[-1] * 2.2, T(sub[-1])) if i == 1 else None))
        slam.append(([b.replace("#", "R") for b in bns], (0.0, -1.0)))
        slam.append(([b.replace("#", "L") for b in bns], (0.0, -1.0)))
    H.socket("mouth", T(bc + V(0, -0.55, -1.15)), "Body")
    H.socket("head", T(bc + V(0, 1.3, 0)), "Body")
    H.rig.update({"head": "Body"})
    MS.writhe(H, arms, slammers=slam, height=3.0, walk=1.3, slam_k=0.8)
    return H


# ================================================================================================ hippocampus (mount)
LEATHER_RGB = [0.42, 0.27, 0.15]


@hero("hippocampus", FAM)
def hippocampus():
    H = Hero("hippocampus", plan="Fish", gait="swim", tags=["mount", "sea horse", "mythic"])
    H.preview = {"primary": "#3E8FA0", "secondary": "#7FD0C0", "hoof": "#2E4A50", "iris": "#202020", "belly": "#D8EEE8"}
    by = 2.45
    H.body((0, by, 0.0))
    shade = combine(topshade(by - 0.7, by + 0.8, 1.0, 0.8), mottle(0.3, 0.07, 0.12, 9))
    scales = combine(spots(0.14, 0.06, depth=0.3, ring=True, seed=2), topshade(1.0, 3.0, 1.0, 0.78))
    tor = ellipsoid(0.62, 0.72, 1.0, (0, by + 0.02, -0.35))
    tor = tor.su(ellipsoid(0.55, 0.62, 0.5, (0, by + 0.25, -0.95)), 0.3)                       # chest / withers
    tor = tor.su(ellipsoid(0.32, 0.4, 0.4, (0.42, by - 0.1, -0.85)).mirror_x(), 0.2)          # shoulders
    tor = tor.su(ellipsoid(0.5, 0.55, 0.7, (0, by - 0.1, 0.55)), 0.35)                         # waist into tail
    tor = tor.su(round_cone((0, by + 0.3, -1.0), (0, by + 0.95, -1.55), 0.5, 0.38), 0.25)       # neck root
    H.piece("Torso", "Body", tor, col="primary", tris=2400, res=128, pattern=shade)
    # neck + head
    H.bone("Neck", "Body", (0, by + 0.6, -1.25))
    neck = tube([(0, by + 0.6, -1.25), (0, by + 1.15, -1.6), (0, by + 1.62, -1.78)], [0.4, 0.32, 0.27], k=0.1)
    neck = neck.su(ellipsoid(0.28, 0.5, 0.3, (0, by + 0.8, -1.6)), 0.15)
    H.piece("NeckP", "Neck", neck, col="primary", tris=1100, role="limb", pattern=shade)
    hp = V(0, by + 1.7, -1.85)
    H.bone("Head", "Neck", T(hp))

    def h(x, y, z):
        return T(hp + V(x, y, z))

    hd = ellipsoid(0.25, 0.26, 0.3, h(0, 0.0, -0.1))
    hd = hd.su(round_cone(h(0, -0.08, -0.3), h(0, -0.48, -0.78), 0.2, 0.15), 0.15)
    hd = hd.su(ellipsoid(0.16, 0.18, 0.19, h(0, -0.55, -0.83)), 0.08)
    hd = hd.su(ellipsoid(0.13, 0.2, 0.22, h(0.1, -0.22, -0.12)).mirror_x(), 0.1)      # jowls
    hd = hd.ss(sphere(0.05, h(0.09, -0.58, -0.98)).mirror_x(), 0.02)                  # nostrils
    hd = hd.ss(capsule(h(-0.1, -0.7, -0.9), h(0.1, -0.7, -0.9), 0.015), 0.01)        # mouth line
    hd = hd.ss(sphere(0.06, h(0.22, 0.0, -0.3)).mirror_x(), 0.02)
    H.piece("HeadP", "Head", hd, col="primary", tris=1800, res=128, role="head", pattern=shade)
    H.eyes("Head", h(0.215, 0.0, -0.3), 0.06, col="iris", pupil=None, look=(1.0, 0.0, -0.4))
    fe = MA.plate(h(0.15, 0.22, -0.02), (0.3, 1, 0.3), (0, 0, 1), [(0, -0.1), (0.35, -0.12), (0.5, 0.05), (0.3, 0.1), (0, 0.1)], 0.04)
    H.mpiece("FinEar#", "Head", fe, col="secondary", tris=300, role="ear", pri=1.4)
    # fin mane along the neck
    pts = [(-1.95, by + 2.0), (-1.75, by + 1.75), (-1.55, by + 1.35), (-1.3, by + 1.0), (-1.0, by + 0.8)]
    poly = [(z + 0.05, y - 0.05) for z, y in pts] + [(-0.95, by + 1.1), (-1.15, by + 1.45), (-1.3, by + 1.5), (-1.42, by + 1.85), (-1.62, by + 1.95), (-1.8, by + 2.3), (-2.0, by + 2.2)]
    mane = MA.plate((0, 0, 0), (0, 0, 1), (0, 1, 0), poly, 0.07, smooth=1)
    for k in range(6):
        z = -1.92 + k * 0.18
        yb = by + 1.98 - k * 0.22
        mane = mane | round_cone((0, yb - 0.1, z), (0, yb + 0.3, z + 0.18), 0.04, 0.012)
    H.piece("FinMane", "Neck", mane, col="secondary", tris=900, role="mane", pri=1.2,
            pattern=MA.par_lines((0, 0, 1), 5.5, depth=0.25))
    # bridle + reins
    br = ring(hp + V(0, -0.5, -0.72), V(0, 0.35, -1), 0.19, 0.025) | ring(hp + V(0, -0.1, -0.2), V(0, -0.2, -1), 0.27, 0.025)
    br = br | capsule(h(0.2, -0.12, -0.22), h(0.17, -0.45, -0.66), 0.022).mirror_x()
    H.piece("Bridle", "Head", br, col=LEATHER_RGB, mat="cloth", tris=500, role="tack", pri=1.6)
    rn = tube([h(0.18, -0.55, -0.75), h(0.3, -0.75, -0.4), (0.3, by + 0.75, -0.7), (0.22, by + 0.82, -0.45)], [0.02, 0.02, 0.02, 0.02], k=0.02)
    H.piece("Reins", "Neck", rn.mirror_x(), col=LEATHER_RGB, mat="cloth", tris=400, role="tack", pri=1.7)
    # saddle + blanket + girth
    sy = by + 0.72
    bl = ellipsoid(0.68, 0.12, 0.62, (0, sy - 0.02, -0.25)) & SDF(lambda p: (sy - 0.12) - p[:, 1])
    bl = (tor.round(0.03) & ellipsoid(0.85, 0.5, 0.62, (0, sy - 0.05, -0.25)))
    H.piece("Blanket", "Body", bl, col="secondary", mat="cloth", tris=700, role="tack", pri=1.3)
    sd = round_box(0.36, 0.1, 0.45, 0.08, (0, sy + 0.08, -0.22))
    sd = sd.su(ellipsoid(0.2, 0.18, 0.1, (0, sy + 0.2, -0.65)), 0.08)        # pommel
    sd = sd.su(ellipsoid(0.3, 0.2, 0.1, (0, sy + 0.22, 0.2)), 0.1)            # cantle
    sd = sd.ss(ellipsoid(0.28, 0.08, 0.32, (0, sy + 0.2, -0.22)), 0.05)
    H.piece("Saddle", "Body", sd, col=LEATHER_RGB, mat="cloth", tris=800, role="tack", pri=1.2)
    gi = (tor.round(0.025) & SDF(lambda p: np.abs(p[:, 2] + 0.1) - 0.09)) & SDF(lambda p: p[:, 1] - (sy - 0.1))
    H.piece("Girth", "Body", gi, col=LEATHER_RGB, mat="cloth", tris=500, role="tack", pri=1.5)
    # forelegs ending in finned hooves
    legs = []
    for sx, nm in ((1, "R"), (-1, "L")):
        sh = V(0.4 * sx, by - 0.15, -0.85)
        kn = V(0.42 * sx, by - 0.85, -1.15)
        ft = V(0.42 * sx, by - 1.45, -1.0)
        H.bone("Shoulder" + nm, "Body", T(sh))
        H.bone("Knee" + nm, "Shoulder" + nm, T(kn))
        H.bone("Fet" + nm, "Knee" + nm, T(ft))
        k = "" if sx > 0 else "_l"
        up = round_cone(T(sh + V(0, 0.15, 0)), T(kn), 0.27, 0.13).su(ellipsoid(0.2, 0.35, 0.25, T(sh + V(0, -0.25, -0.05))), 0.1)
        H.piece("UpperLeg" + nm, "Shoulder" + nm, up, col="primary", tris=600, role="limb", pattern=shade, key=f"h_hippocampus_upper{k}")
        lo = round_cone(T(kn), T(ft), 0.13, 0.09).su(sphere(0.12, T(kn)), 0.04)
        H.piece("Cannon" + nm, "Knee" + nm, lo, col="primary", tris=450, role="limb", pattern=shade, key=f"h_hippocampus_cannon{k}")
        hf = round_cone(T(ft), T(ft + V(0, -0.2, -0.12)), 0.1, 0.13)
        fin = MA.plate(T(ft + V(0, -0.15, -0.05)), (0, -0.4, -1), (1, 0, 0), [(-0.05, -0.18), (0.4, -0.32), (0.55, 0.0), (0.4, 0.32), (-0.05, 0.18)], 0.05)
        H.piece("FinHoof" + nm, "Fet" + nm, hf, col="hoof", mat="hard", tris=300, role="hoof", pri=1.5, key=f"h_hippocampus_hoof{k}")
        H.piece("HoofFin" + nm, "Fet" + nm, fin, col="secondary", tris=300, role="fin", pri=1.6, key=f"h_hippocampus_hooffin{k}")
        legs.append(("Shoulder" + nm, "Knee" + nm, "Fet" + nm, 0.0 if sx > 0 else 0.5))
    # fish tail
    ctrl = [V(0, by - 0.1, 0.55), V(0, by - 0.35, 1.45), V(0, by - 0.95, 2.3), V(0, by - 1.15, 3.2), V(0, by - 0.8, 4.0), V(0, by - 0.15, 4.55)]
    pts3 = catmull(ctrl, 40)
    rad3 = [0.55 * (1 - 0.8 * (i / 39) ** 1.1) for i in range(40)]

    def tfin(i, sub, rr):
        out = None
        if i == 0:   # dorsal fin
            m = len(sub) // 2
            t = unit(sub[-1] - sub[0])
            up = unit(V(0, 1, 0) - t * t[1])
            out = MA.plate(T(sub[m] + up * rr[m] * 0.8), T(t), T(up), [(-0.5, 0), (-0.2, 0.5), (0.3, 0.42), (0.55, 0.0)], 0.06)
        if i == 3:
            t = unit(sub[-1] - sub[-3])
            fk = MA.plate(T(sub[-1] - t * 0.1), (1, 0, 0), T(t), [(0, -0.1), (0.5, 0.2), (0.95, 0.75), (0.75, 0.3), (0.8, 0.0), (0.0, 0.05),
                                                                 (-0.8, 0.0), (-0.75, 0.3), (-0.95, 0.75), (-0.5, 0.2)], 0.07, smooth=1)
            out = fk if out is None else out | fk
        return out

    tb = chain(H, "Tail", "Body", pts3, rad3, 4, col="primary", tris=900, extra=tfin, pattern=scales, role="tail", pri=1.3)
    # pectoral side fins at the waist
    pf = MA.plate((0.5, by - 0.2, 0.45), (1, -0.3, 0.5), (0, 0, 1), [(0, -0.2), (0.55, -0.1), (0.75, 0.25), (0.35, 0.3), (0, 0.2)], 0.05)
    H.mbone("SideFin#", "Body", (0.5, by - 0.2, 0.45))
    H.mpiece("SideFinP#", "SideFin#", pf, col="secondary", tris=300, role="fin", pri=1.5)
    H.socket("mouth", h(0, -0.6, -0.95), "Head")
    H.socket("head", h(0, 0.3, -0.1), "Head")
    H.socket("seat", (0, sy + 0.2, -0.22), "Body")
    H.mount = {"seat": "Saddle", "saddle": {"pos": (0, sy + 0.12, -0.22), "size": (0.9, 0.18, 1.0)}}
    H.rig.update({"head": "Head", "neck": "Neck", "tail": tb,
                  "legs": [{"hip": "ShoulderR", "knee": "KneeR", "phase": 0.0, "side": 1}, {"hip": "ShoulderL", "knee": "KneeL", "phase": 0.5, "side": -1}]})
    MS.hippo(H, legs, tb, neck="Neck", head="Head", fins=[("SideFinR", 1), ("SideFinL", -1)], height=4.0)
    return H


# word -> hero rules (tools/meshgen/heroes/map.py)
SEA = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Plant", "Weather", "Structure", "Person"]}
MAP = [
    ("lamia", "lamia, lamias, snake woman, snake lady, serpent woman, serpent lady, snake queen, snake person, snakefolk, "
              "yuan-ti, yuan ti", SEA),
    ("melusine", "melusine, melusina, dragon maiden, sea dragon maiden", SEA),
    ("shahmaran", "shahmaran, shahmeran, serpent queen, snake goddess, queen of serpents, queen of snakes", SEA),
    ("mami wata", "mami wata, mamiwata, mamy wata, water mother, water spirit queen", SEA),
    ("medusa", "medusa, gorgon, gorgons, stheno, euryale", SEA),
    ("iara", "iara, yara, uiara, mae d'agua, mother of waters", SEA),
    ("merrow", "merrow, merrows, murrough, merrow man", SEA),
    ("amabie", "amabie, amabiko", SEA),
    ("ichthyosaurus", "ichthyosaurus, ichthyosaur, ichthyosaurs, shonisaurus, temnodontosaurus, ophthalmosaurus, mixosaurus", SEA),
    ("pliosaurus", "pliosaurus, pliosaur, pliosaurs, liopleurodon, kronosaurus", SEA),
    ("pakicetus", "pakicetus, indohyus", SEA),
    ("ambulocetus", "ambulocetus, walking whale, rodhocetus", SEA),
    ("platypus", "platypus, platypuses, duck-billed platypus, duckbill platypus, duck billed platypus", SEA),
    ("afanc", "afanc, addanc, avanc", SEA),
    ("bunyip", "bunyip, bunyips", SEA),
    ("dragon turtle", "dragon turtle, dragon turtle hatchling, baby dragon turtle, dragonturtle", SEA),
    ("sandworm", "sandworm, sand worm, sandworms, death worm, mongolian death worm, mongolian worm, sand worm hatchling, giant worm, desert worm, "
                 "great worm, purple worm, burrower, graboid, kaiju worm, space worm", SEA),
    ("ittan-momen", "ittan-momen, ittan momen, ittanmomen, flying cloth, living scarf", SEA),
    ("tsuchinoko", "tsuchinoko, bachi hebi, nozuchi", SEA),
    ("tentacle monster", "tentacle monster, tentacle alien, tentacle, tentacles, tentacle beast, tentacle horror, tentacled horror, "
                         "tentacle creature", SEA),
    ("hippocampus", "hippocampus, hippocampi, hippocamp, sea horse steed, seahorse steed, sea steed, kelpie of the sea, sea stallion", SEA),
    ("kraken", "kraken, kraken king, space kraken, krakens, kraken spawn, baby kraken pet, kraken tentacle, giant kraken, sea kraken", SEA),
]
