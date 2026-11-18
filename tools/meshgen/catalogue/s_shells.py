"""Summon set: turtle and tortoise sculpts (Plans/Chelonian).

Unit pieces authored in studs around their lead ellipsoid (`lead=` = the reference size Chelonian.luau gives it):
shells carry the scutes (raised plates with grooves and growth rings, found as a Voronoi split of the dome), the
flared marginal rim, keels and serrations; heads carry the beak; legs and flippers are authored along the
primitive's local +Y (hip -> foot / root -> tip).
"""
import numpy as np

from sdf import *  # noqa: F401,F403
from . import piece


def _surface_pts(rx, ry, rz, pts):
    """Project (x, z) pairs onto the upper surface of the ellipsoid (rx, ry, rz)."""
    out = []
    for x, z in pts:
        u = 1 - (x / rx) ** 2 - (z / rz) ** 2
        out.append((x, ry * np.sqrt(max(u, 0.0)), z))
    return np.array(out, float)


def _scuted(base, centres, groove=0.035, depth=0.03, bump=0.05, rings=0.0, ring_f=40.0):
    """Scutes on a shell: a Voronoi split of the surface by `centres` (3D) - grooves along the cell borders, each plate
    domed a little toward its centre, optional concentric growth rings."""
    C = np.asarray(centres, float)

    def f(p):
        d = base(p)
        D = np.linalg.norm(p[:, None, :] - C[None, :, :], axis=2)
        D.sort(axis=1)
        gap = D[:, 1] - D[:, 0]
        g = np.clip(1 - gap / groove, 0, 1)
        d = d + depth * g * g
        d = d - bump * np.clip(gap / 0.5, 0, 1) ** 0.5 * 0.5
        if rings > 0:
            d = d + rings * np.clip(gap / 0.4, 0, 1) * (0.5 + 0.5 * np.cos(D[:, 0] * ring_f))
        return d
    return SDF(f)


def _shell(W, H, L, base_cut=-0.42, rim=0.07, taper=0.0, rings=0.004, vert=5, cost=4, marg=11, bump=0.05):
    rx, ry, rz = W / 2, H / 2, L / 2

    def dome(p):
        q = p.copy()
        if taper:
            q[:, 0] = q[:, 0] / (1 - taper * np.clip(q[:, 2] / rz, 0, 1))
        return ellipsoid(rx, ry, rz)(q)
    s = SDF(dome)
    # marginal rim flaring out round the lower edge
    s = s.su(ellipsoid(rx * 1.04, ry * 0.18, rz * 1.03, (0, ry * base_cut * 0.6, 0)), rim)
    # scute centres: vertebral row, costal rows, marginal ring
    xz = [(0, rz * (-0.72 + 1.44 * i / (vert - 1))) for i in range(vert)]
    for i in range(cost):
        z = rz * (-0.55 + 1.1 * i / (cost - 1))
        xz += [(rx * 0.58, z), (-rx * 0.58, z)]
    C = list(_surface_pts(rx, ry, rz, xz))
    for i in range(marg):
        a = np.pi * (i + 0.5) / marg
        for sx in (1, -1):
            C.append((sx * rx * 1.0 * np.sin(a), ry * base_cut * 0.45, -rz * 1.0 * np.cos(a)))
    s = _scuted(s, C, groove=0.05 * W / 2.6, depth=0.035 * H / 1.8, bump=bump * H / 1.8, rings=rings)
    return s & half_space(1, -1, ry * base_cut)


@piece("s_turtle_shell_dome", (1.5, 1.05, 1.65), tris=1500, kind="unit", lead=(2.7, 1.9, 3.0), res=160)
def s_turtle_shell_dome():
    """Tortoise / pond turtle carapace (lead: Shell 2.7 x 1.9 x 3.0): a high dome of raised scutes (five vertebrals, four
    costals a side) with growth rings, a ring of marginals flaring at the rim, flat underneath."""
    return _shell(2.7, 1.9, 3.0, rings=0.006)


@piece("s_turtle_shell_flat", (1.4, 0.55, 1.75), tris=1400, kind="unit", lead=(2.5, 0.95, 3.2), res=160)
def s_turtle_shell_flat():
    """Sea turtle carapace (lead: Shell 2.5 x 0.95 x 3.2): a low streamlined teardrop narrowing to the rear, smooth
    scutes with fine grooves."""
    return _shell(2.5, 0.95, 3.2, taper=0.32, rings=0.0, bump=0.03, base_cut=-0.3)


