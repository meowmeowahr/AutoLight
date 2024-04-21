import asyncio
import logging
import gpiozero
import time
import w1thermsensor

class FanController:
    def __init__(self, pin: int):
        self._pwm = gpiozero.PWMOutputDevice(pin, frequency=100)
        self._fan_curve = {40: 10, 50: 25, 60: 45, 70: 80, 75: 95, 80: 100}
        self._pwm.on()
        self._pwm.value = 1.0

    def set_fan_curve(self, curve: dict):
        self._fan_curve = curve

    async def async_update(self, temperature: float):
        for temp in reversed(self._fan_curve.keys()):
            if temperature >= temp:
                logging.debug(f"Current system temp: {temperature}, Temp threshold: {temp}, Fan PWM: {self._fan_curve[temp]}")
                self._pwm.value = 1.0
                await asyncio.sleep(0.03)
                self._pwm.value = self._fan_curve[temp] / 100
                return
            
        self._pwm.value = 0.0

    def update(self, temperature: float):
        asyncio.run(self.async_update(temperature))

class ThermoFanController(FanController):
    def __init__(self, pin: int):
        super().__init__(pin)
        self._sensor = w1thermsensor.W1ThermSensor()

    def update(self):
        try:
            asyncio.run(self.async_update(self._sensor.get_temperature()))
        except w1thermsensor.SensorNotReadyError as e:
            logging.warning(f"Temperature read error: {e}")
            asyncio.run(self.async_update(50)) # assume a reasonable temperature for a little while

if __name__ == "__main__":
    # Controller demo
    fc = FanController(17)
    fc.set_fan_curve({40: 10, 50: 25, 60: 45, 70: 80, 75: 95, 80: 100})
    fc.update(40)
    time.sleep(1.5)
    fc.update(50)
    time.sleep(1.5)
    fc.update(60)
    time.sleep(1.5)
    fc.update(70)
    time.sleep(1.5)
    fc.update(75)
    time.sleep(1.5)
    fc.update(80)
    time.sleep(1.5)