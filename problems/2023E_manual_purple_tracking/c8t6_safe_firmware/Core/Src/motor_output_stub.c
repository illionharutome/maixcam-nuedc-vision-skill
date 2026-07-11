#include "motor_output_stub.h"

volatile int g_motor_latest_pan;
volatile int g_motor_latest_tilt;
volatile int g_motor_apply_count;

void motor_output_init(void) {
    g_motor_latest_pan  = 0;
    g_motor_latest_tilt = 0;
    g_motor_apply_count = 0;
}

void motor_output_apply(int pan_milli, int tilt_milli) {
    g_motor_latest_pan  = pan_milli;
    g_motor_latest_tilt = tilt_milli;
    g_motor_apply_count++;

#if C8T6_ENABLE_MOTOR_OUTPUT
    /* --- DANGER ZONE: only compiled when explicitly enabled after review --- */
    /* This path intentionally empty until hardware, limit, and safety
       review is complete.  Any GPIO/TIM/PWM must be added here. */
#else
    (void)pan_milli; (void)tilt_milli;
#endif
}
