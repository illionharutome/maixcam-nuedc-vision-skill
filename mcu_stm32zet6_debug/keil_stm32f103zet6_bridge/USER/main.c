#include <stdint.h>

#include "bridge_config.h"

void vision_debug_bridge_init(void);
void vision_debug_bridge_rx_byte(uint8_t byte);

#define REG32(address) (*(volatile uint32_t *)(address))

/* --- RCC --- */
#define RCC_BASE            0x40021000UL
#define RCC_CR              REG32(RCC_BASE + 0x00UL)
#define RCC_CFGR            REG32(RCC_BASE + 0x04UL)
#define RCC_CIR             REG32(RCC_BASE + 0x08UL)
#define RCC_APB2ENR         REG32(RCC_BASE + 0x18UL)
#define RCC_APB1ENR         REG32(RCC_BASE + 0x1CUL)

/* --- GPIOA --- */
#define GPIOA_BASE          0x40010800UL
#define GPIOA_CRL           REG32(GPIOA_BASE + 0x00UL)
#define GPIOA_CRH           REG32(GPIOA_BASE + 0x04UL)

/* --- USART1 (APB2) --- */
#define USART1_BASE         0x40013800UL
#define USART1_SR           REG32(USART1_BASE + 0x00UL)
#define USART1_DR           REG32(USART1_BASE + 0x04UL)
#define USART1_BRR          REG32(USART1_BASE + 0x08UL)
#define USART1_CR1          REG32(USART1_BASE + 0x0CUL)
#define USART1_CR2          REG32(USART1_BASE + 0x10UL)
#define USART1_CR3          REG32(USART1_BASE + 0x14UL)

/* --- USART2 (APB1) --- */
#define USART2_BASE         0x40004400UL
#define USART2_SR           REG32(USART2_BASE + 0x00UL)
#define USART2_DR           REG32(USART2_BASE + 0x04UL)
#define USART2_BRR          REG32(USART2_BASE + 0x08UL)
#define USART2_CR1          REG32(USART2_BASE + 0x0CUL)
#define USART2_CR2          REG32(USART2_BASE + 0x10UL)
#define USART2_CR3          REG32(USART2_BASE + 0x14UL)

/* --- NVIC --- */
#define NVIC_ISER0          REG32(0xE000E100UL)
#define NVIC_ISER1          REG32(0xE000E104UL)

/* --- RCC control bits --- */
#define RCC_CR_HSION        (1UL << 0)
#define RCC_CR_HSIRDY       (1UL << 1)
#define RCC_CR_HSEON        (1UL << 16)
#define RCC_CR_CSSON        (1UL << 19)
#define RCC_CR_PLLON        (1UL << 24)
#define RCC_CFGR_SWS_MASK   (3UL << 2)
#define RCC_APB2ENR_AFIOEN  (1UL << 0)
#define RCC_APB2ENR_IOPAEN  (1UL << 2)
#define RCC_APB2ENR_USART1EN (1UL << 14)
#define RCC_APB1ENR_USART2EN (1UL << 17)

/* --- USART register bits --- */
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

#if BRIDGE_USE_USART1

static void usart1_rx_init(void)
{
    RCC_APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPAEN | RCC_APB2ENR_USART1EN;

    /* PA10 input floating (RX): CNF10=01, MODE10=00 → CRH[11:8] = 0100. */
    GPIOA_CRH = (GPIOA_CRH & ~(0xFUL << 8)) | (0x4UL << 8);

    USART1_CR1 = 0UL;
    USART1_CR2 = 0UL;
    USART1_CR3 = 0UL;
    USART1_BRR = BRIDGE_USART1_BRR;
    USART1_CR1 = USART_CR1_UE | USART_CR1_RE | USART_CR1_RXNEIE;

    /* USART1 IRQ number = 37 → NVIC ISER1 bit 5. */
    {
        uint32_t nvic_bit = BRIDGE_USART1_IRQn - 32UL;
        if (nvic_bit < 32UL) {
            NVIC_ISER1 = (1UL << nvic_bit);
        }
    }
}

void USART1_IRQHandler(void)
{
    uint32_t status;
    uint8_t received_byte;

    status = USART1_SR;
    if ((status & (USART_SR_RXNE | USART_SR_ORE | USART_SR_NE |
                   USART_SR_FE | USART_SR_PE)) != 0UL) {
        received_byte = (uint8_t)USART1_DR;
        vision_debug_bridge_rx_byte(received_byte);
    }
}

int main(void)
{
    vision_debug_bridge_init();
    usart1_rx_init();

    for (;;) {
        /* Watch-only debug bridge: no PID, PWM, or actuator control. */
    }
}

#elif BRIDGE_USE_USART2

static void usart2_rx_init(void)
{
    RCC_APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPAEN;
    RCC_APB1ENR |= RCC_APB1ENR_USART2EN;

    /* PA3 input floating: MODE3=00, CNF3=01 → CRL[15:12] = 0100. */
    GPIOA_CRL = (GPIOA_CRL & ~(0xFUL << 12)) | (0x4UL << 12);

    USART2_CR1 = 0UL;
    USART2_CR2 = 0UL;
    USART2_CR3 = 0UL;
    USART2_BRR = BRIDGE_USART2_BRR;
    USART2_CR1 = USART_CR1_UE | USART_CR1_RE | USART_CR1_RXNEIE;

    /* USART2 IRQ number = 38 → NVIC ISER1 bit 6. */
    {
        uint32_t nvic_bit = BRIDGE_USART2_IRQn - 32UL;
        if (nvic_bit < 32UL) {
            NVIC_ISER1 = (1UL << nvic_bit);
        }
    }
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

#endif
