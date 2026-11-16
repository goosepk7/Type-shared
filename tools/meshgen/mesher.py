"""SDF -> triangle mesh -> .glb for tools/meshgen.

    mesh = build(sdf, box=(hx, hy, hz), tris=1200, res=112)

* samples the SDF on a grid covering the half-extent box (+ padding), marching cubes (skimage),
* light Taubin smoothing (removes voxel stair-steps without shrinking),
* quadric decimation to the triangle budget (fast_simplification via trimesh),
* re-centres the mesh on its bounds centre (Roblox MeshPart pivot = bounds centre) and stores the
  native size; `fit` optionally rescales per axis so the bounds equal an exact box,
* area-weighted smooth vertex normals.

`export_glb(mesh, path, name)` writes a single-node glTF binary whose node + mesh are named `name`
(the Roblox importer names the MeshPart after the node).
"""
from __future__ import annotations

import numpy as np
import trimesh
from skimage import measure


def sample(sdf, lo, hi, res):
    ext = hi - lo
    step = ext.max() / res
    n = np.maximum(np.ceil(ext / step).astype(int) + 1, 8)
    xs = [np.linspace(lo[i], lo[i] + step * (n[i] - 1), n[i]) for i in range(3)]
    X, Y, Z = np.meshgrid(*xs, indexing="ij")
    P = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    out = np.empty(len(P))
    CH = 400_000
    for i in range(0, len(P), CH):
        out[i : i + CH] = sdf(P[i : i + CH])
    return out.reshape(n), step


def _grad(sdf, V, e):
    d = sdf(V)
    g = np.zeros_like(V)
    for i in range(3):
        o = np.zeros(3)
        o[i] = e
        g[:, i] = sdf(V + o) - sdf(V - o)
    n = np.linalg.norm(g, axis=1, keepdims=True)
    return d, g / np.maximum(n, 1e-12)


def finish_direct(m, fit=None):
    """A mesh from direct.py (explicit vertices + normals): recentre on its bounds, optionally fit, keep normals."""
    N = np.asarray(m.direct_normals, float).copy()
    lo, hi = m.bounds
    origin = (lo + hi) / 2
    V = m.vertices - origin
    if fit is not None:
        k = np.asarray(fit, float) / np.maximum(hi - lo, 1e-6)
        V = V * k
        N = N / k
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    out = trimesh.Trimesh(V, m.faces, process=False)
    out.vertex_normals = N
    out.origin = origin
    return out


def build(sdf, box, tris=1200, res=112, smooth=6, fit=None, pad=0.12):
    if isinstance(sdf, trimesh.Trimesh):
        return finish_direct(sdf, fit)
    """box: rough half extents of the shape. The true bounds are found with a coarse pass over a
    region 2.5x larger, then the shape is sampled at `res` cells across its largest dimension."""
    hb = np.asarray(box, float)
    clo, chi = -hb * 2.5 - 0.1, hb * 2.5 + 0.1
    cvol, cstep = sample(sdf, clo, chi, 56)
    inside = np.argwhere(cvol < cstep * 0.5)
    if len(inside) == 0:
        raise ValueError("SDF is empty inside the sampling box")
    lo = clo + (inside.min(0) - 2) * cstep
    hi = clo + (inside.max(0) + 2) * cstep
    vol, step = sample(sdf, lo, hi, res)
    if vol.min() >= 0:
        raise ValueError("SDF is empty inside the sampling box")
    if (vol[0].min() < 0 or vol[-1].min() < 0 or vol[:, 0].min() < 0 or vol[:, -1].min() < 0 or vol[:, :, 0].min() < 0 or vol[:, :, -1].min() < 0):
        raise ValueError("shape touches the sampling boundary")
    verts, faces, _n, _v = measure.marching_cubes(vol, 0.0, spacing=(step, step, step))
    verts += lo
    m = trimesh.Trimesh(verts, faces[:, ::-1], process=True)  # skimage winds inward for our sign
    # keep the largest connected piece plus anything substantial (drop voxel crumbs)
    parts = m.split(only_watertight=False)
    if len(parts) > 1:
        big = max(len(q.faces) for q in parts)
        m = trimesh.util.concatenate([q for q in parts if len(q.faces) >= big * 0.02])
    if smooth:
        trimesh.smoothing.filter_taubin(m, lamb=0.5, nu=-0.53, iterations=smooth)
    if len(m.faces) > tris:
        m = m.simplify_quadric_decimation(face_count=int(tris))
        if len(m.faces) > tris * 1.1:  # flat-faceted shapes: retry with aggression
            m = m.simplify_quadric_decimation(percent=1 - tris / len(m.faces), aggression=9)
    m.remove_unreferenced_vertices()
    m.merge_vertices()
    if m.volume < 0:
        m.invert()
    # snap decimated vertices back onto the true surface and take normals from the SDF gradient:
    # decimation leaves facets slightly off-surface, which shades as pits; the analytic normals keep
    # the shading as smooth as the full-resolution surface.
    V = m.vertices.copy()
    for _ in range(3):
        d, g = _grad(sdf, V, step * 0.5)
        V = V - (d * 0.8)[:, None] * g
    _, g = _grad(sdf, V, step * 0.5)
    m = trimesh.Trimesh(V, m.faces, process=False)
    m.sdf_normals = g
    lo2, hi2 = m.bounds
    origin = (lo2 + hi2) / 2  # authoring-space centre of the bounds (MeshPart pivot)
    m.apply_translation(-origin)
    N = m.sdf_normals
    if fit is not None:
        size = m.bounds[1] - m.bounds[0]
        k = np.asarray(fit, float) / np.maximum(size, 1e-6)
        m = trimesh.Trimesh(m.vertices * k, m.faces, process=False)
        N = N / k
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    # keep the analytic normals where they agree with the face fan, else fall back to the mesh's
    vn = m.vertex_normals
    bad = (N * vn).sum(1) < 0.3
    N[bad] = vn[bad]
    m.vertex_normals = N
    m.origin = origin
    return m


