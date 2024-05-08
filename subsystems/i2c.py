import smbus

def list_devices(bus: smbus.SMBus = smbus.SMBus(1)):
    addresses = []
    for address in range(3, 120): # dont run on reserved addressed
        try:
            bus.read_byte(address)
            addresses.append(address)
        except OSError:
            pass # nothing at address
    return addresses


if __name__ == "__main__":
    list_devices()