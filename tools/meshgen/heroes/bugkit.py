"""Shared sculpt / rig helpers for the bugs hero family (h_bugs*.py): arthropod legs, antennae, compound eyes,
membrane wings, wing pattern masks."""
import math

import numpy as np

import sdf as S
from sdf import sphere, ellipsoid, capsule, round_cone, tube, plane, torus  # noqa: F401
from kit import Hero, hero, stripes, spots, gradient, combine
import motion_bugs as MB

BUG = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Plant", "Weather", "Structure", "Vehicle"]}


def A(*v):
    if len(v) == 1:
        return np.array(v[0], float)
    return np.array(v, float)


def T(v):
    return tuple(float(x) for x in v)


# ------------------------------------------------------------------------------------------------ sdf helpers
def e2(cx, cz, ax, az, ang=0.0):
    """Infinite elliptic prism along Y (a 2D ellipse in the XZ plane, rotated by ang degrees about Y)."""
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    m = min(ax, az)

    def f(p):
        x = p[:, 0] - cx
        z = p[:, 2] - cz
        u = c * x + s * z
        v = -s * x + c * z
        k = np.sqrt((u / ax) ** 2 + (v / az) ** 2)
        return (k - 1.0) * m

    return S.SDF(f)


def slab(t, y=0.0):
    return S.SDF(lambda p: np.abs(p[:, 1] - y) - t)


def membrane(plan, t, camber=0.0):
    """A thin wing: a planform (Y-prism SDF) cut to a slab of half thickness t with rounded edges, optionally
    cambered (y += camber * (x^2)) so it is not dead flat."""
    w = plan.si(slab(t), t * 0.8)
    if camber:
        w = w.warp(lambda p: np.column_stack([p[:, 0], p[:, 1] - camber * (p[:, 0] ** 2 + 0.3 * p[:, 2] ** 2), p[:, 2]]))
    return w


def place(sd, rot, at):
    """Rotate (degrees) then move a local sculpt to `at`."""
    return sd.rot(*rot).at(*at)


# ------------------------------------------------------------------------------------------------ leg helper
def leg(H, tag, hip, knee, ankle, tip, r, col="primary", mat="hard", pat=None, tris=(300, 260, 220), parent="Body",
        spines=0, spine_len=0.12, hair=0.0, claw=True, femur=None, tibia=None, pri=1.3, beads=3, tarsus_col=None):
    """A three-segment arthropod leg (right side; mirrored). Bones Leg<tag>#, Knee<tag>#, Foot<tag>#; pieces
    Femur<tag># (with the coxa ball), Tibia<tag>#, Tarsus<tag># (beaded, with a claw). Returns the bone names."""
    hip, knee, ankle, tip = A(hip), A(knee), A(ankle), A(tip)
    r0, r1, r2, r3 = r
    b0, b1, b2 = f"Leg{tag}#", f"Knee{tag}#", f"Foot{tag}#"
    H.mbone(b0, parent, T(hip))
    H.mbone(b1, b0, T(knee))
    H.mbone(b2, b1, T(ankle))
    fm = femur if femur is not None else round_cone(T(hip), T(knee), r0, r1 * 1.05)
    fm = fm.su(sphere(r0 * 1.2, T(hip)), r0 * 0.4).su(sphere(r1 * 1.18, T(knee)), r1 * 0.35)
    tb = tibia if tibia is not None else round_cone(T(knee), T(ankle), r1 * 0.95, r2)
    tb = tb.su(sphere(r2 * 1.15, T(ankle)), r2 * 0.3)
    if spines:
        d = ankle - knee
        L = np.linalg.norm(d)
        d = d / L
        side = np.cross(d, A(0, 0, 1))
        if np.linalg.norm(side) < 1e-3:
            side = A(1, 0, 0)
        side = side / np.linalg.norm(side)
        for i in range(spines):
            t = 0.2 + 0.7 * i / max(spines - 1, 1)
            c = knee + d * L * t
            for sg in (1, -1):
                out = c + (side * sg * 0.6 + d * 0.5 + A(0, -0.4, 0)) * spine_len
                tb = tb.su(round_cone(T(c), T(out), r2 * 0.45, r2 * 0.12), r2 * 0.2)
    if hair:
        fm = fm.noise(hair, 6.0 / max(r0, 0.05) * 0.25, 3)
        tb = tb.noise(hair * 0.8, 6.0 / max(r1, 0.05) * 0.25, 4)
    mid = ankle + (tip - ankle) * 0.55 + A(0, 0.03, 0)
    ts = tube([T(ankle), T(mid), T(tip)], [r2 * 0.95, r3 * 1.05, r3 * 0.85], k=0.02)
    for i in range(1, beads):
        c = ankle + (tip - ankle) * (i / beads)
        ts = ts.su(sphere(r3 * 1.25, T(c)), r3 * 0.3)
    if claw:
        d = tip - ankle
        d = d / np.linalg.norm(d)
        ts = ts.su(round_cone(T(tip), T(tip + d * r3 * 2.6 + A(0, -r3 * 1.0, 0)), r3 * 0.7, r3 * 0.22), r3 * 0.3)
    H.mpiece(f"Femur{tag}#", b0, fm, col=col, mat=mat, tris=tris[0], role="limb", pattern=pat, pri=pri)
    H.mpiece(f"Tibia{tag}#", b1, tb, col=col, mat=mat, tris=tris[1], role="limb", pattern=pat, pri=pri + 0.1)
    H.mpiece(f"Tarsus{tag}#", b2, ts, col=tarsus_col or col, mat=mat, tris=tris[2], role="foot", pattern=pat, pri=pri + 0.2)
    return b0, b1, b2


