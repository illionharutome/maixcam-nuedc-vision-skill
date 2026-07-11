#include "gimbal_stepper.h"
#include "bridge_config.h"

#define REG32(addr) (*(volatile uint32_t *)(addr))

/* ---- local registers ---- */
#define RCC_BASE            0x40021000UL
#define RCC_APB2ENR         REG32(RCC_BASE + 0x18UL)
#define RCC_APB1ENR         REG32(RCC_BASE + 0x1CUL)
#define RCC_APB2ENR_IOPBEN  (1UL << 3)
#define RCC_APB1ENR_TIM4EN  (1UL << 2)

#define GPIOB_CRL           REG32(GIMBAL_GPIO_BASE + 0x00UL)
#define GPIOB_CRH           REG32(GIMBAL_GPIO_BASE + 0x04UL)
#define GPIOB_ODR           REG32(GIMBAL_GPIO_BASE + 0x0CUL)

#define NVIC_ISER0          REG32(0xE000E100UL)

/* ---- globals ---- */
volatile uint32_t g_gimbal_tick10us;
volatile uint8_t  g_stepper_run_flag;
volatile int32_t  g_stepper_pan_degs_milli;
volatile int32_t  g_stepper_tilt_degs_milli;

/* ---- per-axis state (all integer inside ISR) ---- */
typedef struct {
    int8_t   dir_sign;          /* +1 or -1 as set by PAN/TILT_DIR_SIGN */
    uint32_t half_period_ticks; /* half pulse period in 10us units, pre-computed */
    uint32_t accum;             /* 10us accumulator */
    uint8_t  step_level;        /* current STEP pin state (0/1) */
    uint8_t  pin_step_mask;     /* BSRR SET bit mask for this axis */
    uint8_t  pin_dir_mask;      /* BSRR SET bit mask */
    uint8_t  dir_pending;       /* 1 = direction change requested, axes stopped */
    uint8_t  dir_want_high;     /* new DIR level after pending resolved */
    float    target_deg_s;      /* commanded speed (float, set from 20ms loop) */
} StepperAxis;

static StepperAxis g_pan, g_tilt;

/* ---- helpers ---- */
static uint32_t abs_i32(int32_t v) { return (uint32_t)(v < 0 ? -v : v); }

static void stepper_stop_axis(StepperAxis *a, uint32_t *bsrr) {
    if (a->step_level) {
        *bsrr |= ((uint32_t)a->pin_step_mask) << 16U;  /* RESET = LOW */
        a->step_level = 0;
    }
    a->accum          = 0;
    a->target_deg_s   = 0.0f;
    a->half_period_ticks = 0;
    a->dir_pending    = 0;
}

/* ================================================================
   Init – STEP/DIR start LOW; SLP/RST sequence avoids glitches.
   ================================================================ */
void GimbalStepper_Init(void)
{
    uint32_t crl, crh;
    uint32_t nvic_bit;

    /* clocks */
    RCC_APB2ENR |= RCC_APB2ENR_IOPBEN;
    RCC_APB1ENR |= RCC_APB1ENR_TIM4EN;

    /* GPIOB: PB0,5,6,7,8,9 -> GP output PP 50 MHz (MODE=11, CNF=00 -> 0x3) */
    crl = GPIOB_CRL;
    crl = (crl & ~0xFUL)         | 0x3UL;            /* PB0 */
    crl = (crl & ~(0xFUL << 20)) | (0x3UL << 20);    /* PB5 */
    crl = (crl & ~(0xFUL << 24)) | (0x3UL << 24);    /* PB6 */
    crl = (crl & ~(0xFUL << 28)) | (0x3UL << 28);    /* PB7 */
    GPIOB_CRL = crl;

    crh = GPIOB_CRH;
    crh = (crh & ~0xFUL)         | 0x3UL;            /* PB8 */
    crh = (crh & ~(0xFUL << 4))  | (0x3UL << 4);     /* PB9 */
    GPIOB_CRH = crh;

    /* --- safe init: all outputs LOW, then RST HIGH, then SLP HIGH --- */
    GIMBAL_GPIO_RESET(GIMBAL_MASK_STEP | GIMBAL_MASK_DIR);
    GIMBAL_GPIO_RESET(GIMBAL_MASK_RST);
    GIMBAL_GPIO_RESET(GIMBAL_MASK_SLP);
    GIMBAL_GPIO_SET(GIMBAL_MASK_RST);   /* release reset while STEP low */
    GIMBAL_GPIO_SET(GIMBAL_MASK_SLP);   /* enable driver */

    /* TIM4 for 10us tick (always running, even when stepper output disabled) */
    GIMBAL_TIM_PSC  = GIMBAL_TIM_PSC_VALUE;
    GIMBAL_TIM_ARR  = GIMBAL_TIM_ARR_VALUE;
    GIMBAL_TIM_DIER = (1UL << 0);        /* UIE */
    GIMBAL_TIM_CR1  = (1UL << 0);        /* CEN */

    nvic_bit = GIMBAL_TIM_IRQn;
    if (nvic_bit < 32UL) NVIC_ISER0 = (1UL << nvic_bit);

    /* axis state */
    g_pan.pin_step_mask = GIMBAL_MASK_PAN_STEP;
    g_pan.pin_dir_mask  = GIMBAL_MASK_PAN_DIR;
    g_pan.dir_sign      = (int8_t)PAN_DIR_SIGN;
    g_tilt.pin_step_mask = GIMBAL_MASK_TILT_STEP;
    g_tilt.pin_dir_mask  = GIMBAL_MASK_TILT_DIR;
    g_tilt.dir_sign      = (int8_t)TILT_DIR_SIGN;

    g_gimbal_tick10us       = 0;
    g_stepper_run_flag      = 0;
    g_stepper_pan_degs_milli  = 0;
    g_stepper_tilt_degs_milli = 0;
}

