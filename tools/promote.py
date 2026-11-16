#!/usr/bin/env python3
"""Promote AI-generated words from the live games into the curated library (offline tool).

Reads, via the Roblox Open Cloud v2 DataStore API:
  * DataStore        WordEngine_WordCache_v1   keys "w1:<phrase>"  (both universes)
  * OrderedDataStore WordEngine_Unknown_v1     scope "global"      (fallback phrases + counts)
  * OrderedDataStore WordEngine_AIWordPlays_v1 scope "global"      (AI word play counts, optional)
merges them, flags conflicts and popular new phrases, and writes
  * data/promotion/candidates.json   every merged candidate with status + reasons (review this)
  * data/promotion/report.md         coverage report (unknown phrases the library still misses, etc.)
  * data/words/promoted_NN.jsonl     ONLY with --write: approved entries in the library short-key format

Approval: entries listed in --approve FILE (one phrase per line), and/or every clean candidate with
>= --min-plays plays across both games. Conflicting, refused, mock and library-colliding entries are
never auto-approved.

Auth: if ROBLOX_OPEN_CLOUD_KEY is set it is sent as x-api-key (scopes: universe-datastores.objects:list,
universe-datastores.objects:read, universe.ordered-data-store.scope.entry:read on both universes).
Inside the Claude Code environment the egress proxy authenticates apis.roblox.com, so no key is needed.
The key is never printed or written anywhere.

Offline/testing: --fixture DIR reads <DIR>/<universe>.json shaped like
  {"WordEngine_WordCache_v1": {"w1:foo": {...record...}}, "WordEngine_Unknown_v1": {"foo": 3},
   "WordEngine_AIWordPlays_v1": {"foo": 9}}

Usage:
  python3 tools/promote.py                       # pull live, write candidates + report
  python3 tools/promote.py --min-plays 25 --write
  python3 tools/promote.py --approve approved.txt --write
  python3 tools/promote.py --fixture tests/fixtures/promote --out-dir /tmp/x
"""
import argparse, glob, json, os, re, ssl, sys, time, urllib.error, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import BEHAVIOUR, BODYPLAN, CATEGORY, ELEMENT, MOTION, SHAPE, SIZE  # noqa: E402

GAMES = {"Defend": 10777140395, "Wizard": 10777140284}
CACHE_STORE = "WordEngine_WordCache_v1"
UNKNOWN_STORE = "WordEngine_Unknown_v1"
PLAYS_STORE = "WordEngine_AIWordPlays_v1"
API = "https://apis.roblox.com/cloud/v2/universes/{u}"
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
WORD = re.compile(r"^[a-z0-9][a-z0-9 '\-]*[a-z0-9]$|^[a-z0-9]$")
CONFLICT_FIELDS = ("category", "element", "size", "shape")


# --------------------------------------------------------------------------------------------- HTTP
class NotAuthorized(Exception):
    pass


