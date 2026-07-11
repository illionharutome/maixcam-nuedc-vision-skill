#ifndef GM_PROTOCOL_H
#define GM_PROTOCOL_H

#include "c8t6_config.h"

typedef struct {
    int pan;          /* milli-unit, [-1000, 1000] */
    int tilt;         /* milli-unit, [-1000, 1000] */
    char mode[C8T6_GM_MODE_MAX_LEN];
} GmCommand;

typedef enum {
    GM_PARSE_OK = 0,
    GM_PARSE_SHORT,
    GM_PARSE_FIELD_COUNT,
    GM_PARSE_PAN_RANGE,
    GM_PARSE_TILT_RANGE,
    GM_PARSE_MODE_INVALID,
    GM_PARSE_NO_TERMINATOR,
    GM_PARSE_PREFIX
} GmParseResult;

typedef struct {
    char buf[C8T6_GM_FRAME_MAX_LEN + 1];
    int  len;
    int  collecting;
    int  overflow;
} GmStream;

void gm_stream_init(GmStream *s);
GmParseResult gm_stream_feed(GmStream *s, char byte, GmCommand *out);

const char *gm_parse_result_name(GmParseResult r);

#endif
