#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../../../mcu_common/mv_result.h"
#include "../../../mcu_tmx3507/app/target_aiming_state_machine.h"
#include "../mcu_stm32zet6/protocol_track1.h"
#include "../mcu_stm32zet6/manual_tracker_state.h"

void vision_debug_bridge_init(void);
void vision_debug_bridge_rx_byte(uint8_t byte);
extern volatile Aim_Result g_latest_aim;
extern volatile TargetAimingCommand g_latest_command;
extern volatile Track1Packet g_latest_track1;
extern volatile ManualTracker g_latest_track1_command;
extern char g_latest_gimbal_dry_run[80];
extern volatile uint8_t g_debug_packet_kind;

static void feed(const char *text) { while (*text) vision_debug_bridge_rx_byte((uint8_t)*text++); }

int main(void) {
    vision_debug_bridge_init();
    feed("$MV,AIM,1,160,120,148,132,-12,12,0.91,25.6,AIMING#");
    assert(g_debug_packet_kind == 1U);
    assert(g_latest_aim.aim_error_x == -12 && g_latest_command.valid == 1U);

    feed("$MV,TRACK1,1,140,110,160,120,-20,-10,0.90,30.0,TRACKING#");
    assert(g_debug_packet_kind == 2U && g_latest_track1_command.valid == 1);
    assert(g_latest_track1_command.pan_command < 0 && g_latest_track1_command.tilt_command < 0);
    assert(strcmp(g_latest_gimbal_dry_run, "$GM,CMD,PAN=-300,TILT=-150,MODE=TRACK#") == 0);

    feed("$MV,TRACK1,0,0,0,160,120,0,0,0.00,30.0,NO_TARGET#");
    assert(g_latest_track1_command.valid == 0 && g_latest_track1_command.pan_command == 0 && g_latest_track1_command.tilt_command == 0);

    feed("$MV,TRACK1,1,162,119,160,120,2,-1,0.95,30.0,AIMED#");
    assert(g_latest_track1_command.valid == 1 && g_latest_track1_command.state == MANUAL_AIMED);
    assert(g_latest_track1_command.pan_command == 0 && g_latest_track1_command.tilt_command == 0);
    puts("dual AIM/TRACK1 bridge tests passed");
    return 0;
}
