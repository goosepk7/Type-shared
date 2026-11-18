"""Ground / water birds: chicken, rooster, chick, turkey, peacock, pheasant, quail, duck, goose, swan, penguin,
emperor penguin, puffin, flamingo, heron, stork, crane bird, ostrich (mount), emu, cassowary, kiwi, dodo, terror bird.

One parametric sculpt (`_walker`): a tilted egg body (horizontal duck .. upright penguin) with a separate breast
panel, a 1-3 bone neck (S-curved for swans / herons), a head that tapers into its beak (lower mandible on a jaw
bone), folded wings built from a covert panel over stacked primaries (or penguin flippers / ostrich plumes),
legs with a feathered drumstick, optional bare tibia, scaled tarsus and toes (webbed for waterfowl), and a tail
chosen per bird: fan, rooster sickles, turkey display fan, peacock train with eye spots, duck curl, plume.
Head extras: comb, wattles, snood, casque, crest fans, crown. Motion: motion_birds.walk (head bob, waddle).
"""
import math

import numpy as np

from sdf import *  # noqa: F401,F403
from kit import Hero, hero, stripes, spots, gradient, combine
from h_birds import tail_half, U, A, oell, feather, unite, bounded, lerp, beak_shapes, beak_tip, scallop, band_mask, dist_shade, slab, BIRD, rot_y
import motion_birds as MB

BASE = dict(
    body=1.0, girth=1.0, upright=0.25, neck=0.6, neck_r=0.22, nneck=2, neck_lean=0.25, scurve=0.0, head=1.0,
    beak="short", beak_len=0.35, beak_depth=0.2, beak_w=0.16, beak_col="beak", eye=0.17, eye_col="dark",
    leg=1.0, leg_r=0.08, bare_tibia=0.0, toe=0.38, ntoe=4, webbed=False, foot_col="beak", drum=1.0,
    wing="folded", wing_len=1.0, plume=False,
    tail="fan", tail_len=0.8, tail_w=0.28, ntail=4, tail_spread=0.6, tail_lift=0.3,
    comb=0.0, wattle=0.0, snood=False, casque=False, crest=None, crown=False, knob=False, bald=False, cheek=None,
    fluffy=0.0, cols={}, pat=None, gait="bird", attack="peck", period=0.9, stride=0.42, headbob=0.12, waddle=0.0,
    fur_freq=9.0, mount=False, saddle=False, preview={}, tags=("bird",), fthick=0.06, chord=1.0, kick=False, run=False,
)

COLS = dict(back="primary", belly="secondary", head="primary", neck=None, wing="primary", flight="primary", tail="primary",
            leg="beak", crest="secondary", comb="red", tibia=None, cheek="secondary", train="secondary")


