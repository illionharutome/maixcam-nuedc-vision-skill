#include "gimbal_stepper.h"
#include "bridge_config.h"

#define REG32(addr) (*(volatile uint32_t *)(addr))

/* ---- local register interface (duplicated for independence) ---- */
#define RCC_BASE            0x40021000UL
#define RCC_APB2ENR         REG32(RCC_BASE + 0x18UL)
#define RCC_APB1ENR         REG32(RCC_BASE + 0x1CUL)
#define RCC_APB2ENR_IOPBEN  (1UL << 3)
#define RCC_APB1ENR_TIM4EN  (1UL << 2)

#define GPIOB_CRL           REG32(GIMBAL_GPIO_BASE + 0x00UL)
#define GPIOB_CRH           REG32(GIMBAL_GPIO_BASE + 0x04UL)
#define GPIOB_ODR           REG32(GIMBAL_GPIO_BASE + 0x0CUL)

/* NVIC */
#define NVIC_ISER0          REG32(0xE000E100UL)

/* ---- globals ---- */
volatile uint8_t g_stepper_run_flag;
volatile float   g_stepper_pan_deg_s;
volatile float   g_stepper_tilt_deg_s;

/* ---- per-axis state ---- */
typedef struct {
    uint8_t  dir_high;       /* 1 = DIR pin currently high */
    float    target_deg_s;   /* signed target speed */
    float    current_deg_s;  /* smoothed instantaneous */
    uint32_t half_period_us; /* half pulse period in us */
    uint32_t accum;          /* 10 us accumulator */
    uint8_t  step_level;     /* current STEP pin state (0/1) */
    uint8_t  pin_step;
    uint8_t  pin_dir;
    float    alpha;          /* smoothing factor */
} StepperAxis;

static StepperAxis g_pan, g_tilt;

/* ---- timeout state ---- */
static uint32_t g_last_valid_ms;
static uint8_t  g_timeout_active;

/* ---- direction helpers ---- */
static uint32_t dir_set(GimbalAxis axis, int high) {
    uint8_t pin = (axis == GIMBAL_AXIS_PAN) ? GIMBAL_PIN_PAN_DIR : GIMBAL_PIN_TILT_DIR;
    return high ? GIMBAL_BS_SET(pin) : GIMBAL_BS_RESET(pin);
}

static void update_dir_pin(GimbalAxis axis, StepperAxis *a, float target) {
    int want_high;
    int sign = (axis == GIMBAL_AXIS_PAN) ? PAN_DIR_SIGN : TILT_DIR_SIGN;
    if (target > 0.0f)
        want_high = (sign > 0) ? 1 : 0;
    else if (target < 0.0f)
        want_high = (sign > 0) ? 0 : 1;
    else
        return;  /* zero speed – keep current DIR */

    if (a->dir_high != (uint8_t)want_high) {
        a->dir_high = (uint8_t)want_high;
        GIMBAL_GPIO_BSRR = dir_set(axis, want_high);
    }
}

/* ================================================================
   Initialisation
   ================================================================ */
