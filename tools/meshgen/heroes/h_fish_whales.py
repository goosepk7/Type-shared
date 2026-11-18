"""Aquatic family, marine mammals: whale (blue whale), humpback whale, sperm whale, killer whale, dolphin, beluga,
narwhal, manatee, seal, sea lion, walrus. Built with the fish builder from h_fish.py in "pitch" mode (the body wave
runs up and down, flukes / hind flippers lie flat), with flippers, blowholes, throat grooves, tusks and whiskers.

NOTE: shapes come from h_fish._fish: after changing that builder rebuild these with build.py --force --only ...
"""
import math

import numpy as np

import sdf as S
from kit import spots, stripes, combine
from map import NOTFOOD
import motion_aquatic as MA
from h_fish import _fish, _belly, _fins_std, pv, hero, FAM, barbels, chain

MAMMAL = dict(lift=1.1, mode="pitch", caudal_plane="h", gill=False, scales=0.0, pelvic=None, eye_col="pupil", pupil=None, fin_th=0.014,
              mat="skin", tags=("whale", "mammal"))


def flukes(span=0.24, length=0.14, notch=0.05):
    s, l = span, length
    return [(-0.05, 0.03), (0.02, 0.05), (l * 0.45, s * 0.7), (l * 0.85, s), (l, s * 0.98), (l * 0.9, s * 0.6), (l * 0.75, s * 0.2), (l * 0.75 - notch, 0.0),
            (l * 0.75, -s * 0.2), (l * 0.9, -s * 0.6), (l, -s * 0.98), (l * 0.85, -s), (l * 0.45, -s * 0.7), (0.02, -0.05), (-0.05, -0.03)]


def blowhole(t=0.13, w=0.012, double=False):
    def ex(H, ctx):
        pr, L = ctx["pr"], ctx["L"]
        tp = pr.at(t)[0]
        if double:
            H.mprim("Blow#", "Head", "Ellipsoid", (w * L, 0.006 * L, w * 2.2 * L), (w * 0.9 * L, tp - 0.0015 * L, pr.z(t)), rot=(0, 0.2, 0), col="darker", mat="skin", role="detail", pri=2.2)
        else:
            H.prim("Blow", "Head", "Ellipsoid", (w * 2 * L, 0.006 * L, w * L), (0, tp - 0.0015 * L, pr.z(t)), col="darker", mat="skin", role="detail", pri=2.2)
    return ex


def throat_grooves(t1, t2, frac=0.25, freq=90, depth=0.35):
    def mk(pr, L):
        ts = np.linspace(0, 1, 40)
        cs = np.array([pr.at(t)[3] - frac * pr.at(t)[4] for t in ts])

        def f(Q):
            tt = (Q[:, 2] - pr.z0) / L
            cy = np.interp(np.clip(tt, 0, 1), ts, cs)
            m = (Q[:, 1] < cy) & (tt > t1) & (tt < t2)
            line = np.abs(np.sin(Q[:, 0] / L * freq)) < 0.3
            return 1 - depth * (m & line)
        return f
    return mk


def tusk(length=0.45, r=0.012, side=0.35):
    def ex(H, ctx):
        pr, L, z0 = ctx["pr"], ctx["L"], ctx["z0"]
        tp, bt, w, c, a = pr.at(0.03)
        base = np.array((side * w, c + 0.1 * a, pr.z(0.04)))
        tip = base + np.array((0.02 * L, 0.03 * L, -length * L))
        t = S.round_cone(tuple(base), tuple(tip), r * L, 0.002 * L).twist(0.0)
        # spiral grooves baked as stripes along the tusk
        d = (tip - base) / np.linalg.norm(tip - base)

        def spiral(Q):
            q = Q - base
            along = q @ d
            ang = np.arctan2(q[:, 1], q[:, 0])
            u = np.mod(along / (0.03 * L) + ang / (2 * math.pi), 1.0)
            return 1 - 0.35 * (np.abs(u - 0.5) < 0.18)
        H.piece("Tusk", "Head", t, col="horn", mat="hard", tris=700, role="horn", pri=1.4, pattern=spiral, res=160, smooth=2)
    return ex


def walrus_tusks(H, ctx):
    pr, L = ctx["pr"], ctx["L"]
    tp, bt, w, c, a = pr.at(0.04)
    ts = []
    for sx in (1, -1):
        b = (sx * 0.035 * L, c - 0.35 * a, pr.z(0.045))
        e = (sx * 0.05 * L, c - 0.35 * a - 0.2 * L, pr.z(0.06))
        ts.append(S.round_cone(b, e, 0.016 * L, 0.006 * L).bend(0.0))
    H.piece("Tusks", "Head", ts[0] | ts[1], col="horn", mat="hard", tris=500, role="horn", pri=1.4, res=150)


