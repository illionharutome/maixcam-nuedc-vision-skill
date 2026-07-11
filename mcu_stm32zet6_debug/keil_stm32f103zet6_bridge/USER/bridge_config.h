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

#endif
