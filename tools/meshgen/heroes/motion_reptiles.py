"""Motion cycles + small sculpt helpers for the reptile / amphibian / dinosaur families (h_reptiles.py, h_dinosaurs.py).

Cycles (sampled into keyframe clips by Hero.clip):
  sprawl     lizards, crocodilians, salamanders, turtles: sprawled legs that yaw fore/aft and lift, an S-bending trunk,
             a travelling tail wave; attacks "snap", "roll" (crocodile death roll), "tongue", "frill", "tailwhip".
  slither    snakes: a travelling wave down a bone chain (lateral undulation), raised-front pose for cobras;
             attack "strike" (coil back, lunge, jaw gape).
  hop        frogs / toads: crouch, launch, airborne tuck, land; attack "tongue".
  flipper    sea turtles, plesiosaurs: four-flipper underwater flight; attack bite / ram.
  swimtail   mosasaurs, axolotls (water): body + tail wave, limbs tucked.
  fly        pterosaurs: flap with lagging wing tips, glide; attack dive-peck.
  theropod   two-legged dinosaurs: digitigrade legs, balancing tail, head bob; attacks "bite", "headbutt".
Sign conventions follow motion.py (+rx on a down-hanging limb swings it forward, -rx opens a forward jaw, +ry turns the
model's right side forward, +rz rolls / lifts a right-side limb sticking out along +X).

Sculpt helpers (SDF): eloft (elliptical-section loft along a polyline), squash, grid_bumps (repeated scute bumps).
NOTE build.py hashes only the h_*.py files: after changing a sculpt helper here rebuild with --force.
"""
import math

import numpy as np

import sdf as S

TAU = 2 * math.pi


# ================================================================================================ sculpt helpers
def _smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def eloft(points, rx, ry, k=0.0):
    """Smooth chain of elliptical-section segments through `points` (x = lateral radius, y = vertical radius per
    point). Cross-section frame follows each segment (lateral = up x dir). Ends are rounded."""
    P = [np.asarray(p, float) for p in points]
    RX = list(rx) if hasattr(rx, "__len__") else [rx] * len(P)
    RY = list(ry) if hasattr(ry, "__len__") else [ry] * len(P)
    segs = []
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]
        d = b - a
        L = float(np.linalg.norm(d))
        dr = d / L
        up = np.array([0.0, 1.0, 0.0])
        lat = np.cross(up, dr)
        if np.linalg.norm(lat) < 1e-4:
            lat = np.array([1.0, 0.0, 0.0])
        lat /= np.linalg.norm(lat)
        ver = np.cross(dr, lat)
        segs.append((a, dr, L, lat, ver, RX[i], RX[i + 1], RY[i], RY[i + 1]))

    def f(p):
        out = None
        for a, dr, L, lat, ver, rx0, rx1, ry0, ry1 in segs:
            q = p - a
            al = q @ dr
            t = np.clip(al / L, 0, 1)
            rxx = rx0 + (rx1 - rx0) * t
            ryy = ry0 + (ry1 - ry0) * t
            over = al - t * L
            dx = q @ lat
            dy = q @ ver
            m = np.minimum(rxx, ryy)
            e = np.sqrt((dx / rxx) ** 2 + (dy / ryy) ** 2 + (over / m) ** 2)
            d = (e - 1.0) * m
            out = d if out is None else _smin(out, d, k * 0.2)  # consecutive segments already meet: only soften bends
        return out

    return S.SDF(f)


def squash(sd, axis, f, c=0.0):
    """Scale a shape by f along one axis about coordinate c (approximate distance)."""
    m = min(f, 1.0)

    def g(p):
        q = p.copy()
        q[:, axis] = c + (p[:, axis] - c) / f
        return sd(q) * m

    return S.SDF(g)


def grid_bumps(xs, z0, z1, dz, yfn, r, ry=None, rz=None, jitter=0.0):
    """Rows of ellipsoid bumps (scutes / osteoderms / warts): for each lateral offset x in xs, bumps every dz along
    z in [z0, z1] centred at y = yfn(z, x). Domain repetition: one ellipsoid evaluation per row."""
    ry = ry if ry is not None else r
    rz = rz if rz is not None else r
    n = max(1, int(round((z1 - z0) / dz)))
    dz = (z1 - z0) / n

    def f(p):
        out = None
        cell = np.clip(np.floor((p[:, 2] - z0) / dz), 0, n - 1)
        for j, x in enumerate(xs):
            sh = 0.5 * dz * (j % 2) * jitter
            cz = z0 + (np.clip(np.floor((p[:, 2] - z0 - sh) / dz), 0, n - 1) + 0.5) * dz + sh
            cy = yfn(cz, x)
            q = np.stack([(p[:, 0] - x) / r, (p[:, 1] - cy) / ry, (p[:, 2] - cz) / rz], 1)
            k0 = np.linalg.norm(q, axis=1)
            d = (k0 - 1.0) * min(r, ry, rz)
            out = d if out is None else np.minimum(out, d)
        return out

    return S.SDF(f)


