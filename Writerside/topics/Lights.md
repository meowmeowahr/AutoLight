# Lighting Controllers

Currently, the only supported lighting controller is a single PCA9685.

The PCA9685 is connected to the system's main i2c bus. (The same one the VL53L0X sensors are run on)

## PCA9685 Specs

![PCA9685 PWM Driver](pca9685.png)

The PCA9685 has the following features
- Up to 1526Hz operating frequency
- 16 channels
- 12-bit PWM