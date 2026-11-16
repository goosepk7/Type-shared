#!/usr/bin/env python3
"""Sculpt every catalogue piece into tools/meshgen/out/<id>.glb and write out/manifest.json.

  python3 tools/meshgen/build.py [--only id1,id2] [--jobs 4] [--no-ao] [--preview out.png]

Per piece: SDF -> marching cubes -> Taubin smooth -> quadric decimation to the triangle budget ->
recentre (bounds centre = MeshPart pivot) -> optional fit to the exact native box -> AO-baked
greyscale vertex colours (Roblox keeps COLOR_0 and multiplies it by MeshPart.Color) -> .glb
(pre-rotated 180 degrees about Y for the Roblox importer).
"""
import argparse, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "out")


def make(pid, ao=True):
    from catalogue import load_all
    import mesher

    p = load_all()[pid]
    t = time.time()
    m = mesher.build(p.fn(), p.region, tris=p.tris, res=p.res, smooth=p.smooth, fit=p.fit)
    origin = [float(v) for v in m.origin]
    aoc = mesher.bake_ao(m) if ao else None
    mesher.export_glb(m, os.path.join(OUT, pid + ".glb"), pid, aoc)
    size = (m.bounds[1] - m.bounds[0]).tolist()
    if p.lead:
        # authored in studs on a reference lead: record unit-frame values (fractions of the lead's size)
        size = [float(s / l) for s, l in zip(size, p.lead)]
        origin = [float(o / l) for o, l in zip(origin, p.lead)]
    flat = mesher.flat_faces(m)
    return pid, {
        "size": [round(v, 4) for v in size],
        "origin": [0.0, 0.0, 0.0] if p.fit else [round(v, 4) for v in origin],
        "tris": int(len(m.faces)),
        "kind": p.kind,
        "pivot": p.pivot,
        "note": p.note,
        "set": p.set,
        "flat": flat,
    }, time.time() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--no-ao", action="store_true")
    a = ap.parse_args()
    from catalogue import load_all

    reg = load_all()
    ids = [i for i in reg if not a.only or i in a.only.split(",")]
    os.makedirs(OUT, exist_ok=True)
    mpath = os.path.join(OUT, "manifest.json")
    man = json.load(open(mpath)) if os.path.exists(mpath) else {}
    man = {k: v for k, v in man.items() if k in reg}
    with ProcessPoolExecutor(a.jobs) as ex:
        futs = [ex.submit(make, i, not a.no_ao) for i in ids]
        for f in futs:
            try:
                pid, info, dt = f.result()
            except Exception as e:  # report and continue
                print("FAILED", ids[futs.index(f)], e)
                continue
            man[pid] = info
            print(f"{pid:22s} {info['tris']:5d} tris  size {info['size']}  {dt:.1f}s" + ("  FLAT " + ",".join(info["flat"]) if info["flat"] else ""))
    json.dump(dict(sorted(man.items())), open(mpath, "w"), indent=1)
    print(f"{len(man)} pieces, {sum(v['tris'] for v in man.values())} triangles total")


if __name__ == "__main__":
    main()
