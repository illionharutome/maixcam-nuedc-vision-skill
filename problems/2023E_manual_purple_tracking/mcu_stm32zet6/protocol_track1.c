#include "protocol_track1.h"
#include <stdlib.h>
#include <string.h>
#define FIELDS 12u
static int pi(const char*s,int32_t*out){char*e;long v=strtol(s,&e,10);if(s==e||*e)return 0;*out=(int32_t)v;return 1;}
static int pf(const char*s,float*out){char*e;double v=strtod(s,&e);if(s==e||*e)return 0;*out=(float)v;return 1;}
int track1_parse_frame(char *frame, Track1Packet *out){char*f[FIELDS],*p=frame;size_t n=0;int32_t ok;
 if(!frame||!out||strncmp(frame,"$MV,TRACK1,",11))return 0;
 while(n<FIELDS){f[n++]=p;p=strchr(p,',');if(!p)break;*p++='\0';} if(n!=FIELDS||p)return 0;
 p=strchr(f[11],'#');if(!p||p[1])return 0;*p='\0';memset(out,0,sizeof(*out));
 if(strcmp(f[0],"$MV")||strcmp(f[1],"TRACK1")||!pi(f[2],&ok)||(ok!=0&&ok!=1))return 0;
 out->ok=(uint8_t)ok;
 if(strlen(f[11])==0||strlen(f[11])>=TRACK1_TEXT_MAX)return 0;
 strcpy(out->status,f[11]);
 return pi(f[3],&out->target_cx)&&pi(f[4],&out->target_cy)&&pi(f[5],&out->aim_cx)&&pi(f[6],&out->aim_cy)&&pi(f[7],&out->error_x)&&pi(f[8],&out->error_y)&&pf(f[9],&out->score)&&pf(f[10],&out->fps);}
void track1_stream_init(Track1Stream*s){memset(s,0,sizeof(*s));}
Track1StreamResult track1_stream_push(Track1Stream*s,char b,Track1Packet*out){int ok;if(b=='$'){s->collecting=1;s->overflow=0;s->length=0;}if(!s->collecting)return TRACK1_NONE;if(!s->overflow){if(s->length+1<TRACK1_FRAME_MAX)s->buffer[s->length++]=b;else s->overflow=1;}if(b!='#')return TRACK1_NONE;s->collecting=0;if(s->overflow){s->length=0;return TRACK1_REJECTED;}s->buffer[s->length]='\0';ok=track1_parse_frame(s->buffer,out);s->length=0;return ok?TRACK1_PACKET:TRACK1_REJECTED;}
