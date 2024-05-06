import logging
import threading
import time
from gpiozero import DigitalOutputDevice
from adafruit_vl53l0x import VL53L0X as _VL53L0X

import board

from enum import Enum

class _StartupWarnings(Enum):
    NONE = 0
    ENDED = 1

class BaseSensor:
    pass

class NullSensor(BaseSensor):
    def __init__(self, trip_distance = None, constant_value = True) -> None:
        self.value = constant_value
        self.distance = trip_distance if constant_value else 999

class VL53L0XSensor(BaseSensor):
    _address = 0x30
    _warnings = _StartupWarnings.NONE
    _recovering = False
    def __init__(self, shut_pin: int, root_i2c: board.I2C = board.I2C(), trip_distance: float = 20) -> None:
        self._trip_distance = trip_distance
        self.shut_pin = shut_pin
        self.xshut = DigitalOutputDevice(self.shut_pin)
        self.xshut.value = 0
        self.root_i2c = root_i2c
        self.device = None

        self.tripped = False
        self.value = False
        self.distance = 999

        self._address = VL53L0XSensor._address
        VL53L0XSensor._address += 1

    def begin(self, thread=True):
        if VL53L0XSensor._warnings == _StartupWarnings.ENDED:
            logging.warning("A sensor is starting after this or another sensor has already stopped. This may result in unexpected behavior.")
        self.xshut.value = 1 # Power on device
        print(self._address, "xs_1")
        self.device = _VL53L0X(self.root_i2c)
        print(self._address, "start")
        self.device.start_continuous() # Start device at 0x29

        if thread:
            self._updater_thread = threading.Thread(target=self._update_loop, daemon=True)
            self._updater_thread.start()

        # Device will start out as 0x29, this is incremented up from 0x30 for each class
        self.device.set_address(self._address) 
        print(self._address, "setaddr")

    def end(self):
        if self.device:
            self.device.stop_continuous()
            self.xshut.value = 0
            VL53L0XSensor._warnings = _StartupWarnings.ENDED
        else:
            logging.warning(f"Could not end sensor for {self}, device has not yet been initialized")

    def start(self):
        if self.device:
            self.device.start_continuous()
        else:
            logging.warning(f"Could not re-start sensor for {self}, device has not yet been initialized")

    def stop(self):
        if self.device:
            self.device.stop_continuous()
        else:
            logging.warning(f"Could not stop sensor for {self}, device has not yet been initialized")

    def set_timing_budget(self, budget: int):
        if self.device:
            self.device.measurement_timing_budget = budget
        else:
            logging.error(f"Could not set timing budget for {self}, device has not yet been initialized")

    def set_trip_distance(self, trip_distance: float):
        self._trip_distance = trip_distance

    def _update_loop(self):
        while True:
            try:
                try:
                    self.distance = self.device.distance
                except OSError as e:
                    logging.error(f"Failed to read from i2c, {repr(e)}")
                    self.distance = -1
                    if not VL53L0XSensor._recovering:
                        VL53L0XSensor._recovering = True

                        logging.info(f"Attempting recovery for addr:{self._address}")
                        self.begin(thread=False)

                        VL53L0XSensor._recovering = False
                self.tripped = self.distance < self._trip_distance

                time.sleep(0.02)
            except OSError as e:
                logging.error(f"Failed to recover i2c, {repr(e)}, retrying...")
                VL53L0XSensor._recovering = False
                continue