def spikes(base_pts, tip_pts, r0, r1=0.01):
    """Union of round cones (spines, horns, plates, teeth)."""
    s = None
    for a, b in zip(base_pts, tip_pts):
        c = S.round_cone(tuple(a), tuple(b), r0, r1)
        s = c if s is None else (s | c)
    return s


# ================================================================================================ motion helpers
def _add(pose, bone, v):
    if bone is None:
        return
    o = list(pose.get(bone, (0.0,) * 6))
    for i, x in enumerate(v):
        o[i] += x
    pose[bone] = tuple(o)


def _ease(x):
    return 0.5 - 0.5 * math.cos(math.pi * min(max(x, 0.0), 1.0))


def _win(s, a, b):
    """0 -> 1 -> 0 bump over s in [a, b]."""
    if s <= a or s >= b:
        return 0.0
    return math.sin(math.pi * (s - a) / (b - a))


def _ramp(s, a, b):
    return _ease((s - a) / (b - a)) if b > a else float(s >= a)


def _tlist(tongue):
    """tongue: (bone, dist, axis) or a list of them (telescoping tongue segments)."""
    if tongue and isinstance(tongue[0], str):
        return [tongue]
    return list(tongue or [])


def _scale_pose(pose, k):
    return {b: tuple(x * k for x in v) for b, v in pose.items()}


def _sprawl_leg(u, stride, lift, duty=0.6):
    """Forward amount (+ = foot forward) and lift (0..1) of a sprawled leg over a cycle."""
    u = u % 1.0
    if u < duty:
        s = u / duty
        return stride * (1 - 2 * s), 0.0
    s = (u - duty) / (1 - duty)
    return stride * (-1 + 2 * _ease(s)), math.sin(math.pi * s)


def hit_clip(H, height, head=None, neck=None, jaw=None, tail=(), roll=0.05):
    def hit(t):
        s = t / 0.4
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0.03 * height * k, 0.1 * height * k, 0.12 * k, 0, roll * math.sin(t * 40) * k))
        _add(pose, neck, (0, 0, 0, 0.2 * k, 0, 0))
        _add(pose, head, (0, 0, 0, 0.18 * k, 0.12 * k, 0))
        _add(pose, jaw, (0, 0, 0, -0.35 * k, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.12 * k, 0.15 * k * (1 if i % 2 else -1), 0))
        return pose

    H.clip("Hit", 0.4, hit, keys=8, loop=False)


