"""Shared helpers for the boats / aircraft / spacecraft hero families (h_boats.py, h_aircraft.py, h_spacecraft.py).

* Direct hard-surface meshes as hero pieces. kit.Hero.piece takes an SDF; build.py samples it before meshing, so a
  raw trimesh cannot go through as is. `D(mesh)` wraps a direct mesh in an SDF whose field is the mesh's bounding box
  (good enough for build.py's region search) and this module teaches mesher.build to recognise it and keep the exact
  mesh (finish_direct) instead of marching cubes. `dpiece(H, ...)` / `dmpiece(H, ...)` add such pieces (the mirrored
  copy is a real mirrored mesh).
* Mesh builders in model space: loft (rings -> surface, with fan / strip caps), boat hulls (thick shell or decked),
  rounded boxes, cylinders, revolves along any axis, wings / blades / sails, plank decks, prop blades.
  `finish(V, F, crease)` gives crisp shading: normals are averaged only across edges flatter than `crease` degrees.
* Motion helpers for vessels (bob / roll / bow pitch), aircraft (bank, pitch, propeller spin) and hovering craft.

NOTE: build.py hashes only the h_*.py file for its piece cache: after editing this file rebuild with --force.
"""
from __future__ import annotations

import math

import numpy as np
import trimesh

import direct
import mesher
import sdf as S

TAU = 2 * math.pi


# ================================================================================================ direct pieces
class D(S.SDF):
    """An SDF stand-in for a direct mesh: the field is the (slightly inflated) bounding box."""

    def __init__(self, mesh):
        self.mesh = mesh
        lo, hi = mesh.bounds
        c = (lo + hi) / 2
        h = np.maximum((hi - lo) / 2, 0.02) + 0.04
        bx = S.box(h[0], h[1], h[2], tuple(c))
        super().__init__(bx.f)


_orig_build = mesher.build


def _build(sdf, box, *a, **kw):
    f = getattr(sdf, "f", None)
    if f is not None and getattr(f, "__closure__", None):
        base, off = None, None
        for cell in f.__closure__:
            try:
                v = cell.cell_contents
            except ValueError:
                continue
            if isinstance(v, D):
                base = v
            elif isinstance(v, np.ndarray) and v.shape == (3,):
                off = v
        if base is not None and off is not None:
            return mesher.finish_direct(direct.moved(base.mesh, -off), kw.get("fit"))
    return _orig_build(sdf, box, *a, **kw)


if not getattr(mesher, "_airsea_patched", False):
    mesher.build = _build
    mesher._airsea_patched = True


def mirror(m):
    V = m.vertices.copy()
    V[:, 0] *= -1
    N = m.direct_normals.copy()
    N[:, 0] *= -1
    return direct._finish(V, N, m.faces[:, ::-1].copy())


def ntris(m):
    return len(m.faces)


def dpiece(H, name, bone, mesh, col="primary", mat="hard", role="body", pri=1.0, fallback="Block", ao=True, **kw):
    if isinstance(mesh, (list, tuple)):
        mesh = merge(*mesh)
    return H.piece(name, bone, D(mesh), col=col, mat=mat, role=role, pri=pri, tris=max(ntris(mesh), 1), fallback=fallback, ao=ao, **kw)


def dmpiece(H, name, bone, mesh, key=None, **kw):
    """Right-side (+X) direct mesh and its mirror. name / bone contain '#'."""
    if isinstance(mesh, (list, tuple)):
        mesh = merge(*mesh)
    pair = H._pair()
    k = key or f"h_{H.id}_{name.replace('#', '')}".lower().replace(" ", "_")
    r = dpiece(H, name.replace("#", "R"), bone.replace("#", "R"), mesh, key=k, pair=pair, **kw)
    l = dpiece(H, name.replace("#", "L"), bone.replace("#", "L"), mirror(mesh), key=k + "_l", pair=pair, mirrored=True, **kw)
    return r, l


def budget(H):
    """(parts, triangles) of a hero's pieces (direct meshes counted exactly)."""
    tris = 0
    for p in H.parts:
        if p["kind"] == "piece":
            s = p["sdf"]
            tris += ntris(s.mesh) if isinstance(s, D) else p["tris"]
    return len(H.parts), tris


# ================================================================================================ mesh building
def finish(V, F, crease=35.0):
    """Mesh from positions + triangles with crease-aware normals (edges sharper than `crease` degrees stay hard)."""
    V = np.asarray(V, float)
    F = np.asarray(F, int)
    if len(F) == 0:
        raise ValueError("empty mesh")
    # weld coincident positions
    key = np.round(V * 1e5).astype(np.int64)
    _, idx, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inv = inv.reshape(-1)
    P = V[idx]
    F = inv[F]
    a, b, c = P[F[:, 0]], P[F[:, 1]], P[F[:, 2]]
    cr = np.cross(b - a, c - a)
    area = np.linalg.norm(cr, axis=1)
    keep = area > 1e-10
    F, cr, area = F[keep], cr[keep], area[keep]
    fn = cr / area[:, None]
    cosl = math.cos(math.radians(crease))
    # per vertex: incident faces
    inc = [[] for _ in range(len(P))]
    for fi, f in enumerate(F):
        for v in f:
            inc[v].append(fi)
    outV, outN, outF = [], [], np.zeros_like(F)
    vmap = {}
    for fi, f in enumerate(F):
        for j, v in enumerate(f):
            fs = inc[v]
            nf = fn[fi]
            acc = np.zeros(3)
            for g in fs:
                if fn[g] @ nf >= cosl:
                    acc += cr[g]
            n = acc / max(np.linalg.norm(acc), 1e-12)
            k = (v, round(n[0], 3), round(n[1], 3), round(n[2], 3))
            if k not in vmap:
                vmap[k] = len(outV)
                outV.append(P[v])
                outN.append(n)
            outF[fi, j] = vmap[k]
    return direct._finish(np.array(outV), np.array(outN), outF)


def merge(*ms):
    ms = [m for m in ms if m is not None]
    return direct.merge(*ms)


def xform(m, pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    """Scale, then rotate (degrees, X then Y then Z like sdf.rot), then move."""
    R = S._rotm(*rot)
    return direct.moved(m, pos, R, scale)


def loft(rings, cap0="fan", cap1="fan", crease=35.0, strip=False):
    """Surface through rings (list of (M, 3) arrays with the same M, ordered consistently). Caps: "fan" (centroid
    fan), "strip" (ring = outer half + inner half reversed: the cap is a strip between them), None (open / the ring
    is degenerate)."""
    R = [np.asarray(r, float) for r in rings]
    M = len(R[0])
    V = np.vstack(R)
    F = []
    for k in range(len(R) - 1):
        o0, o1 = k * M, (k + 1) * M
        for i in range(M):
            j = (i + 1) % M
            F.append([o0 + i, o1 + i, o1 + j])
            F.append([o0 + i, o1 + j, o0 + j])
    V = list(V)

    def cap(ring_i, kind, flip):
        nonlocal V
        o = ring_i * M
        tris = []
        if kind == "fan":
            c = len(V)
            V.append(R[ring_i].mean(0))
            for i in range(M):
                j = (i + 1) % M
                tris.append([c, o + j, o + i])
        elif kind == "strip":
            h = M // 2
            for i in range(h - 1):
                a, b = o + i, o + i + 1
                c_, d = o + M - 1 - i, o + M - 2 - i
                tris.append([a, c_, b])
                tris.append([b, c_, d])
        if flip:
            tris = [t[::-1] for t in tris]
        F.extend(tris)

    if cap0:
        cap(0, cap0, False)
    if cap1:
        cap(len(R) - 1, cap1, True)
    m = finish(np.array(V), np.array(F), crease)
    t = trimesh.Trimesh(m.vertices, m.faces, process=False)
    if t.volume < 0:
        m = direct._finish(m.vertices, m.direct_normals, m.faces[:, ::-1].copy())
    return m


def box(size, pos=(0, 0, 0), r=0.0, rot=(0, 0, 0), seg=0):
    sx, sy, sz = size
    r = min(r, min(size) * 0.45)
    if r <= 1e-4:
        h = np.array(size) / 2
        V = np.array([[x, y, z] for x in (-h[0], h[0]) for y in (-h[1], h[1]) for z in (-h[2], h[2])])
        F = [[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1], [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]]
        m = finish(V, F, 30)
        t = trimesh.Trimesh(m.vertices, m.faces, process=False)
        if t.volume < 0:
            m = direct._finish(m.vertices, m.direct_normals, m.faces[:, ::-1].copy())
    else:
        m = direct.rounded_box(size, r, seg)
    return xform(m, pos, rot)


def cyl(r, length, pos=(0, 0, 0), axis=1, bevel=0.0, segs=16, rot=(0, 0, 0), r2=None):
    """Cylinder (or frustum when r2 is given) along axis centred on pos."""
    if r2 is None:
        m = direct.bevel_cylinder(length, r, bevel if bevel > 0 else 1e-3, segs, axis)
    else:
        h = length / 2
        prof = [(-h, 0, -1, 0), (-h, r, -1, 0), (-h, r, (r - r2), length), (h, r2, (r - r2), length), (h, r2, 1, 0), (h, 0, 1, 0)]
        m = direct.lathe(prof, segs, axis)
    return xform(m, pos, rot)


def rev(points, axis=2, segs=16, pos=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), spline=3):
    """Smooth surface of revolution through (t, radius) control points (direct.revolve), along `axis`."""
    m = direct.revolve(points, segs, axis, spline)
    return xform(m, pos, rot, scale)


