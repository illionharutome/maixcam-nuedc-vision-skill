#ifndef BRIDGE_CONFIG_H
#define BRIDGE_CONFIG_H

/* UART selection: USART1 = onboard USB-UART (PA10 RX, PA9 TX), USART2 = PA3 RX. */
#define BRIDGE_USE_USART1    1
#define BRIDGE_USE_USART2    0

/* Minimal debug bridge clocking: reset-default HSI at 8 MHz.
   At reset CFGR=0, PCLK1 (APB1) = PCLK2 (APB2) = 8 MHz. */
#define BRIDGE_PCLK1_HZ       8000000UL
#define BRIDGE_USART_BAUD     115200UL

/* USART1 is on APB2, USART2 on APB1. Both run at BRIDGE_PCLK1_HZ in this
   configuration, so BRR is the same; we keep separate defines for clarity. */
#define BRIDGE_USART1_BRR     ((BRIDGE_PCLK1_HZ + (BRIDGE_USART_BAUD / 2UL)) / BRIDGE_USART_BAUD)
#define BRIDGE_USART2_BRR     ((BRIDGE_PCLK1_HZ + (BRIDGE_USART_BAUD / 2UL)) / BRIDGE_USART_BAUD)

/* STM32F103ZET6 vector table interrupt numbers. */
#define BRIDGE_USART1_IRQn    37UL
#define BRIDGE_USART2_IRQn    38UL

#if (BRIDGE_USE_USART1 == 0) && (BRIDGE_USE_USART2 == 0)
#error "At least one USART must be enabled (USART1 or USART2)"
#endif

#if (BRIDGE_USE_USART1 == 1) && (BRIDGE_USE_USART2 == 1)
#error "Only one USART may be enabled at a time (USART1 or USART2)"
#endif

#if ((BRIDGE_USE_USART1 && (BRIDGE_USART1_BRR == 0UL)) || \
     (BRIDGE_USE_USART2 && (BRIDGE_USART2_BRR == 0UL)))
#error "Invalid baud rate configuration"
#endif

/* --------------------------------------------------------------------------
   Stage 2 dry-run gimbal UART output — multi-port probe framework.
   All defaults are OFF / NONE.  Never push a non-zero / non-NONE value.
   -------------------------------------------------------------------------- */
#define BRIDGE_ENABLE_GIMBAL_DRY_UART      0
#define BRIDGE_GIMBAL_UART_BAUD            115200UL

/* Port selection (only one may be non-zero at a time when DRY_UART=1). */
#define BRIDGE_GIMBAL_DRY_UART_PORT_NONE    0
#define BRIDGE_GIMBAL_DRY_UART_PORT_USART3  3
#define BRIDGE_GIMBAL_DRY_UART_PORT_UART4   4
#define BRIDGE_GIMBAL_DRY_UART_PORT_UART5   5

#define BRIDGE_GIMBAL_DRY_UART_PORT  BRIDGE_GIMBAL_DRY_UART_PORT_NONE

#if BRIDGE_ENABLE_GIMBAL_DRY_UART
#define BRIDGE_GIMBAL_UART_BRR  ((BRIDGE_PCLK1_HZ + (BRIDGE_GIMBAL_UART_BAUD / 2UL)) / BRIDGE_GIMBAL_UART_BAUD)
#endif

/* Boot self-test: send $GM,BOOT,PORT=<name>,OK,TICK=<n># periodically.
   Default 0.  Set to 1 locally for TX-pin probing. */
#define BRIDGE_GIMBAL_DRY_UART_BOOT_TEST   0

/* Stage 2A: mirror $GM,CMD on USART1 (alongside $DBG,TRACK1).
   Default 0.  Use to verify command generation without a second serial port.
   Does NOT control any hardware, C8T6, PWM, or actuator. */
#define BRIDGE_ENABLE_GIMBAL_MIRROR_ON_USART1  0

#endif
