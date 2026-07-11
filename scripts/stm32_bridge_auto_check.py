#!/usr/bin/env python3
"""STM32 ZET6 debug bridge automated serial check.

Sends $MV,AIM test frames over COM port, reads $DBG,AIM responses,
validates each frame against expected values, and optionally calls
DeepSeek API for log analysis.

Usage:
    python scripts/stm32_bridge_auto_check.py --port COM5 --baud 115200
    python scripts/stm32_bridge_auto_check.py --port COM5 --baud 115200 --deepseek
"""

import argparse
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path


def check_pyserial():
    try:
        import serial  # noqa: F401
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Test frames and expected constraints
# ---------------------------------------------------------------------------
TEST_FRAMES = [
    {
        "name": "AIMING -12,12",
        "send": "$MV,AIM,1,160,120,148,132,-12,12,0.91,25.6,AIMING#",
        "expect": {
            "EX": lambda v: v == -12,
            "EY": lambda v: v == 12,
            "PAN": lambda v: v < 0,
            "TILT": lambda v: v > 0,
            "VALID": lambda v: v == 1,
        },
        "expect_desc": "EX=-12, EY=12, PAN<0, TILT>0, VALID=1",
    },
    {
        "name": "AIMING 30,0",
        "send": "$MV,AIM,1,160,120,190,120,30,0,0.91,25.6,AIMING#",
        "expect": {
            "EX": lambda v: v == 30,
            "EY": lambda v: v == 0,
            "PAN": lambda v: v > 0,
            "TILT": lambda v: v == 0,
            "VALID": lambda v: v == 1,
        },
        "expect_desc": "EX=30, EY=0, PAN>0, TILT=0, VALID=1",
    },
    {
        "name": "NO_SPOT",
        "send": "$MV,AIM,0,160,120,0,0,0,0,0.00,25.6,NO_SPOT#",
        "expect": {
            "VALID": lambda v: v == 0,
            "PAN": lambda v: v == 0,
            "TILT": lambda v: v == 0,
        },
        "expect_desc": "VALID=0, PAN=0, TILT=0, (STATUS=NO_SPOT or STATE=NO_SPOT)",
        "extra_checks": [
            ("STATUS or STATE", lambda p: p.get("STATUS", "") == "NO_SPOT"
                                          or p.get("STATE", "") == "NO_SPOT"),
        ],
    },
    {
        "name": "AIMED 2,-1",
        "send": "$MV,AIM,1,160,120,162,119,2,-1,0.95,25.6,AIMED#",
        "expect": {
            "EX": lambda v: v == 2,
            "EY": lambda v: v == -1,
            "VALID": lambda v: v == 1,
            "PAN": lambda v: abs(v) <= 1,
            "TILT": lambda v: abs(v) <= 1,
        },
        "expect_desc": "EX=2, EY=-1, VALID=1, PAN~0, TILT~0, STATE=LOCKED",
        "extra_checks": [
            ("STATE", lambda p: p.get("STATE", "") in ("LOCKED", "AIMED")),
        ],
    },
]

DBG_RE = re.compile(
    r"\$DBG,AIM"
    r"(?:,EX=(?P<EX>-?\d+))?"
    r"(?:,EY=(?P<EY>-?\d+))?"
    r"(?:,CX=(?P<CX>-?\d+))?"
    r"(?:,CY=(?P<CY>-?\d+))?"
    r"(?:,SX=(?P<SX>-?\d+))?"
    r"(?:,SY=(?P<SY>-?\d+))?"
    r"(?:,PAN=(?P<PAN>-?\d+))?"
    r"(?:,TILT=(?P<TILT>-?\d+))?"
    r"(?:,SCORE=(?P<SCORE>-?\d+))?"
    r"(?:,FPS=(?P<FPS>-?\d+))?"
    r"(?:,VALID=(?P<VALID>\d+))?"
    r"(?:,STATUS=(?P<STATUS>[^,#]+))?"
    r"(?:,STATE=(?P<STATE>[^,#]+))?"
    r"#"
)


def parse_dbg_line(line: str) -> dict:
    m = DBG_RE.search(line)
    if not m:
        return None

    parsed = {}
    int_fields = ("EX", "EY", "CX", "CY", "SX", "SY", "PAN", "TILT",
                  "SCORE", "FPS", "VALID")
    str_fields = ("STATUS", "STATE")

    for f in int_fields:
        val = m.group(f)
        if val is not None:
            parsed[f] = int(val)
    for f in str_fields:
        val = m.group(f)
        if val is not None:
            parsed[f] = val
    return parsed


def validate_frame(parsed: dict, test: dict) -> list:
    failures = []
    for field, check in test.get("expect", {}).items():
        if field not in parsed:
            failures.append(f"  MISSING field '{field}' in DBG response")
            continue
        try:
            if not check(parsed[field]):
                failures.append(
                    f"  FIELD '{field}' = {parsed[field]} (expect: {test['expect_desc']})"
                )
        except Exception:
            failures.append(f"  FIELD '{field}' check raised error (value={parsed[field]})")

    for label, check in test.get("extra_checks", []):
        try:
            if not check(parsed):
                failures.append(
                    f"  EXTRA '{label}' check failed (expect: {test['expect_desc']})"
                )
        except Exception:
            failures.append(f"  EXTRA '{label}' check raised error")

    return failures


