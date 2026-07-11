#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "vision_parser.h"

static bool feed(const char *text, VisionCommand_t *command)
{
    bool complete = false;
    for (; *text; ++text) complete = vision_parser_feed((uint8_t)*text, command) || complete;
    return complete;
}

int main(void)
{
    VisionCommand_t command = {0};
    vision_parser_init();
    assert(feed("boot noise\r\n$MV,AIM,1,160,120,148,132,-12,12,91,256,AIMING#", &command));
    assert(command.state == VISION_TRACKING && command.dx == -12 && command.dy == 12);
    assert(command.confidence == 91 && command.dist_mm == 256);
    assert(!feed("$MV,AIM,1,0,0,0,0,99999,0,10,0,AIMING#", &command));
    assert(feed("$garbage$MV,AIM,0,160,120,0,0,0,0,0,0,LOST#", &command));
    assert(command.state == VISION_LOST);
    return 0;
}
