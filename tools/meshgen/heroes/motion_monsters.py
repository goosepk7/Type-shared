"""Extra motion cycles for the monsters / spirits / constructs / apes families (motion.py stays untouched).

Pose values are (px, py, pz, rx, ry, rz) in the parent frame (see motion.py). Conventions for a model facing -Z:
+rx on a hanging limb swings it forward, +rx on Body pitches the nose up; for a RIGHT arm or wing (+X side) +rz raises
it outward / up (left side: -rz); +ry turns the model toward its left.

* overlay(H, clip, fn): add fn(t) on top of an already sampled clip (zombie arms, wing flutter on a biped walk ...)
* floater(...): ghosts, wraiths, elementals, robed figures: bob, drifting arms, trailing cloth chain; the attack is a
  haunting lunge (rear back, then surge forward with clawing arms and a gaping jaw).
* hoverer(...): winged humanoids that hover (fairy, angel, imp): wing beats with lagging tips, dangling legs, a
  dart / swoop attack with the weapon arm.
* swimmer(...): merfolk: dolphin-kick wave down a tail chain, breast-stroke arms.
* blob(...): slimes / oozes: squash-and-stretch hop, wobble, a body-slam attack.
* knuckle(...): apes: motion.quadruped for the knuckle walk, then a rear-up chest-beat / double-fist slam attack.
"""
import math

import motion

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


def bump(s, a, b):
    """0 -> 1 -> 0 between a and b (sine bump)."""
    if s <= a or s >= b:
        return 0.0
    return math.sin(math.pi * (s - a) / (b - a))


def overlay(H, name, fn):
    c = H.clips.get(name)
    if not c:
        return
    n, L = c["keys"], c["len"]
    times = [L * i / n for i in range(n)] if c["loop"] else [L * i / (n - 1) for i in range(n)]
    for i, t in enumerate(times):
        for b, v in fn(t).items():
            if b is None:
                continue
            assert b in H.bidx, f"{H.id}: overlay {name} bone {b} unknown"
            tr = c["tracks"].setdefault(b, [(0.0,) * 6 for _ in range(n)])
            o = list(tr[i])
            for k, x in enumerate(v):
                o[k] += x
            tr[i] = tuple(o)


def replace(H, name, length, fn, keys=14, loop=False):
    H.clip(name, length, fn, keys=keys, loop=loop)


def wing_pose(pose, wings, ph, amp, base=0.0, tip_lag=0.9, fold=0.0, sweep=0.0):
    """wings: list of (root, tip_or_None, side). ph: flap phase (radians). Up-stroke = +rz on the right wing."""
    for root, tip, side in wings:
        sg = 1 if side > 0 else -1
        a = base + amp * math.sin(ph)
        _add(pose, root, (0, 0, 0, 0, sg * (sweep * math.cos(ph)), sg * a))
        if tip:
            _add(pose, tip, (0, 0, 0, 0, sg * fold, sg * amp * 0.55 * math.sin(ph - tip_lag)))


