#ifndef USART_GIMBAL_DRY_H
#define USART_GIMBAL_DRY_H

/*
 * Stage 2 gimbal dry-run UART: TX-only USART2 (PA2) for USB-TTL monitoring.
 * When BRIDGE_ENABLE_GIMBAL_DRY_UART=0 the entire module compiles to nothing.
 */

#include "bridge_config.h"

#if BRIDGE_ENABLE_GIMBAL_DRY_UART && BRIDGE_USE_USART1

void gimbal_dry_uart_init(void);
void gimbal_dry_uart_send_str(const char *s);

#endif /* BRIDGE_ENABLE_GIMBAL_DRY_UART && BRIDGE_USE_USART1 */
#endif /* USART_GIMBAL_DRY_H */
