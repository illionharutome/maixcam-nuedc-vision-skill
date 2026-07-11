# YOLO / MaixHub 训练入口

只在复杂物体类别、数字或符号难以用几何/颜色稳定区分时使用 YOLO。激光点、色块、线、圆和边框优先传统视觉。推荐让 YOLO 找大目标，再在框内用传统视觉找精确中心。

- 路线 A：按 `maixhub_workflow.md` 在 MaixHub 快速训练。
- 路线 B：按 `offline_train_yolo.md` 离线训练，再导出 ONNX、转换 MUD、部署。

设备端以 `maix.nn.YOLO11` 为默认；MaixPy 4.12.5 及以上也可评估 YOLO26。模型、数据集和导出权重禁止提交到 Git。

