from dataclasses import dataclass
import math
import random
import threading
import time
import board
import busio
import adafruit_pca9685
import atexit
import enum

from loguru import logger


class PowerUnits(enum.Enum):
    """Units for led power setters"""

    BITS16 = 0
    BITS8 = 1
    PERCENT = 2


class LedSync(enum.Enum):
    """Sync multiple led channels"""

    SYNC = 0
    RANDOM_SYNC = 1
    RANDOM_UNSYNC = 2
    STAGGERED = 3


@dataclass
class BlinkAnimation:
    """Customizable blink animation"""

    on_time: float = 0.5
    off_time: float = 0.5
    sync: LedSync = LedSync.SYNC


@dataclass
class FadeAnimation:
    """Customizable fade animation"""

    speed_multiplier: float = 4
    sync: LedSync = LedSync.SYNC


@dataclass
class NullAnimation:
    """Steady brightness, animations disabled"""

    pass


@dataclass
class LedSettings:
    """Settings for LedArray"""

    led_count: int = 15
    freq: int = 60
    fps: int = 240
    auto_shutdown: bool = True


class PCA9685LedArray:
    """Array of PCA9685-Driven monochromatic leds starting at index 0"""

    def __init__(self, settings: LedSettings = LedSettings()) -> None:
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = adafruit_pca9685.PCA9685(self.i2c)
        self.pca.reset()

        if settings.auto_shutdown:
            atexit.register(self.end)

        self._led_data = [
            {"power": False, "brightness": 65535, "animation": NullAnimation()}
            for _ in range(settings.led_count)
        ]
        self._fps = settings.fps

        self.enable_recovery = True

        self.pca.frequency = settings.freq

        logger.debug(f"Created new LedArray with settings {settings}")

    def set_freq(self, freq: int):
        self.pca.frequency = freq

    def set_fps(self, fps: float):
        self._fps = fps

    def set_raw_channel_value(self, channel: int, brightness: int):
        self.pca.channels[channel].duty_cycle = brightness

    def get_led_count(self):
        return len(self._led_data)

    def set_brightness(
        self, index: int, brightness: float, unit: PowerUnits = PowerUnits.PERCENT
    ):
        if unit == PowerUnits.BITS16:
            self._led_data[index]["brightness"] = int(brightness)
        elif unit == PowerUnits.BITS8:
            self._led_data[index]["brightness"] = int(brightness * 257)
        elif unit == PowerUnits.PERCENT:
            self._led_data[index]["brightness"] = int(brightness * 65535)

    def set_animation(
        self,
        index: int,
        animation: NullAnimation | BlinkAnimation | FadeAnimation = NullAnimation(),
    ):
        self._led_data[index]["animation"] = animation

    def set_power_state(self, index: int, on: bool):
        if self._led_data[index]["power"] == on:
            return

        self._led_data[index]["power"] = on

    def end(self):
        logger.debug(f"Ended {self}")
        for channel in self.pca.channels:
            channel.duty_cycle = 0

    def update_loop(self):

        # Per-animation rngs
        last_rng_bools: list[bool | int] = [0] * len(self._led_data)
        last_rng_bools_time = 0

        while True:
            loop_time = time.time()
            time.sleep(1 / self._fps)
            try:
                for index, led in enumerate(self._led_data):
                    if self._led_data[index]["power"] is False:
                        self.pca.channels[index].duty_cycle = 0
                        continue

                    if isinstance(led["animation"], NullAnimation):
                        self.pca.channels[index].duty_cycle = self._led_data[index][
                            "brightness"
                        ]
                    elif isinstance(led["animation"], BlinkAnimation):
                        current_time = loop_time % (
                            led["animation"].on_time + led["animation"].off_time
                        )
                        wave_output = current_time < led["animation"].on_time
                        if led["animation"].sync == LedSync.SYNC:
                            if wave_output:
                                self.pca.channels[index].duty_cycle = self._led_data[
                                    index
                                ]["brightness"]
                            else:
                                self.pca.channels[index].duty_cycle = 0
                        elif led["animation"].sync == LedSync.STAGGERED:
                            if (not wave_output) if index % 2 else wave_output:
                                self.pca.channels[index].duty_cycle = self._led_data[
                                    index
                                ]["brightness"]
                            else:
                                self.pca.channels[index].duty_cycle = 0
                        elif led["animation"].sync == LedSync.RANDOM_SYNC:
                            if (
                                time.time() - last_rng_bools_time
                                >= led["animation"].on_time
                            ):
                                last_rng_bools = [
                                    random.getrandbits(1)
                                    for _ in range(len(self._led_data))
                                ]
                                last_rng_bools_time = time.time()
                            if last_rng_bools[0]:
                                self.pca.channels[index].duty_cycle = self._led_data[
                                    index
                                ]["brightness"]
                            else:
                                self.pca.channels[index].duty_cycle = 0
                        elif led["animation"].sync == LedSync.RANDOM_UNSYNC:
                            if (
                                time.time() - last_rng_bools_time
                                >= led["animation"].on_time
                            ):
                                last_rng_bools = [
                                    random.getrandbits(1)
                                    for _ in range(len(self._led_data))
                                ]
                                last_rng_bools_time = time.time()
                            if last_rng_bools[index]:
                                self.pca.channels[index].duty_cycle = self._led_data[
                                    index
                                ]["brightness"]
                            else:
                                self.pca.channels[index].duty_cycle = 0
                        else:
                            raise NotImplementedError(
                                f"Sync mode {led['animation'].sync} is not implemented"
                            )

                    elif isinstance(led["animation"], FadeAnimation):
                        wave_output = (
                            1
                            + (math.sin(loop_time * led["animation"].speed_multiplier))
                        ) / 2
                        if led["animation"].sync == LedSync.SYNC:
                            if wave_output:
                                self.pca.channels[index].duty_cycle = int(
                                    self._led_data[index]["brightness"] * wave_output
                                )
                            else:
                                self.pca.channels[index].duty_cycle = 0
                        elif led["animation"].sync == LedSync.STAGGERED:
                            if (not wave_output) if index % 2 else wave_output:
                                self.pca.channels[index].duty_cycle = int(
                                    self._led_data[index]["brightness"] * wave_output
                                )
                            else:
                                self.pca.channels[index].duty_cycle = int(
                                    self._led_data[index]["brightness"]
                                    * (1 - wave_output)
                                )
                        else:
                            raise NotImplementedError(
                                f"Sync mode {led['animation'].sync} is not implemented"
                            )
            except OSError as e:
                logger.error(f"Failed to read from i2c, {repr(e)}")
                if self.enable_recovery:
                    time.sleep(0.5)

                    try:
                        logger.debug(
                            f"Reloading PCA9685 driver using {self.pca.frequency}hz"
                        )
                        frequency = self.pca.frequency

                        self.pca = adafruit_pca9685.PCA9685(self.i2c)
                        self.pca.reset()

                        self.pca.frequency = frequency
                    except (OSError, RuntimeError) as e:
                        logger.error(f"Failed to recover i2c, {repr(e)}, retrying...")
                else:
                    logger.warning(
                        "PCA9685 experienced an error, and recovery is disabled"
                    )


if __name__ == "__main__":
    la = PCA9685LedArray()

    thread = threading.Thread(target=la.update_loop, daemon=True)
    thread.start()

    # la.set_brightness(0, .005)
    # la.set_brightness(1, .005)

    for i in range(14):
        la.set_power_state(i, True)
        # la.set_power_state(i, True)
        la.set_animation(i, FadeAnimation(sync=LedSync.SYNC))
        # la.set_animation(1, FadeAnimation(sync=LedSync.SYNC))

    while True:
        # la.set_power_state(0, True)
        # la.set_power_state(1, False)
        # time.sleep(1)
        # la.set_power_state(0, False)
        # la.set_power_state(1, True)
        time.sleep(1)
