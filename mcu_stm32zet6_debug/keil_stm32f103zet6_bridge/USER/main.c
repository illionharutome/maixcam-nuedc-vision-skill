#include <stdint.h>

#include "bridge_config.h"
#include "mv_result.h"
#include "target_aiming_state_machine.h"
#include "protocol_track1.h"
#include "manual_tracker_state.h"
#include "dry_uart_probe.h"
#include "gimbal_stepper.h"

void vision_debug_bridge_init(void);
void vision_debug_bridge_rx_byte(uint8_t byte);

extern volatile Aim_Result g_latest_aim;
extern volatile TargetAimingCommand g_latest_command;
extern volatile Track1Packet g_latest_track1;
extern volatile ManualTracker g_latest_track1_command;
extern char g_latest_gimbal_dry_run[80];
extern volatile uint8_t g_debug_tx_pending;
extern volatile uint8_t g_debug_packet_kind;
extern volatile uint32_t g_gimbal_tx_count;
extern volatile uint32_t g_gimbal_boot_sent;

#define DEBUG_PACKET_AIM    1U
#define DEBUG_PACKET_TRACK1 2U

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
#define USART_SR_TXE        (1UL << 7)
#define USART_CR1_RE        (1UL << 2)
#define USART_CR1_TE        (1UL << 3)
#define USART_CR1_RXNEIE    (1UL << 5)
#define USART_CR1_UE        (1UL << 13)

uint32_t SystemCoreClock = BRIDGE_PCLK1_HZ;

void SystemInit(void)
{
    RCC_CR |= RCC_CR_HSION;
    while ((RCC_CR & RCC_CR_HSIRDY) == 0UL) {
    }
    RCC_CFGR = 0UL;
    while ((RCC_CFGR & RCC_CFGR_SWS_MASK) != 0UL) {
    }
    RCC_CR &= ~(RCC_CR_HSEON | RCC_CR_CSSON | RCC_CR_PLLON);
    RCC_CIR = 0UL;
    SystemCoreClock = BRIDGE_PCLK1_HZ;
}

#if BRIDGE_USE_USART1

static void uart1_tx_byte(char c)
{
    while ((USART1_SR & USART_SR_TXE) == 0UL) {
    }
    USART1_DR = (uint32_t)(uint8_t)c;
}

static void uart1_tx_str(const char *s)
{
    while (*s != '\0') {
        uart1_tx_byte(*s++);
    }
}

static void uart1_tx_int(int32_t value)
{
    char buf[12];
    int i = 0;
    uint32_t uval;

    if (value < 0) {
        uart1_tx_byte('-');
        uval = (uint32_t)(-value);
    } else {
        uval = (uint32_t)value;
    }
    if (uval == 0UL) {
        uart1_tx_byte('0');
        return;
    }
    while (uval > 0UL) {
        buf[i++] = (char)('0' + (uval % 10UL));
        uval /= 10UL;
    }
    while (i > 0) {
        uart1_tx_byte(buf[--i]);
    }
}

static void uart1_tx_uint(uint32_t value)
{
    char buf[12];
    int i = 0;

    if (value == 0UL) {
        uart1_tx_byte('0');
        return;
    }
    while (value > 0UL) {
        buf[i++] = (char)('0' + (value % 10UL));
        value /= 10UL;
    }
    while (i > 0) {
        uart1_tx_byte(buf[--i]);
    }
}

static void uart1_tx_milli(float value)
{
    uart1_tx_int((int32_t)(value * 1000.0f));
}

static const char *state_to_string(TargetAimingState state)
{
    switch (state) {
    case TARGET_AIM_DISABLED: return "DISABLED";
    case TARGET_AIM_NO_SPOT:  return "NO_SPOT";
    case TARGET_AIM_TRACKING: return "TRACKING";
    case TARGET_AIM_LOCKED:   return "LOCKED";
    default:                  return "UNKNOWN";
    }
}

static void bridge_debug_print_latest(void)
{
    if (g_debug_packet_kind == DEBUG_PACKET_TRACK1) {
        uart1_tx_str("$DBG,TRACK1");
        uart1_tx_str(",EX=");  uart1_tx_int(g_latest_track1.error_x);
        uart1_tx_str(",EY=");  uart1_tx_int(g_latest_track1.error_y);
        uart1_tx_str(",PAN="); uart1_tx_int(g_latest_track1_command.pan_command);
        uart1_tx_str(",TILT=");uart1_tx_int(g_latest_track1_command.tilt_command);
        uart1_tx_str(",VALID=");uart1_tx_uint((uint32_t)g_latest_track1_command.valid);
        uart1_tx_str(",STATUS=");uart1_tx_str((const char *)g_latest_track1.status);
        uart1_tx_str(",STATE=");uart1_tx_str(manual_state_name(g_latest_track1_command.state));
        uart1_tx_str("#\r\n");
#if BRIDGE_ENABLE_GIMBAL_MIRROR_ON_USART1
        uart1_tx_str(g_latest_gimbal_dry_run);
        uart1_tx_str("\r\n");
#endif
#if BRIDGE_ENABLE_GIMBAL_DRY_UART
        dry_uart_probe_send_str(g_latest_gimbal_dry_run);
#endif
        return;
    }

    /* Original AIM response is intentionally unchanged. */
    uart1_tx_str("$DBG,AIM");
    uart1_tx_str(",EX=");  uart1_tx_int(g_latest_aim.aim_error_x);
    uart1_tx_str(",EY=");  uart1_tx_int(g_latest_aim.aim_error_y);
    uart1_tx_str(",PAN="); uart1_tx_milli(g_latest_command.pan_command);
    uart1_tx_str(",TILT=");uart1_tx_milli(g_latest_command.tilt_command);
    uart1_tx_str(",VALID=");uart1_tx_uint((uint32_t)g_latest_command.valid);
    uart1_tx_str(",STATUS=");uart1_tx_str((const char *)g_latest_aim.status);
    uart1_tx_str(",STATE=");uart1_tx_str(state_to_string(g_latest_command.state));
    uart1_tx_str("#\r\n");
}

