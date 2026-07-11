def screen_center(config):
    corners = config.get("corners", [[20, 20], [300, 20], [300, 220], [20, 220]])
    return (sum(int(p[0]) for p in corners) // 4,
            sum(int(p[1]) for p in corners) // 4)


def normalized_point(config, nx, ny):
    corners = config.get("corners", [[20, 20], [300, 20], [300, 220], [20, 220]])
    left = (corners[0][0] + corners[3][0]) / 2.0
    right = (corners[1][0] + corners[2][0]) / 2.0
    top = (corners[0][1] + corners[1][1]) / 2.0
    bottom = (corners[2][1] + corners[3][1]) / 2.0
    return int(left + nx * (right - left)), int(top + ny * (bottom - top))


def square_path(config, points_per_edge=20):
    path = []
    vertices = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for index, start in enumerate(vertices):
        end = vertices[(index + 1) % 4]
        for step in range(points_per_edge):
            t = step / float(points_per_edge)
            path.append(normalized_point(config, start[0] + (end[0] - start[0]) * t,
                                         start[1] + (end[1] - start[1]) * t))
    return path
