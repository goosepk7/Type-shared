"""Deer, antelopes and giraffes: deer (stag), fawn, reindeer, elk, moose, gazelle, impala, antelope (oryx), giraffe,
okapi. Built by hoofkit.ungulate: slender long legs with cloven hooves, deer heads with a wet nose pad and big mobile
ears, branching / palmate antlers or ringed horns, flag tails. Deer and antelopes bound (pronk) and gore with their
antlers / horns; giraffes pace and kick. Wild animals: clean backs (no saddle), but every one is rideable (seat set).
"""
import numpy as np

from kit import hero, stripes, combine, gradient
from map import NOTFOOD
import hoofkit as K

TAGS = ("ungulate", "cervid")


def deer_kw(**kw):
    d = dict(head="deer", ears="deer", tail="flag", hoof="cloven", leg=1.2, lt=0.68, hoof_r=0.75, girth=0.74, depth=0.8, body=0.78,
             neck_len=0.95, neck_ang=58, neck_thick=0.8, neck_flat=0.85, arch=0.1, withers=0.12, hs=1.18, head_ang=42, tuck=1.0,
             gait="bound", attack="gore", tags=TAGS, shade=0.8, pupil="bar", eye_col=[0.12, 0.07, 0.05],
             preview={"primary": "#A0703E", "secondary": "#F2E6D2", "hoof": "#2B2420", "nose": "#2A2222", "horn": "#BFA27A"})
    d.update(kw)
    return d


@hero("deer", "cervids")
def deer():
    return K.ungulate("deer", **deer_kw(s=0.78, horns="antler", horn_scale=1.15))


@hero("fawn", "cervids")
def fawn():
    return K.ungulate("fawn", **deer_kw(s=0.5, leg=1.32, hs=1.3, ear_scale=1.15, girth=0.78, body=0.8, stride=0.9,
                                        pattern=K.light_spots(0.13, 0.034, depth=0.35, seed=3,
                                                              region=lambda Q: np.clip((Q[:, 1] - 1.42) / 0.1, 0, 1) * np.clip((0.75 - Q[:, 2]) / 0.15, 0, 1)),
                                        preview={"primary": "#C08A52", "secondary": "#F7F2EA", "hoof": "#2B2420", "nose": "#2A2222"}))


@hero("reindeer", "cervids")
def reindeer():
    return K.ungulate("reindeer", **deer_kw(s=0.82, leg=1.0, lt=0.85, hoof_r=1.25, girth=0.95, depth=1.0, horns="reindeer", mane="shaggy",
                                            mane_col="secondary", neck_thick=0.85, tail="stub", shade=0.85, tags=TAGS + ("christmas",),
                                            preview={"primary": "#8A7058", "secondary": "#F2EEE6", "hoof": "#2B2420", "nose": "#2A2222", "horn": "#C9B08A"}))


@hero("elk", "cervids")
def elk():
    return K.ungulate("elk", **deer_kw(s=0.98, leg=1.12, lt=0.8, girth=0.92, depth=0.98, horns="elk", mane="shaggy", mane_col="secondary",
                                       neck_thick=0.85, hs=1.05, legs_dark=0.35,
                                       preview={"primary": "#9A7048", "secondary": "#3E2A1C", "hoof": "#2B2420", "nose": "#2A2222", "horn": "#C2A57E"}))


@hero("moose", "cervids")
def moose():
    return K.ungulate("moose", **deer_kw(s=1.1, leg=1.38, lt=0.95, hoof_r=1.1, girth=0.95, depth=1.05, body=0.84, withers=0.65, slope=0.3,
                                         head="moose", hs=1.12, head_ang=55, neck_len=0.62, neck_ang=40, neck_thick=1.0, horns="palmate", horn_scale=1.25, tuck=0.5,
                                         ears="moose", bell=0.7, tail="stub", gait="trot", attack="gore", shade=0.85, legs_dark=0.0,
                                         preview={"primary": "#4A3626", "secondary": "#8E7458", "hoof": "#2B2420", "nose": "#2A2222", "horn": "#C2A57E"}))


def flank(s, leg, depth_, a=0.28, b=0.4, depth=0.75):
    """Dark flank stripe (gazelle / oryx) limited to the barrel."""
    yb, Dp = 1.8 * leg * s, 1.35 * depth_ * s
    return K.band(1, yb + a * Dp, yb + b * Dp, depth, soft=0.04 * s,
                  region=lambda Q: np.clip((Q[:, 2] + 0.95 * s) / (0.2 * s), 0, 1) * np.clip((0.95 * s - Q[:, 2]) / (0.2 * s), 0, 1))


@hero("gazelle", "cervids")
def gazelle():
    s = 0.6
    return K.ungulate("gazelle", **deer_kw(s=s, leg=1.25, lt=0.6, girth=0.72, horns="gazelle", horn_scale=1.0, ear_scale=1.05,
                                           pattern=flank(s, 1.25, 0.88), shade=0.9,
                                           preview={"primary": "#D8A868", "secondary": "#F2EAE0", "hoof": "#2B2420", "nose": "#2A2222", "horn": "#3A322A"}))


