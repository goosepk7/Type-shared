#!/usr/bin/env python3
"""Render Summon blueprints (JSON from tools/render_blueprint.luau) to PNG contact sheets.

Each blueprint becomes a tile with four orthographic views: front (looking at the face, from -Z), side (from +X),
top (from +Y) and a 3/4 view, flat-shaded with a key light. Spectral parts are drawn translucent/additive-ish.

usage: python3 tools/render_blueprint.py blueprints.json out.png [--cols N] [--tile PX] [--views front,side,top,iso]
"""
import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SS = 2  # supersampling


def frame_matrix(cf):
    p = np.array(cf[0:3], dtype=float)
    r = np.array(cf[3:12], dtype=float).reshape(3, 3)
    return p, r


def sphere_mesh(nu=14, nv=9):
    verts, tris = [], []
    for j in range(nv + 1):
        th = math.pi * j / nv
        for i in range(nu):
            ph = 2 * math.pi * i / nu
            verts.append((math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph)))
    for j in range(nv):
        for i in range(nu):
            a = j * nu + i
            b = j * nu + (i + 1) % nu
            c = (j + 1) * nu + i
            d = (j + 1) * nu + (i + 1) % nu
            if j != 0:
                tris.append((a, b, c))
            if j != nv - 1:
                tris.append((b, d, c))
    return np.array(verts) * 0.5, tris


SPHERE = sphere_mesh()


def cylinder_mesh(n=16):
    verts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        verts.append((0.5, math.cos(a) * 0.5, math.sin(a) * 0.5))
        verts.append((-0.5, math.cos(a) * 0.5, math.sin(a) * 0.5))
    verts.append((0.5, 0, 0))
    verts.append((-0.5, 0, 0))
    tris = []
    ca, cb = 2 * n, 2 * n + 1
    for i in range(n):
        a0, b0 = 2 * i, 2 * i + 1
        a1, b1 = 2 * ((i + 1) % n), 2 * ((i + 1) % n) + 1
        tris.append((a0, a1, b0))
        tris.append((a1, b1, b0))
        tris.append((ca, a1, a0))
        tris.append((cb, b0, b1))
    return np.array(verts), tris


CYL = cylinder_mesh()

BOX_V = np.array([(x, y, z) for x in (-0.5, 0.5) for y in (-0.5, 0.5) for z in (-0.5, 0.5)])
BOX_T = [
    (0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1),
    (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3),
]
# wedge: bottom 4 + top back edge
WEDGE_V = np.array([
    (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (-0.5, -0.5, 0.5),
    (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5),
])
WEDGE_T = [(0, 1, 2), (0, 2, 3), (3, 2, 5), (3, 5, 4), (1, 5, 2), (0, 3, 4), (0, 4, 5), (0, 5, 1)]


def part_tris(p):
    shape = p["shape"]
    size = np.array(p["size"], dtype=float)
    if shape in ("Ball", "Ellipsoid"):
        v, t = SPHERE
        if shape == "Ball":
            size = np.array([min(size)] * 3)
    elif shape == "Cylinder":
        v, t = CYL
        d = min(size[1], size[2])
        size = np.array([size[0], d, d])
    elif shape == "Wedge":
        v, t = WEDGE_V, WEDGE_T
    else:
        v, t = BOX_V, BOX_T
    pos, rot = frame_matrix(p["cf"])
    world = (v * size) @ rot.T + pos
    return world, t


def view_rot(view):
    # returns R such that camera coords = R @ world ; x right, y up, z toward camera
    if view == "front":  # camera at -Z looking +Z: model's right (+X) appears on screen-left
        return np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]], dtype=float)
    if view == "side":  # camera at +X
        return np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], dtype=float)
    if view == "top":  # camera above, forward (-Z) is screen-up
        return np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=float)
    # iso 3/4 from front-right-above
    yaw, pitch = math.radians(-145), math.radians(-24)
    ry = np.array([[math.cos(yaw), 0, math.sin(yaw)], [0, 1, 0], [-math.sin(yaw), 0, math.cos(yaw)]])
    rx = np.array([[1, 0, 0], [0, math.cos(pitch), -math.sin(pitch)], [0, math.sin(pitch), math.cos(pitch)]])
    return rx @ ry


