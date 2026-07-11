#ifndef GIMBAL_BOARD_INTERFACE_H
#define GIMBAL_BOARD_INTERFACE_H
#include <stddef.h>

/* Pure formatter only. This module has no UART, GPIO, PWM or motor output. */
int gimbal_board_build_command(int pan_milli,
                               int tilt_milli,
                               const char *mode,
                               char *out,
                               int out_size);

/* Backward-compatible wrapper used by the current ZET6 dry-run bridge. */
int gimbal_board_format_dry_run(char*out,size_t size,int pan,int tilt,const char*mode);
#endif
