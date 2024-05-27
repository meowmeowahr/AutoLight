import smbus2


def list_devices(bus: smbus2.SMBus = smbus2.SMBus(1)):
    addresses = []
    for address in range(3, 120):  # don't run on reserved addressed
        try:
            bus.read_byte(address)
            addresses.append(address)
        except OSError:
            pass  # nothing at address

    return addresses


if __name__ == "__main__":
    print(list_devices())