def floater(H, arms=(), spine=None, head=None, jaw=None, tail=(), height=5.0, hover=0.35, attack="lunge", weapon_arm=None,
            hair=(), wings=(), lean=0.22, legs=()):
    """legs: (hip, knee, foot, side) that dangle / trail (ghost with feet, elemental wisps)."""

    def base(pose, u, amt=1.0):
        _add(pose, "Body", (0, hover * height * 0.1 + 0.035 * height * math.sin(TAU * u), 0, 0, 0, 0.03 * math.sin(TAU * u * 0.5 + 1)))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.1 * amt * math.sin(TAU * u - i * 0.9), 0.12 * amt * math.sin(TAU * u * 0.5 - i * 0.7), 0.06 * math.sin(TAU * u - i)))
        for i, b in enumerate(hair):
            _add(pose, b, (0, 0, 0, 0.08 * math.sin(TAU * u - i * 0.8 + 0.5), 0, 0.05 * math.sin(TAU * u * 0.5 - i)))

    def idle(t):
        u = t / 4.0
        pose = {}
        base(pose, u)
        _add(pose, spine, (0, 0, 0, 0.03 * math.sin(TAU * u + 0.6), 0.05 * math.sin(TAU * u * 0.5), 0))
        _add(pose, head, (0, 0, 0, 0.05 * math.sin(TAU * u + 1.1), 0.2 * math.sin(TAU * u * 0.5 + 0.3), 0.04 * math.sin(TAU * u)))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            ph = 0 if side > 0 else 1.7
            _add(pose, sh, (0, 0, 0, 0.25 + 0.1 * math.sin(TAU * u + ph), 0, sg * (0.18 + 0.06 * math.sin(TAU * u + ph + 1))))
            _add(pose, el, (0, 0, 0, 0.35 + 0.12 * math.sin(TAU * u + ph + 0.6), 0, 0))
            _add(pose, hd, (0, 0, 0, 0.1 * math.sin(TAU * u + ph + 1.2), 0, 0))
        for hip, knee, foot, side in legs:
            ph = 0 if side > 0 else 2.0
            _add(pose, hip, (0, 0, 0, 0.12 + 0.08 * math.sin(TAU * u + ph), 0, 0))
            _add(pose, knee, (0, 0, 0, -0.25 - 0.08 * math.sin(TAU * u + ph + 0.5), 0, 0))
            _add(pose, foot, (0, 0, 0, -0.3, 0, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.06 * max(0.0, math.sin(TAU * u)) ** 3, 0, 0))
        if wings:
            wing_pose(pose, wings, TAU * u * 2, 0.12, base=0.05)
        return pose

    def move(t):
        u = t / 1.6
        pose = {}
        base(pose, u * 2, 1.6)
        _add(pose, "Body", (0, 0, 0, -lean, 0.05 * math.sin(TAU * u), 0.05 * math.sin(TAU * u)))
        _add(pose, spine, (0, 0, 0, 0.04 * math.sin(TAU * u * 2), 0, 0))
        _add(pose, head, (0, 0, 0, lean * 0.6 + 0.04 * math.sin(TAU * u * 2 + 1), 0.06 * math.sin(TAU * u), 0))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            ph = 0 if side > 0 else math.pi
            _add(pose, sh, (0, 0, 0, -0.35 + 0.18 * math.sin(TAU * u + ph), 0, sg * (0.22 + 0.05 * math.sin(TAU * u * 2))))
            _add(pose, el, (0, 0, 0, 0.3 + 0.15 * math.sin(TAU * u + ph + 0.8), 0, 0))
            _add(pose, hd, (0, 0, 0, -0.15 + 0.12 * math.sin(TAU * u + ph + 1.4), 0, 0))
        for hip, knee, foot, side in legs:
            ph = 0 if side > 0 else math.pi
            _add(pose, hip, (0, 0, 0, -0.35 + 0.12 * math.sin(TAU * u + ph), 0, 0))
            _add(pose, knee, (0, 0, 0, -0.35 + 0.1 * math.sin(TAU * u + ph + 0.7), 0, 0))
            _add(pose, foot, (0, 0, 0, -0.4, 0, 0))
        if wings:
            wing_pose(pose, wings, TAU * u * 2, 0.35, base=0.1)
        return pose

    def attack_fn(t):
        L = 1.0
        s = t / L
        pose = {}
        wind = ease(s / 0.35) * (1 - ease((s - 0.35) / 0.15))
        strike = bump(s, 0.3, 0.85)
        rec = 1 - ease((s - 0.75) / 0.25)
        _add(pose, "Body", (0, (0.12 * wind + 0.04 * strike) * height, (0.14 * wind - 0.38 * strike) * height, (0.18 * wind - 0.32 * strike), 0, 0))
        _add(pose, spine, (0, 0, 0, 0.12 * wind - 0.2 * strike, 0, 0))
        _add(pose, head, (0, 0, 0, 0.15 * wind + 0.12 * strike, 0, 0))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            if attack == "cast" and weapon_arm and sh != weapon_arm:
                continue
            _add(pose, sh, (0, 0, 0, 1.3 * wind + 1.6 * strike, 0, sg * (0.6 * wind + 0.15 * strike)))
            _add(pose, el, (0, 0, 0, 0.9 * wind - 0.2 * strike, 0, 0))
            _add(pose, hd, (0, 0, 0, -0.5 * wind + 0.4 * strike, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, -0.25 * wind + 0.35 * strike, 0.15 * math.sin(TAU * s * 2 - i), 0))
        for i, b in enumerate(hair):
            _add(pose, b, (0, 0, 0, 0.3 * strike, 0, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.55 * strike - 0.1 * wind, 0, 0))
        if wings:
            wing_pose(pose, wings, TAU * s * 2.5, 0.5 * (wind + strike), base=0.3 * wind)
        for k, v in list(pose.items()):
            pose[k] = tuple(x * rec for x in v)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0.03 * height * k, 0.1 * height * k, 0.2 * k, 0, 0.08 * math.sin(t * 38) * k))
        _add(pose, head, (0, 0, 0, 0.3 * k, 0.15 * k, 0))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, 0.6 * k, 0, sg * 0.5 * k))
            _add(pose, el, (0, 0, 0, 0.5 * k, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, -0.3 * k, 0, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.35 * k, 0, 0))
        return pose

    H.clip("Idle", 4.0, idle, keys=20)
    H.clip("Move", 1.6, move, keys=20)
    H.clip("Attack", 1.0, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"height": height})


