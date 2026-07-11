# C8T6 safe firmware scaffold

这是安全固件框架，不是可直接接电机运行的固件。所有电机输出默认禁能。

原 C8T6 工程（`DCC-100-stm32f103c8t6/`）存在上电自动执行两轴 30 度往返的风险，**禁止直接烧录后接电机**。本目录从头构建安全固件，禁止复用原工程的危险 `main.c`。

## 结构

```
c8t6_safe_firmware/
  Core/Inc/   c8t6_config.h, gm_protocol.h, gimbal_safety_state.h, motor_output_stub.h
  Core/Src/   gm_protocol.c, gimbal_safety_state.c, motor_output_stub.c, main_skeleton.c
  docs/       safety_design.md, protocol_gm_cmd.md, bringup_plan.md
  tests/      test_gm_protocol.c, test_gimbal_safety_state.c
```

## 默认安全状态

| 宏 | 值 | 含义 |
|---|---|---|
| C8T6_ENABLE_MOTOR_OUTPUT | 0 | 不写 GPIO/不启动 TIM |
| C8T6_ENABLE_TIM_PULSE_OUTPUT | 0 | 不产生步进脉冲 |
| C8T6_ENABLE_UART_ACK | 1 | 允许 ACK/ERR 回包（字符串） |

## 不接

- DCC-100
- 步进电机
- 云台载荷
- 舵机 / PWM / 激光

## 后续审批门禁

1. C8T6 UART RX 物理口确认
2. 上电禁能实板验证
3. 不接电机空板 UART ACK 测试
4. 空载低速电机测试（需单独审查）
5. 限位/急停硬件设计审查
