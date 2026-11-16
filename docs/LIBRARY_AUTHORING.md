# Word library authoring guide

The library is the heart of both games. A dull or wrong result for a typed word is a broken promise to the player.
**Fun first:** every entry must give the games enough to make it exciting. "asteroid" is a burning rock from the sky
that `Explodes` + `Knockback`; "tornado" `Lifts` + `Pulls` + `Knockback` + `Spreads` and flings things.

## Format

One JSON object per line in `data/words/<domain>_<nn>.jsonl` (~200 lines per file). Keys (see DESIGN.md §6):

```json
{"w":"tornado","a":["tornados","tornadoes","twister","twisters","cyclone"],"c":"Disaster","e":"Wind","z":"Huge","s":"Zone","b":["Lifts","Pulls","Knockback","Spreads","Lingers"],"p":8,"sp":6,"d":5,"pc":"#8A9BA8","sc":"#DCE6EC","bp":"Cloud","sh":"tall funnel, debris ring at base","m":"Spin","snd":"howl","f":"Picks things up. Puts them down far away.","t":["storm","natural"],"sig":1,"ms":["tornadoe","tornato","tornedo"]}
```

Rules:
- `w` lowercase canonical, singular, most common spelling (US spelling canonical, UK as alias: color/colour).
- `a` aliases: plurals (incl. irregular), synonyms that mean the *same thing*, regional spellings, slang, abbreviations,
  spaced/unspaced/hyphenated variants ("t rex", "trex", "t-rex"). Never an alias that is its own distinct thing
  (a "wolf" is not an alias of "dog"). An alias must not collide with any other entry's id or alias.
- `g` synonymGroup: only when distinct entries should count as the same word for no-repeat rules
  (e.g. "kitten" entry with `"g":"cat"`). Usually omit.
- `ms` known misspellings players actually make (2-5 for common/long words; omit for short obvious ones).
- `f` flavour text: <= 60 chars, short, funny, clean, never mean. Vary the jokes; no template repetition.
- `sh` silhouette hint: concrete shape cues for the summon builder ("stubby legs, huge jaw, back spikes").
- `pc`/`sc`: real, tasteful colours for the thing (a shark is slate grey-blue + off-white, not element colour).
- `t` tags (<= 8): useful gameplay tags such as mythical, extinct, undead, robot, mechanical, edible, sweet, royal,
  aquatic, insect, reptile, bird, mammal, plant, space, holiday, sport, music, silly, meme, spooky, cute, ancient,
  explosive, sharp, heavy, flammable, frozen, magnetic, holy.
- `sig: 1` for iconic, high-fantasy-value words that deserve hand-made visuals (~5% of each domain).
- Safe for a kids' platform: no real people, brands/trademarks, real tragedies, drugs, sexual content, gore, slurs,
  real-world weapons by model name (say "rifle", never a brand/model). Cartoon violence is fine.

## Choosing tags

- **category**: what it *is*. Creature (animals/monsters), Person (professions/archetypes), Machine (robots, engines,
  powered contraptions), Tool (non-weapon handheld), Object (everything else that's a thing), Plant, Food, Weapon,
  Vehicle, Structure, Place, Element, Weather, Disaster, Abstract (concepts, verbs, buffs).
- **shape**: how it is *delivered* in a fight. Creatures/People usually Summon (Mount if commonly ridden: horse,
  dragon, camel). Ranged weapons Bolt/Beam, melee Blade, protective Shield/Wall, area things Zone/Cloud/Rain/Wave,
  machines Turret, objects often Trap/Orb, verbs and concepts Buff (self) or matching delivery ("freeze" -> Wave, "explode" -> Orb).
- **element**: the obvious one, else None. Don't force elements: a cat is None; a phoenix is Fire; an anchor is Metal.
- **behaviours**: 2-6 that make it play like itself. Flyers `Flies`; sea life `Swims`; burrowers `Burrows`;
  ranged things `Ranged`, melee `Melee`; rideable `Rideable`. Use the fun verbs liberally where they fit:
  `Lifts` (tornado, crane, magnet), `Knockback` (hammer, bull, wave), `Pulls` (black hole, magnet, octopus),
  `Explodes` (bomb, meteor, firework), `Lures`/`Distracts` (cake, cheese, laser pointer), `Splits`, `Bounces`.

## Balance bands (raw meaning, before each game balances)

| size | typical power | examples |
|---|---|---|
| Tiny | 1-3 | ant, pebble, candy |
| Small | 2-4 | cat, dagger, cupcake |
| Medium | 3-6 | wolf, sword, car |
| Large | 5-7 | bear, cannon, tank |
| Huge | 6-9 | elephant, dragon, tornado |
| Colossal | 8-10 | kaiju, black hole, asteroid, tsunami |

- power 9-10 is rare (< 3% of entries): world-ending things only (black hole, supernova, nuke, apocalypse).
- speed: cheetah 10, snail 1. durability: tank/fortress 9-10, bubble 1.
- Silly things stay viable: a "rubber duck" is power 2 but `Distracts`/`Bounces` and has a great flavour line.

## Process

Write ~200 entries per file, then run `python3 tools/validate.py` (all files: catches cross-file collisions).
Fix every error before moving on. Run `python3 tools/validate.py --stats` to check balance and coverage.