static void usart1_init(void)
{
    RCC_APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPAEN | RCC_APB2ENR_USART1EN;

    /* PA10 input floating (RX): CNF10=01, MODE10=00 -> CRH[11:8] = 0100. */
    GPIOA_CRH = (GPIOA_CRH & ~(0xFUL << 8)) | (0x4UL << 8);
    /* PA9 AF push-pull 50 MHz (TX): CNF9=10, MODE9=11 -> CRH[7:4] = 1011. */
    GPIOA_CRH = (GPIOA_CRH & ~(0xFUL << 4)) | (0xBUL << 4);

    USART1_CR1 = 0UL;
    USART1_CR2 = 0UL;
    USART1_CR3 = 0UL;
    USART1_BRR = BRIDGE_USART1_BRR;
    USART1_CR1 = USART_CR1_UE | USART_CR1_RE | USART_CR1_TE | USART_CR1_RXNEIE;

    /* USART1 IRQ number = 37 -> NVIC ISER1 bit 5. */
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
    usart1_init();
    GimbalStepper_Init();
#if BRIDGE_ENABLE_GIMBAL_DRY_UART
    dry_uart_probe_init();
#endif

    for (;;) {
        if (g_debug_tx_pending != 0U) {
            g_debug_tx_pending = 0U;
            bridge_debug_print_latest();
        }
#if GIMBAL_ENABLE_STEPPER_OUTPUT || GIMBAL_DRY_RUN_LOG_ENABLE
        {
            static uint32_t stepper_tick;
            static uint32_t stepper_ms;
            ++stepper_tick;
            /* rough ms counter: ~1 tick per main-loop iteration;
               at ~2M iter/s (8 MHz empty loop) this is approx 0.5 us/tick.
               Using 500 ticks ≈ 1 ms as a placeholder.
               Replace with a hardware timer for precision. */
            if ((stepper_tick % 1000UL) == 0UL) ++stepper_ms;

            if ((stepper_tick % (GIMBAL_CONTROL_PERIOD_MS * 1000UL)) == 0UL) {
                if (g_debug_packet_kind == DEBUG_PACKET_TRACK1) {
                    GimbalStepper_ControlFromError(
                        g_latest_track1.error_x,
                        g_latest_track1.error_y,
                        (int)g_latest_track1_command.valid,
                        stepper_ms);
                } else {
                    GimbalStepper_ControlFromError(0, 0, 0, stepper_ms);
                }
            }
#if GIMBAL_DRY_RUN_LOG_ENABLE
            {
                static uint32_t log_tick;
                if ((stepper_tick - log_tick) >= GIMBAL_DRY_RUN_LOG_MS * 1000UL) {
                    log_tick = stepper_tick;
                    uart1_tx_str("$DBG,STEPPER,PAN_DEG_S=");
                    uart1_tx_int((int32_t)(g_stepper_pan_deg_s * 1000.0f));
                    uart1_tx_str(",TILT_DEG_S=");
                    uart1_tx_int((int32_t)(g_stepper_tilt_deg_s * 1000.0f));
                    uart1_tx_str(",VALID=");
                    uart1_tx_uint(g_latest_track1_command.valid);
                    uart1_tx_str(",RUN=");
                    uart1_tx_uint(g_stepper_run_flag);
                    uart1_tx_str("#\r\n");
                }
            }
#endif
        }
#endif
#if BRIDGE_GIMBAL_DRY_UART_BOOT_TEST
        {
            static uint32_t diag_tick;
            ++diag_tick;
            if (diag_tick >= 2000000UL) {
                diag_tick = 0UL;
                uart1_tx_str("$DBG,GMUART,PORT=");
                uart1_tx_str(port_name);
                uart1_tx_str(",TX_COUNT=");
                uart1_tx_uint(g_gimbal_tx_count);
                uart1_tx_str("#\r\n");
            }
            dry_uart_probe_boot_tick(diag_tick);
        }
#endif
    }
}

#elif BRIDGE_USE_USART2

static void usart2_rx_init(void)
{
    RCC_APB2ENR |= RCC_APB2ENR_AFIOEN | RCC_APB2ENR_IOPAEN;
    RCC_APB1ENR |= RCC_APB1ENR_USART2EN;

    /* PA3 input floating: MODE3=00, CNF3=01 -> CRL[15:12] = 0100. */
    GPIOA_CRL = (GPIOA_CRL & ~(0xFUL << 12)) | (0x4UL << 12);

    USART2_CR1 = 0UL;
    USART2_CR2 = 0UL;
    USART2_CR3 = 0UL;
    USART2_BRR = BRIDGE_USART2_BRR;
    USART2_CR1 = USART_CR1_UE | USART_CR1_RE | USART_CR1_RXNEIE;

    /* USART2 IRQ number = 38 -> NVIC ISER1 bit 6. */
    {
        uint32_t nvic_bit = BRIDGE_USART2_IRQn - 32UL;
        if (nvic_bit < 32UL) {
            NVIC_ISER1 = (1UL << nvic_bit);
        }
    }
}

void TIM4_IRQHandler(void)
{
    GimbalStepper_Task10usISR();
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
    }
}

#endif