# ================================================================================================ sprawl
def sprawl(H, legs, front=None, hips=None, neck=None, head=None, jaw=None, tail=(), stride=0.5, lift=0.45, walk=1.0,
           bend=0.14, height=1.0, attack="snap", tongue=None, frill=(), extra_idle=None, belly_drag=0.0, tailwave=0.22,
           tail_curl=False):
    """legs: (upper, lower, foot, phase, side(+1 right / -1 left), front?). Diagonal pairs: RF & LH phase 0,
    LF & RH phase 0.5. front / hips: the shoulder and pelvis bones that bend the trunk (S-curve)."""

    def legpose(pose, u, amp=1.0):
        for up, lo, ft, ph, side, fr in legs:
            f, l = _sprawl_leg(u + ph, stride * amp, lift)
            _add(pose, up, (0, 0, 0, 0.12 * l * amp, side * f, side * l * lift * 0.9 * amp))
            _add(pose, lo, (0, 0, 0, (0.25 if fr else -0.15) * l * amp, 0, -side * l * lift * 0.55 * amp))
            _add(pose, ft, (0, 0, 0, (0.35 if fr else -0.3) * l * amp, -side * f * 0.9, 0))

    def move(t):
        u = t / walk
        c = math.cos(TAU * u)
        pose = {}
        legpose(pose, u)
        _add(pose, front, (0, 0, 0, 0, bend * c, 0.03 * c))
        _add(pose, hips, (0, 0, 0, 0, -bend * c, -0.03 * c))
        _add(pose, "Body", (0, 0.02 * height * abs(math.sin(TAU * u)) - belly_drag * height, 0, 0, 0, 0))
        _add(pose, neck, (0, 0, 0, 0, -bend * 0.8 * c, 0))
        _add(pose, head, (0, 0, 0, 0.02 * math.sin(TAU * u * 2), -bend * 0.3 * c, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0, tailwave * math.cos(TAU * u - (i + 1) * 0.85) * (0.6 + 0.12 * i), 0))
        return pose

    def idle(t):
        u = t / 5.0
        pose = {}
        br = math.sin(TAU * u * 2)
        _add(pose, "Body", (0, 0.012 * height * br, 0, 0.01 * br, 0, 0))
        _add(pose, neck, (0, 0, 0, 0.03 * math.sin(TAU * u), 0.12 * math.sin(TAU * u + 0.5), 0))
        look = math.sin(TAU * u) * (0.7 + 0.3 * math.sin(TAU * u * 3))
        _add(pose, head, (0, 0, 0, 0.05 * max(0.0, math.sin(TAU * u * 2 + 1)), 0.18 * look, 0.04 * math.sin(TAU * u + 2)))
        if jaw:
            gape = max(0.0, math.sin(TAU * u)) ** 6
            _add(pose, jaw, (0, 0, 0, -0.35 * gape, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.02 * math.sin(TAU * u * 2 - i), 0.08 * math.sin(TAU * u * 2 - i * 0.7), 0))
        for (b, side) in frill:  # the frill flutters
            _add(pose, b, (0, 0, 0, 0, side * 0.06 * math.sin(TAU * u * 4), 0))
        if extra_idle:
            extra_idle(pose, u)
        return pose

    def atk(t):
        L = alen
        s = t / L
        pose = {}
        if attack == "roll":
            lunge = _win(s, 0.0, 0.42)
            gape = _win(s, 0.0, 0.26)
            roll = _ramp(s, 0.3, 0.8)
            _add(pose, "Body", (0, 0.1 * height * _win(s, 0.25, 0.85), -0.5 * height * lunge, 0.08 * lunge, 0, TAU * roll))
            _add(pose, jaw, (0, 0, 0, -0.9 * gape, 0, 0))
            _add(pose, head, (0, 0, 0, 0.2 * gape, 0, 0))
            for up, lo, ft, ph, side, fr in legs:
                k = _win(s, 0.25, 0.85)
                _add(pose, up, (0, 0, 0, 0, 0, -side * 0.5 * k))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0, 0.25 * math.sin(TAU * s * 2 - i * 0.8) * (1 - s), 0.1 * _win(s, 0.25, 0.85)))
        elif attack == "tongue":
            ext = _win(s, 0.15, 0.75) ** 0.6
            _add(pose, "Body", (0, 0, -0.05 * height * ext, -0.04 * ext, 0, 0))
            _add(pose, head, (0, 0, 0, 0.06 * ext, 0, 0))
            _add(pose, jaw, (0, 0, 0, -0.5 * _win(s, 0.08, 0.85), 0, 0))
            if tongue:
                for bone, dist, axis in _tlist(tongue):
                    _add(pose, bone, tuple(-dist * ext * a for a in axis))
        elif attack == "tailwhip":
            sw = math.sin(math.pi * min(s / 0.8, 1))
            _add(pose, "Body", (0, 0, 0, 0, 0.5 * sw, 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0, -0.35 * math.sin(math.pi * min(max((s - 0.05 * i) / 0.7, 0), 1)), 0))
            _add(pose, jaw, (0, 0, 0, -0.3 * sw, 0, 0))
        else:  # snap / frill: rear up the head, gape, lunge and snap
            wind = _win(s, 0.0, 0.4)
            strike = _win(s, 0.3, 0.75)
            _add(pose, "Body", (0, 0.04 * height * wind, -0.45 * height * strike, 0.1 * wind - 0.05 * strike, 0, 0))
            _add(pose, front, (0, 0, 0, 0.12 * wind, 0, 0))
            _add(pose, neck, (0, 0, 0, 0.25 * wind - 0.2 * strike, 0, 0))
            _add(pose, head, (0, 0, 0, 0.15 * wind - 0.1 * strike, 0, 0))
            g = _win(s, 0.05, 0.62)
            _add(pose, jaw, (0, 0, 0, -0.8 * g, 0, 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0, 0.25 * math.sin(TAU * s * 1.5 - i), 0))
        if attack == "frill" and frill:
            op = _win(s, 0.0, 1.0) ** 0.4
            for (b, side) in frill:
                _add(pose, b, (0, 0, 0, 0, side * -0.9 * op, side * 0.15 * op))
        return pose

    alen = 1.5 if attack == "roll" else 0.9
    H.clip("Move", walk, move, keys=20)
    H.clip("Idle", 5.0, idle, keys=24)
    H.clip("Attack", alen, atk, keys=24 if attack == "roll" else 16, loop=False)
    hit_clip(H, height, head=head, neck=neck, jaw=jaw, tail=tail)
    H.rig.update({"legsAuthored": True, "height": height})


