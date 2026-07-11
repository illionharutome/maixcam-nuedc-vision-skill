# C8T6 bringup plan

## Gate 0: 资料审查（当前）
- [x] 原 C8T6 工程审查完成
- [x] 上电自动 30° 往返风险已确认
- [x] DCC-100 接口文档已审查
- [ ] C8T6 UART RX 物理引脚确认

## Gate 1: 上电禁能验证
- UART RX 接线完成
- 烧录本安全固件
- 不接 DCC-100/电机
- 确认上电后 motor_output_apply_count == 0

## Gate 2: UART ACK 空板测试
- 从 PC USB-TTL 发送 $GM,CMD
- C8T6 回传 $GM,ACK
- 确认 TRACK/STOP/AIMED 模式切换正确
- 确认超时进入 STOP

## Gate 3: 空载低速电机测试（需审批）
- 所有前置通过
- 单轴最低电流/速度
- 物理急停可用

## 不接
DCC-100 / 步进电机 / 舵机 / PWM / 激光 直到 Gate 3 审批通过。
