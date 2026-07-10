#include "target_aiming_state_machine.h"

#include <stdlib.h>
#include <string.h>

static float clamp(float value, float limit)
{
    if (value > limit) {
        return limit;
    }
    if (value < -limit) {
        return -limit;
    }
    return value;
}

void target_aiming_update(const Aim_Result *aim,
                          const TargetAimingConfig *config,
                          TargetAimingCommand *command)
{
    if (command == NULL) {
        return;
    }
    command->state = TARGET_AIM_DISABLED;
    command->pan_command = 0.0f;
    command->tilt_command = 0.0f;
    command->valid = 0U;
    if ((aim == NULL) || (config == NULL) ||
        (strcmp(aim->mode, "AIM") != 0) || (aim->ok == 0U)) {
        command->state = TARGET_AIM_NO_SPOT;
        return;
    }

    command->valid = 1U;
    if (strcmp(aim->status, "AIMED") == 0) {
        command->state = TARGET_AIM_LOCKED;
        return;
    }
    command->state = TARGET_AIM_TRACKING;
    if (labs((long)aim->aim_error_x) > config->dead_zone_x) {
        command->pan_command = clamp(config->pan_gain * (float)aim->aim_error_x,
                                     config->command_limit);
    }
    if (labs((long)aim->aim_error_y) > config->dead_zone_y) {
        command->tilt_command = clamp(config->tilt_gain * (float)aim->aim_error_y,
                                      config->command_limit);
    }
}
