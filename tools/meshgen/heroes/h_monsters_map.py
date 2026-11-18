"""Word -> hero rules for the monsters / spirits / constructs / apes families, kept in one hero-less module so a
mapping tweak never invalidates the mesh cache of the sculpt files (build.py hashes each h_ file)."""

# category / body-plan filters
_CATS = ["Creature", "Machine", "Object", "Abstract", "Element", "Person", "Plant", "Structure"]
HUMANOID = {"cat": _CATS, "bp": ["Humanoid", "Giant", "Ghost", "Biped", "Blob", "Robot"]}
SPIRIT = {"cat": _CATS, "bp": ["Humanoid", "Giant", "Ghost", "Biped", "Blob", "Cloud", "Orb", "Swarm"]}
BLOBBY = {"cat": ["Creature", "Element", "Abstract", "Object", "Plant", "Machine"], "bp": ["Blob", "Humanoid", "Orb", "Ghost"]}
WISPY = {"cat": ["Creature", "Element", "Abstract", "Object"], "bp": ["Orb", "Humanoid", "Ghost", "Blob", "Swarm", "Plant"]}
PLANTY = {"cat": _CATS, "bp": ["Humanoid", "Giant", "Plant", "Biped"]}
MACHINE = {"cat": ["Machine", "Creature", "Object", "Abstract", "Person"], "bp": ["Humanoid", "Robot", "Giant", "Biped"]}
ANIMALS = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Plant", "Person"], "bp": ["Biped", "Quadruped", "Humanoid", "Giant"]}
HYBRID = {"cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Person"], "bp": ["Humanoid", "Quadruped", "Fish", "Giant", "Biped"]}

