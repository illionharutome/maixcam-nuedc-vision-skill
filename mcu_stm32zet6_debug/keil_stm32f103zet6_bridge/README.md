# STM32F103ZET6 Keil debug bridge

这是可由 Keil MDK 打开的最小 STM32F103ZET6/High-density 工程，验证：

```text
板载 USB-UART / Type-C -> PA10 / USART1_RX (115200, 8-N-1)
-> vision_debug_bridge_rx_byte
-> mv_parser_feed
-> g_latest_aim
-> target_aiming_update
-> g_latest_command
-> bridge_debug_print_latest
-> PA9 / USART1_TX -> DBG 回传
```

默认使用板上 USB-UART（USART1, PA10 RX / PA9 TX）。如需切换为 PA3 / USART2，修改 `USER/bridge_config.h`：

```c
#define BRIDGE_USE_USART1    0
#define BRIDGE_USE_USART2    1
```

> USART2 模式下无 TX 回传，只做 watch-only 调试。

STM32ZET6 只是临时 debug bridge，最终主控仍是天猛星 MSPM0G3507。本工程不运行 PID，不输出 PWM，不控制舵机、云台、真实激光、小车或机械臂。

## 工具链依赖

工程已在本机按以下环境生成：

- Keil MDK / UV4；
- ARM Compiler 5.06；
- `Keil.STM32F1xx_DFP` 2.4.1（兼容版本也可）；
- STM32F103ZE 设备支持和 `STM32F10x_512.flm` Flash 算法。

仓库包含从本机 STM32F1xx_DFP 模板复用的 `startup_stm32f10x_hd.s`。工程的设备识别、Flash 算法和 ST-Link 下载仍需要用户本机安装 STM32F1xx Device Family Pack。未安装 ARM Compiler 5 时，Keil 会提示迁移到 ARM Compiler 6；迁移后需要重新 Build 验证。

## 打开与 Build（生成 .hex）

打开：

```text
MDK-ARM/stm32zet6_debug_bridge.uvprojx
```

选择目标 `STM32F103ZET6 Debug Bridge`，确认 `Create HEX File` 已勾选：

```text
Options for Target -> Output -> 勾选 Create HEX File
```

（工程已默认开启此选项。）

执行：

```text
Project -> Build Target
```

成功后本地生成：

```text
Objects/stm32zet6_debug_bridge.hex
```

这些编译产物已被 `.gitignore` 排除，不提交 Git。

---

## FlyMcu 下载流程

> FlyMcu 和 VOFA **不能同时占用同一个 COM 口**。
> 下载完成后必须关闭 FlyMcu（或断开其串口连接），否则 VOFA 打不开 COM 口。

1. 将 STM32F103ZET6 精英板 V2 通过 **Type-C 线** 连接到 PC；
2. 设置 BOOT：
   - **BOOT0 = 1**
   - **BOOT1 = 0**
3. 按一下 **复位** 按键；
4. 打开 **FlyMcu**，选择 Type-C 枚举出的 COM 口；
5. 波特率选 **115200**（或 FlyMcu 自动波特率）；
6. 点击"搜索串口"确认设备在线；
7. 选择 Keil Build 生成的 `Objects/stm32zet6_debug_bridge.hex`；
8. 点击"开始编程"；
9. 等待下载完成（FlyMcu 提示"编程成功"）；
10. **关闭 FlyMcu 或断开其串口连接**；
11. 将 BOOT 设置回：
    - **BOOT0 = 0**
    - **BOOT1 = 0**
12. 按一下 **复位** 按键，运行用户程序。

---

## VOFA 调试串口设置

下载完成后，**先确认 FlyMcu 已完全关闭/断开串口**，然后打开 VOFA：

1. 选择 Type-C 枚举出的 COM 口；
2. 协议：**RawData**；
3. 波特率：**115200**；
4. 数据位：8，校验位：None，停止位：1；
5. **关闭 Hex 显示**；
6. 在发送区选择 **文本 / ASCII 发送**；
7. 发送 `$MV,AIM` 测试帧（每帧以 `#` 结束，不加换行）；

VOFA 接收区应看到 DBG 回传行（每行以 `$DBG,AIM` 开头，以 `#` 结束，跟 `\r\n`）。

---

## 工作原理

USART1_RX 中断接收每个字节 -> `vision_debug_bridge_rx_byte()` -> `mv_parser_feed()`
-> 解析出完整 `$MV,AIM` 帧后设置 `g_debug_tx_pending = 1`
-> 主循环检测到标志后清零，调用 `bridge_debug_print_latest()`
-> 通过 USART1_TX 回传 DBG 行。

