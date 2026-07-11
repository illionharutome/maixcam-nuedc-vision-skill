"""Dominant-line center estimator for OpenCV replay and MaixCAM."""
import cv2
from .base import VisionModule, vision_result


class LineTrackModule(VisionModule):
    name = "line_track"

    def process(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, int(self.config.get("canny_low", 60)), int(self.config.get("canny_high", 160)))
        lines = cv2.HoughLinesP(edges, 1, 3.14159 / 180, int(self.config.get("votes", 30)),
                                minLineLength=int(self.config.get("min_length", 30)), maxLineGap=10)
        h, w = gray.shape
        if lines is None:
            return vision_result(mode="LINE", center_x=w // 2, center_y=h // 2)
        x1, y1, x2, y2 = max((line[0] for line in lines), key=lambda p: (p[2]-p[0])**2 + (p[3]-p[1])**2)
        return vision_result(ok=True, mode="LINE", target_x=(x1+x2)//2, target_y=(y1+y2)//2,
                             center_x=w//2, center_y=h//2, confidence=0.8, status="AIMING",
                             extra={"line": [int(x1), int(y1), int(x2), int(y2)]})

