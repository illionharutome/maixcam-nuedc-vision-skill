"""Single owner of the human-readable MaixCAM UART protocol."""

ALLOWED_MODES = {"AIM", "TRACK", "LINE", "YOLO"}
ALLOWED_STATUS = {"AIMING", "LOCKED", "NO_TARGET", "LOST"}


def encode_vision_result(result: dict) -> str:
    mode = str(result.get("mode", "AIM")).upper()
    status = str(result.get("status", "NO_TARGET")).upper()
    if mode not in ALLOWED_MODES:
        raise ValueError(f"unsupported mode: {mode}")
    if status not in ALLOWED_STATUS:
        raise ValueError(f"unsupported status: {status}")
    fields = (
        "$MV",
        mode,
        1 if result.get("ok") else 0,
        int(result.get("center_x", 0)),
        int(result.get("center_y", 0)),
        int(result.get("target_x", 0)),
        int(result.get("target_y", 0)),
        int(result.get("dx", 0)),
        int(result.get("dy", 0)),
        round(max(0.0, min(1.0, float(result.get("confidence", 0.0)))) * 100),
        round(max(0.0, float(result.get("distance", 0.0)))),
        status,
    )
    return ",".join(map(str, fields)) + "#"

