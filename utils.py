import platform
import ctypes
import os
import dbus

from loguru import logger

def surround_list(input: list[bool], radius=1):
    padded_lst = input.copy()  # Create a copy of the original list
    for i in range(len(input)):
        if input[i]:
            for j in range(1, radius + 1):
                if i - j >= 0:
                    padded_lst[i - j] = 1
                if i + j < len(input):
                    padded_lst[i + j] = 1
    return padded_lst

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

def is_os_64bit():
    return platform.machine().endswith('64')

def is_root():
    return os.getuid() == 0

def is_systemd():
    try:
        # Read the name of the process with PID 1
        with open('/proc/1/comm', 'r') as f:
            init_process_name = f.read().strip()
        
        # Check if it is 'systemd'
        return init_process_name == 'systemd'
    except Exception as e:
        # If there's an error (e.g., the /proc filesystem is not available), return False
        return False

def is_systemd_service_exists(service_name):
    try:
        bus = dbus.SystemBus()
        systemd1 = bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')

        # List all units
        units: list = manager.ListUnitFiles()
        for unit in units:
            if unit[0].split("/")[-1] == service_name + '.service':
                return True
        return False

    except dbus.DBusException as e:
        logger.warning(f"DBusException occurred: {repr(e)}")
        return False

def is_systemd_service_running(service_name):
    try:
        bus = dbus.SystemBus()
        systemd1 = bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')

        # List all active units
        units: list = manager.ListUnits()
        for unit in units:
            if unit[0] == service_name + '.service' and unit[3] == 'active' and unit[4] == 'running':
                return True
        return False

    except dbus.DBusException as e:
        logger.warning(f"DBusException occurred: {repr(e)}")
        return False

def start_systemd_service(service_name):
    try:
        bus = dbus.SystemBus()
        systemd1 = bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')
        
        # Start the service
        manager.StartUnit(service_name + '.service', 'replace')
        logger.info(f"The {service_name} service has been started.")
        return True
    except dbus.DBusException as e:
        logger.error(f"Failed to start the {service_name} service: {repr(e)}")
        return False

def is_systemd_service_enabled(service_name):
    try:
        bus = dbus.SystemBus()
        systemd1 = bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')

        # Get the unit file state
        unit_file_state = manager.GetUnitFileState(service_name + '.service')
        
        # Check if the unit file state indicates the service is enabled
        if unit_file_state == 'enabled':
            return True
        else:
            return False

    except dbus.DBusException as e:
        print(f"DBusException occurred: {e}")
        return False

def enable_systemd_service(service_name):
    try:
        bus = dbus.SystemBus()
        systemd1 = bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')
        
        # Enable the service
        manager.EnableUnitFiles([service_name + '.service'], False, True)
        logger.info(f"The {service_name} service has been enabled.")
        return True
    except dbus.DBusException as e:
        logger.error(f"Failed to enable the {service_name} service: {repr(e)}")
        return False

def daemon_reload_systemd():
    try:
        bus = dbus.SystemBus()
        systemd1 = bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')

        # Reload the systemd manager configuration
        manager.Reload()
        logger.info("systemd daemon-reload performed successfully.")
        return True
    except dbus.DBusException as e:
        logger.error(f"Failed to perform daemon-reload: {repr(e)}")
        return False

def square_wave(t, period, amplitude):
    """Generate square wave

    Args:
        t (float): X input
        period (float): Period of square wave
        amplitude (float): Amplitude of wave

    Returns:
        float: Y output
    """
    # Calculate the remainder when t is divided by T
    remainder = t % period

    # Determine the value of the square wave based on the remainder
    if remainder < period / 2:
        return amplitude
    return -amplitude

def terminate_thread(thread):
    """Terminates a python thread from another thread.

    :param thread: a threading.Thread instance
    """
    if not thread.isAlive():
        return

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
