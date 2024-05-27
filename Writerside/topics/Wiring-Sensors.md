# VL53L0X Sensors

![A common VL53L0X module. Title image](vl53l0x.png)

AutoLight supports the VL53L0X Optical Time-of-Flight sensor for distance measurements.

The VL53L0X datasheet is available [here](https://www.st.com/resource/en/datasheet/vl53l0x.pdf).

Sensors are wired using i2c and each individual XSHUT or SHDN pin is connected to one of the Pi's <tooltip term="GPIO">GPIO</tooltip> pins.
All sensors must be on the Pi's main bus and share the bus with the PCA9685. If this is not ideal for your use case, check out [Sensors controlled by GPIO](gpio-sensors.md).

> If your i2c bus is long, consider adding a LTC4311 to the end of the bus.
> I2C buffers can also be helpful.
{style="note"}

> Ensure to use 3.3v for powering your sensors.
> Your Pi will be damaged if using 5v.
{style="warning"}

<img alt="Basic sensor wiring" src="autolight_vl53l0x_bb.png" width="560"/>

<seealso>
       <category ref="related">
           <a href="Configuration-Reference.md#sensor-segment-sensors">Sensor configuration</a>
       </category>
</seealso>