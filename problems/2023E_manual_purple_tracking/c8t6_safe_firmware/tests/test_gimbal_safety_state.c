#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../Core/Inc/gimbal_safety_state.h"
#include "../Core/Inc/motor_output_stub.h"

static GmCommand mk(int pan, int tilt, const char *mode) {
    GmCommand c = {pan, tilt, ""};
    strncpy(c.mode, mode, C8T6_GM_MODE_MAX_LEN - 1);
    return c;
}

int main(void) {
    SafetyState s;
    int pan, tilt;
    GmCommand c;
    char buf[80];

    /* 1. Default DISABLED */
    safety_state_init(&s);
    assert(s.state == C8T6_STATE_DISABLED);

    /* 2. STOP priority */
    c = mk(300, 200, "TRACK");
    safety_state_tick(&s, &c, GM_PARSE_OK, &pan, &tilt);
    assert(s.state == C8T6_STATE_TRACK && pan == 300 && tilt == 200);
    c = mk(0, 0, "STOP");
    safety_state_tick(&s, &c, GM_PARSE_OK, &pan, &tilt);
    assert(s.state == C8T6_STATE_STOP && pan == 0 && tilt == 0);

    /* 3. Invalid parse -> safe */
    safety_state_init(&s);
    safety_state_tick(&s, NULL, GM_PARSE_FIELD_COUNT, &pan, &tilt);
    assert(pan == 0 && tilt == 0);

    /* 4. HOLD / AIMED zeroes output */
    safety_state_init(&s);
    c = mk(100, 50, "AIMED");
    safety_state_tick(&s, &c, GM_PARSE_OK, &pan, &tilt);
    assert(s.state == C8T6_STATE_HOLD && pan == 0 && tilt == 0);

    /* 5. ACK string */
    assert(safety_build_ack(buf, sizeof(buf), C8T6_STATE_TRACK, -300, 220, "TRACK") > 0);
    assert(strstr(buf, "$GM,ACK") != NULL && strstr(buf, "PAN=-300") != NULL);

    /* 6. ERR string */
    assert(safety_build_err(buf, sizeof(buf), C8T6_STATE_ERROR, GM_PARSE_PAN_RANGE) > 0);
    assert(strstr(buf, "$GM,ERR") != NULL && strstr(buf, "PAN_RANGE") != NULL);

    /* 7. Motor stub default disabled */
    motor_output_init();
    assert(g_motor_apply_count == 0);
    motor_output_apply(100, 200);
    assert(g_motor_latest_pan == 100 && g_motor_latest_tilt == 200 && g_motor_apply_count == 1);

    puts("gimbal_safety_state tests passed");
    return 0;
}
