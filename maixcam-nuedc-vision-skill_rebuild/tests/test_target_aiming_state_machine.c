#include <assert.h>
#include <string.h>

#include "../mcu_tmx3507/app/target_aiming_state_machine.h"

int main(void)
{
    Aim_Result aim;
    TargetAimingConfig config = {0.1f, 0.1f, 1.0f, 2, 2};
    TargetAimingCommand command;
    memset(&aim, 0, sizeof(aim));
    strcpy(aim.mode, "AIM");
    strcpy(aim.status, "AIMING");
    aim.ok = 1U;
    aim.aim_error_x = 20;
    aim.aim_error_y = -5;
    target_aiming_update(&aim, &config, &command);
    assert(command.valid == 1U);
    assert(command.pan_command == 1.0f);
    assert(command.tilt_command == -0.5f);
    return 0;
}