def lathe(prof, axis=2, segs=16, pos=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), closed=False):
    """Hard-edged lathe: prof = [(t, r)] -> normals from the profile with creases (via finish). closed: the profile
    is a loop (rings, ducts, bands): no caps."""
    P = np.asarray(prof, float)
    if closed:
        P = np.vstack([P, P[:1]])
    ang = np.linspace(0, TAU, segs, endpoint=False)
    rings = []
    a = [0, 1, 2]
    a.remove(axis)
    for t, r in P:
        ring = np.zeros((segs, 3))
        ring[:, axis] = t
        ring[:, a[0]] = r * np.cos(ang)
        ring[:, a[1]] = r * np.sin(ang)
        rings.append(ring)
    m = loft(rings, cap0="fan" if (P[0, 1] > 1e-6 and not closed) else None, cap1="fan" if (P[-1, 1] > 1e-6 and not closed) else None, crease=40)
    return xform(m, pos, rot, scale)


def sphere(r, pos=(0, 0, 0), scale=(1, 1, 1), segs=14):
    k = 9 if r * max(scale) > 0.5 else 6
    pts = [(-r, 0)] + [(-r * math.cos(a), r * math.sin(a)) for a in np.linspace(0, math.pi, k)[1:-1]] + [(r, 0)]
    return rev(pts, axis=1, segs=segs, pos=pos, scale=scale, spline=2 if k == 9 else 1)


def tube(points, r, segs=8, closed_ends=True):
    """Polyline tube (rope, rails, struts, broom handle). r: float or list per point."""
    P = np.asarray(points, float)
    rs = np.broadcast_to(np.asarray(r, float), (len(P),))
    rings = []
    up0 = np.array([0, 1, 0.0])
    for i, p in enumerate(P):
        t = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
        t /= np.linalg.norm(t)
        up = up0 if abs(t @ up0) < 0.9 else np.array([1, 0, 0.0])
        u = np.cross(t, up)
        u /= np.linalg.norm(u)
        v = np.cross(u, t)
        ang = np.linspace(0, TAU, segs, endpoint=False)
        rings.append(p + rs[i] * (np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * v))
    return loft(rings, "fan" if closed_ends else None, "fan" if closed_ends else None, crease=60)


def blade(span, chord_lead, chord_trail, thick, pos=(0, 0, 0), rot=(0, 0, 0), camber=None, nt=10, nu=6, axes=(0, 1, 2), scale_span=1.0):
    """direct.blade scaled so t runs over [0, span] along axes[0] from pos. lead / trail: fn(t01) -> chord coords."""
    m = direct.blade(chord_lead, chord_trail, thick, camber, nt, nu, axes)
    V = m.vertices.copy()
    V[:, axes[0]] = (V[:, axes[0]] + 0.5) * span
    m2 = finish(V, m.faces, 70)
    return xform(m2, pos, rot)


def wing(span, root_chord, tip_chord, sweep=0.0, thick=0.08, dihedral=0.0, pos=(0, 0, 0), side=1, nt=8, nu=7, tip_round=0.0):
    """Right wing (+X) from pos (root leading edge) out `span`: airfoil thickness, sweep (tip leading-edge setback),
    dihedral (degrees). Chord runs +Z (back)."""

    def lead(t):
        return sweep * t + (tip_round * (t ** 6) * (root_chord - (root_chord - tip_chord)) * 0.5 if tip_round else 0)

    def trail(t):
        c = root_chord + (tip_chord - root_chord) * t
        return lead(t) + c - (tip_round * (t ** 6) * c * 0.5 if tip_round else 0)

    def th(t, u):
        c = root_chord + (tip_chord - root_chord) * t
        # NACA-ish thickness distribution
        prof = 2.6 * (0.2969 * math.sqrt(max(u, 0)) - 0.126 * u - 0.3516 * u * u + 0.2843 * u ** 3 - 0.1036 * u ** 4)
        return max(prof, 0.02) / 0.26 * thick / 2 * c / max(root_chord, 1e-6) * (1 - 0.25 * t)

    m = direct.blade(lead, trail, th, None, nt, nu, (0, 1, 2))
    V = m.vertices.copy()
    V[:, 0] = (V[:, 0] + 0.5) * span
    V[:, 1] += V[:, 0] * math.tan(math.radians(dihedral))
    m2 = finish(V, m.faces, 75)
    m2 = direct.moved(m2, pos)
    return m2 if side > 0 else mirror(m2)


def fin(height, root_chord, tip_chord, sweep, thick=0.06, pos=(0, 0, 0), rot=(0, 0, 0)):
    """Vertical fin (tail): span along +Y, chord +Z."""
    def lead(t):
        return sweep * t

    def trail(t):
        return sweep * t + root_chord + (tip_chord - root_chord) * t

    def th(t, u):
        prof = 2.6 * (0.2969 * math.sqrt(max(u, 0)) - 0.126 * u - 0.3516 * u * u + 0.2843 * u ** 3 - 0.1036 * u ** 4)
        return max(prof, 0.03) / 0.26 * thick / 2
    m = direct.blade(lead, trail, th, None, 7, 6, (1, 0, 2))
    V = m.vertices.copy()
    V[:, 1] = (V[:, 1] + 0.5) * height
    return xform(finish(V, m.faces, 75), pos, rot)


def sail(pts_luff, pts_leech, billow=0.3, thick=0.03, nt=10, nu=7, side_axis=0):
    """Cloth sail between two edges (luff = along the mast, leech = the free edge), each a fn(t) -> (3,) point.
    billow bulges the middle along +X (side_axis) like wind from -X. Two-sided thin sheet."""
    T = np.linspace(0, 1, nt)
    U = np.linspace(0, 1, nu)
    V, F, idx = [], [], {}
    for side in (1, -1):
        for i, t in enumerate(T):
            a, b = np.asarray(pts_luff(t), float), np.asarray(pts_leech(t), float)
            for j, u in enumerate(U):
                rim = i in (0, nt - 1) or j in (0, nu - 1)
                k = (i, j, 0 if rim else side)
                if k in idx:
                    continue
                p = a + (b - a) * u
                bulge = billow * math.sin(math.pi * u) * (0.35 + 0.65 * math.sin(math.pi * min(t * 1.0, 1.0) * 0.999 + 0.0001)) if nt > 1 else 0
                p = p.copy()
                p[side_axis] += bulge + (0 if rim else side * thick)
                idx[k] = len(V)
                V.append(p)
        for i in range(nt - 1):
            for j in range(nu - 1):
                def kk(a_, b_):
                    rim = a_ in (0, nt - 1) or b_ in (0, nu - 1)
                    return idx[(a_, b_, 0 if rim else side)]
                q = [kk(i, j), kk(i + 1, j), kk(i + 1, j + 1), kk(i, j + 1)]
                if side < 0:
                    q = q[::-1]
                F.append([q[0], q[2], q[1]])
                F.append([q[0], q[3], q[2]])
    m = finish(np.array(V), np.array(F), 80)
    return m


