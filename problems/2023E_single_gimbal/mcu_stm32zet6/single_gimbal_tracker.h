#ifndef SINGLE_GIMBAL_TRACKER_H
#define SINGLE_GIMBAL_TRACKER_H

#include "gimbal_command.h"
#include "protocol_2023e_single.h"

typedef enum { SINGLE_IDLE, SINGLE_TRACKING, SINGLE_AIMED, SINGLE_LOST, SINGLE_ERROR } SingleTrackerState;

typedef struct {
    SingleTrackerState state;
    int valid;
    int32_t pan_command, tilt_command;
    GimbalCommandState command;
} SingleTracker;

void single_tracker_init(SingleTracker *tracker);
void single_tracker_update(SingleTracker *tracker, const SinglePacket *packet,
                           const GimbalCommandConfig *config);
const char *single_tracker_state_name(SingleTrackerState state);

#endif
