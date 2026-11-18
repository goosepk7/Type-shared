"""Word -> hero rules for the birds family (h_birds.py flyers, h_birds_ground.py walkers, h_birds_bats.py bats).
Kept in their own module so editing a mapping never invalidates the meshed pieces of the sculpt modules."""
from h_birds import BIRD

MAP = []

# flying birds
MAP += [
    ("eagle", "eagle, eagles, bald eagle, golden eagle, harpy eagle, philippine eagle, sea eagle, haast's eagle, haasts eagle, eaglet, "
              "spirit eagle, storm eagle, war eagle, steppe eagle, booted eagle, crowned eagle, martial eagle, tawny eagle, "
              "fish eagle, imperial eagle, argentavis", BIRD),
    ("hawk", "hawk, hawks, red tailed hawk, goshawk, northern goshawk, sparrowhawk, harrier, buzzard, kite bird, snail kite, "
             "storm hawk, caracara, hawk eye, !tarantula hawk", BIRD),
    ("falcon", "falcon, falcons, peregrine falcon, kestrel, gyrfalcon, merlin falcon, peregrine, hobby falcon, lanner", BIRD),
    ("vulture", "vulture, vultures, turkey vulture, bearded vulture, king vulture, griffon vulture, lammergeier, marabou", BIRD),
    ("condor", "condor, condors, andean condor, california condor", BIRD),
    ("osprey", "osprey, ospreys, fish hawk", BIRD),
    ("owl", "owl, owls, great horned owl, eagle owl, long eared owl, screech owl, burrowing owl, elf owl, owlet, barred owl, "
            "spectacled owl, pygmy owl, fish owl, horned owl, cosmic owl, clockwork owl, tawny owl, little owl", BIRD),
    ("barn owl", "barn owl, barn owls, ghost owl, grass owl", BIRD),
    ("snowy owl", "snowy owl, snowy owls, frost owl, arctic owl, white owl", BIRD),
    ("parrot", "parrot, parrots, african grey, amazon parrot, eclectus parrot, quaker parrot, conure, budgie, budgerigar, lovebird, "
               "kea, kakapo, parakeet, rainbow lorikeet, lorikeet, lory, rosella, pirate parrot, pirate parrot captain, polly", BIRD),
    ("macaw", "macaw, macaws, hyacinth macaw, scarlet macaw, blue macaw", BIRD),
    ("cockatoo", "cockatoo, cockatoos, cockatiel, galah, sulphur crested cockatoo", BIRD),
    ("toucan", "toucan, toucans, toco toucan, aracari, barbet", BIRD),
    ("hornbill", "hornbill, hornbills, hoopoe", BIRD),
    ("bird", "bird, birds, birdie, songbird, tweety, warbler, nightingale, starling, mockingbird, lark, wren, chickadee, tit, titmouse, "
             "oriole, weaver bird, cuckoo, mynah, myna, nuthatch, treecreeper, kinglet, waxwing, tui, bowerbird, sunbird, "
             "honeyeater, pitta bird, fairywren, flycatcher, catbird, wagtail, dipper, oxpecker, tanager, trogon, "
             "motmot, puffbird, turaco, quetzal, drongo, grackle, cowbird, blackbird, red winged blackbird, song thrush, thrush, "
             "bird of paradise, nightjar, potoo, oilbird, robot bird, sunfire bird, !kaiju bird, !bird warrior, !piasa bird", BIRD),
    ("sparrow", "sparrow, sparrows, house sparrow, java sparrow, bunting, chaffinch, skylark, dunnock, junco, sparrow spirit", BIRD),
    ("robin", "robin, robins, robin redbreast, european robin, american robin", BIRD),
    ("cardinal", "cardinal, cardinals, red cardinal, northern cardinal, bullfinch, grosbeak, crossbill", {**BIRD, "bp": ["Bird"]}),
    ("blue jay", "blue jay, blue jays, jay, jays, steller's jay, stellers jay", BIRD),
    ("bluebird", "bluebird, bluebirds, eastern bluebird, bluebird of happiness", BIRD),
    ("finch", "finch, finches, goldfinch, zebra finch, canary, canaries, siskin, serin", BIRD),
    ("swallow", "swallow, swallows, swift, swifts, barn swallow, tern, terns, swiftlet", {**BIRD, "cat": ["Creature", "Machine", "Element", "Weather"]}),
    ("crow", "crow, crows, rook, jackdaw, storm crow, carrion crow, chough, nutcracker bird", BIRD),
    ("raven", "raven, ravens, shadow raven, three eyed raven, raven spirit, common raven", BIRD),
    ("magpie", "magpie, magpies, shrike, butcherbird", BIRD),
    ("pigeon", "pigeon, pigeons, homing pigeon, passenger pigeon, fantail pigeon, rock dove, carrier pigeon, wood pigeon, mourning dove, turtle dove", BIRD),
    ("dove of peace", "dove, doves, dove of peace, white dove, peace dove", BIRD),
    ("seagull", "seagull, seagulls, gull, gulls, kittiwake, skua, petrel, shearwater, herring gull", BIRD),
    ("albatross", "albatross, albatrosses, frigatebird, gannet, booby, blue footed booby, pelagornis, wandering albatross", BIRD),
    ("pelican", "pelican, pelicans, brown pelican, cormorant, anhinga", BIRD),
    ("hummingbird", "hummingbird, hummingbirds, hummer bird, sunbird hummingbird", BIRD),
    ("woodpecker", "woodpecker, woodpeckers, woody woodpecker, sapsucker, hoatzin", BIRD),
    ("kingfisher", "kingfisher, kingfishers, kookaburra, bee-eater, bee eater, jacamar", BIRD),
]

