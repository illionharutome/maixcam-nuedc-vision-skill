"""QR code center detector; AprilTag may be added behind the same contract."""
import cv2
from .base import VisionModule, vision_result


class QrAprilTagModule(VisionModule):
    name = "qr_apriltag"

    def __init__(self, config):
        super().__init__(config)
        self.qr = cv2.QRCodeDetector()

    def process(self, img):
        value, corners, _ = self.qr.detectAndDecode(img)
        h, w = img.shape[:2]
        if corners is None:
            return vision_result(center_x=w//2, center_y=h//2)
        points = corners[0]
        x, y = int(points[:,0].mean()), int(points[:,1].mean())
        return vision_result(ok=True, target_x=x, target_y=y, center_x=w//2, center_y=h//2,
                             confidence=1.0 if value else 0.6, status="AIMING", extra={"text": value})

