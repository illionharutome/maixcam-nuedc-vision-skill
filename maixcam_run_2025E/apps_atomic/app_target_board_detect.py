"""MaixCAM-Pro target-center bring-up app; default mode is camera image center."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config_loader import load_config
from vision.target_board_detect import detect_target_board


def main():
    from maix import app, camera, display, image

    camera_config = load_config("camera.yaml")
    board_config = load_config("target_board.yaml")
    cam = camera.Camera(int(camera_config["width"]), int(camera_config["height"]), image.Format.FMT_RGB888,
                        fps=float(camera_config.get("fps", -1)), buff_num=int(camera_config.get("buffer_num", 3)))
    disp = display.Display()
    while not app.need_exit():
        frame = cam.read()
        result = detect_target_board(frame, board_config)
        color = image.COLOR_GREEN if result.ok else image.COLOR_RED
        if result.ok:
            frame.draw_cross(result.target_cx, result.target_cy, color, size=10, thickness=2)
        frame.draw_string(4, 4, "%s %s" % (result.cls, result.status), color)
        disp.show(frame)


if __name__ == "__main__":
    main()

