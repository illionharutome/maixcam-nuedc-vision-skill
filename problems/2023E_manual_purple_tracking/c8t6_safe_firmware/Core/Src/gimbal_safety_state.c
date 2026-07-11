#include "gimbal_safety_state.h"
#include <stdio.h>
#include <string.h>

void safety_state_init(SafetyState *s) {
    memset(s, 0, sizeof(*s));
    s->state = C8T6_STATE_DISABLED;
}

void safety_state_tick(SafetyState *s, const GmCommand *cmd, GmParseResult parse_r,
                       int *pan_out, int *tilt_out) {
    int ok = (parse_r == GM_PARSE_OK) && (cmd != NULL);

    /* STOP has absolute priority */
    if (ok && !strcmp(cmd->mode, "STOP")) {
        s->state = C8T6_STATE_STOP;
        s->timeout_ticks = 0;
        *pan_out = 0;
        *tilt_out = 0;
        return;
    }

    if (!ok) {
        s->timeout_ticks++;
        if (s->timeout_ticks > C8T6_CMD_TIMEOUT_TICKS) {
            s->state = C8T6_STATE_STOP;
        }
        *pan_out = 0;
        *tilt_out = 0;
        return;
    }

    s->timeout_ticks = 0;
    s->last_cmd = *cmd;

    if (!strcmp(cmd->mode, "TRACK")) {
        s->state = C8T6_STATE_TRACK;
    } else if (!strcmp(cmd->mode, "AIMED") || !strcmp(cmd->mode, "HOLD")) {
        s->state = C8T6_STATE_HOLD;
        *pan_out = 0;
        *tilt_out = 0;
        return;
    } else {
        s->state = C8T6_STATE_ERROR;
        *pan_out = 0;
        *tilt_out = 0;
        return;
    }

    /* TRACK mode: forward values only if state is TRACK */
    *pan_out = cmd->pan;
    *tilt_out = cmd->tilt;
}

const char *c8t6_state_name(C8t6State st) {
    static const char *n[] = {"DISABLED","IDLE","TRACK","HOLD","STOP","ERROR"};
    return ((unsigned)st <= C8T6_STATE_ERROR) ? n[st] : "ERROR";
}

int safety_build_ack(char *buf, int size, C8t6State st, int pan, int tilt, const char *mode) {
    if (!buf || size <= 0) return 0;
    return snprintf(buf, (size_t)size, "$GM,ACK,MODE=%s,PAN=%d,TILT=%d,STATE=%s#",
                    mode ? mode : "STOP", pan, tilt, c8t6_state_name(st));
}

int safety_build_err(char *buf, int size, C8t6State st, GmParseResult r) {
    if (!buf || size <= 0) return 0;
    return snprintf(buf, (size_t)size, "$GM,ERR,CODE=%s,STATE=%s#",
                    gm_parse_result_name(r), c8t6_state_name(st));
}