def _walker(hid, *presets, **kw):
    P = dict(BASE)
    for pr in presets:
        P.update(pr)
    P.update(kw)
    col = dict(COLS)
    col.update(P["cols"])
    if col["neck"] is None:
        col["neck"] = col["head"]
    if col["tibia"] is None:
        col["tibia"] = col["leg"]
    H = Hero(hid, plan="Bird", gait=P["gait"], tags=list(P["tags"]))
    H.preview = P["preview"]
    BL, G, HS = P["body"], P["girth"], P["head"]
    LL = P["leg"]
    a = P["upright"] * math.pi / 2
    u = A(0, math.sin(a), -math.cos(a))           # body long axis (towards the chest)
    ext = 0.9 * BL * math.sin(a) + 0.55 * G * math.cos(a)
    BY = LL + ext * 0.72
    H.body((0, BY, 0))
    fl = P["fluffy"]

    def fuzz(sd, amp=1.0, fr=10.0, seed=0):
        return sd.noise(fl * amp, fr, seed) if fl > 0 else sd

    fine = scallop(0.12 * G, depth=0.1)
    pat = fine
    if P["pat"] == "spots":
        pat = combine(fine, spots(0.13 * G, 0.04, depth=-1.6, seed=8))      # pale polka dots (guinea fowl)
    elif P["pat"] == "streaks":
        pat = combine(fine, stripes(lambda Q: Q[:, 0] * 3.0 + 0.4 * np.sin(Q[:, 1] * 11), 1.4, width=0.22, depth=0.3, wobble=0.05, seed=4))
    elif P["pat"] == "bars":
        pat = combine(fine, stripes(lambda Q: Q[:, 1] + 0.1 * np.abs(Q[:, 0]), 6.0, width=0.3, depth=0.3, seed=6))
    elif P["pat"] == "scales":
        pat = scallop(0.1 * G, depth=0.3, seed=5)

    # ------------------------------------------------------------------ body
    c0 = A(0, BY, 0)
    torso = oell(c0, u, (1, 0, 0), 0.9 * BL, 0.55 * G, 0.58 * G)
    torso = torso.su(oell(c0 - u * 0.55 * BL + A(0, 0.05, 0), u, (1, 0, 0), 0.5 * BL, 0.42 * G, 0.42 * G), 0.25)   # rump
    torso = torso.su(ellipsoid(0.3 * G, 0.2 * G, 0.45 * BL, tuple(c0 + u * 0.15 + A(0.3 * G, 0.28 * G, 0))).mirror_x(), 0.2)  # shoulders
    if P["upright"] > 0.5:
        torso = torso.su(oell(c0 - u * 0.3 * BL, u, (1, 0, 0), 0.6 * BL, 0.6 * G, 0.6 * G), 0.2)
    H.piece("Torso", "Body", fuzz(torso, 1.0, P["fur_freq"], 1), col=col["back"], tris=1600, res=112, pattern=combine(pat, gradient(1, BY - 0.5, BY + 0.6, 0.94, 1.0)))
    nrm = U(np.cross(u, A(1, 0, 0)))   # body "down/front" normal (belly side)
    if nrm[1] > 0:
        nrm = -nrm
    bo = 0.12 + 0.1 * P["upright"]
    br = oell(c0 + u * 0.1 * BL + nrm * bo * G, u, (1, 0, 0), 0.84 * BL, (0.5 + 0.03 * P["upright"]) * G, 0.5 * G)
    if P["upright"] > 0.5:   # pear-shaped low belly
        br = br.su(oell(c0 - u * 0.3 * BL + nrm * (bo + 0.04) * G, u, (1, 0, 0), 0.55 * BL, 0.56 * G, 0.5 * G), 0.15)
    H.piece("Breast", "Body", fuzz(br, 1.0, P["fur_freq"], 2), col=col["belly"], tris=800, res=104, pri=1.2, pattern=pat)

    # ------------------------------------------------------------------ neck chain + head
    hr = 0.3 * HS
    nb = c0 + u * 0.72 * BL + A(0, 0.25 * G, 0)
    NL = P["neck"]
    lean = P["neck_lean"]
    top = nb + A(0, NL * math.cos(lean), -NL * math.sin(lean))
    n = P["nneck"]
    pts = []
    for i in range(n + 1):
        t = i / n
        p = lerp(nb, top, t)
        p = p + A(0, 0, P["scurve"] * NL * math.sin(math.pi * t) * 0.45)          # S-curve bows back
        p = p + A(0, 0, -P["scurve"] * NL * math.sin(2 * math.pi * t) * 0.12)
        pts.append(p)
    hc = top + A(0, 0.2 * hr, -0.55 * hr)
    neck_bones = []
    parent = "Body"
    for i in range(n):
        nm = f"Neck{i + 1}"
        H.bone(nm, parent, tuple(pts[i]))
        neck_bones.append(nm)
        parent = nm
    H.bone("Head", parent, tuple(top))
    r0 = P["neck_r"] * G * 1.25
    r1 = 0.62 * hr
    for i in range(n):
        ra = r0 + (r1 - r0) * i / n
        rb = r0 + (r1 - r0) * (i + 1) / n
        a_ = pts[i] - (U(pts[i + 1] - pts[i]) * 0.12 if i == 0 else 0)
        b_ = pts[i + 1] if i < n - 1 else hc + A(0, -0.2 * hr, 0.25 * hr)
        seg = round_cone(tuple(a_), tuple(b_), ra * 1.05, rb * 1.02)
        if i == 0:
            seg = seg.su(sphere(r0 * 1.25, tuple(nb + A(0, -0.12, 0.1))), 0.1)
        H.piece(f"NeckP{i + 1}", neck_bones[i], fuzz(seg, 0.6, P["fur_freq"] * 1.2, 3 + i), col=col["neck"], tris=500, res=96, role="limb", pri=1.1, pattern=fine)

    if P.get("ring"):
        rp = lerp(pts[n - 1], pts[n], 0.15)
        rr_ = r0 + (r1 - r0) * (n - 0.85) / n
        H.piece("NeckRing", neck_bones[-1], torus(rr_ * 1.0, 0.05, axis=1).at(*rp), col=P["ring"], tris=300, res=72, role="detail", pri=1.5)

    def h(x, y, z):
        return tuple(hc + A(x * hr, y * hr, z * hr))

    head = ellipsoid(0.82 * hr, 0.82 * hr, 1.0 * hr, h(0, 0, 0.05))
    head = head.su(ellipsoid(0.7 * hr, 0.66 * hr, 0.85 * hr, h(0, -0.15, -0.3)), 0.25 * hr)
    head = head.su(round_cone(h(0, -0.05, -0.3), h(0, -0.08, -0.82), 0.6 * hr, min(0.5 * hr, 0.62 * P["beak_depth"] * HS + 0.12 * hr)), 0.2 * hr)
    ey = P["eye"]
    epos_w = hc + A(0.64, 0.18, -0.42) * hr
    head = head.ss(sphere(ey * hr * 1.08, tuple(epos_w)).mirror_x(), 0.05 * hr)
    H.piece("HeadP", "Head", fuzz(head, 0.4, 14, 7), col=col["head"], tris=1000, res=104, role="head", pri=1.3, pattern=fine if not P["bald"] else None)
    H.eyes("Head", tuple(epos_w), ey * hr, col=("iris" if P["eye_col"] == "iris" else "pupil"), pupil=("round" if P["eye_col"] == "iris" else None),
           look=(0.85, 0.12, -0.45))
    bk = P["beak"]
    BLn, BD, BW = P["beak_len"] * HS, P["beak_depth"] * HS, P["beak_w"] * HS
    b0 = hc + A(0, -0.06 * hr, -0.78 * hr)
    upb, lob = beak_shapes(bk, BLn, BD, BW)
    if bk == "duck":
        upb = round_box(0.5 * BW, 0.22 * BD, 0.5 * BLn, 0.18 * BD, (0, 0.0, -0.45 * BLn)).su(ellipsoid(0.5 * BW, 0.3 * BD, 0.25 * BLn, (0, 0.12 * BD, -0.05 * BLn)), 0.08)
        upb = upb.su(ellipsoid(0.22 * BW, 0.12 * BD, 0.1 * BLn, (0, 0.12 * BD, -0.9 * BLn)), 0.03)   # nail
        lob = round_box(0.46 * BW, 0.15 * BD, 0.46 * BLn, 0.12 * BD, (0, -0.28 * BD, -0.42 * BLn))
        upb, lob = upb.at(*b0), lob.at(*b0)
    elif bk == "puffin":
        upb = tube([(0, 0.1 * BD, 0.05), (0, 0.15 * BD, -0.45 * BLn), (0, -0.25 * BD, -1.0 * BLn)], [0.55 * BD, 0.4 * BD, 0.06 * BD], k=0.05).scale3(BW / BD, 1, 1)
        lob = tube([(0, -0.45 * BD, 0.0), (0, -0.55 * BD, -0.45 * BLn), (0, -0.35 * BD, -0.9 * BLn)], [0.45 * BD, 0.32 * BD, 0.06 * BD], k=0.05).scale3(BW / BD * 0.95, 1, 1)
        upb, lob = upb.at(*b0), lob.at(*b0)
    else:
        upb, lob = upb.at(*b0), lob.at(*b0)
    H.piece("Beak", "Head", upb, col=P["beak_col"], mat="hard", tris=500, res=96, role="beak", pri=1.6, pattern=P.get("beak_pat"))
    jw = b0 + A(0, -0.2 * BD, 0.15 * hr)
    H.bone("Jaw", "Head", tuple(jw))
    H.piece("LowerBeak", "Jaw", lob, col=P.get("lower_col", P["beak_col"]), mat="hard", tris=320, res=88, role="jaw", pri=1.6)
    H.prim("Mouth", "Jaw", "Ellipsoid", (BW * 0.7, BD * 0.12, BLn * 0.5), tuple(b0 + A(0, -0.24 * BD, -0.25 * BLn)), col="mouth", mat="hard", role="mouth", pri=2.4)

    crest_bones = []
    if P["comb"] > 0:
        cm = P["comb"]
        cb = hc + A(0, 0.75 * hr, -0.1 * hr)
        H.bone("Comb", "Head", tuple(cb))
        crest_bones.append("Comb")
        comb = ellipsoid(0.12 * hr, 0.35 * hr * cm, 0.75 * hr * cm, tuple(cb + A(0, 0.05 * hr, -0.05 * hr)))
        for i in range(5):
            z = (-0.55 + 0.27 * i) * hr * cm
            comb = comb.su(sphere(0.2 * hr * cm, tuple(cb + A(0, (0.45 - 0.05 * abs(i - 1.5)) * hr * cm, z))), 0.08 * hr)
        H.piece("CombP", "Comb", comb, col=col["comb"], tris=500, res=96, role="crest", pri=1.5)
    wattle_bone = None
    if P["wattle"] > 0:
        wt = P["wattle"]
        wb = b0 + A(0, -0.3 * BD, 0.08)
        H.bone("Wattle", "Head", tuple(wb))
        wattle_bone = "Wattle"
        wat = unite([ellipsoid(0.13 * hr, 0.42 * hr * wt, 0.18 * hr, tuple(wb + A(0.12 * hr, -0.35 * hr * wt, 0.0))),
                     ellipsoid(0.13 * hr, 0.42 * hr * wt, 0.18 * hr, tuple(wb + A(-0.12 * hr, -0.35 * hr * wt, 0.02)))], 0.04 * hr)
        if P["snood"]:
            wat = wat.su(tube([tuple(b0 + A(0, 0.45 * BD, 0.02)), tuple(b0 + A(0.0, 0.5 * BD, -0.35 * BLn)), tuple(b0 + A(0.04, -0.6 * BD, -0.8 * BLn - 0.1))],
                              [0.08 * hr, 0.09 * hr, 0.07 * hr], k=0.03), 0.02)
        H.piece("WattleP", "Wattle", wat, col=col["comb"], tris=450, res=96, role="detail", pri=1.5)
    if P["casque"]:
        cq = round_cone(h(0, 0.45, -0.45), h(0, 1.9, 0.35), 0.5 * hr, 0.22 * hr)
        cq = cq.su(ellipsoid(0.32 * hr, 0.7 * hr, 0.9 * hr, h(0, 1.1, -0.1)), 0.15 * hr)
        cq = cq & plane((1, 0, 0), 0.3 * hr) & plane((-1, 0, 0), 0.3 * hr)
        H.piece("Casque", "Head", cq.round(0.0), col="horn", mat="hard", tris=450, res=88, role="horn", pri=1.6)
    if P["knob"]:
        H.piece("Knob", "Head", sphere(0.3 * hr, tuple(b0 + A(0, 0.38 * BD, 0.02))), col="darker", tris=200, res=64, role="beak", pri=1.7)
    if P["crest"]:
        ck = P["crest"]
        cb = hc + A(0, 0.7 * hr, 0.1 * hr)
        H.bone("Crest", "Head", tuple(cb))
        crest_bones.append("Crest")
        fs = []
        if ck == "fan":   # peacock / crowned crane: thin shafts with tips
            nfc = 7 if P.get("crown_big") else 5
            for i in range(nfc):
                ang = math.radians(-35 + 70 * i / (nfc - 1))
                L = (1.05 if P.get("crown_big") else 0.95) * hr
                tip = cb + A(math.sin(ang) * 0.45 * L, math.cos(ang) * L, 0.15 * L)
                fs.append(round_cone(tuple(cb), tuple(tip), 0.035 * hr, 0.025 * hr))
                fs.append(ellipsoid(0.1 * hr if not P.get("crown_big") else 0.16 * hr, 0.13 * hr if not P.get("crown_big") else 0.2 * hr, 0.06 * hr, tuple(tip)))
            cr = unite(fs)
        elif ck == "plume":   # quail topknot: one drooping teardrop
            cr = tube([tuple(cb + A(0, 0, 0.0)), tuple(cb + A(0, 0.55 * hr, -0.25 * hr)), tuple(cb + A(0, 0.75 * hr, -0.6 * hr))], [0.08 * hr, 0.1 * hr, 0.16 * hr], k=0.04)
        else:                 # "punk": spiky tuft swept back
            for i in range(5):
                ang = math.radians(-30 + 15 * i)
                tip = cb + A(0.15 * hr * math.sin(ang * 2), 0.65 * hr + 0.1 * hr * (i % 2), 0.55 * hr + 0.2 * hr * math.cos(ang))
                fs.append(round_cone(tuple(cb + A(0, -0.1 * hr, -0.25 * hr + 0.1 * i * hr)), tuple(tip), 0.14 * hr, 0.03 * hr))
            cr = unite(fs, 0.03 * hr)
        H.piece("CrestP", "Crest", cr, col=col["crest"], tris=500, res=96, role="crest", pri=1.4)
    if P["crown"]:   # red crown cap (crane) / white face (coot)
        cp = head.round(0.035 * hr) & ellipsoid(0.62 * hr, 0.45 * hr, 0.6 * hr, h(0, 0.72, -0.25))
        H.piece("Crown", "Head", cp, col=P["crown"] if isinstance(P["crown"], str) else "red", tris=350, res=96, role="crest", pri=1.5)
    if P["cheek"]:   # cheek patch (king penguin, chickadee, gentoo stripe)
        cpos = {"low": (0.55, -0.3, 0.05), "eye": (0.6, 0.35, -0.1), "nape": (0.45, -0.05, 0.6)}[P["cheek"]]
        ck = head.round(0.03 * hr) & ellipsoid(0.42 * hr, 0.36 * hr, 0.45 * hr, h(*cpos)).mirror_x()
        ck = ck.ss(sphere(ey * hr * 1.35, tuple(epos_w)).mirror_x(), 0.02 * hr)
        H.piece("Cheek", "Head", ck, col=col["cheek"], tris=350, res=96, role="detail", pri=1.5)

    # ------------------------------------------------------------------ wings
    wl = P["wing_len"]
    sh = c0 + u * 0.4 * BL + A(0.48 * G, 0.22 * G, 0)
    H.mbone("Wing#", "Body", tuple(sh))
    side_out = A(1, 0, 0)
    if P["wing"] == "flipper":
        tip = sh + A(0.12 * G, -1.15 * BL * wl, 0.18)
        fp = oell(lerp(sh, tip, 0.5) + A(0.05, 0, 0), tip - sh, A(0, 0, 1), np.linalg.norm(tip - sh) * 0.56, 0.2 * G, 0.06)
        fp = fp.su(sphere(0.17 * G, tuple(sh + A(-0.02, -0.05, 0))), 0.1)
        H.mpiece("Flipper#", "Wing#", fp, col=col["wing"], tris=500, res=96, role="wing", pri=1.1)
    elif P["wing"] == "plume":   # ratites: short shaggy wing plumes
        fs = []
        for i in range(7):
            b = sh + A(0.04, -0.04 * i, 0.1 * i)
            d = U(A(0.2, -0.75 + 0.08 * i, 0.75))
            fs.append(feather(b, d, (0.7 + 0.04 * i) * wl * BL, 0.28, 0.06, A(0, 0.3, 1), roll=0.25, droop=0.2))
        H.mpiece("WingPlume#", "Wing#", unite(fs).noise(0.012, 30, 3), col=col["wing"], tris=700, res=104, role="wing", pri=1.1)
    elif P["wing"] == "folded":
        # layered folded wing on the flank: marginal / lesser / median / greater covert rows (shingled, front rows
        # on top), then the secondaries and the long primaries reaching back over the rump
        back_dir = U(-u * 1.0 + A(0, -0.1, 0))
        wl_ = 1.15 * BL * wl
        fc = [oell(sh + back_dir * 0.08 * wl_ + A(0.06 * G, -0.02, 0), back_dir, A(0, 1, 0.0), 0.2 * wl_, 0.2 * G, 0.1 * G)]
        rows = 3
        for r in range(rows):
            nn = 4
            for i in range(nn):
                t = i / (nn - 1)
                b = sh + back_dir * (0.04 + 0.1 * r + 0.24 * t) * wl_ + A(0.13 * G - 0.03 * r, (0.02 - 0.15 * r - 0.07 * t) * G, 0)
                ln = (0.22 + 0.07 * r) * wl_
                fc.append(feather(b, U(back_dir + A(0, -0.35 + 0.08 * r, 0)), ln, (0.2 + 0.03 * r) * G, 0.06, A(0, 1, 0), roll=0.25, over=0.25))
        H.mpiece("WingCov#", "Wing#", unite(fc), col=col["wing"], tris=900, res=120, role="wing", pri=1.15, pattern=fine)
        fp = []
        for i in range(5):   # secondaries: below the greater coverts
            t = i / 4
            b = sh + back_dir * (0.18 + 0.2 * t) * wl_ + A(0.05 * G, (-0.32 - 0.05 * t) * G, 0)
            fp.append(feather(b, U(back_dir + A(0, -0.12, 0)), 0.45 * wl_, 0.24 * G, 0.06, A(0, 1, 0), roll=0.2, over=0.1))
        for i in range(5):   # primaries: long, stacked, tips staggered
            t = i / 4
            b = sh + back_dir * (0.3 + 0.08 * t) * wl_ + A(0.07 * G - 0.012 * i, (-0.2 - 0.04 * t) * G, 0)
            fp.append(feather(b, U(back_dir + A(0, 0.03 - 0.05 * t, 0)), (0.62 + 0.07 * t) * wl_, 0.2 * G, 0.06, A(0, 1, 0), roll=0.18, over=0.1))
        H.mpiece("WingPrim#", "Wing#", unite(fp), col=col["flight"], tris=900, res=120, role="wing", pri=1.05,
                 pattern=dist_shade(sh, 0.4 * wl_, 1.0 * wl_, 1.0, 1.0 - 0.35 * P.get("tipdark", 1.0)))

    # ------------------------------------------------------------------ tail
    tb = c0 - u * 0.95 * BL + A(0, 0.1 * G, 0)
    H.bone("Tail", "Body", tuple(tb))
    fans = []
    tk = P["tail"]
    tl = P["tail_len"]
    if tk in ("fan", "square", "wedge", "long", "stub"):
        H.mbone("TailFan#", "Tail", tuple(tb + A(0.03, 0, 0)))
        fans = [("TailFanR", 1), ("TailFanL", -1)]
        TP = dict(ntail=P["ntail"], tail_len=tl, tail_w=P["tail_w"], fthick=P["fthick"], chord=P["chord"], tail=tk if tk != "fan" else "fan", tail_spread=P["tail_spread"])
        half = tail_half((0, 0, 0), TP).rot(-math.degrees(P["tail_lift"]), 0, 0).at(*tb)
        H.mpiece("TailHalf#", "TailFan#", half, col=col["tail"], tris=600, res=112, role="tail", pri=1.2, pattern=P.get("tail_pat"))
    elif tk == "sickle":   # rooster: arching sickle feathers
        fs = []
        for i in range(7):
            sx = (i - 3) * 0.06
            L = tl * (0.7 + 0.35 * math.cos((i - 3) * 0.5))
            p0 = tb + A(sx, -0.05, -0.05)
            p1 = p0 + A(sx * 0.5, L * 0.75, L * 0.35)
            p2 = p0 + A(sx * 1.5, L * 0.85, L * 0.85)
            p3 = p0 + A(sx * 2.0, L * 0.35, L * 1.15)
            fs.append(tube([tuple(p0), tuple(p1), tuple(p2), tuple(p3)], [0.1, 0.09, 0.07, 0.02], k=0.03).scale3(1.0, 1.0, 1.0))
        tail = unite(fs)
        H.piece("Sickles", "Tail", tail, col=col["tail"], tris=1300, res=120, role="tail", pri=1.2)
    elif tk in ("display", "train"):   # turkey fan / peacock train, raised behind the body
        H.mbone("TailFan#", "Tail", tuple(tb + A(0.03, 0, 0)))
        fans = [("TailFanR", 1), ("TailFanL", -1)]
        nf = 7 if tk == "display" else 11
        R = tl
        fs = []
        eyes_ = []
        for i in range(nf):
            t = (i + 0.5) / nf
            ang = t * math.radians(92)                # from straight up to sideways (right half)
            d = U(A(math.sin(ang), math.cos(ang) * 0.95, 0.32))
            b = tb + A(0.02, 0.0, 0.05) + A(0, 0, 0.01 * i)
            if tk == "display":
                fs.append(feather(b, d, R * (1.0 - 0.06 * t), 0.36 * R / nf * 5.5, 0.06, A(0, 0, 1) if abs(d[1]) > 0.5 else A(0, 1, 0), roll=0.15, over=0.1))
            else:
                fs.append(round_cone(tuple(b), tuple(b + d * R * 0.98), 0.03, 0.02))
                fs.append(feather(b + d * R * 0.4, d, R * 0.64, 0.5 * R / nf * 4.0, 0.05, np.cross(d, A(0, 0, 1)), over=0.05))
                eyes_.append((b + d * R * 0.9, d, 1.0))
        if tk == "train":   # second staggered row of shorter plumes
            for i in range(nf - 1):
                t = (i + 1.0) / nf
                ang = t * math.radians(92)
                d = U(A(math.sin(ang), math.cos(ang) * 0.95, 0.25))
                b = tb + A(0.02, 0, 0.0)
                fs.append(feather(b + d * R * 0.25, d, R * 0.52, 0.45 * R / nf * 4.0, 0.05, np.cross(d, A(0, 0, 1)), over=0.05))
                eyes_.append((b + d * R * 0.72, d, 0.8))
        fan_sd = unite(fs)
        if tk == "train":
            # eye spots as real geometry: a bronze ring disc and a dark blue core standing proud of each plume
            rings, cores = [], []
            for e, d, sc in eyes_:
                v = U(np.cross(d, A(0, 0, 1)))
                nn = np.cross(d, v)
                if nn[2] > 0:
                    nn = -nn
                rr = 0.075 * R * sc
                rings.append(oell(e + nn * 0.04, d, v, rr * 1.25, rr, 0.018))
                cores.append(oell(e + nn * 0.06, d, v, rr * 0.7, rr * 0.55, 0.018))
            H.mpiece("EyeRing#", "TailFan#", unite(rings), col="gold", tris=900, res=150, role="tail", pri=1.3)
            H.mpiece("EyeCore#", "TailFan#", unite(cores), col="primary", tris=700, res=150, role="tail", pri=1.4)
            tpat = combine(dist_shade(tb, 0.2 * R, R, 0.8, 1.0))
        else:
            tpat = combine(band_mask(tb, (0, 1, 0.2), 3.2 / R, width=0.18, depth=0.45), dist_shade(tb, 0.75 * R, R, 1.0, 0.75))
        H.mpiece("Fan#", "TailFan#", fan_sd, col=col["train"] if tk == "train" else col["tail"], tris=1600 if tk == "train" else 1100,
                 res=144, role="tail", pri=1.1, pattern=tpat)
    elif tk == "curl":   # drake curl / short pointed duck tail
        tail = round_cone(tuple(tb + A(0, -0.02, -0.15)), tuple(tb + A(0, 0.25 * tl, 0.5 * tl)), 0.22 * G, 0.04)
        tail = tail.scale3(1.0, 1.0, 1.0)
        H.piece("TailP", "Tail", tail, col=col["tail"], tris=350, res=88, role="tail", pri=1.2)
    elif tk == "plume":  # ostrich / crane: drooping fan of soft plumes
        fs = [ellipsoid(0.3 * G, 0.3 * G, 0.3, tuple(tb + A(0, 0.02, 0.0)))]
        for i in range(7):
            ang = math.radians(-60 + 20 * i)
            d = U(A(math.sin(ang) * 0.55, -0.55 - 0.15 * abs(math.sin(ang)), 0.85))
            fs.append(feather(tb + A(math.sin(ang) * 0.12 * G, 0.05, -0.05), d, (0.85 + 0.15 * math.cos(ang)) * tl, 0.3 * G, 0.07,
                              A(math.cos(ang), 0.0, -math.sin(ang) * 0.3), roll=0.2, droop=0.15))
        H.piece("TailP", "Tail", unite(fs).noise(0.012, 30, 4), col=col["tail"], tris=900, res=112, role="tail", pri=1.2)

    # ------------------------------------------------------------------ legs
    hip = A(0.27 * G, BY - 0.22 * G - 0.15 * math.sin(a), 0.05 * BL)
    ank = A(0.29 * G, LL * 0.48, hip[2] + 0.18 * LL ** 0.5)
    ft = A(0.29 * G, 0.06, hip[2] - 0.02)
    H.mbone("Hip#", "Body", tuple(hip))
    H.mbone("Ankle#", "Hip#", tuple(ank))
    H.mbone("Foot#", "Ankle#", tuple(ft))
    lr = P["leg_r"]
    dl = P["drum"]
    knee_y = lerp(hip, ank, 0.55 * dl if P["bare_tibia"] else 0.85)
    drum = oell(lerp(hip, knee_y, 0.4), hip - knee_y, A(1, 0, 0), np.linalg.norm(hip - knee_y) * 0.55 * dl + 0.05, 0.19 * G * dl, 0.21 * G * dl)
    H.mpiece("Drum#", "Hip#", fuzz(drum, 0.8, P["fur_freq"] * 1.2, 9), col=col.get("thigh", col["belly"]), tris=450, res=88, role="limb", pri=1.2, pattern=pat)
    if P["bare_tibia"]:
        tib = round_cone(tuple(knee_y + A(0, 0.08, 0)), tuple(ank), lr * 1.2, lr * 1.05)
        H.mpiece("Tibia#", "Hip#", tib, col=col["tibia"], tris=300, res=80, role="limb", pri=1.3)
    shk = round_cone(tuple(ank), tuple(ft + A(0, 0.03, 0.02)), lr * 1.08, lr * 0.9).su(sphere(lr * 1.25, tuple(ank)), 0.03)
    H.mpiece("Shank#", "Ankle#", shk, col=col["leg"], tris=320, res=80, role="limb", pri=1.3, pattern=scallop(lr * 0.9, depth=0.18, seed=7))
    T = P["toe"]
    tr_ = lr * 0.65
    toes = [sphere(lr * 1.1, tuple(ft))]
    if P["ntoe"] == 2:
        dirs = [(-0.12, -1), (0.38, -1)]
    elif P["ntoe"] == 3:
        dirs = [(-0.5, -1), (0.0, -1), (0.5, -1)]
    else:
        dirs = [(-0.5, -1), (0.0, -1), (0.5, -1), (0.0, 1.0)]
    tips = []
    for dx, dz in dirs:
        d = U(A(dx, 0, dz))
        ln = T * (0.45 if dz > 0 else (1.0 if dx != 0 or P["ntoe"] == 2 else 1.12)) * (1.25 if P["ntoe"] == 2 and dx > 0 else 1.0)
        tip = ft + d * ln + A(0, -0.03, 0)
        toes.append(tube([tuple(ft), tuple(ft + d * ln * 0.5), tuple(tip)], [tr_, tr_ * 0.95, tr_ * 0.7], k=0.02))
        tips.append(tip)
        toes.append(round_cone(tuple(tip), tuple(tip + d * 0.09 * T / 0.38 + A(0, -0.03, 0)), tr_ * 0.6, tr_ * 0.2))   # nail
    if P["webbed"]:
        web = slab([tuple(ft + A(0, -0.01, 0)), tuple(tips[0] + A(0, 0.0, 0)), tuple((tips[0] + tips[1]) / 2 + A(0, 0, 0.06)), tuple(tips[1]),
                    tuple((tips[1] + tips[2]) / 2 + A(0, 0, 0.06)), tuple(tips[2])], 0.04)
        toes.append(web)
    H.mpiece("Toes#", "Foot#", unite(toes, 0.025), col=col["leg"] if P["foot_col"] == "beak" and col["leg"] != "beak" else (col["leg"]), tris=500, res=96, role="foot", pri=1.4)

    # ------------------------------------------------------------------ mount
    height = BY + 0.9 * G + NL
    if P["mount"]:
        seat = A(0, BY + 0.5 * G, 0.05)
        H.socket("seat", tuple(seat), "Body")
        H.mount = {"seat": "Torso", "saddle": {"pos": tuple(seat), "size": (0.9 * G, 0.16, 0.9 * BL)}}
        if P["saddle"]:
            sb = c0 + A(0, 0.0, 0.05)
            blanket = (torso.round(0.06).shell(0.025) & round_box(0.75 * G, 0.5, 0.45 * BL, 0.08, tuple(seat + A(0, -0.22, 0))))
            H.piece("Blanket", "Body", blanket, col=P.get("blanket_col", "secondary"), mat="cloth", tris=600, res=104, role="cape", pri=1.6)
            sd = round_box(0.32 * G, 0.1, 0.36 * BL, 0.08, tuple(seat + A(0, 0.04, 0)))
            sd = sd.su(round_box(0.22 * G, 0.12, 0.06, 0.05, tuple(seat + A(0, 0.14, -0.3 * BL))), 0.05)       # pommel
            sd = sd.su(round_box(0.3 * G, 0.14, 0.06, 0.05, tuple(seat + A(0, 0.16, 0.32 * BL))), 0.05)       # cantle
            H.piece("Saddle", "Body", sd, col="leather", mat="cloth", tris=600, res=96, role="cape", pri=1.7)
            H.piece("Bridle", "Head", torus(0.62 * hr, 0.05 * hr, axis=2).at(*h(0, -0.05, -0.55)) |
                    torus(0.78 * hr, 0.05 * hr, axis=1).rot(70, 0, 0).at(*h(0, 0.05, 0.05)), col="leather", mat="cloth", tris=400, res=96, role="detail", pri=1.8)
            reins = unite([round_cone(h(sx * 0.6, -0.15, -0.55), tuple(lerp(np.array(h(sx * 0.6, -0.15, -0.55)), seat + A(sx * 0.2, 0.1, -0.35 * BL), 0.5) + A(0, -0.25, 0)), 0.025, 0.025)
                           for sx in (1, -1)])
            H.piece("Reins", "Head", reins, col="leather", mat="cloth", tris=300, res=96, role="detail", pri=1.8)

    # ------------------------------------------------------------------ rig, sockets, motion
    H.socket("mouth", tuple(b0 + beak_tip(bk, BLn, BD)), "Jaw")
    H.socket("head", h(0, 1.0, 0), "Head")
    H.rig.update({"head": "Head", "jaw": "Jaw", "tail": ["Tail"], "neck": neck_bones[0]})
    legs = [("HipR", "AnkleR", "FootR", 0.0), ("HipL", "AnkleL", "FootL", 0.5)]
    wings = [("WingR", 1), ("WingL", -1)]
    MB.walk(H, legs, wings=wings, neck=neck_bones, head="Head", jaw="Jaw", tail="Tail", fans=fans, height=height, period=P["period"],
            stride=P["stride"], headbob=P["headbob"], waddle=P["waddle"], attack=P["attack"], crest=crest_bones, wattle=wattle_bone,
            kick_leg=("HipR", "AnkleR", "FootR") if P["kick"] else None, run=P["run"],
            lean=0.0)
    return H



