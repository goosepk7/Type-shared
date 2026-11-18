"""Pachyderms: elephant (African), war elephant (Asian, with a howdah to ride in), baby elephant, woolly mammoth,
rhino, hippo, tapir. Built by hoofkit.ungulate with column legs on round padded feet with toenails, plus:
* elephants: a domed head, a five-bone trunk chain (sways in the walk, curls in the idle, raises for the trumpet /
  stomp attack), big flapping ears on their own bones, ivory tusks, rope tail; the mammoth adds a shaggy coat with a
  hanging skirt, a high domed skull, small ears and huge curved tusks;
* rhino: armoured skin folds, two nose horns, gore charge;
* hippo: a huge head with a deep jaw that gapes (bite attack), tusks and a pink mouth lining;
* tapir: a short prehensile snout and the pale saddle.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from kit import hero
from map import NOTFOOD
import hoofkit as K

TAGS = ("ungulate", "pachyderm")

K.HEADS["elephant"] = dict(
    cran=(0.42, 0.46, 0.42, 0.02, -0.28), face=(0.36, 0.42, 0.3, -0.3, -0.48), muz=(0.21, 0.26, 0.2, -0.72, -0.6),
    jowl=(0.2, 0.28, 0.28, 0.2, -0.34, -0.32), brow=(0.12, 0.24, 0.02, -0.55), eye=(0.33, -0.16, -0.52, 0.045),
    nost=(0.002, 0.0, -0.8, -0.7), ear=(0.42, -0.02, -0.2), chin=(0.13, 0.1, 0.17, -0.82, -0.42),
    bar=((0.17, -0.62, -0.22), (0.1, -0.8, -0.42), 0.09), pad=None, snout=None, mouth=(0, -0.85, -0.6),
    roman=0.0, dish=0.0, lip=0.0, length=1.0)
K.HEADS["rhino"] = dict(
    cran=(0.3, 0.28, 0.32, 0.0, -0.15), face=(0.27, 0.26, 0.45, -0.1, -0.6), muz=(0.23, 0.22, 0.22, -0.2, -1.0),
    jowl=(0.18, 0.26, 0.3, 0.13, -0.25, -0.32), brow=(0.07, 0.24, 0.02, -0.52), eye=(0.27, -0.05, -0.56, 0.042),
    nost=(0.04, 0.14, -0.17, -1.17), ear=(0.18, 0.22, -0.04), chin=(0.15, 0.08, 0.18, -0.38, -0.96),
    bar=((0.13, -0.33, -0.32), (0.12, -0.38, -0.88), 0.08), pad=None, snout=None, mouth=(0, -0.34, -1.15),
    roman=-0.05, dish=0.0, lip=0.05, length=1.2)
K.HEADS["hippo"] = dict(
    cran=(0.38, 0.32, 0.36, 0.05, -0.15), face=(0.32, 0.27, 0.4, -0.04, -0.55), muz=(0.44, 0.28, 0.33, -0.1, -0.98),
    jowl=(0.28, 0.3, 0.32, 0.2, -0.2, -0.36), brow=(0.11, 0.24, 0.2, -0.42), eye=(0.25, 0.23, -0.44, 0.05),
    nost=(0.05, 0.16, 0.13, -1.17), ear=(0.23, 0.32, -0.08), chin=(0.38, 0.17, 0.32, -0.44, -0.92),
    bar=((0.27, -0.36, -0.3), (0.32, -0.42, -0.88), 0.15), pad=None, snout=None, mouth=(0, -0.3, -1.25),
    roman=0.0, dish=0.0, lip=0.0, length=1.3)
K.HEADS["tapir"] = dict(
    cran=(0.26, 0.26, 0.3, 0.0, -0.12), face=(0.2, 0.2, 0.36, -0.05, -0.5), muz=(0.14, 0.15, 0.18, -0.12, -0.82),
    jowl=(0.12, 0.2, 0.24, 0.11, -0.2, -0.25), brow=(0.06, 0.2, 0.06, -0.35), eye=(0.21, 0.03, -0.38, 0.042),
    nost=(0.002, 0.0, -0.3, -1.1), ear=(0.16, 0.2, -0.05), chin=(0.09, 0.06, 0.13, -0.27, -0.78),
    bar=((0.09, -0.24, -0.25), (0.07, -0.27, -0.7), 0.055), pad=None, snout=None, mouth=(0, -0.27, -0.85),
    roman=0.0, dish=0.0, lip=0.0, length=1.0)
K.EARS["round"] = (0.24, 0.13, 30, 10, 0.7)


# ------------------------------------------------------------------------------------------------ elephant parts
def elephant_extra(ear=1.0, tusk="tusk", tusk_len=1.0, mammoth=False, howdah=False):
    def f(H, X):
        s, hs, hp, hx, L, T = X["s"], X["hs"], X["hp"], X["hx"], X["L"], X["T"]
        # trunk: five bones hanging from the base of the face, curling forward at the tip
        p0 = hp(0, -0.86, -0.62)
        tip_y = 0.32 * s
        drop = p0[1] - tip_y
        pts = [p0]
        for i in range(1, 6):
            u = i / 5
            pts.append(np.array([0.0, p0[1] - drop * (0.95 * u + 0.05 * u * u), p0[2] - 0.12 * s * u - 0.32 * s * u ** 3]))
        pts.append(pts[-1] + np.array([0, 0.05 * s, -0.16 * s]))
        parent = "Head"
        names = []
        r0 = 0.25 * hs
        for i in range(5):
            b = f"Trunk{i + 1}"
            H.bone(b, parent, tuple(pts[i]))
            parent = b
            names.append(b)
            ra = r0 * (1 - 0.13 * i)
            rb = r0 * (1 - 0.13 * (i + 1))
            a = pts[i] + (pts[i] - pts[i + 1]) * 0.15
            e = pts[i + 1] if i < 4 else pts[i + 2]
            seg = K.chain([a, (a + e) / 2, e], ra * 1.02, rb, k=0.03, ridges=0.05)
            if i == 4:
                seg = seg.su(sphere(rb * 1.05, tuple(e)), 0.04)
                seg = seg.ss(sphere(rb * 0.45, tuple(e + np.array([0, -0.02 * s, -rb * 0.9]))), 0.02)
            H.piece(f"Trunk{i + 1}P", b, seg, col="primary", tris=T(420 if i < 4 else 380), role="limb", pri=1.3)
        # ears: big thin flaps hinged at the side of the head
        ex, ey, ez = X["HP"]["ear"]
        eb = hp(ex, ey, ez)
        H.mbone("Ear#", "Head", tuple(eb))
        if mammoth:
            flap = ellipsoid(0.07 * hs, 0.3 * ear * hs, 0.24 * ear * hs, L(ex + 0.05, ey - 0.22 * ear, ez + 0.16 * ear)).noise(0.02 * hs, 10 / hs, 3)
        else:
            # modelled around the hinge (origin), swung back-outward, then placed at the ear root
            flap = ellipsoid(0.05 * hs, 0.55 * ear * hs, 0.42 * ear * hs, L(0.03, -0.3 * ear, 0.36 * ear))
            flap = flap.su(ellipsoid(0.045 * hs, 0.3 * ear * hs, 0.2 * ear * hs, L(0.03, -0.75 * ear, 0.28 * ear)), 0.1)  # lower lobe
            flap = flap.ss(ellipsoid(0.03 * hs, 0.45 * ear * hs, 0.34 * ear * hs, L(-0.02, -0.32 * ear, 0.36 * ear)), 0.02)  # cupped inside
            flap = flap.rot(0, 28, -6).at(*L(ex, ey, ez))
        H.mpiece("Ear#", "Ear#", hx(flap), col="primary", tris=T(700), role="ear", pri=1.3)
        X["R"]["ears"] = ["EarR", "EarL"]
        X["R"]["big_ears"] = True
        X["R"]["trunk"] = names
        H.rig["trunk"] = names
        # tusks
        if tusk:
            b0 = np.array([0.16, -0.78, -0.48])
            if tusk == "mammoth":
                pts = K.curve(lambda u: (b0 + np.array([0.06 + 0.42 * math.sin(u * 2.2) * tusk_len, -0.55 * u * tusk_len + 0.95 * u ** 2.2 * tusk_len,
                                                        -0.85 * u * tusk_len + 0.35 * u ** 2 * tusk_len])) * hs, 12)
                tk = K.chain(pts, 0.085 * hs, 0.025 * hs, k=0.02)
            else:
                pts = K.curve(lambda u: (b0 + np.array([0.04 * u, -0.42 * u * tusk_len + 0.32 * u * u * tusk_len, -0.55 * u * tusk_len])) * hs, 8)
                tk = K.chain(pts, 0.065 * hs, 0.02 * hs, k=0.02)
            H.mpiece("Tusk#", "Head", hx(tk), col="horn", mat="hard", tris=T(380), role="horn", pri=1.4)
        H.socket("mouth", tuple(pts_last(names, H)), names[-1])
        if mammoth:
            K.skirt(H, X, length=0.55, col="primary", amp=0.04)
        if howdah:
            build_howdah(H, X)

    return f


def pts_last(names, H):
    return H.bpos(names[-1]) + np.array([0, -0.25, -0.15])


def build_howdah(H, X):
    """Wooden howdah on a padded caparison: the rider's seat on a war elephant."""
    s, top, Dp, body, zs = X["s"], X["top"] * X["s"], X["Dp"] * X["s"], X["torso"], X["zs"]
    zc = -0.15 * s
    ytop = top - 0.25 * s + K.surf(body, (0, top - 0.25 * s, zc), (0, 1, 0), hi=3 * s)
    cap = body.shell(0.06 * s) & round_box(2.5 * s, 0.75 * Dp, 1.05 * s, 0.3 * s, (0, top, zc)) & half_space(1, -1, top - 0.78 * Dp)
    H.piece("Caparison", "Body", cap, col=K.BLANKET, mat="cloth", tris=X["T"](1100), res=112, role="detail", pri=1.4,
            pattern=K.band(1, top - 0.74 * Dp, top - 0.66 * Dp, 0.5, soft=0.02 * s))
    base_y = ytop + 0.08 * s
    w, l = 0.72 * s, 0.82 * s
    hd = round_box(w, 0.08 * s, l, 0.04 * s, (0, base_y, zc))                       # platform
    hd = hd | (round_box(w, 0.22 * s, l, 0.05 * s, (0, base_y + 0.3 * s, zc)) - round_box(w - 0.07 * s, 0.4 * s, l - 0.07 * s, 0.03 * s, (0, base_y + 0.42 * s, zc)))  # rail box
    for sx in (1, -1):
        for sz in (1, -1):
            hd = hd | cylinder(0.045 * s, 0.55 * s).at(sx * (w - 0.05 * s), base_y + 0.62 * s, zc + sz * (l - 0.05 * s))   # posts
    H.piece("Howdah", "Body", hd, col="darkWood", mat="wood", tris=X["T"](1300), res=112, role="detail", pri=1.4)
    roof = ellipsoid(w + 0.18 * s, 0.32 * s, l + 0.18 * s, (0, base_y + 1.15 * s, zc)) & half_space(1, -1, base_y + 1.12 * s)
    roof = roof.su(round_cone((0, base_y + 1.4 * s, zc), (0, base_y + 1.62 * s, zc), 0.07 * s, 0.02 * s), 0.05)
    H.piece("Canopy", "Body", roof, col="gold", mat="cloth", tris=X["T"](700), res=96, role="detail", pri=1.5)
    hp, hx, L, hs = X["hp"], X["hx"], X["L"], X["hs"]
    c = X["HP"]["cran"]
    plate = X["head_can"].shell(0.04 * hs) & half_space(2, -1, -0.62 * hs) & half_space(2, 1, -0.15 * hs) & half_space(1, -1, -0.35 * hs)
    plate = plate & half_space(0, 1, 0.24 * hs) & half_space(0, -1, -0.24 * hs)
    H.piece("HeadPlate", "Head", hx(plate), col="gold", mat="metal", tris=X["T"](700), res=104, role="detail", pri=1.5)
    H.socket("seat", (0, base_y + 0.15 * s, zc), "Body")
    H.mount = {"seat": "Torso", "saddle": {"pos": (0, base_y + 0.1 * s, zc), "size": (2 * w, 0.18 * s, 2 * l)}}


