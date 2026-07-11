# STM32F103ZET6 Keil debug bridge

这是可由 Keil MDK 打开的最小 STM32F103ZET6/High-density 双协议 debug bridge。原 `$MV,AIM` 路径保持不变，并新增 `$MV,TRACK1` dry-run：

```text
板载 USB-UART / Type-C → PA10 / USART1_RX（115200, 8-N-1）
-> vision_debug_bridge_rx_byte
-> mv_parser_feed
-> g_latest_aim
-> target_aiming_update
-> g_latest_command
```

```text
USART1 -> protocol_track1 -> g_latest_track1
-> manual_tracker_update -> g_latest_track1_command
-> $DBG,TRACK1 回传
```

默认使用板上 USB-UART（USART1, PA10 RX）。如需切换为 PA3 / USART2，修改 `USER/bridge_config.h`：

```c
#define BRIDGE_USE_USART1    0
#define BRIDGE_USE_USART2    1
```

本工程仅做 ZET6 文本解析和控制建议验证，不运行真实 PID，不输出 PWM，不控制舵机、云台、电机、真实激光、小车或机械臂，也不会把 `$GM,CMD` 发送到 C8T6/DCC-100。

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
- AIM + TRACK1 双协议工程已用 ARM Compiler 5.06 update 7 实际构建；
- 构建结果为 `0 Error(s), 0 Warning(s)`，已生成本地 AXF/HEX（均由 Git 忽略）；
- 主机集成测试直接复用了固件接收函数，验证 AIM 原路径和 TRACK1 TRACKING/NO_TARGET/AIMED 路径。

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

## TRACK1 dry-run

同一固件、同一 USART1 自动识别：

```text
$MV,TRACK1,OK,TARGET_CX,TARGET_CY,AIM_CX,AIM_CY,EX,EY,SCORE,FPS,STATUS#
```

测试帧：

```text
$MV,TRACK1,1,140,110,160,120,-20,-10,0.90,30.0,TRACKING#
$MV,TRACK1,1,190,140,160,120,30,20,0.90,30.0,TRACKING#
$MV,TRACK1,0,0,0,160,120,0,0,0.00,30.0,NO_TARGET#
$MV,TRACK1,1,162,119,160,120,2,-1,0.95,30.0,AIMED#
```

回传示例：

```text
$DBG,TRACK1,EX=-20,EY=-10,PAN=-300,TILT=-150,VALID=1,STATUS=TRACKING,STATE=TRACKING#
```

Watch：`g_latest_track1`、`g_latest_track1_command`、`g_latest_gimbal_dry_run`、`g_debug_packet_kind`。`g_latest_gimbal_dry_run` 只是未发送文本。NO_TARGET/LOST/ERROR 时命令立即归零；AIMED 或 deadband 内命令为零。

```text
python problems\2023E_manual_purple_tracking\scripts\stm32_track1_auto_check.py --port COM5
```

若轴符号配置改变，可附加 `--sign-x -1` 或 `--sign-y -1`。脚本只收发 USART1 debug 文本，不连接执行机构。

## Stage 2: gimbal dry UART (USART3 TX to USB-TTL)

### 宏配置

`USER/bridge_config.h` 中：

```c
#define BRIDGE_ENABLE_GIMBAL_DRY_UART  0   /* 仓库默认关闭 */
```

仓库默认 **0**，第二阶段串口代码不编译、不产生任何输出。
用户本地测试时临时改为 **1**，Build 后才生效。

### 接线

```text
ZET6 PB10 (USART3_TX)  -->  USB-TTL 模块 RX
ZET6 GND                -->  USB-TTL 模块 GND
```

> 接线前核对板卡原理图/丝印，确认 PB10 未被其他外设占用。
> 若 PB10 不可用，需根据实际板卡另选引脚并修改代码。

**绝对不接 C8T6、DCC-100、步进电机、舵机或任何执行机构。**
USB-TTL 模块的另一端是 PC 串口助手或双串口脚本。

### 行为