# ====================================================================================================== heroes
FOWL = dict(upright=0.3, neck=0.42, neck_r=0.24, nneck=2, neck_lean=0.15, head=0.95, beak="short", beak_len=0.3, beak_depth=0.22,
            beak_w=0.18, leg=0.85, leg_r=0.075, toe=0.4, eye=0.18, eye_col="iris", period=0.75, headbob=0.14, stride=0.4)


@hero("chicken", "birds")
def chicken():
    return _walker("chicken", FOWL, comb=1.3, wattle=0.9, tail="fan", tail_len=0.75, tail_w=0.3, tail_lift=0.9, ntail=4,
                   cols=dict(belly="primary", comb="secondary", leg="beak"), wing_len=0.85,
                   preview={"primary": "#F2EEE6", "secondary": "#D8261E", "beak": "#E8A83A", "iris": "#E8902A"})


@hero("rooster", "birds")
def rooster():
    return _walker("rooster", FOWL, upright=0.38, comb=1.45, wattle=1.1, tail="sickle", tail_len=1.5, neck=0.5, leg=0.95,
                   cols=dict(belly="secondary", tail="secondary", wing="primary", flight="secondary", comb="red", neck=[0.85, 0.55, 0.2], leg="beak"),
                   attack="kick", kick=True, preview={"primary": "#B8401E", "secondary": "#1E3A2A", "beak": "#E8B83A", "iris": "#E8902A"})