/* ================================================================
   StopAll – emergency, no step edges, SLP optional low.
   ================================================================ */
void GimbalStepper_StopAll(void)
{
    uint32_t bsrr = 0;

    stepper_stop_axis(&g_pan, &bsrr);
    stepper_stop_axis(&g_tilt, &bsrr);
    /* ensure DIR also low for both axes */
    bsrr |= ((uint32_t)GIMBAL_MASK_DIR) << 16U;

    if (bsrr) GIMBAL_GPIO_BSRR = bsrr;

#if GIMBAL_SLEEP_ON_STOPALL
    GIMBAL_GPIO_RESET(GIMBAL_MASK_SLP);
#endif

    g_stepper_run_flag      = 0;
    g_stepper_pan_degs_milli  = 0;
    g_stepper_tilt_degs_milli = 0;
}

/* ================================================================
   SetAxisSpeed – pre-compute half_period_ticks (called from 20ms loop)
   ================================================================ */
void GimbalStepper_SetAxisSpeed(GimbalAxis axis, float deg_per_sec)
{
    StepperAxis *a = (axis == GIMBAL_AXIS_PAN) ? &g_pan : &g_tilt;
    float clamped = deg_per_sec;
    float abs_speed, step_freq, half_period_us;
    uint32_t ticks;
    int new_dir_sign;

    if (clamped >  GIMBAL_MAX_DEG_PER_SEC) clamped =  GIMBAL_MAX_DEG_PER_SEC;
    if (clamped < -GIMBAL_MAX_DEG_PER_SEC) clamped = -GIMBAL_MAX_DEG_PER_SEC;
    a->target_deg_s = clamped;

    abs_speed = (float)(clamped < 0.0f ? -clamped : clamped);

    if (abs_speed < 0.001f) {
        a->half_period_ticks = 0;  /* stopped */
        return;
    }

    step_freq      = abs_speed / GIMBAL_MICROSTEP_DEG_PER_STEP;
    if (step_freq < 1.0f) step_freq = 1.0f;
    half_period_us = 500000.0f / step_freq;
    ticks = (uint32_t)(half_period_us / (float)GIMBAL_ISR_PERIOD_US + 0.5f);
    if (ticks < 1UL) ticks = 1UL;
    a->half_period_ticks = ticks;

    /* DIR update: if speed sign changed, request a safe direction change */
    new_dir_sign = (clamped > 0.0f) ? a->dir_sign : (int8_t)(-a->dir_sign);
    if (new_dir_sign != (a->dir_want_high ? a->dir_sign : (int8_t)(-a->dir_sign))) {
        a->dir_pending   = 1;
        a->dir_want_high = (uint8_t)(new_dir_sign > 0);
        a->dir_sign      = new_dir_sign; /* commit for next comparison */
    }
}

/* ================================================================
   ControlFromCommand – called every 20ms; uses tracker pan/tilt cmd.
   ================================================================ */
