#ifndef STEP_MOTOR_H
#define STEP_MOTOR_H

#include <stdint.h>
#include "ti_msp_dl_config.h"

#define DCC_STEP_DEGREES (0.05625f)

void step_motor_init(void);
void step_motor_dir_set(uint8_t direction, uint8_t stepper_id);
void step_motor_start(uint8_t stepper_id);
void step_motor_stop(uint8_t stepper_id);
void step_set_speed(uint8_t speed, uint8_t stepper_id);
void step_motor_set_angle(float angle, uint8_t stepper_id);

#endif

