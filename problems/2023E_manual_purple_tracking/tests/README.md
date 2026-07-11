# Tests

Python helper test validates TRACK1 serialization and DBG parsing. Host C test covers strict parsing, split/glued frames, oversized rejection, invalid-state zeroing and dry-run GM formatting. No hardware is accessed.

`test_dual_protocol_bridge.c` 直接复用 Keil 工程的 bridge 接收函数，依次验证原 `$MV,AIM` 和新 `$MV,TRACK1`，用于防止兼容性回归。

`test_track1_mcu.c` 验证 TRACK1 parser 半帧/粘包/超长帧丢弃、追踪状态机 AIMED 归零、gimbal 命令字符串 mode 过滤和缓冲区安全。

Stage 2 双串口验证（USART3 PB10 TX → USB-TTL）：`../scripts/stm32_gimbal_dry_uart_check.py`。
