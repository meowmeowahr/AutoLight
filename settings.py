import os
import sys
import yaml
from enum import Enum

from loguru import logger

from typing import TypedDict

class VL53L0XTypedSettings(TypedDict):
    type: str
    calibration: float
    xshut_pin: int
    timing_budget: int

class GPIOSensorTypedSettings(TypedDict):
    type: str
    pin: float
    invert: int
    pullup: int
    bounce_time: float

class LedTypedSettings(TypedDict):
    count: int
    freq: int
    fps_on: int
    fps_off: int

class _ExtraLedTypedSetting(TypedDict):
    channel: int
    ha_name: str
    ha_icon: str
    ha_id: str
    gpio_pin: int
    gpio_pullup: bool
    gpio_invert: bool


ExtraLedsTypedSettings = list[_ExtraLedTypedSetting]

class _BlinkAnimationTypedSettings(TypedDict):
    blink_hz: float

class _FadeAnimationTypedSettings(TypedDict):
    fade_speed_multiplier: float

class AnimationTypedSettings(TypedDict):
    blink: _BlinkAnimationTypedSettings
    fade: _FadeAnimationTypedSettings

class MqttTypedSettings(TypedDict):
    host: str
    port: int
    username: str
    password: str
    connection_timeout: float

class DeviceTypedSettings(TypedDict):
    name: str
    id: str

class LightEntityTypedSettings(TypedDict):
    name: str
    icon: str
    id: str

class DebuggingEntitiesTypedSettings(TypedDict):
    create_debug_entities: bool
    update_rate: float

class HomeAssistantTypedSettings(TypedDict):
    mqtt: MqttTypedSettings
    device: DeviceTypedSettings
    light_entity: LightEntityTypedSettings
    debugging_entities: DebuggingEntitiesTypedSettings

class LoggingTypedSettings(TypedDict):
    interactive_log_level: str
    regular_log_level: str
    log_file: str
    file_logging: bool
    rich_traceback: bool

class MiscTypedSettings(TypedDict):
    do_banner: bool

class Settings:
    def __init__(self, config_file="config.yaml"):
        self.config_file = config_file
        if not os.path.exists(config_file):
            logger.critical(f"Configuration file {config_file} does not exist")
            sys.exit()
        with open(config_file) as f:
            self.root_settings: dict = yaml.load(f, yaml.SafeLoader)

        # Sensor Settings
        self.sensor_settings: list[VL53L0XTypedSettings | GPIOSensorTypedSettings] = self.root_settings.get("sensors")
        self.sensor_count = len(self.sensor_settings)

        # Led Settings
        self.led_settings: LedTypedSettings = self.root_settings.get("leds")

        self.led_count = self.led_settings.get("count")
        self.led_freq = self.led_settings.get("freq", 200)
        self.led_fps_on = self.led_settings.get("fps_on", 120)
        self.led_fps_off = self.led_settings.get("fps_off", 60)

        # Extra Led Settings
        self.extra_led_settings: ExtraLedsTypedSettings = self.root_settings.get("extra_leds", [])

        self.extra_led_count = len(self.extra_led_settings)

        # Animation Settings
        self.animation_settings: AnimationTypedSettings = self.root_settings.get("animations", {})

        # Animations/Blink
        self.blink_animation_settings = self.animation_settings.get("blink", {})

        self.blink_animation_hz = self.blink_animation_settings.get("blink_hz", 2)

        # Animation/Fade
        self.fade_animation_settings = self.animation_settings.get("fade", {})

        self.fade_animation_multiplier = self.fade_animation_settings.get("fade_speed_multiplier", 0.75)

        # HA Settings
        self.ha_settings: HomeAssistantTypedSettings = self.root_settings.get("home_assistant", {})

        # Ha/Mqtt
        self.mqtt_settings = self.ha_settings.get("mqtt", {})

        self.mqtt_host = self.mqtt_settings.get("host", "homeassistant.local")
        self.mqtt_port = self.mqtt_settings.get("port", 1883)
        self.mqtt_user = os.environ.get("BROKER_USER", "") if self.mqtt_settings.get("username", "USE_ENV") == "USE_ENV" else self.mqtt_settings.get("username", "USE_ENV")
        self.mqtt_pass = os.environ.get("BROKER_PASS", "") if self.mqtt_settings.get("password", "USE_ENV") == "USE_ENV" else self.mqtt_settings.get("password", "USE_ENV")
        self.mqtt_timeout = self.mqtt_settings.get("connection_timeout", 6.0)

        # Ha/Device
        self.device_settings = self.ha_settings.get("device", {})

        self.device_name = self.device_settings.get("name", "AutoLight Device")
        self.device_id = self.device_settings.get("id", "autolight_0")

        # Ha/Light
        self.light_entity_settings = self.ha_settings.get("light_entity", {})

        self.light_name = self.light_entity_settings.get("name", "Main Control")
        self.light_icon = self.light_entity_settings.get("icon", "mdi:lightbulb")
        self.light_id = self.light_entity_settings.get("id", "autolight_main")

        # Ha/Debug
        self.debug_entity_settings = self.ha_settings.get("debugging_entities", {})

        self.create_debug_entities = self.debug_entity_settings.get("create_debug_entities", True)
        self.debug_update_rate = self.debug_entity_settings.get("update_rate", 15)

        # Logging Settings
        self.logging_settings: LoggingTypedSettings = self.root_settings.get("logging", {})

        self.interactive_log_level = self.logging_settings.get("interactive_log_level", "INFO")
        self.regular_log_level = self.logging_settings.get("regular_log_level", "WARNING")

        self.log_file_path = self.logging_settings.get("log_file", "logger.log")
        self.log_to_file = self.logging_settings.get("file_logging", False)

        self.rich_tracebacks = self.logging_settings.get("rich_traceback", True)

        # Misc Settings
        self.misc_settings: MiscTypedSettings = self.root_settings.get("misc", {})

        self.do_banner = self.misc_settings.get("do_banner", True)


