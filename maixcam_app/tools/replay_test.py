"""Strict labeled replay evaluation with global and per-scene metrics."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maixcam_app.main import MODULES, load_config
from maixcam_app.tools.dataset_schema import image_paths, load_truth, validate_dataset


def score_metrics(metrics: dict) -> float:
    return (
        3 * metrics["detect_rate"]
        - 2 * metrics["false_positive_rate"]
        - 0.02 * metrics["mean_center_error_px"]
        - 0.02 * metrics["jitter_px"]
        + 0.03 * metrics["fps"]
        - 0.1 * metrics["lost_frame_count"]
    )


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def _summarize(records: list[dict], scoring_fps: float) -> dict:
    positives = [record for record in records if record["label"]["present"]]
    negatives = [record for record in records if not record["label"]["present"]]
    true_positives = [record for record in positives if record["result"]["ok"]]
    false_positives = [record for record in negatives if record["result"]["ok"]]
    center_errors: list[float] = []
    residuals: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for record in true_positives:
        label, result = record["label"], record["result"]
        if "x" not in label or "y" not in label:
            continue
        rx = result["target_x"] - label["x"]
        ry = result["target_y"] - label["y"]
        center_errors.append(math.hypot(rx, ry))
        residuals[str(label.get("sequence", label.get("scene", "default")))].append((rx, ry))
    jitter_steps = [
        math.hypot(current[0] - previous[0], current[1] - previous[1])
        for sequence in residuals.values()
        for previous, current in zip(sequence, sequence[1:])
    ]
    durations = [record["processing_ms"] for record in records]
    total_processing_s = max(sum(durations) / 1000.0, 1e-9)
    metrics = {
        "sample_count": len(records),
        "positive_count": len(positives),
        "negative_count": len(negatives),
        "true_positive_count": len(true_positives),
        "false_positive_count": len(false_positives),
        "detect_rate": len(true_positives) / len(positives) if positives else 0.0,
        "false_positive_rate": len(false_positives) / len(negatives) if negatives else 0.0,
        "mean_center_error_px": statistics.fmean(center_errors) if center_errors else 0.0,
        "p95_center_error_px": _percentile(center_errors, 0.95),
        "jitter_px": statistics.fmean(jitter_steps) if jitter_steps else 0.0,
        "fps": max(0.0, float(scoring_fps)),
        "host_processing_fps": len(records) / total_processing_s,
        "processing_ms_mean": statistics.fmean(durations) if durations else 0.0,
        "processing_ms_p95": _percentile(durations, 0.95),
        "lost_frame_count": len(positives) - len(true_positives),
        "false_positive_files": [record["filename"] for record in false_positives],
        "lost_files": [record["filename"] for record in positives if not record["result"]["ok"]],
    }
    metrics["score"] = score_metrics(metrics)
    return metrics


def evaluate_directory(
    config_path: str,
    samples_path: str,
    module_name: str = "laser_spot",
    *,
    require_labels: bool = True,
    scoring_fps: float = 0.0,
) -> dict:
    config = load_config(config_path)
    samples = Path(samples_path)
    paths = image_paths(samples)
    truth = load_truth(samples)
    report = validate_dataset(samples)
    if require_labels and not report["ready_for_scoring"]:
        details = []
        if report["unlabeled"]:
            details.append(f"{len(report['unlabeled'])} unlabeled")
        if report["invalid"]:
            details.append(f"{len(report['invalid'])} invalid")
        if not report["positive_count"] or not report["negative_count"]:
            details.append("both positive and negative samples are required")
        raise ValueError("dataset is not ready for scoring: " + ", ".join(details))

    groups: dict[str, list[Path]] = defaultdict(list)
    for path in paths:
        label = truth.get(path.name)
        if label is None:
            continue
        groups[str(label.get("sequence", label.get("scene", "default")))].append(path)
    records: list[dict] = []
    for sequence_paths in groups.values():
        module = MODULES[module_name](config)
        for path in sequence_paths:
            frame = cv2.imread(str(path))
            if frame is None:
                continue
            started = time.perf_counter()
            result = module.process(frame)
            duration_ms = (time.perf_counter() - started) * 1000.0
            records.append({"filename": path.name, "label": truth[path.name], "result": result, "processing_ms": duration_ms})
    if not records:
        raise ValueError("no labeled readable images to evaluate")
    metrics = _summarize(records, scoring_fps)
    scenes: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        scenes[str(record["label"].get("scene", "unassigned"))].append(record)
    metrics["by_scene"] = {scene: _summarize(items, scoring_fps) for scene, items in sorted(scenes.items())}
    metrics["dataset"] = report
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--samples", required=True)
    parser.add_argument("--module", choices=sorted(MODULES), default="laser_spot")
    parser.add_argument("--allow-incomplete-labels", action="store_true")
    parser.add_argument("--scoring-fps", type=float, default=0.0,
                        help="MaixCAM-measured FPS used by the score; host replay FPS is diagnostic only")
    parser.add_argument("--output")
    args = parser.parse_args()
    metrics = evaluate_directory(args.config, args.samples, args.module,
                                 require_labels=not args.allow_incomplete_labels, scoring_fps=args.scoring_fps)
    text = json.dumps(metrics, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