@piece("s_turtle_shell_keel", (1.42, 0.68, 1.62), tris=1500, kind="unit", lead=(2.5, 1.15, 2.9), res=160)
def s_turtle_shell_keel():
    """Snapping turtle / mata mata carapace (lead: Shell 2.5 x 1.15 x 2.9): rough scutes each raised into a knob along
    three keels, the rear margin cut into saw teeth."""
    s = _shell(2.5, 1.15, 2.9, rings=0.0, bump=0.02)
    rx, ry, rz = 1.25, 0.575, 1.45
    for x in (0.0, 0.62, -0.62):
        for z in np.linspace(-0.9, 0.9, 4):
            p = _surface_pts(rx, ry, rz, [(x, z)])[0]
            s = s.su(sphere(0.13, tuple(p + np.array([0, 0.02, 0]))), 0.1)
    for i in range(7):
        a = np.radians(-50 + i * (100 / 6))
        p = (rx * 1.0 * np.sin(a), -0.2, rz * np.cos(a))
        s = s.su(round_cone(p, (p[0] * 1.08, -0.22, p[2] * 1.1), 0.12, 0.03), 0.05)
    return s.noise(0.008, freq=14, seed=21)


@piece("s_turtle_shell_leather", (1.4, 0.55, 1.85), tris=1300, kind="unit", lead=(2.5, 0.95, 3.2), res=160)
def s_turtle_shell_leather():
    """Leatherback / archelon carapace (lead: Shell 2.5 x 0.95 x 3.2): a leathery teardrop drawn out to a point at the
    rear, seven long keels, no scutes."""
    rx, ry, rz = 1.25, 0.475, 1.6

    def dome(p):
        q = p.copy()
        k = 1 - 0.55 * np.clip(q[:, 2] / rz, 0, 1) ** 1.3
        q[:, 0] = q[:, 0] / k
        q[:, 1] = q[:, 1] / (0.6 + 0.4 * k)
        return ellipsoid(rx, ry, rz)(q)
    s = SDF(dome).su(round_cone((0, 0.05, 1.2), (0, 0.0, 1.78), 0.25, 0.04), 0.2)
    for x in (0.0, 0.32, 0.64, 0.95):
        y = ry * np.sqrt(max(0.05, 1 - (x / rx) ** 2))
        ridge = capsule((x, y * 0.98, -1.25), (x * 0.35, y * 0.7, 1.65), 0.05)
        s = s.su(ridge.mirror_x() if x > 0 else ridge, 0.05)
    return (s & half_space(1, -1, -ry * 0.3)).noise(0.004, freq=20, seed=22)


@piece("s_turtle_shell_soft", (1.55, 0.32, 1.68), tris=1100, kind="unit", lead=(2.75, 0.5, 3.0), res=160)
def s_turtle_shell_soft():
    """Softshell / pancake carapace (lead: Shell 2.75 x 0.5 x 3.0): a flat leathery disc with a soft flexible flange round
    the edge and small bumps on the back."""
    rx, ry, rz = 1.375, 0.25, 1.5
    s = ellipsoid(rx * 0.92, ry, rz * 0.92)
    s = s.su(ellipsoid(rx, ry * 0.25, rz, (0, -ry * 0.25, 0)), 0.1)
    rng = np.random.default_rng(23)
    for _ in range(14):
        x, z = rng.uniform(-0.8, 0.8), rng.uniform(-0.9, 0.9)
        if (x / 1.0) ** 2 + (z / 1.1) ** 2 > 0.8:
            continue
        y = ry * np.sqrt(max(0.05, 1 - (x / (rx * 0.92)) ** 2 - (z / (rz * 0.92)) ** 2))
        s = s.su(sphere(0.06, (x, y, z)), 0.05)
    return s & half_space(1, -1, -ry * 0.5)


