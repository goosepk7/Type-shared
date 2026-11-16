"""Directly built meshes for hard-surface pieces (tools/meshgen).

Marching cubes + decimation cannot keep a flat face flat-shaded at a few hundred triangles: the bevel vertices
drag their normals across the face. These builders place the vertices where the shading needs them (a flat
face ends in a ring of vertices that all carry the face normal) and give exact normals, so a bevelled block
costs about 100 triangles and still shades like a machined part.

A catalogue function may return one of these meshes (a trimesh.Trimesh with vertex normals) instead of an SDF;
build.py then skips the SDF pipeline and only recentres, fits, bakes AO and exports.
"""
import numpy as np
import trimesh


def _finish(V, N, F):
    m = trimesh.Trimesh(np.asarray(V, float), np.asarray(F, int), process=False)
    m.direct_normals = np.asarray(N, float)
    return m


def weld(m, tol=1e-6):
    """Merge coincident vertices that share a normal (keeps hard edges split)."""
    V, N = m.vertices, m.direct_normals
    key = np.round(np.hstack([V, N]) / tol * 1e-2).astype(np.int64)
    _, idx, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    F = inv.reshape(-1)[m.faces]
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
    return _finish(V[idx], N[idx], F)


def rounded_box(dims, r, seg=1):
    """Box of full size `dims` with edges rounded to radius r. seg = extra arc points per bevel (0 = one 45 degree
    step). Flat faces are single quads whose corners carry the exact face normal."""
    h = np.asarray(dims, float) / 2
    V, N, F = [], [], []

    def coords(hh):
        inner = hh - r
        steps = [np.sin(np.pi / 2 * (i + 1) / (seg + 1)) for i in range(seg)]  # extra positions inside the bevel band
        outer = [inner + r * s for s in steps] + [hh]
        return [-c for c in reversed(outer)] + [-inner, inner] + outer

    for ax in range(3):
        u, v = [a for a in range(3) if a != ax]
        cu, cv = coords(h[u]), coords(h[v])
        for sign in (-1, 1):
            base = len(V)
            for a in cu:
                for b in cv:
                    p = np.zeros(3)
                    p[ax], p[u], p[v] = sign * h[ax], a, b
                    inner = np.clip(p, -(h - r), h - r)
                    d = p - inner
                    # points in the bevel band slide onto the rounded edge / corner
                    n = d / np.linalg.norm(d)
                    V.append(inner + r * n)
                    N.append(n)
            nu, nv = len(cu), len(cv)
            for i in range(nu - 1):
                for j in range(nv - 1):
                    q = [base + i * nv + j, base + (i + 1) * nv + j, base + (i + 1) * nv + j + 1, base + i * nv + j + 1]
                    # winding: outward normal
                    a_, b_, c_ = np.array(V[q[0]]), np.array(V[q[1]]), np.array(V[q[2]])
                    out = np.cross(b_ - a_, c_ - a_) @ (np.array(N[q[0]]) + np.array(N[q[2]]))
                    if out < 0:
                        q = q[::-1]
                    F += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]
    return weld(_finish(V, N, F))


def lathe(profile, segs=24, axis=0):
    """Surface of revolution about `axis`. profile: list of (t, radius, nt, nr): position along the axis, radius,
    and the normal's axial / radial components. Consecutive points with different normals at the same place make
    a hard edge. Points with radius 0 close the caps."""
    a = [0, 1, 2]
    a.remove(axis)
    V, N, F = [], [], []
    ang = np.linspace(0, 2 * np.pi, segs, endpoint=False)
    rings = []
    for t, rad, nt, nr in profile:
        ln = np.hypot(nt, nr) or 1.0
        ring = []
        if rad <= 1e-9:
            p = np.zeros(3)
            p[axis] = t
            n = np.zeros(3)
            n[axis] = np.sign(nt) or 1.0
            ring = [len(V)] * segs
            V.append(p)
            N.append(n)
        else:
            for th in ang:
                p = np.zeros(3)
                p[axis], p[a[0]], p[a[1]] = t, rad * np.cos(th), rad * np.sin(th)
                n = np.zeros(3)
                n[axis], n[a[0]], n[a[1]] = nt / ln, nr / ln * np.cos(th), nr / ln * np.sin(th)
                ring.append(len(V))
                V.append(p)
                N.append(n)
        rings.append(ring)
    for k in range(len(rings) - 1):
        r0, r1 = rings[k], rings[k + 1]
        for i in range(segs):
            j = (i + 1) % segs
            for tri in ([r0[i], r1[i], r1[j]], [r0[i], r1[j], r0[j]]):
                if len(set(tri)) == 3:
                    p0, p1, p2 = (np.array(V[x]) for x in tri)
                    if np.linalg.norm(np.cross(p1 - p0, p2 - p0)) > 1e-12:
                        if np.cross(p1 - p0, p2 - p0) @ (np.array(N[tri[0]]) + np.array(N[tri[1]]) + np.array(N[tri[2]])) < 0:
                            tri = tri[::-1]
                        F.append(tri)
    return _finish(V, N, F)


