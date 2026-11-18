"""Word -> hero mapping for the bugs family (kept apart from the sculpt files so mapping edits do not invalidate the
mesh cache)."""
from bugkit import BUG

INS = {"bp": ["Insect", "Swarm", "Spider", "Worm"], "cat": BUG["cat"]}
ANIM = {"bp": ["Insect", "Swarm", "Spider", "Worm", "Crab", "Blob", "Serpent"], "cat": BUG["cat"]}
MOL = {"bp": ["Blob", "Insect", "Worm"], "cat": BUG["cat"]}
LARVA = {"bp": ["Insect", "Swarm", "Worm", "Serpent"], "cat": BUG["cat"]}

MAP = [
    # ---- h_bugs.py
    ("ant", "ant, ants, fire ant, army ant, carpenter ant, leafcutter ant, honeypot ant, trap-jaw ant, trap jaw ant, velvet ant, soldier ant, "
            "worker ant, red ant, black ant, sugar ant, giant ant, bullet ant, bulldog ant, insect, insects, bug", INS),
    ("queen ant", "queen ant, ant queen, winged ant, flying ant", INS),
    ("termite", "termite, termites, termite queen, white ant", INS),
    ("beetle", "beetle, beetles, ground beetle, carrion beetle, tiger beetle, diving beetle, click beetle, longhorn beetle, blister beetle, "
               "bombardier beetle, june bug, japanese beetle, whirligig beetle, meteor beetle, stink bug, shield bug, assassin bug, alien bug, "
               "xeno drone, violin beetle, rust monster, carrion crawler, cave crawler", ANIM),
    ("scarab", "scarab, scarabs, scarab beetle, dung beetle, jewel beetle, golden scarab, tortoise beetle, scarab swarm", INS),
    ("stag beetle", "stag beetle, rainbow stag beetle, titan beetle, pinching bug", INS),
    ("rhinoceros beetle", "rhinoceros beetle, rhino beetle, goliath beetle, unicorn beetle", INS),
    ("hercules beetle", "hercules beetle, atlas beetle, horned beetle", INS),
    ("ladybug", "ladybug, ladybugs, ladybird, lady beetle, aphid", INS),
    ("firefly", "firefly, fireflies, lightning bug, glowworm, glow worm, adze", INS),
    ("weevil", "weevil, giraffe weevil, boll weevil", INS),
    ("cockroach", "cockroach, cockroaches, roach, hissing cockroach, silverfish, earwig, giant water bug, vermin", INS),
    # ---- h_bugs_fly.py
    ("bee", "bee, bees, honeybee, honey bee, queen bee, worker bee, killer bee, orchid bee, leafcutter bee, sweat bee, bee swarm, !robot", INS),
    ("bumblebee", "bumblebee, bumble bee, bumblebees, carpenter bee", INS),
    ("wasp", "wasp, wasps, yellowjacket, yellow jacket, paper wasp, mud dauber, cuckoo wasp, tarantula hawk, mantisfly", INS),
    ("hornet", "hornet, hornets, murder hornet, bald faced hornet, giant hornet", INS),
    ("butterfly", "butterfly, butterflies, monarch butterfly, swallowtail, blue morpho, morpho, painted lady, red admiral, cabbage white, "
                  "birdwing butterfly, glasswing butterfly, owl butterfly", INS),
    ("moth", "moth, moths, hawk moth, death s head moth, clothes moth, atlas moth, io moth, cecropia moth, poodle moth, rosy maple moth, "
             "giant moth, giant moth monster", INS),
    ("luna moth", "luna moth, moon moth", INS),
    ("fly", "fly, flies, housefly, house fly, fruit fly, horsefly, horse fly, botfly, blow fly, deer fly, tsetse fly, robber fly, bee fly, "
            "hoverfly, scorpionfly", INS),
    ("mosquito", "mosquito, mosquitoes, mosquitos, crane fly, gnat, gnats, midge", INS),
    ("dragonfly", "dragonfly, dragonflies, dragon fly, damselfly, meganeura, mayfly, lacewing, caddisfly, stonefly, dobsonfly, snakefly, "
                  "star dragonfly, antlion, ant lion monster", INS),
    ("cicada", "cicada, cicadas, lanternfly, treehopper, leafhopper, spittlebug", INS),
    # ---- h_bugs_hop.py
    ("grasshopper", "grasshopper, grasshoppers, locust, locusts, katydid, lubber grasshopper, rainbow grasshopper", INS),
    ("cricket", "cricket, crickets, mole cricket, cave cricket, jerusalem cricket, weta", INS),
    ("flea", "flea, fleas, louse, lice, nits", INS),
    ("praying mantis", "praying mantis, mantis, mantises, orchid mantis, mantid", INS),
    ("stick insect", "stick insect, walking stick, stick bug, leaf insect, phasmid", INS),
    ("water strider", "water strider, pond skater, water skater, backswimmer", INS),
    # ---- h_bugs_spider.py
    ("spider", "spider, spiders, wolf spider, brown recluse, huntsman spider, funnel web spider, crab spider, fishing spider, cellar spider, "
               "spitting spider, bolas spider, ogre faced spider, pelican spider, mirror spider, orb weaver, golden orb weaver, trapdoor spider, "
               "diving bell spider, giant spider, phase spider, spider queen, kaiju spider, harvestman, daddy long legs, camel spider, "
               "whip spider, anansi, jorogumo, crystal spider queen, !robot", INS),
    ("tarantula", "tarantula, tarantulas, goliath birdeater, birdeater, bird eater", INS),
    ("black widow", "black widow, redback spider, redback, widow spider", INS),
    ("jumping spider", "jumping spider, peacock spider", INS),
    ("tick", "tick, ticks, mite, mites, bed bug, deer tick, water bear, tardigrade", INS),
    ("scorpion", "scorpion, scorpions, deathstalker, giant scorpion, whip scorpion, pseudoscorpion, eurypterid, jaekelopterus, sea scorpion", INS),
    ("emperor scorpion", "emperor scorpion", INS),
    # ---- h_bugs_crawl.py
    ("centipede", "centipede, centipedes, giant centipede, scutigera, mega centipede, house centipede, hallucigenia", INS),
    ("millipede", "millipede, millipedes, arthropleura, pill millipede", INS),
    ("caterpillar", "caterpillar, caterpillars, monarch caterpillar, inchworm, inch worm, silkworm, larva, alien larva", LARVA),
    ("hornworm", "hornworm, tomato hornworm", INS),
    ("woolly bear", "woolly bear, wooly bear, puss caterpillar", LARVA),
    ("earthworm", "earthworm, earthworms, worm, worms, nightcrawler, mealworm, maggot, grub, leech, tapeworm, flatworm, ribbon worm, "
                  "bristle worm, nematode, velvet worm, peanut worm, arrow worm, bobbit worm, parasite, !christmas tree worm, !feather duster worm, !tube worm", INS),
    ("snail", "snail, snails, giant african snail, moon snail, cone snail, periwinkle, gravity snail, sea snail", MOL),
    ("slug", "slug, slugs, banana slug, leopard slug, sea slug, blue sea slug, lettuce sea slug, sea hare", MOL),
]
