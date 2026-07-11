#include "single_gimbal_tracker.h"

#include <string.h>

void single_tracker_init(SingleTracker *tracker) {
    memset(tracker, 0, sizeof(*tracker));
    tracker->state = SINGLE_IDLE;
}

void single_tracker_update(SingleTracker *tracker, const SinglePacket *packet,
                           const GimbalCommandConfig *config) {
    int safe = packet->ok && strcmp(packet->status, "NO_SPOT") != 0 &&
               strcmp(packet->status, "LOST") != 0 && strcmp(packet->status, "ERROR") != 0;
    tracker->valid = safe;
    if (!safe) {
        tracker->state = strcmp(packet->status, "ERROR") == 0 ? SINGLE_ERROR : SINGLE_LOST;
    } else if (strcmp(packet->status, "AIMED") == 0) {
        tracker->state = SINGLE_AIMED;
    } else {
        tracker->state = SINGLE_TRACKING;
    }
    gimbal_command_update(&tracker->command, config, safe, packet->error_x, packet->error_y,
                          &tracker->pan_command, &tracker->tilt_command);
}

const char *single_tracker_state_name(SingleTrackerState state) {
    static const char *names[] = {"IDLE", "TRACKING", "AIMED", "LOST", "ERROR"};
    return (state >= SINGLE_IDLE && state <= SINGLE_ERROR) ? names[state] : "ERROR";
}