@hero("chick", "birds")
def chick():
    return _walker("chick", upright=0.35, body=0.62, girth=1.0, neck=0.12, neck_r=0.3, nneck=1, head=1.35, beak="short", beak_len=0.2,
                   beak_depth=0.17, beak_w=0.16, leg=0.42, leg_r=0.06, toe=0.28, eye=0.2, wing_len=0.55, tail="stub", tail_len=0.25,
                   tail_w=0.2, ntail=3, fluffy=0.025, period=0.45, headbob=0.08, stride=0.5,
                   cols=dict(belly="primary", leg="secondary"), beak_col="secondary",
                   preview={"primary": "#FFE04A", "secondary": "#F2A01E"})


@hero("turkey", "birds")
def turkey():
    return _walker("turkey", FOWL, body=1.15, girth=1.25, upright=0.3, neck=0.62, neck_r=0.17, head=0.85, bald=True, wattle=1.2, snood=True,
                   tail="display", tail_len=2.0, leg=1.0, beak_len=0.26, attack="display",
                   cols=dict(head=[0.55, 0.62, 0.8], neck=[0.75, 0.3, 0.3], comb="secondary", belly="primary", tail="primary", leg=[0.75, 0.55, 0.5]),
                   pat="scales", preview={"primary": "#5E4232", "secondary": "#C8301E", "beak": "#C8B898"})