def quad_sheet(c00, c10, c01, c11, nt=8, nu=8, bulge=(0, 0, 0), thick=0.03, wave=None):
    """Thin two-sided sheet over a bilinear quad (t along c00->c10, u along c00->c01), bulging by `bulge` * sin*sin;
    wave(t, u) -> (3,) optional displacement (flags, carpets)."""
    c00, c10, c01, c11 = (np.asarray(x, float) for x in (c00, c10, c01, c11))
    bul = np.asarray(bulge, float)

    def pt(t, u):
        p = c00 * (1 - t) * (1 - u) + c10 * t * (1 - u) + c01 * (1 - t) * u + c11 * t * u
        p = p + bul * math.sin(math.pi * t) * math.sin(math.pi * u)
        if wave is not None:
            p = p + np.asarray(wave(t, u), float)
        return p

    T = np.linspace(0, 1, nt)
    U = np.linspace(0, 1, nu)
    # normal of the sheet for thickness
    n = np.cross(c10 - c00, c01 - c00)
    n /= np.linalg.norm(n)
    V, F, idx = [], [], {}
    for side in (1, -1):
        for i, t in enumerate(T):
            for j, u in enumerate(U):
                rim = i in (0, nt - 1) or j in (0, nu - 1)
                k = (i, j, 0 if rim else side)
                if k in idx:
                    continue
                idx[k] = len(V)
                V.append(pt(t, u) + (0 if rim else side * thick) * n)
        for i in range(nt - 1):
            for j in range(nu - 1):
                def kk(a_, b_):
                    rim = a_ in (0, nt - 1) or b_ in (0, nu - 1)
                    return idx[(a_, b_, 0 if rim else side)]
                q = [kk(i, j), kk(i + 1, j), kk(i + 1, j + 1), kk(i, j + 1)]
                if side < 0:
                    q = q[::-1]
                F.append([q[0], q[1], q[2]])
                F.append([q[0], q[2], q[3]])
    return finish(np.array(V), np.array(F), 80)


def slab(sheet_fn, nt, nu, thick, crease=50):
    """Thick sheet: sheet_fn(t, u) -> (point, normal); top and bottom surfaces + closed rim (carpets, wings, decks)."""
    T = np.linspace(0, 1, nt)
    U = np.linspace(0, 1, nu)
    top = np.zeros((nt, nu, 3))
    bot = np.zeros((nt, nu, 3))
    for i, t in enumerate(T):
        for j, u in enumerate(U):
            p, n = sheet_fn(t, u)
            n = np.asarray(n, float)
            n = n / np.linalg.norm(n)
            top[i, j] = np.asarray(p) + n * thick / 2
            bot[i, j] = np.asarray(p) - n * thick / 2
    V = np.vstack([top.reshape(-1, 3), bot.reshape(-1, 3)])
    off = nt * nu
    F = []

    def id_(s, i, j):
        return s * off + i * nu + j

    for i in range(nt - 1):
        for j in range(nu - 1):
            a, b, c, d = id_(0, i, j), id_(0, i + 1, j), id_(0, i + 1, j + 1), id_(0, i, j + 1)
            F += [[a, c, b], [a, d, c]]
            a, b, c, d = id_(1, i, j), id_(1, i + 1, j), id_(1, i + 1, j + 1), id_(1, i, j + 1)
            F += [[a, b, c], [a, c, d]]
    # rim
    loop = [(i, 0) for i in range(nt)] + [(nt - 1, j) for j in range(1, nu)] + [(i, nu - 1) for i in range(nt - 2, -1, -1)] + [(0, j) for j in range(nu - 2, 0, -1)]
    for k in range(len(loop)):
        (i0, j0), (i1, j1) = loop[k], loop[(k + 1) % len(loop)]
        a, b, c, d = id_(0, i0, j0), id_(0, i1, j1), id_(1, i1, j1), id_(1, i0, j0)
        F += [[a, b, c], [a, c, d]]
    m = finish(V, np.array(F), crease)
    t = trimesh.Trimesh(m.vertices, m.faces, process=False)
    if t.volume < 0:
        m = direct._finish(m.vertices, m.direct_normals, m.faces[:, ::-1].copy())
    return m


# ------------------------------------------------------------------------------------------------ fuselages
class Fus:
    """Lofted body through stations (z, half_width, half_height, y_centre[, squareness]): superellipse sections
    interpolated smoothly (fuselages, nacelles, blimp gondolas, floats). Query the surface with x_at / y_top."""

    def __init__(self, stations, n=20, p=2.0, smooth=False):
        S_ = np.array([list(s) + [p] * (5 - len(s)) for s in stations], float)
        self.S = S_[np.argsort(S_[:, 0])]
        self.n = n
        self._pch = None
        if smooth:
            from scipy.interpolate import PchipInterpolator
            self._pch = [PchipInterpolator(self.S[:, 0], self.S[:, k]) for k in range(1, 5)]

    def at(self, z):
        S_ = self.S
        if self._pch is not None:
            zc = min(max(float(z), S_[0, 0]), S_[-1, 0])
            return [float(f(zc)) for f in self._pch]
        return [float(np.interp(z, S_[:, 0], S_[:, k])) for k in range(1, 5)]

    def ring(self, z, n=None):
        n = n or self.n
        w, h, yc, p = self.at(z)
        a = np.linspace(0, TAU, n, endpoint=False)
        c, s = np.cos(a), np.sin(a)
        x = w * np.sign(c) * np.abs(c) ** (2 / p)
        y = yc + h * np.sign(s) * np.abs(s) ** (2 / p)
        return np.column_stack([x, y, np.full(n, z)])

    def mesh(self, nz=None, z0=None, z1=None, crease=70, samples=None):
        S_ = self.S
        if samples is None:
            zs = []
            for i in range(len(S_) - 1):
                k = 3
                zs += list(np.linspace(S_[i, 0], S_[i + 1, 0], k, endpoint=False))
            zs.append(S_[-1, 0])
        else:
            zs = list(samples)
        zs = [z for z in zs if (z0 is None or z >= z0) and (z1 is None or z <= z1)]
        rings = []
        for z in zs:
            w, h = self.at(z)[:2]
            if w < 1e-3 and h < 1e-3:
                rings.append(np.tile([0, self.at(z)[2], z], (self.n, 1)))
            else:
                rings.append(self.ring(z))
        c0 = None if self.at(zs[0])[0] < 1e-3 else "fan"
        c1 = None if self.at(zs[-1])[0] < 1e-3 else "fan"
        return loft(rings, c0, c1, crease=crease)

    def x_at(self, z, y):
        w, h, yc, p = self.at(z)
        v = min(abs(y - yc) / max(h, 1e-6), 1.0)
        return w * max(1 - v ** p, 0) ** (1 / p)

    def y_top(self, z):
        w, h, yc, p = self.at(z)
        return yc + h


def window_row(fus, zs, y, w=0.35, h=0.4, th=0.06, r=0.06, both=True):
    """Window panes standing just proud of a Fus surface at height y."""
    ms = []
    for z in zs:
        x = fus.x_at(z, y)
        ms.append(box((th, h, w), (x - th * 0.3, y, z), r=r))
    m = merge(*ms)
    return merge(m, mirror(m)) if both else m


def wheel(r, width, pos, axis=0, hub_col=False, segs=16):
    """Tyre with a rounded profile (direct lathe)."""
    h = width / 2
    prof = [(-h, 0.0), (-h, r * 0.55), (-h * 0.9, r * 0.85), (-h * 0.5, r), (h * 0.5, r), (h * 0.9, r * 0.85), (h, r * 0.55), (h, 0.0)]
    return lathe(prof, axis=axis, segs=segs, pos=pos)


# ------------------------------------------------------------------------------------------------ boat hulls
def _arc_resample(P, n):
    P = np.asarray(P, float)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = np.linspace(0, d[-1], n)
    return np.column_stack([np.interp(s, d, P[:, k]) for k in range(P.shape[1])])


