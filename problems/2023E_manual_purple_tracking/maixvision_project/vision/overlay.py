def draw_overlay(img, result, radius, image):
    img.draw_cross(result.aim_cx, result.aim_cy, image.COLOR_RED, size=radius, thickness=2)
    if result.ok:
        img.draw_cross(result.target_cx, result.target_cy, image.COLOR_BLUE, size=8, thickness=2)
        img.draw_line(result.aim_cx, result.aim_cy, result.target_cx, result.target_cy, image.COLOR_YELLOW, thickness=2)
    img.draw_string(4, 4, "%s ex=%d ey=%d" % (result.status, result.error_x, result.error_y), image.COLOR_WHITE)
    img.draw_string(4, 22, "fps=%.1f score=%.2f" % (result.fps, result.score), image.COLOR_WHITE)
