#include <stdint.h>

#include "../../mcu_common/mv_parser.h"
#include "../../mcu_tmx3507/app/target_aiming_state_machine.h"

static MV_Parser g_mv_parser;
static const TargetAimingConfig g_debug_aim_config = {
    0.05f, 0.05f, 1.0f, 2, 2
};
volatile Aim_Result g_latest_aim;
volatile TargetAimingCommand g_latest_command;
volatile uint8_t g_latest_aim_ready;
volatile uint8_t g_debug_tx_pending;

void vision_debug_bridge_init(void)
{
    TargetAimingCommand command;
    mv_parser_init(&g_mv_parser);
    target_aiming_update(NULL, &g_debug_aim_config, &command);
    g_latest_command = command;
    g_latest_aim_ready = 0U;
}

void vision_debug_bridge_rx_byte(uint8_t byte)
{
    Aim_Result parsed;
    TargetAimingCommand command;
    if (mv_parser_feed(&g_mv_parser, byte, &parsed) == MV_PARSE_AIM_READY) {
        target_aiming_update(&parsed, &g_debug_aim_config, &command);
        g_latest_aim = parsed;
        g_latest_command = command;
        g_latest_aim_ready = 1U;
        g_debug_tx_pending = 1U;
    }
}

/*
 * Call vision_debug_bridge_rx_byte() from the UART receive path. Place a
 * debugger watch on g_latest_aim, g_latest_command, and g_latest_aim_ready.
 * This bridge performs no PID, PWM, motor, servo, laser, or arm control.
 */