def legspec(hip, yaw, knee_r, knee_y, ank_r, ank_y, tip_r, tip_y=0.05, ank_yaw=None, tip_yaw=None):
    """Positions of a sprawled leg from its hip: yaw (deg, + = forward) of the leg plane, radial reaches and heights."""
    hip = A(hip)

    def at(rr, yy, yw):
        a = math.radians(yw)
        return A(hip[0] + rr * math.cos(a), yy, hip[2] - rr * math.sin(a))

    return hip, at(knee_r, knee_y, yaw), at(ank_r, ank_y, yaw if ank_yaw is None else ank_yaw), at(tip_r, tip_y, yaw if tip_yaw is None else tip_yaw)


def antenna(H, tag, base, pts, r0, r1, col="dark", kind="thread", club=0.0, feather=0.0, parent="Head", tris=260, pri=1.6, mat="hard"):
    """Right antenna through `pts` (absolute, first = base); mirrored. kind: thread, club, feather, elbow."""
    pts = [A(p) for p in pts]
    H.mbone(f"Ant{tag}#", parent, T(base))
    n = len(pts)
    radii = [r0 + (r1 - r0) * i / (n - 1) for i in range(n)]
    sd = tube([T(p) for p in pts], radii, k=0.01)
    sd = sd.su(sphere(r0 * 1.4, T(pts[0])), r0 * 0.4)
    if kind == "elbow":
        sd = sd.su(sphere(r0 * 1.2, T(pts[1])), r0 * 0.3)
    if club:
        d = pts[-1] - pts[-2]
        d = d / np.linalg.norm(d)
        sd = sd.su(round_cone(T(pts[-1] - d * club * 1.6), T(pts[-1] + d * club * 0.3), club * 0.55, club), club * 0.3)
    if feather:
        # bipectinate (moth): side branches along the shaft, flattened into a leaf shape
        for i in range(1, 9):
            t = i / 9.5
            seg = int(t * (n - 1))
            f = t * (n - 1) - seg
            c = pts[seg] + (pts[min(seg + 1, n - 1)] - pts[seg]) * f
            d = pts[min(seg + 1, n - 1)] - pts[seg]
            d = d / np.linalg.norm(d)
            side = np.cross(d, A(0, 1, 0))
            side = side / max(np.linalg.norm(side), 1e-6)
            ln = feather * math.sin(math.pi * (t * 0.9 + 0.05))
            for sg in (1, -1):
                sd = sd.su(round_cone(T(c), T(c + side * sg * ln + d * ln * 0.4), r0 * 0.5, r0 * 0.25), r0 * 0.3)
    H.mpiece(f"Antenna{tag}#", f"Ant{tag}#", sd, col=col, mat=mat, tris=tris, role="detail", pri=pri, smooth=2, res=120)
    return f"Ant{tag}R", f"Ant{tag}L"


