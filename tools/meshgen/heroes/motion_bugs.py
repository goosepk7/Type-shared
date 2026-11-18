"""Authored motion cycles for the bugs family (tools/meshgen/heroes/h_bugs.py): insect tripod walking, spider
alternating-tetrapod walking, hopping, fast "buzz" flight with wing flutter, butterfly flapping, segmented crawlers
(centipede metachronal leg wave, caterpillar inch hump, worm slither) and snail glide.

Pose values are (px, py, pz, rx, ry, rz) at a bone pivot in its parent's frame (see motion.py). Signs for a model
facing -Z: a right-side (+X) leg swings FORWARD with +ry and LIFTS with +rz; the left leg mirrors both (-ry, -rz).
+rx on a part that points back (+Z, an abdomen or tail) lowers its tip; +rx on the body pitches the nose up.
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


def _win(s, a, b):
    """0..1..0 bump over s in [a, b]."""
    if s <= a or s >= b:
        return 0.0
    return math.sin(math.pi * (s - a) / (b - a))


def step_cycle(u, duty=0.5):
    """(forward, lift) of a walking leg over u in 0..1: stance sweeps back at constant speed, swing lifts and reaches."""
    u = u % 1.0
    if u < duty:
        s = u / duty
        return 1 - 2 * s, 0.0
    s = (u - duty) / (1 - duty)
    return -1 + 2 * _ease(s), math.sin(math.pi * s)


def _leg_pose(pose, L, f, l, stride, lift):
    sg = L["side"]
    sc = L.get("scale", 1.0)
    _add(pose, L["hip"], (0, 0, 0, 0, sg * f * stride * sc, sg * l * lift))
    _add(pose, L.get("knee"), (0, 0, 0, 0, 0, sg * l * lift * 0.7))
    _add(pose, L.get("foot"), (0, 0, 0, 0, 0, -sg * l * lift * 0.6))


def _common_idle(pose, u, head, abd, ants, ab_amp=0.04):
    br = math.sin(TAU * u * 2)
    _add(pose, "Body", (0, 0.01 * br, 0, 0.01 * br, 0, 0))
    _add(pose, head, (0, 0, 0, 0.05 * math.sin(TAU * u + 1), 0.16 * math.sin(TAU * u) * (0.6 + 0.4 * math.sin(TAU * u * 3)), 0.04 * math.sin(TAU * u + 2)))
    _add(pose, abd, (0, 0, 0, ab_amp * br, 0.03 * math.sin(TAU * u), 0))
    for i, (b, sg) in enumerate(ants):
        tw = math.sin(TAU * (u * 3 + i * 0.27))
        _add(pose, b, (0, 0, 0, 0.18 * tw, sg * 0.15 * math.sin(TAU * (u * 2 + i * 0.4)), sg * 0.08 * tw))


def walker(H, legs, head=None, abd=None, ants=(), mand=(), wings=(), tail=(), period=0.62, stride=0.3, lift=0.32,
           height=1.0, attack="bite", strike=(), extra_move=None):
    """Clips for a walking arthropod.
    legs: dicts {hip, knee, foot, side (+1 right / -1 left), phase (0 / 0.5 tripod / tetrapod groups), scale}.
    ants: (bone, side) antennae; mand: (bone, side) mandibles / fangs / pincers; wings: (bone, side) folded wings
    (tremble on hit); tail: bone chain that curls (scorpion) for attack="tail".
    attack: bite (lunge + mandibles), sting (abdomen curls under), ram (head toss), strike (raptorial `strike`
    arms: list of (hip, knee, foot, side) that snap forward), tail (scorpion tail strike + claws)."""

    def move(t):
        u = t / period
        pose = {}
        for L in legs:
            f, l = step_cycle(u + L["phase"])
            _leg_pose(pose, L, f, l, stride, lift)
        _add(pose, "Body", (0, 0.012 * height * math.cos(TAU * u * 2), 0, 0.012 * math.sin(TAU * u * 2), 0.035 * math.sin(TAU * u), 0.02 * math.sin(TAU * u)))
        _add(pose, head, (0, 0, 0, 0.03 * math.sin(TAU * u * 2 + 0.5), -0.05 * math.sin(TAU * u), 0))
        _add(pose, abd, (0, 0, 0, 0.03 * math.sin(TAU * u * 2 + 1.2), -0.06 * math.sin(TAU * u + 0.6), 0))
        for i, (b, sg) in enumerate(ants):
            _add(pose, b, (0, 0, 0, 0.12 * math.sin(TAU * u * 2 + i * 1.3), sg * 0.12 * math.sin(TAU * u + i), 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.04 * math.sin(TAU * u * 2 - i * 0.6), 0.05 * math.sin(TAU * u - i * 0.5), 0))
        for arm in strike:
            hip, knee, foot, sg = arm
            _add(pose, hip, (0, 0, 0, 0.06 * math.sin(TAU * u * 2), sg * 0.05 * math.sin(TAU * u), 0))
        if extra_move:
            extra_move(pose, u)
        return pose

    def idle(t):
        u = t / 4.0
        pose = {}
        _common_idle(pose, u, head, abd, ants)
        # one leg at a time shifts its footing
        for i, L in enumerate(legs):
            tw = max(0.0, math.sin(TAU * (u * 2 + i / len(legs)))) ** 10
            _add(pose, L["hip"], (0, 0, 0, 0, L["side"] * 0.06 * tw, L["side"] * 0.12 * tw))
        for i, m in enumerate(mand):
            b, sg = m[0], m[1]
            _add(pose, b, (0, 0, 0, 0, -sg * 0.12 * max(0.0, math.sin(TAU * u * 2 + i)) ** 4, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.04 * math.sin(TAU * u * 2 - i * 0.7), 0.06 * math.sin(TAU * u - i * 0.6), 0))
        for arm in strike:
            hip, knee, foot, sg = arm
            _add(pose, hip, (0, 0, 0, 0.04 * math.sin(TAU * u * 2), sg * 0.06 * math.sin(TAU * u * 2 + 0.6), 0))
        return pose

    def attack_fn(t):
        L = 0.8
        s = t / L
        pose = {}
        wind = _ease(s / 0.3) if s < 0.3 else (1 - _ease((s - 0.3) / 0.15) if s < 0.45 else 0.0)
        hitk = _win(s, 0.3, 0.75)
        rec = 1.0 if s < 0.6 else 1 - _ease((s - 0.6) / 0.4)
        if attack == "sting":
            _add(pose, "Body", (0, 0.08 * height * hitk, -0.15 * height * hitk, 0.25 * hitk - 0.08 * wind, 0, 0))
            _add(pose, abd, (0, 0, 0, -0.3 * wind + 1.0 * hitk, 0, 0))
            _add(pose, head, (0, 0, 0, -0.2 * hitk, 0, 0))
        elif attack == "ram":
            _add(pose, "Body", (0, -0.03 * height * wind, 0.12 * height * wind - 0.45 * height * hitk, -0.12 * wind + 0.08 * hitk, 0, 0))
            _add(pose, head, (0, 0, 0, -0.35 * wind + 0.6 * hitk, 0, 0))
        elif attack == "strike":
            _add(pose, "Body", (0, 0.03 * height * hitk, -0.2 * height * hitk, -0.1 * hitk + 0.06 * wind, 0, 0))
            _add(pose, head, (0, 0, 0, -0.15 * hitk, 0, 0))
        elif attack == "tail":
            _add(pose, "Body", (0, 0, -0.12 * height * hitk, 0.05 * hitk, 0, 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0.15 * wind - 0.42 * hitk, 0, 0))
        else:  # bite
            _add(pose, "Body", (0, 0.04 * height * wind, 0.08 * height * wind - 0.4 * height * hitk, 0.14 * wind - 0.12 * hitk, 0, 0))
            _add(pose, head, (0, 0, 0, 0.15 * wind - 0.3 * hitk, 0, 0))
        open_ = wind + 0.3 * hitk
        close = _win(s, 0.38, 0.8)
        for m in mand:
            b, sg = m[0], m[1]
            k = m[2] if len(m) > 2 else 1.0
            _add(pose, b, (0, 0, 0, 0, sg * k * (-0.45 * open_ + 0.7 * close), 0))
        for arm in strike:
            hip, knee, foot, sg = arm
            snap = _win(s, 0.32, 0.7)
            _add(pose, hip, (0, 0, 0, -0.35 * wind + 1.1 * snap, -sg * 0.15 * snap, 0))
            _add(pose, knee, (0, 0, 0, -0.2 * wind + 1.5 * snap, 0, 0))
            _add(pose, foot, (0, 0, 0, 0.6 * snap, 0, 0))
        for b, sg in ants:
            _add(pose, b, (0, 0, 0, -0.3 * wind, sg * 0.2 * hitk, 0))
        for Lg in legs:
            if Lg.get("front") == 1 and attack in ("bite", "tail"):
                # threat display: the front legs rear up and reach forward
                _add(pose, Lg["hip"], (0, 0, 0, 0, Lg["side"] * 0.35 * (wind + hitk), Lg["side"] * 0.7 * (wind + 0.6 * hitk)))
                _add(pose, Lg.get("knee"), (0, 0, 0, 0, 0, Lg["side"] * 0.3 * wind))
            else:
                _add(pose, Lg["hip"], (0, 0, 0, 0, Lg["side"] * 0.1 * hitk * (1 if Lg["phase"] < 0.25 else -1), 0))
        for k, v in list(pose.items()):
            pose[k] = tuple(x * rec for x in v)
        return pose

    def hit(t):
        s = t / 0.4
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, -0.05 * height * k, 0.12 * height * k, 0.12 * k, 0, 0.08 * math.sin(t * 45) * k))
        _add(pose, head, (0, 0, 0, 0.2 * k, 0, 0))
        _add(pose, abd, (0, 0, 0, -0.15 * k, 0, 0))
        for L in legs:
            _add(pose, L["hip"], (0, 0, 0, 0, 0, L["side"] * 0.25 * k))
        for b, sg in ants:
            _add(pose, b, (0, 0, 0, -0.35 * k, sg * 0.3 * k, 0))
        for b, sg in wings:
            _add(pose, b, (0, 0, 0, 0, 0, sg * 0.25 * math.sin(t * 60) * k))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, -0.12 * k, 0, 0))
        return pose

    H.clip("Move", period, move, keys=16)
    H.clip("Idle", 4.0, idle, keys=24)
    H.clip("Attack", 0.8, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.4, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})


def flyer(H, wings, legs=(), head=None, abd=None, ants=(), mand=(), height=1.0, flaps=7, period=0.5, amp=0.9,
          hover_idle=True, attack="sting", slow=False, sweep=0.15, rest=0.0):
    """Clips for a flying insect (gait "buzz").
    wings: (bone, side, phase, amp scale): each flaps about its root (rz, + raises a right wing) with a little sweep (ry).
    flaps: wing beats per Move cycle (fast buzz; use few with slow=True for butterflies). rest: wing raise offset."""

    def wingpose(pose, u, n, a):
        for b, sg, ph, sc in wings:
            w = math.cos(TAU * (u * n + ph))
            _add(pose, b, (0, 0, 0, 0, sg * sweep * a * sc * math.sin(TAU * (u * n + ph)), sg * (rest + a * amp * sc * w)))

    def legs_tuck(pose, k):
        for L in legs:
            front = L.get("front", 0)
            _add(pose, L["hip"], (0, 0, 0, 0, L["side"] * (-0.25 if front <= 0 else 0.15) * k, -L["side"] * 0.3 * k))
            _add(pose, L.get("knee"), (0, 0, 0, 0, 0, -L["side"] * 0.35 * k))

    def move(t):
        u = t / period
        pose = {}
        wingpose(pose, u, flaps, 1.0)
        legs_tuck(pose, 1.0)
        bob = math.sin(TAU * u * (1 if slow else 2))
        _add(pose, "Body", (0, 0.06 * height * bob, 0, -0.12 + 0.02 * bob, 0.03 * math.sin(TAU * u), 0.04 * math.sin(TAU * u)))
        _add(pose, abd, (0, 0, 0, 0.06 * math.sin(TAU * u * 2 + 1), 0, 0))
        _add(pose, head, (0, 0, 0, 0.03 * math.sin(TAU * u * 2), 0, 0))
        for i, (b, sg) in enumerate(ants):
            _add(pose, b, (0, 0, 0, -0.15 + 0.06 * math.sin(TAU * u * 2 + i), 0, 0))
        return pose

    def idle(t):
        u = t / 2.0
        pose = {}
        if hover_idle:
            wingpose(pose, u, flaps * 4 if not slow else 3, 0.85)
            legs_tuck(pose, 0.6)
            _add(pose, "Body", (0.04 * height * math.sin(TAU * u), 0.05 * height * math.sin(TAU * u * 2), 0, 0.03 * math.sin(TAU * u), 0.06 * math.sin(TAU * u), 0))
        else:
            for b, sg, ph, sc in wings:
                w = _ease(abs(math.sin(TAU * u)))
                _add(pose, b, (0, 0, 0, 0, 0, sg * (rest + 0.35 * amp * sc * (w - 0.5))))
        _add(pose, head, (0, 0, 0, 0.05 * math.sin(TAU * u + 1), 0.15 * math.sin(TAU * u), 0))
        _add(pose, abd, (0, 0, 0, 0.05 * math.sin(TAU * u * 2), 0, 0))
        for i, (b, sg) in enumerate(ants):
            _add(pose, b, (0, 0, 0, 0.12 * math.sin(TAU * (u * 2 + i * 0.3)), sg * 0.1 * math.sin(TAU * u), 0))
        return pose

    def attack_fn(t):
        L = 0.7
        s = t / L
        pose = {}
        wind = _ease(s / 0.3) if s < 0.3 else (1 - _ease((s - 0.3) / 0.15) if s < 0.45 else 0.0)
        hitk = _win(s, 0.28, 0.72)
        rec = 1.0 if s < 0.6 else 1 - _ease((s - 0.6) / 0.4)
        u = s * L / period
        wingpose(pose, u, flaps, 1.0)
        legs_tuck(pose, 1.0)
        if attack == "sting":
            _add(pose, "Body", (0, 0.12 * height * wind - 0.15 * height * hitk, -0.4 * height * hitk, 0.1 * wind + 0.3 * hitk, 0, 0))
            _add(pose, abd, (0, 0, 0, -0.35 * wind + 1.1 * hitk, 0, 0))
        else:  # dive / bite / poke
            _add(pose, "Body", (0, 0.1 * height * wind - 0.2 * height * hitk, -0.5 * height * hitk, 0.12 * wind - 0.35 * hitk, 0, 0))
            _add(pose, head, (0, 0, 0, -0.25 * hitk, 0, 0))
        for b, sg in mand:
            _add(pose, b, (0, 0, 0, 0, sg * (-0.4 * wind + 0.6 * hitk), 0))
        for k, v in list(pose.items()):
            if k in [w[0] for w in wings]:
                continue
            pose[k] = tuple(x * rec for x in v)
        return pose

    def hit(t):
        s = t / 0.4
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        wingpose(pose, s * 0.4 / period, flaps, 0.6)
        legs_tuck(pose, 1.0 - 0.6 * k)
        _add(pose, "Body", (0, -0.12 * height * k, 0.15 * height * k, 0.25 * k, 0, 0.3 * k * math.sin(t * 30)))
        _add(pose, head, (0, 0, 0, 0.2 * k, 0, 0))
        _add(pose, abd, (0, 0, 0, -0.2 * k, 0, 0))
        return pose

    H.clip("Move", period, move, keys=max(16, flaps * 4 if not slow else 16))
    H.clip("Idle", 2.0, idle, keys=max(24, (flaps * 4 if not slow else 3) * 4) if hover_idle else 24)
    H.clip("Attack", 0.7, attack_fn, keys=max(16, int(flaps * 0.7 / period * 4)), loop=False)
    H.clip("Hit", 0.4, hit, keys=12, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})


def hopper(H, legs, jump, head=None, abd=None, ants=(), mand=(), wings=(), height=1.0, period=0.9, hop_h=0.9, hop_z=1.2, attack="kick"):
    """Hopping insect (grasshopper, cricket, flea): crouch, the jump legs (hip, knee, foot, side) kick straight, the body
    arcs up and lands. Small legs (dicts like walker) tuck in the air."""

    def jumpk(s):
        # crouch 0-0.2, launch 0.2-0.35, air 0.35-0.8, land 0.8-1
        crouch = _win(s, 0.0, 0.32) if s < 0.16 else (_win(s, 0.0, 0.32) if s < 0.2 else 0.0)
        crouch = _ease(s / 0.18) if s < 0.18 else (1 - _ease((s - 0.18) / 0.08) if s < 0.26 else 0.0)
        land = _win(s, 0.8, 1.0)
        ext = _win(s, 0.18, 0.55)
        air = _win(s, 0.2, 0.86)
        return crouch, ext, air, land

    def move(t):
        s = (t / period) % 1.0
        crouch, ext, air, land = jumpk(s)
        pose = {}
        _add(pose, "Body", (0, hop_h * height * air ** 1.2 - 0.08 * height * (crouch + land), 0, 0.22 * ext - 0.12 * max(0, s - 0.55) * air * 2 - 0.05 * land, 0, 0))
        for hip, knee, foot, sg in jump:
            _add(pose, hip, (0, 0, 0, -0.35 * crouch + 0.55 * ext - 0.1 * land, 0, 0))
            _add(pose, knee, (0, 0, 0, 0.45 * crouch - 1.5 * ext + 0.3 * land, 0, 0))
            _add(pose, foot, (0, 0, 0, 0.6 * ext, 0, 0))
        for L in legs:
            _add(pose, L["hip"], (0, 0, 0, 0, L["side"] * (0.2 if L["phase"] < 0.25 else -0.2) * air, -L["side"] * 0.2 * air))
            _add(pose, L.get("knee"), (0, 0, 0, 0, 0, L["side"] * 0.15 * land))
        _add(pose, head, (0, 0, 0, -0.08 * ext + 0.06 * land, 0, 0))
        _add(pose, abd, (0, 0, 0, -0.1 * ext + 0.12 * land, 0, 0))
        for i, (b, sg) in enumerate(ants):
            _add(pose, b, (0, 0, 0, -0.35 * air + 0.2 * land, sg * 0.1 * air, 0))
        for b, sg in wings:
            _add(pose, b, (0, 0, 0, 0, 0, sg * 0.12 * air))
        return pose

    def idle(t):
        u = t / 4.0
        pose = {}
        _common_idle(pose, u, head, abd, ants, ab_amp=0.06)
        # leg rub (stridulation) on a hind leg
        rub = max(0.0, math.sin(TAU * u)) ** 2
        if jump:
            hip, knee, foot, sg = jump[0]
            _add(pose, hip, (0, 0, 0, 0.12 * rub * math.sin(TAU * u * 12), 0, sg * 0.08 * rub))
        return pose

    def attack_fn(t):
        L = 0.7
        s = t / L
        pose = {}
        wind = _ease(s / 0.3) if s < 0.3 else (1 - _ease((s - 0.3) / 0.12) if s < 0.42 else 0.0)
        kick = _win(s, 0.3, 0.7)
        rec = 1.0 if s < 0.6 else 1 - _ease((s - 0.6) / 0.4)
        if attack == "kick":
            _add(pose, "Body", (0, -0.05 * height * wind, 0.08 * height * wind - 0.25 * height * kick, -0.1 * wind - 0.15 * kick, 0, 0))
            for hip, knee, foot, sg in jump:
                _add(pose, hip, (0, 0, 0, -0.3 * wind + 0.5 * kick, 0, 0))
                _add(pose, knee, (0, 0, 0, 0.4 * wind - 1.6 * kick, 0, 0))
            for b, sg in mand:
                _add(pose, b, (0, 0, 0, 0, sg * (-0.4 * wind + 0.6 * kick), 0))
            _add(pose, head, (0, 0, 0, -0.25 * kick, 0, 0))
        for k, v in list(pose.items()):
            pose[k] = tuple(x * rec for x in v)
        return pose

    def hit(t):
        s = t / 0.4
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0.05 * height * k, 0.15 * height * k, 0.15 * k, 0, 0.1 * math.sin(t * 45) * k))
        _add(pose, head, (0, 0, 0, 0.2 * k, 0, 0))
        for b, sg in ants:
            _add(pose, b, (0, 0, 0, -0.3 * k, sg * 0.3 * k, 0))
        for hip, knee, foot, sg in jump:
            _add(pose, knee, (0, 0, 0, -0.4 * k, 0, 0))
        return pose

    H.clip("Move", period, move, keys=20)
    H.clip("Idle", 4.0, idle, keys=32)
    H.clip("Attack", 0.7, attack_fn, keys=14, loop=False)
    H.clip("Hit", 0.4, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})


def crawler(H, segs, legpairs=(), head=None, ants=(), mand=(), mode="wave", period=1.0, height=0.6, amp=0.22, leg_amp=0.4,
            waves=1.0, attack="bite", tailseg=None):
    """Segmented crawlers. segs: chain of bones head->tail (each parented to the previous).
    mode: "wave" (centipede/millipede: lateral S-wave + metachronal leg-pair wave; legpairs are bones whose single
    piece holds a left+right leg pair, they swing about Y), "inch" (caterpillar: a vertical hump travels from tail to
    head), "slither" (worm: lateral wave, small vertical ripple)."""
    n = len(segs)

    def move(t):
        u = t / period
        pose = {}
        if mode == "inch":
            # a hump rolls from the tail to the head; the body inches forward
            for i, b in enumerate(segs):
                ph = TAU * (u + i / n * 0.9)
                if i == 0:
                    continue
                _add(pose, b, (0, 0, 0, amp * math.sin(ph) * (1 if i < n else 0), 0.02 * math.sin(TAU * u), 0))
            _add(pose, segs[0], (0, 0, 0, 0.6 * amp * math.sin(TAU * u + 0.5), 0.05 * math.sin(TAU * u), 0))
            _add(pose, "Body", (0, 0.04 * height * (0.5 + 0.5 * math.sin(TAU * u)), 0, 0, 0, 0))
        else:
            for i, b in enumerate(segs):
                ph = TAU * (u - waves * i / n)
                a = amp * (0.6 if i == 0 else 1.0)
                _add(pose, b, (0, 0, 0, (0.03 if mode == "slither" else 0.0) * math.sin(ph * 2), a * math.sin(ph) * (0.35 if i == 0 else 1.0), 0))
            _add(pose, "Body", (0, 0, 0, 0, amp * 0.6 * math.sin(TAU * u + 0.8), 0))
        for i, b in enumerate(legpairs):
            ph = TAU * (u * 2 + i * 0.18)
            _add(pose, b, (0, 0, 0, 0.12 * max(0.0, math.cos(ph)), leg_amp * math.sin(ph), 0.12 * math.cos(ph)))
        for i, (b, sg) in enumerate(ants):
            _add(pose, b, (0, 0, 0, 0.15 * math.sin(TAU * u * 2 + i), sg * 0.15 * math.sin(TAU * u + i), 0))
        return pose

    def idle(t):
        u = t / 4.0
        pose = {}
        for i, b in enumerate(segs):
            ph = TAU * (u - i / n)
            _add(pose, b, (0, 0, 0, 0.02 * math.sin(ph * 2), 0.06 * math.sin(ph), 0))
        _add(pose, segs[0], (0, 0, 0, 0.1 + 0.12 * math.sin(TAU * u), 0.2 * math.sin(TAU * u * 0.5 + 1), 0))
        _add(pose, head, (0, 0, 0, 0.08 * math.sin(TAU * u * 2), 0.15 * math.sin(TAU * u), 0))
        for i, b in enumerate(legpairs):
            ph = TAU * (u * 4 + i * 0.18)
            _add(pose, b, (0, 0, 0, 0, 0.08 * math.sin(ph), 0))
        for i, (b, sg) in enumerate(ants):
            _add(pose, b, (0, 0, 0, 0.18 * math.sin(TAU * (u * 3 + i * 0.3)), sg * 0.15 * math.sin(TAU * u * 2 + i), 0))
        return pose

    def attack_fn(t):
        L = 0.8
        s = t / L
        pose = {}
        wind = _ease(s / 0.3) if s < 0.3 else (1 - _ease((s - 0.3) / 0.15) if s < 0.45 else 0.0)
        hitk = _win(s, 0.3, 0.75)
        rec = 1.0 if s < 0.6 else 1 - _ease((s - 0.6) / 0.4)
        k = min(3, n)
        if attack == "rear":  # rear up and slam the front down (caterpillar head butt / worm lash)
            for i, b in enumerate(segs[:k + 1]):
                _add(pose, b, (0, 0, 0, (0.45 * wind - 0.55 * hitk) * (1.0 if i < k else 0.5), 0, 0))
        else:  # rear back then strike forward and bite
            _add(pose, "Body", (0, 0, 0.1 * height * wind - 0.5 * height * hitk, 0, 0, 0))
            for i, b in enumerate(segs[:k]):
                _add(pose, b, (0, 0, 0, 0.3 * wind - 0.25 * hitk, 0.2 * wind * (1 if i % 2 == 0 else -1), 0))
        _add(pose, head, (0, 0, 0, -0.2 * hitk, 0, 0))
        for b, sg in mand:
            _add(pose, b, (0, 0, 0, 0, sg * (-0.5 * wind + 0.7 * hitk), 0))
        if tailseg:
            _add(pose, tailseg, (0, 0, 0, -0.4 * hitk, 0, 0))
        for kk, v in list(pose.items()):
            pose[kk] = tuple(x * rec for x in v)
        return pose

    def hit(t):
        s = t / 0.4
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0, 0.12 * height * k, 0, 0, 0))
        for i, b in enumerate(segs):
            _add(pose, b, (0, 0, 0, 0.15 * k * (1 if i < 2 else 0.3), 0.2 * k * math.sin(i * 1.3), 0))
        for b, sg in ants:
            _add(pose, b, (0, 0, 0, -0.3 * k, sg * 0.3 * k, 0))
        return pose

    H.clip("Move", period, move, keys=20)
    H.clip("Idle", 4.0, idle, keys=24)
    H.clip("Attack", 0.8, attack_fn, keys=14, loop=False)
    H.clip("Hit", 0.4, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})


def glider(H, foot, head=None, stalks=(), shell=None, height=1.0, period=1.6):
    """Snail / slug: the foot ripples (a small vertical wave along its chain), the head sways, eye stalks wave; the
    attack is a lunge with the stalks pulled in; hit retracts into the shell."""
    n = len(foot)

    def move(t):
        u = t / period
        pose = {}
        for i, b in enumerate(foot):
            _add(pose, b, (0, 0, 0, 0.05 * math.sin(TAU * (u * 2 - i / max(n, 1))), 0.04 * math.sin(TAU * u - i * 0.6), 0))
        _add(pose, "Body", (0, 0.01 * height * math.sin(TAU * u * 2), 0, 0, 0.03 * math.sin(TAU * u), 0))
        _add(pose, head, (0, 0.02 * height * math.sin(TAU * u * 2), 0, 0.04 * math.sin(TAU * u * 2), 0.1 * math.sin(TAU * u), 0))
        _add(pose, shell, (0, 0.015 * height * math.sin(TAU * u * 2 + 1), 0, 0.02 * math.sin(TAU * u * 2 + 1), 0, 0.03 * math.sin(TAU * u)))
        for i, (b, sg) in enumerate(stalks):
            _add(pose, b, (0, 0, 0, 0.15 * math.sin(TAU * u + i * 1.5), 0, sg * 0.12 * math.sin(TAU * u * 2 + i)))
        return pose

    def idle(t):
        u = t / 4.0
        pose = {}
        _add(pose, head, (0, 0, 0, 0.06 * math.sin(TAU * u), 0.2 * math.sin(TAU * u), 0))
        _add(pose, shell, (0, 0.01 * height * math.sin(TAU * u * 2), 0, 0.015 * math.sin(TAU * u * 2), 0, 0))
        for i, b in enumerate(foot):
            _add(pose, b, (0, 0, 0, 0.02 * math.sin(TAU * (u * 2 - i / max(n, 1))), 0, 0))
        for i, (b, sg) in enumerate(stalks):
            _add(pose, b, (0, 0, 0, 0.25 * math.sin(TAU * (u * 2 + i * 0.4)), 0, sg * 0.2 * math.sin(TAU * u * 3 + i)))
        return pose

    def attack_fn(t):
        L = 0.9
        s = t / L
        pose = {}
        wind = _ease(s / 0.35) if s < 0.35 else (1 - _ease((s - 0.35) / 0.15) if s < 0.5 else 0.0)
        hitk = _win(s, 0.35, 0.8)
        rec = 1.0 if s < 0.65 else 1 - _ease((s - 0.65) / 0.35)
        _add(pose, head, (0, 0.15 * height * wind, 0.1 * height * wind - 0.4 * height * hitk, 0.35 * wind - 0.4 * hitk, 0, 0))
        _add(pose, "Body", (0, 0, -0.15 * height * hitk, 0, 0, 0))
        _add(pose, shell, (0, 0, 0, -0.1 * wind + 0.12 * hitk, 0, 0))
        for b, sg in stalks:
            _add(pose, b, (0, 0, 0, -0.5 * hitk, 0, 0))
        for kk, v in list(pose.items()):
            pose[kk] = tuple(x * rec for x in v)
        return pose

    def hit(t):
        s = t / 0.4
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, head, (0, -0.1 * height * k, 0.25 * height * k, -0.3 * k, 0, 0))
        _add(pose, shell, (0, -0.03 * height * k, 0.05 * height * k, 0.1 * k, 0, 0.1 * math.sin(t * 40) * k))
        for b, sg in stalks:
            _add(pose, b, (0, 0, 0, -0.8 * k, 0, 0))
        return pose

    H.clip("Move", period, move, keys=20)
    H.clip("Idle", 4.0, idle, keys=24)
    H.clip("Attack", 0.9, attack_fn, keys=14, loop=False)
    H.clip("Hit", 0.4, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})
