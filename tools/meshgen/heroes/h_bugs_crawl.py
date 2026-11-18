"""Bugs (crawlers): centipede, millipede, caterpillar, earthworm (a chain of segment bones from the head back, each
segment its own piece; centipede / millipede leg pairs on their own bones swinging in a metachronal wave), and snail /
slug (a gliding muscular foot, eye stalks, a logarithmic-spiral shell)."""
import math

import numpy as np

import sdf as S
from sdf import sphere, ellipsoid, capsule, round_cone, tube, torus  # noqa: F401
from kit import Hero, hero, stripes, spots, gradient, combine  # noqa: F401
import motion_bugs as MB
from bugkit import *  # noqa: F401,F403


def _chain(H, n, z0, dz, y):
    """Segment bones Seg1..SegN: Seg1 at the front (child of Body), each next one a child of the previous, pivots at
    the front edge of each segment. Returns (bone names, segment centres z)."""
    segs, zc = [], []
    par = "Body"
    for i in range(n):
        z = z0 + i * dz
        b = H.bone(f"Seg{i + 1}", par, (0, y, z - dz * 0.5))
        segs.append(b)
        zc.append(z)
        par = b
    return segs, zc


# ================================================================================================ centipede / millipede
def _myriapod(hid, kind="centipede", preview=None):
    milli = kind == "millipede"
    H = Hero(hid, plan="Worm", gait="scuttle", tags=["bug", "myriapod"] + ([] if milli else ["venomous"]))
    H.preview = preview or {}
    n = 13 if milli else 12
    dz = 0.3 if milli else 0.38
    y = 0.38 if milli else 0.4
    z0 = -(n - 1) * dz * 0.5
    H.body((0, y, z0))
    segs, zc = _chain(H, n, z0, dz, y)
    legb = []
    for i, (b, z) in enumerate(zip(segs, zc)):
        t = i / (n - 1)
        if milli:
            w = 0.3 * (1 - 0.25 * max(0, t - 0.75) * 4)
            sd = ellipsoid(w, w * 0.95, dz * 0.68, (0, y, z)).su(ellipsoid(w * 1.02, w * 0.6, dz * 0.4, (0, y + 0.05, z - dz * 0.15)), 0.05)
            if i == n - 1:
                sd = sd.su(sphere(w * 0.7, (0, y - 0.02, z + dz * 0.45)), 0.08)
            pat = lambda P, z=z: 1 - 0.5 * np.clip(1 - np.abs(P[:, 2] - z + dz * 0.42) / 0.05, 0, 1)
            col = "primary"
        else:
            w = 0.4 * (1 - 0.3 * max(0, t - 0.8) * 5) * (0.85 if i == 0 else 1.0)
            sd = ellipsoid(w, 0.17, dz * 0.62, (0, y + 0.02, z)).su(ellipsoid(w * 0.75, 0.13, dz * 0.5, (0, y - 0.07, z)), 0.05)
            sd = sd.ss(capsule((0, y + 0.19, z - dz * 0.3), (0, y + 0.19, z + dz * 0.3), 0.025), 0.02)       # dorsal groove
            pat = lambda P, z=z: 1 - 0.55 * np.clip((P[:, 2] - z) / (dz * 0.5), 0, 1) ** 2
            col = "primary"
        H.piece(f"SegP{i + 1}", b, sd, col=col, mat="hard", tris=360, res=100, pattern=pat, pri=1.1 + 0.01 * i, role="body" if i else "body")
        # leg pair(s) on their own bone
        lb = H.bone(f"Legs{i + 1}", b, (0, y - 0.05, z))
        legb.append(lb)
        lg = None
        pairs = (-0.07, 0.07) if milli else (0.0,)
        for dzl in pairs:
            zz = z + dzl
            if milli:
                hp, kn, tp = A(0.12, y - 0.2, zz), A(0.28, y - 0.12, zz), A(0.3, 0.02, zz + 0.04)
                rr = (0.035, 0.03, 0.022)
            elif i == n - 1:  # long trailing ultimate legs
                hp, kn, tp = A(0.22, y - 0.03, zz), A(0.45, y + 0.05, zz + 0.4), A(0.55, y - 0.1, zz + 1.0)
                rr = (0.05, 0.04, 0.02)
            else:
                sw = 0.25 * (i / (n - 1) - 0.5)
                hp, kn, tp = A(w * 0.7, y - 0.05, zz), A(w + 0.4, y + 0.22, zz + 0.05 + sw * 0.3), A(w + 0.8, 0.025, zz + 0.22 + sw)
                rr = (0.065, 0.05, 0.025)
            one = round_cone(T(hp), T(kn), rr[0], rr[1]).su(round_cone(T(kn), T(tp), rr[1], rr[2]), 0.02)
            lg = one if lg is None else (lg | one)
        H.piece(f"LegP{i + 1}", lb, lg.mirror_x(), col="secondary", mat="hard", tris=300 if not milli else 260, res=110, role="limb", pri=1.5)
    # head
    hz = zc[0] - dz * 0.55
    H.bone("Head", segs[0], (0, y, hz + 0.1))
    if milli:
        hd = ellipsoid(0.25, 0.24, 0.2, (0, y - 0.02, hz - 0.08))
        base = A(0.13, y + 0.04, hz - 0.2)
        pts = [base, base + A(0.12, 0.08, -0.12), base + A(0.2, 0.0, -0.3), base + A(0.22, -0.18, -0.42)]
    else:
        hd = ellipsoid(0.32, 0.15, 0.26, (0, y + 0.02, hz - 0.1)).su(ellipsoid(0.22, 0.1, 0.12, (0, y - 0.03, hz - 0.3)), 0.04)
        base = A(0.12, y + 0.03, hz - 0.3)
        pts = [base, base + A(0.2, 0.15, -0.4), base + A(0.45, 0.2, -0.9), base + A(0.6, 0.1, -1.35)]
    H.piece("HeadP", "Head", hd, col="primary" if not milli else "dark", mat="hard", tris=500, role="head", pri=1.1)
    antenna(H, "", T(base), pts, 0.04, 0.02, col="secondary" if not milli else "dark", kind="thread", tris=260)
    mand = []
    if not milli:
        fb = A(0.13, y - 0.07, hz - 0.15)
        H.mbone("Fang#", "Head", T(fb))
        fg = tube([T(fb), T(fb + A(0.1, -0.02, -0.18)), T(fb + A(0.04, -0.03, -0.35)), T(fb + A(-0.08, -0.03, -0.4))], [0.06, 0.05, 0.035, 0.012], k=0.02)
        H.mpiece("Forcipule#", "Fang#", fg, col="darker", mat="hard", tris=220, role="jaw", pri=1.4)
        mand = [("FangR", 1), ("FangL", -1)]
    else:
        H.mprim("Eye#", "Head", "Ball", (0.07,) * 3, (0.16, y + 0.06, hz - 0.18), col="black", mat="hard", pri=1.3, role="eye")
    MB.crawler(H, segs, legpairs=legb, head="Head", ants=[("AntR", 1), ("AntL", -1)], mand=mand, mode="wave", period=1.0 if not milli else 1.4,
               height=0.8, amp=0.16 if not milli else 0.09, leg_amp=0.45 if not milli else 0.35, waves=1.0, attack="bite" if not milli else "rear")
    finish(H, head="Head", mouth=(0, y - 0.05, hz - 0.45), top=(0, y + 0.3, hz), tail=segs[-4:])
    return H


