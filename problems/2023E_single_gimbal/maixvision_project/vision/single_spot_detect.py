from core.result import VisionResult


def _value(blob, index, name):
    method = getattr(blob, name, None)
    return int(method()) if callable(method) else int(blob[index])


def detect_single_spot(img, config):
    blobs = img.find_blobs(
        [config.get("lab_threshold", [0, 100, 25, 127, -20, 100])],
        roi=config.get("roi", []),
        area_threshold=int(config.get("area_threshold", 3)),
        pixels_threshold=int(config.get("pixels_threshold", 3)),
        merge=bool(config.get("merge", False)),
    )
    best = None
    for blob in blobs:
        x, y = _value(blob, 0, "x"), _value(blob, 1, "y")
        w, h = _value(blob, 2, "w"), _value(blob, 3, "h")
        pixels = _value(blob, 4, "pixels")
        density = pixels / float(max(1, w * h))
        if density < float(config.get("min_density", 0.2)):
            continue
        candidate = (pixels, density, x, y, w, h)
        if best is None or candidate[:2] > best[:2]:
            best = candidate
    if best is None:
        return VisionResult(status="NO_SPOT")
    pixels, density, x, y, w, h = best
    score = min(1.0, density * min(1.0, pixels / float(config.get("score_pixels", 20))))
    return VisionResult(ok=True, spot_cx=x + w // 2, spot_cy=y + h // 2,
                        score=score, status="TRACKING")
