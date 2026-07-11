/* Migrated from the supplied 08 dual-axis MSPM0G3507 project. */
#include "step_motor.h"

static volatile uint32_t step_remain_1 = 0;
static volatile uint32_t step_remain_2 = 0;

void step_motor_init(void)
{
    DL_GPIO_setPins(STEP_MOTOR_RST2_PORT, STEP_MOTOR_RST2_PIN);
    DL_GPIO_setPins(STEP_MOTOR_SLP2_PORT, STEP_MOTOR_SLP2_PIN);
    DL_GPIO_setPins(STEP_MOTOR_DIR2_PORT, STEP_MOTOR_DIR2_PIN);
    DL_GPIO_setPins(STEP_MOTOR_DCY2_PORT, STEP_MOTOR_DCY2_PIN);
    NVIC_EnableIRQ(DCC_100_PWM2_INST_INT_IRQN);
    DL_GPIO_setPins(STEP_MOTOR_RST1_PORT, STEP_MOTOR_RST1_PIN);
    DL_GPIO_setPins(STEP_MOTOR_SLP1_PORT, STEP_MOTOR_SLP1_PIN);
    DL_GPIO_setPins(STEP_MOTOR_DIR1_PORT, STEP_MOTOR_DIR1_PIN);
    DL_GPIO_setPins(STEP_MOTOR_DCY1_PORT, STEP_MOTOR_DCY1_PIN);
    NVIC_EnableIRQ(DCC_100_PWM1_INST_INT_IRQN);
}

void step_motor_dir_set(uint8_t direction, uint8_t stepper_id)
{
    GPIO_Regs *port = (stepper_id == 1U) ? STEP_MOTOR_DIR1_PORT : STEP_MOTOR_DIR2_PORT;
    uint32_t pin = (stepper_id == 1U) ? STEP_MOTOR_DIR1_PIN : STEP_MOTOR_DIR2_PIN;
    if (stepper_id != 1U && stepper_id != 2U) return;
    if (direction == 0U) DL_GPIO_clearPins(port, pin); else DL_GPIO_setPins(port, pin);
}

void step_motor_start(uint8_t stepper_id)
{
    if (stepper_id == 1U) {
        NVIC_EnableIRQ(DCC_100_PWM1_INST_INT_IRQN);
        DL_Timer_startCounter(DCC_100_PWM1_INST);
    } else if (stepper_id == 2U) {
        NVIC_EnableIRQ(DCC_100_PWM2_INST_INT_IRQN);
        DL_Timer_startCounter(DCC_100_PWM2_INST);
    }
}

void step_motor_stop(uint8_t stepper_id)
{
    if (stepper_id == 1U) DL_Timer_stopCounter(DCC_100_PWM1_INST);
    else if (stepper_id == 2U) DL_Timer_stopCounter(DCC_100_PWM2_INST);
}

static uint32_t period_for_speed(uint8_t speed, uint32_t clock_hz)
{
    uint32_t frequency = (uint32_t)((float)speed / DCC_STEP_DEGREES);
    uint32_t period;
    if (frequency == 0U) frequency = 1U;
    period = clock_hz / frequency;
    if (period > 65535U) period = 65535U;
    if (period < 800U) period = 800U;
    return period;
}

void step_set_speed(uint8_t speed, uint8_t stepper_id)
{
    uint32_t period;
    if (stepper_id == 1U) {
        period = period_for_speed(speed, DCC_100_PWM1_INST_CLK_FREQ);
        DL_Timer_setLoadValue(DCC_100_PWM1_INST, period);
        DL_Timer_setCaptureCompareValue(DCC_100_PWM1_INST, period / 2U, GPIO_DCC_100_PWM1_C0_IDX);
    } else if (stepper_id == 2U) {
        period = period_for_speed(speed, DCC_100_PWM2_INST_CLK_FREQ);
        DL_Timer_setLoadValue(DCC_100_PWM2_INST, period);
        DL_Timer_setCaptureCompareValue(DCC_100_PWM2_INST, period / 2U, GPIO_DCC_100_PWM2_C0_IDX);
    }
}

void step_motor_set_angle(float angle, uint8_t stepper_id)
{
    uint32_t steps = angle > 0.0f ? (uint32_t)(angle / DCC_STEP_DEGREES) : 0U;
    if (stepper_id == 1U) step_remain_1 = steps;
    else if (stepper_id == 2U) step_remain_2 = steps;
    else return;
    step_motor_start(stepper_id);
}

void DCC_100_PWM1_INST_IRQHandler(void)
{
    if (DL_Timer_getPendingInterrupt(DCC_100_PWM1_INST) == DL_TIMER_IIDX_LOAD) {
        if (step_remain_1 == 0U) step_motor_stop(1U); else --step_remain_1;
    }
}

void DCC_100_PWM2_INST_IRQHandler(void)
{
    if (DL_Timer_getPendingInterrupt(DCC_100_PWM2_INST) == DL_TIMER_IIDX_LOAD) {
        if (step_remain_2 == 0U) step_motor_stop(2U); else --step_remain_2;
    }
}

