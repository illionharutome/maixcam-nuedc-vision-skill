def open_output(uart_module, config):
    if not config.get("enabled", False): return None
    try: return uart_module.UART(config.get("device", "auto"), int(config.get("baudrate", 115200)))
    except Exception as exc:
        print("UART disabled: %s" % exc); return None


def emit(serial, packet):
    print(packet)
    if serial is not None: serial.write((packet + "\r\n").encode("ascii"))
