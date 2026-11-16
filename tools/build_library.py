#!/usr/bin/env python3
"""Compile the word library into Luau ModuleScripts under src/Shared/Library/Generated/.

Usage:
  python3 tools/build_library.py            # (re)write Generated/
  python3 tools/build_library.py --check    # exit 1 if committed Generated/ is stale
  python3 tools/build_library.py --quiet    # no report

Inputs:  data/words/*.jsonl, data/misspellings.jsonl, data/modifiers.json, data/materials.json,
         data/protected_names.json, data/keyboard.json
Outputs (all deterministic, sorted, no timestamps):
  Index.luau        meta, enum tables, ids (ordinal order), rank, packed attrs, signature/group maps,
                    prefix top-lists (1-2 chars), chunk + shard counts
  Chunk_NNN.luau    ~400 entries each as compact positional arrays (lazy loaded by Library)
  Keys_NN.luau      sorted display/fuzzy keys (ids + authored aliases) + owner ordinals + Double Metaphone codes
  Miss_NN.luau      known misspellings -> ordinal (plurals/spacing variants are derived at runtime)
  Modifiers.luau    compiled data/modifiers.json
  Materials.luau    compiled data/materials.json (Types.Material records)
  Protected.luau    compiled data/protected_names.json (brand/franchise/real-person -> generic phrase)
  Keyboard.luau     pairwise substitution costs (QWERTY/phone/QWERTZ/AZERTY) + edit costs

Collision policy: the first owner (by sorted id) of an authored key wins; generated keys never shadow authored keys
and are dropped when two entries generate the same key; misspellings that are real keys or point at unknown words
are dropped. Everything dropped is reported (tools/validate.py is the place that *fails* on authoring errors).
"""
import glob
import hashlib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from schema import CATEGORY, ELEMENT, SIZE, SHAPE, BEHAVIOUR, BODYPLAN, MOTION  # noqa: E402
from metaphone import double_metaphone  # noqa: E402

OUT_DIR = os.path.join(ROOT, "src", "Shared", "Library", "Generated")
CHUNK_SIZE = 400
SHARD_SIZE = 4000
PREFIX_TOP = 12
CODE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&()*+-./:;<=>?@[]^_{}~"
WORD_RE = re.compile(r"^[a-z0-9][a-z0-9 '\-]*[a-z0-9]$|^[a-z0-9]$")
REQ = ["w", "c", "e", "z", "s", "b", "p", "sp", "d", "pc", "sc", "bp", "sh", "m", "snd", "f"]
HEX_RE = re.compile(r"^#?([0-9A-Fa-f]{6})$")

report = []


def warn(msg):
    report.append(msg)


# ---------------------------------------------------------------- helpers

def lua_str(s):
    out = ['"']
    for ch in s:
        o = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif o < 32 or o == 127:
            out.append("\\%03d" % o)
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def lua_list(items, per_line=0, indent="\t"):
    parts = [lua_str(x) if isinstance(x, str) else fmt_num(x) for x in items]
    if not per_line:
        return "{" + ",".join(parts) + "}"
    lines = []
    for i in range(0, len(parts), per_line):
        lines.append(indent + ",".join(parts[i:i + per_line]) + ",")
    return "{\n" + "\n".join(lines) + "\n" + indent[:-1] + "}"


def fmt_num(x):
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, int):
        return str(x)
    if float(x).is_integer():
        return str(int(x))
    return repr(round(float(x), 4))


def clean_key(s):
    if not isinstance(s, str):
        return None
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s if WORD_RE.match(s) else None


def is_vowel(c):
    return c in "aeiou"


