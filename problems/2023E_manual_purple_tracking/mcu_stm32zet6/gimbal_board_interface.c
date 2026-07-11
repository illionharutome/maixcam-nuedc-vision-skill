#include "gimbal_board_interface.h"
#include <stdio.h>
int gimbal_board_format_dry_run(char*out,size_t size,int pan,int tilt,const char*mode){int n;if(!out||!size||!mode)return 0;n=snprintf(out,size,"$GM,CMD,PAN=%d,TILT=%d,MODE=%s#",pan,tilt,mode);return n>0&&(size_t)n<size;}