@hero("peacock", "birds")
def peacock():
    return _walker("peacock", FOWL, body=1.0, girth=0.95, upright=0.25, neck=0.75, neck_r=0.15, head=0.75, crest="fan", tail="train",
                   tail_len=2.9, leg=1.05, leg_r=0.065, beak_len=0.3, attack="display", cheek="eye",
                   cols=dict(belly="primary", head="primary", wing=[0.75, 0.65, 0.5], flight=[0.55, 0.35, 0.2], crest="primary", leg=[0.55, 0.5, 0.48],
                             cheek="white", train="secondary"),
                   beak_col="horn", preview={"primary": "#1E5EA0", "secondary": "#2E8E5A", "horn": "#C8B8A0"})


@hero("pheasant", "birds")
def pheasant():
    return _walker("pheasant", FOWL, body=1.0, girth=0.95, upright=0.2, neck=0.45, head=0.85, tail="long", tail_len=2.6, tail_w=0.18,
                   ntail=3, tail_spread=0.15, tail_lift=0.2, wattle=0.45, cheek="eye",
                   cols=dict(head="secondary", neck="secondary", belly="primary", cheek="red", comb="red", leg=[0.55, 0.5, 0.45]),
                   pat="scales", tail_pat=band_mask((0, 0, 1), (0, 0, 1), 4.0, width=0.15, depth=0.5), beak_col="horn",
                   preview={"primary": "#B8541E", "secondary": "#1E5A3A", "horn": "#D8C8A8"})


