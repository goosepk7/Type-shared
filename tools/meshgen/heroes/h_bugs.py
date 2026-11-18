"""Bugs: insects, spiders, scorpions, centipedes, worms, snails.

Parametric archetypes (each yields several heroes):
* _ant      ant, queen ant, termite: heart-shaped head, elbowed antennae, mandibles, narrow mesosoma, petiole node(s),
            big gaster.
* _beetle   beetle (scarab), stag beetle, rhinoceros beetle, hercules beetle, ladybug, firefly, weevil, cockroach:
            pronotum shield, domed elytra split down the middle (pattern masks for spots), horns / mandibles / snout.
* _bee      bee, bumblebee, wasp, hornet: fuzzy thorax, striped abdomen with stinger, four translucent buzzing wings.
* _lepid    butterfly, monarch butterfly, moth, luna moth: slender furry body, big patterned wings (pattern masks).
* _flyer    fly, mosquito, dragonfly, cicada: two or four glassy wings, compound eyes, proboscis.
* _hopper   grasshopper, cricket, flea: big jumping hind legs (thick femur, folded tibia), hop gait.
* _mantis   praying mantis, stick insect, water strider: long thin bodies, raptorial strike arms / stilt legs.
* _spider   spider, tarantula, black widow, jumping spider, tick, scorpion: cephalothorax + abdomen, eight 3-segment
            legs in an alternating tetrapod gait, fangs, palps, eye clusters; scorpion adds pincers and a segmented
            tail with a stinger.
* _crawler  centipede, millipede, caterpillar, earthworm: a chain of segment bones with leg-pair pieces.
* _snail    snail, slug: a muscular foot, eye stalks, a spiral shell.

Insect legs are three pieces (femur, tibia, tarsus) on Leg / Knee / Foot bones; walking uses a tripod gait (six
legs) or alternating tetrapods (eight legs) with lift; fliers use gait "buzz" with fast wing flutter.
"""
import math

import numpy as np

import sdf as S
from sdf import sphere, ellipsoid, capsule, round_cone, tube, plane, torus  # noqa: F401
from kit import Hero, hero, stripes, spots, gradient, combine  # noqa: F401
import motion_bugs as MB
from bugkit import *  # noqa: F401,F403


