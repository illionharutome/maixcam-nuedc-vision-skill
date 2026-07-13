#ifndef LP_TRACKING_CONFIG_H
#define LP_TRACKING_CONFIG_H

/* Keep this at 0 until UART frames are visible on the XDS110 debug port. */
#define LP_TRACKING_ENABLE_MOTORS       (0U)

/* Enable and direction-calibrate one axis at a time. */
#define LP_TRACKING_ENABLE_PAN          (1U)
#define LP_TRACKING_ENABLE_TILT         (0U)
#define LP_TRACKING_INVERT_PAN          (0U)
#define LP_TRACKING_INVERT_TILT         (0U)

#define LP_TRACKING_DEADBAND_PX         (8U)
#define LP_TRACKING_MIN_SPEED_DPS       (5U)
#define LP_TRACKING_MAX_SPEED_DPS       (20U)
#define LP_TRACKING_CONFIDENCE_MIN      (20U)
#define LP_TRACKING_LOST_FRAME_LIMIT    (2U)
#define LP_TRACKING_TIMEOUT_MS          (100U)

#endif
