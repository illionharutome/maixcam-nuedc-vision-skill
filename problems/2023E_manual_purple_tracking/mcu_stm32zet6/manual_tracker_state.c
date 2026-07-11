#include "manual_tracker_state.h"
#include <string.h>
void manual_tracker_init(ManualTracker*t){memset(t,0,sizeof(*t));t->state=MANUAL_IDLE;}
void manual_tracker_update(ManualTracker*t,const Track1Packet*p,const TrackerCommandConfig*c){int safe=p->ok&&strcmp(p->status,"NO_TARGET")&&strcmp(p->status,"LOST")&&strcmp(p->status,"ERROR");t->valid=safe;if(!safe)t->state=!strcmp(p->status,"ERROR")?MANUAL_ERROR:MANUAL_LOST;else t->state=!strcmp(p->status,"AIMED")?MANUAL_AIMED:MANUAL_TRACKING;tracker_command_update(&t->command,c,safe,p->error_x,p->error_y,&t->pan_command,&t->tilt_command);}
const char*manual_state_name(ManualState s){static const char*n[]={"IDLE","TRACKING","AIMED","LOST","ERROR"};return s>=MANUAL_IDLE&&s<=MANUAL_ERROR?n[s]:"ERROR";}
