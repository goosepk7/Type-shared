"""Summon set: the castle hero sculpt (hard surface, built directly: crisp edges, flat walls).

Modelled in model space on refs.json "sig:castle" (+Y up, -Z front, studs): the keep with a plinth, a corbelled
parapet with merlons, corner buttresses, a gatehouse frame and a central great tower; round towers with a battered
foot, corbel ring and crenellated wall walk; shingled spire roofs; a banded plank gate. Windows, flags, poles and
banners stay the builder's parts. Each piece is a "unit" sculpt in the frame of one lead primitive. Assigned in
Signatures/Machines.luau (S.castle).
"""
import numpy as np

import direct
from . import piece
from .refs import Group

W = "sig:castle"


def cube(dims, c, rot_y=0.0):
    """Hard-edged box (12 triangles) of full size dims centred at c, turned rot_y about +Y."""
    h = np.asarray(dims, float) / 2
    V, N, F = [], [], []
    for ax in range(3):
        u, v = [a for a in range(3) if a != ax]
        for sg in (-1, 1):
            b = len(V)
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = np.zeros(3)
                p[ax], p[u], p[v] = sg * h[ax], su * h[u], sv * h[v]
                n = np.zeros(3)
                n[ax] = sg
                V.append(p)
                N.append(n)
            q = [b, b + 1, b + 2, b + 3]
            if np.cross(V[q[1]] - V[q[0]], V[q[2]] - V[q[0]]) @ N[b] < 0:
                q = q[::-1]
            F += [[q[0], q[1], q[2]], [q[0], q[2], q[3]]]
    m = direct._finish(np.array(V), np.array(N), np.array(F))
    R = None
    if rot_y:
        cs, sn = np.cos(rot_y), np.sin(rot_y)
        R = np.array([[cs, 0, sn], [0, 1, 0], [-sn, 0, cs]])
    return direct.moved(m, offset=c, rot=R)


def local(G, m):
    """Model-space mesh -> the lead's local frame (studs)."""
    return direct.moved(direct.moved(m, offset=-G.pos), rot=G.R.T)


def _unit(pid, G, tris, note, mirror=False):
    def deco(fn):
        piece(pid, (1, 1, 1), tris=tris, kind="unit", note=note, mirror=mirror, lead=tuple(G.s))(lambda: local(G, fn()))
        return fn
    return deco


GK = Group(W, "Keep")
KX, KY, KZ = 3.555, 4.55, 2.84          # keep half width, height, half depth
TX, TZ, TR = 3.55, 2.84, 1.35           # tower centres and radius


@_unit("s_castle_keep", GK, 700, "Castle keep (lead Keep; members: the merlons): walls on a plinth, corbelled parapet with merlons between the towers, "
       "buttresses, gatehouse frame, a central great tower with its own battlements.")
def keep():
    m = [direct.rounded_box((2 * KX, KY, 2 * KZ), 0.05, 0), ]
    m[0] = direct.moved(m[0], offset=(0, KY / 2, 0))
    m.append(cube((2 * KX + 0.3, 0.75, 2 * KZ + 0.3), (0, 0.375, 0)))                        # plinth
    # parapet: a corbel course and a wall walk rim, then merlons between the towers
    m.append(cube((2 * KX + 0.36, 0.3, 2 * KZ + 0.36), (0, KY - 0.02, 0)))
    for sz in (-1, 1):
        m.append(cube((2 * KX - 2.2, 0.5, 0.36), (0, KY + 0.36, sz * (KZ + 0.02))))
        for x in (-1.5, -0.5, 0.5, 1.5):
            m.append(cube((0.56, 0.52, 0.4), (x * 1.02, KY + 0.84, sz * (KZ + 0.02))))
    for sx in (-1, 1):
        m.append(cube((0.36, 0.5, 2 * KZ - 2.2), (sx * (KX + 0.02), KY + 0.36, 0)))
        for z in (-1, 0, 1):
            m.append(cube((0.4, 0.52, 0.56), (sx * (KX + 0.02), KY + 0.84, z * 1.02)))
    # buttresses on the side and back walls
    for sx in (-1, 1):
        m.append(cube((0.3, 3.4, 0.7), (sx * (KX + 0.12), 1.7, 0)))
        m.append(cube((0.7, 3.4, 0.3), (sx * 1.2, 1.7, KZ + 0.12)))
        m.append(cube((0.42, 3.35, 0.36), (sx * 1.46, 1.675, -KZ - 0.14)))                  # gate pilasters
        m.append(cube((0.56, 0.3, 0.46), (sx * 1.46, 3.42, -KZ - 0.16)))
    # central great tower rising behind the wall walk
    gw, gd, gh = 3.5, 2.7, 2.0
    m.append(cube((gw, gh, gd), (0, KY + gh / 2 - 0.05, 0.25)))
    m.append(cube((gw + 0.3, 0.28, gd + 0.3), (0, KY + gh - 0.1, 0.25)))
    for sx in (-1, 0, 1):
        for sz in (-1, 1):
            m.append(cube((0.6, 0.5, 0.4), (sx * (gw / 2 - 0.2), KY + gh + 0.28, 0.25 + sz * (gd / 2 - 0.05))))
    for sx in (-1, 1):
        m.append(cube((0.4, 0.5, 0.6), (sx * (gw / 2 - 0.05), KY + gh + 0.28, 0.25)))
    return direct.merge(*m)


