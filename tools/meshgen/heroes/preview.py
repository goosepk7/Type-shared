#!/usr/bin/env python3
"""Preview hero models with the ray tracer (tools/meshgen/rt.py): every hero in its rest pose from a few angles,
plus optional animation strips sampled from its clips (FK exactly like Motor6D.Transform).

  python3 tools/meshgen/heroes/preview.py out.png [--only lion,tiger] [--family felines] [--views 3] [--size 320]
         [--anim Move --frames 6] [--cols 3] [--colours primary=#C8963E,secondary=#6B4423]

Colours: each hero may define H.preview = {key: "#hex"} for its natural look; unknown keys fall back to a neutral
preview palette that mirrors Summon/Style.luau's Solid defaults.
"""
import argparse, math, os, sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
MG = os.path.dirname(HERE)
sys.path.insert(0, MG)
sys.path.insert(0, HERE)

import build  # noqa: E402
import kit  # noqa: E402
import rt  # noqa: E402


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


BASE = {
    "primary": "#9AA5B1", "secondary": "#E4E7EB", "belly": "#EDE3D0", "dark": "#4A4F57", "darker": "#2E3238", "light": "#C9D0D8",
    "accent": "#B0763C", "inner": "#E9B7B7", "horn": "#EFE3C8", "claw": "#2B2622", "tooth": "#FFF8E8", "nail": "#D9CDB4",
    "hoof": "#3B2F2A", "beak": "#F2A93B", "eyeWhite": "#FFFFFF", "pupil": "#15131A", "iris": "#E8B423", "shine": "#FFFFFF",
    "eyeGlow": "#FFE9A0", "metal": "#A7B1BC", "steel": "#7C8794", "gunmetal": "#3C434C", "gold": "#E8B53A", "wood": "#8A5A33",
    "darkWood": "#5A3820", "stone": "#A39E93", "glass": "#9FD8F2", "tyre": "#24262B", "leaf": "#4E9A3A", "skin": "#F1C29A",
    "hair": "#5A3A24", "cloth": "#9AA5B1", "cloth2": "#E4E7EB", "white": "#F7F7F7", "black": "#1D1D22", "red": "#D9372B",
    "sail": "#F3ECDD", "cream": "#FFF3D6", "mouth": "#3B1820", "tongue": "#E8607A", "nose": "#3A2A28", "leather": "#6B4423",
    "membrane": "#B07A6A", "glow": "#FFD27A", "gem": "#6FD3FF",
}
MATS = {"metal": "Metal", "glass": "Glass", "neon": "Neon", "wood": "Wood", "cloth": "Fabric", "stone": "Slate", "foil": "Foil"}


def euler(rx, ry, rz):
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    X = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return X @ Y @ Z


def sample_clip(H, name, t):
    c = H.clips.get(name)
    if not c:
        return {}
    n, L = c["keys"], c["len"]
    if c["loop"]:
        u = (t % L) / L * n
        i0 = int(math.floor(u)) % n
        f = u - math.floor(u)
        idx = [(i0 - 1) % n, i0, (i0 + 1) % n, (i0 + 2) % n]
    else:
        u = min(max(t / L, 0), 1) * (n - 1)
        i0 = min(int(u), n - 2)
        f = u - i0
        idx = [max(i0 - 1, 0), i0, i0 + 1, min(i0 + 2, n - 1)]
    out = {}
    for b, vals in c["tracks"].items():
        p0, p1, p2, p3 = (np.array(vals[i]) for i in idx)
        # Catmull-Rom
        v = 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)
        out[b] = v
    return out


def world_frames(H, pose):
    """bone -> (R, P) world transform of the bone's frame (rest frame = identity rotation at bone pos)."""
    W = {}
    for name, parent, pos in H.bones:
        pos = np.array(pos)
        v = pose.get(name)
        Rl = euler(*v[3:6]) if v is not None else np.eye(3)
        Tl = np.array(v[:3]) if v is not None else np.zeros(3)
        if parent is None:
            R0, P0 = np.eye(3), pos
        else:
            Rp, Pp = W[parent]
            ppos = np.array(H.bones[H.bidx[parent]][2])
            R0, P0 = Rp, Pp + Rp @ (pos - ppos)
        W[name] = (R0 @ Rl, P0 + R0 @ Tl)
    return W


