"""Small stateful target tracker used by lightweight detectors."""

from __future__ import annotations

import math


class TargetTracker:
    def __init__(self, max_jump_px: float = 80.0, hold_frames: int = 3):
        self.max_jump_px = float(max_jump_px)
        self.hold_frames = int(hold_frames)
        self.last: tuple[int, int] | None = None
        self.lost_frames = 0

    def choose(self, candidates: list[dict]) -> dict | None:
        if not candidates:
            self.lost_frames += 1
            return None
        if self.last is None:
            chosen = max(candidates, key=lambda item: item["score"])
        else:
            nearby = [
                item for item in candidates
                if math.hypot(item["x"] - self.last[0], item["y"] - self.last[1]) <= self.max_jump_px
            ]
            chosen = max(nearby or candidates, key=lambda item: item["score"])
        self.last = (int(chosen["x"]), int(chosen["y"]))
        self.lost_frames = 0
        return chosen

    def held_position(self) -> tuple[int, int] | None:
        if self.last is not None and self.lost_frames <= self.hold_frames:
            return self.last
        return None