# ================================================================================================ ants & termites
def _ant(hid, s=1.0, gaster=1.0, head=1.0, legl=1.0, wings=False, termite=False, mand=1.0, fuzz=0.0, node2=False,
         stinger=False, preview=None, col_legs="primary"):
    H = Hero(hid, plan="Insect", gait="scuttle", tags=["insect", "bug"])
    H.preview = preview or {}
    G = gaster
    y = 1.05 * s

    def v(x, yy, z):
        return (x * s, yy * s, z * s)

    H.body(v(0, 1.05, 0))
    seg = stripes(lambda Q: Q[:, 2] / s, 1 / 0.32 / G, width=0.18, depth=0.3)
    # ---------------------------------------------------------------- mesosoma (thorax)
    if termite:
        th = tube([v(0, 1.0, -0.7), v(0, 1.05, -0.35), v(0, 1.0, 0.05), v(0, 0.98, 0.4)], [0.24 * s, 0.3 * s, 0.28 * s, 0.26 * s], k=0.1)
        th = th.su(ellipsoid(0.36 * s, 0.14 * s, 0.26 * s, v(0, 1.1, -0.5)), 0.08)            # pronotum plate
        th = th.su(ellipsoid(0.32 * s, 0.22 * s, 0.24 * s, v(0, 1.02, 0.0)), 0.1)
    else:
        th = tube([v(0, 1.08, -0.78), v(0, 1.2, -0.42), v(0, 1.1, -0.05), v(0, 0.98, 0.25), v(0, 1.05, 0.5)],
                  [0.2 * s, 0.3 * s, 0.25 * s, 0.19 * s, 0.2 * s], k=0.12)
        th = th.su(ellipsoid(0.29 * s, 0.27 * s, 0.32 * s, v(0, 1.22, -0.45)), 0.1)           # pronotum
        th = th.su(ellipsoid(0.24 * s, 0.24 * s, 0.24 * s, v(0, 1.08, 0.38)), 0.08)           # propodeum
        th = th.su(ellipsoid(0.22 * s, 0.18 * s, 0.26 * s, v(0, 0.92, -0.2)), 0.1)            # sternum (leg sockets)
        if wings:
            th = th.su(ellipsoid(0.32 * s, 0.3 * s, 0.42 * s, v(0, 1.25, -0.15)), 0.15)       # flight muscles (queen)
    H.piece("Torso", "Body", th, col="primary", mat="hard", tris=1200, res=120, pattern=gradient(1, 0.8 * s, 1.4 * s, 0.85, 1.0))
    # ---------------------------------------------------------------- head
    hb = A(v(0, 1.12, -0.72))
    H.bone("Head", "Body", T(hb))
    HS = head * s
    hc = A(v(0, 1.22, -1.2))

    def h(x, yy, z):
        return T(hc + A(x, yy, z) * HS)

    if termite:
        hd = ellipsoid(0.36 * HS, 0.3 * HS, 0.48 * HS, h(0, 0.02, -0.05))
        hd = hd.su(ellipsoid(0.28 * HS, 0.2 * HS, 0.2 * HS, h(0, -0.04, -0.45)), 0.1)
    else:
        hd = ellipsoid(0.44 * HS, 0.4 * HS, 0.36 * HS, h(0, 0, 0))
        hd = hd.su(sphere(0.26 * HS, h(0.2, 0.14, 0.14)).mirror_x(), 0.14)                      # heart-shaped back lobes
        hd = hd.su(ellipsoid(0.26 * HS, 0.14 * HS, 0.16 * HS, h(0, -0.14, -0.33)), 0.1)         # clypeus
        hd = hd.ss(ellipsoid(0.05 * HS, 0.2 * HS, 0.25 * HS, h(0, 0.1, -0.15)), 0.04)          # frontal groove
    hd = hd.su(round_cone(T(hb + A(0, 0, 0.1) * s), h(0, -0.02, 0.2), 0.12 * s, 0.16 * HS), 0.06)  # neck
    H.piece("HeadP", "Head", hd, col="primary", mat="hard", tris=1300, res=120, role="head", pri=1.1)
    if termite:
        H.mprim("Eye#", "Head", "Ball", (0.07 * HS,) * 3, h(0.3, 0.08, -0.28), col="cream", mat="hard", pri=1.3, role="eye")
    else:
        bug_eyes(H, "Head", h(0.38, 0.1, -0.12), 0.11 * HS, flat=0.7)
    # mandibles (bone at the hinge, closing = tips swing inward)
    mz = -0.45 if not termite else -0.6
    mb = A(h(0.17, -0.18, mz))
    H.mbone("Mand#", "Head", T(mb))
    L = 0.42 * mand * HS
    mpts = [mb, mb + A(0.1, -0.02, -0.55) * L, mb + A(0.03, -0.04, -0.95) * L, mb + A(-0.2, -0.05, -1.12) * L]
    md = tube([T(p) for p in mpts], [0.075 * HS, 0.065 * HS, 0.045 * HS, 0.02 * HS], k=0.03)
    md = md.scale3(1, 1, 1) if False else md
    for i in range(3):
        c = mpts[1] + (mpts[3] - mpts[1]) * (0.2 + 0.3 * i)
        md = md.su(round_cone(T(c), T(c + A(-0.09, 0, -0.02) * HS), 0.025 * HS, 0.008 * HS), 0.015)
    H.mpiece("Mandible#", "Mand#", md, col="dark", mat="hard", tris=300, role="jaw", pri=1.5)
    # antennae
    if termite:
        base = A(h(0.24, 0.02, -0.38))
        pts = [base, base + A(0.25, 0.25, -0.2) * HS, base + A(0.45, 0.4, -0.6) * HS, base + A(0.55, 0.35, -1.0) * HS]
        antenna(H, "", T(base), pts, 0.045 * HS, 0.035 * HS, col="primary", kind="thread")
        # beads
    else:
        base = A(h(0.13, 0.05, -0.36))
        el = base + A(0.18, 0.5, -0.12) * HS
        pts = [base, el, el + A(0.3, -0.05, -0.55) * HS, el + A(0.42, -0.28, -0.95) * HS]
        antenna(H, "", T(base), pts, 0.045 * HS, 0.035 * HS, col="dark", kind="elbow", club=0.06 * HS)
    # ---------------------------------------------------------------- gaster (+ petiole)
    ab = A(v(0, 1.05, 0.58))
    H.bone("Abdomen", "Body", T(ab))
    if termite:
        gc = A(v(0, 0.98, 1.25 + 0.35 * (G - 1)))
        ga = ellipsoid(0.45 * G * s, 0.38 * G * s, 0.85 * G * s).rot(4, 0, 0).at(*T(gc))
        ga = ga.su(ellipsoid(0.3 * s, 0.26 * s, 0.25 * s, v(0, 1.0, 0.5)), 0.12)
        gpat = combine(stripes(lambda Q: Q[:, 2] / s, 1 / 0.22, width=0.2, depth=0.45), gradient(1, 0.7 * s, 1.4 * s, 1.0, 0.9))
    else:
        gc = A(v(0, 1.05 + 0.08 * (G - 1), 1.45 + 0.65 * (G - 1)))
        ga = ellipsoid(0.52 * G * s, 0.46 * G * s, 0.7 * G * s).rot(14, 0, 0).at(*T(gc))
        ga = ga.su(capsule(v(0, 1.02, 0.5), v(0, 1.02, 0.95), 0.08 * s), 0.06)                  # petiole stalk
        ga = ga.su(ellipsoid(0.13 * s, 0.2 * s, 0.1 * s, v(0, 1.17, 0.72)), 0.06)               # petiole node
        if node2:
            ga = ga.su(ellipsoid(0.14 * s, 0.15 * s, 0.11 * s, v(0, 1.08, 0.9)), 0.06)          # postpetiole
        if stinger:
            tipc = gc + A(0, -0.25, 0.7) * G * s
            ga = ga.su(round_cone(T(tipc - A(0, 0, 0.1) * s), T(tipc + A(0, -0.1, 0.25) * s), 0.05 * s, 0.01 * s), 0.03)
        gpat = combine(stripes(lambda Q: (Q[:, 2] - gc[2]) / s + 0.05, 1 / (0.3 * G), width=0.14, depth=0.4,
                               region=lambda Q: np.clip((Q[:, 2] - 0.95 * s) * 4 / s, 0, 1)), gradient(1, 0.7 * s, 1.5 * s, 1.0, 0.85))
    if fuzz:
        ga = ga.noise(fuzz * s, 22 / s, 5)
    H.piece("Gaster", "Abdomen", ga, col="primary", mat="hard", tris=1300, res=120, pattern=gpat, pri=1.05)
    # ---------------------------------------------------------------- legs
    r = tuple(x * s for x in (0.085, 0.065, 0.045, 0.034))
    LL = legl
    F = legspec(v(0.15, 0.95, -0.52), 55, 0.5 * LL * s, 1.45 * s, 1.15 * LL * s, 0.42 * s, 1.6 * LL * s, 0.04 * s)
    M = legspec(v(0.17, 0.92, -0.12), -5, 0.62 * LL * s, 1.5 * s, 1.38 * LL * s, 0.38 * s, 1.9 * LL * s, 0.04 * s)
    B = legspec(v(0.17, 0.92, 0.22), -48, 0.62 * LL * s, 1.45 * s, 1.45 * LL * s, 0.38 * s, 2.0 * LL * s, 0.04 * s)
    names = [leg(H, "F", *F, r=r, col=col_legs), leg(H, "M", *M, r=r, col=col_legs), leg(H, "B", *B, r=r, col=col_legs)]
    legs = legs_rig(names, [0.0, 0.5, 0.0])
    wings_b = []
    if wings:
        wings_b += clear_wing(H, "Wing", v(0.12, 1.45, -0.25), 2.3 * s, 0.7 * s, yaw=-78, lift=6, tris=320)
        wings_b += clear_wing(H, "HWing", v(0.12, 1.4, 0.0), 1.7 * s, 0.5 * s, yaw=-72, lift=4, tris=260)
    ants = [("AntR", 1), ("AntL", -1)]
    MB.walker(H, legs, head="Head", abd="Abdomen", ants=ants, mand=[("MandR", 1), ("MandL", -1)],
              wings=[(b, 1 if b.endswith("R") else -1) for b in wings_b], height=1.5 * s, stride=0.32, lift=0.35,
              attack="sting" if stinger else "bite")
    finish(H, mouth=h(0, -0.2, -0.85), top=h(0, 0.45, 0), mouth_bone="Head", legs=legs)
    return H


