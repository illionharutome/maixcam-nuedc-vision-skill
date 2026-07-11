# ZET6 TRACK1 pure-compute framework

本目录不是完整 Keil 工程。它只解析 `$MV,TRACK1`、计算带 sign/kp/kd/deadband/limit/slew 的抽象建议、运行状态机并格式化 dry-run `$GM` 字符串。没有 UART 发送、GPIO、定时器、PWM 或电机启动代码。

`NO_TARGET/LOST/ERROR` 和 `OK=0` 时命令立即归零。接真实底层板前必须单独审查协议、接线、限位、方向、急停和供电。