def bug_eyes(H, bone, pos, r, col="bugEye", shine=True, pri=1.25, flat=1.0):
    """Compound eyes: a glossy ellipsoid (mirrored) with a small specular dot."""
    x, y, z = pos
    H.mprim("Eye#", bone, "Ellipsoid", (r * 2 * flat, r * 2, r * 2), (x, y, z), col=col, mat="glass" if False else "hard", pri=pri, role="eye")
    if shine:
        H.mprim("Shine#", bone, "Ball", (r * 0.38,) * 3, (x + r * 0.55 * flat, y + r * 0.55, z - r * 0.5), col="shine", mat="hard", pri=pri + 1.2, role="shine")


def legs_rig(names, phases, scales=None):
    """[(bones(R,L)...)] -> walker leg dicts. names: list of (b0, b1, b2) base names with '#'. phases: per pair the
    phase of the RIGHT leg (left gets +0.5)."""
    out = []
    for i, (b0, b1, b2) in enumerate(names):
        for side, ch in ((1, "R"), (-1, "L")):
            ph = phases[i] + (0.0 if side > 0 else 0.5)
            out.append({"hip": b0.replace("#", ch), "knee": b1.replace("#", ch), "foot": b2.replace("#", ch), "side": side,
                        "phase": ph % 1.0, "scale": (scales[i] if scales else 1.0), "front": 1 if i == 0 else (-1 if i == len(names) - 1 else 0)})
    return out


def wing_bones(H, tag, pos, parent="Body"):
    H.mbone(f"{tag}#", parent, pos)
    return f"{tag}R", f"{tag}L"


def veins(root, n=6, depth=0.25, width=0.05, spread=1.0):
    """Wing vein mask: dark radial lines fanning out from the wing root (right side; the kit mirrors the left)."""
    root = A(root)

    def f(P):
        d = P - root
        ang = np.arctan2(-d[:, 2], np.abs(d[:, 0]) + 1e-6) * spread
        u = np.mod(ang / (math.pi / 2) * n, 1.0)
        line = np.clip(1 - np.abs(u - 0.5) / (width * 0.5 * n), 0, 1)
        rr = np.linalg.norm(d[:, [0, 2]], axis=1)
        line = line * np.clip(rr * 2.0, 0, 1)
        return 1 - depth * np.clip(line * 2, 0, 1)

    return f


def border(plan_fn, w, depth=0.85):
    """Dark wing border: darken where the planform SDF is within w of the edge."""

    def f(P):
        d = plan_fn(P)
        return 1 - depth * np.clip((d + w) / (w * 0.35), 0, 1)

    return f


def region(fn, depth):
    """Darken by depth * fn(P) (fn in 0..1)."""
    return lambda P: 1 - depth * np.clip(fn(P), 0, 1)


def blob_mask(c, r, soft=0.3):
    c = A(c)

    def f(P):
        d = np.linalg.norm(P - c, axis=1)
        return np.clip((r - d) / (r * soft), 0, 1)

    return f


def mirror_mask(fn):
    """Evaluate fn on |x| (so a right-side spot list also marks the left side of a centred piece)."""

    def f(P):
        Q = P.copy()
        Q[:, 0] = np.abs(Q[:, 0])
        return fn(Q)

    return f