def parts_for(H, pose, colours, man):
    W = world_frames(H, pose)
    out = []
    for p in H.parts:
        R, P = W[p["bone"]]
        bpos = np.array(H.bones[H.bidx[p["bone"]]][2])
        if p["kind"] == "piece":
            info = man.get(p["key"])
            if info is None:
                continue
            c = np.array(info["centre"])
            size = info["size"]
            Rp = np.eye(3)
            s = "Mesh"
        else:
            c = np.array(p["pos"])
            size = p["size"]
            Rp = euler(*p["rot"])
            s = p["shape"]
        wpos = P + R @ (c - bpos)
        wR = R @ Rp
        col = p["col"]
        rgb = tuple(col) if isinstance(col, (list, tuple)) else hexc(colours.get(col, BASE.get(col, "#FF00FF")))
        mat = "Neon" if p.get("glow") else MATS.get(p["mat"], "SmoothPlastic")
        out.append({"s": s, "piece": p.get("key", ""), "size": list(size), "cf": list(wpos) + list(wR.reshape(-1)), "col": rgb,
                    "tr": p.get("tr", 0) or 0, "mat": mat})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--only", default="")
    ap.add_argument("--family", default="")
    ap.add_argument("--views", type=int, default=3)
    ap.add_argument("--size", type=int, default=300)
    ap.add_argument("--anim", default="")
    ap.add_argument("--frames", type=int, default=6)
    ap.add_argument("--cols", type=int, default=1)
    ap.add_argument("--colours", default="")
    a = ap.parse_args()
    build.load()
    import json

    man = json.load(open(os.path.join(MG, "out", "manifest.json")))
    hids = [h for h in kit.REG if (not a.only or h in a.only.split(",")) and (not a.family or kit.FAMILY[h] in a.family.split(","))]
    if a.only:
        hids = [h for h in a.only.split(",") if h in kit.REG]
    over = dict(kv.split("=") for kv in a.colours.split(",") if "=" in kv)
    views = [(35, 18), (150, 12), (270, 4), (215, 30)][: a.views]
    W = a.size
    tiles = []
    for hid in hids:
        H = build.get(hid)
        colours = dict(getattr(H, "preview", {}) or {})
        colours.update(over)
        row = []
        rest = sample_clip(H, "Idle", 0.0)
        pts = None
        for az, el in views:
            parts = parts_for(H, rest, colours, man)
            img = rt.render(parts, az, el, W, ss=2, ao_rays=6, ground=True)
            row.append(Image.fromarray(img))
        if a.anim and a.anim in H.clips:
            L = H.clips[a.anim]["len"]
            for i in range(a.frames):
                pose = sample_clip(H, a.anim, L * i / a.frames)
                parts = parts_for(H, pose, colours, man)
                img = rt.render(parts, 90, 6, W, ss=1, ao_rays=2, ground=True)
                row.append(Image.fromarray(img))
        tiles.append((hid, row))
    per = max(len(r) for _, r in tiles)
    cols = a.cols
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * per * W, rows * (W + 18)), (24, 25, 30))
    dr = ImageDraw.Draw(sheet)
    for i, (hid, row) in enumerate(tiles):
        x0 = (i % cols) * per * W
        y0 = (i // cols) * (W + 18)
        H = build.get(hid)
        n = sum(1 for p in H.parts)
        tris = sum(man.get(p.get("key", ""), {}).get("tris", 0) for p in H.parts if p["kind"] == "piece")
        dr.text((x0 + 4, y0 + 3), f"{hid}  [{kit.FAMILY[hid]}]  {n} parts  {tris} tris", fill=(235, 235, 235))
        for j, im in enumerate(row):
            sheet.paste(im, (x0 + j * W, y0 + 18))
    sheet.save(a.out)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