def hoverer(H, wings, arms=(), legs=(), spine=None, head=None, jaw=None, tail=(), height=5.0, rate=1.0, amp=0.55,
            weapon_arm=None, hair=()):
    """Winged figure hovering: wings (root, tip, side); legs (hip, knee, foot, side) dangle."""

    def body(pose, u, k=1.0):
        _add(pose, "Body", (0, 0.03 * height * math.sin(TAU * u * 2 * rate - 1.2), 0, 0, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.12 * math.sin(TAU * u * 2 - i * 0.8), 0.18 * math.sin(TAU * u - i * 0.9), 0))
        for i, b in enumerate(hair):
            _add(pose, b, (0, 0, 0, 0.06 * math.sin(TAU * u * 2 - i * 0.8), 0, 0))

    def idle(t):
        u = t / 2.0
        pose = {}
        body(pose, u)
        wing_pose(pose, wings, TAU * u * 4 * rate, amp, base=0.1)
        _add(pose, head, (0, 0, 0, 0.04 * math.sin(TAU * u), 0.15 * math.sin(TAU * u * 0.5), 0))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, 0.15 + 0.05 * math.sin(TAU * u * 2), 0, sg * (0.25 + 0.05 * math.sin(TAU * u * 2 + 1))))
            _add(pose, el, (0, 0, 0, 0.4, 0, 0))
        for hip, knee, foot, side in legs:
            ph = 0 if side > 0 else 1.5
            _add(pose, hip, (0, 0, 0, 0.15 + 0.1 * math.sin(TAU * u * 2 + ph), 0, 0))
            _add(pose, knee, (0, 0, 0, -0.45 - 0.1 * math.sin(TAU * u * 2 + ph + 0.7), 0, 0))
            _add(pose, foot, (0, 0, 0, -0.35, 0, 0))
        return pose

    def move(t):
        u = t / 1.0
        pose = {}
        body(pose, u)
        _add(pose, "Body", (0, 0, 0, -0.3, 0, 0.06 * math.sin(TAU * u)))
        _add(pose, head, (0, 0, 0, 0.22, 0, 0))
        wing_pose(pose, wings, TAU * u * 3 * rate, amp * 1.25, base=0.15)
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, -0.45, 0, sg * 0.2))
            _add(pose, el, (0, 0, 0, 0.25, 0, 0))
        for hip, knee, foot, side in legs:
            ph = 0 if side > 0 else math.pi
            _add(pose, hip, (0, 0, 0, -0.25 + 0.1 * math.sin(TAU * u + ph), 0, 0))
            _add(pose, knee, (0, 0, 0, -0.5 + 0.1 * math.sin(TAU * u + ph + 0.6), 0, 0))
            _add(pose, foot, (0, 0, 0, -0.45, 0, 0))
        return pose

    def attack_fn(t):
        L = 0.9
        s = t / L
        pose = {}
        wind = ease(s / 0.35) * (1 - ease((s - 0.35) / 0.15))
        strike = bump(s, 0.3, 0.8)
        rec = 1 - ease((s - 0.7) / 0.3)
        body(pose, s)
        _add(pose, "Body", (0, (0.1 * wind - 0.06 * strike) * height, (0.1 * wind - 0.3 * strike) * height, 0.2 * wind - 0.35 * strike, 0, 0))
        wing_pose(pose, wings, TAU * s * 3 * rate, amp * 1.4, base=0.4 * wind - 0.2 * strike)
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            if weapon_arm is None or sh == weapon_arm:
                _add(pose, sh, (0, 0, 0, 2.2 * wind + 0.5 * strike, 0, sg * 0.25 * wind))
                _add(pose, el, (0, 0, 0, 0.8 * wind - 0.3 * strike, 0, 0))
            else:
                _add(pose, sh, (0, 0, 0, -0.3 * strike, 0, sg * 0.4 * strike))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.4 * strike, 0, 0))
        for k, v in list(pose.items()):
            pose[k] = tuple(x * rec for x in v)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0.04 * height * k, 0.1 * height * k, 0.25 * k, 0, 0.1 * math.sin(t * 40) * k))
        _add(pose, head, (0, 0, 0, 0.25 * k, 0, 0))
        wing_pose(pose, wings, 0.0, 0.0, base=0.6 * k)
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, 0.6 * k, 0, sg * 0.5 * k))
        return pose

    H.clip("Idle", 2.0, idle, keys=24)
    H.clip("Move", 1.0, move, keys=20)
    H.clip("Attack", 0.9, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"height": height})


