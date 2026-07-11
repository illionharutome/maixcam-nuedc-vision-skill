# 2023E 单云台 replay 计划

当前只复现单云台可完成的运动路径和图像误差闭环：先 PC 仿真，再 MaixVision 安全可见光点检测，再 ZET6 文本解析空跑，最后才另行审查执行机构接入。

阶段顺序：

1. `CENTER` 固定目标点，确认 `EX = SPOT_CX - TARGET_CX`、`EY = SPOT_CY - TARGET_CY`。
2. `SCREEN_SQUARE` 使用手动标定四角。
3. `A4_RECT` 与 `A4_ROTATED_RECT` 使用手动四角，自动视觉后置。
4. 收集误差、抖动、饱和与收敛时间日志。
5. ZET6 仅输出 `$DBG,SINGLE` 建议值，不接 PWM/云台。

本阶段只使用一个摄像头加一个低功率可见替代光点；405nm 禁用。完整 2023E 的红、绿独立双系统不在本目录当前能力范围内。
