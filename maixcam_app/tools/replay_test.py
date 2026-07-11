"""Replay a detector over saved samples and compute the competition score."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maixcam_app.main import MODULES, load_config


def score_metrics(metrics: dict) -> float:
    return (
        3 * metrics["detect_rate"]
        - 2 * metrics["false_positive_rate"]
        - 0.02 * metrics["mean_center_error_px"]
        - 0.02 * metrics["jitter_px"]
        + 0.03 * metrics["fps"]
        - 0.1 * metrics["lost_frame_count"]
    )


def evaluate_directory(config_path: str, samples_path: str, module_name: str = "laser_spot") -> dict:
    config = load_config(config_path)
    module = MODULES[module_name](config)
    samples = Path(samples_path)
    truth_path = samples / "ground_truth.json"
    truth = json.loads(truth_path.read_text(encoding="utf-8")) if truth_path.exists() else {}
    images = sorted(path for path in samples.iterdir() if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"})
    detections = false_positives = expected = lost = 0
    errors: list[float] = []
    points: list[tuple[int, int]] = []
    started = time.perf_counter()
    for path in images:
        image = cv2.imread(str(path))
        if image is None:
            continue
        result = module.process(image)
        label = truth.get(path.name)
        if label is None:
            present = True
        else:
            present = bool(label.get("present", True))
        expected += int(present)
        detections += int(result["ok"] and present)
        false_positives += int(result["ok"] and not present)
        lost += int(present and not result["ok"])
        if result["ok"]:
            points.append((result["target_x"], result["target_y"]))
            if label and present and "x" in label and "y" in label:
                errors.append(math.hypot(result["target_x"] - label["x"], result["target_y"] - label["y"]))
    elapsed = max(time.perf_counter() - started, 1e-9)
    jitter = 0.0
    if len(points) > 1:
        jitter = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:])) / (len(points) - 1)
    metrics = {
        "sample_count": len(images),
        "detect_rate": detections / expected if expected else 0.0,
        "false_positive_rate": false_positives / max(len(images) - expected, 1),
        "mean_center_error_px": sum(errors) / len(errors) if errors else 0.0,
        "jitter_px": jitter,
        "fps": len(images) / elapsed,
        "lost_frame_count": lost,
    }
    metrics["score"] = score_metrics(metrics)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--samples", required=True)
    parser.add_argument("--module", choices=sorted(MODULES), default="laser_spot")
    parser.add_argument("--output")
    args = parser.parse_args()
    metrics = evaluate_directory(args.config, args.samples, args.module)
    text = json.dumps(metrics, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

