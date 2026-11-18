#!/usr/bin/env python3
"""Build hero models: mesh every sculpted piece (tools/meshgen/out/<key>.glb, manifest set "hero") and write the
runtime data modules src/Shared/Summon/Heroes/Data/<family>.luau.

  python3 tools/meshgen/heroes/build.py [--only lion,tiger] [--family felines] [--jobs 4] [--force] [--data-only]

Pieces are cached by a hash of the hero module's source + the piece key: an unchanged family rebuilds no meshes.
Writing the data needs every piece of the written heroes to have been meshed (its bounds become the part box).
"""
import argparse, hashlib, importlib, json, math, os, sys, time
import multiprocessing as mp

HERE = os.path.dirname(os.path.abspath(__file__))
MG = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(MG))
sys.path.insert(0, MG)
sys.path.insert(0, HERE)
OUT = os.path.join(MG, "out")
DATA = os.path.join(ROOT, "src/Shared/Summon/Heroes/Data")
CACHE = os.path.join(OUT, "hero_cache.json")

import numpy as np  # noqa: E402

import kit  # noqa: E402


def modules():
    return sorted(f[:-3] for f in os.listdir(HERE) if f.startswith("h_") and f.endswith(".py"))


def load():
    srcs = {}
    for m in modules():
        before = set(kit.REG)
        importlib.import_module(m)
        h = hashlib.sha1(open(os.path.join(HERE, m + ".py"), "rb").read() + open(os.path.join(HERE, "kit.py"), "rb").read()).hexdigest()[:12]
        for hid in set(kit.REG) - before:
            srcs[hid] = (m, h)
    return srcs


_HEROES = {}


def get(hid):
    if hid not in _HEROES:
        _HEROES[hid] = kit.REG[hid]()
    return _HEROES[hid]


def mesh_piece(job):
    hid, idx = job
    import mesher
    import sdf as S

    H = get(hid)
    p = H.parts[idx]
    t0 = time.time()
    lo, hi = H.bounds_hint()
    vol, step = mesher.sample(p["sdf"], lo, hi, 80)
    inside = np.argwhere(vol < step * 0.5)
    if len(inside) == 0:
        raise ValueError(f"{hid}/{p['name']}: empty sculpt")
    plo = lo + (inside.min(0) - 1) * step
    phi = lo + (inside.max(0) + 1) * step
    c = (plo + phi) / 2
    half = (phi - plo) / 2
    base = p["sdf"]
    shifted = S.SDF(lambda q: base(q + c))
    m = mesher.build(shifted, half, tris=p["tris"], res=p["res"], smooth=p["smooth"])
    origin = c + np.asarray(m.origin)
    col = mesher.bake_ao(m) if p["ao"] else np.ones(len(m.vertices))
    if p["pattern"] is not None:
        col = col * np.clip(p["pattern"](m.vertices + origin), 0.05, 1.0)
    mesher.export_glb(m, os.path.join(OUT, p["key"] + ".glb"), p["key"], col)
    size = (m.bounds[1] - m.bounds[0]).tolist()
    return p["key"], {
        "size": [round(v, 4) for v in size], "origin": [0.0, 0.0, 0.0], "tris": int(len(m.faces)), "kind": "box",
        "pivot": "center", "note": f"hero {hid}: {p['name']}", "set": "hero", "flat": mesher.flat_faces(m),
        "centre": [round(float(v), 4) for v in origin],
    }, time.time() - t0


def num(v):
    v = float(v)
    if abs(v) < 5e-5:
        return "0"
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s


def lua_str(s):
    return json.dumps(s)


def lua_col(c):
    if isinstance(c, (list, tuple)):
        return "{ " + ", ".join(num(x) for x in c) + " }"
    return lua_str(c)


def hero_lua(H, man):
    L = []
    L.append(f"\t[{lua_str(H.id)}] = {{")
    L.append(f"\t\tplan = {lua_str(H.plan)}, gait = {lua_str(H.gait)},")
    if H.tags:
        L.append("\t\ttags = { " + ", ".join(lua_str(t) for t in H.tags) + " },")
    L.append("\t\tbones = {")
    for name, parent, pos in H.bones:
        L.append(f"\t\t\t{{ {lua_str(name)}, {lua_str(parent) if parent else 'nil'}, {num(pos[0])}, {num(pos[1])}, {num(pos[2])} }},")
    L.append("\t\t},")
    L.append("\t\tparts = {")
    for p in H.parts:
        f = []
        f.append(f"name = {lua_str(p['name'])}")
        f.append(f"bone = {lua_str(p['bone'])}")
        if p["kind"] == "piece":
            info = man[p["key"]]
            f.append(f"shape = {lua_str(p['fallback'])}")
            f.append("size = { " + ", ".join(num(x) for x in info["size"]) + " }")
            f.append("pos = { " + ", ".join(num(x) for x in info["centre"]) + " }")
            f.append(f"mesh = {lua_str(p['key'])}")
        else:
            f.append(f"shape = {lua_str(p['shape'])}")
            f.append("size = { " + ", ".join(num(x) for x in p["size"]) + " }")
            f.append("pos = { " + ", ".join(num(x) for x in p["pos"]) + " }")
            if any(abs(r) > 1e-6 for r in p["rot"]):
                f.append("rot = { " + ", ".join(num(x) for x in p["rot"]) + " }")
            if p.get("trail"):
                f.append("trail = true")
        f.append(f"col = {lua_col(p['col'])}")
        f.append(f"mat = {lua_str(p['mat'])}")
        f.append(f"pri = {num(p['pri'])}")
        f.append(f"role = {lua_str(p['role'])}")
        if p.get("tr"):
            f.append(f"tr = {num(p['tr'])}")
        if p.get("glow"):
            f.append("glow = true")
        if p.get("pair"):
            f.append(f"pair = {lua_str(H.id + ':' + p['pair'])}")
        if p.get("mirrored"):
            f.append("mirrored = true")
        if p.get("needs"):
            f.append(f"needs = {lua_str(p['needs'])}")
        L.append("\t\t\t{ " + ", ".join(f) + " },")
    L.append("\t\t},")
    rig = dict(H.rig)
    L.append("\t\trig = " + lua_value(rig, 2) + ",")
    if H.sockets:
        L.append("\t\tsockets = {")
        for k, (pos, bone) in H.sockets.items():
            L.append(f"\t\t\t[{lua_str(k)}] = {{ pos = {{ {num(pos[0])}, {num(pos[1])}, {num(pos[2])} }}, bone = {lua_str(bone)} }},")
        L.append("\t\t},")
    if H.mount:
        L.append("\t\tmount = " + lua_value(H.mount, 2) + ",")
    if H.clips:
        L.append("\t\tclips = {")
        for cname, c in H.clips.items():
            L.append(f"\t\t\t[{lua_str(cname)}] = {{ len = {num(c['len'])}, loop = {'true' if c['loop'] else 'false'}, keys = {c['keys']}, tracks = {{")
            for b, vals in c["tracks"].items():
                flat = []
                for v in vals:
                    flat.extend(v)
                if all(abs(x) < 1e-5 for x in flat):
                    continue
                L.append(f"\t\t\t\t[{lua_str(b)}] = {{ " + ", ".join(num(x) for x in flat) + " },")
            L.append("\t\t\t} },")
        L.append("\t\t},")
    L.append("\t},")
    return L


