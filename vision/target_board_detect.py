"""Minimum target-center detector for the 2025E bring-up phase."""

from core.result import VisionResult, STATUS_NO_BOARD, STATUS_TRACKING


def _value(item, index, method):
    candidate = getattr(item, method, None)
    return int(candidate()) if callable(candidate) else int(item[index])


def _image_center(img):
    width = img.width() if callable(getattr(img, "width", None)) else img.width
    height = img.height() if callable(getattr(img, "height", None)) else img.height
    return int(width) // 2, int(height) // 2


def detect_target_board(img, config):
    """Detect a center using ``fixed_center``, `red_center`, or `rectangle_board` mode."""
    mode = config.get("mode", "fixed_center")
    if mode == "fixed_center":
        cx, cy = _image_center(img)
        return VisionResult(ok=True, mode="BOARD", cls="fixed_center", cx=cx, cy=cy,
                            target_cx=cx, target_cy=cy, score=1.0, status=STATUS_TRACKING)
    if mode == "red_center":
        profile = config.get("red_center", {})
        if not profile.get("enabled", False):
            return VisionResult(mode="BOARD", cls="red_center", status=STATUS_NO_BOARD)
        blobs = img.find_blobs([profile["lab_threshold"]], roi=profile.get("roi", []),
                               area_threshold=int(profile.get("area_threshold", 1)),
                               pixels_threshold=int(profile.get("pixels_threshold", 1)))
        if not blobs:
            return VisionResult(mode="BOARD", cls="red_center", status=STATUS_NO_BOARD)
        blob = max(blobs, key=lambda item: _value(item, 4, "pixels"))
        x, y = _value(blob, 0, "x"), _value(blob, 1, "y")
        w, h = _value(blob, 2, "w"), _value(blob, 3, "h")
        cx, cy = x + w // 2, y + h // 2
        return VisionResult(ok=True, mode="BOARD", cls="red_center", cx=cx, cy=cy, w=w, h=h,
                            area=_value(blob, 4, "pixels"), score=1.0, target_cx=cx, target_cy=cy,
                            status=STATUS_TRACKING)
    if mode == "rectangle_board":
        profile = config.get("rectangle_board", {})
        try:
            rects = img.find_rects(roi=profile.get("roi", []), threshold=int(profile.get("threshold", 10000)))
        except AttributeError:
            rects = []
        if rects:
            rect = max(rects, key=lambda item: _value(item, 2, "w") * _value(item, 3, "h"))
            x, y = _value(rect, 0, "x"), _value(rect, 1, "y")
            w, h = _value(rect, 2, "w"), _value(rect, 3, "h")
            cx, cy = x + w // 2, y + h // 2
            return VisionResult(ok=True, mode="BOARD", cls="rectangle_board", cx=cx, cy=cy, w=w, h=h,
                                area=w*h, score=1.0, target_cx=cx, target_cy=cy, status=STATUS_TRACKING)
        return VisionResult(mode="BOARD", cls="rectangle_board", status=STATUS_NO_BOARD)
    raise ValueError("unknown target-board mode: %s" % mode)

