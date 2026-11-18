"""Boats (water mounts): rowboat, canoe, speedboat, sailboat, super yacht, ship (galleon), pirate ship, viking longship,
paddle steamer, tugboat, fishing boat, raft, gondola, submarine, jet ski, hovercraft, paddle boat (swan),
battleship, cruise ship.

Hard-surface direct meshes (tools/meshgen/direct.py via airsea_kit): lofted hull shells with real thickness (clinker
strakes on the wooden boats), plank decks, rails, cabins with separate glass, masts and billowing sails on bones,
oars / paddle wheels / propellers on bones. Everything floats: gait "swim" (bob and roll in Idle, bow pitch in Move).
Model space: -Z is the bow, keel on y = 0, a seated rider ~ 3 studs tall (human 5.5).
"""
import math

import numpy as np

from sdf import ellipsoid, sphere as ssphere, capsule, round_cone, tube as stube, round_box, plane  # noqa: F401
from kit import Hero, hero
import airsea_kit as A
from airsea_kit import HullSpec, dpiece, dmpiece, box, cyl, rev, tube, merge, xform, mirror, sphere

TAU = 2 * math.pi
ROPE = [0.78, 0.68, 0.48]
TINT = [0.13, 0.17, 0.22]       # dark tinted glass
BLACKSAIL = [0.14, 0.14, 0.16]


def waterline(y0, y1, a=0.62):
    """Darker anti-fouling below the waterline (pattern mask)."""
    def f(P):
        return np.where(P[:, 1] < y0, a, np.where(P[:, 1] < y1, a + (1 - a) * (P[:, 1] - y0) / max(y1 - y0, 1e-6), 1.0))
    return f


def side_band(sp, f0, f1, off=0.025, t0=0.05, t1=1.0, n=22, depth=0.06):
    """A painted band standing proud of the hull's outer skin between normalised heights f0 < f1 (both sides)."""
    rings = []
    for t in np.linspace(t0, t1, n):
        o = sp.outer(t, 81)[:41]  # gunwale -> keel (right)
        yb, yt = sp.keel(t), sp.top(t)
        f = (o[:, 1] - yb) / max(yt - yb, 1e-6)
        ys, xs = f[::-1], o[::-1, 0]
        x0, x1 = np.interp(f0, ys, xs), np.interp(f1, ys, xs)
        y0, y1 = yb + f0 * (yt - yb), yb + f1 * (yt - yb)
        z = sp.z(t)
        rings.append(np.array([[x1 + off, y1, z], [x0 + off, y0, z], [x0 - depth, y0, z], [x1 - depth, y1, z]]))
    m = A.loft(rings, "fan", "fan", crease=40)
    return merge(m, mirror(m))


def windows_x(x, y, zs, w, h, th=0.06, r=0.03):
    """Window panes on a wall facing +X at x (both sides)."""
    ms = [box((th, h, w), (x, y, z), r=r) for z in zs]
    m = merge(*ms)
    return merge(m, mirror(m))


def portholes(H, bone, x, y, zs, d=0.32, name="Port"):
    """Round dark portholes (one prim pair each would blow the part budget: one merged mesh both sides)."""
    ms = []
    for z in zs:
        ms.append(cyl(d / 2, 0.06, (x, y, z), axis=0, segs=12, bevel=0.015))
    m = merge(*ms)
    dpiece(H, name, bone, merge(m, mirror(m)), col=TINT, mat="glass", role="detail", pri=1.8)


def flag(c0, w, h, n=8, amp=0.12, phase=0.0):
    """Flag hanging from a pole at c0 (top inner corner), flying toward +Z."""
    c0 = np.asarray(c0, float)
    return A.quad_sheet(c0, c0 + (0, 0, w), c0 + (0, -h, 0), c0 + (0, -h, w), nt=n, nu=4, thick=0.02,
                        wave=lambda t, u: (amp * math.sin(TAU * t * 1.2 + phase) * t, 0, 0))


def rail_posts(pts, h, r=0.04, every=1):
    ms = []
    for i, p in enumerate(pts):
        if i % every == 0:
            ms.append(tube([[p[0], p[1], p[2]], [p[0], p[1] + h, p[2]]], r, 5))
    top = [[p[0], p[1] + h, p[2]] for p in pts]
    ms.append(tube(top, r * 1.1, 6))
    return merge(*ms)


def deck_rail(sp, y_of, t0, t1, h=0.6, inset=0.08, n=12, r=0.035):
    """Railing (posts + top rail) along both gunwales from t0 to t1. y_of(t) gives the deck height at the rail."""
    pts = [[sp.beam(t) - inset, y_of(t), sp.z(t)] for t in np.linspace(t0, t1, n)]
    m = rail_posts(pts, h, r)
    return merge(m, mirror(m))


def mast(x, y0, y1, z, r0, r1, segs=10):
    return cyl(r0, y1 - y0, (x, (y0 + y1) / 2, z), axis=1, segs=segs, r2=r1)


def yard(y, z, half, r=0.09):
    return tube([[-half, y, z], [0, y + 0.05, z], [half, y, z]], [r * 0.6, r, r * 0.6], 8)


def square_sail(y_top, y_bot, z, half_top, half_bot, bulge=1.0, nt=7, nu=7):
    """Square sail hung from a yard (at z), bellying forward (-Z)."""
    return A.quad_sheet((-half_top, y_top, z + 0.05), (half_top, y_top, z + 0.05), (-half_bot, y_bot, z + 0.1), (half_bot, y_bot, z + 0.1),
                        nt=nt, nu=nu, bulge=(0, 0, -bulge), thick=0.04)


def tyre(R, r, pos, axis=0, segs=14, rsegs=8):
    """Torus (fenders, life rings, lashings) about `axis` through pos."""
    ang = np.linspace(0, TAU, rsegs, endpoint=False)
    prof = [(r * math.sin(a), R + r * math.cos(a)) for a in ang]
    rings = []
    a = [0, 1, 2]
    a.remove(axis)
    th = np.linspace(0, TAU, segs, endpoint=False)
    for t_, rad in prof + [prof[0]]:
        ring = np.zeros((segs, 3))
        ring[:, axis] = t_
        ring[:, a[0]] = rad * np.cos(th)
        ring[:, a[1]] = rad * np.sin(th)
        rings.append(ring)
    m = A.loft(rings, None, None, crease=70)
    return direct_move(m, pos)


def direct_move(m, pos):
    import direct
    return direct.moved(m, pos)


def oar_mesh(pivot, out_dir_deg, inboard, outboard, r=0.06, blade=(1.1, 0.4), droop=-18):
    """Oar through a pivot: handle inboard, blade outboard along +X (rotated about Y by out_dir_deg)."""
    a = math.radians(droop)
    d = np.array([math.cos(a), math.sin(a), 0.0])
    yaw = math.radians(out_dir_deg)
    Ry = np.array([[math.cos(yaw), 0, math.sin(yaw)], [0, 1, 0], [-math.sin(yaw), 0, math.cos(yaw)]])
    d = Ry @ d
    p = np.asarray(pivot, float)
    p0, p1 = p - d * inboard, p + d * outboard
    sh = tube([p0, p0 + d * 0.3, p1 - d * blade[0] * 0.9, p1 - d * blade[0] * 0.7], [r, r * 1.1, r * 1.1, r * 0.9], 7)
    bl = box((blade[0], 0.05, blade[1]), (0, 0, 0), r=0.02)
    bl = xform(bl, tuple(p1 - d * blade[0] * 0.45), (0, out_dir_deg * 0 , math.degrees(a)))
    if out_dir_deg:
        bl = xform(box((blade[0], 0.05, blade[1]), (0, 0, 0), r=0.02), (0, 0, 0), (0, 0, math.degrees(a)))
        bl = xform(bl, tuple(p1 - d * blade[0] * 0.45), (0, -out_dir_deg, 0))
    return sh, bl


def common(H, seat_pos, seat_size, front_z, back_z, top_y, muzzle=None):
    A.mount(H, "Seat", seat_pos, seat_size)
    H.socket("head", (0, top_y, 0), "Body")
    H.socket("mouth", (0, seat_pos[1], front_z), "Body")
    H.socket("exhaust", (0, seat_pos[1] * 0.6, back_z), "Body")
    if muzzle is not None:
        H.socket("muzzle", muzzle, "Body")


def V(hid, gait="swim"):
    return Hero(hid, plan="Vehicle", gait=gait, tags=["vehicle", "boat"])


# ================================================================================================ rowboat
@hero("rowboat", "boats")
def rowboat():
    H = V("rowboat")
    H.preview = {"primary": "#3E7CB1", "secondary": "#F2E8D5"}
    sp = HullSpec(10.0, 3.8, 1.45, bow=0.25, stern=0.15, transom=0.55, bow_rise=0.7, stern_rise=0.15, sheer_bow=0.32,
                  sheer_stern=0.12, p_bow=1.5, p_mid=2.3, p_stern=2.2, flare=0.22, maxat=0.55, strakes=5, strake_step=0.06)
    H.body((0, 0.8, 0))
    dpiece(H, "Hull", "Body", A.hull_shell(sp, th=0.1, n=24, nl=26), col="primary", mat="wood", fallback="Ellipsoid", pattern=waterline(0.25, 0.45))
    dpiece(H, "Gunwale", "Body", A.rail(sp, r=0.075, n=20), col="secondary", mat="wood", role="detail")
    dpiece(H, "Band", "Body", side_band(sp, 0.7, 0.8, t0=0.08), col="secondary", mat="hard", role="detail")
    kp = [[0, sp.keel(t) - 0.04, sp.z(t)] for t in np.linspace(0.02, 1.0, 12)]
    dpiece(H, "Keel", "Body", tube(kp, 0.08, 6), col="darkWood", mat="wood", role="detail")
    fy = 0.32
    dpiece(H, "Floor", "Body", A.planks(0.8, -3.2, 4.2, fy, n=5, gap=0.06, th=0.05, width_fn=lambda z: sp.half_width(z, fy + 0.03, 0.13)), col="wood", mat="wood", role="detail")
    tw = []
    for z in (-2.6, 2.55):
        w = sp.half_width(z, 0.9, 0.11)
        tw.append(box((2 * w * 0.98, 0.1, 0.7), (0, 0.95, z), r=0.03))
    dpiece(H, "Thwarts", "Body", merge(*tw, box((0.12, 0.6, 0.12), (0, 0.65, -2.6)), box((0.12, 0.6, 0.12), (0, 0.65, 2.55))), col="wood", mat="wood", role="detail")
    wseat = sp.half_width(0.2, 0.92, 0.11)
    dpiece(H, "Seat", "Body", merge(box((2 * wseat * 0.98, 0.12, 0.85), (0, 0.98, 0.2), r=0.035), box((0.14, 0.62, 0.14), (0, 0.66, 0.2))),
           col="secondary", mat="wood", role="detail")
    dpiece(H, "Coil", "Body", merge(tyre(0.22, 0.06, (0, fy + 0.1, -3.3), axis=1), tyre(0.17, 0.06, (0, fy + 0.2, -3.3), axis=1),
                                    tube([[0, fy + 0.25, -3.3], [0, sp.top(0.04) - 0.1, sp.z(0.04) + 0.1], [0, sp.top(0.02) + 0.05, sp.z(0.02)]], 0.04, 6)),
           col=ROPE, mat="cloth", role="detail")
    zo = 0.0
    wo = sp.beam(sp.t_of(zo))
    yo = sp.top(sp.t_of(zo)) + 0.12
    H.mbone("Oar#", "Body", (wo, yo, zo))
    lock = merge(cyl(0.05, 0.3, (wo, yo - 0.05, zo), axis=1, segs=8), tube([[wo, yo - 0.02, zo - 0.14], [wo, yo + 0.14, zo - 0.12], [wo, yo + 0.16, zo], [wo, yo + 0.14, zo + 0.12], [wo, yo - 0.02, zo + 0.14]], 0.03, 6, False))
    dmpiece(H, "Lock#", "Body", lock, col="metal", mat="metal", role="detail", pri=2)
    sh, bl = oar_mesh((wo, yo, zo), 0, 1.6, 3.6, r=0.065, blade=(1.3, 0.42))
    dmpiece(H, "OarShaft#", "Oar#", sh, col="wood", mat="wood", role="limb")
    dmpiece(H, "OarBlade#", "Oar#", bl, col="secondary", mat="wood", role="detail")
    dpiece(H, "Lantern", "Body", merge(cyl(0.05, 0.8, (0, 1.35, 3.85), axis=1, segs=8), box((0.3, 0.35, 0.3), (0, 1.9, 3.85), r=0.04)), col="darkWood", mat="wood", role="detail")
    H.prim("LanternGlass", "Body", "Block", (0.22, 0.24, 0.22), (0, 1.9, 3.85), col="glow", mat="glass", tr=0.15, glow=True, role="light", pri=2.5)
    common(H, (0, 1.05, 0.2), (2.2, 0.15, 0.85), -5.0, 5.0, 2.2)

    def extra(name, u, pose):
        if name in ("Move", "Attack"):
            ph = TAU * u * (2 if name == "Attack" else 1)
            sweep, lift = 0.55 * math.sin(ph), 0.18 * math.cos(ph)
            A._add(pose, "OarR", (0, 0, 0, 0, sweep, -lift))
            A._add(pose, "OarL", (0, 0, 0, 0, -sweep, lift))
        elif name == "Idle":
            A._add(pose, "OarR", (0, 0, 0, 0, 0.05 * math.sin(TAU * u), 0))
            A._add(pose, "OarL", (0, 0, 0, 0, -0.05 * math.sin(TAU * u), 0))

    A.boat_clips(H, extra=extra)
    return H


