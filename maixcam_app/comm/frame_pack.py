"""Transport helper; formatting remains owned by uart_protocol."""

from .uart_protocol import encode_vision_result


class VisionFrameWriter:
    def __init__(self, serial, debug: bool = False):
        self.serial = serial
        self.debug = debug

    def send(self, result: dict) -> str:
        frame = encode_vision_result(result)
        self.serial.write_str(frame)
        if self.debug:
            print(f"TX {frame}")
        return frame

