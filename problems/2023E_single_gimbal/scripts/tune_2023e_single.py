#!/usr/bin/env python3
"""Analyze local simulation logs and print non-binding parameter suggestions."""

import argparse
import json
import math
import os
from pathlib import Path
from statistics import mean, pstdev


def analyze(rows):
    valid = [r for r in rows if r.get("ok", False)]
    errors = [float(r.get("error", math.hypot(r.get("error_x", 0), r.get("error_y", 0)))) for r in valid]
    fps = [float(r["fps"]) for r in rows if r.get("fps") is not None]
    commands = [max(abs(float(r.get("pan_command", 0))), abs(float(r.get("tilt_command", 0)))) for r in rows]
    limit = max(commands) if commands else 0.0
    lock_time = next((float(r.get("t", 0)) for r in valid if float(r.get("error", 999)) <= 3.0), None)
    tail = errors[-60:]
    return {"lock_time": lock_time, "error_avg": mean(errors) if errors else None,
            "error_max": max(errors) if errors else None, "error_std": pstdev(errors) if len(errors) > 1 else 0.0,
            "overshoot": max(0.0, max(errors[30:], default=0.0) - errors[-1]) if errors else None,
            "jitter": mean(abs(tail[i] - tail[i-1]) for i in range(1, len(tail))) if len(tail) > 1 else 0.0,
            "saturation_rate": mean(1.0 if c >= limit and limit > 0 else 0.0 for c in commands) if commands else 0.0,
            "lost_count": len(rows) - len(valid), "fps_avg": mean(fps) if fps else None,
            "fps_min": min(fps) if fps else None}


def suggestions(summary):
    text = []
    if summary["lock_time"] is None or summary["lock_time"] > 2.0:
        text.append("review kp_x/kp_y and path_speed; convergence is slow")
    if summary["overshoot"] and summary["overshoot"] > 5:
        text.append("consider increasing kd_x/kd_y or reducing kp_x/kp_y")
    if summary["jitter"] > 1:
        text.append("consider deadband_px or smoothing_alpha")
    if summary["saturation_rate"] > 0.1:
        text.append("review command_limit and path_speed")
    return text or ["keep current starting values; collect real safe-dot logs before tuning"]


def deepseek(summary):
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise SystemExit("--deepseek requires DEEPSEEK_API_KEY")
    import urllib.request
    payload = json.dumps({"model": "deepseek-chat", "messages": [
        {"role": "system", "content": "Give cautious parameter suggestions only. Never control hardware or apply configuration."},
        {"role": "user", "content": "Analyze this aggregate summary only: " + json.dumps(summary)}]}).encode()
    request = urllib.request.Request("https://api.deepseek.com/v1/chat/completions", data=payload,
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())["choices"][0]["message"]["content"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path)
    parser.add_argument("--deepseek", action="store_true")
    args = parser.parse_args()
    path = args.file or Path(__file__).resolve().parents[1] / "logs" / "sim_tracking.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    summary = analyze(rows)
    print(json.dumps(summary, indent=2))
    print("suggestions:")
    for item in suggestions(summary): print("-", item)
    if args.deepseek: print("DeepSeek suggestion:\n" + deepseek(summary))
    print("No configuration was changed and no hardware command was sent.")


if __name__ == "__main__":
    main()
