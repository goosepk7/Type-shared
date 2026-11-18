"""Aquatic family, sharks: shark (generic requiem shark), great white shark, hammerhead shark, whale shark. Built with the
fish builder from h_fish.py (lofted body, 5 swimming segments, underslung jaw with rows of teeth, gill slits, big
swept pectorals, heterocercal tail, white belly overlay).

NOTE: shapes come from h_fish._fish: after changing that builder rebuild these with build.py --force --only ...
"""
import math

import numpy as np

import sdf as S
from kit import spots, combine
from map import NOTFOOD
import motion_aquatic as MA
from motion_aquatic import plate
from h_fish import _fish, _belly, _fins_std, pv, hero, FAM

SHARK = [(0, 0.004, -0.018, 0.012), (0.04, 0.042, -0.04, 0.042), (0.12, 0.082, -0.074, 0.075), (0.3, 0.122, -0.108, 0.1), (0.45, 0.125, -0.108, 0.094),
         (0.65, 0.086, -0.07, 0.06), (0.85, 0.042, -0.036, 0.03), (1.0, 0.032, -0.03, 0.022)]


def gills(t1=0.2, t2=0.29, n=5, depth=0.55):
    def mk(pr, L):
        def f(Q):
            tt = (Q[:, 2] - pr.z0) / L
            k = (tt - t1) / (t2 - t1) * (n - 1)
            fr = np.abs(k - np.round(k))
            inside = (k > -0.3) & (k < n - 0.7)
            tp, bt, w, c, a = pr.at((t1 + t2) / 2)
            yy = (Q[:, 1] - c) / a
            side = (np.abs(Q[:, 0]) > 0.45 * w) & (yy > -0.55) & (yy < 0.45)
            return 1 - depth * np.clip(1 - fr / 0.14, 0, 1) * inside * side
        return f
    return mk


def _shark(hid, prev, prof=SHARK, L=8.0, dorsal=1.0, pec=1.0, caud=1.0, belly_wav=0.006, extra=None, **kw):
    d = dict(prof=prof, L=L, mouth=(-1.0, 0, 0.2, -0.22, 0.38), teeth=9, teeth_t0=0.07, tooth_len=0.022, eye=(0.11, 28, 0.016),
             eye_col="pupil", pupil=None, seg=(0.3, 0.5, 0.68, 0.85), gill=False, scales=0.0, back=0.75,
             fins=_fins_std(dict(t=(0.33, 0.47), edge=[(0.33, 0.04), (0.38, 0.17 * dorsal), (0.42, 0.21 * dorsal), (0.445, 0.19 * dorsal), (0.45, 0.13 * dorsal), (0.5, 0.01)], th=1.5, ray=0.0),
                            dict(t=(0.78, 0.83), edge=[(0.78, 0.02), (0.8, 0.05), (0.84, 0.04), (0.87, 0.005)], th=1.2),
                            dict(t=(0.8, 0.85), edge=[(0.8, 0.02), (0.82, 0.045), (0.86, 0.035), (0.88, 0.005)], th=1.2)),
             caudal=("shark", 0.26 * caud, 0.28 * caud), fin_th=0.012,
             pecs=dict(t=0.29, ang=-45, len=0.26 * pec, wid=0.1 * pec, splay=60, droop=22, roll=-72, tipk=0.55, rootw=0.75, th=1.4),
             pelvic=dict(t=0.6, ang=-75, len=0.07, wid=0.04, splay=25, droop=35, roll=-30, th=1.2),
             pattern=gills(), overlays=[_belly(0.0, 0.9, 0.12, "secondary", wav=belly_wav)], amp=0.24, period=1.1, attack="bite",
             tags=("fish", "shark"), preview=prev)
    d.update(kw)
    if extra:
        d["extra"] = extra
    return _fish(hid, **d)


@hero("shark", FAM)
def shark():
    return _shark("shark", pv("shark"))


@hero("great white shark", FAM)
def great_white():
    prof = [(0, 0.006, -0.02, 0.014), (0.04, 0.05, -0.05, 0.05), (0.12, 0.1, -0.09, 0.09), (0.3, 0.15, -0.13, 0.125), (0.45, 0.15, -0.13, 0.115),
            (0.65, 0.1, -0.08, 0.07), (0.85, 0.042, -0.036, 0.03), (1.0, 0.032, -0.03, 0.026)]
    return _shark("great white shark", pv("great white shark"), prof=prof, L=9.0, dorsal=1.1, pec=1.05, teeth=10, tooth_len=0.026,
                  caudal=("lunate", 0.27, 0.24), belly_wav=0.01)


