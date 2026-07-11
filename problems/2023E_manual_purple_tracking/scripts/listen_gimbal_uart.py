#!/usr/bin/env python3
"""Simple listener for the ZET6 USART3 gimbal dry UART.

Opens the USB-TTL COM port and prints every line received.
Use for observing $GM,BOOT,USART3,OK# or $GM,CMD output
during Stage 2 troubleshooting.

Usage:
    python listen_gimbal_uart.py --port COM6 --baud 115200
"""

import argparse
import time


def main():
    try:
        import serial
    except ImportError:
        raise SystemExit("pyserial missing. Install: python -m pip install pyserial")

    p = argparse.ArgumentParser(description="Listen on gimbal dry UART")
    p.add_argument("--port", required=True, help="USB-TTL COM port")
    p.add_argument("--baud", type=int, default=115200)
    args = p.parse_args()

    try:
        ser = serial.Serial(args.port, args.baud, timeout=0.2)
    except Exception as exc:
        raise SystemExit("Cannot open %s: %s" % (args.port, exc))

    print("Listening on %s at %d baud. Ctrl+C to stop." % (args.port, args.baud))
    try:
        while True:
            data = ser.read(ser.in_waiting or 1)
            if data:
                text = data.decode("ascii", errors="replace").rstrip()
                if text:
                    print(text)
            else:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
