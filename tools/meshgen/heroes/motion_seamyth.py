"""Motion cycles for the seamyth family (h_seamyth.py): krakens and tentacle monsters (writhing arm crawl + tentacle
slam), serpent-tailed folk (lamia / naga style: ground wave down the tail, swaying torso, arms), giant worms
(burrow-rise strike), flying cloth strips, and small helpers.

Pose values are (px, py, pz, rx, ry, rz) at each bone pivot in its parent's frame (see motion.py). For an arm whose
rest direction is the horizontal unit vector d = (dx, 0, dz), a LIFT by angle a is the rotation (rx, rz) = (-dz a, dx a)
(the tip rises), and a sweep is ry.
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


def bump(s, a, b):
    if s <= a or s >= b:
        return 0.0
    return math.sin(math.pi * (s - a) / (b - a))


def lift(pose, bone, d, a, sweep=0.0):
    dx, dz = d
    _add(pose, bone, (0, 0, 0, -dz * a, sweep, dx * a))


def _scale(pose, k):
    for b, v in list(pose.items()):
        pose[b] = tuple(x * k for x in v)


# ================================================================================================ cephalopods
def writhe(H, arms, slammers=(), head=None, mantle=(), height=3.0, walk=1.6, idle=4.0, extra=None, slam_k=1.0):
    """Kraken crawl. arms: list of (bones root->tip, (dx, dz) rest direction). Each arm writhes with a travelling
    curl; in Move the arms work in two alternating groups (reach forward lifted, then drag back flat) while the head
    surges and the mantle sways. slammers: arms (same format) that rear up over the body and slam down in Attack."""

    def curls(pose, u, a, k_sweep=0.0, k_reach=0.0):
        for j, (chain, d) in enumerate(arms):
            grp = j % 2
            ph = j * 0.83
            reach = math.sin(TAU * u + grp * math.pi)
            sgn = 1.0 if d[0] >= 0 else -1.0
            for i, b in enumerate(chain):
                w = math.sin(TAU * u * (1 if i else 1) - 1.3 * i + ph)
                la = a * (0.3 + 0.4 * i) * w
                if i == 0:
                    la += k_reach * 0.22 * max(0.0, reach)
                sw = k_sweep * 0.18 * reach * sgn * (1 if i == 0 else 0.4) + 0.08 * a * math.sin(TAU * u - i + ph * 1.3)
                lift(pose, b, d, la, sw)

    def slam_idle(pose, u, a):
        for j, (chain, d) in enumerate(slammers):
            for i, b in enumerate(chain):
                lift(pose, b, d, a * (0.25 + 0.2 * i) * math.sin(TAU * u - 1.1 * i + j * 1.7),
                     0.12 * a * math.sin(TAU * u * 0.5 - i + j))

    def move(t):
        u = t / walk
        pose = {}
        curls(pose, u, 0.22, 1.0, 1.0)
        slam_idle(pose, u, 0.5)
        _add(pose, "Body", (0, 0.05 * height * math.sin(TAU * u * 2 - 0.6), -0.04 * height * math.sin(TAU * u * 2),
                            0.04 * math.sin(TAU * u * 2), 0.03 * math.sin(TAU * u), 0.03 * math.sin(TAU * u)))
        for i, b in enumerate(mantle):
            _add(pose, b, (0, 0, 0, 0.06 * math.sin(TAU * u * 2 - 1 - i * 0.8), 0.07 * math.sin(TAU * u - i * 0.7), 0))
        _add(pose, head, (0, 0, 0, -0.03 * math.sin(TAU * u * 2), 0, 0))
        if extra:
            extra(pose, "move", u, 0.0)
        return pose

    def idle_fn(t):
        u = t / idle
        pose = {}
        curls(pose, u, 0.16)
        slam_idle(pose, u, 0.6)
        _add(pose, "Body", (0, 0.025 * height * math.sin(TAU * u * 2), 0, 0.02 * math.sin(TAU * u * 2), 0.04 * math.sin(TAU * u), 0))
        for i, b in enumerate(mantle):
            _add(pose, b, (0, 0, 0, 0.05 * math.sin(TAU * u * 2 - 1 - i), 0.06 * math.sin(TAU * u - i), 0))
        if extra:
            extra(pose, "idle", u, 0.0)
        return pose

    AL = 1.1

    def attack(t):
        s = t / AL
        pose = {}
        wind = ease(s / 0.4) * (1 - ease((s - 0.4) / 0.14))
        slam = ease((s - 0.4) / 0.14) * (1 - ease((s - 0.72) / 0.28))
        whip = bump(s, 0.38, 0.62)
        for j, (chain, d) in enumerate(slammers):
            for i, b in enumerate(chain):
                k = (1.0, 0.55, 0.45, 0.35)[min(i, 3)] * slam_k
                lift(pose, b, d, k * (1.15 * wind - 1.0 * slam) + (0.5 if i else 0.0) * whip * (1 if i % 2 else -0.6) * slam_k)
        for j, (chain, d) in enumerate(arms):
            for i, b in enumerate(chain):
                brace = -0.12 * (wind + slam) if i == 0 else 0.25 * wind - 0.1 * slam
                lift(pose, b, d, brace + 0.15 * whip * math.sin(j + i))
        _add(pose, "Body", (0, 0.1 * height * wind - 0.06 * height * slam, 0.12 * height * wind - 0.2 * height * slam,
                            0.18 * wind - 0.16 * slam, 0, 0))
        for i, b in enumerate(mantle):
            _add(pose, b, (0, 0, 0, -0.12 * wind + 0.15 * slam, 0, 0))
        _add(pose, head, (0, 0, 0, -0.1 * slam, 0, 0))
        if extra:
            extra(pose, "attack", s, slam)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, -0.04 * height * k, 0.1 * height * k, 0.12 * k, 0, 0.06 * k * math.sin(s * 12)))
        for chain, d in list(arms) + list(slammers):
            for i, b in enumerate(chain):
                lift(pose, b, d, 0.35 * k * (1 if i else 0.5))
        for i, b in enumerate(mantle):
            _add(pose, b, (0, 0, 0, 0.15 * k, 0, 0))
        if extra:
            extra(pose, "hit", s, k)
        return pose

    H.clip("Move", walk, move, keys=24)
    H.clip("Idle", idle, idle_fn, keys=24)
    H.clip("Attack", AL, attack, keys=18, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})


# ================================================================================================ serpent folk
def serpfolk(H, tail, arms=(), spine=None, head=None, jaw=None, hair=(), wings=(), height=5.0, walk=1.4, amp=0.3,
             attack="claw", swim=False, extra=None):
    """Human torso on a snake (or fish) tail. tail: bones from the hips down to the tip (the first one or two stand
    upright, the rest lie on the ground). Move: a lateral wave travels down the tail (relative yaws, so the S keeps its
    shape), the torso counter-sways and the arms balance. swim=True uses an up-down dolphin kick instead.
    Attack "claw": rear up on the tail, then lunge down with both clawed hands; "whip": the tail lashes round."""
    n = len(tail)

    def wave(pose, u, a):
        prev = 0.0
        for i, b in enumerate(tail):
            env = min(1.0, 0.25 + 0.3 * i)
            if swim:
                _add(pose, b, (0, 0, 0, a * env * 0.6 * math.sin(TAU * u - 0.9 * i), 0.04 * math.sin(TAU * u * 0.5 - i), 0))
                continue
            th = a * env * math.cos(TAU * u - 1.15 * i)
            _add(pose, b, (0, 0, 0, 0, (th - prev) if i else th * 0.4, 0))
            prev = th

    def armpose(pose, u, k=1.0):
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            ph = 0 if side > 0 else math.pi
            _add(pose, sh, (0, 0, 0, k * (0.15 + 0.18 * math.sin(TAU * u + ph)), 0, sg * k * (0.32 + 0.06 * math.sin(TAU * u * 2))))
            _add(pose, el, (0, 0, 0, k * (0.45 + 0.12 * math.sin(TAU * u + ph + 0.6)), 0, 0))

    def wingpose(pose, u, a):
        for root, tip, side in wings:
            sg = 1 if side > 0 else -1
            _add(pose, root, (0, 0, 0, 0, 0, sg * a * math.sin(TAU * u)))
            if tip:
                _add(pose, tip, (0, 0, 0, 0, 0, sg * a * 0.6 * math.sin(TAU * u - 0.9)))

    def hairpose(pose, u, a):
        for i, b in enumerate(hair):
            _add(pose, b, (0, 0, 0, a * math.sin(TAU * u - 1 - 0.7 * i), 0, 0.5 * a * math.sin(TAU * u * 0.5 - i)))

    def move(t):
        u = t / walk
        pose = {}
        wave(pose, u, amp)
        armpose(pose, u)
        wingpose(pose, u * 2, 0.25)
        hairpose(pose, u, 0.1)
        _add(pose, "Body", (0, 0.02 * height * math.sin(TAU * u * 2), 0, 0.03 * math.sin(TAU * u * 2) + (-0.25 if swim else 0.0), 0,
                            0.03 * math.sin(TAU * u)))
        _add(pose, spine, (0, 0, 0, 0.03 * math.sin(TAU * u * 2 + 0.5) + (0.12 if swim else 0.0), -0.12 * math.sin(TAU * u), 0.04 * math.sin(TAU * u + 0.7)))
        _add(pose, head, (0, 0, 0, 0.02 * math.sin(TAU * u * 2) + (0.12 if swim else 0.0), 0.1 * math.sin(TAU * u), 0))
        if extra:
            extra(pose, "move", u, 0.0)
        return pose

    def idle(t):
        u = t / 4.0
        pose = {}
        wave(pose, u, amp * 0.3)
        armpose(pose, u, 0.8)
        wingpose(pose, u, 0.08)
        hairpose(pose, u, 0.06)
        _add(pose, "Body", (0, 0.015 * height * math.sin(TAU * u * 2), 0, 0, 0.05 * math.sin(TAU * u), 0.025 * math.sin(TAU * u)))
        _add(pose, spine, (0, 0, 0, 0.015 * math.sin(TAU * u * 2), -0.06 * math.sin(TAU * u), 0.03 * math.sin(TAU * u + 1)))
        _add(pose, head, (0, 0, 0, 0.03 * math.sin(TAU * u * 2 + 1), 0.2 * math.sin(TAU * u), 0))
        if extra:
            extra(pose, "idle", u, 0.0)
        return pose

    AL = 0.95

    def atk(t):
        s = t / AL
        pose = {}
        wind = ease(s / 0.38) * (1 - ease((s - 0.38) / 0.16))
        strike = bump(s, 0.32, 0.8)
        rec = 1 - ease((s - 0.72) / 0.28)
        if attack == "whip":
            for i, b in enumerate(tail):
                if i < 2:
                    continue
                _add(pose, b, (0, 0, 0, 0, (0.35 * wind - 0.55 * strike) * (1 if i % 2 else 0.8), 0))
            _add(pose, "Body", (0, 0, 0, 0, 0.5 * wind - 0.8 * strike, 0))
            _add(pose, spine, (0, 0, 0, 0, -0.3 * wind + 0.4 * strike, 0))
            for sh, el, hd, side in arms:
                sg = 1 if side > 0 else -1
                _add(pose, sh, (0, 0, 0, 0.4 * strike, 0, sg * (0.6 * wind + 0.3)))
        else:
            _add(pose, "Body", (0, 0.12 * height * wind - 0.04 * height * strike, 0.05 * height * wind - 0.18 * height * strike,
                                0.22 * wind - 0.2 * strike, 0, 0))
            _add(pose, spine, (0, 0, 0, 0.15 * wind - 0.3 * strike, 0, 0))
            if len(tail) > 1:
                _add(pose, tail[0], (0, 0, 0, -0.15 * wind + 0.12 * strike, 0, 0))
            for sh, el, hd, side in arms:
                sg = 1 if side > 0 else -1
                _add(pose, sh, (0, 0, 0, 2.3 * wind + 0.9 * strike, 0, sg * (0.35 * wind + 0.1)))
                _add(pose, el, (0, 0, 0, 0.9 * wind - 0.2 * strike, 0, 0))
            for i, b in enumerate(tail[2:]):
                _add(pose, b, (0, 0, 0, 0, 0.12 * math.sin(TAU * s * 2 - i) * (wind + strike), 0))
        _add(pose, head, (0, 0, 0, 0.1 * wind - 0.15 * strike, 0, 0))
        _add(pose, jaw, (0, 0, 0, -0.4 * strike, 0, 0))
        wingpose(pose, s * 2, 0.4 * (wind + strike))
        hairpose(pose, s * 2, 0.15)
        if extra:
            extra(pose, "attack", s, strike)
        _scale(pose, rec)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0, 0.05 * height * k, 0.12 * k, 0, 0.05 * math.sin(t * 40) * k))
        _add(pose, spine, (0, 0, 0, 0.15 * k, 0, 0))
        _add(pose, head, (0, 0, 0, 0.25 * k, 0, 0))
        for sh, el, hd, side in arms:
            _add(pose, sh, (0, 0, 0, 0.5 * k, 0, (1 if side > 0 else -1) * 0.5 * k))
        for i, b in enumerate(tail[2:]):
            _add(pose, b, (0, 0, 0, 0, 0.12 * k * (1 if i % 2 else -1), 0))
        if extra:
            extra(pose, "hit", s, k)
        return pose

    H.clip("Move", walk, move, keys=24)
    H.clip("Idle", 4.0, idle, keys=24)
    H.clip("Attack", AL, atk, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})


# ================================================================================================ giant worm
def worm(H, chain, petals=(), root=None, height=5.0, walk=2.0, extra=None):
    """Sandworm rising out of its burrow. chain: bones from the ground up to the mouth (root first). petals:
    (bone, (ax, ay, az)) with ax.. the rotation axis that opens the petal outward. root: the bone that sinks / rises
    (the burrow mound stays on Body). Move: the column sways in a travelling S and bobs; Attack: burrow-rise strike
    (sink into the sand, burst up high, then slam the gaping mouth down forward)."""
    n = len(chain)

    def open_(pose, a):
        for b, ax in petals:
            _add(pose, b, (0, 0, 0, ax[0] * a, ax[1] * a, ax[2] * a))

    def sway(pose, u, a, b):
        for i, bn in enumerate(chain):
            k = 0.4 + 0.6 * i / max(n - 1, 1)
            _add(pose, bn, (0, 0, 0, b * k * math.sin(TAU * u - 0.9 * i), a * k * math.sin(TAU * u - 0.8 * i + 0.5), 0.5 * a * k * math.cos(TAU * u - 0.8 * i)))

    def move(t):
        u = t / walk
        pose = {}
        sway(pose, u, 0.16, 0.1)
        _add(pose, root, (0, 0.04 * height * math.sin(TAU * u * 2), 0, 0, 0, 0))
        open_(pose, 0.15 + 0.15 * math.sin(TAU * u * 2))
        return pose

    def idle(t):
        u = t / 4.5
        pose = {}
        sway(pose, u, 0.08, 0.05)
        _add(pose, root, (0, 0.02 * height * math.sin(TAU * u * 2), 0, 0, 0, 0))
        open_(pose, 0.2 * max(0.0, math.sin(TAU * u)) ** 2)
        return pose

    AL = 1.3

    def attack(t):
        s = t / AL
        pose = {}
        sink = bump(s, 0.0, 0.42)
        rise = bump(s, 0.3, 0.75)
        slam = bump(s, 0.55, 0.95)
        _add(pose, root, (0, -0.45 * height * sink + 0.15 * height * rise, 0, 0, 0, 0))
        for i, bn in enumerate(chain):
            k = i / max(n - 1, 1)
            _add(pose, bn, (0, 0, 0, 0.12 * rise * (1 - k) - 0.32 * slam * (0.3 + k), 0, 0.05 * math.sin(TAU * s * 3 + i) * rise))
        open_(pose, 0.9 * bump(s, 0.45, 0.95) - 0.2 * sink)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        for i, bn in enumerate(chain):
            _add(pose, bn, (0, 0, 0, 0.1 * k * (1 if i % 2 else -0.5), 0, 0.06 * k * math.sin(s * 12)))
        _add(pose, root, (0, -0.06 * height * k, 0, 0, 0, 0))
        open_(pose, -0.2 * k)
        return pose

    H.clip("Move", walk, move, keys=20)
    H.clip("Idle", 4.5, idle, keys=20)
    H.clip("Attack", AL, attack, keys=20, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})


# ================================================================================================ flying cloth strip
def ribbon(H, chain, arms=(), height=3.0, walk=1.4):
    """A long cloth strip flying head-first: an up-down wave travels from the head (first bone) to the trailing end,
    with a slower side-to-side flutter. Attack: the head end rears back and lashes forward, the strip coils after it."""
    n = len(chain)

    def wave(pose, u, a, b):
        for i, bn in enumerate(chain):
            k = 0.5 + 0.5 * i / max(n - 1, 1)
            _add(pose, bn, (0, 0, 0, a * k * math.sin(TAU * u - 1.0 * i), b * k * math.sin(TAU * u * 0.5 - 0.7 * i), 0.4 * b * math.sin(TAU * u - i)))

    def arm(pose, u, a):
        for b, side in arms:
            _add(pose, b, (0, 0, 0, a * math.sin(TAU * u), 0, side * a * 0.6 * math.sin(TAU * u + 1)))

    def move(t):
        u = t / walk
        pose = {}
        wave(pose, u, 0.22, 0.12)
        arm(pose, u * 2, 0.4)
        _add(pose, "Body", (0, 0.06 * height * math.sin(TAU * u), 0, 0.04 * math.sin(TAU * u + 1), 0, 0.05 * math.sin(TAU * u * 0.5)))
        return pose

    def idle(t):
        u = t / 3.5
        pose = {}
        wave(pose, u, 0.12, 0.08)
        arm(pose, u * 2, 0.25)
        _add(pose, "Body", (0, 0.05 * height * math.sin(TAU * u), 0, 0, 0.06 * math.sin(TAU * u * 0.5), 0))
        return pose

    def attack(t):
        s = t / 1.0
        pose = {}
        wind = bump(s, 0.0, 0.45)
        lash = bump(s, 0.3, 0.85)
        for i, bn in enumerate(chain):
            k = 1.0 - 0.6 * i / max(n - 1, 1)
            _add(pose, bn, (0, 0, 0, (0.45 * wind - 0.5 * lash) * k, 0, 0.2 * lash * math.sin(TAU * s * 2 - i)))
        _add(pose, "Body", (0, 0.05 * height * wind, 0.1 * height * wind - 0.35 * height * lash, 0, 0, 0))
        arm(pose, s * 3, 0.6 * lash)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        for i, bn in enumerate(chain):
            _add(pose, bn, (0, 0, 0, 0.25 * k * (1 if i % 2 else -1), 0, 0))
        _add(pose, "Body", (0, 0.04 * height * k, 0.1 * height * k, 0.1 * k, 0, 0))
        return pose

    H.clip("Move", walk, move, keys=20)
    H.clip("Idle", 3.5, idle, keys=20)
    H.clip("Attack", 1.0, attack, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})


# ================================================================================================ hippocampus
def hippo(H, legs, tail, neck=None, head=None, fins=(), height=4.0, walk=1.3):
    """Sea-horse mount: the forelegs paddle like a swimming horse (alternate reach / fold), a vertical dolphin kick
    runs down the fish tail, the body stays level for the rider. legs: (upper, lower, foot, phase). Attack: rear up,
    strike with both forehooves and slap the tail."""
    def paddle(pose, u, a):
        for up, lo, ft, ph in legs:
            w = math.sin(TAU * (u + ph))
            fold = max(0.0, math.cos(TAU * (u + ph)))
            _add(pose, up, (0, 0, 0, a * (0.25 + 0.45 * w), 0, 0))
            _add(pose, lo, (0, 0, 0, -a * (0.3 + 1.0 * fold), 0, 0))
            _add(pose, ft, (0, 0, 0, a * 0.6 * fold, 0, 0))

    def kick(pose, u, a):
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, a * (0.5 + 0.25 * i) * math.sin(TAU * u - 0.85 * i), 0.03 * math.sin(TAU * u * 0.5 - i), 0))
        for b, side in fins:
            _add(pose, b, (0, 0, 0, 0.1 * math.sin(TAU * u), 0, side * 0.2 * math.sin(TAU * u * 2)))

    def move(t):
        u = t / walk
        pose = {}
        paddle(pose, u, 1.0)
        kick(pose, u, 0.22)
        _add(pose, "Body", (0, 0.03 * height * math.sin(TAU * u * 2), 0, 0.03 * math.sin(TAU * u), 0, 0))
        _add(pose, neck, (0, 0, 0, -0.06 * math.sin(TAU * u * 2 + 0.6), 0, 0))
        _add(pose, head, (0, 0, 0, 0.05 * math.sin(TAU * u * 2 + 1), 0, 0))
        return pose

    def idle(t):
        u = t / 4.0
        pose = {}
        paddle(pose, u * 2, 0.35)
        kick(pose, u * 2, 0.08)
        _add(pose, "Body", (0, 0.03 * height * math.sin(TAU * u), 0, 0.015 * math.sin(TAU * u), 0, 0))
        _add(pose, neck, (0, 0, 0, 0.03 * math.sin(TAU * u), 0.08 * math.sin(TAU * u * 0.5), 0))
        _add(pose, head, (0, 0, 0, 0.04 * math.sin(TAU * u * 2), 0.15 * math.sin(TAU * u), 0))
        return pose

    def attack(t):
        s = t / 1.0
        pose = {}
        rear = bump(s, 0.0, 0.75)
        strike = bump(s, 0.3, 0.65)
        slap = bump(s, 0.5, 0.95)
        _add(pose, "Body", (0, 0.1 * height * rear, 0.05 * height * rear - 0.1 * height * strike, 0.45 * rear, 0, 0))
        for up, lo, ft, ph in legs:
            _add(pose, up, (0, 0, 0, 0.9 * rear + 0.5 * strike * (1 if ph < 0.25 else 0.6), 0, 0))
            _add(pose, lo, (0, 0, 0, -1.2 * rear + 0.9 * strike, 0, 0))
        _add(pose, neck, (0, 0, 0, -0.25 * rear, 0, 0))
        _add(pose, head, (0, 0, 0, -0.15 * rear, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, -0.35 * rear + 0.55 * slap * (0.6 + 0.2 * i), 0, 0))
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0, 0.06 * height * k, 0.1 * k, 0, 0.05 * math.sin(t * 40) * k))
        _add(pose, neck, (0, 0, 0, 0.2 * k, 0, 0))
        _add(pose, head, (0, 0, 0, 0.15 * k, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.2 * k, 0, 0))
        return pose

    H.clip("Move", walk, move, keys=20)
    H.clip("Idle", 4.0, idle, keys=20)
    H.clip("Attack", 1.0, attack, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})
