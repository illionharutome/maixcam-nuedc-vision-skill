# YOLO backup plan

当前不训练 YOLO。紫色目标第一版使用现场标定 LAB 阈值和 blob。YOLO 仅作为复杂背景紫色目标、目标板和屏幕边界检测后备。

数据位于 `datasets/raw` 和 `datasets/labels`，建议类别 `purple_target`、`screen`、`aim_marker`。大数据集和权重不提交；训练、转换、部署前分别审查，MaixCAM 部署必须验证 FPS。