中断里不做任何字符串格式化和 TX 发送，所有 DBG 格式化在主循环完成。

---

## 测试帧与预期 DBG 回传

协议字段顺序（保持不变）：

```text
$MV,AIM,OK,TARGET_CX,TARGET_CY,SPOT_CX,SPOT_CY,AIM_EX,AIM_EY,SCORE,FPS,STATUS#
```

DBG 回传格式：

```text
$DBG,AIM,EX=<aim_error_x>,EY=<aim_error_y>,CX=<target_cx>,CY=<target_cy>,SX=<spot_cx>,SY=<spot_cy>,PAN=<pan_milli>,TILT=<tilt_milli>,SCORE=<score_milli>,FPS=<fps_milli>,VALID=<0|1>,STATUS=<status>,STATE=<state>#
```

其中 PAN/TILT/SCORE/FPS 为整数毫单位（原始浮点值 × 1000）。

---

### 测试帧 1：普通 AIMING（红点在左上）

发送：

```text
$MV,AIM,1,160,120,148,132,-12,12,0.91,25.6,AIMING#
```

预期 DBG 回传包含：

| 字段 | 值 | 说明 |
|---|---|---|
| EX | -12 | aim_error_x |
| EY | 12 | aim_error_y |
| PAN | -600 | pan_command × 1000，负值表示向左 |
| TILT | 600 | tilt_command × 1000，正值表示向上 |
| VALID | 1 | 有目标、有效 |
| STATUS | AIMING | 正在瞄准 |
| STATE | TRACKING | 跟踪中 |

预期完整回传示例：

```text
$DBG,AIM,EX=-12,EY=12,CX=160,CY=120,SX=148,SY=132,PAN=-600,TILT=600,SCORE=910,FPS=256,VALID=1,STATUS=AIMING,STATE=TRACKING#
```

---

### 测试帧 2：红点在右侧

发送：

```text
$MV,AIM,1,160,120,190,120,30,0,0.91,25.6,AIMING#
```

预期 DBG 回传包含：

| 字段 | 值 | 说明 |
|---|---|---|
| EX | 30 | aim_error_x 为正 |
| EY | 0 | 无垂直误差 |
| PAN | 正向或 1000 | pan 为正（limit=1.0, gain=0.05, 30×0.05=1.5 → 限幅 1.0） |
| TILT | 0 | 无 tilt |
| VALID | 1 | 有效 |

---

### 测试帧 3：NO_SPOT（无光斑）

发送：

```text
$MV,AIM,0,160,120,0,0,0,0,0.00,25.6,NO_SPOT#
```

预期 DBG 回传包含：

| 字段 | 值 | 说明 |
|---|---|---|
| VALID | 0 | 无效 |
| PAN | 0 | 归零 |
| TILT | 0 | 归零 |
| STATUS | NO_SPOT | 无光斑 |
| STATE | NO_SPOT | TARGET_AIM_NO_SPOT |

---

### 测试帧 4：AIMED（已锁定）

发送：

```text
$MV,AIM,1,160,120,162,119,2,-1,0.95,25.6,AIMED#
```

预期 DBG 回传包含：

| 字段 | 值 | 说明 |
|---|---|---|
| EX | 2 | 小误差 |
| EY | -1 | 小误差 |
| VALID | 1 | 有效/AIMED 状态 |
| PAN | 0 | 误差在 dead zone 内，不输出 pan |
| TILT | 0 | 误差在 dead zone 内，不输出 tilt |
| STATUS | AIMED | 已瞄准 |
| STATE | LOCKED | TARGET_AIM_LOCKED |

---

## Safety & Constraints

- STM32ZET6 只是 debug bridge，不是最终主控。
- 最终主控仍然是天猛星 MSPM0G3507。
- 本工程不输出 PWM、不控制舵机/云台/激光/小车/机械臂。
- `pan_command` / `tilt_command` 是无量纲建议值，不是角度、脉宽或可直接执行的命令。
- 405nm 激光保持禁用。
- 不使用真实激光、YOLO、小车或机械臂功能。
- 不修改 MaixCAM 视觉逻辑和 `$MV,AIM` 协议字段顺序。

---

## Keil Watch（备选：ST-Link 调试器观察）

如需用 ST-Link 调试器观察变量，进入 Debug 后添加：

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

> 注意：如果本机没有可用的 ST-Link 工具，推荐使用 FlyMcu + VOFA 串口回传方案（见上文），无需 ST-Link 硬件。
