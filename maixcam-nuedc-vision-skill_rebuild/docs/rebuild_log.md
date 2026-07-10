# 重建记录

## 原因

旧 `maixcam-nuedc-vision-skill` 主仓库丢失，只保留了在 MaixVision 上验证过的 `maixcam_run_2025E` 精简目录。本仓库在不修改该目录的前提下重建，并加入阶段性 Git 提交。

## 从已验证目录复制

复制了 `apps_atomic/`、`apps_replay/`、`comm/uart_packet.py`、`config/`、`core/`、`vision/`、`ui/` 和 `main.py`。随后只在新仓库调整默认入口、320×240 配置、UART/print 输出和安全 replay 入口。

## 已验证功能

- MaixCAM/MaixVision 侧已有红点替代物识别和单文件 AIM 画面验证背景。
- 重建后 Python 协议、误差方向、调参统计测试通过。
- C 字节流解析器、MSPM0 建议状态机和两个 MCU 示例通过主机 `-Werror` 编译。

## 仅占位

YOLO 模型、数据集、小车视觉任务、机械臂视觉任务和 TASK/ARM 协议都只是接口或文档；没有训练、部署、执行控制或完整解析。

## Git 阶段

1. `7fa69a1` — backup before maixcam skill rebuild
2. `ab08460` — rebuild skeleton
3. `de5358b` — rebuild maixcam 2025E vision loop
4. `57d99cd` — rebuild mv protocol and tuning
5. `a74d5fe` — rebuild stm32 and tmx templates
6. `e63bb90` — rebuild yolo vehicle arm placeholders
7. `rebuild docs and safety notes` — 本文档所在阶段；准确哈希以 `git log` 为准

备份分支 `backup-before-maixcam-skill-rebuild` 指向重建前提交。

## 安全边界

当前只允许红色 LED、屏幕/纸面红点等替代测试；不启用 405nm，不使用真实激光，不连接云台、舵机、小车或机械臂执行机构。MaixCAM 永远只输出视觉结果。
