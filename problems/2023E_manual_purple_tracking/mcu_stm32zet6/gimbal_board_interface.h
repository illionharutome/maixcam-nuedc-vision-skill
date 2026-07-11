#ifndef GIMBAL_BOARD_INTERFACE_H
#define GIMBAL_BOARD_INTERFACE_H
#include <stddef.h>
int gimbal_board_format_dry_run(char*out,size_t size,int pan,int tilt,const char*mode);
#endif
