#include "gimbal_command.h"

#include <stdlib.h>
#include <string.h>

static int32_t clamp(int32_t value, int32_t limit) {
    if (value > limit) return limit;
    if (value < -limit) return -limit;
    return value;
}

static int32_t slew(int32_t target, int32_t previous, int32_t rate) {
    int32_t delta = target - previous;
    if (rate <= 0) return target;
    if (delta > rate) return previous + rate;
    if (delta < -rate) return previous - rate;
    return target;
}

void gimbal_command_reset(GimbalCommandState *state) { memset(state, 0, sizeof(*state)); }

void gimbal_command_update(GimbalCommandState *state, const GimbalCommandConfig *config,
                           int valid, int32_t error_x, int32_t error_y,
                           int32_t *pan, int32_t *tilt) {
    int32_t target_pan = 0, target_tilt = 0;
    if (valid) {
        if (abs(error_x) > config->deadband_px)
            target_pan = (int32_t)(config->kp_x * error_x + config->kd_x * (error_x - state->previous_error_x));
        if (abs(error_y) > config->deadband_px)
            target_tilt = (int32_t)(config->kp_y * error_y + config->kd_y * (error_y - state->previous_error_y));
        target_pan = clamp(target_pan, config->command_limit);
        target_tilt = clamp(target_tilt, config->command_limit);
        state->pan = slew(target_pan, state->pan, config->slew_rate_limit);
        state->tilt = slew(target_tilt, state->tilt, config->slew_rate_limit);
    } else {
        /* Invalid vision is an immediate safety stop; slew limiting is bypassed. */
        state->pan = 0;
        state->tilt = 0;
    }
    state->previous_error_x = error_x;
    state->previous_error_y = error_y;
    *pan = state->pan;
    *tilt = state->tilt;
}
