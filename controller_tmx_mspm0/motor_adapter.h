#ifndef MOTOR_ADAPTER_H
#define MOTOR_ADAPTER_H

#include <stdint.h>

typedef enum { MOTOR_PAN = 0, MOTOR_TILT = 1 } MotorAxis_t;

void motor_adapter_init(void);
void motor_adapter_drive(MotorAxis_t axis, int8_t direction, uint8_t speed_dps);
void motor_adapter_move(MotorAxis_t axis, int8_t direction, uint8_t speed_dps, float angle_deg);
void motor_adapter_stop(MotorAxis_t axis);
void motor_adapter_stop_all(void);

#endif
