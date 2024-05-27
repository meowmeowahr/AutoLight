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

### Blink Animation `blink`
- `blink_hz`: Blink rate in Hertz - default: 2

### Fade Animation `fade`
- `fade_speed_multiplier`: Fade speed multiplier - default: 0.75

Example usage:
```yaml
animations:
  blink:
    blink_hz: 4
  fade:
    fade_speed_multiplier: 1
```

## Home Assistant and Entities `home_assistant`

### MQTT Broker Settings `mqtt`

> **Tip**
> It is **never** recommended to store passwords in the plain text config file.
> Use the `USE_ENV` option to use environment variables

The username and password options can be set to `USE_ENV` to use the `BROKER_USER` and `BROKER_PASS` environment variables respectively.
The values will default to blank if the variable isn't defined.

- `host`: Broker address - default: "homeassistant.local"
- `port`: Broker's Non-SSL MQTT port - default: 1883
- `username`: Broker username - default: "USE_ENV"
- `password`: Broker password - default: "USE_ENV"
- `connection_timeout`: Maximum time to attempt connection to MQTT - default: 6

### Device Listing `device`

- `name`: Device name - default: "AutoLight Device"
- `id`: Device unique ID - default: "autolight_0"

### Main Controller Entity to Appear in Home Assistant `light_entity`

- `name`: Entity name - default: "Main Control"
- `icon`: Entity icon - default: "mdi:lightbulb"
- `id`: Light unique ID - default: "autolight_main"

### Extra Entities Available for CPU and Memory Usage `debugging_entities`

- `create_debug_entities`: Enabled or not - default: true
- `update_rate`: Update speed in seconds - default: 15

Example usage:
```yaml
home_assistant:
  mqtt:
    host: "homeassistant.local"
    port: 1883
    username: "USE_ENV"
    password: "USE_ENV"
    connection_timeout: 8
  device:
    name: "Staircase Lighting"
    id: "sl"
  light_entity:
    name: "Main Control"
    icon: "mdi:stairs"
    id: "light_staircase"
  debugging_entities:
    create_debug_entities: True
    update_rate: 15.0
```

## Terminal Logging Settings `logging`

Possible log level values are `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

- `interactive_log_level`: Logging level for interactive terminals - default: `INFO`
- `regular_log_level`: Logging level for non-interactive sessions - default: `WARNING`
- `log_file`: Optional file to send logs to - default: "logger.log"
- `file_logging`: Enable logging to file - default: false
- `rich_traceback`: Enable rich tracebacks using the rich module (only available in interactive terminals) - default: true

## Misc Settings

- `do_banner`: Enable fancy startup banner for interactive sessions - default: true