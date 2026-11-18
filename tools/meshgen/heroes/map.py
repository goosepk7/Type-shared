#!/usr/bin/env python3
"""Word -> hero model mapping. Writes src/Shared/Summon/Heroes/Map.luau and prints coverage.

  python3 tools/meshgen/heroes/map.py [--report out.md] [--show hero]

RULES: (hero id, keywords, filter). A keyword matches a whole word or a run of words of the library id
("snow leopard"). Words are tried from the END of the id first ("tiger shark" -> shark before tiger), longest
keyword first. filter limits a rule to body plans ("bp") and / or categories ("cat"), so "hot dog" (Food) never
becomes a dog and "cat burglar" (Person) never becomes a cat. The same rules ship to the runtime (Map.match) for
words the library does not have yet (AI-resolved words), and every library word is resolved here once and written
as an exact entry (Map.words), so the shipped mapping is reviewable in the diff.
"""
import argparse, collections, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = os.path.join(ROOT, "src/Shared/Summon/Heroes/Map.luau")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

ANIMAL = {"bp": ["Quadruped", "Biped", "Bird", "Fish", "Serpent", "Insect", "Spider", "Crab", "Worm", "Turtle", "Octopus", "Swarm", "Blob", "Humanoid", "Dragon", "Giant", "Ghost"],
          "cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Person", "Plant", "Structure", "Weather"]}
NOTFOOD = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Plant", "Weather", "Structure", "Vehicle"]}
VEH = {"cat": ["Vehicle", "Machine", "Object"]}

# (hero, keywords, filter)
RULES = []  # family files contribute MAP lists