class HullSpec:
    """Parametric hull. t in 0..1 runs bow (z0) -> stern (z1).
    beam(t): half beam at the gunwale; keel(t): bottom y; top(t): gunwale (sheer) y; p(t): section squareness
    (1.2 V-hull, 2 round bilge, 4+ boxy); flare: sides lean out toward the top; strakes: clinker steps."""

    def __init__(self, length, beam, depth, z0=None, bow=0.42, stern=0.6, transom=0.0, bow_rise=0.3, stern_rise=0.2,
                 sheer_bow=0.35, sheer_stern=0.2, p_bow=1.4, p_mid=2.6, p_stern=2.6, flare=0.12, maxat=0.55, keel_y=0.0,
                 strakes=0, strake_step=0.04, deadrise=0.0, bow_shape=1.0, tumble=0.0):
        self.L, self.B, self.Dp = length, beam, depth
        self.z0 = -length / 2 if z0 is None else z0
        self.__dict__.update(dict(bow=bow, stern=stern, transom=transom, bow_rise=bow_rise, stern_rise=stern_rise,
                                  sheer_bow=sheer_bow, sheer_stern=sheer_stern, p_bow=p_bow, p_mid=p_mid, p_stern=p_stern,
                                  flare=flare, maxat=maxat, keel_y=keel_y, strakes=strakes, strake_step=strake_step,
                                  deadrise=deadrise, bow_shape=bow_shape, tumble=tumble))

    def z(self, t):
        return self.z0 + self.L * t

    def beam(self, t):
        m = self.maxat
        if t <= m:
            u = 1 - t / m
            w = (1 - u ** 2) ** (0.5 + self.bow) if u < 1 else 0.0
            w = w ** self.bow_shape
        else:
            u = (t - m) / (1 - m)
            w = 1 - (1 - self.transom) * (u ** (1.6 + 2 * self.stern))
        return self.B / 2 * max(w, 0.0)

    def keel(self, t):
        m = self.maxat
        if t < m:
            u = 1 - t / m
            return self.keel_y + self.bow_rise * self.Dp * u ** 2.2
        u = (t - m) / (1 - m)
        return self.keel_y + self.stern_rise * self.Dp * u ** 2.0

    def top(self, t):
        return self.keel_y + self.Dp + self.sheer_bow * self.Dp * (1 - t) ** 3 + self.sheer_stern * self.Dp * t ** 3

    def p(self, t):
        m = self.maxat
        if t < m:
            return self.p_bow + (self.p_mid - self.p_bow) * (t / m) ** 0.7
        return self.p_mid + (self.p_stern - self.p_mid) * ((t - m) / (1 - m))

    def t_of(self, z):
        return min(max((z - self.z0) / self.L, 0.0), 1.0)

    def half_width(self, z, y, inset=0.0):
        """Outer half width of the hull at station z and height y, minus inset (fit seats / decks inside)."""
        t = self.t_of(z)
        o = self.outer(t, 61)[:31]  # right half: gunwale -> keel
        ys, xs = o[::-1, 1], o[::-1, 0]
        if y <= ys[0]:
            return 0.0
        return max(float(np.interp(y, ys, xs)) - inset, 0.0)

    def outer(self, t, n):
        """Section points from the right gunwale, down round the keel, up to the left gunwale (n points)."""
        w, yb, yt, p = self.beam(t), self.keel(t), self.top(t), self.p(t)
        th = np.linspace(0, math.pi, n)
        c, s = np.cos(th), np.sin(th)
        x = w * np.sign(c) * np.abs(c) ** (2 / p)
        hgt = (yt - yb)
        y = yt - hgt * np.abs(s) ** (2 / p)
        if self.deadrise:
            y = y + self.deadrise * hgt * (np.abs(x) / max(w, 1e-6)) * (np.abs(s) ** 2)
        # flare: narrower at the bottom
        f = (y - yb) / max(hgt, 1e-6)
        x = x * (1 - self.flare * (1 - f)) * (1 - self.tumble * np.clip((f - 0.75) / 0.25, 0, 1) ** 2)
        if self.strakes and w > 1e-3:
            # clinker: each strake's lower edge stands out a little
            k = self.strakes
            ph = np.mod(f * k, 1.0)
            out = self.strake_step * (1 - ph) * np.clip(f * 6, 0, 1) * min(1.0, w / (self.B * 0.25))
            x = x + np.sign(x) * out
        return np.column_stack([x, y, np.full(n, self.z(t))])


def hull_shell(spec, th=0.12, n=22, nl=28, floor=None, crease=50, t0=0.0, t1=1.0, cap1="strip"):
    """Open hull with thickness: outer skin + inner skin + gunwale top. floor: y of a flat inner floor (decked or
    open boats); None follows the outer shape. Returns a direct mesh."""
    T = np.linspace(t0, t1, nl) ** 1.0
    # denser near the bow
    T = t0 + (t1 - t0) * (1 - np.cos(np.linspace(0, math.pi, nl))) / 2 * 0.5 + T * 0.5 - t0 * 0.5
    T = np.sort(T)
    rings = []
    for t in T:
        o = spec.outer(t, n)
        w = spec.beam(t)
        yt = spec.top(t)
        wi = w - th
        if floor is not None:
            fy = max(floor, spec.keel(t) + th)
        if wi <= 0.02:
            inner = np.column_stack([np.linspace(0.01, -0.01, n), np.full(n, yt - 0.005), np.full(n, spec.z(t))])
        else:
            if floor is None:
                sub = HullSpec(1, 1, 1)
                xi = o.copy()
                # shrink toward the section's interior
                yb = spec.keel(t)
                xi[:, 0] = o[:, 0] * (wi / w)
                xi[:, 1] = yt - (yt - o[:, 1]) * max((yt - yb - th) / max(yt - yb, 1e-6), 0.02)
                inner = xi
            else:
                fy2 = min(fy, yt - 0.05)
                # inner wall follows the outer at gunwale, then a flat floor
                sel = o[:, 1] >= fy2
                wall = []
                for q in o:
                    if q[1] >= fy2:
                        wall.append([q[0] - np.sign(q[0]) * th, q[1], q[2]])
                left = [q for q in wall if q[0] < 0]
                right = [q for q in wall if q[0] >= 0]
                wr = abs(right[-1][0]) if right else wi
                wl = abs(left[0][0]) if left else wi
                poly = right + [[wr, fy2, spec.z(t)], [-wl, fy2, spec.z(t)]] + left
                inner = _arc_resample(np.array(poly), n)
        ring = np.vstack([o, inner[::-1]])
        rings.append(ring)
    return loft(rings, cap0=None if spec.beam(T[0]) < 1e-3 else "strip", cap1=cap1 if spec.beam(T[-1]) > 1e-3 else None, crease=crease)


def hull_solid(spec, n=22, nl=28, deck_drop=0.0, crease=50):
    """Closed hull: outer skin + flat deck at gunwale height - deck_drop (a slight bulwark is a separate piece)."""
    T = np.sort(np.r_[(1 - np.cos(np.linspace(0, math.pi, nl))) / 2])
    rings = []
    for t in T:
        o = spec.outer(t, n)
        yt = spec.top(t) - deck_drop
        o[:, 1] = np.minimum(o[:, 1], yt)
        top = np.column_stack([np.linspace(o[-1, 0], o[0, 0], n)[1:-1], np.full(n - 2, yt), np.full(n - 2, spec.z(t))])
        rings.append(np.vstack([o, top]))
    return loft(rings, cap0=None if spec.beam(T[0]) < 1e-3 else "fan", cap1="fan" if spec.beam(T[-1]) > 1e-3 else None, crease=crease)


def gunwale_points(spec, t0=0.0, t1=1.0, n=20, inset=0.0, dy=0.0):
    T = np.linspace(t0, t1, n)
    return np.array([[spec.beam(t) - inset, spec.top(t) + dy, spec.z(t)] for t in T])


def rail(spec, r=0.06, t0=0.0, t1=1.0, n=18, inset=0.0, dy=0.0, both=True, segs=6):
    """Rubbing strake / rail along the gunwale (right side; both -> also the left, joined round the bow)."""
    P = gunwale_points(spec, t0, t1, n, inset, dy)
    if both:
        L = P.copy()
        L[:, 0] *= -1
        P = np.vstack([L[::-1], P[1:]]) if spec.beam(t0) < 0.05 else None
        if P is None:
            R = gunwale_points(spec, t0, t1, n, inset, dy)
            return merge(tube(R, r, segs), mirror(tube(R, r, segs)))
    return tube(P, r, segs)


