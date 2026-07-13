# 2023 E 题视觉开源来源与移植边界

本仓库的 E 题视觉实现保持 `VisionModule -> VisionResult -> UART` 架构。算法优先参考以下 MIT 开源项目，
但不直接复制其 STM32 HAL、OpenMV 设备 API 或私有串口协议。

## 主要来源

- `NinoC137/Ti_E_AutoServo`（MIT）：2023 E 题完整实现。复用其“先识别旋转矩形四角、向内偏移到胶带中心线、
  沿四边插值目标点”和低曝光红色光斑检测思路。
  <https://github.com/NinoC137/Ti_E_AutoServo>
- `RaymondMeng/light_trace`（MIT）：复用色块中心作为二维误差反馈、逐帧发送坐标和丢失目标发送停止状态的思路。
  <https://github.com/RaymondMeng/light_trace>
- OpenCV（Apache-2.0）：实际运行使用其颜色空间转换、阈值、轮廓、`minAreaRect`、四边形近似和形态学实现。
  <https://github.com/opencv/opencv>

## 本仓库适配

- OpenMV `find_blobs` 由既有 `LaserSpotModule` 的 OpenCV 阈值与连通域实现替代。
- OpenMV `find_rects` 由 `RectangleDetectModule` 的阈值、轮廓、旋转矩形和角点排序实现替代。
- 所有参数进入 JSON 兼容 YAML；所有模块只输出统一 `VisionResult`。
- 运行时只由 MaixCAM UART1 向 MSPM0G3507 追踪控制器发送视觉误差；红色目标控制系统与追踪系统不通信。
