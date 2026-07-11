#include <stdint.h>

#include "bridge_config.h"

void vision_debug_bridge_init(void);
void vision_debug_bridge_rx_byte(uint8_t byte);

#define REG32(address) (*(volatile uint32_t *)(address))

#define RCC_BASE            0x40021000UL
#define RCC_CR              REG32(RCC_BASE + 0x00UL)
#define RCC_CFGR            REG32(RCC_BASE + 0x04UL)
#define RCC_CIR             REG32(RCC_BASE + 0x08UL)
#define RCC_APB2ENR         REG32(RCC_BASE + 0x18UL)
#define RCC_APB1ENR         REG32(RCC_BASE + 0x1CUL)

#define GPIOA_BASE          0x40010800UL
#define GPIOA_CRL           REG32(GPIOA_BASE + 0x00UL)

#define USART2_BASE         0x40004400UL
#define USART2_SR           REG32(USART2_BASE + 0x00UL)
#define USART2_DR           REG32(USART2_BASE + 0x04UL)
#define USART2_BRR          REG32(USART2_BASE + 0x08UL)
#define USART2_CR1          REG32(USART2_BASE + 0x0CUL)
#define USART2_CR2          REG32(USART2_BASE + 0x10UL)
#define USART2_CR3          REG32(USART2_BASE + 0x14UL)

#define NVIC_ISER1          REG32(0xE000E104UL)

#define RCC_CR_HSION        (1UL << 0)
#define RCC_CR_HSIRDY       (1UL << 1)
#define RCC_CR_HSEON        (1UL << 16)
#define RCC_CR_CSSON        (1UL << 19)
#define RCC_CR_PLLON        (1UL << 24)
#define RCC_CFGR_SWS_MASK   (3UL << 2)
#define RCC_APB2ENR_AFIOEN  (1UL << 0)
#define RCC_APB2ENR_IOPAEN  (1UL << 2)
#define RCC_APB1ENR_USART2EN (1UL << 17)

#define USART_SR_PE         (1UL << 0)
#define USART_SR_FE         (1UL << 1)
#define USART_SR_NE         (1UL << 2)
#define USART_SR_ORE        (1UL << 3)
#define USART_SR_RXNE       (1UL << 5)
#define USART_CR1_RE        (1UL << 2)
#define USART_CR1_RXNEIE    (1UL << 5)
#define USART_CR1_UE        (1UL << 13)

uint32_t SystemCoreClock = BRIDGE_PCLK1_HZ;

void SystemInit(void)
{
    RCC_CR |= RCC_CR_HSION;
    while ((RCC_CR & RCC_CR_HSIRDY) == 0UL) {
        /* Wait for the internal 8 MHz clock. */
    }
    RCC_CFGR = 0UL;
    while ((RCC_CFGR & RCC_CFGR_SWS_MASK) != 0UL) {
        /* Wait until HSI is the system clock. */
    }
    RCC_CR &= ~(RCC_CR_HSEON | RCC_CR_CSSON | RCC_CR_PLLON);
    RCC_CIR = 0UL;
    SystemCoreClock = BRIDGE_PCLK1_HZ;
}

static void usart2_rx_init(void)
{
    RCC_APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPAEN;
    RCC_APB1ENR |= RCC_APB1ENR_USART2EN;

    /* PA3 input floating: MODE3=00, CNF3=01. */
    GPIOA_CRL = (GPIOA_CRL & ~(0xFUL << 12)) | (0x4UL << 12);

    USART2_CR1 = 0UL;
    USART2_CR2 = 0UL;
    USART2_CR3 = 0UL;
    USART2_BRR = BRIDGE_USART2_BRR;
    USART2_CR1 = USART_CR1_UE | USART_CR1_RE | USART_CR1_RXNEIE;

    NVIC_ISER1 = (1UL << (BRIDGE_USART2_IRQn - 32UL));
}

void USART2_IRQHandler(void)
{
    uint32_t status;
    uint8_t received_byte;

    status = USART2_SR;
    if ((status & (USART_SR_RXNE | USART_SR_ORE | USART_SR_NE |
                   USART_SR_FE | USART_SR_PE)) != 0UL) {
        received_byte = (uint8_t)USART2_DR;
        vision_debug_bridge_rx_byte(received_byte);
    }
}

int main(void)
{
    vision_debug_bridge_init();
    usart2_rx_init();

    for (;;) {
        /* Watch-only debug bridge: no PID, PWM, or actuator control. */
    }
}
