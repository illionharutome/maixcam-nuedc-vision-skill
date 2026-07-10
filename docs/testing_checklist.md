# 无激光替代测试 checklist

## 开始前

- [ ] 只准备红点图片、红色 LED、屏幕红点、红色纸点等低风险替代物。
- [ ] 不接真实激光、405nm、云台、舵机、小车或机械臂。
- [ ] MaixVision 打开整个项目文件夹。
- [ ] `laser_spot.yaml` 的 `active_profile` 是 `red`，405nm 是 `enabled: false`。

## 原子测试

- [ ] 运行 `app_target_board_detect`，确认画面中心绿色十字和 BOARD 普通帧。
- [ ] 运行 `app_laser_spot_detect`，确认有红点时 TRACKING、移走红点时 NO_SPOT。
- [ ] 确认独立红点 app 只输出 `$MV,SPOT`，不输出 AIM。
- [ ] 运行 `app_aim_error_demo`，确认 AIMING 和连续三帧后的 AIMED。
- [ ] 红点在左边时 `aim_error_x < 0`，右边时 `> 0`。
- [ ] 红点在上边时 `aim_error_y < 0`，下边时 `> 0`。

## 协议与日志

- [ ] MaixVision 控制台能看到完整 `$MV,AIM,...#`。
- [ ] 若使用 UART，确认 COM 口、115200 波特率、TX/RX 交叉和 GND 共地。
- [ ] 明确 MaixVision 无线连接不是 COM 串口。
- [ ] `tune.py log` 能生成 JSONL；`tune.py analyze` 能输出十项指标。
- [ ] STM32ZET6 仅观察解析结果；MSPM0G3507 仅观察建议值，不连接执行机构。
