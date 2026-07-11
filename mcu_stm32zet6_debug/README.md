# STM32ZET6 debug bridge —— 实板 FlyMcu + VOFA 验证

本目录只用于验证以下数据链路：

```text
$MV,AIM 文本字节流
-> mcu_common/mv_parser
-> Aim_Result
-> target_aiming_state_machine
-> TargetAimingCommand
-> USART1_TX 回传 DBG 调试文本到 VOFA
```

STM32ZET6 只是临时 debug bridge，不是最终主控。最终主控仍然是天猛星 MSPM0G3507；后续真实小车、云台和其他执行机构控制必须迁移到天猛星 MSPM0G3507。本阶段 STM32ZET6 只验证 UART 接收、`$MV,AIM` 解析、状态机建议值方向和 USART1 TX 回传，不运行真实 PID，不输出 PWM，不控制舵机、云台、真实激光、小车或机械臂。`pan_command` 和 `tilt_command` 是无量纲建议值，不是角度、脉宽或可直接执行的命令。

---

## 1. 代码结构

```
mcu_stm32zet6_debug/
├── README.md                          <- 本文件
├── examples/
│   └── example_receive_aiming.c       <- vision_debug_bridge 接收 + 解析 + 全局变量
└── keil_stm32f103zet6_bridge/
    ├── README.md                      <- Keil 工程说明书 + FlyMcu/VOFA 操作指南
    ├── MDK-ARM/
    │   └── stm32zet6_debug_bridge.uvprojx
    ├── CMSIS/
    │   └── startup_stm32f10x_hd.s
    └── USER/
        ├── bridge_config.h            <- UART 选择 + 时钟 + 中断号
        └── main.c                     <- 时钟、UART RX/TX 初始化、TX helper、DBG 输出主循环
```

引用依赖：

```
mcu_common/mv_parser.c              <- $MV,AIM 帧解析器（复用）
mcu_common/mv_parser.h
mcu_common/mv_protocol.h
mcu_common/mv_result.h              <- Aim_Result 结构体
mcu_tmx3507/app/target_aiming_state_machine.c  <- 瞄准状态机（复用）
mcu_tmx3507/app/target_aiming_state_machine.h
```

---

## 2. 已确认的精英板 V2 UART 引脚

依据原理图：

- **PA10 = USART1_RX** ← USB-UART TXD（通过 P3 跳帽）
- **PA9  = USART1_TX** → USB-UART RXD（通过 P3 跳帽）
- P3 默认短接即可使用；Type-C 枚举出的 COM 口可同时收发。
- 备选：PA3 = USART2_RX（受 P5 跳帽影响，需先处理 P5 配置）。

**本阶段使用 USART1（板载 USB-UART，PA10 RX + PA9 TX）。**

---

## 3. 最小接线

**无需额外接线**——Type-C 线直连 PC 即可：

```text
板载 USB-UART TXD -> PA10 / USART1_RX（通过 P3 跳帽）
板载 USB-UART RXD <- PA9  / USART1_TX（通过 P3 跳帽）
板载 GND 已在板上共地。
```

---

## 4. 编译与下载

### 4.1 Keil Build 生成 .hex

1. 打开 `keil_stm32f103zet6_bridge/MDK-ARM/stm32zet6_debug_bridge.uvprojx`；
2. 确认 `Options for Target -> Output -> Create HEX File` **已勾选**（工程已默认开启）；
3. 执行 `Project -> Build Target`；
4. 成功生成 `Objects/stm32zet6_debug_bridge.hex`。

### 4.2 FlyMcu 下载 .hex

> **FlyMcu 和 VOFA 不能同时占用同一个 COM 口。下载完成后必须关闭 FlyMcu 或断开其串口连接。**

1. 将精英板 V2 通过 **Type-C 线** 连接到 PC；
2. **BOOT0 = 1，BOOT1 = 0**；
3. 按一下 **复位** 按键；
4. 打开 **FlyMcu**，选择 Type-C 枚举出的 COM 口；
5. 波特率选 115200；
6. 选择 `Objects/stm32zet6_debug_bridge.hex`；
7. 点击"开始编程"；
8. 下载成功后 **关闭 FlyMcu**（否则 VOFA 打不开 COM 口）；
9. **BOOT0 = 0，BOOT1 = 0**；
10. 按一下 **复位** 按键，运行用户程序。

