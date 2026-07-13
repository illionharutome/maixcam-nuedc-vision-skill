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
from maixcam_app.modules.e23_track import E23TrackModule
from maixcam_app.modules.laser_spot import LaserSpotModule
from maixcam_app.modules.line_track import LineTrackModule
from maixcam_app.modules.qr_apriltag import QrAprilTagModule
from maixcam_app.modules.rectangle_detect import RectangleDetectModule
from maixcam_app.modules.yolo_detect import YoloDetectModule

MODULES = {
    "circle_detect": CircleDetectModule,
    "e23_track": E23TrackModule,
    "color_blob": ColorBlobModule,
    "laser_spot": LaserSpotModule,
    "line_track": LineTrackModule,
    "qr_apriltag": QrAprilTagModule,
    "rectangle_detect": RectangleDetectModule,
    "yolo_detect": YoloDetectModule,
}


def resolve_camera_profile(config: dict) -> dict:
    raw = config.get("camera", {})
    profile = {
        "width": int(raw.get("width", 320)),
        "height": int(raw.get("height", 240)),
        "exposure_mode": str(raw.get("exposure_mode", "auto")).lower(),
        "exposure_us": int(raw.get("exposure_us", 0)),
        "gain": int(raw.get("gain", 0)),
        "awb_mode": str(raw.get("awb_mode", "auto")).lower(),
        "settle_frames": int(raw.get("settle_frames", 20)),
    }
    if profile["width"] <= 0 or profile["height"] <= 0 or profile["settle_frames"] < 0:
        raise ValueError("camera width/height must be positive and settle_frames cannot be negative")
    if profile["exposure_mode"] not in {"auto", "manual"}:
        raise ValueError("camera exposure_mode must be auto or manual")
    if profile["exposure_mode"] == "manual" and (profile["exposure_us"] <= 0 or profile["gain"] <= 0):
        raise ValueError("manual camera mode requires positive exposure_us and gain")
    if profile["awb_mode"] != "auto":
        raise ValueError("only auto AWB is currently supported by the field entry point")
    return profile


def apply_camera_profile(cam, camera_api, profile: dict) -> None:
    if profile["exposure_mode"] == "manual":
        cam.exp_mode(camera_api.AeMode.Manual)
        cam.exposure(profile["exposure_us"])
        cam.gain(profile["gain"])
    else:
        cam.exp_mode(camera_api.AeMode.Auto)
    cam.awb_mode(camera_api.AwbMode.Auto)


def uart_pin_functions(device: str) -> list[tuple[str, str]]:
    if device == "/dev/ttyS1":
        return [("A19", "UART1_TX"), ("A18", "UART1_RX")]
    return []


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
    parser.add_argument("--uart", default="/dev/ttyS1")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--no-display", action="store_true")
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    from maix import app, camera, display, err, image, pinmap, uart

    config = load_config(args.config)
    module = MODULES[args.module](config)
    camera_profile = resolve_camera_profile(config)
    cam = camera.Camera(camera_profile["width"], camera_profile["height"], image.Format.FMT_BGR888, buff_num=1)
    apply_camera_profile(cam, camera, camera_profile)
    cam.skip_frames(camera_profile["settle_frames"])
    disp = None if args.no_display else display.Display()
    for pin, function in uart_pin_functions(args.uart):
        err.check_raise(pinmap.set_pin_function(pin, function), f"failed to map {pin} to {function}")
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
