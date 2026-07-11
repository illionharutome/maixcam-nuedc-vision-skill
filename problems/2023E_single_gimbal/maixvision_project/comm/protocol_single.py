FIELD_COUNT = 14


def _text(value):
    value = str(value)
    if any(c in value for c in ",$#\r\n"):
        raise ValueError("unsafe protocol text field")
    return value


def _number(value, digits):
    text = (("%%.%df" % digits) % float(value)).rstrip("0").rstrip(".")
    return text or "0"


def serialize_single(result):
    fields = [
        "$MV", "SINGLE", "1" if result.ok else "0",
        str(result.spot_cx), str(result.spot_cy),
        str(result.target_cx), str(result.target_cy),
        str(result.error_x), str(result.error_y),
        _text(result.path_id), str(result.step_id),
        _number(result.score, 3), _number(result.fps, 2),
        _text(result.status),
    ]
    return ",".join(fields) + "#"
