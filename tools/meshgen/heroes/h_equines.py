"""Horses and their kin (the game's main MOUNTS): horse, warhorse, clydesdale, pony, foal, zebra, donkey, mule,
unicorn, pegasus, alicorn, nightmare. Built by hoofkit.ungulate (shared hoofed anatomy) with full riding tack where
it fits (blanket, saddle with pommel / cantle / girth, leather stirrup straps + irons on swinging bones, bridle with
bit rings, reins), plate barding for the warhorse, a transverse-gallop Move with spine flex and neck bob, and a
rear-up fore-hoof strike (horses) or double-barrelled buck (donkeys, mules, zebras). Fantasy horses fly (pegasus,
alicorn: spread feathered wings, flapping Move with tucked legs).
"""
import numpy as np

from kit import hero, stripes, combine
from map import NOTFOOD
import hoofkit as K

TAGS = ("ungulate", "equine", "mount")


def horse_kw(**kw):
    d = dict(head="horse", ears="horse", mane="horse", forelock=True, tail="horse", hoof="solid", tack="riding", pupil=None,
             gait="gallop", attack="rear", tags=TAGS, tuck=0.35,
             preview={"primary": "#7A4A2A", "secondary": "#2A1A12", "hoof": "#3B2F2A"})
    d.update(kw)
    return d


def zebra_stripes(s=1.0, yb=1.8, cy=2.45):
    def axis(Q):
        y = Q[:, 1] / s
        z = Q[:, 2] / s
        legw = np.clip((yb + 0.1 - y) / 0.45, 0, 1)
        body = z * 1.0 + 0.45 * np.clip(z - 0.6, 0, None) * (y - cy) + 0.12 * np.abs(y - cy)
        return body * (1 - legw) + (y * 1.35 + 0.2 * z) * legw
    return stripes(axis, 2.6, width=0.42, depth=0.93, wobble=0.05, seed=4)


@hero("horse", "equines")
def horse():
    return K.ungulate("horse", **horse_kw(legs_dark=0.55))


@hero("warhorse", "equines")
def warhorse():
    return K.ungulate("warhorse", **horse_kw(tack="barding", forelock=False, bit=False, blanket=False, girth=1.1, lt=1.15, s=1.05,
                                             hs=1.05, legs_dark=0.4, neck_thick=1.1, tris=0.9,
                                             preview={"primary": "#3B2E2A", "secondary": "#2F4E8C", "hoof": "#2B2420", "steel": "#9AA4AE"}))


@hero("clydesdale", "equines")
def clydesdale():
    return K.ungulate("clydesdale", **horse_kw(s=1.1, girth=1.22, depth=1.08, lt=1.3, hoof_r=1.2, feather=0.8, hs=1.08, neck_thick=1.15, mane_col="dark",
                                               head_over={"roman": 0.04}, legs_dark=0.0,
                                               preview={"primary": "#6A3A1E", "secondary": "#F2F0EA", "hoof": "#3B2F2A"}))


@hero("pony", "equines")
def pony():
    return K.ungulate("pony", **horse_kw(s=0.72, leg=0.84, girth=1.18, depth=1.08, body=0.9, hs=1.18, neck_len=0.82, neck_thick=1.15,
                                         ears="pony", lt=1.2, arch=0.16, legs_dark=0.0,
                                         preview={"primary": "#B88A5A", "secondary": "#F2E6D4", "hoof": "#3B2F2A"}))


@hero("foal", "equines")
def foal():
    return K.ungulate("foal", **horse_kw(s=0.62, leg=1.28, girth=0.78, depth=0.82, body=0.78, hs=1.3, neck_len=0.86, neck_thick=0.9,
                                         lt=0.85, tack=None, tail_len=0.6, forelock=False, mane="brush", legs_dark=0.0, stride=0.9,
                                         preview={"primary": "#A06A3E", "secondary": "#F0E0C8", "hoof": "#3B2F2A"}))


@hero("zebra", "equines")
def zebra():
    return K.ungulate("zebra", **horse_kw(s=0.88, girth=1.08, depth=1.05, hs=1.08, ears="zebra", mane="brush", forelock=False, tail="tuft",
                                          tack=None, attack="buck", pattern=zebra_stripes(0.88, 1.8, 2.45), mane_col="secondary", shade=0.95,
                                          preview={"primary": "#F2F2F0", "secondary": "#1A1A1A", "hoof": "#2B2420"}))


@hero("donkey", "equines")
def donkey():
    return K.ungulate("donkey", **horse_kw(s=0.74, leg=0.92, girth=1.1, depth=1.08, hs=1.25, ears="donkey", mane="brush", forelock=False,
                                           tail="tuft", neck_len=0.85, neck_ang=40, neck_thick=1.1, arch=0.05, attack="buck", gait="trot",
                                           lt=1.1, withers=0.12, legs_dark=0.0,
                                           preview={"primary": "#8A8076", "secondary": "#3A332E", "hoof": "#3B2F2A"}))


