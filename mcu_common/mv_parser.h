#ifndef MV_PARSER_H
#define MV_PARSER_H

#include <stddef.h>
#include <stdint.h>

#include "mv_protocol.h"
#include "mv_result.h"

typedef enum {
    MV_PARSE_NONE = 0,
    MV_PARSE_AIM_READY = 1,
    MV_PARSE_INVALID = -1,
    MV_PARSE_OVERFLOW = -2
} MV_ParseStatus;

typedef struct {
    char buffer[MV_FRAME_MAX_LENGTH + 1U];
    size_t length;
    uint8_t collecting;
    uint8_t overflowed;
} MV_Parser;

void mv_parser_init(MV_Parser *parser);

/*
 * Parse one complete, writable `$MV,AIM,...#` packet.
 * WARNING: mv_parse_packet modifies the input buffer in-place. Do not pass
 * string literals or const buffers.
 */
MV_ParseStatus mv_parse_packet(char *packet, Aim_Result *out);

/* Feed one byte. Handles noise, half frames, sticky frames, and overlength frames. */
MV_ParseStatus mv_parser_feed(MV_Parser *parser, uint8_t byte, Aim_Result *out);

#endif