def plurals(word):
    """Regular English plural candidates for the last token of a key."""
    head, _, last = word.rpartition(" ")
    pre = head + " " if head else ""
    out = []
    if len(last) < 2 or not last[-1].isalpha():
        return out
    if last.endswith(("s", "x", "z", "ch", "sh")):
        out.append(last + "es")
    elif last.endswith("y") and len(last) > 1 and not is_vowel(last[-2]):
        out.append(last[:-1] + "ies")
    elif last.endswith("fe"):
        out += [last[:-2] + "ves", last + "s"]
    elif last.endswith("f") and not last.endswith("ff"):
        out += [last[:-1] + "ves", last + "s"]
    elif last.endswith("o") and len(last) > 1 and not is_vowel(last[-2]):
        out += [last + "es", last + "s"]
    elif last.endswith("man") and len(last) > 3:
        out += [last[:-3] + "men", last + "s"]
    elif last.endswith("us") and len(last) > 4:
        out += [last[:-2] + "i", last + "es"]
    else:
        out.append(last + "s")
    return [pre + p for p in out]


def spacing_variants(key):
    out = []
    if "-" in key:
        out.append(key.replace("-", " "))
        out.append(key.replace("-", ""))
    if " " in key:
        out.append(key.replace(" ", ""))
        out.append(key.replace(" ", "-"))
    if "'" in key:
        out.append(key.replace("'", ""))
    out2 = []
    for v in out:
        v = re.sub(r"\s+", " ", v).strip()
        if v != key and v and WORD_RE.match(v) and v not in out2:
            out2.append(v)
    return out2


def phon_code(key):
    p, s = double_metaphone(key)
    if not p and not s:
        return ""
    return p if p == s else p + "/" + s


# ---------------------------------------------------------------- load

def load_entries():
    entries = []
    seen = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "words", "*.jsonl"))):
        rel = os.path.relpath(path, ROOT)
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except Exception as ex:  # noqa: BLE001
                    warn(f"{rel}:{n}: bad JSON ({ex}); skipped")
                    continue
                missing = [k for k in REQ if k not in e]
                w = clean_key(e.get("w"))
                if missing or not w:
                    warn(f"{rel}:{n}: entry {e.get('w')!r} missing {missing or 'valid w'}; skipped")
                    continue
                if w in seen:
                    warn(f"{rel}:{n}: duplicate id {w!r} (first at {seen[w]}); skipped")
                    continue
                seen[w] = f"{rel}:{n}"
                e["w"] = w
                e["_loc"] = f"{rel}:{n}"
                entries.append(e)
    entries.sort(key=lambda e: e["w"])
    return entries


def enum_index(lst, value, default):
    try:
        return lst.index(value)
    except ValueError:
        return lst.index(default)


def clamp_int(v, lo, hi, default):
    try:
        v = int(round(float(v)))
    except Exception:  # noqa: BLE001
        return default
    return max(lo, min(hi, v))


def hex6(v, default):
    m = HEX_RE.match(str(v or ""))
    return m.group(1).upper() if m else default


def clean_text(s, n):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s[:n]


def clean_tags(tags):
    out = []
    for t in tags or []:
        t = re.sub(r"[^a-z0-9 \-]", "", str(t).lower()).strip()
        if t and t not in out:
            out.append(t)
    return out[:8]


def rank_of(e):
    """Popularity heuristic: signature words, well-aliased (familiar) words and short single words rank higher."""
    w = e["w"]
    r = 0
    if e.get("sig"):
        r += 400
    r += 18 * min(len(e.get("a") or []), 8)
    r += 10 * min(len(e.get("ms") or []), 4)
    if " " not in w and "-" not in w:
        r += 60
    r -= 4 * len(w)
    r += {"Creature": 20, "Element": 20, "Weapon": 15, "Disaster": 15, "Weather": 10}.get(e.get("c"), 0)
    return max(0, r + 100)


# ---------------------------------------------------------------- build