class OpenCloud:
    def __init__(self, universe, verbose=False):
        self.base = API.format(u=universe)
        self.key = os.environ.get("ROBLOX_OPEN_CLOUD_KEY") or None
        self.verbose = verbose
        cafile = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
        if not cafile and os.path.exists("/root/.ccr/ca-bundle.crt"):
            cafile = "/root/.ccr/ca-bundle.crt"
        self.ctx = ssl.create_default_context(cafile=cafile) if cafile else ssl.create_default_context()
        self.calls = 0

    def get(self, path, params=None):
        url = self.base + path + ("?" + urllib.parse.urlencode(params) if params else "")
        headers = {"Accept": "application/json"}
        if self.key:
            headers["x-api-key"] = self.key
        for attempt in range(5):
            self.calls += 1
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, context=self.ctx, timeout=30) as r:
                    body = r.read().decode("utf-8")
                    return json.loads(body) if body else {}
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                if e.code in (429, 500, 502, 503, 504) and attempt < 4:
                    wait = float(e.headers.get("Retry-After") or 2 ** attempt)
                    time.sleep(min(wait, 30))
                    continue
                detail = e.read().decode("utf-8", "replace")[:300].strip()
                if e.code in (401, 403):
                    raise NotAuthorized(f"Open Cloud {e.code} on {path}: {detail}")
                raise SystemExit(f"Open Cloud {e.code} on {path}: {detail}")
            except urllib.error.URLError as e:
                if attempt < 4:
                    time.sleep(2 ** attempt)
                    continue
                raise SystemExit(f"Open Cloud unreachable ({e.reason})")
        return None

    def list_entry_ids(self, store, prefix=None, limit=None):
        ids, token = [], None
        while True:
            params = {"maxPageSize": 256}
            if prefix:
                params["filter"] = f'id.startsWith("{prefix}")'
            if token:
                params["pageToken"] = token
            page = self.get(f"/data-stores/{urllib.parse.quote(store, safe='')}/entries", params) or {}
            for e in page.get("dataStoreEntries", []):
                ids.append(e.get("id") or e.get("path", "").rsplit("/", 1)[-1])
                if limit and len(ids) >= limit:
                    return ids
            token = page.get("nextPageToken")
            if not token:
                return ids

    def get_entry(self, store, entry_id):
        # "@" in an entry id selects a revision; "@latest" makes ids containing "@" unambiguous.
        eid = urllib.parse.quote(entry_id + "@latest", safe="")
        res = self.get(f"/data-stores/{urllib.parse.quote(store, safe='')}/entries/{eid}")
        return None if res is None else res.get("value")

    def ordered(self, store, scope="global", limit=None):
        out, token = {}, None
        while True:
            params = {"maxPageSize": 100, "orderBy": "value desc"}
            if token:
                params["pageToken"] = token
            path = f"/ordered-data-stores/{urllib.parse.quote(store, safe='')}/scopes/{urllib.parse.quote(scope, safe='')}/entries"
            page = self.get(path, params) or {}
            for e in page.get("orderedDataStoreEntries", []):
                key = e.get("id") or e.get("path", "").rsplit("/", 1)[-1]
                out[urllib.parse.unquote(key)] = int(e.get("value") or 0)
                if limit and len(out) >= limit:
                    return out
            token = page.get("nextPageToken")
            if not token:
                return out


def pull_live(universe, limit, verbose):
    oc = OpenCloud(universe, verbose)
    cache = {}
    ids = oc.list_entry_ids(CACHE_STORE, prefix="w1:", limit=limit)
    for i, eid in enumerate(ids):
        v = oc.get_entry(CACHE_STORE, eid)
        if v is not None:
            cache[eid] = v
        if verbose and i % 50 == 0:
            print(f"  {universe}: {i}/{len(ids)} entries", file=sys.stderr)
    out = {CACHE_STORE: cache, "_warnings": []}
    for store in (UNKNOWN_STORE, PLAYS_STORE):
        try:
            out[store] = oc.ordered(store, limit=limit)
        except NotAuthorized as e:
            # The key (or proxy credential) lacks universe.ordered-data-store.scope.entry:read.
            out[store] = {}
            out["_warnings"].append(f"{universe}: skipped {store} ({e})")
            print(f"  WARNING: {out['_warnings'][-1]}", file=sys.stderr)
    out["_calls"] = oc.calls
    return out


def pull_fixture(fixture_dir, universe):
    path = os.path.join(fixture_dir, f"{universe}.json")
    if not os.path.exists(path):
        return {CACHE_STORE: {}, UNKNOWN_STORE: {}, PLAYS_STORE: {}}
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return {k: data.get(k, {}) for k in (CACHE_STORE, UNKNOWN_STORE, PLAYS_STORE)}


# ---------------------------------------------------------------------------------------- library
def load_library(root):
    keys, ids = {}, set()
    for path in sorted(glob.glob(os.path.join(root, "data", "words", "*.jsonl"))):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                e = json.loads(line)
                ids.add(e["w"])
                for k in [e["w"]] + list(e.get("a", [])) + list(e.get("ms", [])):
                    keys.setdefault(k, e["w"])
    return keys, ids


