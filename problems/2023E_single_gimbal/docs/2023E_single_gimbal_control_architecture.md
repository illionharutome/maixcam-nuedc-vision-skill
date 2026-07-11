# 控制架构

```text
MaixCAM image -> local spot/path modules -> $MV,SINGLE text
                                              |
                                              v
ZET6 stream parser -> safety state -> P/PD suggestion -> $DBG,SINGLE
                                              |
                                      no PWM / no actuator
```

MaixCAM 只产生图像坐标误差，不产生舵机角度。ZET6 当前只计算 `pan_command/tilt_command` 毫单位建议值；无效检测立即归零。真正接入执行机构前必须单独审查机械限位、方向、增益、供电、急停和遮挡。

这是单板集成 subset。题面完整合规架构必须把红色目标和绿色追踪拆为两套不通信的独立系统；当前单云台不能满足该条件。
