#ifndef GIMBAL_COMMAND_H
#define GIMBAL_COMMAND_H

#include <stdint.h>

typedef struct {
    float kp_x, kp_y, kd_x, kd_y;
    int32_t deadband_px;
    int32_t command_limit;
    int32_t slew_rate_limit;
} GimbalCommandConfig;

typedef struct {
    int32_t pan, tilt;
    int32_t previous_error_x, previous_error_y;
} GimbalCommandState;

void gimbal_command_reset(GimbalCommandState *state);
void gimbal_command_update(GimbalCommandState *state, const GimbalCommandConfig *config,
                           int valid, int32_t error_x, int32_t error_y,
                           int32_t *pan, int32_t *tilt);

#endif
