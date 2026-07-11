"""Purple target tracking measurement only; no actuator output."""
import json, os
from comm.protocol_track1 import serialize_track1
from comm.uart_send import emit, open_output
from core.result import TrackResult
from vision.aim_calibration import AimCalibration
from vision.overlay import draw_overlay
from vision.purple_target_detect import PurpleDetector

ROOT = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    with open(os.path.join(ROOT, "config", name), "r") as f: return json.loads(f.read())


def main():
    from maix import app, camera, display, image, time, uart
    cfg, aim_cfg = _load("app.yaml"), _load("aim_calibration.yaml")
    detector, aim = PurpleDetector(_load("purple_detect.yaml")), AimCalibration(aim_cfg)
    serial = open_output(uart, _load("uart.yaml"))
    cam = camera.Camera(int(cfg["width"]), int(cfg["height"]), image.Format.FMT_RGB888,
                        fps=float(cfg.get("fps", -1)), buff_num=int(cfg.get("buffer_num", 3)))
    disp = display.Display(); time.fps_start()
    try:
        while not app.need_exit():
            frame = cam.read(); target = detector.detect(frame)
            ex, ey, status = aim.evaluate(target)
            result = TrackResult(target.ok, target.target_cx, target.target_cy, aim.cx, aim.cy,
                                 ex, ey, target.area, target.score, time.fps(), status)
            draw_overlay(frame, result, int(aim_cfg.get("aim_radius_px", 8)), image)
            emit(serial, serialize_track1(result)); disp.show(frame)
    finally:
        if serial is not None: serial.close()


if __name__ == "__main__": main()
