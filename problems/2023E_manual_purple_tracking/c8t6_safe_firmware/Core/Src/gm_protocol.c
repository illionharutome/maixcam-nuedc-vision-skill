#include "gm_protocol.h"
#include <string.h>

static int parse_int(const char *s, int *out) {
    int sign = 1, val = 0;
    if (!s || !*s) return 0;
    if (*s == '-') { sign = -1; ++s; }
    while (*s >= '0' && *s <= '9') { val = val * 10 + (*s - '0'); ++s; }
    if (*s != '\0') return 0;
    *out = sign * val;
    return 1;
}

static int valid_mode(const char *s) {
    if (!s || !*s) return 0;
    return !strcmp(s, "TRACK") || !strcmp(s, "AIMED") ||
           !strcmp(s, "HOLD")  || !strcmp(s, "STOP");
}

static GmParseResult parse_frame(char *frame, GmCommand *out) {
    char *fields[C8T6_GM_FIELD_COUNT];
    char *cursor = frame;
    int count = 0;
    int pan, tilt;

    while (count < C8T6_GM_FIELD_COUNT) {
        char *end = strchr(cursor, ',');
        fields[count++] = cursor;
        if (!end) {
            end = strchr(cursor, '#');
            if (!end) return GM_PARSE_FIELD_COUNT;
            *end = '\0';
            break;
        }
        *end = '\0';
        cursor = end + 1;
    }
    if (count != C8T6_GM_FIELD_COUNT) return GM_PARSE_FIELD_COUNT;

    if (strcmp(fields[0], "$GM") != 0 || strcmp(fields[1], "CMD") != 0)
        return GM_PARSE_PREFIX;

    if (!parse_int(fields[2], &pan))  return GM_PARSE_PAN_RANGE;
    if (!parse_int(fields[3], &tilt)) return GM_PARSE_TILT_RANGE;
    if (pan < C8T6_GM_PAN_MIN || pan > C8T6_GM_PAN_MAX) return GM_PARSE_PAN_RANGE;
    if (tilt < C8T6_GM_TILT_MIN || tilt > C8T6_GM_TILT_MAX) return GM_PARSE_TILT_RANGE;
    if (!valid_mode(fields[4])) return GM_PARSE_MODE_INVALID;

    out->pan = pan;
    out->tilt = tilt;
    strncpy(out->mode, fields[4], C8T6_GM_MODE_MAX_LEN - 1);
    out->mode[C8T6_GM_MODE_MAX_LEN - 1] = '\0';
    return GM_PARSE_OK;
}

void gm_stream_init(GmStream *s) { memset(s, 0, sizeof(*s)); }

GmParseResult gm_stream_feed(GmStream *s, char byte, GmCommand *out) {
    GmParseResult r;
    if (byte == '$') { s->collecting = 1; s->overflow = 0; s->len = 0; }
    if (!s->collecting) return GM_PARSE_SHORT;
    if (!s->overflow) {
        if (s->len + 1 < C8T6_GM_FRAME_MAX_LEN) s->buf[s->len++] = byte;
        else s->overflow = 1;
    }
    if (byte != '#') return GM_PARSE_SHORT;
    s->collecting = 0;
    if (s->overflow) { s->len = 0; return GM_PARSE_FIELD_COUNT; }
    s->buf[s->len] = '\0';
    r = parse_frame(s->buf, out);
    s->len = 0;
    return r;
}

const char *gm_parse_result_name(GmParseResult r) {
    static const char *t[] = {"OK","SHORT","FIELD_COUNT","PAN_RANGE",
                               "TILT_RANGE","MODE_INVALID","NO_TERMINATOR","PREFIX"};
    return ((unsigned)r < 8) ? t[r] : "?";
}