def load_words():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data/words/*.jsonl"))):
        for line in open(f):
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def tokens(s):
    return [t for t in re.split(r"[^a-z0-9]+", s.lower()) if t]


# words that may follow the creature noun without changing what it is ("lion cub", "tiger king")
TRAIL = set("cub cubs pup pups baby babies king queen lord lady monster beast spirit god goddess familiar prime alpha elder "
            "guardian warrior mount steed of the night storm".split())


def ends_ok(t, end):
    return all(x in TRAIL for x in t[end:])


def match(id_, bp, cat, rules):
    t = tokens(id_)
    best = None
    for hero, words, flt in rules:
        if any(" ".join(t).find(x) >= 0 for x in NOT.get(hero, [])):
            continue
        for kwd in PHRASES[hero]:
            k = kwd.split(" ")
            n = len(k)
            for end in range(len(t), n - 1, -1):
                if t[end - n:end] == k and ends_ok(t, end):
                    ok = True
                    if flt:
                        if "bp" in flt and bp and bp not in flt["bp"]:
                            ok = False
                        if "cat" in flt and cat and cat not in flt["cat"]:
                            ok = False
                    if ok:
                        score = (end, n)  # later in the id first, then longer phrase
                        if best is None or score > best[0]:
                            best = (score, hero)
    return best[1] if best else None


PHRASES = {}
NOT = {}


def build_phrases(rules):
    """A rule's text is a comma-separated list of phrases ("snow leopard, ounce")."""
    for hero, text, flt in rules:
        ph = PHRASES.setdefault(hero, [hero])
        items = [x.strip().lower() for x in text.split(",") if x.strip()]
        ph.extend(x for x in items if not x.startswith("!"))
        NOT.setdefault(hero, []).extend(x[1:] for x in items if x.startswith("!"))
        PHRASES[hero] = sorted(set(ph), key=lambda s: (-len(s.split()), -len(s)))


def all_rules():
    rules = list(RULES)
    for m in sorted(glob.glob(os.path.join(HERE, "h_*.py"))):
        mod = __import__(os.path.basename(m)[:-3])
        rules.extend(getattr(mod, "MAP", []))
    return rules


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="")
    ap.add_argument("--show", default="")
    a = ap.parse_args()
    import kit

    rules = all_rules()
    for m in sorted(glob.glob(os.path.join(HERE, "h_*.py"))):
        __import__(os.path.basename(m)[:-3])
    known = set(kit.REG)
    rules = [r for r in rules if r[0] in known]
    build_phrases(rules)
    words = load_words()
    exact = {}
    for w in words:
        hid = match(w["w"], w.get("bp"), w.get("c"), rules)
        if hid:
            exact[w["w"].lower()] = hid
    cnt = collections.Counter(exact.values())
    shapes = collections.Counter()
    for w in words:
        if w["w"].lower() in exact:
            shapes[w.get("s")] += 1
    print(f"{len(exact)} library words map to {len(cnt)} heroes; by shape: {dict(shapes)}")
    if a.show:
        print(sorted(k for k, v in exact.items() if v == a.show))
    # runtime rules: phrases per hero + filters
    L = ["--!strict", "-- GENERATED by tools/meshgen/heroes/map.py. Do not edit: change the RULES / MAP lists there.",
         "-- words: every library word id -> hero id. match(id, result): the same keyword rules for words not in the library.",
         "local Map = {}", "", "Map.words = {"]
    for k in sorted(exact):
        L.append(f"\t[{json.dumps(k)}] = {json.dumps(exact[k])},")
    L.append("} :: { [string]: string }")
    L.append("")
    L.append("-- { hero, phrases (longest first), plans?, categories? }")
    L.append("Map.rules = {")
    for hero, text, flt in rules:
        ph = ", ".join(json.dumps(p) for p in PHRASES[hero])
        bp = ", ".join(json.dumps(x) for x in (flt or {}).get("bp", []))
        cat = ", ".join(json.dumps(x) for x in (flt or {}).get("cat", []))
        nots = ", ".join(json.dumps(x) for x in NOT.get(hero, []))
        L.append(f"\t{{ {json.dumps(hero)}, {{ {ph} }}, {{ {bp} }}, {{ {cat} }}, {{ {nots} }} }},")
    L.append("} :: { any }")
    L.append("""
local TRAIL: { [string]: boolean } = {}
for w in string.gmatch("TRAILWORDS", "%a+") do
	TRAIL[w] = true
end

local function split(s: string): { string }
	local out = {}
	for w in string.gmatch(string.lower(s), "[%a%d]+") do
		table.insert(out, w)
	end
	return out
end

local function allowed(list: { string }, v: string?): boolean
	if #list == 0 or v == nil then
		return true
	end
	return table.find(list, v) ~= nil
end

function Map.match(id: string, r: any): string?
	local t = split(id)
	local bp = r and r.visual and r.visual.bodyPlan
	local cat = r and r.category
	local joined = table.concat(t, " ")
	local bestEnd, bestLen, best = -1, -1, nil
	for _, rule in Map.rules do
		local banned = false
		for _, x in rule[5] do
			if string.find(joined, x, 1, true) then
				banned = true
			end
		end
		if not banned and allowed(rule[3], bp) and allowed(rule[4], cat) then
			for _, phrase in rule[2] do
				local k = split(phrase)
				local n = #k
				for e = #t, n, -1 do
					local hit = true
					for j = 1, n do
						if t[e - n + j] ~= k[j] then
							hit = false
							break
						end
					end
					for j = e + 1, #t do
						if not TRAIL[t[j]] then
							hit = false
						end
					end
					if hit then
						if e > bestEnd or (e == bestEnd and n > bestLen) then
							bestEnd, bestLen, best = e, n, rule[1]
						end
						break
					end
				end
			end
		end
	end
	return best
end

return Map""")
    with open(OUT, "w") as f:
        f.write("\n".join(L).replace("TRAILWORDS", " ".join(sorted(TRAIL))) + "\n")
    print("wrote", OUT)
    if a.report:
        with open(a.report, "w") as f:
            for h, n in cnt.most_common():
                f.write(f"{h}: {n}\n")


if __name__ == "__main__":
    main()