def swimmer(H, tail, arms=(), spine=None, head=None, jaw=None, height=5.0, hair=()):
    """Merfolk: a dolphin kick travels down the tail chain (rx), arms stroke."""

    def wave(pose, u, amp, lag=0.75):
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, amp * (0.5 + 0.25 * i) * math.sin(TAU * u - i * lag), 0.03 * math.sin(TAU * u * 0.5 - i), 0))
        for i, b in enumerate(hair):
            _add(pose, b, (0, 0, 0, 0.1 * math.sin(TAU * u - 1 - i * 0.7), 0, 0.05 * math.sin(TAU * u * 0.5 - i)))

    def idle(t):
        u = t / 3.0
        pose = {}
        wave(pose, u, 0.18)
        _add(pose, "Body", (0, 0.03 * height * math.sin(TAU * u + 0.6), 0, 0.03 * math.sin(TAU * u), 0, 0))
        _add(pose, head, (0, 0, 0, 0.03 * math.sin(TAU * u), 0.18 * math.sin(TAU * u * 0.5 + 0.4), 0))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            ph = 0 if side > 0 else 1.2
            _add(pose, sh, (0, 0, 0, 0.2 + 0.12 * math.sin(TAU * u + ph), 0, sg * (0.35 + 0.1 * math.sin(TAU * u + ph + 1))))
            _add(pose, el, (0, 0, 0, 0.35 + 0.1 * math.sin(TAU * u + ph), 0, 0))
        return pose

    def move(t):
        u = t / 1.2
        pose = {}
        wave(pose, u, 0.35)
        _add(pose, "Body", (0, 0.04 * height * math.sin(TAU * u + 0.9), 0, -0.45 + 0.06 * math.sin(TAU * u + 0.4), 0, 0))
        _add(pose, head, (0, 0, 0, 0.35, 0, 0))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            st = math.sin(TAU * u)
            _add(pose, sh, (0, 0, 0, 0.9 + 0.9 * st, 0, sg * (0.4 - 0.35 * st)))
            _add(pose, el, (0, 0, 0, 0.3 + 0.3 * max(0.0, -st), 0, 0))
        return pose

    def attack_fn(t):
        L = 0.9
        s = t / L
        pose = {}
        wind = ease(s / 0.35) * (1 - ease((s - 0.35) / 0.15))
        strike = bump(s, 0.3, 0.8)
        rec = 1 - ease((s - 0.7) / 0.3)
        wave(pose, s * 2, 0.3 * (wind + strike))
        _add(pose, "Body", (0, 0.06 * height * wind, (0.08 * wind - 0.3 * strike) * height, 0.25 * wind - 0.3 * strike, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, -0.35 * wind + 0.5 * strike, 0, 0))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, 2.0 * wind + 0.9 * strike, 0, sg * 0.2 * wind))
            _add(pose, el, (0, 0, 0, 0.7 * wind - 0.4 * strike, 0, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.4 * strike, 0, 0))
        for k, v in list(pose.items()):
            pose[k] = tuple(x * rec for x in v)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0, 0.1 * height * k, 0.25 * k, 0, 0.08 * math.sin(t * 40) * k))
        _add(pose, head, (0, 0, 0, 0.25 * k, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, -0.3 * k, 0, 0))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, 0.5 * k, 0, sg * 0.5 * k))
        return pose

    H.clip("Idle", 3.0, idle, keys=20)
    H.clip("Move", 1.2, move, keys=20)
    H.clip("Attack", 0.9, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"height": height})


