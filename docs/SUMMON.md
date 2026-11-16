# Summon builder

`src/Shared/Summon` turns a WordResult into a summon model. It is one builder with two looks:

- **Spectral:** glowing magic energy in the element's colours, with trails and particles.
- **Solid:** a chunky, stylised, real-looking creature or object.

The design is in DESIGN.md §8, and the Roblox research behind it is in `docs/platform/summon.md`.

## API

```lua
local Summon = WordEngine.Summon
local bp    = Summon.blueprint(result, { style = "Solid" | "Spectral", seed = n?, scale = k?,
                                         budget = { maxParts?, maxParticles? }?, material = id | record? })
local model = Summon.build(result, opts)          -- Roblox: Model (PrimaryPart Root, Motor6D rig, fx)
local model = Summon.buildBlueprint(bp, opts)     -- opts: anchored, collisionGroup, parent, cframe, effects, loadMesh
local anim  = Summon.animate(model, result)       -- :play("Idle"|"Move"|"Attack"|"Hit"|"Die"|"Spawn"), :setSpeed(s), :onFinished(fn), :destroy()
Summon.check(bp)                                  -- z-fighting violations (empty after the built-in fix pass)
Summon.registerSignature(id, fn(B, ctx), { plan = "Quadruped|Dragon", mesh = { assetId, scale?, offset?, keepRoles? } }?)
Summon.setSignatureMesh(id, mesh) / Summon.signatures() / Summon.signatureFor(result)
Summon.setMaterialProvider(fn(id) -> Material?)  -- used when Library.material has no record for the id
```

`blueprint` is pure and deterministic, and it runs under Lune. `build` and `animate` need Roblox.

## Build order

The build runs these stages in order:

1. **Budget and detail.**
   - The part budget comes from `Config.Visual.SummonPartBudget` for the size class. A signature gets 25% more.
     A formation shares `FormationBudgetScale` budgets across its members.
   - The material and accent reservations are taken off the budget first.
   - What is left picks a detail level from 0 to 3. Plans scale the eyes, legs, wings and neck to that level, so
     nothing is built only to be dropped.
2. **Body plan or signature.**
   - There are 15 generic generators and 45 specialised routes, so all 60 `Schema.Enums.BodyPlan` values build.
     There is also an Objects generator for furniture, appliances and containers.
   - A signature starts from a tuned base body (`SigKit.base`) and then adds hand-placed hero details on anchors
     measured from what was built: eyes, top of the head, mouth and body bounds.
3. **Material (`Materials.apply`).** The material changes how the thing is built. See the next section.
4. **Accents (`Accents.apply`).** Modifiers add visible accents from a registry (`result.visual.accents`). An
   accent can do three things:
   - add geometry: hats, eyepatch, sunglasses, visor, mustache, bowtie, horns, wings, spikes, fangs, extra heads,
     propeller, jetpack, thrusters, laser, cannon, armour, shield, crack, bandage, stitches, bolts, gears, tears,
     sweat, drool, blush;
   - re-tint: zombie, skeleton, ghostly, cursed, rainbow, glow, disco, and pixel (which makes everything voxel);
   - request an effect (`Effects.play` id): steam, snore, sparkle, stars, hearts, notes, question, flames, frost
     and others.

   Mouth accents (scowl, smile, snore…) set the face mood when the result's mood is Neutral. Unknown ids do
   nothing.
5. **Style.**
   - **Solid:** colours come from the word's own colours, and the material's colour and Roblox material win.
   - **Spectral:** each big mass becomes a ForceField shell with a smaller Neon core. Other parts get layered Neon
     transparency. A Spectral summon gets a Highlight, Trails on extremities, element particles and a core
     PointLight.
   - **Split element:** when `secondaryElement` is set, the left half takes the second element's palette, and
     the second element adds its own particles.
6. **Finishing passes.**
   - fit the part budget by priority (mirrored pairs stay together, and dependent parts go with what they need);
   - prune bones that have no parts;
   - scale to `SummonHeight[size]`;
   - run the **z-fighting fix pass**;
   - give parts unique names;
   - apply the FX budgets.

## Materials and how each one builds

Material records come from `Library.material(id)` (`data/materials.json`, 250 records). If that has nothing, the
builder tries the material provider, then a built-in fallback table. `opts.material` overrides all of them.
Materials apply to plans and signatures, in both styles.

