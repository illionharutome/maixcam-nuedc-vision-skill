#include <assert.h>

#include "../mcu_common/mv_parser.h"
#include "../mcu_tmx3507/app/target_aiming_state_machine.h"

static int near_zero(float value)
{
    return (value > -0.0001f) && (value < 0.0001f);
}

static TargetAimingCommand parse_and_update(char *packet)
{
    static const TargetAimingConfig config = {0.05f, 0.05f, 1.0f, 2, 2};
    Aim_Result aim;
    TargetAimingCommand command;
    assert(mv_parse_packet(packet, &aim) == MV_PARSE_AIM_READY);
    target_aiming_update(&aim, &config, &command);
    return command;
}

int main(void)
{
    TargetAimingCommand command;
    char sample[] = "$MV,AIM,1,160,120,148,132,-12,12,0.91,25.6,AIMING#";
    char spot_right[] = "$MV,AIM,1,160,120,190,120,30,0,0.91,25.6,AIMING#";
    char spot_left[] = "$MV,AIM,1,160,120,120,120,-40,0,0.91,25.6,AIMING#";
    char spot_above[] = "$MV,AIM,1,160,120,160,100,0,-20,0.91,25.6,AIMING#";
    char no_spot[] = "$MV,AIM,0,160,120,0,0,0,0,0.00,25.6,NO_SPOT#";
    char aimed[] = "$MV,AIM,1,160,120,162,119,2,-1,0.95,25.6,AIMED#";
    char lost[] = "$MV,AIM,1,160,120,120,120,-40,0,0.91,25.6,LOST#";
    char error[] = "$MV,AIM,1,160,120,190,120,30,0,0.91,25.6,ERROR#";

    command = parse_and_update(sample);
    assert(command.valid == 1U);
    assert(command.state == TARGET_AIM_TRACKING);
    assert(command.pan_command < 0.0f);
    assert(command.tilt_command > 0.0f);

    command = parse_and_update(spot_right);
    assert(command.valid == 1U);
    assert(command.pan_command > 0.0f);
    assert(near_zero(command.tilt_command));

    command = parse_and_update(spot_left);
    assert(command.valid == 1U);
    assert(command.pan_command < 0.0f);
    assert(near_zero(command.tilt_command));

    command = parse_and_update(spot_above);
    assert(command.valid == 1U);
    assert(near_zero(command.pan_command));
    assert(command.tilt_command < 0.0f);

    command = parse_and_update(no_spot);
    assert(command.valid == 0U);
    assert(command.state == TARGET_AIM_NO_SPOT);
    assert(near_zero(command.pan_command));
    assert(near_zero(command.tilt_command));

    command = parse_and_update(aimed);
    assert(command.valid == 1U);
    assert(command.state == TARGET_AIM_LOCKED);
    assert(near_zero(command.pan_command));
    assert(near_zero(command.tilt_command));

    command = parse_and_update(lost);
    assert(command.valid == 0U);
    assert(near_zero(command.pan_command));
    assert(near_zero(command.tilt_command));

    command = parse_and_update(error);
    assert(command.valid == 0U);
    assert(near_zero(command.pan_command));
    assert(near_zero(command.tilt_command));
    return 0;
}
