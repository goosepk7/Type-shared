"""Authored motion for the canines / smallmammals families: trotting dogs with wagging tails and bouncing ears, heavy
bear walks with a rolling gait, bounding / hopping small mammals, and characterful one-shot attacks (bite lunge with a
head shake, bear rear-and-swipe, rabbit double kick, skunk tail spray, quill bristle, curl-and-roll charge).

Pose values are (px, py, pz, rx, ry, rz) at a bone pivot (see motion.py for sign conventions: +rx on a downward limb
swings it forward, +rx on Body pitches the nose up, -rx on a forward jaw opens it, +ry turns left).
"""
import math

from motion import leg_cycle

TAU = 2 * math.pi


def _add(pose, bone, v):
    if not bone:
        return
    o = list(pose.get(bone, (0.0,) * 6))
    for i, x in enumerate(v):
        o[i] += x
    pose[bone] = tuple(o)


def ease(x):
    return 0.5 - 0.5 * math.cos(math.pi * min(max(x, 0.0), 1.0))


def bump(s, a, b):
    """0 -> 1 -> 0 between a and b (smooth)."""
    if s <= a or s >= b:
        return 0.0
    return math.sin(math.pi * (s - a) / (b - a))


def ramp(s, a, b):
    return ease((s - a) / (b - a)) if b > a else float(s >= a)


def _many(pose, bones, v):
    for b in bones or ():
        _add(pose, b, v)


