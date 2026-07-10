from maix import camera, display, app, time, image

cam = camera.Camera(320, 240)
disp = display.Display()

# 红色阈值：先用粗略值，后面根据实际画面调
red_threshold = [[30, 100, 15, 127, 15, 127]]

aimed_threshold_x = 8
aimed_threshold_y = 8
aimed_required_frames = 3
aimed_count = 0

while not app.need_exit():
    img = cam.read()

    img_w = img.width()
    img_h = img.height()

    # 先用画面中心作为靶心
    target_cx = img_w // 2
    target_cy = img_h // 2

    # 画靶心
    img.draw_cross(target_cx, target_cy, color=image.COLOR_GREEN)
    img.draw_string(5, 5, "TARGET CENTER", color=image.COLOR_WHITE)

    blobs = img.find_blobs(
        red_threshold,
        area_threshold=20,
        pixels_threshold=20,
        merge=True
    )

    if blobs:
        best = max(blobs, key=lambda b: b.pixels())

        x, y, w, h = best.x(), best.y(), best.w(), best.h()
        spot_cx = x + w // 2
        spot_cy = y + h // 2

        aim_error_x = spot_cx - target_cx
        aim_error_y = spot_cy - target_cy

        if abs(aim_error_x) <= aimed_threshold_x and abs(aim_error_y) <= aimed_threshold_y:
            aimed_count += 1
        else:
            aimed_count = 0

        if aimed_count >= aimed_required_frames:
            status = "AIMED"
        else:
            status = "AIMING"

        img.draw_rect(x, y, w, h, color=image.COLOR_RED)
        img.draw_cross(spot_cx, spot_cy, color=image.COLOR_RED)

        img.draw_string(5, 25, "SPOT: %d,%d" % (spot_cx, spot_cy), color=image.COLOR_WHITE)
        img.draw_string(5, 45, "ERR: %d,%d" % (aim_error_x, aim_error_y), color=image.COLOR_WHITE)
        img.draw_string(5, 65, status, color=image.COLOR_WHITE)

        print("$MV,AIM,1,%d,%d,%d,%d,%d,%d,1.00,0.0,%s#" % (
            target_cx,
            target_cy,
            spot_cx,
            spot_cy,
            aim_error_x,
            aim_error_y,
            status
        ))

    else:
        aimed_count = 0
        status = "NO_SPOT"

        img.draw_string(5, 25, "NO_SPOT", color=image.COLOR_WHITE)

        print("$MV,AIM,0,%d,%d,0,0,0,0,0.00,0.0,NO_SPOT#" % (
            target_cx,
            target_cy
        ))

    disp.show(img)
    time.sleep_ms(20)