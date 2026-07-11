# MaixVision 独立工程

在 MaixVision 中选择 **Open Folder / Project**，打开本 `maixvision_project` 目录，运行 `main.py`。不要只复制单个文件，也不需要打开仓库根目录。

工程只依赖自身的 `core/`、`comm/`、`vision/` 与 `config/`，不使用 `problems.*`、`../../shared` 或桌面 OpenCV。默认 UART 关闭，协议会打印到控制台；如需连接 ZET6，仅在确认共地和串口电平后修改 `config/uart.yaml`。

首次运行前必须在 MaixVision 阈值工具中实测安全可见低功率光点的 LAB 范围，并更新 `config/spot_detect.yaml`。`405nm_enabled` 必须保持 `false`。

当前程序只测量 `EX/EY` 并发送 `$MV,SINGLE`，不控制光源、PWM、舵机或云台。