@hero("dolphin", FAM)
def dolphin():
    prof = [(0, 0.0, -0.012, 0.011), (0.03, 0.012, -0.022, 0.02), (0.065, 0.022, -0.03, 0.027), (0.09, 0.06, -0.045, 0.05), (0.14, 0.095, -0.07, 0.075),
            (0.3, 0.12, -0.1, 0.095), (0.45, 0.115, -0.095, 0.088), (0.65, 0.075, -0.06, 0.052), (0.85, 0.036, -0.028, 0.022), (0.95, 0.024, -0.02, 0.015),
            (1.0, 0.02, -0.018, 0.013)]
    return _fish("dolphin", prof=prof, L=7.0, mouth=(-0.15, 0, 0.11, 0.12, 0.45), eye=(0.13, 5, 0.016), seg=(0.26, 0.48, 0.66, 0.84),
                 fins=_fins_std(dict(t=(0.4, 0.55), edge=[(0.4, 0.03), (0.46, 0.11), (0.53, 0.15), (0.56, 0.145), (0.54, 0.08), (0.6, 0.01)], th=1.3, ray=0.0)),
                 caudal=(flukes(0.21, 0.13), 0, 0), pecs=dict(t=0.21, ang=-50, len=0.13, wid=0.05, splay=50, droop=35, roll=-65, tipk=0.55, rootw=0.7, th=1.3),
                 overlays=[_belly(0.0, 0.9, 0.1, "secondary", wav=0.004)], extra=blowhole(0.14), back=0.8, amp=0.22, period=1.0,
                 preview=pv("dolphin"), **MAMMAL)


@hero("killer whale", FAM)
def orca():
    prof = [(0, 0.0, -0.025, 0.02), (0.04, 0.04, -0.05, 0.05), (0.12, 0.09, -0.085, 0.085), (0.3, 0.13, -0.12, 0.11), (0.45, 0.13, -0.115, 0.105),
            (0.65, 0.085, -0.07, 0.065), (0.85, 0.04, -0.032, 0.026), (1.0, 0.022, -0.02, 0.016)]

    def eye_patch(pr, L):
        p = np.array(pr.surface(0.17, 15))
        return S.ellipsoid(0.03 * L, 0.025 * L, 0.06 * L, tuple(p + np.array((0, 0, 0.03 * L)))).mirror_x()

    def belly(pr, L):
        ts = np.linspace(0, 1, 40)
        cs = np.array([pr.at(t)[3] - 0.35 * pr.at(t)[4] for t in ts])

        def f(Q):
            tt = np.clip((Q[:, 2] - pr.z0) / L, 0, 1)
            cy = np.interp(tt, ts, cs) + 0.06 * L * np.exp(-((tt - 0.6) / 0.06) ** 2)  # flank lobe
            return Q[:, 1] - cy
        return S.SDF(f)

    def saddle(pr, L):
        p = np.array(pr.surface(0.56, 90))
        return S.ellipsoid(0.07 * L, 0.03 * L, 0.06 * L, tuple(p))

    return _fish("killer whale", prof=prof, L=8.0, mouth=(-0.1, 0, 0.12, 0.05, 0.45), eye=(0.13, 10, 0.012), seg=(0.27, 0.5, 0.68, 0.85),
                 teeth=6, teeth_t0=0.03, tooth_len=0.012,
                 fins=_fins_std(dict(t=(0.38, 0.52), edge=[(0.38, 0.03), (0.42, 0.18), (0.44, 0.3), (0.455, 0.31), (0.48, 0.15), (0.54, 0.01)], th=1.6, ray=0.0)),
                 caudal=(flukes(0.2, 0.13), 0, 0), pecs=dict(t=0.22, ang=-55, len=0.14, wid=0.08, splay=50, droop=40, roll=-60, rootw=0.6, th=1.4),
                 overlays=[(0.12, 0.25, eye_patch, "secondary"), (0.0, 0.8, belly, "secondary"), (0.5, 0.63, saddle, "light")],
                 extra=blowhole(0.15), back=0.95, amp=0.2, period=1.1, preview=pv("killer whale", light="#A8ACB0"), **MAMMAL)