@hero("quail", "birds")
def quail():
    return _walker("quail", upright=0.2, body=0.8, girth=1.05, neck=0.2, neck_r=0.28, nneck=1, head=1.0, beak="short", beak_len=0.22,
                   beak_depth=0.17, beak_w=0.14, leg=0.5, leg_r=0.05, toe=0.3, eye=0.17, crest="plume", tail="stub", tail_len=0.35, ntail=3,
                   period=0.4, headbob=0.06, pat="spots", wing_len=0.85, cheek="low",
                   cols=dict(belly="secondary", crest="darker", cheek="white", leg=[0.6, 0.5, 0.45]), beak_col="darker",
                   preview={"primary": "#8A6A4A", "secondary": "#D8C4A8", "darker": "#2A2420"})


DUCK = dict(upright=0.05, body=1.0, girth=1.0, neck=0.45, neck_r=0.2, nneck=2, neck_lean=0.05, head=1.0, beak="duck", beak_len=0.55,
            beak_depth=0.2, beak_w=0.36, leg=0.42, leg_r=0.06, toe=0.4, webbed=True, eye=0.15, eye_col="dark", tail="curl", tail_len=0.5,
            gait="waddle", waddle=0.14, period=0.7, headbob=0.04, stride=0.45, wing_len=0.95, drum=0.6)


