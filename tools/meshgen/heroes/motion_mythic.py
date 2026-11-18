"""Authored motion for dragons and mythic beasts: winged flyers (flap cycle with a fast downstroke, lagging hands,
tucked legs, body bob), rear-and-breathe attacks, serpent chains (travelling waves for flying / swimming lung
dragons and sea serpents), multi-necked beasts, and an overlay helper to add wing tracks to the motion.py cycles.

Pose values are (px, py, pz, rx, ry, rz) at a bone pivot in its parent's frame (see motion.py). For a right wing
(+X), +rz raises the tip; side = +1 right, -1 left.
"""
import math

TAU = 2 * math.pi


def _add(pose, bone, v):
    if bone is None:
        return
    o = list(pose.get(bone, (0.0,) * 6))
    for i, x in enumerate(v):
        o[i] += x
    pose[bone] = tuple(o)


def ease(x):
    return 0.5 - 0.5 * math.cos(math.pi * min(max(x, 0.0), 1.0))


def window(s, a, b, c, d):
    """0 before a, eases to 1 over a..b, holds to c, eases back to 0 over c..d."""
    if s < a:
        return 0.0
    if s < b:
        return ease((s - a) / max(b - a, 1e-6))
    if s < c:
        return 1.0
    if s < d:
        return 1.0 - ease((s - c) / max(d - c, 1e-6))
    return 0.0


def overlay(H, name, fn):
    """Add fn(t) -> pose to an existing clip at its own key times (e.g. wing flutter on top of motion.quadruped)."""
    c = H.clips[name]
    n, L = c["keys"], c["len"]
    times = [L * i / n for i in range(n)] if c["loop"] else [L * i / (n - 1) for i in range(n)]
    for i, t in enumerate(times):
        for b, v in fn(t).items():
            tr = c["tracks"].setdefault(b, [(0.0,) * 6 for _ in range(n)])
            v = tuple(float(x) for x in v) + (0.0,) * (6 - len(v))
            tr[i] = tuple(a + x for a, x in zip(tr[i], v))


def wing_flap(pose, wings, w, amp=1.0, base=0.12, sweep=0.12, fold=0.28):
    """One flap at phase w (0 = top of the upstroke). wings: (arm, hand, side)."""
    ang = math.cos(TAU * w)
    for arm, hand, side in wings:
        _add(pose, arm, (0, 0, 0, 0.04 * math.sin(TAU * w), side * sweep * math.sin(TAU * w), side * (base + 0.62 * amp * ang)))
        if hand:
            _add(pose, hand, (0, 0, 0, 0, side * 0.1 * math.sin(TAU * (w - 0.1)),
                              side * (0.32 * amp * math.cos(TAU * (w - 0.13)) - fold * amp * max(0.0, -math.sin(TAU * w)))))


