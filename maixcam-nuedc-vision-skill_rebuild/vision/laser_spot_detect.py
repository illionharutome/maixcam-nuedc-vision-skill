"""Detect a configured low-power competition light spot with MaixPy ``find_blobs``."""

from core.result import VisionResult, STATUS_NO_SPOT, STATUS_TRACKING


def _value(blob, index, method):
    candidate = getattr(blob, method, None)
    return int(candidate()) if callable(candidate) else int(blob[index])


def _profile(config, name):
    profiles = config.get("profiles", {})
    name = name or config.get("active_profile")
    if name not in profiles:
        raise ValueError("unknown laser profile: %s" % name)
    return name, profiles[name]


def detect_laser_spot(img, config, profile_name=None, roi=None):
    """Return the best blob in an explicit LAB profile as ``VisionResult``.

    ``lab_threshold`` and all area values are starter placeholders. They must be
    calibrated with the actual MaixCAM-Pro, target paper, exposure, and ambient
    lighting before enabling physical 405 nm closed-loop tests.
    """
    name, profile = _profile(config, profile_name)
    if not profile.get("enabled", False):
        return VisionResult(mode="SPOT", cls=name, status=STATUS_NO_SPOT)
    effective_roi = roi if roi is not None else profile.get("roi", [])
    blobs = img.find_blobs(
        [profile["lab_threshold"]], roi=effective_roi,
        area_threshold=int(profile.get("area_threshold", 1)),
        pixels_threshold=int(profile.get("pixels_threshold", 1)),
        merge=bool(profile.get("merge", False)),
    )
    best = None
    for blob in blobs:
        x, y = _value(blob, 0, "x"), _value(blob, 1, "y")
        w, h = _value(blob, 2, "w"), _value(blob, 3, "h")
        pixels = _value(blob, 4, "pixels")
        area = max(1, w * h)
        density = pixels / float(area)
        if density < float(profile.get("min_density", 0.0)):
            continue
        score = min(1.0, density) * min(1.0, pixels / float(max(1, profile.get("score_pixels", 1))))
        candidate = (score, pixels, x, y, w, h, density)
        if best is None or candidate[:2] > best[:2]:
            best = candidate
    if best is None:
        return VisionResult(mode="SPOT", cls=name, status=STATUS_NO_SPOT)
    score, pixels, x, y, w, h, _ = best
    return VisionResult(ok=True, mode="SPOT", cls=name, cx=x + w // 2, cy=y + h // 2,
                        w=w, h=h, area=pixels, score=score, status=STATUS_TRACKING,
                        spot_cx=x + w // 2, spot_cy=y + h // 2)

