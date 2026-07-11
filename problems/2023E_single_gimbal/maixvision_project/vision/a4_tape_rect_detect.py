def detect_a4_tape_rect(img, config):
    # Safe first version: use explicitly calibrated corners. Automatic black
    # tape detection is intentionally deferred until field images exist.
    corners = config.get("a4_corners", [])
    if len(corners) != 4:
        return {"ok": False, "corners": [], "score": 0.0, "status": "NO_RECT"}
    return {"ok": True, "corners": corners, "score": 1.0, "status": "TRACKING"}


def estimate_rect_path(corners, points_per_edge=20):
    if len(corners) != 4:
        return []
    path = []
    for index, start in enumerate(corners):
        end = corners[(index + 1) % 4]
        for step in range(points_per_edge):
            t = step / float(points_per_edge)
            path.append((int(start[0] + (end[0] - start[0]) * t),
                         int(start[1] + (end[1] - start[1]) * t)))
    return path