当 `BRIDGE_ENABLE_GIMBAL_DRY_UART = 1` 且收到有效 TRACK1 帧时，ZET6 通过 USART3_TX (PB10) 发送：

- TRACKING：`$GM,CMD,PAN=...,TILT=...,MODE=TRACK#`
- AIMED/deadband：`$GM,CMD,PAN=0,TILT=0,MODE=AIMED#`
- NO_TARGET/LOST/ERROR：`$GM,CMD,PAN=0,TILT=0,MODE=STOP#`

每收到一帧 TRACK1 最多发送一帧 $GM,CMD。AIM 帧不触发 gimbal 输出。

### 双串口自动验证

需要 **两个 COM 口**（Type-C + USB-TTL 各一个）：

```text
# 先跑单串口回归（确认基础链路正常）
python scripts\stm32_bridge_auto_check.py --port COM5
python problems\2023E_manual_purple_tracking\scripts\stm32_track1_auto_check.py --port COM5

# 再跑双串口
python problems\2023E_manual_purple_tracking\scripts\stm32_gimbal_dry_uart_check.py --debug-port COM5 --gimbal-port COM7
```

`--debug-port` 是 Type-C COM 口（USART1），`--gimbal-port` 是 USB-TTL COM 口（USART3_TX）。

### 故障排查：GM TIMEOUT

如果双串口测试中 DBG 正常但 GM 全部 TIMEOUT，按顺序排查：

1. 确认 `BRIDGE_ENABLE_GIMBAL_DRY_UART = 1`
2. 确认 Build + Download + Reset
3. 确认 USB-TTL 对应 COM 口号
4. 确认 PB10 → USB-TTL RX，GND → GND
5. 临时设置 `BRIDGE_GIMBAL_DRY_UART_BOOT_TEST = 1`，Build + 烧录
6. 运行监听脚本：
   ```text
   python problems\2023E_manual_purple_tracking\scripts\listen_gimbal_uart.py --port COM6
   ```
7. 若看到 `$GM,BOOT,USART3,OK#`，说明 USART3 物理链路 OK；继续排查 TRACK1 触发路径
8. 若未见 BOOT 输出，问题在 USART3 初始化、PB10 引脚、Keil 工程或硬件接线
9. USART1 侧可观察诊断行 `$DBG,GMUART,EN=1,BOOT=1,TX_COUNT=N#`，确认固件侧是否进入发送路径

> 完成后将两个宏都改回 0，不要提交 BOOT_TEST=1 的配置。

---

## 自动串口验证

固件在收到完整 `$MV,AIM` 帧后，会通过 **USART1_TX** 回传一行 `$DBG,AIM,...#` 调试文本。

PC 端可用 Python 脚本自动完成发送、接收、解析、验证：

```text
python scripts\stm32_bridge_auto_check.py --port COM5 --baud 115200
```

脚本自动：
1. 打开 Type-C / COM 口；
2. 依次发送四帧 `$MV,AIM`；
3. 每帧等待 `$DBG,AIM` 回传；
4. 解析 DBG，检查 EX/EY/PAN/TILT/VALID/STATUS/STATE；
5. 输出每帧 PASS/FAIL 及汇总；
6. 保存日志到 `logs/serial/stm32_bridge_auto_check.txt`。

### 可选 DeepSeek API 分析

```text
set DEEPSEEK_API_KEY=你的key
python scripts\stm32_bridge_auto_check.py --port COM5 --baud 115200 --deepseek
```

DeepSeek 仅分析脚本采集到的串口日志，**不直接访问 Keil Watch**，**不控制任何硬件**。

> API key 通过环境变量传入，不写在代码里，不提交 Git。

### 前提条件

- 已安装 pyserial：`pip install pyserial`
- 固件已通过 ST-Link 下载到 ZET6 且正在运行
- FlyMcu / 其他串口工具已关闭，不占用 COM 口
- STM32ZET6 仍然是 debug bridge，最终主控仍然是天猛星 MSPM0G3507
