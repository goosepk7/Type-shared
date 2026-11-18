"""Motion for the flora / sky-spirit heroes (h_flora.py): waddling plant folk, hopping pumpkins, puffing clouds,
curling smoke, twinkling stars, a rotating sun corona and low-gravity / comet quadrupeds.

Pose values are (px, py, pz, rx, ry, rz) in the parent frame (see motion.py): model faces -Z, +rx on a hanging limb
swings it forward, +rz on a RIGHT arm raises it outward, +ry turns toward the model's left.

* waddle(...): motion.biped with a short stride, a big side-to-side roll as each stubby foot plants, a lagging cap /
  hat jiggle, and a head-butt (cap slam) or staff attack.
* hopper(...): a legless body that springs: crouch, launch with a spin wobble, land with squash; lid / stem pops.
* puffer(...): clouds: motion_monsters.floater plus puffs that swell outward and in like breathing, a big inhale
  then blow (cheek puffs out, body rocks back then surges) as the attack.
* twinkle(...): star / sun: bob, slow tilt, star points flex like little limbs, rays rotate a whole symmetric step per
  loop (seamless), a spin-dash attack.
* beast(...): motion.quadruped plus a streaming tail chain; low=True turns the walk into a floaty low-gravity bound.
"""
import math

import motion
import motion_monsters as mm

TAU = 2 * math.pi
_add = mm._add
ease = mm.ease
bump = mm.bump


def _scale(pose, k):
    for b, v in list(pose.items()):
        pose[b] = tuple(x * k for x in v)
    return pose


# ------------------------------------------------------------------------------------------------ waddle
def waddle(H, legs, arms=(), spine=None, head=None, cap=None, jiggle=(), height=4.0, walk=0.7, stride=0.42, roll=0.12,
           attack="butt", weapon_arm=None):
    """legs (hip, knee, foot, phase); arms (shoulder, elbow, hand, side); cap = a bone carried on top (mushroom cap,
    flower hat) that lags the roll; jiggle = extra bones (spots, petals) that wobble after it."""
    motion.biped(H, legs, arms=arms, spine=spine, head=head, stride=stride, walk=walk, height=height,
                 attack="slam" if attack == "butt" else "punch", weapon_arm=weapon_arm)

    def mv(t):
        u = t / walk
        pose = {}
        w = math.sin(TAU * u)
        _add(pose, "Body", (0, 0.03 * height * abs(w), 0, 0, 0.06 * w, roll * w))
        _add(pose, spine, (0, 0, 0, 0.03 * math.sin(TAU * u * 2), 0, -0.4 * roll * w))
        _add(pose, cap, (0, 0.01 * height * abs(math.sin(TAU * u - 0.6)), 0, 0.06 * math.sin(TAU * u * 2 - 0.9), 0, -0.8 * roll * math.sin(TAU * u - 0.7)))
        for i, b in enumerate(jiggle):
            _add(pose, b, (0, 0, 0, 0.12 * math.sin(TAU * u * 2 - 1.2 - i * 0.4), 0, 0.12 * math.sin(TAU * u - 1.0 - i * 0.6)))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, 0, 0, sg * (0.25 + 0.12 * max(0.0, sg * w))))
        return pose

    def idl(t):
        u = t / 4.0
        pose = {}
        br = math.sin(TAU * u * 2)
        _add(pose, "Body", (0, 0.012 * height * br, 0, 0, 0, 0.03 * math.sin(TAU * u)))
        _add(pose, cap, (0, 0.006 * height * math.sin(TAU * u * 2 - 0.7), 0, 0.03 * math.sin(TAU * u * 2 - 0.8), 0.06 * math.sin(TAU * u), -0.05 * math.sin(TAU * u - 0.6)))
        for i, b in enumerate(jiggle):
            _add(pose, b, (0, 0, 0, 0.06 * math.sin(TAU * u * 2 - 1 - i * 0.5), 0, 0.06 * math.sin(TAU * u - i)))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, 0.05 * math.sin(TAU * u + side), 0, sg * 0.12))
        return pose

    mm.overlay(H, "Move", mv)
    mm.overlay(H, "Idle", idl)
    if attack == "butt":
        # rear up, then slam the heavy cap forward like a head-butt; the cap lags and overshoots
        def atk(t):
            s = t / 0.9
            pose = {}
            wind = ease(s / 0.4) * (1 - ease((s - 0.4) / 0.12))
            strike = bump(s, 0.36, 0.8)
            rec = 1 - ease((s - 0.72) / 0.28)
            _add(pose, "Body", (0, 0.06 * height * wind, (0.05 * wind - 0.12 * strike) * height, 0.3 * wind - 0.55 * strike, 0, 0))
            _add(pose, spine, (0, 0, 0, 0.1 * wind - 0.2 * strike, 0, 0))
            _add(pose, cap, (0, 0, 0, 0.15 * wind - 0.3 * bump(s, 0.42, 0.9), 0, 0))
            for i, b in enumerate(jiggle):
                _add(pose, b, (0, 0, 0, -0.3 * bump(s, 0.45, 0.95), 0, 0))
            for hip, knee, foot, ph in legs:
                _add(pose, hip, (0, 0, 0, (0.4 if ph == 0 else -0.3) * strike, 0, 0))
                _add(pose, knee, (0, 0, 0, -0.35 * strike - 0.25 * wind, 0, 0))
            for sh, el, hd, side in arms:
                sg = 1 if side > 0 else -1
                _add(pose, sh, (0, 0, 0, -0.5 * wind + 0.9 * strike, 0, sg * 0.5 * wind))
            return _scale(pose, rec)

        H.clip("Attack", 0.9, atk, keys=16, loop=False)
    H.rig.update({"legs": [{"hip": l[0], "knee": l[1], "phase": l[3], "side": 1 if i == 0 else -1} for i, l in enumerate(legs)]})