# ================================================================================================ slither
def slither(H, chain, fore=(), head=None, jaw=None, tongue=None, amp=0.32, waves=1.2, walk=1.2, height=1.0, raised=False,
            rattle=None, hood=(), swim=False):
    """chain: body bones from the Body root backwards to the tail tip (each child of the previous).
    fore: bones from Body forwards to the neck (each child of the previous), the head bone is the child of the last.
    Lateral undulation: the absolute heading along the body is theta(s) = A cos(wt - k s); each bone gets the relative
    yaw theta_i - theta_{i-1}. Raised (cobra): the fore chain keeps its rest pose (modelled raised) and only sways."""
    n = len(chain)
    m = len(fore)
    k = TAU * waves / max(n + m, 1)

    def heading(u, i):  # i: position index from the head end (0 = head)
        env = min(1.0, 0.35 + i * 0.22)
        return amp * env * math.cos(TAU * u - k * i)

    def move(t):
        u = t / walk
        pose = {}
        # the Body sits at index m from the head
        th_body = heading(u, m) if not raised else 0.0
        _add(pose, "Body", (0, 0, 0, 0, th_body, 0))
        prev = th_body
        for j, b in enumerate(chain):
            th = heading(u, m + 1 + j)
            _add(pose, b, (0, 0, 0, 0, th - prev, 0))
            prev = th
        prev = th_body
        for j, b in enumerate(fore):
            idx = m - 1 - j
            th = heading(u, idx) * (0.35 if raised else 0.5)
            _add(pose, b, (0, 0, 0, 0, th - prev, 0))
            prev = th
        if raised:
            for j, b in enumerate(fore):
                _add(pose, b, (0, 0, 0, 0.03 * math.sin(TAU * u * 2 + j), 0.06 * math.sin(TAU * u + j * 0.5), 0))
        _add(pose, head, (0, 0, 0, 0.02 * math.sin(TAU * u * 2), -prev * 0.8, 0))
        if rattle:
            _add(pose, rattle, (0, 0, 0, 0.3 * math.sin(TAU * u * 8), 0, 0.2 * math.sin(TAU * u * 8)))
        if swim:
            _add(pose, "Body", (0, 0.03 * height * math.sin(TAU * u), 0, 0, 0, 0))
        return pose

    def idle(t):
        u = t / 5.0
        pose = {}
        for j, b in enumerate(chain):
            _add(pose, b, (0, 0, 0, 0, 0.05 * math.sin(TAU * u - j * 0.6), 0))
        for j, b in enumerate(fore):
            _add(pose, b, (0, 0, 0, 0.03 * math.sin(TAU * u * 2 + j * 0.4), 0.07 * math.sin(TAU * u + j * 0.5), 0))
        _add(pose, head, (0, 0, 0, 0.04 * math.sin(TAU * u * 2 + 1), 0.15 * math.sin(TAU * u), 0))
        if tongue:
            fl = max(0.0, math.sin(TAU * u * 3)) ** 8
            for bone, dist, axis in _tlist(tongue):
                _add(pose, bone, tuple(-dist * fl * a for a in axis) + (0.25 * fl * math.sin(TAU * u * 40), 0, 0))
        if rattle:
            _add(pose, rattle, (0, 0, 0, 0.35 * math.sin(TAU * u * 28), 0, 0.25 * math.sin(TAU * u * 28 + 1)))
        if swim:
            _add(pose, "Body", (0, 0.03 * height * math.sin(TAU * u * 2), 0, 0, 0, 0))
        return pose

    def atk(t):
        s = t / 0.9
        pose = {}
        coil = _win(s, 0.0, 0.42)
        strike = _win(s, 0.32, 0.72)
        # coil back into an S then lunge
        for j, b in enumerate(fore):
            sgn = 1 if j % 2 == 0 else -1
            _add(pose, b, (0, 0, 0, (0.28 if not raised else 0.12) * coil - 0.3 * strike * (0.6 if raised else 1.0), sgn * 0.25 * coil, 0))
        for j, b in enumerate(chain[:4]):
            _add(pose, b, (0, 0, 0, 0, (1 if j % 2 else -1) * 0.3 * coil, 0))
        _add(pose, "Body", (0, 0, -0.6 * height * strike + 0.15 * height * coil, 0, 0, 0))
        _add(pose, head, (0, 0, 0, 0.2 * coil - 0.2 * strike, 0, 0))
        _add(pose, jaw, (0, 0, 0, -1.1 * _win(s, 0.25, 0.75), 0, 0))
        for i, b in enumerate(hood):
            _add(pose, b, (0, 0, 0, 0, 0, 0))
        if rattle:
            _add(pose, rattle, (0, 0, 0, 0.35 * math.sin(TAU * s * 12), 0, 0))
        return pose

    H.clip("Move", walk, move, keys=24)
    H.clip("Idle", 5.0, idle, keys=30)
    H.clip("Attack", 0.9, atk, keys=16, loop=False)

    def hit(t):
        s = t / 0.4
        kk = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0, 0.1 * height * kk, 0, 0, 0))
        for j, b in enumerate(fore):
            _add(pose, b, (0, 0, 0, 0.15 * kk, 0.1 * kk, 0))
        for j, b in enumerate(chain):
            _add(pose, b, (0, 0, 0, 0, 0.12 * kk * (1 if j % 2 else -1), 0))
        _add(pose, head, (0, 0, 0, 0.2 * kk, 0, 0))
        _add(pose, jaw, (0, 0, 0, -0.4 * kk, 0, 0))
        return pose

    H.clip("Hit", 0.4, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})


