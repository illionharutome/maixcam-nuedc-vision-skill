"""Configurable dark rectangular-frame detector with unified output.

The detect-once/order-corners/interpolate-edges flow is adapted for OpenCV
from the MIT-licensed OpenMV implementation in NinoC137/Ti_E_AutoServo.
"""

from __future__ import annotations

import cv2
import numpy as np

from .base import VisionModule, vision_result


def order_corners(points) -> list[list[int]]:
    pts = np.asarray(points, dtype=np.float32).reshape(4, 2)
    center = pts.mean(axis=0)
    angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
    ordered = pts[np.argsort(angles)]
    start = int(np.argmin(ordered.sum(axis=1) + ordered[:, 0] * 1e-3))
    ordered = np.roll(ordered, -start, axis=0)
    return np.rint(ordered).astype(int).tolist()


def inset_corners(corners: list[list[int]], inset_px: float) -> list[list[int]]:
    pts = np.asarray(corners, dtype=np.float32)
    center = pts.mean(axis=0)
    vectors = center - pts
    lengths = np.linalg.norm(vectors, axis=1, keepdims=True)
    safe = np.maximum(lengths, 1.0)
    return np.rint(pts + vectors / safe * float(inset_px)).astype(int).tolist()


def interpolate_perimeter(corners: list[list[int]], points_per_edge: int) -> list[list[int]]:
    pts = np.asarray(corners, dtype=np.float32)
    count = max(2, int(points_per_edge))
    path = []
    for index in range(4):
        start = pts[index]
        end = pts[(index + 1) % 4]
        for step in range(count):
            point = start + (end - start) * (step / count)
            path.append([int(round(point[0])), int(round(point[1]))])
    return path


class RectangleDetectModule(VisionModule):
    name = "rectangle_detect"

    def process(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur_size = max(1, int(self.config.get("blur_size", 5)))
        if blur_size % 2 == 0:
            blur_size += 1
        blurred = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
        threshold = int(self.config.get("dark_threshold", 0))
        if threshold > 0:
            _, mask = cv2.threshold(blurred, threshold, 255, cv2.THRESH_BINARY_INV)
        else:
            _, mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel_size = max(1, int(self.config.get("morphology_kernel", 3)))
        kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        h, w = gray.shape
        frame_area = float(w * h)
        candidates = []
        for contour in contours:
            area = float(cv2.contourArea(contour))
            area_ratio = area / max(frame_area, 1.0)
            if not float(self.config.get("min_area_ratio", 0.03)) <= area_ratio <= float(
                    self.config.get("max_area_ratio", 0.85)):
                continue
            x, y, bw, bh = cv2.boundingRect(contour)
            border_margin = int(self.config.get("border_margin_px", 2))
            if self.config.get("reject_border_touching", True) and (
                    x <= border_margin or y <= border_margin or
                    x + bw >= w - border_margin or y + bh >= h - border_margin):
                continue
            rect = cv2.minAreaRect(contour)
            rw, rh = rect[1]
            if min(rw, rh) <= 1.0:
                continue
            aspect = max(rw, rh) / min(rw, rh)
            if not float(self.config.get("min_aspect_ratio", 1.1)) <= aspect <= float(
                    self.config.get("max_aspect_ratio", 1.8)):
                continue
            rectangularity = area / max(rw * rh, 1.0)
            if rectangularity < float(self.config.get("min_rectangularity", 0.65)):
                continue
            approx = cv2.approxPolyDP(contour, float(self.config.get("epsilon_ratio", 0.02)) *
                                      cv2.arcLength(contour, True), True)
            points = approx.reshape(-1, 2) if len(approx) == 4 and cv2.isContourConvex(approx) else cv2.boxPoints(rect)
            aspect_target = float(self.config.get("aspect_ratio_target", 1.414))
            aspect_score = max(0.0, 1.0 - abs(aspect - aspect_target) / max(aspect_target, 1e-6))
            score = area_ratio * rectangularity * (0.5 + 0.5 * aspect_score)
            candidates.append((score, area, rectangularity, aspect, points))
        if not candidates:
            return vision_result(mode="LINE", center_x=w // 2, center_y=h // 2)
        score, area, rectangularity, aspect, points = max(candidates, key=lambda item: item[0])
        corners = order_corners(points)
        path_corners = inset_corners(corners, float(self.config.get("path_inset_px", 4)))
        path = interpolate_perimeter(path_corners, int(self.config.get("points_per_edge", 50)))
        center = np.rint(np.asarray(corners, dtype=np.float32).mean(axis=0)).astype(int)
        confidence = min(1.0, rectangularity * (0.5 + min(score * 8.0, 0.5)))
        return vision_result(ok=True, mode="LINE", target_x=int(center[0]), target_y=int(center[1]),
                             center_x=w // 2, center_y=h // 2, confidence=confidence, status="LOCKED",
                             extra={"area": round(area, 2), "aspect_ratio": round(aspect, 3),
                                    "rectangularity": round(rectangularity, 3), "corners": corners,
                                    "path_corners": path_corners, "path": path})

    def draw_debug(self, img, result):
        corners = result.get("extra", {}).get("corners", [])
        path_corners = result.get("extra", {}).get("path_corners", [])
        if len(corners) == 4:
            cv2.polylines(img, [np.asarray(corners, dtype=np.int32)], True, (0, 255, 0), 2)
        if len(path_corners) == 4:
            cv2.polylines(img, [np.asarray(path_corners, dtype=np.int32)], True, (0, 255, 255), 1)
            for index, point in enumerate(path_corners):
                cv2.circle(img, tuple(point), 3, (255, 0, 255), -1)
                cv2.putText(img, str(index), tuple(point), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 0, 255), 1)
        cv2.putText(img, f"rectangle {result['status']} c={result['confidence']:.2f}", (5, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)
        return img
