import unittest

from scripts.tune import _frames_from_buffer, analyze_rows


class TuneTests(unittest.TestCase):
    def test_fragmented_and_multiple_frames(self):
        frames, rest = _frames_from_buffer("noise$MV,AIM,1,1,2")
        self.assertEqual(frames, [])
        frames, rest = _frames_from_buffer(rest + ",3,4,2,2,1,20,AIMED#$MV,SPOT,0,x,0,0,0,0,0,0,0,0,1,NO_SPOT#")
        self.assertEqual(len(frames), 2)
        self.assertEqual(rest, "")

    def test_statistics(self):
        rows = [
            {"ok": True, "status": "AIMED", "aim_error_x": -2, "aim_error_y": 0, "fps": 20},
            {"ok": False, "status": "NO_SPOT", "aim_error_x": 0, "aim_error_y": 2, "fps": 10},
        ]
        result = analyze_rows(rows)
        self.assertEqual(result["ok_rate"], 0.5)
        self.assertEqual(result["no_spot_rate"], 0.5)
        self.assertEqual(result["aim_error_x_avg"], -1.0)
        self.assertEqual(result["aim_error_y_std"], 1.0)
        self.assertEqual(result["fps_min"], 10.0)


if __name__ == "__main__":
    unittest.main()