def blob(H, top=None, eyes=(), drips=(), arms=(), height=3.0, jaw=None):
    """Slimes: Body squashes and stretches through translation + a 'Top' bone that lifts / tilts (the dome),
    eye stalks lag, drips sway. Move = hop; Attack = rear up tall then belly slam forward."""

    def idle(t):
        u = t / 2.4
        pose = {}
        w = math.sin(TAU * u)
        _add(pose, top, (0, 0.04 * height * w, 0, 0.04 * math.sin(TAU * u + 1), 0, 0.05 * math.sin(TAU * u * 0.5)))
        for i, b in enumerate(eyes):
            _add(pose, b, (0, 0.015 * height * math.sin(TAU * u - 0.8), 0, 0.06 * math.sin(TAU * u - 1 - i), 0, 0.06 * math.sin(TAU * u * 0.5 + i)))
        for i, b in enumerate(drips):
            _add(pose, b, (0, -0.02 * height * max(0.0, math.sin(TAU * u + i * 1.3)), 0, 0.08 * math.sin(TAU * u + i), 0, 0.08 * math.sin(TAU * u + i * 2)))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, 0.1 * math.sin(TAU * u + side), 0, sg * 0.15 * math.sin(TAU * u)))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.08 * max(0.0, math.sin(TAU * u)), 0, 0))
        return pose

    def move(t):
        u = t / 0.8
        pose = {}
        ph = TAU * u
        air = max(0.0, math.sin(ph))  # 0..1 in the air
        squash = max(0.0, -math.sin(ph))
        _add(pose, "Body", (0, 0.32 * height * air, 0, 0.12 * math.cos(ph), 0, 0))
        _add(pose, top, (0, (0.1 * air - 0.12 * squash) * height, 0.05 * height * math.cos(ph), -0.18 * math.cos(ph), 0, 0))
        for i, b in enumerate(eyes):
            _add(pose, b, (0, -0.04 * height * math.cos(ph - 0.6), 0, 0.2 * math.cos(ph - 0.8), 0, 0))
        for i, b in enumerate(drips):
            _add(pose, b, (0, 0, 0, -0.25 * math.cos(ph - 0.5 - i * 0.3), 0, 0))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, 0, 0, sg * (0.25 * air - 0.1)))
        return pose

    def attack_fn(t):
        L = 0.9
        s = t / L
        pose = {}
        wind = ease(s / 0.4) * (1 - ease((s - 0.4) / 0.12))
        strike = bump(s, 0.38, 0.8)
        rec = 1 - ease((s - 0.7) / 0.3)
        _add(pose, "Body", (0, (0.15 * wind + 0.05 * strike) * height, (0.1 * wind - 0.45 * strike) * height, 0.15 * wind - 0.45 * strike, 0, 0))
        _add(pose, top, (0, (0.25 * wind - 0.15 * strike) * height, -0.1 * height * strike, -0.3 * strike, 0, 0))
        for i, b in enumerate(eyes):
            _add(pose, b, (0, 0, 0, 0.3 * wind - 0.3 * strike, 0, 0))
        for i, b in enumerate(drips):
            _add(pose, b, (0, 0, 0, 0.4 * strike, 0, 0))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, 1.5 * wind + 1.0 * strike, 0, sg * 0.3 * wind))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.6 * strike, 0, 0))
        for k, v in list(pose.items()):
            pose[k] = tuple(x * rec for x in v)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, -0.05 * height * k, 0.12 * height * k, 0.2 * k, 0, 0.1 * math.sin(t * 40) * k))
        _add(pose, top, (0, -0.1 * height * k, 0.05 * height * k, 0.2 * k, 0, 0))
        for i, b in enumerate(eyes):
            _add(pose, b, (0, 0, 0, 0.4 * k, 0, 0.2 * k * (1 if i % 2 else -1)))
        return pose

    H.clip("Idle", 2.4, idle, keys=20)
    H.clip("Move", 0.8, move, keys=16)
    H.clip("Attack", 0.9, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"height": height})


