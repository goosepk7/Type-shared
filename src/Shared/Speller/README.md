# Speller

Turns anything a player types into **one base thing + modifiers + material + extras**, with a confidence.
Entry points: `Speller.correct(text) -> SpellResult` (this module), `Resolver.resolveLocal(text) -> WordResult`
(applies the result), `Resolver.parse(text)` (breakdown for inspectors), `Suggest.prefix` (autocomplete).

## Pipeline

1. **Normalize** (`Normalizer.luau`): unicode fold (accents, full-width, smart quotes), lowercase, punctuation and
   emoji become spaces, apostrophes/hyphens kept only inside words, leetspeak inside words with >= 2 letters
   (`dr4gon`, `f1re`; `100`, `r2d2`, `4x4` untouched), `2 headed` -> `two headed`, 3+ repeated letters -> 2.
2. **Protected names** (`data/protected_names.json`): brands, franchises, copyrighted characters and real people
   become the generic idea (`pikachu` -> `electric yellow mouse`); brand words (`pokemon dragon`) are dropped.
   Results that went through this step are capped at 0.88 so the chip shows what was understood.
3. **Whole phrase, cheap** (O(1) hash probes, for each `Normalizer.variants` form): authored id / alias, spacing
   variant (`t rex`, `firedragon`), known misspelling (`data/misspellings.jsonl` + entry `ms`), stemmer
   (plurals, `-ing`, `-ed`, `-er`, irregulars like `wolves`, `mice`, `froze`).
4. **Single word**: fuzzy + phonetic (`Fuzzy.luau`), or a compound split (`giantshark`, `spaghettidragon`).
   - Candidates: exhaustive edits-1 probes (words <= 8 letters), padded-bigram index bucketed by length with
     prefix filtering of the commonest bigrams (multi-edit typos), Double Metaphone codes (sound-alikes).
   - Score: weighted Damerau-Levenshtein (`Distance.luau`, costs in `data/keyboard.json`): keyboard distance on
     QWERTY / phone / QWERTZ / AZERTY, look-alike sounds (c/k, s/z), vowel swaps, doubled/missing double letters,
     fat-finger inserts, dropped vowels, cheap transpositions, extra cost on the first letter.
   - Threshold scales with length (`Config.Speller.FuzzyMaxCost`; 1-2 letters never fuzzy-match).
   - Ranking: cost, minus a phonetic-agreement bonus, minus a popularity prior (signature / well-aliased words),
     plus a small penalty for alias-only and multi-word keys. Up to 3 alternatives.
5. **Phrase parser** (multi-word): minimum-cost segmentation (dynamic programming) of the tokens into exactly one
   **base** library phrase (longest phrase preferred, rightmost head preferred, nouns after `wearing/with/holding`
   are accessories), **modifiers** (Size, Count, Mood, Quality, Element, State, Motion; `data/modifiers.json`, 1,700+
   words incl. misspellings), **materials** (`data/materials.json`), numbers, **fillers** (`a`, `made`, `out`, `of`,
   `but`, `powered`...) and **extras** (unplaced words, sent to the AI). Every slot is typo-tolerant; order is free.
   A word that is both a thing and a material is the material when another base exists (`cheese tank`).
6. **Cache**: LRU (`Config.Speller.CacheSize`) keyed by the normalized + light forms.

Applying a parse (`Modifiers.apply`) is a separate, capped step: kinds apply in the order Size, Count, Mood,
Quality, Element, State, Motion, Material; opposing sizes cancel to Medium + `Confused`; two elements become
`element` + `secondaryElement`; totals are capped by `Config.Modifiers`.

## Confidence bands

| confidence | typical source | UX |
|---|---|---|
| 1.0 | exact id / alias, exact phrase parse | silent |
| 0.97 | normalized (leetspeak, repeats, spacing variant) | silent |
| 0.93-0.96 | known misspelling, plural stem | silent |
| 0.80-0.92 | one-slip fuzzy (adjacent key, transposition, doubled letter), `-ing/-ed` stems | silent >= 0.9, else chip |
| 0.60-0.86 | multi-edit fuzzy, phonetic, protected-name rewrite, ambiguous near-ties (-0.08) | "did you mean" chip |
| < 0.6 | unplaced extras (x0.72 each), no base found | unknown: Fallback locally, AI on the server |

Phrase confidence is the product of its slots' confidences times `ExtraPenalty ^ #extras`.

## Performance (Lune, 9.1k entries / 37k keys; `lune run tools/bench_speller.luau`)

Exact words ~0.05 ms; single-word typos median ~0.9 ms (p90 ~2.4 ms); phrases median ~0.12 ms; cached ~0.1 ms;
`Suggest.prefix` ~0.05 ms. The fuzzy index is built lazily on the first miss (~150 ms in Lune including source
compile); call `Speller.preload()` during a loading screen to hide it.
