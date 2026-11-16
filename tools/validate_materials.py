#!/usr/bin/env python3
"""Validate data/materials.json (Types.Material records, see DESIGN.md §8 and docs/MATERIALS.md).

Usage: python3 tools/validate_materials.py [--stats] [--words]
  --stats  print counts by family / construction / element / robloxMaterial / hook usage
  --words  also report material words that are word-library ids/aliases (informational; expected by design:
           "cheese" alone is the thing, "cheese tank" uses the material)

Exit code 1 on any error. Overlaps with data/modifiers.json are REPORTED, never errors (the phrase parser
decides by context; tools/build_library.py warns about them too).
"""
import json, re, sys, os, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "materials.json")

HEX = re.compile(r"^#[0-9A-F]{6}$")
# Same rule as tools/build_library.py WORD_RE (clean_key): words that fail it are silently dropped by the compiler.
WORD = re.compile(r"^[a-z0-9][a-z0-9 '\-]*[a-z0-9]$|^[a-z0-9]$")
MAX_ID = 24  # Schema.luau clamps WordResult.material to 24 chars

FAMILIES = {"Food", "Natural", "Manufactured", "Weird"}
CONSTRUCTIONS = {"Solid", "Strands", "Bricks", "Panels", "Wobble", "Swarm", "Shards", "Inflated", "Woven", "Pile",
                 "Liquid", "Energy"}
ELEMENTS = {"Fire", "Water", "Ice", "Lightning", "Earth", "Wind", "Nature", "Light", "Shadow", "Poison", "Metal",
            "Arcane", "None"}
# Enum.Material values usable on BaseParts (verified against the live API dump / create.roblox.com 2026-11).
# Air and Water exist in the enum but are terrain-only and are rejected here.
ROBLOX_MATERIALS = {
    "Plastic", "SmoothPlastic", "Neon", "Wood", "WoodPlanks", "Marble", "Basalt", "Slate", "CrackedLava", "Concrete",
    "Limestone", "Granite", "Pavement", "Brick", "Pebble", "Cobblestone", "Rock", "Sandstone", "CorrodedMetal",
    "DiamondPlate", "Foil", "Metal", "Grass", "LeafyGrass", "Sand", "Fabric", "Snow", "Mud", "Ground", "Asphalt",
    "Salt", "Ice", "Glacier", "Glass", "ForceField", "Cardboard", "Carpet", "CeramicTiles", "ClayRoofTiles",
    "RoofShingles", "Leather", "Plaster", "Rubber",
}
# Canonical Effects-library particle ids (coordinator list). Particles are tinted by the material palette.
PARTICLES = {
    "drip_sauce", "drip_honey", "goo_drip", "water_drip", "ink_drip", "sawdust", "crumbs", "sprinkles", "sparkle",
    "glitter", "confetti", "bees", "flies", "butterflies", "shards", "steam", "smoke", "embers", "sparks", "zap",
    "frost", "snowflakes", "bubbles", "petals", "leaves", "feathers", "fluff", "sand", "dust", "coins", "music_notes",
    "hearts", "snore", "anger_steam", "sweat_drops", "thruster", "glitch", "rainbow_trail", "stars", "question_marks",
    "halo_glow",
}
# Summon-builder accent ids (optional "accents" key).
ACCENTS = {
    "scowl", "frown", "smile", "grin", "smirk", "tongue", "drool", "snore", "sweat", "tears", "blush", "steam",
    "sparkle", "glitter", "halo", "horns", "crown", "partyhat", "tophat", "piratehat", "wizardhat", "chefhat",
    "eyepatch", "monocle", "sunglasses", "mustache", "bowtie", "crack", "bandage", "stitches", "bolts", "gears",
    "thrusters", "jetpack", "wings", "propeller", "laser", "cannon", "armour", "shield", "spikes", "fangs", "flames",
    "frost", "sparks", "drip", "slime", "bubbles", "rainbow", "glow", "ghostly", "zombie", "skeleton", "visor",
    "pixel", "disco", "cursed", "stars", "question", "extrahead", "extraheads", "lightning", "leaves", "petals",
    "hearts", "notes",
}
SOUNDS = {
    "squelch", "clank", "crinkle", "crunch", "boing", "buzz", "slosh", "shatter", "rustle", "thud", "sizzle",
    "jingle", "squeak", "squish", "pop", "hiss", "crackle", "creak", "chime", "whoosh", "flutter", "rattle", "slurp",
    "snap", "rumble", "hum", "blip", "moan", "rip", "splat", "tick", "click", "boom", "melody", "whisper", "clack",
    "gong", "poof", "flop", "scratch", "skitter", "chatter",
}
# Reaction tags (data/material_reactions.json keys on these) + descriptive tags.
REACTION_TAGS = {"flammable", "edible", "meltable", "conductive", "absorbent", "brittle", "frozen", "sticky", "liquid",
                 "metal", "wood", "paper", "plastic", "rubber", "glass", "stone", "cloth", "organic", "living"}
