# 2023E manual purple target tracking

当前硬件为一个二维云台，摄像头与低功率红色可见光点固定在同一云台上；用户手动移动紫色目标。画面准星代表红点理论落点，误差定义为 `EX=TARGET_CX-AIM_CX`、`EY=TARGET_CY-AIM_CY`，ZET6 只生成抽象 pan/tilt 建议。

分层：MaixCAM 检测紫色目标并输出 `$MV,TRACK1`；ZET6 解析、运行安全状态机并输出 `$DBG,TRACK1`；真实驱动应由经过确认的底层控制层负责；PC/API 只分析日志。本阶段不输出 PWM、不发送真实云台命令、不控制光源/舵机/电机，405nm 禁用。