void GimbalStepper_Init(void)
{
    uint32_t crl, crh;
    uint32_t nvic_bit;

    /* clocks */
    RCC_APB2ENR |= RCC_APB2ENR_IOPBEN;
    RCC_APB1ENR |= RCC_APB1ENR_TIM4EN;

    /* GPIO config:
       PB5  (PAN_STEP)  -> GP output PP 50 MHz  : MODE=11 CNF=00
       PB6  (PAN_DIR)   -> GP output PP 50 MHz
       PB7  (TILT_STEP) -> GP output PP 50 MHz
       PB8  (TILT_DIR)  -> GP output PP 50 MHz
       PB9  (SLP)       -> GP output PP 50 MHz
       PB0  (RST)       -> GP output PP 50 MHz
    */
    crl = GPIOB_CRL;
    /* PB0: CRL[3:0] = 0011 */
    crl = (crl & ~0xFUL) | 0x3UL;
    /* PB5: CRL[23:20] = 0011 */
    crl = (crl & ~(0xFUL << 20)) | (0x3UL << 20);
    /* PB6: CRL[27:24] = 0011 */
    crl = (crl & ~(0xFUL << 24)) | (0x3UL << 24);
    /* PB7: CRL[31:28] = 0011 */
    crl = (crl & ~(0xFUL << 28)) | (0x3UL << 28);
    GPIOB_CRL = crl;

    crh = GPIOB_CRH;
    /* PB8: CRH[3:0] = 0011 */
    crh = (crh & ~0xFUL) | 0x3UL;
    /* PB9: CRH[7:4] = 0011 */
    crh = (crh & ~(0xFUL << 4)) | (0x3UL << 4);
    GPIOB_CRH = crh;

    /* start with all outputs low, then release SLP/RST (high) */
    GIMBAL_GPIO_BSRR = GIMBAL_STEP_MASK | GIMBAL_DIR_MASK | GIMBAL_CTL_MASK;
    GIMBAL_GPIO_BSRR = GIMBAL_BS_SET(GIMBAL_PIN_RST);
    GIMBAL_GPIO_BSRR = GIMBAL_BS_SET(GIMBAL_PIN_SLP);

    /* TIM4 for 10 us ISR */
    GIMBAL_TIM_PSC = GIMBAL_TIM_PSC_VALUE;
    GIMBAL_TIM_ARR = GIMBAL_TIM_ARR_VALUE;
    GIMBAL_TIM_DIER = (1UL << 0);  /* UI enable */
    GIMBAL_TIM_CR1  = (1UL << 0);  /* CEN */

    nvic_bit = GIMBAL_TIM_IRQn;
    if (nvic_bit < 32UL) NVIC_ISER0 = (1UL << nvic_bit);

    /* axis state init */
    g_pan.pin_step   = GIMBAL_PIN_PAN_STEP;
    g_pan.pin_dir    = GIMBAL_PIN_PAN_DIR;
    g_pan.alpha      = 0.3f;
    g_tilt.pin_step  = GIMBAL_PIN_TILT_STEP;
    g_tilt.pin_dir   = GIMBAL_PIN_TILT_DIR;
    g_tilt.alpha     = 0.3f;

    g_stepper_run_flag    = 0;
    g_stepper_pan_deg_s   = 0.0f;
    g_stepper_tilt_deg_s  = 0.0f;
    g_last_valid_ms       = 0;
    g_timeout_active      = 0;
}

/* ================================================================
   Stop all immediately
   ================================================================ */
void GimbalStepper_StopAll(void)
{
    GIMBAL_GPIO_BSRR = GIMBAL_STEP_MASK | GIMBAL_DIR_MASK;
    g_pan.target_deg_s  = 0.0f;
    g_pan.current_deg_s = 0.0f;
    g_pan.accum         = 0;
    g_tilt.target_deg_s  = 0.0f;
    g_tilt.current_deg_s = 0.0f;
    g_tilt.accum         = 0;
    g_stepper_run_flag   = 0;
    g_stepper_pan_deg_s  = 0.0f;
    g_stepper_tilt_deg_s = 0.0f;
    g_timeout_active     = 1;
}

/* ================================================================
   Set signed speed target
   ================================================================ */
void GimbalStepper_SetAxisSpeed(GimbalAxis axis, float deg_per_sec)
{
    StepperAxis *a = (axis == GIMBAL_AXIS_PAN) ? &g_pan : &g_tilt;
    float clamped = deg_per_sec;
    if (clamped >  GIMBAL_MAX_DEG_PER_SEC) clamped =  GIMBAL_MAX_DEG_PER_SEC;
    if (clamped < -GIMBAL_MAX_DEG_PER_SEC) clamped = -GIMBAL_MAX_DEG_PER_SEC;
    a->target_deg_s = clamped;
}

/* ================================================================
   Control from vision error
   ================================================================ */
void GimbalStepper_ControlFromError(int32_t ex, int32_t ey, int valid,
                                    uint32_t now_ms)
{
    float pan_raw, tilt_raw;
    float pan_target, tilt_target;
    int pan_dead, tilt_dead;

    if (!valid) {
        if (now_ms - g_last_valid_ms > GIMBAL_TIMEOUT_MS) {
            GimbalStepper_StopAll();
        }
        return;
    }
    g_last_valid_ms = now_ms;
    g_timeout_active = 0;

    /* convert pixel error -> raw command (using the tracker gains that
       produce -1000..+1000 pan/tilt commands from manual_tracker_state) */
    pan_raw  = (float)ex * 0.05f;   /* rough gain – same order as tracker kp */
    tilt_raw = (float)ey * 0.05f;

    /* deadband */
    pan_dead  = (abs(ex) <= GIMBAL_DEADBAND_PX);
    tilt_dead = (abs(ey) <= GIMBAL_DEADBAND_PX);

    pan_target  = pan_dead  ? 0.0f : GIMBAL_RAW_TO_DEG_S(pan_raw);
    tilt_target = tilt_dead ? 0.0f : GIMBAL_RAW_TO_DEG_S(tilt_raw);

    GimbalStepper_SetAxisSpeed(GIMBAL_AXIS_PAN,  pan_target);
    GimbalStepper_SetAxisSpeed(GIMBAL_AXIS_TILT, tilt_target);

    g_stepper_run_flag    = 1;
    g_stepper_pan_deg_s   = pan_target;
    g_stepper_tilt_deg_s  = tilt_target;
}

