# 2025E 第一阶段视觉说明

第一版只做实时红点或低风险替代光点检测，靶心默认取 320×240 画面中心，输出：

```text
aim_error_x = spot_cx - target_cx
aim_error_y = spot_cy - target_cy
```

误差只表示图像空间方向和像素量，不是舵机角度、PWM 或 PID 输出。传统 LAB 阈值与几何方法是当前主线，YOLO 不是 2025E 第一阶段必需项。

旧残迹识别和 405nm 是第二阶段问题。405nm 在 MaixCAM 传感器上的颜色响应不能凭颜色名称推断，必须现场采集图像并实测 LAB 阈值。当前 profile 保持禁用。

后续调试应保存代表不同光照、距离、背景和曝光的测试图像，并用 `tune.py` 记录 JSONL，避免只凭单次画面调整参数。

## 阶段 2：主控侧空跑验证

视觉原子测试和 2025E replay 通过后，不再改变 MaixCAM 视觉逻辑。使用 PC 模拟 `$MV,AIM` 帧验证共享 C 解析器、图像误差字段和天猛星目标建议状态机。

空跑阶段只观察 `pan_command / tilt_command` 的符号、限幅与安全归零：`AIMING` 根据图像误差产生建议，`AIMED` 接近零，`NO_SPOT / LOST / ERROR` 必须无效并归零。通过后下一步仅允许 STM32ZET6 debug bridge 或 MSPM0G3507 实板解析，不允许连接真实执行机构。