def quad(H, legs, neck=None, head=None, jaw=None, tail=(), ears=(), height=3.0, gait="trot", stride=0.42, lift=1.0,
         walk=0.9, attack="bite", swipe=None, wag=0.0, floppy=False, heads=(), spine=None, bounce=1.0, sway=1.0,
         extra=None):
    """Clips for a four-legged mammal.
    legs: (upper, lower, foot, front, side) with side +1 right / -1 left.
    gait: "trot" (diagonal pairs), "walk" (lateral 4-beat, heavy roll for bears), "bound" (small mammals: front pair
    then hind pair, back flexing).
    heads: extra (neck, head, jaw) tuples (cerberus) animated with offsets.
    wag: idle tail wag amplitude (dogs ~0.45, wolves 0.1).
    attack: bite | swipe (bear rear + swipe) | kick (rabbit / hoofless back kick) | spray (skunk) | bristle (quills) |
            charge (head-down ram) | pounce.
    extra: optional fn(clip, t, pose) to add family-specific motion (quill rattles, cheek puffs ...)."""
    heads = list(heads) or [(neck, head, jaw)]
    if (neck, head, jaw) not in heads:
        heads.insert(0, (neck, head, jaw))
    allj = [h[2] for h in heads if h[2]]
    alln = [h[0] for h in heads if h[0]]
    allh = [h[1] for h in heads if h[1]]

    def phase_of(front, side):
        if gait == "trot":   # LF + RH together, RF + LH together
            return 0.0 if (front and side < 0) or (not front and side > 0) else 0.5
        if gait == "bound":  # front pair, then hind pair (slight stagger)
            return (0.0 if front else 0.5) + (0.04 if side > 0 else 0.0)
        # lateral walk: LH 0, LF .25, RH .5, RF .75
        return {(False, -1): 0.0, (True, -1): 0.25, (False, 1): 0.5, (True, 1): 0.75}[(front, side)]

    duty = {"trot": 0.56, "bound": 0.5, "walk": 0.64}[gait]
    hind = [l[0] for l in legs if not l[3]]
    hipd = (H.bpos(hind[0]) - H.bpos("Body")) if hind else (0.0, 0.0, 1.0)
    if hind and H.bones[H.bidx[hind[0]]][1] != "Body":  # hip on a spine bone: still measure from Body
        hipd = H.bpos(hind[0]) - H.bpos("Body")

    def move(t):
        u = t / walk
        pose = {}
        for up, lo, ft, front, side in legs:
            a, b, c = leg_cycle(u + phase_of(front, side), stride, lift, front, duty=duty)
            _add(pose, up, (0, 0, 0, a, 0, 0))
            _add(pose, lo, (0, 0, 0, b, 0, 0))
            _add(pose, ft, (0, 0, 0, c, 0, 0))
        if gait == "trot":
            bob = -abs(math.sin(TAU * u)) * 0.03 * height * bounce + 0.015 * height
            _add(pose, "Body", (0, bob, 0, 0.015 * math.sin(TAU * u * 2), 0.02 * math.sin(TAU * u) * sway, 0.03 * math.sin(TAU * u) * sway))
        elif gait == "bound":
            k = math.sin(TAU * u)
            _add(pose, "Body", (0, (0.06 * max(0.0, math.sin(TAU * u - 0.6)) - 0.01) * height * bounce, 0, 0.09 * k, 0, 0))
            if spine:
                _add(pose, spine, (0, 0, 0, -0.18 * k, 0, 0))
        else:  # heavy lateral walk: deep roll and yaw
            _add(pose, "Body", (0, -abs(math.sin(TAU * u * 2)) * 0.02 * height + 0.01 * height, 0, 0.01 * math.sin(TAU * u * 2),
                                0.05 * math.sin(TAU * u) * sway, 0.06 * math.sin(TAU * u + 0.4) * sway))
            if spine:
                _add(pose, spine, (0, 0, 0, 0, -0.06 * math.sin(TAU * u), -0.04 * math.sin(TAU * u)))
        for i, (n, h, j) in enumerate(heads):
            off = i * 0.7
            _add(pose, n, (0, 0, 0, -0.06 * math.sin(TAU * u * 2 + 0.6 + off), 0.03 * math.sin(TAU * u + off) * (1 if i == 0 else 2), 0))
            _add(pose, h, (0, 0, 0, 0.06 * math.sin(TAU * u * 2 + 0.9 + off), -0.04 * math.sin(TAU * u + off), 0))
            if j and wag > 0.2:  # happy dogs pant
                _add(pose, j, (0, 0, 0, -0.08 - 0.05 * math.sin(TAU * u * 2), 0, 0))
        for i, b in enumerate(tail):
            if gait == "bound":
                _add(pose, b, (0, 0, 0, 0.12 * math.sin(TAU * u - 0.8 - i * 0.6), 0.05 * math.sin(TAU * u - i), 0))
            else:
                _add(pose, b, (0, 0, 0, 0.05 * math.sin(TAU * u * 2 - i * 0.7), (0.14 + 0.5 * wag) * math.sin(TAU * u * 2 - i * 0.8), 0))
        for i, b in enumerate(ears):
            if floppy:
                _add(pose, b, (0, 0, 0, 0.18 * math.sin(TAU * u * 2 - 1.4), 0, (1 if i % 2 == 0 else -1) * 0.12 * math.sin(TAU * u * 2 - 1.8)))
            else:
                _add(pose, b, (0, 0, 0, 0.05 * math.sin(TAU * u * 2 - 1.0), 0, 0))
        if extra:
            extra("Move", t, pose)
        return pose

    def idle(t):
        u = t / 4.8
        pose = {}
        br = math.sin(TAU * u * 2)
        _add(pose, "Body", (0, 0.008 * height * br, 0, 0.008 * br, 0, 0))
        for i, (n, h, j) in enumerate(heads):
            off = i * 1.9
            _add(pose, n, (0, 0, 0, 0.04 * math.sin(TAU * u + off) - 0.02, 0.12 * math.sin(TAU * u + 0.5 + off), 0))
            _add(pose, h, (0, 0, 0, 0.05 * math.sin(TAU * u * 2 + 1 + off), 0.22 * math.sin(TAU * u + off) * (0.6 + 0.4 * math.sin(TAU * u * 3)),
                           0.08 * math.sin(TAU * u + 2 + off)))
            if j:
                if wag > 0.2:
                    _add(pose, j, (0, 0, 0, -0.12 - 0.06 * math.sin(TAU * u * 12), 0, 0))  # panting
                else:
                    _add(pose, j, (0, 0, 0, -0.05 * max(0.0, math.sin(TAU * u + off)) ** 4, 0, 0))
        for i, b in enumerate(tail):
            if wag > 0:
                _add(pose, b, (0, 0, 0, 0.03 * math.sin(TAU * u * 3 - i), wag * math.sin(TAU * u * 12 - i * 0.9), 0))
            else:
                _add(pose, b, (0, 0, 0, 0.04 * math.sin(TAU * u * 3 - i), 0.2 * math.sin(TAU * u * 2 - i * 0.8), 0))
        for i, b in enumerate(ears):
            tw = max(0.0, math.sin(TAU * (u * 3 + i * 0.37))) ** 12
            _add(pose, b, (0, 0, 0, -0.3 * tw, 0, (1 if i % 2 == 0 else -1) * 0.18 * tw))
        if extra:
            extra("Idle", t, pose)
        return pose

    AL = 0.95 if attack != "swipe" else 1.25

    def attack_fn(t):
        s = t / AL
        pose = {}
        fronts = [l for l in legs if l[3]]
        hinds = [l for l in legs if not l[3]]
        rec = 1 - ramp(s, 0.7, 1.0)
        if attack == "bite":
            crouch = bump(s, 0.0, 0.45) * (1 if s < 0.3 else 1)
            wind = ramp(s, 0.0, 0.25) * (1 - ramp(s, 0.25, 0.4))
            lunge = ramp(s, 0.25, 0.42) * rec
            snap = ramp(s, 0.25, 0.4) * (1 - ramp(s, 0.45, 0.52))
            shake = bump(s, 0.5, 0.82) * math.sin(TAU * (s - 0.5) * 6)
            _add(pose, "Body", (0, -0.06 * height * wind - 0.02 * height * lunge, 0.06 * height * wind - 0.22 * height * lunge,
                                -0.06 * wind - 0.06 * lunge, 0.08 * shake, 0.05 * shake))
            for up, lo, ft, front, side in legs:
                if front:
                    _add(pose, up, (0, 0, 0, -0.2 * wind + 0.45 * lunge, 0, 0))
                    _add(pose, lo, (0, 0, 0, 0.25 * wind - 0.2 * lunge, 0, 0))
                else:
                    _add(pose, up, (0, 0, 0, 0.35 * wind - 0.45 * lunge, 0, 0))
                    _add(pose, lo, (0, 0, 0, 0.35 * wind, 0, 0))
                    _add(pose, ft, (0, 0, 0, -0.3 * wind + 0.2 * lunge, 0, 0))
            for i, (n, h, j) in enumerate(heads):
                _add(pose, n, (0, 0, 0, 0.25 * wind - 0.3 * lunge, 0, 0))
                _add(pose, h, (0, 0, 0, 0.15 * wind + 0.12 * lunge, 0.3 * shake, 0.25 * shake))
                _add(pose, j, (0, 0, 0, -0.75 * snap - 0.12 * wind, 0, 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0.25 * lunge, 0.15 * shake, 0))
            for b in ears:
                _add(pose, b, (0, 0, 0, 0.35 * (wind + lunge), 0, 0))
        elif attack == "swipe":  # bear: rear up on the hind legs, both paws high, slam a swipe down
            rear = ramp(s, 0.05, 0.4) * (1 - ramp(s, 0.55, 0.75))
            sw = bump(s, 0.38, 0.68)
            slam = ramp(s, 0.5, 0.65) * rec
            th = 0.95 * rear - 0.1 * slam
            dy, dz = hipd[1], hipd[2]  # keep the hips where they are: the bear pivots up over its hind feet
            py = dy - (dy * math.cos(th) - dz * math.sin(th))
            pz = dz - (dy * math.sin(th) + dz * math.cos(th))
            _add(pose, "Body", (0, py + 0.04 * height * rear, pz - 0.12 * height * slam, th, 0.15 * sw, 0.1 * sw))
            for up, lo, ft, front, side in legs:
                if front:
                    lift_ = 1.0 if side > 0 else 0.6
                    _add(pose, up, (0, 0, 0, -0.95 * rear + 1.0 * sw * lift_ + 0.3 * slam, 0, side * 0.35 * rear))
                    _add(pose, lo, (0, 0, 0, -0.6 * rear - 0.4 * sw, 0, 0))
                    _add(pose, ft, (0, 0, 0, 0.5 * rear, 0, 0))
                else:
                    _add(pose, up, (0, 0, 0, -th - 0.15 * rear, 0, 0))
                    _add(pose, lo, (0, 0, 0, 0.3 * rear, 0, 0))
                    _add(pose, ft, (0, 0, 0, -0.15 * rear, 0, 0))
            for (n, h, j) in heads:
                _add(pose, n, (0, 0, 0, -0.55 * rear - 0.15 * slam, 0, 0))
                _add(pose, h, (0, 0, 0, -0.35 * rear + 0.25 * bump(s, 0.1, 0.4), 0, 0))
                _add(pose, j, (0, 0, 0, -0.7 * bump(s, 0.12, 0.45) - 0.4 * slam, 0, 0))
            for b in tail:
                _add(pose, b, (0, 0, 0, -0.3 * rear, 0, 0))
        elif attack == "kick":  # rabbit / kangaroo-like: weight onto the front, both hind feet thrust back
            load = ramp(s, 0.0, 0.25) * (1 - ramp(s, 0.25, 0.4))
            kick = bump(s, 0.3, 0.75)
            _add(pose, "Body", (0, 0.05 * height * kick, -0.05 * height * kick, -0.35 * kick + 0.08 * load, 0, 0))
            for up, lo, ft, front, side in legs:
                if front:
                    _add(pose, up, (0, 0, 0, -0.35 * kick, 0, 0))
                    _add(pose, lo, (0, 0, 0, 0.2 * kick, 0, 0))
                else:
                    _add(pose, up, (0, 0, 0, 0.5 * load - 1.2 * kick, 0, 0))
                    _add(pose, lo, (0, 0, 0, 0.6 * load - 0.5 * kick, 0, 0))
                    _add(pose, ft, (0, 0, 0, -0.5 * load + 0.9 * kick, 0, 0))
            for (n, h, j) in heads:
                _add(pose, n, (0, 0, 0, 0.3 * kick, 0, 0))
                _add(pose, h, (0, 0, 0, 0.2 * kick, 0, 0))
            for b in ears:
                _add(pose, b, (0, 0, 0, 0.5 * kick, 0, 0))
        elif attack == "spray":  # skunk: stamp, swing the rear round and hoist the tail
            stamp = bump(s, 0.0, 0.2) + bump(s, 0.15, 0.32)
            turn = ramp(s, 0.2, 0.45) * rec
            up_ = ramp(s, 0.3, 0.5) * rec
            _add(pose, "Body", (0, 0.04 * height * stamp, 0, 0.1 * stamp - 0.25 * up_, 1.4 * turn, 0))
            for up, lo, ft, front, side in legs:
                if front:
                    _add(pose, up, (0, 0, 0, 0.5 * stamp + 0.3 * up_, 0, 0))
                else:
                    _add(pose, up, (0, 0, 0, -0.35 * up_, 0, 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, -0.5 * up_ + 0.12 * math.sin(TAU * s * 5 - i) * up_, 0.1 * math.sin(TAU * s * 4 - i) * up_, 0))
            for (n, h, j) in heads:
                _add(pose, n, (0, 0, 0, 0, -0.5 * turn, 0))
                _add(pose, h, (0, 0, 0, 0, -0.6 * turn, 0))
        elif attack in ("bristle", "charge"):  # head down, rush forward (quills up / armour first)
            wind = ramp(s, 0.0, 0.3) * (1 - ramp(s, 0.3, 0.45))
            rush = bump(s, 0.3, 0.8)
            _add(pose, "Body", (0, -0.05 * height * wind, 0.08 * height * wind - 0.32 * height * rush, -0.12 * rush, 0.05 * math.sin(TAU * s * 4) * rush, 0))
            for up, lo, ft, front, side in legs:
                k = math.sin(TAU * (s * 3 + (0.5 if (front == (side > 0)) else 0)))
                _add(pose, up, (0, 0, 0, 0.45 * k * rush, 0, 0))
                _add(pose, lo, (0, 0, 0, (-0.4 if front else 0.4) * max(0.0, k) * rush, 0, 0))
            for (n, h, j) in heads:
                _add(pose, n, (0, 0, 0, -0.3 * (wind + rush), 0, 0))
                _add(pose, h, (0, 0, 0, -0.2 * rush, 0, 0))
                _add(pose, j, (0, 0, 0, -0.35 * rush, 0, 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, -0.3 * rush, 0.25 * math.sin(TAU * s * 5 - i) * rush, 0))
        else:  # pounce
            wind = ramp(s, 0.0, 0.3) * (1 - ramp(s, 0.3, 0.45))
            st = bump(s, 0.25, 0.8)
            _add(pose, "Body", (0, 0.12 * height * st - 0.05 * height * wind, -0.25 * height * st, 0.35 * st - 0.08 * wind, 0, 0))
            for up, lo, ft, front, side in legs:
                if front:
                    _add(pose, up, (0, 0, 0, 0.9 * st - 0.2 * wind, 0, 0))
                    _add(pose, lo, (0, 0, 0, -0.7 * st, 0, 0))
                else:
                    _add(pose, up, (0, 0, 0, -0.4 * st - 0.15 * wind, 0, 0))
                    _add(pose, lo, (0, 0, 0, 0.3 * wind, 0, 0))
            for (n, h, j) in heads:
                _add(pose, n, (0, 0, 0, -0.25 * st, 0, 0))
                _add(pose, j, (0, 0, 0, -0.55 * st, 0, 0))
        if extra:
            extra("Attack", t, pose)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, -0.04 * height * k, 0.08 * height * k, 0.1 * k, 0, 0.06 * math.sin(t * 40) * k))
        for (n, h, j) in heads:
            _add(pose, n, (0, 0, 0, 0.22 * k, 0, 0))
            _add(pose, h, (0, 0, 0, 0.18 * k, 0.12 * k, 0))
            _add(pose, j, (0, 0, 0, -0.3 * k, 0, 0))
        for up, lo, ft, front, side in legs:
            _add(pose, up, (0, 0, 0, (-0.15 if front else 0.15) * k, 0, 0))
        for b in tail:
            _add(pose, b, (0, 0, 0, 0.35 * k, 0, 0))
        for b in ears:
            _add(pose, b, (0, 0, 0, 0.45 * k, 0, 0))
        if extra:
            extra("Hit", t, pose)
        return pose

    H.clip("Move", walk, move, keys=20)
    H.clip("Idle", 4.8, idle, keys=48 if wag > 0 else 24)
    H.clip("Attack", AL, attack_fn, keys=18, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})
    H.rig["legs"] = [{"hip": up, "knee": lo, "phase": phase_of(front, side), "side": side} for up, lo, ft, front, side in legs]