def planks(xw, z0, z1, y, n=5, gap=0.04, th=0.05, width_fn=None, nz=8):
    """Deck planking: n planks across [-xw, xw] from z0 to z1 (width_fn(z) -> half width for a tapering deck)."""
    ms = []
    pw = (2 * xw - gap * (n - 1)) / n
    for i in range(n):
        x0 = -xw + i * (pw + gap)
        x1 = x0 + pw
        if width_fn is None:
            ms.append(box((pw, th, z1 - z0), ((x0 + x1) / 2, y, (z0 + z1) / 2)))
        else:
            # clip planks to the deck outline via rings
            Z = np.linspace(z0, z1, nz)
            rings = []
            for z in Z:
                hw = width_fn(z)
                a, b = max(x0, -hw), min(x1, hw)
                if b - a < 0.01:
                    m_ = (a + b) / 2
                    a, b = m_ - 0.005, m_ + 0.005
                rings.append(np.array([[a, y - th / 2, z], [b, y - th / 2, z], [b, y + th / 2, z], [a, y + th / 2, z]]))
            ms.append(loft(rings, "fan", "fan", crease=30))
    return merge(*ms)


# ------------------------------------------------------------------------------------------------ props / rotors
def prop(nblades, radius, chord, axis="z", hub=None, pitch=25, pos=(0, 0, 0), thick=0.03, twist=True, spinner=None):
    """Propeller / rotor disc in its own frame: blades in the XY plane spinning about Z (axis "z") or in the XZ plane
    spinning about Y (axis "y"). spinner: (radius, length) nose cone (z props)."""
    ms = []
    for k in range(nblades):
        a = 360 * k / nblades

        def lead(t, c=chord):
            return -c * (0.45 + 0.15 * math.sin(math.pi * t)) * (1 - 0.5 * t ** 3)

        def trail(t, c=chord):
            return c * (0.55 + 0.2 * math.sin(math.pi * t)) * (1 - 0.6 * t ** 3)

        def th(t, u):
            return thick * (1 - 0.6 * t) * math.sin(math.pi * u) ** 0.6

        b = direct.blade(lead, trail, th, None, 8, 5, (0, 2, 1))  # span X, thickness Z, chord Y
        V = b.vertices.copy()
        V[:, 0] = (V[:, 0] + 0.5) * radius * 0.92 + radius * 0.08
        bm = finish(V, b.faces, 75)
        bm = xform(bm, (0, 0, 0), (pitch, 0, 0))  # blade pitch about its span
        if axis == "z":
            bm = xform(bm, (0, 0, 0), (0, 0, a))
        else:
            bm = xform(bm, (0, 0, 0), (90, 0, 0))
            bm = xform(bm, (0, 0, 0), (0, a, 0))
        ms.append(bm)
    if hub is not None:
        ax = 2 if axis == "z" else 1
        ms.append(cyl(hub[0], hub[1], (0, 0, 0), axis=ax, bevel=hub[0] * 0.3, segs=12))
    if spinner is not None and axis == "z":
        sr, sl = spinner
        ms.append(rev([(0, 0), (-sl * 0.05, sr), (-sl * 0.5, sr * 0.8), (-sl, 0)][::-1], axis=2, segs=12))
    return direct.moved(merge(*ms), pos)


# ================================================================================================ motion
def spin(angle):
    return angle


def spin_pose(t, L, turns, axis):
    """Spin a rotor: `turns` blade-symmetry steps per loop are smoothed by the clip (16 keys); returns (rx, ry, rz)."""
    a = TAU * turns * t / L
    return (a, 0, 0) if axis == "x" else ((0, a, 0) if axis == "y" else (0, 0, a))


def rotors(pose, specs, t, speed):
    """specs: list of (bone, axis, sign, symmetry_angle). Rotation per key step ~0.45 of the blade symmetry angle so
    the Catmull-Rom between keys turns forward; speed scales it."""
    for bone, axis, sgn, sym in specs:
        a = sgn * sym * 0.42 * speed * t
        v = [0, 0, 0, 0, 0, 0]
        v[3 + "xyz".index(axis)] = a
        _add(pose, bone, v)


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


def pulse(x, a, b):
    """0 -> 1 -> 0 bump over [a, b] (smooth)."""
    if x <= a or x >= b:
        return 0.0
    return math.sin(math.pi * (x - a) / (b - a)) ** 2


def boat_clips(H, size=1.0, extra=None, keys=24, attack="ram", spinners=(), oars=None):
    """Vessel clips. Idle: bob + gentle roll / pitch. Move: bow up, pitching over the swell, slight roll.
    Attack: 'ram' (surge forward, bow dips into the hit) or 'broadside' (roll away from the recoil, cannons kick).
    extra(name, t, pose, phase) adds per-hero motion (oars, sails, paddle wheels). spinners: rotor specs."""
    s = size

    def idle(t):
        u = t / 2.4
        pose = {}
        _add(pose, "Body", (0, 0.06 * s * math.sin(TAU * u), 0, 0.018 * math.sin(TAU * u + 0.8), 0, 0.035 * math.sin(TAU * u + 1.9)))
        rotors(pose, spinners, t / 2.4 * keys, 0.4)
        if extra:
            extra("Idle", u, pose)
        return pose

    def move(t):
        u = t / 1.2
        pose = {}
        _add(pose, "Body", (0, 0.1 * s * math.sin(TAU * u), 0, 0.07 + 0.045 * math.sin(TAU * u), 0.015 * math.sin(TAU * u * 0.0 + TAU * u), 0.04 * math.sin(TAU * u + 1.3)))
        rotors(pose, spinners, t / 1.2 * keys, 1.0)
        if extra:
            extra("Move", u, pose)
        return pose

    def attack_fn(t):
        u = t / 0.8
        pose = {}
        if attack == "broadside":
            k = pulse(u, 0.15, 0.95)
            _add(pose, "Body", (0.25 * s * k, 0.05 * s * k, 0, 0, 0, -0.12 * k + 0.04 * pulse(u, 0.6, 1.0)))
        else:
            k = ease(u / 0.45) * (1 - ease((u - 0.55) / 0.45))
            _add(pose, "Body", (0, 0.05 * s * k, -1.2 * s * k, 0.12 * pulse(u, 0.0, 0.4) - 0.1 * pulse(u, 0.4, 0.8), 0, 0.03 * k))
        rotors(pose, spinners, t / 0.8 * 16, 1.4)
        if extra:
            extra("Attack", u, pose)
        return pose

    def hit(t):
        u = t / 0.45
        pose = {}
        k = math.sin(math.pi * u) * (1 - u)
        _add(pose, "Body", (0, -0.05 * s * k, 0.2 * s * k, -0.05 * k, 0.04 * k, 0.16 * math.sin(TAU * u * 1.5) * (1 - u)))
        if extra:
            extra("Hit", u, pose)
        return pose

    fix_bounds(H)
    H.clip("Idle", 2.4, idle, keys=keys)
    H.clip("Move", 1.2, move, keys=keys)
    H.clip("Attack", 0.8, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=10, loop=False)


def air_clips(H, size=1.0, spinners=(), extra=None, keys=24, attack="dive", bank=0.35, hover=False):
    """Aircraft clips. Idle: gentle float (hover) with props ticking over; Move: banking S-turns, pitch, props at full
    speed; Attack: 'dive' (nose down swoop, pull up), 'roll' (barrel roll), 'ram' (lunge); Hit: knocked + wobble."""
    s = size

    def idle(t):
        u = t / 2.4
        pose = {}
        _add(pose, "Body", (0, 0.12 * s * math.sin(TAU * u), 0, 0.03 * math.sin(TAU * u + 0.6), 0, 0.04 * math.sin(TAU * u + 1.5)))
        rotors(pose, spinners, t / 2.4 * keys, 0.9 if hover else 0.6)
        if extra:
            extra("Idle", u, pose)
        return pose

    def move(t):
        u = t / 1.6
        pose = {}
        _add(pose, "Body", (0.15 * s * math.sin(TAU * u), 0.18 * s * math.sin(TAU * u * 2), 0,
                            (-0.12 if hover else 0.04) + 0.04 * math.sin(TAU * u * 2), 0.08 * math.sin(TAU * u), -bank * math.sin(TAU * u)))
        rotors(pose, spinners, t / 1.6 * keys, 1.0)
        if extra:
            extra("Move", u, pose)
        return pose

    def attack_fn(t):
        u = t / 0.9
        pose = {}
        if attack == "roll":
            _add(pose, "Body", (0, 0.4 * s * pulse(u, 0, 1), -1.0 * s * pulse(u, 0, 1), 0.1 * pulse(u, 0, 0.5), 0, TAU * ease(u)))
        elif attack == "ram":
            k = ease(u / 0.4) * (1 - ease((u - 0.5) / 0.5))
            _add(pose, "Body", (0, -0.1 * s * k, -1.6 * s * k, -0.15 * k, 0, 0))
        else:
            k1 = pulse(u, 0.0, 0.6)
            k2 = pulse(u, 0.45, 1.0)
            _add(pose, "Body", (0, -0.9 * s * k1 + 0.2 * s * k2, -1.4 * s * pulse(u, 0.1, 0.9), -0.45 * k1 + 0.3 * k2, 0, 0.1 * k1))
        rotors(pose, spinners, t / 0.9 * 16, 1.4)
        if extra:
            extra("Attack", u, pose)
        return pose

    def hit(t):
        u = t / 0.45
        pose = {}
        k = math.sin(math.pi * u) * (1 - u)
        _add(pose, "Body", (0.15 * s * k, -0.2 * s * k, 0.25 * s * k, 0.1 * k, 0.06 * k, 0.3 * math.sin(TAU * u * 1.5) * (1 - u)))
        rotors(pose, spinners, t / 0.45 * 10, 1.0)
        if extra:
            extra("Hit", u, pose)
        return pose

    fix_bounds(H)
    H.clip("Idle", 2.4, idle, keys=keys)
    H.clip("Move", 1.6, move, keys=keys)
    H.clip("Attack", 0.9, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=10, loop=False)