# ------------------------------------------------------------------------------------------------ heads
def _head(rx, ry, rz, hook=0.0, snap=False):
    s = ellipsoid(rx, ry, rz)
    # beak: a horny edge round the front of the mouth, the upper tip hooking down
    s = s.su(ellipsoid(rx * 0.55, ry * 0.42, rz * 0.3, (0, -ry * 0.28, -rz * 0.78)), rx * 0.25)
    s = s.ss(capsule((-rx * 0.6, -ry * 0.42, -rz * 0.55), (rx * 0.6, -ry * 0.42, -rz * 0.55), ry * 0.04).warp(
        lambda p: np.column_stack([p[:, 0], p[:, 1] - 0.3 * p[:, 0] ** 2, p[:, 2] + 0.6 * p[:, 0] ** 2])), ry * 0.06)
    if hook:
        s = s.su(round_cone((0, -ry * 0.05, -rz * 0.95), (0, -ry * 0.45, -rz * (1.0 + hook)), rx * 0.18, rx * 0.04), rx * 0.1)
    s = s.ss(sphere(rx * 0.06, (rx * 0.12, ry * 0.12, -rz * 0.99)).mirror_x(), rx * 0.03)       # nostrils
    if snap:
        s = s.su(ellipsoid(rx * 0.55, ry * 0.55, rz * 0.5, (rx * 0.45, -ry * 0.1, rz * 0.25)).mirror_x(), rx * 0.3)  # jaw muscles
        s = s.su(ellipsoid(rx * 0.7, ry * 0.25, rz * 0.6, (0, ry * 0.75, -rz * 0.1)), rx * 0.2)                      # skull plates
    # head scales: shallow plate grooves on the crown
    s = s.ss(capsule((0, ry * 0.98, -rz * 0.6), (0, ry * 0.95, rz * 0.4), ry * 0.025), ry * 0.03)
    return s


@piece("s_turtle_head", (0.5, 0.45, 0.62), tris=900, kind="unit", lead=(0.79, 0.69, 1.01), res=130)
def s_turtle_head():
    """Turtle / tortoise head (lead: Head 0.79 x 0.69 x 1.01): a blunt reptile head with a horny beak, a jaw line, nostrils
    at the tip and crown plates."""
    return _head(0.395, 0.345, 0.505, hook=0.12)


@piece("s_turtle_head_snap", (0.66, 0.58, 0.82), tris=1000, kind="unit", lead=(1.02, 0.89, 1.3), res=130)
def s_turtle_head_snap():
    """Snapping turtle head (lead 1.02 x 0.89 x 1.3): massive, wide jaw muscles, a sharply hooked beak, rough plates."""
    return _head(0.51, 0.445, 0.65, hook=0.28, snap=True).noise(0.006, freq=20, seed=24)


@piece("s_matamata_head", (0.8, 0.3, 0.75), tris=900, kind="unit", lead=(1.265, 0.418, 1.21), res=140)
def s_matamata_head():
    """Mata mata head (lead 1.265 x 0.418 x 1.21): a flat triangle with skin frills along the sides and a tubular snout."""
    rx, ry, rz = 0.6325, 0.209, 0.605
    tri = SDF(lambda p: np.abs(p[:, 0]) - rx * (0.35 + 0.65 * np.clip((p[:, 2] + rz) / (2 * rz), 0, 1)))
    s = ellipsoid(rx, ry, rz).si(tri, 0.05)
    for i in range(4):
        z = -rz * 0.5 + i * rz * 0.38
        w = rx * (0.4 + 0.65 * (z + rz) / (2 * rz))
        s = s.su(ellipsoid(0.12, 0.04, 0.1, (w * 0.98, -ry * 0.3, z)).mirror_x(), 0.04)
    return s.noise(0.006, freq=25, seed=25)


