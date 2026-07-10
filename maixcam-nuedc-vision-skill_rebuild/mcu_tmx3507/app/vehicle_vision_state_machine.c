#include "vehicle_vision_state_machine.h"

#include <stddef.h>

void vehicle_vision_state_init(VehicleVisionState *state)
{
    if (state != NULL) {
        state->state = VEHICLE_VISION_DISABLED;
        state->manual_stop = 1U;
        state->execution_enabled = 0U;
        state->last_result_ms = 0U;
    }
}
