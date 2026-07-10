#ifndef MV_RESULT_H
#define MV_RESULT_H

#include <stdint.h>

#define MV_MODE_LENGTH 8U
#define MV_STATUS_LENGTH 24U

typedef struct {
    char mode[MV_MODE_LENGTH];
    uint8_t ok;
    int32_t target_cx;
    int32_t target_cy;
    int32_t spot_cx;
    int32_t spot_cy;
    int32_t aim_error_x;
    int32_t aim_error_y;
    float score;
    float fps;
    char status[MV_STATUS_LENGTH];
} Aim_Result;

#endif
