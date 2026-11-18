"""Landmyth quadrupeds: cryptids (chupacabra, jersey devil, displacer beast, hodag, squonk, ahuizotl), prehistoric
land mammals (chalicotherium, gorgonopsid, lystrosaurus, macrauchenia) and ammit, from one parametric beast builder.

Part of the landmyth family (see h_landmyth.py for the shared helpers and the MAP). NOTE: build.py hashes only this
file + kit.py: after a change in h_landmyth.py helpers / h_monsters / mythic_geo rebuild with --force.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF
from kit import Hero, hero, stripes, spots, gradient, combine
import motion
import motion_landmyth as ml
import mythic_geo as mg
import h_monsters as HM
from h_landmyth import A, T, nrm, hard, feathers, feather_mask, feather_wing, tail_fan, bird_legs, human_ctx, human_head, crest_plumes, crown

# ================================================================================================ quadruped beasts
BEAST = dict(
    s=1.0, leg=1.0, body=1.0, girth=1.0, hind=1.0, fleg=1.0, stance=1.0, legT=1.0,
    neck_len=1.0, neck_ang=35.0, neck_thick=1.0, head=1.0, pitch=8.0,
    # head shape (local units, scaled by hs; muzzle toward -z)
    cran=(0.42, 0.4, 0.45), snout=(0.3, 0.24, 0.55), snout_y=-0.02, snout_z=-0.4, jaw=(0.24, 0.12, 0.5), brow=0.6,
    eye=(0.27, 0.16, -0.42, 0.085), eye_look=(0.5, 0.05, -1.0), pupil="slit", eye_col="iris",
    ears=None, ear_size=1.0, horns=None, horn_size=1.0, teeth=0, fangs=0.0, sabers=0.0, tusks=0.0, trunk=0.0, beak=False,
    nostrils=True, grin=0.0, sad=0.0, mane=0.0, wart=0.0,
    front_foot="paw", hind_foot="paw", claws=0.0, knuckle=False,
    tail="taper", tail_len=1.0, tail_thick=1.0, tail_spikes=0, tail_up=0.0,
    spines=0, spine_h=0.35, spine_col="secondary", spikes_tail=False,
    pattern=None, shade=0.82, belly_col=None, skin="skin", fur=0.0,
    six=False, tentacles=False, wings=False,
    attack="bite", stride=0.42, walk=1.1, gait="trot", tags=(), preview={}, plan="Quadruped", tris=1.0,
)


def _hframe(pivot, hs, pitch):
    a = math.radians(-pitch)
    c, s_ = math.cos(a), math.sin(a)
    R = np.array([[1, 0, 0], [0, c, -s_], [0, s_, c]])

    def hp(x, y, z):
        return T(A(*pivot) + R @ A(x, y, z) * hs)

    def hx(sd):
        return sd.scale(hs).rot(-pitch, 0, 0).at(*pivot)

    return hp, hx, R


def _beast(hid, **kw):
    P = dict(BEAST)
    P.update(kw)
    # one modelling scale for every beast (the engine rescales each word to its size class): only proportions matter
    s, LG, BL, G, HS = 1.0, P["leg"], P["body"], P["girth"], P["head"]
    H = Hero(hid, plan=P["plan"], gait=P["gait"], tags=list(P["tags"]))
    H.preview = P["preview"]
    TR = P["tris"]

    def tr(n):
        return int(max(150, min(2600, n * TR)))

    def v(x, y, z):
        return A(x * s, y * s, z * s)

    lift = 3.0 * LG
    fy = lift * P["fleg"]               # withers height
    hy = lift * P["hind"]               # hip height
    zc, zr = -1.45 * BL, 1.4 * BL
    by = (fy + hy) / 2
    H.body(T(v(0, by, 0)))
    W = 0.62 * G * P["stance"]
    col = "primary"

    # ---------------------------------------------------------------- patterns
    def back_shade(Q):
        t = np.clip((Q[:, 1] / s - (by - 0.9)) / 1.6, 0, 1)
        return 1.0 - (1.0 - P["shade"]) * t

    pat = P["pattern"]

    def skin_pat(extra=None):
        return combine(back_shade, pat, extra)

    def fin(sd, amp=1.0):
        if P["wart"]:
            sd = sd.noise(P["wart"] * amp * s, 6.0 / s, 11)
        if P["fur"]:
            sd = sd.noise(P["fur"] * amp * s, 10.0 / s, 12)
        return sd

    # ---------------------------------------------------------------- torso
    chest_y, rump_y = fy + 0.02, hy + 0.12
    tor = ellipsoid(0.82 * G, 0.98 * G, 1.25 * BL, T(v(0, chest_y, zc + 0.6 * BL)))
    tor = tor.su(ellipsoid(0.7 * G, 0.78 * G, 1.2 * BL, T(v(0, (chest_y + rump_y) / 2 + 0.08, 0.35 * BL))), 0.45)
    tor = tor.su(ellipsoid(0.8 * G * (1.15 if P["hind"] > 1.0 else 1.0), 0.88 * G, 0.95 * BL, T(v(0, rump_y + 0.1, zr))), 0.45)
    tor = tor.su(ellipsoid(0.35 * G, 0.6, 0.55, T(v(0.58 * G, chest_y + 0.25, zc + 0.2))).mirror_x(), 0.25)
    tor = tor.su(ellipsoid(0.42 * G, 0.68, 0.72, T(v(0.56 * G, rump_y, zr + 0.1))).mirror_x(), 0.3)
    tor = tor.su(ellipsoid(0.6 * G, 0.7 * G, 0.6, T(v(0, chest_y - 0.45, zc - 0.25))), 0.4)
    nb = v(0, chest_y + 0.4, zc - 0.65)
    tor = tor.su(round_cone(T(v(0, chest_y + 0.3, zc - 0.2)), T(nb), 0.62 * G * P["neck_thick"] * s, 0.5 * G * P["neck_thick"] * s), 0.35)
    H.piece("Torso", "Body", fin(tor), col=col, mat=P["skin"], tris=tr(2400), res=128, pattern=skin_pat())

    # ---------------------------------------------------------------- legs
    legs = []

    def front_leg(tag, z, ph, scale=1.0, foot=None, two=False):
        sh = v(W, chest_y + 0.05, z)
        el = v(W, fy * 0.58, z + 0.3)
        wr = v(W * 0.97, 0.4 * scale, z + 0.12)
        b0, b1, b2 = f"Shoulder{tag}#", f"Elbow{tag}#", f"Wrist{tag}#"
        H.mbone(b0, "Body", T(sh))
        H.mbone(b1, b0, T(el))
        if not two:
            H.mbone(b2, b1, T(wr))
        k = P["legT"] * G
        up = round_cone(T(sh + v(0, 0.15, 0)), T(el), 0.42 * k * s, 0.26 * k * s)
        up = up.su(ellipsoid(0.3 * k, 0.65 * LG, 0.44 * k, T(sh + v(0.02, -0.45 * LG, -0.02))), 0.25)
        H.mpiece(f"Upper{tag}#", b0, fin(up, 0.7), col=col, mat=P["skin"], tris=tr(800), role="limb", pattern=skin_pat())
        fo = round_cone(T(el), T(wr + v(0, 0.06, 0)), 0.25 * k * s, 0.16 * k * s)
        fo = fo.su(ellipsoid(0.2 * k, 0.5 * LG, 0.25 * k, T(el + v(0.01, -0.4 * LG, -0.05))), 0.15)
        ft = _foot(foot or P["front_foot"], wr, s, k, True)
        if two:
            H.mpiece(f"Fore{tag}#", b1, fin(fo.su(ft[0], 0.08), 0.6), col=col, mat=P["skin"], tris=tr(900), role="limb", pattern=skin_pat())
            legs.append((b0, b1, None, ph, True))
        else:
            H.mpiece(f"Fore{tag}#", b1, fin(fo, 0.6), col=col, mat=P["skin"], tris=tr(650), role="limb", pattern=skin_pat())
            H.mpiece(f"Foot{tag}#", b2, ft[0], col=ft[1], mat=P["skin"] if ft[1] == col else "hard", tris=tr(600), role="foot",
                     pattern=skin_pat() if ft[1] == col else None)
            legs.append((b0, b1, b2, ph, True))
        return ft

    def hind_leg(z, ph):
        hp = v(W * 0.95, rump_y + 0.12, z)
        kn = v(W * 1.02, hy * 0.62, z - 0.45)
        hk = v(W, hy * 0.33, z + 0.4)
        H.mbone("HipB#", "Body", T(hp))
        H.mbone("KneeB#", "HipB#", T(kn))
        H.mbone("HockB#", "KneeB#", T(hk))
        k = P["legT"] * G * (1.15 if P["hind_foot"] == "hippo" else 1.0)
        th = round_cone(T(hp + v(0, 0.2, 0.05)), T(kn), 0.52 * k * s, 0.3 * k * s)
        th = th.su(ellipsoid(0.38 * k, 0.8 * LG * P["hind"], 0.68 * k, T(hp + v(0.02, -0.42 * LG * P["hind"], 0.0))), 0.3)
        H.mpiece("Thigh#", "HipB#", fin(th, 0.7), col=col, mat=P["skin"], tris=tr(900), role="limb", pattern=skin_pat())
        sn = round_cone(T(kn), T(hk), 0.28 * k * s, 0.17 * k * s)
        sn = sn.su(ellipsoid(0.23 * k, 0.4 * LG * P["hind"], 0.28 * k, T(kn + v(0, -0.3 * LG * P["hind"], 0.2))), 0.15)
        H.mpiece("Shin#", "KneeB#", fin(sn, 0.6), col=col, mat=P["skin"], tris=tr(650), role="limb", pattern=skin_pat())
        base = v(W, 0.4, z + 0.18)
        ft = round_cone(T(hk), T(base), 0.16 * k * s, 0.15 * k * s)
        f2 = _foot(P["hind_foot"], base, s, k, False)
        if f2[1] == col:
            H.mpiece("FootB#", "HockB#", ft.su(f2[0], 0.08), col=col, mat=P["skin"], tris=tr(650), role="foot", pattern=skin_pat())
        else:
            H.mpiece("FootB#", "HockB#", ft.su(f2[0], 0.05), col=f2[1], mat="hard", tris=tr(600), role="foot")
        legs.append(("HipBR", "KneeBR", "HockBR", 0.5, False))
        legs.append(("HipBL", "KneeBL", "HockBL", 0.0, False))

    front_leg("F", zc + 0.15, 0.75)
    legs[-1] = ("ShoulderFR", "ElbowFR", "WristFR", 0.75, True)
    legs.append(("ShoulderFL", "ElbowFL", "WristFL", 0.25, True))
    if P["six"]:
        front_leg("M", 0.25 * BL, 0.25, two=True)
        legs[-1] = ("ShoulderMR", "ElbowMR", None, 0.25, True)
        legs.append(("ShoulderML", "ElbowML", None, 0.75, True))
    hind_leg(zr + 0.05, 0.5)

    # ---------------------------------------------------------------- neck + head
    a = math.radians(P["neck_ang"])
    NL = 1.25 * P["neck_len"]
    hpiv = nb + v(0, math.sin(a) * NL, -math.cos(a) * NL)
    H.bone("Neck", "Body", T(nb))
    nt = P["neck_thick"] * G
    neck = round_cone(T(nb + v(0, -0.15, 0.25)), T(hpiv), 0.55 * nt * s, 0.36 * nt * s)
    neck = neck.su(ellipsoid(0.4 * nt, 0.5 * nt, 0.5, T((nb + hpiv) / 2 + v(0, -0.15, 0))), 0.25)
    H.piece("NeckP", "Neck", fin(neck, 0.8), col=col, mat=P["skin"], tris=tr(800), role="limb", pattern=skin_pat())
    hs = HS * s
    H.bone("Head", "Neck", T(hpiv))
    hp, hx, R = _hframe(hpiv, hs, P["pitch"])
    cw, chh, cl = P["cran"]
    sw, sh_, sl = P["snout"]
    sy, sz = P["snout_y"], P["snout_z"]
    hd = ellipsoid(cw, chh, cl, (0, 0.12, -0.15))
    hd = hd.su(ellipsoid(sw, sh_, sl, (0, sy, sz - sl * 0.75)), 0.18)
    hd = hd.su(ellipsoid(cw * 0.7, chh * 0.6, cl * 0.6, (cw * 0.38, -0.05, -0.32)).mirror_x(), 0.15)   # cheeks
    ex, ey, ez, er = P["eye"]
    if P["brow"]:
        hd = hd.su(capsule((ex * 0.35, ey + er * 1.3, ez - 0.02), (ex * 1.15, ey + er * 1.1 - 0.05 * P["sad"], ez + 0.05), 0.07 * P["brow"] + 0.02).mirror_x(), 0.06)
    hd = hd.ss(sphere(er * 1.2, (ex, ey, ez)).mirror_x(), 0.04)
    mouth_y = sy - sh_ * 0.35
    tipz = sz - sl * 1.75
    hd = hd.ss(box(sw + 0.1, 0.3, (abs(tipz) + 0.3) / 2, (0, mouth_y - 0.3, (tipz - 0.3 + 0.05) / 2 - 0.05)), 0.04)
    if P["nostrils"]:
        hd = hd.ss(sphere(0.045, (sw * 0.35, sy + sh_ * 0.45, tipz + 0.06)).mirror_x(), 0.03)
    if P["grin"]:
        hd = hd.ss(capsule((sw * 0.95, mouth_y + 0.02, sz - sl * 0.4), (cw * 0.85, mouth_y + 0.06 + 0.1 * P["grin"], -0.05), 0.03), 0.02)
    ears = P["ears"]
    es = P["ear_size"]
    if ears == "pointed":
        ear = ellipsoid(0.13 * es, 0.24 * es, 0.06).ss(ellipsoid(0.09 * es, 0.18 * es, 0.045, (0, -0.02, -0.04)), 0.02)
        hd = hd.su(ear.rot(-10, 0, -20).at(cw * 0.65, chh * 0.85 + 0.12, -0.05).mirror_x(), 0.05)
    elif ears == "bat":
        ear = ellipsoid(0.2 * es, 0.42 * es, 0.06).ss(ellipsoid(0.15 * es, 0.34 * es, 0.05, (0, -0.02, -0.04)), 0.02)
        hd = hd.su(ear.rot(-5, 10, -35).at(cw * 0.75, chh * 0.85 + 0.25 * es, 0.0).mirror_x(), 0.05)
    elif ears == "horse":
        ear = ellipsoid(0.09 * es, 0.22 * es, 0.07).ss(ellipsoid(0.06 * es, 0.17 * es, 0.05, (0, 0, -0.04)), 0.02)
        hd = hd.su(ear.rot(-12, 0, -12).at(cw * 0.55, chh + 0.12 * es, 0.05).mirror_x(), 0.04)
    elif ears == "droop":
        ear = ellipsoid(0.07, 0.32 * es, 0.16 * es).rot(0, 0, 30).at(cw * 0.95, chh * 0.2 - 0.2 * es, 0.0)
        hd = hd.su(ear.mirror_x(), 0.06)
    elif ears == "round":
        hd = hd.su(ellipsoid(0.1 * es, 0.12 * es, 0.05).rot(0, 0, -25).at(cw * 0.7, chh * 0.8, 0.05).mirror_x(), 0.04)
    if P["mane"]:
        mn = P["mane"]
        m = ellipsoid((cw + 0.35) * mn, (chh + 0.4) * mn, 0.55 * mn, (0, 0.0, 0.25))
        m = m.su(ellipsoid(0.6 * mn, 0.6 * mn, 0.8 * mn, (0, -0.35, 0.55)), 0.3)
        m = m.ss(ellipsoid(cw * 1.05, chh * 1.1, 0.8, (0, 0.05, -0.55)), 0.12)
        H.piece("Mane", "Head", hx(m).noise(0.05 * s, 9 / s, 8), col="secondary", mat="cloth", tris=tr(1800), role="mane", pri=1.1)
    H.piece("HeadP", "Head", fin(hx(hd), 0.4), col=col, mat=P["skin"], tris=tr(2200), res=136, role="head", pattern=pat)
    # jaw
    jw, jh, jl = P["jaw"]
    H.bone("Jaw", "Head", hp(0, mouth_y - 0.02, -0.1))
    jz0 = -0.15
    jaw = ellipsoid(jw, jh, jl, (0, mouth_y - jh * 0.8, jz0 - jl * 0.85))
    jaw = jaw.su(capsule((cw * 0.6, mouth_y - 0.05, -0.05), (jw * 0.8, mouth_y - jh, jz0 - jl * 0.9), 0.08).mirror_x(), 0.08)
    jaw = jaw & plane((0, 1, 0), mouth_y - 0.015)
    H.piece("JawP", "Jaw", fin(hx(jaw), 0.3), col=col, mat=P["skin"], tris=tr(700), role="jaw", pri=1.3, pattern=pat)
    H.prim("Mouth", "Head", "Ellipsoid", (jw * 1.6 * hs, 0.07 * hs, jl * 1.5 * hs), hp(0, mouth_y - 0.05, jz0 - jl * 0.85), rot=(math.radians(-P["pitch"]), 0, 0),
           col="mouth", mat="hard", role="mouth", pri=2.4)
    # teeth / fangs / tusks / beak / trunk / horns
    tooth = []
    if P["teeth"]:
        n = P["teeth"]
        for i in range(n):
            u = i / max(n - 1, 1)
            z = tipz + 0.12 + u * (abs(tipz) - 0.35)
            x = sw * (0.55 + 0.4 * u) if True else 0
            for sx in (1, -1):
                tooth.append(round_cone((sx * x, mouth_y + 0.02, z), (sx * x, mouth_y - 0.1 - 0.04 * (1 - u), z), 0.035, 0.008))
    if P["fangs"]:
        f = P["fangs"]
        for sx in (1, -1):
            tooth.append(round_cone((sx * sw * 0.55, mouth_y + 0.02, tipz + 0.18), (sx * sw * 0.55, mouth_y - 0.18 * f, tipz + 0.2), 0.045, 0.01))
    if P["sabers"]:
        f = P["sabers"]
        for sx in (1, -1):
            tooth.append(mg.curved_horn([A(sx * sw * 0.6, mouth_y + 0.02, tipz + 0.22), A(sx * sw * 0.62, mouth_y - 0.25 * f, tipz + 0.22), A(sx * sw * 0.6, mouth_y - 0.5 * f, tipz + 0.32)], 0.06, 0.01))
    if P["tusks"]:
        f = P["tusks"]
        for sx in (1, -1):
            tooth.append(mg.curved_horn([A(sx * sw * 0.75, mouth_y + 0.05, tipz + 0.3), A(sx * sw * 0.85, mouth_y - 0.25 * f, tipz + 0.28), A(sx * sw * 0.8, mouth_y - 0.45 * f, tipz + 0.15)], 0.08, 0.025))
    if tooth:
        H.piece("Teeth", "Head", hx(hard(tooth)), col="tooth", mat="hard", tris=tr(500), role="tooth", pri=1.8, ao=False, smooth=2)
    if P["beak"]:
        bk = ellipsoid(sw * 0.95, sh_ * 0.85, 0.22, (0, sy - 0.02, tipz + 0.14)) & plane((0, 0, 1), tipz + 0.3)
        bk = bk | (ellipsoid(jw * 0.95, jh * 1.05, 0.2, (0, mouth_y - jh * 0.8, jz0 - jl * 1.7 + 0.1)) & plane((0, 0, 1), jz0 - jl * 1.7 + 0.25))
        H.piece("Beak", "Head", hx(bk), col="horn", mat="hard", tris=tr(450), role="beak", pri=1.5)
    if P["trunk"]:
        t_ = P["trunk"]
        pts = [A(0, sy + 0.05, tipz + 0.2), A(0, sy - 0.05, tipz - 0.15 * t_), A(0, sy - 0.35 * t_, tipz - 0.3 * t_), A(0, sy - 0.65 * t_, tipz - 0.25 * t_)]
        tk = tube([T(p) for p in pts], [sh_ * 0.6, 0.13, 0.1, 0.08], k=0.03)
        tk = tk.ss(sphere(0.04, T(pts[-1] + A(0.03, -0.06, 0))).mirror_x(), 0.02)
        H.bone("Trunk", "Head", hp(*pts[0]))
        H.piece("TrunkP", "Trunk", hx(tk), col=col, mat=P["skin"], tris=tr(600), role="trunk", pri=1.3, pattern=pat)
    hn = P["horns"]
    if hn:
        k = P["horn_size"]
        if hn == "goat_back":
            pts = [A(cw * 0.45, chh * 0.85, -0.2), A(cw * 0.6, chh + 0.35 * k, 0.05), A(cw * 0.7, chh + 0.45 * k, 0.45 * k), A(cw * 0.75, chh + 0.25 * k, 0.75 * k)]
            r0 = 0.1
        elif hn == "frog":   # hodag: up and curling forward
            pts = [A(cw * 0.5, chh * 0.8, -0.15), A(cw * 0.7, chh + 0.35 * k, -0.1), A(cw * 0.75, chh + 0.65 * k, -0.25 * k), A(cw * 0.65, chh + 0.7 * k, -0.5 * k)]
            r0 = 0.12
        elif hn == "bull":
            pts = [A(cw * 0.6, chh * 0.6, -0.05), A(cw + 0.3 * k, chh * 0.8, -0.1), A(cw + 0.5 * k, chh + 0.3 * k, -0.3 * k), A(cw + 0.45 * k, chh + 0.55 * k, -0.45 * k)]
            r0 = 0.12
        else:   # short spikes
            pts = [A(cw * 0.4, chh * 0.85, -0.1), A(cw * 0.45, chh + 0.25 * k, 0.0), A(cw * 0.5, chh + 0.4 * k, 0.12 * k)]
            r0 = 0.08
        horn = mg.curved_horn(pts, r0, 0.015)
        H.mpiece("Horn#", "Head", hx(horn), col="horn", mat="hard", tris=tr(450), role="horn", pri=1.5)
    H.eyes("Head", hp(ex, ey, ez), er * hs, col=P["eye_col"], pupil=P["pupil"], look=P["eye_look"])
    if P["sad"]:
        for sx, nm in ((1, "TearR"), (-1, "TearL")):
            H.prim(nm, "Head", "Ball", (0.07 * hs, 0.1 * hs, 0.07 * hs), hp(sx * (ex + 0.02), ey - er * 1.6, ez - 0.02), col=[0.55, 0.8, 1.0], mat="glass", tr=0.25, role="detail", pri=2.2)

    # ---------------------------------------------------------------- spines along the back
    if P["spines"]:
        n = P["spines"]
        sp = []
        for i in range(n):
            u = i / max(n - 1, 1)
            z = (zc - 0.5) + u * (zr + 0.4 - (zc - 0.5))
            ytop = mg.surface_y(tor, 0.0, z * s, by * s + 3 * s, by * s - 1 * s)
            hgt = P["spine_h"] * s * (0.6 + 0.4 * math.sin(math.pi * (0.15 + 0.85 * u)))
            sp.append(round_cone((0, ytop - 0.08 * s, z * s), (0, ytop + hgt, z * s + 0.18 * hgt), 0.09 * s, 0.012 * s))
        H.piece("Spines", "Body", hard(sp), col=P["spine_col"], mat="hard", tris=tr(800), role="spines", pri=1.4)

    # ---------------------------------------------------------------- tail
    TL, TT = P["tail_len"], P["tail_thick"]
    tails = []
    kind = P["tail"]
    if kind and TL > 0:
        t0 = v(0, rump_y + 0.35, zr + 0.85 * BL)
        if kind in ("taper", "spiked", "hand"):
            dirs = [(0, -0.35 + P["tail_up"], 1.0), (0, -0.4 + P["tail_up"], 1.0), (0, -0.25 + P["tail_up"], 1.0)]
            seg = [0.95, 0.85, 0.75]
            rad = [0.36, 0.25, 0.15, 0.06]
        elif kind == "whip":
            dirs = [(0, -0.7, 1.0), (0, -0.2, 1.0), (0, 0.45, 1.0)]
            seg = [0.85, 0.85, 0.75]
            rad = [0.12, 0.09, 0.07, 0.05]
        else:  # stub
            dirs = [(0, -0.6, 1.0), (0, -0.9, 0.6)]
            seg = [0.35, 0.25]
            rad = [0.22, 0.15, 0.06]
        pts = [t0]
        for d, L in zip(dirs, seg):
            pts.append(pts[-1] + nrm(A(*d)) * L * TL * s)
        for i in range(len(dirs)):
            nm = f"Tail{i + 1}"
            H.bone(nm, "Body" if i == 0 else f"Tail{i}", T(pts[i]))
            tails.append(nm)
            a_ = pts[i] - (pts[i + 1] - pts[i]) * (0.15 if i else 0.35)
            sg = round_cone(T(a_), T(pts[i + 1]), rad[i] * TT * s, rad[i + 1] * TT * s)
            last = i == len(dirs) - 1
            if last and kind == "whip":   # forked arrow tip
                d = nrm(pts[-1] - pts[-2])
                for sx in (1, -1):
                    sg = sg | mg.blade_fin(pts[-1] - d * 0.05 * s, nrm(d + A(0.6 * sx, 0, 0)), 0.32 * s, 0.07 * s, (0, 1, 0), flat=0.3)
            if last and kind == "hand":   # ahuizotl: a little grasping hand at the tip
                d = nrm(pts[-1] - pts[-2])
                c = pts[-1] + d * 0.08 * s
                sg = sg.su(ellipsoid(0.12 * s, 0.07 * s, 0.13 * s, T(c)), 0.05)
                for j, ang in enumerate((-50, -18, 15, 45)):
                    q = math.radians(ang)
                    dd = nrm(d + A(math.sin(q) * 0.9, -0.3, 0))
                    sg = sg.su(tube([T(c), T(c + dd * 0.18 * s), T(c + dd * 0.3 * s + A(0, -0.08, 0) * s)], [0.04 * s, 0.035 * s, 0.025 * s], k=0.01), 0.02)
            if kind == "spiked":
                d = nrm(pts[i + 1] - pts[i])
                for j in range(3):
                    c = pts[i] + (pts[i + 1] - pts[i]) * (0.2 + 0.3 * j)
                    r = rad[i] * TT * s * (1 - 0.3 * j / 3)
                    sg = sg | round_cone(T(c + A(0, r * 0.7, 0)), T(c + A(0, r + 0.25 * s * (1 - 0.15 * i), 0.1 * s)), 0.06 * s, 0.01 * s)
            H.piece(f"TailP{i + 1}", nm, fin(sg, 0.5), col=col, mat=P["skin"], tris=tr(500), role="tail", pri=1.5 + 0.1 * i, pattern=skin_pat())
    # ---------------------------------------------------------------- extras
    extra = {"zc": zc, "zr": zr, "chest_y": chest_y, "rump_y": rump_y, "W": W, "v": v, "s": s, "hp": hp, "hx": hx, "hs": hs, "tails": tails,
             "legs": legs, "tor": tor, "by": by, "fy": fy}
    H.socket("mouth", hp(0, mouth_y, tipz), "Jaw")
    H.socket("head", hp(0, chh + 0.3, -0.1), "Head")
    H.socket("seat", T(v(0, fy + 0.95, 0)), "Body")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": tails,
                  "legs": [{"hip": L[0], "knee": L[1], "phase": L[3], "side": 1 if L[0].endswith("R") else -1} for L in legs]})
    return H, extra


def _foot(kind, c, s, k, front):
    """(sdf, colour key) of a foot centred over c (ground at y = 0)."""
    c = A(*c)
    gnd = plane((0, -1, 0), 0.0)

    def v(x, y, z):
        return A(x * s, y * s, z * s)

    if kind == "hoof":
        p = round_cone(T(c + v(0, 0.05, 0)), T(c + v(0, -0.2, -0.05)), 0.14 * k * s, 0.16 * k * s)
        hf = cone(0.21 * k * s, 0.16 * k * s, 0.12 * s, axis=1, rr=0.02 * s).at(*T(c + v(0, -0.28, -0.08)))
        hf = hf.ss(box(0.015 * s, 0.2 * s, 0.14 * s, T(c + v(0, -0.3, -0.24))), 0.01)
        return (p.su(hf, 0.05) & gnd), "hoof"
    if kind == "knuckle":   # chalicothere: walks on the knuckles, long claws curled back
        p = round_cone(T(c + v(0, 0.1, 0)), T(c + v(0, -0.25, -0.05)), 0.18 * k * s, 0.2 * k * s)
        p = p.su(ellipsoid(0.26 * k, 0.16, 0.22, T(c + v(0, -0.28, -0.1))), 0.08)
        for dx in (-0.12, 0.0, 0.12):
            p = p | mg.curved_horn([c + v(dx * k, -0.25, -0.25), c + v(dx * k, -0.1, -0.42), c + v(dx * k, 0.15, -0.38), c + v(dx * k, 0.28, -0.25)], 0.065 * s, 0.015 * s)
        return (p & gnd), "claw"
    if kind == "hippo":
        p = round_cone(T(c + v(0, 0.05, 0)), T(c + v(0, -0.25, -0.05)), 0.2 * k * s, 0.24 * k * s)
        for dx in (-0.13, -0.045, 0.045, 0.13):
            p = p.su(ellipsoid(0.07, 0.07, 0.08, T(c + v(dx * k, -0.33, -0.22))), 0.04)
        return (p & gnd), "primary"
    if kind == "hand":   # ahuizotl: monkey-like hands
        p = round_cone(T(c + v(0, 0.08, 0)), T(c + v(0, -0.25, -0.12)), 0.14 * s, 0.15 * s)
        p = p.su(ellipsoid(0.2, 0.09, 0.22, T(c + v(0, -0.32, -0.18))), 0.06)
        for dx in (-0.12, -0.04, 0.04, 0.12):
            p = p.su(tube([T(c + v(dx, -0.33, -0.3)), T(c + v(dx * 1.15, -0.34, -0.5)), T(c + v(dx * 1.2, -0.37, -0.6))], [0.045 * s, 0.04 * s, 0.03 * s], k=0.01), 0.03)
        p = p.su(tube([T(c + v(-0.15, -0.3, -0.15)), T(c + v(-0.27, -0.34, -0.3))], [0.045 * s, 0.035 * s], k=0.01), 0.03)
        return (p & gnd), "primary"
    if kind == "claw":   # splayed reptile toes with claws
        p = round_cone(T(c + v(0, 0.08, 0)), T(c + v(0, -0.25, -0.1)), 0.16 * k * s, 0.17 * k * s)
        p = p.su(ellipsoid(0.24 * k, 0.11, 0.24, T(c + v(0, -0.3, -0.15))), 0.06)
        for ang in (-40, -15, 10, 35):
            q = math.radians(ang)
            d = A(math.sin(q), 0, -math.cos(q))
            b = c + v(0, -0.33, -0.15)
            e = b + d * 0.42 * s * k
            p = p.su(tube([T(b), T(e)], [0.06 * s * k, 0.045 * s * k], k=0.01), 0.03)
            p = p | round_cone(T(e), T(e + d * 0.12 * s + v(0, -0.05, 0)), 0.035 * s, 0.008 * s)
        return (p & gnd), "primary"
    # paw (with optional claws merged)
    p = round_cone(T(c + v(0, 0.08, 0)), T(c + v(0, -0.22, -0.12)), 0.18 * k * s, 0.2 * k * s)
    p = p.su(ellipsoid(0.26 * k, 0.15, 0.3, T(c + v(0, -0.3, -0.2))), 0.1)
    for dx in (-0.15, -0.05, 0.05, 0.15):
        p = p.su(sphere(0.095 * s * k, T(c + v(dx * k, -0.33, -0.43 + 0.05 * abs(dx) * 4))), 0.05)
    return (p & gnd), "primary"


def _beast_motion(H, X, P, neck_extra=None):
    motion.quadruped(H, X["legs"], neck="Neck", head="Head", jaw="Jaw", tail=X["tails"], stride=P["stride"], walk=P["walk"],
                     height=X["fy"] * X["s"] + 1.0, attack=P["attack"], swipe="ShoulderFR" if P["attack"] in ("pounce", "swipe") else None)


def beast(hid, **kw):
    P = dict(BEAST)
    P.update(kw)
    H, X = _beast(hid, **kw)
    _beast_motion(H, X, P)
    return H, X, P


def _wart_spots(seed=3):
    return spots(0.32, 0.1, depth=0.25, seed=seed)


# ---------------------------------------------------------------------------------------------- cryptids
@hero("chupacabra", "landmyth")
def chupacabra():
    H, X, P = beast("chupacabra", s=0.85, leg=1.05, body=0.85, girth=0.72, hind=1.08, legT=0.75, neck_len=0.8, neck_ang=28, neck_thick=0.8,
                    head=1.05, pitch=12, cran=(0.4, 0.4, 0.42), snout=(0.2, 0.18, 0.5), jaw=(0.17, 0.09, 0.42), eye=(0.27, 0.15, -0.4, 0.13),
                    pupil=None, eye_col="black", ears="bat", ear_size=1.0, fangs=1.3, teeth=4, spines=11, spine_h=0.55, spine_col="secondary",
                    front_foot="paw", hind_foot="claw", tail="whip", tail_len=0.85, tail_thick=0.8, wart=0.008, shade=0.85, attack="pounce",
                    pattern=_wart_spots(4), tags=("cryptid", "spooky"), walk=0.95, stride=0.46,
                    preview={"primary": "#6B6660", "secondary": "#7CB82F", "black": "#0E0E12", "tooth": "#F1E9D2"})
    return H


@hero("jersey devil", "landmyth")
def jersey_devil():
    H, X, P = beast("jersey devil", s=0.95, leg=1.0, body=0.9, girth=0.78, hind=1.12, legT=0.8, neck_len=1.15, neck_ang=48, neck_thick=0.8,
                    head=1.0, pitch=30, cran=(0.3, 0.32, 0.36), snout=(0.2, 0.22, 0.48), snout_y=-0.06, jaw=(0.16, 0.1, 0.42),
                    eye=(0.24, 0.12, -0.28, 0.075), eye_col=[1.0, 0.45, 0.1], pupil="slit", ears="horse", horns="goat_back", horn_size=1.0,
                    fangs=0.8, front_foot="hoof", hind_foot="hoof", tail="whip", tail_len=1.25, tail_thick=0.9, shade=0.8,
                    attack="pounce", tags=("cryptid", "spooky", "flying"), walk=1.0,
                    preview={"primary": "#4F4A45", "secondary": "#7A3A1A", "hoof": "#1E1A18", "horn": "#2B2622"})
    v, s = X["v"], X["s"]
    C = HM.Ctx(v=lambda x, y, z: v(x, y, z), s=s, chest=v(0.0, X["chest_y"] + 0.15, X["zc"] + 0.2) - v(0, 0, 0.32 * 0.9), P=P)
    wings = HM._bat_wings(H, C, {"depth": 0.9}, span=2.1, col="secondary", bone="Body")
    import motion_monsters as mm

    def wingfx(name):
        def f(t):
            pose = {}
            L = H.clips[name]["len"]
            u = t / L
            if name == "Attack":
                mm.wing_pose(pose, wings, 0.0, 0.0, base=0.7 * math.sin(math.pi * min(u * 1.4, 1)), fold=0.0)
            elif name == "Move":
                mm.wing_pose(pose, wings, TAU_ * u, 0.25, base=0.1)
            elif name == "Idle":
                mm.wing_pose(pose, wings, TAU_ * u * 2, 0.08, base=0.0)
            else:
                mm.wing_pose(pose, wings, 0.0, 0.0, base=0.4 * math.sin(math.pi * min(u, 1)))
            return pose
        return f
    for nm in ("Idle", "Move", "Attack", "Hit"):
        ml.overlay(H, nm, wingfx(nm))
    return H


TAU_ = 2 * math.pi


@hero("displacer beast", "landmyth")
def displacer_beast():
    H, X, P = beast("displacer beast", s=1.0, leg=0.95, body=1.25, girth=0.9, legT=0.85, neck_len=0.85, neck_ang=30, head=0.95, pitch=6,
                    cran=(0.45, 0.42, 0.48), snout=(0.3, 0.24, 0.32), jaw=(0.22, 0.11, 0.33), eye=(0.25, 0.16, -0.5, 0.09),
                    eye_col=[0.3, 0.95, 0.85], pupil="slit", ears="pointed", ear_size=1.1, fangs=1.0, six=True, tail="taper", tail_len=1.35,
                    tail_thick=0.55, tail_up=0.2, shade=0.75, attack="pounce", tags=("dungeon", "cat", "magic"), walk=1.05, stride=0.44,
                    pattern=stripes(lambda Q: Q[:, 2] + 0.3 * np.abs(Q[:, 1] - 3.0), 1.4, width=0.2, depth=0.35, wobble=0.1, seed=8),
                    preview={"primary": "#2E2B5C", "secondary": "#22D3EE", "claw": "#1A1A22"})
    v, s, W = X["v"], X["s"], X["W"]
    tents = []
    for sx, side in ((1, "R"), (-1, "L")):
        root = v(sx * 0.42, X["chest_y"] + 0.55, X["zc"] + 0.5)
        mid = root + v(sx * 0.55, 1.15, 0.55)
        tip = mid + v(sx * 0.25, 0.75, -0.95)
        end = tip + v(0, -0.25, -0.65)
        H.bone("Tent1" + side, "Body", T(root))
        H.bone("Tent2" + side, "Tent1" + side, T(mid))
        a = tube([T(root - v(0, 0.15, 0)), T(root + (mid - root) * 0.5 + v(sx * 0.1, 0, 0.1)), T(mid)], [0.24 * s, 0.19 * s, 0.15 * s], k=0.03)
        b = tube([T(mid), T(tip), T(end)], [0.15 * s, 0.12 * s, 0.09 * s], k=0.03)
        pad = ellipsoid(0.3 * s, 0.17 * s, 0.45 * s, T(end + v(0, -0.02, -0.1)))
        for j in range(5):
            q = j / 4
            c = end + v(0, 0.05, 0.15 - 0.4 * q)
            pad = pad | round_cone(T(c), T(c + v(sx * 0.12, 0.2, -0.05)), 0.05 * s, 0.01 * s) | round_cone(T(c), T(c + v(-sx * 0.12, 0.2, -0.05)), 0.05 * s, 0.01 * s)
        key = f"h_displacer beast_tent{'' if sx > 0 else '_l'}"
        H.piece("TentA" + side, "Tent1" + side, a, col="primary", mat="skin", tris=500, role="tentacle", pri=1.4, key=key + "a")
        H.piece("TentB" + side, "Tent2" + side, b.su(pad, 0.06), col="primary", mat="skin", tris=900, role="tentacle", pri=1.45, key=key + "b",
                pattern=lambda Q, e=end: np.where(np.linalg.norm(Q - e, axis=1) < 0.4 * s, 0.6, 1.0))
        tents.append(("Tent1" + side, "Tent2" + side, sx))

    def tent(name):
        def f(t):
            L = H.clips[name]["len"]
            u = t / L
            pose = {}
            for b1, b2, sx in tents:
                if name == "Attack":
                    k = ml.bump(u, 0.25, 0.8)
                    w = ml.env(u, 0.0, 0.25, 0.3, 0.45)
                    ml._add(pose, b1, (0, 0, 0, -0.4 * w + 0.9 * k, 0, -sx * 0.2 * k))
                    ml._add(pose, b2, (0, 0, 0, -0.5 * w + 1.1 * k, 0, 0))
                else:
                    amp = 0.25 if name == "Idle" else (0.35 if name == "Move" else 0.4)
                    cyc = 2 if name == "Idle" else 1
                    ph = 0 if sx > 0 else 1.7
                    ml._add(pose, b1, (0, 0, 0, amp * math.sin(TAU_ * u * cyc + ph), 0, sx * 0.6 * amp * math.cos(TAU_ * u * cyc + ph)))
                    ml._add(pose, b2, (0, 0, 0, 1.2 * amp * math.sin(TAU_ * u * cyc + ph - 1.0), 0, sx * 0.5 * amp * math.sin(TAU_ * u * cyc + ph - 0.6)))
            return pose
        return f
    for nm in ("Idle", "Move", "Attack", "Hit"):
        ml.overlay(H, nm, tent(nm))
    return H


@hero("hodag", "landmyth")
def hodag():
    H, X, P = beast("hodag", s=1.0, leg=0.72, body=1.1, girth=1.1, legT=1.05, stance=1.15, neck_len=0.45, neck_ang=12, neck_thick=1.2, head=1.25,
                    pitch=0, cran=(0.55, 0.42, 0.5), snout=(0.5, 0.25, 0.42), snout_y=-0.05, jaw=(0.46, 0.13, 0.45), eye=(0.33, 0.3, -0.25, 0.1),
                    eye_col=[0.95, 0.75, 0.15], ears=None, horns="frog", horn_size=1.0, teeth=7, grin=1.0, fangs=0.7, brow=1.0,
                    front_foot="claw", hind_foot="claw", tail="spiked", tail_len=1.0, tail_thick=0.9, spines=12, spine_h=0.5,
                    spine_col="horn", wart=0.012, shade=0.75, attack="bite", tags=("cryptid",), walk=1.15, stride=0.38,
                    pattern=_wart_spots(6), preview={"primary": "#3E5A1E", "secondary": "#F5F5F4", "horn": "#E9E2CF"})
    return H


@hero("squonk", "landmyth")
def squonk():
    H, X, P = beast("squonk", s=0.75, leg=0.7, body=0.85, girth=1.05, legT=0.95, neck_len=0.45, neck_ang=10, head=1.2, pitch=18,
                    cran=(0.45, 0.42, 0.45), snout=(0.3, 0.26, 0.38), snout_y=-0.1, jaw=(0.24, 0.1, 0.3), eye=(0.27, 0.1, -0.45, 0.11),
                    eye_col="eyeWhite", pupil="round", eye_look=(0.2, -0.25, -1.0), ears="droop", ear_size=1.1, sad=1.0, brow=0.9, wart=0.03, fur=0.0,
                    front_foot="paw", hind_foot="paw", tail="stub", tail_len=1.2, shade=0.9, attack="bite", tags=("cryptid", "silly"),
                    walk=0.9, stride=0.36, pattern=combine(_wart_spots(9), spots(0.22, 0.07, depth=0.2, seed=12)),
                    preview={"primary": "#9A948C", "secondary": "#7DD3FC", "iris": "#4A3A30"})
    return H


@hero("ahuizotl", "landmyth")
def ahuizotl():
    H, X, P = beast("ahuizotl", s=0.75, leg=0.78, body=1.05, girth=0.75, legT=0.8, neck_len=0.7, neck_ang=22, head=0.95, pitch=8,
                    cran=(0.38, 0.36, 0.42), snout=(0.24, 0.2, 0.42), jaw=(0.19, 0.09, 0.38), eye=(0.25, 0.14, -0.42, 0.085),
                    eye_col=[0.9, 0.8, 0.3], pupil="round", ears="pointed", ear_size=0.8, fangs=0.7, teeth=3,
                    front_foot="hand", hind_foot="hand", tail="hand", tail_len=1.6, tail_thick=0.5, tail_up=0.35, fur=0.006, shade=0.8,
                    attack="bite", tags=("myth", "aquatic", "dog"), walk=0.9,
                    preview={"primary": "#24305E", "secondary": "#57534E"})
    return H


# ---------------------------------------------------------------------------------------------- prehistoric
@hero("chalicotherium", "landmyth")
def chalicotherium():
    H, X, P = beast("chalicotherium", s=1.0, leg=1.05, fleg=1.25, hind=0.82, body=0.95, girth=1.05, legT=1.05, neck_len=1.0, neck_ang=30,
                    head=1.05, pitch=20, cran=(0.3, 0.32, 0.38), snout=(0.2, 0.22, 0.5), snout_y=-0.05, jaw=(0.17, 0.11, 0.45),
                    eye=(0.24, 0.12, -0.32, 0.07), eye_col=[0.3, 0.2, 0.12], pupil="round", ears="horse", ear_size=0.9,
                    front_foot="knuckle", hind_foot="paw", tail="stub", tail_len=1.0, fur=0.012, shade=0.8, attack="swipe",
                    tags=("mammal", "extinct", "heavy"), walk=1.3, stride=0.36,
                    preview={"primary": "#7E6E52", "secondary": "#C8B08A", "claw": "#2A2420"})
    return H


@hero("gorgonopsid", "landmyth")
def gorgonopsid():
    H, X, P = beast("gorgonopsid", s=0.95, leg=0.78, body=1.15, girth=0.85, legT=0.9, stance=1.15, neck_len=0.55, neck_ang=12, head=1.25, pitch=4,
                    cran=(0.36, 0.36, 0.5), snout=(0.26, 0.26, 0.6), snout_y=-0.02, jaw=(0.22, 0.12, 0.58), eye=(0.27, 0.2, -0.3, 0.075),
                    eye_col=[0.85, 0.6, 0.15], ears=None, sabers=1.2, teeth=6, brow=0.8, front_foot="claw", hind_foot="claw",
                    tail="taper", tail_len=0.75, tail_thick=0.7, shade=0.75, attack="bite", tags=("extinct", "ancient", "reptile"),
                    pattern=stripes(lambda Q: Q[:, 2] + 0.2 * Q[:, 1], 1.6, width=0.25, depth=0.4, wobble=0.15, seed=4), walk=1.0,
                    preview={"primary": "#6A5A4A", "secondary": "#C8A07A", "tooth": "#F2EAD4"})
    return H


@hero("lystrosaurus", "landmyth")
def lystrosaurus():
    H, X, P = beast("lystrosaurus", s=0.8, leg=0.6, body=0.9, girth=1.25, legT=1.2, stance=1.15, neck_len=0.35, neck_ang=5, neck_thick=1.2,
                    head=1.1, pitch=35, cran=(0.42, 0.42, 0.4), snout=(0.26, 0.3, 0.32), snout_y=-0.12, jaw=(0.22, 0.1, 0.3),
                    eye=(0.3, 0.25, -0.18, 0.075), eye_col=[0.6, 0.45, 0.2], pupil="round", ears=None, tusks=1.0, beak=True, nostrils=True,
                    front_foot="claw", hind_foot="claw", tail="stub", tail_len=0.9, wart=0.008, shade=0.8, attack="gore",
                    tags=("extinct", "ancient"), walk=1.0, stride=0.32,
                    pattern=spots(0.35, 0.12, depth=0.25, seed=21), preview={"primary": "#8A7A5A", "secondary": "#C8B08A", "horn": "#3A3530"})
    return H


@hero("macrauchenia", "landmyth")
def macrauchenia():
    H, X, P = beast("macrauchenia", s=1.0, leg=1.35, body=1.05, girth=0.85, legT=0.75, neck_len=1.9, neck_ang=62, neck_thick=0.7, head=0.9,
                    pitch=10, cran=(0.3, 0.3, 0.36), snout=(0.2, 0.2, 0.4), snout_y=-0.02, jaw=(0.16, 0.09, 0.38), eye=(0.25, 0.12, -0.3, 0.07),
                    eye_col=[0.25, 0.18, 0.12], pupil="round", ears="horse", ear_size=0.8, trunk=1.0, nostrils=False,
                    front_foot="hoof", hind_foot="hoof", tail="taper", tail_len=0.55, tail_thick=0.35, fur=0.008, shade=0.82,
                    attack="gore", tags=("mammal", "extinct"), walk=1.25,
                    preview={"primary": "#9A7A5A", "secondary": "#D8C8A8", "hoof": "#3A2E28"})
    return H


@hero("ammit", "landmyth")
def ammit():
    H, X, P = beast("ammit", s=1.1, leg=0.85, body=1.15, girth=1.05, hind=0.95, legT=1.05, neck_len=0.6, neck_ang=18, neck_thick=1.15, head=1.25,
                    pitch=5, cran=(0.38, 0.3, 0.42), snout=(0.3, 0.17, 0.85), snout_y=-0.06, jaw=(0.28, 0.1, 0.8), eye=(0.24, 0.3, -0.25, 0.075),
                    eye_col=[0.9, 0.75, 0.15], brow=1.0, teeth=11, ears=None, mane=1.0, front_foot="paw", hind_foot="hippo", tail="taper",
                    tail_len=0.8, tail_thick=0.65, shade=0.8, attack="bite", tags=("myth", "ancient", "egypt"), walk=1.2,
                    pattern=combine(gradient(2, -1.0, 1.0, 1.0, 0.85), spots(0.2, 0.07, depth=0.25, seed=5)),
                    preview={"primary": "#4A6A2A", "secondary": "#C9962A", "tooth": "#F2EAD4"})
    return H