| Construction | What the builder does | Examples |
|---|---|---|
| Solid | Changes colour and Roblox material only; some materials add extras | gold, wood, cheese (holes, wedge hull) |
| Strands | Shrinks the core and wraps it in twisted strand plies | spaghetti (sauce core, sauce drips, meatball eyes), yarn, rope |
| Woven | Puts alternating bands around each mass | wicker, chainmail |
| Bricks | Tiles staggered blocks over mortar | brick, stone, toy bricks |
| Panels | Makes masses boxy, with proud plates, plus rivets on metal | cardboard, metal, screens |
| Wobble | Makes it see-through, with bits suspended inside; it jiggles when animated | jelly, slime |
| Swarm | Turns masses into clusters of small units | a bee wall made of bees |
| Shards | Makes a faceted core with wedges sticking out | glass (see-through), crystal, ice |
| Inflated | Makes it round and shiny, with a knot | balloons, wool, cloud |
| Pile | Heaps items over a core | coins, popcorn, googly eyes (with pupils) |
| Liquid | Makes it smooth and see-through, with drips | water, lava |
| Energy | Makes it Neon, with zig-zag arcs | lightning, magic |

Rules that apply to every material:
- **Priority.** Material detail ranks just below the eyes, so the face always survives a tight budget.
- **Motion.** Each material sets a motion style in `rig.materialMotion`: wobble, flop, clank, bob, jiggle, swarm
  or flicker.
- **Particles.** The material's particles use the Effects ids.

## Faces

- **Who gets a face.** Creatures always get one. Objects get one only when the mood is not Neutral, or the tags
  include silly or cute. A plain object stays clean.
- **Mood.** `result.mood` drives the expression: eye shape, pupils, lids, brows, mouth, tongue, teeth and blush.
  There are 14 moods (Face.Expressions).
- **Small budgets.** At detail 0–1 the eyes outrank secondary limbs.

## Signatures

There are 21 hand-built signatures:
- **Creatures:** dragon, shark, t rex, phoenix, kraken, golem, cat, dog, bee, octopus, unicorn, glitter blob.
- **People:** robot, wizard, knight.
- **Machines and buildings:** pirate ship, tank, castle, rocket, ufo, cannon.

How a word finds its signature:
- It matches on the id, then the synonym group, then a suffix match whose body plan agrees. So "ice dragon" uses
  the dragon, but "hot dog" does not use the dog.
- A signature recolours to the word's own colours and element. Materials, moods and accents apply on top, so
  "spaghetti dragon" is the dragon woven from noodles.
- A signature can also be backed by an uploaded mesh (see `docs/platform/summon.md`).

## Part counts

These are measured over all 60 plans at seed 1, as average and maximum parts. The budget is in brackets; a
signature can go 25% over it.

| Size | Solid avg / max | Spectral avg / max |
|---|---|---|
| Tiny (8) | 6.2 / 10 | 7.2 / 10 |
| Small (12) | 8.2 / 15 | 8.9 / 15 |
| Medium (20) | 12.6 / 25 | 14.1 / 25 |
| Large (30) | 16.2 / 37 | 18.1 / 37 |
| Huge / Colossal (40) | 17.5 / 50 | 19.8 / 50 |

Other budgets:
- **FX:** 2 emitters in Solid and 3 in Spectral, at most 60 particles/s each; 4 trails; 1 light; 2 or 3 looping
  effects.
- **Formations:** a formation with count above 1 shares 2 budgets across its members, with at least 5 parts per
  member.

## QA

- **`lune run tests`.** `summon.spec` covers:
  - determinism, budgets and FX budgets;
  - signatures, and materials changing how things are built;
  - the material provider chain;
  - faces for all moods, accents (every canonical id) and the split-element look;
  - unit cases for the checker and fixer;
  - Motion curve math, and Instantiate under `@lune/roblox`.

  `summon_zfight.spec` runs the zero-violation sweep. `SUMMON_SEEDS=n` shortens it.
- **`lune run tools/gallery [n] [seed] [outdir]`.** Renders 320 random base × material × modifier phrases in both
  styles to `docs/img/gallery_*.png`, and flags builds that are:
  - too few parts;
  - boxy creatures;
  - low contrast;
  - missing a face;
  - z-fighting;
  - over budget;
  - invisible.

  The worst builds go in `gallery_flagged.png`.
- **`lune run tools/render_blueprint ...`.** Renders single plans, all plans, special plans, signatures,
  phrases, one material, or the contact sheet (`docs/img/summons_contact_sheet.png`).
- **`testplace/Gallery`.** The Roblox client gallery shows the same phrases and signatures, Solid and Spectral
  side by side, animated, with flags shown on labels. Keys:
  - G: new seed;
  - M: switch between move and idle;
  - F: attack;
  - H: hit;
  - P: spawn.
