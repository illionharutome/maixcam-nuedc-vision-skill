# 视觉到小车主控的后续接口

MaixCAM 未来可提供 `target_error_x/y`、`line_error_x`、`line_angle`、距离估计、类别、置信度、状态和任务模式。它不得输出电机 PWM、底盘速度、转向或刹车命令。

MSPM0G3507 必须负责速度与转向、制动、避障、PID、限幅、目标丢失、超时、搜索、回中、手动停止和执行使能。视觉识别模块与底盘执行模块必须解耦。

当前 `VehicleTaskResult` 和 MCU 文件仅占位，初始化保持 `manual_stop=1`、`execution_enabled=0`。不实现自动驾驶控制，也不实现 TASK 解析。

未来新增 TASK 帧时必须保持现有 AIM 帧不变，并增加 Python/C 解析器测试。
