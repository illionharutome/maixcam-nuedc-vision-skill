#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "../mcu_common/mv_parser.h"

static MV_ParseStatus feed_text(MV_Parser *parser, const char *text, Aim_Result *out)
{
    MV_ParseStatus final = MV_PARSE_NONE;
    while (*text != '\0') {
        MV_ParseStatus status = mv_parser_feed(parser, (uint8_t)*text++, out);
        if (status != MV_PARSE_NONE) {
            final = status;
        }
    }
    return final;
}

int main(void)
{
    MV_Parser parser;
    Aim_Result aim;
    char writable[] = "$MV,AIM,1,160,120,148,132,-12,12,0.91,25.6,AIMING#";
    char too_long[MV_FRAME_MAX_LENGTH + 8U];
    size_t index;

    assert(mv_parse_packet(writable, &aim) == MV_PARSE_AIM_READY);
    assert(strcmp(aim.mode, "AIM") == 0);
    assert(aim.aim_error_x == -12);

    mv_parser_init(&parser);
    assert(feed_text(&parser, "noise$MV,AIM,1,160,120,", &aim) == MV_PARSE_NONE);
    assert(feed_text(&parser, "148,132,-12,12,0.91,25.6,AIMING#$MV,AIM,0,160,120,0,0,0,0,0,20,NO_SPOT#", &aim)
           == MV_PARSE_AIM_READY);
    assert(strcmp(aim.status, "NO_SPOT") == 0);

    mv_parser_init(&parser);
    too_long[0] = '$';
    for (index = 1U; index < sizeof(too_long) - 2U; ++index) {
        too_long[index] = 'X';
    }
    too_long[sizeof(too_long) - 2U] = '#';
    too_long[sizeof(too_long) - 1U] = '\0';
    assert(feed_text(&parser, too_long, &aim) == MV_PARSE_OVERFLOW);

    {
        char bad[] = "$MV,AIM,1,160#";
        assert(mv_parse_packet(bad, &aim) == MV_PARSE_INVALID);
    }
    return 0;
}