def elephant_kw(**kw):
    d = dict(head="elephant", hs=1.85, head_ang=12, ears=None, hoof="pad", leg=1.12, lt=1.8, girth=1.22, depth=1.25, body=1.0,
             slope=0.2, withers=0.25, neck_len=0.22, neck_ang=30, neck_thick=1.9, neck_flat=1.0, arch=0.0, knee_h=0.5, stifle_h=0.62,
             stifle_fwd=0.4, hock_h=0.3, tail="tuft", tail_len=0.9, gait="walk", attack="stomp", heavy=1.0, stride=0.8, fold=0.7,
             tags=TAGS + ("elephant",), rig_gait="stomp", graze=0.25, shade=0.95, pupil=None, eye_col=[0.15, 0.1, 0.06], mane_col="dark",
             preview={"primary": "#8E8A86", "secondary": "#E8E2D8", "nail": "#D9CDB4", "horn": "#F2EAD8", "nose": "#3A2A28"})
    d.update(kw)
    return d


def asian_dome(head, L, hs, HP):
    return head.su(sphere(0.3 * hs, L(0.16, 0.28, -0.32)).mirror_x(), 0.15)


def mammoth_dome(head, L, hs, HP):
    return head.su(ellipsoid(0.3 * hs, 0.42 * hs, 0.3 * hs, L(0, 0.32, -0.2)), 0.2)


