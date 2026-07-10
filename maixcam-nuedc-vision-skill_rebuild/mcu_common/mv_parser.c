#include "mv_parser.h"

#include <errno.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>

static int copy_text(char *destination, size_t capacity, const char *source)
{
    size_t length;
    if ((destination == NULL) || (source == NULL) || (capacity == 0U)) {
        return 0;
    }
    length = strlen(source);
    if (length >= capacity) {
        return 0;
    }
    memcpy(destination, source, length + 1U);
    return 1;
}

static int parse_int32(const char *text, int32_t *out)
{
    char *end = NULL;
    long parsed;
    if ((text == NULL) || (out == NULL) || (*text == '\0')) {
        return 0;
    }
    errno = 0;
    parsed = strtol(text, &end, 10);
    if ((errno == ERANGE) || (*end != '\0') ||
        (parsed < INT32_MIN) || (parsed > INT32_MAX)) {
        return 0;
    }
    *out = (int32_t)parsed;
    return 1;
}

static int parse_float_value(const char *text, float *out)
{
    char *end = NULL;
    double parsed;
    if ((text == NULL) || (out == NULL) || (*text == '\0')) {
        return 0;
    }
    /* strtod is available in the MSPM0 newlib toolchain; cast for float storage. */
    errno = 0;
    parsed = strtod(text, &end);
    if ((errno == ERANGE) || (*end != '\0')) {
        return 0;
    }
    *out = (float)parsed;
    return 1;
}

static size_t split_fields(char *text, char **fields, size_t capacity)
{
    size_t count = 0U;
    char *cursor = text;
    if ((text == NULL) || (fields == NULL) || (capacity == 0U)) {
        return 0U;
    }
    fields[count++] = cursor;
    while (*cursor != '\0') {
        if (*cursor == ',') {
            *cursor = '\0';
            if (count >= capacity) {
                return capacity + 1U;
            }
            fields[count++] = cursor + 1;
        }
        ++cursor;
    }
    return count;
}

void mv_parser_init(MV_Parser *parser)
{
    if (parser != NULL) {
        memset(parser, 0, sizeof(*parser));
    }
}

MV_ParseStatus mv_parse_packet(char *packet, Aim_Result *out)
{
    char *fields[MV_AIM_FIELD_COUNT];
    size_t length;
    size_t count;
    int32_t ok_value;

    if ((packet == NULL) || (out == NULL)) {
        return MV_PARSE_INVALID;
    }
    length = strlen(packet);
    if ((length < 5U) || (packet[0] != MV_FRAME_START) ||
        (packet[length - 1U] != MV_FRAME_END)) {
        return MV_PARSE_INVALID;
    }
    packet[length - 1U] = '\0';
    count = split_fields(packet, fields, MV_AIM_FIELD_COUNT);
    if ((count != MV_AIM_FIELD_COUNT) || (strcmp(fields[0], "$MV") != 0) ||
        (strcmp(fields[1], "AIM") != 0)) {
        return MV_PARSE_INVALID;
    }
    if (!parse_int32(fields[2], &ok_value) || ((ok_value != 0) && (ok_value != 1))) {
        return MV_PARSE_INVALID;
    }

    memset(out, 0, sizeof(*out));
    if (!copy_text(out->mode, sizeof(out->mode), fields[1]) ||
        !parse_int32(fields[3], &out->target_cx) ||
        !parse_int32(fields[4], &out->target_cy) ||
        !parse_int32(fields[5], &out->spot_cx) ||
        !parse_int32(fields[6], &out->spot_cy) ||
        !parse_int32(fields[7], &out->aim_error_x) ||
        !parse_int32(fields[8], &out->aim_error_y) ||
        !parse_float_value(fields[9], &out->score) ||
        !parse_float_value(fields[10], &out->fps) ||
        !copy_text(out->status, sizeof(out->status), fields[11])) {
        memset(out, 0, sizeof(*out));
        return MV_PARSE_INVALID;
    }
    out->ok = (uint8_t)ok_value;
    return MV_PARSE_AIM_READY;
}

MV_ParseStatus mv_parser_feed(MV_Parser *parser, uint8_t byte, Aim_Result *out)
{
    char character = (char)byte;
    MV_ParseStatus status;
    if ((parser == NULL) || (out == NULL)) {
        return MV_PARSE_INVALID;
    }

    if (character == MV_FRAME_START) {
        parser->buffer[0] = character;
        parser->length = 1U;
        parser->collecting = 1U;
        parser->overflowed = 0U;
        return MV_PARSE_NONE;
    }
    if (parser->collecting == 0U) {
        return MV_PARSE_NONE;
    }
    if (parser->overflowed != 0U) {
        if (character == MV_FRAME_END) {
            parser->collecting = 0U;
            parser->overflowed = 0U;
            parser->length = 0U;
        }
        return MV_PARSE_NONE;
    }
    if (parser->length >= MV_FRAME_MAX_LENGTH) {
        parser->overflowed = 1U;
        parser->length = 0U;
        return MV_PARSE_OVERFLOW;
    }

    parser->buffer[parser->length++] = character;
    if (character != MV_FRAME_END) {
        return MV_PARSE_NONE;
    }
    parser->buffer[parser->length] = '\0';
    parser->collecting = 0U;
    status = mv_parse_packet(parser->buffer, out);
    parser->length = 0U;
    return status;
}
