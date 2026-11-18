"""Living objects and toys: teapot spirit, tsukumogami (one-eyed one-legged umbrella), sock puppet, living sword,
animated broom, wind-up toy, teddy bear (+ teddy bear monster), balloon animal, pet rock, slinky, humpty dumpty,
dinosaur egg, floating eye, brain alien.

Each is a sculpted object first (porcelain, oiled paper, knitted wool, forged steel, straw and staves, lithographed
tin, plush, latex, granite, coiled wire, eggshell) that has come alive, with its own charming motion: the teapot hops
with a rattling lid and steam puffs, the umbrella pogos on its one leg with a flapping tongue, the sock puppet
chatters, the sword hovers and slashes, the broom marches with sloshing buckets and sweeps, the wind-up toy waddles
while its key turns, the floating eye blinks and its stalks wriggle.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF
from kit import hero, stripes, spots, gradient, combine
from objkit import (T, A, U, TAU, add, ease, bump, env, scaled, hitk, clips, spin, OH, cartoon_eye, button_eye, led_eye, googly,
                    helix_rings, teeth_row)

OBJ = {"cat": ["Creature", "Object", "Machine", "Person"],
       "bp": ["Blob", "Orb", "Ball", "Biped", "Quadruped", "Humanoid", "Weapon", "Robot", "Structure", "Insect", "Bird", "Ghost"]}


def _ang(p):
    return np.arctan2(p[:, 0], -p[:, 2])


# ================================================================================================ teapot spirit
@hero("teapot spirit", "objects")
def teapot_spirit():
    """Chatty porcelain teapot: round glazed belly with a gold band, the spout as a curled-up nose between two big
    cartoon eyes, a grin under it, a looped handle at the back, a domed lid with a knob that rattles, rosy cheeks
    and two stubby feet. Hops with the lid clattering and puffs steam; the attack tips it forward to pour."""
    H = OH("teapot spirit", plan="Blob", gait="hop", tags=["object", "teapot"])
    H.preview = {"primary": "#F4F1EA", "secondary": "#3B6FB6", "gold": "#E1B54A", "blush": "#FF8FA3"}
    H.body((0, 0.55, 0))
    H.bone("Pot", "Body", (0, 0.75, 0))
    H.bone("Lid", "Pot", (0, 1.8, 0.0))
    H.bone("Spout", "Pot", (0, 1.0, -0.85))
    H.bone("Steam", "Spout", (0, 1.6, -1.7))
    H.mbone("Foot#", "Body", (0.45, 0.3, -0.15))
    por = dict(col="primary", mat="plastic")
    pot = ellipsoid(1.05, 0.8, 1.05, (0, 1.05, 0)).su(ellipsoid(0.82, 0.35, 0.82, (0, 0.45, 0)), 0.25)
    pot = pot.su(cylinder(0.6, 0.1, rr=0.04).at(0, 0.32, 0), 0.08)
    pot = pot.su(cylinder(0.66, 0.08, rr=0.04).at(0, 1.74, 0), 0.06)  # shoulder collar under the lid
    pot = pot & plane((0, -1, 0), -0.24)
    # mouth: a wide grin pocket under the spout
    grin = ellipsoid(0.36, 0.14, 0.2, (0, 0.66, -0.98)).su(ellipsoid(0.12, 0.12, 0.2, (0.3, 0.74, -0.92)).mirror_x(), 0.06)
    pot = pot.ss(grin, 0.04)
    pot = pot.ss(ellipsoid(0.17, 0.2, 0.12, (0.47, 1.5, -0.8)).mirror_x(), 0.03)  # eye sockets
    band = stripes(lambda P: P[:, 1], 1.0, width=0.07, depth=0.0)
    flowers = spots(0.32, 0.09, depth=0.45, region=lambda P: np.clip(1 - np.abs(P[:, 1] - 1.0) / 0.18, 0, 1) * (P[:, 2] > -0.55), seed=3)
    H.piece("Belly", "Pot", pot, tris=2200, res=136, pattern=combine(band, flowers), **por)
    trim = U(torus(0.86, 0.035).at(0, 0.62, 0), torus(0.68, 0.035).at(0, 1.82, 0))
    H.piece("Trim", "Pot", trim, col="gold", mat="metal", tris=600, role="detail", pri=1.4)
    sp = tube([(0, 0.98, -0.8), (0, 1.0, -1.2), (0, 1.22, -1.52), (0, 1.55, -1.68)], [0.19, 0.12, 0.09, 0.085], k=0.08)
    sp = sp.su(torus(0.09, 0.025).at(0, 1.57, -1.69), 0.02)
    sp = sp.ss(capsule((0, 1.5, -1.68), (0, 1.75, -1.7), 0.055), 0.02)
    H.piece("SpoutP", "Spout", sp, tris=900, role="nose", **por)
    hd = tube([(0, 1.55, 0.8), (0, 1.75, 1.3), (0, 1.35, 1.62), (0, 0.85, 1.35), (0, 0.7, 0.9)], [0.1, 0.1, 0.1, 0.1, 0.11], k=0.06)
    H.piece("Handle", "Pot", hd, tris=700, role="tail", **por)
    lid = (ellipsoid(0.66, 0.3, 0.66, (0, 1.82, 0)) & plane((0, -1, 0), -1.8)).su(ellipsoid(0.12, 0.08, 0.12, (0, 2.12, 0)), 0.06)
    lid = lid.su(sphere(0.15, (0, 2.27, 0)), 0.05)
    lid = lid | torus(0.67, 0.03).at(0, 1.83, 0)
    H.piece("LidP", "Lid", lid, tris=800, role="head", **por)
    H.prim("LidGold", "Lid", "Ball", (0.18, 0.18, 0.18), (0, 2.31, 0), col="gold", mat="metal", role="detail", pri=1.6)
    for sx, nm in ((1, "R"), (-1, "L")):
        ft = ellipsoid(0.24, 0.17, 0.32, (0.45 * sx, 0.17, -0.2)) & plane((0, -1, 0), 0.0)
        H.piece("FootP" + nm, "Foot" + nm, ft, tris=300, role="foot", key=f"h_teapot spirit_foot{'' if sx > 0 else '_l'}", **por)
    cartoon_eye(H, "Eye#", "Pot", (0.47, 1.5, -0.7), 0.18, look=(0.35, 0.15, -1))
    H.mprim("Cheek#", "Pot", "Ellipsoid", (0.22, 0.13, 0.06), (0.62, 0.95, -0.8), rot=(0, -0.6, 0), col="blush", mat="hard", role="cheek", pri=2.2, tr=0.15)
    H.prim("MouthIn", "Pot", "Ellipsoid", (0.62, 0.2, 0.2), (0, 0.67, -0.9), col="mouth", mat="hard", role="mouth", pri=1.5)
    H.prim("Tongue", "Pot", "Ellipsoid", (0.3, 0.08, 0.18), (0, 0.6, -0.95), col="tongue", mat="hard", role="mouth", pri=1.9)
    H.prim("SteamA", "Steam", "Ball", (0.22, 0.22, 0.22), (0, 1.82, -1.72), col="white", mat="hard", role="steam", tr=0.35, pri=2.2)
    H.prim("SteamB", "Steam", "Ball", (0.15, 0.15, 0.15), (0.07, 2.04, -1.68), col="white", mat="hard", role="steam", tr=0.45, pri=2.4)
    H.socket("mouth", (0, 1.62, -1.72), "Spout")
    H.socket("head", (0, 2.5, 0), "Lid")
    H.rig.update({"head": "Pot", "jaw": "Lid"})

    def rattle(u, amt):
        return amt * abs(math.sin(TAU * u * 7)) * max(0.0, math.sin(TAU * u * 2)) ** 2

    def idle(t):
        u = t / 2.4
        p = {}
        add(p, "Pot", (0, 0.03 * math.sin(TAU * u), 0, 0.03 * math.sin(TAU * u + 1), 0.08 * math.sin(TAU * u * 0.5), 0.04 * math.sin(TAU * u)))
        r = rattle(u, 1.0)
        add(p, "Lid", (0, 0.05 * r, 0, 0.06 * r * math.sin(TAU * u * 9), 0, 0.08 * r * math.cos(TAU * u * 7)))
        add(p, "Spout", (0, 0, 0, 0.08 * math.sin(TAU * u + 0.5), 0, 0.05 * math.sin(TAU * u * 0.5)))
        add(p, "Steam", (0, 0.25 * (u % 1.0), 0, 0, 0, 0.15 * math.sin(TAU * u)))
        return p

    def move(t):
        u = t / 0.7
        ph = TAU * u
        air = max(0.0, math.sin(ph))
        land = max(0.0, -math.sin(ph))
        p = {}
        add(p, "Body", (0, 0.55 * air - 0.08 * land, 0, -0.12 * math.cos(ph), 0, 0.05 * math.sin(ph * 0.5)))
        add(p, "Pot", (0, -0.06 * land, 0, 0.1 * land, 0, 0.06 * math.sin(ph)))
        add(p, "Lid", (0, 0.18 * max(0.0, math.sin(ph - 1.6)) ** 2, 0, 0.18 * math.sin(ph * 2), 0, 0.15 * math.sin(ph * 3)))
        add(p, "Spout", (0, 0, 0, -0.18 * math.cos(ph - 0.6), 0, 0))
        add(p, "Steam", (0, 0.15 * air, 0.2 * air, 0, 0, 0))
        for f, sg in (("FootR", 1), ("FootL", -1)):
            add(p, f, (0, 0.06 * air, 0, -0.5 * air * sg * 0 + 0.4 * air, 0, sg * 0.25 * air))
        return p

    def attack(t):
        s = t / 0.9
        w, st, rec = env(s)
        p = {}
        add(p, "Body", (0, 0.35 * w + 0.1 * st, 0.2 * w - 0.45 * st, 0.3 * w - 0.75 * st, 0, 0))
        add(p, "Lid", (0, 0.35 * st, 0.1 * st, -0.6 * st, 0, 0.3 * st * math.sin(TAU * s * 6)))
        add(p, "Spout", (0, 0, 0, 0.25 * w - 0.35 * st, 0, 0))
        add(p, "Steam", (0, 0.2 * st, -0.3 * st, 0, 0, 0))
        for f in ("FootR", "FootL"):
            add(p, f, (0, 0, 0, -0.5 * w + 0.6 * st, 0, 0))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, 0.1 * k, 0.25 * k, 0.3 * k, 0, 0.15 * math.sin(t * 40) * k))
        add(p, "Lid", (0, 0.3 * k, 0.1 * k, 0.5 * k, 0, 0.3 * k))
        return p

    clips(H, idle, move, attack, hit, 2.4, move_len=0.7)
    return H


# ================================================================================================ tsukumogami
def _canopy_r(y, y0=1.45, y1=3.75, r0=1.05):
    t = np.clip((y - y0) / (y1 - y0), 0, 1)
    return r0 * (1 - t) ** 0.85 + 0.04 * np.sin(np.pi * t)


@hero("tsukumogami", "objects")
def tsukumogami():
    """Kasa-obake: an old oiled-paper umbrella come alive. Closed pleated canopy with dark ribs and pointed rib tips
    at the hem, a finial on top, ONE huge eye with a heavy lid, a wide grin with a long lolling tongue, and a single
    hairy leg in a wooden geta sandal under the handle. Pogos on its one leg; licks as its attack."""
    H = OH("tsukumogami", plan="Blob", gait="hop", tags=["object", "yokai", "umbrella"])
    H.preview = {"primary": "#B8352B", "secondary": "#E9C46A"}
    H.body((0, 1.25, 0))
    H.bone("Canopy", "Body", (0, 1.55, 0))
    H.bone("Tip", "Canopy", (0, 3.2, 0))
    H.bone("EyeB", "Canopy", (0, 2.45, -0.62))
    H.bone("Tongue", "Canopy", (0, 1.88, -0.8))
    H.bone("Hip", "Body", (0, 1.15, 0))
    H.bone("Knee", "Hip", (0, 0.68, -0.05))
    H.bone("Foot", "Knee", (0, 0.2, 0.0))

    def can(p):
        y = p[:, 1]
        th = _ang(p)
        R = _canopy_r(y)
        pleat = 1 - 0.07 * (1 - np.abs(np.cos(th * 4)))  # panels sag in between the 8 ribs
        rho = np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2)
        hem = 1.45 - 0.16 * np.abs(np.cos(th * 4)) ** 6
        d = (rho - R * pleat) * 0.85
        d = np.maximum(d, hem - y)
        d = np.maximum(d, y - 3.75)
        return d

    cv = SDF(can)
    cv = cv.su(ellipsoid(0.3, 0.12, 0.2, (0, 2.78, -0.42)), 0.12)  # brow ridge
    cv = cv.ss(ellipsoid(0.34, 0.36, 0.3, (0, 2.45, -0.72)), 0.06)  # eye socket
    grin = ellipsoid(0.42, 0.13, 0.25, (0, 1.9, -0.92)).su(ellipsoid(0.1, 0.1, 0.25, (0.38, 1.98, -0.85)).mirror_x(), 0.05)
    cv = cv.ss(grin, 0.04)
    ribs = stripes(lambda P: _ang(P) / (TAU / 8), 1.0, width=0.08, depth=0.55)
    age = spots(0.4, 0.12, depth=0.18, seed=7)
    H.piece("CanopyP", "Canopy", cv, col="primary", mat="cloth", tris=2400, res=140, pattern=combine(ribs, age))
    # rib tips at the hem, lashing ring, finial
    tips = None
    for i in range(8):
        a = i / 8 * TAU
        d = A(math.sin(a), 0, -math.cos(a))
        tips = U(tips, capsule(T(d * 1.02 + A(0, 1.3, 0)), T(d * 0.92 + A(0, 1.5, 0)), 0.035))
    tips = U(tips, torus(0.22, 0.04).at(0, 1.42, 0), cylinder(0.08, 0.12).at(0, 1.35, 0))
    H.piece("Ribs", "Canopy", tips, col="darkWood", mat="wood", tris=700, role="detail", pri=1.4)
    fin = U(cylinder(0.05, 0.15).at(0, 3.82, 0), sphere(0.09, (0, 3.98, 0)), torus(0.09, 0.025).at(0, 3.7, 0))
    H.piece("Finial", "Tip", fin, col="darkWood", mat="wood", tris=300, role="detail", pri=1.6)
    # the one eye: white ball, iris, pupil, shine (on its own bone so it can roll), heavy upper lid
    H.prim("EyeW", "EyeB", "Ellipsoid", (0.56, 0.56, 0.5), (0, 2.45, -0.62), col="eyeWhite", mat="hard", role="eye", pri=1.1)
    H.prim("Iris", "EyeB", "Ellipsoid", (0.32, 0.32, 0.2), (0, 2.45, -0.83), col="iris", mat="hard", role="eye", pri=1.15)
    H.prim("Pupil", "EyeB", "Ellipsoid", (0.17, 0.2, 0.1), (0, 2.45, -0.9), col="pupil", mat="hard", role="pupil", pri=1.2)
    H.prim("Shine", "EyeB", "Ellipsoid", (0.08, 0.08, 0.06), (0.06, 2.52, -0.93), col="shine", mat="hard", role="shine", pri=2.2)
    H.prim("MouthIn", "Canopy", "Ellipsoid", (0.8, 0.2, 0.3), (0, 1.92, -0.82), col="mouth", mat="hard", role="mouth", pri=1.5)
    tg = tube([(0, 1.88, -0.85), (0, 1.72, -1.1), (0, 1.35, -1.18), (0, 1.12, -1.05)], [0.13, 0.15, 0.14, 0.1], k=0.06)
    tg = tg.scale3(1.35, 1.0, 1.0) if False else tg
    tg = tg.ss(capsule((0, 1.75, -1.25), (0, 1.15, -1.2), 0.025), 0.02)  # tongue groove
    H.piece("TongueP", "Tongue", tg, col="tongue", mat="skin", tris=600, role="tongue", pri=1.3)
    # the leg: a short handle stub, a sturdy hairy leg, a geta sandal with two teeth and a thong
    lg = U(cylinder(0.09, 0.12).at(0, 1.35, 0),
           round_cone((0, 1.22, 0), (0, 0.7, -0.05), 0.17, 0.13), sphere(0.13, (0, 0.68, -0.06)), k=0.06)
    H.piece("Thigh", "Hip", lg, col="skin", mat="skin", tris=700, role="limb")
    sh = round_cone((0, 0.68, -0.05), (0, 0.24, 0.0), 0.12, 0.08).su(ellipsoid(0.1, 0.12, 0.08, (0, 0.5, 0.06)), 0.06)
    sh = sh.su(ellipsoid(0.1, 0.08, 0.2, (0, 0.17, -0.1)), 0.06)
    H.piece("Shin", "Knee", sh, col="skin", mat="skin", tris=600, role="limb")
    geta = round_box(0.15, 0.035, 0.3, 0.02, (0, 0.105, -0.06)) | round_box(0.13, 0.04, 0.035, 0.01, (0, 0.04, -0.24)) | round_box(0.13, 0.04, 0.035, 0.01, (0, 0.04, 0.12))
    H.piece("Geta", "Foot", geta, col="wood", mat="wood", tris=400, role="foot")
    H.prim("Thong", "Foot", "Block", (0.2, 0.04, 0.06), (0, 0.2, -0.2), rot=(0.4, 0, 0), col="red", mat="cloth", role="detail", pri=1.8)
    H.socket("mouth", (0, 1.15, -1.1), "Tongue")
    H.socket("head", (0, 3.9, 0), "Tip")
    H.rig.update({"head": "Canopy", "jaw": "Tongue", "legs": [{"hip": "Hip", "knee": "Knee", "phase": 0.0, "side": 1}]})

    def crouch(p, c):
        add(p, "Body", (0, -0.35 * c, 0, 0, 0, 0))
        add(p, "Hip", (0, 0, 0, 0.55 * c, 0, 0))
        add(p, "Knee", (0, 0, 0, -1.1 * c, 0, 0))
        add(p, "Foot", (0, 0, 0, 0.55 * c, 0, 0))

    def idle(t):
        u = t / 2.0
        p = {}
        c = 0.25 + 0.2 * math.sin(TAU * u)
        crouch(p, c)
        add(p, "Canopy", (0, 0, 0, 0.04 * math.sin(TAU * u - 0.6), 0, 0.05 * math.sin(TAU * u * 0.5)))
        add(p, "Tip", (0, 0, 0, 0.06 * math.sin(TAU * u - 1.2), 0, 0.08 * math.sin(TAU * u * 0.5 - 1)))
        add(p, "EyeB", (0, 0, 0, 0.12 * math.sin(TAU * u * 0.5), 0.45 * math.sin(TAU * u * 0.5 + 0.5), 0))
        add(p, "Tongue", (0, 0, 0, 0.12 * math.sin(TAU * u - 1.5), 0, 0.1 * math.sin(TAU * u * 0.5)))
        return p

    def move(t):
        u = t / 0.6
        ph = TAU * u
        air = max(0.0, math.sin(ph))
        land = max(0.0, -math.sin(ph))
        p = {}
        crouch(p, 0.15 + 0.7 * land)
        add(p, "Body", (0, 0.9 * air, 0, -0.15 + 0.12 * math.cos(ph), 0, 0))
        add(p, "Hip", (0, 0, 0, -0.2 * air, 0, 0))
        add(p, "Canopy", (0, 0, 0, 0.14 * math.cos(ph - 0.8), 0, 0.04 * math.sin(ph)))
        add(p, "Tip", (0, 0, 0, 0.2 * math.cos(ph - 1.6), 0, 0))
        add(p, "Tongue", (0, 0, 0, -0.45 * math.cos(ph - 1.0), 0, 0.2 * math.sin(ph)))
        add(p, "EyeB", (0, 0, 0, -0.15 * air, 0, 0))
        return p

    def attack(t):
        s = t / 0.9
        w, st, rec = env(s)
        p = {}
        crouch(p, 0.7 * w)
        add(p, "Body", (0, 0.3 * st, -0.6 * st, 0.15 * w - 0.35 * st, 0, 0))
        add(p, "Canopy", (0, 0, 0, 0.2 * w - 0.2 * st, 0, 0))
        add(p, "Tongue", (0, 0, -0.1 * st, 0.25 * w - 1.6 * st, 0, 0.3 * st * math.sin(TAU * s * 3)))
        add(p, "EyeB", (0, 0, 0, -0.2 * st, 0, 0))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, 0.1 * k, 0.3 * k, 0.35 * k, 0, 0.12 * math.sin(t * 40) * k))
        add(p, "Tip", (0, 0, 0, -0.3 * k, 0, 0))
        add(p, "Tongue", (0, 0, 0, 0.6 * k, 0, 0))
        add(p, "EyeB", (0, 0, 0, 0.3 * k, 0.4 * k, 0))
        return p

    clips(H, idle, move, attack, hit, 4.0, idle_len=2.0, move_len=0.6)
    return H


# ================================================================================================ sock puppet
@hero("sock puppet", "objects")
def sock_puppet():
    """A striped knitted sock standing up out of its ribbed cuff, the toe bent forward into a puppet head: a hinged
    mouth (upper toe and lower jaw) with a red felt tongue, two mismatched sewing-button eyes on top, a heel bump at
    the back, yarn hair loops. Chatters, sways like an arm inside it, hops and chomps."""
    H = OH("sock puppet", plan="Blob", gait="hop", tags=["object", "puppet", "cloth"])
    H.preview = {"primary": "#E9E4D8", "secondary": "#C2412D"}
    H.body((0, 0.45, 0))
    H.bone("Neck", "Body", (0, 1.15, 0.0))
    H.bone("Head", "Neck", (0, 2.15, -0.25))
    H.bone("Jaw", "Head", (0, 2.12, -0.2))
    H.bone("Hair", "Head", (0, 2.62, -0.4))
    wool = dict(mat="cloth")
    knit = stripes(lambda P: P[:, 1], 2.4, width=0.35, depth=0.5)
    ribbed = stripes(lambda P: _ang(P) / (TAU / 28), 1.0, width=0.35, depth=0.12)
    low = U(cylinder(0.5, 0.25, rr=0.08).at(0, 0.25, 0.02), round_cone((0, 0.5, 0.02), (0, 1.25, 0.0), 0.46, 0.43), k=0.12)
    low = low.su(ellipsoid(0.38, 0.32, 0.3, (0, 0.85, 0.28)), 0.2)  # heel bump at the back
    low = (low & plane((0, -1, 0), 0.0)).ss(cylinder(0.38, 0.08).at(0, 0.0, 0.02), 0.05)  # open cuff
    H.piece("Cuff", "Body", (cylinder(0.53, 0.2, rr=0.06).at(0, 0.2, 0.02) & plane((0, -1, 0), 0.0)).ss(cylinder(0.4, 0.08).at(0, 0.0, 0.02), 0.04),
            col="secondary", tris=700, pattern=ribbed, **wool)
    H.piece("Lower", "Body", low & plane((0, 1, 0), 1.3), col="primary", tris=1100, **wool)
    up = tube([(0, 1.1, 0.0), (0, 1.6, 0.03), (0, 2.0, -0.05), (0, 2.22, -0.3)], [0.43, 0.42, 0.41, 0.4], k=0.1)
    H.piece("Upper", "Neck", up, col="primary", tris=1100, **wool)
    bands = None
    for y0 in (0.55, 0.95):
        bands = U(bands, low.round(0.018) & SDF(lambda p, y0=y0: np.abs(p[:, 1] - y0) - 0.12))
    H.piece("StripesLo", "Body", bands, col="secondary", tris=700, role="detail", pri=1.3, **wool)
    ub = None
    for y0 in (1.45, 1.85):
        ub = U(ub, up.round(0.018) & SDF(lambda p, y0=y0: np.abs(p[:, 1] - y0) - 0.12))
    H.piece("StripesUp", "Neck", ub, col="secondary", tris=600, role="detail", pri=1.3, **wool)
    top = ellipsoid(0.47, 0.32, 0.62, (0, 2.3, -0.62)).su(sphere(0.4, (0, 2.25, -0.25)), 0.2)
    top = top & SDF(lambda p: 2.17 - p[:, 1] + 0.0 * p[:, 2])
    H.piece("Toe", "Head", top.round(0.0), col="secondary", tris=1100, role="head", pattern=knit, **wool)
    jaw = ellipsoid(0.43, 0.22, 0.58, (0, 2.1, -0.6)).su(sphere(0.36, (0, 2.08, -0.25)), 0.2)
    jaw = jaw & SDF(lambda p: p[:, 1] - 2.13)
    H.piece("JawP", "Jaw", jaw, col="secondary", tris=900, role="jaw", pattern=knit, **wool)
    H.prim("MouthIn", "Head", "Ellipsoid", (0.78, 0.07, 1.02), (0, 2.16, -0.6), col="mouth", mat="cloth", role="mouth", pri=1.4)
    H.prim("TongueF", "Jaw", "Ellipsoid", (0.42, 0.06, 0.55), (0, 2.15, -0.66), col="red", mat="cloth", role="tongue", pri=1.6)
    for sx, nm, r, c in ((1, "R", 0.15, "black"), (-1, "L", 0.12, "dark")):
        n = A(0.25 * sx, 0.75, -0.6)
        b = button_eye(r, (0.2 * sx, 2.58, -0.62), n, holes=4 if sx > 0 else 2)
        H.piece("Button" + nm, "Head", b, col=c, mat="plastic", tris=400, role="eye", pri=1.2, smooth=1, key=f"h_sock puppet_button{nm.lower()}")
    loops = None
    for i, (x, z, a) in enumerate(((0.0, -0.32, 0), (0.12, -0.24, 30), (-0.12, -0.24, -30), (0.05, -0.12, 15), (-0.06, -0.1, -15))):
        loops = U(loops, torus(0.1, 0.025, axis=2).rot(0, a, 0).at(x, 2.68, z))
    H.piece("HairP", "Hair", loops, col="gold", mat="cloth", tris=700, role="hair", pri=1.5)
    H.socket("mouth", (0, 2.15, -1.15), "Jaw")
    H.socket("head", (0, 2.9, -0.4), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw"})

    def talk(u, rate=3.0):
        return max(0.0, math.sin(TAU * u * rate)) * (0.6 + 0.4 * math.sin(TAU * u * 1.3))

    def idle(t):
        u = t / 2.4
        p = {}
        add(p, "Body", (0, 0, 0, 0, 0.1 * math.sin(TAU * u * 0.5), 0))
        add(p, "Neck", (0, 0, 0, 0.06 * math.sin(TAU * u), 0, 0.1 * math.sin(TAU * u * 0.5)))
        add(p, "Head", (0, 0, 0, 0.08 * math.sin(TAU * u + 0.8) + 0.1 * talk(u), 0.25 * math.sin(TAU * u * 0.5 + 0.6), -0.1 * math.sin(TAU * u * 0.5 + 0.4)))
        add(p, "Jaw", (0, 0, 0, 0.45 * talk(u), 0, 0))
        add(p, "Hair", (0, 0, 0, 0.15 * math.sin(TAU * u * 2), 0, 0.15 * math.sin(TAU * u)))
        return p

    def move(t):
        u = t / 0.7
        ph = TAU * u
        air = max(0.0, math.sin(ph))
        land = max(0.0, -math.sin(ph))
        p = {}
        add(p, "Body", (0, 0.45 * air, 0, -0.1 * math.cos(ph), 0, 0.06 * math.sin(ph * 0.5)))
        add(p, "Neck", (0, -0.08 * land, 0, 0.25 * land - 0.12 * air, 0, 0))
        add(p, "Head", (0, 0, 0, -0.25 * land + 0.2 * air, 0, 0))
        add(p, "Jaw", (0, 0, 0, 0.35 * air, 0, 0))
        add(p, "Hair", (0, 0, 0, -0.4 * math.cos(ph - 0.8), 0, 0))
        return p

    def attack(t):
        s = t / 0.8
        w, st, rec = env(s, 0.4, (0.35, 0.8))
        p = {}
        add(p, "Body", (0, 0, 0.2 * w - 0.25 * st, 0, 0, 0))
        add(p, "Neck", (0, 0, 0, -0.35 * w + 0.6 * st, 0, 0))
        add(p, "Head", (0, 0, 0, -0.5 * w + 0.25 * st, 0, 0))
        add(p, "Jaw", (0, 0, 0, 1.0 * w + 0.9 * min(1.0, w + st) * (1 - bump(s, 0.5, 0.75)) - 0.9 * bump(s, 0.5, 0.75), 0, 0))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Neck", (0, 0, 0, -0.45 * k, 0, 0.2 * math.sin(t * 35) * k))
        add(p, "Head", (0, 0, 0, -0.3 * k, 0.3 * k, 0))
        add(p, "Jaw", (0, 0, 0, 0.6 * k, 0, 0))
        return p

    clips(H, idle, move, attack, hit, 3.0, move_len=0.7, attack_len=0.8)
    return H


# ================================================================================================ living sword
def _blade(p):
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    w = np.where(y > 1.05, 0.21 - 0.03 * (y - 1.05) / 1.3, 0.21 * np.clip((y - 0.32) / 0.73, 0, 1) ** 0.8)
    w = np.maximum(w, 1e-3)
    t = 0.06 * np.clip(1 - np.abs(x) / w, 0, 1) + 0.008
    d = np.maximum(np.abs(x) - w, np.abs(z) - t)
    d = np.maximum(d, y - 2.42)
    d = np.maximum(d, 0.3 - y)
    return d * 0.8


@hero("living sword", "objects")
def living_sword():
    """A haunted longsword hovering point-down: a beveled steel blade with a fuller groove and glowing runes, an
    ornate crossguard whose quillons curl up like horns, a round guard boss holding ONE living eye (iris, slit
    pupil, lid), a leather-wrapped grip and a gem pommel. Hovers and sways, blinks, and swings itself in a big slash."""
    H = OH("living sword", plan="Ghost", gait="hover", tags=["object", "weapon", "haunted"])
    H.preview = {"primary": "#B9C2CC", "secondary": "#8B5CF6", "leather": "#5B3A24"}
    H.body((0, 2.5, 0))
    H.bone("Tip", "Body", (0, 0.4, 0))
    H.bone("Pommel", "Body", (0, 3.45, 0))
    H.bone("EyeB", "Body", (0, 2.5, -0.1))
    H.bone("Lid", "Body", (0, 2.5, -0.1))
    bl = SDF(_blade)
    bl = bl.ss(round_box(0.035, 0.6, 0.2, 0.03, (0, 1.75, 0)), 0.015)  # fuller
    H.piece("BladeP", "Body", bl, col="primary", mat="metal", tris=1300, res=150, smooth=2, role="body",
            pattern=gradient(1, 0.4, 2.4, 0.82, 1.0))
    for z, nm in ((-0.035, "F"), (0.035, "B")):
        H.prim("Rune" + nm, "Body", "Block", (0.03, 1.05, 0.012), (0, 1.75, z), col="glow", mat="hard", glow=True, role="rune", pri=1.7)
    # crossguard: thick bar, quillons curling up into horn tips, a round boss for the eye
    g = capsule((-0.55, 2.47, 0), (0.55, 2.47, 0), 0.085).scale3(1.0, 1.0, 1.0)
    for sx in (1, -1):
        g = g.su(tube([(0.5 * sx, 2.47, 0), (0.78 * sx, 2.58, 0), (0.92 * sx, 2.82, 0), (0.86 * sx, 3.02, 0)], [0.085, 0.07, 0.05, 0.02], k=0.03), 0.03)
        g = g.su(round_cone((0.18 * sx, 2.4, 0), (0.3 * sx, 2.2, 0), 0.06, 0.03), 0.04)  # down-swept langets
    g = g.su(ellipsoid(0.3, 0.3, 0.17, (0, 2.5, 0)), 0.06)
    g = g.ss(ellipsoid(0.21, 0.21, 0.1, (0, 2.5, -0.17)), 0.02)  # eye socket
    g = g | torus(0.23, 0.03, axis=2).at(0, 2.5, -0.13)
    H.piece("Guard", "Body", g, col="gold", mat="metal", tris=1300, role="head", pri=1.1)
    H.prim("EyeW", "EyeB", "Ellipsoid", (0.4, 0.4, 0.26), (0, 2.5, -0.1), col="eyeWhite", mat="hard", role="eye", pri=1.2)
    H.prim("Iris", "EyeB", "Ellipsoid", (0.26, 0.26, 0.12), (0, 2.5, -0.2), col="glow", mat="hard", glow=True, role="eye", pri=1.25)
    H.prim("Pupil", "EyeB", "Ellipsoid", (0.06, 0.2, 0.08), (0, 2.5, -0.25), col="pupil", mat="hard", role="pupil", pri=1.3)
    lid = (sphere(0.21, (0, 2.5, -0.1)).shell(0.025) & plane((0, -1, 0), -2.53)) & plane((0, 0, 1), 0.02)
    H.piece("LidP", "Lid", lid, col="gold", mat="metal", tris=300, role="lid", pri=1.3)
    grip = U(cylinder(0.075, 0.36).at(0, 2.95, 0), *(torus(0.078, 0.022).rot(18, 0, 0).at(0, 2.66 + 0.09 * i, 0) for i in range(7)))
    H.piece("Grip", "Body", grip, col="leather", mat="cloth", tris=700, role="limb", pri=1.4)
    pm = U(sphere(0.15, (0, 3.42, 0)), cylinder(0.1, 0.05).at(0, 3.3, 0), cone(0.08, 0.0, 0.08).at(0, 3.62, 0), k=0.03)
    pm = pm.ss(sphere(0.08, (0, 3.42, -0.15)), 0.02)
    H.piece("PommelP", "Pommel", pm, col="gold", mat="metal", tris=500, role="detail", pri=1.4)
    H.prim("Gem", "Pommel", "Ellipsoid", (0.13, 0.13, 0.09), (0, 3.42, -0.12), col="gem", mat="glass", glow=True, role="gem", pri=1.6)
    H.socket("mouth", (0, 0.4, 0), "Tip")
    H.socket("head", (0, 3.7, 0), "Pommel")
    H.socket("hand", (0, 0.35, 0), "Tip")
    H.rig.update({"head": "EyeB"})

    def blink(u, at=0.55, w=0.05):
        return bump(u % 1.0, at - w, at + w)

    def idle(t):
        u = t / 3.0
        p = {}
        add(p, "Body", (0, 0.12 * math.sin(TAU * u), 0, 0.05 * math.sin(TAU * u + 1), 0.35 * math.sin(TAU * u * 0.5), 0.06 * math.sin(TAU * u)))
        add(p, "EyeB", (0, 0, 0, 0.15 * math.sin(TAU * u * 0.5 + 2), 0.5 * math.sin(TAU * u * 0.5 + 0.7), 0))
        add(p, "Lid", (0, 0, 0, -1.35 * blink(u) + 0.15, 0, 0))
        return p

    def move(t):
        u = t / 1.0
        p = {}
        add(p, "Body", (0, 0.3 + 0.08 * math.sin(TAU * u * 2), 0, -0.35 + 0.05 * math.sin(TAU * u * 2), 0.08 * math.sin(TAU * u), 0.12 * math.sin(TAU * u)))
        add(p, "EyeB", (0, 0, 0, 0.45, 0, 0))
        add(p, "Lid", (0, 0, 0, 0.1, 0, 0))
        return p

    def attack(t):
        s = t / 0.85
        w, st, rec = env(s, 0.35, (0.3, 0.75))
        p = {}
        add(p, "Body", (0, 0.6 * w + 0.2 * st, 0.35 * w - 0.9 * st, -1.2 * w + 2.6 * st, 0.3 * w, 0.4 * w - 0.6 * st))
        add(p, "Lid", (0, 0, 0, -0.3 * w + 0.25 * st, 0, 0))
        add(p, "EyeB", (0, 0, 0, 0.6 * w - 0.6 * st, 0, 0))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, 0.1 * k, 0.35 * k, -0.4 * k, 0, 0.25 * math.sin(t * 45) * k))
        add(p, "Lid", (0, 0, 0, -1.2 * k, 0, 0))
        return p

    clips(H, idle, move, attack, hit, 3.6, idle_len=3.0, move_len=1.0, attack_len=0.85)
    return H


# ================================================================================================ animated broom
@hero("animated broom", "objects")
def animated_broom():
    """An enchanted besom broom marching on its straw: a flared bundle of bristles bound with twine, a gnarled
    wooden handle with a carved knot face (two glowing eye holes), and twig arms that carry two wooden buckets with
    iron hoops and sloshing water. Marches with hops and swinging buckets; its attack is a big sweep."""
    H = OH("animated broom", plan="Biped", gait="hop", tags=["object", "enchanted"])
    H.preview = {"primary": "#D9B45A", "secondary": "#8A5A33", "glass": "#7CC6E8"}
    H.body((0, 0.55, 0))
    H.bone("Handle", "Body", (0, 1.05, 0))
    H.bone("Knob", "Handle", (0, 3.4, 0))
    H.mbone("Shoulder#", "Handle", (0.06, 2.35, 0))
    H.mbone("Elbow#", "Shoulder#", (0.55, 2.0, -0.12))
    H.mbone("Hand#", "Elbow#", (0.72, 1.62, -0.22))
    H.mbone("Bucket#", "Hand#", (0.72, 1.55, -0.22))

    def straw(p):
        y = p[:, 1]
        th = np.arctan2(p[:, 0], p[:, 2])
        t = np.clip((1.05 - y) / 1.05, 0, 1)
        R = 0.2 + 0.42 * t ** 1.3 + 0.012 * np.sin(th * 23 + y * 3)
        rho = np.sqrt(p[:, 0] ** 2 + (p[:, 2] * 1.25) ** 2)
        d = (rho - R) * 0.8
        tips = 0.03 + 0.05 * (0.5 + 0.5 * np.sin(th * 11)) * (0.5 + 0.5 * np.cos(th * 7 + 1))
        d = np.maximum(d, tips - y)
        return np.maximum(d, y - 1.12)

    br = SDF(straw)
    H.piece("Bristles", "Body", br, col="primary", mat="cloth", tris=1800, res=140, role="body",
            pattern=combine(stripes(lambda P: np.arctan2(P[:, 0], P[:, 2]) / (TAU / 40), 1.0, width=0.4, depth=0.3), gradient(1, 0.0, 1.0, 0.75, 1.0)))
    twine = U(torus(0.25, 0.045).at(0, 0.95, 0).scale3(1.0, 1.0, 0.82), torus(0.3, 0.05).at(0, 0.72, 0).scale3(1.0, 1.0, 0.82))
    H.piece("Twine", "Body", twine, col="red", mat="cloth", tris=600, role="detail", pri=1.4,
            pattern=stripes(lambda P: np.arctan2(P[:, 0], P[:, 2]) / (TAU / 30), 1.0, width=0.3, depth=0.35))
    hd = tube([(0, 0.9, 0), (0.02, 1.8, 0.0), (-0.02, 2.6, 0.02), (0, 3.3, 0)], [0.085, 0.08, 0.085, 0.09], k=0.04)
    hd = hd.su(ellipsoid(0.17, 0.24, 0.15, (0, 3.05, -0.02)), 0.12)  # knot head
    hd = hd.su(sphere(0.11, (0, 3.45, 0)), 0.06)
    hd = hd.ss(ellipsoid(0.045, 0.06, 0.06, (0.07, 3.1, -0.16)).mirror_x(), 0.02)
    hd = hd.su(sphere(0.04, (0.06, 2.0, -0.07)), 0.03).noise(0.008, 9, 2)
    H.piece("Stick", "Handle", hd, col="secondary", mat="wood", tris=1100, role="head",
            pattern=stripes(lambda P: P[:, 1] + 0.3 * np.sin(np.arctan2(P[:, 0], P[:, 2]) * 2), 6.0, width=0.2, depth=0.18))
    for sx in (1, -1):
        led_eye(H, "Eye" + ("R" if sx > 0 else "L"), "Handle", (0.07 * sx, 3.1, -0.14), (0.06, 0.08, 0.04), col="eyeGlow")
    H.prim("Brow", "Handle", "Block", (0.24, 0.035, 0.05), (0, 3.2, -0.15), rot=(0.2, 0, 0), col="darkWood", mat="wood", role="brow", pri=2.0)

    for sx, nm in ((1, "R"), (-1, "L")):
        sfx = "" if sx > 0 else "_l"
        sh, el, wr = A(0.06 * sx, 2.35, 0), A(0.55 * sx, 2.0, -0.12), A(0.72 * sx, 1.62, -0.22)
        arm = tube([T(sh), T((sh + el) / 2 + A(0.02 * sx, 0.05, 0)), T(el)], [0.045, 0.04, 0.038], k=0.02)
        arm = arm.su(round_cone(T((sh + el) / 2), T((sh + el) / 2 + A(0.05 * sx, 0.18, 0.03)), 0.02, 0.008), 0.01)
        H.piece("UpperArm" + nm, "Shoulder" + nm, arm, col="secondary", mat="wood", tris=300, role="limb", key=f"h_animated broom_ua{sfx}")
        fo = tube([T(el), T(wr)], [0.038, 0.032])
        for i, (dz, dy) in enumerate(((-0.06, 0.0), (0.0, 0.02), (0.06, 0.0))):
            fo = fo | tube([T(wr), T(wr + A(0.02 * sx, -0.08, dz)), T(wr + A(-0.03 * sx, -0.14, dz * 1.3))], [0.026, 0.02, 0.012])
        H.piece("Forearm" + nm, "Elbow" + nm, fo, col="secondary", mat="wood", tris=400, role="hand", key=f"h_animated broom_fo{sfx}")
        bc = A(0.72 * sx, 0.95, -0.22)

        def bucket_f(p, bc=bc):
            q = p - bc
            yy = q[:, 1]
            r = 0.24 + 0.05 * (yy + 0.22) / 0.44
            rho = np.sqrt(q[:, 0] ** 2 + q[:, 2] ** 2)
            outer = np.maximum(rho - r, np.abs(yy) - 0.22)
            inner = np.maximum(rho - (r - 0.03), -(yy + 0.18))
            return np.maximum(outer, -inner)

        bk = SDF(bucket_f)
        hoops = U(torus(0.255, 0.018).at(*T(bc + A(0, -0.13, 0))), torus(0.285, 0.018).at(*T(bc + A(0, 0.15, 0))))
        H.piece("Pail" + nm, "Bucket" + nm, bk, col="wood", mat="wood", tris=700, role="detail", key=f"h_animated broom_pail{sfx}", pri=1.2,
                pattern=stripes(lambda P, c=bc: np.arctan2(P[:, 0] - c[0], P[:, 2] - c[2]) / (TAU / 14), 1.0, width=0.12, depth=0.4))
        bail = (torus(0.27, 0.016, axis=2).at(*T(bc + A(0, 0.2, 0))) & plane((0, -1, 0), -(bc[1] + 0.2)))
        H.piece("Hoops" + nm, "Bucket" + nm, U(hoops, bail), col="steel", mat="metal", tris=500, role="detail", key=f"h_animated broom_hoop{sfx}", pri=1.5)
        H.prim("Water" + nm, "Bucket" + nm, "Cylinder", (0.03, 0.5, 0.5), T(bc + A(0, 0.12, 0)), rot=(0, 0, math.pi / 2), col="glass", mat="glass", tr=0.25, role="water", pri=1.8)
    H.socket("mouth", (0, 3.05, -0.2), "Handle")
    H.socket("head", (0, 3.6, 0), "Knob")
    H.socket("hand", (0.72, 0.9, -0.22), "BucketR")
    H.rig.update({"head": "Handle", "arms": [{"shoulder": "ShoulderR", "elbow": "ElbowR", "side": 1}, {"shoulder": "ShoulderL", "elbow": "ElbowL", "side": -1}]})

    def idle(t):
        u = t / 2.6
        p = {}
        add(p, "Handle", (0, 0, 0, 0.03 * math.sin(TAU * u), 0.12 * math.sin(TAU * u * 0.5), 0.05 * math.sin(TAU * u + 0.5)))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Shoulder" + nm, (0, 0, 0, 0.05 * math.sin(TAU * u + sg), 0, sg * 0.05 * math.sin(TAU * u)))
            add(p, "Bucket" + nm, (0, 0, 0, 0.12 * math.sin(TAU * u + 1 + sg * 0.5), 0, sg * 0.08 * math.sin(TAU * u + 2)))
        add(p, "Body", (0, 0.02 * math.sin(TAU * u * 2), 0, 0, 0, 0))
        return p

    def move(t):
        u = t / 0.8
        ph = TAU * u
        air = max(0.0, math.sin(ph * 2))
        p = {}
        add(p, "Body", (0, 0.32 * air, 0, -0.08, 0, 0.12 * math.sin(ph)))
        add(p, "Handle", (0, 0, 0, -0.05, 0.1 * math.sin(ph), -0.08 * math.sin(ph)))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Shoulder" + nm, (0, 0, 0, 0.25 * math.sin(ph + (0 if sg > 0 else math.pi)), 0, 0))
            add(p, "Bucket" + nm, (0, 0, 0, -0.3 * math.sin(ph + (0 if sg > 0 else math.pi) - 0.9), 0, sg * 0.15 * math.sin(ph * 2 - 1)))
        return p

    def attack(t):
        s = t / 1.0
        w, st, rec = env(s, 0.35, (0.3, 0.85))
        sweep = math.sin(math.pi * min(max((s - 0.3) / 0.55, 0), 1) - math.pi / 2) if 0.3 < s < 0.85 else (-1.0 if s <= 0.3 else 1.0)
        p = {}
        add(p, "Body", (0, 0.45 * w + 0.15 * st, -0.2 * st, 0.4 * w + 0.15 * st, -0.9 * sweep * (w + st), 0.35 * st))
        add(p, "Handle", (0, 0, 0, -0.2 * st, 0, 0))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Shoulder" + nm, (0, 0, 0, 0.8 * w - 0.3 * st, 0, sg * 0.5 * (w + st)))
            add(p, "Bucket" + nm, (0, 0, 0, -0.6 * st, 0, sg * 0.4 * st))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, 0.1 * k, 0.3 * k, 0.35 * k, 0, 0.15 * math.sin(t * 40) * k))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Shoulder" + nm, (0, 0, 0, 0.5 * k, 0, sg * 0.6 * k))
            add(p, "Bucket" + nm, (0, 0, 0, 0.6 * k, 0, 0))
        return p

    clips(H, idle, move, attack, hit, 3.6, idle_len=2.6, move_len=0.8, attack_len=1.0)
    return H


# ================================================================================================ wind-up toy
@hero("wind-up toy", "objects")
def wind_up_toy():
    """A lithographed tin toy chick: two pressed tin halves crimped together with a rolled seam and folded tabs,
    printed stripes, painted dot eyes with lashes, a tin beak, flapping tin wings, big tin feet on pegs, and a giant
    brass butterfly key in its back that turns as it waddles."""
    H = OH("wind-up toy", plan="Biped", gait="waddle", tags=["object", "toy", "tin", "clockwork"])
    H.preview = {"primary": "#F2C230", "secondary": "#D9372B", "gold": "#D9A93A", "blush": "#FF8FA3"}
    H.body((0, 0.55, 0))
    H.bone("Shell", "Body", (0, 0.9, 0))
    H.bone("Head", "Shell", (0, 1.7, -0.1))
    H.bone("Key", "Shell", (0, 1.15, 0.72))
    H.mbone("Wing#", "Shell", (0.62, 1.25, 0.05))
    H.mbone("Leg#", "Body", (0.3, 0.45, -0.02))
    tin = dict(col="primary", mat="metal")
    bd = ellipsoid(0.72, 0.7, 0.68, (0, 1.1, 0.02)).su(ellipsoid(0.55, 0.5, 0.5, (0, 1.7, -0.08)), 0.3)
    seam = SDF(lambda p: np.abs(p[:, 2] - 0.05) - 0.035) & bd.round(0.035)
    for sx in (1, -1):  # crimped tabs folded over the seam
        for y in (0.75, 1.35, 1.85):
            seam = seam | round_box(0.03, 0.07, 0.06, 0.015, (0.0, 0, 0)).at(sx * float(np.sqrt(max(0.0, 0.6 ** 2 - (y - 1.2) ** 2 * 0.5))) + sx * 0.12, y, 0.05)
    dots = spots(0.22, 0.05, depth=0.35, region=lambda P: np.clip((1.05 - P[:, 1]) / 0.2, 0, 1), seed=11)
    H.piece("Tin", "Shell", bd & plane((0, -1, 0), -0.45), tris=2000, res=128, pattern=dots, **tin)
    H.piece("Seam", "Shell", seam & plane((0, -1, 0), -0.48), col="gold", mat="metal", tris=900, role="detail", pri=1.3)
    band = bd.round(0.012) & SDF(lambda p: np.abs(p[:, 1] - 1.05) - 0.07)
    H.piece("Band", "Shell", band, col="secondary", mat="metal", tris=700, role="detail", pri=1.4)
    H.prim("BeakU", "Head", "Ellipsoid", (0.22, 0.12, 0.3), (0, 1.62, -0.66), rot=(0.25, 0, 0), col="beak", mat="metal", role="beak", pri=1.4)
    H.prim("BeakL", "Head", "Ellipsoid", (0.18, 0.08, 0.22), (0, 1.53, -0.62), rot=(0.1, 0, 0), col="dark", mat="metal", role="beak", pri=1.6)
    for sx, nm in ((1, "R"), (-1, "L")):
        H.prim("EyeDisc" + nm, "Head", "Cylinder", (0.03, 0.28, 0.28), (0.22 * sx, 1.82, -0.56), rot=(0, -0.42 * sx + math.pi / 2, 0.25), col="eyeWhite", mat="hard", role="eye", pri=1.2)
        H.prim("EyeDot" + nm, "Head", "Cylinder", (0.03, 0.15, 0.15), (0.235 * sx, 1.8, -0.585), rot=(0, -0.42 * sx + math.pi / 2, 0.25), col="pupil", mat="hard", role="pupil", pri=1.3)
        H.prim("Cheek" + nm, "Head", "Cylinder", (0.02, 0.16, 0.16), (0.42 * sx, 1.55, -0.5), rot=(0, -0.75 * sx + math.pi / 2, 0.3), col="blush", mat="hard", role="cheek", pri=2.0)
    crest = U(*(round_cone((0, 2.05, -0.1 + dz), (0.0, 2.3 + h, -0.05 + dz * 1.6), 0.07, 0.025) for dz, h in ((-0.12, 0.0), (0.0, 0.08), (0.12, 0.0))))
    H.piece("Crest", "Head", crest, col="secondary", mat="metal", tris=400, role="crest", pri=1.5)
    for sx, nm in ((1, "R"), (-1, "L")):
        sfx = "" if sx > 0 else "_l"
        wg = ellipsoid(0.08, 0.3, 0.22, (0.66 * sx, 1.08, 0.08)).rot(0, 0, 0)
        wg = wg.su(ellipsoid(0.06, 0.18, 0.12, (0.7 * sx, 0.86, 0.18)), 0.06)
        H.piece("WingP" + nm, "Wing" + nm, wg, tris=400, role="wing", key=f"h_wind_up_toy_wing{sfx}", **tin)
        lg = cylinder(0.05, 0.12).at(0.3 * sx, 0.38, -0.02) | ellipsoid(0.22, 0.08, 0.34, (0.3 * sx, 0.12, -0.15))
        lg = lg.su(U(*(ellipsoid(0.07, 0.06, 0.12, (0.3 * sx + dx, 0.1, -0.45)) for dx in (-0.12, 0.0, 0.12))), 0.05) & plane((0, -1, 0), 0.0)
        H.piece("Foot" + nm, "Leg" + nm, lg, col="beak", mat="metal", tris=500, role="foot", key=f"h_wind_up_toy_foot{sfx}")
    key = cylinder(0.06, 0.2, axis=2).at(0, 1.15, 0.85)
    key = key | cylinder(0.12, 0.04, axis=2).at(0, 1.15, 0.72)
    for sx in (1, -1):
        bow = (ellipsoid(0.3, 0.2, 0.05, (0.32 * sx, 1.15, 1.08))).ss(ellipsoid(0.15, 0.08, 0.2, (0.36 * sx, 1.15, 1.08)), 0.02)
        key = key.su(bow, 0.05)
    key = key.su(sphere(0.1, (0, 1.15, 1.08)), 0.04)
    H.piece("KeyP", "Key", key, col="gold", mat="metal", tris=800, role="key", pri=1.1)
    H.socket("mouth", (0, 1.58, -0.8), "Head")
    H.socket("head", (0, 2.4, 0), "Head")
    H.rig.update({"head": "Head", "legs": [{"hip": "LegR", "knee": "LegR", "phase": 0.0, "side": 1}, {"hip": "LegL", "knee": "LegL", "phase": 0.5, "side": -1}]})

    def idle(t):
        u = t / 2.4
        p = {}
        spin(p, "Key", "z", t / 2.4 * 20, math.pi, sgn=1, speed=0.35)
        tick = math.sin(TAU * u * 4)
        add(p, "Shell", (0, 0.01 * abs(tick), 0, 0.02 * math.sin(TAU * u), 0.06 * math.sin(TAU * u * 0.5), 0.04 * tick))
        add(p, "Head", (0, 0, 0, 0.08 * math.sin(TAU * u + 1), 0.2 * math.sin(TAU * u * 0.5 + 0.5), 0.06 * math.sin(TAU * u)))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Wing" + nm, (0, 0, 0, 0, 0, sg * 0.15 * max(0.0, math.sin(TAU * u * 2 + sg))))
        return p

    def move(t):
        u = t / 0.6
        ph = TAU * u
        p = {}
        spin(p, "Key", "z", t / 0.6 * 20, math.pi, sgn=1, speed=1.0)
        add(p, "Body", (0, 0.06 * abs(math.sin(ph)), 0, -0.05, 0, 0.16 * math.sin(ph)))
        add(p, "Shell", (0, 0, 0, 0.04 * math.sin(ph * 2), 0.1 * math.sin(ph), 0))
        add(p, "Head", (0, 0, 0, 0.06 * math.sin(ph * 2), -0.08 * math.sin(ph), -0.1 * math.sin(ph)))
        for sg, nm in ((1, "R"), (-1, "L")):
            ph2 = ph + (0 if sg > 0 else math.pi)
            add(p, "Leg" + nm, (0, 0.08 * max(0.0, math.sin(ph2)), 0, 0.45 * math.sin(ph2 + math.pi / 2), 0, -0.16 * math.sin(ph)))
            add(p, "Wing" + nm, (0, 0, 0, 0, 0, sg * 0.45 * max(0.0, math.sin(ph * 2))))
        return p

    def attack(t):
        s = t / 0.8
        w, st, rec = env(s, 0.4, (0.35, 0.8))
        p = {}
        spin(p, "Key", "z", t / 0.8 * 16, math.pi, sgn=1, speed=1.6)
        add(p, "Body", (0, 0.35 * st, -0.4 * st, 0.3 * w - 0.6 * st, 0, 0))
        add(p, "Head", (0, 0, 0, 0.35 * w - 0.4 * st, 0, 0))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Wing" + nm, (0, 0, 0, 0, 0, sg * (0.9 * w + 0.6 * st * math.sin(TAU * s * 6))))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, 0.05 * k, 0.25 * k, 0.3 * k, 0, 0.2 * math.sin(t * 40) * k))
        add(p, "Head", (0, 0, 0, 0.3 * k, 0.3 * k, 0))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Wing" + nm, (0, 0, 0, 0, 0, sg * 0.8 * k))
        return p

    clips(H, idle, move, attack, hit, 2.4, move_len=0.6, attack_len=0.8)
    return H


# ================================================================================================ teddy bears
def _teddy(hid, monster):
    """Plush teddy: a pear-shaped body with a belly patch, a big round head with a centre seam, a velvet muzzle,
    stitched nose and mouth, round ears with inner pads, stubby arms and legs with paw pads, a ribbon bow.
    monster=True: a torn ear, one button eye and one X-stitched eye, a gaping stitched grin full of fangs, claws
    poking through the paws and stuffing bursting out of a ripped belly seam."""
    H = OH(hid, plan="Biped", gait="waddle", tags=["object", "toy", "plush"] + (["monster"] if monster else []))
    H.preview = {"primary": "#B07A45", "secondary": "#C2412D", "belly": "#E9CFA4"} if not monster else {"primary": "#6E5A6E", "secondary": "#5B2A86", "belly": "#BFA7A0"}
    H.body((0, 0.85, 0))
    H.bone("Spine", "Body", (0, 1.15, 0))
    H.bone("Head", "Spine", (0, 1.75, -0.02))
    H.bone("Jaw", "Head", (0, 1.78, -0.42))
    H.mbone("Shoulder#", "Spine", (0.4, 1.48, 0.0))
    H.mbone("Hip#", "Body", (0.28, 0.72, 0.0))
    fur = dict(col="primary", mat="fur")
    seam = lambda P: 1 - 0.45 * np.exp(-(P[:, 0] / 0.018) ** 2)  # noqa: E731
    bd = ellipsoid(0.5, 0.58, 0.44, (0, 1.1, 0.02)).su(ellipsoid(0.44, 0.3, 0.4, (0, 0.78, 0.04)), 0.2)
    bd = bd.noise(0.01, 9, 1)
    if monster:
        bd = bd.ss(ellipsoid(0.14, 0.26, 0.2, (0.08, 1.05, -0.43)), 0.03)  # ripped belly
    H.piece("Torso", "Spine", bd, tris=1300, res=128, pattern=seam, **fur)
    H.prim("BellyPatch", "Spine", "Ellipsoid", (0.56, 0.62, 0.12), (-0.05 if monster else 0, 1.03, -0.38), col="belly", mat="fur", role="belly", pri=1.4)
    if monster:
        stuff = U(*(sphere(r, c) for r, c in ((0.1, (0.08, 1.12, -0.45)), (0.09, (0.13, 0.98, -0.47)), (0.08, (0.02, 0.95, -0.46)),
                                             (0.07, (0.15, 1.2, -0.44)), (0.06, (0.05, 1.27, -0.45)))), k=0.05).noise(0.02, 18, 4)
        H.piece("Stuffing", "Spine", stuff, col="cream", mat="cloth", tris=600, role="detail", pri=1.3)
        stitch = U(*(capsule((0.0 + dx, 1.25 - i * 0.1, -0.45), (0.17 + dx, 1.25 - i * 0.1 - 0.04, -0.43), 0.012) for i, dx in enumerate((-0.02, 0, 0.02, 0.0))))
        H.piece("Stitches", "Spine", stitch, col="black", mat="cloth", tris=300, role="detail", pri=1.8)
    hc = A(0, 1.98, -0.02)
    hd = sphere(0.52, T(hc)).su(ellipsoid(0.5, 0.42, 0.46, T(hc + A(0, -0.12, 0.02))), 0.15).noise(0.008, 9, 2)
    ears = []
    for sx in (1, -1):
        ear = ellipsoid(0.2, 0.2, 0.09, T(hc + A(0.38 * sx, 0.4, 0.04)))
        if monster and sx < 0:
            ear = ear.ss(sphere(0.12, T(hc + A(-0.52, 0.55, 0.04))), 0.02)  # bitten / torn ear
        hd = hd.su(ear, 0.06)
        hd = hd.ss(ellipsoid(0.11, 0.11, 0.06, T(hc + A(0.38 * sx, 0.4, -0.08))), 0.02)
    H.piece("HeadP", "Head", hd, tris=1300, res=128, role="head", pattern=seam, **fur)
    for sx, nm in ((1, "R"), (-1, "L")):
        if monster and sx < 0:
            continue
        H.prim("EarPad" + nm, "Head", "Ellipsoid", (0.2, 0.2, 0.05), T(hc + A(0.38 * sx, 0.4, -0.06)), col="belly", mat="fur", role="ear", pri=1.8)
    mz = ellipsoid(0.27, 0.19, 0.2, T(hc + A(0, -0.16, -0.4)))
    if monster:
        mz = mz.ss(ellipsoid(0.26, 0.08, 0.2, T(hc + A(0, -0.25, -0.55))), 0.03)
    H.piece("Muzzle", "Head", mz, col="belly", mat="fur", tris=600, role="snout", pri=1.2)
    H.prim("Nose", "Head", "Ellipsoid", (0.17, 0.11, 0.1), T(hc + A(0, -0.07, -0.59)), col="nose", mat="plastic", role="nose", pri=1.3)
    if not monster:
        H.prim("MouthV", "Head", "Block", (0.018, 0.1, 0.02), T(hc + A(0, -0.18, -0.6)), col="nose", mat="cloth", role="mouth", pri=1.9)
        for sx in (1, -1):
            H.prim("Smile" + ("R" if sx > 0 else "L"), "Head", "Block", (0.1, 0.018, 0.02), T(hc + A(0.045 * sx, -0.24, -0.585)), rot=(0, 0.3 * sx, 0.45 * sx), col="nose", mat="cloth", role="mouth", pri=1.9)
        for sx, nm in ((1, "R"), (-1, "L")):
            b = button_eye(0.085, T(hc + A(0.19 * sx, 0.08, -0.5)), (0.3 * sx, 0.1, -1.0), holes=4)
            H.piece("Button" + nm, "Head", b, col="black", mat="plastic", tris=350, role="eye", pri=1.2, smooth=1)
        H.prim("Shine", "Head", "Ellipsoid", (0.04, 0.04, 0.03), T(hc + A(0.21, 0.12, -0.54)), col="shine", mat="hard", role="shine", pri=2.4)
    else:
        b = button_eye(0.1, T(hc + A(0.19, 0.08, -0.5)), (0.3, 0.1, -1.0), holes=2)
        H.piece("ButtonR", "Head", b, col="black", mat="plastic", tris=350, role="eye", pri=1.2, smooth=1)
        H.prim("EyeGlow", "Head", "Ellipsoid", (0.05, 0.05, 0.03), T(hc + A(0.205, 0.08, -0.54)), col="eyeGlow", mat="hard", glow=True, role="eye", pri=1.3)
        xs = U(capsule(T(hc + A(-0.27, 0.16, -0.46)), T(hc + A(-0.11, 0.0, -0.5)), 0.02), capsule(T(hc + A(-0.27, 0.0, -0.46)), T(hc + A(-0.11, 0.16, -0.5)), 0.02))
        H.piece("XEye", "Head", xs, col="black", mat="cloth", tris=200, role="eye", pri=1.2)
        H.prim("MouthIn", "Head", "Ellipsoid", (0.44, 0.13, 0.16), T(hc + A(0, -0.25, -0.5)), col="mouth", mat="hard", role="mouth", pri=1.4)
        fangs = U(teeth_row(T(hc + A(0, -0.2, -0.56)), (1, 0, 0), 5, 0.075, 0.11), teeth_row(T(hc + A(0, -0.31, -0.54)), (1, 0, 0), 4, 0.075, 0.08, up=True))
        H.piece("Fangs", "Head", fangs, col="tooth", mat="hard", tris=400, role="teeth", pri=1.3, smooth=1)
    for sx, nm in ((1, "R"), (-1, "L")):
        sh = A(0.4 * sx, 1.48, 0.0)
        pw = A(0.62 * sx, 1.02, -0.18)
        arm = round_cone(T(sh), T(pw), 0.15, 0.14).su(sphere(0.15, T(pw + A(0, -0.03, -0.02))), 0.05)
        H.piece("Arm" + nm, "Shoulder" + nm, arm, tris=450, role="limb", **fur)
        H.prim("PawPad" + nm, "Shoulder" + nm, "Ellipsoid", (0.16, 0.18, 0.06), T(pw + A(0.02 * sx, -0.04, -0.14)), rot=(-0.4, 0, 0), col="belly", mat="fur", role="pad", pri=1.8)
        hp = A(0.28 * sx, 0.72, 0.0)
        leg = round_cone(T(hp), T(A(0.32 * sx, 0.22, -0.04)), 0.21, 0.17).su(ellipsoid(0.2, 0.15, 0.27, (0.32 * sx, 0.15, -0.14)), 0.08)
        leg = leg & plane((0, -1, 0), 0.0)
        H.piece("Leg" + nm, "Hip" + nm, leg, tris=550, role="foot", **fur)
        H.prim("Sole" + nm, "Hip" + nm, "Cylinder", (0.04, 0.24, 0.28), (0.32 * sx, 0.17, -0.39), rot=(0, math.pi / 2, math.pi / 2 - 0.25), col="belly", mat="fur", role="pad", pri=1.8)
        if monster:
            cl = U(*(cone(0.035, 0.0, 0.06, axis=1).rot(-110, 0, 0).at(*T(pw + A(dx * sx, -0.1, -0.15))) for dx in (-0.06, 0.02, 0.09)))
            H.piece("Claws" + nm, "Shoulder" + nm, cl, col="claw", mat="hard", tris=200, role="claw", pri=1.6, smooth=1)
    bow = U(ellipsoid(0.18, 0.11, 0.06, (0.17, 1.6, -0.38)).rot(0, 0, 0), ellipsoid(0.18, 0.11, 0.06, (-0.17, 1.6, -0.38)), sphere(0.07, (0, 1.6, -0.42)), k=0.03)
    bow = bow.su(round_cone((0.04, 1.56, -0.4), (0.12, 1.38, -0.38), 0.04, 0.03).mirror_x(), 0.02)
    H.piece("Bow", "Spine", bow, col="secondary", mat="cloth", tris=500, role="detail", pri=1.4)
    H.socket("mouth", T(hc + A(0, -0.25, -0.62)), "Head")
    H.socket("head", T(hc + A(0, 0.65, 0)), "Head")
    H.socket("hand", (0.64, 0.95, -0.2), "ShoulderR")
    H.rig.update({"head": "Head", "legs": [{"hip": "HipR", "knee": "HipR", "phase": 0.0, "side": 1}, {"hip": "HipL", "knee": "HipL", "phase": 0.5, "side": -1}],
                  "arms": [{"shoulder": "ShoulderR", "elbow": "ShoulderR", "side": 1}, {"shoulder": "ShoulderL", "elbow": "ShoulderL", "side": -1}]})

    def idle(t):
        u = t / 2.8
        p = {}
        add(p, "Spine", (0, 0.015 * math.sin(TAU * u * 2), 0, 0.03 * math.sin(TAU * u), 0, 0.03 * math.sin(TAU * u * 0.5)))
        add(p, "Head", (0, 0, 0, 0.06 * math.sin(TAU * u + 0.8), 0.15 * math.sin(TAU * u * 0.5 + 0.3), (0.12 if not monster else -0.1) * math.sin(TAU * u * 0.5)))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Shoulder" + nm, (0, 0, 0, 0.1 * math.sin(TAU * u + sg), 0, sg * (0.1 + 0.06 * math.sin(TAU * u))))
        if monster:
            add(p, "Spine", (0, 0, 0, 0.12, 0, 0))
            add(p, "Head", (0, 0, 0, -0.1, 0, 0))
        return p

    def move(t):
        u = t / 0.7
        ph = TAU * u
        p = {}
        add(p, "Body", (0, 0.07 * abs(math.sin(ph)), 0, -0.06 if not monster else -0.18, 0, 0.14 * math.sin(ph)))
        add(p, "Spine", (0, 0, 0, 0, 0.1 * math.sin(ph), -0.05 * math.sin(ph)))
        add(p, "Head", (0, 0, 0, 0.05 * math.sin(ph * 2), -0.08 * math.sin(ph), -0.08 * math.sin(ph)))
        for sg, nm in ((1, "R"), (-1, "L")):
            ph2 = ph + (0 if sg > 0 else math.pi)
            add(p, "Hip" + nm, (0, 0.06 * max(0.0, math.sin(ph2)), 0, 0.5 * math.sin(ph2 + math.pi / 2), 0, -0.14 * math.sin(ph)))
            if monster:
                add(p, "Shoulder" + nm, (0, 0, 0, 1.1 + 0.2 * math.sin(ph2), 0, sg * 0.3))
            else:
                add(p, "Shoulder" + nm, (0, 0, 0, -0.45 * math.sin(ph2 + math.pi / 2), 0, sg * 0.15))
        return p

    def attack(t):
        s = t / 0.85
        w, st, rec = env(s, 0.4, (0.35, 0.8))
        p = {}
        add(p, "Body", (0, 0.25 * st, -0.45 * st, 0.15 * w - 0.4 * st, 0, 0))
        add(p, "Spine", (0, 0, 0, 0.25 * w - 0.2 * st, 0, 0))
        add(p, "Head", (0, 0, 0, 0.3 * w - 0.2 * st, 0, 0))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Shoulder" + nm, (0, 0, 0, 2.4 * w + 0.4 * st, 0, sg * (0.6 * w - 0.4 * st)))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, 0.05 * k, 0.25 * k, 0.3 * k, 0, 0.12 * math.sin(t * 40) * k))
        add(p, "Head", (0, 0, 0, 0.35 * k, 0.2 * k, 0.2 * k))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Shoulder" + nm, (0, 0, 0, 0.5 * k, 0, sg * 0.9 * k))
        return p

    clips(H, idle, move, attack, hit, 2.6, idle_len=2.8, move_len=0.7, attack_len=0.85)
    return H


@hero("teddy bear", "objects")
def teddy_bear():
    return _teddy("teddy bear", False)


@hero("teddy bear monster", "objects")
def teddy_bear_monster():
    return _teddy("teddy bear monster", True)


# ================================================================================================ balloon animal
@hero("balloon animal", "objects")
def balloon_animal():
    """A twisted balloon poodle: glossy latex sausages pinched at the twists, a round head with a long snout and a
    knot nose, floppy balloon ears, a pom-pom tail and four stiff balloon legs; marker-drawn eyes. Bounces along on
    stiff legs and squeaks into a head-butt."""
    H = OH("balloon animal", plan="Quadruped", gait="bound", tags=["object", "toy", "balloon"])
    H.preview = {"primary": "#EC4899", "secondary": "#F9A8D4"}
    H.body((0, 1.25, 0.1))
    H.bone("Neck", "Body", (0, 1.35, -0.3))
    H.bone("Head", "Neck", (0, 1.85, -0.5))
    H.bone("Tail", "Body", (0, 1.35, 0.55))
    legs = {"FR": (0.2, -0.22), "FL": (-0.2, -0.22), "BR": (0.2, 0.45), "BL": (-0.2, 0.45)}
    for nm, (x, z) in legs.items():
        H.bone("Leg" + nm, "Body", (x, 1.15, z))
    lat = dict(col="primary", mat="plastic")

    def sausage(a, b, r):
        return capsule(a, b, r)

    bd = U(sausage((0, 1.25, 0.5), (0, 1.25, 0.05), 0.2), sausage((0, 1.25, -0.0), (0, 1.25, -0.28), 0.19))
    H.piece("Torso", "Body", bd, tris=900, **lat)
    nk = sausage((0, 1.42, -0.32), (0, 1.75, -0.47), 0.15)
    H.piece("NeckP", "Neck", nk, tris=500, **lat)
    hd = U(sphere(0.21, (0, 1.95, -0.5)), sausage((0, 1.9, -0.66), (0, 1.86, -1.0), 0.12))
    hd = hd | sphere(0.045, (0, 1.86, -1.13))
    H.piece("HeadP", "Head", hd, tris=900, role="head", **lat)
    ears = U(sausage((0.17, 1.98, -0.48), (0.24, 1.62, -0.42), 0.1), sausage((-0.17, 1.98, -0.48), (-0.24, 1.62, -0.42), 0.1))
    H.piece("Ears", "Head", ears, tris=600, role="ear", **lat)
    for sx, nm in ((1, "R"), (-1, "L")):
        H.prim("Eye" + nm, "Head", "Ellipsoid", (0.05, 0.09, 0.04), (0.11 * sx, 2.02, -0.67), rot=(0.3, -0.5 * sx, 0), col="black", mat="hard", role="eye", pri=1.3)
        H.prim("EyeShine" + nm, "Head", "Ellipsoid", (0.025, 0.025, 0.02), (0.12 * sx, 2.05, -0.69), col="shine", mat="hard", role="shine", pri=2.2)
    H.prim("Smile", "Head", "Block", (0.12, 0.015, 0.02), (0, 1.78, -0.98), rot=(0, 0, 0), col="black", mat="hard", role="mouth", pri=2.0)
    tl = U(sausage((0, 1.35, 0.55), (0, 1.6, 0.75), 0.11), sphere(0.2, (0, 1.75, 0.85)))
    H.piece("TailP", "Tail", tl, tris=700, role="tail", **lat)
    for nm, (x, z) in legs.items():
        lg = sausage((x, 1.12, z), (x * 1.15, 0.13, z - 0.03), 0.12)
        H.piece("Leg" + nm + "P", "Leg" + nm, lg, tris=500, role="foot", **lat)
    shine = [("ShineB", "Body", (0.1, 1.42, 0.25), (0.06, 0.05, 0.3)), ("ShineH", "Head", (0.08, 2.1, -0.55), (0.06, 0.06, 0.06)),
             ("ShineT", "Tail", (0.08, 1.88, 0.8), (0.06, 0.06, 0.06))]
    for n_, b_, c_, s_ in shine:
        H.prim(n_, b_, "Ellipsoid", s_, c_, col="white", mat="hard", role="shine", pri=2.4, tr=0.25)
    H.socket("mouth", (0, 1.86, -1.15), "Head")
    H.socket("head", (0, 2.3, -0.5), "Head")
    H.rig.update({"head": "Head", "tail": ["Tail"],
                  "legs": [{"hip": "Leg" + n, "knee": "Leg" + n, "phase": ph, "side": 1 if n[1] == "R" else -1} for n, ph in (("FR", 0.0), ("BL", 0.0), ("FL", 0.5), ("BR", 0.5))]})

    def idle(t):
        u = t / 2.0
        p = {}
        add(p, "Body", (0, 0.04 * abs(math.sin(TAU * u)), 0, 0.02 * math.sin(TAU * u), 0, 0.03 * math.sin(TAU * u * 0.5)))
        add(p, "Head", (0, 0, 0, 0.1 * math.sin(TAU * u + 0.5), 0.25 * math.sin(TAU * u * 0.5), 0.15 * math.sin(TAU * u * 0.5 + 1)))
        add(p, "Tail", (0, 0, 0, 0, 0.45 * math.sin(TAU * u * 2), 0.2 * math.sin(TAU * u * 2)))
        return p

    def move(t):
        u = t / 0.5
        ph = TAU * u
        p = {}
        add(p, "Body", (0, 0.2 * abs(math.sin(ph)), 0, 0.08 * math.sin(ph), 0, 0.05 * math.sin(ph)))
        add(p, "Neck", (0, 0, 0, -0.1 * math.sin(ph), 0, 0))
        add(p, "Head", (0, 0, 0, 0.12 * math.sin(ph + 0.5), 0, 0))
        add(p, "Tail", (0, 0, 0, 0.3 * math.sin(ph), 0.4 * math.sin(ph * 2), 0))
        for nm, off in (("FR", 0), ("BL", 0), ("FL", math.pi), ("BR", math.pi)):
            add(p, "Leg" + nm, (0, 0, 0, 0.55 * math.sin(ph + off), 0, 0))
        return p

    def attack(t):
        s = t / 0.8
        w, st, rec = env(s, 0.4, (0.35, 0.8))
        p = {}
        add(p, "Body", (0, -0.1 * w + 0.4 * st, 0.15 * w - 0.6 * st, 0.25 * w - 0.35 * st, 0, 0))
        add(p, "Neck", (0, 0, 0, 0.3 * w - 0.6 * st, 0, 0))
        add(p, "Head", (0, 0, 0, 0.2 * w - 0.3 * st, 0, 0))
        for nm in ("FR", "FL"):
            add(p, "Leg" + nm, (0, 0, 0, -0.5 * w + 0.8 * st, 0, 0))
        for nm in ("BR", "BL"):
            add(p, "Leg" + nm, (0, 0, 0, 0.3 * w - 0.7 * st, 0, 0))
        add(p, "Tail", (0, 0, 0, 0.5 * st, 0, 0))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, 0.15 * k, 0.25 * k, 0.25 * k, 0, 0.2 * math.sin(t * 50) * k))
        add(p, "Head", (0, 0, 0, 0.4 * k, 0, 0.3 * k))
        return p

    clips(H, idle, move, attack, hit, 2.2, idle_len=2.0, move_len=0.5, attack_len=0.8)
    return H


# ================================================================================================ pet rock
@hero("pet rock", "objects")
def pet_rock():
    """A smooth river pebble (speckled granite) with two big googly eyes whose loose pupils jiggle, a little screw
    eye on top and a tiny red leash trailing behind to a loop handle. Scoots in little hops; bonks by tumbling."""
    H = OH("pet rock", plan="Blob", gait="hop", tags=["object", "rock", "toy"])
    H.preview = {"primary": "#9A948A", "secondary": "#D9372B"}
    H.body((0, 0.45, 0))
    H.bone("Rock", "Body", (0, 0.5, 0))
    H.bone("PupilR", "Rock", (0.27, 0.78, -0.58))
    H.bone("PupilL", "Rock", (-0.27, 0.78, -0.58))
    H.bone("Leash", "Rock", (0, 1.02, 0.2))
    H.bone("Handle", "Leash", (0, 0.1, 1.6))
    rk = ellipsoid(0.82, 0.52, 0.7, (0, 0.52, 0)).su(ellipsoid(0.55, 0.3, 0.45, (0.12, 0.85, 0.08)), 0.3)
    rk = (rk & plane((0, -1, 0), -0.03)).noise(0.025, 3.5, 5)
    gran = combine(spots(0.12, 0.035, depth=0.4, seed=2), spots(0.2, 0.05, depth=-0.25, seed=5))
    H.piece("Pebble", "Rock", rk, col="primary", mat="stone", tris=1600, res=128, pattern=gran)
    for sx, nm in ((1, "R"), (-1, "L")):
        n = A(0.25 * sx, 0.35, -1.0)
        googly(H, nm, "Rock", (0.27 * sx, 0.8, -0.56), 0.17, n=T(n), pupil_bone="Pupil" + nm)
        H.prim("Rim" + nm, "Rock", "Cylinder", (0.06, 0.37, 0.37), (0.27 * sx, 0.8, -0.535), rot=(0, math.atan2(-n[0], -n[2]) + math.pi / 2, 0),
               col="white", mat="glass", role="eye", pri=1.6, tr=0.4)
    hook = U(cylinder(0.025, 0.05).at(0, 1.02, 0.2), torus(0.06, 0.018, axis=0).at(0, 1.12, 0.2))
    H.piece("Hook", "Rock", hook, col="steel", mat="metal", tris=200, role="detail", pri=1.7)
    lead = tube([(0, 1.12, 0.22), (0, 1.25, 0.6), (0, 0.85, 1.05), (0, 0.25, 1.4), (0, 0.06, 1.62)], [0.03, 0.03, 0.03, 0.03, 0.03], k=0.04)
    H.piece("LeashP", "Leash", lead, col="secondary", mat="cloth", tris=400, role="tail", pri=1.4)
    hl = torus(0.15, 0.03).at(0, 0.035, 1.75)
    H.piece("HandleP", "Handle", hl, col="secondary", mat="cloth", tris=250, role="tail", pri=1.6)
    H.socket("mouth", (0, 0.6, -0.75), "Rock")
    H.socket("head", (0, 1.2, 0), "Rock")
    H.rig.update({"head": "Rock", "tail": ["Leash"]})

    def jig(p, u, amt):
        for nm, ph in (("PupilR", 0.0), ("PupilL", 1.9)):
            add(p, nm, (0.04 * amt * math.sin(TAU * u * 3 + ph), 0.05 * amt * math.cos(TAU * u * 2 + ph * 1.3), 0, 0, 0, 0))

    def idle(t):
        u = t / 3.0
        p = {}
        add(p, "Rock", (0, 0, 0, 0.02 * math.sin(TAU * u), 0.08 * math.sin(TAU * u * 0.5), 0.03 * math.sin(TAU * u * 2) * max(0, math.sin(TAU * u))))
        jig(p, u, 0.6)
        add(p, "Leash", (0, 0, 0, 0.03 * math.sin(TAU * u), 0.05 * math.sin(TAU * u * 0.5), 0))
        return p

    def move(t):
        u = t / 0.5
        ph = TAU * u
        air = max(0.0, math.sin(ph))
        p = {}
        add(p, "Body", (0, 0.3 * air, 0, -0.15 * air, 0, 0.08 * math.sin(ph * 0.5)))
        add(p, "Rock", (0, 0, 0, 0.08 * max(0.0, -math.sin(ph)), 0, 0))
        jig(p, u, 1.5)
        add(p, "PupilR", (0, -0.04 * air, 0, 0, 0, 0))
        add(p, "PupilL", (0, -0.04 * air, 0, 0, 0, 0))
        add(p, "Leash", (0, 0, 0, 0.12 * air, 0, 0))
        return p

    def attack(t):
        s = t / 0.9
        w, st, rec = env(s, 0.35, (0.3, 0.85))
        p = {}
        add(p, "Body", (0, 0.4 * w + 0.15 * st, 0.2 * w - 0.7 * st, 0.35 * w - 1.6 * st, 0, 0))
        jig(p, s, 2.0)
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, 0.1 * k, 0.2 * k, 0.2 * k, 0, 0.15 * math.sin(t * 45) * k))
        jig(p, t * 3, 2.5 * k)
        return p

    clips(H, idle, move, attack, hit, 1.2, idle_len=3.0, move_len=0.5, attack_len=0.9)
    return H


# ================================================================================================ slinky
@hero("slinky", "objects")
def slinky():
    """A coiled metal spring toy standing on end: a stack of tilted rings (the coil) split over a chain of bones so
    it can bend, squash and stretch, with two cartoon eyes peeking over the top coil. Walks by arching over itself,
    wobbles when idle, stretches up tall and whips down as its attack."""
    H = OH("slinky", plan="Blob", gait="inch", tags=["object", "toy", "spring"])
    H.preview = {"primary": "#C9D2DB", "secondary": "#38BDF8"}
    H.body((0, 0.05, 0))
    seg = ["Seg1", "Seg2", "Seg3", "Seg4", "Top"]
    ys = [0.0, 0.34, 0.68, 1.02, 1.36, 1.7]
    prev = "Body"
    for i, nm in enumerate(seg):
        H.bone(nm, prev, (0, ys[i + 1] - 0.02, 0))
        prev = nm
    coil = dict(col="primary", mat="metal")
    H.piece("Coil0", "Body", helix_rings((0, 0), 0.55, 0.042, 0.02, ys[1] - 0.02, 3, axis_tilt=6, flat=False), tris=1100, res=140, smooth=3, ao=False, **coil)
    for i, nm in enumerate(seg):
        rings = helix_rings((0, 0), 0.55, 0.042, ys[i + 1] - 0.02, ys[i + 2] - 0.02 if i + 2 < len(ys) else ys[-1] + 0.3, 3, axis_tilt=6, flat=False)
        H.piece("Coil" + str(i + 1), nm, rings, tris=1100, res=140, smooth=3, ao=False, role="head" if nm == "Top" else "body", **coil)
    for sx, nm in ((1, "R"), (-1, "L")):
        H.prim("Eye" + nm, "Top", "Ellipsoid", (0.3, 0.34, 0.3), (0.17 * sx, 2.08, -0.3), col="eyeWhite", mat="hard", role="eye", pri=1.2)
        H.prim("Pupil" + nm, "Top", "Ellipsoid", (0.15, 0.17, 0.12), (0.17 * sx, 2.08, -0.43), col="pupil", mat="hard", role="pupil", pri=1.3)
        H.prim("Shine" + nm, "Top", "Ellipsoid", (0.06, 0.06, 0.05), (0.2 * sx, 2.14, -0.48), col="shine", mat="hard", role="shine", pri=2.2)
    H.socket("mouth", (0, 2.1, -0.6), "Top")
    H.socket("head", (0, 2.4, 0), "Top")
    H.rig.update({"head": "Top", "tail": seg[:-1]})

    def idle(t):
        u = t / 2.0
        p = {}
        for i, nm in enumerate(seg):
            add(p, nm, (0, -0.04 * (0.5 + 0.5 * math.sin(TAU * u - i * 0.5)), 0, 0.05 * math.sin(TAU * u - i * 0.6), 0, 0.06 * math.sin(TAU * u * 0.5 - i * 0.5)))
        return p

    def move(t):
        u = t / 0.9
        ph = TAU * u
        p = {}
        arch = 0.5 - 0.5 * math.cos(ph)
        for i, nm in enumerate(seg):
            add(p, nm, (0, 0.06 * arch - 0.05 * (1 - arch), 0, -0.34 * arch * (0.6 + 0.2 * i) + 0.06 * math.sin(ph * 2 - i), 0, 0))
        add(p, "Body", (0, 0.05 * max(0.0, math.sin(ph * 2)), 0, 0.1 * arch, 0, 0))
        add(p, "Top", (0, 0, 0, 0.5 * arch, 0, 0))
        return p

    def attack(t):
        s = t / 0.9
        w, st, rec = env(s, 0.4, (0.35, 0.8))
        p = {}
        for i, nm in enumerate(seg):
            add(p, nm, (0, 0.14 * w - 0.03 * st, 0, 0.08 * w - 0.38 * st, 0, 0))
        add(p, "Top", (0, 0, 0, 0.6 * st, 0, 0))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        for i, nm in enumerate(seg):
            add(p, nm, (0, -0.06 * k, 0, 0.1 * k, 0, 0.12 * math.sin(t * 40 - i) * k))
        return p

    clips(H, idle, move, attack, hit, 2.2, idle_len=2.0, move_len=0.9)
    return H


# ================================================================================================ eggs
def _egg(c, a, b, k=0.16):
    """Egg solid centred at c: radius a at the equator, half-height b, narrower toward the top by k."""
    c = np.asarray(c, float)

    def f(p):
        q = p - c
        t = np.clip(q[:, 1] / b, -1, 1)
        R = a * np.sqrt(np.maximum(1 - t * t, 0)) * (1 - k * t)
        rho = np.sqrt(q[:, 0] ** 2 + q[:, 2] ** 2)
        d_side = rho - R
        d_cap = np.abs(q[:, 1]) - b
        return np.maximum(d_side * 0.85, d_cap) if True else d_side

    return SDF(f).round(0.0)


@hero("humpty dumpty", "objects")
def humpty_dumpty():
    """The nursery-rhyme egg man: a big glossy egg with a cheerful face high up (round eyes, arched brows, a button
    nose, a wide grin), a shirt collar and a polka-dot bowtie, a belt at the 'waist', thin arms in white gloves and
    thin striped-stocking legs in buckled shoes. Waddles; attacks with a big belly bump."""
    H = OH("humpty dumpty", plan="Biped", gait="waddle", tags=["egg", "nursery"])
    H.preview = {"primary": "#F3EBDD", "secondary": "#2F5DA8", "blush": "#FF8FA3"}
    H.body((0, 0.85, 0))
    H.bone("Egg", "Body", (0, 1.15, 0))
    H.mbone("Shoulder#", "Egg", (0.8, 1.55, 0.0))
    H.mbone("Hand#", "Shoulder#", (1.12, 1.0, -0.15))
    H.mbone("Hip#", "Body", (0.3, 0.85, 0.0))
    H.mbone("Foot#", "Hip#", (0.33, 0.12, -0.05))
    eg = _egg((0, 1.95, 0), 0.88, 1.15, 0.12)
    eg = eg.ss(ellipsoid(0.16, 0.2, 0.14, (0.28, 2.32, -0.78)).mirror_x(), 0.03)
    eg = eg.su(ellipsoid(0.09, 0.08, 0.08, (0, 2.12, -0.86)), 0.05)  # button nose
    grin = ellipsoid(0.42, 0.12, 0.22, (0, 1.88, -0.82)).su(ellipsoid(0.08, 0.08, 0.2, (0.42, 1.95, -0.72)).mirror_x(), 0.05)
    eg = eg.ss(grin, 0.04)
    H.piece("Shell", "Egg", eg, col="primary", mat="plastic", tris=1800, res=128, role="head", pattern=gradient(1, 0.9, 3.0, 0.92, 1.0))
    cartoon_eye(H, "Eye#", "Egg", (0.28, 2.33, -0.72), 0.16, look=(0.15, 0.05, -1))
    H.mprim("Brow#", "Egg", "Ellipsoid", (0.24, 0.05, 0.08), (0.28, 2.6, -0.66), rot=(-0.55, 0.3, -0.2), col="hair", mat="hard", role="brow", pri=1.8)
    H.prim("MouthIn", "Egg", "Ellipsoid", (0.8, 0.2, 0.25), (0, 1.89, -0.74), col="mouth", mat="hard", role="mouth", pri=1.5)
    H.prim("Teeth", "Egg", "Ellipsoid", (0.56, 0.07, 0.18), (0, 1.94, -0.78), col="tooth", mat="hard", role="mouth", pri=1.7)
    H.mprim("Cheek#", "Egg", "Ellipsoid", (0.2, 0.12, 0.05), (0.5, 2.0, -0.66), rot=(0, -0.65, 0), col="blush", mat="hard", role="cheek", pri=2.2, tr=0.2)
    col_ = (_egg((0, 1.95, 0), 0.88, 1.15, 0.12).round(0.03) & SDF(lambda p: np.abs(p[:, 1] - 1.52) - 0.07))
    H.piece("Collar", "Egg", col_, col="white", mat="cloth", tris=700, role="detail", pri=1.3)
    belt = (_egg((0, 1.95, 0), 0.88, 1.15, 0.12).round(0.03) & SDF(lambda p: np.abs(p[:, 1] - 1.2) - 0.09))
    H.piece("Belt", "Egg", belt, col="secondary", mat="cloth", tris=700, role="detail", pri=1.3)
    H.prim("Buckle", "Egg", "Block", (0.22, 0.18, 0.05), (0, 1.2, -0.84), rot=(0.25, 0, 0), col="gold", mat="metal", role="detail", pri=1.6)
    bow = U(ellipsoid(0.2, 0.13, 0.07, (0.19, 1.55, -0.85)).rot(0, 0, 0), ellipsoid(0.2, 0.13, 0.07, (-0.19, 1.55, -0.85)), sphere(0.07, (0, 1.55, -0.88)), k=0.03)
    H.piece("Bowtie", "Egg", bow, col="red", mat="cloth", tris=500, role="detail", pri=1.4,
            pattern=spots(0.09, 0.025, depth=-0.6, seed=4))
    for sx, nm in ((1, "R"), (-1, "L")):
        sh, hn = A(0.8 * sx, 1.55, 0.0), A(1.12 * sx, 1.0, -0.15)
        H.piece("Arm" + nm, "Shoulder" + nm, capsule(T(sh), T(hn + A(0, 0.05, 0)), 0.065), col="primary", mat="plastic", tris=250, role="limb")
        gl = sphere(0.13, T(hn + A(0, -0.05, 0))).su(cylinder(0.11, 0.06).at(*T(hn + A(0, 0.08, 0))), 0.04)
        gl = gl.su(capsule(T(hn + A(-0.08 * sx, -0.02, -0.08)), T(hn + A(-0.12 * sx, 0.06, -0.12)), 0.04), 0.02)
        H.piece("Glove" + nm, "Hand" + nm, gl, col="white", mat="cloth", tris=400, role="hand")
        hp, ft = A(0.3 * sx, 0.9, 0.0), A(0.33 * sx, 0.12, -0.05)
        H.piece("Leg" + nm, "Hip" + nm, capsule(T(hp), T(ft + A(0, 0.08, 0)), 0.075), col="secondary", mat="cloth", tris=300, role="limb",
                pattern=stripes(lambda P: P[:, 1], 6.0, width=0.45, depth=0.45))
        sh_ = ellipsoid(0.15, 0.1, 0.27, T(ft + A(0, -0.02, -0.1))) & plane((0, -1, 0), 0.0)
        sh_ = sh_.su(cylinder(0.09, 0.05).at(*T(ft + A(0, 0.06, 0))), 0.04)
        H.piece("Shoe" + nm, "Foot" + nm, sh_, col="black", mat="plastic", tris=400, role="foot")
        H.prim("ShoeBuckle" + nm, "Foot" + nm, "Block", (0.12, 0.08, 0.03), T(ft + A(0, 0.06, -0.28)), rot=(0.5, 0, 0), col="gold", mat="metal", role="detail", pri=1.9)
    H.socket("mouth", (0, 1.9, -0.95), "Egg")
    H.socket("head", (0, 3.2, 0), "Egg")
    H.socket("hand", (1.12, 0.95, -0.15), "HandR")
    H.rig.update({"head": "Egg", "legs": [{"hip": "HipR", "knee": "FootR", "phase": 0.0, "side": 1}, {"hip": "HipL", "knee": "FootL", "phase": 0.5, "side": -1}],
                  "arms": [{"shoulder": "ShoulderR", "elbow": "HandR", "side": 1}, {"shoulder": "ShoulderL", "elbow": "HandL", "side": -1}]})

    def idle(t):
        u = t / 2.6
        p = {}
        add(p, "Egg", (0, 0.02 * math.sin(TAU * u * 2), 0, 0.03 * math.sin(TAU * u), 0.1 * math.sin(TAU * u * 0.5), 0.07 * math.sin(TAU * u)))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Shoulder" + nm, (0, 0, 0, 0.15 * math.sin(TAU * u + sg), 0, sg * (0.1 + 0.08 * math.sin(TAU * u * 2))))
        return p

    def move(t):
        u = t / 0.7
        ph = TAU * u
        p = {}
        add(p, "Body", (0, 0.08 * abs(math.sin(ph)), 0, 0, 0, 0))
        add(p, "Egg", (0, 0, 0, -0.08, 0.12 * math.sin(ph), 0.16 * math.sin(ph)))
        for sg, nm in ((1, "R"), (-1, "L")):
            ph2 = ph + (0 if sg > 0 else math.pi)
            add(p, "Hip" + nm, (0, 0.05 * max(0.0, math.sin(ph2)), 0, 0.55 * math.sin(ph2 + math.pi / 2), 0, 0))
            add(p, "Foot" + nm, (0, 0, 0, -0.3 * max(0.0, math.sin(ph2 + math.pi / 2)), 0, 0))
            add(p, "Shoulder" + nm, (0, 0, 0, -0.5 * math.sin(ph2 + math.pi / 2), 0, sg * 0.3))
        return p

    def attack(t):
        s = t / 0.9
        w, st, rec = env(s, 0.4, (0.35, 0.8))
        p = {}
        add(p, "Body", (0, 0.2 * st, -0.5 * st, 0, 0, 0))
        add(p, "Egg", (0, 0, 0.1 * w, 0.35 * w - 0.55 * st, 0, 0))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Shoulder" + nm, (0, 0, 0, -0.6 * w + 0.4 * st, 0, sg * (0.9 * w + 0.4 * st)))
            add(p, "Hip" + nm, (0, 0, 0, -0.25 * w + 0.4 * st, 0, 0))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Egg", (0, 0.05 * k, 0.2 * k, 0.3 * k, 0, 0.18 * math.sin(t * 40) * k))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Shoulder" + nm, (0, 0, 0, 0.4 * k, 0, sg * 1.0 * k))
        return p

    clips(H, idle, move, attack, hit, 3.2, idle_len=2.6, move_len=0.7, attack_len=0.9)
    return H


def _zig(th, base, amp, n=7):
    x = th / TAU * n
    return base + amp * (2 * np.abs(2 * (x - np.floor(x + 0.5))) - 1)


@hero("dinosaur egg", "objects")
def dinosaur_egg():
    """A big speckled dinosaur egg cracking open: the lower shell with a zig-zag broken rim, the cap lifted off on
    top, a baby dinosaur peeking out between them (round head, huge eyes, tiny teeth, little horn nub) and two clawed
    feet poking out of holes in the bottom. Rocks and peeks when idle, hops along, pops its cap to bite."""
    H = OH("dinosaur egg", plan="Blob", gait="hop", tags=["egg", "dinosaur", "baby"])
    H.preview = {"primary": "#EADFC8", "secondary": "#6CBF5A", "belly": "#D9E8A8"}
    H.body((0, 0.45, 0))
    H.bone("Shell", "Body", (0, 0.7, 0))
    H.bone("Head", "Shell", (0, 1.45, 0.0))
    H.bone("Cap", "Head", (0, 2.3, 0.0))
    H.bone("Jaw", "Head", (0, 1.75, -0.25))
    H.mbone("Foot#", "Body", (0.32, 0.3, -0.35))
    egg = _egg((0, 1.25, 0), 0.82, 1.2, 0.12)
    shell = egg - _egg((0, 1.25, 0), 0.75, 1.13, 0.12)
    zig = lambda p: _zig(np.arctan2(p[:, 0], -p[:, 2]), 1.62, 0.09)  # noqa: E731
    lower = shell & SDF(lambda p: p[:, 1] - zig(p))
    lower = lower.ss(U(sphere(0.17, (0.32, 0.2, -0.55)), sphere(0.17, (-0.32, 0.2, -0.55))), 0.02)
    speck = combine(spots(0.16, 0.045, depth=0.45, seed=21), spots(0.3, 0.08, depth=0.25, seed=22))
    H.piece("Lower", "Shell", lower, col="primary", mat="stone", tris=1800, res=136, pattern=speck)
    cap = (shell & SDF(lambda p: zig(p) + 0.02 - p[:, 1])).at(0, -2.0, 0).rot(-12, 0, 8).at(0, 2.0 + 0.55, 0.06)  # worn like a helmet
    H.piece("CapP", "Cap", cap, col="primary", mat="stone", tris=1100, res=128, role="head", pattern=speck)
    H.prim("Inside", "Shell", "Ellipsoid", (1.45, 1.5, 1.45), (0, 1.0, 0), col="darker", mat="hard", role="detail", pri=1.6)
    hc = A(0, 1.86, -0.08)
    hd = ellipsoid(0.44, 0.4, 0.42, T(hc)).su(ellipsoid(0.32, 0.22, 0.32, T(hc + A(0, -0.08, -0.3))), 0.15)
    hd = hd.su(cone(0.07, 0.0, 0.07).at(*T(hc + A(0, 0.42, -0.08))), 0.04)
    hd = hd.ss(ellipsoid(0.13, 0.15, 0.1, T(hc + A(0.2, 0.08, -0.35))).mirror_x(), 0.03)
    H.piece("HeadP", "Head", hd, col="secondary", mat="skin", tris=1100, role="head",
            pattern=spots(0.15, 0.04, depth=0.3, region=lambda P: np.clip((P[:, 1] - 1.7) / 0.2, 0, 1), seed=8))
    cartoon_eye(H, "Eye#", "Head", (0.2, 1.95, -0.37), 0.13, look=(0.2, 0.05, -1))
    H.mprim("Nostril#", "Head", "Ellipsoid", (0.04, 0.03, 0.03), (0.07, 1.82, -0.62), col="dark", mat="hard", role="nose", pri=2.1)
    jaw = ellipsoid(0.26, 0.11, 0.28, T(hc + A(0, -0.24, -0.28))) & SDF(lambda p: p[:, 1] - (hc[1] - 0.16))
    jaw = jaw | teeth_row(T(hc + A(0, -0.16, -0.5)), (1, 0, 0), 4, 0.07, 0.06, up=True)
    H.piece("JawP", "Jaw", jaw, col="belly", mat="skin", tris=500, role="jaw", pri=1.3)
    H.prim("MouthIn", "Head", "Ellipsoid", (0.42, 0.1, 0.38), T(hc + A(0, -0.17, -0.3)), col="mouth", mat="hard", role="mouth", pri=1.6)
    for sx, nm in ((1, "R"), (-1, "L")):
        f = A(0.32 * sx, 0.12, -0.6)
        ft = ellipsoid(0.13, 0.11, 0.18, T(f)) & plane((0, -1, 0), 0.0)
        for dx in (-0.07, 0.0, 0.07):
            ft = ft.su(cone(0.035, 0.0, 0.05, axis=2).rot(0, 180, 0).at(*T(f + A(dx, -0.03, -0.2))), 0.01)
        H.piece("Foot" + nm + "P", "Foot" + nm, ft, col="secondary", mat="skin", tris=400, role="foot")
    H.socket("mouth", T(hc + A(0, -0.15, -0.55)), "Head")
    H.socket("head", (0, 2.7, 0), "Cap")
    H.rig.update({"head": "Head", "jaw": "Jaw"})

    def idle(t):
        u = t / 3.0
        p = {}
        rock = math.sin(TAU * u)
        add(p, "Shell", (0, 0, 0, 0.03 * math.sin(TAU * u * 2), 0, 0.08 * rock))
        peek = ease((math.sin(TAU * u) + 0.2) * 1.4)
        add(p, "Cap", (0, 0.03 * peek, 0, -0.1 * peek, 0, 0.06 * rock))
        add(p, "Head", (0, -0.12 + 0.12 * peek, 0, 0.04 * math.sin(TAU * u * 2), 0.4 * math.sin(TAU * u * 0.5), 0))
        add(p, "Jaw", (0, 0, 0, 0.25 * max(0.0, math.sin(TAU * u * 3)) * peek, 0, 0))
        return p

    def move(t):
        u = t / 0.6
        ph = TAU * u
        air = max(0.0, math.sin(ph))
        p = {}
        add(p, "Body", (0, 0.35 * air, 0, -0.08 * math.cos(ph), 0, 0.1 * math.sin(ph * 0.5)))
        add(p, "Cap", (0, 0.08 * air, 0, -0.15 * air, 0, 0.08 * math.sin(ph)))
        add(p, "Head", (0, 0, 0, -0.1 * math.cos(ph - 0.5), 0, 0))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Foot" + nm, (0, -0.05 * air, 0, 0.5 * air, 0, sg * 0.15 * air))
        return p

    def attack(t):
        s = t / 0.9
        w, st, rec = env(s, 0.4, (0.35, 0.8))
        p = {}
        add(p, "Shell", (0, 0, 0.1 * w - 0.2 * st, 0.15 * w - 0.25 * st, 0, 0))
        add(p, "Cap", (0, 0.4 * st, 0.2 * st, -0.7 * st, 0, 0.3 * st))
        add(p, "Head", (0, 0.1 * w + 0.35 * st, -0.35 * st, 0.2 * w - 0.25 * st, 0, 0))
        add(p, "Jaw", (0, 0, 0, 0.7 * w + 0.4 * st - 0.9 * bump(s, 0.55, 0.75), 0, 0))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Shell", (0, 0, 0.15 * k, 0.25 * k, 0, 0.15 * math.sin(t * 40) * k))
        add(p, "Cap", (0, 0.15 * k, 0, 0.3 * k, 0, 0.2 * k))
        add(p, "Head", (0, -0.25 * k, 0, 0, 0, 0))
        return p

    clips(H, idle, move, attack, hit, 2.6, idle_len=3.0, move_len=0.6, attack_len=0.9)
    return H


# ================================================================================================ floating eye
@hero("floating eye", "objects")
def floating_eye():
    """A giant floating eyeball: a wet white sclera laced with red veins, a big coloured iris under a glassy cornea,
    fleshy upper and lower lids that blink, four wriggling eyestalks each ending in a little eye, and a trailing
    optic-nerve bundle behind. Hovers, looks around, blinks; its attack is a wide-eyed glare lunge."""
    H = OH("floating eye", plan="Orb", gait="hover", tags=["eye", "aberration"])
    H.preview = {"primary": "#8E4A7A", "secondary": "#C8456B", "iris": "#2BB3A6"}
    c = A(0, 2.2, 0)
    R = 0.92
    H.body(T(c))
    H.bone("Orb", "Body", T(c))
    H.bone("LidU", "Body", T(c))
    H.bone("LidD", "Body", T(c))
    H.bone("Nerve1", "Body", T(c + A(0, -0.2, 0.85)))
    H.bone("Nerve2", "Nerve1", T(c + A(0, -0.55, 1.5)))
    stalks = []
    for i, (az, el) in enumerate(((0.55, 1.0), (-0.55, 1.0), (1.6, 0.65), (-1.6, 0.65))):
        d = A(math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el) * 0.6 + 0.25)
        d /= np.linalg.norm(d)
        base = c + d * (R * 0.95)
        mid = base + d * 0.45 + A(0, 0.2, 0)
        tip = mid + d * 0.35 + A(0, 0.25, -0.1)
        a_, b_ = f"Stalk{i + 1}a", f"Stalk{i + 1}b"
        H.bone(a_, "Body", T(base))
        H.bone(b_, a_, T(mid))
        stalks.append((a_, b_, base, mid, tip, i))
    sc = sphere(R, T(c))
    H.piece("Sclera", "Orb", sc, col="eyeWhite", mat="plastic", tris=1400, res=120, role="body",
            pattern=gradient(2, -0.5 + c[2], 0.9 + c[2], 1.0, 0.82))
    rng = np.random.default_rng(5)
    veins = None
    for k in range(9):
        a0 = rng.uniform(-math.pi, math.pi)
        e0 = rng.uniform(-0.6, 0.6)
        pts, rr = [], []
        for j in range(5):
            th = a0 + rng.uniform(-0.25, 0.25) * j
            el = e0 + rng.uniform(-0.15, 0.15) * j
            z = 0.75 - 0.32 * j
            v = A(math.cos(th) * math.cos(el), math.sin(el), 0) * math.sqrt(max(0.0, 1 - z * z)) / max(1e-3, math.cos(el)) * math.cos(el)
            v = A(v[0], v[1], -z)
            v /= np.linalg.norm(v)
            pts.append(T(c + v * (R + 0.005)))
            rr.append(0.022 - 0.003 * j)
        veins = U(veins, tube(pts, rr))
    H.piece("Veins", "Orb", veins, col="red", mat="skin", tris=900, role="detail", pri=1.4)
    H.prim("Iris", "Orb", "Ellipsoid", (0.92, 0.92, 0.24), T(c + A(0, 0, -0.83)), col="iris", mat="hard", role="eye", pri=1.1)
    H.prim("IrisRing", "Orb", "Ellipsoid", (0.98, 0.98, 0.2), T(c + A(0, 0, -0.815)), col="darker", mat="hard", role="eye", pri=1.15)
    H.prim("Pupil", "Orb", "Ellipsoid", (0.4, 0.4, 0.14), T(c + A(0, 0, -0.93)), col="pupil", mat="hard", role="pupil", pri=1.2)
    H.prim("Cornea", "Orb", "Ellipsoid", (1.02, 1.02, 0.36), T(c + A(0, 0, -0.84)), col="white", mat="glass", tr=0.7, role="eye", pri=1.6)
    H.prim("Shine", "Orb", "Ellipsoid", (0.16, 0.16, 0.06), T(c + A(0.2, 0.22, -0.98)), col="shine", mat="hard", role="shine", pri=2.0)
    nu = A(0, 0.85, 0.53)
    lid = sphere(R + 0.07, T(c)).shell(0.035) & SDF(lambda p: 0.08 - (p - c) @ (nu / np.linalg.norm(nu)))
    lid = lid.su(torus(R * 0.78, 0.06, axis=1).rot(-58, 0, 0).at(*T(c)) & SDF(lambda p: 0.15 - (p - c) @ (nu / np.linalg.norm(nu))), 0.02) if False else lid
    H.piece("LidUP", "LidU", lid, col="primary", mat="skin", tris=1100, role="lid", pri=1.05)
    nd = A(0, -0.85, 0.53)
    lidd = sphere(R + 0.06, T(c)).shell(0.03) & SDF(lambda p: 0.3 - (p - c) @ (nd / np.linalg.norm(nd)))
    H.piece("LidDP", "LidD", lidd, col="primary", mat="skin", tris=800, role="lid", pri=1.05)
    for a_, b_, base, mid, tip, i in stalks:
        st = tube([T(base - (mid - base) * 0.15), T(base + (mid - base) * 0.5), T(mid)], [0.11, 0.08, 0.07], k=0.03)
        H.piece(f"Stalk{i + 1}P", a_, st, col="primary", mat="skin", tris=300, role="limb", pri=1.6)
        st2 = tube([T(mid), T(mid + (tip - mid) * 0.6), T(tip)], [0.07, 0.065, 0.1], k=0.03)
        H.piece(f"Stalk{i + 1}Q", b_, st2, col="primary", mat="skin", tris=300, role="limb", pri=1.6)
        H.prim(f"MiniEye{i + 1}", b_, "Ball", (0.2, 0.2, 0.2), T(tip + A(0, 0.03, -0.05)), col="eyeWhite", mat="hard", role="eye", pri=1.7)
        H.prim(f"MiniPupil{i + 1}", b_, "Ellipsoid", (0.09, 0.09, 0.06), T(tip + A(0, 0.03, -0.14)), col="pupil", mat="hard", role="pupil", pri=1.8)
    nv = U(tube([T(c + A(0, -0.15, 0.82)), T(c + A(0, -0.3, 1.2)), T(c + A(0, -0.55, 1.5))], [0.2, 0.14, 0.11], k=0.04))
    H.piece("NerveA", "Nerve1", nv, col="secondary", mat="skin", tris=500, role="tail", pri=1.4)
    nv2 = U(*(tube([T(c + A(0, -0.55, 1.5)), T(c + A(0.15 * sx, -0.8, 1.85)), T(c + A(0.25 * sx, -1.15, 2.0))], [0.1, 0.06, 0.02], k=0.03) for sx in (1, -1)),
            tube([T(c + A(0, -0.55, 1.5)), T(c + A(0, -0.65, 1.95)), T(c + A(0, -0.75, 2.25))], [0.1, 0.06, 0.02], k=0.03))
    H.piece("NerveB", "Nerve2", nv2, col="secondary", mat="skin", tris=600, role="tail", pri=1.5)
    H.socket("mouth", T(c + A(0, 0, -1.0)), "Orb")
    H.socket("head", T(c + A(0, 1.4, 0)), "Body")
    H.rig.update({"head": "Orb", "tail": ["Nerve1", "Nerve2"]})
    sts = [(s_[0], s_[1], s_[5]) for s_ in stalks]

    def blink(u, at, w=0.06):
        return bump(u % 1.0, at - w, at + w)

    def wriggle(p, u, amt=1.0):
        for a_, b_, i in sts:
            add(p, a_, (0, 0, 0, 0.18 * amt * math.sin(TAU * u * 2 + i * 1.7), 0, 0.2 * amt * math.sin(TAU * u + i * 2.3)))
            add(p, b_, (0, 0, 0, 0.3 * amt * math.sin(TAU * u * 2 + i * 1.7 - 1.0), 0, 0.3 * amt * math.sin(TAU * u + i * 2.3 - 1.2)))

    def idle(t):
        u = t / 3.2
        p = {}
        add(p, "Body", (0, 0.12 * math.sin(TAU * u), 0, 0, 0, 0.04 * math.sin(TAU * u * 0.5)))
        add(p, "Orb", (0, 0, 0, 0.18 * math.sin(TAU * u * 0.5 + 1.3), 0.45 * math.sin(TAU * u * 0.5), 0))
        b = blink(u, 0.3) + blink(u, 0.82)
        add(p, "LidU", (0, 0, 0, -1.05 * b, 0, 0))
        add(p, "LidD", (0, 0, 0, 0.45 * b, 0, 0))
        add(p, "Nerve1", (0, 0, 0, 0.12 * math.sin(TAU * u), 0.15 * math.sin(TAU * u * 0.5), 0))
        add(p, "Nerve2", (0, 0, 0, 0.2 * math.sin(TAU * u - 1), 0.25 * math.sin(TAU * u * 0.5 - 1), 0))
        wriggle(p, u)
        return p

    def move(t):
        u = t / 1.2
        p = {}
        add(p, "Body", (0, 0.08 * math.sin(TAU * u * 2), 0, -0.25, 0.05 * math.sin(TAU * u), 0.06 * math.sin(TAU * u)))
        add(p, "Orb", (0, 0, 0, 0.2, 0, 0))
        add(p, "LidU", (0, 0, 0, -0.2, 0, 0))
        add(p, "Nerve1", (0, 0, 0, 0.3 + 0.15 * math.sin(TAU * u * 2), 0.2 * math.sin(TAU * u), 0))
        add(p, "Nerve2", (0, 0, 0, 0.3 + 0.25 * math.sin(TAU * u * 2 - 1), 0.3 * math.sin(TAU * u - 1), 0))
        wriggle(p, u * 1.5, 0.8)
        for a_, b_, i in sts:
            add(p, a_, (0, 0, 0, 0.35, 0, 0))
        return p

    def attack(t):
        s = t / 0.9
        w, st, rec = env(s, 0.4, (0.35, 0.8))
        p = {}
        add(p, "Body", (0, 0.2 * w, 0.3 * w - 0.6 * st, 0.15 * w - 0.2 * st, 0, 0))
        add(p, "LidU", (0, 0, 0, -0.6 * w + 0.35 * st, 0, 0))
        add(p, "LidD", (0, 0, 0, 0.3 * w - 0.25 * st, 0, 0))
        for a_, b_, i in sts:
            add(p, a_, (0, 0, 0, 0.4 * w - 0.9 * st, 0, 0))
            add(p, b_, (0, 0, 0, -0.4 * st, 0, 0))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, 0.1 * k, 0.3 * k, 0.3 * k, 0, 0.2 * math.sin(t * 40) * k))
        add(p, "LidU", (0, 0, 0, -1.1 * k, 0, 0))
        add(p, "LidD", (0, 0, 0, 0.45 * k, 0, 0))
        wriggle(p, t * 4, 2 * k)
        return p

    clips(H, idle, move, attack, hit, 3.4, idle_len=3.2, move_len=1.2, attack_len=0.9)
    return H


# ================================================================================================ brain alien
def _brain(c, rx, ry, rz):
    c = np.asarray(c, float)

    def f(p):
        q = (p - c) / np.array([rx, ry, rz])
        r = np.linalg.norm(q, axis=1)
        d = (r - 1.0) * min(rx, ry, rz)
        x, y, z = p[:, 0] * 9, p[:, 1] * 9, p[:, 2] * 9
        g = np.sin(x + 2.4 * np.sin(y * 0.8)) + np.sin(y + 2.4 * np.sin(z * 0.8)) + np.sin(z + 2.4 * np.sin(x * 0.8))
        d = d + 0.05 * np.exp(-(g / 0.45) ** 2) * np.clip(1.2 - np.abs(r - 1) * 4, 0, 1)
        d = np.maximum(d, -(np.abs(p[:, 0] - c[0]) - 0.035) * np.clip((p[:, 1] - c[1] + ry * 0.2) * 4, 0, 1) - 0.0)  # midline fissure
        return d

    return SDF(f)


@hero("brain alien", "objects")
def brain_alien():
    """A giant wrinkled brain floating in a glass dome: deep folds and a midline fissure, a pulsing glow underneath,
    a chunky chrome collar ring set with blinking lights and a visor of two glowing eyes, a domed machine housing
    below, and four dangling tentacles that curl and lash. Hovers; its attack is a psychic lunge with tentacles."""
    H = OH("brain alien", plan="Orb", gait="hover", tags=["alien", "brain"])
    H.preview = {"primary": "#E98AA6", "secondary": "#5EEAD4", "chrome": "#C9D2DB"}
    H.body((0, 1.8, 0))
    H.bone("Brain", "Body", (0, 2.3, 0))
    H.bone("Dome", "Body", (0, 2.3, 0))
    tents = []
    for nm, (x, z) in (("TentFR", (0.4, -0.4)), ("TentFL", (-0.4, -0.4)), ("TentBR", (0.4, 0.4)), ("TentBL", (-0.4, 0.4))):
        H.bone(nm + "1", "Body", (x, 1.3, z))
        H.bone(nm + "2", nm + "1", (x * 1.5, 0.75, z * 1.5))
        tents.append((nm, x, z))
    br = _brain((0, 2.3, 0.0), 0.78, 0.62, 0.9)
    H.piece("BrainP", "Brain", br, col="primary", mat="skin", tris=2000, res=150, role="head",
            pattern=gradient(1, 1.8, 2.9, 0.75, 1.0))
    H.prim("Stem", "Brain", "Cylinder", (0.4, 0.3, 0.3), (0, 1.8, 0.1), rot=(0, 0, math.pi / 2), col="secondary", mat="hard", glow=True, role="core", pri=1.4)
    dome = sphere(1.08, (0, 2.08, 0)).shell(0.025) & plane((0, -1, 0), -1.9)
    H.piece("DomeP", "Dome", dome, col="glass", mat="glass", tr=0.72, tris=1000, role="shell", pri=1.5)
    col = U(torus(1.06, 0.12).at(0, 1.88, 0), cylinder(1.1, 0.12, rr=0.05).at(0, 1.78, 0), k=0.04)
    col = col.ss(U(*(sphere(0.07, (1.18 * math.sin(a), 1.8, 1.18 * math.cos(a))) for a in np.linspace(0, TAU, 12, endpoint=False))), 0.01)
    H.piece("Collar", "Body", col, col="chrome", mat="metal", tris=1000, role="body", pri=1.1)
    hous = (ellipsoid(1.0, 0.55, 1.0, (0, 1.65, 0)) & plane((0, 1, 0), 1.7)).su(cylinder(0.35, 0.15, rr=0.05).at(0, 1.1, 0), 0.15)
    hous = hous.ss(torus(0.75, 0.025).at(0, 1.45, 0), 0.01)
    H.piece("Housing", "Body", hous, col="gunmetal", mat="metal", tris=1000, role="body", pri=1.1)
    for i, a in enumerate(np.linspace(0, TAU, 8, endpoint=False)):
        if abs(math.sin(a)) < 0.2 and math.cos(a) < 0:
            continue
        H.prim(f"Light{i}", "Body", "Ball", (0.1, 0.1, 0.1), (1.17 * math.sin(a + 0.26), 1.8, 1.17 * math.cos(a + 0.26)), col="secondary", mat="hard", glow=True, role="light", pri=2.0)
    H.prim("Visor", "Body", "Block", (0.72, 0.18, 0.06), (0, 1.8, -1.12), col="black", mat="glass", role="face", pri=1.3)
    for sx, nm in ((1, "R"), (-1, "L")):
        H.prim("Eye" + nm, "Body", "Ellipsoid", (0.2, 0.1, 0.05), (0.17 * sx, 1.8, -1.16), col="glow", mat="hard", glow=True, role="eye", pri=1.4)
    for nm, x, z in tents:
        a1, a2 = A(x, 1.3, z), A(x * 1.5, 0.75, z * 1.5)
        tip = A(x * 1.9, 0.25, z * 1.9) + A(0.05 * np.sign(x), 0, -0.1)
        H.piece(nm + "P1", nm + "1", tube([T(a1 + A(0, 0.15, 0)), T((a1 + a2) / 2 + A(0, 0, 0)), T(a2)], [0.13, 0.11, 0.09], k=0.03),
                col="primary", mat="skin", tris=350, role="limb", pri=1.5)
        H.piece(nm + "P2", nm + "2", tube([T(a2), T((a2 + tip) / 2 + A(0, 0.02, 0)), T(tip), T(tip + A(-0.08 * np.sign(x), 0.1, 0.0))], [0.09, 0.07, 0.04, 0.02], k=0.02),
                col="primary", mat="skin", tris=350, role="limb", pri=1.6)
    H.socket("mouth", (0, 2.3, -1.0), "Brain")
    H.socket("head", (0, 3.3, 0), "Dome")
    H.socket("core", (0, 2.3, 0), "Brain")
    H.rig.update({"head": "Brain", "tail": [t[0] + "1" for t in tents]})

    def tent(p, u, amt=1.0, lash=0.0):
        for i, (nm, x, z) in enumerate(tents):
            sx, sz = np.sign(x), np.sign(z)
            add(p, nm + "1", (0, 0, 0, -sz * (0.15 * amt * math.sin(TAU * u + i * 1.3) + lash * 0.6), 0, sx * (0.15 * amt * math.sin(TAU * u + i * 1.9) + lash * 0.3)))
            add(p, nm + "2", (0, 0, 0, -sz * 0.3 * amt * math.sin(TAU * u + i * 1.3 - 1.1), 0, sx * 0.3 * amt * math.sin(TAU * u + i * 1.9 - 1.2)))

    def idle(t):
        u = t / 3.0
        p = {}
        add(p, "Body", (0, 0.12 * math.sin(TAU * u), 0, 0.02 * math.sin(TAU * u * 0.5), 0.15 * math.sin(TAU * u * 0.5), 0.03 * math.sin(TAU * u)))
        add(p, "Brain", (0, 0.03 * math.sin(TAU * u * 2), 0, 0.03 * math.sin(TAU * u * 2 + 1), 0, 0))
        tent(p, u)
        return p

    def move(t):
        u = t / 1.2
        p = {}
        add(p, "Body", (0, 0.08 * math.sin(TAU * u * 2), 0, -0.2, 0.05 * math.sin(TAU * u), 0.06 * math.sin(TAU * u)))
        add(p, "Brain", (0, 0, 0.04, 0, 0, 0))
        tent(p, u * 2, 0.8, lash=-0.5)
        return p

    def attack(t):
        s = t / 1.0
        w, st, rec = env(s, 0.4, (0.35, 0.85))
        p = {}
        add(p, "Body", (0, 0.35 * w, 0.2 * w - 0.6 * st, 0.25 * w - 0.25 * st, 0, 0))
        add(p, "Brain", (0, 0.08 * math.sin(TAU * s * 6) * (w + st), 0, 0, 0, 0))
        tent(p, s * 3, 0.6, lash=-0.6 * w + 1.2 * st)
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, 0.1 * k, 0.3 * k, 0.3 * k, 0, 0.2 * math.sin(t * 40) * k))
        add(p, "Brain", (0, -0.1 * k, 0.05 * k, 0, 0, 0))
        tent(p, t * 4, 2 * k)
        return p

    clips(H, idle, move, attack, hit, 3.3, idle_len=3.0, move_len=1.2, attack_len=1.0)
    return H
