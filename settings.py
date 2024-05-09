from logging import INFO
from os import environ

from ha_mqtt_discoverable import Settings

## Sensor Section

# Number of sensors present in the system (must all be on the main i2c bus)
SENSOR_COUNT = 6

# Sensor trip distances (cm)
PER_SENSOR_CALIBRATIONS = [60, 51, 51, 43.5, 60, 55]

# VL53L0X Shutdown Pins (required)
SENSOR_XSHUT_PINS = [21, 20, 7, 8, 25, 24, 16, 12, 23, 18, 14, 15, 26, 19]

# Sensor Timing Budget in microseconds (Higher means better accuracy, but slower read times)
SENSOR_TIMING_BUDGET = 72000

## Led Section

# Number of leds present in system (must be the same as the number of sensors)
LED_COUNT = 6

# Lighting frequency control (usually the higher the better, but required settingss may vary)
LED_FREQ = 120

# Lighting frame rate cap
LED_FPS = 560
LED_OFF_FPS = 560

## Per-animation settings

# Speed for Blink Animation
BLINK_HZ = 2

# Speed for Fade Animation
FADE_SPEED_MULTIPLIER = 0.75

## Home Assistant Options

# MQTT Broker for Home Assistant
MQTT_SETTINGS = Settings.MQTT(host="homeassistant.local", username=environ["BROKER_USER"], password=environ["BROKER_PASS"])

# Maximum time for MQTT to connect
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
# Use types from Python's standard logging module (ex: logging.INFO, logging.WARNING)
# For trace level logging, use 0, or use the -Vt cmdline arg

INTERACTIVE_LOG_LEVEL = INFO # Logging level for use in an interactive terminal
REGULAR_LOG_LEVEL = INFO # Logging level for non-interactive shell

DO_BANNER = True