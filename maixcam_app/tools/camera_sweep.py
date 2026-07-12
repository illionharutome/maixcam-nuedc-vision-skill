"""Measure auto camera state and sweep manual exposure/gain on MaixCAM."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maixcam_app.main import MODULES, load_config


def _number_list(text: str) -> list[int]:
    values = [int(item.strip()) for item in text.split(",") if item.strip()]
    if not values or any(value <= 0 for value in values):
        raise argparse.ArgumentTypeError("expected comma-separated positive integers")
    return values


def analyze_frame(frame: np.ndarray, result: dict, roi: list[int] | None = None) -> dict:
    height, width = frame.shape[:2]
    if roi is None:
        x, y, w, h = 0, 0, width, height
    else:
        x, y, w, h = (int(value) for value in roi)
        x, y = max(0, x), max(0, y)
        w, h = max(1, min(w, width - x)), max(1, min(h, height - y))
    gray = cv2.cvtColor(frame[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
    return {
        "brightness_mean": float(gray.mean()),
        "brightness_p05": float(np.percentile(gray, 5)),
        "brightness_p95": float(np.percentile(gray, 95)),
        "underexposed_ratio": float(np.count_nonzero(gray <= 5) / gray.size),
        "overexposed_ratio": float(np.count_nonzero(gray >= 250) / gray.size),
        "detected": bool(result["ok"]),
        "confidence": float(result["confidence"]),
        "area": float(result.get("extra", {}).get("area", 0.0)),
        "circularity": float(result.get("extra", {}).get("circularity", 0.0)),
        "target_x": int(result["target_x"]),
        "target_y": int(result["target_y"]),
    }


def summarize_condition(frames: list[dict], elapsed_s: float, expected: str) -> dict:
    detected = [item for item in frames if item["detected"]]
    points = [(item["target_x"], item["target_y"]) for item in detected]
    jitter_steps = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:])]
    detection_rate = len(detected) / len(frames) if frames else 0.0
    expected_score = detection_rate if expected == "present" else (1.0 - detection_rate if expected == "absent" else 0.5)
    mean_over = statistics.fmean(item["overexposed_ratio"] for item in frames) if frames else 0.0
    mean_under = statistics.fmean(item["underexposed_ratio"] for item in frames) if frames else 0.0
    mean_confidence = statistics.fmean(item["confidence"] for item in detected) if detected else 0.0
    jitter = statistics.fmean(jitter_steps) if jitter_steps else 0.0
    summary = {
        "frame_count": len(frames),
        "detection_rate": detection_rate,
        "confidence_mean": mean_confidence,
        "area_mean": statistics.fmean(item["area"] for item in detected) if detected else 0.0,
        "circularity_mean": statistics.fmean(item["circularity"] for item in detected) if detected else 0.0,
        "target_jitter_px": jitter,
        "brightness_mean": statistics.fmean(item["brightness_mean"] for item in frames) if frames else 0.0,
        "brightness_p05_mean": statistics.fmean(item["brightness_p05"] for item in frames) if frames else 0.0,
        "brightness_p95_mean": statistics.fmean(item["brightness_p95"] for item in frames) if frames else 0.0,
        "underexposed_ratio": mean_under,
        "overexposed_ratio": mean_over,
        "measured_fps": len(frames) / max(elapsed_s, 1e-9),
    }
    summary["diagnostic_score"] = (
        3.0 * expected_score + mean_confidence - 3.0 * mean_over - 1.5 * mean_under - 0.02 * jitter
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto-baseline plus exposure/gain sweep on MaixCAM")
    parser.add_argument("--module", choices=sorted(MODULES), default="laser_spot")
    parser.add_argument("--config", default="maixcam_app/configs/purple_to_blue_wall.yaml")
    parser.add_argument("--session", required=True)
    parser.add_argument("--scene", required=True)
    parser.add_argument("--lighting", default="unknown")
    parser.add_argument("--distance-mm", type=int, default=0)
    parser.add_argument("--expected", choices=("present", "absent", "unknown"), default="present")
    parser.add_argument("--exposures-us", type=_number_list, default=_number_list("250,500,1000,2000,4000,8000"))
    parser.add_argument("--gains", type=_number_list, help="manual gains; default uses auto-baseline gain only")
    parser.add_argument("--frames", type=int, default=30, help="measured frames per condition")
    parser.add_argument("--settle-frames", type=int, default=20)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--no-display", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    from maix import app, camera, display, image

    session = Path("logs/tuning") / args.session
    if session.exists() and any(session.iterdir()):
        raise FileExistsError(f"session already contains data: {session}")
    images_dir = session / "representatives"
    images_dir.mkdir(parents=True, exist_ok=True)
    config = load_config(args.config)
    roi = config.get("roi")
    cam = camera.Camera(args.width, args.height, image.Format.FMT_BGR888, buff_num=1)
    disp = None if args.no_display else display.Display()
    cam.exp_mode(camera.AeMode.Auto)
    cam.awb_mode(camera.AwbMode.Auto)
    cam.skip_frames(max(30, args.settle_frames))
    auto_state = {
        "exposure_us": int(cam.exposure()),
        "gain": int(cam.gain()),
        "iso": int(cam.iso()),
        "wb_gain": [float(value) for value in cam.set_wb_gain()],
        "camera_fps": float(cam.fps()),
    }
    gains = args.gains or [max(1, auto_state["gain"])]
    conditions = [{"name": "auto", "mode": "auto", **auto_state}]
    conditions.extend(
        {"name": f"exp_{exposure}us_gain_{gain}", "mode": "manual", "exposure_us": exposure, "gain": gain}
        for exposure in args.exposures_us for gain in gains
    )
    results = []
    try:
        for condition in conditions:
            if app.need_exit():
                break
            detector = MODULES[args.module](config)
            if condition["mode"] == "auto":
                cam.exp_mode(camera.AeMode.Auto)
            else:
                cam.exp_mode(camera.AeMode.Manual)
                condition["exposure_us"] = int(cam.exposure(int(condition["exposure_us"])))
                condition["gain"] = int(cam.gain(int(condition["gain"])))
            cam.clear_buff()
            cam.skip_frames(max(1, args.settle_frames))
            condition["measured_exposure_us"] = int(cam.exposure())
            condition["measured_gain"] = int(cam.gain())
            measured = []
            representative = None
            started = time.perf_counter()
            for frame_index in range(max(1, args.frames)):
                maix_img = cam.read()
                frame = image.image2cv(maix_img, ensure_bgr=True, copy=True)
                result = detector.process(frame)
                measured.append(analyze_frame(frame, result, roi))
                if frame_index == max(1, args.frames) // 2:
                    representative = frame.copy()
                if disp is not None:
                    debug = detector.draw_debug(frame, result)
                    cv2.putText(debug, condition["name"], (5, args.height - 8), cv2.FONT_HERSHEY_SIMPLEX,
                                0.45, (0, 255, 255), 1, cv2.LINE_AA)
                    disp.show(image.cv2image(debug, bgr=True, copy=False))
            summary = summarize_condition(measured, time.perf_counter() - started, args.expected)
            results.append({**condition, **summary})
            if representative is not None:
                cv2.imwrite(str(images_dir / f"{condition['name']}.png"), representative)
            print(f"{condition['name']}: detect={summary['detection_rate']:.3f} "
                  f"bright={summary['brightness_mean']:.1f} over={summary['overexposed_ratio']:.3f} "
                  f"score={summary['diagnostic_score']:.3f}")
    finally:
        cam.exp_mode(camera.AeMode.Auto)
        cam.awb_mode(camera.AwbMode.Auto)
        cam.close()

    ranked = sorted(results, key=lambda item: item["diagnostic_score"], reverse=True)
    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "module": args.module,
        "config": args.config,
        "scene": args.scene,
        "lighting": args.lighting,
        "distance_mm": max(0, args.distance_mm),
        "expected": args.expected,
        "auto_baseline": auto_state,
        "recommended_diagnostic_condition": ranked[0]["name"] if ranked else None,
        "note": "Diagnostic ranking is not a final parameter score; validate on labeled positive and negative datasets.",
        "conditions": results,
    }
    (session / "camera_sweep.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"report: {session / 'camera_sweep.json'}")


if __name__ == "__main__":
    main()
