#include "key_debug.h"
#include "motor_adapter.h"

void key_debug_update(bool up, bool down, bool left, bool right, uint8_t speed_dps)
{
    if (left != right) motor_adapter_drive(MOTOR_PAN, right ? 1 : -1, speed_dps);
    else motor_adapter_stop(MOTOR_PAN);
    if (up != down) motor_adapter_drive(MOTOR_TILT, down ? 1 : -1, speed_dps);
    else motor_adapter_stop(MOTOR_TILT);
}

