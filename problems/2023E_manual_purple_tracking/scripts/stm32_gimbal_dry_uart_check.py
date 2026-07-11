#!/usr/bin/env python3
"""Stage 2 dual-serial check: debug-port sends $MV,TRACK1 and reads $DBG,TRACK1;
gimbal-port reads $GM,CMD from ZET6 USART2_TX via USB-TTL.

Usage:
    python stm32_gimbal_dry_uart_check.py --debug-port COM5 --gimbal-port COM7 --baud 115200
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
GM_RE = re.compile(r"\$GM,CMD,([^#]+)#")


def parse_kv(text: str) -> dict:
    d = {}
    for item in text.split(","):
        k, s, v = item.partition("=")
        if s:
            if k in ("EX", "EY", "PAN", "TILT", "VALID"):
                d[k] = int(v)
            else:
                d[k] = v
    return d


def flush_and_read(ser, marker: bytes, timeout: float) -> str:
    ser.reset_input_buffer()
    deadline = time.monotonic() + timeout
    buf = b""
    while time.monotonic() < deadline:
        w = ser.in_waiting
        if w > 0:
            buf += ser.read(w)
            if marker in buf and b"#" in buf:
                break
        else:
            time.sleep(0.05)
    return buf.decode("ascii", errors="replace").strip()


def main():
    try:
        import serial
    except ImportError:
        raise SystemExit("pyserial missing. Install: python -m pip install pyserial")

    p = argparse.ArgumentParser(description="Stage 2 gimbal dry UART check")
    p.add_argument("--debug-port", required=True, help="ZET6 USART1 COM port")
    p.add_argument("--gimbal-port", required=True, help="USB-TTL COM port (ZET6 USART2_TX)")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--timeout", type=float, default=4.0)
    args = p.parse_args()

    from pathlib import Path

    log_dir = Path(__file__).resolve().parents[1] / "logs"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / "gimbal_dry_uart_check.txt"
    log = []
    passed = True

    try:
        debug_ser = serial.Serial(args.debug_port, args.baud, timeout=0.1)
    except Exception as exc:
        raise SystemExit("Cannot open debug port %s: %s" % (args.debug_port, exc))
    try:
        gimbal_ser = serial.Serial(args.gimbal_port, args.baud, timeout=0.1)
    except Exception as exc:
        debug_ser.close()
        raise SystemExit("Cannot open gimbal port %s: %s" % (args.gimbal_port, exc))

    try:
        for case in CASES:
            print("\n--- %s ---" % case["name"])
            print("  SEND: %s" % case["send"])
            log.append("CASE: %s  SEND: %s" % (case["name"], case["send"]))

            debug_ser.write((case["send"] + "\r\n").encode("ascii"))
            resp = flush_and_read(debug_ser, b"$DBG,TRACK1", args.timeout)
            print("  DBG:  %s" % (resp or "TIMEOUT"))
            log.append("  DBG: %s" % (resp or "TIMEOUT"))

            gm = flush_and_read(gimbal_ser, b"$GM,CMD", args.timeout)
            print("  GM:   %s" % (gm or "TIMEOUT"))
            log.append("  GM:  %s" % (gm or "TIMEOUT"))

            dbg_parsed = None
            gm_parsed = None

            m = DBG_RE.search(resp) if resp else None
            if m:
                dbg_parsed = parse_kv(m.group(1))

            m = GM_RE.search(gm) if gm else None
            if m:
                gm_parsed = parse_kv(m.group(1))

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
        debug_ser.close()
        gimbal_ser.close()

    print("\n" + "=" * 50)
    print("OVERALL: %s" % ("PASS" if passed else "FAIL"))
    log.insert(0, "OVERALL: %s" % ("PASS" if passed else "FAIL"))
    log_path.write_text("\n".join(log), encoding="utf-8")
    print("Log: %s" % log_path)
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
