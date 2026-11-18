"""Cattle, goats, sheep and pigs: cow, bull, ox, calf, bison, water buffalo, yak, sheep, ram, goat, mountain goat,
ibex, pig, boar, warthog. Built by hoofkit.ungulate: heavy barrels on shorter legs with cloven hooves, broad cattle
heads with a wet nose pad, dewlaps, horns of every shape (curved bull horns, sweeping buffalo crescents, bison hooks,
spiral ram curls, scimitar goat horns), wool and shaggy skirts, pig snouts with curly tails, boar tusks. Cattle trot
and gore (head down charge and toss), goats and rams rear and butt, pigs charge.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from kit import hero, combine
from map import NOTFOOD
import hoofkit as K

TAGS = ("ungulate", "bovid")


def cattle_kw(**kw):
    d = dict(head="cow", ears="cow", tail="tuft", tail_len=1.15, hoof="cloven", hoof_r=1.2, leg=0.78, lt=1.05, girth=1.2, depth=1.15,
             body=1.0, slope=0.0, withers=0.12, neck_len=0.62, neck_ang=32, neck_thick=1.25, neck_flat=0.95, arch=0.04, dewlap=0.35,
             hs=1.22, head_ang=52, gait="trot", attack="gore", heavy=0.4, tags=TAGS + ("cattle",), shade=0.9, pupil=None,
             mane_col="secondary", eye_col=[0.12, 0.08, 0.06],
             preview={"primary": "#8A5E3A", "secondary": "#2A2018", "hoof": "#2B2420", "nose": "#3A2A28", "horn": "#E6DCC4"})
    d.update(kw)
    return d


def cow_patches(s=1.0):
    return K.patches(0.95 * s, 0.4 * s, depth=0.93, seed=5)


@hero("cow", "bovids")
def cow():
    return K.ungulate("cow", **cattle_kw(horns="cow", udder=True, belly=0.25, pattern=cow_patches(), shade=0.97, mane_col="secondary",
                                         preview={"primary": "#F2F0EC", "secondary": "#1A1A1A", "hoof": "#3A3030", "nose": "#D89A9A", "horn": "#E6DCC4"}))


def nose_ring(H, X):
    hp, hs, HP = X["hp"], X["hs"], X["HP"]
    pd = HP["pad"]
    c = hp(0, pd[3] - 0.12, pd[4] + 0.0)
    ring = torus(0.07 * hs, 0.016 * hs, axis=0).at(*c)
    H.piece("NoseRing", "Head", ring, col="gold", mat="metal", tris=260, role="detail", pri=2.0, ao=False)


@hero("bull", "bovids")
def bull():
    return K.ungulate("bull", **cattle_kw(horns="bull", girth=1.3, neck_thick=1.55, withers=0.45, lt=1.15, hs=1.15, extra=nose_ring,
                                          preview={"primary": "#3A2A20", "secondary": "#1C1410", "hoof": "#2B2420", "nose": "#2A2020", "horn": "#E6DCC4", "gold": "#E8B53A"}))


def yoke(H, X):
    """Wooden neck yoke: a beam across the top of the neck and a bow under it."""
    s, dn, nperp = X["s"], X["dn"], X["nperp"]
    p, r = X["neck_pt"](0.25)
    na = math.degrees(math.atan2(dn[1], -dn[2]))
    c = p + nperp * (r + 0.07 * s)
    beam = round_box(0.85 * s, 0.075 * s, 0.1 * s, 0.035 * s, (0, 0, 0)).rot(na * 0.0, 0, 0).at(*c)
    bow = torus(r * 1.08, 0.035 * s, axis=2).rot(na, 0, 0).at(*p) & half_space(1, 1, float(p[1] + 0.1 * s))
    H.piece("Yoke", "Neck", beam | bow, col="wood", mat="wood", tris=700, role="detail", pri=1.6)


@hero("ox", "bovids")
def ox():
    return K.ungulate("ox", **cattle_kw(s=1.08, horns="longhorn", horn_scale=0.7, girth=1.28, neck_thick=1.4, withers=0.3, extra=yoke,
                                        preview={"primary": "#8A5E3A", "secondary": "#E2D2BC", "hoof": "#2B2420", "nose": "#2A2020", "horn": "#E6DCC4", "wood": "#8A5A33"}))


@hero("calf", "bovids")
def calf():
    return K.ungulate("calf", **cattle_kw(s=0.6, leg=1.05, lt=0.9, girth=1.0, depth=1.0, hs=1.4, neck_len=0.7, dewlap=0.0, neck_thick=1.0,
                                          ear_scale=1.2, pattern=cow_patches(0.6), shade=0.97, stride=0.9, attack="butt",
                                          preview={"primary": "#F2EEE6", "secondary": "#7A4A2A", "hoof": "#3A3030", "nose": "#D89A9A"}))


@hero("bison", "bovids")
def bison():
    return K.ungulate("bison", **cattle_kw(s=1.05, leg=0.74, hump=[(-0.9, 0.6, 0.65)], withers=0.6, slope=0.3, girth=1.2, depth=1.25,
                                           body=0.95, neck_len=0.45, neck_ang=12, neck_thick=1.6, head_ang=72, hs=1.15, horns="bison",
                                           mane="shaggy", mane_col="secondary", beard=0.7, shaggy=0.02, tail="tuft", tail_len=0.8,
                                           head_over={"ear": (0.27, 0.0, -0.1)}, ear_scale=0.75,
                                           preview={"primary": "#5A3E28", "secondary": "#2A1E14", "hoof": "#2B2420", "nose": "#2A2020", "horn": "#2A2420"}))


@hero("water buffalo", "bovids")
def water_buffalo():
    return K.ungulate("water buffalo", **cattle_kw(s=1.05, horns="buffalo", girth=1.25, hs=1.12, head_ang=48, neck_ang=18, dewlap=0.2,
                                                   legs_dark=0.0, shade=0.92,
                                                   preview={"primary": "#3A3634", "secondary": "#8A8680", "hoof": "#2B2420", "nose": "#2A2020", "horn": "#3A3634"}))


@hero("cape buffalo", "bovids")
def cape_buffalo():
    return K.ungulate("cape buffalo", **cattle_kw(s=1.05, horns="cape", horn_scale=1.3, girth=1.3, hs=1.12, neck_thick=1.45, withers=0.35, dewlap=0.2, ear_scale=1.15,
                                                  preview={"primary": "#2E2A28", "secondary": "#1A1816", "hoof": "#2B2420", "nose": "#2A2020", "horn": "#2A2624"}))


def yak_extra(H, X):
    K.skirt(H, X, length=0.62, col="primary", amp=0.035)


@hero("yak", "bovids")
def yak():
    return K.ungulate("yak", **cattle_kw(s=1.0, leg=0.82, horns="bull", horn_scale=0.95, withers=0.45, girth=1.2, shaggy=0.025, tail="horse",
                                         tail_len=0.8, mane="shaggy", mane_col="primary", dewlap=0.0, extra=yak_extra, head_ang=60,
                                         preview={"primary": "#2E2622", "secondary": "#F2EEE6", "hoof": "#2B2420", "nose": "#2A2020", "horn": "#E6DCC4"}))


# ------------------------------------------------------------------------------------------------ sheep & goats
def caprine_kw(**kw):
    d = dict(head="goat", ears="goat", tail="stub", tail_len=0.7, hoof="cloven", hoof_r=0.85, leg=0.95, lt=0.72, girth=0.92, depth=1.0,
             body=0.8, withers=0.08, tuck=0.45, neck_len=0.68, neck_ang=50, neck_thick=0.85, neck_flat=0.9, arch=0.05, hs=1.05, head_ang=45,
             gait="trot", attack="butt", tags=TAGS + ("caprine",), shade=0.9, pupil="bar", eye_col=[0.85, 0.66, 0.2],
             preview={"primary": "#E8E2D8", "secondary": "#6E5A44", "hoof": "#2B2420", "nose": "#3A2A28", "horn": "#9A8A70"})
    d.update(kw)
    return d


@hero("sheep", "bovids")
def sheep():
    return K.ungulate("sheep", **caprine_kw(s=0.62, head="sheep", ears="sheep", leg=0.72, girth=1.3, depth=1.25, body=0.92, neck_len=0.48,
                                            neck_thick=1.25, wool=0.075, face_col="secondary", leg_col="secondary", hs=1.08,
                                            preview={"primary": "#F2EEE6", "secondary": "#2A2420", "hoof": "#1E1A18", "nose": "#2A2020"}))


@hero("lamb", "bovids")
def lamb():
    return K.ungulate("lamb", **caprine_kw(s=0.42, head="sheep", ears="sheep", leg=0.95, girth=1.15, depth=1.1, body=0.85, neck_len=0.6,
                                           neck_thick=1.15, wool=0.06, hs=1.4, ear_scale=1.15, face_col="primary",
                                           preview={"primary": "#FFFDF8", "secondary": "#E8DED0", "hoof": "#3A3030", "nose": "#D89A9A"}))


@hero("ram", "bovids")
def ram():
    return K.ungulate("ram", **caprine_kw(s=0.72, head="sheep", ears="sheep", horns="ram", girth=1.1, depth=1.1, neck_thick=1.15, hs=1.05,
                                          ear_scale=0.8, shade=0.85,
                                          preview={"primary": "#8E7458", "secondary": "#F2EEE6", "hoof": "#2B2420", "nose": "#2A2020", "horn": "#C9B898"}))


@hero("goat", "bovids")
def goat():
    return K.ungulate("goat", **caprine_kw(s=0.62, horns="goat", beard=0.9, depth=0.92, girth=0.85))


@hero("mountain goat", "bovids")
def mountain_goat():
    return K.ungulate("mountain goat", **caprine_kw(s=0.7, horns="mountain", beard=1.0, shaggy=0.022, withers=0.4, girth=1.05, depth=1.08,
                                                    leg=0.9, lt=0.85, mane="shaggy", mane_col="primary", ears="goat", ear_scale=0.75,
                                                    preview={"primary": "#F7F7F4", "secondary": "#2A2420", "hoof": "#1E1A18", "nose": "#2A2020", "horn": "#1E1A18"}))


@hero("ibex", "bovids")
def ibex():
    return K.ungulate("ibex", **caprine_kw(s=0.72, horns="ibex", beard=0.4, girth=0.98, lt=0.8, shade=0.82,
                                           preview={"primary": "#9E8064", "secondary": "#3E3026", "hoof": "#2B2420", "nose": "#2A2020", "horn": "#5A4A3A"}))


# ------------------------------------------------------------------------------------------------ pigs
def pig_kw(**kw):
    d = dict(head="pig", ears="pig", tail="curl", hoof="cloven", hoof_r=0.75, leg=0.58, lt=0.85, girth=1.25, depth=1.22, body=0.88,
             withers=0.0, neck_len=0.36, neck_ang=15, neck_thick=1.5, neck_flat=1.0, arch=0.0, hs=1.15, head_ang=22, gait="trot",
             attack="gore", tags=("ungulate", "pig"), shade=0.95, pupil=None, eye_col=[0.12, 0.08, 0.06],
             preview={"primary": "#F2A8B0", "secondary": "#D8808A", "hoof": "#8A6A6A", "nose": "#D8808A"})
    d.update(kw)
    return d


@hero("pig", "bovids")
def pig():
    return K.ungulate("pig", **pig_kw(s=0.6))


@hero("boar", "bovids")
def boar():
    return K.ungulate("boar", **pig_kw(s=0.65, leg=0.7, girth=1.1, depth=1.25, body=0.82, withers=0.55, slope=0.2, hs=1.45, brush_h=0.38, ears="deer", ear_scale=0.55,
                                       horns="tusk", tail="tuft", tail_len=0.5, mane="brush", mane_col="secondary", shaggy=0.015,
                                       head_over={"muz": (0.13, 0.13, 0.22, -0.13, -0.78)},
                                       preview={"primary": "#4A3A2E", "secondary": "#2A2018", "hoof": "#2B2420", "nose": "#3A2A28", "horn": "#F2EAD8"}))


def warts(head, L, hs, HP):
    for (x, y, z, r) in ((0.24, -0.02, -0.5, 0.06), (0.2, -0.1, -0.68, 0.05)):
        head = head.su(sphere(r * hs, L(x, y, z)).mirror_x(), 0.03)
    return head


@hero("warthog", "bovids")
def warthog():
    return K.ungulate("warthog", **pig_kw(s=0.62, leg=0.75, lt=0.78, girth=1.0, depth=1.1, body=0.85, withers=0.3, hs=1.5, brush_h=0.45, ears="deer", ear_scale=0.6,
                                          horns="bigtusk", tail="tuft", tail_len=0.75, mane="brush", mane_col="secondary", head_mod=warts,
                                          head_over={"muz": (0.16, 0.12, 0.2, -0.13, -0.76)},
                                          preview={"primary": "#7A6A5E", "secondary": "#3A2E26", "hoof": "#2B2420", "nose": "#3A2A28", "horn": "#F2EAD8"}))


A = NOTFOOD
MAP = [
    ("cow", "cow, cows, cattle, dairy cow, holstein, heifer, moo cow, cash cow, steller's cow, !sea cow, !steller's sea cow", A),
    ("bull", "bull, bulls, steer, bullock, longhorn, texas longhorn, aurochs, zebu, gaur, banteng, anoa, minotaur bull, iron bull, "
             "bull rider, !skid steer, !pit bull, !pitbull, !bull terrier, !bull shark, !bull frog, !bullfrog, !red bull", A),
    ("ox", "ox, oxen, yoked ox, oxcart ox, takin", A),
    ("calf", "calf, calves, baby cow, veal calf, !moose calf, !giraffe calf, !okapi calf", A),
    ("bison", "bison, buffalo, american buffalo, wisent, european bison, !water buffalo, !cape buffalo, !buffalo wings", A),
    ("water buffalo", "water buffalo, carabao, arni", A),
    ("cape buffalo", "cape buffalo, african buffalo", A),
    ("yak", "yak, yaks, highland cow, highland cattle, musk ox, muskox", A),
    ("sheep", "sheep, ewe, ewes, cloud sheep, star sheep, merino, black sheep, flock of sheep", A),
    ("lamb", "lamb, lambs, baby sheep, little lamb, sacrificial lamb, !lamb chop, !lamb chops", A),
    ("ram", "ram, rams, bighorn sheep, bighorn, mouflon, dall sheep, argali, barbary sheep, urial, battering ram goat, !battering ram", A),
    ("goat", "goat, goats, kid goat, billy goat, nanny goat, pygmy goat, goatling, scapegoat, !goat cheese", A),
    ("mountain goat", "mountain goat, serow, chamois, tahr, goral", A),
    ("ibex", "ibex, markhor, alpine ibex", A),
    ("pig", "pig, pigs, piglet, piglets, hog, sow, swine, piggy, pot-bellied pig, guinea hog, potbelly pig, !guinea pig, !sea pig, "
            "!pig iron", A),
    ("boar", "boar, boars, wild boar, razorback, calydonian boar, erymanthian boar, iron boar, peccary, javelina, babirusa, "
             "red river hog, giant forest hog, bearded pig, wild pig, feral hog, war boar", A),
    ("warthog", "warthog, warthogs, pumbaa", A),
]
