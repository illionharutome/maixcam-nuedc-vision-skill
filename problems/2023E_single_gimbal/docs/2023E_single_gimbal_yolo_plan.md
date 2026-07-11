# YOLO 后备计划

当前不立即训练。小光点优先使用现场实测 LAB 阈值与 blob；YOLO 主要作为 A4 黑胶带矩形、旋转 A4、屏幕边界和复杂背景鲁棒性的后备。

数据位于 `datasets/2023e_single/raw` 与 `labels`，建议类别为 `a4_tape_rect`、`screen_border`、`black_tape_edge`、`spot`。第一步只采集并审查数据；训练、模型转换和 MaixCAM 部署分别审查，部署时必须测 FPS。大数据集和权重不提交 Git。
