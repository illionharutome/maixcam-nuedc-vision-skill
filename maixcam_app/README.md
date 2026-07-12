# MaixCAM 应用

入口为 `main.py`。设备需要 MaixPy v4、OpenCV 和 NumPy；普通 YAML 语法还需 PyYAML，仓库默认配置不需要它。

电脑端可用 `replay_test.py` 对保存图像测试传统视觉；`main.py` 的 Camera/Display/UART 只在 MaixCAM Pro 上运行。模块不得自行拼串口字符串，必须返回 `VisionResult`，由 `uart_protocol.py` 编码。

官方 API 参考：

- <https://wiki.sipeed.com/maixpy/doc/en/vision/camera.html>
- <https://wiki.sipeed.com/maixpy/doc/en/vision/opencv.html>
- <https://wiki.sipeed.com/maixpy/doc/en/peripheral/uart.html>

## 视觉优化工具

- `collect_dataset.py`：在 MaixCAM 上记录相机/场景元数据、处理耗时和代表帧。
- `annotate_samples.py`：在电脑端点击目标中心或标记无目标。
- `dataset_report.py`：检查标注完整性、正负样本和场景覆盖。
- `replay_test.py`：输出全局及逐场景指标，拒绝不完整数据集。
- `parameter_sweep.py`：对嵌套 YAML 参数做有上限的确定性网格搜索。

完整命令见 `docs/vision_optimization.md`。
