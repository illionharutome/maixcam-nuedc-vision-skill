# Tests

Python helper test validates TRACK1 serialization and DBG parsing. Host C test covers strict parsing, split/glued frames, oversized rejection, invalid-state zeroing and dry-run GM formatting. No hardware is accessed.

`test_dual_protocol_bridge.c` 直接复用 Keil 工程的 bridge 接收函数，依次验证原 `$MV,AIM` 和新 `$MV,TRACK1`，用于防止兼容性回归。