# ================================================================================================ canoe
@hero("canoe", "boats")
def canoe():
    H = V("canoe")
    H.preview = {"primary": "#D84315", "secondary": "#FFCC80"}
    sp = HullSpec(12.0, 2.4, 1.0, bow=0.35, stern=0.35, transom=0.0, bow_rise=0.45, stern_rise=0.45, sheer_bow=0.9, sheer_stern=0.9,
                  p_bow=1.5, p_mid=2.3, p_stern=1.5, flare=0.12, maxat=0.5)
    H.body((0, 0.6, 0))
    dpiece(H, "Hull", "Body", A.hull_shell(sp, th=0.07, n=22, nl=30), col="primary", mat="wood", fallback="Ellipsoid", pattern=waterline(0.15, 0.3, 0.75))
    dpiece(H, "Gunwale", "Body", A.rail(sp, r=0.06, t0=0.0, t1=1.0, n=26), col="wood", mat="wood", role="detail")
    dpiece(H, "Band", "Body", side_band(sp, 0.62, 0.7, t0=0.08, t1=0.92), col="secondary", role="detail")
    # end decks (small triangular caps) + carry handles
    ends = []
    for t0, t1 in ((0.015, 0.1), (0.9, 0.985)):
        rings = []
        for t in np.linspace(t0, t1, 6):
            w = max(sp.beam(t) - 0.05, 0.01)
            y = sp.top(t) - 0.04
            rings.append(np.array([[w, y - 0.04, sp.z(t)], [-w, y - 0.04, sp.z(t)], [-w, y + 0.03, sp.z(t)], [w, y + 0.03, sp.z(t)]]))
        ends.append(A.loft(rings, "fan", "fan", crease=40))
    dpiece(H, "EndDecks", "Body", merge(*ends), col="wood", mat="wood", role="detail")
    # ribs inside
    ribs = []
    for z in np.linspace(-4.2, 4.2, 9):
        t = sp.t_of(z)
        o = sp.outer(t, 15)
        pts = [[q[0] * 0.93, q[1] + 0.07, q[2]] for q in o[1:-1]]
        ribs.append(tube(pts, 0.035, 5, closed_ends=True))
    dpiece(H, "Ribs", "Body", merge(*ribs), col="wood", mat="wood", role="detail")
    seats = []
    for z, y in ((-3.6, 0.62), (0.0, 0.66)):
        w = sp.half_width(z, y, 0.08)
        seats.append(box((2 * w, 0.07, 0.5), (0, y, z), r=0.02))
    dpiece(H, "Thwarts", "Body", merge(*seats), col="secondary", mat="cloth", role="detail")
    w = sp.half_width(3.4, 0.6, 0.08)
    dpiece(H, "Seat", "Body", merge(box((2 * w, 0.09, 0.62), (0, 0.6, 3.4), r=0.03), box((2 * w * 0.8, 0.5, 0.08), (0, 0.85, 3.75), r=0.03, rot=(-12, 0, 0))),
           col="secondary", mat="cloth", role="detail")
    # cargo: a rolled dry bag
    dpiece(H, "Pack", "Body", merge(rev([(-0.55, 0), (-0.5, 0.3), (0.0, 0.34), (0.5, 0.3), (0.62, 0.12), (0.7, 0)], axis=0, segs=12, pos=(0, 0.5, -1.6)),
                                    tyre(0.33, 0.03, (-0.25, 0.5, -1.6), axis=0), tyre(0.33, 0.03, (0.25, 0.5, -1.6), axis=0)), col=[0.2, 0.45, 0.35], mat="cloth", role="detail")
    # paddle held at the right side
    H.bone("Paddle", "Body", (0.6, 1.6, 2.9))
    pp = [(0.55, 2.4, 2.75), (1.25, -0.2, 3.05)]
    sh = tube([pp[0], pp[1]], 0.05, 8)
    grip = box((0.3, 0.09, 0.09), pp[0], r=0.03, rot=(0, 0, 15))
    bl = A.quad_sheet((1.08, 0.3, 2.85), (1.42, -0.95, 3.0), (1.08, 0.3, 3.3), (1.42, -0.95, 3.45), nt=5, nu=4, thick=0.03)
    dpiece(H, "PaddleP", "Paddle", merge(sh, grip, bl), col="wood", mat="wood", role="limb")
    common(H, (0, 0.72, 3.35), (1.6, 0.12, 0.6), -6.0, 6.0, 1.8)

    def extra(name, u, pose):
        if name in ("Move", "Attack"):
            ph = TAU * u * (2 if name == "Attack" else 1)
            A._add(pose, "Paddle", (0, 0.15 * math.cos(ph), 0, 0.5 * math.sin(ph), 0, 0.12 * max(0, math.cos(ph))))
        else:
            A._add(pose, "Paddle", (0, 0, 0, 0.06 * math.sin(TAU * u), 0, 0))

    A.boat_clips(H, extra=extra)
    return H


# ================================================================================================ speedboat
@hero("speedboat", "boats")
def speedboat():
    H = V("speedboat")
    H.preview = {"primary": "#E53935", "secondary": "#F5F5F5"}
    sp = HullSpec(11.0, 3.7, 1.6, bow=0.55, stern=0.2, transom=0.88, bow_rise=0.9, stern_rise=0.0, sheer_bow=0.18, sheer_stern=0.0,
                  p_bow=1.15, p_mid=1.5, p_stern=1.7, flare=0.08, maxat=0.62, deadrise=0.12)
    H.body((0, 0.9, 0))
    floor = 0.75
    dpiece(H, "Hull", "Body", A.hull_shell(sp, th=0.1, n=24, nl=26, floor=floor), col="primary", mat="hard", fallback="Ellipsoid",
           pattern=waterline(0.35, 0.5, 0.7))
    dpiece(H, "Stripe", "Body", side_band(sp, 0.55, 0.68, t0=0.1, t1=1.0), col="secondary", role="detail")
    # foredeck: crowned slab over the bow third
    rings = []
    for t in np.linspace(0.0, 0.42, 12):
        w = max(sp.beam(t) - 0.02, 0.01)
        y = sp.top(t)
        xs = np.linspace(-w, w, 9)
        top = [[x, y + 0.03 + 0.18 * (1 - (x / max(w, 1e-3)) ** 2) * min(1, t * 6), sp.z(t)] for x in xs]
        bot = [[x, y - 0.12, sp.z(t)] for x in xs[::-1]]
        rings.append(np.array(top + bot))
    dpiece(H, "Deck", "Body", A.loft(rings, None, "fan", crease=35), col="secondary", mat="hard", role="detail")
    # windscreen: raked wraparound glass with a chrome frame
    zw = sp.z(0.42) + 0.15
    yw = sp.top(0.42) + 0.1
    w = sp.beam(0.44) - 0.05
    gl = A.quad_sheet((-w, yw, zw), (w, yw, zw), (-w * 0.92, yw + 0.75, zw + 0.55), (w * 0.92, yw + 0.75, zw + 0.55), nt=9, nu=3, bulge=(0, 0, -0.35), thick=0.03)
    dpiece(H, "Windshield", "Body", gl, col="glass", mat="glass", tr=0.35, role="glass", pri=1.5)
    frame = tube([[-w * 0.92, yw + 0.77, zw + 0.55], [0, yw + 0.77, zw + 0.2], [w * 0.92, yw + 0.77, zw + 0.55]], 0.04, 6)
    dpiece(H, "Frame", "Body", merge(frame, deck_rail(sp, lambda t: sp.top(t), 0.05, 0.3, h=0.25, inset=0.15, n=6, r=0.03)), col="chrome", mat="metal", role="detail")
    # cockpit: dash, wheel, two bucket seats (driver = Seat), rear bench
    dpiece(H, "Dash", "Body", box((2 * w * 0.9, 0.5, 0.5), (0, floor + 0.55, zw + 0.45), r=0.08), col="dark", role="detail")
    dpiece(H, "Wheel", "Body", merge(tyre(0.25, 0.035, (0.75, floor + 1.0, zw + 0.75), axis=2), cyl(0.04, 0.4, (0.75, floor + 0.9, zw + 0.6), axis=2)), col="black", role="detail", pri=2)

    def bucket(x, z):
        return merge(box((0.95, 0.3, 0.9), (x, floor + 0.35, z), r=0.12), box((0.95, 0.95, 0.25), (x, floor + 0.9, z + 0.42), r=0.12, rot=(-12, 0, 0)))
    dpiece(H, "Seat", "Body", bucket(0.75, zw + 1.6), col="secondary", mat="hard", role="detail")
    dpiece(H, "Seats2", "Body", merge(bucket(-0.75, zw + 1.6), box((2 * sp.half_width(3.6, 1.2, 0.15), 0.35, 1.0), (0, floor + 0.35, 3.7), r=0.12),
                                      box((2 * sp.half_width(4.3, 1.4, 0.15), 0.8, 0.3), (0, floor + 0.8, 4.35), r=0.12)), col="secondary", role="detail")
    # twin outboards
    mz = sp.z(1.0) + 0.25
    H.mbone("Motor#", "Body", (0.8, sp.top(1.0), mz))
    eng = merge(box((0.6, 0.85, 0.8), (0.8, sp.top(1.0) + 0.35, mz + 0.35), r=0.18), box((0.22, 1.5, 0.35), (0.8, sp.top(1.0) - 0.75, mz + 0.35), r=0.08),
                rev([(-0.35, 0), (-0.3, 0.14), (0.25, 0.14), (0.35, 0)], axis=2, segs=10, pos=(0.8, 0.2, mz + 0.3)))
    dmpiece(H, "Motor#", "Motor#", eng, col="black", mat="hard", role="detail")
    H.mbone("Prop#", "Motor#", (0.8, 0.2, mz + 0.7))
    dmpiece(H, "Prop#", "Prop#", A.prop(3, 0.32, 0.18, axis="z", pos=(0.8, 0.2, mz + 0.72), thick=0.025), col="metal", mat="metal", role="detail")
    H.prim("Light", "Body", "Ball", (0.18, 0.18, 0.18), (0, sp.top(0.05) + 0.25, sp.z(0.05)), col="red", glow=True, role="light", pri=2.5)
    common(H, (0.75, floor + 0.55, zw + 1.6), (0.95, 0.15, 0.9), -6.0, 6.2, 3.0)
    spins = [("PropR", "z", 1, TAU / 3), ("PropL", "z", -1, TAU / 3)]

    def extra(name, u, pose):
        if name == "Move":
            A._add(pose, "Body", (0, 0.15, 0, 0.08, 0, 0))

    A.boat_clips(H, extra=extra, spinners=spins)
    return H


# ================================================================================================ sailboat
@hero("sailboat", "boats")
def sailboat():
    H = V("sailboat")
    H.preview = {"primary": "#F5F5F5", "secondary": "#1E88E5"}
    ky = 1.3
    sp = HullSpec(12.0, 3.8, 1.5, bow=0.45, stern=0.2, transom=0.6, bow_rise=0.7, stern_rise=0.35, sheer_bow=0.3, sheer_stern=0.05,
                  p_bow=1.5, p_mid=2.4, p_stern=2.6, flare=0.1, maxat=0.55, keel_y=ky)
    H.body((0, ky + 0.8, 0))
    deck = ky + 1.25
    dpiece(H, "Hull", "Body", A.hull_shell(sp, th=0.1, n=24, nl=26, floor=deck), col="primary", mat="hard", fallback="Ellipsoid", pattern=waterline(ky + 0.2, ky + 0.35, 0.7))
    dpiece(H, "Stripe", "Body", side_band(sp, 0.6, 0.7, t0=0.06), col="secondary", role="detail")
    dpiece(H, "Deck", "Body", A.planks(1.7, -5.2, 5.5, deck + 0.03, n=7, gap=0.04, th=0.05, width_fn=lambda z: sp.half_width(z, deck + 0.06, 0.13)), col="wood", mat="wood", role="detail")
    # fin keel + rudder
    fk = A.fin(1.3, 1.6, 0.9, 0.5, thick=0.12, pos=(0, 0.0, -0.3))
    fk = A.direct.moved(fk, (0, 0, 0), np.diag([1, -1, 1.0])) if False else xform(fk, (0, ky + 0.15, 0), (180, 0, 0))
    bulb = rev([(-0.9, 0), (-0.6, 0.22), (0.4, 0.22), (0.9, 0)], axis=2, segs=10, pos=(0, 0.2, 0.1))
    rud = xform(A.fin(1.0, 0.7, 0.45, 0.2, thick=0.08), (0, ky + 0.25, 4.6), (180, 0, 0))
    dpiece(H, "Keel", "Body", merge(fk, bulb, rud), col="darker", mat="hard", role="detail")
    # cabin with portholes
    cab = merge(box((2.2, 0.7, 3.6), (0, deck + 0.35, -1.0), r=0.25), box((1.8, 0.2, 3.0), (0, deck + 0.75, -1.0), r=0.1))
    dpiece(H, "Cabin", "Body", cab, col="primary", role="body")
    dpiece(H, "CabinGlass", "Body", windows_x(1.1, deck + 0.42, [-2.0, -1.0, 0.0], 0.7, 0.26, th=0.06), col=TINT, mat="glass", role="glass", pri=1.6)
    dpiece(H, "Hatch", "Body", box((0.8, 0.12, 0.8), (0, deck + 0.9, -1.4), r=0.05), col="wood", mat="wood", role="detail")
    # cockpit seat + tiller
    dpiece(H, "Seat", "Body", merge(box((2.6, 0.35, 1.2), (0, deck + 0.18, 2.8), r=0.1), box((2.6, 0.5, 0.2), (0, deck + 0.45, 3.45), r=0.08)), col="secondary", mat="cloth", role="detail")
    dpiece(H, "Tiller", "Body", tube([[0, deck + 0.3, 5.7], [0, deck + 0.55, 4.6], [0, deck + 0.6, 4.0]], 0.05, 6), col="wood", mat="wood", role="detail")
    dpiece(H, "Rails", "Body", merge(deck_rail(sp, lambda t: sp.top(t), 0.04, 0.9, h=0.55, inset=0.12, n=12, r=0.03)), col="chrome", mat="metal", role="detail")
    # mast + boom + sails (on bones: the sails swing / billow)
    mz, mh = -2.6, deck + 12.0
    H.bone("Mast", "Body", (0, deck, mz))
    dpiece(H, "MastP", "Mast", merge(mast(0, deck, mh, mz, 0.12, 0.07), tube([[0, mh - 0.3, mz], [0, mh + 0.2, mz]], 0.03, 5),
                                     tube([[0, mh - 4.5, mz - 0.05], [0.9, mh - 4.6, mz], [0, mh - 4.7, mz + 0.05]], 0.025, 5)), col="metal", mat="metal", role="limb")
    H.bone("Boom", "Mast", (0, deck + 1.6, mz))
    dpiece(H, "BoomP", "Boom", tube([[0, deck + 1.6, mz + 0.1], [0, deck + 1.6, mz + 5.6]], 0.08, 8), col="metal", mat="metal", role="limb")
    ms = A.sail(lambda t: (0, deck + 1.75 + t * (mh - deck - 2.2), mz + 0.15), lambda t: (0, deck + 1.75 + t * (mh - deck - 2.2), mz + 5.5 * (1 - t) ** 1.1 + 0.2 * t),
                billow=0.55, thick=0.03, nt=10, nu=6)
    dpiece(H, "MainSail", "Boom", ms, col="sail", mat="cloth", role="wing", pri=1.2)
    dpiece(H, "SailStripe", "Boom", A.sail(lambda t: (0, deck + 2.2 + t * 0.5, mz + 0.4), lambda t: (0, deck + 2.2 + t * 0.5, mz + 4.9),
                                           billow=0.62, thick=0.06, nt=3, nu=6), col="secondary", mat="cloth", role="detail")
    H.bone("Jib", "Body", (0, deck, -5.6))
    js = A.sail(lambda t: (0, deck + 0.4 + t * (mh - deck - 2.6), -5.6 + t * (5.6 + mz - 0.2)), lambda t: (0, deck + 0.4 + t * 0.3, -5.6 + (1 - t) * 4.0 + t * 0.2),
                billow=0.45, thick=0.03, nt=8, nu=5)
    dpiece(H, "JibSail", "Jib", js, col="sail", mat="cloth", role="wing", pri=1.3)
    dpiece(H, "Rigging", "Body", merge(tube([[0, mh - 0.4, mz], [0, deck + 0.2, -5.7]], 0.02, 4), tube([[0, mh - 0.4, mz], [0, deck + 0.4, 5.7]], 0.02, 4),
                                       tube([[1.75, deck, mz], [0, mh - 1.5, mz]], 0.02, 4), tube([[-1.75, deck, mz], [0, mh - 1.5, mz]], 0.02, 4)), col="steel", mat="metal", role="detail", pri=2.5)
    common(H, (0, deck + 0.4, 2.8), (2.4, 0.15, 1.1), -6.5, 6.4, mh)

    def extra(name, u, pose):
        k = 1.0 if name == "Move" else 0.4
        A._add(pose, "Boom", (0, 0, 0, 0, 0.25 * k + 0.05 * math.sin(TAU * u), 0))
        A._add(pose, "Jib", (0, 0, 0, 0, 0.12 * k + 0.03 * math.sin(TAU * u + 1), 0))
        if name == "Move":
            A._add(pose, "Body", (0, 0, 0, 0, 0, -0.12))

    A.boat_clips(H, extra=extra)
    return H