def fix_bounds(H):
    """build.py searches each piece inside Hero.bounds_hint() (from the bones): widen it to every direct mesh."""
    lo0, hi0 = Hero_bounds(H)
    lo, hi = lo0.copy(), hi0.copy()
    for p in H.parts:
        if p["kind"] == "piece" and isinstance(p["sdf"], D):
            b = p["sdf"].mesh.bounds
            lo = np.minimum(lo, b[0] - 0.5)
            hi = np.maximum(hi, b[1] + 0.5)
    H.bounds_hint = lambda: (lo, hi)


def Hero_bounds(H):
    import kit
    return kit.Hero.bounds_hint(H)


PREVIEW_DEFAULTS = {"chrome": "#D5DCE3", "rubber": "#2A2C31", "flame": "#FF8A1F", "flameCore": "#FFE7A3", "paint": None, "trim": None, "bark": "#6B4A2E"}


def mount(H, seat_part, pos, size, bone="Body", length=None, enter=None, stand=False):
    """Seat socket (the rider's HIP point, rider faces -Z) + H.mount. length: the model's Z length in studs at its
    authored (real game) size ("auto" measures the rest-pose parts); enter: (x, z) ground point to climb in from."""
    fix_bounds(H)
    pv = getattr(H, "preview", None) or {}
    for k, v in PREVIEW_DEFAULTS.items():
        if v and k not in pv:
            pv[k] = v
    H.preview = pv
    H.socket("seat", pos, bone)
    H.mount = {"seat": seat_part, "saddle": {"pos": tuple(float(v) for v in pos), "size": tuple(float(v) for v in size)}}
    if length is not None:
        H.mount["length"] = round(float(model_length(H) if length == "auto" else length), 2)
    if stand:
        H.mount["stand"] = True
    if enter is not None:
        H.socket("enter", (float(enter[0]), 0.0, float(enter[1])), "Body")


def model_bounds(H):
    """Rest-pose model-space bounds of the pieces (direct meshes exactly, sculpts sampled) and prims."""
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    blo, bhi = None, None
    for p in H.parts:
        if p["kind"] == "piece" and isinstance(p["sdf"], D):
            b = p["sdf"].mesh.bounds
            lo, hi = np.minimum(lo, b[0]), np.maximum(hi, b[1])
        elif p["kind"] == "piece":  # sculpt: coarse sample of its field over the search region
            if blo is None:
                blo, bhi = H.bounds_hint()
            vol, step = mesher.sample(p["sdf"], blo, bhi, 72)
            inside = np.argwhere(vol < 0)
            if len(inside):
                lo, hi = np.minimum(lo, blo + inside.min(0) * step), np.maximum(hi, blo + inside.max(0) * step)
        elif p["kind"] == "prim":
            c, s = np.array(p["pos"]), np.array(p["size"]) / 2
            lo, hi = np.minimum(lo, c - s), np.maximum(hi, c + s)
    return lo, hi


def model_length(H):
    lo, hi = model_bounds(H)
    return float(hi[2] - lo[2])


# ================================================================================================ real-scale craft
def fus_angle(fus, z, y):
    """Angle (radians, right side, 0 = +X) where the Fus section at z reaches height y."""
    w, h, yc, p = fus.at(z)
    s = min(max((y - yc) / max(h, 1e-6), -1.0), 1.0)
    return math.asin(math.copysign(abs(s) ** (p / 2), s))


def fus_point(fus, z, a, inset=0.0):
    w, h, yc, p = fus.at(z)
    c, s = math.cos(a), math.sin(a)
    w2, h2 = max(w - inset, 1e-4), max(h - inset, 1e-4)
    return np.array([w2 * math.copysign(abs(c) ** (2 / p), c), yc + h2 * math.copysign(abs(s) ** (2 / p), s), z])


def band(fus, zs, ylo=None, yhi=None, th=0.15, n=32, side=False, crease=60, out=0.0):
    """Thick shell over the part of a Fus surface between heights ylo and yhi at every station z (ylo / yhi: float,
    fn(z) or None). ylo None: the bottom tub (right edge at yhi, down round the keel, up to the left edge); yhi None:
    the top cap (canopies, roofs); side=True: only the right-hand strip between ylo and yhi (mirror it yourself).
    The inner skin is the section shrunk by th, edges are closed: an open cockpit tub, a glass bubble, a roof."""
    def val(v, z, d):
        if v is None:
            return d
        return float(v(z)) if callable(v) else float(v)

    rings = []
    for z in zs:
        if side:
            a0, a1 = fus_angle(fus, z, val(ylo, z, -1e9)), fus_angle(fus, z, val(yhi, z, 1e9))
        elif ylo is None:
            a0 = fus_angle(fus, z, val(yhi, z, 1e9))
            a1 = -math.pi - a0
        else:
            a0 = fus_angle(fus, z, val(ylo, z, -1e9))
            a1 = math.pi - a0
        A_ = np.linspace(a0, a1, n)
        o = np.array([fus_point(fus, z, a, -out) for a in A_])
        i = np.array([fus_point(fus, z, a, th - out) for a in A_])
        rings.append(np.vstack([o, i[::-1]]))
    return loft(rings, "strip", "strip", crease=crease)


def surface_line(fus, zs, y, r=0.06, out=0.0, segs=6, both=True, yfn=None):
    """Tube hugging a Fus side at height y (or yfn(z)): trims, beltlines, stripes, door seams along z."""
    pts = []
    for z in zs:
        yy = yfn(z) if yfn else y
        a = fus_angle(fus, z, yy)
        p = fus_point(fus, z, a, -out)
        pts.append(p)
    m = tube(pts, r, segs)
    return merge(m, mirror(m)) if both else m


def ring_line(fus, z, r=0.05, ylo=None, yhi=None, out=0.0, n=24):
    """Tube round a Fus section at z (between heights, or the whole ring): panel seams, frames, pillars."""
    if ylo is None and yhi is None:
        A_ = np.linspace(0, TAU, n + 1)
    elif ylo is None:
        a0 = fus_angle(fus, z, yhi)
        A_ = np.linspace(a0, -math.pi - a0, n)
    else:
        a0 = fus_angle(fus, z, ylo)
        a1 = math.pi - a0 if yhi is None else fus_angle(fus, z, yhi)
        A_ = np.linspace(a0, a1, n)
    pts = [fus_point(fus, z, a, -out) for a in A_]
    return tube(pts, r, 6)


def pilot_seat(hip, w=1.7, back_h=2.9, rake=8, depth=1.5, floor_y=None):
    """Bucket seat for a seated R15 rider whose HIP point is `hip` (cushion top 0.25 below it, under the thighs, backrest behind the
    torso, headrest), on a pedestal down to floor_y. Returns a direct mesh."""
    x, y, z = hip
    cz = z - depth / 2 + 0.45
    ms = [box((w, 0.42, depth), (x, y - 0.46, cz), r=0.14, seg=1),
          box((0.24, 0.3, depth * 0.85), (x + w / 2 - 0.06, y - 0.2, cz + 0.05), r=0.1),
          box((0.24, 0.3, depth * 0.85), (x - w / 2 + 0.06, y - 0.2, cz + 0.05), r=0.1),
          xform(box((w, back_h, 0.4), (0, back_h / 2, 0), r=0.15, seg=1), (x, y - 0.3, z + 0.78), (rake, 0, 0)),
          xform(box((w * 0.62, 0.75, 0.32), (0, back_h + 0.42, -0.04), r=0.13, seg=1), (x, y - 0.3, z + 0.78), (rake, 0, 0))]
    if floor_y is not None and y - 0.67 - floor_y > 0.05:
        hgt = y - 0.67 - floor_y
        # the pedestal sinks 0.06 into the floor (its foot never shares the floor's top plane: z-fighting at small scales)
        ms.append(box((w * 0.6, hgt + 0.09, depth * 0.6), (x, floor_y + hgt / 2 - 0.015, cz), r=0.05))
    return merge(*ms)