# ------------------------------------------------------------------------------------------------ hopper
def hopper(H, top=None, lid=None, tendrils=(), face=None, height=3.0, period=0.75, spin=0.35):
    """Legless springer (pumpkins, sprites): Body launches, `top` squashes on landing, the lid / stem pops on the
    way up, tendrils trail."""

    def idle(t):
        u = t / 2.6
        pose = {}
        w = math.sin(TAU * u)
        _add(pose, "Body", (0, 0.02 * height * max(0.0, w) ** 2, 0, 0, 0.12 * math.sin(TAU * u * 0.5), 0.05 * math.sin(TAU * u)))
        _add(pose, top, (0, -0.02 * height * max(0.0, -w), 0, 0.04 * math.sin(TAU * u + 1), 0, 0))
        _add(pose, lid, (0, 0.03 * height * max(0.0, math.sin(TAU * u * 2 - 0.5)) ** 4, 0, 0.1 * math.sin(TAU * u - 0.4), 0, 0.12 * math.sin(TAU * u * 0.5)))
        _add(pose, face, (0, 0, 0, 0.04 * math.sin(TAU * u + 2), 0.08 * math.sin(TAU * u * 0.5 + 1), 0))
        for i, b in enumerate(tendrils):
            _add(pose, b, (0, 0, 0, 0.18 * math.sin(TAU * u + i * 1.3), 0.1 * math.sin(TAU * u * 0.5 + i), 0.15 * math.sin(TAU * u - i * 0.9)))
        return pose

    def move(t):
        u = t / period
        pose = {}
        ph = TAU * u
        air = max(0.0, math.sin(ph))
        squash = max(0.0, -math.sin(ph))
        _add(pose, "Body", (0, 0.3 * height * air, 0, -0.18 * math.cos(ph), spin * math.sin(ph * 0.5) * air, 0.08 * math.sin(ph)))
        _add(pose, top, (0, -0.07 * height * squash, 0, 0.12 * math.cos(ph - 0.4), 0, 0))
        _add(pose, lid, (0, 0.06 * height * max(0.0, math.cos(ph - 0.3)) * air, 0, 0.25 * math.cos(ph - 0.6), 0, 0.15 * math.sin(ph)))
        for i, b in enumerate(tendrils):
            _add(pose, b, (0, 0, 0, -0.35 * math.cos(ph - 0.7 - i * 0.3), 0, 0.2 * math.sin(ph - i)))
        return pose

    def attack_fn(t):
        s = t / 0.85
        pose = {}
        wind = ease(s / 0.35) * (1 - ease((s - 0.35) / 0.1))
        strike = bump(s, 0.32, 0.78)
        rec = 1 - ease((s - 0.7) / 0.3)
        _add(pose, "Body", (0, (-0.08 * wind + 0.2 * strike) * height, -0.5 * height * strike, 0.2 * wind - 0.6 * strike, 0, 0))
        _add(pose, top, (0, -0.1 * height * wind, 0, 0, 0, 0))
        _add(pose, lid, (0, 0.18 * height * bump(s, 0.3, 0.7), 0, -0.6 * bump(s, 0.3, 0.75), 0, 0))
        _add(pose, face, (0, 0, 0, -0.2 * strike, 0, 0))
        for i, b in enumerate(tendrils):
            _add(pose, b, (0, 0, 0, 0.8 * wind - 1.2 * strike, 0, 0))
        return _scale(pose, rec)

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, -0.03 * height * k, 0.1 * height * k, 0.25 * k, 0, 0.12 * math.sin(t * 40) * k))
        _add(pose, lid, (0, 0.08 * height * k, 0, 0.4 * k, 0, 0))
        return pose

    H.clip("Idle", 2.6, idle, keys=20)
    H.clip("Move", period, move, keys=16)
    H.clip("Attack", 0.85, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"height": height})


