import threading
import time

from loguru import logger

from gpiozero import DigitalOutputDevice
from adafruit_vl53l0x import VL53L0X as _VL53L0X

import board

from enum import Enum

from subsystems.i2c import list_devices as _list_i2c_devices

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
    _initial_address = 0x29
    _address_range = 0x30
    _warnings = _StartupWarnings.NONE
    _recovering = False
    _all_classes: list[BaseSensor] = []
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
        VL53L0XSensor._all_classes.append(self)

        logger.trace(f"Created a new class of VL53L0XSensor, using future address 0x{self._address:x}")
    def begin(self, thread=True):
        if VL53L0XSensor._warnings == _StartupWarnings.ENDED:
            logger.warning("A sensor is starting after this or another sensor has already stopped. This may result in unexpected behavior.")
        self.xshut.value = 1 # Power on device
        logger.debug(f"Sensor at future address {self._address} (decimal) has been powered on")
        self.device = _VL53L0X(self.root_i2c, address=VL53L0XSensor._initial_address)
        logger.debug(f"Sensor at future address {self._address} (decimal) has been initialized")
        self.device.start_continuous() # Start device at 0x29

        if thread:
            self._updater_thread = threading.Thread(target=self._update_loop, daemon=True)
            self._updater_thread.start()

        # Device will start out as 0x29, this is incremented up from 0x30 for each class
        self.device.set_address(self._address) 
        logger.debug(f"Sensor set address to {self._address} (decimal)")

    def end(self):
        if self.device:
            self.device.stop_continuous()
            self.xshut.value = 0
            VL53L0XSensor._warnings = _StartupWarnings.ENDED
        else:
            logger.warning(f"Could not end sensor for {self}, device has not yet been initialized")

    def start(self):
        if self.device:
            self.device.start_continuous()
        else:
            logger.warning(f"Could not re-start sensor for {self}, device has not yet been initialized")

    def stop(self):
        if self.device:
            self.device.stop_continuous()
        else:
            logger.warning(f"Could not stop sensor for {self}, device has not yet been initialized")

    @property
    def timing_budget(self):
        if self.device:
            return self.device.measurement_timing_budget
        else:
            logger.error(f"Could not get timing budget for {self}, device has not yet been initialized")

    @timing_budget.setter
    def timing_budget(self, budget: int):
        if self.device:
            self.device.measurement_timing_budget = budget
        else:
            logger.error(f"Could not get timing budget for {self}, device has not yet been initialized")

    @property
    def trip_distance(self):
        return self._trip_distance

    @trip_distance.setter
    def trip_distance(self, value: float):
        self._trip_distance = value

    def _update_loop(self):
        while True:
            try:
                try:
                    self.distance = self.device.distance
                except OSError as e:
                    logger.error(f"Failed to read from i2c, {repr(e)}")
                    time.sleep(0.5)
                    self.distance = -1

                    # recovery process
                    # only recover if the first sensor
                    if self._address == VL53L0XSensor._address_range:
                        if 0x29 not in _list_i2c_devices():
                            logger.warning("Address 0x29 not found, skipping recovery for now")
                            continue
                        print("here")
                        if not VL53L0XSensor._recovering:
                            print("here1")
                            VL53L0XSensor._recovering = True

                            logger.info(f"Attempting recovery for addr:{self._address}")

                            # Power off all devices
                            for obj in VL53L0XSensor._all_classes:
                                obj.xshut.value = 0

                            # Reinitialize all devices
                            for obj in VL53L0XSensor._all_classes:
                                obj.begin(thread=False)

                            VL53L0XSensor._recovering = False
                    else:
                        logger.trace(f"Device at address {self._address} != starting address {VL53L0XSensor._address_range}, not recovering from this thread")

                self.tripped = self.distance < self._trip_distance

                time.sleep(0.02)
            except (OSError, RuntimeError) as e:
                logger.error(f"Failed to recover i2c, {repr(e)}, retrying...")
                VL53L0XSensor._recovering = False
                continue


