class VisionResult:
    def __init__(self, ok=False, spot_cx=0, spot_cy=0, target_cx=0, target_cy=0,
                 error_x=0, error_y=0, path_id="CENTER", step_id=0,
                 score=0.0, fps=0.0, status="ERROR"):
        self.ok = bool(ok)
        self.spot_cx = int(spot_cx)
        self.spot_cy = int(spot_cy)
        self.target_cx = int(target_cx)
        self.target_cy = int(target_cy)
        self.error_x = int(error_x)
        self.error_y = int(error_y)
        self.path_id = str(path_id)
        self.step_id = int(step_id)
        self.score = float(score)
        self.fps = float(fps)
        self.status = str(status)
