#include "tracker_command.h"
#include <stdlib.h>
#include <string.h>
static int32_t clamp(int32_t v,int32_t l){return v>l?l:(v<-l?-l:v);}static int32_t slew(int32_t t,int32_t p,int32_t r){int32_t d=t-p;if(r<=0)return t;return d>r?p+r:(d<-r?p-r:t);}
void tracker_command_reset(TrackerCommandState*s){memset(s,0,sizeof(*s));}
void tracker_command_update(TrackerCommandState*s,const TrackerCommandConfig*c,int valid,int32_t ex,int32_t ey,int32_t*pan,int32_t*tilt){int32_t p=0,t=0;if(valid){if(abs(ex)>c->deadband_px)p=(int32_t)(c->sign_x*(c->kp_x*ex+c->kd_x*(ex-s->previous_x)));if(abs(ey)>c->deadband_px)t=(int32_t)(c->sign_y*(c->kp_y*ey+c->kd_y*(ey-s->previous_y)));s->pan=slew(clamp(p,c->command_limit),s->pan,c->slew_rate_limit);s->tilt=slew(clamp(t,c->command_limit),s->tilt,c->slew_rate_limit);}else{s->pan=0;s->tilt=0;}s->previous_x=ex;s->previous_y=ey;*pan=s->pan;*tilt=s->tilt;}