def hop(H, legs, neck=None, head=None, jaw=None, tail=(), ears=(), height=3.0, walk=0.7, attack="kick", spine=None,
        kangaroo=False, arms=None, extra=None):
    """Hopping gait (rabbits, hares, kangaroos): the hind legs push off together, the body arcs through the air and the
    front paws (rabbit) or tail (kangaroo) take the landing. legs: (upper, lower, foot, front, side)."""

    def move(t):
        u = (t / walk) % 1.0
        pose = {}
        # 0..0.3 push-off, 0.3..0.75 airborne, 0.75..1 land + gather
        push = bump(u, 0.0, 0.35)
        air = bump(u, 0.2, 0.85)
        land = bump(u, 0.7, 1.0) + bump(u, -0.3, 0.05)
        _add(pose, "Body", (0, 0.22 * height * air, 0, (0.1 if kangaroo else 0.22) * push - (0.05 if kangaroo else 0.22) * land, 0, 0))
        if spine:
            _add(pose, spine, (0, 0, 0, -0.2 * push + 0.2 * land, 0, 0))
        for up, lo, ft, front, side in legs:
            if front:
                if kangaroo:
                    _add(pose, up, (0, 0, 0, 0.25 + 0.15 * air, 0, 0))
                    _add(pose, lo, (0, 0, 0, -0.5, 0, 0))
                else:
                    _add(pose, up, (0, 0, 0, -0.35 * push + 0.75 * air - 0.3 * land, 0, 0))
                    _add(pose, lo, (0, 0, 0, -0.4 * push + 0.3 * air, 0, 0))
                    _add(pose, ft, (0, 0, 0, 0.3 * push - 0.2 * air, 0, 0))
            else:
                ext = push
                _add(pose, up, (0, 0, 0, -0.75 * ext + 0.3 * land + 0.25 * air * (1 - ext), 0, 0))
                _add(pose, lo, (0, 0, 0, -0.6 * ext + 0.2 * land, 0, 0))
                _add(pose, ft, (0, 0, 0, 0.9 * ext - 0.2 * air, 0, 0))
        _add(pose, neck, (0, 0, 0, -0.1 * push + 0.12 * land, 0, 0))
        _add(pose, head, (0, 0, 0, 0.12 * air - 0.08 * land, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, (0.4 if kangaroo else 0.2) * air - 0.3 * land - (0.2 * push if kangaroo else 0), 0, 0))
        for i, b in enumerate(ears):
            _add(pose, b, (0, 0, 0, 0.3 * air - 0.15 * land, 0, 0))
        if extra:
            extra("Move", t, pose)
        return pose

    def idle(t):
        u = t / 4.0
        pose = {}
        br = math.sin(TAU * u * 4)
        sniff = max(0.0, math.sin(TAU * u * 2)) ** 3
        _add(pose, "Body", (0, 0.01 * height * br, 0, 0.01 * br, 0, 0))
        _add(pose, neck, (0, 0, 0, 0.05 * math.sin(TAU * u), 0.12 * math.sin(TAU * u + 0.5), 0))
        _add(pose, head, (0, 0, 0, 0.06 * sniff * math.sin(TAU * u * 24), 0.2 * math.sin(TAU * u), 0.06 * math.sin(TAU * u * 2)))
        for i, b in enumerate(ears):
            tw = max(0.0, math.sin(TAU * (u * 2 + i * 0.4))) ** 10
            _add(pose, b, (0, 0, 0, 0.25 * tw - 0.05, 0, (1 if i % 2 == 0 else -1) * 0.2 * tw))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.05 * math.sin(TAU * u * 3 - i), 0.08 * math.sin(TAU * u * 2 - i), 0))
        if kangaroo and arms:
            for b in arms:
                _add(pose, b, (0, 0, 0, 0.06 * br, 0, 0))
        if extra:
            extra("Idle", t, pose)
        return pose

    def attack_fn(t):
        s = t / 0.95
        pose = {}
        rec = 1 - ramp(s, 0.7, 1.0)
        if kangaroo:  # lean back on the tail, both feet kick forward, then a boxing jab
            lean = ramp(s, 0.0, 0.3) * rec
            kick = bump(s, 0.3, 0.7)
            _add(pose, "Body", (0, 0.18 * height * kick, -0.15 * height * kick, 0.25 * lean + 0.25 * kick, 0, 0))
            for up, lo, ft, front, side in legs:
                if front:
                    jab = bump(s, 0.1 if side > 0 else 0.22, 0.4 if side > 0 else 0.52)
                    _add(pose, up, (0, 0, 0, 1.1 * jab + 0.3 * lean, 0, 0))
                    _add(pose, lo, (0, 0, 0, 0.6 * jab, 0, 0))
                else:
                    _add(pose, up, (0, 0, 0, 1.3 * kick - 0.3 * lean, 0, 0))
                    _add(pose, lo, (0, 0, 0, -0.6 * kick, 0, 0))
                    _add(pose, ft, (0, 0, 0, 0.6 * kick, 0, 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, -0.35 * lean - 0.2 * kick, 0, 0))
            _add(pose, neck, (0, 0, 0, -0.2 * lean, 0, 0))
            _add(pose, head, (0, 0, 0, -0.1 * kick, 0, 0))
        else:  # rabbit: thump then double back kick
            thump = bump(s, 0.0, 0.18)
            kick = bump(s, 0.28, 0.5) + 0.8 * bump(s, 0.5, 0.72)
            _add(pose, "Body", (0, 0.06 * height * kick, -0.06 * height * kick, -0.4 * kick + 0.1 * thump, 0, 0))
            for up, lo, ft, front, side in legs:
                if front:
                    _add(pose, up, (0, 0, 0, -0.4 * kick, 0, 0))
                    _add(pose, lo, (0, 0, 0, 0.2 * kick, 0, 0))
                else:
                    _add(pose, up, (0, 0, 0, -1.25 * kick + 0.3 * thump, 0, 0))
                    _add(pose, lo, (0, 0, 0, -0.5 * kick, 0, 0))
                    _add(pose, ft, (0, 0, 0, 1.0 * kick - 0.4 * thump, 0, 0))
            _add(pose, neck, (0, 0, 0, 0.3 * kick, 0, 0))
            _add(pose, head, (0, 0, 0, 0.25 * kick, 0, 0))
            for b in ears:
                _add(pose, b, (0, 0, 0, 0.6 * kick, 0, 0))
        _add(pose, jaw, (0, 0, 0, -0.3 * bump(s, 0.3, 0.6), 0, 0))
        if extra:
            extra("Attack", t, pose)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0.05 * height * k, 0.08 * height * k, 0.12 * k, 0, 0.06 * math.sin(t * 40) * k))
        _add(pose, neck, (0, 0, 0, 0.2 * k, 0, 0))
        _add(pose, head, (0, 0, 0, 0.15 * k, 0.1 * k, 0))
        for b in ears:
            _add(pose, b, (0, 0, 0, 0.5 * k, 0, 0))
        for up, lo, ft, front, side in legs:
            _add(pose, up, (0, 0, 0, (-0.2 if front else 0.25) * k, 0, 0))
        return pose

    H.clip("Move", walk, move, keys=20)
    H.clip("Idle", 4.0, idle, keys=40)
    H.clip("Attack", 0.95, attack_fn, keys=18, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})
    H.rig["legs"] = [{"hip": up, "knee": lo, "phase": 0.0 if not front else 0.5, "side": side} for up, lo, ft, front, side in legs]