# ------------------------------------------------------------------------------------------ merge
def is_mock(r):
    return "mock" in (r.get("tags") or []) or str(r.get("flavourText", "")).startswith("[MOCK]")


def merge(pulls, library_keys):
    """pulls: {game: {store: {...}}} -> (candidates dict by canonical id, aliases, unknowns)."""
    cands, aliases, unknown, plays = {}, {}, {}, {}
    for game, data in pulls.items():
        for k, n in (data.get(UNKNOWN_STORE) or {}).items():
            unknown.setdefault(k, {})[game] = int(n)
        for k, n in (data.get(PLAYS_STORE) or {}).items():
            plays[k] = plays.get(k, 0) + int(n)
        for sk, rec in (data.get(CACHE_STORE) or {}).items():
            if not isinstance(rec, dict) or not sk.startswith("w1:"):
                continue
            key = sk[3:]
            if rec.get("alias"):
                aliases.setdefault(key, set()).add(rec["alias"])
                continue
            if rec.get("ref"):
                c = cands.setdefault(key, new_cand(key))
                c["refused"].add(game)
                continue
            r = rec.get("r")
            if not isinstance(r, dict):
                continue
            cid = str(r.get("id") or key).lower()
            c = cands.setdefault(cid, new_cand(cid))
            c["games"][game] = r
            c["pc"] += int(rec.get("pc") or 0)
            fs = rec.get("fs")
            if isinstance(fs, (int, float)):
                c["fs"] = fs if c["fs"] is None else min(c["fs"], fs)
            c["src"].add(str(rec.get("src") or r.get("source") or "?"))
            if key != cid and not key.startswith("#"):
                c["typos"].add(key)
    for typo, targets in aliases.items():
        for t in targets:
            if t in cands:
                cands[t]["typos"].add(typo)
            if len(targets) > 1:
                for t2 in targets:
                    if t2 in cands:
                        cands[t2]["reasons"].append(f"alias '{typo}' points at {sorted(targets)} in different games")
    for cid, c in cands.items():
        c["pc"] = max(c["pc"], plays.get(cid, 0))
        evaluate(c, library_keys)
    return cands, aliases, unknown


def new_cand(cid):
    return {"id": cid, "games": {}, "pc": 0, "fs": None, "src": set(), "typos": set(), "refused": set(),
            "reasons": [], "status": "candidate"}


def evaluate(c, library_keys):
    rs = list(c["games"].values())
    if c["refused"] and not rs:
        c["status"] = "refused"
        c["reasons"].append("refused by the AI safety rules")
        return
    if c["refused"]:
        c["reasons"].append(f"refused in {sorted(c['refused'])} but answered elsewhere")
        c["status"] = "conflict"
    if any(is_mock(r) for r in rs):
        c["status"] = "mock"
        c["reasons"].append("mock-provider output (Studio), never promote")
        return
    if c["id"] in library_keys:
        c["status"] = "in_library"
        c["reasons"].append(f"already in library as '{library_keys[c['id']]}'")
        return
    if not WORD.match(c["id"]) or len(c["id"]) > 40:
        c["status"] = "bad_id"
        c["reasons"].append("id is not a plain lowercase phrase")
        return
    if len(rs) > 1:
        a, b = rs[0], rs[1]
        diffs = [f for f in CONFLICT_FIELDS if a.get(f) != b.get(f)]
        if (a.get("visual") or {}).get("bodyPlan") != (b.get("visual") or {}).get("bodyPlan"):
            diffs.append("bodyPlan")
        if diffs:
            c["status"] = "conflict"
            c["reasons"].append("games disagree on " + ", ".join(diffs))
    for t in c["typos"]:
        if t in library_keys and library_keys[t] != c["id"]:
            c["reasons"].append(f"typo alias '{t}' already belongs to library word '{library_keys[t]}' (dropped)")
    problems = validate_short(to_short(c))
    if problems:
        c["status"] = "invalid"
        c["reasons"].extend(problems)