@hero("duck", "birds")
def duck():
    return _walker("duck", DUCK, ring="white", drum=0.6,
                   cols=dict(head="primary", neck="primary", back=[0.55, 0.45, 0.38], belly=[0.82, 0.8, 0.78], wing=[0.55, 0.48, 0.42],
                             flight=[0.35, 0.32, 0.3], tail="dark", cheek="white", leg="beak"), beak_col="gold",
                   preview={"primary": "#3A7A3A", "secondary": "#A0702E", "gold": "#E8C83A", "beak": "#F2902A", "dark": "#2A2A2A"})


@hero("duckling", "birds")
def duckling():
    return _walker("duckling", DUCK, body=0.68, girth=1.0, neck=0.22, neck_r=0.28, nneck=1, head=1.4, beak_len=0.35, beak_w=0.3, eye=0.2,
                   tail="stub", tail_len=0.2, ntail=3, tail_w=0.18, fluffy=0.02, wing_len=0.5, period=0.45,
                   cols=dict(belly="primary", leg="secondary"), beak_col="secondary",
                   preview={"primary": "#FFE268", "secondary": "#F2A030"})


@hero("goose", "birds")
def goose():
    return _walker("goose", DUCK, body=1.2, girth=1.1, upright=0.15, neck=0.95, neck_r=0.17, nneck=3, neck_lean=0.15, head=0.95,
                   beak_len=0.5, beak_depth=0.26, beak_w=0.26, leg=0.55, attack="lunge", knob=False, tail="fan", tail_len=0.45, tail_w=0.26,
                   tail_lift=0.3, cols=dict(belly="primary", head="primary", leg="secondary", flight=[0.75, 0.75, 0.75]), beak_col="secondary",
                   preview={"primary": "#E8E4DC", "secondary": "#F28A1E"})


@hero("canada goose", "birds")
def canada_goose():
    return _walker("canada goose", DUCK, body=1.2, girth=1.1, upright=0.15, neck=1.0, neck_r=0.16, nneck=3, neck_lean=0.12, head=0.95,
                   beak_len=0.48, beak_depth=0.24, beak_w=0.24, leg=0.55, attack="lunge", tail="fan", tail_len=0.45, tail_w=0.26,
                   cheek="low", cols=dict(head="darker", neck="darker", back=[0.45, 0.38, 0.3], belly=[0.82, 0.78, 0.72], wing=[0.45, 0.38, 0.3],
                                         flight=[0.3, 0.26, 0.22], tail="darker", cheek="secondary", leg="darker"),
                   beak_col="darker", preview={"primary": "#3A2A20", "secondary": "#F2F2F0", "darker": "#1E1E1E"})


@hero("swan", "birds")
def swan():
    return _walker("swan", DUCK, body=1.3, girth=1.12, upright=0.02, neck=1.45, neck_r=0.14, nneck=3, neck_lean=-0.05, scurve=0.55,
                   head=0.85, beak_len=0.5, beak_depth=0.2, beak_w=0.24, leg=0.45, knob=True, attack="lunge", wing_len=1.1,
                   tail="fan", tail_len=0.45, tail_w=0.28, tail_lift=0.5, period=0.9,
                   cols=dict(belly="primary", leg="darker", flight="primary"), beak_col="secondary", tipdark=0.0,
                   preview={"primary": "#F7F7F4", "secondary": "#F2701E", "darker": "#2A2A2A"})


PENG = dict(upright=0.92, body=1.15, girth=1.05, neck=0.2, neck_r=0.3, nneck=1, neck_lean=0.0, head=1.3, beak="dagger",
            beak_len=0.48, beak_depth=0.17, beak_w=0.13, leg=0.2, leg_r=0.09, toe=0.34, webbed=True, eye=0.13, eye_col="dark",
            wing="flipper", wing_len=0.75, tail="stub", tail_len=0.3, tail_w=0.18, ntail=3, tail_lift=-0.6, gait="waddle", waddle=0.2,
            period=0.6, headbob=0.0, stride=0.3, drum=0.5)


@hero("penguin", "birds")
def penguin():
    return _walker("penguin", PENG, cols=dict(belly="secondary", head="primary", leg="darker", wing="primary"), beak_col="darker",
                   preview={"primary": "#1E1E24", "secondary": "#F7F7F2", "darker": "#2A2A30"})


@hero("emperor penguin", "birds")
def emperor_penguin():
    return _walker("emperor penguin", PENG, body=1.4, girth=1.15, head=0.95, beak="decurve", beak_len=0.55, beak_depth=0.15, cheek="low",
                   cols=dict(belly=[0.97, 0.95, 0.88], head="primary", leg="darker", wing="primary", cheek="secondary"), beak_col="darker",
                   lower_col="secondary", preview={"primary": "#1E1E24", "secondary": "#F2B02A", "darker": "#2A2A30"})


@hero("rockhopper penguin", "birds")
def rockhopper():
    return _walker("rockhopper penguin", PENG, body=1.0, head=1.1, crest="punk", beak="crow", beak_len=0.32, beak_depth=0.22,
                   eye_col="iris", gait="hop", cols=dict(belly="white", head="primary", leg=[0.9, 0.6, 0.6], wing="primary", crest="secondary"),
                   beak_col="red", preview={"primary": "#1E1E24", "secondary": "#F2D82A", "white": "#F7F7F2", "red": "#D8401E", "iris": "#C8201E"})


@hero("puffin", "birds")
def puffin():
    return _walker("puffin", PENG, upright=0.6, body=0.9, head=1.25, beak="puffin", beak_len=0.42, beak_depth=0.38, beak_w=0.16,
                   wing="folded", wing_len=0.75, leg=0.3, cheek="eye",
                   beak_pat=band_mask((0, 0, 0), (0, 0, 1), 9.0, width=0.18, depth=0.4),
                   cols=dict(belly="white", head="primary", cheek="white", leg="secondary", flight="primary"), beak_col="secondary",
                   preview={"primary": "#1E1E1E", "secondary": "#F2701E", "white": "#F2F2EE"})


WADER = dict(upright=0.2, body=1.0, girth=0.9, neck=1.25, neck_r=0.13, nneck=3, neck_lean=0.25, scurve=0.45, head=0.85,
             beak="dagger", beak_len=1.0, beak_depth=0.2, beak_w=0.14, leg=2.6, leg_r=0.06, bare_tibia=1.0, drum=0.55, toe=0.5,
             eye=0.14, eye_col="iris", period=1.2, stride=0.32, headbob=0.06, tail="fan", tail_len=0.5, tail_w=0.26, tail_lift=0.35)


