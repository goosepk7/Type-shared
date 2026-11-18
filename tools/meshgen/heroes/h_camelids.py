"""Camels and their cousins: camel (two humps, bactrian), dromedary (one hump), llama, alpaca. Built by
hoofkit.ungulate: long legs with knobbly knees and wide two-toed pads, the camel's dipped S-neck and droopy lips,
humps sculpted into the barrel, a woven riding blanket draped over the hump(s) with the seat on top; llamas and
alpacas get fleece and banana ears. Camels pace (both legs of a side together, the rolling camel walk).
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from kit import hero
from map import NOTFOOD
import hoofkit as K

TAGS = ("ungulate", "camelid")


def hump_saddle(humps, rug=True):
    """Extra hook: rug over the hump(s) (camels are ridden) and the seat moved onto the hump."""

    def f(H, X):
        s, top, body, BL = X["s"], X["top"], X["body"], X["BL"]
        zs = sum(h[0] for h in humps) / len(humps) * BL * s
        ytop = top * s - 0.2 * s + K.surf(body, (0, top * s - 0.2 * s, zs), (0, 1, 0), hi=3 * s)
        if rug:
            two = len(humps) > 1
            zr = 0.42 if two else 0.72
            cut = ytop + (0.12 if two else -0.24) * s
            rug_ = body.shell(0.05 * s) & ellipsoid(1.6 * s, 1.1 * s, zr * s, (0, ytop - 0.5 * s, zs)) & half_space(1, 1, cut)
            rug_ = rug_ & half_space(1, -1, (X["yb"] + 0.45 * X["Dp"]) * s)
            H.piece("Rug", "Body", rug_, col=K.BLANKET, mat="cloth", tris=X["T"](1100), res=128, role="detail", pri=1.4,
                    pattern=K.band(1, (X["yb"] + 0.48 * X["Dp"]) * s, (X["yb"] + 0.58 * X["Dp"]) * s, 0.45, soft=0.02 * s))
        H.socket("seat", (0, ytop + 0.12 * s, zs), "Body")
        H.mount = {"seat": "Torso", "saddle": {"pos": (0, ytop + 0.05 * s, zs), "size": (0.9 * s, 0.18 * s, 0.9 * s)}}

    return f


def camel_kw(**kw):
    d = dict(head="camel", ears="camel", tail="tuft", tail_len=0.9, hoof="cloven", hoof_r=1.45, leg=1.28, lt=0.85, girth=0.92, depth=0.88,
             body=0.9, slope=0.15, withers=0.05, neck_len=1.15, neck_ang=22, neck_thick=0.78, neck_flat=0.85, arch=-0.32, hs=1.0,
             head_ang=8, gait="pace", attack="bite", stride=0.9, tags=TAGS + ("mount",), shade=0.9, pupil=None,
             preview={"primary": "#C8A070", "secondary": "#8A6A44", "hoof": "#5A4636", "nose": "#3A2A28"})
    d.update(kw)
    return d


@hero("camel", "camelids")
def camel():
    humps = [(-0.45, 0.55, 0.38), (0.48, 0.5, 0.36)]
    return K.ungulate("camel", **camel_kw(hump=humps, mane="shaggy", mane_col="secondary", shaggy=0.012, extra=hump_saddle(humps)))


@hero("dromedary", "camelids")
def dromedary():
    humps = [(0.0, 0.75, 0.62)]
    return K.ungulate("dromedary", **camel_kw(hump=humps, extra=hump_saddle(humps),
                                              preview={"primary": "#D2AE7A", "secondary": "#A8845A", "hoof": "#5A4636", "nose": "#3A2A28"}))


def pompom(head, L, hs, HP):
    c = HP["cran"]
    tuft = sphere(0.24 * hs, L(0, c[3] + c[1] * 0.75, c[4] - 0.08)).noise(0.03 * hs, 12 / hs, 21)
    return head.su(tuft, 0.06)


def llama_kw(**kw):
    d = dict(head="camel", ears="llama", ear_scale=1.25, tail="stub", hoof="cloven", hoof_r=1.1, leg=1.05, lt=0.75, girth=0.9, depth=0.95, body=0.85,
             neck_len=1.12, neck_ang=76, neck_thick=0.8, neck_flat=0.9, arch=0.0, hs=0.78, head_ang=12, withers=0.05,
             head_over={"lip": 0.03}, wool=0.035, gait="pace", attack="bite", tags=TAGS, shade=0.95, pupil=None,
             preview={"primary": "#F2EEE6", "secondary": "#8A6A4A", "hoof": "#3A2E26", "nose": "#3A2A28"})
    d.update(kw)
    return d


@hero("llama", "camelids")
def llama():
    return K.ungulate("llama", **llama_kw(s=0.7))


@hero("alpaca", "camelids")
def alpaca():
    return K.ungulate("alpaca", **llama_kw(s=0.6, wool=0.05, leg=0.95, girth=1.0, neck_thick=1.0, neck_len=0.95, hs=0.72, ear_scale=0.85, head_mod=pompom,
                                           preview={"primary": "#F7F2EA", "secondary": "#D8C4A8", "hoof": "#3A2E26", "nose": "#3A2A28"}))


A = NOTFOOD
MAP = [
    ("camel", "camel, camels, bactrian camel, bactrian, camel caravan, war camel", A),
    ("dromedary", "dromedary, dromedaries, arabian camel, racing camel", A),
    ("llama", "llama, llamas, baby llama, guanaco, vicuna, cria", A),
    ("alpaca", "alpaca, alpacas, baby alpaca", A),
]