def bevel_cylinder(length, r=0.5, bevel=0.07, segs=24, axis=0):
    """Capped cylinder with a rounded rim; flat caps carry the exact cap normal."""
    h = length / 2
    b = min(bevel, h * 0.9, r * 0.9)
    s = np.sqrt(0.5)
    prof = [
        (-h, 0, -1, 0), (-h, r - b, -1, 0), (-h + b * (1 - s), r - b * (1 - s), -1, 1), (-h + b, r, 0, 1),
        (h - b, r, 0, 1), (h - b * (1 - s), r - b * (1 - s), 1, 1), (h, r - b, 1, 0), (h, 0, 1, 0),
    ]
    return lathe(prof, segs, axis)


def merge(*meshes):
    V, N, F, off = [], [], [], 0
    for m in meshes:
        V.append(m.vertices)
        N.append(m.direct_normals)
        F.append(m.faces + off)
        off += len(m.vertices)
    return _finish(np.vstack(V), np.vstack(N), np.vstack(F))


def moved(m, offset=(0, 0, 0), rot=None, scale=(1, 1, 1)):
    V = m.vertices * np.asarray(scale, float)
    N = m.direct_normals / np.asarray(scale, float)
    if rot is not None:
        V, N = V @ np.asarray(rot).T, N @ np.asarray(rot).T
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return _finish(V + np.asarray(offset, float), N, m.faces)


def revolve(points, segs=16, axis=1, spline=4):
    """Smooth surface of revolution through (t, radius) control points (Catmull-Rom, `spline` samples per span).
    Normals follow the profile, so even a 200 triangle limb shades as a smooth organic form. The first and last
    points should have radius 0 (closed ends)."""
    P = np.asarray(points, float)
    ext = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    prof = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for k in range(spline):
            u = k / spline
            prof.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    prof.append(P[-1])
    prof = np.array(prof)
    prof[:, 1] = np.maximum(prof[:, 1], 0)
    prof[0, 1] = prof[-1, 1] = 0
    out = []
    for i, (t, r) in enumerate(prof):
        a, b = prof[max(i - 1, 0)], prof[min(i + 1, len(prof) - 1)]
        dt, dr = b[0] - a[0], b[1] - a[1]
        nt, nr = -dr, dt  # rotate the tangent: outward when t increases along the profile
        if i == 0:
            nt, nr = -1.0, 0.0
        elif i == len(prof) - 1:
            nt, nr = 1.0, 0.0
        out.append((t, r, nt, nr))
    return lathe(out, segs, axis)


def deform(m, fn):
    """Move vertices with fn(V) -> V'. Normals are recomputed from the welded surface (smooth)."""
    V = fn(m.vertices.copy())
    t = trimesh.Trimesh(V, m.faces, process=False)
    # average face normals over vertices that share a position (the lathe pole and seams stay smooth)
    key = np.round(V * 1e5).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    fn_ = t.face_normals * t.area_faces[:, None]
    acc = np.zeros((inv.max() + 1, 3))
    for c in range(3):
        np.add.at(acc, inv[t.faces[:, c]], fn_)
    N = acc[inv]
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return _finish(V, N, m.faces)


def blade(lead, trail, thick, camber=None, nt=14, nu=6, axes=(0, 1, 2)):
    """Thin two-sided blade (wing, fin, feather, petal). t in 0..1 runs along the span axis (axes[0], from -0.5 to
    +0.5), u in 0..1 across the chord (axes[2]) from lead(t) to trail(t); thick(t, u) is the half thickness along
    axes[1] and camber(t, u) lifts the mid surface. The rim is closed, normals are smooth."""
    T = np.linspace(0, 1, nt)
    U = np.linspace(0, 1, nu)
    V, F = [], []
    idx = {}
    for side in (1, -1):
        for i, t in enumerate(T):
            for j, u in enumerate(U):
                z = lead(t) + (trail(t) - lead(t)) * u
                rim = i in (0, nt - 1) or j in (0, nu - 1)
                th = 0.0 if rim else float(thick(t, u))
                c = float(camber(t, u)) if camber else 0.0
                key = (i, j, 0 if rim else side)
                if key not in idx:
                    p = np.zeros(3)
                    p[axes[0]], p[axes[1]], p[axes[2]] = t - 0.5, c + side * th, z
                    idx[key] = len(V)
                    V.append(p)
        for i in range(nt - 1):
            for j in range(nu - 1):
                def k(a, b):
                    rim = a in (0, nt - 1) or b in (0, nu - 1)
                    return idx[(a, b, 0 if rim else side)]
                q = [k(i, j), k(i + 1, j), k(i + 1, j + 1), k(i, j + 1)]
                if side < 0:
                    q = q[::-1]
                for tri in ([q[0], q[2], q[1]], [q[0], q[3], q[2]]):
                    if len(set(tri)) == 3:
                        F.append(tri)
    V = np.array(V)
    m = trimesh.Trimesh(V, np.array(F), process=False)
    # orientation: make the +side face outward along axes[1]
    if m.volume < 0:
        m = trimesh.Trimesh(V, np.array(F)[:, ::-1], process=False)
    fn_ = m.face_normals * m.area_faces[:, None]
    acc = np.zeros_like(V)
    for c in range(3):
        np.add.at(acc, m.faces[:, c], fn_)
    N = acc / np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-12)
    return _finish(V, N, m.faces)
