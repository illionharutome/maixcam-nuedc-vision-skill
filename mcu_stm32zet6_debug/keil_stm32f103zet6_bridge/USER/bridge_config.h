#ifndef BRIDGE_CONFIG_H
#define BRIDGE_CONFIG_H

/* Minimal debug bridge clocking: reset-default HSI at 8 MHz. */
#define BRIDGE_PCLK1_HZ       8000000UL
#define BRIDGE_USART_BAUD     115200UL
#define BRIDGE_USART2_BRR     ((BRIDGE_PCLK1_HZ + (BRIDGE_USART_BAUD / 2UL)) / BRIDGE_USART_BAUD)

/* STM32F103ZET6 USART2 RX: PA3, 8-N-1, receive interrupt only. */
#define BRIDGE_USART2_IRQn    38UL

#if (BRIDGE_USART2_BRR == 0UL)
#error "Invalid USART2 baud configuration"
#endif

#endif
