"""Reusable 2023-E tracking composition built from existing laser modules.

The color-blob tracking and frame-error pattern follows the MIT-licensed
RaymondMeng/light_trace and NinoC137/Ti_E_AutoServo projects, adapted to the
repository VisionResult interface and MaixPy/OpenCV image representation.
"""

from __future__ import annotations

import cv2
import numpy as np

from .base import VisionModule, vision_result
from .laser_spot import LaserSpotModule
from .rectangle_detect import RectangleDetectModule, inset_corners


class E23TrackModule(VisionModule):
    name = "e23_track"

    def __init__(self, config: dict):
        super().__init__(config)
        self.target_detector = LaserSpotModule(config["target_detector"])
        reference = config.get("reference_detector")
        self.reference_detector = LaserSpotModule(reference) if reference else None
        frame_roi = config.get("frame_roi", {})
        frame_detector = frame_roi.get("detector")
        self.frame_detector = RectangleDetectModule(frame_detector) if frame_detector else None
        self.frame_required = bool(frame_roi.get("required", False))
        self.frame_inset_px = max(0.0, float(frame_roi.get("inset_px", 12)))
        self.frame_hold_frames = max(0, int(frame_roi.get("hold_frames", 3)))
        self.last_frame_corners: list[list[int]] | None = None
        self.frame_lost_frames = 0

    @staticmethod
    def _point(result: dict) -> tuple[int, int]:
        return int(result["target_x"]), int(result["target_y"])

    def _reset_spot_tracking(self) -> None:
        self.target_detector.reset_tracking()
        if self.reference_detector is not None:
            self.reference_detector.reset_tracking()

    def _frame_mask(self, img) -> tuple[np.ndarray | None, dict | None, list[list[int]], bool]:
        if self.frame_detector is None:
            return None, None, [], False
        frame = self.frame_detector.process(img)
        held = False
        if frame["ok"]:
            self.last_frame_corners = frame["extra"]["corners"]
            self.frame_lost_frames = 0
        else:
            self.frame_lost_frames += 1
            held = self.last_frame_corners is not None and self.frame_lost_frames <= self.frame_hold_frames
        corners = self.last_frame_corners if frame["ok"] or held else None
        if corners is None:
            return None, frame, [], False
        roi_corners = inset_corners(corners, self.frame_inset_px)
        mask = np.zeros(img.shape[:2], dtype=np.uint8)
        cv2.fillConvexPoly(mask, np.asarray(roi_corners, dtype=np.int32), 255)
        return mask, frame, roi_corners, held

    def process(self, img) -> dict:
        height, width = img.shape[:2]
        frame_mask, frame, frame_roi_corners, frame_held = self._frame_mask(img)
        if self.frame_required and frame_mask is None:
            self._reset_spot_tracking()
            status = "LOST" if self.last_frame_corners is not None else "NO_TARGET"
            return vision_result(mode="TRACK", center_x=width // 2, center_y=height // 2,
                                 status=status, extra={"target": None, "reference": None,
                                                       "frame": frame, "frame_roi_corners": [],
                                                       "reason": "frame_missing", "area": 0,
                                                       "circularity": 0})
        target = self.target_detector.process(img, roi_mask=frame_mask)
        reference_mode = str(self.config.get("reference_mode", "image_center")).lower()
        reference = (self.reference_detector.process(img, roi_mask=frame_mask)
                     if self.reference_detector is not None else None)
        if not target["ok"]:
            status = "LOST" if target.get("status") == "LOST" else "NO_TARGET"
            return vision_result(mode="TRACK", center_x=width // 2, center_y=height // 2,
                                 status=status, extra={"target": target, "reference": reference,
                                                       "frame": frame,
                                                       "frame_roi_corners": frame_roi_corners,
                                                       "frame_roi_held": frame_held,
                                                       "area": 0, "circularity": 0})
        if reference_mode == "tracking_laser":
            if reference is None or not reference["ok"]:
                return vision_result(mode="TRACK", center_x=width // 2, center_y=height // 2,
                                     status="LOST", extra={"target": target, "reference": reference,
                                                            "frame": frame,
                                                            "frame_roi_corners": frame_roi_corners,
                                                            "frame_roi_held": frame_held,
                                                            "reason": "tracking_laser_missing",
                                                            "area": target["extra"].get("area", 0),
                                                            "circularity": target["extra"].get("circularity", 0)})
            center_x, center_y = self._point(reference)
            confidence = min(float(target["confidence"]), float(reference["confidence"]))
        elif reference_mode == "image_center":
            center_x, center_y = width // 2, height // 2
            confidence = float(target["confidence"])
        else:
            raise ValueError(f"unsupported E23 reference_mode: {reference_mode}")
        target_x, target_y = self._point(target)
        deadband = max(0, int(self.config.get("lock_deadband_px", 8)))
        locked = abs(target_x - center_x) <= deadband and abs(target_y - center_y) <= deadband
        return vision_result(ok=True, mode="TRACK", target_x=target_x, target_y=target_y,
                             center_x=center_x, center_y=center_y, confidence=confidence,
                             status="LOCKED" if locked else "AIMING",
                             extra={"target": target, "reference": reference,
                                    "frame": frame, "frame_roi_corners": frame_roi_corners,
                                    "frame_roi_held": frame_held,
                                    "reference_mode": reference_mode, "lock_deadband_px": deadband,
                                    "area": target["extra"].get("area", 0),
                                    "circularity": target["extra"].get("circularity", 0)})

    def draw_debug(self, img, result):
        extra = result.get("extra", {})
        target = extra.get("target") or {}
        reference = extra.get("reference") or {}
        frame = extra.get("frame") or {}
        frame_corners = frame.get("extra", {}).get("corners", [])
        roi_corners = extra.get("frame_roi_corners", [])
        if len(frame_corners) == 4:
            cv2.polylines(img, [np.asarray(frame_corners, dtype=np.int32)], True, (0, 255, 0), 2)
        if len(roi_corners) == 4:
            color = (0, 165, 255) if extra.get("frame_roi_held") else (255, 255, 0)
            cv2.polylines(img, [np.asarray(roi_corners, dtype=np.int32)], True, color, 1)
        if target.get("ok"):
            cv2.circle(img, self._point(target), 7, (0, 0, 255), 2)
        reference_point = (int(result["center_x"]), int(result["center_y"]))
        if reference.get("ok"):
            cv2.circle(img, self._point(reference), 7, (255, 128, 0), 2)
        else:
            cv2.drawMarker(img, reference_point, (255, 255, 0), cv2.MARKER_CROSS, 14, 1)
        if result.get("ok"):
            cv2.line(img, reference_point, (int(result["target_x"]), int(result["target_y"])), (0, 255, 255), 1)
        cv2.putText(img, f"E23 {result['status']} dx={result['dx']} dy={result['dy']}", (5, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)
        return img
