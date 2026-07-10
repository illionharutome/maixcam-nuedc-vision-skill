"""First MaixCAM-Pro hardware test: detect a configured light spot and send `$MV`."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from comm.uart_packet import serialize_vision_result
from core.config_loader import load_config
from vision.laser_spot_detect import detect_laser_spot


def _open_uart(uart_module, config):
    device = config.get("device", "auto")
    if device == "auto":
        devices = uart_module.list_devices()
        if not devices:
            return None
        device = devices[0]
    return uart_module.UART(device, int(config.get("baudrate", 115200)))


def _draw_spot(img, result, image_module):
    color = image_module.COLOR_GREEN if result.ok else image_module.COLOR_RED
    if result.ok:
        img.draw_cross(result.spot_cx, result.spot_cy, color, size=8, thickness=2)
    img.draw_string(4, 4, "%s %s" % (result.cls, result.status), color)


def main():
    # Official MaixPy v4 modules; no K230/CanMV APIs are used here.
    from maix import app, camera, display, image, time, uart

    camera_config = load_config("camera.yaml")
    laser_config = load_config("laser_spot.yaml")
    uart_config = load_config("uart.yaml")
    cam = camera.Camera(int(camera_config["width"]), int(camera_config["height"]),
                        image.Format.FMT_RGB888, fps=float(camera_config.get("fps", -1)),
                        buff_num=int(camera_config.get("buffer_num", 3)))
    disp = display.Display()
    serial = _open_uart(uart, uart_config)
    time.fps_start()
    while not app.need_exit():
        frame = cam.read()
        result = detect_laser_spot(frame, laser_config)
        result.fps = time.fps()
        _draw_spot(frame, result, image)
        if serial:
            # This standalone detector never emits AIM: it has no verified target center.
            serial.write_str(serialize_vision_result(result))
        disp.show(frame)
    if serial:
        serial.close()


if __name__ == "__main__":
    main()
