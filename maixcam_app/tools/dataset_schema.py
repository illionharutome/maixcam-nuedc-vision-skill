"""Shared labeled-sample schema and validation helpers."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import cv2

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


def image_paths(samples: Path) -> list[Path]:
    return sorted(path for path in samples.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)


def load_truth(samples: Path) -> dict[str, dict]:
    path = samples / "ground_truth.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("ground_truth.json root must be an object keyed by image filename")
    return data


def save_truth(samples: Path, truth: dict[str, dict]) -> None:
    path = samples / "ground_truth.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(truth, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def validate_dataset(samples: Path) -> dict:
    images = image_paths(samples)
    truth = load_truth(samples)
    names = {path.name for path in images}
    unlabeled = sorted(names - set(truth))
    orphan_labels = sorted(set(truth) - names)
    invalid: list[str] = []
    scenes: Counter[str] = Counter()
    positives = negatives = 0
    distances: Counter[str] = Counter()
    for path in images:
        label = truth.get(path.name)
        if label is None:
            continue
        if not isinstance(label, dict) or not isinstance(label.get("present"), bool):
            invalid.append(f"{path.name}: present must be boolean")
            continue
        scene = str(label.get("scene", "unassigned"))
        scenes[scene] += 1
        distance = int(label.get("distance_mm", 0) or 0)
        distances["unknown" if distance <= 0 else f"{(distance // 500) * 500}-{(distance // 500 + 1) * 500}mm"] += 1
        if label["present"]:
            positives += 1
            image = cv2.imread(str(path))
            if image is None:
                invalid.append(f"{path.name}: unreadable image")
                continue
            height, width = image.shape[:2]
            x, y = label.get("x"), label.get("y")
            if not isinstance(x, int) or not isinstance(y, int) or not (0 <= x < width and 0 <= y < height):
                invalid.append(f"{path.name}: positive label requires in-range integer x/y")
        else:
            negatives += 1
    return {
        "image_count": len(images),
        "labeled_count": len(images) - len(unlabeled),
        "positive_count": positives,
        "negative_count": negatives,
        "unlabeled": unlabeled,
        "orphan_labels": orphan_labels,
        "invalid": invalid,
        "scenes": dict(sorted(scenes.items())),
        "distance_buckets": dict(sorted(distances.items())),
        "ready_for_scoring": bool(images) and not unlabeled and not orphan_labels and not invalid and positives > 0 and negatives > 0,
    }

