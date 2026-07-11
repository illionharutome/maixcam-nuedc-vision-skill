#!/usr/bin/env python3
"""Send SINGLE frames to a debug-only ZET6 build and validate DBG replies."""

import argparse
import re
import time


CASES = [
    ("left_up", "$MV,SINGLE,1,140,110,160,120,-20,-10,CENTER,0,0.90,30.0,TRACKING#",
     lambda d: d["PAN"] < 0 and d["TILT"] < 0 and d["VALID"] == 1),
    ("right_down", "$MV,SINGLE,1,190,140,160,120,30,20,CENTER,0,0.90,30.0,TRACKING#",
     lambda d: d["PAN"] > 0 and d["TILT"] > 0 and d["VALID"] == 1),
    ("no_spot", "$MV,SINGLE,0,0,0,160,120,0,0,CENTER,0,0.00,30.0,NO_SPOT#",
     lambda d: d["PAN"] == 0 and d["TILT"] == 0 and d["VALID"] == 0 and d.get("STATE") in ("LOST", "NO_SPOT")),
    ("aimed", "$MV,SINGLE,1,162,119,160,120,2,-1,CENTER,0,0.95,30.0,AIMED#",
     lambda d: abs(d["PAN"]) <= 1 and abs(d["TILT"]) <= 1 and d["VALID"] == 1 and d.get("STATE") in ("AIMED", "LOCKED")),
]


def parse_dbg(text):
    match = re.search(r"\$DBG,SINGLE,([^#]+)#", text)
    if not match: return None
    parsed = {}
    for item in match.group(1).split(","):
        key, separator, value = item.partition("=")
        if separator: parsed[key] = int(value) if key in ("EX", "EY", "PAN", "TILT", "VALID", "STEP") else value
    return parsed


def exchange(serial, packet, timeout):
    serial.reset_input_buffer(); serial.write((packet + "\r\n").encode("ascii"))
    deadline, data = time.monotonic() + timeout, b""
    while time.monotonic() < deadline:
        data += serial.read(serial.in_waiting or 1)
        if b"$DBG,SINGLE" in data and b"#" in data: break
    return data.decode("ascii", errors="replace")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()
    try: import serial
    except ImportError: raise SystemExit("install pyserial: python -m pip install pyserial")
    passed = True
    with serial.Serial(args.port, args.baud, timeout=0.1) as port:
        for name, packet, check in CASES:
            response = exchange(port, packet, args.timeout)
            parsed = parse_dbg(response)
            ok = parsed is not None and check(parsed)
            print("%s: %s\n  send: %s\n  recv: %s" % (name, "PASS" if ok else "FAIL", packet, response.strip()))
            passed = passed and ok
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