# ------------------------------------------------------------------------------------------------ meshing speed-up
# Not motion, but shared by the canines / smallmammals / bears modules: build.py and mesher.py sample every piece's SDF
# over large boxes (the whole hero's bounds); complex sculpts (smooth unions + noise) make that slow. fast() finds the
# piece's own bounding box with a cheap coarse pass and answers the exact SDF only inside it (outside: the distance to
# the box, a positive lower bound), so the result is identical where it matters and meshing is several times faster.
import numpy as _np
from kit import Hero as _Hero


def _box(sd, lo, hi, n):
    lo = _np.asarray(lo, float)
    hi = _np.asarray(hi, float)
    for _ in range(2):  # coarse grid, then refine inside the found box
        xs = [_np.linspace(lo[i], hi[i], n) for i in range(3)]
        X, Y, Z = _np.meshgrid(*xs, indexing="ij")
        P = _np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
        step = float((hi - lo).max()) / (n - 1)
        near = P[sd(P) < step * 1.0]
        if len(near) == 0:
            return None
        lo, hi = near.min(0) - step * 1.5, near.max(0) + step * 1.5
    return (lo + hi) / 2, (hi - lo) / 2


def fast(sd, lo=(-12, -2, -16), hi=(12, 16, 16), n=40):
    """Lazily bounded SDF (the box is found on the first evaluation, i.e. inside the meshing worker)."""
    import sdf as S
    st = {}

    def f(p):
        if "b" not in st:
            st["b"] = _box(sd, lo, hi, n)
        if st["b"] is None:
            return sd(p)
        c, hb = st["b"]
        q = _np.abs(p - c) - hb
        out = _np.linalg.norm(_np.maximum(q, 0), axis=1) + _np.minimum(q.max(1), 0)
        m = out < 0.0
        if m.any():
            out = out + 0.02
            out[m] = sd(p[m])
        return out

    return S.SDF(f)


class FastHero(_Hero):
    """Hero whose sculpted pieces are wrapped with fast() (mirrored copies included)."""

    def piece(self, name, bone, shape, *a, **kw):
        if hasattr(shape, "f"):
            shape = fast(shape)
        return super().piece(name, bone, shape, *a, **kw)
