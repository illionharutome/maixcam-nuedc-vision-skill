"""$MV ASCII serialization shared by MaixCAM and desktop-side tests."""

try:
    from core.result import VisionResult
except ImportError:  # Permit `python comm/uart_packet.py` during field bring-up.
    import os
    import sys
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from core.result import VisionResult


GENERAL_FIELD_COUNT = 14
AIM_FIELD_COUNT = 12


def _as_int(value):
    return int(value) if value is not None else 0


def _as_float(value):
    value = float(value) if value is not None else 0.0
    return ("%.3f" % value).rstrip("0").rstrip(".") if value else "0"


def _as_text(value, fallback="NONE"):
    value = str(value or fallback)
    if any(char in value for char in ",$#\r\n"):
        raise ValueError("protocol text fields cannot contain comma, '$', or '#'")
    return value


def serialize_vision_result(result):
    """Serialize the fixed 14-field general `$MV` frame."""
    fields = [
        "$MV", _as_text(result.mode, "NONE"), "1" if result.ok else "0",
        _as_text(result.cls), str(_as_int(result.cx)), str(_as_int(result.cy)),
        str(_as_int(result.w)), str(_as_int(result.h)), str(_as_int(result.area)),
        _as_float(result.score), str(_as_int(result.error_x)), str(_as_int(result.error_y)),
        _as_float(result.fps), _as_text(result.status, "ERROR"),
    ]
    return ",".join(fields) + "#"


def serialize_aim_result(result):
    """Serialize the fixed 12-field 2025E `$MV,AIM` frame."""
    fields = [
        "$MV", "AIM", "1" if result.ok else "0",
        str(_as_int(result.target_cx)), str(_as_int(result.target_cy)),
        str(_as_int(result.spot_cx)), str(_as_int(result.spot_cy)),
        str(_as_int(result.aim_error_x)), str(_as_int(result.aim_error_y)),
        _as_float(result.score), _as_float(result.fps), _as_text(result.status, "ERROR"),
    ]
    return ",".join(fields) + "#"


def _parse_int(value, name):
    try:
        return int(value)
    except ValueError:
        raise ValueError("%s must be an integer" % name)


def _parse_float(value, name):
    try:
        return float(value)
    except ValueError:
        raise ValueError("%s must be a float" % name)


def _parse_ok(value):
    if value not in ("0", "1"):
        raise ValueError("OK must be 0 or 1")
    return value == "1"


def parse_mv_packet(packet):
    """Parse one complete `$MV,...#` packet into a ``VisionResult``.

    This is intentionally strict so desktop tests catch packets that the MCU
    parser will reject as well. It accepts ``str`` or ASCII ``bytes`` only.
    """
    if isinstance(packet, bytes):
        packet = packet.decode("ascii")
    if not isinstance(packet, str) or not packet.startswith("$MV,") or not packet.endswith("#"):
        raise ValueError("packet must start with '$MV,' and end with '#'")
    fields = packet[:-1].split(",")
    if fields[1] == "AIM":
        if len(fields) != AIM_FIELD_COUNT:
            raise ValueError("AIM packet has wrong field count")
        result = VisionResult(
            ok=_parse_ok(fields[2]), mode="AIM",
            target_cx=_parse_int(fields[3], "TARGET_CX"), target_cy=_parse_int(fields[4], "TARGET_CY"),
            spot_cx=_parse_int(fields[5], "SPOT_CX"), spot_cy=_parse_int(fields[6], "SPOT_CY"),
            aim_error_x=_parse_int(fields[7], "AIM_EX"), aim_error_y=_parse_int(fields[8], "AIM_EY"),
            score=_parse_float(fields[9], "SCORE"), fps=_parse_float(fields[10], "FPS"),
            status=_as_text(fields[11], "ERROR"),
        )
        result.cx, result.cy = result.spot_cx, result.spot_cy
        result.error_x, result.error_y = result.aim_error_x, result.aim_error_y
        return result
    if len(fields) != GENERAL_FIELD_COUNT:
        raise ValueError("general packet has wrong field count")
    return VisionResult(
        mode=_as_text(fields[1], "NONE"), ok=_parse_ok(fields[2]), cls=_as_text(fields[3]),
        cx=_parse_int(fields[4], "CX"), cy=_parse_int(fields[5], "CY"),
        w=_parse_int(fields[6], "W"), h=_parse_int(fields[7], "H"), area=_parse_int(fields[8], "AREA"),
        score=_parse_float(fields[9], "SCORE"), error_x=_parse_int(fields[10], "EX"),
        error_y=_parse_int(fields[11], "EY"), fps=_parse_float(fields[12], "FPS"),
        status=_as_text(fields[13], "ERROR"),
    )


def _self_test():
    aim = VisionResult(ok=True, mode="AIM", target_cx=160, target_cy=120, spot_cx=148, spot_cy=132,
                       aim_error_x=-12, aim_error_y=12, score=0.91, fps=25.6, status="AIMING")
    packet = serialize_aim_result(aim)
    assert packet == "$MV,AIM,1,160,120,148,132,-12,12,0.91,25.6,AIMING#"
    assert parse_mv_packet(packet).aim_error_x == -12
    normal = VisionResult(ok=True, mode="SPOT", cls="red", cx=12, cy=34, w=5, h=6, area=30,
                          score=0.8, fps=20.0, status="TRACKING")
    assert parse_mv_packet(serialize_vision_result(normal)).cx == 12


if __name__ == "__main__":
    _self_test()
    print("uart_packet self-test passed")
