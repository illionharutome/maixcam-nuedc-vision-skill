"""Perception-only placeholder for a future vehicle task protocol."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VehicleTaskResult:
    ok: bool = False
    task_mode: str = "NONE"
    object_class: str = "NONE"
    target_error_x: int = 0
    target_error_y: int = 0
    line_error_x: int = 0
    line_angle: float = 0.0
    distance_estimate: Optional[float] = None
    score: float = 0.0
    status: str = "NO_TARGET"
    timestamp_ms: int = 0

    # Deliberately no speed, steering, brake, motor PWM, or actuator fields.
