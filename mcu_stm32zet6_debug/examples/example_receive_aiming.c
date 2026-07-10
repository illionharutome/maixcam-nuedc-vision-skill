#include <stdint.h>

#include "../../mcu_common/mv_parser.h"

static MV_Parser g_mv_parser;
volatile Aim_Result g_latest_aim;
volatile uint8_t g_latest_aim_ready;

void vision_debug_bridge_init(void)
{
    mv_parser_init(&g_mv_parser);
    g_latest_aim_ready = 0U;
}

void vision_debug_bridge_rx_byte(uint8_t byte)
{
    Aim_Result parsed;
    if (mv_parser_feed(&g_mv_parser, byte, &parsed) == MV_PARSE_AIM_READY) {
        g_latest_aim = parsed;
        g_latest_aim_ready = 1U;
    }
}

/*
 * Call vision_debug_bridge_rx_byte() from the UART receive path. Place a
 * debugger watch on g_latest_aim and g_latest_aim_ready. This bridge performs
 * no PID, PWM, motor, servo, laser, or arm control.
 */