TAGS = REACTION_TAGS | {
    "bouncy", "heavy", "light", "transparent", "shiny", "soft", "hot", "cold", "magnetic", "slippery", "smelly",
    "loud", "holy", "cursed", "sweet", "savory", "sour", "crunchy", "sharp", "spooky", "cute", "silly", "lucky",
    "glowing", "magic", "hard", "fancy", "gross", "healthy", "flaky", "durable", "explosive", "toxic",
}
HOOKS = {
    "Bounces", "ShattersOnHit", "EdibleLure", "BurnsFast", "Durable", "Slow", "Fast", "DamageAura", "Conductive",
    "Tangles", "Sticky", "Slippery", "Heals", "Reflects", "Floats", "Melts", "Absorbs", "Explodes", "Regenerates",
    "Blinds", "Distracts", "Light", "Heavy",
    # extensions documented in docs/MATERIALS.md
    "Splits", "Phases", "Lucky", "Poisons", "Scares", "Pulls",
}
KEYS_REQ = ["id", "family", "aliases", "palette", "robloxMaterial", "transparency", "glow", "construction",
            "particles", "sound", "element", "tags", "hooks", "statHints", "ms"]
KEYS_OPT = {"accents"}
BANNED = {"lego", "legos", "lego bricks", "styrofoam", "play doh", "playdoh", "play-doh", "slinky", "velcro",
          "post-it", "post it", "super ball", "superball", "cheerios", "jell o"}


def load_modifier_words():
    p = os.path.join(ROOT, "data", "modifiers.json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p, encoding="utf-8"))
    out = {}
    for m in d.get("modifiers", []):
        for w in [m.get("id")] + list(m.get("a") or []):
            if isinstance(w, str):
                out[w.strip().lower()] = f"{m.get('kind')}:{m.get('id')}"
    return out


def load_word_library():
    out = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "words", "*.jsonl"))):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            for w in [e.get("w")] + list(e.get("a") or []):
                if isinstance(w, str):
                    out[w.lower()] = e.get("w")
    return out


