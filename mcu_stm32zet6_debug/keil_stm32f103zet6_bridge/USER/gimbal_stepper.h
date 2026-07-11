#ifndef GIMBAL_STEPPER_H
#define GIMBAL_STEPPER_H

#include <stdint.h>
#include "gimbal_stepper_config.h"

typedef enum {
    GIMBAL_AXIS_PAN = 0,
    GIMBAL_AXIS_TILT = 1
} GimbalAxis;

/* Call once after clocks are ready.  Initialises GPIO direction,
   sets SLP/RST high, configures TIM4 ISR, resets all axes to idle. */
void GimbalStepper_Init(void);

/* Immediate emergency stop: clear STEP/DIR, optional SLP low. */
void GimbalStepper_StopAll(void);

/* Set signed speed target for one axis (deg/s).  ISR will ramp towards it. */
void GimbalStepper_SetAxisSpeed(GimbalAxis axis, float deg_per_sec);

/* Called every GIMBAL_CONTROL_PERIOD_MS from the main loop (or a timer).
   ex, ey  – pixel errors from vision (EX = TARGET_CX - AIM_CX style).
   valid   – 1 when tracking, 0 when LOST / NO_TARGET / STOP.
   now_ms  – monotonic millisecond counter for timeout. */
void GimbalStepper_ControlFromError(int32_t ex, int32_t ey, int valid,
                                    uint32_t now_ms);

/* TIM4 ISR handler (10 us).  Place this inside TIM4_IRQHandler(). */
void GimbalStepper_Task10usISR(void);

/* Read-only status for dry-run log / DBG output. */
extern volatile uint8_t g_stepper_run_flag;
extern volatile float g_stepper_pan_deg_s;
extern volatile float g_stepper_tilt_deg_s;

#endif
