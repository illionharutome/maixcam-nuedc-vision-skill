def _number(value, digits):
    text = (("%%.%df" % digits) % float(value)).rstrip("0").rstrip(".")
    return text or "0"


def serialize_track1(result):
    status = str(result.status)
    if any(c in status for c in ",$#\r\n"): raise ValueError("unsafe status")
    return ",".join(["$MV", "TRACK1", "1" if result.ok else "0",
        str(result.target_cx), str(result.target_cy), str(result.aim_cx), str(result.aim_cy),
        str(result.error_x), str(result.error_y), _number(result.score, 3),
        _number(result.fps, 2), status]) + "#"
