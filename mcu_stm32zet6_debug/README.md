# STM32ZET6 debug bridge 实板解析验证

本目录只用于验证以下数据链路：

```text
$MV,AIM 文本字节流
-> mcu_common/mv_parser
-> Aim_Result
-> target_aiming_state_machine
-> TargetAimingCommand（仅供调试器观察）
```

STM32ZET6 只是 debug bridge，不是最终主控。本阶段不运行 PID，不输出 PWM，不控制舵机、云台、真实激光、小车或机械臂。`pan_command` 和 `tilt_command` 是无量纲建议值，不是角度、脉宽或可直接执行的命令。

## 1. 示例代码能力与工程集成

[`examples/example_receive_aiming.c`](examples/example_receive_aiming.c) 已完成：

1. 逐字节调用 `mv_parser_feed()`；
2. 保存最新 `Aim_Result` 到 `g_latest_aim`；
3. 调用现有 `target_aiming_update()`；
4. 保存建议结果到 `g_latest_command`；
5. 最后置位 `g_latest_aim_ready`，方便断点或 watch 判断新帧。

把以下源码加入 STM32 工程：

```text
mcu_common/mv_parser.c
mcu_tmx3507/app/target_aiming_state_machine.c
mcu_stm32zet6_debug/examples/example_receive_aiming.c
```

在时钟和 UART 初始化完成后调用一次：

```c
vision_debug_bridge_init();
```

在 UART RX 中断、HAL 回调或 DMA 消费循环中，把收到的每一个字节依次传入：

```c
vision_debug_bridge_rx_byte(received_byte);
```

示例故意不写死 HAL/标准库、UART 号、中断函数、DMA、GPIO 或时钟配置。先用 115200、8-N-1；实际 UART 外设与引脚必须以当前 STM32 工程和板卡资料为准。

## 2. 已确认的精英板 V2 UART 候选引脚

依据工作区 `H:\ForCodex\MaixCam\zet6\精英板V2 IO引脚分配表.xlsx`：

- 推荐单向接收：`PA3 = USART2_RX`。表中说明 PA3 与 `RS485_TX` 受 P5 跳帽配置影响；用于本测试前，应按板卡资料断开/调整 P5，使 PA3 不受 RS485 发送端驱动。
- USART2 可选回传：`PA2 = USART2_TX`。PA2 与 `RS485_RX` 同样受 P5 配置影响。
- 备选接收：`PA10 = USART1_RX`。它默认通过 P3 连接 CH340_TX；接 MaixCAM TX 前必须处理 P3，避免 CH340_TX 与 MaixCAM TX 同时驱动 PA10。
- USART1 可选回传：`PA9 = USART1_TX`，默认通过 P3 连接 CH340_RX。

不要把 MaixCAM TTL UART 接到 RS485 的 A/B 差分端子。引脚表中的 36/37/101/102 是 MCU 引脚编号，不应直接当作板上排针编号；实际排针位置继续对照原理图和板卡丝印。

## 3. 最小接线

只做单向解析时：

```text
MaixCAM TX -> STM32ZET6 UART RX（推荐 PA3/USART2_RX，先处理 P5）
MaixCAM GND -> STM32ZET6 GND
```

只有未来确实需要双向通信时才增加：

```text
MaixCAM RX <- STM32ZET6 UART TX
```

接线前确认两端 UART 逻辑电平兼容。不要接任何执行机构。MaixVision 无线连接不是 UART 物理链路：无线运行和控制台 `print` 不会自动让 STM32 RX 收到字节。若 MaixCAM 当前仍是 print-only 配置，则其 TX 引脚不会输出这些帧；本指南不修改 MaixCAM 配置或协议。

## 4. 测试帧

按顺序发送以下 ASCII 文本，每帧以 `#` 结束：

```text
$MV,AIM,1,160,120,148,132,-12,12,0.91,25.6,AIMING#
$MV,AIM,1,160,120,190,120,30,0,0.91,25.6,AIMING#
$MV,AIM,0,160,120,0,0,0,0,0.00,25.6,NO_SPOT#
```

使用示例中的调试配置（gain 0.05、limit 1.0、dead zone 2）时，预期：

| 帧 | valid | state | pan_command | tilt_command |
|---|---:|---|---:|---:|
| `-12,12,AIMING` | 1 | `TARGET_AIM_TRACKING` | 约 -0.60 | 约 +0.60 |
| `30,0,AIMING` | 1 | `TARGET_AIM_TRACKING` | +1.00（限幅） | 0 |
| `NO_SPOT` | 0 | `TARGET_AIM_NO_SPOT` | 0 | 0 |

以上数值只验证解析、方向、限幅和安全归零，不得连接到 PWM 或执行器。

## 5. Debugger watch 清单

建议添加：

```text
g_latest_aim_ready
g_latest_aim.target_cx
g_latest_aim.target_cy
g_latest_aim.spot_cx
g_latest_aim.spot_cy
g_latest_aim.aim_error_x
g_latest_aim.aim_error_y
g_latest_aim.status
g_latest_command.pan_command
g_latest_command.tilt_command
g_latest_command.valid
g_latest_command.state
```

对应用户关注字段为：`target_cx`、`target_cy`、`spot_cx`、`spot_cy`、`aim_error_x`、`aim_error_y`、`status`、`pan_command`、`tilt_command`、`valid`、`state`。

## 6. 通过标准

1. 三种测试帧都能使 `g_latest_aim_ready` 更新；
2. `Aim_Result` 与文本字段完全一致；
3. 左右误差对应 pan 建议符号正确；
4. `NO_SPOT` 时 `valid=0` 且 pan/tilt 为 0；
5. 全程没有 PID、PWM 或执行机构动作；
6. 405nm 保持禁用，仍不使用真实激光、YOLO、小车或机械臂功能。