---

## 5. VOFA 串口回传验证

### 5.1 VOFA 设置

1. 打开 VOFA，选择 Type-C 枚举出的 COM 口；
2. 协议：**RawData**；
3. 波特率：**115200**，8-N-1；
4. **关闭 Hex 显示**；
5. 发送区选择 **文本 / ASCII 发送**。

### 5.2 DBG 回传格式

每收到一帧完整的 `$MV,AIM`，STM32ZET6 通过 USART1_TX 回传一行：

```text
$DBG,AIM,EX=<int>,EY=<int>,CX=<int>,CY=<int>,SX=<int>,SY=<int>,PAN=<milli_int>,TILT=<milli_int>,SCORE=<milli_int>,FPS=<milli_int>,VALID=<0|1>,STATUS=<str>,STATE=<str>#
```

其中：
- **EX/EY**：aim_error_x / aim_error_y（整数像素）
- **CX/CY**：target_cx / target_cy（目标质心）
- **SX/SY**：spot_cx / spot_cy（光斑质心）
- **PAN/TILT**：pan/tilt 命令 × 1000（整数毫单位，例如 -600 表示 -0.600）
- **SCORE/FPS**：置信度/帧率 × 1000
- **VALID**：0 或 1
- **STATUS**：AIMING / AIMED / NO_SPOT 等
- **STATE**：DISABLED / NO_SPOT / TRACKING / LOCKED

---

## 6. 测试帧与预期 DBG 回传

### 测试帧 1：普通 AIMING（红点在左上）

发送：

```text
$MV,AIM,1,160,120,148,132,-12,12,0.91,25.6,AIMING#
```

期望 DBG 包含：

| 字段 | 期望值 |
|---|---|
| EX | -12 |
| EY | 12 |
| PAN | 负值（约 -600） |
| TILT | 正值（约 +600） |
| VALID | 1 |
| STATUS | AIMING |
| STATE | TRACKING |

---

### 测试帧 2：红点在右侧

发送：

```text
$MV,AIM,1,160,120,190,120,30,0,0.91,25.6,AIMING#
```

期望 DBG 包含：

| 字段 | 期望值 |
|---|---|
| EX | 30 |
| EY | 0 |
| PAN | 正值或 +1000（限幅） |
| TILT | 0 |
| VALID | 1 |

---

### 测试帧 3：NO_SPOT（无光斑）

发送：

```text
$MV,AIM,0,160,120,0,0,0,0,0.00,25.6,NO_SPOT#
```

期望 DBG 包含：

| 字段 | 期望值 |
|---|---|
| VALID | 0 |
| PAN | 0 |
| TILT | 0 |
| STATUS | NO_SPOT |
| STATE | NO_SPOT |

---

### 测试帧 4：AIMED（已锁定）

发送：

```text
$MV,AIM,1,160,120,162,119,2,-1,0.95,25.6,AIMED#
```

期望 DBG 包含：

| 字段 | 期望值 |
|---|---|
| EX | 2 |
| EY | -1 |
| VALID | 1 |
| PAN | 0（dead zone 内） |
| TILT | 0（dead zone 内） |
| STATUS | AIMED |
| STATE | LOCKED |

---

## 7. 通过标准

1. 四种测试帧都能使 `g_latest_aim_ready` 更新；
2. VOFA 接收区收到对应 DBG 回传行；
3. `Aim_Result` 字段与发送的文本字段完全一致；
4. 左右误差对应 pan 建议值符号正确；
5. `NO_SPOT` 时 `valid=0` 且 pan/tilt 为 0；
6. 全程没有 PID、PWM 或执行机构动作；
7. 405nm 保持禁用，仍不使用真实激光、YOLO、小车或机械臂功能。
8. STM32ZET6 仍然是 debug bridge，天猛星 MSPM0G3507 仍然是最终主控。