# -------------------------------------------------------------------------------------- formatting
def pick(c):
    """Pick the record to promote: the one from the game with the most info, Defend first on ties."""
    rs = sorted(c["games"].items(), key=lambda kv: (kv[0] != "Defend"))
    return rs[0][1] if rs else {}


def to_short(c, library_keys=None):
    r = pick(c)
    v = r.get("visual") or {}
    e = {
        "w": c["id"],
        "c": r.get("category"), "e": r.get("element"), "z": r.get("size"), "s": r.get("shape"),
        "b": [b for b in (r.get("behaviours") or []) if b in BEHAVIOUR][:8],
        "p": int(r.get("power") or 5), "sp": int(r.get("speed") or 5), "d": int(r.get("durability") or 5),
        "pc": v.get("primaryColour"), "sc": v.get("secondaryColour"), "bp": v.get("bodyPlan"),
        "sh": str(v.get("silhouetteHint") or "")[:60], "m": v.get("motionHint"),
        "snd": str(v.get("soundHint") or "whoosh"), "f": str(r.get("flavourText") or "")[:80],
        "t": [t for t in (r.get("tags") or []) if isinstance(t, str)][:7] + ["ai"],
    }
    typos = sorted(t for t in c["typos"] if WORD.match(t) and (library_keys is None or t not in library_keys))
    if typos:
        e["ms"] = typos[:8]
    return e


def validate_short(e):
    p = []
    for k, lst in (("c", CATEGORY), ("e", ELEMENT), ("z", SIZE), ("s", SHAPE), ("bp", BODYPLAN), ("m", MOTION)):
        if e.get(k) not in lst:
            p.append(f"bad {k}={e.get(k)!r}")
    for k in ("p", "sp", "d"):
        if not 1 <= e[k] <= 10:
            p.append(f"{k} out of range")
    for k in ("pc", "sc"):
        if not HEX.match(str(e.get(k))):
            p.append(f"bad colour {k}")
    if not e["f"]:
        p.append("empty flavour text")
    return p


# ------------------------------------------------------------------------------------------ output
def next_promoted_path(root):
    n = 1
    while os.path.exists(os.path.join(root, "data", "words", f"promoted_{n:02d}.jsonl")):
        n += 1
    return os.path.join(root, "data", "words", f"promoted_{n:02d}.jsonl")


def report(cands, unknown, library_keys, approved, args, meta):
    lines = [f"# Word promotion report", "", f"Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}"
             f" from {meta['source']}.", ""]
    by = {}
    for c in cands.values():
        by.setdefault(c["status"], []).append(c)
    lines += ["## Summary", "", "| status | count |", "|---|---|"]
    for s in sorted(by):
        lines.append(f"| {s} | {len(by[s])} |")
    lines.append("")
    pop = sorted((c for c in cands.values() if c["status"] in ("candidate", "approved")), key=lambda c: -c["pc"])
    lines += ["## Popular new phrases (not in library)", "", "| phrase | plays | games | typos | status |", "|---|---|---|---|---|"]
    for c in pop[:50]:
        lines.append(f"| {c['id']} | {c['pc']} | {', '.join(sorted(c['games']))} | {', '.join(sorted(c['typos'])[:4])} | {c['status']} |")
    lines += ["", "## Conflicts and problems", ""]
    for c in sorted(cands.values(), key=lambda c: c["id"]):
        if c["status"] in ("conflict", "invalid", "bad_id"):
            lines.append(f"- **{c['id']}** ({c['status']}): {'; '.join(c['reasons'])}")
    total_unknown = sum(sum(g.values()) for g in unknown.values())
    covered = {k: g for k, g in unknown.items() if k in library_keys or k in cands}
    missing = sorted(((k, sum(g.values())) for k, g in unknown.items() if k not in covered), key=lambda kv: -kv[1])
    lines += ["", "## Coverage of fallback phrases", "",
              f"{len(unknown)} distinct fallback phrases ({total_unknown} plays). "
              f"{len(covered)} are now covered by the library or the AI cache; {len(missing)} are still uncovered.", "",
              "| phrase | fallback plays |", "|---|---|"]
    for k, n in missing[:100]:
        lines.append(f"| {k} | {n} |")
    lines += ["", f"Library lookup keys: {len(library_keys)}. Open Cloud calls: {meta.get('calls', 0)}."]
    if meta.get("warnings"):
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in meta["warnings"]]
    return "\n".join(lines) + "\n"


