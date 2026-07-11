# API tuning plan

`tune_manual_tracking.py` 本地计算误差、锁定时间、抖动、超调、饱和率、丢失次数和 FPS，并建议 kp/kd、deadband、limit、smoothing 与 sign 检查。

可选 `--deepseek` 仅在 `DEEPSEEK_API_KEY` 环境变量存在时上传聚合摘要；不打印 key、不上传原始图像、不改配置、不控制硬件、不自动发送云台命令。
