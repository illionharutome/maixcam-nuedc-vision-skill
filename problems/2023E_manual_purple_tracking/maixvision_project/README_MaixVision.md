# MaixVision 独立工程

在 MaixVision 选择 Open Folder / Project，直接打开本目录并运行 `main.py`。工程不依赖仓库根目录、`problems.*`、`../../shared` 或桌面 OpenCV。

先用实际紫色手动目标在现场标定 `config/purple_detect.yaml` 的 LAB 阈值，再通过 `aim_calibration.yaml` 手动调整红色光点理论落点准星。默认 UART 关闭，第一阶段只在控制台打印 `$MV,TRACK1`。

程序不检测自己的红色光点，不控制光源、PWM、舵机、云台、电机、小车或机械臂，405nm 保持禁用。
