#ifndef MOTOR_OUTPUT_STUB_H
#define MOTOR_OUTPUT_STUB_H

#include "c8t6_config.h"

/* Stub: never writes GPIO, TIM, or PWM when C8T6_ENABLE_MOTOR_OUTPUT=0. */
void motor_output_init(void);
void motor_output_apply(int pan_milli, int tilt_milli);

extern volatile int g_motor_latest_pan;
extern volatile int g_motor_latest_tilt;
extern volatile int g_motor_apply_count;

#endif
