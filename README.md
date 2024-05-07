# Auto-Light
Raspberry Pi controlled VL53L0X activated lights via PCA9685

## Hardware Requirements

* A Raspberry Pi (Original Pi Zero and Original Pi A/B are not supported)
* PCA9685
* Up to 16 VL53L0X sensors
* As many leds as there are sensors

## Installation

### Software requirements

Raspberry Pi OS Bookworm (Older OSes may work with pyenv and building lgpio from source)

### System Dependencies
Install these before Python dependencies

`sudo apt install python3-dev`

### Python Dependencies

* Change directory into AutoLight

    `cd AutoLight`

* Setting virtual environment

    `python3 -m venv .venv`

* Source environment
    
    `source .venv/bin/activate`

* Install dependencies

    `pip install -r requirements.txt`

### 🚀 AutoLight is now installed