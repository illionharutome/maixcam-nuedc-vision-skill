#include "usart_gimbal_dry.h"
#include <stdint.h>

#if BRIDGE_ENABLE_GIMBAL_DRY_UART && BRIDGE_USE_USART1

#define REG32(addr) (*(volatile uint32_t *)(addr))

#define RCC_BASE            0x40021000UL
#define RCC_APB2ENR         REG32(RCC_BASE + 0x18UL)
#define RCC_APB1ENR         REG32(RCC_BASE + 0x1CUL)

#define GPIOA_BASE          0x40010800UL
#define GPIOA_CRL           REG32(GPIOA_BASE + 0x00UL)

#define USART2_BASE         0x40004400UL
#define USART2_SR           REG32(USART2_BASE + 0x00UL)
#define USART2_DR           REG32(USART2_BASE + 0x04UL)
#define USART2_BRR          REG32(USART2_BASE + 0x08UL)
#define USART2_CR1          REG32(USART2_BASE + 0x0CUL)

#define RCC_APB2ENR_AFIOEN  (1UL << 0)
#define RCC_APB2ENR_IOPAEN  (1UL << 2)
#define RCC_APB1ENR_USART2EN (1UL << 17)
#define USART_SR_TXE        (1UL << 7)
#define USART_CR1_TE        (1UL << 3)
#define USART_CR1_UE        (1UL << 13)

void gimbal_dry_uart_init(void)
{
    RCC_APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPAEN;
    RCC_APB1ENR |= RCC_APB1ENR_USART2EN;

    /* PA2 AF push-pull 50 MHz TX: CNF2=10, MODE2=11 -> CRL[11:8] = 1011. */
    GPIOA_CRL = (GPIOA_CRL & ~(0xFUL << 8)) | (0xBUL << 8);

    USART2_CR1 = 0UL;
    USART2_BRR = BRIDGE_GIMBAL_UART_BRR;
    USART2_CR1 = USART_CR1_UE | USART_CR1_TE;
}

void gimbal_dry_uart_send_str(const char *s)
{
    while (*s != '\0') {
        while ((USART2_SR & USART_SR_TXE) == 0UL) {
        }
        USART2_DR = (uint32_t)(uint8_t)(*s++);
    }
    while ((USART2_SR & USART_SR_TXE) == 0UL) {
    }
    USART2_DR = (uint32_t)'\r';
    while ((USART2_SR & USART_SR_TXE) == 0UL) {
    }
    USART2_DR = (uint32_t)'\n';
}

#endif /* BRIDGE_ENABLE_GIMBAL_DRY_UART && BRIDGE_USE_USART1 */
