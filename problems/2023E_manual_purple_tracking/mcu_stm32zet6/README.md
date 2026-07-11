# ZET6 TRACK1 pure-compute framework

本目录不是完整 Keil 工程。它只解析 `$MV,TRACK1`、计算带 sign/kp/kd/deadband/limit/slew 的抽象建议、运行状态机并格式化 dry-run `$GM` 字符串。没有 UART 发送、GPIO、定时器、PWM 或电机启动代码。

`NO_TARGET/LOST/ERROR` 和 `OK=0` 时命令立即归零。接真实底层板前必须单独审查协议、接线、限位、方向、急停和供电。

这些模块已作为 `TRACK1 Dry Run` 文件组接入现有双协议 Keil bridge：

```text
mcu_stm32zet6_debug/keil_stm32f103zet6_bridge/MDK-ARM/stm32zet6_debug_bridge.uvprojx
```

该工程只通过 USART1 回传 `$DBG,TRACK1`；`g_latest_gimbal_dry_run` 仅供 Watch 观察，从未发送到 C8T6 或 DCC-100。
