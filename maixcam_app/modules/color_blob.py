"""Configurable LAB/HSV/brightness blob detector for BGR numpy images."""

from __future__ import annotations

import math

import cv2
import numpy as np

from .base import VisionModule, vision_result
from .tracker import TargetTracker


def _range_mask(image: np.ndarray, space: str, lower: list[int], upper: list[int]) -> np.ndarray:
    if space == "hsv":
        converted = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    elif space == "lab":
        converted = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    elif space == "brightness":
        converted = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif space == "blue_excess":
        blue, green, red = cv2.split(image.astype(np.int16))
        converted = np.clip(blue - np.maximum(green, red), 0, 255).astype(np.uint8)
    else:
        raise ValueError(f"unsupported color space: {space}")
    return cv2.inRange(converted, np.array(lower, dtype=np.uint8), np.array(upper, dtype=np.uint8))


class ColorBlobModule(VisionModule):
    name = "color_blob"

    def __init__(self, config: dict):
        super().__init__(config)
        tracking = config.get("tracking", {})
        self.tracker = TargetTracker(tracking.get("max_jump_px", 80), tracking.get("hold_frames", 3))
        self.last_contour = None

    def _mask(self, roi_img: np.ndarray) -> np.ndarray:
        masks = []
        for rule in self.config.get("thresholds", []):
            if not rule.get("enabled", True):
                continue
            space = str(rule["space"]).lower()
            lower = rule["lower"]
            upper = rule["upper"]
            if space in {"brightness", "blue_excess"}:
                lower, upper = [int(lower)], [int(upper)]
            masks.append(_range_mask(roi_img, space, lower, upper))
        if not masks:
            raise ValueError("at least one threshold rule must be enabled")
        strategy = str(self.config.get("threshold_strategy", "or")).lower()
        mask = masks[0]
        for item in masks[1:]:
            mask = cv2.bitwise_and(mask, item) if strategy == "and" else cv2.bitwise_or(mask, item)
        kernel = max(1, int(self.config.get("morphology", {}).get("kernel", 3)))
        shape = np.ones((kernel, kernel), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, shape)
        return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, shape)

    def process(self, img) -> dict:
        height, width = img.shape[:2]
        x, y, w, h = self.config.get("roi", [0, 0, width, height])
        x, y = max(0, int(x)), max(0, int(y))
        w, h = min(int(w), width - x), min(int(h), height - y)
        mask = self._mask(img[y:y + h, x:x + w])
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        minimum = float(self.config.get("filters", {}).get("min_area", 3))
        maximum = float(self.config.get("filters", {}).get("max_area", 2000))
        min_circularity = float(self.config.get("filters", {}).get("min_circularity", 0.3))
        candidates = []
        for contour in contours:
            contour_area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            bx, by, bw, bh = cv2.boundingRect(contour)
            local_contour = contour - np.array([[[bx, by]]], dtype=contour.dtype)
            component = np.zeros((bh, bw), dtype=np.uint8)
            cv2.drawContours(component, [local_contour], -1, 255, -1)
            area = float(cv2.countNonZero(component))
            if contour_area > 0 and perimeter > 0:
                circularity = 4 * math.pi * contour_area / (perimeter * perimeter)
            else:
                fill_ratio = area / max(1, bw * bh)
                aspect_ratio = min(bw, bh) / max(1, max(bw, bh))
                circularity = fill_ratio * aspect_ratio
            if not minimum <= area <= maximum or circularity < min_circularity:
                continue
            moments = cv2.moments(contour)
            if moments["m00"] == 0:
                pixels_y, pixels_x = np.nonzero(component)
                cx = x + bx + int(round(float(pixels_x.mean())))
                cy = y + by + int(round(float(pixels_y.mean())))
            else:
                cx = x + int(moments["m10"] / moments["m00"])
                cy = y + int(moments["m01"] / moments["m00"])
            score = area * (0.5 + 0.5 * circularity)
            candidates.append({"x": cx, "y": cy, "area": area, "circularity": circularity, "score": score, "contour": contour})
        chosen = self.tracker.choose(candidates)
        center_x, center_y = width // 2, height // 2
        if chosen is not None:
            self.last_contour = chosen["contour"]
            confidence = min(1.0, chosen["circularity"] * min(1.0, chosen["area"] / max(minimum * 4, 1)))
            status = "LOCKED" if abs(chosen["x"] - center_x) <= 3 and abs(chosen["y"] - center_y) <= 3 else "AIMING"
            return vision_result(ok=True, target_x=chosen["x"], target_y=chosen["y"], center_x=center_x, center_y=center_y,
                                 confidence=confidence, status=status,
                                 extra={"area": round(chosen["area"], 2), "circularity": round(chosen["circularity"], 3), "roi": [x, y, w, h]})
        held = self.tracker.held_position()
        if held is not None:
            return vision_result(ok=False, target_x=held[0], target_y=held[1], center_x=center_x, center_y=center_y,
                                 status="LOST", extra={"held": True, "lost_frames": self.tracker.lost_frames})
        return vision_result(center_x=center_x, center_y=center_y, status="NO_TARGET", extra={"lost_frames": self.tracker.lost_frames})

    def draw_debug(self, img, result: dict):
        x, y, w, h = result.get("extra", {}).get("roi", self.config.get("roi", [0, 0, img.shape[1], img.shape[0]]))
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 128, 0), 1)
        if result.get("ok"):
            point = (result["target_x"], result["target_y"])
            cv2.circle(img, point, 8, (0, 255, 0), 2)
            cv2.line(img, (result["center_x"], result["center_y"]), point, (0, 255, 255), 1)
        cv2.putText(img, f"{self.name} {result['status']} c={result['confidence']:.2f}", (5, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)
        return img
