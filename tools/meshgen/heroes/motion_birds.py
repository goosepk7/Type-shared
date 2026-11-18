"""Authored motion for birds and bats (sampled into keyframe clips by Hero.clip).

Pose values are (px, py, pz, rx, ry, rz) at a bone pivot in its parent's frame (see motion.py). Wings are modelled
spread along +X (right) / -X (left): +rz lifts the right wing, -rz lifts the left one, so every wing rotation about
Y / Z is multiplied by the wing's `side` (+1 right, -1 left). rx about the wing's long axis pitches the leading edge
(+rx = leading edge up), the same sign on both sides.

* fly(...)   flying birds and bats: flap cycle (downstroke / upstroke with elbow and wrist lag, the hand folding back
             on the upstroke, pronation twist), tail fanning, legs tucked; Idle = slow hovering flaps; Attack =
             talon strike / peck / dive; Hit = flinch with a wing flare.
* walk(...)  ground birds: stepping legs (folding tarsus, curling toes), head bob (the head holds still while the
             body passes, then snaps forward), waddle roll for ducks / penguins; Attack = peck / lunge / kick /
             wing-flap display; Hit = recoil.
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


def _bump(s, a, b):
    """0 outside [a, b], a smooth hump inside."""
    if s <= a or s >= b:
        return 0.0
    return math.sin(math.pi * (s - a) / (b - a))


def _env(s, a, b, c, d):
    """Rise a->b, hold b->c, fall c->d (smooth)."""
    if s < a or s > d:
        return 0.0
    if s < b:
        return _ease((s - a) / (b - a))
    if s < c:
        return 1.0
    return 1.0 - _ease((s - c) / (d - c))


# ====================================================================================================== flight
def wing_pose(pose, wing, ph, amp, fold_amt=0.55, lag=0.55, dihedral=0.08, twist=0.18, sweep=0.0, span_scale=1.0):
    """One flap at phase ph (radians). wing = (shoulder, elbow, wrist, side). Downstroke for ph in 0..pi."""
    sh, el, wr, side = wing
    c = math.cos(ph)
    s = math.sin(ph)
    up = max(0.0, -s)            # upstroke
    # elevation (top of the stroke at ph = 0 when using cos): wing high at 0, low at pi
    e_sh = dihedral + amp * c
    e_el = 0.32 * amp * math.cos(ph - lag)
    e_wr = 0.42 * amp * math.cos(ph - 2 * lag)
    _add(pose, sh, (0, 0, 0, -twist * s, -side * (sweep + 0.18 * up * fold_amt), side * e_sh))
    _add(pose, el, (0, 0, 0, -0.5 * twist * s, -side * 0.55 * fold_amt * up, side * (e_el + 0.25 * fold_amt * up)))
    _add(pose, wr, (0, 0, 0, -0.6 * twist * s, -side * 0.95 * fold_amt * up, side * (e_wr - 0.15 * fold_amt * up)))


def fly(H, wings, neck=None, head=None, jaw=None, tail=None, fans=(), legs=(), height=2.0, period=0.8, amp=0.75,
        lift=0.32, pitch=-0.1, attack="talon", fold=0.55, hover_pitch=0.0, idle_amp=0.55, idle_period=None,
        buzz=0, crest=(), extra=None, lag=0.55):
    """Clips for a flying bird / bat.
    wings: [(shoulder, elbow, wrist, side)]; fans: [(tail half bone, side)] spread in ry to fan the tail;
    legs: [(hip, ankle, foot)]; lift: hover height as a fraction of `height` (the model is authored standing, the
    clips carry it up into the air); buzz: flaps per loop override for hummingbirds (fast blur flaps)."""
    idle_period = idle_period or period * 1.6

    def tuck(pose, k, open_=0.0):
        for hip, ank, ft in legs:
            _add(pose, hip, (0, 0, 0, -1.05 * k + 0.9 * open_, 0, 0))
            _add(pose, ank, (0, 0, 0, -0.35 * k - 0.4 * open_, 0, 0))
            _add(pose, ft, (0, 0, 0, 0.9 * k - 0.7 * open_, 0, 0))

    def fan(pose, a):
        for b, side in fans:
            _add(pose, b, (0, 0, 0, 0, side * a, 0))

    def move(t):
        u = t / period
        n = buzz or 1
        ph = TAU * u * n
        pose = {}
        for w in wings:
            wing_pose(pose, w, ph, amp, fold_amt=fold, sweep=0.05, lag=lag)
        bob = -math.cos(ph) * 0.03 * height
        _add(pose, "Body", (0, lift * height + bob, 0, pitch + hover_pitch * 0.5 + 0.04 * math.sin(ph + 0.5), 0.0, 0.03 * math.sin(TAU * u)))
        _add(pose, neck, (0, 0, 0, -0.5 * pitch + 0.03 * math.sin(ph + 1.2), 0, 0))
        _add(pose, head, (0, 0, 0, -0.5 * pitch - 0.03 * math.sin(ph + 1.2), 0.04 * math.sin(TAU * u), 0))
        _add(pose, tail, (0, 0, 0, 0.06 * math.sin(ph + 2.0), 0, 0))
        fan(pose, 0.06 + 0.05 * (1 - math.cos(ph)) * 0.5)
        tuck(pose, 1.0)
        for i, b in enumerate(crest):
            _add(pose, b, (0, 0, 0, -0.12 - 0.05 * math.sin(ph - i), 0, 0))
        if extra:
            extra(pose, "Move", u)
        return pose

    def idle(t):
        u = t / idle_period
        n = buzz or 1
        ph = TAU * u * n + math.pi / 2    # rest frame: wings level, mid-downstroke
        pose = {}
        for w in wings:
            wing_pose(pose, w, ph, idle_amp, fold_amt=fold * 0.8, twist=0.12, lag=lag)
        bob = -math.cos(ph) * 0.025 * height
        _add(pose, "Body", (0, lift * height * 0.92 + bob, 0, hover_pitch + 0.03 * math.sin(ph + 0.4), 0, 0))
        _add(pose, neck, (0, 0, 0, -0.5 * hover_pitch, 0.1 * math.sin(TAU * u), 0))
        _add(pose, head, (0, 0, 0, -0.5 * hover_pitch + 0.03 * math.sin(ph + 1.0), 0.16 * math.sin(TAU * u + 0.7), 0.05 * math.sin(TAU * u + 1)))
        _add(pose, tail, (0, 0, 0, 0.08 * math.sin(ph + 1.8), 0, 0))
        fan(pose, 0.14 + 0.06 * math.sin(ph))
        tuck(pose, 0.55)
        for i, b in enumerate(crest):
            _add(pose, b, (0, 0, 0, 0.05 * math.sin(ph - i), 0, 0))
        if extra:
            extra(pose, "Idle", u)
        return pose

    AL = 0.95

    def attack_fn(t):
        s = t / AL
        pose = {}
        wind = _env(s, 0.0, 0.3, 0.32, 0.5)
        strike = _env(s, 0.3, 0.48, 0.6, 0.95)
        base_ph = math.pi / 2
        if attack == "talon":
            # rear back, mantle the wings high, swing the feet forward with talons spread, then clench
            for w in wings:
                sh, el, wr, side = w
                ph = base_ph + TAU * 1.0 * _ease(s)          # one big flap through the strike
                wing_pose(pose, w, ph, idle_amp * (0.6 + 0.6 * strike), fold_amt=fold, twist=0.15)
                _add(pose, sh, (0, 0, 0, 0.2 * wind, -side * 0.35 * strike, side * 0.45 * wind))
            _add(pose, "Body", (0, lift * height * (0.92 - 0.35 * strike) + 0.08 * height * wind, -0.45 * height * strike + 0.1 * height * wind,
                                hover_pitch + 0.25 * wind + 0.55 * strike, 0, 0))
            _add(pose, neck, (0, 0, 0, -0.35 * strike, 0, 0))
            _add(pose, head, (0, 0, 0, -0.25 * strike - 0.1 * wind, 0, 0))
            grab = _env(s, 0.5, 0.58, 0.75, 0.95)
            for hip, ank, ft in legs:
                _add(pose, hip, (0, 0, 0, -0.6 * (1 - strike) + 1.25 * strike, 0, 0))
                _add(pose, ank, (0, 0, 0, -0.25 * (1 - strike) - 0.35 * strike, 0, 0))
                _add(pose, ft, (0, 0, 0, 0.5 - 0.9 * strike * (1 - grab) + 0.9 * grab, 0, 0))
            fan(pose, 0.15 + 0.3 * strike)
            _add(pose, tail, (0, 0, 0, -0.3 * strike, 0, 0))
        elif attack == "dive":
            # tuck the wings back and stoop down-forward, flare at the bottom with a bite / peck
            for w in wings:
                sh, el, wr, side = w
                wing_pose(pose, w, base_ph, idle_amp * (1 - 0.6 * strike), fold_amt=fold, twist=0.1)
                _add(pose, sh, (0, 0, 0, 0, -side * 0.7 * strike, side * (0.55 * wind + 0.35 * strike)))
                _add(pose, el, (0, 0, 0, 0, -side * 0.55 * strike, -side * 0.3 * strike))
                _add(pose, wr, (0, 0, 0, 0, -side * 0.6 * strike, 0))
            _add(pose, "Body", (0, lift * height * (0.92 - 0.6 * strike) + 0.1 * height * wind, -0.55 * height * strike, hover_pitch + 0.2 * wind - 0.55 * strike, 0, 0))
            _add(pose, neck, (0, 0, 0, 0.25 * strike, 0, 0))
            _add(pose, head, (0, 0, 0, 0.15 * strike, 0, 0))
            tuck(pose, 0.55 + 0.45 * strike)
            fan(pose, 0.12 - 0.08 * strike)
        else:  # peck / bite: hover forward and jab the head
            for w in wings:
                ph = base_ph + TAU * 1.5 * s
                wing_pose(pose, w, ph, idle_amp * 1.15, fold_amt=fold, twist=0.15)
            jab = _bump(s, 0.3, 0.55) + 0.8 * _bump(s, 0.55, 0.78)
            _add(pose, "Body", (0, lift * height * 0.92 - 0.05 * height * strike, -0.3 * height * strike + 0.06 * height * wind, hover_pitch - 0.3 * strike + 0.15 * wind, 0, 0))
            _add(pose, neck, (0, 0, -0.12 * height * jab, -0.1 * wind - 0.35 * jab, 0, 0))
            _add(pose, head, (0, 0, 0, 0.2 * wind - 0.4 * jab, 0, 0))
            tuck(pose, 0.55)
            fan(pose, 0.15)
        if jaw:
            _add(pose, jaw, (0, 0, 0, -(0.45 * wind + 0.25 * _bump(s, 0.3, 0.7)), 0, 0))
        for i, b in enumerate(crest):
            _add(pose, b, (0, 0, 0, -0.35 * wind, 0, 0))
        if extra:
            extra(pose, "Attack", s)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        for w in wings:
            sh, el, wr, side = w
            wing_pose(pose, w, math.pi / 2 - 1.2 * k, idle_amp, fold_amt=fold, twist=0.1)
            _add(pose, sh, (0, 0, 0, 0, side * 0.2 * k, side * 0.3 * k))
        _add(pose, "Body", (0, lift * height * 0.92 + 0.04 * height * k, 0.12 * height * k, hover_pitch + 0.3 * k, 0, 0.12 * math.sin(t * 45) * k))
        _add(pose, neck, (0, 0, 0, 0.3 * k, 0, 0))
        _add(pose, head, (0, 0, 0, 0.2 * k, 0.15 * k, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -(0.35 * k), 0, 0))
        tuck(pose, 0.55 - 0.3 * k, 0.2 * k)
        fan(pose, 0.14 + 0.3 * k)
        for i, b in enumerate(crest):
            _add(pose, b, (0, 0, 0, -0.4 * k, 0, 0))
        return pose

    mkeys = 24 if not buzz else min(48, 8 * buzz)
    H.clip("Move", period, move, keys=mkeys)
    H.clip("Idle", idle_period, idle, keys=24 if not buzz else min(48, 8 * buzz))
    H.clip("Attack", AL, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height, "flying": True})


# ====================================================================================================== ground
def walk(H, legs, wings=(), neck=(), head=None, jaw=None, tail=None, fans=(), height=2.0, period=0.9, stride=0.42,
         bob=0.05, headbob=0.12, waddle=0.0, attack="peck", lean=0.0, crest=(), wattle=None, kick_leg=None, display=None,
         extra=None, run=False):
    """Clips for a ground bird. legs: [(hip, ankle, foot, phase)]; wings: [(wing bone, side)] folded at the sides;
    neck: list of neck bones (base first); headbob: forward-back head travel (fraction of height)."""
    neck = list(neck)

    def legpose(pose, u, k=1.0):
        for hip, ank, ft, ph in legs:
            w = (u + ph) % 1.0
            duty = 0.58 if not run else 0.42
            if w < duty:
                q = w / duty
                a = stride * (1 - 2 * q)          # planted foot sweeps back
                fold = 0.0
            else:
                q = (w - duty) / (1 - duty)
                a = stride * (-1 + 2 * _ease(q))
                fold = math.sin(math.pi * q)
            _add(pose, hip, (0, 0, 0, k * (a + 0.25 * fold), 0, 0))
            _add(pose, ank, (0, 0, 0, k * (-1.1 * fold), 0, 0))
            _add(pose, ft, (0, 0, 0, k * (0.95 * fold - 0.25 * max(0.0, a / max(stride, 1e-3)) * 0.3), 0, 0))

    def headbob_pose(pose, u, amp):
        s = (u * 2) % 1.0
        if s < 0.68:
            z = amp * (s / 0.68 - 0.5)
        else:
            z = amp * (0.5 - _ease((s - 0.68) / 0.32))
        if neck:
            _add(pose, neck[-1], (0, -0.15 * abs(z), z * height, 0, 0, 0))

    def move(t):
        u = t / period
        pose = {}
        legpose(pose, u)
        sw = math.sin(TAU * u)
        _add(pose, "Body", (0, -abs(math.sin(TAU * u)) * bob * height + bob * height * 0.5, 0, -lean + 0.03 * math.sin(TAU * u * 2), 0.06 * waddle * sw * 1.5 + 0.03 * sw, waddle * sw))
        headbob_pose(pose, u, headbob)
        if neck:
            _add(pose, neck[0], (0, 0, 0, 0.03 * math.sin(TAU * u * 2 + 0.5), -0.03 * sw, -0.6 * waddle * sw))
        _add(pose, head, (0, 0, 0, 0.03 * math.sin(TAU * u * 2 + 1), 0, -0.3 * waddle * sw))
        _add(pose, tail, (0, 0, 0, 0.06 * math.sin(TAU * u * 2 - 0.8), 0.1 * sw, 0))
        for b, side in wings:
            _add(pose, b, (0, 0, 0, 0, 0, side * (0.04 + 0.04 * math.sin(TAU * u * 2)) + (side * 0.15 if run else 0)))
        for i, b in enumerate(crest):
            _add(pose, b, (0, 0, 0, 0.08 * math.sin(TAU * u * 2 - 0.6 - i * 0.5), 0, 0))
        if wattle:
            _add(pose, wattle, (0, 0, 0, 0.15 * math.sin(TAU * u * 2 - 1.2), 0, 0.1 * sw))
        if extra:
            extra(pose, "Move", u)
        return pose

    IL = 4.0

    def idle(t):
        u = t / IL
        pose = {}
        br = math.sin(TAU * u * 3)
        _add(pose, "Body", (0, 0.006 * height * br, 0, -lean + 0.01 * br, 0.04 * math.sin(TAU * u), 0))
        # look around in quick turns, one ground peck per loop
        look = math.sin(TAU * u) + 0.4 * math.sin(TAU * u * 3 + 1)
        peck = _bump(u, 0.62, 0.74)
        if neck:
            _add(pose, neck[0], (0, 0, 0, -0.35 * peck, 0.12 * look, 0))
            if len(neck) > 1:
                _add(pose, neck[-1], (0, 0, -0.04 * height * peck, -0.35 * peck, 0.1 * look, 0))
        _add(pose, head, (0, 0, 0, -0.25 * peck + 0.04 * br, 0.3 * look, 0.12 * math.sin(TAU * u * 2 + 0.4)))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -(0.12 * _bump(u, 0.2, 0.3)), 0, 0))
        _add(pose, tail, (0, 0, 0, 0.04 * br, 0.12 * _bump(u, 0.35, 0.45) * math.sin(TAU * u * 20), 0))
        ruffle = _bump(u, 0.82, 0.95)
        for b, side in wings:
            _add(pose, b, (0, 0, 0, 0, 0, side * (0.03 + 0.35 * ruffle * abs(math.sin(TAU * u * 14)))))
        for b, side in fans:
            _add(pose, b, (0, 0, 0, 0, side * 0.04 * br, 0))
        for i, b in enumerate(crest):
            _add(pose, b, (0, 0, 0, 0.06 * br, 0, 0))
        if wattle:
            _add(pose, wattle, (0, 0, 0, 0.08 * math.sin(TAU * u * 2), 0, 0))
        if extra:
            extra(pose, "Idle", u)
        return pose

    AL = 0.85

    def attack_fn(t):
        s = t / AL
        pose = {}
        wind = _env(s, 0.0, 0.3, 0.32, 0.45)
        strike = _env(s, 0.3, 0.45, 0.58, 0.95)
        flap = _env(s, 0.1, 0.3, 0.6, 0.95)
        if attack == "kick" and kick_leg:
            hip, ank, ft = kick_leg
            _add(pose, "Body", (0, 0.02 * height * wind, 0.05 * height * strike, 0.15 * wind + 0.12 * strike, 0, 0))
            _add(pose, hip, (0, 0, 0, 0.9 * wind - 0.35 * strike + 1.1 * strike * (1 - wind), 0, 0))
            _add(pose, ank, (0, 0, 0, -1.4 * wind + 1.0 * strike, 0, 0))
            _add(pose, ft, (0, 0, 0, 0.8 * wind - 0.4 * strike, 0, 0))
            if neck:
                _add(pose, neck[0], (0, 0, 0, 0.25 * strike, 0, 0))
            for b, side in wings:
                _add(pose, b, (0, 0, 0, 0, 0, side * 0.6 * flap))
        else:
            lunge = 0.12 if attack == "peck" else 0.22
            _add(pose, "Body", (0, -0.02 * height * strike, -lunge * height * strike + 0.04 * height * wind, 0.12 * wind - 0.25 * strike, 0, 0))
            if neck:
                _add(pose, neck[0], (0, 0, 0, 0.3 * wind - 0.55 * strike, 0, 0))
                for b in neck[1:]:
                    _add(pose, b, (0, 0, 0, 0.15 * wind - 0.25 * strike, 0, 0))
            _add(pose, head, (0, 0, 0, 0.1 * wind - 0.35 * strike, 0, 0))
            wf = 0.9 if attack in ("lunge", "display") else 0.45
            for b, side in wings:
                _add(pose, b, (0, 0, 0, 0.0, -side * 0.1 * flap, side * wf * flap * (0.8 + 0.3 * math.sin(TAU * s * 4))))
            for hip, ank, ft, ph in legs:
                _add(pose, hip, (0, 0, 0, (0.25 if ph == 0 else -0.2) * strike, 0, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -(0.5 * wind + 0.2 * strike), 0, 0))
        for b, side in fans:
            _add(pose, b, (0, 0, 0, 0, side * 0.15 * flap, 0))
        _add(pose, tail, (0, 0, 0, 0.25 * flap, 0, 0))
        for i, b in enumerate(crest):
            _add(pose, b, (0, 0, 0, -0.35 * flap, 0, 0))
        if wattle:
            _add(pose, wattle, (0, 0, 0, 0.4 * strike, 0, 0))
        if extra:
            extra(pose, "Attack", s)
        return pose

    def hit(t):
        s = t / 0.4
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0.02 * height * k, 0.08 * height * k, 0.15 * k - lean, 0, 0.08 * math.sin(t * 45) * k))
        if neck:
            _add(pose, neck[0], (0, 0, 0, 0.3 * k, 0, 0))
        _add(pose, head, (0, 0, 0, 0.25 * k, 0.15 * k, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -(0.3 * k), 0, 0))
        for b, side in wings:
            _add(pose, b, (0, 0, 0, 0, 0, side * 0.6 * k))
        for i, b in enumerate(crest):
            _add(pose, b, (0, 0, 0, -0.3 * k, 0, 0))
        return pose

    H.clip("Move", period, move, keys=20)
    H.clip("Idle", IL, idle, keys=32)
    H.clip("Attack", AL, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.4, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": height})
