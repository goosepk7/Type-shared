"""Extra mythic beasts built from the h_mythic chimera-builder: the foo dog (guardian lion-dog: stocky lion body,
big-headed with a curled mane and tufted tail)."""
from kit import hero
from h_mythic import _beast


@hero("foo dog", "mythic")
def foo_dog():
    return _beast("foo dog", torso="lion", heads=("lion",), mane=True, tail="lion", girth=1.18, leg=0.82, body=0.85, head=1.3, neck=0.8,
                  attack="pounce", preview={"primary": "#C8A04A", "secondary": "#8A3A1A", "nose": "#3A2A28", "iris": "#2A1A10"})
