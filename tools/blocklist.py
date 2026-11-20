#!/usr/bin/env python3
"""Blocklist builder (hashes only, never commits plaintext).

    python3 tools/blocklist.py add <plaintext.txt>   # merge words into data/blocklist.txt + regen
    python3 tools/blocklist.py build                 # regen src/Server/BlocklistData.luau
    python3 tools/blocklist.py fold                  # regen src/Server/BlocklistFold.luau
    python3 tools/blocklist.py scan <words.txt>...   # print lines a current list would block (FP check)

Plaintext file format (keep it OUTSIDE the repo): one entry per line, `<set> <word>`, where set is
exact1 / exact2 / contains1 / contains2 (see src/Server/Blocklist.luau), `#` comments allowed.
Mirrors Blocklist.luau exactly: fold homoglyphs -> lowercase -> leet -> [a-z]+ tokens -> collapse.
"""
import re, sys, os, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "blocklist.txt")
OUT = os.path.join(ROOT, "src", "Server", "BlocklistData.luau")
SETS = ("exact1", "exact2", "contains1", "contains2", "allow")

LEET = {"0": "o", "1": "i", "2": "z", "3": "e", "4": "a", "5": "s", "6": "g", "7": "t", "8": "b", "9": "g",
        "@": "a", "$": "s", "!": "i", "|": "l", "+": "t"}

def _load_fold():
    # same table as src/Server/BlocklistFold.luau (generated from here)
    path = os.path.join(ROOT, "src", "Server", "BlocklistFold.luau")
    m = {}
    if os.path.exists(path):
        for k, v in re.findall(r'\["([^"]+)"\] = "([a-z]+)"', open(path, encoding="utf-8").read()):
            m[k] = v
    return m

FOLD = _load_fold()

def fold(text):
    out = []
    for ch in text:
        out.append(FOLD.get(ch, ch))
    return "".join(out)

def collapse(s, keep):
    out, last, run = [], "", 0
    for c in s:
        if c == last:
            run += 1
        else:
            last, run = c, 1
        if run <= keep:
            out.append(c)
    return "".join(out)

def tokens(text, keep):
    t = fold(text)
    lower = "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in t)
    mapped = "".join(LEET.get(c, c) for c in lower).replace("€", "e")
    return [collapse(w, keep) for w in re.findall(r"[a-z]+", mapped)]

def skeleton(text, keep):
    return collapse("".join(tokens(text, keep)), keep)

M32 = 4294967296
def fnv(s, basis):
    h = basis
    for b in s.encode("utf-8"):
        h ^= b
        h = ((h << 24) + h * 403) % M32
    return h

def hsh(s):
    return "%08x%08x" % (fnv(s, 2166136261), fnv(s, 3735928559))

