"""Hough circle detector with unified output."""
import cv2
from .base import VisionModule, vision_result


class CircleDetectModule(VisionModule):
    name = "circle_detect"

    def process(self, img):
        gray = cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 5)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.2, 20, param1=100,
                                   param2=int(self.config.get("threshold", 30)),
                                   minRadius=int(self.config.get("min_radius", 4)), maxRadius=int(self.config.get("max_radius", 100)))
        h, w = gray.shape
        if circles is None:
            return vision_result(center_x=w//2, center_y=h//2)
        x, y, radius = max(circles[0], key=lambda c: c[2])
        return vision_result(ok=True, target_x=round(x), target_y=round(y), center_x=w//2, center_y=h//2,
                             confidence=0.8, status="AIMING", extra={"radius": round(float(radius), 2)})

