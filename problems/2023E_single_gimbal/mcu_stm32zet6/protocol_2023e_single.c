#include "protocol_2023e_single.h"

#include <stdlib.h>
#include <string.h>

#define SINGLE_FIELD_COUNT 14u

static int parse_i32(const char *text, int32_t *out) {
    char *end;
    long value = strtol(text, &end, 10);
    if (text == end || *end != '\0') return 0;
    *out = (int32_t)value;
    return 1;
}

static int parse_float(const char *text, float *out) {
    char *end;
    double value = strtod(text, &end);
    if (text == end || *end != '\0') return 0;
    *out = (float)value;
    return 1;
}

static int copy_text(char *dst, const char *src) {
    size_t length = strlen(src);
    if (length == 0u || length >= SINGLE_TEXT_MAX) return 0;
    memcpy(dst, src, length + 1u);
    return 1;
}

int single_parse_frame(char *frame, SinglePacket *out) {
    char *fields[SINGLE_FIELD_COUNT];
    char *cursor;
    size_t count = 0u;
    int32_t ok;
    if (frame == NULL || out == NULL || strncmp(frame, "$MV,SINGLE,", 11u) != 0) return 0;
    cursor = frame;
    while (count < SINGLE_FIELD_COUNT) {
        fields[count++] = cursor;
        cursor = strchr(cursor, ',');
        if (cursor == NULL) break;
        *cursor++ = '\0';
    }
    if (count != SINGLE_FIELD_COUNT || cursor != NULL) return 0;
    cursor = strchr(fields[13], '#');
    if (cursor == NULL || cursor[1] != '\0') return 0;
    *cursor = '\0';
    memset(out, 0, sizeof(*out));
    if (strcmp(fields[0], "$MV") != 0 || strcmp(fields[1], "SINGLE") != 0) return 0;
    if (!parse_i32(fields[2], &ok) || (ok != 0 && ok != 1)) return 0;
    out->ok = (uint8_t)ok;
    return parse_i32(fields[3], &out->spot_cx) && parse_i32(fields[4], &out->spot_cy) &&
           parse_i32(fields[5], &out->target_cx) && parse_i32(fields[6], &out->target_cy) &&
           parse_i32(fields[7], &out->error_x) && parse_i32(fields[8], &out->error_y) &&
           copy_text(out->path_id, fields[9]) && parse_i32(fields[10], &out->step_id) &&
           parse_float(fields[11], &out->score) && parse_float(fields[12], &out->fps) &&
           copy_text(out->status, fields[13]);
}

void single_stream_init(SingleStreamParser *parser) {
    memset(parser, 0, sizeof(*parser));
}

SingleStreamResult single_stream_push(SingleStreamParser *parser, char byte, SinglePacket *out) {
    int parsed;
    if (byte == '$') {
        parser->collecting = 1u;
        parser->overflow = 0u;
        parser->length = 0u;
    }
    if (!parser->collecting) return SINGLE_STREAM_NONE;
    if (!parser->overflow) {
        if (parser->length + 1u < SINGLE_FRAME_MAX) parser->buffer[parser->length++] = byte;
        else parser->overflow = 1u;
    }
    if (byte != '#') return SINGLE_STREAM_NONE;
    parser->collecting = 0u;
    if (parser->overflow) {
        parser->length = 0u;
        return SINGLE_STREAM_REJECTED;
    }
    parser->buffer[parser->length] = '\0';
    parsed = single_parse_frame(parser->buffer, out);
    parser->length = 0u;
    return parsed ? SINGLE_STREAM_PACKET : SINGLE_STREAM_REJECTED;
}
