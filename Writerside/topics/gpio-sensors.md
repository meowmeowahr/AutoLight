# GPIO Controlled Sensors

![Raspberry Pi Pinout Title Image](raspberry-pi-pinout.png)

Sensors are wired directly to <tooltip term="GPIO">GPIO</tooltip> pins. This is better is you are using non-VL53L0X sensors or are running very long distances.

> Ensure that you are not sending more than 3.5v into the Pi's <tooltip term="GPIO">GPIO</tooltip>.
> Use level shifters or voltage dividers if necessary.
{style="warning"}

Below is an example use of VL53L0X sensors connected to an arduino and then to the Pi's <tooltip term="GPIO">GPIO</tooltip>.

Example code for this setup can be found [here](https://github.com/meowmeowahr/VL53L0X_DigitalOut).

<img alt="Example use of VL53L0X sensors each connected to an Arduino, and sending a signal to the Pi&#39;s GPIO." src="autolight_vl53l0x_alt_bb.png" width="560"/>