#ifndef GIMBAL_STEPPER_CONFIG_H
#define GIMBAL_STEPPER_CONFIG_H

#include "bridge_config.h"

/* ================================================================
   DCC-100 dual stepper driver pinout & parameters for STM32F103ZET6
   All outputs default LOW / inactive.
   Never push ENABLE_STEPPER_OUTPUT=1 into the repo.
   ================================================================ */

/* ---- master enable (default OFF) ---- */
#define GIMBAL_ENABLE_STEPPER_OUTPUT    0

/* ---- DCC-100 microstep spec ---- */
#define GIMBAL_MICROSTEP_DEG_PER_STEP   0.05625f
#define GIMBAL_STEP_FREQ_FROM_DEG_S(s)  ((uint32_t)((float)(s) / 0.05625f + 0.5f))

/* ---- speed & timing ---- */
#define GIMBAL_MAX_DEG_PER_SEC          20.0f
#define GIMBAL_CONTROL_PERIOD_MS        20
#define GIMBAL_CONTROL_TICKS            ((GIMBAL_CONTROL_PERIOD_MS) * 100UL)  /* 2000 ten-us ticks */
#define GIMBAL_ISR_PERIOD_US            10
#define GIMBAL_TIMEOUT_MS               200
#define GIMBAL_TIMEOUT_TICKS            ((GIMBAL_TIMEOUT_MS) * 100UL)

/* ---- error deadband (pixels) ---- */
#define GIMBAL_DEADBAND_PX              20

/* ---- conversion: raw command (-1000..+1000) -> deg/s target ---- */
#define GIMBAL_RAW_RANGE                1000.0f
#define GIMBAL_RAW_TO_DEG_S(r)          (((float)(r) / GIMBAL_RAW_RANGE) * GIMBAL_MAX_DEG_PER_SEC)

/* ---- direction sign (set -1 in the field if axis is reversed) ---- */
#define PAN_DIR_SIGN    1
#define TILT_DIR_SIGN   1

/* ---- sleep on emergency stop ---- */
#define GIMBAL_SLEEP_ON_STOPALL         1

/* ---- GPIO pins (PB port, step/dir for each axis + SLP/RST) ---- */
#define GIMBAL_GPIO_BASE            0x40010C00UL
#define GIMBAL_GPIO_BSRR            REG32(GIMBAL_GPIO_BASE + 0x10UL)

#define GIMBAL_PIN_PAN_STEP         5    /* PB5  */
#define GIMBAL_PIN_PAN_DIR          6    /* PB6  */
#define GIMBAL_PIN_TILT_STEP        7    /* PB7  */
#define GIMBAL_PIN_TILT_DIR         8    /* PB8  */
#define GIMBAL_PIN_SLP              9    /* PB9  (high = active) */
#define GIMBAL_PIN_RST              0    /* PB0  (high = active) */

/* Use BSRR SET (0-15) = high, RESET (16-31) = low */
#define GIMBAL_GPIO_SET(mask)       GIMBAL_GPIO_BSRR = (mask)
#define GIMBAL_GPIO_RESET(mask)     GIMBAL_GPIO_BSRR = ((mask) << 16U)

/* Individual pin masks (for BSRR SET bits 0-15) */
#define GIMBAL_MASK_PAN_STEP        (1UL << GIMBAL_PIN_PAN_STEP)
#define GIMBAL_MASK_PAN_DIR         (1UL << GIMBAL_PIN_PAN_DIR)
#define GIMBAL_MASK_TILT_STEP       (1UL << GIMBAL_PIN_TILT_STEP)
#define GIMBAL_MASK_TILT_DIR        (1UL << GIMBAL_PIN_TILT_DIR)
#define GIMBAL_MASK_SLP             (1UL << GIMBAL_PIN_SLP)
#define GIMBAL_MASK_RST             (1UL << GIMBAL_PIN_RST)

#define GIMBAL_MASK_STEP        (GIMBAL_MASK_PAN_STEP  | GIMBAL_MASK_TILT_STEP)
#define GIMBAL_MASK_DIR         (GIMBAL_MASK_PAN_DIR   | GIMBAL_MASK_TILT_DIR)
#define GIMBAL_MASK_CTL         (GIMBAL_MASK_SLP       | GIMBAL_MASK_RST)

/* ---- timer base for 10 us ISR ---- */
#define GIMBAL_TIM_BASE             0x40000800UL
#define GIMBAL_TIM_CR1              REG32(GIMBAL_TIM_BASE + 0x00UL)
#define GIMBAL_TIM_DIER             REG32(GIMBAL_TIM_BASE + 0x0CUL)
#define GIMBAL_TIM_SR               REG32(GIMBAL_TIM_BASE + 0x10UL)
#define GIMBAL_TIM_PSC              REG32(GIMBAL_TIM_BASE + 0x28UL)
#define GIMBAL_TIM_ARR              REG32(GIMBAL_TIM_BASE + 0x2CUL)
#define GIMBAL_TIM_PSC_VALUE        ((BRIDGE_PCLK1_HZ / 1000000UL) - 1UL)
#define GIMBAL_TIM_ARR_VALUE        9UL   /* (9+1)*1us=10us */
#define GIMBAL_TIM_IRQn             30UL

/* ---- dry-run logging over USART1 ---- */
#define GIMBAL_DRY_RUN_LOG_ENABLE   0
#define GIMBAL_DRY_RUN_LOG_MS       500

#endif