@hero("mule", "equines")
def mule():
    return K.ungulate("mule", **horse_kw(s=0.88, girth=1.05, hs=1.18, ears="mule", mane="brush", forelock=False, tail="horse", tail_len=0.85,
                                         neck_ang=45, attack="buck", withers=0.15, legs_dark=0.3,
                                         preview={"primary": "#6E5444", "secondary": "#2E2420", "hoof": "#3B2F2A"}))


@hero("unicorn", "equines")
def unicorn():
    return K.ungulate("unicorn", **horse_kw(tack=None, horn_unicorn=True, leg=1.05, girth=0.95, arch=0.18, feather=0.35, hoof_col="gold",
                                            legs_dark=0.0, shade=0.94, tags=TAGS + ("magic",),
                                            preview={"primary": "#FDF4FF", "secondary": "#F0ABFC", "horn": "#F3E3B0", "gold": "#E8B53A"}))


def _winged(hid, horn, prev):
    return K.ungulate(hid, **horse_kw(tack="bridle", wings="spread", horn_unicorn=horn, gait="fly", rig_gait="fly", leg=1.02, girth=0.95,
                                      arch=0.16, legs_dark=0.0, shade=0.94, tris=0.8, hoof_col="gold" if horn else "hoof", tags=TAGS + ("magic", "flying"),
                                      preview=prev))


@hero("pegasus", "equines")
def pegasus():
    return _winged("pegasus", False, {"primary": "#F8FAFC", "secondary": "#93C5FD", "hoof": "#8A8F99"})


@hero("alicorn", "equines")
def alicorn():
    return _winged("alicorn", True, {"primary": "#E9D5FF", "secondary": "#FDE68A", "horn": "#F3E3B0", "gold": "#E8B53A"})


@hero("nightmare", "equines")
def nightmare():
    return K.ungulate("nightmare", **horse_kw(tack=None, mane="flame", forelock=False, hoof_col="secondary", eye_col=[1.0, 0.35, 0.1], eye_glow=True,
                                              girth=1.05, lt=1.1, neck_thick=1.05, legs_dark=0.0, shade=0.9, tags=TAGS + ("undead", "fire"),
                                              preview={"primary": "#1B1F2A", "secondary": "#F97316", "hoof": "#2B2420"}))


# word -> hero rules (tools/meshgen/heroes/map.py)
A = NOTFOOD
MAP = [
    ("horse", "horse, horses, stallion, mare, mustang, bronco, steed, arabian horse, thoroughbred, appaloosa, palomino, pinto, "
              "racehorse, race horse, wild horse, przewalski's horse, quarter horse, colt, filly, gelding, palfrey, courser, "
              "ghost horse, fire horse, ice horse, wind horse, thunder horse, shadow steed, valkyrie steed, robot horse, wooden horse, "
              "kelpie, each uisge, horse spirit, spirit horse, !horse carriage, !horse drawn, !sea horse, !seahorse, !rocking horse, !pommel horse, "
              "!horsefly, !horse fly", A),
    ("warhorse", "warhorse, war horse, destrier, battle horse, knight horse, armored horse, armoured horse, cavalry horse, "
                 "mounted knight, jouster, cavalry, pegasus warhorse", {"cat": A["cat"] + ["Person"]}),
    ("clydesdale", "clydesdale, shire horse, draft horse, draught horse, workhorse, plow horse, friesian horse, friesian, percheron, "
                   "belgian horse, sleipnir", A),
    ("pony", "pony, ponies, shetland pony, shetland, pit pony, rocking horse", A),
    ("foal", "foal, foals, baby horse, kelpie foal, nightmare horse foal", A),
    ("zebra", "zebra, zebras, grevy's zebra, quagga, zebroid, zorse", A),
    ("donkey", "donkey, donkeys, burro, ass, jackass, wild donkey, onager, kiang", A),
    ("mule", "mule, mules, hinny, pack mule", A),
    ("unicorn", "unicorn, unicorns, rainbow unicorn, holy unicorn, fire unicorn, ice unicorn, zombie unicorn, nightmare unicorn, "
                "robot unicorn, unicorn foal, !narwhal unicorn", A),
    ("pegasus", "pegasus, pegasi, winged horse, storm pegasus, dark pegasus, pegasus foal, hippogriff steed", A),
    ("alicorn", "alicorn, pegacorn, winged unicorn", A),
    ("nightmare", "nightmare, nightmare horse, hellhorse, hell horse, skeleton horse, zombie horse, undead horse, dullahan horse, "
                  "headless horseman horse, death horse, black stallion, ghost horse rider, dark steed, nuckelavee, pooka, !nightmare beast", A),
]
