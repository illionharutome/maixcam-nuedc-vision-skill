import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from maixcam_app.comm.uart_protocol import encode_vision_result
from maixcam_app.main import apply_camera_profile, load_config, resolve_camera_profile, uart_pin_functions
from maixcam_app.modules.laser_spot import LaserSpotModule
from maixcam_app.modules.e23_track import E23TrackModule
from maixcam_app.modules.rectangle_detect import RectangleDetectModule, order_corners
from maixcam_app.tools.dataset_schema import save_truth, validate_dataset
from maixcam_app.tools.camera_sweep import analyze_frame, summarize_condition
from maixcam_app.tools.collect_dataset import apply_capture_camera_settings
from maixcam_app.tools.parameter_sweep import set_nested
from maixcam_app.tools.replay_test import evaluate_directory
from maixcam_app.tools.session_utils import prepare_session


class VisionTests(unittest.TestCase):
    def test_e23_red_target_tracks_image_center(self):
        config = load_config("maixcam_app/configs/e23_red_center_track.yaml")
        image = np.full((240, 320, 3), 220, dtype=np.uint8)
        cv2.rectangle(image, (65, 35), (255, 205), (10, 10, 10), 10)
        cv2.circle(image, (190, 100), 2, (30, 35, 150), -1)
        result = E23TrackModule(config).process(image)
        self.assertTrue(result["ok"])
        self.assertEqual((result["center_x"], result["center_y"]), (160, 120))
        self.assertEqual((result["dx"], result["dy"]), (30, -20))
        self.assertEqual(result["mode"], "TRACK")

    def test_e23_dual_laser_uses_tracking_spot_as_reference(self):
        config = load_config("maixcam_app/configs/e23_dual_laser_track.yaml")
        image = np.full((240, 320, 3), 220, dtype=np.uint8)
        cv2.rectangle(image, (65, 35), (255, 205), (10, 10, 10), 10)
        cv2.circle(image, (190, 100), 2, (30, 35, 150), -1)
        cv2.circle(image, (170, 110), 2, (150, 45, 70), -1)
        result = E23TrackModule(config).process(image)
        self.assertTrue(result["ok"])
        self.assertEqual((result["center_x"], result["center_y"]), (170, 110))
        self.assertEqual((result["dx"], result["dy"]), (20, -10))

    def test_e23_frame_roi_rejects_larger_red_distractor_outside_frame(self):
        config = load_config("maixcam_app/configs/e23_red_center_track.yaml")
        image = np.full((240, 320, 3), 220, dtype=np.uint8)
        cv2.rectangle(image, (70, 40), (250, 200), (10, 10, 10), 10)
        cv2.circle(image, (190, 100), 2, (30, 35, 150), -1)
        cv2.circle(image, (30, 25), 7, (20, 25, 200), -1)
        result = E23TrackModule(config).process(image)
        self.assertTrue(result["ok"])
        self.assertEqual((result["target_x"], result["target_y"]), (190, 100))
        self.assertEqual(len(result["extra"]["frame_roi_corners"]), 4)

    def test_e23_requires_frame_before_accepting_red_target(self):
        config = load_config("maixcam_app/configs/e23_red_center_track.yaml")
        image = np.full((240, 320, 3), 220, dtype=np.uint8)
        cv2.circle(image, (190, 100), 4, (30, 35, 150), -1)
        result = E23TrackModule(config).process(image)
        self.assertFalse(result["ok"])
        self.assertEqual(result["extra"]["reason"], "frame_missing")
        self.assertEqual((result["dx"], result["dy"]), (0, 0))

    def test_rotated_a4_frame_returns_ordered_corners_and_path(self):
        config = load_config("maixcam_app/configs/e23_a4_black_frame.yaml")
        image = np.full((240, 320, 3), 220, dtype=np.uint8)
        box = cv2.boxPoints(((160, 120), (150, 106), 18)).astype(np.int32)
        cv2.polylines(image, [box], True, (10, 10, 10), 12)
        result = RectangleDetectModule(config).process(image)
        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "LINE")
        self.assertEqual(len(result["extra"]["corners"]), 4)
        self.assertEqual(len(result["extra"]["path"]), 200)
        corners = result["extra"]["corners"]
        self.assertLess(corners[0][0] + corners[0][1], corners[2][0] + corners[2][1])

    def test_corner_order_is_tl_tr_br_bl(self):
        self.assertEqual(order_corners([[90, 80], [10, 20], [80, 10], [20, 90]]),
                         [[10, 20], [80, 10], [90, 80], [20, 90]])

    def test_red_laser_config_detects_red_excess(self):
        image = np.full((240, 320, 3), 30, dtype=np.uint8)
        image[132, 148] = (20, 25, 90)
        module = LaserSpotModule(load_config("maixcam_app/configs/red_laser_wall.yaml"))
        result = module.process(image)
        self.assertTrue(result["ok"])
        self.assertEqual((result["target_x"], result["target_y"]), (148, 132))

    def test_dataset_capture_enters_explicit_manual_mode(self):
        class FakeCameraApi:
            class AeMode:
                Manual = "manual"
                Auto = "auto"

            class AwbMode:
                Manual = "manual_wb"
                Auto = "auto_wb"

        class FakeCamera:
            def __init__(self):
                self.calls = []

            def exp_mode(self, value): self.calls.append(("exp_mode", value))
            def exposure(self, value): self.calls.append(("exposure", value))
            def gain(self, value): self.calls.append(("gain", value))
            def awb_mode(self, value): self.calls.append(("awb_mode", value))
            def set_wb_gain(self, value): self.calls.append(("wb_gain", value))

        cam = FakeCamera()
        apply_capture_camera_settings(cam, FakeCameraApi, 600, 1024, None)
        self.assertEqual(cam.calls, [
            ("exp_mode", "manual"),
            ("exposure", 600),
            ("gain", 1024),
            ("awb_mode", "auto_wb"),
        ])

    def test_maixcam_uses_dedicated_uart1_pinmap(self):
        self.assertEqual(uart_pin_functions("/dev/ttyS1"), [
            ("A19", "UART1_TX"),
            ("A18", "UART1_RX"),
        ])
        self.assertEqual(uart_pin_functions("/dev/ttyS0"), [])

    def test_field_camera_profile_is_manual_and_applied(self):
        config = load_config("maixcam_app/configs/purple_to_blue_wall.yaml")
        profile = resolve_camera_profile(config)
        self.assertEqual((profile["exposure_us"], profile["gain"]), (600, 1024))

        class FakeCameraApi:
            class AeMode:
                Manual = "ae_manual"
                Auto = "ae_auto"

            class AwbMode:
                Auto = "awb_auto"

        class FakeCamera:
            def __init__(self):
                self.calls = []

            def exp_mode(self, value):
                self.calls.append(("exp_mode", value))

            def exposure(self, value):
                self.calls.append(("exposure", value))

            def gain(self, value):
                self.calls.append(("gain", value))

            def awb_mode(self, value):
                self.calls.append(("awb_mode", value))

        cam = FakeCamera()
        apply_camera_profile(cam, FakeCameraApi, profile)
        self.assertEqual(cam.calls, [
            ("exp_mode", "ae_manual"),
            ("exposure", 600),
            ("gain", 1024),
            ("awb_mode", "awb_auto"),
        ])

    def test_protocol_example(self):
        result = {"ok": True, "mode": "AIM", "center_x": 160, "center_y": 120, "target_x": 148,
                  "target_y": 132, "dx": -12, "dy": 12, "confidence": 0.91, "distance": 256, "status": "AIMING"}
        self.assertEqual(encode_vision_result(result), "$MV,AIM,1,160,120,148,132,-12,12,91,256,AIMING#")

    def test_laser_synthetic(self):
        image = np.zeros((240, 320, 3), dtype=np.uint8)
        cv2.circle(image, (148, 132), 4, (255, 80, 160), -1)
        module = LaserSpotModule(load_config("maixcam_app/configs/purple_to_blue_wall.yaml"))
        result = module.process(image)
        self.assertTrue(result["ok"])
        self.assertEqual((result["target_x"], result["target_y"]), (148, 132))
        self.assertEqual((result["dx"], result["dy"]), (-12, 12))

    def test_single_pixel_dim_laser_survives_without_accepting_highlights(self):
        config = load_config("maixcam_app/configs/purple_to_blue_wall.yaml")
        image = np.full((240, 320, 3), 200, dtype=np.uint8)
        cv2.circle(image, (250, 80), 5, (255, 255, 255), -1)
        image[132, 148] = (55, 39, 46)
        result = LaserSpotModule(config).process(image)
        self.assertTrue(result["ok"])
        self.assertEqual((result["target_x"], result["target_y"]), (148, 132))

        highlight_only = np.full((240, 320, 3), 200, dtype=np.uint8)
        cv2.circle(highlight_only, (250, 80), 5, (255, 255, 255), -1)
        highlight_only[132, 148] = (50, 45, 46)
        self.assertFalse(LaserSpotModule(config).process(highlight_only)["ok"])

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
            cv2.circle(positive, (148, 132), 4, (255, 80, 160), -1)
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
