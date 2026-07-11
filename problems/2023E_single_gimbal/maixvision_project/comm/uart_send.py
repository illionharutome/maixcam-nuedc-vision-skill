def open_output(uart_module, config):
    if not config.get("enabled", False):
        return None
    device = config.get("device", "auto")
    baud = int(config.get("baudrate", 115200))
    try:
        return uart_module.UART(device, baud)
    except Exception as exc:
        print("UART disabled after open failure: %s" % exc)
        return None


def emit(serial, packet):
    print(packet)
    if serial is not None:
        serial.write((packet + "\r\n").encode("ascii"))
