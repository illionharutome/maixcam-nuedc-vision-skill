#include "gimbal_board_interface.h"
#include <stdio.h>

static int valid_mode(const char *mode)
{
    const char *p;
    if ((mode == NULL) || (*mode == '\0')) return 0;
    for (p = mode; *p != '\0'; ++p) {
        if ((*p == ',') || (*p == '$') || (*p == '#') ||
            (*p == '\r') || (*p == '\n')) return 0;
    }
    return 1;
}

int gimbal_board_build_command(int pan_milli, int tilt_milli,
                               const char *mode, char *out, int out_size)
{
    int length;
    if ((out == NULL) || (out_size <= 0) || !valid_mode(mode)) return 0;
    length = snprintf(out, (size_t)out_size,
                      "$GM,CMD,PAN=%d,TILT=%d,MODE=%s#",
                      pan_milli, tilt_milli, mode);
    return (length > 0) && (length < out_size);
}

int gimbal_board_format_dry_run(char *out, size_t size, int pan, int tilt,
                                const char *mode)
{
    if (size > 0x7FFFFFFFUL) return 0;
    return gimbal_board_build_command(pan, tilt, mode, out, (int)size);
}