def flyer(H, legs=(), wings=(), neck=(), head=None, jaw=None, tail=(), height=4.0, hipz=1.5, flap=1.0, lift=0.22, period=1.1,
          attack="breathe", tuck=1.0, idle_wing=1.0, keys=24):
    """Clips for a winged creature that flies when it moves.
    legs: (upper, lower, foot, front, side); wings: (arm, hand, side); neck: bones base -> head."""

    def move(t):
        u = t / period
        w = u + 0.08 * math.sin(TAU * u)            # fast downstroke, slower recovery
        pose = {}
        wing_flap(pose, wings, w, flap)
        bob = -math.cos(TAU * w)
        _add(pose, "Body", (0, lift * height + 0.035 * height * bob, 0, 0.03 * math.sin(TAU * w + 0.6) - 0.04, 0, 0.015 * math.sin(TAU * u * 0.5)))
        for up, lo, ft, front, side in legs:
            d = 0.06 * math.sin(TAU * (u - 0.2))
            if front:
                _add(pose, up, (0, 0, 0, (-0.45 + d) * tuck, 0, 0))
                _add(pose, lo, (0, 0, 0, 1.0 * tuck, 0, 0))
                _add(pose, ft, (0, 0, 0, 0.45 * tuck, 0, 0))
            else:
                _add(pose, up, (0, 0, 0, (-1.0 + d) * tuck, 0, 0))
                _add(pose, lo, (0, 0, 0, 0.2 * tuck, 0, 0))
                _add(pose, ft, (0, 0, 0, -0.9 * tuck, 0, 0))
        n = max(len(neck), 1)
        for i, b in enumerate(neck):
            _add(pose, b, (0, 0, 0, 0.05 * math.sin(TAU * w + 1.2 + i * 0.6) + 0.06 / n, 0.03 * math.sin(TAU * u * 0.5 + i), 0))
        _add(pose, head, (0, 0, 0, -0.05 * math.sin(TAU * w + 1.8) - 0.06, 0, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.06 - 0.04 * math.sin(TAU * u), 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.07 * math.sin(TAU * w - 1.0 - i * 0.7) + 0.03, 0.1 * math.sin(TAU * u * 0.5 * 2 - i * 0.9), 0))
        return pose

    def idle(t):
        u = t / 5.0
        pose = {}
        br = math.sin(TAU * u * 2)
        _add(pose, "Body", (0, 0.008 * height * br, 0, 0.01 * br, 0, 0))
        for arm, hand, side in wings:
            m = math.sin(TAU * u * 2 + 0.4)
            _add(pose, arm, (0, 0, 0, 0, side * 0.04 * m * idle_wing, side * (0.05 * m + 0.03 * math.sin(TAU * u * 5)) * idle_wing))
            if hand:
                _add(pose, hand, (0, 0, 0, 0, 0, side * 0.06 * math.sin(TAU * u * 2 - 0.4) * idle_wing))
        for i, b in enumerate(neck):
            _add(pose, b, (0, 0, 0, 0.035 * math.sin(TAU * u * 2 - i * 0.7), 0.07 * math.sin(TAU * u + 0.5 - i * 0.4), 0))
        _add(pose, head, (0, 0, 0, 0.05 * math.sin(TAU * u * 2 + 1), 0.25 * math.sin(TAU * u) * (0.6 + 0.4 * math.sin(TAU * u * 3)), 0.04 * math.sin(TAU * u + 2)))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.12 * max(0.0, math.sin(TAU * u * 2 - 1.0)) ** 6, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.025 * math.sin(TAU * u * 2 - i), 0.13 * math.sin(TAU * u * 2 - i * 0.8), 0))
        return pose

    L = 1.4

    def atk(t):
        s = t / L
        pose = {}
        rear = window(s, 0.0, 0.3, 0.72, 1.0)
        wind = window(s, 0.0, 0.28, 0.32, 0.45)
        fire = window(s, 0.34, 0.45, 0.72, 0.92)
        th = 0.36 * rear
        _add(pose, "Body", (0, hipz * math.sin(th) + 0.04 * height * rear, 0.05 * height * fire, th, 0, 0))
        for up, lo, ft, front, side in legs:
            if front:
                _add(pose, up, (0, 0, 0, 0.75 * rear - th, 0, -side * 0.12 * rear))
                _add(pose, lo, (0, 0, 0, -0.95 * rear, 0, 0))
                _add(pose, ft, (0, 0, 0, 0.6 * rear, 0, 0))
            else:
                _add(pose, up, (0, 0, 0, -th + 0.1 * rear, 0, 0))
                _add(pose, lo, (0, 0, 0, -0.1 * rear, 0, 0))
                _add(pose, ft, (0, 0, 0, 0.05 * rear, 0, 0))
        beat = math.sin(math.pi * min(max((s - 0.35) / 0.4, 0), 1))
        for arm, hand, side in wings:
            _add(pose, arm, (0, 0, 0, 0, side * 0.15 * rear, side * (0.38 * rear - 0.55 * beat)))
            if hand:
                _add(pose, hand, (0, 0, 0, 0, 0, side * (0.2 * rear - 0.25 * beat)))
        n = max(len(neck), 1)
        for b in neck:
            _add(pose, b, (0, 0, 0, (0.3 * wind - 0.32 * fire - th * 0.7) / n * 2.0, 0, 0))
        _add(pose, head, (0, 0, 0, 0.15 * wind - 0.22 * fire, 0, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.18 * wind - 0.62 * fire, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.1 * rear - 0.05 * i * rear, 0.25 * math.sin(TAU * s * 1.5 - i * 0.8) * rear, 0))
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, -0.02 * height * k, 0.07 * height * k, 0.1 * k, 0, 0.06 * math.sin(t * 38) * k))
        for b in neck:
            _add(pose, b, (0, 0, 0, 0.12 * k, 0.05 * k, 0))
        _add(pose, head, (0, 0, 0, 0.18 * k, 0.12 * k, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.35 * k, 0, 0))
        for arm, hand, side in wings:
            _add(pose, arm, (0, 0, 0, 0, 0, side * 0.3 * k))
            if hand:
                _add(pose, hand, (0, 0, 0, 0, 0, -side * 0.2 * k))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, -0.1 * k, 0.15 * k * (1 if i % 2 else -1), 0))
        return pose

    H.clip("Move", period, move, keys=keys)
    H.clip("Idle", 5.0, idle, keys=24)
    H.clip("Attack", L, atk, keys=18, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})
    if wings:
        H.rig["wings"] = [{"bone": a, "side": s} for a, h, s in wings]


