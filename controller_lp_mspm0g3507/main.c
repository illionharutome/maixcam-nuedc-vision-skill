#include "ti_msp_dl_config.h"

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#include "gimbal_control.h"
#include "lp_tracking_config.h"
#include "vision_parser.h"

static volatile VisionCommand_t pending_command;
static volatile bool command_ready;

static void debug_write(const char *text)
{
    while (*text != '\0') {
        DL_UART_transmitDataBlocking(DEBUG_UART_INST, (uint8_t)*text++);
    }
}

static void debug_command(const VisionCommand_t *command)
{
    char line[80];
    (void)snprintf(line, sizeof(line), "MV state=%u dx=%d dy=%d conf=%u\r\n",
                   (unsigned)command->state, (int)command->dx, (int)command->dy,
                   (unsigned)command->confidence);
    debug_write(line);
}

void VISION_UART_INST_IRQHandler(void)
{
    if (DL_UART_getPendingInterrupt(VISION_UART_INST) == DL_UART_IIDX_RX) {
        VisionCommand_t parsed;
        uint8_t byte = DL_UART_receiveData(VISION_UART_INST);
        if (vision_parser_feed(byte, &parsed)) {
            pending_command = parsed;
            command_ready = true;
        }
    }
}

int main(void)
{
    uint16_t frame_age_ms = 0U;
    const GimbalConfig_t gimbal_config = {
        .deadband_px = LP_TRACKING_DEADBAND_PX,
        .min_speed_dps = LP_TRACKING_MIN_SPEED_DPS,
        .max_speed_dps = LP_TRACKING_MAX_SPEED_DPS,
        .confidence_min = LP_TRACKING_CONFIDENCE_MIN,
        .lost_frame_limit = LP_TRACKING_LOST_FRAME_LIMIT,
        .invert_pan = LP_TRACKING_INVERT_PAN,
        .invert_tilt = LP_TRACKING_INVERT_TILT,
    };

    SYSCFG_DL_init();
    vision_parser_init();
    command_ready = false;
#if LP_TRACKING_ENABLE_MOTORS
    gimbal_control_init(&gimbal_config);
#else
    (void)gimbal_config;
#endif
    NVIC_EnableIRQ(VISION_UART_INST_INT_IRQN);
    debug_write("LP-MSPM0G3507 vision UART ready; motors disabled by default\r\n");

    while (1) {
        VisionCommand_t command;
        bool ready;

        __disable_irq();
        ready = command_ready;
        if (ready) {
            command = pending_command;
            command_ready = false;
        }
        __enable_irq();

        if (ready) {
            frame_age_ms = 0U;
            debug_command(&command);
#if LP_TRACKING_ENABLE_MOTORS
            if (!LP_TRACKING_ENABLE_PAN) command.dx = 0;
            if (!LP_TRACKING_ENABLE_TILT) command.dy = 0;
            gimbal_control_update(&command);
#endif
        } else if (++frame_age_ms >= LP_TRACKING_TIMEOUT_MS) {
            frame_age_ms = 0U;
#if LP_TRACKING_ENABLE_MOTORS
            gimbal_control_on_frame_timeout();
#endif
        }
        delay_cycles(CPUCLK_FREQ / 1000U);
    }
}
