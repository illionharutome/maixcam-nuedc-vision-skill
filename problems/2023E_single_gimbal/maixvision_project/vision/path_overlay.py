def draw_overlay(img, result, path, image_module):
    for point in path[::max(1, len(path) // 24)]:
        img.draw_circle(point[0], point[1], 1, image_module.COLOR_BLUE, thickness=1)
    img.draw_cross(result.target_cx, result.target_cy, image_module.COLOR_GREEN, size=9, thickness=2)
    if result.ok:
        img.draw_cross(result.spot_cx, result.spot_cy, image_module.COLOR_RED, size=7, thickness=2)
        img.draw_line(result.target_cx, result.target_cy, result.spot_cx, result.spot_cy,
                      image_module.COLOR_YELLOW, thickness=2)
    img.draw_string(4, 4, "%s %s" % (result.path_id, result.status), image_module.COLOR_WHITE)
    img.draw_string(4, 22, "ex=%d ey=%d fps=%.1f" %
                    (result.error_x, result.error_y, result.fps), image_module.COLOR_WHITE)
