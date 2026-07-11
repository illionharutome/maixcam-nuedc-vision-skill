#ifndef TRACKER_COMMAND_H
#define TRACKER_COMMAND_H
#include <stdint.h>
typedef struct {float kp_x,kp_y,kd_x,kd_y;int32_t deadband_px,command_limit,slew_rate_limit;int8_t sign_x,sign_y;} TrackerCommandConfig;
typedef struct {int32_t pan,tilt,previous_x,previous_y;} TrackerCommandState;
void tracker_command_reset(TrackerCommandState*s);
void tracker_command_update(TrackerCommandState*s,const TrackerCommandConfig*c,int valid,int32_t ex,int32_t ey,int32_t*pan,int32_t*tilt);
#endif
