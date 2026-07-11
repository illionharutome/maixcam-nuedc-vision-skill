class TrackResult:
    def __init__(self, ok=False, target_cx=0, target_cy=0, aim_cx=0, aim_cy=0,
                 error_x=0, error_y=0, area=0, score=0.0, fps=0.0, status="ERROR"):
        self.ok, self.target_cx, self.target_cy = bool(ok), int(target_cx), int(target_cy)
        self.aim_cx, self.aim_cy = int(aim_cx), int(aim_cy)
        self.error_x, self.error_y = int(error_x), int(error_y)
        self.area, self.score, self.fps, self.status = int(area), float(score), float(fps), str(status)
