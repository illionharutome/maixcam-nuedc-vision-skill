#include <assert.h>
#include <stdio.h>
#include <string.h>

#include "../mcu_stm32zet6/protocol_2023e_single.h"
#include "../mcu_stm32zet6/single_gimbal_tracker.h"

static SinglePacket feed(SingleStreamParser *parser, const char *text, int *packets) {
    SinglePacket packet = {0};
    size_t i;
    for (i = 0; text[i] != '\0'; ++i) {
        if (single_stream_push(parser, text[i], &packet) == SINGLE_STREAM_PACKET) (*packets)++;
    }
    return packet;
}

int main(void) {
    const char *left = "$MV,SINGLE,1,140,110,160,120,-20,-10,CENTER,0,0.90,30.0,TRACKING#";
    SingleStreamParser parser;
    SinglePacket packet;
    SingleTracker tracker;
    GimbalCommandConfig config = {10.0f, 10.0f, 0.0f, 0.0f, 3, 1000, 1000};
    int packets = 0;
    size_t i;

    single_stream_init(&parser);
    packet = feed(&parser, left, &packets);
    assert(packets == 1 && packet.error_x == -20 && packet.error_y == -10);

    /* A split frame remains buffered; a subsequent glued frame is separate. */
    single_stream_init(&parser); packets = 0;
    packet = feed(&parser, "$MV,SINGLE,1,140,110,160,120,-20", &packets);
    assert(packets == 0);
    packet = feed(&parser, ",-10,CENTER,0,0.90,30.0,TRACKING#$MV,SINGLE,0,0,0,160,120,0,0,CENTER,0,0.00,30.0,NO_SPOT#", &packets);
    assert(packets == 2 && strcmp(packet.status, "NO_SPOT") == 0);

    single_tracker_init(&tracker);
    single_tracker_update(&tracker, &packet, &config);
    assert(tracker.valid == 0 && tracker.pan_command == 0 && tracker.tilt_command == 0);

    single_stream_init(&parser);
    single_stream_push(&parser, '$', &packet);
    for (i = 0; i < SINGLE_FRAME_MAX + 10u; ++i) single_stream_push(&parser, 'X', &packet);
    assert(single_stream_push(&parser, '#', &packet) == SINGLE_STREAM_REJECTED);
    puts("single MCU tests passed");
    return 0;
}
