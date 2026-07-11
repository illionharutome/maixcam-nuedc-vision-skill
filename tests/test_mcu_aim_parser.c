#include <assert.h>
#include <string.h>

#include "../mcu_common/mv_parser.h"

static void assert_packet(char *packet,
                          int32_t target_cx,
                          int32_t target_cy,
                          int32_t spot_cx,
                          int32_t spot_cy,
                          int32_t error_x,
                          int32_t error_y,
                          uint8_t ok,
                          const char *status)
{
    Aim_Result aim;
    assert(mv_parse_packet(packet, &aim) == MV_PARSE_AIM_READY);
    assert(strcmp(aim.mode, "AIM") == 0);
    assert(aim.ok == ok);
    assert(aim.target_cx == target_cx);
    assert(aim.target_cy == target_cy);
    assert(aim.spot_cx == spot_cx);
    assert(aim.spot_cy == spot_cy);
    assert(aim.aim_error_x == error_x);
    assert(aim.aim_error_y == error_y);
    assert(strcmp(aim.status, status) == 0);
}

int main(void)
{
    char sample[] = "$MV,AIM,1,160,120,148,132,-12,12,0.91,25.6,AIMING#";
    char spot_right[] = "$MV,AIM,1,160,120,190,120,30,0,0.91,25.6,AIMING#";
    char spot_left[] = "$MV,AIM,1,160,120,120,120,-40,0,0.91,25.6,AIMING#";
    char no_spot[] = "$MV,AIM,0,160,120,0,0,0,0,0.00,25.6,NO_SPOT#";
    char aimed[] = "$MV,AIM,1,160,120,162,119,2,-1,0.95,25.6,AIMED#";

    assert_packet(sample, 160, 120, 148, 132, -12, 12, 1U, "AIMING");
    assert_packet(spot_right, 160, 120, 190, 120, 30, 0, 1U, "AIMING");
    assert_packet(spot_left, 160, 120, 120, 120, -40, 0, 1U, "AIMING");
    assert_packet(no_spot, 160, 120, 0, 0, 0, 0, 0U, "NO_SPOT");
    assert_packet(aimed, 160, 120, 162, 119, 2, -1, 1U, "AIMED");
    return 0;
}
