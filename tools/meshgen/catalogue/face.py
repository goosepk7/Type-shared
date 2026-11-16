"""Face pieces: eyelid+brow shells per mood (eye-radius units, eye centre origin, looking -Z) and
mouths per mood (head-radius units, origin = the mouth point on the face; head centre at (0,.4,.86))."""
import numpy as np

from sdf import SDF, capsule, half_space, sphere, tube, union

from . import piece

HEAD_C = (0.0, 0.4, 0.86)


def _lid(cut, brow_pts, brow_r, merge=0.0):
    shell = sphere(1.2) - sphere(1.05)
    lid = shell.si(half_space(1, -1, cut), 0.05).si(half_space(2, 1, 0.35), 0.08)
    brow = tube(brow_pts, brow_r, k=0.05)
    return lid.su(brow, merge) if merge > 0 else (lid | brow)


@piece("lid_neutral", (1.4, 2.0, 1.4), tris=900)
def lid_neutral():
    """Relaxed upper lid with a soft arched brow above."""
    return _lid(0.55, [(-0.95, 1.1, -0.7), (0, 1.38, -0.8), (0.95, 1.1, -0.7)], [0.13, 0.17, 0.13])


@piece("lid_angry", (1.4, 2.0, 1.4), tris=900)
def lid_angry():
    """Heavy lowered lid fused with a thick scowling brow (rolled inward per side in code)."""
    return _lid(0.12, [(-1.05, 0.72, -0.78), (0, 1.0, -0.98), (1.05, 0.72, -0.78)], [0.2, 0.25, 0.2], merge=0.12)


@piece("lid_sleepy", (1.4, 2.0, 1.4), tris=900)
def lid_sleepy():
    """Half-closed drooping lid with a low flat brow."""
    return _lid(-0.12, [(-0.95, 0.95, -0.62), (0, 1.08, -0.75), (0.95, 0.95, -0.62)], [0.12, 0.14, 0.12], merge=0.06)


@piece("lid_scared", (1.4, 2.2, 1.4), tris=900)
def lid_scared():
    """Wide-open thin lid and a brow raised high in a worried arch."""
    return _lid(0.78, [(-0.9, 1.42, -0.55), (0, 1.75, -0.62), (0.9, 1.42, -0.55)], [0.12, 0.15, 0.12])


def _on_face(shape2d, t0=0.95, t1=1.06):
    """Intersect a z-extruded 2D shape with a thin shell of the head sphere."""
    c = np.array(HEAD_C)
    shell = SDF(lambda p: np.maximum(np.linalg.norm(p - c, axis=1) - t1, t0 - np.linalg.norm(p - c, axis=1)))
    flat = SDF(lambda p: shape2d(np.column_stack([p[:, 0], p[:, 1], np.zeros(len(p))])))
    return shell.si(flat, 0.02)


@piece("mouth_neutral", (0.5, 0.4, 0.4), tris=500)
def mouth_neutral():
    """Small content smile."""
    return _on_face(tube([(-0.22, 0.05, 0), (0, -0.04, 0), (0.22, 0.05, 0)], [0.04, 0.055, 0.04], k=0.04))


@piece("mouth_angry", (0.5, 0.4, 0.4), tris=600)
def mouth_angry():
    """Gritted frown: downturned, thicker at the corners."""
    return _on_face(tube([(-0.27, -0.09, 0), (-0.1, 0.03, 0), (0.1, 0.03, 0), (0.27, -0.09, 0)], [0.06, 0.07, 0.07, 0.06], k=0.04))


@piece("mouth_scared", (0.5, 0.4, 0.4), tris=500)
def mouth_scared():
    """Small open 'o' of fright (slightly wobbly)."""
    o = SDF(lambda p: np.sqrt((p[:, 0] / 0.11) ** 2 + (p[:, 1] / 0.14) ** 2) * 0.11 - 0.11)
    return _on_face(o, 0.93, 1.05)


@piece("mouth_sleepy", (0.5, 0.4, 0.4), tris=400)
def mouth_sleepy():
    """Short drowsy squiggle."""
    return _on_face(tube([(-0.13, 0.0, 0), (-0.04, -0.03, 0), (0.05, 0.0, 0), (0.13, -0.02, 0)], [0.035, 0.04, 0.04, 0.035], k=0.03))


def _grin():
    def f(p):
        x, y = p[:, 0], p[:, 1]
        ell = np.sqrt((x / 0.4) ** 2 + (np.minimum(y, 0) / 0.24) ** 2) - 1.0
        return np.maximum(ell * 0.24, y - 0.05)

    return SDF(f).round(0.02)


@piece("mouth_crazy", (0.6, 0.5, 0.45), tris=700)
def mouth_crazy():
    """Huge lopsided D-shaped grin."""
    return _on_face(_grin(), 0.92, 1.05).rot(0, 0, -7)


@piece("teeth_crazy", (0.6, 0.5, 0.45), tris=600)
def teeth_crazy():
    """Upper teeth row for the crazy grin (sits just proud of the mouth)."""
    teeth = union(*[SDF(lambda p, x=x: np.maximum(np.abs(p[:, 0] - x) - 0.045, np.abs(p[:, 1] + 0.01) - 0.06)).round(0.012) for x in np.linspace(-0.3, 0.3, 6)])
    return _on_face(teeth, 1.0, 1.075).rot(0, 0, -7)


# ---- paired lids: both eyes in one piece (one part instead of two). Eye-radius units, origin midway
# between the eyes, eyes at x = +-PAIR_HALF; Luau stretches X to the actual spacing.
PAIR_HALF = 1.4
LIDS = {
    "neutral": (lambda: lid_neutral(), 0.0),
    "angry": (lambda: lid_angry(), 22.0),
    "sleepy": (lambda: lid_sleepy(), -5.0),
    "scared": (lambda: lid_scared(), -18.0),
}


def _pair(left, right):
    (lf, lt), (rf, rt) = left, right
    return lf().rot(0, 0, -lt).at(-PAIR_HALF, 0, 0) | rf().rot(0, 0, rt).at(PAIR_HALF, 0, 0)


@piece("lids2_neutral", (3.0, 2.2, 1.5), tris=1400)
def lids2_neutral():
    """Both relaxed lids + brows in one piece."""
    return _pair(LIDS["neutral"], LIDS["neutral"])


@piece("lids2_angry", (3.0, 2.2, 1.5), tris=1400)
def lids2_angry():
    """Both scowling lids + brows (inner ends lowered)."""
    return _pair(LIDS["angry"], LIDS["angry"])


@piece("lids2_sleepy", (3.0, 2.2, 1.5), tris=1400)
def lids2_sleepy():
    """Both half-closed lids."""
    return _pair(LIDS["sleepy"], LIDS["sleepy"])


@piece("lids2_scared", (3.0, 2.4, 1.5), tris=1400)
def lids2_scared():
    """Both wide-open lids with raised worried brows."""
    return _pair(LIDS["scared"], LIDS["scared"])


@piece("lids2_crazy", (3.0, 2.4, 1.5), tris=1400)
def lids2_crazy():
    """Mismatched lids: left eye wide and raised, right eye scowling."""
    return _pair((LIDS["scared"][0], -22.0), (LIDS["angry"][0], 14.0))