def finish(H, head="Head", jaw=None, tail=(), mouth=(0, 1, -2), top=(0, 2, -1), mouth_bone="Head", height=1.0, legs=None):
    H.socket("mouth", T(mouth), mouth_bone)
    H.socket("head", T(top), head)
    H.rig.update({"head": head, "tail": list(tail)})
    if jaw:
        H.rig["jaw"] = jaw
    if legs:
        H.rig["legs"] = [{"hip": L["hip"], "knee": L["knee"], "phase": L["phase"], "side": L["side"]} for L in legs]


def orient(sd, yaw=0.0, lift=0.0, roll=0.0, at=(0, 0, 0)):
    """Orient a sculpt built along +X from the origin: roll about X, raise the tip by `lift` (deg about Z), then yaw
    (deg about Y, + = toward the front, - = folded back), then move to `at`."""
    return sd.rot(roll, 0, 0).rot(0, 0, lift).rot(0, yaw, 0).at(*at)


def clear_wing(H, tag, root, span, chord, yaw=0.0, lift=0.0, roll=0.0, t=0.022, col="wingGlass", tr=0.45, plan=None, vein_n=6,
               parent="Body", tris=360, pri=1.8, extra_pat=None, camber=0.03, base_w=None):
    """A glassy membrane wing (right side, mirrored) on bone <tag>#: built along +X with `span` and `chord`, then
    oriented (orient) at `root`."""
    root = A(root)
    H.mbone(f"{tag}#", parent, T(root))
    if plan is None:
        plan = e2(span * 0.53, chord * 0.05, span * 0.5, chord * 0.5, 4)
        plan = plan.su(e2(span * 0.12, 0.0, span * 0.16, (base_w or chord * 0.2), 0), chord * 0.1)
        plan = plan & S.SDF(lambda p: -p[:, 0] - 0.0)
    sd = orient(membrane(plan, t, camber), yaw, lift, roll, T(root))
    pat = combine(lambda P: veins(root, n=vein_n, depth=0.3, width=0.04)(P), extra_pat)
    H.mpiece(f"{tag}P#", f"{tag}#", sd, col=col, mat="glass", tr=tr, tris=tris, role="wing", pattern=pat, pri=pri, res=150, smooth=2, ao=False)
    return f"{tag}R", f"{tag}L"




def poly2(pts):
    """Infinite prism along Y whose XZ cross-section is the polygon `pts` [(x, z), ...] (exact 2D SDF, any polygon)."""
    V = np.array(pts, float)
    N = len(V)

    def f(p):
        P = p[:, [0, 2]]
        d = ((P - V[0]) ** 2).sum(1)
        sgn = np.ones(len(P))
        j = N - 1
        for i in range(N):
            e = V[j] - V[i]
            w = P - V[i]
            b = w - e * np.clip((w @ e) / (e @ e), 0, 1)[:, None]
            d = np.minimum(d, (b * b).sum(1))
            c1 = P[:, 1] >= V[i][1]
            c2 = P[:, 1] < V[j][1]
            c3 = e[0] * w[:, 1] > e[1] * w[:, 0]
            flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
            sgn = np.where(flip, -sgn, sgn)
            j = i
        return sgn * np.sqrt(d)

    return S.SDF(f)


def smooth_poly(pts, r):
    """Rounded polygon planform: polygon shrunk then inflated by r (round corners)."""
    return poly2(pts).round(r) if r < 0 else poly2(pts)


def hairy(sd, amp, freq, seed=0):
    return sd.noise(amp, freq, seed) if amp > 0 else sd


def surface_cut(body, region, depth=0.03, k=0.015):
    """Carve `region` (e.g. a slab or a periodic groove field) out of `body` only within `depth` of its surface, so
    grooves and seams stay shallow instead of slicing through the whole sculpt."""
    cut = region & S.SDF(lambda p: -(body(p) + depth))
    return body.ss(cut, k)


def zgrooves(z0, period, width, ymin=-1e9):
    """Periodic grooves across Z (true distances): |frac| bands of half width `width`, above ymin."""
    def f(p):
        u = np.mod(p[:, 2] - z0, period) - period * 0.5
        return np.maximum(np.abs(np.abs(u) - period * 0.5) - width, ymin - p[:, 1])
    return S.SDF(f)