def jsonable(c):
    return {"id": c["id"], "status": c["status"], "plays": c["pc"], "firstSeen": c["fs"],
            "games": sorted(c["games"]), "sources": sorted(c["src"]), "typos": sorted(c["typos"]),
            "refusedIn": sorted(c["refused"]), "reasons": c["reasons"],
            "entry": to_short(c) if c["games"] else None}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--fixture", help="read <dir>/<universe>.json instead of Open Cloud")
    ap.add_argument("--out-dir", help="where candidates.json + report.md go (default data/promotion)")
    ap.add_argument("--approve", help="file with one approved phrase per line")
    ap.add_argument("--min-plays", type=int, default=0, help="auto-approve clean candidates with >= N plays")
    ap.add_argument("--write", action="store_true", help="write approved entries to data/words/promoted_NN.jsonl")
    ap.add_argument("--limit", type=int, default=None, help="max entries per store per game (testing)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    root = args.root
    out_dir = args.out_dir or os.path.join(root, "data", "promotion")
    library_keys, _ = load_library(root)

    pulls, calls, warnings = {}, 0, []
    for game, universe in GAMES.items():
        if args.fixture:
            pulls[game] = pull_fixture(args.fixture, universe)
        else:
            print(f"Pulling {game} (universe {universe}) ...", file=sys.stderr)
            pulls[game] = pull_live(universe, args.limit, args.verbose)
            calls += pulls[game].pop("_calls", 0)
            warnings += pulls[game].pop("_warnings", [])
        d = pulls[game]
        print(f"  {game}: {len(d[CACHE_STORE])} cache records, {len(d[UNKNOWN_STORE])} unknown phrases, "
              f"{len(d[PLAYS_STORE])} play counters", file=sys.stderr)

    cands, _, unknown = merge(pulls, library_keys)

    wanted = set()
    if args.approve:
        with open(args.approve, encoding="utf-8") as fh:
            wanted = {l.strip().lower() for l in fh if l.strip() and not l.startswith("#")}
    approved = []
    for c in sorted(cands.values(), key=lambda c: (-c["pc"], c["id"])):
        if c["status"] != "candidate":
            if c["id"] in wanted:
                print(f"  not approving '{c['id']}': {c['status']} ({'; '.join(c['reasons'])})", file=sys.stderr)
            continue
        if c["id"] in wanted or (args.min_plays and c["pc"] >= args.min_plays):
            c["status"] = "approved"
            approved.append(c)

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "candidates.json"), "w", encoding="utf-8") as fh:
        json.dump([jsonable(c) for c in sorted(cands.values(), key=lambda c: (-c["pc"], c["id"]))], fh, indent=1)
    meta = {"source": f"fixture {args.fixture}" if args.fixture else "Open Cloud (live)", "calls": calls,
            "warnings": warnings}
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(report(cands, unknown, library_keys, approved, args, meta))

    if args.write and approved:
        path = next_promoted_path(root)
        with open(path, "w", encoding="utf-8") as fh:
            for c in approved:
                fh.write(json.dumps(to_short(c, library_keys), ensure_ascii=False, separators=(",", ":")) + "\n")
        print(f"Wrote {len(approved)} entries to {path}. Run tools/validate.py and tools/build_library.py next.",
              file=sys.stderr)
    elif approved:
        print(f"{len(approved)} approved (dry run; pass --write to create promoted_NN.jsonl)", file=sys.stderr)
    print(f"{len(cands)} candidates; report in {out_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
