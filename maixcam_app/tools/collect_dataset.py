"""Explicit MaixCAM sampling mode with reproducible camera and scene metadata."""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maixcam_app.main import MODULES, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect an explicit visual-optimization session on MaixCAM")
    parser.add_argument("--module", choices=sorted(MODULES), default="laser_spot")
    parser.add_argument("--config", default="maixcam_app/configs/purple_to_blue_wall.yaml")
    parser.add_argument("--session", required=True, help="new name below logs/tuning")
    parser.add_argument("--scene", required=True, help="stable scene label, e.g. indoor_white_wall")
    parser.add_argument("--lighting", default="unknown", help="e.g. bright, dim, backlight")
    parser.add_argument("--distance-mm", type=int, default=0)
    parser.add_argument("--expected", choices=("present", "absent", "mixed", "unknown"), default="unknown")
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--exposure-us", type=int)
    parser.add_argument("--gain", type=int)
    parser.add_argument("--wb-gain", nargs=4, type=float, metavar=("R", "GR", "GB", "B"))
    parser.add_argument("--sample-every", type=int, default=15)
    parser.add_argument("--image-format", choices=("png", "jpg"), default="png")
    parser.add_argument("--save-failures", action="store_true", help="save every missed frame; may use much storage")
    parser.add_argument("--max-frames", type=int, default=0)
    return parser.parse_args()


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def main() -> None:
    args = parse_args()
    import cv2
    from maix import app, camera, image

    session = Path("logs/tuning") / args.session
    if session.exists() and any(session.iterdir()):
        raise FileExistsError(f"session already contains data: {session}")
    samples = session / "samples"
    samples.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.config, session / "current_config.yaml")
    (session / "failure_cases.json").write_text("[]\n", encoding="utf-8")
    metadata = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "module": args.module,
        "config": str(Path(args.config)),
        "scene": args.scene,
        "lighting": args.lighting,
        "distance_mm": max(0, args.distance_mm),
        "expected": args.expected,
        "camera": {
            "width": args.width,
            "height": args.height,
            "exposure_us": args.exposure_us,
            "gain": args.gain,
            "wb_gain": args.wb_gain,
        },
        "sampling": {"every": args.sample_every, "format": args.image_format, "save_failures": args.save_failures},
    }
    (session / "session.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    detector = MODULES[args.module](load_config(args.config))
    cam = camera.Camera(args.width, args.height, image.Format.FMT_BGR888, buff_num=1)
    if args.exposure_us is not None:
        cam.exposure(args.exposure_us)
    if args.gain is not None:
        cam.gain(args.gain)
    if args.wb_gain is not None:
        cam.awb_mode(camera.AwbMode.Manual)
        cam.set_wb_gain(list(args.wb_gain))
    cam.skip_frames(30)

    frame_id = detected = saved = 0
    processing_ms: list[float] = []
    previous_status = None
    started = time.perf_counter()
    log_path = session / "frames.jsonl"
    with log_path.open("w", encoding="utf-8") as log:
        while not app.need_exit() and (args.max_frames <= 0 or frame_id < args.max_frames):
            frame_id += 1
            maix_img = cam.read()
            frame = image.image2cv(maix_img, ensure_bgr=True, copy=True)
            process_started = time.perf_counter()
            result = detector.process(frame)
            duration_ms = (time.perf_counter() - process_started) * 1000.0
            processing_ms.append(duration_ms)
            detected += int(result["ok"])
            elapsed = max(time.perf_counter() - started, 1e-9)
            record = {
                "frame_id": frame_id,
                "timestamp_ms": round(elapsed * 1000.0, 3),
                "processing_ms": round(duration_ms, 3),
                "ok": result["ok"],
                "target_x": result["target_x"], "target_y": result["target_y"],
                "dx": result["dx"], "dy": result["dy"],
                "confidence": result["confidence"],
                "area": result["extra"].get("area", 0),
                "circularity": result["extra"].get("circularity", 0),
                "fps": frame_id / elapsed,
                "status": result["status"],
                "config_name": Path(args.config).stem,
                "scene": args.scene, "lighting": args.lighting,
                "distance_mm": max(0, args.distance_mm), "expected": args.expected,
            }
            log.write(json.dumps(record, ensure_ascii=False) + "\n")
            periodic = frame_id % max(1, args.sample_every) == 0
            transition = previous_status is not None and result["status"] != previous_status
            save = periodic or transition or (args.save_failures and not result["ok"])
            if save:
                filename = f"frame_{frame_id:06d}.{args.image_format}"
                if not cv2.imwrite(str(samples / filename), frame):
                    raise OSError(f"failed to save {filename}")
                saved += 1
            previous_status = result["status"]

    elapsed = max(time.perf_counter() - started, 1e-9)
    metrics = {
        "frame_count": frame_id,
        "sample_count": saved,
        "detect_rate_unlabeled": detected / frame_id if frame_id else 0.0,
        "capture_fps": frame_id / elapsed,
        "processing_ms_mean": statistics.fmean(processing_ms) if processing_ms else 0.0,
        "processing_ms_p95": _percentile(processing_ms, 0.95),
        "note": "Detection rate is provisional until samples/ground_truth.json is manually labeled.",
    }
    (session / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"saved {saved} samples in {session}; label them before replay scoring")


if __name__ == "__main__":
    main()