def main():
    stats = "--stats" in sys.argv
    errors, warns = [], []
    try:
        data = json.load(open(PATH, encoding="utf-8"))
    except Exception as ex:  # noqa: BLE001
        print(f"ERROR: cannot parse {PATH}: {ex}")
        return 1
    rows = data.get("materials") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        print("ERROR: materials.json must be an array (or {materials: [...]})")
        return 1

    owner = {}  # word -> (material id, role)

    def claim(word, mid, role):
        if not isinstance(word, str) or not WORD.match(word):
            errors.append(f"{mid}: {role} {word!r} is not a clean lowercase word (build_library would drop it)")
            return
        if word in BANNED:
            errors.append(f"{mid}: {role} {word!r} is a banned brand/trademark word")
        prev = owner.get(word)
        if prev and prev[0] != mid:
            errors.append(f"{mid}: {role} {word!r} collides with {prev[1]} of {prev[0]!r}")
        elif prev:
            errors.append(f"{mid}: {role} {word!r} repeated inside the same material (already its {prev[1]})")
        else:
            owner[word] = (mid, role)

    for i, m in enumerate(rows):
        if not isinstance(m, dict):
            errors.append(f"row {i}: not an object")
            continue
        mid = m.get("id", f"<row {i}>")
        for k in KEYS_REQ:
            if k not in m:
                errors.append(f"{mid}: missing key {k!r}")
        for k in m:
            if k not in KEYS_REQ and k not in KEYS_OPT:
                errors.append(f"{mid}: unknown key {k!r}")
        if not isinstance(mid, str) or len(mid) > MAX_ID:
            errors.append(f"{mid}: id must be a string <= {MAX_ID} chars (Schema clamps WordResult.material)")
        claim(mid, mid, "id")
        if m.get("family") not in FAMILIES:
            errors.append(f"{mid}: family {m.get('family')!r}")
        al = m.get("aliases")
        if not isinstance(al, list):
            errors.append(f"{mid}: aliases must be a list")
            al = []
        for a in al:
            claim(a, mid, "alias")
        ms = m.get("ms")
        if not isinstance(ms, list) or not 1 <= len(ms) <= 4:
            errors.append(f"{mid}: ms must list 1-4 misspellings")
            ms = ms if isinstance(ms, list) else []
        for w in ms:
            claim(w, mid, "misspelling")
        pal = m.get("palette")
        if not isinstance(pal, list) or not 2 <= len(pal) <= 5:
            errors.append(f"{mid}: palette must have 2-5 colours")
        else:
            for c in pal:
                if not isinstance(c, str) or not HEX.match(c):
                    errors.append(f"{mid}: bad hex colour {c!r} (want #RRGGBB uppercase)")
            if len(set(pal)) != len(pal):
                errors.append(f"{mid}: duplicate palette colour")
        if m.get("robloxMaterial") not in ROBLOX_MATERIALS:
            errors.append(f"{mid}: robloxMaterial {m.get('robloxMaterial')!r} is not a BasePart Enum.Material name")
        for k, hi in (("transparency", 0.95), ("glow", 1.0)):
            v = m.get(k)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 <= v <= hi:
                errors.append(f"{mid}: {k} {v!r} out of 0..{hi}")
        if m.get("construction") not in CONSTRUCTIONS:
            errors.append(f"{mid}: construction {m.get('construction')!r}")
        parts = m.get("particles")
        if not isinstance(parts, list) or not 1 <= len(parts) <= 3:
            errors.append(f"{mid}: particles must list 1-3 effect ids (summon budget is 2-3 emitters)")
        else:
            for p in parts:
                if p not in PARTICLES:
                    errors.append(f"{mid}: unknown particle id {p!r}")
            if len(set(parts)) != len(parts):
                errors.append(f"{mid}: duplicate particle")
        if m.get("sound") not in SOUNDS:
            errors.append(f"{mid}: sound {m.get('sound')!r} not in sound key list")
        if m.get("element") not in ELEMENTS:
            errors.append(f"{mid}: element {m.get('element')!r}")
        tags = m.get("tags")
        if not isinstance(tags, list) or not 1 <= len(tags) <= 8:
            errors.append(f"{mid}: tags must list 1-8 (compiler keeps 8)")
        else:
            for t in tags:
                if t not in TAGS:
                    errors.append(f"{mid}: unknown tag {t!r}")
            if len(set(tags)) != len(tags):
                errors.append(f"{mid}: duplicate tag")
            if not set(tags) & REACTION_TAGS and not {"light", "magic", "cursed", "spooky", "hot", "cold"} & set(tags):
                warns.append(f"{mid}: no reaction tag (material x element reactions will ignore it)")
        hooks = m.get("hooks")
        if not isinstance(hooks, list) or not 1 <= len(hooks) <= 4:
            errors.append(f"{mid}: hooks must list 1-4")
        else:
            for h in hooks:
                if h not in HOOKS:
                    errors.append(f"{mid}: unknown hook {h!r}")
            if len(set(hooks)) != len(hooks):
                errors.append(f"{mid}: duplicate hook")
            if "Light" in hooks and "Heavy" in hooks:
                errors.append(f"{mid}: hooks Light and Heavy contradict")
        sh = m.get("statHints")
        if not isinstance(sh, dict):
            errors.append(f"{mid}: statHints must be an object")
        else:
            for k, v in sh.items():
                if k not in ("power", "speed", "durability"):
                    errors.append(f"{mid}: statHints key {k!r}")
                elif not isinstance(v, int) or isinstance(v, bool) or not -2 <= v <= 2 or v == 0:
                    errors.append(f"{mid}: statHints.{k} {v!r} must be a non-zero int in -2..2 (omit zero)")
            if sum(sh.values()) > 2:
                errors.append(f"{mid}: statHints sum {sum(sh.values())} > 2 (materials are flavour, not upgrades)")
        acc = m.get("accents")
        if acc is not None:
            if not isinstance(acc, list) or len(acc) > 3:
                errors.append(f"{mid}: accents must be a list of <= 3")
            else:
                for a in acc:
                    if a not in ACCENTS:
                        errors.append(f"{mid}: unknown accent {a!r}")
        if m.get("construction") == "Energy" and (m.get("glow") or 0) < 0.3:
            warns.append(f"{mid}: Energy construction with low glow")
        if m.get("robloxMaterial") == "Neon" and (m.get("glow") or 0) < 0.5:
            warns.append(f"{mid}: Neon material with glow < 0.5")

    ids = [m.get("id") for m in rows if isinstance(m, dict)]
    if len(ids) < 150:
        errors.append(f"only {len(ids)} materials (need >= 150)")
    fam = collections.Counter(m.get("family") for m in rows if isinstance(m, dict))
    for f in FAMILIES:
        if fam[f] < 25:
            errors.append(f"family {f} has only {fam[f]} materials (need >= 25)")

    # Overlaps with modifier words (report only).
    mods = load_modifier_words()
    overlaps = []
    if mods is not None:
        for w, (mid, role) in sorted(owner.items()):
            if role != "misspelling" and w in mods:
                overlaps.append(f"{w!r} ({role} of {mid}) = modifier {mods[w]}")
            elif role == "misspelling" and w in mods:
                errors.append(f"misspelling {w!r} of {mid} is a modifier word {mods[w]}")

    for e in errors:
        print("ERROR:", e)
    for w in warns:
        print("WARN:", w)
    print(f"materials: {len(ids)}  " + "  ".join(f"{k}={fam[k]}" for k in sorted(FAMILIES)) +
          f"  words claimed: {len(owner)}")
    if mods is None:
        print("modifier overlap check skipped (data/modifiers.json missing)")
    else:
        print(f"modifier-word overlaps (report only, parser decides by context): {len(overlaps)}")
        for o in overlaps:
            print("  OVERLAP:", o)
    if "--words" in sys.argv:
        lib = load_word_library()
        hits = sorted((w, mid, lib[w]) for w, (mid, role) in owner.items() if w in lib)
        print(f"word-library overlaps (expected, informational): {len(hits)}")
        for w, mid, e in hits:
            print(f"  {w!r} ({mid}) = word {e!r}")
    if stats:
        for key in ("construction", "element", "robloxMaterial", "sound"):
            c = collections.Counter(m.get(key) for m in rows)
            print(f"{key}: " + ", ".join(f"{k}={v}" for k, v in c.most_common()))
        for key in ("hooks", "particles", "tags"):
            c = collections.Counter(x for m in rows for x in m.get(key, []))
            print(f"{key}: " + ", ".join(f"{k}={v}" for k, v in c.most_common()))
    print("OK" if not errors else f"FAILED: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