@hero("whale", FAM)
def whale():
    prof = [(0, 0.0, -0.03, 0.03), (0.04, 0.025, -0.055, 0.06), (0.12, 0.05, -0.085, 0.085), (0.3, 0.075, -0.095, 0.09), (0.5, 0.075, -0.08, 0.08),
            (0.7, 0.05, -0.05, 0.05), (0.88, 0.024, -0.022, 0.022), (1.0, 0.016, -0.015, 0.013)]
    return _fish("whale", prof=prof, L=14.0, mouth=(0.0, 0, 0.22, -0.02, 0.45), eye=(0.21, -10, 0.008), seg=(0.27, 0.5, 0.68, 0.85),
                 fins=_fins_std(dict(t=(0.72, 0.79), edge=[(0.72, 0.01), (0.76, 0.03), (0.78, 0.035), (0.8, 0.01)], th=1.4, ray=0.0)),
                 caudal=(flukes(0.17, 0.1, 0.03), 0, 0), pecs=dict(t=0.29, ang=-60, len=0.13, wid=0.03, splay=50, droop=35, roll=-60, tipk=0.6, rootw=0.7, th=1.4),
                 pattern=lambda pr, L: combine(throat_grooves(0.03, 0.42, 0.2, 70)(pr, L), spots(0.025 * L, 0.008 * L, depth=0.2, seed=6)),
                 overlays=[_belly(0.0, 0.5, 0.25, "secondary", taper=0.2)], extra=blowhole(0.16, 0.008, double=True), back=0.85, amp=0.16, period=2.0,
                 attack="slap", preview=pv("whale"), **MAMMAL)


@hero("humpback whale", FAM)
def humpback():
    prof = [(0, 0.0, -0.03, 0.035), (0.04, 0.03, -0.06, 0.07), (0.12, 0.065, -0.1, 0.1), (0.3, 0.1, -0.12, 0.115), (0.5, 0.09, -0.1, 0.1),
            (0.7, 0.06, -0.06, 0.06), (0.88, 0.028, -0.025, 0.025), (1.0, 0.018, -0.017, 0.015)]

    def knobs(b, pr):
        L = pr.L
        ks = []
        rng = np.random.default_rng(3)
        for i in range(14):
            t = 0.01 + 0.13 * i / 13
            for ang in (70, 88):
                p = np.array(pr.surface(t, ang + rng.uniform(-6, 6)))
                ks.append(S.sphere(0.011 * L, tuple(p)))
        kk = MA.union_all(ks).mirror_x()
        # hump dorsal base
        return b.su(kk, 0.004 * L)

    pec = dict(t=0.28, ang=-55, len=0.32, wid=0.06, splay=62, droop=18, roll=-78, tipk=0.4, rootw=0.75, th=1.4, col="secondary",
               pts=[(-0.01 * 14, 0.025 * 14), (0.1 * 14, 0.035 * 14), (0.2 * 14, 0.025 * 14), (0.3 * 14, 0.012 * 14), (0.32 * 14, 0.0), (0.3 * 14, -0.012 * 14),
                    (0.24 * 14, -0.014 * 14), (0.2 * 14, -0.02 * 14), (0.14 * 14, -0.018 * 14), (0.08 * 14, -0.025 * 14), (-0.01 * 14, -0.025 * 14)])
    return _fish("humpback whale", prof=prof, L=14.0, sculpt=knobs, mouth=(0.0, 0, 0.24, -0.04, 0.45), eye=(0.23, -15, 0.008),
                 seg=(0.27, 0.5, 0.68, 0.85),
                 fins=_fins_std(dict(t=(0.62, 0.7), edge=[(0.62, 0.01), (0.66, 0.035), (0.68, 0.04), (0.71, 0.01)], th=1.6, ray=0.0)),
                 caudal=(flukes(0.17, 0.1, 0.03), 0, 0), pecs=pec,
                 pattern=lambda pr, L: throat_grooves(0.03, 0.45, 0.15, 60, 0.4)(pr, L),
                 overlays=[_belly(0.0, 0.5, 0.2, "secondary", wav=0.006, taper=0.2)], extra=blowhole(0.17, 0.008, double=True), back=0.9, amp=0.17, period=2.0,
                 attack="slap", preview=pv("humpback whale"), **MAMMAL)


