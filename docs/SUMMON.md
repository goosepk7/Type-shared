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
   - **Spectral:** the silhouette stays solid. Body, head and torso masses, limbs, necks, tails, wings, horns and
     held / worn parts are near-opaque SmoothPlastic in the element's colours (wing membranes and fins at most
     0.25 transparent); only small detail is layered Neon, and pure energy (orb cores) keeps the ForceField shell
     around a smaller Neon core. Glow is an accent: one ForceField aura shell on the biggest mass, the Highlight
     rim, glowing eyes, Trails on extremities, element particles and a core PointLight. (A body made of faint
     shells around small cores read as a firefly, not a dragon.)
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

## Plan notes

- **Quadrupeds** pick a head archetype from the id (`Heads.Arch`): canine, feline, ursine, equine, bovine,
  porcine, rodent, plus reptile, bird (beak) and pachyderm fallbacks from traits. Each archetype sets body
  proportions, neck, snout, nose, ears, tail and coat marks (stripes, spots, panda patches). Posture is horizontal,
  with the head carried forward on a short neck.
- **Orbs** have a distinct build per kind: fireball/meteor (hot core, flame shell, licks, trail), planet (bands as
  separate shells, rings, craters), earth, sun, moon, magic orb (rune ring on a rotor), plasma, frost, boulder,
  void, bomb, bubble. Food words go to the Blob food builders.
- **Structures:** towers have a plinth, machicolations, merlons, a 4-wedge roof with staggered lifts, and framed
  windows and doors set back from the wall. Portals stand on a plinth with a keystone, a turning vortex and runes.
  Nothing decorative is flush with a face: insets and proud details are always offset.
- **Swarms** have hero units in front (full detail: bee bands and wings, bat membranes, firefly bodies) and a
  depth-sorted cloud of cheaper fillers.
- **Spectral** masses are solid; the biggest one gets a ForceField aura shell of strictly larger radii, and orb
  cores keep a ForceField shell around a strictly smaller Neon core.
- **Bat / dragon wings** are an arm (two bones) plus ONE membrane per side in the plane of the spread wing
  (`Membrane`, sculpt `s_wing_bat`), budgeted right after the upper arm so a dragon never loses its wings.
- **Vortex** (tornado): every funnel ring is its own rotor under Body (`rig.rotors`), odd rings one way and even
  rings the other at different speeds; rings are oval, off-axis and carry wind streaks so the rotation reads;
  two counter-orbiting debris rings at the base; streak, wisp and dust emitters and trails ride the spinning
  parts. The ring that carries a face does not spin.

## Faces

- **Who gets a face.** Creatures always get one. Objects get one only when the mood is not Neutral, or the tags
  include silly or cute. A plain object stays clean.
- **Mood.** `result.mood` drives the expression: eye shape, pupils, lids, brows, mouth, tongue, teeth and blush.
  There are 14 moods (Face.Expressions).
- **Small budgets.** At detail 0–1 the eyes outrank secondary limbs.
- **Contrast.** In Solid, dot eyes that would melt into a dark (or mid-tone) head are swapped for bright (or
  near-black) ones.
- **Accents stay visible.** Each accent's lead part is lifted to just below the face, so a modifier outranks plan
  dressing such as ears, tails and spines.

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

## Sculpted meshes

Blueprint parts carry an optional piece id (`part.mesh`) from the shared mesh library
(`src/Shared/Meshes`, sculpted by `tools/meshgen`). `Instantiate` shows the piece as a MeshPart when its asset is
loaded and builds the primitive otherwise, so the primitive build is always the complete fallback.

- **Choosing pieces is pure data.** `Summon/MeshMap.luau` runs after the plan: (1) hints from the generator
  (`mesh = "id"` on a part spec, `mesh = false` to opt out, `B:sculpt(lead, id, members)`), (2) hero pieces by
  role + name + shape (`MeshMap.Hero`: rocket body, nose, nozzle, gun barrel, muzzle, treads, saucer, tower drum,
  roof cone, mantle, wizard hat, beard, robe, helmet, pauldron, rocks, rain drops, flame licks, sword blade) and
  by name (`MeshMap.Named`: cloud puffs, canopies, turret ...), (3) role + shape rules (limbs, tails, horns,
  claws, teeth, fins, ears, feathers, fists, hooves, wheels) and bevelled blocks / cylinders for every other
  hard-surface part. Nothing random is drawn, no part moves: `Summon.blueprint(r, { meshes = false })` gives the
  identical primitive build without mesh fields, and `stats.meshParts` counts the sculpted parts.
- **Fit.** A box piece fills the part's box (MeshPart.Size = part size). Head and body sculpts are *unit*
  pieces authored in the lead ellipsoid's unit frame, so they scale with every seed and size; the sculpt contains
  the lead ellipsoid untouched where the face goes, so eyes, lids and mouths sit on it. Primitives a sculpt
  absorbs (snout, chest, haunch, lower beak) are its group members (`part.meshOf = lead name`): they are built
  only while the lead's primitive is shown. Left copies of mirrored pairs use the `_l` twin of asymmetric pieces.