@hero("centipede", "bugs")
def centipede():
    return _myriapod("centipede", "centipede", preview={"primary": "#B8501E", "secondary": "#E8A02A", "darker": "#2A140A"})


@hero("millipede", "bugs")
def millipede():
    return _myriapod("millipede", "millipede", preview={"primary": "#3A2A1E", "secondary": "#C8701E", "dark": "#1E140E"})


# ================================================================================================ caterpillar / worm
def _larva(hid, kind="caterpillar", preview=None):
    worm = kind == "worm"
    H = Hero(hid, plan="Worm", gait="slither", tags=["bug", "larva" if not worm else "worm"])
    H.preview = preview or {}
    n = 9 if not worm else 13
    dz = 0.42 if not worm else 0.3
    R = 0.36 if not worm else 0.24
    y = R + 0.02
    z0 = -(n - 1) * dz * 0.5
    H.body((0, y, z0))
    segs, zc = _chain(H, n, z0, dz, y)
    for i, (b, z) in enumerate(zip(segs, zc)):
        t = i / (n - 1)
        if worm:
            r = R * (0.75 + 0.25 * math.sin(math.pi * min(1.0, t * 1.15 + 0.1))) * (1.25 if i == 3 else 1.0)
            sd = ellipsoid(r, r * 0.92, dz * 0.62, (0, r * 0.92 + 0.02, z))
            if i == n - 1:
                sd = sd.su(round_cone((0, r, z), (0, r * 0.7, z + dz * 0.9), r * 0.85, r * 0.35), 0.05)
            col = "secondary" if i == 3 else "primary"
            pat = combine(gradient(1, 0.0, 2 * R, 1.0, 0.85), lambda P, z=z: 1 - 0.2 * np.clip(np.abs(P[:, 2] - z) / (dz * 0.5), 0, 1) ** 3)
            mat = "plastic"
        else:
            r = R * (0.88 if i == 0 else (0.9 if i == n - 1 else 1.0))
            yy = r + 0.04
            sd = ellipsoid(r, r, dz * 0.64, (0, yy, z))
            if i < 3:   # true legs: small pointed jointed legs
                for sx in (1, -1):
                    sd = sd.su(round_cone((0.17 * sx, yy - r * 0.7, z), (0.2 * sx, 0.03, z - 0.05), 0.07, 0.025), 0.04)
            elif 4 <= i < 8 or i == n - 1:  # prolegs: stubby suckers
                for sx in (1, -1):
                    sd = sd.su(round_cone((0.2 * sx, yy - r * 0.6, z), (0.22 * sx, 0.06, z), 0.11, 0.08), 0.05)
            if kind == "hornworm" and i == n - 1:
                sd = sd.su(tube([(0, yy + r * 0.7, z), (0, yy + r + 0.3, z + 0.15), (0, yy + r + 0.45, z + 0.4)], [0.07, 0.04, 0.015]), 0.05)
            if kind == "caterpillar" and i in (1, n - 2):  # monarch-like filaments
                for sx in (1, -1):
                    sd = sd.su(tube([(0.12 * sx, yy + r * 0.8, z), (0.25 * sx, yy + r + 0.35, z - 0.05), (0.35 * sx, yy + r + 0.55, z - 0.2)],
                                    [0.04, 0.03, 0.015]), 0.03)
            if kind == "woolly":
                sd = sd.noise(0.028, 70, i)
            col = "primary"
            mat = "skin" if kind != "woolly" else "fur"
            if kind == "caterpillar":
                band = lambda P, z=z: 1 - 0.85 * (np.clip(1 - np.abs(np.abs(P[:, 2] - z) - dz * 0.25) / 0.045, 0, 1))
                pat = combine(band, lambda P: 1 - 0.75 * np.clip((0.12 - P[:, 1]) / 0.05, 0, 1),
                              lambda P, yy=yy, r=r: 1 - 0.9 * np.clip((P[:, 1] - yy - r * 1.05) / 0.08, 0, 1))
            elif kind == "woolly":
                pat = (lambda P, i=i: np.full(len(P), 0.25 if (i < 2 or i > n - 3) else 1.0))
            else:
                pat = combine(lambda P, z=z: 1 - 0.35 * np.clip(1 - np.abs((P[:, 2] - z) - 0.4 * (P[:, 1] - yy)) / 0.04, 0, 1),
                              lambda P: 1 - 0.6 * np.clip((0.12 - P[:, 1]) / 0.05, 0, 1))
        H.piece(f"SegP{i + 1}", b, sd, col=col, mat=mat, tris=520 if not worm else 320, res=104, pattern=pat, pri=1.1 + 0.01 * i)
        if kind == "caterpillar" and 0 < i:
            body_ = ellipsoid(r, r, dz * 0.64, (0, yy, z))
            ring = S.SDF(lambda p, body_=body_: np.abs(body_(p) - 0.012) - 0.014) & S.SDF(lambda p, z=z: np.abs(p[:, 2] - z) - 0.05) & \
                S.SDF(lambda p: 0.14 - p[:, 1])
            H.piece(f"Band{i + 1}", b, ring, col="secondary", mat=mat, tris=260, res=120, role="detail", pri=1.3, ao=False, smooth=1)
    # head
    hz = zc[0] - dz * 0.55
    H.bone("Head", segs[0], (0, y, hz + 0.1))
    mand = []
    if worm:
        hd = round_cone((0, y, hz + 0.05), (0, y - 0.03, hz - 0.3), R * 0.75, R * 0.35)
        H.piece("HeadP", "Head", hd, col="primary", mat="plastic", tris=300, role="head", pri=1.1, pattern=gradient(2, hz - 0.3, hz + 0.1, 1.0, 0.9))
        mouth = (0, y - 0.05, hz - 0.35)
    else:
        hc = A(0, y + 0.02, hz - 0.12)
        hd = sphere(R * 0.85, T(hc)).su(ellipsoid(R * 0.5, R * 0.35, R * 0.4, T(hc + A(0, -R * 0.45, -R * 0.45))), 0.06)
        hd = hd.ss(ellipsoid(0.03, R * 0.6, R * 0.3, T(hc + A(0, 0.08, -R * 0.75))), 0.03)            # epicranial suture
        H.piece("HeadP", "Head", hd, col="dark" if kind != "woolly" else "black", mat="hard", tris=700, role="head", pri=1.1)
        H.mprim("Eye#", "Head", "Ball", (0.12,) * 3, T(hc + A(R * 0.48, 0.0, -R * 0.62)), col="black", mat="hard", pri=1.3, role="eye")
        H.mprim("Shine#", "Head", "Ball", (0.045,) * 3, T(hc + A(R * 0.52, 0.04, -R * 0.75)), col="shine", mat="hard", pri=2.4, role="shine")
        mb = hc + A(0.08, -R * 0.6, -R * 0.7)
        H.mbone("Mand#", "Head", T(mb))
        H.mpiece("Mandible#", "Mand#", tube([T(mb), T(mb + A(0.03, -0.04, -0.06)), T(mb + A(-0.05, -0.06, -0.08))], [0.045, 0.035, 0.015]),
                 col="darker", mat="hard", tris=160, role="jaw", pri=1.5)
        base = hc + A(R * 0.4, -R * 0.3, -R * 0.7)
        antenna(H, "", T(base), [base, base + A(0.06, -0.03, -0.08), base + A(0.1, -0.06, -0.12)], 0.025, 0.018, col="cream", tris=120)
        mand = [("MandR", 1), ("MandL", -1)]
        mouth = tuple(hc + A(0, -R * 0.7, -R * 0.9))
    if worm:
        MB.crawler(H, segs, head="Head", mode="slither", period=1.6, height=0.4, amp=0.28, waves=1.2, attack="rear")
    else:
        MB.crawler(H, segs, head="Head", ants=[("AntR", 1), ("AntL", -1)], mand=mand, mode="inch", period=1.4, height=0.8, amp=0.07, attack="rear")
    finish(H, head="Head", mouth=mouth, top=(0, y + R * 1.2, hz), tail=segs[-3:])
    return H