# ================================================================================================ hop (frogs)
def hop(H, hind, fore, head=None, jaw=None, tongue=None, walk=0.9, height=1.0, jump=1.0):
    """hind: (thigh, shin, foot, side) bones; fore: (upper, fore, hand, side). One hop per cycle."""

    def pose_at(s, pose, amp=1.0):
        # s: 0 crouch, 0.15-0.35 push off, 0.35-0.75 airborne, 0.75-0.9 land, 0.9-1 settle
        push = _win(s, 0.12, 0.55)
        air = _win(s, 0.3, 0.85)
        land = _win(s, 0.72, 1.0)
        y = height * jump * (0.3 * push + 0.42 * math.sin(math.pi * min(max((s - 0.22) / 0.6, 0), 1)) ** 1.2)
        _add(pose, "Body", (0, y * amp, 0, (-0.35 * push + 0.15 * land + 0.08 * air) * amp, 0, 0))
        for th, sh, ft, side in hind:
            _add(pose, th, (0, 0, 0, -1.0 * push * amp, 0, 0))
            _add(pose, sh, (0, 0, 0, 0.9 * push * amp, 0, 0))
            _add(pose, ft, (0, 0, 0, -0.9 * push * amp + 0.25 * land * amp, 0, 0))
        for up, fo, hd, side in fore:
            _add(pose, up, (0, 0, 0, (0.7 * air - 0.2 * push) * amp, 0, 0))
            _add(pose, fo, (0, 0, 0, (-0.3 * air) * amp, 0, 0))
            _add(pose, hd, (0, 0, 0, (0.3 * air) * amp, 0, 0))
        _add(pose, head, (0, 0, 0, (0.2 * push - 0.1 * land) * amp, 0, 0))

    def move(t):
        pose = {}
        pose_at((t / walk) % 1.0, pose)
        return pose

    def idle(t):
        u = t / 4.0
        pose = {}
        th = math.sin(TAU * u * 4)
        _add(pose, "Body", (0, 0.01 * height * th, 0, 0.02 * th, 0, 0))
        if jaw:  # throat pulse
            _add(pose, jaw, (0, -0.012 * height * max(0.0, math.sin(TAU * u * 6)), 0, 0, 0, 0))
        _add(pose, head, (0, 0, 0, 0, 0.1 * math.sin(TAU * u), 0))
        return pose

    def atk(t):
        s = t / 0.8
        pose = {}
        ext = _win(s, 0.15, 0.7) ** 0.5
        _add(pose, "Body", (0, 0.02 * height * ext, -0.05 * height * ext, 0.12 * ext, 0, 0))
        _add(pose, jaw, (0, 0, 0, -0.6 * _win(s, 0.1, 0.78), 0, 0))
        if tongue:
            for bone, dist, axis in _tlist(tongue):
                _add(pose, bone, tuple(-dist * ext * a for a in axis) + (-0.12 * ext, 0, 0))
        for up, fo, hd, side in fore:
            _add(pose, up, (0, 0, 0, -0.15 * ext, 0, 0))
        return pose

    H.clip("Move", walk, move, keys=20)
    H.clip("Idle", 4.0, idle, keys=24)
    H.clip("Attack", 0.8, atk, keys=14, loop=False)
    hit_clip(H, height, head=head, jaw=jaw)
    H.rig.update({"legsAuthored": True, "height": height})


# ================================================================================================ flipper swim
def flipper(H, fl_front, fl_back=(), head=None, neck=(), jaw=None, tail=(), walk=1.6, height=1.0, attack="bite",
            fl_amp=0.75, body_wave=0.0, spine=()):
    """fl_front / fl_back: (bone, tipbone_or_None, side). Down-stroke = rz on the flipper (right side: -rz pushes the tip
    down); a pitch twist (rx) follows the stroke. neck: list of neck bones (plesiosaurs)."""

    def flaps(pose, u, amp=1.0):
        for b, tip, side in fl_front:
            st = math.sin(TAU * u)
            _add(pose, b, (0, 0, 0, 0.35 * math.cos(TAU * u) * amp, side * 0.25 * math.cos(TAU * u) * amp, side * fl_amp * st * amp))
            _add(pose, tip, (0, 0, 0, 0, 0, side * 0.35 * math.sin(TAU * u - 0.9) * amp))
        for b, tip, side in fl_back:
            st = math.sin(TAU * u + math.pi * 0.7)
            _add(pose, b, (0, 0, 0, 0.25 * math.cos(TAU * u + 2.2) * amp, 0, side * fl_amp * 0.55 * st * amp))
            _add(pose, tip, (0, 0, 0, 0, 0, side * 0.25 * math.sin(TAU * u + 1.3) * amp))

    def move(t):
        u = t / walk
        pose = {}
        flaps(pose, u)
        _add(pose, "Body", (0, 0.05 * height * math.sin(TAU * u - 0.6), 0, 0.04 * math.sin(TAU * u), 0, 0))
        for i, b in enumerate(neck):
            _add(pose, b, (0, 0, 0, -0.03 * math.sin(TAU * u - 0.6 - i * 0.4), 0.06 * math.sin(TAU * u * 0.5 - i * 0.5), 0))
        _add(pose, head, (0, 0, 0, -0.03 * math.sin(TAU * u - 1), 0, 0))
        for i, b in enumerate(spine):
            _add(pose, b, (0, 0, 0, 0, body_wave * math.sin(TAU * u - i * 0.8), 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0, (0.15 + body_wave) * math.sin(TAU * u - (i + 1) * 0.8), 0))
        return pose

    def idle(t):
        u = t / 4.0
        pose = {}
        flaps(pose, u * 2, 0.3)
        _add(pose, "Body", (0, 0.04 * height * math.sin(TAU * u), 0, 0.02 * math.sin(TAU * u), 0, 0))
        for i, b in enumerate(neck):
            _add(pose, b, (0, 0, 0, 0.03 * math.sin(TAU * u - i * 0.5), 0.1 * math.sin(TAU * u * 0.5 - i * 0.4), 0))
        _add(pose, head, (0, 0, 0, 0.03 * math.sin(TAU * u * 2), 0.12 * math.sin(TAU * u), 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0, 0.08 * math.sin(TAU * u * 2 - i), 0))
        return pose

    def atk(t):
        s = t / 0.9
        pose = {}
        wind = _win(s, 0.0, 0.4)
        strike = _win(s, 0.3, 0.75)
        flaps(pose, s * 1.5, 0.6)
        _add(pose, "Body", (0, 0, -0.5 * height * strike, 0.08 * wind - 0.08 * strike, 0, 0))
        for i, b in enumerate(neck):
            _add(pose, b, (0, 0, 0, 0.15 * wind - 0.18 * strike, 0, 0))
        _add(pose, head, (0, 0, 0, 0.15 * wind - 0.1 * strike, 0, 0))
        _add(pose, jaw, (0, 0, 0, -0.8 * _win(s, 0.1, 0.65), 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0, 0.3 * math.sin(TAU * s * 2 - i), 0))
        return pose

    H.clip("Move", walk, move, keys=20)
    H.clip("Idle", 4.0, idle, keys=20)
    H.clip("Attack", 0.9, atk, keys=14, loop=False)
    hit_clip(H, height, head=head, neck=neck[-1] if neck else None, jaw=jaw, tail=tail)
    H.rig.update({"legsAuthored": True, "height": height})


