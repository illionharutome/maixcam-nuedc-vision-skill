# 天猛星 MSPM0G3507 集成说明

1. 在 TI MSPM0 SDK 工程中导入 08 工程的 `empty.syscfg`，由 SysConfig 重新生成 `ti_msp_dl_config.c/.h`。
2. 加入本目录的 `step_motor.*`、解析器、控制器和适配层；先只编译，不接电机电源。
3. UART RX ISR 只把每个字节传给 `vision_parser_feed()`；返回 `true` 时把 `VisionCommand_t` 投递给主循环，不在 ISR 控电机。
4. 主循环以固定周期调用 `gimbal_control_update()`；若超过约定帧周期未收到新帧，调用 `gimbal_control_on_frame_timeout()`。
5. 无负载点动确认：电机 1/2 的机械轴、正方向、软限位。再设置 `invert_pan/invert_tilt`。
6. DCC-100 先共地，再接 11–26V 动力电源；MSPM0 只提供 3.3V 逻辑。

`step_motor.c` 是唯一允许直接使用 DriverLib GPIO/Timer 的文件。`motor_adapter.c` 只调用迁移接口；`vision_parser.c` 只解析文本。

注意：连续跟踪使用 `step_motor_start()`；定角点动使用 `step_motor_set_angle()`。同一路未完成的定角命令会被后续命令覆盖，现场应避免高频重复下发定角命令。