# ---------------------------------------------------------------------------
# Serial I/O
# ---------------------------------------------------------------------------
def open_serial(port: str, baud: int, timeout: float = 3.0):
    import serial
    ser = serial.Serial(port, baud, timeout=timeout, bytesize=8,
                        parity=serial.PARITY_NONE, stopbits=1)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    return ser


def send_and_read(ser, text: str, timeout: float = 5.0) -> str:
    ser.reset_input_buffer()
    raw = (text + "\r\n").encode("ascii", errors="replace")
    ser.write(raw)

    deadline = time.monotonic() + timeout
    buf = b""
    while time.monotonic() < deadline:
        waiting = ser.in_waiting
        if waiting > 0:
            chunk = ser.read(waiting)
            buf += chunk
            if b"$DBG,AIM" in buf and b"#" in buf:
                break
        else:
            time.sleep(0.05)
    return buf.decode("ascii", errors="replace").strip()


# ---------------------------------------------------------------------------
# DeepSeek API
# ---------------------------------------------------------------------------
def call_deepseek(log_text: str, api_key: str):
    try:
        import json as json_mod
        import urllib.request
    except ImportError:
        return "[DeepSeek] urllib.request not available"

    prompt = (
        "You are an STM32 embedded debug assistant. Below is a serial log from "
        "an STM32F103ZET6 debug bridge that received $MV,AIM test frames over "
        "USART1 and replied with $DBG,AIM telemetry.\n\n"
        "Analyze the log and answer:\n"
        "1. Did all four frames pass? If not, which frame(s) failed?\n"
        "2. What is the most likely root cause of any failure?\n"
        "3. Give one specific next debugging step (code, wiring, or tool).\n\n"
        "Do NOT suggest connecting lasers, PWM outputs, servos, gimbals, "
        "motors, robot arms, or any actuator hardware.\n\n"
        f"--- LOG START ---\n{log_text}\n--- LOG END ---"
    )

    body = json_mod.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are an STM32 embedded debug assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json_mod.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[DeepSeek] API call failed: {e}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not check_pyserial():
        print("pyserial is not installed. Install it with:")
        print("  pip install pyserial")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="STM32 ZET6 debug bridge automated serial check"
    )
    parser.add_argument("--port", required=True, help="COM port (e.g. COM5)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default 115200)")
    parser.add_argument("--deepseek", action="store_true",
                        help="Send log to DeepSeek API for analysis (requires DEEPSEEK_API_KEY env var)")
    args = parser.parse_args()

    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if args.deepseek and not api_key:
        print("[DeepSeek] DEEPSEEK_API_KEY not set. Running local check only.\n")

    import serial

    log_lines = []
    results = []
    overall_pass = True

    log_dir = Path("logs/serial")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "stm32_bridge_auto_check.txt"

    print(f"Opening {args.port} at {args.baud} baud...")
    try:
        ser = open_serial(args.port, args.baud, timeout=3.0)
    except serial.SerialException as e:
        print(f"FAILED to open {args.port}: {e}")
        sys.exit(1)

    try:
        for i, test in enumerate(TEST_FRAMES, 1):
            print(f"\n--- Frame {i}: {test['name']} ---")
            print(f"  SEND: {test['send']}")

            response = send_and_read(ser, test["send"], timeout=5.0)
            log_lines.append(f"FRAME {i} ({test['name']})")
            log_lines.append(f"  SEND: {test['send']}")
            log_lines.append(f"  RECV: {response}")

            print(f"  RECV: {response}")

            parsed = parse_dbg_line(response)
            if parsed is None:
                print(f"  FAIL: Could not parse DBG line from response")
                log_lines.append("  RESULT: FAIL (unparseable)")
                results.append(False)
                overall_pass = False
                continue

            failures = validate_frame(parsed, test)
            if failures:
                print("  FAIL:")
                for f in failures:
                    print(f)
                log_lines.append("  RESULT: FAIL")
                for f in failures:
                    log_lines.append(f)
                results.append(False)
                overall_pass = False
            else:
                print("  PASS")
                log_lines.append("  RESULT: PASS")
                results.append(True)

            time.sleep(0.3)

    finally:
        ser.close()

    # Summary
    print("\n" + "=" * 50)
    summary = "PASS" if overall_pass else "FAIL"
    print(f"OVERALL: {summary}")
    log_lines.insert(0, f"OVERALL: {summary}")

    log_text = "\n".join(log_lines)
    log_path.write_text(log_text, encoding="utf-8")
    print(f"Log saved to: {log_path}")

    if args.deepseek and api_key:
        print("\nCalling DeepSeek API for analysis...")
        analysis = call_deepseek(log_text, api_key)
        print(f"\n--- DeepSeek Analysis ---\n{analysis}\n---")

    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
