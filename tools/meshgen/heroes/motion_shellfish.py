"""Authored motion for the shellfish family (h_shellfish.py): bivalves that breathe open / clap-hop / snap shut,
gastropods that glide or lurch (conch), segmented armour that walks on a metachronal leg wave and ENROLLS into a
ball (pill bug, isopod, trilobite), colonial chains that drift on a travelling wave (salp, siphonophore, pyrosome),
sessile tubes whose crowns fan and snap back into the tube (tube worms, sea squirt, hydra) and squishy crawlers.

Pose values (px, py, pz, rx, ry, rz) at a bone pivot in its parent frame (see motion.py). +rx pitches a
forward-pointing (-Z) part UP and a backward-pointing (+Z) part DOWN.
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


def _ease(x):
    return 0.5 - 0.5 * math.cos(math.pi * min(max(x, 0.0), 1.0))


def _env(s, a, b):
    """0 -> 1 -> 0 bump between s = a and s = b."""
    return math.sin(math.pi * min(max((s - a) / (b - a), 0.0), 1.0))


def _ramp(s, a, b):
    return _ease((s - a) / (b - a))


def _scale(pose, k):
    for b, v in list(pose.items()):
        pose[b] = tuple(x * k for x in v)


def _rec(s, a=0.62):
    return 1.0 if s < a else 1 - _ease((s - a) / (1 - a))


# ================================================================================================ bivalves
def bivalve(H, valves, height=1.0, rest=0.22, style="hop", foot=None, neck=(), mantle=None, eyes=(), period=1.0, hinge_axis=3,
            extra=None):
    """valves: list of (bone, sign): the valve opens when its hinge_axis angle (3 = rx, 5 = rz) goes to sign * a.
    style: "hop" (the foot kicks the shell into a little hop), "swim" (scallop: rapid clap-jets that lift it off the
    ground and lurch it forward), "rock" (oyster / giant clam: a heavy rock-and-scoot), "neck" (geoduck: the siphon
    neck leads, the shell scoots behind). foot: bone of the muscular foot (pushes out front and back in)."""

    def opn(pose, a):
        for b, sg in valves:
            v = [0.0] * 6
            v[hinge_axis] = sg * a
            _add(pose, b, tuple(v))

    def neck_wave(pose, u, a, lift=0.0):
        for i, b in enumerate(neck):
            _add(pose, b, (0, 0, 0, lift * (1 if i == 0 else 0.4) + 0.12 * a * math.sin(TAU * u - i * 0.9), 0.3 * a * math.sin(TAU * u * 0.5 - i * 0.8 + 0.4),
                           0.08 * a * math.sin(TAU * u - i * 0.7)))

    def idle(t):
        u = t / 4.8
        pose = {}
        # slow breathing gape with a quick 'cough' clap two thirds of the way through
        cough = _env(u, 0.62, 0.74)
        a = rest + 0.08 * math.sin(TAU * u) - (rest + 0.04) * cough
        opn(pose, a)
        _add(pose, "Body", (0, 0.04 * height * cough, 0, 0.015 * math.sin(TAU * u), 0, 0.02 * math.sin(TAU * u * 2)))
        if foot:
            _add(pose, foot, (0, 0, -0.08 * height * math.sin(TAU * u), 0.15 * math.sin(TAU * u * 2), 0, 0))
        neck_wave(pose, u * 2, 1.0)
        for i, (b, sg) in enumerate(eyes):
            tw = max(0.0, math.sin(TAU * (u * 3 + i * 0.13))) ** 6
            _add(pose, b, (0, 0, 0, sg * 0.25 * tw, 0, 0))
        if extra:
            extra(pose, "idle", u, a)
        return pose

    def move(t):
        u = t / period
        pose = {}
        if style == "swim":
            # two quick claps per cycle: shell jumps up and forward, then glides back down open
            c = 0.5 + 0.5 * math.cos(TAU * u * 2)
            a = 0.08 + 0.42 * c
            lift = 0.35 * height * (0.6 + 0.4 * math.sin(TAU * u))
            _add(pose, "Body", (0, lift, 0, 0.18 + 0.1 * (1 - c), 0.08 * math.sin(TAU * u), 0.06 * math.sin(TAU * u * 2)))
        elif style == "rock":
            a = rest * 0.7 + 0.06 * math.sin(TAU * u)
            w = math.sin(TAU * u)
            _add(pose, "Body", (0, 0.05 * height * abs(w), 0, 0.06 * max(0.0, w), 0, 0.09 * w))
        elif style == "neck":
            a = rest * 0.6 + 0.05 * math.sin(TAU * u)
            _add(pose, "Body", (0, 0.04 * height * abs(math.sin(TAU * u)), 0, 0.03 * math.sin(TAU * u), 0.06 * math.sin(TAU * u), 0.04 * math.sin(TAU * u)))
        else:  # hop
            ph = u % 1.0
            push = _env(ph, 0.0, 0.45)
            air = _env(ph, 0.2, 0.7)
            a = rest * 0.6 - 0.1 * air
            _add(pose, "Body", (0, 0.32 * height * air, 0, -0.12 * push + 0.15 * air, 0, 0.04 * math.sin(TAU * u)))
        opn(pose, a)
        if foot:
            _add(pose, foot, (0, -0.05 * height, -0.15 * height * math.sin(TAU * u), 0.5 * math.sin(TAU * u), 0, 0))
        neck_wave(pose, u, 1.4, lift=-0.05)
        for i, (b, sg) in enumerate(eyes):
            _add(pose, b, (0, 0, 0, sg * 0.1 * math.sin(TAU * u * 2 + i), 0, 0))
        if extra:
            extra(pose, "move", u, a)
        return pose

    def attack(t):
        s = t / 0.8
        pose = {}
        gape = _ramp(s, 0.0, 0.35) * (1 - _ramp(s, 0.38, 0.48))
        strike = _env(s, 0.36, 0.75)
        a = rest + (0.75 - rest) * gape - rest * strike * 0.9
        opn(pose, a)
        _add(pose, "Body", (0, 0.12 * height * gape, -0.45 * height * strike, 0.25 * gape - 0.15 * strike, 0, 0))
        if foot:
            _add(pose, foot, (0, 0, 0.2 * height * strike, -0.4 * strike, 0, 0))
        for i, b in enumerate(neck):
            _add(pose, b, (0, 0, 0, (0.35 * gape - 0.55 * strike) * (1.0 if i == 0 else 0.6), 0, 0))
        if extra:
            extra(pose, "attack", s, strike)
        _scale(pose, _rec(s, 0.7))
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        opn(pose, rest - rest * min(1.0, s * 4) * (1 - s))  # snap shut
        _add(pose, "Body", (0, 0.06 * height * k, 0.15 * height * k, 0.12 * k, 0, 0.15 * k * math.sin(s * 14)))
        for i, b in enumerate(neck):
            _add(pose, b, (0, 0, 0, 0.4 * k, 0, 0))
        if extra:
            extra(pose, "hit", s, k)
        return pose

    H.clip("Idle", 4.8, idle, keys=24)
    H.clip("Move", period, move, keys=20)
    H.clip("Attack", 0.8, attack, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})


# ================================================================================================ gastropods
def gastropod(H, foot=(), head=None, stalks=(), shell=None, height=1.0, period=1.6, style="glide", mantle=(), proboscis=None):
    """Snail-like: style "glide" (a ripple runs down the foot, the shell sways), "lurch" (conch: the shell is hauled
    forward in a heavy hop by the sickle foot), "clamp" (limpet / chiton: hugs the ground, the shell lifts a crack and
    clamps down). stalks: (bone, side) eye stalks / tentacles. mantle: (bone, side) mantle flaps (cowrie) that ripple."""
    n = max(len(foot), 1)

    def move(t):
        u = t / period
        pose = {}
        if style == "lurch":
            ph = u % 1.0
            heave = _env(ph, 0.1, 0.6)
            _add(pose, shell, (0, 0.28 * height * heave, -0.12 * height * heave, 0.12 * heave, 0, 0.1 * math.sin(TAU * u)))
            _add(pose, "Body", (0, 0.03 * height * heave, 0, 0, 0.05 * math.sin(TAU * u), 0))
            for i, b in enumerate(foot):
                _add(pose, b, (0, 0, 0, -0.35 * heave + 0.2 * _env(ph, 0.55, 0.95), 0, 0))
        else:
            for i, b in enumerate(foot):
                _add(pose, b, (0, 0.012 * height * math.sin(TAU * (u * 2 - i / n)), 0, 0.05 * math.sin(TAU * (u * 2 - i / n)), 0.04 * math.sin(TAU * u - i * 0.6), 0))
            k = 0.3 if style == "clamp" else 1.0
            _add(pose, shell, (0, 0.015 * height * math.sin(TAU * u * 2 + 1) * k, 0, 0.025 * math.sin(TAU * u * 2 + 1) * k, 0, 0.04 * math.sin(TAU * u) * k))
            _add(pose, "Body", (0, 0, 0, 0, 0.04 * math.sin(TAU * u), 0))
        _add(pose, head, (0, 0.02 * height * math.sin(TAU * u * 2), 0, 0.05 * math.sin(TAU * u * 2), 0.14 * math.sin(TAU * u), 0))
        for i, (b, sg) in enumerate(stalks):
            _add(pose, b, (0, 0, 0, 0.18 * math.sin(TAU * u + i * 1.5), 0, sg * 0.14 * math.sin(TAU * u * 2 + i)))
        for i, (b, sg) in enumerate(mantle):
            _add(pose, b, (0, 0, 0, 0, 0, sg * 0.1 * math.sin(TAU * u * 2 + i * 0.9)))
        _add(pose, proboscis, (0, 0, 0, 0.12 * math.sin(TAU * u * 2), 0.2 * math.sin(TAU * u), 0))
        return pose

    def idle(t):
        u = t / 4.8
        pose = {}
        _add(pose, head, (0, 0, 0, 0.08 * math.sin(TAU * u), 0.25 * math.sin(TAU * u), 0))
        if style == "clamp":
            lift = _env(u, 0.15, 0.55)
            _add(pose, shell, (0, 0.06 * height * lift, 0, 0.04 * lift * math.sin(TAU * u * 3), 0, 0))
        else:
            _add(pose, shell, (0, 0.012 * height * math.sin(TAU * u * 2), 0, 0.02 * math.sin(TAU * u * 2), 0.05 * math.sin(TAU * u), 0.02 * math.sin(TAU * u)))
        for i, b in enumerate(foot):
            _add(pose, b, (0, 0, 0, 0.025 * math.sin(TAU * (u * 2 - i / n)), 0.03 * math.sin(TAU * u - i), 0))
        for i, (b, sg) in enumerate(stalks):
            _add(pose, b, (0, 0, 0, 0.28 * math.sin(TAU * (u * 2 + i * 0.4)), 0, sg * 0.22 * math.sin(TAU * u * 3 + i)))
        for i, (b, sg) in enumerate(mantle):
            _add(pose, b, (0, 0, 0, 0, 0, sg * 0.08 * math.sin(TAU * u * 3 + i * 1.3)))
        _add(pose, proboscis, (0, 0, 0, 0.2 * math.sin(TAU * u * 2), 0.35 * math.sin(TAU * u), 0))
        return pose

    def attack(t):
        s = t / 0.9
        pose = {}
        wind = _ramp(s, 0.0, 0.35) * (1 - _ramp(s, 0.35, 0.5))
        hitk = _env(s, 0.35, 0.8)
        if style == "clamp":
            _add(pose, shell, (0, 0.2 * height * wind - 0.05 * height * hitk, -0.25 * height * hitk, -0.2 * wind + 0.15 * hitk, 0, 0))
            _add(pose, "Body", (0, 0, -0.2 * height * hitk, 0, 0, 0))
        else:
            _add(pose, shell, (0, 0.1 * height * wind, 0.1 * height * wind - 0.35 * height * hitk, 0.15 * wind - 0.3 * hitk, 0, 0))
            _add(pose, head, (0, 0.1 * height * wind, 0.1 * height * wind - 0.35 * height * hitk, 0.3 * wind - 0.3 * hitk, 0, 0))
            _add(pose, "Body", (0, 0, -0.15 * height * hitk, 0, 0, 0))
        _add(pose, proboscis, (0, 0, 0, 0.5 * wind - 0.6 * hitk, 0, 0))
        for b, sg in stalks:
            _add(pose, b, (0, 0, 0, -0.5 * hitk, 0, 0))
        _scale(pose, _rec(s, 0.65))
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, head, (0, -0.1 * height * k, 0.25 * height * k, -0.3 * k, 0, 0))
        _add(pose, shell, (0, -0.04 * height * k, 0.06 * height * k, 0.1 * k, 0, 0.12 * math.sin(t * 40) * k))
        for b, sg in stalks:
            _add(pose, b, (0, 0, 0, -0.8 * k, 0, 0))
        for b, sg in mantle:
            _add(pose, b, (0, 0, 0, 0, 0, -sg * 0.3 * k))
        return pose

    H.clip("Move", period, move, keys=20)
    H.clip("Idle", 4.8, idle, keys=24)
    H.clip("Attack", 0.9, attack, keys=14, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})


# ================================================================================================ armoured crawlers
def armour(H, front=(), back=(), legs=(), ants=(), extra_bones=(), height=1.0, period=0.8, curl=0.0, roll=False, stride=0.35,
           lift=0.22, flaps=(), extra=None):
    """Isopod / pill bug / trilobite. front: segment bones from Body forward (head last); back: from Body backward.
    legs: (bone, side, index) one bone per leg (hip), swinging fore-aft (ry) with a lift (rz) in a metachronal wave
    running front to back. curl: total enrolment angle (radians) used by Hit / Idle; roll: the Attack curls into a
    ball and rolls forward two turns (pill bug). flaps: (bone, side, index) swimming lobes (opabinia)."""
    nf, nb = max(len(front), 1), max(len(back), 1)

    def enroll(pose, k):
        # spread the curl over the joints; front parts tuck down (-rx), rear parts curl under (+rx)
        nj = len(front) + len(back)
        if nj == 0 or k == 0:
            return
        per = curl * k / nj
        for b in front:
            _add(pose, b, (0, 0, 0, -per, 0, 0))
        for b in back:
            _add(pose, b, (0, 0, 0, per, 0, 0))
        for b, sd, i in legs:
            _add(pose, b, (0, 0, 0, 0, 0, -sd * 0.9 * k))

    def legwave(pose, u, k=1.0):
        nl = max((i for _, _, i in legs), default=0) + 1
        for b, sd, i in legs:
            w = TAU * (u - i / nl * 0.85) + (0.0 if sd > 0 else math.pi)
            sw = math.sin(w)
            lf = max(0.0, math.cos(w)) ** 1.5
            _add(pose, b, (0, 0, 0, 0, stride * k * sw * sd, sd * lift * k * lf))
        nfl = max((i for _, _, i in flaps), default=0) + 1
        for b, sd, i in flaps:
            w = TAU * (u * 1.0 - i / nfl * 0.9)
            _add(pose, b, (0, 0, 0, 0, 0, sd * 0.35 * k * math.sin(w)))

    def move(t):
        u = t / period
        pose = {}
        legwave(pose, u * (1 if not flaps else 1), 1.0)
        _add(pose, "Body", (0, 0.015 * height * math.sin(TAU * u * 2), 0, 0, 0.03 * math.sin(TAU * u), 0.015 * math.sin(TAU * u * 2)))
        for i, b in enumerate(back):
            _add(pose, b, (0, 0, 0, 0.02 * math.sin(TAU * u * 2 - i * 0.5) if not flaps else 0.06 * math.sin(TAU * u - i * 0.7), -0.04 * math.sin(TAU * u - i * 0.6), 0))
        for i, b in enumerate(front):
            _add(pose, b, (0, 0, 0, 0.02 * math.sin(TAU * u * 2 + i), 0.03 * math.sin(TAU * u + i * 0.4), 0))
        for i, (b, sg) in enumerate(ants):
            _add(pose, b, (0, 0, 0, 0.12 * math.sin(TAU * u * 2 + i), sg * 0.18 * math.sin(TAU * u + i * 0.7), 0))
        if extra:
            extra(pose, "move", u, 1.0)
        return pose

    def idle(t):
        u = t / 6.0
        pose = {}
        legwave(pose, u * 3, 0.12)
        # a cautious half-curl midway (only for rollers), otherwise a slow breathing flex
        if curl:
            k = _env(u, 0.45, 0.85) ** 1.5 * 0.55
            enroll(pose, k)
        for i, b in enumerate(back):
            _add(pose, b, (0, 0, 0, 0.02 * math.sin(TAU * u * 2 - i * 0.5), 0.02 * math.sin(TAU * u - i * 0.4), 0))
        for i, (b, sg) in enumerate(ants):
            _add(pose, b, (0, 0, 0, 0.18 * math.sin(TAU * (u * 4 + i * 0.3)), sg * 0.25 * math.sin(TAU * u * 3 + i), 0))
        _add(pose, front[-1] if front else None, (0, 0, 0, 0.04 * math.sin(TAU * u * 2), 0.08 * math.sin(TAU * u), 0))
        if extra:
            extra(pose, "idle", u, 0.0)
        return pose

    def attack(t):
        L = 1.2 if roll else 0.8
        s = t / L
        pose = {}
        if roll:
            k = _ramp(s, 0.0, 0.2) * (1 - _ramp(s, 0.8, 1.0))
            enroll(pose, k)
            # ball radius ~ height: roll forward two turns while rolled up
            turns = _ramp(s, 0.18, 0.82)
            r = 0.55 * height
            _add(pose, "Body", (0, r * 0.4 * k, -TAU * 2 * r * turns * 0.35, TAU * 2 * turns, 0, 0))
        else:
            wind = _ramp(s, 0.0, 0.3) * (1 - _ramp(s, 0.3, 0.45))
            hitk = _env(s, 0.3, 0.75)
            _add(pose, "Body", (0, 0.05 * height * wind, 0.1 * height * wind - 0.4 * height * hitk, 0.12 * wind - 0.1 * hitk, 0, 0))
            if front:
                _add(pose, front[-1], (0, 0, 0, 0.3 * wind - 0.35 * hitk, 0, 0))
            for b, sg in ants:
                _add(pose, b, (0, 0, 0, -0.3 * hitk, sg * 0.3 * wind, 0))
            legwave(pose, s * 3, 0.8)
        if extra:
            extra(pose, "attack", s, 1.0)
        if not roll:
            _scale(pose, _rec(s, 0.7))
        return pose

    def hit(t):
        s = t / 0.5
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.2 * s)
        pose = {}
        if curl:
            enroll(pose, 0.7 * k)
        _add(pose, "Body", (0, 0.05 * height * k, 0.12 * height * k, 0.1 * k, 0, 0.1 * k * math.sin(s * 12)))
        for b, sg in ants:
            _add(pose, b, (0, 0, 0, -0.4 * k, sg * 0.3 * k, 0))
        if extra:
            extra(pose, "hit", s, k)
        return pose

    H.clip("Move", period, move, keys=20)
    H.clip("Idle", 6.0, idle, keys=30)
    H.clip("Attack", 1.2 if roll else 0.8, attack, keys=24 if roll else 14, loop=False)
    H.clip("Hit", 0.5, hit, keys=10, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})


# ================================================================================================ drifting chains
def drift(H, chain, height=2.0, period=2.4, amp=0.16, axis="yaw", pulses=(), tents=(), bob=0.12, attack="lash", extra=None):
    """Colonial chains / gelatinous floaters: a slow travelling wave down `chain` (yaw = side to side, pitch = up and
    down), pulses: (bone, (dx, dy, dz)) parts that squeeze / jet in sequence (bells, barrels, siphons), tents:
    (bone, side) dangling tentacles that trail."""
    n = max(len(chain), 1)
    ax = 4 if axis == "yaw" else 3

    def wave(pose, u, a):
        for i, b in enumerate(chain):
            v = [0.0] * 6
            v[ax] = a * (0.5 + 0.5 * i / n) * math.sin(TAU * u - i * 0.8)
            v[3 if ax == 4 else 4] += 0.25 * a * math.sin(TAU * u * 0.5 - i * 0.6)
            _add(pose, b, tuple(v))

    def pulse(pose, u, k):
        m = max(len(pulses), 1)
        for i, (b, d) in enumerate(pulses):
            p = max(0.0, math.sin(TAU * (u * 2 - i / m))) ** 2 * k
            _add(pose, b, (d[0] * p, d[1] * p, d[2] * p, 0, 0, 0))

    def trail(pose, u, a):
        for i, (b, sg) in enumerate(tents):
            _add(pose, b, (0, 0, 0, a * 0.25 * math.sin(TAU * u - i * 0.5), 0, sg * a * 0.2 * math.sin(TAU * u * 0.7 + i)))

    def move(t):
        u = t / period
        pose = {}
        wave(pose, u, amp)
        pulse(pose, u, 1.0)
        trail(pose, u, 1.2)
        _add(pose, "Body", (0, bob * height * math.sin(TAU * u), 0, 0.04 * math.sin(TAU * u + 1), 0, 0.03 * math.sin(TAU * u)))
        if extra:
            extra(pose, "move", u, 1.0)
        return pose

    def idle(t):
        u = t / (period * 2)
        pose = {}
        wave(pose, u, amp * 0.55)
        pulse(pose, u, 0.5)
        trail(pose, u, 0.8)
        _add(pose, "Body", (0, bob * 0.8 * height * math.sin(TAU * u), 0, 0.03 * math.sin(TAU * u), 0.06 * math.sin(TAU * u * 0.5), 0.02 * math.sin(TAU * u * 2)))
        if extra:
            extra(pose, "idle", u, 0.5)
        return pose

    def attack_fn(t):
        s = t / 0.9
        pose = {}
        wind = _ramp(s, 0.0, 0.35) * (1 - _ramp(s, 0.35, 0.5))
        hitk = _env(s, 0.35, 0.8)
        for i, b in enumerate(chain):
            v = [0.0] * 6
            v[ax] = (0.45 * wind - 0.6 * hitk) * (0.4 + 0.6 * i / n)
            _add(pose, b, tuple(v))
        pulse(pose, s * 2, 2.0 * hitk)
        for i, (b, sg) in enumerate(tents):
            _add(pose, b, (0, 0, 0, -0.6 * hitk, 0, sg * 0.3 * wind))
        _add(pose, "Body", (0, 0.1 * height * wind, 0.1 * height * wind - 0.3 * height * hitk, 0.1 * wind - 0.1 * hitk, 0, 0))
        if extra:
            extra(pose, "attack", s, hitk)
        _scale(pose, _rec(s, 0.7))
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        for i, b in enumerate(chain):
            v = [0.0] * 6
            v[ax] = 0.3 * k * (1 if i % 2 == 0 else -0.7)
            _add(pose, b, tuple(v))
        _add(pose, "Body", (0, 0.05 * height * k, 0.12 * height * k, 0.12 * k, 0, 0.1 * k))
        if extra:
            extra(pose, "hit", s, k)
        return pose

    H.clip("Move", period, move, keys=20)
    H.clip("Idle", period * 2, idle, keys=24)
    H.clip("Attack", 0.9, attack_fn, keys=14, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"swimAuthored": True, "height": height})


# ================================================================================================ sessile tubes
def sessile(H, stalks=(), crowns=(), retract=(), height=2.0, period=1.4, attack="retract", hop=0.0, extra=None):
    """Tube worms, sea squirts, hydras: stalks = bone chains that sway; crowns = (bone, (ox, oz), k) plume / tentacle
    groups that fan open-closed (rotating outward about the axis perpendicular to their outward direction);
    retract = (bone, depth) plumes that shoot down into their tube on Hit / Attack wind-up. attack: "retract" (plumes
    snap in, then BURST out and whip), "squirt" (body squeezes, siphon jets), "lash" (stalk whips forward)."""

    def sway(pose, u, a):
        for j, chain in enumerate(stalks):
            for i, b in enumerate(chain):
                _add(pose, b, (0, 0, 0, a * 0.6 * math.sin(TAU * u - i * 0.7 + j * 1.1), 0, a * math.sin(TAU * u * 0.5 - i * 0.6 + j * 2.0)))

    def fan(pose, u, a, base=0.0):
        for j, (b, (ox, oz), k) in enumerate(crowns):
            w = base + a * math.sin(TAU * u - j * 0.45)
            _add(pose, b, (0, 0, 0, -w * oz * k, 0, w * ox * k))

    def move(t):
        u = t / period
        pose = {}
        sway(pose, u, 0.1)
        fan(pose, u * 2, 0.12)
        if hop:
            _add(pose, "Body", (0, hop * height * abs(math.sin(TAU * u)), 0, 0, 0, 0.05 * math.sin(TAU * u)))
        else:
            _add(pose, "Body", (0, 0.02 * height * abs(math.sin(TAU * u)), 0, 0.03 * math.sin(TAU * u), 0, 0.04 * math.sin(TAU * u)))
        if extra:
            extra(pose, "move", u, 1.0)
        return pose

    def idle(t):
        u = t / 4.0
        pose = {}
        sway(pose, u, 0.07)
        fan(pose, u * 2, 0.1)
        # a twitch: one plume group darts in and back out
        tw = _env(u, 0.55, 0.75)
        for i, (b, depth) in enumerate(retract):
            if i % 2 == 0:
                _add(pose, b, (0, -depth * 0.6 * tw, 0, 0, 0, 0))
        if extra:
            extra(pose, "idle", u, tw)
        return pose

    def attack_fn(t):
        s = t / 0.9
        pose = {}
        wind = _ramp(s, 0.0, 0.3) * (1 - _ramp(s, 0.3, 0.42))
        hitk = _env(s, 0.3, 0.8)
        if attack == "retract":
            for b, depth in retract:
                _add(pose, b, (0, -depth * wind + 0.15 * depth * hitk, 0, 0, 0, 0))
            fan(pose, 0, 0, base=0.45 * hitk - 0.4 * wind)
            for chain in stalks:
                for i, b in enumerate(chain):
                    _add(pose, b, (0, 0, 0, -0.2 * hitk * (1 if i else 0.5), 0, 0))
        elif attack == "squirt":
            for chain in stalks:
                for i, b in enumerate(chain):
                    _add(pose, b, (0, -0.05 * height * wind, 0, 0.15 * wind - 0.3 * hitk, 0, 0))
            fan(pose, 0, 0, base=-0.3 * wind + 0.3 * hitk)
        else:  # lash
            for chain in stalks:
                for i, b in enumerate(chain):
                    _add(pose, b, (0, 0, 0, 0.35 * wind - 0.6 * hitk, 0, 0))
            fan(pose, 0, 0, base=0.5 * hitk)
        if extra:
            extra(pose, "attack", s, hitk)
        _scale(pose, _rec(s, 0.7))
        return pose

    def hit(t):
        s = t / 0.5
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.2 * s)
        pose = {}
        for b, depth in retract:
            _add(pose, b, (0, -depth * k, 0, 0, 0, 0))
        fan(pose, 0, 0, base=-0.35 * k)
        for chain in stalks:
            for i, b in enumerate(chain):
                _add(pose, b, (0, 0, 0, 0.15 * k, 0, 0.1 * k * math.sin(s * 12 + i)))
        if extra:
            extra(pose, "hit", s, k)
        return pose

    H.clip("Move", period, move, keys=20)
    H.clip("Idle", 4.0, idle, keys=24)
    H.clip("Attack", 0.9, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.5, hit, keys=10, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})