def read_data():
    entries = set()
    header = []
    maxlen = 12
    for line in open(DATA, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("#") or not line.strip():
            if line.startswith("# maxLen "):
                maxlen = int(line.split()[2])
            elif line.startswith("#"):
                header.append(line)
            continue
        s, h = line.split()
        entries.add((s, h))
    return header, entries, maxlen

def write_data(header, entries, maxlen):
    with open(DATA, "w", encoding="utf-8") as f:
        for l in header:
            f.write(l + "\n")
        f.write("# maxLen %d\n" % maxlen)
        for s, h in sorted(entries):
            f.write("%s %s\n" % (s, h))

def build():
    _, entries, maxlen = read_data()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("--!strict\n-- GENERATED from data/blocklist.txt by tools/blocklist.py. Hashes only; see Blocklist.luau. Do not edit by hand.\n")
        f.write("return {\n\tmaxLen = %d,\n" % maxlen)
        for s in SETS:
            f.write("\t%s = {\n" % s)
            for h in sorted(h for (ss, h) in entries if ss == s):
                f.write('\t\t"%s",\n' % h)
            f.write("\t},\n")
        f.write("}\n")
    print("wrote %s (%d hashes, maxLen %d)" % (OUT, len(entries), maxlen))

def parse_plain(path):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        s, w = line.split(None, 1)
        assert s in SETS, line
        out.append((s, w.strip()))
    return out

def add(path):
    header, entries, maxlen = read_data()
    n0 = len(entries)
    for s, w in parse_plain(path):
        keep = 1 if s == "allow" else int(s[-1])
        sk = skeleton(w, keep)
        if not sk:
            continue
        if s.startswith("contains"):
            maxlen = max(maxlen, len(sk))
        entries.add((s, hsh(sk)))
    write_data(header, entries, maxlen)
    print("added %d new hashes (%d total)" % (len(entries) - n0, len(entries)))
    build()

def load_sets():
    _, entries, maxlen = read_data()
    sets = {s: set() for s in SETS}
    for s, h in entries:
        sets[s].add(h)
    return sets, maxlen

def blocked(text, sets, maxlen):
    if hsh(skeleton(text, 1)) in sets["allow"]:
        return None
    for keep in (1, 2):
        exact, contains = sets["exact%d" % keep], sets["contains%d" % keep]
        toks = tokens(text, keep)
        for t in toks:
            if hsh(t) in exact:
                return "exact%d:%s" % (keep, t)
        whole = collapse("".join(toks), keep)
        if not whole:
            continue
        if hsh(whole) in exact:
            return "exact%d:%s" % (keep, whole)
        n = len(whole)
        for i in range(n):
            for j in range(i + 2, min(n, i + maxlen - 1) + 1):
                if hsh(whole[i:j + 1]) in contains:
                    return "contains%d:%s" % (keep, whole[i:j + 1])
    return None

def scan(paths):
    sets, maxlen = load_sets()
    hits = 0
    for p in paths:
        for line in open(p, encoding="utf-8"):
            w = line.strip()
            if w and not w.startswith("#"):
                why = blocked(w, sets, maxlen)
                if why:
                    hits += 1
                    print("%s\t%s" % (w, why))
    print("-- %d blocked" % hits, file=sys.stderr)

# ---- homoglyph fold table -------------------------------------------------------------------
MANUAL = {
    # Cyrillic lookalikes
    "а": "a", "в": "b", "е": "e", "ё": "e", "з": "z", "и": "u", "й": "u", "і": "i", "ї": "i", "ј": "j", "к": "k",
    "л": "n", "м": "m", "н": "h", "о": "o", "п": "n", "р": "p", "с": "c", "т": "t", "у": "y", "ф": "f",
    "х": "x", "ц": "u", "ч": "y", "ш": "w", "щ": "w", "ъ": "b", "ы": "bi", "ь": "b", "э": "e", "ю": "io",
    "я": "r", "ѕ": "s", "ԁ": "d", "ԛ": "q", "ԝ": "w", "һ": "h", "ӏ": "l", "ɡ": "g", "ɑ": "a",
    # Greek lookalikes
    "α": "a", "β": "b", "γ": "y", "δ": "d", "ε": "e", "ζ": "z", "η": "n", "θ": "o", "ι": "i", "κ": "k",
    "λ": "l", "μ": "u", "ν": "v", "ξ": "e", "ο": "o", "π": "n", "ρ": "p", "σ": "o", "ς": "c", "τ": "t",
    "υ": "u", "φ": "f", "χ": "x", "ψ": "y", "ω": "w",
    # letters NFKD can't split
    "ß": "ss", "æ": "ae", "œ": "oe", "ø": "o", "đ": "d", "ð": "d", "ħ": "h", "ı": "i", "ł": "l",
    "ŀ": "l", "ŧ": "t", "þ": "p", "ƒ": "f", "ʋ": "u", "ʏ": "y", "ʀ": "r", "ɪ": "i", "ɴ": "n",
    "ᴀ": "a", "ʙ": "b", "ᴄ": "c", "ᴅ": "d", "ᴇ": "e", "ꜰ": "f", "ɢ": "g", "ʜ": "h", "ᴊ": "j", "ᴋ": "k",
    "ʟ": "l", "ᴍ": "m", "ᴏ": "o", "ᴘ": "p", "ꞯ": "q", "ꜱ": "s", "ᴛ": "t", "ᴜ": "u", "ᴠ": "v", "ᴡ": "w", "ᴢ": "z",
    "¡": "i", "€": "e", "£": "l", "¥": "y", "§": "s", "©": "c", "®": "r", "µ": "u", "×": "x",
}

def fold_table():
    m = {}
    ranges = [(0x00C0, 0x024F), (0x0370, 0x03FF), (0x0400, 0x04FF), (0x1D00, 0x1D7F), (0x1E00, 0x1EFF),
              (0x24B6, 0x24E9), (0xFF01, 0xFF5E), (0xA720, 0xA7FF), (0x00A1, 0x00BF)]
    for lo, hi in ranges:
        for cp in range(lo, hi + 1):
            ch = chr(cp)
            low = ch.lower()
            v = MANUAL.get(ch) or MANUAL.get(low)
            if v is None:
                d = unicodedata.normalize("NFKD", ch)
                base = "".join(c for c in d if ord(c) < 128).lower()
                if base and (base.isalpha() or (len(base) == 1 and base in LEET)):
                    v = "".join(LEET.get(c, c) for c in base)
            if v and re.fullmatch(r"[a-z]+", v):
                m[ch] = v
    for k, v in MANUAL.items():
        if re.fullmatch(r"[a-z]+", v):
            m[k] = v
            m[k.upper()] = m.get(k.upper(), v) if k.upper() != k else v
    return m

def gen_fold():
    m = fold_table()
    path = os.path.join(ROOT, "src", "Server", "BlocklistFold.luau")
    with open(path, "w", encoding="utf-8") as f:
        f.write("--!strict\n-- GENERATED by tools/blocklist.py fold. Lookalike / accented / fullwidth letters -> ASCII, so\n")
        f.write("-- \"фуск\"-style homoglyph spellings and \"fück\" hit the same blocklist hashes. Do not edit by hand.\n")
        f.write("return {\n")
        for k in sorted(m):
            f.write('\t["%s"] = "%s",\n' % (k, m[k]))
        f.write("}\n")
    print("wrote %s (%d glyphs)" % (path, len(m)))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "add":
        add(sys.argv[2])
    elif cmd == "build":
        build()
    elif cmd == "scan":
        scan(sys.argv[2:])
    elif cmd == "fold":
        gen_fold()
    else:
        print(__doc__)

