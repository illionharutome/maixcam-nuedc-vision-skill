"""MaixCAM Pro field entry point using current MaixPy v4 APIs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json

from maixcam_app.comm.uart_protocol import encode_vision_result
from maixcam_app.modules.color_blob import ColorBlobModule
from maixcam_app.modules.circle_detect import CircleDetectModule
from maixcam_app.modules.laser_spot import LaserSpotModule
from maixcam_app.modules.line_track import LineTrackModule
from maixcam_app.modules.qr_apriltag import QrAprilTagModule
from maixcam_app.modules.rectangle_detect import RectangleDetectModule
from maixcam_app.modules.yolo_detect import YoloDetectModule

MODULES = {
    "circle_detect": CircleDetectModule,
    "color_blob": ColorBlobModule,
    "laser_spot": LaserSpotModule,
    "line_track": LineTrackModule,
    "qr_apriltag": QrAprilTagModule,
    "rectangle_detect": RectangleDetectModule,
    "yolo_detect": YoloDetectModule,
}


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("non-JSON YAML requires PyYAML; field configs use dependency-free JSON syntax") from exc
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("config root must be a mapping")
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", choices=sorted(MODULES), default="laser_spot")
    parser.add_argument("--config", default="maixcam_app/configs/purple_to_blue_wall.yaml")
    parser.add_argument("--uart", default="/dev/ttyS0")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--no-display", action="store_true")
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    from maix import app, camera, display, image, uart

    config = load_config(args.config)
    module = MODULES[args.module](config)
    cam = camera.Camera(320, 240, image.Format.FMT_BGR888, buff_num=1)
    cam.skip_frames(20)
    disp = None if args.no_display else display.Display()
    serial = uart.UART(args.uart, args.baudrate)
    while not app.need_exit():
        maix_img = cam.read()
        frame = image.image2cv(maix_img, ensure_bgr=True, copy=True)
        result = module.process(frame)
        payload = encode_vision_result(result)
        serial.write_str(payload)
        if args.debug:
            print(payload)
        if disp is not None:
            module.draw_debug(frame, result)
            disp.show(image.cv2image(frame, bgr=True, copy=False))


if __name__ == "__main__":
    run(parse_args())