def knuckle(H, legs, arms, spine=None, neck=None, head=None, jaw=None, tail=(), height=3.0, walk=1.1, stride=0.38, beat=True):
    """Apes: knuckle walk on all fours (motion.quadruped, arms = front legs), then an upright chest-beat (beat=True)
    or a double-fist slam attack."""
    qlegs = [(a[0], a[1], a[2], ph, True) for a, ph in zip(arms, (0.75, 0.25))] + [(l[0], l[1], l[2], ph, False) for l, ph in zip(legs, (0.5, 0.0))]
    motion.quadruped(H, qlegs, spine=spine, neck=neck, head=head, jaw=jaw, tail=tail, stride=stride, walk=walk, height=height, attack="bite")

    def attack_fn(t):
        L = 1.2
        s = t / L
        pose = {}
        up = ease(s / 0.3) * (1 - ease((s - 0.75) / 0.25))
        _add(pose, "Body", (0, 0.18 * height * up, 0.1 * height * up, 0.75 * up, 0, 0))
        _add(pose, spine, (0, 0, 0, 0.2 * up, 0, 0))
        _add(pose, head, (0, 0, 0, -0.5 * up, 0, 0))
        for hip, knee, foot in legs:
            _add(pose, hip, (0, 0, 0, -0.65 * up, 0, 0))
            _add(pose, knee, (0, 0, 0, 0.25 * up, 0, 0))
            _add(pose, foot, (0, 0, 0, 0.35 * up, 0, 0))
        for i, (sh, el, hd, side) in enumerate(arms):
            sg = 1 if side > 0 else -1
            if beat:
                b = 0.5 + 0.5 * math.sin(TAU * (s - 0.3) * 4 + (0 if side > 0 else math.pi))
                _add(pose, sh, (0, 0, 0, -0.5 * up + 0.5 * up * b, 0, sg * (-0.25 * up)))
                _add(pose, el, (0, 0, 0, 1.9 * up, 0, 0))
                _add(pose, hd, (0, 0, 0, 0.0, 0, 0))
            else:
                sl = bump(s, 0.45, 0.85)
                _add(pose, sh, (0, 0, 0, -1.0 * up - 1.6 * sl, 0, 0))
                _add(pose, el, (0, 0, 0, 0.6 * up - 0.4 * sl, 0, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.55 * up, 0, 0))
        return pose

    H.clip("Attack", 1.2, attack_fn, keys=18, loop=False)


