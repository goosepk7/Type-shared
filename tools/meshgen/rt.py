"""Embree ray tracer for contact sheets (used by tools/render_blueprint.py and tools/meshgen/preview.py).
Ported from Type-defend tools/render/rt.py; additions: "Ellipsoid" parts, "unit" pieces through
`part_from_piece`, ForceField shells drawn as translucent rim-lit layers, a `mesh_dir` override.

Everything is triangulated (Blocks / Wedges with flat normals, Balls and Cylinders smooth, MeshParts
loaded from tools/meshgen/out/<piece>.glb and scaled to the part Size, the same way a Roblox
MeshPart scales its mesh to its Size) and traced with Embree:

* orthographic camera, 2x2 supersampling,
* key light with ray-traced soft-ish shadows (4 jittered shadow rays), sky/ground hemisphere fill,
  ray-traced ambient occlusion (6 rays), back rim light, Blinn specular for Metal / Glass / Foil,
* Neon is emissive, translucent parts are composited as one layer over the opaque hit,
* a ground disc at y=0 catches the contact shadow and AO,
* baked mesh vertex colours (AO) multiply the part colour, as Roblox does with COLOR_0.
"""
import os
import numpy as np
import trimesh
from trimesh.ray.ray_pyembree import RayMeshIntersector

HERE = os.path.dirname(os.path.abspath(__file__))
MESH_DIR = os.path.join(HERE, "out")
FLIP = np.array([-1.0, 1.0, -1.0])

_unit = {}
_piece = {}


def _flat(v, f):
    """Split vertices per face so normals are flat."""
    tri = v[f]  # (F,3,3)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    V = tri.reshape(-1, 3)
    N = np.repeat(n, 3, axis=0)
    F = np.arange(len(V)).reshape(-1, 3)
    return V, N, F


def unit(shape):
    """Unit-size (1x1x1 box) triangulation: (V, N, F)."""
    if shape in _unit:
        return _unit[shape]
    if shape in ("Ball", "Ellipsoid"):
        m = trimesh.creation.icosphere(subdivisions=3, radius=0.5)
        r = (m.vertices, m.vertex_normals.copy(), m.faces)
    elif shape == "Cylinder":
        seg = 40
        a = np.linspace(0, 2 * np.pi, seg, endpoint=False)
        y, z = 0.5 * np.cos(a), 0.5 * np.sin(a)
        Vs, Ns, Fs = [], [], []
        # side (smooth)
        for x in (-0.5, 0.5):
            Vs.append(np.column_stack([np.full(seg, x), y, z]))
            Ns.append(np.column_stack([np.zeros(seg), np.cos(a), np.sin(a)]))
        V = np.vstack(Vs)
        N = np.vstack(Ns)
        F = []
        for i in range(seg):
            j = (i + 1) % seg
            F += [[i, j, seg + i], [j, seg + j, seg + i]]
        F = np.array(F)
        # caps (flat)
        capV, capN, capF = [], [], []
        base = len(V)
        for x, s in ((-0.5, -1), (0.5, 1)):
            c = len(capV)
            capV.append([x, 0, 0])
            capN.append([s, 0, 0])
            for i in range(seg):
                capV.append([x, y[i], z[i]])
                capN.append([s, 0, 0])
            for i in range(seg):
                j = (i + 1) % seg
                capF.append([base + c, base + c + 1 + i, base + c + 1 + j])
        V = np.vstack([V, capV])
        N = np.vstack([N, capN])
        F = np.vstack([F, capF])
        r = (V, N, F)
    elif shape == "Wedge":
        # vertical edge at +Z, slope descending to the front-bottom edge (Roblox WedgePart)
        v = np.array([[-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5], [-0.5, 0.5, 0.5], [0.5, 0.5, 0.5]])
        f = np.array([[0, 2, 1], [0, 3, 2], [3, 4, 5], [3, 5, 2], [0, 4, 3], [1, 2, 5], [0, 1, 5], [0, 5, 4]])
        r = _flat(v, f)
    else:
        m = trimesh.creation.box((1, 1, 1))
        r = _flat(m.vertices, m.faces)
    _unit[shape] = r
    return r


