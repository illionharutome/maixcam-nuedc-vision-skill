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
#define GIMBAL_MAX_DEG_PER_SEC          20.0f     /* initial safe max */
#define GIMBAL_CONTROL_PERIOD_MS        20
#define GIMBAL_ISR_PERIOD_US            10        /* TIM4 tick */
#define GIMBAL_ISR_US_TO_MS             (GIMBAL_ISR_PERIOD_US / 1000.0f)
#define GIMBAL_TIMEOUT_MS               200

/* ---- error deadband (pixels) ---- */
#define GIMBAL_DEADBAND_PX              20

/* ---- conversion: raw command (-1000..+1000) -> deg/s target ---- */
#define GIMBAL_RAW_RANGE                1000.0f
#define GIMBAL_RAW_TO_DEG_S(r)          (((float)(r) / GIMBAL_RAW_RANGE) * GIMBAL_MAX_DEG_PER_SEC)

/* ---- direction sign (set -1 in the field if axis is reversed) ---- */
#define PAN_DIR_SIGN    1
#define TILT_DIR_SIGN   1

/* ---- GPIO pins (PB port, step/dir for each axis + SLP/RST) ---- */
/* All on GPIOB to minimise register writes. */
#define GIMBAL_GPIO_BASE            0x40010C00UL
#define GIMBAL_GPIO_ODR             REG32(GIMBAL_GPIO_BASE + 0x0CUL)
#define GIMBAL_GPIO_BSRR            REG32(GIMBAL_GPIO_BASE + 0x10UL)

#define GIMBAL_PIN_PAN_STEP         5    /* PB5  */
#define GIMBAL_PIN_PAN_DIR          6    /* PB6  */
#define GIMBAL_PIN_TILT_STEP        7    /* PB7  */
#define GIMBAL_PIN_TILT_DIR         8    /* PB8  */
#define GIMBAL_PIN_SLP              9    /* PB9  (high = active, low = sleep) */
#define GIMBAL_PIN_RST              0    /* PB0  (high = active, low = reset) */

#define GIMBAL_BS_SET(pin)          (1UL << (pin))
#define GIMBAL_BS_RESET(pin)        (1UL << ((pin) + 16U))

#define GIMBAL_STEP_MASK            (GIMBAL_BS_SET(GIMBAL_PIN_PAN_STEP)  | \
                                     GIMBAL_BS_SET(GIMBAL_PIN_TILT_STEP))
#define GIMBAL_DIR_MASK             (GIMBAL_BS_SET(GIMBAL_PIN_PAN_DIR)   | \
                                     GIMBAL_BS_SET(GIMBAL_PIN_TILT_DIR))
#define GIMBAL_CTL_MASK             (GIMBAL_BS_SET(GIMBAL_PIN_SLP) | \
                                     GIMBAL_BS_SET(GIMBAL_PIN_RST))

/* ---- timer base for 10 us ISR ---- */
/* TIM4 on APB1: base 0x40000800, IRQn = 30 */
#define GIMBAL_TIM_BASE             0x40000800UL
#define GIMBAL_TIM_CR1              REG32(GIMBAL_TIM_BASE + 0x00UL)
#define GIMBAL_TIM_DIER             REG32(GIMBAL_TIM_BASE + 0x0CUL)
#define GIMBAL_TIM_SR               REG32(GIMBAL_TIM_BASE + 0x10UL)
#define GIMBAL_TIM_PSC              REG32(GIMBAL_TIM_BASE + 0x28UL)
#define GIMBAL_TIM_ARR              REG32(GIMBAL_TIM_BASE + 0x2CUL)
#define GIMBAL_TIM_PSC_VALUE        ((BRIDGE_PCLK1_HZ / 1000000UL) - 1UL)  /* 1 MHz timer clock */
#define GIMBAL_TIM_ARR_VALUE        9UL   /* (9+1) * 1 us = 10 us */
#define GIMBAL_TIM_IRQn             30UL

/* ---- dry-run logging over USART1 ---- */
#define GIMBAL_DRY_RUN_LOG_ENABLE   0
#define GIMBAL_DRY_RUN_LOG_MS       500  /* log interval */

#endif
