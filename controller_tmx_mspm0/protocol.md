# MaixCAM Pro → 天猛星 ASCII UART 协议

## 物理层

- 115200 baud，8N1，3.3V TTL。
- MaixCAM TX 接 MSPM0 RX；两板必须共地。
- 建议优先 UART1，避免 UART0 启动日志；若使用 `/dev/ttyS0`，主控解析器会忽略 `$MV` 之外的文本。

## 帧格式

```text
$MV,mode,valid,cx,cy,tx,ty,dx,dy,conf,dist_mm,status#
```

示例：

```text
$MV,AIM,1,160,120,148,132,-12,12,91,256,AIMING#
```

| 字段 | 约束 |
|---|---|
| mode | AIM / TRACK / LINE / YOLO |
| valid | 0 无目标，1 有目标 |
| cx, cy | 图像中心，整数像素 |
| tx, ty | 目标中心，整数像素 |
| dx, dy | `target - center`，有符号整数像素 |
| conf | 0–100 |
| dist_mm | 0–65535 mm；未知时为 0 |
| status | AIMING / LOCKED / NO_TARGET / LOST |

帧最大长度受解析缓冲区 96 字节限制。MaixCAM 端只有 `uart_protocol.py` 可以生成字符串；主控端 `vision_parser.c` 逐字节解析，解析阶段不控制电机。

## 故障恢复

遇到 `$` 时无条件开始新帧；遇到 `#` 才提交；字段、数字范围或枚举非法时丢弃整帧。控制循环必须另行做接收超时与丢帧保护。