void GimbalStepper_ControlFromCommand(int32_t pan_cmd, int32_t tilt_cmd,
                                      int valid)
{
    float pan_dps, tilt_dps;

    if (!valid) {
        /* timeout is checked by the caller; here just zero targets */
        GimbalStepper_SetAxisSpeed(GIMBAL_AXIS_PAN,  0.0f);
        GimbalStepper_SetAxisSpeed(GIMBAL_AXIS_TILT, 0.0f);
    } else {
        pan_dps  = GIMBAL_RAW_TO_DEG_S((float)pan_cmd);
        tilt_dps = GIMBAL_RAW_TO_DEG_S((float)tilt_cmd);
        GimbalStepper_SetAxisSpeed(GIMBAL_AXIS_PAN,  pan_dps);
        GimbalStepper_SetAxisSpeed(GIMBAL_AXIS_TILT, tilt_dps);
    }

    g_stepper_run_flag      = (uint8_t)valid;
    g_stepper_pan_degs_milli  = (int32_t)(GIMBAL_RAW_TO_DEG_S((float)pan_cmd) * 1000.0f);
    g_stepper_tilt_degs_milli = (int32_t)(GIMBAL_RAW_TO_DEG_S((float)tilt_cmd) * 1000.0f);

    if (!valid) {
        g_stepper_pan_degs_milli  = 0;
        g_stepper_tilt_degs_milli = 0;
    }
}

/* ================================================================
   10us ISR – integer only; UIF always cleared.
   ================================================================ */
void GimbalStepper_Task10usISR(void)
{
    uint32_t bsrr = 0;

    /* Always clear UIF and increment tick — safe for macro=0. */
    GIMBAL_TIM_SR = 0U;   /* write 0 to clear all rc_w0 flags */
    ++g_gimbal_tick10us;

#if GIMBAL_ENABLE_STEPPER_OUTPUT
    if (!g_stepper_run_flag) return;

    /* --- PAN --- */
    {
        uint32_t ticks = g_pan.half_period_ticks;

        if (ticks == 0UL) {
            /* stopped */
            if (g_pan.step_level) {
                bsrr |= ((uint32_t)g_pan.pin_step_mask) << 16U;
                g_pan.step_level = 0;
            }
            g_pan.accum = 0;
        } else {
            /* pending DIR change: complete current step, then apply */
            if (g_pan.dir_pending) {
                if (g_pan.step_level) {
                    bsrr |= ((uint32_t)g_pan.pin_step_mask) << 16U;
                    g_pan.step_level = 0;
                }
                g_pan.accum = 0;
                g_pan.dir_pending = 0;
                bsrr |= g_pan.dir_want_high
                        ? (uint32_t)g_pan.pin_dir_mask
                        : ((uint32_t)g_pan.pin_dir_mask) << 16U;
            }

            g_pan.accum += 1UL;
            if (g_pan.accum >= ticks) {
                g_pan.accum -= ticks;
                g_pan.step_level ^= 1;
                bsrr |= g_pan.step_level
                        ? (uint32_t)g_pan.pin_step_mask
                        : ((uint32_t)g_pan.pin_step_mask) << 16U;
            }
        }
    }

    /* --- TILT --- */
    {
        uint32_t ticks = g_tilt.half_period_ticks;

        if (ticks == 0UL) {
            if (g_tilt.step_level) {
                bsrr |= ((uint32_t)g_tilt.pin_step_mask) << 16U;
                g_tilt.step_level = 0;
            }
            g_tilt.accum = 0;
        } else {
            if (g_tilt.dir_pending) {
                if (g_tilt.step_level) {
                    bsrr |= ((uint32_t)g_tilt.pin_step_mask) << 16U;
                    g_tilt.step_level = 0;
                }
                g_tilt.accum = 0;
                g_tilt.dir_pending = 0;
                bsrr |= g_tilt.dir_want_high
                        ? (uint32_t)g_tilt.pin_dir_mask
                        : ((uint32_t)g_tilt.pin_dir_mask) << 16U;
            }

            g_tilt.accum += 1UL;
            if (g_tilt.accum >= ticks) {
                g_tilt.accum -= ticks;
                g_tilt.step_level ^= 1;
                bsrr |= g_tilt.step_level
                        ? (uint32_t)g_tilt.pin_step_mask
                        : ((uint32_t)g_tilt.pin_step_mask) << 16U;
            }
        }
    }

    if (bsrr) GIMBAL_GPIO_BSRR = bsrr;
#endif /* GIMBAL_ENABLE_STEPPER_OUTPUT */
}