GT = Group(W, "Tower1", ["Tower1Ring"])


@_unit("s_castle_tower", GT, 700, "Castle round tower (lead Tower; member: its ring): battered foot, shaft, string course, corbel ring, wall walk "
       "with eight merlons.")
def tower():
    # authored about the tower axis (model Y), from the ground at y = 0 to the wall walk
    r, top = TR, 6.8
    prof = [
        (0.0, 0, -1, 0), (0.0, r + 0.26, -1, 0), (0.0, r + 0.26, 0, 1), (0.5, r + 0.26, 0, 1), (0.5, r + 0.26, 1, 1), (1.1, r, 1, 1),
        (1.1, r, 0, 1), (top - 0.75, r, 0, 1), (top - 0.75, r, -1, 1), (top - 0.3, r + 0.34, -1, 1), (top - 0.3, r + 0.34, 0, 1),
        (top + 0.55, r + 0.34, 0, 1), (top + 0.55, r + 0.34, 1, 0), (top + 0.55, r + 0.02, 1, 0), (top + 0.55, r + 0.02, 0, -1),
        (top + 0.3, r + 0.02, 0, -1), (top + 0.3, r + 0.02, 1, 0), (top + 0.3, 0, 1, 0),
    ]
    m = [direct.moved(direct.lathe(prof, 20, axis=1), offset=(TX, 0, -TZ))]
    for i in range(8):
        a = (i + 0.5) / 8 * 2 * np.pi
        rr = r + 0.18
        m.append(cube((0.5, 0.5, 0.33), (TX + np.sin(a) * rr, top + 0.8, -TZ + np.cos(a) * rr), rot_y=a))
    return direct.merge(*m)


GR = Group(W, "Tower1Roof")


@_unit("s_castle_roof", GR, 360, "Castle spire roof (lead: tower roof): flared eaves, three shingle courses, ball finial.")
def roof():
    y0, tip = 7.15, 10.3
    prof = [(y0, 0, -1, 0), (y0, 1.72, -1, 0)]
    steps = [(y0, 1.72), (y0 + 0.75, 1.2), (y0 + 1.6, 0.8), (y0 + 2.45, 0.42), (tip - 0.12, 0.07)]
    for i in range(len(steps) - 1):
        (ya, ra), (yb, rb) = steps[i], steps[i + 1]
        lip = 0.07 if i < len(steps) - 2 else 0.0
        nt, nr = (ra - rb), (yb - ya)
        prof += [(ya, ra, nt, nr), (yb, rb + lip, nt, nr)]
        if lip:
            prof += [(yb, rb + lip, -1, 0), (yb, rb, -1, 0)]
    prof += [(tip - 0.12, 0.07, 0, 1), (tip - 0.1, 0.16, -1, 1), (tip + 0.03, 0.2, 0, 1), (tip + 0.16, 0.14, 1, 1), (tip + 0.22, 0, 1, 0)]
    return direct.moved(direct.lathe(prof, 16, axis=1), offset=(TX, 0, -TZ))


GG = Group(W, "Gate")


@_unit("s_castle_gate", GG, 260, "Castle gate (lead Gate): six planks, three iron bands with studs, a ring handle boss on each leaf.")
def gate():
    c = GG.pos
    w, h, d = GG.s
    m = [cube((w, h, d * 0.6), (c[0], c[1], c[2] + d * 0.2))]
    pw = w / 6
    for i in range(6):
        x = c[0] + (i - 2.5) * pw
        m.append(cube((pw * 0.9, h * 0.985, d * 0.3), (x, c[1], c[2] - d * 0.2 - (0.012 if i % 2 else 0))))
    for y in (-0.33, 0.0, 0.33):
        m.append(cube((w * 0.99, h * 0.055, d * 0.14), (c[0], c[1] + y * h, c[2] - d * 0.4)))
        for i in range(6):
            m.append(cube((0.09, 0.09, 0.08), (c[0] + (i - 2.5) * pw, c[1] + y * h, c[2] - d * 0.47)))
    for sx in (-1, 1):
        m.append(cube((0.2, 0.26, 0.1), (c[0] + sx * pw * 0.55, c[1] - h * 0.14, c[2] - d * 0.45)))
    return direct.merge(*m)
