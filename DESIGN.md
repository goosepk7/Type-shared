# WordEngine — shared word engine for Typing Wizards and Type to Defend

WordEngine turns anything a player types into one structured, validated `WordResult`.
Each game maps that result into its own gameplay. **The engine decides meaning, never balance.**

Brief 4 (update: Claude API, stacked modifiers, materials, 40+ body plans, promotion pipeline) is folded in;
it overrides earlier briefs where they conflict.

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
  secondaryElement: Element,  -- "None" unless split-element ("fire ice dragon")
  material: string?,          -- material id ("spaghetti"); nil = the thing's natural material
  mood: Mood,                 -- "Neutral" default; drives face, posture, particles, sound pitch
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
  accents: { string },        -- feature hints from modifiers/materials: "scowl","steam","thrusters","halo","snore"
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
- **BodyPlan** (60): generic Quadruped, Biped, Serpent, Bird, Fish, Insect, Blob, Vehicle, Structure, Weapon, Orb, Swarm,
  Plant, Humanoid, Cloud; specialised Dragon, Spider, Crab, Octopus, Worm, Turtle, Ghost, Robot, Giant, Knight, Wizard, Tree,
  Flower, Mushroom, Cactus, CarWheeled, Tracked, Aircraft, Helicopter, Boat, Submarine, Rocket, Building, Tower, Wall, Gate,
  Bridge, Castle, Sword, Axe, Hammer, Spear, Bow, Gun, Cannon, Shield, Staff, Furniture, Appliance, Container, Ball, Crystal,
  Vortex, Wave, Food. `Schema.BodyPlanParent` maps each specialised plan to its generic parent, so a builder can always
  fall back.
- **Mood**: Neutral, Angry, Sleepy, Scared, Crazy, Hungry, Happy, Sneaky, Lazy, Hyper, Confused, Sad, Smug, Cute
- **Motion**: Walk, Fly, Swim, Slither, Hover, Roll, Hop, Burrow, Static, Float, Spin, Drive
- **Source**: Library, Cache, AI, Admin, Fallback
- **CorrectionMethod**: Exact, Alias, Normalized, Stem, Misspelling, Fuzzy, Phonetic, MultiWord, AI
- **ModifierKind** (also the application order): Size, Count, Mood, Quality, Element, State, Motion, Material

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
  aiSecretName = "ANTHROPIC_API_KEY",  -- Secrets Store name (domain api.anthropic.com), one key per game
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
 -> per-server memory cache -> MemoryStore hot cache -> DataStore permanent cache     [server; free]
 -> Library exact / alias
 -> Stemmer (plurals, -ing/-ed/-er, irregulars: wolves->wolf, mice->mouse)
 -> Known-misspellings table
 -> Fuzzy: Damerau-Levenshtein w/ keyboard-adjacency costs (QWERTY + phone), BK-tree, length-scaled thresholds
 -> Phonetic: Double Metaphone index
 -> Phrase parser (§5a): count + modifiers + material + base thing + extras, each token corrected
 -> [server] AI (Claude, strict JSON via tool use -> Schema.repair) — only if confidence < Config.AI.Threshold,
    the AI is enabled (live kill switch), under the daily spend cap and the player's new-phrase rate limit.
    MemoryStore lock per phrase so only one server in the game ever pays for a phrase. Result written to the
    permanent cache immediately (retry + queue, never lose a paid result), plus the typo as an alias.
 -> Fallback blob
```

### 5a. Phrase parser (brief 4 §2-3)

Every input parses into **count + modifiers + material + base thing + extras**:

- Word order is forgiving ("shark angry" == "angry shark"). Articles/fillers are dropped ("a", "the", "some").
- Material phrasings: "spaghetti dragon", "dragon made of spaghetti", "dragon made out of spaghetti",
  "spaghetti-dragon", "dragon of spaghetti", "dragon but spaghetti". A token that is both a thing and a material
  is a material when another base thing is present ("cheese tank") and the base otherwise ("cheese").
- Modifier kinds, applied in this order with caps from `Config.Modifiers`: Size, Count, Mood, Quality, Element,
  State, Motion, Material. At least 4 stacked modifiers are supported ("tiny angry golden robot shark").
- Contradictions resolve sensibly and with humour: opposing sizes cancel to Medium and set mood Confused
  ("tiny giant shark"); two elements make a split-element result (`element` + `secondaryElement`).
- Every applied modifier must be visible: modifiers add `visual.accents` and/or `mood`, which the builder renders.
- Brands, franchises, copyrighted characters and real people are stripped to the generic idea by the parser
  (blocklist of protected names -> generic replacement table) and by the AI prompt.

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

Build order: **body plan from the base thing -> material reshapes construction -> modifiers change proportions,
posture, face, accents, effects and sound.** Faces (eyes + mouth with mood expressions) go on everything, objects
included ("angry toaster"). Materials define construction (Strands for spaghetti/yarn, Bricks, Panels for cardboard,
Wobble for jelly, Swarm for bees, Shards for glass/crystal, Inflated for balloons...), palette, particles, sound and
gameplay hooks; they apply to signature models too and to both styles (a spectral spaghetti dragon is woven from
glowing noodle strands). Material data: `data/materials.json` (150+), material x element interactions in
`data/material_reactions.json` (fire melts cheese/ice, burns wood/cardboard; water ruins paper; lightning conducts
through metal). Visual QA: `tools/gallery` renders 300+ random base x material x modifier phrases in both styles to a
contact sheet each milestone; the worst 10% get fixed before moving on.

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
- **Cross-game sharing = promotion pipeline (brief 4 §5).** DataStores are per-game, so each game keeps its own
  permanent word cache (`WordEngine_WordCache_v1`) and word book. `tools/promote.py` (run offline with an Open Cloud
  key from env vars) pulls both games' caches through the Open Cloud DataStore API, merges them, flags conflicts and
  popular new phrases for review, and writes approved entries into `data/words/promoted_*.jsonl`. Shipping a shared
  update gives both games every word either has learned. Unknown/fallback phrases are logged with counts
  (`WordEngine_Unknown_v1`) and pulled by the same tool into a coverage report.
- The word book is per game in v1 (brief 1 wanted it shared; brief 4 makes per-game stores the rule). The promotion
  tool can merge word books later if needed.
- Permanent cache record: normalized phrase -> `{ result: WordResult JSON, playCount, firstSeen, source, aliasOf? }`.
  MemoryStore SortedMap is the hot layer and also holds the per-phrase AI lock.
- AI cost controls: daily spend cap (estimated from returned token usage, MemoryStore counter per UTC day), per-player
  new-phrase limit, live kill switch (`Config.AI.Enabled`, readable live from a DataStore/attribute), Studio play-solo
  uses an obvious mock provider because Secrets are only available in live servers and Team Test.

## 11. Testing

`lune run tests` runs every `*.spec.luau`. Required suites: Normalizer, Speller (incl. a 500-typo golden set),
Library integrity, Modifiers caps, Reactions symmetry/coverage, Schema repair fuzzing, Summon overlap checks.
