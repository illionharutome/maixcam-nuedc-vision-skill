# 2023E manual purple target tracking

当前硬件为一个二维云台，摄像头与低功率红色可见光点固定在同一云台上；用户手动移动紫色目标。画面准星代表红点理论落点，误差定义为 `EX=TARGET_CX-AIM_CX`、`EY=TARGET_CY-AIM_CY`，ZET6 只生成抽象 pan/tilt 建议。

分层：MaixCAM 检测紫色目标并输出 `$MV,TRACK1`；ZET6 解析、运行安全状态机并输出 `$DBG,TRACK1`；真实驱动应由经过确认的底层控制层负责；PC/API 只分析日志。本阶段不输出 PWM、不发送真实云台命令、不控制光源/舵机/电机，405nm 禁用。

## 当前验证状态

已完成 MaixVision TRACK1 视觉输出、四方向 EX/EY、PC 仿真/分析、ZET6 双协议 Keil Build 与烧录、AIM 回归及 TRACK1 dry-run 自动验证。结论见 `tests/track1_dry_run_test_report.md`。

当前进入 C8T6 资料审查和 ZET6 -> C8T6 dry-run 规划。下一步只能在内存生成字符串；之后先让 ZET6 第二串口接 USB-TTL，由 PC 观察，不接 C8T6。C8T6 无电机接收验证通过后，才允许单独审批空载低速测试。

C8T6 原始固件是两轴步进开环往返演示，没有通信协议、限位或闭环，并且会主动调用电机函数，当前禁止直接接电机使用。