@hero("flamingo", "birds")
def flamingo():
    return _walker("flamingo", WADER, leg=2.9, neck=1.6, scurve=0.75, beak="decurve", beak_len=0.62, beak_depth=0.3, beak_w=0.2,
                   webbed=True, cols=dict(belly="primary", leg=[0.92, 0.55, 0.62], flight="secondary"), beak_col="cream",
                   lower_col="secondary",
                   tipdark=0.0, preview={"primary": "#F28AA0", "secondary": "#1E1E1E", "cream": "#F2E2D2"})


@hero("heron", "birds")
def heron():
    return _walker("heron", WADER, crest="plume", cols=dict(belly="secondary", head="secondary", neck="secondary", leg=[0.65, 0.6, 0.45], crest="darker"),
                   beak_col="gold", attack="lunge", preview={"primary": "#6A7A8E", "secondary": "#F2F2F0", "gold": "#D8B040", "darker": "#1E1E22"})


@hero("stork", "birds")
def stork():
    return _walker("stork", WADER, neck=1.05, scurve=0.15, beak_len=1.05, beak_depth=0.26, beak_w=0.17, leg=2.4, leg_r=0.07,
                   cols=dict(belly="primary", head="primary", leg="secondary", flight="darker", wing="primary"), beak_col="secondary",
                   preview={"primary": "#F7F7F2", "secondary": "#D8201E", "darker": "#1E1E1E"})


@hero("crane bird", "birds")
def crane():
    return _walker("crane bird", WADER, neck=1.4, scurve=0.2, beak_len=0.75, leg=2.7, crown=True, plume=True, tail="plume",
                   tail_len=0.7, cols=dict(belly="primary", head="primary", leg="darker", flight="darker", neck=[0.25, 0.25, 0.27], tail="darker"),
                   beak_col="horn", attack="kick", kick=True,
                   preview={"primary": "#E8E8EC", "secondary": "#D8201E", "darker": "#2A2A2E", "horn": "#C8B890", "red": "#D8201E"})


RATITE = dict(upright=0.12, body=1.4, girth=1.3, neck=2.2, neck_r=0.16, nneck=3, neck_lean=0.18, scurve=0.18, head=0.9, beak="short",
              beak_len=0.5, beak_depth=0.22, beak_w=0.28, leg=3.0, leg_r=0.15, bare_tibia=1.0, drum=1.25, toe=0.65, ntoe=2,
              eye=0.2, eye_col="dark", wing="plume", wing_len=1.0, tail="plume", tail_len=0.9, period=0.75, stride=0.5,
              headbob=0.04, attack="kick", kick=True, run=True, fluffy=0.0, mount=True, fur_freq=26.0)


@hero("ostrich", "birds")
def ostrich():
    return _walker("ostrich", RATITE, saddle=True, blanket_col=[0.62, 0.16, 0.14],
                   cols=dict(belly="primary", neck=[0.85, 0.72, 0.68], head=[0.82, 0.7, 0.65], tibia=[0.85, 0.7, 0.65], leg=[0.78, 0.66, 0.62],
                             wing="secondary", tail="secondary", thigh=[0.85, 0.7, 0.65]), beak_col="horn",
                   preview={"primary": "#2A2420", "secondary": "#F2F2F0", "horn": "#D8C0A8", "leather": "#6B4423"})


@hero("emu", "birds")
def emu():
    return _walker("emu", RATITE, body=1.3, girth=1.25, neck=1.6, leg=2.5, ntoe=3, fluffy=0.022, wing="none", head=0.85, tail="none",
                   cols=dict(belly="primary", neck="secondary", head=[0.25, 0.3, 0.38], tibia=[0.45, 0.42, 0.4], leg=[0.4, 0.38, 0.36],
                             tail="primary"), beak_col="darker",
                   preview={"primary": "#6A5A4A", "secondary": "#3AA0D8", "darker": "#2A2A2A"})


@hero("cassowary", "birds")
def cassowary():
    return _walker("cassowary", RATITE, body=1.35, girth=1.3, neck=1.35, leg=2.4, leg_r=0.15, ntoe=3, fluffy=0.022, wing="none", tail="none",
                   casque=True, wattle=1.0, head=0.95,
                   cols=dict(belly="primary", neck="secondary", head="secondary", comb="red", tibia=[0.3, 0.3, 0.32], leg=[0.3, 0.3, 0.32], tail="primary"),
                   beak_col="darker", preview={"primary": "#1E1E24", "secondary": "#2A6AE8", "darker": "#2A2A2A", "horn": "#8A6A4A"})


@hero("kiwi", "birds")
def kiwi():
    return _walker("kiwi", upright=0.05, body=1.0, girth=1.15, neck=0.2, neck_r=0.34, nneck=1, neck_lean=0.6, head=0.95, beak="needle",
                   beak_len=1.3, beak_depth=0.13, beak_w=0.12, leg=0.6, leg_r=0.09, toe=0.38, eye=0.1, wing="none", tail="none",
                   fluffy=0.018, fur_freq=28.0, period=0.55, headbob=0.03, stride=0.45, pat="streaks",
                   cols=dict(belly="primary", leg=[0.85, 0.72, 0.6]), beak_col="cream",
                   preview={"primary": "#6A5440", "secondary": "#C8B490", "cream": "#E8D8B8"})


@hero("dodo", "birds")
def dodo():
    return _walker("dodo", upright=0.2, body=1.15, girth=1.3, neck=0.45, neck_r=0.28, nneck=2, neck_lean=0.3, head=1.2, beak="hook",
                   beak_len=0.75, beak_depth=0.36, beak_w=0.26, leg=0.8, leg_r=0.12, toe=0.42, eye=0.13, eye_col="iris", wing="folded",
                   wing_len=0.45, tail="plume", tail_len=0.5, period=0.85, headbob=0.06, waddle=0.08, gait="waddle", bald=True, drum=0.65,
                   cols=dict(belly="primary", head=[0.75, 0.72, 0.68], tail="secondary", leg=[0.85, 0.72, 0.4], flight="secondary"),
                   beak_col="secondary", preview={"primary": "#8A8A8E", "secondary": "#F2E8C8", "iris": "#E8D07A"})


@hero("terror bird", "birds")
def terror_bird():
    return _walker("terror bird", upright=0.2, body=1.35, girth=1.15, neck=1.2, neck_r=0.24, nneck=2, neck_lean=0.4, head=1.7, beak="hook",
                   beak_len=0.85, beak_depth=0.5, beak_w=0.28, leg=2.4, leg_r=0.14, bare_tibia=1.0, drum=1.2, toe=0.55, eye=0.12, eye_col="iris",
                   wing="folded", wing_len=0.45, tail="plume", tail_len=0.7, period=0.7, stride=0.5, headbob=0.05, attack="lunge", run=True,
                   cols=dict(belly="secondary", leg=[0.55, 0.45, 0.35], tail="primary", thigh="primary"), beak_col="horn",
                   preview={"primary": "#6A4A2E", "secondary": "#D8A04A", "horn": "#E8D8B0", "iris": "#E8C030"})
