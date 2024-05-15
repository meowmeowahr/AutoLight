import os
import sys
import yaml
from enum import Enum

from loguru import logger


class SettingsEnum(Enum):
    SENSOR_COUNT = "sensors.count"
    PER_SENSOR_CALIBRATIONS = "sensors.per_sensor_calibrations"
    SENSOR_XSHUT_PINS = "sensors.xshut_pins"
    SENSOR_TIMING_BUDGET = "sensors.timing_budget"
    MAIN_LED_COUNT = "leds.main_count"
    LED_FREQ = "leds.freq"
    LED_FPS_ON = "leds.fps_on"
    LED_FPS_OFF = "leds.fps_off"
    BLINK_HZ = "animations.blink.blink_hz"
    FADE_SPEED_MULTIPLIER = "animations.fade.fade_speed_multiplier"
    MQTT_HOST = "home_assistant.mqtt.host"
    MQTT_PORT = "home_assistant.mqtt.port"
    BROKER_USER = "home_assistant.mqtt.username"
    BROKER_PASS = "home_assistant.mqtt.password"
    MQTT_CONNECTION_TIMEOUT = "home_assistant.mqtt.connection_timeout"
    DEVICE_NAME = "home_assistant.device.name"
    DEVICE_ID = "home_assistant.device.id"
    LIGHT_NAME = "home_assistant.light_entity.name"
    LIGHT_ICON = "home_assistant.light_entity.icon"
    LIGHT_UID = "home_assistant.light_entity.uid"
    EXTRA_LIGHTS = "extra_leds"
    CREATE_DEBUG_ENTITIES = "home_assistant.debugging_entities.create_debug_entities"
    DEBUG_UPDATE_RATE = "home_assistant.debugging_entities.update_rate"
    INTERACTIVE_LOG_LEVEL = "logging.interactive_log_level"
    REGULAR_LOG_LEVEL = "logging.regular_log_level"
    DO_BANNER = "misc.do_banner"


class Settings:
    def __init__(self, config_file="config.yaml"):
        self.config_file = config_file
        if not os.path.exists(config_file):
            logger.critical(f"Configuration file {config_file} does not exist")
            sys.exit()
        with open(config_file) as f:
            self.root_settings: dict = yaml.load(f, yaml.SafeLoader)

    def get_by_enum(self, setting_enum: SettingsEnum):
        setting_path = setting_enum.value.split(".")
        setting_value = self.root_settings

        if setting_enum == SettingsEnum.EXTRA_LIGHTS:
            default = []
        else:
            default = None

        for key in setting_path:
            setting_value = setting_value.get(key, default)

        if setting_value == "USE_ENV":
            setting_value = os.environ[setting_enum.name]

        return setting_value

    def get(self, key):
        return self.root_settings.get(key)

    def set(self, key, value):
        self.root_settings[key] = value

    def save(self):
        with open(self.config_file, "w") as f:
            yaml.dump(self.root_settings, f)