# ================================================================================================ tail-driven swim
def swimtail(H, spine, tail, head=None, jaw=None, limbs=(), walk=1.4, height=1.0, amp=0.18, gills=()):
    """Anguilliform / carangiform swim: a yaw wave growing toward the tail. limbs: (bone, side) paddles held back."""

    def move(t):
        u = t / walk
        pose = {}
        chain = list(spine) + list(tail)
        for i, b in enumerate(chain):
            env = 0.25 + 0.75 * i / max(len(chain) - 1, 1)
            _add(pose, b, (0, 0, 0, 0, amp * env * math.sin(TAU * u - i * 0.7), 0))
        _add(pose, "Body", (0, 0.03 * height * math.sin(TAU * u * 2), 0, 0, -amp * 0.35 * math.sin(TAU * u + 0.6), 0))
        _add(pose, head, (0, 0, 0, 0, amp * 0.25 * math.sin(TAU * u + 0.6), 0))
        for b, side in limbs:
            _add(pose, b, (0, 0, 0, -0.4 + 0.15 * math.sin(TAU * u + side), 0, side * 0.12 * math.sin(TAU * u)))
        for b, side in gills:
            _add(pose, b, (0, 0, 0, 0.1 * math.sin(TAU * u * 2), 0, side * 0.08 * math.sin(TAU * u * 2)))
        return pose

    def idle(t):
        u = t / 4.0
        pose = {}
        for i, b in enumerate(list(spine) + list(tail)):
            _add(pose, b, (0, 0, 0, 0, 0.05 * math.sin(TAU * u - i * 0.6), 0))
        _add(pose, "Body", (0, 0.03 * height * math.sin(TAU * u), 0, 0.02 * math.sin(TAU * u), 0, 0))
        _add(pose, head, (0, 0, 0, 0.03 * math.sin(TAU * u * 2), 0.1 * math.sin(TAU * u), 0))
        for b, side in limbs:
            _add(pose, b, (0, 0, 0, 0.12 * math.sin(TAU * u * 2 + side), 0, side * 0.1 * math.sin(TAU * u * 2)))
        for b, side in gills:
            _add(pose, b, (0, 0, 0, 0.15 * math.sin(TAU * u * 3), 0, side * 0.12 * math.sin(TAU * u * 3)))
        _add(pose, jaw, (0, 0, 0, -0.08 * max(0.0, math.sin(TAU * u)) ** 4, 0, 0))
        return pose

    def atk(t):
        s = t / 0.8
        pose = {}
        strike = _win(s, 0.2, 0.7)
        _add(pose, "Body", (0, 0, -0.6 * height * strike, -0.05 * strike, 0, 0))
        _add(pose, head, (0, 0, 0, 0.2 * _win(s, 0.0, 0.4) - 0.1 * strike, 0, 0))
        _add(pose, jaw, (0, 0, 0, -0.85 * _win(s, 0.05, 0.62), 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0, 0.35 * math.sin(TAU * s * 2 - i * 0.7), 0))
        return pose

    H.clip("Move", walk, move, keys=20)
    H.clip("Idle", 4.0, idle, keys=20)
    H.clip("Attack", 0.8, atk, keys=14, loop=False)
    hit_clip(H, height, head=head, jaw=jaw, tail=tail)
    H.rig.update({"legsAuthored": True, "height": height})


