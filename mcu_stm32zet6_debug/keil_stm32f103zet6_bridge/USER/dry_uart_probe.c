#include "dry_uart_probe.h"

#if BRIDGE_ENABLE_GIMBAL_DRY_UART && BRIDGE_USE_USART1

#define REG32(addr) (*(volatile uint32_t *)(addr))

/* --- RCC --- */
#define RCC_BASE            0x40021000UL
#define RCC_APB2ENR         REG32(RCC_BASE + 0x18UL)
#define RCC_APB1ENR         REG32(RCC_BASE + 0x1CUL)

/* --- GPIO --- */
#define GPIOB_BASE          0x40010C00UL
#define GPIOB_CRH           REG32(GPIOB_BASE + 0x04UL)

#define GPIOC_BASE          0x40011000UL
#define GPIOC_CRH           REG32(GPIOC_BASE + 0x04UL)

/* --- USART3 --- */
#define USART3_BASE         0x40004800UL

/* --- UART4 --- */
#define UART4_BASE          0x40004C00UL

/* --- UART5 --- */
#define UART5_BASE          0x40005000UL

#define UART_SR_OFFSET      0x00UL
#define UART_DR_OFFSET      0x04UL
#define UART_BRR_OFFSET     0x08UL
#define UART_CR1_OFFSET     0x0CUL

/* --- RCC bits --- */
#define RCC_APB2ENR_AFIOEN       (1UL << 0)
#define RCC_APB2ENR_IOPBEN       (1UL << 3)
#define RCC_APB2ENR_IOPCEN       (1UL << 4)
#define RCC_APB1ENR_USART3EN     (1UL << 18)
#define RCC_APB1ENR_UART4EN      (1UL << 19)
#define RCC_APB1ENR_UART5EN      (1UL << 20)

/* --- USART bit helpers --- */
#define UART_SR_TXE         (1UL << 7)
#define UART_CR1_TE         (1UL << 3)
#define UART_CR1_UE         (1UL << 13)

/* --- AFIO remap for USART3 partial remap (TX -> PC10) --- */
#define AFIO_BASE           0x40010000UL
#define AFIO_MAPR           REG32(AFIO_BASE + 0x04UL)
#define AFIO_MAPR_USART3_REMAP  (1UL << 0)

volatile uint32_t g_gimbal_tx_count;
volatile uint32_t g_gimbal_boot_sent;

static uint32_t probe_base;
static uint32_t uart_sr;
static uint32_t uart_dr;

#define PORT_NAME_USART3  "USART3"
#define PORT_NAME_UART4   "UART4"
#define PORT_NAME_UART5   "UART5"
const char *port_name = "NONE";

static void dry_uart_tx_byte(char c)
{
    while ((REG32(uart_sr) & UART_SR_TXE) == 0UL) {
    }
    REG32(uart_dr) = (uint32_t)(uint8_t)c;
}

void dry_uart_probe_send_str(const char *s)
{
    while (*s != '\0') {
        dry_uart_tx_byte(*s++);
    }
    dry_uart_tx_byte('\r');
    dry_uart_tx_byte('\n');
    ++g_gimbal_tx_count;
}

void dry_uart_probe_init(void)
{
    g_gimbal_tx_count = 0UL;
    g_gimbal_boot_sent = 0UL;

#if (BRIDGE_GIMBAL_DRY_UART_PORT == BRIDGE_GIMBAL_DRY_UART_PORT_USART3)
    port_name = PORT_NAME_USART3;
    RCC_APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPBEN;
    RCC_APB1ENR |= RCC_APB1ENR_USART3EN;
    GPIOB_CRH = (GPIOB_CRH & ~(0xFUL << 12)) | (0xBUL << 12);  /* PB10 AF PP 50MHz */
    GPIOB_CRH = (GPIOB_CRH & ~(0xFUL << 20)) | (0x4UL << 20);  /* PB11 IN floating */
    probe_base = USART3_BASE;

#elif (BRIDGE_GIMBAL_DRY_UART_PORT == BRIDGE_GIMBAL_DRY_UART_PORT_UART4)
    port_name = PORT_NAME_UART4;
    RCC_APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPCEN;
    RCC_APB1ENR |= RCC_APB1ENR_UART4EN;
    GPIOC_CRH = (GPIOC_CRH & ~(0xFUL << 12)) | (0xBUL << 12);  /* PC10 AF PP 50MHz */
    probe_base = UART4_BASE;

#elif (BRIDGE_GIMBAL_DRY_UART_PORT == BRIDGE_GIMBAL_DRY_UART_PORT_UART5)
    port_name = PORT_NAME_UART5;
    RCC_APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPCEN;
    RCC_APB1ENR |= RCC_APB1ENR_UART5EN;
    GPIOC_CRH = (GPIOC_CRH & ~(0xFUL << 20)) | (0xBUL << 20);  /* PC12 AF PP 50MHz */
    probe_base = UART5_BASE;

#else
    return;
#endif

    uart_sr  = probe_base + UART_SR_OFFSET;
    uart_dr  = probe_base + UART_DR_OFFSET;
    REG32(probe_base + UART_CR1_OFFSET) = 0UL;
    REG32(probe_base + UART_BRR_OFFSET) = BRIDGE_GIMBAL_UART_BRR;
    REG32(probe_base + UART_CR1_OFFSET) = UART_CR1_UE | UART_CR1_TE;
}

#if BRIDGE_GIMBAL_DRY_UART_BOOT_TEST
void dry_uart_probe_boot_tick(uint32_t tick)
{
    char buf[64];
    int n;
    char *p;
    uint32_t idx;
    n = 0;
    p = buf;
    while (n < (int)sizeof(buf) - 1) {
        char c = "$GM,BOOT,PORT=NONE,OK,TICK=xxxxx#\n"[n];
        if (c == '\0') break;
        p[n++] = c;
    }
    p[n] = '\0';

    /* Replace NONE and xxxxx placeholders. */
    {
        /* Find "PORT=" */
        char *port_start = buf;
        while (*port_start && (*port_start != 'P' || port_start[1] != 'O')) ++port_start;
        if (port_start[0] == 'P') {
            ++port_start; ++port_start; ++port_start; ++port_start; ++port_start; /* skip "PORT=" */
            {
                const char *src = port_name;
                while (*src) *port_start++ = *src++;
            }
        }
    }
    {
        /* Find "TICK=" */
        char *tick_start = buf;
        while (*tick_start && (*tick_start != 'T' || tick_start[1] != 'I')) ++tick_start;
        if (tick_start[0] == 'T') {
            tick_start += 5; /* skip "TICK=" */
            idx = (uint32_t)(tick / 1000UL);
            {
                char tmp[12];
                int pos = 0;
                if (idx == 0UL) { tmp[pos++] = '0'; }
                else { while (idx > 0UL) { tmp[pos++] = (char)('0' + (idx % 10UL)); idx /= 10UL; } }
                while (pos > 0) *tick_start++ = tmp[--pos];
            }
            *tick_start = '\0';
        }
    }
    dry_uart_probe_send_str(buf);
    g_gimbal_boot_sent = 1UL;
}
#endif /* BRIDGE_GIMBAL_DRY_UART_BOOT_TEST */

#endif /* BRIDGE_ENABLE_GIMBAL_DRY_UART && BRIDGE_USE_USART1 */
