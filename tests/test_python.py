import json
import unittest

import cv2
import numpy as np

from maixcam_app.comm.uart_protocol import encode_vision_result
from maixcam_app.main import load_config
from maixcam_app.modules.laser_spot import LaserSpotModule


class VisionTests(unittest.TestCase):
    def test_protocol_example(self):
        result = {"ok": True, "mode": "AIM", "center_x": 160, "center_y": 120, "target_x": 148,
                  "target_y": 132, "dx": -12, "dy": 12, "confidence": 0.91, "distance": 256, "status": "AIMING"}
        self.assertEqual(encode_vision_result(result), "$MV,AIM,1,160,120,148,132,-12,12,91,256,AIMING#")

    def test_laser_synthetic(self):
        image = np.zeros((240, 320, 3), dtype=np.uint8)
        cv2.circle(image, (148, 132), 4, (255, 150, 255), -1)
        module = LaserSpotModule(load_config("maixcam_app/configs/purple_to_blue_wall.yaml"))
        result = module.process(image)
        self.assertTrue(result["ok"])
        self.assertEqual((result["target_x"], result["target_y"]), (148, 132))
        self.assertEqual((result["dx"], result["dy"]), (-12, 12))

    def test_default_yaml_is_dependency_free_json(self):
        with open("maixcam_app/configs/default.yaml", encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["camera"]["width"], 320)


if __name__ == "__main__":
    unittest.main()
