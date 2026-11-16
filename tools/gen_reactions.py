#!/usr/bin/env python3
"""Compile data/reactions.json + data/matchups.json + data/material_reactions.json into the GENERATED block of src/Shared/Reactions.luau.

data/*.json is the source of truth. Run after editing either file:
    python3 tools/gen_reactions.py          # rewrite
    python3 tools/gen_reactions.py --check  # exit 1 if Reactions.luau is stale (CI)
tests/specs/reactions.spec.luau also checks the embedded data equals the JSON.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, "src", "Shared", "Reactions.luau")
BEGIN, END = "-- BEGIN GENERATED DATA (tools/gen_reactions.py)", "-- END GENERATED DATA"


def lstr(s):
    return json.dumps(s, ensure_ascii=False)  # JSON string escapes are valid Luau


def ltab(xs):
    return "{ " + ", ".join(lstr(x) for x in xs) + " }" if xs else "{}"


def num(n):
    return repr(float(n)).rstrip("0").rstrip(".") if isinstance(n, float) else str(n)


def build():
    m = json.load(open(os.path.join(ROOT, "data", "matchups.json"), encoding="utf-8"))
    r = json.load(open(os.path.join(ROOT, "data", "reactions.json"), encoding="utf-8"))
    els = m["elements"]
    out = [BEGIN, "local ELEMENTS = " + ltab(els), "local MATCHUPS = {"]
    for a in els:
        row = m["table"][a]
        out.append("\t%s = {" % a)
        for d in els:
            out.append("\t\t%s = { m = %s, why = %s }," % (d, num(row[d]["m"]), lstr(row[d]["why"])))
        out.append("\t},")
    out.append("}")
    out.append("local REACTIONS = {")
    for x in r["reactions"]:
        out.append(
            "\t{ id = %s, elements = %s, name = %s, description = %s, result = %s, statuses = %s, hooks = %s, magnitudeHint = %s, durationHint = %s, vfx = %s, sfx = %s },"
            % (lstr(x["id"]), ltab(x["elements"]), lstr(x["name"]), lstr(x["description"]), lstr(x["result"]),
               ltab(x["statuses"]), ltab(x["hooks"]), num(x["magnitudeHint"]), num(x["durationHint"]), lstr(x["vfx"]), lstr(x["sfx"])))
    out.append("}")
    mr = json.load(open(os.path.join(ROOT, "data", "material_reactions.json"), encoding="utf-8"))
    out.append("local MATERIAL_OUTCOMES = {")
    for k in sorted(mr["outcomes"]):
        o = mr["outcomes"][k]
        tr = ""
        if o.get("transform"):
            tr = ", transform = { " + ", ".join("%s = %s" % (tk, lstr(tv)) for tk, tv in sorted(o["transform"].items())) + " }"
        out.append(
            "\t%s = { name = %s, description = %s, statuses = %s, hooks = %s, magnitudeHint = %s, durationHint = %s, vfx = %s, sfx = %s%s },"
            % (k, lstr(o["name"]), lstr(o["description"]), ltab(o["statuses"]), ltab(o["hooks"]), num(o["magnitudeHint"]),
               num(o["durationHint"]), lstr(o["vfx"]), lstr(o["sfx"]), tr))
    out.append("}")
    out.append("local MATERIAL_RULES = {")
    for x in mr["rules"]:
        out.append("\t{ element = %s, tags = %s, outcome = %s }," % (lstr(x["element"]), ltab(x["tags"]), lstr(x["outcome"])))
    out.append("}")
    out.append("local MATERIAL_OVERRIDES = {")
    for mid in sorted(mr["overrides"]):
        row = mr["overrides"][mid]
        out.append("\t[%s] = { %s }," % (lstr(mid), ", ".join("%s = %s" % (e, lstr(row[e])) for e in sorted(row))))
    out.append("}")
    out.append(END)
    return "\n".join(out)


def main():
    src = open(TARGET, encoding="utf-8").read()
    i, j = src.index(BEGIN), src.index(END) + len(END)
    new = src[:i] + build() + src[j:]
    if "--check" in sys.argv:
        if new != src:
            print("Reactions.luau is stale: run python3 tools/gen_reactions.py")
            sys.exit(1)
        print("Reactions.luau up to date")
        return
    open(TARGET, "w", encoding="utf-8").write(new)
    print("wrote", os.path.relpath(TARGET, ROOT))


if __name__ == "__main__":
    main()
