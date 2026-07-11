# TRACK1 dry-run 验证报告

本报告只记录已经确认的结论与复现命令，不包含串口临时日志或大文件。

## 已通过

1. MaixVision `2023E_manual_purple_tracking` 离线视觉测试通过，紫色目标可输出完整 `$MV,TRACK1`。
2. 目标位于准星左、右、上、下时，`EX = TARGET_CX - AIM_CX`、`EY = TARGET_CY - AIM_CY` 四方向验证通过。
3. `simulate_manual_tracking.py` PC 仿真通过。
4. `tune_manual_tracking.py` 本地日志分析通过。
5. STM32ZET6 已完成 Build、烧录，原 `$MV,AIM` 回归自动验证 PASS。
6. STM32ZET6 `$MV,TRACK1` dry-run 四帧自动验证 PASS，包括左上、右下、NO_TARGET 和 AIMED。

## 复现命令

```powershell
python problems\2023E_manual_purple_tracking\scripts\simulate_manual_tracking.py --no-plot
python problems\2023E_manual_purple_tracking\scripts\tune_manual_tracking.py --file problems\2023E_manual_purple_tracking\logs\manual_tracking_sim.jsonl
python scripts\stm32_bridge_auto_check.py --port COM5
python problems\2023E_manual_purple_tracking\scripts\stm32_track1_auto_check.py --port COM5
```

COM 号按实机修改。

## 当前安全状态

当前仍未连接 C8T6、DCC-100、电机、PWM 或真实光源，未向 C8T6 发送 `$GM,CMD`。链路终止于 ZET6 `$DBG,AIM/$DBG,TRACK1` 和内存中的 dry-run 字符串，安全状态仍为 dry-run。
