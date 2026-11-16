# "Made of" materials

`data/materials.json` holds the material library: **250 materials**, one `Types.Material` record each. A material
turns *any* base thing into a version of it made of that stuff: "spaghetti dragon", "dragon made of spaghetti",
"glass shark", "bee wall", "cheese tank", "toilet paper mummy". It changes five things:

1. how the thing **looks**: palette, `robloxMaterial`, transparency, glow, optional `accents`
2. how it's **built**: `construction`
3. its **particles**: Effects-library ids, tinted by the palette
4. its **sound**: `sound`
5. a **gameplay effect**: `hooks`, `statHints`, `element` affinity, and the reaction `tags` that
   `data/material_reactions.json` keys on

Validate with `python3 tools/validate_materials.py` (`--stats` prints the distributions, `--words` lists overlaps with
the word library). The compiler is `tools/build_library.py` → `Materials.luau`.

## Record format

```json
{"id":"spaghetti","family":"Food","aliases":["pasta","spaghet","linguine"],"palette":["#F2C46D","#E8B04B","#C8361F","#F7E3A3"],
 "robloxMaterial":"SmoothPlastic","transparency":0,"glow":0,"construction":"Strands","particles":["drip_sauce","steam"],
 "sound":"squelch","element":"None","tags":["edible","organic","sticky","soft","savory","smelly"],
 "hooks":["Tangles","EdibleLure","Sticky"],"statHints":{"speed":-1,"durability":-1},
 "ms":["spagetti","spaghettti","sphagetti","spagehtti"],"accents":["drip"]}
```

| key | rule |
|---|---|
| `id` | lowercase canonical, at most 24 chars (Schema clamps `WordResult.material` to 24) |
| `family` | `Food` / `Natural` / `Manufactured` / `Weird` |
| `aliases` | plurals, synonyms, regional spellings. Unique across every material id, alias and `ms` |
| `ms` | 1-4 likely typos (`lightening`, `spagetti`, `marshmellow`). Unique, and never a modifier word |
| `palette` | 2-5 `#RRGGBB`. `[1]` is the body, `[2]` the secondary/trim, `[3+]` accents (sauce, sprinkles, stitches) |
| `robloxMaterial` | a BasePart `Enum.Material` name. Air and Water are terrain-only and rejected |
| `transparency` | 0..0.95. Glass-likes are 0.15-0.45, wisps 0.4-0.6 |
| `glow` | 0..1: the PointLight brightness and neon-rim weight. Energy materials are ≥ 0.3 |
| `particles` | 1-3 ids from the Effects library (list below) |
| `sound` | a sound key (list below) |
| `element` | the affinity for element reactions (lava = Fire, ice = Ice, copper = Lightning). Most are `None` |
| `tags` | ≤ 8 (the compiler keeps 8). Always includes the applicable **reaction tags** |
| `hooks` | 1-4 gameplay hooks (list below) |
| `statHints` | non-zero ints in -2..+2, sum ≤ 2. Materials add flavour, not upgrades |
| `accents` | optional, ≤ 3 summon-builder accent ids (`drip`, `sparkle`, `stitches`, `bolts`, `spikes`...) |

## Families (250)

- **Food (66):** spaghetti, noodles, macaroni, cheese, jelly, chocolate, bread, toast, pizza, candy, candy cane, gummy,
  jellybean, ice cream, bacon, cake, cookie, donut, popcorn, marshmallow, gum, honey, honeycomb, pudding, sushi, waffle,
  pancake, cereal, sprinkles, cotton candy, caramel, peanut butter, sausage, meat, burger, taco, watermelon, banana,
  pickle, broccoli, carrot, potato, french fries, egg, butter, soup, milk, sugar, gingerbread, pretzel, frosting,
  whipped cream, lollipop, licorice, tofu, popsicle, pie, grapes, pumpkin, coconut, chili, cheesecake, croissant,
  muffin, strawberry, cinnamon roll
