#ifndef ARM_VISION_STATE_MACHINE_H
#define ARM_VISION_STATE_MACHINE_H

#include <stdint.h>

typedef enum {
    ARM_VISION_DISABLED = 0,
    ARM_VISION_NO_OBJECT,
    ARM_VISION_TRACKING,
    ARM_VISION_READY_TO_GRASP,
    ARM_VISION_LOST,
    ARM_VISION_ERROR
} ArmVisionStateId;

typedef struct {
    ArmVisionStateId state;
    uint8_t manual_stop;
    uint8_t execution_enabled;
    uint32_t last_result_ms;
} ArmVisionState;

/* Placeholder only: initialization keeps execution disabled. */
void arm_vision_state_init(ArmVisionState *state);

#endif