MAP = [
    # ------------------------------------------------------------------ monsters (h_monsters.py)
    ("goblin", "goblin, goblins, hobgoblin, goblin archer, goblin bomber, goblin pirate, goblin tinkerer, goblin king, goblin queen, goblin shaman, "
               "redcap, gremlin, moon goblin, boggart, toyol, kobold, dokkaebi, knocker, tokoloshe, lutin, clurichaun", HUMANOID),
    ("orc", "orc, orcs, half orc, half-orc, orc warlord, orc shaman, orc archer, orc queen, uruk, bugbear, gnoll, ratfolk, wererat", HUMANOID),
    ("ogre", "ogre, ogres, ogre mage, ogre chef, ettin, ettin brute, fomorian, zombie giant", HUMANOID),
    ("troll", "troll, trolls, cave troll, ice troll, bridge troll, river troll, moss troll, troll shaman, troll king, two headed troll, "
              "bog troll, ghoul", HUMANOID),
    ("cyclops", "cyclops, cyclopes, cyclops baby, cyclops blacksmith, likho, hill giant, argus, hitotsume-kozo, hitotsume kozo", HUMANOID),
    ("minotaur", "minotaur, minotaurs, minotaur chief, minotaur gladiator, bull man, tikbalang", HUMANOID),
    ("satyr", "satyr, satyrs, faun, fauns, pan, satyr bard, krampus", HUMANOID),
    ("demon", "demon, demons, devil, devils, fiend, archdemon, demon lord, balrog, ifrit demon, rakshasa, oni, blue oni, mothman, gargoyle demon", HUMANOID),
    ("imp", "imp, imps, fire imp, ice imp, shadow imp, akaname, sasabonsam, mananangal", HUMANOID),
    ("werewolf", "werewolf, werewolves, werewolf alpha, lycan, lycanthrope, wolfman, wolf man, wulver, anubis guardian, werebear, werecat, werefox, tabaxi, wendigo, big bad wolf", HUMANOID),
    ("lizardman", "lizardman, lizard man, lizardfolk, lizard folk, dragonborn, kobold dragonkin, lizard man of the swamp, loveland frogman, kappa", HUMANOID),
    ("fishman", "fishman, fish man, fishfolk, deep one, deep one priest, vodyanoy, wereshark, sahuagin", HUMANOID),
    ("alien", "alien, aliens, grey alien, gray alien, martian, little green man, alien soldier, alien scientist, alien overlord, cyclops alien, "
              "space pirate alien, mind control alien, space cowboy alien, alien gladiator, four armed alien, four-armed alien, moon man, dover creature, flatwoods monster, alien invader", HUMANOID),
    ("mummy", "mummy, mummies, pharaoh mummy, mummified, draugr, jiangshi", HUMANOID),
    ("skeleton", "skeleton, skeletons, skeleton archer, skeleton king, skeleton warrior, skeleton mage, skeleton pirate, skeleton cowboy, "
                 "skeleton samurai, gashadokuro, revenant, bone warrior, dry bones", HUMANOID),
    ("yeti", "yeti, yetis, abominable snowman, yeti king, yeti family, cookie beast, tickle monster, closet monster, monster under the bed, snowman monster", HUMANOID),
    ("bigfoot", "bigfoot, sasquatch, bigfoot chief, bigfoot family, yowie, skunk ape, mapinguari", HUMANOID),
    # ------------------------------------------------------------------ hybrids (h_monsters_hybrid.py)
    ("centaur", "centaur, centaurs, centaur archer, sagittarius", HYBRID),
    ("mermaid", "mermaid, mermaids, merman, mermen, merfolk, mermaid queen, mermaid princess, siren, siren queen, sea maiden, naiad, triton, rusalka, nixie", HYBRID),
    # ------------------------------------------------------------------ spirits (h_spirits.py)
    ("ghost", "ghost, ghosts, poltergeist, spook, phantom, specter, spectre, ghost child, disco ghost, cyber ghost, ghost king, headless ghost, "
              "mirror ghost, ghost slime, ghost lantern bearer, ghost pirate captain, ghost ship crew, it, !tag you", SPIRIT),
    ("wraith", "wraith, wraiths, shade, shadow man, living shadow, bogeyman, dementor, ice wraith, bog wraith, sand wraith, soul eater, wight, strigoi, "
               "mare spirit, el silbon, specter knight, shadow elemental, void walker, death knight spirit, shadow giant", SPIRIT),
    ("grim reaper", "grim reaper, reaper, death, crypt keeper", SPIRIT),
    ("lich", "lich, liches, lich queen, lich king, koschei, ghoul king", SPIRIT),
    ("banshee", "banshee, banshees, banshee queen, la llorona, ghost bride, yuki onna, white lady, weeping ghost, vila", SPIRIT),
    ("fire elemental", "fire elemental, flame elemental, ifrit, fire spirit, flame spirit, magma titan, lava elemental, fire giant, ember elemental, "
                       "blaze elemental, inferno elemental, djinn, djinn king", SPIRIT),
    ("water elemental", "water elemental, marid, undine, ocean spirit, water spirit, tide elemental, nymph, sea spirit, genie lamp spirit, umibozu", SPIRIT),
    ("earth elemental", "earth elemental, rock monster, stone colossus, mountain giant, rock elemental, stone elemental, earth spirit, rock giant, "
                        "crystal elemental, crystal giant, sea giant", SPIRIT),
    ("ice elemental", "ice elemental, frost elemental, frost titan, frost giant, frost spirit, ice spirit, crystal golem lord, ice sculpture golem, ice golem", SPIRIT),
    ("lightning elemental", "lightning elemental, storm elemental, thunder elemental, storm titan, raijin, fujin, storm spirit, thunder spirit, "
                            "plasma being, storm giant, cloud giant king, arcane elemental", SPIRIT),
    ("wisp", "wisp, will o the wisp, will-o-the-wisp, will o wisp, wisps, sprite, ember sprite, water sprite, light sprite, shadow sprite, wind sprite, "
             "ice sprite, earth sprite, lava sprite, kodama, orb spirit, spirit lantern, candle spirit, snow spirit, light elemental, ancestor spirit, "
             "guardian spirit, kami, piskie, pumpkin spirit", WISPY),
    ("slime", "slime, slimes, ooze, the blob, blob, king slime, fire slime, ice slime, metal slime, gold slime, poison slime, rainbow slime, "
              "gelatinous cube, jelly knight, dragon slime, alien blob, blob alien, alien goo pet, tar monster, ink monster, kaiju slime, radiation blob, goo, shapeshifter, shapeshift alien, doppelganger, sock monster, dust bunny monster, cotton candy monster, bubble monster, balloon monster", BLOBBY),
    ("mud monster", "mud monster, mud man, mud elemental, bog monster, swamp monster, poison elemental, sludge monster, swamp thing", SPIRIT),
    ("treant", "treant, ent, tree ent, treant sapling, tree man, tree monster, leshy, forest giant, wood golem, forest spirit, green man, spriggan, "
               "dryad, moss golem, tree giant, polevik, myconid, wicker man monster", PLANTY),
    # ------------------------------------------------------------------ constructs (h_constructs.py)
    ("golem", "golem, golems, stone golem, rock golem, golem king, golem bot, gargoyle, gargoyle lord, gargoyle pup, grotesque, living statue, "
              "temple guardian, stone giant, titan, colossal titan, sand golem, jade golem, quartz golem, crystal golem, asteroid golem, bone golem", HUMANOID),
    ("clay golem", "clay golem, terracotta warrior, gingerbread golem, candy golem, gummy golem, flesh golem, flesh golem patchwork, "
                   "frankenstein's monster, frankenstein s monster, homunculus, pumpkin golem, mushroom golem, coral golem, snow golem, glitter golem, mud golem, abomination", HUMANOID),
    ("iron golem", "iron golem, metal golem, steel golem, bronze golem, colossus, talos, living armor, clockwork knight, automaton, automaton knight, "
                   "steam robot, iron giant, magnet robot, metal elemental", MACHINE),
    ("lava golem", "lava golem, fire golem, magma golem, obsidian golem, lava giant, volcano golem", HUMANOID),
    ("robot", "robot, robots, giant robot, killer robot, robot butler, robot chef, robot soldier, security robot, scrap robot, robot minion, "
              "robot janitor, robot referee, robot teacher, robot pirate, robot king, robot queen, robot wizard, robot knight, robot samurai, "
              "wind-up toy robot, wind up toy robot, toy robot, tin robot, mech, mech warrior, mech titan, mech pilot suit, farmer mech, "
              "firefighter robot, police robot, sheriff robot, cleaning robot, medic robot, robot dance crew, transforming robot, friendly giant robot, "
              "battle droid, droid", MACHINE),
    ("android", "android, androids, cyborg, cyborg soldier, cyber ninja, android assassin, chrome endoskeleton, bionic man, synth, mirror knight, star knight alien", MACHINE),
    # ------------------------------------------------------------------ apes (h_apes.py)
    ("gorilla", "gorilla, gorillas, silverback, mountain gorilla, baby gorilla, giant ape, ape, apes, king kong, robot gorilla, cyborg gorilla", ANIMALS),
    ("chimpanzee", "chimpanzee, chimp, chimps, bonobo, baby chimp, siamang, gibbon, orang pendek, vanara, monkey ninja, monkey sage", ANIMALS),
    ("orangutan", "orangutan, orangutans, baby orangutan, orang utan", ANIMALS),
    ("monkey", "monkey, monkeys, baby monkey, macaque, snow monkey, capuchin, howler monkey, spider monkey, squirrel monkey, proboscis monkey, "
               "golden snub-nosed monkey, golden snub nosed monkey, marmoset, tamarin, baboon, mandrill, gelada, colobus, langur, uakari, saki, "
               "titi monkey, night monkey, space monkey", ANIMALS),
    ("lemur", "lemur, lemurs, ring tailed lemur, aye-aye, aye aye, loris, tarsier, galago, bushbaby, sifaka, indri", ANIMALS),
]
