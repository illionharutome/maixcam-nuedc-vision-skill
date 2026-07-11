#include "vision_parser.h"

#include <limits.h>
#include <stdlib.h>
#include <string.h>

#define FRAME_CAPACITY 96U
#define FIELD_COUNT 12U

static char frame[FRAME_CAPACITY];
static uint8_t length;
static bool receiving;

static bool parse_long(const char *text, long minimum, long maximum, long *value)
{
    char *end;
    long parsed = strtol(text, &end, 10);
    if (*text == '\0' || *end != '\0' || parsed < minimum || parsed > maximum) return false;
    *value = parsed;
    return true;
}

static bool parse_frame(char *text, VisionCommand_t *command)
{
    char *fields[FIELD_COUNT];
    uint8_t count = 0U;
    char *cursor = text;
    long valid, dx, dy, confidence, distance, ignored;
    while (count < FIELD_COUNT) {
        fields[count++] = cursor;
        cursor = strchr(cursor, ',');
        if (cursor == NULL) break;
        *cursor++ = '\0';
    }
    if (count != FIELD_COUNT || cursor != NULL || strcmp(fields[0], "$MV") != 0) return false;
    if (strcmp(fields[1], "AIM") && strcmp(fields[1], "TRACK") && strcmp(fields[1], "LINE") && strcmp(fields[1], "YOLO")) return false;
    if (!parse_long(fields[2], 0, 1, &valid)) return false;
    if (!parse_long(fields[3], 0, INT16_MAX, &ignored) || !parse_long(fields[4], 0, INT16_MAX, &ignored) ||
        !parse_long(fields[5], 0, INT16_MAX, &ignored) || !parse_long(fields[6], 0, INT16_MAX, &ignored)) return false;
    if (!parse_long(fields[7], INT16_MIN, INT16_MAX, &dx) || !parse_long(fields[8], INT16_MIN, INT16_MAX, &dy) ||
        !parse_long(fields[9], 0, 100, &confidence) || !parse_long(fields[10], 0, UINT16_MAX, &distance)) return false;
    if (valid == 0) command->state = strcmp(fields[11], "LOST") == 0 ? VISION_LOST : VISION_NO_TARGET;
    else if (strcmp(fields[11], "LOCKED") == 0) command->state = VISION_LOCKED;
    else if (strcmp(fields[11], "AIMING") == 0) command->state = VISION_TRACKING;
    else return false;
    command->dx = (int16_t)dx;
    command->dy = (int16_t)dy;
    command->confidence = (uint8_t)confidence;
    command->dist_mm = (uint16_t)distance;
    return true;
}

void vision_parser_init(void) { length = 0U; receiving = false; }

bool vision_parser_feed(uint8_t byte, VisionCommand_t *command)
{
    if (byte == '$') { receiving = true; length = 0U; frame[length++] = '$'; return false; }
    if (!receiving) return false;
    if (byte == '#') {
        bool valid;
        frame[length] = '\0';
        receiving = false;
        valid = parse_frame(frame, command);
        length = 0U;
        return valid;
    }
    if (length >= FRAME_CAPACITY - 1U) { receiving = false; length = 0U; return false; }
    frame[length++] = (char)byte;
    return false;
}