@hero("ant", "bugs")
def ant():
    return _ant("ant", preview={"primary": "#3A1E14", "secondary": "#8A3A1E", "dark": "#24120C", "bugEye": "#121014"})


@hero("queen ant", "bugs")
def queen_ant():
    return _ant("queen ant", gaster=1.45, head=1.05, wings=True, preview={"primary": "#6A3A1E", "secondary": "#2A1E14", "dark": "#2A140C",
                                                                           "bugEye": "#121014", "wingGlass": "#D8E4EE"})


@hero("termite", "bugs")
def termite():
    return _ant("termite", termite=True, gaster=1.0, head=1.15, mand=1.35, legl=0.85,
                preview={"primary": "#E8D8B0", "secondary": "#B8702A", "dark": "#8A4A1E"})


# ================================================================================================ beetles & roaches
def _beetle(hid, s=1.0, L=1.0, W=0.85, dome=0.6, yb=0.62, pron=(0.62, 0.36, 0.42), headr=(0.34, 0.26, 0.28), horn=None,
            mand=None, snout=0.0, ant="club", ant_len=1.0, legl=1.0, spines=2, spots=None, seam=True, glow=False,
            roach=False, pron_pat=None, el_pat=None, legcol="dark", headcol="dark", proncol="primary", elcol="primary",
            bellycol="dark", eye=0.09, preview=None, gait_attack="bite", cerci=False, tag=("insect", "bug", "beetle"), ridges=0, spots_geo=None, spot_col="black"):
    H = Hero(hid, plan="Insect", gait="scuttle", tags=list(tag))
    H.preview = preview or {}

    def v(x, y, z):
        return (x * s, y * s, z * s)

    le = 0.95 * L
    ze = 0.45 * L
    Pw, Ph, Pl = pron
    zp = ze - le + 0.05 - Pl * 0.55
    zh = zp - Pl * 0.85
    if roach:
        zh = zp - Pl * 0.45
    H.body(v(0, yb, zp + 0.2))
    # ---------------------------------------------------------------- pronotum + sternum (Torso)
    pr = ellipsoid(Pw * s, Ph * s, Pl * s, v(0, yb + Ph * 0.15, zp))
    if roach:
        pr = ellipsoid(Pw * s, Ph * s, Pl * s, v(0, yb + 0.05, zp)) & S.SDF(lambda p: (yb - 0.06) * s - p[:, 1])
        pr = pr.su(ellipsoid(Pw * 0.55 * s, 0.14 * s, Pl * 0.8 * s, v(0, yb - 0.03, zp + 0.1)), 0.06)
    pr = pr.su(ellipsoid(Pw * 0.7 * s, 0.22 * s, (Pl + 0.4) * s, v(0, yb - 0.12, zp + 0.25)), 0.1)     # sternum
    if horn == "rhino":
        pr = pr.su(round_cone(v(0, yb + Ph * 0.9, zp + 0.05), v(0, yb + Ph + 0.38, zp - 0.3), 0.16 * s, 0.05 * s), 0.12)
    if horn == "hercules":
        hp = [v(0, yb + Ph * 0.9, zp + 0.1), v(0, yb + Ph + 0.35, zp - 0.45), v(0, yb + Ph + 0.42, zp - 1.25), v(0, yb + Ph + 0.15, zp - 1.85)]
        hn = tube(hp, [0.2 * s, 0.13 * s, 0.09 * s, 0.04 * s], k=0.05)
        hn = hn.su(sphere(0.08 * s, v(0, yb + Ph + 0.27, zp - 1.0)).at(0, -0.08 * s, 0), 0.06)     # underside tooth
        pr = pr.su(hn, 0.1)
    if horn == "atlas":
        for sx in (1, -1):
            pr = pr.su(tube([v(0.3 * sx, yb + Ph * 0.6, zp - 0.05), v(0.45 * sx, yb + Ph + 0.2, zp - 0.55), v(0.3 * sx, yb + Ph + 0.35, zp - 1.0)],
                            [0.13 * s, 0.08 * s, 0.03 * s]), 0.08)
    if ridges:
        pr = pr.ss(ellipsoid(0.06 * s, 0.1 * s, Pl * 0.8 * s, v(0, yb + Ph * 1.1, zp)), 0.04)
    H.piece("Torso", "Body", pr, col=proncol, mat="hard", tris=1400, res=128, pattern=pron_pat, pri=1.0)
    # ---------------------------------------------------------------- elytra (+ belly) on the Abdomen bone
    H.bone("Abdomen", "Body", v(0, yb + 0.05, ze - le + 0.15))
    if roach:
        el = ellipsoid(W * s, dome * s, le * s, v(0, yb, ze)) & S.SDF(lambda p: (yb - 0.02) * s - p[:, 1])
        el = el.su(ellipsoid(W * 0.95 * s, 0.05 * s, le * 1.02 * s, v(0, yb, ze + 0.03)), 0.04)
    else:
        el = ellipsoid(W * s, dome * s, le * s, v(0, yb, ze)) & S.SDF(lambda p: (yb - 0.1) * s - p[:, 1])
        el = el.round(0.0)
    if seam:
        el = surface_cut(el, S.SDF(lambda p: np.maximum(np.abs(p[:, 0]) - 0.014 * s, (yb + 0.02) * s - p[:, 1])), 0.04 * s, 0.015 * s)
    if ridges:
        for i in range(1, ridges + 1):
            x = W * i / (ridges + 1.3)
            el = surface_cut(el, S.SDF(lambda p, x=x: np.maximum(np.abs(np.abs(p[:, 0]) - x * s) - 0.012 * s, (yb + 0.05) * s - p[:, 1])), 0.035 * s, 0.012 * s)
    H.piece("Elytra", "Abdomen", el, col=elcol, mat="hard", tris=2000, res=136, pattern=el_pat, pri=1.0)
    if spots_geo:
        dome_ = ellipsoid(W * s, dome * s, le * s, v(0, yb, ze))
        cyl = None
        for fx, fz, rr in spots_geo:
            c_ = e2(fx * W * s, (ze + fz * le) * s, rr * s, rr * s)
            cyl = c_ if cyl is None else (cyl | c_)
        cyl = cyl.mirror_x()
        shell = S.SDF(lambda p: np.abs(dome_(p) - 0.012 * s) - 0.016 * s)
        mk = shell & cyl & S.SDF(lambda p: (yb - 0.02) * s - p[:, 1])
        mk = mk & S.SDF(lambda p: 0.015 * s - np.abs(p[:, 0]) - 0.0) if False else mk
        H.piece("Spots", "Abdomen", mk, col=spot_col, mat="hard", tris=900, res=170, role="detail", pri=1.3, smooth=1, ao=False)
    bel = ellipsoid(W * 0.86 * s, 0.24 * s, le * 0.94 * s, v(0, yb - 0.08, ze))
    bel = surface_cut(bel, zgrooves(ze * s, 0.22 * s, 0.012 * s), 0.03 * s, 0.01 * s)
    if cerci:
        for sx in (1, -1):
            bel = bel.su(round_cone(v(0.2 * sx, yb - 0.05, ze + le * 0.9), v(0.35 * sx, yb + 0.02, ze + le * 1.2), 0.05 * s, 0.015 * s), 0.04)
    H.piece("Belly", "Abdomen", bel, col=bellycol, mat="hard", tris=700, res=110, pri=1.2,
            pattern=stripes(lambda Q: Q[:, 2] / s, 1 / 0.22, width=0.15, depth=0.35))
    if glow:
        H.piece("Lantern", "Abdomen", ellipsoid(0.42 * W * s, 0.16 * s, 0.26 * s, v(0, yb - 0.12, ze + le * 0.72)),
                col="glow", mat="skin", glow=True, tris=300, role="light", pri=1.3)
    # ---------------------------------------------------------------- head
    hb = A(v(0, yb + 0.02, zh + headr[2] * 0.6))
    H.bone("Head", "Body", T(hb))
    hc = A(v(0, yb - 0.02 + (0.06 if not roach else -0.08), zh))
    hx, hy, hz = headr
    hd = ellipsoid(hx * s, hy * s, hz * s, T(hc))
    hd = hd.su(ellipsoid(hx * 0.75 * s, hy * 0.6 * s, hz * 0.6 * s, T(hc + A(0, -0.06, -hz * 0.65) * s)), 0.06)   # clypeus
    if horn == "rhino":
        hp = [hc + A(0, 0.05, -hz * 0.6) * s, hc + A(0, 0.35, -hz - 0.35) * s, hc + A(0, 0.95, -hz - 0.55) * s, hc + A(0, 1.35, -hz - 0.35) * s]
        hd = hd.su(tube([T(p) for p in hp], [0.15 * s, 0.12 * s, 0.07 * s, 0.025 * s], k=0.05), 0.08)
    if horn in ("hercules", "atlas"):
        hp = [hc + A(0, 0.05, -hz * 0.6) * s, hc + A(0, 0.15, -hz - 0.45) * s, hc + A(0, 0.4, -hz - 0.9) * s, hc + A(0, 0.75, -hz - 1.05) * s]
        hd = hd.su(tube([T(p) for p in hp], [0.12 * s, 0.1 * s, 0.07 * s, 0.025 * s], k=0.05), 0.08)
    if snout:
        sp = [hc + A(0, 0, -hz * 0.5) * s, hc + A(0, -0.12, -hz - snout * 0.5) * s, hc + A(0, -0.35, -hz - snout) * s]
        hd = hd.su(tube([T(p) for p in sp], [0.12 * s, 0.09 * s, 0.07 * s], k=0.04), 0.06)
        hd = hd.su(sphere(0.085 * s, T(sp[-1])), 0.03)
    H.piece("HeadP", "Head", hd, col=headcol, mat="hard", tris=1100, res=124, role="head", pri=1.1)
    bug_eyes(H, "Head", T(hc + A(hx * 0.82, hy * 0.25, -hz * 0.35) * s), eye * s, flat=0.75)
    mands = []
    if mand == "stag":
        mb = A(T(hc + A(hx * 0.45, -0.02, -hz * 0.75) * s))
        H.mbone("Mand#", "Head", T(mb))
        mp = [mb, mb + A(0.3, 0.12, -0.45) * s, mb + A(0.38, 0.28, -1.0) * s, mb + A(0.22, 0.42, -1.45) * s, mb + A(-0.05, 0.45, -1.62) * s]
        md = tube([T(p) for p in mp], [0.12 * s, 0.11 * s, 0.09 * s, 0.07 * s, 0.035 * s], k=0.06)
        for i, t in enumerate((0.35, 0.6, 0.8)):
            c = mp[1] + (mp[3] - mp[1]) * t
            md = md.su(round_cone(T(c), T(c + A(-0.2, 0.05 + 0.05 * i, -0.03) * s), 0.05 * s, 0.015 * s), 0.03)
        md = md.su(round_cone(T(mp[3]), T(mp[3] + A(0.08, 0.2, 0.05) * s), 0.06 * s, 0.02 * s), 0.03)     # fork
        H.mpiece("Mandible#", "Mand#", md, col="secondary", mat="hard", tris=800, res=128, role="jaw", pri=1.2)
        mands = [("MandR", 1), ("MandL", -1)]
    elif mand == "small":
        mb = A(T(hc + A(hx * 0.4, -0.08, -hz * 0.8) * s))
        H.mbone("Mand#", "Head", T(mb))
        md = tube([T(mb), T(mb + A(0.08, -0.02, -0.2) * s), T(mb + A(-0.08, -0.04, -0.32) * s)], [0.06 * s, 0.05 * s, 0.02 * s], k=0.02)
        H.mpiece("Mandible#", "Mand#", md, col="darker", mat="hard", tris=220, role="jaw", pri=1.4)
        mands = [("MandR", 1), ("MandL", -1)]
    # antennae
    if snout:
        base = hc + A(0.07, -0.12, -hz - snout * 0.5) * s
        el_ = base + A(0.22, 0.25, 0.0) * s
        pts = [base, el_, el_ + A(0.15, 0.1, -0.35) * s * ant_len, el_ + A(0.2, 0.05, -0.55) * s * ant_len]
        antenna(H, "", T(base), pts, 0.035 * s, 0.03 * s, col="darker", kind="elbow", club=0.07 * s)
    elif ant == "long":
        base = hc + A(hx * 0.55, hy * 0.35, -hz * 0.6) * s
        pts = [base, base + A(0.3, 0.3, -0.5) * s * ant_len, base + A(0.9, 0.35, -1.5) * s * ant_len, base + A(1.6, 0.1, -2.4) * s * ant_len]
        antenna(H, "", T(base), pts, 0.04 * s, 0.015 * s, col="dark", kind="thread", tris=320)
    elif ant == "lamellate":
        base = hc + A(hx * 0.65, 0.0, -hz * 0.65) * s
        pts = [base, base + A(0.2, 0.12, -0.18) * s, base + A(0.32, 0.18, -0.35) * s]
        a_ = antenna(H, "", T(base), pts, 0.035 * s, 0.03 * s, col="darker", kind="thread", club=0.1 * s)
    elif ant == "comb":
        base = hc + A(hx * 0.6, hy * 0.2, -hz * 0.7) * s
        pts = [base, base + A(0.25, 0.25, -0.3) * s * ant_len, base + A(0.45, 0.35, -0.75) * s * ant_len]
        antenna(H, "", T(base), pts, 0.04 * s, 0.03 * s, col="darker", kind="thread", feather=0.09 * s)
    else:
        base = hc + A(hx * 0.62, hy * 0.2, -hz * 0.7) * s
        pts = [base, base + A(0.2, 0.18, -0.25) * s * ant_len, base + A(0.4, 0.28, -0.55) * s * ant_len, base + A(0.55, 0.3, -0.8) * s * ant_len]
        antenna(H, "", T(base), pts, 0.035 * s, 0.03 * s, col="darker", kind="thread", club=0.07 * s if ant == "club" else 0.0)
    # ---------------------------------------------------------------- legs
    r = tuple(x * s for x in (0.12, 0.1, 0.07, 0.045))
    LL = legl * 0.85
    F = legspec(v(0.3, yb - 0.18, zp + 0.05), 50, 0.48 * LL * s, (yb + 0.02) * s, 0.98 * LL * s, 0.2 * s, 1.35 * LL * s, 0.045 * s)
    M = legspec(v(0.35, yb - 0.2, zp + Pl * 0.9 + 0.1), -12, 0.6 * LL * s, (yb + 0.04) * s, 1.15 * LL * s, 0.2 * s, 1.55 * LL * s, 0.045 * s)
    B = legspec(v(0.35, yb - 0.2, zp + Pl * 0.9 + 0.55), -50, 0.6 * LL * s, (yb + 0.02) * s, 1.22 * LL * s, 0.2 * s, 1.65 * LL * s, 0.045 * s)
    names = [leg(H, "F", *F, r=r, col=legcol, spines=spines), leg(H, "M", *M, r=r, col=legcol, spines=spines),
             leg(H, "B", *B, r=r, col=legcol, spines=spines)]
    legs = legs_rig(names, [0.0, 0.5, 0.0])
    MB.walker(H, legs, head="Head", abd="Abdomen", ants=[("AntR", 1), ("AntL", -1)], mand=mands, height=1.2 * s, stride=0.3,
              lift=0.32, attack=gait_attack, period=0.6)
    finish(H, mouth=T(hc + A(0, -0.05, -hz - 0.25 - snout) * s), top=T(A(v(0, yb + Ph + 0.3, zp))), mouth_bone="Head", legs=legs)
    return H


