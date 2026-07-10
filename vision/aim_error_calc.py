"""Combine board and spot observations into a stateful 2025E AIM result."""

from core.result import VisionResult, STATUS_AIMED, STATUS_AIMING, STATUS_NO_BOARD, STATUS_NO_SPOT


class AimErrorCalculator:
    def __init__(self, config):
        self.config = config
        self.aimed_frames = 0

    def update(self, board, spot):
        if not board.ok or board.target_cx is None or board.target_cy is None:
            self.aimed_frames = 0
            return VisionResult(mode="AIM", status=STATUS_NO_BOARD, lost_frames=board.lost_frames + 1)
        if not spot.ok or spot.spot_cx is None or spot.spot_cy is None:
            self.aimed_frames = 0
            return VisionResult(mode="AIM", target_cx=board.target_cx, target_cy=board.target_cy,
                                status=STATUS_NO_SPOT, lost_frames=spot.lost_frames + 1)
        error_x = int(spot.spot_cx) - int(board.target_cx)
        error_y = int(spot.spot_cy) - int(board.target_cy)
        within = (abs(error_x) <= int(self.config["aimed_threshold_x"]) and
                  abs(error_y) <= int(self.config["aimed_threshold_y"]))
        self.aimed_frames = self.aimed_frames + 1 if within else 0
        status = STATUS_AIMED if self.aimed_frames >= int(self.config["aimed_required_frames"]) else STATUS_AIMING
        return VisionResult(ok=True, mode="AIM", cls="target_aiming", cx=spot.spot_cx, cy=spot.spot_cy,
                            score=min(board.score, spot.score), status=status, target_cx=board.target_cx,
                            target_cy=board.target_cy, spot_cx=spot.spot_cx, spot_cy=spot.spot_cy,
                            aim_error_x=error_x, aim_error_y=error_y, error_x=error_x, error_y=error_y)


def calculate_aim_error(board, spot, config):
    """Stateless convenience function; use ``AimErrorCalculator`` in a live app."""
    return AimErrorCalculator(config).update(board, spot)

