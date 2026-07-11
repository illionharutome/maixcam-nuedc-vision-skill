#ifndef PROTOCOL_2023E_SINGLE_H
#define PROTOCOL_2023E_SINGLE_H

#include <stddef.h>
#include <stdint.h>

#define SINGLE_FRAME_MAX 192u
#define SINGLE_TEXT_MAX 24u

typedef struct {
    uint8_t ok;
    int32_t spot_cx, spot_cy;
    int32_t target_cx, target_cy;
    int32_t error_x, error_y;
    char path_id[SINGLE_TEXT_MAX];
    int32_t step_id;
    float score, fps;
    char status[SINGLE_TEXT_MAX];
} SinglePacket;

typedef enum {
    SINGLE_STREAM_NONE = 0,
    SINGLE_STREAM_PACKET = 1,
    SINGLE_STREAM_REJECTED = -1
} SingleStreamResult;

typedef struct {
    char buffer[SINGLE_FRAME_MAX];
    size_t length;
    uint8_t collecting;
    uint8_t overflow;
} SingleStreamParser;

void single_stream_init(SingleStreamParser *parser);
SingleStreamResult single_stream_push(SingleStreamParser *parser, char byte, SinglePacket *out);

/* WARNING: this function modifies frame in-place. Pass a writable char array. */
int single_parse_frame(char *frame, SinglePacket *out);

#endif