# ================================================================================================ flying (pterosaurs)
def fly(H, wings, head=None, neck=None, jaw=None, legs=(), walk=1.2, height=1.0, flap=0.75):
    """wings: (arm, hand, side): arm = inner wing (shoulder), hand = outer wing (wrist, lags behind)."""

    def wing_pose(pose, u, amp=1.0, glide=0.0):
        for arm, hand, side in wings:
            a = math.sin(TAU * u)
            b = math.sin(TAU * u - 1.0)
            _add(pose, arm, (0, 0, 0, 0.12 * math.cos(TAU * u) * amp, 0, side * (flap * a * amp + 0.1 * glide)))
            _add(pose, hand, (0, 0, 0, 0, side * 0.08 * a * amp, side * (0.3 * b * amp - 0.05 * glide)))

    def move(t):
        u = t / walk
        pose = {}
        wing_pose(pose, u)
        _add(pose, "Body", (0, -0.12 * height * math.sin(TAU * u), 0, 0.04 * math.sin(TAU * u + 0.5), 0, 0))
        _add(pose, neck, (0, 0, 0, 0.05 * math.sin(TAU * u + 1.2), 0, 0))
        _add(pose, head, (0, 0, 0, -0.05 * math.sin(TAU * u + 1.4), 0, 0))
        for b, side in legs:
            _add(pose, b, (0, 0, 0, -0.9, 0, 0))
        return pose

    def idle(t):  # hovering glide with slow beats
        u = t / 2.4
        pose = {}
        wing_pose(pose, u, 0.55, glide=1.0)
        _add(pose, "Body", (0, -0.08 * height * math.sin(TAU * u), 0, 0.03 * math.sin(TAU * u), 0, 0.03 * math.sin(TAU * u * 0.5)))
        _add(pose, head, (0, 0, 0, 0.04 * math.sin(TAU * u * 2), 0.18 * math.sin(TAU * u * 0.5), 0))
        for b, side in legs:
            _add(pose, b, (0, 0, 0, -0.9, 0, 0))
        return pose

    def atk(t):
        s = t / 1.0
        pose = {}
        dive = _win(s, 0.1, 0.8)
        wing_pose(pose, 0.25, 0.9 * _win(s, 0.0, 0.3))
        for arm, hand, side in wings:
            _add(pose, arm, (0, 0, 0, 0, side * 0.35 * dive, side * -0.4 * dive))
        _add(pose, "Body", (0, -0.6 * height * dive, -0.8 * height * dive, -0.35 * dive, 0, 0))
        _add(pose, neck, (0, 0, 0, 0.2 * _win(s, 0.0, 0.4) - 0.3 * _win(s, 0.45, 0.8), 0, 0))
        _add(pose, jaw, (0, 0, 0, -0.6 * _win(s, 0.3, 0.75), 0, 0))
        for b, side in legs:
            _add(pose, b, (0, 0, 0, -0.9 + 0.9 * dive, 0, 0))
        return pose

    H.clip("Move", walk, move, keys=20)
    H.clip("Idle", 2.4, idle, keys=20)
    H.clip("Attack", 1.0, atk, keys=16, loop=False)
    hit_clip(H, height, head=head, neck=neck, jaw=jaw)
    H.rig.update({"legsAuthored": True, "height": height})


