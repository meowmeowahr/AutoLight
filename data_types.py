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
    brightness: int = 127
    effect: Animations = Animations.STEADY

LIGHT_EFFECTS = {
    "Steady": Animations.STEADY,
    "Steady with Light Sensor": Animations.STEADY_LS,
    "Walking": Animations.WALKING,
    "Walking with Light Sensor": Animations.WALKING_LS,
    "Flicker": Animations.FLICKER,
    "Flicker with Light Sensor": Animations.FLCIKER_LS,
    "Blink": Animations.BLINK,
    "Blink with Light Sensor": Animations.BLINK_LS,
    "Fade": Animations.FADE,
    "Fade with Light Sensor": Animations.FADE_LS
}