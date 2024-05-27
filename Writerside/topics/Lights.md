# Lighting Controllers

Currently, the only supported lighting controller is a single PCA9685.

The PCA9685 is connected to the system's main i2c bus. (The same one the VL53L0X sensors are run on)

## PCA9685 Specs

![PCA9685 PWM Driver](pca9685.png)

The PCA9685 has the following features
- Up to 1526Hz operating frequency
- 16 channels
- 12-bit <tooltip term="PWM">PWM</tooltip>

## Example Wiring

> **Warning**
> 
> Ensure that you are using 3.3v and not 5v. If using 5v, your Pi will be damaged!
>
{style="warning"}

![autolight_pca9685_bb.png](autolight_pca9685_bb.png)

## Configuration

Lighting controllers are configured in the [LED configuration segment](Configuration-Reference.md#main-led-segments-leds)

> **Warning**
> 
> When configuring an LED controller, ensure that there are an equal amount of sensors as there are led channels. 
> 
{style="note"}