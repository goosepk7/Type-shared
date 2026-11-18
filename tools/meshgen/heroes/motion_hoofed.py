"""Motion cycles for hoofed animals (horses, deer, cattle, camels, elephants ...), used by hoofkit.ungulate.

Rig (built by hoofkit): Body (centre of mass) -> Loin (hindquarters, spine flex) -> Hip#/Stifle#/Hock#/Fet#B and
Tail1..; Body -> Shoulder#/Knee#F/Fet#F; Body -> Neck -> Head -> Jaw / Ear# / Trunk1..; optional Wing#1/#2.

Sign conventions (model faces -Z): +rx on a downward limb swings its tip FORWARD; +rx on Body pitches the nose UP;
+rx on Loin drops the rump (back rounds / flexes); -rx on the forward-pointing jaw opens it.

Gaits:
  gallop  transverse gallop (LH, RH, LF, RF + suspension) with rocking pitch, spine flex, neck bob.
  bound   pronking / bounding (deer, gazelles): hind pair then fore pair, long suspension.
  trot    diagonal pairs (cattle, pigs, goats, sheep).
  walk    four-beat lateral walk (elephants, rhinos, hippos, giraffes) with roll and head nod.
  pace    lateral pairs (camels, giraffes, llamas): the rolling camel gait.
  fly     wings flap with follow-through, legs tucked and paddling (pegasus).
Attacks: rear (rear up + forehoof strikes), buck (kick back with both hind legs), gore (lower horns and charge),
  butt (rear back on hind legs and slam the head down: goats / rams), stomp (elephant: rear, trunk up, slam down),
  bite (hippo: gape), tusk (boar: low upward slash).
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
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def _bump(x):
    """0 -> 1 -> 0 over x in 0..1 (sin), 0 outside."""
    if x <= 0 or x >= 1:
        return 0.0
    return math.sin(math.pi * x)


def _win(s, a, b):
    """Normalised position of s inside [a, b] (clamped)."""
    return min(max((s - a) / (b - a), 0.0), 1.0)


def front_leg(u, duty, A, fold, reach=0.15):
    """Fore leg over the cycle (u = 0 at touchdown). Returns (shoulder, knee, fetlock) rx.
    Stance: the column sweeps back from +A to -A, straight. Swing: the knee folds back (cannon tucked under the
    forearm), the hoof flips up, then the leg unfolds and reaches forward before touchdown."""
    u = u % 1.0
    if u < duty:
        s = u / duty
        up = A * (1 - 2 * s)
        knee = 0.0
        # fetlock sinks mid-stance, hoof rolls over the toe at push-off
        fet = 0.12 * fold * math.sin(math.pi * s) - 0.35 * fold * max(0.0, (s - 0.75) / 0.25) ** 2
        return up, knee, fet
    s = (u - duty) / (1 - duty)
    up = -A + (2 * A + reach) * _ease(s / 0.8) - reach * _ease((s - 0.8) / 0.2)
    f = _bump(min(s / 0.85, 1.0)) ** 0.8
    knee = -1.55 * fold * f
    fet = -0.9 * fold * f + 0.15 * fold * _bump((s - 0.7) / 0.3)
    return up + 0.25 * fold * f, knee, fet


def hind_leg(u, duty, A, fold, reach=0.1):
    """Hind leg over the cycle (u = 0 at touchdown). Returns (hip, stifle, hock, fetlock) rx. Stifle and hock flex
    together (reciprocal apparatus): the gaskin swings back while the cannon swings forward."""
    u = u % 1.0
    if u < duty:
        s = u / duty
        up = A * (1 - 2 * s)
        push = max(0.0, (s - 0.6) / 0.4)
        return up, 0.1 * fold * push, -0.12 * fold * push, 0.1 * fold * math.sin(math.pi * s) + 0.3 * fold * push ** 2
    s = (u - duty) / (1 - duty)
    up = -A + (2 * A + reach) * _ease(s / 0.85) - reach * _ease((s - 0.85) / 0.15)
    f = _bump(min(s / 0.9, 1.0)) ** 0.8
    return up + 0.1 * fold * f, -0.55 * fold * f, 1.05 * fold * f, -0.85 * fold * f


GAITS = {
    # name: (footfall offsets LH, RH, LF, RF  (touchdown time in the cycle), duty, stride amp, fold)
    "gallop": ((0.0, 0.1, 0.32, 0.44), 0.36, 0.5, 1.0),
    "bound": ((0.0, 0.04, 0.34, 0.38), 0.3, 0.55, 1.0),
    "trot": ((0.0, 0.5, 0.5, 0.0), 0.55, 0.36, 0.75),
    "walk": ((0.0, 0.5, 0.25, 0.75), 0.66, 0.26, 0.55),
    "pace": ((0.0, 0.5, 0.02, 0.52), 0.6, 0.32, 0.65),
    "fly": ((0.0, 0.08, 0.5, 0.58), 0.0, 0.3, 1.0),
}


def ungulate_clips(H, R, gait="gallop", attack="rear", length=None, height=3.2, stride=1.0, fold=1.0, heavy=0.0,
                   idle_len=5.0, flap=1.0):
    """Author Move / Idle / Attack / Hit for a hoofed rig. R = hoofkit rig dict (bone names)."""
    offs, duty, A, fd = GAITS[gait]
    A *= stride
    fd *= fold
    L = length or {"gallop": 0.62, "bound": 0.7, "trot": 0.7, "walk": 1.3, "pace": 1.0, "fly": 0.9}[gait]
    FR, FL, HR, HL = R["FR"], R["FL"], R["HR"], R["HL"]  # leg bone tuples
    loin, neck, head, jaw = R.get("loin"), R.get("neck"), R.get("head"), R.get("jaw")
    tail, ears, trunk = R.get("tail", []), R.get("ears", []), R.get("trunk", [])
    wings = R.get("wings", [])  # [(w1R, w2R), (w1L, w2L)]
    h = height

    def legs_at(pose, u, scale=1.0, airborne=False):
        for (bones, off, front) in ((HL, offs[0], False), (HR, offs[1], False), (FL, offs[2], True), (FR, offs[3], True)):
            ph = u - off
            if airborne:
                # flying: legs tucked and paddling slowly
                w = math.sin(TAU * ph)
                if front:
                    _add(pose, bones[0], (0, 0, 0, 0.55 + 0.25 * w, 0, 0))
                    _add(pose, bones[1], (0, 0, 0, -1.5 - 0.25 * w, 0, 0))
                    _add(pose, bones[2], (0, 0, 0, -0.6, 0, 0))
                else:
                    _add(pose, bones[0], (0, 0, 0, -0.35 + 0.2 * w, 0, 0))
                    _add(pose, bones[1], (0, 0, 0, -0.25, 0, 0))
                    _add(pose, bones[2], (0, 0, 0, 0.55 + 0.15 * w, 0, 0))
                    _add(pose, bones[3], (0, 0, 0, -0.5, 0, 0))
                continue
            if front:
                a, b, c = front_leg(ph, duty, A * scale, fd * scale)
                _add(pose, bones[0], (0, 0, 0, a, 0, 0))
                _add(pose, bones[1], (0, 0, 0, b, 0, 0))
                _add(pose, bones[2], (0, 0, 0, c, 0, 0))
            else:
                a, b, c, d = hind_leg(ph, duty, A * scale, fd * scale)
                _add(pose, bones[0], (0, 0, 0, a, 0, 0))
                _add(pose, bones[1], (0, 0, 0, b, 0, 0))
                _add(pose, bones[2], (0, 0, 0, c, 0, 0))
                _add(pose, bones[3], (0, 0, 0, d, 0, 0))

    def wings_at(pose, u, amp=1.0, glide=0.0):
        for side, (w1, w2) in zip((1, -1), wings):
            ph = TAU * u
            down = math.sin(ph)                      # +1 = top of the stroke
            lag = math.sin(ph - 0.9)                 # the hand follows the arm
            _add(pose, w1, (0, 0.0, 0, 0.0, 0.08 * side * math.cos(ph) * amp, side * (0.55 * down * amp + glide)))
            _add(pose, w2, (0, 0, 0, 0.0, 0.1 * side * math.cos(ph - 0.9) * amp, side * (0.45 * lag * amp + 0.1 * glide)))

    def move(t):
        u = t / L
        pose = {}
        if gait == "fly":
            legs_at(pose, u, airborne=True)
            wings_at(pose, u, flap)
            bob = math.sin(TAU * u - 0.4)
            _add(pose, "Body", (0, 0.08 * h * bob + 0.35 * h, 0, 0.04 * math.sin(TAU * u + 0.6) + 0.05, 0, 0))
            _add(pose, loin, (0, 0, 0, 0.04 * math.sin(TAU * u), 0, 0))
            _add(pose, neck, (0, 0, 0, -0.06 * math.sin(TAU * u + 0.3) - 0.15, 0, 0))
            _add(pose, head, (0, 0, 0, 0.05 * math.sin(TAU * u + 0.8) + 0.1, 0, 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0.12 * math.sin(TAU * u - 0.8 * i) - 0.25 * (i == 0), 0.05 * math.sin(TAU * u * 0.5 - i), 0))
            for i, b in enumerate(ears):
                _add(pose, b, (0, 0, 0, -0.35, 0, 0))
            return pose
        legs_at(pose, u)
        if gait in ("gallop", "bound"):
            # rocking-horse pitch: nose up while the hinds push, nose down as the fores land; highest when gathered
            lift = 0.5 - 0.5 * math.cos(TAU * (u - 0.88 + (0.1 if gait == "bound" else 0)))
            pitch = 0.075 * math.cos(TAU * (u - 0.2))
            _add(pose, "Body", (0, (0.06 * lift - 0.035) * h * (1.4 if gait == "bound" else 1.0), 0, pitch, 0, 0.012 * math.sin(TAU * u)))
            _add(pose, loin, (0, 0, 0, 0.11 * math.cos(TAU * (u - 0.02)), 0, 0))
            nb = math.cos(TAU * (u - 0.55))
            _add(pose, neck, (0, 0, 0, -0.13 * nb - 0.06, 0, 0))
            _add(pose, head, (0, 0, 0, 0.07 * nb + 0.03, 0, 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0.12 * math.cos(TAU * (u - 0.1 - 0.12 * i)) + (0.18 if i == 0 else 0.05), 0.04 * math.sin(TAU * u - i), 0))
            for i, b in enumerate(ears):
                _add(pose, b, (0, 0, 0, -0.18 + 0.05 * math.sin(TAU * u), 0, 0))
        else:
            k = 2 if gait == "trot" else 2
            bob = math.cos(TAU * u * k)
            roll = math.sin(TAU * u) * (0.035 if gait in ("walk", "pace") else 0.015) * (1 + heavy)
            _add(pose, "Body", (0, (0.012 + 0.012 * heavy) * h * bob, 0, 0.012 * math.sin(TAU * u * k + 0.5), 0.02 * math.sin(TAU * u), roll))
            _add(pose, loin, (0, 0, 0, 0.02 * math.sin(TAU * u * k + 1.5), 0.04 * math.sin(TAU * u), -roll * 0.6))
            _add(pose, neck, (0, 0, 0, -0.06 * math.cos(TAU * u * k - 0.7), 0.03 * math.sin(TAU * u), 0))
            _add(pose, head, (0, 0, 0, 0.04 * math.cos(TAU * u * k - 1.0), -0.02 * math.sin(TAU * u), 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0.03 * math.sin(TAU * u * 2 - i), 0.14 * math.sin(TAU * u - 0.7 * i), 0))
            for i, b in enumerate(ears):
                _add(pose, b, (0, 0, 0, 0.06 * math.sin(TAU * u * k + i), 0, 0))
        for i, b in enumerate(trunk):
            _add(pose, b, (0, 0, 0, 0.1 * math.sin(TAU * u - 0.6 * i) * (1 + 0.3 * i) + (0.03 * i), 0.08 * math.sin(TAU * u * 0.5 - 0.5 * i), 0))
        if wings:
            wings_at(pose, 0.25, 0.0, glide=-0.05)
        for k, b in enumerate(R.get("stirrups", [])):
            _add(pose, b, (0, 0, 0, 0.18 * math.sin(TAU * u - 1.2), 0, (1 if k == 0 else -1) * 0.06 * (1 + math.sin(TAU * u * 2))))
        return pose

    def idle(t):
        u = t / idle_len
        pose = {}
        br = math.sin(TAU * u * 3)
        _add(pose, "Body", (0, 0.004 * h * br, 0, 0.004 * br, 0, 0))
        # head: look around, dip as if to graze, come back
        graze = _ease(_win(u, 0.42, 0.55)) - _ease(_win(u, 0.7, 0.85))
        look = math.sin(TAU * u) * (1 - graze)
        _add(pose, neck, (0, 0, 0, -0.8 * graze * R.get("graze", 1.0) + 0.03 * math.sin(TAU * u * 2), 0.12 * look, 0))
        _add(pose, head, (0, 0, 0, -0.3 * graze * R.get("graze", 1.0) + 0.05 * math.sin(TAU * u * 2 + 1), 0.15 * look, 0.06 * math.sin(TAU * u + 2) * (1 - graze)))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.08 * graze * max(0.0, math.sin(TAU * u * 12)), 0, 0))
        # tail swish (flies!)
        sw = _bump(_win(u, 0.15, 0.35)) + _bump(_win(u, 0.62, 0.8))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.02 * math.sin(TAU * u * 2 - i), 0.08 * math.sin(TAU * u * 2 - 0.8 * i) + 0.4 * sw * math.sin(TAU * (u * 5) - 0.9 * i), 0))
        # ear flicks: each ear twitches at its own moments, ears also track the look direction
        for i, b in enumerate(ears):
            side = 1 if i % 2 == 0 else -1
            tw = max(0.0, math.sin(TAU * (u * 3 + i * 0.37))) ** 16
            rot = -0.25 * tw
            if R.get("big_ears"):  # elephant: slow fanning flap of the whole ear
                fan = math.sin(TAU * u * 4 + i * 0.6)
                _add(pose, b, (0, 0, 0, 0, side * (-0.25 * fan - 0.1), 0))
            else:
                _add(pose, b, (0, 0, 0, rot - 0.1 * graze, side * 0.25 * look * 0.5 + 0.35 * tw * side, side * 0.15 * tw))
        for i, b in enumerate(trunk):
            sway = math.sin(TAU * u * 2 - 0.7 * i)
            curl = _bump(_win(u, 0.05, 0.3))
            _add(pose, b, (0, 0, 0, 0.08 * sway + 0.35 * curl * (i / max(1, len(trunk) - 1)) + 0.25 * graze * (i == 0), 0.12 * math.sin(TAU * u - 0.5 * i), 0))
        # weight shift: rest a hind leg
        rest = _bump(_win(u, 0.05, 0.4))
        _add(pose, HL[1], (0, 0, 0, -0.12 * rest * (1 - heavy), 0, 0))
        _add(pose, HL[2], (0, 0, 0, 0.18 * rest * (1 - heavy), 0, 0))
        _add(pose, HL[3], (0, 0, 0, -0.35 * rest * (1 - heavy), 0, 0))
        if wings:
            for side, (w1, w2) in zip((1, -1), wings):
                _add(pose, w1, (0, 0, 0, 0, 0, side * (0.04 * br - 0.05)))
                _add(pose, w2, (0, 0, 0, 0, 0, side * 0.04 * math.sin(TAU * u * 3 - 0.8)))
        if gait == "fly":
            _add(pose, "Body", (0, 0.35 * h + 0.03 * h * math.sin(TAU * u * 4), 0, 0.04, 0, 0))
            wings_at(pose, u * 4, 0.7)
            legs_at(pose, u * 2, airborne=True)
        return pose

    AL = 1.1 if attack in ("rear", "stomp", "butt") else 0.9

    def attack_fn(t):
        s = t / AL
        pose = {}
        rec = 1 - _ease(_win(s, 0.72, 1.0))
        if attack in ("rear", "stomp", "butt"):
            # rear up around the hind hooves: the body pitches up, the hinds stay planted (counter-rotated hips)
            up = _ease(_win(s, 0.0, 0.35)) * rec
            th = (0.62 if attack == "rear" else 0.45 if attack == "stomp" else 0.5) * up
            if attack in ("stomp", "butt"):
                slam = _ease(_win(s, 0.45, 0.62))
                th = th * (1 - slam) - (0.06 if attack == "stomp" else 0.1) * slam * rec
            hy, hz = R["hip_rel"]  # hip relative to the Body pivot (y, z)
            c, sn = math.cos(th), math.sin(th)
            ny, nz = c * hy - sn * hz, sn * hy + c * hz
            _add(pose, "Body", (0, hy - ny - 0.02 * h * up, hz - nz, th, 0, 0))
            for bones in (HL, HR):
                _add(pose, bones[0], (0, 0, 0, -th * 0.9, 0, 0))
                _add(pose, bones[1], (0, 0, 0, -0.15 * up, 0, 0))
                _add(pose, bones[2], (0, 0, 0, 0.3 * up, 0, 0))
                _add(pose, bones[3], (0, 0, 0, 0.1 * up, 0, 0))
            _add(pose, loin, (0, 0, 0, 0.15 * up, 0, 0))
            if attack == "rear":
                # alternating fore-hoof strikes
                for k, bones in enumerate((FR, FL)):
                    pw = math.sin(TAU * (s * 2.2 + 0.5 * k))
                    _add(pose, bones[0], (0, 0, 0, (0.55 + 0.45 * pw) * up, 0, 0))
                    _add(pose, bones[1], (0, 0, 0, (-1.5 - 0.5 * pw) * up, 0, 0))
                    _add(pose, bones[2], (0, 0, 0, -0.6 * up, 0, 0))
                _add(pose, neck, (0, 0, 0, -0.35 * up, 0, 0))
                _add(pose, head, (0, 0, 0, 0.25 * up, 0, 0))
                if jaw:
                    _add(pose, jaw, (0, 0, 0, -0.35 * _bump(_win(s, 0.2, 0.7)), 0, 0))
            else:
                for bones in (FR, FL):
                    _add(pose, bones[0], (0, 0, 0, 0.5 * up * (1 - slam) - 0.1 * slam * rec, 0, 0))
                    _add(pose, bones[1], (0, 0, 0, -0.9 * up * (1 - slam), 0, 0))
                if attack == "stomp":
                    _add(pose, neck, (0, 0, 0, -0.1 * up + 0.15 * slam * rec, 0, 0))
                    for i, b in enumerate(trunk):
                        _add(pose, b, (0, 0, 0, (0.55 * up * (1 - slam) - 0.35 * slam * rec) * (1 + 0.15 * i), 0, 0))
                    if jaw:
                        _add(pose, jaw, (0, 0, 0, -0.3 * up, 0, 0))
                else:
                    _add(pose, neck, (0, 0, 0, 0.3 * up * (1 - slam) - 0.6 * slam * rec, 0, 0))
                    _add(pose, head, (0, 0, 0, 0.25 * up * (1 - slam) - 0.45 * slam * rec, 0, 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0.3 * up, 0, 0))
            for b in ears:
                _add(pose, b, (0, 0, 0, 0.5 * up, 0, 0))
        elif attack == "buck":
            # weight onto the fores, both hinds lash out backwards
            dip = _ease(_win(s, 0.0, 0.25)) * rec
            kick = _bump(_win(s, 0.2, 0.75))
            th = -0.12 * dip - 0.22 * kick
            _add(pose, "Body", (0, 0.05 * h * kick, -0.04 * h * kick, th, 0, 0))
            _add(pose, loin, (0, 0, 0, -0.12 * kick + 0.08 * dip, 0, 0))
            for bones in (HL, HR):
                _add(pose, bones[0], (0, 0, 0, 0.35 * dip * (1 - kick) - 1.05 * kick, 0, 0))
                _add(pose, bones[1], (0, 0, 0, -0.5 * dip * (1 - kick) + 0.35 * kick, 0, 0))
                _add(pose, bones[2], (0, 0, 0, 0.7 * dip * (1 - kick) - 0.2 * kick, 0, 0))
                _add(pose, bones[3], (0, 0, 0, -0.2 * dip + 0.4 * kick, 0, 0))
            for bones in (FR, FL):
                _add(pose, bones[0], (0, 0, 0, -th * 0.9 + 0.08 * kick, 0, 0))
            _add(pose, neck, (0, 0, 0, -0.25 * kick - 0.1 * dip, 0, 0))
            _add(pose, head, (0, 0, 0, -0.1 * kick, 0, 0))
            for b in ears:
                _add(pose, b, (0, 0, 0, 0.6 * (dip + kick), 0, 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0.6 * kick, 0, 0))
        else:  # gore / bite / tusk: lower the head, lunge forward, toss up
            wind = _ease(_win(s, 0.0, 0.3)) * (1 - _ease(_win(s, 0.3, 0.45)))
            lunge = _bump(_win(s, 0.25, 0.85))
            toss = _bump(_win(s, 0.45, 0.85))
            dz = (-0.35 if attack == "gore" else -0.22) * h * lunge
            _add(pose, "Body", (0, -0.03 * h * wind - 0.04 * h * lunge * heavy, dz, -0.05 * wind - 0.05 * lunge + 0.05 * toss, 0, 0))
            for bones in (FR, FL):
                _add(pose, bones[0], (0, 0, 0, -0.25 * wind + 0.25 * lunge, 0, 0))
                _add(pose, bones[1], (0, 0, 0, 0.0, 0, 0))
            for bones in (HL, HR):
                _add(pose, bones[0], (0, 0, 0, 0.25 * wind - 0.35 * lunge, 0, 0))
                _add(pose, bones[2], (0, 0, 0, 0.2 * wind, 0, 0))
            if attack == "bite":
                _add(pose, neck, (0, 0, 0, 0.2 * wind - 0.1 * lunge, 0, 0))
                _add(pose, head, (0, 0, 0, 0.35 * wind + 0.25 * lunge - 0.3 * toss, 0, 0))
                if jaw:
                    _add(pose, jaw, (0, 0, 0, -1.0 * _bump(_win(s, 0.1, 0.6)) - 0.15 * lunge, 0, 0))
            else:
                _add(pose, neck, (0, 0, 0, -0.45 * wind - 0.2 * lunge + 0.55 * toss, 0, 0))
                _add(pose, head, (0, 0, 0, -0.35 * wind - 0.15 * lunge + 0.35 * toss, 0.12 * toss, 0))
                if jaw:
                    _add(pose, jaw, (0, 0, 0, -0.2 * toss, 0, 0))
            for b in ears:
                _add(pose, b, (0, 0, 0, 0.45 * (wind + lunge), 0, 0))
            for i, b in enumerate(trunk):
                _add(pose, b, (0, 0, 0, 0.3 * toss * (1 + 0.3 * i) - 0.1 * wind, 0, 0))
            for i, b in enumerate(tail):
                _add(pose, b, (0, 0, 0, 0.35 * lunge, 0.3 * math.sin(TAU * s * 3 - i) * lunge, 0))
        if wings:
            fl = _bump(_win(s, 0.0, 0.9))
            for side, (w1, w2) in zip((1, -1), wings):
                _add(pose, w1, (0, 0, 0, 0, 0, side * (0.7 * fl * math.sin(TAU * s * 1.5))))
                _add(pose, w2, (0, 0, 0, 0, 0, side * (0.5 * fl * math.sin(TAU * s * 1.5 - 0.8))))
        if gait == "fly":
            _add(pose, "Body", (0, 0.35 * h * (1 - 0.6 * _bump(_win(s, 0.1, 0.9))), 0, 0, 0, 0))
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.3 * s)
        pose = {}
        _add(pose, "Body", (0, -0.02 * h * k, 0.05 * h * k, 0.1 * k, 0, 0.04 * math.sin(t * 40) * k))
        _add(pose, loin, (0, 0, 0, 0.06 * k, 0, 0))
        _add(pose, neck, (0, 0, 0, 0.25 * k, 0.12 * k, 0))
        _add(pose, head, (0, 0, 0, 0.15 * k, 0.1 * k, 0))
        for b in ears:
            _add(pose, b, (0, 0, 0, 0.6 * k, 0, 0))
        for bones in (FR, FL):
            _add(pose, bones[0], (0, 0, 0, -0.1 * k, 0, 0))
        if jaw:
            _add(pose, jaw, (0, 0, 0, -0.2 * k, 0, 0))
        for i, b in enumerate(tail):
            _add(pose, b, (0, 0, 0, 0.25 * k, 0, 0))
        if gait == "fly":
            _add(pose, "Body", (0, 0.35 * h, 0, 0, 0, 0))
        return pose

    H.clip("Move", L, move, keys=24)
    H.clip("Idle", idle_len, idle, keys=30)
    H.clip("Attack", AL, attack_fn, keys=18, loop=False)
    H.clip("Hit", 0.45, hit, keys=8, loop=False)
    H.rig.update({"legsAuthored": True, "height": h})