# ------------------------------------------------------------------------------------------------ puffer (clouds, smoke)
def puffer(H, arms=(), spine=None, head=None, tail=(), puffs=(), cheeks=(), height=4.0, hover=0.4, lean=0.18, swirl=0.0):
    """puffs: (bone, outward unit vector) that swell and settle out of phase (breathing cloud masses);
    cheeks: bones that bulge on the inhale before the blow attack. swirl > 0 adds a corkscrew sway (smoke)."""
    mm.floater(H, arms=arms, spine=spine, head=head, tail=tail, height=height, hover=hover, lean=lean)

    def breathe(u, amt, rate=1):
        pose = {}
        for i, (b, d) in enumerate(puffs):
            k = amt * 0.035 * height * (0.5 + 0.5 * math.sin(TAU * u * rate - i * 1.1))
            _add(pose, b, (d[0] * k, d[1] * k, d[2] * k, 0, 0, 0.05 * math.sin(TAU * u * rate - i)))
        if swirl:
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0, swirl * 0.35 * math.sin(TAU * u - i * 1.2), 0))
            _add(pose, spine, (0, 0, 0, 0, swirl * 0.12 * math.sin(TAU * u - 0.4), swirl * 0.05 * math.sin(TAU * u)))
        return pose

    mm.overlay(H, "Idle", lambda t: breathe(t / 4.0, 1.0, 2))
    mm.overlay(H, "Move", lambda t: breathe(t / 1.6, 1.4, 2))

    def blow(t):
        s = t / 1.1
        pose = {}
        inhale = ease(s / 0.45) * (1 - ease((s - 0.45) / 0.12))
        gust = bump(s, 0.42, 0.95)
        rec = 1 - ease((s - 0.8) / 0.2)
        _add(pose, "Body", (0, 0.05 * height * inhale, (0.12 * inhale - 0.2 * gust) * height, 0.25 * inhale - 0.3 * gust, 0, 0))
        _add(pose, spine, (0, 0, 0, 0.12 * inhale - 0.15 * gust, 0, 0))
        _add(pose, head, (0, 0, 0, 0.2 * inhale - 0.25 * gust, 0, 0))
        for b, d in puffs:
            k = 0.06 * height * inhale - 0.02 * height * gust
            _add(pose, b, (d[0] * k, d[1] * k, d[2] * k, 0, 0, 0))
        for i, b in enumerate(cheeks):
            sg = 1 if i % 2 == 0 else -1
            k = 0.05 * height * (inhale + 0.6 * gust)
            _add(pose, b, (sg * k * 0.6, 0, -k * 0.3, 0, 0, 0))
        for sh, el, hd, side in arms:
            sg = 1 if side > 0 else -1
            _add(pose, sh, (0, 0, 0, -0.4 * inhale + 1.4 * gust, 0, sg * (0.7 * inhale + 0.1 * gust)))
            _add(pose, el, (0, 0, 0, 0.6 * inhale - 0.2 * gust, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, -0.2 * inhale + 0.4 * gust, 0.25 * math.sin(TAU * s * 2 - i), 0))
        return _scale(pose, rec)

    H.clip("Attack", 1.1, blow, keys=18, loop=False)