# ================================================================================================ super yacht
@hero("super yacht", "boats")
def super_yacht():
    H = V("super yacht")
    H.preview = {"primary": "#F5F5F5", "secondary": "#1A1A1A"}
    sp = HullSpec(24.0, 6.0, 2.8, bow=0.75, stern=0.1, transom=0.82, bow_rise=0.85, stern_rise=0.05, sheer_bow=0.35, sheer_stern=0.0,
                  p_bow=1.2, p_mid=2.0, p_stern=2.6, flare=0.12, maxat=0.62, deadrise=0.1)
    H.body((0, 1.5, 0))
    deck = 2.55
    dpiece(H, "Hull", "Body", A.hull_shell(sp, th=0.15, n=24, nl=27, floor=deck), col="primary", mat="hard", fallback="Ellipsoid", pattern=waterline(0.5, 0.7, 0.55))
    dpiece(H, "Stripe", "Body", side_band(sp, 0.66, 0.74, t0=0.1, t1=1.0), col="secondary", role="detail")
    dpiece(H, "HullGlass", "Body", side_band(sp, 0.45, 0.55, off=0.03, t0=0.35, t1=0.82, n=10), col=TINT, mat="glass", role="glass")
    dpiece(H, "Deck", "Body", A.planks(2.8, -11.0, 11.8, deck + 0.03, n=9, gap=0.05, th=0.05, width_fn=lambda z: sp.half_width(z, deck + 0.06, 0.2)), col="wood", mat="wood", role="detail")
    # superstructure: three stepped tiers, raked fronts, tinted window bands
    tiers = [(-3.5, 6.0, 4.8, 1.4, deck), (-2.0, 3.5, 4.0, 1.25, deck + 1.4), (-0.5, 1.2, 3.0, 1.1, deck + 2.65)]
    sup, gls = [], []
    for z0, z1, w, h, y0 in tiers:
        rings = []
        for k, z in enumerate(np.linspace(z0, z1, 6)):
            f = (z - z0) / (z1 - z0)
            rake = 1 - max(0, 0.35 - f) * 1.2  # front slopes back
            hh = h * min(1.0, 0.55 + f * 2.2)
            rings.append(np.array([[w / 2, y0, z], [w / 2 * rake, y0 + hh, z], [-w / 2 * rake, y0 + hh, z], [-w / 2, y0, z]]))
        sup.append(A.loft(rings, "fan", "fan", crease=35))
        sup.append(box((w + 0.5, 0.14, z1 - z0 + 1.0), (0, y0 + h + 0.02, (z0 + z1) / 2 + 0.3), r=0.06))  # overhanging roof
        gls.append(box((w + 0.07, h * 0.42, (z1 - z0) * 0.62), (0, y0 + h * 0.55, (z0 + z1) / 2 + 0.3), r=0.05))
    dpiece(H, "Super", "Body", merge(*sup), col="primary", role="body")
    dpiece(H, "Glass", "Body", merge(*gls), col=TINT, mat="glass", role="glass", pri=1.4)
    # flybridge seat + console, radar arch, helipad, swim platform
    yb = deck + 3.75 + 0.14
    dpiece(H, "Seat", "Body", merge(box((1.0, 0.35, 0.9), (0, yb + 0.18, 0.2), r=0.12), box((1.0, 0.8, 0.25), (0, yb + 0.6, 0.62), r=0.1)), col="cream", mat="cloth", role="detail")
    dpiece(H, "Console", "Body", merge(box((1.6, 0.7, 0.45), (0, yb + 0.35, -0.8), r=0.1), box((1.6, 0.05, 0.45), (0, yb + 0.72, -0.82), r=0.02)), col="secondary", role="detail")
    arch = tube([[-1.4, yb, 1.5], [-1.1, yb + 1.7, 1.9], [0, yb + 2.0, 2.0], [1.1, yb + 1.7, 1.9], [1.4, yb, 1.5]], 0.14, 8)
    radar = merge(cyl(0.1, 0.5, (0, yb + 2.3, 2.0), axis=1, segs=8), box((1.8, 0.12, 0.25), (0, yb + 2.6, 2.0), r=0.05), sphere(0.35, (0.9, yb + 2.15, 2.1)), sphere(0.35, (-0.9, yb + 2.15, 2.1)))
    dpiece(H, "Arch", "Body", merge(arch, radar), col="secondary", role="detail")
    pad = merge(cyl(2.4, 0.18, (0, deck + 1.55, 8.4), axis=1, segs=24), cyl(0.18, 1.4, (1.4, deck + 0.75, 8.4), axis=1), cyl(0.18, 1.4, (-1.4, deck + 0.75, 8.4), axis=1))
    dpiece(H, "Helipad", "Body", pad, col="secondary", role="detail")
    hmark = merge(box((0.25, 0.08, 1.5), (-0.5, deck + 1.66, 8.4)), box((0.25, 0.08, 1.5), (0.5, deck + 1.66, 8.4)), box((1.0, 0.08, 0.25), (0, deck + 1.66, 8.4)))
    dpiece(H, "PadMark", "Body", merge(hmark, A.lathe([(-0.03, 2.0), (0.03, 2.0), (0.03, 1.85), (-0.03, 1.85)], axis=1, segs=24, pos=(0, deck + 1.66, 8.4), closed=True)), col="white", role="detail", pri=2)
    dpiece(H, "Platform", "Body", merge(box((5.0, 0.2, 1.2), (0, 0.85, 12.5), r=0.05), deck_rail(sp, lambda t: deck, 0.06, 0.55, h=0.8, inset=0.15, n=10, r=0.035)), col="chrome", mat="metal", role="detail")
    common(H, (0, yb + 0.4, 0.2), (1.0, 0.15, 0.9), -12.5, 12.8, yb + 2.6)
    A.boat_clips(H, size=1.5)
    return H


# ================================================================================================ galleons
def _galleon(hid, pirate=False, ghost=False):
    H = V(hid)
    if pirate:
        H.preview = {"primary": "#3E2723", "secondary": "#1A1A1A"}
    else:
        H.preview = {"primary": "#6D4C41", "secondary": "#F2E6C9"}
    sp = HullSpec(24.0, 7.2, 3.6, bow=0.45, stern=0.1, transom=0.72, bow_rise=0.55, stern_rise=0.25, sheer_bow=0.5, sheer_stern=0.95,
                  p_bow=1.7, p_mid=2.6, p_stern=3.0, flare=0.0, tumble=0.12, maxat=0.5, strakes=0)
    H.body((0, 2.5, 0))
    deck = 3.0
    dpiece(H, "Hull", "Body", A.hull_shell(sp, th=0.2, n=24, nl=26, floor=deck), col="primary", mat="wood", fallback="Ellipsoid",
           pattern=A_stripes(sp))
    dpiece(H, "Wale", "Body", merge(side_band(sp, 0.55, 0.6, off=0.05, t0=0.08, t1=0.98), side_band(sp, 0.8, 0.84, off=0.05, t0=0.1, t1=0.98)),
           col="secondary" if not pirate else "darkWood", mat="wood", role="detail")
    dpiece(H, "Deck", "Body", A.planks(3.1, -10.4, 11.4, deck + 0.04, n=9, gap=0.06, th=0.06, width_fn=lambda z: sp.half_width(z, deck + 0.08, 0.26)), col="wood", mat="wood", role="detail")
    # sterncastle (quarterdeck) and forecastle decks with stairs
    qz0, qz1 = 5.0, 11.0
    qy = deck + 1.9
    rings = []
    for z in np.linspace(qz0, qz1, 6):
        w = sp.half_width(z, qy, 0.22)
        rings.append(np.array([[w, deck, z], [w, qy, z], [-w, qy, z], [-w, deck, z]]))
    castle = A.loft(rings, "fan", "fan", crease=35)
    fz0, fz1 = -10.4, -6.0
    fy = deck + 1.3
    rings = []
    for z in np.linspace(fz0, fz1, 6):
        w = sp.half_width(z, fy, 0.22)
        rings.append(np.array([[w, deck, z], [w, fy, z], [-w, fy, z], [-w, deck, z]]))
    fore = A.loft(rings, "fan", "fan", crease=35)
    dpiece(H, "Castles", "Body", merge(castle, fore), col="wood" if not pirate else "darkWood", mat="wood", role="body")
    dpiece(H, "Rails", "Body", merge(deck_rail(sp, lambda t: qy if sp.z(t) > qz0 else (fy if sp.z(t) < fz1 else deck), 0.08, 0.97, h=0.7, inset=0.22, n=16, r=0.06),
                                     box((5.2, 0.12, 0.12), (0, qy + 0.7, qz0), r=0.03), box((4.8, 0.12, 0.12), (0, fy + 0.7, fz1), r=0.03)),
           col="darkWood", mat="wood", role="detail")
    # gun ports / cannons
    zs = [-6.0, -3.0, 0.0, 3.0, 6.0]
    yg = deck - 0.75
    ports = []
    for z in zs:
        x = sp.half_width(z, yg, 0.0)
        ports.append(box((0.2, 0.7, 0.8), (x + 0.02, yg, z), r=0.03))
    pm = merge(*ports)
    dpiece(H, "Ports", "Body", merge(pm, mirror(pm)), col=[0.08, 0.06, 0.05] if not pirate else "secondary", mat="wood", role="detail")
    if pirate:
        H.mbone("Guns#", "Body", (sp.half_width(0, yg, 0), yg, 0))
        cs = []
        for z in zs:
            x = sp.half_width(z, yg, 0.0)
            cs.append(A.lathe([(x - 0.3, 0.0), (x - 0.3, 0.28), (x + 0.3, 0.24), (x + 0.75, 0.2), (x + 0.82, 0.24), (x + 0.86, 0.24), (x + 0.86, 0.12), (x + 0.6, 0.11)], axis=0, segs=12, pos=(0, yg, z)))
        dmpiece(H, "Cannons#", "Guns#", merge(*cs), col="gunmetal", mat="metal", role="detail")
    # stern: windows + lanterns, rudder; bow: bowsprit + figurehead
    zst = sp.z(1.0)
    win = merge(*[box((0.7, 0.8, 0.12), (x, deck + 1.0, zst + 0.12), r=0.05) for x in (-2.0, -0.7, 0.7, 2.0)],
                *[box((0.55, 0.6, 0.12), (x, deck + 2.4, zst + 0.08), r=0.05) for x in (-1.3, 0, 1.3)])
    dpiece(H, "SternGlass", "Body", win, col="glow" if ghost else [0.95, 0.75, 0.35], mat="glass", role="glass", pri=1.5)
    dpiece(H, "SternTrim", "Body", merge(box((6.4, 0.25, 0.25), (0, deck + 3.45, zst + 0.05), r=0.08), box((5.6, 0.2, 0.22), (0, deck + 1.75, zst + 0.1), r=0.06),
                                         xform(A.fin(3.0, 1.0, 0.7, 0.3, thick=0.14), (0, 0.15, zst - 0.3), (0, 0, 0))), col="gold" if not pirate else "darkWood", mat="wood", role="detail")
    for i, x in enumerate((-2.6, 0.0, 2.6)):
        H.prim(f"Lantern{i}", "Body", "Ball", (0.45, 0.6, 0.45), (x, deck + 4.4 - (0.3 if x else 0), zst + 0.35), col="glow", mat="glass", glow=True, role="light", pri=2.6)
    bs = tube([[0, deck + 0.6, sp.z(0.05)], [0, deck + 3.2, sp.z(0.0) - 5.0]], [0.22, 0.12], 8)
    head = xform(sphere(0.55, scale=(0.8, 1.0, 1.3)), (0, deck - 0.3, sp.z(0.0) - 0.2))
    dpiece(H, "Bowsprit", "Body", merge(bs, head), col="wood" if not pirate else "darkWood", mat="wood", role="detail")
    # masts (one bone each: the sails flex with the wind)
    masts = [(-6.0, 15.5, 4.8), (0.5, 19.0, 5.6), (7.5, 13.0, 4.0)]
    rig = []
    for i, (z, h, half) in enumerate(masts, 1):
        b = H.bone(f"Mast{i}", "Body", (0, deck, z))
        top = deck + h
        parts = [mast(0, deck - 0.5, top, z, 0.28, 0.13)]
        sails = []
        lv = [(deck + h * 0.33, deck + h * 0.62, half, half * 1.08), (deck + h * 0.66, deck + h * 0.88, half * 0.78, half * 0.95)]
        for (yb_, yt_, ht, hb) in lv:
            parts.append(yard(yt_, z - 0.25, ht * 1.08))
            sails.append(square_sail(yt_ - 0.15, yb_ + 0.3, z - 0.35, ht, hb, bulge=1.1))
        parts.append(yard(lv[0][0] + 0.2, z - 0.25, half * 1.1))
        if i == 2:
            parts.append(A.lathe([(top - 4.6, 0.0), (top - 4.6, 1.0), (top - 4.0, 1.05), (top - 4.0, 0.9), (top - 4.45, 0.85), (top - 4.45, 0.0)], axis=1, segs=14))  # crow's nest
        dpiece(H, f"MastP{i}", b, merge(*parts), col="darkWood", mat="wood", role="limb")
        dpiece(H, f"Sails{i}", b, merge(*sails), col=BLACKSAIL if pirate else "sail", mat="cloth", role="wing", pri=1.2,
               pattern=_tatter() if (pirate or ghost) else None)
        rig.append(tube([[0, top - 0.3, z], [0, deck + 0.6, z - 6.0 if i == 1 else masts[i - 2][0] + 0.5]], 0.04, 4))
        for sx in (1, -1):
            w0 = sp.half_width(z, deck + 0.5, 0.0)
            rig.append(tube([[sx * w0, deck + 0.4, z + 0.6], [0, top - 1.5, z]], 0.04, 4))
            rig.append(tube([[sx * w0, deck + 0.4, z - 0.6], [0, top - 1.5, z]], 0.04, 4))
    rig.append(tube([[0, deck + 3.2, sp.z(0.0) - 5.0], [0, deck + 15.0, -6.0]], 0.04, 4))
    dpiece(H, "Rigging", "Body", merge(*rig), col=[0.25, 0.2, 0.15], mat="cloth", role="detail", pri=2.5)
    js = A.sail(lambda t: (0, deck + 3.4 + t * 10.5, sp.z(0.0) - 4.7 + t * 3.8), lambda t: (0, deck + 3.0 + t * 1.0, sp.z(0.0) - 4.7 + 3.0 * (1 - t) + 1.0 * t),
                billow=0.5, thick=0.04, nt=7, nu=5)
    dpiece(H, "Jib", "Body", js, col=BLACKSAIL if pirate else "sail", mat="cloth", role="wing", pri=1.4)
    # flag on the main top
    ftop = deck + masts[1][1] + 0.1
    H.bone("Flag", "Mast2", (0, ftop, 0.5))
    dpiece(H, "FlagP", "Flag", merge(flag((0, ftop + 1.9, 0.6), 2.4, 1.5, amp=0.18), tube([[0, ftop - 0.5, 0.5], [0, ftop + 2.0, 0.5]], 0.06, 6)),
           col="black" if pirate else "secondary", mat="cloth", role="detail")
    if pirate:
        H.prim("Skull", "Flag", "Ball", (0.18, 0.55, 0.5), (0.06, ftop + 1.25, 1.8), col="white", role="detail", pri=2.2)
        H.prim("Bone1", "Flag", "Block", (0.12, 0.12, 1.3), (0.07, ftop + 1.0, 1.8), rot=(0.7, 0, 0), col="white", role="detail", pri=2.3)
        H.prim("Bone2", "Flag", "Block", (0.12, 0.12, 1.3), (0.07, ftop + 1.0, 1.8), rot=(-0.7, 0, 0), col="white", role="detail", pri=2.3)
        # skull emblem on the main course (stands proud of the bellied sail)
        lv0 = deck + 19.0 * 0.475
        H.prim("SailSkull", "Mast2", "Ellipsoid", (2.0, 1.9, 0.25), (0, lv0 + 0.4, 0.5 - 0.35 - 1.1 - 0.12), col="white", role="detail", pri=2.0)
        H.prim("SailJaw", "Mast2", "Block", (1.1, 0.6, 0.22), (0, lv0 - 0.7, 0.5 - 0.35 - 1.0 - 0.1), col="white", role="detail", pri=2.0)
    # helm on the quarterdeck: wheel + the captain's seat (Seat)
    wz = 7.4
    wheel = merge(tyre(0.75, 0.06, (0, qy + 1.3, wz), axis=2), *[tube([[0, qy + 1.3, wz], [0.95 * math.cos(a), qy + 1.3 + 0.95 * math.sin(a), wz]], 0.04, 5) for a in np.linspace(0, TAU, 8, endpoint=False)],
                  box((0.3, 1.2, 0.3), (0, qy + 0.6, wz + 0.2), r=0.06))
    dpiece(H, "Helm", "Body", wheel, col="wood", mat="wood", role="detail")
    dpiece(H, "Seat", "Body", merge(box((1.2, 0.5, 1.0), (0, qy + 0.25, wz + 1.6), r=0.1), box((1.2, 1.2, 0.2), (0, qy + 0.9, wz + 2.1), r=0.08)), col="secondary" if not pirate else [0.55, 0.1, 0.1], mat="cloth", role="detail")
    common(H, (0, qy + 0.55, wz + 1.6), (1.2, 0.15, 1.0), -17.0, 12.5, deck + 20.0, muzzle=(sp.half_width(0, yg, 0) + 0.9, yg, 0) if pirate else None)

    def extra(name, u, pose):
        k = 1.0 if name == "Move" else 0.35
        for i in (1, 2, 3):
            A._add(pose, f"Mast{i}", (0, 0, 0, 0.012 * k * math.sin(TAU * u + i), 0.03 * math.sin(TAU * u * 0.5 + i) * k, 0))
        A._add(pose, "Flag", (0, 0, 0, 0, 0.25 * math.sin(TAU * u * 2) * (0.5 + k), 0))
        if pirate and name == "Attack":
            r = A.pulse(u, 0.15, 0.5)
            A._add(pose, "GunsR", (-0.45 * r, 0, 0, 0, 0, 0))
            A._add(pose, "GunsL", (0.45 * r * 0.0, 0, 0, 0, 0, 0))

    A.boat_clips(H, size=2.0, extra=extra, attack="broadside" if pirate else "ram")
    return H


