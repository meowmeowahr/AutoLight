import platform
import threading
import ctypes

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