@hero("elephant", "pachyderms")
def elephant():
    return K.ungulate("elephant", **elephant_kw(s=1.3, extra=elephant_extra(ear=1.0, tusk="tusk")))


@hero("war elephant", "pachyderms")
def war_elephant():
    return K.ungulate("war elephant", **elephant_kw(s=1.25, slope=0.05, withers=0.45, head_mod=asian_dome, tags=TAGS + ("elephant", "mount"),
                                                    extra=elephant_extra(ear=0.7, tusk="tusk", tusk_len=0.8, howdah=True),
                                                    preview={"primary": "#7E7A78", "secondary": "#B03030", "nail": "#D9CDB4", "horn": "#F2EAD8",
                                                             "darkWood": "#5A3820", "gold": "#E8B53A"}))


@hero("baby elephant", "pachyderms")
def baby_elephant():
    return K.ungulate("baby elephant", **elephant_kw(s=0.75, hs=2.25, leg=1.0, girth=1.3, extra=elephant_extra(ear=1.05, tusk=None),
                                                     stride=0.9, preview={"primary": "#9A9692", "secondary": "#F0E8DE", "nail": "#D9CDB4"}))


@hero("woolly mammoth", "pachyderms")
def mammoth():
    return K.ungulate("woolly mammoth", **elephant_kw(s=1.4, slope=0.55, withers=0.75, shaggy=0.035, head_mod=mammoth_dome, tail_len=0.5,
                                                      extra=elephant_extra(ear=1.0, tusk="mammoth", tusk_len=1.15, mammoth=True), tags=TAGS + ("elephant", "ice age"),
                                                      preview={"primary": "#6A4A2E", "secondary": "#C8A87A", "nail": "#D9CDB4", "horn": "#F2EAD8"}))


