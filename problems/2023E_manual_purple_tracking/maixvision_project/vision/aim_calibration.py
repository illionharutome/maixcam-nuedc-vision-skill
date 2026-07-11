class AimCalibration:
    def __init__(self, config):
        self.cx, self.cy = int(config["aim_cx"]), int(config["aim_cy"])
        self.tx, self.ty = int(config.get("threshold_x", 8)), int(config.get("threshold_y", 8))
        self.required, self.stable = int(config.get("aimed_required_frames", 3)), 0

    def evaluate(self, target):
        if not target.ok: self.stable = 0; return 0, 0, target.status
        ex, ey = target.target_cx - self.cx, target.target_cy - self.cy
        self.stable = self.stable + 1 if abs(ex) <= self.tx and abs(ey) <= self.ty else 0
        return ex, ey, "AIMED" if self.stable >= self.required else "TRACKING"
