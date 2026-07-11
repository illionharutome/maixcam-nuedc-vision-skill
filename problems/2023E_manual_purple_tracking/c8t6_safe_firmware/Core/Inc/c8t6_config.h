#ifndef C8T6_CONFIG_H
#define C8T6_CONFIG_H

/* ---------- safety master switches (ALL default OFF) ---------- */

#define C8T6_ENABLE_MOTOR_OUTPUT       0  /* must be 0 in repo */
#define C8T6_ENABLE_TIM_PULSE_OUTPUT   0  /* must be 0 in repo */
#define C8T6_ENABLE_UART_ACK           1  /* safe: string-only */

/* ---------- protocol limits ---------- */

#define C8T6_GM_PAN_MIN   (-1000)
#define C8T6_GM_PAN_MAX   ( 1000)
#define C8T6_GM_TILT_MIN  (-1000)
#define C8T6_GM_TILT_MAX  ( 1000)

#define C8T6_GM_FRAME_MAX_LEN   96
#define C8T6_GM_MODE_MAX_LEN    16
#define C8T6_GM_FIELD_COUNT      5   /* $GM,CMD,PAN,TILT,MODE# -> 5 after split */

/* ---------- watch-dog / timeout ---------- */

#define C8T6_CMD_TIMEOUT_TICKS   2000   /* ~2 s (1 ms per tick example) */
#define C8T6_ACK_BUF_SIZE        64

#endif
