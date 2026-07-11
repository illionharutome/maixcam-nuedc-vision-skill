#include "gimbal_control.h"
#include "motor_adapter.h"

static GimbalConfig_t active;
static uint8_t lost_frames;

static uint8_t speed_for_error(int16_t error)
{
    uint16_t magnitude = error < 0 ? (uint16_t)(-(int32_t)error) : (uint16_t)error;
    uint16_t span = active.max_speed_dps - active.min_speed_dps;
    uint16_t speed = active.min_speed_dps + (magnitude * span) / 160U;
    return (uint8_t)(speed > active.max_speed_dps ? active.max_speed_dps : speed);
}

static void drive_axis(MotorAxis_t axis, int16_t error, uint8_t invert)
{
    int8_t direction;
    uint16_t magnitude = error < 0 ? (uint16_t)(-(int32_t)error) : (uint16_t)error;
    if (magnitude <= active.deadband_px) { motor_adapter_stop(axis); return; }
    direction = error > 0 ? 1 : -1;
    if (invert) direction = -direction;
    motor_adapter_drive(axis, direction, speed_for_error(error));
}

void gimbal_control_init(const GimbalConfig_t *config)
{
    active = *config;
    lost_frames = 0U;
    motor_adapter_init();
    motor_adapter_stop_all();
}

void gimbal_control_update(const VisionCommand_t *command)
{
    if (command->state == VISION_NO_TARGET || command->state == VISION_LOST || command->confidence < active.confidence_min) {
        if (lost_frames < 255U) ++lost_frames;
        if (lost_frames >= active.lost_frame_limit) motor_adapter_stop_all();
        return;
    }
    lost_frames = 0U;
    if (command->state == VISION_LOCKED) { motor_adapter_stop_all(); return; }
    drive_axis(MOTOR_PAN, command->dx, active.invert_pan);
    drive_axis(MOTOR_TILT, command->dy, active.invert_tilt);
}

void gimbal_control_on_frame_timeout(void)
{
    if (lost_frames < 255U) ++lost_frames;
    if (lost_frames >= active.lost_frame_limit) motor_adapter_stop_all();
}

