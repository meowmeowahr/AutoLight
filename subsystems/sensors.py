import threading
import time

from loguru import logger

from gpiozero import DigitalOutputDevice, DigitalInputDevice
from adafruit_vl53l0x import VL53L0X as _VL53L0X

import board
import busio

from enum import Enum

class _StartupWarnings(Enum):
    NONE = 0
    ENDED = 1


class BaseSensor:
    pass


class NullSensor(BaseSensor):
    def __init__(self, trip_distance=None, constant_value=True) -> None:
        self.value = constant_value
        self.distance = trip_distance if constant_value else 999

class GPIOSensor(BaseSensor):
    def __init__(self, pin: int, invert: bool, pullup: bool = False, bounce_time: float = 0.0):
        self.device = DigitalInputDevice(pin, pull_up=pullup, active_state=not invert, bounce_time=bounce_time)
        self.device.when_activated = self._activated
        self.device.when_deactivated = self._deactivated

    def _activated(self):
        self.tripped = True

    def _deactivated(self):
        self.tripped = False

    def begin():
        raise NotImplementedError("This function is not implemented")

    def end():
        raise NotImplementedError("This function is not implemented")

    def start():
        raise NotImplementedError("This function is not implemented")

    def stop():
        raise NotImplementedError("This function is not implemented")

class VL53L0XSensor(BaseSensor):
    _address = 0x30
    _initial_address = 0x29
    _address_range = 0x30
    _warnings = _StartupWarnings.NONE
    _all_classes: list[BaseSensor] = []

    def __init__(
        self,
        shut_pin: int,
        root_i2c: board.I2C = busio.I2C(board.SCL, board.SDA),
        trip_distance: float = 20,
    ) -> None:

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

        self.updater_thread = threading.Thread(target=self._update_loop, daemon=True)

        logger.trace(
            f"Created a new class of VL53L0XSensor, using future address 0x{self._address:x}"
        )

    def begin(self, thread=True):
        if VL53L0XSensor._warnings == _StartupWarnings.ENDED:
            logger.warning(
                "A sensor is starting after this or another sensor has already stopped. This may result in unexpected behavior."
            )
        self.xshut.value = 1  # Power on device
        logger.debug(
            f"Sensor at future address 0x{self._address:x} has been powered on"
        )

        self.device = None

        self._create_root_device()

        logger.debug(
            f"Sensor at future address 0x{self._address:x} has been initialized"
        )
        self.device.start_continuous()  # Start device at 0x29

        if thread:
            self.updater_thread.start()

        # Device will start out as 0x29, this is incremented up from 0x30 for each class
        self.device.set_address(self._address)
        logger.debug(f"Sensor set address to 0x{self._address:x}")

    def _create_root_device(self):
        try:
            self.device = _VL53L0X(self.root_i2c, address=VL53L0XSensor._initial_address)
        except OSError as e:
            logger.error(f"Error trying to create new _VL53L0X, {repr(e)}, retrying in one second")
            time.sleep(1)
            self._create_root_device()

    def end(self):
        if self.device:
            self.xshut.value = 0
            VL53L0XSensor._warnings = _StartupWarnings.ENDED
        else:
            logger.warning(
                f"Could not end sensor for {self}, device has not yet been initialized"
            )

    def start(self):
        if self.device:
            self.device.start_continuous()
        else:
            logger.warning(
                f"Could not re-start sensor for {self}, device has not yet been initialized"
            )

    def stop(self):
        if self.device:
            self.device.stop_continuous()
        else:
            logger.warning(
                f"Could not stop sensor for {self}, device has not yet been initialized"
            )

    @property
    def timing_budget(self):
        if self.device:
            return self.device.measurement_timing_budget
        else:
            logger.error(
                f"Could not get timing budget for {self}, device has not yet been initialized"
            )

    @timing_budget.setter
    def timing_budget(self, budget: int):
        if self.device:
            self.device.measurement_timing_budget = budget
        else:
            logger.error(
                f"Could not get timing budget for {self}, device has not yet been initialized"
            )

    @property
    def trip_distance(self):
        return self._trip_distance

    @trip_distance.setter
    def trip_distance(self, value: float):
        self._trip_distance = value

    def _update_loop(self):
        cycle = 0
        while True:
            try:
                self.distance = self.device.distance
                if self.distance == -1:
                    raise OSError("Forced fail due to invalid reading")
                
                cycle += 1
                if cycle % 100 == 0:
                    logger.trace(
                        f"Sensor 0x{self._address:x} cycle: {cycle}, dist:{self.distance}"
                    )
            except OSError as e:
                logger.error(f"Failed to read from i2c, {repr(e)}")

            self.tripped = self.distance < self._trip_distance
