#ifndef VEHICLE_VISION_STATE_MACHINE_H
#define VEHICLE_VISION_STATE_MACHINE_H

#include <stdint.h>

typedef enum {
    VEHICLE_VISION_DISABLED = 0,
    VEHICLE_VISION_NO_TARGET,
    VEHICLE_VISION_TRACKING,
    VEHICLE_VISION_LOST,
    VEHICLE_VISION_ERROR
} VehicleVisionStateId;

typedef struct {
    VehicleVisionStateId state;
    uint8_t manual_stop;
    uint8_t execution_enabled;
    uint32_t last_result_ms;
} VehicleVisionState;

/* Placeholder only: initialization keeps execution disabled. */
void vehicle_vision_state_init(VehicleVisionState *state);

#endif
