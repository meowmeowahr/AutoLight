import json
import logging
import sys
import threading
import atexit
import time

from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import (
    BinarySensor,
    BinarySensorInfo,
    DeviceInfo,
    Light,
    LightInfo,
)
from paho.mqtt.client import Client, MQTTMessage

from subsystems.leds import LedArray, LedSettings, NullAnimation, PowerUnits
from subsystems.sensors import VL53L0XSensor

from terminal import banner, FancyDisplay, is_interactive
from terminal import DisplayStatusTypes as StatusTypes

from utils import surround_list
from data_types import LightingData, LIGHT_EFFECTS, Animations

import checks
import settings

__version__ = "0.1.0"


class Main:
    def __init__(self) -> None:
        self.sensors = None

        # Application start time
        startup_time = time.time()

        # Visual setup
        if settings.DO_FANCY_TERM_OUT:
            banner()
        self.fancy_display = FancyDisplay(settings.FANCY_LOGGING_LEVELS if settings.DO_FANCY_TERM_OUT else [])
        atexit.register(self.at_exit)

        # Quick sanity checks
        if not checks.run_sanity(self.fancy_display):
            sys.exit()

        # Global lighting state
        self.lighting_data = LightingData()

        # Home Assistant Device Class
        self.device_info = DeviceInfo(name=settings.DEVICE_NAME, identifiers=settings.DEVICE_ID)

        # Create physical and Home Assistant sensors
        self.sensors, self.ha_sensors = self.create_sensors(self.device_info)
        self.fancy_display.display(StatusTypes.SUCCESS, f"Initialized {settings.SENSOR_COUNT} sensors of type {type(self.sensors[0]).__name__}")
        self.sensor_trips = [[]] * settings.SENSOR_COUNT

        # Physical led outputs
        self.led_array = LedArray(LedSettings(led_count=settings.LED_COUNT, freq=settings.LED_FREQ))
        self.fancy_display.display(StatusTypes.SUCCESS, f"Initialized {settings.LED_COUNT} leds over PCA")

        # Create Home Assistant Light
        self.ha_light, self.ha_light_info = self.create_ha_light(self.ha_light_callback, self.device_info)

        # Launch led thread
        self.led_update_thread = threading.Thread(target=self.led_array.update_loop, daemon=True)
        self.led_update_thread.start()

        # Sensor thread
        self.sensor_thread = threading.Thread(target=self.sensor_loop)
        self.sensor_thread.start()

        # Animation thread
        self.animator_thread = threading.Thread(target=self.animator_loop)
        self.animator_thread.start()

        self.fancy_display.display(StatusTypes.LAUNCH, f"Auto-Light version {__version__} is up!")
        self.fancy_display.display(StatusTypes.INFO, f"Startup time: {round(time.time() - startup_time, 2)}s")

    def ha_light_callback(self, client: Client, user_data, message: MQTTMessage):
        if not self.ha_light:
            logging.error("Callback was called without an existing ha_light")
            return

        if not self.ha_light_info:
            logging.error("Callback was called without an existing ha_light_info")
            return

        # Make sure received payload is json
        try:
            payload = json.loads(message.payload.decode())
        except ValueError as e:
            logging.error(f"Ony JSON schema is supported for light entities! {e}")
            return

        if "brightness" in payload:
            # for index in range(led_array.get_led_count()):
            #     led_array.set_brightness(index, payload["brightness"], subsystems.leds.PowerUnits.BITS8)
            self.lighting_data.brightness = payload["brightness"]
            self.ha_light.brightness(payload["brightness"])
        if "effect" in payload:
            # when changing effect led is auto-on
            # for index in range(led_array.get_led_count()):
            #     led_array.set_power_state(index, True)
            self.lighting_data.effect = LIGHT_EFFECTS[payload["effect"]]
            self.ha_light.effect(payload["effect"])
        if "state" in payload:
            if payload["state"] == self.ha_light_info.payload_on:
                # for index in range(led_array.get_led_count()):
                #     led_array.set_power_state(index, True)
                self.lighting_data.power = True
                self.ha_light.on()
            else:
                # for index in range(led_array.get_led_count()):
                #     led_array.set_power_state(index, False)
                self.lighting_data.power = False
                self.ha_light.off()
        else:
            logging.warning(f"Unknown payload: {payload}")

    def create_ha_light(self, callback, device_info):
        # Information about the light
        ha_light_info = LightInfo(
            name=settings.LIGHT_NAME,
            icon=settings.LIGHT_ICON,
            device=device_info,
            unique_id=settings.LIGHT_UID,
            brightness=True,
            color_mode=False,
            force_update=True,
            effect=True,
            effect_list=list(LIGHT_EFFECTS.keys()))

        ha_light_settings = Settings(mqtt=settings.MQTT_SETTINGS, entity=ha_light_info)

        ha_light = Light(ha_light_settings, callback)

        return ha_light, ha_light_info

    def create_sensors(self, device_info):
        sensors: list[VL53L0XSensor] = []
        ha_sensors: list[BinarySensor] = []

        for index, pin in enumerate(settings.SENSOR_XSHUT_PINS):
            # HA entity
            sensor_info = BinarySensorInfo(name=f"Staircase Segment {index+1}", device_class="motion", unique_id=f"stair_motion_{index}", device=device_info)
            ha_sensor = BinarySensor(Settings(mqtt=settings.MQTT_SETTINGS, entity=sensor_info))
            ha_sensors.append(ha_sensor)
            
            # Physical device
            sensor = VL53L0XSensor(pin)
            sensor.begin()
            sensor.set_timing_budget(settings.SENSOR_TIMING_BUDGET)
            sensor.set_trip_distance(settings.SENSOR_TRIP_DISTANCE)
            sensors.append(sensor)

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
            if self.lighting_data.power is False:
                for index in range(len(self.sensor_trips)):
                    self.led_array.set_power_state(index, False)
                continue

            if self.lighting_data.effect == Animations.WALKING:
                powers = surround_list(self.sensor_trips)
                for index, value in enumerate(powers):
                    self.led_array.set_power_state(index, value)
                    self.led_array.set_brightness(index, self.lighting_data.brightness, PowerUnits.BITS8)
                    self.led_array.set_animation(index, NullAnimation())

            time.sleep(0.1)

    def at_exit(self):
        if not self.sensors:
            self.fancy_display.display(StatusTypes.FAILURE, "Auto-Light experienced an error")
            return

        for sensor in self.sensors:
            sensor.end()
        
        self.fancy_display.display(StatusTypes.END, "Auto-Light stopped")

if __name__ == "__main__":
    # Create logger
    if is_interactive():
        logging.basicConfig(level=settings.INTERACTIVE_LOG_LEVEL)
    else:
        logging.basicConfig(level=settings.REGULAR_LOG_LEVEL)

    main = Main()    
