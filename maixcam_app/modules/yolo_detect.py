"""MaixPy YOLO adapter that emits the shared VisionResult."""

from __future__ import annotations

from .base import VisionModule, vision_result


class YoloDetectModule(VisionModule):
    name = "yolo_detect"

    def __init__(self, config: dict):
        super().__init__(config)
        self.detector = None

    def _load(self):
        if self.detector is None:
            from maix import nn
            family = str(self.config.get("family", "YOLO11")).upper()
            cls = {"YOLOV8": nn.YOLOv8, "YOLO11": nn.YOLO11, "YOLO26": nn.YOLO26}[family]
            self.detector = cls(model=self.config["model"], dual_buff=bool(self.config.get("dual_buff", True)))
        return self.detector

    def process(self, img) -> dict:
        from maix import image
        detector = self._load()
        maix_img = img if hasattr(img, "format") else image.cv2image(img, bgr=True, copy=False)
        objects = detector.detect(maix_img, conf_th=float(self.config.get("confidence", 0.5)),
                                  iou_th=float(self.config.get("iou", 0.45)))
        wanted = set(self.config.get("labels", []))
        candidates = [obj for obj in objects if not wanted or detector.labels[obj.class_id] in wanted]
        width, height = maix_img.width(), maix_img.height()
        if not candidates:
            return vision_result(mode="YOLO", center_x=width // 2, center_y=height // 2)
        best = max(candidates, key=lambda obj: obj.score * obj.w * obj.h)
        x, y = int(best.x + best.w / 2), int(best.y + best.h / 2)
        label = detector.labels[best.class_id]
        return vision_result(ok=True, mode="YOLO", target_x=x, target_y=y, center_x=width // 2, center_y=height // 2,
                             confidence=best.score, status="AIMING",
                             extra={"label": label, "bbox": [best.x, best.y, best.w, best.h]})