@hero("sperm whale", FAM)
def sperm_whale():
    prof = [(0, 0.08, -0.05, 0.06), (0.03, 0.115, -0.09, 0.09), (0.15, 0.125, -0.11, 0.1), (0.33, 0.125, -0.115, 0.1), (0.5, 0.11, -0.1, 0.09),
            (0.7, 0.07, -0.06, 0.055), (0.88, 0.03, -0.028, 0.025), (1.0, 0.02, -0.018, 0.015)]

    def box_head(b, pr):
        L = pr.L
        tp, bt, w, c, a = pr.at(0.15)
        hd = S.round_box(0.085 * L, 0.1 * L, 0.17 * L, 0.06 * L, (0, c + 0.015 * L, pr.z(0.16)))
        b = b.su(hd, 0.04 * L)
        # knuckles along the back
        ks = [S.sphere(0.014 * L, pr.surface(t, 90)) for t in np.linspace(0.62, 0.82, 6)]
        b = b.su(MA.union_all(ks), 0.01 * L)
        wr = b.noise(0.003 * L, 10.0 / L, 2)
        return S.SDF(lambda Q: np.where(Q[:, 2] > pr.z(0.35), wr(Q), b(Q)))
    return _fish("sperm whale", prof=prof, L=12.0, sculpt=box_head, square=0.0, mouth=(-0.85, 0, 0.27, -0.03, 0.18), teeth=8, teeth_t0=0.06,
                 tooth_len=0.012, eye=(0.31, -20, 0.008), seg=(0.34, 0.52, 0.68, 0.85),
                 fins=_fins_std(dict(t=(0.55, 0.62), edge=[(0.55, 0.01), (0.58, 0.03), (0.6, 0.032), (0.63, 0.01)], th=1.8, ray=0.0)),
                 caudal=(flukes(0.16, 0.1, 0.03), 0, 0), pecs=dict(t=0.36, ang=-65, len=0.08, wid=0.04, splay=50, droop=40, roll=-60, rootw=0.7, th=1.4),
                 pattern=None, overlays=[], extra=blowhole(0.02, 0.01), back=0.85, amp=0.16, period=1.9, attack="slap",
                 preview=pv("sperm whale", mouth="#E8E0E0"), **MAMMAL)


@hero("beluga", FAM)
def beluga():
    prof = [(0, 0.0, -0.02, 0.02), (0.03, 0.03, -0.035, 0.035), (0.075, 0.1, -0.06, 0.07), (0.14, 0.12, -0.08, 0.085), (0.2, 0.105, -0.095, 0.088),
            (0.35, 0.13, -0.12, 0.11), (0.5, 0.125, -0.11, 0.1), (0.7, 0.08, -0.065, 0.06), (0.88, 0.035, -0.03, 0.025), (1.0, 0.02, -0.018, 0.015)]
    ridge = lambda b, pr: b.su(S.tube([pr.surface(t, 90) for t in np.linspace(0.42, 0.66, 4)], [0.006 * pr.L] * 4, k=0.01 * pr.L), 0.02 * pr.L)
    return _fish("beluga", prof=prof, L=7.0, sculpt=ridge, mouth=(-0.2, 0, 0.065, 0.15, 0.45), eye=(0.11, 5, 0.014), seg=(0.25, 0.5, 0.68, 0.85),
                 fins=(), caudal=(flukes(0.18, 0.12), 0, 0), pecs=dict(t=0.25, ang=-55, len=0.12, wid=0.06, splay=50, droop=40, roll=-60, rootw=0.65, th=1.4),
                 overlays=[], extra=blowhole(0.11), back=0.95, amp=0.2, period=1.3, preview=pv("beluga", pupil="#1A1C22"), **MAMMAL)


@hero("narwhal", FAM)
def narwhal():
    prof = [(0, 0.03, -0.03, 0.03), (0.04, 0.07, -0.055, 0.06), (0.12, 0.1, -0.08, 0.085), (0.3, 0.125, -0.11, 0.105), (0.5, 0.12, -0.1, 0.095),
            (0.7, 0.075, -0.06, 0.058), (0.88, 0.033, -0.028, 0.024), (1.0, 0.02, -0.018, 0.015)]
    ridge = lambda b, pr: b.su(S.tube([pr.surface(t, 90) for t in np.linspace(0.45, 0.68, 4)], [0.006 * pr.L] * 4, k=0.01 * pr.L), 0.02 * pr.L)
    return _fish("narwhal", prof=prof, L=7.0, sculpt=ridge, mouth=(-0.35, 0, 0.05, 0.1, 0.45), eye=(0.1, 0, 0.012), seg=(0.25, 0.5, 0.68, 0.85),
                 fins=(), caudal=(flukes(0.19, 0.13), 0, 0), pecs=dict(t=0.2, ang=-55, len=0.1, wid=0.05, splay=50, droop=40, roll=-60, rootw=0.65, th=1.4),
                 pattern=lambda pr, L: spots(0.03 * L, 0.011 * L, depth=0.55, region=lambda Q: np.clip((Q[:, 1] - pr.y0) / (0.05 * L) + 0.6, 0, 1), seed=8),
                 overlays=[_belly(0.0, 0.85, 0.3, "secondary", wav=0.004)], extra=chain(tusk(0.5, 0.013), blowhole(0.1)), back=0.8, amp=0.2, period=1.3,
                 attack="ram", preview=pv("narwhal"), **MAMMAL)


