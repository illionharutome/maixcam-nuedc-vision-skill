from core.result import TrackResult


class PurpleDetector:
    def __init__(self, config):
        self.config, self.cx, self.cy, self.lost = config, None, None, 0

    @staticmethod
    def _v(blob, index, name):
        fn = getattr(blob, name, None)
        return int(fn()) if callable(fn) else int(blob[index])

    def detect(self, img):
        if not self.config.get("enabled", True): return TrackResult(status="ERROR")
        blobs = img.find_blobs([self.config["lab_threshold"]], area_threshold=int(self.config["min_area"]),
                               pixels_threshold=int(self.config["min_area"]), merge=False)
        candidates = []
        for b in blobs:
            x, y, w, h = self._v(b,0,"x"), self._v(b,1,"y"), self._v(b,2,"w"), self._v(b,3,"h")
            area = self._v(b,4,"pixels")
            if int(self.config["min_area"]) <= area <= int(self.config["max_area"]):
                candidates.append((area, x, y, w, h))
        if not candidates:
            self.lost += 1
            status = "LOST" if self.lost > int(self.config.get("lost_timeout_frames", 5)) else "NO_TARGET"
            return TrackResult(status=status)
        area, x, y, w, h = max(candidates)
        raw_x, raw_y = x + w // 2, y + h // 2
        alpha = float(self.config.get("smoothing_alpha", 0.5))
        self.cx = raw_x if self.cx is None else alpha * raw_x + (1-alpha) * self.cx
        self.cy = raw_y if self.cy is None else alpha * raw_y + (1-alpha) * self.cy
        score = min(1.0, area / float(max(1, self.config["max_area"])))
        self.lost = 0
        if score < float(self.config.get("min_score", 0.0)): return TrackResult(status="NO_TARGET")
        return TrackResult(True, int(self.cx), int(self.cy), area=area, score=score, status="TRACKING")


def detect_purple_target(img, config):
    return PurpleDetector(config).detect(img)