def yoke(hip, span=3.0, col=None):
    """Control yoke where a seated R15 rider's hands are (hip + (+-1.5, 1.3, -1.6)): horns, hub, column forward."""
    x, y, z = hip
    hy, hz = y + 1.3, z - 1.65
    horns = merge(tube([[x - span / 2, hy + 0.35, hz], [x - span / 2, hy - 0.15, hz], [x - span / 2 + 0.5, hy - 0.4, hz], [x + span / 2 - 0.5, hy - 0.4, hz],
                        [x + span / 2, hy - 0.15, hz], [x + span / 2, hy + 0.35, hz]], 0.1, 8),
                  box((0.7, 0.4, 0.25), (x, hy - 0.35, hz), r=0.08))
    col_ = cyl(0.11, 1.4, (x, hy - 0.35, hz - 0.75), axis=2, segs=10)
    return horns, col_


def stick(hip, floor_y, dz=-1.7, dx=0.0, h=1.1):
    """Centre control stick rising from the floor to hip + (0, h, dz) (fighter / glider / helicopter cyclic)."""
    x, y, z = hip
    top = np.array([x + dx, y + h, z + dz])
    boot = rev([(floor_y, 0), (floor_y + 0.02, 0.32), (floor_y + 0.25, 0.22), (floor_y + 0.4, 0.0)], axis=1, segs=12, pos=(top[0], 0, top[2] - 0.35))
    shaft = tube([[top[0], floor_y + 0.2, top[2] - 0.35], [top[0], (floor_y + top[1]) / 2, top[2] - 0.15], top - np.array([0, 0.3, 0])], 0.07, 8)
    grip = xform(rev([(-0.3, 0), (-0.28, 0.13), (0.1, 0.15), (0.3, 0.12), (0.34, 0)], axis=1, segs=10), tuple(top), (-12, 0, 0))
    return merge(boot, shaft, grip)


def craft_clips(H, L, hover=False, attack="dive", bank=0.3, extra=None, keys=24):
    """Clips for a real-scale rideable craft (the game spins rotors / props / wheels and folds gear itself, so
    clips never turn them). Idle: engine shudder (+ a gentle hover bob for hovering craft). Move: subtle airframe
    buzz + slow rock. Attack / Hit: one-shots scaled to the craft length L (summons)."""
    s = L / 10.0

    def idle(t):
        u = t / 2.4
        pose = {}
        b = 0.06 * s * math.sin(TAU * u) if hover else 0.0
        _add(pose, "Body", (0, b + 0.012 * math.sin(TAU * u * 8), 0, 0.004 * math.sin(TAU * u * 6 + 0.5), 0, 0.006 * math.sin(TAU * u * 5 + 1.1)))
        if extra:
            extra("Idle", u, pose)
        return pose

    def move(t):
        u = t / 1.6
        pose = {}
        _add(pose, "Body", (0, 0.03 * s * math.sin(TAU * u) + 0.01 * math.sin(TAU * u * 7), 0, (-0.05 if hover else 0.0) + 0.012 * math.sin(TAU * u + 0.3),
                            0, 0.025 * bank * math.sin(TAU * u) * 2 + 0.004 * math.sin(TAU * u * 6)))
        if extra:
            extra("Move", u, pose)
        return pose

    def attack_fn(t):
        u = t / 0.9
        pose = {}
        if attack == "roll":
            _add(pose, "Body", (0, 0.3 * s * pulse(u, 0, 1), -0.8 * s * pulse(u, 0, 1), 0.08 * pulse(u, 0, 0.5), 0, TAU * ease(u)))
        elif attack == "ram":
            k = ease(u / 0.4) * (1 - ease((u - 0.5) / 0.5))
            _add(pose, "Body", (0, -0.08 * s * k, -1.2 * s * k, -0.15 * k, 0, 0))
        else:
            k1, k2 = pulse(u, 0.0, 0.6), pulse(u, 0.45, 1.0)
            _add(pose, "Body", (0, -0.6 * s * k1 + 0.15 * s * k2, -1.0 * s * pulse(u, 0.1, 0.9), -0.35 * k1 + 0.25 * k2, 0, 0.08 * k1))
        if extra:
            extra("Attack", u, pose)
        return pose

    def hit(t):
        u = t / 0.45
        pose = {}
        k = math.sin(math.pi * u) * (1 - u)
        _add(pose, "Body", (0.1 * s * k, -0.12 * s * k, 0.15 * s * k, 0.06 * k, 0.04 * k, 0.18 * math.sin(TAU * u * 1.5) * (1 - u)))
        if extra:
            extra("Hit", u, pose)
        return pose

    fix_bounds(H)
    H.clip("Idle", 2.4, idle, keys=keys)
    H.clip("Move", 1.6, move, keys=keys)
    H.clip("Attack", 0.9, attack_fn, keys=16, loop=False)
    H.clip("Hit", 0.45, hit, keys=10, loop=False)


