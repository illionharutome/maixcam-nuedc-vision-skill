"""Standalone MaixVision single-gimbal visual measurement app.

This module only measures image-space error and emits text telemetry. It does
not drive PWM, a gimbal, a servo, a light source, or any other actuator.
"""

import json
import os

from comm.protocol_single import serialize_single
from comm.uart_send import emit, open_output
from core.result import VisionResult
from vision.a4_tape_rect_detect import estimate_rect_path
from vision.path_overlay import draw_overlay
from vision.screen_calibration import screen_center, square_path
from vision.single_spot_detect import detect_single_spot


ROOT = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    path = os.path.join(ROOT, "config", name)
    with open(path, "r") as handle:
        return json.loads(handle.read())


def _path(path_id, screen):
    if path_id == "SCREEN_SQUARE":
        return square_path(screen)
    if path_id == "A4_RECT":
        return estimate_rect_path(screen.get("a4_corners", []))
    if path_id == "A4_ROTATED_RECT":
        return estimate_rect_path(screen.get("a4_rotated_corners", []))
    return [screen_center(screen)]


def main():
    from maix import app, camera, display, image, time, uart

    runtime = _load("single_gimbal.yaml")
    screen = _load("screen_calibration.yaml")
    spot_config = _load("spot_detect.yaml")
    uart_config = _load("uart.yaml")
    path_id = runtime.get("path_id", "CENTER")
    path = _path(path_id, screen) or [screen_center(screen)]
    serial = open_output(uart, uart_config)
    cam = camera.Camera(int(runtime["camera_width"]), int(runtime["camera_height"]),
                        image.Format.FMT_RGB888, fps=float(runtime.get("camera_fps", -1)),
                        buff_num=int(runtime.get("buffer_num", 3)))
    disp = display.Display()
    frame_index = 0
    time.fps_start()
    try:
        while not app.need_exit():
            frame = cam.read()
            step_frames = max(1, int(runtime.get("path_step_frames", 3)))
            step_id = (frame_index // step_frames) % len(path)
            target_cx, target_cy = path[step_id]
            spot = detect_single_spot(frame, spot_config)
            ex = spot.spot_cx - target_cx if spot.ok else 0
            ey = spot.spot_cy - target_cy if spot.ok else 0
            deadband = int(runtime.get("aimed_deadband_px", 4))
            status = "AIMED" if spot.ok and abs(ex) <= deadband and abs(ey) <= deadband else spot.status
            result = VisionResult(
                ok=spot.ok, spot_cx=spot.spot_cx, spot_cy=spot.spot_cy,
                target_cx=target_cx, target_cy=target_cy, error_x=ex, error_y=ey,
                path_id=path_id, step_id=step_id, score=spot.score,
                fps=time.fps(), status=status,
            )
            draw_overlay(frame, result, path, image)
            emit(serial, serialize_single(result))
            disp.show(frame)
            frame_index += 1
    finally:
        if serial is not None:
            serial.close()


if __name__ == "__main__":
    main()
