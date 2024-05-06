from dataclasses import dataclass
from enum import Enum

class Animations(Enum):
    STEADY = 0
    STEADY_LS = 1
    WALKING = 2
    WALKING_LS = 3
    FLICKER = 4
    FLCIKER_LS = 5
    BLINK = 6
    BLINK_LS = 7
    FADE = 8
    FADE_LS = 9

@dataclass
class LightingData:
    power: bool = False
    brightness: int = 255
    effect: Animations = Animations.WALKING

LIGHT_EFFECTS = {
    "Steady": Animations.STEADY,
    "Walking": Animations.WALKING,
    "Flicker": Animations.FLICKER,
    "Blink": Animations.BLINK,
    "Fade": Animations.FADE,
}