LIGHT = np.array([0.45, 0.8, 0.4])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def render_view(bp, view, size):
    W = H = size * SS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    R = view_rot(view)
    polys = []
    allpts = []
    members = bp.get("members") or [None]
    for m in members:
        mp, mr = (np.zeros(3), np.eye(3)) if m is None else frame_matrix(m)
        for p in bp["parts"]:
            tr = p.get("transparency", 0)
            if tr >= 0.99:
                continue
            world, tris = part_tris(p)
            world = world @ mr.T + mp
            cam = world @ R.T
            allpts.append(cam)
            col = np.array(p.get("colour", [0.7, 0.7, 0.7]))
            mat = p.get("material", "SmoothPlastic")
            for t in tris:
                a, b, c = world[t[0]], world[t[1]], world[t[2]]
                n = np.cross(b - a, c - a)
                ln = np.linalg.norm(n)
                if ln < 1e-12:
                    continue
                n /= ln
                cn = R @ n
                if cn[2] < 0:  # back-facing
                    continue
                if mat == "Neon":
                    shade = col * 1.05 + 0.12
                elif mat == "ForceField":
                    shade = col * (0.55 + 0.6 * (1 - abs(cn[2])))  # fresnel rim
                else:
                    lam = max(0.0, float(np.dot(n, LIGHT)))
                    shade = col * (0.42 + 0.62 * lam)
                alpha = 1 - tr
                if mat == "ForceField":
                    alpha *= 0.55
                if mat == "Glass":
                    alpha *= 0.8
                pa, pb, pc = cam[t[0]], cam[t[1]], cam[t[2]]
                depth = (pa[2] + pb[2] + pc[2]) / 3
                polys.append((depth, (pa, pb, pc), np.clip(shade, 0, 1), alpha))
    if not allpts:
        return img.resize((size, size), Image.LANCZOS)
    pts = np.vstack(allpts)
    mn, mx = pts[:, :2].min(0), pts[:, :2].max(0)
    span = max(mx[0] - mn[0], mx[1] - mn[1], 1e-3)
    scale = (W * 0.86) / span
    cx, cy = (mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2
    draw = ImageDraw.Draw(img, "RGBA")
    # ground line for front/side
    if view in ("front", "side"):
        gy = H / 2 - (0 - cy) * scale
        draw.line([(0, gy), (W, gy)], fill=(120, 120, 130, 120), width=SS)
    polys.sort(key=lambda q: q[0])
    for depth, tri, shade, alpha in polys:
        xy = [(W / 2 + (v[0] - cx) * scale, H / 2 - (v[1] - cy) * scale) for v in tri]
        c = tuple(int(x * 255) for x in shade) + (int(alpha * 255),)
        draw.polygon(xy, fill=c)
    return img.resize((size, size), Image.LANCZOS)


def tile(bp, tile_px, views):
    vsz = tile_px
    lab = 34
    img = Image.new("RGB", (vsz * len(views), vsz + lab), (28, 30, 36))
    for i, v in enumerate(views):
        bg = Image.new("RGBA", (vsz, vsz), (40, 43, 52, 255) if i % 2 == 0 else (44, 47, 57, 255))
        r = render_view(bp, v, vsz)
        bg.alpha_composite(r)
        img.paste(bg.convert("RGB"), (i * vsz, lab))
    d = ImageDraw.Draw(img)
    st = bp.get("stats", {})
    text = f'{bp["id"]}  [{bp["style"]} {bp["size"]}]  {bp.get("builder","")}  parts {st.get("parts")}/{st.get("budget")}  drop {st.get("dropped")}  fix {st.get("fixes")}'
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 13)
    except Exception:
        font = ImageFont.load_default()
    if "label" in bp:
        # gallery tiles: phrase on line 1, flags (red) or stats on line 2
        try:
            small = ImageFont.truetype("DejaVuSans.ttf", 11)
        except Exception:
            small = font
        d.text((4, 2), bp["label"], fill=(230, 232, 240), font=small)
        flags = bp.get("flags") or []
        if flags:
            d.text((4, 17), "FLAG: " + ", ".join(flags), fill=(255, 110, 100), font=small)
        else:
            d.text((4, 17), f'{bp["style"]} {st.get("parts")}/{st.get("budget")}p', fill=(150, 156, 170), font=small)
        if flags:
            d.rectangle([0, 0, img.size[0] - 1, img.size[1] - 1], outline=(220, 70, 60), width=2)
    else:
        d.text((6, 9), text, fill=(230, 232, 240), font=font)
    return img


def main():
    args = sys.argv[1:]
    src, out = args[0], args[1]
    cols = 2
    tpx = 220
    views = ["front", "side", "top", "iso"]
    if "--cols" in args:
        cols = int(args[args.index("--cols") + 1])
    if "--tile" in args:
        tpx = int(args[args.index("--tile") + 1])
    if "--views" in args:
        views = args[args.index("--views") + 1].split(",")
    with open(src) as f:
        bps = json.load(f)
    tiles = [tile(bp, tpx, views) for bp in bps]
    tw, th = tiles[0].size
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (tw * cols, th * rows), (20, 21, 26))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * tw, (i // cols) * th))
    sheet.save(out)
    print(f"wrote {out} ({len(tiles)} blueprints)")


if __name__ == "__main__":
    main()
