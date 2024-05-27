# Installation

AutoLight is easy to install. Follow the steps and AutoLight will be functional in no time!

> **Note**
>
> This guide may work for other boards and OSes, but they are not supported. Proceed at your own risk!
>
{style="note"}

## Before you start

You must meet the minimum requirements

Make sure that you have:
- Raspberry Pi OS Bookworm
- A Pi4B, Pi3B, Pi3A, PiZero2, or a PiCM4 

## Installation steps

1. Install system dependencies

   ```bash
    sudo apt install python3-dev python3-venv git libdbus-1-dev libglib2.0-dev build-essential
   ```

2. Clone the AutoLight repo

   ```Bash
    git clone https://github.com/meowmeowahr/AutoLight
   ```

3. Change directory into AutoLight
   
   ```bash
    cd AutoLight
   ```

4. Create a new python environment

   ```bash
    python -m venv .venv
   ```

5. Source environment

   ```bash
    source .venv/bin/activate
   ```

6. Install Python dependencies

   ```bash
    pip install -r requirements.txt
   ```

🚀 AutoLight is now installed

## Autostart

> **Note**
>
> AutoLight will no longer autostart after being moved to another directory.
> If moving, follow the uninstall steps and then re-install it.
>
{style="warning"}

To Install AutoLight as a Systemd Service, run the following command

```Bash
python main.py --systemd-install
```

To Remove the service, run the following commands

```Bash
sudo systemctl stop autolight.service
sudo systemctl disable autolight.service
sudo rm /etc/systemd/system/autolight.service
sudo systemctl daemon-reload
```