def A_stripes(sp):
    """Dark wood hull with lighter planking lines + darker waterline."""
    w = waterline(0.4, 0.8, 0.6)

    def f(P):
        band = 0.9 + 0.1 * np.cos(P[:, 1] * TAU / 0.45)
        return w(P) * band
    return f


def _tatter():
    def f(P):
        return 0.82 + 0.18 * np.sin(P[:, 0] * 3.1) * np.cos(P[:, 1] * 2.3)
    return f


@hero("ship", "boats")
def ship():
    return _galleon("ship")


@hero("pirate ship", "boats")
def pirate_ship():
    return _galleon("pirate ship", pirate=True)


# ================================================================================================ viking longship
@hero("viking longship", "boats")
def longship():
    H = V("viking longship")
    H.preview = {"primary": "#8D6E63", "secondary": "#C62828"}
    sp = HullSpec(22.0, 4.8, 1.9, bow=0.5, stern=0.5, transom=0.0, bow_rise=0.55, stern_rise=0.55, sheer_bow=1.25, sheer_stern=1.05,
                  p_bow=1.4, p_mid=2.2, p_stern=1.4, flare=0.25, maxat=0.5, strakes=6, strake_step=0.07, bow_shape=1.0)
    H.body((0, 1.2, 0))
    dpiece(H, "Hull", "Body", A.hull_shell(sp, th=0.11, n=24, nl=28), col="primary", mat="wood", fallback="Ellipsoid", pattern=waterline(0.3, 0.6, 0.72))
    dpiece(H, "Gunwale", "Body", A.rail(sp, r=0.09, t0=0.03, t1=0.97, n=26), col="darkWood", mat="wood", role="detail")
    fy = 0.55
    dpiece(H, "Floor", "Body", A.planks(1.6, -8.0, 8.0, fy, n=6, gap=0.05, th=0.06, width_fn=lambda z: sp.half_width(z, fy + 0.04, 0.13)), col="wood", mat="wood", role="detail")
    # rowers' sea chests along both sides
    ch = []
    for z in np.linspace(-6.0, 6.0, 7):
        w = sp.half_width(z, 1.0, 0.18)
        ch.append(box((0.9, 0.55, 0.7), (w - 0.5, fy + 0.3, z), r=0.06))
    cm = merge(*ch)
    dpiece(H, "Chests", "Body", merge(cm, mirror(cm)), col="darkWood", mat="wood", role="detail")
    # dragon head prow + curled stern (SDF sculpts)
    tb, ts = 0.0, 1.0
    p0 = np.array([0, sp.top(0.02) - 0.3, sp.z(0.02)])
    H.bone("Prow", "Body", tuple(p0))
    neck = stube([tuple(p0 + (0, -0.2, 0.3)), tuple(p0 + (0, 1.2, -0.5)), tuple(p0 + (0, 2.4, -0.6)), tuple(p0 + (0, 3.2, -0.2))], [0.32, 0.3, 0.27, 0.3], k=0.15)
    hc = p0 + np.array((0, 3.35, -0.55))
    head = ellipsoid(0.36, 0.42, 0.62, tuple(hc))
    head = head.su(round_cone(tuple(hc + (0, -0.05, -0.3)), tuple(hc + (0, -0.15, -1.2)), 0.3, 0.2), 0.15)              # snout
    head = head.su(round_cone(tuple(hc + (0, -0.35, -0.1)), tuple(hc + (0, -0.6, -1.0)), 0.18, 0.12), 0.08)              # open jaw
    head = head.ss(round_cone(tuple(hc + (0, -0.3, -0.5)), tuple(hc + (0, -0.32, -1.4)), 0.07, 0.14), 0.05)              # mouth gap
    for sx in (1, -1):
        head = head.su(round_cone(tuple(hc + (0.2 * sx, 0.3, 0.1)), tuple(hc + (0.35 * sx, 0.95, 0.65)), 0.11, 0.025), 0.06)  # horns
        head = head.su(capsule(tuple(hc + (0.22 * sx, 0.22, -0.35)), tuple(hc + (0.2 * sx, 0.2, -0.15)), 0.09), 0.05)        # brow
    crest = None
    for i in range(5):
        c = p0 + (0, 0.9 + 0.55 * i, -0.15 - 0.06 * i)
        sp_ = round_cone(tuple(c + (0, 0, 0.2)), tuple(c + (0, 0.15, 0.6)), 0.09, 0.02)
        crest = sp_ if crest is None else crest | sp_
    prow = neck.su(head, 0.2) | crest
    H.piece("DragonHead", "Prow", prow, col="secondary", mat="wood", tris=2200, role="head", fallback="Ellipsoid")
    H.eyes("Prow", tuple(hc + (0.27, 0.15, -0.45)), 0.08, col="gold", pupil="slit", look=(0.6, 0.1, -1))
    H.prim("Tongue", "Prow", "Block", (0.1, 0.06, 0.55), tuple(hc + (0, -0.38, -1.25)), rot=(0.4, 0, 0), col="red", role="mouth", pri=2.3)
    s0 = np.array([0, sp.top(0.98) - 0.3, sp.z(0.98)])
    pts = [tuple(s0 + (0, -0.1, -0.3)), tuple(s0 + (0, 1.2, 0.2)), tuple(s0 + (0, 2.3, 0.1)), tuple(s0 + (0, 2.8, -0.5)), tuple(s0 + (0, 2.4, -1.0)), tuple(s0 + (0, 1.95, -0.7))]
    tail = stube(pts, [0.3, 0.27, 0.23, 0.18, 0.13, 0.1], k=0.1)
    dpiece_sdf = H.piece("SternCurl", "Body", tail, col="secondary", mat="wood", tris=900, role="tail", fallback="Ellipsoid")
    # shields along both gunwales, alternating colours
    sa, sb = [], []
    zs = np.linspace(-6.6, 6.6, 9)
    for i, z in enumerate(zs):
        t = sp.t_of(z)
        x, y = sp.beam(t) + 0.06, sp.top(t) - 0.25
        s = A.lathe([(-0.06, 0.0), (-0.06, 0.62), (0.02, 0.62), (0.04, 0.5), (0.04, 0.0)], axis=0, segs=16, pos=(x, y, z))
        (sa if i % 2 == 0 else sb).append(s)
    ma, mb = merge(*sa), merge(*sb)
    dpiece(H, "ShieldsA", "Body", merge(ma, mirror(mb)), col="secondary", mat="wood", role="detail")
    dpiece(H, "ShieldsB", "Body", merge(mb, mirror(ma)), col="cream", mat="wood", role="detail")
    bosses = merge(*[sphere(0.16, (sp.beam(sp.t_of(z)) + 0.12, sp.top(sp.t_of(z)) - 0.25, z), scale=(0.6, 1, 1), segs=8) for z in zs])
    dpiece(H, "Bosses", "Body", merge(bosses, mirror(bosses)), col="metal", mat="metal", role="detail", pri=2)
    # oar banks on bones
    H.mbone("Oars#", "Body", (sp.half_width(0, 1.3, 0), 1.2, 0))
    oars = []
    for z in np.linspace(-5.4, 5.4, 6):
        x = sp.half_width(z, 1.3, 0.0)
        sh, bl = oar_mesh((x, 1.3, z), 0, 1.0, 4.2, r=0.06, blade=(0.9, 0.32), droop=-28)
        oars += [sh, bl]
    dmpiece(H, "OarBank#", "Oars#", merge(*oars), col="wood", mat="wood", role="limb")
    # mast, yard and a striped square sail (alternate strips in two pieces)
    H.bone("Mast", "Body", (0, fy, 0.0))
    mh = 13.0
    dpiece(H, "MastP", "Mast", merge(mast(0, fy, mh, 0.0, 0.22, 0.12), yard(mh - 1.0, -0.25, 4.6, r=0.14)), col="darkWood", mat="wood", role="limb")
    stripsA, stripsB = [], []
    nst = 6
    half_t, half_b, yt, yb = 4.2, 4.6, mh - 1.15, 5.0
    for k in range(nst):
        u0, u1 = k / nst, (k + 1) / nst

        def P(u, y):
            f = (yt - y) / (yt - yb)
            hw = half_t + (half_b - half_t) * f
            x = -hw + 2 * hw * u
            bul = -1.4 * math.sin(math.pi * u) * math.sin(math.pi * min(max(f, 0), 1))
            return np.array([x, y, -0.35 + bul])
        sheet = _strip(P, u0, u1, yt, yb)
        (stripsA if k % 2 == 0 else stripsB).append(sheet)
    dpiece(H, "SailA", "Mast", merge(*stripsA), col="secondary", mat="cloth", role="wing", pri=1.2)
    dpiece(H, "SailB", "Mast", merge(*stripsB), col="cream", mat="cloth", role="wing", pri=1.2)
    dpiece(H, "Rigging", "Body", merge(tube([[0, mh - 0.5, 0], [0, sp.top(0.05), sp.z(0.06)]], 0.04, 4), tube([[0, mh - 0.5, 0], [0, sp.top(0.95), sp.z(0.94)]], 0.04, 4),
                                       tube([[2.2, 1.6, 0.8], [0, mh - 1.8, 0]], 0.035, 4), tube([[-2.2, 1.6, 0.8], [0, mh - 1.8, 0]], 0.035, 4)), col=ROPE, mat="cloth", role="detail", pri=2.5)
    # steering oar + helmsman's seat at the stern (right side)
    so = merge(tube([[1.6, 2.6, 7.4], [2.1, -0.1, 8.6]], 0.09, 6), box((0.12, 1.4, 0.5), (2.05, 0.4, 8.45), r=0.04, rot=(-24, 0, 0)))
    dpiece(H, "Steer", "Body", so, col="wood", mat="wood", role="detail")
    wz = 6.8
    w = sp.half_width(wz, 1.2, 0.15)
    dpiece(H, "Seat", "Body", merge(box((1.3, 0.75, 1.0), (0.6, fy + 0.38, wz), r=0.08), box((1.4, 0.18, 1.1), (0.6, fy + 0.82, wz), r=0.06)), col="darkWood", mat="wood", role="detail")
    common(H, (0.6, fy + 1.0, wz), (1.3, 0.15, 1.0), -14.0, 12.0, mh)

    def extra(name, u, pose):
        if name in ("Move", "Attack"):
            ph = TAU * u * (2 if name == "Attack" else 1)
            sweep, lift = 0.4 * math.sin(ph), 0.15 * math.cos(ph)
            A._add(pose, "OarsR", (0, 0, 0, 0, sweep, -lift))
            A._add(pose, "OarsL", (0, 0, 0, 0, -sweep, lift))
        k = 1.0 if name == "Move" else 0.3
        A._add(pose, "Mast", (0, 0, 0, 0.015 * k * math.sin(TAU * u), 0.02 * k * math.sin(TAU * u * 0.5), 0))
        A._add(pose, "Prow", (0, 0, 0, 0.04 * math.sin(TAU * u + 0.5) if name == "Idle" else (-0.25 * A.pulse(u, 0.2, 0.7) if name == "Attack" else 0), 0, 0))

    A.boat_clips(H, size=1.5, extra=extra)
    return H


def _strip(P, u0, u1, yt, yb, nt=7, nu=3, th=0.035):
    """One vertical strip of a bellied square sail (P(u, y) -> point)."""
    def fn(t, u):
        y = yt + (yb - yt) * t
        uu = u0 + (u1 - u0) * u
        p = P(uu, y)
        e = 1e-3
        du = P(min(uu + e, 1), y) - P(max(uu - e, 0), y)
        dy = P(uu, y + e) - P(uu, y - e)
        n = np.cross(du, dy)
        return p, n
    return A.slab(fn, nt, nu, th, crease=80)


