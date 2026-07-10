"""Future YOLO adapter; not part of the 2025E minimum loop."""


class YoloDetector:
    """Reserve a unified detector interface without claiming a model exists."""

    def __init__(self, model_path=None):
        self.model_path = model_path

    def load(self):
        raise NotImplementedError("YOLO model loading is a later phase; no model is bundled")

    def detect(self, image):
        del image
        raise NotImplementedError("YOLO inference is not implemented in the 2025E minimum loop")