@hero("manatee", FAM)
def manatee():
    prof = [(0, 0.0, -0.045, 0.045), (0.04, 0.05, -0.07, 0.075), (0.1, 0.07, -0.08, 0.085), (0.16, 0.085, -0.095, 0.098), (0.35, 0.15, -0.145, 0.15),
            (0.55, 0.14, -0.14, 0.14), (0.75, 0.09, -0.09, 0.09), (0.9, 0.045, -0.04, 0.05), (1.0, 0.03, -0.03, 0.035)]

    def snout(b, pr):
        L = pr.L
        pad = S.ellipsoid(0.05 * L, 0.04 * L, 0.035 * L, (0.022 * L, pr.y0 - 0.02 * L, pr.z(0.03))).mirror_x()
        return b.su(pad, 0.02 * L).noise(0.003 * L, 9.0 / L, 3)
    paddle = [(-0.05, 0.04), (0.04, 0.08)] + [(0.11 + 0.11 * math.cos(math.radians(a)), 0.16 * math.sin(math.radians(a))) for a in range(110, -111, -20)] + [(0.04, -0.08), (-0.05, -0.04)]
    return _fish("manatee", prof=prof, L=7.0, sculpt=snout, mouth=(-0.6, 0, 0.06, 0.0, 0.4), eye=(0.12, 20, 0.008), seg=(0.25, 0.5, 0.68, 0.85),
                 fins=(), caudal=(paddle, 0, 0), pecs=dict(t=0.22, ang=-55, len=0.12, wid=0.05, splay=40, droop=50, roll=-55, rootw=0.7, th=2.0),
                 pattern=lambda pr, L: spots(0.03 * L, 0.012 * L, depth=0.15, seed=12),
                 extra=barbels([(0.01, -10, "Head", (1, -0.4, -0.3), 0.025, 0.003), (0.02, 10, "Head", (1, 0.0, -0.4), 0.025, 0.003),
                                (0.03, -30, "Head", (1, -0.6, -0.2), 0.025, 0.003)], col="dark"),
                 overlays=[], back=0.9, amp=0.16, period=1.8, attack="slap", preview=pv("manatee"), **MAMMAL)


def _pinniped(hid, prev, prof, L=6.0, tusks=False, front=0.13, **kw):
    hind = [(-0.05, 0.03), (0.03, 0.05), (0.12, 0.09), (0.19, 0.12), (0.21, 0.1), (0.2, 0.05), (0.14, 0.015), (0.2, -0.015), (0.21, -0.05),
            (0.2, -0.1), (0.19, -0.12), (0.12, -0.09), (0.03, -0.05), (-0.05, -0.03)]
    whisk = barbels([(0.02, -20, "Head", (1, -0.1, 0.2), 0.08, 0.0025), (0.025, -5, "Head", (1, 0.15, 0.25), 0.07, 0.0025),
                     (0.03, -35, "Head", (1, -0.35, 0.2), 0.07, 0.0025)], col="cream")
    d = dict(prof=prof, L=L, mouth=(-0.45, 0, 0.06, 0.0, 0.4), eye=(0.07, 25, 0.02), seg=(0.2, 0.42, 0.62, 0.82), fins=(),
             caudal=(hind, 0, 0), pecs=dict(t=0.26, ang=-60, len=front, wid=0.05, splay=40, droop=55, roll=-50, rootw=0.7, th=1.6, col="dark"),
             extra=chain(whisk, walrus_tusks if tusks else None), back=0.8, amp=0.22, period=1.2, preview=prev)
    d.update(MAMMAL)
    d["tags"] = ("seal", "mammal")
    d.update(kw)
    return _fish(hid, **d)


