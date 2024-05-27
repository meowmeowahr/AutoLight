import platform
import os


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
    return platform.machine().endswith("64")


def is_root():
    return os.getuid() == 0


def get_non_root_user():
    while True:
        # Read the contents of the /etc/passwd file to get a list of users
        with open("/etc/passwd", "r") as passwd_file:
            user_list = []
            for line in passwd_file:
                parts = line.strip().split(":")
                username = parts[0]
                home_dir = parts[5]
                # Include only users with a home directory and a valid shell (excluding nologin)
                if home_dir not in [
                    "/sbin/nologin",
                    "/bin/false",
                    "/nonexistent",
                    "/",
                    "/root",
                    "/bin",
                    "/dev",
                ] and os.path.isdir(home_dir):
                    user_list.append(username)

        # Prompt the user to enter a username
        username = input(f"Please enter your UNIX user ({','.join(user_list)}): ")

        # Check if the provided username is not root
        if username not in user_list:
            print(
                f"Error: User '{username}' is not allowed. Please choose from the list."
            )
        else:
            return username


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
