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

class ExtraEffects(Enum):
    STEADY = 0
    SENSOR = 1

@dataclass
class LightingData:
    power: bool = True
    brightness: int = 255
    effect: Animations = Animations.WALKING

@dataclass
class ExtraLightData:
    power: bool = True
    brightness: int = 255
    effect: ExtraEffects = ExtraEffects.SENSOR

LIGHT_EFFECTS = {
    "Steady": Animations.STEADY,
    "Walking": Animations.WALKING,
    "Flicker": Animations.FLICKER,
    "Blink": Animations.BLINK,
    "Fade": Animations.FADE,
}

EXTRA_LIGHT_EFFECTS = {
    "Steady": ExtraEffects.STEADY,
    "Sensor": ExtraEffects.SENSOR
}