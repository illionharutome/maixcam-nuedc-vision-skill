#include <stdint.h>

#include "../../mcu_common/mv_parser.h"
#include "../../mcu_tmx3507/app/target_aiming_state_machine.h"
#include "../../problems/2023E_manual_purple_tracking/mcu_stm32zet6/protocol_track1.h"
#include "../../problems/2023E_manual_purple_tracking/mcu_stm32zet6/manual_tracker_state.h"
#include "../../problems/2023E_manual_purple_tracking/mcu_stm32zet6/gimbal_board_interface.h"

static MV_Parser g_mv_parser;
static Track1Stream g_track1_parser;
static const TargetAimingConfig g_debug_aim_config = {
    0.05f, 0.05f, 1.0f, 2, 2
};
static const TrackerCommandConfig g_debug_track1_config = {
    15.0f, 15.0f, 0.0f, 0.0f, 3, 1000, 1000, 1, 1
};
volatile Aim_Result g_latest_aim;
volatile TargetAimingCommand g_latest_command;
volatile Track1Packet g_latest_track1;
volatile ManualTracker g_latest_track1_command;
char g_latest_gimbal_dry_run[80];
volatile uint8_t g_latest_aim_ready;
volatile uint8_t g_debug_tx_pending;
volatile uint8_t g_debug_packet_kind;

#define DEBUG_PACKET_NONE   0U
#define DEBUG_PACKET_AIM    1U
#define DEBUG_PACKET_TRACK1 2U

void vision_debug_bridge_init(void)
{
    TargetAimingCommand command;
    ManualTracker tracker;
    mv_parser_init(&g_mv_parser);
    track1_stream_init(&g_track1_parser);
    target_aiming_update(NULL, &g_debug_aim_config, &command);
    g_latest_command = command;
    manual_tracker_init(&tracker);
    g_latest_track1_command = tracker;
    g_latest_gimbal_dry_run[0] = '\0';
    g_latest_aim_ready = 0U;
    g_debug_tx_pending = 0U;
    g_debug_packet_kind = DEBUG_PACKET_NONE;
}

void vision_debug_bridge_rx_byte(uint8_t byte)
{
    Aim_Result parsed;
    TargetAimingCommand command;
    Track1Packet track1;
    ManualTracker tracker;
    if (mv_parser_feed(&g_mv_parser, byte, &parsed) == MV_PARSE_AIM_READY) {
        target_aiming_update(&parsed, &g_debug_aim_config, &command);
        g_latest_aim = parsed;
        g_latest_command = command;
        g_latest_aim_ready = 1U;
        g_debug_packet_kind = DEBUG_PACKET_AIM;
        g_debug_tx_pending = 1U;
    }
    if (track1_stream_push(&g_track1_parser, (char)byte, &track1) == TRACK1_PACKET) {
        tracker = g_latest_track1_command;
        manual_tracker_update(&tracker, &track1, &g_debug_track1_config);
        g_latest_track1 = track1;
        g_latest_track1_command = tracker;
        (void)gimbal_board_format_dry_run(g_latest_gimbal_dry_run,
                                          sizeof(g_latest_gimbal_dry_run),
                                          (int)tracker.pan_command,
                                          (int)tracker.tilt_command,
                                          "TRACK");
        g_debug_packet_kind = DEBUG_PACKET_TRACK1;
        g_debug_tx_pending = 1U;
    }
}

/*
 * Call vision_debug_bridge_rx_byte() from the UART receive path. Place a
 * debugger watch on g_latest_aim, g_latest_command, and g_latest_aim_ready.
 * This bridge performs no PID, PWM, motor, servo, laser, or arm control.
 */