def piece_mesh(pid):
    """Normalised piece: vertices in a unit box (bounds -0.5..0.5), smooth normals, AO colours."""
    if pid in _piece:
        return _piece[pid]
    path = os.path.join(MESH_DIR, pid + ".glb")
    if not os.path.exists(path):
        _piece[pid] = None
        return None
    sc = trimesh.load(path, force="scene", process=False)
    m = list(sc.geometry.values())[0]  # single node, identity transform (keeps the file's normals)
    V = m.vertices * FLIP
    lo, hi = V.min(0), V.max(0)
    k = np.maximum(hi - lo, 1e-6)
    V = (V - (lo + hi) / 2) / k
    N = (m.vertex_normals * FLIP) * k  # normals transform by the inverse of the (1/k) scale
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    ao = np.ones(len(V))
    try:
        vc = m.visual.vertex_colors
        if vc is not None and len(vc) == len(V):
            ao = vc[:, 0] / 255.0
    except Exception:
        pass
    _piece[pid] = (V, N, m.faces, ao)
    return _piece[pid]


_manifest = None


def manifest():
    global _manifest
    if _manifest is None:
        import json

        path = os.path.join(MESH_DIR, "manifest.json")
        _manifest = json.load(open(path)) if os.path.exists(path) else {}
    return _manifest


def piece_box(pid, size, cf):
    """Box (size, cf) a piece occupies when it stands in for a primitive of `size` at `cf` (MeshLibrary.fit):
    "box" pieces fill the primitive's box, "unit"/"anchor" pieces are authored in its unit frame."""
    info = manifest().get(pid)
    if info is None or piece_mesh(pid) is None:
        return None
    size = np.asarray(size, float)
    if info.get("kind") == "box":
        return size.tolist(), list(cf)
    R = rot(cf)
    pos = np.array(cf[:3]) + R @ (np.array(info["origin"]) * size)
    return (np.array(info["size"]) * size).tolist(), pos.tolist() + list(cf[3:])


def rot(c):
    return np.array([[c[3], c[4], c[5]], [c[6], c[7], c[8]], [c[9], c[10], c[11]]])


METAL = {"Metal", "DiamondPlate", "CorrodedMetal", "Foil", "Glass"}


def triangulate(parts):
    """-> dict of arrays for opaque and translucent sets."""
    sets = {"op": [], "tr": []}
    for p in parts:
        if p["tr"] >= 0.95:
            continue
        size = np.array(p["size"], float)
        R = rot(p["cf"])
        P = np.array(p["cf"][:3])
        ao = None
        if p["s"] == "Mesh":
            pm = piece_mesh(p.get("piece", ""))
            if pm is None:
                V, N, F = unit("Block")
            else:
                V, N, F, ao = pm
        else:
            V, N, F = unit(p["s"])
        if p["s"] == "Ball":
            sz = np.full(3, size.min())
        elif p["s"] == "Cylinder":
            r = min(size[1], size[2])
            sz = np.array([size[0], r, r])
        else:
            sz = size
        Vw = (V * sz) @ R.T + P
        Nw = (N / np.maximum(sz, 1e-6)) @ R.T
        Nw /= np.maximum(np.linalg.norm(Nw, axis=1, keepdims=True), 1e-12)
        col = np.array(p["col"], float)
        aoV = ao if ao is not None else np.ones(len(V))
        mat = p.get("mat", "SmoothPlastic")
        flags = np.array([1.0 if mat == "Neon" else 0.0, 1.0 if mat in METAL else 0.0, 1.0 if mat == "ForceField" else 0.0])
        sets["tr" if (p["tr"] > 0.05 or mat == "ForceField") else "op"].append((Vw, Nw, F, col, aoV, flags, p["tr"]))
    out = {}
    for k, lst in sets.items():
        if not lst:
            out[k] = None
            continue
        Vs, Ns, Fs, C, A, FL, TR = [], [], [], [], [], [], []
        off = 0
        for Vw, Nw, F, col, aoV, flags, tr in lst:
            Vs.append(Vw)
            Ns.append(Nw)
            Fs.append(F + off)
            C.append(np.tile(col, (len(F), 1)))
            A.append(aoV)
            FL.append(np.tile(flags, (len(F), 1)))
            TR.append(np.full(len(F), tr))
            off += len(Vw)
        V = np.vstack(Vs)
        F = np.vstack(Fs)
        out[k] = {
            "mesh": trimesh.Trimesh(V, F, process=False),
            "N": np.vstack(Ns),
            "C": np.vstack(C),
            "A": np.concatenate(A),
            "FL": np.vstack(FL),
            "TR": np.concatenate(TR),
        }
    return out


