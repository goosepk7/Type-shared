"""Word -> hero rules for the living-object / toy (h_objects) and robot-critter (h_bots) heroes. Kept apart from the
sculpt modules so editing the mapping does not invalidate their cached meshes. See map.py for the rules."""

OBJ = {"cat": ["Creature", "Object", "Person", "Machine"],
       "bp": ["Blob", "Orb", "Ball", "Biped", "Quadruped", "Humanoid", "Weapon", "Robot", "Ghost", "Structure"]}
TOY = {"cat": ["Object", "Creature", "Machine"], "bp": ["Biped", "Quadruped", "Humanoid", "Robot"]}
BOT = {"cat": ["Machine", "Creature", "Object"],
       "bp": ["Blob", "Orb", "Ball", "Bird", "Vehicle", "Robot", "Insect", "Structure", "Appliance", "Giant", "Biped", "Quadruped"]}
WALKER = {"cat": ["Creature", "Machine", "Structure"], "bp": ["Structure", "Giant", "Insect", "Biped", "Robot", "Appliance", "Quadruped"]}

MAP = [
    ("teapot spirit", "teapot spirit, living teapot, teapot monster, kettle spirit, tea kettle spirit", OBJ),
    ("tsukumogami", "tsukumogami, kasa obake, karakasa, karakasa obake, umbrella spirit, umbrella monster, haunted umbrella, umbrella yokai", OBJ),
    ("sock puppet", "sock puppet, sock monster, sock creature, sock buddy", OBJ),
    ("living sword", "living sword, animated sword, haunted sword, sentient sword, possessed sword, living blade, haunted blade", OBJ),
    ("animated broom", "animated broom, living broom, enchanted broom, broom spirit, broom monster, magic broom servant", OBJ),
    ("wind-up toy", "wind-up toy, wind up toy, windup toy, clockwork toy, tin toy, clockwork chick, toy", TOY),
    ("teddy bear", "teddy bear, teddy, stuffed animal, stuffed toy, plush, plushie, plush toy, stuffed bear", TOY),
    ("teddy bear monster", "teddy bear monster, evil teddy, haunted teddy, killer teddy, cursed teddy, possessed teddy, nightmare plush", OBJ),
    ("balloon animal", "balloon animal, balloon dog, balloon poodle, balloon monster, balloon creature", TOY),
    ("pet rock", "pet rock, pet pebble, googly rock", OBJ),
    ("slinky", "slinky, spring toy, walking spring, coil spring", OBJ),
    ("humpty dumpty", "humpty dumpty, humpty, egg man", OBJ),
    ("dinosaur egg", "dinosaur egg, dino egg, hatching egg", OBJ),
    ("floating eye", "floating eye, eyeball monster, eye monster, flying eye, watcher eye, gazer, eye", OBJ),
    ("brain alien", "brain alien, brain in a jar, alien brain, brain monster, big brain, brain", OBJ),
    ("robot vacuum", "robot vacuum, vacuum robot, vacuum bot, robo vacuum, cleaning robot", BOT),
    ("robot vacuum monster", "robot vacuum monster, vacuum monster, killer vacuum", BOT),
    ("mine bot", "mine bot, minebot, bomb bot, bomb robot, mine robot, rolling bomb, walking bomb", BOT),
    ("robot ball", "robot ball, ball robot, ball bot, rolling robot, sphere bot", BOT),
    ("combat drone", "combat drone, attack drone, war drone, laser drone, sentry drone, killer drone, drone", {"cat": ["Machine"], "bp": BOT["bp"]}),
    ("repair drone", "repair drone, repair bot, maintenance drone, medic drone, welding drone, fix-it drone", BOT),
    ("alien tripod", "alien tripod, tripod walker, martian tripod, tripod war machine, tripod", WALKER),
    ("robot arm monster", "robot arm monster, robot arm, robotic arm, grabber bot, claw bot", {"cat": ["Machine", "Creature"], "bp": WALKER["bp"]}),
    ("chicken-legged hut", "chicken-legged hut, chicken legged hut, hut on chicken legs, baba yaga hut, baba yagas hut, walking hut, izbushka",
     {"cat": ["Creature", "Structure", "Place"], "bp": ["Structure", "Giant", "Biped"]}),
]