def build():
    entries = load_entries()
    n = len(entries)
    ordinal = {e["w"]: i + 1 for i, e in enumerate(entries)}

    # Authored keys: ids first (so an id always beats someone else's alias), then aliases.
    authored = {}  # key -> ord
    kinds = {}  # key -> 'id' | 'alias'
    for e in entries:
        authored[e["w"]] = ordinal[e["w"]]
        kinds[e["w"]] = "id"
    for e in entries:
        o = ordinal[e["w"]]
        for a in e.get("a") or []:
            k = clean_key(a)
            if not k:
                warn(f"{e['_loc']}: bad alias {a!r} on {e['w']!r}; skipped")
                continue
            if k in authored:
                if authored[k] != o:
                    warn(f"{e['_loc']}: alias {k!r} of {e['w']!r} already owned by {entries[authored[k]-1]['w']!r}; skipped")
                continue
            authored[k] = o
            kinds[k] = "alias"

    # Generated keys: plurals + spacing variants. Never shadow authored keys; drop ambiguous ones.
    gen = {}
    ambiguous = set()
    for k in sorted(authored):
        o = authored[k]
        cands = list(spacing_variants(k))
        cands += plurals(k)
        for v in list(cands):
            cands += [p for p in plurals(v) if p not in cands] if v in spacing_variants(k) else []
        for c in cands:
            c = clean_key(c)
            if not c or c in authored or c in ambiguous:
                continue
            if c in gen and gen[c] != o:
                del gen[c]
                ambiguous.add(c)
                continue
            gen[c] = o

    # Misspellings: data/misspellings.jsonl (wins conflicts) + per-entry 'ms'. Target may be an id or alias.
    miss = {}
    dangling = 0
    shadow = 0

    def add_miss(m, target_key, where):
        nonlocal dangling, shadow
        m = clean_key(m)
        t = clean_key(target_key)
        if not m:
            return
        o = authored.get(t) if t else None
        if o is None and t:
            o = gen.get(t)
        if o is None:
            dangling += 1
            warn(f"{where}: misspelling {m!r} -> unknown word {target_key!r}; dropped")
            return
        if m in authored or m in gen:
            shadow += 1
            return
        if m in miss and miss[m] != o:
            warn(f"{where}: misspelling {m!r} maps to both {entries[miss[m]-1]['w']!r} and {entries[o-1]['w']!r}; kept first")
            return
        miss[m] = o

    mpath = os.path.join(ROOT, "data", "misspellings.jsonl")
    if os.path.exists(mpath):
        with open(mpath, encoding="utf-8") as fh:
            for ln, line in enumerate(fh, 1):
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                try:
                    row = json.loads(line)
                except Exception as ex:  # noqa: BLE001
                    warn(f"data/misspellings.jsonl:{ln}: bad JSON ({ex})")
                    continue
                for m in row.get("ms") or []:
                    add_miss(m, row.get("w"), f"data/misspellings.jsonl:{ln}")
    # curated data/misspellings.jsonl first (it wins conflicts), then per-entry 'ms'
    for e in entries:
        for m in e.get("ms") or []:
            add_miss(m, e["w"], e["_loc"])

    # ------------------------------------------------ entries -> chunks
    files = {}
    ids = [e["w"] for e in entries]
    ranks = [rank_of(e) for e in entries]
    attrs = []
    sig = []
    groups = {}
    for i, e in enumerate(entries):
        o = i + 1
        c = enum_index(CATEGORY, e.get("c"), "Object")
        el = enum_index(ELEMENT, e.get("e"), "None")
        z = enum_index(SIZE, e.get("z"), "Medium")
        s = enum_index(SHAPE, e.get("s"), "Summon")
        attrs.append(CODE[c] + CODE[el] + CODE[z] + CODE[s])
        if e.get("sig"):
            sig.append(o)
        g = clean_key(e.get("g"))
        if g and g != e["w"]:
            groups[o] = g

    chunk_count = max(1, math.ceil(n / CHUNK_SIZE))
    for ci in range(chunk_count):
        part = entries[ci * CHUNK_SIZE:(ci + 1) * CHUNK_SIZE]
        lines = [
            "--!strict",
            "-- GENERATED by tools/build_library.py from data/words/*.jsonl. DO NOT EDIT.",
            "-- Entry: {id, enums(c e z s bp m), behaviours, power, speed, durability, primary, secondary,",
            "--         silhouette, sound, flavour, tags(comma separated)}  -- enums/behaviours are CODE chars",
            "return {",
        ]
        for e in part:
            enums = (CODE[enum_index(CATEGORY, e.get("c"), "Object")]
                     + CODE[enum_index(ELEMENT, e.get("e"), "None")]
                     + CODE[enum_index(SIZE, e.get("z"), "Medium")]
                     + CODE[enum_index(SHAPE, e.get("s"), "Summon")]
                     + CODE[enum_index(BODYPLAN, e.get("bp"), "Blob")]
                     + CODE[enum_index(MOTION, e.get("m"), "Static")])
            bs = []
            for b in e.get("b") or []:
                if b in BEHAVIOUR:
                    ch = CODE[BEHAVIOUR.index(b)]
                    if ch not in bs:
                        bs.append(ch)
            bs = "".join(sorted(bs, key=lambda ch: BEHAVIOUR[CODE.index(ch)]))[:8]
            row = [
                e["w"], enums, bs,
                clamp_int(e.get("p"), 1, 10, 5), clamp_int(e.get("sp"), 1, 10, 5), clamp_int(e.get("d"), 1, 10, 5),
                hex6(e.get("pc"), "9AA5B1"), hex6(e.get("sc"), "E4E7EB"),
                clean_text(e.get("sh"), 60), clean_text(e.get("snd"), 24).lower() or "whoosh",
                clean_text(e.get("f"), 80), ",".join(clean_tags(e.get("t"))),
            ]
            lines.append("\t{" + ",".join(lua_str(x) if isinstance(x, str) else fmt_num(x) for x in row) + "},")
        lines.append("}")
        files["Chunk_%03d.luau" % (ci + 1)] = "\n".join(lines) + "\n"

    # ------------------------------------------------ keys (display + fuzzy)
    keys = sorted(authored)
    key_owner = [authored[k] for k in keys]
    key_phon = [phon_code(k) for k in keys]
    key_kind = "".join("I" if kinds[k] == "id" else "A" for k in keys)
    shard_count = max(1, math.ceil(len(keys) / SHARD_SIZE))
    for si in range(shard_count):
        lo, hi = si * SHARD_SIZE, (si + 1) * SHARD_SIZE
        lines = [
            "--!strict",
            "-- GENERATED by tools/build_library.py. DO NOT EDIT. Sorted authored keys (ids + aliases),",
            "-- owner ordinals and Double Metaphone codes (\"PRI\" or \"PRI/ALT\").",
            "return {",
            "\tkeys = " + lua_list(keys[lo:hi], 16, "\t\t") + ",",
            "\towners = " + lua_list(key_owner[lo:hi], 40, "\t\t") + ",",
            "\tphon = " + lua_list(key_phon[lo:hi], 24, "\t\t") + ",",
            "\tkinds = " + lua_str(key_kind[lo:hi]) + ",",
            "}",
        ]
        files["Keys_%02d.luau" % (si + 1)] = "\n".join(lines) + "\n"

    # Plurals and spacing variants are NOT emitted: the runtime derives them (Library: spacing variants of
    # multi-word keys at index load; Stemmer: plural/-ing/-ed forms per query). That keeps Generated/ ~40% smaller.
    # They are still computed here so misspellings may target a plural and so collisions get reported.
    extra = sorted((k, o, "M") for k, o in miss.items())
    extra_count = max(1, math.ceil(len(extra) / SHARD_SIZE))
    for si in range(extra_count):
        part = extra[si * SHARD_SIZE:(si + 1) * SHARD_SIZE]
        lines = [
            "--!strict",
            "-- GENERATED by tools/build_library.py. DO NOT EDIT. Known misspellings -> owner ordinal",
            "-- (data/misspellings.jsonl + per-entry 'ms'), sorted.",
            "return {",
            "\tkeys = " + lua_list([x[0] for x in part], 16, "\t\t") + ",",
            "\towners = " + lua_list([x[1] for x in part], 40, "\t\t") + ",",
            "}",
        ]
        files["Miss_%02d.luau" % (si + 1)] = "\n".join(lines) + "\n"

    # ------------------------------------------------ prefix top-lists (1-2 chars) over authored keys
    best_by_prefix = {}
    for ki, k in enumerate(keys):
        o = key_owner[ki]
        for L in (1, 2):
            if len(k) < L:
                continue
            p = k[:L]
            best_by_prefix.setdefault(p, {})
            cur = best_by_prefix[p].get(o)
            # one key per owner: prefer the id, then the shortest alias
            score = (0 if kinds[k] == "id" else 1, len(k), k)
            if cur is None or score < cur[0]:
                best_by_prefix[p][o] = (score, ki + 1)
    prefix_lines = []
    for p in sorted(best_by_prefix):
        cands = sorted(best_by_prefix[p].items(), key=lambda kv: (-ranks[kv[0] - 1], kv[1][0][1], kv[1][0][2]))
        top = [kv[1][1] for kv in cands[:PREFIX_TOP]]
        prefix_lines.append("\t\t[" + lua_str(p) + "] = " + lua_list(top) + ",")

    # ------------------------------------------------ modifiers + keyboard
    files["Modifiers.luau"], mod_words = build_modifiers()
    files["Materials.luau"], material_count = build_materials(mod_words)
    files["Protected.luau"] = build_protected()
    files["Keyboard.luau"] = build_keyboard()

    # ------------------------------------------------ index
    body_hash = hashlib.sha1()
    for name in sorted(files):
        body_hash.update(name.encode())
        body_hash.update(files[name].encode("utf-8"))
    lines = [
        "--!strict",
        "-- GENERATED by tools/build_library.py. DO NOT EDIT. Library index: everything needed for lookups",
        "-- without decoding entries. attrs packs 4 CODE chars per ordinal: category, element, size, shape.",
        "return {",
        "\tversion = " + lua_str(body_hash.hexdigest()[:16]) + ",",
        f"\tcount = {n},",
        f"\tchunkSize = {CHUNK_SIZE},",
        f"\tchunks = {chunk_count},",
        f"\tkeyShards = {shard_count},",
        f"\tmissShards = {extra_count},",
        f"\tkeyCount = {len(keys)},",
        f"\tmissCount = {len(extra)},",
        "\tcode = " + lua_str(CODE) + ",",
        "\tenums = {",
        "\t\tCategory = " + lua_list(CATEGORY) + ",",
        "\t\tElement = " + lua_list(ELEMENT) + ",",
        "\t\tSize = " + lua_list(SIZE) + ",",
        "\t\tShape = " + lua_list(SHAPE) + ",",
        "\t\tBodyPlan = " + lua_list(BODYPLAN) + ",",
        "\t\tMotion = " + lua_list(MOTION) + ",",
        "\t\tBehaviour = " + lua_list(BEHAVIOUR) + ",",
        "\t},",
        "\tids = " + lua_list(ids, 12, "\t\t") + ",",
        "\trank = " + lua_list(ranks, 40, "\t\t") + ",",
        "\tattrs = " + lua_str("".join(attrs)) + ",",
        "\tsignature = " + lua_list(sig, 40, "\t\t") + ",",
        "\tgroups = {",
    ]
    for o in sorted(groups):
        lines.append(f"\t\t[{o}] = " + lua_str(groups[o]) + ",")
    lines.append("\t},")
    lines.append("\tprefix = {")
    lines += prefix_lines
    lines.append("\t},")
    lines.append("}")
    files["Index.luau"] = "\n".join(lines) + "\n"

    stats = {
        "entries": n, "authored_keys": len(keys), "generated_keys": len(gen), "ambiguous_generated": len(ambiguous),
        "misspellings": len(miss), "misspellings_dangling": dangling, "misspellings_shadowing_real_keys": shadow,
        "chunks": chunk_count, "signature": len(sig), "modifier_words": len(mod_words), "materials": material_count,
    }
    return files, stats


