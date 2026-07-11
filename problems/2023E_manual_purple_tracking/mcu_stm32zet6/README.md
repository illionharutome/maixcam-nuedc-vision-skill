# ZET6 TRACK1 pure-compute framework

本目录不是完整 Keil 工程。它只解析 `$MV,TRACK1`、计算带 sign/kp/kd/deadband/limit/slew 的抽象建议、运行状态机并格式化 dry-run `$GM` 字符串。没有 UART 发送、GPIO、定时器、PWM 或电机启动代码。

`NO_TARGET/LOST/ERROR` 和 `OK=0` 时命令立即归零。接真实底层板前必须单独审查协议、接线、限位、方向、急停和供电。

这些模块已作为 `TRACK1 Dry Run` 文件组接入现有双协议 Keil bridge：

```text
mcu_stm32zet6_debug/keil_stm32f103zet6_bridge/MDK-ARM/stm32zet6_debug_bridge.uvprojx
```

该工程只通过 USART1 回传 `$DBG,TRACK1`；`g_latest_gimbal_dry_run` 仅供 Watch 观察，从未发送到 C8T6 或 DCC-100。

## C8T6 规划阶段

MaixVision TRACK1、ZET6 AIM 回归和 TRACK1 自动验证均已通过。`gimbal_board_build_command()` 现在提供稳定的纯字符串接口：

```c
int gimbal_board_build_command(int pan_milli, int tilt_milli,
                               const char *mode, char *out, int out_size);
```

它只格式化 `$GM,CMD,PAN=...,TILT=...,MODE=...#`，拒绝包含协议分隔符的 mode。模块没有 UART 发送函数、外设初始化或执行输出。

未来若批准串口实验，USART1 继续服务 PC debug；USART2/3 先只连接 USB-TTL 到 PC 观察。不得把当前字符串直接发送给 C8T6，因为 C8T6 原始固件尚无 UART parser 或明确协议。

Stage 2 固件已完成：`BRIDGE_ENABLE_GIMBAL_DRY_UART` 宏（默认 0）控制 USART3 PB10 TX。启用后 TRACKING→`MODE=TRACK`，AIMED→`MODE=AIMED`，LOST/ERROR/NO_TARGET→`MODE=STOP`。接线前核对 PB10 未被占用。详细阶段门禁见 `docs/zet6_to_c8t6_test_plan.md`。
