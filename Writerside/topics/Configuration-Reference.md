# Configuration Reference

## Sensor Segment `sensors`

The sensor segment is a list of the sensors being used in the system. 
It is recommended to have an equal number of sensors as there are leds.

- **VL53L0X Sensors:**
    - `type`: vl53l0x_i2c
    - `calibration`: Tripping distance in cm, supports floats
    - `xshut_pin`: XSHUT <tooltip term="GPIO">GPIO</tooltip> connection for this sensor
    - `timing_budget`: Calculation time in μS allotted to sensor, higher values result in better accuracy but may cause lag
- **GPIO Sensors**
  - `type`: gpio
  - `pin`: <tooltip term="GPIO">GPIO</tooltip> pin of the Pi to be used
  - `invert`: Invert thr HIGH/LOW values - default: false
  - `pullup`: Use the Pi's internal pullups - default: false
  - `bounce_time`: Time in seconds to counteract "bounce" - default: 0.0

Example usage:

```yaml
sensors:
 - type: vl53l0x_i2c
   calibration: 64
   xshut_pin: 21
   timing_budget: 72000
 - type: vl53l0x_i2c
   calibration: 65.2
   xshut_pin: 20
   timing_budget: 72000
```

## Main LED Segments `leds`

Currently, only one PCA9685 I2C PWM driver is supported.

- `count`: Number of LEDs for main channels
- `freq`: Operation frequency of each LED in Hertz (higher is usually better) - default: 200
- `fps_on`: LED update rate when the system is enabled  - default: 120
- `fps_off`: LED update rate when the system is disabled - default: 60

Example usage:

```yaml
leds:
  count: 2
  freq: 240
  fps_on : 60
  fps_off: 30
```

## Extra LED Channels `extra_leds`

The extra channels section is a list of each led/sensor pair

Each list element has the below options

- `channel`: PCA channel for extra light
- `ha_name`: Entity name to appear in Home Assistant
- `ha_icon`: Home Assistant Entity icon
- `ha_id`: Home Assistant Entity unique ID
- `gpio_pin`: Pi's GPIO pin for sensor
- `gpio_pullup`: Enable Pi's built-in pullup resistor - default: false
- `gpio_invert`: Invert sensor value - default: false

Example usage:
```yaml
extra_leds:
  - channel: 15
    ha_name: "Closet Lights"
    ha_icon: "mdi:lightbulb"
    ha_id: "extra1"
    gpio_pin: 11
    gpio_pullup: True
    gpio_invert: False
```

## Per-Animation Settings `animations`

- **Blink Animation `blink`:**
    - `blink_hz`: Blink rate in Hertz - default: 2
- **Fade Animation `fade`:**
    - `fade_speed_multiplier`: Fade speed multiplier - default: 0.75

Example usage:
```yaml
animations:
  blink:
    blink_hz: 4
  fade:
    fade_speed_multiplier: 1
```

## Home Assistant Connection and Entities

### MQTT Broker Settings

- `host`: Broker address
- `port`: Broker's Non-SSL MQTT port
- `username`: Broker username
- `password`: Broker password
- `connection_timeout`: Maximum time to attempt connection to MQTT

### Device Listing to Appear in Home Assistant

- `name`: Device name
- `id`: Device unique ID

### Main Controller Entity to Appear in Home Assistant

- `name`: Entity name
- `icon`: Entity icon
- `id`: Light unique ID

### Extra Entities Available for Monitoring CPU and Memory Usage

- `create_debug_entities`: Enabled or not
- `update_rate`: Update speed in seconds

---

## Terminal Logging Settings

Possible values are "TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL".

- `interactive_log_level`: Logging level for interactive terminals
- `regular_log_level`: Logging level for non-interactive sessions
- `log_file`: Optional file to send logs to
- `file_logging`: Enable logging to file
- `rich_traceback`: Enable rich tracebacks using the rich module (only available in interactive terminals)

---

## Misc Settings

- `do_banner`: Enable fancy banner for interactive sessions