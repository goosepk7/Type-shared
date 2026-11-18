"""Authored motion cycles for hero models (sampled into keyframe clips by Hero.clip).

Pose values are (px, py, pz, rx, ry, rz): a translation and model-axis Euler angles applied at a bone's pivot, in its
parent's frame (Motor6D.Transform). Signs for a model facing -Z: +rx on a downward limb swings its tip FORWARD,
+rx on the body pitches the nose UP, -rx on a forward-pointing jaw opens it, +ry turns left (toward -X ... the
model's right side moves forward), +rz rolls.
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


def leg_cycle(u, stride, lift, front, duty=0.62):
    """One leg over a cycle u in 0..1: returns (upper, lower, foot) rx. Stance: the upper sweeps back at constant
    speed (foot planted); swing: the leg folds and reaches forward again."""
    u = u % 1.0
    if u < duty:
        s = u / duty
        up = stride * (1 - 2 * s)
        fold = 0.0
    else:
        s = (u - duty) / (1 - duty)
        up = stride * (-1 + 2 * _ease(s))
        fold = math.sin(math.pi * s)
    if front:
        # forearm folds back under the elbow, paw curls
        return up + 0.15 * fold * lift, -1.1 * fold * lift, 0.9 * fold * lift
    # hind: stifle / hock fold, the shin swings forward and the foot hangs
    return up - 0.1 * fold * lift, 0.75 * fold * lift, -0.85 * fold * lift


def quadruped(H, legs, spine=None, neck=None, head=None, jaw=None, tail=(), ears=(), stride=0.42, lift=1.0, walk=1.0,
              run=0.85, height=3.0, attack="pounce", swipe=None):
    """Clips for a four-legged animal.
    legs: list of (upper, lower, foot, phase, front). Lateral walk phases: LH 0, LF .25, RH .5, RF .75.
    spine: optional bone between Body and the hindquarters / chest (flexes in the run).
    swipe: the upper bone of the leg used for a paw swipe (attack = "pounce" or "swipe" or "gore" or "bite")."""

    def move(t):
        u = t / walk
        pose = {}
        for up, lo, ft, ph, front in legs:
            a, b, c = leg_cycle(u + ph, stride, lift, front)
            _add(pose, up, (0, 0, 0, a, 0, 0))
            _add(pose, lo, (0, 0, 0, b, 0, 0))
            _add(pose, ft, (0, 0, 0, c, 0, 0))
        _add(pose, "Body", (0, -abs(math.sin(TAU * u * 2)) * 0.035 * height + 0.02 * height, 0, 0.025 * math.sin(TAU * u * 2), 0.03 * math.sin(TAU * u), 0.025 * math.sin(TAU * u)))
        if spine:
            _add(pose, spine, (0, 0, 0, 0.03 * math.sin(TAU * u * 2 + 1), -0.04 * math.sin(TAU * u), 0))
        _add(pose, neck, (0, 0, 0, -0.06 * math.sin(TAU * u * 2 + 0.6), 0, 0))
        _add(pose, head, (0, 0, 0, 0.05 * math.sin(TAU * u * 2 + 0.9), -0.03 * math.sin(TAU * u), 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.05 * math.sin(TAU * u * 2 - i * 0.7), 0.16 * math.sin(TAU * u - i * 0.9), 0))
        return pose

    def idle(t):
        u = t / 4.8
        pose = {}
        br = math.sin(TAU * u * 2)
        _add(pose, "Body", (0, 0.008 * height * br, 0, 0.008 * br, 0, 0))
        _add(pose, neck, (0, 0, 0, 0.04 * math.sin(TAU * u) - 0.02, 0.1 * math.sin(TAU * u + 0.5), 0))
        _add(pose, head, (0, 0, 0, 0.05 * math.sin(TAU * u * 2 + 1), 0.22 * math.sin(TAU * u) * (0.6 + 0.4 * math.sin(TAU * u * 3)), 0.05 * math.sin(TAU * u + 2)))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.04 * math.sin(TAU * u * 3 - i), 0.22 * math.sin(TAU * u * 2 - i * 0.8), 0))
        for i, b in enumerate(ears):
            tw = max(0.0, math.sin(TAU * (u * 3 + i * 0.37))) ** 12
            _add(pose, b, (0, 0, 0, -0.25 * tw, 0, (1 if i % 2 == 0 else -1) * 0.15 * tw))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.04 * max(0.0, math.sin(TAU * u)) ** 4, 0, 0))
        return pose

    def attack(t):
        L = 0.9
        s = t / L
        pose = {}
        wind = _ease(s / 0.3) if s < 0.3 else 1 - _ease((s - 0.3) / 0.25) if s < 0.55 else 0.0
        strike = math.sin(math.pi * min(max((s - 0.25) / 0.5, 0), 1))
        rec = 1 - _ease((s - 0.55) / 0.45) if s > 0.55 else 1.0
        if attack in ("pounce", "swipe"):
            rear = 0.38 * strike
            _add(pose, "Body", (0, 0.12 * height * strike - 0.05 * height * wind, -0.25 * height * strike, rear - 0.08 * wind, 0, 0))
            for up, lo, ft, ph, front in legs:
                if front:
                    _add(pose, up, (0, 0, 0, 0.9 * strike - 0.2 * wind, 0, 0))
                    _add(pose, lo, (0, 0, 0, -0.7 * strike, 0, 0))
                    _add(pose, ft, (0, 0, 0, 0.6 * strike, 0, 0))
                else:
                    _add(pose, up, (0, 0, 0, -rear * 1.1 - 0.15 * wind, 0, 0))
                    _add(pose, lo, (0, 0, 0, 0.3 * wind, 0, 0))
            if swipe:
                _add(pose, swipe, (0, 0, 0, 0.7 * math.sin(math.pi * min(max((s - 0.35) / 0.35, 0), 1)), 0, 0.35 * strike))
            _add(pose, neck, (0, 0, 0, -0.25 * strike, 0, 0))
            _add(pose, head, (0, 0, 0, -0.2 * strike, 0, 0))
        elif attack == "gore":
            _add(pose, "Body", (0, -0.04 * height * wind, -0.3 * height * strike, -0.12 * strike, 0, 0))
            _add(pose, neck, (0, 0, 0, -0.35 * wind + 0.45 * strike, 0, 0))
            _add(pose, head, (0, 0, 0, -0.3 * wind + 0.4 * strike, 0, 0))
            for up, lo, ft, ph, front in legs:
                _add(pose, up, (0, 0, 0, (0.25 if front else -0.25) * strike, 0, 0))
        else:  # bite / lunge
            _add(pose, "Body", (0, 0, -0.18 * height * strike, -0.05 * strike, 0, 0))
            _add(pose, neck, (0, 0, 0, 0.15 * wind - 0.35 * strike, 0, 0))
            _add(pose, head, (0, 0, 0, -0.2 * strike, 0, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.55 * strike, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.25 * strike, 0.2 * math.sin(TAU * s * 2 - i), 0))
        for k, v in list(pose.items()):
            pose[k] = tuple(x * (rec if s > 0.55 else 1.0) for x in v)
        return pose

    def hit(t):
        s = t / 0.4
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, -0.03 * height * k, 0.08 * height * k, 0.12 * k, 0, 0.05 * math.sin(t * 40) * k))
        _add(pose, neck, (0, 0, 0, 0.2 * k, 0, 0))
        _add(pose, head, (0, 0, 0, 0.15 * k, 0.1 * k, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.3 * k, 0, 0))
        return pose

    H.clip("Move", walk, move, keys=20)
    H.clip("Idle", 4.8, idle, keys=24)
    H.clip("Attack", 0.9, attack, keys=14, loop=False)
    H.clip("Hit", 0.4, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})


def biped(H, legs, arms=(), spine=None, neck=None, head=None, jaw=None, tail=(), stride=0.5, walk=1.0, height=5.0, attack="punch",
          lean=0.0, weapon_arm=None):
    """Clips for an upright two-legged figure. legs: (hip, knee, foot, phase); arms: (shoulder, elbow, hand, side)."""

    def move(t):
        u = t / walk
        pose = {}
        for hip, knee, foot, ph in legs:
            w = (u + ph) % 1.0
            sw = math.sin(TAU * w)
            _add(pose, hip, (0, 0, 0, stride * sw, 0, 0))
            fold = max(0.0, math.sin(TAU * w + 1.3))
            _add(pose, knee, (0, 0, 0, -1.0 * stride * fold - 0.05, 0, 0))
            _add(pose, foot, (0, 0, 0, 0.4 * stride * fold * 0.6, 0, 0))
        for sh, el, hd, side in arms:
            sgn = 1 if side > 0 else -1
            ph = 0.0 if side > 0 else 0.5
            sw = math.sin(TAU * (u + ph))
            _add(pose, sh, (0, 0, 0, -0.55 * stride * sw, 0, 0))
            _add(pose, el, (0, 0, 0, 0.35 + 0.25 * max(0.0, sw), 0, 0))
        _add(pose, "Body", (0, 0.025 * height * abs(math.sin(TAU * u)) - 0.012 * height, 0, -lean + 0.02 * math.sin(TAU * u * 2), 0.05 * math.sin(TAU * u), 0.025 * math.sin(TAU * u)))
        _add(pose, spine, (0, 0, 0, 0, -0.08 * math.sin(TAU * u), 0))
        _add(pose, head, (0, 0, 0, 0.02 * math.sin(TAU * u * 2), 0.05 * math.sin(TAU * u), 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.04 * math.sin(TAU * u * 2 - i), 0.2 * math.sin(TAU * u - i * 0.8), 0))
        return pose

    def idle(t):
        u = t / 4.0
        pose = {}
        br = math.sin(TAU * u * 2)
        _add(pose, "Body", (0, 0.004 * height * br, 0, 0, 0.03 * math.sin(TAU * u), 0.012 * math.sin(TAU * u)))
        _add(pose, spine, (0, 0, 0, 0.012 * br, 0, 0))
        _add(pose, head, (0, 0, 0, 0.03 * math.sin(TAU * u * 2 + 1), 0.18 * math.sin(TAU * u), 0))
        for sh, el, hd, side in arms:
            sgn = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, 0.03 * br, 0, sgn * (0.08 + 0.02 * br)))
            _add(pose, el, (0, 0, 0, 0.18, 0, 0))
        for hip, knee, foot, ph in legs:
            _add(pose, knee, (0, 0, 0, -0.04, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.03 * math.sin(TAU * u * 2 - i), 0.18 * math.sin(TAU * u * 2 - i * 0.8), 0))
        return pose

    def attack_fn(t):
        L = 0.8
        s = t / L
        pose = {}
        wind = _ease(s / 0.35) if s < 0.35 else 1 - _ease((s - 0.35) / 0.15) if s < 0.5 else 0.0
        strike = math.sin(math.pi * min(max((s - 0.3) / 0.45, 0), 1))
        arm = None
        for a in arms:
            if weapon_arm is None or a[0] == weapon_arm:
                arm = a
                break
        if attack == "slam":
            _add(pose, "Body", (0, -0.05 * height * strike, -0.08 * height * strike, -0.25 * strike + 0.12 * wind, 0, 0))
            for sh, el, hd, side in arms:
                _add(pose, sh, (0, 0, 0, 2.4 * wind + 0.6 * strike, 0, 0))
                _add(pose, el, (0, 0, 0, 0.4 * wind, 0, 0))
        elif arm:
            sh, el, hd, side = arm
            sgn = 1 if side > 0 else -1
            _add(pose, "Body", (0, 0, -0.06 * height * strike, -0.08 * strike, sgn * (0.35 * wind - 0.55 * strike), 0))
            _add(pose, sh, (0, 0, 0, 1.9 * wind + 0.2 * strike, 0, sgn * 0.3 * wind))
            _add(pose, el, (0, 0, 0, 0.9 * wind - 0.4 * strike, 0, 0))
        _add(pose, head, (0, 0, 0, -0.1 * strike, 0, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.4 * strike, 0, 0))
        for hip, knee, foot, ph in legs:
            _add(pose, hip, (0, 0, 0, (0.35 if ph == 0 else -0.25) * strike, 0, 0))
            _add(pose, knee, (0, 0, 0, -0.3 * strike, 0, 0))
        return pose

    def hit(t):
        s = t / 0.4
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0, 0.06 * height * k, 0.18 * k, 0, 0.06 * math.sin(t * 40) * k))
        _add(pose, head, (0, 0, 0, 0.25 * k, 0, 0))
        for sh, el, hd, side in arms:
            _add(pose, sh, (0, 0, 0, 0.5 * k, 0, (1 if side > 0 else -1) * 0.4 * k))
        return pose

    H.clip("Move", walk, move, keys=20)
    H.clip("Idle", 4.0, idle, keys=20)
    H.clip("Attack", 0.8, attack_fn, keys=14, loop=False)
    H.clip("Hit", 0.4, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})
