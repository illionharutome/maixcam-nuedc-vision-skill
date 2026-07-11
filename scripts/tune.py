"""Record and analyze `$MV,AIM` serial or copied MaixVision logs."""

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from comm.uart_packet import parse_mv_packet


LOG_FIELDS = (
    "timestamp", "ok", "target_cx", "target_cy", "spot_cx", "spot_cy",
    "aim_error_x", "aim_error_y", "score", "fps", "status",
)


def _timestamp():
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def _row_from_result(result):
    return {
        "timestamp": _timestamp(),
        "ok": bool(result.ok),
        "target_cx": result.target_cx,
        "target_cy": result.target_cy,
        "spot_cx": result.spot_cx,
        "spot_cy": result.spot_cy,
        "aim_error_x": result.aim_error_x,
        "aim_error_y": result.aim_error_y,
        "score": result.score,
        "fps": result.fps,
        "status": result.status,
    }


def _frames_from_buffer(buffer):
    frames = []
    while True:
        start = buffer.find("$MV,")
        if start < 0:
            return frames, buffer[-3:]
        if start:
            buffer = buffer[start:]
        end = buffer.find("#", 4)
        if end < 0:
            return frames, buffer
        frames.append(buffer[:end + 1])
        buffer = buffer[end + 1:]


def log_serial(port, baud, seconds, log_dir=None):
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError(
            "pyserial is not installed. Run: python -m pip install pyserial"
        ) from exc

    log_dir = log_dir or os.path.join(ROOT, "logs", "serial")
    os.makedirs(log_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(log_dir, "aim_%s.jsonl" % stamp)

    try:
        stream = serial.Serial(port=port, baudrate=baud, timeout=0.1)
    except Exception as exc:
        raise RuntimeError(
            "Cannot open serial port %s at %d baud: %s\n"
            "Check the COM port, baud rate, TX/RX wiring, and common GND. "
            "MaixVision wireless connection is not a PC COM serial port."
            % (port, baud, exc)
        ) from exc

    deadline = time.monotonic() + seconds
    buffer = ""
    saved = 0
    try:
        with open(path, "a", encoding="utf-8") as handle:
            while time.monotonic() < deadline:
                data = stream.read(max(1, getattr(stream, "in_waiting", 0)))
                if not data:
                    continue
                buffer += data.decode("ascii", errors="ignore")
                frames, buffer = _frames_from_buffer(buffer)
                for frame in frames:
                    try:
                        result = parse_mv_packet(frame)
                    except ValueError:
                        continue
                    if result.mode != "AIM":
                        continue
                    row = _row_from_result(result)
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    handle.flush()
                    saved += 1
    finally:
        stream.close()
    print("saved_frames=%d" % saved)
    print("file=%s" % path)
    return path


def _rate(rows, predicate):
    return sum(1 for row in rows if predicate(row)) / float(len(rows)) if rows else 0.0


def _numbers(rows, key):
    return [float(row.get(key, 0.0) or 0.0) for row in rows]


def _avg(values):
    return statistics.mean(values) if values else 0.0


def _std(values):
    return statistics.pstdev(values) if values else 0.0


def analyze_rows(rows, source_name="<memory>", line_counts=None):
    errors_x = _numbers(rows, "aim_error_x")
    errors_y = _numbers(rows, "aim_error_y")
    fps = _numbers(rows, "fps")
    result = {
        "ok_rate": _rate(rows, lambda row: bool(row.get("ok"))),
        "aimed_rate": _rate(rows, lambda row: row.get("status") == "AIMED"),
        "no_board_rate": _rate(rows, lambda row: row.get("status") == "NO_BOARD"),
        "no_spot_rate": _rate(rows, lambda row: row.get("status") == "NO_SPOT"),
        "aim_error_x_avg": _avg(errors_x),
        "aim_error_y_avg": _avg(errors_y),
        "aim_error_x_std": _std(errors_x),
        "aim_error_y_std": _std(errors_y),
        "fps_avg": _avg(fps),
        "fps_min": min(fps) if fps else 0.0,
    }
    if line_counts:
        result.update(line_counts)
    print("source=%s" % source_name)
    if line_counts:
        print("total_lines=%d" % line_counts["total_lines"])
        print("valid_frames=%d" % line_counts["valid_frames"])
        print("skipped_lines=%d" % line_counts["skipped_lines"])
    else:
        print("frames=%d" % len(rows))
    for key in (
        "ok_rate", "aimed_rate", "no_board_rate", "no_spot_rate",
        "aim_error_x_avg", "aim_error_y_avg", "aim_error_x_std",
        "aim_error_y_std", "fps_avg", "fps_min",
    ):
        print("%s=%.4f" % (key, result[key]))
    return result


def _latest_log(log_dir):
    candidates = [
        os.path.join(log_dir, name) for name in os.listdir(log_dir)
        if name.lower().endswith(".jsonl")
    ] if os.path.isdir(log_dir) else []
    if not candidates:
        raise RuntimeError("No JSONL logs found in %s" % log_dir)
    return max(candidates, key=os.path.getmtime)


def analyze_log(path=None):
    path = path or _latest_log(os.path.join(ROOT, "logs", "serial"))
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except ValueError as exc:
                    raise RuntimeError("Invalid JSON on line %d of %s: %s" % (line_number, path, exc))
                missing = [key for key in LOG_FIELDS if key not in row]
                if missing:
                    raise RuntimeError("Missing fields on line %d: %s" % (line_number, ", ".join(missing)))
                rows.append(row)
    except OSError as exc:
        raise RuntimeError("Cannot read log %s: %s" % (path, exc)) from exc
    return analyze_rows(rows, path)


def analyze_raw_log(path):
    """Analyze AIM frames copied verbatim from the MaixVision console."""
    rows = []
    total_lines = 0
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
            for line in handle:
                total_lines += 1
                text = line.strip()
                start = text.find("$MV,AIM,")
                if start < 0 or not text.endswith("#"):
                    continue
                packet = text[start:]
                try:
                    result = parse_mv_packet(packet)
                except (UnicodeError, ValueError):
                    continue
                if result.mode != "AIM":
                    continue
                rows.append(_row_from_result(result))
    except OSError as exc:
        raise RuntimeError("Cannot read raw MaixVision log %s: %s" % (path, exc)) from exc

    counts = {
        "total_lines": total_lines,
        "valid_frames": len(rows),
        "skipped_lines": total_lines - len(rows),
    }
    return analyze_rows(rows, path, line_counts=counts)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    log_parser = subparsers.add_parser("log", help="record $MV,AIM frames to JSONL")
    log_parser.add_argument("--port", required=True)
    log_parser.add_argument("--baud", type=int, default=115200)
    log_parser.add_argument("--seconds", type=float, default=30.0)
    analyze_parser = subparsers.add_parser("analyze", help="analyze a JSONL log")
    analyze_parser.add_argument("--file", help="JSONL file; defaults to the newest serial log")
    raw_parser = subparsers.add_parser(
        "analyze-raw", help="analyze raw text copied from the MaixVision console"
    )
    raw_parser.add_argument("--file", required=True, help="raw MaixVision console text file")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "log":
            if args.seconds <= 0:
                raise RuntimeError("--seconds must be greater than zero")
            log_serial(args.port, args.baud, args.seconds)
        elif args.command == "analyze":
            analyze_log(args.file)
        else:
            analyze_raw_log(args.file)
    except RuntimeError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
