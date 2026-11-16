# WordEngine — shared word engine for Typing Wizards and Type to Defend

WordEngine turns anything a player types into one structured, validated `WordResult`.
Each game maps that result into its own gameplay. **The engine decides meaning, never balance.**

Status: v0 interfaces (frozen for game threads; additive changes only, breaking changes bump `WordEngine.VERSION` major).

## 0. Design principles

1. **Fun first.** Every typed word must do something exciting and on-theme. "asteroid" drops a burning rock from the
   sky with a shockwave; "tornado" (even "small tornado") spawns a twister that lifts and flings enemies. Tags must
   carry enough verbs (`Lifts`, `Knockback`, `Pulls`, `Explodes`...) for the games to deliver that fantasy.
2. **AAA look.** Clean silhouettes, cohesive palettes per element, layered VFX, and zero z-fighting.
3. **Never fail silently.** Every input resolves to something, at worst a funny glitter blob.
4. **Meaning, not balance.** The engine says what a word *is*; each game decides the numbers.

---

## 1. Packaging and consumption

**Choice: git submodule + Rojo `$path` mounts.**

| Option | Verdict |
|---|---|
| Wally package | Needs a registry. wally.run is public (would publish our library and prompts); a private registry is extra infra to host. Rejected. |
| Roblox Packages | Edited in Studio, not diffable, no CI, no tests, auto-update is all-or-nothing. Rejected as the source of truth. |
| **git submodule + Rojo** | Private, pinned to an exact commit per game, reviewable diffs, CI-tested, zero extra tooling (games already use Rojo). Chosen. |

How a game consumes it:

```bash
git submodule add -b claude/project-thread-a6z2p7 https://github.com/goosepk7/Type-shared Packages/WordEngine
# later, after the shared branch merges: git submodule set-branch -b main Packages/WordEngine
```

In the game's `default.project.json`:

```json
"ReplicatedStorage": { "$className": "ReplicatedStorage",
  "WordEngine": { "$path": "Packages/WordEngine/src/Shared" } },
"ServerScriptService": { "$className": "ServerScriptService",
  "WordEngineServer": { "$path": "Packages/WordEngine/src/Server" } }
```

The shared repo ships `default.project.json` exposing the same two mounts, and `test.project.json`
for the standalone test place.

Generated files (the compiled word library) **are committed**, so consumers never run a build step.
CI fails if `tools/build_library.py` output differs from what's committed.

### Module conventions