@hero("hammerhead shark", FAM)
def hammerhead():
    def head(b, pr):
        L = pr.L
        tp, bt, w, c, a = pr.at(0.04)
        foil = S.ellipsoid(0.24 * L, 0.022 * L, 0.05 * L, (0, c + 0.005 * L, pr.z(0.045)))
        foil = foil.su(S.ellipsoid(0.04 * L, 0.024 * L, 0.06 * L, (0.215 * L, c + 0.005 * L, pr.z(0.05))).mirror_x(), 0.02 * L)
        return b.su(foil, 0.03 * L)

    def eyes(H, ctx):
        pr, L = ctx["pr"], ctx["L"]
        c = pr.at(0.05)[3]
        H.eyes("Head", (0.245 * L, c + 0.006 * L, pr.z(0.05)), 0.016 * L, col="pupil", pupil=None, look=(1.0, 0.1, -0.2))
    return _shark("hammerhead shark", pv("hammerhead shark"), dorsal=1.35, sculpt=head, eye=None, extra=eyes,
                  mouth=(-1.0, 0, 0.18, -0.25, 0.36), teeth_t0=0.085)


@hero("whale shark", FAM)
def whale_shark():
    prof = [(0, 0.03, -0.05, 0.07), (0.04, 0.07, -0.075, 0.12), (0.15, 0.115, -0.1, 0.14), (0.35, 0.15, -0.12, 0.13), (0.5, 0.14, -0.11, 0.11),
            (0.7, 0.09, -0.07, 0.065), (0.87, 0.045, -0.038, 0.032), (1.0, 0.034, -0.03, 0.026)]

    def ridges(b, pr):
        L = pr.L
        rs = []
        for ang in (55, 30):
            pts = [pr.surface(t, ang) for t in np.linspace(0.2, 0.85, 6)]
            rs.append(S.tube(pts, [0.008 * L] * len(pts), k=0.01 * L).mirror_x())
        return b.su(MA.union_all(rs), 0.01 * L)

    def spot_region(pr, L):
        rng = np.random.default_rng(4)
        sh = []
        for i in range(70):
            t = rng.uniform(0.05, 0.88)
            ang = rng.uniform(5, 90)
            p = np.array(pr.surface(t, ang))
            r = 0.011 * L * (1.3 if t < 0.2 else 1.0)
            sh.append(S.sphere(r, tuple(p)))
            sh.append(S.sphere(r, tuple(p * np.array((-1, 1, 1)))))
        return MA.union_all(sh)
    return _shark("whale shark", pv("whale shark"), prof=prof, L=11.0, dorsal=0.9, pec=1.1, sculpt=ridges, square=0.15,
                  mouth=(-0.15, 0, 0.07, 0.0, 0.35), teeth=0, eye=(0.08, 5, 0.012),
                  overlays=[_belly(0.0, 0.9, 0.05, "secondary"), (0.03, 0.9, spot_region, "secondary")],
                  amp=0.18, period=1.6, preview=pv("whale shark"))


MAP = [
    ("shark", "shark, sharks, tiger shark, bull shark, reef shark, blacktip shark, lemon shark, mako shark, blue shark, silky shark, "
              "oceanic whitetip, nurse shark, dogfish, catshark, thresher shark, goblin shark, greenland shark, sand shark, "
              "lantern shark, leopard shark, zebra shark, cookiecutter shark, swell shark, horn shark, epaulette shark, sawshark, "
              "frilled shark, cretoxyrhina, stethacanthus, edestus, zombie shark, baby shark, mecha shark, skeleton shark, !wereshark, !gummy shark, !shark rider, !shark car, !sharkataur", NOTFOOD),
    ("great white shark", "great white, great white shark, white shark, megalodon, megamouth shark, basking shark", NOTFOOD),
    ("hammerhead shark", "hammerhead, hammerhead shark, bonnethead", NOTFOOD),
    ("whale shark", "whale shark", NOTFOOD),
]
