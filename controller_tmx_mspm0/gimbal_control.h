#ifndef GIMBAL_CONTROL_H
#define GIMBAL_CONTROL_H

#include <stdint.h>
#include "vision_command.h"

typedef struct {
    uint16_t deadband_px;
    uint8_t min_speed_dps;
    uint8_t max_speed_dps;
    uint8_t confidence_min;
    uint8_t lost_frame_limit;
    uint8_t invert_pan;
    uint8_t invert_tilt;
} GimbalConfig_t;

void gimbal_control_init(const GimbalConfig_t *config);
void gimbal_control_update(const VisionCommand_t *command);
void gimbal_control_on_frame_timeout(void);

#endif

