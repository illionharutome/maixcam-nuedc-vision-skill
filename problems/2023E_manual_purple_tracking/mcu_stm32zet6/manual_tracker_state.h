#ifndef MANUAL_TRACKER_STATE_H
#define MANUAL_TRACKER_STATE_H
#include "protocol_track1.h"
#include "tracker_command.h"
typedef enum {MANUAL_IDLE,MANUAL_TRACKING,MANUAL_AIMED,MANUAL_LOST,MANUAL_ERROR} ManualState;
typedef struct {ManualState state;int valid;int32_t pan_command,tilt_command;TrackerCommandState command;} ManualTracker;
void manual_tracker_init(ManualTracker*t);void manual_tracker_update(ManualTracker*t,const Track1Packet*p,const TrackerCommandConfig*c);const char*manual_state_name(ManualState s);
#endif