# ================================================================================================ paddle steamer
@hero("paddle steamer", "boats")
def paddle_steamer():
    H = V("paddle steamer")
    H.preview = {"primary": "#F5F5F5", "secondary": "#C62828"}
    sp = HullSpec(18.0, 6.0, 1.4, bow=0.6, stern=0.05, transom=0.95, bow_rise=0.4, stern_rise=0.0, sheer_bow=0.35, sheer_stern=0.0,
                  p_bow=1.8, p_mid=4.0, p_stern=4.0, flare=0.05, maxat=0.45)
    H.body((0, 1.2, 0))
    deck = 1.3
    dpiece(H, "Hull", "Body", A.hull_shell(sp, th=0.15, n=22, nl=24, floor=deck), col="primary", mat="wood", fallback="Block", pattern=waterline(0.3, 0.5, 0.6))
    dpiece(H, "Trim", "Body", side_band(sp, 0.75, 0.9, t0=0.06), col="secondary", role="detail")
    dpiece(H, "Deck", "Body", A.planks(2.8, -8.2, 9.0, deck + 0.04, n=8, gap=0.05, th=0.05, width_fn=lambda z: sp.half_width(z, deck + 0.08, 0.17)), col="wood", mat="wood", role="detail")
    # two decks of cabins with a gallery of posts and rails, wheelhouse on top
    y1, y2, y3 = deck, deck + 2.0, deck + 3.9
    c1 = box((4.4, 1.9, 9.0), (0, y1 + 0.95, 1.5), r=0.08)
    c2 = box((3.8, 1.8, 7.0), (0, y2 + 1.0, 1.5), r=0.08)
    roofs = merge(box((5.6, 0.14, 12.0), (0, y2 + 0.04, 1.4), r=0.05), box((5.4, 0.14, 10.0), (0, y3 + 0.04, 1.5), r=0.05))
    wh = merge(box((2.4, 1.6, 2.2), (0, y3 + 0.85, -1.5), r=0.1), box((2.8, 0.16, 2.6), (0, y3 + 1.7, -1.5), r=0.05))
    dpiece(H, "Cabins", "Body", merge(c1, c2, wh), col="primary", mat="wood", role="body")
    dpiece(H, "Roofs", "Body", roofs, col="secondary", mat="wood", role="detail")
    g = merge(windows_x(2.2, y1 + 1.05, np.linspace(-2.2, 5.2, 7), 0.6, 0.9))
    g2 = merge(windows_x(1.9, y2 + 1.05, np.linspace(-1.2, 4.2, 6), 0.55, 0.85), box((2.0, 0.7, 0.07), (0, y3 + 1.0, -2.6), r=0.04), windows_x(1.2, y3 + 1.0, [-1.6, -0.9], 0.45, 0.7))
    dpiece(H, "Windows", "Body", g, col=TINT, mat="glass", role="glass", pri=1.5)
    dpiece(H, "Windows2", "Body", g2, col=TINT, mat="glass", role="glass", pri=1.5)
    posts = []
    for yy in (y1, y2):
        pts = [[2.65, yy + 0.07, z] for z in np.linspace(-4.2, 7.2, 9)]
        m = rail_posts(pts, 1.9, 0.05)
        posts.append(m)
        posts.append(mirror(m))
    dpiece(H, "Gallery", "Body", merge(*posts), col="white", mat="wood", role="detail")
    # twin chimneys with crowns
    chs = []
    for x in (1.1, -1.1):
        chs.append(A.lathe([(y2, 0.0), (y2, 0.42), (y2 + 6.2, 0.38), (y2 + 6.5, 0.6), (y2 + 6.8, 0.68), (y2 + 6.8, 0.5), (y2 + 6.4, 0.34), (y2 + 6.4, 0.0)], axis=1, segs=14, pos=(x, 0, -4.0)))
    dpiece(H, "Chimneys", "Body", merge(*chs), col="black", mat="metal", role="detail")
    dpiece(H, "ChimBands", "Body", merge(*[cyl(0.44, 0.35, (x, y2 + 4.8, -4.0), axis=1, segs=14) for x in (1.1, -1.1)]), col="secondary", mat="metal", role="detail", pri=2)
    # stern paddle wheel on a bone
    wz, wy, R = 10.6, 1.6, 2.5
    H.bone("Wheel", "Body", (0, wy, wz))
    wheel = [tyre(R, 0.07, (2.0, wy, wz), axis=0, segs=20, rsegs=6), tyre(R, 0.07, (-2.0, wy, wz), axis=0, segs=20, rsegs=6), cyl(0.25, 4.6, (0, wy, wz), axis=0, segs=12)]
    for a in np.linspace(0, TAU, 10, endpoint=False):
        c, s = math.cos(a), math.sin(a)
        wheel.append(box((4.0, 0.7, 0.12), (0, wy + s * (R - 0.35), wz + c * (R - 0.35)), r=0.02, rot=(-math.degrees(a) + 90, 0, 0)))
        for x in (2.0, -2.0):
            wheel.append(tube([[x, wy, wz], [x, wy + s * R, wz + c * R]], 0.05, 5))
    dpiece(H, "PaddleWheel", "Wheel", merge(*wheel), col="secondary", mat="wood", role="limb")
    dpiece(H, "WheelFrame", "Body", merge(tube([[2.2, deck, 8.6], [2.2, wy + 0.1, wz], [2.2, deck, 12.4]], 0.12, 6), tube([[-2.2, deck, 8.6], [-2.2, wy + 0.1, wz], [-2.2, deck, 12.4]], 0.12, 6),
                                          tube([[2.2, y2, 8.0], [2.2, wy + R + 0.4, wz]], 0.1, 6), tube([[-2.2, y2, 8.0], [-2.2, wy + R + 0.4, wz]], 0.1, 6)), col="darkWood", mat="wood", role="detail")
    # helmsman seat on the hurricane deck, in front of the wheelhouse
    dpiece(H, "Seat", "Body", merge(box((1.1, 0.45, 0.9), (0, y3 + 0.3, -3.6), r=0.1), box((1.1, 0.9, 0.2), (0, y3 + 0.7, -3.1), r=0.06)), col="secondary", mat="cloth", role="detail")
    H.bone("Flag", "Body", (0, y3 + 1.8, -1.5))
    dpiece(H, "FlagP", "Flag", merge(flag((0, y3 + 3.5, -1.45), 1.5, 0.9), tube([[0, y3 + 1.7, -1.5], [0, y3 + 3.6, -1.5]], 0.05, 6)), col="secondary", mat="cloth", role="detail")
    common(H, (0, y3 + 0.6, -3.6), (1.1, 0.15, 0.9), -10.0, 13.5, y3 + 3.0)
    H.socket("exhaust", (1.1, y2 + 6.9, -4.0), "Body")
    spins = [("Wheel", "x", -1, TAU / 10)]

    def extra(name, u, pose):
        A._add(pose, "Flag", (0, 0, 0, 0, 0.25 * math.sin(TAU * u * 2), 0))

    A.boat_clips(H, size=1.5, extra=extra, spinners=spins)
    return H


# ================================================================================================ tugboat
@hero("tugboat", "boats")
def tugboat():
    H = V("tugboat")
    H.preview = {"primary": "#E53935", "secondary": "#1A1A1A"}
    sp = HullSpec(10.0, 4.6, 2.0, bow=0.25, stern=0.4, transom=0.25, bow_rise=0.5, stern_rise=0.3, sheer_bow=0.45, sheer_stern=0.05,
                  p_bow=1.8, p_mid=2.6, p_stern=2.2, flare=0.12, maxat=0.45)
    H.body((0, 1.2, 0))
    deck = 1.75
    dpiece(H, "Hull", "Body", A.hull_shell(sp, th=0.14, n=24, nl=26, floor=deck), col="primary", mat="metal", fallback="Ellipsoid", pattern=waterline(0.45, 0.65, 0.5))
    dpiece(H, "Band", "Body", side_band(sp, 0.84, 0.97, t0=0.02, t1=1.0), col="secondary", role="detail")
    dpiece(H, "Deck", "Body", A.planks(2.0, -4.6, 4.8, deck + 0.04, n=6, gap=0.05, th=0.05, width_fn=lambda z: sp.half_width(z, deck + 0.08, 0.16)), col=[0.45, 0.47, 0.5], mat="metal", role="detail")
    # tyre fenders: a fat bow bumper + tyres hung along the sides
    bow = tube([[sp.beam(0.1) + 0.05, sp.top(0.1) - 0.35, sp.z(0.1)], [0.6, sp.top(0.02) - 0.4, sp.z(0.02) - 0.15], [0, sp.top(0.0) - 0.4, sp.z(0.0) - 0.28],
                [-0.6, sp.top(0.02) - 0.4, sp.z(0.02) - 0.15], [-sp.beam(0.1) - 0.05, sp.top(0.1) - 0.35, sp.z(0.1)]], 0.33, 10)
    ty = []
    for z in (-2.2, -0.4, 1.4, 3.0):
        t = sp.t_of(z)
        ty.append(tyre(0.38, 0.17, (sp.half_width(z, deck - 0.6, 0) + 0.18, deck - 0.6, z), axis=0, segs=12, rsegs=7))
    tm = merge(*ty)
    dpiece(H, "Fenders", "Body", merge(bow, tm, mirror(tm)), col="tyre", mat="rubber", role="detail")
    # wheelhouse (tall, windows all round), lower deckhouse, funnel, mast
    dpiece(H, "House", "Body", merge(box((3.0, 1.6, 4.4), (0, deck + 0.8, 0.3), r=0.12), box((2.6, 1.6, 2.2), (0, deck + 2.35, -0.6), r=0.12),
                                     box((3.0, 0.15, 2.6), (0, deck + 3.2, -0.6), r=0.06)), col="white", mat="metal", role="body")
    gl = merge(box((2.2, 0.7, 0.07), (0, deck + 2.5, -1.71), r=0.04), windows_x(1.31, deck + 2.5, [-1.1, -0.1], 0.75, 0.7), windows_x(1.51, deck + 0.95, [-0.9, 0.4, 1.7], 0.5, 0.5))
    dpiece(H, "Windows", "Body", gl, col=TINT, mat="glass", role="glass", pri=1.5)
    dpiece(H, "Funnel", "Body", merge(A.lathe([(deck + 1.5, 0.0), (deck + 1.5, 0.55), (deck + 3.6, 0.5), (deck + 3.6, 0.0)], axis=1, segs=14, pos=(0, 0, 1.6), scale=(1, 1, 1.3))),
           col="primary", mat="metal", role="detail")
    dpiece(H, "FunnelTop", "Body", A.lathe([(deck + 3.2, 0.0), (deck + 3.2, 0.53), (deck + 3.9, 0.52), (deck + 3.9, 0.0)], axis=1, segs=14, pos=(0, 0, 1.6), scale=(1, 1, 1.3)), col="secondary", mat="metal", role="detail")
    mst = merge(tube([[0, deck + 3.2, -0.2], [0, deck + 5.6, -0.2]], 0.06, 6), box((1.4, 0.08, 0.08), (0, deck + 4.9, -0.2)))
    dpiece(H, "Mast", "Body", mst, col="white", mat="metal", role="detail")
    H.prim("MastLight", "Body", "Ball", (0.2, 0.2, 0.2), (0, deck + 5.7, -0.2), col="glow", glow=True, role="light", pri=2.5)
    H.mprim("SideLight#", "Body", "Block", (0.12, 0.2, 0.3), (1.32, deck + 3.0, -1.3), col="red", glow=True, role="light", pri=2.6)
    # towing bitt + life ring + rails
    dpiece(H, "Bitt", "Body", merge(cyl(0.22, 0.9, (0.5, deck + 0.45, 3.6), axis=1, segs=10), cyl(0.22, 0.9, (-0.5, deck + 0.45, 3.6), axis=1, segs=10),
                                    cyl(0.1, 1.5, (0, deck + 0.7, 3.6), axis=0, segs=8), tyre(0.35, 0.08, (0, deck + 0.15, 4.4), axis=1, segs=12)), col="secondary", mat="metal", role="detail")
    dpiece(H, "LifeRing", "Body", tyre(0.35, 0.09, (1.52, deck + 1.0, 1.5), axis=0, segs=14), col="white", role="detail", pri=2)
    dpiece(H, "Rails", "Body", deck_rail(sp, lambda t: sp.top(t), 0.15, 0.98, h=0.45, inset=0.1, n=10, r=0.035), col="white", mat="metal", role="detail")
    # flying bridge seat on the wheelhouse roof
    dpiece(H, "Seat", "Body", merge(box((1.0, 0.4, 0.9), (0, deck + 3.5, -0.5), r=0.1), box((1.0, 0.8, 0.2), (0, deck + 3.85, -0.05), r=0.06)), col="secondary", mat="cloth", role="detail")
    common(H, (0, deck + 3.75, -0.5), (1.0, 0.15, 0.9), -5.8, 5.5, deck + 5.5)
    H.socket("exhaust", (0, deck + 4.0, 1.6), "Body")
    A.boat_clips(H, size=1.0, attack="ram")
    return H


