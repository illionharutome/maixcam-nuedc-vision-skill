/*
 * C8T6 safety firmware skeleton.
 * This is NOT a runnable Keil project. It only illustrates the safe
 * boot sequence and main-loop structure. All motor output is disabled.
 *
 * DO NOT flash this onto actual hardware without:
 *  - UART RX pin confirmation
 *  - board-specific clock / GPIO init
 *  - empty-load-only motor test approval
 */

#include "../Inc/c8t6_config.h"
#include "../Inc/gm_protocol.h"
#include "../Inc/gimbal_safety_state.h"
#include "../Inc/motor_output_stub.h"

/*
static void system_init(void);   // board-specific: clock, UART RX, etc.
static int  uart_rx_byte(void);  // board-specific: read one byte or return -1
static void uart_tx_str(const char *s); // board-specific: debug TX
*/

int main(void)
{
    GmStream stream;
    SafetyState safe;
    char ack_buf[C8T6_ACK_BUF_SIZE];
    int pan = 0, tilt = 0;

    /* system_init(); */
    gm_stream_init(&stream);
    safety_state_init(&safe);
    motor_output_init();

    for (;;) {
#if 0 /* board-specific UART RX */
        int ch = uart_rx_byte();
        if (ch >= 0) {
            GmCommand cmd;
            GmParseResult r = gm_stream_feed(&stream, (char)ch, &cmd);
            if (r == GM_PARSE_OK || r >= GM_PARSE_FIELD_COUNT) {
                safety_state_tick(&safe, (r == GM_PARSE_OK) ? &cmd : NULL, r, &pan, &tilt);
                if (safe.state == C8T6_STATE_STOP || safe.state == C8T6_STATE_ERROR) {
                    pan = 0; tilt = 0;
                }
                motor_output_apply(pan, tilt);
#if C8T6_ENABLE_UART_ACK
                if (r == GM_PARSE_OK)
                    safety_build_ack(ack_buf, sizeof(ack_buf), safe.state, pan, tilt, cmd.mode);
                else
                    safety_build_err(ack_buf, sizeof(ack_buf), safe.state, r);
                /* uart_tx_str(ack_buf); */
#endif
            }
        }
#endif
    }
    return 0;
}
