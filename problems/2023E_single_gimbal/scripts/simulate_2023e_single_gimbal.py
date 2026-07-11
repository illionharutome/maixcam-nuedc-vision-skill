#!/usr/bin/env python3
"""Pure PC simulation. No camera, serial port, PWM, or actuator access."""

import argparse
import json
import math
from pathlib import Path
from statistics import mean


def rectangle(cx, cy, width, height, rotation_deg=0, edge_points=30):
    points = [(-width / 2, -height / 2), (width / 2, -height / 2),
              (width / 2, height / 2), (-width / 2, height / 2)]
    angle = math.radians(rotation_deg)
    rotated = [(cx + x * math.cos(angle) - y * math.sin(angle),
                cy + x * math.sin(angle) + y * math.cos(angle)) for x, y in points]
    path = []
    for index, start in enumerate(rotated):
        end = rotated[(index + 1) % 4]
        for step in range(edge_points):
            t = step / edge_points
            path.append((start[0] + (end[0] - start[0]) * t,
                         start[1] + (end[1] - start[1]) * t))
    return path


def paths():
    return {
        "CENTER": [(160.0, 120.0)] * 120,
        "SCREEN_SQUARE": rectangle(160, 120, 260, 180),
        "A4_RECT": rectangle(160, 120, 140, 100),
        "A4_ROTATED_RECT": rectangle(160, 120, 140, 100, 22),
    }


def simulate(path_id, target_path, kp=0.18, kd=0.05, limit=20.0, deadband=2.0):
    spot_x, spot_y = 130.0, 95.0
    previous_ex = previous_ey = 0.0
    records = []
    for step in range(360):
        target_x, target_y = target_path[step % len(target_path)]
        ex, ey = spot_x - target_x, spot_y - target_y
        pan = 0.0 if abs(ex) <= deadband else max(-limit, min(limit, kp * ex + kd * (ex - previous_ex)))
        tilt = 0.0 if abs(ey) <= deadband else max(-limit, min(limit, kp * ey + kd * (ey - previous_ey)))
        # Plant sign is negative: positive command reduces positive image error.
        spot_x -= pan * 0.65
        spot_y -= tilt * 0.65
        error = math.hypot(ex, ey)
        records.append({"t": step / 30.0, "path_id": path_id, "target_cx": target_x,
                        "target_cy": target_y, "spot_cx": spot_x, "spot_cy": spot_y,
                        "error_x": ex, "error_y": ey, "error": error,
                        "pan_command": pan, "tilt_command": tilt, "ok": True,
                        "status": "AIMED" if error <= deadband else "TRACKING", "fps": 30.0})
        previous_ex, previous_ey = ex, ey
    return records


def metrics(records, limit=20.0):
    errors = [r["error"] for r in records]
    lock = next((r["t"] for r in records if r["error"] <= 3.0), None)
    tail = records[-60:]
    return {
        "tracking_error_avg": mean(errors), "tracking_error_max": max(errors),
        "lock_time": lock, "overshoot": max(0.0, max(errors[30:]) - errors[-1]),
        "jitter": mean(abs(tail[i]["error"] - tail[i - 1]["error"]) for i in range(1, len(tail))),
        "saturation_rate": mean(1.0 if abs(r["pan_command"]) >= limit or abs(r["tilt_command"]) >= limit else 0.0 for r in records),
        "lost_count": sum(1 for r in records if not r["ok"]),
    }


def plot(records, output):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipped plot")
        return
    fig, axes = plt.subplots(3, 1, figsize=(9, 10))
    axes[0].plot([r["t"] for r in records], [r["error_x"] for r in records], label="error_x")
    axes[0].plot([r["t"] for r in records], [r["error_y"] for r in records], label="error_y")
    axes[0].legend()
    axes[1].plot([r["target_cx"] for r in records], [r["target_cy"] for r in records], label="target")
    axes[1].plot([r["spot_cx"] for r in records], [r["spot_cy"] for r in records], label="spot")
    axes[1].invert_yaxis(); axes[1].axis("equal"); axes[1].legend()
    axes[2].plot([r["t"] for r in records], [r["pan_command"] for r in records], label="pan")
    axes[2].plot([r["t"] for r in records], [r["tilt_command"] for r in records], label="tilt")
    axes[2].legend(); fig.tight_layout(); fig.savefig(output); plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", choices=list(paths()), default="SCREEN_SQUARE")
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / "logs" / "sim_tracking.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    records = simulate(args.path, paths()[args.path])
    output.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    print(json.dumps(metrics(records), indent=2))
    print("log:", output)
    if not args.no_plot:
        plot(records, output.with_suffix(".png"))


if __name__ == "__main__":
    main()