# ================================================================================================ fishing boat
@hero("fishing boat", "boats")
def fishing_boat():
    H = V("fishing boat")
    H.preview = {"primary": "#1565C0", "secondary": "#F5F5F5"}
    sp = HullSpec(13.0, 4.6, 2.0, bow=0.4, stern=0.25, transom=0.65, bow_rise=0.6, stern_rise=0.15, sheer_bow=0.45, sheer_stern=0.1,
                  p_bow=1.6, p_mid=2.5, p_stern=2.8, flare=0.15, maxat=0.5)
    H.body((0, 1.2, 0))
    deck = 1.75
    dpiece(H, "Hull", "Body", A.hull_shell(sp, th=0.14, n=24, nl=26, floor=deck), col="primary", mat="wood", fallback="Ellipsoid", pattern=waterline(0.45, 0.65, 0.55))
    dpiece(H, "Band", "Body", side_band(sp, 0.86, 0.98, t0=0.02), col="secondary", role="detail")
    dpiece(H, "Deck", "Body", A.planks(2.0, -6.0, 6.3, deck + 0.04, n=7, gap=0.05, th=0.05, width_fn=lambda z: sp.half_width(z, deck + 0.08, 0.16)), col="wood", mat="wood", role="detail")
    dpiece(H, "House", "Body", merge(box((2.8, 2.1, 2.8), (0, deck + 1.05, -2.4), r=0.12), box((3.2, 0.16, 3.3), (0, deck + 2.16, -2.4), r=0.06)), col="secondary", mat="wood", role="body")
    gl = merge(box((2.2, 0.7, 0.07), (0, deck + 1.5, -3.81), r=0.04), windows_x(1.41, deck + 1.5, [-2.8, -1.9], 0.6, 0.6), box((1.6, 0.7, 0.07), (0, deck + 1.5, -0.99), r=0.04))
    dpiece(H, "Windows", "Body", gl, col=TINT, mat="glass", role="glass", pri=1.5)
    # gantry (A-frame) aft + outrigger booms with nets
    gz = 4.6
    gan = merge(tube([[1.7, deck, gz], [0.9, deck + 3.6, gz - 0.2]], 0.1, 6), tube([[-1.7, deck, gz], [-0.9, deck + 3.6, gz - 0.2]], 0.1, 6), tube([[-1.0, deck + 3.5, gz - 0.2], [1.0, deck + 3.5, gz - 0.2]], 0.1, 6),
                cyl(0.35, 2.0, (0, deck + 0.5, 2.6), axis=0, segs=12), box((2.6, 0.3, 0.8), (0, deck + 0.15, 2.6), r=0.05))  # net drum
    mast_ = merge(tube([[0, deck + 2.2, -1.6], [0, deck + 6.5, -1.6]], 0.1, 6), box((1.6, 0.1, 0.1), (0, deck + 5.5, -1.6)))
    dpiece(H, "Gantry", "Body", merge(gan, mast_), col="white", mat="metal", role="detail")
    H.mbone("Boom#", "Body", (0.3, deck + 2.5, -1.2))
    bm = tube([[0.3, deck + 2.5, -1.2], [4.6, deck + 5.6, 0.6]], [0.09, 0.06], 6)
    net = A.quad_sheet((4.4, deck + 5.3, 0.4), (4.7, deck + 1.0, 0.0), (4.4, deck + 5.3, 1.2), (4.8, deck + 0.8, 2.0), nt=6, nu=4, bulge=(0.4, 0, 0.1), thick=0.03)
    dmpiece(H, "BoomP#", "Boom#", bm, col="metal", mat="metal", role="limb")
    dmpiece(H, "Net#", "Boom#", net, col=[0.35, 0.42, 0.3], mat="cloth", role="detail")
    dpiece(H, "DrumNet", "Body", cyl(0.42, 1.7, (0, deck + 0.5, 2.6), axis=0, segs=12), col=[0.35, 0.42, 0.3], mat="cloth", role="detail")
    dpiece(H, "Buoys", "Body", merge(sphere(0.32, (1.0, deck + 3.6, gz - 0.3)), sphere(0.32, (-1.0, deck + 3.6, gz - 0.3)), sphere(0.3, (1.5, deck + 0.3, 5.7)), sphere(0.3, (0.9, deck + 0.3, 5.9))),
           col=[1.0, 0.45, 0.1], role="detail", pri=2)
    crates = merge(box((1.0, 0.55, 0.7), (-1.1, deck + 0.3, 0.6), r=0.05), box((1.0, 0.55, 0.7), (-1.1, deck + 0.85, 0.6), r=0.05), box((1.0, 0.55, 0.7), (-1.0, deck + 0.3, 1.4), r=0.05))
    dpiece(H, "Crates", "Body", crates, col=[0.2, 0.6, 0.85], role="detail")
    dpiece(H, "Rails", "Body", deck_rail(sp, lambda t: sp.top(t), 0.08, 0.6, h=0.45, inset=0.1, n=10, r=0.035), col="white", mat="metal", role="detail")
    dpiece(H, "Seat", "Body", merge(box((1.0, 0.5, 0.8), (0.8, deck + 0.25, 0.4), r=0.1), box((1.0, 0.8, 0.18), (0.8, deck + 0.75, 0.82), r=0.06)), col="secondary", mat="cloth", role="detail")
    H.prim("MastLight", "Body", "Ball", (0.22, 0.22, 0.22), (0, deck + 6.6, -1.6), col="glow", glow=True, role="light", pri=2.5)
    common(H, (0.8, deck + 0.6, 0.4), (1.0, 0.15, 0.8), -7.5, 7.0, deck + 6.5)

    def extra(name, u, pose):
        k = 1.0 if name == "Move" else 0.5
        A._add(pose, "BoomR", (0, 0, 0, 0, 0, 0.05 * k * math.sin(TAU * u)))
        A._add(pose, "BoomL", (0, 0, 0, 0, 0, -0.05 * k * math.sin(TAU * u)))

    A.boat_clips(H, size=1.0, extra=extra)
    return H


# ================================================================================================ raft
@hero("raft", "boats")
def raft():
    H = V("raft")
    H.preview = {"primary": "#B07A3E", "secondary": "#8D6E63"}
    H.body((0, 0.5, 0))
    logs = []
    n = 7
    r = 0.42
    for i in range(n):
        x = (i - (n - 1) / 2) * (2 * r - 0.02)
        L = 8.0 - 0.3 * abs(i - 3) + 0.25 * math.sin(i * 2.1)
        z0 = 0.15 * math.sin(i * 1.7)
        logs.append(A.lathe([(-L / 2, 0.0), (-L / 2 - 0.05, r * 0.7), (-L / 2 + 0.1, r), (L / 2 - 0.1, r * 0.97), (L / 2 + 0.05, r * 0.7), (L / 2, 0.0)], axis=2, segs=10, pos=(x, r, z0)))
    dpiece(H, "Hull", "Body", merge(*logs), col="primary", mat="wood", fallback="Block", pattern=lambda P: 0.85 + 0.15 * np.sin(P[:, 2] * 5.0 + P[:, 0] * 9.0))
    cross = [A.lathe([(-3.1, 0.0), (-3.1, 0.22), (3.1, 0.22), (3.1, 0.0)], axis=0, segs=8, pos=(0, 2 * r + 0.12, z)) for z in (-3.0, 0.2, 3.0)]
    dpiece(H, "Cross", "Body", merge(*cross), col="secondary", mat="wood", role="detail")
    lash = []
    for z in (-3.0, 0.2, 3.0):
        for i in (0, 2, 4, 6):
            x = (i - 3) * (2 * r - 0.02)
            lash.append(tyre(0.3, 0.05, (x, 2 * r - 0.05, z), axis=0, segs=10, rsegs=5))
    dpiece(H, "Lashings", "Body", merge(*lash), col=ROPE, mat="cloth", role="detail")
    # little mast with a patched square sail on a bone
    H.bone("Mast", "Body", (0, 2 * r, -1.2))
    dpiece(H, "MastP", "Mast", merge(cyl(0.12, 5.2, (0, 2 * r + 2.6, -1.2), axis=1, segs=8), yard(2 * r + 4.8, -1.35, 1.8, r=0.08), yard(2 * r + 1.9, -1.35, 1.7, r=0.07)),
           col="secondary", mat="wood", role="limb")
    dpiece(H, "Sail", "Mast", square_sail(2 * r + 4.75, 2 * r + 2.0, -1.5, 1.7, 1.6, bulge=0.6, nt=6, nu=6), col="sail", mat="cloth", role="wing",
           pattern=lambda P: np.where((np.abs(P[:, 0] - 0.6) < 0.45) & (np.abs(P[:, 1] - 3.5) < 0.5), 0.75, 1.0))
    dpiece(H, "Seat", "Body", merge(box((1.1, 0.6, 0.9), (0, 2 * r + 0.35, 1.8), r=0.06), box((1.15, 0.08, 0.95), (0, 2 * r + 0.67, 1.8), r=0.02)), col="wood", mat="wood", role="detail")
    dpiece(H, "Barrel", "Body", rev([(-0.5, 0), (-0.48, 0.3), (0, 0.38), (0.48, 0.3), (0.5, 0)], axis=1, segs=12, pos=(-1.6, 2 * r + 0.55, 2.9)), col="wood", mat="wood", role="detail")
    H.bone("Paddle", "Body", (0.9, 2.0, 1.8))
    pd = merge(tube([[0.7, 3.0, 1.6], [1.9, -0.2, 2.2]], 0.05, 6), A.quad_sheet((1.7, 0.4, 1.9), (2.0, -0.6, 2.1), (1.7, 0.4, 2.35), (2.0, -0.6, 2.55), nt=4, nu=3, thick=0.03))
    dpiece(H, "PaddleP", "Paddle", pd, col="wood", mat="wood", role="limb")
    H.bone("Flag", "Mast", (0, 2 * r + 5.2, -1.2))
    dpiece(H, "FlagP", "Flag", flag((0, 2 * r + 5.3, -1.18), 0.9, 0.5), col="red", mat="cloth", role="detail")
    common(H, (0, 2 * r + 0.75, 1.8), (1.1, 0.15, 0.9), -4.5, 4.5, 6.0)

    def extra(name, u, pose):
        A._add(pose, "Flag", (0, 0, 0, 0, 0.3 * math.sin(TAU * u * 2), 0))
        A._add(pose, "Mast", (0, 0, 0, 0.02 * math.sin(TAU * u), 0, 0.03 * math.sin(TAU * u + 1)))
        if name in ("Move", "Attack"):
            A._add(pose, "Paddle", (0, 0.1 * math.cos(TAU * u), 0, 0.45 * math.sin(TAU * u), 0, 0))

    A.boat_clips(H, size=0.8, extra=extra)
    return H


# ================================================================================================ gondola
@hero("gondola", "boats")
def gondola():
    H = V("gondola")
    H.preview = {"primary": "#1A1A1A", "secondary": "#D4AF37"}
    sp = HullSpec(12.0, 1.9, 0.75, bow=0.6, stern=0.6, transom=0.0, bow_rise=0.9, stern_rise=0.8, sheer_bow=1.6, sheer_stern=1.3,
                  p_bow=1.6, p_mid=2.4, p_stern=1.6, flare=0.15, maxat=0.5)
    H.body((0, 0.5, 0))
    dpiece(H, "Hull", "Body", A.hull_shell(sp, th=0.07, n=22, nl=28), col="primary", mat="wood", fallback="Ellipsoid")
    dpiece(H, "Gunwale", "Body", A.rail(sp, r=0.05, t0=0.06, t1=0.94, n=26), col="secondary", mat="metal", role="detail")
    fy = 0.3
    dpiece(H, "Floor", "Body", A.planks(0.6, -3.5, 3.5, fy, n=3, gap=0.05, th=0.05, width_fn=lambda z: sp.half_width(z, fy + 0.03, 0.08)), col="wood", mat="wood", role="detail")
    # ferro: the iconic six-toothed steel prow comb
    bz, by = sp.z(0.0), sp.top(0.0)
    fe = [box((0.06, 1.3, 0.35), (0, by + 0.45, bz - 0.12), r=0.02), box((0.06, 0.25, 0.85), (0, by + 1.1, bz - 0.25), r=0.02, rot=(10, 0, 0))]
    for k in range(6):
        fe.append(box((0.05, 0.12, 0.42), (0, by + 0.05 + k * 0.18, bz - 0.45), r=0.02))
    dpiece(H, "Ferro", "Body", merge(*fe), col="metal", mat="metal", role="detail")
    sz, sy = sp.z(1.0), sp.top(1.0)
    dpiece(H, "SternCurl", "Body", tube([[0, sy - 0.2, sz - 0.3], [0, sy + 0.3, sz + 0.1], [0, sy + 0.55, sz - 0.1], [0, sy + 0.45, sz - 0.35]], [0.12, 0.1, 0.08, 0.06], 6), col="secondary", mat="metal", role="detail")
    # love seat with a cushion, gold sea-horse ornaments at its sides
    dpiece(H, "Seat", "Body", merge(box((1.2, 0.45, 1.0), (0, fy + 0.35, 0.6), r=0.12), box((1.2, 0.9, 0.25), (0, fy + 0.75, 1.1), r=0.12, rot=(-10, 0, 0))), col=[0.62, 0.08, 0.12], mat="cloth", role="detail")
    orn = merge(*[tube([[sx * 0.66, fy + 0.4, 0.1], [sx * 0.7, fy + 1.0, 0.2], [sx * 0.68, fy + 1.15, 0.0], [sx * 0.67, fy + 1.0, -0.12]], [0.07, 0.06, 0.05, 0.04], 6) for sx in (1, -1)])
    dpiece(H, "Ornaments", "Body", orn, col="secondary", mat="metal", role="detail")
    # forcola + the gondolier's long oar on a bone
    fz = 3.6
    fxw = sp.half_width(fz, sp.top(sp.t_of(fz)) - 0.05, 0.0)
    dpiece(H, "Forcola", "Body", merge(box((0.18, 0.8, 0.35), (fxw - 0.05, sp.top(sp.t_of(fz)) + 0.35, fz), r=0.05), sphere(0.1, (fxw - 0.05, sp.top(sp.t_of(fz)) + 0.8, fz + 0.1))), col="wood", mat="wood", role="detail")
    py = sp.top(sp.t_of(fz)) + 0.65
    H.bone("Oar", "Body", (fxw, py, fz))
    sh = tube([[fxw - 1.2, py + 0.9, fz - 1.2], [fxw + 0.8, py - 1.7, fz + 3.2]], 0.05, 7)
    bl = box((0.06, 0.25, 1.0), (fxw + 0.8, py - 1.75, fz + 3.25), r=0.02, rot=(30, 0, 0))
    dpiece(H, "OarP", "Oar", merge(sh, bl), col="wood", mat="wood", role="limb")
    H.prim("Lamp", "Body", "Ball", (0.25, 0.3, 0.25), (0, by + 1.45, bz - 0.2), col="glow", glow=True, role="light", pri=2.6)
    common(H, (0, fy + 0.6, 0.6), (1.2, 0.15, 1.0), -7.0, 7.0, 2.6)

    def extra(name, u, pose):
        if name in ("Move", "Attack"):
            A._add(pose, "Oar", (0, 0, 0, 0.35 * math.sin(TAU * u), 0.08 * math.cos(TAU * u), 0))
        else:
            A._add(pose, "Oar", (0, 0, 0, 0.05 * math.sin(TAU * u), 0, 0))

    A.boat_clips(H, size=0.8, extra=extra)
    return H


