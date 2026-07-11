"""Explicit sampling mode for structured MaixVision-friendly logs."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from maixcam_app.main import MODULES, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", choices=sorted(MODULES), default="laser_spot")
    parser.add_argument("--config", default="maixcam_app/configs/purple_to_blue_wall.yaml")
    parser.add_argument("--session", required=True)
    parser.add_argument("--sample-every", type=int, default=30)
    parser.add_argument("--max-frames", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    from maix import app, camera, image

    args = parse_args()
    session = Path("logs/tuning") / args.session
    samples = session / "samples"
    samples.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.config, session / "current_config.yaml")
    (session / "failure_cases.json").write_text("[]\n", encoding="utf-8")
    config = load_config(args.config)
    detector = MODULES[args.module](config)
    cam = camera.Camera(320, 240, image.Format.FMT_BGR888, buff_num=1)
    cam.skip_frames(20)
    frame_id = detected = 0
    started = time.perf_counter()
    with (session / "frames.jsonl").open("w", encoding="utf-8") as log:
        while not app.need_exit() and (args.max_frames <= 0 or frame_id < args.max_frames):
            frame_id += 1
            maix_img = cam.read()
            frame = image.image2cv(maix_img, ensure_bgr=True, copy=True)
            result = detector.process(frame)
            detected += int(result["ok"])
            elapsed = max(time.perf_counter() - started, 1e-9)
            record = {
                "frame_id": frame_id, "ok": result["ok"], "target_x": result["target_x"],
                "target_y": result["target_y"], "dx": result["dx"], "dy": result["dy"],
                "confidence": result["confidence"], "area": result["extra"].get("area", 0),
                "fps": frame_id / elapsed, "status": result["status"], "config_name": Path(args.config).stem,
            }
            log.write(json.dumps(record, ensure_ascii=False) + "\n")
            if frame_id % max(1, args.sample_every) == 0 or not result["ok"]:
                cv2_path = samples / f"frame_{frame_id:06d}.jpg"
                import cv2
                cv2.imwrite(str(cv2_path), frame)
    elapsed = max(time.perf_counter() - started, 1e-9)
    metrics = {"frame_count": frame_id, "detect_rate": detected / frame_id if frame_id else 0.0, "fps": frame_id / elapsed}
    (session / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