def lua_value(v, depth=0):
    if isinstance(v, dict):
        items = []
        for k, x in v.items():
            key = k if isinstance(k, str) and k.isidentifier() else f"[{lua_str(k)}]"
            items.append(f"{key} = {lua_value(x, depth + 1)}")
        return "{ " + ", ".join(items) + " }"
    if isinstance(v, (list, tuple)):
        return "{ " + ", ".join(lua_value(x, depth + 1) for x in v) + " }"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return num(v)
    if v is None:
        return "nil"
    return lua_str(v)


def write_family(fam, hids, man):
    os.makedirs(DATA, exist_ok=True)
    L = ["--!strict", f"-- GENERATED by tools/meshgen/heroes/build.py from tools/meshgen/heroes/*.py (family {fam}). Do not edit.",
         "-- See Summon/Heroes/init.luau for the format.", "return {"]
    for hid in sorted(hids):
        L.extend(hero_lua(get(hid), man))
    L.append("} :: { [string]: any }")
    path = os.path.join(DATA, fam + ".luau")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")
    return path


def write_index():
    os.makedirs(DATA, exist_ok=True)
    fams = sorted(f[:-5] for f in os.listdir(DATA) if f.endswith(".luau"))
    L = ["--!strict", "-- GENERATED by tools/meshgen/heroes/build.py: every hero data family. Do not edit.", "local Data = script.Parent", "return {"]
    for f in fams:
        L.append(f"\t{lua_str(f)},")
    L.append("}")
    with open(os.path.join(os.path.dirname(DATA), "Families.luau"), "w") as fh:
        fh.write("\n".join(L).replace("local Data = script.Parent\n", "") + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--family", default="")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--data-only", action="store_true")
    a = ap.parse_args()
    srcs = load()
    hids = [h for h in kit.REG if (not a.only or h in a.only.split(",")) and (not a.family or kit.FAMILY[h] in a.family.split(","))]
    os.makedirs(OUT, exist_ok=True)
    mpath = os.path.join(OUT, "manifest.json")
    man = json.load(open(mpath)) if os.path.exists(mpath) else {}
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    jobs, seen = [], set()
    for hid in hids:
        H = get(hid)
        for i, p in enumerate(H.parts):
            if p["kind"] != "piece" or p["key"] in seen:
                continue
            seen.add(p["key"])
            tag = srcs[hid][1]
            fresh = cache.get(p["key"]) == tag and p["key"] in man and os.path.exists(os.path.join(OUT, p["key"] + ".glb"))
            if a.data_only or (fresh and not a.force):
                continue
            jobs.append((hid, i))
    print(f"{len(hids)} heroes, {len(seen)} pieces, {len(jobs)} to mesh")
    if jobs:
        ctx = mp.get_context("fork")
        with ctx.Pool(a.jobs) as pool:
            for key, info, dt in pool.imap_unordered(mesh_piece, jobs):
                man[key] = info
                hid = next(h for h, i in jobs if get(h).parts[i]["key"] == key)
                cache[key] = srcs[hid][1]
                print(f"  {key:34s} {info['tris']:5d} tris  {dt:.1f}s")
        json.dump(dict(sorted(man.items())), open(mpath, "w"), indent=1)
        json.dump(cache, open(CACHE, "w"), indent=0)
    fams = {}
    for hid in kit.REG:
        fams.setdefault(kit.FAMILY[hid], []).append(hid)
    for fam, members in fams.items():
        if a.family and fam not in a.family.split(","):
            continue
        if a.only and not set(members) & set(a.only.split(",")):
            continue
        missing = [p["key"] for h in members for p in get(h).parts if p["kind"] == "piece" and p["key"] not in man]
        if missing:
            print(f"family {fam}: {len(missing)} pieces not meshed yet (e.g. {missing[:3]}); data not written")
            continue
        print("wrote", write_family(fam, members, man))
    write_index()


if __name__ == "__main__":
    main()
