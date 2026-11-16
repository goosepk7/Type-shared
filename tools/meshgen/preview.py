#!/usr/bin/env python3
"""Contact sheet of catalogue pieces (QA for sculpts).

  python3 tools/meshgen/preview.py out.png [--only a,b] [--set summon] [--match head] [--size 200] [--cols 8] [--views 1|2|3]
"""
import argparse, json, os, sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rt  # noqa: E402

COLS = [(0.45, 0.7, 0.35), (0.85, 0.55, 0.3), (0.5, 0.6, 0.85), (0.8, 0.75, 0.6), (0.75, 0.4, 0.5)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--only", default="")
    ap.add_argument("--size", type=int, default=200)
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--views", type=int, default=1)
    ap.add_argument("--set", default="", help="only pieces of this set (td | summon)")
    ap.add_argument("--match", default="", help="only ids containing this text")
    a = ap.parse_args()
    man = json.load(open(os.path.join(HERE, "out", "manifest.json")))
    ids = [i for i in man if (not a.only or i in a.only.split(",")) and (not a.set or man[i].get("set") == a.set) and (not a.match or a.match in i)]
    W = a.size
    views = [(35, 25), (200, 25), (90, 5)][: a.views]
    cw = W * len(views)
    cols = min(a.cols, len(ids))
    rows = (len(ids) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cw + 4), rows * (W + 18)), (18, 18, 22))
    dr = ImageDraw.Draw(sheet)
    for i, pid in enumerate(ids):
        info = man[pid]
        part = {"s": "Mesh", "piece": pid, "size": info["size"], "cf": [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1], "col": COLS[i % len(COLS)], "tr": 0, "mat": "SmoothPlastic"}
        x0 = (i % cols) * (cw + 4)
        y0 = (i // cols) * (W + 18)
        for j, (az, el) in enumerate(views):
            img = rt.render([part], az, el, W, ss=2, ao_rays=4, ground=False)
            sheet.paste(Image.fromarray(img), (x0 + j * W, y0 + 16))
        dr.text((x0 + 3, y0 + 2), f"{pid} {info['tris']}t", fill=(230, 230, 230))
    sheet.save(a.out)
    print("wrote", a.out, len(ids))


if __name__ == "__main__":
    main()
