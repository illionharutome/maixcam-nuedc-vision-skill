"""Perception-only placeholder for a future arm task protocol."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ArmTaskResult:
    ok: bool = False
    object_class: str = "NONE"
    object_cx: int = 0
    object_cy: int = 0
    object_w: int = 0
    object_h: int = 0
    object_angle: float = 0.0
    object_score: float = 0.0
    grasp_point_x: int = 0
    grasp_point_y: int = 0
    grasp_angle: float = 0.0
    distance_estimate: Optional[float] = None
    status: str = "NO_OBJECT"
    timestamp_ms: int = 0

    # Deliberately no servo angles, PWM values, or action sequences.
