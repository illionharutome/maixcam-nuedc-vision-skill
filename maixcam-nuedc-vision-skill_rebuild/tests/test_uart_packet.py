import unittest

from comm.uart_packet import parse_mv_packet, serialize_aim_result, serialize_vision_result
from core.result import VisionResult


class PacketTests(unittest.TestCase):
    def test_aim_round_trip(self):
        result = VisionResult(ok=True, mode="AIM", target_cx=160, target_cy=120,
                              spot_cx=148, spot_cy=132, aim_error_x=-12,
                              aim_error_y=12, score=0.91, fps=25.6,
                              status="AIMING")
        packet = serialize_aim_result(result)
        self.assertEqual(packet, "$MV,AIM,1,160,120,148,132,-12,12,0.91,25.6,AIMING#")
        self.assertEqual(parse_mv_packet(packet).aim_error_x, -12)

    def test_spot_is_not_aim(self):
        packet = serialize_vision_result(VisionResult(ok=True, mode="SPOT", cls="red",
            cx=10, cy=20, spot_cx=10, spot_cy=20, status="TRACKING"))
        self.assertEqual(parse_mv_packet(packet).mode, "SPOT")

    def test_wrong_field_count_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_mv_packet("$MV,AIM,1,160,120#")


if __name__ == "__main__":
    unittest.main()
