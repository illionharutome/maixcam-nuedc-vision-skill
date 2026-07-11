# Testing guide

1. MaixVision 打开 `maixvision_project`，UART 保持关闭。
2. 用紫色纸片/标记现场标定 LAB，确认红色光点不会被识别为紫色目标。
3. 手工调整 `aim_cx/aim_cy`，只观察 `$MV,TRACK1`。
4. PC 运行仿真和日志分析。
5. ZET6 只验证 `$DBG,TRACK1` 与 dry-run `$GM` 字符串。
6. 未完成底层板、限位和接线审查前不接执行机构。
