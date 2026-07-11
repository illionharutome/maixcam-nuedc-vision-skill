"""Shared vision module interface and result helpers."""

from __future__ import annotations

from typing import Any


def vision_result(
    *,
    ok: bool = False,
    mode: str = "AIM",
    target_x: int = 0,
    target_y: int = 0,
    center_x: int = 160,
    center_y: int = 120,
    confidence: float = 0.0,
    distance: float = 0.0,
    status: str = "NO_TARGET",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the only result shape allowed across modules and communication."""
    return {
        "ok": bool(ok),
        "mode": str(mode).upper(),
        "target_x": int(target_x),
        "target_y": int(target_y),
        "center_x": int(center_x),
        "center_y": int(center_y),
        "dx": int(target_x) - int(center_x) if ok else 0,
        "dy": int(target_y) - int(center_y) if ok else 0,
        "confidence": max(0.0, min(1.0, float(confidence))),
        "distance": max(0.0, float(distance)),
        "status": str(status).upper(),
        "extra": dict(extra or {}),
    }


class VisionModule:
    name = "base"

    def __init__(self, config: dict):
        self.config = config

    def process(self, img) -> dict:
        raise NotImplementedError

    def draw_debug(self, img, result: dict):
        return img

