#ifndef VISION_COMMAND_H
#define VISION_COMMAND_H

#include <stdint.h>

typedef enum {
    VISION_NO_TARGET = 0,
    VISION_TRACKING  = 1,
    VISION_LOCKED    = 2,
    VISION_LOST      = 3
} VisionState_t;

typedef struct {
    VisionState_t state;
    int16_t dx;
    int16_t dy;
    uint8_t confidence;
    uint16_t dist_mm;
} VisionCommand_t;

#endif

