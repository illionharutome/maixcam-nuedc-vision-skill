"""Transport-neutral result object returned by every vision module."""

from dataclasses import dataclass
from typing import Optional


STATUS_TRACKING = "TRACKING"
STATUS_NO_TARGET = "NO_TARGET"
STATUS_NO_SPOT = "NO_SPOT"
STATUS_NO_BOARD = "NO_BOARD"
STATUS_AIMING = "AIMING"
STATUS_AIMED = "AIMED"
STATUS_LOST = "LOST"
STATUS_ERROR = "ERROR"


@dataclass
class VisionResult:
    ok: bool = False
    mode: str = "NONE"
    cls: str = "NONE"
    cx: Optional[int] = None
    cy: Optional[int] = None
    w: int = 0
    h: int = 0
    area: int = 0
    score: float = 0.0
    error_x: int = 0
    error_y: int = 0
    world_x: Optional[float] = None
    world_y: Optional[float] = None
    distance: Optional[float] = None
    size: Optional[float] = None
    grid: str = "NONE"
    row: int = 0
    col: int = 0
    angle: float = 0.0
    status: str = STATUS_ERROR
    lost_frames: int = 0
    fps: float = 0.0
    target_cx: Optional[int] = None
    target_cy: Optional[int] = None
    spot_cx: Optional[int] = None
    spot_cy: Optional[int] = None
    aim_error_x: int = 0
    aim_error_y: int = 0

