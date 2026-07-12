import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from maixcam_app.comm.uart_protocol import encode_vision_result
from maixcam_app.main import load_config
from maixcam_app.modules.laser_spot import LaserSpotModule
from maixcam_app.tools.dataset_schema import save_truth, validate_dataset
from maixcam_app.tools.camera_sweep import analyze_frame, summarize_condition
from maixcam_app.tools.parameter_sweep import set_nested
from maixcam_app.tools.replay_test import evaluate_directory
from maixcam_app.tools.session_utils import prepare_session


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

    def test_nested_sweep_path_supports_list_indices(self):
        config = {"thresholds": [{"lower": [1, 2, 3]}]}
        set_nested(config, "thresholds.0.lower.1", 9)
        self.assertEqual(config["thresholds"][0]["lower"], [1, 9, 3])

    def test_labeled_dataset_and_scene_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            samples = Path(temporary)
            positive = np.zeros((240, 320, 3), dtype=np.uint8)
            cv2.circle(positive, (148, 132), 4, (255, 150, 255), -1)
            cv2.imwrite(str(samples / "positive.png"), positive)
            cv2.imwrite(str(samples / "negative.png"), np.zeros_like(positive))
            save_truth(samples, {
                "positive.png": {"present": True, "x": 148, "y": 132, "scene": "indoor", "sequence": "a"},
                "negative.png": {"present": False, "scene": "indoor", "sequence": "a"},
            })
            report = validate_dataset(samples)
            self.assertTrue(report["ready_for_scoring"])
            metrics = evaluate_directory("maixcam_app/configs/purple_to_blue_wall.yaml", str(samples))
            self.assertEqual(metrics["detect_rate"], 1.0)
            self.assertEqual(metrics["false_positive_rate"], 0.0)
            self.assertIn("indoor", metrics["by_scene"])

    def test_unlabeled_dataset_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            cv2.imwrite(str(Path(temporary) / "unlabeled.png"), np.zeros((20, 20, 3), dtype=np.uint8))
            with self.assertRaisesRegex(ValueError, "not ready"):
                evaluate_directory("maixcam_app/configs/purple_to_blue_wall.yaml", temporary)

    def test_camera_sweep_frame_statistics(self):
        frame = np.full((20, 30, 3), 255, dtype=np.uint8)
        result = {"ok": True, "confidence": 0.8, "target_x": 10, "target_y": 12,
                  "extra": {"area": 8, "circularity": 0.9}}
        analyzed = analyze_frame(frame, result)
        self.assertEqual(analyzed["brightness_mean"], 255.0)
        self.assertEqual(analyzed["overexposed_ratio"], 1.0)
        summary = summarize_condition([analyzed, analyzed], 0.1, "present")
        self.assertEqual(summary["detection_rate"], 1.0)
        self.assertEqual(summary["target_jitter_px"], 0.0)

    def test_session_auto_suffix_and_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "logs" / "tuning"
            first = prepare_session(root, "laser_run")
            (first / "result.json").write_text("{}", encoding="utf-8")
            second = prepare_session(root, "laser_run")
            self.assertEqual(second.name, "laser_run_002")
            (second / "result.json").write_text("{}", encoding="utf-8")
            overwritten = prepare_session(root, "laser_run", overwrite=True)
            self.assertEqual(overwritten, first)
            self.assertEqual(list(overwritten.iterdir()), [])

    def test_session_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                prepare_session(Path(temporary), "../outside", overwrite=True)


if __name__ == "__main__":
    unittest.main()
