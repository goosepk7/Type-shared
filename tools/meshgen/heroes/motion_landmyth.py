"""Authored motion for the landmyth family (h_landmyth.py): wing-armed hoverers with a dive-claw (harpies), a
cosmic-mass float with tentacle waves and swirling debris (eldritch horrors, planet eaters, ophanim rings), and
small overlays (tentacles on a six-legged cat, a rider on a horse).

Pose values are (px, py, pz, rx, ry, rz) at a bone pivot in its parent's frame. For a model facing -Z: +rx on a
downward limb swings its tip FORWARD, +rx on the body pitches the nose UP, -rx on a forward jaw opens it, +rz raises
a right (+X) wing. Looping clips are built from whole-cycle sines so Idle / Move join seamlessly. Rotations never
wrap a full turn (clips are cyclic Catmull-Rom in Euler angles), so rings and debris swing in large arcs instead.
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
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def bump(s, a, b):
    """0 -> 1 -> 0 over [a, b]."""
    if s <= a or s >= b:
        return 0.0
    return math.sin(math.pi * (s - a) / (b - a))


def env(s, a, b, c, d):
    """Rise a->b, hold, fall c->d."""
    if s <= a or s >= d:
        return 0.0
    if s < b:
        return ease((s - a) / (b - a))
    if s <= c:
        return 1.0
    return 1.0 - ease((s - c) / (d - c))


def overlay(H, name, fn):
    """Add fn(t) poses onto the existing clip `name` (same key times)."""
    c = H.clips[name]
    n, L = c["keys"], c["len"]
    times = [L * i / n for i in range(n)] if c["loop"] else [L * i / (n - 1) for i in range(n)]
    for i, t in enumerate(times):
        pose = fn(t)
        for b, v in pose.items():
            assert b in H.bidx, f"{H.id}: overlay {name} bone {b} unknown"
            tr = c["tracks"].setdefault(b, [(0.0,) * 6 for _ in range(n)])
            o = list(tr[i])
            for j, x in enumerate(v):
                o[j] += float(x)
            tr[i] = tuple(o)


def flap(pose, wings, ph, amp, base=0.1, lag=0.6, twist=0.15, sweep=0.0):
    """wings: (shoulder, elbow, hand, side). Upstroke at ph = 0 (cos), downstroke through pi. Elbow / hand lag."""
    for sh, el, hd, side in wings:
        sg = 1 if side > 0 else -1
        _add(pose, sh, (0, 0, 0, -twist * math.sin(ph), sg * sweep, sg * (base + amp * math.cos(ph))))
        _add(pose, el, (0, 0, 0, 0, 0, sg * 0.35 * amp * math.cos(ph - lag)))
        _add(pose, hd, (0, 0, 0, -0.5 * twist * math.sin(ph), 0, sg * 0.45 * amp * math.cos(ph - 2 * lag)))


# ================================================================================================ hover + dive-claw
def wing_hover(H, wings, legs=(), arms=(), spine=None, head=None, jaw=None, tail=(), crest=(), hair=(), height=5.0,
               rate=1.0, amp=0.62, lift=0.12, attack="dive", weapon_arm=None, fold_tip=0.0):
    """A winged biped that hovers (Idle), flies pitched forward (Move) and strikes with a dive-claw (Attack: climbs
    with wings high, dives forward and swings both taloned feet into the target, flares, recovers).
    wings: (shoulder, elbow, hand, side); legs: (hip, knee, foot); arms: (shoulder, elbow, hand, side) of a figure
    whose wings are on its back; attack "dive" (talons) or "shoot" (draw a bow with `arms`)."""
    H.rig["gait"] = "hover"
    up = lift * height

    def common(pose, u, k=1.0):
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.08 * k * math.sin(TAU * u * 2 - i * 0.8), 0.1 * k * math.sin(TAU * u - i), 0))
        for i, b in enumerate(crest):
            _add(pose, b, (0, 0, 0, 0.1 * math.sin(TAU * u * 2 - 0.6 - i * 0.5), 0, 0.04 * math.sin(TAU * u + i)))
        for i, b in enumerate(hair):
            _add(pose, b, (0, 0, 0, 0.07 * math.sin(TAU * u * 2 - 1.0 - i * 0.6), 0, 0.03 * math.sin(TAU * u - i)))

    def dangle(pose, u, k=1.0, back=0.0):
        for i, (hip, knee, foot) in enumerate(legs):
            ph = i * 1.9
            _add(pose, hip, (0, 0, 0, 0.18 * k - back + 0.1 * math.sin(TAU * u * 2 + ph), 0, 0))
            _add(pose, knee, (0, 0, 0, 0.35 * k + 0.6 * back + 0.08 * math.sin(TAU * u * 2 + ph + 0.8), 0, 0))
            _add(pose, foot, (0, 0, 0, -0.3 * k - 0.2 * back, 0, 0))

    def idle(t):
        u = t / 2.0
        pose = {}
        ph = TAU * u * 2 * rate
        _add(pose, "Body", (0, up + 0.035 * height * math.sin(ph - 1.3), 0, 0.03 * math.sin(ph - 1.6), 0.08 * math.sin(TAU * u), 0))
        _add(pose, spine, (0, 0, 0, -0.04 * math.sin(ph - 1.0), 0, 0))
        flap(pose, wings, ph + math.pi / 2, amp, base=0.05, sweep=0.0)
        _add(pose, head, (0, 0, 0, 0.05 * math.sin(ph - 2.0), 0.25 * math.sin(TAU * u), 0))
        dangle(pose, u)
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, 0.12 + 0.05 * math.sin(ph), 0, sg * (0.18 + 0.04 * math.sin(ph + 1))))
            _add(pose, el, (0, 0, 0, 0.35, 0, 0))
        common(pose, u)
        return pose

    def move(t):
        u = t / 1.0
        pose = {}
        ph = TAU * u * 2 * rate
        _add(pose, "Body", (0, up + 0.05 * height * math.sin(ph - 1.3), 0, -0.42 + 0.04 * math.sin(ph - 1.6), 0, 0.06 * math.sin(TAU * u)))
        _add(pose, spine, (0, 0, 0, 0.08, 0, 0))
        _add(pose, head, (0, 0, 0, 0.35 + 0.05 * math.sin(ph - 2.0), 0, -0.04 * math.sin(TAU * u)))
        flap(pose, wings, ph, amp * 1.3, base=0.12, twist=0.3, sweep=-0.1)
        dangle(pose, u, 0.3, back=0.75)
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, -0.5, 0, sg * 0.15))
            _add(pose, el, (0, 0, 0, 0.3, 0, 0))
        common(pose, u * 2, 1.5)
        return pose

    def attack_fn(t):
        L = 1.0
        s = t / L
        pose = {}
        climb = env(s, 0.0, 0.28, 0.32, 0.5)
        dive = env(s, 0.3, 0.5, 0.58, 0.8)
        strike = bump(s, 0.45, 0.72)
        rec = 1.0 - ease((s - 0.72) / 0.28) if s > 0.72 else 1.0
        if attack == "shoot":
            draw = env(s, 0.05, 0.4, 0.5, 0.62)
            loose = bump(s, 0.5, 0.75)
            _add(pose, "Body", (0, up + 0.05 * height * draw, 0.05 * height * loose, 0.06 * draw - 0.08 * loose, -0.25 * draw, 0))
            flap(pose, wings, TAU * s * 2.5, amp * 0.8, base=0.15)
            for sh, el, hd, side in arms:
                if side > 0:   # draw hand (right) pulls back to the cheek
                    _add(pose, sh, (0, 0, 0, 1.45 * draw, 0.2 * draw, 0.35 * draw))
                    _add(pose, el, (0, 0, 0, 1.6 * draw - 0.8 * loose, 0, 0))
                else:          # bow arm straight out
                    _add(pose, sh, (0, 0, 0, 1.5 * draw, 0, -0.1 * draw))
                    _add(pose, el, (0, 0, 0, 0.05 * draw, 0, 0))
            _add(pose, head, (0, 0, 0, 0.0, 0.2 * draw, 0))
            dangle(pose, s)
        else:
            _add(pose, "Body", (0, up + (0.22 * climb - 0.2 * dive) * height, -0.45 * height * dive, 0.25 * climb - 0.6 * dive + 0.5 * strike, 0, 0))
            _add(pose, spine, (0, 0, 0, -0.15 * dive + 0.2 * strike, 0, 0))
            # wings beat hard on the climb, sweep back in the dive, flare out at the strike
            flap(pose, wings, TAU * s * 3.0, amp * (1.2 * climb + 0.2), base=0.55 * climb + 0.25 * dive - 0.1 * strike,
                 sweep=-0.7 * dive + 0.2 * strike)
            for hip, knee, foot in legs:
                _add(pose, hip, (0, 0, 0, -0.5 * climb - 0.4 * dive + 1.45 * strike, 0, 0))
                _add(pose, knee, (0, 0, 0, 0.6 * climb + 0.6 * dive - 0.3 * strike, 0, 0))
                _add(pose, foot, (0, 0, 0, -0.4 * climb - 0.6 * dive + 0.9 * strike, 0, 0))
            _add(pose, head, (0, 0, 0, -0.2 * climb + 0.5 * dive - 0.3 * strike, 0, 0))
            if jaw:
                _add(pose, jaw, (0, 0, 0, -0.45 * (dive + strike) * 0.7, 0, 0))
        common(pose, s, 1.5)
        for k, v in list(pose.items()):
            if k == "Body":
                v = (v[0], up + (v[1] - up) * rec) + tuple(x * rec for x in v[2:])
                pose[k] = v
            else:
                pose[k] = tuple(x * rec for x in v)
        if rec < 1.0:
            idl = idle(0.0)
            for k, v in idl.items():
                _add(pose, k, tuple(x * (1 - rec) for x in (v if k != "Body" else (v[0], v[1] - up) + tuple(v[2:]))))
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, up - 0.06 * height * k, 0.12 * height * k, 0.3 * k, 0, 0.12 * math.sin(t * 40) * k))
        _add(pose, head, (0, 0, 0, 0.3 * k, 0, 0))
        flap(pose, wings, 0.0, 0.0, base=0.7 * k)
        for hip, knee, foot in legs:
            _add(pose, hip, (0, 0, 0, 0.5 * k, 0, 0))
            _add(pose, knee, (0, 0, 0, 0.4 * k, 0, 0))
        for sh, el, hd, side in arms:
            _add(pose, sh, (0, 0, 0, 0.5 * k, 0, (1 if side > 0 else -1) * 0.4 * k))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.35 * k, 0, 0))
        return pose

    H.clip("Idle", 2.0, idle, keys=24)
    H.clip("Move", 1.0, move, keys=20)
    H.clip("Attack", 1.0, attack_fn, keys=18, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"height": height})


# ================================================================================================ cosmic masses
def mass_float(H, tentacles=(), eyes=(), swirl=(), core=None, jaw=None, lids=(), height=4.0, hover=0.18, attack="lash",
               pulse=0.04, drift_pitch=-0.18, extra=None):
    """A floating mass: the core breathes, tentacle chains wave (a travelling wave from root to tip), eye bones glance
    around, swirl bones (debris rings / halo rings) swing in big counter-turning arcs.
    tentacles: list of bone chains, each [(bone, dir_sign)...] or a plain list of bones; swirl: (bone, axis 3/4/5,
    amplitude, cycles per loop). attack: lash (tentacles snap forward, maw opens) or gaze (body rears, eyes bulge, rings
    flare) or devour (the core lunges with the maw open)."""
    H.rig["gait"] = "hover"
    up = hover * height

    def chains():
        out = []
        for ci, ch in enumerate(tentacles):
            out.append([(b if isinstance(b, str) else b[0]) for b in ch])
        return out

    CH = chains()

    def wave(pose, u, amp, speed=1, k_fwd=0.0):
        for ci, ch in enumerate(CH):
            ph0 = ci * 2.399
            for i, b in enumerate(ch):
                a = amp * (0.6 + 0.4 * i / max(len(ch) - 1, 1))
                _add(pose, b, (0, 0, 0, a * math.sin(TAU * u * speed - i * 0.9 + ph0) + k_fwd,
                               0.6 * a * math.sin(TAU * u * speed - i * 0.8 + ph0 + 1.3),
                               0.8 * a * math.cos(TAU * u * speed - i * 0.7 + ph0)))

    def swirl_pose(pose, u, k=1.0):
        for b, axis, a, cyc in swirl:
            v = [0, 0, 0, 0, 0, 0]
            v[axis] = k * a * math.sin(TAU * u * cyc + (sum(map(ord, b)) % 7))
            _add(pose, b, v)

    def glance(pose, u):
        for i, b in enumerate(eyes):
            g = math.sin(TAU * (u * 2 + i * 0.37))
            _add(pose, b, (0, 0, 0, 0.18 * math.sin(TAU * (u + i * 0.21)), 0.3 * g, 0))

    def idle(t):
        u = t / 4.0
        pose = {}
        br = math.sin(TAU * u * 2)
        _add(pose, "Body", (0, up + 0.05 * height * math.sin(TAU * u), 0, 0.04 * math.sin(TAU * u + 1), 0.12 * math.sin(TAU * u), 0.04 * math.sin(TAU * u * 2)))
        _add(pose, core, (0, pulse * height * br, 0, 0, 0, 0))
        wave(pose, u, 0.22, speed=2)
        swirl_pose(pose, u)
        glance(pose, u)
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.12 * max(0.0, math.sin(TAU * u * 2)) ** 2, 0, 0))
        for i, b in enumerate(lids):
            blink = max(0.0, math.sin(TAU * (u * 2 + i * 0.3))) ** 30
            _add(pose, b, (0, 0, 0, 0.6 * blink, 0, 0))
        if extra:
            extra("Idle", u, pose)
        return pose

    def move(t):
        u = t / 2.0
        pose = {}
        _add(pose, "Body", (0, up + 0.04 * height * math.sin(TAU * u * 2), 0, drift_pitch, 0, 0.05 * math.sin(TAU * u)))
        _add(pose, core, (0, 0.6 * pulse * height * math.sin(TAU * u * 2), 0, 0, 0, 0))
        wave(pose, u, 0.3, speed=2, k_fwd=0.0)
        swirl_pose(pose, u, 1.2)
        glance(pose, u)
        if extra:
            extra("Move", u, pose)
        return pose

    def attack_fn(t):
        L = 1.0
        s = t / L
        pose = {}
        wind = env(s, 0.0, 0.3, 0.35, 0.5)
        hitk = bump(s, 0.35, 0.75)
        rec = 1.0 - ease((s - 0.7) / 0.3) if s > 0.7 else 1.0
        if attack == "gaze":
            _add(pose, "Body", (0, up + 0.12 * height * wind * rec, -0.1 * height * hitk, (0.25 * wind - 0.2 * hitk) * rec, 0, 0))
            swirl_pose(pose, s, 1.0 + 1.5 * hitk)
            for b in eyes:
                _add(pose, b, (0, 0, 0, -0.2 * hitk * rec, 0, 0))
            wave(pose, s, 0.4 * rec, speed=3)
        else:
            _add(pose, "Body", (0, up + 0.08 * height * wind * rec, (0.1 * wind - 0.35 * hitk) * height * rec, (0.2 * wind - 0.3 * hitk) * rec, 0, 0))
            _add(pose, core, (0, 0, 0, 0, 0, 0))
            for ci, ch in enumerate(CH):
                for i, b in enumerate(ch):
                    # coil back, then whip forward (+rx swings a downward tentacle tip forward)
                    _add(pose, b, (0, 0, 0, (-0.45 * wind + 0.75 * hitk) * rec * (0.7 + 0.3 * i), 0, 0))
            swirl_pose(pose, s, 1.6 * rec)
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.7 * (0.5 * wind + hitk) * rec, 0, 0))
        if extra:
            extra("Attack", s, pose)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, up - 0.04 * height * k, 0.1 * height * k, 0.2 * k, 0, 0.1 * math.sin(t * 38) * k))
        _add(pose, core, (0, -0.04 * height * k, 0, 0, 0, 0))
        for ch in CH:
            for i, b in enumerate(ch):
                _add(pose, b, (0, 0, 0, -0.35 * k, 0, 0.2 * math.sin(t * 30 + i) * k))
        for i, b in enumerate(lids):
            _add(pose, b, (0, 0, 0, 0.6 * k, 0, 0))
        if extra:
            extra("Hit", s, pose)
        return pose

    H.clip("Idle", 4.0, idle, keys=28)
    H.clip("Move", 2.0, move, keys=20)
    H.clip("Attack", 1.0, attack_fn, keys=18, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"height": height})