# ------------------------------------------------------------------------------------------------ rhino / hippo / tapir
def rhino_horns(front=1.0, rear=0.5):
    def f(H, X):
        hs, hx, HP = X["hs"], X["hx"], X["HP"]
        m, fc = HP["muz"], HP["face"]
        b1 = np.array([0, m[3] + m[1] * 0.75, m[4] + 0.04]) * hs
        pts = K.curve(lambda u: b1 + np.array([0, 0.75 * front * u, -0.2 * front * u + 0.32 * front * u ** 2]) * hs, 8)
        hn = K.chain(pts, 0.17 * hs, 0.02 * hs, k=0.03)
        if rear:
            b2 = np.array([0, fc[3] + fc[1] * 0.85, fc[4] - 0.12]) * hs
            pts2 = K.curve(lambda u: b2 + np.array([0, 0.42 * rear * u, 0.08 * rear * u]) * hs, 5)
            hn = hn | K.chain(pts2, 0.13 * hs, 0.02 * hs, k=0.02)
        H.piece("Horns", "Head", hx(hn), col="dark", mat="hard", tris=X["T"](700), role="horn", pri=1.3)
    return f


@hero("rhinoceros", "pachyderms")
def rhino():
    return K.ungulate("rhinoceros", **elephant_kw(s=1.0, head="rhino", hs=1.15, head_ang=58, ears="deer", ear_scale=0.7, leg=0.72, lt=1.55,
                                                  girth=1.32, depth=1.15, body=1.0, slope=0.05, withers=0.35, neck_len=0.42, neck_ang=12,
                                                  neck_thick=1.6, knee_h=0.52, stifle_h=0.9, stifle_fwd=0.8, hock_h=0.42, folds=(-0.85, 0.55),
                                                  gait="trot", attack="gore", heavy=0.6, stride=0.9, fold=0.8, extra=rhino_horns(),
                                                  tags=TAGS + ("rhino",), rig_gait="heavy",
                                                  preview={"primary": "#8C8A84", "secondary": "#5E5A54", "nail": "#6A6560", "dark": "#4A4744"}))


