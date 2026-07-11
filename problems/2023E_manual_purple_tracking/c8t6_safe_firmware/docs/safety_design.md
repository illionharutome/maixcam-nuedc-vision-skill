# C8T6 safety design

## 核心原则

所有电机输出默认禁能。任何执行输出必须在以下所有条件满足后
经过单独审批才能打开：

1. UART RX 物理口确认
2. 上电禁能实板验证
3. 不接电机空板 UART ACK 测试通过
4. 空载低速电机测试通过
5. 限位/急停硬件设计审查通过

## 状态机
```
上电 -> DISABLED -> IDLE -> TRACK/HOLD/STOP/ERROR
       (无输出)
```

- STOP 优先级最高
- 无命令超时后自动进入 STOP
- 非法命令进入 ERROR 或返回 ERR
- 所有错误状态下电机输出为零

## 当前默认配置
- C8T6_ENABLE_MOTOR_OUTPUT = 0
- C8T6_ENABLE_TIM_PULSE_OUTPUT = 0
- motor_output_apply() 只更新内存变量，不写 GPIO/TIM
