# DCC-100 / 云台资料扫描与迁移记录

## 扫描结论

2026-07-12 已扫描并比对以下资料：

- `【云台】08_按键上下左右遥控开环电机/yuntai_8_yao2kong4kai1huan2`
- `15_step_motor_mspm0g3507_已完成_可以控制速度和角度/15_step_motor_2`
- `14_step_motor_mspm0g3507_已完成_可以转起来/14_step_motor_1`
- `tripod__head-master`（STM32，仅参考控制思路）
- `DCC-100v1v2说明书.pdf` 与 `DCC-100v3说明书-2026-05-24.pdf`

迁移基线采用 08 工程的 `step_motor.c/.h` 和 `empty.syscfg`。15 工程用于交叉确认速度、角度和定时器换算，14 工程只用于确认基础脉冲接口。适配层保留下列接口：

```c
void step_motor_init(void);
void step_motor_dir_set(uint8_t direction, uint8_t stepper_id);
void step_motor_start(uint8_t stepper_id);
void step_motor_stop(uint8_t stepper_id);
void step_set_speed(uint8_t speed, uint8_t stepper_id);
void step_motor_set_angle(float angle, uint8_t stepper_id);
```

原实现中 `step_motor_stop()` 已存在而头文件漏声明；迁移副本只补充声明，不重写停止逻辑。

## 已确认硬件与单位

- 电机 1：PA28 PWM（TIMA1）、PA31 DIR、PB24 DCY、PB20 SLP、PA7 RST。
- 电机 2：PA12 PWM（TIMG0）、PA13 DIR、PA14 DCY、PA15 SLP、PA16 RST。
- 两路 PWM 的 SysConfig 时钟均为 5 MHz，占空比为 50%。
- 默认 1/32 细分时，一个脉冲为 0.05625°；角速度单位为 °/s，频率为 `speed / 0.05625` Hz。
- `step_motor_set_angle(float angle, ...)` 的角度单位为度，内部换算为 `angle / 0.05625` 个脉冲。
- DCC-100 v3：电源 11–26V；逻辑高 3.3V、低 0V；两路共地。
- PWM：每脉冲一个微步；DIR：高低电平控制方向；DCY：高电平大扭矩、低电平小扭矩；SLP/RST：高电平工作。
- v1/v2 的 MODE 焊盘可选 1、1/2、1/4、1/8、1/16、1/32 细分；源工程的 0.05625° 只在 1/32 细分成立。

## 迁移顺序

1. 以“08_按键上下左右遥控开环电机”为双路定时器和按键控制主来源。
2. 以“15_step_motor”补充速度、角度和 PWM 频率语义。
3. 以“14_step_motor”仅核对基础步进脉冲。
4. `tripod__head-master` 只参考上层控制思想，禁止移入 STM32 HAL。

## 待核实硬件映射

| 项目 | 当前状态 |
|---|---|
| 电机 1 / 电机 2 对应水平或俯仰轴 | 08 工程按键 1/4 控制电机 1、2/3 控制电机 2；机械轴仍需现场确认 |
| 方向反转 | 由 `GimbalConfig` 配置，现场点动确认 |
| 速度单位 | °/s，原接口受 `uint8_t` 限制为 0–255 |
| 角度单位 | 度，0.05625°/脉冲（仅 1/32 细分） |
| `step_motor_stop` | 若源 `.c` 已实现但 `.h` 未声明，只补声明 |

接线已经由 08 工程 `step_motor.h` 和生成的 `ti_msp_dl_config.h` 交叉确认：

```text
第一路：PA28 PWM, PA31 DIR, PB24 DCY, PB20 SLP, PA7 RST
第二路：PA12 PWM, PA13 DIR, PA14 DCY, PA15 SLP, PA16 RST
```

## 已知风险

- `period >= 800` 的硬下限限制最高脉冲频率；5 MHz 时约为 6250 Hz，即约 351.6°/s，接口自身又限制为 255°/s。
- `step_motor_set_angle(0)` 会启动后在首次 LOAD 中断停止，控制层不应把 0° 当连续运动命令。
- 源驱动用全局剩余步数且没有并发保护；更新同一路角度命令时可能覆盖未完成动作。
- 微步 MODE 或电机本体步距改变后，0.05625° 常量必须同步校准。
- 未完成机械零位、软限位和方向标定前，不得带负载高速运行。
- 接入时只允许替换/补入 DCC 源文件与 `ti_msp_dl_config.*` 配置；解析器和控制器不得直接操作 GPIO/Timer。