@hero("seal", FAM)
def seal():
    prof = [(0, 0.0, -0.022, 0.02), (0.035, 0.035, -0.035, 0.042), (0.09, 0.062, -0.052, 0.062), (0.16, 0.055, -0.06, 0.058), (0.3, 0.1, -0.1, 0.11),
            (0.5, 0.11, -0.11, 0.12), (0.7, 0.08, -0.08, 0.085), (0.88, 0.04, -0.04, 0.05), (1.0, 0.025, -0.022, 0.035)]
    return _pinniped("seal", pv("seal", pupil="#141418", cream="#E8E2D2", dark="#5A5E64"), prof,
                     pattern=lambda pr, L: spots(0.035 * L, 0.012 * L, depth=0.45, seed=21), overlays=[_belly(0.05, 0.9, 0.2, "secondary")])


@hero("sea lion", FAM)
def sea_lion():
    prof = [(0, 0.04, 0.02, 0.018), (0.035, 0.075, 0.0, 0.038), (0.09, 0.1, 0.015, 0.058), (0.17, 0.075, -0.035, 0.055), (0.32, 0.105, -0.1, 0.1),
            (0.5, 0.1, -0.1, 0.105), (0.7, 0.07, -0.07, 0.075), (0.88, 0.035, -0.035, 0.045), (1.0, 0.022, -0.02, 0.032)]
    return _pinniped("sea lion", pv("sea lion", pupil="#141418", cream="#E8E2D2", dark="#4A3420"), prof, L=6.5, front=0.2,
                     pecs=dict(t=0.29, ang=-70, len=0.2, wid=0.07, splay=35, droop=60, roll=-50, rootw=0.7, th=1.6, col="dark"),
                     overlays=[_belly(0.1, 0.9, 0.3, "secondary")])


@hero("walrus", FAM)
def walrus():
    prof = [(0, 0.03, -0.04, 0.05), (0.04, 0.07, -0.07, 0.08), (0.1, 0.09, -0.08, 0.09), (0.18, 0.1, -0.12, 0.12), (0.35, 0.15, -0.16, 0.17),
            (0.55, 0.14, -0.15, 0.16), (0.75, 0.1, -0.1, 0.11), (0.9, 0.05, -0.05, 0.06), (1.0, 0.03, -0.028, 0.04)]

    def muzzle(b, pr):
        L = pr.L
        pad = S.ellipsoid(0.045 * L, 0.045 * L, 0.035 * L, (0.032 * L, pr.y0 - 0.025 * L, pr.z(0.03))).mirror_x()
        return b.su(pad, 0.02 * L).noise(0.004 * pr.L, 7.0 / pr.L, 4)
    return _pinniped("walrus", pv("walrus", pupil="#141418", cream="#E8D8B0", dark="#7A5240", horn="#F2EAD6"), prof, L=7.0, tusks=True, sculpt=muzzle,
                     eye=(0.09, 30, 0.012), mouth=(-0.7, 0, 0.05, 0.0, 0.3), overlays=[])


MAP = [
    ("dolphin", "dolphin, dolphins, spinner dolphin, river dolphin, porpoise, vaquita, dall's porpoise, risso's dolphin, baby dolphin, "
                "space dolphin, encantado, ichthyosaurus, shonisaurus, temnodontosaurus", NOTFOOD),
    ("killer whale", "killer whale, orca, orcas, false killer whale, pilot whale", NOTFOOD),
    ("whale", "whale, whales, blue whale, gray whale, grey whale, fin whale, minke whale, sei whale, bryde's whale, bowhead whale, right whale, "
              "baby whale, spirit whale, celestial whale, astro whale, beaked whale, bahamut, bakekujira, !killer whale, !whale shark, !sperm whale, !humpback", NOTFOOD),
    ("humpback whale", "humpback, humpback whale", NOTFOOD),
    ("sperm whale", "sperm whale, cachalot, livyatan", NOTFOOD),
    ("beluga", "beluga, beluga whale, white whale", NOTFOOD),
    ("narwhal", "narwhal, narwhals, narwhal unicorn", NOTFOOD),
    ("manatee", "manatee, manatees, dugong, sea cow, steller's sea cow", NOTFOOD),
    ("seal", "seal, seals, seal pup, harp seal, grey seal, gray seal, monk seal, ringed seal, hooded seal, weddell seal, leopard seal, "
             "elephant seal, fur seal, selkie, nothosaurus, !navy seal", {"cat": ["Creature"]}),
    ("sea lion", "sea lion, sea lions", NOTFOOD),
    ("walrus", "walrus, walruses", NOTFOOD),
]
