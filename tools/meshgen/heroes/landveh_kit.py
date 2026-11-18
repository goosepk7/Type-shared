"""Hard-surface kit for the land-vehicle hero families (h_cars, h_trucks, h_rail, h_rides).

Everything here builds DIRECT meshes (tools/meshgen/direct.py style: explicit vertices + exact normals, so a
bevelled panel stays crisp at a few hundred triangles) and hands them to Hero.piece as the piece "shape".

heroes/build.py was written for SDF pieces: it probes every shape on a grid to find its bounds, then wraps it in a
recentring SDF before calling mesher.build. Two small adapters make direct meshes go through it unchanged:
  * DMesh: a trimesh that is also callable (the box SDF of its own bounds) for the bounds probe;
  * a wrapper around mesher.build that recognises that recentring lambda around a DMesh and hands the (shifted)
    mesh to mesher.finish_direct instead of marching cubes.
Neither kit.py nor build.py is changed; SDF pieces of every other family take the original path.

Geometry: box / cyl / rod / bar / extrude (side-profile slab with rounded bevels) / warp (any deformation with
exact normal transport, keeps hard edges) / lathe_profile (surface of revolution from a 2D outline, hard corners
allowed) / tyre / rim / torus / seat / steering wheel / lamps.
Motion: vehicle_clips (wheels spinning, suspension bob, body roll, idle engine shake, ram/honk attack, jolt hit),
plus helpers for tracks and legs used by the families.
"""
from __future__ import annotations

import math

import numpy as np
import trimesh

import direct as D
import mesher
import sdf as S

TAU = 2 * math.pi


# ================================================================================================ DMesh adapter
class DMesh(trimesh.Trimesh):
    """A direct mesh that build.py can probe like an SDF (box distance to its own bounds)."""

    def __call__(self, P):
        lo, hi = self.bounds
        c, h = (lo + hi) / 2, (hi - lo) / 2 + 1e-3
        q = np.abs(P - c) - h
        return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0)


def dm(m):
    o = DMesh(np.asarray(m.vertices, float), np.asarray(m.faces, int), process=False)
    o.direct_normals = np.asarray(m.direct_normals, float)
    return o


_orig_build = mesher.build


def _build(sdf, box, *a, **kw):
    f = getattr(sdf, "f", None)
    cl = getattr(f, "__closure__", None)
    if isinstance(sdf, S.SDF) and cl:
        cells = []
        for c in cl:
            try:
                cells.append(c.cell_contents)
            except ValueError:
                pass
        dms = [c for c in cells if isinstance(c, DMesh)]
        offs = [c for c in cells if isinstance(c, np.ndarray) and c.shape == (3,)]
        if dms and offs:
            m = D.moved(dms[0], offset=-offs[0])
            return mesher.finish_direct(m, kw.get("fit"))
    return _orig_build(sdf, box, *a, **kw)


# chain onto any other kit's wrapper (airsea_kit also wraps mesher.build, under the same function name)
if not getattr(mesher, "_landveh_patched", False):
    mesher.build = _build
    mesher._landveh_patched = True


# ================================================================================================ transforms
def rot(rx=0.0, ry=0.0, rz=0.0):
    """Rotation matrix from degrees (applied X, then Y, then Z)."""
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    X = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Y = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Z = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Z @ Y @ X


def xf(m, pos=(0, 0, 0), r=None, scale=(1, 1, 1)):
    R = rot(*r) if r is not None and len(np.shape(r)) == 1 else r
    return D.moved(m, offset=pos, rot=R, scale=scale)


def merge(*ms):
    ms = [m for m in ms if m is not None]
    if not ms:
        return None
    if len(ms) == 1:
        return ms[0]
    return D.merge(*ms)


def mirror(m):
    f = np.array([-1.0, 1.0, 1.0])
    return D._finish(m.vertices * f, m.direct_normals * f, m.faces[:, ::-1])


def mirrored_pair(m):
    """The mesh plus its x-mirror (both sides in one piece)."""
    return merge(m, mirror(m))


def warp(m, fn, eps=1e-4):
    """Deform vertices with fn(V) -> V'. Normals are carried by the inverse-transpose Jacobian (finite
    differences), so hard edges stay hard and flat faces stay flat-shaded."""
    V = np.asarray(m.vertices, float)
    N = np.asarray(m.direct_normals, float)
    V2 = fn(V.copy())
    J = np.zeros((len(V), 3, 3))
    for i in range(3):
        d = np.zeros(3)
        d[i] = eps
        J[:, :, i] = (fn(V + d) - fn(V - d)) / (2 * eps)
    j0, j1, j2 = J[:, :, 0], J[:, :, 1], J[:, :, 2]
    # adjugate transpose (= det * inv(J)^T, defined for flattening maps too): columns j1 x j2, j2 x j0, j0 x j1
    N2 = np.cross(j1, j2) * N[:, :1] + np.cross(j2, j0) * N[:, 1:2] + np.cross(j0, j1) * N[:, 2:3]
    det = np.einsum("ni,ni->n", j0, np.cross(j1, j2))
    N2 = N2 * np.where(det < 0, -1.0, 1.0)[:, None]
    bad = np.linalg.norm(N2, axis=1) < 1e-9
    N2[bad] = N[bad]
    N2 /= np.maximum(np.linalg.norm(N2, axis=1, keepdims=True), 1e-12)
    return D._finish(V2, N2, m.faces)


# ================================================================================================ primitives
def cbox(size, pos=(0, 0, 0), c=0.03, rot_=None):
    """Chamfered box (44 triangles, flat shaded facets): the cheap crisp block for small details."""
    h = np.asarray(size, float) / 2
    c = min(c, h.min() * 0.45)
    pts = []
    for ax in range(3):
        u, v = [a for a in range(3) if a != ax]
        for sgn in (-1, 1):
            for su in (-1, 1):
                for sv in (-1, 1):
                    p = np.zeros(3)
                    p[ax] = sgn * h[ax]
                    p[u] = su * (h[u] - c)
                    p[v] = sv * (h[v] - c)
                    pts.append(p)
    hull = trimesh.convex.convex_hull(np.array(pts))
    tri = hull.vertices[hull.faces]
    fn = hull.face_normals
    V = tri.reshape(-1, 3)
    N = np.repeat(fn, 3, axis=0)
    F = np.arange(len(V)).reshape(-1, 3)
    return xf(D._finish(V, N, F), pos, rot_)