@hero("impala", "cervids")
def impala():
    s = 0.68
    return K.ungulate("impala", **deer_kw(s=s, leg=1.22, lt=0.64, girth=0.76, horns="impala", shade=0.78,
                                          preview={"primary": "#C88A4A", "secondary": "#F2EEE6", "hoof": "#2B2420", "nose": "#2A2222", "horn": "#3A322A"}))


@hero("antelope", "cervids")
def antelope():
    s = 0.8
    return K.ungulate("antelope", **deer_kw(s=s, leg=1.08, lt=0.75, girth=0.86, depth=0.95, horns="oryx", tail="tuft", tail_len=0.8,
                                            pattern=flank(s, 1.08, 0.95, 0.3, 0.38, 0.7), legs_dark=0.45, head_ang=48, gait="gallop",
                                            preview={"primary": "#C9B79A", "secondary": "#2A2420", "hoof": "#2B2420", "nose": "#2A2222", "horn": "#2A2420"}))


@hero("giraffe", "cervids")
def giraffe():
    return K.ungulate("giraffe", **deer_kw(s=0.95, leg=1.5, lt=0.85, hoof_r=1.25, girth=0.85, depth=0.95, body=0.82, slope=0.75, withers=0.35,
                                           neck_len=1.55, neck_ang=68, neck_thick=0.78, arch=0.0, head="giraffe", hs=0.82, head_ang=60,
                                           ears="giraffe", horns="ossicones", mane="brush", mane_col="secondary", tail="tuft", tail_len=1.2,
                                           pattern=K.voronoi_net(0.42, line=0.12, depth=0.55, seed=11), shade=0.95, graze=0.35, gait="pace", attack="buck",
                                           stride=0.85, heavy=0.2,
                                           preview={"primary": "#E8C08A", "secondary": "#7A4A22", "hoof": "#2B2420", "nose": "#2A2222"}))


def okapi_legs(s):
    st = stripes(lambda Q: Q[:, 1] / s * 1.6 + 0.15 * Q[:, 2] / s, 2.4, width=0.45, depth=0.9, wobble=0.04, seed=8)

    def f(Q):
        y = Q[:, 1] / s
        z = Q[:, 2] / s
        reg = np.clip((1.75 - y) / 0.3, 0, 1) * np.clip((y - 0.35) / 0.1, 0, 1)
        reg = np.maximum(reg, np.clip((z - 0.95) / 0.15, 0, 1) * np.clip((2.6 - y) / 0.3, 0, 1))
        m = st(Q)
        return 1 - (1 - m) * reg
    return f


@hero("okapi", "cervids")
def okapi():
    s = 0.85
    return K.ungulate("okapi", **deer_kw(s=s, leg=1.05, lt=0.8, girth=0.88, depth=1.0, slope=0.25, withers=0.2, neck_len=1.0, neck_ang=50,
                                         neck_thick=0.85, head="giraffe", hs=0.98, ears="deer", ear_scale=1.25, tail="tuft", tail_len=0.8,
                                         pattern=okapi_legs(s), gait="trot", attack="buck", shade=0.9, legs_dark=0.0,
                                         preview={"primary": "#4A2A20", "secondary": "#F2EEE6", "hoof": "#2B2420", "nose": "#2A2222"}))


A = NOTFOOD
MAP = [
    ("deer", "deer, stag, stags, buck, hart, roe deer, red deer, white-tailed deer, whitetail, fallow deer, sika deer, chital, axis deer, "
             "mule deer, doe, hind, spectral stag, celestial stag, crystal deer, cerynean hind, musk deer, water deer, muntjac, pudu, "
             "deer spirit, forest stag, golden stag, white stag, !mouse deer, !deer mouse, !reindeer", A),
    ("fawn", "fawn, fawns, baby deer, mouse deer, dik-dik, dik dik, chevrotain, bambi", A),
    ("reindeer", "reindeer, caribou, rudolph, santa's reindeer", A),
    ("elk", "elk, wapiti, irish elk, megaloceros, sambar", A),
    ("moose", "moose, moose calf, bull moose", A),
    ("gazelle", "gazelle, gazelles, springbok, thomson's gazelle, blackbuck, gerenuk, saiga, pronghorn, klipspringer, steenbok, duiker", A),
    ("impala", "impala, impalas, nyala, kudu, bongo, sitatunga, bushbuck, eland, waterbuck, topi, hartebeest, nilgai", A),
    ("antelope", "antelope, antelopes, oryx, gemsbok, addax, sable antelope, roan antelope, gnu, wildebeest, scimitar oryx", A),
    ("giraffe", "giraffe, giraffes, baby giraffe, giraffe calf, camelopard", A),
    ("okapi", "okapi, okapi calf", A),
]