def _interp(S, tri, loc):
    m = S["mesh"]
    f = m.faces[tri]
    bc = trimesh.triangles.points_to_barycentric(m.triangles[tri], loc)
    n = (S["N"][f] * bc[:, :, None]).sum(1)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    a = (S["A"][f] * bc).sum(1)
    return n, a


LIGHT = np.array([-0.5, 0.85, -0.55])
LIGHT /= np.linalg.norm(LIGHT)
RIM = np.array([0.55, 0.35, 0.75])
RIM /= np.linalg.norm(RIM)
SKY = np.array([0.62, 0.7, 0.85])
GROUND = np.array([0.42, 0.36, 0.3])
BG_TOP = np.array([0.20, 0.22, 0.27])
BG_BOT = np.array([0.09, 0.10, 0.12])


def render(parts, az, el, W, ss=2, ao_rays=6, ground=True, bounds_pts=None, bg=None):
    sets = triangulate(parts)
    op = sets["op"]
    allV = np.vstack([s["mesh"].vertices for s in sets.values() if s is not None])
    if bounds_pts is not None:
        allV = bounds_pts
    a, e = np.radians(az), np.radians(el)
    fwd = np.array([-np.sin(a) * np.cos(e), -np.sin(e), np.cos(a) * np.cos(e)])
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    ctr = (allV.min(0) + allV.max(0)) / 2
    pr = (allV - ctr) @ np.stack([right, up]).T
    ext = np.abs(pr).max() * 1.1 + 0.25
    groundR = max(np.abs(allV[:, [0, 2]]).max() * 1.6, 2.0)
    if ground and op is not None:
        g = trimesh.creation.cylinder(radius=groundR, height=0.02, sections=64)  # axis Z
        g.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        g.apply_translation([0, -0.011, 0])
        gN = np.tile([0, 1.0, 0], (len(g.vertices), 1))
        gm = trimesh.Trimesh(np.vstack([op["mesh"].vertices, g.vertices]), np.vstack([op["mesh"].faces, g.faces + len(op["mesh"].vertices)]), process=False)
        nG = len(g.faces)
        op = {
            "mesh": gm,
            "N": np.vstack([op["N"], gN]),
            "C": np.vstack([op["C"], np.tile([-1, -1, -1], (nG, 1))]),  # marker: ground
            "A": np.concatenate([op["A"], np.ones(len(g.vertices))]),
            "FL": np.vstack([op["FL"], np.zeros((nG, 3))]),
            "TR": np.concatenate([op["TR"], np.zeros(nG)]),
        }
    S = W * ss
    xs = np.linspace(-ext, ext, S)
    ys = np.linspace(ext, -ext, S)
    X, Y = np.meshgrid(xs, ys)
    O = (ctr + X[..., None] * right + Y[..., None] * up - fwd * 200).reshape(-1, 3)
    D = np.tile(fwd, (len(O), 1))
    yy = np.linspace(0, 1, S)[:, None].repeat(S, 1).reshape(-1)
    col = BG_TOP * (1 - yy[:, None]) + BG_BOT * yy[:, None]
    if bg is not None:
        col = np.tile(np.asarray(bg, float), (len(O), 1))
    depth = np.full(len(O), np.inf)
    rng = np.random.default_rng(7)
    if op is not None:
        rt = RayMeshIntersector(op["mesh"])
        tri, ray, loc = rt.intersects_id(O, D, multiple_hits=False, return_locations=True)
        if len(tri):
            n, aoV = _interp(op, tri, loc)
            n = np.where(((n * D[ray]).sum(1) > 0)[:, None], -n, n)
            depth[ray] = ((loc - O[ray]) * fwd).sum(1)
            base = op["C"][tri]
            isG = base[:, 0] < 0
            base = np.where(isG[:, None], np.array([0.24, 0.25, 0.28]), base)
            fl = op["FL"][tri]
            P0 = loc + n * 1e-3
            # shadows: 4 jittered rays toward the key light
            vis = np.zeros(len(tri))
            for k in range(4):
                L = LIGHT + rng.normal(scale=0.05, size=3)
                L /= np.linalg.norm(L)
                hit = rt.intersects_any(P0, np.tile(L, (len(P0), 1)))
                vis += ~hit
            vis /= 4
            # ambient occlusion
            occ = np.zeros(len(tri))
            if ao_rays:
                for k in range(ao_rays):
                    d = rng.normal(size=(len(P0), 3))
                    d /= np.linalg.norm(d, axis=1, keepdims=True)
                    d = np.where(((d * n).sum(1) < 0)[:, None], -d, d)
                    d = (d + n) / 2
                    d /= np.linalg.norm(d, axis=1, keepdims=True)
                    t2, r2, l2 = rt.intersects_id(P0, d, multiple_hits=False, return_locations=True)
                    if len(t2):
                        dist = np.linalg.norm(l2 - P0[r2], axis=1)
                        occ[r2] += np.clip(1.2 - dist / 1.6, 0, 1)
                occ /= ao_rays
            ao = (1 - 0.75 * occ) * (0.55 + 0.45 * aoV)
            lam = np.clip(n @ LIGHT, 0, 1)
            hemi = SKY * (0.5 + 0.5 * n[:, 1:2]) + GROUND * (0.5 - 0.5 * n[:, 1:2])
            rim = np.clip(n @ RIM, 0, 1) ** 2
            shade = base * (1.05 * lam[:, None] * vis[:, None] * np.array([1.0, 0.96, 0.9]) + 0.5 * hemi * ao[:, None]) + 0.18 * rim[:, None] * ao[:, None]
            h = LIGHT - fwd
            h /= np.linalg.norm(h)
            spec = np.clip(n @ h, 0, 1) ** np.where(fl[:, 1] > 0, 40, 18)
            shade += (np.where(fl[:, 1] > 0, 0.45, 0.08) * spec * vis)[:, None]
            glow = fl[:, 0] > 0
            shade[glow] = np.clip(base[glow] * 1.25 + 0.08, 0, 1.2)
            # ground is a shadow catcher: background colour darkened by shadow + contact AO
            bgc = col[ray]
            gshade = bgc * (0.62 + 0.38 * vis[:, None]) * (1 - 0.55 * occ[:, None])
            shade = np.where(isG[:, None], gshade, shade)
            col[ray] = shade
    tr = sets["tr"]
    if tr is not None:
        rt2 = RayMeshIntersector(tr["mesh"])
        tri, ray, loc = rt2.intersects_id(O, D, multiple_hits=False, return_locations=True)
        if len(tri):
            dd = ((loc - O[ray]) * fwd).sum(1)
            ok = dd < depth[ray]
            tri, ray, loc = tri[ok], ray[ok], loc[ok]
            n, _ = _interp(tr, tri, loc)
            n = np.where(((n * D[ray]).sum(1) > 0)[:, None], -n, n)
            base = tr["C"][tri]
            lam = np.clip(n @ LIGHT, 0, 1)
            fl = tr["FL"][tri]
            sh = base * (0.45 + 0.75 * lam[:, None])
            fres = (1 - np.abs((n * fwd).sum(1))) ** 2
            sh += 0.25 * fres[:, None]
            sh = np.where((fl[:, 0] > 0)[:, None], base * 1.2, sh)
            alpha = (1 - tr["TR"][tri]) * (0.75 + 0.25 * fres)
            ff = fl[:, 2] > 0  # ForceField: additive-looking rim-lit shell
            sh = np.where(ff[:, None], base * (0.7 + 0.9 * fres[:, None]) + 0.1, sh)
            alpha = np.where(ff, (1 - tr["TR"][tri]) * (0.3 + 0.6 * fres), alpha)
            col[ray] = col[ray] * (1 - alpha[:, None]) + sh * alpha[:, None]
    col = np.clip(col, 0, None)
    col = col / (1 + 0.25 * col)  # gentle highlight roll-off
    col = np.clip(col * 1.12, 0, 1) ** (1 / 1.08)
    img = col.reshape(S, S, 3)
    if ss > 1:
        img = img.reshape(W, ss, W, ss, 3).mean((1, 3))
    return (img * 255).astype(np.uint8)
