#!/usr/bin/env python3
"""Validate every data/words/*.jsonl entry. Usage: python3 tools/validate.py [--stats] [files...]
Exit code 1 on any error. Checks schema, enums, ranges, hex colours, flavour length, and global uniqueness of
every id and alias across the whole library (an alias may not equal another entry's id or alias)."""
import json, re, sys, glob, collections, os
sys.path.insert(0, os.path.dirname(__file__))
from schema import *

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
WORD = re.compile(r"^[a-z0-9][a-z0-9 '\-]*[a-z0-9]$|^[a-z0-9]$")
REQ = ["w","c","e","z","s","b","p","sp","d","pc","sc","bp","sh","m","snd","f"]
ENUMS = {"c":CATEGORY,"e":ELEMENT,"z":SIZE,"s":SHAPE,"bp":BODYPLAN,"m":MOTION}

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    stats = "--stats" in sys.argv
    files = args or sorted(glob.glob("data/words/*.jsonl"))
    allfiles = sorted(glob.glob("data/words/*.jsonl"))
    errors = []
    owner = {}  # key -> (file:line, id)
    entries = []
    for path in allfiles:
        checking = path in files
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                loc = f"{path}:{n}"
                try:
                    e = json.loads(line)
                except Exception as ex:
                    errors.append(f"{loc}: bad JSON ({ex})"); continue
                w = e.get("w", "")
                if checking:
                    for k in REQ:
                        if k not in e: errors.append(f"{loc} {w}: missing '{k}'")
                    for k, lst in ENUMS.items():
                        if k in e and e[k] not in lst: errors.append(f"{loc} {w}: bad {k}={e[k]!r}")
                    for b in e.get("b", []):
                        if b not in BEHAVIOUR: errors.append(f"{loc} {w}: bad behaviour {b!r}")
                    if len(set(e.get("b", []))) != len(e.get("b", [])): errors.append(f"{loc} {w}: duplicate behaviour")
                    if len(e.get("b", [])) > 8: errors.append(f"{loc} {w}: >8 behaviours")
                    for k in ("p","sp","d"):
                        v = e.get(k)
                        if not isinstance(v, int) or not 1 <= v <= 10: errors.append(f"{loc} {w}: {k} must be int 1..10")
                    for k in ("pc","sc"):
                        if k in e and not HEX.match(str(e[k])): errors.append(f"{loc} {w}: bad colour {k}")
                    if len(e.get("f","")) > 80: errors.append(f"{loc} {w}: flavour > 80 chars")
                    if len(e.get("sh","")) > 60: errors.append(f"{loc} {w}: silhouette > 60 chars")
                    if not WORD.match(w): errors.append(f"{loc}: bad id {w!r}")
                    for a in e.get("a", []):
                        if not WORD.match(a): errors.append(f"{loc} {w}: bad alias {a!r}")
                    if len(e.get("t", [])) > 8: errors.append(f"{loc} {w}: >8 tags")
                for key in [w] + list(e.get("a", [])):
                    if key in owner and owner[key][1] != w:
                        errors.append(f"{loc} {w}: '{key}' already used by '{owner[key][1]}' at {owner[key][0]}")
                    elif key in owner and key != w and owner[key][1] == w:
                        pass
                    else:
                        owner.setdefault(key, (loc, w))
                entries.append(e)
    ids = collections.Counter(e.get("w") for e in entries)
    for w, c in ids.items():
        if c > 1: errors.append(f"duplicate id {w!r} x{c}")
    for err in errors[:400]:
        print("ERROR", err)
    if len(errors) > 400: print(f"... {len(errors)-400} more")
    print(f"{len(entries)} entries, {len(owner)} lookup keys, {len(errors)} errors")
    if stats:
        for field, name in (("c","category"),("e","element"),("z","size"),("s","shape")):
            c = collections.Counter(e.get(field) for e in entries)
            print(f"\n{name}: " + ", ".join(f"{k}={v}" for k, v in c.most_common()))
        print("\nsignature:", sum(1 for e in entries if e.get("sig")))
        pw = collections.Counter(e.get("p") for e in entries)
        print("power:", ", ".join(f"{k}={pw[k]}" for k in sorted(pw)))
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