# ground and water birds
MAP += [
    ("chicken", "chicken, chickens, hen, hens, bantam, silkie chicken, silkie, zombie chicken, rubber chicken monster, guinea fowl, "
                "prairie chicken, grouse, sage grouse, capercaillie, partridge, ptarmigan, chook", BIRD),
    ("rooster", "rooster, roosters, cockerel, cock, gamecock, rooster king", BIRD),
    ("chick", "chick, chicks, baby chick, pea chick, ember phoenix chick, chicklet, !gryphon chick, !hippogriff chick, !griffin chick", BIRD),
    ("turkey", "turkey, turkeys, wild turkey, gobbler", BIRD),
    ("peacock", "peacock, peacocks, peafowl, peahen", BIRD),
    ("pheasant", "pheasant, pheasants, golden pheasant, lyrebird, roadrunner, road runner", BIRD),
    ("quail", "quail, quails, bobwhite, woodcock, snipe, sandpiper, plover, killdeer, oystercatcher, dunlin, lapwing", BIRD),
    ("duck", "duck, ducks, mallard, mandarin duck, wood duck, eider, teal, pintail, merganser, shelduck, muscovy duck, "
             "whistling duck, canvasback, coot, moorhen, grebe, loon, rubber duck, giant rubber duck, takahe, weka, rail bird", BIRD),
    ("duckling", "duckling, ducklings, gosling, goslings, cygnet, puffin chick", BIRD),
    ("goose", "goose, geese, snow goose, swan goose, domestic goose, greylag goose, !duck duck goose", BIRD),
    ("canada goose", "canada goose, barnacle goose, brant goose, canada geese", BIRD),
    ("swan", "swan, swans, black swan, mute swan, trumpeter swan, swan maiden", BIRD),
    ("penguin", "penguin, penguins, adelie penguin, little blue penguin, penguin chick, penguin soldier, robot penguin, "
                "giant penguin cryptid, great auk, chinstrap penguin", BIRD),
    ("emperor penguin", "emperor penguin, king penguin, emperor penguins, king penguins", BIRD),
    ("rockhopper penguin", "rockhopper penguin, rockhopper, macaroni penguin, gentoo penguin, crested penguin", BIRD),
    ("puffin", "puffin, puffins, auklet, guillemot, auk, razorbill", BIRD),
    ("flamingo", "flamingo, flamingos, flamingoes, flamingo chick, lawn flamingo, inflatable flamingo, spoonbill, roseate spoonbill", BIRD),
    ("heron", "heron, herons, egret, egrets, great blue heron, night heron, boat billed heron, bittern, "
              "ibis, sacred ibis, curlew, avocet, sunbittern", BIRD),
    ("stork", "stork, storks, jabiru, marabou stork, shoebill, hammerkop, wood stork", BIRD),
    ("crane bird", "crane bird, whooping crane, crowned crane, sandhill crane, red crowned crane, seriema, kagu, secretary bird", BIRD),
    ("ostrich", "ostrich, ostriches, ostrich chick, rhea, moa, elephant bird, ostrich mount, ostrich steed", BIRD),
    ("emu", "emu, emus, emu chick", BIRD),
    ("cassowary", "cassowary, cassowaries", BIRD),
    ("kiwi", "kiwi bird, kiwi, kiwi chick, kiwis", {"cat": ["Creature", "Machine", "Abstract", "Element"], "bp": ["Bird", "Quadruped", "Biped", "Blob"]}),
    ("dodo", "dodo, dodos, dodo bird", BIRD),
    ("terror bird", "terror bird, titanis, gastornis, phorusrhacos, diatryma, terror birds", BIRD),
]

# bats
MAP += [
    ("bat", "bat, bats, baby bat, pipistrelle, hoary bat, horseshoe bat, long eared bat, ghost bat, honduran white bat, "
            "mexican free tailed bat, free tailed bat, brown bat, hellbat, crystal bat, bat swarm, chonchon, camazotz", {**BIRD, "cat": ["Creature", "Machine", "Element"]}),
    ("fruit bat", "fruit bat, fruit bats, flying fox, flying foxes, megabat, hammer headed bat, ahool, spectral bat", BIRD),
    ("vampire bat", "vampire bat, vampire bats, vampire bat lord, blood bat, dracula bat", BIRD),
]
