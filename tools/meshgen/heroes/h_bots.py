"""Robot critters and walking machines: robot vacuum (+ robot vacuum monster), mine bot, robot ball, combat drone,
repair drone, alien tripod, robot arm monster and the chicken-legged hut.

Distinct from the constructs family (golems, the boxy tin robot, the android) and the spider walker: these are small
household / utility machines with personality (LED faces, scanning turrets, spinning brushes and rotors, blinking
warning lights) and two big walkers (a three-legged alien war machine with a heat-ray arm, a hut striding on giant
scaly chicken legs). Rotors, wheels and brushes spin on their own bones in every clip.
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from sdf import SDF
from kit import hero, stripes, spots, gradient, combine
from objkit import T, A, U, TAU, OH, add, ease, bump, env, scaled, hitk, clips, spin, cartoon_eye, led_eye, teeth_row

MACH = {"cat": ["Machine", "Creature", "Object"]}


def _hazard(axis_fn, freq=4.0, depth=0.85, region=None):
    return stripes(axis_fn, freq, width=0.5, depth=depth, region=region)


# ================================================================================================ robot vacuum
def _vacuum(hid, monster):
    """Round robot vacuum puck: a domed lid with a seam groove and a dust-bin hatch, a rubber front bumper, a
    scanning lidar turret, two spinning corner brushes, side wheels, a dark display with LED eyes.
    monster=True: angry slanted red LED eyes and a jagged LED grin, saw-blade brushes, a row of steel teeth in
    the intake, bumper studs and a chipped lid; its attack is a full 360 spin."""
    H = OH(hid, plan="Blob", gait="drive", tags=["robot", "machine", "appliance"] + (["monster"] if monster else []))
    H.preview = ({"primary": "#E8EBEF", "secondary": "#22D3EE"} if not monster else {"primary": "#2E3238", "secondary": "#EF4444"}) | {"rubber": "#2A2C31", "chrome": "#D5DCE3"}
    H.body((0, 0.27, 0))
    H.bone("Turret", "Body", (0, 0.5, 0.38))
    H.bone("Eyes", "Body", (0, 0.45, -0.55))
    H.mbone("Brush#", "Body", (0.62, 0.07, -0.62))
    H.mbone("Wheel#", "Body", (0.84, 0.14, 0.05))
    sh = cylinder(1.0, 0.16, rr=0.09).at(0, 0.27, 0).su(ellipsoid(0.92, 0.12, 0.92, (0, 0.38, 0.02)), 0.08)
    sh = sh.ss(torus(0.72, 0.018).at(0, 0.48, 0.05), 0.01)
    sh = sh.ss(round_box(0.42, 0.04, 0.2, 0.03, (0, 0.5, 0.62)), 0.01)  # bin hatch seam
    sh = sh.ss(cylinder(0.11, 0.05).at(0, 0.5, -0.05), 0.01)
    if monster:
        sh = sh.ss(sphere(0.18, (0.7, 0.48, 0.45)), 0.03).ss(sphere(0.12, (-0.55, 0.45, 0.6)), 0.03)  # dents
    H.piece("Shell", "Body", sh & plane((0, -1, 0), -0.1), col="primary", mat="plastic", tris=1500, res=128, role="body")
    H.prim("Button", "Body", "Cylinder", (0.06, 0.18, 0.18), (0, 0.48, -0.05), rot=(0, 0, math.pi / 2), col="secondary", mat="hard", glow=True, role="light", pri=1.9)
    bump_ = (cylinder(1.05, 0.11, rr=0.05).at(0, 0.24, 0) - cylinder(0.97, 0.3).at(0, 0.24, 0)) & SDF(lambda p: p[:, 2] - 0.15)
    if monster:
        for a in np.linspace(-1.2, 1.2, 7):
            bump_ = bump_ | cone(0.06, 0.0, 0.06, axis=2).rot(0, 180, 0).rot(0, math.degrees(a), 0).at(1.06 * math.sin(a), 0.24, -1.06 * math.cos(a) - 0.0)
    H.piece("Bumper", "Body", bump_, col="rubber", mat="rubber", tris=800, role="detail", pri=1.2)
    tur = cylinder(0.22, 0.06, rr=0.02).at(0, 0.5, 0.38).su(cylinder(0.18, 0.05, rr=0.03).at(0, 0.58, 0.38), 0.02)
    tur = tur.ss(round_box(0.14, 0.025, 0.08, 0.01, (0, 0.53, 0.2)), 0.005)
    H.piece("TurretP", "Turret", tur, col="gunmetal", mat="metal", tris=500, role="sensor", pri=1.3)
    H.prim("Lens", "Turret", "Block", (0.24, 0.035, 0.03), (0, 0.53, 0.18), col="secondary", mat="hard", glow=True, role="eye", pri=1.8)
    H.prim("Visor", "Body", "Ellipsoid", (1.0, 0.07, 0.42), (0, 0.45, -0.55), rot=(0.2, 0, 0), col="black", mat="glass", role="face", pri=1.1)
    if not monster:
        for sx, nm in ((1, "R"), (-1, "L")):
            led_eye(H, "Eye" + nm, "Eyes", (0.22 * sx, 0.49, -0.62), (0.18, 0.05, 0.24), rot=(0.25, 0, 0), col="secondary")
        H.prim("Smile", "Eyes", "Ellipsoid", (0.2, 0.03, 0.05), (0, 0.47, -0.76), rot=(0.25, 0, 0), col="secondary", mat="hard", glow=True, role="mouth", pri=1.8)
    else:
        for sx, nm in ((1, "R"), (-1, "L")):
            led_eye(H, "Eye" + nm, "Eyes", (0.2 * sx, 0.49, -0.6), (0.24, 0.04, 0.08), rot=(0.25, 0.45 * sx, 0), col="red", shape="Block")
        for i, x in enumerate((-0.15, -0.05, 0.05, 0.15)):
            H.prim(f"Grin{i}", "Eyes", "Block", (0.08, 0.035, 0.03), (x, 0.47, -0.77), rot=(0.25, 0, 0.5 if i % 2 else -0.5), col="red", mat="hard", glow=True, role="mouth", pri=1.9)
        teeth = teeth_row((0, 0.2, -0.99), (1, 0, 0), 9, 0.14, 0.11, up=False) & plane((0, -1, 0), -0.08)
        H.piece("Teeth", "Body", teeth.rot(0, 0, 0), col="chrome", mat="metal", tris=500, role="teeth", pri=1.3, smooth=1)
    for sx, nm in ((1, "R"), (-1, "L")):
        c = A(0.62 * sx, 0.07, -0.62)
        if monster:
            br = cylinder(0.3, 0.012, rr=0.005).at(*T(c))
            for a in np.linspace(0, TAU, 10, endpoint=False):
                d = A(math.sin(a), 0, math.cos(a))
                br = br | cone(0.06, 0.0, 0.05, axis=0).rot(0, math.degrees(a + 0.5) - 90, 0).at(*T(c + d * 0.32))
            br = br | cylinder(0.07, 0.03).at(*T(c + A(0, 0.02, 0)))
            H.piece("Saw" + nm, "Brush" + nm, br, col="chrome", mat="metal", tris=500, role="blade", pri=1.3, smooth=1)
        else:
            br = cylinder(0.06, 0.03).at(*T(c + A(0, 0.02, 0)))
            for a in (0.0, TAU / 3, 2 * TAU / 3):
                d = A(math.sin(a), 0, math.cos(a))
                br = br | U(*(capsule(T(c + d * 0.05), T(c + d * 0.32 + A(math.cos(a), 0, -math.sin(a)) * j * 0.04 + A(0, -0.02, 0)), 0.014) for j in (-1, 0, 1)))
            H.piece("Brush" + nm + "P", "Brush" + nm, br, col="dark", mat="plastic", tris=400, role="detail", pri=1.5)
        wh = cylinder(0.14, 0.05, axis=0, rr=0.02).at(0.84 * sx, 0.14, 0.05)
        wh = wh.ss(U(*(round_box(0.08, 0.02, 0.15, 0.005).rot(a, 0, 0).at(0.84 * sx + 0.05 * sx, 0.14, 0.05) for a in (0, 60, 120))), 0.005)
        H.piece("Wheel" + nm + "P", "Wheel" + nm, wh, col="tyre", mat="rubber", tris=300, role="wheel", pri=1.6)
    H.socket("mouth", (0, 0.3, -1.05), "Body")
    H.socket("head", (0, 0.75, 0), "Body")
    H.socket("core", (0, 0.4, 0), "Body")
    H.rig.update({"head": "Body"})

    def brushes(p, tk, speed):
        spin(p, "BrushR", "y", tk, TAU / 3 if not monster else TAU / 10, sgn=1, speed=speed)
        spin(p, "BrushL", "y", tk, TAU / 3 if not monster else TAU / 10, sgn=-1, speed=speed)

    def blink(p, u, at):
        b = bump(u % 1.0, at - 0.04, at + 0.04)
        add(p, "Eyes", (0, -0.035 * b, 0, 0, 0, 0))

    def idle(t):
        u = t / 3.0
        p = {}
        brushes(p, t / 3.0 * 20, 0.25)
        add(p, "Turret", (0, 0, 0, 0, 1.4 * math.sin(TAU * u), 0))
        add(p, "Body", (0, 0.01 * math.sin(TAU * u * 4), 0, 0.01 * math.sin(TAU * u * 2), 0.2 * math.sin(TAU * u * 0.5) if not monster else 0.12 * math.sin(TAU * u), 0))
        blink(p, u, 0.35)
        blink(p, u, 0.85)
        if monster:
            add(p, "Body", (0, 0.015 * abs(math.sin(TAU * u * 6)), 0, 0, 0, 0.01 * math.sin(TAU * u * 9)))
        return p

    def move(t):
        u = t / 0.8
        p = {}
        brushes(p, t / 0.8 * 20, 1.0)
        spin(p, "WheelR", "x", t / 0.8 * 20, math.pi / 3, sgn=-1, speed=0.8)
        spin(p, "WheelL", "x", t / 0.8 * 20, math.pi / 3, sgn=-1, speed=0.8)
        add(p, "Body", (0, 0.015 * abs(math.sin(TAU * u * 3)), 0, 0.04, 0.15 * math.sin(TAU * u), 0.02 * math.sin(TAU * u)))
        add(p, "Turret", (0, 0, 0, 0, 2.0 * math.sin(TAU * u), 0))
        return p

    def attack(t):
        s = t / 0.9
        w, st, rec = env(s, 0.35, (0.3, 0.85))
        p = {}
        tk = t / 0.9 * 16
        brushes(p, tk, 1.6)
        if monster:
            sp = ease((s - 0.3) / 0.5)
            add(p, "Body", (0, 0.25 * st, 0.15 * w - 0.6 * st, 0.1 * w, -TAU * sp, 0))
        else:
            add(p, "Body", (0, 0.12 * st, 0.25 * w - 0.8 * st, 0.15 * w - 0.12 * st, 0, 0))
        add(p, "Eyes", (0, 0.02 * w, 0, 0, 0, 0))
        out = scaled(p, rec)
        if monster:
            o = list(out.get("Body", (0,) * 6))
            o[4] = -TAU * ease((s - 0.3) / 0.5)
            out["Body"] = tuple(o)
        return out

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, 0.12 * k, 0.3 * k, 0.25 * k, 0, 0.15 * math.sin(t * 40) * k))
        add(p, "Eyes", (0, -0.03 * k, 0, 0, 0, 0))
        return p

    clips(H, idle, move, attack, hit, 0.8, idle_len=3.0, move_len=0.8, attack_len=0.9)
    return H


@hero("robot vacuum", "bots")
def robot_vacuum():
    return _vacuum("robot vacuum", False)


@hero("robot vacuum monster", "bots")
def robot_vacuum_monster():
    return _vacuum("robot vacuum monster", True)


# ================================================================================================ mine bot
@hero("mine bot", "bots")
def mine_bot():
    """A rolling bomb robot: a riveted iron sphere with an equator band and stubby contact horns, a visor slit
    with two red LED eyes, a fuse-cap housing on top whose red warning light blinks (it pops in and out of its
    housing), two chunky treaded wheels on an axle and a little tail caster. Rolls with a wobble; its attack is a
    shaking, blinking charge."""
    H = OH("mine bot", plan="Blob", gait="drive", tags=["robot", "machine", "bomb"])
    H.preview = {"primary": "#4B5563", "secondary": "#EF4444"}
    H.body((0, 0.32, 0))
    H.bone("Bomb", "Body", (0, 0.75, 0))
    H.bone("Light", "Bomb", (0, 1.33, 0))
    H.mbone("Wheel#", "Body", (0.62, 0.32, 0))
    c = A(0, 0.78, 0)
    bm = sphere(0.56, T(c)).su(torus(0.57, 0.05).at(*T(c)), 0.02)
    for i, a in enumerate(np.linspace(0, TAU, 5, endpoint=False)):
        d = A(math.sin(a) * 0.72, 0.69, math.cos(a) * 0.72)
        d /= np.linalg.norm(d)
        bm = bm.su(capsule(T(c + d * 0.5), T(c + d * 0.7), 0.045), 0.03) | sphere(0.065, T(c + d * 0.7))
    bm = bm | U(*(sphere(0.032, (0.585 * math.sin(a), c[1], 0.585 * math.cos(a))) for a in np.linspace(0, TAU, 16, endpoint=False)))
    bm = bm.su(cylinder(0.15, 0.07, rr=0.02).at(*T(c + A(0, 0.55, 0))), 0.05)
    bm = bm.ss(ellipsoid(0.36, 0.09, 0.15, T(c + A(0, 0.08, -0.55))), 0.02)
    H.piece("BombP", "Bomb", bm, col="primary", mat="metal", tris=1800, res=128, role="body",
            pattern=spots(0.18, 0.05, depth=0.2, seed=13))
    H.prim("Visor", "Bomb", "Ellipsoid", (0.68, 0.14, 0.2), T(c + A(0, 0.08, -0.48)), col="black", mat="glass", role="face", pri=1.2)
    for sx, nm in ((1, "R"), (-1, "L")):
        led_eye(H, "Eye" + nm, "Bomb", T(c + A(0.13 * sx, 0.08, -0.55)), (0.1, 0.07, 0.04), col="secondary")
    H.prim("Warn", "Bomb", "Block", (0.3, 0.05, 0.02), T(c + A(0, -0.22, -0.53)), rot=(-0.4, 0, 0), col=[1.0, 0.8, 0.15], mat="hard", role="detail", pri=2.0)
    H.prim("LightP", "Light", "Ball", (0.18, 0.18, 0.18), (0, 1.38, 0), col="secondary", mat="hard", glow=True, role="light", pri=1.3)
    H.prim("Cage", "Bomb", "Cylinder", (0.06, 0.24, 0.24), (0, 1.36, 0), rot=(0, 0, math.pi / 2), col="gunmetal", mat="metal", role="detail", pri=1.6)
    H.piece("Axle", "Body", capsule((-0.6, 0.32, 0), (0.6, 0.32, 0), 0.06) | capsule((0, 0.3, 0.1), (0, 0.12, 0.5), 0.04) | sphere(0.08, (0, 0.08, 0.52)),
            col="gunmetal", mat="metal", tris=400, role="detail", pri=1.4)
    for sx, nm in ((1, "R"), (-1, "L")):
        wc = A(0.62 * sx, 0.32, 0)
        tyre = torus(0.24, 0.08, axis=0).at(*T(wc))
        tyre = tyre | U(*(round_box(0.07, 0.035, 0.05, 0.01).rot(math.degrees(a), 0, 0).at(*T(wc + A(0, 0.31 * math.cos(a), 0.31 * math.sin(a)))) for a in np.linspace(0, TAU, 12, endpoint=False)))
        hub = cylinder(0.17, 0.05, axis=0).at(*T(wc)) | U(*(round_box(0.06, 0.035, 0.16, 0.01).rot(math.degrees(a), 0, 0).at(*T(wc)) for a in (0, 60, 120)))
        H.piece("Wheel" + nm + "P", "Wheel" + nm, U(tyre, hub), col="tyre", mat="rubber", tris=900, role="wheel", pri=1.2)
        H.prim("Hubcap" + nm, "Wheel" + nm, "Cylinder", (0.05, 0.16, 0.16), T(wc + A(0.04 * sx, 0, 0)), col="secondary", mat="metal", role="detail", pri=1.8)
    H.socket("mouth", T(c + A(0, 0, -0.65)), "Bomb")
    H.socket("head", (0, 1.6, 0), "Light")
    H.socket("core", T(c), "Bomb")
    H.rig.update({"head": "Bomb"})

    def blink(u, n=2, w=0.06):
        x = (u * n) % 1.0
        return 1.0 - bump(x, 0.5 - w, 0.5 + w)

    def idle(t):
        u = t / 2.0
        p = {}
        add(p, "Bomb", (0, 0.01 * math.sin(TAU * u * 2), 0, 0.05 * math.sin(TAU * u), 0.25 * math.sin(TAU * u * 0.5), 0.03 * math.sin(TAU * u)))
        add(p, "Light", (0, -0.12 * (1 - blink(u, 2)), 0, 0, 0, 0))
        return p

    def move(t):
        u = t / 0.6
        p = {}
        tk = t / 0.6 * 20
        spin(p, "WheelR", "x", tk, TAU / 6, sgn=-1, speed=1.0)
        spin(p, "WheelL", "x", tk, TAU / 6, sgn=-1, speed=1.0)
        add(p, "Bomb", (0, 0.03 * abs(math.sin(TAU * u * 2)), 0, -0.18 + 0.06 * math.sin(TAU * u * 2), 0, 0.06 * math.sin(TAU * u)))
        add(p, "Light", (0, -0.12 * (1 - blink(u, 1, 0.1)), 0, 0.2 * math.sin(TAU * u * 2), 0, 0))
        add(p, "Body", (0, 0, 0, 0, 0.08 * math.sin(TAU * u), 0))
        return p

    def attack(t):
        s = t / 0.9
        w, st, rec = env(s, 0.45, (0.4, 0.85))
        p = {}
        tk = t / 0.9 * 16
        spin(p, "WheelR", "x", tk, TAU / 6, sgn=-1, speed=1.8)
        spin(p, "WheelL", "x", tk, TAU / 6, sgn=-1, speed=1.8)
        shake = math.sin(TAU * s * 14) * w
        add(p, "Body", (0.03 * shake, 0.35 * st, -0.8 * st, 0, 0, 0))
        add(p, "Bomb", (0, 0, 0, 0.15 * w - 0.45 * st, 0, 0.08 * shake))
        add(p, "Light", (0, 0.1 * (w + st) - 0.12 * (1 - blink(s, 6, 0.15)) * w, 0, 0, 0, 0))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, 0.1 * k, 0.25 * k, 0, 0, 0))
        add(p, "Bomb", (0, 0, 0, 0.4 * k, 0, 0.2 * math.sin(t * 40) * k))
        add(p, "Light", (0, 0.12 * k, 0, 0, 0, 0))
        return p

    clips(H, idle, move, attack, hit, 1.6, idle_len=2.0, move_len=0.6, attack_len=0.9)
    return H


# ================================================================================================ robot ball
@hero("robot ball", "bots")
def robot_ball():
    """A rolling sphere robot: a ball body with six round hatch panels and a groove ring, carrying a separate
    saucer-dome head that stays upright on top: a dark visor band, one big camera eye and a small one, twin
    antennae. The ball rolls under the steady head; it rams as its attack."""
    H = OH("robot ball", plan="Orb", gait="roll", tags=["robot", "machine"])
    H.preview = {"primary": "#F1F3F5", "secondary": "#F59E0B", "rubber": "#2A2C31"}
    H.body((0, 0.72, 0))
    H.bone("Ball", "Body", (0, 0.72, 0))
    H.bone("Head", "Body", (0, 1.45, 0))
    c = A(0, 0.72, 0)
    R = 0.72
    ball = sphere(R, T(c))
    ball = ball.ss(torus(R, 0.018, axis=0).at(*T(c)), 0.008)
    # a rubber tread band around the rolling direction (yz ring, invariant under the roll) and two big side hubs
    ball = ball.ss(U(torus(R, 0.03, axis=0).at(*T(c + A(0.2, 0, 0))), torus(R, 0.03, axis=0).at(*T(c + A(-0.2, 0, 0)))), 0.01)
    ball = ball.ss(U(*(sphere(0.05, T(c + A(0, R * math.cos(a), R * math.sin(a)))) for a in np.linspace(0, TAU, 8, endpoint=False))), 0.01)
    H.piece("BallP", "Ball", ball, col="primary", mat="plastic", tris=1600, res=128, role="body")
    tread = (sphere(R + 0.03, T(c)) & SDF(lambda p: np.abs(p[:, 0]) - 0.15)) - sphere(R - 0.05, T(c))
    tread = tread.ss(U(*(round_box(0.2, 0.02, 0.05, 0.01).rot(math.degrees(a), 0, 0).at(*T(c + A(0, (R + 0.03) * math.cos(a), (R + 0.03) * math.sin(a)))) for a in np.linspace(0, TAU, 16, endpoint=False))), 0.01)
    hubs = U(*(cylinder(0.3, 0.05, axis=0, rr=0.02).at(*T(c + A(0.7 * sx, 0, 0))) | cylinder(0.12, 0.08, axis=0, rr=0.02).at(*T(c + A(0.74 * sx, 0, 0))) for sx in (1, -1)))
    H.piece("Tread", "Ball", tread, col="rubber", mat="rubber", tris=900, role="detail", pri=1.2)
    H.piece("Hubs", "Ball", hubs, col="secondary", mat="metal", tris=500, role="detail", pri=1.3)
    hc = A(0, 1.62, 0)
    hd = round_box(0.42, 0.3, 0.36, 0.14, T(hc)).su(cylinder(0.14, 0.12).at(*T(hc + A(0, -0.32, 0))), 0.05)
    hd = hd.ss(round_box(0.36, 0.2, 0.1, 0.08, T(hc + A(0, 0.0, -0.38))), 0.02)
    for sx in (1, -1):
        hd = hd | capsule(T(hc + A(0.28 * sx, 0.25, 0.05)), T(hc + A(0.42 * sx, 0.62, 0.1)), 0.02) | sphere(0.05, T(hc + A(0.42 * sx, 0.64, 0.1)))
        hd = hd.su(cylinder(0.1, 0.05, axis=0, rr=0.02).at(*T(hc + A(0.43 * sx, 0, 0))), 0.02)
    H.piece("HeadP", "Head", hd, col="primary", mat="plastic", tris=1100, role="head")
    H.prim("Screen", "Head", "Block", (0.66, 0.36, 0.04), T(hc + A(0, 0.0, -0.31)), col="black", mat="glass", role="face", pri=1.1)
    for sx, nm in ((1, "R"), (-1, "L")):
        H.prim("Eye" + nm, "Head", "Ellipsoid", (0.14, 0.2, 0.04), T(hc + A(0.15 * sx, 0.03, -0.34)), col="glow", mat="hard", glow=True, role="eye", pri=1.2)
    H.prim("Mouth", "Head", "Block", (0.14, 0.03, 0.03), T(hc + A(0, -0.11, -0.34)), col="glow", mat="hard", glow=True, role="mouth", pri=1.6)
    H.socket("mouth", T(hc + A(0, -0.1, -0.45)), "Head")
    H.socket("head", T(hc + A(0, 0.7, 0)), "Head")
    H.rig.update({"head": "Head"})

    def idle(t):
        u = t / 2.6
        p = {}
        add(p, "Ball", (0, 0, 0, 0.1 * math.sin(TAU * u * 0.5), 0, 0.05 * math.sin(TAU * u)))
        add(p, "Head", (0, 0.02 * math.sin(TAU * u * 2), 0, 0.08 * math.sin(TAU * u + 1), 0.5 * math.sin(TAU * u * 0.5), 0.1 * math.sin(TAU * u)))
        return p

    def move(t):
        u = t / 0.8
        p = {}
        spin(p, "Ball", "x", t / 0.8 * 20, math.pi / 2, sgn=-1, speed=0.9)
        add(p, "Head", (0, 0.02 * abs(math.sin(TAU * u * 2)), 0.05, 0.15 + 0.04 * math.sin(TAU * u * 2), 0.1 * math.sin(TAU * u), 0.08 * math.sin(TAU * u)))
        add(p, "Body", (0, 0.01 * abs(math.sin(TAU * u * 2)), 0, 0, 0, 0.04 * math.sin(TAU * u)))
        return p

    def attack(t):
        s = t / 0.9
        w, st, rec = env(s, 0.4, (0.35, 0.85))
        p = {}
        roll = -(1.2 * w + 3.2 * ease((s - 0.35) / 0.4))
        add(p, "Ball", (0, 0, 0, roll, 0, 0))
        add(p, "Body", (0, 0.15 * st, 0.3 * w - 0.9 * st, 0, 0, 0))
        add(p, "Head", (0, -0.05 * w, 0.05 * w, -0.25 * w + 0.3 * st, 0, 0))
        out = scaled(p, rec)
        o = list(out.get("Ball", (0,) * 6))
        o[3] = roll
        out["Ball"] = tuple(o)
        return out

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, 0.1 * k, 0.3 * k, 0, 0, 0))
        add(p, "Ball", (0, 0, 0, 0.5 * k, 0, 0))
        add(p, "Head", (0, 0.1 * k, 0.1 * k, 0.4 * k, 0.3 * k, 0.25 * math.sin(t * 40) * k))
        return p

    clips(H, idle, move, attack, hit, 2.0, idle_len=2.6, move_len=0.8, attack_len=0.9)
    return H


# ================================================================================================ drones
def _drone(hid, kind):
    """combat: a sleek wedge quadcopter with a dark sensor canopy, a red eye in the nose, four ducted rotors on
    swept struts, tail fins and twin laser cannons under the belly that track and recoil.
    repair: a round hovering pod with yellow-black hazard bands, a big camera eye, one top rotor on a mast, a
    wrench arm and a welding-torch arm with a glowing tip."""
    combat = kind == "combat"
    H = OH(hid, plan="Bird", gait="hover", tags=["robot", "machine", "drone"])
    H.preview = ({"primary": "#3C434C", "secondary": "#EF4444"} if combat else {"primary": "#F2C230", "secondary": "#22D3EE"}) | {"chrome": "#D5DCE3"}
    yc = 1.8
    H.body((0, yc, 0))
    rotors = []
    if combat:
        for nm, (x, z) in (("FR", (0.95, -0.7)), ("FL", (-0.95, -0.7)), ("BR", (0.95, 0.75)), ("BL", (-0.95, 0.75))):
            H.bone("Rotor" + nm, "Body", (x, yc + 0.06, z))
            rotors.append(("Rotor" + nm, x, z, 1 if nm in ("FR", "BL") else -1))
        H.bone("Gun", "Body", (0, yc - 0.18, -0.1))
        fus = ellipsoid(0.42, 0.18, 0.85, (0, yc, 0.05)).su(ellipsoid(0.3, 0.14, 0.4, (0, yc - 0.06, -0.55)), 0.15)
        fus = fus.su(cone(0.2, 0.0, 0.25, axis=2).rot(0, 180, 0).at(0, yc - 0.04, -0.98), 0.08)
        fus = fus.ss(SDF(lambda p: np.abs(p[:, 0]) - 0.012) & ellipsoid(0.5, 0.3, 1.0, (0, yc + 0.1, 0.05)) & plane((0, -1, 0), -(yc + 0.12)), 0.004)
        for sx in (1, -1):
            fus = fus.su(plate_fin(sx, yc), 0.02)
        H.piece("Fuselage", "Body", fus, col="primary", mat="metal", tris=1500, res=136, role="body",
                pattern=stripes(lambda P: P[:, 2], 1.0, width=0.08, depth=-0.0))
        can = ellipsoid(0.24, 0.12, 0.38, (0, yc + 0.14, -0.25)) & plane((0, -1, 0), -(yc + 0.06))
        H.piece("Canopy", "Body", can, col="black", mat="glass", tris=500, role="face", pri=1.2)
        led_eye(H, "Eye", "Body", (0, yc - 0.02, -1.12), (0.16, 0.08, 0.06), col="secondary")
        struts = None
        ducts = None
        for rb, x, z, _ in rotors:
            struts = U(struts, capsule((x * 0.25, yc, z * 0.35), (x * 0.82, yc + 0.03, z * 0.88), 0.05))
            ducts = U(ducts, torus(0.4, 0.05).scale3(1.0, 1.6, 1.0).at(x, yc + 0.05, z), cylinder(0.07, 0.06).at(x, yc + 0.0, z))
            ducts = U(ducts, capsule((x - 0.38, yc + 0.0, z), (x + 0.38, yc + 0.0, z), 0.018), capsule((x, yc, z - 0.38), (x, yc, z + 0.38), 0.018))
        H.piece("Struts", "Body", struts, col="gunmetal", mat="metal", tris=500, role="limb", pri=1.2)
        H.piece("Ducts", "Body", ducts, col="primary", mat="metal", tris=1300, role="wing", pri=1.1)
        for rb, x, z, sg in rotors:
            bl = U(*(round_box(0.34, 0.012, 0.045, 0.01).rot(0, a, 6 if i == 0 else -6).at(x, yc + 0.08, z) for i, a in enumerate((0, 90))))
            H.piece(rb + "P", rb, bl | cylinder(0.05, 0.03).at(x, yc + 0.09, z), col="dark", mat="plastic", tris=300, role="rotor", pri=1.5)
        gun = U(*(capsule((0.17 * sx, yc - 0.26, 0.15), (0.17 * sx, yc - 0.26, -0.75), 0.05) for sx in (1, -1)), round_box(0.26, 0.07, 0.2, 0.04, (0, yc - 0.2, 0.0)))
        gun = gun | U(*(torus(0.065, 0.02, axis=2).at(0.17 * sx, yc - 0.26, -0.55) for sx in (1, -1)))
        H.piece("Guns", "Gun", gun, col="gunmetal", mat="metal", tris=700, role="weapon", pri=1.2)
        for sx, nm in ((1, "R"), (-1, "L")):
            H.prim("Muzzle" + nm, "Gun", "Ball", (0.08, 0.08, 0.08), (0.17 * sx, yc - 0.26, -0.79), col="secondary", mat="hard", glow=True, role="light", pri=1.7)
        H.socket("mouth", (0, yc - 0.26, -0.85), "Gun")
        H.socket("muzzle", (0, yc - 0.26, -0.85), "Gun")
        H.socket("exhaust", (0, yc, 0.9), "Body")
        H.rig.update({"head": "Body"})
    else:
        H.bone("Rotor", "Body", (0, yc + 0.72, 0))
        H.bone("Cam", "Body", (0, yc, -0.42))
        H.mbone("Shoulder#", "Body", (0.45, yc - 0.12, -0.05))
        H.mbone("Elbow#", "Shoulder#", (0.78, yc - 0.42, -0.25))
        H.mbone("Hand#", "Elbow#", (0.82, yc - 0.78, -0.45))
        rotors.append(("Rotor", 0, 0, 1))
        pod = sphere(0.52, (0, yc, 0)).su(ellipsoid(0.4, 0.2, 0.4, (0, yc - 0.42, 0.0)), 0.12)
        pod = pod.ss(torus(0.53, 0.015).at(0, yc + 0.18, 0), 0.006)
        haz = _hazard(lambda P: (P[:, 0] + P[:, 1]) * 1.0, 4.0, region=lambda P: np.clip(1 - np.abs(P[:, 1] - (yc - 0.12)) / 0.14, 0, 1))
        H.piece("Pod", "Body", pod, col="primary", mat="plastic", tris=1400, res=128, role="body", pattern=haz)
        mast = U(cylinder(0.06, 0.18).at(0, yc + 0.58, 0), cylinder(0.14, 0.04, rr=0.02).at(0, yc + 0.5, 0))
        H.piece("Mast", "Body", mast, col="gunmetal", mat="metal", tris=300, role="detail", pri=1.4)
        bl = U(*(round_box(0.62, 0.014, 0.06, 0.012).rot(0, a, 7).at(0, yc + 0.76, 0).rot(0, 0, 0) for a in (0, 120, 240)))
        H.piece("RotorP", "Rotor", (bl | cylinder(0.08, 0.04).at(0, yc + 0.77, 0)), col="dark", mat="plastic", tris=500, role="rotor", pri=1.3)
        camb = cylinder(0.2, 0.1, axis=2, rr=0.03).at(0, yc + 0.02, -0.48)
        H.piece("CamBarrel", "Cam", camb, col="gunmetal", mat="metal", tris=300, role="eye", pri=1.15)
        H.prim("CamLens", "Cam", "Cylinder", (0.05, 0.3, 0.3), (0, yc + 0.02, -0.58), rot=(0, math.pi / 2, 0), col="secondary", mat="glass", glow=True, role="eye", pri=1.2)
        H.prim("CamPupil", "Cam", "Cylinder", (0.05, 0.12, 0.12), (0, yc + 0.02, -0.6), rot=(0, math.pi / 2, 0), col="black", mat="hard", role="pupil", pri=1.25)
        H.prim("CamShine", "Cam", "Ball", (0.05, 0.05, 0.05), (0.06, yc + 0.08, -0.62), col="shine", mat="hard", role="shine", pri=2.2)
        H.prim("Status", "Body", "Ball", (0.08, 0.08, 0.08), (0.24, yc + 0.32, -0.32), col=[0.3, 1.0, 0.4], mat="hard", glow=True, role="light", pri=2.0)
        for sx, nm in ((1, "R"), (-1, "L")):
            sh, el, hn = A(0.45 * sx, yc - 0.12, -0.05), A(0.78 * sx, yc - 0.42, -0.25), A(0.82 * sx, yc - 0.78, -0.45)
            H.piece("Upper" + nm, "Shoulder" + nm, U(sphere(0.09, T(sh)), capsule(T(sh), T(el), 0.05), sphere(0.07, T(el))), col="gunmetal", mat="metal", tris=300, role="limb")
            H.piece("Fore" + nm, "Elbow" + nm, capsule(T(el), T(hn), 0.045) | cylinder(0.07, 0.05).at(*T(hn)), col="gunmetal", mat="metal", tris=250, role="limb")
            if sx > 0:  # wrench
                w0 = hn + A(0, -0.08, 0)
                wr = round_box(0.03, 0.22, 0.06, 0.02, T(w0 + A(0, -0.18, 0)))
                jaw = (cylinder(0.13, 0.03, axis=0).at(*T(w0 + A(0, -0.45, 0))) - cylinder(0.06, 0.1, axis=0).at(*T(w0 + A(0, -0.47, 0))))
                jaw = jaw - round_box(0.1, 0.12, 0.05, 0.0, T(w0 + A(0, -0.56, 0.0)))
                H.piece("Wrench", "Hand" + nm, U(wr, jaw), col="steel", mat="metal", tris=500, role="weapon", pri=1.2)
            else:  # welding torch
                w0 = hn + A(0, -0.06, 0)
                tc = U(cylinder(0.06, 0.12).at(*T(w0 + A(0, -0.1, 0))), cone(0.05, 0.025, 0.14).rot(180, 0, 0).at(*T(w0 + A(0, -0.32, 0))))
                H.piece("Torch", "Hand" + nm, tc, col="chrome", mat="metal", tris=400, role="weapon", pri=1.2)
                H.prim("Flame", "Hand" + nm, "Ellipsoid", (0.07, 0.16, 0.07), T(w0 + A(0, -0.54, 0)), col="glow", mat="hard", glow=True, role="flame", pri=1.6)
        H.socket("mouth", (-0.82, yc - 1.4, -0.45), "HandL")
        H.socket("hand", (0.82, yc - 1.4, -0.45), "HandR")
        H.socket("head", (0, yc + 1.0, 0), "Body")
        H.rig.update({"head": "Cam", "arms": [{"shoulder": "ShoulderR", "elbow": "ElbowR", "side": 1}, {"shoulder": "ShoulderL", "elbow": "ElbowL", "side": -1}]})

    def rot(p, tk, speed):
        for rb, x, z, sg in rotors:
            spin(p, rb, "y", tk, math.pi / 2 if combat else TAU / 3, sgn=sg, speed=speed)

    def idle(t):
        u = t / 2.4
        p = {}
        rot(p, t / 2.4 * 20, 1.0)
        add(p, "Body", (0, 0.1 * math.sin(TAU * u), 0, 0.03 * math.sin(TAU * u + 1), 0.15 * math.sin(TAU * u * 0.5), 0.04 * math.sin(TAU * u)))
        if combat:
            add(p, "Gun", (0, 0, 0, 0.1 * math.sin(TAU * u + 0.5), 0.3 * math.sin(TAU * u * 0.5 + 1), 0))
        else:
            add(p, "Cam", (0, 0, 0, 0.1 * math.sin(TAU * u * 0.5), 0.35 * math.sin(TAU * u * 0.5 + 0.5), 0))
            add(p, "ShoulderR", (0, 0, 0, 0.2 + 0.15 * math.sin(TAU * u), 0, 0.1))
            add(p, "HandR", (0, 0, 0, 0, 0.6 * math.sin(TAU * u * 2), 0))
            add(p, "ShoulderL", (0, 0, 0, 0.15 + 0.1 * math.sin(TAU * u + 2), 0, -0.1))
        return p

    def move(t):
        u = t / 1.0
        p = {}
        rot(p, t / 1.0 * 20, 1.3)
        add(p, "Body", (0, 0.06 * math.sin(TAU * u * 2), 0, -0.3, 0.05 * math.sin(TAU * u), 0.08 * math.sin(TAU * u)))
        if combat:
            add(p, "Gun", (0, 0, 0, 0.3, 0, 0))
        else:
            add(p, "ShoulderR", (0, 0, 0, -0.3, 0, 0.15))
            add(p, "ShoulderL", (0, 0, 0, -0.3, 0, -0.15))
            add(p, "Cam", (0, 0, 0, 0.3, 0, 0))
        return p

    def attack(t):
        s = t / 0.9
        w, st, rec = env(s, 0.35, (0.3, 0.85))
        p = {}
        rot(p, t / 0.9 * 16, 1.6)
        if combat:
            add(p, "Body", (0, 0.25 * w - 0.1 * st, 0.1 * w, 0.15 * w - 0.25 * st, 0, 0))
            kick = (abs(math.sin(TAU * s * 5)) * st)
            add(p, "Gun", (0, 0, 0.12 * kick, -0.25 * w - 0.1 * st + 0.08 * kick, 0, 0))
        else:
            add(p, "Body", (0, 0.15 * w, 0.15 * w - 0.4 * st, 0.15 * w - 0.25 * st, 0.4 * w - 0.5 * st, 0))
            add(p, "ShoulderR", (0, 0, 0, 1.6 * w - 0.6 * st, 0, 0.4 * w))
            add(p, "ElbowR", (0, 0, 0, 0.8 * w - 0.6 * st, 0, 0))
            add(p, "HandR", (0, 0, 0, 0, 0, -0.8 * st))
            add(p, "ShoulderL", (0, 0, 0, 0.6 * st, 0, -0.3 * st))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        rot(p, t / 0.45 * 8, 0.7)
        add(p, "Body", (0, -0.15 * k, 0.3 * k, 0.35 * k, 0, 0.35 * math.sin(t * 40) * k))
        return p

    clips(H, idle, move, attack, hit, 2.6, idle_len=2.4, move_len=1.0, attack_len=0.9)
    return H


def plate_fin(sx, yc):
    """Small swept tail fin (combat drone)."""
    return round_box(0.025, 0.14, 0.18, 0.015).rot(0, 0, -35 * sx).rot(-25, 0, 0).at(0.22 * sx, yc + 0.17, 0.72)


@hero("combat drone", "bots")
def combat_drone():
    return _drone("combat drone", "combat")


@hero("repair drone", "bots")
def repair_drone():
    return _drone("repair drone", "repair")


# ================================================================================================ tripods
def _leg_pts(a, hip_r, hip_y, knee_r, knee_y, foot_r):
    d = A(math.sin(a), 0, math.cos(a))
    return d * hip_r + A(0, hip_y, 0), d * knee_r + A(0, knee_y, 0), d * foot_r + A(0, 0.0, 0), d


def _tri_walk(p, u, legs, lift, swing, duty=0.34):
    """Three legs stepping one after another: (hip bone, knee bone, phase). +rx on a hip swings its foot forward."""
    for hip, knee, ph in legs:
        x = (u + ph) % 1.0
        if x < duty:
            k = x / duty
            add(p, hip, (0, lift * math.sin(math.pi * k), 0, swing * (2 * ease(k) - 1), 0, 0))
            add(p, knee, (0, 0, 0, -0.25 * math.sin(math.pi * k), 0, 0))
        else:
            k = (x - duty) / (1 - duty)
            add(p, hip, (0, 0, 0, swing * (1 - 2 * k), 0, 0))


@hero("alien tripod", "bots")
def alien_tripod():
    """A towering three-legged alien war machine: a flattened saucer hull with a raised lip and a domed bridge
    ringed by glowing ports, a heat-ray emitter on an articulated neck under its front, and three long jointed
    legs whose high knees arch above the hull before plunging down to pointed, clawed feet. Walks one leg at a
    time; its attack aims the heat-ray and recoils."""
    H = OH("alien tripod", plan="Giant", gait="stomp", tags=["alien", "machine", "walker"])
    H.preview = {"primary": "#7C8794", "secondary": "#4ADE80"}
    yc = 4.3
    H.body((0, yc, 0))
    H.bone("Ray1", "Body", (0, yc - 0.3, -1.05))
    H.bone("Ray2", "Ray1", (0, yc - 0.65, -1.6))
    legs = []
    for nm, a in (("B", 0.0), ("R", 2 * math.pi / 3), ("L", -2 * math.pi / 3)):
        hp, kn, ft, d = _leg_pts(a, 0.75, yc - 0.35, 1.85, yc + 0.75, 2.5)
        H.bone("Hip" + nm, "Body", T(hp))
        H.bone("Knee" + nm, "Hip" + nm, T(kn))
        legs.append((nm, hp, kn, ft, d))
    hull = ellipsoid(1.45, 0.42, 1.45, (0, yc, 0)).su(ellipsoid(0.95, 0.5, 0.95, (0, yc + 0.35, 0)), 0.2)
    hull = hull.su(torus(1.42, 0.09).at(0, yc + 0.02, 0), 0.06)
    hull = hull.su(ellipsoid(0.8, 0.4, 0.8, (0, yc - 0.3, 0)), 0.2)
    hull = hull.ss(U(*(torus(1.1 - 0.25 * i, 0.016).at(0, yc + 0.2 + 0.12 * i, 0) for i in range(3))), 0.005)
    for nm, hp, kn, ft, d in legs:
        hull = hull.su(sphere(0.3, T(hp + A(0, 0.05, 0))), 0.12)
    H.piece("Hull", "Body", hull, col="primary", mat="metal", tris=1800, res=140, role="body",
            pattern=gradient(1, yc - 0.6, yc + 0.6, 0.72, 1.0))
    dome = ellipsoid(0.62, 0.36, 0.62, (0, yc + 0.72, 0.05)) & plane((0, -1, 0), -(yc + 0.6))
    H.piece("Bridge", "Body", dome, col="darker", mat="glass", tris=600, role="head", pri=1.1)
    for i, a in enumerate(np.linspace(0, TAU, 7, endpoint=False)):
        H.prim(f"Port{i}", "Body", "Ball", (0.16, 0.16, 0.16), (0.98 * math.sin(a + 0.45), yc + 0.42, 0.98 * math.cos(a + 0.45)), col="secondary", mat="hard", glow=True, role="light", pri=1.9)
    r1 = U(sphere(0.2, (0, yc - 0.3, -1.05)), tube([(0, yc - 0.3, -1.05), (0, yc - 0.5, -1.35), (0, yc - 0.65, -1.6)], [0.12, 0.1, 0.1], k=0.03))
    H.piece("Neck", "Ray1", r1, col="gunmetal", mat="metal", tris=500, role="limb", pri=1.3)
    em = U(sphere(0.13, (0, yc - 0.65, -1.6)), cone(0.12, 0.32, 0.18, axis=2).rot(0, 180, 0).at(0, yc - 0.68, -1.85))
    em = em.ss(sphere(0.25, (0, yc - 0.68, -2.1)), 0.02)
    em = em | U(*(capsule((0.28 * math.cos(a), yc - 0.68 + 0.28 * math.sin(a), -2.02), (0.4 * math.cos(a), yc - 0.68 + 0.4 * math.sin(a), -2.25), 0.025) for a in (0.5, 2.6, 4.7)))
    H.piece("Emitter", "Ray2", em, col="primary", mat="metal", tris=700, role="weapon", pri=1.2)
    H.prim("RayCore", "Ray2", "Ball", (0.2, 0.2, 0.2), (0, yc - 0.68, -1.95), col="secondary", mat="hard", glow=True, role="eye", pri=1.3)
    for nm, hp, kn, ft, d in legs:
        th = U(sphere(0.2, T(hp)), tube([T(hp), T((hp + kn) / 2 + A(0, 0.15, 0)), T(kn)], [0.17, 0.14, 0.13], k=0.04), sphere(0.17, T(kn)))
        th = th.ss(U(*(torus(0.15, 0.012).rot(0, 0, 0).at(*T(hp + (kn - hp) * f)) for f in (0.35, 0.6))), 0.004) if False else th
        H.piece("Thigh" + nm, "Hip" + nm, th, col="gunmetal", mat="metal", tris=700, role="limb")
        sh = tube([T(kn), T(kn + (ft - kn) * 0.45 + d * 0.15), T(ft + A(0, 0.35, 0)), T(ft + A(0, 0.03, 0))], [0.13, 0.11, 0.07, 0.03], k=0.04)
        sh = sh | U(*(torus(0.12, 0.025).at(*T(kn + (ft - kn) * f)) for f in (0.15, 0.3)))
        claws = U(*(round_cone(T(ft + A(0, 0.25, 0)), T(ft + (d * math.cos(b) + A(0, 0, 0)) * 0.0 + A(0.28 * math.sin(a2), 0.02, 0.28 * math.cos(a2))), 0.05, 0.02)
                    for b, a2 in ((0, math.atan2(d[0], d[2]) + 0.0), (0, math.atan2(d[0], d[2]) + 2.1), (0, math.atan2(d[0], d[2]) - 2.1))))
        H.piece("Shin" + nm, "Knee" + nm, U(sh, claws) & plane((0, -1, 0), 0.0), col="primary", mat="metal", tris=700, role="foot")
    H.socket("mouth", (0, yc - 0.68, -2.1), "Ray2")
    H.socket("muzzle", (0, yc - 0.68, -2.1), "Ray2")
    H.socket("head", (0, yc + 1.2, 0), "Body")
    H.rig.update({"head": "Ray1", "legs": [{"hip": "Hip" + n, "knee": "Knee" + n, "phase": ph, "side": s_} for n, ph, s_ in (("B", 0.0, 1), ("R", 0.33, 1), ("L", 0.66, -1))]})
    wl = [("HipB", "KneeB", 0.0), ("HipR", "KneeR", 1 / 3), ("HipL", "KneeL", 2 / 3)]

    def idle(t):
        u = t / 3.0
        p = {}
        add(p, "Body", (0, 0.06 * math.sin(TAU * u * 2), 0, 0.02 * math.sin(TAU * u), 0.12 * math.sin(TAU * u * 0.5), 0.03 * math.sin(TAU * u)))
        for hip, knee, ph in wl:
            add(p, hip, (0, -0.06 * math.sin(TAU * u * 2), 0, 0, 0, 0))
        add(p, "Ray1", (0, 0, 0, 0.12 * math.sin(TAU * u), 0.5 * math.sin(TAU * u * 0.5 + 0.7), 0))
        add(p, "Ray2", (0, 0, 0, 0.15 * math.sin(TAU * u + 1), 0, 0))
        return p

    def move(t):
        u = t / 1.5
        p = {}
        _tri_walk(p, u, wl, 0.45, 0.2)
        add(p, "Body", (0, 0.1 * math.sin(TAU * u * 3), 0, -0.05, 0.06 * math.sin(TAU * u), 0.05 * math.sin(TAU * u * 3)))
        add(p, "Ray1", (0, 0, 0, 0.1 * math.sin(TAU * u * 3 + 1), 0.25 * math.sin(TAU * u), 0))
        return p

    def attack(t):
        s = t / 1.1
        w, st, rec = env(s, 0.4, (0.35, 0.85))
        p = {}
        add(p, "Body", (0, -0.35 * w, 0.15 * st, -0.1 * w + 0.08 * st, 0, 0))
        for hip, knee, ph in wl:
            add(p, hip, (0, 0.35 * w, 0, 0, 0, 0))
        jit = math.sin(TAU * s * 12) * st
        add(p, "Ray1", (0, 0, 0, -0.35 * w, 0, 0))
        add(p, "Ray2", (0, 0, 0.12 * st, -0.3 * w + 0.15 * st, 0, 0.05 * jit))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, -0.1 * k, 0.25 * k, 0.15 * k, 0, 0.1 * math.sin(t * 35) * k))
        add(p, "Ray1", (0, 0, 0, 0.4 * k, 0, 0))
        return p

    clips(H, idle, move, attack, hit, 5.6, idle_len=3.0, move_len=1.5, attack_len=1.1)
    return H


@hero("robot arm monster", "bots")
def robot_arm_monster():
    """An industrial robot arm that tore itself off the factory floor: a hazard-striped base on three short
    insect legs, a turntable, a big two-segment arm with hydraulic pistons and cable loops, a wrist camera eye and a
    giant three-finger grabber claw. Scuttles; its attack swings the arm down and snaps the claw shut."""
    H = OH("robot arm monster", plan="Insect", gait="scuttle", tags=["robot", "machine", "industrial"])
    H.preview = {"primary": "#F2B01E", "secondary": "#EF4444", "chrome": "#D5DCE3"}
    H.body((0, 1.0, 0))
    H.bone("Turret", "Body", (0, 1.3, 0))
    H.bone("Shoulder", "Turret", (0, 1.7, 0.25))
    H.bone("Elbow", "Shoulder", (0, 3.35, 0.55))
    H.bone("Wrist", "Elbow", (0, 3.0, -1.15))
    H.mbone("Finger#", "Wrist", (0.18, 2.72, -1.3))
    H.bone("Thumb", "Wrist", (0, 2.72, -1.0))
    legs = []
    for nm, a in (("B", 0.0), ("R", 2 * math.pi / 3), ("L", -2 * math.pi / 3)):
        hp, kn, ft, d = _leg_pts(a, 0.62, 0.95, 1.3, 1.4, 1.75)
        H.bone("Hip" + nm, "Body", T(hp))
        H.bone("Knee" + nm, "Hip" + nm, T(kn))
        legs.append((nm, hp, kn, ft, d))
    base = cylinder(0.85, 0.22, rr=0.08).at(0, 1.0, 0).su(cylinder(0.6, 0.12, rr=0.05).at(0, 0.75, 0), 0.08)
    for nm, hp, kn, ft, d in legs:
        base = base.su(sphere(0.2, T(hp)), 0.06)
    haz = _hazard(lambda P: (P[:, 0] + P[:, 2]) * 1.0 + P[:, 1], 3.0, region=lambda P: np.clip(1 - np.abs(P[:, 1] - 1.0) / 0.16, 0, 1))
    H.piece("Base", "Body", base, col="primary", mat="metal", tris=1000, res=128, role="body", pattern=haz)
    tt = cylinder(0.55, 0.1, rr=0.03).at(0, 1.3, 0).su(round_box(0.32, 0.32, 0.35, 0.08, (0, 1.62, 0.2)), 0.05)
    tt = tt | U(*(cylinder(0.12, 0.38, axis=0).at(0, 1.7, 0.25) for _ in (0,)))
    H.piece("TurretP", "Turret", tt, col="gunmetal", mat="metal", tris=700, role="body", pri=1.1)
    sh, el, wr = A(0, 1.7, 0.25), A(0, 3.35, 0.55), A(0, 3.0, -1.15)
    ua = U(round_cone(T(sh), T(el), 0.3, 0.24), sphere(0.32, T(el)), k=0.06)
    ua = ua.ss(U(*(round_box(0.32, 0.05, 0.05, 0.02).at(*T(sh + (el - sh) * f + A(0, 0, -0.27))) for f in (0.3, 0.5, 0.7))), 0.01)
    H.piece("UpperArm", "Shoulder", ua, col="primary", mat="metal", tris=1000, role="limb",
            pattern=_hazard(lambda P: P[:, 1] - P[:, 2] * 0.6, 3.5, region=lambda P: np.clip((P[:, 1] - 1.9) / 0.1, 0, 1) * np.clip((2.6 - P[:, 1]) / 0.1, 0, 1)))
    pist = U(*(U(capsule(T(sh + A(0.36 * sx, 0.1, 0.05)), T(sh + (el - sh) * 0.55 + A(0.36 * sx, 0, 0.05)), 0.07),
                 capsule(T(sh + (el - sh) * 0.5 + A(0.36 * sx, 0, 0.05)), T(el + A(0.33 * sx, -0.1, 0.05)), 0.04)) for sx in (1, -1)))
    cable = tube([T(sh + A(0, 0.2, 0.32)), T((sh + el) / 2 + A(0, 0, 0.55)), T(el + A(0, 0.1, 0.35))], [0.05, 0.05, 0.05], k=0.02)
    H.piece("Pistons", "Shoulder", U(pist, cable), col="chrome", mat="metal", tris=500, role="detail", pri=1.3)
    fa = U(round_cone(T(el), T(wr), 0.22, 0.15), cylinder(0.2, 0.1, axis=2, rr=0.03).at(*T(wr + A(0, 0.0, 0.1))), k=0.05)
    H.piece("Forearm", "Elbow", fa, col="primary", mat="metal", tris=800, role="limb")
    wrist = U(cylinder(0.22, 0.14, axis=1, rr=0.04).at(*T(wr + A(0, -0.12, -0.05))), sphere(0.17, T(wr)))
    H.piece("WristP", "Wrist", wrist, col="gunmetal", mat="metal", tris=600, role="head")
    H.prim("CamEye", "Wrist", "Ball", (0.14, 0.14, 0.14), T(wr + A(0, 0.06, -0.2)), col="secondary", mat="hard", glow=True, role="eye", pri=1.3)
    H.prim("CamHood", "Wrist", "Block", (0.22, 0.05, 0.12), T(wr + A(0, 0.15, -0.2)), col="gunmetal", mat="metal", role="detail", pri=1.6)
    fb = wr + A(0, -0.28, -0.15)
    for sx, nm in ((1, "R"), (-1, "L")):
        f0 = A(0.18 * sx, 2.72, -1.3)
        fg = tube([T(f0), T(f0 + A(0.15 * sx, -0.35, -0.1)), T(f0 + A(0.05 * sx, -0.7, -0.15)), T(f0 + A(-0.08 * sx, -0.8, -0.12))], [0.09, 0.08, 0.06, 0.03], k=0.03)
        H.piece("Finger" + nm + "P", "Finger" + nm, fg, col="gunmetal", mat="metal", tris=350, role="claw")
    th = tube([(0, 2.72, -1.0), (0, 2.4, -0.85), (0, 2.08, -0.98), (0, 1.98, -1.12)], [0.09, 0.08, 0.06, 0.03], k=0.03)
    H.piece("ThumbP", "Thumb", th, col="gunmetal", mat="metal", tris=350, role="claw")
    for nm, hp, kn, ft, d in legs:
        lg = U(sphere(0.14, T(hp)), capsule(T(hp), T(kn), 0.1), sphere(0.12, T(kn)))
        H.piece("LegU" + nm, "Hip" + nm, lg, col="gunmetal", mat="metal", tris=400, role="limb")
        sn = U(capsule(T(kn), T(ft + A(0, 0.12, 0)), 0.08), cone(0.14, 0.0, 0.08).rot(180, 0, 0).at(*T(ft + A(0, 0.06, 0))) if False else sphere(0.11, T(ft + A(0, 0.1, 0))))
        sn = U(sn, cylinder(0.15, 0.04, rr=0.02).at(*T(ft + A(0, 0.04, 0)))) & plane((0, -1, 0), 0.0)
        H.piece("LegL" + nm, "Knee" + nm, sn, col="primary", mat="metal", tris=350, role="foot")
    H.socket("mouth", T(wr + A(0, -0.9, -0.15)), "Wrist")
    H.socket("hand", T(wr + A(0, -0.9, -0.15)), "Wrist")
    H.socket("head", T(wr + A(0, 0.5, 0)), "Wrist")
    H.rig.update({"head": "Wrist", "legs": [{"hip": "Hip" + n, "knee": "Knee" + n, "phase": ph, "side": s_} for n, ph, s_ in (("B", 0.0, 1), ("R", 0.33, 1), ("L", 0.66, -1))]})
    wl = [("HipB", "KneeB", 0.0), ("HipR", "KneeR", 1 / 3), ("HipL", "KneeL", 2 / 3)]

    def claw(p, o):
        add(p, "FingerR", (0, 0, 0, 0, 0, 0.35 * o))
        add(p, "FingerL", (0, 0, 0, 0, 0, -0.35 * o))
        add(p, "Thumb", (0, 0, 0, -0.4 * o, 0, 0))

    def idle(t):
        u = t / 3.0
        p = {}
        add(p, "Turret", (0, 0, 0, 0, 0.35 * math.sin(TAU * u * 0.5), 0))
        add(p, "Shoulder", (0, 0, 0, 0.06 * math.sin(TAU * u), 0, 0))
        add(p, "Elbow", (0, 0, 0, 0.08 * math.sin(TAU * u + 0.8), 0, 0))
        add(p, "Wrist", (0, 0, 0, 0.12 * math.sin(TAU * u + 1.6), 0.4 * math.sin(TAU * u * 0.5 + 1), 0))
        claw(p, 0.4 + 0.4 * math.sin(TAU * u * 2))
        add(p, "Body", (0, 0.02 * math.sin(TAU * u * 2), 0, 0, 0, 0))
        return p

    def move(t):
        u = t / 0.8
        p = {}
        _tri_walk(p, u, wl, 0.3, 0.35)
        add(p, "Body", (0, 0.06 * abs(math.sin(TAU * u * 3)), 0, 0, 0.05 * math.sin(TAU * u), 0.04 * math.sin(TAU * u * 3)))
        add(p, "Shoulder", (0, 0, 0, -0.1, 0, 0))
        add(p, "Elbow", (0, 0, 0, 0.1 * math.sin(TAU * u * 3), 0, 0))
        claw(p, 0.6 + 0.3 * math.sin(TAU * u * 3))
        return p

    def attack(t):
        s = t / 1.0
        w, st, rec = env(s, 0.4, (0.35, 0.85))
        p = {}
        add(p, "Shoulder", (0, 0, 0, -0.35 * w + 0.75 * st, 0, 0))
        add(p, "Elbow", (0, 0, 0, -0.3 * w + 0.35 * st, 0, 0))
        add(p, "Wrist", (0, 0, 0, 0.3 * w + 0.2 * st, 0, 0))
        snap = ease((s - 0.55) / 0.1)
        claw(p, 1.0 * (w + st) * (1 - snap) - 0.15 * snap)
        add(p, "Body", (0, 0, -0.15 * st, 0, 0, 0))
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, 0.05 * k, 0.2 * k, 0.15 * k, 0, 0.1 * math.sin(t * 40) * k))
        add(p, "Shoulder", (0, 0, 0, -0.35 * k, 0, 0))
        add(p, "Wrist", (0, 0, 0, 0.4 * k, 0.3 * k, 0))
        claw(p, k)
        return p

    clips(H, idle, move, attack, hit, 3.8, idle_len=3.0, move_len=0.8, attack_len=1.0)
    return H


# ================================================================================================ chicken-legged hut
@hero("chicken-legged hut", "bots")
def chicken_legged_hut():
    """The witch's hut on giant chicken legs: an interlocking log cabin on a log platform, a shaggy thatched gable
    roof with a ridge, a crooked stone chimney puffing smoke, two glowing shuttered windows like eyes and a plank
    door like a mouth; underneath, two huge chicken legs with feathered drumsticks, scaly shanks, three splayed
    clawed toes forward and a spur toe behind. Strides like a bird, bobbing and swaying."""
    H = OH("chicken-legged hut", plan="Giant", gait="stomp", tags=["structure", "witch", "walker"])
    H.preview = {"primary": "#8A5A33", "secondary": "#C9A24A", "cream": "#EDE3D0"}
    H.body((0, 2.45, 0))
    H.bone("Hut", "Body", (0, 2.55, 0))
    H.bone("Smoke", "Hut", (0.48, 4.75, 0.3))
    H.mbone("Hip#", "Body", (0.42, 2.38, 0.08))
    H.mbone("Hock#", "Hip#", (0.5, 1.32, 0.42))
    H.mbone("Toe#", "Hock#", (0.5, 0.14, 0.02))
    logs = None
    for i in range(5):
        y = 2.68 + i * 0.2
        for sz in (1, -1):
            logs = U(logs, capsule((-0.92, y, 0.6 * sz), (0.92, y, 0.6 * sz), 0.105))
        for sx in (1, -1):
            logs = U(logs, capsule((0.76 * sx, y + 0.1, -0.74), (0.76 * sx, y + 0.1, 0.74), 0.105))
    logs = logs.noise(0.01, 7, 3)
    logs = logs.ss(round_box(0.22, 0.34, 0.2, 0.03, (0, 2.95, -0.62)), 0.01)  # door opening
    logs = logs.ss(round_box(0.16, 0.13, 0.2, 0.02, (0.5, 3.28, -0.62)).mirror_x(), 0.01)  # windows
    H.piece("Logs", "Hut", logs, col="primary", mat="wood", tris=1900, res=140, role="body",
            pattern=stripes(lambda P: P[:, 0] * 0.5 + P[:, 2] * 0.5, 9.0, width=0.15, depth=0.2))
    plat = round_box(1.05, 0.1, 0.85, 0.06, (0, 2.5, 0)).noise(0.01, 6, 4)
    gable = None
    for sz in (1, -1):
        g = SDF(lambda p, sz=sz: np.maximum(np.maximum(np.abs(p[:, 2] - 0.6 * sz) - 0.05, (p[:, 1] - 3.62) + np.abs(p[:, 0]) * 0.85 - 0.75), 3.62 - p[:, 1]))
        gable = U(gable, g)
    H.piece("Frame", "Hut", U(plat, gable), col="darkWood", mat="wood", tris=600, role="detail", pri=1.2,
            pattern=stripes(lambda P: P[:, 0], 6.0, width=0.1, depth=0.3))

    def roof_f(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        top = 4.55 - np.abs(x) * 0.95 + 0.02 * np.sin(z * 9 + x * 4)
        d_out = y - top
        d_in = (top - 0.22) - y
        d = np.maximum(d_out, d_in)
        d = np.maximum(d, np.abs(z) - 0.92 - 0.04 * np.sin(x * 11))
        d = np.maximum(d, 3.48 - y - 0.06 * np.sin(z * 13))
        return d * 0.7

    roof = SDF(roof_f).su(capsule((0, 4.55, -0.95), (0, 4.55, 0.95), 0.09), 0.05).noise(0.015, 10, 6)
    H.piece("Thatch", "Hut", roof, col="secondary", mat="cloth", tris=1200, res=136, role="head",
            pattern=stripes(lambda P: P[:, 2] * 0.3 + P[:, 1], 14.0, width=0.3, depth=0.25))
    ch = U(round_box(0.16, 0.45, 0.16, 0.04, (0.48, 4.3, 0.3)).noise(0.02, 9, 7), round_box(0.2, 0.06, 0.2, 0.02, (0.48, 4.72, 0.3)))
    H.piece("Chimney", "Hut", ch, col="stone", mat="stone", tris=600, role="detail", pri=1.3,
            pattern=spots(0.1, 0.035, depth=0.35, seed=9))
    for i, (dy, r, dx) in enumerate(((0.2, 0.2, 0.0), (0.5, 0.26, 0.1), (0.85, 0.3, 0.25))):
        H.prim(f"Puff{i}", "Smoke", "Ball", (r * 2, r * 2, r * 2), (0.48 + dx, 4.75 + dy, 0.3 + dx * 0.4), col="light", mat="hard", tr=0.35 + 0.15 * i, role="smoke", pri=2.0 + i * 0.2)
    H.prim("Door", "Hut", "Block", (0.42, 0.66, 0.06), (0, 2.95, -0.56), col="darkWood", mat="wood", role="mouth", pri=1.2)
    H.prim("DoorRing", "Hut", "Ball", (0.07, 0.07, 0.07), (0.13, 2.95, -0.6), col="steel", mat="metal", role="detail", pri=2.0)
    for sx, nm in ((1, "R"), (-1, "L")):
        H.prim("Window" + nm, "Hut", "Block", (0.3, 0.24, 0.05), (0.5 * sx, 3.28, -0.57), col="eyeGlow", mat="hard", glow=True, role="eye", pri=1.2)
        H.prim("Shutter" + nm, "Hut", "Block", (0.14, 0.3, 0.04), (0.5 * sx + 0.24 * sx, 3.28, -0.66), rot=(0, 0.5 * sx, 0), col="darkWood", mat="wood", role="detail", pri=1.6)
        H.prim("Brow" + nm, "Hut", "Block", (0.38, 0.06, 0.08), (0.5 * sx, 3.45, -0.66), rot=(0, 0, -0.18 * sx), col="darkWood", mat="wood", role="brow", pri=1.7)
    for sx, nm in ((1, "R"), (-1, "L")):
        hp, hk, tf = A(0.42 * sx, 2.38, 0.08), A(0.5 * sx, 1.32, 0.42), A(0.5 * sx, 0.14, 0.02)
        th = round_cone(T(hp + A(0, 0.05, 0)), T(hk), 0.36, 0.14).noise(0.035, 9, 10 + (sx > 0))
        for j in range(6):
            a = j / 6 * TAU
            q = hp + (hk - hp) * 0.62 + A(0.2 * math.sin(a), 0, 0.2 * math.cos(a))
            th = th.su(round_cone(T(q), T(q + A(0.06 * math.sin(a), -0.32, 0.06 * math.cos(a))), 0.08, 0.02), 0.04)
        H.piece("Drum" + nm, "Hip" + nm, th, col="cream", mat="fur", tris=850, role="limb")
        sk = round_cone(T(hk), T(tf + A(0, 0.06, 0)), 0.13, 0.09).su(sphere(0.15, T(hk)), 0.05)
        H.piece("Shank" + nm, "Hock" + nm, sk, col="beak", mat="skin", tris=600, role="limb",
                pattern=stripes(lambda P: P[:, 1], 9.0, width=0.2, depth=0.35))
        toes = sphere(0.14, T(tf + A(0, 0.02, 0)))
        for a, ln in ((-0.5, 0.62), (0.0, 0.72), (0.5, 0.62), (math.pi, 0.35)):
            d = A(math.sin(a) * sx, 0, -math.cos(a))
            e = tf + d * ln + A(0, -0.06, 0)
            toes = toes.su(tube([T(tf + A(0, 0.02, 0)), T(tf + d * ln * 0.55 + A(0, 0.0, 0)), T(e)], [0.09, 0.07, 0.05], k=0.03), 0.04)
            toes = toes | cone(0.045, 0.0, 0.1, axis=2).rot(0, 0, 0).rot(0, math.degrees(math.atan2(-d[0], -d[2])) + 180, 0).at(*T(e + d * 0.08))
        toes = toes & plane((0, -1, 0), 0.0)
        H.piece("Toes" + nm, "Toe" + nm, toes, col="beak", mat="skin", tris=700, role="foot")
    H.socket("mouth", (0, 2.95, -0.7), "Hut")
    H.socket("head", (0, 4.9, 0), "Hut")
    H.socket("exhaust", (0.48, 4.9, 0.3), "Hut")
    H.rig.update({"head": "Hut", "legs": [{"hip": "HipR", "knee": "HockR", "phase": 0.0, "side": 1}, {"hip": "HipL", "knee": "HockL", "phase": 0.5, "side": -1}]})

    def smoke(p, u, k=1.0):
        add(p, "Smoke", (0.05 * math.sin(TAU * u), 0.15 * (u % 1.0) * k, 0, 0, 0, 0.1 * math.sin(TAU * u)))

    def idle(t):
        u = t / 3.0
        p = {}
        add(p, "Hut", (0, 0.03 * math.sin(TAU * u), 0, 0.03 * math.sin(TAU * u + 1), 0.08 * math.sin(TAU * u * 0.5), 0.03 * math.sin(TAU * u)))
        for sg, nm in ((1, "R"), (-1, "L")):
            add(p, "Hip" + nm, (0, 0, 0, 0.12 + 0.03 * math.sin(TAU * u), 0, 0))
            add(p, "Hock" + nm, (0, 0, 0, -0.25 - 0.06 * math.sin(TAU * u), 0, 0))
            add(p, "Toe" + nm, (0, 0, 0, 0.13 + 0.03 * math.sin(TAU * u), 0, 0))
        add(p, "Body", (0, -0.08 - 0.03 * math.sin(TAU * u), 0, 0, 0, 0))
        smoke(p, u)
        return p

    def move(t):
        u = t / 1.1
        ph = TAU * u
        p = {}
        add(p, "Body", (0, 0.12 * abs(math.sin(ph)) - 0.06, 0, -0.06, 0.06 * math.sin(ph), 0.08 * math.sin(ph)))
        add(p, "Hut", (0, 0, 0, 0.05 * math.sin(ph * 2), 0, -0.05 * math.sin(ph)))
        for sg, nm in ((1, "R"), (-1, "L")):
            ph2 = ph + (0 if sg > 0 else math.pi)
            sw = math.sin(ph2)
            lift = max(0.0, math.cos(ph2))
            add(p, "Hip" + nm, (0, 0, 0, 0.5 * sw + 0.15, 0, 0))
            add(p, "Hock" + nm, (0, 0, 0, -0.35 - 0.6 * lift, 0, 0))
            add(p, "Toe" + nm, (0, 0, 0, -0.5 * sw + 0.2 + 0.5 * lift, 0, 0))
        smoke(p, u, 1.5)
        return p

    def attack(t):
        s = t / 1.1
        w, st, rec = env(s, 0.4, (0.35, 0.85))
        p = {}
        add(p, "Body", (0, 0.3 * w, 0.1 * w - 0.3 * st, 0.15 * w - 0.2 * st, 0, 0.1 * w))
        add(p, "HipR", (0, 0, 0, 1.1 * w - 0.2 * st, 0, 0))
        add(p, "HockR", (0, 0, 0, -1.0 * w + 0.6 * st, 0, 0))
        add(p, "ToeR", (0, 0, 0, 0.3 * w - 0.6 * st, 0, 0))
        add(p, "HipL", (0, 0, 0, -0.2 * w, 0, 0))
        add(p, "Hut", (0, 0, 0, -0.1 * st, 0, 0.05 * math.sin(TAU * s * 8) * st))
        smoke(p, s, 2.0)
        return scaled(p, rec)

    def hit(t):
        k = hitk(t)
        p = {}
        add(p, "Body", (0, -0.1 * k, 0.25 * k, 0.15 * k, 0, 0.1 * math.sin(t * 35) * k))
        add(p, "Hut", (0, 0, 0, 0.1 * k, 0, 0.12 * k))
        return p

    clips(H, idle, move, attack, hit, 5.0, idle_len=3.0, move_len=1.1, attack_len=1.1)
    return H