def ladyspots(W, le, ze, yb, s):
    pts = [(0.0, 0.3), (0.45, -0.35), (0.55, 0.25), (0.3, 0.75), (0.7, 0.75)]
    cs = []
    for fx, fz in pts:
        x = W * s * (fx * 0.75 + 0.12)
        z = (ze + le * (fz * 0.7)) * s
        cs.append((x, z))

    def f(P):
        m = np.zeros(len(P))
        ax = np.abs(P[:, 0])
        for x, z in cs:
            d = np.hypot(ax - x, P[:, 2] - z)
            m = np.maximum(m, np.clip((0.2 * s - d) / (0.04 * s), 0, 1))
        return 1 - 0.93 * m * (P[:, 1] > (yb - 0.05) * s)

    return f


@hero("beetle", "bugs")
def beetle():
    return _beetle("beetle", ant="lamellate", mand="small", ridges=3, preview={"primary": "#2A3A2A", "dark": "#1A1F1A", "darker": "#121512", "bugEye": "#0E0E10"})


@hero("scarab", "bugs")
def scarab():
    return _beetle("scarab", L=0.9, W=0.95, dome=0.55, pron=(0.75, 0.38, 0.45), headr=(0.45, 0.18, 0.32), ant="lamellate", spines=3, legl=1.05,
                   proncol="primary", headcol="primary", legcol="primary", preview={"primary": "#3A7A5A", "secondary": "#C8A040", "dark": "#1A2A20", "darker": "#121A14", "bugEye": "#0E0E10"})