@hero("caterpillar", "bugs")
def caterpillar():
    return _larva("caterpillar", "caterpillar", preview={"primary": "#6AC84A", "secondary": "#F2D82A", "dark": "#1E1E1A", "darker": "#0E0E0C", "cream": "#E8E0C8"})


@hero("hornworm", "bugs")
def hornworm():
    return _larva("hornworm", "hornworm", preview={"primary": "#7AC85A", "secondary": "#E8F0C8", "dark": "#3A6A2A", "darker": "#1A1A14", "cream": "#E8E0C8"})


@hero("woolly bear", "bugs")
def woolly_bear():
    return _larva("woolly bear", "woolly", preview={"primary": "#B8602A", "secondary": "#1E1A16", "darker": "#0E0E0C", "cream": "#E8E0C8"})


@hero("earthworm", "bugs")
def earthworm():
    return _larva("earthworm", "worm", preview={"primary": "#D88A7A", "secondary": "#C86A6A"})


# ================================================================================================ snail / slug
def _shell(c, R0=0.55, r0=0.46, turns=3.2, shrink=0.42, steps=46, lean=0.18):
    """Logarithmic-spiral shell around an axis along X through c: spheres along the whorl, smooth-unioned; the
    aperture (biggest whorl) at the bottom front. Returns (sdf, pattern)."""
    c = A(c)
    k = math.log(1 / shrink) / (2 * math.pi)
    sd = None
    for i in range(steps):
        th = turns * 2 * math.pi * i / (steps - 1)
        e = math.exp(-k * th)
        R, r = R0 * e, r0 * e
        p = c + A(lean * (1 - e) * 1.6, -R * math.cos(th), -R * math.sin(th))
        sp = sphere(r, T(p))
        sd = sp if sd is None else sd.su(sp, r * 0.25)
    sd = sd.ss(ellipsoid(0.1, R0 * 0.55, R0 * 0.6, T(c + A(-r0 * 0.95, -R0 * 0.7, 0))), 0.05)  # aperture recess

    def pat(P):
        q = P - c
        th = np.arctan2(-q[:, 2], -q[:, 1])
        rr = np.hypot(q[:, 1], q[:, 2])
        growth = 1 - 0.18 * np.clip(1 - np.abs(np.mod(th * 9 / math.pi, 1) - 0.5) / 0.15, 0, 1)
        band = 1 - 0.55 * np.clip(1 - np.abs(np.mod(np.log(np.maximum(rr, 1e-3)) / (2 * math.pi * k) + th / (2 * math.pi), 1) - 0.5) / 0.12, 0, 1)
        return growth * band

    return sd, pat