- **Materials and accents.** Pieces carry only greyscale baked AO in vertex colour, which multiplies
  `MeshPart.Color`: palette colours, Roblox materials, moods and faces are unchanged. Materials that rebuild a
  surface out of units (strands, weave, bricks, panels, swarm, shards, pile) and accents that reshape a part keep
  the primitive (`MeshMap.validate`); a sculpt group falls back as a whole. Faces (eyes, pupils, brows, lids,
  mouths), glows, cores, shells, rings and paper-thin or translucent sheets are never meshed.
- **Spectral.** The sculpt is the solid body; the ForceField aura (and the Neon core of an orb shell) reuse the
  piece at their own, distinct sizes, so no two layers are coincident.
- **Loading.** `Summon.preloadMeshes()` (or the first build) starts `MeshLibrary.preload` for the "summon" set plus
  `MeshMap.Shared` pieces of the "td" set. It never yields a build: a model built early has
  `MeshPending = true` and `Instantiate.upgradeMeshes(model)` swaps its parts when the library is ready (wired
  automatically in a live game). `opts.meshes = false` forces primitives.
- **Z-fighting.** The checker keeps testing every part as its primitive, which is what the fallback renders, and
  that verdict covers the mesh build: box pieces that keep flat faces (bevelled blocks, cylinders, treads, tower
  drums; listed per piece as `flat` in the manifest) keep them exactly on the primitive's faces, so two meshes
  are coplanar only where their primitives were; organic and unit sculpts have no planar box faces, they sit
  inside or bulge slightly past the primitive's curved surface, where surfaces intersect at an angle instead
  of lying coincident. A mesh next to a still-primitive neighbour is the same case.
- **Budgets.** 107 summon pieces, 70.8k triangles in total; a generic piece costs 20-1500 triangles, a hero piece up to
  3200 (blocks about 300,
  limbs about 300, heads 600-1300, bodies up to 1500). The part budget already caps a summon's part count, and
  sculpt groups remove parts, so a 50-part hero stays under about 20k triangles.
- **Hero sculpts.** Signature heroes are one coherent model sculpted in model space on the signature's reference
  build (`tools/meshgen/refs.json`) and then cut along the rig, one unit piece per bone, so the Animator still
  moves every joint (joints are overlapping balls):
  - *dragon* (`catalogue/s_dragon.py`, 17 pieces, 19.9k triangles, about 22k with the wings): body, belly and breast
    plates, neck with throat scutes and dorsal fins, skull, jaw, horn crown, four two-piece legs with clawed feet,
    three tail pieces ending in a barbed spade, plus the `s_wing_bat` membranes;
  - *shark* (`s_fx.py`): trunk with overhanging snout, tail stock with keels and small fins, crescent caudal
    fin, swept dorsal fin; the pale Belly primitive stays a separate part in a recess of the trunk;
  - *tornado*: every funnel ring is an `s_funnel` auger with three helical ridges (the per-ring rotors make it a
    barber pole), `s_streak` wind ribbons, boulder debris;
  - *asteroid / meteor*: `s_asteroid` (rimmed craters, chipped facets) leading the Rock blocks, `s_blaze` flame
    shroud and wake; *black hole*: `s_accretion` pinwheel discs.
  Each hero lead carries `heroSet`; when a material or accent takes any piece of a set back to a primitive
  (spaghetti dragon, glass shark), `MeshMap.validate` steps the WHOLE set down to the generic role / shape pieces,
  so sculpted and primitive pieces of one hero never mix.
- **Offline.** `lune run tools/render_blueprint hero <words> out.png` draws Solid primitives, Solid sculpt and
  Spectral sculpt next to a 5 stud figure (`docs/img/hero_*.png`); `lune run tools/render_blueprint beforeafter out.png` ray-traces the same blueprints with and
  without the pieces (`docs/img/mesh_before_after.png`); `scale <style> <words> out.png` draws summons next to a
  5 stud character-height figure (`docs/img/spectral_scale.png`); the contact sheet shows the mesh build
  (`SUMMON_MESH=0` for primitives). `tests/specs/mesh.spec.luau` checks the manifest, that every referenced
  piece exists, determinism, and both Instantiate paths.

## Part counts

These are measured over the generic plans (one variant each) at seed 1, as average and maximum parts. The budget
is in brackets; a signature can go 25% over it.

| Size | Solid avg / max | Spectral avg / max |
|---|---|---|
| Tiny (8) | 6.9 / 8 | 7.6 / 8 |
| Small (12) | 10.1 / 12 | 10.1 / 12 |
| Medium (20) | 15.4 / 20 | 16.7 / 20 |
| Large (30) | 21.5 / 30 | 23.1 / 30 |
| Huge / Colossal (40) | 23.1 / 40 | 25.8 / 40 |

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
  phrases, one material, exemplar sheets (`quads`, `orbs`, `builds`, `swarms`), or the contact sheet
  (`docs/img/summons_contact_sheet.png`). The renderer is flat-shaded with a camera-side key light, blends
  translucent parts properly, draws ForceField and Neon parts additively with bloom, and draws the Spectral
  Highlight outline.
- **`testplace/Gallery`.** The Roblox client gallery shows the same phrases and signatures, Solid and Spectral
  side by side, animated, with flags shown on labels. Keys:
  - G: new seed;
  - M: switch between move and idle;
  - F: attack;
  - H: hit;
  - P: spawn.
