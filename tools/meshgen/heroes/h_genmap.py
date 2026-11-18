"""Word -> hero rules for leftover library words that were still building from the generic plans (thread "Polish
generic summon and mount bodies"): cat breeds and cat spirits, extinct look-alikes, worm monsters, slugs. Kept apart
from the sculpt modules so editing the mapping does not invalidate their cached meshes. See map.py for the rules."""
from map import NOTFOOD

MAP = [
    ("cat", "abyssinian, british shorthair, russian blue, scottish fold, devon rex, maine coon, wildcat, margay, jaguarundi, "
            "familiar, hellcat, cait sith, bakeneko", NOTFOOD),
    ("lion", "liger", NOTFOOD),
    ("leopard", "nahual", NOTFOOD),
    ("boar", "entelodont", NOTFOOD),
    ("hippopotamus", "toxodon", NOTFOOD),
    ("rhinoceros", "uintatherium, megacerops", NOTFOOD),
    ("diplodocus", "mokele-mbembe, mokele mbembe", NOTFOOD),
    ("frog", "frog prince, frog knight", NOTFOOD),
    ("earthworm", "death worm, lava worm, ice worm, mongolian worm, sand worm hatchling, kaiju worm, space worm", NOTFOOD),
    ("slug", "lava slug, space slug, sea bunny", NOTFOOD),
]
MAP += [
    ("ice elemental", "snow elemental", NOTFOOD),
    ("earth elemental", "sand elemental", NOTFOOD),
    ("treant", "nature elemental, bramble elemental, vine horror", NOTFOOD),
]
MAP += [("slime", "!balloon monster, !sock monster", NOTFOOD)]