# ------------------------------------------------------------------------------------------------ limbs
@piece("s_turtle_leg", (0.48, 0.66, 0.5), tris=900, kind="unit", lead=(0.68, 1.11, 0.626), res=130)
def s_turtle_leg():
    """Tortoise leg (lead: the hip-foot ellipsoid, local +Y down the leg, local +Z front): an elephantine column armoured
    with big scales, a round foot pad with five blunt nails at the front."""
    s = round_cone((0, -0.42, 0), (0, 0.38, 0), 0.32, 0.27)
    s = s.su(ellipsoid(0.36, 0.14, 0.36, (0, 0.46, 0.04)), 0.1)                    # foot pad
    for i in range(5):
        a = np.radians(-50 + i * 25)
        s = s.su(round_cone((0.26 * np.sin(a), 0.48, 0.26 * np.cos(a)), (0.32 * np.sin(a), 0.54, 0.36 * np.cos(a)), 0.06, 0.03), 0.03)
    for y in (-0.25, -0.05, 0.15):                                                   # big front scales
        for x in (-0.12, 0.12):
            s = s.su(ellipsoid(0.1, 0.08, 0.05, (x + (0.06 if y > -0.1 else 0), y, 0.3 - y * 0.06)), 0.04)
    return s.noise(0.006, freq=22, seed=26)


@piece("s_turtle_leg_webbed", (0.42, 0.62, 0.45), tris=700, kind="unit", lead=(0.42, 0.95, 0.39), res=130)
def s_turtle_leg_webbed():
    """Pond turtle leg (lead: the hip-foot ellipsoid, local +Y down, +Z front): a scaly limb ending in a broad webbed foot
    with four claws."""
    s = round_cone((0, -0.4, 0), (0, 0.32, 0.02), 0.2, 0.16)
    s = s.su(ellipsoid(0.26, 0.07, 0.24, (0, 0.42, 0.12)), 0.08)                    # webbed foot
    for i in range(4):
        a = np.radians(-40 + i * 27)
        s = s.su(round_cone((0.18 * np.sin(a), 0.43, 0.12 + 0.2 * np.cos(a)), (0.24 * np.sin(a), 0.46, 0.12 + 0.32 * np.cos(a)), 0.035, 0.012), 0.02)
    return s


@piece("s_turtle_flipper", (0.56, 0.56, 0.24), tris=600, kind="unit", lead=(0.95, 2.47, 0.21), mirror=True, res=140)
def s_turtle_flipper():
    """Sea turtle flipper (lead: the root-tip ellipsoid, local +Y to the tip, -X the leading edge, +Z up; left twin
    mirrored): a long blade, thick and rounded along the leading edge, thin at the trailing edge, sweeping back to a
    point, with scales and a claw on the leading edge."""
    def f(p):
        x, y, z = p[:, 0], p[:, 1], p[:, 2]
        t = np.clip((y + 1.2) / 2.4, 0, 1)
        sweep = 0.22 * t ** 2                                    # the tip sweeps back (+X)
        half = 0.46 * np.sin(np.pi * np.clip(t * 0.95 + 0.05, 0, 1)) ** 0.7 * (1 - 0.35 * t)
        cx = sweep + 0.0
        u = (x - cx) / np.maximum(half, 1e-3)
        thick = 0.1 * (1 - 0.6 * t) * np.clip(1 - (u + 0.3) ** 2 / 1.69, 0, 1) ** 0.5
        d_plan = np.abs(u) - 1.0
        d_th = np.abs(z) - thick
        d = np.maximum(d_plan * np.maximum(half, 0.05), d_th)
        return np.maximum(d, np.abs(y) - 1.22)
    s = SDF(f)
    s = s.su(round_cone((-0.2, -1.05, 0), (-0.25, 0.3, 0), 0.1, 0.05), 0.06)          # leading edge
    s = s.su(round_cone((-0.28, -0.4, 0.02), (-0.36, -0.32, 0.02), 0.04, 0.01), 0.02)   # claw
    return s.noise(0.003, freq=40, seed=27)


@piece("s_tail_spiked", (0.3, 1.2, 0.3), tris=500, kind="unit", lead=(0.42, 2.27, 0.42), res=130)
def s_tail_spiked():
    """Snapping turtle tail (lead 0.42 x 2.27 x 0.42 studs, root -Y): a long tapering tail ringed with rows of knobby
    scales, biggest at the root."""
    s = round_cone((0, -1.1, 0), (0, 1.1, 0), 0.2, 0.035)
    for i in range(8):
        y = -0.95 + i * 0.27
        r = 0.2 - (y + 1.1) / 2.2 * 0.165
        for a in (0, 120, 240):
            ra = np.radians(a + i * 40)
            s = s.su(sphere(r * 0.33, (r * 0.92 * np.cos(ra), y, r * 0.92 * np.sin(ra))), r * 0.2)
    return s
