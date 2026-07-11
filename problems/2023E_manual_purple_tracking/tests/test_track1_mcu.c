#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../mcu_stm32zet6/protocol_track1.h"
#include "../mcu_stm32zet6/manual_tracker_state.h"
#include "../mcu_stm32zet6/gimbal_board_interface.h"
static Track1Packet feed(Track1Stream*s,const char*t,int*n){Track1Packet p={0};size_t i;for(i=0;t[i];i++)if(track1_stream_push(s,t[i],&p)==TRACK1_PACKET)(*n)++;return p;}
int main(void){Track1Stream s;Track1Packet p;ManualTracker t;TrackerCommandConfig c={10,10,0,0,3,1000,1000,1,1};char gm[80];int n=0;size_t i;
 track1_stream_init(&s);p=feed(&s,"$MV,TRACK1,1,140,110,160,120,-20,-10,0.90,30.0,TRACKING#",&n);assert(n==1&&p.error_x==-20&&p.error_y==-10);
 track1_stream_init(&s);n=0;p=feed(&s,"$MV,TRACK1,1,140,110,160",&n);assert(n==0);p=feed(&s,",120,-20,-10,0.90,30.0,TRACKING#$MV,TRACK1,0,0,0,160,120,0,0,0,30,NO_TARGET#",&n);assert(n==2);
 manual_tracker_init(&t);manual_tracker_update(&t,&p,&c);assert(!t.valid&&t.pan_command==0&&t.tilt_command==0);
 assert(gimbal_board_build_command(-300,220,"TRACK",gm,(int)sizeof(gm)));assert(!strcmp(gm,"$GM,CMD,PAN=-300,TILT=220,MODE=TRACK#"));
 assert(!gimbal_board_build_command(1,2,"BAD,MODE",gm,(int)sizeof(gm)));
 track1_stream_init(&s);track1_stream_push(&s,'$',&p);for(i=0;i<TRACK1_FRAME_MAX+5;i++)track1_stream_push(&s,'X',&p);assert(track1_stream_push(&s,'#',&p)==TRACK1_REJECTED);puts("TRACK1 MCU tests passed");return 0;}