@hero("stag beetle", "bugs")
def stag_beetle():
    return _beetle("stag beetle", L=1.05, W=0.78, dome=0.42, pron=(0.62, 0.3, 0.4), headr=(0.48, 0.22, 0.34), mand="stag", ant="club",
                   headcol="primary", legcol="primary", preview={"primary": "#3A2418", "secondary": "#6A3A1E", "dark": "#24160E", "darker": "#160E08", "bugEye": "#0E0E10"})


@hero("rhinoceros beetle", "bugs")
def rhino_beetle():
    return _beetle("rhinoceros beetle", L=1.05, W=0.88, dome=0.6, pron=(0.7, 0.42, 0.5), headr=(0.32, 0.24, 0.28), horn="rhino", ant="lamellate",
                   headcol="primary", legcol="primary", gait_attack="ram", spines=3,
                   preview={"primary": "#4A2A18", "secondary": "#6A3A1E", "dark": "#2A180E", "darker": "#1A0E08", "bugEye": "#0E0E10"})


@hero("hercules beetle", "bugs")
def hercules_beetle():
    return _beetle("hercules beetle", L=1.1, W=0.85, dome=0.58, pron=(0.68, 0.4, 0.5), headr=(0.3, 0.22, 0.26), horn="hercules", ant="lamellate",
                   elcol="secondary", headcol="primary", legcol="primary", gait_attack="ram", spines=3,
                   el_pat=spots(0.35, 0.09, depth=0.6, seed=4),
                   preview={"primary": "#1E1A16", "secondary": "#B8A060", "dark": "#141210", "darker": "#0E0C0A", "bugEye": "#0E0E10"})