def hippo_extra(H, X):
    hs, hx, L, T = X["hs"], X["hx"], X["L"], X["T"]
    lining = ellipsoid(0.36 * hs, 0.05 * hs, 0.4 * hs, L(0, -0.3, -0.85))
    H.piece("MouthIn", "Head", hx(lining), col=[0.85, 0.5, 0.52], mat="skin", tris=T(300), role="mouth", pri=1.6, ao=False)
    tusks = None
    for sx in (1, -1):
        t = round_cone(L(0.3 * sx, -0.42, -1.05), L(0.33 * sx, -0.18, -1.12), 0.05 * hs, 0.02 * hs)
        tusks = t if tusks is None else tusks | t
    H.piece("Tusks", "Jaw", hx(tusks), col="tooth", mat="hard", tris=T(300), role="tooth", pri=1.8, ao=False)


@hero("hippopotamus", "pachyderms")
def hippo():
    return K.ungulate("hippopotamus", **elephant_kw(s=1.0, head="hippo", hs=1.25, head_ang=18, ears="round", ear_scale=0.55, leg=0.5, lt=1.75,
                                                    girth=1.45, depth=1.32, body=1.0, belly=0.4, slope=0.0, withers=0.1, neck_len=0.3, neck_ang=10,
                                                    neck_thick=2.1, knee_h=0.55, stifle_h=0.95, stifle_fwd=0.6, hock_h=0.45, tail="stub",
                                                    gait="walk", attack="bite", heavy=0.8, stride=0.75, fold=0.7, extra=hippo_extra,
                                                    tags=TAGS + ("hippo",), rig_gait="heavy", shade=0.88,
                                                    preview={"primary": "#7E6A72", "secondary": "#D8A0A0", "nail": "#6A5A60", "tooth": "#FFF8E8"}))


def tapir_snout(head, L, hs, HP):
    return head.su(K.chain([np.array(L(0, -0.08, -0.78)), np.array(L(0, -0.14, -1.0)), np.array(L(0, -0.28, -1.12))], 0.12 * hs, 0.065 * hs, k=0.04, ridges=0.05), 0.08)


@hero("tapir", "pachyderms")
def tapir():
    return K.ungulate("tapir", **elephant_kw(s=0.78, head="tapir", hs=1.1, head_ang=35, ears="round", ear_scale=1.0, leg=0.8, lt=1.05,
                                             hoof="cloven", hoof_r=1.1, girth=1.05, depth=1.12, body=0.95, slope=-0.05, withers=0.0, neck_len=0.48,
                                             neck_ang=25, neck_thick=1.15, knee_h=0.545, stifle_h=1.0, stifle_fwd=1.0, hock_h=0.6, tail="stub",
                                             gait="trot", attack="gore", heavy=0.2, stride=0.9, fold=0.9, head_mod=tapir_snout, rump_col="secondary",
                                             extra=None, tags=TAGS + ("tapir",), rig_gait="trot",
                                             preview={"primary": "#2A2624", "secondary": "#E6E2DC", "hoof": "#1E1A18"}))


A = NOTFOOD
MAP = [
    ("elephant", "elephant, elephants, african elephant, bull elephant, elephant spirit, airavata, ganesha elephant, "
                 "iron elephant, robot elephant, !elephant seal, !elephant shrew, !elephant bird, !baby elephant shrew", A),
    ("war elephant", "war elephant, asian elephant, indian elephant, battle elephant, elephant mount, royal elephant, howdah", A),
    ("baby elephant", "baby elephant, elephant calf, dumbo", A),
    ("woolly mammoth", "woolly mammoth, wooly mammoth, mammoth, mammoths, mastodon, gomphotherium, deinotherium, ice age mammoth", A),
    ("rhinoceros", "rhinoceros, rhino, rhinos, white rhino, black rhino, indian rhino, baby rhino, woolly rhinoceros, woolly rhino, "
                   "javan rhino, sumatran rhino, elasmotherium, paraceratherium, arsinoitherium", A),
    ("hippopotamus", "hippopotamus, hippo, hippos, pygmy hippo, hungry hippo, river horse, !hippogriff", A),
    ("tapir", "tapir, tapirs, malayan tapir, baby tapir, baku", A),
]