def serpent(H, chain, head=None, jaw=None, height=3.0, mode="fly", amp=0.16, lat=0.08, period=1.6, legs=(), lift=0.0, waves=1.0,
            fins=(), whiskers=(), attack="lunge", neck=()):
    """Travelling-wave clips for a serpent body. chain: bones from the neck (index 0) to the tail tip, each a child of
    the previous. mode fly / swim: vertical undulation; slither: lateral. legs: (upper, lower, side) paddle in time."""
    n = len(chain)
    vert = mode in ("fly", "swim")

    def wave(pose, u, a_v, a_h, k=waves):
        # each link's ORIENTATION follows the wave (local delta = difference to the parent), so the chain undulates
        # in place instead of the rotations piling up down a long body
        prev_v = prev_h = 0.0
        for i, b in enumerate(chain):
            ph = TAU * (u - k * i / n)
            if vert:
                tv, th = a_v * math.sin(ph), a_h * math.sin(ph - 0.9)
            else:
                tv, th = 0.15 * a_v * math.sin(ph), a_h * math.sin(ph)
            _add(pose, b, (0, 0, 0, tv - prev_v, th - prev_h, 0))
            prev_v, prev_h = tv, th

    def neckwave(pose, u, a):
        for i, b in enumerate(neck):
            _add(pose, b, (0, 0, 0, -a * 0.5 * math.sin(TAU * (u + (i + 1) * waves / n)), 0, 0))

    def move(t):
        u = t / period
        pose = {}
        wave(pose, u, amp, lat if vert else amp * 1.6)
        neckwave(pose, u, amp if vert else 0.0)
        _add(pose, "Body", (0, lift * height + 0.03 * height * math.sin(TAU * u), 0, -amp * 0.3 * math.sin(TAU * u + 0.9), 0, 0))
        _add(pose, head, (0, 0, 0, amp * 0.6 * math.sin(TAU * u + 2.2), 0, 0))
        for i, (up, lo, side) in enumerate(legs):
            ph = TAU * (u + (0.5 if side > 0 else 0.0) + 0.25 * (i // 2))
            _add(pose, up, (0, 0, 0, 0.45 * math.sin(ph), 0, 0))
            _add(pose, lo, (0, 0, 0, -0.35 * max(0.0, math.cos(ph)), 0, 0))
        for i, (b, side) in enumerate(fins):
            _add(pose, b, (0, 0, 0, 0, 0, side * 0.3 * math.sin(TAU * u * 2 - i)))
        for i, (b, side) in enumerate(whiskers):
            _add(pose, b, (0, 0, 0, 0.12 * math.sin(TAU * u - i), side * 0.15 * math.sin(TAU * u - 0.5 - i), 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.05 - 0.04 * math.sin(TAU * u), 0, 0))
        return pose

    def idle(t):
        u = t / 4.0
        pose = {}
        wave(pose, u, amp * 0.45, lat * 0.6 if vert else amp * 0.5)
        neckwave(pose, u, amp * 0.45)
        _add(pose, "Body", (0, lift * height * 0.6 + 0.02 * height * math.sin(TAU * u), 0, 0, 0, 0))
        _add(pose, head, (0, 0, 0, 0.06 * math.sin(TAU * u * 2 + 1), 0.25 * math.sin(TAU * u), 0))
        for i, (up, lo, side) in enumerate(legs):
            _add(pose, up, (0, 0, 0, 0.12 * math.sin(TAU * u * 2 + i), 0, 0))
        for i, (b, side) in enumerate(fins):
            _add(pose, b, (0, 0, 0, 0, 0, side * 0.15 * math.sin(TAU * u * 3 - i)))
        for i, (b, side) in enumerate(whiskers):
            _add(pose, b, (0, 0, 0, 0.1 * math.sin(TAU * u * 2 - i), side * 0.12 * math.sin(TAU * u * 2 - 0.5 - i), 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.1 * max(0.0, math.sin(TAU * u - 1)) ** 6, 0, 0))
        return pose

    L = 1.0

    def atk(t):
        s = t / L
        pose = {}
        coil = window(s, 0.0, 0.3, 0.32, 0.5)
        strike = window(s, 0.3, 0.45, 0.6, 0.95)
        m = min(n, 4)
        for i, b in enumerate(chain[:m]):
            _add(pose, b, (0, 0, 0, (0.22 * coil - 0.2 * strike) * (1 - i / m), 0, 0))
        _add(pose, "Body", (0, 0.04 * height * coil, -0.25 * height * strike, 0.12 * coil - 0.05 * strike, 0, 0))
        _add(pose, head, (0, 0, 0, 0.2 * coil - 0.25 * strike, 0, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.3 * coil - 0.5 * strike, 0, 0))
        for i, b in enumerate(chain[m:]):
            _add(pose, b, (0, 0, 0, 0, 0.2 * math.sin(TAU * s - i * 0.6) * (coil + strike), 0))
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0, 0.06 * height * k, 0.08 * k, 0, 0.05 * math.sin(t * 38) * k))
        for i, b in enumerate(chain[:3]):
            _add(pose, b, (0, 0, 0, 0.15 * k, 0.08 * k, 0))
        _add(pose, head, (0, 0, 0, 0.2 * k, 0.1 * k, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.3 * k, 0, 0))
        for i, b in enumerate(chain[3:]):
            _add(pose, b, (0, 0, 0, 0, 0.12 * k * math.sin(i), 0))
        return pose

    H.clip("Move", period, move, keys=24)
    H.clip("Idle", 4.0, idle, keys=24)
    H.clip("Attack", L, atk, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})