def biped_extra(H, legs, arms, spine=None, head=None, jaw=None, tail=(), stride=0.5, walk=1.0, height=5.0, attack="punch",
                lean=0.0, weapon_arm=None, shamble=0.0, arms_out=0.0, stomp=0.0, wings=(), hair=()):
    """motion.biped plus: zombie arms held out, shamble limp, heavy stomp (body drops, shoulders roll), wing tuck."""
    motion.biped(H, legs, arms=arms, spine=spine, head=head, jaw=jaw, tail=tail, stride=stride, walk=walk, height=height,
                 attack=attack, lean=lean, weapon_arm=weapon_arm)

    def mv(t):
        u = t / walk
        pose = {}
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            if arms_out:
                _add(pose, sh, (0, 0, 0, arms_out + 0.08 * math.sin(TAU * u * 2 + side), 0, sg * 0.05))
                _add(pose, el, (0, 0, 0, -0.25, 0, 0))
            if stomp:
                _add(pose, sh, (0, 0, 0, 0, 0, sg * stomp * 0.15 * (1 + math.sin(TAU * u * 2))))
        if shamble:
            _add(pose, "Body", (0, 0, 0, 0, 0, shamble * 0.08 * math.sin(TAU * u)))
            _add(pose, head, (0, 0, 0, 0, 0, shamble * 0.25 + shamble * 0.06 * math.sin(TAU * u)))
            if legs:
                _add(pose, legs[0][1], (0, 0, 0, -shamble * 0.15, 0, 0))
        if stomp:
            _add(pose, "Body", (0, -stomp * 0.02 * height * abs(math.cos(TAU * u)), 0, 0, 0, stomp * 0.04 * math.sin(TAU * u)))
            _add(pose, spine, (0, 0, 0, 0, 0, -stomp * 0.04 * math.sin(TAU * u)))
        wing_pose(pose, wings, TAU * u * 2, 0.05, base=0.0)
        for i, b in enumerate(hair):
            _add(pose, b, (0, 0, 0, 0.08 * math.sin(TAU * u * 2 - i * 0.8), 0, 0))
        return pose

    def idl(t):
        u = t / 4.0
        pose = {}
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            if arms_out:
                _add(pose, sh, (0, 0, 0, arms_out * 0.9 + 0.05 * math.sin(TAU * u * 2 + side), 0, 0))
                _add(pose, el, (0, 0, 0, -0.3, 0, 0))
        if shamble:
            _add(pose, head, (0, 0, 0, 0.05 * math.sin(TAU * u), 0, shamble * 0.3))
        wing_pose(pose, wings, TAU * u * 2, 0.06, base=0.0)
        for i, b in enumerate(hair):
            _add(pose, b, (0, 0, 0, 0.04 * math.sin(TAU * u * 2 - i * 0.8), 0, 0))
        return pose

    def atk(t):
        s = t / 0.8
        pose = {}
        wind = ease(s / 0.35) * (1 - ease((s - 0.35) / 0.15))
        strike = bump(s, 0.3, 0.75)
        wing_pose(pose, wings, 0.0, 0.0, base=0.5 * wind + 0.2 * strike)
        if stomp:
            _add(pose, "Body", (0, -0.04 * height * strike, 0, 0, 0, 0))
        return pose

    overlay(H, "Move", mv)
    overlay(H, "Idle", idl)
    overlay(H, "Attack", atk)
