#ifndef GIMBAL_STEPPER_H
#define GIMBAL_STEPPER_H

#include <stdint.h>
#include "gimbal_stepper_config.h"

typedef enum {
    GIMBAL_AXIS_PAN = 0,
    GIMBAL_AXIS_TILT = 1
} GimbalAxis;

/* Global 10us tick counter updated in TIM4 ISR (always, even when macro=0). */
extern volatile uint32_t g_gimbal_tick10us;

/* Init: GPIO direction, SLP/RST LOW first then HIGH, TIM4 ISR, axes to idle.
   Safe when GIMBAL_ENABLE_STEPPER_OUTPUT=0 (no GPIO writes on STEP/DIR). */
void GimbalStepper_Init(void);

/* Emergency stop: STEP=LOW, run_flag=0, speeds=0, counters=0.
   When GIMBAL_SLEEP_ON_STOPALL=1 also pulls SLP LOW. */
void GimbalStepper_StopAll(void);

/* Set signed speed target (deg/s).  ISR ramps towards it via pre-computed ticks. */
void GimbalStepper_SetAxisSpeed(GimbalAxis axis, float deg_per_sec);

/* Called every 20ms from main loop.
   pan_cmd, tilt_cmd – raw commands from tracker (-1000..+1000 milli-unit).
   valid – 1 when tracking, 0 otherwise. */
void GimbalStepper_ControlFromCommand(int32_t pan_cmd, int32_t tilt_cmd,
                                      int valid);

/* TIM4 ISR handler.  Always clears UIF and increments tick.
   GPIO toggling only when GIMBAL_ENABLE_STEPPER_OUTPUT=1. */
void GimbalStepper_Task10usISR(void);

/* Read-only status. */
extern volatile uint8_t  g_stepper_run_flag;
extern volatile int32_t  g_stepper_pan_degs_milli;
extern volatile int32_t  g_stepper_tilt_degs_milli;

#endif