- **Natural (60):** wood, planks, bamboo, stone, cobblestone, marble, granite, pebbles, sand, mud, clay, dirt, leaves,
  grass, hay, flowers, vines, moss, mushroom, cactus, thorns, crystal, amethyst, ruby, sapphire, emerald, diamond,
  gemstone, pearl, coral, shell, feathers, fur, wool, cloud, storm cloud, smoke, fire, ash, steam, fog, pinecone,
  seaweed, meteorite, lava, magma, obsidian, basalt, sandstone, slate, salt, amber, ice, glacier, snow, water, tar,
  cobwebs, acorns, bark
- **Manufactured (74):** metal, steel, iron, scrap metal, gold, silver, bronze, copper, chrome, titanium, tin foil,
  armor, chainmail, chains, nuts and bolts, gears, circuits, neon, wire, glass, stained glass, plastic, **toy bricks**
  (generic; brand names are banned and the validator rejects them), rubber, tires, bouncy balls, cardboard, paper,
  origami, newspaper, sticky notes, balloons, pillows, plush, yarn, rope, denim, velvet, silk, leather, carpet, cotton,
  socks, toilet paper, duct tape, bubble wrap, foam, sponge, soap, slime, glue, paint, ink, crayon, chalk, play dough,
  marbles, wax, porcelain, tiles, concrete, brick, pipes, springs, magnets, paperclips, cutlery, drinking straws,
  glow sticks, fairy lights, tinsel, screens, pencils, pasta shapes
- **Weird (50):** lightning, electricity, shadow, light, void, bees, ants, butterflies, fireflies, flies, worms,
  spiders, tentacles, coins, cash, eyeballs, googly eyes, teeth, bones, skulls, sock puppets, mustaches, hair,
  rubber ducks, glitter, stars, rainbows, bubbles, ghosts, ectoplasm, mirrors, pixels, static, glitch, dice, buttons,
  playing cards, confetti, music notes, hearts, keys, fireworks, clocks, question marks, snot, crowns, trophies, magic,
  nightmares, dreams

## Construction kinds: how the summon builder builds each one

Build order (DESIGN §8): **body plan → material construction → modifiers.** The body plan gives a set of **body
volumes** (torso, head, limbs, tail, wings: each one an oriented box/capsule plus a centre-line curve). Construction
decides how each volume is filled. Every kind has to keep the body plan's silhouette readable, stay inside the part
budget (Small 12 / Medium 20 / Large 30 / Huge 40), and follow the **no z-fighting rule**: touching parts are inset by
`Config.Visual.Inset` (0.02 studs) or meet at non-coplanar angles. Repeated elements are never placed flush on a face.

