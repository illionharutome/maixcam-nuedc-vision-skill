# Control architecture

```text
MaixCAM: purple blob + manual aim -> TRACK1
STM32ZET6: parser -> IDLE/TRACKING/AIMED/LOST/ERROR -> abstract command + DBG
gimbal interface: dry-run string only
PC/API: log summary and human-reviewed suggestions only
```

摄像头和红色光点随云台一起运动；视觉不追踪红点，而是让紫色目标趋近标定准星。`NO_TARGET/LOST/ERROR` 必须立即归零。真实接入前需验证轴方向、机械限位、回零、供电、急停和底层控制板职责。