# ================================================================================================ submarine
@hero("submarine", "boats")
def submarine():
    H = V("submarine")
    H.preview = {"primary": "#37474F", "secondary": "#FFC107"}
    R, L = 1.55, 16.0
    cy = R + 0.05
    H.body((0, cy, 0))
    hull = rev([(-L / 2, 0), (-L / 2 + 0.25, 0.75 * R), (-L / 2 + 1.4, R * 0.98), (-L / 2 + 3.0, R), (2.5, R), (5.0, 0.82 * R), (7.2, 0.35 * R), (L / 2, 0.08)],
               axis=2, segs=22, pos=(0, cy, 0), spline=4)
    dpiece(H, "Hull", "Body", hull, col="primary", mat="metal", fallback="Ellipsoid", pattern=lambda P: np.where(P[:, 1] < cy - R * 0.55, 0.65, 1.0))
    dpiece(H, "Stripe", "Body", merge(*[A.lathe([(z - 0.1, R * k + 0.025), (z + 0.1, R * k + 0.025), (z + 0.1, R * k - 0.1), (z - 0.1, R * k - 0.1)], axis=2, segs=22, pos=(0, cy, 0), closed=True) for z, k in ((-6.0, 0.985), (3.0, 0.975))]),
           col="secondary", mat="metal", role="detail")
    # sail (conning tower) with fairwater planes, periscopes, hatch seat
    sx0 = -3.2
    rings = []
    for k, y in enumerate(np.linspace(cy + R - 0.3, cy + R + 2.4, 6)):
        f = k / 5
        ln, hw = 3.6 - 0.5 * f, 0.55 - 0.08 * f
        prof = []
        for a in np.linspace(0, TAU, 16, endpoint=False):
            # teardrop plan: round front, tapered back
            c, s = math.cos(a), math.sin(a)
            zz = -ln * 0.3 * c if c > 0 else -ln * 0.7 * c
            prof.append([hw * s * (1 if c > 0 else (1 + c * 0.6)), y, sx0 + zz])
        rings.append(np.array(prof))
    sail_ = A.loft(rings, None, "fan", crease=50)
    planes = merge(A.wing(1.3, 0.8, 0.55, sweep=0.15, thick=0.08, pos=(0.45, cy + R + 1.6, sx0 - 0.9)), A.wing(1.3, 0.8, 0.55, sweep=0.15, thick=0.08, pos=(-0.45, cy + R + 1.6, sx0 - 0.9), side=-1))
    dpiece(H, "Tower", "Body", merge(sail_, planes), col="primary", mat="metal", role="body")
    ty = cy + R + 2.4
    dpiece(H, "Masts", "Body", merge(tube([[0, ty, sx0 + 0.3], [0, ty + 1.8, sx0 + 0.3], [0, ty + 1.9, sx0 - 0.1]], 0.08, 6), box((0.12, 0.18, 0.3), (0, ty + 1.9, sx0 - 0.2), r=0.03),
                                     tube([[0.2, ty, sx0 + 0.9], [0.2, ty + 1.2, sx0 + 0.9]], 0.05, 5), tube([[-0.2, ty, sx0 + 0.6], [-0.2, ty + 0.9, sx0 + 0.6]], 0.04, 5)),
           col="gunmetal", mat="metal", role="detail")
    dpiece(H, "Seat", "Body", merge(A.lathe([(ty, 0.0), (ty, 0.38), (ty + 0.12, 0.38), (ty + 0.12, 0.0)], axis=1, segs=14, pos=(0, 0, sx0 - 0.4)),
                                    box((0.7, 0.6, 0.12), (0, ty + 0.35, sx0 - 0.05), r=0.04, rot=(-60, 0, 0))), col="secondary", mat="metal", role="detail")
    # cruciform tail with rudders + 7-blade propeller on a bone
    tz = 5.6
    tails = [A.wing(1.6, 1.3, 0.8, sweep=0.5, thick=0.07, pos=(0.5, cy, tz)), A.wing(1.6, 1.3, 0.8, sweep=0.5, thick=0.07, pos=(-0.5, cy, tz), side=-1),
             A.fin(1.7, 1.3, 0.8, 0.5, thick=0.07, pos=(0, cy + 0.45, tz)), xform(A.fin(1.5, 1.3, 0.8, 0.5, thick=0.07), (0, cy - 0.45, tz), (0, 0, 180))]
    dpiece(H, "Tail", "Body", merge(*tails), col="primary", mat="metal", role="detail")
    H.bone("Prop", "Body", (0, cy, L / 2 + 0.2))
    dpiece(H, "PropP", "Prop", A.prop(7, 0.95, 0.45, axis="z", pos=(0, cy, L / 2 + 0.3), thick=0.04, hub=(0.22, 0.5)), col="secondary", mat="metal", role="detail")
    # bow planes, torpedo doors, limber holes
    dpiece(H, "BowPlanes", "Body", merge(A.wing(1.0, 0.7, 0.45, sweep=0.15, thick=0.07, pos=(R - 0.1, cy - 0.2, -5.5)), A.wing(1.0, 0.7, 0.45, sweep=0.15, thick=0.07, pos=(-R + 0.1, cy - 0.2, -5.5), side=-1)),
           col="primary", mat="metal", role="detail")
    holes = merge(*[box((0.06, 0.16, 0.5), (R * 0.97 + 0.0, cy + 0.6, z), r=0.03) for z in np.linspace(-4.5, 2.5, 8)])
    dpiece(H, "Holes", "Body", merge(holes, mirror(holes)), col=[0.08, 0.09, 0.1], mat="metal", role="detail", pri=2.2)
    H.mprim("Torp#", "Body", "Cylinder", (0.06, 0.38, 0.38), (0.55, cy - 0.3, -7.25), rot=(0, 0.55, 0), col="darker", role="detail", pri=2.4)
    H.mprim("Lamp#", "Body", "Ball", (0.22, 0.22, 0.22), (0.45, cy + 0.65, -7.35), col="glow", glow=True, role="light", pri=2.6)
    common(H, (0, ty + 0.25, sx0 - 0.4), (0.7, 0.15, 0.7), -8.5, 8.6, ty + 2.0, muzzle=(0, cy - 0.3, -8.2))
    spins = [("Prop", "z", 1, TAU / 7)]

    def extra(name, u, pose):
        if name == "Move":
            A._add(pose, "Body", (0, -0.3, 0, -0.05, 0, 0))

    A.boat_clips(H, size=1.2, spinners=spins, extra=extra)
    return H


# ================================================================================================ jet ski
@hero("jet ski", "boats")
def jet_ski():
    H = V("jet ski")
    H.preview = {"primary": "#FFEB3B", "secondary": "#1565C0"}
    sp = HullSpec(4.2, 1.5, 0.6, bow=0.55, stern=0.1, transom=0.8, bow_rise=1.0, stern_rise=0.0, sheer_bow=0.3, sheer_stern=0.0,
                  p_bow=1.2, p_mid=1.5, p_stern=1.8, flare=0.1, maxat=0.6, deadrise=0.1)
    H.body((0, 0.5, 0))
    hull = A.hull_solid(sp, n=20, nl=20)
    dpiece(H, "Hull", "Body", hull, col="secondary", mat="hard", fallback="Ellipsoid")
    # upper body: a rounded shell over the hull with footwell steps at the sides
    top = sp.top(0.5)
    rings = []
    for t in np.linspace(0.02, 0.98, 14):
        w = sp.beam(t) * 0.92
        y0 = sp.top(t) - 0.02
        hgt = 0.45 * (1 - (1 - t) ** 4) if t < 0.5 else 0.45 - 0.25 * (t - 0.5)
        hw = w * (0.85 if t < 0.35 else 0.55)
        pts = []
        for a in np.linspace(0, math.pi, 11):
            pts.append([hw * math.cos(a), y0 + hgt * math.sin(a) ** 0.7, sp.z(t)])
        pts.append([-w, y0, sp.z(t)])
        pts.append([w, y0, sp.z(t)])
        rings.append(np.array(pts[:-2][::-1] + [[-w, y0, sp.z(t)], [w, y0, sp.z(t)]][::-1]))
    dpiece(H, "Body2", "Body", A.loft([r[np.r_[0:11]] if False else r for r in rings], "fan", "fan", crease=45), col="primary", mat="hard", role="body")
    # saddle seat (the rider sits astride), handlebars on a steering bone, nozzle, mirrors
    dpiece(H, "Seat", "Body", rev([(-0.9, 0), (-0.85, 0.22), (0.0, 0.26), (0.8, 0.22), (0.9, 0)], axis=2, segs=12, pos=(0, top + 0.5, 0.75), scale=(1.15, 0.8, 1.0)),
           col="black", mat="hard", role="detail")
    H.bone("Bars", "Body", (0, top + 0.6, -0.55))
    bars = merge(tube([[0, top + 0.4, -0.6], [0, top + 0.95, -0.45]], 0.08, 8), tube([[-0.6, top + 1.0, -0.38], [0, top + 0.95, -0.45], [0.6, top + 1.0, -0.38]], 0.05, 6),
                 cyl(0.07, 0.25, (0.62, top + 1.0, -0.38), axis=0, segs=8), cyl(0.07, 0.25, (-0.62, top + 1.0, -0.38), axis=0, segs=8), box((0.5, 0.25, 0.25), (0, top + 0.95, -0.58), r=0.08))
    dpiece(H, "Handlebars", "Bars", bars, col="black", role="limb")
    dpiece(H, "Hood", "Body", rev([(-0.6, 0), (-0.5, 0.3), (0.2, 0.35), (0.6, 0)], axis=2, segs=12, pos=(0, top + 0.28, -1.0), scale=(1.4, 0.55, 1.0)), col="secondary", mat="hard", role="detail")
    dpiece(H, "Glass", "Body", A.quad_sheet((-0.35, top + 0.5, -0.82), (0.35, top + 0.5, -0.82), (-0.3, top + 0.75, -0.65), (0.3, top + 0.75, -0.65), nt=4, nu=3, bulge=(0, 0, -0.08), thick=0.02),
           col=TINT, mat="glass", tr=0.3, role="glass", pri=1.8)
    dpiece(H, "Nozzle", "Body", merge(A.lathe([(1.9, 0.0), (1.9, 0.2), (2.25, 0.16), (2.25, 0.1), (2.0, 0.1), (2.0, 0.0)], axis=2, segs=12, pos=(0, 0.35, 0)), box((0.8, 0.06, 0.4), (0, 0.18, 2.1), r=0.02)), col="gunmetal", mat="metal", role="detail")
    H.prim("Light", "Body", "Ball", (0.18, 0.1, 0.12), (0, top + 0.4, -1.55), col="glow", glow=True, role="light", pri=2.6)
    common(H, (0, top + 0.72, 0.75), (0.7, 0.15, 1.6), -2.6, 2.4, top + 1.5)
    H.socket("exhaust", (0, 0.35, 2.3), "Body")

    def extra(name, u, pose):
        if name == "Move":
            A._add(pose, "Body", (0, 0.1, 0, 0.12, 0, -0.1 * math.sin(TAU * u)))
            A._add(pose, "Bars", (0, 0, 0, 0, 0.18 * math.sin(TAU * u), 0))

    A.boat_clips(H, size=0.5, extra=extra)
    return H


# ================================================================================================ hovercraft
@hero("hovercraft", "boats")
def hovercraft():
    H = V("hovercraft", gait="hover")
    H.preview = {"primary": "#F2F2F2", "secondary": "#E53935"}
    L, W = 11.0, 5.4
    H.body((0, 1.0, 0))
    # black rubber skirt: a fat rounded ring loft round a rounded-rectangle plan
    def plan(n, inset=0.0, rr=1.8):
        pts = []
        hl, hw = L / 2 - inset, W / 2 - inset
        r = rr - inset
        for k in range(n):
            a = TAU * k / n
            c, s = math.cos(a), math.sin(a)
            x = (hw - r) * np.sign(c) + r * c
            z = (hl - r) * np.sign(s) + r * s
            pts.append((x, z, c, s))
        return pts
    n = 40
    rings = []
    for x, z, c, s in plan(n):
        pass
    prof = [(0.0, 0.0), (0.35, 0.1), (0.62, 0.45), (0.72, 0.9), (0.6, 1.3), (0.3, 1.45), (0.0, 1.45)]
    rings = []
    for (r_out, y) in prof:
        ring = []
        for x, z, c, s in plan(n):
            ring.append([x + c * (r_out - 0.3) * 1.0, y, z + s * (r_out - 0.3)])
        rings.append(np.array(ring))
    skirt = A.loft(rings, "fan", "fan", crease=50)
    dpiece(H, "Skirt", "Body", skirt, col="tyre", mat="rubber", fallback="Block")
    # hull deck + cabin
    deck = 1.45
    rings = []
    for k, (dy, ins) in enumerate(((0.0, 0.0), (0.5, 0.05), (0.62, 0.25))):
        rings.append(np.array([[x - c * ins, deck + dy, z - s * ins] for x, z, c, s in plan(n, 0.25, 1.6)]))
    dpiece(H, "Hull", "Body", A.loft(rings, "fan", "fan", crease=40), col="primary", mat="hard")
    dpiece(H, "Band", "Body", A.loft([np.array([[x + c * 0.02, deck + dy, z + s * 0.02] for x, z, c, s in plan(n, 0.25, 1.6)]) for dy in (0.15, 0.35)] , None, None, crease=40),
           col="secondary", role="detail") if False else None
    cab = merge(box((3.6, 1.6, 4.8), (0, deck + 1.4, -1.2), r=0.35), box((3.2, 0.2, 4.4), (0, deck + 2.25, -1.2), r=0.1))
    dpiece(H, "Cabin", "Body", cab, col="primary", role="body")
    gl = merge(box((3.0, 0.8, 0.08), (0, deck + 1.65, -3.62), r=0.05, rot=(-12, 0, 0)), windows_x(1.81, deck + 1.65, [-2.2, -1.1, 0.0, 1.1], 0.8, 0.65))
    dpiece(H, "Windows", "Body", gl, col=TINT, mat="glass", role="glass", pri=1.5)
    dpiece(H, "Stripe", "Body", merge(box((3.66, 0.25, 4.0), (0, deck + 0.85, -1.2), r=0.05)), col="secondary", role="detail")
    # two ducted fans + rudders at the stern
    fz = 3.9
    fy = deck + 2.0
    ducts, rud = [], []
    for x in (1.35, -1.35):
        ducts.append(A.lathe([(-0.4, 1.12), (0.4, 1.12), (0.4, 1.28), (-0.4, 1.28)], axis=2, segs=24, pos=(x, fy, fz), closed=True))
        ducts.append(box((0.25, 1.4, 0.4), (x, deck + 0.9, fz), r=0.05))
        rud += [box((0.08, 2.0, 0.6), (x + dx, fy, fz + 0.9), r=0.03) for dx in (-0.4, 0.4)]
    dpiece(H, "Ducts", "Body", merge(*ducts), col="secondary", mat="hard", role="detail")
    dpiece(H, "Rudders", "Body", merge(*rud), col="primary", role="detail")
    H.mbone("Fan#", "Body", (1.35, fy, fz))
    dmpiece(H, "Fan#", "Fan#", merge(A.prop(5, 1.05, 0.4, axis="z", pos=(1.35, fy, fz), thick=0.04, hub=(0.22, 0.5))), col="black", mat="hard", role="detail")
    dpiece(H, "Seat", "Body", merge(box((1.0, 0.4, 0.9), (0, deck + 2.5, -1.0), r=0.1), box((1.0, 0.9, 0.2), (0, deck + 2.9, -0.55), r=0.06),
                                    tube([[-0.9, deck + 2.3, -2.0], [-0.9, deck + 2.9, -2.0], [0.9, deck + 2.9, -2.0], [0.9, deck + 2.3, -2.0]], 0.04, 6)),
           col="secondary", mat="cloth", role="detail")
    H.mprim("HeadLight#", "Body", "Ball", (0.3, 0.2, 0.12), (1.1, deck + 0.4, -5.2), col="glow", glow=True, role="light", pri=2.5)
    common(H, (0, deck + 2.75, -1.0), (1.0, 0.15, 0.9), -6.0, 5.0, deck + 3.6)
    spins = [("FanR", "z", 1, TAU / 5), ("FanL", "z", -1, TAU / 5)]
    A.boat_clips(H, size=0.8, spinners=spins)
    return H


