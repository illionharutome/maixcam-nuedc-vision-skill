"""MaixCAM-Pro AIM visualizer. It emits image-space errors only, never motor commands."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from apps_atomic.app_laser_spot_detect import _emit_packet, _open_uart
from comm.uart_packet import serialize_aim_result
from core.config_loader import load_config
from vision.aim_error_calc import AimErrorCalculator
from vision.laser_spot_detect import detect_laser_spot
from vision.target_board_detect import detect_target_board


def main():
    from maix import app, camera, display, image, time, uart

    camera_config = load_config("camera.yaml")
    laser_config = load_config("laser_spot.yaml")
    board_config = load_config("target_board.yaml")
    aiming_config = load_config("aiming.yaml")
    serial = _open_uart(uart, load_config("uart.yaml"))
    cam = camera.Camera(int(camera_config["width"]), int(camera_config["height"]), image.Format.FMT_RGB888,
                        fps=float(camera_config.get("fps", -1)), buff_num=int(camera_config.get("buffer_num", 3)))
    disp, evaluator = display.Display(), AimErrorCalculator(aiming_config)
    time.fps_start()
    while not app.need_exit():
        frame = cam.read()
        board = detect_target_board(frame, board_config)
        spot = detect_laser_spot(frame, laser_config)
        result = evaluator.update(board, spot)
        result.fps = time.fps()
        if board.ok:
            frame.draw_cross(board.target_cx, board.target_cy, image.COLOR_GREEN, size=10, thickness=2)
        if spot.ok:
            frame.draw_cross(spot.spot_cx, spot.spot_cy, image.COLOR_RED, size=7, thickness=2)
        frame.draw_string(4, 4, "%s ex=%d ey=%d" % (result.status, result.aim_error_x, result.aim_error_y), image.COLOR_WHITE)
        _emit_packet(serial, serialize_aim_result(result))
        disp.show(frame)
    if serial:
        serial.close()


# Backward-compatible name used by the 2025E replay wrapper.
run_loop = main


if __name__ == "__main__":
    main()
