"""
Auto-Light
Raspberry Pi controlled VL53L0X activated lights via PCA9685
"""

import argparse
import json
import logging
import sys
import threading
import atexit
import time
import socket

from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import (
    BinarySensor,
    BinarySensorInfo,
    Sensor,
    SensorInfo,
    DeviceInfo,
    Light,
    LightInfo,
)
from paho.mqtt.client import Client, MQTTMessage

import psutil

import structlog
from rich.traceback import install as traceback_install

from subsystems.leds import (
    LedArray,
    LedSettings,
    NullAnimation,
    PowerUnits,
    FadeAnimation,
)
from subsystems.sensors import VL53L0XSensor

from terminal import banner, is_interactive

from utils import surround_list, is_os_64bit, square_wave
from data_types import LightingData, LIGHT_EFFECTS, Animations

import checks
import settings

__version__ = "0.1.0"


class Main:
    def __init__(self, args) -> None:
        self.sensors = None
        self.ha_light = None

        # Application start time
        startup_time = time.time()

        # Visual setup
        if settings.DO_BANNER:
            banner()

        self.logger: structlog.BoundLogger = structlog.get_logger()

        atexit.register(self.at_exit)

        # Quick sanity checks
        if not checks.run_sanity(self.logger):
            sys.exit()

        # Network connectivity test
        network_available = False
        while not network_available:
            try:
                socket.getaddrinfo(
                    settings.MQTT_SETTINGS.host, settings.MQTT_SETTINGS.port
                )
                network_available = True
            except socket.gaierror as e:
                self.logger.error(f"Network test failed, retrying, {repr(e)}")
                time.sleep(1)

        # Global lighting state
        self.lighting_data = LightingData()

        # Home Assistant Device Class
        self.device_info = DeviceInfo(
            name=settings.DEVICE_NAME, identifiers=settings.DEVICE_ID
        )

        # Create physical and Home Assistant sensors
        self.sensors, self.ha_sensors = self.create_sensors(self.device_info)
        self.logger.info(f"Initialized {settings.SENSOR_COUNT} sensors of type {type(self.sensors[0]).__name__}")
        self.sensor_trips = [[]] * settings.SENSOR_COUNT

        # Physical led outputs
        self.led_array = LedArray(
            LedSettings(
                led_count=settings.LED_COUNT,
                freq=settings.LED_FREQ,
                fps=settings.LED_FPS,
            )
        )
        self.logger.info(f"Initialized {settings.LED_COUNT} leds over PCA")

        # Create Home Assistant Light
        self.ha_light, self.ha_light_info = self.create_ha_light(
            self.ha_light_callback, self.device_info
        )

        # Create Home Assistant Debug Devices
        self.cpu_sensor = None
        self.mem_sensor = None
        if settings.CREATE_DEBUG_ENTITIES:
            sensor_info = SensorInfo(
                device=self.device_info,
                name="CPU Usage",
                icon="mdi:cpu-64-bit" if is_os_64bit() else "mdi:cpu-32-bit",
                unit_of_measurement="%",
                unique_id="cpu",
            )
            self.cpu_sensor = Sensor(
                Settings(mqtt=settings.MQTT_SETTINGS, entity=sensor_info)
            )

            sensor_info = SensorInfo(
                device=self.device_info,
                name="Memory Usage",
                icon="mdi:memory",
                unit_of_measurement="%",
                unique_id="mem",
            )
            self.mem_sensor = Sensor(
                Settings(mqtt=settings.MQTT_SETTINGS, entity=sensor_info)
            )

        # Launch led thread
        self.led_update_thread = threading.Thread(
            target=self.led_array.update_loop, daemon=True
        )
        self.led_update_thread.start()

        # Sensor thread
        self.sensor_thread = threading.Thread(target=self.sensor_loop, daemon=True)
        self.sensor_thread.start()

        # Animation thread
        self.animator_thread = threading.Thread(target=self.animator_loop, daemon=True)
        self.animator_thread.start()

        # Set light startup
        time.sleep(0.1)  # Home Assistant needs this small delay
        self.ha_light.brightness(255)
        self.ha_light.effect("Walking")
        self.ha_light.on()

        self.logger.info(f"Auto-Light version {__version__} is up!")
        self.logger.info(f"Startup time: {round(time.time() - startup_time, 2)}s")

    def ha_light_callback(self, client: Client, user_data, message: MQTTMessage):
        if not self.ha_light:
            self.logger.error("Callback was called without an existing ha_light")
            return

        if not self.ha_light_info:
            self.logger.error("Callback was called without an existing ha_light_info")
            return

        # Make sure received payload is json
        try:
            payload = json.loads(message.payload.decode())
        except ValueError as e:
            logging.error(f"Ony JSON schema is supported for light entities! {e}")
            return

        if "brightness" in payload:
            self.lighting_data.brightness = payload["brightness"]
            self.ha_light.brightness(payload["brightness"])
            return
        if "effect" in payload:
            self.lighting_data.effect = LIGHT_EFFECTS[payload["effect"]]
            self.ha_light.effect(payload["effect"])
            return
        if "state" in payload:
            if payload["state"] == self.ha_light_info.payload_on:
                self.lighting_data.power = True
                self.ha_light.on()
            else:
                self.lighting_data.power = False
                self.ha_light.off()
            return

        self.logger.warning(f"Unknown light payload: {payload}")

    def create_ha_light(self, callback, device_info):
        # Information about the light
        ha_light_info = LightInfo(
            name=settings.LIGHT_NAME,
            icon=settings.LIGHT_ICON,
            device=device_info,
            unique_id=settings.LIGHT_UID,
            brightness=True,
            color_mode=False,
            effect=True,
            effect_list=list(LIGHT_EFFECTS.keys()),
        )

        ha_light_settings = Settings(mqtt=settings.MQTT_SETTINGS, entity=ha_light_info)

        ha_light = Light(ha_light_settings, callback)

        start_connect_time = time.time()
        while not ha_light.mqtt_client.is_connected():
            if time.time() - start_connect_time > settings.MQTT_CONNECTION_TIMEOUT:
                self.logger.critical("MQTT Client Timeout")
                sys.exit()
            time.sleep(0.05)

        self.logger.info("MQTT Client Connected")

        return ha_light, ha_light_info

    def create_sensors(self, device_info):
        sensors: list[VL53L0XSensor] = []
        ha_sensors: list[BinarySensor] = []

        for pin in settings.SENSOR_XSHUT_PINS[: settings.SENSOR_COUNT]:
            sensors.append(VL53L0XSensor(pin))

        for index, pin in enumerate(
            settings.SENSOR_XSHUT_PINS[: settings.SENSOR_COUNT]
        ):
            # HA entity
            sensor_info = BinarySensorInfo(
                name=f"Staircase Segment {index+1}",
                device_class="motion",
                unique_id=f"stair_motion_{index}",
                device=device_info,
            )
            ha_sensor = BinarySensor(
                Settings(mqtt=settings.MQTT_SETTINGS, entity=sensor_info)
            )
            ha_sensors.append(ha_sensor)

            # Physical device
            sensors[index].begin()
            sensors[index].timing_budget = settings.SENSOR_TIMING_BUDGET
            sensors[index].trip_distance = settings.PER_SENSOR_CALIBRATIONS[index]

        return sensors, ha_sensors

    def sensor_loop(self):
        while True:
            for i, s in enumerate(self.sensors):
                self.sensor_trips[i] = s.tripped
                self.ha_sensors[i]._update_state(self.sensor_trips[i])
                self.ha_sensors[i].set_attributes({"distance": s.distance})
            time.sleep(0.05)

    def animator_loop(self):
        while True:
            time.sleep(
                1
                / (
                    settings.LED_FPS
                    if self.lighting_data.power
                    else settings.LED_OFF_FPS
                )
            )

            if self.lighting_data.power is False:
                self.led_array.raw_brightness = False
                for index in range(settings.LED_COUNT):
                    self.led_array.set_power_state(index, False)
                continue

            if self.lighting_data.effect == Animations.WALKING:
                self.led_array.raw_brightness = False
                powers = surround_list(self.sensor_trips)
                for index, value in enumerate(powers):
                    self.led_array.set_power_state(index, value)
                    self.led_array.set_brightness(
                        index, self.lighting_data.brightness, PowerUnits.BITS8
                    )
                    self.led_array.set_animation(index, NullAnimation())
            elif self.lighting_data.effect == Animations.STEADY:
                self.led_array.raw_brightness = False
                for i in range(settings.LED_COUNT):
                    self.led_array.set_power_state(i, True)
                    self.led_array.set_brightness(
                        i, self.lighting_data.brightness, PowerUnits.BITS8
                    )
                    self.led_array.set_animation(i, NullAnimation())
            elif self.lighting_data.effect == Animations.BLINK:
                self.led_array.raw_brightness = False
                if square_wave(time.time(), settings.BLINK_HZ, 1) == 1:
                    for index in range(settings.LED_COUNT):
                        self.led_array.set_power_state(index, True)
                        self.led_array.set_brightness(
                            index, self.lighting_data.brightness, PowerUnits.BITS8
                        )
                        self.led_array.set_animation(index, NullAnimation())
                else:
                    for index in range(settings.LED_COUNT):
                        self.led_array.set_power_state(index, False)
                        self.led_array.set_brightness(
                            index, self.lighting_data.brightness, PowerUnits.BITS8
                        )
                        self.led_array.set_animation(index, NullAnimation())
            elif self.lighting_data.effect == Animations.FADE:
                for index in range(settings.LED_COUNT):
                    self.led_array.set_power_state(index, True)
                    self.led_array.set_brightness(
                        index, self.lighting_data.brightness, PowerUnits.BITS8
                    )
                    self.led_array.set_animation(
                        index, FadeAnimation(settings.FADE_SPEED_MULTIPLIER)
                    )

    def at_exit(self):
        if not self.sensors:
            self.logger.error("Auto-Light experienced an error")
            return

        for sensor in self.sensors:
            sensor.end()

        self.logger.info("Auto-Light stopped")


if __name__ == "__main__":
    # CLI Argument Parser
    parser = argparse.ArgumentParser(
        prog="Auto-Light",
        description="Control up to 16 leds with ToF sensors and an additional PIR channel",
    )

    parser.add_argument("-V", "--verbose", default=False, action="store_true")

    args = parser.parse_args()

    # Create logger
    traceback_install(show_locals=False)

    if is_interactive():
        log_level = settings.INTERACTIVE_LOG_LEVEL if not args.verbose else logging.DEBUG
    else:
        log_level = settings.REGULAR_LOG_LEVEL if not args.verbose else logging.DEBUG

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )

    main = Main(args)

    # Main loop
    while True:
        if main.cpu_sensor:
            main.cpu_sensor.set_state(psutil.cpu_percent())

        if main.mem_sensor:
            main.mem_sensor.set_state(psutil.virtual_memory()[2])

        time.sleep(settings.DEBUG_UPDATE_RATE)