MOODS = ["Neutral", "Angry", "Sleepy", "Scared", "Crazy", "Hungry", "Happy", "Sneaky", "Lazy", "Hyper", "Confused",
         "Sad", "Smug", "Cute"]
MOD_KINDS = ["Size", "Count", "Mood", "Quality", "Element", "State", "Motion", "Material"]


def load_json(name, default):
    path = os.path.join(ROOT, "data", name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def build_modifiers():
    data = load_json("modifiers.json", {"modifiers": [], "elements": {}})
    accents = set(data.get("accents") or [])
    used = {}
    lines = [
        "--!strict",
        "-- GENERATED by tools/build_library.py from data/modifiers.json. DO NOT EDIT.",
        "-- misspellings resolve to the modifier with slightly lower confidence than aliases.",
        "return {",
        "\taccents = " + lua_list(sorted(accents)) + ",",
        "\telements = {",
    ]
    for el in sorted(data.get("elements", {})):
        v = data["elements"][el]
        if el not in ELEMENT:
            warn(f"modifiers.json: unknown element palette {el!r}")
            continue
        lines.append(f"\t\t{el} = {{ pc = {lua_str('#' + hex6(v.get('pc'), 'FFFFFF'))}, sc = {lua_str('#' + hex6(v.get('sc'), 'FFFFFF'))}, "
                     f"b = {lua_list([b for b in v.get('b', []) if b in BEHAVIOUR])}, t = {lua_list(clean_tags(v.get('t')))}, "
                     f"accents = {lua_list([a for a in v.get('ac', []) if not accents or a in accents])} }},")
    lines.append("\t},")
    lines.append("\tmodifiers = {")
    for m in data.get("modifiers", []):
        mid = clean_key(m.get("id"))
        kind = m.get("kind")
        if not mid or kind not in MOD_KINDS or kind == "Material":
            warn(f"modifiers.json: bad modifier {m.get('id')!r} kind {kind!r}")
            continue

        def take(words):
            keep = []
            for w in words:
                k = clean_key(w)
                if not k or k in keep:
                    continue
                if k in used:
                    if used[k] != mid:
                        warn(f"modifiers.json: word {k!r} of {mid!r} already used by {used[k]!r}; skipped")
                    continue
                used[k] = mid
                keep.append(k)
            return keep
        if mid in used:
            warn(f"modifiers.json: duplicate modifier id {mid!r}; skipped")
            continue
        take([mid])
        aliases = take(m.get("a") or [])
        miss = take(m.get("ms") or [])
        parts = [f"id = {lua_str(mid)}", f"kind = {lua_str(kind)}", f"order = {MOD_KINDS.index(kind) + 1}",
                 f"aliases = {lua_list(aliases)}"]
        if miss:
            parts.append(f"misspellings = {lua_list(miss)}")
        for k in ("size", "count", "power", "speed", "durability"):
            if k in m:
                parts.append(f"{k} = {fmt_num(m[k])}")
        if m.get("element") in ELEMENT:
            parts.append(f"element = {lua_str(m['element'])}")
        if m.get("mood") in MOODS:
            parts.append(f"mood = {lua_str(m['mood'])}")
        elif m.get("mood"):
            warn(f"modifiers.json: {mid!r} bad mood {m['mood']!r}")
        if m.get("motion") in MOTION:
            parts.append(f"motion = {lua_str(m['motion'])}")
        ac = []
        for a in m.get("ac") or []:
            if accents and a not in accents:
                warn(f"modifiers.json: {mid!r} unknown accent {a!r}; skipped")
            elif a not in ac:
                ac.append(a)
        if ac:
            parts.append(f"accents = {lua_list(ac)}")
        bs = [b for b in m.get("b") or [] if b in BEHAVIOUR]
        if bs:
            parts.append(f"addBehaviours = {lua_list(bs)}")
        ts = clean_tags(m.get("t"))
        if ts:
            parts.append(f"addTags = {lua_list(ts)}")
        for key, field in (("colour", "colour"), ("colour2", "colour2"), ("tint", "tint")):
            if m.get(key):
                parts.append(f"{field} = {lua_str('#' + hex6(m[key], 'FFFFFF'))}")
        lines.append("\t\t{ " + ", ".join(parts) + " },")
    lines.append("\t},")
    lines.append("}")
    return "\n".join(lines) + "\n", used


FAMILIES = ["Food", "Natural", "Manufactured", "Weird"]
CONSTRUCTIONS = ["Solid", "Strands", "Bricks", "Panels", "Wobble", "Swarm", "Shards", "Inflated", "Woven", "Pile", "Liquid", "Energy"]


def build_materials(mod_words):
    data = load_json("materials.json", {"materials": []})
    rows = data.get("materials") if isinstance(data, dict) else data
    rows = rows or []
    used = {}
    out = []
    overlaps = []
    for m in sorted(rows, key=lambda r: str(r.get("id", ""))):
        mid = clean_key(m.get("id"))
        if not mid:
            warn(f"materials.json: bad material {m.get('id')!r}")
            continue
        if mid in used:
            warn(f"materials.json: duplicate material {mid!r}; skipped")
            continue

        def take(words):
            keep = []
            for w in words:
                k = clean_key(w)
                if not k or k in keep:
                    continue
                if k in used:
                    if used[k] != mid:
                        warn(f"materials.json: word {k!r} of {mid!r} already used by {used[k]!r}; skipped")
                    continue
                used[k] = mid
                keep.append(k)
            return keep
        take([mid])
        aliases = take(m.get("aliases") or m.get("a") or [])
        miss = take(m.get("ms") or [])
        overlaps.extend(w for w in [mid] + aliases if w in mod_words)
        pal = ["#" + hex6(c, "9AA5B1") for c in (m.get("palette") or [])][:5] or ["#9AA5B1", "#E4E7EB"]
        hints = m.get("statHints") or {}
        hint_parts = []
        for k in ("power", "speed", "durability"):
            if isinstance(hints.get(k), (int, float)):
                hint_parts.append(f"{k} = {fmt_num(max(-3, min(3, hints[k])))}")
        fam = m.get("family") if m.get("family") in FAMILIES else "Weird"
        cons = m.get("construction") if m.get("construction") in CONSTRUCTIONS else "Solid"
        el = m.get("element") if m.get("element") in ELEMENT else "None"
        try:
            transp = max(0.0, min(0.95, float(m.get("transparency") or 0)))
            glow = max(0.0, min(1.0, float(m.get("glow") or 0)))
        except (TypeError, ValueError):
            transp, glow = 0.0, 0.0
        parts = [
            f"id = {lua_str(mid)}", f"family = {lua_str(fam)}", f"aliases = {lua_list(aliases)}",
            f"misspellings = {lua_list(miss)}", f"palette = {lua_list(pal)}",
            f"robloxMaterial = {lua_str(clean_text(m.get('robloxMaterial') or 'SmoothPlastic', 32))}",
            f"transparency = {fmt_num(transp)}", f"glow = {fmt_num(glow)}", f"construction = {lua_str(cons)}",
            f"particles = {lua_list([clean_text(x, 32) for x in (m.get('particles') or [])][:6])}",
            f"sound = {lua_str(clean_text(m.get('sound') or 'thud', 24).lower())}", f"element = {lua_str(el)}",
            f"tags = {lua_list(clean_tags(m.get('tags')))}",
            f"hooks = {lua_list([clean_text(x, 32) for x in (m.get('hooks') or [])][:8])}",
            "statHints = { " + ", ".join(hint_parts) + " }",
        ]
        out.append("\t{ " + ", ".join(parts) + " },")
    if overlaps:
        warn(f"materials.json: {len(overlaps)} material words are also modifier words (parser prefers the modifier"
             f" on a tie): {', '.join(sorted(overlaps)[:12])}{' ...' if len(overlaps) > 12 else ''}")
    lines = [
        "--!strict",
        "-- GENERATED by tools/build_library.py from data/materials.json. DO NOT EDIT. Types.Material records.",
        "return {",
    ] + out + ["}"]
    return "\n".join(lines) + "\n", len(out)


def build_protected():
    data = load_json("protected_names.json", {"names": [], "strip": []})
    rows = []
    for r in data.get("names", []):
        rep = clean_key(r.get("r"))
        if not rep:
            warn(f"protected_names.json: bad replacement in {r!r}")
            continue
        for n in r.get("n") or []:
            k = clean_key(n)
            if k:
                rows.append((k, rep))
    rows = sorted(dict(rows).items())
    strip = sorted({k for k in (clean_key(x) for x in data.get("strip", [])) if k})
    lines = [
        "--!strict",
        "-- GENERATED by tools/build_library.py from data/protected_names.json. DO NOT EDIT.",
        "-- Brand / franchise / real-person names -> generic replacement phrase; strip = words removed outright.",
        "return {",
        "\tnames = {",
    ]
    for k, rep in rows:
        lines.append(f"\t\t[{lua_str(k)}] = {lua_str(rep)},")
    lines += ["\t},", "\tstrip = " + lua_list(strip) + ",", "}"]
    return "\n".join(lines) + "\n"


def build_keyboard():
    with open(os.path.join(ROOT, "data", "keyboard.json"), encoding="utf-8") as fh:
        kb = json.load(fh)
    letters = "abcdefghijklmnopqrstuvwxyz0123456789"
    best = {}
    bands = sorted(kb["distanceBands"], key=lambda b: b["maxDistance"])
    for name in sorted(kb["layouts"]):
        lay = kb["layouts"][name]
        pos = {}
        for r, row in enumerate(lay["rows"]):
            for i, ch in enumerate(row["keys"]):
                pos[ch] = (row["offset"] + i, r * lay.get("rowScale", 1.0))
        for a in pos:
            for b in pos:
                if a == b:
                    continue
                d = math.dist(pos[a], pos[b])
                for band in bands:
                    if d <= band["maxDistance"] + 1e-9:
                        c = band["cost"] + lay.get("penalty", 0)
                        key = (a, b)
                        if c < best.get(key, 99):
                            best[key] = round(c, 3)
                        break
    for a, b, c in kb.get("similar", []):
        for key in ((a, b), (b, a)):
            if c < best.get(key, 99):
                best[key] = c
    pairs = []
    for a in letters:
        for b in letters:
            if (a, b) in best and best[(a, b)] < kb["costs"]["substitute"]:
                pairs.append((a, b, best[(a, b)]))
    lines = [
        "--!strict",
        "-- GENERATED by tools/build_library.py from data/keyboard.json. DO NOT EDIT.",
        "-- sub: \"ab\" -> cost for substituting typed a where b was meant (cheapest over all layouts).",
        "return {",
        "\tcosts = {",
    ]
    for k in sorted(kb["costs"]):
        lines.append(f"\t\t{k} = {fmt_num(kb['costs'][k])},")
    lines.append("\t},")
    lines.append("\tsub = {")
    row = []
    for a, b, c in pairs:
        row.append(f"{a}{b} = {fmt_num(c)}" if (a + b).isalpha() and not (a + b)[0].isdigit() else f"[{lua_str(a + b)}] = {fmt_num(c)}")
        if len(row) == 12:
            lines.append("\t\t" + ", ".join(row) + ",")
            row = []
    if row:
        lines.append("\t\t" + ", ".join(row) + ",")
    lines.append("\t},")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    check = "--check" in sys.argv
    quiet = "--quiet" in sys.argv
    files, stats = build()
    existing = set()
    if os.path.isdir(OUT_DIR):
        existing = {f for f in os.listdir(OUT_DIR) if f.endswith(".luau")}
    if check:
        stale = []
        for name, content in files.items():
            p = os.path.join(OUT_DIR, name)
            if not os.path.exists(p) or open(p, encoding="utf-8").read() != content:
                stale.append(name)
        stale += sorted(existing - set(files))
        if stale:
            print("Generated library is STALE: " + ", ".join(sorted(stale)[:10]) + (" ..." if len(stale) > 10 else ""))
            print("Run: python3 tools/build_library.py")
            sys.exit(1)
        print("Generated library is up to date (%d files)." % len(files))
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    for name in sorted(existing - set(files)):
        os.remove(os.path.join(OUT_DIR, name))
    total = 0
    for name, content in sorted(files.items()):
        p = os.path.join(OUT_DIR, name)
        data = content.encode("utf-8")
        total += len(data)
        old = open(p, "rb").read() if os.path.exists(p) else None
        if old != data:
            with open(p, "wb") as fh:
                fh.write(data)
    if not quiet:
        for msg in report[:60]:
            print("WARN", msg)
        if len(report) > 60:
            print(f"WARN ... {len(report) - 60} more")
        print(", ".join(f"{k}={v}" for k, v in stats.items()))
        print(f"wrote {len(files)} files, {total} bytes -> {os.path.relpath(OUT_DIR, ROOT)}")


if __name__ == "__main__":
    main()