/* ================================================================
   10 us ISR – software STEP/DIR pulse generation
   ================================================================ */
void GimbalStepper_Task10usISR(void)
{
    uint32_t sr = GIMBAL_TIM_SR;
    uint32_t bsrr = 0;
    (void)sr;
    /* clear UIF */
    GIMBAL_TIM_SR = (uint16_t)~((uint16_t)0x0001);

#if GIMBAL_ENABLE_STEPPER_OUTPUT
    if (!g_stepper_run_flag) return;

    /* --- PAN --- */
    {
        float speed = g_pan.target_deg_s;
        /* smooth */
        g_pan.current_deg_s += g_pan.alpha * (speed - g_pan.current_deg_s);
        if (g_pan.current_deg_s > -0.01f && g_pan.current_deg_s < 0.01f) {
            /* stopped */
            if (g_pan.step_level) {
                bsrr |= GIMBAL_BS_RESET(g_pan.pin_step);
                g_pan.step_level = 0;
            }
            g_pan.accum = 0;
        } else {
            float abs_speed = (g_pan.current_deg_s > 0.0f) ? g_pan.current_deg_s
                                                            : -g_pan.current_deg_s;
            float step_freq = (float)GIMBAL_STEP_FREQ_FROM_DEG_S(abs_speed);
            uint32_t half_period;
            if (step_freq < 1.0f) step_freq = 1.0f;
            half_period = (uint32_t)(500000.0f / step_freq + 0.5f);  /* half period in us */
            if (half_period < (uint32_t)GIMBAL_ISR_PERIOD_US)
                half_period = (uint32_t)GIMBAL_ISR_PERIOD_US;
            g_pan.half_period_us = half_period;

            update_dir_pin(GIMBAL_AXIS_PAN, &g_pan, g_pan.current_deg_s);

            g_pan.accum += (uint32_t)GIMBAL_ISR_PERIOD_US;
            if (g_pan.accum >= half_period) {
                g_pan.accum -= half_period;
                g_pan.step_level ^= 1;
                bsrr |= g_pan.step_level ? GIMBAL_BS_SET(g_pan.pin_step)
                                         : GIMBAL_BS_RESET(g_pan.pin_step);
            }
        }
    }

    /* --- TILT --- */
    {
        float speed = g_tilt.target_deg_s;
        g_tilt.current_deg_s += g_tilt.alpha * (speed - g_tilt.current_deg_s);
        if (g_tilt.current_deg_s > -0.01f && g_tilt.current_deg_s < 0.01f) {
            if (g_tilt.step_level) {
                bsrr |= GIMBAL_BS_RESET(g_tilt.pin_step);
                g_tilt.step_level = 0;
            }
            g_tilt.accum = 0;
        } else {
            float abs_speed = (g_tilt.current_deg_s > 0.0f) ? g_tilt.current_deg_s
                                                              : -g_tilt.current_deg_s;
            float step_freq = (float)GIMBAL_STEP_FREQ_FROM_DEG_S(abs_speed);
            uint32_t half_period;
            if (step_freq < 1.0f) step_freq = 1.0f;
            half_period = (uint32_t)(500000.0f / step_freq + 0.5f);
            if (half_period < (uint32_t)GIMBAL_ISR_PERIOD_US)
                half_period = (uint32_t)GIMBAL_ISR_PERIOD_US;
            g_tilt.half_period_us = half_period;

            update_dir_pin(GIMBAL_AXIS_TILT, &g_tilt, g_tilt.current_deg_s);

            g_tilt.accum += (uint32_t)GIMBAL_ISR_PERIOD_US;
            if (g_tilt.accum >= half_period) {
                g_tilt.accum -= half_period;
                g_tilt.step_level ^= 1;
                bsrr |= g_tilt.step_level ? GIMBAL_BS_SET(g_tilt.pin_step)
                                          : GIMBAL_BS_RESET(g_tilt.pin_step);
            }
        }
    }

    if (bsrr) GIMBAL_GPIO_BSRR = bsrr;
#endif /* GIMBAL_ENABLE_STEPPER_OUTPUT */
}
