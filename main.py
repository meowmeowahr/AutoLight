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
import platform
import functools
import os

from ha_mqtt_discoverable import Settings as HASettings
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
import elevate

from loguru import logger
from rich.traceback import install as traceback_install

from subsystems.leds import (
    PCA9685LedArray,
    PCA9685ExtraChannel,
    LedSettings,
    NullAnimation,
    PowerUnits,
    FadeAnimation,
)
from subsystems.sensors import VL53L0XSensor, GPIOSensor, NullSensor

from terminal import banner, is_interactive, ask_yes_no
from utils import (
    surround_list,
    is_os_64bit,
    square_wave,
    is_root,
    is_systemd,
    is_systemd_service_exists,
    is_systemd_service_running,
    start_systemd_service,
    is_systemd_service_enabled,
    enable_systemd_service,
    daemon_reload_systemd,
    get_non_root_user,
)
from data_types import (
    LightingData,
    LIGHT_EFFECTS,
    Animations,
    ExtraLightData,
    ExtraEffects,
    EXTRA_LIGHT_EFFECTS,
)

import checks
from settings import Settings

__version__ = "0.5.0"


class Main:
    def __init__(self, args) -> None:
        self.sensors = None
        self.ha_light = None

        # Application start time
        startup_time = time.time()

        # Visual setup
        if settings.do_banner:
            banner()

        atexit.register(self.at_exit)

        # Quick sanity checks
        if not checks.run_sanity(settings):
            sys.exit()

        # Network connectivity test
        network_available = False
        while not network_available:
            try:
                socket.getaddrinfo(
                    settings.mqtt_host,
                    settings.mqtt_port,
                )
                network_available = True
            except socket.gaierror as e:
                logger.error(f"Network test failed, retrying, {repr(e)}")
                time.sleep(1)

        # MQTT
        self.mqtt_settings = HASettings.MQTT(
            host=settings.mqtt_host,
            port=settings.mqtt_port,
            username=settings.mqtt_user,
            password=settings.mqtt_pass,
        )

        # Global lighting state
        self.lighting_data = LightingData()

        self.extra_lighting_data = [ExtraLightData()] * settings.extra_led_count

        # Home Assistant Device Class
        self.device_info = DeviceInfo(
            name=settings.device_name,
            identifiers=settings.device_id,
        )

        # Create physical and Home Assistant sensors
        self.sensors, self.ha_sensors = self.create_sensors(self.device_info)
        logger.info(
            f"Initialized {settings.sensor_count} sensors of type {type(self.sensors[0]).__name__}"
        )
        self.sensor_trips = [[]] * settings.sensor_count

        # Physical led outputs
        self.led_array = PCA9685LedArray(
            LedSettings(
                led_count=settings.led_count,
                freq=settings.led_freq,
                fps=settings.led_fps_on,
            )
        )
        logger.info(f"Initialized {settings.led_count} leds over PCA")

        # Create Home Assistant Light
        self.ha_light, self.ha_light_info = self.create_ha_light(
            self.ha_light_callback, self.device_info
        )

        # Create Home Asisstant Extra Lights
        self.extra_lights, self.ha_extra_lights = self.create_extra_lights(self.device_info)

        # Create Home Assistant Debug Devices
        self.cpu_sensor = None
        self.mem_sensor = None
        if settings.create_debug_entities:
            sensor_info = SensorInfo(
                device=self.device_info,
                name="CPU Usage",
                icon="mdi:cpu-64-bit" if is_os_64bit() else "mdi:cpu-32-bit",
                unit_of_measurement="%",
                unique_id="cpu",
            )
            self.cpu_sensor = Sensor(
                HASettings(mqtt=self.mqtt_settings, entity=sensor_info)
            )

            sensor_info = SensorInfo(
                device=self.device_info,
                name="Memory Usage",
                icon="mdi:memory",
                unit_of_measurement="%",
                unique_id="mem",
            )
            self.mem_sensor = Sensor(
                HASettings(mqtt=self.mqtt_settings, entity=sensor_info)
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

        # Extra Animation thread
        self.extra_animator_thread = threading.Thread(target=self.extra_animator_loop, daemon=True)
        if settings.extra_led_count > 0:
            self.extra_animator_thread.start()

        # Set light startup
        time.sleep(0.1)  # Home Assistant needs this small delay
        self.ha_light.brightness(255)
        self.ha_light.effect("Walking")
        self.ha_light.on()

        for light in self.ha_extra_lights:
            light.brightness(255)
            light.effect("Sensor")
            light.on()

        logger.success(f"Auto-Light version {__version__} is up!")
        logger.info(f"Startup time: {round(time.time() - startup_time, 2)}s")

        # Main loop
        while True:
            if self.cpu_sensor:
                self.cpu_sensor.set_state(psutil.cpu_percent())

            if self.mem_sensor:
                self.mem_sensor.set_state(psutil.virtual_memory()[2])

            time.sleep(settings.debug_update_rate)

    def ha_light_callback(self, client: Client, user_data, message: MQTTMessage):
        if not self.ha_light:
            logger.error("Callback was called without an existing ha_light")
            return

        if not self.ha_light_info:
            logger.error("Callback was called without an existing ha_light_info")
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

        logger.warning(f"Unknown light payload: {payload}")

    def ha_extra_light_callback(
        self, client: Client, user_data, message: MQTTMessage, index: int
    ):
        if not self.ha_extra_lights:
            logger.error("Callback was called without an existing ha_extra_lights")
            return

        # Make sure received payload is json
        try:
            payload = json.loads(message.payload.decode())
        except ValueError as e:
            logging.error(f"Ony JSON schema is supported for light entities! {e}")
            return

        if "brightness" in payload:
            self.extra_lighting_data[index].brightness = payload["brightness"]
            self.ha_extra_lights[index].brightness(payload["brightness"])
            return
        if "effect" in payload:
            self.extra_lighting_data[index].effect = EXTRA_LIGHT_EFFECTS[
                payload["effect"]
            ]
            self.ha_extra_lights[index].effect(payload["effect"])
            return
        if "state" in payload:
            if payload["state"] == self.ha_light_info.payload_on:
                self.extra_lighting_data[index].power = True
                self.ha_extra_lights[index].on()
            else:
                self.extra_lighting_data[index].power = False
                self.ha_extra_lights[index].off()
            return

    def create_ha_light(self, callback, device_info):
        # Information about the light
        ha_light_info = LightInfo(
            name=settings.light_name,
            icon=settings.light_icon,
            device=device_info,
            unique_id=settings.light_id,
            brightness=True,
            color_mode=False,
            effect=True,
            effect_list=list(LIGHT_EFFECTS.keys()),
        )

        ha_light_settings = HASettings(mqtt=self.mqtt_settings, entity=ha_light_info)

        ha_light = Light(ha_light_settings, callback)

        start_connect_time = time.time()
        while not ha_light.mqtt_client.is_connected():
            if time.time() - start_connect_time > settings.mqtt_timeout:
                logger.critical("MQTT Client Timeout")
                sys.exit()
            time.sleep(0.05)

        logger.success("MQTT Client Connected")

        return ha_light, ha_light_info

    def create_extra_lights(self, device_info):
        logger.debug(f"Using extra light config: {settings.extra_led_settings}")
        if not self.ha_light:
            logger.critical(
                "Extra lights are being created before main lights. Exiting"
            )
            sys.exit()

        ha_lights: list[Light] = []
        extra_lights: list[PCA9685ExtraChannel] = []

        for i in range(settings.extra_led_count):
            # Information about the light
            ha_light_info = LightInfo(
                name=settings.extra_led_settings[i].get(
                    "ha_name",
                    f"Extra Channel {settings.extra_led_settings[i].get('channel', '?')}",
                ),
                icon=settings.extra_led_settings[i].get("ha_icon", "mdi:lightbulb"),
                device=device_info,
                unique_id=settings.extra_led_settings[i].get(
                    "ha_id",
                    f"extra{settings.extra_led_settings[i].get('channel')}",
                ),
                brightness=True,
                color_mode=False,
                effect=True,
                effect_list=list(EXTRA_LIGHT_EFFECTS.keys()),
            )

            ha_light_settings = HASettings(
                mqtt=self.mqtt_settings, entity=ha_light_info
            )

            ha_lights.append(
                Light(
                    ha_light_settings,
                    functools.partial(self.ha_extra_light_callback, index=i),
                )
            )

            sensor_setting = settings.extra_led_settings[i].get('sensor')

            if sensor_setting.get("type") == "gpio":
                sensor = GPIOSensor(
                    sensor_setting.get("pin"),
                    sensor_setting.get("invert", False),
                    sensor_setting.get("pullup", False),
                    sensor_setting.get("bounce_time", 0)
                )
            else:
                sensor = NullSensor()

            extra_lights.append(
                PCA9685ExtraChannel(
                    self.led_array,
                    settings.extra_led_settings[i].get('channel'),
                    sensor
                )
            )

        return extra_lights, ha_lights

    def create_sensors(self, device_info):
        sensors: list[VL53L0XSensor | GPIOSensor] = []

        vl_sensors: list[VL53L0XSensor] = []
        vl_budgets: list[int] = []

        io_sensors: list[GPIOSensor] = []

        ha_sensors: list[BinarySensor] = []

        for sensor in settings.sensor_settings:
            logger.trace(f"Adding new sensor, {sensor}")
            if sensor.get("type") == "vl53l0x_i2c":
                s = VL53L0XSensor(
                    sensor.get("xshut_pin"), trip_distance=sensor.get("calibration")
                )
                vl_budgets.append(sensor.get("timing_budget"))
                vl_sensors.append(s)
            else:
                s = GPIOSensor(
                    sensor.get("pin"),
                    sensor.get("invert", False),
                    sensor.get("pullup", False),
                    sensor.get("bounce_time", 0.0),
                )
                io_sensors.append(s)
            sensors.append(s)

        for index, s in enumerate(vl_sensors):
            # Physical device
            vl_sensors[index].begin()
            vl_sensors[index].timing_budget = vl_budgets[index]

        for index in range(len(sensors)):
            # HA entity
            sensor_info = BinarySensorInfo(
                name=f"Staircase Segment {index+1}",
                device_class="motion",
                unique_id=f"stair_motion_{index}",
                device=device_info,
            )
            ha_sensor = BinarySensor(
                HASettings(mqtt=self.mqtt_settings, entity=sensor_info)
            )
            ha_sensors.append(ha_sensor)

        return sensors, ha_sensors

    def sensor_loop(self):
        while True:
            for i, s in enumerate(self.sensors):
                self.sensor_trips[i] = s.tripped
                self.ha_sensors[i]._update_state(self.sensor_trips[i])
                if isinstance(s, VL53L0XSensor):
                    self.ha_sensors[i].set_attributes({"distance": s.distance})
            time.sleep(0.05)

    def animator_loop(self):
        logger.info("Animation loop started")
        while True:
            time.sleep(
                1
                / (
                    settings.led_fps_on
                    if self.lighting_data.power
                    else settings.led_fps_off
                )
            )

            if self.lighting_data.power is False:
                for index in range(settings.led_count):
                    self.led_array.set_power_state(index, False)
                continue
            if self.lighting_data.effect == Animations.WALKING:
                powers = surround_list(self.sensor_trips, settings.walking_activation_radius)
                for index, value in enumerate(powers):
                    self.led_array.set_power_state(index, value)
                    self.led_array.set_brightness(
                        index, self.lighting_data.brightness, PowerUnits.BITS8
                    )
                    self.led_array.set_animation(index, NullAnimation())
            elif self.lighting_data.effect == Animations.STEADY:
                for i in range(settings.led_count):
                    self.led_array.set_power_state(i, True)
                    self.led_array.set_brightness(
                        i, self.lighting_data.brightness, PowerUnits.BITS8
                    )
                    self.led_array.set_animation(i, NullAnimation())
            elif self.lighting_data.effect == Animations.BLINK:
                if square_wave(time.time(), settings.blink_animation_hz, 1) == 1:
                    for index in range(settings.led_count):
                        self.led_array.set_power_state(index, True)
                        self.led_array.set_brightness(
                            index, self.lighting_data.brightness, PowerUnits.BITS8
                        )
                        self.led_array.set_animation(index, NullAnimation())
                else:
                    for index in range(settings.led_count):
                        self.led_array.set_power_state(index, False)
                        self.led_array.set_brightness(
                            index, self.lighting_data.brightness, PowerUnits.BITS8
                        )
                        self.led_array.set_animation(index, NullAnimation())
            elif self.lighting_data.effect == Animations.FADE:
                for index in range(settings.led_count):
                    self.led_array.set_power_state(index, True)
                    self.led_array.set_brightness(
                        index, self.lighting_data.brightness, PowerUnits.BITS8
                    )
                    self.led_array.set_animation(
                        index,
                        FadeAnimation(settings.fade_animation_multiplier),
                    )

    def extra_animator_loop(self):
        while True:
            time.sleep(1 / settings.led_fps_on)
            for index, light in enumerate(self.extra_lights):
                light.animation_cycle(self.extra_lighting_data[index])

    def at_exit(self):
        for sensor in self.sensors:
            if isinstance(sensor, VL53L0XSensor):
                sensor.end()

        logger.info("Auto-Light stopped")


class SystemdInstaller:
    def __init__(self):
        if platform.system() != "Linux":
            logger.critical("Your system is not Linux, exiting now.")
            logger.warning("Operation cancelled.")
            sys.exit(0)

        if not is_systemd():
            logger.critical("Your Linux distro must run systemd. Exiting now.")
            logger.warning("Operation cancelled.")
            sys.exit(0)

        if not is_root():
            if not ask_yes_no(
                "This process will now be elevated as the root user. Do you want to Continue?"
            ):
                logger.warning("Operation cancelled.")
                sys.exit(0)
            else:
                logger.info("Elevating to root")

        elevate.elevate(graphical=False)
        if not ask_yes_no(
            "A Systemd Service to auto-start AutoLight on boot will now be installed. Do you want to Continue?"
        ):
            logger.warning("Operation cancelled.")
            sys.exit(0)

        # Check if service exists
        if is_systemd_service_exists("autolight"):
            logger.info("An AutoLight service already exists")
            if is_systemd_service_running("autolight"):
                logger.success("AutoLight service is already running")
            else:
                if ask_yes_no(
                    "AutoLight service exists, but is not running. Should I start it?"
                ):
                    start_systemd_service("autolight")
                    logger.success("AutoLight service has started.")

            if is_systemd_service_enabled("autolight"):
                logger.success("AutoLight service is enabled.")
            else:
                logger.info("AutoLight service is not enabled")
                if ask_yes_no(
                    "AutoLight service is not enabled for start on boot. Should I enabled it?"
                ):
                    enable_systemd_service("autolight")
                    logger.success("AutoLight service has been enabled.")
        else:
            logger.info("Service does not exist. Installing.")

            script_directory = os.path.dirname(os.path.abspath(__file__))
            source_file_path = os.path.join(
                script_directory, "extras/service/autolight.service"
            )

            if not os.path.exists("/etc/systemd/system"):
                logger.critical("/etc/systemd/system does not exist. Exiting")
                sys.exit(0)

            if not os.path.exists(source_file_path):
                logger.critical(f"{source_file_path} does not exist. Exiting")
                sys.exit(0)

            # Read the source file content
            with open(source_file_path, "r") as file:
                content = file.read()

            # Replace placeholders with provided values
            user = get_non_root_user()
            modified_content = content.format(
                user=user,
                cmd=f"{sys.executable} {os.path.abspath(__file__)}",
                wdir=script_directory,
            )

            # Write the modified content to the destination file
            with open("/etc/systemd/system/autolight.service", "w") as file:
                file.write(modified_content)

            logger.success("Copied service file")

            if daemon_reload_systemd():
                logger.success("Systemd Daemod Reloaded")
            else:
                logger.critical("Systemd Daemon failed to reload. Exiting")
                sys.exit(0)

            start_systemd_service("autolight")
            logger.success("AutoLight service has started.")

            enable_systemd_service("autolight")
            logger.success("AutoLight service has been enabled.")


if __name__ == "__main__":
    # CLI Argument Parser
    parser = argparse.ArgumentParser(
        prog="Auto-Light",
        description="Control up to 16 leds with ToF sensors and additional GPIO channels",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}, using Python {platform.python_version()}",
    )

    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        type=str,
        help="YAML based configuration path",
        action="store",
    )

    parser.add_argument(
        "-V",
        "--verbose",
        default=False,
        help="Enable verbose logging",
        action="store_true",
    )
    parser.add_argument(
        "-Vt",
        "--trace",
        default=False,
        help="Enable extra-verbose trace logging",
        action="store_true",
    )

    parser.add_argument(
        "--systemd-install",
        default=False,
        help="Install systemd service to start on boot",
        action="store_true",
    )

    args = parser.parse_args()

    # Load settings
    settings = Settings(args.config)

    # Create logger
    if settings.rich_tracebacks and is_interactive():
        traceback_install(show_locals=True)

    if args.trace:
        log_level = 0
    elif args.verbose:
        log_level = logging.DEBUG
    elif is_interactive():
        log_level = settings.interactive_log_level
    else:
        log_level = settings.regular_log_level

    logger.remove()
    logger.add(sys.stderr, level=log_level)

    if settings.log_to_file:
        logger.add(settings.log_file_path, level=log_level)

    if args.systemd_install:
        main = SystemdInstaller()
        sys.exit(0)

    main = Main(args)
