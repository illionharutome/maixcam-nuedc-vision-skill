#ifndef USART_GIMBAL_DRY_H
#define USART_GIMBAL_DRY_H
#include <stdint.h>

/*
 * Stage 2 gimbal dry-run UART: TX-only USART3 (PB10) for USB-TTL monitoring.
 * When BRIDGE_ENABLE_GIMBAL_DRY_UART=0 the entire module compiles to nothing.
 */

#include "bridge_config.h"

#if BRIDGE_ENABLE_GIMBAL_DRY_UART && BRIDGE_USE_USART1

void gimbal_dry_uart_init(void);
void gimbal_dry_uart_send_str(const char *s);

/* Boot self-test: send $GM,BOOT,USART3,OK# once via USART3.
   Only compiled when BRIDGE_GIMBAL_DRY_UART_BOOT_TEST=1. */
void gimbal_dry_uart_boot_send(void);

/* Read-only counters for diagnostic DBG on USART1. */
extern volatile uint32_t g_gimbal_tx_count;
extern volatile uint32_t g_gimbal_boot_sent;

#endif /* BRIDGE_ENABLE_GIMBAL_DRY_UART && BRIDGE_USE_USART1 */
#endif /* USART_GIMBAL_DRY_H */
