#include <stdint.h>
#include <string.h>

#include "../../mcu_common/mv_parser.h"
#include "../app/target_aiming_state_machine.h"

static MV_Parser g_parser;
static Aim_Result g_aim;
static TargetAimingCommand g_command;
static const TargetAimingConfig g_config = {
    0.05f, 0.05f, 1.0f, 2, 2
};

void example_2025e_init(void)
{
    mv_parser_init(&g_parser);
}

void example_2025e_rx_byte(uint8_t byte)
{
    if (mv_parser_feed(&g_parser, byte, &g_aim) == MV_PARSE_AIM_READY) {
        if (strcmp(g_aim.mode, "AIM") == 0) {
            target_aiming_update(&g_aim, &g_config, &g_command);
        }
    }
}

/* g_command contains bounded abstract suggestions only. It is not PWM, a
 * servo angle, or an actuator command. No UART/PWM/GPIO pin is fixed here. */