class SplitFus:
    """A fuselage as two half-shells meeting at the sill line y = yc(z): a lower half (h_lo, squareness p_lo) and an
    upper half (h_up, p_up) with the same half width. The upper half can rise into a canopy hump over the cockpit,
    so the glass is simply the upper band over the cockpit's z range and the decks in front / behind are the same
    surface in paint. stations: (z, w, h_lo, h_up, yc)."""

    def __init__(self, stations, n=32, p_lo=2.4, p_up=2.2):
        self.lo = Fus([(z, w, hl, yc, p_lo) for z, w, hl, hu, yc in stations], n=n, smooth=True)
        self.up = Fus([(z, w, hu, yc, p_up) for z, w, hl, hu, yc in stations], n=n, smooth=True)
        self.z0, self.z1 = float(self.lo.S[0, 0]), float(self.lo.S[-1, 0])

    def yc(self, z):
        return self.lo.at(z)[2]

    def top(self, z):
        w, h, yc, p = self.up.at(z)
        return yc + h

    def bottom(self, z):
        w, h, yc, p = self.lo.at(z)
        return yc - h

    def half(self, y, z):
        return self.up if y >= self.yc(z) else self.lo

    def x_at(self, z, y):
        return self.half(y, z).x_at(z, y)

    def lower(self, zs, th=0.15, n=24, **kw):
        return band(self.lo, zs, yhi=self.yc, th=th, n=n, **kw)

    def upper(self, zs, th=0.15, n=24, **kw):
        return band(self.up, zs, ylo=self.yc, th=th, n=n, **kw)

    def shell(self, zs, th=0.15, n=24):
        return merge(self.lower(zs, th, n), self.upper(zs, th, n))

    def point(self, z, y, out=0.0, side=1):
        f = self.half(y, z)
        p = fus_point(f, z, fus_angle(f, z, y), -out)
        p[0] *= side
        return p

    def line(self, zs, y=None, yfn=None, r=0.06, out=0.0, both=True, segs=6):
        """Tube along the side at height y (or yfn(z)); y=None + yfn=None runs along the top centre."""
        pts = []
        for z in zs:
            if y is None and yfn is None:
                pts.append(np.array([0.0, self.top(z) + out, z]))
            else:
                pts.append(self.point(z, yfn(z) if yfn else y, out))
        m = tube(pts, r, segs)
        return m if (not both or (y is None and yfn is None)) else merge(m, mirror(m))

    def ring(self, z, r=0.06, out=0.0, ylo=None, n=28):
        """Frame hoop over the top half at z (from the sill, or from height ylo on both sides), or round the whole
        section when ylo == "full"."""
        if ylo == "full":
            pts = [fus_point(self.up, z, a, -out) for a in np.linspace(0, math.pi, n // 2 + 1)] + \
                  [fus_point(self.lo, z, a, -out) for a in np.linspace(-math.pi, 0, n // 2 + 1)[1:]]
            return tube(pts, r, 6)
        if ylo is None or ylo >= self.yc(z):
            a0 = 0.0 if ylo is None else fus_angle(self.up, z, ylo)
            pts = [fus_point(self.up, z, a, -out) for a in np.linspace(a0, math.pi - a0, n)]
        else:
            a0 = fus_angle(self.lo, z, ylo)
            pts = [fus_point(self.lo, z, a, -out) for a in np.linspace(a0, 0, n // 4, endpoint=False)] + \
                  [fus_point(self.up, z, a, -out) for a in np.linspace(0, math.pi, n // 2)] + \
                  [fus_point(self.lo, z, a, -out) for a in np.linspace(-math.pi, -math.pi - a0, n // 4 + 1)[1:]]
        return tube(pts, r, 6)

    def floor(self, z0, z1, y, inset=0.25, th=0.14, nz=10):
        rings = []
        for z in np.linspace(z0, z1, nz):
            hw = max(self.x_at(z, y) - inset, 0.05)
            rings.append(np.array([[-hw, y - th, z], [hw, y - th, z], [hw, y, z], [-hw, y, z]]))
        return loft(rings, "fan", "fan", crease=30)


def zrange(z0, z1, step=0.6, extra=()):
    n = max(int(math.ceil((z1 - z0) / step)), 1)
    zs = sorted(set([round(float(z), 4) for z in np.linspace(z0, z1, n + 1)] + [round(float(e), 4) for e in extra if z0 < e < z1]))
    return zs


def gear_leg(top, axle, wheel_r, wheel_w, pant=True, fork=False, segs=18):
    """Landing gear unit: strut from `top` (pivot) to the axle, tyre + hub, optional wheel pant (fairing).
    Returns (metal, tyre, pant) meshes."""
    top, axle = np.asarray(top, float), np.asarray(axle, float)
    ax = axle.copy()
    strut = merge(tube([top, (top + ax) / 2 + np.array([0, 0, 0.0]), ax + np.array([0, wheel_r * 0.55, 0])], 0.16, 8),
                  cyl(0.22, 0.6, tuple(top + (ax - top) * 0.3), axis=1, segs=10))
    tyre = merge(wheel(wheel_r, wheel_w, tuple(ax), axis=0, segs=segs),
                 cyl(wheel_r * 0.55, wheel_w + 0.08, tuple(ax), axis=0, segs=14, bevel=0.05))
    pm = None
    if pant:
        L = wheel_r * 2.9
        pm = rev([(-L * 0.42, 0.0), (-L * 0.36, wheel_r * 0.55), (-L * 0.1, wheel_r * 0.82), (L * 0.2, wheel_r * 0.78), (L * 0.5, wheel_r * 0.35), (L * 0.58, 0.0)],
                 axis=2, segs=16, pos=(ax[0], ax[1] + wheel_r * 0.25, ax[2]), scale=((wheel_w * 0.5 + 0.18) / (wheel_r * 0.82), 1.0, 1.0))
    return strut, tyre, pm


# ================================================================================================ rideable craft helpers
GLASS = [0.62, 0.8, 0.92]
SCREEN = [0.35, 0.75, 1.0]



def ride(H, hip, enter, nose_z, tail_z, top_y, seat_size=(1.8, 0.15, 1.5), muzzle=None, exhaust=None, length="auto"):
    """Real-scale rideable craft: seat socket at the rider's hip, enter socket on the ground, measured length."""
    mount(H, "Seat", hip, seat_size, length=length, enter=enter)
    H.socket("head", (hip[0], top_y, hip[2]), "Body")
    H.socket("mouth", (0, hip[1] - 0.3, nose_z), "Body")
    H.socket("exhaust", exhaust or (0, hip[1] - 0.5, tail_z), "Body")
    if muzzle is not None:
        H.socket("muzzle", muzzle, "Body")


def bulkhead(fus, z, th=0.12, inset=0.1, ylo=None):
    r = fus.ring(z, 32)
    w, h, yc, p = fus.at(z)
    r[:, 0] *= (w - inset) / w
    r[:, 1] = yc + (r[:, 1] - yc) * (h - inset) / h
    if ylo is not None:
        r[:, 1] = np.maximum(r[:, 1], ylo)
    a, b = r.copy(), r.copy()
    a[:, 2] = z - th / 2
    b[:, 2] = z + th / 2
    return loft([a, b], "fan", "fan", crease=40)


def cockpit(H, F, hip, floor_y, panel_z, panel_w, panel_top, ctrl="stick", seat_w=1.9, screens=2, col="darker", side_console=True):
    """Floor, pilot seat, instrument panel (glare shield + glowing screens), control stick / yoke, rudder pedals
    and a throttle for a single pilot whose HIP point is `hip`."""
    x, y, z = hip
    dpiece(H, "Seat", "Body", pilot_seat(hip, w=seat_w, floor_y=floor_y), col="dark", mat="cloth", role="detail", pri=1.2)
    pz0 = panel_z - 0.75
    pb = floor_y + 0.6
    panel = merge(xform(box((panel_w, panel_top - pb, 0.75), (0, 0, 0), r=0.15, seg=1), (x, (panel_top + pb) / 2, panel_z - 0.37), (-8, 0, 0)),
                  xform(box((panel_w * 0.96, 0.16, 1.15), (0, 0, 0), r=0.07), (x, panel_top + 0.08, panel_z - 0.45), (-5, 0, 0)))
    dpiece(H, "Panel", "Body", panel, col=col, role="detail", pri=1.3)
    xs = [x] if screens == 1 else list(np.linspace(x - panel_w * 0.24, x + panel_w * 0.24, screens))
    for i, sx in enumerate(xs):
        H.prim(f"Screen{i + 1}", "Body", "Block", (min(1.0, panel_w / (screens + 1.2)), 0.62, 0.06), (sx, panel_top - 0.55, panel_z + 0.035),
               rot=(math.radians(-8), 0, 0), col=SCREEN, glow=True, role="light", pri=2.0)
    ms = []
    if ctrl == "stick":
        ms.append(stick(hip, floor_y, dz=-1.85, h=1.05))
    else:
        hn, cl = yoke(hip)
        ms += [hn, cl]
    for sx in (x - 0.5, x + 0.5):
        ms.append(xform(box((0.42, 0.62, 0.12), (0, 0, 0), r=0.04), (sx, floor_y + 0.42, z - 2.0), (-38, 0, 0)))
    if side_console:
        ms.append(box((0.35, 0.5, 1.2), (x - seat_w / 2 - 0.3, y + 0.25, z - 0.9), r=0.08))
        ms.append(tube([[x - seat_w / 2 - 0.3, y + 0.45, z - 0.9], [x - seat_w / 2 - 0.3, y + 0.95, z - 1.15]], 0.06, 6))
        ms.append(sphere(0.13, (x - seat_w / 2 - 0.3, y + 1.0, z - 1.17), segs=8))
    dpiece(H, "Controls", "Body", merge(*ms), col="gunmetal", mat="metal", role="detail", pri=1.6)
    dpiece(H, "Floor", "Body", F.floor(z - 2.6, z + 1.1, floor_y), col="darker", role="detail", pri=1.6)


def rescale(H, k):
    """Scale a finished hero's geometry by k about the origin (bones, direct meshes, SDF sculpts, patterns, prims,
    sockets): lifts a model authored at summon scale to real game scale before its sockets / clips are set."""
    H.bones = [(n, p, tuple(float(v) * k for v in pos)) for n, p, pos in H.bones]
    for p in H.parts:
        if p["kind"] == "piece":
            s = p["sdf"]
            if isinstance(s, D):
                p["sdf"] = D(direct.moved(s.mesh, (0, 0, 0), None, (k, k, k)))
            else:
                p["sdf"] = S.SDF(lambda q, _s=s: _s(q / k) * k)
            if p.get("pattern") is not None:
                p["pattern"] = (lambda P_, _f=p["pattern"]: _f(P_ / k))
        else:
            p["pos"] = tuple(v * k for v in p["pos"])
            p["size"] = tuple(v * k for v in p["size"])
    H.sockets = {n: (tuple(v * k for v in pos), b) for n, (pos, b) in H.sockets.items()}
    H.__dict__.pop("bounds_hint", None)
    fix_bounds(H)
