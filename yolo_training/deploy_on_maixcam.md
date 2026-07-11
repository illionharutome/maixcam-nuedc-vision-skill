# 部署到 MaixCAM Pro

1. 将 `.mud` 及其关联模型复制到 `/root/models/`。
2. 修改 `maixcam_app/configs/yolo_target.yaml`，不要改模块代码。
3. 先在 MaixVision 检查框、标签、FPS 与温度，再接 UART。
4. 用 `replay_test.py` 固化阈值，用现场负样本确认误报率。
5. 需要精确中心时，把 YOLO 框作为传统视觉 ROI。
