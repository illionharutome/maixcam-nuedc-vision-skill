#ifndef DRY_UART_PROBE_H
#define DRY_UART_PROBE_H

/*
 * Multi-port dry UART TX probe framework for Stage 2 gimbal output.
 * Supports USART3 (PB10), UART4 (PC10), UART5 (PC12).
 * All code is guarded by BRIDGE_ENABLE_GIMBAL_DRY_UART.
 */

#include "bridge_config.h"

#if BRIDGE_ENABLE_GIMBAL_DRY_UART && BRIDGE_USE_USART1

#include <stdint.h>

void dry_uart_probe_init(void);
void dry_uart_probe_send_str(const char *s);

#if BRIDGE_GIMBAL_DRY_UART_BOOT_TEST
void dry_uart_probe_boot_tick(uint32_t tick);
#endif

extern volatile uint32_t g_gimbal_tx_count;
extern volatile uint32_t g_gimbal_boot_sent;
extern const char *port_name;

#endif /* BRIDGE_ENABLE_GIMBAL_DRY_UART && BRIDGE_USE_USART1 */
#endif /* DRY_UART_PROBE_H */