# ------------------------------------------------------------------------------------------------ twinkle (star / sun)
def twinkle(H, points=(), rays=None, ray_step=0.0, face=None, height=3.0, hover=0.5, dash=True, extra=()):
    """points: (bone, side) star arms / legs that flex; rays: a bone spun about the facing axis by ray_step (one
    symmetric step) per loop; extra: (bone, phase) small orbiting sparkles that bob."""

    def body(pose, u, amt=1.0):
        _add(pose, "Body", (0, hover * height * 0.12 + 0.05 * height * math.sin(TAU * u), 0, 0.05 * math.sin(TAU * u + 1), 0, 0.08 * amt * math.sin(TAU * u * 0.5)))
        for i, (b, side) in enumerate(points):
            _add(pose, b, (0, 0, 0, 0.12 * amt * math.sin(TAU * u * 2 + i * 1.3), 0, 0.15 * amt * math.sin(TAU * u + i * 1.7)))
        for b, ph in extra:
            _add(pose, b, (0, 0.04 * height * math.sin(TAU * u * 2 + ph), 0, 0, 0, 0))
        _add(pose, face, (0, 0, 0, 0.04 * math.sin(TAU * u + 2), 0.1 * math.sin(TAU * u * 0.5 + 0.3), 0))

    def idle(t):
        u = t / 4.0
        pose = {}
        body(pose, u)
        _add(pose, rays, (0, 0, 0, 0, 0, ray_step * u))
        return pose

    def move(t):
        u = t / 1.2
        pose = {}
        body(pose, u * 2 % 1.0, 1.5)
        _add(pose, "Body", (0, 0, 0, -0.25, 0.1 * math.sin(TAU * u), 0.12 * math.sin(TAU * u)))
        _add(pose, rays, (0, 0, 0, 0, 0, ray_step * u))
        return pose

    def attack_fn(t):
        s = t / 0.9
        pose = {}
        wind = ease(s / 0.3) * (1 - ease((s - 0.3) / 0.1))
        strike = bump(s, 0.28, 0.85)
        rec = 1 - ease((s - 0.75) / 0.25)
        spin = TAU * ease((s - 0.28) / 0.5) if dash else 0.0
        _add(pose, "Body", (0, 0.05 * height * wind, (0.1 * wind - 0.45 * strike) * height, 0.2 * wind - 0.3 * strike, 0, 0))
        for i, (b, side) in enumerate(points):
            _add(pose, b, (0, 0, 0, -0.4 * wind + 0.3 * strike, 0, 0.3 * wind * (1 if side > 0 else -1)))
        _add(pose, face, (0, 0, 0, 0.2 * wind, 0, 0))
        pose = _scale(pose, rec)
        # a full barrel spin about the facing axis (whole turn = seamless at both ends)
        _add(pose, "Body", (0, 0, 0, 0, 0, spin))
        _add(pose, rays, (0, 0, 0, 0, 0, ray_step * 2 * s))
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, 0, 0.12 * height * k, 0.3 * k, 0, 0.15 * math.sin(t * 40) * k))
        for i, (b, side) in enumerate(points):
            _add(pose, b, (0, 0, 0, 0.3 * k, 0, 0))
        return pose

    H.clip("Idle", 4.0, idle, keys=20)
    H.clip("Move", 1.2, move, keys=16)
    H.clip("Attack", 0.9, attack_fn, keys=18, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"height": height})


# ------------------------------------------------------------------------------------------------ quadruped beasts
def beast(H, legs, spine=None, neck=None, head=None, jaw=None, tail=(), ears=(), height=3.0, walk=0.8, stride=0.45,
          low=False, stream=0.0):
    """motion.quadruped + tail streaming behind (comet: stream > 0 keeps the tail lifted and rippling); low = a
    floaty low-gravity bound for the Move clip (all four legs gathered then stretched, long hang time)."""
    motion.quadruped(H, legs, spine=spine, neck=neck, head=head, jaw=jaw, tail=tail, ears=ears, stride=stride, walk=walk,
                     height=height, attack="pounce")

    def tailwave(u, amp):
        pose = {}
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, -stream * 0.15 + amp * 0.08 * math.sin(TAU * u * 2 - i * 0.9), amp * 0.1 * math.sin(TAU * u - i * 0.8), 0.05 * amp * math.sin(TAU * u * 2 - i)))
        return pose

    if stream:
        mm.overlay(H, "Idle", lambda t: tailwave(t / 4.8, 1.0))
        mm.overlay(H, "Move", lambda t: tailwave(t / walk, 1.8))
    if low:
        period = walk * 1.6

        def bound(t):
            u = t / period
            pose = {}
            ph = TAU * u
            air = max(0.0, math.sin(ph))
            gather = max(0.0, -math.sin(ph))
            _add(pose, "Body", (0, 0.22 * height * air ** 0.7, 0, 0.12 * math.cos(ph), 0, 0.03 * math.sin(ph)))
            _add(pose, spine, (0, 0, 0, -0.1 * math.cos(ph), 0, 0))
            _add(pose, neck, (0, 0, 0, -0.08 * math.cos(ph - 0.4), 0, 0))
            _add(pose, head, (0, 0, 0, 0.1 * math.cos(ph - 0.6), 0, 0))
            for up, lo, ft, phase, front in legs:
                sg = 1 if front else -1
                stretch = math.cos(ph) * 0.55
                _add(pose, up, (0, 0, 0, sg * stretch * 0.9 + (0.2 if front else -0.2) * gather, 0, 0))
                _add(pose, lo, (0, 0, 0, (-0.6 if front else 0.6) * gather + (-0.25 if front else 0.2) * air, 0, 0))
                _add(pose, ft, (0, 0, 0, (0.5 if front else -0.4) * air, 0, 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, -0.25 * math.cos(ph - 0.8 - i * 0.4), 0, 0))
            for b in ears:
                _add(pose, b, (0, 0, 0, -0.3 * math.cos(ph - 0.7), 0, 0))
            return pose

        H.clip("Move", period, bound, keys=20)
