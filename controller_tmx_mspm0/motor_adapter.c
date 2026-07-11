#include "motor_adapter.h"
#include "step_motor.h"

static uint8_t id_for_axis(MotorAxis_t axis) { return axis == MOTOR_PAN ? 1U : 2U; }

void motor_adapter_init(void) { step_motor_init(); }

void motor_adapter_drive(MotorAxis_t axis, int8_t direction, uint8_t speed_dps)
{
    uint8_t id = id_for_axis(axis);
    if (speed_dps == 0U) { step_motor_stop(id); return; }
    step_motor_dir_set(direction >= 0 ? 1U : 0U, id);
    step_set_speed(speed_dps, id);
    step_motor_start(id);
}

void motor_adapter_move(MotorAxis_t axis, int8_t direction, uint8_t speed_dps, float angle_deg)
{
    uint8_t id = id_for_axis(axis);
    if (angle_deg <= 0.0f || speed_dps == 0U) { step_motor_stop(id); return; }
    step_motor_dir_set(direction >= 0 ? 1U : 0U, id);
    step_set_speed(speed_dps, id);
    step_motor_set_angle(angle_deg, id);
}

void motor_adapter_stop(MotorAxis_t axis) { step_motor_stop(id_for_axis(axis)); }
void motor_adapter_stop_all(void) { step_motor_stop(1U); step_motor_stop(2U); }

