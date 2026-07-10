#ifndef TARGET_AIMING_STATE_MACHINE_H
#define TARGET_AIMING_STATE_MACHINE_H

#include <stdint.h>

#include "../../mcu_common/mv_result.h"

typedef enum {
    TARGET_AIM_DISABLED = 0,
    TARGET_AIM_NO_SPOT,
    TARGET_AIM_TRACKING,
    TARGET_AIM_LOCKED
} TargetAimingState;

typedef struct {
    float pan_gain;
    float tilt_gain;
    float command_limit;
    int32_t dead_zone_x;
    int32_t dead_zone_y;
} TargetAimingConfig;

typedef struct {
    TargetAimingState state;
    float pan_command;
    float tilt_command;
    uint8_t valid;
} TargetAimingCommand;

void target_aiming_update(const Aim_Result *aim,
                          const TargetAimingConfig *config,
                          TargetAimingCommand *command);

#endif