@hero("ladybug", "bugs")
def ladybug():
    L, W, yb = 0.82, 0.95, 0.6
    return _beetle("ladybug", L=L, W=W, dome=0.82, yb=yb, pron=(0.55, 0.3, 0.3), headr=(0.3, 0.2, 0.2), ant="club", ant_len=0.6, legl=0.9,
                   spines=0, proncol="black", headcol="black", legcol="black", bellycol="black",
                   spots_geo=[(0.22, -0.45, 0.16), (0.55, -0.05, 0.19), (0.3, 0.38, 0.17), (0.62, 0.55, 0.12), (0.0, -0.7, 0.13)],
                   pron_pat=None, preview={"primary": "#D8281E", "secondary": "#1E1E1E", "bugEye": "#0E0E10"})


@hero("firefly", "bugs")
def firefly():
    return _beetle("firefly", L=1.15, W=0.58, dome=0.28, pron=(0.5, 0.18, 0.4), headr=(0.24, 0.2, 0.2), ant="thread", ant_len=1.3, legl=0.95,
                   spines=0, glow=True, roach=True, proncol="secondary", headcol="black", legcol="black", eye=0.1,
                   pron_pat=lambda P: 1 - 0.0 * P[:, 0],
                   preview={"primary": "#3A3A2A", "secondary": "#E8A84A", "glow": "#F2F27A", "bugEye": "#0E0E10"})