# ================================================================================================ theropod
def theropod(H, legs, arms=(), neck=None, head=None, jaw=None, tail=(), hips=None, chest=None, stride=0.45, walk=1.1,
             height=5.0, attack="bite", heavy=1.0):
    """legs: (hip, knee, ankle, toe, phase). Digitigrade: thigh swings, the knee folds forward(-), the ankle back(+).
    arms: (shoulder, elbow, side). heavy (0..1+) adds weight: deeper bob and a slower swaggering trunk roll."""

    def legpose(pose, u, amp=1.0):
        for hip, knee, ank, toe, ph in legs:
            w = (u + ph) % 1.0
            duty = 0.58
            if w < duty:
                s = w / duty
                sw = stride * (1 - 2 * s)
                fold = 0.0
            else:
                s = (w - duty) / (1 - duty)
                sw = stride * (-1 + 2 * _ease(s))
                fold = math.sin(math.pi * s)
            _add(pose, hip, (0, 0, 0, (sw + 0.25 * fold) * amp, 0, 0))
            _add(pose, knee, (0, 0, 0, (-0.75 * fold - 0.08) * amp, 0, 0))
            _add(pose, ank, (0, 0, 0, (0.7 * fold + 0.06 - 0.25 * max(0.0, -sw)) * amp, 0, 0))
            _add(pose, toe, (0, 0, 0, (-0.6 * fold + 0.35 * max(0.0, -sw / max(stride, 1e-3)) * (1 - fold)) * amp, 0, 0))

    def move(t):
        u = t / walk
        pose = {}
        legpose(pose, u)
        bob = abs(math.sin(TAU * u))
        _add(pose, "Body", (0, (0.025 + 0.02 * heavy) * height * (bob - 0.5), 0, 0.02 * math.sin(TAU * u * 2), 0.05 * math.sin(TAU * u), (0.03 + 0.03 * heavy) * math.sin(TAU * u)))
        _add(pose, hips, (0, 0, 0, 0, -0.04 * math.sin(TAU * u), 0))
        _add(pose, chest, (0, 0, 0, 0, -0.04 * math.sin(TAU * u), 0))
        _add(pose, neck, (0, 0, 0, -0.06 * math.sin(TAU * u * 2 + 0.7), -0.06 * math.sin(TAU * u), 0))
        _add(pose, head, (0, 0, 0, 0.05 * math.sin(TAU * u * 2 + 1.1), 0.03 * math.sin(TAU * u), 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.03 * math.sin(TAU * u * 2 - i * 0.6), -0.12 * math.sin(TAU * u - 0.5 - i * 0.6), 0))
        for sh, el, side in arms:
            _add(pose, sh, (0, 0, 0, 0.12 * math.sin(TAU * u * 2 + side), 0, 0))
        return pose

    def idle(t):
        u = t / 5.0
        pose = {}
        br = math.sin(TAU * u * 2)
        _add(pose, "Body", (0, 0.006 * height * br, 0, 0.012 * br, 0.03 * math.sin(TAU * u), 0))
        _add(pose, neck, (0, 0, 0, 0.04 * math.sin(TAU * u + 0.3), 0.1 * math.sin(TAU * u + 0.6), 0))
        look = math.sin(TAU * u) * (0.6 + 0.4 * math.sin(TAU * u * 3))
        _add(pose, head, (0, 0, 0, 0.05 * math.sin(TAU * u * 2 + 1), 0.22 * look, 0.06 * math.sin(TAU * u + 2)))
        _add(pose, jaw, (0, 0, 0, -0.12 * max(0.0, math.sin(TAU * u * 1 + 2)) ** 6, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.02 * math.sin(TAU * u * 2 - i), 0.08 * math.sin(TAU * u * 2 - i * 0.7), 0))
        for hip, knee, ank, toe, ph in legs:
            _add(pose, knee, (0, 0, 0, -0.05 - 0.02 * br, 0, 0))
            _add(pose, ank, (0, 0, 0, 0.05 + 0.02 * br, 0, 0))
        for sh, el, side in arms:
            _add(pose, sh, (0, 0, 0, 0.06 * br, 0, 0))
            _add(pose, el, (0, 0, 0, 0.08 * math.sin(TAU * u * 3 + side), 0, 0))
        return pose

    def atk(t):
        s = t / 0.95
        pose = {}
        wind = _win(s, 0.0, 0.42)
        strike = _win(s, 0.32, 0.78)
        if attack == "headbutt":
            _add(pose, "Body", (0, -0.03 * height * strike, -0.25 * height * strike + 0.06 * height * wind, -0.15 * strike + 0.08 * wind, 0, 0))
            _add(pose, neck, (0, 0, 0, 0.3 * wind - 0.5 * strike, 0, 0))
            _add(pose, head, (0, 0, 0, 0.2 * wind - 0.55 * strike, 0, 0))
        elif attack == "slash":
            _add(pose, "Body", (0, 0.12 * height * strike, -0.3 * height * strike, 0.35 * strike - 0.08 * wind, 0, 0))
            for hip, knee, ank, toe, ph in legs[:1]:
                _add(pose, hip, (0, 0, 0, 1.1 * strike, 0, 0))
                _add(pose, knee, (0, 0, 0, -0.9 * strike, 0, 0))
                _add(pose, toe, (0, 0, 0, -0.8 * strike, 0, 0))
            for sh, el, side in arms:
                _add(pose, sh, (0, 0, 0, 0.9 * strike - 0.3 * wind, 0, 0))
            _add(pose, jaw, (0, 0, 0, -0.6 * strike, 0, 0))
            _add(pose, neck, (0, 0, 0, -0.2 * strike, 0, 0))
        else:  # bite: rear back, gape, lunge and snap
            _add(pose, "Body", (0, 0.02 * height * wind, -0.22 * height * strike, 0.1 * wind - 0.12 * strike, 0, 0))
            _add(pose, neck, (0, 0, 0, 0.3 * wind - 0.3 * strike, 0, 0))
            _add(pose, head, (0, 0, 0, 0.2 * wind - 0.15 * strike, 0.08 * strike, 0))
            _add(pose, jaw, (0, 0, 0, -0.75 * _win(s, 0.1, 0.66), 0, 0))
            for hip, knee, ank, toe, ph in legs:
                _add(pose, knee, (0, 0, 0, -0.2 * wind, 0, 0))
                _add(pose, ank, (0, 0, 0, 0.2 * wind, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.1 * wind - 0.08 * strike, 0.15 * math.sin(TAU * s - i * 0.7), 0))
        return pose

    H.clip("Move", walk, move, keys=20)
    H.clip("Idle", 5.0, idle, keys=24)
    H.clip("Attack", 0.95, atk, keys=16, loop=False)
    hit_clip(H, height, head=head, neck=neck, jaw=jaw, tail=tail, roll=0.04)
    H.rig.update({"legsAuthored": True, "height": height})
