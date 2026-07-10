#include "arm_vision_state_machine.h"

#include <stddef.h>

void arm_vision_state_init(ArmVisionState *state)
{
    if (state != NULL) {
        state->state = ARM_VISION_DISABLED;
        state->manual_stop = 1U;
        state->execution_enabled = 0U;
        state->last_result_ms = 0U;
    }
}
