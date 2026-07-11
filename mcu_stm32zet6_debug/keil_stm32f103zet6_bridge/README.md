# STM32F103ZET6 Keil debug bridge

这是可由 Keil MDK 打开的最小 STM32F103ZET6/High-density 工程，只验证：

```text
板载 USB-UART / Type-C → PA10 / USART1_RX（115200, 8-N-1）
-> vision_debug_bridge_rx_byte
-> mv_parser_feed
-> g_latest_aim
-> target_aiming_update
-> g_latest_command
```

默认使用板上 USB-UART（USART1, PA10 RX）。如需切换为 PA3 / USART2，修改 `USER/bridge_config.h`：

```c
#define BRIDGE_USE_USART1    0
#define BRIDGE_USE_USART2    1
```

STM32ZET6 只是临时 debug bridge，最终主控仍是天猛星 MSPM0G3507。本工程不运行 PID，不输出 PWM，不控制舵机、云台、真实激光、小车或机械臂。

## 工具链依赖

工程已在本机按以下环境生成：

- Keil MDK / UV4；
- ARM Compiler 5.06；
- `Keil.STM32F1xx_DFP` 2.4.1（兼容版本也可）；
- STM32F103ZE 设备支持和 `STM32F10x_512.flm` Flash 算法。

仓库包含从本机 STM32F1xx_DFP 模板复用的 `startup_stm32f10x_hd.s`。工程的设备识别、Flash 算法和 ST-Link 下载仍需要用户本机安装 STM32F1xx Device Family Pack。未安装 ARM Compiler 5 时，Keil 会提示迁移到 ARM Compiler 6；迁移后需要重新 Build 验证。

## 当前验证状态

- `.uvprojx/.uvoptx` 可被本机 Keil UV4 识别，目标为 `STM32F103ZE`，Pack 为 `Keil.STM32F1xx_DFP.2.4.1`；
- 所有工程源文件和 include 相对路径已做静态存在性检查；
- 首次 UV4 命令行 Build 发现模板残留 RTOS 选项，现已在最终工程中修正为 `mOS=0`；
- 修正后的最终 UV4 Build 复测被 Codex 桌面执行审批/用量限制阻止，因此当前不能宣称已经生成可用 AXF/HEX。请在本机按下一节执行一次 Build，以最终编译结果为准。

## 打开与 Build

打开：

```text
MDK-ARM/stm32zet6_debug_bridge.uvprojx
```

选择目标 `STM32F103ZET6 Debug Bridge`，执行：

```text
Project -> Build Target
```

成功后本地生成：

```text
Objects/stm32zet6_debug_bridge.axf
Objects/stm32zet6_debug_bridge.hex
```

这些编译产物已被 `.gitignore` 排除，不提交 Git。

## ST-Link 下载

1. 在 `Options for Target -> Debug` 选择 `ST-Link Debugger`；
2. 在 `Utilities` 选择使用 Debug Driver；
3. 确认 Flash Download Algorithm 包含 STM32F10x 512 KB；
4. 连接 SWDIO、SWCLK、GND 和目标板参考电压；
5. 执行 `Download`，然后进入 Debug。

不同 ST-Link 固件与 Keil 安装可能需要首次手动选择调试器；该选择保存在用户本地选项中，不应作为团队通用硬件序列号提交。

## UART 接线

默认使用板载 USB-UART（USART1），Type-C 枚举出的 COM 口直接收发。确认精英板 V2 的 **P3 跳帽** 已短接 PA10↔TXD、PA9↔RXD（通常默认已连），就可以用串口助手选择 Type-C 对应的 COM 口发送测试帧。

```text
板载 USB-UART TXD → PA10 / USART1_RX（通过 P3 跳帽）
板载 USB-UART RXD ← PA9  / USART1_TX（通过 P3 跳帽，当前未使用）
板载 GND 已在板上共地，无需额外接线。
```

若改用外部 USB-TTL 接 PA3 / USART2（需先修改 `bridge_config.h`）：

```text
外部 USB-TTL TX → PA3 / USART2_RX
发送端 GND      → STM32 GND
```

精英板 V2 的 PA3 与 RS485_TX 受 P5 跳帽影响。使用 PA3 前按板卡资料处理 P5，确保 PA3 不被 RS485 发送端驱动。不要连接 RS485 A/B 端子，也不要接执行机构。

MaixVision 无线连接不是 UART 物理链路；`analyze-raw` 只能验证复制的控制台文本。本阶段必须让串口助手通过 Type-C COM 口实际向 USART1_RX 发送字节流。

## 测试帧

在串口助手中选择 ASCII/文本发送，关闭自动附加换行也可以；每帧必须保留结尾 `#`：

```text
$MV,AIM,1,160,120,148,132,-12,12,0.91,25.6,AIMING#
$MV,AIM,1,160,120,190,120,30,0,0.91,25.6,AIMING#
$MV,AIM,0,160,120,0,0,0,0,0.00,25.6,NO_SPOT#
$MV,AIM,1,160,120,162,119,2,-1,0.95,25.6,AIMED#
```

协议字段顺序保持：

```text
$MV,AIM,OK,TARGET_CX,TARGET_CY,SPOT_CX,SPOT_CY,AIM_EX,AIM_EY,SCORE,FPS,STATUS#
```

## Keil Watch

进入 Debug 后添加：

```text
g_latest_aim_ready
g_latest_aim.target_cx
g_latest_aim.target_cy
g_latest_aim.spot_cx
g_latest_aim.spot_cy
g_latest_aim.aim_error_x
g_latest_aim.aim_error_y
g_latest_aim.score
g_latest_aim.fps
g_latest_aim.status
g_latest_command.pan_command
g_latest_command.tilt_command
g_latest_command.valid
g_latest_command.state
```

预期：AIMING 更新误差和建议方向；NO_SPOT 时 `valid=0` 且建议归零；AIMED 时进入 locked/stable 且建议归零。全程不得把建议值接到 GPIO、PWM 或执行器。
