# STM32ZET6 debug bridge 实板解析验证

本目录只用于验证以下数据链路：

```text
$MV,AIM 文本字节流
-> mcu_common/mv_parser
-> Aim_Result
-> target_aiming_state_machine
-> TargetAimingCommand（仅供调试器观察）
```

STM32ZET6 只是临时 debug bridge，不是最终主控。最终主控仍然是天猛星 MSPM0G3507；后续真实小车、云台和其他执行机构控制必须迁移到天猛星 MSPM0G3507。本阶段 STM32ZET6 只验证 UART 接收、`$MV,AIM` 解析和状态机建议值方向，不运行真实 PID，不输出 PWM，不控制舵机、云台、真实激光、小车或机械臂。`pan_command` 和 `tilt_command` 是无量纲建议值，不是角度、脉宽或可直接执行的命令。

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

依据工作区 `H:\ForCodex\MaixCam\zet6\精英板V2 IO引脚分配表.xlsx` 和原理图：

- **默认（板载 USB-UART / Type-C）**：`PA10 = USART1_RX`、`PA9 = USART1_TX`，通过 P3 跳帽连接板载 CH340。P3 默认短接即可使用；串口助手选择 Type-C 枚举出的 COM 口，115200、8-N-1、ASCII，可同时收发。
- 备选接收：`PA3 = USART2_RX`。PA3 与 `RS485_TX` 受 P5 跳帽配置影响；用于本测试前，应按板卡资料断开/调整 P5，使 PA3 不受 RS485 发送端驱动。
- USART2 可选回传：`PA2 = USART2_TX`。PA2 与 `RS485_RX` 同样受 P5 配置影响。

不要把 MaixCAM TTL UART 接到 RS485 的 A/B 差分端子。引脚表中的 36/37/101/102 是 MCU 引脚编号，不应直接当作板上排针编号；实际排针位置继续对照原理图和板卡丝印。

## 3. 最小接线

默认使用板载 USB-UART（USART1），无需额外接线——Type-C 线直连 PC，串口助手选择对应 COM 口即可：

```text
板载 USB-UART TXD → PA10 / USART1_RX（通过 P3 跳帽）
板载 GND 已在板上共地。
```

若改用外部 USB-TTL 接 USART2（需先在 `keil_stm32f103zet6_bridge/USER/bridge_config.h` 中将 `BRIDGE_USE_USART1` 改为 0、`BRIDGE_USE_USART2` 改为 1）：

```text
外部 USB-TTL TX → PA3 / USART2_RX
发送端 GND      → STM32 GND
```

只有未来确实需要双向通信时才增加 TX 接线。接线前确认两端 UART 逻辑电平兼容。不要接任何执行机构。MaixVision 无线连接不是 UART 物理链路：无线运行和控制台 `print` 不会自动让 STM32 RX 收到字节。若 MaixCAM 当前仍是 print-only 配置，则其 TX 引脚不会输出这些帧；本指南不修改 MaixCAM 配置或协议。

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

---

## 7. 自动串口验证（Python 脚本）

固件在收到完整 `$MV,AIM` 帧后通过 USART1_TX 回传 `$DBG,AIM,...#`。可用脚本自动验证：

```text
python scripts\stm32_bridge_auto_check.py --port COM5 --baud 115200
```

脚本流程：

1. 打开 Type-C 枚举的 COM 口；
2. 自动发送四帧 `$MV,AIM`；
3. 每帧等待 `$DBG,AIM` 回传并解析；
4. 按预期字段判断每帧 PASS/FAIL；
5. 打印汇总，输出日志到 `logs/serial/stm32_bridge_auto_check.txt`。

看到 `OVERALL: PASS` 即说明 PC → USART1 → parser → state machine → DBG 回传链路通过。

### 可选 DeepSeek API 分析

```text
set DEEPSEEK_API_KEY=你的key
python scripts\stm32_bridge_auto_check.py --port COM5 --baud 115200 --deepseek
```

DeepSeek 仅分析本地串口日志文本，不直接访问 Keil Watch，不控制硬件。

### 前置

- `pip install pyserial`
- ST-Link 已 Download 固件，ZET6 正在运行
- 关闭 FlyMcu / 其他占用 COM 口的工具
- 本阶段不接真实激光、云台、舵机、小车、机械臂、PWM
- STM32ZET6 仍是 debug bridge，天猛星 MSPM0G3507 仍是最终主控