# ================================================================================================ swan paddle boat
@hero("paddle boat", "boats")
def paddle_boat():
    H = V("paddle boat")
    H.preview = {"primary": "#F5F5F5", "secondary": "#FFB300"}
    H.body((0, 1.0, 0))
    # swan body: a plump sculpt hollowed into a two-seat cockpit, raised wings along the sides, tail feathers
    body = ellipsoid(2.0, 1.2, 3.3, (0, 1.15, 0.3))
    body = body.su(ellipsoid(1.6, 0.9, 1.5, (0, 1.4, -2.2)), 0.6)                                   # chest
    body = body.su(round_cone((0, 1.6, 2.9), (0, 2.6, 4.2), 0.9, 0.25), 0.4)                         # tail
    body = body & plane((0, -1, 0), 0.0)                                                             # flat bottom
    for sx in (1, -1):
        wing = ellipsoid(0.45, 1.0, 2.6, (sx * 1.75, 2.0, 0.8)).rot(0, 0, 0)
        wing = wing.su(round_cone((sx * 1.8, 2.3, 2.6), (sx * 1.6, 3.2, 3.6), 0.35, 0.1), 0.3)
        body = body.su(wing, 0.35)
    body = body.ss(round_box(1.25, 1.2, 1.9, 0.5, (0, 2.3, 0.3)), 0.2)                               # cockpit
    H.piece("Hull", "Body", body, col="primary", mat="plastic", tris=2600, res=128, role="body",
            pattern=lambda P: np.where(P[:, 1] < 0.35, 0.75, 1.0))
    # neck + head on bones
    H.bone("Neck", "Body", (0, 1.9, -2.6))
    neck = stube([(0, 1.6, -2.4), (0, 2.6, -3.1), (0, 3.9, -3.0), (0, 4.8, -2.6), (0, 5.3, -2.8)], [0.8, 0.6, 0.48, 0.42, 0.4], k=0.25)
    H.piece("NeckP", "Neck", neck, col="primary", mat="plastic", tris=1200, role="neck")
    H.bone("Head", "Neck", (0, 5.3, -2.85))
    hd = ellipsoid(0.42, 0.42, 0.55, (0, 5.4, -3.0))
    hd = hd.su(ellipsoid(0.2, 0.25, 0.25, (0, 5.25, -3.45)), 0.15)
    H.piece("HeadP", "Head", hd, col="primary", mat="plastic", tris=800, role="head")
    beak = round_cone((0, 5.3, -3.45), (0, 5.12, -4.25), 0.17, 0.06).su(ellipsoid(0.18, 0.18, 0.12, (0, 5.4, -3.5)), 0.05)
    H.piece("Beak", "Head", beak, col="secondary", mat="plastic", tris=500, role="beak")
    H.piece("Knob", "Head", ellipsoid(0.14, 0.2, 0.18, (0, 5.42, -3.5)).su(ellipsoid(0.2, 0.12, 0.2, (0, 5.3, -3.42)), 0.05), col="black", mat="plastic", tris=300, role="detail", pri=1.5)
    H.eyes("Head", (0.3, 5.5, -3.2), 0.085, col="pupil", pupil=None, look=(0.8, 0.1, -0.6))
    # bench with backrest (Seat), a steering stick, pedal wheel at the stern
    dpiece(H, "Seat", "Body", merge(box((2.2, 0.35, 1.0), (0, 1.25, 0.9), r=0.1), box((2.2, 1.0, 0.25), (0, 1.75, 1.5), r=0.1, rot=(-10, 0, 0))), col="secondary", mat="plastic", role="detail")
    dpiece(H, "Console", "Body", merge(box((2.0, 0.5, 0.5), (0, 1.3, -0.9), r=0.12), tube([[0, 1.5, -0.7], [0, 2.1, -0.4]], 0.05, 6), sphere(0.11, (0, 2.15, -0.38))), col=[0.25, 0.55, 0.85], mat="plastic", role="detail")
    H.bone("Wheel", "Body", (0, 0.7, 3.4))
    wh = [cyl(0.15, 1.3, (0, 0.7, 3.4), axis=0, segs=10)]
    for a in np.linspace(0, TAU, 6, endpoint=False):
        wh.append(box((1.0, 0.6, 0.08), (0, 0.7 + 0.45 * math.sin(a), 3.4 + 0.45 * math.cos(a)), r=0.02, rot=(-math.degrees(a) + 90, 0, 0)))
    dpiece(H, "Paddles", "Wheel", merge(*wh), col="secondary", mat="plastic", role="limb")
    common(H, (0, 1.5, 0.9), (2.0, 0.15, 1.0), -4.3, 4.0, 5.8)
    H.socket("head", (0, 5.9, -3.0), "Head")
    H.socket("mouth", (0, 5.2, -4.3), "Head")
    H.rig.update({"head": "Head"})
    spins = [("Wheel", "x", -1, TAU / 6)]

    def extra(name, u, pose):
        A._add(pose, "Neck", (0, 0, 0, 0.05 * math.sin(TAU * u), 0.06 * math.sin(TAU * u * (1 if name == "Idle" else 2)), 0))
        A._add(pose, "Head", (0, 0, 0, -0.08 * math.sin(TAU * u + 1), 0, 0))
        if name == "Attack":
            k = A.pulse(u, 0.1, 0.7)
            A._add(pose, "Neck", (0, 0, 0, -0.5 * k, 0, 0))
            A._add(pose, "Head", (0, 0, 0, -0.3 * k, 0, 0))

    A.boat_clips(H, size=0.7, spinners=spins, extra=extra)
    return H


# ================================================================================================ warships
def _warship(hid, carrier=False):
    H = V(hid)
    H.preview = {"primary": "#607D8B", "secondary": "#37474F"}
    L, Bm = (30.0, 6.2) if not carrier else (32.0, 6.6)
    sp = HullSpec(L, Bm, 3.0, bow=0.85, stern=0.1, transom=0.7, bow_rise=0.7, stern_rise=0.1, sheer_bow=0.45, sheer_stern=0.0,
                  p_bow=1.2, p_mid=2.6, p_stern=2.8, flare=0.1, maxat=0.55)
    H.body((0, 1.8, 0))
    deck = 2.9
    dpiece(H, "Hull", "Body", A.hull_shell(sp, th=0.15, n=24, nl=27, floor=deck), col="primary", mat="metal", fallback="Ellipsoid", pattern=waterline(0.7, 0.95, 0.45))
    dpiece(H, "Deck", "Body", A.planks(2.9, -13.5, 14.5, deck + 0.04, n=7, gap=0.04, th=0.05, width_fn=lambda z: sp.half_width(z, deck + 0.08, 0.17)),
           col=[0.5, 0.42, 0.33] if not carrier else "secondary", mat="wood", role="detail")
    if not carrier:
        # superstructure: stepped bridge tower, funnel, masts
        sup = merge(box((3.6, 1.6, 6.0), (0, deck + 0.8, -1.0), r=0.1), box((2.8, 1.4, 3.2), (0, deck + 2.3, -2.2), r=0.1), box((2.2, 1.2, 1.8), (0, deck + 3.6, -2.8), r=0.1),
                    box((4.0, 0.15, 1.2), (0, deck + 4.25, -2.8), r=0.04))
        dpiece(H, "Super", "Body", sup, col="primary", mat="metal", role="body")
        dpiece(H, "Bridge", "Body", merge(box((2.27, 0.35, 1.0), (0, deck + 3.85, -3.0), r=0.03), box((1.8, 0.35, 0.07), (0, deck + 3.85, -3.72), r=0.03)), col=TINT, mat="glass", role="glass", pri=1.5)
        fun = A.lathe([(deck + 2.9, 0.0), (deck + 2.9, 0.8), (deck + 5.4, 0.7), (deck + 5.4, 0.0)], axis=1, segs=14, pos=(0, 0, 1.4), scale=(0.9, 1, 1.3), rot=(-8, 0, 0))
        mast_ = merge(tube([[0, deck + 4.3, -2.6], [0, deck + 8.5, -2.4]], 0.1, 6), box((2.4, 0.1, 0.1), (0, deck + 7.4, -2.45)), box((0.9, 0.6, 0.12), (0, deck + 8.0, -2.4), r=0.04),
                      tube([[0, deck + 1.6, 3.4], [0, deck + 6.0, 3.6]], 0.08, 6))
        dpiece(H, "Funnel", "Body", merge(fun, mast_), col="secondary", mat="metal", role="detail")
        # three triple turrets on bones (they train round for the attack)
        guns = []
        for i, (z, y, d) in enumerate(((-8.5, deck, -1), (-5.6, deck + 0.9, -1), (8.0, deck, 1))):
            b = H.bone(f"Turret{i + 1}", "Body", (0, y, z))
            tur = A.lathe([(y, 0.0), (y, 1.55), (y + 0.8, 1.35), (y + 1.0, 1.1), (y + 1.0, 0.0)], axis=1, segs=16, pos=(0, 0, z), scale=(1, 1, 1.25))
            dpiece(H, f"TurretP{i + 1}", b, tur, col="primary", mat="metal", role="detail")
            bar = [cyl(0.13, 3.6, (x, y + 0.55, z + d * 3.0), axis=2, segs=8, r2=0.1) for x in (-0.45, 0.0, 0.45)]
            dpiece(H, f"Guns{i + 1}", b, merge(*bar), col="gunmetal", mat="metal", role="detail")
            guns.append(b)
        seat_pos = (0, deck + 4.4, -2.0)
        dpiece(H, "Seat", "Body", merge(box((0.9, 0.35, 0.8), (0, deck + 4.5, -2.0), r=0.08), box((0.9, 0.8, 0.18), (0, deck + 4.9, -1.6), r=0.06)), col="secondary", mat="cloth", role="detail")
        muzzle = (0, deck + 0.55, -12.2)
    else:
        # flight deck overhanging the hull, island on the starboard side, parked jets
        fd = []
        rings = []
        for z in np.linspace(-15.5, 15.5, 12):
            w = 4.6 if abs(z) < 12 else 4.6 - (abs(z) - 12) * 0.5
            rings.append(np.array([[w, deck + 1.2, z], [w, deck + 1.55, z], [-w, deck + 1.55, z], [-w, deck + 1.2, z]]))
        fd.append(A.loft(rings, "fan", "fan", crease=35))
        fd += [box((3.0, 1.3, 20.0), (0, deck + 0.6, 0.0), r=0.05)]
        dpiece(H, "FlightDeck", "Body", merge(*fd), col="secondary", mat="metal", role="body")
        dpiece(H, "DeckLines", "Body", merge(box((0.15, 0.06, 28.0), (0, deck + 1.56, 0.0)), box((0.15, 0.06, 14.0), (-1.4, deck + 1.56, 6.0), rot=(0, -9, 0)),
                                              *[box((0.12, 0.06, 1.2), (-2.5, deck + 1.56, z)) for z in np.linspace(-12, 12, 9)]), col="white", role="detail", pri=2)
        isl = merge(box((1.4, 3.2, 6.0), (3.6, deck + 3.1, 2.0), r=0.1), box((1.2, 1.2, 2.5), (3.6, deck + 5.3, 1.0), r=0.1), tube([[3.6, deck + 5.9, 1.5], [3.6, deck + 8.5, 1.5]], 0.1, 6),
                    box((0.15, 0.6, 2.0), (3.6, deck + 7.6, 1.5), r=0.03))
        dpiece(H, "Island", "Body", isl, col="primary", mat="metal", role="detail")
        dpiece(H, "Bridge", "Body", merge(box((1.47, 0.35, 2.3), (3.6, deck + 5.4, 1.0), r=0.03)), col=TINT, mat="glass", role="glass", pri=1.5)
        jets = []
        for x, z, a in ((-2.2, -9.0, 30), (-2.4, -4.5, 30), (1.6, 9.0, -150), (-2.2, 9.5, 20)):
            jt = merge(rev([(-1.4, 0), (-1.1, 0.18), (0.2, 0.28), (1.2, 0.22), (1.3, 0)], axis=2, segs=8, spline=2),
                       A.wing(1.1, 1.4, 0.3, sweep=1.1, thick=0.08, pos=(0.1, 0, -0.3)), A.wing(1.1, 1.4, 0.3, sweep=1.1, thick=0.08, pos=(-0.1, 0, -0.3), side=-1),
                       A.fin(0.6, 0.6, 0.25, 0.4, thick=0.06, pos=(0, 0.15, 0.6)))
            jets.append(xform(jt, (x, deck + 1.82, z), (0, a, 0)))
        dpiece(H, "Jets", "Body", merge(*jets), col="metal", mat="metal", role="detail")
        guns = []
        seat_pos = (3.6, deck + 6.05, 0.0)
        dpiece(H, "Seat", "Body", merge(box((0.9, 0.35, 0.8), (3.6, deck + 6.1, -0.3), r=0.08), box((0.9, 0.8, 0.18), (3.6, deck + 6.5, 0.1), r=0.06)), col="secondary", mat="cloth", role="detail")
        muzzle = None
    dpiece(H, "Rails", "Body", deck_rail(sp, lambda t: deck, 0.03, 0.97, h=0.5, inset=0.17, n=16, r=0.03), col="white", mat="metal", role="detail", pri=2.3)
    dpiece(H, "Anchors", "Body", merge(*[box((0.1, 0.6, 0.5), (s * sp.half_width(-12.5, deck - 0.6, 0.0), deck - 0.6, -12.5), r=0.05) for s in (1, -1)]), col="darker", mat="metal", role="detail", pri=2.5)
    H.bone("Flag", "Body", (0, deck + (8.5 if not carrier else 8.5), -2.4 if not carrier else 1.5))
    dpiece(H, "FlagP", "Flag", flag((0 if not carrier else 3.6, deck + 8.4, -2.35 if not carrier else 1.55), 1.4, 0.8), col="secondary" if carrier else "red", mat="cloth", role="detail")
    common(H, (seat_pos[0], seat_pos[1] + 0.25, seat_pos[2]), (0.9, 0.15, 0.8), -15.5, 15.5, deck + 9.0, muzzle=muzzle)

    def extra(name, u, pose):
        A._add(pose, "Flag", (0, 0, 0, 0, 0.25 * math.sin(TAU * u * 2), 0))
        if name == "Attack" and guns:
            k = A.pulse(u, 0.0, 1.0)
            for i, b in enumerate(guns):
                A._add(pose, b, (0, 0, 0, 0, (0.5 if i < 2 else -0.5) * k, 0))

    A.boat_clips(H, size=2.0, extra=extra, attack="broadside")
    return H


@hero("battleship", "boats")
def battleship():
    return _warship("battleship")


@hero("aircraft carrier", "boats")
def aircraft_carrier():
    return _warship("aircraft carrier", carrier=True)


# ================================================================================================ word map
B = VEH_ = {"cat": ["Vehicle", "Machine", "Object"]}
MAP = [
    ("rowboat", "rowboat, row boat, rowing boat, dinghy, skiff, lifeboat, coracle, row, inflatable boat, rubber boat, banana boat, glass bottom boat, toy boat, boat, lantern boat, magic boat, giant leaf boat, log flume, bathtub boat", B),
    ("canoe", "canoe, kayak, dugout, war canoe, outrigger, punt, dragon boat", B),
    ("speedboat", "speedboat, speed boat, powerboat, motorboat, jet boat, police boat, fireboat, hydroplane, hydrofoil, torpedo boat, airboat, water skis", B),
    ("sailboat", "sailboat, sail boat, yacht, catamaran, dhow, ice yacht, sail, junk ship, junk", B),
    ("super yacht", "super yacht, superyacht, mega yacht, luxury yacht, cruise ship, ferry, research vessel, royal barge, pontoon boat, houseboat", B),
    ("ship", "ship, sailing ship, tall ship, galleon, frigate, schooner, clipper ship, ship of the line, noahs ark, ark, flying ship, cloud ship, trireme, treasure galleon", B),
    ("pirate ship", "pirate ship, pirate boat, pirate galleon, ghost ship, skeleton ship, buccaneer ship", B),
    ("viking longship", "viking longship, longship, viking ship, drakkar", B),
    ("paddle steamer", "paddle steamer, riverboat, steamboat, steamship, paddlewheel", B),
    ("tugboat", "tugboat, tug boat, tug, icebreaker, minesweeper, landing craft boat, barge, cargo ship", B),
    ("fishing boat", "fishing boat, trawler, fishing trawler", B),
    ("raft", "raft, life raft, log raft", B),
    ("gondola", "gondola", B),
    ("submarine", "submarine, sub, u boat, mini submarine, nautilus submarine, bathysphere", B),
    ("jet ski", "jet ski, jetski, water scooter", B),
    ("hovercraft", "hovercraft, hover craft", B),
    ("battleship", "battleship, warship, destroyer, dreadnought, cruiser ship, ironclad, fleet, frigate warship", B),
    ("aircraft carrier", "aircraft carrier, carrier ship, supercarrier", B),
    ("paddle boat", "paddle boat, pedal boat, pedalo, swan boat, pedal swan, rubber duck boat", B),
]