def box(size, pos=(0, 0, 0), r=0.05, rot_=None, seg=None):
    sz = np.asarray(size, float)
    if seg is None:
        seg = 0 if sz.max() < 0.6 else 1
    r = min(r, sz.min() * 0.45)
    return xf(D.rounded_box(sz, r, seg), pos, rot_)


def cyl(length, radius, pos=(0, 0, 0), axis="x", bevel=0.04, segs=20, r=None):
    ax = "xyz".index(axis)
    return xf(D.bevel_cylinder(length, radius, min(bevel, radius * 0.5, length * 0.45), segs, ax), pos, r)


def _frame(p0, p1, up=(0, 1, 0)):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    z = d / L
    u = np.asarray(up, float)
    if abs(z @ u) > 0.95:
        u = np.array([1.0, 0, 0]) if abs(z[0]) < 0.9 else np.array([0, 0, 1.0])
    x = np.cross(u, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.column_stack([x, y, z]), (p0 + p1) / 2, L


def bar(p0, p1, w, h=None, r=0.03, up=(0, 1, 0), ext=0.0, round_=False):
    """Square bar from p0 to p1 (w across, h along `up`); ext lengthens both ends. Chamfered (cheap) unless round_."""
    R, c, L = _frame(p0, p1, up)
    h = w if h is None else h
    if not round_:
        return D.moved(cbox((w, h, L + 2 * ext), (0, 0, 0), c=min(r, w * 0.3, h * 0.3)), offset=c, rot=R)
    return D.moved(D.rounded_box((w, h, L + 2 * ext), min(r, w * 0.45, h * 0.45), 1), offset=c, rot=R)


def rod(p0, p1, radius, segs=10, bevel=0.02, ext=0.0):
    R, c, L = _frame(p0, p1)
    return D.moved(D.bevel_cylinder(L + 2 * ext, radius, min(bevel, radius * 0.5), segs, 2), offset=c, rot=R)


def _ear_clip(P):
    """Triangulate a simple CCW polygon (K, 2) -> list of index triples."""
    idx = list(range(len(P)))
    tris = []

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        n = len(idx)
        cut = False
        for k in range(n):
            i0, i1, i2 = idx[(k - 1) % n], idx[k], idx[(k + 1) % n]
            a, b, c = P[i0], P[i1], P[i2]
            if cross(a, b, c) <= 1e-12:
                continue
            ok = True
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                p = P[j]
                if cross(a, b, p) >= -1e-12 and cross(b, c, p) >= -1e-12 and cross(c, a, p) >= -1e-12:
                    ok = False
                    break
            if ok:
                tris.append((i0, i1, i2))
                idx.pop(k)
                cut = True
                break
        if not cut:  # degenerate: drop the flattest vertex
            idx.pop(0)
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


def round_poly(pts, radii, seg=3):
    """Round the corners of a polygon: radii is a number or a list per vertex (0 = keep sharp)."""
    P = np.asarray(pts, float)
    n = len(P)
    rr = [radii] * n if np.isscalar(radii) else list(radii)
    out = []
    for i in range(n):
        r = rr[i]
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        if r <= 0:
            out.append(b)
            continue
        u, v = a - b, c - b
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        u, v = u / lu, v / lv
        ang = math.acos(np.clip(u @ v, -1, 1))
        if ang > math.pi - 1e-3 or ang < 1e-3:
            out.append(b)
            continue
        t = r / math.tan(ang / 2)
        t = min(t, lu * 0.49, lv * 0.49)
        r = t * math.tan(ang / 2)
        p0, p1 = b + u * t, b + v * t
        bis = (u + v) / np.linalg.norm(u + v)
        cc = b + bis * (r / math.sin(ang / 2))
        a0 = math.atan2(*(p0 - cc)[::-1])
        a1 = math.atan2(*(p1 - cc)[::-1])
        da = (a1 - a0 + math.pi) % TAU - math.pi
        for k in range(seg + 1):
            th = a0 + da * k / seg
            out.append(cc + r * np.array([math.cos(th), math.sin(th)]))
    return np.array(out)


def extrude(poly, width, bevel=0.06, axis="x", center=0.0, seg=2, hard_deg=38.0):
    """Slab: a 2D outline extruded `width` across `axis` with rounded bevels on both rims.
    axis "x": poly is in (z, y) (a SIDE profile, the usual way to draw a vehicle body);
    axis "z": poly is in (x, y) (a FRONT profile); axis "y": poly is in (x, z) (a PLAN outline)."""
    P = np.asarray(poly, float)
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    if area < 0:
        P = P[::-1]
    # drop duplicate consecutive points
    keep = [0]
    for i in range(1, len(P)):
        if np.linalg.norm(P[i] - P[keep[-1]]) > 1e-6:
            keep.append(i)
    P = P[keep]
    if np.linalg.norm(P[0] - P[-1]) < 1e-6:
        P = P[:-1]
    n = len(P)
    E = np.roll(P, -1, 0) - P
    En = np.column_stack([E[:, 1], -E[:, 0]])
    En /= np.maximum(np.linalg.norm(En, axis=1, keepdims=True), 1e-12)  # outward edge normals (CCW)
    Vn = En + np.roll(En, 1, 0)
    Vn /= np.maximum(np.linalg.norm(Vn, axis=1, keepdims=True), 1e-12)
    turn = np.degrees(np.arccos(np.clip((En * np.roll(En, 1, 0)).sum(1), -1, 1)))
    hard = turn > hard_deg
    b = min(bevel, width * 0.45)
    miter = 1.0 / np.maximum((Vn * En).sum(1), 0.35)
    Q = P - Vn * (b * miter)[:, None]
    hw = width / 2
    V, N, F = [], [], []

    # map (u, v, w) = (profile coord 0, profile coord 1, across) -> xyz
    def to3(u, v, w):
        if axis == "x":
            return (w, v, u)
        if axis == "z":
            return (u, v, w)
        return (u, w, v)

    phis = [math.pi / 2 * k / seg for k in range(seg + 1)]
    # band around the outline
    for i in range(n):
        j = (i + 1) % n
        cols = []
        for vi, en in ((i, En[i]), (j, En[i])):
            nrm2 = en if hard[vi] else Vn[vi]
            col = []
            for side in (-1, 1):
                ph_list = phis[::-1] if side < 0 else phis
                for ph in ph_list:
                    cn = math.cos(ph)
                    sn = math.sin(ph)
                    base = Q[vi]
                    off2 = (P[vi] - Q[vi]) * cn  # reaches the true outline at ph = 0
                    xx = side * (hw - b + b * sn)
                    pos2 = base + off2
                    nn2 = nrm2 * cn
                    col.append((to3(pos2[0], pos2[1], xx), to3(nn2[0], nn2[1], side * sn)))
            cols.append(col)
        c0, c1 = cols
        base = len(V)
        for (p, nn) in c0 + c1:
            V.append(p)
            N.append(nn)
        m = len(c0)
        for k in range(m - 1):
            a0, a1, b0, b1 = base + k, base + k + 1, base + m + k, base + m + k + 1
            F += [[a0, b0, b1], [a0, b1, a1]]
    # caps
    tris = _ear_clip(Q)
    for side in (-1, 1):
        base = len(V)
        for q in Q:
            V.append(to3(q[0], q[1], side * hw))
            N.append(to3(0, 0, side))
        for t in tris:
            F.append([base + t[0], base + t[1], base + t[2]])
    m = D._finish(np.array(V, float), np.array(N, float), np.array(F, int))
    m = _orient(m)
    if center:
        o = [0, 0, 0]
        o["xyz".index(axis)] = center
        m = xf(m, o)
    return m


def _orient(m):
    """Flip triangles whose winding disagrees with the stored normals."""
    V, N, F = m.vertices, m.direct_normals, m.faces.copy()
    tri = V[F]
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    vn = N[F].sum(1)
    bad = (fn * vn).sum(1) < 0
    F[bad] = F[bad][:, ::-1]
    keep = np.linalg.norm(fn, axis=1) > 1e-14
    return D._finish(V, N, F[keep])


def lathe_profile(pts, segs=24, axis="x", closed=False, hard=(), hard_deg=50.0):
    """Surface of revolution of a 2D outline [(t, r), ...] about `axis`. Normals follow the outline (smooth),
    split at corners sharper than hard_deg or listed in `hard`. closed: the outline is a loop (tyre, torus)."""
    P = np.asarray(pts, float)
    n = len(P)
    if closed:
        area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
        sgn = 1.0 if area > 0 else -1.0
    else:
        # open outline from the axis back to the axis; outward is "away from the axis" for a convex hull
        sgn = None
    prof = []
    rng = range(n) if closed else range(n - 1)
    edges = []
    for i in rng:
        j = (i + 1) % n
        d = P[j] - P[i]
        L = np.linalg.norm(d)
        if L < 1e-9:
            continue
        nn = np.array([d[1], -d[0]]) / L
        edges.append((i, j, nn))
    if not closed:
        # pick the sign so normals point away from the axis on average
        s = sum(e[2][1] * (np.linalg.norm(P[e[1]] - P[e[0]])) for e in edges)
        sgn = 1.0 if s >= 0 else -1.0
    edges = [(i, j, nn * sgn) for i, j, nn in edges]
    # vertex normals: average of adjacent edge normals unless the corner is hard
    ne = len(edges)
    for k, (i, j, nn) in enumerate(edges):
        prv = edges[k - 1][2] if (closed or k > 0) else None
        nxt = edges[(k + 1) % ne][2] if (closed or k < ne - 1) else None

        def vn(other, idx):
            if other is None:
                return nn
            ang = math.degrees(math.acos(np.clip(other @ nn, -1, 1)))
            if ang > hard_deg or idx in hard:
                return nn
            v = other + nn
            return v / np.linalg.norm(v)

        prof.append((P[i][0], P[i][1], *vn(prv, i)))
        prof.append((P[j][0], P[j][1], *vn(nxt, j)))
    m = D.lathe(prof, segs, "xyz".index(axis))
    return _orient(m)


def torus(R, r, axis="x", segs=24, rsegs=8, pos=(0, 0, 0)):
    pts = [(r * math.cos(a), R + r * math.sin(a)) for a in np.linspace(0, TAU, rsegs, endpoint=False)]
    return xf(lathe_profile(pts, segs, axis, closed=True, hard_deg=90), pos)


def tube_ring(r_out, r_in, length, axis="x", segs=14, pos=(0, 0, 0), bevel=0.02):
    """Hollow cylinder (pipe end, exhaust, bezel)."""
    h = length / 2
    b = min(bevel, (r_out - r_in) * 0.4)
    pts = [(-h, r_in), (-h, r_out - b), (-h + b, r_out), (h - b, r_out), (h, r_out - b), (h, r_in)]
    return xf(lathe_profile(pts + [(h - 0.001, r_in * 0.999), (-h + 0.001, r_in * 0.999)], segs, axis, closed=True, hard_deg=40), pos)


# ================================================================================================ wheels
def tyre(ro, width, ri=None, segs=26, knobby=0.0, lugs=18, grooves=True, axis="x"):
    """Tyre about the X axis at the origin: rounded sidewalls, tread with grooves; knobby > 0 adds lugs."""
    ri = ri if ri is not None else ro * 0.62
    w = width / 2
    h = ro - ri
    pts = [(-w * 0.86, ri), (-w * 1.0, ri + h * 0.4), (-w * 0.95, ri + h * 0.84), (-w * 0.72, ro)]
    if grooves:
        pts += [(-w * 0.12, ro), (-w * 0.1, ro - h * 0.09), (w * 0.1, ro - h * 0.09), (w * 0.12, ro)]
    pts += [(w * 0.72, ro), (w * 0.95, ri + h * 0.84), (w * 1.0, ri + h * 0.4), (w * 0.86, ri), (0, ri * 0.97)]
    m = lathe_profile(pts, segs, "x", closed=True, hard_deg=55)
    if knobby > 0:
        def f(V):
            r = np.hypot(V[:, 1], V[:, 2])
            a = np.arctan2(V[:, 2], V[:, 1])
            lug = (np.cos(a * lugs) > 0.1).astype(float)
            # stagger the two lug rows
            lug2 = (np.cos(a * lugs + math.pi) > 0.1).astype(float)
            row = np.where(V[:, 0] > 0, lug, lug2)
            k = np.clip((r - (ro - h * 0.35)) / (h * 0.35), 0, 1) * row * knobby
            s = (r + k) / np.maximum(r, 1e-9)
            return np.column_stack([V[:, 0], V[:, 1] * s, V[:, 2] * s])
        m = warp(m, f)
    if axis != "x":
        m = xf(m, r=(0, 90, 0) if axis == "z" else (0, 0, 90))
    return m


def rim(r, width, style="alloy", spokes=5, segs=28, hub=True):
    """Wheel rim about X at the origin, outer face +X. styles: alloy (spokes), steel (dish + hubcap), mag (deep
    dish), wire (many thin spokes), cart (wooden spokes), disc (flat hubcap)."""
    w = width / 2
    parts = []
    if style in ("alloy", "mag", "wire", "steel", "disc", "truck"):
        lip = [(w * 0.75, r * 0.62), (w * 0.95, r * 0.98), (w * 0.8, r * 1.04), (-w * 0.6, r * 0.98), (-w * 0.7, r * 0.62)]
        parts.append(lathe_profile(lip, segs, "x", closed=True, hard_deg=40))
    if style == "alloy" or style == "mag":
        dish = [(w * 0.1, 0), (w * 0.1, r * 0.25), (w * 0.42, r * 0.3), (w * 0.42, r * 0.0)]
        parts.append(lathe_profile([(w * 0.05, 0), (w * 0.05, r * 0.33), (w * 0.4, r * 0.33), (w * 0.55, r * 0.18), (w * 0.55, 0)], segs, "x"))
        for k in range(spokes):
            a = TAU * k / spokes
            d = np.array([0, math.cos(a), math.sin(a)])
            p0 = np.array([w * 0.35, 0, 0]) + d * r * 0.25
            p1 = np.array([w * (0.55 if style == "alloy" else 0.7), 0, 0]) + d * r * 0.9
            parts.append(bar(p0, p1, r * (0.2 if style == "alloy" else 0.26), w * 0.24, r=0.025, up=(1, 0, 0)))
        del dish
    elif style in ("steel", "truck"):
        prof = [(w * 0.0, 0), (w * 0.0, r * 0.55), (w * 0.35, r * 0.62), (w * 0.4, r * 0.86), (w * 0.2, r * 0.88), (-w * 0.2, r * 0.6), (-w * 0.2, 0)]
        parts.append(lathe_profile(prof, segs, "x"))
        cap = [(w * 0.2, 0), (w * 0.2, r * 0.42), (w * 0.45, r * 0.36), (w * 0.62, r * 0.18), (w * 0.66, 0)]
        parts.append(lathe_profile(cap, segs, "x"))
        if style == "truck":
            for k in range(8):
                a = TAU * k / 8
                parts.append(cyl(w * 0.2, r * 0.05, (w * 0.48, math.cos(a) * r * 0.48, math.sin(a) * r * 0.48), segs=6, bevel=0.01))
    elif style == "disc":
        cap = [(w * 0.3, 0), (w * 0.3, r * 0.92), (w * 0.62, r * 0.75), (w * 0.8, r * 0.3), (w * 0.82, 0)]
        parts.append(lathe_profile(cap, segs, "x"))
    elif style == "wire":
        parts.append(lathe_profile([(-w * 0.5, 0), (-w * 0.5, r * 0.2), (w * 0.5, r * 0.2), (w * 0.62, 0)], 12, "x"))
        for k in range(spokes):
            a = TAU * (k + 0.5 * (k % 2)) / spokes
            d = np.array([0, math.cos(a), math.sin(a)])
            sx = w * 0.4 if k % 2 else -w * 0.4
            parts.append(rod((sx, *(d[1:] * r * 0.18)), (0.0, *(d[1:] * r * 0.97)), r * 0.025, segs=5, bevel=0.003))
    elif style == "cart":  # wooden cart wheel: felloe ring + spokes + hub
        parts.append(lathe_profile([(-w, r * 0.82), (w, r * 0.82), (w, r * 1.0), (-w, r * 1.0)], segs, "x", closed=True, hard_deg=40))
        for k in range(spokes):
            a = TAU * k / spokes
            d = np.array([0, math.cos(a), math.sin(a)])
            parts.append(bar(d * r * 0.15, d * r * 0.86, r * 0.09, w * 0.6, r=0.02, up=(1, 0, 0)))
        parts.append(lathe_profile([(-w * 1.6, 0), (-w * 1.6, r * 0.12), (-w * 1.2, r * 0.2), (w * 1.2, r * 0.2), (w * 1.6, r * 0.12), (w * 1.6, 0)], 14, "x"))
    if hub and style in ("alloy", "mag", "wire"):
        parts.append(lathe_profile([(w * 0.5, 0), (w * 0.5, r * 0.16), (w * 0.72, r * 0.12), (w * 0.78, 0)], 12, "x"))
    return merge(*parts)


def wheel_pieces(H, name, bone, pos, ro, width, style="alloy", spokes=5, knobby=0.0, side=1, tyre_col="tyre", rim_col="metal",
                 rim_r=None, segs=26, pri=1.2, lugs=18, grooves=True, tris_note=None):
    """Tyre + rim pieces for one wheel at `pos` (its own bone). side +1: outer face +X, -1: mirrored."""
    rr = rim_r if rim_r is not None else ro * 0.6
    t = tyre(ro, width, ri=rr * 0.98, segs=segs, knobby=knobby, lugs=lugs, grooves=grooves)
    rmesh = rim(rr, width, style, spokes, segs=max(16, segs - 8))
    if side < 0:
        t, rmesh = mirror(t), mirror(rmesh)
    t = xf(t, pos)
    rmesh = xf(rmesh, pos)
    piece(H, name + "Tyre", bone, t, col=tyre_col, mat="rubber", role="wheel", pri=pri, fallback="Cylinder")
    piece(H, name + "Rim", bone, rmesh, col=rim_col, mat="metal", role="wheel", pri=pri + 0.3, fallback="Cylinder")


# ================================================================================================ interior / lamps
def seat_mesh(pos, w=0.9, d=0.85, back=1.0, cushion=0.22, recline=12.0, bucket=True):
    """Seat at pos (cushion centre top surface y = pos.y), facing -Z."""
    x, y, z = pos
    c = box((w, cushion, d), (x, y - cushion / 2, z), r=cushion * 0.4, seg=1)
    bk = box((w, back, cushion * 0.9), (0, back / 2, 0), r=cushion * 0.35, seg=1)
    bk = xf(bk, (x, y - cushion * 0.3, z + d / 2 - cushion * 0.2), r=(recline, 0, 0))
    parts = [c, bk]
    if bucket:
        for s in (-1, 1):
            parts.append(cbox((cushion * 0.5, cushion * 0.9, d * 0.85), (x + s * (w / 2 - cushion * 0.15), y + cushion * 0.15, z), c=cushion * 0.15))
    return merge(*parts)


def steering_mesh(pos, r=0.32, tilt=60.0, col_len=0.5):
    """Steering wheel at pos (centre), rim tilted `tilt` degrees from vertical toward the driver, with a column
    running forward/down into the dash."""
    ring = torus(r, r * 0.12, axis="z", segs=20, rsegs=6)
    spokes = merge(bar((0, 0, 0), (r * 0.95, 0, 0), r * 0.12, r * 0.08), bar((0, 0, 0), (-r * 0.95, 0, 0), r * 0.12, r * 0.08),
                   bar((0, 0, 0), (0, -r * 0.95, 0), r * 0.12, r * 0.08), cyl(r * 0.2, r * 0.25, (0, 0, 0), "z", segs=12))
    col = rod((0, 0, 0), (0, 0, -col_len), r * 0.1, segs=8) if col_len > 0.01 else None
    m = merge(ring, spokes, col)
    return xf(m, pos, r=(-(90 - tilt), 0, 0))


def lamp(pos, r, depth=0.12, axis="-z", shape="round", w=None, h=None):
    """A lamp lens facing along axis ("-z" front, "+z" back, "+x" ...). round: domed disc; rect: rounded slab."""
    if shape == "round":
        prof = [(-depth / 2, 0), (-depth / 2, r), (depth * 0.1, r), (depth * 0.35, r * 0.8), (depth / 2, 0)]
        m = lathe_profile(prof, 18, "z")
    else:
        m = box((w, h, depth), (0, 0, 0), r=min(w, h) * 0.3, seg=1)
    R = {"-z": None, "+z": (0, 180, 0), "+x": (0, -90, 0), "-x": (0, 90, 0), "+y": (90, 0, 0), "-y": (-90, 0, 0)}[axis]
    return xf(m, pos, R)


def bezel(pos, r, depth=0.1, axis="-z"):
    m = tube_ring(r * 1.25, r * 0.95, depth, axis="z", segs=18)
    R = {"-z": None, "+z": (0, 180, 0), "+x": (0, -90, 0), "-x": (0, 90, 0)}[axis]
    return xf(m, pos, R)


# ================================================================================================ pieces
def _cover(H, mesh):
    """Keep two pivot bones at the min / max corner of all direct pieces: build.py searches for a piece inside the box
    spanned by the bones (Hero.bounds_hint), so a sled or board with only one bone still finds its far ends."""
    lo, hi = mesh.bounds
    for nm, v, f in (("BoundLo", lo, np.minimum), ("BoundHi", hi, np.maximum)):
        if nm in H.bidx:
            i = H.bidx[nm]
            cur = np.array(H.bones[i][2])
            H.bones[i] = (nm, "Body", tuple(float(x) for x in f(cur, v)))
        else:
            H.bone(nm, "Body", tuple(float(x) for x in v))


def piece(H, name, bone, mesh, col="primary", mat="plastic", role="body", pri=1.0, ao=True, fallback="Block", tr=0.0, glow=False,
          pattern=None, pair=None, mirrored=False, key=None, needs=None):
    """A direct-mesh piece. tris = the mesh's own triangle count."""
    nt = len(mesh.faces)
    assert nt <= 2600, f"{H.id}/{name}: {nt} tris > 2600"
    _cover(H, mesh)
    return H.piece(name, bone, dm(mesh), col=col, mat=mat, role=role, pri=pri, tris=nt, ao=ao, fallback=fallback, tr=tr, glow=glow,
                   pattern=pattern, pair=pair, mirrored=mirrored, key=key, needs=needs)


def mpiece(H, name, bone, mesh, **kw):
    """Right piece (+X, '#' -> R) and its mirrored left copy as a pair."""
    pair = H._pair()
    k = f"h_{H.id}_{name.replace('#', '')}".lower().replace(" ", "_")
    r = piece(H, name.replace("#", "R"), bone.replace("#", "R"), mesh, pair=pair, key=k, **kw)
    l = piece(H, name.replace("#", "L"), bone.replace("#", "L"), mirror(mesh), pair=pair, mirrored=True, key=k + "_l", **kw)
    return r, l


# ================================================================================================ motion
def _ease(x):
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def _bump(s, a, b):
    """0 -> 1 -> 0 over s in [a, b]."""
    if s <= a or s >= b:
        return 0.0
    return math.sin(math.pi * (s - a) / (b - a))


def add(pose, bone, v):
    if bone is None:
        return
    o = list(pose.get(bone, (0.0,) * 6))
    for i, x in enumerate(v):
        o[i] += x
    pose[bone] = tuple(o)


def vehicle_clips(H, wheels, susp="Chassis", height=3.0, length=8.0, move_len=0.8, turns=1.6, sym=5, steer=(), extra_move=None,
                  extra_idle=None, extra_attack=None, attack="ram", bob=1.0, roll=1.0, idle_shake=1.0, keys=48, spinners=()):
    """Clips for a wheeled vehicle.
    wheels: list of (bone, radius). Each wheel spins forward (-rx); the Move loop rotates a wheel by a whole number of
    its spoke periods (2*pi/sym) so the loop seam lands on an identical-looking pose (keys=48 keeps the seam short).
    susp: the sprung-body bone (bobs, pitches, rolls; wheels stay planted). steer: front steer bones (Move: gentle
    weave). spinners: (bone, axis, turns) for other spinning parts (mixer drum, fans).
    attack: "ram" (lunge forward, nose dips, bounce back) or "honk" (two quick bounces)."""
    period = TAU / sym
    # an extra pivot at the roof line keeps tall vehicles inside build.py's search box (bounds_hint spans the bones)
    if H.bones and height + 0.5 > max(b[2][1] for b in H.bones):
        H.bone("Top", susp if susp in H.bidx else "Body", (0, height + 0.6, 0))

    def spin_angle(t, L, r):
        # distance travelled per loop ~ turns * 2*pi*r_ref; smaller wheels turn faster, quantised to the symmetry period
        r_ref = max(r for _, r in wheels) if wheels else 1.0
        n = max(1, round(turns * TAU * r_ref / r / period))
        return -n * period * (t / L)

    def move(t):
        u = t / move_len
        pose = {}
        for b, r in wheels:
            add(pose, b, (0, 0, 0, spin_angle(t, move_len, r), 0, 0))
        for b, ax, tn in spinners:
            a = TAU * tn * u
            add(pose, b, (0, 0, 0, a if ax == "x" else 0, a if ax == "y" else 0, a if ax == "z" else 0))
        add(pose, susp, (0, bob * height * (0.012 * math.sin(TAU * u * 2) + 0.006 * math.sin(TAU * u * 3 + 1)), 0,
                         bob * 0.012 * math.sin(TAU * u * 2 + 0.7), 0.0, roll * 0.03 * math.sin(TAU * u)))
        for b in steer:
            add(pose, b, (0, 0, 0, 0, 0.12 * math.sin(TAU * u), 0))
        if extra_move:
            extra_move(pose, u)
        return pose

    def idle(t):
        L = 2.0
        u = t / L
        pose = {}
        sh = idle_shake
        add(pose, susp, (0, height * sh * (0.006 * math.sin(TAU * u * 8) + 0.003 * math.sin(TAU * u * 2)), 0,
                         sh * 0.006 * math.sin(TAU * u * 2 + 0.5), 0, sh * 0.006 * math.sin(TAU * u * 8 + 1.1)))
        for b, ax, tn in spinners:
            a = TAU * max(1, round(tn * 0.5)) * u
            add(pose, b, (0, 0, 0, a if ax == "x" else 0, a if ax == "y" else 0, a if ax == "z" else 0))
        if extra_idle:
            extra_idle(pose, u)
        return pose

    def attack_fn(t):
        L = 0.9
        s = t / L
        pose = {}
        if attack == "ram":
            wind = _bump(s, 0.0, 0.32)
            lunge = _bump(s, 0.22, 0.62)
            settle = _bump(s, 0.55, 1.0)
            dz = 0.22 * length * wind - 0.55 * length * lunge * (1 if s < 0.5 else 1) + 0.04 * length * settle
            add(pose, "Body", (0, 0, dz * 0.25, 0, 0, 0))
            add(pose, susp, (0, height * (0.06 * wind + 0.08 * settle), 0, 0.08 * wind - 0.12 * lunge + 0.05 * settle, 0, 0))
            for b, r in wheels:
                add(pose, b, (0, 0, 0, 2.5 * wind - 7.0 * _ease((s - 0.22) / 0.4) * (1 if s > 0.22 else 0), 0, 0))
        else:  # honk: two quick hops
            h1 = _bump(s, 0.05, 0.35)
            h2 = _bump(s, 0.38, 0.68)
            add(pose, susp, (0, height * (0.08 * h1 + 0.06 * h2), 0, -0.05 * h1 + 0.04 * h2, 0, 0.03 * h2))
        if extra_attack:
            extra_attack(pose, s)
        return pose

    def hit(t):
        s = t / 0.45
        k = math.sin(math.pi * min(s, 1)) * (1 - 0.4 * s)
        pose = {}
        add(pose, susp, (0, height * 0.03 * k, length * 0.03 * k, 0.09 * k, 0, 0.06 * math.sin(t * 38) * k))
        add(pose, "Body", (0, 0, length * 0.04 * k, 0, 0.04 * k, 0))
        return pose

    H.clip("Move", move_len, move, keys=keys)
    H.clip("Idle", 2.0, idle, keys=40)
    H.clip("Attack", 0.9, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=10, loop=False)
    H.rig["wheels"] = [{"bone": b, "r": round(float(r), 3)} for b, r in wheels]
    H.rig["height"] = height


def mount(H, seat_part, pos, size, bone):
    H.mount = {"seat": seat_part, "saddle": {"pos": tuple(float(v) for v in pos), "size": tuple(float(v) for v in size)}}
    H.socket("seat", pos, bone)


def add_wheels(H, specs, parent="Body", **common):
    """specs: list of dicts {name, pos, r, w, side (+1 right / -1 left), steer (bool), + wheel_pieces kwargs}.
    Makes Steer<name> (optional) and <name> bones and the tyre + rim pieces. Returns (wheels [(bone, r)], steer bones)."""
    wheels, steer = [], []
    for s in specs:
        s = dict(s)
        nm, pos, r, w, side = s.pop("name"), s.pop("pos"), s.pop("r"), s.pop("w"), s.pop("side", None)
        side = side if side is not None else (1 if pos[0] >= 0 else -1)
        st = s.pop("steer", False)
        par = parent
        if st:
            sb = H.bone("Steer" + nm, parent, pos)
            steer.append(sb)
            par = sb
        H.bone(nm, par, pos)
        kw = dict(common)
        kw.update(s)
        if "rim" in kw:
            kw["style"] = kw.pop("rim")
        wheel_pieces(H, nm, nm, pos, r, w, side=side, **kw)
        wheels.append((nm, r))
    return wheels, steer


def four_wheels(xf_, zf, xr, zr, rf, wf, rr=None, wr_=None, steer=True):
    rr = rr or rf
    wr_ = wr_ or wf
    return [dict(name="WheelFR", pos=(xf_, rf, zf), r=rf, w=wf, side=1, steer=steer), dict(name="WheelFL", pos=(-xf_, rf, zf), r=rf, w=wf, side=-1, steer=steer),
            dict(name="WheelBR", pos=(xr, rr, zr), r=rr, w=wr_, side=1), dict(name="WheelBL", pos=(-xr, rr, zr), r=rr, w=wr_, side=-1)]


def greenhouse(H, bone, ws, belt, roof0, roofy, roof1, back, xg, tumble=0.12, bpillars=(), pw=0.16, glass_tr=0.22, roof_col="primary",
               vertical_back=False, rear_pw=None, crown=0.05):
    """Glass greenhouse (translucent volume, seats show through) with a proud roof skin and A / B / C pillars.
    Side profile: windshield from (ws, belt) up to (roof0, roofy), roof to roof1, back down to (back, belt)."""
    gpoly = np.array([(ws - 0.05, belt - 0.08), (roof0, roofy), (roof1, roofy), (back + 0.05, belt - 0.08)])
    gpoly = round_poly(gpoly, [0.0, 0.18, 0.18 if not vertical_back else 0.08, 0.0], 3)

    def gwarp(V):
        x, y, z = V[:, 0], V[:, 1], V[:, 2]
        t = np.clip((y - belt) / (roofy - belt), 0, 1)
        return np.column_stack([x * (1 - tumble * t), y + crown * np.clip(1 - (x / xg) ** 2, 0, 1) * t ** 4, z])

    glass = warp(extrude(gpoly, 2 * xg, bevel=0.1, seg=2), gwarp)
    piece(H, "Glass", bone, glass, col="glass", mat="glass", role="window", pri=0.8, tr=glass_tr, ao=False)
    xt = xg * (1 - tumble)
    rpoly = np.array([(roof0 - 0.06, roofy - 0.12), (roof0 + 0.12, roofy + 0.07), (roof1 - 0.12, roofy + 0.07), (roof1 + 0.06, roofy - 0.12)])
    roof = warp(extrude(round_poly(rpoly, 0.05, 2), 2 * xt + 0.12, bevel=0.06, seg=2),
                lambda V: np.column_stack([V[:, 0], V[:, 1] + crown * np.clip(1 - (V[:, 0] / (xt + 0.06)) ** 2, 0, 1), V[:, 2]]))
    pil = []
    rpw = rear_pw or pw * 1.6
    for s in (-1, 1):
        pil.append(bar((s * (xg + 0.02), belt - 0.02, ws + 0.08), (s * (xt + 0.03), roofy - 0.02, roof0 + 0.06), pw, pw * 0.8, r=0.04))
        for zb in bpillars:
            pil.append(bar((s * (xg + 0.03), belt - 0.02, zb), (s * (xt + 0.035), roofy - 0.03, zb), pw * 1.3, pw * 0.8, r=0.04))
        pil.append(bar((s * (xg + 0.02), belt - 0.02, back - 0.02), (s * (xt + 0.03), roofy - 0.02, roof1 - 0.04), rpw, pw * 0.8, r=0.04))
    piece(H, "Roof", bone, merge(roof, *pil), col=roof_col, mat="metal", role="body", pri=0.9)
    return xt


def lamp_pair(H, name, bone, pos, r=0.2, axis="-z", col=None, shape="round", w=None, h=None, depth=0.14, pri=1.5):
    m = lamp(pos, r, depth, axis=axis, shape=shape, w=w, h=h)
    mpiece(H, name + "#", bone, m, col=col or [0.95, 0.96, 0.92], mat="glass", role="light", pri=pri, ao=False)


# ================================================================================================ tracks
def stadium(z0, z1, y0, r, n=10):
    """Stadium outline (z, y): a belt around two end wheels of radius r centred at (z0, y0+r) and (z1, y0+r)."""
    pts = []
    cy = y0 + r
    for k in range(n + 1):
        a = -math.pi / 2 - math.pi * k / n  # rear wheel? start bottom going around the front end
        pts.append((z0 + r * math.cos(a), cy + r * math.sin(a)))
    for k in range(n + 1):
        a = math.pi / 2 - math.pi * k / n
        pts.append((z1 + r * math.cos(a), cy + r * math.sin(a)))
    return np.array(pts)


def track_loop(z0, z1, y_bottom, r_front, r_back, width, thick=0.16, cleats=26, sag_top=0.0, n=9, top_y=None):
    """Track belt as a closed ring (keyhole outline extruded across X) with grouser cleats on the outside."""
    cyf, cyb = y_bottom + r_front, y_bottom + r_back
    outer = []
    for k in range(n + 1):  # front end: from bottom (-90) around the front (-180) to top (-270)
        a = -math.pi / 2 - math.pi * k / n
        outer.append((z0 + r_front * math.cos(a), cyf + r_front * math.sin(a)))
    for k in range(n + 1):  # back end: from top around the back to bottom
        a = math.pi / 2 - math.pi * k / n
        outer.append((z1 + r_back * math.cos(a), cyb + r_back * math.sin(a)))
    outer = np.array(outer)
    c = outer.mean(0)
    inner = []
    for p in outer:
        d = p - c
        # inset toward the end centres: scale radially around each end
        inner.append(p)
    # proper inset: offset each point along its own end-wheel radius
    inner = []
    for k, p in enumerate(outer):
        if k <= n:
            cc = np.array([z0, cyf])
            rr = r_front
        else:
            cc = np.array([z1, cyb])
            rr = r_back
        d = (p - cc) / rr
        inner.append(cc + d * (rr - thick))
    inner = np.array(inner)
    # keyhole: outer CCW-ish, then a slit to inner traversed backwards
    poly = np.vstack([outer, outer[:1] + (0.0, 0.002), inner[:1] + (0.0, 0.002), inner[::-1][:-1], inner[:1]])
    belt = extrude(poly, width, bevel=0.04, seg=1, hard_deg=30)
    cl = []
    L = np.linalg.norm(np.diff(np.vstack([outer, outer[:1]]), axis=0), axis=1)
    per = np.cumsum(L)
    tot = per[-1]
    for k in range(cleats):
        s = tot * k / cleats
        i = int(np.searchsorted(per, s))
        a, b = outer[i % len(outer)], outer[(i + 1) % len(outer)]
        s0 = per[i - 1] if i > 0 else 0.0
        t = (s - s0) / max(L[i % len(L)], 1e-9)
        p = a + (b - a) * t
        d = b - a
        ang = math.degrees(math.atan2(d[1], d[0]))
        nrm = np.array([d[1], -d[0]]) / max(np.linalg.norm(d), 1e-9)
        if (p - c) @ nrm < 0:
            nrm = -nrm
        q = p + nrm * 0.04
        cl.append(cbox((width + 0.04, 0.09, 0.14), (0, q[1], q[0]), c=0.02, rot_=(-ang, 0, 0)))
    return merge(belt, *cl)


def road_wheel(r, w, pos, side=1, hub=True, segs=16):
    m = lathe_profile([(-w / 2, 0), (-w / 2, r * 0.92), (-w / 2 + 0.04, r), (w / 2 - 0.04, r), (w / 2, r * 0.92), (w / 2, r * 0.45),
                       (w / 2 + 0.05, r * 0.4), (w / 2 + 0.08, 0)], segs, "x")
    if side < 0:
        m = mirror(m)
    return xf(m, pos)


def sprocket(r, w, pos, teeth=10, side=1):
    m = lathe_profile([(-w / 2, 0), (-w / 2, r * 0.85), (w / 2, r * 0.85), (w / 2, r * 0.3), (w / 2 + 0.06, 0)], 16, "x")
    tt = [cbox((w * 0.9, r * 0.3, r * 0.28), (0, math.cos(TAU * k / teeth) * r * 0.92, math.sin(TAU * k / teeth) * r * 0.92), c=0.02,
               rot_=(math.degrees(TAU * k / teeth), 0, 0)) for k in range(teeth)]
    m = merge(m, *tt)
    if side < 0:
        m = mirror(m)
    return xf(m, pos)


def tracks(H, parent, x, z0, z1, width, r_end=0.55, y_bottom=0.0, n_road=5, r_road=0.42, col="darker", wheel_col="steel", pri=0.9, cleats=26,
           sprocket_back=True):
    """A pair of tracks (both sides) with spinning sprocket, idler and road wheels. Returns wheel list for clips."""
    belt = track_loop(z0, z1, y_bottom, r_end, r_end, width, cleats=cleats)
    piece(H, "TrackR", parent, xf(belt, (x, 0, 0)), col="tyre", mat="rubber", role="wheel", pri=pri)
    piece(H, "TrackL", parent, xf(belt, (-x, 0, 0)), col="tyre", mat="rubber", role="wheel", pri=pri)
    wheels = []
    cy = y_bottom + r_end
    ends = [("Sprocket", z1 if sprocket_back else z0), ("Idler", z0 if sprocket_back else z1)]
    for nm, z in ends:
        for side, tag in ((1, "R"), (-1, "L")):
            b = H.bone(nm + tag, parent, (side * x, cy, z))
            if nm == "Sprocket":
                m = sprocket(r_end * 0.86, width * 0.7, (side * x, cy, z), side=side)
            else:
                m = road_wheel(r_end * 0.8, width * 0.7, (side * x, cy, z), side=side)
            piece(H, nm + tag, b, m, col=wheel_col, mat="metal", role="wheel", pri=pri + 0.6)
            wheels.append((b, r_end * 0.86))
    for i in range(n_road):
        z = z0 + r_end * 0.6 + (z1 - z0 - r_end * 1.2) * (i + 0.5) / n_road
        for side, tag in ((1, "R"), (-1, "L")):
            b = H.bone(f"Road{i}{tag}", parent, (side * x, y_bottom + r_road + 0.12, z))
            piece(H, f"Road{i}{tag}", b, road_wheel(r_road, width * 0.6, (side * x, y_bottom + r_road + 0.12, z), side=side), col=wheel_col,
                  mat="metal", role="wheel", pri=pri + 1.0)
            wheels.append((b, r_road))
    return wheels


# word filters for the land-vehicle MAP rules: Vehicle words, plus toy / robot vehicles from Machine / Object
LAND = {"cat": ["Vehicle", "Machine", "Object"], "bp": ["Vehicle", "CarWheeled", "Tracked", "Insect", "Humanoid", "Biped"]}
