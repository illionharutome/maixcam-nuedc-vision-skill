#!/usr/bin/env python3
"""Stage 2A: single-port USART1 GM mirror dry-run check.

Uses only one COM port (the same Type-C debug port as AIM/TRACK1).
Sends $MV,TRACK1 frames and reads both $DBG,TRACK1 and $GM,CMD
from the same serial stream.

Usage:
    python stm32_gimbal_mirror_usart1_check.py --port COM5 --baud 115200
"""

import argparse
import re
import time


CASES = [
    {
        "name": "tracking_left_up",
        "send": "$MV,TRACK1,1,140,110,160,120,-20,-10,0.90,30.0,TRACKING#",
        "dbg_check": lambda d: d["EX"] == -20 and d["EY"] == -10 and d["VALID"] == 1,
        "gm_check": lambda g: g["PAN"] != 0 or g["TILT"] != 0,
    },
    {
        "name": "tracking_right_down",
        "send": "$MV,TRACK1,1,190,140,160,120,30,20,0.90,30.0,TRACKING#",
        "dbg_check": lambda d: d["EX"] == 30 and d["EY"] == 20 and d["VALID"] == 1,
        "gm_check": lambda g: g["PAN"] != 0 or g["TILT"] != 0,
    },
    {
        "name": "no_target",
        "send": "$MV,TRACK1,0,0,0,160,120,0,0,0.00,30.0,NO_TARGET#",
        "dbg_check": lambda d: d["VALID"] == 0,
        "gm_check": lambda g: (g["PAN"] == 0 and g["TILT"] == 0 and
                               g.get("MODE", "") in ("STOP",)),
    },
    {
        "name": "aimed",
        "send": "$MV,TRACK1,1,162,119,160,120,2,-1,0.95,30.0,AIMED#",
        "dbg_check": lambda d: d["VALID"] == 1,
        "gm_check": lambda g: (g["PAN"] == 0 and g["TILT"] == 0 and
                               g.get("MODE", "") in ("AIMED",)),
    },
]

DBG_RE = re.compile(r"\$DBG,TRACK1,([^#]+)#")
GM_RE  = re.compile(r"\$GM,CMD,([^#]+)#")


def parse_kv(text):
    d = {}
    for item in text.split(","):
        k, s, v = item.partition("=")
        if s:
            d[k] = int(v) if k in ("EX", "EY", "PAN", "TILT", "VALID") else v
    return d


def read_all_lines(ser, timeout):
    ser.reset_input_buffer()
    deadline = time.monotonic() + timeout
    dbg_raw, gm_raw = None, None
    buf = b""
    while time.monotonic() < deadline:
        w = ser.in_waiting
        if w > 0:
            buf += ser.read(w)
        else:
            time.sleep(0.05)
    text = buf.decode("ascii", errors="replace")
    m = DBG_RE.search(text)
    if m:
        dbg_raw = m.group(1)
    m = GM_RE.search(text)
    if m:
        gm_raw = m.group(1)
    return dbg_raw, gm_raw


def main():
    try:
        import serial
    except ImportError:
        raise SystemExit("pyserial missing. Install: python -m pip install pyserial")

    p = argparse.ArgumentParser(description="Stage 2A USART1 GM mirror check")
    p.add_argument("--port", required=True, help="ZET6 USART1 COM port")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--timeout", type=float, default=4.0)
    args = p.parse_args()

    try:
        ser = serial.Serial(args.port, args.baud, timeout=0.1)
    except Exception as exc:
        raise SystemExit("Cannot open %s: %s" % (args.port, exc))

    from pathlib import Path
    log_dir = Path(__file__).resolve().parents[1] / "logs"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / "gimbal_mirror_usart1_check.txt"
    log = []
    passed = True

    try:
        for case in CASES:
            print("\n--- %s ---" % case["name"])
            print("  SEND: %s" % case["send"])
            log.append("CASE: %s  SEND: %s" % (case["name"], case["send"]))

            ser.write((case["send"] + "\r\n").encode("ascii"))
            dbg_raw, gm_raw = read_all_lines(ser, args.timeout)

            print("  DBG:  %s" % (dbg_raw or "TIMEOUT"))
            print("  GM:   %s" % (gm_raw or "TIMEOUT"))
            log.append("  DBG: %s" % (dbg_raw or "TIMEOUT"))
            log.append("  GM:  %s" % (gm_raw or "TIMEOUT"))

            dbg_parsed = parse_kv(dbg_raw) if dbg_raw else None
            gm_parsed  = parse_kv(gm_raw) if gm_raw else None

            fail = []
            if dbg_parsed:
                if not case["dbg_check"](dbg_parsed):
                    fail.append("DBG check failed")
            else:
                fail.append("DBG not parsed")

            if gm_parsed:
                if not case["gm_check"](gm_parsed):
                    fail.append("GM check failed")
            else:
                fail.append("GM not parsed")

            ok = not fail
            print("  %s: %s" % ("PASS" if ok else "FAIL", fail if fail else ""))
            log.append("  RESULT: %s %s" % ("PASS" if ok else "FAIL", fail if fail else ""))
            passed = passed and ok

            time.sleep(0.3)

    finally:
        ser.close()

    print("\n" + "=" * 50)
    print("OVERALL: %s" % ("PASS" if passed else "FAIL"))
    log.insert(0, "OVERALL: %s" % ("PASS" if passed else "FAIL"))
    log_path.write_text("\n".join(log), encoding="utf-8")
    print("Log: %s" % log_path)
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
