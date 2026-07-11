# MaixCAM 应用

入口为 `main.py`。设备需要 MaixPy v4、OpenCV 和 NumPy；普通 YAML 语法还需 PyYAML，仓库默认配置不需要它。

电脑端可用 `replay_test.py` 对保存图像测试传统视觉；`main.py` 的 Camera/Display/UART 只在 MaixCAM Pro 上运行。模块不得自行拼串口字符串，必须返回 `VisionResult`，由 `uart_protocol.py` 编码。

官方 API 参考：

- <https://wiki.sipeed.com/maixpy/doc/en/vision/camera.html>
- <https://wiki.sipeed.com/maixpy/doc/en/vision/opencv.html>
- <https://wiki.sipeed.com/maixpy/doc/en/peripheral/uart.html>