- Typed Luau, `--!strict` everywhere except where Roblox APIs make it impractical (noted per file).
- `src/Shared` is **pure Luau** wherever possible (no `game:` access at require time) so it runs under
  [Lune](https://lune-org.github.io/docs) for unit tests. Roblox-only modules (Summon, Effects, UI, Net)
  only touch Roblox APIs inside functions.
- Requires inside a root use `script` relative instances (`require(script.Parent.Schema)`).
  Tests run under Lune with a tiny `script` shim (`tests/shim.luau`) that maps instance paths to files.
- `src/Server` requires Shared through `ReplicatedStorage.WordEngine`.
- No secrets in code, logs or client-visible scripts. Server reads keys with `HttpService:GetSecret`.

## 2. Module layout

```
src/Shared/            -> ReplicatedStorage.WordEngine   (client + server)
  init.luau            -- facade: WordEngine.VERSION, lazy accessors to everything below
  Types.luau           -- all exported types (WordResult, enums, Reaction, ...)
  Schema.luau          -- enum lists, validate/repair/clamp, fallback result, (de)serialize
  Normalizer.luau      -- normalize(), tokenize(), leetspeak/number words, repeat collapse
  Speller/             -- correction pipeline (stem, misspellings, BK-tree DL fuzzy, Double Metaphone)
  Library/             -- get/lookup/aliases/signature; Generated/ compiled chunks (lazy loaded)
  Modifiers.luau       -- parse + apply modifiers with caps
  Resolver.luau        -- resolveLocal(input): the full library-only pipeline (no network)
  Reactions.luau       -- element matchups + reactions (data-driven)
  Summon/              -- procedural summon builder (Spectral + Solid styles), body plans, animator
  Effects/             -- pooled projectiles, beams, impacts, explosions, auras, weather, statuses
  UI/                  -- mobile-first UI kit (TypingBox, Hotbar, Toast, DidYouMean, WordReveal, Settings)
  Net.luau             -- remote names + client helpers (WordEngine.Net.interpret(text))
  Config.luau          -- tunables (budgets, thresholds, rate limits). Games override via Config.set()

src/Server/            -> ServerScriptService.WordEngineServer  (server only)
  init.luau            -- WordEngineServer.start(options)
  Interpreter.luau     -- library guess + AI upgrade, caching, analytics
  AI/                  -- provider client, prompt, JSON parse/repair, queue, cost tracking
  Cache.luau           -- MemoryStore hot layer + DataStore global word cache
  Safety.luau          -- TextService filtering, blocklist, per-player rate limit + spam detection
  Data/                -- session-locked player data (retries, versioning, migrations)
  WordBook.luau        -- per-player word history, shared across both games
  Currency.luau, Purchases.luau, Analytics.luau, Admin.luau

data/                  -- source of truth for all content (JSONL / JSON), compiled into Generated/
tools/                 -- build_library.py (compile), validate.py (schema + stats), gen_words_md.py
tests/                 -- Lune test runner + specs
testplace/             -- test place scripts (type any word, see both styles side by side)
```

## 3. The tag schema: `WordResult`

```lua
export type WordResult = {
  schemaVersion: number,      -- 1
  id: string,                 -- canonical library key incl. modifiers stripped: "shark"
  canonical: string,          -- display canonical incl. modifiers: "giant fire shark"
  input: string,              -- what the player typed (UNFILTERED; server only, never replicate raw)
  confidence: number,         -- 0..1 overall
  source: Source,             -- "Library" | "Cache" | "AI" | "Admin" | "Fallback"
  correction: Correction?,    -- set when input ~= canonical; drives "did you mean"
  category: Category,
  element: Element,
  size: Size,
  shape: Shape,
  behaviours: { Behaviour },  -- array, unique, sorted. Use Schema.has(r, "Flies")
  power: number,              -- 1..10 (float allowed after modifiers, always clamped)
  speed: number,              -- 1..10
  durability: number,         -- 1..10
  count: number,              -- 1..Config.MaxCount (swarm/army/triple modifiers)
  modifiers: { AppliedModifier },
  signature: boolean,         -- hand-made visuals exist (or will) for this id
  synonymGroup: string,       -- no-repeat key: "cat" for cat/kitty/kitten/cats. == id unless grouped
  visual: Visual,
  flavourText: string,        -- one short, clean, funny line
  tags: { string },           -- free extra tags ("undead","mechanical","edible","royal",...)
}

export type Visual = {
  primaryColour: string,      -- "#RRGGBB" (Color3.fromHex)
  secondaryColour: string,
  bodyPlan: BodyPlan,         -- summon builder skeleton
  silhouetteHint: string,     -- short free text: "long neck, wings, spiked tail"
  motionHint: Motion,
  soundHint: string,          -- sound key: "roar","whoosh","clank","splash","zap",...
}

export type Correction = { method: CorrectionMethod, from: string, to: string, confidence: number,
                           alternatives: { string } }   -- up to 3 other candidates for the chip
export type AppliedModifier = { id: string, kind: ModifierKind }
```

Enums (exact strings; `Schema.Enums.*` lists them):

- **Category**: Creature, Object, Weapon, Vehicle, Structure, Element, Weather, Disaster, Food, Tool, Abstract, Person, Place, Plant, Machine
- **Element** (12 + None): Fire, Water, Ice, Lightning, Earth, Wind, Nature, Light, Shadow, Poison, Metal, Arcane, None
- **Size**: Tiny, Small, Medium, Large, Huge, Colossal
- **Shape**: Bolt, Beam, Wall, Cloud, Rain, Wave, Orb, Blade, Shield, Summon, Mount, Trap, Turret, Zone, Buff
- **Behaviour**: Flies, Swims, Burrows, Charges, Explodes, Heals, Blocks, Pulls, Pushes, Freezes, Burns, Shocks,
  Poisons, Slows, Stuns, Spreads, Follows, Orbits, Lingers, Pierces, Bounces, Splits, Grows, Shrinks, Teleports,
  Invisible, Reflects, Steals, Lures, Distracts, Ranged, Melee, Rideable, Summons, Drains, Confuses, Knockback, Lifts
- **BodyPlan**: Quadruped, Biped, Serpent, Bird, Fish, Insect, Blob, Vehicle, Structure, Weapon, Orb, Swarm, Plant, Humanoid, Cloud
- **Motion**: Walk, Fly, Swim, Slither, Hover, Roll, Hop, Burrow, Static, Float, Spin, Drive
- **Source**: Library, Cache, AI, Admin, Fallback
- **CorrectionMethod**: Exact, Alias, Normalized, Stem, Misspelling, Fuzzy, Phonetic, MultiWord, AI
- **ModifierKind**: Size, Element, Count, Quality

Notes:
- `Plant` and `Machine` categories were added to the brief's list (both briefs need them: TD maps Machines to turrets).
- `input` is unfiltered: servers keep it, but **never** send it to other clients. Show `canonical` (a library
  word) or the filtered string from `Safety`.
- `Schema.validate(raw) -> (WordResult?, {string})` and `Schema.repair(raw) -> WordResult` are the only way
  untrusted data (AI JSON, DataStore cache, admin edits) becomes a `WordResult`. Numbers are clamped, unknown
  enums mapped to closest/default, strings length-limited.
- `Schema.fallback(input) -> WordResult`: the "confused glitter blob" (Arcane, Tiny, Summon, Blob, power 1).
  It always does *something small*; never nil.

## 4. Public APIs

### Shared (client + server)

```lua
local WordEngine = require(ReplicatedStorage.WordEngine)
WordEngine.VERSION                          -- "0.1.0"
WordEngine.Types                            -- types only
WordEngine.Schema.Enums / validate / repair / fallback / has(result, behaviour) / clone
WordEngine.Normalizer.normalize(text): string
WordEngine.Normalizer.tokenize(text): { string }
WordEngine.Speller.correct(text): SpellResult
    -- { canonical: string?, confidence, method, alternatives, tokens }
WordEngine.Library.get(id): WordResult?     -- by canonical id
WordEngine.Library.lookup(word): string?    -- alias/plural/variant -> canonical id
WordEngine.Library.synonymGroup(word): string?  -- "kitty" -> "cat"
WordEngine.Library.isSignature(id): boolean
WordEngine.Library.count(): number
WordEngine.Library.prefixSearch(prefix, limit): { string }   -- autocomplete
WordEngine.Library.random(filter?): WordResult               -- bots / empty loadout
    -- filter = { shape?, element?, category?, size?, excludeGroups: {[string]: true}?, signatureOnly?, rng: Random? }
WordEngine.Suggest.prefix(prefix, wordBook: {string}?, limit): { string }  -- client-side autocomplete, word book first
WordEngine.Modifiers.parse(tokens): (rest: {string}, mods: {Modifier})
WordEngine.Modifiers.apply(result, mods): WordResult         -- caps enforced (Config.Modifiers)
WordEngine.Resolver.resolveLocal(text): WordResult           -- full pipeline minus AI; never nil
WordEngine.Reactions.get(a: Element, b: Element): Reaction?  -- order-independent
WordEngine.Reactions.matchup(attacker, defender): number     -- multiplier hint: 0.5 | 1 | 1.5 (games may rescale)
WordEngine.Reactions.all(): { Reaction }
WordEngine.Summon.build(result, opts: SummonOptions): Model
    -- opts = { style: "Spectral" | "Solid", budget: { maxParts: number?, maxParticles: number? }?,
    --          scale: number?, seed: number? }
    -- Deterministic: same (result, seed) -> identical model on every client. Summon.blueprint(result, opts) is the pure stage.
WordEngine.Summon.animate(model, result): Animator   -- :play("Idle"|"Move"|"Attack"|"Hit"|"Die"|"Spawn"), :destroy()
WordEngine.Effects.play(effectId, params): EffectHandle  -- pooled
WordEngine.Effects.status(target, status, duration)       -- Burn/Freeze/Shock/Poison/Slow/Stun visuals
WordEngine.UI.*                                           -- see src/Shared/UI/README.md
WordEngine.Net.interpret(text): WordResult    -- client: yields; fires onUpgrade later via Net.Upgraded signal
```

`Reaction`:
```lua
export type Reaction = {
  id: string,                 -- "Steam"
  elements: { Element },      -- {"Fire","Ice"}
  name: string,               -- "Steam Cloud"
  description: string,
  result: "Zone" | "Burst" | "Status" | "Transform" | "Buff" | "Cancel",
  statuses: { string },       -- {"Blind"} ; gameplay hooks
  hooks: { string },          -- semantic hooks the games implement: "BlocksVision","Spreads","Chain","AreaDamage",...
  magnitudeHint: number,      -- 0..1 relative strength; games pick numbers
  durationHint: number,       -- seconds hint
  vfx: string,                -- Effects id
  sfx: string,
}
```

### Server only

```lua
local WordEngineServer = require(ServerScriptService.WordEngineServer)
WordEngineServer.start({
  game = "Wizard" | "Defend",          -- analytics namespace
  aiSecretName = "WORDENGINE_AI_KEY",  -- Secrets Store name
  remotes = true,                       -- create default remotes in ReplicatedStorage.WordEngineRemotes
})

Interpreter.interpretAsync(player, text, opts?): (WordResult, InterpretHandle)
    -- Yields at most Config.AI.InstantTimeout (1.5s). Returns the best result available then.
    -- handle.upgraded:Connect(fn(newResult)) fires once if the AI answers later with a better result.
    -- Applies Safety (rate limit, blocklist, filter) first. Never errors, never nil.
Safety.filterForBroadcast(player, text): string        -- TextService, correct broadcast method
Safety.filterForUser(player, text, toPlayer): string
Safety.isBlocked(text): boolean
WordBook.get(player): { WordBookEntry }   WordBook.record(player, result)
Data.get(player) / Data.update(player, fn) / Data.onLoaded
Currency.add/spend/balance   Purchases.registerProduct(id, handler)   Analytics.event(name, fields)
Admin.retag(id, patch) / Admin.forceResult(word, result) / Admin.ban(word) / Admin.testCast(word)
```

## 5. Resolution pipeline

```
input
 -> Safety (rate limit, spam, blocklist on normalized text) -> Fallback if blocked
 -> Normalizer (lowercase, trim, collapse spaces, strip punctuation/emoji, number words, leetspeak, 3+ repeats -> 2)
 -> Library exact / alias
 -> Stemmer (plurals, -ing/-ed/-er, irregulars: wolves->wolf, mice->mouse)
 -> Known-misspellings table
 -> Fuzzy: Damerau-Levenshtein w/ keyboard-adjacency costs (QWERTY + phone), BK-tree, length-scaled thresholds
 -> Phonetic: Double Metaphone index
 -> Multi-word: split, strip/parse modifiers (max 3, Config caps), correct each token, longest library phrase wins
 -> [server] Cache (MemoryStore -> DataStore)
 -> [server] AI (strict JSON -> Schema.repair) — only if confidence < Config.AI.Threshold
 -> Fallback blob
```

Confidence bands: `>= 0.9` silent; `0.6..0.9` show "did you mean" chip with `correction.alternatives`; `< 0.6`
treated as unknown (AI). Every successful correction is cached (`Cache`), so a typo is fuzzy-matched once.

## 6. Data formats (`data/`)

`data/words/*.jsonl` — one entry per line, short keys (authoring cost matters at 10k+ entries):

```json
{"w":"dragon","a":["dragons","drake","wyrm"],"c":"Creature","e":"Fire","z":"Huge","s":"Summon","b":["Flies","Burns","Ranged"],"p":8,"sp":6,"d":8,"pc":"#B3261E","sc":"#F2A43A","bp":"Quadruped","sh":"winged reptile, horns, long tail","m":"Fly","snd":"roar","f":"Breathes fire. Hoards loot. Judges you.","t":["mythical","reptile"],"sig":1,"g":"dragon"}
```

| key | field | key | field |
|---|---|---|---|
| w | canonical id (lowercase, spaces allowed) | bp | bodyPlan |
| a | aliases (plurals, synonyms, regional, slang) | sh | silhouetteHint |
| c | category | m | motionHint |
| e | element | snd | soundHint |
| z | size | f | flavourText (<= 60 chars) |
| s | shape | t | tags |
| b | behaviours | sig | 1 if signature |
| p, sp, d | power, speed, durability (1..10 ints) | g | synonymGroup (optional; defaults to w) |
| pc, sc | primary/secondary colour hex | ms | known misspellings (optional) |

Other data: `modifiers.json`, `reactions.json`, `matchups.json`, `misspellings.jsonl`, `blocklist.txt`
(hashed, see Safety), `keyboard.json`. `tools/validate.py` enforces the schema, uniqueness of every id and alias
across the whole library, power distribution by category and size, and element coverage. `tools/build_library.py`
compiles to `src/Shared/Library/Generated/*.luau` (chunks of ~400 entries, loaded lazily, O(1) hash lookups).

## 7. Element reactions

12 elements, full 12x12 matchup table (`data/matchups.json`, multiplier hints) and 40+ reactions
(`data/reactions.json`). Examples: Fire+Ice=Steam (BlocksVision), Water+Lightning=Electrified (Chain, AreaDamage),
Fire+Nature=Wildfire (Spreads), Wind+Fire=Firestorm, Earth blocks Lightning, Light weakens Shadow.

## 8. Visual generation

- One builder, two styles. `Spectral` = Neon/ForceField energy, element-gradient Beams, Trails, ParticleEmitters,
  additive glow; `Solid` = chunky stylized SmoothPlastic/Plastic/Metal parts with readable silhouettes and
  colour-blocked materials.
- **No z-fighting rule (enforced in code and tests):** no two coplanar coincident faces. Parts that touch are either
  inset (`Config.Visual.Inset = 0.02` studs), welded at non-coplanar angles, or merged. Decals/SurfaceGuis are
  offset by `Config.Visual.DecalOffset`. `tests/summon_overlap.spec` checks every body plan for coplanar overlaps.
- Body plans: quadruped, biped, serpent, bird, fish, insect, blob, vehicle, structure, weapon, orb, swarm, plant,
  humanoid, cloud. Parts library (heads, limbs, wings, tails, horns, wheels, turrets...) chosen by tags.
- Budgets (phone-first, per summon): Small <= 12 parts, Medium <= 20, Large <= 30, Huge/Colossal <= 40;
  <= 2 emitters (Spectral 3), <= 60 particles/sec per emitter. Signature summons may use MeshParts.
- Procedural animation via `Summon.animate` (CFrame/Motor6D-driven, anticipation + overshoot easing).

## 9. Safety

- Every player string shown to others goes through `TextService:FilterStringAsync` and
  `GetNonChatStringForBroadcastAsync` / `GetNonChatStringForUserAsync`. Raw input never replicates.
- If filtering hashes the text: resolve for gameplay only if the normalized input is an exact/alias library hit
  and not blocklisted; otherwise Fallback. Display the library canonical, never the raw input.
- Blocklist (`data/blocklist.txt`, normalized) maps to Fallback regardless of filter. AI prompt refuses and returns
  the Fallback category.
- Rate limit: token bucket per player (Config.Safety), spam detection on repeats.

## 10. Persistence

- Player data: session-locked DataStore records (lock with server JobId + timestamp, steal after timeout), retries
  with backoff, `version` field + ordered migrations, autosave + BindToClose.
- **Cross-game sharing (word book + global word cache).** DataStores are per-universe, and the two games are
  separate universes. Design: the **Type to Defend universe (10777140395) is the "home" store** for cross-game data.
  - Each game keeps a local copy in its own DataStores (`WordEngine_WordBook_v1`, `WordEngine_WordCache_v1`) so
    play never depends on the network.
  - Servers sync with the home universe through **Open Cloud DataStore/MemoryStore APIs called from HttpService**
    (`apis.roblox.com`, API key from the Secrets Store, scoped to the home universe's DataStores only). The Defend
    game talks to its own stores directly and skips HTTP.
  - Sync is write-behind and batched (word book merged on join/leave; cache entries pushed when the AI creates them,
    pulled on cache miss before calling the AI). Merge is a union with max(playCount), so it is conflict-free.
  - If the home is unreachable everything still works locally; the AI may be called twice for one word in the
    worst case. Exact API availability and limits are verified in `docs/ROBLOX_PLATFORM_NOTES.md`.
- Global word cache keys: normalized input -> `WordResult` JSON (+ `playCount`, `firstSeen`, `source`).
  MemoryStore SortedMap is the hot layer (TTL 7 days, refreshed on hit).

## 11. Testing

`lune run tests` runs every `*.spec.luau`. Required suites: Normalizer, Speller (incl. a 500-typo golden set),
Library integrity, Modifiers caps, Reactions symmetry/coverage, Schema repair fuzzing, Summon overlap checks.
