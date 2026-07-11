#ifndef GIMBAL_SAFETY_STATE_H
#define GIMBAL_SAFETY_STATE_H

#include "c8t6_config.h"
#include "gm_protocol.h"

typedef enum {
    C8T6_STATE_DISABLED = 0,
    C8T6_STATE_IDLE,
    C8T6_STATE_TRACK,
    C8T6_STATE_HOLD,
    C8T6_STATE_STOP,
    C8T6_STATE_ERROR
} C8t6State;

typedef struct {
    C8t6State state;
    int timeout_ticks;
    GmCommand last_cmd;
    int ack_count;
} SafetyState;

void safety_state_init(SafetyState *s);
void safety_state_tick(SafetyState *s, const GmCommand *cmd, GmParseResult parse_r,
                       int *pan_out, int *tilt_out);
const char *c8t6_state_name(C8t6State st);

/* ACK/ERR string builder (safe: only formats text, no HW output) */
int safety_build_ack(char *buf, int size, C8t6State st, int pan, int tilt, const char *mode);
int safety_build_err(char *buf, int size, C8t6State st, GmParseResult r);

#endif