def _gastropod(hid, kind="snail", preview=None):
    slug = kind == "slug"
    H = Hero(hid, plan="Blob", gait="slither", tags=["mollusc", "bug", "slimy"])
    H.preview = preview or {}
    L = 1.0 if not slug else 1.35
    H.body((0, 0.25, 0))
    bcol = "secondary" if not slug else "primary"
    # foot (mid) on Body, the tail end on Tail
    foot = ellipsoid(0.42, 0.26 if not slug else 0.34, 0.85 * L, (0, 0.2, 0.0)) & S.SDF(lambda p: 0.0 - p[:, 1])
    foot = foot.su(ellipsoid(0.46, 0.06, 0.88 * L, (0, 0.06, 0.0)), 0.06)                          # skirt
    foot = foot.noise(0.012, 14, 1)
    tubercle = lambda P: 1 - 0.18 * np.clip(np.sin(P[:, 2] * 22 + np.sin(P[:, 0] * 18) * 2) * np.sin(P[:, 0] * 20) - 0.3, 0, 1) - 0.25 * np.clip((0.07 - P[:, 1]) / 0.04, 0, 1)
    H.piece("Foot", "Body", foot, col=bcol, mat="plastic", tris=1300, res=120, pattern=tubercle)
    H.bone("Tail", "Body", (0, 0.2, 0.55 * L))
    tl = round_cone((0, 0.18, 0.55 * L), (0, 0.06, 1.45 * L), 0.36 if not slug else 0.4, 0.06) & S.SDF(lambda p: 0.0 - p[:, 1])
    if slug:
        tl = tl.su(capsule((0, 0.38, 0.7), (0, 0.12, 1.5 * L), 0.035), 0.06)                          # keel
    H.piece("TailP", "Tail", tl.noise(0.012, 14, 2), col=bcol, mat="plastic", tris=700, res=110, pattern=tubercle, role="tail")
    # head / neck with the lower tentacles
    H.bone("Head", "Body", (0, 0.3, -0.6 * L))
    hc = A(0, 0.48, -1.12 * L)
    nk = tube([(0, 0.2, -0.45 * L), (0, 0.38, -0.85 * L), T(hc)], [0.36, 0.3, 0.24], k=0.06)
    nk = nk.ss(ellipsoid(0.08, 0.03, 0.04, T(hc + A(0, -0.17, -0.2))), 0.02)                       # mouth slit
    H.piece("HeadP", "Head", nk.noise(0.01, 14, 3), col=bcol, mat="plastic", tris=1000, res=120, role="head", pattern=tubercle)
    # lower (feeler) tentacles on their own bones
    fb = hc + A(0.12, -0.1, -0.12)
    H.mbone("Feeler#", "Head", T(fb))
    H.mpiece("FeelerP#", "Feeler#", round_cone(T(fb), T(fb + A(0.12, -0.12, -0.32)), 0.065, 0.035), col=bcol, mat="plastic", tris=200, role="detail", pri=1.5)
    # eye stalks
    stalks = []
    for side, ch in ((1, "R"), (-1, "L")):
        pass
    sb = A(0.12, 0.62, -1.15 * L)
    H.mbone("Stalk#", "Head", T(sb))
    tip = sb + A(0.18, 0.62, -0.3)
    st = round_cone(T(sb - A(0, 0.05, 0)), T(tip), 0.065, 0.04).su(sphere(0.06, T(tip)), 0.02)
    H.mpiece("StalkP#", "Stalk#", st, col=bcol, mat="plastic", tris=260, role="detail", pri=1.4)
    H.mprim("Eye#", "Stalk#", "Ball", (0.1,) * 3, T(tip + A(0.0, 0.03, -0.04)), col="black", mat="hard", pri=1.5, role="eye")
    H.mprim("Shine#", "Stalk#", "Ball", (0.035,) * 3, T(tip + A(0.02, 0.07, -0.08)), col="shine", mat="hard", pri=2.4, role="shine")
    stalks = [("StalkR", 1), ("StalkL", -1), ("FeelerR", 1), ("FeelerL", -1)]
    # shell or mantle
    if not slug:
        sc = A(0.0, 0.85, 0.1)
        H.bone("Shell", "Body", (0, 0.35, 0.1))
        sh, spat = _shell(sc)
        H.piece("ShellP", "Shell", sh, col="primary", mat="hard", tris=2400, res=140, pattern=spat)
        H.piece("Mantle", "Shell", ellipsoid(0.4, 0.14, 0.5, (0.0, 0.33, 0.05)), col="secondary", mat="plastic", tris=400, pri=1.2,
                pattern=lambda P: np.full(len(P), 0.82))
        shell = "Shell"
    else:
        H.bone("Shell", "Body", (0, 0.4, -0.3))
        mt = ellipsoid(0.44, 0.3, 0.6, (0, 0.38, -0.35)).ss(sphere(0.07, (0.4, 0.42, -0.2)), 0.03)   # pneumostome
        H.piece("Mantle", "Shell", mt.noise(0.01, 16, 5), col="primary", mat="plastic", tris=800, pri=1.2,
                pattern=combine(gradient(1, 0.2, 0.68, 1.0, 0.82), spots(0.18, 0.04, depth=0.35, seed=2)))
        shell = "Shell"
    MB.glider(H, foot=["Tail"], head="Head", stalks=stalks, shell=shell, height=1.0, period=1.8)
    finish(H, head="Head", mouth=T(hc + A(0, -0.15, -0.3)), top=T(hc + A(0, 0.5, 0)), tail=["Tail"])
    return H


@hero("snail", "bugs")
def snail():
    return _gastropod("snail", "snail", preview={"primary": "#A86A3A", "secondary": "#E8C8A0"})


@hero("slug", "bugs")
def slug():
    return _gastropod("slug", "slug", preview={"primary": "#8A7A4A", "secondary": "#C8B87A"})
