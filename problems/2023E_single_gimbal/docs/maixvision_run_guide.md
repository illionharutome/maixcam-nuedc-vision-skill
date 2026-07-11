# MaixVision 运行指南

1. 在 MaixVision 选择 Open Folder / Project。
2. 打开 `problems/2023E_single_gimbal/maixvision_project`，不要打开单个脚本。
3. 先用固定屏幕和低功率安全可见替代光点实测 LAB 阈值，保持 `405nm_enabled=false`。
4. 检查 `screen_calibration.yaml` 四角和 `single_gimbal.yaml` 的 `path_id`。
5. 运行唯一入口 `main.py`，观察十字、路径、误差和控制台 `$MV,SINGLE`。
6. 默认 `uart.yaml` 中 UART 关闭；无线 MaixVision 控制台不是 UART 物理链路。

程序只输出观测协议，不控制光源、PWM、舵机或云台。光束只允许落在固定屏幕，有物理遮挡和急停准备。