| kind | count | build recipe |
|---|---|---|
| **Solid** | 44 | One part per body volume in `robloxMaterial`, colour `palette[1]`, trim/accent parts in `palette[2]`. Rounded volumes use Ball/Cylinder or a SpecialMesh, never stacked flush blocks. Surface features (cheese holes, watermelon seeds, magma cracks) are *recessed* child parts sunk by `Inset`, or Decals at `DecalOffset`. |
| **Strands** | 33 | Replace each volume with 3-7 tube chains that follow its centre-line curve (spaghetti, vines, wire, chains, hair, tentacles). A chain is 4-8 short cylinders with ball joints. Neighbouring strands get a radial offset of at least their radius plus `Inset`, and a twist phase so they never overlap coplanar. Free ends dangle 1-2 segments past the volume and sway in `animate`. Flat-ribbon variants (bacon, silk, toilet paper) use thin boxes rotated 15-30° per segment. |
| **Bricks** | 16 | Voxelise each volume at a grid of about volume/4 (minimum 2 per axis), keep only the cells inside the volume, and merge runs along the longest axis to save parts. Toy bricks get studs: cylinders on top faces, raised `Inset` above the face and inset from the edges, never coplanar. Chocolate/tiles get bevel grooves, made by shrinking each cell by 2×`Inset` so the gaps read as mortar. Pixels/glitch use pure cubes with no studs, and glitch jitters cells every 0.2 s. |
| **Panels** | 35 | Shell the volume with 4-8 thin plates (thickness 0.1-0.2) tilted 5-12° off the surface like shingles or armour, overlapping by offset rather than coplanar contact. Cardboard and paper show folded flaps on the edges, metal and armour show rivets (`bolts` accent), cookies, pancakes and pizza stack discs, and feathers and pinecones fan scales tail-ward. |
| **Wobble** | 15 | One rounded part per volume with Glass/SmoothPlastic and transparency, plus jiggle bones: in `animate`, scale each part on a damped spring (squash Y by -15%, stretch XZ by +8%, about 6 Hz, damping 0.35) driven by movement and hits. Add an inner core part (smaller, `palette[2]`, inset by ≥ 0.1) for depth in transparent jellies. Drips (`drip` accent) hang from the lowest points. |
| **Swarm** | 19 | No solid body. A ParticleEmitter or attachment cloud fills each volume's shape (bees, leaves, confetti, smoke, stars): 8-20 small instanced meshes/billboards orbit points sampled inside the volumes on noise paths. The silhouette must still read as the base thing. Keep the head volume densest and give eyes their own anchored parts so the face stays readable. On a hit, a few members scatter and return (`Splits`). |
| **Shards** | 11 | Build each volume from 3-6 faceted wedges/prisms (crystal, glass, diamond, obsidian, mirrors) pointing outward from the centre-line at varied angles. No two shard faces share a plane (random roll of ±8°). Add a bright inner glow part when `glow` ≥ 0.3. On death, shatter into the `shards` particle. |
| **Inflated** | 18 | Volumes become overinflated rounded lobes: balls and capsules scaled 1.15× with pinched joints (balloons twist at joints like balloon animals, bread and marshmallows puff, pillows show a centre seam). Idle "breathing" scale ±3%. Joints use a small knot part instead of overlapping lobes. |
| **Woven** | 8 | Volumes are covered with a crossing lattice of thin strips: two families of strips at ±45° with alternating radial offsets (over/under) so crossings never coincide. Lattice pies, chainmail rings, cobwebs, carpet and duct tape use it. The interior is a darker core part inset by ≥ 0.1. |
| **Pile** | 30 | Each volume is a heap of 5-12 small items (popcorn, coins, pebbles, socks, dice, rubber ducks), jittered in position and rotation and packed to its silhouette. Items overlap by interpenetration at random angles, never by face contact. Merge into fewer, larger items to stay on budget. Items fall off on hit and the summon regrows them (`Splits`/`Regenerates`). |
| **Liquid** | 10 | A smooth rounded body (high-poly SpecialMesh sphere/capsule per volume) with transparency, a flowing surface (a texture scrolling down slowly), drips and puddles at its base. The puddle is a cylinder 0.05 above ground, never at Y = ground. The silhouette softens: edges round off and limbs taper into flows. |
| **Energy** | 11 | Neon/ForceField cores with additive outer shells (core 0.6× scale, shell 1.0× at transparency 0.5+), element-gradient Beams along the centre-lines, flicker in `animate` (fire tongues, lightning arcs between joints, shadow wisps). The core and shell are concentric, never coplanar. |

### Spectral vs Solid style

- **Solid (Type to Defend):** follow the table literally with the listed `robloxMaterial`.
- **Spectral (Typing Wizards):** keep the **construction** (the shape language is what makes "spaghetti dragon" read),
  but render every part as Neon/ForceField, with the palette pushed toward glow. Strands become glowing noodle tubes,
  Bricks glowing voxels, Swarm a sparkling particle body. Raise `glow` to at least 0.5 and add the element-gradient
  Beams.

### Picking `palette` by role

`palette[1]` is the body, `[2]` trim, inner cores, strand alternates or icing, `[3]` and later are accent bits (sauce,
sprinkles, seeds, gems). Multi-colour Pile/Swarm materials (jellybean, confetti, bouncy balls) cycle through the
whole palette.

## Particles (Effects library ids)

`drip_sauce, drip_honey, goo_drip, water_drip, ink_drip, sawdust, crumbs, sprinkles, sparkle, glitter, confetti, bees,
flies, butterflies, shards, steam, smoke, embers, sparks, zap, frost, snowflakes, bubbles, petals, leaves, feathers,
fluff, sand, dust, coins, music_notes, hearts, snore, anger_steam, sweat_drops, thruster, glitch, rainbow_trail, stars,
question_marks, halo_glow`

Particles are tinted by the palette: `drip_sauce` on chocolate is brown, on paint it's multicolour, on lava it's
orange. Materials list 1-3 ids, and the summon emitter budget (2, or 3 in Spectral) takes them in order.