@hero("weevil", "bugs")
def weevil():
    return _beetle("weevil", L=0.9, W=0.62, dome=0.62, pron=(0.42, 0.34, 0.42), headr=(0.2, 0.2, 0.2), snout=0.75, legl=1.05, spines=0,
                   proncol="primary", headcol="primary", legcol="primary", ridges=2,
                   el_pat=spots(0.22, 0.06, depth=0.35, seed=9), preview={"primary": "#5A4A3A", "dark": "#2A2018", "darker": "#1A140E", "bugEye": "#0E0E10"})


@hero("cockroach", "bugs")
def cockroach():
    return _beetle("cockroach", L=1.25, W=0.82, dome=0.22, yb=0.5, pron=(0.6, 0.16, 0.42), headr=(0.24, 0.24, 0.2), ant="long", ant_len=1.2,
                   legl=1.2, spines=4, roach=True, seam=False, proncol="primary", headcol="dark", legcol="primary", cerci=True,
                   pron_pat=combine(lambda P: 1 - 0.55 * np.clip((0.35 - np.abs(P[:, 0])) / 0.1, 0, 1) * (P[:, 1] > 0.5)),
                   el_pat=gradient(2, -0.5, 1.5, 0.85, 1.0),
                   preview={"primary": "#7A3A18", "secondary": "#C8902A", "dark": "#3A1A0C", "darker": "#24100A", "bugEye": "#0E0E10"})