def flat_faces(m, eps=0.004, min_frac=0.03):
    """Names of the bounding-box faces ("+x", "-y", ...) on which the mesh has planar area (more than
    min_frac of that box face). The Summon z-fighting checker relies on this: a piece with no flat box face
    cannot be coplanar with anything, and a "box" piece's flat faces lie on the faces of the primitive it
    replaces, which the checker already tests (docs/SUMMON.md)."""
    lo, hi = m.bounds
    ext = np.maximum(hi - lo, 1e-9)
    tri = m.triangles
    area = m.area_faces
    out = []
    for ax in range(3):
        o = [a for a in range(3) if a != ax]
        box_area = ext[o[0]] * ext[o[1]]
        for sign, plane in (("-", lo[ax]), ("+", hi[ax])):
            on = np.all(np.abs(tri[:, :, ax] - plane) < eps * ext[ax], axis=1)
            if area[on].sum() > min_frac * box_area:
                out.append(sign + "xyz"[ax])
    return out


# Verified in a live Roblox server (tools/meshgen/README.md): the glTF importer keeps 1 unit = 1 stud,
# keeps COLOR_0 vertex colours, and turns the model 180 degrees about Y (glTF faces +Z, Roblox -Z).
# We author in Roblox space (-Z front), so the file is pre-rotated by 180 degrees about Y.
FLIP = np.array([-1.0, 1.0, -1.0])


def bake_ao(m: trimesh.Trimesh, rays=48, dist=None, lo=0.62, seed=0):
    """Per-vertex ambient occlusion (greyscale 0..1). Hemisphere rays against the mesh itself."""
    from trimesh.ray.ray_pyembree import RayMeshIntersector

    ext = (m.bounds[1] - m.bounds[0]).max()
    dist = dist or ext * 0.35
    rng = np.random.default_rng(seed)
    d = rng.normal(size=(rays, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    V, N = m.vertices, m.vertex_normals
    rt = RayMeshIntersector(m)
    nv = len(V)
    D = np.repeat(d[None], nv, 0)
    flip = (D * N[:, None, :]).sum(2) < 0
    D[flip] *= -1
    w = (D * N[:, None, :]).sum(2)  # cosine weight
    O = np.repeat((V + N * ext * 0.004)[:, None, :], rays, 1)
    loc, idx_ray, _ = rt.intersects_location(O.reshape(-1, 3), D.reshape(-1, 3), multiple_hits=False)
    hit = np.zeros(nv * rays, bool)
    if len(idx_ray):
        dd = np.linalg.norm(loc - O.reshape(-1, 3)[idx_ray], axis=1)
        hit[idx_ray[dd < dist]] = True
    hit = hit.reshape(nv, rays)
    open_ = ((~hit) * w).sum(1) / np.maximum(w.sum(1), 1e-6)
    ao = lo + (1 - lo) * np.clip(open_, 0, 1) ** 0.8
    return ao


def export_glb(m: trimesh.Trimesh, path: str, name: str, ao=None):
    mm = trimesh.Trimesh(m.vertices * FLIP, m.faces, vertex_normals=m.vertex_normals * FLIP, process=False)
    if ao is not None:
        g = (np.clip(ao, 0, 1) * 255).astype(np.uint8)
        mm.visual = trimesh.visual.ColorVisuals(mm, vertex_colors=np.column_stack([g, g, g, np.full_like(g, 255)]))
    mm.vertex_normals = m.vertex_normals * FLIP  # (re)set after the visual: it clears cached normals
    sc = trimesh.Scene()
    sc.add_geometry(mm, node_name=name, geom_name=name)
    data = sc.export(file_type="glb", include_normals=True)
    with open(path, "wb") as f:
        f.write(data)
    return len(data)


def load_glb(path: str) -> trimesh.Trimesh:
    """Load a piece back into Roblox space (undo the export flip). Vertex colours kept if present."""
    s = trimesh.load(path, force="scene", process=False)
    m = list(s.geometry.values())[0]  # single node, identity transform (keeps the file's normals)
    n = m.vertex_normals * FLIP
    return trimesh.Trimesh(m.vertices * FLIP, m.faces, vertex_normals=n, process=False)
