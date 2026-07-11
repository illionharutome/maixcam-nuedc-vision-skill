#include "usart_gimbal_dry.h"
#include <stdint.h>

#if BRIDGE_ENABLE_GIMBAL_DRY_UART && BRIDGE_USE_USART1

#define REG32(addr) (*(volatile uint32_t *)(addr))

#define RCC_BASE            0x40021000UL
#define RCC_APB2ENR         REG32(RCC_BASE + 0x18UL)
#define RCC_APB1ENR         REG32(RCC_BASE + 0x1CUL)

#define GPIOB_BASE          0x40010C00UL
#define GPIOB_CRH           REG32(GPIOB_BASE + 0x04UL)

#define USART3_BASE         0x40004800UL
#define USART3_SR           REG32(USART3_BASE + 0x00UL)
#define USART3_DR           REG32(USART3_BASE + 0x04UL)
#define USART3_BRR          REG32(USART3_BASE + 0x08UL)
#define USART3_CR1          REG32(USART3_BASE + 0x0CUL)

#define RCC_APB2ENR_AFIOEN  (1UL << 0)
#define RCC_APB2ENR_IOPBEN  (1UL << 3)
#define RCC_APB1ENR_USART3EN (1UL << 18)
#define USART_SR_TXE        (1UL << 7)
#define USART_CR1_TE        (1UL << 3)
#define USART_CR1_UE        (1UL << 13)

void gimbal_dry_uart_init(void)
{
    RCC_APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPBEN;
    RCC_APB1ENR |= RCC_APB1ENR_USART3EN;

    /* PB10 AF push-pull 50 MHz TX: CNF10=10, MODE10=11 -> CRH[15:12] = 1011. */
    GPIOB_CRH = (GPIOB_CRH & ~(0xFUL << 12)) | (0xBUL << 12);
    /* PB11 input floating (RX, unconnected in stage 2): CNF11=01, MODE11=00
       -> CRH[23:20] = 0100.  Safe default; not used for TX-only dry-run. */
    GPIOB_CRH = (GPIOB_CRH & ~(0xFUL << 20)) | (0x4UL << 20);

    USART3_CR1 = 0UL;
    USART3_BRR = BRIDGE_GIMBAL_UART_BRR;
    USART3_CR1 = USART_CR1_UE | USART_CR1_TE;
}

void gimbal_dry_uart_send_str(const char *s)
{
    while (*s != '\0') {
        while ((USART3_SR & USART_SR_TXE) == 0UL) {
        }
        USART3_DR = (uint32_t)(uint8_t)(*s++);
    }
    while ((USART3_SR & USART_SR_TXE) == 0UL) {
    }
    USART3_DR = (uint32_t)'\r';
    while ((USART3_SR & USART_SR_TXE) == 0UL) {
    }
    USART3_DR = (uint32_t)'\n';
}

#endif /* BRIDGE_ENABLE_GIMBAL_DRY_UART && BRIDGE_USE_USART1 */
