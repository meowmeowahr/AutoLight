from logging import WARNING
from os import environ

from ha_mqtt_discoverable import Settings

from terminal import DisplayStatusTypes

## Sensor Section

# Number of sensors present in the system (must all be on the main i2c bus)
# SENSOR_COUNT = 15
SENSOR_COUNT = 1

# VL53L0X Shutdown Pins (required)
#SENSOR_XSHUT_PINS = [21, 15, 18, 23, 24, 25, 8, 7, 12, 16, 20, 14, 4, 17, 27]
SENSOR_XSHUT_PINS = [21]

# Sensor Timing Budget in microseconds (Higher means better accuracy, but slower read times)
SENSOR_TIMING_BUDGET = 66000

# Sensor trip distance (cm)
SENSOR_TRIP_DISTANCE = 87

## Led Section

# Number of leds present in system (must be the same as the number of sensors)
LED_COUNT = SENSOR_COUNT

# Lighting frequency control (usually the higher the better, but required settingss may vary)
LED_FREQ = 120

# Lighting frame rate cap
LED_FPS = 120
LED_OFF_FPS = 24

# Per-animation settings
BLINK_HZ = 2

FADE_SPEED_MULTIPLIER = 0.75

## Home Assistant Options

# MQTT Broker for Home Assistant
MQTT_SETTINGS = Settings.MQTT(host="homeassistant.lan", username=environ["BROKER_USER"], password=environ["BROKER_PASS"])

MQTT_CONNECTION_TIMEOUT = 6.0

# Home Assistant Device Options
DEVICE_NAME = "Staircase Lighting"
DEVICE_ID = "sl"

# Home Assistant Light Entity Options
LIGHT_NAME = "Main Control"
LIGHT_ICON = "mdi:stairs"
LIGHT_UID = "light_staircase"

# Home Assistant debugging entities
CREATE_DEBUG_ENTITIES = True
DEBUG_UPDATE_RATE = 15.0 # seconds

## Logging Settings

# Logging
INTERACTIVE_LOG_LEVEL = WARNING # Logging level for use in an interactive terminal
REGULAR_LOG_LEVEL = WARNING # Logging level for non-interactive shell

# Fancy Terminal Output
DO_FANCY_TERM_OUT = True
FANCY_LOGGING_LEVELS = [DisplayStatusTypes.ALL]