## Sounds

`squelch, clank, crinkle, crunch, boing, buzz, slosh, shatter, rustle, thud, sizzle, jingle, squeak, squish, pop,
hiss, crackle, creak, chime, whoosh, flutter, rattle, slurp, snap, rumble, hum, blip, moan, rip, splat, tick, click,
boom, melody, whisper, clack, gong, poof, flop, scratch, skitter, chatter`

Sounds play on spawn, on footsteps or movement (quieter), and on hit. The material sound layers *under* the base
thing's `soundHint` (a spaghetti dragon still roars, with a squelch).

## Gameplay hooks

The engine only says what a material is. Each game maps the hooks to numbers.

| hook | meaning (suggested use) |
|---|---|
| Bounces | knockback on contact, bouncy movement, ricochets |
| ShattersOnHit | low HP but bursts into damaging shards on death |
| EdibleLure | enemies are drawn to it / stop to eat it (tower defense: a taunt) |
| BurnsFast | takes extra Fire damage and spreads burning |
| Durable | extra HP / armour |
| Slow / Fast | movement or attack speed |
| DamageAura | small damage around it (thorns, bees, stink, heat) |
| Conductive | chains Lightning to nearby targets, takes Lightning bonus |
| Tangles | roots or slows what it touches (strands, ropes, webs) |
| Sticky | leaves a slow puddle, holds targets briefly |
| Slippery | enemies slide or trip near it, harder to grab |
| Heals | small heal or regen to allies nearby |
| Reflects | reflects a portion of projectiles / beams |
| Floats | hovers over ground hazards and water |
| Melts | weak to Fire and heat, leaves a puddle when destroyed |
| Absorbs | soaks a portion of damage or liquids (pillows, sponge) |
| Explodes | bursts on death (popcorn, balloons, fireworks) |
| Regenerates | slowly regrows lost pieces or HP |
| Blinds | obscures vision / reduces enemy accuracy |
| Distracts | pulls enemy attention or aggro |
| Light / Heavy | light = fast and fragile, floats easily. Heavy = slow, knockback-resistant, stomps |
| Splits *(ext.)* | pieces break off as mini-minions or scatter and reform (swarms, piles, dice) |
| Phases *(ext.)* | can pass through walls or projectiles briefly (ghosts, smoke, shadow) |
| Lucky *(ext.)* | random crit or bonus (dice, coins, cards) |
| Poisons *(ext.)* | applies poison on hit (mushroom, spiders) |
| Scares *(ext.)* | fear: enemies flee briefly (skulls, eyeballs, nightmares) |
| Pulls *(ext.)* | drags nearby enemies in (magnets, void) |

## Reaction tags

`data/material_reactions.json` keys on these tags, so every applicable one is included: `flammable, edible, meltable,
conductive, absorbent, brittle, frozen, sticky, liquid, metal, wood, paper, plastic, rubber, glass, stone, cloth,
organic, living`. Examples: fire melts `meltable` cheese and ice, burns `flammable` wood and cardboard, water ruins
`paper`, lightning conducts through `metal`/`conductive`.

## Overlaps with modifier words

71 material words are also words in `data/modifiers.json`, for example fire, ice, lava, stone, metal, gold ("golden"),
crystal, diamond, glitch, rainbow, ghost, mustache, rubber and shadow. This is expected. Per DESIGN §5a the parser
decides by context: "golden dragon" applies the Quality modifier, "dragon made of gold" applies the gold material.
`python3 tools/validate_materials.py` lists them all. Misspellings are never allowed to be modifier words.

## Authoring rules

- Each material must plausibly build **any** base thing: a creature, a vehicle, a wall, a weapon. If it only makes
  sense for one shape, it is a thing, not a material.
- No brands or trademarks. "toy bricks", never the brand; "play dough", "foam", "bouncy balls" stay generic. The
  validator's `BANNED` set catches the common ones.
- Keep it kid-safe and funny. Gross-funny (snot, socks, eyeballs) is fine. Gore is not.
- Add new materials to `data/materials.json` (one per line), then run the validator until it prints `OK`.
