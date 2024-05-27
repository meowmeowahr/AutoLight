import sys
import os
import platform

import dbus
import elevate
from loguru import logger

from utils import get_non_root_user, is_root
from terminal import ask_yes_no


def is_systemd():
    try:
        # Read the name of the process with PID 1
        with open("/proc/1/comm", "r") as f:
            init_process_name = f.read().strip()

        # Check if it is 'systemd'
        return init_process_name == "systemd"
    except Exception:
        # If there's an error (e.g., the /proc filesystem is not available), return False
        return False


def is_systemd_service_exists(service_name):
    try:
        bus = dbus.SystemBus()
        systemd1 = bus.get_object(
            "org.freedesktop.systemd1", "/org/freedesktop/systemd1"
        )
        manager = dbus.Interface(systemd1, "org.freedesktop.systemd1.Manager")

        # List all units
        units: list = manager.ListUnitFiles()
        for unit in units:
            if unit[0].split("/")[-1] == service_name + ".service":
                return True
        return False

    except dbus.DBusException as e:
        logger.warning(f"DBusException occurred: {repr(e)}")
        return False


def is_systemd_service_running(service_name):
    try:
        bus = dbus.SystemBus()
        systemd1 = bus.get_object(
            "org.freedesktop.systemd1", "/org/freedesktop/systemd1"
        )
        manager = dbus.Interface(systemd1, "org.freedesktop.systemd1.Manager")

        # List all active units
        units: list = manager.ListUnits()
        for unit in units:
            if (
                unit[0] == service_name + ".service"
                and unit[3] == "active"
                and unit[4] == "running"
            ):
                return True
        return False

    except dbus.DBusException as e:
        logger.warning(f"DBusException occurred: {repr(e)}")
        return False


def start_systemd_service(service_name):
    try:
        bus = dbus.SystemBus()
        systemd1 = bus.get_object(
            "org.freedesktop.systemd1", "/org/freedesktop/systemd1"
        )
        manager = dbus.Interface(systemd1, "org.freedesktop.systemd1.Manager")

        # Start the service
        manager.StartUnit(service_name + ".service", "replace")
        logger.info(f"The {service_name} service has been started.")
        return True
    except dbus.DBusException as e:
        logger.error(f"Failed to start the {service_name} service: {repr(e)}")
        return False


def is_systemd_service_enabled(service_name):
    try:
        bus = dbus.SystemBus()
        systemd1 = bus.get_object(
            "org.freedesktop.systemd1", "/org/freedesktop/systemd1"
        )
        manager = dbus.Interface(systemd1, "org.freedesktop.systemd1.Manager")

        # Get the unit file state
        unit_file_state = manager.GetUnitFileState(service_name + ".service")

        # Check if the unit file state indicates the service is enabled
        if unit_file_state == "enabled":
            return True
        else:
            return False

    except dbus.DBusException as e:
        print(f"DBusException occurred: {e}")
        return False


def enable_systemd_service(service_name):
    try:
        bus = dbus.SystemBus()
        systemd1 = bus.get_object(
            "org.freedesktop.systemd1", "/org/freedesktop/systemd1"
        )
        manager = dbus.Interface(systemd1, "org.freedesktop.systemd1.Manager")

        # Enable the service
        manager.EnableUnitFiles([service_name + ".service"], False, True)
        logger.info(f"The {service_name} service has been enabled.")
        return True
    except dbus.DBusException as e:
        logger.error(f"Failed to enable the {service_name} service: {repr(e)}")
        return False


def daemon_reload_systemd():
    try:
        bus = dbus.SystemBus()
        systemd1 = bus.get_object(
            "org.freedesktop.systemd1", "/org/freedesktop/systemd1"
        )
        manager = dbus.Interface(systemd1, "org.freedesktop.systemd1.Manager")

        # Reload the systemd manager configuration
        manager.Reload()
        logger.info("systemd daemon-reload performed successfully.")
        return True
    except dbus.DBusException as e:
        logger.error(f"Failed to perform daemon-reload: {repr(e)}")
        return False

class SystemdInstaller:
    def __init__(self):
        if platform.system() != "Linux":
            logger.critical("Your system is not Linux, exiting now.")
            logger.warning("Operation cancelled.")
            sys.exit(0)

        if not is_systemd():
            logger.critical("Your Linux distro must run systemd. Exiting now.")
            logger.warning("Operation cancelled.")
            sys.exit(0)

        if not is_root():
            if not ask_yes_no(
                "This process will now be elevated as the root user. Do you want to Continue?"
            ):
                logger.warning("Operation cancelled.")
                sys.exit(0)
            else:
                logger.info("Elevating to root")

        elevate.elevate(graphical=False)
        if not ask_yes_no(
            "A Systemd Service to auto-start AutoLight on boot will now be installed. Do you want to Continue?"
        ):
            logger.warning("Operation cancelled.")
            sys.exit(0)

        # Check if service exists
        if is_systemd_service_exists("autolight"):
            logger.info("An AutoLight service already exists")
            if is_systemd_service_running("autolight"):
                logger.success("AutoLight service is already running")
            else:
                if ask_yes_no(
                    "AutoLight service exists, but is not running. Should I start it?"
                ):
                    start_systemd_service("autolight")
                    logger.success("AutoLight service has started.")

            if is_systemd_service_enabled("autolight"):
                logger.success("AutoLight service is enabled.")
            else:
                logger.info("AutoLight service is not enabled")
                if ask_yes_no(
                    "AutoLight service is not enabled for start on boot. Should I enabled it?"
                ):
                    enable_systemd_service("autolight")
                    logger.success("AutoLight service has been enabled.")
        else:
            logger.info("Service does not exist. Installing.")

            script_directory = os.path.dirname(os.path.abspath(__file__))
            source_file_path = os.path.join(
                script_directory, "extras/service/autolight.service"
            )

            if not os.path.exists("/etc/systemd/system"):
                logger.critical("/etc/systemd/system does not exist. Exiting")
                sys.exit(0)

            if not os.path.exists(source_file_path):
                logger.critical(f"{source_file_path} does not exist. Exiting")
                sys.exit(0)

            # Read the source file content
            with open(source_file_path, "r") as file:
                content = file.read()

            # Replace placeholders with provided values
            user = get_non_root_user()
            modified_content = content.format(
                user=user,
                cmd=f"{sys.executable} {os.path.abspath(__file__)}",
                wdir=script_directory,
            )

            # Write the modified content to the destination file
            with open("/etc/systemd/system/autolight.service", "w") as file:
                file.write(modified_content)

            logger.success("Copied service file")

            if daemon_reload_systemd():
                logger.success("Systemd Daemod Reloaded")
            else:
                logger.critical("Systemd Daemon failed to reload. Exiting")
                sys.exit(0)

            start_systemd_service("autolight")
            logger.success("AutoLight service has started.")

            enable_systemd_service("autolight")
            logger.success("AutoLight service has been enabled.")
