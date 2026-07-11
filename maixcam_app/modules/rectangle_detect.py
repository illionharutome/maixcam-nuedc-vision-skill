"""Quadrilateral detector with unified output."""
import cv2
from .base import VisionModule, vision_result


class RectangleDetectModule(VisionModule):
    name = "rectangle_detect"

    def process(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        contours, _ = cv2.findContours(cv2.Canny(gray, 60, 160), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        h, w = gray.shape
        candidates = []
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                area = cv2.contourArea(approx)
                if area >= float(self.config.get("min_area", 200)):
                    candidates.append((area, approx))
        if not candidates:
            return vision_result(center_x=w//2, center_y=h//2)
        area, contour = max(candidates, key=lambda item: item[0])
        moments = cv2.moments(contour)
        x, y = int(moments["m10"]/moments["m00"]), int(moments["m01"]/moments["m00"])
        return vision_result(ok=True, target_x=x, target_y=y, center_x=w//2, center_y=h//2,
                             confidence=0.8, status="AIMING", extra={"area": area})

