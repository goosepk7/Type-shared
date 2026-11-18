"""Word -> hero rules for the dragons and mythic families (kept apart from the sculpt modules so that editing the
mapping does not invalidate their cached meshes). See map.py for the matching rules."""
from map import NOTFOOD

# creatures only (keeps "dragon storm", "dragon fruit", "dragon sword" ... away), plus Person for "dragon rider" style mounts
BEAST = {"bp": ["Quadruped", "Serpent", "Dragon", "Bird", "Biped", "Fish", "Swarm", "Giant"],
         "cat": ["Creature", "Machine", "Object", "Abstract", "Element", "Person"]}
LIZARDS = "!komodo dragon, !bearded dragon, !water dragon, !leafy sea dragon, !cockatoo dragon, !flying dragon lizard, !dragon storm, !dragonfly"

MAP = [
    # ---------------------------------------------------------------- western dragons (h_dragons.py)
    ("dragon", "dragon, dragons, fire dragon, red dragon, ice dragon, frost dragon, storm dragon, thunder dragon, shadow dragon, dark dragon, "
               "forest dragon, golden dragon, gold dragon, crystal dragon, poison dragon, metal dragon, lava dragon, light dragon, "
               "bone dragon, undead dragon, mecha dragon, clockwork dragon, robot dragon, dragon rider, dragon mount, war dragon, "
               "blue dragon, green dragon, black dragon, white dragon, silver dragon, " + LIZARDS, BEAST),
    ("elder dragon", "elder dragon, ancient dragon, dragon king, dragon queen, dragon lord, void dragon, earth dragon, fafnir, zmey, "
                     "great wyrm, dracolich, smaug", BEAST),
    ("drake", "drake, drakes, fire drake, ember drake, rock drake, fire-drake, dragon whelp adult", NOTFOOD),
    ("wyvern", "wyvern, wyverns, sea wyvern, frost wyvern, snallygaster, piasa bird, kongamato", NOTFOOD),
    ("baby dragon", "baby dragon, dragon whelp, whelp, wyrmling, dragonling, dragon hatchling, pocket dragon, paper dragon, candy dragon, "
                    "thunder dragon hatchling, bone dragon hatchling, robot dragon hatchling, dragon pup", NOTFOOD),
    ("fairy dragon", "fairy dragon, faerie dragon, pixie dragon, butterfly dragon", NOTFOOD),
    ("hydra", "hydra, hydras, hydra king, hydra hatchling, two-headed dragon, two headed dragon, three headed space dragon, three headed dragon, multi headed dragon, "
              "yamata no orochi, orochi, lernaean hydra, !hydra polyp", NOTFOOD),
    # ---------------------------------------------------------------- serpent dragons (h_dragons_serp.py)
    ("chinese dragon", "chinese dragon, lung dragon, eastern dragon, oriental dragon, azure dragon, jade dragon, pearl dragon, wind dragon, rainbow dragon, "
                       "moon dragon, comet dragon, lantern dragon, kite dragon, sun dragon, sun dragon spirit, ryujin, zhulong, bashe, bakunawa, imugi, "
                       "celestial dragon, sky dragon, cloud dragon, spirit dragon, river dragon, japanese dragon", NOTFOOD),
    ("sea serpent", "sea serpent, sea serpents, sea dragon, ogopogo, lake monster, loch ness monster, taniwha, ninki nanka, inkanyamba, "
                    "horned serpent, rainbow serpent, sea serpent hatchling, sea dragon hatchling, lava serpent, sky serpent, cosmic serpent, "
                    "nebula serpent, scylla, makara, !leafy sea dragon", NOTFOOD),
    ("leviathan", "leviathan, jormungandr, world serpent, midgard serpent, apep, apophis, sea kaiju, ketos", NOTFOOD),
    ("lindworm", "lindworm, wyrm, wurm, tatzelwurm, zmey gorynych, nidhogg, ladon, bone serpent, mother of monsters, grootslang", NOTFOOD),
    ("amphiptere", "amphiptere, quetzalcoatl, coatl, feathered serpent, kukulkan, winged serpent", NOTFOOD),
    ("basilisk", "basilisk, basilisks, basilisk king, basilisk hatchling, boitata, serpent king, naga, naga queen, naga king", NOTFOOD),
    # ---------------------------------------------------------------- mythic beasts (h_mythic.py)
    ("griffin", "griffin, griffins, gryphon, gryphons, griffon, griffin king, golden griffin, black griffin, ice griffin, gryphon chick, "
                "catbird griffin, griffin mount, griffin rider, winged lion, !griffon vulture", NOTFOOD),
    ("hippogriff", "hippogriff, hippogriffs, hippogryph, hippogriff rider, hippogriff chick, hippalectryon", NOTFOOD),
    ("manticore", "manticore, manticores, manticore cub, manticore queen", NOTFOOD),
    ("chimera", "chimera, chimaera, chimera cub, chimera dragon, nue", NOTFOOD),
    ("sphinx", "sphinx, sphinxes, sphinx queen, androsphinx, lamassu, !sphinx cat", NOTFOOD),
    ("kitsune", "kitsune, nine-tailed fox, nine tailed fox, ninetails, huli jing, kumiho, nogitsune, fox spirit", NOTFOOD),
    ("qilin", "qilin, kirin, ki-rin, kirin foal, xiezhi, bai ze", NOTFOOD),
    ("behemoth", "behemoth, behemoths, tarasque, bulgasari, cipactli", NOTFOOD),
    # ---------------------------------------------------------------- mythic birds (h_mythic_birds.py)
    ("phoenix", "phoenix, phoenixes, ice phoenix, phoenix lord, fire phoenix king, fire phoenix, bennu, bennu phoenix, fenghuang, vermilion bird, firebird, "
                "firebird of the east, ember phoenix chick, phoenix chick, phoenix feather spirit, huma bird, caladrius", NOTFOOD),
    ("thunderbird", "thunderbird, thunderbirds, thunderbird chick, impundulu, stymphalian bird, storm bird, lightning bird", NOTFOOD),
    ("roc", "roc, rocs, roc chick, ziz, kaiju bird, simurgh, garuda, garuda chick, giant eagle, gandaberunda", NOTFOOD),
    ("cockatrice", "cockatrice, cockatrices, cockatrice chick", NOTFOOD),
    ("foo dog", "foo dog, fu dog, foo lion, guardian lion, komainu, shisa, haetae, pixiu, nian, yali, barong, shishi", NOTFOOD),
]
